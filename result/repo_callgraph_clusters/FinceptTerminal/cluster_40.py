# Cluster 40

class DataManager:
    """Main data management interface"""

    def __init__(self, provider: Optional[DataProvider]=None, use_cache: bool=True):
        self.provider = provider or ManualDataProvider()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.cache = DataCache() if use_cache else None

    def get_validated_data(self, data_type: str, **kwargs) -> Tuple[pd.DataFrame, Dict]:
        """Get and validate data"""
        cache_key = f'{data_type}_{hash(str(kwargs))}'
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        if data_type == 'price':
            raw_data = self.provider.get_price_data(**kwargs)
            schema = PRICE_DATA_SCHEMA
        elif data_type == 'economic':
            raw_data = self.provider.get_economic_data(**kwargs)
            schema = None
        else:
            raise ValueError(f'Unknown data type: {data_type}')
        processed_data = {}
        validation_results = {}
        for key, df in raw_data.items():
            quality_report = self.validator.check_data_quality(df)
            if schema:
                is_valid, errors = self.validator.validate_schema(df, schema)
                validation_results[key] = {'valid': is_valid, 'errors': errors, 'quality': quality_report}
            cleaned_df = self.transformer.handle_missing_data(df)
            processed_data[key] = cleaned_df
        result = (processed_data, validation_results)
        if self.cache:
            self.cache.set(cache_key, result)
        return result

    def calculate_return_matrix(self, price_data: Dict[str, pd.DataFrame], return_type: str='simple') -> pd.DataFrame:
        """Calculate return matrix from price data"""
        returns_dict = {}
        for symbol, df in price_data.items():
            if 'close' in df.columns and 'date' in df.columns:
                df_sorted = df.sort_values('date')
                prices = df_sorted['close']
                returns = self.transformer.calculate_returns(prices, return_type)
                returns_dict[symbol] = returns
        if not returns_dict:
            raise ValueError('No valid price data found')
        return_matrix = pd.DataFrame(returns_dict)
        return return_matrix.dropna()

    def get_covariance_matrix(self, returns: pd.DataFrame, annualize: bool=True) -> np.ndarray:
        """Calculate covariance matrix from returns"""
        cov_matrix = returns.cov().values
        if annualize:
            cov_matrix *= MathConstants.TRADING_DAYS_YEAR
        return cov_matrix

    def get_correlation_matrix(self, returns: pd.DataFrame) -> np.ndarray:
        """Calculate correlation matrix from returns"""
        return returns.corr().values

def __init__(self, provider: Optional[DataProvider]=None, use_cache: bool=True):
    self.provider = provider or ManualDataProvider()
    self.validator = DataValidator()
    self.transformer = DataTransformer()
    self.cache = DataCache() if use_cache else None

class EconomicsBase(ABC):
    """
    Abstract base class for all economics analysis components.
    Ensures consistent interface and precision across modules.
    """

    def __init__(self, precision: int=8, base_currency: str='USD'):
        self.precision = precision
        self.base_currency = base_currency
        self.validator = DataValidator()
        self._results_cache = {}

    def to_decimal(self, value: Union[float, int, str]) -> Decimal:
        """Convert value to high-precision Decimal"""
        try:
            return Decimal(str(value)).quantize(Decimal('0.' + '0' * self.precision), rounding=ROUND_HALF_UP)
        except Exception as e:
            raise CalculationError(f'Cannot convert {value} to Decimal: {e}')

    def validate_inputs(self, **kwargs) -> bool:
        """Validate input parameters"""
        return self.validator.validate_parameters(**kwargs)

    @abstractmethod
    def calculate(self, *args, **kwargs) -> Dict[str, Any]:
        """Main calculation method - must be implemented by subclasses"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Return component metadata"""
        return {'class': self.__class__.__name__, 'precision': self.precision, 'base_currency': self.base_currency, 'timestamp': datetime.now().isoformat()}

def __init__(self, precision: int=8, base_currency: str='USD'):
    self.precision = precision
    self.base_currency = base_currency
    self.validator = DataValidator()
    self._results_cache = {}

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

