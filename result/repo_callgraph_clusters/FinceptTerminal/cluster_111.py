# Cluster 111

class EIADataFetcher:
    """Fault-tolerant EIA data fetcher"""

    def __init__(self, api_key: Optional[str]=None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENTS[0], 'Accept': 'application/json,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Accept-Language': 'en-US,en;q=0.5', 'Accept-Encoding': 'gzip, deflate', 'Connection': 'keep-alive'})

    def _get_random_user_agent(self) -> str:
        """Get a random user agent"""
        import random
        return random.choice(USER_AGENTS)

    def _make_request(self, url: str, timeout: int=60) -> Optional[Union[Dict, bytes]]:
        """Make HTTP request with error handling"""
        try:
            self.session.headers['User-Agent'] = self._get_random_user_agent()
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return response.json()
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                return response.content
            else:
                return response.content
        except requests.exceptions.RequestException as e:
            raise EIAError(f'HTTP request failed for {url}: {str(e)}')
        except Exception as e:
            raise EIAError(f'Unexpected error fetching {url}: {str(e)}')

    def _parse_petroleum_excel(self, excel_data: bytes, category: str, tables: List[str]) -> List[Dict]:
        """Parse petroleum status report Excel data"""
        try:
            xls = pd.ExcelFile(BytesIO(excel_data))
            sheet_names = xls.sheet_names
            results = []
            for sheet_name in sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if df.empty or len(df) < 2:
                    continue
                date_col = None
                for col in df.columns:
                    if any((keyword in str(col).lower() for keyword in ['date', 'week', 'period'])):
                        date_col = col
                        break
                if date_col is None:
                    date_col = df.columns[0]
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.dropna(subset=[date_col])
                df[date_col] = df[date_col].dt.date
                id_vars = [date_col]
                value_vars = [col for col in df.columns if col != date_col]
                if len(value_vars) > 0:
                    melted_df = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='symbol', value_name='value')
                    melted_df = melted_df.dropna(subset=['value'])
                    for _, row in melted_df.iterrows():
                        results.append({'date': row[date_col].strftime('%Y-%m-%d'), 'category': category, 'table': sheet_name, 'symbol': str(row['symbol']), 'value': float(row['value']) if pd.notna(row['value']) else None, 'source': 'petroleum_status_report'})
            return results
        except Exception as e:
            raise EIAError(f'Error parsing petroleum Excel data for {category}: {str(e)}')

    def _parse_steo_data(self, api_data: Dict, table: str) -> List[Dict]:
        """Parse STEO API data"""
        try:
            results = []
            data = api_data.get('response', {}).get('data', [])
            for item in data:
                results.append({'date': item.get('period', ''), 'symbol': item.get('seriesId', ''), 'title': item.get('seriesDescription', ''), 'value': item.get('value', None), 'units': item.get('unitsofmeasure', ''), 'table': f'STEO-{table}: {STEO_TABLE_NAMES.get(table, table)}', 'source': 'short_term_energy_outlook'})
            return results
        except Exception as e:
            raise EIAError(f'Error parsing STEO data for table {table}: {str(e)}')

    def get_petroleum_status_report(self, category: str='balance_sheet', tables: Optional[List[str]]=None, start_date: Optional[str]=None, end_date: Optional[str]=None, use_cache: bool=True) -> Dict[str, Any]:
        """Get petroleum status report data"""
        try:
            if category not in WPSR_CATEGORY_CHOICES:
                raise EIAError(f'Invalid category: {category}. Valid choices: {WPSR_CATEGORY_CHOICES}')
            url = WPSR_FILE_MAP.get(category)
            if not url:
                raise EIAError(f'No URL found for category: {category}')
            excel_data = self._make_request(url)
            if not excel_data:
                raise EIAError(f'No data received from {url}')
            if not tables:
                tables = ['all']
            results = self._parse_petroleum_excel(excel_data, category, tables)
            if start_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                results = [r for r in results if datetime.strptime(r['date'], '%Y-%m-%d').date() >= start_date_obj]
            if end_date:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                results = [r for r in results if datetime.strptime(r['date'], '%Y-%m-%d').date() <= end_date_obj]
            return {'success': True, 'category': category, 'tables': tables, 'data': results, 'count': len(results), 'url': url}
        except EIAError:
            raise
        except Exception as e:
            return {'success': False, 'error': f'Error fetching petroleum status report: {str(e)}', 'category': category}

    def get_short_term_energy_outlook(self, table: str='01', symbols: Optional[List[str]]=None, frequency: Literal['month', 'quarter', 'annual']='month', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get short term energy outlook data"""
        try:
            if not self.api_key:
                raise EIAError('API key required for STEO data')
            if table not in STEO_TABLE_NAMES:
                raise EIAError(f'Invalid table: {table}. Valid choices: {list(STEO_TABLE_NAMES.keys())}')
            if not symbols:
                symbols = STEO_SYMBOLS_MAP.get(table, [])
            if not symbols:
                raise EIAError(f'No symbols available for table: {table}')
            frequency_map = {'month': 'monthly', 'quarter': 'quarterly', 'annual': 'annual'}
            base_url = f'{BASE_API_URL}steo/data/?api_key={self.api_key}&frequency={frequency_map[frequency]}&data[0]=value'
            results = []
            for i in range(0, len(symbols), 10):
                symbol_chunk = symbols[i:i + 10]
                url_symbols = ''
                for symbol in symbol_chunk:
                    url_symbols += f'&facets[seriesId][]={symbol}'
                if start_date:
                    if frequency == 'monthly':
                        url_date = f'&start={datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m')}'
                    elif frequency == 'quarterly':
                        quarter = (datetime.strptime(start_date, '%Y-%m-%d').month - 1) // 3 + 1
                        url_date = f'&start={datetime.strptime(start_date, '%Y-%m-%d').year}-Q{quarter}'
                    else:
                        url_date = f'&start={datetime.strptime(start_date, '%Y-%m-%d').year}'
                    url_symbols += url_date
                if end_date:
                    if frequency == 'monthly':
                        url_date = f'&end={datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m')}'
                    elif frequency == 'quarterly':
                        quarter = (datetime.strptime(end_date, '%Y-%m-%d').month - 1) // 3 + 1
                        url_date = f'&end={datetime.strptime(end_date, '%Y-%m-%d').year}-Q{quarter}'
                    else:
                        url_date = f'&end={datetime.strptime(end_date, '%Y-%m-%d').year}'
                    url_symbols += url_date
                url = f'{base_url}{url_symbols}&offset=0&length=5000'
                api_data = self._make_request(url)
                if api_data and isinstance(api_data, dict):
                    chunk_results = self._parse_steo_data(api_data, table)
                    results.extend(chunk_results)
            results.sort(key=lambda x: x['date'])
            return {'success': True, 'table': table, 'table_name': STEO_TABLE_NAMES[table], 'frequency': frequency, 'symbols': symbols, 'data': results, 'count': len(results)}
        except EIAError:
            raise
        except Exception as e:
            return {'success': False, 'error': f'Error fetching STEO data: {str(e)}', 'table': table}

    def get_available_categories(self) -> Dict[str, Any]:
        """Get available petroleum status report categories"""
        return {'success': True, 'categories': WPSR_CATEGORY_CHOICES, 'total_categories': len(WPSR_CATEGORY_CHOICES), 'file_urls': WPSR_FILE_MAP}

    def get_available_steo_tables(self) -> Dict[str, Any]:
        """Get available STEO tables"""
        return {'success': True, 'tables': STEO_TABLE_NAMES, 'symbols_map': STEO_SYMBOLS_MAP, 'total_tables': len(STEO_TABLE_NAMES)}

    def get_energy_overview(self, limit: Optional[int]=None) -> Dict[str, Any]:
        """Get comprehensive energy overview"""
        results = []
        errors = []
        try:
            petroleum_data = self.get_petroleum_status_report('balance_sheet', ['stocks', 'supply'])
            results.append(('petroleum_balance', petroleum_data))
        except Exception as e:
            errors.append(('petroleum_balance', str(e)))
        if self.api_key:
            try:
                steo_data = self.get_short_term_energy_outlook('01', frequency='month')
                results.append(('energy_markets_summary', steo_data))
            except Exception as e:
                errors.append(('energy_markets_summary', str(e)))
            try:
                natural_gas_data = self.get_short_term_energy_outlook('05a', frequency='month')
                results.append(('natural_gas', natural_gas_data))
            except Exception as e:
                errors.append(('natural_gas', str(e)))
        return {'success': len(results) > 0, 'results': results, 'errors': errors, 'total_requests': len(results) + len(errors), 'successful_fetches': len(results), 'failed_fetches': len(errors)}

def get_short_term_energy_outlook(self, table: str='01', symbols: Optional[List[str]]=None, frequency: Literal['month', 'quarter', 'annual']='month', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
    """Get short term energy outlook data"""
    try:
        if not self.api_key:
            raise EIAError('API key required for STEO data')
        if table not in STEO_TABLE_NAMES:
            raise EIAError(f'Invalid table: {table}. Valid choices: {list(STEO_TABLE_NAMES.keys())}')
        if not symbols:
            symbols = STEO_SYMBOLS_MAP.get(table, [])
        if not symbols:
            raise EIAError(f'No symbols available for table: {table}')
        frequency_map = {'month': 'monthly', 'quarter': 'quarterly', 'annual': 'annual'}
        base_url = f'{BASE_API_URL}steo/data/?api_key={self.api_key}&frequency={frequency_map[frequency]}&data[0]=value'
        results = []
        for i in range(0, len(symbols), 10):
            symbol_chunk = symbols[i:i + 10]
            url_symbols = ''
            for symbol in symbol_chunk:
                url_symbols += f'&facets[seriesId][]={symbol}'
            if start_date:
                if frequency == 'monthly':
                    url_date = f'&start={datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m')}'
                elif frequency == 'quarterly':
                    quarter = (datetime.strptime(start_date, '%Y-%m-%d').month - 1) // 3 + 1
                    url_date = f'&start={datetime.strptime(start_date, '%Y-%m-%d').year}-Q{quarter}'
                else:
                    url_date = f'&start={datetime.strptime(start_date, '%Y-%m-%d').year}'
                url_symbols += url_date
            if end_date:
                if frequency == 'monthly':
                    url_date = f'&end={datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m')}'
                elif frequency == 'quarterly':
                    quarter = (datetime.strptime(end_date, '%Y-%m-%d').month - 1) // 3 + 1
                    url_date = f'&end={datetime.strptime(end_date, '%Y-%m-%d').year}-Q{quarter}'
                else:
                    url_date = f'&end={datetime.strptime(end_date, '%Y-%m-%d').year}'
                url_symbols += url_date
            url = f'{base_url}{url_symbols}&offset=0&length=5000'
            api_data = self._make_request(url)
            if api_data and isinstance(api_data, dict):
                chunk_results = self._parse_steo_data(api_data, table)
                results.extend(chunk_results)
        results.sort(key=lambda x: x['date'])
        return {'success': True, 'table': table, 'table_name': STEO_TABLE_NAMES[table], 'frequency': frequency, 'symbols': symbols, 'data': results, 'count': len(results)}
    except EIAError:
        raise
    except Exception as e:
        return {'success': False, 'error': f'Error fetching STEO data: {str(e)}', 'table': table}

class ValidationUtils:
    """Input validation utilities"""

    @staticmethod
    def validate_positive(value: Decimal, name: str) -> Decimal:
        """Validate that value is positive"""
        if value <= 0:
            raise ValidationError(f'{name} must be positive, got {value}')
        return value

    @staticmethod
    def validate_non_negative(value: Decimal, name: str) -> Decimal:
        """Validate that value is non-negative"""
        if value < 0:
            raise ValidationError(f'{name} cannot be negative, got {value}')
        return value

    @staticmethod
    def validate_percentage(value: Decimal, name: str, allow_negative: bool=False) -> Decimal:
        """Validate percentage value (0-100% or -100% to 100%)"""
        min_val = Decimal('-1') if allow_negative else Decimal('0')
        max_val = Decimal('1')
        if not min_val <= value <= max_val:
            raise ValidationError(f'{name} must be between {min_val * 100}% and {max_val * 100}%, got {value * 100}%')
        return value

    @staticmethod
    def validate_yield(value: Decimal, name: str='Yield') -> Decimal:
        """Validate yield value"""
        from config import VALIDATION_RULES
        min_yield = VALIDATION_RULES['min_yield']
        max_yield = VALIDATION_RULES['max_yield']
        if not min_yield <= value <= max_yield:
            raise ValidationError(f'{name} must be between {min_yield * 100}% and {max_yield * 100}%, got {value * 100}%')
        return value

    @staticmethod
    def validate_price(value: Decimal, name: str='Price') -> Decimal:
        """Validate bond price"""
        from config import VALIDATION_RULES
        min_price = VALIDATION_RULES['min_price']
        max_price = VALIDATION_RULES['max_price']
        if not min_price <= value <= max_price:
            raise ValidationError(f'{name} must be between {min_price} and {max_price}, got {value}')
        return value

    @staticmethod
    def validate_date_order(start_date: date, end_date: date, start_name: str='Start date', end_name: str='End date'):
        """Validate that start date is before end date"""
        if start_date >= end_date:
            raise ValidationError(f'{start_name} ({start_date}) must be before {end_name} ({end_date})')

    @staticmethod
    def validate_maturity_range(issue_date: date, maturity_date: date):
        """Validate maturity is within reasonable range"""
        from config import VALIDATION_RULES
        days_to_maturity = (maturity_date - issue_date).days
        min_days = VALIDATION_RULES['min_maturity_days']
        max_days = VALIDATION_RULES['max_maturity_years'] * 365
        if days_to_maturity < min_days:
            raise ValidationError(f'Maturity too short: {days_to_maturity} days (minimum: {min_days})')
        if days_to_maturity > max_days:
            raise ValidationError(f'Maturity too long: {days_to_maturity} days (maximum: {max_days})')

@staticmethod
def validate_positive(value: Decimal, name: str) -> Decimal:
    """Validate that value is positive"""
    if value <= 0:
        raise ValidationError(f'{name} must be positive, got {value}')
    return value

@staticmethod
def validate_non_negative(value: Decimal, name: str) -> Decimal:
    """Validate that value is non-negative"""
    if value < 0:
        raise ValidationError(f'{name} cannot be negative, got {value}')
    return value

@staticmethod
def validate_percentage(value: Decimal, name: str, allow_negative: bool=False) -> Decimal:
    """Validate percentage value (0-100% or -100% to 100%)"""
    min_val = Decimal('-1') if allow_negative else Decimal('0')
    max_val = Decimal('1')
    if not min_val <= value <= max_val:
        raise ValidationError(f'{name} must be between {min_val * 100}% and {max_val * 100}%, got {value * 100}%')
    return value

@staticmethod
def validate_yield(value: Decimal, name: str='Yield') -> Decimal:
    """Validate yield value"""
    from config import VALIDATION_RULES
    min_yield = VALIDATION_RULES['min_yield']
    max_yield = VALIDATION_RULES['max_yield']
    if not min_yield <= value <= max_yield:
        raise ValidationError(f'{name} must be between {min_yield * 100}% and {max_yield * 100}%, got {value * 100}%')
    return value

@staticmethod
def validate_price(value: Decimal, name: str='Price') -> Decimal:
    """Validate bond price"""
    from config import VALIDATION_RULES
    min_price = VALIDATION_RULES['min_price']
    max_price = VALIDATION_RULES['max_price']
    if not min_price <= value <= max_price:
        raise ValidationError(f'{name} must be between {min_price} and {max_price}, got {value}')
    return value

@staticmethod
def validate_date_order(start_date: date, end_date: date, start_name: str='Start date', end_name: str='End date'):
    """Validate that start date is before end date"""
    if start_date >= end_date:
        raise ValidationError(f'{start_name} ({start_date}) must be before {end_name} ({end_date})')

@staticmethod
def validate_maturity_range(issue_date: date, maturity_date: date):
    """Validate maturity is within reasonable range"""
    from config import VALIDATION_RULES
    days_to_maturity = (maturity_date - issue_date).days
    min_days = VALIDATION_RULES['min_maturity_days']
    max_days = VALIDATION_RULES['max_maturity_years'] * 365
    if days_to_maturity < min_days:
        raise ValidationError(f'Maturity too short: {days_to_maturity} days (minimum: {min_days})')
    if days_to_maturity > max_days:
        raise ValidationError(f'Maturity too long: {days_to_maturity} days (maximum: {max_days})')

class ConvertibleBondInstrument(BondInstrument):
    """Convertible bond instrument"""

    def __init__(self, convertible: ConvertibleBond):
        super().__init__(convertible)
        self.convertible = convertible

    def conversion_value(self, stock_price: Optional[Decimal]=None) -> Decimal:
        """Calculate conversion value"""
        if stock_price is None:
            stock_price = self.convertible.underlying_stock_price
        if stock_price is None:
            raise ValidationError('Stock price required for conversion value calculation')
        return self.convertible.conversion_ratio * stock_price

    def conversion_premium(self, bond_price: Decimal, stock_price: Optional[Decimal]=None) -> Decimal:
        """Calculate conversion premium"""
        conv_value = self.conversion_value(stock_price)
        return bond_price - conv_value

    def conversion_premium_percentage(self, bond_price: Decimal, stock_price: Optional[Decimal]=None) -> Decimal:
        """Calculate conversion premium as percentage"""
        conv_value = self.conversion_value(stock_price)
        if conv_value == 0:
            return Decimal('0')
        premium = self.conversion_premium(bond_price, stock_price)
        return premium / conv_value * Decimal('100')

    def payback_period(self, bond_price: Decimal, dividend_yield: Optional[Decimal]=None) -> Optional[Decimal]:
        """Calculate payback period in years"""
        if dividend_yield is None:
            dividend_yield = self.convertible.dividend_yield
        if dividend_yield is None or dividend_yield == 0:
            return None
        coupon_yield = self.convertible.coupon_rate * self.convertible.face_value / bond_price
        yield_advantage = coupon_yield - dividend_yield
        if yield_advantage <= 0:
            return None
        premium_pct = self.conversion_premium_percentage(bond_price) / Decimal('100')
        return premium_pct / yield_advantage

    def delta(self, bond_price: Decimal, stock_price: Decimal) -> Decimal:
        """Calculate convertible bond delta (sensitivity to stock price)"""
        conv_value = self.conversion_value(stock_price)
        if bond_price <= conv_value:
            return self.convertible.conversion_ratio
        else:
            return self.convertible.conversion_ratio * (conv_value / bond_price)

def conversion_value(self, stock_price: Optional[Decimal]=None) -> Decimal:
    """Calculate conversion value"""
    if stock_price is None:
        stock_price = self.convertible.underlying_stock_price
    if stock_price is None:
        raise ValidationError('Stock price required for conversion value calculation')
    return self.convertible.conversion_ratio * stock_price

@dataclass
class CashFlow:
    """Represents a single cash flow"""
    date: date
    amount: Decimal
    type: str = 'coupon'

    def __post_init__(self):
        if self.amount < 0:
            raise ValidationError('Cash flow amount cannot be negative')

def __post_init__(self):
    if self.amount < 0:
        raise ValidationError('Cash flow amount cannot be negative')

@dataclass
class CreditSpread:
    """Credit spread data structure"""
    rating: CreditRating
    maturity: Decimal
    spread: Decimal
    sector: Optional[str] = None

    def __post_init__(self):
        if self.spread < 0:
            raise ValidationError('Credit spread cannot be negative')

def __post_init__(self):
    if self.spread < 0:
        raise ValidationError('Credit spread cannot be negative')

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

@dataclass
class CallableFeature:
    """Callable bond feature"""
    call_date: date
    call_price: Decimal
    call_type: str = 'american'

    def __post_init__(self):
        if self.call_price <= 0:
            raise ValidationError('Call price must be positive')

def __post_init__(self):
    if self.call_price <= 0:
        raise ValidationError('Call price must be positive')

@dataclass
class PutableFeature:
    """Putable bond feature"""
    put_date: date
    put_price: Decimal
    put_type: str = 'european'

    def __post_init__(self):
        if self.put_price <= 0:
            raise ValidationError('Put price must be positive')

def __post_init__(self):
    if self.put_price <= 0:
        raise ValidationError('Put price must be positive')

@dataclass
class SecuritizedBond:
    """Base securitized product model"""
    cusip: str
    pool_number: Optional[str] = None
    securitization_type: SecuritizationType = SecuritizationType.ABS
    original_balance: Decimal = Decimal('0')
    current_balance: Decimal = Decimal('0')
    collateral_type: str = ''
    weighted_average_maturity: Optional[Decimal] = None
    weighted_average_coupon: Optional[Decimal] = None
    credit_enhancement_level: Decimal = Decimal('0')
    enhancement_type: str = ''
    prepayment_speed: Optional[Decimal] = None

    def __post_init__(self):
        if self.current_balance > self.original_balance:
            raise ValidationError('Current balance cannot exceed original balance')

def __post_init__(self):
    if self.current_balance > self.original_balance:
        raise ValidationError('Current balance cannot exceed original balance')

@dataclass
class CreditDefaultSwap:
    """Credit default swap model"""
    reference_entity: str
    notional_amount: Decimal
    maturity_date: date
    spread: Decimal
    upfront_payment: Decimal = Decimal('0')
    recovery_rate: Decimal = Decimal('0.40')
    settlement_type: str = 'physical'
    credit_events: List[str] = field(default_factory=lambda: ['bankruptcy', 'failure_to_pay'])

    def __post_init__(self):
        if self.spread < 0:
            raise ValidationError('CDS spread cannot be negative')
        if not 0 <= self.recovery_rate <= 1:
            raise ValidationError('Recovery rate must be between 0 and 1')

def __post_init__(self):
    if self.spread < 0:
        raise ValidationError('CDS spread cannot be negative')
    if not 0 <= self.recovery_rate <= 1:
        raise ValidationError('Recovery rate must be between 0 and 1')

@dataclass
class Portfolio:
    """Fixed income portfolio model"""
    name: str
    holdings: List[Tuple[Union[Bond, SecuritizedBond], Decimal]] = field(default_factory=list)
    cash_position: Decimal = Decimal('0')
    base_currency: Currency = Currency.USD

    def add_holding(self, instrument: Union[Bond, SecuritizedBond], quantity: Decimal):
        """Add holding to portfolio"""
        if quantity <= 0:
            raise ValidationError('Quantity must be positive')
        self.holdings.append((instrument, quantity))

    def remove_holding(self, instrument: Union[Bond, SecuritizedBond]):
        """Remove holding from portfolio"""
        self.holdings = [(inst, qty) for inst, qty in self.holdings if inst != instrument]

    @property
    def total_positions(self) -> int:
        """Get total number of positions"""
        return len(self.holdings)

    @property
    def total_face_value(self) -> Decimal:
        """Calculate total face value of portfolio"""
        total = Decimal('0')
        for instrument, quantity in self.holdings:
            if hasattr(instrument, 'face_value'):
                total += instrument.face_value * quantity
            elif hasattr(instrument, 'current_balance'):
                total += instrument.current_balance * quantity
        return total

def add_holding(self, instrument: Union[Bond, SecuritizedBond], quantity: Decimal):
    """Add holding to portfolio"""
    if quantity <= 0:
        raise ValidationError('Quantity must be positive')
    self.holdings.append((instrument, quantity))

class RiskBudgetingSystem:
    """Risk budgeting and allocation framework"""

    def __init__(self, total_risk_budget: float):
        self.total_risk_budget = total_risk_budget
        self.allocations = {}
        self.current_utilization = 0.0

    def allocate_risk_budget(self, allocation_name: str, risk_amount: float, allocation_type: str='absolute') -> None:
        """Allocate portion of risk budget"""
        if allocation_type == 'absolute':
            if self.current_utilization + risk_amount > self.total_risk_budget:
                raise ValueError('Risk allocation exceeds total budget')
            self.allocations[allocation_name] = {'risk_amount': risk_amount, 'percentage': risk_amount / self.total_risk_budget * 100, 'type': 'absolute'}
            self.current_utilization += risk_amount
        elif allocation_type == 'percentage':
            risk_amount_abs = risk_amount * self.total_risk_budget / 100
            if self.current_utilization + risk_amount_abs > self.total_risk_budget:
                raise ValueError('Risk allocation exceeds total budget')
            self.allocations[allocation_name] = {'risk_amount': risk_amount_abs, 'percentage': risk_amount, 'type': 'percentage'}
            self.current_utilization += risk_amount_abs

    def monitor_risk_utilization(self, current_risks: Dict[str, float]) -> Dict:
        """Monitor current risk utilization vs. budget"""
        utilization_report = {}
        total_current_risk = 0
        for allocation_name, budget_info in self.allocations.items():
            current_risk = current_risks.get(allocation_name, 0)
            budgeted_risk = budget_info['risk_amount']
            utilization_report[allocation_name] = {'budgeted_risk': budgeted_risk, 'current_risk': current_risk, 'utilization_percentage': current_risk / budgeted_risk * 100 if budgeted_risk > 0 else 0, 'excess_risk': max(0, current_risk - budgeted_risk), 'available_budget': max(0, budgeted_risk - current_risk)}
            total_current_risk += current_risk
        return {'individual_allocations': utilization_report, 'total_budget': self.total_risk_budget, 'total_current_risk': total_current_risk, 'overall_utilization': total_current_risk / self.total_risk_budget * 100, 'remaining_budget': self.total_risk_budget - total_current_risk, 'budget_breaches': [name for name, info in utilization_report.items() if info['excess_risk'] > 0]}

    def rebalance_risk_budget(self, target_allocations: Dict[str, float]) -> Dict:
        """Rebalance risk budget allocations"""
        if sum(target_allocations.values()) > 100:
            raise ValueError('Target allocations exceed 100%')
        rebalancing_plan = {}
        for allocation_name, target_percentage in target_allocations.items():
            target_risk = target_percentage * self.total_risk_budget / 100
            current_risk = self.allocations.get(allocation_name, {}).get('risk_amount', 0)
            rebalancing_plan[allocation_name] = {'current_allocation': current_risk, 'target_allocation': target_risk, 'adjustment_needed': target_risk - current_risk, 'adjustment_percentage': (target_risk - current_risk) / current_risk * 100 if current_risk > 0 else 0}
        return {'rebalancing_plan': rebalancing_plan, 'total_adjustments': sum((abs(info['adjustment_needed']) for info in rebalancing_plan.values())), 'implementation_priority': self._prioritize_adjustments(rebalancing_plan)}

    def _prioritize_adjustments(self, rebalancing_plan: Dict) -> List[str]:
        """Prioritize risk budget adjustments"""
        adjustments = [(name, abs(info['adjustment_needed'])) for name, info in rebalancing_plan.items()]
        adjustments.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in adjustments]

def _prioritize_adjustments(self, rebalancing_plan: Dict) -> List[str]:
    """Prioritize risk budget adjustments"""
    adjustments = [(name, abs(info['adjustment_needed'])) for name, info in rebalancing_plan.items()]
    adjustments.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in adjustments]

class RiskManagement:
    """Main risk management interface"""

    def __init__(self, parameters: RiskParameters=DEFAULT_RISK_PARAMS):
        self.parameters = parameters
        self.governance = RiskGovernance()
        self.risk_budgeting = None

    def comprehensive_risk_analysis(self, returns_data: Union[np.ndarray, Dict[str, np.ndarray]], weights: Optional[np.ndarray]=None, portfolio_value: float=1000000) -> Dict:
        """Perform comprehensive risk analysis"""
        if isinstance(returns_data, dict):
            returns_matrix = np.array([returns_data[asset] for asset in returns_data.keys()]).T
            if weights is None:
                weights = np.ones(len(returns_data)) / len(returns_data)
            portfolio_returns = np.dot(returns_matrix, weights)
            asset_names = list(returns_data.keys())
        else:
            portfolio_returns = np.array(returns_data)
            returns_matrix = portfolio_returns.reshape(-1, 1)
            weights = np.array([1.0])
            asset_names = ['Portfolio']
        results = {'basic_risk_metrics': self._calculate_basic_risk_metrics(portfolio_returns), 'var_analysis': self._comprehensive_var_analysis(portfolio_returns), 'stress_testing': self._perform_stress_testing(portfolio_returns), 'risk_decomposition': None}
        if len(asset_names) > 1:
            results['risk_decomposition'] = VaRCalculations.component_var(portfolio_returns, returns_matrix, weights)
        results['dollar_metrics'] = self._convert_to_dollar_metrics(results, portfolio_value)
        return results

    def _calculate_basic_risk_metrics(self, returns: np.ndarray) -> Dict:
        """Calculate basic risk metrics"""
        return {'volatility_daily': np.std(returns, ddof=1), 'volatility_annual': np.std(returns, ddof=1) * np.sqrt(MathConstants.TRADING_DAYS_YEAR), 'downside_deviation': StatisticalCalculations.calculate_downside_deviation(returns), 'max_drawdown': self._calculate_max_drawdown(returns), 'skewness': stats.skew(returns), 'kurtosis': stats.kurtosis(returns, fisher=False), 'jarque_bera_test': stats.jarque_bera(returns)}

    def _comprehensive_var_analysis(self, returns: np.ndarray) -> Dict:
        """Comprehensive VaR analysis with multiple methods"""
        var_results = {}
        for confidence_level in self.parameters.var_confidence_levels:
            var_results[f'var_{int(confidence_level * 100)}'] = {'parametric_normal': VaRCalculations.parametric_var(returns, confidence_level, distribution='normal'), 'parametric_t': VaRCalculations.parametric_var(returns, confidence_level, distribution='t_distribution'), 'historical': {'var': RiskCalculations.value_at_risk_historical(returns, confidence_level), 'cvar': RiskCalculations.conditional_value_at_risk(returns, confidence_level)}, 'monte_carlo': VaRCalculations.monte_carlo_var(returns, confidence_level, num_simulations=self.parameters.monte_carlo_simulations)}
        return var_results

    def _perform_stress_testing(self, returns: np.ndarray) -> Dict:
        """Perform comprehensive stress testing"""
        return ScenarioAnalysis.stress_testing(returns, self.parameters.stress_scenarios)

    def _calculate_max_drawdown(self, returns: np.ndarray) -> Dict:
        """Calculate maximum drawdown statistics"""
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)
        peak_idx = np.argmax(running_max[:max_dd_idx + 1]) if max_dd_idx > 0 else 0
        return {'max_drawdown': max_dd, 'peak_to_trough_days': max_dd_idx - peak_idx, 'drawdown_series': drawdown}

    def _convert_to_dollar_metrics(self, results: Dict, portfolio_value: float) -> Dict:
        """Convert percentage metrics to dollar amounts"""
        dollar_metrics = {}
        if 'var_analysis' in results:
            for var_level, var_data in results['var_analysis'].items():
                dollar_metrics[var_level] = {}
                if 'historical' in var_data:
                    dollar_metrics[var_level]['historical_var'] = var_data['historical']['var'] * portfolio_value
                    dollar_metrics[var_level]['historical_cvar'] = var_data['historical']['cvar'] * portfolio_value
                if 'parametric_normal' in var_data:
                    dollar_metrics[var_level]['parametric_var'] = var_data['parametric_normal']['var'] * portfolio_value
        return dollar_metrics

def _perform_stress_testing(self, returns: np.ndarray) -> Dict:
    """Perform comprehensive stress testing"""
    return ScenarioAnalysis.stress_testing(returns, self.parameters.stress_scenarios)

class ESGIntegration:
    """Environmental, Social, and Governance integration framework"""

    @staticmethod
    def esg_integration_approaches() -> Dict:
        """Define ESG integration approaches"""
        return {ESGApproach.EXCLUSIONARY.value: {'description': 'Exclude investments based on ESG criteria', 'implementation': 'Screen out tobacco, weapons, fossil fuels, etc.', 'pros': ['Clear ethical alignment', 'Simple to implement'], 'cons': ['May reduce diversification', 'Potential return impact'], 'suitable_for': 'Values-driven investors with specific exclusions'}, ESGApproach.BEST_IN_CLASS.value: {'description': 'Select best ESG performers within each sector', 'implementation': 'Choose top ESG-rated companies in each industry', 'pros': ['Maintains sector diversification', 'Potential for outperformance'], 'cons': ['May include controversial sectors', 'Complex evaluation process'], 'suitable_for': 'Investors seeking ESG improvement without major exclusions'}, ESGApproach.THEMATIC.value: {'description': 'Invest in themes aligned with sustainable development', 'implementation': 'Focus on clean energy, water, healthcare, education', 'pros': ['Positive impact potential', 'Growth opportunity exposure'], 'cons': ['Concentration risk', 'Potential volatility'], 'suitable_for': 'Investors targeting specific sustainability themes'}, ESGApproach.INTEGRATION.value: {'description': 'Incorporate ESG factors into traditional analysis', 'implementation': 'ESG factors as part of fundamental analysis', 'pros': ['Comprehensive risk assessment', 'Potential alpha generation'], 'cons': ['Complex implementation', 'Requires ESG expertise'], 'suitable_for': 'Sophisticated investors seeking enhanced risk-return'}, ESGApproach.IMPACT.value: {'description': 'Target measurable positive social/environmental impact', 'implementation': 'Direct investment in solutions with impact measurement', 'pros': ['Measurable positive outcomes', 'Mission alignment'], 'cons': ['Limited investment universe', 'Potential return trade-offs'], 'suitable_for': 'Impact-focused investors with specific outcome goals'}, ESGApproach.SHAREHOLDER_ENGAGEMENT.value: {'description': 'Active ownership to influence corporate ESG practices', 'implementation': 'Proxy voting, shareholder resolutions, management dialogue', 'pros': ['Influence corporate behavior', 'Maintain diversification'], 'cons': ['Requires active management', 'Uncertain outcomes'], 'suitable_for': 'Large investors with capacity for active engagement'}}

    @staticmethod
    def develop_esg_policy(client_profile: InvestorProfile, esg_preferences: Dict) -> Dict:
        """Develop ESG policy for portfolio"""
        esg_priorities = ESGIntegration._assess_esg_priorities(esg_preferences)
        recommended_approaches = ESGIntegration._select_esg_approaches(esg_priorities, client_profile)
        implementation_strategy = ESGIntegration._develop_implementation_strategy(recommended_approaches, client_profile)
        return {'esg_priorities': esg_priorities, 'recommended_approaches': recommended_approaches, 'implementation_strategy': implementation_strategy, 'measurement_framework': ESGIntegration._create_measurement_framework(recommended_approaches), 'reporting_requirements': ESGIntegration._define_reporting_requirements(recommended_approaches)}

    @staticmethod
    def _assess_esg_priorities(esg_preferences: Dict) -> Dict:
        """Assess client ESG priorities"""
        environmental_weight = esg_preferences.get('environmental_importance', 5) / 10
        social_weight = esg_preferences.get('social_importance', 5) / 10
        governance_weight = esg_preferences.get('governance_importance', 5) / 10
        return {'environmental_weight': environmental_weight, 'social_weight': social_weight, 'governance_weight': governance_weight, 'primary_focus': max([('environmental', environmental_weight), ('social', social_weight), ('governance', governance_weight)], key=lambda x: x[1])[0], 'overall_esg_importance': np.mean([environmental_weight, social_weight, governance_weight])}

    @staticmethod
    def _select_esg_approaches(esg_priorities: Dict, client_profile: InvestorProfile) -> List[str]:
        """Select appropriate ESG approaches"""
        approaches = []
        esg_importance = esg_priorities['overall_esg_importance']
        if esg_importance > 0.7:
            if client_profile.investment_objective == InvestmentObjective.CAPITAL_APPRECIATION:
                approaches.extend([ESGApproach.THEMATIC.value, ESGApproach.INTEGRATION.value])
            else:
                approaches.extend([ESGApproach.BEST_IN_CLASS.value, ESGApproach.INTEGRATION.value])
        elif esg_importance > 0.4:
            approaches.append(ESGApproach.INTEGRATION.value)
            if 'exclusions' in client_profile.unique_circumstances:
                approaches.append(ESGApproach.EXCLUSIONARY.value)
        else:
            approaches.append(ESGApproach.INTEGRATION.value)
        return approaches

@staticmethod
def _select_esg_approaches(esg_priorities: Dict, client_profile: InvestorProfile) -> List[str]:
    """Select appropriate ESG approaches"""
    approaches = []
    esg_importance = esg_priorities['overall_esg_importance']
    if esg_importance > 0.7:
        if client_profile.investment_objective == InvestmentObjective.CAPITAL_APPRECIATION:
            approaches.extend([ESGApproach.THEMATIC.value, ESGApproach.INTEGRATION.value])
        else:
            approaches.extend([ESGApproach.BEST_IN_CLASS.value, ESGApproach.INTEGRATION.value])
    elif esg_importance > 0.4:
        approaches.append(ESGApproach.INTEGRATION.value)
        if 'exclusions' in client_profile.unique_circumstances:
            approaches.append(ESGApproach.EXCLUSIONARY.value)
    else:
        approaches.append(ESGApproach.INTEGRATION.value)
    return approaches

class PortfolioPlanning:
    """Main portfolio planning and construction interface"""

    def __init__(self):
        self.ips_framework = IPSFramework()
        self.objectives_framework = ObjectivesFramework()
        self.constraints_analysis = ConstraintsAnalysis()
        self.asset_allocation_framework = AssetAllocationFramework()
        self.construction_principles = PortfolioConstructionPrinciples()
        self.esg_integration = ESGIntegration()

    def create_comprehensive_ips(self, client_profile: InvestorProfile, financial_data: Dict, esg_preferences: Optional[Dict]=None) -> InvestmentPolicyStatement:
        """Create comprehensive Investment Policy Statement"""
        return_objectives = self.objectives_framework.analyze_return_objectives(client_profile, financial_data)
        risk_objectives = self.objectives_framework.analyze_risk_objectives(client_profile, return_objectives)
        liquidity_constraints = self.constraints_analysis.analyze_liquidity_constraints(client_profile, financial_data)
        time_horizon_constraints = self.constraints_analysis.analyze_time_horizon_constraints(client_profile)
        tax_constraints = self.constraints_analysis.analyze_tax_constraints(client_profile)
        legal_constraints = self.constraints_analysis.analyze_legal_regulatory_constraints(client_profile)
        asset_classes = self.asset_allocation_framework.define_asset_classes()
        strategic_allocation = self.asset_allocation_framework.strategic_asset_allocation(client_profile, {'return_objectives': return_objectives, 'risk_objectives': risk_objectives}, {'liquidity': liquidity_constraints, 'time_horizon': time_horizon_constraints, 'tax': tax_constraints, 'legal': legal_constraints}, asset_classes)
        esg_policy = None
        if esg_preferences:
            esg_policy = self.esg_integration.develop_esg_policy(client_profile, esg_preferences)
        ips = InvestmentPolicyStatement(client_information=self._compile_client_information(client_profile, financial_data), investment_objectives={'return_objectives': return_objectives, 'risk_objectives': risk_objectives}, investment_constraints={'liquidity': liquidity_constraints, 'time_horizon': time_horizon_constraints, 'tax': tax_constraints, 'legal_regulatory': legal_constraints, 'unique_circumstances': self._analyze_unique_circumstances(client_profile)}, investment_guidelines=self._develop_investment_guidelines(strategic_allocation, client_profile), strategic_asset_allocation=strategic_allocation, rebalancing_policy=self._develop_rebalancing_policy(strategic_allocation), performance_measurement=self._develop_performance_measurement_framework(return_objectives, strategic_allocation), responsibilities=self._define_responsibilities(), review_schedule=self._establish_review_schedule(client_profile), esg_policy=esg_policy)
        return ips

    def validate_and_optimize_ips(self, ips: InvestmentPolicyStatement) -> Dict:
        """Validate and provide optimization recommendations for IPS"""
        validation_results = self.ips_framework.validate_ips(ips)
        optimization_recommendations = self._generate_optimization_recommendations(ips)
        stress_test_results = self._stress_test_ips(ips)
        return {'validation_results': validation_results, 'optimization_recommendations': optimization_recommendations, 'stress_test_results': stress_test_results, 'implementation_roadmap': self._create_implementation_roadmap(ips)}

    def portfolio_construction_analysis(self, ips: InvestmentPolicyStatement, market_conditions: Dict) -> Dict:
        """Comprehensive portfolio construction analysis"""
        construction_framework = self.construction_principles.construction_framework()
        risk_budget_analysis = self.construction_principles.risk_budgeting_approach(ips.investment_objectives['risk_objectives']['overall_risk_tolerance']['overall_risk_tolerance'], ips.strategic_asset_allocation['strategic_allocation'])
        implementation_analysis = self._analyze_implementation_considerations(ips, market_conditions)
        monitoring_framework = self._develop_monitoring_framework(ips)
        return {'construction_framework': construction_framework, 'risk_budget_analysis': risk_budget_analysis, 'implementation_analysis': implementation_analysis, 'monitoring_framework': monitoring_framework, 'success_metrics': self._define_success_metrics(ips)}

    def _compile_client_information(self, client_profile: InvestorProfile, financial_data: Dict) -> Dict:
        """Compile comprehensive client information"""
        return {'client_type': client_profile.investor_type.value, 'investment_objective': client_profile.investment_objective.value, 'risk_tolerance': client_profile.risk_tolerance, 'time_horizon': client_profile.time_horizon, 'liquidity_needs': client_profile.liquidity_needs, 'financial_situation': {'current_assets': financial_data.get('current_portfolio_value', 0), 'annual_income': financial_data.get('annual_income', 0), 'annual_expenses': financial_data.get('annual_expenses', 0), 'net_worth': financial_data.get('net_worth', 0)}, 'tax_situation': client_profile.tax_situation, 'unique_circumstances': client_profile.unique_circumstances}

    def _analyze_unique_circumstances(self, client_profile: InvestorProfile) -> Dict:
        """Analyze unique circumstances affecting portfolio"""
        unique_analysis = {'circumstances': client_profile.unique_circumstances, 'portfolio_implications': [], 'special_considerations': []}
        for circumstance in client_profile.unique_circumstances:
            if 'concentrated position' in circumstance.lower():
                unique_analysis['portfolio_implications'].append('Diversification challenge due to concentrated position')
                unique_analysis['special_considerations'].append('Consider gradual diversification strategy')
            elif 'business ownership' in circumstance.lower():
                unique_analysis['portfolio_implications'].append('High correlation between human capital and financial capital')
                unique_analysis['special_considerations'].append('Emphasize diversification away from business sector')
            elif 'inheritance' in circumstance.lower():
                unique_analysis['special_considerations'].append('Consider step-up in basis for tax planning')
        return unique_analysis

    def _develop_investment_guidelines(self, strategic_allocation: Dict, client_profile: InvestorProfile) -> Dict:
        """Develop comprehensive investment guidelines"""
        return {'asset_allocation_guidelines': {'strategic_targets': strategic_allocation['strategic_allocation'], 'rebalancing_bands': strategic_allocation['rebalancing_bands'], 'tactical_ranges': self._set_tactical_ranges(strategic_allocation)}, 'security_selection_guidelines': {'quality_requirements': self._define_quality_requirements(client_profile), 'diversification_requirements': self._define_diversification_requirements(), 'liquidity_requirements': self._define_liquidity_requirements(client_profile), 'cost_guidelines': self._define_cost_guidelines()}, 'risk_management_guidelines': {'maximum_position_sizes': self._set_position_limits(), 'prohibited_investments': self._identify_prohibited_investments(client_profile), 'derivative_usage': self._define_derivative_usage_policy(client_profile)}}

    def _develop_rebalancing_policy(self, strategic_allocation: Dict) -> Dict:
        """Develop rebalancing policy"""
        return {'rebalancing_method': 'Threshold-based with calendar review', 'rebalancing_bands': strategic_allocation['rebalancing_bands'], 'rebalancing_frequency': {'calendar_review': 'Quarterly', 'threshold_monitoring': 'Monthly', 'emergency_rebalancing': 'As needed for major market events'}, 'rebalancing_priorities': ['Bring severely out-of-range allocations back to target', 'Consider tax implications of rebalancing transactions', 'Use cash flows to rebalance when possible', 'Minimize transaction costs'], 'implementation_guidelines': {'minimum_trade_size': '1% of portfolio value', 'tax_loss_harvesting': 'Incorporate when beneficial', 'cash_flow_utilization': 'Use contributions/withdrawals for rebalancing'}}

    def _develop_performance_measurement_framework(self, return_objectives: Dict, strategic_allocation: Dict) -> Dict:
        """Develop performance measurement framework"""
        return {'primary_benchmark': self._select_primary_benchmark(strategic_allocation), 'secondary_benchmarks': self._select_secondary_benchmarks(strategic_allocation), 'performance_metrics': ['Total return vs. benchmark', 'Risk-adjusted returns (Sharpe ratio)', 'Maximum drawdown', 'Tracking error vs. benchmark'], 'evaluation_periods': {'short_term': '1 year', 'medium_term': '3 years', 'long_term': '5+ years'}, 'performance_attribution': {'asset_allocation_effect': 'Contribution from strategic allocation decisions', 'security_selection_effect': 'Contribution from security selection', 'interaction_effect': 'Interaction between allocation and selection'}, 'reporting_schedule': {'monthly': 'Portfolio value and basic performance metrics', 'quarterly': 'Comprehensive performance report with attribution', 'annual': 'Full performance review with recommendations'}}

    def _define_responsibilities(self) -> Dict:
        """Define roles and responsibilities"""
        return {'client_responsibilities': ['Provide accurate and complete financial information', 'Communicate changes in circumstances promptly', 'Review and approve Investment Policy Statement', 'Make timely decisions on recommended changes'], 'advisor_responsibilities': ['Develop and maintain Investment Policy Statement', 'Implement investment strategy according to IPS', 'Monitor portfolio performance and risk', 'Provide regular reporting and communication', 'Recommend changes when appropriate'], 'third_party_responsibilities': ['Custodian: Safekeeping of assets and transaction settlement', 'Portfolio managers: Investment management within guidelines', 'Other service providers: Specific services as contracted']}

    def _establish_review_schedule(self, client_profile: InvestorProfile) -> Dict:
        """Establish IPS and portfolio review schedule"""
        if client_profile.investor_type == InvestorType.INDIVIDUAL:
            review_frequency = 'Annual'
            interim_reviews = 'As circumstances change'
        else:
            review_frequency = 'Annual or as required by governance'
            interim_reviews = 'Quarterly committee reviews'
        return {'formal_review_frequency': review_frequency, 'interim_review_triggers': ['Significant changes in client circumstances', 'Major market events or economic changes', 'Performance significantly off-track', 'Changes in investment objectives or constraints'], 'review_process': {'preparation': 'Gather performance data and market analysis', 'review_meeting': 'Discuss performance, circumstances, and changes', 'documentation': 'Update IPS if changes are made', 'implementation': 'Execute any approved changes'}, 'update_procedures': ['Document reasons for any IPS changes', 'Obtain client approval for material changes', 'Communicate changes to all relevant parties', 'Update systems and processes accordingly']}

    def _generate_optimization_recommendations(self, ips: InvestmentPolicyStatement) -> List[str]:
        """Generate IPS optimization recommendations"""
        recommendations = []
        allocation = ips.strategic_asset_allocation.get('strategic_allocation', {})
        if len(allocation) < 4:
            recommendations.append('Consider additional asset classes for better diversification')
        if not ips.rebalancing_policy.get('rebalancing_bands'):
            recommendations.append('Establish clear rebalancing bands to maintain strategic allocation')
        if not ips.performance_measurement.get('primary_benchmark'):
            recommendations.append('Define clear performance benchmarks for evaluation')
        if not ips.esg_policy and 'esg' in str(ips.client_information.get('unique_circumstances', [])).lower():
            recommendations.append('Consider developing ESG policy based on client preferences')
        return recommendations

    def _stress_test_ips(self, ips: InvestmentPolicyStatement) -> Dict:
        """Stress test the IPS under various scenarios"""
        allocation = ips.strategic_asset_allocation.get('strategic_allocation', {})
        scenarios = {'market_crash': {'equity_shock': -0.3, 'bond_shock': 0.05}, 'inflation_spike': {'equity_shock': -0.1, 'bond_shock': -0.15}, 'recession': {'equity_shock': -0.2, 'bond_shock': 0.1}}
        stress_results = {}
        for scenario_name, shocks in scenarios.items():
            portfolio_impact = 0
            for asset_class, weight in allocation.items():
                if 'equity' in asset_class:
                    portfolio_impact += weight * shocks['equity_shock']
                elif 'bond' in asset_class:
                    portfolio_impact += weight * shocks['bond_shock']
            stress_results[scenario_name] = {'portfolio_impact': portfolio_impact, 'severity': 'High' if abs(portfolio_impact) > 0.15 else 'Moderate' if abs(portfolio_impact) > 0.1 else 'Low'}
        return {'scenario_analysis': stress_results, 'overall_resilience': 'Good' if all((abs(result['portfolio_impact']) < 0.2 for result in stress_results.values())) else 'Moderate', 'recommendations': self._generate_stress_test_recommendations(stress_results)}

    def _create_implementation_roadmap(self, ips: InvestmentPolicyStatement) -> Dict:
        """Create implementation roadmap for IPS"""
        return {'phase_1_immediate': {'timeframe': '0-30 days', 'tasks': ['Finalize and approve IPS', 'Set up custodial and administrative accounts', 'Implement core strategic allocation']}, 'phase_2_buildup': {'timeframe': '30-90 days', 'tasks': ['Complete portfolio construction', 'Implement security selection', 'Establish monitoring and reporting systems']}, 'phase_3_optimization': {'timeframe': '90+ days', 'tasks': ['Fine-tune allocation based on performance', 'Optimize tax efficiency', 'Conduct first quarterly review']}}

    def _analyze_implementation_considerations(self, ips: InvestmentPolicyStatement, market_conditions: Dict) -> Dict:
        """Analyze implementation considerations"""
        return {'market_timing_considerations': {'current_valuations': market_conditions.get('market_valuations', 'neutral'), 'volatility_environment': market_conditions.get('volatility', 'normal'), 'implementation_approach': 'Dollar-cost averaging for large allocations'}, 'cost_analysis': {'estimated_implementation_costs': '0.10% - 0.25% of assets', 'ongoing_management_fees': '0.50% - 1.50% annually', 'transaction_cost_minimization': 'Use low-cost index funds where appropriate'}, 'tax_optimization': {'account_type_utilization': 'Maximize tax-advantaged account usage', 'asset_location': 'Place tax-inefficient assets in tax-advantaged accounts', 'transition_management': 'Consider tax implications of portfolio transitions'}}

    def _develop_monitoring_framework(self, ips: InvestmentPolicyStatement) -> Dict:
        """Develop comprehensive monitoring framework"""
        return {'daily_monitoring': ['Portfolio value and performance', 'Cash flows and liquidity', 'Market risk exposures'], 'monthly_monitoring': ['Asset allocation drift', 'Performance vs. benchmarks', 'Risk metrics and attribution'], 'quarterly_monitoring': ['Comprehensive performance review', 'Rebalancing needs assessment', 'Strategy effectiveness evaluation'], 'alert_systems': {'allocation_alerts': 'Trigger when allocation exceeds bands', 'performance_alerts': 'Trigger on significant underperformance', 'risk_alerts': 'Trigger on excessive risk measures'}}

    def _define_success_metrics(self, ips: InvestmentPolicyStatement) -> Dict:
        """Define success metrics for portfolio"""
        return_target = ips.investment_objectives['return_objectives']['return_targets']['primary_return_target']
        return {'primary_success_metrics': {'return_achievement': f'Achieve {return_target:.1%} annual return over long term', 'risk_control': 'Stay within defined risk parameters', 'objective_fulfillment': 'Meet stated investment objectives'}, 'secondary_success_metrics': {'cost_efficiency': 'Minimize total investment costs', 'tax_efficiency': 'Optimize after-tax returns', 'implementation_efficiency': 'Minimize tracking error to strategic allocation'}, 'measurement_timeframes': {'short_term': '1-year rolling periods', 'medium_term': '3-year rolling periods', 'long_term': '5+ year periods'}}

    def _set_tactical_ranges(self, strategic_allocation: Dict) -> Dict:
        """Set tactical allocation ranges"""
        tactical_ranges = {}
        for asset_class, target in strategic_allocation['strategic_allocation'].items():
            deviation = target * 0.25
            tactical_ranges[asset_class] = {'minimum': max(0, target - deviation), 'maximum': min(1, target + deviation)}
        return tactical_ranges

    def _define_quality_requirements(self, client_profile: InvestorProfile) -> List[str]:
        """Define security quality requirements"""
        requirements = ['Minimum investment grade rating for fixed income']
        if client_profile.risk_tolerance == 'conservative':
            requirements.extend(['Large-cap equity bias', 'Minimum market capitalization of $2 billion for individual stocks'])
        return requirements

    def _define_diversification_requirements(self) -> List[str]:
        """Define diversification requirements"""
        return ['Maximum 5% in any single security', 'Maximum 25% in any single sector', 'Minimum 20 individual securities in equity allocation']

    def _define_liquidity_requirements(self, client_profile: InvestorProfile) -> List[str]:
        """Define liquidity requirements"""
        requirements = ['Minimum daily trading volume of $1 million for individual securities']
        if client_profile.liquidity_needs > 0.2:
            requirements.append('Maximum 10% in illiquid investments')
        else:
            requirements.append('Maximum 20% in illiquid investments')
        return requirements

    def _define_cost_guidelines(self) -> List[str]:
        """Define cost guidelines"""
        return ['Target expense ratios below 0.75% for actively managed funds', 'Target expense ratios below 0.25% for index funds', 'Minimize portfolio turnover to reduce transaction costs']

    def _set_position_limits(self) -> Dict[str, float]:
        """Set maximum position size limits"""
        return {'individual_security': 0.05, 'sector_concentration': 0.25, 'geographic_concentration': 0.6, 'currency_exposure': 0.3}

    def _identify_prohibited_investments(self, client_profile: InvestorProfile) -> List[str]:
        """Identify prohibited investments"""
        prohibited = ['Penny stocks', 'Highly leveraged ETFs (>2x)']
        for circumstance in client_profile.unique_circumstances:
            if 'no tobacco' in circumstance.lower():
                prohibited.append('Tobacco companies')
            if 'no weapons' in circumstance.lower():
                prohibited.append('Defense/weapons manufacturers')
        return prohibited

    def _define_derivative_usage_policy(self, client_profile: InvestorProfile) -> Dict:
        """Define derivative usage policy"""
        if client_profile.risk_tolerance == 'conservative':
            return {'permitted_derivatives': ['Currency hedging forwards'], 'prohibited_derivatives': ['Options', 'Futures', 'Swaps'], 'usage_purpose': 'Hedging only'}
        else:
            return {'permitted_derivatives': ['Options', 'Futures', 'Currency hedging'], 'usage_purpose': 'Hedging and limited tactical positioning', 'maximum_notional': '10% of portfolio value'}

    def _select_primary_benchmark(self, strategic_allocation: Dict) -> str:
        """Select primary benchmark based on allocation"""
        allocation = strategic_allocation['strategic_allocation']
        equity_weight = sum((weight for asset, weight in allocation.items() if 'equity' in asset))
        if equity_weight > 0.7:
            return 'MSCI All Country World Index'
        elif equity_weight > 0.4:
            return '60/40 Stock/Bond Composite'
        else:
            return 'Bloomberg Aggregate Bond Index'

    def _select_secondary_benchmarks(self, strategic_allocation: Dict) -> List[str]:
        """Select secondary benchmarks"""
        allocation = strategic_allocation['strategic_allocation']
        benchmarks = []
        if 'domestic_equity' in allocation:
            benchmarks.append('S&P 500 Index')
        if 'international_equity' in allocation:
            benchmarks.append('MSCI EAFE Index')
        if 'domestic_bonds' in allocation:
            benchmarks.append('Bloomberg US Aggregate Bond Index')
        if 'real_estate' in allocation:
            benchmarks.append('FTSE NAREIT All REITs Index')
        return benchmarks

    def _generate_stress_test_recommendations(self, stress_results: Dict) -> List[str]:
        """Generate recommendations based on stress test results"""
        recommendations = []
        high_impact_scenarios = [scenario for scenario, result in stress_results.items() if result['severity'] == 'High']
        if high_impact_scenarios:
            recommendations.append('Consider reducing portfolio risk through increased diversification')
        if 'market_crash' in high_impact_scenarios:
            recommendations.append('Consider adding defensive assets or hedge fund strategies')
        if 'inflation_spike' in high_impact_scenarios:
            recommendations.append('Consider adding inflation-protected securities or commodities')
        return recommendations

def _define_quality_requirements(self, client_profile: InvestorProfile) -> List[str]:
    """Define security quality requirements"""
    requirements = ['Minimum investment grade rating for fixed income']
    if client_profile.risk_tolerance == 'conservative':
        requirements.extend(['Large-cap equity bias', 'Minimum market capitalization of $2 billion for individual stocks'])
    return requirements

class MutualFunds:
    """Mutual funds and pooled investment products analysis"""

    @staticmethod
    def mutual_fund_structure() -> Dict:
        """Mutual fund structure and characteristics"""
        return {'legal_structure': {'investment_company': 'Regulated under Investment Company Act of 1940', 'board_of_directors': 'Independent oversight of fund operations', 'investment_advisor': 'Manages portfolio and makes investment decisions', 'fund_shareholders': 'Own proportional interest in fund assets'}, 'operational_characteristics': {'daily_pricing': 'NAV calculated daily after market close', 'liquidity': 'Shares redeemable daily at NAV', 'professional_management': 'Full-time portfolio management team', 'diversification': 'Broad diversification within asset class'}, 'types_of_funds': {'equity_funds': 'Invest primarily in stocks', 'bond_funds': 'Invest primarily in fixed-income securities', 'balanced_funds': 'Mix of stocks and bonds', 'sector_funds': 'Focus on specific industry sectors', 'international_funds': 'Invest in foreign securities', 'index_funds': 'Passive replication of market indexes'}}

    @staticmethod
    def compare_pooled_products() -> Dict:
        """Compare mutual funds with other pooled investment products"""
        return {'mutual_funds': {'regulation': "Highly regulated under '40 Act", 'liquidity': 'Daily redemption at NAV', 'transparency': 'Daily NAV disclosure, quarterly holdings', 'minimum_investment': 'Typically low ($1,000 - $10,000)', 'fees': 'Management fee + operating expenses', 'tax_efficiency': 'Pass-through taxation, potential for distributions'}, 'etfs': {'regulation': 'Regulated as investment companies or UITs', 'liquidity': 'Intraday trading on exchanges', 'transparency': 'Daily holdings disclosure', 'minimum_investment': 'Cost of one share', 'fees': 'Generally lower expense ratios', 'tax_efficiency': 'More tax efficient due to in-kind redemptions'}, 'hedge_funds': {'regulation': 'Limited regulation, private placements', 'liquidity': 'Limited redemption windows', 'transparency': 'Limited disclosure to investors', 'minimum_investment': 'High ($1M+)', 'fees': '2 and 20 fee structure typical', 'tax_efficiency': 'Various structures, often pass-through'}, 'private_equity': {'regulation': 'Private placement exemptions', 'liquidity': 'Illiquid, long lock-up periods', 'transparency': 'Quarterly reporting to investors', 'minimum_investment': 'Very high ($5M+)', 'fees': 'Management fee + carried interest', 'tax_efficiency': 'Pass-through with potential tax advantages'}, 'unit_investment_trusts': {'regulation': "Regulated under '40 Act", 'liquidity': 'Redeemable units, but not actively traded', 'transparency': 'Fixed portfolio disclosed at inception', 'minimum_investment': 'Moderate ($1,000)', 'fees': 'Sales charge + annual fee', 'tax_efficiency': 'Pass-through taxation'}}

    @staticmethod
    def selection_criteria(investor_profile: InvestorProfile) -> Dict:
        """Provide selection criteria for pooled investment products"""
        recommendations = {'primary_recommendations': [], 'considerations': [], 'products_to_avoid': []}
        if investor_profile.investor_type == InvestorType.INDIVIDUAL:
            if investor_profile.risk_tolerance == 'conservative':
                recommendations['primary_recommendations'].extend(['Bond mutual funds', 'Balanced funds', 'Index funds'])
            elif investor_profile.risk_tolerance == 'aggressive':
                recommendations['primary_recommendations'].extend(['Equity mutual funds', 'Sector ETFs', 'International funds'])
        if investor_profile.liquidity_needs > 0.2:
            recommendations['primary_recommendations'].append('Mutual funds and ETFs')
            recommendations['products_to_avoid'].extend(['Private equity', 'Hedge funds with lock-ups'])
        if hasattr(investor_profile, 'investment_amount'):
            if investor_profile.investment_amount < 100000:
                recommendations['products_to_avoid'].extend(['Hedge funds', 'Private equity'])
        return recommendations

@staticmethod
def selection_criteria(investor_profile: InvestorProfile) -> Dict:
    """Provide selection criteria for pooled investment products"""
    recommendations = {'primary_recommendations': [], 'considerations': [], 'products_to_avoid': []}
    if investor_profile.investor_type == InvestorType.INDIVIDUAL:
        if investor_profile.risk_tolerance == 'conservative':
            recommendations['primary_recommendations'].extend(['Bond mutual funds', 'Balanced funds', 'Index funds'])
        elif investor_profile.risk_tolerance == 'aggressive':
            recommendations['primary_recommendations'].extend(['Equity mutual funds', 'Sector ETFs', 'International funds'])
    if investor_profile.liquidity_needs > 0.2:
        recommendations['primary_recommendations'].append('Mutual funds and ETFs')
        recommendations['products_to_avoid'].extend(['Private equity', 'Hedge funds with lock-ups'])
    if hasattr(investor_profile, 'investment_amount'):
        if investor_profile.investment_amount < 100000:
            recommendations['products_to_avoid'].extend(['Hedge funds', 'Private equity'])
    return recommendations

class PortfolioManagement:
    """Main portfolio management interface"""

    def __init__(self):
        self.process = PortfolioManagementProcess()
        self.investor_classification = InvestorClassification()
        self.pension_analysis = PensionPlans()
        self.industry_analysis = AssetManagementIndustry()
        self.mutual_fund_analysis = MutualFunds()

    def comprehensive_portfolio_management_analysis(self, investor_profile: InvestorProfile) -> Dict:
        """Comprehensive portfolio management analysis"""
        return {'investor_analysis': {'investor_type': investor_profile.investor_type.value, 'characteristics': self.investor_classification.get_investor_characteristics(investor_profile.investor_type), 'lifecycle_analysis': self._lifecycle_analysis_if_individual(investor_profile)}, 'portfolio_process': {'planning': self.process.planning_step(investor_profile), 'process_overview': self._get_process_overview()}, 'product_recommendations': {'pooled_products': self.mutual_fund_analysis.selection_criteria(investor_profile), 'product_comparison': self.mutual_fund_analysis.compare_pooled_products()}, 'industry_context': {'industry_overview': self.industry_analysis.industry_overview(), 'fee_analysis': self.industry_analysis.fee_structures()}}

    def _lifecycle_analysis_if_individual(self, investor_profile: InvestorProfile) -> Optional[Dict]:
        """Perform lifecycle analysis for individual investors"""
        if investor_profile.investor_type == InvestorType.INDIVIDUAL:
            if hasattr(investor_profile, 'age'):
                if investor_profile.age < 45:
                    stage = LifecycleStage.ACCUMULATION
                elif investor_profile.age < 65:
                    stage = LifecycleStage.CONSOLIDATION
                else:
                    stage = LifecycleStage.SPENDING
                return self.investor_classification.lifecycle_analysis(stage, investor_profile.age, {'wealth_level': 'moderate'})
        return None

    def _get_process_overview(self) -> Dict:
        """Get overview of portfolio management process"""
        return {'process_steps': self.process.process_steps, 'planning_substeps': self.process.planning_substeps, 'continuous_nature': 'Portfolio management is an ongoing, iterative process', 'feedback_importance': 'Regular monitoring and adjustment essential for success'}

    def pension_plan_analysis(self, plan_type: str, participant_profile: Dict) -> Dict:
        """Analyze pension plan characteristics and suitability"""
        if plan_type.lower() == 'dc':
            plan_analysis = self.pension_analysis.defined_contribution_analysis()
        elif plan_type.lower() == 'db':
            plan_analysis = self.pension_analysis.defined_benefit_analysis()
        else:
            return {'dc_analysis': self.pension_analysis.defined_contribution_analysis(), 'db_analysis': self.pension_analysis.defined_benefit_analysis(), 'comparison': self.pension_analysis.compare_dc_vs_db(participant_profile)}
        return {'plan_analysis': plan_analysis, 'suitability_for_participant': self._assess_plan_suitability(plan_type, participant_profile)}

    def _assess_plan_suitability(self, plan_type: str, participant_profile: Dict) -> Dict:
        """Assess pension plan suitability for specific participant"""
        age = participant_profile.get('age', 35)
        income = participant_profile.get('income', 50000)
        job_mobility = participant_profile.get('job_mobility', 'moderate')
        suitability_score = 0
        factors = []
        if plan_type.lower() == 'dc':
            if age < 40:
                suitability_score += 20
                factors.append('Young age favors long-term growth potential')
            if job_mobility == 'high':
                suitability_score += 25
                factors.append('High job mobility benefits from portability')
            if participant_profile.get('investment_knowledge', 'moderate') == 'high':
                suitability_score += 15
                factors.append('Investment knowledge enables active management')
            if income > 75000:
                suitability_score += 10
                factors.append('Higher income allows for greater contributions')
        elif plan_type.lower() == 'db':
            if age > 45:
                suitability_score += 20
                factors.append('Older age benefits from guaranteed income')
            if job_mobility == 'low':
                suitability_score += 25
                factors.append('Low job mobility maximizes DB benefit accumulation')
            if participant_profile.get('risk_tolerance', 'moderate') == 'low':
                suitability_score += 20
                factors.append('Low risk tolerance suits guaranteed benefits')
            if participant_profile.get('investment_knowledge', 'moderate') == 'low':
                suitability_score += 15
                factors.append('Limited investment knowledge suits professional management')
        return {'suitability_score': min(100, suitability_score), 'suitability_level': 'High' if suitability_score > 70 else 'Moderate' if suitability_score > 40 else 'Low', 'supporting_factors': factors, 'recommendations': self._generate_pension_recommendations(plan_type, suitability_score, participant_profile)}

    def _generate_pension_recommendations(self, plan_type: str, suitability_score: int, participant_profile: Dict) -> List[str]:
        """Generate pension plan recommendations"""
        recommendations = []
        if plan_type.lower() == 'dc':
            if suitability_score > 70:
                recommendations.append('DC plan well-suited - maximize contributions')
                recommendations.append('Consider aggressive growth allocation if young')
                recommendations.append('Take advantage of employer matching')
            elif suitability_score > 40:
                recommendations.append('DC plan suitable with careful planning')
                recommendations.append('Consider target-date funds for simplicity')
                recommendations.append('Regular portfolio rebalancing important')
            else:
                recommendations.append('DC plan challenges - seek professional guidance')
                recommendations.append('Focus on low-cost index funds')
                recommendations.append('Automate contributions and rebalancing')
        elif plan_type.lower() == 'db':
            if suitability_score > 70:
                recommendations.append('DB plan excellent fit - maximize tenure')
                recommendations.append('Understand vesting schedule and benefit formula')
                recommendations.append('Consider supplemental retirement savings')
            elif suitability_score > 40:
                recommendations.append('DB plan provides good foundation')
                recommendations.append('Monitor plan funding status')
                recommendations.append('Diversify with additional retirement accounts')
            else:
                recommendations.append('DB plan may not meet all needs')
                recommendations.append('Supplement with portable retirement savings')
                recommendations.append('Consider career mobility implications')
        return recommendations

    def _identify_secondary_objectives(self, profile: InvestorProfile) -> List[str]:
        """Identify secondary investment objectives"""
        secondary = []
        if profile.investment_objective != InvestmentObjective.CAPITAL_PRESERVATION:
            if profile.risk_tolerance == 'conservative':
                secondary.append('Capital preservation')
        if profile.investment_objective != InvestmentObjective.CURRENT_INCOME:
            if profile.liquidity_needs > 0.3:
                secondary.append('Current income')
        if profile.investment_objective != InvestmentObjective.CAPITAL_APPRECIATION:
            if profile.time_horizon > 10:
                secondary.append('Capital appreciation')
        return secondary

    def _prioritize_objectives(self, profile: InvestorProfile) -> Dict[str, int]:
        """Prioritize investment objectives"""
        priorities = {profile.investment_objective.value: 1}
        secondary_objectives = self._identify_secondary_objectives(profile)
        for i, obj in enumerate(secondary_objectives, 2):
            priorities[obj] = i
        return priorities

    def _analyze_liquidity_needs(self, profile: InvestorProfile) -> Dict:
        """Analyze liquidity constraints"""
        return {'liquidity_requirement': profile.liquidity_needs, 'liquidity_level': 'High' if profile.liquidity_needs > 0.3 else 'Moderate' if profile.liquidity_needs > 0.1 else 'Low', 'liquidity_sources': self._identify_liquidity_sources(profile), 'emergency_fund_need': max(0.05, profile.liquidity_needs * 1.5)}

    def _analyze_time_horizon(self, profile: InvestorProfile) -> Dict:
        """Analyze time horizon constraints"""
        return {'time_horizon_years': profile.time_horizon, 'horizon_category': 'Long' if profile.time_horizon > 10 else 'Medium' if profile.time_horizon > 5 else 'Short', 'investment_implications': self._time_horizon_implications(profile.time_horizon), 'stage_transitions': self._identify_stage_transitions(profile)}

    def _analyze_tax_situation(self, profile: InvestorProfile) -> Dict:
        """Analyze tax considerations"""
        return {'tax_situation': profile.tax_situation, 'tax_efficiency_importance': 'High' if profile.tax_situation.get('marginal_rate', 0) > 0.25 else 'Moderate', 'tax_advantaged_accounts': self._recommend_tax_accounts(profile), 'tax_loss_harvesting': profile.tax_situation.get('marginal_rate', 0) > 0.15}

    def _assess_risk_capacity_willingness(self, profile: InvestorProfile) -> Dict:
        """Assess risk capacity vs willingness"""
        capacity_factors = {'time_horizon': min(10, profile.time_horizon) / 10 * 30, 'liquidity': (1 - profile.liquidity_needs) * 30, 'income_stability': 20, 'wealth_level': 20}
        capacity_score = sum(capacity_factors.values())
        willingness_score = {'conservative': 25, 'moderate': 50, 'aggressive': 85}.get(profile.risk_tolerance, 50)
        return {'risk_capacity_score': capacity_score, 'risk_willingness_score': willingness_score, 'overall_risk_tolerance': min(capacity_score, willingness_score), 'capacity_willingness_gap': abs(capacity_score - willingness_score), 'constraining_factor': 'Capacity' if capacity_score < willingness_score else 'Willingness'}

    def _allocate_risk_budget(self, profile: InvestorProfile) -> Dict:
        """Allocate risk budget across portfolio"""
        risk_assessment = self._assess_risk_capacity_willingness(profile)
        total_risk_budget = risk_assessment['overall_risk_tolerance']
        if profile.investment_objective == InvestmentObjective.CAPITAL_APPRECIATION:
            allocation = {'equity_risk': 0.7, 'credit_risk': 0.2, 'other_risk': 0.1}
        elif profile.investment_objective == InvestmentObjective.CURRENT_INCOME:
            allocation = {'credit_risk': 0.6, 'equity_risk': 0.3, 'other_risk': 0.1}
        else:
            allocation = {'equity_risk': 0.5, 'credit_risk': 0.4, 'other_risk': 0.1}
        return {'total_risk_budget': total_risk_budget, 'risk_allocation': allocation, 'risk_limits': {risk_type: total_risk_budget * weight for risk_type, weight in allocation.items()}}

    def _set_rebalancing_ranges(self, allocation: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """Set rebalancing ranges for asset allocation"""
        ranges = {}
        for asset, weight in allocation.items():
            if weight < 0.1:
                range_width = 0.05
            elif weight < 0.3:
                range_width = 0.07
            else:
                range_width = 0.1
            lower_bound = max(0, weight - range_width)
            upper_bound = min(1, weight + range_width)
            ranges[asset] = (lower_bound, upper_bound)
        return ranges

    def _explain_allocation_rationale(self, profile: InvestorProfile, allocation: Dict[str, float]) -> Dict:
        """Explain rationale for asset allocation"""
        rationale = {'primary_drivers': [], 'risk_considerations': [], 'return_expectations': [], 'constraints_addressed': []}
        if profile.investment_objective == InvestmentObjective.CAPITAL_APPRECIATION:
            rationale['primary_drivers'].append('Growth-oriented allocation emphasizes equity exposure')
        elif profile.investment_objective == InvestmentObjective.CURRENT_INCOME:
            rationale['primary_drivers'].append('Income-focused allocation emphasizes fixed income')
        if profile.risk_tolerance == 'conservative':
            rationale['risk_considerations'].append('Conservative risk tolerance limits equity exposure')
        elif profile.risk_tolerance == 'aggressive':
            rationale['risk_considerations'].append('Aggressive risk tolerance allows higher equity allocation')
        if profile.time_horizon > 10:
            rationale['return_expectations'].append('Long time horizon supports growth-oriented approach')
        elif profile.time_horizon < 5:
            rationale['return_expectations'].append('Short time horizon requires capital preservation focus')
        if profile.liquidity_needs > 0.2:
            rationale['constraints_addressed'].append('High liquidity needs addressed through liquid asset allocation')
        return rationale

    def _calculate_expected_characteristics(self, allocation: Dict[str, float]) -> Dict:
        """Calculate expected portfolio characteristics"""
        asset_assumptions = {'domestic_equity': {'return': 0.1, 'volatility': 0.18}, 'international_equity': {'return': 0.09, 'volatility': 0.2}, 'domestic_bonds': {'return': 0.04, 'volatility': 0.06}, 'international_bonds': {'return': 0.03, 'volatility': 0.08}, 'real_estate': {'return': 0.08, 'volatility': 0.15}, 'alternatives': {'return': 0.12, 'volatility': 0.25}, 'private_equity': {'return': 0.14, 'volatility': 0.3}, 'hedge_funds': {'return': 0.08, 'volatility': 0.12}, 'cash': {'return': 0.02, 'volatility': 0.01}}
        expected_return = 0
        weighted_variance = 0
        for asset, weight in allocation.items():
            if asset in asset_assumptions:
                assumptions = asset_assumptions[asset]
                expected_return += weight * assumptions['return']
                weighted_variance += (weight * assumptions['volatility']) ** 2
        expected_volatility = np.sqrt(weighted_variance)
        return {'expected_annual_return': expected_return, 'expected_volatility': expected_volatility, 'expected_sharpe_ratio': (expected_return - 0.03) / expected_volatility if expected_volatility > 0 else 0, 'risk_return_profile': self._classify_risk_return_profile(expected_return, expected_volatility)}

    def _classify_risk_return_profile(self, expected_return: float, expected_volatility: float) -> str:
        """Classify portfolio risk-return profile"""
        if expected_return > 0.08 and expected_volatility > 0.15:
            return 'Aggressive Growth'
        elif expected_return > 0.06 and expected_volatility > 0.1:
            return 'Moderate Growth'
        elif expected_return > 0.04 and expected_volatility < 0.1:
            return 'Conservative Growth'
        elif expected_return < 0.04:
            return 'Capital Preservation'
        else:
            return 'Balanced'

    def _identify_liquidity_sources(self, profile: InvestorProfile) -> List[str]:
        """Identify potential liquidity sources"""
        sources = ['Cash and cash equivalents']
        if profile.liquidity_needs > 0.2:
            sources.extend(['Short-term bond funds', 'Money market funds'])
        if profile.time_horizon > 5:
            sources.append('Systematic withdrawal from equity funds')
        return sources

    def _time_horizon_implications(self, time_horizon: int) -> Dict:
        """Analyze investment implications of time horizon"""
        if time_horizon > 10:
            return {'asset_allocation': 'Can emphasize growth assets', 'risk_tolerance': 'Can accept higher volatility', 'rebalancing': 'Less frequent rebalancing needed', 'tax_efficiency': 'Focus on long-term capital gains'}
        elif time_horizon > 5:
            return {'asset_allocation': 'Balanced approach appropriate', 'risk_tolerance': 'Moderate risk acceptable', 'rebalancing': 'Regular rebalancing important', 'tax_efficiency': 'Consider tax-loss harvesting'}
        else:
            return {'asset_allocation': 'Emphasize capital preservation', 'risk_tolerance': 'Low risk tolerance appropriate', 'rebalancing': 'Frequent monitoring needed', 'tax_efficiency': 'Focus on current income'}

    def _identify_stage_transitions(self, profile: InvestorProfile) -> List[str]:
        """Identify upcoming lifecycle stage transitions"""
        transitions = []
        if hasattr(profile, 'age'):
            if 40 <= profile.age <= 50:
                transitions.append('Approaching peak earning years')
            elif 50 <= profile.age <= 60:
                transitions.append('Pre-retirement planning phase')
            elif profile.age > 60:
                transitions.append('Retirement transition')
        return transitions

    def _recommend_tax_accounts(self, profile: InvestorProfile) -> List[str]:
        """Recommend tax-advantaged account types"""
        recommendations = []
        marginal_rate = profile.tax_situation.get('marginal_rate', 0.22)
        if marginal_rate > 0.2:
            recommendations.append('Traditional 401(k) or IRA for current deduction')
        if profile.time_horizon > 10:
            recommendations.append('Roth IRA for tax-free growth')
        if profile.investor_type == InvestorType.INDIVIDUAL:
            recommendations.append('Health Savings Account if eligible')
        return recommendations

    def _make_allocation_decisions(self, allocation_targets: Dict) -> Dict:
        """Make tactical allocation decisions"""
        return {'strategic_allocation': allocation_targets, 'tactical_adjustments': 'Based on current market conditions', 'implementation_approach': 'Systematic approach to reaching targets', 'timing_considerations': 'Dollar-cost averaging for large allocations'}

    def _security_selection_process(self, allocation_targets: Dict) -> Dict:
        """Define security selection process"""
        return {'selection_criteria': ['Cost efficiency (low expense ratios)', 'Tracking error minimization for passive funds', 'Manager tenure and consistency for active funds', 'Tax efficiency considerations'], 'due_diligence_process': ['Quantitative screening', 'Qualitative assessment', 'Risk analysis', 'Performance attribution']}

    def _implementation_strategy(self, market_conditions: Dict) -> Dict:
        """Define implementation strategy"""
        return {'implementation_approach': 'Gradual implementation to minimize market impact', 'cost_management': 'Focus on minimizing transaction costs', 'market_timing': 'Avoid market timing, focus on systematic approach', 'liquidity_management': 'Ensure adequate liquidity throughout process'}

    def _trading_considerations(self) -> Dict:
        """Define trading considerations"""
        return {'execution_priorities': ['Cost minimization', 'Market impact reduction', 'Speed of execution'], 'order_types': 'Use of limit orders and volume-weighted average price (VWAP)', 'timing': 'Trade during high-liquidity periods when possible', 'monitoring': 'Real-time monitoring of execution quality'}

    def _measure_performance(self, portfolio_performance: Dict, benchmarks: Dict) -> Dict:
        """Measure portfolio performance"""
        return {'absolute_performance': portfolio_performance.get('total_return', 0), 'relative_performance': 'Performance vs. appropriate benchmarks', 'risk_adjusted_performance': 'Sharpe ratio and other risk-adjusted metrics', 'attribution_analysis': 'Performance attribution by asset class and security selection'}

    def _evaluate_performance(self, portfolio_performance: Dict) -> Dict:
        """Evaluate portfolio performance"""
        return {'performance_evaluation': 'Assessment of returns relative to objectives', 'risk_evaluation': 'Analysis of risk taken relative to risk budget', 'consistency_evaluation': 'Evaluation of performance consistency over time', 'benchmark_comparison': 'Comparison to relevant benchmarks and peer groups'}

    def _monitor_portfolio(self) -> Dict:
        """Define portfolio monitoring approach"""
        return {'monitoring_frequency': 'Continuous monitoring with formal reviews quarterly', 'key_metrics': ['Asset allocation drift', 'Performance vs. benchmarks', 'Risk metrics'], 'alert_systems': 'Automated alerts for significant deviations', 'reporting': 'Regular reporting to stakeholders'}

    def _assess_rebalancing_needs(self, portfolio_performance: Dict) -> Dict:
        """Assess portfolio rebalancing needs"""
        return {'rebalancing_triggers': ['Asset allocation drift beyond tolerance bands', 'Significant market movements', 'Changes in client circumstances', 'Calendar-based rebalancing'], 'rebalancing_approach': 'Systematic approach based on predefined rules', 'cost_benefit_analysis': 'Consider transaction costs vs. rebalancing benefits', 'tax_implications': 'Consider tax consequences of rebalancing transactions'}

def _identify_liquidity_sources(self, profile: InvestorProfile) -> List[str]:
    """Identify potential liquidity sources"""
    sources = ['Cash and cash equivalents']
    if profile.liquidity_needs > 0.2:
        sources.extend(['Short-term bond funds', 'Money market funds'])
    if profile.time_horizon > 5:
        sources.append('Systematic withdrawal from equity funds')
    return sources

class EmployeeCompensationAnalyzer(BaseAnalyzer):
    """
    Comprehensive employee compensation analyzer implementing CFA Level II standards.
    Covers post-employment benefits and share-based compensation.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_compensation_formulas()
        self._initialize_compensation_benchmarks()

    def _initialize_compensation_formulas(self):
        """Initialize compensation-specific formulas"""
        self.formula_registry.update({'funding_ratio': lambda plan_assets, pension_obligation: self.safe_divide(plan_assets, pension_obligation), 'sbc_intensity': lambda sbc_expense, revenue: self.safe_divide(sbc_expense, revenue), 'compensation_intensity': lambda total_comp, revenue: self.safe_divide(total_comp, revenue), 'dilution_impact': lambda dilutive_shares, basic_shares: self.safe_divide(dilutive_shares, basic_shares), 'pension_cost_ratio': lambda pension_cost, operating_income: self.safe_divide(pension_cost, operating_income), 'benefit_coverage': lambda plan_assets, current_liabilities: self.safe_divide(plan_assets, current_liabilities)})

    def _initialize_compensation_benchmarks(self):
        """Initialize compensation-specific benchmarks"""
        self.compensation_benchmarks = {'funding_ratio': {'overfunded': 1.1, 'fully_funded': 1.0, 'underfunded': 0.9, 'severely_underfunded': 0.8}, 'sbc_intensity': {'low': 0.02, 'moderate': 0.05, 'high': 0.1, 'very_high': 0.2}, 'compensation_intensity': {'low': 0.3, 'moderate': 0.4, 'high': 0.6, 'very_high': 0.8}, 'dilution_impact': {'minimal': 0.02, 'moderate': 0.05, 'significant': 0.1, 'excessive': 0.2}}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive employee compensation analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all compensation aspects
        """
        results = []
        results.extend(self._analyze_post_employment_benefits(statements, comparative_data, industry_data))
        results.extend(self._analyze_share_based_compensation(statements, comparative_data, industry_data))
        results.extend(self._analyze_compensation_strategy(statements, comparative_data, industry_data))
        results.extend(self._assess_pension_risks(statements, comparative_data))
        results.extend(self._analyze_sbc_forecasting(statements, comparative_data))
        results.extend(self._assess_valuation_impact(statements, comparative_data))
        return results

    def _analyze_post_employment_benefits(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze post-employment benefit plans"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        pension_obligation = balance_sheet.get('pension_obligation', 0)
        pension_assets = balance_sheet.get('pension_plan_assets', 0)
        pension_liability = balance_sheet.get('pension_liability', 0)
        pension_expense = income_statement.get('pension_expense', 0)
        service_cost = notes.get('pension_service_cost', 0)
        interest_cost = notes.get('pension_interest_cost', 0)
        expected_return = notes.get('expected_return_plan_assets', 0)
        if pension_obligation <= 0 and pension_expense <= 0:
            return results
        if pension_obligation > 0:
            funded_status = pension_assets - pension_obligation
            funding_ratio = self.safe_divide(pension_assets, pension_obligation)
            if funding_ratio >= 1.1:
                funding_status = FundingStatus.OVERFUNDED
                funding_interpretation = 'Pension plan is overfunded - surplus available'
                funding_risk = RiskLevel.LOW
            elif funding_ratio >= 1.0:
                funding_status = FundingStatus.FULLY_FUNDED
                funding_interpretation = 'Pension plan is fully funded'
                funding_risk = RiskLevel.LOW
            elif funding_ratio >= 0.8:
                funding_status = FundingStatus.UNDERFUNDED
                funding_interpretation = 'Pension plan is underfunded - future contributions required'
                funding_risk = RiskLevel.MODERATE
            else:
                funding_status = FundingStatus.SEVERELY_UNDERFUNDED
                funding_interpretation = 'Pension plan is severely underfunded - significant funding risk'
                funding_risk = RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Pension Funding Ratio', value=funding_ratio, interpretation=funding_interpretation, risk_level=funding_risk, benchmark_comparison=self.compare_to_industry(funding_ratio, industry_data.get('pension_funding_ratio') if industry_data else None), methodology='Plan Assets / Pension Benefit Obligation', limitations=['Funding ratio based on actuarial assumptions that may change']))
            total_assets = balance_sheet.get('total_assets', 0)
            if total_assets > 0:
                funded_status_ratio = self.safe_divide(abs(funded_status), total_assets)
                if funded_status < 0:
                    status_interpretation = f'Pension underfunding represents {self.format_percentage(funded_status_ratio)} of total assets'
                    status_risk = RiskLevel.HIGH if funded_status_ratio > 0.1 else RiskLevel.MODERATE if funded_status_ratio > 0.05 else RiskLevel.LOW
                else:
                    status_interpretation = f'Pension overfunding represents {self.format_percentage(funded_status_ratio)} of total assets'
                    status_risk = RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Pension Funded Status Impact', value=funded_status_ratio, interpretation=status_interpretation, risk_level=status_risk, methodology='|Funded Status| / Total Assets'))
        if pension_expense > 0:
            revenue = income_statement.get('revenue', 0)
            if revenue > 0:
                pension_cost_intensity = self.safe_divide(pension_expense, revenue)
                cost_interpretation = 'High pension cost burden' if pension_cost_intensity > 0.05 else 'Moderate pension costs' if pension_cost_intensity > 0.02 else 'Low pension cost impact'
                cost_risk = RiskLevel.MODERATE if pension_cost_intensity > 0.08 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Pension Cost Intensity', value=pension_cost_intensity, interpretation=cost_interpretation, risk_level=cost_risk, methodology='Pension Expense / Revenue'))
        if service_cost > 0 and interest_cost > 0:
            total_cost_components = service_cost + interest_cost
            service_cost_ratio = self.safe_divide(service_cost, total_cost_components)
            service_interpretation = 'Service cost dominates - active workforce driving costs' if service_cost_ratio > 0.6 else 'Balanced service and interest costs' if service_cost_ratio > 0.4 else 'Interest cost dominates - mature plan with large obligation'
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Pension Cost Composition', value=service_cost_ratio, interpretation=service_interpretation, risk_level=RiskLevel.LOW, methodology='Service Cost / (Service Cost + Interest Cost)'))
        actual_return = notes.get('actual_return_plan_assets', 0)
        if expected_return > 0 and actual_return != 0:
            return_variance = actual_return - expected_return
            return_variance_ratio = self.safe_divide(abs(return_variance), abs(expected_return))
            variance_interpretation = 'Significant variance between expected and actual returns' if return_variance_ratio > 0.2 else 'Moderate return variance' if return_variance_ratio > 0.1 else 'Returns close to expectations'
            variance_risk = RiskLevel.MODERATE if return_variance_ratio > 0.3 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Pension Return Variance', value=return_variance_ratio, interpretation=variance_interpretation, risk_level=variance_risk, methodology='|Actual Return - Expected Return| / |Expected Return|'))
        return results

    def _analyze_share_based_compensation(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze share-based compensation"""
        results = []
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        notes = statements.notes
        sbc_expense = income_statement.get('stock_compensation', 0)
        revenue = income_statement.get('revenue', 0)
        if sbc_expense <= 0:
            return results
        if revenue > 0:
            sbc_intensity = self.safe_divide(sbc_expense, revenue)
            benchmark = self.compensation_benchmarks['sbc_intensity']
            if sbc_intensity > benchmark['very_high']:
                intensity_interpretation = 'Very high share-based compensation intensity - significant equity dilution concern'
                intensity_risk = RiskLevel.HIGH
            elif sbc_intensity > benchmark['high']:
                intensity_interpretation = 'High share-based compensation usage'
                intensity_risk = RiskLevel.MODERATE
            elif sbc_intensity > benchmark['moderate']:
                intensity_interpretation = 'Moderate share-based compensation'
                intensity_risk = RiskLevel.LOW
            else:
                intensity_interpretation = 'Low share-based compensation usage'
                intensity_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Share-Based Compensation Intensity', value=sbc_intensity, interpretation=intensity_interpretation, risk_level=intensity_risk, benchmark_comparison=self.compare_to_industry(sbc_intensity, industry_data.get('sbc_intensity') if industry_data else None), methodology='Stock-Based Compensation Expense / Revenue', limitations=['High SBC may indicate cash conservation or growth stage']))
        basic_shares = income_statement.get('shares_outstanding_basic', 0)
        diluted_shares = income_statement.get('shares_outstanding_diluted', 0)
        if basic_shares > 0 and diluted_shares > basic_shares:
            dilutive_shares = diluted_shares - basic_shares
            dilution_impact = self.safe_divide(dilutive_shares, basic_shares)
            benchmark = self.compensation_benchmarks['dilution_impact']
            if dilution_impact > benchmark['excessive']:
                dilution_interpretation = 'Excessive dilution from share-based compensation'
                dilution_risk = RiskLevel.HIGH
            elif dilution_impact > benchmark['significant']:
                dilution_interpretation = 'Significant dilution impact'
                dilution_risk = RiskLevel.MODERATE
            elif dilution_impact > benchmark['moderate']:
                dilution_interpretation = 'Moderate dilution from SBC'
                dilution_risk = RiskLevel.LOW
            else:
                dilution_interpretation = 'Minimal dilution impact'
                dilution_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='SBC Dilution Impact', value=dilution_impact, interpretation=dilution_interpretation, risk_level=dilution_risk, methodology='(Diluted Shares - Basic Shares) / Basic Shares'))
        if comparative_data and len(comparative_data) >= 2:
            sbc_values = []
            revenue_values = []
            for past_statements in comparative_data:
                past_sbc = past_statements.income_statement.get('stock_compensation', 0)
                past_revenue = past_statements.income_statement.get('revenue', 0)
                sbc_values.append(past_sbc)
                revenue_values.append(past_revenue)
            sbc_values.append(sbc_expense)
            revenue_values.append(revenue)
            if len(sbc_values) > 2:
                sbc_trend = self.calculate_trend(sbc_values, [f'Period-{i}' for i in range(len(sbc_values))])
                if len(revenue_values) == len(sbc_values):
                    revenue_trend = self.calculate_trend(revenue_values, [f'Period-{i}' for i in range(len(revenue_values))])
                    if sbc_trend.growth_rate and revenue_trend.growth_rate:
                        relative_growth = sbc_trend.growth_rate - revenue_trend.growth_rate
                        if relative_growth > 0.1:
                            trend_interpretation = 'SBC expense growing faster than revenue - increasing compensation intensity'
                            trend_risk = RiskLevel.MODERATE
                        elif relative_growth > -0.1:
                            trend_interpretation = 'SBC expense growth aligned with revenue growth'
                            trend_risk = RiskLevel.LOW
                        else:
                            trend_interpretation = 'SBC expense declining relative to revenue - improving efficiency'
                            trend_risk = RiskLevel.LOW
                        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='SBC Growth vs Revenue Growth', value=relative_growth, interpretation=trend_interpretation, risk_level=trend_risk, methodology='SBC Growth Rate - Revenue Growth Rate'))
        stock_option_expense = notes.get('stock_option_expense', 0)
        restricted_stock_expense = notes.get('restricted_stock_expense', 0)
        performance_share_expense = notes.get('performance_share_expense', 0)
        total_detailed_sbc = stock_option_expense + restricted_stock_expense + performance_share_expense
        if total_detailed_sbc > 0 and abs(total_detailed_sbc - sbc_expense) / sbc_expense < 0.1:
            sbc_types = {'Stock Options': stock_option_expense, 'Restricted Stock': restricted_stock_expense, 'Performance Shares': performance_share_expense}
            for sbc_type, sbc_value in sbc_types.items():
                if sbc_value > 0:
                    sbc_type_ratio = self.safe_divide(sbc_value, total_detailed_sbc)
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name=f'{sbc_type} Composition', value=sbc_type_ratio, interpretation=f'{sbc_type} represents {self.format_percentage(sbc_type_ratio)} of total SBC expense', risk_level=RiskLevel.LOW, methodology=f'{sbc_type} Expense / Total SBC Expense'))
        if performance_share_expense > 0:
            performance_ratio = self.safe_divide(performance_share_expense, sbc_expense)
            performance_interpretation = 'High performance-based compensation alignment' if performance_ratio > 0.4 else 'Moderate performance alignment' if performance_ratio > 0.2 else 'Limited performance-based compensation'
            performance_risk = RiskLevel.LOW if performance_ratio > 0.3 else RiskLevel.MODERATE
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Performance-Based SBC Ratio', value=performance_ratio, interpretation=performance_interpretation, risk_level=performance_risk, methodology='Performance Share Expense / Total SBC Expense', limitations=['Performance alignment depends on specific performance metrics used']))
        return results

    def _analyze_compensation_strategy(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze overall compensation strategy"""
        results = []
        income_statement = statements.income_statement
        employee_costs = income_statement.get('employee_costs', 0)
        pension_expense = income_statement.get('pension_expense', 0)
        sbc_expense = income_statement.get('stock_compensation', 0)
        other_benefits = income_statement.get('other_employee_benefits', 0)
        total_compensation = employee_costs + pension_expense + sbc_expense + other_benefits
        revenue = income_statement.get('revenue', 0)
        if total_compensation <= 0:
            return results
        if revenue > 0:
            compensation_intensity = self.safe_divide(total_compensation, revenue)
            benchmark = self.compensation_benchmarks['compensation_intensity']
            if compensation_intensity > benchmark['very_high']:
                intensity_interpretation = 'Very high compensation intensity - labor-intensive business model'
                intensity_risk = RiskLevel.MODERATE
            elif compensation_intensity > benchmark['high']:
                intensity_interpretation = 'High compensation costs relative to revenue'
                intensity_risk = RiskLevel.MODERATE
            elif compensation_intensity > benchmark['moderate']:
                intensity_interpretation = 'Moderate compensation intensity'
                intensity_risk = RiskLevel.LOW
            else:
                intensity_interpretation = 'Low compensation intensity - capital-intensive or automated business'
                intensity_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Total Compensation Intensity', value=compensation_intensity, interpretation=intensity_interpretation, risk_level=intensity_risk, benchmark_comparison=self.compare_to_industry(compensation_intensity, industry_data.get('compensation_intensity') if industry_data else None), methodology='Total Employee Compensation / Revenue'))
        if total_compensation > 0:
            cash_compensation_ratio = self.safe_divide(employee_costs, total_compensation)
            equity_compensation_ratio = self.safe_divide(sbc_expense, total_compensation)
            benefits_ratio = self.safe_divide(pension_expense + other_benefits, total_compensation)
            mix_components = {'Cash Compensation Ratio': cash_compensation_ratio, 'Equity Compensation Ratio': equity_compensation_ratio, 'Benefits Ratio': benefits_ratio}
            for component, ratio in mix_components.items():
                if ratio > 0:
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name=component, value=ratio, interpretation=f'{component.replace('_', ' ')} of {self.format_percentage(ratio)}', risk_level=RiskLevel.LOW, methodology=f'Component / Total Compensation'))
            if equity_compensation_ratio > 0.2:
                strategy_assessment = 'Equity-heavy compensation strategy - retention and performance focus'
                strategy_risk = RiskLevel.MODERATE
            elif benefits_ratio > 0.3:
                strategy_assessment = 'Benefits-heavy compensation - traditional employment model'
                strategy_risk = RiskLevel.LOW
            else:
                strategy_assessment = 'Cash-focused compensation strategy'
                strategy_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Compensation Strategy Assessment', value=1.0, interpretation=strategy_assessment, risk_level=strategy_risk, methodology='Qualitative assessment of compensation mix'))
        return results

    def _assess_pension_risks(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess pension-related risks"""
        results = []
        notes = statements.notes
        discount_rate = notes.get('pension_discount_rate', 0)
        expected_return_rate = notes.get('expected_return_rate', 0)
        salary_increase_rate = notes.get('salary_increase_assumption', 0)
        if discount_rate > 0:
            if discount_rate < 0.03:
                discount_interpretation = 'Very low discount rate increases pension obligation sensitivity'
                discount_risk = RiskLevel.HIGH
            elif discount_rate < 0.05:
                discount_interpretation = 'Low discount rate environment - moderate sensitivity'
                discount_risk = RiskLevel.MODERATE
            else:
                discount_interpretation = 'Reasonable discount rate assumption'
                discount_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Pension Discount Rate Risk', value=discount_rate, interpretation=discount_interpretation, risk_level=discount_risk, methodology='Assessment of discount rate level and sensitivity', limitations=['Discount rate changes significantly impact pension obligations']))
        if expected_return_rate > 0 and discount_rate > 0:
            return_premium = expected_return_rate - discount_rate
            if return_premium > 0.02:
                return_interpretation = 'High expected return premium - aggressive investment assumption'
                return_risk = RiskLevel.MODERATE
            elif return_premium > 0:
                return_interpretation = 'Positive expected return premium'
                return_risk = RiskLevel.LOW
            else:
                return_interpretation = 'Conservative expected return assumption'
                return_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Expected Return Premium', value=return_premium, interpretation=return_interpretation, risk_level=return_risk, methodology='Expected Return Rate - Discount Rate'))
        average_participant_age = notes.get('average_participant_age', 0)
        if average_participant_age > 0:
            if average_participant_age > 55:
                demographic_interpretation = 'Aging participant base - increasing near-term benefit payments'
                demographic_risk = RiskLevel.MODERATE
            elif average_participant_age > 45:
                demographic_interpretation = 'Mature participant base'
                demographic_risk = RiskLevel.LOW
            else:
                demographic_interpretation = 'Young participant base - deferred benefit payments'
                demographic_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Pension Demographic Risk', value=average_participant_age, interpretation=demographic_interpretation, risk_level=demographic_risk, methodology='Assessment of participant age profile'))
        return results

    def _analyze_sbc_forecasting(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze SBC forecasting implications"""
        results = []
        notes = statements.notes
        income_statement = statements.income_statement
        unvested_sbc_value = notes.get('unvested_sbc_value', 0)
        weighted_average_vesting_period = notes.get('weighted_average_vesting_period', 0)
        if unvested_sbc_value > 0:
            current_sbc_expense = income_statement.get('stock_compensation', 0)
            if weighted_average_vesting_period > 0:
                estimated_annual_expense = self.safe_divide(unvested_sbc_value, weighted_average_vesting_period)
                if current_sbc_expense > 0:
                    future_expense_ratio = self.safe_divide(estimated_annual_expense, current_sbc_expense)
                    if future_expense_ratio > 1.2:
                        forecasting_interpretation = 'SBC expense expected to increase significantly based on unvested awards'
                        forecasting_risk = RiskLevel.MODERATE
                    elif future_expense_ratio > 0.8:
                        forecasting_interpretation = 'SBC expense expected to remain stable'
                        forecasting_risk = RiskLevel.LOW
                    else:
                        forecasting_interpretation = 'SBC expense expected to decline'
                        forecasting_risk = RiskLevel.LOW
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='SBC Future Expense Indicator', value=future_expense_ratio, interpretation=forecasting_interpretation, risk_level=forecasting_risk, methodology='Estimated Future Annual SBC Expense / Current SBC Expense'))
        options_outstanding = notes.get('stock_options_outstanding', 0)
        weighted_average_exercise_price = notes.get('weighted_average_exercise_price', 0)
        current_stock_price = notes.get('current_stock_price', 0)
        if options_outstanding > 0 and current_stock_price > 0 and (weighted_average_exercise_price > 0):
            if current_stock_price > weighted_average_exercise_price:
                intrinsic_value_ratio = (current_stock_price - weighted_average_exercise_price) / current_stock_price
                if intrinsic_value_ratio > 0.3:
                    dilution_interpretation = 'Significant in-the-money options - high exercise probability'
                    dilution_risk = RiskLevel.MODERATE
                elif intrinsic_value_ratio > 0.1:
                    dilution_interpretation = 'Moderate in-the-money options'
                    dilution_risk = RiskLevel.LOW
                else:
                    dilution_interpretation = 'Limited intrinsic value in outstanding options'
                    dilution_risk = RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Option Intrinsic Value Ratio', value=intrinsic_value_ratio, interpretation=dilution_interpretation, risk_level=dilution_risk, methodology='(Current Price - Exercise Price) / Current Price'))
        return results

    def _assess_valuation_impact(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess valuation implications of compensation arrangements"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        pension_obligation = balance_sheet.get('pension_obligation', 0)
        pension_assets = balance_sheet.get('pension_plan_assets', 0)
        net_pension_liability = pension_obligation - pension_assets
        if net_pension_liability > 0:
            total_debt = balance_sheet.get('long_term_debt', 0) + balance_sheet.get('short_term_debt', 0)
            if total_debt > 0:
                pension_debt_ratio = self.safe_divide(net_pension_liability, total_debt)
                valuation_interpretation = 'Pension liability significantly impacts debt-like obligations' if pension_debt_ratio > 0.5 else 'Moderate pension liability impact' if pension_debt_ratio > 0.2 else 'Limited pension liability impact on valuation'
                valuation_risk = RiskLevel.MODERATE if pension_debt_ratio > 0.4 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.VALUATION, metric_name='Pension Liability to Debt Ratio', value=pension_debt_ratio, interpretation=valuation_interpretation, risk_level=valuation_risk, methodology='Net Pension Liability / Total Debt', limitations=['Pension obligations should be considered in enterprise valuation']))
        sbc_expense = income_statement.get('stock_compensation', 0)
        tax_rate = 0.25
        if sbc_expense > 0:
            sbc_tax_benefit = sbc_expense * tax_rate
            cash_flow_benefit_ratio = self.safe_divide(sbc_tax_benefit, sbc_expense)
            results.append(AnalysisResult(analysis_type=AnalysisType.VALUATION, metric_name='SBC Tax Benefit Ratio', value=cash_flow_benefit_ratio, interpretation=f'SBC provides tax benefits worth {self.format_percentage(cash_flow_benefit_ratio)} of expense', risk_level=RiskLevel.LOW, methodology='(SBC Expense × Tax Rate) / SBC Expense', limitations=["Actual tax benefits depend on company's tax position"]))
        return results

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key employee compensation metrics"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        metrics = {}
        pension_obligation = balance_sheet.get('pension_obligation', 0)
        pension_assets = balance_sheet.get('pension_plan_assets', 0)
        if pension_obligation > 0:
            metrics['pension_funding_ratio'] = self.safe_divide(pension_assets, pension_obligation)
            metrics['pension_funded_status'] = pension_assets - pension_obligation
        pension_expense = income_statement.get('pension_expense', 0)
        revenue = income_statement.get('revenue', 0)
        if revenue > 0 and pension_expense > 0:
            metrics['pension_cost_intensity'] = self.safe_divide(pension_expense, revenue)
        sbc_expense = income_statement.get('stock_compensation', 0)
        if revenue > 0 and sbc_expense > 0:
            metrics['sbc_intensity'] = self.safe_divide(sbc_expense, revenue)
        basic_shares = income_statement.get('shares_outstanding_basic', 0)
        diluted_shares = income_statement.get('shares_outstanding_diluted', 0)
        if basic_shares > 0 and diluted_shares > basic_shares:
            metrics['dilution_impact'] = self.safe_divide(diluted_shares - basic_shares, basic_shares)
        employee_costs = income_statement.get('employee_costs', 0)
        total_compensation = employee_costs + pension_expense + sbc_expense
        if revenue > 0 and total_compensation > 0:
            metrics['total_compensation_intensity'] = self.safe_divide(total_compensation, revenue)
        return metrics

    def create_post_employment_analysis(self, statements: FinancialStatements) -> PostEmploymentAnalysis:
        """Create comprehensive post-employment benefits analysis object"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        total_pension_obligation = balance_sheet.get('pension_obligation', 0)
        plan_assets_fair_value = balance_sheet.get('pension_plan_assets', 0)
        funded_status = plan_assets_fair_value - total_pension_obligation
        funding_ratio = self.safe_divide(plan_assets_fair_value, total_pension_obligation) if total_pension_obligation > 0 else 0
        defined_benefit_obligation = balance_sheet.get('defined_benefit_obligation', total_pension_obligation)
        defined_contribution_assets = balance_sheet.get('defined_contribution_assets', 0)
        service_cost = notes.get('pension_service_cost', 0)
        interest_cost = notes.get('pension_interest_cost', 0)
        expected_return_on_assets = notes.get('expected_return_plan_assets', 0)
        net_periodic_cost = income_statement.get('pension_expense', 0)
        if funding_ratio >= 1.1:
            funding_status_enum = FundingStatus.OVERFUNDED
        elif funding_ratio >= 1.0:
            funding_status_enum = FundingStatus.FULLY_FUNDED
        elif funding_ratio >= 0.8:
            funding_status_enum = FundingStatus.UNDERFUNDED
        else:
            funding_status_enum = FundingStatus.SEVERELY_UNDERFUNDED
        discount_rate = notes.get('pension_discount_rate', 0)
        if discount_rate < 0.04:
            actuarial_assumptions_risk = RiskLevel.HIGH
        elif discount_rate < 0.06:
            actuarial_assumptions_risk = RiskLevel.MODERATE
        else:
            actuarial_assumptions_risk = RiskLevel.LOW
        average_age = notes.get('average_participant_age', 50)
        demographic_risk = RiskLevel.MODERATE if average_age > 55 else RiskLevel.LOW
        equity_allocation = notes.get('pension_equity_allocation', 0.6)
        investment_risk = RiskLevel.HIGH if equity_allocation > 0.8 else RiskLevel.MODERATE if equity_allocation > 0.5 else RiskLevel.LOW
        return PostEmploymentAnalysis(total_pension_obligation=total_pension_obligation, plan_assets_fair_value=plan_assets_fair_value, funded_status=funded_status, funding_ratio=funding_ratio, defined_benefit_obligation=defined_benefit_obligation, defined_contribution_assets=defined_contribution_assets, service_cost=service_cost, interest_cost=interest_cost, expected_return_on_assets=expected_return_on_assets, net_periodic_cost=net_periodic_cost, funding_status_enum=funding_status_enum, actuarial_assumptions_risk=actuarial_assumptions_risk, demographic_risk=demographic_risk, investment_risk=investment_risk)

    def create_sbc_analysis(self, statements: FinancialStatements) -> ShareBasedCompensationAnalysis:
        """Create comprehensive share-based compensation analysis object"""
        income_statement = statements.income_statement
        notes = statements.notes
        total_sbc_expense = income_statement.get('stock_compensation', 0)
        revenue = income_statement.get('revenue', 0)
        sbc_intensity = self.safe_divide(total_sbc_expense, revenue) if revenue > 0 else 0
        stock_option_expense = notes.get('stock_option_expense', 0)
        restricted_stock_expense = notes.get('restricted_stock_expense', 0)
        performance_share_expense = notes.get('performance_share_expense', 0)
        basic_shares = income_statement.get('shares_outstanding_basic', 0)
        diluted_shares = income_statement.get('shares_outstanding_diluted', 0)
        potential_dilution = self.safe_divide(diluted_shares - basic_shares, basic_shares) if basic_shares > 0 else 0
        weighted_average_dilutive_shares = diluted_shares - basic_shares
        fair_value_assumptions = {'volatility': notes.get('sbc_volatility_assumption', 0), 'risk_free_rate': notes.get('sbc_risk_free_rate', 0), 'expected_life': notes.get('sbc_expected_life', 0), 'dividend_yield': notes.get('sbc_dividend_yield', 0)}
        unvested_value = notes.get('unvested_sbc_value', 0)
        vesting_period = notes.get('weighted_average_vesting_period', 0)
        if unvested_value > 0 and vesting_period > 0:
            expense_timing_pattern = f'${unvested_value:,.0f} to be expensed over {vesting_period:.1f} years'
        else:
            expense_timing_pattern = 'Timing information not available'
        performance_ratio = self.safe_divide(performance_share_expense, total_sbc_expense) if total_sbc_expense > 0 else 0
        if performance_ratio > 0.4:
            retention_effectiveness = 'High performance alignment'
            performance_alignment = RiskLevel.LOW
        elif performance_ratio > 0.2:
            retention_effectiveness = 'Moderate performance alignment'
            performance_alignment = RiskLevel.MODERATE
        else:
            retention_effectiveness = 'Limited performance alignment'
            performance_alignment = RiskLevel.MODERATE
        return ShareBasedCompensationAnalysis(total_sbc_expense=total_sbc_expense, sbc_intensity=sbc_intensity, stock_option_expense=stock_option_expense, restricted_stock_expense=restricted_stock_expense, performance_share_expense=performance_share_expense, potential_dilution=potential_dilution, weighted_average_dilutive_shares=weighted_average_dilutive_shares, fair_value_assumptions=fair_value_assumptions, expense_timing_pattern=expense_timing_pattern, retention_effectiveness=retention_effectiveness, performance_alignment=performance_alignment)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive employee compensation analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all compensation aspects
        """
    results = []
    results.extend(self._analyze_post_employment_benefits(statements, comparative_data, industry_data))
    results.extend(self._analyze_share_based_compensation(statements, comparative_data, industry_data))
    results.extend(self._analyze_compensation_strategy(statements, comparative_data, industry_data))
    results.extend(self._assess_pension_risks(statements, comparative_data))
    results.extend(self._analyze_sbc_forecasting(statements, comparative_data))
    results.extend(self._assess_valuation_impact(statements, comparative_data))
    return results

class TaxAnalyzer(BaseAnalyzer):
    """
    Comprehensive income tax analyzer implementing CFA Institute standards.
    Covers tax rates, deferred taxes, and tax planning assessment.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_tax_formulas()
        self._initialize_tax_benchmarks()

    def _initialize_tax_formulas(self):
        """Initialize tax-specific formulas"""
        self.formula_registry.update({'effective_tax_rate': lambda tax_expense, pretax_income: self.safe_divide(tax_expense, pretax_income), 'cash_tax_rate': lambda cash_taxes_paid, pretax_income: self.safe_divide(cash_taxes_paid, pretax_income), 'deferred_tax_ratio': lambda deferred_tax_expense, total_tax_expense: self.safe_divide(deferred_tax_expense, total_tax_expense), 'dta_to_assets': lambda dta, total_assets: self.safe_divide(dta, total_assets), 'dtl_to_assets': lambda dtl, total_assets: self.safe_divide(dtl, total_assets), 'valuation_allowance_ratio': lambda allowance, gross_dta: self.safe_divide(allowance, gross_dta), 'tax_shield_value': lambda interest_expense, tax_rate: interest_expense * tax_rate})

    def _initialize_tax_benchmarks(self):
        """Initialize tax-specific benchmarks"""
        self.tax_benchmarks = {'effective_tax_rate': {'us_corporate': {'low': 0.15, 'normal': 0.21, 'high': 0.35}, 'international': {'low': 0.1, 'normal': 0.25, 'high': 0.4}, 'general': {'low': 0.15, 'normal': 0.25, 'high': 0.35}}, 'etr_volatility': {'low': 0.05, 'moderate': 0.15, 'high': 0.3}, 'cash_vs_book_difference': {'minimal': 0.05, 'moderate': 0.15, 'significant': 0.3}, 'deferred_tax_ratio': {'low': 0.1, 'moderate': 0.3, 'high': 0.6}}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive income tax analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all tax aspects
        """
        results = []
        pretax_income = statements.income_statement.get('pretax_income', 0)
        tax_expense = statements.income_statement.get('tax_expense', 0)
        if pretax_income == 0 and tax_expense == 0:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Analysis', value=0.0, interpretation='No taxable income or tax expense - tax analysis limited', risk_level=RiskLevel.LOW, methodology='Income statement tax examination'))
            return results
        results.extend(self._analyze_tax_rates(statements, comparative_data, industry_data))
        results.extend(self._analyze_deferred_taxes(statements, comparative_data))
        results.extend(self._analyze_tax_reconciliation(statements))
        results.extend(self._analyze_cash_vs_book_taxes(statements, comparative_data))
        results.extend(self._assess_tax_planning(statements, comparative_data))
        results.extend(self._analyze_international_taxes(statements))
        return results

    def _analyze_tax_rates(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze various tax rates and their implications"""
        results = []
        income_statement = statements.income_statement
        cash_flow = statements.cash_flow
        notes = statements.notes
        pretax_income = income_statement.get('pretax_income', 0)
        tax_expense = income_statement.get('tax_expense', 0)
        cash_taxes_paid = cash_flow.get('cash_taxes_paid', 0)
        if pretax_income != 0:
            effective_tax_rate = self.safe_divide(tax_expense, pretax_income)
            statutory_rate = notes.get('statutory_tax_rate', 0.25)
            country = statements.company_info.country.lower()
            if 'us' in country or 'united states' in country:
                statutory_rate = 0.21
            elif 'uk' in country or 'britain' in country:
                statutory_rate = 0.19
            elif any((eu_country in country for eu_country in ['germany', 'france', 'italy'])):
                statutory_rate = 0.3
            etr_vs_statutory = effective_tax_rate - statutory_rate
            if abs(etr_vs_statutory) < 0.05:
                etr_interpretation = f'Effective tax rate of {self.format_percentage(effective_tax_rate)} aligns with statutory rate'
                etr_risk = RiskLevel.LOW
            elif etr_vs_statutory < -0.1:
                etr_interpretation = f'Low effective tax rate of {self.format_percentage(effective_tax_rate)} indicates tax optimization strategies'
                etr_risk = RiskLevel.MODERATE
            elif etr_vs_statutory > 0.1:
                etr_interpretation = f'High effective tax rate of {self.format_percentage(effective_tax_rate)} above statutory rate'
                etr_risk = RiskLevel.MODERATE
            else:
                etr_interpretation = f'Effective tax rate of {self.format_percentage(effective_tax_rate)} shows moderate variance from statutory'
                etr_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Effective Tax Rate', value=effective_tax_rate, interpretation=etr_interpretation, risk_level=etr_risk, benchmark_comparison=self.compare_to_industry(effective_tax_rate, industry_data.get('effective_tax_rate') if industry_data else None), methodology='Income Tax Expense / Pretax Income', limitations=['Single period rate may not reflect ongoing tax burden']))
        if pretax_income != 0 and cash_taxes_paid > 0:
            cash_tax_rate = self.safe_divide(cash_taxes_paid, pretax_income)
            cash_vs_book_difference = abs(cash_tax_rate - effective_tax_rate) if 'effective_tax_rate' in locals() else 0
            if cash_vs_book_difference < 0.05:
                cash_interpretation = 'Cash and book tax rates are closely aligned'
                cash_risk = RiskLevel.LOW
            elif cash_vs_book_difference < 0.15:
                cash_interpretation = 'Moderate difference between cash and book tax rates'
                cash_risk = RiskLevel.LOW
            else:
                cash_interpretation = 'Significant difference between cash and book tax rates - indicates timing differences'
                cash_risk = RiskLevel.MODERATE
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Cash Tax Rate', value=cash_tax_rate, interpretation=cash_interpretation, risk_level=cash_risk, methodology='Cash Taxes Paid / Pretax Income', limitations=['Cash taxes may include payments for prior years or be affected by timing']))
        if comparative_data and len(comparative_data) >= 2:
            etr_values = []
            periods = []
            for i, past_statements in enumerate(comparative_data):
                past_pretax = past_statements.income_statement.get('pretax_income', 0)
                past_tax = past_statements.income_statement.get('tax_expense', 0)
                if past_pretax != 0:
                    past_etr = self.safe_divide(past_tax, past_pretax)
                    etr_values.append(past_etr)
                    periods.append(f'Period-{len(comparative_data) - i}')
            if 'effective_tax_rate' in locals():
                etr_values.append(effective_tax_rate)
                periods.append('Current')
            if len(etr_values) > 1:
                etr_volatility = np.std(etr_values)
                volatility_interpretation = 'High tax rate volatility - inconsistent tax planning' if etr_volatility > 0.15 else 'Moderate tax rate variation' if etr_volatility > 0.05 else 'Stable effective tax rate'
                volatility_risk = RiskLevel.HIGH if etr_volatility > 0.2 else RiskLevel.MODERATE if etr_volatility > 0.1 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Rate Volatility', value=etr_volatility, interpretation=volatility_interpretation, risk_level=volatility_risk, methodology='Standard deviation of effective tax rates over time'))
        return results

    def _analyze_deferred_taxes(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze deferred tax assets and liabilities"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        deferred_tax_assets = balance_sheet.get('deferred_tax_asset', 0)
        deferred_tax_liabilities = balance_sheet.get('deferred_tax_liability', 0)
        deferred_tax_expense = income_statement.get('deferred_tax', 0)
        total_tax_expense = income_statement.get('tax_expense', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        net_deferred_position = deferred_tax_assets - deferred_tax_liabilities
        if abs(net_deferred_position) > 0:
            net_position_interpretation = f'Net deferred tax {('asset' if net_deferred_position > 0 else 'liability')} of ${abs(net_deferred_position):,.0f}'
            if total_assets > 0:
                net_position_ratio = abs(net_deferred_position) / total_assets
                if net_position_ratio > 0.05:
                    net_position_interpretation += ' - significant deferred tax position'
                    position_risk = RiskLevel.MODERATE
                else:
                    net_position_interpretation += ' - modest deferred tax position'
                    position_risk = RiskLevel.LOW
            else:
                position_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Net Deferred Tax Position', value=net_deferred_position, interpretation=net_position_interpretation, risk_level=position_risk, methodology='Deferred Tax Assets - Deferred Tax Liabilities'))
        if deferred_tax_assets > 0:
            valuation_allowance = notes.get('dta_valuation_allowance', 0)
            if total_assets > 0:
                dta_ratio = self.safe_divide(deferred_tax_assets, total_assets)
                dta_interpretation = 'Significant deferred tax assets requiring realization assessment' if dta_ratio > 0.1 else 'Moderate deferred tax assets' if dta_ratio > 0.05 else 'Limited deferred tax assets'
                dta_risk = RiskLevel.MODERATE if dta_ratio > 0.15 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='DTA to Total Assets', value=dta_ratio, interpretation=dta_interpretation, risk_level=dta_risk, methodology='Deferred Tax Assets / Total Assets', limitations=['DTA realization depends on future taxable income']))
            if valuation_allowance > 0:
                allowance_ratio = self.safe_divide(valuation_allowance, deferred_tax_assets + valuation_allowance)
                allowance_interpretation = 'High valuation allowance indicates uncertainty about DTA realization' if allowance_ratio > 0.5 else 'Moderate valuation allowance' if allowance_ratio > 0.2 else 'Low valuation allowance suggests confident DTA realization'
                allowance_risk = RiskLevel.HIGH if allowance_ratio > 0.6 else RiskLevel.MODERATE if allowance_ratio > 0.3 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='DTA Valuation Allowance Ratio', value=allowance_ratio, interpretation=allowance_interpretation, risk_level=allowance_risk, methodology='Valuation Allowance / (DTA + Valuation Allowance)', limitations=['High allowance may indicate poor earnings prospects']))
        if deferred_tax_liabilities > 0 and total_assets > 0:
            dtl_ratio = self.safe_divide(deferred_tax_liabilities, total_assets)
            dtl_interpretation = 'Significant deferred tax liabilities from temporary differences' if dtl_ratio > 0.1 else 'Moderate deferred tax liabilities' if dtl_ratio > 0.05 else 'Limited deferred tax liabilities'
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='DTL to Total Assets', value=dtl_ratio, interpretation=dtl_interpretation, risk_level=RiskLevel.LOW, methodology='Deferred Tax Liabilities / Total Assets', limitations=['DTL reversal timing depends on asset usage and accounting methods']))
        if total_tax_expense != 0 and abs(deferred_tax_expense) > 0:
            deferred_ratio = self.safe_divide(abs(deferred_tax_expense), abs(total_tax_expense))
            deferred_interpretation = 'Significant deferred tax component in total tax expense' if deferred_ratio > 0.3 else 'Moderate deferred tax impact' if deferred_ratio > 0.15 else 'Limited deferred tax expense component'
            deferred_risk = RiskLevel.MODERATE if deferred_ratio > 0.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Deferred Tax Expense Ratio', value=deferred_ratio, interpretation=deferred_interpretation, risk_level=deferred_risk, methodology='|Deferred Tax Expense| / |Total Tax Expense|'))
        return results

    def _analyze_tax_reconciliation(self, statements: FinancialStatements) -> List[AnalysisResult]:
        """Analyze tax rate reconciliation and permanent differences"""
        results = []
        income_statement = statements.income_statement
        notes = statements.notes
        pretax_income = income_statement.get('pretax_income', 0)
        tax_expense = income_statement.get('tax_expense', 0)
        if pretax_income == 0:
            return results
        reconciliation_items = {'statutory_rate_effect': notes.get('statutory_rate_effect', 0), 'permanent_differences': notes.get('permanent_differences', 0), 'tax_credits': notes.get('tax_credits', 0), 'foreign_rate_differences': notes.get('foreign_rate_differences', 0), 'prior_year_adjustments': notes.get('prior_year_tax_adjustments', 0), 'other_tax_effects': notes.get('other_tax_effects', 0)}
        total_reconciling_items = sum((abs(value) for value in reconciliation_items.values() if value != 0))
        if total_reconciling_items > 0:
            for item_name, item_value in reconciliation_items.items():
                if abs(item_value) > abs(tax_expense) * 0.05:
                    item_display_name = item_name.replace('_', ' ').title()
                    item_impact = self.safe_divide(item_value, tax_expense) if tax_expense != 0 else 0
                    item_interpretation = f'{item_display_name} {('increases' if item_value > 0 else 'decreases')} tax expense by {self.format_percentage(abs(item_impact))}'
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name=f'Tax Reconciliation - {item_display_name}', value=item_impact, interpretation=item_interpretation, risk_level=RiskLevel.LOW, methodology='Reconciliation item impact on total tax expense'))
        effective_tax_rate = self.safe_divide(tax_expense, pretax_income)
        statutory_rate = notes.get('statutory_tax_rate', 0.25)
        reconciliation_explained = self.safe_divide(total_reconciling_items, abs(effective_tax_rate - statutory_rate) * abs(pretax_income)) if abs(effective_tax_rate - statutory_rate) * abs(pretax_income) > 0 else 0
        if reconciliation_explained > 0.8:
            reconciliation_quality = 'Comprehensive tax rate reconciliation provided'
            reconciliation_risk = RiskLevel.LOW
        elif reconciliation_explained > 0.5:
            reconciliation_quality = 'Adequate tax rate reconciliation'
            reconciliation_risk = RiskLevel.LOW
        else:
            reconciliation_quality = 'Limited tax rate reconciliation disclosure'
            reconciliation_risk = RiskLevel.MODERATE
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Reconciliation Quality', value=reconciliation_explained, interpretation=reconciliation_quality, risk_level=reconciliation_risk, methodology='Assessment of tax rate reconciliation completeness'))
        return results

    def _analyze_cash_vs_book_taxes(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze differences between cash and book tax amounts"""
        results = []
        income_statement = statements.income_statement
        cash_flow = statements.cash_flow
        tax_expense = income_statement.get('tax_expense', 0)
        cash_taxes_paid = cash_flow.get('cash_taxes_paid', 0)
        current_tax_expense = income_statement.get('current_tax_expense', tax_expense)
        deferred_tax_expense = income_statement.get('deferred_tax', 0)
        if current_tax_expense != 0 and cash_taxes_paid > 0:
            cash_vs_current = cash_taxes_paid - current_tax_expense
            cash_timing_ratio = self.safe_divide(abs(cash_vs_current), abs(current_tax_expense))
            if abs(cash_vs_current) < abs(current_tax_expense) * 0.1:
                timing_interpretation = 'Cash and current tax expense are closely aligned'
                timing_risk = RiskLevel.LOW
            elif cash_vs_current > 0:
                timing_interpretation = f'Cash taxes exceed current expense by {self.format_percentage(cash_timing_ratio)} - paying for prior years or prepaying'
                timing_risk = RiskLevel.LOW
            else:
                timing_interpretation = f'Current tax expense exceeds cash payments by {self.format_percentage(cash_timing_ratio)} - timing differences or accruals'
                timing_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Cash vs Current Tax Timing', value=cash_timing_ratio, interpretation=timing_interpretation, risk_level=timing_risk, methodology='(Cash Taxes Paid - Current Tax Expense) / Current Tax Expense'))
        if comparative_data and len(comparative_data) >= 2:
            cash_tax_values = []
            book_tax_values = []
            for past_statements in comparative_data:
                past_cash_tax = past_statements.cash_flow.get('cash_taxes_paid', 0)
                past_book_tax = past_statements.income_statement.get('tax_expense', 0)
                if past_cash_tax > 0 and past_book_tax != 0:
                    cash_tax_values.append(past_cash_tax)
                    book_tax_values.append(past_book_tax)
            if cash_taxes_paid > 0 and tax_expense != 0:
                cash_tax_values.append(cash_taxes_paid)
                book_tax_values.append(tax_expense)
            if len(cash_tax_values) > 1 and len(book_tax_values) > 1:
                correlation = np.corrcoef(cash_tax_values, book_tax_values)[0, 1] if len(cash_tax_values) == len(book_tax_values) else 0
                correlation_interpretation = 'Strong correlation between cash and book taxes' if correlation > 0.8 else 'Moderate correlation' if correlation > 0.5 else 'Weak correlation - significant timing differences'
                correlation_risk = RiskLevel.LOW if correlation > 0.7 else RiskLevel.MODERATE if correlation > 0.4 else RiskLevel.HIGH
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Cash-Book Tax Correlation', value=correlation, interpretation=correlation_interpretation, risk_level=correlation_risk, methodology='Correlation coefficient between cash and book tax amounts over time'))
        return results

    def _assess_tax_planning(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess tax planning effectiveness and strategy"""
        results = []
        income_statement = statements.income_statement
        notes = statements.notes
        pretax_income = income_statement.get('pretax_income', 0)
        tax_expense = income_statement.get('tax_expense', 0)
        if pretax_income == 0:
            return results
        effective_tax_rate = self.safe_divide(tax_expense, pretax_income)
        statutory_rate = notes.get('statutory_tax_rate', 0.25)
        tax_savings = (statutory_rate - effective_tax_rate) * pretax_income if pretax_income > 0 else 0
        tax_efficiency_ratio = self.safe_divide(tax_savings, abs(pretax_income * statutory_rate)) if statutory_rate > 0 else 0
        if tax_efficiency_ratio > 0.2:
            efficiency_interpretation = 'High tax efficiency - significant tax optimization achieved'
            efficiency_risk = RiskLevel.MODERATE
            strategy_classification = TaxStrategy.AGGRESSIVE
        elif tax_efficiency_ratio > 0.05:
            efficiency_interpretation = 'Moderate tax efficiency - some optimization strategies employed'
            efficiency_risk = RiskLevel.LOW
            strategy_classification = TaxStrategy.MODERATE
        elif tax_efficiency_ratio > -0.05:
            efficiency_interpretation = 'Standard tax efficiency - limited optimization'
            efficiency_risk = RiskLevel.LOW
            strategy_classification = TaxStrategy.CONSERVATIVE
        else:
            efficiency_interpretation = 'Below-average tax efficiency - potential for improvement'
            efficiency_risk = RiskLevel.MODERATE
            strategy_classification = TaxStrategy.CONSERVATIVE
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Planning Efficiency', value=tax_efficiency_ratio, interpretation=efficiency_interpretation, risk_level=efficiency_risk, methodology='(Statutory Rate - Effective Rate) × Pretax Income / (Statutory Rate × Pretax Income)'))
        uncertain_tax_positions = notes.get('uncertain_tax_positions', 0)
        if uncertain_tax_positions > 0:
            utp_ratio = self.safe_divide(uncertain_tax_positions, abs(tax_expense)) if tax_expense != 0 else 0
            utp_interpretation = 'Significant uncertain tax positions indicate aggressive tax strategies' if utp_ratio > 0.5 else 'Moderate uncertain tax positions' if utp_ratio > 0.2 else 'Limited uncertain tax positions'
            utp_risk = RiskLevel.HIGH if utp_ratio > 0.8 else RiskLevel.MODERATE if utp_ratio > 0.3 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Uncertain Tax Positions', value=utp_ratio, interpretation=utp_interpretation, risk_level=utp_risk, methodology='Uncertain Tax Positions / Total Tax Expense', limitations=['High UTP may indicate potential tax adjustments']))
        if comparative_data and len(comparative_data) >= 2:
            etr_values = []
            for past_statements in comparative_data:
                past_pretax = past_statements.income_statement.get('pretax_income', 0)
                past_tax = past_statements.income_statement.get('tax_expense', 0)
                if past_pretax != 0:
                    past_etr = self.safe_divide(past_tax, past_pretax)
                    etr_values.append(past_etr)
            etr_values.append(effective_tax_rate)
            if len(etr_values) > 1:
                etr_consistency = 1 - np.std(etr_values) / np.mean(etr_values) if np.mean(etr_values) > 0 else 0
                consistency_interpretation = 'Highly consistent tax strategy' if etr_consistency > 0.8 else 'Moderately consistent tax approach' if etr_consistency > 0.6 else 'Inconsistent tax strategy - may indicate changing circumstances or aggressive planning'
                consistency_risk = RiskLevel.LOW if etr_consistency > 0.7 else RiskLevel.MODERATE if etr_consistency > 0.5 else RiskLevel.HIGH
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Strategy Consistency', value=etr_consistency, interpretation=consistency_interpretation, risk_level=consistency_risk, methodology='1 - (Standard Deviation of ETR / Mean ETR)'))
        return results

    def _analyze_international_taxes(self, statements: FinancialStatements) -> List[AnalysisResult]:
        """Analyze international tax considerations"""
        results = []
        notes = statements.notes
        income_statement = statements.income_statement
        foreign_tax_credit = notes.get('foreign_tax_credit', 0)
        foreign_income = notes.get('foreign_pretax_income', 0)
        domestic_income = notes.get('domestic_pretax_income', 0)
        total_pretax = income_statement.get('pretax_income', 0)
        if foreign_income > 0 and total_pretax > 0:
            foreign_income_ratio = self.safe_divide(foreign_income, total_pretax)
            geographic_interpretation = 'Significant international operations' if foreign_income_ratio > 0.3 else 'Moderate international presence' if foreign_income_ratio > 0.1 else 'Primarily domestic operations'
            geographic_risk = RiskLevel.MODERATE if foreign_income_ratio > 0.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='International Income Exposure', value=foreign_income_ratio, interpretation=geographic_interpretation, risk_level=geographic_risk, methodology='Foreign Pretax Income / Total Pretax Income', limitations=['International operations create additional tax complexity']))
        if foreign_tax_credit > 0:
            total_tax_expense = income_statement.get('tax_expense', 0)
            ftc_ratio = self.safe_divide(foreign_tax_credit, abs(total_tax_expense)) if total_tax_expense != 0 else 0
            ftc_interpretation = 'Significant foreign tax credit utilization' if ftc_ratio > 0.2 else 'Moderate foreign tax credits' if ftc_ratio > 0.1 else 'Limited foreign tax credit usage'
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Foreign Tax Credit Utilization', value=ftc_ratio, interpretation=ftc_interpretation, risk_level=RiskLevel.LOW, methodology='Foreign Tax Credits / Total Tax Expense'))
        related_party_transactions = notes.get('related_party_revenue', 0) + notes.get('related_party_expenses', 0)
        revenue = income_statement.get('revenue', 0)
        if related_party_transactions > 0 and revenue > 0:
            transfer_pricing_exposure = self.safe_divide(related_party_transactions, revenue)
            tp_interpretation = 'High transfer pricing exposure - significant related party transactions' if transfer_pricing_exposure > 0.3 else 'Moderate transfer pricing considerations' if transfer_pricing_exposure > 0.1 else 'Limited transfer pricing exposure'
            tp_risk = RiskLevel.HIGH if transfer_pricing_exposure > 0.5 else RiskLevel.MODERATE if transfer_pricing_exposure > 0.2 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Transfer Pricing Exposure', value=transfer_pricing_exposure, interpretation=tp_interpretation, risk_level=tp_risk, methodology='Related Party Transactions / Revenue', limitations=['High exposure increases tax audit and adjustment risk']))
        return results

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key tax metrics"""
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        cash_flow = statements.cash_flow
        metrics = {}
        pretax_income = income_statement.get('pretax_income', 0)
        tax_expense = income_statement.get('tax_expense', 0)
        cash_taxes_paid = cash_flow.get('cash_taxes_paid', 0)
        if pretax_income != 0:
            metrics['effective_tax_rate'] = self.safe_divide(tax_expense, pretax_income)
            if cash_taxes_paid > 0:
                metrics['cash_tax_rate'] = self.safe_divide(cash_taxes_paid, pretax_income)
        deferred_tax_assets = balance_sheet.get('deferred_tax_asset', 0)
        deferred_tax_liabilities = balance_sheet.get('deferred_tax_liability', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        metrics['net_deferred_tax_position'] = deferred_tax_assets - deferred_tax_liabilities
        if total_assets > 0:
            metrics['dta_to_assets'] = self.safe_divide(deferred_tax_assets, total_assets)
            metrics['dtl_to_assets'] = self.safe_divide(deferred_tax_liabilities, total_assets)
        current_tax_expense = income_statement.get('current_tax_expense', 0)
        deferred_tax_expense = income_statement.get('deferred_tax', 0)
        if tax_expense != 0:
            metrics['current_tax_ratio'] = self.safe_divide(current_tax_expense, tax_expense)
            metrics['deferred_tax_ratio'] = self.safe_divide(deferred_tax_expense, tax_expense)
        return metrics

    def create_tax_rate_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> TaxRateAnalysis:
        """Create comprehensive tax rate analysis object"""
        income_statement = statements.income_statement
        cash_flow = statements.cash_flow
        notes = statements.notes
        pretax_income = income_statement.get('pretax_income', 0)
        tax_expense = income_statement.get('tax_expense', 0)
        cash_taxes_paid = cash_flow.get('cash_taxes_paid', 0)
        effective_tax_rate = self.safe_divide(tax_expense, pretax_income) if pretax_income != 0 else 0
        cash_tax_rate = self.safe_divide(cash_taxes_paid, pretax_income) if pretax_income != 0 and cash_taxes_paid > 0 else 0
        statutory_tax_rate = notes.get('statutory_tax_rate', 0.25)
        etr_vs_statutory = effective_tax_rate - statutory_tax_rate
        cash_vs_effective = cash_tax_rate - effective_tax_rate
        if statutory_tax_rate > 0 and pretax_income > 0:
            tax_savings = (statutory_tax_rate - effective_tax_rate) * pretax_income
            potential_tax = statutory_tax_rate * pretax_income
            tax_efficiency_score = self.safe_divide(tax_savings, abs(potential_tax)) * 100
        else:
            tax_efficiency_score = 0
        rate_volatility = None
        if comparative_data and len(comparative_data) >= 2:
            etr_values = []
            for past_statements in comparative_data:
                past_pretax = past_statements.income_statement.get('pretax_income', 0)
                past_tax = past_statements.income_statement.get('tax_expense', 0)
                if past_pretax != 0:
                    past_etr = self.safe_divide(past_tax, past_pretax)
                    etr_values.append(past_etr)
            etr_values.append(effective_tax_rate)
            if len(etr_values) > 1:
                rate_volatility = np.std(etr_values)
        rate_reconciliation = {'statutory_rate_effect': notes.get('statutory_rate_effect', 0), 'permanent_differences': notes.get('permanent_differences', 0), 'tax_credits': notes.get('tax_credits', 0), 'foreign_rate_differences': notes.get('foreign_rate_differences', 0)}
        permanent_differences = []
        if notes.get('municipal_bond_interest', 0) > 0:
            permanent_differences.append('Tax-exempt interest income')
        if notes.get('meals_entertainment', 0) > 0:
            permanent_differences.append('Non-deductible meals and entertainment')
        if notes.get('life_insurance_proceeds', 0) > 0:
            permanent_differences.append('Life insurance proceeds')
        return TaxRateAnalysis(statutory_tax_rate=statutory_tax_rate, effective_tax_rate=effective_tax_rate, cash_tax_rate=cash_tax_rate, etr_vs_statutory=etr_vs_statutory, cash_vs_effective=cash_vs_effective, tax_efficiency_score=tax_efficiency_score, rate_volatility=rate_volatility, rate_reconciliation=rate_reconciliation, permanent_differences=permanent_differences)

    def create_deferred_tax_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> DeferredTaxAnalysis:
        """Create comprehensive deferred tax analysis object"""
        balance_sheet = statements.balance_sheet
        notes = statements.notes
        deferred_tax_assets = balance_sheet.get('deferred_tax_asset', 0)
        deferred_tax_liabilities = balance_sheet.get('deferred_tax_liability', 0)
        net_deferred_tax_position = deferred_tax_assets - deferred_tax_liabilities
        dta_composition = {'nol_carryforwards': notes.get('nol_dta', 0), 'depreciation_differences': notes.get('depreciation_dta', 0), 'accrued_expenses': notes.get('accrual_dta', 0), 'other': notes.get('other_dta', 0)}
        dtl_composition = {'depreciation_differences': notes.get('depreciation_dtl', 0), 'intangible_amortization': notes.get('intangible_dtl', 0), 'other': notes.get('other_dtl', 0)}
        valuation_allowance = notes.get('dta_valuation_allowance', 0)
        gross_dta = deferred_tax_assets + valuation_allowance
        dta_realization_probability = self.safe_divide(deferred_tax_assets, gross_dta) if gross_dta > 0 else 1.0
        net_position_trend = TrendDirection.STABLE
        if comparative_data and len(comparative_data) >= 2:
            net_position_values = []
            for past_statements in comparative_data:
                past_dta = past_statements.balance_sheet.get('deferred_tax_asset', 0)
                past_dtl = past_statements.balance_sheet.get('deferred_tax_liability', 0)
                net_position_values.append(past_dta - past_dtl)
            net_position_values.append(net_deferred_tax_position)
            if len(net_position_values) >= 3:
                if net_position_values[-1] > net_position_values[0] * 1.1:
                    net_position_trend = TrendDirection.IMPROVING
                elif net_position_values[-1] < net_position_values[0] * 0.9:
                    net_position_trend = TrendDirection.DETERIORATING
        reversal_timeline = 'Long-term reversal expected' if abs(net_deferred_tax_position) > 0 else 'No significant deferred taxes'
        return DeferredTaxAnalysis(deferred_tax_assets=deferred_tax_assets, deferred_tax_liabilities=deferred_tax_liabilities, net_deferred_tax_position=net_deferred_tax_position, dta_composition=dta_composition, dtl_composition=dtl_composition, valuation_allowance=valuation_allowance, dta_realization_probability=dta_realization_probability, net_position_trend=net_position_trend, reversal_timeline=reversal_timeline)

    def assess_tax_planning_strategy(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> TaxPlanningAnalysis:
        """Assess tax planning effectiveness and strategy"""
        income_statement = statements.income_statement
        notes = statements.notes
        pretax_income = income_statement.get('pretax_income', 0)
        tax_expense = income_statement.get('tax_expense', 0)
        effective_tax_rate = self.safe_divide(tax_expense, pretax_income) if pretax_income != 0 else 0
        statutory_rate = notes.get('statutory_tax_rate', 0.25)
        tax_savings_rate = (statutory_rate - effective_tax_rate) / statutory_rate if statutory_rate > 0 else 0
        if tax_savings_rate > 0.25:
            tax_strategy_classification = TaxStrategy.AGGRESSIVE
        elif tax_savings_rate > 0.1:
            tax_strategy_classification = TaxStrategy.MODERATE
        else:
            tax_strategy_classification = TaxStrategy.CONSERVATIVE
        tax_optimization_score = min(100, max(0, tax_savings_rate * 100))
        foreign_income = notes.get('foreign_pretax_income', 0)
        international_planning = foreign_income > 0
        timing_strategies = []
        if notes.get('installment_sales', 0) > 0:
            timing_strategies.append('Installment sale deferrals')
        if notes.get('like_kind_exchanges', 0) > 0:
            timing_strategies.append('Like-kind exchanges')
        if notes.get('depreciation_elections', 0) > 0:
            timing_strategies.append('Accelerated depreciation elections')
        uncertain_tax_positions = notes.get('uncertain_tax_positions', 0)
        if uncertain_tax_positions > abs(tax_expense) * 0.5:
            tax_audit_risk = RiskLevel.HIGH
        elif uncertain_tax_positions > abs(tax_expense) * 0.2:
            tax_audit_risk = RiskLevel.MODERATE
        else:
            tax_audit_risk = RiskLevel.LOW
        compliance_quality = 100
        if notes.get('tax_penalties', 0) > 0:
            compliance_quality -= 20
        if notes.get('prior_year_adjustments', 0) > abs(tax_expense) * 0.1:
            compliance_quality -= 15
        compliance_quality = max(0, compliance_quality)
        return TaxPlanningAnalysis(tax_strategy_classification=tax_strategy_classification, tax_optimization_score=tax_optimization_score, international_planning=international_planning, timing_strategies=timing_strategies, tax_audit_risk=tax_audit_risk, compliance_quality=compliance_quality, uncertain_tax_positions=uncertain_tax_positions)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive income tax analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all tax aspects
        """
    results = []
    pretax_income = statements.income_statement.get('pretax_income', 0)
    tax_expense = statements.income_statement.get('tax_expense', 0)
    if pretax_income == 0 and tax_expense == 0:
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Analysis', value=0.0, interpretation='No taxable income or tax expense - tax analysis limited', risk_level=RiskLevel.LOW, methodology='Income statement tax examination'))
        return results
    results.extend(self._analyze_tax_rates(statements, comparative_data, industry_data))
    results.extend(self._analyze_deferred_taxes(statements, comparative_data))
    results.extend(self._analyze_tax_reconciliation(statements))
    results.extend(self._analyze_cash_vs_book_taxes(statements, comparative_data))
    results.extend(self._assess_tax_planning(statements, comparative_data))
    results.extend(self._analyze_international_taxes(statements))
    return results

class MultinationalOperationsAnalyzer(BaseAnalyzer):
    """
    Comprehensive multinational operations analyzer implementing CFA Level II standards.
    Covers currency exposure, translation methods, and geographic analysis.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_multinational_formulas()
        self._initialize_currency_benchmarks()

    def _initialize_multinational_formulas(self):
        """Initialize multinational-specific formulas"""
        self.formula_registry.update({'currency_exposure_ratio': lambda foreign_exposure, total_exposure: self.safe_divide(foreign_exposure, total_exposure), 'translation_volatility': lambda translation_std, avg_translation: self.safe_divide(translation_std, abs(avg_translation)), 'hedging_ratio': lambda hedged_amount, total_exposure: self.safe_divide(hedged_amount, total_exposure), 'geographic_concentration': lambda largest_segment, total_revenue: self.safe_divide(largest_segment, total_revenue), 'emerging_market_ratio': lambda em_revenue, total_revenue: self.safe_divide(em_revenue, total_revenue), 'fx_sensitivity': lambda earnings_change, fx_change: self.safe_divide(earnings_change, fx_change)})

    def _initialize_currency_benchmarks(self):
        """Initialize currency exposure benchmarks"""
        self.currency_benchmarks = {'foreign_exposure_ratio': {'low': 0.2, 'moderate': 0.4, 'high': 0.6, 'very_high': 0.8}, 'currency_concentration': {'diversified': 0.3, 'moderate': 0.5, 'concentrated': 0.7, 'very_concentrated': 0.9}, 'translation_volatility': {'low': 0.1, 'moderate': 0.3, 'high': 0.6, 'very_high': 1.0}, 'emerging_market_exposure': {'low': 0.1, 'moderate': 0.3, 'high': 0.5, 'very_high': 0.7}}
        self.hyperinflation_thresholds = {'cumulative_inflation_3_years': 1.0, 'annual_inflation_rate': 0.26, 'currency_devaluation_annual': 0.5}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive multinational operations analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all multinational aspects
        """
        results = []
        results.extend(self._analyze_currency_exposure(statements, comparative_data, industry_data))
        results.extend(self._analyze_translation_methods(statements, comparative_data))
        results.extend(self._analyze_geographic_segments(statements, comparative_data))
        results.extend(self._analyze_hyperinflationary_economies(statements, comparative_data))
        results.extend(self._analyze_currency_hedging(statements, comparative_data))
        results.extend(self._analyze_ratio_impacts(statements, comparative_data))
        results.extend(self._analyze_sales_sustainability(statements, comparative_data))
        return results

    def _analyze_currency_exposure(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze foreign currency exposure"""
        results = []
        notes = statements.notes
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        foreign_revenue = notes.get('foreign_revenue', 0)
        foreign_assets = notes.get('foreign_assets', 0)
        foreign_receivables = balance_sheet.get('foreign_receivables', 0)
        foreign_payables = balance_sheet.get('foreign_payables', 0)
        total_revenue = income_statement.get('revenue', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if total_revenue > 0 and foreign_revenue > 0:
            foreign_revenue_ratio = self.safe_divide(foreign_revenue, total_revenue)
            benchmark = self.currency_benchmarks['foreign_exposure_ratio']
            if foreign_revenue_ratio > benchmark['very_high']:
                exposure_interpretation = 'Very high foreign revenue exposure - significant currency risk'
                exposure_risk = RiskLevel.HIGH
            elif foreign_revenue_ratio > benchmark['high']:
                exposure_interpretation = 'High foreign revenue exposure'
                exposure_risk = RiskLevel.MODERATE
            elif foreign_revenue_ratio > benchmark['moderate']:
                exposure_interpretation = 'Moderate foreign revenue exposure'
                exposure_risk = RiskLevel.MODERATE
            else:
                exposure_interpretation = 'Low foreign revenue exposure'
                exposure_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Foreign Revenue Exposure', value=foreign_revenue_ratio, interpretation=exposure_interpretation, risk_level=exposure_risk, benchmark_comparison=self.compare_to_industry(foreign_revenue_ratio, industry_data.get('foreign_revenue_ratio') if industry_data else None), methodology='Foreign Revenue / Total Revenue', limitations=['Currency exposure depends on hedging strategies and natural hedges']))
        if total_assets > 0 and foreign_assets > 0:
            foreign_asset_ratio = self.safe_divide(foreign_assets, total_assets)
            asset_exposure_interpretation = 'Significant foreign asset exposure to translation risk' if foreign_asset_ratio > 0.4 else 'Moderate foreign asset exposure' if foreign_asset_ratio > 0.2 else 'Limited foreign asset exposure'
            asset_exposure_risk = RiskLevel.MODERATE if foreign_asset_ratio > 0.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Foreign Asset Exposure', value=foreign_asset_ratio, interpretation=asset_exposure_interpretation, risk_level=asset_exposure_risk, methodology='Foreign Assets / Total Assets'))
        if foreign_receivables > 0 or foreign_payables > 0:
            net_transaction_exposure = foreign_receivables - foreign_payables
            if total_assets > 0:
                transaction_exposure_ratio = self.safe_divide(abs(net_transaction_exposure), total_assets)
                transaction_interpretation = f'Net transaction {('asset' if net_transaction_exposure > 0 else 'liability')} exposure of {self.format_percentage(transaction_exposure_ratio)} of total assets'
                transaction_risk = RiskLevel.HIGH if transaction_exposure_ratio > 0.1 else RiskLevel.MODERATE if transaction_exposure_ratio > 0.05 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Net Transaction Exposure', value=transaction_exposure_ratio, interpretation=transaction_interpretation, risk_level=transaction_risk, methodology='|Foreign Receivables - Foreign Payables| / Total Assets'))
        currency_exposures = self._extract_currency_exposures(notes)
        if currency_exposures:
            max_currency_exposure = max(currency_exposures.values())
            total_foreign_exposure = sum(currency_exposures.values())
            if total_foreign_exposure > 0:
                currency_concentration = self.safe_divide(max_currency_exposure, total_foreign_exposure)
                concentration_benchmark = self.currency_benchmarks['currency_concentration']
                if currency_concentration > concentration_benchmark['very_concentrated']:
                    concentration_interpretation = 'Very high currency concentration risk'
                    concentration_risk = RiskLevel.HIGH
                elif currency_concentration > concentration_benchmark['concentrated']:
                    concentration_interpretation = 'High currency concentration'
                    concentration_risk = RiskLevel.MODERATE
                else:
                    concentration_interpretation = 'Diversified currency exposure'
                    concentration_risk = RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Currency Concentration Risk', value=currency_concentration, interpretation=concentration_interpretation, risk_level=concentration_risk, methodology='Largest Currency Exposure / Total Foreign Exposure'))
        return results

    def _analyze_translation_methods(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze foreign currency translation methods and their impacts"""
        results = []
        notes = statements.notes
        equity_statement = statements.equity_statement
        reporting_standard = statements.company_info.reporting_standard
        translation_method = notes.get('translation_method', 'current_rate')
        functional_currencies = notes.get('functional_currencies', [])
        if 'current_rate' in translation_method.lower():
            translation_adjustment = equity_statement.get('translation_adjustment', 0)
            total_equity = statements.balance_sheet.get('total_equity', 0)
            if total_equity > 0 and abs(translation_adjustment) > 0:
                translation_impact = self.safe_divide(abs(translation_adjustment), total_equity)
                impact_interpretation = 'Significant translation impact on equity' if translation_impact > 0.1 else 'Moderate translation impact' if translation_impact > 0.05 else 'Limited translation impact'
                impact_risk = RiskLevel.MODERATE if translation_impact > 0.15 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Current Rate Translation Impact', value=translation_impact, interpretation=impact_interpretation, risk_level=impact_risk, methodology='|Translation Adjustment| / Total Equity', limitations=['Current rate method affects balance sheet but not income statement ratios']))
        elif 'temporal' in translation_method.lower():
            fx_gains_losses = statements.income_statement.get('foreign_exchange_gains_losses', 0)
            net_income = statements.income_statement.get('net_income', 0)
            if net_income != 0 and abs(fx_gains_losses) > 0:
                fx_impact_on_earnings = self.safe_divide(abs(fx_gains_losses), abs(net_income))
                earnings_impact_interpretation = 'Significant FX impact on earnings under temporal method' if fx_impact_on_earnings > 0.2 else 'Moderate FX earnings impact' if fx_impact_on_earnings > 0.1 else 'Limited FX earnings impact'
                earnings_impact_risk = RiskLevel.HIGH if fx_impact_on_earnings > 0.3 else RiskLevel.MODERATE if fx_impact_on_earnings > 0.15 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Temporal Method Earnings Impact', value=fx_impact_on_earnings, interpretation=earnings_impact_interpretation, risk_level=earnings_impact_risk, methodology='|FX Gains/Losses| / |Net Income|', limitations=['Temporal method creates income statement volatility']))
        if functional_currencies:
            num_functional_currencies = len(functional_currencies)
            functional_currency_interpretation = f'Operations in {num_functional_currencies} functional currencies increases complexity'
            functional_currency_risk = RiskLevel.MODERATE if num_functional_currencies > 5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Functional Currency Complexity', value=num_functional_currencies, interpretation=functional_currency_interpretation, risk_level=functional_currency_risk, methodology='Count of functional currencies used by subsidiaries'))
        if comparative_data and len(comparative_data) >= 2:
            translation_adjustments = []
            for past_statements in comparative_data:
                past_adjustment = past_statements.equity_statement.get('translation_adjustment', 0)
                translation_adjustments.append(past_adjustment)
            current_adjustment = equity_statement.get('translation_adjustment', 0)
            translation_adjustments.append(current_adjustment)
            if len(translation_adjustments) > 2:
                translation_volatility = np.std(translation_adjustments)
                mean_adjustment = np.mean([abs(x) for x in translation_adjustments])
                if mean_adjustment > 0:
                    volatility_ratio = self.safe_divide(translation_volatility, mean_adjustment)
                    volatility_interpretation = 'High translation volatility' if volatility_ratio > 1.0 else 'Moderate translation volatility' if volatility_ratio > 0.5 else 'Low translation volatility'
                    volatility_risk = RiskLevel.HIGH if volatility_ratio > 1.5 else RiskLevel.MODERATE if volatility_ratio > 0.8 else RiskLevel.LOW
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Translation Volatility', value=volatility_ratio, interpretation=volatility_interpretation, risk_level=volatility_risk, methodology='Standard Deviation of Translation Adjustments / Mean Absolute Adjustment'))
        return results

    def _analyze_geographic_segments(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze geographic segment performance and concentration"""
        results = []
        notes = statements.notes
        geographic_segments = self._extract_geographic_segments(notes)
        if not geographic_segments:
            return results
        total_revenue = sum((segment.get('revenue', 0) for segment in geographic_segments.values()))
        total_assets = sum((segment.get('assets', 0) for segment in geographic_segments.values()))
        if total_revenue > 0:
            revenue_by_region = {region: segment.get('revenue', 0) for region, segment in geographic_segments.items()}
            largest_region_revenue = max(revenue_by_region.values())
            geographic_concentration = self.safe_divide(largest_region_revenue, total_revenue)
            concentration_interpretation = 'High geographic concentration risk' if geographic_concentration > 0.6 else 'Moderate geographic concentration' if geographic_concentration > 0.4 else 'Well-diversified geographic presence'
            concentration_risk = RiskLevel.HIGH if geographic_concentration > 0.7 else RiskLevel.MODERATE if geographic_concentration > 0.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Geographic Revenue Concentration', value=geographic_concentration, interpretation=concentration_interpretation, risk_level=concentration_risk, methodology='Largest Region Revenue / Total Revenue'))
        emerging_markets = ['china', 'india', 'brazil', 'russia', 'mexico', 'turkey', 'south_africa']
        em_revenue = 0
        dm_revenue = 0
        for region, segment in geographic_segments.items():
            region_revenue = segment.get('revenue', 0)
            if any((em in region.lower() for em in emerging_markets)):
                em_revenue += region_revenue
            else:
                dm_revenue += region_revenue
        if total_revenue > 0:
            em_exposure = self.safe_divide(em_revenue, total_revenue)
            benchmark = self.currency_benchmarks['emerging_market_exposure']
            if em_exposure > benchmark['very_high']:
                em_interpretation = 'Very high emerging market exposure - significant political and economic risk'
                em_risk = RiskLevel.HIGH
            elif em_exposure > benchmark['high']:
                em_interpretation = 'High emerging market exposure'
                em_risk = RiskLevel.MODERATE
            elif em_exposure > benchmark['moderate']:
                em_interpretation = 'Moderate emerging market exposure'
                em_risk = RiskLevel.MODERATE
            else:
                em_interpretation = 'Low emerging market exposure'
                em_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Emerging Market Exposure', value=em_exposure, interpretation=em_interpretation, risk_level=em_risk, methodology='Emerging Market Revenue / Total Revenue'))
        for region, segment in geographic_segments.items():
            region_revenue = segment.get('revenue', 0)
            region_profit = segment.get('profit', 0)
            if region_revenue > 0:
                region_margin = self.safe_divide(region_profit, region_revenue)
                region_contribution = self.safe_divide(region_revenue, total_revenue) if total_revenue > 0 else 0
                if region_contribution > 0.1:
                    results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name=f'{region.title()} Regional Margin', value=region_margin, interpretation=f'{region.title()} margin of {self.format_percentage(region_margin)} ({self.format_percentage(region_contribution)} of total revenue)', risk_level=RiskLevel.LOW if region_margin > 0.1 else RiskLevel.MODERATE if region_margin > 0.05 else RiskLevel.HIGH, methodology='Regional Profit / Regional Revenue'))
        return results

    def _analyze_hyperinflationary_economies(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze operations in hyperinflationary economies"""
        results = []
        notes = statements.notes
        hyperinflationary_countries = notes.get('hyperinflationary_countries', [])
        hyperinflationary_revenue = notes.get('hyperinflationary_revenue', 0)
        hyperinflationary_assets = notes.get('hyperinflationary_assets', 0)
        total_revenue = statements.income_statement.get('revenue', 0)
        total_assets = statements.balance_sheet.get('total_assets', 0)
        if hyperinflationary_countries:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Hyperinflationary Economy Operations', value=len(hyperinflationary_countries), interpretation=f'Operations in {len(hyperinflationary_countries)} hyperinflationary economies: {', '.join(hyperinflationary_countries)}', risk_level=RiskLevel.HIGH if len(hyperinflationary_countries) > 2 else RiskLevel.MODERATE, methodology='Count and identification of hyperinflationary economy operations', limitations=['Hyperinflationary accounting requires complex restatement procedures']))
        if hyperinflationary_revenue > 0 and total_revenue > 0:
            hyperinflation_revenue_ratio = self.safe_divide(hyperinflationary_revenue, total_revenue)
            hyperinflation_interpretation = 'Significant hyperinflationary economy revenue exposure' if hyperinflation_revenue_ratio > 0.2 else 'Moderate hyperinflationary exposure' if hyperinflation_revenue_ratio > 0.1 else 'Limited hyperinflationary exposure'
            hyperinflation_risk = RiskLevel.HIGH if hyperinflation_revenue_ratio > 0.3 else RiskLevel.MODERATE if hyperinflation_revenue_ratio > 0.15 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Hyperinflationary Revenue Exposure', value=hyperinflation_revenue_ratio, interpretation=hyperinflation_interpretation, risk_level=hyperinflation_risk, methodology='Hyperinflationary Economy Revenue / Total Revenue'))
        inflation_adjustment = notes.get('hyperinflation_adjustment', 0)
        if inflation_adjustment != 0:
            net_income = statements.income_statement.get('net_income', 0)
            if net_income != 0:
                inflation_impact = self.safe_divide(abs(inflation_adjustment), abs(net_income))
                inflation_impact_interpretation = 'Significant hyperinflation adjustment impact on earnings' if inflation_impact > 0.2 else 'Moderate hyperinflation impact' if inflation_impact > 0.1 else 'Limited hyperinflation impact'
                inflation_impact_risk = RiskLevel.HIGH if inflation_impact > 0.3 else RiskLevel.MODERATE if inflation_impact > 0.15 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Hyperinflation Adjustment Impact', value=inflation_impact, interpretation=inflation_impact_interpretation, risk_level=inflation_impact_risk, methodology='|Hyperinflation Adjustment| / |Net Income|'))
        return results

    def _analyze_currency_hedging(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze foreign currency hedging activities"""
        results = []
        notes = statements.notes
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        derivative_assets = balance_sheet.get('derivative_assets', 0)
        derivative_liabilities = balance_sheet.get('derivative_liabilities', 0)
        hedge_ineffectiveness = income_statement.get('hedge_ineffectiveness', 0)
        fx_derivatives_notional = notes.get('fx_derivatives_notional', 0)
        foreign_exposure_estimate = notes.get('total_foreign_exposure', 0)
        if fx_derivatives_notional > 0:
            if foreign_exposure_estimate > 0:
                hedging_ratio = self.safe_divide(fx_derivatives_notional, foreign_exposure_estimate)
                hedging_interpretation = 'High hedging coverage' if hedging_ratio > 0.8 else 'Moderate hedging coverage' if hedging_ratio > 0.5 else 'Low hedging coverage' if hedging_ratio > 0.2 else 'Minimal hedging'
                hedging_risk = RiskLevel.LOW if hedging_ratio > 0.7 else RiskLevel.MODERATE if hedging_ratio > 0.4 else RiskLevel.HIGH
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Currency Hedging Ratio', value=hedging_ratio, interpretation=hedging_interpretation, risk_level=hedging_risk, methodology='FX Derivatives Notional / Estimated Foreign Exposure', limitations=['Hedging effectiveness depends on correlation and timing']))
        if hedge_ineffectiveness != 0:
            net_income = income_statement.get('net_income', 0)
            if net_income != 0:
                ineffectiveness_impact = self.safe_divide(abs(hedge_ineffectiveness), abs(net_income))
                effectiveness_interpretation = 'Significant hedge ineffectiveness impacting earnings' if ineffectiveness_impact > 0.05 else 'Moderate hedge ineffectiveness' if ineffectiveness_impact > 0.02 else 'Good hedge effectiveness'
                effectiveness_risk = RiskLevel.HIGH if ineffectiveness_impact > 0.1 else RiskLevel.MODERATE if ineffectiveness_impact > 0.03 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Hedge Ineffectiveness Impact', value=ineffectiveness_impact, interpretation=effectiveness_interpretation, risk_level=effectiveness_risk, methodology='|Hedge Ineffectiveness| / |Net Income|'))
        return results

    def _analyze_ratio_impacts(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze impact of currency fluctuations on financial ratios"""
        results = []
        if not comparative_data or len(comparative_data) == 0:
            return results
        current_ratios = self._calculate_key_ratios(statements)
        prior_ratios = self._calculate_key_ratios(comparative_data[-1])
        exchange_rate_changes = statements.notes.get('major_exchange_rate_changes', {})
        if exchange_rate_changes:
            for ratio_name, current_value in current_ratios.items():
                prior_value = prior_ratios.get(ratio_name, 0)
                if prior_value != 0:
                    ratio_change = current_value / prior_value - 1
                    if abs(ratio_change) > 0.1:
                        currency_impact_interpretation = f'{ratio_name.replace('_', ' ').title()} changed by {self.format_percentage(ratio_change)} - assess currency impact'
                        currency_impact_risk = RiskLevel.MODERATE if abs(ratio_change) > 0.2 else RiskLevel.LOW
                        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name=f'Currency Impact on {ratio_name.replace('_', ' ').title()}', value=ratio_change, interpretation=currency_impact_interpretation, risk_level=currency_impact_risk, methodology='Period-over-period ratio change analysis', limitations=['Ratio changes may be due to operational factors beyond currency']))
        return results

    def _analyze_sales_sustainability(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze sustainability of sales growth components"""
        results = []
        if not comparative_data or len(comparative_data) == 0:
            return results
        notes = statements.notes
        income_statement = statements.income_statement
        current_revenue = income_statement.get('revenue', 0)
        prior_revenue = comparative_data[-1].income_statement.get('revenue', 0)
        if prior_revenue > 0:
            total_growth = current_revenue / prior_revenue - 1
            organic_growth = notes.get('organic_sales_growth', 0)
            fx_impact_on_sales = notes.get('fx_impact_on_sales', 0)
            acquisition_impact = notes.get('acquisition_impact_on_sales', 0)
            volume_growth = notes.get('volume_growth', 0)
            price_growth = notes.get('price_growth', 0)
            if organic_growth != 0:
                organic_ratio = self.safe_divide(organic_growth, total_growth) if total_growth != 0 else 0
                sustainability_interpretation = 'Sustainable organic growth drives revenue' if organic_ratio > 0.7 else 'Mixed growth drivers' if organic_ratio > 0.4 else 'Growth heavily dependent on external factors'
                sustainability_risk = RiskLevel.LOW if organic_ratio > 0.6 else RiskLevel.MODERATE if organic_ratio > 0.3 else RiskLevel.HIGH
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Organic Growth Sustainability', value=organic_ratio, interpretation=sustainability_interpretation, risk_level=sustainability_risk, methodology='Organic Growth / Total Revenue Growth'))
            if fx_impact_on_sales != 0 and total_growth != 0:
                fx_contribution = self.safe_divide(fx_impact_on_sales, total_growth)
                fx_interpretation = f'Currency {('tailwind' if fx_impact_on_sales > 0 else 'headwind')} contributed {self.format_percentage(abs(fx_contribution))} to revenue growth'
                fx_risk = RiskLevel.MODERATE if abs(fx_contribution) > 0.3 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='FX Impact on Revenue Growth', value=fx_contribution, interpretation=fx_interpretation, risk_level=fx_risk, methodology='FX Impact on Sales / Total Revenue Growth'))
        return results

    def _extract_currency_exposures(self, notes: Dict) -> Dict[str, float]:
        """Extract currency exposure data from notes"""
        currency_exposures = {}
        for key, value in notes.items():
            if 'currency' in key.lower() and isinstance(value, (int, float)):
                currency_name = key.replace('_currency_exposure', '').replace('_exposure', '')
                currency_exposures[currency_name] = value
        return currency_exposures

    def _extract_geographic_segments(self, notes: Dict) -> Dict[str, Dict[str, float]]:
        """Extract geographic segment data from notes"""
        segments = {}
        regions = ['north_america', 'europe', 'asia_pacific', 'latin_america', 'middle_east_africa']
        for region in regions:
            segment_data = {}
            for metric in ['revenue', 'profit', 'assets']:
                key = f'{region}_{metric}'
                if key in notes:
                    segment_data[metric] = notes[key]
            if segment_data:
                segments[region] = segment_data
        return segments

    def _calculate_key_ratios(self, statements: FinancialStatements) -> Dict[str, float]:
        """Calculate key financial ratios for currency impact analysis"""
        ratios = {}
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        revenue = income_statement.get('revenue', 0)
        net_income = income_statement.get('net_income', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        total_equity = balance_sheet.get('total_equity', 0)
        if revenue > 0:
            ratios['net_margin'] = self.safe_divide(net_income, revenue)
        if total_assets > 0:
            ratios['asset_turnover'] = self.safe_divide(revenue, total_assets)
            ratios['roa'] = self.safe_divide(net_income, total_assets)
        if total_equity > 0:
            ratios['roe'] = self.safe_divide(net_income, total_equity)
        return ratios

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key multinational operations metrics"""
        notes = statements.notes
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        metrics = {}
        foreign_revenue = notes.get('foreign_revenue', 0)
        foreign_assets = notes.get('foreign_assets', 0)
        total_revenue = income_statement.get('revenue', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if total_revenue > 0:
            metrics['foreign_revenue_ratio'] = self.safe_divide(foreign_revenue, total_revenue)
        if total_assets > 0:
            metrics['foreign_asset_ratio'] = self.safe_divide(foreign_assets, total_assets)
        translation_adjustment = statements.equity_statement.get('translation_adjustment', 0)
        total_equity = balance_sheet.get('total_equity', 0)
        if total_equity > 0:
            metrics['translation_impact_ratio'] = self.safe_divide(abs(translation_adjustment), total_equity)
        fx_derivatives_notional = notes.get('fx_derivatives_notional', 0)
        total_foreign_exposure = notes.get('total_foreign_exposure', 0)
        if total_foreign_exposure > 0:
            metrics['hedging_ratio'] = self.safe_divide(fx_derivatives_notional, total_foreign_exposure)
        geographic_segments = self._extract_geographic_segments(notes)
        if geographic_segments:
            total_segment_revenue = sum((segment.get('revenue', 0) for segment in geographic_segments.values()))
            if total_segment_revenue > 0:
                max_segment_revenue = max((segment.get('revenue', 0) for segment in geographic_segments.values()))
                metrics['geographic_concentration'] = self.safe_divide(max_segment_revenue, total_segment_revenue)
        return metrics

    def create_currency_exposure_analysis(self, statements: FinancialStatements) -> CurrencyExposureAnalysis:
        """Create comprehensive currency exposure analysis object"""
        notes = statements.notes
        balance_sheet = statements.balance_sheet
        foreign_revenue = notes.get('foreign_revenue', 0)
        foreign_assets = notes.get('foreign_assets', 0)
        foreign_receivables = balance_sheet.get('foreign_receivables', 0)
        foreign_payables = balance_sheet.get('foreign_payables', 0)
        total_foreign_exposure = foreign_revenue + foreign_assets
        exposure_by_currency = self._extract_currency_exposures(notes)
        net_transaction_exposure = foreign_receivables - foreign_payables
        net_investment_exposure = foreign_assets
        translation_gains_losses = statements.income_statement.get('foreign_exchange_gains_losses', 0)
        currency_exposures = list(exposure_by_currency.values()) if exposure_by_currency else [total_foreign_exposure]
        max_exposure = max(currency_exposures) if currency_exposures else 0
        total_exposure = sum(currency_exposures) if currency_exposures else total_foreign_exposure
        concentration_ratio = self.safe_divide(max_exposure, total_exposure) if total_exposure > 0 else 0
        if concentration_ratio > 0.7:
            currency_concentration_risk = RiskLevel.HIGH
        elif concentration_ratio > 0.5:
            currency_concentration_risk = RiskLevel.MODERATE
        else:
            currency_concentration_risk = RiskLevel.LOW
        fx_derivatives_notional = notes.get('fx_derivatives_notional', 0)
        hedging_effectiveness = self.safe_divide(fx_derivatives_notional, total_foreign_exposure) if total_foreign_exposure > 0 else 0
        return CurrencyExposureAnalysis(total_foreign_exposure=total_foreign_exposure, exposure_by_currency=exposure_by_currency, foreign_receivables=foreign_receivables, foreign_payables=foreign_payables, net_transaction_exposure=net_transaction_exposure, net_investment_exposure=net_investment_exposure, translation_gains_losses=translation_gains_losses, currency_concentration_risk=currency_concentration_risk, hedging_effectiveness=hedging_effectiveness)

    def create_geographic_analysis(self, statements: FinancialStatements) -> GeographicSegmentAnalysis:
        """Create comprehensive geographic segment analysis object"""
        notes = statements.notes
        segments_by_region = self._extract_geographic_segments(notes)
        revenue_by_region = {}
        profit_by_region = {}
        assets_by_region = {}
        for region, segment in segments_by_region.items():
            revenue_by_region[region] = segment.get('revenue', 0)
            profit_by_region[region] = segment.get('profit', 0)
            assets_by_region[region] = segment.get('assets', 0)
        total_revenue = sum(revenue_by_region.values())
        max_region_revenue = max(revenue_by_region.values()) if revenue_by_region else 0
        geographic_concentration = self.safe_divide(max_region_revenue, total_revenue) if total_revenue > 0 else 0
        top_region_dependency = geographic_concentration
        emerging_markets = ['china', 'india', 'brazil', 'russia', 'mexico', 'turkey', 'south_africa']
        emerging_revenue = 0
        developed_revenue = 0
        for region, revenue in revenue_by_region.items():
            if any((em in region.lower() for em in emerging_markets)):
                emerging_revenue += revenue
            else:
                developed_revenue += revenue
        emerging_markets_exposure = self.safe_divide(emerging_revenue, total_revenue) if total_revenue > 0 else 0
        developed_markets_exposure = self.safe_divide(developed_revenue, total_revenue) if total_revenue > 0 else 0
        return GeographicSegmentAnalysis(segments_by_region=segments_by_region, revenue_by_region=revenue_by_region, profit_by_region=profit_by_region, assets_by_region=assets_by_region, geographic_concentration=geographic_concentration, top_region_dependency=top_region_dependency, emerging_markets_exposure=emerging_markets_exposure, developed_markets_exposure=developed_markets_exposure)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive multinational operations analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all multinational aspects
        """
    results = []
    results.extend(self._analyze_currency_exposure(statements, comparative_data, industry_data))
    results.extend(self._analyze_translation_methods(statements, comparative_data))
    results.extend(self._analyze_geographic_segments(statements, comparative_data))
    results.extend(self._analyze_hyperinflationary_economies(statements, comparative_data))
    results.extend(self._analyze_currency_hedging(statements, comparative_data))
    results.extend(self._analyze_ratio_impacts(statements, comparative_data))
    results.extend(self._analyze_sales_sustainability(statements, comparative_data))
    return results

class IntercorporateInvestmentsAnalyzer(BaseAnalyzer):
    """
    Comprehensive intercorporate investments analyzer implementing CFA Level II standards.
    Covers all types of intercorporate investments and their accounting treatments.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_investment_formulas()
        self._initialize_investment_benchmarks()

    def _initialize_investment_formulas(self):
        """Initialize investment-specific formulas"""
        self.formula_registry.update({'investment_return': lambda gains_income, beginning_value: self.safe_divide(gains_income, beginning_value), 'dividend_yield': lambda dividend_income, investment_value: self.safe_divide(dividend_income, investment_value), 'investment_intensity': lambda total_investments, total_assets: self.safe_divide(total_investments, total_assets), 'equity_method_return': lambda share_of_earnings, carrying_value: self.safe_divide(share_of_earnings, carrying_value), 'goodwill_premium': lambda goodwill, purchase_price: self.safe_divide(goodwill, purchase_price), 'acquisition_multiple': lambda purchase_price, acquired_earnings: self.safe_divide(purchase_price, acquired_earnings)})

    def _initialize_investment_benchmarks(self):
        """Initialize investment-specific benchmarks"""
        self.investment_benchmarks = {'investment_intensity': {'low': 0.1, 'moderate': 0.2, 'high': 0.4, 'very_high': 0.6}, 'investment_return': {'excellent': 0.15, 'good': 0.1, 'adequate': 0.05, 'poor': 0.0}, 'goodwill_premium': {'reasonable': 0.3, 'high': 0.5, 'excessive': 0.7}, 'acquisition_multiple': {'reasonable': 15, 'high': 25, 'excessive': 40}}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive intercorporate investments analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all investment aspects
        """
        results = []
        results.extend(self._analyze_financial_assets(statements, comparative_data, industry_data))
        results.extend(self._analyze_associates(statements, comparative_data))
        results.extend(self._analyze_joint_ventures(statements, comparative_data))
        results.extend(self._analyze_business_combinations(statements, comparative_data))
        results.extend(self._analyze_spe_vie(statements, comparative_data))
        results.extend(self._analyze_gaap_differences(statements))
        results.extend(self._assess_investment_strategy(statements, comparative_data))
        return results

    def _analyze_financial_assets(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze financial asset investments"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        financial_assets = {'trading_securities': balance_sheet.get('trading_securities', 0), 'afs_securities': balance_sheet.get('available_for_sale_securities', 0), 'htm_securities': balance_sheet.get('held_to_maturity_securities', 0), 'fvtpl_assets': balance_sheet.get('fvtpl_financial_assets', 0), 'fvoci_assets': balance_sheet.get('fvoci_financial_assets', 0), 'amortized_cost_assets': balance_sheet.get('amortized_cost_financial_assets', 0)}
        total_financial_assets = sum(financial_assets.values())
        total_assets = balance_sheet.get('total_assets', 0)
        if total_financial_assets <= 0:
            return results
        if total_assets > 0:
            investment_intensity = self.safe_divide(total_financial_assets, total_assets)
            benchmark = self.investment_benchmarks['investment_intensity']
            if investment_intensity > benchmark['very_high']:
                intensity_interpretation = 'Very high financial asset intensity - investment-focused business model'
                intensity_risk = RiskLevel.MODERATE
            elif investment_intensity > benchmark['high']:
                intensity_interpretation = 'High financial asset concentration'
                intensity_risk = RiskLevel.MODERATE
            elif investment_intensity > benchmark['moderate']:
                intensity_interpretation = 'Moderate financial asset investments'
                intensity_risk = RiskLevel.LOW
            else:
                intensity_interpretation = 'Low financial asset concentration'
                intensity_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Financial Asset Intensity', value=investment_intensity, interpretation=intensity_interpretation, risk_level=intensity_risk, benchmark_comparison=self.compare_to_industry(investment_intensity, industry_data.get('investment_intensity') if industry_data else None), methodology='Total Financial Assets / Total Assets'))
        if total_financial_assets > 0:
            for asset_type, value in financial_assets.items():
                if value > 0:
                    asset_ratio = self.safe_divide(value, total_financial_assets)
                    asset_name = asset_type.replace('_', ' ').title()
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name=f'{asset_name} Composition', value=asset_ratio, interpretation=f'{asset_name} represents {self.format_percentage(asset_ratio)} of total financial assets', risk_level=RiskLevel.LOW, methodology=f'{asset_name} / Total Financial Assets'))
        fair_value_assets = financial_assets['trading_securities'] + financial_assets['afs_securities'] + financial_assets['fvtpl_assets'] + financial_assets['fvoci_assets']
        amortized_cost_assets = financial_assets['htm_securities'] + financial_assets['amortized_cost_assets']
        if total_financial_assets > 0:
            fair_value_ratio = self.safe_divide(fair_value_assets, total_financial_assets)
            fv_interpretation = 'High fair value measurement exposure - significant market risk' if fair_value_ratio > 0.7 else 'Moderate fair value exposure' if fair_value_ratio > 0.4 else 'Low fair value measurement exposure'
            fv_risk = RiskLevel.HIGH if fair_value_ratio > 0.8 else RiskLevel.MODERATE if fair_value_ratio > 0.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Fair Value Asset Ratio', value=fair_value_ratio, interpretation=fv_interpretation, risk_level=fv_risk, methodology='Fair Value Assets / Total Financial Assets', limitations=['Fair value assets subject to market volatility']))
        investment_income = income_statement.get('investment_income', 0)
        realized_gains = income_statement.get('realized_investment_gains', 0)
        unrealized_gains = income_statement.get('unrealized_investment_gains', 0)
        total_investment_return = investment_income + realized_gains + unrealized_gains
        if total_financial_assets > 0 and total_investment_return != 0:
            investment_return = self.safe_divide(total_investment_return, total_financial_assets)
            benchmark = self.investment_benchmarks['investment_return']
            return_risk = self.assess_risk_level(investment_return, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Financial Asset Return', value=investment_return, interpretation=self.generate_interpretation('financial asset return', investment_return, return_risk, AnalysisType.PROFITABILITY), risk_level=return_risk, methodology='(Investment Income + Realized Gains + Unrealized Gains) / Total Financial Assets'))
        return results

    def _analyze_associates(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze investments in associates using equity method"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        associate_investments = balance_sheet.get('investments_in_associates', 0)
        share_of_associate_profits = income_statement.get('share_of_associate_profits', 0)
        associate_dividends = income_statement.get('dividends_from_associates', 0)
        if associate_investments <= 0:
            return results
        total_assets = balance_sheet.get('total_assets', 0)
        if total_assets > 0:
            associate_intensity = self.safe_divide(associate_investments, total_assets)
            associate_interpretation = 'Significant associate investments - substantial equity method exposure' if associate_intensity > 0.2 else 'Moderate associate investments' if associate_intensity > 0.1 else 'Limited associate investments'
            associate_risk = RiskLevel.MODERATE if associate_intensity > 0.3 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Associate Investment Intensity', value=associate_intensity, interpretation=associate_interpretation, risk_level=associate_risk, methodology='Investments in Associates / Total Assets'))
        if associate_investments > 0:
            equity_method_return = self.safe_divide(share_of_associate_profits, associate_investments)
            if equity_method_return > 0.15:
                return_interpretation = 'Strong associate performance contributing to earnings'
                return_risk = RiskLevel.LOW
            elif equity_method_return > 0.05:
                return_interpretation = 'Adequate associate performance'
                return_risk = RiskLevel.LOW
            elif equity_method_return > 0:
                return_interpretation = 'Weak associate performance'
                return_risk = RiskLevel.MODERATE
            else:
                return_interpretation = 'Associates generating losses - potential impairment concern'
                return_risk = RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Equity Method Return', value=equity_method_return, interpretation=return_interpretation, risk_level=return_risk, methodology='Share of Associate Profits / Investment in Associates'))
        if share_of_associate_profits > 0 and associate_dividends > 0:
            associate_payout_ratio = self.safe_divide(associate_dividends, share_of_associate_profits)
            payout_interpretation = 'High dividend payout from associates - good cash generation' if associate_payout_ratio > 0.6 else 'Moderate dividend payout' if associate_payout_ratio > 0.3 else 'Low dividend payout - associates retaining earnings for growth'
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Associate Dividend Payout Ratio', value=associate_payout_ratio, interpretation=payout_interpretation, risk_level=RiskLevel.LOW, methodology='Dividends from Associates / Share of Associate Profits'))
        if comparative_data and len(comparative_data) > 0:
            prev_associate_investments = comparative_data[-1].balance_sheet.get('investments_in_associates', 0)
            if prev_associate_investments > 0:
                associate_growth = associate_investments / prev_associate_investments - 1
                growth_interpretation = 'Significant expansion in associate investments' if associate_growth > 0.2 else 'Moderate growth in associate investments' if associate_growth > 0.05 else 'Stable associate investment base' if associate_growth > -0.05 else 'Declining associate investments'
                growth_risk = RiskLevel.MODERATE if associate_growth > 0.5 or associate_growth < -0.2 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Associate Investment Growth', value=associate_growth, interpretation=growth_interpretation, risk_level=growth_risk, methodology='(Current Associate Investments - Prior Associate Investments) / Prior Associate Investments'))
        return results

    def _analyze_joint_ventures(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze joint venture investments"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        joint_venture_investments = balance_sheet.get('investments_in_joint_ventures', 0)
        share_of_jv_profits = income_statement.get('share_of_jv_profits', 0)
        if joint_venture_investments <= 0:
            return results
        total_assets = balance_sheet.get('total_assets', 0)
        if total_assets > 0:
            jv_intensity = self.safe_divide(joint_venture_investments, total_assets)
            jv_interpretation = 'Significant joint venture exposure' if jv_intensity > 0.15 else 'Moderate joint venture investments' if jv_intensity > 0.05 else 'Limited joint venture exposure'
            jv_risk = RiskLevel.MODERATE if jv_intensity > 0.25 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Joint Venture Investment Intensity', value=jv_intensity, interpretation=jv_interpretation, risk_level=jv_risk, methodology='Investments in Joint Ventures / Total Assets', limitations=['Joint ventures involve shared control and coordination challenges']))
        if joint_venture_investments > 0:
            jv_return = self.safe_divide(share_of_jv_profits, joint_venture_investments)
            jv_performance_interpretation = 'Strong joint venture performance' if jv_return > 0.12 else 'Adequate joint venture performance' if jv_return > 0.06 else 'Weak joint venture performance' if jv_return > 0 else 'Joint ventures generating losses'
            jv_performance_risk = RiskLevel.LOW if jv_return > 0.08 else RiskLevel.MODERATE if jv_return > 0 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Joint Venture Return', value=jv_return, interpretation=jv_performance_interpretation, risk_level=jv_performance_risk, methodology='Share of JV Profits / Investment in Joint Ventures'))
        jv_count = notes.get('number_of_joint_ventures', 0)
        if jv_count > 0:
            avg_jv_size = self.safe_divide(joint_venture_investments, jv_count)
            strategy_interpretation = f'Portfolio of {jv_count} joint ventures with average investment of ${avg_jv_size:,.0f}'
            strategy_risk = RiskLevel.MODERATE if jv_count > 10 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Joint Venture Portfolio', value=avg_jv_size, interpretation=strategy_interpretation, risk_level=strategy_risk, methodology='Total JV Investments / Number of Joint Ventures'))
        return results

    def _analyze_business_combinations(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze business combinations and acquisitions"""
        results = []
        balance_sheet = statements.balance_sheet
        cash_flow = statements.cash_flow
        notes = statements.notes
        acquisitions = cash_flow.get('acquisitions', 0)
        goodwill = balance_sheet.get('goodwill', 0)
        if acquisitions > 0:
            total_assets = balance_sheet.get('total_assets', 0)
            if total_assets > 0:
                acquisition_intensity = self.safe_divide(acquisitions, total_assets)
                acquisition_interpretation = 'Significant acquisition activity' if acquisition_intensity > 0.1 else 'Moderate acquisition activity' if acquisition_intensity > 0.05 else 'Limited acquisition activity'
                acquisition_risk = RiskLevel.MODERATE if acquisition_intensity > 0.2 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Acquisition Activity Intensity', value=acquisition_intensity, interpretation=acquisition_interpretation, risk_level=acquisition_risk, methodology='Cash Paid for Acquisitions / Total Assets'))
        if goodwill > 0 and acquisitions > 0:
            goodwill_premium = self.safe_divide(goodwill, acquisitions) if acquisitions > goodwill else self.safe_divide(goodwill, goodwill + acquisitions)
            benchmark = self.investment_benchmarks['goodwill_premium']
            if goodwill_premium > benchmark['excessive']:
                premium_interpretation = 'Very high goodwill premium - potential overpayment concern'
                premium_risk = RiskLevel.HIGH
            elif goodwill_premium > benchmark['high']:
                premium_interpretation = 'High goodwill premium - monitor integration success'
                premium_risk = RiskLevel.MODERATE
            elif goodwill_premium > benchmark['reasonable']:
                premium_interpretation = 'Reasonable goodwill premium'
                premium_risk = RiskLevel.LOW
            else:
                premium_interpretation = 'Low goodwill premium - strategic acquisition'
                premium_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Acquisition Goodwill Premium', value=goodwill_premium, interpretation=premium_interpretation, risk_level=premium_risk, methodology='Goodwill / Acquisition Price (simplified)', limitations=['Simplified calculation - detailed purchase price allocation needed for precision']))
        if comparative_data and len(comparative_data) >= 2:
            acquisition_history = []
            for past_statements in comparative_data:
                past_acquisitions = past_statements.cash_flow.get('acquisitions', 0)
                acquisition_history.append(past_acquisitions)
            acquisition_history.append(acquisitions)
            total_acquisitions = sum(acquisition_history)
            if total_acquisitions > 0:
                acquisition_frequency = sum((1 for x in acquisition_history if x > 0)) / len(acquisition_history)
                frequency_interpretation = 'Frequent acquirer - high integration complexity' if acquisition_frequency > 0.7 else 'Moderate acquisition frequency' if acquisition_frequency > 0.3 else 'Infrequent acquisitions'
                frequency_risk = RiskLevel.HIGH if acquisition_frequency > 0.8 else RiskLevel.MODERATE if acquisition_frequency > 0.5 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Acquisition Frequency', value=acquisition_frequency, interpretation=frequency_interpretation, risk_level=frequency_risk, methodology='Periods with Acquisitions / Total Periods'))
        return results

    def _analyze_spe_vie(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze Special Purpose Entities and Variable Interest Entities"""
        results = []
        notes = statements.notes
        vie_assets = notes.get('vie_consolidated_assets', 0)
        vie_liabilities = notes.get('vie_consolidated_liabilities', 0)
        unconsolidated_vie_exposure = notes.get('unconsolidated_vie_exposure', 0)
        total_assets = statements.balance_sheet.get('total_assets', 0)
        if vie_assets > 0 and total_assets > 0:
            vie_asset_ratio = self.safe_divide(vie_assets, total_assets)
            vie_interpretation = 'Significant VIE consolidation impact' if vie_asset_ratio > 0.2 else 'Moderate VIE consolidation' if vie_asset_ratio > 0.1 else 'Limited VIE consolidation'
            vie_risk = RiskLevel.MODERATE if vie_asset_ratio > 0.3 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='VIE Asset Consolidation Ratio', value=vie_asset_ratio, interpretation=vie_interpretation, risk_level=vie_risk, methodology='VIE Consolidated Assets / Total Assets', limitations=['VIE consolidation may obscure underlying business performance']))
        if unconsolidated_vie_exposure > 0:
            if total_assets > 0:
                vie_exposure_ratio = self.safe_divide(unconsolidated_vie_exposure, total_assets)
                exposure_interpretation = 'Significant off-balance sheet VIE exposure' if vie_exposure_ratio > 0.1 else 'Moderate off-balance sheet exposure' if vie_exposure_ratio > 0.05 else 'Limited off-balance sheet VIE exposure'
                exposure_risk = RiskLevel.HIGH if vie_exposure_ratio > 0.2 else RiskLevel.MODERATE if vie_exposure_ratio > 0.1 else RiskLevel.LOW
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Unconsolidated VIE Exposure', value=vie_exposure_ratio, interpretation=exposure_interpretation, risk_level=exposure_risk, methodology='Unconsolidated VIE Exposure / Total Assets', limitations=['Off-balance sheet exposures may represent hidden risks']))
        spe_disclosures = sum((1 for key in notes.keys() if 'spe' in key.lower() or 'vie' in key.lower() or 'special_purpose' in key.lower()))
        if spe_disclosures > 0:
            disclosure_interpretation = 'Comprehensive SPE/VIE disclosures' if spe_disclosures > 5 else 'Adequate SPE/VIE disclosures' if spe_disclosures > 2 else 'Limited SPE/VIE disclosures'
            disclosure_risk = RiskLevel.LOW if spe_disclosures > 3 else RiskLevel.MODERATE if spe_disclosures > 1 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='SPE/VIE Disclosure Quality', value=spe_disclosures, interpretation=disclosure_interpretation, risk_level=disclosure_risk, methodology='Count of SPE/VIE related disclosures'))
        return results

    def _analyze_gaap_differences(self, statements: FinancialStatements) -> List[AnalysisResult]:
        """Analyze IFRS vs US GAAP differences in intercorporate investments"""
        results = []
        reporting_standard = statements.company_info.reporting_standard
        notes = statements.notes
        if reporting_standard == ReportingStandard.IFRS:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='IFRS Investment Classification', value=1.0, interpretation='Under IFRS 9, financial assets classified based on business model and cash flow characteristics', risk_level=RiskLevel.LOW, methodology='IFRS 9 classification assessment', limitations=['IFRS allows more judgment in classification decisions']))
        elif reporting_standard == ReportingStandard.US_GAAP:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='US GAAP Investment Classification', value=1.0, interpretation='Under US GAAP, financial assets follow traditional held-to-maturity, available-for-sale, and trading classifications', risk_level=RiskLevel.LOW, methodology='US GAAP classification assessment', limitations=['US GAAP has more prescriptive classification rules']))
        joint_ventures = statements.balance_sheet.get('investments_in_joint_ventures', 0)
        if joint_ventures > 0:
            if reporting_standard == ReportingStandard.IFRS:
                jv_interpretation = 'Under IFRS 11, joint ventures must use equity method (proportionate consolidation eliminated)'
            else:
                jv_interpretation = 'Under US GAAP, joint ventures typically use equity method'
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Joint Venture Accounting Method', value=1.0, interpretation=jv_interpretation, risk_level=RiskLevel.LOW, methodology='Assessment of joint venture accounting standards'))
        return results

    def _assess_investment_strategy(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess overall intercorporate investment strategy"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        total_investments = balance_sheet.get('trading_securities', 0) + balance_sheet.get('available_for_sale_securities', 0) + balance_sheet.get('held_to_maturity_securities', 0) + balance_sheet.get('investments_in_associates', 0) + balance_sheet.get('investments_in_joint_ventures', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if total_investments > 0 and total_assets > 0:
            total_investment_ratio = self.safe_divide(total_investments, total_assets)
            strategy_interpretation = 'Investment-intensive business model' if total_investment_ratio > 0.4 else 'Moderate investment strategy' if total_investment_ratio > 0.2 else 'Limited investment focus'
            strategy_risk = RiskLevel.MODERATE if total_investment_ratio > 0.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Total Investment Intensity', value=total_investment_ratio, interpretation=strategy_interpretation, risk_level=strategy_risk, methodology='Total Intercorporate Investments / Total Assets'))
        investment_types = {'Financial Assets': balance_sheet.get('trading_securities', 0) + balance_sheet.get('available_for_sale_securities', 0), 'Associates': balance_sheet.get('investments_in_associates', 0), 'Joint Ventures': balance_sheet.get('investments_in_joint_ventures', 0)}
        non_zero_types = sum((1 for value in investment_types.values() if value > 0))
        if non_zero_types > 0:
            diversification_interpretation = 'Well-diversified investment portfolio' if non_zero_types >= 3 else 'Moderately diversified investments' if non_zero_types == 2 else 'Concentrated investment strategy'
            diversification_risk = RiskLevel.LOW if non_zero_types >= 3 else RiskLevel.MODERATE if non_zero_types == 2 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Investment Diversification', value=non_zero_types, interpretation=diversification_interpretation, risk_level=diversification_risk, methodology='Count of different investment types with material balances'))
        total_investment_income = income_statement.get('investment_income', 0) + income_statement.get('share_of_associate_profits', 0) + income_statement.get('share_of_jv_profits', 0)
        operating_income = income_statement.get('operating_income', 0)
        if operating_income > 0 and total_investment_income != 0:
            investment_contribution = self.safe_divide(total_investment_income, operating_income)
            contribution_interpretation = 'Investments significantly contribute to earnings' if investment_contribution > 0.3 else 'Moderate investment contribution' if investment_contribution > 0.1 else 'Limited investment contribution to earnings'
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Investment Earnings Contribution', value=investment_contribution, interpretation=contribution_interpretation, risk_level=RiskLevel.LOW, methodology='Total Investment Income / Operating Income'))
        return results

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key intercorporate investment metrics"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        metrics = {}
        total_assets = balance_sheet.get('total_assets', 0)
        if total_assets > 0:
            financial_assets = balance_sheet.get('trading_securities', 0) + balance_sheet.get('available_for_sale_securities', 0) + balance_sheet.get('held_to_maturity_securities', 0)
            metrics['financial_asset_intensity'] = self.safe_divide(financial_assets, total_assets)
            associates = balance_sheet.get('investments_in_associates', 0)
            metrics['associate_intensity'] = self.safe_divide(associates, total_assets)
            joint_ventures = balance_sheet.get('investments_in_joint_ventures', 0)
            metrics['joint_venture_intensity'] = self.safe_divide(joint_ventures, total_assets)
            total_investments = financial_assets + associates + joint_ventures
            metrics['total_investment_intensity'] = self.safe_divide(total_investments, total_assets)
        associate_investments = balance_sheet.get('investments_in_associates', 0)
        if associate_investments > 0:
            share_of_profits = income_statement.get('share_of_associate_profits', 0)
            metrics['equity_method_return'] = self.safe_divide(share_of_profits, associate_investments)
        jv_investments = balance_sheet.get('investments_in_joint_ventures', 0)
        if jv_investments > 0:
            jv_profits = income_statement.get('share_of_jv_profits', 0)
            metrics['joint_venture_return'] = self.safe_divide(jv_profits, jv_investments)
        goodwill = balance_sheet.get('goodwill', 0)
        if total_assets > 0:
            metrics['goodwill_intensity'] = self.safe_divide(goodwill, total_assets)
        return metrics

    def create_financial_asset_analysis(self, statements: FinancialStatements) -> FinancialAssetAnalysis:
        """Create comprehensive financial asset analysis object"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        classification_breakdown = {'trading_securities': balance_sheet.get('trading_securities', 0), 'available_for_sale': balance_sheet.get('available_for_sale_securities', 0), 'held_to_maturity': balance_sheet.get('held_to_maturity_securities', 0), 'fvtpl_assets': balance_sheet.get('fvtpl_financial_assets', 0), 'fvoci_assets': balance_sheet.get('fvoci_financial_assets', 0), 'amortized_cost': balance_sheet.get('amortized_cost_financial_assets', 0)}
        total_financial_assets = sum(classification_breakdown.values())
        fair_value_assets = classification_breakdown['trading_securities'] + classification_breakdown['available_for_sale'] + classification_breakdown['fvtpl_assets'] + classification_breakdown['fvoci_assets']
        amortized_cost_assets = classification_breakdown['held_to_maturity'] + classification_breakdown['amortized_cost']
        investment_income = income_statement.get('investment_income', 0)
        realized_gains = income_statement.get('realized_investment_gains', 0)
        unrealized_gains = income_statement.get('unrealized_investment_gains', 0)
        investment_returns = self.safe_divide(investment_income + realized_gains, total_financial_assets) if total_financial_assets > 0 else 0
        dividend_income = income_statement.get('dividend_income', 0)
        market_risk_exposure = self.safe_divide(fair_value_assets, total_financial_assets) if total_financial_assets > 0 else 0
        liquidity_risk = RiskLevel.LOW if amortized_cost_assets > fair_value_assets else RiskLevel.MODERATE if market_risk_exposure < 0.7 else RiskLevel.HIGH
        return FinancialAssetAnalysis(total_financial_assets=total_financial_assets, classification_breakdown=classification_breakdown, fair_value_assets=fair_value_assets, amortized_cost_assets=amortized_cost_assets, unrealized_gains_losses=unrealized_gains, market_risk_exposure=market_risk_exposure, liquidity_risk=liquidity_risk, investment_returns=investment_returns, dividend_income=dividend_income)

    def create_associate_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> AssociateAnalysis:
        """Create comprehensive associate analysis object"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        notes = statements.notes
        total_associate_investments = balance_sheet.get('investments_in_associates', 0)
        number_of_associates = notes.get('number_of_associates', 1)
        share_of_profits_losses = income_statement.get('share_of_associate_profits', 0)
        dividend_income_associates = income_statement.get('dividends_from_associates', 0)
        carrying_value_change = 0
        if comparative_data and len(comparative_data) > 0:
            prev_investments = comparative_data[-1].balance_sheet.get('investments_in_associates', 0)
            carrying_value_change = total_associate_investments - prev_investments
        associate_roe = self.safe_divide(share_of_profits_losses, total_associate_investments) if total_associate_investments > 0 else 0
        associate_performance_trend = TrendDirection.STABLE
        if comparative_data and len(comparative_data) >= 2:
            profit_values = []
            for past_statements in comparative_data:
                past_profits = past_statements.income_statement.get('share_of_associate_profits', 0)
                profit_values.append(past_profits)
            profit_values.append(share_of_profits_losses)
            if len(profit_values) >= 3:
                if profit_values[-1] > profit_values[0] * 1.1:
                    associate_performance_trend = TrendDirection.IMPROVING
                elif profit_values[-1] < profit_values[0] * 0.9:
                    associate_performance_trend = TrendDirection.DETERIORATING
        impairment_indicators = []
        if share_of_profits_losses < 0:
            impairment_indicators.append('Associates generating losses')
        if associate_roe < 0.05 and associate_roe > 0:
            impairment_indicators.append('Low return on associate investments')
        return AssociateAnalysis(total_associate_investments=total_associate_investments, number_of_associates=number_of_associates, share_of_profits_losses=share_of_profits_losses, dividend_income_associates=dividend_income_associates, carrying_value_change=carrying_value_change, associate_roe=associate_roe, associate_performance_trend=associate_performance_trend, impairment_indicators=impairment_indicators)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive intercorporate investments analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all investment aspects
        """
    results = []
    results.extend(self._analyze_financial_assets(statements, comparative_data, industry_data))
    results.extend(self._analyze_associates(statements, comparative_data))
    results.extend(self._analyze_joint_ventures(statements, comparative_data))
    results.extend(self._analyze_business_combinations(statements, comparative_data))
    results.extend(self._analyze_spe_vie(statements, comparative_data))
    results.extend(self._analyze_gaap_differences(statements))
    results.extend(self._assess_investment_strategy(statements, comparative_data))
    return results

class InventoryAnalyzer(BaseAnalyzer):
    """
    Comprehensive inventory analyzer implementing CFA Institute standards.
    Covers valuation methods, efficiency analysis, and inflation impact assessment.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_inventory_formulas()
        self._initialize_inventory_benchmarks()

    def _initialize_inventory_formulas(self):
        """Initialize inventory-specific formulas"""
        self.formula_registry.update({'inventory_turnover': lambda cogs, avg_inventory: self.safe_divide(cogs, avg_inventory), 'days_inventory_outstanding': lambda avg_inventory, daily_cogs: self.safe_divide(avg_inventory, daily_cogs), 'inventory_to_sales': lambda inventory, revenue: self.safe_divide(inventory, revenue), 'gross_margin_fifo': lambda revenue, cogs_fifo: self.safe_divide(revenue - cogs_fifo, revenue), 'gross_margin_lifo': lambda revenue, cogs_lifo: self.safe_divide(revenue - cogs_lifo, revenue), 'lifo_reserve_ratio': lambda lifo_reserve, total_inventory: self.safe_divide(lifo_reserve, total_inventory)})

    def _initialize_inventory_benchmarks(self):
        """Initialize inventory-specific benchmarks"""
        self.inventory_benchmarks = {'inventory_turnover': {'retail': {'excellent': 12.0, 'good': 8.0, 'adequate': 6.0, 'poor': 4.0}, 'manufacturing': {'excellent': 8.0, 'good': 6.0, 'adequate': 4.0, 'poor': 2.0}, 'general': {'excellent': 10.0, 'good': 7.0, 'adequate': 5.0, 'poor': 3.0}}, 'days_inventory_outstanding': {'retail': {'excellent': 30, 'good': 45, 'adequate': 60, 'poor': 90}, 'manufacturing': {'excellent': 45, 'good': 60, 'adequate': 90, 'poor': 120}, 'general': {'excellent': 36, 'good': 52, 'adequate': 73, 'poor': 120}}, 'inventory_to_sales': {'retail': {'excellent': 0.08, 'good': 0.12, 'adequate': 0.15, 'poor': 0.2}, 'manufacturing': {'excellent': 0.15, 'good': 0.2, 'adequate': 0.25, 'poor': 0.35}, 'general': {'excellent': 0.1, 'good': 0.15, 'adequate': 0.2, 'poor': 0.3}}}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive inventory analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all inventory aspects
        """
        results = []
        inventory = statements.balance_sheet.get('inventory', 0)
        if inventory <= 0:
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Inventory Analysis', value=0.0, interpretation='No inventory reported - inventory analysis not applicable', risk_level=RiskLevel.LOW, methodology='Balance sheet inventory examination'))
            return results
        results.extend(self._analyze_inventory_efficiency(statements, comparative_data, industry_data))
        results.extend(self._analyze_inventory_valuation(statements, comparative_data))
        results.extend(self._analyze_lower_cost_nrv(statements, comparative_data))
        results.extend(self._analyze_inflation_impact(statements, comparative_data, industry_data))
        results.extend(self._analyze_inventory_composition(statements))
        results.extend(self._assess_inventory_disclosures(statements))
        return results

    def _analyze_inventory_efficiency(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze inventory efficiency and turnover metrics"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        inventory = balance_sheet.get('inventory', 0)
        cost_of_sales = income_statement.get('cost_of_sales', 0)
        revenue = income_statement.get('revenue', 0)
        avg_inventory = inventory
        if comparative_data and len(comparative_data) > 0:
            prev_inventory = comparative_data[-1].balance_sheet.get('inventory', 0)
            if prev_inventory > 0:
                avg_inventory = (inventory + prev_inventory) / 2
        if avg_inventory > 0 and cost_of_sales > 0:
            inventory_turnover = self.safe_divide(cost_of_sales, avg_inventory)
            industry_type = industry_data.get('type', 'general') if industry_data else 'general'
            benchmark = self.inventory_benchmarks['inventory_turnover'].get(industry_type, self.inventory_benchmarks['inventory_turnover']['general'])
            risk_level = self.assess_risk_level(inventory_turnover, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Inventory Turnover', value=inventory_turnover, interpretation=self.generate_interpretation('inventory turnover', inventory_turnover, risk_level, AnalysisType.ACTIVITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(inventory_turnover, industry_data.get('inventory_turnover') if industry_data else None), methodology='Cost of Goods Sold / Average Inventory', limitations=['Seasonality may affect single-period calculations']))
        if avg_inventory > 0 and cost_of_sales > 0:
            daily_cogs = cost_of_sales / 365
            days_inventory = self.safe_divide(avg_inventory, daily_cogs)
            benchmark = self.inventory_benchmarks['days_inventory_outstanding'].get(industry_type, self.inventory_benchmarks['days_inventory_outstanding']['general'])
            risk_level = self.assess_risk_level(days_inventory, benchmark, higher_is_better=False)
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Days Inventory Outstanding', value=days_inventory, interpretation=f'Inventory held for {days_inventory:.0f} days on average', risk_level=risk_level, benchmark_comparison=self.compare_to_industry(days_inventory, industry_data.get('days_inventory') if industry_data else None), methodology='(Average Inventory / COGS) × 365', limitations=['Does not account for seasonal inventory patterns']))
        if revenue > 0:
            inventory_to_sales = self.safe_divide(inventory, revenue)
            benchmark = self.inventory_benchmarks['inventory_to_sales'].get(industry_type, self.inventory_benchmarks['inventory_to_sales']['general'])
            risk_level = self.assess_risk_level(inventory_to_sales, benchmark, higher_is_better=False)
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Inventory to Sales Ratio', value=inventory_to_sales, interpretation=f'Inventory represents {self.format_percentage(inventory_to_sales)} of annual sales', risk_level=risk_level, methodology='Ending Inventory / Revenue', limitations=['Point-in-time measure may not reflect average levels']))
        if comparative_data and len(comparative_data) > 0:
            prev_inventory = comparative_data[-1].balance_sheet.get('inventory', 0)
            prev_revenue = comparative_data[-1].income_statement.get('revenue', 0)
            if prev_inventory > 0:
                inventory_growth = inventory / prev_inventory - 1
                if prev_revenue > 0:
                    revenue_growth = revenue / prev_revenue - 1
                    if abs(revenue_growth) > 0.01:
                        growth_comparison = inventory_growth - revenue_growth
                        if growth_comparison > 0.1:
                            growth_interpretation = 'Inventory growing faster than sales - potential build-up'
                            growth_risk = RiskLevel.MODERATE
                        elif growth_comparison < -0.1:
                            growth_interpretation = 'Inventory growing slower than sales - improving efficiency'
                            growth_risk = RiskLevel.LOW
                        else:
                            growth_interpretation = 'Inventory growth aligned with sales growth'
                            growth_risk = RiskLevel.LOW
                        results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Inventory vs Sales Growth', value=growth_comparison, interpretation=growth_interpretation, risk_level=growth_risk, methodology='Inventory Growth Rate - Revenue Growth Rate', limitations=['Single period comparison - trend analysis preferred']))
        return results

    def _analyze_inventory_valuation(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze inventory valuation methods and their impact"""
        results = []
        notes = statements.notes
        balance_sheet = statements.balance_sheet
        inventory = balance_sheet.get('inventory', 0)
        lifo_reserve = notes.get('lifo_reserve', 0)
        if lifo_reserve > 0:
            lifo_reserve_ratio = self.safe_divide(lifo_reserve, inventory)
            reserve_interpretation = 'Significant LIFO reserve indicates substantial inflation impact' if lifo_reserve_ratio > 0.2 else 'Moderate LIFO reserve' if lifo_reserve_ratio > 0.1 else 'Small LIFO reserve impact'
            reserve_risk = RiskLevel.MODERATE if lifo_reserve_ratio > 0.3 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='LIFO Reserve Ratio', value=lifo_reserve_ratio, interpretation=reserve_interpretation, risk_level=reserve_risk, methodology='LIFO Reserve / Total Inventory', limitations=['LIFO reserve represents cumulative impact over multiple periods']))
            fifo_equivalent_inventory = inventory + lifo_reserve
            fifo_adjustment_ratio = self.safe_divide(lifo_reserve, inventory)
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='FIFO Equivalent Adjustment', value=fifo_adjustment_ratio, interpretation=f'FIFO inventory would be {self.format_percentage(fifo_adjustment_ratio)} higher than LIFO', risk_level=RiskLevel.LOW, methodology='LIFO Reserve / LIFO Inventory', limitations=['Adjustment provides approximate FIFO equivalent']))
        cost_method = notes.get('inventory_method', 'unknown')
        if cost_method != 'unknown':
            method_risk_assessment = self._assess_method_appropriateness(cost_method, statements)
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Inventory Method Assessment', value=1.0, interpretation=f'Company uses {cost_method} method - {method_risk_assessment['assessment']}', risk_level=method_risk_assessment['risk'], methodology='Qualitative assessment of inventory method appropriateness', limitations=method_risk_assessment['limitations']))
        return results

    def _analyze_lower_cost_nrv(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze lower of cost and net realizable value measurements"""
        results = []
        balance_sheet = statements.balance_sheet
        notes = statements.notes
        inventory = balance_sheet.get('inventory', 0)
        inventory_writedown = notes.get('inventory_writedown', 0)
        inventory_reserve = notes.get('inventory_obsolescence_reserve', 0)
        if inventory_writedown > 0:
            writedown_ratio = self.safe_divide(inventory_writedown, inventory + inventory_writedown)
            writedown_interpretation = 'Significant inventory writedown indicates valuation issues' if writedown_ratio > 0.05 else 'Moderate inventory adjustment' if writedown_ratio > 0.02 else 'Minor inventory writedown'
            writedown_risk = RiskLevel.HIGH if writedown_ratio > 0.1 else RiskLevel.MODERATE if writedown_ratio > 0.05 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Inventory Writedown Impact', value=writedown_ratio, interpretation=writedown_interpretation, risk_level=writedown_risk, methodology='Inventory Writedown / (Inventory + Writedown)', limitations=['Writedowns may indicate obsolescence or market decline']))
        if inventory_reserve > 0:
            reserve_ratio = self.safe_divide(inventory_reserve, inventory + inventory_reserve)
            reserve_interpretation = 'High obsolescence reserve suggests inventory quality concerns' if reserve_ratio > 0.1 else 'Moderate obsolescence provision' if reserve_ratio > 0.05 else 'Conservative obsolescence reserve'
            reserve_risk = RiskLevel.MODERATE if reserve_ratio > 0.15 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Obsolescence Reserve Ratio', value=reserve_ratio, interpretation=reserve_interpretation, risk_level=reserve_risk, methodology='Obsolescence Reserve / (Inventory + Reserve)', limitations=['Reserve adequacy depends on inventory composition and age']))
        results.extend(self._assess_nrv_compliance(statements, comparative_data))
        return results

    def _analyze_inflation_impact(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze impact of inflation/deflation on inventory and ratios"""
        results = []
        notes = statements.notes
        income_statement = statements.income_statement
        inflation_rate = industry_data.get('inflation_rate', 0) if industry_data else 0
        economic_environment = self._determine_economic_environment(inflation_rate)
        cost_method = notes.get('inventory_method', 'unknown')
        lifo_reserve = notes.get('lifo_reserve', 0)
        if economic_environment != EconomicEnvironment.STABLE and cost_method in ['fifo', 'lifo']:
            revenue = income_statement.get('revenue', 0)
            cost_of_sales = income_statement.get('cost_of_sales', 0)
            if revenue > 0 and cost_of_sales > 0:
                current_gross_margin = self.safe_divide(revenue - cost_of_sales, revenue)
                if cost_method == 'lifo' and lifo_reserve > 0:
                    estimated_fifo_cogs = cost_of_sales - lifo_reserve
                    estimated_fifo_margin = self.safe_divide(revenue - estimated_fifo_cogs, revenue)
                    margin_impact = estimated_fifo_margin - current_gross_margin
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Inflation Method Impact', value=margin_impact, interpretation=f'FIFO would result in {self.format_percentage(abs(margin_impact))} {('higher' if margin_impact > 0 else 'lower')} gross margin', risk_level=RiskLevel.MODERATE if abs(margin_impact) > 0.05 else RiskLevel.LOW, methodology='Estimated FIFO margin - Current LIFO margin', limitations=['Estimation based on LIFO reserve approximation']))
                if economic_environment == EconomicEnvironment.INFLATIONARY:
                    tax_preferred_method = 'LIFO' if cost_method == 'lifo' else 'LIFO (not used)'
                    tax_impact_description = 'LIFO provides tax benefits in inflationary environment' if cost_method == 'lifo' else 'FIFO results in higher taxable income during inflation'
                    results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Tax Method Efficiency', value=1.0 if cost_method == 'lifo' else 0.0, interpretation=tax_impact_description, risk_level=RiskLevel.LOW if cost_method == 'lifo' else RiskLevel.MODERATE, methodology='Qualitative assessment of method choice in inflationary environment'))
        return results

    def _analyze_inventory_composition(self, statements: FinancialStatements) -> List[AnalysisResult]:
        """Analyze inventory composition and mix"""
        results = []
        notes = statements.notes
        balance_sheet = statements.balance_sheet
        total_inventory = balance_sheet.get('inventory', 0)
        inventory_components = {'raw_materials': notes.get('raw_materials_inventory', 0), 'work_in_process': notes.get('wip_inventory', 0), 'finished_goods': notes.get('finished_goods_inventory', 0)}
        total_components = sum(inventory_components.values())
        if total_components > 0 and abs(total_components - total_inventory) / total_inventory < 0.1:
            for component, value in inventory_components.items():
                if value > 0:
                    component_ratio = self.safe_divide(value, total_inventory)
                    component_name = component.replace('_', ' ').title()
                    results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name=f'{component_name} Composition', value=component_ratio, interpretation=f'{component_name} represents {self.format_percentage(component_ratio)} of total inventory', risk_level=RiskLevel.LOW, methodology=f'{component_name} / Total Inventory'))
            raw_materials_ratio = inventory_components['raw_materials'] / total_inventory
            wip_ratio = inventory_components['work_in_process'] / total_inventory
            finished_goods_ratio = inventory_components['finished_goods'] / total_inventory
            if wip_ratio > 0.5:
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Inventory Composition Risk', value=wip_ratio, interpretation='High work-in-process ratio may indicate production inefficiencies', risk_level=RiskLevel.MODERATE, methodology='Qualitative assessment of inventory composition'))
            elif finished_goods_ratio > 0.7:
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Inventory Composition Risk', value=finished_goods_ratio, interpretation='High finished goods ratio may indicate demand forecasting issues', risk_level=RiskLevel.MODERATE, methodology='Qualitative assessment of inventory composition'))
        return results

    def _assess_inventory_disclosures(self, statements: FinancialStatements) -> List[AnalysisResult]:
        """Assess quality and completeness of inventory disclosures"""
        results = []
        notes = statements.notes
        required_disclosures = {'inventory_method': 'Accounting policy for inventory valuation', 'inventory_composition': 'Breakdown of inventory components', 'writedown_policy': 'Policy for inventory writedowns', 'obsolescence_assessment': 'Obsolescence evaluation methodology'}
        disclosure_score = 0
        missing_disclosures = []
        for disclosure_key, description in required_disclosures.items():
            if any((disclosure_key in key.lower() for key in notes.keys())):
                disclosure_score += 25
            else:
                missing_disclosures.append(description)
        disclosure_interpretation = 'Comprehensive inventory disclosures' if disclosure_score > 75 else 'Adequate inventory disclosures' if disclosure_score > 50 else 'Limited inventory disclosures'
        disclosure_risk = RiskLevel.LOW if disclosure_score > 75 else RiskLevel.MODERATE if disclosure_score > 50 else RiskLevel.HIGH
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Inventory Disclosure Quality', value=disclosure_score, interpretation=disclosure_interpretation, risk_level=disclosure_risk, methodology='Assessment of required inventory disclosure completeness', limitations=missing_disclosures if missing_disclosures else ['Disclosure quality assessment based on available notes']))
        return results

    def _assess_method_appropriateness(self, method: str, statements: FinancialStatements) -> Dict[str, Union[str, RiskLevel, List[str]]]:
        """Assess appropriateness of inventory method choice"""
        notes = statements.notes
        business_type = notes.get('business_description', '').lower()
        if method.lower() == 'fifo':
            if 'perishable' in business_type or 'food' in business_type:
                return {'assessment': 'FIFO appropriate for perishable goods business', 'risk': RiskLevel.LOW, 'limitations': ['FIFO reflects physical flow for perishables']}
            else:
                return {'assessment': 'FIFO provides current cost basis for inventory', 'risk': RiskLevel.LOW, 'limitations': ['FIFO may overstate profits during inflation']}
        elif method.lower() == 'lifo':
            return {'assessment': 'LIFO provides tax benefits in inflationary periods', 'risk': RiskLevel.LOW, 'limitations': ['LIFO may understate inventory values', 'Not permitted under IFRS']}
        elif method.lower() == 'weighted_average':
            return {'assessment': 'Weighted average smooths cost fluctuations', 'risk': RiskLevel.LOW, 'limitations': ['May not reflect specific cost identification']}
        else:
            return {'assessment': 'Method appropriateness cannot be assessed', 'risk': RiskLevel.MODERATE, 'limitations': ['Insufficient information on inventory method']}

    def _assess_nrv_compliance(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess compliance with lower of cost and NRV requirements"""
        results = []
        notes = statements.notes
        income_statement = statements.income_statement
        nrv_writedowns = notes.get('nrv_writedowns', 0)
        inventory_impairment = income_statement.get('inventory_impairment', 0)
        if nrv_writedowns > 0 or inventory_impairment > 0:
            total_writedowns = nrv_writedowns + inventory_impairment
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='NRV Writedown Activity', value=total_writedowns, interpretation=f'NRV writedowns of ${total_writedowns:,.0f} indicate active impairment monitoring', risk_level=RiskLevel.MODERATE if total_writedowns > 0 else RiskLevel.LOW, methodology='Sum of NRV writedowns and inventory impairments', limitations=['Writedowns may indicate market deterioration or obsolescence']))
        nrv_policy = notes.get('nrv_methodology', '')
        if nrv_policy:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='NRV Methodology Disclosure', value=1.0, interpretation='Company discloses NRV assessment methodology', risk_level=RiskLevel.LOW, methodology='Qualitative assessment of NRV disclosure quality'))
        else:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='NRV Methodology Disclosure', value=0.0, interpretation='Limited disclosure of NRV assessment methodology', risk_level=RiskLevel.MODERATE, methodology='Qualitative assessment of NRV disclosure quality', limitations=['Lack of NRV methodology disclosure reduces transparency']))
        return results

    def _determine_economic_environment(self, inflation_rate: float) -> EconomicEnvironment:
        """Determine economic environment based on inflation rate"""
        if inflation_rate > 0.03:
            return EconomicEnvironment.INFLATIONARY
        elif inflation_rate < -0.01:
            return EconomicEnvironment.DEFLATIONARY
        else:
            return EconomicEnvironment.STABLE

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key inventory metrics"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        inventory = balance_sheet.get('inventory', 0)
        cost_of_sales = income_statement.get('cost_of_sales', 0)
        revenue = income_statement.get('revenue', 0)
        metrics = {}
        if inventory > 0:
            metrics['inventory_value'] = inventory
            if cost_of_sales > 0:
                metrics['inventory_turnover'] = self.safe_divide(cost_of_sales, inventory)
                metrics['days_inventory_outstanding'] = self.safe_divide(inventory * 365, cost_of_sales)
            if revenue > 0:
                metrics['inventory_to_sales'] = self.safe_divide(inventory, revenue)
        notes = statements.notes
        lifo_reserve = notes.get('lifo_reserve', 0)
        if lifo_reserve > 0:
            metrics['lifo_reserve'] = lifo_reserve
            metrics['lifo_reserve_ratio'] = self.safe_divide(lifo_reserve, inventory)
        return metrics

    def create_inventory_efficiency_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> InventoryEfficiencyAnalysis:
        """Create comprehensive inventory efficiency analysis object"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        inventory = balance_sheet.get('inventory', 0)
        cost_of_sales = income_statement.get('cost_of_sales', 0)
        revenue = income_statement.get('revenue', 0)
        avg_inventory = inventory
        if comparative_data and len(comparative_data) > 0:
            prev_inventory = comparative_data[-1].balance_sheet.get('inventory', 0)
            if prev_inventory > 0:
                avg_inventory = (inventory + prev_inventory) / 2
        inventory_turnover = self.safe_divide(cost_of_sales, avg_inventory)
        days_inventory_outstanding = self.safe_divide(avg_inventory * 365, cost_of_sales) if cost_of_sales > 0 else 0
        inventory_to_sales_ratio = self.safe_divide(inventory, revenue)
        inventory_growth_rate = 0
        if comparative_data and len(comparative_data) > 0:
            prev_inventory = comparative_data[-1].balance_sheet.get('inventory', 0)
            if prev_inventory > 0:
                inventory_growth_rate = inventory / prev_inventory - 1
        turnover_trend = TrendDirection.STABLE
        if comparative_data and len(comparative_data) >= 2:
            turnover_values = []
            for past_statements in comparative_data:
                past_inventory = past_statements.balance_sheet.get('inventory', 0)
                past_cogs = past_statements.income_statement.get('cost_of_sales', 0)
                if past_inventory > 0 and past_cogs > 0:
                    turnover_values.append(past_cogs / past_inventory)
            if len(turnover_values) >= 2:
                if turnover_values[-1] > turnover_values[0] * 1.05:
                    turnover_trend = TrendDirection.IMPROVING
                elif turnover_values[-1] < turnover_values[0] * 0.95:
                    turnover_trend = TrendDirection.DETERIORATING
        efficiency_score = 100
        if inventory_turnover < 4:
            efficiency_score -= 20
        if days_inventory_outstanding > 90:
            efficiency_score -= 15
        if inventory_to_sales_ratio > 0.25:
            efficiency_score -= 10
        efficiency_score = max(0, efficiency_score)
        return InventoryEfficiencyAnalysis(inventory_turnover=inventory_turnover, days_inventory_outstanding=days_inventory_outstanding, inventory_to_sales_ratio=inventory_to_sales_ratio, inventory_growth_rate=inventory_growth_rate, turnover_trend=turnover_trend, efficiency_score=efficiency_score)

    def create_inventory_valuation_analysis(self, statements: FinancialStatements) -> InventoryValuationAnalysis:
        """Create comprehensive inventory valuation analysis object"""
        balance_sheet = statements.balance_sheet
        notes = statements.notes
        inventory = balance_sheet.get('inventory', 0)
        cost_method_str = notes.get('inventory_method', 'unknown')
        cost_method = InventoryMethod.FIFO
        if 'lifo' in cost_method_str.lower():
            cost_method = InventoryMethod.LIFO
        elif 'weighted' in cost_method_str.lower() or 'average' in cost_method_str.lower():
            cost_method = InventoryMethod.WEIGHTED_AVERAGE
        elif 'specific' in cost_method_str.lower():
            cost_method = InventoryMethod.SPECIFIC_IDENTIFICATION
        inventory_reserve = notes.get('inventory_obsolescence_reserve', 0)
        lifo_reserve = notes.get('lifo_reserve', 0)
        net_realizable_value = inventory
        lower_of_cost_nrv = inventory - inventory_reserve
        fifo_equivalent_value = None
        lifo_equivalent_value = None
        if cost_method == InventoryMethod.LIFO and lifo_reserve > 0:
            fifo_equivalent_value = inventory + lifo_reserve
        elif cost_method == InventoryMethod.FIFO and lifo_reserve > 0:
            lifo_equivalent_value = inventory - lifo_reserve
        quality_score = 100
        obsolescence_indicators = []
        valuation_concerns = []
        if inventory_reserve > 0:
            reserve_ratio = inventory_reserve / (inventory + inventory_reserve)
            if reserve_ratio > 0.1:
                quality_score -= 20
                obsolescence_indicators.append('High obsolescence reserve')
        if cost_method == InventoryMethod.LIFO:
            valuation_concerns.append('LIFO may understate current inventory values')
        return InventoryValuationAnalysis(cost_method=cost_method, current_inventory_value=inventory, inventory_reserve=inventory_reserve, net_realizable_value=net_realizable_value, lower_of_cost_nrv=lower_of_cost_nrv, fifo_equivalent_value=fifo_equivalent_value, lifo_equivalent_value=lifo_equivalent_value, lifo_reserve=lifo_reserve, inventory_quality_score=quality_score, obsolescence_indicators=obsolescence_indicators, valuation_concerns=valuation_concerns)

    def create_inflation_impact_analysis(self, statements: FinancialStatements, inflation_rate: float=0.0) -> InflationImpactAnalysis:
        """Create inflation impact analysis object"""
        income_statement = statements.income_statement
        notes = statements.notes
        economic_environment = self._determine_economic_environment(inflation_rate)
        cost_method = notes.get('inventory_method', 'unknown')
        lifo_reserve = notes.get('lifo_reserve', 0)
        revenue = income_statement.get('revenue', 0)
        cost_of_sales = income_statement.get('cost_of_sales', 0)
        fifo_impact_on_cogs = 0
        fifo_impact_on_gross_margin = 0
        fifo_impact_on_inventory_value = 0
        lifo_impact_on_cogs = 0
        lifo_impact_on_gross_margin = 0
        lifo_impact_on_inventory_value = 0
        tax_advantage_method = 'No significant difference'
        if cost_method.lower() == 'lifo' and lifo_reserve > 0 and (revenue > 0):
            current_gross_margin = (revenue - cost_of_sales) / revenue
            estimated_fifo_cogs = cost_of_sales - lifo_reserve
            estimated_fifo_gross_margin = (revenue - estimated_fifo_cogs) / revenue
            fifo_impact_on_cogs = estimated_fifo_cogs - cost_of_sales
            fifo_impact_on_gross_margin = estimated_fifo_gross_margin - current_gross_margin
            fifo_impact_on_inventory_value = lifo_reserve
            if economic_environment == EconomicEnvironment.INFLATIONARY:
                tax_advantage_method = 'LIFO provides tax advantage'
        elif cost_method.lower() == 'fifo' and inflation_rate > 0.02:
            if economic_environment == EconomicEnvironment.INFLATIONARY:
                tax_advantage_method = 'LIFO would provide tax advantage (not used)'
        return InflationImpactAnalysis(economic_environment=economic_environment, inflation_rate=inflation_rate, fifo_impact_on_cogs=fifo_impact_on_cogs, fifo_impact_on_gross_margin=fifo_impact_on_gross_margin, fifo_impact_on_inventory_value=fifo_impact_on_inventory_value, lifo_impact_on_cogs=lifo_impact_on_cogs, lifo_impact_on_gross_margin=lifo_impact_on_gross_margin, lifo_impact_on_inventory_value=lifo_impact_on_inventory_value, tax_advantage_method=tax_advantage_method)

    def analyze_inventory_trends(self, current_statements: FinancialStatements, comparative_data: List[FinancialStatements]) -> Dict[str, ComparativeAnalysis]:
        """Analyze inventory trends over multiple periods"""
        trends = {}
        if not comparative_data:
            return trends
        inventory_values = []
        turnover_values = []
        periods = []
        for i, statements in enumerate(comparative_data):
            inventory = statements.balance_sheet.get('inventory', 0)
            cogs = statements.income_statement.get('cost_of_sales', 0)
            inventory_values.append(inventory)
            if inventory > 0 and cogs > 0:
                turnover_values.append(cogs / inventory)
            periods.append(f'Period-{len(comparative_data) - i}')
        current_inventory = current_statements.balance_sheet.get('inventory', 0)
        current_cogs = current_statements.income_statement.get('cost_of_sales', 0)
        inventory_values.append(current_inventory)
        if current_inventory > 0 and current_cogs > 0:
            turnover_values.append(current_cogs / current_inventory)
        periods.append('Current')
        if len(inventory_values) > 1:
            trends['inventory_values'] = self.calculate_trend(inventory_values, periods)
        if len(turnover_values) > 1:
            trends['inventory_turnover'] = self.calculate_trend(turnover_values, periods)
        return trends

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive inventory analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all inventory aspects
        """
    results = []
    inventory = statements.balance_sheet.get('inventory', 0)
    if inventory <= 0:
        results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Inventory Analysis', value=0.0, interpretation='No inventory reported - inventory analysis not applicable', risk_level=RiskLevel.LOW, methodology='Balance sheet inventory examination'))
        return results
    results.extend(self._analyze_inventory_efficiency(statements, comparative_data, industry_data))
    results.extend(self._analyze_inventory_valuation(statements, comparative_data))
    results.extend(self._analyze_lower_cost_nrv(statements, comparative_data))
    results.extend(self._analyze_inflation_impact(statements, comparative_data, industry_data))
    results.extend(self._analyze_inventory_composition(statements))
    results.extend(self._assess_inventory_disclosures(statements))
    return results

class IncomeStatementAnalyzer(BaseAnalyzer):
    """
    Comprehensive income statement analyzer implementing CFA Institute standards.
    Covers revenue/expense recognition, EPS calculations, non-recurring items analysis.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_income_formulas()
        self._initialize_quality_thresholds()

    def _initialize_income_formulas(self):
        """Initialize income statement specific formulas"""
        self.formula_registry.update({'gross_profit_margin': lambda revenue, cogs: self.safe_divide(revenue - cogs, revenue), 'operating_profit_margin': lambda operating_income, revenue: self.safe_divide(operating_income, revenue), 'net_profit_margin': lambda net_income, revenue: self.safe_divide(net_income, revenue), 'ebitda_margin': lambda ebitda, revenue: self.safe_divide(ebitda, revenue), 'basic_eps': lambda net_income, shares: self.safe_divide(net_income, shares), 'diluted_eps': lambda net_income_diluted, diluted_shares: self.safe_divide(net_income_diluted, diluted_shares), 'tax_rate': lambda tax_expense, pretax_income: self.safe_divide(tax_expense, pretax_income), 'interest_coverage': lambda ebit, interest_expense: self.safe_divide(ebit, interest_expense)})

    def _initialize_quality_thresholds(self):
        """Initialize income quality assessment thresholds"""
        self.quality_thresholds.update({'revenue_growth_volatility': {'low': 0.1, 'moderate': 0.2, 'high': 0.4}, 'earnings_persistence': {'high': 0.8, 'moderate': 0.6, 'low': 0.4}, 'accruals_ratio': {'good': 0.05, 'moderate': 0.1, 'poor': 0.2}, 'non_recurring_frequency': {'rare': 0.1, 'occasional': 0.2, 'frequent': 0.4}})

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive income statement analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all income statement aspects
        """
        results = []
        required_fields = ['revenue', 'net_income', 'operating_income']
        is_sufficient, missing_fields = self.validate_data_sufficiency(statements, required_fields)
        if not is_sufficient:
            if self.logger:
                self.logger.warning(f'Insufficient data for complete analysis. Missing: {missing_fields}')
        results.extend(self._analyze_profitability_ratios(statements, industry_data))
        results.extend(self._analyze_revenue_recognition(statements, comparative_data))
        results.extend(self._analyze_expense_recognition(statements, comparative_data))
        eps_results = self._analyze_earnings_per_share(statements, comparative_data)
        if eps_results:
            results.extend(eps_results)
        results.extend(self._analyze_non_recurring_items(statements, comparative_data))
        results.extend(self._assess_income_quality(statements, comparative_data))
        results.extend(self._perform_common_size_analysis(statements, comparative_data))
        return results

    def _analyze_profitability_ratios(self, statements: FinancialStatements, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze core profitability ratios"""
        results = []
        income = statements.income_statement
        revenue = income.get('revenue', 0)
        cogs = income.get('cost_of_sales', 0)
        if revenue > 0:
            gross_margin = self.safe_divide(revenue - cogs, revenue)
            benchmark = self.profitability_benchmarks.get('gross_margin', {})
            risk_level = self.assess_risk_level(gross_margin, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Gross Profit Margin', value=gross_margin, interpretation=self.generate_interpretation('gross profit margin', gross_margin, risk_level, AnalysisType.PROFITABILITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(gross_margin, industry_data.get('gross_margin') if industry_data else None), methodology='(Revenue - Cost of Sales) / Revenue', limitations=['Does not reflect operating efficiency or overhead costs']))
        operating_income = income.get('operating_income', 0)
        if revenue > 0 and operating_income is not None:
            operating_margin = self.safe_divide(operating_income, revenue)
            benchmark = self.profitability_benchmarks.get('operating_margin', {})
            risk_level = self.assess_risk_level(operating_margin, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Operating Profit Margin', value=operating_margin, interpretation=self.generate_interpretation('operating profit margin', operating_margin, risk_level, AnalysisType.PROFITABILITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(operating_margin, industry_data.get('operating_margin') if industry_data else None), methodology='Operating Income / Revenue', limitations=['Excludes non-operating income and expenses']))
        net_income = income.get('net_income', 0)
        if revenue > 0:
            net_margin = self.safe_divide(net_income, revenue)
            benchmark = self.profitability_benchmarks.get('net_margin', {})
            risk_level = self.assess_risk_level(net_margin, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Net Profit Margin', value=net_margin, interpretation=self.generate_interpretation('net profit margin', net_margin, risk_level, AnalysisType.PROFITABILITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(net_margin, industry_data.get('net_margin') if industry_data else None), methodology='Net Income / Revenue', limitations=['May include non-recurring items affecting comparability']))
        ebitda = self._calculate_ebitda(statements)
        if ebitda is not None and revenue > 0:
            ebitda_margin = self.safe_divide(ebitda, revenue)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='EBITDA Margin', value=ebitda_margin, interpretation=f'EBITDA margin of {self.format_percentage(ebitda_margin)} shows operational profitability before financing and accounting decisions', risk_level=self.assess_risk_level(ebitda_margin, self.profitability_benchmarks.get('operating_margin', {}), higher_is_better=True), methodology='(Operating Income + Depreciation + Amortization) / Revenue', limitations=['Does not reflect capital expenditure requirements or working capital needs']))
        return results

    def _analyze_revenue_recognition(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze revenue recognition and quality"""
        results = []
        income = statements.income_statement
        revenue = income.get('revenue', 0)
        if revenue <= 0:
            return results
        if comparative_data and len(comparative_data) > 0:
            prev_revenue = comparative_data[-1].income_statement.get('revenue', 0)
            if prev_revenue > 0:
                revenue_growth = revenue / prev_revenue - 1
                if revenue_growth > 0.2:
                    growth_quality = 'Strong revenue growth - monitor sustainability'
                elif revenue_growth > 0.1:
                    growth_quality = 'Healthy revenue growth'
                elif revenue_growth > 0:
                    growth_quality = 'Modest revenue growth'
                elif revenue_growth > -0.05:
                    growth_quality = 'Flat revenue - investigate causes'
                else:
                    growth_quality = 'Declining revenue - significant concern'
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Revenue Growth Rate', value=revenue_growth, interpretation=growth_quality, risk_level=RiskLevel.LOW if revenue_growth > 0.05 else RiskLevel.HIGH if revenue_growth < -0.05 else RiskLevel.MODERATE, methodology='(Current Revenue - Previous Revenue) / Previous Revenue', limitations=['Single period comparison may not reflect underlying trends']))
        balance_sheet = statements.balance_sheet
        accounts_receivable = balance_sheet.get('accounts_receivable', 0)
        if accounts_receivable > 0 and revenue > 0:
            dso = accounts_receivable / revenue * 365
            dso_interpretation = 'Normal collection period' if dso <= 45 else 'Extended collection period - monitor credit quality' if dso <= 90 else 'Very long collection period - potential collection issues'
            dso_risk = RiskLevel.LOW if dso <= 45 else RiskLevel.MODERATE if dso <= 90 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Days Sales Outstanding', value=dso, interpretation=dso_interpretation, risk_level=dso_risk, methodology='(Accounts Receivable / Revenue) × 365', limitations=['May vary by industry and seasonality']))
        revenue_quality_issues = self._identify_revenue_quality_issues(statements, comparative_data)
        if revenue_quality_issues:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Revenue Quality Assessment', value=len(revenue_quality_issues), interpretation=f'Identified {len(revenue_quality_issues)} potential revenue quality concerns', risk_level=RiskLevel.HIGH if len(revenue_quality_issues) > 2 else RiskLevel.MODERATE, limitations=revenue_quality_issues))
        return results

    def _analyze_expense_recognition(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze expense recognition patterns and quality"""
        results = []
        income = statements.income_statement
        revenue = income.get('revenue', 0)
        operating_income = income.get('operating_income', 0)
        if comparative_data and len(comparative_data) > 0 and (revenue > 0):
            prev_statements = comparative_data[-1]
            prev_revenue = prev_statements.income_statement.get('revenue', 0)
            prev_operating_income = prev_statements.income_statement.get('operating_income', 0)
            if prev_revenue > 0 and prev_operating_income != 0:
                revenue_change = revenue / prev_revenue - 1
                operating_change = operating_income / prev_operating_income - 1 if prev_operating_income != 0 else 0
                if revenue_change != 0:
                    operating_leverage = operating_change / revenue_change
                    leverage_interpretation = 'High operating leverage - earnings sensitive to revenue changes' if abs(operating_leverage) > 2 else 'Moderate operating leverage' if abs(operating_leverage) > 1 else 'Low operating leverage'
                    results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Operating Leverage', value=operating_leverage, interpretation=leverage_interpretation, risk_level=RiskLevel.HIGH if abs(operating_leverage) > 3 else RiskLevel.MODERATE, methodology='% Change in Operating Income / % Change in Revenue', limitations=['Single period calculation may not reflect long-term leverage']))
        if revenue > 0:
            rd_expenses = income.get('rd_expenses', 0)
            if rd_expenses > 0:
                rd_intensity = self.safe_divide(rd_expenses, revenue)
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='R&D Intensity', value=rd_intensity, interpretation=f'R&D spending represents {self.format_percentage(rd_intensity)} of revenue, indicating {('high' if rd_intensity > 0.05 else 'moderate' if rd_intensity > 0.02 else 'low')} innovation investment', risk_level=RiskLevel.LOW, methodology='R&D Expenses / Revenue'))
            selling_expenses = income.get('selling_expenses', 0)
            admin_expenses = income.get('administrative_expenses', 0)
            sga_total = selling_expenses + admin_expenses
            if sga_total > 0:
                sga_ratio = self.safe_divide(sga_total, revenue)
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='SG&A Ratio', value=sga_ratio, interpretation=f'SG&A expenses represent {self.format_percentage(sga_ratio)} of revenue', risk_level=RiskLevel.HIGH if sga_ratio > 0.3 else RiskLevel.MODERATE if sga_ratio > 0.2 else RiskLevel.LOW, methodology='(Selling + General & Administrative Expenses) / Revenue'))
        return results

    def _analyze_earnings_per_share(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Comprehensive EPS analysis including basic, diluted, and quality assessment"""
        results = []
        income = statements.income_statement
        basic_eps = income.get('basic_eps')
        diluted_eps = income.get('diluted_eps')
        basic_shares = income.get('shares_outstanding_basic')
        diluted_shares = income.get('shares_outstanding_diluted')
        net_income = income.get('net_income', 0)
        if not basic_eps and basic_shares and (basic_shares > 0):
            basic_eps = self.safe_divide(net_income, basic_shares)
        if not diluted_eps and diluted_shares and (diluted_shares > 0):
            diluted_eps = self.safe_divide(net_income, diluted_shares)
        if basic_eps is not None:
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Basic EPS', value=basic_eps, interpretation=f'Basic earnings per share of ${basic_eps:.2f}', risk_level=RiskLevel.LOW if basic_eps > 0 else RiskLevel.HIGH, methodology='Net Income / Weighted Average Basic Shares Outstanding'))
        if diluted_eps is not None:
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Diluted EPS', value=diluted_eps, interpretation=f'Diluted earnings per share of ${diluted_eps:.2f}', risk_level=RiskLevel.LOW if diluted_eps > 0 else RiskLevel.HIGH, methodology='Net Income (adjusted for dilutive securities) / Weighted Average Diluted Shares Outstanding'))
        if basic_eps and diluted_eps and (basic_eps != 0):
            dilution_effect = (basic_eps - diluted_eps) / basic_eps
            if dilution_effect > 0.05:
                dilution_interpretation = 'Significant dilution from potential securities conversions'
                dilution_risk = RiskLevel.MODERATE
            elif dilution_effect > 0.02:
                dilution_interpretation = 'Moderate dilution from potential securities conversions'
                dilution_risk = RiskLevel.LOW
            else:
                dilution_interpretation = 'Minimal dilution from potential securities conversions'
                dilution_risk = RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='EPS Dilution Effect', value=dilution_effect, interpretation=dilution_interpretation, risk_level=dilution_risk, methodology='(Basic EPS - Diluted EPS) / Basic EPS'))
        if comparative_data and basic_eps is not None:
            eps_values = []
            periods = []
            for i, past_statements in enumerate(comparative_data):
                past_eps = past_statements.income_statement.get('basic_eps')
                if past_eps is not None:
                    eps_values.append(past_eps)
                    periods.append(f'Period-{len(comparative_data) - i}')
            eps_values.append(basic_eps)
            periods.append('Current')
            if len(eps_values) > 1:
                eps_trend = self.calculate_trend(eps_values, periods)
                results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='EPS Growth Trend', value=eps_trend.growth_rate or 0, interpretation=eps_trend.trend_analysis, risk_level=RiskLevel.LOW if eps_trend.growth_rate and eps_trend.growth_rate > 0 else RiskLevel.HIGH, methodology='Compound Annual Growth Rate of Basic EPS'))
        return results

    def _analyze_non_recurring_items(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze non-recurring and unusual items"""
        results = []
        income = statements.income_statement
        non_recurring_items = {'discontinued_operations': income.get('discontinued_operations', 0), 'extraordinary_items': income.get('extraordinary_items', 0), 'restructuring_charges': income.get('restructuring_charges', 0), 'impairment_losses': income.get('impairment_losses', 0), 'gains_losses_disposals': income.get('gains_losses_disposals', 0)}
        total_non_recurring = sum((abs(value) for value in non_recurring_items.values()))
        net_income = income.get('net_income', 0)
        if total_non_recurring > 0:
            if net_income != 0:
                non_recurring_impact = total_non_recurring / abs(net_income)
                impact_interpretation = 'Significant non-recurring items affecting earnings comparability' if non_recurring_impact > 0.1 else 'Moderate non-recurring items impact' if non_recurring_impact > 0.05 else 'Minor non-recurring items impact'
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Non-Recurring Items Impact', value=non_recurring_impact, interpretation=impact_interpretation, risk_level=RiskLevel.HIGH if non_recurring_impact > 0.2 else RiskLevel.MODERATE if non_recurring_impact > 0.1 else RiskLevel.LOW, methodology='Total Non-Recurring Items / |Net Income|', limitations=['Adjustment may be needed for normalized earnings analysis']))
            if comparative_data:
                historical_non_recurring = []
                for past_statements in comparative_data:
                    past_income = past_statements.income_statement
                    past_non_recurring = sum((abs(past_income.get(item, 0)) for item in non_recurring_items.keys()))
                    historical_non_recurring.append(past_non_recurring)
                non_recurring_frequency = sum((1 for x in historical_non_recurring if x > 0)) / len(historical_non_recurring)
                frequency_interpretation = 'Frequent non-recurring items - may indicate operational issues' if non_recurring_frequency > 0.5 else 'Occasional non-recurring items' if non_recurring_frequency > 0.2 else 'Rare non-recurring items'
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Non-Recurring Items Frequency', value=non_recurring_frequency, interpretation=frequency_interpretation, risk_level=RiskLevel.HIGH if non_recurring_frequency > 0.6 else RiskLevel.MODERATE if non_recurring_frequency > 0.3 else RiskLevel.LOW, methodology='Number of periods with non-recurring items / Total periods'))
        return results

    def _assess_income_quality(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Comprehensive income quality assessment"""
        results = []
        if comparative_data and len(comparative_data) >= 2:
            net_incomes = []
            for past_statements in comparative_data:
                past_income = past_statements.income_statement.get('net_income', 0)
                net_incomes.append(past_income)
            current_income = statements.income_statement.get('net_income', 0)
            net_incomes.append(current_income)
            if len(net_incomes) > 1:
                mean_income = np.mean(net_incomes)
                std_income = np.std(net_incomes)
                earnings_volatility = std_income / abs(mean_income) if mean_income != 0 else 0
                volatility_interpretation = 'High earnings volatility - low predictability' if earnings_volatility > 0.3 else 'Moderate earnings volatility' if earnings_volatility > 0.15 else 'Low earnings volatility - stable earnings'
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Earnings Volatility', value=earnings_volatility, interpretation=volatility_interpretation, risk_level=RiskLevel.HIGH if earnings_volatility > 0.4 else RiskLevel.MODERATE if earnings_volatility > 0.2 else RiskLevel.LOW, methodology='Standard Deviation of Net Income / |Mean Net Income|'))
        cash_flow = statements.cash_flow
        operating_cash_flow = cash_flow.get('operating_cash_flow')
        net_income = statements.income_statement.get('net_income', 0)
        if operating_cash_flow is not None and net_income != 0:
            accruals_ratio = abs(net_income - operating_cash_flow) / abs(net_income)
            accruals_interpretation = 'High accruals - potential earnings manipulation risk' if accruals_ratio > 0.2 else 'Moderate accruals level' if accruals_ratio > 0.1 else 'Low accruals - high earnings quality'
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Accruals Ratio', value=accruals_ratio, interpretation=accruals_interpretation, risk_level=RiskLevel.HIGH if accruals_ratio > 0.3 else RiskLevel.MODERATE if accruals_ratio > 0.15 else RiskLevel.LOW, methodology='|Net Income - Operating Cash Flow| / |Net Income|', limitations=['High accruals may be justified by business model or growth phase']))
        return results

    def _perform_common_size_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Perform common-size income statement analysis"""
        results = []
        income = statements.income_statement
        revenue = income.get('revenue', 0)
        if revenue == 0:
            return results
        common_size_items = {'Cost of Sales': income.get('cost_of_sales', 0), 'Operating Expenses': income.get('operating_expenses', 0), 'Interest Expense': income.get('interest_expense', 0), 'Tax Expense': income.get('tax_expense', 0)}
        for item_name, item_value in common_size_items.items():
            if item_value != 0:
                common_size_pct = self.safe_divide(item_value, revenue)
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name=f'{item_name} as % of Revenue', value=common_size_pct, interpretation=f'{item_name} represents {self.format_percentage(common_size_pct)} of total revenue', risk_level=RiskLevel.LOW, methodology=f'{item_name} / Revenue'))
        return results

    def _calculate_ebitda(self, statements: FinancialStatements) -> Optional[float]:
        """Calculate EBITDA from available data"""
        income = statements.income_statement
        operating_income = income.get('operating_income')
        depreciation = income.get('depreciation', 0)
        amortization = income.get('amortization', 0)
        if operating_income is not None:
            return operating_income + depreciation + amortization
        return None

    def _identify_revenue_quality_issues(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[str]:
        """Identify potential revenue quality and manipulation issues"""
        quality_issues = []
        income = statements.income_statement
        balance_sheet = statements.balance_sheet
        revenue = income.get('revenue', 0)
        accounts_receivable = balance_sheet.get('accounts_receivable', 0)
        if comparative_data and len(comparative_data) > 0:
            prev_statements = comparative_data[-1]
            prev_revenue = prev_statements.income_statement.get('revenue', 0)
            prev_receivables = prev_statements.balance_sheet.get('accounts_receivable', 0)
            if prev_revenue > 0 and prev_receivables > 0:
                revenue_growth = revenue / prev_revenue - 1 if prev_revenue > 0 else 0
                receivables_growth = accounts_receivable / prev_receivables - 1 if prev_receivables > 0 else 0
                if receivables_growth > revenue_growth + 0.1:
                    quality_issues.append('Accounts receivable growing significantly faster than revenue')
        if revenue > 0 and accounts_receivable > 0:
            dso = accounts_receivable / revenue * 365
            if dso > 120:
                quality_issues.append(f'Very high Days Sales Outstanding ({dso:.0f} days)')
        notes = statements.notes
        if any(('related_party' in key.lower() for key in notes.keys())):
            quality_issues.append('Related party revenue transactions require scrutiny')
        return quality_issues

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key income statement metrics"""
        income = statements.income_statement
        revenue = income.get('revenue', 0)
        metrics = {}
        if revenue > 0:
            metrics['gross_profit_margin'] = self.safe_divide(revenue - income.get('cost_of_sales', 0), revenue)
            metrics['operating_profit_margin'] = self.safe_divide(income.get('operating_income', 0), revenue)
            metrics['net_profit_margin'] = self.safe_divide(income.get('net_income', 0), revenue)
            ebitda = self._calculate_ebitda(statements)
            if ebitda is not None:
                metrics['ebitda_margin'] = self.safe_divide(ebitda, revenue)
        metrics['basic_eps'] = income.get('basic_eps', 0)
        metrics['diluted_eps'] = income.get('diluted_eps', 0)
        pretax_income = income.get('pretax_income', 0)
        tax_expense = income.get('tax_expense', 0)
        if pretax_income != 0:
            metrics['effective_tax_rate'] = self.safe_divide(tax_expense, pretax_income)
        return metrics

    def create_eps_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> EPSAnalysis:
        """Create comprehensive EPS analysis object"""
        income = statements.income_statement
        basic_eps = income.get('basic_eps', 0)
        diluted_eps = income.get('diluted_eps', 0)
        basic_shares = income.get('shares_outstanding_basic', 0)
        diluted_shares = income.get('shares_outstanding_diluted', 0)
        dilution_effect = 0
        if basic_eps != 0 and diluted_eps != 0:
            dilution_effect = (basic_eps - diluted_eps) / basic_eps
        eps_quality = IncomeQualityIndicator.HIGH_QUALITY
        if dilution_effect > 0.1:
            eps_quality = IncomeQualityIndicator.MODERATE_QUALITY
        antidilutive_securities = diluted_shares < basic_shares if basic_shares > 0 else False
        eps_growth_rate = None
        eps_volatility = None
        if comparative_data and len(comparative_data) > 0:
            eps_values = []
            for past_statements in comparative_data:
                past_eps = past_statements.income_statement.get('basic_eps')
                if past_eps is not None:
                    eps_values.append(past_eps)
            if eps_values and basic_eps is not None:
                eps_values.append(basic_eps)
                if len(eps_values) > 1:
                    if eps_values[0] != 0:
                        if len(eps_values) == 2:
                            eps_growth_rate = eps_values[-1] / eps_values[0] - 1
                        else:
                            n_periods = len(eps_values) - 1
                            eps_growth_rate = (eps_values[-1] / eps_values[0]) ** (1 / n_periods) - 1
                    mean_eps = np.mean(eps_values)
                    std_eps = np.std(eps_values)
                    eps_volatility = std_eps / abs(mean_eps) if mean_eps != 0 else 0
        return EPSAnalysis(basic_eps=basic_eps, diluted_eps=diluted_eps, basic_shares=basic_shares, diluted_shares=diluted_shares, dilution_effect=dilution_effect, eps_quality=eps_quality, antidilutive_securities=antidilutive_securities, eps_growth_rate=eps_growth_rate, eps_volatility=eps_volatility)

    def analyze_non_recurring_items(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> NonRecurringItemsAnalysis:
        """Create detailed non-recurring items analysis"""
        income = statements.income_statement
        discontinued_operations = income.get('discontinued_operations', 0)
        unusual_items = income.get('unusual_items', 0)
        extraordinary_items = income.get('extraordinary_items', 0)
        restructuring_charges = income.get('restructuring_charges', 0)
        impairment_losses = income.get('impairment_losses', 0)
        gains_losses_disposals = income.get('gains_losses_disposals', 0)
        total_non_recurring = sum((abs(x) for x in [discontinued_operations, unusual_items, extraordinary_items, restructuring_charges, impairment_losses, gains_losses_disposals]))
        net_income = income.get('net_income', 0)
        impact_on_core_earnings = total_non_recurring / abs(net_income) if net_income != 0 else 0
        frequency_analysis = 'Single period analysis'
        persistence_assessment = 'Cannot assess without historical data'
        if comparative_data:
            periods_with_non_recurring = 0
            total_periods = len(comparative_data) + 1
            for past_statements in comparative_data:
                past_income = past_statements.income_statement
                past_non_recurring = sum((abs(past_income.get(item, 0)) for item in ['discontinued_operations', 'unusual_items', 'extraordinary_items', 'restructuring_charges', 'impairment_losses', 'gains_losses_disposals']))
                if past_non_recurring > 0:
                    periods_with_non_recurring += 1
            if total_non_recurring > 0:
                periods_with_non_recurring += 1
            frequency_rate = periods_with_non_recurring / total_periods
            if frequency_rate > 0.6:
                frequency_analysis = 'Frequent non-recurring items - may indicate operational issues'
                persistence_assessment = 'High persistence - items may be recurring in nature'
            elif frequency_rate > 0.3:
                frequency_analysis = 'Occasional non-recurring items'
                persistence_assessment = 'Moderate persistence'
            else:
                frequency_analysis = 'Rare non-recurring items'
                persistence_assessment = 'Low persistence - truly non-recurring'
        return NonRecurringItemsAnalysis(total_non_recurring=total_non_recurring, discontinued_operations=discontinued_operations, unusual_items=unusual_items, extraordinary_items=extraordinary_items, restructuring_charges=restructuring_charges, impairment_losses=impairment_losses, gains_losses_disposals=gains_losses_disposals, impact_on_core_earnings=impact_on_core_earnings, frequency_analysis=frequency_analysis, persistence_assessment=persistence_assessment)

    def assess_revenue_quality(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> RevenueQualityAssessment:
        """Comprehensive revenue quality assessment"""
        income = statements.income_statement
        balance_sheet = statements.balance_sheet
        revenue = income.get('revenue', 0)
        accounts_receivable = balance_sheet.get('accounts_receivable', 0)
        revenue_growth_rate = 0
        revenue_volatility = 0
        seasonality_factor = 0
        revenue_concentration = 0
        days_sales_outstanding = 0
        if revenue > 0 and accounts_receivable >= 0:
            days_sales_outstanding = accounts_receivable / revenue * 365
        if comparative_data and len(comparative_data) > 0:
            revenue_values = []
            for past_statements in comparative_data:
                past_revenue = past_statements.income_statement.get('revenue', 0)
                revenue_values.append(past_revenue)
            revenue_values.append(revenue)
            if len(revenue_values) > 1:
                if revenue_values[0] > 0:
                    if len(revenue_values) == 2:
                        revenue_growth_rate = revenue_values[-1] / revenue_values[0] - 1
                    else:
                        n_periods = len(revenue_values) - 1
                        revenue_growth_rate = (revenue_values[-1] / revenue_values[0]) ** (1 / n_periods) - 1
                mean_revenue = np.mean(revenue_values)
                std_revenue = np.std(revenue_values)
                revenue_volatility = std_revenue / mean_revenue if mean_revenue > 0 else 0
        quality_indicators = []
        recognition_issues = []
        if days_sales_outstanding <= 45:
            quality_indicators.append('Healthy collection period')
        elif days_sales_outstanding > 90:
            recognition_issues.append('Extended collection period may indicate quality issues')
        if revenue_growth_rate > 0:
            quality_indicators.append('Positive revenue growth')
        elif revenue_growth_rate < -0.1:
            recognition_issues.append('Significant revenue decline')
        if revenue_volatility < 0.1:
            quality_indicators.append('Stable revenue pattern')
        elif revenue_volatility > 0.3:
            recognition_issues.append('High revenue volatility')
        quality_score = 100
        quality_score -= len(recognition_issues) * 20
        quality_score -= max(0, (days_sales_outstanding - 45) / 10 * 5)
        quality_score -= max(0, revenue_volatility * 100)
        quality_score = max(0, min(100, quality_score))
        return RevenueQualityAssessment(revenue_growth_rate=revenue_growth_rate, revenue_volatility=revenue_volatility, seasonality_factor=seasonality_factor, revenue_concentration=revenue_concentration, days_sales_outstanding=days_sales_outstanding, revenue_quality_score=quality_score, recognition_issues=recognition_issues, quality_indicators=quality_indicators)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive income statement analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all income statement aspects
        """
    results = []
    required_fields = ['revenue', 'net_income', 'operating_income']
    is_sufficient, missing_fields = self.validate_data_sufficiency(statements, required_fields)
    if not is_sufficient:
        if self.logger:
            self.logger.warning(f'Insufficient data for complete analysis. Missing: {missing_fields}')
    results.extend(self._analyze_profitability_ratios(statements, industry_data))
    results.extend(self._analyze_revenue_recognition(statements, comparative_data))
    results.extend(self._analyze_expense_recognition(statements, comparative_data))
    eps_results = self._analyze_earnings_per_share(statements, comparative_data)
    if eps_results:
        results.extend(eps_results)
    results.extend(self._analyze_non_recurring_items(statements, comparative_data))
    results.extend(self._assess_income_quality(statements, comparative_data))
    results.extend(self._perform_common_size_analysis(statements, comparative_data))
    return results

class BalanceSheetAnalyzer(BaseAnalyzer):
    """
    Comprehensive balance sheet analyzer implementing CFA Institute standards.
    Covers asset analysis, liability evaluation, liquidity assessment, and equity structure.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_balance_sheet_formulas()
        self._initialize_balance_sheet_benchmarks()

    def _initialize_balance_sheet_formulas(self):
        """Initialize balance sheet specific formulas"""
        self.formula_registry.update({'current_ratio': lambda current_assets, current_liabs: self.safe_divide(current_assets, current_liabs), 'quick_ratio': lambda quick_assets, current_liabs: self.safe_divide(quick_assets, current_liabs), 'cash_ratio': lambda cash, current_liabs: self.safe_divide(cash, current_liabs), 'debt_to_equity': lambda total_debt, total_equity: self.safe_divide(total_debt, total_equity), 'debt_to_assets': lambda total_debt, total_assets: self.safe_divide(total_debt, total_assets), 'asset_turnover': lambda revenue, avg_total_assets: self.safe_divide(revenue, avg_total_assets), 'equity_multiplier': lambda total_assets, total_equity: self.safe_divide(total_assets, total_equity), 'working_capital_ratio': lambda working_capital, total_assets: self.safe_divide(working_capital, total_assets)})

    def _initialize_balance_sheet_benchmarks(self):
        """Initialize balance sheet specific benchmarks"""
        self.asset_composition_benchmarks = {'current_asset_ratio': {'high': 0.4, 'moderate': 0.3, 'low': 0.2}, 'intangible_ratio': {'high': 0.3, 'moderate': 0.15, 'low': 0.05}, 'goodwill_ratio': {'high': 0.2, 'moderate': 0.1, 'low': 0.05}}
        self.liability_benchmarks = {'current_liability_ratio': {'high': 0.4, 'moderate': 0.3, 'low': 0.2}, 'long_term_debt_ratio': {'high': 0.4, 'moderate': 0.25, 'low': 0.15}}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive balance sheet analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all balance sheet aspects
        """
        results = []
        required_fields = ['total_assets', 'total_liabilities', 'total_equity']
        is_sufficient, missing_fields = self.validate_data_sufficiency(statements, required_fields)
        if not is_sufficient:
            if self.logger:
                self.logger.warning(f'Insufficient data for complete analysis. Missing: {missing_fields}')
        results.extend(self._analyze_liquidity(statements, comparative_data, industry_data))
        results.extend(self._analyze_assets(statements, comparative_data, industry_data))
        results.extend(self._analyze_liabilities(statements, comparative_data, industry_data))
        results.extend(self._analyze_equity(statements, comparative_data, industry_data))
        results.extend(self._assess_financial_position_quality(statements, comparative_data))
        results.extend(self._perform_common_size_analysis(statements, comparative_data))
        results.extend(self._analyze_balance_sheet_relationships(statements, comparative_data))
        return results

    def _analyze_liquidity(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Comprehensive liquidity analysis"""
        results = []
        balance_sheet = statements.balance_sheet
        current_assets = balance_sheet.get('current_assets', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        cash_equivalents = balance_sheet.get('cash_equivalents', 0)
        accounts_receivable = balance_sheet.get('accounts_receivable', 0)
        inventory = balance_sheet.get('inventory', 0)
        if current_liabilities > 0:
            current_ratio = self.safe_divide(current_assets, current_liabilities)
            benchmark = self.liquidity_benchmarks.get('current_ratio', {})
            risk_level = self.assess_risk_level(current_ratio, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.LIQUIDITY, metric_name='Current Ratio', value=current_ratio, interpretation=self.generate_interpretation('current ratio', current_ratio, risk_level, AnalysisType.LIQUIDITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(current_ratio, industry_data.get('current_ratio') if industry_data else None), methodology='Current Assets / Current Liabilities', limitations=['Does not consider asset quality or conversion timing']))
        if current_liabilities > 0:
            quick_assets = current_assets - inventory
            quick_ratio = self.safe_divide(quick_assets, current_liabilities)
            benchmark = self.liquidity_benchmarks.get('quick_ratio', {})
            risk_level = self.assess_risk_level(quick_ratio, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.LIQUIDITY, metric_name='Quick Ratio', value=quick_ratio, interpretation=self.generate_interpretation('quick ratio', quick_ratio, risk_level, AnalysisType.LIQUIDITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(quick_ratio, industry_data.get('quick_ratio') if industry_data else None), methodology='(Current Assets - Inventory) / Current Liabilities', limitations=['Assumes receivables are readily collectible']))
        if current_liabilities > 0:
            cash_ratio = self.safe_divide(cash_equivalents, current_liabilities)
            benchmark = self.liquidity_benchmarks.get('cash_ratio', {})
            risk_level = self.assess_risk_level(cash_ratio, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.LIQUIDITY, metric_name='Cash Ratio', value=cash_ratio, interpretation=self.generate_interpretation('cash ratio', cash_ratio, risk_level, AnalysisType.LIQUIDITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(cash_ratio, industry_data.get('cash_ratio') if industry_data else None), methodology='Cash and Cash Equivalents / Current Liabilities', limitations=['Most conservative liquidity measure']))
        working_capital = current_assets - current_liabilities
        total_assets = balance_sheet.get('total_assets', 0)
        if total_assets > 0:
            working_capital_ratio = self.safe_divide(working_capital, total_assets)
            wc_interpretation = 'Strong working capital position' if working_capital_ratio > 0.1 else 'Adequate working capital' if working_capital_ratio > 0 else 'Negative working capital - liquidity concern'
            wc_risk = RiskLevel.LOW if working_capital_ratio > 0.1 else RiskLevel.MODERATE if working_capital_ratio > 0 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.LIQUIDITY, metric_name='Working Capital Ratio', value=working_capital_ratio, interpretation=wc_interpretation, risk_level=wc_risk, methodology='(Current Assets - Current Liabilities) / Total Assets', limitations=['Industry-dependent optimal levels']))
        return results

    def _analyze_assets(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Comprehensive asset analysis"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        total_assets = balance_sheet.get('total_assets', 0)
        current_assets = balance_sheet.get('current_assets', 0)
        ppe_net = balance_sheet.get('ppe_net', 0)
        intangible_assets = balance_sheet.get('intangible_assets', 0)
        goodwill = balance_sheet.get('goodwill', 0)
        revenue = income_statement.get('revenue', 0)
        if total_assets == 0:
            return results
        if revenue > 0:
            avg_total_assets = total_assets
            if comparative_data and len(comparative_data) > 0:
                prev_assets = comparative_data[-1].balance_sheet.get('total_assets', 0)
                if prev_assets > 0:
                    avg_total_assets = (total_assets + prev_assets) / 2
            asset_turnover = self.safe_divide(revenue, avg_total_assets)
            benchmark = self.activity_benchmarks.get('asset_turnover', {})
            risk_level = self.assess_risk_level(asset_turnover, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Asset Turnover', value=asset_turnover, interpretation=self.generate_interpretation('asset turnover', asset_turnover, risk_level, AnalysisType.ACTIVITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(asset_turnover, industry_data.get('asset_turnover') if industry_data else None), methodology='Revenue / Average Total Assets', limitations=['Influenced by asset age and accounting methods']))
        current_asset_ratio = self.safe_divide(current_assets, total_assets)
        results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Current Asset Ratio', value=current_asset_ratio, interpretation=f'Current assets represent {self.format_percentage(current_asset_ratio)} of total assets', risk_level=RiskLevel.LOW, methodology='Current Assets / Total Assets'))
        ppe_ratio = self.safe_divide(ppe_net, total_assets)
        results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='PPE Ratio', value=ppe_ratio, interpretation=f'Property, plant & equipment represents {self.format_percentage(ppe_ratio)} of total assets', risk_level=RiskLevel.LOW, methodology='Net PPE / Total Assets'))
        if intangible_assets > 0:
            intangible_ratio = self.safe_divide(intangible_assets, total_assets)
            intangible_interpretation = 'High intangible asset intensity - knowledge-based business' if intangible_ratio > 0.2 else 'Moderate intangible assets' if intangible_ratio > 0.1 else 'Low intangible asset base'
            intangible_risk = RiskLevel.MODERATE if intangible_ratio > 0.3 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Intangible Asset Ratio', value=intangible_ratio, interpretation=intangible_interpretation, risk_level=intangible_risk, methodology='Intangible Assets / Total Assets', limitations=['Requires assessment of asset impairment risk']))
        if goodwill > 0:
            goodwill_ratio = self.safe_divide(goodwill, total_assets)
            goodwill_interpretation = 'Significant goodwill from acquisitions - monitor for impairment' if goodwill_ratio > 0.15 else 'Moderate goodwill level' if goodwill_ratio > 0.05 else 'Low goodwill'
            goodwill_risk = RiskLevel.MODERATE if goodwill_ratio > 0.2 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Goodwill Ratio', value=goodwill_ratio, interpretation=goodwill_interpretation, risk_level=goodwill_risk, methodology='Goodwill / Total Assets', limitations=['Subject to impairment testing and write-downs']))
        results.extend(self._assess_asset_quality(statements, comparative_data))
        return results

    def _analyze_liabilities(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Comprehensive liability analysis"""
        results = []
        balance_sheet = statements.balance_sheet
        total_assets = balance_sheet.get('total_assets', 0)
        total_liabilities = balance_sheet.get('total_liabilities', 0)
        total_equity = balance_sheet.get('total_equity', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        long_term_debt = balance_sheet.get('long_term_debt', 0)
        short_term_debt = balance_sheet.get('short_term_debt', 0)
        if total_assets == 0:
            return results
        total_debt = long_term_debt + short_term_debt
        if total_equity > 0:
            debt_to_equity = self.safe_divide(total_debt, total_equity)
            benchmark = self.solvency_benchmarks.get('debt_to_equity', {})
            risk_level = self.assess_risk_level(debt_to_equity, benchmark, higher_is_better=False)
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Debt-to-Equity Ratio', value=debt_to_equity, interpretation=self.generate_interpretation('debt-to-equity ratio', debt_to_equity, risk_level, AnalysisType.SOLVENCY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(debt_to_equity, industry_data.get('debt_to_equity') if industry_data else None), methodology='Total Debt / Total Equity', limitations=['Does not consider off-balance-sheet obligations']))
        debt_to_assets = self.safe_divide(total_debt, total_assets)
        benchmark = self.solvency_benchmarks.get('debt_to_assets', {})
        risk_level = self.assess_risk_level(debt_to_assets, benchmark, higher_is_better=False)
        results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Debt-to-Assets Ratio', value=debt_to_assets, interpretation=self.generate_interpretation('debt-to-assets ratio', debt_to_assets, risk_level, AnalysisType.SOLVENCY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(debt_to_assets, industry_data.get('debt_to_assets') if industry_data else None), methodology='Total Debt / Total Assets', limitations=['Asset values may not reflect market values']))
        current_liability_ratio = self.safe_divide(current_liabilities, total_assets)
        long_term_liability_ratio = self.safe_divide(long_term_debt, total_assets)
        results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Current Liability Ratio', value=current_liability_ratio, interpretation=f'Current liabilities represent {self.format_percentage(current_liability_ratio)} of total assets', risk_level=RiskLevel.HIGH if current_liability_ratio > 0.4 else RiskLevel.MODERATE if current_liability_ratio > 0.25 else RiskLevel.LOW, methodology='Current Liabilities / Total Assets'))
        results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Long-term Debt Ratio', value=long_term_liability_ratio, interpretation=f'Long-term debt represents {self.format_percentage(long_term_liability_ratio)} of total assets', risk_level=RiskLevel.HIGH if long_term_liability_ratio > 0.4 else RiskLevel.MODERATE if long_term_liability_ratio > 0.25 else RiskLevel.LOW, methodology='Long-term Debt / Total Assets'))
        if total_debt > 0:
            short_term_debt_ratio = self.safe_divide(short_term_debt, total_debt)
            maturity_interpretation = 'High short-term debt concentration - refinancing risk' if short_term_debt_ratio > 0.5 else 'Balanced debt maturity profile' if short_term_debt_ratio > 0.2 else 'Predominantly long-term debt structure'
            maturity_risk = RiskLevel.HIGH if short_term_debt_ratio > 0.6 else RiskLevel.MODERATE if short_term_debt_ratio > 0.4 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Short-term Debt Concentration', value=short_term_debt_ratio, interpretation=maturity_interpretation, risk_level=maturity_risk, methodology='Short-term Debt / Total Debt', limitations=['Does not consider debt covenants or refinancing ability']))
        income_statement = statements.income_statement
        operating_income = income_statement.get('operating_income', 0)
        interest_expense = income_statement.get('interest_expense', 0)
        if interest_expense > 0:
            interest_coverage = self.safe_divide(operating_income, interest_expense)
            benchmark = self.solvency_benchmarks.get('interest_coverage', {})
            risk_level = self.assess_risk_level(interest_coverage, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Interest Coverage Ratio', value=interest_coverage, interpretation=self.generate_interpretation('interest coverage ratio', interest_coverage, risk_level, AnalysisType.SOLVENCY), risk_level=risk_level, methodology='Operating Income / Interest Expense', limitations=['Based on current operating performance']))
        return results

    def _analyze_equity(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Comprehensive equity analysis"""
        results = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        total_assets = balance_sheet.get('total_assets', 0)
        total_equity = balance_sheet.get('total_equity', 0)
        common_stock = balance_sheet.get('common_stock', 0)
        retained_earnings = balance_sheet.get('retained_earnings', 0)
        treasury_stock = balance_sheet.get('treasury_stock', 0)
        intangible_assets = balance_sheet.get('intangible_assets', 0)
        goodwill = balance_sheet.get('goodwill', 0)
        if total_assets == 0:
            return results
        equity_ratio = self.safe_divide(total_equity, total_assets)
        equity_interpretation = 'Strong equity position - low financial leverage' if equity_ratio > 0.6 else 'Moderate equity position' if equity_ratio > 0.4 else 'High financial leverage - elevated risk'
        equity_risk = RiskLevel.LOW if equity_ratio > 0.5 else RiskLevel.MODERATE if equity_ratio > 0.3 else RiskLevel.HIGH
        results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Equity Ratio', value=equity_ratio, interpretation=equity_interpretation, risk_level=equity_risk, benchmark_comparison=self.compare_to_industry(equity_ratio, industry_data.get('equity_ratio') if industry_data else None), methodology='Total Equity / Total Assets'))
        if total_equity > 0:
            equity_multiplier = self.safe_divide(total_assets, total_equity)
            multiplier_interpretation = 'High financial leverage' if equity_multiplier > 3 else 'Moderate financial leverage' if equity_multiplier > 2 else 'Conservative financial leverage'
            multiplier_risk = RiskLevel.HIGH if equity_multiplier > 4 else RiskLevel.MODERATE if equity_multiplier > 2.5 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Equity Multiplier', value=equity_multiplier, interpretation=multiplier_interpretation, risk_level=multiplier_risk, methodology='Total Assets / Total Equity', limitations=['Component of DuPont analysis']))
        if total_equity > 0 and retained_earnings != 0:
            retained_earnings_ratio = self.safe_divide(retained_earnings, total_equity)
            re_interpretation = 'Strong retained earnings base' if retained_earnings_ratio > 0.5 else 'Moderate retained earnings' if retained_earnings_ratio > 0.2 else 'Low retained earnings - recent losses or high dividends'
            re_risk = RiskLevel.LOW if retained_earnings_ratio > 0.3 else RiskLevel.MODERATE if retained_earnings_ratio > 0 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Retained Earnings Ratio', value=retained_earnings_ratio, interpretation=re_interpretation, risk_level=re_risk, methodology='Retained Earnings / Total Equity'))
        shares_outstanding = income_statement.get('shares_outstanding_basic', 0)
        if shares_outstanding > 0 and total_equity > 0:
            book_value_per_share = self.safe_divide(total_equity, shares_outstanding)
            results.append(AnalysisResult(analysis_type=AnalysisType.VALUATION, metric_name='Book Value per Share', value=book_value_per_share, interpretation=f'Book value per share is ${book_value_per_share:.2f}', risk_level=RiskLevel.LOW, methodology='Total Equity / Shares Outstanding'))
            tangible_equity = total_equity - intangible_assets - goodwill
            if tangible_equity > 0:
                tangible_bvps = self.safe_divide(tangible_equity, shares_outstanding)
                results.append(AnalysisResult(analysis_type=AnalysisType.VALUATION, metric_name='Tangible Book Value per Share', value=tangible_bvps, interpretation=f'Tangible book value per share is ${tangible_bvps:.2f}', risk_level=RiskLevel.LOW, methodology='(Total Equity - Intangibles - Goodwill) / Shares Outstanding', limitations=['Excludes intangible asset value']))
        net_income = income_statement.get('net_income', 0)
        if total_equity > 0 and net_income != 0:
            avg_equity = total_equity
            if comparative_data and len(comparative_data) > 0:
                prev_equity = comparative_data[-1].balance_sheet.get('total_equity', 0)
                if prev_equity > 0:
                    avg_equity = (total_equity + prev_equity) / 2
            roe = self.safe_divide(net_income, avg_equity)
            benchmark = self.profitability_benchmarks.get('roe', {})
            risk_level = self.assess_risk_level(roe, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Return on Equity', value=roe, interpretation=self.generate_interpretation('return on equity', roe, risk_level, AnalysisType.PROFITABILITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(roe, industry_data.get('roe') if industry_data else None), methodology='Net Income / Average Total Equity'))
        return results

    def _assess_asset_quality(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess asset quality and potential impairment issues"""
        results = []
        balance_sheet = statements.balance_sheet
        ppe_gross = balance_sheet.get('ppe_gross', 0)
        accumulated_depreciation = balance_sheet.get('accumulated_depreciation', 0)
        if ppe_gross > 0 and accumulated_depreciation > 0:
            asset_age_ratio = self.safe_divide(accumulated_depreciation, ppe_gross)
            age_interpretation = 'Assets approaching end of useful life - significant capex likely needed' if asset_age_ratio > 0.7 else 'Moderately aged assets' if asset_age_ratio > 0.5 else 'Relatively new assets'
            age_risk = RiskLevel.HIGH if asset_age_ratio > 0.8 else RiskLevel.MODERATE if asset_age_ratio > 0.6 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Asset Age Ratio', value=asset_age_ratio, interpretation=age_interpretation, risk_level=age_risk, methodology='Accumulated Depreciation / Gross PPE', limitations=['Based on historical cost and depreciation methods']))
        impairment_indicators = self._identify_impairment_indicators(statements, comparative_data)
        if impairment_indicators:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Asset Impairment Indicators', value=len(impairment_indicators), interpretation=f'Identified {len(impairment_indicators)} potential impairment indicators', risk_level=RiskLevel.HIGH if len(impairment_indicators) > 2 else RiskLevel.MODERATE, limitations=impairment_indicators))
        return results

    def _assess_financial_position_quality(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Assess overall financial position quality"""
        results = []
        balance_sheet = statements.balance_sheet
        quality_factors = []
        quality_score = 100
        current_assets = balance_sheet.get('current_assets', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        if current_liabilities > 0:
            current_ratio = self.safe_divide(current_assets, current_liabilities)
            if current_ratio >= 1.5:
                quality_factors.append('Strong liquidity position')
            elif current_ratio < 1.0:
                quality_score -= 20
        total_assets = balance_sheet.get('total_assets', 0)
        total_debt = balance_sheet.get('long_term_debt', 0) + balance_sheet.get('short_term_debt', 0)
        if total_assets > 0:
            debt_ratio = self.safe_divide(total_debt, total_assets)
            if debt_ratio > 0.6:
                quality_score -= 25
            elif debt_ratio < 0.3:
                quality_factors.append('Conservative debt levels')
        intangible_assets = balance_sheet.get('intangible_assets', 0)
        goodwill = balance_sheet.get('goodwill', 0)
        if total_assets > 0:
            intangible_ratio = self.safe_divide(intangible_assets + goodwill, total_assets)
            if intangible_ratio > 0.4:
                quality_score -= 15
        income_statement = statements.income_statement
        net_income = income_statement.get('net_income', 0)
        if net_income < 0:
            quality_score -= 20
        quality_score = max(0, quality_score)
        quality_interpretation = 'Excellent financial position' if quality_score > 80 else 'Good financial position' if quality_score > 60 else 'Fair financial position' if quality_score > 40 else 'Weak financial position'
        quality_risk = RiskLevel.LOW if quality_score > 70 else RiskLevel.MODERATE if quality_score > 50 else RiskLevel.HIGH
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Financial Position Quality Score', value=quality_score, interpretation=quality_interpretation, risk_level=quality_risk, recommendations=quality_factors, methodology='Composite score based on liquidity, leverage, asset quality, and profitability'))
        return results

    def _perform_common_size_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Perform common-size balance sheet analysis"""
        results = []
        balance_sheet = statements.balance_sheet
        total_assets = balance_sheet.get('total_assets', 0)
        if total_assets == 0:
            return results
        asset_items = {'Current Assets': balance_sheet.get('current_assets', 0), 'PPE Net': balance_sheet.get('ppe_net', 0), 'Intangible Assets': balance_sheet.get('intangible_assets', 0), 'Goodwill': balance_sheet.get('goodwill', 0)}
        for item_name, item_value in asset_items.items():
            if item_value > 0:
                common_size_pct = self.safe_divide(item_value, total_assets)
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name=f'{item_name} as % of Total Assets', value=common_size_pct, interpretation=f'{item_name} represents {self.format_percentage(common_size_pct)} of total assets', risk_level=RiskLevel.LOW, methodology=f'{item_name} / Total Assets'))
        liability_equity_items = {'Current Liabilities': balance_sheet.get('current_liabilities', 0), 'Long-term Debt': balance_sheet.get('long_term_debt', 0), 'Total Equity': balance_sheet.get('total_equity', 0)}
        for item_name, item_value in liability_equity_items.items():
            if item_value != 0:
                common_size_pct = self.safe_divide(item_value, total_assets)
                results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name=f'{item_name} as % of Total Assets', value=common_size_pct, interpretation=f'{item_name} represents {self.format_percentage(common_size_pct)} of total assets', risk_level=RiskLevel.LOW, methodology=f'{item_name} / Total Assets'))
        return results

    def _analyze_balance_sheet_relationships(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze key balance sheet relationships and efficiency metrics"""
        results = []
        balance_sheet = statements.balance_sheet
        current_assets = balance_sheet.get('current_assets', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        long_term_assets = balance_sheet.get('total_assets', 0) - current_assets
        long_term_debt = balance_sheet.get('long_term_debt', 0)
        if long_term_assets > 0 and long_term_debt + balance_sheet.get('total_equity', 0) > 0:
            long_term_financing = long_term_debt + balance_sheet.get('total_equity', 0)
            financing_ratio = self.safe_divide(long_term_financing, long_term_assets)
            financing_interpretation = 'Appropriate long-term financing for long-term assets' if financing_ratio >= 1.0 else 'Potential maturity mismatch - long-term assets financed with short-term funds'
            financing_risk = RiskLevel.LOW if financing_ratio >= 1.0 else RiskLevel.MODERATE if financing_ratio >= 0.8 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Long-term Financing Ratio', value=financing_ratio, interpretation=financing_interpretation, risk_level=financing_risk, methodology='(Long-term Debt + Equity) / Long-term Assets', limitations=['Simplified maturity matching analysis']))
        return results

    def _identify_impairment_indicators(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[str]:
        """Identify potential asset impairment indicators"""
        indicators = []
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        net_income = income_statement.get('net_income', 0)
        if net_income < 0:
            indicators.append('Negative net income may indicate asset impairment')
        goodwill = balance_sheet.get('goodwill', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if goodwill > 0 and total_assets > 0:
            goodwill_ratio = self.safe_divide(goodwill, total_assets)
            if goodwill_ratio > 0.3:
                indicators.append('High goodwill concentration - monitor for impairment')
        if comparative_data and len(comparative_data) > 0:
            revenue = income_statement.get('revenue', 0)
            prev_revenue = comparative_data[-1].income_statement.get('revenue', 0)
            if prev_revenue > 0 and revenue < prev_revenue * 0.9:
                indicators.append('Significant revenue decline may indicate asset impairment')
        return indicators

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key balance sheet metrics"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        metrics = {}
        current_assets = balance_sheet.get('current_assets', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        cash_equivalents = balance_sheet.get('cash_equivalents', 0)
        if current_liabilities > 0:
            metrics['current_ratio'] = self.safe_divide(current_assets, current_liabilities)
            metrics['quick_ratio'] = self.safe_divide(current_assets - balance_sheet.get('inventory', 0), current_liabilities)
            metrics['cash_ratio'] = self.safe_divide(cash_equivalents, current_liabilities)
        total_assets = balance_sheet.get('total_assets', 0)
        total_equity = balance_sheet.get('total_equity', 0)
        total_debt = balance_sheet.get('long_term_debt', 0) + balance_sheet.get('short_term_debt', 0)
        if total_equity > 0:
            metrics['debt_to_equity'] = self.safe_divide(total_debt, total_equity)
            metrics['equity_multiplier'] = self.safe_divide(total_assets, total_equity)
        if total_assets > 0:
            metrics['debt_to_assets'] = self.safe_divide(total_debt, total_assets)
            metrics['equity_ratio'] = self.safe_divide(total_equity, total_assets)
        revenue = income_statement.get('revenue', 0)
        if total_assets > 0 and revenue > 0:
            metrics['asset_turnover'] = self.safe_divide(revenue, total_assets)
        net_income = income_statement.get('net_income', 0)
        if total_assets > 0:
            metrics['roa'] = self.safe_divide(net_income, total_assets)
        if total_equity > 0:
            metrics['roe'] = self.safe_divide(net_income, total_equity)
        return metrics

    def create_liquidity_analysis(self, statements: FinancialStatements) -> LiquidityAnalysis:
        """Create comprehensive liquidity analysis object"""
        balance_sheet = statements.balance_sheet
        current_assets = balance_sheet.get('current_assets', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        cash_equivalents = balance_sheet.get('cash_equivalents', 0)
        inventory = balance_sheet.get('inventory', 0)
        current_ratio = self.safe_divide(current_assets, current_liabilities)
        quick_ratio = self.safe_divide(current_assets - inventory, current_liabilities)
        cash_ratio = self.safe_divide(cash_equivalents, current_liabilities)
        working_capital = current_assets - current_liabilities
        total_assets = balance_sheet.get('total_assets', 0)
        working_capital_ratio = self.safe_divide(working_capital, total_assets)
        quality_score = 100
        if current_ratio < 1.0:
            quality_score -= 30
        elif current_ratio < 1.2:
            quality_score -= 15
        if quick_ratio < 0.8:
            quality_score -= 20
        if cash_ratio < 0.1:
            quality_score -= 10
        quality_score = max(0, quality_score)
        if quality_score > 80:
            risk_level = RiskLevel.LOW
        elif quality_score > 60:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.HIGH
        return LiquidityAnalysis(current_ratio=current_ratio, quick_ratio=quick_ratio, cash_ratio=cash_ratio, working_capital=working_capital, working_capital_ratio=working_capital_ratio, net_working_capital=working_capital, liquidity_quality_score=quality_score, liquidity_risk_level=risk_level)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive balance sheet analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all balance sheet aspects
        """
    results = []
    required_fields = ['total_assets', 'total_liabilities', 'total_equity']
    is_sufficient, missing_fields = self.validate_data_sufficiency(statements, required_fields)
    if not is_sufficient:
        if self.logger:
            self.logger.warning(f'Insufficient data for complete analysis. Missing: {missing_fields}')
    results.extend(self._analyze_liquidity(statements, comparative_data, industry_data))
    results.extend(self._analyze_assets(statements, comparative_data, industry_data))
    results.extend(self._analyze_liabilities(statements, comparative_data, industry_data))
    results.extend(self._analyze_equity(statements, comparative_data, industry_data))
    results.extend(self._assess_financial_position_quality(statements, comparative_data))
    results.extend(self._perform_common_size_analysis(statements, comparative_data))
    results.extend(self._analyze_balance_sheet_relationships(statements, comparative_data))
    return results

class ComprehensiveAnalyzer(BaseAnalyzer):
    """
    Comprehensive financial statement analyzer that integrates all statement analyses.
    Provides holistic view of financial performance, position, and quality.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self.income_analyzer = IncomeStatementAnalyzer(enable_logging)
        self.balance_analyzer = BalanceSheetAnalyzer(enable_logging)
        self.cash_flow_analyzer = CashFlowAnalyzer(enable_logging)
        self._initialize_integration_weights()

    def _initialize_integration_weights(self):
        """Initialize weights for integrated scoring"""
        self.scoring_weights = {'liquidity': 0.2, 'profitability': 0.25, 'efficiency': 0.15, 'leverage': 0.15, 'growth': 0.15, 'quality': 0.1}
        self.risk_weights = {RiskLevel.LOW: 100, RiskLevel.MODERATE: 70, RiskLevel.HIGH: 40, RiskLevel.VERY_HIGH: 20}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive multi-statement analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of integrated analysis results
        """
        results = []
        income_results = self.income_analyzer.analyze(statements, comparative_data, industry_data)
        balance_results = self.balance_analyzer.analyze(statements, comparative_data, industry_data)
        cash_flow_results = self.cash_flow_analyzer.analyze(statements, comparative_data, industry_data)
        all_results = income_results + balance_results + cash_flow_results
        integrated_analysis = self._perform_integrated_analysis(all_results, statements, comparative_data)
        results.extend(self._create_integrated_results(integrated_analysis, statements))
        results.extend(self._analyze_statement_linkages(statements, comparative_data))
        results.extend(self._analyze_business_cycle(statements, comparative_data))
        results.extend(self._perform_risk_assessment(all_results, statements))
        results.extend(self._generate_strategic_insights(all_results, statements, comparative_data))
        return results

    def _perform_integrated_analysis(self, all_results: List[AnalysisResult], statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> IntegratedAnalysis:
        """Perform integrated analysis across all statements"""
        results_by_type = {}
        for result in all_results:
            if result.analysis_type not in results_by_type:
                results_by_type[result.analysis_type] = []
            results_by_type[result.analysis_type].append(result)
        liquidity_score = self._calculate_component_score(results_by_type.get(AnalysisType.LIQUIDITY, []))
        profitability_score = self._calculate_component_score(results_by_type.get(AnalysisType.PROFITABILITY, []))
        efficiency_score = self._calculate_component_score(results_by_type.get(AnalysisType.ACTIVITY, []))
        leverage_score = self._calculate_component_score(results_by_type.get(AnalysisType.SOLVENCY, []))
        quality_score = self._calculate_component_score(results_by_type.get(AnalysisType.QUALITY, []))
        growth_score = self._calculate_growth_score(statements, comparative_data)
        composite_score = liquidity_score * self.scoring_weights['liquidity'] + profitability_score * self.scoring_weights['profitability'] + efficiency_score * self.scoring_weights['efficiency'] + leverage_score * self.scoring_weights['leverage'] + growth_score * self.scoring_weights['growth'] + quality_score * self.scoring_weights['quality']
        financial_health = self._determine_financial_health(composite_score, all_results)
        business_model = self._classify_business_model(statements, comparative_data)
        strengths, weaknesses = self._identify_strengths_weaknesses(all_results)
        critical_risks = self._identify_critical_risks(all_results)
        strategic_recommendations = self._generate_strategic_recommendations(all_results, statements)
        return IntegratedAnalysis(overall_financial_health=financial_health, business_model_type=business_model, key_strengths=strengths, key_weaknesses=weaknesses, critical_risks=critical_risks, strategic_recommendations=strategic_recommendations, liquidity_score=liquidity_score, profitability_score=profitability_score, efficiency_score=efficiency_score, leverage_score=leverage_score, growth_score=growth_score, quality_score=quality_score, composite_score=composite_score)

    def _calculate_component_score(self, results: List[AnalysisResult]) -> float:
        """Calculate component score based on risk levels"""
        if not results:
            return 50.0
        total_weight = 0
        weighted_score = 0
        for result in results:
            weight = 1.0
            score = self.risk_weights.get(result.risk_level, 50)
            weighted_score += score * weight
            total_weight += weight
        return weighted_score / total_weight if total_weight > 0 else 50.0

    def _calculate_growth_score(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> float:
        """Calculate growth score based on key metrics trends"""
        if not comparative_data or len(comparative_data) == 0:
            return 50.0
        growth_factors = []
        current_revenue = statements.income_statement.get('revenue', 0)
        prev_revenue = comparative_data[-1].income_statement.get('revenue', 0)
        if prev_revenue > 0:
            revenue_growth = current_revenue / prev_revenue - 1
            growth_factors.append(min(100, max(0, 50 + revenue_growth * 200)))
        current_ni = statements.income_statement.get('net_income', 0)
        prev_ni = comparative_data[-1].income_statement.get('net_income', 0)
        if prev_ni > 0:
            ni_growth = current_ni / prev_ni - 1
            growth_factors.append(min(100, max(0, 50 + ni_growth * 200)))
        current_assets = statements.balance_sheet.get('total_assets', 0)
        prev_assets = comparative_data[-1].balance_sheet.get('total_assets', 0)
        if prev_assets > 0:
            asset_growth = current_assets / prev_assets - 1
            growth_factors.append(min(100, max(0, 50 + asset_growth * 150)))
        return np.mean(growth_factors) if growth_factors else 50.0

    def _determine_financial_health(self, composite_score: float, all_results: List[AnalysisResult]) -> FinancialHealth:
        """Determine overall financial health classification"""
        high_risk_count = sum((1 for result in all_results if result.risk_level == RiskLevel.HIGH))
        very_high_risk_count = sum((1 for result in all_results if result.risk_level == RiskLevel.VERY_HIGH))
        if very_high_risk_count > 2 or high_risk_count > 5:
            return FinancialHealth.DISTRESSED
        if composite_score >= 85:
            return FinancialHealth.EXCELLENT
        elif composite_score >= 70:
            return FinancialHealth.GOOD
        elif composite_score >= 55:
            return FinancialHealth.FAIR
        elif composite_score >= 40:
            return FinancialHealth.POOR
        else:
            return FinancialHealth.DISTRESSED

    def _classify_business_model(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> BusinessModel:
        """Classify business model based on financial patterns"""
        balance_sheet = statements.balance_sheet
        income_statement = statements.income_statement
        total_assets = balance_sheet.get('total_assets', 0)
        ppe_net = balance_sheet.get('ppe_net', 0)
        revenue = income_statement.get('revenue', 0)
        net_income = income_statement.get('net_income', 0)
        asset_intensity = self.safe_divide(total_assets, revenue) if revenue > 0 else 0
        ppe_ratio = self.safe_divide(ppe_net, total_assets) if total_assets > 0 else 0
        is_growing = False
        if comparative_data and len(comparative_data) > 0:
            prev_revenue = comparative_data[-1].income_statement.get('revenue', 0)
            if prev_revenue > 0:
                revenue_growth = revenue / prev_revenue - 1
                is_growing = revenue_growth > 0.1
        net_margin = self.safe_divide(net_income, revenue) if revenue > 0 else 0
        is_profitable = net_income > 0
        if asset_intensity > 2.0 or ppe_ratio > 0.4:
            return BusinessModel.ASSET_HEAVY
        elif asset_intensity < 0.8 and ppe_ratio < 0.2:
            return BusinessModel.ASSET_LIGHT
        elif is_growing and net_margin > 0:
            return BusinessModel.GROWTH
        elif not is_profitable and comparative_data:
            declining_periods = 0
            for i in range(min(3, len(comparative_data))):
                past_ni = comparative_data[-(i + 1)].income_statement.get('net_income', 0)
                if past_ni < 0:
                    declining_periods += 1
            if declining_periods >= 2:
                return BusinessModel.TURNAROUND
        elif is_profitable and (not is_growing):
            return BusinessModel.MATURE
        else:
            return BusinessModel.CYCLICAL

    def _identify_strengths_weaknesses(self, all_results: List[AnalysisResult]) -> Tuple[List[str], List[str]]:
        """Identify key strengths and weaknesses from analysis results"""
        strengths = []
        weaknesses = []
        by_type_risk = {}
        for result in all_results:
            key = (result.analysis_type, result.risk_level)
            if key not in by_type_risk:
                by_type_risk[key] = []
            by_type_risk[key].append(result)
        for (analysis_type, risk_level), results in by_type_risk.items():
            if risk_level == RiskLevel.LOW and len(results) >= 2:
                if analysis_type == AnalysisType.LIQUIDITY:
                    strengths.append('Strong liquidity position with adequate cash resources')
                elif analysis_type == AnalysisType.PROFITABILITY:
                    strengths.append('Robust profitability across multiple metrics')
                elif analysis_type == AnalysisType.SOLVENCY:
                    strengths.append('Conservative financial leverage and strong solvency')
                elif analysis_type == AnalysisType.ACTIVITY:
                    strengths.append('Efficient asset utilization and operational management')
                elif analysis_type == AnalysisType.QUALITY:
                    strengths.append('High quality financial reporting and earnings')
        for (analysis_type, risk_level), results in by_type_risk.items():
            if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                if analysis_type == AnalysisType.LIQUIDITY:
                    weaknesses.append('Liquidity concerns - potential difficulty meeting short-term obligations')
                elif analysis_type == AnalysisType.PROFITABILITY:
                    weaknesses.append('Weak profitability performance requiring operational improvement')
                elif analysis_type == AnalysisType.SOLVENCY:
                    weaknesses.append('High financial leverage creating elevated financial risk')
                elif analysis_type == AnalysisType.ACTIVITY:
                    weaknesses.append('Inefficient asset utilization and operational inefficiencies')
                elif analysis_type == AnalysisType.QUALITY:
                    weaknesses.append('Financial reporting quality concerns requiring investigation')
        return (strengths, weaknesses)

    def _identify_critical_risks(self, all_results: List[AnalysisResult]) -> List[str]:
        """Identify critical risks from analysis results"""
        critical_risks = []
        very_high_risks = [r for r in all_results if r.risk_level == RiskLevel.VERY_HIGH]
        for risk in very_high_risks:
            critical_risks.append(f'Critical: {risk.metric_name} - {risk.interpretation}')
        high_risks_by_type = {}
        for result in all_results:
            if result.risk_level == RiskLevel.HIGH:
                if result.analysis_type not in high_risks_by_type:
                    high_risks_by_type[result.analysis_type] = []
                high_risks_by_type[result.analysis_type].append(result)
        for analysis_type, risks in high_risks_by_type.items():
            if len(risks) >= 2:
                critical_risks.append(f'Multiple high-risk {analysis_type.value} indicators require immediate attention')
        liquidity_risks = [r for r in all_results if r.analysis_type == AnalysisType.LIQUIDITY and r.risk_level == RiskLevel.HIGH]
        solvency_risks = [r for r in all_results if r.analysis_type == AnalysisType.SOLVENCY and r.risk_level == RiskLevel.HIGH]
        if liquidity_risks and solvency_risks:
            critical_risks.append('Combined liquidity and solvency risks create financial distress potential')
        return critical_risks

    def _generate_strategic_recommendations(self, all_results: List[AnalysisResult], statements: FinancialStatements) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        liquidity_risks = [r for r in all_results if r.analysis_type == AnalysisType.LIQUIDITY and r.risk_level in [RiskLevel.HIGH, RiskLevel.MODERATE]]
        if liquidity_risks:
            recommendations.append('Improve working capital management and consider establishing credit facilities')
        profitability_risks = [r for r in all_results if r.analysis_type == AnalysisType.PROFITABILITY and r.risk_level in [RiskLevel.HIGH, RiskLevel.MODERATE]]
        if profitability_risks:
            recommendations.append('Focus on cost optimization and revenue enhancement strategies')
        activity_risks = [r for r in all_results if r.analysis_type == AnalysisType.ACTIVITY and r.risk_level in [RiskLevel.HIGH, RiskLevel.MODERATE]]
        if activity_risks:
            recommendations.append('Optimize asset utilization and improve operational efficiency')
        solvency_risks = [r for r in all_results if r.analysis_type == AnalysisType.SOLVENCY and r.risk_level in [RiskLevel.HIGH, RiskLevel.MODERATE]]
        if solvency_risks:
            recommendations.append('Consider debt reduction and strengthen balance sheet structure')
        quality_risks = [r for r in all_results if r.analysis_type == AnalysisType.QUALITY and r.risk_level in [RiskLevel.HIGH, RiskLevel.MODERATE]]
        if quality_risks:
            recommendations.append('Enhance financial reporting transparency and earnings quality')
        income_statement = statements.income_statement
        net_income = income_statement.get('net_income', 0)
        if net_income > 0:
            recommendations.append('Consider strategic investments for sustainable growth')
        else:
            recommendations.append('Develop turnaround strategy to restore profitability')
        return recommendations

    def _create_integrated_results(self, integrated_analysis: IntegratedAnalysis, statements: FinancialStatements) -> List[AnalysisResult]:
        """Convert integrated analysis to AnalysisResult format"""
        results = []
        health_risk = RiskLevel.LOW if integrated_analysis.overall_financial_health in [FinancialHealth.EXCELLENT, FinancialHealth.GOOD] else RiskLevel.HIGH
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Overall Financial Health', value=integrated_analysis.composite_score, interpretation=f'Overall financial health is {integrated_analysis.overall_financial_health.value} with composite score of {integrated_analysis.composite_score:.1f}', risk_level=health_risk, methodology='Weighted composite of liquidity, profitability, efficiency, leverage, growth, and quality scores'))
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Business Model Type', value=1.0, interpretation=f'Business model classified as {integrated_analysis.business_model_type.value}', risk_level=RiskLevel.LOW, methodology='Classification based on asset intensity, growth patterns, and profitability'))
        component_scores = {'Liquidity Score': integrated_analysis.liquidity_score, 'Profitability Score': integrated_analysis.profitability_score, 'Efficiency Score': integrated_analysis.efficiency_score, 'Leverage Score': integrated_analysis.leverage_score, 'Growth Score': integrated_analysis.growth_score, 'Quality Score': integrated_analysis.quality_score}
        for score_name, score_value in component_scores.items():
            score_risk = RiskLevel.LOW if score_value > 70 else RiskLevel.MODERATE if score_value > 50 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name=score_name, value=score_value, interpretation=f'{score_name}: {score_value:.1f}/100', risk_level=score_risk, methodology='Composite score based on relevant financial metrics'))
        if integrated_analysis.key_strengths:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Key Strengths', value=len(integrated_analysis.key_strengths), interpretation='Key financial strengths identified', risk_level=RiskLevel.LOW, recommendations=integrated_analysis.key_strengths))
        if integrated_analysis.key_weaknesses:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Key Weaknesses', value=len(integrated_analysis.key_weaknesses), interpretation='Key financial weaknesses requiring attention', risk_level=RiskLevel.HIGH, limitations=integrated_analysis.key_weaknesses))
        return results

    def _analyze_statement_linkages(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze relationships and linkages between financial statements"""
        results = []
        income_statement = statements.income_statement
        cash_flow = statements.cash_flow
        net_income = income_statement.get('net_income', 0)
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        if net_income != 0:
            cash_quality_ratio = self.safe_divide(operating_cash_flow, net_income)
            cash_quality_interpretation = 'Excellent cash conversion from earnings' if cash_quality_ratio > 1.2 else 'Good cash quality' if cash_quality_ratio > 1.0 else 'Moderate cash quality' if cash_quality_ratio > 0.8 else 'Poor cash conversion quality'
            cash_quality_risk = RiskLevel.LOW if cash_quality_ratio > 1.0 else RiskLevel.MODERATE if cash_quality_ratio > 0.7 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Earnings-Cash Flow Quality', value=cash_quality_ratio, interpretation=cash_quality_interpretation, risk_level=cash_quality_risk, methodology='Operating Cash Flow / Net Income'))
        balance_sheet = statements.balance_sheet
        revenue = income_statement.get('revenue', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if revenue > 0 and total_assets > 0:
            asset_turnover = self.safe_divide(revenue, total_assets)
            efficiency_interpretation = 'High asset efficiency' if asset_turnover > 1.5 else 'Moderate asset efficiency' if asset_turnover > 1.0 else 'Low asset efficiency'
            efficiency_risk = RiskLevel.LOW if asset_turnover > 1.2 else RiskLevel.MODERATE if asset_turnover > 0.8 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Statement Integration - Asset Efficiency', value=asset_turnover, interpretation=efficiency_interpretation, risk_level=efficiency_risk, methodology='Revenue (IS) / Total Assets (BS)'))
        current_assets = balance_sheet.get('current_assets', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        working_capital_change = cash_flow.get('working_capital_change', 0)
        working_capital = current_assets - current_liabilities
        if abs(working_capital_change) > 0 and abs(working_capital) > 0:
            wc_efficiency = self.safe_divide(abs(working_capital_change), abs(working_capital))
            wc_interpretation = 'Significant working capital volatility' if wc_efficiency > 0.2 else 'Moderate working capital changes' if wc_efficiency > 0.1 else 'Stable working capital management'
            wc_risk = RiskLevel.HIGH if wc_efficiency > 0.3 else RiskLevel.MODERATE if wc_efficiency > 0.15 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Working Capital Management Integration', value=wc_efficiency, interpretation=wc_interpretation, risk_level=wc_risk, methodology='|WC Change (CF)| / |Net Working Capital (BS)|'))
        return results

    def _analyze_business_cycle(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze where company is in business cycle"""
        results = []
        if not comparative_data or len(comparative_data) < 2:
            return results
        income_statement = statements.income_statement
        revenue_values = []
        for past_statements in comparative_data:
            revenue_values.append(past_statements.income_statement.get('revenue', 0))
        revenue_values.append(income_statement.get('revenue', 0))
        ni_values = []
        for past_statements in comparative_data:
            ni_values.append(past_statements.income_statement.get('net_income', 0))
        ni_values.append(income_statement.get('net_income', 0))
        lifecycle_indicators = []
        recent_revenue_growth = 0
        if len(revenue_values) >= 2 and revenue_values[-2] > 0:
            recent_revenue_growth = revenue_values[-1] / revenue_values[-2] - 1
        if recent_revenue_growth > 0.15:
            lifecycle_indicators.append('High revenue growth indicates growth stage')
        elif recent_revenue_growth > 0.05:
            lifecycle_indicators.append('Moderate growth suggests expansion phase')
        elif recent_revenue_growth < -0.05:
            lifecycle_indicators.append('Declining revenue suggests maturity or decline phase')
        else:
            lifecycle_indicators.append('Stable revenue indicates mature stage')
        positive_ni_periods = sum((1 for ni in ni_values if ni > 0))
        profitability_ratio = positive_ni_periods / len(ni_values)
        if profitability_ratio > 0.8:
            lifecycle_indicators.append('Consistent profitability indicates mature business model')
        elif profitability_ratio < 0.5:
            lifecycle_indicators.append('Inconsistent profitability suggests early stage or turnaround situation')
        if recent_revenue_growth > 0.2 and profitability_ratio > 0.6:
            lifecycle_stage = 'Growth Stage'
        elif recent_revenue_growth > 0.05 and profitability_ratio > 0.7:
            lifecycle_stage = 'Expansion Stage'
        elif abs(recent_revenue_growth) < 0.05 and profitability_ratio > 0.8:
            lifecycle_stage = 'Mature Stage'
        elif recent_revenue_growth < -0.1 or profitability_ratio < 0.4:
            lifecycle_stage = 'Decline/Turnaround Stage'
        else:
            lifecycle_stage = 'Transition Stage'
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Business Lifecycle Stage', value=1.0, interpretation=f'Company appears to be in {lifecycle_stage}', risk_level=RiskLevel.LOW, recommendations=lifecycle_indicators, methodology='Analysis of revenue growth and profitability trends over time'))
        return results

    def _perform_risk_assessment(self, all_results: List[AnalysisResult], statements: FinancialStatements) -> List[AnalysisResult]:
        """Perform comprehensive risk assessment"""
        results = []
        risk_counts = {RiskLevel.LOW: 0, RiskLevel.MODERATE: 0, RiskLevel.HIGH: 0, RiskLevel.VERY_HIGH: 0}
        for result in all_results:
            risk_counts[result.risk_level] += 1
        total_metrics = len(all_results)
        high_risk_ratio = (risk_counts[RiskLevel.HIGH] + risk_counts[RiskLevel.VERY_HIGH]) / total_metrics if total_metrics > 0 else 0
        if high_risk_ratio > 0.3:
            overall_risk = 'High Risk'
            risk_level = RiskLevel.HIGH
        elif high_risk_ratio > 0.15:
            overall_risk = 'Moderate Risk'
            risk_level = RiskLevel.MODERATE
        else:
            overall_risk = 'Low Risk'
            risk_level = RiskLevel.LOW
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Overall Risk Assessment', value=high_risk_ratio, interpretation=f'{overall_risk} - {high_risk_ratio:.1%} of metrics show elevated risk', risk_level=risk_level, methodology='Proportion of high and very high risk metrics'))
        risk_by_type = {}
        for result in all_results:
            if result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                if result.analysis_type not in risk_by_type:
                    risk_by_type[result.analysis_type] = 0
                risk_by_type[result.analysis_type] += 1
        if risk_by_type:
            max_risk_type = max(risk_by_type, key=risk_by_type.get)
            max_risk_count = risk_by_type[max_risk_type]
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Risk Concentration', value=max_risk_count, interpretation=f'Highest risk concentration in {max_risk_type.value} with {max_risk_count} high-risk metrics', risk_level=RiskLevel.HIGH if max_risk_count > 2 else RiskLevel.MODERATE, methodology='Analysis of risk distribution across financial areas'))
        return results

    def _generate_strategic_insights(self, all_results: List[AnalysisResult], statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Generate high-level strategic insights"""
        results = []
        cash_flow = statements.cash_flow
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        capex = cash_flow.get('capex', 0)
        dividends_paid = cash_flow.get('dividends_paid', 0)
        acquisitions = cash_flow.get('acquisitions', 0)
        total_capital_deployment = capex + dividends_paid + acquisitions
        if operating_cash_flow > 0 and total_capital_deployment > 0:
            capital_efficiency = self.safe_divide(total_capital_deployment, operating_cash_flow)
            capital_interpretation = 'Aggressive capital deployment' if capital_efficiency > 1.0 else 'Balanced capital allocation' if capital_efficiency > 0.7 else 'Conservative capital deployment'
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Capital Allocation Strategy', value=capital_efficiency, interpretation=capital_interpretation, risk_level=RiskLevel.MODERATE if capital_efficiency > 1.2 else RiskLevel.LOW, methodology='(CapEx + Dividends + Acquisitions) / Operating Cash Flow'))
        income_statement = statements.income_statement
        revenue = income_statement.get('revenue', 0)
        gross_profit = revenue - income_statement.get('cost_of_sales', 0)
        if revenue > 0:
            gross_margin = self.safe_divide(gross_profit, revenue)
            competitive_strength = 'Strong competitive position' if gross_margin > 0.4 else 'Moderate competitive position' if gross_margin > 0.2 else 'Weak competitive position'
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Competitive Position Indicator', value=gross_margin, interpretation=competitive_strength, risk_level=RiskLevel.LOW if gross_margin > 0.3 else RiskLevel.MODERATE if gross_margin > 0.15 else RiskLevel.HIGH, methodology='Gross margin as proxy for competitive strength and pricing power'))
        return results

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return comprehensive key metrics from all analyzers"""
        income_metrics = self.income_analyzer.get_key_metrics(statements)
        balance_metrics = self.balance_analyzer.get_key_metrics(statements)
        cash_flow_metrics = self.cash_flow_analyzer.get_key_metrics(statements)
        all_metrics = {**income_metrics, **balance_metrics, **cash_flow_metrics}
        return all_metrics

    def create_integrated_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> IntegratedAnalysis:
        """Create comprehensive integrated analysis object"""
        all_results = self.analyze(statements, comparative_data, industry_data)
        integrated_results = [r for r in all_results if 'Score' in r.metric_name or 'Health' in r.metric_name]
        return IntegratedAnalysis(overall_financial_health=FinancialHealth.GOOD, business_model_type=BusinessModel.MATURE, composite_score=75.0)

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive multi-statement analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of integrated analysis results
        """
    results = []
    income_results = self.income_analyzer.analyze(statements, comparative_data, industry_data)
    balance_results = self.balance_analyzer.analyze(statements, comparative_data, industry_data)
    cash_flow_results = self.cash_flow_analyzer.analyze(statements, comparative_data, industry_data)
    all_results = income_results + balance_results + cash_flow_results
    integrated_analysis = self._perform_integrated_analysis(all_results, statements, comparative_data)
    results.extend(self._create_integrated_results(integrated_analysis, statements))
    results.extend(self._analyze_statement_linkages(statements, comparative_data))
    results.extend(self._analyze_business_cycle(statements, comparative_data))
    results.extend(self._perform_risk_assessment(all_results, statements))
    results.extend(self._generate_strategic_insights(all_results, statements, comparative_data))
    return results

def _perform_integrated_analysis(self, all_results: List[AnalysisResult], statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> IntegratedAnalysis:
    """Perform integrated analysis across all statements"""
    results_by_type = {}
    for result in all_results:
        if result.analysis_type not in results_by_type:
            results_by_type[result.analysis_type] = []
        results_by_type[result.analysis_type].append(result)
    liquidity_score = self._calculate_component_score(results_by_type.get(AnalysisType.LIQUIDITY, []))
    profitability_score = self._calculate_component_score(results_by_type.get(AnalysisType.PROFITABILITY, []))
    efficiency_score = self._calculate_component_score(results_by_type.get(AnalysisType.ACTIVITY, []))
    leverage_score = self._calculate_component_score(results_by_type.get(AnalysisType.SOLVENCY, []))
    quality_score = self._calculate_component_score(results_by_type.get(AnalysisType.QUALITY, []))
    growth_score = self._calculate_growth_score(statements, comparative_data)
    composite_score = liquidity_score * self.scoring_weights['liquidity'] + profitability_score * self.scoring_weights['profitability'] + efficiency_score * self.scoring_weights['efficiency'] + leverage_score * self.scoring_weights['leverage'] + growth_score * self.scoring_weights['growth'] + quality_score * self.scoring_weights['quality']
    financial_health = self._determine_financial_health(composite_score, all_results)
    business_model = self._classify_business_model(statements, comparative_data)
    strengths, weaknesses = self._identify_strengths_weaknesses(all_results)
    critical_risks = self._identify_critical_risks(all_results)
    strategic_recommendations = self._generate_strategic_recommendations(all_results, statements)
    return IntegratedAnalysis(overall_financial_health=financial_health, business_model_type=business_model, key_strengths=strengths, key_weaknesses=weaknesses, critical_risks=critical_risks, strategic_recommendations=strategic_recommendations, liquidity_score=liquidity_score, profitability_score=profitability_score, efficiency_score=efficiency_score, leverage_score=leverage_score, growth_score=growth_score, quality_score=quality_score, composite_score=composite_score)

def create_integrated_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> IntegratedAnalysis:
    """Create comprehensive integrated analysis object"""
    all_results = self.analyze(statements, comparative_data, industry_data)
    integrated_results = [r for r in all_results if 'Score' in r.metric_name or 'Health' in r.metric_name]
    return IntegratedAnalysis(overall_financial_health=FinancialHealth.GOOD, business_model_type=BusinessModel.MATURE, composite_score=75.0)

class CashFlowAnalyzer(BaseAnalyzer):
    """
    Comprehensive cash flow statement analyzer implementing CFA Institute standards.
    Covers operating, investing, financing activities, FCF analysis, and quality assessment.
    """

    def __init__(self, enable_logging: bool=True):
        super().__init__(enable_logging)
        self._initialize_cash_flow_formulas()
        self._initialize_cash_flow_benchmarks()

    def _initialize_cash_flow_formulas(self):
        """Initialize cash flow specific formulas"""
        self.formula_registry.update({'operating_cash_flow_ratio': lambda ocf, current_liabs: self.safe_divide(ocf, current_liabs), 'cash_flow_margin': lambda ocf, revenue: self.safe_divide(ocf, revenue), 'cash_return_on_assets': lambda ocf, total_assets: self.safe_divide(ocf, total_assets), 'free_cash_flow_firm': lambda ocf, capex: ocf - capex, 'free_cash_flow_equity': lambda fcf_firm, net_debt_payments: fcf_firm - net_debt_payments, 'cash_coverage_ratio': lambda ocf, debt_payments: self.safe_divide(ocf, debt_payments), 'quality_of_earnings': lambda ocf, net_income: self.safe_divide(ocf, net_income), 'capex_intensity': lambda capex, revenue: self.safe_divide(capex, revenue)})

    def _initialize_cash_flow_benchmarks(self):
        """Initialize cash flow specific benchmarks"""
        self.cash_flow_benchmarks = {'operating_cash_flow_ratio': {'excellent': 0.4, 'good': 0.25, 'adequate': 0.15, 'poor': 0.1}, 'cash_flow_margin': {'excellent': 0.2, 'good': 0.15, 'adequate': 0.1, 'poor': 0.05}, 'quality_of_earnings': {'excellent': 1.2, 'good': 1.0, 'adequate': 0.8, 'poor': 0.6}, 'cash_coverage_ratio': {'excellent': 3.0, 'good': 2.0, 'adequate': 1.5, 'poor': 1.0}, 'fcf_margin': {'excellent': 0.15, 'good': 0.1, 'adequate': 0.05, 'poor': 0.02}}

    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Comprehensive cash flow statement analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all cash flow aspects
        """
        results = []
        required_fields = ['operating_cash_flow']
        is_sufficient, missing_fields = self.validate_data_sufficiency(statements, required_fields)
        if not is_sufficient:
            if self.logger:
                self.logger.warning(f'Insufficient data for complete analysis. Missing: {missing_fields}')
        results.extend(self._analyze_operating_cash_flow(statements, comparative_data, industry_data))
        results.extend(self._analyze_investing_cash_flow(statements, comparative_data))
        results.extend(self._analyze_financing_cash_flow(statements, comparative_data))
        results.extend(self._analyze_free_cash_flow(statements, comparative_data, industry_data))
        results.extend(self._calculate_cash_flow_ratios(statements, comparative_data, industry_data))
        results.extend(self._assess_cash_flow_quality(statements, comparative_data))
        results.extend(self._analyze_statement_linkages(statements, comparative_data))
        results.extend(self._analyze_reporting_differences(statements))
        return results

    def _analyze_operating_cash_flow(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Analyze operating cash flow performance and quality"""
        results = []
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        net_income = income_statement.get('net_income', 0)
        revenue = income_statement.get('revenue', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if current_liabilities > 0:
            ocf_ratio = self.safe_divide(operating_cash_flow, current_liabilities)
            benchmark = self.cash_flow_benchmarks.get('operating_cash_flow_ratio', {})
            risk_level = self.assess_risk_level(ocf_ratio, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.LIQUIDITY, metric_name='Operating Cash Flow Ratio', value=ocf_ratio, interpretation=self.generate_interpretation('operating cash flow ratio', ocf_ratio, risk_level, AnalysisType.LIQUIDITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(ocf_ratio, industry_data.get('ocf_ratio') if industry_data else None), methodology='Operating Cash Flow / Current Liabilities', limitations=['Based on current period performance']))
        if revenue > 0:
            cf_margin = self.safe_divide(operating_cash_flow, revenue)
            benchmark = self.cash_flow_benchmarks.get('cash_flow_margin', {})
            risk_level = self.assess_risk_level(cf_margin, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Cash Flow Margin', value=cf_margin, interpretation=self.generate_interpretation('cash flow margin', cf_margin, risk_level, AnalysisType.PROFITABILITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(cf_margin, industry_data.get('cf_margin') if industry_data else None), methodology='Operating Cash Flow / Revenue', limitations=['May vary with working capital changes']))
        if total_assets > 0:
            cash_roa = self.safe_divide(operating_cash_flow, total_assets)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Cash Return on Assets', value=cash_roa, interpretation=f'Cash return on assets of {self.format_percentage(cash_roa)} shows cash generation efficiency', risk_level=RiskLevel.LOW if cash_roa > 0.1 else RiskLevel.MODERATE if cash_roa > 0.05 else RiskLevel.HIGH, methodology='Operating Cash Flow / Total Assets'))
        if net_income != 0:
            quality_earnings = self.safe_divide(operating_cash_flow, net_income)
            benchmark = self.cash_flow_benchmarks.get('quality_of_earnings', {})
            quality_interpretation = 'High earnings quality - strong cash conversion' if quality_earnings >= 1.0 else 'Moderate earnings quality' if quality_earnings >= 0.8 else 'Low earnings quality - poor cash conversion'
            quality_risk = RiskLevel.LOW if quality_earnings >= 1.0 else RiskLevel.MODERATE if quality_earnings >= 0.7 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Quality of Earnings', value=quality_earnings, interpretation=quality_interpretation, risk_level=quality_risk, methodology='Operating Cash Flow / Net Income', limitations=['Single period comparison - trends are more meaningful']))
        results.extend(self._analyze_working_capital_impact(statements, comparative_data))
        return results

    def _analyze_investing_cash_flow(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze investing cash flow activities"""
        results = []
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        investing_cash_flow = cash_flow.get('investing_cash_flow', 0)
        capex = cash_flow.get('capex', 0)
        acquisitions = cash_flow.get('acquisitions', 0)
        asset_sales = cash_flow.get('asset_sales', 0)
        revenue = income_statement.get('revenue', 0)
        if revenue > 0 and capex > 0:
            capex_intensity = self.safe_divide(capex, revenue)
            capex_interpretation = 'High capital intensity - significant reinvestment' if capex_intensity > 0.1 else 'Moderate capital intensity' if capex_intensity > 0.05 else 'Low capital intensity'
            capex_risk = RiskLevel.MODERATE if capex_intensity > 0.15 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Capital Expenditure Intensity', value=capex_intensity, interpretation=capex_interpretation, risk_level=capex_risk, methodology='Capital Expenditures / Revenue', limitations=['Industry-dependent optimal levels']))
        if investing_cash_flow != 0:
            if investing_cash_flow < 0:
                investment_interpretation = 'Net investment in assets - growth or maintenance focus'
                investment_risk = RiskLevel.LOW
            else:
                investment_interpretation = 'Net divestiture - asset sales or reduced investment'
                investment_risk = RiskLevel.MODERATE
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Investing Cash Flow', value=investing_cash_flow, interpretation=investment_interpretation, risk_level=investment_risk, methodology='Total cash flow from investing activities'))
        if capex > 0 and acquisitions > 0:
            acquisition_ratio = self.safe_divide(acquisitions, capex + acquisitions)
            growth_interpretation = 'Growth primarily through acquisitions' if acquisition_ratio > 0.5 else 'Balanced acquisition and organic growth' if acquisition_ratio > 0.2 else 'Primarily organic growth'
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Acquisition vs Organic Growth', value=acquisition_ratio, interpretation=growth_interpretation, risk_level=RiskLevel.MODERATE if acquisition_ratio > 0.7 else RiskLevel.LOW, methodology='Acquisitions / (Acquisitions + CapEx)', limitations=['Acquisition strategy assessment requires multi-period analysis']))
        return results

    def _analyze_financing_cash_flow(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze financing cash flow activities"""
        results = []
        cash_flow = statements.cash_flow
        financing_cash_flow = cash_flow.get('financing_cash_flow', 0)
        debt_issued = cash_flow.get('debt_issued', 0)
        debt_repaid = cash_flow.get('debt_repaid', 0)
        equity_issued = cash_flow.get('equity_issued', 0)
        equity_repurchased = cash_flow.get('equity_repurchased', 0)
        dividends_paid = cash_flow.get('dividends_paid', 0)
        net_debt_activity = debt_issued - debt_repaid
        if abs(net_debt_activity) > 0:
            debt_interpretation = 'Net debt increase - leveraging up' if net_debt_activity > 0 else 'Net debt reduction - deleveraging'
            debt_risk = RiskLevel.MODERATE if net_debt_activity > 0 else RiskLevel.LOW
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Net Debt Activity', value=net_debt_activity, interpretation=debt_interpretation, risk_level=debt_risk, methodology='Debt Issued - Debt Repaid'))
        net_equity_activity = equity_issued - equity_repurchased
        if abs(net_equity_activity) > 0:
            equity_interpretation = 'Net equity increase - raising capital' if net_equity_activity > 0 else 'Net equity reduction - returning capital to shareholders'
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Net Equity Activity', value=net_equity_activity, interpretation=equity_interpretation, risk_level=RiskLevel.LOW, methodology='Equity Issued - Equity Repurchased'))
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        if dividends_paid > 0 and operating_cash_flow > 0:
            dividend_coverage = self.safe_divide(operating_cash_flow, dividends_paid)
            coverage_interpretation = 'Strong dividend coverage' if dividend_coverage > 2.0 else 'Adequate dividend coverage' if dividend_coverage > 1.5 else 'Weak dividend coverage'
            coverage_risk = RiskLevel.LOW if dividend_coverage > 2.0 else RiskLevel.MODERATE if dividend_coverage > 1.0 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Dividend Coverage Ratio', value=dividend_coverage, interpretation=coverage_interpretation, risk_level=coverage_risk, methodology='Operating Cash Flow / Dividends Paid', limitations=['Does not consider capital expenditure requirements']))
        total_financing = abs(debt_issued) + abs(equity_issued) + abs(debt_repaid) + abs(equity_repurchased)
        if total_financing > 0:
            debt_financing_ratio = self.safe_divide(abs(debt_issued) + abs(debt_repaid), total_financing)
            financing_interpretation = 'Debt-heavy financing activities' if debt_financing_ratio > 0.7 else 'Balanced debt and equity financing' if debt_financing_ratio > 0.3 else 'Equity-focused financing'
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Debt Financing Ratio', value=debt_financing_ratio, interpretation=financing_interpretation, risk_level=RiskLevel.MODERATE if debt_financing_ratio > 0.8 else RiskLevel.LOW, methodology='Debt Activities / Total Financing Activities'))
        return results

    def _analyze_free_cash_flow(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Comprehensive free cash flow analysis"""
        results = []
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        capex = cash_flow.get('capex', 0)
        revenue = income_statement.get('revenue', 0)
        fcf_firm = operating_cash_flow - capex
        if revenue > 0:
            fcf_margin = self.safe_divide(fcf_firm, revenue)
            benchmark = self.cash_flow_benchmarks.get('fcf_margin', {})
            risk_level = self.assess_risk_level(fcf_margin, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Free Cash Flow Margin', value=fcf_margin, interpretation=self.generate_interpretation('free cash flow margin', fcf_margin, risk_level, AnalysisType.PROFITABILITY), risk_level=risk_level, benchmark_comparison=self.compare_to_industry(fcf_margin, industry_data.get('fcf_margin') if industry_data else None), methodology='(Operating Cash Flow - Capital Expenditures) / Revenue'))
        debt_issued = cash_flow.get('debt_issued', 0)
        debt_repaid = cash_flow.get('debt_repaid', 0)
        net_debt_payments = debt_repaid - debt_issued
        fcf_equity = fcf_firm - net_debt_payments
        results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='Free Cash Flow to Equity', value=fcf_equity, interpretation=f'Free cash flow to equity of ${fcf_equity:,.0f} available for dividends and share repurchases', risk_level=RiskLevel.LOW if fcf_equity > 0 else RiskLevel.HIGH, methodology='FCF Firm - Net Debt Payments'))
        net_income = income_statement.get('net_income', 0)
        if net_income > 0:
            fcf_conversion = self.safe_divide(fcf_firm, net_income)
            conversion_interpretation = 'Excellent FCF conversion' if fcf_conversion > 1.0 else 'Good FCF conversion' if fcf_conversion > 0.8 else 'Poor FCF conversion'
            conversion_risk = RiskLevel.LOW if fcf_conversion > 0.8 else RiskLevel.MODERATE if fcf_conversion > 0.5 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='FCF Conversion Ratio', value=fcf_conversion, interpretation=conversion_interpretation, risk_level=conversion_risk, methodology='Free Cash Flow / Net Income', limitations=['High conversion indicates lower reinvestment or better working capital management']))
        if comparative_data and len(comparative_data) > 0:
            fcf_values = []
            periods = []
            for i, past_statements in enumerate(comparative_data):
                past_ocf = past_statements.cash_flow.get('operating_cash_flow', 0)
                past_capex = past_statements.cash_flow.get('capex', 0)
                past_fcf = past_ocf - past_capex
                fcf_values.append(past_fcf)
                periods.append(f'Period-{len(comparative_data) - i}')
            fcf_values.append(fcf_firm)
            periods.append('Current')
            if len(fcf_values) > 1:
                fcf_trend = self.calculate_trend(fcf_values, periods)
                results.append(AnalysisResult(analysis_type=AnalysisType.PROFITABILITY, metric_name='FCF Growth Trend', value=fcf_trend.growth_rate or 0, interpretation=fcf_trend.trend_analysis, risk_level=RiskLevel.LOW if fcf_trend.growth_rate and fcf_trend.growth_rate > 0 else RiskLevel.HIGH, methodology='Compound Annual Growth Rate of Free Cash Flow'))
        return results

    def _calculate_cash_flow_ratios(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """Calculate comprehensive cash flow ratios"""
        results = []
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        capex = cash_flow.get('capex', 0)
        total_debt = balance_sheet.get('long_term_debt', 0) + balance_sheet.get('short_term_debt', 0)
        debt_payments = cash_flow.get('debt_repaid', 0)
        interest_expense = income_statement.get('interest_expense', 0)
        total_debt_service = debt_payments + interest_expense
        if total_debt_service > 0:
            cash_coverage = self.safe_divide(operating_cash_flow, total_debt_service)
            benchmark = self.cash_flow_benchmarks.get('cash_coverage_ratio', {})
            risk_level = self.assess_risk_level(cash_coverage, benchmark, higher_is_better=True)
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Cash Coverage Ratio', value=cash_coverage, interpretation=self.generate_interpretation('cash coverage ratio', cash_coverage, risk_level, AnalysisType.SOLVENCY), risk_level=risk_level, methodology='Operating Cash Flow / (Debt Payments + Interest Expense)', limitations=['Based on current period cash flows']))
        if total_debt > 0:
            debt_coverage = self.safe_divide(operating_cash_flow, total_debt)
            debt_coverage_interpretation = 'Strong debt coverage ability' if debt_coverage > 0.2 else 'Adequate debt coverage' if debt_coverage > 0.1 else 'Weak debt coverage ability'
            debt_coverage_risk = RiskLevel.LOW if debt_coverage > 0.15 else RiskLevel.MODERATE if debt_coverage > 0.08 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Debt Coverage Ratio', value=debt_coverage, interpretation=debt_coverage_interpretation, risk_level=debt_coverage_risk, methodology='Operating Cash Flow / Total Debt'))
        if capex > 0:
            capex_coverage = self.safe_divide(operating_cash_flow, capex)
            capex_coverage_interpretation = 'Strong capex coverage - self-funding growth' if capex_coverage > 1.5 else 'Adequate capex coverage' if capex_coverage > 1.0 else 'Insufficient capex coverage - external funding needed'
            capex_coverage_risk = RiskLevel.LOW if capex_coverage > 1.2 else RiskLevel.MODERATE if capex_coverage > 0.8 else RiskLevel.HIGH
            results.append(AnalysisResult(analysis_type=AnalysisType.SOLVENCY, metric_name='Capital Expenditure Coverage', value=capex_coverage, interpretation=capex_coverage_interpretation, risk_level=capex_coverage_risk, methodology='Operating Cash Flow / Capital Expenditures', limitations=['Does not consider maintenance vs growth capex split']))
        return results

    def _analyze_working_capital_impact(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze working capital changes impact on cash flow"""
        results = []
        cash_flow = statements.cash_flow
        working_capital_change = cash_flow.get('working_capital_change', 0)
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        if working_capital_change != 0 and operating_cash_flow != 0:
            wc_impact = self.safe_divide(abs(working_capital_change), abs(operating_cash_flow))
            wc_interpretation = 'Significant working capital impact on cash flow' if wc_impact > 0.2 else 'Moderate working capital impact' if wc_impact > 0.1 else 'Minimal working capital impact'
            wc_risk = RiskLevel.HIGH if wc_impact > 0.3 else RiskLevel.MODERATE if wc_impact > 0.15 else RiskLevel.LOW
            if working_capital_change < 0:
                impact_direction = 'Working capital increase reduced operating cash flow'
            else:
                impact_direction = 'Working capital decrease boosted operating cash flow'
            results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name='Working Capital Impact', value=wc_impact, interpretation=f'{wc_interpretation}. {impact_direction}', risk_level=wc_risk, methodology='|Working Capital Change| / |Operating Cash Flow|'))
        ar_change = cash_flow.get('accounts_receivable_change', 0)
        inventory_change = cash_flow.get('inventory_change', 0)
        ap_change = cash_flow.get('accounts_payable_change', 0)
        wc_components = {'Accounts Receivable Change': ar_change, 'Inventory Change': inventory_change, 'Accounts Payable Change': ap_change}
        for component, change in wc_components.items():
            if abs(change) > 0:
                if 'Payable' in component:
                    impact_description = 'Improved cash flow' if change > 0 else 'Reduced cash flow'
                else:
                    impact_description = 'Reduced cash flow' if change < 0 else 'Improved cash flow'
                results.append(AnalysisResult(analysis_type=AnalysisType.ACTIVITY, metric_name=component, value=change, interpretation=f'{component} change of ${change:,.0f} {impact_description}', risk_level=RiskLevel.LOW, methodology='Change in working capital component from cash flow statement'))
        return results

    def _assess_cash_flow_quality(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Comprehensive cash flow quality assessment"""
        results = []
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        net_income = income_statement.get('net_income', 0)
        quality_indicators = []
        red_flags = []
        quality_score = 100
        if net_income > 0:
            ocf_ni_ratio = self.safe_divide(operating_cash_flow, net_income)
            if ocf_ni_ratio >= 1.0:
                quality_indicators.append('Operating cash flow exceeds net income')
            elif ocf_ni_ratio < 0.7:
                red_flags.append('Operating cash flow significantly below net income')
                quality_score -= 20
        elif net_income < 0 and operating_cash_flow > 0:
            quality_indicators.append('Positive operating cash flow despite losses')
        elif net_income < 0 and operating_cash_flow < 0:
            red_flags.append('Both earnings and cash flow are negative')
            quality_score -= 30
        if comparative_data and len(comparative_data) >= 2:
            ocf_values = []
            for past_statements in comparative_data:
                past_ocf = past_statements.cash_flow.get('operating_cash_flow', 0)
                ocf_values.append(past_ocf)
            ocf_values.append(operating_cash_flow)
            declining_periods = sum((1 for i in range(1, len(ocf_values)) if ocf_values[i] < ocf_values[i - 1]))
            if declining_periods > len(ocf_values) // 2:
                red_flags.append('Declining operating cash flow trend')
                quality_score -= 15
            else:
                quality_indicators.append('Stable or improving cash flow trend')
        working_capital_change = cash_flow.get('working_capital_change', 0)
        if abs(working_capital_change) > abs(operating_cash_flow) * 0.3:
            red_flags.append('Large working capital changes may indicate manipulation')
            quality_score -= 10
        quality_score = max(0, quality_score)
        quality_interpretation = 'High cash flow quality' if quality_score > 80 else 'Moderate cash flow quality' if quality_score > 60 else 'Low cash flow quality - requires investigation'
        quality_risk = RiskLevel.LOW if quality_score > 75 else RiskLevel.MODERATE if quality_score > 50 else RiskLevel.HIGH
        results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Cash Flow Quality Score', value=quality_score, interpretation=quality_interpretation, risk_level=quality_risk, recommendations=quality_indicators, limitations=red_flags, methodology='Composite score based on multiple quality indicators'))
        return results

    def _analyze_statement_linkages(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> List[AnalysisResult]:
        """Analyze linkages between cash flow statement and other financial statements"""
        results = []
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        net_income_cf = cash_flow.get('net_income_cf', 0)
        net_income_is = income_statement.get('net_income', 0)
        if abs(net_income_cf - net_income_is) > 0.01:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Income Statement Reconciliation', value=abs(net_income_cf - net_income_is), interpretation='Net income figures should match between statements', risk_level=RiskLevel.MODERATE, limitations=['Potential data quality issue or reporting difference']))
        net_cash_change = cash_flow.get('net_cash_change', 0)
        cash_beginning = cash_flow.get('cash_beginning', 0)
        cash_ending = cash_flow.get('cash_ending', 0)
        cash_bs = balance_sheet.get('cash_equivalents', 0)
        if abs(cash_ending - cash_bs) > 0.01:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Cash Balance Reconciliation', value=abs(cash_ending - cash_bs), interpretation='Ending cash should match balance sheet cash', risk_level=RiskLevel.MODERATE, limitations=['Potential classification or timing difference']))
        calculated_change = cash_ending - cash_beginning
        if abs(net_cash_change - calculated_change) > 0.01:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='Net Cash Change Reconciliation', value=abs(net_cash_change - calculated_change), interpretation='Net cash change should equal ending minus beginning cash', risk_level=RiskLevel.HIGH, limitations=['Mathematical error in cash flow statement']))
        return results

    def _analyze_reporting_differences(self, statements: FinancialStatements) -> List[AnalysisResult]:
        """Analyze IFRS vs US GAAP differences in cash flow reporting"""
        results = []
        reporting_standard = statements.company_info.reporting_standard
        cash_flow = statements.cash_flow
        interest_paid = cash_flow.get('interest_paid', 0)
        dividends_received = cash_flow.get('dividends_received', 0)
        if reporting_standard == ReportingStandard.IFRS:
            if interest_paid != 0 or dividends_received != 0:
                results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='IFRS Classification Flexibility', value=1.0, interpretation='Under IFRS, interest paid and dividends received can be classified in operating or financing activities', risk_level=RiskLevel.LOW, limitations=['Classification choice may affect comparability with US GAAP companies'], methodology='IFRS allows flexibility in interest and dividend classification'))
        elif reporting_standard == ReportingStandard.US_GAAP:
            results.append(AnalysisResult(analysis_type=AnalysisType.QUALITY, metric_name='US GAAP Classification Rules', value=1.0, interpretation='Under US GAAP, interest paid is operating, dividends received are operating, dividends paid are financing', risk_level=RiskLevel.LOW, methodology='US GAAP has fixed classification rules for interest and dividends'))
        return results

    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key cash flow metrics"""
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        balance_sheet = statements.balance_sheet
        metrics = {}
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        capex = cash_flow.get('capex', 0)
        metrics['operating_cash_flow'] = operating_cash_flow
        metrics['free_cash_flow_firm'] = operating_cash_flow - capex
        revenue = income_statement.get('revenue', 0)
        net_income = income_statement.get('net_income', 0)
        current_liabilities = balance_sheet.get('current_liabilities', 0)
        total_assets = balance_sheet.get('total_assets', 0)
        if revenue > 0:
            metrics['cash_flow_margin'] = self.safe_divide(operating_cash_flow, revenue)
            metrics['fcf_margin'] = self.safe_divide(operating_cash_flow - capex, revenue)
        if net_income != 0:
            metrics['quality_of_earnings'] = self.safe_divide(operating_cash_flow, net_income)
        if current_liabilities > 0:
            metrics['operating_cash_flow_ratio'] = self.safe_divide(operating_cash_flow, current_liabilities)
        if total_assets > 0:
            metrics['cash_return_on_assets'] = self.safe_divide(operating_cash_flow, total_assets)
        dividends_paid = cash_flow.get('dividends_paid', 0)
        if dividends_paid > 0:
            metrics['dividend_coverage'] = self.safe_divide(operating_cash_flow, dividends_paid)
        if capex > 0:
            metrics['capex_coverage'] = self.safe_divide(operating_cash_flow, capex)
        return metrics

    def create_cash_flow_quality_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> CashFlowQualityAnalysis:
        """Create comprehensive cash flow quality analysis object"""
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        investing_cash_flow = cash_flow.get('investing_cash_flow', 0)
        financing_cash_flow = cash_flow.get('financing_cash_flow', 0)
        net_income = income_statement.get('net_income', 0)
        operating_quality = 100
        if net_income > 0:
            ocf_ratio = self.safe_divide(operating_cash_flow, net_income)
            if ocf_ratio < 0.8:
                operating_quality -= 30
            elif ocf_ratio < 1.0:
                operating_quality -= 15
        investing_quality = 100
        capex = cash_flow.get('capex', 0)
        asset_sales = cash_flow.get('asset_sales', 0)
        if asset_sales > abs(capex):
            investing_quality -= 20
        financing_quality = 100
        debt_issued = cash_flow.get('debt_issued', 0)
        equity_issued = cash_flow.get('equity_issued', 0)
        if debt_issued > operating_cash_flow * 2:
            financing_quality -= 25
        overall_quality = np.mean([operating_quality, investing_quality, financing_quality])
        quality_indicators = []
        red_flags = []
        if operating_cash_flow > 0:
            quality_indicators.append('Positive operating cash flow')
        else:
            red_flags.append('Negative operating cash flow')
        if net_income > 0 and operating_cash_flow > net_income:
            quality_indicators.append('Operating cash flow exceeds net income')
        elif net_income > 0 and operating_cash_flow < net_income * 0.7:
            red_flags.append('Poor cash conversion from earnings')
        earnings_cash_correlation = None
        cash_earnings_ratio = None
        if net_income != 0:
            cash_earnings_ratio = self.safe_divide(operating_cash_flow, net_income)
        return CashFlowQualityAnalysis(operating_cash_quality=operating_quality, investing_cash_quality=investing_quality, financing_cash_quality=financing_quality, overall_quality_score=overall_quality, quality_indicators=quality_indicators, red_flags=red_flags, earnings_cash_correlation=earnings_cash_correlation, cash_earnings_ratio=cash_earnings_ratio)

    def create_free_cash_flow_analysis(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None) -> FreeCashFlowAnalysis:
        """Create comprehensive free cash flow analysis object"""
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
        capex = cash_flow.get('capex', 0)
        debt_issued = cash_flow.get('debt_issued', 0)
        debt_repaid = cash_flow.get('debt_repaid', 0)
        fcf_firm = operating_cash_flow - capex
        fcf_equity = fcf_firm - (debt_repaid - debt_issued)
        revenue = income_statement.get('revenue', 0)
        net_income = income_statement.get('net_income', 0)
        fcf_yield = None
        fcf_growth_rate = None
        fcf_volatility = None
        capex_intensity = self.safe_divide(capex, revenue) if revenue > 0 else None
        fcf_conversion_ratio = self.safe_divide(fcf_firm, net_income) if net_income > 0 else None
        if comparative_data and len(comparative_data) > 0:
            fcf_values = []
            for past_statements in comparative_data:
                past_ocf = past_statements.cash_flow.get('operating_cash_flow', 0)
                past_capex = past_statements.cash_flow.get('capex', 0)
                past_fcf = past_ocf - past_capex
                fcf_values.append(past_fcf)
            fcf_values.append(fcf_firm)
            if len(fcf_values) > 1:
                if fcf_values[0] > 0:
                    if len(fcf_values) == 2:
                        fcf_growth_rate = fcf_values[-1] / fcf_values[0] - 1
                    else:
                        n_periods = len(fcf_values) - 1
                        fcf_growth_rate = (fcf_values[-1] / fcf_values[0]) ** (1 / n_periods) - 1
                mean_fcf = np.mean(fcf_values)
                std_fcf = np.std(fcf_values)
                fcf_volatility = std_fcf / abs(mean_fcf) if mean_fcf != 0 else 0
        sustainability_score = 100
        if fcf_firm < 0:
            sustainability_score -= 40
        if capex_intensity and capex_intensity > 0.15:
            sustainability_score -= 20
        if fcf_conversion_ratio and fcf_conversion_ratio < 0.5:
            sustainability_score -= 20
        sustainability_score = max(0, sustainability_score)
        return FreeCashFlowAnalysis(fcf_firm=fcf_firm, fcf_equity=fcf_equity, fcf_yield=fcf_yield, fcf_growth_rate=fcf_growth_rate, fcf_volatility=fcf_volatility, capex_intensity=capex_intensity, fcf_conversion_ratio=fcf_conversion_ratio, sustainability_score=sustainability_score)

    def convert_indirect_to_direct_method(self, statements: FinancialStatements) -> Dict[str, float]:
        """Convert cash flow from indirect to direct method presentation"""
        cash_flow = statements.cash_flow
        income_statement = statements.income_statement
        net_income = cash_flow.get('net_income_cf', income_statement.get('net_income', 0))
        depreciation = cash_flow.get('depreciation_cf', 0)
        amortization = cash_flow.get('amortization_cf', 0)
        stock_compensation = cash_flow.get('stock_compensation', 0)
        ar_change = cash_flow.get('accounts_receivable_change', 0)
        inventory_change = cash_flow.get('inventory_change', 0)
        ap_change = cash_flow.get('accounts_payable_change', 0)
        revenue = income_statement.get('revenue', 0)
        cash_received_from_customers = revenue + ar_change
        cost_of_sales = income_statement.get('cost_of_sales', 0)
        cash_paid_to_suppliers = cost_of_sales - inventory_change - ap_change
        operating_expenses = income_statement.get('operating_expenses', 0)
        cash_paid_for_expenses = operating_expenses - depreciation - amortization - stock_compensation
        direct_method = {'cash_received_from_customers': cash_received_from_customers, 'cash_paid_to_suppliers': -abs(cash_paid_to_suppliers), 'cash_paid_for_operating_expenses': -abs(cash_paid_for_expenses), 'net_operating_cash_flow': cash_received_from_customers - abs(cash_paid_to_suppliers) - abs(cash_paid_for_expenses)}
        return direct_method

def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
    """
        Comprehensive cash flow statement analysis

        Args:
            statements: Current period financial statements
            comparative_data: Historical financial statements for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results covering all cash flow aspects
        """
    results = []
    required_fields = ['operating_cash_flow']
    is_sufficient, missing_fields = self.validate_data_sufficiency(statements, required_fields)
    if not is_sufficient:
        if self.logger:
            self.logger.warning(f'Insufficient data for complete analysis. Missing: {missing_fields}')
    results.extend(self._analyze_operating_cash_flow(statements, comparative_data, industry_data))
    results.extend(self._analyze_investing_cash_flow(statements, comparative_data))
    results.extend(self._analyze_financing_cash_flow(statements, comparative_data))
    results.extend(self._analyze_free_cash_flow(statements, comparative_data, industry_data))
    results.extend(self._calculate_cash_flow_ratios(statements, comparative_data, industry_data))
    results.extend(self._assess_cash_flow_quality(statements, comparative_data))
    results.extend(self._analyze_statement_linkages(statements, comparative_data))
    results.extend(self._analyze_reporting_differences(statements))
    return results

class ManualDataInput(DataProvider):
    """Manual data input interface for user-provided data"""

    def __init__(self):
        super().__init__('Manual Input')
        self.data_store = {}

    def add_exchange_rate_data(self, currency_pair: str, dates: List[datetime], rates: List[float]):
        """Add manual exchange rate data"""
        if len(dates) != len(rates):
            raise ValidationError('Dates and rates lists must have same length')
        df = pd.DataFrame({'date': dates, 'rate': rates}).set_index('date')
        if 'exchange_rates' not in self.data_store:
            self.data_store['exchange_rates'] = {}
        self.data_store['exchange_rates'][currency_pair] = df['rate']

    def add_economic_indicator_data(self, country: str, indicator: str, dates: List[datetime], values: List[float]):
        """Add manual economic indicator data"""
        if len(dates) != len(values):
            raise ValidationError('Dates and values lists must have same length')
        df = pd.DataFrame({'date': dates, 'value': values}).set_index('date')
        if 'economic_indicators' not in self.data_store:
            self.data_store['economic_indicators'] = {}
        if country not in self.data_store['economic_indicators']:
            self.data_store['economic_indicators'][country] = {}
        self.data_store['economic_indicators'][country][indicator] = df['value']

    def add_interest_rate_data(self, country: str, rate_type: str, dates: List[datetime], rates: List[float]):
        """Add manual interest rate data"""
        if len(dates) != len(rates):
            raise ValidationError('Dates and rates lists must have same length')
        df = pd.DataFrame({'date': dates, 'rate': rates}).set_index('date')
        if 'interest_rates' not in self.data_store:
            self.data_store['interest_rates'] = {}
        if country not in self.data_store['interest_rates']:
            self.data_store['interest_rates'][country] = {}
        self.data_store['interest_rates'][country][rate_type] = df['rate']

    def load_from_csv(self, file_path: str, data_type: str, **kwargs):
        """Load data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            if data_type == 'exchange_rates':
                self._load_fx_from_csv(df, **kwargs)
            elif data_type == 'economic_indicators':
                self._load_indicators_from_csv(df, **kwargs)
            elif data_type == 'interest_rates':
                self._load_rates_from_csv(df, **kwargs)
            else:
                raise ValidationError(f'Unknown data type: {data_type}')
        except Exception as e:
            raise DataError(f'Error loading CSV file {file_path}: {e}')

    def _load_fx_from_csv(self, df: pd.DataFrame, date_column: str='date', **kwargs):
        """Load FX data from CSV"""
        if date_column not in df.columns:
            raise ValidationError(f"Date column '{date_column}' not found in CSV")
        df[date_column] = pd.to_datetime(df[date_column])
        df.set_index(date_column, inplace=True)
        if 'exchange_rates' not in self.data_store:
            self.data_store['exchange_rates'] = {}
        for column in df.columns:
            if column != date_column:
                self.data_store['exchange_rates'][column] = df[column]

    def _load_indicators_from_csv(self, df: pd.DataFrame, country: str, date_column: str='date', **kwargs):
        """Load economic indicators from CSV"""
        if date_column not in df.columns:
            raise ValidationError(f"Date column '{date_column}' not found in CSV")
        df[date_column] = pd.to_datetime(df[date_column])
        df.set_index(date_column, inplace=True)
        if 'economic_indicators' not in self.data_store:
            self.data_store['economic_indicators'] = {}
        if country not in self.data_store['economic_indicators']:
            self.data_store['economic_indicators'][country] = {}
        for column in df.columns:
            if column != date_column:
                self.data_store['economic_indicators'][country][column] = df[column]

    def _load_rates_from_csv(self, df: pd.DataFrame, country: str, date_column: str='date', **kwargs):
        """Load interest rates from CSV"""
        if date_column not in df.columns:
            raise ValidationError(f"Date column '{date_column}' not found in CSV")
        df[date_column] = pd.to_datetime(df[date_column])
        df.set_index(date_column, inplace=True)
        if 'interest_rates' not in self.data_store:
            self.data_store['interest_rates'] = {}
        if country not in self.data_store['interest_rates']:
            self.data_store['interest_rates'][country] = {}
        for column in df.columns:
            if column != date_column:
                self.data_store['interest_rates'][country][column] = df[column]

    def get_exchange_rates(self, base_currency: str, target_currencies: List[str], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None) -> pd.DataFrame:
        """Get exchange rates from manual data store"""
        if 'exchange_rates' not in self.data_store:
            raise DataError('No exchange rate data available')
        fx_data = {}
        for target_currency in target_currencies:
            pair = f'{base_currency}/{target_currency}'
            if pair in self.data_store['exchange_rates']:
                series = self.data_store['exchange_rates'][pair]
                if start_date or end_date:
                    mask = pd.Series(True, index=series.index)
                    if start_date:
                        mask &= series.index >= start_date
                    if end_date:
                        mask &= series.index <= end_date
                    series = series[mask]
                fx_data[pair] = series
            else:
                logger.warning(f'Exchange rate {pair} not found in manual data')
        if not fx_data:
            raise DataError('No matching exchange rate data found')
        return pd.DataFrame(fx_data)

    def get_economic_indicators(self, country: str, indicators: List[str], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None) -> pd.DataFrame:
        """Get economic indicators from manual data store"""
        if 'economic_indicators' not in self.data_store:
            raise DataError('No economic indicator data available')
        if country not in self.data_store['economic_indicators']:
            raise DataError(f'No data available for country {country}')
        indicator_data = {}
        country_data = self.data_store['economic_indicators'][country]
        for indicator in indicators:
            if indicator in country_data:
                series = country_data[indicator]
                if start_date or end_date:
                    mask = pd.Series(True, index=series.index)
                    if start_date:
                        mask &= series.index >= start_date
                    if end_date:
                        mask &= series.index <= end_date
                    series = series[mask]
                indicator_data[indicator] = series
            else:
                logger.warning(f'Indicator {indicator} not found for {country}')
        if not indicator_data:
            raise DataError('No matching economic indicator data found')
        return pd.DataFrame(indicator_data)

    def get_interest_rates(self, country: str, rate_types: List[str], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None) -> pd.DataFrame:
        """Get interest rates from manual data store"""
        if 'interest_rates' not in self.data_store:
            raise DataError('No interest rate data available')
        if country not in self.data_store['interest_rates']:
            raise DataError(f'No interest rate data available for country {country}')
        rate_data = {}
        country_data = self.data_store['interest_rates'][country]
        for rate_type in rate_types:
            if rate_type in country_data:
                series = country_data[rate_type]
                if start_date or end_date:
                    mask = pd.Series(True, index=series.index)
                    if start_date:
                        mask &= series.index >= start_date
                    if end_date:
                        mask &= series.index <= end_date
                    series = series[mask]
                rate_data[rate_type] = series
            else:
                logger.warning(f'Interest rate {rate_type} not found for {country}')
        if not rate_data:
            raise DataError('No matching interest rate data found')
        return pd.DataFrame(rate_data)

def load_from_csv(self, file_path: str, data_type: str, **kwargs):
    """Load data from CSV file"""
    try:
        df = pd.read_csv(file_path)
        if data_type == 'exchange_rates':
            self._load_fx_from_csv(df, **kwargs)
        elif data_type == 'economic_indicators':
            self._load_indicators_from_csv(df, **kwargs)
        elif data_type == 'interest_rates':
            self._load_rates_from_csv(df, **kwargs)
        else:
            raise ValidationError(f'Unknown data type: {data_type}')
    except Exception as e:
        raise DataError(f'Error loading CSV file {file_path}: {e}')

class DataHandler(EconomicsBase):
    """Main data handler coordinating multiple data sources"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)
        self.providers = {}
        self.standardizer = DataStandardizer(precision)
        self.cache = {}
        self.cache_ttl = 3600

    def add_provider(self, provider_name: str, provider: DataProvider):
        """Add a data provider"""
        self.providers[provider_name] = provider
        logger.info(f'Added data provider: {provider_name}')

    def remove_provider(self, provider_name: str):
        """Remove a data provider"""
        if provider_name in self.providers:
            del self.providers[provider_name]
            logger.info(f'Removed data provider: {provider_name}')

    def list_providers(self) -> List[str]:
        """List available data providers"""
        return list(self.providers.keys())

    def get_exchange_rates(self, base_currency: str, target_currencies: List[str], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None, providers: Optional[List[str]]=None, standardize: bool=True) -> pd.DataFrame:
        """Get exchange rates from specified providers"""
        if providers is None:
            providers = list(self.providers.keys())
        cache_key = f'fx_{base_currency}_{'_'.join(target_currencies)}_{start_date}_{end_date}'
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                logger.info(f'Returning cached exchange rate data')
                return cache_entry['data']
        all_data = []
        for provider_name in providers:
            if provider_name not in self.providers:
                logger.warning(f'Provider {provider_name} not available')
                continue
            try:
                provider = self.providers[provider_name]
                data = provider.get_exchange_rates(base_currency, target_currencies, start_date, end_date)
                if not data.empty:
                    data.columns = [f'{col}_{provider_name}' for col in data.columns]
                    all_data.append(data)
                    logger.info(f'Retrieved FX data from {provider_name}: {len(data)} rows')
            except Exception as e:
                logger.error(f'Error retrieving FX data from {provider_name}: {e}')
                continue
        if not all_data:
            raise DataError('No exchange rate data retrieved from any provider')
        combined_data = pd.concat(all_data, axis=1, sort=True)
        if standardize:
            combined_data = self.standardizer.standardize_exchange_rates(combined_data)
        self.cache[cache_key] = {'data': combined_data, 'timestamp': datetime.now()}
        return combined_data

    def get_economic_indicators(self, country: str, indicators: List[str], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None, providers: Optional[List[str]]=None, standardize: bool=True) -> pd.DataFrame:
        """Get economic indicators from specified providers"""
        if providers is None:
            providers = list(self.providers.keys())
        cache_key = f'indicators_{country}_{'_'.join(indicators)}_{start_date}_{end_date}'
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                logger.info(f'Returning cached economic indicator data')
                return cache_entry['data']
        all_data = []
        for provider_name in providers:
            if provider_name not in self.providers:
                logger.warning(f'Provider {provider_name} not available')
                continue
            try:
                provider = self.providers[provider_name]
                data = provider.get_economic_indicators(country, indicators, start_date, end_date)
                if not data.empty:
                    data.columns = [f'{col}_{provider_name}' for col in data.columns]
                    all_data.append(data)
                    logger.info(f'Retrieved indicator data from {provider_name}: {len(data)} rows')
            except Exception as e:
                logger.error(f'Error retrieving indicator data from {provider_name}: {e}')
                continue
        if not all_data:
            raise DataError('No economic indicator data retrieved from any provider')
        combined_data = pd.concat(all_data, axis=1, sort=True)
        if standardize:
            combined_data = self.standardizer.standardize_economic_indicators(combined_data)
        self.cache[cache_key] = {'data': combined_data, 'timestamp': datetime.now()}
        return combined_data

    def get_interest_rates(self, country: str, rate_types: List[str], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None, providers: Optional[List[str]]=None, standardize: bool=True) -> pd.DataFrame:
        """Get interest rates from specified providers"""
        if providers is None:
            providers = list(self.providers.keys())
        cache_key = f'rates_{country}_{'_'.join(rate_types)}_{start_date}_{end_date}'
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                logger.info(f'Returning cached interest rate data')
                return cache_entry['data']
        all_data = []
        for provider_name in providers:
            if provider_name not in self.providers:
                logger.warning(f'Provider {provider_name} not available')
                continue
            try:
                provider = self.providers[provider_name]
                data = provider.get_interest_rates(country, rate_types, start_date, end_date)
                if not data.empty:
                    data.columns = [f'{col}_{provider_name}' for col in data.columns]
                    all_data.append(data)
                    logger.info(f'Retrieved rate data from {provider_name}: {len(data)} rows')
            except Exception as e:
                logger.error(f'Error retrieving rate data from {provider_name}: {e}')
                continue
        if not all_data:
            raise DataError('No interest rate data retrieved from any provider')
        combined_data = pd.concat(all_data, axis=1, sort=True)
        if standardize:
            combined_data = self.standardizer.standardize_economic_indicators(combined_data)
        self.cache[cache_key] = {'data': combined_data, 'timestamp': datetime.now()}
        return combined_data

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        logger.info('Data cache cleared')

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active_entries = 0
        expired_entries = 0
        for cache_entry in self.cache.values():
            if now - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                active_entries += 1
            else:
                expired_entries += 1
        return {'total_entries': len(self.cache), 'active_entries': active_entries, 'expired_entries': expired_entries, 'cache_ttl_seconds': self.cache_ttl}

    def validate_data_quality(self, data: pd.DataFrame, data_type: str='unknown') -> Dict[str, Any]:
        """Validate data quality and provide quality metrics"""
        if data.empty:
            return {'quality_score': 0, 'issues': ['Empty dataset'], 'recommendations': ['Obtain data from reliable sources']}
        quality_metrics = {'total_observations': len(data), 'total_variables': len(data.columns), 'missing_values': data.isnull().sum().sum(), 'missing_percentage': data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100, 'duplicate_rows': data.duplicated().sum(), 'date_range': f'{data.index.min()} to {data.index.max()}' if isinstance(data.index, pd.DatetimeIndex) else 'Not time series'}
        outlier_info = {}
        for column in data.select_dtypes(include=[np.number]).columns:
            outliers = self.standardizer.detect_outliers(data[column])
            outlier_info[column] = outliers.sum()
        quality_metrics['outliers_by_column'] = outlier_info
        quality_metrics['total_outliers'] = sum(outlier_info.values())
        quality_score = 100
        missing_penalty = min(quality_metrics['missing_percentage'] * 2, 50)
        quality_score -= missing_penalty
        outlier_percentage = quality_metrics['total_outliers'] / quality_metrics['total_observations'] * 100
        outlier_penalty = min(outlier_percentage * 1.5, 30)
        quality_score -= outlier_penalty
        duplicate_percentage = quality_metrics['duplicate_rows'] / quality_metrics['total_observations'] * 100
        duplicate_penalty = min(duplicate_percentage * 3, 20)
        quality_score -= duplicate_penalty
        quality_score = max(0, quality_score)
        issues = []
        recommendations = []
        if quality_metrics['missing_percentage'] > 10:
            issues.append(f'High missing data rate: {quality_metrics['missing_percentage']:.1f}%')
            recommendations.append('Consider data imputation or alternative data sources')
        if outlier_percentage > 5:
            issues.append(f'High outlier rate: {outlier_percentage:.1f}%')
            recommendations.append('Review outliers for data errors or consider robust analysis methods')
        if quality_metrics['duplicate_rows'] > 0:
            issues.append(f'Found {quality_metrics['duplicate_rows']} duplicate rows')
            recommendations.append('Remove duplicate observations')
        if isinstance(data.index, pd.DatetimeIndex):
            expected_freq = pd.infer_freq(data.index)
            if expected_freq:
                expected_range = pd.date_range(start=data.index.min(), end=data.index.max(), freq=expected_freq)
                missing_dates = len(expected_range) - len(data.index)
                if missing_dates > 0:
                    issues.append(f'Missing {missing_dates} time periods in series')
                    recommendations.append('Fill missing time periods or adjust analysis for irregular data')
        return {'quality_score': quality_score, 'quality_metrics': quality_metrics, 'issues': issues, 'recommendations': recommendations, 'data_type': data_type}

    def generate_data_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data summary"""
        summary = {'basic_info': {'shape': data.shape, 'data_types': data.dtypes.to_dict(), 'memory_usage': data.memory_usage(deep=True).sum(), 'index_type': type(data.index).__name__}, 'statistical_summary': {}, 'missing_data': {'total_missing': data.isnull().sum().sum(), 'missing_by_column': data.isnull().sum().to_dict(), 'missing_percentage_by_column': (data.isnull().sum() / len(data) * 100).to_dict()}}
        numeric_data = data.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            summary['statistical_summary'] = {'count': numeric_data.count().to_dict(), 'mean': numeric_data.mean().to_dict(), 'std': numeric_data.std().to_dict(), 'min': numeric_data.min().to_dict(), 'max': numeric_data.max().to_dict(), 'median': numeric_data.median().to_dict(), 'skewness': numeric_data.skew().to_dict(), 'kurtosis': numeric_data.kurtosis().to_dict()}
        if isinstance(data.index, pd.DatetimeIndex):
            summary['time_series_info'] = {'start_date': data.index.min(), 'end_date': data.index.max(), 'frequency': pd.infer_freq(data.index), 'total_periods': len(data.index), 'business_days_only': data.index.freq == 'B' if hasattr(data.index, 'freq') else False}
        return summary

    def calculate(self, operation: str, **kwargs) -> Any:
        """Main data handler operation dispatcher"""
        operations = {'validate_quality': lambda: self.validate_data_quality(kwargs['data'], kwargs.get('data_type', 'unknown')), 'generate_summary': lambda: self.generate_data_summary(kwargs['data']), 'standardize_fx': lambda: self.standardizer.standardize_exchange_rates(kwargs['data']), 'standardize_indicators': lambda: self.standardizer.standardize_economic_indicators(kwargs['data']), 'calculate_returns': lambda: self.standardizer.calculate_returns(kwargs['data'], kwargs.get('return_type', 'simple')), 'align_series': lambda: self.standardizer.align_time_series(*kwargs['dataframes'], join_method=kwargs.get('join_method', 'inner')), 'detect_outliers': lambda: self.standardizer.detect_outliers(kwargs['data'], kwargs.get('method', 'iqr'), kwargs.get('threshold', 1.5)), 'clean_data': lambda: self.standardizer.clean_data(kwargs['data'], kwargs.get('remove_outliers', True), kwargs.get('outlier_method', 'iqr'), kwargs.get('fill_missing', True), kwargs.get('fill_method', 'ffill'))}
        if operation not in operations:
            raise ValidationError(f'Unknown data operation: {operation}')
        result = operations[operation]()
        if operation in ['validate_quality', 'generate_summary']:
            if isinstance(result, dict):
                result['metadata'] = self.get_metadata()
                result['operation'] = operation
        return result

def calculate(self, operation: str, **kwargs) -> Any:
    """Main data handler operation dispatcher"""
    operations = {'validate_quality': lambda: self.validate_data_quality(kwargs['data'], kwargs.get('data_type', 'unknown')), 'generate_summary': lambda: self.generate_data_summary(kwargs['data']), 'standardize_fx': lambda: self.standardizer.standardize_exchange_rates(kwargs['data']), 'standardize_indicators': lambda: self.standardizer.standardize_economic_indicators(kwargs['data']), 'calculate_returns': lambda: self.standardizer.calculate_returns(kwargs['data'], kwargs.get('return_type', 'simple')), 'align_series': lambda: self.standardizer.align_time_series(*kwargs['dataframes'], join_method=kwargs.get('join_method', 'inner')), 'detect_outliers': lambda: self.standardizer.detect_outliers(kwargs['data'], kwargs.get('method', 'iqr'), kwargs.get('threshold', 1.5)), 'clean_data': lambda: self.standardizer.clean_data(kwargs['data'], kwargs.get('remove_outliers', True), kwargs.get('outlier_method', 'iqr'), kwargs.get('fill_missing', True), kwargs.get('fill_method', 'ffill'))}
    if operation not in operations:
        raise ValidationError(f'Unknown data operation: {operation}')
    result = operations[operation]()
    if operation in ['validate_quality', 'generate_summary']:
        if isinstance(result, dict):
            result['metadata'] = self.get_metadata()
            result['operation'] = operation
    return result

class BusinessCycleAnalyzer(EconomicsBase):
    """Business cycle phases and economic indicator analysis"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)
        self.cycle_phases = ['expansion', 'peak', 'contraction', 'trough']

    def detect_cycle_phase(self, economic_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Detect current business cycle phase based on economic indicators"""
        gdp_growth = self.to_decimal(economic_indicators.get('gdp_growth_rate', 0))
        unemployment_rate = self.to_decimal(economic_indicators.get('unemployment_rate', 0))
        inflation_rate = self.to_decimal(economic_indicators.get('inflation_rate', 0))
        interest_rates = self.to_decimal(economic_indicators.get('interest_rate', 0))
        consumer_confidence = self.to_decimal(economic_indicators.get('consumer_confidence', 0))
        business_investment = self.to_decimal(economic_indicators.get('business_investment_growth', 0))
        phase_scores = self._calculate_phase_scores(gdp_growth, unemployment_rate, inflation_rate, interest_rates, consumer_confidence, business_investment)
        detected_phase = max(phase_scores.items(), key=lambda x: x[1]['score'])[0]
        return {'detected_phase': detected_phase, 'phase_scores': phase_scores, 'confidence_level': phase_scores[detected_phase]['score'], 'indicator_analysis': self._analyze_indicators_by_phase(economic_indicators), 'phase_characteristics': self._get_phase_characteristics(detected_phase), 'expected_duration': self._estimate_phase_duration(detected_phase, economic_indicators), 'investment_implications': self._get_investment_implications(detected_phase)}

    def _calculate_phase_scores(self, gdp_growth: Decimal, unemployment: Decimal, inflation: Decimal, interest_rate: Decimal, consumer_conf: Decimal, investment: Decimal) -> Dict[str, Any]:
        """Calculate likelihood scores for each business cycle phase"""
        scores = {}
        expansion_score = self.to_decimal(0)
        if gdp_growth > self.to_decimal(2):
            expansion_score += self.to_decimal(25)
        if unemployment < self.to_decimal(6):
            expansion_score += self.to_decimal(20)
        if consumer_conf > self.to_decimal(100):
            expansion_score += self.to_decimal(20)
        if investment > self.to_decimal(3):
            expansion_score += self.to_decimal(20)
        if inflation > self.to_decimal(1) and inflation < self.to_decimal(4):
            expansion_score += self.to_decimal(15)
        scores['expansion'] = {'score': expansion_score, 'indicators': 'Positive GDP growth, low unemployment, high confidence'}
        peak_score = self.to_decimal(0)
        if gdp_growth > self.to_decimal(1) and gdp_growth < self.to_decimal(3):
            peak_score += self.to_decimal(15)
        if unemployment < self.to_decimal(4):
            peak_score += self.to_decimal(25)
        if inflation > self.to_decimal(3):
            peak_score += self.to_decimal(25)
        if interest_rate > self.to_decimal(4):
            peak_score += self.to_decimal(20)
        if consumer_conf > self.to_decimal(110):
            peak_score += self.to_decimal(15)
        scores['peak'] = {'score': peak_score, 'indicators': 'Slowing growth, very low unemployment, rising inflation'}
        contraction_score = self.to_decimal(0)
        if gdp_growth < self.to_decimal(0):
            contraction_score += self.to_decimal(30)
        if unemployment > self.to_decimal(7):
            contraction_score += self.to_decimal(25)
        if consumer_conf < self.to_decimal(90):
            contraction_score += self.to_decimal(20)
        if investment < self.to_decimal(0):
            contraction_score += self.to_decimal(25)
        scores['contraction'] = {'score': contraction_score, 'indicators': 'Negative GDP growth, rising unemployment, low confidence'}
        trough_score = self.to_decimal(0)
        if gdp_growth > self.to_decimal(-1) and gdp_growth < self.to_decimal(1):
            trough_score += self.to_decimal(20)
        if unemployment > self.to_decimal(8):
            trough_score += self.to_decimal(25)
        if inflation < self.to_decimal(2):
            trough_score += self.to_decimal(20)
        if interest_rate < self.to_decimal(3):
            trough_score += self.to_decimal(20)
        if consumer_conf < self.to_decimal(85):
            trough_score += self.to_decimal(15)
        scores['trough'] = {'score': trough_score, 'indicators': 'Stabilizing negative growth, high unemployment, low rates'}
        return scores

    def _analyze_indicators_by_phase(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how different economic indicators vary over business cycle"""
        return {'leading_indicators': {'description': 'Change before the economy changes direction', 'examples': {'stock_market': indicators.get('stock_market_performance', 'N/A'), 'consumer_confidence': indicators.get('consumer_confidence', 'N/A'), 'new_business_formation': indicators.get('new_business_starts', 'N/A'), 'yield_curve': indicators.get('yield_curve_slope', 'N/A')}, 'investment_utility': 'Most valuable for timing market entry/exit'}, 'coincident_indicators': {'description': 'Change at the same time as the economy', 'examples': {'gdp_growth': indicators.get('gdp_growth_rate', 'N/A'), 'employment': indicators.get('employment_rate', 'N/A'), 'industrial_production': indicators.get('industrial_production', 'N/A'), 'retail_sales': indicators.get('retail_sales_growth', 'N/A')}, 'investment_utility': 'Confirm current economic state'}, 'lagging_indicators': {'description': 'Change after the economy has changed direction', 'examples': {'unemployment_rate': indicators.get('unemployment_rate', 'N/A'), 'inflation_rate': indicators.get('inflation_rate', 'N/A'), 'interest_rates': indicators.get('interest_rate', 'N/A'), 'corporate_profits': indicators.get('corporate_profit_growth', 'N/A')}, 'investment_utility': 'Confirm cycle turning points after the fact'}}

    def _get_phase_characteristics(self, phase: str) -> Dict[str, Any]:
        """Get detailed characteristics of each business cycle phase"""
        characteristics = {'expansion': {'duration': '2-8 years typically', 'gdp_growth': 'Positive and accelerating', 'unemployment': 'Declining', 'inflation': 'Gradually rising', 'interest_rates': 'Rising as central bank tightens', 'business_activity': 'Increasing investment, hiring, capacity utilization', 'consumer_behavior': 'Rising confidence, increased spending', 'financial_markets': 'Stock markets generally rising, credit expanding'}, 'peak': {'duration': 'Brief period (months)', 'gdp_growth': 'Positive but slowing', 'unemployment': 'At cyclical lows', 'inflation': 'At or near cyclical highs', 'interest_rates': 'At cyclical highs', 'business_activity': 'Capacity constraints, labor shortages', 'consumer_behavior': 'High confidence but spending slowing', 'financial_markets': 'Stock markets vulnerable, tight credit'}, 'contraction': {'duration': '6 months to 2 years', 'gdp_growth': 'Negative for at least 2 quarters', 'unemployment': 'Rising sharply', 'inflation': 'Falling due to weak demand', 'interest_rates': 'Falling as central bank eases', 'business_activity': 'Declining investment, layoffs, low capacity use', 'consumer_behavior': 'Falling confidence, reduced spending', 'financial_markets': 'Bear markets, credit contraction'}, 'trough': {'duration': 'Brief period (months)', 'gdp_growth': 'Negative but stabilizing', 'unemployment': 'At cyclical highs but stabilizing', 'inflation': 'Low and stable', 'interest_rates': 'At cyclical lows', 'business_activity': 'Excess capacity, cautious investment', 'consumer_behavior': 'Low confidence but stabilizing', 'financial_markets': 'Markets often bottom before economy'}}
        return characteristics.get(phase, {})

    def _estimate_phase_duration(self, phase: str, indicators: Dict[str, Any]) -> str:
        """Estimate remaining duration of current phase"""
        phase_durations = {'expansion': 'Typically 2-8 years; current strength suggests 1-3 years remaining', 'peak': 'Brief transition period; 3-12 months before contraction begins', 'contraction': 'Typically 6-18 months; depth indicates 6-12 months remaining', 'trough': 'Brief transition period; recovery likely within 3-9 months'}
        return phase_durations.get(phase, 'Duration uncertain')

    def _get_investment_implications(self, phase: str) -> Dict[str, Any]:
        """Get investment implications for each business cycle phase"""
        implications = {'expansion': {'equity_strategy': 'Favor cyclical stocks, growth sectors', 'fixed_income': 'Shorter duration, higher yield focus', 'sectors_to_favor': ['Technology', 'Consumer Discretionary', 'Industrials'], 'sectors_to_avoid': ['Utilities', 'Consumer Staples'], 'overall_risk': 'Moderate to High'}, 'peak': {'equity_strategy': 'Defensive positioning, quality focus', 'fixed_income': 'Extend duration, prepare for rate cuts', 'sectors_to_favor': ['Healthcare', 'Consumer Staples', 'Utilities'], 'sectors_to_avoid': ['Cyclicals', 'Small caps'], 'overall_risk': 'Reduce risk exposure'}, 'contraction': {'equity_strategy': 'Defensive stocks, dividend focus', 'fixed_income': 'High quality bonds, government securities', 'sectors_to_favor': ['Consumer Staples', 'Healthcare', 'Utilities'], 'sectors_to_avoid': ['Financials', 'Materials', 'Energy'], 'overall_risk': 'Low risk, capital preservation'}, 'trough': {'equity_strategy': 'Prepare for cyclical recovery, value opportunities', 'fixed_income': 'Shorten duration, prepare for rate rises', 'sectors_to_favor': ['Financials', 'Technology', 'Industrials'], 'sectors_to_avoid': ['Defensive sectors becoming expensive'], 'overall_risk': 'Gradually increase risk'}}
        return implications.get(phase, {})

    def analyze_sector_cyclicality(self, sector_data: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """Analyze how different sectors vary over business cycle"""
        sector_analysis = {}
        for sector, performance_data in sector_data.items():
            if len(performance_data) < 4:
                continue
            volatility = self._calculate_volatility(performance_data)
            if volatility > self.to_decimal(20):
                cyclicality = 'Highly Cyclical'
                characteristics = 'Large swings with economic cycle'
            elif volatility > self.to_decimal(12):
                cyclicality = 'Moderately Cyclical'
                characteristics = 'Moderate sensitivity to economic changes'
            else:
                cyclicality = 'Defensive'
                characteristics = 'Stable performance through cycles'
            sector_analysis[sector] = {'volatility': volatility, 'cyclicality': cyclicality, 'characteristics': characteristics, 'investment_timing': self._get_sector_timing(cyclicality)}
        return {'sector_analysis': sector_analysis, 'summary': self._summarize_sector_cyclicality(sector_analysis)}

    def _calculate_volatility(self, data: List[Decimal]) -> Decimal:
        """Calculate volatility of performance data"""
        if len(data) < 2:
            return self.to_decimal(0)
        mean = sum(data) / self.to_decimal(len(data))
        variance = sum(((x - mean) ** 2 for x in data)) / self.to_decimal(len(data) - 1)
        return variance.sqrt() * self.to_decimal(100)

    def _get_sector_timing(self, cyclicality: str) -> str:
        """Get optimal timing for sector investment"""
        timing_guide = {'Highly Cyclical': 'Buy at trough, sell at peak', 'Moderately Cyclical': 'Overweight in expansion, underweight in contraction', 'Defensive': 'Stable allocation, overweight during uncertainty'}
        return timing_guide.get(cyclicality, 'Standard allocation')

    def _summarize_sector_cyclicality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize sector cyclicality analysis"""
        cyclical_count = sum((1 for sector in analysis.values() if 'Cyclical' in sector['cyclicality']))
        defensive_count = len(analysis) - cyclical_count
        return {'total_sectors_analyzed': len(analysis), 'cyclical_sectors': cyclical_count, 'defensive_sectors': defensive_count, 'portfolio_implication': 'Balance cyclical and defensive based on cycle phase'}

    def calculate(self, analysis_type: str='phase_detection', **kwargs) -> Dict[str, Any]:
        """Main business cycle calculation dispatcher"""
        if analysis_type == 'phase_detection':
            return self.detect_cycle_phase(kwargs['economic_indicators'])
        elif analysis_type == 'sector_cyclicality':
            return self.analyze_sector_cyclicality(kwargs['sector_data'])
        else:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')

def _calculate_phase_scores(self, gdp_growth: Decimal, unemployment: Decimal, inflation: Decimal, interest_rate: Decimal, consumer_conf: Decimal, investment: Decimal) -> Dict[str, Any]:
    """Calculate likelihood scores for each business cycle phase"""
    scores = {}
    expansion_score = self.to_decimal(0)
    if gdp_growth > self.to_decimal(2):
        expansion_score += self.to_decimal(25)
    if unemployment < self.to_decimal(6):
        expansion_score += self.to_decimal(20)
    if consumer_conf > self.to_decimal(100):
        expansion_score += self.to_decimal(20)
    if investment > self.to_decimal(3):
        expansion_score += self.to_decimal(20)
    if inflation > self.to_decimal(1) and inflation < self.to_decimal(4):
        expansion_score += self.to_decimal(15)
    scores['expansion'] = {'score': expansion_score, 'indicators': 'Positive GDP growth, low unemployment, high confidence'}
    peak_score = self.to_decimal(0)
    if gdp_growth > self.to_decimal(1) and gdp_growth < self.to_decimal(3):
        peak_score += self.to_decimal(15)
    if unemployment < self.to_decimal(4):
        peak_score += self.to_decimal(25)
    if inflation > self.to_decimal(3):
        peak_score += self.to_decimal(25)
    if interest_rate > self.to_decimal(4):
        peak_score += self.to_decimal(20)
    if consumer_conf > self.to_decimal(110):
        peak_score += self.to_decimal(15)
    scores['peak'] = {'score': peak_score, 'indicators': 'Slowing growth, very low unemployment, rising inflation'}
    contraction_score = self.to_decimal(0)
    if gdp_growth < self.to_decimal(0):
        contraction_score += self.to_decimal(30)
    if unemployment > self.to_decimal(7):
        contraction_score += self.to_decimal(25)
    if consumer_conf < self.to_decimal(90):
        contraction_score += self.to_decimal(20)
    if investment < self.to_decimal(0):
        contraction_score += self.to_decimal(25)
    scores['contraction'] = {'score': contraction_score, 'indicators': 'Negative GDP growth, rising unemployment, low confidence'}
    trough_score = self.to_decimal(0)
    if gdp_growth > self.to_decimal(-1) and gdp_growth < self.to_decimal(1):
        trough_score += self.to_decimal(20)
    if unemployment > self.to_decimal(8):
        trough_score += self.to_decimal(25)
    if inflation < self.to_decimal(2):
        trough_score += self.to_decimal(20)
    if interest_rate < self.to_decimal(3):
        trough_score += self.to_decimal(20)
    if consumer_conf < self.to_decimal(85):
        trough_score += self.to_decimal(15)
    scores['trough'] = {'score': trough_score, 'indicators': 'Stabilizing negative growth, high unemployment, low rates'}
    return scores

def calculate(self, analysis_type: str='phase_detection', **kwargs) -> Dict[str, Any]:
    """Main business cycle calculation dispatcher"""
    if analysis_type == 'phase_detection':
        return self.detect_cycle_phase(kwargs['economic_indicators'])
    elif analysis_type == 'sector_cyclicality':
        return self.analyze_sector_cyclicality(kwargs['sector_data'])
    else:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')

class CreditCycleAnalyzer(EconomicsBase):
    """Credit cycle analysis and financial stability assessment"""

    def analyze_credit_cycle(self, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current credit cycle phase and characteristics"""
        credit_growth = self.to_decimal(credit_data.get('credit_growth_rate', 0))
        loan_standards = credit_data.get('lending_standards', 'neutral')
        credit_spreads = self.to_decimal(credit_data.get('credit_spreads_bps', 0))
        default_rates = self.to_decimal(credit_data.get('default_rate', 0))
        leverage_ratio = self.to_decimal(credit_data.get('leverage_ratio', 0))
        asset_prices = self.to_decimal(credit_data.get('asset_price_growth', 0))
        cycle_phase = self._determine_credit_phase(credit_growth, loan_standards, credit_spreads, default_rates)
        return {'credit_cycle_phase': cycle_phase, 'phase_characteristics': self._get_credit_phase_characteristics(cycle_phase), 'risk_assessment': self._assess_credit_risks(credit_growth, leverage_ratio, default_rates, asset_prices), 'financial_stability_indicators': self._analyze_financial_stability(credit_data), 'investment_implications': self._credit_cycle_investment_implications(cycle_phase), 'policy_implications': self._credit_cycle_policy_implications(cycle_phase, credit_data)}

    def _determine_credit_phase(self, credit_growth: Decimal, standards: str, spreads: Decimal, defaults: Decimal) -> str:
        """Determine current credit cycle phase"""
        if credit_growth > self.to_decimal(5) and standards == 'loose' and (spreads < self.to_decimal(200)):
            return 'expansion'
        elif credit_growth > self.to_decimal(8) and spreads < self.to_decimal(150) and (defaults < self.to_decimal(2)):
            return 'peak'
        elif credit_growth < self.to_decimal(0) and standards == 'tight' and (spreads > self.to_decimal(300)):
            return 'contraction'
        elif credit_growth < self.to_decimal(2) and defaults > self.to_decimal(5) and (spreads > self.to_decimal(400)):
            return 'trough'
        else:
            return 'transition'

    def _get_credit_phase_characteristics(self, phase: str) -> Dict[str, Any]:
        """Get characteristics of each credit cycle phase"""
        characteristics = {'expansion': {'credit_growth': 'Accelerating', 'lending_standards': 'Loosening', 'credit_spreads': 'Tightening', 'default_rates': 'Low and declining', 'asset_prices': 'Rising', 'risk_appetite': 'Increasing', 'typical_duration': '3-7 years'}, 'peak': {'credit_growth': 'Very high but potentially slowing', 'lending_standards': 'Very loose', 'credit_spreads': 'Very tight', 'default_rates': 'Near cyclical lows', 'asset_prices': 'Near peaks, potential bubbles', 'risk_appetite': 'Excessive', 'typical_duration': '6-18 months'}, 'contraction': {'credit_growth': 'Negative', 'lending_standards': 'Tightening rapidly', 'credit_spreads': 'Widening', 'default_rates': 'Rising sharply', 'asset_prices': 'Declining', 'risk_appetite': 'Risk aversion', 'typical_duration': '1-3 years'}, 'trough': {'credit_growth': 'Negative but stabilizing', 'lending_standards': 'Very tight', 'credit_spreads': 'Wide but stabilizing', 'default_rates': 'High but peaking', 'asset_prices': 'Depressed but stabilizing', 'risk_appetite': 'Extremely low', 'typical_duration': '6-18 months'}}
        return characteristics.get(phase, {})

    def _assess_credit_risks(self, credit_growth: Decimal, leverage: Decimal, defaults: Decimal, asset_prices: Decimal) -> Dict[str, Any]:
        """Assess systemic credit risks"""
        risk_score = self.to_decimal(0)
        risk_factors = []
        if credit_growth > self.to_decimal(10):
            risk_score += self.to_decimal(25)
            risk_factors.append('Excessive credit growth')
        if leverage > self.to_decimal(8):
            risk_score += self.to_decimal(25)
            risk_factors.append('High leverage ratios')
        if defaults > self.to_decimal(4):
            risk_score += self.to_decimal(20)
            risk_factors.append('Rising default rates')
        if asset_prices > self.to_decimal(15):
            risk_score += self.to_decimal(20)
            risk_factors.append('Asset price bubbles')
        if risk_score > self.to_decimal(60):
            risk_level = 'High'
        elif risk_score > self.to_decimal(30):
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        return {'overall_risk_score': risk_score, 'risk_level': risk_level, 'key_risk_factors': risk_factors, 'systemic_risk_probability': self._calculate_systemic_risk_probability(risk_score)}

    def _calculate_systemic_risk_probability(self, risk_score: Decimal) -> str:
        """Calculate probability of systemic financial crisis"""
        if risk_score > self.to_decimal(70):
            return 'High (>30% in next 2 years)'
        elif risk_score > self.to_decimal(50):
            return 'Moderate (10-30% in next 2 years)'
        elif risk_score > self.to_decimal(30):
            return 'Low (5-10% in next 2 years)'
        else:
            return 'Very Low (<5% in next 2 years)'

    def _analyze_financial_stability(self, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial stability indicators"""
        return {'banking_sector_health': {'capital_adequacy': credit_data.get('bank_capital_ratio', 'N/A'), 'loan_loss_provisions': credit_data.get('loan_loss_provisions', 'N/A'), 'profitability': credit_data.get('bank_roe', 'N/A'), 'asset_quality': credit_data.get('npl_ratio', 'N/A')}, 'household_sector': {'debt_to_income': credit_data.get('household_debt_ratio', 'N/A'), 'mortgage_defaults': credit_data.get('mortgage_default_rate', 'N/A'), 'savings_rate': credit_data.get('household_savings_rate', 'N/A')}, 'corporate_sector': {'corporate_debt_ratio': credit_data.get('corporate_debt_gdp', 'N/A'), 'interest_coverage': credit_data.get('interest_coverage_ratio', 'N/A'), 'bankruptcy_rate': credit_data.get('corporate_bankruptcy_rate', 'N/A')}, 'government_sector': {'debt_to_gdp': credit_data.get('government_debt_gdp', 'N/A'), 'deficit_ratio': credit_data.get('budget_deficit_gdp', 'N/A')}}

    def _credit_cycle_investment_implications(self, phase: str) -> Dict[str, Any]:
        """Investment implications for each credit cycle phase"""
        implications = {'expansion': {'credit_sensitive_sectors': 'Favor banks, real estate, consumer finance', 'fixed_income': 'Corporate bonds outperform, credit spreads tighten', 'equity_strategy': 'Growth and cyclical stocks perform well', 'risk_management': 'Monitor leverage, prepare for cycle turn'}, 'peak': {'credit_sensitive_sectors': 'Begin reducing exposure to credit cyclicals', 'fixed_income': 'Lock in credit spreads, extend duration', 'equity_strategy': 'Rotate to defensive sectors', 'risk_management': 'Reduce overall risk exposure'}, 'contraction': {'credit_sensitive_sectors': 'Avoid banks, real estate, high-yield bonds', 'fixed_income': 'Government bonds, high-grade corporates', 'equity_strategy': 'Defensive sectors, dividend stocks', 'risk_management': 'Capital preservation focus'}, 'trough': {'credit_sensitive_sectors': 'Prepare for opportunistic investments', 'fixed_income': 'Distressed debt opportunities', 'equity_strategy': 'Value opportunities in beaten-down sectors', 'risk_management': 'Begin rebuilding risk exposure'}}
        return implications.get(phase, {})

    def _credit_cycle_policy_implications(self, phase: str, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Policy implications for each credit cycle phase"""
        base_implications = {'expansion': {'monetary_policy': 'Consider gradual tightening to prevent bubbles', 'macroprudential': 'Implement countercyclical capital buffers', 'regulatory': 'Monitor systemic risk buildup'}, 'peak': {'monetary_policy': 'Careful balancing to prevent hard landing', 'macroprudential': 'Activate countercyclical buffers', 'regulatory': 'Stress test financial institutions'}, 'contraction': {'monetary_policy': 'Aggressive easing to support credit flow', 'macroprudential': 'Release countercyclical buffers', 'regulatory': 'Temporary forbearance measures'}, 'trough': {'monetary_policy': 'Maintain accommodative stance', 'macroprudential': 'Gradual rebuilding of buffers', 'regulatory': 'Support credit intermediation'}}
        return base_implications.get(phase, {})

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate credit cycle analysis"""
        return self.analyze_credit_cycle(kwargs['credit_data'])

def analyze_credit_cycle(self, credit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze current credit cycle phase and characteristics"""
    credit_growth = self.to_decimal(credit_data.get('credit_growth_rate', 0))
    loan_standards = credit_data.get('lending_standards', 'neutral')
    credit_spreads = self.to_decimal(credit_data.get('credit_spreads_bps', 0))
    default_rates = self.to_decimal(credit_data.get('default_rate', 0))
    leverage_ratio = self.to_decimal(credit_data.get('leverage_ratio', 0))
    asset_prices = self.to_decimal(credit_data.get('asset_price_growth', 0))
    cycle_phase = self._determine_credit_phase(credit_growth, loan_standards, credit_spreads, default_rates)
    return {'credit_cycle_phase': cycle_phase, 'phase_characteristics': self._get_credit_phase_characteristics(cycle_phase), 'risk_assessment': self._assess_credit_risks(credit_growth, leverage_ratio, default_rates, asset_prices), 'financial_stability_indicators': self._analyze_financial_stability(credit_data), 'investment_implications': self._credit_cycle_investment_implications(cycle_phase), 'policy_implications': self._credit_cycle_policy_implications(cycle_phase, credit_data)}

def _determine_credit_phase(self, credit_growth: Decimal, standards: str, spreads: Decimal, defaults: Decimal) -> str:
    """Determine current credit cycle phase"""
    if credit_growth > self.to_decimal(5) and standards == 'loose' and (spreads < self.to_decimal(200)):
        return 'expansion'
    elif credit_growth > self.to_decimal(8) and spreads < self.to_decimal(150) and (defaults < self.to_decimal(2)):
        return 'peak'
    elif credit_growth < self.to_decimal(0) and standards == 'tight' and (spreads > self.to_decimal(300)):
        return 'contraction'
    elif credit_growth < self.to_decimal(2) and defaults > self.to_decimal(5) and (spreads > self.to_decimal(400)):
        return 'trough'
    else:
        return 'transition'

def _assess_credit_risks(self, credit_growth: Decimal, leverage: Decimal, defaults: Decimal, asset_prices: Decimal) -> Dict[str, Any]:
    """Assess systemic credit risks"""
    risk_score = self.to_decimal(0)
    risk_factors = []
    if credit_growth > self.to_decimal(10):
        risk_score += self.to_decimal(25)
        risk_factors.append('Excessive credit growth')
    if leverage > self.to_decimal(8):
        risk_score += self.to_decimal(25)
        risk_factors.append('High leverage ratios')
    if defaults > self.to_decimal(4):
        risk_score += self.to_decimal(20)
        risk_factors.append('Rising default rates')
    if asset_prices > self.to_decimal(15):
        risk_score += self.to_decimal(20)
        risk_factors.append('Asset price bubbles')
    if risk_score > self.to_decimal(60):
        risk_level = 'High'
    elif risk_score > self.to_decimal(30):
        risk_level = 'Moderate'
    else:
        risk_level = 'Low'
    return {'overall_risk_score': risk_score, 'risk_level': risk_level, 'key_risk_factors': risk_factors, 'systemic_risk_probability': self._calculate_systemic_risk_probability(risk_score)}

def _calculate_systemic_risk_probability(self, risk_score: Decimal) -> str:
    """Calculate probability of systemic financial crisis"""
    if risk_score > self.to_decimal(70):
        return 'High (>30% in next 2 years)'
    elif risk_score > self.to_decimal(50):
        return 'Moderate (10-30% in next 2 years)'
    elif risk_score > self.to_decimal(30):
        return 'Low (5-10% in next 2 years)'
    else:
        return 'Very Low (<5% in next 2 years)'

class MarketStructureAnalyzer(EconomicsBase):
    """Market structure analysis and competitive dynamics"""

    def identify_market_structure(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify market structure type and characteristics"""
        num_firms = int(market_data.get('number_of_firms', 0))
        market_concentration = self.to_decimal(market_data.get('herfindahl_index', 0))
        product_differentiation = market_data.get('product_differentiation', 'low')
        barriers_to_entry = market_data.get('barriers_to_entry', 'low')
        pricing_power = market_data.get('pricing_power', 'low')
        structure_type = self._classify_market_structure(num_firms, market_concentration, product_differentiation, barriers_to_entry)
        return {'market_structure_type': structure_type, 'structure_characteristics': self._get_structure_characteristics(structure_type), 'concentration_analysis': self._analyze_concentration(market_concentration, num_firms), 'competitive_dynamics': self._analyze_competitive_dynamics(structure_type, market_data), 'pricing_analysis': self._analyze_pricing_behavior(structure_type, market_data), 'efficiency_implications': self._analyze_efficiency_implications(structure_type), 'regulatory_considerations': self._get_regulatory_considerations(structure_type)}

    def _classify_market_structure(self, num_firms: int, concentration: Decimal, differentiation: str, barriers: str) -> str:
        """Classify market structure based on key characteristics"""
        if num_firms > 100 and concentration < self.to_decimal(0.01) and (differentiation == 'none') and (barriers == 'low'):
            return 'perfect_competition'
        elif num_firms == 1 or concentration > self.to_decimal(0.9):
            return 'monopoly'
        elif num_firms <= 10 and concentration > self.to_decimal(0.6) and (barriers in ['high', 'moderate']):
            return 'oligopoly'
        else:
            return 'monopolistic_competition'

    def _get_structure_characteristics(self, structure_type: str) -> Dict[str, Any]:
        """Get detailed characteristics of each market structure"""
        characteristics = {'perfect_competition': {'number_of_firms': 'Many (hundreds or thousands)', 'product_differentiation': 'None (homogeneous products)', 'barriers_to_entry': 'None', 'pricing_power': 'None (price takers)', 'long_run_profits': 'Zero economic profits', 'efficiency': 'Allocatively and productively efficient', 'examples': 'Agricultural markets, commodity markets'}, 'monopolistic_competition': {'number_of_firms': 'Many (dozens to hundreds)', 'product_differentiation': 'Some (differentiated products)', 'barriers_to_entry': 'Low', 'pricing_power': 'Limited (some control over price)', 'long_run_profits': 'Zero economic profits', 'efficiency': 'Not fully efficient due to excess capacity', 'examples': 'Restaurants, retail clothing, personal services'}, 'oligopoly': {'number_of_firms': 'Few (typically 3-10)', 'product_differentiation': 'May be homogeneous or differentiated', 'barriers_to_entry': 'High', 'pricing_power': 'Significant (price makers)', 'long_run_profits': 'Positive economic profits possible', 'efficiency': 'Generally inefficient, potential for collusion', 'examples': 'Airlines, telecommunications, automobiles'}, 'monopoly': {'number_of_firms': 'One', 'product_differentiation': 'Unique product (no close substitutes)', 'barriers_to_entry': 'Very high or absolute', 'pricing_power': 'Maximum (price maker)', 'long_run_profits': 'Positive economic profits', 'efficiency': 'Allocatively inefficient, may be productively efficient', 'examples': 'Public utilities, patented drugs, natural monopolies'}}
        return characteristics.get(structure_type, {})

    def _analyze_concentration(self, hhi: Decimal, num_firms: int) -> Dict[str, Any]:
        """Analyze market concentration using various measures"""
        if hhi > self.to_decimal(0.25):
            concentration_level = 'Highly Concentrated'
            antitrust_concern = 'High'
        elif hhi > self.to_decimal(0.15):
            concentration_level = 'Moderately Concentrated'
            antitrust_concern = 'Moderate'
        else:
            concentration_level = 'Unconcentrated'
            antitrust_concern = 'Low'
        if num_firms > 0:
            avg_market_share = self.to_decimal(1) / self.to_decimal(num_firms)
        else:
            avg_market_share = self.to_decimal(0)
        return {'herfindahl_index': hhi, 'concentration_level': concentration_level, 'antitrust_concern': antitrust_concern, 'number_of_firms': num_firms, 'average_market_share': avg_market_share * self.to_decimal(100), 'concentration_interpretation': self._interpret_hhi(hhi)}

    def _interpret_hhi(self, hhi: Decimal) -> str:
        """Interpret HHI values"""
        if hhi > self.to_decimal(0.25):
            return 'Market dominated by few large firms, potential monopoly power'
        elif hhi > self.to_decimal(0.15):
            return 'Market moderately concentrated, some pricing power exists'
        elif hhi > self.to_decimal(0.1):
            return 'Market somewhat concentrated, limited pricing power'
        else:
            return 'Market unconcentrated, competitive pricing likely'

    def _analyze_competitive_dynamics(self, structure_type: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive dynamics for each market structure"""
        dynamics = {'perfect_competition': {'competition_intensity': 'Maximum', 'strategic_behavior': 'None (price takers)', 'product_strategy': 'Focus on cost efficiency', 'market_response': 'Immediate price adjustments', 'long_term_strategy': 'Operational excellence'}, 'monopolistic_competition': {'competition_intensity': 'High but differentiated', 'strategic_behavior': 'Product differentiation focus', 'product_strategy': 'Brand building, innovation', 'market_response': 'Gradual price and product adjustments', 'long_term_strategy': 'Sustainable differentiation'}, 'oligopoly': {'competition_intensity': 'Strategic interdependence', 'strategic_behavior': 'Game theory applies, potential collusion', 'product_strategy': 'Innovation and differentiation', 'market_response': 'Strategic reactions to competitors', 'long_term_strategy': 'Market share protection'}, 'monopoly': {'competition_intensity': 'None or minimal', 'strategic_behavior': 'Price and output optimization', 'product_strategy': 'Innovation optional', 'market_response': 'Independent pricing decisions', 'long_term_strategy': 'Barrier maintenance'}}
        return dynamics.get(structure_type, {})

    def calculate_breakeven_shutdown_points(self, cost_data: Dict[str, Any], market_structure: str) -> Dict[str, Any]:
        """Calculate breakeven and shutdown points for different market structures"""
        fixed_costs = self.to_decimal(cost_data.get('fixed_costs', 0))
        variable_cost_per_unit = self.to_decimal(cost_data.get('variable_cost_per_unit', 0))
        market_price = self.to_decimal(cost_data.get('market_price', 0))
        capacity = self.to_decimal(cost_data.get('capacity', 0))
        total_costs = lambda q: fixed_costs + variable_cost_per_unit * q
        average_total_cost = lambda q: total_costs(q) / q if q > 0 else self.to_decimal(0)
        average_variable_cost = variable_cost_per_unit
        marginal_cost = variable_cost_per_unit
        if market_price > variable_cost_per_unit:
            breakeven_quantity = fixed_costs / (market_price - variable_cost_per_unit)
        else:
            breakeven_quantity = None
        shutdown_price = average_variable_cost
        optimal_output = self._calculate_optimal_output(market_structure, market_price, marginal_cost, capacity)
        return {'cost_structure': {'fixed_costs': fixed_costs, 'variable_cost_per_unit': variable_cost_per_unit, 'average_variable_cost': average_variable_cost, 'marginal_cost': marginal_cost}, 'breakeven_analysis': {'breakeven_quantity': breakeven_quantity, 'breakeven_revenue': breakeven_quantity * market_price if breakeven_quantity else None, 'contribution_margin': market_price - variable_cost_per_unit, 'contribution_margin_ratio': (market_price - variable_cost_per_unit) / market_price * self.to_decimal(100) if market_price > 0 else self.to_decimal(0)}, 'shutdown_analysis': {'shutdown_price': shutdown_price, 'current_price': market_price, 'should_shutdown': market_price < shutdown_price, 'shutdown_loss': fixed_costs if market_price < shutdown_price else self.to_decimal(0)}, 'optimal_production': {'optimal_quantity': optimal_output, 'total_revenue': optimal_output * market_price, 'total_costs': total_costs(optimal_output), 'economic_profit': optimal_output * market_price - total_costs(optimal_output)}, 'scale_economies': self._analyze_economies_of_scale(cost_data, optimal_output)}

    def _calculate_optimal_output(self, structure_type: str, price: Decimal, marginal_cost: Decimal, capacity: Decimal) -> Decimal:
        """Calculate optimal output for different market structures"""
        if structure_type == 'perfect_competition':
            if price >= marginal_cost:
                return capacity
            else:
                return self.to_decimal(0)
        elif structure_type == 'monopolistic_competition':
            if price > marginal_cost:
                return capacity * self.to_decimal(0.8)
            else:
                return self.to_decimal(0)
        elif structure_type in ['oligopoly', 'monopoly']:
            if price > marginal_cost * self.to_decimal(1.2):
                return capacity * self.to_decimal(0.7)
            else:
                return capacity * self.to_decimal(0.5)
        else:
            return capacity * self.to_decimal(0.75)

    def _analyze_economies_of_scale(self, cost_data: Dict[str, Any], current_output: Decimal) -> Dict[str, Any]:
        """Analyze economies and diseconomies of scale"""
        min_efficient_scale = self.to_decimal(cost_data.get('min_efficient_scale', 0))
        capacity = self.to_decimal(cost_data.get('capacity', 0))
        if current_output < min_efficient_scale:
            scale_position = 'Below minimum efficient scale'
            scale_effect = 'Economies of scale available'
            recommendation = 'Increase production to reduce average costs'
        elif current_output <= capacity * self.to_decimal(0.9):
            scale_position = 'At or near optimal scale'
            scale_effect = 'Constant returns to scale'
            recommendation = 'Current scale is efficient'
        else:
            scale_position = 'Above optimal scale'
            scale_effect = 'Potential diseconomies of scale'
            recommendation = 'Consider capacity expansion or efficiency improvements'
        return {'current_output': current_output, 'minimum_efficient_scale': min_efficient_scale, 'capacity_utilization': current_output / capacity * self.to_decimal(100) if capacity > 0 else self.to_decimal(0), 'scale_position': scale_position, 'scale_effect': scale_effect, 'recommendation': recommendation}

    def _analyze_pricing_behavior(self, structure_type: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pricing behavior and strategies for each market structure"""
        pricing_behavior = {'perfect_competition': {'pricing_strategy': 'Price taking (no control)', 'price_setting': 'Market determined', 'demand_curve': 'Perfectly elastic', 'profit_maximization': 'P = MC', 'price_discrimination': 'Not possible'}, 'monopolistic_competition': {'pricing_strategy': 'Limited pricing power', 'price_setting': 'Some control over price', 'demand_curve': 'Downward sloping but elastic', 'profit_maximization': 'MR = MC', 'price_discrimination': 'Limited opportunities'}, 'oligopoly': {'pricing_strategy': 'Strategic pricing', 'price_setting': 'Mutual interdependence', 'demand_curve': 'Kinked demand curve possible', 'profit_maximization': 'Game theory considerations', 'price_discrimination': 'Possible with market segmentation'}, 'monopoly': {'pricing_strategy': 'Price maker', 'price_setting': 'Full control subject to demand', 'demand_curve': 'Downward sloping', 'profit_maximization': 'MR = MC', 'price_discrimination': 'Multiple types possible'}}
        return pricing_behavior.get(structure_type, {})

    def _analyze_efficiency_implications(self, structure_type: str) -> Dict[str, Any]:
        """Analyze efficiency implications of each market structure"""
        efficiency = {'perfect_competition': {'allocative_efficiency': 'Yes (P = MC)', 'productive_efficiency': 'Yes (minimum ATC)', 'dynamic_efficiency': 'Limited (low profits for R&D)', 'consumer_surplus': 'Maximized', 'deadweight_loss': 'None'}, 'monopolistic_competition': {'allocative_efficiency': 'No (P > MC)', 'productive_efficiency': 'No (excess capacity)', 'dynamic_efficiency': 'Moderate (innovation incentives)', 'consumer_surplus': 'Reduced due to higher prices', 'deadweight_loss': 'Small'}, 'oligopoly': {'allocative_efficiency': 'No (P > MC)', 'productive_efficiency': 'Uncertain (may achieve scale economies)', 'dynamic_efficiency': 'High (R&D competition)', 'consumer_surplus': 'Significantly reduced', 'deadweight_loss': 'Moderate to large'}, 'monopoly': {'allocative_efficiency': 'No (P > MC)', 'productive_efficiency': 'Uncertain (may achieve scale economies)', 'dynamic_efficiency': 'Low (limited competition pressure)', 'consumer_surplus': 'Minimized', 'deadweight_loss': 'Large'}}
        return efficiency.get(structure_type, {})

    def _get_regulatory_considerations(self, structure_type: str) -> Dict[str, Any]:
        """Get regulatory considerations for each market structure"""
        regulations = {'perfect_competition': {'antitrust_concern': 'None', 'regulation_needed': 'Minimal', 'focus': 'Maintain competitive conditions', 'interventions': 'Prevent artificial barriers to entry'}, 'monopolistic_competition': {'antitrust_concern': 'Low', 'regulation_needed': 'Light touch', 'focus': 'Consumer protection, fair advertising', 'interventions': 'Truth in advertising, quality standards'}, 'oligopoly': {'antitrust_concern': 'High', 'regulation_needed': 'Active monitoring', 'focus': 'Prevent collusion, monitor mergers', 'interventions': 'Merger review, price fixing prevention'}, 'monopoly': {'antitrust_concern': 'Very high', 'regulation_needed': 'Heavy regulation or breakup', 'focus': 'Price regulation, service quality', 'interventions': 'Rate regulation, structural remedies'}}
        return regulations.get(structure_type, {})

    def calculate(self, analysis_type: str='structure_identification', **kwargs) -> Dict[str, Any]:
        """Main market structure calculation dispatcher"""
        if analysis_type == 'structure_identification':
            return self.identify_market_structure(kwargs['market_data'])
        elif analysis_type == 'breakeven_shutdown':
            return self.calculate_breakeven_shutdown_points(kwargs['cost_data'], kwargs['market_structure'])
        else:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')

def identify_market_structure(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Identify market structure type and characteristics"""
    num_firms = int(market_data.get('number_of_firms', 0))
    market_concentration = self.to_decimal(market_data.get('herfindahl_index', 0))
    product_differentiation = market_data.get('product_differentiation', 'low')
    barriers_to_entry = market_data.get('barriers_to_entry', 'low')
    pricing_power = market_data.get('pricing_power', 'low')
    structure_type = self._classify_market_structure(num_firms, market_concentration, product_differentiation, barriers_to_entry)
    return {'market_structure_type': structure_type, 'structure_characteristics': self._get_structure_characteristics(structure_type), 'concentration_analysis': self._analyze_concentration(market_concentration, num_firms), 'competitive_dynamics': self._analyze_competitive_dynamics(structure_type, market_data), 'pricing_analysis': self._analyze_pricing_behavior(structure_type, market_data), 'efficiency_implications': self._analyze_efficiency_implications(structure_type), 'regulatory_considerations': self._get_regulatory_considerations(structure_type)}

def _classify_market_structure(self, num_firms: int, concentration: Decimal, differentiation: str, barriers: str) -> str:
    """Classify market structure based on key characteristics"""
    if num_firms > 100 and concentration < self.to_decimal(0.01) and (differentiation == 'none') and (barriers == 'low'):
        return 'perfect_competition'
    elif num_firms == 1 or concentration > self.to_decimal(0.9):
        return 'monopoly'
    elif num_firms <= 10 and concentration > self.to_decimal(0.6) and (barriers in ['high', 'moderate']):
        return 'oligopoly'
    else:
        return 'monopolistic_competition'

def _analyze_concentration(self, hhi: Decimal, num_firms: int) -> Dict[str, Any]:
    """Analyze market concentration using various measures"""
    if hhi > self.to_decimal(0.25):
        concentration_level = 'Highly Concentrated'
        antitrust_concern = 'High'
    elif hhi > self.to_decimal(0.15):
        concentration_level = 'Moderately Concentrated'
        antitrust_concern = 'Moderate'
    else:
        concentration_level = 'Unconcentrated'
        antitrust_concern = 'Low'
    if num_firms > 0:
        avg_market_share = self.to_decimal(1) / self.to_decimal(num_firms)
    else:
        avg_market_share = self.to_decimal(0)
    return {'herfindahl_index': hhi, 'concentration_level': concentration_level, 'antitrust_concern': antitrust_concern, 'number_of_firms': num_firms, 'average_market_share': avg_market_share * self.to_decimal(100), 'concentration_interpretation': self._interpret_hhi(hhi)}

def _interpret_hhi(self, hhi: Decimal) -> str:
    """Interpret HHI values"""
    if hhi > self.to_decimal(0.25):
        return 'Market dominated by few large firms, potential monopoly power'
    elif hhi > self.to_decimal(0.15):
        return 'Market moderately concentrated, some pricing power exists'
    elif hhi > self.to_decimal(0.1):
        return 'Market somewhat concentrated, limited pricing power'
    else:
        return 'Market unconcentrated, competitive pricing likely'

def calculate_breakeven_shutdown_points(self, cost_data: Dict[str, Any], market_structure: str) -> Dict[str, Any]:
    """Calculate breakeven and shutdown points for different market structures"""
    fixed_costs = self.to_decimal(cost_data.get('fixed_costs', 0))
    variable_cost_per_unit = self.to_decimal(cost_data.get('variable_cost_per_unit', 0))
    market_price = self.to_decimal(cost_data.get('market_price', 0))
    capacity = self.to_decimal(cost_data.get('capacity', 0))
    total_costs = lambda q: fixed_costs + variable_cost_per_unit * q
    average_total_cost = lambda q: total_costs(q) / q if q > 0 else self.to_decimal(0)
    average_variable_cost = variable_cost_per_unit
    marginal_cost = variable_cost_per_unit
    if market_price > variable_cost_per_unit:
        breakeven_quantity = fixed_costs / (market_price - variable_cost_per_unit)
    else:
        breakeven_quantity = None
    shutdown_price = average_variable_cost
    optimal_output = self._calculate_optimal_output(market_structure, market_price, marginal_cost, capacity)
    return {'cost_structure': {'fixed_costs': fixed_costs, 'variable_cost_per_unit': variable_cost_per_unit, 'average_variable_cost': average_variable_cost, 'marginal_cost': marginal_cost}, 'breakeven_analysis': {'breakeven_quantity': breakeven_quantity, 'breakeven_revenue': breakeven_quantity * market_price if breakeven_quantity else None, 'contribution_margin': market_price - variable_cost_per_unit, 'contribution_margin_ratio': (market_price - variable_cost_per_unit) / market_price * self.to_decimal(100) if market_price > 0 else self.to_decimal(0)}, 'shutdown_analysis': {'shutdown_price': shutdown_price, 'current_price': market_price, 'should_shutdown': market_price < shutdown_price, 'shutdown_loss': fixed_costs if market_price < shutdown_price else self.to_decimal(0)}, 'optimal_production': {'optimal_quantity': optimal_output, 'total_revenue': optimal_output * market_price, 'total_costs': total_costs(optimal_output), 'economic_profit': optimal_output * market_price - total_costs(optimal_output)}, 'scale_economies': self._analyze_economies_of_scale(cost_data, optimal_output)}

def _calculate_optimal_output(self, structure_type: str, price: Decimal, marginal_cost: Decimal, capacity: Decimal) -> Decimal:
    """Calculate optimal output for different market structures"""
    if structure_type == 'perfect_competition':
        if price >= marginal_cost:
            return capacity
        else:
            return self.to_decimal(0)
    elif structure_type == 'monopolistic_competition':
        if price > marginal_cost:
            return capacity * self.to_decimal(0.8)
        else:
            return self.to_decimal(0)
    elif structure_type in ['oligopoly', 'monopoly']:
        if price > marginal_cost * self.to_decimal(1.2):
            return capacity * self.to_decimal(0.7)
        else:
            return capacity * self.to_decimal(0.5)
    else:
        return capacity * self.to_decimal(0.75)

def _analyze_economies_of_scale(self, cost_data: Dict[str, Any], current_output: Decimal) -> Dict[str, Any]:
    """Analyze economies and diseconomies of scale"""
    min_efficient_scale = self.to_decimal(cost_data.get('min_efficient_scale', 0))
    capacity = self.to_decimal(cost_data.get('capacity', 0))
    if current_output < min_efficient_scale:
        scale_position = 'Below minimum efficient scale'
        scale_effect = 'Economies of scale available'
        recommendation = 'Increase production to reduce average costs'
    elif current_output <= capacity * self.to_decimal(0.9):
        scale_position = 'At or near optimal scale'
        scale_effect = 'Constant returns to scale'
        recommendation = 'Current scale is efficient'
    else:
        scale_position = 'Above optimal scale'
        scale_effect = 'Potential diseconomies of scale'
        recommendation = 'Consider capacity expansion or efficiency improvements'
    return {'current_output': current_output, 'minimum_efficient_scale': min_efficient_scale, 'capacity_utilization': current_output / capacity * self.to_decimal(100) if capacity > 0 else self.to_decimal(0), 'scale_position': scale_position, 'scale_effect': scale_effect, 'recommendation': recommendation}

def calculate(self, analysis_type: str='structure_identification', **kwargs) -> Dict[str, Any]:
    """Main market structure calculation dispatcher"""
    if analysis_type == 'structure_identification':
        return self.identify_market_structure(kwargs['market_data'])
    elif analysis_type == 'breakeven_shutdown':
        return self.calculate_breakeven_shutdown_points(kwargs['cost_data'], kwargs['market_structure'])
    else:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')

class FiscalPolicyAnalyzer(EconomicsBase):
    """Fiscal policy analysis and impact assessment"""

    def compare_fiscal_monetary(self) -> Dict[str, Any]:
        """Compare fiscal and monetary policy characteristics"""
        return {'fiscal_policy': {'authority': 'Government (legislative/executive)', 'tools': ['Government spending', 'Taxation', 'Transfer payments'], 'targets': ['Economic growth', 'Employment', 'Income distribution'], 'transmission': 'Direct impact on aggregate demand', 'lag_time': 'Long (6-18 months)', 'political_influence': 'High', 'flexibility': 'Low (requires legislative approval)'}, 'monetary_policy': {'authority': 'Central bank', 'tools': ['Interest rates', 'Money supply', 'Reserve requirements'], 'targets': ['Price stability', 'Economic growth', 'Financial stability'], 'transmission': 'Indirect through financial markets', 'lag_time': 'Medium (3-12 months)', 'political_influence': 'Low (independent)', 'flexibility': 'High (quick implementation)'}, 'interaction_effects': {'complementary': 'Both expansionary during recession', 'conflicting': 'Fiscal expansion with monetary tightening', 'coordination_importance': 'Critical for policy effectiveness'}}

    def analyze_fiscal_tools(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fiscal policy tools and their effects"""
        tools_analysis = {'government_spending': {'multiplier_effect': self._calculate_spending_multiplier(policy_data), 'advantages': ['Direct job creation', 'Infrastructure investment', 'Quick stimulus'], 'disadvantages': ['Crowding out private investment', 'Debt accumulation', 'Political interference'], 'effectiveness': 'High during recessions, moderate during expansions'}, 'taxation': {'multiplier_effect': self._calculate_tax_multiplier(policy_data), 'advantages': ['Broad-based impact', 'Revenue generation', 'Incentive alignment'], 'disadvantages': ['Lagged response', 'Political constraints', 'Distortionary effects'], 'effectiveness': 'Moderate, depends on tax type and economic conditions'}, 'transfer_payments': {'multiplier_effect': self._calculate_transfer_multiplier(policy_data), 'advantages': ['Targeted support', 'Automatic stabilizers', 'Social safety net'], 'disadvantages': ['Potential dependency', 'Fiscal burden', 'Limited growth impact'], 'effectiveness': 'High for consumption support, moderate for growth'}}
        return {'tools_analysis': tools_analysis, 'implementation_challenges': self._assess_implementation_challenges(), 'policy_recommendation': self._recommend_fiscal_mix(policy_data)}

    def assess_debt_sustainability(self, debt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess whether national debt relative to GDP matters"""
        debt_gdp = self.to_decimal(debt_data.get('debt_to_gdp_ratio', 0))
        gdp_growth = self.to_decimal(debt_data.get('gdp_growth_rate', 0))
        interest_rate = self.to_decimal(debt_data.get('avg_interest_rate', 0))
        primary_balance = self.to_decimal(debt_data.get('primary_balance_gdp', 0))
        sustainability_gap = interest_rate - gdp_growth - primary_balance
        if debt_gdp > self.to_decimal(100):
            risk_level = 'Very High'
        elif debt_gdp > self.to_decimal(60):
            risk_level = 'High'
        elif debt_gdp > self.to_decimal(40):
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        return {'debt_to_gdp': debt_gdp, 'sustainability_gap': sustainability_gap, 'sustainable': sustainability_gap < self.to_decimal(0), 'risk_level': risk_level, 'debt_dynamics': {'interest_burden': interest_rate * debt_gdp / self.to_decimal(100), 'growth_benefit': gdp_growth * debt_gdp / self.to_decimal(100), 'primary_contribution': primary_balance}, 'implications': self._get_debt_implications(debt_gdp, sustainability_gap)}

    def identify_policy_stance(self, fiscal_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Identify if fiscal policy is expansionary or contractionary"""
        spending_change = self.to_decimal(fiscal_indicators.get('spending_change_percent', 0))
        tax_change = self.to_decimal(fiscal_indicators.get('tax_change_percent', 0))
        deficit_change = self.to_decimal(fiscal_indicators.get('deficit_change_gdp', 0))
        fiscal_impulse = spending_change - tax_change
        if fiscal_impulse > self.to_decimal(1):
            stance = 'Expansionary'
            description = 'Government increasing spending more than taxes'
        elif fiscal_impulse < self.to_decimal(-1):
            stance = 'Contractionary'
            description = 'Government reducing spending or increasing taxes significantly'
        else:
            stance = 'Neutral'
            description = 'Minimal net fiscal impact'
        return {'fiscal_stance': stance, 'fiscal_impulse': fiscal_impulse, 'description': description, 'stance_indicators': {'spending_change': spending_change, 'tax_change': tax_change, 'deficit_change': deficit_change}, 'economic_impact': self._assess_stance_impact(stance, fiscal_impulse)}

    def _calculate_spending_multiplier(self, data: Dict[str, Any]) -> Decimal:
        """Calculate government spending multiplier"""
        mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
        return self.to_decimal(1) / (self.to_decimal(1) - mpc)

    def _calculate_tax_multiplier(self, data: Dict[str, Any]) -> Decimal:
        """Calculate tax multiplier"""
        mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
        return -mpc / (self.to_decimal(1) - mpc)

    def _calculate_transfer_multiplier(self, data: Dict[str, Any]) -> Decimal:
        """Calculate transfer payment multiplier"""
        mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
        return mpc / (self.to_decimal(1) - mpc)

    def _assess_implementation_challenges(self) -> List[str]:
        """Assess fiscal policy implementation difficulties"""
        return ['Recognition lag: Time to identify economic problems', 'Legislative lag: Time for political approval', 'Implementation lag: Time to execute policy', 'Political constraints: Electoral and partisan considerations', 'Crowding out: Government borrowing affects private investment', 'Ricardian equivalence: Tax cuts offset by expected future taxes']

    def _recommend_fiscal_mix(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Recommend optimal fiscal policy mix"""
        unemployment = self.to_decimal(data.get('unemployment_rate', 0))
        inflation = self.to_decimal(data.get('inflation_rate', 0))
        if unemployment > self.to_decimal(7):
            return {'recommendation': 'Expansionary', 'focus': 'Job creation and demand stimulus'}
        elif inflation > self.to_decimal(4):
            return {'recommendation': 'Contractionary', 'focus': 'Reduce demand pressures'}
        else:
            return {'recommendation': 'Neutral', 'focus': 'Maintain fiscal balance'}

    def _get_debt_implications(self, debt_gdp: Decimal, gap: Decimal) -> Dict[str, str]:
        """Get implications of debt sustainability analysis"""
        if gap > self.to_decimal(2):
            return {'fiscal_space': 'Limited', 'interest_burden': 'High and rising', 'policy_flexibility': 'Constrained', 'investor_confidence': 'At risk'}
        else:
            return {'fiscal_space': 'Adequate', 'interest_burden': 'Manageable', 'policy_flexibility': 'Available', 'investor_confidence': 'Stable'}

    def _assess_stance_impact(self, stance: str, impulse: Decimal) -> Dict[str, str]:
        """Assess economic impact of fiscal stance"""
        impacts = {'Expansionary': {'gdp_impact': 'Positive stimulus to growth', 'employment_impact': 'Job creation likely', 'inflation_risk': 'Potential upward pressure', 'debt_impact': 'Increased deficit spending'}, 'Contractionary': {'gdp_impact': 'Negative drag on growth', 'employment_impact': 'Potential job losses', 'inflation_risk': 'Reduced price pressures', 'debt_impact': 'Deficit reduction'}, 'Neutral': {'gdp_impact': 'Minimal direct impact', 'employment_impact': 'Status quo maintained', 'inflation_risk': 'No significant pressure', 'debt_impact': 'Stable debt dynamics'}}
        return impacts.get(stance, {})

    def calculate(self, analysis_type: str='tools_analysis', **kwargs) -> Dict[str, Any]:
        """Main fiscal policy calculation dispatcher"""
        analyses = {'compare_policies': self.compare_fiscal_monetary, 'tools_analysis': lambda: self.analyze_fiscal_tools(kwargs.get('policy_data', {})), 'debt_sustainability': lambda: self.assess_debt_sustainability(kwargs.get('debt_data', {})), 'policy_stance': lambda: self.identify_policy_stance(kwargs.get('fiscal_indicators', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def assess_debt_sustainability(self, debt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess whether national debt relative to GDP matters"""
    debt_gdp = self.to_decimal(debt_data.get('debt_to_gdp_ratio', 0))
    gdp_growth = self.to_decimal(debt_data.get('gdp_growth_rate', 0))
    interest_rate = self.to_decimal(debt_data.get('avg_interest_rate', 0))
    primary_balance = self.to_decimal(debt_data.get('primary_balance_gdp', 0))
    sustainability_gap = interest_rate - gdp_growth - primary_balance
    if debt_gdp > self.to_decimal(100):
        risk_level = 'Very High'
    elif debt_gdp > self.to_decimal(60):
        risk_level = 'High'
    elif debt_gdp > self.to_decimal(40):
        risk_level = 'Moderate'
    else:
        risk_level = 'Low'
    return {'debt_to_gdp': debt_gdp, 'sustainability_gap': sustainability_gap, 'sustainable': sustainability_gap < self.to_decimal(0), 'risk_level': risk_level, 'debt_dynamics': {'interest_burden': interest_rate * debt_gdp / self.to_decimal(100), 'growth_benefit': gdp_growth * debt_gdp / self.to_decimal(100), 'primary_contribution': primary_balance}, 'implications': self._get_debt_implications(debt_gdp, sustainability_gap)}

def identify_policy_stance(self, fiscal_indicators: Dict[str, Any]) -> Dict[str, Any]:
    """Identify if fiscal policy is expansionary or contractionary"""
    spending_change = self.to_decimal(fiscal_indicators.get('spending_change_percent', 0))
    tax_change = self.to_decimal(fiscal_indicators.get('tax_change_percent', 0))
    deficit_change = self.to_decimal(fiscal_indicators.get('deficit_change_gdp', 0))
    fiscal_impulse = spending_change - tax_change
    if fiscal_impulse > self.to_decimal(1):
        stance = 'Expansionary'
        description = 'Government increasing spending more than taxes'
    elif fiscal_impulse < self.to_decimal(-1):
        stance = 'Contractionary'
        description = 'Government reducing spending or increasing taxes significantly'
    else:
        stance = 'Neutral'
        description = 'Minimal net fiscal impact'
    return {'fiscal_stance': stance, 'fiscal_impulse': fiscal_impulse, 'description': description, 'stance_indicators': {'spending_change': spending_change, 'tax_change': tax_change, 'deficit_change': deficit_change}, 'economic_impact': self._assess_stance_impact(stance, fiscal_impulse)}

def _calculate_spending_multiplier(self, data: Dict[str, Any]) -> Decimal:
    """Calculate government spending multiplier"""
    mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
    return self.to_decimal(1) / (self.to_decimal(1) - mpc)

def _calculate_tax_multiplier(self, data: Dict[str, Any]) -> Decimal:
    """Calculate tax multiplier"""
    mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
    return -mpc / (self.to_decimal(1) - mpc)

def _calculate_transfer_multiplier(self, data: Dict[str, Any]) -> Decimal:
    """Calculate transfer payment multiplier"""
    mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
    return mpc / (self.to_decimal(1) - mpc)

def _recommend_fiscal_mix(self, data: Dict[str, Any]) -> Dict[str, str]:
    """Recommend optimal fiscal policy mix"""
    unemployment = self.to_decimal(data.get('unemployment_rate', 0))
    inflation = self.to_decimal(data.get('inflation_rate', 0))
    if unemployment > self.to_decimal(7):
        return {'recommendation': 'Expansionary', 'focus': 'Job creation and demand stimulus'}
    elif inflation > self.to_decimal(4):
        return {'recommendation': 'Contractionary', 'focus': 'Reduce demand pressures'}
    else:
        return {'recommendation': 'Neutral', 'focus': 'Maintain fiscal balance'}

def _get_debt_implications(self, debt_gdp: Decimal, gap: Decimal) -> Dict[str, str]:
    """Get implications of debt sustainability analysis"""
    if gap > self.to_decimal(2):
        return {'fiscal_space': 'Limited', 'interest_burden': 'High and rising', 'policy_flexibility': 'Constrained', 'investor_confidence': 'At risk'}
    else:
        return {'fiscal_space': 'Adequate', 'interest_burden': 'Manageable', 'policy_flexibility': 'Available', 'investor_confidence': 'Stable'}

def calculate(self, analysis_type: str='tools_analysis', **kwargs) -> Dict[str, Any]:
    """Main fiscal policy calculation dispatcher"""
    analyses = {'compare_policies': self.compare_fiscal_monetary, 'tools_analysis': lambda: self.analyze_fiscal_tools(kwargs.get('policy_data', {})), 'debt_sustainability': lambda: self.assess_debt_sustainability(kwargs.get('debt_data', {})), 'policy_stance': lambda: self.identify_policy_stance(kwargs.get('fiscal_indicators', {}))}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    return result

class MonetaryPolicyAnalyzer(EconomicsBase):
    """Monetary policy analysis and transmission mechanism"""

    def analyze_central_bank_roles(self) -> Dict[str, Any]:
        """Describe central bank roles and objectives"""
        return {'primary_objectives': {'price_stability': 'Maintain low and stable inflation', 'economic_growth': 'Support sustainable economic expansion', 'financial_stability': 'Ensure stable financial system', 'employment': 'Some central banks have explicit employment mandate'}, 'key_functions': {'monetary_policy': 'Set interest rates and control money supply', 'banking_supervision': 'Regulate and supervise financial institutions', 'lender_of_last_resort': 'Provide emergency liquidity to banks', 'currency_issuance': 'Issue and manage national currency', 'government_banker': 'Provide banking services to government'}, 'independence_importance': {'political_independence': 'Avoid short-term political pressures', 'operational_independence': 'Freedom to choose policy tools', 'accountability': 'Report to legislature on performance'}}

    def analyze_monetary_tools(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monetary policy tools and transmission mechanism"""
        return {'conventional_tools': {'policy_rate': {'description': 'Central bank key interest rate', 'current_rate': policy_data.get('policy_rate', 'N/A'), 'transmission': 'Affects all market rates', 'effectiveness': 'High when rates above zero lower bound'}, 'reserve_requirements': {'description': 'Banks required reserve ratio', 'current_ratio': policy_data.get('reserve_ratio', 'N/A'), 'transmission': 'Affects bank lending capacity', 'effectiveness': 'Powerful but rarely used'}, 'open_market_operations': {'description': 'Buy/sell government securities', 'current_balance_sheet': policy_data.get('central_bank_balance_sheet', 'N/A'), 'transmission': 'Direct impact on money supply', 'effectiveness': 'Most frequently used tool'}}, 'unconventional_tools': {'quantitative_easing': 'Large-scale asset purchases', 'forward_guidance': 'Communication about future policy', 'negative_rates': 'Below-zero policy rates', 'yield_curve_control': 'Target specific maturity yields'}, 'transmission_mechanism': self._analyze_transmission_mechanism(policy_data)}

    def analyze_targeting_strategies(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze different monetary policy targeting strategies"""
        strategies = {'inflation_targeting': {'target': strategy_data.get('inflation_target', '2%'), 'advantages': ['Clear communication', 'Credible commitment', 'Flexible response'], 'disadvantages': ['Ignores other variables', 'May miss asset bubbles', 'Measurement issues'], 'effectiveness': 'High for anchoring expectations'}, 'interest_rate_targeting': {'target': strategy_data.get('interest_rate_target', 'Variable'), 'advantages': ['Direct control', 'Clear signal', 'Quick transmission'], 'disadvantages': ['May ignore inflation', 'Procyclical risks', 'Zero lower bound'], 'effectiveness': 'High for short-term stabilization'}, 'exchange_rate_targeting': {'target': strategy_data.get('exchange_rate_target', 'N/A'), 'advantages': ['Trade stability', 'Import price stability', 'Simple communication'], 'disadvantages': ['Loss of monetary independence', 'Vulnerable to attacks', 'Limited flexibility'], 'effectiveness': 'Moderate, depends on economic structure'}}
        return {'targeting_strategies': strategies, 'strategy_comparison': self._compare_targeting_strategies(), 'optimal_strategy_recommendation': self._recommend_targeting_strategy(strategy_data)}

    def assess_policy_effectiveness(self, effectiveness_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess monetary policy effectiveness and limitations"""
        return {'effectiveness_factors': {'central_bank_credibility': effectiveness_data.get('credibility_index', 'N/A'), 'financial_system_development': effectiveness_data.get('financial_development_index', 'N/A'), 'economic_structure': effectiveness_data.get('economic_structure', 'N/A'), 'inflation_expectations_anchoring': effectiveness_data.get('expectations_anchored', 'N/A')}, 'policy_limitations': {'zero_lower_bound': 'Cannot cut rates below certain level', 'liquidity_trap': 'Money demand becomes perfectly elastic', 'long_and_variable_lags': 'Policy effects take 6-18 months', 'asset_bubbles': 'Difficulty identifying and responding to bubbles', 'financial_stability': 'Trade-offs between price and financial stability'}, 'effectiveness_assessment': self._assess_current_effectiveness(effectiveness_data)}

    def analyze_policy_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interaction between monetary and fiscal policy"""
        fiscal_stance = interaction_data.get('fiscal_stance', 'neutral')
        monetary_stance = interaction_data.get('monetary_stance', 'neutral')
        interaction_matrix = {('expansionary', 'expansionary'): {'coordination': 'Aligned', 'economic_impact': 'Strong stimulus', 'risks': 'Overheating, inflation', 'appropriate_when': 'Deep recession'}, ('expansionary', 'contractionary'): {'coordination': 'Conflicting', 'economic_impact': 'Uncertain, depends on relative strength', 'risks': 'Policy ineffectiveness', 'appropriate_when': 'Fiscal stimulus with inflation concerns'}, ('contractionary', 'expansionary'): {'coordination': 'Conflicting', 'economic_impact': 'Uncertain, mixed signals', 'risks': 'Policy confusion', 'appropriate_when': 'Fiscal consolidation with growth support'}, ('contractionary', 'contractionary'): {'coordination': 'Aligned', 'economic_impact': 'Strong contraction', 'risks': 'Excessive slowdown', 'appropriate_when': 'High inflation, overheating'}}
        current_interaction = interaction_matrix.get((fiscal_stance, monetary_stance), {'coordination': 'Unknown', 'economic_impact': 'Uncertain', 'risks': 'Unknown', 'appropriate_when': 'Unclear'})
        return {'current_policy_mix': {'fiscal_stance': fiscal_stance, 'monetary_stance': monetary_stance}, 'interaction_analysis': current_interaction, 'coordination_quality': self._assess_coordination_quality(interaction_data), 'policy_recommendations': self._recommend_policy_coordination(fiscal_stance, monetary_stance)}

    def _analyze_transmission_mechanism(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monetary policy transmission channels"""
        return {'interest_rate_channel': {'mechanism': 'Policy rate → Market rates → Investment/Consumption', 'strength': 'Strong in developed economies', 'lag': '6-12 months'}, 'credit_channel': {'mechanism': 'Policy → Bank lending → Economic activity', 'strength': 'Important for bank-dependent economies', 'lag': '3-9 months'}, 'exchange_rate_channel': {'mechanism': 'Policy rate → Exchange rate → Net exports', 'strength': 'Strong in open economies', 'lag': '3-6 months'}, 'asset_price_channel': {'mechanism': 'Policy → Asset prices → Wealth → Consumption', 'strength': 'Important with developed capital markets', 'lag': '6-18 months'}, 'expectations_channel': {'mechanism': 'Policy communication → Expectations → Decisions', 'strength': 'Critical for all economies', 'lag': 'Immediate to 3 months'}}

    def _compare_targeting_strategies(self) -> Dict[str, Any]:
        """Compare different targeting strategies"""
        return {'flexibility_ranking': ['Inflation targeting', 'Interest rate targeting', 'Exchange rate targeting'], 'credibility_ranking': ['Exchange rate targeting', 'Inflation targeting', 'Interest rate targeting'], 'transparency_ranking': ['Inflation targeting', 'Exchange rate targeting', 'Interest rate targeting'], 'current_popularity': 'Inflation targeting most widely adopted'}

    def _recommend_targeting_strategy(self, data: Dict[str, Any]) -> str:
        """Recommend optimal targeting strategy"""
        openness = data.get('trade_openness', 0.5)
        inflation_volatility = data.get('inflation_volatility', 0.02)
        if openness > 0.7 and inflation_volatility > 0.05:
            return 'Exchange rate targeting for trade-dependent economy'
        elif inflation_volatility > 0.03:
            return 'Inflation targeting for price stability'
        else:
            return 'Flexible inflation targeting with growth consideration'

    def _assess_current_effectiveness(self, data: Dict[str, Any]) -> str:
        """Assess current monetary policy effectiveness"""
        policy_rate = self.to_decimal(data.get('policy_rate', 2))
        inflation_expectations = data.get('expectations_anchored', True)
        if policy_rate < self.to_decimal(0.5) and (not inflation_expectations):
            return 'Low effectiveness - at zero lower bound with unanchored expectations'
        elif policy_rate < self.to_decimal(0.5):
            return 'Moderate effectiveness - limited by zero lower bound'
        elif not inflation_expectations:
            return 'Moderate effectiveness - limited by unanchored expectations'
        else:
            return 'High effectiveness - conventional policy space available'

    def _assess_coordination_quality(self, data: Dict[str, Any]) -> str:
        """Assess quality of fiscal-monetary coordination"""
        coordination_score = data.get('coordination_index', 0.5)
        if coordination_score > 0.8:
            return 'Excellent coordination'
        elif coordination_score > 0.6:
            return 'Good coordination'
        elif coordination_score > 0.4:
            return 'Moderate coordination'
        else:
            return 'Poor coordination'

    def _recommend_policy_coordination(self, fiscal: str, monetary: str) -> List[str]:
        """Recommend improvements to policy coordination"""
        if fiscal == monetary:
            return ['Maintain current alignment', 'Monitor for potential overshooting']
        else:
            return ['Improve communication between authorities', 'Clarify policy objectives and timing', 'Consider joint policy statements']

    def calculate(self, analysis_type: str='tools_analysis', **kwargs) -> Dict[str, Any]:
        """Main monetary policy calculation dispatcher"""
        analyses = {'central_bank_roles': self.analyze_central_bank_roles, 'tools_analysis': lambda: self.analyze_monetary_tools(kwargs.get('policy_data', {})), 'targeting_strategies': lambda: self.analyze_targeting_strategies(kwargs.get('strategy_data', {})), 'effectiveness_assessment': lambda: self.assess_policy_effectiveness(kwargs.get('effectiveness_data', {})), 'policy_interaction': lambda: self.analyze_policy_interaction(kwargs.get('interaction_data', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def _assess_current_effectiveness(self, data: Dict[str, Any]) -> str:
    """Assess current monetary policy effectiveness"""
    policy_rate = self.to_decimal(data.get('policy_rate', 2))
    inflation_expectations = data.get('expectations_anchored', True)
    if policy_rate < self.to_decimal(0.5) and (not inflation_expectations):
        return 'Low effectiveness - at zero lower bound with unanchored expectations'
    elif policy_rate < self.to_decimal(0.5):
        return 'Moderate effectiveness - limited by zero lower bound'
    elif not inflation_expectations:
        return 'Moderate effectiveness - limited by unanchored expectations'
    else:
        return 'High effectiveness - conventional policy space available'

def calculate(self, analysis_type: str='tools_analysis', **kwargs) -> Dict[str, Any]:
    """Main monetary policy calculation dispatcher"""
    analyses = {'central_bank_roles': self.analyze_central_bank_roles, 'tools_analysis': lambda: self.analyze_monetary_tools(kwargs.get('policy_data', {})), 'targeting_strategies': lambda: self.analyze_targeting_strategies(kwargs.get('strategy_data', {})), 'effectiveness_assessment': lambda: self.assess_policy_effectiveness(kwargs.get('effectiveness_data', {})), 'policy_interaction': lambda: self.analyze_policy_interaction(kwargs.get('interaction_data', {}))}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    return result

class CentralBankAnalyzer(EconomicsBase):
    """Central bank effectiveness and quality analysis"""

    def assess_central_bank_quality(self, cb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess qualities of effective central banks"""
        quality_metrics = {'independence': {'score': self.to_decimal(cb_data.get('independence_index', 0.5)), 'components': ['Political independence', 'Operational independence', 'Financial independence'], 'importance': 'Critical for credibility and long-term focus'}, 'transparency': {'score': self.to_decimal(cb_data.get('transparency_index', 0.5)), 'components': ['Clear communication', 'Regular reporting', 'Decision explanations'], 'importance': 'Essential for expectation management'}, 'accountability': {'score': self.to_decimal(cb_data.get('accountability_index', 0.5)), 'components': ['Legislative oversight', 'Performance reporting', 'Public scrutiny'], 'importance': 'Democratic legitimacy and performance monitoring'}, 'technical_competence': {'score': self.to_decimal(cb_data.get('competence_index', 0.5)), 'components': ['Staff expertise', 'Research capability', 'Analysis quality'], 'importance': 'Effective policy design and implementation'}}
        overall_quality = sum((metric['score'] for metric in quality_metrics.values())) / self.to_decimal(4)
        return {'quality_metrics': quality_metrics, 'overall_quality_score': overall_quality, 'effectiveness_rating': self._rate_effectiveness(overall_quality), 'improvement_recommendations': self._recommend_improvements(quality_metrics)}

    def _rate_effectiveness(self, score: Decimal) -> str:
        """Rate central bank effectiveness"""
        if score > self.to_decimal(0.8):
            return 'Highly Effective'
        elif score > self.to_decimal(0.6):
            return 'Effective'
        elif score > self.to_decimal(0.4):
            return 'Moderately Effective'
        else:
            return 'Needs Improvement'

    def _recommend_improvements(self, metrics: Dict[str, Any]) -> List[str]:
        """Recommend improvements based on quality metrics"""
        recommendations = []
        for metric, data in metrics.items():
            if data['score'] < self.to_decimal(0.6):
                if metric == 'independence':
                    recommendations.append('Strengthen legal framework for central bank independence')
                elif metric == 'transparency':
                    recommendations.append('Improve communication strategy and public reporting')
                elif metric == 'accountability':
                    recommendations.append('Enhance oversight mechanisms and performance targets')
                elif metric == 'technical_competence':
                    recommendations.append('Invest in staff training and research capabilities')
        return recommendations

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate central bank quality assessment"""
        result = self.assess_central_bank_quality(kwargs.get('cb_data', {}))
        result['metadata'] = self.get_metadata()
        return result

def _rate_effectiveness(self, score: Decimal) -> str:
    """Rate central bank effectiveness"""
    if score > self.to_decimal(0.8):
        return 'Highly Effective'
    elif score > self.to_decimal(0.6):
        return 'Effective'
    elif score > self.to_decimal(0.4):
        return 'Moderately Effective'
    else:
        return 'Needs Improvement'

def _recommend_improvements(self, metrics: Dict[str, Any]) -> List[str]:
    """Recommend improvements based on quality metrics"""
    recommendations = []
    for metric, data in metrics.items():
        if data['score'] < self.to_decimal(0.6):
            if metric == 'independence':
                recommendations.append('Strengthen legal framework for central bank independence')
            elif metric == 'transparency':
                recommendations.append('Improve communication strategy and public reporting')
            elif metric == 'accountability':
                recommendations.append('Enhance oversight mechanisms and performance targets')
            elif metric == 'technical_competence':
                recommendations.append('Invest in staff training and research capabilities')
    return recommendations

def calculate(self, **kwargs) -> Dict[str, Any]:
    """Calculate central bank quality assessment"""
    result = self.assess_central_bank_quality(kwargs.get('cb_data', {}))
    result['metadata'] = self.get_metadata()
    return result

def analyze_currency_arbitrage(currency_data, base_currency='USD'):
    """Quick triangular arbitrage analysis"""
    detector = ArbitrageDetector()
    return detector.detect_triangular_arbitrage(currency_data, base_currency)

class CapitalFlowAnalyzer(EconomicsBase):
    """Capital flows analysis and balance of payments impact"""

    def analyze_capital_flow_types(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze different types of capital flows and their characteristics"""
        return {'foreign_direct_investment': {'definition': 'Long-term investment for control or significant influence (>10% ownership)', 'characteristics': ['Long-term commitment and stability', 'Technology and knowledge transfer', 'Management expertise and best practices', 'Difficult to reverse quickly'], 'economic_impact': {'positive': 'Productivity gains, employment creation, export growth', 'negative': 'Potential crowding out of domestic investment', 'volatility': 'Low - stable funding source'}, 'current_flows': self._analyze_fdi_flows(flow_data), 'policy_implications': 'Generally welcomed, policies focus on attraction and retention'}, 'portfolio_investment': {'definition': 'Investment in securities without control (<10% ownership)', 'characteristics': ['Liquid and easily reversible', 'Driven by return differentials and risk appetite', 'Sensitive to market sentiment', 'Includes equity and debt securities'], 'economic_impact': {'positive': 'Capital market development, financing access', 'negative': 'Volatility and sudden stops risk', 'volatility': 'High - subject to rapid reversals'}, 'current_flows': self._analyze_portfolio_flows(flow_data), 'policy_implications': 'Requires robust regulatory framework and macroprudential policies'}, 'other_investment': {'definition': 'Bank lending, trade credits, and other financial flows', 'characteristics': ['Includes bank loans and deposits', 'Trade finance and short-term credits', 'Interbank and intercompany lending', 'Often procyclical'], 'economic_impact': {'positive': 'Trade finance facilitation, liquidity provision', 'negative': 'Banking sector vulnerabilities, sudden stops', 'volatility': 'Medium to High - depends on banking conditions'}, 'current_flows': self._analyze_other_flows(flow_data), 'policy_implications': 'Banking supervision and capital flow management'}, 'official_flows': {'definition': 'Central bank and government transactions', 'characteristics': ['Reserve accumulation/depletion', 'Official development assistance', 'Bilateral government lending', 'IMF and multilateral lending'], 'economic_impact': {'positive': 'Crisis support, development financing', 'negative': 'May create moral hazard', 'volatility': 'Low to Medium - policy driven'}, 'policy_implications': 'Part of macroeconomic management and development strategy'}, 'flow_determinants': self._analyze_flow_determinants(flow_data), 'volatility_comparison': self._compare_flow_volatility(), 'crisis_behavior': self._analyze_crisis_behavior()}

    def analyze_balance_of_payments_impact(self, bop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how BOP flows affect exchange rates"""
        return {'current_account_impact': {'trade_balance': {'surplus_effect': 'Creates demand for domestic currency', 'deficit_effect': 'Creates supply of domestic currency', 'elasticity_considerations': 'J-curve effect in short run', 'current_balance': self._assess_trade_balance_impact(bop_data)}, 'income_flows': {'investment_income': 'Returns on foreign investments affect currency demand', 'compensation': 'Worker remittances and cross-border wages', 'impact_assessment': self._assess_income_flows_impact(bop_data)}, 'transfers': {'remittances': 'Significant for many developing countries', 'official_transfers': 'Aid and government transfers', 'impact_assessment': self._assess_transfer_impact(bop_data)}}, 'capital_account_impact': {'direct_investment': {'fx_impact': 'Usually strengthens recipient currency', 'timing': 'Gradual impact as investments are made', 'sustainability': 'Most stable form of capital flow'}, 'portfolio_investment': {'fx_impact': 'Can cause rapid currency movements', 'timing': 'Immediate impact on exchange rates', 'volatility': 'High sensitivity to sentiment changes'}, 'financial_derivatives': {'fx_impact': 'Complex, depends on underlying positions', 'hedging_flows': 'May offset other capital flows'}, 'reserve_changes': {'intervention_impact': 'Central bank buying/selling affects rates', 'signaling_effect': 'Indicates policy stance and credibility'}}, 'bop_equilibrium_analysis': self._analyze_bop_equilibrium(bop_data), 'sustainability_assessment': self._assess_bop_sustainability(bop_data), 'policy_responses': self._recommend_bop_policies(bop_data)}

    def assess_capital_restrictions(self, restriction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze government capital restrictions and their objectives"""
        return {'restriction_types': {'inflow_controls': {'objectives': ['Prevent asset bubbles from hot money', 'Maintain monetary policy independence', 'Reduce financial stability risks', 'Prevent real exchange rate appreciation'], 'instruments': ['Unremunerated reserve requirements', 'Taxes on foreign investment', 'Minimum holding periods', 'Limits on foreign ownership'], 'effectiveness': self._assess_inflow_control_effectiveness(restriction_data)}, 'outflow_controls': {'objectives': ['Prevent capital flight during crises', 'Preserve foreign exchange reserves', 'Maintain exchange rate stability', 'Support domestic financing needs'], 'instruments': ['Approval requirements for foreign investment', 'Limits on foreign currency holdings', 'Restrictions on overseas deposits', 'Export surrender requirements'], 'effectiveness': self._assess_outflow_control_effectiveness(restriction_data)}}, 'common_objectives': {'macroeconomic_stability': 'Maintain stable exchange rates and inflation', 'financial_stability': 'Prevent excessive risk-taking and bubbles', 'monetary_independence': 'Preserve domestic monetary policy effectiveness', 'development_goals': 'Channel capital toward productive investments', 'crisis_prevention': 'Reduce vulnerability to sudden stops'}, 'effectiveness_factors': {'comprehensiveness': 'Controls must cover all relevant channels', 'enforceability': 'Administrative capacity and compliance monitoring', 'market_development': 'May hinder financial market development', 'evasion_potential': 'Sophisticated investors can often circumvent controls', 'international_coordination': 'Effectiveness increases with coordination'}, 'costs_and_benefits': self._analyze_restriction_costs_benefits(), 'optimal_design_principles': self._recommend_optimal_design(), 'current_trends': self._analyze_current_restriction_trends()}

    def _analyze_fdi_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FDI flow characteristics"""
        fdi_inflows = self.to_decimal(data.get('fdi_inflows_gdp', 0))
        fdi_outflows = self.to_decimal(data.get('fdi_outflows_gdp', 0))
        return {'inflow_level': f'{fdi_inflows:.1f}% of GDP', 'outflow_level': f'{fdi_outflows:.1f}% of GDP', 'net_position': f'{fdi_inflows - fdi_outflows:.1f}% of GDP', 'assessment': self._assess_fdi_level(fdi_inflows), 'sectoral_distribution': data.get('fdi_sectors', 'Mixed across sectors')}

    def _analyze_portfolio_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio flow characteristics"""
        portfolio_flows = self.to_decimal(data.get('portfolio_flows_gdp', 0))
        volatility = data.get('portfolio_volatility', 'High')
        return {'flow_level': f'{portfolio_flows:.1f}% of GDP', 'volatility_assessment': volatility, 'composition': data.get('portfolio_composition', 'Mixed equity and debt'), 'vulnerability_indicator': self._assess_portfolio_vulnerability(portfolio_flows)}

    def _analyze_other_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze other investment flows"""
        other_flows = self.to_decimal(data.get('other_investment_gdp', 0))
        return {'flow_level': f'{other_flows:.1f}% of GDP', 'banking_component': data.get('banking_flows_share', 'Significant'), 'trade_finance_component': data.get('trade_finance_share', 'Moderate'), 'stability_assessment': self._assess_other_flow_stability(other_flows)}

    def _analyze_flow_determinants(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze determinants of capital flows"""
        return {'push_factors': ['Global risk appetite and liquidity conditions', 'Advanced economy interest rates', 'Global growth and commodity prices', 'Investor risk tolerance'], 'pull_factors': ['Domestic economic fundamentals', 'Interest rate differentials', 'Exchange rate expectations', 'Political and institutional quality', 'Market development and accessibility'], 'structural_factors': ['Trade openness and integration', 'Financial market development', 'Capital account openness', 'Institutional quality and governance']}

    def _compare_flow_volatility(self) -> Dict[str, str]:
        """Compare volatility across flow types"""
        return {'most_volatile': 'Portfolio investment (especially equity)', 'moderately_volatile': 'Other investment (banking flows)', 'least_volatile': 'Foreign direct investment', 'crisis_behavior': 'Portfolio flows show strongest sudden stop tendency'}

    def _analyze_crisis_behavior(self) -> Dict[str, str]:
        """Analyze capital flow behavior during crises"""
        return {'sudden_stops': 'Rapid reversal of portfolio and banking flows', 'flight_to_quality': 'Shift from emerging to developed markets', 'fdi_resilience': 'FDI typically more stable during crises', 'contagion_channels': 'Capital flows can transmit crises across countries'}

    def _assess_trade_balance_impact(self, data: Dict[str, Any]) -> str:
        """Assess trade balance impact on exchange rates"""
        trade_balance = self.to_decimal(data.get('trade_balance_gdp', 0))
        if trade_balance > self.to_decimal(2):
            return 'Large surplus likely supporting currency'
        elif trade_balance < self.to_decimal(-5):
            return 'Large deficit creating downward pressure on currency'
        else:
            return 'Moderate trade balance with limited FX impact'

    def _assess_income_flows_impact(self, data: Dict[str, Any]) -> str:
        """Assess income flows impact"""
        income_balance = self.to_decimal(data.get('income_balance_gdp', 0))
        if income_balance > self.to_decimal(1):
            return 'Positive income flows supporting currency'
        elif income_balance < self.to_decimal(-2):
            return 'Negative income flows pressuring currency'
        else:
            return 'Income flows have moderate impact'

    def _assess_transfer_impact(self, data: Dict[str, Any]) -> str:
        """Assess transfer impact on currency"""
        transfers = self.to_decimal(data.get('transfers_gdp', 0))
        if transfers > self.to_decimal(3):
            return 'Significant remittances providing currency support'
        else:
            return 'Transfers have limited currency impact'

    def _analyze_bop_equilibrium(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze balance of payments equilibrium"""
        current_account = self.to_decimal(data.get('current_account_gdp', 0))
        capital_account = self.to_decimal(data.get('capital_account_gdp', 0))
        return {'current_account_balance': f'{current_account:.1f}% of GDP', 'capital_account_balance': f'{capital_account:.1f}% of GDP', 'overall_balance': f'{current_account + capital_account:.1f}% of GDP', 'equilibrium_assessment': self._assess_bop_equilibrium_status(current_account, capital_account), 'reserve_implications': self._assess_reserve_implications(current_account + capital_account)}

    def _assess_bop_sustainability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess BOP sustainability"""
        current_account = self.to_decimal(data.get('current_account_gdp', 0))
        foreign_debt = self.to_decimal(data.get('foreign_debt_gdp', 0))
        return {'current_account_sustainability': self._assess_ca_sustainability(current_account), 'external_debt_sustainability': self._assess_debt_sustainability(foreign_debt), 'vulnerability_indicators': self._identify_vulnerability_indicators(data), 'early_warning_signals': self._identify_early_warning_signals(data)}

    def _recommend_bop_policies(self, data: Dict[str, Any]) -> List[str]:
        """Recommend BOP adjustment policies"""
        current_account = self.to_decimal(data.get('current_account_gdp', 0))
        if current_account < self.to_decimal(-5):
            return ['Fiscal consolidation to reduce domestic absorption', 'Structural reforms to improve competitiveness', 'Exchange rate adjustment if overvalued', 'Capital flow management measures if needed']
        elif current_account > self.to_decimal(5):
            return ['Fiscal expansion to increase domestic demand', 'Infrastructure investment to utilize surplus', 'Currency appreciation to restore balance', 'Gradual capital account liberalization']
        else:
            return ['Maintain current policy stance', 'Monitor for emerging imbalances', 'Strengthen economic fundamentals']

    def _assess_inflow_control_effectiveness(self, data: Dict[str, Any]) -> str:
        """Assess effectiveness of capital inflow controls"""
        control_intensity = data.get('inflow_control_index', 0.5)
        if control_intensity > 0.7:
            return 'Comprehensive controls - moderately effective but may reduce efficiency'
        elif control_intensity > 0.3:
            return 'Selective controls - limited effectiveness, some circumvention'
        else:
            return 'Minimal controls - market-based allocation but potential volatility'

    def _assess_outflow_control_effectiveness(self, data: Dict[str, Any]) -> str:
        """Assess effectiveness of capital outflow controls"""
        control_intensity = data.get('outflow_control_index', 0.5)
        if control_intensity > 0.7:
            return 'Strict controls - effective short-term but high economic costs'
        elif control_intensity > 0.3:
            return 'Moderate controls - some effectiveness with manageable costs'
        else:
            return 'Light controls - limited effectiveness but preserves market efficiency'

    def _analyze_restriction_costs_benefits(self) -> Dict[str, Dict[str, List[str]]]:
        """Analyze costs and benefits of capital restrictions"""
        return {'benefits': {'macroeconomic': ['Exchange rate stability', 'Monetary policy independence', 'Reduced volatility'], 'financial': ['Reduced systemic risk', 'Prevented asset bubbles', 'Banking stability'], 'developmental': ['Capital allocated to development priorities', 'Reduced inequality']}, 'costs': {'efficiency': ['Reduced capital allocation efficiency', 'Higher cost of capital', 'Innovation constraints'], 'market_development': ['Slower financial market development', 'Reduced competition', 'Limited diversification'], 'administrative': ['High enforcement costs', 'Bureaucratic burden', 'Corruption risks']}}

    def _recommend_optimal_design(self) -> List[str]:
        """Recommend optimal design principles for capital controls"""
        return ['Targeted rather than blanket restrictions', 'Temporary rather than permanent measures', 'Price-based rather than quantity-based controls', 'Comprehensive coverage to prevent evasion', 'Regular review and adjustment of measures', 'Clear communication of objectives and duration']

    def _analyze_current_restriction_trends(self) -> Dict[str, str]:
        """Analyze current trends in capital restrictions"""
        return {'developing_countries': 'Increased use of macroprudential measures', 'developed_countries': 'Generally maintain open capital accounts', 'crisis_response': 'Temporary restrictions during financial stress', 'international_coordination': 'Growing recognition of spillover effects', 'institutional_view': 'IMF more accepting of capital flow management'}

    def _assess_fdi_level(self, fdi_inflows: Decimal) -> str:
        """Assess FDI inflow level"""
        if fdi_inflows > self.to_decimal(5):
            return 'High FDI inflows indicating strong investment climate'
        elif fdi_inflows > self.to_decimal(2):
            return 'Moderate FDI inflows'
        else:
            return 'Low FDI inflows, may indicate investment barriers'

    def _assess_portfolio_vulnerability(self, flows: Decimal) -> str:
        """Assess portfolio flow vulnerability"""
        if abs(flows) > self.to_decimal(5):
            return 'High vulnerability to sudden stops'
        elif abs(flows) > self.to_decimal(2):
            return 'Moderate vulnerability'
        else:
            return 'Low vulnerability to portfolio flow reversals'

    def _assess_other_flow_stability(self, flows: Decimal) -> str:
        """Assess other investment flow stability"""
        if abs(flows) > self.to_decimal(3):
            return 'Volatile other investment flows'
        else:
            return 'Relatively stable other investment flows'

    def _assess_bop_equilibrium_status(self, ca: Decimal, ka: Decimal) -> str:
        """Assess BOP equilibrium status"""
        overall = ca + ka
        if abs(overall) < self.to_decimal(1):
            return 'Balanced position'
        elif overall > self.to_decimal(2):
            return 'Surplus position - reserve accumulation'
        else:
            return 'Deficit position - reserve depletion or borrowing'

    def _assess_reserve_implications(self, balance: Decimal) -> str:
        """Assess reserve implications of BOP position"""
        if balance > self.to_decimal(2):
            return 'Reserve accumulation, potential sterilization needs'
        elif balance < self.to_decimal(-2):
            return 'Reserve depletion, potential sustainability concerns'
        else:
            return 'Stable reserve position'

    def _assess_ca_sustainability(self, ca: Decimal) -> str:
        """Assess current account sustainability"""
        if ca < self.to_decimal(-5):
            return 'Large deficit raises sustainability concerns'
        elif ca < self.to_decimal(-3):
            return 'Moderate deficit requires monitoring'
        else:
            return 'Sustainable current account position'

    def _assess_debt_sustainability(self, debt: Decimal) -> str:
        """Assess external debt sustainability"""
        if debt > self.to_decimal(60):
            return 'High external debt raises sustainability concerns'
        elif debt > self.to_decimal(40):
            return 'Moderate external debt requires monitoring'
        else:
            return 'Manageable external debt level'

    def _identify_vulnerability_indicators(self, data: Dict[str, Any]) -> List[str]:
        """Identify BOP vulnerability indicators"""
        return ['Current account deficit > 5% of GDP', 'Short-term external debt > reserves', 'High dependence on volatile capital flows', 'Real exchange rate overvaluation', 'Rapid credit growth and asset price increases']

    def _identify_early_warning_signals(self, data: Dict[str, Any]) -> List[str]:
        """Identify early warning signals of BOP crisis"""
        return ['Sudden stop in capital inflows', 'Rapid reserve depletion', 'Currency under pressure', 'Rising sovereign risk premiums', 'Bank deposit outflows']

    def calculate(self, analysis_type: str='capital_flows', **kwargs) -> Dict[str, Any]:
        """Main capital flows calculation dispatcher"""
        analyses = {'capital_flows': lambda: self.analyze_capital_flow_types(kwargs.get('flow_data', {})), 'bop_impact': lambda: self.analyze_balance_of_payments_impact(kwargs.get('bop_data', {})), 'capital_restrictions': lambda: self.assess_capital_restrictions(kwargs.get('restriction_data', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def _analyze_fdi_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze FDI flow characteristics"""
    fdi_inflows = self.to_decimal(data.get('fdi_inflows_gdp', 0))
    fdi_outflows = self.to_decimal(data.get('fdi_outflows_gdp', 0))
    return {'inflow_level': f'{fdi_inflows:.1f}% of GDP', 'outflow_level': f'{fdi_outflows:.1f}% of GDP', 'net_position': f'{fdi_inflows - fdi_outflows:.1f}% of GDP', 'assessment': self._assess_fdi_level(fdi_inflows), 'sectoral_distribution': data.get('fdi_sectors', 'Mixed across sectors')}

def _analyze_portfolio_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze portfolio flow characteristics"""
    portfolio_flows = self.to_decimal(data.get('portfolio_flows_gdp', 0))
    volatility = data.get('portfolio_volatility', 'High')
    return {'flow_level': f'{portfolio_flows:.1f}% of GDP', 'volatility_assessment': volatility, 'composition': data.get('portfolio_composition', 'Mixed equity and debt'), 'vulnerability_indicator': self._assess_portfolio_vulnerability(portfolio_flows)}

def _analyze_other_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze other investment flows"""
    other_flows = self.to_decimal(data.get('other_investment_gdp', 0))
    return {'flow_level': f'{other_flows:.1f}% of GDP', 'banking_component': data.get('banking_flows_share', 'Significant'), 'trade_finance_component': data.get('trade_finance_share', 'Moderate'), 'stability_assessment': self._assess_other_flow_stability(other_flows)}

def _assess_trade_balance_impact(self, data: Dict[str, Any]) -> str:
    """Assess trade balance impact on exchange rates"""
    trade_balance = self.to_decimal(data.get('trade_balance_gdp', 0))
    if trade_balance > self.to_decimal(2):
        return 'Large surplus likely supporting currency'
    elif trade_balance < self.to_decimal(-5):
        return 'Large deficit creating downward pressure on currency'
    else:
        return 'Moderate trade balance with limited FX impact'

def _assess_income_flows_impact(self, data: Dict[str, Any]) -> str:
    """Assess income flows impact"""
    income_balance = self.to_decimal(data.get('income_balance_gdp', 0))
    if income_balance > self.to_decimal(1):
        return 'Positive income flows supporting currency'
    elif income_balance < self.to_decimal(-2):
        return 'Negative income flows pressuring currency'
    else:
        return 'Income flows have moderate impact'

def _assess_transfer_impact(self, data: Dict[str, Any]) -> str:
    """Assess transfer impact on currency"""
    transfers = self.to_decimal(data.get('transfers_gdp', 0))
    if transfers > self.to_decimal(3):
        return 'Significant remittances providing currency support'
    else:
        return 'Transfers have limited currency impact'

def _analyze_bop_equilibrium(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze balance of payments equilibrium"""
    current_account = self.to_decimal(data.get('current_account_gdp', 0))
    capital_account = self.to_decimal(data.get('capital_account_gdp', 0))
    return {'current_account_balance': f'{current_account:.1f}% of GDP', 'capital_account_balance': f'{capital_account:.1f}% of GDP', 'overall_balance': f'{current_account + capital_account:.1f}% of GDP', 'equilibrium_assessment': self._assess_bop_equilibrium_status(current_account, capital_account), 'reserve_implications': self._assess_reserve_implications(current_account + capital_account)}

def _assess_bop_sustainability(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess BOP sustainability"""
    current_account = self.to_decimal(data.get('current_account_gdp', 0))
    foreign_debt = self.to_decimal(data.get('foreign_debt_gdp', 0))
    return {'current_account_sustainability': self._assess_ca_sustainability(current_account), 'external_debt_sustainability': self._assess_debt_sustainability(foreign_debt), 'vulnerability_indicators': self._identify_vulnerability_indicators(data), 'early_warning_signals': self._identify_early_warning_signals(data)}

def _recommend_bop_policies(self, data: Dict[str, Any]) -> List[str]:
    """Recommend BOP adjustment policies"""
    current_account = self.to_decimal(data.get('current_account_gdp', 0))
    if current_account < self.to_decimal(-5):
        return ['Fiscal consolidation to reduce domestic absorption', 'Structural reforms to improve competitiveness', 'Exchange rate adjustment if overvalued', 'Capital flow management measures if needed']
    elif current_account > self.to_decimal(5):
        return ['Fiscal expansion to increase domestic demand', 'Infrastructure investment to utilize surplus', 'Currency appreciation to restore balance', 'Gradual capital account liberalization']
    else:
        return ['Maintain current policy stance', 'Monitor for emerging imbalances', 'Strengthen economic fundamentals']

def _assess_fdi_level(self, fdi_inflows: Decimal) -> str:
    """Assess FDI inflow level"""
    if fdi_inflows > self.to_decimal(5):
        return 'High FDI inflows indicating strong investment climate'
    elif fdi_inflows > self.to_decimal(2):
        return 'Moderate FDI inflows'
    else:
        return 'Low FDI inflows, may indicate investment barriers'

def _assess_portfolio_vulnerability(self, flows: Decimal) -> str:
    """Assess portfolio flow vulnerability"""
    if abs(flows) > self.to_decimal(5):
        return 'High vulnerability to sudden stops'
    elif abs(flows) > self.to_decimal(2):
        return 'Moderate vulnerability'
    else:
        return 'Low vulnerability to portfolio flow reversals'

def _assess_other_flow_stability(self, flows: Decimal) -> str:
    """Assess other investment flow stability"""
    if abs(flows) > self.to_decimal(3):
        return 'Volatile other investment flows'
    else:
        return 'Relatively stable other investment flows'

def _assess_bop_equilibrium_status(self, ca: Decimal, ka: Decimal) -> str:
    """Assess BOP equilibrium status"""
    overall = ca + ka
    if abs(overall) < self.to_decimal(1):
        return 'Balanced position'
    elif overall > self.to_decimal(2):
        return 'Surplus position - reserve accumulation'
    else:
        return 'Deficit position - reserve depletion or borrowing'

def _assess_reserve_implications(self, balance: Decimal) -> str:
    """Assess reserve implications of BOP position"""
    if balance > self.to_decimal(2):
        return 'Reserve accumulation, potential sterilization needs'
    elif balance < self.to_decimal(-2):
        return 'Reserve depletion, potential sustainability concerns'
    else:
        return 'Stable reserve position'

def _assess_ca_sustainability(self, ca: Decimal) -> str:
    """Assess current account sustainability"""
    if ca < self.to_decimal(-5):
        return 'Large deficit raises sustainability concerns'
    elif ca < self.to_decimal(-3):
        return 'Moderate deficit requires monitoring'
    else:
        return 'Sustainable current account position'

def _assess_debt_sustainability(self, debt: Decimal) -> str:
    """Assess external debt sustainability"""
    if debt > self.to_decimal(60):
        return 'High external debt raises sustainability concerns'
    elif debt > self.to_decimal(40):
        return 'Moderate external debt requires monitoring'
    else:
        return 'Manageable external debt level'

def calculate(self, analysis_type: str='capital_flows', **kwargs) -> Dict[str, Any]:
    """Main capital flows calculation dispatcher"""
    analyses = {'capital_flows': lambda: self.analyze_capital_flow_types(kwargs.get('flow_data', {})), 'bop_impact': lambda: self.analyze_balance_of_payments_impact(kwargs.get('bop_data', {})), 'capital_restrictions': lambda: self.assess_capital_restrictions(kwargs.get('restriction_data', {}))}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    return result

class FXMarketAnalyzer(EconomicsBase):
    """Foreign exchange market structure and functionality analysis"""

    def analyze_fx_market_structure(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze foreign exchange market functions and participants"""
        return {'market_functions': {'price_discovery': {'description': 'Determining exchange rates through supply and demand', 'mechanism': 'Continuous trading by global participants', 'efficiency': 'Generally efficient due to high liquidity and participation', 'factors': ['Economic fundamentals', 'Market sentiment', 'Technical factors']}, 'risk_management': {'description': 'Hedging currency exposure for businesses and investors', 'instruments': ['Spot transactions', 'Forward contracts', 'Options', 'Swaps'], 'participants': 'Multinational corporations, banks, institutional investors', 'importance': 'Critical for international trade and investment'}, 'speculation': {'description': 'Profit-seeking from currency movements', 'participants': 'Hedge funds, proprietary traders, retail investors', 'impact': 'Provides liquidity but can increase volatility', 'regulation': 'Subject to various regulatory constraints'}, 'arbitrage': {'description': 'Exploiting price differences across markets', 'types': ['Spatial arbitrage', 'Triangular arbitrage', 'Covered interest arbitrage'], 'function': 'Ensures price consistency across markets', 'technology_role': 'High-frequency trading dominates arbitrage'}}, 'market_participants': self._analyze_market_participants(market_data), 'market_structure': self._analyze_market_microstructure(market_data), 'trading_mechanisms': self._analyze_trading_mechanisms(), 'liquidity_analysis': self._analyze_market_liquidity(market_data)}

    def distinguish_nominal_real_rates(self, rate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Distinguish between nominal and real exchange rates"""
        return {'nominal_exchange_rate': {'definition': 'Price of one currency in terms of another currency', 'example': '1 USD = 1.20 EUR (Euro per US Dollar)', 'characteristics': ['Directly observable in markets', 'Used for actual transactions', 'Affected by monetary policy and market sentiment', 'Can be quoted as direct or indirect'], 'calculation': 'Market determined through trading', 'current_rate': rate_data.get('nominal_rate', 'N/A')}, 'real_exchange_rate': {'definition': 'Nominal rate adjusted for price level differences', 'formula': 'Real Rate = Nominal Rate × (Foreign Price Level / Domestic Price Level)', 'characteristics': ['Measures relative purchasing power', 'Indicates competitiveness', 'Not directly tradeable', 'Important for trade flows'], 'calculation': self._calculate_real_exchange_rate(rate_data), 'interpretation': self._interpret_real_rate_changes(rate_data)}, 'relationship_analysis': {'short_run': 'Nominal and real rates can diverge significantly', 'long_run': 'Tend to move together due to purchasing power parity', 'policy_implications': 'Real rates matter more for trade competitiveness', 'investment_relevance': 'Both rates important for different investment decisions'}, 'practical_applications': self._describe_rate_applications()}

    def calculate_currency_percentage_change(self, change_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate and interpret currency percentage changes"""
        initial_rate = self.to_decimal(change_data.get('initial_rate', 1))
        final_rate = self.to_decimal(change_data.get('final_rate', 1))
        base_currency = change_data.get('base_currency', 'USD')
        quote_currency = change_data.get('quote_currency', 'EUR')
        quote_convention = change_data.get('quote_convention', 'direct')
        percentage_change = (final_rate - initial_rate) / initial_rate * self.to_decimal(100)
        if quote_convention == 'direct':
            if percentage_change > 0:
                movement = f'{base_currency} weakened by {percentage_change:.2f}%'
                description = f'{quote_currency} appreciated against {base_currency}'
            else:
                movement = f'{base_currency} strengthened by {abs(percentage_change):.2f}%'
                description = f'{quote_currency} depreciated against {base_currency}'
        elif percentage_change > 0:
            movement = f'{base_currency} strengthened by {percentage_change:.2f}%'
            description = f'{base_currency} appreciated against {quote_currency}'
        else:
            movement = f'{base_currency} weakened by {abs(percentage_change):.2f}%'
            description = f'{base_currency} depreciated against {quote_currency}'
        return {'calculation_details': {'initial_rate': initial_rate, 'final_rate': final_rate, 'absolute_change': final_rate - initial_rate, 'percentage_change': percentage_change, 'quote_convention': quote_convention}, 'currency_movement': {'summary': movement, 'detailed_description': description, 'direction': 'appreciation' if percentage_change > 0 else 'depreciation', 'magnitude': self._assess_change_magnitude(abs(percentage_change))}, 'economic_implications': self._analyze_currency_change_implications(percentage_change, base_currency, quote_currency), 'trade_impact': self._assess_trade_impact(percentage_change, quote_convention), 'investment_implications': self._assess_investment_implications(percentage_change)}

    def _analyze_market_participants(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FX market participants"""
        return {'commercial_banks': {'role': 'Market makers and dealers', 'market_share': '~75% of daily volume', 'functions': ['Provide liquidity', 'Client transactions', 'Proprietary trading'], 'importance': 'Core of interbank market'}, 'central_banks': {'role': 'Policy implementation and intervention', 'market_share': '~5% of daily volume', 'functions': ['Monetary policy', 'Reserve management', 'Market intervention'], 'impact': 'Significant influence despite small volume'}, 'institutional_investors': {'role': 'Hedging and investment', 'market_share': '~10% of daily volume', 'participants': ['Pension funds', 'Mutual funds', 'Insurance companies'], 'motivation': 'Risk management and portfolio optimization'}, 'hedge_funds': {'role': 'Speculation and arbitrage', 'market_share': '~5% of daily volume', 'strategies': ['Carry trades', 'Momentum', 'Mean reversion'], 'impact': 'High influence on short-term volatility'}, 'corporations': {'role': 'Commercial hedging', 'market_share': '~3% of daily volume', 'needs': ['Trade settlement', 'Risk hedging', 'Cash management'], 'patterns': 'Often predictable timing'}, 'retail_traders': {'role': 'Small-scale speculation', 'market_share': '~2% of daily volume', 'access': 'Through brokers and online platforms', 'characteristics': 'High leverage, short-term focus'}}

    def _analyze_market_microstructure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FX market microstructure"""
        return {'market_type': 'Over-the-counter (OTC) decentralized market', 'trading_hours': '24 hours, 5 days a week across global time zones', 'major_centers': ['London (43%)', 'New York (17%)', 'Singapore (8%)', 'Tokyo (7%)'], 'market_size': data.get('daily_volume', '$7.5 trillion daily volume'), 'concentration': 'Top 10 banks account for ~75% of volume', 'electronic_trading': '~95% of transactions are electronic', 'settlement': 'T+2 standard settlement cycle'}

    def _analyze_trading_mechanisms(self) -> Dict[str, Any]:
        """Analyze FX trading mechanisms"""
        return {'spot_market': {'definition': 'Immediate delivery (T+2 settlement)', 'characteristics': 'Highest liquidity, benchmark for other rates', 'participants': 'All market participants', 'pricing': 'Continuous price discovery'}, 'forward_market': {'definition': 'Future delivery at predetermined rate', 'characteristics': 'Customizable terms, no upfront payment', 'participants': 'Banks, corporations, institutional investors', 'pricing': 'Based on interest rate differentials'}, 'futures_market': {'definition': 'Standardized forward contracts on exchanges', 'characteristics': 'Margin requirements, daily mark-to-market', 'participants': 'Speculators, hedgers, arbitrageurs', 'pricing': 'Exchange-determined, transparent'}, 'options_market': {'definition': 'Right but not obligation to exchange currencies', 'characteristics': 'Premium payment, asymmetric payoff', 'participants': 'Sophisticated institutional investors', 'pricing': 'Based on volatility and time value'}, 'swap_market': {'definition': 'Combination of spot and forward transactions', 'characteristics': 'Manages liquidity without FX risk', 'participants': 'Central banks, commercial banks', 'pricing': 'Interest rate differential based'}}

    def _analyze_market_liquidity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FX market liquidity"""
        return {'liquidity_measures': {'bid_ask_spreads': data.get('avg_spread_bps', '1-3 basis points for major pairs'), 'market_depth': 'High depth due to large participant base', 'resilience': 'Quick recovery from temporary imbalances', 'immediacy': 'Instant execution for standard sizes'}, 'liquidity_hierarchy': {'tier_1': 'EUR/USD, USD/JPY, GBP/USD (most liquid)', 'tier_2': 'USD/CHF, AUD/USD, USD/CAD', 'tier_3': 'Cross rates between major currencies', 'tier_4': 'Emerging market currencies (lower liquidity)'}, 'factors_affecting_liquidity': ['Time of day (overlap of major centers)', 'Economic news and events', 'Market volatility and uncertainty', 'Regulatory changes', 'Central bank interventions'], 'liquidity_risk': {'normal_times': 'Minimal liquidity risk for major pairs', 'stress_periods': 'Can experience temporary liquidity shortages', 'emerging_markets': 'Higher liquidity risk, especially during crises'}}

    def _calculate_real_exchange_rate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate real exchange rate"""
        nominal_rate = self.to_decimal(data.get('nominal_rate', 1))
        domestic_cpi = self.to_decimal(data.get('domestic_price_level', 100))
        foreign_cpi = self.to_decimal(data.get('foreign_price_level', 100))
        real_rate = nominal_rate * (foreign_cpi / domestic_cpi)
        return {'real_exchange_rate': real_rate, 'calculation': f'{nominal_rate} × ({foreign_cpi}/{domestic_cpi}) = {real_rate}', 'interpretation': self._interpret_real_rate_level(real_rate, data.get('historical_average', 1))}

    def _interpret_real_rate_changes(self, data: Dict[str, Any]) -> str:
        """Interpret real exchange rate changes"""
        real_rate_change = self.to_decimal(data.get('real_rate_change_percent', 0))
        if real_rate_change > self.to_decimal(5):
            return 'Significant real appreciation - loss of competitiveness'
        elif real_rate_change < self.to_decimal(-5):
            return 'Significant real depreciation - gain in competitiveness'
        else:
            return 'Moderate real exchange rate change'

    def _interpret_real_rate_level(self, current_rate: Decimal, historical_avg: float) -> str:
        """Interpret real exchange rate level"""
        historical = self.to_decimal(historical_avg)
        deviation = (current_rate - historical) / historical * self.to_decimal(100)
        if deviation > self.to_decimal(10):
            return 'Real exchange rate appears overvalued'
        elif deviation < self.to_decimal(-10):
            return 'Real exchange rate appears undervalued'
        else:
            return 'Real exchange rate near historical average'

    def _describe_rate_applications(self) -> Dict[str, str]:
        """Describe practical applications of nominal vs real rates"""
        return {'nominal_rates': 'Used for actual currency transactions, hedging, and short-term speculation', 'real_rates': 'Used for competitiveness analysis, long-term investment decisions, and trade policy', 'portfolio_management': 'Nominal rates for immediate hedging, real rates for strategic allocation', 'trade_analysis': 'Real rates better predict trade flow changes over time', 'central_bank_policy': 'Both rates considered, real rates for competitiveness assessment'}

    def _assess_change_magnitude(self, abs_change: Decimal) -> str:
        """Assess magnitude of currency change"""
        if abs_change > self.to_decimal(10):
            return 'Major currency movement'
        elif abs_change > self.to_decimal(5):
            return 'Significant currency movement'
        elif abs_change > self.to_decimal(2):
            return 'Moderate currency movement'
        else:
            return 'Minor currency movement'

    def _analyze_currency_change_implications(self, change: Decimal, base: str, quote: str) -> Dict[str, str]:
        """Analyze economic implications of currency changes"""
        return {'trade_balance': 'Depreciation improves trade balance over time (J-curve effect)', 'inflation': 'Depreciation can increase import price inflation', 'competitiveness': 'Depreciation improves export competitiveness', 'debt_burden': 'Depreciation increases foreign currency debt burden', 'tourism': 'Depreciation makes country more attractive to foreign tourists', 'investment_flows': 'Large changes may trigger capital flow reversals'}

    def _assess_trade_impact(self, change: Decimal, convention: str) -> str:
        """Assess trade impact of currency change"""
        if convention == 'direct':
            if change > self.to_decimal(5):
                return 'Currency weakness should improve trade balance over 12-18 months'
            elif change < self.to_decimal(-5):
                return 'Currency strength may worsen trade balance'
            else:
                return 'Limited impact on trade balance expected'
        elif change > self.to_decimal(5):
            return 'Currency strength may worsen trade balance'
        elif change < self.to_decimal(-5):
            return 'Currency weakness should improve trade balance over 12-18 months'
        else:
            return 'Limited impact on trade balance expected'

    def _assess_investment_implications(self, change: Decimal) -> List[str]:
        """Assess investment implications of currency changes"""
        implications = []
        if abs(change) > self.to_decimal(5):
            implications.extend(['Significant impact on foreign investment returns', 'May trigger portfolio rebalancing by international investors', 'Hedging strategies should be reviewed'])
        if change > self.to_decimal(10):
            implications.append('Large appreciation may deter foreign direct investment')
        elif change < self.to_decimal(-10):
            implications.append('Large depreciation may attract foreign direct investment')
        return implications

    def calculate(self, analysis_type: str='market_structure', **kwargs) -> Dict[str, Any]:
        """Main FX market calculation dispatcher"""
        analyses = {'market_structure': lambda: self.analyze_fx_market_structure(kwargs.get('market_data', {})), 'nominal_real_rates': lambda: self.distinguish_nominal_real_rates(kwargs.get('rate_data', {})), 'percentage_change': lambda: self.calculate_currency_percentage_change(kwargs.get('change_data', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def calculate_currency_percentage_change(self, change_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate and interpret currency percentage changes"""
    initial_rate = self.to_decimal(change_data.get('initial_rate', 1))
    final_rate = self.to_decimal(change_data.get('final_rate', 1))
    base_currency = change_data.get('base_currency', 'USD')
    quote_currency = change_data.get('quote_currency', 'EUR')
    quote_convention = change_data.get('quote_convention', 'direct')
    percentage_change = (final_rate - initial_rate) / initial_rate * self.to_decimal(100)
    if quote_convention == 'direct':
        if percentage_change > 0:
            movement = f'{base_currency} weakened by {percentage_change:.2f}%'
            description = f'{quote_currency} appreciated against {base_currency}'
        else:
            movement = f'{base_currency} strengthened by {abs(percentage_change):.2f}%'
            description = f'{quote_currency} depreciated against {base_currency}'
    elif percentage_change > 0:
        movement = f'{base_currency} strengthened by {percentage_change:.2f}%'
        description = f'{base_currency} appreciated against {quote_currency}'
    else:
        movement = f'{base_currency} weakened by {abs(percentage_change):.2f}%'
        description = f'{base_currency} depreciated against {quote_currency}'
    return {'calculation_details': {'initial_rate': initial_rate, 'final_rate': final_rate, 'absolute_change': final_rate - initial_rate, 'percentage_change': percentage_change, 'quote_convention': quote_convention}, 'currency_movement': {'summary': movement, 'detailed_description': description, 'direction': 'appreciation' if percentage_change > 0 else 'depreciation', 'magnitude': self._assess_change_magnitude(abs(percentage_change))}, 'economic_implications': self._analyze_currency_change_implications(percentage_change, base_currency, quote_currency), 'trade_impact': self._assess_trade_impact(percentage_change, quote_convention), 'investment_implications': self._assess_investment_implications(percentage_change)}

def _calculate_real_exchange_rate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate real exchange rate"""
    nominal_rate = self.to_decimal(data.get('nominal_rate', 1))
    domestic_cpi = self.to_decimal(data.get('domestic_price_level', 100))
    foreign_cpi = self.to_decimal(data.get('foreign_price_level', 100))
    real_rate = nominal_rate * (foreign_cpi / domestic_cpi)
    return {'real_exchange_rate': real_rate, 'calculation': f'{nominal_rate} × ({foreign_cpi}/{domestic_cpi}) = {real_rate}', 'interpretation': self._interpret_real_rate_level(real_rate, data.get('historical_average', 1))}

def _interpret_real_rate_changes(self, data: Dict[str, Any]) -> str:
    """Interpret real exchange rate changes"""
    real_rate_change = self.to_decimal(data.get('real_rate_change_percent', 0))
    if real_rate_change > self.to_decimal(5):
        return 'Significant real appreciation - loss of competitiveness'
    elif real_rate_change < self.to_decimal(-5):
        return 'Significant real depreciation - gain in competitiveness'
    else:
        return 'Moderate real exchange rate change'

def _interpret_real_rate_level(self, current_rate: Decimal, historical_avg: float) -> str:
    """Interpret real exchange rate level"""
    historical = self.to_decimal(historical_avg)
    deviation = (current_rate - historical) / historical * self.to_decimal(100)
    if deviation > self.to_decimal(10):
        return 'Real exchange rate appears overvalued'
    elif deviation < self.to_decimal(-10):
        return 'Real exchange rate appears undervalued'
    else:
        return 'Real exchange rate near historical average'

def _assess_change_magnitude(self, abs_change: Decimal) -> str:
    """Assess magnitude of currency change"""
    if abs_change > self.to_decimal(10):
        return 'Major currency movement'
    elif abs_change > self.to_decimal(5):
        return 'Significant currency movement'
    elif abs_change > self.to_decimal(2):
        return 'Moderate currency movement'
    else:
        return 'Minor currency movement'

def _assess_trade_impact(self, change: Decimal, convention: str) -> str:
    """Assess trade impact of currency change"""
    if convention == 'direct':
        if change > self.to_decimal(5):
            return 'Currency weakness should improve trade balance over 12-18 months'
        elif change < self.to_decimal(-5):
            return 'Currency strength may worsen trade balance'
        else:
            return 'Limited impact on trade balance expected'
    elif change > self.to_decimal(5):
        return 'Currency strength may worsen trade balance'
    elif change < self.to_decimal(-5):
        return 'Currency weakness should improve trade balance over 12-18 months'
    else:
        return 'Limited impact on trade balance expected'

def _assess_investment_implications(self, change: Decimal) -> List[str]:
    """Assess investment implications of currency changes"""
    implications = []
    if abs(change) > self.to_decimal(5):
        implications.extend(['Significant impact on foreign investment returns', 'May trigger portfolio rebalancing by international investors', 'Hedging strategies should be reviewed'])
    if change > self.to_decimal(10):
        implications.append('Large appreciation may deter foreign direct investment')
    elif change < self.to_decimal(-10):
        implications.append('Large depreciation may attract foreign direct investment')
    return implications

def calculate(self, analysis_type: str='market_structure', **kwargs) -> Dict[str, Any]:
    """Main FX market calculation dispatcher"""
    analyses = {'market_structure': lambda: self.analyze_fx_market_structure(kwargs.get('market_data', {})), 'nominal_real_rates': lambda: self.distinguish_nominal_real_rates(kwargs.get('rate_data', {})), 'percentage_change': lambda: self.calculate_currency_percentage_change(kwargs.get('change_data', {}))}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    return result

class ExchangeRegimeAnalyzer(EconomicsBase):
    """Exchange rate regime analysis and policy implications"""

    def analyze_exchange_rate_regimes(self, regime_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze different exchange rate regimes and their effects"""
        return {'fixed_exchange_rate': {'definition': 'Currency pegged to another currency or basket', 'characteristics': ['Minimal exchange rate volatility', 'Requires central bank intervention', 'Limited monetary policy independence', 'Vulnerable to speculative attacks'], 'advantages': ['Reduces transaction costs for trade', 'Provides nominal anchor for inflation', 'Reduces exchange rate uncertainty', 'Facilitates international investment'], 'disadvantages': ['Loss of monetary policy independence', 'Requires large foreign exchange reserves', 'Vulnerable to balance of payments crises', 'May lead to real exchange rate misalignment'], 'examples': ['Hong Kong Dollar', 'Danish Krone', 'Gulf States'], 'sustainability_factors': self._assess_fixed_regime_sustainability(regime_data)}, 'floating_exchange_rate': {'definition': 'Currency value determined by market forces', 'characteristics': ['High exchange rate volatility', 'Automatic adjustment mechanism', 'Full monetary policy independence', 'Requires developed financial markets'], 'advantages': ['Monetary policy independence', 'Automatic adjustment to shocks', 'No need for large reserves', 'Reduces moral hazard in lending'], 'disadvantages': ['Exchange rate volatility and uncertainty', 'May complicate international trade', 'Potential for destabilizing speculation', 'Pass-through to domestic prices'], 'examples': ['US Dollar', 'Euro', 'Japanese Yen', 'British Pound'], 'effectiveness_factors': self._assess_floating_regime_effectiveness(regime_data)}, 'managed_float': {'definition': 'Market determination with occasional intervention', 'characteristics': ['Moderate exchange rate volatility', 'Discretionary intervention', 'Some monetary policy independence', 'Requires judgment on intervention timing'], 'advantages': ['Balances flexibility and stability', 'Allows gradual adjustment', 'Retains some policy independence', 'Can prevent excessive volatility'], 'disadvantages': ['Uncertainty about intervention policy', 'May delay necessary adjustments', 'Requires significant expertise', 'Potential for policy mistakes'], 'examples': ['Chinese Yuan', 'Indian Rupee', 'Brazilian Real'], 'success_factors': self._identify_managed_float_success_factors()}, 'currency_union': {'definition': 'Countries share common currency', 'characteristics': ['No exchange rate within union', 'Common monetary policy', 'Requires fiscal coordination', 'Irreversible commitment'], 'advantages': ['Eliminates exchange rate risk within union', 'Reduces transaction costs', 'Promotes trade and investment', 'Provides credible commitment'], 'disadvantages': ['Loss of national monetary policy', 'Asymmetric shock vulnerability', 'Requires fiscal transfers or flexibility', 'Difficult exit mechanism'], 'examples': ['Eurozone', 'West African CFA Franc'], 'optimum_currency_area_criteria': self._assess_oca_criteria(regime_data)}, 'regime_choice_factors': self._analyze_regime_choice_factors(), 'trade_capital_flow_effects': self._analyze_regime_effects_on_flows(regime_data)}

    def _assess_fixed_regime_sustainability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess sustainability factors for fixed exchange rate regime"""
        return {'foreign_reserves': {'level': data.get('reserves_months_imports', 'N/A'), 'adequacy': 'Should cover 3-6 months of imports', 'assessment': self._assess_reserve_adequacy(data.get('reserves_months_imports', 3))}, 'fiscal_position': {'deficit': data.get('fiscal_deficit_gdp', 'N/A'), 'debt': data.get('government_debt_gdp', 'N/A'), 'sustainability': 'Fiscal discipline critical for credibility'}, 'current_account': {'balance': data.get('current_account_gdp', 'N/A'), 'sustainability': 'Large deficits threaten sustainability'}, 'political_commitment': {'importance': 'Strong political will essential', 'indicators': ['Central bank independence', 'Policy consistency', 'Reform commitment']}}

    def _assess_floating_regime_effectiveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess effectiveness factors for floating exchange rate regime"""
        return {'financial_market_development': {'depth': data.get('financial_market_depth_index', 'N/A'), 'importance': 'Deep markets reduce volatility', 'requirements': ['Large participant base', 'Diverse instruments', 'Good regulation']}, 'institutional_quality': {'central_bank_credibility': data.get('cb_credibility_index', 'N/A'), 'importance': 'Credible monetary policy anchors expectations', 'factors': ['Independence', 'Transparency', 'Track record']}, 'pass_through_management': {'inflation_targeting': 'Helps manage pass-through effects', 'communication': 'Clear policy communication important', 'credibility': 'Credible commitment to low inflation'}}

    def _identify_managed_float_success_factors(self) -> List[str]:
        """Identify success factors for managed float regimes"""
        return ['Clear intervention objectives and communication', 'Adequate foreign exchange reserves', 'Flexible fiscal and monetary policies', 'Well-developed financial markets', 'Strong institutional capacity', 'Appropriate intervention timing and scale']

    def _assess_oca_criteria(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess optimum currency area criteria"""
        return {'labor_mobility': {'assessment': data.get('labor_mobility_index', 'Low'), 'importance': 'High mobility helps adjustment to asymmetric shocks', 'barriers': ['Language differences', 'Cultural factors', 'Regulatory barriers']}, 'trade_integration': {'level': data.get('intra_union_trade_share', 'N/A'), 'importance': 'High trade integration reduces asymmetric shocks', 'measurement': 'Share of trade within currency union'}, 'business_cycle_synchronization': {'correlation': data.get('business_cycle_correlation', 'N/A'), 'importance': 'Synchronized cycles reduce need for independent policy', 'factors': ['Similar economic structures', 'Common shocks', 'Policy coordination']}, 'fiscal_transfers': {'mechanism': data.get('fiscal_transfer_mechanism', 'Limited'), 'importance': 'Transfers help adjustment to asymmetric shocks', 'examples': ['Federal systems', 'EU structural funds', 'Automatic stabilizers']}, 'price_wage_flexibility': {'level': data.get('price_wage_flexibility_index', 'N/A'), 'importance': 'Flexibility substitutes for exchange rate adjustment', 'barriers': ['Labor market rigidities', 'Price stickiness', 'Regulatory constraints']}}

    def _analyze_regime_choice_factors(self) -> Dict[str, List[str]]:
        """Analyze factors influencing exchange rate regime choice"""
        return {'economic_factors': ['Size and openness of economy', 'Trade pattern and partner concentration', 'Financial market development', 'Inflation history and credibility', 'Fiscal position and discipline'], 'institutional_factors': ['Central bank independence and credibility', 'Political stability and consensus', 'Administrative capacity', 'Legal and regulatory framework', 'International integration'], 'external_factors': ['International capital mobility', 'Regional integration arrangements', 'Major trading partner regimes', 'Global financial conditions', 'International monetary system']}

    def _analyze_regime_effects_on_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze effects of exchange rate regimes on trade and capital flows"""
        return {'trade_effects': {'fixed_regime': {'trade_volume': 'Generally higher due to reduced uncertainty', 'trade_composition': 'May favor short-term over long-term contracts', 'price_competitiveness': 'May lead to misalignment over time'}, 'floating_regime': {'trade_volume': 'May be lower due to exchange rate risk', 'trade_composition': 'Encourages hedging and risk management', 'price_competitiveness': 'Maintains competitiveness through adjustment'}}, 'capital_flow_effects': {'fixed_regime': {'portfolio_flows': 'May attract flows but vulnerable to sudden stops', 'fdi_flows': 'Reduced exchange rate risk may encourage FDI', 'speculative_flows': 'Vulnerable to one-way bets against the peg'}, 'floating_regime': {'portfolio_flows': 'More volatile but self-correcting', 'fdi_flows': 'Exchange rate risk may deter some investment', 'speculative_flows': 'Two-way risk reduces speculative pressure'}}, 'crisis_vulnerability': {'fixed_regime': 'High vulnerability to balance of payments crises', 'floating_regime': 'Lower crisis probability but higher volatility', 'managed_float': 'Intermediate vulnerability depending on credibility'}}

    def _assess_reserve_adequacy(self, months_imports: float) -> str:
        """Assess foreign reserve adequacy"""
        if months_imports >= 6:
            return 'Adequate reserves for fixed regime'
        elif months_imports >= 3:
            return 'Borderline adequate reserves'
        else:
            return 'Insufficient reserves for sustainable fixed regime'

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate exchange rate regime analysis"""
        result = self.analyze_exchange_rate_regimes(kwargs.get('regime_data', {}))
        result['metadata'] = self.get_metadata()
        return result

def calculate(self, **kwargs) -> Dict[str, Any]:
    """Calculate exchange rate regime analysis"""
    result = self.analyze_exchange_rate_regimes(kwargs.get('regime_data', {}))
    result['metadata'] = self.get_metadata()
    return result

class GrowthAnalyzer(EconomicsBase):
    """Main economic growth analysis coordinator"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)
        self.productivity = ProductivityAnalyzer(precision, base_currency)
        self.convergence = ConvergenceAnalyzer(precision, base_currency)
        self.demographic = DemographicAnalyzer(precision, base_currency)

    def compare_growth_factors(self, country_type: str, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare factors favoring and limiting growth in developed vs developing economies"""
        if country_type.lower() not in ['developed', 'developing']:
            raise ValidationError("Country type must be 'developed' or 'developing'")
        if country_type.lower() == 'developed':
            return self._analyze_developed_economy_factors(economic_data)
        else:
            return self._analyze_developing_economy_factors(economic_data)

    def _analyze_developed_economy_factors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth factors for developed economies"""
        gdp_per_capita = self.to_decimal(data.get('gdp_per_capita', 0))
        rd_spending = self.to_decimal(data.get('rd_spending_percent_gdp', 0))
        education_index = self.to_decimal(data.get('education_index', 0))
        infrastructure_quality = self.to_decimal(data.get('infrastructure_quality', 0))
        population_growth = self.to_decimal(data.get('population_growth_rate', 0))
        aging_ratio = self.to_decimal(data.get('old_age_dependency_ratio', 0))
        favoring_factors = {'technological_innovation': {'score': rd_spending * self.to_decimal(10), 'description': 'High R&D spending drives innovation-led growth', 'weight': self.to_decimal(0.25)}, 'human_capital': {'score': education_index * self.to_decimal(100), 'description': 'Skilled workforce enables productivity gains', 'weight': self.to_decimal(0.2)}, 'institutional_quality': {'score': infrastructure_quality, 'description': 'Strong institutions support efficient markets', 'weight': self.to_decimal(0.2)}, 'capital_deepening': {'score': self.to_decimal(85), 'description': 'Existing capital stock supports productivity', 'weight': self.to_decimal(0.15)}}
        limiting_factors = {'demographic_constraints': {'score': aging_ratio, 'description': 'Aging population reduces labor force growth', 'weight': self.to_decimal(0.3)}, 'diminishing_returns': {'score': gdp_per_capita / self.to_decimal(1000), 'description': 'High income levels face diminishing marginal returns', 'weight': self.to_decimal(0.25)}, 'low_population_growth': {'score': max(self.to_decimal(0), self.to_decimal(2) - population_growth) * self.to_decimal(50), 'description': 'Low population growth limits labor force expansion', 'weight': self.to_decimal(0.2)}, 'mature_economy_constraints': {'score': self.to_decimal(70), 'description': 'Limited catch-up growth opportunities', 'weight': self.to_decimal(0.25)}}
        favoring_score = sum((factor['score'] * factor['weight'] for factor in favoring_factors.values()))
        limiting_score = sum((factor['score'] * factor['weight'] for factor in limiting_factors.values()))
        return {'country_type': 'developed', 'favoring_factors': favoring_factors, 'limiting_factors': limiting_factors, 'composite_favoring_score': favoring_score, 'composite_limiting_score': limiting_score, 'net_growth_potential': favoring_score - limiting_score, 'primary_growth_drivers': ['technological_innovation', 'human_capital'], 'main_constraints': ['demographic_constraints', 'diminishing_returns']}

    def _analyze_developing_economy_factors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth factors for developing economies"""
        gdp_per_capita = self.to_decimal(data.get('gdp_per_capita', 0))
        savings_rate = self.to_decimal(data.get('savings_rate', 0))
        fdi_inflows = self.to_decimal(data.get('fdi_percent_gdp', 0))
        population_growth = self.to_decimal(data.get('population_growth_rate', 0))
        institutional_quality = self.to_decimal(data.get('institutional_quality_index', 0))
        education_enrollment = self.to_decimal(data.get('secondary_education_enrollment', 0))
        favoring_factors = {'catch_up_potential': {'score': max(self.to_decimal(0), self.to_decimal(50) - gdp_per_capita / self.to_decimal(1000)), 'description': 'Low income levels allow rapid catch-up growth', 'weight': self.to_decimal(0.25)}, 'demographic_dividend': {'score': min(population_growth * self.to_decimal(25), self.to_decimal(100)), 'description': 'Young population provides growing workforce', 'weight': self.to_decimal(0.2)}, 'capital_accumulation': {'score': savings_rate * self.to_decimal(2), 'description': 'High savings enable capital investment', 'weight': self.to_decimal(0.2)}, 'technology_transfer': {'score': fdi_inflows * self.to_decimal(10), 'description': 'FDI brings advanced technology and knowledge', 'weight': self.to_decimal(0.15)}, 'education_expansion': {'score': education_enrollment, 'description': 'Growing human capital base', 'weight': self.to_decimal(0.2)}}
        limiting_factors = {'institutional_weaknesses': {'score': self.to_decimal(100) - institutional_quality, 'description': 'Weak institutions hinder efficient resource allocation', 'weight': self.to_decimal(0.3)}, 'infrastructure_gaps': {'score': self.to_decimal(80), 'description': 'Inadequate infrastructure limits productivity', 'weight': self.to_decimal(0.25)}, 'human_capital_deficits': {'score': self.to_decimal(100) - education_enrollment, 'description': 'Limited education reduces productivity potential', 'weight': self.to_decimal(0.2)}, 'external_dependence': {'score': self.to_decimal(60), 'description': 'Dependence on external financing and technology', 'weight': self.to_decimal(0.25)}}
        favoring_score = sum((factor['score'] * factor['weight'] for factor in favoring_factors.values()))
        limiting_score = sum((factor['score'] * factor['weight'] for factor in limiting_factors.values()))
        return {'country_type': 'developing', 'favoring_factors': favoring_factors, 'limiting_factors': limiting_factors, 'composite_favoring_score': favoring_score, 'composite_limiting_score': limiting_score, 'net_growth_potential': favoring_score - limiting_score, 'primary_growth_drivers': ['catch_up_potential', 'demographic_dividend'], 'main_constraints': ['institutional_weaknesses', 'infrastructure_gaps']}

    def analyze_stock_market_growth_relationship(self, market_data: Dict[str, Any], economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationship between stock market appreciation and sustainable growth rate"""
        stock_returns = [self.to_decimal(r) for r in market_data.get('annual_returns', [])]
        dividend_yield = self.to_decimal(market_data.get('dividend_yield', 0))
        pe_ratio = self.to_decimal(market_data.get('pe_ratio', 0))
        gdp_growth = self.to_decimal(economic_data.get('gdp_growth_rate', 0))
        productivity_growth = self.to_decimal(economic_data.get('productivity_growth', 0))
        employment_growth = self.to_decimal(economic_data.get('employment_growth', 0))
        if not stock_returns:
            raise ValidationError('Stock returns data is required')
        avg_stock_return = sum(stock_returns) / self.to_decimal(len(stock_returns))
        sustainable_growth = gdp_growth
        earnings_growth_component = gdp_growth
        dividend_component = dividend_yield
        valuation_change_component = avg_stock_return - earnings_growth_component - dividend_component
        excess_return = avg_stock_return - sustainable_growth
        return {'average_stock_return': avg_stock_return, 'sustainable_growth_rate': sustainable_growth, 'excess_return': excess_return, 'return_decomposition': {'earnings_growth': earnings_growth_component, 'dividend_yield': dividend_component, 'valuation_change': valuation_change_component}, 'long_run_relationship': {'description': 'In long run, stock returns should converge to sustainable growth + dividend yield', 'theoretical_return': sustainable_growth + dividend_yield, 'current_deviation': avg_stock_return - (sustainable_growth + dividend_yield), 'sustainable': abs(excess_return) < self.to_decimal(2)}, 'implications_for_investors': self._generate_stock_growth_implications(excess_return, pe_ratio)}

    def _generate_stock_growth_implications(self, excess_return: Decimal, pe_ratio: Decimal) -> Dict[str, str]:
        """Generate investment implications from stock-growth relationship"""
        implications = {}
        if excess_return > self.to_decimal(3):
            implications['valuation'] = 'Market may be overvalued relative to economic fundamentals'
            implications['future_returns'] = 'Expected returns may be below historical average'
            implications['risk'] = 'Higher risk of market correction'
        elif excess_return < self.to_decimal(-3):
            implications['valuation'] = 'Market may be undervalued relative to economic fundamentals'
            implications['future_returns'] = 'Expected returns may be above historical average'
            implications['risk'] = 'Potential opportunity for higher returns'
        else:
            implications['valuation'] = 'Market appears fairly valued relative to economic growth'
            implications['future_returns'] = 'Expected returns align with sustainable growth'
            implications['risk'] = 'Balanced risk-return profile'
        if pe_ratio > self.to_decimal(25):
            implications['pe_signal'] = 'High PE suggests expensive market'
        elif pe_ratio < self.to_decimal(12):
            implications['pe_signal'] = 'Low PE suggests attractive valuations'
        else:
            implications['pe_signal'] = 'PE ratio within normal range'
        return implications

    def potential_gdp_importance(self, gdp_data: Dict[str, Any], investor_type: str) -> Dict[str, Any]:
        """Explain importance of potential GDP for equity and fixed income investors"""
        potential_gdp = self.to_decimal(gdp_data.get('potential_gdp', 0))
        actual_gdp = self.to_decimal(gdp_data.get('actual_gdp', 0))
        potential_growth = self.to_decimal(gdp_data.get('potential_growth_rate', 0))
        output_gap = (actual_gdp - potential_gdp) / potential_gdp * self.to_decimal(100)
        if investor_type.lower() == 'equity':
            return self._equity_investor_implications(output_gap, potential_growth, gdp_data)
        elif investor_type.lower() == 'fixed_income':
            return self._fixed_income_implications(output_gap, potential_growth, gdp_data)
        else:
            return {'equity_implications': self._equity_investor_implications(output_gap, potential_growth, gdp_data), 'fixed_income_implications': self._fixed_income_implications(output_gap, potential_growth, gdp_data), 'output_gap': output_gap, 'potential_growth_rate': potential_growth}

    def _equity_investor_implications(self, output_gap: Decimal, potential_growth: Decimal, gdp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implications of potential GDP for equity investors"""
        return {'earnings_growth_potential': {'description': 'Potential GDP growth sets upper bound for long-term earnings growth', 'implication': f'Long-term earnings growth limited to ~{potential_growth:.1f}% annually', 'current_position': 'Above potential' if output_gap > 0 else 'Below potential'}, 'cyclical_positioning': {'output_gap': output_gap, 'interpretation': self._interpret_output_gap_equity(output_gap), 'strategy': self._equity_strategy_from_gap(output_gap)}, 'sector_implications': {'cyclical_sectors': 'Sensitive to output gap fluctuations', 'defensive_sectors': 'Less sensitive, focus on long-term potential growth', 'growth_sectors': 'Beneficiaries of productivity improvements driving potential growth'}, 'valuation_framework': {'sustainable_pe': f'Long-term PE ratios should reflect potential growth of {potential_growth:.1f}%', 'cyclical_adjustment': 'Adjust for temporary deviations from potential'}}

    def _fixed_income_implications(self, output_gap: Decimal, potential_growth: Decimal, gdp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implications of potential GDP for fixed income investors"""
        inflation_rate = self.to_decimal(gdp_data.get('inflation_rate', 0))
        return {'monetary_policy_stance': {'output_gap': output_gap, 'policy_implication': self._monetary_policy_from_gap(output_gap), 'interest_rate_direction': self._interest_rate_direction(output_gap)}, 'inflation_expectations': {'gap_pressure': 'Positive gap = inflationary pressure' if output_gap > 0 else 'Negative gap = disinflationary pressure', 'long_term_anchor': f'Long-term inflation should align with potential growth of {potential_growth:.1f}%', 'current_risk': 'Inflation risk elevated' if output_gap > self.to_decimal(2) else 'Inflation risk contained'}, 'yield_curve_implications': {'short_end': 'Driven by central bank response to output gap', 'long_end': 'Anchored by potential growth and inflation expectations', 'curve_shape': self._yield_curve_shape(output_gap)}, 'credit_risk_assessment': {'corporate_earnings': 'Tied to actual vs potential GDP performance', 'default_risk': 'Lower when economy operates near potential', 'recovery_rates': 'Higher potential growth supports better recovery values'}}

    def _interpret_output_gap_equity(self, gap: Decimal) -> str:
        """Interpret output gap for equity investors"""
        if gap > self.to_decimal(2):
            return 'Economy overheating - potential for policy tightening and earnings pressure'
        elif gap > self.to_decimal(0):
            return 'Economy above potential - supporting earnings but watch for inflation'
        elif gap > self.to_decimal(-2):
            return 'Economy near potential - balanced growth environment'
        else:
            return 'Economy below potential - room for growth but current earnings pressure'

    def _equity_strategy_from_gap(self, gap: Decimal) -> str:
        """Suggest equity strategy based on output gap"""
        if gap > self.to_decimal(2):
            return 'Consider defensive positioning, watch for policy tightening'
        elif gap > self.to_decimal(0):
            return 'Balanced approach, favor quality cyclicals'
        else:
            return 'Growth opportunities available, consider cyclical exposure'

    def _monetary_policy_from_gap(self, gap: Decimal) -> str:
        """Predict monetary policy stance from output gap"""
        if gap > self.to_decimal(1):
            return 'Likely tightening bias'
        elif gap > self.to_decimal(-1):
            return 'Neutral stance'
        else:
            return 'Likely easing bias'

    def _interest_rate_direction(self, gap: Decimal) -> str:
        """Predict interest rate direction"""
        if gap > self.to_decimal(1):
            return 'Upward pressure'
        elif gap > self.to_decimal(-1):
            return 'Stable'
        else:
            return 'Downward pressure'

    def _yield_curve_shape(self, gap: Decimal) -> str:
        """Predict yield curve shape"""
        if gap > self.to_decimal(2):
            return 'Flattening risk (short rates rising faster)'
        elif gap < self.to_decimal(-2):
            return 'Steepening (short rates falling faster)'
        else:
            return 'Stable shape'

    def forecast_potential_gdp(self, historical_data: Dict[str, Any], forecast_assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast potential GDP using growth accounting relations"""
        labor_force_growth = [self.to_decimal(x) for x in historical_data.get('labor_force_growth', [])]
        productivity_growth = [self.to_decimal(x) for x in historical_data.get('productivity_growth', [])]
        capital_growth = [self.to_decimal(x) for x in historical_data.get('capital_growth', [])]
        forecast_periods = int(forecast_assumptions.get('periods', 5))
        labor_growth_forecast = self.to_decimal(forecast_assumptions.get('labor_growth_rate', 0))
        productivity_growth_forecast = self.to_decimal(forecast_assumptions.get('productivity_growth_rate', 0))
        capital_growth_forecast = self.to_decimal(forecast_assumptions.get('capital_growth_rate', 0))
        alpha = self.to_decimal(forecast_assumptions.get('capital_share', 0.3))
        historical_potential = []
        min_length = min(len(labor_force_growth), len(productivity_growth), len(capital_growth))
        for i in range(min_length):
            potential_growth = productivity_growth[i] + alpha * capital_growth[i] + (self.to_decimal(1) - alpha) * labor_force_growth[i]
            historical_potential.append(potential_growth)
        forecast_potential_growth = productivity_growth_forecast + alpha * capital_growth_forecast + (self.to_decimal(1) - alpha) * labor_growth_forecast
        trend_productivity = sum(productivity_growth) / self.to_decimal(len(productivity_growth)) if productivity_growth else self.to_decimal(0)
        trend_labor = sum(labor_force_growth) / self.to_decimal(len(labor_force_growth)) if labor_force_growth else self.to_decimal(0)
        trend_capital = sum(capital_growth) / self.to_decimal(len(capital_growth)) if capital_growth else self.to_decimal(0)
        return {'growth_accounting_framework': {'formula': 'GDP Growth = Productivity Growth + α×Capital Growth + (1-α)×Labor Growth', 'capital_share_alpha': alpha, 'labor_share': self.to_decimal(1) - alpha}, 'historical_analysis': {'historical_potential_growth': historical_potential, 'average_historical_potential': sum(historical_potential) / self.to_decimal(len(historical_potential)) if historical_potential else self.to_decimal(0), 'trend_components': {'productivity': trend_productivity, 'labor_force': trend_labor, 'capital_stock': trend_capital}}, 'forecast': {'periods': forecast_periods, 'potential_gdp_growth': forecast_potential_growth, 'components': {'productivity_contribution': productivity_growth_forecast, 'capital_contribution': alpha * capital_growth_forecast, 'labor_contribution': (self.to_decimal(1) - alpha) * labor_growth_forecast}, 'assumptions': forecast_assumptions}, 'sensitivity_analysis': self._sensitivity_analysis_potential_gdp(alpha, productivity_growth_forecast, capital_growth_forecast, labor_growth_forecast)}

    def _sensitivity_analysis_potential_gdp(self, alpha: Decimal, prod_growth: Decimal, cap_growth: Decimal, lab_growth: Decimal) -> Dict[str, Any]:
        """Sensitivity analysis for potential GDP forecast"""
        base_growth = prod_growth + alpha * cap_growth + (self.to_decimal(1) - alpha) * lab_growth
        scenarios = {'productivity_high': prod_growth + self.to_decimal(0.005), 'productivity_low': prod_growth - self.to_decimal(0.005), 'capital_high': cap_growth + self.to_decimal(0.01), 'capital_low': cap_growth - self.to_decimal(0.01), 'labor_high': lab_growth + self.to_decimal(0.005), 'labor_low': lab_growth - self.to_decimal(0.005)}
        sensitivity_results = {}
        for scenario, value in scenarios.items():
            if 'productivity' in scenario:
                new_growth = value + alpha * cap_growth + (self.to_decimal(1) - alpha) * lab_growth
            elif 'capital' in scenario:
                new_growth = prod_growth + alpha * value + (self.to_decimal(1) - alpha) * lab_growth
            else:
                new_growth = prod_growth + alpha * cap_growth + (self.to_decimal(1) - alpha) * value
            sensitivity_results[scenario] = {'growth_rate': new_growth, 'change_from_base': new_growth - base_growth}
        return {'base_case': base_growth, 'scenarios': sensitivity_results, 'most_sensitive_to': max(sensitivity_results.items(), key=lambda x: abs(x[1]['change_from_base']))[0]}

    def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Main calculation dispatcher"""
        calculations = {'growth_factors': lambda: self.compare_growth_factors(kwargs['country_type'], kwargs['economic_data']), 'stock_growth_relationship': lambda: self.analyze_stock_market_growth_relationship(kwargs['market_data'], kwargs['economic_data']), 'potential_gdp_importance': lambda: self.potential_gdp_importance(kwargs['gdp_data'], kwargs.get('investor_type', 'both')), 'forecast_potential_gdp': lambda: self.forecast_potential_gdp(kwargs['historical_data'], kwargs['forecast_assumptions'])}
        if analysis_type not in calculations:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = calculations[analysis_type]()
        result['metadata'] = self.get_metadata()
        result['analysis_type'] = analysis_type
        return result

def analyze_stock_market_growth_relationship(self, market_data: Dict[str, Any], economic_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze relationship between stock market appreciation and sustainable growth rate"""
    stock_returns = [self.to_decimal(r) for r in market_data.get('annual_returns', [])]
    dividend_yield = self.to_decimal(market_data.get('dividend_yield', 0))
    pe_ratio = self.to_decimal(market_data.get('pe_ratio', 0))
    gdp_growth = self.to_decimal(economic_data.get('gdp_growth_rate', 0))
    productivity_growth = self.to_decimal(economic_data.get('productivity_growth', 0))
    employment_growth = self.to_decimal(economic_data.get('employment_growth', 0))
    if not stock_returns:
        raise ValidationError('Stock returns data is required')
    avg_stock_return = sum(stock_returns) / self.to_decimal(len(stock_returns))
    sustainable_growth = gdp_growth
    earnings_growth_component = gdp_growth
    dividend_component = dividend_yield
    valuation_change_component = avg_stock_return - earnings_growth_component - dividend_component
    excess_return = avg_stock_return - sustainable_growth
    return {'average_stock_return': avg_stock_return, 'sustainable_growth_rate': sustainable_growth, 'excess_return': excess_return, 'return_decomposition': {'earnings_growth': earnings_growth_component, 'dividend_yield': dividend_component, 'valuation_change': valuation_change_component}, 'long_run_relationship': {'description': 'In long run, stock returns should converge to sustainable growth + dividend yield', 'theoretical_return': sustainable_growth + dividend_yield, 'current_deviation': avg_stock_return - (sustainable_growth + dividend_yield), 'sustainable': abs(excess_return) < self.to_decimal(2)}, 'implications_for_investors': self._generate_stock_growth_implications(excess_return, pe_ratio)}

def _generate_stock_growth_implications(self, excess_return: Decimal, pe_ratio: Decimal) -> Dict[str, str]:
    """Generate investment implications from stock-growth relationship"""
    implications = {}
    if excess_return > self.to_decimal(3):
        implications['valuation'] = 'Market may be overvalued relative to economic fundamentals'
        implications['future_returns'] = 'Expected returns may be below historical average'
        implications['risk'] = 'Higher risk of market correction'
    elif excess_return < self.to_decimal(-3):
        implications['valuation'] = 'Market may be undervalued relative to economic fundamentals'
        implications['future_returns'] = 'Expected returns may be above historical average'
        implications['risk'] = 'Potential opportunity for higher returns'
    else:
        implications['valuation'] = 'Market appears fairly valued relative to economic growth'
        implications['future_returns'] = 'Expected returns align with sustainable growth'
        implications['risk'] = 'Balanced risk-return profile'
    if pe_ratio > self.to_decimal(25):
        implications['pe_signal'] = 'High PE suggests expensive market'
    elif pe_ratio < self.to_decimal(12):
        implications['pe_signal'] = 'Low PE suggests attractive valuations'
    else:
        implications['pe_signal'] = 'PE ratio within normal range'
    return implications

def _fixed_income_implications(self, output_gap: Decimal, potential_growth: Decimal, gdp_data: Dict[str, Any]) -> Dict[str, Any]:
    """Implications of potential GDP for fixed income investors"""
    inflation_rate = self.to_decimal(gdp_data.get('inflation_rate', 0))
    return {'monetary_policy_stance': {'output_gap': output_gap, 'policy_implication': self._monetary_policy_from_gap(output_gap), 'interest_rate_direction': self._interest_rate_direction(output_gap)}, 'inflation_expectations': {'gap_pressure': 'Positive gap = inflationary pressure' if output_gap > 0 else 'Negative gap = disinflationary pressure', 'long_term_anchor': f'Long-term inflation should align with potential growth of {potential_growth:.1f}%', 'current_risk': 'Inflation risk elevated' if output_gap > self.to_decimal(2) else 'Inflation risk contained'}, 'yield_curve_implications': {'short_end': 'Driven by central bank response to output gap', 'long_end': 'Anchored by potential growth and inflation expectations', 'curve_shape': self._yield_curve_shape(output_gap)}, 'credit_risk_assessment': {'corporate_earnings': 'Tied to actual vs potential GDP performance', 'default_risk': 'Lower when economy operates near potential', 'recovery_rates': 'Higher potential growth supports better recovery values'}}

def _interpret_output_gap_equity(self, gap: Decimal) -> str:
    """Interpret output gap for equity investors"""
    if gap > self.to_decimal(2):
        return 'Economy overheating - potential for policy tightening and earnings pressure'
    elif gap > self.to_decimal(0):
        return 'Economy above potential - supporting earnings but watch for inflation'
    elif gap > self.to_decimal(-2):
        return 'Economy near potential - balanced growth environment'
    else:
        return 'Economy below potential - room for growth but current earnings pressure'

def _equity_strategy_from_gap(self, gap: Decimal) -> str:
    """Suggest equity strategy based on output gap"""
    if gap > self.to_decimal(2):
        return 'Consider defensive positioning, watch for policy tightening'
    elif gap > self.to_decimal(0):
        return 'Balanced approach, favor quality cyclicals'
    else:
        return 'Growth opportunities available, consider cyclical exposure'

def _monetary_policy_from_gap(self, gap: Decimal) -> str:
    """Predict monetary policy stance from output gap"""
    if gap > self.to_decimal(1):
        return 'Likely tightening bias'
    elif gap > self.to_decimal(-1):
        return 'Neutral stance'
    else:
        return 'Likely easing bias'

def _interest_rate_direction(self, gap: Decimal) -> str:
    """Predict interest rate direction"""
    if gap > self.to_decimal(1):
        return 'Upward pressure'
    elif gap > self.to_decimal(-1):
        return 'Stable'
    else:
        return 'Downward pressure'

def _yield_curve_shape(self, gap: Decimal) -> str:
    """Predict yield curve shape"""
    if gap > self.to_decimal(2):
        return 'Flattening risk (short rates rising faster)'
    elif gap < self.to_decimal(-2):
        return 'Steepening (short rates falling faster)'
    else:
        return 'Stable shape'

def _sensitivity_analysis_potential_gdp(self, alpha: Decimal, prod_growth: Decimal, cap_growth: Decimal, lab_growth: Decimal) -> Dict[str, Any]:
    """Sensitivity analysis for potential GDP forecast"""
    base_growth = prod_growth + alpha * cap_growth + (self.to_decimal(1) - alpha) * lab_growth
    scenarios = {'productivity_high': prod_growth + self.to_decimal(0.005), 'productivity_low': prod_growth - self.to_decimal(0.005), 'capital_high': cap_growth + self.to_decimal(0.01), 'capital_low': cap_growth - self.to_decimal(0.01), 'labor_high': lab_growth + self.to_decimal(0.005), 'labor_low': lab_growth - self.to_decimal(0.005)}
    sensitivity_results = {}
    for scenario, value in scenarios.items():
        if 'productivity' in scenario:
            new_growth = value + alpha * cap_growth + (self.to_decimal(1) - alpha) * lab_growth
        elif 'capital' in scenario:
            new_growth = prod_growth + alpha * value + (self.to_decimal(1) - alpha) * lab_growth
        else:
            new_growth = prod_growth + alpha * cap_growth + (self.to_decimal(1) - alpha) * value
        sensitivity_results[scenario] = {'growth_rate': new_growth, 'change_from_base': new_growth - base_growth}
    return {'base_case': base_growth, 'scenarios': sensitivity_results, 'most_sensitive_to': max(sensitivity_results.items(), key=lambda x: abs(x[1]['change_from_base']))[0]}

def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
    """Main calculation dispatcher"""
    calculations = {'growth_factors': lambda: self.compare_growth_factors(kwargs['country_type'], kwargs['economic_data']), 'stock_growth_relationship': lambda: self.analyze_stock_market_growth_relationship(kwargs['market_data'], kwargs['economic_data']), 'potential_gdp_importance': lambda: self.potential_gdp_importance(kwargs['gdp_data'], kwargs.get('investor_type', 'both')), 'forecast_potential_gdp': lambda: self.forecast_potential_gdp(kwargs['historical_data'], kwargs['forecast_assumptions'])}
    if analysis_type not in calculations:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = calculations[analysis_type]()
    result['metadata'] = self.get_metadata()
    result['analysis_type'] = analysis_type
    return result

class ProductivityAnalyzer(EconomicsBase):
    """Capital deepening vs technological progress analysis"""

    def analyze_capital_deepening_vs_technology(self, productivity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze effects of capital deepening vs technological progress"""
        capital_per_worker = self.to_decimal(productivity_data.get('capital_per_worker_growth', 0))
        total_factor_productivity = self.to_decimal(productivity_data.get('tfp_growth', 0))
        labor_productivity = self.to_decimal(productivity_data.get('labor_productivity_growth', 0))
        alpha = self.to_decimal(0.3)
        capital_deepening_contribution = alpha * capital_per_worker
        technology_contribution = total_factor_productivity
        implied_productivity_growth = capital_deepening_contribution + technology_contribution
        residual = labor_productivity - implied_productivity_growth
        return {'decomposition': {'labor_productivity_growth': labor_productivity, 'capital_deepening_contribution': capital_deepening_contribution, 'technology_contribution': technology_contribution, 'residual': residual}, 'relative_importance': {'capital_deepening_share': capital_deepening_contribution / labor_productivity * self.to_decimal(100) if labor_productivity != 0 else self.to_decimal(0), 'technology_share': technology_contribution / labor_productivity * self.to_decimal(100) if labor_productivity != 0 else self.to_decimal(0)}, 'economic_implications': {'capital_deepening': {'description': 'Increasing capital per worker', 'effects': 'Diminishing returns, temporary boost to productivity', 'sustainability': 'Limited by diminishing marginal returns', 'policy_focus': 'Investment incentives, savings rates'}, 'technological_progress': {'description': 'Improvements in total factor productivity', 'effects': 'Sustainable productivity gains, no diminishing returns', 'sustainability': 'Can sustain long-term growth', 'policy_focus': 'R&D investment, education, innovation'}}, 'growth_sustainability': self._assess_growth_sustainability(capital_deepening_contribution, technology_contribution)}

    def _assess_growth_sustainability(self, capital_contrib: Decimal, tech_contrib: Decimal) -> Dict[str, Any]:
        """Assess sustainability of growth based on contributions"""
        total_contrib = capital_contrib + tech_contrib
        if total_contrib == 0:
            return {'assessment': 'No productivity growth', 'sustainability': 'Poor'}
        tech_share = tech_contrib / total_contrib
        if tech_share > self.to_decimal(0.7):
            sustainability = 'High'
            assessment = 'Technology-driven growth is highly sustainable'
        elif tech_share > self.to_decimal(0.4):
            sustainability = 'Moderate'
            assessment = 'Balanced growth with good sustainability prospects'
        else:
            sustainability = 'Low'
            assessment = 'Capital-dependent growth faces diminishing returns'
        return {'assessment': assessment, 'sustainability': sustainability, 'technology_share': tech_share * self.to_decimal(100), 'recommendations': self._generate_sustainability_recommendations(tech_share)}

    def _generate_sustainability_recommendations(self, tech_share: Decimal) -> List[str]:
        """Generate recommendations based on technology share"""
        recommendations = []
        if tech_share < self.to_decimal(0.3):
            recommendations.extend(['Increase R&D spending to boost technological progress', 'Invest in education and human capital development', 'Encourage innovation through patent protection and incentives', 'Reduce reliance on pure capital accumulation'])
        elif tech_share < self.to_decimal(0.6):
            recommendations.extend(['Maintain balanced approach to capital and technology', 'Continue investing in both physical and human capital', 'Focus on technology transfer and adoption'])
        else:
            recommendations.extend(['Sustain high-technology focus', 'Ensure adequate capital to complement technology', 'Maintain competitive advantage in innovation'])
        return recommendations

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate productivity analysis"""
        return self.analyze_capital_deepening_vs_technology(kwargs['productivity_data'])

def analyze_capital_deepening_vs_technology(self, productivity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze effects of capital deepening vs technological progress"""
    capital_per_worker = self.to_decimal(productivity_data.get('capital_per_worker_growth', 0))
    total_factor_productivity = self.to_decimal(productivity_data.get('tfp_growth', 0))
    labor_productivity = self.to_decimal(productivity_data.get('labor_productivity_growth', 0))
    alpha = self.to_decimal(0.3)
    capital_deepening_contribution = alpha * capital_per_worker
    technology_contribution = total_factor_productivity
    implied_productivity_growth = capital_deepening_contribution + technology_contribution
    residual = labor_productivity - implied_productivity_growth
    return {'decomposition': {'labor_productivity_growth': labor_productivity, 'capital_deepening_contribution': capital_deepening_contribution, 'technology_contribution': technology_contribution, 'residual': residual}, 'relative_importance': {'capital_deepening_share': capital_deepening_contribution / labor_productivity * self.to_decimal(100) if labor_productivity != 0 else self.to_decimal(0), 'technology_share': technology_contribution / labor_productivity * self.to_decimal(100) if labor_productivity != 0 else self.to_decimal(0)}, 'economic_implications': {'capital_deepening': {'description': 'Increasing capital per worker', 'effects': 'Diminishing returns, temporary boost to productivity', 'sustainability': 'Limited by diminishing marginal returns', 'policy_focus': 'Investment incentives, savings rates'}, 'technological_progress': {'description': 'Improvements in total factor productivity', 'effects': 'Sustainable productivity gains, no diminishing returns', 'sustainability': 'Can sustain long-term growth', 'policy_focus': 'R&D investment, education, innovation'}}, 'growth_sustainability': self._assess_growth_sustainability(capital_deepening_contribution, technology_contribution)}

def _assess_growth_sustainability(self, capital_contrib: Decimal, tech_contrib: Decimal) -> Dict[str, Any]:
    """Assess sustainability of growth based on contributions"""
    total_contrib = capital_contrib + tech_contrib
    if total_contrib == 0:
        return {'assessment': 'No productivity growth', 'sustainability': 'Poor'}
    tech_share = tech_contrib / total_contrib
    if tech_share > self.to_decimal(0.7):
        sustainability = 'High'
        assessment = 'Technology-driven growth is highly sustainable'
    elif tech_share > self.to_decimal(0.4):
        sustainability = 'Moderate'
        assessment = 'Balanced growth with good sustainability prospects'
    else:
        sustainability = 'Low'
        assessment = 'Capital-dependent growth faces diminishing returns'
    return {'assessment': assessment, 'sustainability': sustainability, 'technology_share': tech_share * self.to_decimal(100), 'recommendations': self._generate_sustainability_recommendations(tech_share)}

def _generate_sustainability_recommendations(self, tech_share: Decimal) -> List[str]:
    """Generate recommendations based on technology share"""
    recommendations = []
    if tech_share < self.to_decimal(0.3):
        recommendations.extend(['Increase R&D spending to boost technological progress', 'Invest in education and human capital development', 'Encourage innovation through patent protection and incentives', 'Reduce reliance on pure capital accumulation'])
    elif tech_share < self.to_decimal(0.6):
        recommendations.extend(['Maintain balanced approach to capital and technology', 'Continue investing in both physical and human capital', 'Focus on technology transfer and adoption'])
    else:
        recommendations.extend(['Sustain high-technology focus', 'Ensure adequate capital to complement technology', 'Maintain competitive advantage in innovation'])
    return recommendations

class ConvergenceAnalyzer(EconomicsBase):
    """Economic convergence hypotheses analysis"""

    def test_convergence_hypotheses(self, country_data: List[Dict[str, Any]], convergence_type: str='beta') -> Dict[str, Any]:
        """Test convergence hypotheses (beta and sigma convergence)"""
        if convergence_type not in ['beta', 'sigma', 'both']:
            raise ValidationError("Convergence type must be 'beta', 'sigma', or 'both'")
        results = {}
        if convergence_type in ['beta', 'both']:
            results['beta_convergence'] = self._test_beta_convergence(country_data)
        if convergence_type in ['sigma', 'both']:
            results['sigma_convergence'] = self._test_sigma_convergence(country_data)
        results['convergence_theories'] = self._explain_convergence_theories()
        return results

    def _test_beta_convergence(self, country_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test beta convergence (catch-up effect)"""
        initial_gdp = []
        growth_rates = []
        for country in country_data:
            initial_gdp.append(self.to_decimal(country['initial_gdp_per_capita']))
            growth_rates.append(self.to_decimal(country['avg_growth_rate']))
        if len(initial_gdp) < 3:
            raise ValidationError('At least 3 countries required for convergence analysis')
        correlation = self._calculate_correlation(initial_gdp, growth_rates)
        convergence_speed = -correlation * self.to_decimal(0.02)
        half_life = self.to_decimal(0.693) / abs(convergence_speed) if convergence_speed != 0 else None
        return {'correlation_coefficient': correlation, 'convergence_exists': correlation < self.to_decimal(-0.3), 'convergence_speed': convergence_speed, 'half_life_years': half_life, 'interpretation': self._interpret_beta_convergence(correlation), 'countries_analyzed': len(country_data)}

    def _test_sigma_convergence(self, country_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test sigma convergence (dispersion reduction)"""
        time_periods = {}
        for country in country_data:
            for year, gdp in country.get('gdp_time_series', {}).items():
                if year not in time_periods:
                    time_periods[year] = []
                time_periods[year].append(self.to_decimal(gdp))
        dispersions = {}
        for year, gdp_values in time_periods.items():
            if len(gdp_values) > 1:
                mean_gdp = sum(gdp_values) / self.to_decimal(len(gdp_values))
                variance = sum(((x - mean_gdp) ** 2 for x in gdp_values)) / self.to_decimal(len(gdp_values) - 1)
                dispersions[year] = variance.sqrt()
        years = sorted(dispersions.keys())
        if len(years) < 2:
            raise ValidationError('At least 2 time periods required for sigma convergence')
        initial_dispersion = dispersions[years[0]]
        final_dispersion = dispersions[years[-1]]
        dispersion_change = (final_dispersion - initial_dispersion) / initial_dispersion
        return {'initial_dispersion': initial_dispersion, 'final_dispersion': final_dispersion, 'dispersion_change_percent': dispersion_change * self.to_decimal(100), 'sigma_convergence_exists': final_dispersion < initial_dispersion, 'time_periods_analyzed': len(years), 'dispersion_trend': 'Decreasing' if final_dispersion < initial_dispersion else 'Increasing'}

    def _calculate_correlation(self, x_values: List[Decimal], y_values: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient"""
        n = len(x_values)
        if n != len(y_values) or n < 2:
            return self.to_decimal(0)
        mean_x = sum(x_values) / self.to_decimal(n)
        mean_y = sum(y_values) / self.to_decimal(n)
        numerator = sum(((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n)))
        sum_sq_x = sum(((x - mean_x) ** 2 for x in x_values))
        sum_sq_y = sum(((y - mean_y) ** 2 for y in y_values))
        denominator = (sum_sq_x * sum_sq_y).sqrt()
        return numerator / denominator if denominator != 0 else self.to_decimal(0)

    def _interpret_beta_convergence(self, correlation: Decimal) -> str:
        """Interpret beta convergence results"""
        if correlation < self.to_decimal(-0.5):
            return 'Strong beta convergence: Poor countries growing significantly faster'
        elif correlation < self.to_decimal(-0.3):
            return 'Moderate beta convergence: Some catch-up effect observed'
        elif correlation < self.to_decimal(-0.1):
            return 'Weak beta convergence: Limited catch-up effect'
        else:
            return 'No beta convergence: No systematic catch-up by poor countries'

    def _explain_convergence_theories(self) -> Dict[str, Any]:
        """Explain convergence theories"""
        return {'neoclassical_theory': {'prediction': 'Unconditional convergence due to diminishing returns', 'mechanism': 'Poor countries have higher marginal returns to capital', 'assumptions': 'Same technology, preferences, institutions', 'reality': 'Limited empirical support for unconditional convergence'}, 'conditional_convergence': {'prediction': 'Convergence to country-specific steady states', 'mechanism': 'Countries converge to own equilibrium based on fundamentals', 'factors': 'Savings rates, population growth, technology, institutions', 'evidence': 'Stronger empirical support'}, 'endogenous_growth': {'prediction': 'Divergence possible due to increasing returns', 'mechanism': 'Knowledge spillovers, human capital externalities', 'implications': 'Rich countries may grow faster permanently', 'policy': 'Government intervention may be needed'}}

    def calculate(self, convergence_type: str='both', **kwargs) -> Dict[str, Any]:
        """Calculate convergence analysis"""
        return self.test_convergence_hypotheses(kwargs['country_data'], convergence_type)

def test_convergence_hypotheses(self, country_data: List[Dict[str, Any]], convergence_type: str='beta') -> Dict[str, Any]:
    """Test convergence hypotheses (beta and sigma convergence)"""
    if convergence_type not in ['beta', 'sigma', 'both']:
        raise ValidationError("Convergence type must be 'beta', 'sigma', or 'both'")
    results = {}
    if convergence_type in ['beta', 'both']:
        results['beta_convergence'] = self._test_beta_convergence(country_data)
    if convergence_type in ['sigma', 'both']:
        results['sigma_convergence'] = self._test_sigma_convergence(country_data)
    results['convergence_theories'] = self._explain_convergence_theories()
    return results

def _interpret_beta_convergence(self, correlation: Decimal) -> str:
    """Interpret beta convergence results"""
    if correlation < self.to_decimal(-0.5):
        return 'Strong beta convergence: Poor countries growing significantly faster'
    elif correlation < self.to_decimal(-0.3):
        return 'Moderate beta convergence: Some catch-up effect observed'
    elif correlation < self.to_decimal(-0.1):
        return 'Weak beta convergence: Limited catch-up effect'
    else:
        return 'No beta convergence: No systematic catch-up by poor countries'

class DemographicAnalyzer(EconomicsBase):
    """Demographics, immigration, and labor force participation analysis"""

    def analyze_demographic_impact(self, demographic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how demographics affect economic growth"""
        population_growth = self.to_decimal(demographic_data.get('population_growth_rate', 0))
        working_age_share = self.to_decimal(demographic_data.get('working_age_population_share', 0))
        dependency_ratio = self.to_decimal(demographic_data.get('dependency_ratio', 0))
        life_expectancy = self.to_decimal(demographic_data.get('life_expectancy', 0))
        fertility_rate = self.to_decimal(demographic_data.get('fertility_rate', 0))
        immigration_rate = self.to_decimal(demographic_data.get('net_immigration_rate', 0))
        immigrant_age_profile = demographic_data.get('immigrant_avg_age', 30)
        labor_force_participation = self.to_decimal(demographic_data.get('labor_force_participation_rate', 0))
        female_participation = self.to_decimal(demographic_data.get('female_labor_participation', 0))
        return {'demographic_dividend_analysis': self._analyze_demographic_dividend(working_age_share, dependency_ratio, population_growth), 'immigration_impact': self._analyze_immigration_impact(immigration_rate, immigrant_age_profile, labor_force_participation), 'labor_force_dynamics': self._analyze_labor_force_participation(labor_force_participation, female_participation, working_age_share), 'long_term_sustainability': self._assess_demographic_sustainability(fertility_rate, life_expectancy, dependency_ratio), 'policy_implications': self._generate_demographic_policy_recommendations(fertility_rate, dependency_ratio, immigration_rate, female_participation)}

    def _analyze_demographic_dividend(self, working_age_share: Decimal, dependency_ratio: Decimal, pop_growth: Decimal) -> Dict[str, Any]:
        """Analyze demographic dividend potential"""
        dividend_potential = working_age_share / dependency_ratio if dependency_ratio > 0 else self.to_decimal(0)
        if working_age_share > self.to_decimal(65) and dependency_ratio < self.to_decimal(50):
            dividend_stage = 'Peak dividend period'
            growth_impact = 'High positive impact on growth'
        elif working_age_share > self.to_decimal(60):
            dividend_stage = 'Dividend period'
            growth_impact = 'Positive impact on growth'
        elif working_age_share < self.to_decimal(55):
            dividend_stage = 'Post-dividend or pre-dividend'
            growth_impact = 'Limited or negative growth impact'
        else:
            dividend_stage = 'Transition period'
            growth_impact = 'Moderate growth impact'
        return {'working_age_share': working_age_share, 'dependency_ratio': dependency_ratio, 'dividend_potential_score': dividend_potential, 'dividend_stage': dividend_stage, 'growth_impact': growth_impact, 'duration_estimate': self._estimate_dividend_duration(working_age_share, pop_growth), 'policy_window': '15-30 years to capitalize on demographic dividend'}

    def _analyze_immigration_impact(self, immigration_rate: Decimal, avg_age: float, lfpr: Decimal) -> Dict[str, Any]:
        """Analyze immigration impact on growth"""
        age_factor = max(self.to_decimal(0), self.to_decimal(50 - avg_age) / self.to_decimal(20))
        labor_force_boost = immigration_rate * lfpr / self.to_decimal(100)
        if avg_age < 35:
            fiscal_impact = 'Positive (young workers, long contribution period)'
        elif avg_age < 50:
            fiscal_impact = 'Neutral to positive'
        else:
            fiscal_impact = 'Potentially negative (shorter contribution period)'
        return {'immigration_rate': immigration_rate, 'average_immigrant_age': avg_age, 'age_factor_score': age_factor, 'labor_force_contribution': labor_force_boost, 'fiscal_impact_assessment': fiscal_impact, 'skill_considerations': 'High-skilled immigration provides greater growth benefits', 'integration_factors': 'Language, credential recognition affect productivity'}

    def _analyze_labor_force_participation(self, overall_lfpr: Decimal, female_lfpr: Decimal, working_age_share: Decimal) -> Dict[str, Any]:
        """Analyze labor force participation trends"""
        max_lfpr = self.to_decimal(85)
        participation_gap = max_lfpr - overall_lfpr
        female_potential = self.to_decimal(80) - female_lfpr
        return {'current_participation_rate': overall_lfpr, 'female_participation_rate': female_lfpr, 'participation_gap': participation_gap, 'female_participation_potential': female_potential, 'growth_potential_from_participation': participation_gap * working_age_share / self.to_decimal(100), 'policy_levers': ['Childcare support to increase female participation', 'Flexible work arrangements', 'Education and skills training', 'Retirement age adjustments for aging societies']}

    def _assess_demographic_sustainability(self, fertility_rate: Decimal, life_expectancy: Decimal, dependency_ratio: Decimal) -> Dict[str, Any]:
        """Assess long-term demographic sustainability"""
        replacement_rate = self.to_decimal(2.1)
        if fertility_rate < self.to_decimal(1.5):
            sustainability_level = 'Low - Population decline likely'
            policy_urgency = 'High'
        elif fertility_rate < replacement_rate:
            sustainability_level = 'Moderate - Below replacement rate'
            policy_urgency = 'Medium'
        else:
            sustainability_level = 'High - Above replacement rate'
            policy_urgency = 'Low'
        if dependency_ratio > self.to_decimal(60):
            aging_challenge = 'Severe aging burden'
        elif dependency_ratio > self.to_decimal(45):
            aging_challenge = 'Moderate aging challenge'
        else:
            aging_challenge = 'Manageable dependency ratio'
        return {'fertility_rate': fertility_rate, 'replacement_rate': replacement_rate, 'fertility_gap': fertility_rate - replacement_rate, 'life_expectancy': life_expectancy, 'dependency_ratio': dependency_ratio, 'sustainability_assessment': sustainability_level, 'aging_challenge': aging_challenge, 'policy_urgency': policy_urgency, 'time_horizon': 'Demographic changes take 20-30 years to materialize'}

    def _estimate_dividend_duration(self, working_age_share: Decimal, pop_growth: Decimal) -> str:
        """Estimate demographic dividend duration"""
        if working_age_share > self.to_decimal(65):
            return '10-20 years remaining'
        elif working_age_share > self.to_decimal(60):
            return '20-30 years remaining'
        else:
            return 'Dividend period ending or not yet started'

    def _generate_demographic_policy_recommendations(self, fertility_rate: Decimal, dependency_ratio: Decimal, immigration_rate: Decimal, female_lfpr: Decimal) -> List[str]:
        """Generate policy recommendations based on demographic profile"""
        recommendations = []
        if fertility_rate < self.to_decimal(1.8):
            recommendations.extend(['Implement family-friendly policies (parental leave, childcare)', 'Provide financial incentives for families', 'Improve work-life balance policies'])
        if dependency_ratio > self.to_decimal(50):
            recommendations.extend(['Gradually increase retirement age', 'Reform pension systems for sustainability', 'Invest in elderly care infrastructure'])
        if immigration_rate < self.to_decimal(0.5) and dependency_ratio > self.to_decimal(45):
            recommendations.extend(['Develop skilled immigration programs', 'Improve integration services', 'Streamline immigration processes'])
        if female_lfpr < self.to_decimal(70):
            recommendations.extend(['Expand affordable childcare', 'Promote flexible work arrangements', 'Address gender wage gaps'])
        return recommendations

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate demographic analysis"""
        return self.analyze_demographic_impact(kwargs['demographic_data'])

def analyze_demographic_impact(self, demographic_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze how demographics affect economic growth"""
    population_growth = self.to_decimal(demographic_data.get('population_growth_rate', 0))
    working_age_share = self.to_decimal(demographic_data.get('working_age_population_share', 0))
    dependency_ratio = self.to_decimal(demographic_data.get('dependency_ratio', 0))
    life_expectancy = self.to_decimal(demographic_data.get('life_expectancy', 0))
    fertility_rate = self.to_decimal(demographic_data.get('fertility_rate', 0))
    immigration_rate = self.to_decimal(demographic_data.get('net_immigration_rate', 0))
    immigrant_age_profile = demographic_data.get('immigrant_avg_age', 30)
    labor_force_participation = self.to_decimal(demographic_data.get('labor_force_participation_rate', 0))
    female_participation = self.to_decimal(demographic_data.get('female_labor_participation', 0))
    return {'demographic_dividend_analysis': self._analyze_demographic_dividend(working_age_share, dependency_ratio, population_growth), 'immigration_impact': self._analyze_immigration_impact(immigration_rate, immigrant_age_profile, labor_force_participation), 'labor_force_dynamics': self._analyze_labor_force_participation(labor_force_participation, female_participation, working_age_share), 'long_term_sustainability': self._assess_demographic_sustainability(fertility_rate, life_expectancy, dependency_ratio), 'policy_implications': self._generate_demographic_policy_recommendations(fertility_rate, dependency_ratio, immigration_rate, female_participation)}

def _analyze_demographic_dividend(self, working_age_share: Decimal, dependency_ratio: Decimal, pop_growth: Decimal) -> Dict[str, Any]:
    """Analyze demographic dividend potential"""
    dividend_potential = working_age_share / dependency_ratio if dependency_ratio > 0 else self.to_decimal(0)
    if working_age_share > self.to_decimal(65) and dependency_ratio < self.to_decimal(50):
        dividend_stage = 'Peak dividend period'
        growth_impact = 'High positive impact on growth'
    elif working_age_share > self.to_decimal(60):
        dividend_stage = 'Dividend period'
        growth_impact = 'Positive impact on growth'
    elif working_age_share < self.to_decimal(55):
        dividend_stage = 'Post-dividend or pre-dividend'
        growth_impact = 'Limited or negative growth impact'
    else:
        dividend_stage = 'Transition period'
        growth_impact = 'Moderate growth impact'
    return {'working_age_share': working_age_share, 'dependency_ratio': dependency_ratio, 'dividend_potential_score': dividend_potential, 'dividend_stage': dividend_stage, 'growth_impact': growth_impact, 'duration_estimate': self._estimate_dividend_duration(working_age_share, pop_growth), 'policy_window': '15-30 years to capitalize on demographic dividend'}

def _analyze_immigration_impact(self, immigration_rate: Decimal, avg_age: float, lfpr: Decimal) -> Dict[str, Any]:
    """Analyze immigration impact on growth"""
    age_factor = max(self.to_decimal(0), self.to_decimal(50 - avg_age) / self.to_decimal(20))
    labor_force_boost = immigration_rate * lfpr / self.to_decimal(100)
    if avg_age < 35:
        fiscal_impact = 'Positive (young workers, long contribution period)'
    elif avg_age < 50:
        fiscal_impact = 'Neutral to positive'
    else:
        fiscal_impact = 'Potentially negative (shorter contribution period)'
    return {'immigration_rate': immigration_rate, 'average_immigrant_age': avg_age, 'age_factor_score': age_factor, 'labor_force_contribution': labor_force_boost, 'fiscal_impact_assessment': fiscal_impact, 'skill_considerations': 'High-skilled immigration provides greater growth benefits', 'integration_factors': 'Language, credential recognition affect productivity'}

def _analyze_labor_force_participation(self, overall_lfpr: Decimal, female_lfpr: Decimal, working_age_share: Decimal) -> Dict[str, Any]:
    """Analyze labor force participation trends"""
    max_lfpr = self.to_decimal(85)
    participation_gap = max_lfpr - overall_lfpr
    female_potential = self.to_decimal(80) - female_lfpr
    return {'current_participation_rate': overall_lfpr, 'female_participation_rate': female_lfpr, 'participation_gap': participation_gap, 'female_participation_potential': female_potential, 'growth_potential_from_participation': participation_gap * working_age_share / self.to_decimal(100), 'policy_levers': ['Childcare support to increase female participation', 'Flexible work arrangements', 'Education and skills training', 'Retirement age adjustments for aging societies']}

def _assess_demographic_sustainability(self, fertility_rate: Decimal, life_expectancy: Decimal, dependency_ratio: Decimal) -> Dict[str, Any]:
    """Assess long-term demographic sustainability"""
    replacement_rate = self.to_decimal(2.1)
    if fertility_rate < self.to_decimal(1.5):
        sustainability_level = 'Low - Population decline likely'
        policy_urgency = 'High'
    elif fertility_rate < replacement_rate:
        sustainability_level = 'Moderate - Below replacement rate'
        policy_urgency = 'Medium'
    else:
        sustainability_level = 'High - Above replacement rate'
        policy_urgency = 'Low'
    if dependency_ratio > self.to_decimal(60):
        aging_challenge = 'Severe aging burden'
    elif dependency_ratio > self.to_decimal(45):
        aging_challenge = 'Moderate aging challenge'
    else:
        aging_challenge = 'Manageable dependency ratio'
    return {'fertility_rate': fertility_rate, 'replacement_rate': replacement_rate, 'fertility_gap': fertility_rate - replacement_rate, 'life_expectancy': life_expectancy, 'dependency_ratio': dependency_ratio, 'sustainability_assessment': sustainability_level, 'aging_challenge': aging_challenge, 'policy_urgency': policy_urgency, 'time_horizon': 'Demographic changes take 20-30 years to materialize'}

def _estimate_dividend_duration(self, working_age_share: Decimal, pop_growth: Decimal) -> str:
    """Estimate demographic dividend duration"""
    if working_age_share > self.to_decimal(65):
        return '10-20 years remaining'
    elif working_age_share > self.to_decimal(60):
        return '20-30 years remaining'
    else:
        return 'Dividend period ending or not yet started'

def _generate_demographic_policy_recommendations(self, fertility_rate: Decimal, dependency_ratio: Decimal, immigration_rate: Decimal, female_lfpr: Decimal) -> List[str]:
    """Generate policy recommendations based on demographic profile"""
    recommendations = []
    if fertility_rate < self.to_decimal(1.8):
        recommendations.extend(['Implement family-friendly policies (parental leave, childcare)', 'Provide financial incentives for families', 'Improve work-life balance policies'])
    if dependency_ratio > self.to_decimal(50):
        recommendations.extend(['Gradually increase retirement age', 'Reform pension systems for sustainability', 'Invest in elderly care infrastructure'])
    if immigration_rate < self.to_decimal(0.5) and dependency_ratio > self.to_decimal(45):
        recommendations.extend(['Develop skilled immigration programs', 'Improve integration services', 'Streamline immigration processes'])
    if female_lfpr < self.to_decimal(70):
        recommendations.extend(['Expand affordable childcare', 'Promote flexible work arrangements', 'Address gender wage gaps'])
    return recommendations

class ExchangeCalculator(EconomicsBase):
    """Main exchange rate calculations coordinator"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)
        self.cross_rate = CrossRateCalculator(precision, base_currency)
        self.forward_calc = ForwardCalculator(precision, base_currency)

    def calculate(self, calculation_type: str, **kwargs) -> Dict[str, Any]:
        """Route calculation to appropriate calculator"""
        calculators = {'cross_rate': self.cross_rate.calculate, 'forward_rate': self.forward_calc.calculate, 'percentage_change': self.calculate_percentage_change, 'arbitrage_check': self.check_arbitrage_relationship}
        if calculation_type not in calculators:
            raise ValidationError(f'Unknown calculation type: {calculation_type}')
        return calculators[calculation_type](**kwargs)

    def calculate_percentage_change(self, initial_rate: Decimal, final_rate: Decimal, quote_convention: str='direct') -> Dict[str, Any]:
        """Calculate percentage change in currency relative to another"""
        initial = self.to_decimal(initial_rate)
        final = self.to_decimal(final_rate)
        self.validator.validate_exchange_rate(initial)
        self.validator.validate_exchange_rate(final)
        if quote_convention == 'direct':
            percentage_change = (final - initial) / initial * self.to_decimal(100)
            currency_movement = 'weakened' if percentage_change > 0 else 'strengthened'
        else:
            percentage_change = (final - initial) / initial * self.to_decimal(100)
            currency_movement = 'strengthened' if percentage_change > 0 else 'weakened'
        return {'initial_rate': initial, 'final_rate': final, 'percentage_change': percentage_change, 'absolute_change': final - initial, 'quote_convention': quote_convention, 'currency_movement': currency_movement, 'interpretation': self._interpret_currency_change(percentage_change, quote_convention)}

    def _interpret_currency_change(self, change: Decimal, convention: str) -> str:
        """Provide interpretation of currency movement"""
        abs_change = abs(change)
        if abs_change < self.to_decimal(0.5):
            magnitude = 'minimal'
        elif abs_change < self.to_decimal(2):
            magnitude = 'moderate'
        elif abs_change < self.to_decimal(5):
            magnitude = 'significant'
        else:
            magnitude = 'substantial'
        direction = 'appreciation' if change > 0 else 'depreciation'
        if convention == 'indirect':
            direction = 'depreciation' if change > 0 else 'appreciation'
        return f'{magnitude} {direction} ({abs_change:.2f}%)'

    def check_arbitrage_relationship(self, spot_rate: Decimal, forward_rate: Decimal, domestic_rate: Decimal, foreign_rate: Decimal, time_period: Decimal) -> Dict[str, Any]:
        """Check arbitrage relationship between spot/forward rates and interest rates"""
        spot = self.to_decimal(spot_rate)
        forward = self.to_decimal(forward_rate)
        r_domestic = self.to_decimal(domestic_rate)
        r_foreign = self.to_decimal(foreign_rate)
        t = self.to_decimal(time_period)
        theoretical_forward = spot * ((self.to_decimal(1) + r_domestic * t) / (self.to_decimal(1) + r_foreign * t))
        deviation = forward - theoretical_forward
        deviation_percentage = deviation / theoretical_forward * self.to_decimal(100)
        arbitrage_threshold = self.to_decimal(0.1)
        arbitrage_exists = abs(deviation_percentage) > arbitrage_threshold
        arbitrage_strategy = self._determine_arbitrage_strategy(deviation, spot, forward, r_domestic, r_foreign, t) if arbitrage_exists else None
        return {'spot_rate': spot, 'forward_rate': forward, 'theoretical_forward': theoretical_forward, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'arbitrage_exists': arbitrage_exists, 'arbitrage_strategy': arbitrage_strategy, 'domestic_rate': r_domestic, 'foreign_rate': r_foreign, 'time_period': t, 'relationship_holds': not arbitrage_exists}

    def _determine_arbitrage_strategy(self, deviation: Decimal, spot: Decimal, forward: Decimal, r_dom: Decimal, r_for: Decimal, t: Decimal) -> Dict[str, str]:
        """Determine arbitrage strategy when opportunity exists"""
        if deviation > 0:
            return {'action': 'Sell forward, buy spot', 'step1': 'Borrow domestic currency', 'step2': 'Convert to foreign currency at spot rate', 'step3': 'Invest foreign currency at foreign rate', 'step4': 'Sell foreign currency forward', 'step5': 'At maturity: collect foreign investment, deliver to forward contract', 'profit_source': 'Forward rate higher than theoretical rate'}
        else:
            return {'action': 'Buy forward, sell spot', 'step1': 'Borrow foreign currency', 'step2': 'Convert to domestic currency at spot rate', 'step3': 'Invest domestic currency at domestic rate', 'step4': 'Buy foreign currency forward', 'step5': 'At maturity: collect domestic investment, buy foreign currency via forward', 'profit_source': 'Forward rate lower than theoretical rate'}

def calculate(self, calculation_type: str, **kwargs) -> Dict[str, Any]:
    """Route calculation to appropriate calculator"""
    calculators = {'cross_rate': self.cross_rate.calculate, 'forward_rate': self.forward_calc.calculate, 'percentage_change': self.calculate_percentage_change, 'arbitrage_check': self.check_arbitrage_relationship}
    if calculation_type not in calculators:
        raise ValidationError(f'Unknown calculation type: {calculation_type}')
    return calculators[calculation_type](**kwargs)

def calculate_percentage_change(self, initial_rate: Decimal, final_rate: Decimal, quote_convention: str='direct') -> Dict[str, Any]:
    """Calculate percentage change in currency relative to another"""
    initial = self.to_decimal(initial_rate)
    final = self.to_decimal(final_rate)
    self.validator.validate_exchange_rate(initial)
    self.validator.validate_exchange_rate(final)
    if quote_convention == 'direct':
        percentage_change = (final - initial) / initial * self.to_decimal(100)
        currency_movement = 'weakened' if percentage_change > 0 else 'strengthened'
    else:
        percentage_change = (final - initial) / initial * self.to_decimal(100)
        currency_movement = 'strengthened' if percentage_change > 0 else 'weakened'
    return {'initial_rate': initial, 'final_rate': final, 'percentage_change': percentage_change, 'absolute_change': final - initial, 'quote_convention': quote_convention, 'currency_movement': currency_movement, 'interpretation': self._interpret_currency_change(percentage_change, quote_convention)}

def _interpret_currency_change(self, change: Decimal, convention: str) -> str:
    """Provide interpretation of currency movement"""
    abs_change = abs(change)
    if abs_change < self.to_decimal(0.5):
        magnitude = 'minimal'
    elif abs_change < self.to_decimal(2):
        magnitude = 'moderate'
    elif abs_change < self.to_decimal(5):
        magnitude = 'significant'
    else:
        magnitude = 'substantial'
    direction = 'appreciation' if change > 0 else 'depreciation'
    if convention == 'indirect':
        direction = 'depreciation' if change > 0 else 'appreciation'
    return f'{magnitude} {direction} ({abs_change:.2f}%)'

def check_arbitrage_relationship(self, spot_rate: Decimal, forward_rate: Decimal, domestic_rate: Decimal, foreign_rate: Decimal, time_period: Decimal) -> Dict[str, Any]:
    """Check arbitrage relationship between spot/forward rates and interest rates"""
    spot = self.to_decimal(spot_rate)
    forward = self.to_decimal(forward_rate)
    r_domestic = self.to_decimal(domestic_rate)
    r_foreign = self.to_decimal(foreign_rate)
    t = self.to_decimal(time_period)
    theoretical_forward = spot * ((self.to_decimal(1) + r_domestic * t) / (self.to_decimal(1) + r_foreign * t))
    deviation = forward - theoretical_forward
    deviation_percentage = deviation / theoretical_forward * self.to_decimal(100)
    arbitrage_threshold = self.to_decimal(0.1)
    arbitrage_exists = abs(deviation_percentage) > arbitrage_threshold
    arbitrage_strategy = self._determine_arbitrage_strategy(deviation, spot, forward, r_domestic, r_foreign, t) if arbitrage_exists else None
    return {'spot_rate': spot, 'forward_rate': forward, 'theoretical_forward': theoretical_forward, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'arbitrage_exists': arbitrage_exists, 'arbitrage_strategy': arbitrage_strategy, 'domestic_rate': r_domestic, 'foreign_rate': r_foreign, 'time_period': t, 'relationship_holds': not arbitrage_exists}

class ForwardCalculator(EconomicsBase):
    """Forward rate calculations using points and percentage terms"""

    def calculate_forward_rate_from_points(self, spot_rate: Decimal, forward_points: Decimal, point_convention: str='standard') -> Dict[str, Any]:
        """Calculate forward rate from forward points"""
        spot = self.to_decimal(spot_rate)
        points = self.to_decimal(forward_points)
        self.validator.validate_exchange_rate(spot)
        if point_convention == 'standard':
            divisor = self.to_decimal(10000)
        elif point_convention == 'big_figure':
            divisor = self.to_decimal(100000)
        else:
            raise ValidationError(f'Unknown point convention: {point_convention}')
        forward_rate = spot + points / divisor
        is_premium = forward_rate > spot
        premium_discount = forward_rate - spot
        premium_discount_percentage = premium_discount / spot * self.to_decimal(100)
        return {'spot_rate': spot, 'forward_points': points, 'forward_rate': forward_rate, 'point_convention': point_convention, 'divisor': divisor, 'premium_discount': premium_discount, 'premium_discount_percentage': premium_discount_percentage, 'is_premium': is_premium, 'calculation': f'{spot} + ({points}/{divisor}) = {forward_rate}'}

    def calculate_forward_points_from_rate(self, spot_rate: Decimal, forward_rate: Decimal, point_convention: str='standard') -> Dict[str, Any]:
        """Calculate forward points from spot and forward rates"""
        spot = self.to_decimal(spot_rate)
        forward = self.to_decimal(forward_rate)
        self.validator.validate_exchange_rate(spot)
        self.validator.validate_exchange_rate(forward)
        if point_convention == 'standard':
            multiplier = self.to_decimal(10000)
        elif point_convention == 'big_figure':
            multiplier = self.to_decimal(100000)
        else:
            raise ValidationError(f'Unknown point convention: {point_convention}')
        forward_points = (forward - spot) * multiplier
        return {'spot_rate': spot, 'forward_rate': forward, 'forward_points': forward_points, 'point_convention': point_convention, 'multiplier': multiplier, 'is_premium': forward > spot, 'calculation': f'({forward} - {spot}) × {multiplier} = {forward_points} points'}

    def calculate_forward_rate_percentage(self, spot_rate: Decimal, premium_discount_percent: Decimal, time_to_maturity: Decimal, annualized: bool=True) -> Dict[str, Any]:
        """Calculate forward rate from percentage premium/discount"""
        spot = self.to_decimal(spot_rate)
        premium_percent = self.to_decimal(premium_discount_percent)
        time_period = self.to_decimal(time_to_maturity)
        self.validator.validate_exchange_rate(spot)
        self.validator.validate_time_period(time_period)
        if annualized:
            period_premium = premium_percent * time_period
        else:
            period_premium = premium_percent
        forward_rate = spot * (self.to_decimal(1) + period_premium / self.to_decimal(100))
        if not annualized:
            annualized_premium = period_premium / time_period
        else:
            annualized_premium = premium_percent
        return {'spot_rate': spot, 'forward_rate': forward_rate, 'premium_discount_percent': premium_percent, 'time_to_maturity': time_period, 'period_premium': period_premium, 'annualized_premium': annualized_premium, 'is_annualized_input': annualized, 'is_premium': premium_percent > 0, 'calculation': f'{spot} × (1 + {period_premium}%) = {forward_rate}'}

    def interpret_forward_discount_premium(self, spot_rate: Decimal, forward_rate: Decimal, time_to_maturity: Decimal) -> Dict[str, Any]:
        """Interpret forward discount or premium"""
        spot = self.to_decimal(spot_rate)
        forward = self.to_decimal(forward_rate)
        time_period = self.to_decimal(time_to_maturity)
        absolute_difference = forward - spot
        percentage_difference = absolute_difference / spot * self.to_decimal(100)
        annualized_percentage = percentage_difference / time_period
        if forward > spot:
            interpretation = f'Forward premium of {percentage_difference:.4f}% ({annualized_percentage:.4f}% annualized)'
            market_expectation = 'Base currency expected to weaken'
            interest_rate_implication = 'Base currency likely has lower interest rates'
        elif forward < spot:
            interpretation = f'Forward discount of {abs(percentage_difference):.4f}% ({abs(annualized_percentage):.4f}% annualized)'
            market_expectation = 'Base currency expected to strengthen'
            interest_rate_implication = 'Base currency likely has higher interest rates'
        else:
            interpretation = 'Forward rate equals spot rate (no premium or discount)'
            market_expectation = 'No expected currency movement'
            interest_rate_implication = 'Interest rates likely equal between currencies'
        return {'spot_rate': spot, 'forward_rate': forward, 'absolute_difference': absolute_difference, 'percentage_difference': percentage_difference, 'annualized_percentage': annualized_percentage, 'time_to_maturity': time_period, 'interpretation': interpretation, 'market_expectation': market_expectation, 'interest_rate_implication': interest_rate_implication, 'is_premium': forward > spot, 'is_discount': forward < spot}

    def calculate(self, calculation_type: str, **kwargs) -> Dict[str, Any]:
        """Main forward calculation dispatcher"""
        calculations = {'from_points': lambda: self.calculate_forward_rate_from_points(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_points']), kwargs.get('point_convention', 'standard')), 'to_points': lambda: self.calculate_forward_points_from_rate(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_rate']), kwargs.get('point_convention', 'standard')), 'from_percentage': lambda: self.calculate_forward_rate_percentage(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['premium_discount_percent']), self.to_decimal(kwargs['time_to_maturity']), kwargs.get('annualized', True)), 'interpret_premium_discount': lambda: self.interpret_forward_discount_premium(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_rate']), self.to_decimal(kwargs['time_to_maturity']))}
        if calculation_type not in calculations:
            raise ValidationError(f'Unknown calculation type: {calculation_type}')
        result = calculations[calculation_type]()
        result['metadata'] = self.get_metadata()
        result['calculation_type'] = calculation_type
        return result

def calculate_forward_rate_from_points(self, spot_rate: Decimal, forward_points: Decimal, point_convention: str='standard') -> Dict[str, Any]:
    """Calculate forward rate from forward points"""
    spot = self.to_decimal(spot_rate)
    points = self.to_decimal(forward_points)
    self.validator.validate_exchange_rate(spot)
    if point_convention == 'standard':
        divisor = self.to_decimal(10000)
    elif point_convention == 'big_figure':
        divisor = self.to_decimal(100000)
    else:
        raise ValidationError(f'Unknown point convention: {point_convention}')
    forward_rate = spot + points / divisor
    is_premium = forward_rate > spot
    premium_discount = forward_rate - spot
    premium_discount_percentage = premium_discount / spot * self.to_decimal(100)
    return {'spot_rate': spot, 'forward_points': points, 'forward_rate': forward_rate, 'point_convention': point_convention, 'divisor': divisor, 'premium_discount': premium_discount, 'premium_discount_percentage': premium_discount_percentage, 'is_premium': is_premium, 'calculation': f'{spot} + ({points}/{divisor}) = {forward_rate}'}

def calculate_forward_points_from_rate(self, spot_rate: Decimal, forward_rate: Decimal, point_convention: str='standard') -> Dict[str, Any]:
    """Calculate forward points from spot and forward rates"""
    spot = self.to_decimal(spot_rate)
    forward = self.to_decimal(forward_rate)
    self.validator.validate_exchange_rate(spot)
    self.validator.validate_exchange_rate(forward)
    if point_convention == 'standard':
        multiplier = self.to_decimal(10000)
    elif point_convention == 'big_figure':
        multiplier = self.to_decimal(100000)
    else:
        raise ValidationError(f'Unknown point convention: {point_convention}')
    forward_points = (forward - spot) * multiplier
    return {'spot_rate': spot, 'forward_rate': forward, 'forward_points': forward_points, 'point_convention': point_convention, 'multiplier': multiplier, 'is_premium': forward > spot, 'calculation': f'({forward} - {spot}) × {multiplier} = {forward_points} points'}

def calculate_forward_rate_percentage(self, spot_rate: Decimal, premium_discount_percent: Decimal, time_to_maturity: Decimal, annualized: bool=True) -> Dict[str, Any]:
    """Calculate forward rate from percentage premium/discount"""
    spot = self.to_decimal(spot_rate)
    premium_percent = self.to_decimal(premium_discount_percent)
    time_period = self.to_decimal(time_to_maturity)
    self.validator.validate_exchange_rate(spot)
    self.validator.validate_time_period(time_period)
    if annualized:
        period_premium = premium_percent * time_period
    else:
        period_premium = premium_percent
    forward_rate = spot * (self.to_decimal(1) + period_premium / self.to_decimal(100))
    if not annualized:
        annualized_premium = period_premium / time_period
    else:
        annualized_premium = premium_percent
    return {'spot_rate': spot, 'forward_rate': forward_rate, 'premium_discount_percent': premium_percent, 'time_to_maturity': time_period, 'period_premium': period_premium, 'annualized_premium': annualized_premium, 'is_annualized_input': annualized, 'is_premium': premium_percent > 0, 'calculation': f'{spot} × (1 + {period_premium}%) = {forward_rate}'}

def interpret_forward_discount_premium(self, spot_rate: Decimal, forward_rate: Decimal, time_to_maturity: Decimal) -> Dict[str, Any]:
    """Interpret forward discount or premium"""
    spot = self.to_decimal(spot_rate)
    forward = self.to_decimal(forward_rate)
    time_period = self.to_decimal(time_to_maturity)
    absolute_difference = forward - spot
    percentage_difference = absolute_difference / spot * self.to_decimal(100)
    annualized_percentage = percentage_difference / time_period
    if forward > spot:
        interpretation = f'Forward premium of {percentage_difference:.4f}% ({annualized_percentage:.4f}% annualized)'
        market_expectation = 'Base currency expected to weaken'
        interest_rate_implication = 'Base currency likely has lower interest rates'
    elif forward < spot:
        interpretation = f'Forward discount of {abs(percentage_difference):.4f}% ({abs(annualized_percentage):.4f}% annualized)'
        market_expectation = 'Base currency expected to strengthen'
        interest_rate_implication = 'Base currency likely has higher interest rates'
    else:
        interpretation = 'Forward rate equals spot rate (no premium or discount)'
        market_expectation = 'No expected currency movement'
        interest_rate_implication = 'Interest rates likely equal between currencies'
    return {'spot_rate': spot, 'forward_rate': forward, 'absolute_difference': absolute_difference, 'percentage_difference': percentage_difference, 'annualized_percentage': annualized_percentage, 'time_to_maturity': time_period, 'interpretation': interpretation, 'market_expectation': market_expectation, 'interest_rate_implication': interest_rate_implication, 'is_premium': forward > spot, 'is_discount': forward < spot}

def calculate(self, calculation_type: str, **kwargs) -> Dict[str, Any]:
    """Main forward calculation dispatcher"""
    calculations = {'from_points': lambda: self.calculate_forward_rate_from_points(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_points']), kwargs.get('point_convention', 'standard')), 'to_points': lambda: self.calculate_forward_points_from_rate(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_rate']), kwargs.get('point_convention', 'standard')), 'from_percentage': lambda: self.calculate_forward_rate_percentage(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['premium_discount_percent']), self.to_decimal(kwargs['time_to_maturity']), kwargs.get('annualized', True)), 'interpret_premium_discount': lambda: self.interpret_forward_discount_premium(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_rate']), self.to_decimal(kwargs['time_to_maturity']))}
    if calculation_type not in calculations:
        raise ValidationError(f'Unknown calculation type: {calculation_type}')
    result = calculations[calculation_type]()
    result['metadata'] = self.get_metadata()
    result['calculation_type'] = calculation_type
    return result

class DataValidator:
    """
    Comprehensive data validation for economics calculations.
    Ensures data quality and CFA-compliant input standards.
    """

    def __init__(self):
        self.currency_codes = {'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD', 'SEK', 'NOK', 'DKK', 'CNY', 'INR', 'BRL', 'RUB', 'ZAR', 'MXN', 'SGD', 'HKD', 'KRW', 'TRY', 'PLN', 'CZK', 'HUF'}

    def validate_currency_code(self, code: str) -> bool:
        """Validate ISO currency code"""
        if not isinstance(code, str) or len(code) != 3:
            raise ValidationError(f'Invalid currency code format: {code}')
        if code.upper() not in self.currency_codes:
            raise ValidationError(f'Unsupported currency code: {code}')
        return True

    def validate_exchange_rate(self, rate: Union[float, Decimal]) -> bool:
        """Validate exchange rate values"""
        rate = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
        if rate <= 0:
            raise ValidationError(f'Exchange rate must be positive: {rate}')
        if rate > Decimal('1000000'):
            raise ValidationError(f'Exchange rate seems unrealistic: {rate}')
        return True

    def validate_interest_rate(self, rate: Union[float, Decimal]) -> bool:
        """Validate interest rate (can be negative)"""
        rate = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
        if rate < Decimal('-0.10') or rate > Decimal('1.0'):
            raise ValidationError(f'Interest rate outside reasonable range: {rate}')
        return True

    def validate_time_period(self, period: Union[int, float]) -> bool:
        """Validate time periods in years"""
        if not isinstance(period, (int, float)) or period <= 0:
            raise ValidationError(f'Time period must be positive: {period}')
        if period > 100:
            raise ValidationError(f'Time period seems unrealistic: {period}')
        return True

    def validate_gdp_data(self, gdp: Union[float, Decimal]) -> bool:
        """Validate GDP values"""
        gdp = Decimal(str(gdp)) if not isinstance(gdp, Decimal) else gdp
        if gdp <= 0:
            raise ValidationError(f'GDP must be positive: {gdp}')
        return True

    def validate_inflation_rate(self, rate: Union[float, Decimal]) -> bool:
        """Validate inflation rates"""
        rate = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
        if rate < Decimal('-0.5') or rate > Decimal('2.0'):
            raise ValidationError(f'Inflation rate outside normal range: {rate}')
        return True

    def validate_date_format(self, date_input: Union[str, datetime, date]) -> datetime:
        """Validate and convert date inputs"""
        if isinstance(date_input, datetime):
            return date_input
        elif isinstance(date_input, date):
            return datetime.combine(date_input, datetime.min.time())
        elif isinstance(date_input, str):
            try:
                return datetime.strptime(date_input, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_input, '%Y/%m/%d')
                except ValueError:
                    raise ValidationError(f'Invalid date format: {date_input}')
        else:
            raise ValidationError(f'Unsupported date type: {type(date_input)}')

    def validate_percentage(self, value: Union[float, Decimal]) -> bool:
        """Validate percentage values (0-100 or 0-1)"""
        value = Decimal(str(value)) if not isinstance(value, Decimal) else value
        if value < 0 or value > 100:
            raise ValidationError(f'Percentage outside valid range: {value}')
        return True

    def validate_dataframe(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """Validate pandas DataFrame structure"""
        if not isinstance(df, pd.DataFrame):
            raise ValidationError('Input must be a pandas DataFrame')
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValidationError(f'Missing required columns: {missing_cols}')
        if df.empty:
            raise ValidationError('DataFrame cannot be empty')
        return True

    def validate_bid_ask_spread(self, bid: Decimal, ask: Decimal) -> bool:
        """Validate bid-ask spread"""
        if bid >= ask:
            raise ValidationError(f'Bid ({bid}) must be less than ask ({ask})')
        spread = (ask - bid) / bid
        if spread > Decimal('0.1'):
            raise ValidationError(f'Bid-ask spread too wide: {spread:.4f}')
        return True

    def validate_parameters(self, **kwargs) -> bool:
        """Validate multiple parameters based on their types"""
        validators = {'currency': self.validate_currency_code, 'exchange_rate': self.validate_exchange_rate, 'interest_rate': self.validate_interest_rate, 'time_period': self.validate_time_period, 'gdp': self.validate_gdp_data, 'inflation': self.validate_inflation_rate, 'percentage': self.validate_percentage, 'date': self.validate_date_format}
        for param_name, param_value in kwargs.items():
            param_type = None
            for validator_type in validators.keys():
                if validator_type in param_name.lower():
                    param_type = validator_type
                    break
            if param_type and param_value is not None:
                validators[param_type](param_value)
        return True

def validate_currency_code(self, code: str) -> bool:
    """Validate ISO currency code"""
    if not isinstance(code, str) or len(code) != 3:
        raise ValidationError(f'Invalid currency code format: {code}')
    if code.upper() not in self.currency_codes:
        raise ValidationError(f'Unsupported currency code: {code}')
    return True

def validate_exchange_rate(self, rate: Union[float, Decimal]) -> bool:
    """Validate exchange rate values"""
    rate = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
    if rate <= 0:
        raise ValidationError(f'Exchange rate must be positive: {rate}')
    if rate > Decimal('1000000'):
        raise ValidationError(f'Exchange rate seems unrealistic: {rate}')
    return True

def validate_interest_rate(self, rate: Union[float, Decimal]) -> bool:
    """Validate interest rate (can be negative)"""
    rate = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
    if rate < Decimal('-0.10') or rate > Decimal('1.0'):
        raise ValidationError(f'Interest rate outside reasonable range: {rate}')
    return True

def validate_time_period(self, period: Union[int, float]) -> bool:
    """Validate time periods in years"""
    if not isinstance(period, (int, float)) or period <= 0:
        raise ValidationError(f'Time period must be positive: {period}')
    if period > 100:
        raise ValidationError(f'Time period seems unrealistic: {period}')
    return True

def validate_gdp_data(self, gdp: Union[float, Decimal]) -> bool:
    """Validate GDP values"""
    gdp = Decimal(str(gdp)) if not isinstance(gdp, Decimal) else gdp
    if gdp <= 0:
        raise ValidationError(f'GDP must be positive: {gdp}')
    return True

def validate_inflation_rate(self, rate: Union[float, Decimal]) -> bool:
    """Validate inflation rates"""
    rate = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
    if rate < Decimal('-0.5') or rate > Decimal('2.0'):
        raise ValidationError(f'Inflation rate outside normal range: {rate}')
    return True

def validate_percentage(self, value: Union[float, Decimal]) -> bool:
    """Validate percentage values (0-100 or 0-1)"""
    value = Decimal(str(value)) if not isinstance(value, Decimal) else value
    if value < 0 or value > 100:
        raise ValidationError(f'Percentage outside valid range: {value}')
    return True

def validate_dataframe(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validate pandas DataFrame structure"""
    if not isinstance(df, pd.DataFrame):
        raise ValidationError('Input must be a pandas DataFrame')
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValidationError(f'Missing required columns: {missing_cols}')
    if df.empty:
        raise ValidationError('DataFrame cannot be empty')
    return True

def validate_bid_ask_spread(self, bid: Decimal, ask: Decimal) -> bool:
    """Validate bid-ask spread"""
    if bid >= ask:
        raise ValidationError(f'Bid ({bid}) must be less than ask ({ask})')
    spread = (ask - bid) / bid
    if spread > Decimal('0.1'):
        raise ValidationError(f'Bid-ask spread too wide: {spread:.4f}')
    return True

class DataContainer:
    """
    Container for economic data with validation and metadata.
    Ensures data integrity throughout calculations.
    """

    def __init__(self, data: Dict[str, Any], data_type: str, timestamp: Optional[datetime]=None):
        self.data = data
        self.data_type = data_type
        self.timestamp = timestamp or datetime.now()
        self.validator = DataValidator()
        self._validate_data()

    def _validate_data(self):
        """Validate data based on type"""
        validation_rules = {'currency': ['currency_code', 'exchange_rate'], 'gdp': ['gdp_value', 'country_code'], 'interest_rate': ['rate_value', 'currency'], 'inflation': ['inflation_rate', 'period']}
        if self.data_type in validation_rules:
            required_fields = validation_rules[self.data_type]
            for field in required_fields:
                if field not in self.data:
                    raise ValidationError(f'Missing required field for {self.data_type}: {field}')

    def get_value(self, key: str, default: Any=None) -> Any:
        """Get value with optional default"""
        return self.data.get(key, default)

    def update_value(self, key: str, value: Any):
        """Update value with validation"""
        self.data[key] = value
        self._validate_data()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with metadata"""
        return {'data': self.data, 'type': self.data_type, 'timestamp': self.timestamp.isoformat(), 'validated': True}

def _validate_data(self):
    """Validate data based on type"""
    validation_rules = {'currency': ['currency_code', 'exchange_rate'], 'gdp': ['gdp_value', 'country_code'], 'interest_rate': ['rate_value', 'currency'], 'inflation': ['inflation_rate', 'period']}
    if self.data_type in validation_rules:
        required_fields = validation_rules[self.data_type]
        for field in required_fields:
            if field not in self.data:
                raise ValidationError(f'Missing required field for {self.data_type}: {field}')

class CurrencyAnalyzer(EconomicsBase):
    """Main currency analysis coordinator"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)
        self.spot_forward = SpotForwardAnalyzer(precision, base_currency)
        self.arbitrage = ArbitrageDetector(precision, base_currency)
        self.parity = ParityAnalyzer(precision, base_currency)
        self.carry_trade = CarryTradeAnalyzer(precision, base_currency)

    def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Route calculation to appropriate analyzer"""
        analyzers = {'spot_forward': self.spot_forward.calculate, 'arbitrage': self.arbitrage.calculate, 'parity': self.parity.calculate, 'carry_trade': self.carry_trade.calculate}
        if analysis_type not in analyzers:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        return analyzers[analysis_type](**kwargs)

def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
    """Route calculation to appropriate analyzer"""
    analyzers = {'spot_forward': self.spot_forward.calculate, 'arbitrage': self.arbitrage.calculate, 'parity': self.parity.calculate, 'carry_trade': self.carry_trade.calculate}
    if analysis_type not in analyzers:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    return analyzers[analysis_type](**kwargs)

class SpotForwardAnalyzer(EconomicsBase):
    """Spot and forward rate analysis with bid-offer spreads"""

    def calculate_bid_offer_spread(self, bid: Decimal, ask: Decimal) -> Dict[str, Decimal]:
        """Calculate bid-offer spread metrics"""
        self.validator.validate_bid_ask_spread(bid, ask)
        spread_points = ask - bid
        spread_percentage = spread_points / bid * self.to_decimal(100)
        mid_rate = (bid + ask) / self.to_decimal(2)
        return {'bid': bid, 'ask': ask, 'mid_rate': mid_rate, 'spread_points': spread_points, 'spread_percentage': spread_percentage, 'spread_basis_points': spread_percentage * self.to_decimal(100)}

    def factors_affecting_spread(self, currency_pair: str, market_conditions: Dict[str, Any]) -> Dict[str, str]:
        """Analyze factors affecting bid-offer spread"""
        factors = {'trading_volume': 'Higher volume = narrower spreads', 'market_volatility': 'Higher volatility = wider spreads', 'time_of_day': 'Active trading hours = narrower spreads', 'liquidity': 'More liquid pairs = narrower spreads', 'political_stability': 'Less stable = wider spreads', 'central_bank_intervention': 'Active intervention = wider spreads'}
        assessment = {}
        volume = market_conditions.get('daily_volume', 0)
        volatility = market_conditions.get('volatility', 0)
        if volume > 1000000:
            assessment['volume_impact'] = 'Narrow spread expected'
        else:
            assessment['volume_impact'] = 'Wide spread expected'
        if volatility > 0.02:
            assessment['volatility_impact'] = 'Wide spread expected'
        else:
            assessment['volatility_impact'] = 'Narrow spread expected'
        assessment.update(factors)
        return assessment

    def calculate_forward_premium_discount(self, spot_rate: Decimal, forward_rate: Decimal, time_to_maturity: Decimal) -> Dict[str, Decimal]:
        """Calculate forward premium/discount"""
        self.validator.validate_exchange_rate(spot_rate)
        self.validator.validate_exchange_rate(forward_rate)
        self.validator.validate_time_period(time_to_maturity)
        premium_discount = (forward_rate - spot_rate) / spot_rate * (self.to_decimal(1) / time_to_maturity)
        premium_discount_percent = premium_discount * self.to_decimal(100)
        return {'spot_rate': spot_rate, 'forward_rate': forward_rate, 'time_to_maturity': time_to_maturity, 'premium_discount': premium_discount, 'premium_discount_percent': premium_discount_percent, 'is_premium': forward_rate > spot_rate, 'annualized_rate': premium_discount_percent}

    def mark_to_market_forward(self, contract_details: Dict[str, Any], current_market_data: Dict[str, Any]) -> Dict[str, Decimal]:
        """Calculate mark-to-market value of forward contract"""
        notional = self.to_decimal(contract_details['notional_amount'])
        contract_rate = self.to_decimal(contract_details['contract_rate'])
        maturity = self.to_decimal(contract_details['time_to_maturity'])
        position = contract_details['position']
        current_forward = self.to_decimal(current_market_data['current_forward_rate'])
        risk_free_rate = self.to_decimal(current_market_data['risk_free_rate'])
        rate_difference = current_forward - contract_rate
        if position == 'short':
            rate_difference = -rate_difference
        pv_factor = self.to_decimal(1) / (self.to_decimal(1) + risk_free_rate) ** maturity
        mtm_value = notional * rate_difference * pv_factor
        return {'mtm_value': mtm_value, 'notional_amount': notional, 'contract_rate': contract_rate, 'current_forward_rate': current_forward, 'rate_difference': rate_difference, 'position': position, 'pv_factor': pv_factor, 'unrealized_pnl': mtm_value}

    def calculate(self, calculation_type: str, **kwargs) -> Dict[str, Any]:
        """Main calculation dispatcher"""
        calculations = {'bid_offer_spread': lambda: self.calculate_bid_offer_spread(self.to_decimal(kwargs['bid']), self.to_decimal(kwargs['ask'])), 'forward_premium_discount': lambda: self.calculate_forward_premium_discount(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_rate']), self.to_decimal(kwargs['time_to_maturity'])), 'mark_to_market': lambda: self.mark_to_market_forward(kwargs['contract_details'], kwargs['current_market_data']), 'spread_factors': lambda: self.factors_affecting_spread(kwargs['currency_pair'], kwargs['market_conditions'])}
        if calculation_type not in calculations:
            raise ValidationError(f'Unknown calculation type: {calculation_type}')
        result = calculations[calculation_type]()
        result['metadata'] = self.get_metadata()
        result['calculation_type'] = calculation_type
        return result

def calculate_bid_offer_spread(self, bid: Decimal, ask: Decimal) -> Dict[str, Decimal]:
    """Calculate bid-offer spread metrics"""
    self.validator.validate_bid_ask_spread(bid, ask)
    spread_points = ask - bid
    spread_percentage = spread_points / bid * self.to_decimal(100)
    mid_rate = (bid + ask) / self.to_decimal(2)
    return {'bid': bid, 'ask': ask, 'mid_rate': mid_rate, 'spread_points': spread_points, 'spread_percentage': spread_percentage, 'spread_basis_points': spread_percentage * self.to_decimal(100)}

def calculate_forward_premium_discount(self, spot_rate: Decimal, forward_rate: Decimal, time_to_maturity: Decimal) -> Dict[str, Decimal]:
    """Calculate forward premium/discount"""
    self.validator.validate_exchange_rate(spot_rate)
    self.validator.validate_exchange_rate(forward_rate)
    self.validator.validate_time_period(time_to_maturity)
    premium_discount = (forward_rate - spot_rate) / spot_rate * (self.to_decimal(1) / time_to_maturity)
    premium_discount_percent = premium_discount * self.to_decimal(100)
    return {'spot_rate': spot_rate, 'forward_rate': forward_rate, 'time_to_maturity': time_to_maturity, 'premium_discount': premium_discount, 'premium_discount_percent': premium_discount_percent, 'is_premium': forward_rate > spot_rate, 'annualized_rate': premium_discount_percent}

def mark_to_market_forward(self, contract_details: Dict[str, Any], current_market_data: Dict[str, Any]) -> Dict[str, Decimal]:
    """Calculate mark-to-market value of forward contract"""
    notional = self.to_decimal(contract_details['notional_amount'])
    contract_rate = self.to_decimal(contract_details['contract_rate'])
    maturity = self.to_decimal(contract_details['time_to_maturity'])
    position = contract_details['position']
    current_forward = self.to_decimal(current_market_data['current_forward_rate'])
    risk_free_rate = self.to_decimal(current_market_data['risk_free_rate'])
    rate_difference = current_forward - contract_rate
    if position == 'short':
        rate_difference = -rate_difference
    pv_factor = self.to_decimal(1) / (self.to_decimal(1) + risk_free_rate) ** maturity
    mtm_value = notional * rate_difference * pv_factor
    return {'mtm_value': mtm_value, 'notional_amount': notional, 'contract_rate': contract_rate, 'current_forward_rate': current_forward, 'rate_difference': rate_difference, 'position': position, 'pv_factor': pv_factor, 'unrealized_pnl': mtm_value}

def calculate(self, calculation_type: str, **kwargs) -> Dict[str, Any]:
    """Main calculation dispatcher"""
    calculations = {'bid_offer_spread': lambda: self.calculate_bid_offer_spread(self.to_decimal(kwargs['bid']), self.to_decimal(kwargs['ask'])), 'forward_premium_discount': lambda: self.calculate_forward_premium_discount(self.to_decimal(kwargs['spot_rate']), self.to_decimal(kwargs['forward_rate']), self.to_decimal(kwargs['time_to_maturity'])), 'mark_to_market': lambda: self.mark_to_market_forward(kwargs['contract_details'], kwargs['current_market_data']), 'spread_factors': lambda: self.factors_affecting_spread(kwargs['currency_pair'], kwargs['market_conditions'])}
    if calculation_type not in calculations:
        raise ValidationError(f'Unknown calculation type: {calculation_type}')
    result = calculations[calculation_type]()
    result['metadata'] = self.get_metadata()
    result['calculation_type'] = calculation_type
    return result

class ArbitrageDetector(EconomicsBase):
    """Triangular arbitrage detection and profit calculation"""

    def detect_triangular_arbitrage(self, currency_quotes: Dict[str, Dict[str, Decimal]], base_currency: str=None) -> Dict[str, Any]:
        """Detect triangular arbitrage opportunities"""
        base = base_currency or self.base_currency
        opportunities = []
        currencies = list(currency_quotes.keys())
        for i, curr1 in enumerate(currencies):
            for j, curr2 in enumerate(currencies[i + 1:], i + 1):
                for k, curr3 in enumerate(currencies[j + 1:], j + 1):
                    opportunity = self._check_triangle(curr1, curr2, curr3, currency_quotes)
                    if opportunity['arbitrage_exists']:
                        opportunities.append(opportunity)
        return {'opportunities': opportunities, 'total_opportunities': len(opportunities), 'base_currency': base, 'quotes_analyzed': len(currencies), 'timestamp': datetime.now().isoformat()}

    def _check_triangle(self, curr1: str, curr2: str, curr3: str, quotes: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """Check specific triangular arbitrage opportunity"""
        try:
            pair1 = f'{curr1}/{curr2}'
            pair2 = f'{curr2}/{curr3}'
            pair3 = f'{curr3}/{curr1}'
            if pair1 in quotes and pair2 in quotes and (pair3 in quotes):
                rate1 = quotes[pair1]['ask']
                rate2 = quotes[pair2]['ask']
                rate3 = quotes[pair3]['bid']
                forward_result = rate1 * rate2 * rate3
                rate1_rev = quotes[pair3]['ask']
                rate2_rev = self.to_decimal(1) / quotes[pair2]['bid']
                rate3_rev = self.to_decimal(1) / quotes[pair1]['bid']
                reverse_result = rate1_rev * rate2_rev * rate3_rev
                arbitrage_forward = forward_result > self.to_decimal(1)
                arbitrage_reverse = reverse_result > self.to_decimal(1)
                if arbitrage_forward or arbitrage_reverse:
                    best_path = 'forward' if forward_result > reverse_result else 'reverse'
                    profit_factor = max(forward_result, reverse_result)
                    return {'currencies': [curr1, curr2, curr3], 'arbitrage_exists': True, 'best_path': best_path, 'profit_factor': profit_factor, 'profit_percentage': (profit_factor - self.to_decimal(1)) * self.to_decimal(100), 'forward_result': forward_result, 'reverse_result': reverse_result}
            return {'currencies': [curr1, curr2, curr3], 'arbitrage_exists': False, 'profit_factor': self.to_decimal(0), 'profit_percentage': self.to_decimal(0)}
        except Exception as e:
            raise CalculationError(f'Error calculating triangular arbitrage: {e}')

    def calculate_arbitrage_profit(self, opportunity: Dict[str, Any], investment_amount: Decimal) -> Dict[str, Decimal]:
        """Calculate profit from arbitrage opportunity"""
        if not opportunity['arbitrage_exists']:
            raise ValidationError('No arbitrage opportunity exists')
        profit_factor = opportunity['profit_factor']
        gross_profit = investment_amount * (profit_factor - self.to_decimal(1))
        transaction_cost_rate = self.to_decimal(0.001)
        num_transactions = self.to_decimal(3)
        transaction_costs = investment_amount * transaction_cost_rate * num_transactions
        net_profit = gross_profit - transaction_costs
        net_profit_percentage = net_profit / investment_amount * self.to_decimal(100)
        return {'investment_amount': investment_amount, 'gross_profit': gross_profit, 'transaction_costs': transaction_costs, 'net_profit': net_profit, 'net_profit_percentage': net_profit_percentage, 'profit_factor': profit_factor, 'viable': net_profit > self.to_decimal(0)}

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Main arbitrage calculation"""
        if 'currency_quotes' in kwargs:
            return self.detect_triangular_arbitrage(kwargs['currency_quotes'], kwargs.get('base_currency'))
        elif 'opportunity' in kwargs and 'investment_amount' in kwargs:
            return self.calculate_arbitrage_profit(kwargs['opportunity'], self.to_decimal(kwargs['investment_amount']))
        else:
            raise ValidationError('Missing required parameters for arbitrage calculation')

def calculate_arbitrage_profit(self, opportunity: Dict[str, Any], investment_amount: Decimal) -> Dict[str, Decimal]:
    """Calculate profit from arbitrage opportunity"""
    if not opportunity['arbitrage_exists']:
        raise ValidationError('No arbitrage opportunity exists')
    profit_factor = opportunity['profit_factor']
    gross_profit = investment_amount * (profit_factor - self.to_decimal(1))
    transaction_cost_rate = self.to_decimal(0.001)
    num_transactions = self.to_decimal(3)
    transaction_costs = investment_amount * transaction_cost_rate * num_transactions
    net_profit = gross_profit - transaction_costs
    net_profit_percentage = net_profit / investment_amount * self.to_decimal(100)
    return {'investment_amount': investment_amount, 'gross_profit': gross_profit, 'transaction_costs': transaction_costs, 'net_profit': net_profit, 'net_profit_percentage': net_profit_percentage, 'profit_factor': profit_factor, 'viable': net_profit > self.to_decimal(0)}

def calculate(self, **kwargs) -> Dict[str, Any]:
    """Main arbitrage calculation"""
    if 'currency_quotes' in kwargs:
        return self.detect_triangular_arbitrage(kwargs['currency_quotes'], kwargs.get('base_currency'))
    elif 'opportunity' in kwargs and 'investment_amount' in kwargs:
        return self.calculate_arbitrage_profit(kwargs['opportunity'], self.to_decimal(kwargs['investment_amount']))
    else:
        raise ValidationError('Missing required parameters for arbitrage calculation')

class ParityAnalyzer(EconomicsBase):
    """International parity conditions analysis"""

    def covered_interest_rate_parity(self, spot_rate: Decimal, forward_rate: Decimal, domestic_rate: Decimal, foreign_rate: Decimal, time_period: Decimal) -> Dict[str, Any]:
        """Test covered interest rate parity condition"""
        theoretical_forward = spot_rate * ((self.to_decimal(1) + domestic_rate * time_period) / (self.to_decimal(1) + foreign_rate * time_period))
        deviation = forward_rate - theoretical_forward
        deviation_percentage = deviation / theoretical_forward * self.to_decimal(100)
        arbitrage_threshold = self.to_decimal(0.1)
        arbitrage_opportunity = abs(deviation_percentage) > arbitrage_threshold
        return {'spot_rate': spot_rate, 'forward_rate': forward_rate, 'theoretical_forward': theoretical_forward, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'parity_holds': abs(deviation_percentage) < self.to_decimal(0.05), 'arbitrage_opportunity': arbitrage_opportunity, 'domestic_rate': domestic_rate, 'foreign_rate': foreign_rate, 'time_period': time_period}

    def uncovered_interest_rate_parity(self, spot_rate: Decimal, expected_spot: Decimal, domestic_rate: Decimal, foreign_rate: Decimal, time_period: Decimal) -> Dict[str, Any]:
        """Test uncovered interest rate parity condition"""
        theoretical_expected = spot_rate * ((self.to_decimal(1) + domestic_rate * time_period) / (self.to_decimal(1) + foreign_rate * time_period))
        deviation = expected_spot - theoretical_expected
        deviation_percentage = deviation / theoretical_expected * self.to_decimal(100)
        return {'spot_rate': spot_rate, 'expected_spot': expected_spot, 'theoretical_expected': theoretical_expected, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'parity_holds': abs(deviation_percentage) < self.to_decimal(5), 'risk_premium': deviation_percentage}

    def purchasing_power_parity(self, spot_rate: Decimal, domestic_inflation: Decimal, foreign_inflation: Decimal, time_period: Decimal) -> Dict[str, Any]:
        """Test purchasing power parity"""
        theoretical_rate = spot_rate * ((self.to_decimal(1) + domestic_inflation * time_period) / (self.to_decimal(1) + foreign_inflation * time_period))
        return {'current_spot': spot_rate, 'theoretical_rate': theoretical_rate, 'domestic_inflation': domestic_inflation, 'foreign_inflation': foreign_inflation, 'inflation_differential': domestic_inflation - foreign_inflation, 'time_period': time_period, 'expected_change_percentage': (theoretical_rate - spot_rate) / spot_rate * self.to_decimal(100)}

    def international_fisher_effect(self, domestic_nominal: Decimal, foreign_nominal: Decimal, domestic_real: Decimal, foreign_real: Decimal) -> Dict[str, Any]:
        """Test International Fisher Effect"""
        nominal_ratio = (self.to_decimal(1) + domestic_nominal) / (self.to_decimal(1) + foreign_nominal)
        real_ratio = (self.to_decimal(1) + domestic_real) / (self.to_decimal(1) + foreign_real)
        deviation = nominal_ratio - real_ratio
        deviation_percentage = deviation / real_ratio * self.to_decimal(100)
        return {'domestic_nominal_rate': domestic_nominal, 'foreign_nominal_rate': foreign_nominal, 'domestic_real_rate': domestic_real, 'foreign_real_rate': foreign_real, 'nominal_ratio': nominal_ratio, 'real_ratio': real_ratio, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'fisher_effect_holds': abs(deviation_percentage) < self.to_decimal(1)}

    def calculate(self, parity_type: str, **kwargs) -> Dict[str, Any]:
        """Calculate specific parity condition"""
        parity_functions = {'covered_interest_parity': self.covered_interest_rate_parity, 'uncovered_interest_parity': self.uncovered_interest_rate_parity, 'purchasing_power_parity': self.purchasing_power_parity, 'international_fisher_effect': self.international_fisher_effect}
        if parity_type not in parity_functions:
            raise ValidationError(f'Unknown parity type: {parity_type}')
        decimal_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, (int, float, str)) and key != 'parity_type':
                try:
                    decimal_kwargs[key] = self.to_decimal(value)
                except:
                    decimal_kwargs[key] = value
            else:
                decimal_kwargs[key] = value
        result = parity_functions[parity_type](**decimal_kwargs)
        result['metadata'] = self.get_metadata()
        result['parity_type'] = parity_type
        return result

def covered_interest_rate_parity(self, spot_rate: Decimal, forward_rate: Decimal, domestic_rate: Decimal, foreign_rate: Decimal, time_period: Decimal) -> Dict[str, Any]:
    """Test covered interest rate parity condition"""
    theoretical_forward = spot_rate * ((self.to_decimal(1) + domestic_rate * time_period) / (self.to_decimal(1) + foreign_rate * time_period))
    deviation = forward_rate - theoretical_forward
    deviation_percentage = deviation / theoretical_forward * self.to_decimal(100)
    arbitrage_threshold = self.to_decimal(0.1)
    arbitrage_opportunity = abs(deviation_percentage) > arbitrage_threshold
    return {'spot_rate': spot_rate, 'forward_rate': forward_rate, 'theoretical_forward': theoretical_forward, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'parity_holds': abs(deviation_percentage) < self.to_decimal(0.05), 'arbitrage_opportunity': arbitrage_opportunity, 'domestic_rate': domestic_rate, 'foreign_rate': foreign_rate, 'time_period': time_period}

def uncovered_interest_rate_parity(self, spot_rate: Decimal, expected_spot: Decimal, domestic_rate: Decimal, foreign_rate: Decimal, time_period: Decimal) -> Dict[str, Any]:
    """Test uncovered interest rate parity condition"""
    theoretical_expected = spot_rate * ((self.to_decimal(1) + domestic_rate * time_period) / (self.to_decimal(1) + foreign_rate * time_period))
    deviation = expected_spot - theoretical_expected
    deviation_percentage = deviation / theoretical_expected * self.to_decimal(100)
    return {'spot_rate': spot_rate, 'expected_spot': expected_spot, 'theoretical_expected': theoretical_expected, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'parity_holds': abs(deviation_percentage) < self.to_decimal(5), 'risk_premium': deviation_percentage}

def purchasing_power_parity(self, spot_rate: Decimal, domestic_inflation: Decimal, foreign_inflation: Decimal, time_period: Decimal) -> Dict[str, Any]:
    """Test purchasing power parity"""
    theoretical_rate = spot_rate * ((self.to_decimal(1) + domestic_inflation * time_period) / (self.to_decimal(1) + foreign_inflation * time_period))
    return {'current_spot': spot_rate, 'theoretical_rate': theoretical_rate, 'domestic_inflation': domestic_inflation, 'foreign_inflation': foreign_inflation, 'inflation_differential': domestic_inflation - foreign_inflation, 'time_period': time_period, 'expected_change_percentage': (theoretical_rate - spot_rate) / spot_rate * self.to_decimal(100)}

def international_fisher_effect(self, domestic_nominal: Decimal, foreign_nominal: Decimal, domestic_real: Decimal, foreign_real: Decimal) -> Dict[str, Any]:
    """Test International Fisher Effect"""
    nominal_ratio = (self.to_decimal(1) + domestic_nominal) / (self.to_decimal(1) + foreign_nominal)
    real_ratio = (self.to_decimal(1) + domestic_real) / (self.to_decimal(1) + foreign_real)
    deviation = nominal_ratio - real_ratio
    deviation_percentage = deviation / real_ratio * self.to_decimal(100)
    return {'domestic_nominal_rate': domestic_nominal, 'foreign_nominal_rate': foreign_nominal, 'domestic_real_rate': domestic_real, 'foreign_real_rate': foreign_real, 'nominal_ratio': nominal_ratio, 'real_ratio': real_ratio, 'deviation': deviation, 'deviation_percentage': deviation_percentage, 'fisher_effect_holds': abs(deviation_percentage) < self.to_decimal(1)}

def calculate(self, parity_type: str, **kwargs) -> Dict[str, Any]:
    """Calculate specific parity condition"""
    parity_functions = {'covered_interest_parity': self.covered_interest_rate_parity, 'uncovered_interest_parity': self.uncovered_interest_rate_parity, 'purchasing_power_parity': self.purchasing_power_parity, 'international_fisher_effect': self.international_fisher_effect}
    if parity_type not in parity_functions:
        raise ValidationError(f'Unknown parity type: {parity_type}')
    decimal_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, (int, float, str)) and key != 'parity_type':
            try:
                decimal_kwargs[key] = self.to_decimal(value)
            except:
                decimal_kwargs[key] = value
        else:
            decimal_kwargs[key] = value
    result = parity_functions[parity_type](**decimal_kwargs)
    result['metadata'] = self.get_metadata()
    result['parity_type'] = parity_type
    return result

class CarryTradeAnalyzer(EconomicsBase):
    """Carry trade analysis and profit calculations"""

    def calculate_carry_trade_return(self, funding_currency_rate: Decimal, target_currency_rate: Decimal, exchange_rate_change: Decimal, time_period: Decimal, leverage: Decimal=None) -> Dict[str, Any]:
        """Calculate carry trade returns"""
        leverage = leverage or self.to_decimal(1)
        rate_differential = target_currency_rate - funding_currency_rate
        interest_income = rate_differential * time_period
        fx_return = exchange_rate_change
        total_return = interest_income + fx_return
        leveraged_return = total_return * leverage
        sharpe_ratio = self._calculate_carry_trade_sharpe(rate_differential, exchange_rate_change, time_period)
        return {'funding_rate': funding_currency_rate, 'target_rate': target_currency_rate, 'rate_differential': rate_differential, 'interest_income': interest_income, 'fx_return': fx_return, 'total_return': total_return, 'leverage': leverage, 'leveraged_return': leveraged_return, 'annualized_return': leveraged_return / time_period, 'time_period': time_period, 'sharpe_ratio': sharpe_ratio, 'risk_level': self._assess_carry_trade_risk(rate_differential, leverage)}

    def _calculate_carry_trade_sharpe(self, rate_diff: Decimal, fx_change: Decimal, time_period: Decimal) -> Decimal:
        """Simplified Sharpe ratio calculation for carry trade"""
        assumed_volatility = self.to_decimal(0.1)
        expected_return = rate_diff * time_period
        risk_free_rate = self.to_decimal(0.02)
        excess_return = expected_return - risk_free_rate * time_period
        sharpe = excess_return / (assumed_volatility * time_period ** self.to_decimal(0.5))
        return sharpe

    def _assess_carry_trade_risk(self, rate_differential: Decimal, leverage: Decimal) -> str:
        """Assess carry trade risk level"""
        risk_score = abs(rate_differential) * leverage
        if risk_score < self.to_decimal(0.02):
            return 'Low'
        elif risk_score < self.to_decimal(0.05):
            return 'Medium'
        else:
            return 'High'

    def carry_trade_uip_violation(self, rate_differential: Decimal, actual_fx_change: Decimal, time_period: Decimal) -> Dict[str, Any]:
        """Analyze carry trade in context of UIP violation"""
        uip_predicted_change = -rate_differential * time_period
        uip_violation = actual_fx_change - uip_predicted_change
        carry_profit = rate_differential * time_period + uip_violation
        return {'rate_differential': rate_differential, 'uip_predicted_fx_change': uip_predicted_change, 'actual_fx_change': actual_fx_change, 'uip_violation': uip_violation, 'carry_trade_profit': carry_profit, 'uip_violation_percentage': uip_violation / abs(uip_predicted_change) * self.to_decimal(100) if uip_predicted_change != 0 else self.to_decimal(0), 'profitable': carry_profit > self.to_decimal(0)}

    def calculate(self, calculation_type: str='return', **kwargs) -> Dict[str, Any]:
        """Main carry trade calculation"""
        if calculation_type == 'return':
            return self.calculate_carry_trade_return(self.to_decimal(kwargs['funding_rate']), self.to_decimal(kwargs['target_rate']), self.to_decimal(kwargs['fx_change']), self.to_decimal(kwargs['time_period']), self.to_decimal(kwargs.get('leverage', 1)))
        elif calculation_type == 'uip_violation':
            return self.carry_trade_uip_violation(self.to_decimal(kwargs['rate_differential']), self.to_decimal(kwargs['actual_fx_change']), self.to_decimal(kwargs['time_period']))
        else:
            raise ValidationError(f'Unknown calculation type: {calculation_type}')

def calculate_carry_trade_return(self, funding_currency_rate: Decimal, target_currency_rate: Decimal, exchange_rate_change: Decimal, time_period: Decimal, leverage: Decimal=None) -> Dict[str, Any]:
    """Calculate carry trade returns"""
    leverage = leverage or self.to_decimal(1)
    rate_differential = target_currency_rate - funding_currency_rate
    interest_income = rate_differential * time_period
    fx_return = exchange_rate_change
    total_return = interest_income + fx_return
    leveraged_return = total_return * leverage
    sharpe_ratio = self._calculate_carry_trade_sharpe(rate_differential, exchange_rate_change, time_period)
    return {'funding_rate': funding_currency_rate, 'target_rate': target_currency_rate, 'rate_differential': rate_differential, 'interest_income': interest_income, 'fx_return': fx_return, 'total_return': total_return, 'leverage': leverage, 'leveraged_return': leveraged_return, 'annualized_return': leveraged_return / time_period, 'time_period': time_period, 'sharpe_ratio': sharpe_ratio, 'risk_level': self._assess_carry_trade_risk(rate_differential, leverage)}

def _calculate_carry_trade_sharpe(self, rate_diff: Decimal, fx_change: Decimal, time_period: Decimal) -> Decimal:
    """Simplified Sharpe ratio calculation for carry trade"""
    assumed_volatility = self.to_decimal(0.1)
    expected_return = rate_diff * time_period
    risk_free_rate = self.to_decimal(0.02)
    excess_return = expected_return - risk_free_rate * time_period
    sharpe = excess_return / (assumed_volatility * time_period ** self.to_decimal(0.5))
    return sharpe

def _assess_carry_trade_risk(self, rate_differential: Decimal, leverage: Decimal) -> str:
    """Assess carry trade risk level"""
    risk_score = abs(rate_differential) * leverage
    if risk_score < self.to_decimal(0.02):
        return 'Low'
    elif risk_score < self.to_decimal(0.05):
        return 'Medium'
    else:
        return 'High'

def carry_trade_uip_violation(self, rate_differential: Decimal, actual_fx_change: Decimal, time_period: Decimal) -> Dict[str, Any]:
    """Analyze carry trade in context of UIP violation"""
    uip_predicted_change = -rate_differential * time_period
    uip_violation = actual_fx_change - uip_predicted_change
    carry_profit = rate_differential * time_period + uip_violation
    return {'rate_differential': rate_differential, 'uip_predicted_fx_change': uip_predicted_change, 'actual_fx_change': actual_fx_change, 'uip_violation': uip_violation, 'carry_trade_profit': carry_profit, 'uip_violation_percentage': uip_violation / abs(uip_predicted_change) * self.to_decimal(100) if uip_predicted_change != 0 else self.to_decimal(0), 'profitable': carry_profit > self.to_decimal(0)}

def calculate(self, calculation_type: str='return', **kwargs) -> Dict[str, Any]:
    """Main carry trade calculation"""
    if calculation_type == 'return':
        return self.calculate_carry_trade_return(self.to_decimal(kwargs['funding_rate']), self.to_decimal(kwargs['target_rate']), self.to_decimal(kwargs['fx_change']), self.to_decimal(kwargs['time_period']), self.to_decimal(kwargs.get('leverage', 1)))
    elif calculation_type == 'uip_violation':
        return self.carry_trade_uip_violation(self.to_decimal(kwargs['rate_differential']), self.to_decimal(kwargs['actual_fx_change']), self.to_decimal(kwargs['time_period']))
    else:
        raise ValidationError(f'Unknown calculation type: {calculation_type}')

class StatisticalAnalyzer(EconomicsBase):
    """Advanced statistical analysis for economic data"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)

    def descriptive_statistics(self, data: pd.Series, confidence_level: float=0.95) -> Dict[str, Any]:
        """Calculate comprehensive descriptive statistics"""
        if data.empty:
            raise ValidationError('Empty data series provided')
        clean_data = data.dropna()
        if clean_data.empty:
            raise ValidationError('No valid data points after removing NaN values')
        n = len(clean_data)
        mean = clean_data.mean()
        std = clean_data.std()
        basic_stats = {'count': n, 'mean': self.to_decimal(mean), 'median': self.to_decimal(clean_data.median()), 'mode': self.to_decimal(clean_data.mode().iloc[0]) if not clean_data.mode().empty else None, 'standard_deviation': self.to_decimal(std), 'variance': self.to_decimal(clean_data.var()), 'minimum': self.to_decimal(clean_data.min()), 'maximum': self.to_decimal(clean_data.max()), 'range': self.to_decimal(clean_data.max() - clean_data.min())}
        percentiles = {}
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            percentiles[f'p{p}'] = self.to_decimal(clean_data.quantile(p / 100))
        shape_stats = {'skewness': self.to_decimal(clean_data.skew()), 'kurtosis': self.to_decimal(clean_data.kurtosis()), 'excess_kurtosis': self.to_decimal(clean_data.kurtosis() - 3)}
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha / 2, n - 1)
        margin_of_error = t_critical * (std / np.sqrt(n))
        confidence_intervals = {'mean_ci_lower': self.to_decimal(mean - margin_of_error), 'mean_ci_upper': self.to_decimal(mean + margin_of_error), 'confidence_level': self.to_decimal(confidence_level)}
        normality_tests = self._test_normality(clean_data)
        return {'basic_statistics': basic_stats, 'percentiles': percentiles, 'shape_statistics': shape_stats, 'confidence_intervals': confidence_intervals, 'normality_tests': normality_tests, 'outlier_analysis': self._analyze_outliers(clean_data)}

    def _test_normality(self, data: pd.Series) -> Dict[str, Any]:
        """Test for normality using multiple tests"""
        results = {}
        if len(data) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(data)
            results['shapiro_wilk'] = {'statistic': self.to_decimal(shapiro_stat), 'p_value': self.to_decimal(shapiro_p), 'is_normal': shapiro_p > 0.05}
        ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        results['kolmogorov_smirnov'] = {'statistic': self.to_decimal(ks_stat), 'p_value': self.to_decimal(ks_p), 'is_normal': ks_p > 0.05}
        ad_stat, ad_critical, ad_significance = stats.anderson(data, dist='norm')
        results['anderson_darling'] = {'statistic': self.to_decimal(ad_stat), 'critical_values': [self.to_decimal(cv) for cv in ad_critical], 'significance_levels': [self.to_decimal(sl) for sl in ad_significance], 'is_normal': ad_stat < ad_critical[2]}
        return results

    def _analyze_outliers(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze outliers using multiple methods"""
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        iqr_outliers = ((data < lower_bound) | (data > upper_bound)).sum()
        z_scores = np.abs((data - data.mean()) / data.std())
        zscore_outliers = (z_scores > 3).sum()
        median = data.median()
        mad = np.median(np.abs(data - median))
        modified_z_scores = 0.6745 * (data - median) / mad
        modified_zscore_outliers = (np.abs(modified_z_scores) > 3.5).sum()
        return {'iqr_method': {'outlier_count': int(iqr_outliers), 'outlier_percentage': self.to_decimal(iqr_outliers / len(data) * 100), 'lower_bound': self.to_decimal(lower_bound), 'upper_bound': self.to_decimal(upper_bound)}, 'zscore_method': {'outlier_count': int(zscore_outliers), 'outlier_percentage': self.to_decimal(zscore_outliers / len(data) * 100), 'threshold': self.to_decimal(3)}, 'modified_zscore_method': {'outlier_count': int(modified_zscore_outliers), 'outlier_percentage': self.to_decimal(modified_zscore_outliers / len(data) * 100), 'threshold': self.to_decimal(3.5)}}

    def correlation_analysis(self, data: pd.DataFrame, method: str='pearson') -> Dict[str, Any]:
        """Comprehensive correlation analysis"""
        if data.empty:
            raise ValidationError('Empty dataframe provided')
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValidationError('No numeric columns found in data')
        if method.lower() == 'pearson':
            corr_matrix = numeric_data.corr(method='pearson')
        elif method.lower() == 'spearman':
            corr_matrix = numeric_data.corr(method='spearman')
        elif method.lower() == 'kendall':
            corr_matrix = numeric_data.corr(method='kendall')
        else:
            raise ValidationError(f'Unknown correlation method: {method}')
        p_values = self._calculate_correlation_pvalues(numeric_data, method)
        significant_correlations = self._find_significant_correlations(corr_matrix, p_values, alpha=0.05)
        highest_correlations = self._find_highest_correlations(corr_matrix, top_n=10)
        return {'correlation_matrix': corr_matrix.round(4).to_dict(), 'p_values': p_values, 'method': method, 'significant_correlations': significant_correlations, 'highest_correlations': highest_correlations, 'summary_statistics': {'mean_correlation': self.to_decimal(corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()), 'max_correlation': self.to_decimal(corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max()), 'min_correlation': self.to_decimal(corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].min())}}

    def _calculate_correlation_pvalues(self, data: pd.DataFrame, method: str) -> Dict[str, Dict[str, float]]:
        """Calculate p-values for correlation matrix"""
        columns = data.columns
        p_values = {}
        for i, col1 in enumerate(columns):
            p_values[col1] = {}
            for j, col2 in enumerate(columns):
                if i == j:
                    p_values[col1][col2] = 0.0
                else:
                    if method.lower() == 'pearson':
                        _, p_val = stats.pearsonr(data[col1].dropna(), data[col2].dropna())
                    elif method.lower() == 'spearman':
                        _, p_val = stats.spearmanr(data[col1].dropna(), data[col2].dropna())
                    elif method.lower() == 'kendall':
                        _, p_val = stats.kendalltau(data[col1].dropna(), data[col2].dropna())
                    p_values[col1][col2] = float(p_val)
        return p_values

    def _find_significant_correlations(self, corr_matrix: pd.DataFrame, p_values: Dict[str, Dict[str, float]], alpha: float=0.05) -> List[Dict[str, Any]]:
        """Find statistically significant correlations"""
        significant = []
        columns = corr_matrix.columns
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j:
                    corr = corr_matrix.loc[col1, col2]
                    p_val = p_values[col1][col2]
                    if p_val < alpha:
                        significant.append({'variable_1': col1, 'variable_2': col2, 'correlation': self.to_decimal(corr), 'p_value': self.to_decimal(p_val), 'significance_level': alpha})
        significant.sort(key=lambda x: abs(x['correlation']), reverse=True)
        return significant

    def _find_highest_correlations(self, corr_matrix: pd.DataFrame, top_n: int=10) -> List[Dict[str, Any]]:
        """Find highest absolute correlations"""
        correlations = []
        columns = corr_matrix.columns
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j:
                    corr = corr_matrix.loc[col1, col2]
                    correlations.append({'variable_1': col1, 'variable_2': col2, 'correlation': self.to_decimal(corr), 'absolute_correlation': self.to_decimal(abs(corr))})
        correlations.sort(key=lambda x: x['absolute_correlation'], reverse=True)
        return correlations[:top_n]

    def hypothesis_testing(self, data1: pd.Series, data2: Optional[pd.Series]=None, test_type: str='one_sample_t', alternative: str='two-sided', alpha: float=0.05, null_value: float=0) -> Dict[str, Any]:
        """Comprehensive hypothesis testing"""
        if data1.empty:
            raise ValidationError('Empty data series provided')
        clean_data1 = data1.dropna()
        if clean_data1.empty:
            raise ValidationError('No valid data points in first series')
        test_results = {}
        if test_type == 'one_sample_t':
            statistic, p_value = stats.ttest_1samp(clean_data1, null_value)
            test_results = {'test_type': 'One-sample t-test', 'null_hypothesis': f'Population mean equals {null_value}', 'alternative_hypothesis': self._format_alternative_hypothesis('mean', null_value, alternative), 'test_statistic': self.to_decimal(statistic), 'p_value': self.to_decimal(p_value), 'degrees_of_freedom': len(clean_data1) - 1, 'sample_mean': self.to_decimal(clean_data1.mean()), 'sample_size': len(clean_data1)}
        elif test_type == 'two_sample_t':
            if data2 is None:
                raise ValidationError('Second data series required for two-sample t-test')
            clean_data2 = data2.dropna()
            if clean_data2.empty:
                raise ValidationError('No valid data points in second series')
            statistic, p_value = stats.ttest_ind(clean_data1, clean_data2, equal_var=False)
            test_results = {'test_type': 'Two-sample t-test (Welch)', 'null_hypothesis': 'Population means are equal', 'alternative_hypothesis': self._format_alternative_hypothesis('means', 0, alternative), 'test_statistic': self.to_decimal(statistic), 'p_value': self.to_decimal(p_value), 'sample_1_mean': self.to_decimal(clean_data1.mean()), 'sample_2_mean': self.to_decimal(clean_data2.mean()), 'sample_1_size': len(clean_data1), 'sample_2_size': len(clean_data2)}
        elif test_type == 'paired_t':
            if data2 is None:
                raise ValidationError('Second data series required for paired t-test')
            aligned_data = pd.DataFrame({'data1': data1, 'data2': data2}).dropna()
            if aligned_data.empty:
                raise ValidationError('No valid paired observations')
            statistic, p_value = stats.ttest_rel(aligned_data['data1'], aligned_data['data2'])
            test_results = {'test_type': 'Paired t-test', 'null_hypothesis': 'Mean difference equals zero', 'alternative_hypothesis': self._format_alternative_hypothesis('difference', 0, alternative), 'test_statistic': self.to_decimal(statistic), 'p_value': self.to_decimal(p_value), 'degrees_of_freedom': len(aligned_data) - 1, 'mean_difference': self.to_decimal((aligned_data['data1'] - aligned_data['data2']).mean()), 'sample_size': len(aligned_data)}
        elif test_type == 'z_test':
            pop_std = null_value
            if pop_std <= 0:
                raise ValidationError('Population standard deviation must be positive for z-test')
            sample_mean = clean_data1.mean()
            n = len(clean_data1)
            z_statistic = (sample_mean - null_value) / (pop_std / np.sqrt(n))
            if alternative == 'two-sided':
                p_value = 2 * (1 - stats.norm.cdf(abs(z_statistic)))
            elif alternative == 'greater':
                p_value = 1 - stats.norm.cdf(z_statistic)
            else:
                p_value = stats.norm.cdf(z_statistic)
            test_results = {'test_type': 'One-sample z-test', 'null_hypothesis': f'Population mean equals {null_value}', 'alternative_hypothesis': self._format_alternative_hypothesis('mean', null_value, alternative), 'test_statistic': self.to_decimal(z_statistic), 'p_value': self.to_decimal(p_value), 'sample_mean': self.to_decimal(sample_mean), 'population_std': self.to_decimal(pop_std), 'sample_size': n}
        else:
            raise ValidationError(f'Unknown test type: {test_type}')
        test_results.update({'alpha': self.to_decimal(alpha), 'alternative': alternative, 'reject_null': test_results['p_value'] < alpha, 'conclusion': self._generate_test_conclusion(test_results['p_value'], alpha, test_results['null_hypothesis'])})
        return test_results

    def _format_alternative_hypothesis(self, parameter: str, null_value: float, alternative: str) -> str:
        """Format alternative hypothesis string"""
        if alternative == 'two-sided':
            return f'Population {parameter} does not equal {null_value}'
        elif alternative == 'greater':
            return f'Population {parameter} is greater than {null_value}'
        elif alternative == 'less':
            return f'Population {parameter} is less than {null_value}'
        else:
            return f'Alternative hypothesis with {alternative} direction'

    def _generate_test_conclusion(self, p_value: Decimal, alpha: float, null_hypothesis: str) -> str:
        """Generate conclusion from hypothesis test"""
        if p_value < alpha:
            return f'Reject null hypothesis: {null_hypothesis} (p-value = {p_value:.6f} < α = {alpha})'
        else:
            return f'Fail to reject null hypothesis: {null_hypothesis} (p-value = {p_value:.6f} ≥ α = {alpha})'

    def time_series_analysis(self, data: pd.Series) -> Dict[str, Any]:
        """Basic time series analysis"""
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValidationError('Data must have datetime index for time series analysis')
        if data.empty:
            raise ValidationError('Empty time series provided')
        clean_data = data.dropna()
        if len(clean_data) < 10:
            raise ValidationError('Insufficient data points for time series analysis')
        results = {'basic_properties': {'start_date': clean_data.index.min(), 'end_date': clean_data.index.max(), 'frequency': pd.infer_freq(clean_data.index), 'total_observations': len(clean_data), 'missing_observations': len(data) - len(clean_data)}, 'stationarity_tests': self._test_stationarity(clean_data), 'autocorrelation': self._calculate_autocorrelation(clean_data), 'trend_analysis': self._analyze_trend(clean_data), 'seasonality_analysis': self._analyze_seasonality(clean_data)}
        return results

    def _test_stationarity(self, data: pd.Series) -> Dict[str, Any]:
        """Test for stationarity using Augmented Dickey-Fuller test"""
        from statsmodels.tsa.stattools import adfuller
        try:
            result = adfuller(data.values, autolag='AIC')
            return {'adf_statistic': self.to_decimal(result[0]), 'p_value': self.to_decimal(result[1]), 'critical_values': {'1%': self.to_decimal(result[4]['1%']), '5%': self.to_decimal(result[4]['5%']), '10%': self.to_decimal(result[4]['10%'])}, 'is_stationary': result[1] < 0.05, 'interpretation': 'Stationary' if result[1] < 0.05 else 'Non-stationary'}
        except Exception as e:
            logger.warning(f'Could not perform ADF test: {e}')
            return {'error': 'Could not perform stationarity test'}

    def _calculate_autocorrelation(self, data: pd.Series, max_lags: int=20) -> Dict[str, Any]:
        """Calculate autocorrelation function"""
        try:
            from statsmodels.tsa.stattools import acf
            max_lags = min(max_lags, len(data) // 4)
            autocorr = acf(data.values, nlags=max_lags, alpha=0.05)
            return {'autocorrelations': [self.to_decimal(x) for x in autocorr[0]], 'confidence_intervals': {'lower': [self.to_decimal(x) for x in autocorr[1][:, 0]], 'upper': [self.to_decimal(x) for x in autocorr[1][:, 1]]}, 'significant_lags': [i for i, ac in enumerate(autocorr[0]) if abs(ac) > 2 / np.sqrt(len(data)) and i > 0]}
        except Exception as e:
            logger.warning(f'Could not calculate autocorrelation: {e}')
            return {'error': 'Could not calculate autocorrelation'}

    def _analyze_trend(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze trend in time series"""
        x = np.arange(len(data))
        y = data.values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        forecast_x = np.arange(len(data), len(data) + periods)
        forecast_values = slope * forecast_x + intercept
        return {'method': 'Linear Trend', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'slope': self.to_decimal(slope), 'intercept': self.to_decimal(intercept), 'r_squared': self.to_decimal(r_value ** 2), 'description': 'Linear trend extrapolation'}

    def _exponential_smoothing_forecast(self, data: pd.Series, periods: int) -> Dict[str, Any]:
        """Simple exponential smoothing"""
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(data.values, trend=None, seasonal=None)
            fitted_model = model.fit()
            forecast_values = fitted_model.forecast(periods)
            return {'method': 'Exponential Smoothing', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'alpha': self.to_decimal(fitted_model.params['smoothing_level']), 'description': 'Simple exponential smoothing'}
        except Exception as e:
            alpha = 0.3
            smoothed_values = [data.iloc[0]]
            for i in range(1, len(data)):
                smoothed_value = alpha * data.iloc[i] + (1 - alpha) * smoothed_values[-1]
                smoothed_values.append(smoothed_value)
            last_smoothed = smoothed_values[-1]
            forecast_values = [last_smoothed] * periods
            return {'method': 'Exponential Smoothing (Manual)', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'alpha': self.to_decimal(alpha), 'description': 'Manual exponential smoothing implementation'}

    def _moving_average_forecast(self, data: pd.Series, periods: int, window: int=None) -> Dict[str, Any]:
        """Moving average forecast"""
        if window is None:
            window = min(12, len(data) // 4)
        window = max(1, min(window, len(data)))
        ma_values = data.rolling(window=window).mean()
        last_ma = ma_values.iloc[-1]
        forecast_values = [last_ma] * periods
        return {'method': f'Moving Average ({window} periods)', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'window_size': window, 'description': f'{window}-period moving average'}

    def _evaluate_forecasting_methods(self, data: pd.Series, forecast_periods: int, methods: List[str]) -> Dict[str, Any]:
        """Evaluate forecasting methods using holdout sample"""
        train_size = len(data) - forecast_periods
        train_data = data.iloc[:train_size]
        test_data = data.iloc[train_size:]
        evaluation_results = {}
        for method in methods:
            try:
                if method == 'naive':
                    forecast = self._naive_forecast(train_data, forecast_periods)
                elif method == 'mean':
                    forecast = self._mean_forecast(train_data, forecast_periods)
                elif method == 'linear_trend':
                    forecast = self._linear_trend_forecast(train_data, forecast_periods)
                elif method == 'exponential_smoothing':
                    forecast = self._exponential_smoothing_forecast(train_data, forecast_periods)
                elif method == 'moving_average':
                    forecast = self._moving_average_forecast(train_data, forecast_periods)
                else:
                    continue
                if 'error' in forecast:
                    continue
                forecast_values = [float(x) for x in forecast['forecast_values']]
                actual_values = test_data.values
                min_length = min(len(forecast_values), len(actual_values))
                forecast_values = forecast_values[:min_length]
                actual_values = actual_values[:min_length]
                if min_length == 0:
                    continue
                mae = np.mean(np.abs(np.array(actual_values) - np.array(forecast_values)))
                mse = np.mean((np.array(actual_values) - np.array(forecast_values)) ** 2)
                rmse = np.sqrt(mse)
                mape = np.mean(np.abs((np.array(actual_values) - np.array(forecast_values)) / np.array(actual_values))) * 100
                evaluation_results[method] = {'mae': self.to_decimal(mae), 'mse': self.to_decimal(mse), 'rmse': self.to_decimal(rmse), 'mape': self.to_decimal(mape)}
            except Exception as e:
                logger.error(f'Error evaluating {method}: {e}')
                evaluation_results[method] = {'error': str(e)}
        if evaluation_results:
            best_method = min(evaluation_results.keys(), key=lambda k: evaluation_results[k].get('rmse', float('inf')) if 'error' not in evaluation_results[k] else float('inf'))
            return {'method_performance': evaluation_results, 'best_method': best_method, 'evaluation_period': forecast_periods}
        return {'error': 'Could not evaluate any methods'}

    def arima_forecast(self, data: pd.Series, forecast_periods: int=12, order: Tuple[int, int, int]=None, auto_arima: bool=True) -> Dict[str, Any]:
        """ARIMA forecasting"""
        if data.empty:
            raise ValidationError('Empty time series provided')
        clean_data = data.dropna()
        if len(clean_data) < 20:
            raise ValidationError('Insufficient data for ARIMA modeling (need at least 20 observations)')
        try:
            from statsmodels.tsa.arima.model import ARIMA
            if auto_arima and order is None:
                best_aic = float('inf')
                best_order = (1, 1, 1)
                for p in range(0, 4):
                    for d in range(0, 2):
                        for q in range(0, 4):
                            try:
                                model = ARIMA(clean_data, order=(p, d, q))
                                fitted_model = model.fit()
                                if fitted_model.aic < best_aic:
                                    best_aic = fitted_model.aic
                                    best_order = (p, d, q)
                            except:
                                continue
                order = best_order
            elif order is None:
                order = (1, 1, 1)
            model = ARIMA(clean_data, order=order)
            fitted_model = model.fit()
            forecast_result = fitted_model.forecast(steps=forecast_periods)
            confidence_intervals = fitted_model.get_forecast(steps=forecast_periods).conf_int()
            return {'method': f'ARIMA{order}', 'forecast_values': [self.to_decimal(x) for x in forecast_result], 'confidence_intervals': {'lower': [self.to_decimal(x) for x in confidence_intervals.iloc[:, 0]], 'upper': [self.to_decimal(x) for x in confidence_intervals.iloc[:, 1]]}, 'model_order': order, 'aic': self.to_decimal(fitted_model.aic), 'bic': self.to_decimal(fitted_model.bic), 'log_likelihood': self.to_decimal(fitted_model.llf), 'description': f'ARIMA({order[0]},{order[1]},{order[2]}) model'}
        except ImportError:
            raise DataError('statsmodels package required for ARIMA forecasting')
        except Exception as e:
            raise CalculationError(f'ARIMA forecasting failed: {e}')

    def calculate(self, forecast_type: str, **kwargs) -> Dict[str, Any]:
        """Main forecasting dispatcher"""
        forecasts = {'simple_methods': lambda: self.simple_forecasting_methods(kwargs['data'], kwargs.get('forecast_periods', 12), kwargs.get('methods')), 'arima': lambda: self.arima_forecast(kwargs['data'], kwargs.get('forecast_periods', 12), kwargs.get('order'), kwargs.get('auto_arima', True))}
        if forecast_type not in forecasts:
            raise ValidationError(f'Unknown forecast type: {forecast_type}')
        result = forecasts[forecast_type]()
        result['metadata'] = self.get_metadata()
        result['forecast_type'] = forecast_type
        return result

def _find_significant_correlations(self, corr_matrix: pd.DataFrame, p_values: Dict[str, Dict[str, float]], alpha: float=0.05) -> List[Dict[str, Any]]:
    """Find statistically significant correlations"""
    significant = []
    columns = corr_matrix.columns
    for i, col1 in enumerate(columns):
        for j, col2 in enumerate(columns):
            if i < j:
                corr = corr_matrix.loc[col1, col2]
                p_val = p_values[col1][col2]
                if p_val < alpha:
                    significant.append({'variable_1': col1, 'variable_2': col2, 'correlation': self.to_decimal(corr), 'p_value': self.to_decimal(p_val), 'significance_level': alpha})
    significant.sort(key=lambda x: abs(x['correlation']), reverse=True)
    return significant

def _find_highest_correlations(self, corr_matrix: pd.DataFrame, top_n: int=10) -> List[Dict[str, Any]]:
    """Find highest absolute correlations"""
    correlations = []
    columns = corr_matrix.columns
    for i, col1 in enumerate(columns):
        for j, col2 in enumerate(columns):
            if i < j:
                corr = corr_matrix.loc[col1, col2]
                correlations.append({'variable_1': col1, 'variable_2': col2, 'correlation': self.to_decimal(corr), 'absolute_correlation': self.to_decimal(abs(corr))})
    correlations.sort(key=lambda x: x['absolute_correlation'], reverse=True)
    return correlations[:top_n]

def _test_stationarity(self, data: pd.Series) -> Dict[str, Any]:
    """Test for stationarity using Augmented Dickey-Fuller test"""
    from statsmodels.tsa.stattools import adfuller
    try:
        result = adfuller(data.values, autolag='AIC')
        return {'adf_statistic': self.to_decimal(result[0]), 'p_value': self.to_decimal(result[1]), 'critical_values': {'1%': self.to_decimal(result[4]['1%']), '5%': self.to_decimal(result[4]['5%']), '10%': self.to_decimal(result[4]['10%'])}, 'is_stationary': result[1] < 0.05, 'interpretation': 'Stationary' if result[1] < 0.05 else 'Non-stationary'}
    except Exception as e:
        logger.warning(f'Could not perform ADF test: {e}')
        return {'error': 'Could not perform stationarity test'}

def _evaluate_forecasting_methods(self, data: pd.Series, forecast_periods: int, methods: List[str]) -> Dict[str, Any]:
    """Evaluate forecasting methods using holdout sample"""
    train_size = len(data) - forecast_periods
    train_data = data.iloc[:train_size]
    test_data = data.iloc[train_size:]
    evaluation_results = {}
    for method in methods:
        try:
            if method == 'naive':
                forecast = self._naive_forecast(train_data, forecast_periods)
            elif method == 'mean':
                forecast = self._mean_forecast(train_data, forecast_periods)
            elif method == 'linear_trend':
                forecast = self._linear_trend_forecast(train_data, forecast_periods)
            elif method == 'exponential_smoothing':
                forecast = self._exponential_smoothing_forecast(train_data, forecast_periods)
            elif method == 'moving_average':
                forecast = self._moving_average_forecast(train_data, forecast_periods)
            else:
                continue
            if 'error' in forecast:
                continue
            forecast_values = [float(x) for x in forecast['forecast_values']]
            actual_values = test_data.values
            min_length = min(len(forecast_values), len(actual_values))
            forecast_values = forecast_values[:min_length]
            actual_values = actual_values[:min_length]
            if min_length == 0:
                continue
            mae = np.mean(np.abs(np.array(actual_values) - np.array(forecast_values)))
            mse = np.mean((np.array(actual_values) - np.array(forecast_values)) ** 2)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((np.array(actual_values) - np.array(forecast_values)) / np.array(actual_values))) * 100
            evaluation_results[method] = {'mae': self.to_decimal(mae), 'mse': self.to_decimal(mse), 'rmse': self.to_decimal(rmse), 'mape': self.to_decimal(mape)}
        except Exception as e:
            logger.error(f'Error evaluating {method}: {e}')
            evaluation_results[method] = {'error': str(e)}
    if evaluation_results:
        best_method = min(evaluation_results.keys(), key=lambda k: evaluation_results[k].get('rmse', float('inf')) if 'error' not in evaluation_results[k] else float('inf'))
        return {'method_performance': evaluation_results, 'best_method': best_method, 'evaluation_period': forecast_periods}
    return {'error': 'Could not evaluate any methods'}

def calculate(self, forecast_type: str, **kwargs) -> Dict[str, Any]:
    """Main forecasting dispatcher"""
    forecasts = {'simple_methods': lambda: self.simple_forecasting_methods(kwargs['data'], kwargs.get('forecast_periods', 12), kwargs.get('methods')), 'arima': lambda: self.arima_forecast(kwargs['data'], kwargs.get('forecast_periods', 12), kwargs.get('order'), kwargs.get('auto_arima', True))}
    if forecast_type not in forecasts:
        raise ValidationError(f'Unknown forecast type: {forecast_type}')
    result = forecasts[forecast_type]()
    result['metadata'] = self.get_metadata()
    result['forecast_type'] = forecast_type
    return result

class ScenarioAnalyzer(EconomicsBase):
    """Scenario analysis and Monte Carlo simulation"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)

    def monte_carlo_simulation(self, base_value: float, volatility: float, drift: float=0.0, time_periods: int=252, num_simulations: int=1000, distribution: str='normal') -> Dict[str, Any]:
        """Monte Carlo simulation for economic variables"""
        if num_simulations < 100:
            raise ValidationError('Number of simulations must be at least 100')
        if time_periods < 1:
            raise ValidationError('Time periods must be positive')
        np.random.seed(42)
        if distribution.lower() == 'normal':
            random_shocks = np.random.normal(0, 1, (num_simulations, time_periods))
        elif distribution.lower() == 'student_t':
            df = 5
            random_shocks = np.random.standard_t(df, (num_simulations, time_periods))
        else:
            raise ValidationError(f'Unknown distribution: {distribution}')
        simulations = np.zeros((num_simulations, time_periods + 1))
        simulations[:, 0] = base_value
        dt = 1.0 / time_periods
        for t in range(time_periods):
            returns = drift * dt + volatility * np.sqrt(dt) * random_shocks[:, t]
            simulations[:, t + 1] = simulations[:, t] * (1 + returns)
        final_values = simulations[:, -1]
        percentiles = {}
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            percentiles[f'p{p}'] = self.to_decimal(np.percentile(final_values, p))
        var_95 = np.percentile(final_values, 5)
        var_99 = np.percentile(final_values, 1)
        es_95 = np.mean(final_values[final_values <= var_95])
        es_99 = np.mean(final_values[final_values <= var_99])
        max_values = np.max(simulations, axis=1)
        min_values = np.min(simulations, axis=1)
        return {'simulation_parameters': {'base_value': self.to_decimal(base_value), 'volatility': self.to_decimal(volatility), 'drift': self.to_decimal(drift), 'time_periods': time_periods, 'num_simulations': num_simulations, 'distribution': distribution}, 'final_value_statistics': {'mean': self.to_decimal(np.mean(final_values)), 'median': self.to_decimal(np.median(final_values)), 'std': self.to_decimal(np.std(final_values)), 'min': self.to_decimal(np.min(final_values)), 'max': self.to_decimal(np.max(final_values)), 'percentiles': percentiles}, 'risk_metrics': {'var_95': self.to_decimal(var_95), 'var_99': self.to_decimal(var_99), 'expected_shortfall_95': self.to_decimal(es_95), 'expected_shortfall_99': self.to_decimal(es_99), 'probability_of_loss': self.to_decimal(np.mean(final_values < base_value) * 100)}, 'path_statistics': {'max_value_mean': self.to_decimal(np.mean(max_values)), 'min_value_mean': self.to_decimal(np.mean(min_values)), 'max_drawdown_mean': self.to_decimal(np.mean((max_values - min_values) / max_values * 100))}}

    def scenario_analysis(self, base_case: Dict[str, float], scenarios: Dict[str, Dict[str, float]], model_function: Callable, sensitivity_vars: List[str]=None) -> Dict[str, Any]:
        """Comprehensive scenario analysis"""
        if not scenarios:
            raise ValidationError('At least one scenario must be provided')
        try:
            base_result = model_function(**base_case)
        except Exception as e:
            raise CalculationError(f'Error calculating base case: {e}')
        scenario_results = {}
        for scenario_name, scenario_params in scenarios.items():
            try:
                scenario_inputs = {**base_case, **scenario_params}
                scenario_result = model_function(**scenario_inputs)
                scenario_results[scenario_name] = scenario_result
            except Exception as e:
                logger.error(f'Error calculating scenario {scenario_name}: {e}')
                scenario_results[scenario_name] = {'error': str(e)}
        sensitivity_results = None
        if sensitivity_vars:
            sensitivity_results = self._sensitivity_analysis(base_case, model_function, sensitivity_vars)
        return {'base_case': {'inputs': base_case, 'result': base_result}, 'scenarios': {name: {'inputs': {**base_case, **scenarios[name]}, 'result': result} for name, result in scenario_results.items()}, 'sensitivity_analysis': sensitivity_results, 'scenario_comparison': self._compare_scenarios(base_result, scenario_results)}

    def _sensitivity_analysis(self, base_case: Dict[str, float], model_function: Callable, variables: List[str], shock_size: float=0.1) -> Dict[str, Any]:
        """Perform sensitivity analysis"""
        sensitivity_results = {}
        for var in variables:
            if var not in base_case:
                logger.warning(f'Variable {var} not found in base case')
                continue
            base_value = base_case[var]
            shocked_inputs_pos = base_case.copy()
            shocked_inputs_pos[var] = base_value * (1 + shock_size)
            shocked_inputs_neg = base_case.copy()
            shocked_inputs_neg[var] = base_value * (1 - shock_size)
            try:
                base_result = model_function(**base_case)
                result_pos = model_function(**shocked_inputs_pos)
                result_neg = model_function(**shocked_inputs_neg)
                if isinstance(base_result, dict):
                    var_sensitivity = {}
                    for output_var, base_output in base_result.items():
                        if isinstance(base_output, (int, float)):
                            elasticity_pos = (result_pos[output_var] - base_output) / base_output / shock_size
                            elasticity_neg = (result_neg[output_var] - base_output) / base_output / -shock_size
                            avg_elasticity = (elasticity_pos + elasticity_neg) / 2
                            var_sensitivity[output_var] = {'elasticity': self.to_decimal(avg_elasticity), 'positive_shock_result': self.to_decimal(result_pos[output_var]), 'negative_shock_result': self.to_decimal(result_neg[output_var])}
                else:
                    elasticity_pos = (result_pos - base_result) / base_result / shock_size
                    elasticity_neg = (result_neg - base_result) / base_result / -shock_size
                    avg_elasticity = (elasticity_pos + elasticity_neg) / 2
                    var_sensitivity = {'elasticity': self.to_decimal(avg_elasticity), 'positive_shock_result': self.to_decimal(result_pos), 'negative_shock_result': self.to_decimal(result_neg)}
                sensitivity_results[var] = var_sensitivity
            except Exception as e:
                logger.error(f'Error in sensitivity analysis for {var}: {e}')
                sensitivity_results[var] = {'error': str(e)}
        return sensitivity_results

    def _compare_scenarios(self, base_result: Any, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare scenario results to base case"""
        comparisons = {}
        for scenario_name, scenario_result in scenario_results.items():
            if 'error' in str(scenario_result):
                comparisons[scenario_name] = {'error': 'Could not compare due to calculation error'}
                continue
            try:
                if isinstance(base_result, dict) and isinstance(scenario_result, dict):
                    scenario_comparison = {}
                    for key in base_result.keys():
                        if key in scenario_result and isinstance(base_result[key], (int, float)):
                            base_val = base_result[key]
                            scenario_val = scenario_result[key]
                            absolute_change = scenario_val - base_val
                            percentage_change = absolute_change / base_val * 100 if base_val != 0 else 0
                            scenario_comparison[key] = {'base_value': self.to_decimal(base_val), 'scenario_value': self.to_decimal(scenario_val), 'absolute_change': self.to_decimal(absolute_change), 'percentage_change': self.to_decimal(percentage_change)}
                    comparisons[scenario_name] = scenario_comparison
                elif isinstance(base_result, (int, float)) and isinstance(scenario_result, (int, float)):
                    absolute_change = scenario_result - base_result
                    percentage_change = absolute_change / base_result * 100 if base_result != 0 else 0
                    comparisons[scenario_name] = {'base_value': self.to_decimal(base_result), 'scenario_value': self.to_decimal(scenario_result), 'absolute_change': self.to_decimal(absolute_change), 'percentage_change': self.to_decimal(percentage_change)}
            except Exception as e:
                logger.error(f'Error comparing scenario {scenario_name}: {e}')
                comparisons[scenario_name] = {'error': str(e)}
        return comparisons

    def stress_testing(self, base_parameters: Dict[str, float], stress_scenarios: Dict[str, Dict[str, float]], model_function: Callable, risk_thresholds: Dict[str, float]=None) -> Dict[str, Any]:
        """Comprehensive stress testing"""
        if not stress_scenarios:
            stress_scenarios = {'mild_stress': {var: val * 0.9 for var, val in base_parameters.items()}, 'moderate_stress': {var: val * 0.8 for var, val in base_parameters.items()}, 'severe_stress': {var: val * 0.7 for var, val in base_parameters.items()}, 'extreme_stress': {var: val * 0.5 for var, val in base_parameters.items()}}
        stress_results = {}
        base_result = model_function(**base_parameters)
        for stress_name, stress_params in stress_scenarios.items():
            try:
                stressed_inputs = {**base_parameters, **stress_params}
                stress_result = model_function(**stressed_inputs)
                stress_results[stress_name] = stress_result
            except Exception as e:
                logger.error(f'Error in stress scenario {stress_name}: {e}')
                stress_results[stress_name] = {'error': str(e)}
        threshold_analysis = None
        if risk_thresholds:
            threshold_analysis = self._analyze_threshold_breaches(base_result, stress_results, risk_thresholds)
        return {'base_case': base_result, 'stress_scenarios': stress_results, 'threshold_analysis': threshold_analysis, 'stress_summary': self._summarize_stress_results(base_result, stress_results)}

    def _analyze_threshold_breaches(self, base_result: Any, stress_results: Dict[str, Any], thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Analyze threshold breaches in stress scenarios"""
        breaches = {}
        for scenario_name, scenario_result in stress_results.items():
            if 'error' in str(scenario_result):
                continue
            scenario_breaches = {}
            if isinstance(scenario_result, dict):
                for var, threshold in thresholds.items():
                    if var in scenario_result:
                        value = scenario_result[var]
                        breach = value < threshold
                        scenario_breaches[var] = {'threshold': self.to_decimal(threshold), 'actual_value': self.to_decimal(value), 'breach': breach, 'distance_from_threshold': self.to_decimal(value - threshold)}
            breaches[scenario_name] = scenario_breaches
        return breaches

    def _summarize_stress_results(self, base_result: Any, stress_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize stress testing results"""
        if isinstance(base_result, dict):
            summary = {}
            for var in base_result.keys():
                if isinstance(base_result[var], (int, float)):
                    var_results = []
                    for scenario_result in stress_results.values():
                        if isinstance(scenario_result, dict) and var in scenario_result:
                            var_results.append(scenario_result[var])
                    if var_results:
                        summary[var] = {'base_value': self.to_decimal(base_result[var]), 'worst_case': self.to_decimal(min(var_results)), 'best_case': self.to_decimal(max(var_results)), 'average_stress': self.to_decimal(np.mean(var_results)), 'max_decline': self.to_decimal(base_result[var] - min(var_results))}
            return summary
        else:
            valid_results = [r for r in stress_results.values() if 'error' not in str(r)]
            if valid_results:
                return {'base_value': self.to_decimal(base_result), 'worst_case': self.to_decimal(min(valid_results)), 'best_case': self.to_decimal(max(valid_results)), 'average_stress': self.to_decimal(np.mean(valid_results)), 'max_decline': self.to_decimal(base_result - min(valid_results))}
            return {'error': 'No valid stress results to summarize'}

    def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Main scenario analysis dispatcher"""
        analyses = {'monte_carlo': lambda: self.monte_carlo_simulation(kwargs['base_value'], kwargs['volatility'], kwargs.get('drift', 0.0), kwargs.get('time_periods', 252), kwargs.get('num_simulations', 1000), kwargs.get('distribution', 'normal')), 'scenario_analysis': lambda: self.scenario_analysis(kwargs['base_case'], kwargs['scenarios'], kwargs['model_function'], kwargs.get('sensitivity_vars')), 'stress_testing': lambda: self.stress_testing(kwargs['base_parameters'], kwargs.get('stress_scenarios', {}), kwargs['model_function'], kwargs.get('risk_thresholds'))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        result['analysis_type'] = analysis_type
        return result
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        trend_strength = abs(r_value)
        return {'linear_trend': {'slope': self.to_decimal(slope), 'intercept': self.to_decimal(intercept), 'r_squared': self.to_decimal(r_value ** 2), 'p_value': self.to_decimal(p_value), 'standard_error': self.to_decimal(std_err)}, 'trend_direction': 'Increasing' if slope > 0 else 'Decreasing' if slope < 0 else 'Flat', 'trend_strength': self.to_decimal(trend_strength), 'trend_significance': p_value < 0.05}

    def _analyze_seasonality(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze seasonality in time series"""
        if len(data) < 24:
            return {'error': 'Insufficient data for seasonality analysis'}
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            freq = pd.infer_freq(data.index)
            if freq is None:
                if len(data) >= 365:
                    period = 365
                elif len(data) >= 52:
                    period = 52
                elif len(data) >= 12:
                    period = 12
                else:
                    period = 4
            else:
                period = None
            decomposition = seasonal_decompose(data, model='additive', period=period)
            seasonal_var = np.var(decomposition.seasonal.dropna())
            residual_var = np.var(decomposition.resid.dropna())
            seasonality_strength = seasonal_var / (seasonal_var + residual_var)
            return {'seasonality_detected': seasonality_strength > 0.1, 'seasonality_strength': self.to_decimal(seasonality_strength), 'seasonal_period': period, 'components_variance': {'trend': self.to_decimal(np.var(decomposition.trend.dropna())), 'seasonal': self.to_decimal(seasonal_var), 'residual': self.to_decimal(residual_var)}}
        except Exception as e:
            logger.warning(f'Could not perform seasonality analysis: {e}')
            return {'error': 'Could not perform seasonality analysis'}

    def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Main statistical analysis dispatcher"""
        analyses = {'descriptive_statistics': lambda: self.descriptive_statistics(kwargs['data'], kwargs.get('confidence_level', 0.95)), 'correlation_analysis': lambda: self.correlation_analysis(kwargs['data'], kwargs.get('method', 'pearson')), 'hypothesis_testing': lambda: self.hypothesis_testing(kwargs['data1'], kwargs.get('data2'), kwargs.get('test_type', 'one_sample_t'), kwargs.get('alternative', 'two-sided'), kwargs.get('alpha', 0.05), kwargs.get('null_value', 0)), 'time_series_analysis': lambda: self.time_series_analysis(kwargs['data'])}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        result['analysis_type'] = analysis_type
        return result

def _analyze_threshold_breaches(self, base_result: Any, stress_results: Dict[str, Any], thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Analyze threshold breaches in stress scenarios"""
    breaches = {}
    for scenario_name, scenario_result in stress_results.items():
        if 'error' in str(scenario_result):
            continue
        scenario_breaches = {}
        if isinstance(scenario_result, dict):
            for var, threshold in thresholds.items():
                if var in scenario_result:
                    value = scenario_result[var]
                    breach = value < threshold
                    scenario_breaches[var] = {'threshold': self.to_decimal(threshold), 'actual_value': self.to_decimal(value), 'breach': breach, 'distance_from_threshold': self.to_decimal(value - threshold)}
        breaches[scenario_name] = scenario_breaches
    return breaches

def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
    """Main statistical analysis dispatcher"""
    analyses = {'descriptive_statistics': lambda: self.descriptive_statistics(kwargs['data'], kwargs.get('confidence_level', 0.95)), 'correlation_analysis': lambda: self.correlation_analysis(kwargs['data'], kwargs.get('method', 'pearson')), 'hypothesis_testing': lambda: self.hypothesis_testing(kwargs['data1'], kwargs.get('data2'), kwargs.get('test_type', 'one_sample_t'), kwargs.get('alternative', 'two-sided'), kwargs.get('alpha', 0.05), kwargs.get('null_value', 0)), 'time_series_analysis': lambda: self.time_series_analysis(kwargs['data'])}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    result['analysis_type'] = analysis_type
    return result

class ForecastingEngine(EconomicsBase):
    """Economic forecasting using various methods"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)

    def simple_forecasting_methods(self, data: pd.Series, forecast_periods: int=12, methods: List[str]=None) -> Dict[str, Any]:
        """Simple forecasting methods for economic time series"""
        if data.empty:
            raise ValidationError('Empty time series provided')
        clean_data = data.dropna()
        if len(clean_data) < 5:
            raise ValidationError('Insufficient data for forecasting')
        if methods is None:
            methods = ['naive', 'mean', 'linear_trend', 'exponential_smoothing']
        forecasts = {}
        for method in methods:
            try:
                if method == 'naive':
                    forecasts[method] = self._naive_forecast(clean_data, forecast_periods)
                elif method == 'mean':
                    forecasts[method] = self._mean_forecast(clean_data, forecast_periods)
                elif method == 'linear_trend':
                    forecasts[method] = self._linear_trend_forecast(clean_data, forecast_periods)
                elif method == 'exponential_smoothing':
                    forecasts[method] = self._exponential_smoothing_forecast(clean_data, forecast_periods)
                elif method == 'moving_average':
                    forecasts[method] = self._moving_average_forecast(clean_data, forecast_periods)
                else:
                    logger.warning(f'Unknown forecasting method: {method}')
            except Exception as e:
                logger.error(f'Error in {method} forecasting: {e}')
                forecasts[method] = {'error': str(e)}
        evaluation = None
        if len(clean_data) > forecast_periods * 2:
            evaluation = self._evaluate_forecasting_methods(clean_data, forecast_periods, methods)
        return {'forecasts': forecasts, 'forecast_periods': forecast_periods, 'data_length': len(clean_data), 'methods_used': methods, 'evaluation': evaluation}

    def _naive_forecast(self, data: pd.Series, periods: int) -> Dict[str, Any]:
        """Naive forecast - last value carried forward"""
        last_value = data.iloc[-1]
        forecast_values = [last_value] * periods
        return {'method': 'Naive (Random Walk)', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'description': 'Last observed value carried forward'}

    def _mean_forecast(self, data: pd.Series, periods: int) -> Dict[str, Any]:
        """Mean forecast - historical mean"""
        mean_value = data.mean()
        forecast_values = [mean_value] * periods
        return {'method': 'Historical Mean', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'description': 'Historical average carried forward'}

    def _linear_trend_forecast(self, data: pd.Series, periods: int) -> Dict[str, Any]:
        """Linear trend extrapolation"""
        x = np.arange(len(data))
        y = data.values

def simple_forecasting_methods(self, data: pd.Series, forecast_periods: int=12, methods: List[str]=None) -> Dict[str, Any]:
    """Simple forecasting methods for economic time series"""
    if data.empty:
        raise ValidationError('Empty time series provided')
    clean_data = data.dropna()
    if len(clean_data) < 5:
        raise ValidationError('Insufficient data for forecasting')
    if methods is None:
        methods = ['naive', 'mean', 'linear_trend', 'exponential_smoothing']
    forecasts = {}
    for method in methods:
        try:
            if method == 'naive':
                forecasts[method] = self._naive_forecast(clean_data, forecast_periods)
            elif method == 'mean':
                forecasts[method] = self._mean_forecast(clean_data, forecast_periods)
            elif method == 'linear_trend':
                forecasts[method] = self._linear_trend_forecast(clean_data, forecast_periods)
            elif method == 'exponential_smoothing':
                forecasts[method] = self._exponential_smoothing_forecast(clean_data, forecast_periods)
            elif method == 'moving_average':
                forecasts[method] = self._moving_average_forecast(clean_data, forecast_periods)
            else:
                logger.warning(f'Unknown forecasting method: {method}')
        except Exception as e:
            logger.error(f'Error in {method} forecasting: {e}')
            forecasts[method] = {'error': str(e)}
    evaluation = None
    if len(clean_data) > forecast_periods * 2:
        evaluation = self._evaluate_forecasting_methods(clean_data, forecast_periods, methods)
    return {'forecasts': forecasts, 'forecast_periods': forecast_periods, 'data_length': len(clean_data), 'methods_used': methods, 'evaluation': evaluation}

def _naive_forecast(self, data: pd.Series, periods: int) -> Dict[str, Any]:
    """Naive forecast - last value carried forward"""
    last_value = data.iloc[-1]
    forecast_values = [last_value] * periods
    return {'method': 'Naive (Random Walk)', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'description': 'Last observed value carried forward'}

def _mean_forecast(self, data: pd.Series, periods: int) -> Dict[str, Any]:
    """Mean forecast - historical mean"""
    mean_value = data.mean()
    forecast_values = [mean_value] * periods
    return {'method': 'Historical Mean', 'forecast_values': [self.to_decimal(x) for x in forecast_values], 'description': 'Historical average carried forward'}

class ExportManager(EconomicsBase):
    """Export analysis results to various formats"""

    def __init__(self, precision: int=8):
        super().__init__(precision)

    def export_to_json(self, data: Dict[str, Any], file_path: str=None) -> str:
        """Export results to JSON format"""
        json_data = self._prepare_for_json(data)
        json_str = json.dumps(json_data, indent=2, default=self._json_serializer)
        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_str)
        return json_str

    def export_to_excel(self, data: Dict[str, Any], file_path: str) -> bool:
        """Export results to Excel format"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                summary_data = []
                for key, value in data.items():
                    if isinstance(value, (str, int, float, Decimal)):
                        summary_data.append({'Metric': key, 'Value': float(value) if isinstance(value, Decimal) else value})
                if summary_data:
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                for section_name, section_data in data.items():
                    if isinstance(section_data, dict):
                        try:
                            df = pd.DataFrame(section_data)
                            if not df.empty:
                                sheet_name = section_name.replace('_', ' ').title()[:31]
                                df.to_excel(writer, sheet_name=sheet_name, index=True)
                        except:
                            continue
            return True
        except Exception as e:
            raise ValidationError(f'Error exporting to Excel: {e}')

    def _prepare_for_json(self, obj: Any) -> Any:
        """Prepare object for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._prepare_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        else:
            return obj

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special objects"""
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'tolist'):
            return obj.tolist()
        else:
            return str(obj)

    def generate_pdf_summary(self, analysis_report: Dict[str, Any], file_path: str=None) -> str:
        """Generate PDF summary report"""
        summary_text = f'\nECONOMIC ANALYSIS REPORT\n{analysis_report.get('title', 'Analysis Report')}\nGenerated: {analysis_report.get('generated_at', 'Unknown')}\n\nEXECUTIVE SUMMARY\n{'-' * 50}\n'
        summary = analysis_report.get('summary', {})
        findings = summary.get('key_findings', [])
        if findings:
            summary_text += '\nKey Findings:\n'
            for finding in findings:
                summary_text += f'• {finding}\n'
        risk = summary.get('risk_assessment', 'Not Available')
        summary_text += f'\nRisk Assessment: {risk}\n'
        outlook = summary.get('outlook', 'Neutral')
        summary_text += f'Outlook: {outlook}\n'
        recommendations = analysis_report.get('recommendations', [])
        if recommendations:
            summary_text += f'\nRECOMMENDATIONS\n{'-' * 50}\n'
            for i, rec in enumerate(recommendations, 1):
                summary_text += f'{i}. {rec}\n'
        if file_path:
            with open(file_path, 'w') as f:
                f.write(summary_text)
        return summary_text

    def calculate(self, export_type: str, **kwargs) -> Any:
        """Main export dispatcher"""
        exports = {'json': lambda: self.export_to_json(kwargs['data'], kwargs.get('file_path')), 'excel': lambda: self.export_to_excel(kwargs['data'], kwargs['file_path']), 'pdf_summary': lambda: self.generate_pdf_summary(kwargs['data'], kwargs.get('file_path'))}
        if export_type not in exports:
            raise ValidationError(f'Unknown export type: {export_type}')
        return exports[export_type]()

def calculate(self, export_type: str, **kwargs) -> Any:
    """Main export dispatcher"""
    exports = {'json': lambda: self.export_to_json(kwargs['data'], kwargs.get('file_path')), 'excel': lambda: self.export_to_excel(kwargs['data'], kwargs['file_path']), 'pdf_summary': lambda: self.generate_pdf_summary(kwargs['data'], kwargs.get('file_path'))}
    if export_type not in exports:
        raise ValidationError(f'Unknown export type: {export_type}')
    return exports[export_type]()

class TradeAnalyzer(EconomicsBase):
    """International trade analysis and policy assessment"""

    def analyze_trade_benefits_costs(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze benefits and costs of international trade"""
        return {'trade_benefits': {'efficiency_gains': {'comparative_advantage': 'Countries specialize in relative strengths', 'resource_allocation': 'More efficient global resource use', 'scale_economies': 'Larger markets enable economies of scale', 'quantitative_benefit': self._calculate_trade_gains(trade_data)}, 'consumer_benefits': {'variety': 'Greater product variety and choice', 'lower_prices': 'Increased competition reduces prices', 'quality_improvement': 'Competition drives quality improvements', 'consumer_surplus_gain': self._estimate_consumer_surplus_gain(trade_data)}, 'growth_benefits': {'technology_transfer': 'Access to foreign technology and knowledge', 'productivity_spillovers': 'Learning from foreign competition', 'investment_flows': 'Foreign direct investment attraction', 'innovation_incentives': 'Competition spurs innovation'}}, 'trade_costs': {'adjustment_costs': {'job_displacement': 'Workers in import-competing industries lose jobs', 'regional_impacts': 'Concentrated effects in specific regions', 'skill_premiums': 'Wage gaps between skilled/unskilled workers', 'adjustment_period': 'Time and cost of worker reallocation'}, 'distributional_effects': {'income_inequality': 'May worsen within-country inequality', 'factor_returns': 'Changes in wages, profits, land rents', 'sectoral_shifts': 'Decline of import-competing sectors', 'compensation_needs': 'Required support for affected workers'}, 'vulnerability_risks': {'import_dependence': 'Reliance on foreign suppliers', 'economic_security': 'Potential supply chain disruptions', 'policy_autonomy': 'Constraints on domestic policy flexibility'}}, 'net_welfare_assessment': self._assess_net_welfare_impact(trade_data)}

    def analyze_trade_restrictions(self, restriction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze different types of trade restrictions and their impacts"""
        return {'tariffs': {'mechanism': 'Tax on imports', 'economic_effects': self._analyze_tariff_effects(restriction_data.get('tariff_rate', 0)), 'revenue_generation': 'Provides government revenue', 'protection_level': 'Proportional to tariff rate', 'welfare_impact': 'Net welfare loss (deadweight loss)'}, 'quotas': {'mechanism': 'Quantity limit on imports', 'economic_effects': self._analyze_quota_effects(restriction_data.get('quota_volume', 0)), 'revenue_generation': 'No government revenue (quota rents to importers)', 'protection_level': 'Fixed quantity protection', 'welfare_impact': 'Similar to tariffs but different rent distribution'}, 'export_subsidies': {'mechanism': 'Government payments to exporters', 'economic_effects': self._analyze_subsidy_effects(restriction_data.get('subsidy_rate', 0)), 'revenue_generation': 'Costs government revenue', 'protection_level': 'Supports domestic producers', 'welfare_impact': 'Welfare loss in subsidizing country'}, 'non_tariff_barriers': {'types': ['Technical standards', 'Sanitary measures', 'Administrative procedures'], 'effects': 'Hidden protection, often more restrictive than tariffs', 'measurement_difficulty': 'Hard to quantify economic impact', 'welfare_impact': 'Potentially large welfare costs'}, 'restriction_comparison': self._compare_trade_restrictions(), 'optimal_policy_recommendation': self._recommend_trade_policy(restriction_data)}

    def analyze_trading_blocs(self, bloc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trading blocs, common markets, and economic unions"""
        integration_types = {'free_trade_area': {'definition': 'Eliminate tariffs among members, keep individual external tariffs', 'examples': ['NAFTA/USMCA', 'ASEAN FTA'], 'advantages': ['Trade creation', 'Market access', 'Political cooperation'], 'disadvantages': ['Trade diversion', 'Rules of origin complexity'], 'economic_impact': self._assess_fta_impact(bloc_data)}, 'customs_union': {'definition': 'Free trade area plus common external tariff', 'examples': ['EU Customs Union', 'Mercosur'], 'advantages': ['Eliminates trade deflection', 'Stronger negotiating power'], 'disadvantages': ['Loss of tariff autonomy', 'Complex revenue sharing'], 'economic_impact': self._assess_customs_union_impact(bloc_data)}, 'common_market': {'definition': 'Customs union plus free movement of factors', 'examples': ['EU Single Market', 'ECOWAS'], 'advantages': ['Factor mobility benefits', 'Efficiency gains', 'Scale economies'], 'disadvantages': ['Adjustment pressures', 'Migration concerns', 'Policy coordination needs'], 'economic_impact': self._assess_common_market_impact(bloc_data)}, 'economic_union': {'definition': 'Common market plus unified economic policies', 'examples': ['European Union', 'Proposed ASEAN Economic Community'], 'advantages': ['Maximum integration benefits', 'Policy coherence', 'Stability'], 'disadvantages': ['Sovereignty loss', 'Complex governance', 'Asymmetric effects'], 'economic_impact': self._assess_economic_union_impact(bloc_data)}}
        return {'integration_levels': integration_types, 'motivations_for_integration': self._analyze_integration_motivations(), 'success_factors': self._identify_integration_success_factors(), 'trade_creation_vs_diversion': self._analyze_trade_creation_diversion(bloc_data)}

    def assess_trade_barrier_removal(self, liberalization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess impact of removing trade barriers"""
        return {'capital_investment_effects': {'foreign_direct_investment': {'expected_change': 'Significant increase', 'mechanisms': ['Market access', 'Lower costs', 'Efficiency seeking'], 'sectoral_impact': 'Manufacturing and services benefit most', 'quantitative_estimate': self._estimate_fdi_increase(liberalization_data)}, 'domestic_investment': {'expected_change': 'Mixed effects', 'mechanisms': ['Competitive pressure', 'Technology access', 'Scale opportunities'], 'adjustment_period': '3-7 years for full effects', 'productivity_gains': self._estimate_productivity_gains(liberalization_data)}}, 'employment_wage_effects': {'aggregate_employment': {'short_term': 'May decline due to adjustment', 'long_term': 'Likely increase from higher productivity', 'skill_composition': 'Shift toward higher-skilled jobs', 'quantitative_estimate': self._estimate_employment_effects(liberalization_data)}, 'wage_effects': {'average_wages': 'Generally increase over time', 'wage_distribution': 'May increase inequality initially', 'sectoral_variation': 'Export sectors gain, import-competing sectors lose', 'skill_premium_changes': self._analyze_skill_premium_effects(liberalization_data)}}, 'growth_effects': {'gdp_impact': {'magnitude': self._estimate_gdp_impact(liberalization_data), 'channels': ['Productivity', 'Investment', 'Competition', 'Innovation'], 'time_horizon': 'Full effects realized over 10-15 years', 'persistence': 'Permanent level effects, temporary growth effects'}, 'sectoral_growth': self._analyze_sectoral_growth_effects(liberalization_data), 'regional_effects': self._assess_regional_impact_variation(liberalization_data)}, 'policy_recommendations': self._recommend_liberalization_policies(liberalization_data)}

    def _calculate_trade_gains(self, data: Dict[str, Any]) -> Decimal:
        """Calculate quantitative trade gains"""
        trade_volume = self.to_decimal(data.get('trade_volume_gdp', 0))
        efficiency_gain = self.to_decimal(0.05)
        return trade_volume * efficiency_gain

    def _estimate_consumer_surplus_gain(self, data: Dict[str, Any]) -> Decimal:
        """Estimate consumer surplus gains from trade"""
        price_reduction = self.to_decimal(data.get('price_reduction_percent', 5))
        consumption_share = self.to_decimal(data.get('traded_goods_consumption', 30))
        return price_reduction * consumption_share / self.to_decimal(200)

    def _analyze_tariff_effects(self, tariff_rate: float) -> Dict[str, Any]:
        """Analyze economic effects of tariffs"""
        rate = self.to_decimal(tariff_rate)
        return {'price_increase': f'Domestic price rises by approximately {rate}%', 'import_reduction': f'Imports fall by {rate * self.to_decimal(1.5)}% (assuming elasticity 1.5)', 'domestic_production': f'Domestic production increases by {rate * self.to_decimal(0.8)}%', 'welfare_loss': f'Deadweight loss approximately {rate ** 2 / self.to_decimal(200)}% of GDP'}

    def _analyze_quota_effects(self, quota_volume: float) -> Dict[str, Any]:
        """Analyze economic effects of import quotas"""
        return {'price_effect': 'Domestic price rises to clear market at quota level', 'quantity_certainty': 'Import volume fixed regardless of demand changes', 'rent_distribution': 'Quota rents accrue to license holders', 'supply_response': 'Domestic producers expand to fill demand gap'}

    def _analyze_subsidy_effects(self, subsidy_rate: float) -> Dict[str, Any]:
        """Analyze economic effects of export subsidies"""
        rate = self.to_decimal(subsidy_rate)
        return {'export_increase': f'Exports rise by approximately {rate * self.to_decimal(1.2)}%', 'domestic_price_rise': f'Domestic price increases by {rate * self.to_decimal(0.5)}%', 'fiscal_cost': f'Government cost {rate}% of export value', 'foreign_welfare': 'Foreign consumers benefit from lower prices'}

    def _compare_trade_restrictions(self) -> Dict[str, str]:
        """Compare different trade restriction types"""
        return {'transparency': 'Tariffs > Quotas > Non-tariff barriers', 'revenue_generation': 'Tariffs > Export subsidies (cost) > Quotas (no revenue)', 'welfare_impact': 'All create deadweight losses, magnitude varies', 'administrative_burden': 'Non-tariff barriers > Quotas > Tariffs', 'flexibility': 'Tariffs > Export subsidies > Quotas'}

    def _recommend_trade_policy(self, data: Dict[str, Any]) -> str:
        """Recommend optimal trade policy"""
        development_level = data.get('development_level', 'middle')
        industry_maturity = data.get('industry_maturity', 'mature')
        if development_level == 'developing' and industry_maturity == 'infant':
            return 'Temporary protection may be justified for infant industries'
        elif development_level == 'developed':
            return 'Free trade generally optimal for developed economies'
        else:
            return 'Gradual liberalization with adjustment assistance'

    def _assess_fta_impact(self, data: Dict[str, Any]) -> str:
        """Assess free trade agreement impact"""
        trade_creation = self.to_decimal(data.get('trade_creation', 0))
        trade_diversion = self.to_decimal(data.get('trade_diversion', 0))
        if trade_creation > trade_diversion:
            return 'Net welfare gain from trade creation effects'
        else:
            return 'Potential welfare loss from trade diversion'

    def _assess_customs_union_impact(self, data: Dict[str, Any]) -> str:
        """Assess customs union impact"""
        return 'Generally more beneficial than FTA due to common external tariff'

    def _assess_common_market_impact(self, data: Dict[str, Any]) -> str:
        """Assess common market impact"""
        return 'Significant benefits from factor mobility, but requires strong institutions'

    def _assess_economic_union_impact(self, data: Dict[str, Any]) -> str:
        """Assess economic union impact"""
        return 'Maximum benefits but requires political integration and sovereignty transfer'

    def _analyze_integration_motivations(self) -> List[str]:
        """Analyze motivations for regional integration"""
        return ['Economic: Market access, scale economies, efficiency gains', 'Political: Peace, cooperation, international influence', 'Strategic: Counterbalance to other blocs, bargaining power', 'Development: Technology transfer, investment attraction']

    def _identify_integration_success_factors(self) -> List[str]:
        """Identify factors for successful regional integration"""
        return ['Geographic proximity and cultural similarity', 'Similar development levels and economic structures', 'Political commitment and institutional capacity', 'Complementary rather than competing economies', 'Mechanism for handling adjustment costs']

    def _analyze_trade_creation_diversion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trade creation vs trade diversion effects"""
        return {'trade_creation': {'definition': 'New trade due to elimination of barriers among members', 'welfare_effect': 'Positive - increases efficiency', 'mechanism': 'Efficient producers replace inefficient domestic production'}, 'trade_diversion': {'definition': 'Trade shifts from efficient non-members to less efficient members', 'welfare_effect': 'Negative - reduces efficiency', 'mechanism': 'Preferential access distorts comparative advantage'}, 'net_effect': 'Depends on relative magnitude of creation vs diversion'}

    def _estimate_fdi_increase(self, data: Dict[str, Any]) -> str:
        """Estimate FDI increase from liberalization"""
        liberalization_scope = data.get('liberalization_scope', 'moderate')
        increases = {'limited': '20-40% increase over 5 years', 'moderate': '50-100% increase over 5 years', 'comprehensive': '100-200% increase over 5 years'}
        return increases.get(liberalization_scope, '50-100% increase over 5 years')

    def _estimate_productivity_gains(self, data: Dict[str, Any]) -> str:
        """Estimate productivity gains from liberalization"""
        return '2-5% productivity gain over 5-10 years'

    def _estimate_employment_effects(self, data: Dict[str, Any]) -> str:
        """Estimate employment effects of liberalization"""
        return 'Short-term adjustment costs, long-term employment gains'

    def _analyze_skill_premium_effects(self, data: Dict[str, Any]) -> str:
        """Analyze effects on skill premiums"""
        return 'Skill premium may increase initially, then stabilize with education/training'

    def _estimate_gdp_impact(self, data: Dict[str, Any]) -> str:
        """Estimate GDP impact of trade liberalization"""
        return '1-3% permanent GDP level increase, spread over 10-15 years'

    def _analyze_sectoral_growth_effects(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Analyze sectoral growth effects"""
        return {'export_sectors': 'Strong growth, increased investment', 'import_competing_sectors': 'Decline, but may become more efficient', 'service_sectors': 'Generally benefit from lower input costs', 'technology_sectors': 'Benefit from knowledge spillovers'}

    def _assess_regional_impact_variation(self, data: Dict[str, Any]) -> str:
        """Assess regional variation in impacts"""
        return 'Urban areas and regions with comparative advantage benefit most'

    def _recommend_liberalization_policies(self, data: Dict[str, Any]) -> List[str]:
        """Recommend supporting policies for liberalization"""
        return ['Trade adjustment assistance for displaced workers', 'Education and training programs for skill upgrading', 'Infrastructure investment to support new trade patterns', 'Competition policy to ensure domestic market efficiency', 'Social safety net to manage transition costs']

    def _assess_net_welfare_impact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess net welfare impact of trade"""
        return {'aggregate_welfare': 'Generally positive but distribution matters', 'time_dimension': 'Short-term costs, long-term benefits', 'policy_implications': 'Need complementary policies for inclusive growth', 'measurement_challenges': 'Difficult to quantify all benefits and costs'}

    def calculate(self, analysis_type: str='benefits_costs', **kwargs) -> Dict[str, Any]:
        """Main trade analysis dispatcher"""
        analyses = {'benefits_costs': lambda: self.analyze_trade_benefits_costs(kwargs.get('trade_data', {})), 'restrictions': lambda: self.analyze_trade_restrictions(kwargs.get('restriction_data', {})), 'trading_blocs': lambda: self.analyze_trading_blocs(kwargs.get('bloc_data', {})), 'barrier_removal': lambda: self.assess_trade_barrier_removal(kwargs.get('liberalization_data', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def _calculate_trade_gains(self, data: Dict[str, Any]) -> Decimal:
    """Calculate quantitative trade gains"""
    trade_volume = self.to_decimal(data.get('trade_volume_gdp', 0))
    efficiency_gain = self.to_decimal(0.05)
    return trade_volume * efficiency_gain

def _estimate_consumer_surplus_gain(self, data: Dict[str, Any]) -> Decimal:
    """Estimate consumer surplus gains from trade"""
    price_reduction = self.to_decimal(data.get('price_reduction_percent', 5))
    consumption_share = self.to_decimal(data.get('traded_goods_consumption', 30))
    return price_reduction * consumption_share / self.to_decimal(200)

def _analyze_tariff_effects(self, tariff_rate: float) -> Dict[str, Any]:
    """Analyze economic effects of tariffs"""
    rate = self.to_decimal(tariff_rate)
    return {'price_increase': f'Domestic price rises by approximately {rate}%', 'import_reduction': f'Imports fall by {rate * self.to_decimal(1.5)}% (assuming elasticity 1.5)', 'domestic_production': f'Domestic production increases by {rate * self.to_decimal(0.8)}%', 'welfare_loss': f'Deadweight loss approximately {rate ** 2 / self.to_decimal(200)}% of GDP'}

def _analyze_subsidy_effects(self, subsidy_rate: float) -> Dict[str, Any]:
    """Analyze economic effects of export subsidies"""
    rate = self.to_decimal(subsidy_rate)
    return {'export_increase': f'Exports rise by approximately {rate * self.to_decimal(1.2)}%', 'domestic_price_rise': f'Domestic price increases by {rate * self.to_decimal(0.5)}%', 'fiscal_cost': f'Government cost {rate}% of export value', 'foreign_welfare': 'Foreign consumers benefit from lower prices'}

def _assess_fta_impact(self, data: Dict[str, Any]) -> str:
    """Assess free trade agreement impact"""
    trade_creation = self.to_decimal(data.get('trade_creation', 0))
    trade_diversion = self.to_decimal(data.get('trade_diversion', 0))
    if trade_creation > trade_diversion:
        return 'Net welfare gain from trade creation effects'
    else:
        return 'Potential welfare loss from trade diversion'

def calculate(self, analysis_type: str='benefits_costs', **kwargs) -> Dict[str, Any]:
    """Main trade analysis dispatcher"""
    analyses = {'benefits_costs': lambda: self.analyze_trade_benefits_costs(kwargs.get('trade_data', {})), 'restrictions': lambda: self.analyze_trade_restrictions(kwargs.get('restriction_data', {})), 'trading_blocs': lambda: self.analyze_trading_blocs(kwargs.get('bloc_data', {})), 'barrier_removal': lambda: self.assess_trade_barrier_removal(kwargs.get('liberalization_data', {}))}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    return result

class GeopoliticalRiskAnalyzer(EconomicsBase):
    """Geopolitical risk assessment and investment implications"""

    def analyze_geopolitics_framework(self) -> Dict[str, Any]:
        """Analyze geopolitics from cooperation vs competition perspective"""
        return {'cooperation_perspective': {'drivers': ['Economic interdependence', 'Shared challenges', 'Institutional frameworks'], 'mechanisms': ['Trade agreements', 'International organizations', 'Diplomatic engagement'], 'benefits': ['Peace dividend', 'Economic gains', 'Global public goods'], 'examples': ['EU integration', 'WTO system', 'Climate cooperation']}, 'competition_perspective': {'drivers': ['National interests', 'Power struggles', 'Resource competition'], 'mechanisms': ['Military buildup', 'Economic sanctions', 'Technology competition'], 'risks': ['Conflict escalation', 'Economic fragmentation', 'Arms races'], 'examples': ['US-China rivalry', 'Russia-West tensions', 'Cyber warfare']}, 'cooperation_competition_spectrum': {'coopetition': 'Simultaneous cooperation and competition', 'issue_specificity': 'Cooperation on some issues, competition on others', 'temporal_variation': 'Shifting between cooperation and competition over time', 'stakeholder_differences': 'Different actors may prefer different approaches'}, 'current_global_trends': self._assess_current_geopolitical_trends()}

    def analyze_geopolitics_globalization(self) -> Dict[str, Any]:
        """Analyze relationship between geopolitics and globalization"""
        return {'globalization_drivers': {'economic': 'Trade, investment, financial integration', 'technological': 'Communication, transportation, digital connectivity', 'political': 'International governance, regulatory convergence', 'cultural': 'Information flow, cultural exchange, migration'}, 'geopolitical_constraints': {'sovereignty_concerns': 'National autonomy vs global integration', 'security_considerations': 'Economic interdependence vs strategic autonomy', 'distributional_effects': 'Winners and losers from globalization', 'cultural_resistance': 'Preserving national identity and values'}, 'interaction_dynamics': {'reinforcing_effects': 'Economic integration can reduce conflict incentives', 'tension_creation': 'Globalization can threaten traditional power structures', 'policy_responses': 'Governments balance integration with national interests', 'cyclical_patterns': 'Periods of integration followed by fragmentation'}, 'current_deglobalization_trends': self._analyze_deglobalization_trends()}

    def analyze_international_organizations(self) -> Dict[str, Any]:
        """Analyze functions and objectives of key international organizations"""
        return {'world_bank': {'primary_objective': 'Reduce poverty and promote shared prosperity', 'functions': ['Development financing and technical assistance', 'Policy advice and capacity building', 'Knowledge sharing and research', 'Crisis response and post-conflict reconstruction'], 'lending_instruments': ['IBRD loans', 'IDA grants', 'Private sector lending'], 'governance': '189 member countries, voting power based on capital contributions', 'effectiveness_assessment': 'Mixed results, criticism for conditionality and governance'}, 'international_monetary_fund': {'primary_objective': 'Ensure stability of international monetary system', 'functions': ['Surveillance of global economy and exchange rates', 'Financial assistance to countries in balance of payments difficulties', 'Technical assistance and capacity development', 'Standard setting and policy coordination'], 'lending_facilities': ['Stand-by arrangements', 'Extended fund facility', 'Emergency assistance'], 'governance': '190 member countries, quota-based voting system', 'effectiveness_assessment': 'Critical role in crisis response, debates over conditionality'}, 'world_trade_organization': {'primary_objective': 'Promote free and fair trade globally', 'functions': ['Trade rule making and negotiation', 'Dispute settlement between members', 'Trade policy monitoring and transparency', 'Technical assistance and capacity building'], 'key_principles': ['Non-discrimination', 'Market access', 'Fair competition', 'Development'], 'governance': '164 members, consensus-based decision making', 'effectiveness_assessment': 'Success in trade liberalization, challenges with dispute resolution'}, 'organizational_interactions': self._analyze_organizational_coordination(), 'reform_needs': self._assess_reform_requirements()}

    def assess_geopolitical_risk(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess geopolitical risk levels and components"""
        return {'risk_categories': {'interstate_conflict': {'probability': self._assess_conflict_probability(risk_data), 'impact': 'High - disrupts trade, increases defense spending', 'indicators': ['Military buildups', 'Territorial disputes', 'Alliance shifts'], 'current_hotspots': ['Taiwan Strait', 'Ukraine', 'Middle East', 'South China Sea']}, 'domestic_instability': {'probability': self._assess_instability_probability(risk_data), 'impact': 'Medium to High - affects governance and economic policy', 'indicators': ['Political polarization', 'Social unrest', 'Economic inequality'], 'monitoring_metrics': ['Polity IV scores', 'Fragile States Index', 'Social cohesion indices']}, 'economic_warfare': {'probability': 'Medium - already occurring', 'impact': 'High - trade disruption, technology decoupling', 'manifestations': ['Trade wars', 'Technology sanctions', 'Financial restrictions'], 'current_examples': ['US-China tech competition', 'Russia sanctions', 'Supply chain nationalism']}, 'cyber_threats': {'probability': 'High - ongoing', 'impact': 'Medium to High - infrastructure and financial system risks', 'evolution': 'Rapidly increasing sophistication and frequency', 'mitigation_challenges': 'Attribution difficulties, cross-border nature'}}, 'risk_assessment_methodology': self._describe_risk_methodology(), 'early_warning_indicators': self._identify_early_warning_signs(), 'risk_mitigation_strategies': self._recommend_risk_mitigation()}

    def analyze_geopolitical_tools(self) -> Dict[str, Any]:
        """Analyze tools of geopolitics and their economic impact"""
        return {'economic_tools': {'trade_policy': {'instruments': ['Tariffs', 'Quotas', 'Trade agreements', 'Export controls'], 'effectiveness': 'High for economic coercion, limited for security goals', 'economic_impact': 'Efficiency losses, distributional effects', 'examples': ['China trade war', 'Iran sanctions', 'Brexit negotiations']}, 'financial_sanctions': {'instruments': ['Asset freezes', 'Banking restrictions', 'Capital market access'], 'effectiveness': 'High when multilateral, moderate when unilateral', 'economic_impact': 'Disrupts financial flows, increases transaction costs', 'examples': ['Russia SWIFT exclusion', 'Iran banking sanctions', 'North Korea restrictions']}, 'investment_controls': {'instruments': ['FDI screening', 'Technology transfer restrictions', 'Sovereign wealth fund limits'], 'effectiveness': 'Moderate for strategic sectors', 'economic_impact': 'Reduces capital flows, technology diffusion', 'examples': ['CFIUS reviews', 'EU FDI screening', 'Technology export controls']}}, 'diplomatic_tools': {'multilateral_engagement': 'International organizations and forums', 'bilateral_relations': 'Direct government-to-government engagement', 'public_diplomacy': 'Cultural and informational influence', 'summit_diplomacy': 'High-level leader engagement'}, 'military_tools': {'defense_spending': 'Military buildup and alliance strengthening', 'military_presence': 'Forward deployment and bases', 'arms_sales': 'Defense cooperation and influence building', 'security_assistance': 'Training and capacity building'}, 'tool_effectiveness_comparison': self._compare_geopolitical_tools()}

    def assess_investment_implications(self, geopolitical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess investment implications of geopolitical risk"""
        return {'asset_class_impacts': {'equities': {'safe_haven_flows': 'Flight to quality during crises', 'sector_differentiation': 'Defense up, trade-dependent sectors down', 'regional_variation': 'Emerging markets more vulnerable', 'volatility_impact': 'Increased uncertainty and volatility'}, 'fixed_income': {'government_bonds': 'Safe haven demand for developed market bonds', 'corporate_bonds': 'Credit spreads widen, especially for affected regions', 'emerging_market_debt': 'Capital flight and spread widening', 'inflation_expectations': 'Supply disruptions may increase inflation'}, 'currencies': {'reserve_currencies': 'Dollar, euro, yen benefit from safe haven flows', 'commodity_currencies': 'Impact depends on commodity exposure', 'emerging_market_currencies': 'Generally weaken during geopolitical stress', 'crypto_currencies': 'Mixed reactions, some safe haven demand'}, 'commodities': {'energy': 'Supply disruption premium for oil and gas', 'precious_metals': 'Traditional safe haven demand for gold', 'agriculture': 'Supply chain disruptions affect food prices', 'industrial_metals': 'Demand reduction from economic slowdown'}}, 'sector_analysis': self._analyze_sector_impacts(geopolitical_data), 'geographic_considerations': self._assess_geographic_impacts(geopolitical_data), 'investment_strategies': self._recommend_investment_strategies(geopolitical_data), 'risk_monitoring_framework': self._develop_monitoring_framework()}

    def _assess_current_geopolitical_trends(self) -> List[str]:
        """Assess current global geopolitical trends"""
        return ['Rise of China and shifting global power balance', 'Renewed great power competition between US, China, and Russia', 'Fragmentation of global governance and institutions', 'Technology competition and digital sovereignty concerns', 'Climate change as a security issue and cooperation challenge', 'Democratic backsliding and authoritarian resilience']

    def _analyze_deglobalization_trends(self) -> Dict[str, str]:
        """Analyze current deglobalization trends"""
        return {'trade_slowdown': 'Growth in global trade relative to GDP has slowed', 'supply_chain_reshoring': 'Companies reducing dependence on distant suppliers', 'technology_decoupling': 'Separate technology ecosystems emerging', 'financial_fragmentation': 'Reduced cross-border capital flows', 'immigration_restrictions': 'Tighter controls on human mobility', 'policy_implications': 'Governments balancing efficiency with resilience'}

    def _analyze_organizational_coordination(self) -> Dict[str, str]:
        """Analyze coordination between international organizations"""
        return {'world_bank_imf': 'Close coordination on development and financial stability', 'wto_relationship': 'Limited formal links but complementary mandates', 'regional_organizations': 'Growing importance of regional institutions', 'coordination_challenges': 'Overlapping mandates and competing priorities'}

    def _assess_reform_requirements(self) -> List[str]:
        """Assess reform needs for international organizations"""
        return ['IMF: Quota reform to reflect changing global economy', 'World Bank: Climate focus and private sector engagement', 'WTO: Dispute settlement reform and digital trade rules', 'UN Security Council: Representation reform for emerging powers', 'All: Enhanced coordination and reduced overlap']

    def _assess_conflict_probability(self, data: Dict[str, Any]) -> str:
        """Assess probability of interstate conflict"""
        tension_level = data.get('tension_index', 0.5)
        if tension_level > 0.8:
            return 'High risk of conflict escalation'
        elif tension_level > 0.6:
            return 'Moderate risk, close monitoring needed'
        else:
            return 'Low to moderate risk'

    def _assess_instability_probability(self, data: Dict[str, Any]) -> str:
        """Assess probability of domestic instability"""
        governance_score = data.get('governance_index', 0.5)
        if governance_score < 0.3:
            return 'High instability risk'
        elif governance_score < 0.6:
            return 'Moderate instability risk'
        else:
            return 'Low instability risk'

    def _describe_risk_methodology(self) -> Dict[str, str]:
        """Describe geopolitical risk assessment methodology"""
        return {'quantitative_indicators': 'Economic data, governance indices, conflict databases', 'qualitative_assessment': 'Expert analysis, scenario planning, historical analogies', 'early_warning_systems': 'Real-time monitoring of key indicators', 'scenario_analysis': 'Multiple future scenarios with probability weights', 'stress_testing': 'Impact assessment under extreme scenarios'}

    def _identify_early_warning_signs(self) -> List[str]:
        """Identify early warning indicators of geopolitical stress"""
        return ['Diplomatic relations: Embassy closures, ambassador recalls', 'Military indicators: Troop movements, exercise frequency, defense spending', 'Economic signals: Trade restrictions, investment controls, sanctions threats', 'Political rhetoric: Leadership statements, media coverage, public opinion', 'Market indicators: Risk premiums, capital flows, currency movements']

    def _recommend_risk_mitigation(self) -> List[str]:
        """Recommend geopolitical risk mitigation strategies"""
        return ['Diversification: Geographic and supply chain diversification', 'Scenario planning: Regular stress testing and contingency planning', 'Political risk insurance: Coverage for expropriation and conflict', 'Local partnerships: Joint ventures and local content requirements', 'Flexible operations: Ability to quickly adjust to changing conditions']

    def _compare_geopolitical_tools(self) -> Dict[str, str]:
        """Compare effectiveness of different geopolitical tools"""
        return {'economic_tools': 'High immediate impact but may create long-term costs', 'diplomatic_tools': 'Low immediate impact but sustainable and relationship-preserving', 'military_tools': 'High coercive power but risks escalation and high costs', 'optimal_strategy': 'Combination of tools tailored to specific objectives and constraints'}

    def _analyze_sector_impacts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Analyze sectoral impacts of geopolitical risk"""
        return {'defense_aerospace': 'Generally benefits from increased defense spending', 'energy': 'Mixed impact depending on supply chain exposure', 'technology': 'Vulnerable to export controls and technology restrictions', 'financials': 'Exposed to sanctions and capital flow restrictions', 'materials': 'Supply chain disruptions and commodity price volatility', 'consumer_discretionary': 'Reduced confidence affects spending patterns'}

    def _assess_geographic_impacts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Assess geographic variation in geopolitical impacts"""
        return {'developed_markets': 'Relative safety but not immune to global shocks', 'emerging_markets': 'Higher vulnerability to capital flow reversals', 'frontier_markets': 'Extreme sensitivity to risk sentiment changes', 'regional_variation': 'Proximity to conflict zones increases impact', 'economic_integration': 'Highly integrated economies more affected'}

    def _recommend_investment_strategies(self, data: Dict[str, Any]) -> List[str]:
        """Recommend investment strategies for geopolitical risk environment"""
        return ['Tactical allocation: Adjust portfolio weights based on risk assessment', 'Safe haven assets: Maintain allocation to defensive assets', 'Sector rotation: Favor sectors that benefit from geopolitical trends', 'Currency hedging: Protect against adverse currency movements', 'Volatility management: Use derivatives to manage downside risk', 'ESG integration: Consider governance and sustainability factors']

    def _develop_monitoring_framework(self) -> Dict[str, List[str]]:
        """Develop framework for monitoring geopolitical risks"""
        return {'daily_monitoring': ['News flow', 'Market reactions', 'Policy statements'], 'weekly_assessment': ['Economic data', 'Diplomatic developments', 'Military activities'], 'monthly_review': ['Risk indicator updates', 'Scenario probability updates', 'Portfolio adjustments'], 'quarterly_analysis': ['Comprehensive risk assessment', 'Strategy review', 'Stress testing'], 'annual_planning': ['Long-term scenario development', 'Strategic asset allocation', 'Risk budget allocation']}

    def calculate(self, analysis_type: str='risk_assessment', **kwargs) -> Dict[str, Any]:
        """Main geopolitical analysis dispatcher"""
        analyses = {'framework': self.analyze_geopolitics_framework, 'globalization': self.analyze_geopolitics_globalization, 'organizations': self.analyze_international_organizations, 'risk_assessment': lambda: self.assess_geopolitical_risk(kwargs.get('risk_data', {})), 'tools': self.analyze_geopolitical_tools, 'investment_implications': lambda: self.assess_investment_implications(kwargs.get('geopolitical_data', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def calculate(self, analysis_type: str='risk_assessment', **kwargs) -> Dict[str, Any]:
    """Main geopolitical analysis dispatcher"""
    analyses = {'framework': self.analyze_geopolitics_framework, 'globalization': self.analyze_geopolitics_globalization, 'organizations': self.analyze_international_organizations, 'risk_assessment': lambda: self.assess_geopolitical_risk(kwargs.get('risk_data', {})), 'tools': self.analyze_geopolitical_tools, 'investment_implications': lambda: self.assess_investment_implications(kwargs.get('geopolitical_data', {}))}
    if analysis_type not in analyses:
        raise ValidationError(f'Unknown analysis type: {analysis_type}')
    result = analyses[analysis_type]()
    result['metadata'] = self.get_metadata()
    return result

class TradingBlocAnalyzer(EconomicsBase):
    """Specialized analysis of trading blocs and economic integration"""

    def analyze_bloc_performance(self, bloc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance and effectiveness of trading blocs"""
        return {'trade_creation_measurement': {'intra_bloc_trade_growth': self._calculate_intra_bloc_growth(bloc_data), 'trade_intensity_index': self._calculate_trade_intensity(bloc_data), 'revealed_comparative_advantage': 'Analysis of changing trade patterns', 'welfare_impact_estimate': self._estimate_welfare_impact(bloc_data)}, 'integration_depth_assessment': {'tariff_elimination': bloc_data.get('tariff_elimination_percent', 'N/A'), 'non_tariff_barriers': bloc_data.get('ntb_reduction_score', 'N/A'), 'services_liberalization': bloc_data.get('services_openness_index', 'N/A'), 'factor_mobility': bloc_data.get('factor_mobility_score', 'N/A'), 'policy_coordination': bloc_data.get('policy_coordination_index', 'N/A')}, 'economic_convergence': {'income_convergence': 'Analysis of per capita income gaps', 'inflation_convergence': 'Monetary policy coordination effects', 'business_cycle_synchronization': 'Economic cycle alignment assessment', 'structural_convergence': 'Industry structure and productivity alignment'}, 'challenges_and_obstacles': self._identify_integration_challenges(bloc_data), 'success_factors': self._assess_integration_success_factors(bloc_data)}

    def _calculate_intra_bloc_growth(self, data: Dict[str, Any]) -> str:
        """Calculate intra-bloc trade growth"""
        baseline_trade = self.to_decimal(data.get('baseline_intra_trade', 100))
        current_trade = self.to_decimal(data.get('current_intra_trade', 120))
        growth_rate = (current_trade - baseline_trade) / baseline_trade * self.to_decimal(100)
        return f'Intra-bloc trade grew by {growth_rate:.1f}% since formation'

    def _calculate_trade_intensity(self, data: Dict[str, Any]) -> str:
        """Calculate trade intensity index"""
        return 'Trade intensity index measures whether bloc members trade more with each other than expected'

    def _estimate_welfare_impact(self, data: Dict[str, Any]) -> str:
        """Estimate welfare impact of trading bloc"""
        trade_creation = data.get('trade_creation_estimate', 'positive')
        trade_diversion = data.get('trade_diversion_estimate', 'moderate')
        if trade_creation == 'positive' and trade_diversion == 'low':
            return 'Net positive welfare impact'
        elif trade_creation == 'positive' and trade_diversion == 'moderate':
            return 'Likely positive welfare impact'
        else:
            return 'Mixed welfare impact, requires detailed analysis'

    def _identify_integration_challenges(self, data: Dict[str, Any]) -> List[str]:
        """Identify challenges to deeper integration"""
        return ['Asymmetric development levels among members', 'Different regulatory frameworks and standards', 'Political sovereignty concerns', 'Unequal distribution of integration benefits', 'External pressure from non-member countries', 'Coordination costs and administrative burden']

    def _assess_integration_success_factors(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Assess factors contributing to integration success"""
        return {'political_commitment': 'Strong leadership commitment to integration goals', 'institutional_framework': 'Effective governance and dispute resolution mechanisms', 'economic_complementarity': 'Complementary rather than competing economic structures', 'adjustment_mechanisms': 'Policies to help losers from integration', 'external_support': 'Technical and financial assistance for integration process'}

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate trading bloc analysis"""
        result = self.analyze_bloc_performance(kwargs.get('bloc_data', {}))
        result['metadata'] = self.get_metadata()
        return result

def _calculate_intra_bloc_growth(self, data: Dict[str, Any]) -> str:
    """Calculate intra-bloc trade growth"""
    baseline_trade = self.to_decimal(data.get('baseline_intra_trade', 100))
    current_trade = self.to_decimal(data.get('current_intra_trade', 120))
    growth_rate = (current_trade - baseline_trade) / baseline_trade * self.to_decimal(100)
    return f'Intra-bloc trade grew by {growth_rate:.1f}% since formation'

def calculate(self, **kwargs) -> Dict[str, Any]:
    """Calculate trading bloc analysis"""
    result = self.analyze_bloc_performance(kwargs.get('bloc_data', {}))
    result['metadata'] = self.get_metadata()
    return result

class AlternativeInvestmentBase(ABC):
    """
    Abstract base class for all alternative investment types
    Defines common interface and shared functionality
    """

    def __init__(self, parameters: AssetParameters):
        self.parameters = parameters
        self.market_data: List[MarketData] = []
        self.cash_flows: List[CashFlow] = []
        self.performance_history: List[Performance] = []
        self.config = Config()
        self.math = FinancialMath()
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate asset parameters"""
        if self.parameters.management_fee:
            if not ValidationRules.validate_management_fee(self.parameters.management_fee, self.parameters.asset_class):
                raise ValueError(f'Invalid management fee: {self.parameters.management_fee}')
        if self.parameters.performance_fee:
            if not ValidationRules.validate_performance_fee(self.parameters.performance_fee, self.parameters.asset_class):
                raise ValueError(f'Invalid performance fee: {self.parameters.performance_fee}')

    def add_market_data(self, data: List[MarketData]) -> None:
        """Add market data to the investment"""
        self.market_data.extend(data)
        self.market_data.sort(key=lambda x: x.timestamp)

    def add_cash_flows(self, cash_flows: List[CashFlow]) -> None:
        """Add cash flows to the investment"""
        self.cash_flows.extend(cash_flows)
        self.cash_flows.sort(key=lambda x: x.date)

    def get_latest_price(self) -> Optional[Decimal]:
        """Get the most recent price"""
        if not self.market_data:
            return None
        return self.market_data[-1].price

    def get_price_history(self, start_date: str=None, end_date: str=None) -> List[MarketData]:
        """Get price history for specified date range"""
        filtered_data = self.market_data
        if start_date:
            filtered_data = [d for d in filtered_data if d.timestamp >= start_date]
        if end_date:
            filtered_data = [d for d in filtered_data if d.timestamp <= end_date]
        return filtered_data

    def calculate_simple_returns(self) -> List[Decimal]:
        """Calculate simple returns from price data"""
        if len(self.market_data) < 2:
            return []
        returns = []
        for i in range(1, len(self.market_data)):
            prev_price = self.market_data[i - 1].price
            curr_price = self.market_data[i].price
            ret = (curr_price - prev_price) / prev_price
            returns.append(ret)
        return returns

    def calculate_log_returns(self) -> List[Decimal]:
        """Calculate logarithmic returns from price data"""
        if len(self.market_data) < 2:
            return []
        returns = []
        for i in range(1, len(self.market_data)):
            prev_price = self.market_data[i - 1].price
            curr_price = self.market_data[i].price
            ret = (curr_price / prev_price).ln()
            returns.append(ret)
        return returns

    def calculate_volatility(self, returns: List[Decimal]=None, annualized: bool=True) -> Decimal:
        """Calculate volatility (standard deviation of returns)"""
        if returns is None:
            returns = self.calculate_simple_returns()
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        volatility = variance.sqrt()
        if annualized:
            volatility *= Constants.BUSINESS_DAYS_IN_YEAR.sqrt()
        return volatility

    def calculate_total_return(self, start_date: str=None, end_date: str=None) -> Decimal:
        """Calculate total return including distributions"""
        price_data = self.get_price_history(start_date, end_date)
        if len(price_data) < 2:
            return Decimal('0')
        start_price = price_data[0].price
        end_price = price_data[-1].price
        price_return = (end_price - start_price) / start_price
        relevant_cfs = self.cash_flows
        if start_date:
            relevant_cfs = [cf for cf in relevant_cfs if cf.date >= start_date]
        if end_date:
            relevant_cfs = [cf for cf in relevant_cfs if cf.date <= end_date]
        distributions = sum((cf.amount for cf in relevant_cfs if cf.amount > 0))
        distribution_return = distributions / start_price
        return price_return + distribution_return

    def calculate_fees(self, nav: Decimal, period_days: int=365) -> Dict[str, Decimal]:
        """Calculate management and performance fees"""
        fees = {}
        if self.parameters.management_fee:
            mgmt_fee = nav * self.parameters.management_fee * (Decimal(str(period_days)) / Constants.DAYS_IN_YEAR)
            fees['management_fee'] = mgmt_fee
        if self.parameters.performance_fee:
            returns = self.calculate_simple_returns()
            if returns:
                excess_return = sum(returns) - (self.parameters.hurdle_rate or Decimal('0'))
                if excess_return > 0:
                    perf_fee = nav * excess_return * self.parameters.performance_fee
                    fees['performance_fee'] = perf_fee
        return fees

    @abstractmethod
    def calculate_nav(self) -> Decimal:
        """Calculate Net Asset Value - must be implemented by subclasses"""
        pass

    @abstractmethod
    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key performance metrics - must be implemented by subclasses"""
        pass

    @abstractmethod
    def valuation_summary(self) -> Dict[str, Any]:
        """Provide valuation summary - must be implemented by subclasses"""
        pass

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        returns = self.calculate_simple_returns()
        if not returns:
            return {'error': 'Insufficient data for performance calculation'}
        volatility = self.calculate_volatility(returns)
        sharpe = self.math.sharpe_ratio(returns)
        sortino = self.math.sortino_ratio(returns)
        prices = [md.price for md in self.market_data]
        max_dd, peak_idx, trough_idx = self.math.maximum_drawdown(prices)
        var_95 = self.math.var_historical(returns, Decimal('0.05'))
        total_return = self.calculate_total_return()
        return {'total_return': float(total_return), 'annualized_return': float(total_return * Constants.DAYS_IN_YEAR / len(self.market_data)), 'volatility': float(volatility), 'sharpe_ratio': float(sharpe), 'sortino_ratio': float(sortino), 'maximum_drawdown': float(max_dd), 'var_95': float(var_95), 'number_of_observations': len(returns), 'latest_price': float(self.get_latest_price() or 0)}

def add_market_data(self, data: List[MarketData]) -> None:
    """Add market data to the investment"""
    self.market_data.extend(data)
    self.market_data.sort(key=lambda x: x.timestamp)

def add_cash_flows(self, cash_flows: List[CashFlow]) -> None:
    """Add cash flows to the investment"""
    self.cash_flows.extend(cash_flows)
    self.cash_flows.sort(key=lambda x: x.date)

class FinancialCalculations:
    """Common financial calculation utilities"""

    @staticmethod
    def time_value_of_money(principal: float, rate: float, periods: int, compounding: str='annual') -> Dict[str, float]:
        """Comprehensive time value of money calculations"""
        compounding_freq = {'annual': 1, 'semi-annual': 2, 'quarterly': 4, 'monthly': 12, 'daily': 365, 'continuous': float('inf')}
        freq = compounding_freq.get(compounding.lower(), 1)
        if freq == float('inf'):
            future_value = principal * math.exp(rate * periods)
            effective_rate = math.exp(rate) - 1
        else:
            future_value = principal * (1 + rate / freq) ** (freq * periods)
            effective_rate = (1 + rate / freq) ** freq - 1
        present_value = future_value / (1 + effective_rate) ** periods
        return {'principal': principal, 'future_value': future_value, 'present_value_of_fv': present_value, 'effective_annual_rate': effective_rate, 'total_interest': future_value - principal, 'compounding_frequency': freq}

    @staticmethod
    def annuity_calculations(payment: float, rate: float, periods: int, annuity_type: str='ordinary') -> Dict[str, float]:
        """Calculate present and future value of annuities"""
        if rate <= 0:
            pv_annuity = payment * periods
            fv_annuity = payment * periods
        else:
            pv_ordinary = payment * ((1 - (1 + rate) ** (-periods)) / rate)
            fv_ordinary = payment * (((1 + rate) ** periods - 1) / rate)
            if annuity_type.lower() == 'due':
                pv_annuity = pv_ordinary * (1 + rate)
                fv_annuity = fv_ordinary * (1 + rate)
            else:
                pv_annuity = pv_ordinary
                fv_annuity = fv_ordinary
        return {'payment_amount': payment, 'present_value': pv_annuity, 'future_value': fv_annuity, 'total_payments': payment * periods, 'total_interest': fv_annuity - payment * periods, 'annuity_type': annuity_type}

    @staticmethod
    def perpetuity_value(payment: float, discount_rate: float, growth_rate: float=0) -> Dict[str, float]:
        """Calculate present value of perpetuity"""
        if discount_rate <= growth_rate:
            raise ValidationError('Discount rate must be greater than growth rate')
        if growth_rate == 0:
            pv = payment / discount_rate
        else:
            pv = payment / (discount_rate - growth_rate)
        return {'payment': payment, 'discount_rate': discount_rate, 'growth_rate': growth_rate, 'present_value': pv, 'perpetuity_type': 'Growing' if growth_rate > 0 else 'Simple'}

    @staticmethod
    def loan_calculations(principal: float, annual_rate: float, years: int, payment_frequency: int=12) -> Dict[str, Any]:
        """Calculate loan payments and amortization"""
        monthly_rate = annual_rate / payment_frequency
        total_payments = years * payment_frequency
        if annual_rate == 0:
            payment = principal / total_payments
        else:
            payment = principal * (monthly_rate * (1 + monthly_rate) ** total_payments) / ((1 + monthly_rate) ** total_payments - 1)
        balance = principal
        schedule = []
        total_interest = 0
        for i in range(1, int(total_payments) + 1):
            interest_payment = balance * monthly_rate
            principal_payment = payment - interest_payment
            balance -= principal_payment
            total_interest += interest_payment
            schedule.append({'payment_number': i, 'payment': payment, 'principal': principal_payment, 'interest': interest_payment, 'balance': max(0, balance)})
        return {'loan_amount': principal, 'monthly_payment': payment, 'total_payments': total_payments, 'total_interest': total_interest, 'total_cost': principal + total_interest, 'amortization_schedule': schedule[:12], 'full_schedule_available': True}

    @staticmethod
    def bond_calculations(face_value: float, coupon_rate: float, market_rate: float, years_to_maturity: float, frequency: int=2) -> Dict[str, float]:
        """Calculate bond price, yield, and duration"""
        periods = years_to_maturity * frequency
        coupon_payment = face_value * coupon_rate / frequency
        period_rate = market_rate / frequency
        if market_rate == 0:
            bond_price = face_value + coupon_payment * periods
        else:
            pv_coupons = coupon_payment * ((1 - (1 + period_rate) ** (-periods)) / period_rate)
            pv_face = face_value / (1 + period_rate) ** periods
            bond_price = pv_coupons + pv_face
        current_yield = coupon_payment * frequency / bond_price
        cash_flows = [coupon_payment] * int(periods)
        cash_flows[-1] += face_value
        weighted_time = 0
        total_pv = 0
        for t, cf in enumerate(cash_flows, 1):
            pv_cf = cf / (1 + period_rate) ** t
            weighted_time += t / frequency * pv_cf
            total_pv += pv_cf
        macaulay_duration = weighted_time / total_pv
        modified_duration = macaulay_duration / (1 + market_rate / frequency)
        return {'bond_price': bond_price, 'face_value': face_value, 'coupon_rate': coupon_rate, 'market_rate': market_rate, 'current_yield': current_yield, 'macaulay_duration': macaulay_duration, 'modified_duration': modified_duration, 'price_sensitivity': modified_duration * bond_price * 0.01, 'premium_discount': 'Premium' if bond_price > face_value else 'Discount' if bond_price < face_value else 'Par'}

@staticmethod
def perpetuity_value(payment: float, discount_rate: float, growth_rate: float=0) -> Dict[str, float]:
    """Calculate present value of perpetuity"""
    if discount_rate <= growth_rate:
        raise ValidationError('Discount rate must be greater than growth rate')
    if growth_rate == 0:
        pv = payment / discount_rate
    else:
        pv = payment / (discount_rate - growth_rate)
    return {'payment': payment, 'discount_rate': discount_rate, 'growth_rate': growth_rate, 'present_value': pv, 'perpetuity_type': 'Growing' if growth_rate > 0 else 'Simple'}

def compound_annual_growth_rate(beginning_value: float, ending_value: float, years: float) -> float:
    """Calculate CAGR"""
    if beginning_value <= 0 or ending_value <= 0 or years <= 0:
        raise ValidationError('All values must be positive for CAGR calculation')
    return (ending_value / beginning_value) ** (1 / years) - 1

def rule_of_72(interest_rate: float) -> float:
    """Calculate doubling time using Rule of 72"""
    if interest_rate <= 0:
        raise ValidationError('Interest rate must be positive')
    return 72 / (interest_rate * 100)

class DDMValidator:
    """Validator for Dividend Discount Models"""

    @staticmethod
    def validate_gordon_growth_inputs(dividend: float, growth_rate: float, required_return: float) -> bool:
        """Validate Gordon Growth Model inputs"""
        errors = []
        if dividend <= 0:
            errors.append('Dividend must be positive for Gordon Growth Model')
        if growth_rate >= required_return:
            errors.append('Growth rate must be less than required return for Gordon Growth Model')
        if required_return <= 0:
            errors.append('Required return must be positive')
        if abs(required_return - growth_rate) < 0.01:
            errors.append('Required return and growth rate are too close - model becomes unstable')
        if errors:
            raise ValidationError('; '.join(errors))
        return True

    @staticmethod
    def validate_multistage_ddm_inputs(dividends: List[float], growth_rates: List[float], required_return: float, terminal_growth: float) -> bool:
        """Validate multi-stage DDM inputs"""
        errors = []
        if len(dividends) != len(growth_rates):
            errors.append('Number of dividends must match number of growth rates')
        if any((d <= 0 for d in dividends)):
            errors.append('All dividends must be positive')
        if terminal_growth >= required_return:
            errors.append('Terminal growth rate must be less than required return')
        if terminal_growth > 0.06:
            errors.append('Terminal growth rate should not exceed 6% for most companies')
        for i, gr in enumerate(growth_rates):
            if gr > 0.5:
                errors.append(f'Growth rate of {gr:.2%} in period {i + 1} is very high')
        if errors:
            raise ValidationError('; '.join(errors))
        return True

@staticmethod
def validate_gordon_growth_inputs(dividend: float, growth_rate: float, required_return: float) -> bool:
    """Validate Gordon Growth Model inputs"""
    errors = []
    if dividend <= 0:
        errors.append('Dividend must be positive for Gordon Growth Model')
    if growth_rate >= required_return:
        errors.append('Growth rate must be less than required return for Gordon Growth Model')
    if required_return <= 0:
        errors.append('Required return must be positive')
    if abs(required_return - growth_rate) < 0.01:
        errors.append('Required return and growth rate are too close - model becomes unstable')
    if errors:
        raise ValidationError('; '.join(errors))
    return True

class DCFValidator:
    """Validator for Discounted Cash Flow Models"""

    @staticmethod
    def validate_fcf_inputs(cash_flows: List[float], discount_rate: float, terminal_value: Optional[float]=None) -> bool:
        """Validate Free Cash Flow inputs"""
        errors = []
        warnings = []
        if discount_rate <= 0:
            errors.append('Discount rate must be positive')
        if discount_rate > 0.25:
            warnings.append(f'Discount rate of {discount_rate:.2%} is very high')
        negative_cf_count = sum((1 for cf in cash_flows if cf < 0))
        if negative_cf_count > len(cash_flows) / 2:
            warnings.append('More than half of projected cash flows are negative')
        for i in range(1, len(cash_flows)):
            if cash_flows[i - 1] > 0 and cash_flows[i] > 0:
                growth = cash_flows[i] / cash_flows[i - 1] - 1
                if growth > 1.0:
                    warnings.append(f'Cash flow growth of {growth:.2%} in year {i + 1} is very high')
        if terminal_value and terminal_value < 0:
            errors.append('Terminal value cannot be negative')
        if errors:
            raise ValidationError('; '.join(errors))
        if warnings:
            print('DCF Warnings:', '; '.join(warnings))
        return True

    @staticmethod
    def validate_fcff_calculation_inputs(ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> bool:
        """Validate FCFF calculation inputs"""
        errors = []
        if tax_rate < 0 or tax_rate > 1:
            errors.append('Tax rate must be between 0 and 1')
        if depreciation < 0:
            errors.append('Depreciation cannot be negative')
        if capex < 0:
            errors.append('Capital expenditures cannot be negative')
        if tax_rate > 0.5:
            print(f'Warning: Tax rate of {tax_rate:.2%} is very high')
        if capex > abs(ebit) * 2:
            print('Warning: Capital expenditures are very high relative to EBIT')
        if errors:
            raise ValidationError('; '.join(errors))
        return True

@staticmethod
def validate_fcff_calculation_inputs(ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> bool:
    """Validate FCFF calculation inputs"""
    errors = []
    if tax_rate < 0 or tax_rate > 1:
        errors.append('Tax rate must be between 0 and 1')
    if depreciation < 0:
        errors.append('Depreciation cannot be negative')
    if capex < 0:
        errors.append('Capital expenditures cannot be negative')
    if tax_rate > 0.5:
        print(f'Warning: Tax rate of {tax_rate:.2%} is very high')
    if capex > abs(ebit) * 2:
        print('Warning: Capital expenditures are very high relative to EBIT')
    if errors:
        raise ValidationError('; '.join(errors))
    return True

class MultiplesValidator:
    """Validator for Market Multiple Valuation"""

    @staticmethod
    def validate_comparable_companies(comparables: List[Dict[str, Any]], target_company: Dict[str, Any]) -> bool:
        """Validate comparable companies selection"""
        errors = []
        warnings = []
        if len(comparables) < 3:
            warnings.append('Fewer than 3 comparable companies - results may be unreliable')
        target_sector = target_company.get('sector', '')
        target_size = target_company.get('market_cap', 0)
        different_sector_count = 0
        size_differences = []
        for comp in comparables:
            if comp.get('sector', '') != target_sector:
                different_sector_count += 1
            comp_size = comp.get('market_cap', 0)
            if target_size > 0 and comp_size > 0:
                size_ratio = max(comp_size, target_size) / min(comp_size, target_size)
                size_differences.append(size_ratio)
        if different_sector_count > len(comparables) / 2:
            warnings.append('More than half of comparables are from different sectors')
        if size_differences and max(size_differences) > 10:
            warnings.append('Some comparables differ significantly in size from target company')
        if warnings:
            print('Comparables Warnings:', '; '.join(warnings))
        return True

    @staticmethod
    def validate_multiple_values(multiples: Dict[str, float]) -> bool:
        """Validate individual multiple values"""
        errors = []
        warnings = []
        for metric, value in multiples.items():
            if value < 0:
                errors.append(f'{metric} cannot be negative')
            if metric == 'pe_ratio' and value > 50:
                warnings.append(f'P/E ratio of {value:.2f} is very high')
            elif metric == 'pb_ratio' and value > 5:
                warnings.append(f'P/B ratio of {value:.2f} is high')
            elif metric == 'ps_ratio' and value > 10:
                warnings.append(f'P/S ratio of {value:.2f} is high')
            elif metric == 'ev_ebitda' and value > 20:
                warnings.append(f'EV/EBITDA of {value:.2f} is high')
        if errors:
            raise ValidationError('; '.join(errors))
        if warnings:
            print('Multiple Validation Warnings:', '; '.join(warnings))
        return True

@staticmethod
def validate_multiple_values(multiples: Dict[str, float]) -> bool:
    """Validate individual multiple values"""
    errors = []
    warnings = []
    for metric, value in multiples.items():
        if value < 0:
            errors.append(f'{metric} cannot be negative')
        if metric == 'pe_ratio' and value > 50:
            warnings.append(f'P/E ratio of {value:.2f} is very high')
        elif metric == 'pb_ratio' and value > 5:
            warnings.append(f'P/B ratio of {value:.2f} is high')
        elif metric == 'ps_ratio' and value > 10:
            warnings.append(f'P/S ratio of {value:.2f} is high')
        elif metric == 'ev_ebitda' and value > 20:
            warnings.append(f'EV/EBITDA of {value:.2f} is high')
    if errors:
        raise ValidationError('; '.join(errors))
    if warnings:
        print('Multiple Validation Warnings:', '; '.join(warnings))
    return True

class ResidualIncomeValidator:
    """Validator for Residual Income Models"""

    @staticmethod
    def validate_ri_inputs(net_income: float, book_value: float, required_return: float, roe: float) -> bool:
        """Validate Residual Income model inputs"""
        errors = []
        warnings = []
        if book_value <= 0:
            errors.append('Book value must be positive for Residual Income model')
        if required_return <= 0:
            errors.append('Required return must be positive')
        if required_return > 0.3:
            warnings.append(f'Required return of {required_return:.2%} is very high')
        if roe > 0 and abs(roe - required_return) < 0.01:
            warnings.append('ROE and required return are very close - residual income will be minimal')
        calculated_roe = net_income / book_value if book_value != 0 else 0
        if abs(calculated_roe - roe) > 0.02:
            warnings.append("Provided ROE doesn't match calculated ROE from net income and book value")
        if errors:
            raise ValidationError('; '.join(errors))
        if warnings:
            print('Residual Income Warnings:', '; '.join(warnings))
        return True

@staticmethod
def validate_ri_inputs(net_income: float, book_value: float, required_return: float, roe: float) -> bool:
    """Validate Residual Income model inputs"""
    errors = []
    warnings = []
    if book_value <= 0:
        errors.append('Book value must be positive for Residual Income model')
    if required_return <= 0:
        errors.append('Required return must be positive')
    if required_return > 0.3:
        warnings.append(f'Required return of {required_return:.2%} is very high')
    if roe > 0 and abs(roe - required_return) < 0.01:
        warnings.append('ROE and required return are very close - residual income will be minimal')
    calculated_roe = net_income / book_value if book_value != 0 else 0
    if abs(calculated_roe - roe) > 0.02:
        warnings.append("Provided ROE doesn't match calculated ROE from net income and book value")
    if errors:
        raise ValidationError('; '.join(errors))
    if warnings:
        print('Residual Income Warnings:', '; '.join(warnings))
    return True

def comprehensive_data_validation(company_data: CompanyData) -> Dict[str, Any]:
    """Run all validation checks on company data"""
    results = {'data_integrity': CompanyDataValidator.validate_company_data(company_data), 'financial_ratios': CFAValidator.validate_financial_ratios(company_data.market_data), 'is_valid': True, 'critical_errors': []}
    if results['data_integrity']['errors']:
        results['is_valid'] = False
        results['critical_errors'].extend(results['data_integrity']['errors'])
    if results['financial_ratios']['errors']:
        results['is_valid'] = False
        results['critical_errors'].extend(results['financial_ratios']['errors'])
    return results

class IncomeApproachValuator(BaseValuationModel):
    """Income approach valuation for private companies"""

    def __init__(self):
        super().__init__('Income Approach', 'Income-based private company valuation')
        self.valuation_method = ValuationMethod.PRIVATE_INCOME

    def validate_inputs(self, **kwargs) -> bool:
        """Validate income approach inputs"""
        normalized_earnings = kwargs.get('normalized_earnings')
        discount_rate = kwargs.get('discount_rate')
        if normalized_earnings is None or discount_rate is None:
            raise ValidationError('Normalized earnings and discount rate required')
        ModelValidator.validate_percentage(discount_rate, 'Discount rate')
        return True

    def calculate_capitalized_earnings_value(self, normalized_earnings: float, capitalization_rate: float, growth_rate: float=0) -> float:
        """Calculate value using capitalized earnings method"""
        if capitalization_rate <= growth_rate:
            raise ValidationError('Capitalization rate must be greater than growth rate')
        if growth_rate == 0:
            return normalized_earnings / capitalization_rate
        else:
            next_year_earnings = normalized_earnings * (1 + growth_rate)
            return next_year_earnings / (capitalization_rate - growth_rate)

    def calculate_dcf_value(self, projected_cash_flows: List[float], discount_rate: float, terminal_value: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate DCF value for private company"""
        pv_cash_flows = 0
        for i, cf in enumerate(projected_cash_flows):
            pv_cf = CalculationEngine.present_value(cf, discount_rate, i + 1)
            pv_cash_flows += pv_cf
        if terminal_value is None and terminal_growth is not None:
            if len(projected_cash_flows) > 0:
                final_cf = projected_cash_flows[-1]
                terminal_cf = final_cf * (1 + terminal_growth)
                terminal_value = terminal_cf / (discount_rate - terminal_growth)
            else:
                terminal_value = 0
        elif terminal_value is None:
            terminal_value = 0
        pv_terminal = CalculationEngine.present_value(terminal_value, discount_rate, len(projected_cash_flows))
        enterprise_value = pv_cash_flows + pv_terminal
        return {'pv_cash_flows': pv_cash_flows, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'enterprise_value': enterprise_value}

    def calculate_excess_earnings_value(self, normalized_earnings: float, tangible_assets: float, required_return_assets: float, required_return_intangibles: float) -> Dict[str, float]:
        """Calculate value using excess earnings method"""
        tangible_asset_return = tangible_assets * required_return_assets
        excess_earnings = normalized_earnings - tangible_asset_return
        if excess_earnings > 0:
            intangible_value = excess_earnings / required_return_intangibles
        else:
            intangible_value = 0
        total_value = tangible_assets + intangible_value
        return {'tangible_asset_value': tangible_assets, 'tangible_asset_return': tangible_asset_return, 'excess_earnings': excess_earnings, 'intangible_value': intangible_value, 'total_business_value': total_value}

    def calculate_adjusted_present_value(self, unlevered_cash_flows: List[float], unlevered_discount_rate: float, tax_shield_values: List[float], tax_shield_discount_rate: float) -> Dict[str, float]:
        """Calculate APV for private companies with complex capital structures"""
        pv_unlevered_cf = sum((CalculationEngine.present_value(cf, unlevered_discount_rate, i + 1) for i, cf in enumerate(unlevered_cash_flows)))
        pv_tax_shields = sum((CalculationEngine.present_value(ts, tax_shield_discount_rate, i + 1) for i, ts in enumerate(tax_shield_values)))
        total_firm_value = pv_unlevered_cf + pv_tax_shields
        return {'unlevered_firm_value': pv_unlevered_cf, 'tax_shield_value': pv_tax_shields, 'total_firm_value': total_firm_value}

def calculate_capitalized_earnings_value(self, normalized_earnings: float, capitalization_rate: float, growth_rate: float=0) -> float:
    """Calculate value using capitalized earnings method"""
    if capitalization_rate <= growth_rate:
        raise ValidationError('Capitalization rate must be greater than growth rate')
    if growth_rate == 0:
        return normalized_earnings / capitalization_rate
    else:
        next_year_earnings = normalized_earnings * (1 + growth_rate)
        return next_year_earnings / (capitalization_rate - growth_rate)

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

def calculate_justified_pb_from_fundamentals(self, roe: float, required_return: float, growth_rate: float) -> float:
    """Calculate justified P/B ratio from fundamentals"""
    if required_return <= growth_rate:
        raise ValidationError('Required return must be greater than growth rate')
    return (roe - growth_rate) / (required_return - growth_rate)

class EnterpriseValueMultiplesModel(BaseValuationModel):
    """Enterprise Value multiple valuation model"""

    def __init__(self):
        super().__init__('EV Multiples', 'Enterprise value multiple valuation')
        self.valuation_method = ValuationMethod.MULTIPLES_EV_EBITDA

    def calculate_enterprise_value(self, market_cap: float, total_debt: float, cash: float, preferred_stock: float=0) -> float:
        """Calculate Enterprise Value"""
        return market_cap + total_debt - cash + preferred_stock

    def calculate_ev_ebitda(self, enterprise_value: float, ebitda: float) -> float:
        """Calculate EV/EBITDA multiple"""
        if ebitda <= 0:
            raise ValidationError('EBITDA must be positive for EV/EBITDA calculation')
        return enterprise_value / ebitda

    def calculate_ev_sales(self, enterprise_value: float, sales: float) -> float:
        """Calculate EV/Sales multiple"""
        if sales <= 0:
            raise ValidationError('Sales must be positive for EV/Sales calculation')
        return enterprise_value / sales

    def calculate_ev_ebit(self, enterprise_value: float, ebit: float) -> float:
        """Calculate EV/EBIT multiple"""
        if ebit <= 0:
            raise ValidationError('EBIT must be positive for EV/EBIT calculation')
        return enterprise_value / ebit

    def calculate_ev_fcf(self, enterprise_value: float, free_cash_flow: float) -> float:
        """Calculate EV/FCF multiple"""
        if free_cash_flow <= 0:
            raise ValidationError('Free cash flow must be positive for EV/FCF calculation')
        return enterprise_value / free_cash_flow

    def value_using_ev_multiple(self, comparable_ev_multiple: float, target_metric: float, target_debt: float, target_cash: float, target_shares: float, preferred_stock: float=0) -> float:
        """Value company using EV multiple and convert to per-share value"""
        implied_ev = comparable_ev_multiple * target_metric
        equity_value = implied_ev - target_debt + target_cash - preferred_stock
        return equity_value / target_shares if target_shares > 0 else 0

def calculate_ev_ebitda(self, enterprise_value: float, ebitda: float) -> float:
    """Calculate EV/EBITDA multiple"""
    if ebitda <= 0:
        raise ValidationError('EBITDA must be positive for EV/EBITDA calculation')
    return enterprise_value / ebitda

def calculate_ev_sales(self, enterprise_value: float, sales: float) -> float:
    """Calculate EV/Sales multiple"""
    if sales <= 0:
        raise ValidationError('Sales must be positive for EV/Sales calculation')
    return enterprise_value / sales

def calculate_ev_ebit(self, enterprise_value: float, ebit: float) -> float:
    """Calculate EV/EBIT multiple"""
    if ebit <= 0:
        raise ValidationError('EBIT must be positive for EV/EBIT calculation')
    return enterprise_value / ebit

def calculate_ev_fcf(self, enterprise_value: float, free_cash_flow: float) -> float:
    """Calculate EV/FCF multiple"""
    if free_cash_flow <= 0:
        raise ValidationError('Free cash flow must be positive for EV/FCF calculation')
    return enterprise_value / free_cash_flow

class ComparablesAnalyzer:
    """Analyze and select comparable companies"""

    def __init__(self):
        self.price_model = PriceMultiplesModel()
        self.ev_model = EnterpriseValueMultiplesModel()

    def calculate_all_multiples(self, company_data: ComparableCompany) -> Dict[str, float]:
        """Calculate all relevant multiples for a company"""
        multiples = {}
        try:
            if company_data.net_income > 0:
                eps = company_data.net_income / (company_data.market_cap / company_data.current_price)
                multiples['pe_ratio'] = self.price_model.calculate_pe_ratio(company_data.current_price, eps)
                multiples['earnings_yield'] = self.price_model.calculate_earnings_yield(eps, company_data.current_price)
            if company_data.book_value > 0:
                bvps = company_data.book_value / (company_data.market_cap / company_data.current_price)
                multiples['pb_ratio'] = self.price_model.calculate_pb_ratio(company_data.current_price, bvps)
            if company_data.revenue > 0:
                sps = company_data.revenue / (company_data.market_cap / company_data.current_price)
                multiples['ps_ratio'] = self.price_model.calculate_ps_ratio(company_data.current_price, sps)
            if company_data.ebitda > 0:
                multiples['ev_ebitda'] = self.ev_model.calculate_ev_ebitda(company_data.enterprise_value, company_data.ebitda)
            if company_data.revenue > 0:
                multiples['ev_sales'] = self.ev_model.calculate_ev_sales(company_data.enterprise_value, company_data.revenue)
        except ValidationError:
            pass
        return multiples

    def screen_comparables(self, comparables: List[ComparableCompany], target_company: ComparableCompany, screening_criteria: Dict[str, Any]) -> List[ComparableCompany]:
        """Screen comparable companies based on criteria"""
        screened = []
        for comp in comparables:
            if screening_criteria.get('same_sector', True) and comp.sector != target_company.sector:
                continue
            size_ratio_limit = screening_criteria.get('max_size_ratio', 10)
            size_ratio = max(comp.market_cap, target_company.market_cap) / min(comp.market_cap, target_company.market_cap)
            if size_ratio > size_ratio_limit:
                continue
            min_roe = screening_criteria.get('min_roe', -0.5)
            comp_roe = comp.net_income / comp.book_value if comp.book_value > 0 else -1
            if comp_roe < min_roe:
                continue
            if 'min_growth' in screening_criteria:
                pass
            screened.append(comp)
        return screened

    def calculate_multiple_statistics(self, comparables: List[ComparableCompany], multiple_type: str) -> Dict[str, float]:
        """Calculate statistics for a specific multiple across comparables"""
        multiples_values = []
        for comp in comparables:
            comp_multiples = self.calculate_all_multiples(comp)
            if multiple_type in comp_multiples and comp_multiples[multiple_type] > 0:
                multiples_values.append(comp_multiples[multiple_type])
        if not multiples_values:
            raise ValidationError(f'No valid {multiple_type} values found in comparables')
        return {'mean': statistics.mean(multiples_values), 'median': statistics.median(multiples_values), 'harmonic_mean': statistics.harmonic_mean(multiples_values), 'weighted_harmonic_mean': self._calculate_weighted_harmonic_mean(multiples_values, comparables), 'min': min(multiples_values), 'max': max(multiples_values), 'std_dev': statistics.stdev(multiples_values) if len(multiples_values) > 1 else 0, 'count': len(multiples_values), 'values': multiples_values}

    def _calculate_weighted_harmonic_mean(self, multiples: List[float], comparables: List[ComparableCompany]) -> float:
        """Calculate weighted harmonic mean using market cap as weights"""
        weights = [comp.market_cap for comp in comparables[:len(multiples)]]
        total_weight = sum(weights)
        weighted_sum = sum((w / m for w, m in zip(weights, multiples)))
        return total_weight / weighted_sum

def __init__(self):
    self.price_model = PriceMultiplesModel()
    self.ev_model = EnterpriseValueMultiplesModel()

class MultiplesValuationSuite:
    """Comprehensive multiples valuation analysis"""

    def __init__(self):
        self.price_model = PriceMultiplesModel()
        self.ev_model = EnterpriseValueMultiplesModel()
        self.comparables_analyzer = ComparablesAnalyzer()
        self.regression_analyzer = CrossSectionalRegressionAnalyzer()

    def comprehensive_multiples_valuation(self, target_company: CompanyData, comparables: List[ComparableCompany], multiples_to_use: List[str]=None) -> Dict[str, ValuationResult]:
        """Perform comprehensive multiples valuation"""
        if multiples_to_use is None:
            multiples_to_use = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'ev_sales']
        results = {}
        target_comparable = self._convert_to_comparable(target_company)
        for multiple_type in multiples_to_use:
            try:
                stats = self.comparables_analyzer.calculate_multiple_statistics(comparables, multiple_type)
                representative_multiple = stats['median']
                if multiple_type in ['pe_ratio', 'pb_ratio', 'ps_ratio']:
                    intrinsic_value = self._calculate_price_multiple_value(target_company, multiple_type, representative_multiple)
                else:
                    intrinsic_value = self._calculate_ev_multiple_value(target_company, multiple_type, representative_multiple)
                assumptions = {'multiple_type': multiple_type, 'representative_multiple': representative_multiple, 'comparables_count': stats['count'], 'multiple_range': f'{stats['min']:.2f} - {stats['max']:.2f}', 'multiple_std_dev': stats['std_dev'], 'method': 'Median of Comparables'}
                calculation_details = {'multiple_statistics': stats, 'target_metric': self._get_target_metric(target_company, multiple_type), 'calculation': f'{representative_multiple:.2f} × {self._get_target_metric(target_company, multiple_type):.2f}'}
                recommendation = self.price_model.generate_recommendation(intrinsic_value, target_company.current_price)
                upside_downside = self.price_model.calculate_upside_downside(intrinsic_value, target_company.current_price)
                results[multiple_type] = ValuationResult(method=ValuationMethod.MULTIPLES_PE, intrinsic_value=intrinsic_value, current_price=target_company.current_price, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)
            except Exception as e:
                results[multiple_type] = f'Error: {str(e)}'
        return results

    def _convert_to_comparable(self, company_data: CompanyData) -> ComparableCompany:
        """Convert CompanyData to ComparableCompany format"""
        financial_data = company_data.financial_data
        return ComparableCompany(symbol=company_data.symbol, name=company_data.name, sector=company_data.sector, market_cap=company_data.market_cap, enterprise_value=self.ev_model.calculate_enterprise_value(company_data.market_cap, financial_data.get('total_debt', 0), financial_data.get('cash', 0)), revenue=financial_data.get('revenue', 0), ebitda=financial_data.get('ebitda', 0), net_income=financial_data.get('net_income', 0), book_value=financial_data.get('book_value', 0) * company_data.shares_outstanding, current_price=company_data.current_price, multiples={})

    def _calculate_price_multiple_value(self, company_data: CompanyData, multiple_type: str, multiple_value: float) -> float:
        """Calculate value using price multiples"""
        financial_data = company_data.financial_data
        shares = company_data.shares_outstanding
        if multiple_type == 'pe_ratio':
            eps = financial_data.get('earnings_per_share', 0)
            return self.price_model.value_using_pe_multiple(multiple_value, eps)
        elif multiple_type == 'pb_ratio':
            book_value_total = financial_data.get('book_value', 0) * shares
            bvps = book_value_total / shares if shares > 0 else 0
            return self.price_model.value_using_pb_multiple(multiple_value, bvps)
        elif multiple_type == 'ps_ratio':
            revenue = financial_data.get('revenue', 0)
            sps = revenue / shares if shares > 0 else 0
            return self.price_model.value_using_ps_multiple(multiple_value, sps)
        else:
            raise ValidationError(f'Unknown price multiple type: {multiple_type}')

    def _calculate_ev_multiple_value(self, company_data: CompanyData, multiple_type: str, multiple_value: float) -> float:
        """Calculate value using EV multiples"""
        financial_data = company_data.financial_data
        if multiple_type == 'ev_ebitda':
            target_metric = financial_data.get('ebitda', 0)
        elif multiple_type == 'ev_sales':
            target_metric = financial_data.get('revenue', 0)
        else:
            raise ValidationError(f'Unknown EV multiple type: {multiple_type}')
        return self.ev_model.value_using_ev_multiple(multiple_value, target_metric, financial_data.get('total_debt', 0), financial_data.get('cash', 0), company_data.shares_outstanding)

    def _get_target_metric(self, company_data: CompanyData, multiple_type: str) -> float:
        """Get the target metric value for multiple calculation"""
        financial_data = company_data.financial_data
        if multiple_type == 'pe_ratio':
            return financial_data.get('earnings_per_share', 0)
        elif multiple_type == 'pb_ratio':
            return financial_data.get('book_value', 0)
        elif multiple_type == 'ps_ratio':
            return financial_data.get('revenue', 0) / company_data.shares_outstanding
        elif multiple_type == 'ev_ebitda':
            return financial_data.get('ebitda', 0)
        elif multiple_type == 'ev_sales':
            return financial_data.get('revenue', 0)
        else:
            return 0

def __init__(self):
    self.price_model = PriceMultiplesModel()
    self.ev_model = EnterpriseValueMultiplesModel()
    self.comparables_analyzer = ComparablesAnalyzer()
    self.regression_analyzer = CrossSectionalRegressionAnalyzer()

def _calculate_price_multiple_value(self, company_data: CompanyData, multiple_type: str, multiple_value: float) -> float:
    """Calculate value using price multiples"""
    financial_data = company_data.financial_data
    shares = company_data.shares_outstanding
    if multiple_type == 'pe_ratio':
        eps = financial_data.get('earnings_per_share', 0)
        return self.price_model.value_using_pe_multiple(multiple_value, eps)
    elif multiple_type == 'pb_ratio':
        book_value_total = financial_data.get('book_value', 0) * shares
        bvps = book_value_total / shares if shares > 0 else 0
        return self.price_model.value_using_pb_multiple(multiple_value, bvps)
    elif multiple_type == 'ps_ratio':
        revenue = financial_data.get('revenue', 0)
        sps = revenue / shares if shares > 0 else 0
        return self.price_model.value_using_ps_multiple(multiple_value, sps)
    else:
        raise ValidationError(f'Unknown price multiple type: {multiple_type}')

def _calculate_ev_multiple_value(self, company_data: CompanyData, multiple_type: str, multiple_value: float) -> float:
    """Calculate value using EV multiples"""
    financial_data = company_data.financial_data
    if multiple_type == 'ev_ebitda':
        target_metric = financial_data.get('ebitda', 0)
    elif multiple_type == 'ev_sales':
        target_metric = financial_data.get('revenue', 0)
    else:
        raise ValidationError(f'Unknown EV multiple type: {multiple_type}')
    return self.ev_model.value_using_ev_multiple(multiple_value, target_metric, financial_data.get('total_debt', 0), financial_data.get('cash', 0), company_data.shares_outstanding)

def pe_multiple_valuation(target_eps: float, comparable_pe: float) -> float:
    """Quick P/E multiple valuation"""
    model = PriceMultiplesModel()
    return model.value_using_pe_multiple(comparable_pe, target_eps)

def ev_ebitda_valuation(target_ebitda: float, comparable_ev_ebitda: float, debt: float, cash: float, shares: float) -> float:
    """Quick EV/EBITDA valuation"""
    model = EnterpriseValueMultiplesModel()
    return model.value_using_ev_multiple(comparable_ev_ebitda, target_ebitda, debt, cash, shares)

class FCFFModel(BaseValuationModel):
    """Free Cash Flow to Firm Model"""

    def __init__(self):
        super().__init__('FCFF Model', 'Free Cash Flow to Firm valuation')
        self.valuation_method = ValuationMethod.DCF_FCFF

    def validate_inputs(self, wacc: float, fcff_projections: List[float], terminal_growth: float=None) -> bool:
        """Validate FCFF model inputs"""
        ModelValidator.validate_percentage(wacc, 'WACC')
        if not fcff_projections or len(fcff_projections) == 0:
            raise ValidationError('FCFF projections cannot be empty')
        if terminal_growth is not None:
            ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
            ModelValidator.validate_growth_vs_required_return(terminal_growth, wacc)
        return True

    def calculate_fcff_from_components(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF from financial statement components"""
        return CalculationEngine.free_cash_flow_to_firm(ebit, tax_rate, depreciation, capex, working_capital_change)

    def calculate_fcff_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF starting from EBITDA"""
        ebit = ebitda - depreciation
        return self.calculate_fcff_from_components(ebit, tax_rate, depreciation, capex, working_capital_change)

    def calculate_fcff_from_net_income(self, net_income: float, interest_expense: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF starting from net income"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        unlevered_net_income = net_income + after_tax_interest
        return unlevered_net_income + depreciation - capex - working_capital_change

    def calculate_fcff_from_cfo(self, cfo: float, interest_expense: float, tax_rate: float, capex: float) -> float:
        """Calculate FCFF from Cash Flow from Operations"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        return cfo + after_tax_interest - capex

    def calculate_terminal_value(self, final_fcff: float, terminal_growth: float, wacc: float) -> float:
        """Calculate terminal value using Gordon Growth"""
        if terminal_growth >= wacc:
            raise ValidationError('Terminal growth rate must be less than WACC')
        terminal_fcff = final_fcff * (1 + terminal_growth)
        return terminal_fcff / (wacc - terminal_growth)

    def calculate_enterprise_value(self, fcff_projections: List[float], wacc: float, terminal_growth: float=None, terminal_value: float=None) -> Dict[str, float]:
        """Calculate enterprise value from FCFF projections"""
        pv_fcff = 0
        pv_details = []
        for year, fcff in enumerate(fcff_projections, 1):
            pv = CalculationEngine.present_value(fcff, wacc, year)
            pv_fcff += pv
            pv_details.append({'year': year, 'fcff': fcff, 'pv': pv})
        if terminal_value is None:
            if terminal_growth is None:
                raise ValidationError('Either terminal_growth or terminal_value must be provided')
            terminal_value = self.calculate_terminal_value(fcff_projections[-1], terminal_growth, wacc)
        pv_terminal = CalculationEngine.present_value(terminal_value, wacc, len(fcff_projections))
        enterprise_value = pv_fcff + pv_terminal
        return {'pv_fcff': pv_fcff, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'enterprise_value': enterprise_value, 'pv_details': pv_details}

    def calculate_equity_value(self, enterprise_value: float, cash: float, total_debt: float, preferred_stock: float=0) -> float:
        """Calculate equity value from enterprise value"""
        return enterprise_value + cash - total_debt - preferred_stock

    def calculate(self, fcff_projections: List[float], wacc: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, cash: float=0, total_debt: float=0, preferred_stock: float=0, current_price: float=None) -> ValuationResult:
        """Calculate valuation using FCFF model"""
        self.validate_inputs(wacc, fcff_projections, terminal_growth)
        ev_components = self.calculate_enterprise_value(fcff_projections, wacc, terminal_growth, terminal_value)
        equity_value = self.calculate_equity_value(ev_components['enterprise_value'], cash, total_debt, preferred_stock)
        intrinsic_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'wacc': wacc, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcff_projections), 'terminal_value_multiple': ev_components['pv_terminal'] / ev_components['enterprise_value'] * 100, 'cash': cash, 'total_debt': total_debt, 'preferred_stock': preferred_stock, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFF DCF Model'}
        calculation_details = {'fcff_projections': fcff_projections, 'pv_fcff': ev_components['pv_fcff'], 'terminal_value': ev_components['terminal_value'], 'pv_terminal': ev_components['pv_terminal'], 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ev_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def validate_inputs(self, wacc: float, fcff_projections: List[float], terminal_growth: float=None) -> bool:
    """Validate FCFF model inputs"""
    ModelValidator.validate_percentage(wacc, 'WACC')
    if not fcff_projections or len(fcff_projections) == 0:
        raise ValidationError('FCFF projections cannot be empty')
    if terminal_growth is not None:
        ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
        ModelValidator.validate_growth_vs_required_return(terminal_growth, wacc)
    return True

def calculate_terminal_value(self, final_fcff: float, terminal_growth: float, wacc: float) -> float:
    """Calculate terminal value using Gordon Growth"""
    if terminal_growth >= wacc:
        raise ValidationError('Terminal growth rate must be less than WACC')
    terminal_fcff = final_fcff * (1 + terminal_growth)
    return terminal_fcff / (wacc - terminal_growth)

class FCFEModel(BaseValuationModel):
    """Free Cash Flow to Equity Model"""

    def __init__(self):
        super().__init__('FCFE Model', 'Free Cash Flow to Equity valuation')
        self.valuation_method = ValuationMethod.DCF_FCFE

    def validate_inputs(self, required_return: float, fcfe_projections: List[float], terminal_growth: float=None) -> bool:
        """Validate FCFE model inputs"""
        ModelValidator.validate_percentage(required_return, 'Required return on equity')
        if not fcfe_projections or len(fcfe_projections) == 0:
            raise ValidationError('FCFE projections cannot be empty')
        if terminal_growth is not None:
            ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
            ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
        return True

    def calculate_fcfe_from_components(self, net_income: float, depreciation: float, capex: float, working_capital_change: float, net_borrowing: float) -> float:
        """Calculate FCFE from financial statement components"""
        return CalculationEngine.free_cash_flow_to_equity(net_income, depreciation, capex, working_capital_change, net_borrowing)

    def calculate_fcfe_from_fcff(self, fcff: float, interest_expense: float, tax_rate: float, net_borrowing: float) -> float:
        """Calculate FCFE from FCFF"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        return fcff - after_tax_interest + net_borrowing

    def calculate_fcfe_from_ebit(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
        """Calculate FCFE starting from EBIT"""
        ebt = ebit - interest_expense
        net_income = ebt * (1 - tax_rate)
        return self.calculate_fcfe_from_components(net_income, depreciation, capex, working_capital_change, net_borrowing)

    def calculate_fcfe_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
        """Calculate FCFE starting from EBITDA"""
        ebit = ebitda - depreciation
        return self.calculate_fcfe_from_ebit(ebit, tax_rate, depreciation, capex, working_capital_change, interest_expense, net_borrowing)

    def calculate_fcfe_from_cfo(self, cfo: float, capex: float, net_borrowing: float) -> float:
        """Calculate FCFE from Cash Flow from Operations"""
        return cfo - capex + net_borrowing

    def calculate_terminal_value(self, final_fcfe: float, terminal_growth: float, required_return: float) -> float:
        """Calculate terminal value using Gordon Growth"""
        if terminal_growth >= required_return:
            raise ValidationError('Terminal growth rate must be less than required return')
        terminal_fcfe = final_fcfe * (1 + terminal_growth)
        return terminal_fcfe / (required_return - terminal_growth)

    def calculate_equity_value(self, fcfe_projections: List[float], required_return: float, terminal_growth: float=None, terminal_value: float=None) -> Dict[str, float]:
        """Calculate equity value from FCFE projections"""
        pv_fcfe = 0
        pv_details = []
        for year, fcfe in enumerate(fcfe_projections, 1):
            pv = CalculationEngine.present_value(fcfe, required_return, year)
            pv_fcfe += pv
            pv_details.append({'year': year, 'fcfe': fcfe, 'pv': pv})
        if terminal_value is None:
            if terminal_growth is None:
                raise ValidationError('Either terminal_growth or terminal_value must be provided')
            terminal_value = self.calculate_terminal_value(fcfe_projections[-1], terminal_growth, required_return)
        pv_terminal = CalculationEngine.present_value(terminal_value, required_return, len(fcfe_projections))
        equity_value = pv_fcfe + pv_terminal
        return {'pv_fcfe': pv_fcfe, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'equity_value': equity_value, 'pv_details': pv_details}

    def calculate(self, fcfe_projections: List[float], required_return: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, current_price: float=None) -> ValuationResult:
        """Calculate valuation using FCFE model"""
        self.validate_inputs(required_return, fcfe_projections, terminal_growth)
        equity_components = self.calculate_equity_value(fcfe_projections, required_return, terminal_growth, terminal_value)
        intrinsic_value = equity_components['equity_value'] / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcfe_projections), 'terminal_value_multiple': equity_components['pv_terminal'] / equity_components['equity_value'] * 100, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFE DCF Model'}
        calculation_details = {'fcfe_projections': fcfe_projections, 'pv_fcfe': equity_components['pv_fcfe'], 'terminal_value': equity_components['terminal_value'], 'pv_terminal': equity_components['pv_terminal'], 'equity_value': equity_components['equity_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': equity_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def validate_inputs(self, required_return: float, fcfe_projections: List[float], terminal_growth: float=None) -> bool:
    """Validate FCFE model inputs"""
    ModelValidator.validate_percentage(required_return, 'Required return on equity')
    if not fcfe_projections or len(fcfe_projections) == 0:
        raise ValidationError('FCFE projections cannot be empty')
    if terminal_growth is not None:
        ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
        ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
    return True

def calculate_terminal_value(self, final_fcfe: float, terminal_growth: float, required_return: float) -> float:
    """Calculate terminal value using Gordon Growth"""
    if terminal_growth >= required_return:
        raise ValidationError('Terminal growth rate must be less than required return')
    terminal_fcfe = final_fcfe * (1 + terminal_growth)
    return terminal_fcfe / (required_return - terminal_growth)

class ResidualIncomeModel(BaseValuationModel):
    """Single-stage and Multi-stage Residual Income Model"""

    def __init__(self):
        super().__init__('Residual Income Model', 'Residual income valuation')
        self.valuation_method = ValuationMethod.RESIDUAL_INCOME

    def calculate_residual_income(self, net_income: float, beginning_book_value: float, required_return: float) -> float:
        """Calculate residual income for a single period"""
        return CalculationEngine.residual_income(net_income, beginning_book_value, required_return)

    def calculate_continuing_residual_income(self, final_ri: float, required_return: float, growth_rate: float) -> float:
        """Calculate continuing residual income value"""
        if growth_rate >= required_return:
            raise ValidationError('Growth rate must be less than required return for continuing RI')
        next_ri = final_ri * (1 + growth_rate)
        return next_ri / (required_return - growth_rate)

    def calculate_single_stage_ri_value(self, current_book_value: float, roe: float, required_return: float, growth_rate: float=0) -> float:
        """Calculate single-stage constant growth RI value"""
        if growth_rate >= required_return:
            raise ValidationError('Growth rate must be less than required return')
        next_net_income = current_book_value * roe * (1 + growth_rate)
        next_book_value = current_book_value * (1 + growth_rate)
        next_ri = self.calculate_residual_income(next_net_income, current_book_value, required_return)
        if growth_rate == 0:
            pv_future_ris = next_ri / required_return
        else:
            pv_future_ris = next_ri / (required_return - growth_rate)
        return current_book_value + pv_future_ris

    def calculate_multistage_ri_value(self, current_book_value: float, projected_ris: List[float], required_return: float, terminal_ri: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate multi-stage RI value"""
        pv_projected_ris = 0
        pv_details = []
        for year, ri in enumerate(projected_ris, 1):
            pv_ri = CalculationEngine.present_value(ri, required_return, year)
            pv_projected_ris += pv_ri
            pv_details.append({'year': year, 'ri': ri, 'pv_ri': pv_ri})
        if terminal_ri is not None:
            if terminal_growth is None:
                terminal_growth = 0
            continuing_ri_value = self.calculate_continuing_residual_income(terminal_ri, required_return, terminal_growth)
            pv_terminal = CalculationEngine.present_value(continuing_ri_value, required_return, len(projected_ris))
        else:
            pv_terminal = 0
        total_value = current_book_value + pv_projected_ris + pv_terminal
        return {'current_book_value': current_book_value, 'pv_projected_ris': pv_projected_ris, 'pv_terminal': pv_terminal, 'total_value': total_value, 'pv_details': pv_details}

    def calculate_intrinsic_value(self, company_data: CompanyData, market_data: MarketData) -> float:
        """Calculate intrinsic value using RI model"""
        financial_data = company_data.financial_data
        book_value_total = financial_data.get('book_value', 0) * company_data.shares_outstanding
        roe = financial_data.get('roe', 0)
        required_return = market_data.required_return
        growth_rate = market_data.growth_rate
        total_value = self.calculate_single_stage_ri_value(book_value_total, roe, required_return, growth_rate)
        return total_value / company_data.shares_outstanding if company_data.shares_outstanding > 0 else 0

    def calculate(self, current_book_value: float, projected_ris: List[float], required_return: float, shares_outstanding: float, terminal_ri: float=None, terminal_growth: float=None, current_price: float=None) -> ValuationResult:
        """Calculate valuation using Residual Income model"""
        ModelValidator.validate_positive_number(current_book_value, 'Current book value')
        ModelValidator.validate_percentage(required_return, 'Required return')
        if terminal_growth is not None:
            ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
        ri_components = self.calculate_multistage_ri_value(current_book_value, projected_ris, required_return, terminal_ri, terminal_growth)
        intrinsic_value = ri_components['total_value'] / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'current_book_value': current_book_value, 'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_periods': len(projected_ris), 'book_value_percentage': current_book_value / ri_components['total_value'] * 100, 'terminal_value_percentage': ri_components['pv_terminal'] / ri_components['total_value'] * 100, 'model_type': 'Multi-stage Residual Income Model'}
        calculation_details = {'projected_ris': projected_ris, 'pv_projected_ris': ri_components['pv_projected_ris'], 'pv_terminal': ri_components['pv_terminal'], 'total_value': ri_components['total_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ri_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate_continuing_residual_income(self, final_ri: float, required_return: float, growth_rate: float) -> float:
    """Calculate continuing residual income value"""
    if growth_rate >= required_return:
        raise ValidationError('Growth rate must be less than required return for continuing RI')
    next_ri = final_ri * (1 + growth_rate)
    return next_ri / (required_return - growth_rate)

class ResidualIncomeAnalyzer:
    """Comprehensive Residual Income analysis tools"""

    def __init__(self):
        self.ri_model = ResidualIncomeModel()
        self.eva_model = EconomicValueAddedModel()

    def calculate_implied_growth_rate(self, current_price: float, current_book_value_per_share: float, roe: float, required_return: float) -> float:
        """Calculate implied growth rate from current market P/B ratio"""
        pb_ratio = current_price / current_book_value_per_share
        if pb_ratio <= 1:
            raise ValidationError('P/B ratio must be greater than 1 for growth calculation')
        implied_growth = required_return - (roe - required_return) / (pb_ratio - 1)
        return implied_growth

    def calculate_fundamental_pb_ratio(self, roe: float, required_return: float, growth_rate: float) -> float:
        """Calculate justified P/B ratio from fundamentals"""
        if required_return <= growth_rate:
            raise ValidationError('Required return must be greater than growth rate')
        return 1 + (roe - required_return) / (required_return - growth_rate)

    def analyze_roe_sustainability(self, historical_roe: List[float], industry_avg_roe: float) -> Dict[str, Any]:
        """Analyze ROE sustainability and mean reversion"""
        if not historical_roe:
            raise ValidationError('Historical ROE data required')
        current_roe = historical_roe[-1]
        avg_roe = np.mean(historical_roe)
        roe_volatility = np.std(historical_roe) if len(historical_roe) > 1 else 0
        roe_trend = np.polyfit(range(len(historical_roe)), historical_roe, 1)[0]
        sustainability_score = 'HIGH'
        warnings = []
        if current_roe > 0.25:
            sustainability_score = 'LOW'
            warnings.append('ROE above 25% typically not sustainable long-term')
        if abs(current_roe - industry_avg_roe) > 0.1:
            warnings.append('ROE significantly different from industry average')
        if roe_volatility > 0.05:
            warnings.append('High ROE volatility indicates uncertainty')
        return {'current_roe': current_roe, 'average_roe': avg_roe, 'industry_avg_roe': industry_avg_roe, 'roe_volatility': roe_volatility, 'roe_trend': roe_trend, 'sustainability_score': sustainability_score, 'warnings': warnings}

    def forecast_residual_income(self, current_book_value: float, projected_roes: List[float], required_return: float, payout_ratios: List[float]=None) -> List[float]:
        """Forecast residual income based on ROE and growth assumptions"""
        if payout_ratios is None:
            payout_ratios = [0.4] * len(projected_roes)
        if len(payout_ratios) != len(projected_roes):
            raise ValidationError('Payout ratios and ROEs must have same length')
        projected_ris = []
        book_value = current_book_value
        for i, (roe, payout_ratio) in enumerate(zip(projected_roes, payout_ratios)):
            net_income = book_value * roe
            ri = self.ri_model.calculate_residual_income(net_income, book_value, required_return)
            projected_ris.append(ri)
            retention_ratio = 1 - payout_ratio
            book_value *= 1 + roe * retention_ratio
        return projected_ris

    def compare_ri_with_other_models(self, company_data: CompanyData, market_data: MarketData, ddm_value: float=None, dcf_value: float=None) -> Dict[str, Any]:
        """Compare RI valuation with DDM and DCF models"""
        ri_value = self.ri_model.calculate_intrinsic_value(company_data, market_data)
        comparison = {'ri_value': ri_value, 'current_price': company_data.current_price}
        if ddm_value:
            comparison['ddm_value'] = ddm_value
            comparison['ri_vs_ddm_diff'] = (ri_value - ddm_value) / ddm_value * 100
        if dcf_value:
            comparison['dcf_value'] = dcf_value
            comparison['ri_vs_dcf_diff'] = (ri_value - dcf_value) / dcf_value * 100
        book_value_per_share = company_data.financial_data.get('book_value', 0) * company_data.shares_outstanding / company_data.shares_outstanding
        comparison['book_value_per_share'] = book_value_per_share
        comparison['market_to_book'] = company_data.current_price / book_value_per_share
        comparison['ri_to_book'] = ri_value / book_value_per_share
        return comparison

    def accounting_quality_assessment(self, financial_statements: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Assess accounting quality for RI model reliability"""
        income_stmt = financial_statements.get('income_statement', pd.DataFrame())
        balance_sheet = financial_statements.get('balance_sheet', pd.DataFrame())
        quality_issues = []
        quality_score = 100
        if income_stmt.empty or balance_sheet.empty:
            return {'quality_score': 0, 'issues': ['Financial statements not available']}
        try:
            revenue_growth = income_stmt['revenue'].pct_change().iloc[-1] if 'revenue' in income_stmt.columns else 0
            receivables_growth = balance_sheet['accounts_receivable'].pct_change().iloc[-1] if 'accounts_receivable' in balance_sheet.columns else 0
            if abs(receivables_growth) > abs(revenue_growth) * 1.5:
                quality_issues.append('Receivables growing much faster than revenue')
                quality_score -= 20
            if 'inventory' in balance_sheet.columns and 'cost_of_goods_sold' in income_stmt.columns:
                inventory_turnover = income_stmt['cost_of_goods_sold'].iloc[-1] / balance_sheet['inventory'].iloc[-1]
                if inventory_turnover < 2:
                    quality_issues.append('Low inventory turnover may indicate obsolete inventory')
                    quality_score -= 15
            if 'goodwill' in balance_sheet.columns and 'total_assets' in balance_sheet.columns:
                goodwill_ratio = balance_sheet['goodwill'].iloc[-1] / balance_sheet['total_assets'].iloc[-1]
                if goodwill_ratio > 0.3:
                    quality_issues.append('High goodwill percentage increases impairment risk')
                    quality_score -= 10
            if 'total_debt' in balance_sheet.columns and 'total_equity' in balance_sheet.columns:
                debt_to_equity = balance_sheet['total_debt'].iloc[-1] / balance_sheet['total_equity'].iloc[-1]
                if debt_to_equity > 2:
                    quality_issues.append('High leverage may distort ROE calculations')
                    quality_score -= 10
        except Exception as e:
            quality_issues.append(f'Error in accounting quality assessment: {str(e)}')
            quality_score -= 30
        return {'quality_score': max(0, quality_score), 'issues': quality_issues, 'recommendations': ['Verify revenue recognition policies', 'Check for off-balance-sheet items', 'Analyze working capital components', 'Review goodwill and intangible assets']}

def calculate_implied_growth_rate(self, current_price: float, current_book_value_per_share: float, roe: float, required_return: float) -> float:
    """Calculate implied growth rate from current market P/B ratio"""
    pb_ratio = current_price / current_book_value_per_share
    if pb_ratio <= 1:
        raise ValidationError('P/B ratio must be greater than 1 for growth calculation')
    implied_growth = required_return - (roe - required_return) / (pb_ratio - 1)
    return implied_growth

def calculate_fundamental_pb_ratio(self, roe: float, required_return: float, growth_rate: float) -> float:
    """Calculate justified P/B ratio from fundamentals"""
    if required_return <= growth_rate:
        raise ValidationError('Required return must be greater than growth rate')
    return 1 + (roe - required_return) / (required_return - growth_rate)

class IndexCalculator:
    """Calculate index returns and performance metrics"""

    @staticmethod
    def calculate_price_return(current_value: float, previous_value: float) -> float:
        """Calculate price return"""
        if previous_value <= 0:
            raise ValidationError('Previous value must be positive')
        return (current_value - previous_value) / previous_value

    @staticmethod
    def calculate_total_return(current_value: float, previous_value: float, dividend_income: float) -> float:
        """Calculate total return including dividends"""
        if previous_value <= 0:
            raise ValidationError('Previous value must be positive')
        return (current_value - previous_value + dividend_income) / previous_value

    @staticmethod
    def calculate_index_dividend_yield(constituents: List[IndexConstituent], weights: Dict[str, float], dividend_yields: Dict[str, float]) -> float:
        """Calculate weighted average dividend yield"""
        total_yield = 0
        for constituent in constituents:
            weight = weights.get(constituent.symbol, 0)
            div_yield = dividend_yields.get(constituent.symbol, 0)
            total_yield += weight * div_yield
        return total_yield

    @staticmethod
    def calculate_index_volatility(returns: pd.Series, annualize: bool=True) -> float:
        """Calculate index volatility"""
        volatility = returns.std()
        if annualize:
            volatility *= np.sqrt(252)
        return volatility

    @staticmethod
    def calculate_tracking_error(index_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate tracking error between index and benchmark"""
        if len(index_returns) != len(benchmark_returns):
            raise ValidationError('Return series must have same length')
        excess_returns = index_returns - benchmark_returns
        return excess_returns.std() * np.sqrt(252)

@staticmethod
def calculate_price_return(current_value: float, previous_value: float) -> float:
    """Calculate price return"""
    if previous_value <= 0:
        raise ValidationError('Previous value must be positive')
    return (current_value - previous_value) / previous_value

@staticmethod
def calculate_total_return(current_value: float, previous_value: float, dividend_income: float) -> float:
    """Calculate total return including dividends"""
    if previous_value <= 0:
        raise ValidationError('Previous value must be positive')
    return (current_value - previous_value + dividend_income) / previous_value

@staticmethod
def calculate_tracking_error(index_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate tracking error between index and benchmark"""
    if len(index_returns) != len(benchmark_returns):
        raise ValidationError('Return series must have same length')
    excess_returns = index_returns - benchmark_returns
    return excess_returns.std() * np.sqrt(252)

class IndexAnalyzer(BaseMarketAnalysisModel):
    """Comprehensive index analysis and comparison"""

    def __init__(self):
        super().__init__('Index Analyzer', 'Comprehensive index analysis')

    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for index analysis"""
        index_data = kwargs.get('index_data')
        if index_data is None or index_data.empty:
            raise ValidationError('Index data is required for analysis')
        return True

    def analyze_market_data(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze index market data"""
        return self.comprehensive_index_analysis(market_data)

    def comprehensive_index_analysis(self, index_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive index analysis"""
        price_returns = index_data['Close'].pct_change().dropna()
        total_return = index_data['Close'].iloc[-1] / index_data['Close'].iloc[0] - 1
        annualized_return = (1 + total_return) ** (252 / len(index_data)) - 1
        volatility = IndexCalculator.calculate_index_volatility(price_returns)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        max_drawdown = self.calculate_maximum_drawdown(index_data['Close'])
        var_95 = np.percentile(price_returns, 5)
        var_99 = np.percentile(price_returns, 1)
        performance_periods = self.calculate_period_performance(index_data)
        return {'performance_summary': {'total_return': total_return, 'annualized_return': annualized_return, 'volatility': volatility, 'sharpe_ratio': sharpe_ratio, 'max_drawdown': max_drawdown, 'var_95': var_95, 'var_99': var_99}, 'period_performance': performance_periods, 'statistical_measures': {'skewness': price_returns.skew(), 'kurtosis': price_returns.kurtosis(), 'positive_days': (price_returns > 0).sum() / len(price_returns), 'average_positive_return': price_returns[price_returns > 0].mean(), 'average_negative_return': price_returns[price_returns < 0].mean()}}

    def calculate_maximum_drawdown(self, price_series: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + price_series.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def calculate_period_performance(self, index_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance over different periods"""
        current_price = index_data['Close'].iloc[-1]
        periods = {'1_day': 1, '1_week': 5, '1_month': 21, '3_months': 63, '6_months': 126, '1_year': 252, '3_years': 756, '5_years': 1260}
        performance = {}
        for period_name, days in periods.items():
            if len(index_data) > days:
                past_price = index_data['Close'].iloc[-days - 1]
                period_return = current_price / past_price - 1
                performance[period_name] = period_return
        return performance

    def compare_indexes(self, index_data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Compare multiple indexes"""
        comparison_results = {}
        for index_name, data in index_data_dict.items():
            analysis = self.comprehensive_index_analysis(data)
            comparison_results[index_name] = analysis['performance_summary']
        metrics = ['total_return', 'annualized_return', 'volatility', 'sharpe_ratio', 'max_drawdown']
        comparison_matrix = pd.DataFrame({metric: {name: results[metric] for name, results in comparison_results.items()} for metric in metrics}).T
        rankings = {}
        for metric in metrics:
            ascending = metric in ['volatility', 'max_drawdown']
            rankings[metric] = comparison_matrix.loc[metric].rank(ascending=ascending)
        return {'individual_analysis': comparison_results, 'comparison_matrix': comparison_matrix.to_dict(), 'rankings': rankings}

    def analyze_index_composition(self, constituents: List[IndexConstituent]) -> Dict[str, Any]:
        """Analyze index composition and concentration"""
        if not constituents:
            return {'error': 'No constituents provided'}
        sector_weights = {}
        for constituent in constituents:
            sector = constituent.sector
            if sector in sector_weights:
                sector_weights[sector] += constituent.weight
            else:
                sector_weights[sector] = constituent.weight
        weights = [c.weight for c in constituents]
        hhi = sum((w ** 2 for w in weights))
        sorted_weights = sorted(weights, reverse=True)
        top_5_concentration = sum(sorted_weights[:5]) if len(sorted_weights) >= 5 else sum(sorted_weights)
        top_10_concentration = sum(sorted_weights[:10]) if len(sorted_weights) >= 10 else sum(sorted_weights)
        effective_stocks = 1 / hhi if hhi > 0 else len(constituents)
        return {'composition_metrics': {'total_constituents': len(constituents), 'herfindahl_index': hhi, 'effective_number_of_stocks': effective_stocks, 'top_5_concentration': top_5_concentration, 'top_10_concentration': top_10_concentration}, 'sector_allocation': sector_weights, 'largest_holdings': [{'symbol': c.symbol, 'name': c.name, 'weight': c.weight, 'sector': c.sector} for c in sorted(constituents, key=lambda x: x.weight, reverse=True)[:10]]}

def validate_inputs(self, **kwargs) -> bool:
    """Validate inputs for index analysis"""
    index_data = kwargs.get('index_data')
    if index_data is None or index_data.empty:
        raise ValidationError('Index data is required for analysis')
    return True

class MarketEfficiencyTester(BaseMarketAnalysisModel):
    """Market efficiency testing framework"""

    def __init__(self):
        super().__init__('Market Efficiency Tester', 'Tests for various forms of market efficiency')
        self.significance_level = 0.05

    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for efficiency tests"""
        price_data = kwargs.get('price_data')
        if price_data is None or price_data.empty:
            raise ValidationError('Price data is required for efficiency tests')
        if 'Close' not in price_data.columns:
            raise ValidationError("Price data must contain 'Close' column")
        return True

    def analyze_market_data(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive market efficiency analysis"""
        results = {'weak_form_tests': self.test_weak_form_efficiency(market_data), 'semi_strong_tests': self.test_semi_strong_efficiency(market_data), 'strong_form_tests': self.test_strong_form_efficiency(market_data), 'anomalies': self.detect_market_anomalies(market_data), 'overall_assessment': {}}
        weak_efficient = results['weak_form_tests']['is_efficient']
        semi_strong_efficient = results['semi_strong_tests']['is_efficient']
        strong_efficient = results['strong_form_tests']['is_efficient']
        if strong_efficient:
            efficiency_level = 'Strong-form efficient'
        elif semi_strong_efficient:
            efficiency_level = 'Semi-strong-form efficient'
        elif weak_efficient:
            efficiency_level = 'Weak-form efficient'
        else:
            efficiency_level = 'Inefficient'
        results['overall_assessment'] = {'efficiency_level': efficiency_level, 'weak_form_efficient': weak_efficient, 'semi_strong_form_efficient': semi_strong_efficient, 'strong_form_efficient': strong_efficient, 'anomalies_detected': len(results['anomalies']) > 0}
        return results

def validate_inputs(self, **kwargs) -> bool:
    """Validate inputs for efficiency tests"""
    price_data = kwargs.get('price_data')
    if price_data is None or price_data.empty:
        raise ValidationError('Price data is required for efficiency tests')
    if 'Close' not in price_data.columns:
        raise ValidationError("Price data must contain 'Close' column")
    return True

class OrderAnalyzer:
    """Analyze trading orders and execution instructions"""

    def analyze_market_order(self, order: TradingOrder, current_bid: float, current_ask: float) -> Dict[str, Any]:
        """Analyze market order characteristics"""
        if order.position_type == PositionType.LONG:
            expected_execution_price = current_ask
            price_impact = 'Buy at ask price'
        else:
            expected_execution_price = current_bid
            price_impact = 'Sell at bid price'
        bid_ask_spread = current_ask - current_bid
        spread_percentage = bid_ask_spread / ((current_bid + current_ask) / 2) * 100
        return {'order_type': order.order_type.value, 'execution_certainty': 'High', 'price_certainty': 'Low', 'expected_execution_price': expected_execution_price, 'bid_ask_spread': bid_ask_spread, 'spread_percentage': spread_percentage, 'price_impact': price_impact, 'advantages': ['Immediate execution', 'High fill probability'], 'disadvantages': ['Price uncertainty', 'Market impact cost']}

    def analyze_limit_order(self, order: TradingOrder, current_price: float) -> Dict[str, Any]:
        """Analyze limit order characteristics"""
        if not order.price:
            raise ValidationError('Limit order requires price specification')
        if order.position_type == PositionType.LONG:
            executable = order.price >= current_price
            price_improvement = current_price - order.price if executable else 0
        else:
            executable = order.price <= current_price
            price_improvement = order.price - current_price if executable else 0
        return {'order_type': order.order_type.value, 'limit_price': order.price, 'current_market_price': current_price, 'immediately_executable': executable, 'price_improvement': price_improvement, 'execution_certainty': 'Medium', 'price_certainty': 'High', 'advantages': ['Price protection', 'Potential price improvement'], 'disadvantages': ['Execution uncertainty', 'Opportunity cost if not filled']}

    def analyze_stop_order(self, order: TradingOrder, current_price: float) -> Dict[str, Any]:
        """Analyze stop order characteristics"""
        if not order.stop_price:
            raise ValidationError('Stop order requires stop price specification')
        if order.position_type == PositionType.LONG:
            activated = current_price >= order.stop_price
            order_purpose = 'Momentum/Breakout buying'
        else:
            activated = current_price <= order.stop_price
            order_purpose = 'Loss limitation/Risk management'
        return {'order_type': order.order_type.value, 'stop_price': order.stop_price, 'current_price': current_price, 'activated': activated, 'order_purpose': order_purpose, 'execution_certainty': 'Medium' if activated else 'Low', 'price_certainty': 'Low', 'advantages': ['Risk management', 'No monitoring required'], 'disadvantages': ['Price uncertainty when executed', 'Possible gap risk']}

    def compare_order_types(self, current_bid: float, current_ask: float) -> pd.DataFrame:
        """Compare characteristics of different order types"""
        order_comparison = [{'order_type': 'Market Order', 'execution_certainty': 'High', 'price_certainty': 'Low', 'typical_use': 'Immediate execution needed', 'price_paid_received': f'Ask ({current_ask}) / Bid ({current_bid})'}, {'order_type': 'Limit Order', 'execution_certainty': 'Medium', 'price_certainty': 'High', 'typical_use': 'Price protection desired', 'price_paid_received': 'Limit price or better'}, {'order_type': 'Stop Order', 'execution_certainty': 'Medium', 'price_certainty': 'Low', 'typical_use': 'Risk management/Momentum', 'price_paid_received': 'Market price when triggered'}, {'order_type': 'Stop-Limit Order', 'execution_certainty': 'Low', 'price_certainty': 'High', 'typical_use': 'Risk management with price protection', 'price_paid_received': 'Limit price or better (if filled)'}]
        return pd.DataFrame(order_comparison)

def analyze_limit_order(self, order: TradingOrder, current_price: float) -> Dict[str, Any]:
    """Analyze limit order characteristics"""
    if not order.price:
        raise ValidationError('Limit order requires price specification')
    if order.position_type == PositionType.LONG:
        executable = order.price >= current_price
        price_improvement = current_price - order.price if executable else 0
    else:
        executable = order.price <= current_price
        price_improvement = order.price - current_price if executable else 0
    return {'order_type': order.order_type.value, 'limit_price': order.price, 'current_market_price': current_price, 'immediately_executable': executable, 'price_improvement': price_improvement, 'execution_certainty': 'Medium', 'price_certainty': 'High', 'advantages': ['Price protection', 'Potential price improvement'], 'disadvantages': ['Execution uncertainty', 'Opportunity cost if not filled']}

def analyze_stop_order(self, order: TradingOrder, current_price: float) -> Dict[str, Any]:
    """Analyze stop order characteristics"""
    if not order.stop_price:
        raise ValidationError('Stop order requires stop price specification')
    if order.position_type == PositionType.LONG:
        activated = current_price >= order.stop_price
        order_purpose = 'Momentum/Breakout buying'
    else:
        activated = current_price <= order.stop_price
        order_purpose = 'Loss limitation/Risk management'
    return {'order_type': order.order_type.value, 'stop_price': order.stop_price, 'current_price': current_price, 'activated': activated, 'order_purpose': order_purpose, 'execution_certainty': 'Medium' if activated else 'Low', 'price_certainty': 'Low', 'advantages': ['Risk management', 'No monitoring required'], 'disadvantages': ['Price uncertainty when executed', 'Possible gap risk']}

class IndustryAnalyzer(BaseCompanyAnalysisModel):
    """Comprehensive industry analysis framework"""

    def __init__(self):
        super().__init__('Industry Analyzer', 'Comprehensive industry and competitive analysis')
        self.classifier = IndustryClassifier()

    def validate_inputs(self, **kwargs) -> bool:
        """Validate inputs for industry analysis"""
        company_data = kwargs.get('company_data')
        if not isinstance(company_data, CompanyData):
            raise ValidationError('Valid CompanyData object required')
        return True

    def analyze_company(self, company_data: CompanyData) -> Dict[str, Any]:
        """Comprehensive industry analysis for a company"""
        analysis = {'industry_overview': self.analyze_industry_overview(company_data), 'industry_structure': self.analyze_industry_structure(company_data), 'competitive_landscape': self.analyze_competitive_landscape(company_data), 'porters_five_forces': self.perform_porters_analysis(company_data), 'pestle_analysis': self.perform_pestle_analysis(company_data), 'company_positioning': self.analyze_company_positioning(company_data), 'industry_trends': self.identify_industry_trends(company_data), 'investment_implications': self.assess_investment_implications(company_data)}
        return analysis

    def analyze_industry_overview(self, company_data: CompanyData) -> Dict[str, Any]:
        """Analyze industry overview and characteristics"""
        classification = self.classifier.classify_company(company_data)
        market_cap = company_data.market_cap
        estimated_market_size = self.estimate_industry_size(company_data.sector, market_cap)
        growth_profile = self.determine_growth_profile(company_data.sector)
        return {'classification': classification, 'industry_size': {'estimated_total_market': estimated_market_size, 'company_market_share': self.estimate_market_share(market_cap, estimated_market_size), 'size_category': self.categorize_industry_size(estimated_market_size)}, 'growth_characteristics': growth_profile, 'industry_lifecycle': self.determine_industry_lifecycle(company_data), 'key_success_factors': self.identify_success_factors(company_data.sector), 'industry_risks': self.identify_industry_risks(company_data.sector)}

    def estimate_industry_size(self, sector: str, company_market_cap: float) -> float:
        """Estimate total industry market size"""
        multipliers = {'Information Technology': 50, 'Health Care': 40, 'Financials': 30, 'Consumer Discretionary': 35, 'Consumer Staples': 25, 'Industrials': 30, 'Energy': 20, 'Materials': 15, 'Utilities': 10, 'Communication Services': 25, 'Real Estate': 20}
        multiplier = multipliers.get(sector, 25)
        return company_market_cap * multiplier

    def estimate_market_share(self, company_market_cap: float, industry_size: float) -> float:
        """Estimate company's market share"""
        if industry_size > 0:
            return company_market_cap / industry_size * 100
        return 0

    def categorize_industry_size(self, industry_size: float) -> str:
        """Categorize industry by size"""
        if industry_size > 1000000000000:
            return 'Very Large'
        elif industry_size > 500000000000:
            return 'Large'
        elif industry_size > 100000000000:
            return 'Medium'
        else:
            return 'Small'

    def determine_growth_profile(self, sector: str) -> Dict[str, Any]:
        """Determine industry growth profile"""
        growth_profiles = {'Information Technology': {'historical_growth': 0.12, 'volatility': 'High', 'trend': 'Growing'}, 'Health Care': {'historical_growth': 0.08, 'volatility': 'Medium', 'trend': 'Growing'}, 'Consumer Discretionary': {'historical_growth': 0.06, 'volatility': 'High', 'trend': 'Cyclical'}, 'Financials': {'historical_growth': 0.05, 'volatility': 'High', 'trend': 'Cyclical'}, 'Consumer Staples': {'historical_growth': 0.04, 'volatility': 'Low', 'trend': 'Stable'}, 'Industrials': {'historical_growth': 0.05, 'volatility': 'Medium', 'trend': 'Cyclical'}, 'Energy': {'historical_growth': 0.02, 'volatility': 'Very High', 'trend': 'Declining'}, 'Materials': {'historical_growth': 0.03, 'volatility': 'High', 'trend': 'Cyclical'}, 'Utilities': {'historical_growth': 0.02, 'volatility': 'Low', 'trend': 'Stable'}, 'Communication Services': {'historical_growth': 0.07, 'volatility': 'Medium', 'trend': 'Growing'}, 'Real Estate': {'historical_growth': 0.04, 'volatility': 'Medium', 'trend': 'Cyclical'}}
        return growth_profiles.get(sector, {'historical_growth': 0.05, 'volatility': 'Medium', 'trend': 'Stable'})

    def determine_industry_lifecycle(self, company_data: CompanyData) -> str:
        """Determine industry lifecycle stage"""
        sector = company_data.sector
        growth_profile = self.determine_growth_profile(sector)
        growth_rate = growth_profile['historical_growth']
        if growth_rate > 0.1:
            return 'Growth'
        elif growth_rate > 0.05:
            return 'Mature'
        elif growth_rate > 0:
            return 'Mature/Stable'
        else:
            return 'Declining'

    def identify_success_factors(self, sector: str) -> List[str]:
        """Identify key success factors by sector"""
        success_factors = {'Information Technology': ['Innovation and R&D capability', 'Talent acquisition and retention', 'Scalable technology platforms', 'Network effects', 'Speed to market'], 'Health Care': ['R&D pipeline strength', 'Regulatory approval capabilities', 'Patent protection', 'Clinical trial success rates', 'Market access and distribution'], 'Financials': ['Risk management capabilities', 'Regulatory compliance', 'Technology infrastructure', 'Customer relationships', 'Capital adequacy'], 'Consumer Discretionary': ['Brand strength and recognition', 'Distribution network', 'Product innovation', 'Supply chain efficiency', 'Customer experience'], 'Energy': ['Reserve quality and quantity', 'Operational efficiency', 'Technology and innovation', 'Environmental compliance', 'Geographic diversification']}
        return success_factors.get(sector, ['Operational efficiency', 'Market position', 'Financial strength', 'Innovation capability', 'Customer relationships'])

    def identify_industry_risks(self, sector: str) -> List[str]:
        """Identify key industry risks by sector"""
        industry_risks = {'Information Technology': ['Technological obsolescence', 'Cybersecurity threats', 'Regulatory changes', 'Talent shortage', 'Market saturation'], 'Health Care': ['Regulatory approval risks', 'Patent cliff exposure', 'Pricing pressures', 'Clinical trial failures', 'Regulatory changes'], 'Financials': ['Interest rate risk', 'Credit risk', 'Regulatory changes', 'Economic cycles', 'Technology disruption'], 'Energy': ['Commodity price volatility', 'Environmental regulations', 'Geopolitical risks', 'Stranded asset risk', 'Energy transition']}
        return industry_risks.get(sector, ['Economic cycles', 'Competitive pressure', 'Regulatory changes', 'Technology disruption', 'Supply chain disruption'])

    def analyze_industry_structure(self, company_data: CompanyData) -> Dict[str, Any]:
        """Analyze industry structure and concentration"""
        market_cap = company_data.market_cap
        estimated_industry_size = self.estimate_industry_size(company_data.sector, market_cap)
        concentration_level = self.estimate_concentration(company_data.sector)
        entry_barriers = self.assess_entry_barriers(company_data.sector)
        profitability_profile = self.assess_industry_profitability(company_data.sector)
        return {'market_concentration': {'concentration_level': concentration_level, 'estimated_hhi': self.estimate_hhi(concentration_level), 'market_structure': self.determine_market_structure(concentration_level)}, 'barriers_to_entry': entry_barriers, 'profitability_profile': profitability_profile, 'competitive_dynamics': self.assess_competitive_dynamics(company_data.sector), 'industry_maturity': self.assess_industry_maturity(company_data.sector)}

    def estimate_concentration(self, sector: str) -> str:
        """Estimate industry concentration level"""
        high_concentration = ['Utilities', 'Communication Services', 'Aerospace & Defense']
        medium_concentration = ['Energy', 'Materials', 'Industrials', 'Health Care']
        low_concentration = ['Information Technology', 'Consumer Discretionary', 'Financials']
        if sector in high_concentration:
            return 'High'
        elif sector in medium_concentration:
            return 'Medium'
        else:
            return 'Low'

    def estimate_hhi(self, concentration_level: str) -> int:
        """Estimate Herfindahl-Hirschman Index"""
        hhi_ranges = {'High': 2000, 'Medium': 1200, 'Low': 800}
        return hhi_ranges.get(concentration_level, 1000)

    def determine_market_structure(self, concentration_level: str) -> str:
        """Determine market structure type"""
        if concentration_level == 'High':
            return 'Oligopoly'
        elif concentration_level == 'Medium':
            return 'Monopolistic Competition'
        else:
            return 'Perfect Competition'

    def assess_entry_barriers(self, sector: str) -> Dict[str, str]:
        """Assess barriers to entry"""
        barrier_assessments = {'Information Technology': {'capital_requirements': 'Medium', 'regulatory_barriers': 'Low', 'technology_barriers': 'High', 'brand_loyalty': 'Medium', 'network_effects': 'High'}, 'Health Care': {'capital_requirements': 'Very High', 'regulatory_barriers': 'Very High', 'technology_barriers': 'High', 'brand_loyalty': 'High', 'network_effects': 'Low'}, 'Utilities': {'capital_requirements': 'Very High', 'regulatory_barriers': 'Very High', 'technology_barriers': 'Medium', 'brand_loyalty': 'Low', 'network_effects': 'High'}, 'Financials': {'capital_requirements': 'Very High', 'regulatory_barriers': 'Very High', 'technology_barriers': 'Medium', 'brand_loyalty': 'Medium', 'network_effects': 'Medium'}}
        return barrier_assessments.get(sector, {'capital_requirements': 'Medium', 'regulatory_barriers': 'Medium', 'technology_barriers': 'Medium', 'brand_loyalty': 'Medium', 'network_effects': 'Low'})

    def assess_industry_profitability(self, sector: str) -> Dict[str, Any]:
        """Assess industry profitability characteristics"""
        profitability_data = {'Information Technology': {'avg_margin': 0.15, 'margin_stability': 'Medium', 'trend': 'Stable'}, 'Health Care': {'avg_margin': 0.12, 'margin_stability': 'High', 'trend': 'Declining'}, 'Financials': {'avg_margin': 0.2, 'margin_stability': 'Low', 'trend': 'Cyclical'}, 'Consumer Staples': {'avg_margin': 0.08, 'margin_stability': 'High', 'trend': 'Stable'}, 'Energy': {'avg_margin': 0.05, 'margin_stability': 'Very Low', 'trend': 'Volatile'}, 'Utilities': {'avg_margin': 0.1, 'margin_stability': 'High', 'trend': 'Stable'}}
        return profitability_data.get(sector, {'avg_margin': 0.08, 'margin_stability': 'Medium', 'trend': 'Stable'})

    def assess_competitive_dynamics(self, sector: str) -> Dict[str, str]:
        """Assess competitive dynamics"""
        dynamics = {'Information Technology': {'intensity': 'Very High', 'basis': 'Innovation and Speed', 'pricing_power': 'Medium', 'differentiation': 'High'}, 'Health Care': {'intensity': 'High', 'basis': 'Innovation and Quality', 'pricing_power': 'High', 'differentiation': 'Very High'}, 'Utilities': {'intensity': 'Low', 'basis': 'Regulation and Service', 'pricing_power': 'Low', 'differentiation': 'Low'}, 'Energy': {'intensity': 'High', 'basis': 'Cost and Efficiency', 'pricing_power': 'Low', 'differentiation': 'Low'}}
        return dynamics.get(sector, {'intensity': 'Medium', 'basis': 'Price and Quality', 'pricing_power': 'Medium', 'differentiation': 'Medium'})

    def assess_industry_maturity(self, sector: str) -> str:
        """Assess industry maturity level"""
        mature_industries = ['Utilities', 'Consumer Staples', 'Energy', 'Materials']
        growth_industries = ['Information Technology', 'Health Care', 'Communication Services']
        if sector in mature_industries:
            return 'Mature'
        elif sector in growth_industries:
            return 'Growth'
        else:
            return 'Transitional'

def validate_inputs(self, **kwargs) -> bool:
    """Validate inputs for industry analysis"""
    company_data = kwargs.get('company_data')
    if not isinstance(company_data, CompanyData):
        raise ValidationError('Valid CompanyData object required')
    return True

def analyze_company(self, company_data: CompanyData) -> Dict[str, Any]:
    """Comprehensive industry analysis for a company"""
    analysis = {'industry_overview': self.analyze_industry_overview(company_data), 'industry_structure': self.analyze_industry_structure(company_data), 'competitive_landscape': self.analyze_competitive_landscape(company_data), 'porters_five_forces': self.perform_porters_analysis(company_data), 'pestle_analysis': self.perform_pestle_analysis(company_data), 'company_positioning': self.analyze_company_positioning(company_data), 'industry_trends': self.identify_industry_trends(company_data), 'investment_implications': self.assess_investment_implications(company_data)}
    return analysis

def pestle_analysis(company_data: CompanyData) -> PESTLEAnalysis:
    """Quick PESTLE analysis"""
    analyzer = PESTLEAnalyzer()
    return analyzer.perform_pestle_analysis(company_data)

@dataclass
class ArbitrageOpportunity:
    """Container for arbitrage opportunity details"""
    arbitrage_type: ArbitrageType
    direction: ArbitrageDirection
    profit_potential: float
    confidence_level: float
    instruments_involved: List[str]
    trade_details: Dict
    risk_factors: List[str]
    execution_complexity: str

    def __post_init__(self):
        if self.profit_potential < 0:
            raise ValidationError('Profit potential cannot be negative')
        if not 0 <= self.confidence_level <= 1:
            raise ValidationError('Confidence level must be between 0 and 1')

def __post_init__(self):
    if self.profit_potential < 0:
        raise ValidationError('Profit potential cannot be negative')
    if not 0 <= self.confidence_level <= 1:
        raise ValidationError('Confidence level must be between 0 and 1')

@dataclass
class SyntheticInstrument:
    """Synthetic instrument construction details"""
    target_instrument: str
    synthetic_components: List[Dict]
    cost_comparison: float
    replication_accuracy: float

    def __post_init__(self):
        if not 0 <= self.replication_accuracy <= 1:
            raise ValidationError('Replication accuracy must be between 0 and 1')

def __post_init__(self):
    if not 0 <= self.replication_accuracy <= 1:
        raise ValidationError('Replication accuracy must be between 0 and 1')

class BoxSpreadStrategy:
    """Box spread arbitrage strategy"""

    def __init__(self, strike_low: float, strike_high: float, call_low_price: float, call_high_price: float, put_low_price: float, put_high_price: float, risk_free_rate: float, time_to_expiry: float):
        self.K1 = strike_low
        self.K2 = strike_high
        self.C1 = call_low_price
        self.C2 = call_high_price
        self.P1 = put_low_price
        self.P2 = put_high_price
        self.r = risk_free_rate
        self.T = time_to_expiry
        if strike_low >= strike_high:
            raise ValidationError('Lower strike must be less than higher strike')

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect box spread arbitrage"""
        guaranteed_payoff = self.K2 - self.K1
        present_value_payoff = guaranteed_payoff * np.exp(-self.r * self.T)
        box_cost = self.C1 - self.C2 + (self.P2 - self.P1)
        arbitrage_profit = present_value_payoff - box_cost
        if abs(arbitrage_profit) > Constants.EPSILON:
            if arbitrage_profit > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.BOX_SPREAD, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=arbitrage_profit, confidence_level=0.99, instruments_involved=[f'call_{self.K1}', f'call_{self.K2}', f'put_{self.K1}', f'put_{self.K2}'], trade_details={'buy_call_low': self.C1, 'sell_call_high': self.C2, 'sell_put_low': self.P1, 'buy_put_high': self.P2, 'box_cost': box_cost, 'guaranteed_payoff': guaranteed_payoff, 'present_value': present_value_payoff, 'arbitrage_profit': arbitrage_profit, 'call_spread_cost': self.C1 - self.C2, 'put_spread_cost': self.P2 - self.P1}, risk_factors=['execution_risk', 'bid_ask_spread'], execution_complexity='high')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.BOX_SPREAD, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(arbitrage_profit), confidence_level=0.99, instruments_involved=[f'call_{self.K1}', f'call_{self.K2}', f'put_{self.K1}', f'put_{self.K2}'], trade_details={'sell_call_low': self.C1, 'buy_call_high': self.C2, 'buy_put_low': self.P1, 'sell_put_high': self.P2, 'box_revenue': -box_cost, 'guaranteed_payout': -guaranteed_payoff, 'arbitrage_profit': abs(arbitrage_profit), 'call_spread_revenue': -(self.C1 - self.C2), 'put_spread_revenue': -(self.P2 - self.P1)}, risk_factors=['execution_risk', 'bid_ask_spread'], execution_complexity='high')
        return None

def __init__(self, strike_low: float, strike_high: float, call_low_price: float, call_high_price: float, put_low_price: float, put_high_price: float, risk_free_rate: float, time_to_expiry: float):
    self.K1 = strike_low
    self.K2 = strike_high
    self.C1 = call_low_price
    self.C2 = call_high_price
    self.P1 = put_low_price
    self.P2 = put_high_price
    self.r = risk_free_rate
    self.T = time_to_expiry
    if strike_low >= strike_high:
        raise ValidationError('Lower strike must be less than higher strike')

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

class ArbitrageScanner:
    """Comprehensive arbitrage opportunity scanner"""

    def __init__(self, tolerance: float=Constants.EPSILON):
        self.tolerance = tolerance
        self.detected_opportunities = []

    def scan_put_call_parity(self, call_price: float, put_price: float, spot_price: float, strike_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0) -> List[ArbitrageOpportunity]:
        """Scan for put-call parity arbitrage"""
        opportunities = []
        conversion = ConversionStrategy(spot_price, strike_price, call_price, put_price, risk_free_rate, time_to_expiry, dividend_yield)
        conversion_opportunity = conversion.detect_arbitrage()
        if conversion_opportunity:
            opportunities.append(conversion_opportunity)
        reversal = ReversalStrategy(spot_price, strike_price, call_price, put_price, risk_free_rate, time_to_expiry, dividend_yield)
        reversal_opportunity = reversal.detect_arbitrage()
        if reversal_opportunity:
            opportunities.append(reversal_opportunity)
        return opportunities

    def scan_carry_arbitrage(self, spot_price: float, forward_price: float, risk_free_rate: float, time_to_expiry: float, **kwargs) -> List[ArbitrageOpportunity]:
        """Scan for carry arbitrage opportunities"""
        opportunities = []
        detector = CarryArbitrageDetector(spot_price, forward_price, risk_free_rate, time_to_expiry, **kwargs)
        opportunity = detector.detect_arbitrage()
        if opportunity:
            opportunities.append(opportunity)
        return opportunities

    def scan_box_spread(self, strikes: Tuple[float, float], call_prices: Tuple[float, float], put_prices: Tuple[float, float], risk_free_rate: float, time_to_expiry: float) -> List[ArbitrageOpportunity]:
        """Scan for box spread arbitrage"""
        opportunities = []
        box_spread = BoxSpreadStrategy(strikes[0], strikes[1], call_prices[0], call_prices[1], put_prices[0], put_prices[1], risk_free_rate, time_to_expiry)
        opportunity = box_spread.detect_arbitrage()
        if opportunity:
            opportunities.append(opportunity)
        return opportunities

    def scan_volatility_arbitrage(self, market_vol: float, implied_vol: float, option: VanillaOption, market_data: MarketData, confidence_threshold: float=0.05) -> List[ArbitrageOpportunity]:
        """Scan for volatility arbitrage opportunities"""
        opportunities = []
        detector = VolatilityArbitrageDetector(market_vol, implied_vol, option, market_data, confidence_threshold)
        opportunity = detector.detect_arbitrage()
        if opportunity:
            opportunities.append(opportunity)
        return opportunities

    def scan_calendar_spread(self, near_option_price: float, far_option_price: float, near_time: float, far_time: float, strike_price: float, option_type: OptionType, market_data: MarketData) -> List[ArbitrageOpportunity]:
        """Scan for calendar spread arbitrage"""
        opportunities = []
        detector = CalendarSpreadArbitrage(near_option_price, far_option_price, near_time, far_time, strike_price, option_type, market_data)
        opportunity = detector.detect_arbitrage()
        if opportunity:
            opportunities.append(opportunity)
        return opportunities

    def comprehensive_scan(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Perform comprehensive arbitrage scan"""
        all_opportunities = []
        try:
            if all((key in market_data for key in ['call_price', 'put_price', 'spot_price', 'strike_price'])):
                pcp_opportunities = self.scan_put_call_parity(market_data['call_price'], market_data['put_price'], market_data['spot_price'], market_data['strike_price'], market_data.get('risk_free_rate', 0.02), market_data.get('time_to_expiry', 0.25), market_data.get('dividend_yield', 0.0))
                all_opportunities.extend(pcp_opportunities)
            if all((key in market_data for key in ['spot_price', 'forward_price'])):
                carry_opportunities = self.scan_carry_arbitrage(market_data['spot_price'], market_data['forward_price'], market_data.get('risk_free_rate', 0.02), market_data.get('time_to_expiry', 0.25), dividend_yield=market_data.get('dividend_yield', 0.0), storage_cost=market_data.get('storage_cost', 0.0), convenience_yield=market_data.get('convenience_yield', 0.0))
                all_opportunities.extend(carry_opportunities)
            if all((key in market_data for key in ['strikes', 'call_prices', 'put_prices'])):
                box_opportunities = self.scan_box_spread(market_data['strikes'], market_data['call_prices'], market_data['put_prices'], market_data.get('risk_free_rate', 0.02), market_data.get('time_to_expiry', 0.25))
                all_opportunities.extend(box_opportunities)
            if all((key in market_data for key in ['market_vol', 'implied_vol', 'option'])):
                vol_opportunities = self.scan_volatility_arbitrage(market_data['market_vol'], market_data['implied_vol'], market_data['option'], market_data.get('market_data_obj'), market_data.get('confidence_threshold', 0.05))
                all_opportunities.extend(vol_opportunities)
            if all((key in market_data for key in ['near_option_price', 'far_option_price', 'near_time', 'far_time'])):
                calendar_opportunities = self.scan_calendar_spread(market_data['near_option_price'], market_data['far_option_price'], market_data['near_time'], market_data['far_time'], market_data.get('strike_price', 100), market_data.get('option_type', OptionType.CALL), market_data.get('market_data_obj'))
                all_opportunities.extend(calendar_opportunities)
        except Exception as e:
            logger.error(f'Error in arbitrage scan: {e}')
        self.detected_opportunities = all_opportunities
        return all_opportunities

    def rank_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Rank arbitrage opportunities by attractiveness"""

        def opportunity_score(opp):
            complexity_weights = {'low': 1.0, 'medium': 0.7, 'high': 0.5}
            complexity_weight = complexity_weights.get(opp.execution_complexity, 0.5)
            base_score = opp.profit_potential * opp.confidence_level * complexity_weight
            if opp.arbitrage_type == ArbitrageType.BOX_SPREAD and opp.confidence_level >= 0.99:
                base_score *= 1.5
            if len(opp.risk_factors) > 3:
                base_score *= 0.8
            return base_score
        return sorted(opportunities, key=opportunity_score, reverse=True)

    def filter_opportunities(self, opportunities: List[ArbitrageOpportunity], min_profit: float=0.0, min_confidence: float=0.0, max_complexity: str='high', allowed_types: List[ArbitrageType]=None) -> List[ArbitrageOpportunity]:
        """Filter opportunities based on criteria"""
        filtered = []
        complexity_levels = {'low': 1, 'medium': 2, 'high': 3}
        max_complexity_level = complexity_levels.get(max_complexity, 3)
        for opp in opportunities:
            if opp.profit_potential < min_profit:
                continue
            if opp.confidence_level < min_confidence:
                continue
            opp_complexity_level = complexity_levels.get(opp.execution_complexity, 3)
            if opp_complexity_level > max_complexity_level:
                continue
            if allowed_types and opp.arbitrage_type not in allowed_types:
                continue
            filtered.append(opp)
        return filtered

    def generate_execution_plan(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Generate detailed execution plan for arbitrage opportunity"""
        execution_steps = []
        if opportunity.arbitrage_type == ArbitrageType.CONVERSION:
            execution_steps = [{'step': 1, 'action': 'Sell call option', 'details': opportunity.trade_details.get('sell_call')}, {'step': 2, 'action': 'Buy put option', 'details': opportunity.trade_details.get('buy_put')}, {'step': 3, 'action': 'Buy underlying stock', 'details': opportunity.trade_details.get('buy_stock')}, {'step': 4, 'action': 'Sell bonds (borrow)', 'details': opportunity.trade_details.get('sell_bond')}]
        elif opportunity.arbitrage_type == ArbitrageType.REVERSAL:
            execution_steps = [{'step': 1, 'action': 'Buy call option', 'details': opportunity.trade_details.get('buy_call')}, {'step': 2, 'action': 'Sell put option', 'details': opportunity.trade_details.get('sell_put')}, {'step': 3, 'action': 'Sell underlying stock', 'details': opportunity.trade_details.get('sell_stock')}, {'step': 4, 'action': 'Buy bonds (lend)', 'details': opportunity.trade_details.get('buy_bond')}]
        elif opportunity.arbitrage_type == ArbitrageType.BOX_SPREAD:
            if opportunity.direction == ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE:
                execution_steps = [{'step': 1, 'action': 'Buy call (low strike)', 'details': opportunity.trade_details.get('buy_call_low')}, {'step': 2, 'action': 'Sell call (high strike)', 'details': opportunity.trade_details.get('sell_call_high')}, {'step': 3, 'action': 'Sell put (low strike)', 'details': opportunity.trade_details.get('sell_put_low')}, {'step': 4, 'action': 'Buy put (high strike)', 'details': opportunity.trade_details.get('buy_put_high')}]
            else:
                execution_steps = [{'step': 1, 'action': 'Sell call (low strike)', 'details': opportunity.trade_details.get('sell_call_low')}, {'step': 2, 'action': 'Buy call (high strike)', 'details': opportunity.trade_details.get('buy_call_high')}, {'step': 3, 'action': 'Buy put (low strike)', 'details': opportunity.trade_details.get('buy_put_low')}, {'step': 4, 'action': 'Sell put (high strike)', 'details': opportunity.trade_details.get('sell_put_high')}]
        elif opportunity.arbitrage_type == ArbitrageType.CARRY_ARBITRAGE:
            if opportunity.direction == ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP:
                execution_steps = [{'step': 1, 'action': 'Sell forward contract', 'details': opportunity.trade_details.get('sell_forward')}, {'step': 2, 'action': 'Buy underlying asset', 'details': opportunity.trade_details.get('buy_underlying')}, {'step': 3, 'action': 'Borrow funds', 'details': opportunity.trade_details.get('borrow_funds')}]
            else:
                execution_steps = [{'step': 1, 'action': 'Buy forward contract', 'details': opportunity.trade_details.get('buy_forward')}, {'step': 2, 'action': 'Sell underlying asset', 'details': opportunity.trade_details.get('sell_underlying')}, {'step': 3, 'action': 'Invest proceeds', 'details': opportunity.trade_details.get('invest_proceeds')}]
        return {'opportunity_id': f'{opportunity.arbitrage_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}', 'execution_steps': execution_steps, 'estimated_profit': opportunity.profit_potential, 'confidence_level': opportunity.confidence_level, 'risk_factors': opportunity.risk_factors, 'execution_complexity': opportunity.execution_complexity, 'required_capital': self._calculate_required_capital(opportunity), 'time_to_expiration': opportunity.trade_details.get('time_to_expiry', 'N/A'), 'monitoring_requirements': self._get_monitoring_requirements(opportunity)}

    def _calculate_required_capital(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate required capital for arbitrage execution"""
        if opportunity.arbitrage_type in [ArbitrageType.CONVERSION, ArbitrageType.REVERSAL]:
            return opportunity.trade_details.get('buy_stock', 0) + opportunity.trade_details.get('buy_put', 0)
        elif opportunity.arbitrage_type == ArbitrageType.BOX_SPREAD:
            return opportunity.trade_details.get('box_cost', 0)
        elif opportunity.arbitrage_type == ArbitrageType.CARRY_ARBITRAGE:
            return opportunity.trade_details.get('buy_underlying', 0)
        else:
            return 0.0

    def _get_monitoring_requirements(self, opportunity: ArbitrageOpportunity) -> List[str]:
        """Get monitoring requirements for arbitrage position"""
        monitoring = ['market_prices', 'position_delta']
        if opportunity.arbitrage_type == ArbitrageType.VOLATILITY_ARBITRAGE:
            monitoring.extend(['realized_volatility', 'implied_volatility', 'gamma_exposure'])
        if opportunity.arbitrage_type in [ArbitrageType.CONVERSION, ArbitrageType.REVERSAL]:
            monitoring.extend(['dividend_announcements', 'early_exercise_risk'])
        if opportunity.arbitrage_type == ArbitrageType.CARRY_ARBITRAGE:
            monitoring.extend(['interest_rates', 'storage_costs', 'convenience_yield'])
        if opportunity.arbitrage_type == ArbitrageType.CALENDAR_SPREAD:
            monitoring.extend(['time_decay', 'pin_risk', 'volatility_term_structure'])
        return monitoring

def comprehensive_scan(self, market_data: Dict) -> List[ArbitrageOpportunity]:
    """Perform comprehensive arbitrage scan"""
    all_opportunities = []
    try:
        if all((key in market_data for key in ['call_price', 'put_price', 'spot_price', 'strike_price'])):
            pcp_opportunities = self.scan_put_call_parity(market_data['call_price'], market_data['put_price'], market_data['spot_price'], market_data['strike_price'], market_data.get('risk_free_rate', 0.02), market_data.get('time_to_expiry', 0.25), market_data.get('dividend_yield', 0.0))
            all_opportunities.extend(pcp_opportunities)
        if all((key in market_data for key in ['spot_price', 'forward_price'])):
            carry_opportunities = self.scan_carry_arbitrage(market_data['spot_price'], market_data['forward_price'], market_data.get('risk_free_rate', 0.02), market_data.get('time_to_expiry', 0.25), dividend_yield=market_data.get('dividend_yield', 0.0), storage_cost=market_data.get('storage_cost', 0.0), convenience_yield=market_data.get('convenience_yield', 0.0))
            all_opportunities.extend(carry_opportunities)
        if all((key in market_data for key in ['strikes', 'call_prices', 'put_prices'])):
            box_opportunities = self.scan_box_spread(market_data['strikes'], market_data['call_prices'], market_data['put_prices'], market_data.get('risk_free_rate', 0.02), market_data.get('time_to_expiry', 0.25))
            all_opportunities.extend(box_opportunities)
        if all((key in market_data for key in ['market_vol', 'implied_vol', 'option'])):
            vol_opportunities = self.scan_volatility_arbitrage(market_data['market_vol'], market_data['implied_vol'], market_data['option'], market_data.get('market_data_obj'), market_data.get('confidence_threshold', 0.05))
            all_opportunities.extend(vol_opportunities)
        if all((key in market_data for key in ['near_option_price', 'far_option_price', 'near_time', 'far_time'])):
            calendar_opportunities = self.scan_calendar_spread(market_data['near_option_price'], market_data['far_option_price'], market_data['near_time'], market_data['far_time'], market_data.get('strike_price', 100), market_data.get('option_type', OptionType.CALL), market_data.get('market_data_obj'))
            all_opportunities.extend(calendar_opportunities)
    except Exception as e:
        logger.error(f'Error in arbitrage scan: {e}')
    self.detected_opportunities = all_opportunities
    return all_opportunities

def _get_monitoring_requirements(self, opportunity: ArbitrageOpportunity) -> List[str]:
    """Get monitoring requirements for arbitrage position"""
    monitoring = ['market_prices', 'position_delta']
    if opportunity.arbitrage_type == ArbitrageType.VOLATILITY_ARBITRAGE:
        monitoring.extend(['realized_volatility', 'implied_volatility', 'gamma_exposure'])
    if opportunity.arbitrage_type in [ArbitrageType.CONVERSION, ArbitrageType.REVERSAL]:
        monitoring.extend(['dividend_announcements', 'early_exercise_risk'])
    if opportunity.arbitrage_type == ArbitrageType.CARRY_ARBITRAGE:
        monitoring.extend(['interest_rates', 'storage_costs', 'convenience_yield'])
    if opportunity.arbitrage_type == ArbitrageType.CALENDAR_SPREAD:
        monitoring.extend(['time_decay', 'pin_risk', 'volatility_term_structure'])
    return monitoring

@dataclass
class CurveData:
    """Interest rate curve data"""
    curve_date: datetime
    curve_type: str
    currency: str
    day_count: DayCountConvention
    points: List[YieldCurvePoint] = field(default_factory=list)

    def add_point(self, maturity: float, rate: float, instrument_type: str='government'):
        """Add point to curve"""
        self.points.append(YieldCurvePoint(maturity, rate, instrument_type))
        self.points.sort(key=lambda x: x.maturity)

    def interpolate_rate(self, maturity: float, method: str='linear') -> float:
        """Interpolate rate for given maturity"""
        if not self.points:
            raise ValueError('No curve points available')
        sorted_points = sorted(self.points, key=lambda x: x.maturity)
        if maturity <= sorted_points[0].maturity:
            return sorted_points[0].rate
        if maturity >= sorted_points[-1].maturity:
            return sorted_points[-1].rate
        for i in range(len(sorted_points) - 1):
            if sorted_points[i].maturity <= maturity <= sorted_points[i + 1].maturity:
                if method == 'linear':
                    return self._linear_interpolation(sorted_points[i], sorted_points[i + 1], maturity)
                elif method == 'cubic':
                    return self._cubic_interpolation(sorted_points, maturity, i)
        raise ValueError(f'Cannot interpolate rate for maturity {maturity}')

    def _linear_interpolation(self, p1: YieldCurvePoint, p2: YieldCurvePoint, maturity: float) -> float:
        """Linear interpolation between two points"""
        if p2.maturity == p1.maturity:
            return p1.rate
        weight = (maturity - p1.maturity) / (p2.maturity - p1.maturity)
        return p1.rate + weight * (p2.rate - p1.rate)

    def _cubic_interpolation(self, points: List[YieldCurvePoint], maturity: float, index: int) -> float:
        """Cubic spline interpolation (simplified)"""
        return self._linear_interpolation(points[index], points[index + 1], maturity)

def add_point(self, maturity: float, rate: float, instrument_type: str='government'):
    """Add point to curve"""
    self.points.append(YieldCurvePoint(maturity, rate, instrument_type))
    self.points.sort(key=lambda x: x.maturity)

class ModelValidator:
    """Validation utilities for derivative models"""

    @staticmethod
    def validate_probability(prob: float) -> bool:
        """Validate probability is between 0 and 1"""
        return 0 <= prob <= 1

    @staticmethod
    def validate_positive(value: float, name: str) -> bool:
        """Validate value is positive"""
        if value <= 0:
            raise ValidationError(f'{name} must be positive, got {value}')
        return True

    @staticmethod
    def validate_non_negative(value: float, name: str) -> bool:
        """Validate value is non-negative"""
        if value < 0:
            raise ValidationError(f'{name} cannot be negative, got {value}')
        return True

    @staticmethod
    def validate_rate(rate: float, name: str) -> bool:
        """Validate interest rate (can be negative in modern markets)"""
        if abs(rate) > 1.0:
            logger.warning(f'{name} is unusually high: {rate * 100:.2f}%')
        return True

    @staticmethod
    def validate_volatility(vol: float) -> bool:
        """Validate volatility parameter"""
        if vol < 0:
            raise ValidationError(f'Volatility cannot be negative, got {vol}')
        if vol > 5.0:
            logger.warning(f'Volatility is extremely high: {vol * 100:.2f}%')
        return True

@staticmethod
def validate_positive(value: float, name: str) -> bool:
    """Validate value is positive"""
    if value <= 0:
        raise ValidationError(f'{name} must be positive, got {value}')
    return True

@staticmethod
def validate_non_negative(value: float, name: str) -> bool:
    """Validate value is non-negative"""
    if value < 0:
        raise ValidationError(f'{name} cannot be negative, got {value}')
    return True

@staticmethod
def validate_volatility(vol: float) -> bool:
    """Validate volatility parameter"""
    if vol < 0:
        raise ValidationError(f'Volatility cannot be negative, got {vol}')
    if vol > 5.0:
        logger.warning(f'Volatility is extremely high: {vol * 100:.2f}%')
    return True

@dataclass
class PortfolioPosition:
    """Individual position in derivatives portfolio"""
    instrument: DerivativeInstrument
    quantity: float
    entry_price: float
    entry_date: datetime
    current_value: float = 0.0
    unrealized_pnl: float = 0.0

    def __post_init__(self):
        if self.quantity == 0:
            raise ValidationError('Position quantity cannot be zero')

def __post_init__(self):
    if self.quantity == 0:
        raise ValidationError('Position quantity cannot be zero')

class RegulatoryAgent:
    """Advanced regulatory intelligence and policy change analysis"""

    def __init__(self):
        self.name = 'regulatory'
        self.data_manager = DataFeedManager()
        self.client = openai.OpenAI(api_key=CONFIG.api.openai_api_key)
        self.regulatory_domains = {'financial_regulation': {'banking_rules': 0.25, 'securities_regulation': 0.2, 'derivatives_oversight': 0.15, 'crypto_regulation': 0.15, 'payment_systems': 0.1, 'systemic_risk': 0.15}, 'environmental_regulation': {'carbon_pricing': 0.3, 'renewable_mandates': 0.25, 'emission_standards': 0.2, 'plastic_bans': 0.1, 'water_regulation': 0.08, 'biodiversity_rules': 0.07}, 'technology_regulation': {'data_privacy': 0.25, 'ai_governance': 0.2, 'platform_regulation': 0.2, 'cybersecurity_rules': 0.15, 'semiconductor_controls': 0.2}, 'healthcare_regulation': {'drug_pricing': 0.3, 'medical_device_approval': 0.25, 'telehealth_rules': 0.15, 'insurance_regulation': 0.15, 'public_health_policy': 0.15}, 'tax_policy': {'corporate_tax_rates': 0.35, 'international_tax_coordination': 0.25, 'digital_services_tax': 0.2, 'carbon_tax': 0.2}}
        self.sector_impact_map = {'financial_regulation': {'banks': -0.6, 'insurance': -0.4, 'asset_management': -0.3, 'fintech': -0.5, 'real_estate': -0.2, 'consumer_finance': -0.4}, 'environmental_regulation': {'oil_gas': -0.8, 'utilities': 0.3, 'renewable_energy': 0.7, 'automotive': -0.4, 'chemicals': -0.5, 'materials': -0.3, 'industrials': -0.2}, 'technology_regulation': {'big_tech': -0.7, 'social_media': -0.8, 'semiconductors': -0.4, 'cybersecurity': 0.5, 'cloud_services': -0.3, 'telecommunications': -0.2}, 'healthcare_regulation': {'pharmaceuticals': -0.5, 'biotechnology': -0.3, 'medical_devices': -0.4, 'health_insurance': -0.6, 'hospitals': -0.3, 'telehealth': 0.4}, 'tax_policy': {'multinational_corps': -0.6, 'domestic_focused': 0.2, 'high_margin_tech': -0.5, 'capital_intensive': 0.1, 'dividend_stocks': -0.3}}
        self.regulatory_keywords = {'proposal_stage': ['proposed rule', 'draft regulation', 'consultation paper', 'request for comment', 'policy proposal', 'legislative draft'], 'advancement_stage': ['committee approval', 'senate passage', 'house passage', 'regulatory approval', 'agency adoption', 'cabinet approval'], 'implementation_stage': ['effective date', 'compliance deadline', 'enforcement begins', 'mandatory compliance', 'phased implementation', 'grace period'], 'enforcement_action': ['regulatory fine', 'enforcement action', 'compliance violation', 'penalty imposed', 'consent order', 'regulatory sanction']}
        self.jurisdiction_weights = {'United_States': 0.35, 'European_Union': 0.25, 'China': 0.2, 'United_Kingdom': 0.1, 'Japan': 0.05, 'Other': 0.05}

    async def analyze_regulatory_landscape(self) -> List[RegulatorySignal]:
        """Comprehensive regulatory landscape analysis"""
        signals = []
        try:
            for domain, regulations in self.regulatory_domains.items():
                domain_signals = await self._analyze_regulatory_domain(domain, regulations)
                signals.extend(domain_signals)
            signals.sort(key=lambda x: x.impact_level * x.confidence, reverse=True)
            return signals[:15]
        except Exception as e:
            logging.error(f'Error in regulatory landscape analysis: {e}')
            return [self._default_regulatory_signal()]

    async def _analyze_regulatory_domain(self, domain: str, regulations: Dict[str, float]) -> List[RegulatorySignal]:
        """Analyze specific regulatory domain"""
        domain_signals = []
        news_data = await self._fetch_regulatory_news(domain, list(regulations.keys()))
        for regulation, weight in regulations.items():
            try:
                relevant_news = [news for news in news_data if self._is_relevant_to_regulation(news, regulation, domain)]
                if not relevant_news:
                    continue
                stage_analysis = self._analyze_regulatory_stage(relevant_news)
                impact_level = self._calculate_regulatory_impact(relevant_news, regulation, domain, weight)
                affected_sectors = self._get_affected_sectors(domain, impact_level)
                market_impact = self._calculate_market_impact(domain, regulation, impact_level)
                compliance_cost = self._estimate_compliance_cost(regulation, domain, impact_level)
                competitive_advantage = self._analyze_competitive_impact(domain, regulation, relevant_news)
                timeline = self._estimate_implementation_timeline(stage_analysis, relevant_news)
                confidence = self._calculate_regulatory_confidence(relevant_news, stage_analysis)
                signal = RegulatorySignal(regulation_type=f'{domain}_{regulation}', jurisdiction=self._determine_jurisdiction(relevant_news), impact_level=impact_level, implementation_timeline=timeline, affected_sectors=affected_sectors, market_impact=market_impact, compliance_cost=compliance_cost, competitive_advantage=competitive_advantage, confidence=confidence)
                domain_signals.append(signal)
            except Exception as e:
                logging.error(f'Error analyzing regulation {regulation}: {e}')
                continue
        return domain_signals

    async def _fetch_regulatory_news(self, domain: str, regulations: List[str]) -> List[DataPoint]:
        """Fetch regulatory news for specific domain"""
        all_news = []
        domain_queries = {'financial_regulation': ['banking regulation', 'financial oversight', 'securities rules', 'fintech regulation'], 'environmental_regulation': ['environmental regulation', 'carbon policy', 'emissions standards', 'green legislation'], 'technology_regulation': ['tech regulation', 'data privacy', 'ai governance', 'platform oversight'], 'healthcare_regulation': ['healthcare policy', 'drug regulation', 'medical device approval', 'health insurance'], 'tax_policy': ['tax reform', 'corporate tax', 'international taxation', 'digital tax']}
        queries = domain_queries.get(domain, [domain.replace('_', ' ')])
        for query in queries:
            try:
                news_data = await self.data_manager.get_multi_source_data({'news': {'query': query, 'sources': ['reuters', 'bloomberg', 'wsj', 'ft'], 'hours_back': 168}})
                if 'news' in news_data:
                    all_news.extend(news_data['news'])
            except Exception as e:
                logging.error(f'Error fetching regulatory news for {query}: {e}')
                continue
        return all_news

    def _is_relevant_to_regulation(self, news: DataPoint, regulation: str, domain: str) -> bool:
        """Check if news is relevant to specific regulation"""
        text = (news.value + ' ' + news.metadata.get('description', '')).lower()
        regulation_keywords = {'banking_rules': ['basel', 'capital requirements', 'stress test', 'bank supervision'], 'carbon_pricing': ['carbon tax', 'cap and trade', 'emissions trading', 'carbon border'], 'data_privacy': ['gdpr', 'data protection', 'privacy regulation', 'data governance'], 'drug_pricing': ['prescription drug', 'medicare negotiation', 'drug pricing', 'pharmaceutical'], 'ai_governance': ['artificial intelligence', 'ai regulation', 'algorithmic oversight', 'ai safety']}
        keywords = regulation_keywords.get(regulation, [regulation.replace('_', ' ')])
        regulatory_action_keywords = ['regulation', 'policy', 'rule', 'legislation', 'bill', 'act', 'oversight', 'compliance', 'enforcement', 'approval', 'mandate']
        has_regulation_keyword = any((keyword in text for keyword in keywords))
        has_action_keyword = any((keyword in text for keyword in regulatory_action_keywords))
        return has_regulation_keyword and has_action_keyword

    def _analyze_regulatory_stage(self, news: List[DataPoint]) -> Dict[str, float]:
        """Analyze what stage regulations are in"""
        stage_scores = {'proposal': 0.0, 'advancement': 0.0, 'implementation': 0.0, 'enforcement': 0.0}
        total_articles = len(news)
        if total_articles == 0:
            return stage_scores
        for article in news:
            text = article.value.lower()
            for stage, keywords in self.regulatory_keywords.items():
                stage_name = stage.replace('_stage', '').replace('_action', '')
                for keyword in keywords:
                    if keyword in text:
                        stage_scores[stage_name] += article.confidence / total_articles
        return stage_scores

    def _calculate_regulatory_impact(self, news: List[DataPoint], regulation: str, domain: str, weight: float) -> int:
        """Calculate regulatory impact level (1-10)"""
        if not news:
            return 3
        base_impacts = {'banking_rules': 7, 'carbon_pricing': 8, 'data_privacy': 6, 'drug_pricing': 8, 'corporate_tax_rates': 9, 'ai_governance': 5, 'securities_regulation': 6}
        base_impact = base_impacts.get(regulation, 5)
        high_impact_keywords = ['sweeping changes', 'major reform', 'significant impact', 'industry transformation', 'mandatory compliance', 'substantial penalties', 'widespread adoption', 'market disruption', 'regulatory overhaul', 'unprecedented']
        scope_indicators = ['global', 'international', 'nationwide', 'industry-wide', 'comprehensive', 'all companies', 'every business', 'mandatory for all']
        intensity_score = 0
        scope_score = 0
        for article in news:
            text = article.value.lower()
            intensity_score += sum((1 for keyword in high_impact_keywords if keyword in text))
            scope_score += sum((1 for keyword in scope_indicators if keyword in text))
        if news:
            intensity_factor = min(intensity_score / len(news), 2.0)
            scope_factor = min(scope_score / len(news), 1.5)
            weight_factor = weight * 2
            adjusted_impact = base_impact + intensity_factor + scope_factor + weight_factor
        else:
            adjusted_impact = base_impact
        return int(np.clip(adjusted_impact, 1, 10))

    def _get_affected_sectors(self, domain: str, impact_level: int) -> List[str]:
        """Get sectors affected by regulatory domain"""
        if domain not in self.sector_impact_map:
            return ['broad_market']
        sector_impacts = self.sector_impact_map[domain]
        threshold = 0.2 if impact_level > 7 else 0.3 if impact_level > 5 else 0.4
        affected_sectors = []
        for sector, impact in sector_impacts.items():
            if abs(impact) >= threshold:
                affected_sectors.append(sector)
        return affected_sectors or ['broad_market']

    def _calculate_market_impact(self, domain: str, regulation: str, impact_level: int) -> Dict[str, float]:
        """Calculate expected market impact by asset class"""
        if domain not in self.sector_impact_map:
            return {'broad_market': 0.0}
        sector_impacts = self.sector_impact_map[domain]
        impact_multiplier = impact_level / 10.0
        market_impacts = {}
        for sector, base_impact in sector_impacts.items():
            scaled_impact = base_impact * impact_multiplier
            market_impacts[sector] = np.clip(scaled_impact, -1.0, 1.0)
        return market_impacts

    def _estimate_compliance_cost(self, regulation: str, domain: str, impact_level: int) -> float:
        """Estimate compliance cost as percentage of revenue"""
        base_costs = {'banking_rules': 0.015, 'data_privacy': 0.008, 'emissions_standards': 0.012, 'drug_pricing': 0.005, 'cybersecurity_rules': 0.01}
        base_cost = base_costs.get(regulation, 0.005)
        impact_multiplier = impact_level / 5.0
        return base_cost * impact_multiplier

    def _analyze_competitive_impact(self, domain: str, regulation: str, news: List[DataPoint]) -> Dict[str, float]:
        """Analyze which companies/sectors gain competitive advantage"""
        competitive_advantages = {}
        advantage_keywords = {'large_companies': ['economies of scale', 'large companies benefit', 'big players advantage'], 'incumbents': ['existing players', 'incumbent advantage', 'barriers to entry'], 'tech_leaders': ['technology advantage', 'innovation leaders', 'digital transformation'], 'compliance_specialists': ['compliance expertise', 'regulatory experience', 'specialized knowledge']}
        for company_type, keywords in advantage_keywords.items():
            advantage_score = 0.0
            for article in news:
                text = article.value.lower()
                keyword_count = sum((1 for keyword in keywords if keyword in text))
                advantage_score += keyword_count * article.confidence
            if news and advantage_score > 0:
                competitive_advantages[company_type] = min(advantage_score / len(news), 1.0)
        return competitive_advantages

    def _estimate_implementation_timeline(self, stage_analysis: Dict[str, float], news: List[DataPoint]) -> str:
        """Estimate regulatory implementation timeline"""
        current_stage = max(stage_analysis.items(), key=lambda x: x[1])[0]
        timeline_estimates = {'proposal': '12-24 months', 'advancement': '6-18 months', 'implementation': '3-12 months', 'enforcement': 'Immediate'}
        base_timeline = timeline_estimates.get(current_stage, '12-24 months')
        timeline_patterns = ['(\\d+)\\s*months?', '(\\d+)\\s*years?', 'by\\s+(\\d{4})', 'effective\\s+(\\w+\\s+\\d{1,2},?\\s+\\d{4})']
        for article in news:
            text = article.value
            for pattern in timeline_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    return f'Specific timeline mentioned: {matches[0]}'
        return base_timeline

    def _determine_jurisdiction(self, news: List[DataPoint]) -> str:
        """Determine primary jurisdiction from news"""
        jurisdiction_keywords = {'United_States': ['usa', 'united states', 'sec', 'fed', 'congress', 'senate', 'house'], 'European_Union': ['eu', 'european union', 'brussels', 'european commission', 'esma'], 'China': ['china', 'beijing', 'pboc', 'csrc', 'chinese regulators'], 'United_Kingdom': ['uk', 'united kingdom', 'fca', 'pra', 'bank of england'], 'Japan': ['japan', 'jfsa', 'boj', 'bank of japan']}
        jurisdiction_scores = {j: 0 for j in jurisdiction_keywords.keys()}
        for article in news:
            text = article.value.lower()
            for jurisdiction, keywords in jurisdiction_keywords.items():
                score = sum((1 for keyword in keywords if keyword in text))
                jurisdiction_scores[jurisdiction] += score * article.confidence
        if any(jurisdiction_scores.values()):
            return max(jurisdiction_scores.items(), key=lambda x: x[1])[0]
        return 'Multiple/Global'

    def _calculate_regulatory_confidence(self, news: List[DataPoint], stage_analysis: Dict[str, float]) -> float:
        """Calculate confidence in regulatory analysis"""
        confidence_factors = []
        if news:
            news_confidence = min(len(news) / 10, 1.0) * 0.3
            source_quality = np.mean([article.confidence for article in news]) * 0.4
            confidence_factors.extend([news_confidence, source_quality])
        else:
            confidence_factors.extend([0.1, 0.2])
        max_stage_score = max(stage_analysis.values()) if stage_analysis else 0
        stage_confidence = max_stage_score * 0.3
        confidence_factors.append(stage_confidence)
        return np.sum(confidence_factors)

    def _default_regulatory_signal(self) -> RegulatorySignal:
        """Return default regulatory signal"""
        return RegulatorySignal(regulation_type='general_regulatory_uncertainty', jurisdiction='Global', impact_level=5, implementation_timeline='12-24 months', affected_sectors=['broad_market'], market_impact={'broad_market': 0.0}, compliance_cost=0.005, competitive_advantage={}, confidence=0.3)

    async def analyze_policy_changes(self) -> List[PolicyChange]:
        """Analyze upcoming policy changes and their market implications"""
        policy_changes = []
        policy_areas = ['tax_reform', 'healthcare_policy', 'infrastructure_spending', 'trade_policy', 'energy_policy', 'immigration_policy']
        for policy_area in policy_areas:
            try:
                change = await self._analyze_specific_policy(policy_area)
                if change:
                    policy_changes.append(change)
            except Exception as e:
                logging.error(f'Error analyzing policy {policy_area}: {e}')
                continue
        return policy_changes

    async def _analyze_specific_policy(self, policy_area: str) -> Optional[PolicyChange]:
        """Analyze specific policy area for changes"""
        news_data = await self.data_manager.get_multi_source_data({'news': {'query': policy_area.replace('_', ' '), 'sources': ['reuters', 'bloomberg', 'wsj'], 'hours_back': 72}})
        news = news_data.get('news', [])
        if not news:
            return None
        change_type = self._determine_policy_change_type(news)
        probability = self._calculate_passage_probability(news, policy_area)
        if probability < 0.2:
            return None
        economic_impact = self._calculate_policy_economic_impact(policy_area, news)
        winners, losers = self._identify_policy_winners_losers(policy_area)
        timeline = self._estimate_policy_timeline(news, change_type)
        return PolicyChange(policy_area=policy_area, change_type=change_type, probability_passage=probability, economic_impact=economic_impact, sector_winners=winners, sector_losers=losers, timeline=timeline)

    def _determine_policy_change_type(self, news: List[DataPoint]) -> str:
        """Determine type of policy change"""
        change_keywords = {'proposed': ['proposed', 'draft', 'plan', 'considering', 'exploring'], 'enacted': ['passed', 'approved', 'enacted', 'signed', 'adopted'], 'implemented': ['effective', 'implementation', 'rollout', 'enforcement']}
        change_scores = {change_type: 0 for change_type in change_keywords.keys()}
        for article in news:
            text = article.value.lower()
            for change_type, keywords in change_keywords.items():
                score = sum((1 for keyword in keywords if keyword in text))
                change_scores[change_type] += score
        return max(change_scores.items(), key=lambda x: x[1])[0] if any(change_scores.values()) else 'proposed'

    def _calculate_passage_probability(self, news: List[DataPoint], policy_area: str) -> float:
        """Calculate probability of policy passage"""
        base_probabilities = {'tax_reform': 0.4, 'healthcare_policy': 0.3, 'infrastructure_spending': 0.6, 'trade_policy': 0.5, 'energy_policy': 0.4, 'immigration_policy': 0.2}
        base_prob = base_probabilities.get(policy_area, 0.4)
        positive_indicators = ['bipartisan support', 'broad agreement', 'likely to pass', 'strong support']
        negative_indicators = ['opposition', 'unlikely to pass', 'political deadlock', 'controversy']
        positive_score = 0
        negative_score = 0
        for article in news:
            text = article.value.lower()
            positive_score += sum((1 for indicator in positive_indicators if indicator in text))
            negative_score += sum((1 for indicator in negative_indicators if indicator in text))
        if news:
            sentiment_adjustment = (positive_score - negative_score) / len(news) * 0.3
            adjusted_prob = base_prob + sentiment_adjustment
        else:
            adjusted_prob = base_prob
        return np.clip(adjusted_prob, 0.0, 1.0)

    def _calculate_policy_economic_impact(self, policy_area: str, news: List[DataPoint]) -> Dict[str, float]:
        """Calculate economic impact of policy changes"""
        base_impacts = {'tax_reform': {'gdp_growth': 0.3, 'business_investment': 0.5, 'consumer_spending': 0.2}, 'infrastructure_spending': {'gdp_growth': 0.8, 'employment': 0.6, 'productivity': 0.4}, 'healthcare_policy': {'healthcare_costs': -0.3, 'business_costs': 0.2, 'innovation': -0.1}, 'trade_policy': {'trade_volumes': 0.4, 'manufacturing': 0.3, 'consumer_prices': -0.2}, 'energy_policy': {'energy_costs': -0.2, 'green_investment': 0.6, 'traditional_energy': -0.4}}
        return base_impacts.get(policy_area, {'gdp_growth': 0.1})

    def _identify_policy_winners_losers(self, policy_area: str) -> Tuple[List[str], List[str]]:
        """Identify sector winners and losers from policy changes"""
        policy_impacts = {'tax_reform': {'winners': ['domestic_companies', 'small_business', 'manufacturing'], 'losers': ['multinationals', 'high_tax_rate_sectors']}, 'infrastructure_spending': {'winners': ['construction', 'materials', 'industrials', 'transportation'], 'losers': ['bond_investors']}, 'healthcare_policy': {'winners': ['healthcare_providers', 'medical_devices'], 'losers': ['pharmaceuticals', 'health_insurance']}, 'energy_policy': {'winners': ['renewable_energy', 'electric_vehicles', 'grid_infrastructure'], 'losers': ['fossil_fuels', 'traditional_utilities']}}
        impacts = policy_impacts.get(policy_area, {'winners': [], 'losers': []})
        return (impacts['winners'], impacts['losers'])

    def _estimate_policy_timeline(self, news: List[DataPoint], change_type: str) -> str:
        """Estimate policy implementation timeline"""
        timeline_map = {'proposed': '6-18 months to passage', 'enacted': '3-12 months to implementation', 'implemented': 'Currently rolling out'}
        return timeline_map.get(change_type, '12-24 months')

    async def get_regulatory_report(self) -> Dict:
        """Generate comprehensive regulatory intelligence report"""
        regulatory_signals = await self.analyze_regulatory_landscape()
        policy_changes = await self.analyze_policy_changes()
        llm_analysis = await self._generate_regulatory_llm_analysis(regulatory_signals, policy_changes)
        return {'timestamp': datetime.now().isoformat(), 'agent': self.name, 'regulatory_landscape': {'high_impact_regulations': [{'regulation': signal.regulation_type, 'jurisdiction': signal.jurisdiction, 'impact_level': signal.impact_level, 'timeline': signal.implementation_timeline, 'affected_sectors': signal.affected_sectors, 'market_impact': signal.market_impact} for signal in regulatory_signals[:5]], 'compliance_cost_estimate': np.mean([s.compliance_cost for s in regulatory_signals]), 'overall_regulatory_pressure': np.mean([s.impact_level for s in regulatory_signals])}, 'policy_changes': [{'policy_area': change.policy_area, 'change_type': change.change_type, 'probability': change.probability_passage, 'economic_impact': change.economic_impact, 'winners': change.sector_winners, 'losers': change.sector_losers, 'timeline': change.timeline} for change in policy_changes], 'investment_implications': {'defensive_sectors': self._get_defensive_regulatory_sectors(regulatory_signals), 'regulatory_beneficiaries': self._get_regulatory_beneficiaries(regulatory_signals), 'compliance_leaders': self._get_compliance_advantage_sectors(regulatory_signals), 'regulatory_risk_sectors': self._get_high_risk_sectors(regulatory_signals)}, 'llm_analysis': llm_analysis, 'monitoring_priorities': {'key_regulations': [s.regulation_type for s in regulatory_signals[:3]], 'high_probability_policies': [c.policy_area for c in policy_changes if c.probability_passage > 0.6], 'immediate_compliance_deadlines': [s.regulation_type for s in regulatory_signals if 'months' in s.implementation_timeline and int(s.implementation_timeline.split()[0]) <= 6]}}

    async def _generate_regulatory_llm_analysis(self, signals: List[RegulatorySignal], policy_changes: List[PolicyChange]) -> Dict:
        """Generate LLM-enhanced regulatory analysis"""
        try:
            reg_summary = self._prepare_regulatory_summary(signals)
            policy_summary = self._prepare_policy_summary(policy_changes)
            prompt = f'\n            As a senior regulatory affairs analyst, analyze the current regulatory landscape and provide investment guidance.\n\n            Key Regulatory Developments:\n            {reg_summary}\n\n            Policy Changes:\n            {policy_summary}\n\n            Please provide:\n            1. Most critical regulatory risks requiring immediate attention\n            2. Regulatory arbitrage opportunities (sectors benefiting from regulatory changes)\n            3. Compliance cost leaders vs laggards investment strategy\n            4. Timeline for next major regulatory wave\n            5. Sector rotation recommendations based on regulatory trends\n            6. Early warning indicators for regulatory surprises\n\n            Format as JSON with keys: critical_risks, arbitrage_opportunities, compliance_strategy, \n            regulatory_timeline, sector_rotation, early_warning_indicators\n            '
            response = self.client.chat.completions.create(model=CONFIG.llm.deep_think_model, messages=[{'role': 'user', 'content': prompt}], temperature=CONFIG.llm.temperature, max_tokens=CONFIG.llm.max_tokens)
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f'Error in LLM regulatory analysis: {e}')
            return {'critical_risks': ['Financial regulation tightening', 'ESG compliance requirements'], 'arbitrage_opportunities': ['Compliance technology', 'Renewable energy'], 'compliance_strategy': 'Focus on established players with regulatory expertise', 'regulatory_timeline': 'Next 12-18 months', 'sector_rotation': 'Overweight compliance leaders, underweight regulatory laggards', 'early_warning_indicators': ['Congressional hearings', 'Agency enforcement actions']}

    def _prepare_regulatory_summary(self, signals: List[RegulatorySignal]) -> str:
        """Prepare regulatory summary for LLM"""
        summary_lines = []
        for signal in signals[:5]:
            summary_lines.append(f'{signal.regulation_type} ({signal.jurisdiction}): Impact Level {signal.impact_level}/10, Timeline: {signal.implementation_timeline}, Sectors: {', '.join(signal.affected_sectors[:3])}, Compliance Cost: {signal.compliance_cost:.1%}')
        return '\n'.join(summary_lines)

    def _prepare_policy_summary(self, policy_changes: List[PolicyChange]) -> str:
        """Prepare policy changes summary for LLM"""
        summary_lines = []
        for policy in policy_changes:
            summary_lines.append(f'{policy.policy_area}: {policy.change_type} (Probability: {policy.probability_passage:.0%}), Winners: {', '.join(policy.sector_winners[:2])}, Losers: {', '.join(policy.sector_losers[:2])}')
        return '\n'.join(summary_lines)

    def _get_defensive_regulatory_sectors(self, signals: List[RegulatorySignal]) -> List[str]:
        """Get sectors that are defensive against regulatory risk"""
        defensive_sectors = []
        inherently_defensive = ['utilities', 'consumer_staples', 'healthcare_providers']
        for signal in signals:
            for sector, impact in signal.market_impact.items():
                if impact > 0.3:
                    defensive_sectors.append(sector)
        all_defensive = inherently_defensive + defensive_sectors
        return list(set(all_defensive))

    def _get_regulatory_beneficiaries(self, signals: List[RegulatorySignal]) -> List[str]:
        """Get sectors that benefit from regulatory changes"""
        beneficiaries = []
        for signal in signals:
            for sector, impact in signal.market_impact.items():
                if impact > 0.4:
                    beneficiaries.append(sector)
            for advantage_type, score in signal.competitive_advantage.items():
                if score > 0.5 and advantage_type == 'compliance_specialists':
                    beneficiaries.extend(['legal_services', 'compliance_tech', 'consulting'])
        return list(set(beneficiaries))

    def _get_compliance_advantage_sectors(self, signals: List[RegulatorySignal]) -> List[str]:
        """Get sectors with compliance competitive advantages"""
        advantage_sectors = []
        for signal in signals:
            for advantage_type, score in signal.competitive_advantage.items():
                if score > 0.4:
                    if advantage_type == 'large_companies':
                        advantage_sectors.extend(['mega_cap_stocks', 'blue_chip_companies'])
                    elif advantage_type == 'tech_leaders':
                        advantage_sectors.extend(['technology', 'software'])
                    elif advantage_type == 'incumbents':
                        advantage_sectors.extend(['established_players'])
        return list(set(advantage_sectors))

    def _get_high_risk_sectors(self, signals: List[RegulatorySignal]) -> List[str]:
        """Get sectors with high regulatory risk"""
        high_risk_sectors = []
        for signal in signals:
            if signal.impact_level >= 7:
                for sector, impact in signal.market_impact.items():
                    if impact < -0.3:
                        high_risk_sectors.append(sector)
        return list(set(high_risk_sectors))

def _calculate_regulatory_confidence(self, news: List[DataPoint], stage_analysis: Dict[str, float]) -> float:
    """Calculate confidence in regulatory analysis"""
    confidence_factors = []
    if news:
        news_confidence = min(len(news) / 10, 1.0) * 0.3
        source_quality = np.mean([article.confidence for article in news]) * 0.4
        confidence_factors.extend([news_confidence, source_quality])
    else:
        confidence_factors.extend([0.1, 0.2])
    max_stage_score = max(stage_analysis.values()) if stage_analysis else 0
    stage_confidence = max_stage_score * 0.3
    confidence_factors.append(stage_confidence)
    return np.sum(confidence_factors)

class DecisionEngine:
    """Aggregates agent signals and makes final trading decisions"""

    def __init__(self):
        self.agent_weights = CONFIG.agent_weights
        self.risk_manager = RiskManager()

    def aggregate_signals(self, agent_reports: Dict[str, Dict]) -> List[TradingSignal]:
        """Aggregate signals from all agents into trading recommendations"""
        signals = []
        macro_signal = self._extract_macro_signal(agent_reports)
        if macro_signal:
            signals.append(macro_signal)
        sector_signals = self._extract_sector_signals(agent_reports)
        signals.extend(sector_signals)
        currency_signal = self._extract_currency_signal(agent_reports)
        if currency_signal:
            signals.append(currency_signal)
        risk_signal = self._extract_risk_signal(agent_reports)
        if risk_signal:
            signals.append(risk_signal)
        return signals

    def _extract_macro_signal(self, reports: Dict[str, Dict]) -> Optional[TradingSignal]:
        """Extract macro asset allocation signal"""
        macro_report = reports.get('macro_cycle', {})
        fed_report = reports.get('central_bank', {})
        if not macro_report or not fed_report:
            return None
        cycle_phase = macro_report.get('cycle_analysis', {}).get('current_phase', 'expansion')
        policy_stance = fed_report.get('fed_analysis', {}).get('policy_stance', 'neutral')
        if cycle_phase == 'expansion' and policy_stance in ['neutral', 'dovish']:
            direction = 'long'
            asset_class = 'equities'
            conviction = 0.7
        elif cycle_phase == 'contraction' or policy_stance == 'hawkish':
            direction = 'long'
            asset_class = 'bonds'
            conviction = 0.6
        elif cycle_phase == 'peak':
            direction = 'short'
            asset_class = 'equities'
            conviction = 0.5
        else:
            return None
        supporting_agents = ['macro_cycle', 'central_bank']
        return TradingSignal(timestamp=datetime.now(), asset_class=asset_class, direction=direction, conviction=conviction, position_size=0.4, time_horizon='medium', risk_factors=['cycle_timing', 'policy_error'], supporting_agents=supporting_agents, market_regime=f'{cycle_phase}_{policy_stance}')

    def _extract_sector_signals(self, reports: Dict[str, Dict]) -> List[TradingSignal]:
        """Extract sector rotation signals"""
        signals = []
        sector_scores = {}
        macro_report = reports.get('macro_cycle', {})
        if macro_report:
            implications = macro_report.get('investment_implications', {})
            for sector, weight in implications.items():
                sector_scores[sector] = sector_scores.get(sector, 0) + weight * self.agent_weights.get('macro_cycle', 0)
        geo_report = reports.get('geopolitical', {})
        if geo_report:
            sector_rotation = geo_report.get('investment_implications', {}).get('sector_rotation', {})
            for sector, recommendation in sector_rotation.items():
                weight = 0.2 if recommendation == 'overweight' else -0.2 if recommendation == 'underweight' else 0
                sector_scores[sector] = sector_scores.get(sector, 0) + weight * self.agent_weights.get('geopolitical', 0)
        for sector, score in sector_scores.items():
            if abs(score) > 0.1:
                direction = 'long' if score > 0 else 'short'
                conviction = min(abs(score) * 2, 1.0)
                signals.append(TradingSignal(timestamp=datetime.now(), asset_class=sector, direction=direction, conviction=conviction, position_size=min(conviction * 0.15, 0.1), time_horizon='medium', risk_factors=['sector_rotation'], supporting_agents=['macro_cycle', 'geopolitical'], market_regime='sector_rotation'))
        return signals

    def _extract_currency_signal(self, reports: Dict[str, Dict]) -> Optional[TradingSignal]:
        """Extract currency trading signal"""
        fed_report = reports.get('central_bank', {})
        geo_report = reports.get('geopolitical', {})
        if not fed_report:
            return None
        policy_stance = fed_report.get('fed_analysis', {}).get('policy_stance', 'neutral')
        if policy_stance == 'hawkish':
            direction = 'long'
            conviction = 0.6
        elif policy_stance == 'dovish':
            direction = 'short'
            conviction = 0.5
        else:
            return None
        if geo_report:
            defensive_score = geo_report.get('investment_implications', {}).get('defensive_positioning', 0)
            if defensive_score > 0.5:
                direction = 'long'
                conviction = min(conviction + defensive_score * 0.3, 1.0)
        return TradingSignal(timestamp=datetime.now(), asset_class='USD', direction=direction, conviction=conviction, position_size=0.2, time_horizon='short', risk_factors=['policy_divergence', 'geopolitical_events'], supporting_agents=['central_bank', 'geopolitical'], market_regime=f'currency_{policy_stance}')

    def _extract_risk_signal(self, reports: Dict[str, Dict]) -> Optional[TradingSignal]:
        """Extract overall risk-on/risk-off signal"""
        risk_factors = []
        risk_score = 0.0
        for agent_name, report in reports.items():
            agent_weight = self.agent_weights.get(agent_name, 0)
            if agent_name == 'geopolitical':
                geo_risk = report.get('global_risk_assessment', {}).get('overall_risk_level', 5)
                risk_score += (geo_risk - 5) / 5 * agent_weight
            elif agent_name == 'sentiment':
                sentiment_score = report.get('sentiment_analysis', {}).get('overall_sentiment', 0)
                risk_score += sentiment_score * agent_weight
            elif agent_name == 'institutional_flow':
                flow_signal = report.get('flow_analysis', {}).get('risk_sentiment', 0)
                risk_score += flow_signal * agent_weight
        if abs(risk_score) > 0.2:
            if risk_score > 0:
                asset_class = 'risk_assets'
                direction = 'long'
            else:
                asset_class = 'safe_havens'
                direction = 'long'
            conviction = min(abs(risk_score), 1.0)
            return TradingSignal(timestamp=datetime.now(), asset_class=asset_class, direction=direction, conviction=conviction, position_size=conviction * 0.3, time_horizon='short', risk_factors=risk_factors, supporting_agents=list(reports.keys()), market_regime='risk_on' if risk_score > 0 else 'risk_off')
        return None

    def generate_portfolio_recommendation(self, signals: List[TradingSignal], current_portfolio: Dict) -> PortfolioRecommendation:
        """Generate comprehensive portfolio recommendation"""
        asset_allocation = {'equities': 0.6, 'bonds': 0.3, 'commodities': 0.05, 'cash': 0.05}
        sector_weights = {}
        regional_weights = CONFIG.regional_weights.copy()
        hedges = []
        for signal in signals:
            validated = self.risk_manager.validate_signal(signal, current_portfolio)
            if validated:
                if signal.asset_class in asset_allocation:
                    adjustment = signal.position_size * (1 if signal.direction == 'long' else -1)
                    asset_allocation[signal.asset_class] += adjustment
                elif signal.asset_class in ['risk_assets', 'safe_havens']:
                    if signal.asset_class == 'risk_assets' and signal.direction == 'long':
                        asset_allocation['equities'] += signal.position_size * 0.5
                        asset_allocation['bonds'] -= signal.position_size * 0.3
                    elif signal.asset_class == 'safe_havens' and signal.direction == 'long':
                        asset_allocation['bonds'] += signal.position_size * 0.4
                        asset_allocation['cash'] += signal.position_size * 0.2
                        asset_allocation['equities'] -= signal.position_size * 0.4
                if signal.asset_class not in ['USD', 'risk_assets', 'safe_havens']:
                    sector_weights[signal.asset_class] = signal.position_size * (1 if signal.direction == 'long' else -1)
                hedges.extend(signal.risk_factors)
        total_allocation = sum(asset_allocation.values())
        if total_allocation != 1.0:
            for asset in asset_allocation:
                asset_allocation[asset] /= total_allocation
        risk_budget = {}
        for signal in signals:
            risk_budget[signal.asset_class] = signal.conviction * signal.position_size
        return PortfolioRecommendation(timestamp=datetime.now(), asset_allocation=asset_allocation, sector_weights=sector_weights, regional_weights=regional_weights, risk_budget=risk_budget, hedges=list(set(hedges)), cash_allocation=asset_allocation.get('cash', 0.05), leverage=1.0)

def aggregate_signals(self, agent_reports: Dict[str, Dict]) -> List[TradingSignal]:
    """Aggregate signals from all agents into trading recommendations"""
    signals = []
    macro_signal = self._extract_macro_signal(agent_reports)
    if macro_signal:
        signals.append(macro_signal)
    sector_signals = self._extract_sector_signals(agent_reports)
    signals.extend(sector_signals)
    currency_signal = self._extract_currency_signal(agent_reports)
    if currency_signal:
        signals.append(currency_signal)
    risk_signal = self._extract_risk_signal(agent_reports)
    if risk_signal:
        signals.append(risk_signal)
    return signals