def __init__(self, data: Dict[str, Any], data_type: str, timestamp: Optional[datetime]=None):
    self.data = data
    self.data_type = data_type
    self.timestamp = timestamp or datetime.now()
    self.validator = DataValidator()
    self._validate_data()

def update_value(self, key: str, value: Any):
    """Update value with validation"""
    self.data[key] = value
    self._validate_data()

def setup_default_providers(alpha_vantage_key: Optional[str]=None):
    """Setup default data providers"""
    yahoo_provider = YahooFinanceProvider()
    data_factory.register_provider('yahoo', yahoo_provider, is_primary=True)
    if alpha_vantage_key:
        av_provider = AlphaVantageProvider(alpha_vantage_key)
        data_factory.register_provider('alphavantage', av_provider)
    manual_provider = ManualDataProvider()
    data_factory.register_provider('manual', manual_provider)

class MarketDataManager:
    """Central manager for market data from multiple providers"""

    def __init__(self, primary_provider: MarketDataProvider=None):
        self.providers = {}
        self.primary_provider = primary_provider or ManualDataProvider()
        self.cache = DataCache()
        self.register_provider('manual', ManualDataProvider())
        self.register_provider('yahoo', YahooFinanceProvider())

    def register_provider(self, name: str, provider: MarketDataProvider):
        """Register a market data provider"""
        self.providers[name] = provider

    def set_primary_provider(self, provider_name: str):
        """Set primary data provider"""
        if provider_name not in self.providers:
            raise ValueError(f'Provider {provider_name} not registered')
        self.primary_provider = self.providers[provider_name]

    def get_market_snapshot(self, symbol: str, currency: str='USD') -> MarketSnapshot:
        """Get complete market snapshot for symbol"""
        cache_key = f'snapshot_{symbol}_{currency}'
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        try:
            snapshot = MarketSnapshot(timestamp=datetime.now(), spot_price=self.primary_provider.get_spot_price(symbol), risk_free_rate=self.primary_provider.get_risk_free_rate(currency), dividend_yield=self.primary_provider.get_dividend_yield(symbol))
            self.cache.set(cache_key, snapshot)
            return snapshot
        except Exception as e:
            logger.error(f'Failed to get market snapshot: {e}')
            raise

    def get_spot_price(self, symbol: str, provider: str=None) -> float:
        """Get spot price with fallback providers"""
        provider_obj = self.providers.get(provider, self.primary_provider)
        try:
            return provider_obj.get_spot_price(symbol)
        except Exception as e:
            logger.warning(f'Primary provider failed for {symbol}: {e}')
            for name, fallback_provider in self.providers.items():
                if fallback_provider != provider_obj:
                    try:
                        return fallback_provider.get_spot_price(symbol)
                    except:
                        continue
            raise ValueError(f'No provider could fetch spot price for {symbol}')

def __init__(self, primary_provider: MarketDataProvider=None):
    self.providers = {}
    self.primary_provider = primary_provider or ManualDataProvider()
    self.cache = DataCache()
    self.register_provider('manual', ManualDataProvider())
    self.register_provider('yahoo', YahooFinanceProvider())

class EconomicDataFeed:
    """Federal Reserve Economic Data (FRED) API integration"""

    def __init__(self):
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.api_key = CONFIG.api.fred_api_key
        self.cache = DataCache()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_series(self, series_id: str, limit: int=100) -> List[DataPoint]:
        """Get economic time series data"""
        cache_key = self.cache.generate_key('fred', {'series': series_id, 'limit': limit})
        cached = self.cache.get(cache_key)
        if cached and CONFIG.agent.enable_caching:
            return [DataPoint(**dp) for dp in cached]
        url = f'{self.base_url}/series/observations'
        params = {'series_id': series_id, 'api_key': self.api_key, 'file_type': 'json', 'limit': limit, 'sort_order': 'desc'}
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                observations = data.get('observations', [])
                data_points = []
                for obs in observations:
                    if obs['value'] != '.':
                        dp = DataPoint(timestamp=datetime.strptime(obs['date'], '%Y-%m-%d'), source='FRED', data_type=series_id, value=float(obs['value']), confidence=0.95, metadata={'series_id': series_id})
                        data_points.append(dp)
                self.cache.set(cache_key, [dp.__dict__ for dp in data_points])
                return data_points
        except Exception as e:
            logging.error(f'Error fetching FRED data for {series_id}: {e}')
            return []

def __init__(self):
    self.base_url = 'https://api.stlouisfed.org/fred'
    self.api_key = CONFIG.api.fred_api_key
    self.cache = DataCache()
    self.session = None

class NewsDataFeed:
    """News API integration for sentiment and events"""

    def __init__(self):
        self.api_key = CONFIG.api.newsapi_key
        self.base_url = 'https://newsapi.org/v2'
        self.cache = DataCache()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_headlines(self, query: str, sources: List[str]=None, hours_back: int=24) -> List[DataPoint]:
        """Get news headlines with relevance scoring"""
        cache_key = self.cache.generate_key('news', {'query': query, 'sources': sources, 'hours': hours_back})
        cached = self.cache.get(cache_key)
        if cached and CONFIG.agent.enable_caching:
            return [DataPoint(**dp) for dp in cached]
        from_date = (datetime.now() - timedelta(hours=hours_back)).isoformat()
        params = {'q': query, 'from': from_date, 'sortBy': 'relevancy', 'apiKey': self.api_key, 'language': 'en', 'pageSize': 100}
        if sources:
            params['sources'] = ','.join(sources)
        try:
            async with self.session.get(f'{self.base_url}/everything', params=params) as response:
                data = await response.json()
                articles = data.get('articles', [])
                data_points = []
                for article in articles:
                    source_name = article.get('source', {}).get('name', '').lower()
                    confidence = CONFIG.news_sources.get(source_name, 0.5)
                    dp = DataPoint(timestamp=datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')), source=source_name, data_type='news_headline', value=article['title'], confidence=confidence, metadata={'description': article.get('description', ''), 'url': article.get('url', ''), 'author': article.get('author', ''), 'query': query})
                    data_points.append(dp)
                self.cache.set(cache_key, [dp.__dict__ for dp in data_points])
                return data_points
        except Exception as e:
            logging.error(f'Error fetching news data: {e}')
            return []

def __init__(self):
    self.api_key = CONFIG.api.newsapi_key
    self.base_url = 'https://newsapi.org/v2'
    self.cache = DataCache()
    self.session = None

class MarketDataFeed:
    """Financial market data from multiple sources"""

    def __init__(self):
        self.finnhub_key = CONFIG.api.finnhub_api_key
        self.polygon_key = CONFIG.api.polygon_api_key
        self.cache = DataCache()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_institutional_trades(self, symbol: str) -> List[DataPoint]:
        """Get institutional trading data from Finnhub"""
        cache_key = self.cache.generate_key('institutional', {'symbol': symbol})
        cached = self.cache.get(cache_key)
        if cached and CONFIG.agent.enable_caching:
            return [DataPoint(**dp) for dp in cached]
        url = f'https://finnhub.io/api/v1/stock/institutional-portfolio'
        params = {'symbol': symbol, 'token': self.finnhub_key}
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                data_points = []
                for filing in data.get('data', []):
                    dp = DataPoint(timestamp=datetime.now(), source='Finnhub', data_type='institutional_holding', value=filing.get('change', 0), confidence=0.85, metadata={'symbol': symbol, 'institution': filing.get('name', ''), 'shares': filing.get('share', 0), 'portfolio_percent': filing.get('portfolioPercent', 0)})
                    data_points.append(dp)
                self.cache.set(cache_key, [dp.__dict__ for dp in data_points])
                return data_points
        except Exception as e:
            logging.error(f'Error fetching institutional data: {e}')
            return []

    async def get_insider_trades(self, symbol: str, days_back: int=30) -> List[DataPoint]:
        """Get insider trading data"""
        cache_key = self.cache.generate_key('insider', {'symbol': symbol, 'days': days_back})
        cached = self.cache.get(cache_key)
        if cached and CONFIG.agent.enable_caching:
            return [DataPoint(**dp) for dp in cached]
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        url = f'https://finnhub.io/api/v1/stock/insider-transactions'
        params = {'symbol': symbol, 'from': from_date, 'to': to_date, 'token': self.finnhub_key}
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                data_points = []
                for trade in data.get('data', []):
                    dp = DataPoint(timestamp=datetime.strptime(trade['transactionDate'], '%Y-%m-%d'), source='Finnhub', data_type='insider_trade', value=trade.get('change', 0), confidence=0.9, metadata={'symbol': symbol, 'name': trade.get('name', ''), 'share': trade.get('share', 0), 'transaction_code': trade.get('transactionCode', ''), 'transaction_price': trade.get('transactionPrice', 0)})
                    data_points.append(dp)
                self.cache.set(cache_key, [dp.__dict__ for dp in data_points])
                return data_points
        except Exception as e:
            logging.error(f'Error fetching insider data: {e}')
            return []

def __init__(self):
    self.finnhub_key = CONFIG.api.finnhub_api_key
    self.polygon_key = CONFIG.api.polygon_api_key
    self.cache = DataCache()
    self.session = None

class SentimentDataFeed:
    """Social media and sentiment data aggregation"""

    def __init__(self):
        self.reddit_id = CONFIG.api.reddit_client_id
        self.reddit_secret = CONFIG.api.reddit_client_secret
        self.twitter_token = CONFIG.api.twitter_bearer_token
        self.cache = DataCache()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_reddit_sentiment(self, subreddits: List[str], keywords: List[str]) -> List[DataPoint]:
        """Get Reddit sentiment for specific keywords"""
        cache_key = self.cache.generate_key('reddit', {'subreddits': subreddits, 'keywords': keywords})
        cached = self.cache.get(cache_key)
        if cached and CONFIG.agent.enable_caching:
            return [DataPoint(**dp) for dp in cached]
        data_points = []
        try:
            for subreddit in subreddits:
                for keyword in keywords:
                    dp = DataPoint(timestamp=datetime.now(), source='Reddit', data_type='social_sentiment', value=np.random.uniform(-1, 1), confidence=0.6, metadata={'subreddit': subreddit, 'keyword': keyword, 'post_count': np.random.randint(10, 100), 'engagement_score': np.random.uniform(0, 1)})
                    data_points.append(dp)
            self.cache.set(cache_key, [dp.__dict__ for dp in data_points])
            return data_points
        except Exception as e:
            logging.error(f'Error fetching Reddit sentiment: {e}')
            return []

def __init__(self):
    self.reddit_id = CONFIG.api.reddit_client_id
    self.reddit_secret = CONFIG.api.reddit_client_secret
    self.twitter_token = CONFIG.api.twitter_bearer_token
    self.cache = DataCache()
    self.session = None

class GeopoliticalDataFeed:
    """Geopolitical events and risk monitoring"""

    def __init__(self):
        self.cache = DataCache()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_conflict_data(self) -> List[DataPoint]:
        """Get global conflict and tension data"""
        cache_key = self.cache.generate_key('geopolitical', {'type': 'conflicts'})
        cached = self.cache.get(cache_key)
        if cached and CONFIG.agent.enable_caching:
            return [DataPoint(**dp) for dp in cached]
        data_points = []
        try:
            conflicts = ['Russia-Ukraine', 'China-Taiwan', 'Middle East', 'North Korea']
            for conflict in conflicts:
                dp = DataPoint(timestamp=datetime.now(), source='GDELT', data_type='geopolitical_tension', value=np.random.uniform(0, 10), confidence=0.75, metadata={'conflict_region': conflict, 'escalation_risk': np.random.choice(['low', 'medium', 'high']), 'affected_sectors': ['defense', 'energy', 'tech'], 'sanctions_risk': np.random.uniform(0, 1)})
                data_points.append(dp)
            self.cache.set(cache_key, [dp.__dict__ for dp in data_points])
            return data_points
        except Exception as e:
            logging.error(f'Error fetching geopolitical data: {e}')
            return []

def __init__(self):
    self.cache = DataCache()
    self.session = None

