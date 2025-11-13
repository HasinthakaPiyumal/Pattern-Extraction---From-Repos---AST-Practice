# Cluster 12

class CBOEDataAPI:
    """CBOE Data API wrapper for modular data fetching"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept-Terminal/1.0', 'Accept': 'application/json', 'Content-Type': 'application/json'})
        self._cache_timeout = 24 * 60 * 60
        self._cache = {}

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False
        cached_time = self._cache[cache_key].get('timestamp', 0)
        current_time = datetime.now().timestamp()
        return current_time - cached_time < self._cache_timeout

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key].get('data')
        return None

    def _set_cache_data(self, cache_key: str, data: pd.DataFrame) -> None:
        """Set cached data with timestamp"""
        self._cache[cache_key] = {'data': data, 'timestamp': datetime.now().timestamp()}

    def _make_request(self, url: str, params: Optional[Dict]=None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                return CBOEError(url, data['error'], response.status_code).to_dict()
            return {'success': True, 'data': data}
        except requests.exceptions.RequestException as e:
            return CBOEError(url, str(e), getattr(e.response, 'status_code', None)).to_dict()
        except json.JSONDecodeError as e:
            return CBOEError(url, f'JSON decode error: {str(e)}').to_dict()
        except Exception as e:
            return CBOEError(url, f'Unexpected error: {str(e)}').to_dict()

    def _parse_dataframe_response(self, data: Dict) -> pd.DataFrame:
        """Parse response into DataFrame"""
        if 'data' not in data or not isinstance(data['data'], list):
            return pd.DataFrame()
        return pd.DataFrame(data['data'])

    def get_equity_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time equity quote with implied volatility data

        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")

        Returns:
            Dict containing equity quote data
        """
        try:
            symbol_clean = symbol.replace('^', '').upper()
            if symbol_clean in TICKER_EXCEPTIONS:
                url = f'{BASE_URL}/quotes/_{symbol_clean}.json'
            else:
                url = f'{BASE_URL}/quotes/{symbol_clean}.json'
            result = self._make_request(url)
            if 'error' in result:
                return result
            quote_data = result.get('data', {})
            if not quote_data:
                return CBOEError('equity_quote', 'No data found for symbol').to_dict()
            return {'success': True, 'data': {'symbol': quote_data.get('symbol'), 'current_price': quote_data.get('current_price'), 'open': quote_data.get('open'), 'high': quote_data.get('high'), 'low': quote_data.get('low'), 'close': quote_data.get('close'), 'volume': quote_data.get('volume'), 'bid': quote_data.get('bid'), 'ask': quote_data.get('ask'), 'bid_size': quote_data.get('bid_size'), 'ask_size': quote_data.get('ask_size'), 'prev_day_close': quote_data.get('prev_day_close'), 'price_change': quote_data.get('price_change'), 'price_change_percent': quote_data.get('price_change_percent'), 'iv30': quote_data.get('iv30'), 'iv30_change': quote_data.get('iv30_change'), 'iv30_change_percent': quote_data.get('iv30_change_percent'), 'last_trade_time': quote_data.get('last_trade_time'), 'security_type': quote_data.get('security_type'), 'tick': quote_data.get('tick'), 'mkt_data_delay': quote_data.get('mkt_data_delay')}}
        except Exception as e:
            return CBOEError('equity_quote', str(e)).to_dict()

    def get_equity_historical(self, symbol: str, interval: str='1d', start_date: Optional[str]=None, end_date: Optional[str]=None, use_cache: bool=True) -> Dict[str, Any]:
        """Get historical equity price data

        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
            interval: Data interval ("1d" for daily, "1m" for 1-minute)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: Whether to use cached directory data

        Returns:
            Dict containing historical price data
        """
        try:
            symbol_clean = symbol.replace('^', '').upper()
            interval_type = 'intraday' if interval == '1m' else 'historical'
            if symbol_clean in TICKER_EXCEPTIONS:
                if interval_type == 'historical':
                    interval_type = 'intraday'
                url = f'{BASE_URL}/charts/{interval_type}/_{symbol_clean}.json'
            else:
                url = f'{BASE_URL}/charts/{interval_type}/{symbol_clean}.json'
            result = self._make_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            if 'data' not in data or not data['data']:
                return CBOEError('equity_historical', 'No historical data found').to_dict()
            historical_data = data['data']
            if interval == '1d':
                df = pd.DataFrame(historical_data)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            else:
                records = []
                for item in historical_data:
                    record = {'date': item.get('datetime'), 'open': item.get('price', {}).get('open'), 'high': item.get('price', {}).get('high'), 'low': item.get('price', {}).get('low'), 'close': item.get('price', {}).get('close'), 'volume': item.get('volume'), 'calls_volume': item.get('calls_volume'), 'puts_volume': item.get('puts_volume'), 'total_options_volume': item.get('total_options_volume')}
                    records.append(record)
                df = pd.DataFrame(records)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['date'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date) + timedelta(days=1)
                df = df[df['date'] < end_dt]
            df = df.sort_values('date').reset_index(drop=True)
            return {'success': True, 'data': {'symbol': symbol, 'interval': interval, 'data': df.to_dict('records')}}
        except Exception as e:
            return CBOEError('equity_historical', str(e)).to_dict()

    def get_index_constituents(self, symbol: str) -> Dict[str, Any]:
        """Get constituents for European indices

        Args:
            symbol: European index symbol (e.g., "BUK100P", "BEP50P")

        Returns:
            Dict containing index constituents data
        """
        try:
            symbol_clean = symbol.upper()
            if symbol_clean not in EU_INDEX_CONSTITUENTS:
                return CBOEError('index_constituents', f'Invalid European index symbol. Supported: {', '.join(EU_INDEX_CONSTITUENTS[:10])}...').to_dict()
            url = f'{EU_BASE_URL}/constituent_quotes/{symbol_clean}.json'
            result = self._make_request(url)
            if 'error' in result:
                return result
            constituents_data = result.get('data', [])
            if not constituents_data:
                return CBOEError('index_constituents', f'No constituents found for {symbol}').to_dict()
            df = pd.DataFrame(constituents_data)
            if 'price_change_percent' in df.columns:
                df['price_change_percent'] = df['price_change_percent'] / 100
            if 'exchange_id' in df.columns:
                df = df.drop(columns=['exchange_id'])
            return {'success': True, 'data': {'symbol': symbol, 'constituents': df.to_dict('records')}}
        except Exception as e:
            return CBOEError('index_constituents', str(e)).to_dict()

    def get_index_historical(self, symbol: str, interval: str='1d', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get historical index data

        Args:
            symbol: Index symbol (e.g., "SPX", "VIX", "BUK100P")
            interval: Data interval ("1d" for daily, "1m" for 1-minute)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing historical index data
        """
        try:
            symbol_clean = symbol.replace('^', '').upper()
            interval_type = 'intraday' if interval == '1m' else 'historical'
            is_european_index = symbol_clean in EU_INDEX_CONSTITUENTS
            if is_european_index:
                base_url = f'{EU_BASE_URL}/index_history/' if interval_type == 'historical' else f'{EU_BASE_URL}/intraday_chart_data/'
                url = f'{base_url}{symbol_clean}.json'
            elif symbol_clean in TICKER_EXCEPTIONS:
                url = f'{BASE_URL}/charts/{interval_type}/_{symbol_clean}.json'
            else:
                url = f'{BASE_URL}/charts/{interval_type}/{symbol_clean}.json'
            result = self._make_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            if 'data' not in data or not data['data']:
                return CBOEError('index_historical', 'No historical data found').to_dict()
            historical_data = data['data']
            if interval == '1d':
                df = pd.DataFrame(historical_data)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                if 'volume' in df.columns:
                    df = df.drop(columns='volume')
            else:
                records = []
                for item in historical_data:
                    record = {'date': item.get('datetime'), 'open': item.get('price', {}).get('open'), 'high': item.get('price', {}).get('high'), 'low': item.get('price', {}).get('low'), 'close': item.get('price', {}).get('close')}
                    records.append(record)
                df = pd.DataFrame(records)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['date'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date) + timedelta(days=1)
                df = df[df['date'] < end_dt]
            df = df.sort_values('date').reset_index(drop=True)
            return {'success': True, 'data': {'symbol': symbol, 'interval': interval, 'data': df.to_dict('records')}}
        except Exception as e:
            return CBOEError('index_historical', str(e)).to_dict()

    def get_index_snapshots(self, region: str='us') -> Dict[str, Any]:
        """Get snapshots for all indices in a region

        Args:
            region: Region - "us" for US indices, "eu" for European indices

        Returns:
            Dict containing index snapshots data
        """
        try:
            region = region.lower()
            if region == 'us':
                url = US_INDICES_URL
            elif region == 'eu':
                url = EU_INDICES_URL
            else:
                return CBOEError('index_snapshots', f"Invalid region: {region}. Use 'us' or 'eu'").to_dict()
            result = self._make_request(url)
            if 'error' in result:
                return result
            indices_data = result.get('data', [])
            if not indices_data:
                return CBOEError('index_snapshots', f'No indices data found for region: {region}').to_dict()
            df = pd.DataFrame(indices_data)
            percent_cols = ['price_change_percent', 'iv30', 'iv30_change', 'iv30_change_percent']
            for col in percent_cols:
                if col in df.columns:
                    df[col] = round(df[col] / 100, 6)
            df = df.replace(0, None).replace('', None)
            df = df.dropna(how='all', axis=1)
            df = df.fillna('N/A').replace('N/A', None)
            drop_cols = ['exchange_id', 'seqno', 'index', 'security_type', 'ask_size', 'bid_size']
            for col in drop_cols:
                if col in df.columns:
                    df = df.drop(columns=col)
            return {'success': True, 'data': {'region': region, 'indices': df.to_dict('records')}}
        except Exception as e:
            return CBOEError('index_snapshots', str(e)).to_dict()

    def get_futures_curve(self, symbol: str='VX_EOD', date: Optional[str]=None) -> Dict[str, Any]:
        """Get VIX futures curve data

        Args:
            symbol: VIX futures symbol ("VX_EOD" or "VX_AM")
            date: Specific date in YYYY-MM-DD format (optional)

        Returns:
            Dict containing futures curve data
        """
        try:
            symbol = symbol.upper()
            if symbol not in VIX_SYMBOLS:
                symbol = 'VX_EOD'
            vx_type = 'am' if symbol == 'VX_AM' else 'eod'
            if date:
                url = f'https://cdn.cboe.com/api/global/futures/vx_{vx_type}_curve/{date}.json'
            else:
                url = f'https://cdn.cboe.com/api/global/futures/vx_{vx_type}_curve.json'
            result = self._make_request(url)
            if 'error' in result:
                return result
            futures_data = result.get('data', [])
            if not futures_data:
                return CBOEError('futures_curve', 'No futures curve data found').to_dict()
            df = pd.DataFrame(futures_data)
            return {'success': True, 'data': {'symbol': symbol, 'date': date or 'current', 'futures': df.to_dict('records')}}
        except Exception as e:
            return CBOEError('futures_curve', str(e)).to_dict()

    def get_options_chains(self, symbol: str) -> Dict[str, Any]:
        """Get options chains data for a symbol

        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")

        Returns:
            Dict containing options chains data with metadata
        """
        try:
            symbol_clean = symbol.replace('^', '').upper()
            if symbol_clean in TICKER_EXCEPTIONS:
                url = f'{BASE_URL}/options/_{symbol_clean}.json'
            else:
                url = f'{BASE_URL}/options/{symbol_clean}.json'
            result = self._make_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            if not data:
                return CBOEError('options_chains', 'No options data found for symbol').to_dict()
            metadata = {'symbol': data.get('symbol'), 'security_type': data.get('security_type'), 'bid': data.get('bid'), 'bid_size': data.get('bid_size'), 'ask': data.get('ask'), 'ask_size': data.get('ask_size'), 'open': data.get('open'), 'high': data.get('high'), 'low': data.get('low'), 'close': data.get('close'), 'volume': data.get('volume'), 'current_price': data.get('current_price'), 'prev_close': data.get('prev_day_close'), 'change': data.get('price_change'), 'change_percent': data.get('price_change_percent'), 'iv30': data.get('iv30'), 'iv30_change': data.get('iv30_change'), 'iv30_change_percent': data.get('iv30_change_percent'), 'last_trade_time': data.get('last_trade_time')}
            options = data.get('options', [])
            if not options:
                return CBOEError('options_chains', 'No options chains found').to_dict()
            options_df = pd.DataFrame(options)

            def parse_option_symbol(option_symbol):
                """Parse option symbol to extract components"""
                import re
                pattern = '^(?P<ticker>\\D*)(?P<expiration>\\d*)(?P<option_type>\\D*)(?P<strike>\\d*)$'
                match = re.match(pattern, option_symbol)
                if match:
                    ticker = match.group('ticker')
                    expiration = match.group('expiration')
                    option_type = match.group('option_type').replace('C', 'call').replace('P', 'put')
                    strike = match.group('strike').lstrip('0')
                    if strike:
                        strike = float(strike) / 1000
                    return (ticker, expiration, option_type, strike)
                return (None, None, None, None)
            parsed_data = []
            for _, row in options_df.iterrows():
                ticker, expiration, option_type, strike = parse_option_symbol(row['option'])
                if ticker and expiration and option_type and strike:
                    try:
                        exp_date = pd.to_datetime(expiration, format='%y%m%d')
                        dte = (exp_date - datetime.now()).days + 1
                    except:
                        dte = None
                    option_data = {'contract_symbol': row['option'], 'underlying_symbol': ticker, 'expiration': expiration, 'strike': strike, 'option_type': option_type, 'dte': dte, 'last': row.get('last'), 'bid': row.get('bid'), 'ask': row.get('ask'), 'mid': row.get('mid'), 'change': row.get('change'), 'change_percent': row.get('percent_change') / 100 if row.get('percent_change') else None, 'volume': row.get('volume'), 'open_interest': row.get('open_interest'), 'implied_volatility': row.get('iv'), 'theoretical_price': row.get('theo'), 'delta': row.get('delta'), 'gamma': row.get('gamma'), 'theta': row.get('theta'), 'vega': row.get('vega'), 'prev_close': row.get('prev_day_close'), 'last_trade_time': row.get('last_trade_time')}
                    parsed_data.append(option_data)
            if not parsed_data:
                return CBOEError('options_chains', 'Failed to parse options data').to_dict()
            options_parsed_df = pd.DataFrame(parsed_data)
            return {'success': True, 'data': {'metadata': {k: v for k, v in metadata.items() if v is not None}, 'options': options_parsed_df.to_dict('records')}}
        except Exception as e:
            return CBOEError('options_chains', str(e)).to_dict()

    def search_equities(self, query: str, is_symbol: bool=False) -> Dict[str, Any]:
        """Search for equities in CBOE directory

        Args:
            query: Search query (symbol or company name)
            is_symbol: If True, search only by symbol

        Returns:
            Dict containing search results
        """
        try:
            cache_key = 'company_directory'
            symbols_df = self._get_cached_data(cache_key)
            if symbols_df is None:
                url = f'{BASE_URL}/directory/symbol_search.json'
                result = self._make_request(url)
                if 'error' in result:
                    return result
                data = result.get('data', [])
                symbols_df = pd.DataFrame(data)
                self._set_cache_data(cache_key, symbols_df)
            if symbols_df.empty:
                return CBOEError('equity_search', 'Company directory not available').to_dict()
            symbols_df = symbols_df.reset_index()
            target = 'name' if not is_symbol else 'symbol'
            mask = symbols_df[target].str.contains(query, case=False, na=False)
            results_df = symbols_df[mask]
            return {'success': True, 'data': {'query': query, 'results': results_df.to_dict('records')}}
        except Exception as e:
            return CBOEError('equity_search', str(e)).to_dict()

    def search_indices(self, query: str, is_symbol: bool=False) -> Dict[str, Any]:
        """Search for indices in CBOE directory

        Args:
            query: Search query (symbol or index name)
            is_symbol: If True, search only by symbol

        Returns:
            Dict containing search results
        """
        try:
            cache_key = 'index_directory'
            indices_df = self._get_cached_data(cache_key)
            if indices_df is None:
                url = f'{BASE_URL}/directory/index_search.json'
                result = self._make_request(url)
                if 'error' in result:
                    return result
                data = result.get('data', [])
                indices_df = pd.DataFrame(data)
                if 'source' in indices_df.columns:
                    indices_df = indices_df.drop(columns=['source'])
                self._set_cache_data(cache_key, indices_df)
            if indices_df.empty:
                return CBOEError('index_search', 'Index directory not available').to_dict()
            if is_symbol:
                mask = indices_df['index_symbol'].str.contains(query, case=False, na=False)
            else:
                mask = indices_df['name'].str.contains(query, case=False, na=False) | indices_df['index_symbol'].str.contains(query, case=False, na=False) | indices_df['description'].str.contains(query, case=False, na=False)
            results_df = indices_df[mask]
            return {'success': True, 'data': {'query': query, 'results': results_df.to_dict('records')}}
        except Exception as e:
            return CBOEError('index_search', str(e)).to_dict()

    def get_available_indices(self) -> Dict[str, Any]:
        """Get list of all available indices

        Returns:
            Dict containing available indices
        """
        try:
            cache_key = 'index_directory'
            indices_df = self._get_cached_data(cache_key)
            if indices_df is None:
                url = f'{BASE_URL}/directory/index_search.json'
                result = self._make_request(url)
                if 'error' in result:
                    return result
                data = result.get('data', [])
                indices_df = pd.DataFrame(data)
                self._set_cache_data(cache_key, indices_df)
            if indices_df.empty:
                return CBOEError('available_indices', 'Index directory not available').to_dict()
            return {'success': True, 'data': {'indices': indices_df.to_dict('records')}}
        except Exception as e:
            return CBOEError('available_indices', str(e)).to_dict()

def parse_option_symbol(option_symbol):
    """Parse option symbol to extract components"""
    import re
    pattern = '^(?P<ticker>\\D*)(?P<expiration>\\d*)(?P<option_type>\\D*)(?P<strike>\\d*)$'
    match = re.match(pattern, option_symbol)
    if match:
        ticker = match.group('ticker')
        expiration = match.group('expiration')
        option_type = match.group('option_type').replace('C', 'call').replace('P', 'put')
        strike = match.group('strike').lstrip('0')
        if strike:
            strike = float(strike) / 1000
        return (ticker, expiration, option_type, strike)
    return (None, None, None, None)

def main():
    """Main function for CLI interface"""
    if len(sys.argv) < 2:
        print(json.dumps(CBOEError('cli', 'Usage: python cboe_data.py <command> [args...]').to_dict()))
        sys.exit(1)
    command = sys.argv[1]
    api = CBOEDataAPI()
    command_map = {'equity_quote': lambda: api.get_equity_quote(sys.argv[2] if len(sys.argv) > 2 else ''), 'equity_historical': lambda: api.get_equity_historical(sys.argv[2] if len(sys.argv) > 2 else '', sys.argv[3] if len(sys.argv) > 3 else '1d', sys.argv[4] if len(sys.argv) > 4 else None, sys.argv[5] if len(sys.argv) > 5 else None), 'equity_search': lambda: api.search_equities(sys.argv[2] if len(sys.argv) > 2 else '', sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False), 'index_constituents': lambda: api.get_index_constituents(sys.argv[2] if len(sys.argv) > 2 else ''), 'index_historical': lambda: api.get_index_historical(sys.argv[2] if len(sys.argv) > 2 else '', sys.argv[3] if len(sys.argv) > 3 else '1d', sys.argv[4] if len(sys.argv) > 4 else None, sys.argv[5] if len(sys.argv) > 5 else None), 'index_search': lambda: api.search_indices(sys.argv[2] if len(sys.argv) > 2 else '', sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False), 'index_snapshots': lambda: api.get_index_snapshots(sys.argv[2] if len(sys.argv) > 2 else 'us'), 'futures_curve': lambda: api.get_futures_curve(sys.argv[2] if len(sys.argv) > 2 else 'VX_EOD', sys.argv[3] if len(sys.argv) > 3 else None), 'options_chains': lambda: api.get_options_chains(sys.argv[2] if len(sys.argv) > 2 else ''), 'available_indices': lambda: api.get_available_indices()}
    if command not in command_map:
        print(json.dumps(CBOEError('cli', f'Unknown command: {command}').to_dict()))
        sys.exit(1)
    try:
        result = command_map[command]()
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps(CBOEError(command, str(e)).to_dict(), indent=2))
        sys.exit(1)

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python polygon_data.py <command> <args>', 'commands': ['tickers --ticker=SYMBOL --type=TYPE --market=MARKET --exchange=EXCHANGE --cusip=CUSIP --cik=CIK --date=DATE --search=SEARCH --active=true/false --ticker-gte=SYMBOL --ticker-gt=SYMBOL --ticker-lte=SYMBOL --ticker-lt=SYMBOL --order=ORDER --limit=NUMBER --sort=SORT', 'ticker-details --ticker=SYMBOL --date=DATE', 'ticker-types --asset-class=ASSET_CLASS --locale=LOCALE', 'related-tickers --ticker=SYMBOL', 'news --ticker=SYMBOL --published-utc=DATE --limit=NUMBER --sort=SORT --order=ORDER', 'ipos --ticker=SYMBOL --ipo-status=STATUS --listing-date=DATE --limit=NUMBER --sort=SORT --order=ORDER', 'splits --ticker=SYMBOL --execution-date=DATE --reverse-split=true/false --limit=NUMBER --sort=SORT --order=ORDER', 'dividends --ticker=SYMBOL --ex-dividend-date=DATE --frequency=NUMBER --dividend-type=TYPE --cash-amount=AMOUNT --limit=NUMBER --sort=SORT --order=ORDER', 'ticker-events --identifier=IDENTIFIER --types=TYPES', 'exchanges --asset-class=ASSET_CLASS --locale=LOCALE', 'market-holidays', 'market-status', 'condition-codes --asset-class=ASSET_CLASS --data-type=TYPE --id=ID --sip=SIP --limit=NUMBER --sort=SORT --order=ORDER', 'ticker-snapshot --ticker=SYMBOL', 'market-snapshot --tickers=SYMBOL1,SYMBOL2 --include-otc=true/false', 'unified-snapshot --ticker=SYMBOL --type=TYPE --ticker-any-of=SYMBOL1,SYMBOL2 --limit=NUMBER --sort=SORT --order=ORDER', 'top-movers --direction=gainers/losers --include-otc=true/false', 'trades --ticker=SYMBOL --timestamp=TIMESTAMP --timestamp-gte=TIMESTAMP --timestamp-lte=TIMESTAMP --limit=NUMBER --sort=SORT --order=ORDER', 'last-trade --ticker=SYMBOL', 'quotes --ticker=SYMBOL --timestamp=TIMESTAMP --timestamp-gte=TIMESTAMP --timestamp-lte=TIMESTAMP --limit=NUMBER --sort=SORT --order=ORDER', 'last-quote --ticker=SYMBOL', 'sma --ticker=SYMBOL --window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER', 'ema --ticker=SYMBOL --window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER', 'macd --ticker=SYMBOL --short-window=NUMBER --long-window=NUMBER --signal-window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER', 'rsi --ticker=SYMBOL --window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER', 'balance-sheets --cik=CIK --tickers=SYMBOL --period-end=DATE --filing-date=DATE --fiscal-year=YEAR --fiscal-quarter=QUARTER --timeframe=TIMEFRAME --limit=NUMBER --sort=SORT', 'cash-flow-statements --cik=CIK --tickers=SYMBOL --period-end=DATE --filing-date=DATE --fiscal-year=YEAR --fiscal-quarter=QUARTER --timeframe=TIMEFRAME --limit=NUMBER --sort=SORT', 'income-statements --cik=CIK --tickers=SYMBOL --period-end=DATE --filing-date=DATE --fiscal-year=YEAR --fiscal-quarter=QUARTER --timeframe=TIMEFRAME --limit=NUMBER --sort=SORT', 'ratios --ticker=SYMBOL --timeframe=TIMEFRAME --period-type=TYPE --period=PERIOD --fy-of=YEAR --q-of=QUARTER --as-of-date=DATE --include-sources=true/false --period-of-report-date=DATE --date-field=FIELD --splits=true/false --field-format=FORMAT --precision=NUMBER --locale=LOCALE --sic=CODE --cik=CIK --unit-multiplier=MULTIPLIER --period-of-report-label=LABEL --include-qt-fact=true/false --search-by-column-values=VALUES --period-of-report-day=DAY --quarterly-report-day=DAY --payout-ratio-gte=VALUE --payout-ratio-lte=VALUE --payout-ratio-gt=VALUE --payout-ratio-lt=VALUE --payout-ratio-eq=VALUE --dividend-yield-gte=VALUE --dividend-yield-lte=VALUE --dividend-yield-gt=VALUE --dividend-yield-lt=VALUE --dividend-yield-eq=VALUE --dividend-per-share-gte=VALUE --dividend-per-share-lte=VALUE --dividend-per-share-gt=VALUE --dividend-per-share-lt=VALUE --dividend-per-share-eq=VALUE --dividend-yield-ttm-gte=VALUE --dividend-yield-ttm-lte=VALUE --dividend-yield-ttm-gt=VALUE --dividend-yield-ttm-lt=VALUE --dividend-yield-ttm-eq=VALUE --book-value-per-share-gte=VALUE --book-value-per-share-lte=VALUE --book-value-per-share-gt=VALUE --book-value-per-share-lt=VALUE --book-value-per-share-eq=VALUE --book-value-per-share-ttm-gte=VALUE --book-value-per-share-ttm-lte=VALUE --book-value-per-share-ttm-gt=VALUE --book-value-per-share-ttm-lt=VALUE --book-value-per-share-ttm-eq=VALUE --book-value-per-share-growth-ttm-pct-gte=VALUE --book-value-per-share-growth-ttm-pct-lte=VALUE --book-value-per-share-growth-ttm-pct-gt=VALUE --book-value-per-share-growth-ttm-pct-lt=VALUE --book-value-per-share-growth-ttm-pct-eq=VALUE --diluted-eps-growth-ttm-pct-gte=VALUE --diluted-eps-growth-ttm-pct-lte=VALUE --diluted-eps-growth-ttm-pct-gt=VALUE --diluted-eps-growth-ttm-pct-lt=VALUE --diluted-eps-growth-ttm-pct-eq=VALUE --basic-earnings-per-share-gte=VALUE --basic-earnings-per-share-lte=VALUE --basic-earnings-per-share-gt=VALUE --basic-earnings-per-share-lt=VALUE --basic-earnings-per-share-eq=VALUE --basic-eps-ttm-gte=VALUE --basic-eps-ttm-lte=VALUE --basic-eps-ttm-gt=VALUE --basic-eps-ttm-lt=VALUE --basic-eps-ttm-eq=VALUE --basic-average-shares-gte=VALUE --basic-average-shares-lte=VALUE --basic-average-shares-gt=VALUE --basic-average-shares-lt=VALUE --basic-average-shares-eq=VALUE --diluted-earnings-per-share-gte=VALUE --diluted-earnings-per-share-lte=VALUE --diluted-earnings-per-share-gt=VALUE --diluted-earnings-per-share-lt=VALUE --diluted-earnings-per-share-eq=VALUE --diluted-eps-ttm-gte=VALUE --diluted-eps-ttm-lte=VALUE --diluted-eps-ttm-gt=VALUE --diluted-eps-ttm-lt=VALUE --diluted-eps-ttm-eq=VALUE --diluted-average-shares-gte=VALUE --diluted-average-shares-lte=VALUE --diluted-average-shares-gt=VALUE --diluted-average-shares-lt=VALUE --diluted-average-shares-eq=VALUE --weighted-average-shares-gte=VALUE --weighted-average-shares-lte=VALUE --weighted-average-shares-gt=VALUE --weighted-average-shares-lt=VALUE --weighted-average-shares-eq=VALUE --market-capitalization-gte=VALUE --market-capitalization-lte=VALUE --market-capitalization-gt=VALUE --market-capitalization-lt=VALUE --market-capitalization-eq=VALUE --ev-gte=VALUE --ev-lte=VALUE --ev-gt=VALUE --ev-lt=VALUE --ev-eq=VALUE --pe-basic-gte=VALUE --pe-basic-lte=VALUE --pe-basic-gt=VALUE --pe-basic-lt=VALUE --pe-basic-eq=VALUE --pe-basic-ttm-gte=VALUE --pe-basic-ttm-lte=VALUE --pe-basic-ttm-gt=VALUE --pe-basic-ttm-lt=VALUE --pe-basic-ttm-eq=VALUE --pe-diluted-gte=VALUE --pe-diluted-lte=VALUE --pe-diluted-gt=VALUE --pe-diluted-lt=VALUE --pe-diluted-eq=VALUE --pe-diluted-ttm-gte=VALUE --pe-diluted-ttm-lte=VALUE --pe-diluted-ttm-gt=VALUE --pe-diluted-ttm-lt=VALUE --pe-diluted-ttm-eq=VALUE --pb-ttm-gte=VALUE --pb-ttm-lte=VALUE --pb-ttm-gt=VALUE --pb-ttm-lt=VALUE --pb-ttm-eq=VALUE --roe-ttm-gte=VALUE --roe-ttm-lte=VALUE --roe-ttm-gt=VALUE --roe-ttm-lt=VALUE --roe-ttm-eq=VALUE --roa-ttm-gte=VALUE --roa-ttm-lte=VALUE --roa-ttm-gt=VALUE --roa-ttm-lt=VALUE --roa-ttm-eq=VALUE --roic-ttm-gte=VALUE --roic-ttm-lte=VALUE --roic-ttm-gt=VALUE --roic-ttm-lt=VALUE --roic-ttm-eq=VALUE --profit-margin-ttm-gte=VALUE --profit-margin-ttm-lte=VALUE --profit-margin-ttm-gt=VALUE --profit-margin-ttm-lt=VALUE --profit-margin-ttm-eq=VALUE --gross-margin-ttm-gte=VALUE --gross-margin-ttm-lte=VALUE --gross-margin-ttm-gt=VALUE --gross-margin-ttm-lt=VALUE --gross-margin-ttm-eq=VALUE --sga-to-revenue-ttm-gte=VALUE --sga-to-revenue-ttm-lte=VALUE --sga-to-revenue-ttm-gt=VALUE --sga-to-revenue-ttm-lt=VALUE --sga-to-revenue-ttm-eq=VALUE --rd-to-revenue-ttm-gte=VALUE --rd-to-revenue-ttm-lte=VALUE --rd-to-revenue-ttm-gt=VALUE --rd-to-revenue-ttm-lt=VALUE --rd-to-revenue-ttm-eq=VALUE --r-and-d-to-revenue-ttm-gte=VALUE --r-and-d-to-revenue-ttm-lte=VALUE --r-and-d-to-revenue-ttm-gt=VALUE --r-and-d-to-revenue-ttm-lt=VALUE --r-and-d-to-revenue-ttm-eq=VALUE --effective-tax-rate-ttm-gte=VALUE --effective-tax-rate-ttm-lte=VALUE --effective-tax-rate-ttm-gt=VALUE --effective-tax-rate-ttm-lt=VALUE --effective-tax-rate-ttm-eq=VALUE --return-on-tangible-assets-ttm-gte=VALUE --return-on-tangible-assets-ttm-lte=VALUE --return-on-tangible-assets-ttm-gt=VALUE --return-on-tangible-assets-ttm-lt=VALUE --return-on-tangible-assets-ttm-eq=VALUE --interest-coverage-ttm-gte=VALUE --interest-coverage-ttm-lte=VALUE --interest-coverage-ttm-gt=VALUE --interest-coverage-ttm-lt=VALUE --interest-coverage-ttm-eq=VALUE --current-ratio-gte=VALUE --current-ratio-lte=VALUE --current-ratio-gt=VALUE --current-ratio-lt=VALUE --current-ratio-eq=VALUE --quick-ratio-gte=VALUE --quick-ratio-lte=VALUE --quick-ratio-gt=VALUE --quick-ratio-lt=VALUE --quick-ratio-eq=VALUE --cash-ratio-gte=VALUE --cash-ratio-lte=VALUE --cash-ratio-gt=VALUE --cash-ratio-lt=VALUE --cash-ratio-eq=VALUE --days-of-sales-outstanding-gte=VALUE --days-of-sales-outstanding-lte=VALUE --days-of-sales-outstanding-gt=VALUE --days-of-sales-outstanding-lt=VALUE --days-of-sales-outstanding-eq=VALUE --days-of-inventory-on-hand-gte=VALUE --days-of-inventory-on-hand-lte=VALUE --days-of-inventory-on-hand-gt=VALUE --days-of-inventory-on-hand-lt=VALUE --days-of-inventory-on-hand-eq=VALUE --ebitda-margin-ttm-gte=VALUE --ebitda-margin-ttm-lte=VALUE --ebitda-margin-ttm-gt=VALUE --ebitda-margin-ttm-lt=VALUE --ebitda-margin-ttm-eq=VALUE --ebitda-to-interest-coverage-ttm-gte=VALUE --ebitda-to-interest-coverage-ttm-lte=VALUE --ebitda-to-interest-coverage-ttm-gt=VALUE --ebitda-to-interest-coverage-ttm-lt=VALUE --ebitda-to-interest-coverage-ttm-eq=VALUE --ebitda-to-revenue-ttm-gte=VALUE --ebitda-to-revenue-ttm-lte=VALUE --ebitda-to-revenue-ttm-gt=VALUE --ebitda-to-revenue-ttm-lt=VALUE --ebitda-to-revenue-ttm-eq=VALUE --ev-to-ebitda-ttm-gte=VALUE --ev-to-ebitda-ttm-lte=VALUE --ev-to-ebitda-ttm-gt=VALUE --ev-to-ebitda-ttm-lt=VALUE --ev-to-ebitda-ttm-eq=VALUE --ev-to-operating-cash-flow-ttm-gte=VALUE --ev-to-operating-cash-flow-ttm-lte=VALUE --ev-to-operating-cash-flow-ttm-gt=VALUE --ev-to-operating-cash-flow-ttm-lt=VALUE --ev-to-operating-cash-flow-ttm-eq=VALUE --ev-to-sales-ttm-gte=VALUE --ev-to-sales-ttm-lte=VALUE --ev-to-sales-ttm-gt=VALUE --ev-to-sales-ttm-lt=VALUE --ev-to-sales-ttm-eq=VALUE --ps-ttm-gte=VALUE --ps-ttm-lte=VALUE --ps-ttm-gt=VALUE --ps-ttm-lt=VALUE --ps-ttm-eq=VALUE --price-to-book-ttm-gte=VALUE --price-to-book-ttm-lte=VALUE --price-to-book-ttm-gt=VALUE --price-to-book-ttm-lt=VALUE --price-to-book-ttm-eq=VALUE --price-to-tangible-book-ttm-gte=VALUE --price-to-tangible-book-ttm-lte=VALUE --price-to-tangible-book-ttm-gt=VALUE --price-to-tangible-book-ttm-lt=VALUE --price-to-tangible-book-ttm-eq=VALUE --price-to-sales-ttm-gte=VALUE --price-to-sales-ttm-lte=VALUE --price-to-sales-ttm-gt=VALUE --price-to-sales-ttm-lt=VALUE --price-to-sales-ttm-eq=VALUE --fcfe-yield-ttm-gte=VALUE --fcfe-yield-ttm-lte=VALUE --fcfe-yield-ttm-gt=VALUE --fcfe-yield-ttm-lt=VALUE --fcfe-yield-ttm-eq=VALUE --fcff-yield-ttm-gte=VALUE --fcff-yield-ttm-lte=VALUE --fcff-yield-ttm-gt=VALUE --fcff-yield-ttm-lt=VALUE --fcff-yield-ttm-eq=VALUE --dividend-yield-basic-ttm-gte=VALUE --dividend-yield-basic-ttm-lte=VALUE --dividend-yield-basic-ttm-gt=VALUE --dividend-yield-basic-ttm-lt=VALUE --dividend-yield-basic-ttm-eq=VALUE --dividend-yield-ttm-gte=VALUE --dividend-yield-ttm-lte=VALUE --dividend-yield-ttm-gt=VALUE --dividend-yield-ttm-lt=VALUE --dividend-yield-ttm-eq=VALUE --total-debt-to-capitalization-gte=VALUE --total-debt-to-capitalization-lte=VALUE --total-debt-to-capitalization-gt=VALUE --total-debt-to-capitalization-lt=VALUE --total-debt-to-capitalization-eq=VALUE --total-debt-to-equity-gte=VALUE --total-debt-to-equity-lte=VALUE --total-debt-to-equity-gt=VALUE --total-debt-to-equity-lt=VALUE --total-debt-to-equity-eq=VALUE --long-term-debt-to-equity-gte=VALUE --long-term-debt-to-equity-lte=VALUE --long-term-debt-to-equity-gt=VALUE --long-term-debt-to-equity-lt=VALUE --long-term-debt-to-equity-eq=VALUE --short-term-debt-to-equity-gte=VALUE --short-term-debt-to-equity-lte=VALUE --short-term-debt-to-equity-gt=VALUE --short-term-debt-to-equity-lt=VALUE --short-term-debt-to-equity-eq=VALUE --long-term-debt-to-total-assets-gte=VALUE --long-term-debt-to-total-assets-lte=VALUE --long-term-debt-to-total-assets-gt=VALUE --long-term-debt-to-total-assets-lt=VALUE --long-term-debt-to-total-assets-eq=VALUE --total-assets-to-total-equity-gte=VALUE --total-assets-to-total-equity-lte=VALUE --total-assets-to-total-equity-gt=VALUE --total-assets-to-total-equity-lt=VALUE --total-assets-to-total-equity-eq=VALUE --debt-to-assets-gte=VALUE --debt-to-assets-lte=VALUE --debt-to-assets-gt=VALUE --debt-to-assets-lt=VALUE --debt-to-assets-eq=VALUE --book-yield-ttm-gte=VALUE --book-yield-ttm-lte=VALUE --book-yield-ttm-gt=VALUE --book-yield-ttm-lt=VALUE --book-yield-ttm-eq=VALUE --dividend-payout-ratio-ttm-gte=VALUE --dividend-payout-ratio-ttm-lte=VALUE --dividend-payout-ratio-ttm-gt=VALUE --dividend-payout-ratio-ttm-lt=VALUE --dividend-payout-ratio-ttm-eq=VALUE --free-cash-flow-yield-ttm-gte=VALUE --free-cash-flow-yield-ttm-lte=VALUE --free-cash-flow-yield-ttm-gt=VALUE --free-cash-flow-yield-ttm-lt=VALUE --free-cash-flow-yield-ttm-eq=VALUE --graham-number-ttm-gte=VALUE --graham-number-ttm-lte=VALUE --graham-number-ttm-gt=VALUE --graham-number-ttm-lt=VALUE --graham-number-ttm-eq=VALUE --graham-number-ttm-to-net-current-asset-value-ttm-gte=VALUE --graham-number-ttm-to-net-current-asset-value-ttm-lte=VALUE --graham-number-ttm-to-net-current-asset-value-ttm-gt=VALUE --graham-number-ttm-to-net-current-asset-value-ttm-lt=VALUE --graham-number-ttm-to-net-current-asset-value-ttm-eq=VALUE', 'short-interest --ticker=SYMBOL --ticker-any-of=SYMBOLS --ticker-gt=SYMBOL --ticker-gte=SYMBOL --ticker-lt=SYMBOL --ticker-lte=SYMBOL --days-to-cover=NUMBER --days-to-cover-any-of=VALUES --days-to-cover-gt=NUMBER --days-to-cover-gte=NUMBER --days-to-cover-lt=NUMBER --days-to-cover-lte=NUMBER --settlement-date=DATE --settlement-date-any-of=DATES --settlement-date-gt=DATE --settlement-date-gte=DATE --settlement-date-lt=DATE --settlement-date-lte=DATE --avg-daily-volume=NUMBER --avg-daily-volume-any-of=VALUES --avg-daily-volume-gt=NUMBER --avg-daily-volume-gte=NUMBER --avg-daily-volume-lt=NUMBER --avg-daily-volume-lte=NUMBER --limit=NUMBER --sort=SORT', 'short-volume --ticker=SYMBOL --ticker-any-of=SYMBOLS --ticker-gt=SYMBOL --ticker-gte=SYMBOL --ticker-lt=SYMBOL --ticker-lte=SYMBOL --date=DATE --date-any-of=DATES --date-gt=DATE --date-gte=DATE --date-lt=DATE --date-lte=DATE --short-volume-ratio=NUMBER --short-volume-ratio-any-of=VALUES --short-volume-ratio-gt=NUMBER --short-volume-ratio-gte=NUMBER --short-volume-ratio-lt=NUMBER --short-volume-ratio-lte=NUMBER --total-volume=NUMBER --total-volume-any-of=VALUES --total-volume-gt=NUMBER --total-volume-gte=NUMBER --total-volume-lt=NUMBER --total-volume-lte=NUMBER --limit=NUMBER --sort=SORT', 'Examples:', '  python polygon_data.py tickers --ticker=AAPL --type=CS --market=stocks --exchange=XNYS --limit=100 --active=true', '  python polygon_data.py ticker-details --ticker=AAPL --date=2021-04-25', '  python polygon_data.py ticker-types --asset-class=stocks --locale=us', '  python polygon_data.py related-tickers --ticker=AAPL', '  python polygon_data.py news --ticker=AAPL --limit=10 --sort=published_utc --order=descending', '  python polygon_data.py ipos --ipo-status=pending --limit=20 --sort=listing_date', '  python polygon_data.py splits --ticker=AAPL --limit=10 --sort=execution_date', '  python polygon_data.py dividends --ticker=AAPL --frequency=4 --limit=20 --sort=pay_date', '  python polygon_data.py ticker-events --identifier=META --types=ticker_change', '  python polygon_data.py exchanges --asset-class=stocks --locale=us', '  python polygon_data.py market-holidays', '  python polygon_data.py market-status', '  python polygon_data.py condition-codes --asset-class=stocks --data-type=trade --limit=50', '  python polygon_data.py ticker-snapshot --ticker=AAPL', '  python polygon_data.py market-snapshot --tickers=AAPL,TSLA,GOOG --include-otc=false', '  python polygon_data.py unified-snapshot --type=stocks --limit=50', '  python polygon_data.py unified-snapshot --ticker-any-of=AAPL,TSLA,BTC-USD --limit=10', '  python polygon_data.py top-movers --direction=gainers --include-otc=false', '  python polygon_data.py top-movers --direction=losers --include-otc=true', '  python polygon_data.py trades --ticker=AAPL --timestamp-gte=2021-04-25 --timestamp-lte=2021-04-25 --limit=1000', '  python polygon_data.py trades --ticker=AAPL --timestamp=1619337600000000000 --limit=500', '  python polygon_data.py last-trade --ticker=AAPL', '  python polygon_data.py quotes --ticker=AAPL --timestamp-gte=2021-04-25 --timestamp-lte=2021-04-25 --limit=1000', '  python polygon_data.py last-quote --ticker=AAPL', '  python polygon_data.py sma --ticker=AAPL --window=20 --timespan=day --series-type=close --limit=50', '  python polygon_data.py ema --ticker=AAPL --window=12 --timespan=day --series-type=close --expand-underlying=true --limit=30', '  python polygon_data.py macd --ticker=AAPL --short-window=12 --long-window=26 --signal-window=9 --timespan=day --series-type=close --expand-underlying=true --limit=50', '  python polygon_data.py rsi --ticker=AAPL --window=14 --timespan=day --series-type=close --expand-underlying=true --limit=50', '  python polygon_data.py balance-sheets --tickers=AAPL --timeframe=quarterly --limit=10 --sort=period_end.desc', '  python polygon_data.py balance-sheets --cik=0000320193 --fiscal-year=2024 --timeframe=annual --limit=5', '  python polygon_data.py balance-sheets --tickers=AAPL,MSFT,GOOGL --timeframe=quarterly --fiscal-year=2024 --limit=30', '  python polygon_data.py cash-flow-statements --tickers=AAPL --timeframe=quarterly --limit=10 --sort=period_end.desc', '  python polygon_data.py cash-flow-statements --cik=0000320193 --fiscal-year=2024 --timeframe=trailing_twelve_months --limit=5', '  python polygon_data.py cash-flow-statements --tickers=AAPL,MSFT,GOOGL --timeframe=annual --fiscal-year-gte=2023 --limit=15', '  python polygon_data.py income-statements --tickers=AAPL --timeframe=quarterly --limit=10 --sort=period_end.desc', '  python polygon_data.py income-statements --cik=0000320193 --fiscal-year=2024 --timeframe=trailing_twelve_months --limit=5', '  python polygon_data.py income-statements --tickers=AAPL,MSFT,GOOGL --timeframe=annual --fiscal-year-gte=2023 --limit=15', '  python polygon_data.py ratios --ticker=AAPL --timeframe=quarterly --limit=10 --sort=period_end.desc', '  python polygon_data.py ratios --ticker=AAPL --timeframe=trailing_twelve_months --pe-basic-ttm-gte=10 --roe-ttm-gte=0.15 --current-ratio-gte=1.5', '  python polygon_data.py ratios --ticker=AAPL --timeframe=quarterly --pb-ttm-lte=3 --ps-ttm-lte=5 --debt-to-equity-lte=1.0 --roe-ttm-gte=0.10', '  python polygon_data.py ratios --ticker=AAPL --timeframe=annual --market-capitalization-gte=1000000000 --ev-to-ebitda-ttm-lte=15 --roic-ttm-gte=0.12', '  python polygon_data.py ratios --ticker=AAPL --timeframe=quarterly --dividend-yield-ttm-gte=0.02 --profit-margin-ttm-gte=0.10 --quick-ratio-gte=1.0', '  python polygon_data.py ratios --ticker=AAPL --timeframe=trailing_twelve_months --pe-basic-ttm-gte=5 --pe-basic-ttm-lte=20 --roe-ttm-gte=0.15 --roa-ttm-gte=0.05', '  python polygon_data.py short-interest --ticker=AAPL --limit=10 --sort=settlement_date.desc', '  python polygon_data.py short-interest --ticker=AAPL --days-to-cover-gte=5 --settlement-date-gte=2024-01-01 --limit=20', '  python polygon_data.py short-interest --ticker-any-of=AAPL,TSLA,MSFT --days-to-cover-gt=2 --avg-daily-volume-gte=1000000 --sort=settlement_date.desc', '  python polygon_data.py short-interest --ticker=AAPL --settlement-date=2024-03-14 --days-to-cover-lte=10 --avg-daily-volume-gte=500000', '  python polygon_data.py short-volume --ticker=AAPL --limit=10 --sort=date.desc', '  python polygon_data.py short-volume --ticker=AAPL --short-volume-ratio-gte=30 --date-gte=2024-01-01 --limit=50', '  python polygon_data.py short-volume --ticker=AAPL --date=2024-03-25 --short-volume-ratio-lte=50 --total-volume-gte=100000', '  python polygon_data.py short-volume --ticker-any-of=AAPL,TSLA,MSFT --short-volume-ratio-gt=25 --date-gte=2024-03-01 --sort=date.desc']}))
        sys.exit(1)
    command = sys.argv[1]
    if command == 'tickers':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'active':
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['ticker_gte', 'ticker_gt', 'ticker_lte', 'ticker_lt']:
                    if key == 'ticker_gte':
                        kwargs['ticker_gte'] = value
                    elif key == 'ticker_gt':
                        kwargs['ticker_gt'] = value
                    elif key == 'ticker_lte':
                        kwargs['ticker_lte'] = value
                    elif key == 'ticker_lt':
                        kwargs['ticker_lt'] = value
                else:
                    kwargs[key] = value
        result = get_all_tickers(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ticker-details':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py ticker-details --ticker=SYMBOL [--date=DATE]'}))
            sys.exit(1)
        kwargs = {}
        ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    ticker = value
                else:
                    kwargs[key] = value
        if not ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_ticker_details(ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ticker-types':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                kwargs[key] = value
        result = get_ticker_types(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'related-tickers':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py related-tickers --ticker=SYMBOL'}))
            sys.exit(1)
        ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    ticker = value
        if not ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_related_tickers(ticker)
        print(json.dumps(result, indent=2))
    elif command == 'news':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['ticker_gte', 'ticker_gt', 'ticker_lte', 'ticker_lt', 'published_utc_gte', 'published_utc_gt', 'published_utc_lte', 'published_utc_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_news(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ipos':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['listing_date_gte', 'listing_date_gt', 'listing_date_lte', 'listing_date_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_ipos(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'splits':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key == 'reverse_split':
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key in ['ticker_gte', 'ticker_gt', 'ticker_lte', 'ticker_lt', 'execution_date_gte', 'execution_date_gt', 'execution_date_lte', 'execution_date_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_splits(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'dividends':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key in ['limit', 'frequency']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key == 'cash_amount':
                    try:
                        kwargs[key] = float(value)
                    except ValueError:
                        pass
                elif key in ['ticker_gte', 'ticker_gt', 'ticker_lte', 'ticker_lt', 'ex_dividend_date_gte', 'ex_dividend_date_gt', 'ex_dividend_date_lte', 'ex_dividend_date_lt', 'record_date_gte', 'record_date_gt', 'record_date_lte', 'record_date_lt', 'declaration_date_gte', 'declaration_date_gt', 'declaration_date_lte', 'declaration_date_lt', 'pay_date_gte', 'pay_date_gt', 'pay_date_lte', 'pay_date_lt', 'cash_amount_gte', 'cash_amount_gt', 'cash_amount_lte', 'cash_amount_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_dividends(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ticker-events':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py ticker-events --identifier=IDENTIFIER [--types=TYPES]'}))
            sys.exit(1)
        kwargs = {}
        identifier = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'identifier':
                    identifier = value
                else:
                    kwargs[key] = value
        if not identifier:
            print(json.dumps({'error': 'Identifier (ticker, CUSIP, or Composite FIGI) is required'}))
            sys.exit(1)
        result = get_ticker_events(identifier, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'exchanges':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                kwargs[key] = value
        result = get_exchanges(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'market-holidays':
        result = get_market_holidays()
        print(json.dumps(result, indent=2))
    elif command == 'market-status':
        result = get_market_status()
        print(json.dumps(result, indent=2))
    elif command == 'condition-codes':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'id' or key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                else:
                    kwargs[key] = value
        result = get_condition_codes(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ticker-snapshot':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py ticker-snapshot --ticker=SYMBOL'}))
            sys.exit(1)
        ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    ticker = value
        if not ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_single_ticker_snapshot(ticker)
        print(json.dumps(result, indent=2))
    elif command == 'market-snapshot':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'include_otc':
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key == 'tickers':
                    if value:
                        kwargs[key] = [ticker.strip() for ticker in value.split(',')]
                    else:
                        kwargs[key] = None
        result = get_full_market_snapshot(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'unified-snapshot':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['ticker_gte', 'ticker_gt', 'ticker_lte', 'ticker_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_unified_snapshot(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'top-movers':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py top-movers --direction=gainers/losers [--include-otc=true/false]'}))
            sys.exit(1)
        kwargs = {}
        direction = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'direction':
                    direction = value
                elif key == 'include_otc':
                    kwargs['include_otc'] = value.lower() in ('true', '1', 'yes')
        if not direction:
            print(json.dumps({'error': "Direction parameter is required and must be either 'gainers' or 'losers'"}))
            sys.exit(1)
        result = get_top_market_movers(direction, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'trades':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py trades --ticker=SYMBOL [--timestamp=TIMESTAMP] [--timestamp-gte=TIMESTAMP] [--timestamp-lte=TIMESTAMP] [--limit=NUMBER] [--sort=SORT] [--order=ORDER]'}))
            sys.exit(1)
        kwargs = {}
        stock_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stock_ticker = value
                elif key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['timestamp_gte', 'timestamp_gt', 'timestamp_lte', 'timestamp_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        if not stock_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_trades(stock_ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'last-trade':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py last-trade --ticker=SYMBOL'}))
            sys.exit(1)
        stocks_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stocks_ticker = value
        if not stocks_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_last_trade(stocks_ticker)
        print(json.dumps(result, indent=2))
    elif command == 'quotes':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py quotes --ticker=SYMBOL [--timestamp=TIMESTAMP] [--timestamp-gte=TIMESTAMP] [--timestamp-lte=TIMESTAMP] [--limit=NUMBER] [--sort=SORT] [--order=ORDER]'}))
            sys.exit(1)
        kwargs = {}
        stock_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stock_ticker = value
                elif key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['timestamp_gte', 'timestamp_gt', 'timestamp_lte', 'timestamp_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        if not stock_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_quotes(stock_ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'last-quote':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py last-quote --ticker=SYMBOL'}))
            sys.exit(1)
        stocks_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stocks_ticker = value
        if not stocks_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_last_quote(stocks_ticker)
        print(json.dumps(result, indent=2))
    elif command == 'sma':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py sma --ticker=SYMBOL --window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER'}))
            sys.exit(1)
        kwargs = {}
        stock_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stock_ticker = value
                elif key in ['limit', 'window']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['adjusted', 'expand_underlying']:
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key in ['timestamp_gte', 'timestamp_gt', 'timestamp_lte', 'timestamp_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        if not stock_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_sma(stock_ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ema':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py ema --ticker=SYMBOL --window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER'}))
            sys.exit(1)
        kwargs = {}
        stock_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stock_ticker = value
                elif key in ['limit', 'window']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['adjusted', 'expand_underlying']:
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key in ['timestamp_gte', 'timestamp_gt', 'timestamp_lte', 'timestamp_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        if not stock_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_ema(stock_ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'macd':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py macd --ticker=SYMBOL --short-window=NUMBER --long-window=NUMBER --signal-window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER'}))
            sys.exit(1)
        kwargs = {}
        stock_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stock_ticker = value
                elif key in ['limit', 'short_window', 'long_window', 'signal_window']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['adjusted', 'expand_underlying']:
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key in ['timestamp_gte', 'timestamp_gt', 'timestamp_lte', 'timestamp_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        if not stock_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_macd(stock_ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'rsi':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: python polygon_data.py rsi --ticker=SYMBOL --window=NUMBER --timespan=TIMESPAN --series-type=TYPE --adjusted=true/false --expand-underlying=true/false --limit=NUMBER'}))
            sys.exit(1)
        kwargs = {}
        stock_ticker = None
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'ticker':
                    stock_ticker = value
                elif key in ['limit', 'window']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['adjusted', 'expand_underlying']:
                    kwargs[key] = value.lower() in ('true', '1', 'yes')
                elif key in ['timestamp_gte', 'timestamp_gt', 'timestamp_lte', 'timestamp_lt']:
                    kwargs[key] = value
                else:
                    kwargs[key] = value
        if not stock_ticker:
            print(json.dumps({'error': 'Ticker symbol is required'}))
            sys.exit(1)
        result = get_rsi(stock_ticker, **kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'balance-sheets':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'cik':
                    kwargs['cik'] = value
                elif key == 'cik_any_of':
                    kwargs['cik_any_of'] = value
                elif key == 'cik_gt':
                    kwargs['cik_gt'] = value
                elif key == 'cik_gte':
                    kwargs['cik_gte'] = value
                elif key == 'cik_lt':
                    kwargs['cik_lt'] = value
                elif key == 'cik_lte':
                    kwargs['cik_lte'] = value
                elif key == 'tickers':
                    kwargs['tickers'] = value
                elif key == 'tickers_all_of':
                    kwargs['tickers_all_of'] = value
                elif key == 'tickers_any_of':
                    kwargs['tickers_any_of'] = value
                elif key == 'period_end':
                    kwargs['period_end'] = value
                elif key == 'period_end_gt':
                    kwargs['period_end_gt'] = value
                elif key == 'period_end_gte':
                    kwargs['period_end_gte'] = value
                elif key == 'period_end_lt':
                    kwargs['period_end_lt'] = value
                elif key == 'period_end_lte':
                    kwargs['period_end_lte'] = value
                elif key == 'filing_date':
                    kwargs['filing_date'] = value
                elif key == 'filing_date_gt':
                    kwargs['filing_date_gt'] = value
                elif key == 'filing_date_gte':
                    kwargs['filing_date_gte'] = value
                elif key == 'filing_date_lt':
                    kwargs['filing_date_lt'] = value
                elif key == 'filing_date_lte':
                    kwargs['filing_date_lte'] = value
                elif key == 'fiscal_year':
                    try:
                        kwargs['fiscal_year'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_gt':
                    try:
                        kwargs['fiscal_year_gt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_gte':
                    try:
                        kwargs['fiscal_year_gte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_lt':
                    try:
                        kwargs['fiscal_year_lt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_lte':
                    try:
                        kwargs['fiscal_year_lte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter':
                    try:
                        kwargs['fiscal_quarter'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_gt':
                    try:
                        kwargs['fiscal_quarter_gt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_gte':
                    try:
                        kwargs['fiscal_quarter_gte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_lt':
                    try:
                        kwargs['fiscal_quarter_lt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_lte':
                    try:
                        kwargs['fiscal_quarter_lte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'timeframe':
                    kwargs['timeframe'] = value
                elif key == 'timeframe_any_of':
                    kwargs['timeframe_any_of'] = value
                elif key == 'timeframe_gt':
                    kwargs['timeframe_gt'] = value
                elif key == 'timeframe_gte':
                    kwargs['timeframe_gte'] = value
                elif key == 'timeframe_lt':
                    kwargs['timeframe_lt'] = value
                elif key == 'timeframe_lte':
                    kwargs['timeframe_lte'] = value
                elif key == 'limit':
                    try:
                        kwargs['limit'] = int(value)
                    except ValueError:
                        pass
                elif key == 'sort':
                    kwargs['sort'] = value
        result = get_balance_sheets(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'cash-flow-statements':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'cik':
                    kwargs['cik'] = value
                elif key == 'cik_any_of':
                    kwargs['cik_any_of'] = value
                elif key == 'cik_gt':
                    kwargs['cik_gt'] = value
                elif key == 'cik_gte':
                    kwargs['cik_gte'] = value
                elif key == 'cik_lt':
                    kwargs['cik_lt'] = value
                elif key == 'cik_lte':
                    kwargs['cik_lte'] = value
                elif key == 'period_end':
                    kwargs['period_end'] = value
                elif key == 'period_end_gt':
                    kwargs['period_end_gt'] = value
                elif key == 'period_end_gte':
                    kwargs['period_end_gte'] = value
                elif key == 'period_end_lt':
                    kwargs['period_end_lt'] = value
                elif key == 'period_end_lte':
                    kwargs['period_end_lte'] = value
                elif key == 'filing_date':
                    kwargs['filing_date'] = value
                elif key == 'filing_date_gt':
                    kwargs['filing_date_gt'] = value
                elif key == 'filing_date_gte':
                    kwargs['filing_date_gte'] = value
                elif key == 'filing_date_lt':
                    kwargs['filing_date_lt'] = value
                elif key == 'filing_date_lte':
                    kwargs['filing_date_lte'] = value
                elif key == 'tickers':
                    kwargs['tickers'] = value
                elif key == 'tickers_all_of':
                    kwargs['tickers_all_of'] = value
                elif key == 'tickers_any_of':
                    kwargs['tickers_any_of'] = value
                elif key == 'fiscal_year':
                    try:
                        kwargs['fiscal_year'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_gt':
                    try:
                        kwargs['fiscal_year_gt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_gte':
                    try:
                        kwargs['fiscal_year_gte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_lt':
                    try:
                        kwargs['fiscal_year_lt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_lte':
                    try:
                        kwargs['fiscal_year_lte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter':
                    try:
                        kwargs['fiscal_quarter'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_gt':
                    try:
                        kwargs['fiscal_quarter_gt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_gte':
                    try:
                        kwargs['fiscal_quarter_gte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_lt':
                    try:
                        kwargs['fiscal_quarter_lt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_lte':
                    try:
                        kwargs['fiscal_quarter_lte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'timeframe':
                    kwargs['timeframe'] = value
                elif key == 'timeframe_any_of':
                    kwargs['timeframe_any_of'] = value
                elif key == 'timeframe_gt':
                    kwargs['timeframe_gt'] = value
                elif key == 'timeframe_gte':
                    kwargs['timeframe_gte'] = value
                elif key == 'timeframe_lt':
                    kwargs['timeframe_lt'] = value
                elif key == 'timeframe_lte':
                    kwargs['timeframe_lte'] = value
                elif key == 'limit':
                    try:
                        kwargs['limit'] = int(value)
                    except ValueError:
                        pass
                elif key == 'sort':
                    kwargs['sort'] = value
        result = get_cash_flow_statements(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'income-statements':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key == 'cik':
                    kwargs['cik'] = value
                elif key == 'cik_any_of':
                    kwargs['cik_any_of'] = value
                elif key == 'cik_gt':
                    kwargs['cik_gt'] = value
                elif key == 'cik_gte':
                    kwargs['cik_gte'] = value
                elif key == 'cik_lt':
                    kwargs['cik_lt'] = value
                elif key == 'cik_lte':
                    kwargs['cik_lte'] = value
                elif key == 'tickers':
                    kwargs['tickers'] = value
                elif key == 'tickers_all_of':
                    kwargs['tickers_all_of'] = value
                elif key == 'tickers_any_of':
                    kwargs['tickers_any_of'] = value
                elif key == 'period_end':
                    kwargs['period_end'] = value
                elif key == 'period_end_gt':
                    kwargs['period_end_gt'] = value
                elif key == 'period_end_gte':
                    kwargs['period_end_gte'] = value
                elif key == 'period_end_lt':
                    kwargs['period_end_lt'] = value
                elif key == 'period_end_lte':
                    kwargs['period_end_lte'] = value
                elif key == 'filing_date':
                    kwargs['filing_date'] = value
                elif key == 'filing_date_gt':
                    kwargs['filing_date_gt'] = value
                elif key == 'filing_date_gte':
                    kwargs['filing_date_gte'] = value
                elif key == 'filing_date_lt':
                    kwargs['filing_date_lt'] = value
                elif key == 'filing_date_lte':
                    kwargs['filing_date_lte'] = value
                elif key == 'fiscal_year':
                    try:
                        kwargs['fiscal_year'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_gt':
                    try:
                        kwargs['fiscal_year_gt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_gte':
                    try:
                        kwargs['fiscal_year_gte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_lt':
                    try:
                        kwargs['fiscal_year_lt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_year_lte':
                    try:
                        kwargs['fiscal_year_lte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter':
                    try:
                        kwargs['fiscal_quarter'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_gt':
                    try:
                        kwargs['fiscal_quarter_gt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_gte':
                    try:
                        kwargs['fiscal_quarter_gte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_lt':
                    try:
                        kwargs['fiscal_quarter_lt'] = float(value)
                    except ValueError:
                        pass
                elif key == 'fiscal_quarter_lte':
                    try:
                        kwargs['fiscal_quarter_lte'] = float(value)
                    except ValueError:
                        pass
                elif key == 'timeframe':
                    kwargs['timeframe'] = value
                elif key == 'timeframe_any_of':
                    kwargs['timeframe_any_of'] = value
                elif key == 'timeframe_gt':
                    kwargs['timeframe_gt'] = value
                elif key == 'timeframe_gte':
                    kwargs['timeframe_gte'] = value
                elif key == 'timeframe_lt':
                    kwargs['timeframe_lt'] = value
                elif key == 'timeframe_lte':
                    kwargs['timeframe_lte'] = value
                elif key == 'limit':
                    try:
                        kwargs['limit'] = int(value)
                    except ValueError:
                        pass
                elif key == 'sort':
                    kwargs['sort'] = value
        result = get_income_statements(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'ratios':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key.endswith('_any_of'):
                    kwargs[key] = value
                elif key.endswith(('_gt', '_gte', '_lt', '_lte')):
                    kwargs[key] = value
                elif key == 'limit':
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        kwargs[key] = value
                elif key in ['price', 'price_gt', 'price_gte', 'price_lt', 'price_lte', 'dividend_yield_gte', 'dividend_yield_lte', 'dividend_yield_gt', 'dividend_yield_lt', 'dividend_yield_eq', 'dividend_per_share_gte', 'dividend_per_share_lte', 'dividend_per_share_gt', 'dividend_per_share_lt', 'dividend_per_share_eq', 'dividend_yield_ttm_gte', 'dividend_yield_ttm_lte', 'dividend_yield_ttm_gt', 'dividend_yield_ttm_lt', 'dividend_yield_ttm_eq', 'book_value_per_share_gte', 'book_value_per_share_lte', 'book_value_per_share_gt', 'book_value_per_share_lt', 'book_value_per_share_eq', 'book_value_per_share_ttm_gte', 'book_value_per_share_ttm_lte', 'book_value_per_share_ttm_gt', 'book_value_per_share_ttm_lt', 'book_value_per_share_ttm_eq', 'book_value_per_share_growth_ttm_pct_gte', 'book_value_per_share_growth_ttm_pct_lte', 'book_value_per_share_growth_ttm_pct_gt', 'book_value_per_share_growth_ttm_pct_lt', 'book_value_per_share_growth_ttm_pct_eq', 'diluted_eps_growth_ttm_pct_gte', 'diluted_eps_growth_ttm_pct_lte', 'diluted_eps_growth_ttm_pct_gt', 'diluted_eps_growth_ttm_pct_lt', 'diluted_eps_growth_ttm_pct_eq', 'basic_earnings_per_share_gte', 'basic_earnings_per_share_lte', 'basic_earnings_per_share_gt', 'basic_earnings_per_share_lt', 'basic_earnings_per_share_eq', 'basic_eps_ttm_gte', 'basic_eps_ttm_lte', 'basic_eps_ttm_gt', 'basic_eps_ttm_lt', 'basic_eps_ttm_eq', 'basic_average_shares_gte', 'basic_average_shares_lte', 'basic_average_shares_gt', 'basic_average_shares_lt', 'basic_average_shares_eq', 'diluted_earnings_per_share_gte', 'diluted_earnings_per_share_lte', 'diluted_earnings_per_share_gt', 'diluted_earnings_per_share_lt', 'diluted_earnings_per_share_eq', 'diluted_eps_ttm_gte', 'diluted_eps_ttm_lte', 'diluted_eps_ttm_gt', 'diluted_eps_ttm_lt', 'diluted_eps_ttm_eq', 'diluted_average_shares_gte', 'diluted_average_shares_lte', 'diluted_average_shares_gt', 'diluted_average_shares_lt', 'diluted_average_shares_eq', 'weighted_average_shares_gte', 'weighted_average_shares_lte', 'weighted_average_shares_gt', 'weighted_average_shares_lt', 'weighted_average_shares_eq', 'market_capitalization_gte', 'market_capitalization_lte', 'market_capitalization_gt', 'market_capitalization_lt', 'market_capitalization_eq', 'ev_gte', 'ev_lte', 'ev_gt', 'ev_lt', 'ev_eq', 'pe_basic_gte', 'pe_basic_lte', 'pe_basic_gt', 'pe_basic_lt', 'pe_basic_eq', 'pe_basic_ttm_gte', 'pe_basic_ttm_lte', 'pe_basic_ttm_gt', 'pe_basic_ttm_lt', 'pe_basic_ttm_eq', 'pe_diluted_gte', 'pe_diluted_lte', 'pe_diluted_gt', 'pe_diluted_lt', 'pe_diluted_eq', 'pe_diluted_ttm_gte', 'pe_diluted_ttm_lte', 'pe_diluted_ttm_gt', 'pe_diluted_ttm_lt', 'pe_diluted_ttm_eq', 'pb_ttm_gte', 'pb_ttm_lte', 'pb_ttm_gt', 'pb_ttm_lt', 'pb_ttm_eq', 'roe_ttm_gte', 'roe_ttm_lte', 'roe_ttm_gt', 'roe_ttm_lt', 'roe_ttm_eq', 'roa_ttm_gte', 'roa_ttm_lte', 'roa_ttm_gt', 'roa_ttm_lt', 'roa_ttm_eq', 'roic_ttm_gte', 'roic_ttm_lte', 'roic_ttm_gt', 'roic_ttm_lt', 'roic_ttm_eq', 'profit_margin_ttm_gte', 'profit_margin_ttm_lte', 'profit_margin_ttm_gt', 'profit_margin_ttm_lt', 'profit_margin_ttm_eq', 'gross_margin_ttm_gte', 'gross_margin_ttm_lte', 'gross_margin_ttm_gt', 'gross_margin_ttm_lt', 'gross_margin_ttm_eq', 'sga_to_revenue_ttm_gte', 'sga_to_revenue_ttm_lte', 'sga_to_revenue_ttm_gt', 'sga_to_revenue_ttm_lt', 'sga_to_revenue_ttm_eq', 'rd_to_revenue_ttm_gte', 'rd_to_revenue_ttm_lte', 'rd_to_revenue_ttm_gt', 'rd_to_revenue_ttm_lt', 'rd_to_revenue_ttm_eq', 'r_and_d_to_revenue_ttm_gte', 'r_and_d_to_revenue_ttm_lte', 'r_and_d_to_revenue_ttm_gt', 'r_and_d_to_revenue_ttm_lt', 'r_and_d_to_revenue_ttm_eq', 'effective_tax_rate_ttm_gte', 'effective_tax_rate_ttm_lte', 'effective_tax_rate_ttm_gt', 'effective_tax_rate_ttm_lt', 'effective_tax_rate_ttm_eq', 'return_on_tangible_assets_ttm_gte', 'return_on_tangible_assets_ttm_lte', 'return_on_tangible_assets_ttm_gt', 'return_on_tangible_assets_ttm_lt', 'return_on_tangible_assets_ttm_eq', 'interest_coverage_ttm_gte', 'interest_coverage_ttm_lte', 'interest_coverage_ttm_gt', 'interest_coverage_ttm_lt', 'interest_coverage_ttm_eq', 'current_ratio_gte', 'current_ratio_lte', 'current_ratio_gt', 'current_ratio_lt', 'current_ratio_eq', 'quick_ratio_gte', 'quick_ratio_lte', 'quick_ratio_gt', 'quick_ratio_lt', 'quick_ratio_eq', 'cash_ratio_gte', 'cash_ratio_lte', 'cash_ratio_gt', 'cash_ratio_lt', 'cash_ratio_eq', 'days_of_sales_outstanding_gte', 'days_of_sales_outstanding_lte', 'days_of_sales_outstanding_gt', 'days_of_sales_outstanding_lt', 'days_of_sales_outstanding_eq', 'days_of_inventory_on_hand_gte', 'days_of_inventory_on_hand_lte', 'days_of_inventory_on_hand_gt', 'days_of_inventory_on_hand_lt', 'days_of_inventory_on_hand_eq', 'ebitda_margin_ttm_gte', 'ebitda_margin_ttm_lte', 'ebitda_margin_ttm_gt', 'ebitda_margin_ttm_lt', 'ebitda_margin_ttm_eq', 'ebitda_to_interest_coverage_ttm_gte', 'ebitda_to_interest_coverage_ttm_lte', 'ebitda_to_interest_coverage_ttm_gt', 'ebitda_to_interest_coverage_ttm_lt', 'ebitda_to_interest_coverage_ttm_eq', 'ebitda_to_revenue_ttm_gte', 'ebitda_to_revenue_ttm_lte', 'ebitda_to_revenue_ttm_gt', 'ebitda_to_revenue_ttm_lt', 'ebitda_to_revenue_ttm_eq', 'ev_to_ebitda_ttm_gte', 'ev_to_ebitda_ttm_lte', 'ev_to_ebitda_ttm_gt', 'ev_to_ebitda_ttm_lt', 'ev_to_ebitda_ttm_eq', 'ev_to_operating_cash_flow_ttm_gte', 'ev_to_operating_cash_flow_ttm_lte', 'ev_to_operating_cash_flow_ttm_gt', 'ev_to_operating_cash_flow_ttm_lt', 'ev_to_operating_cash_flow_ttm_eq', 'ev_to_sales_ttm_gte', 'ev_to_sales_ttm_lte', 'ev_to_sales_ttm_gt', 'ev_to_sales_ttm_lt', 'ev_to_sales_ttm_eq', 'ps_ttm_gte', 'ps_ttm_lte', 'ps_ttm_gt', 'ps_ttm_lt', 'ps_ttm_eq', 'price_to_book_ttm_gte', 'price_to_book_ttm_lte', 'price_to_book_ttm_gt', 'price_to_book_ttm_lt', 'price_to_book_ttm_eq', 'price_to_tangible_book_ttm_gte', 'price_to_tangible_book_ttm_lte', 'price_to_tangible_book_ttm_gt', 'price_to_tangible_book_ttm_lt', 'price_to_tangible_book_ttm_eq', 'price_to_sales_ttm_gte', 'price_to_sales_ttm_lte', 'price_to_sales_ttm_gt', 'price_to_sales_ttm_lt', 'price_to_sales_ttm_eq', 'fcfe_yield_ttm_gte', 'fcfe_yield_ttm_lte', 'fcfe_yield_ttm_gt', 'fcfe_yield_ttm_lt', 'fcfe_yield_ttm_eq', 'fcff_yield_ttm_gte', 'fcff_yield_ttm_lte', 'fcff_yield_ttm_gt', 'fcff_yield_ttm_lt', 'fcff_yield_ttm_eq', 'dividend_yield_basic_ttm_gte', 'dividend_yield_basic_ttm_lte', 'dividend_yield_basic_ttm_gt', 'dividend_yield_basic_ttm_lt', 'dividend_yield_basic_ttm_eq', 'dividend_yield_ttm_gte', 'dividend_yield_ttm_lte', 'dividend_yield_ttm_gt', 'dividend_yield_ttm_lt', 'dividend_yield_ttm_eq', 'total_debt_to_capitalization_gte', 'total_debt_to_capitalization_lte', 'total_debt_to_capitalization_gt', 'total_debt_to_capitalization_lt', 'total_debt_to_capitalization_eq', 'total_debt_to_equity_gte', 'total_debt_to_equity_lte', 'total_debt_to_equity_gt', 'total_debt_to_equity_lt', 'total_debt_to_equity_eq', 'long_term_debt_to_equity_gte', 'long_term_debt_to_equity_lte', 'long_term_debt_to_equity_gt', 'long_term_debt_to_equity_lt', 'long_term_debt_to_equity_eq', 'short_term_debt_to_equity_gte', 'short_term_debt_to_equity_lte', 'short_term_debt_to_equity_gt', 'short_term_debt_to_equity_lt', 'short_term_debt_to_equity_eq', 'long_term_debt_to_total_assets_gte', 'long_term_debt_to_total_assets_lte', 'long_term_debt_to_total_assets_gt', 'long_term_debt_to_total_assets_lt', 'long_term_debt_to_total_assets_eq', 'total_assets_to_total_equity_gte', 'total_assets_to_total_equity_lte', 'total_assets_to_total_equity_gt', 'total_assets_to_total_equity_lt', 'total_assets_to_total_equity_eq', 'debt_to_assets_gte', 'debt_to_assets_lte', 'debt_to_assets_gt', 'debt_to_assets_lt', 'debt_to_assets_eq', 'book_yield_ttm_gte', 'book_yield_ttm_lte', 'book_yield_ttm_gt', 'book_yield_ttm_lt', 'book_yield_ttm_eq', 'dividend_payout_ratio_ttm_gte', 'dividend_payout_ratio_ttm_lte', 'dividend_payout_ratio_ttm_gt', 'dividend_payout_ratio_ttm_lt', 'dividend_payout_ratio_ttm_eq', 'free_cash_flow_yield_ttm_gte', 'free_cash_flow_yield_ttm_lte', 'free_cash_flow_yield_ttm_gt', 'free_cash_flow_yield_ttm_lt', 'free_cash_flow_yield_ttm_eq', 'graham_number_ttm_gte', 'graham_number_ttm_lte', 'graham_number_ttm_gt', 'graham_number_ttm_lt', 'graham_number_ttm_eq', 'graham_number_ttm_to_net_current_asset_value_ttm_gte', 'graham_number_ttm_to_net_current_asset_value_ttm_lte', 'graham_number_ttm_to_net_current_asset_value_ttm_gt', 'graham_number_ttm_to_net_current_asset_value_ttm_lt', 'graham_number_ttm_to_net_current_asset_value_ttm_eq']:
                    try:
                        kwargs[key] = float(value)
                    except ValueError:
                        kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_financial_ratios(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'short-interest':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key in ['limit']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        kwargs[key] = value
                elif key in ['days_to_cover', 'days_to_cover_any_of', 'days_to_cover_gt', 'days_to_cover_gte', 'days_to_cover_lt', 'days_to_cover_lte', 'avg_daily_volume', 'avg_daily_volume_any_of', 'avg_daily_volume_gt', 'avg_daily_volume_gte', 'avg_daily_volume_lt', 'avg_daily_volume_lte']:
                    try:
                        kwargs[key] = float(value) if key.startswith('days_to_cover') else int(value)
                    except ValueError:
                        kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_short_interest(**kwargs)
        print(json.dumps(result, indent=2))
    elif command == 'short-volume':
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.lstrip('-')
                key = key.replace('-', '_')
                if key in ['limit']:
                    try:
                        kwargs[key] = int(value)
                    except ValueError:
                        kwargs[key] = value
                elif key in ['short_volume_ratio', 'short_volume_ratio_any_of', 'short_volume_ratio_gt', 'short_volume_ratio_gte', 'short_volume_ratio_lt', 'short_volume_ratio_lte', 'total_volume', 'total_volume_any_of', 'total_volume_gt', 'total_volume_gte', 'total_volume_lt', 'total_volume_lte']:
                    try:
                        kwargs[key] = float(value) if key.startswith('short_volume_ratio') else int(value)
                    except ValueError:
                        kwargs[key] = value
                else:
                    kwargs[key] = value
        result = get_short_volume(**kwargs)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({'error': f'Unknown command: {command}'}))
        sys.exit(1)

class NASDAQDataAPI:
    """NASDAQ Data API wrapper for modular data fetching"""

    def __init__(self, api_key: Optional[str]=None):
        self.api_key = api_key or os.getenv('NASDAQ_API_KEY')
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        """Update session headers with random user agent"""
        self.session.headers.update({'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Origin': 'https://www.nasdaq.com', 'Referer': 'https://www.nasdaq.com/', 'Connection': 'keep-alive'})

    def _get_random_user_agent(self) -> str:
        """Generate a random user agent"""
        user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0']
        import random
        return random.choice(user_agents)

    async def _make_async_request(self, url: str, headers: Optional[Dict]=None) -> Dict[str, Any]:
        """Make async HTTP request with error handling"""
        try:
            default_headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Origin': 'https://www.nasdaq.com', 'Referer': 'https://www.nasdaq.com/', 'Connection': 'keep-alive'}
            final_headers = {**default_headers, **(headers or {})}
            async with aiohttp.ClientSession(headers=final_headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {'success': True, 'data': result}
                    else:
                        text = await response.text()
                        return NASDAQError(url, f'HTTP {response.status}: {text}', response.status).to_dict()
        except aiohttp.ClientError as e:
            return NASDAQError(url, f'Network error: {str(e)}').to_dict()
        except json.JSONDecodeError as e:
            return NASDAQError(url, f'JSON decode error: {str(e)}').to_dict()
        except Exception as e:
            return NASDAQError(url, f'Unexpected error: {str(e)}').to_dict()

    def _make_request(self, url: str, headers: Optional[Dict]=None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            final_headers = {**self.session.headers, **(headers or {})}
            response = self.session.get(url, headers=final_headers, timeout=30)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {'success': True, 'data': data}
                except json.JSONDecodeError:
                    return NASDAQError(url, 'Invalid JSON response', response.status_code).to_dict()
            else:
                return NASDAQError(url, f'HTTP {response.status_code}: {response.text}', response.status_code).to_dict()
        except requests.exceptions.RequestException as e:
            return NASDAQError(url, f'Network error: {str(e)}', getattr(e.response, 'status_code', None)).to_dict()
        except Exception as e:
            return NASDAQError(url, f'Unexpected error: {str(e)}').to_dict()

    def _parse_equity_directory(self, content: str) -> pd.DataFrame:
        """Parse NASDAQ equity directory data"""
        try:
            df = pd.read_csv(StringIO(content), sep='|')
            if len(df) > 0:
                df = df.iloc[:-1]
            df.columns = [col.strip() for col in df.columns]
            if 'Security Name' in df.columns:
                df = df[~df['Security Name'].str.contains('test', case=False, na=False)]
            return df
        except Exception as e:
            raise ValueError(f'Failed to parse equity directory: {str(e)}')

    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return text
        clean = re.compile('<.*?>')
        return re.sub(clean, ' ', text)

    def _clean_html_text(self, text: str) -> str:
        """Clean HTML entities and tags"""
        if not text:
            return text
        text = html.unescape(text)
        text = text.replace('\r\n\r\n', ' ').replace('\r\n', ' ')
        text = text.replace("''", "'")
        text = self._remove_html_tags(text)
        return text.strip() if text else None

    async def search_equities(self, query: str='', is_etf: Optional[bool]=None) -> Dict[str, Any]:
        """Search for equities in NASDAQ directory

        Args:
            query: Search query (symbol or company name)
            is_etf: Filter by ETF status (True, False, or None for all)

        Returns:
            Dict containing search results
        """
        try:
            result = self._make_request(NASDAQ_EQUITY_DIR_URL, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
            if 'error' in result:
                return result
            df = self._parse_equity_directory(result['data'])
            if df.empty:
                return NASDAQError('equity_search', 'No equity data found').to_dict()
            if is_etf is not None and 'ETF' in df.columns:
                df = df[df['ETF'] == ('Y' if is_etf else 'N')]
            if query.strip():
                search_columns = ['Symbol', 'Security Name']
                if 'CQS Symbol' in df.columns:
                    search_columns.append('CQS Symbol')
                if 'NASDAQ Symbol' in df.columns:
                    search_columns.append('NASDAQ Symbol')
                mask = pd.Series([False] * len(df))
                for col in search_columns:
                    if col in df.columns:
                        mask |= df[col].str.contains(query, case=False, na=False)
                df = df[mask]
            if df.empty:
                return NASDAQError('equity_search', f"No results found for query: '{query}'").to_dict()
            if 'Market Category' in df.columns:
                df['Market Category'] = df['Market Category'].replace(' ', None)
            results = df.replace({pd.NA: None, 'nan': None}).to_dict('records')
            return {'success': True, 'data': {'query': query, 'is_etf_filter': is_etf, 'results': results, 'total_count': len(results)}}
        except Exception as e:
            return NASDAQError('equity_search', str(e)).to_dict()

    async def get_equity_screener(self, exchange: str='all', market_cap: str='all', sector: str='all', country: str='all', limit: Optional[int]=None) -> Dict[str, Any]:
        """Get equity screener results with filters

        Args:
            exchange: Exchange filter (nasdaq, nyse, amex, all)
            market_cap: Market cap filter (mega, large, mid, small, micro, all)
            sector: Sector filter
            country: Country filter
            limit: Maximum number of results

        Returns:
            Dict containing screener results
        """
        try:
            limit_param = limit if limit else 10000
            base_url = f'{NASDAQ_BASE_URL}/screener/stocks?tableonly=true&limit={limit_param}&'
            params = {}
            if exchange != 'all':
                params['exchange'] = exchange.upper()
            if market_cap != 'all':
                params['marketcap'] = market_cap
            if sector != 'all':
                sector_mapping = {'communication_services': 'telecommunications', 'financial_services': 'finance'}
                sector_clean = sector_mapping.get(sector, sector)
                params['sector'] = sector_clean
            if country != 'all':
                params['country'] = country.lower().replace(' ', '_')
            if params:
                query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
                url = base_url + query_string
            else:
                url = base_url
            result = await self._make_async_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            rows = data.get('data', {}).get('table', {}).get('rows', [])
            if not rows:
                return NASDAQError('equity_screener', 'No screener results found').to_dict()
            sorted_rows = sorted(rows, key=lambda x: float(x.get('pctchange', 0)), reverse=True)
            cleaned_results = []
            for row in sorted_rows:
                cleaned_row = {}
                for key, value in row.items():
                    if key in ['lastsale', 'netchange', 'pctchange', 'marketCap']:
                        if isinstance(value, str):
                            cleaned_value = value.replace('%', '').replace('$', '').replace(',', '')
                            cleaned_value = cleaned_value.replace('UNCH', '').replace('--', '').replace('NA', '')
                            try:
                                if key == 'pctchange':
                                    cleaned_row[key] = float(cleaned_value) / 100 if cleaned_value else None
                                else:
                                    cleaned_row[key] = float(cleaned_value) if cleaned_value else None
                            except ValueError:
                                cleaned_row[key] = None
                        else:
                            cleaned_row[key] = value
                    else:
                        cleaned_row[key] = value
                cleaned_results.append(cleaned_row)
            return {'success': True, 'data': {'filters': {'exchange': exchange, 'market_cap': market_cap, 'sector': sector, 'country': country}, 'results': cleaned_results[:limit] if limit else cleaned_results, 'total_count': len(cleaned_results)}}
        except Exception as e:
            return NASDAQError('equity_screener', str(e)).to_dict()

    async def get_dividend_calendar(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get dividend calendar

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing dividend calendar data
        """
        try:
            now = datetime.now().date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now + timedelta(days=3)
            date_list = []
            current = start
            while current <= end:
                date_list.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            all_dividends = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_dividends_for_date(date_str):
                url = f'{NASDAQ_BASE_URL}/calendar/dividends?date={date_str}'
                result = await self._make_async_request(url, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    calendar_data = data.get('calendar', {}).get('rows', [])
                    return calendar_data
                return []
            tasks = [fetch_dividends_for_date(date_str) for date_str in date_list]
            results = await asyncio.gather(*tasks)
            for date_results in results:
                all_dividends.extend(date_results)
            if not all_dividends:
                return NASDAQError('dividend_calendar', 'No dividend data found').to_dict()
            sorted_dividends = sorted(all_dividends, key=lambda x: x.get('dividend_Ex_Date', ''), reverse=True)
            formatted_results = []
            for dividend in sorted_dividends:
                formatted_dividend = {'symbol': dividend.get('symbol'), 'company_name': dividend.get('companyName'), 'ex_dividend_date': self._parse_date(dividend.get('dividend_Ex_Date')), 'payment_date': self._parse_date(dividend.get('payment_Date')), 'record_date': self._parse_date(dividend.get('record_Date')), 'declaration_date': self._parse_date(dividend.get('announcement_Date')), 'amount': self._parse_float(dividend.get('dividend_Rate')), 'annualized_amount': self._parse_float(dividend.get('indicated_Annual_Dividend'))}
                formatted_results.append(formatted_dividend)
            return {'success': True, 'data': {'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'dividends': formatted_results, 'total_count': len(formatted_results)}}
        except Exception as e:
            return NASDAQError('dividend_calendar', str(e)).to_dict()

    async def get_earnings_calendar(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get earnings calendar

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing earnings calendar data
        """
        try:
            now = datetime.now().date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now + timedelta(days=3)
            date_list = []
            current = start
            while current <= end:
                date_list.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            all_earnings = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_earnings_for_date(date_str):
                url = f'{NASDAQ_BASE_URL}/calendar/earnings?date={date_str}'
                result = await self._make_async_request(url, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    rows = data.get('rows', [])
                    if rows and data.get('asOf'):
                        report_date = datetime.strptime(data['asOf'], '%a, %b %d, %Y').date()
                        for row in rows:
                            row['date'] = report_date.strftime('%Y-%m-%d')
                    return rows
                return []
            tasks = [fetch_earnings_for_date(date_str) for date_str in date_list]
            results = await asyncio.gather(*tasks)
            for date_results in results:
                all_earnings.extend(date_results)
            if not all_earnings:
                return NASDAQError('earnings_calendar', 'No earnings data found').to_dict()
            sorted_earnings = sorted(all_earnings, key=lambda x: x.get('date', ''), reverse=True)
            formatted_results = []
            for earnings in sorted_earnings:
                formatted_earnings = {'symbol': earnings.get('symbol'), 'company_name': earnings.get('name'), 'report_date': earnings.get('date'), 'eps_previous': self._parse_float(earnings.get('lastYearEPS')), 'eps_consensus': self._parse_float(earnings.get('epsForecast')), 'eps_actual': self._parse_float(earnings.get('eps')), 'surprise_percent': self._parse_float(earnings.get('surprise')), 'num_estimates': self._parse_int(earnings.get('noOfEsts')), 'period_ending': self._parse_period_ending(earnings.get('fiscalQuarterEnding')), 'previous_report_date': self._parse_date(earnings.get('lastYearRptDt')), 'reporting_time': earnings.get('time', '').replace('time-', '') if earnings.get('time') else None, 'market_cap': self._parse_int(earnings.get('marketCap'))}
                formatted_results.append(formatted_earnings)
            return {'success': True, 'data': {'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'earnings': formatted_results, 'total_count': len(formatted_results)}}
        except Exception as e:
            return NASDAQError('earnings_calendar', str(e)).to_dict()

    async def get_ipo_calendar(self, status: str='priced', is_spo: bool=False, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get IPO calendar

        Args:
            status: IPO status (upcoming, priced, filed, withdrawn)
            is_spo: Whether to include secondary public offerings
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing IPO calendar data
        """
        try:
            if status not in IPO_STATUS_CHOICES:
                return NASDAQError('ipo_calendar', f'Invalid status. Choose from: {', '.join(IPO_STATUS_CHOICES)}').to_dict()
            now = datetime.now()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now - timedelta(days=300)
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now.date()
            months = set()
            current = start
            while current <= end:
                months.add(current.strftime('%Y-%m'))
                current = current.replace(day=1) + timedelta(days=32)
                current = current.replace(day=1)
            all_ipos = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_ipos_for_month(month_str):
                url_base = f'{NASDAQ_BASE_URL}/ipo/calendar?date={month_str}'
                if is_spo:
                    url_base += '&type=spo'
                result = await self._make_async_request(url_base, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    if status in data:
                        if status == 'upcoming':
                            return data['upcoming']['upcomingTable']['rows']
                        else:
                            return data[status]['rows']
                return []
            tasks = [fetch_ipos_for_month(month) for month in sorted(months)]
            results = await asyncio.gather(*tasks)
            for month_results in results:
                all_ipos.extend(month_results)
            if not all_ipos:
                return NASDAQError('ipo_calendar', f'No IPO data found for status: {status}').to_dict()
            if status == 'priced':
                sorted_ipos = sorted(all_ipos, key=lambda x: self._parse_date(x.get('pricedDate', '')))
            elif status == 'withdrawn':
                sorted_ipos = sorted(all_ipos, key=lambda x: self._parse_date(x.get('withdrawDate', '')))
            elif status == 'filed':
                sorted_ipos = sorted(all_ipos, key=lambda x: self._parse_date(x.get('filedDate', '')))
            else:
                sorted_ipos = all_ipos
            formatted_results = []
            for ipo in sorted_ipos:
                formatted_ipo = {'symbol': ipo.get('proposedTickerSymbol'), 'company_name': ipo.get('companyName'), 'ipo_date': self._parse_date(ipo.get('pricedDate')), 'share_price': self._parse_float(ipo.get('proposedSharePrice')), 'exchange': ipo.get('proposedExchange'), 'offer_amount': self._parse_float(ipo.get('dollarValueOfSharesOffered')), 'share_count': self._parse_int(ipo.get('sharesOffered')), 'expected_price_date': self._parse_date(ipo.get('expectedPriceDate')), 'filed_date': self._parse_date(ipo.get('filedDate')), 'withdraw_date': self._parse_date(ipo.get('withdrawDate')), 'deal_status': ipo.get('dealStatus'), 'deal_id': ipo.get('dealID')}
                formatted_results.append(formatted_ipo)
            return {'success': True, 'data': {'status': status, 'is_spo': is_spo, 'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'ipos': formatted_results, 'total_count': len(formatted_results)}}
        except Exception as e:
            return NASDAQError('ipo_calendar', str(e)).to_dict()

    async def get_economic_calendar(self, start_date: Optional[str]=None, end_date: Optional[str]=None, country: Optional[str]=None) -> Dict[str, Any]:
        """Get economic calendar

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            country: Country filter (comma-separated for multiple)

        Returns:
            Dict containing economic calendar data
        """
        try:
            now = datetime.now().date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now - timedelta(days=2)
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now + timedelta(days=3)
            date_list = []
            current = start
            while current <= end:
                if current.weekday() < 5:
                    date_list.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            all_events = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_events_for_date(date_str):
                url = f'{NASDAQ_BASE_URL}/calendar/economicevents?date={date_str}'
                result = await self._make_async_request(url, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    rows = data.get('rows', [])
                    processed_events = []
                    for event in rows:
                        gmt = event.get('gmt', '')
                        if gmt == 'All Day':
                            datetime_str = f'{date_str} 00:00'
                        else:
                            clean_gmt = gmt.replace('Tentative', '00:00').replace('24H', '00:00')
                            datetime_str = f'{date_str} {clean_gmt}'
                        event['date'] = datetime_str
                        event.pop('gmt', None)
                        for field in ['actual', 'previous', 'consensus']:
                            if event.get(field):
                                event[field] = event[field].replace('&nbsp;', '-')
                        if event.get('description'):
                            event['description'] = self._clean_html_text(event['description'])
                        processed_events.append(event)
                    return processed_events
                return []
            tasks = [fetch_events_for_date(date_str) for date_str in date_list]
            results = await asyncio.gather(*tasks)
            for date_results in results:
                all_events.extend(date_results)
            if not all_events:
                return NASDAQError('economic_calendar', 'No economic events found').to_dict()
            if country:
                country_list = [c.strip().lower().replace(' ', '_') for c in country.split(',')]
                all_events = [event for event in all_events if event.get('country', '').lower().replace(' ', '_') in country_list]
            sorted_events = sorted(all_events, key=lambda x: x.get('date', ''))
            return {'success': True, 'data': {'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'country_filter': country, 'events': sorted_events, 'total_count': len(sorted_events)}}
        except Exception as e:
            return NASDAQError('economic_calendar', str(e)).to_dict()

    async def get_top_retail_activity(self, limit: int=10) -> Dict[str, Any]:
        """Get top retail activity

        Args:
            limit: Maximum number of results

        Returns:
            Dict containing top retail activity data
        """
        try:
            if not self.api_key:
                return NASDAQError('top_retail', 'NASDAQ API key required for retail activity data').to_dict()
            url = f'{NASDAQ_RTAT_URL}?api_key={self.api_key}'
            result = self._make_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            if 'datatable' not in data or 'data' not in data['datatable']:
                return NASDAQError('top_retail', 'Invalid response format').to_dict()
            retail_data = data['datatable']['data']
            if not retail_data:
                return NASDAQError('top_retail', 'No retail activity data found').to_dict()
            formatted_results = []
            for row in retail_data[:limit]:
                formatted_result = {'date': self._parse_date(row[0]), 'symbol': row[1], 'activity': row[2], 'sentiment': row[3]}
                formatted_results.append(formatted_result)
            return {'success': True, 'data': {'retail_activity': formatted_results, 'total_count': len(formatted_results), 'limit': limit}}
        except Exception as e:
            return NASDAQError('top_retail', str(e)).to_dict()

    async def get_comprehensive_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview with multiple data sources"""
        try:
            results = {}
            screener_result = await self.get_equity_screener(limit=50)
            results['top_performers'] = screener_result
            dividends_result = await self.get_dividend_calendar(start_date=datetime.now().strftime('%Y-%m-%d'), end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            results['upcoming_dividends'] = dividends_result
            earnings_result = await self.get_earnings_calendar(start_date=datetime.now().strftime('%Y-%m-%d'), end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            results['upcoming_earnings'] = earnings_result
            ipo_result = await self.get_ipo_calendar(status='upcoming')
            results['upcoming_ipos'] = ipo_result
            recent_ipo_result = await self.get_ipo_calendar(status='priced', start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'), end_date=datetime.now().strftime('%Y-%m-%d'))
            results['recent_ipos'] = recent_ipo_result
            economic_result = await self.get_economic_calendar(start_date=datetime.now().strftime('%Y-%m-%d'), end_date=datetime.now().strftime('%Y-%m-%d'))
            results['today_economic_events'] = economic_result
            if self.api_key:
                retail_result = await self.get_top_retail_activity(limit=20)
                results['top_retail_activity'] = retail_result
            else:
                results['top_retail_activity'] = {'success': False, 'message': 'NASDAQ API key required for retail activity data'}
            return {'success': True, 'data': {'overview': results, 'generated_at': datetime.now().isoformat(), 'data_sources': ['Equity Screener', 'Dividend Calendar', 'Earnings Calendar', 'IPO Calendar', 'Economic Calendar', 'Top Retail Activity']}}
        except Exception as e:
            return NASDAQError('market_overview', str(e)).to_dict()

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string and return ISO format"""
        if not date_str or date_str == 'N/A':
            return None
        try:
            for fmt in ['%m/%d/%Y', '%Y-%m-%d']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return date_str
        except:
            return date_str

    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse value as float"""
        if not value or value == 'N/A':
            return None
        try:
            if isinstance(value, str):
                clean_value = value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                return float(clean_value) if clean_value else None
            return float(value)
        except:
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse value as integer"""
        if not value or value == 'N/A':
            return None
        try:
            if isinstance(value, str):
                clean_value = value.replace(',', '')
                return int(clean_value) if clean_value else None
            return int(value)
        except:
            return None

    def _parse_period_ending(self, period_str: str) -> Optional[str]:
        """Parse fiscal quarter ending period"""
        if not period_str or period_str == 'N/A':
            return None
        try:
            parsed_date = datetime.strptime(period_str, '%b/%Y')
            return parsed_date.strftime('%Y-%m')
        except:
            return period_str

def _remove_html_tags(self, text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return text
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)

class FMPDataWrapper:
    """Modular FMP data wrapper with fault-tolerant endpoints"""

    def __init__(self, api_key: Optional[str]=None):
        self.base_url = 'https://financialmodelingprep.com/api/v3'
        self.api_key = api_key or os.environ.get('FMP_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept-Terminal/1.0'})
        self.default_limit = 10
        self.interval_map = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '1h': '1hour', '4h': '4hour', '1d': 'day'}
        self.period_map = {'annual': 'annual', 'quarter': 'quarter', 'ttm': 'ttm'}
        self.statement_periods = ['annual', 'quarter']

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                error_message = data.get('Error Message', data.get('error'))
                if error_message:
                    if any((keyword in error_message.lower() for keyword in ['upgrade', 'subscription', 'exclusive', 'unauthorized'])):
                        raise Exception(f'API Access Error: {error_message}. This feature may require a premium subscription.')
                    else:
                        raise Exception(f'FMP API Error: {error_message}')
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f'HTTP request failed: {str(e)}')
        except json.JSONDecodeError as e:
            raise Exception(f'JSON decode error: {str(e)}')

    def _build_url(self, endpoint: str, params: Dict[str, Any]=None) -> str:
        """Build API URL with parameters"""
        url = f'{self.base_url}/{endpoint}?apikey={self.api_key}'
        if params:
            filtered_params = {k: v for k, v in params.items() if v is not None}
            for key, value in filtered_params.items():
                if key not in ['symbol']:
                    url += f'&{key}={value}'
        return url

    def get_equity_quote(self, symbols: str) -> Dict[str, Any]:
        """Get real-time stock quotes for multiple symbols"""
        try:
            if not symbols:
                return {'error': FMPError('equity_quote', 'Symbols parameter is required').to_dict()}
            symbol_list = [s.strip() for s in symbols.split(',')]
            results = []
            for symbol in symbol_list:
                try:
                    url = self._build_url(f'quote/{symbol}')
                    data = self._make_request(url)
                    if isinstance(data, list) and len(data) > 0:
                        results.extend(data)
                    elif isinstance(data, dict):
                        results.append(data)
                except Exception as e:
                    continue
            if not results:
                return {'error': FMPError('equity_quote', f'No data found for symbols: {symbols}').to_dict()}
            return {'success': True, 'data': results, 'parameters': {'symbols': symbols}}
        except Exception as e:
            return {'error': FMPError('equity_quote', str(e)).to_dict()}

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile and basic information"""
        try:
            if not symbol:
                return {'error': FMPError('company_profile', 'Symbol parameter is required').to_dict()}
            url = self._build_url(f'profile/{symbol}')
            data = self._make_request(url)
            if not data:
                return {'error': FMPError('company_profile', f'No data found for symbol: {symbol}').to_dict()}
            if isinstance(data, list):
                data = data[0] if data else {}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol}}
        except Exception as e:
            return {'error': FMPError('company_profile', str(e)).to_dict()}

    def get_historical_prices(self, symbol: str, start_date: Optional[str]=None, end_date: Optional[str]=None, interval: str='1d') -> Dict[str, Any]:
        """Get historical price data for a symbol"""
        try:
            if not symbol:
                return {'error': FMPError('historical_prices', 'Symbol parameter is required').to_dict()}
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            fmp_interval = self.interval_map.get(interval, 'day')
            params = {'from': start_date, 'to': end_date}
            if fmp_interval == 'day':
                url = self._build_url(f'historical-price-full/{symbol}', params)
                data = self._make_request(url)
                historical_data = data.get('historical', []) if isinstance(data, dict) else []
            else:
                url = self._build_url(f'historical-chart/{fmp_interval}/{symbol}', params)
                historical_data = self._make_request(url)
                if not isinstance(historical_data, list):
                    historical_data = []
            if not historical_data:
                return {'error': FMPError('historical_prices', f'No historical data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': historical_data, 'parameters': {'symbol': symbol, 'start_date': start_date, 'end_date': end_date, 'interval': interval}}
        except Exception as e:
            return {'error': FMPError('historical_prices', str(e)).to_dict()}

    def get_income_statement(self, symbol: str, period: str='annual', limit: int=10) -> Dict[str, Any]:
        """Get income statement data"""
        try:
            if not symbol:
                return {'error': FMPError('income_statement', 'Symbol parameter is required').to_dict()}
            if period not in self.statement_periods:
                period = 'annual'
            params = {'period': period, 'limit': limit}
            url = self._build_url(f'income-statement/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('income_statement', f'No income statement data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('income_statement', str(e)).to_dict()}

    def get_balance_sheet(self, symbol: str, period: str='annual', limit: int=10) -> Dict[str, Any]:
        """Get balance sheet data"""
        try:
            if not symbol:
                return {'error': FMPError('balance_sheet', 'Symbol parameter is required').to_dict()}
            if period not in self.statement_periods:
                period = 'annual'
            params = {'period': period, 'limit': limit}
            url = self._build_url(f'balance-sheet-statement/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('balance_sheet', f'No balance sheet data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('balance_sheet', str(e)).to_dict()}

    def get_cash_flow_statement(self, symbol: str, period: str='annual', limit: int=10) -> Dict[str, Any]:
        """Get cash flow statement data"""
        try:
            if not symbol:
                return {'error': FMPError('cash_flow_statement', 'Symbol parameter is required').to_dict()}
            if period not in self.statement_periods:
                period = 'annual'
            params = {'period': period, 'limit': limit}
            url = self._build_url(f'cash-flow-statement/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('cash_flow_statement', f'No cash flow data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('cash_flow_statement', str(e)).to_dict()}

    def get_financial_ratios(self, symbol: str, period: str='annual', limit: int=10) -> Dict[str, Any]:
        """Get financial ratios data"""
        try:
            if not symbol:
                return {'error': FMPError('financial_ratios', 'Symbol parameter is required').to_dict()}
            if period not in self.statement_periods + ['ttm']:
                period = 'annual'
            if period == 'ttm':
                url = self._build_url(f'ratios-ttm/{symbol}')
                data = self._make_request(url)
                if isinstance(data, dict):
                    data = [data]
            else:
                params = {'period': period, 'limit': limit}
                url = self._build_url(f'ratios/{symbol}', params)
                data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('financial_ratios', f'No financial ratios found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('financial_ratios', str(e)).to_dict()}

    def get_key_metrics(self, symbol: str, period: str='annual', limit: int=10) -> Dict[str, Any]:
        """Get key metrics data"""
        try:
            if not symbol:
                return {'error': FMPError('key_metrics', 'Symbol parameter is required').to_dict()}
            if period not in self.statement_periods:
                period = 'annual'
            params = {'period': period, 'limit': limit}
            url = self._build_url(f'key-metrics/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('key_metrics', f'No key metrics found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('key_metrics', str(e)).to_dict()}

    def get_market_snapshots(self) -> Dict[str, Any]:
        """Get market snapshots and indices"""
        try:
            indices_url = self._build_url('majors-indexes')
            indices_data = self._make_request(indices_url)
            sectors_url = self._build_url('sectors-performance')
            sectors_data = self._make_request(sectors_url)
            market_cap_url = self._build_url('market-capitalization/AAPL')
            market_cap_data = self._make_request(market_cap_url)
            result = {'indices': indices_data if isinstance(indices_data, list) else [], 'sectors': sectors_data if isinstance(sectors_data, list) else [], 'market_cap_example': market_cap_data}
            return {'success': True, 'data': result, 'parameters': {}}
        except Exception as e:
            return {'error': FMPError('market_snapshots', str(e)).to_dict()}

    def get_treasury_rates(self) -> Dict[str, Any]:
        """Get current treasury rates"""
        try:
            url = self._build_url('treasury')
            data = self._make_request(url)
            if not data:
                return {'error': FMPError('treasury_rates', 'No treasury rates data found').to_dict()}
            return {'success': True, 'data': data, 'parameters': {}}
        except Exception as e:
            return {'error': FMPError('treasury_rates', str(e)).to_dict()}

    def get_etf_info(self, symbol: str) -> Dict[str, Any]:
        """Get ETF information"""
        try:
            if not symbol:
                return {'error': FMPError('etf_info', 'Symbol parameter is required').to_dict()}
            url = self._build_url(f'etf-info/{symbol}')
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('etf_info', f'No ETF data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol}}
        except Exception as e:
            return {'error': FMPError('etf_info', str(e)).to_dict()}

    def get_etf_holdings(self, symbol: str) -> Dict[str, Any]:
        """Get ETF holdings data"""
        try:
            if not symbol:
                return {'error': FMPError('etf_holdings', 'Symbol parameter is required').to_dict()}
            url = self._build_url(f'etf-holder/{symbol}')
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('etf_holdings', f'No ETF holdings found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol}}
        except Exception as e:
            return {'error': FMPError('etf_holdings', str(e)).to_dict()}

    def get_crypto_list(self) -> Dict[str, Any]:
        """Get list of available cryptocurrencies"""
        try:
            url = self._build_url('cryptocurrency/list')
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('crypto_list', 'No cryptocurrency data found').to_dict()}
            return {'success': True, 'data': data[:100], 'parameters': {}}
        except Exception as e:
            return {'error': FMPError('crypto_list', str(e)).to_dict()}

    def get_crypto_historical(self, symbol: str, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get historical cryptocurrency prices"""
        try:
            if not symbol:
                return {'error': FMPError('crypto_historical', 'Symbol parameter is required').to_dict()}
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            params = {'from': start_date, 'to': end_date}
            url = self._build_url(f'historical-price-crypto/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('crypto_historical', f'No crypto data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'start_date': start_date, 'end_date': end_date}}
        except Exception as e:
            return {'error': FMPError('crypto_historical', str(e)).to_dict()}

    def get_company_news(self, symbol: str, limit: int=50) -> Dict[str, Any]:
        """Get news for a specific company"""
        try:
            if not symbol:
                return {'error': FMPError('company_news', 'Symbol parameter is required').to_dict()}
            params = {'limit': limit}
            url = self._build_url(f'stock_news?tickers={symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('company_news', f'No news found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('company_news', str(e)).to_dict()}

    def get_general_news(self) -> Dict[str, Any]:
        """Get general financial news"""
        try:
            url = self._build_url('stock_news')
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('general_news', 'No news data found').to_dict()}
            return {'success': True, 'data': data[:100], 'parameters': {}}
        except Exception as e:
            return {'error': FMPError('general_news', str(e)).to_dict()}

    def get_economic_calendar(self) -> Dict[str, Any]:
        """Get economic calendar data"""
        try:
            url = self._build_url('economic_calendar')
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('economic_calendar', 'No economic calendar data found').to_dict()}
            return {'success': True, 'data': data, 'parameters': {}}
        except Exception as e:
            return {'error': FMPError('economic_calendar', str(e)).to_dict()}

    def get_insider_trading(self, symbol: str, limit: int=100) -> Dict[str, Any]:
        """Get insider trading data for a symbol"""
        try:
            if not symbol:
                return {'error': FMPError('insider_trading', 'Symbol parameter is required').to_dict()}
            params = {'limit': limit}
            url = self._build_url(f'insider-trading/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('insider_trading', f'No insider trading data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('insider_trading', str(e)).to_dict()}

    def get_institutional_ownership(self, symbol: str, limit: int=100) -> Dict[str, Any]:
        """Get institutional ownership data"""
        try:
            if not symbol:
                return {'error': FMPError('institutional_ownership', 'Symbol parameter is required').to_dict()}
            params = {'limit': limit}
            url = self._build_url(f'institutional-holder/{symbol}', params)
            data = self._make_request(url)
            if not data or not isinstance(data, list):
                return {'error': FMPError('institutional_ownership', f'No institutional ownership data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': data, 'parameters': {'symbol': symbol, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('institutional_ownership', str(e)).to_dict()}

    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive company overview including profile, quotes, and key metrics"""
        try:
            if not symbol:
                return {'error': FMPError('company_overview', 'Symbol parameter is required').to_dict()}
            results = {}
            profile_result = self.get_company_profile(symbol)
            results['profile'] = profile_result
            quote_result = self.get_equity_quote(symbol)
            results['quote'] = quote_result
            metrics_result = self.get_key_metrics(symbol, 'annual', 1)
            results['key_metrics'] = metrics_result
            ratios_result = self.get_financial_ratios(symbol, 'ttm', 1)
            results['financial_ratios'] = ratios_result
            news_result = self.get_company_news(symbol, 10)
            results['recent_news'] = news_result
            has_data = any((result.get('success') and result.get('data') for result in results.values()))
            if not has_data:
                return {'error': FMPError('company_overview', f'No data found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': results, 'parameters': {'symbol': symbol}}
        except Exception as e:
            return {'error': FMPError('company_overview', str(e)).to_dict()}

    def get_financial_statements(self, symbol: str, period: str='annual', limit: int=5) -> Dict[str, Any]:
        """Get all financial statements for a company"""
        try:
            if not symbol:
                return {'error': FMPError('financial_statements', 'Symbol parameter is required').to_dict()}
            results = {}
            income_result = self.get_income_statement(symbol, period, limit)
            results['income_statement'] = income_result
            balance_result = self.get_balance_sheet(symbol, period, limit)
            results['balance_sheet'] = balance_result
            cash_flow_result = self.get_cash_flow_statement(symbol, period, limit)
            results['cash_flow_statement'] = cash_flow_result
            ratios_result = self.get_financial_ratios(symbol, period, limit)
            results['financial_ratios'] = ratios_result
            metrics_result = self.get_key_metrics(symbol, period, limit)
            results['key_metrics'] = metrics_result
            has_data = any((result.get('success') and result.get('data') for result in results.values()))
            if not has_data:
                return {'error': FMPError('financial_statements', f'No financial statements found for symbol: {symbol}').to_dict()}
            return {'success': True, 'data': results, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
        except Exception as e:
            return {'error': FMPError('financial_statements', str(e)).to_dict()}

def get_company_overview(self, symbol: str) -> Dict[str, Any]:
    """Get comprehensive company overview including profile, quotes, and key metrics"""
    try:
        if not symbol:
            return {'error': FMPError('company_overview', 'Symbol parameter is required').to_dict()}
        results = {}
        profile_result = self.get_company_profile(symbol)
        results['profile'] = profile_result
        quote_result = self.get_equity_quote(symbol)
        results['quote'] = quote_result
        metrics_result = self.get_key_metrics(symbol, 'annual', 1)
        results['key_metrics'] = metrics_result
        ratios_result = self.get_financial_ratios(symbol, 'ttm', 1)
        results['financial_ratios'] = ratios_result
        news_result = self.get_company_news(symbol, 10)
        results['recent_news'] = news_result
        has_data = any((result.get('success') and result.get('data') for result in results.values()))
        if not has_data:
            return {'error': FMPError('company_overview', f'No data found for symbol: {symbol}').to_dict()}
        return {'success': True, 'data': results, 'parameters': {'symbol': symbol}}
    except Exception as e:
        return {'error': FMPError('company_overview', str(e)).to_dict()}

def get_financial_statements(self, symbol: str, period: str='annual', limit: int=5) -> Dict[str, Any]:
    """Get all financial statements for a company"""
    try:
        if not symbol:
            return {'error': FMPError('financial_statements', 'Symbol parameter is required').to_dict()}
        results = {}
        income_result = self.get_income_statement(symbol, period, limit)
        results['income_statement'] = income_result
        balance_result = self.get_balance_sheet(symbol, period, limit)
        results['balance_sheet'] = balance_result
        cash_flow_result = self.get_cash_flow_statement(symbol, period, limit)
        results['cash_flow_statement'] = cash_flow_result
        ratios_result = self.get_financial_ratios(symbol, period, limit)
        results['financial_ratios'] = ratios_result
        metrics_result = self.get_key_metrics(symbol, period, limit)
        results['key_metrics'] = metrics_result
        has_data = any((result.get('success') and result.get('data') for result in results.values()))
        if not has_data:
            return {'error': FMPError('financial_statements', f'No financial statements found for symbol: {symbol}').to_dict()}
        return {'success': True, 'data': results, 'parameters': {'symbol': symbol, 'period': period, 'limit': limit}}
    except Exception as e:
        return {'error': FMPError('financial_statements', str(e)).to_dict()}

def main():
    """Main function for CLI interface"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python fmp_data.py <command> [args...]', 'commands': ['equity_quote [symbols]', 'company_profile [symbol]', 'historical_prices [symbol] [start_date] [end_date] [interval]', 'income_statement [symbol] [period] [limit]', 'balance_sheet [symbol] [period] [limit]', 'cash_flow_statement [symbol] [period] [limit]', 'financial_ratios [symbol] [period] [limit]', 'key_metrics [symbol] [period] [limit]', 'market_snapshots', 'treasury_rates', 'etf_info [symbol]', 'etf_holdings [symbol]', 'crypto_list', 'crypto_historical [symbol] [start_date] [end_date]', 'company_news [symbol] [limit]', 'general_news', 'economic_calendar', 'insider_trading [symbol] [limit]', 'institutional_ownership [symbol] [limit]', 'company_overview [symbol]', 'financial_statements [symbol] [period] [limit]'], 'note': 'FMP API key required. Set FMP_API_KEY environment variable or pass to wrapper constructor.'}))
        sys.exit(1)
    command = sys.argv[1]
    wrapper = FMPDataWrapper()
    try:
        if command == 'equity_quote':
            symbols = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_equity_quote(symbols)
        elif command == 'company_profile':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_company_profile(symbol)
        elif command == 'historical_prices':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            interval = sys.argv[5] if len(sys.argv) > 5 else '1d'
            result = wrapper.get_historical_prices(symbol, start_date, end_date, interval)
        elif command == 'income_statement':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            result = wrapper.get_income_statement(symbol, period, limit)
        elif command == 'balance_sheet':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            result = wrapper.get_balance_sheet(symbol, period, limit)
        elif command == 'cash_flow_statement':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            result = wrapper.get_cash_flow_statement(symbol, period, limit)
        elif command == 'financial_ratios':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            result = wrapper.get_financial_ratios(symbol, period, limit)
        elif command == 'key_metrics':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            result = wrapper.get_key_metrics(symbol, period, limit)
        elif command == 'market_snapshots':
            result = wrapper.get_market_snapshots()
        elif command == 'treasury_rates':
            result = wrapper.get_treasury_rates()
        elif command == 'etf_info':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_etf_info(symbol)
        elif command == 'etf_holdings':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_etf_holdings(symbol)
        elif command == 'crypto_list':
            result = wrapper.get_crypto_list()
        elif command == 'crypto_historical':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            result = wrapper.get_crypto_historical(symbol, start_date, end_date)
        elif command == 'company_news':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            result = wrapper.get_company_news(symbol, limit)
        elif command == 'general_news':
            result = wrapper.get_general_news()
        elif command == 'economic_calendar':
            result = wrapper.get_economic_calendar()
        elif command == 'insider_trading':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            result = wrapper.get_insider_trading(symbol, limit)
        elif command == 'institutional_ownership':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            result = wrapper.get_institutional_ownership(symbol, limit)
        elif command == 'company_overview':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_company_overview(symbol)
        elif command == 'financial_statements':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 5
            result = wrapper.get_financial_statements(symbol, period, limit)
        else:
            result = {'error': FMPError(command, f'Unknown command: {command}').to_dict()}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': FMPError(command, str(e)).to_dict()}, indent=2))

class SECDataWrapper:
    """Modular SEC data wrapper with fault-tolerant endpoints"""

    def __init__(self):
        self.base_url = 'https://www.sec.gov'
        self.data_url = 'https://data.sec.gov'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept Terminal - financial analysis tool (contact@fincept.com)', 'Accept-Encoding': 'gzip, deflate', 'Accept': 'application/json'})
        self.common_form_types = ['10-K', '10-Q', '8-K', '10-D', '20-F', '40-F', '6-K', '8-A', 'S-1', 'S-3', 'S-4', 'S-8', 'F-1', 'F-3', 'F-4', '424A', '424B', 'SC 13D', 'SC 13G', '13F-HR', '13F-NT', '3', '4', '5', '144', 'N-1A', 'N-2', 'N-CSR', 'N-PX', 'N-PORT', '485BPOS']
        self.taxonomy_facts = ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'NetIncomeLoss', 'Assets', 'Liabilities', 'StockholdersEquity', 'CashAndCashEquivalentsAtCarryingValue', 'AccountsReceivableNetCurrent', 'InventoryNet', 'PropertyPlantAndEquipmentNet', 'Goodwill', 'LongTermDebt', 'OperatingIncomeLoss', 'EarningsPerShareBasic', 'EarningsPerShareDiluted', 'CostOfGoodsAndServicesSold', 'SellingGeneralAndAdministrativeExpense', 'ResearchAndDevelopmentExpense', 'InterestExpenseDebt', 'IncomeTaxExpenseBenefit']
        self.transaction_codes = {'A': 'Grant, award or other acquisition', 'C': 'Conversion of derivative security', 'D': 'Disposition to the issuer', 'E': 'Expiration of short derivative position', 'F': 'Payment of exercise price or tax liability', 'G': 'Bona fide gift', 'H': 'Expiration of long derivative position', 'I': 'Discretionary transaction', 'J': 'Other acquisition or disposition', 'L': 'Small acquisition under Rule 16a-6', 'M': 'Exercise or conversion of derivative security', 'O': 'Exercise of out-of-the-money derivative security', 'P': 'Open market or private purchase', 'S': 'Open market or private sale', 'U': 'Disposition pursuant to a tender of shares', 'W': 'Acquisition or disposition by will or the laws of descent and distribution', 'X': 'Exercise of in-the-money or at-the-money derivative security', 'Z': 'Deposit into or withdrawal from voting trust'}

    def _make_request(self, url: str, use_cache: bool=True) -> Dict[str, Any]:
        """Make HTTP request with proper headers and error handling"""
        try:
            time.sleep(0.1)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and 'error' in data:
                raise Exception(f'SEC API error: {data['error']}')
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f'HTTP request failed: {str(e)}')
        except json.JSONDecodeError as e:
            raise Exception(f'JSON decode error: {str(e)}')

    def _normalize_cik(self, cik: Union[str, int]) -> str:
        """Normalize CIK to 10-digit format with leading zeros"""
        cik_str = str(cik).strip()
        cik_str = cik_str.lstrip('0')
        return cik_str.zfill(10)

    def _format_date(self, date_str: str) -> str:
        """Format date string to SEC format (YYYYMMDD)"""
        try:
            if not date_str:
                return ''
            if '-' in date_str:
                return date_str.replace('-', '')
            elif len(date_str) == 8 and date_str.isdigit():
                return date_str
            else:
                date_obj = pd.to_datetime(date_str)
                return date_obj.strftime('%Y%m%d')
        except:
            return date_str

    def get_company_filings(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None, form_type: Optional[str]=None, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=100) -> Dict[str, Any]:
        """Get company filings from SEC database"""
        try:
            if not symbol and (not cik):
                return {'error': SECError('company_filings', 'Either symbol or CIK must be provided').to_dict()}
            if symbol and (not cik):
                cik_result = self.get_cik_map(symbol)
                if not cik_result.get('success'):
                    return cik_result
                cik = cik_result['data'].get('cik')
            if not cik:
                return {'error': SECError('company_filings', 'CIK not found for the provided symbol').to_dict()}
            normalized_cik = self._normalize_cik(cik)
            url = f'{self.data_url}/submissions/CIK{normalized_cik}.json'
            data = self._make_request(url)
            if not data or 'filings' not in data:
                return {'error': SECError('company_filings', f'No filings found for CIK: {cik}').to_dict()}
            filings_data = data['filings']['recent']
            filings_df = pd.DataFrame(filings_data)
            if form_type:
                form_types = [ft.upper().strip() for ft in form_type.split(',')]
                filings_df = filings_df[filings_df['form'].isin(form_types)]
            if start_date:
                start_formatted = self._format_date(start_date)
                filings_df = filings_df[filings_df['filingDate'] >= start_formatted]
            if end_date:
                end_formatted = self._format_date(end_date)
                filings_df = filings_df[filings_df['filingDate'] <= end_formatted]
            filings_df = filings_df.sort_values('filingDate', ascending=False)
            if limit and limit > 0:
                filings_df = filings_df.head(limit)
            base_url = f'{self.base_url}/Archives/edgar/data/{str(int(normalized_cik))}/'

            def format_urls(row):
                accession = row['accessionNumber']
                accession_clean = accession.replace('-', '')
                primary_doc = row['primaryDocument']
                return {'filing_url': f'{base_url}{accession_clean}/{primary_doc}', 'complete_submission_url': f'{base_url}{accession}.txt', 'filing_detail_url': f'{base_url}{accession}-index.htm'}
            url_data = filings_df.apply(format_urls, axis=1)
            url_df = pd.DataFrame(list(url_data))
            filings_df = pd.concat([filings_df.reset_index(drop=True), url_df], axis=1)
            filings_list = filings_df.to_dict('records')
            return {'success': True, 'data': filings_list, 'parameters': {'symbol': symbol, 'cik': str(cik), 'form_type': form_type, 'start_date': start_date, 'end_date': end_date, 'limit': limit}}
        except Exception as e:
            return {'error': SECError('company_filings', str(e)).to_dict()}

    def get_cik_map(self, symbol: str) -> Dict[str, Any]:
        """Get CIK (Central Index Key) for a company symbol"""
        try:
            if not symbol:
                return {'error': SECError('cik_map', 'Symbol parameter is required').to_dict()}
            symbol_upper = symbol.upper().strip()
            common_cik_mappings = {'AAPL': '0000320193', 'MSFT': '0000789019', 'GOOGL': '0001652044', 'GOOG': '0001652044', 'AMZN': '0001018724', 'META': '0001326801', 'FB': '0001326801', 'NVDA': '0001045810', 'TSLA': '0001318605', 'ADBE': '0000796343', 'CRM': '0001108703', 'NFLX': '0001065280', 'INTC': '0000050863', 'AMD': '0000002488', 'PYPL': '0001633917', 'EBAY': '0001065088', 'ORCL': '0001341439', 'SAP': '0001003010', 'IBM': '0000051143', 'CSCO': '0000858877', 'JPM': '0000019617', 'BAC': '0000070858', 'WFC': '0000072971', 'GS': '0000885620', 'MS': '0000895421', 'C': '0000083107', 'AXP': '0000004962', 'BLK': '0000007339', 'V': '0001492633', 'MA': '0001141391', 'COF': '0000091974', 'AIG': '0000005114', 'SPGI': '0000025348', 'MCO': '0000072969', 'ICE': '0001623622', 'CME': '0001158449', 'JNJ': '0000200406', 'UNH': '0000731766', 'PFE': '0000078003', 'ABBV': '0001551152', 'TMO': '0001135217', 'ABT': '0000001800', 'DHR': '0000038777', 'MDT': '0000008229', 'LLY': '0000059478', 'BMY': '0000014272', 'AMGN': '0000006951', 'GILD': '0000320193', 'CVS': '0000070205', 'WBA': '0000109212', 'MRK': '0000066404', 'BSX': '0000014099', 'AMZN': '0001018724', 'TSLA': '0001318605', 'HD': '0000023545', 'MCD': '0000063908', 'NKE': '0000320187', 'LOW': '0000055133', 'TGT': '0000021344', 'COST': '0000711579', 'BKNG': '0000108800', 'TJX': '0000109130', 'ROST': '0000071471', 'AZO': '0000872470', 'EBAY': '0001065088', 'ETSY': '0001564408', 'PTON': '0001767421', 'ZM': '0001813756', 'WMT': '0000104169', 'PG': '0000080424', 'KO': '0000021344', 'PEP': '0000077476', 'COST': '0000711579', 'CL': '0000206724', 'KMB': '0000058039', 'GIS': '0000041049', 'K': '0000056701', 'HSY': '0000047565', 'KDP': '0001768217', 'STZ': '0000946744', 'MNST': '0001326801', 'SYY': '0000096021', 'ADM': '0000005867', 'BGS': '0000007212', 'XOM': '0000047457', 'CVX': '0000093410', 'COP': '0000077476', 'EOG': '0001121788', 'SLB': '0000788198', 'KMI': '0000047539', 'PSX': '0000104169', 'VLO': '0000094126', 'MPC': '0000060833', 'OXY': '0000788881', 'HAL': '0000047228', 'BKR': '0001778682', 'BA': '0000012927', 'CAT': '0000018230', 'GE': '0000040533', 'MMM': '0000066740', 'HON': '0000077336', 'UPS': '0000109130', 'RTX': '0000950210', 'LMT': '0000051143', 'DE': '0000031520', 'EMR': '0000032604', 'GD': '0000405334', 'NOC': '0000069232', 'LIN': '0000946744', 'APD': '0000006093', 'DOW': '0000025236', 'DD': '0000025530', 'ECL': '0000032604', 'NEM': '0000047228', 'FCX': '0000080729', 'BHP': '0000638343', 'RIO': '0000896708', 'VALE': '0000106248', 'SHW': '0000105808', 'PPG': '0000077476', 'AMT': '0001063761', 'PLD': '0001063761', 'CCI': '0001063761', 'EQIX': '0001063761', 'PSA': '0001063761', 'WELL': '0001063761', 'VTR': '0001063761', 'O': '0001063761', 'DLR': '0001063761', 'SPG': '0001063761', 'NEE': '0000759975', 'DUK': '0000065734', 'SO': '0000064176', 'AEP': '0000004904', 'XEL': '0000072113', 'SRE': '0000073266', 'PEG': '0000073124', 'ED': '0000104169', 'DIS': '0001001039', 'NFLX': '0001065280', 'CMCSA': '0001166691', 'T': '0000732717', 'VZ': '0000732717', 'TMUS': '0001293996', 'CHTR': '0001633917', 'FOX': '0001773323', 'BRK-A': '0001067983', 'BRK-B': '0001067983', 'SPY': '0000097602', 'QQQ': '0000759975', 'GLD': '0000932471', 'SLV': '0001564408', 'BTC': 'N/A', 'ETH': 'N/A', 'SPY': '0000097602', 'IVV': '0000738124', 'VOO': '0000738124', 'VTI': '0000738124', 'QQQ': '0000759975', 'IWM': '0000077476', 'EFA': '0000932471', 'EEM': '0000932471', 'VNQ': '0000738124', 'XLF': '0000932471', 'XLK': '0000932471', 'XLE': '0000932471', 'NOW': '0001762926', 'SNOW': '0001813756', 'PLTR': '0001823094', 'CRWD': '0001813756', 'ZS': '0001813756', 'DOCU': '0001813756', 'TWLO': '0001813756', 'SQ': '0001813756', 'ROKU': '0001813756', 'ZM': '0001813756', 'PTON': '0001767421', 'ABNB': '0001559720', 'SCHW': '0000733385', 'IBKR': '0001492904', 'MCO': '0000072969', 'SPGI': '0000025348', 'ICE': '0001623622', 'CME': '0001158449', 'CBOE': '0001158449', 'NDAQ': '0000073297', 'REGN': '0000314618', 'GILD': '0000320193', 'BIIB': '0000875321', 'MRNA': '0001813756', 'BNTX': '0001813756', 'CVS': '0000070205', 'WBA': '0000109212', 'CI': '0000716659', 'LULU': '0001065088', 'SBUX': '0000899233', 'DKS': '0000872470', 'BBY': '0000109212', 'BB': '0000932471', 'NWSA': '0000932471', 'FOX-A': '0001773323'}
            cik = common_cik_mappings.get(symbol_upper)
            if not cik:
                return {'success': False, 'error': SECError('cik_map', f'CIK not found for symbol: {symbol_upper}').to_dict(), 'note': f"Symbol '{symbol_upper}' not found in common company database. Available symbols: {list(common_cik_mappings.keys())[:10]}..."}
            return {'success': True, 'data': {'cik': cik, 'symbol': symbol_upper}, 'parameters': {'symbol': symbol}}
        except Exception as e:
            return {'error': SECError('cik_map', str(e)).to_dict()}

    def get_symbol_map(self, cik: Union[str, int]) -> Dict[str, Any]:
        """Get symbol mapping for a CIK"""
        try:
            if not cik:
                return {'error': SECError('symbol_map', 'CIK parameter is required').to_dict()}
            common_cik_mappings = {'AAPL': '0000320193', 'MSFT': '0000789019', 'GOOGL': '0001652044', 'GOOG': '0001652044', 'AMZN': '0001018724', 'META': '0001326801', 'FB': '0001326801', 'NVDA': '0001045810', 'TSLA': '0001318605', 'ADBE': '0000796343', 'CRM': '0001108703', 'NFLX': '0001065280', 'INTC': '0000050863', 'AMD': '0000002488', 'PYPL': '0001633917', 'EBAY': '0001065088', 'ORCL': '0001341439', 'SAP': '0001003010', 'IBM': '0000051143', 'CSCO': '0000858877', 'JPM': '0000019617', 'BAC': '0000070858', 'WFC': '0000072971', 'GS': '0000885620', 'MS': '0000895421', 'C': '0000083107', 'AXP': '0000004962', 'BLK': '0000007339', 'V': '0001492633', 'MA': '0001141391', 'COF': '0000091974', 'AIG': '0000005114', 'SPGI': '0000025348', 'MCO': '0000072969', 'ICE': '0001623622', 'CME': '0001158449', 'JNJ': '0000200406', 'UNH': '0000731766', 'PFE': '0000078003', 'ABBV': '0001551152', 'TMO': '0001135217', 'ABT': '0000001800', 'DHR': '0000038777', 'MDT': '0000008229', 'LLY': '0000059478', 'BMY': '0000014272', 'AMGN': '0000006951', 'GILD': '0000320193', 'CVS': '0000070205', 'WBA': '0000109212', 'MRK': '0000066404', 'BSX': '0000014099', 'AMZN': '0001018724', 'TSLA': '0001318605', 'HD': '0000023545', 'MCD': '0000063908', 'NKE': '0000320187', 'LOW': '0000055133', 'TGT': '0000021344', 'COST': '0000711579', 'BKNG': '0000108800', 'TJX': '0000109130', 'ROST': '0000071471', 'AZO': '0000872470', 'EBAY': '0001065088', 'ETSY': '0001564408', 'PTON': '0001767421', 'ZM': '0001813756', 'WMT': '0000104169', 'PG': '0000080424', 'KO': '0000021344', 'PEP': '0000077476', 'COST': '0000711579', 'CL': '0000206724', 'KMB': '0000058039', 'GIS': '0000041049', 'K': '0000056701', 'HSY': '0000047565', 'KDP': '0001768217', 'STZ': '0000946744', 'MNST': '0001326801', 'SYY': '0000096021', 'ADM': '0000005867', 'BGS': '0000007212', 'XOM': '0000047457', 'CVX': '0000093410', 'COP': '0000077476', 'EOG': '0001121788', 'SLB': '0000788198', 'KMI': '0000047539', 'PSX': '0000104169', 'VLO': '0000094126', 'MPC': '0000060833', 'OXY': '0000788881', 'HAL': '0000047228', 'BKR': '0001778682', 'BA': '0000012927', 'CAT': '0000018230', 'GE': '0000040533', 'MMM': '0000066740', 'HON': '0000077336', 'UPS': '0000109130', 'RTX': '0000950210', 'LMT': '0000051143', 'DE': '0000031520', 'EMR': '0000032604', 'GD': '0000405334', 'NOC': '0000069232', 'LIN': '0000946744', 'APD': '0000006093', 'DOW': '0000025236', 'DD': '0000025530', 'ECL': '0000032604', 'NEM': '0000047228', 'FCX': '0000080729', 'BHP': '0000638343', 'RIO': '0000896708', 'VALE': '0000106248', 'SHW': '0000105808', 'PPG': '0000077476', 'AMT': '0001063761', 'PLD': '0001063761', 'CCI': '0001063761', 'EQIX': '0001063761', 'PSA': '0001063761', 'WPL': '0001063761', 'VTR': '0001063761', 'O': '0001063761', 'DLR': '0001063761', 'SPG': '0001063761', 'NEE': '0000759975', 'DUK': '0000065734', 'SO': '0000064176', 'AEP': '0000004904', 'XEL': '0000072113', 'SRE': '0000073266', 'PEG': '0000073124', 'ED': '0000104169', 'DIS': '0001001039', 'NFLX': '0001065280', 'CMCSA': '0001166691', 'T': '0000732717', 'VZ': '0000732717', 'TMUS': '0001293996', 'CHTR': '0001633917', 'FOX': '0001773323', 'BRK-A': '0001067983', 'BRK-B': '0001067983', 'SPY': '0000097602', 'QQQ': '0000759975', 'GLD': '0000932471', 'SLV': '0001564408', 'BTC': 'N/A', 'ETH': 'N/A', 'SPY': '0000097602', 'IVV': '0000738124', 'VOO': '0000738124', 'VTI': '0000738124', 'QQQ': '0000759975', 'IWM': '0000077476', 'EFA': '0000932471', 'EEM': '0000932471', 'VNQ': '0000738124', 'XLF': '0000932471', 'XLK': '0000932471', 'XLE': '0000932471', 'NOW': '0001762926', 'SNOW': '0001813756', 'PLTR': '0001823094', 'CRWD': '0001813756', 'ZS': '0001813756', 'DOCU': '0001813756', 'TWLO': '0001813756', 'SQ': '0001813756', 'ROKU': '0001813756', 'ZM': '0001813756', 'PTON': '0001767421', 'ABNB': '0001559720', 'SCHW': '0000733385', 'IBKR': '0001492904', 'MCO': '0000072969', 'SPGI': '0000025348', 'ICE': '0001623622', 'CME': '0001158449', 'CBOE': '0001158449', 'NDAQ': '0000073297', 'REGN': '0000314618', 'GILD': '0000320193', 'BIIB': '0000875321', 'MRNA': '0001813756', 'BNTX': '0001813756', 'CVS': '0000070205', 'WBA': '0000109212', 'CI': '0000716659', 'LULU': '0001065088', 'SBUX': '0000899233', 'DKS': '0000872470', 'BBY': '0000109212', 'BB': '0000932471', 'NWSA': '0000932471', 'FOX-A': '0001773323'}
            cik_to_symbol = {v: k for k, v in common_cik_mappings.items()}
            normalized_cik = self._normalize_cik(cik)
            symbol = cik_to_symbol.get(normalized_cik)
            if not symbol:
                return {'success': False, 'error': SECError('symbol_map', f'Symbol not found for CIK: {normalized_cik}').to_dict(), 'note': f"CIK '{normalized_cik}' not found in common company database."}
            return {'success': True, 'data': {'cik': normalized_cik, 'symbol': symbol}, 'parameters': {'cik': str(cik)}}
        except Exception as e:
            return {'error': SECError('symbol_map', str(e)).to_dict()}

    def get_filing_content(self, filing_url: str) -> Dict[str, Any]:
        """Get content of a specific SEC filing"""
        try:
            if not filing_url:
                return {'error': SECError('filing_content', 'Filing URL is required').to_dict()}
            if '/data/' not in filing_url:
                return {'error': SECError('filing_content', 'Invalid SEC filing URL format').to_dict()}
            return {'success': True, 'data': {'url': filing_url, 'content_type': 'text/html', 'note': 'Filing content download would be implemented here'}, 'parameters': {'filing_url': filing_url}}
        except Exception as e:
            return {'error': SECError('filing_content', str(e)).to_dict()}

    def parse_filing_html(self, html_content: str) -> Dict[str, Any]:
        """Parse HTML content from SEC filing"""
        try:
            if not html_content:
                return {'error': SECError('parse_filing_html', 'HTML content is required').to_dict()}
            try:
                from bs4 import BeautifulSoup
                import re
            except ImportError:
                return {'success': True, 'data': {'parsed_content': "BeautifulSoup not available - install with 'pip install beautifulsoup4'", 'tables_found': 0, 'text_content': 'HTML parsing requires additional dependencies'}, 'parameters': {'content_length': len(html_content)}, 'note': 'Install BeautifulSoup4 for full HTML parsing capabilities'}
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            text_content = re.sub('\\s+', ' ', text_content).strip()
            tables = soup.find_all('table')
            table_data = []
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                table_rows = []
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        table_rows.append(row_data)
                if table_rows:
                    table_data.append({'table_index': i, 'headers': table_rows[0] if table_rows else [], 'data': table_rows[1:] if len(table_rows) > 1 else [], 'row_count': len(table_rows), 'column_count': len(table_rows[0]) if table_rows else 0})
            extracted_info = {'company_name': self._extract_company_name(text_content), 'filing_date': self._extract_filing_date(text_content), 'period_end_date': self._extract_period_end_date(text_content), 'form_type': self._extract_form_type(text_content), 'cik': self._extract_cik(text_content)}
            financial_keywords = ['revenue', 'net income', 'earnings', 'cash flow', 'assets', 'liabilities', 'equity']
            financial_data_found = []
            for keyword in financial_keywords:
                if keyword.lower() in text_content.lower():
                    financial_data_found.append(keyword)
            return {'success': True, 'data': {'parsed_content': 'HTML content successfully parsed', 'text_content': text_content[:1000] + '...' if len(text_content) > 1000 else text_content, 'text_length': len(text_content), 'tables_found': len(tables), 'table_data': table_data, 'extracted_info': extracted_info, 'financial_keywords_found': financial_data_found, 'html_elements': {'title': soup.title.get_text(strip=True) if soup.title else None, 'links': len(soup.find_all('a')), 'images': len(soup.find_all('img')), 'divs': len(soup.find_all('div'))}}, 'parameters': {'content_length': len(html_content), 'parsing_method': 'BeautifulSoup'}}
        except Exception as e:
            return {'error': SECError('parse_filing_html', str(e)).to_dict()}

    def _extract_company_name(self, text_content: str) -> str:
        """Extract company name from text content"""
        patterns = ['COMPANY CONFORMED NAME:\\s*([^\\n]+)', 'Company Name:\\s*([^\\n]+)', 'NAME OF ISSUER:\\s*([^\\n]+)']
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_filing_date(self, text_content: str) -> str:
        """Extract filing date from text content"""
        patterns = ['FILED AS OF DATE:\\s*(\\d{8})', 'Filed:\\s*(\\d{4}-\\d{2}-\\d{2})', 'FILING DATE:\\s*(\\d{8})']
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                if '-' in date_str:
                    return date_str
                elif len(date_str) == 8:
                    return f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}'
        return ''

    def _extract_period_end_date(self, text_content: str) -> str:
        """Extract period end date from text content"""
        patterns = ['PERIOD OF REPORT:\\s*(\\d{8})', 'For the period ended\\s*(\\d{4}-\\d{2}-\\d{2})', 'PERIOD END DATE:\\s*(\\d{8})']
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                if '-' in date_str:
                    return date_str
                elif len(date_str) == 8:
                    return f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}'
        return ''

    def _extract_form_type(self, text_content: str) -> str:
        """Extract form type from text content"""
        patterns = ['FORM TYPE:\\s*([^\\n]+)', 'Form\\s+([0-9]+[A-Z\\-]*)', 'CONFORMED SUBMISSION TYPE:\\s*([^\\n]+)']
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_cik(self, text_content: str) -> str:
        """Extract CIK from text content"""
        patterns = ['CENTRAL INDEX KEY:\\s*(\\d{10})', 'CIK:\\s*(\\d{10})', 'SEC FILE NUMBER:\\s*(\\d{10})']
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1)
        return ''

    def get_insider_trading(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=100) -> Dict[str, Any]:
        """Get insider trading data (Form 4 filings)"""
        try:
            if not symbol and (not cik):
                return {'error': SECError('insider_trading', 'Either symbol or CIK must be provided').to_dict()}
            filings_result = self.get_company_filings(symbol=symbol, cik=cik, form_type='4', start_date=start_date, end_date=end_date, limit=limit)
            if not filings_result.get('success'):
                return filings_result
            filings_data = filings_result['data']
            insider_trades = []
            for filing in filings_data:
                insider_trade = {'filing_date': filing.get('filingDate'), 'accession_number': filing.get('accessionNumber'), 'company_name': 'Extracted from filing', 'insider_name': 'Extracted from filing', 'transaction_type': 'P', 'securities_transacted': 0, 'price': 0, 'amount': 0, 'ownership_type': 'Direct', 'note': 'Form 4 parsing would be implemented here'}
                insider_trades.append(insider_trade)
            return {'success': True, 'data': insider_trades, 'parameters': {'symbol': symbol, 'cik': str(cik) if cik else None, 'start_date': start_date, 'end_date': end_date, 'limit': limit}}
        except Exception as e:
            return {'error': SECError('insider_trading', str(e)).to_dict()}

    def get_institutional_ownership(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=50) -> Dict[str, Any]:
        """Get institutional ownership data (Form 13F filings)"""
        try:
            if not symbol and (not cik):
                return {'error': SECError('institutional_ownership', 'Either symbol or CIK must be provided').to_dict()}
            filings_result = self.get_company_filings(symbol=symbol, cik=cik, form_type='13F-HR', start_date=start_date, end_date=end_date, limit=limit)
            if not filings_result.get('success'):
                return filings_result
            filings_data = filings_result['data']
            institutional_holdings = []
            for filing in filings_data:
                holding = {'filing_date': filing.get('filingDate', ''), 'accession_number': filing.get('accessionNumber', ''), 'institution_name': 'Extracted from filing', 'cusip': 'Extracted from filing', 'security_name': 'Extracted from filing', 'shares': 0, 'market_value': 0, 'note': 'Form 13F parsing would be implemented here'}
                institutional_holdings.append(holding)
            return {'success': True, 'data': institutional_holdings, 'parameters': {'symbol': symbol, 'cik': str(cik) if cik else None, 'start_date': start_date, 'end_date': end_date, 'limit': limit}}
        except Exception as e:
            return {'error': SECError('institutional_ownership', str(e)).to_dict()}

    def search_companies(self, query: str, is_fund: bool=False) -> Dict[str, Any]:
        """Search for companies in SEC database"""
        try:
            if not query:
                return {'error': SECError('search_companies', 'Search query is required').to_dict()}
            query_upper = query.upper().strip()
            common_cik_mappings = {'AAPL': {'cik': '0000320193', 'name': 'Apple Inc.', 'exchange': 'NASDAQ', 'sic': '3571', 'state': 'CA'}, 'MSFT': {'cik': '0000789019', 'name': 'Microsoft Corporation', 'exchange': 'NASDAQ', 'sic': '7372', 'state': 'WA'}, 'GOOGL': {'cik': '0001652044', 'name': 'Alphabet Inc.', 'exchange': 'NASDAQ', 'sic': '7370', 'state': 'DE'}, 'GOOG': {'cik': '0001652044', 'name': 'Alphabet Inc.', 'exchange': 'NASDAQ', 'sic': '7370', 'state': 'DE'}, 'AMZN': {'cik': '0001018724', 'name': 'Amazon.com, Inc.', 'exchange': 'NASDAQ', 'sic': '5961', 'state': 'DE'}, 'META': {'cik': '0001326801', 'name': 'Meta Platforms, Inc.', 'exchange': 'NASDAQ', 'sic': '7370', 'state': 'DE'}, 'NVDA': {'cik': '0001045810', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ', 'sic': '3674', 'state': 'DE'}, 'TSLA': {'cik': '0001318605', 'name': 'Tesla, Inc.', 'exchange': 'NASDAQ', 'sic': '3711', 'state': 'DE'}, 'JPM': {'cik': '0000019617', 'name': 'JPMorgan Chase & Co.', 'exchange': 'NYSE', 'sic': '6021', 'state': 'DE'}, 'BAC': {'cik': '0000070858', 'name': 'Bank of America Corporation', 'exchange': 'NYSE', 'sic': '6021', 'state': 'DE'}, 'WFC': {'cik': '0000072971', 'name': 'Wells Fargo & Company', 'exchange': 'NYSE', 'sic': '6021', 'state': 'DE'}, 'GS': {'cik': '0000885620', 'name': 'The Goldman Sachs Group, Inc.', 'exchange': 'NYSE', 'sic': '6211', 'state': 'DE'}, 'V': {'cik': '0001492633', 'name': 'Visa Inc.', 'exchange': 'NYSE', 'sic': '6021', 'state': 'DE'}, 'MA': {'cik': '0001141391', 'name': 'Mastercard Incorporated', 'exchange': 'NYSE', 'sic': '6021', 'state': 'DE'}, 'JNJ': {'cik': '0000200406', 'name': 'Johnson & Johnson', 'exchange': 'NYSE', 'sic': '2834', 'state': 'DE'}, 'UNH': {'cik': '0000731766', 'name': 'UnitedHealth Group Incorporated', 'exchange': 'NYSE', 'sic': '8099', 'state': 'DE'}, 'PFE': {'cik': '0000078003', 'name': 'Pfizer Inc.', 'exchange': 'NYSE', 'sic': '2834', 'state': 'DE'}, 'TMO': {'cik': '0001135217', 'name': 'Thermo Fisher Scientific Inc.', 'exchange': 'NYSE', 'sic': '3821', 'state': 'DE'}, 'ABT': {'cik': '0000001800', 'name': 'Abbott Laboratories', 'exchange': 'NYSE', 'sic': '3841', 'state': 'DE'}, 'WMT': {'cik': '0000104169', 'name': 'Walmart Inc.', 'exchange': 'NYSE', 'sic': '5331', 'state': 'DE'}, 'PG': {'cik': '0000080424', 'name': 'The Procter & Gamble Company', 'exchange': 'NYSE', 'sic': '2844', 'state': 'DE'}, 'KO': {'cik': '0000021344', 'name': 'The Coca-Cola Company', 'exchange': 'NYSE', 'sic': '2086', 'state': 'DE'}, 'PEP': {'cik': '0000077476', 'name': 'PepsiCo, Inc.', 'exchange': 'NASDAQ', 'sic': '2086', 'state': 'DE'}, 'COST': {'cik': '0000711579', 'name': 'Costco Wholesale Corporation', 'exchange': 'NASDAQ', 'sic': '5331', 'state': 'DE'}, 'XOM': {'cik': '0000047457', 'name': 'Exxon Mobil Corporation', 'exchange': 'NYSE', 'sic': '2911', 'state': 'DE'}, 'CVX': {'cik': '0000093410', 'name': 'Chevron Corporation', 'exchange': 'NYSE', 'sic': '2911', 'state': 'DE'}, 'COP': {'cik': '0000077476', 'name': 'ConocoPhillips', 'exchange': 'NYSE', 'sic': '2911', 'state': 'DE'}, 'BA': {'cik': '0000012927', 'name': 'The Boeing Company', 'exchange': 'NYSE', 'sic': '3721', 'state': 'DE'}, 'CAT': {'cik': '0000018230', 'name': 'Caterpillar Inc.', 'exchange': 'NYSE', 'sic': '3531', 'state': 'DE'}, 'GE': {'cik': '0000040533', 'name': 'General Electric Company', 'exchange': 'NYSE', 'sic': '3621', 'state': 'DE'}, 'MMM': {'cik': '0000066740', 'name': '3M Company', 'exchange': 'NYSE', 'sic': '2670', 'state': 'DE'}, 'SPY': {'cik': '0000097602', 'name': 'SPDR S&P 500 ETF Trust', 'exchange': 'AMEX', 'sic': '6726', 'state': 'MA'}, 'QQQ': {'cik': '0000759975', 'name': 'Invesco QQQ Trust', 'exchange': 'NASDAQ', 'sic': '6726', 'state': 'MA'}, 'VTI': {'cik': '0000738124', 'name': 'Vanguard Total Stock Market ETF', 'exchange': 'AMEX', 'sic': '6726', 'state': 'PA'}, 'IVV': {'cik': '0000738124', 'name': 'iShares Core S&P 500 ETF', 'exchange': 'AMEX', 'sic': '6726', 'state': 'PA'}}
            results = []
            if query_upper in common_cik_mappings:
                company_data = common_cik_mappings[query_upper]
                results.append({'cik': company_data['cik'], 'name': company_data['name'], 'symbol': query_upper, 'exchange': company_data['exchange'], 'sic': company_data['sic'], 'state_location': company_data['state'], 'state_of_incorporation': 'DE', 'match_type': 'exact_symbol'})
            for symbol, data in common_cik_mappings.items():
                if query_upper in symbol and symbol != query_upper:
                    results.append({'cik': data['cik'], 'name': data['name'], 'symbol': symbol, 'exchange': data['exchange'], 'sic': data['sic'], 'state_location': data['state'], 'state_of_incorporation': 'DE', 'match_type': 'partial_symbol'})
            for symbol, data in common_cik_mappings.items():
                if query_upper in data['name'].upper() and symbol != query_upper:
                    results.append({'cik': data['cik'], 'name': data['name'], 'symbol': symbol, 'exchange': data['exchange'], 'sic': data['sic'], 'state_location': data['state'], 'state_of_incorporation': 'DE', 'match_type': 'name_match'})
            unique_results = []
            seen_ciks = set()
            priority_order = {'exact_symbol': 0, 'partial_symbol': 1, 'name_match': 2}
            results.sort(key=lambda x: priority_order.get(x.get('match_type', 'name_match'), 3))
            for result in results:
                if result['cik'] not in seen_ciks:
                    unique_results.append(result)
                    seen_ciks.add(result['cik'])
                    if len(unique_results) >= 10:
                        break
            if not unique_results:
                available_symbols = list(common_cik_mappings.keys())[:20]
                return {'success': True, 'data': [], 'parameters': {'query': query, 'is_fund': is_fund}, 'note': f"No companies found matching '{query}'. Available symbols include: {', '.join(available_symbols)}"}
            return {'success': True, 'data': unique_results, 'parameters': {'query': query, 'is_fund': is_fund}, 'total_results': len(unique_results), 'database_coverage': len(common_cik_mappings)}
        except Exception as e:
            return {'error': SECError('search_companies', str(e)).to_dict()}

    def search_etfs_mutual_funds(self, query: str) -> Dict[str, Any]:
        """Search for ETFs and mutual funds"""
        try:
            if not query:
                return {'error': SECError('search_etfs_mutual_funds', 'Search query is required').to_dict()}
            return self.search_companies(query, is_fund=True)
        except Exception as e:
            return {'error': SECError('search_etfs_mutual_funds', str(e)).to_dict()}

    def get_available_form_types(self) -> Dict[str, Any]:
        """Get list of available SEC form types"""
        try:
            form_info = {}
            form_descriptions = {'10-K': "Annual report providing comprehensive overview of company's business and financial condition", '10-Q': 'Quarterly report covering financial performance and operations', '8-K': 'Current report disclosing material events that shareholders should know about', '10-D': 'Annual report for registered investment companies (mutual funds)', '20-F': 'Annual report for foreign private issuers', '40-F': 'Annual report for foreign private issuers (Canadian)', '6-K': 'Current report for foreign private issuers', 'S-1': 'Registration statement for new securities offerings', 'S-3': 'Registration statement for established companies', 'S-4': 'Registration statement for mergers and acquisitions', 'F-1': 'Registration statement for foreign private issuers', '424A': 'Prospectus filed under Rule 424(a)', 'SC 13D': 'Beneficial ownership report (5%+ ownership)', 'SC 13G': 'Beneficial ownership report (passive investor)', '13F-HR': 'Institutional investment manager holdings report', '3': 'Initial statement of beneficial ownership', '4': 'Statement of changes in beneficial ownership (insider trading)', '144': 'Notice of proposed sale of securities'}
            for form_type in self.common_form_types:
                form_info[form_type] = {'description': form_descriptions.get(form_type, 'SEC filing form'), 'frequency': 'Annual' if form_type in ['10-K', '10-D', '20-F', '40-F'] else 'Quarterly' if form_type in ['10-Q'] else 'As needed'}
            return {'success': True, 'data': form_info, 'parameters': {}}
        except Exception as e:
            return {'error': SECError('available_form_types', str(e)).to_dict()}

    def get_company_facts(self, cik: Union[str, int]) -> Dict[str, Any]:
        """Get company facts data from SEC API"""
        try:
            if not cik:
                return {'error': SECError('company_facts', 'CIK parameter is required').to_dict()}
            normalized_cik = self._normalize_cik(cik)
            url = f'{self.data_url}/api/xbrl/companyfacts/CIK{normalized_cik}.json'
            data = self._make_request(url)
            if not data or 'facts' not in data:
                return {'error': SECError('company_facts', f'No facts found for CIK: {cik}').to_dict()}
            facts_data = data.get('facts', {})
            us_gaap_facts = facts_data.get('us-gaap', {})
            dei_facts = facts_data.get('dei', {})
            key_metrics = {'RevenueFromContractWithCustomerExcludingAssessedTax': 'Revenue', 'NetIncomeLoss': 'Net Income', 'Assets': 'Total Assets', 'Liabilities': 'Total Liabilities', 'StockholdersEquity': "Shareholders' Equity", 'CashAndCashEquivalentsAtCarryingValue': 'Cash & Cash Equivalents', 'AccountsReceivableNetCurrent': 'Accounts Receivable', 'InventoryNet': 'Inventory', 'PropertyPlantAndEquipmentNet': 'PP&E (Net)', 'Goodwill': 'Goodwill', 'LongTermDebt': 'Long-Term Debt', 'OperatingIncomeLoss': 'Operating Income', 'EarningsPerShareBasic': 'EPS (Basic)', 'EarningsPerShareDiluted': 'EPS (Diluted)', 'CostOfGoodsAndServicesSold': 'Cost of Revenue', 'SellingGeneralAndAdministrativeExpense': 'SG&A Expense', 'ResearchAndDevelopmentExpense': 'R&D Expense', 'InterestExpenseDebt': 'Interest Expense', 'IncomeTaxExpenseBenefit': 'Income Tax Expense'}
            key_facts = {}
            for fact_name, display_name in key_metrics.items():
                if fact_name in us_gaap_facts:
                    fact_data = us_gaap_facts[fact_name]
                    units = list(fact_data.keys())
                    if units:
                        unit_key = units[0]
                        values = fact_data[unit_key]
                        if values and isinstance(values, list):
                            recent_value = max(values, key=lambda x: x.get('end', '') if isinstance(x, dict) and x.get('end') else '')
                            if isinstance(recent_value, dict):
                                key_facts[display_name] = {'value': recent_value.get('val'), 'end_date': recent_value.get('end'), 'unit': unit_key, 'frame': recent_value.get('frame'), 'fy': recent_value.get('fy'), 'fp': recent_value.get('fp'), 'formatted_value': f'{unit_key.upper()} {recent_value.get('val', 0):,.0f}' if recent_value.get('val') and 'USD' in unit_key else f'{recent_value.get('val', 0)}'}
            company_info = {}
            if 'EntityCommonStockSharesOutstanding' in dei_facts:
                shares_data = dei_facts['EntityCommonStockSharesOutstanding']
                if shares_data and list(shares_data.keys()):
                    values = shares_data[list(shares_data.keys())[0]]
                    if values and isinstance(values, list):
                        recent_shares = max(values, key=lambda x: x.get('end', '') if isinstance(x, dict) and x.get('end') else '')
                        if isinstance(recent_shares, dict):
                            company_info['shares_outstanding'] = recent_shares.get('val')
            return {'success': True, 'data': {'entity_name': data.get('entityName'), 'cik': normalized_cik, 'company_info': company_info, 'financial_metrics': key_facts, 'taxonomy_coverage': {'us-gaap': len(us_gaap_facts), 'dei': len(dei_facts), 'total_metrics': len(key_facts)}, 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, 'parameters': {'cik': str(cik)}}
        except Exception as e:
            return {'error': SECError('company_facts', str(e)).to_dict()}

    def get_financial_statements(self, cik: Union[str, int], taxonomy: str='us-gaap', fact_list: Optional[List[str]]=None) -> Dict[str, Any]:
        """Get financial statements data using company facts"""
        try:
            facts_result = self.get_company_facts(cik)
            if not facts_result.get('success'):
                return facts_result
            facts_data = facts_result['data']['facts']
            if fact_list:
                filtered_facts = {k: v for k, v in facts_data.items() if k in fact_list}
            else:
                filtered_facts = facts_data
            return {'success': True, 'data': filtered_facts, 'parameters': {'cik': str(cik), 'taxonomy': taxonomy, 'fact_list': fact_list}}
        except Exception as e:
            return {'error': SECError('financial_statements', str(e)).to_dict()}

    def get_company_overview(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None) -> Dict[str, Any]:
        """Get comprehensive company overview including filings, facts, and insider data"""
        try:
            if not symbol and (not cik):
                return {'error': SECError('company_overview', 'Either symbol or CIK must be provided').to_dict()}
            if symbol and (not cik):
                cik_result = self.get_cik_map(symbol)
                if cik_result.get('success'):
                    cik = cik_result['data'].get('cik')
            if not cik:
                return {'error': SECError('company_overview', 'CIK not found for the provided symbol').to_dict()}
            results = {}
            filings_result = self.get_company_filings(cik=cik, form_type='10-K,10-Q,8-K', limit=10)
            results['recent_filings'] = filings_result
            facts_result = self.get_company_facts(cik)
            results['company_facts'] = facts_result
            insider_result = self.get_insider_trading(cik=cik, limit=10)
            results['insider_trading'] = insider_result
            has_data = any((result.get('success') and result.get('data') for result in results.values()))
            if not has_data:
                return {'error': SECError('company_overview', f'No data found for CIK: {cik}').to_dict()}
            return {'success': True, 'data': results, 'parameters': {'symbol': symbol, 'cik': str(cik)}}
        except Exception as e:
            return {'error': SECError('company_overview', str(e)).to_dict()}

    def get_filings_by_form_type(self, form_type: str, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=100) -> Dict[str, Any]:
        """Get all filings of a specific form type within date range"""
        try:
            return {'success': True, 'data': [], 'parameters': {'form_type': form_type, 'start_date': start_date, 'end_date': end_date, 'limit': limit}, 'note': "This endpoint requires SEC's advanced search API for full implementation."}
        except Exception as e:
            return {'error': SECError('filings_by_form_type', str(e)).to_dict()}

def _normalize_cik(self, cik: Union[str, int]) -> str:
    """Normalize CIK to 10-digit format with leading zeros"""
    cik_str = str(cik).strip()
    cik_str = cik_str.lstrip('0')
    return cik_str.zfill(10)

def get_filing_content(self, filing_url: str) -> Dict[str, Any]:
    """Get content of a specific SEC filing"""
    try:
        if not filing_url:
            return {'error': SECError('filing_content', 'Filing URL is required').to_dict()}
        if '/data/' not in filing_url:
            return {'error': SECError('filing_content', 'Invalid SEC filing URL format').to_dict()}
        return {'success': True, 'data': {'url': filing_url, 'content_type': 'text/html', 'note': 'Filing content download would be implemented here'}, 'parameters': {'filing_url': filing_url}}
    except Exception as e:
        return {'error': SECError('filing_content', str(e)).to_dict()}

def get_insider_trading(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=100) -> Dict[str, Any]:
    """Get insider trading data (Form 4 filings)"""
    try:
        if not symbol and (not cik):
            return {'error': SECError('insider_trading', 'Either symbol or CIK must be provided').to_dict()}
        filings_result = self.get_company_filings(symbol=symbol, cik=cik, form_type='4', start_date=start_date, end_date=end_date, limit=limit)
        if not filings_result.get('success'):
            return filings_result
        filings_data = filings_result['data']
        insider_trades = []
        for filing in filings_data:
            insider_trade = {'filing_date': filing.get('filingDate'), 'accession_number': filing.get('accessionNumber'), 'company_name': 'Extracted from filing', 'insider_name': 'Extracted from filing', 'transaction_type': 'P', 'securities_transacted': 0, 'price': 0, 'amount': 0, 'ownership_type': 'Direct', 'note': 'Form 4 parsing would be implemented here'}
            insider_trades.append(insider_trade)
        return {'success': True, 'data': insider_trades, 'parameters': {'symbol': symbol, 'cik': str(cik) if cik else None, 'start_date': start_date, 'end_date': end_date, 'limit': limit}}
    except Exception as e:
        return {'error': SECError('insider_trading', str(e)).to_dict()}

def get_institutional_ownership(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=50) -> Dict[str, Any]:
    """Get institutional ownership data (Form 13F filings)"""
    try:
        if not symbol and (not cik):
            return {'error': SECError('institutional_ownership', 'Either symbol or CIK must be provided').to_dict()}
        filings_result = self.get_company_filings(symbol=symbol, cik=cik, form_type='13F-HR', start_date=start_date, end_date=end_date, limit=limit)
        if not filings_result.get('success'):
            return filings_result
        filings_data = filings_result['data']
        institutional_holdings = []
        for filing in filings_data:
            holding = {'filing_date': filing.get('filingDate', ''), 'accession_number': filing.get('accessionNumber', ''), 'institution_name': 'Extracted from filing', 'cusip': 'Extracted from filing', 'security_name': 'Extracted from filing', 'shares': 0, 'market_value': 0, 'note': 'Form 13F parsing would be implemented here'}
            institutional_holdings.append(holding)
        return {'success': True, 'data': institutional_holdings, 'parameters': {'symbol': symbol, 'cik': str(cik) if cik else None, 'start_date': start_date, 'end_date': end_date, 'limit': limit}}
    except Exception as e:
        return {'error': SECError('institutional_ownership', str(e)).to_dict()}

def search_etfs_mutual_funds(self, query: str) -> Dict[str, Any]:
    """Search for ETFs and mutual funds"""
    try:
        if not query:
            return {'error': SECError('search_etfs_mutual_funds', 'Search query is required').to_dict()}
        return self.search_companies(query, is_fund=True)
    except Exception as e:
        return {'error': SECError('search_etfs_mutual_funds', str(e)).to_dict()}

def get_available_form_types(self) -> Dict[str, Any]:
    """Get list of available SEC form types"""
    try:
        form_info = {}
        form_descriptions = {'10-K': "Annual report providing comprehensive overview of company's business and financial condition", '10-Q': 'Quarterly report covering financial performance and operations', '8-K': 'Current report disclosing material events that shareholders should know about', '10-D': 'Annual report for registered investment companies (mutual funds)', '20-F': 'Annual report for foreign private issuers', '40-F': 'Annual report for foreign private issuers (Canadian)', '6-K': 'Current report for foreign private issuers', 'S-1': 'Registration statement for new securities offerings', 'S-3': 'Registration statement for established companies', 'S-4': 'Registration statement for mergers and acquisitions', 'F-1': 'Registration statement for foreign private issuers', '424A': 'Prospectus filed under Rule 424(a)', 'SC 13D': 'Beneficial ownership report (5%+ ownership)', 'SC 13G': 'Beneficial ownership report (passive investor)', '13F-HR': 'Institutional investment manager holdings report', '3': 'Initial statement of beneficial ownership', '4': 'Statement of changes in beneficial ownership (insider trading)', '144': 'Notice of proposed sale of securities'}
        for form_type in self.common_form_types:
            form_info[form_type] = {'description': form_descriptions.get(form_type, 'SEC filing form'), 'frequency': 'Annual' if form_type in ['10-K', '10-D', '20-F', '40-F'] else 'Quarterly' if form_type in ['10-Q'] else 'As needed'}
        return {'success': True, 'data': form_info, 'parameters': {}}
    except Exception as e:
        return {'error': SECError('available_form_types', str(e)).to_dict()}

def get_financial_statements(self, cik: Union[str, int], taxonomy: str='us-gaap', fact_list: Optional[List[str]]=None) -> Dict[str, Any]:
    """Get financial statements data using company facts"""
    try:
        facts_result = self.get_company_facts(cik)
        if not facts_result.get('success'):
            return facts_result
        facts_data = facts_result['data']['facts']
        if fact_list:
            filtered_facts = {k: v for k, v in facts_data.items() if k in fact_list}
        else:
            filtered_facts = facts_data
        return {'success': True, 'data': filtered_facts, 'parameters': {'cik': str(cik), 'taxonomy': taxonomy, 'fact_list': fact_list}}
    except Exception as e:
        return {'error': SECError('financial_statements', str(e)).to_dict()}

def get_company_overview(self, symbol: Optional[str]=None, cik: Optional[Union[str, int]]=None) -> Dict[str, Any]:
    """Get comprehensive company overview including filings, facts, and insider data"""
    try:
        if not symbol and (not cik):
            return {'error': SECError('company_overview', 'Either symbol or CIK must be provided').to_dict()}
        if symbol and (not cik):
            cik_result = self.get_cik_map(symbol)
            if cik_result.get('success'):
                cik = cik_result['data'].get('cik')
        if not cik:
            return {'error': SECError('company_overview', 'CIK not found for the provided symbol').to_dict()}
        results = {}
        filings_result = self.get_company_filings(cik=cik, form_type='10-K,10-Q,8-K', limit=10)
        results['recent_filings'] = filings_result
        facts_result = self.get_company_facts(cik)
        results['company_facts'] = facts_result
        insider_result = self.get_insider_trading(cik=cik, limit=10)
        results['insider_trading'] = insider_result
        has_data = any((result.get('success') and result.get('data') for result in results.values()))
        if not has_data:
            return {'error': SECError('company_overview', f'No data found for CIK: {cik}').to_dict()}
        return {'success': True, 'data': results, 'parameters': {'symbol': symbol, 'cik': str(cik)}}
    except Exception as e:
        return {'error': SECError('company_overview', str(e)).to_dict()}

def get_filings_by_form_type(self, form_type: str, start_date: Optional[str]=None, end_date: Optional[str]=None, limit: Optional[int]=100) -> Dict[str, Any]:
    """Get all filings of a specific form type within date range"""
    try:
        return {'success': True, 'data': [], 'parameters': {'form_type': form_type, 'start_date': start_date, 'end_date': end_date, 'limit': limit}, 'note': "This endpoint requires SEC's advanced search API for full implementation."}
    except Exception as e:
        return {'error': SECError('filings_by_form_type', str(e)).to_dict()}

def main():
    """Main function for CLI interface"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python sec_data.py <command> [args...]', 'commands': ['company_filings [symbol] [cik] [form_type] [start_date] [end_date] [limit]', 'cik_map [symbol]', 'symbol_map [cik]', 'filing_content [filing_url]', 'parse_filing_html [html_content]', 'insider_trading [symbol] [cik] [start_date] [end_date] [limit]', 'institutional_ownership [symbol] [cik] [start_date] [end_date] [limit]', 'search_companies [query] [is_fund]', 'search_etfs_mutual_funds [query]', 'available_form_types', 'company_facts [cik]', 'financial_statements [cik] [taxonomy] [fact_list]', 'company_overview [symbol] [cik]', 'filings_by_form_type [form_type] [start_date] [end_date] [limit]']}))
        sys.exit(1)
    command = sys.argv[1]
    wrapper = SECDataWrapper()
    try:
        if command == 'company_filings':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            cik = sys.argv[3] if len(sys.argv) > 3 else None
            form_type = sys.argv[4] if len(sys.argv) > 4 else None
            start_date = sys.argv[5] if len(sys.argv) > 5 else None
            end_date = sys.argv[6] if len(sys.argv) > 6 else None
            limit = int(sys.argv[7]) if len(sys.argv) > 7 else 100
            result = wrapper.get_company_filings(symbol, cik, form_type, start_date, end_date, limit)
        elif command == 'cik_map':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_cik_map(symbol)
        elif command == 'symbol_map':
            cik = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_symbol_map(cik)
        elif command == 'filing_content':
            filing_url = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_filing_content(filing_url)
        elif command == 'parse_filing_html':
            html_content = sys.argv[2] if len(sys.argv) > 2 else ''
            result = wrapper.parse_filing_html(html_content)
        elif command == 'insider_trading':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            cik = sys.argv[3] if len(sys.argv) > 3 else None
            start_date = sys.argv[4] if len(sys.argv) > 4 else None
            end_date = sys.argv[5] if len(sys.argv) > 5 else None
            limit = int(sys.argv[6]) if len(sys.argv) > 6 else 100
            result = wrapper.get_insider_trading(symbol, cik, start_date, end_date, limit)
        elif command == 'institutional_ownership':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            cik = sys.argv[3] if len(sys.argv) > 3 else None
            start_date = sys.argv[4] if len(sys.argv) > 4 else None
            end_date = sys.argv[5] if len(sys.argv) > 5 else None
            limit = int(sys.argv[6]) if len(sys.argv) > 6 else 50
            result = wrapper.get_institutional_ownership(symbol, cik, start_date, end_date, limit)
        elif command == 'search_companies':
            query = sys.argv[2] if len(sys.argv) > 2 else None
            is_fund = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False
            result = wrapper.search_companies(query, is_fund)
        elif command == 'search_etfs_mutual_funds':
            query = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.search_etfs_mutual_funds(query)
        elif command == 'available_form_types':
            result = wrapper.get_available_form_types()
        elif command == 'company_facts':
            cik = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_company_facts(cik)
        elif command == 'financial_statements':
            cik = sys.argv[2] if len(sys.argv) > 2 else None
            taxonomy = sys.argv[3] if len(sys.argv) > 3 else 'us-gaap'
            fact_list = sys.argv[4].split(',') if len(sys.argv) > 4 else None
            result = wrapper.get_financial_statements(cik, taxonomy, fact_list)
        elif command == 'company_overview':
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            cik = sys.argv[3] if len(sys.argv) > 3 else None
            result = wrapper.get_company_overview(symbol, cik)
        elif command == 'filings_by_form_type':
            form_type = sys.argv[2] if len(sys.argv) > 2 else None
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            limit = int(sys.argv[5]) if len(sys.argv) > 5 else 100
            result = wrapper.get_filings_by_form_type(form_type, start_date, end_date, limit)
        else:
            result = {'error': SECError(command, f'Unknown command: {command}').to_dict()}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': SECError(command, str(e)).to_dict()}, indent=2))

class DataValidator:
    """
    Comprehensive data validation and quality control system.
    """

    def __init__(self, strict_mode: bool=False):
        """
        Initialize data validator.

        Args:
            strict_mode: If True, raises exceptions for quality issues
        """
        self.strict_mode = strict_mode
        self.validation_rules = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default validation rules."""
        self.validation_rules = {'min_observations': 2, 'max_missing_ratio': 0.1, 'outlier_std_threshold': 3.0, 'min_numeric_ratio': 0.95, 'date_format_patterns': ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']}

    def validate_financial_data(self, data: Union[pd.DataFrame, pd.Series, np.ndarray, List], data_type: str='general', data_name: str='data') -> Tuple[Any, DataQualityReport]:
        """
        Comprehensive validation of financial data.

        Args:
            data: Input data to validate
            data_type: Type of financial data ('returns', 'prices', 'rates', 'general')
            data_name: Name for reporting purposes

        Returns:
            Tuple of (cleaned_data, quality_report)
        """
        report = DataQualityReport(data_name)
        try:
            if isinstance(data, (list, tuple)):
                data = pd.Series(data)
            elif isinstance(data, np.ndarray):
                if data.ndim == 1:
                    data = pd.Series(data)
                else:
                    data = pd.DataFrame(data)
            cleaned_data = self._validate_structure(data, report)
            if data_type == 'returns':
                cleaned_data = self._validate_returns(cleaned_data, report)
            elif data_type == 'prices':
                cleaned_data = self._validate_prices(cleaned_data, report)
            elif data_type == 'rates':
                cleaned_data = self._validate_rates(cleaned_data, report)
            self._check_data_quality(cleaned_data, report)
            self._generate_recommendations(cleaned_data, report)
            return (cleaned_data, report)
        except Exception as e:
            report.add_issue('validation_error', f'Validation failed: {str(e)}', 'critical')
            if self.strict_mode:
                raise
            return (data, report)

    def _validate_structure(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate basic data structure."""
        if len(data) == 0:
            report.add_issue('empty_data', 'Dataset is empty', 'critical')
            if self.strict_mode:
                raise ValueError('Dataset is empty')
        if len(data) < self.validation_rules['min_observations']:
            report.add_issue('insufficient_data', f'Only {len(data)} observations, minimum {self.validation_rules['min_observations']} required', 'high')
        if isinstance(data, (pd.DataFrame, pd.Series)):
            if data.index.duplicated().any():
                report.add_warning('duplicate_index', 'Duplicate index values found')
                data = data.loc[~data.index.duplicated(keep='first')]
        report.statistics['total_observations'] = len(data)
        return data

    def _validate_returns(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate return data specifically."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
        else:
            numeric_data = data
        if isinstance(numeric_data, pd.DataFrame):
            for col in numeric_data.columns:
                extreme_returns = numeric_data[col].abs() > 1.0
                if extreme_returns.any():
                    count = extreme_returns.sum()
                    report.add_warning('extreme_returns', f'Column {col}: {count} returns > 100% found')
        else:
            extreme_returns = numeric_data.abs() > 1.0
            if extreme_returns.any():
                count = extreme_returns.sum()
                report.add_warning('extreme_returns', f'{count} returns > 100% found')
        self._check_return_patterns(numeric_data, report)
        return data

    def _validate_prices(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate price data specifically."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
        else:
            numeric_data = data
        if isinstance(numeric_data, pd.DataFrame):
            for col in numeric_data.columns:
                negative_prices = numeric_data[col] <= 0
                if negative_prices.any():
                    count = negative_prices.sum()
                    report.add_issue('negative_prices', f'Column {col}: {count} non-positive prices found', 'high')
        else:
            negative_prices = numeric_data <= 0
            if negative_prices.any():
                count = negative_prices.sum()
                report.add_issue('negative_prices', f'{count} non-positive prices found', 'high')
        self._check_price_jumps(numeric_data, report)
        return data

    def _validate_rates(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate interest rate data specifically."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
        else:
            numeric_data = data
        if isinstance(numeric_data, pd.DataFrame):
            for col in numeric_data.columns:
                high_rates = numeric_data[col] > 1.0
                if high_rates.any():
                    count = high_rates.sum()
                    report.add_warning('high_rates', f'Column {col}: {count} rates > 100% found')
        else:
            high_rates = numeric_data > 1.0
            if high_rates.any():
                count = high_rates.sum()
                report.add_warning('high_rates', f'{count} rates > 100% found')
        return data

    def _check_data_quality(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Perform general data quality checks."""
        self._analyze_missing_data(data, report)
        self._detect_outliers(data, report)
        self._check_data_types(data, report)
        self._generate_statistics(data, report)

    def _analyze_missing_data(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Analyze missing data patterns."""
        if isinstance(data, pd.DataFrame):
            total_cells = data.size
            missing_cells = data.isna().sum().sum()
            missing_ratio = missing_cells / total_cells if total_cells > 0 else 0
            missing_by_column = data.isna().sum()
            for col, missing_count in missing_by_column.items():
                if missing_count > 0:
                    col_ratio = missing_count / len(data)
                    if col_ratio > self.validation_rules['max_missing_ratio']:
                        report.add_issue('high_missing_data', f'Column {col}: {col_ratio:.1%} missing data', 'medium')
        else:
            missing_count = data.isna().sum()
            missing_ratio = missing_count / len(data) if len(data) > 0 else 0
            if missing_ratio > self.validation_rules['max_missing_ratio']:
                report.add_issue('high_missing_data', f'{missing_ratio:.1%} missing data', 'medium')
        report.statistics['missing_data_ratio'] = round(missing_ratio, 4)

    def _detect_outliers(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Detect statistical outliers."""

        def detect_outliers_series(series: pd.Series, name: str=''):
            if not pd.api.types.is_numeric_dtype(series):
                return
            clean_series = series.dropna()
            if len(clean_series) < 3:
                return
            z_scores = np.abs(stats.zscore(clean_series))
            outliers_zscore = z_scores > self.validation_rules['outlier_std_threshold']
            Q1 = clean_series.quantile(0.25)
            Q3 = clean_series.quantile(0.75)
            IQR = Q3 - Q1
            outliers_iqr = (clean_series < Q1 - 1.5 * IQR) | (clean_series > Q3 + 1.5 * IQR)
            outlier_count_z = outliers_zscore.sum()
            outlier_count_iqr = outliers_iqr.sum()
            if outlier_count_z > 0:
                report.add_warning('outliers_zscore', f'{name}Z-score outliers detected: {outlier_count_z}')
            if outlier_count_iqr > 0:
                report.add_warning('outliers_iqr', f'{name}IQR outliers detected: {outlier_count_iqr}')
        if isinstance(data, pd.DataFrame):
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                detect_outliers_series(data[col], f'Column {col}: ')
        else:
            detect_outliers_series(data)

    def _check_data_types(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Check data type consistency."""
        if isinstance(data, pd.DataFrame):
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            total_cols = len(data.columns)
            numeric_ratio = len(numeric_cols) / total_cols if total_cols > 0 else 0
            if numeric_ratio < self.validation_rules['min_numeric_ratio']:
                report.add_warning('low_numeric_ratio', f'Only {numeric_ratio:.1%} of columns are numeric')
            for col in data.columns:
                if data[col].dtype == 'object':
                    sample = data[col].dropna().head(100)
                    if self._looks_like_numeric(sample):
                        report.add_issue('type_mismatch', f'Column {col} contains numeric data stored as text', 'medium')
                    elif self._looks_like_date(sample):
                        report.add_issue('type_mismatch', f'Column {col} contains date data stored as text', 'medium')
        report.statistics['data_types'] = data.dtypes.astype(str).to_dict() if isinstance(data, pd.DataFrame) else str(data.dtype)

    def _looks_like_numeric(self, sample: pd.Series) -> bool:
        """Check if text data looks like it should be numeric."""
        if len(sample) == 0:
            return False
        numeric_pattern = re.compile('^-?\\d*\\.?\\d+([eE][+-]?\\d+)?')
        numeric_count = sample.astype(str).str.match(numeric_pattern).sum()
        return numeric_count / len(sample) > 0.8

    def _looks_like_date(self, sample: pd.Series) -> bool:
        """Check if text data looks like it should be dates."""
        if len(sample) == 0:
            return False
        date_patterns = ['\\d{4}-\\d{2}-\\d{2}', '\\d{2}/\\d{2}/\\d{4}', '\\d{2}-\\d{2}-\\d{4}']
        for pattern in date_patterns:
            matches = sample.astype(str).str.match(pattern).sum()
            if matches / len(sample) > 0.8:
                return True
        return False

    def _generate_statistics(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Generate comprehensive statistics for the data."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                stats_dict = {'shape': data.shape, 'numeric_columns': len(numeric_data.columns), 'total_columns': len(data.columns), 'memory_usage_mb': round(data.memory_usage(deep=True).sum() / 1024 ** 2, 2)}
                desc_stats = numeric_data.describe()
                stats_dict['summary_statistics'] = desc_stats.to_dict()
        elif pd.api.types.is_numeric_dtype(data):
            clean_data = data.dropna()
            stats_dict = {'length': len(data), 'non_null_count': len(clean_data), 'mean': float(clean_data.mean()) if len(clean_data) > 0 else None, 'std': float(clean_data.std()) if len(clean_data) > 1 else None, 'min': float(clean_data.min()) if len(clean_data) > 0 else None, 'max': float(clean_data.max()) if len(clean_data) > 0 else None, 'skewness': float(clean_data.skew()) if len(clean_data) > 2 else None, 'kurtosis': float(clean_data.kurtosis()) if len(clean_data) > 3 else None}
        else:
            stats_dict = {'length': len(data), 'non_null_count': data.notna().sum(), 'unique_values': data.nunique(), 'data_type': str(data.dtype)}
        report.statistics.update(stats_dict)

    def _check_return_patterns(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Check for suspicious patterns in return data."""

        def check_series_patterns(series: pd.Series, name: str=''):
            clean_series = series.dropna()
            if len(clean_series) < 10:
                return
            zero_count = (clean_series == 0).sum()
            zero_ratio = zero_count / len(clean_series)
            if zero_ratio > 0.1:
                report.add_warning('high_zero_returns', f'{name}High proportion of zero returns: {zero_ratio:.1%}')
            if len(clean_series) > 20:
                for window in [5, 10]:
                    if len(clean_series) >= window * 3:
                        rolling_std = clean_series.rolling(window).std()
                        low_variance_periods = (rolling_std < 0.001).sum()
                        if low_variance_periods > len(clean_series) * 0.1:
                            report.add_warning('low_variance_periods', f'{name}Detected periods with suspiciously low variance')
            if len(clean_series) > 30:
                try:
                    jb_stat, jb_pvalue = stats.jarque_bera(clean_series)
                    if jb_pvalue < 0.01:
                        report.add_warning('non_normal_returns', f'{name}Returns significantly deviate from normal distribution')
                except:
                    pass
        if isinstance(data, pd.DataFrame):
            for col in data.select_dtypes(include=[np.number]).columns:
                check_series_patterns(data[col], f'Column {col}: ')
        else:
            check_series_patterns(data)

    def _check_price_jumps(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Check for suspicious price jumps."""

        def check_series_jumps(series: pd.Series, name: str=''):
            clean_series = series.dropna()
            if len(clean_series) < 2:
                return
            price_changes = clean_series.pct_change().dropna()
            large_jumps = price_changes.abs() > 0.5
            if large_jumps.any():
                jump_count = large_jumps.sum()
                report.add_warning('large_price_jumps', f'{name}{jump_count} large price jumps (>50%) detected')
            halving = (price_changes > -0.55) & (price_changes < -0.45)
            doubling = (price_changes > 0.95) & (price_changes < 1.05)
            if halving.any() or doubling.any():
                report.add_warning('potential_splits', f'{name}Potential stock splits/reverse splits detected')
        if isinstance(data, pd.DataFrame):
            for col in data.select_dtypes(include=[np.number]).columns:
                check_series_jumps(data[col], f'Column {col}: ')
        else:
            check_series_jumps(data)

    def _generate_recommendations(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Generate data improvement recommendations."""
        issue_types = [issue['type'] for issue in report.issues]
        warning_types = [warning['type'] for warning in report.warnings]
        if 'high_missing_data' in issue_types:
            report.add_recommendation('Consider using interpolation or forward-fill for missing data')
            report.add_recommendation('Investigate the source of missing data - is it systematic?')
        if 'negative_prices' in issue_types:
            report.add_recommendation('Remove or correct negative price observations')
            report.add_recommendation('Verify data source and collection methodology')
        if 'extreme_returns' in warning_types:
            report.add_recommendation('Review extreme returns - may indicate data errors or corporate actions')
            report.add_recommendation('Consider winsorizing extreme values if confirmed as outliers')
        if 'outliers_zscore' in warning_types or 'outliers_iqr' in warning_types:
            report.add_recommendation('Investigate outliers - may be valid extreme events or data errors')
            report.add_recommendation('Consider robust statistical methods that are less sensitive to outliers')
        if 'type_mismatch' in issue_types:
            report.add_recommendation('Convert text columns to appropriate data types (numeric/datetime)')
            report.add_recommendation('Standardize data formats before importing')
        if 'insufficient_data' in issue_types:
            report.add_recommendation('Collect more historical data for reliable statistical analysis')
            report.add_recommendation('Consider using higher frequency data if available')
        if len(report.recommendations) == 0:
            report.add_recommendation('Data quality appears good - proceed with analysis')

    def clean_data(self, data: Union[pd.DataFrame, pd.Series], method: str='conservative', **kwargs) -> Union[pd.DataFrame, pd.Series]:
        """
        Clean data based on validation results.

        Args:
            data: Data to clean
            method: Cleaning method ('conservative', 'aggressive', 'custom')
            **kwargs: Additional parameters for cleaning

        Returns:
            Cleaned data
        """
        cleaned_data = data.copy()
        if method == 'conservative':
            if isinstance(cleaned_data, pd.DataFrame):
                cleaned_data = cleaned_data.dropna(how='all')
                numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if 'price' in col.lower():
                        cleaned_data = cleaned_data[cleaned_data[col] > 0]
            else:
                cleaned_data = cleaned_data.dropna()
        elif method == 'aggressive':
            if isinstance(cleaned_data, pd.DataFrame):
                missing_ratio = cleaned_data.isna().mean()
                cols_to_keep = missing_ratio[missing_ratio <= 0.5].index
                cleaned_data = cleaned_data[cols_to_keep]
                numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    Q1 = cleaned_data[col].quantile(0.25)
                    Q3 = cleaned_data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    cleaned_data = cleaned_data[(cleaned_data[col] >= lower_bound) & (cleaned_data[col] <= upper_bound)]
            else:
                Q1 = cleaned_data.quantile(0.25)
                Q3 = cleaned_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                cleaned_data = cleaned_data[(cleaned_data >= lower_bound) & (cleaned_data <= upper_bound)]
        return cleaned_data

    def validate_date_range(self, dates: Union[pd.DatetimeIndex, pd.Series, List], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None) -> Tuple[bool, List[str]]:
        """
        Validate date range and continuity.

        Args:
            dates: Date data to validate
            start_date: Expected start date
            end_date: Expected end date

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        try:
            if isinstance(dates, list):
                dates = pd.to_datetime(dates)
            elif isinstance(dates, pd.Series):
                dates = pd.to_datetime(dates)
            if dates.duplicated().any():
                issues.append('Duplicate dates found')
            if not dates.is_monotonic_increasing:
                issues.append('Dates are not in chronological order')
            if start_date and dates.min() < start_date:
                issues.append(f'Data starts before expected date: {start_date}')
            if end_date and dates.max() > end_date:
                issues.append(f'Data ends after expected date: {end_date}')
            if len(dates) > 1:
                date_diffs = dates.to_series().diff().dropna()
                median_diff = date_diffs.median()
                large_gaps = date_diffs > median_diff * 5
                if large_gaps.any():
                    gap_count = large_gaps.sum()
                    issues.append(f'Found {gap_count} large gaps in date sequence')
            return (len(issues) == 0, issues)
        except Exception as e:
            issues.append(f'Date validation error: {str(e)}')
            return (False, issues)

    def validate_correlation_matrix(self, corr_matrix: pd.DataFrame, tolerance: float=1e-06) -> Tuple[bool, List[str]]:
        """
        Validate correlation matrix properties.

        Args:
            corr_matrix: Correlation matrix to validate
            tolerance: Numerical tolerance for validation

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        try:
            if corr_matrix.shape[0] != corr_matrix.shape[1]:
                issues.append('Correlation matrix is not square')
                return (False, issues)
            if not np.allclose(corr_matrix.values, corr_matrix.values.T, atol=tolerance):
                issues.append('Correlation matrix is not symmetric')
            diagonal = np.diag(corr_matrix.values)
            if not np.allclose(diagonal, 1.0, atol=tolerance):
                issues.append('Diagonal elements are not equal to 1')
            if (corr_matrix.values < -1 - tolerance).any() or (corr_matrix.values > 1 + tolerance).any():
                issues.append('Correlation values outside [-1, 1] range')
            off_diagonal = corr_matrix.values[~np.eye(corr_matrix.shape[0], dtype=bool)]
            perfect_corrs = np.abs(off_diagonal) > 1 - tolerance
            if perfect_corrs.any():
                issues.append('Perfect correlations detected (may indicate data issues)')
            eigenvals = np.linalg.eigvals(corr_matrix.values)
            if (eigenvals < -tolerance).any():
                issues.append('Correlation matrix is not positive semi-definite')
            return (len(issues) == 0, issues)
        except Exception as e:
            issues.append(f'Correlation matrix validation error: {str(e)}')
            return (False, issues)

    def validate_portfolio_weights(self, weights: Union[List, np.ndarray, pd.Series], tolerance: float=1e-06) -> Tuple[bool, List[str]]:
        """
        Validate portfolio weights.

        Args:
            weights: Portfolio weights to validate
            tolerance: Numerical tolerance

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        try:
            weights = np.array(weights)
            weights_sum = np.sum(weights)
            if not np.isclose(weights_sum, 1.0, atol=tolerance):
                issues.append(f'Weights sum to {weights_sum:.6f}, not 1.0')
            if (weights < -tolerance).any():
                negative_count = (weights < -tolerance).sum()
                issues.append(f'Found {negative_count} negative weights (short positions)')
            very_small = np.abs(weights) < tolerance
            if very_small.any():
                small_count = very_small.sum()
                issues.append(f'Found {small_count} very small weights (< {tolerance})')
            return (len(issues) == 0, issues)
        except Exception as e:
            issues.append(f'Portfolio weights validation error: {str(e)}')
            return (False, issues)

def _looks_like_numeric(self, sample: pd.Series) -> bool:
    """Check if text data looks like it should be numeric."""
    if len(sample) == 0:
        return False
    numeric_pattern = re.compile('^-?\\d*\\.?\\d+([eE][+-]?\\d+)?')
    numeric_count = sample.astype(str).str.match(numeric_pattern).sum()
    return numeric_count / len(sample) > 0.8

def _looks_like_date(self, sample: pd.Series) -> bool:
    """Check if text data looks like it should be dates."""
    if len(sample) == 0:
        return False
    date_patterns = ['\\d{4}-\\d{2}-\\d{2}', '\\d{2}/\\d{2}/\\d{4}', '\\d{2}-\\d{2}-\\d{4}']
    for pattern in date_patterns:
        matches = sample.astype(str).str.match(pattern).sum()
        if matches / len(sample) > 0.8:
            return True
    return False

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

def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
    """Return comprehensive key metrics from all analyzers"""
    income_metrics = self.income_analyzer.get_key_metrics(statements)
    balance_metrics = self.balance_analyzer.get_key_metrics(statements)
    cash_flow_metrics = self.cash_flow_analyzer.get_key_metrics(statements)
    all_metrics = {**income_metrics, **balance_metrics, **cash_flow_metrics}
    return all_metrics

def _fetch_data_in_process(indicator_config, params):
    """Function to run in separate process for complete isolation"""
    try:
        import asyncio
        from fincept_terminal.DatabaseConnector.DataSources.oced_data.oced_provider import OECDProvider
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            provider = OECDProvider()
            method = getattr(provider, indicator_config['method'])
            result = loop.run_until_complete(method(**params))
            if hasattr(provider, 'close'):
                loop.run_until_complete(provider.close())
            return result
        finally:
            loop.close()
    except Exception as e:
        return {'success': False, 'error': str(e)}

class DataViewerTab(BaseTab):
    """Enhanced Data Viewer tab for displaying comprehensive financial data from Alpha Vantage and other providers"""

    def __init__(self, app):
        print('🔧 DEBUG: DataViewerTab.__init__ called')
        try:
            super().__init__(app)
            print('🔧 DEBUG: BaseTab.__init__ completed')
            self.tab_id = str(uuid.uuid4())[:8]
            self.data_source_manager = get_data_source_manager(app)
            print(f'🔧 DEBUG: DataSourceManager: {self.data_source_manager}')
            self.current_data = {}
            self.last_refresh = None
            self.auto_refresh = False
            self.refresh_interval = 30
            self.refresh_thread = None
            self._stop_refresh = False
            self.data_types = {'Stock Data': {'Time Series Daily': 'get_stock_data', 'Time Series Intraday': 'get_stock_data', 'Time Series Weekly': 'get_weekly_data', 'Time Series Monthly': 'get_monthly_data', 'Daily Adjusted': 'get_daily_adjusted', 'Weekly Adjusted': 'get_weekly_adjusted', 'Monthly Adjusted': 'get_monthly_adjusted', 'Global Quote': 'get_global_quote', 'Symbol Search': 'search_symbols'}, 'Fundamental Data': {'Company Overview': 'get_company_overview', 'Income Statement': 'get_income_statement', 'Balance Sheet': 'get_balance_sheet', 'Cash Flow': 'get_cash_flow', 'Earnings': 'get_earnings', 'Earnings Estimates': 'get_earnings_estimates', 'Dividends': 'get_dividends', 'Splits': 'get_splits'}, 'Technical Indicators': {'SMA': 'get_sma', 'EMA': 'get_ema', 'RSI': 'get_rsi', 'MACD': 'get_macd', 'Bollinger Bands': 'get_bbands', 'Stochastic': 'get_stoch', 'ADX': 'get_adx', 'VWAP': 'get_vwap'}, 'Forex': {'Currency Exchange Rate': 'get_currency_exchange_rate', 'FX Daily': 'get_forex_data', 'FX Intraday': 'get_fx_intraday', 'FX Weekly': 'get_fx_weekly', 'FX Monthly': 'get_fx_monthly'}, 'Cryptocurrency': {'Crypto Daily': 'get_crypto_data', 'Crypto Intraday': 'get_crypto_intraday', 'Digital Currency Weekly': 'get_digital_currency_weekly', 'Digital Currency Monthly': 'get_digital_currency_monthly'}, 'Commodities': {'WTI Oil': 'get_wti_oil', 'Brent Oil': 'get_brent_oil', 'Natural Gas': 'get_natural_gas', 'Gold': 'get_copper', 'Silver': 'get_aluminum'}, 'Economic Indicators': {'Real GDP': 'get_real_gdp', 'Unemployment': 'get_unemployment', 'CPI': 'get_cpi', 'Treasury Yield': 'get_treasury_yield', 'Federal Funds Rate': 'get_federal_funds_rate'}, 'Market Intelligence': {'News Sentiment': 'get_news_sentiment', 'Top Gainers/Losers': 'get_top_gainers_losers', 'Insider Transactions': 'get_insider_transactions'}}
            print('✅ DEBUG: DataViewerTab initialization completed successfully')
        except Exception as e:
            print(f'❌ DEBUG: Error in DataViewerTab.__init__: {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
            raise

    def get_label(self):
        return 'Data Viewer'

    def safe_add_item(self, add_function, *args, **kwargs):
        """Safely add DPG items with error handling"""
        try:
            return add_function(*args, **kwargs)
        except Exception as e:
            print(f'❌ DEBUG: Error adding item {add_function.__name__}: {str(e)}')
            try:
                if 'tag' in kwargs:
                    kwargs['tag'] = f'{kwargs['tag']}_{self.tab_id}'
                return add_function(*args, **kwargs)
            except:
                print(f'❌ DEBUG: Failed to add {add_function.__name__} even with modified tag')
                return None

    def create_content(self):
        """Create the enhanced data viewer interface"""
        print('🔧 DEBUG: create_content() called')
        try:
            self.add_section_header('📊 Advanced Financial Data Viewer')
            self.safe_add_item(dpg.add_text, 'Access comprehensive financial data from Alpha Vantage and other providers', color=[200, 200, 200])
            self.safe_add_item(dpg.add_spacer, height=20)
            with dpg.child_window(height=800, border=True):
                self.create_control_panel()
                self.safe_add_item(dpg.add_separator)
                self.safe_add_item(dpg.add_spacer, height=10)
                self.create_data_display()
            print('✅ DEBUG: create_content() completed successfully')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_content(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
            try:
                self.safe_add_item(dpg.add_text, f'Error creating content: {str(e)}', color=[255, 100, 100])
            except:
                pass

    def create_control_panel(self):
        """Create enhanced control panel"""
        print('🔧 DEBUG: create_control_panel() called')
        try:
            self.safe_add_item(dpg.add_text, '🎛️ Data Controls', color=[255, 255, 100])
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Category:', width=100)
                self.safe_add_item(dpg.add_combo, list(self.data_types.keys()), tag=f'data_category_{self.tab_id}', default_value='Stock Data', width=150, callback=self.on_category_change)
                self.safe_add_item(dpg.add_text, 'Data Type:', width=100)
                self.safe_add_item(dpg.add_combo, list(self.data_types['Stock Data'].keys()), tag=f'data_type_{self.tab_id}', default_value='Time Series Daily', width=150)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Symbol:', width=100)
                self.safe_add_item(dpg.add_input_text, tag=f'symbol_input_{self.tab_id}', default_value='AAPL', width=100, hint='e.g., AAPL, EURUSD, BTC')
                self.safe_add_item(dpg.add_text, 'Period:', width=100)
                self.safe_add_item(dpg.add_combo, ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'], tag=f'period_combo_{self.tab_id}', default_value='1d', width=80)
                self.safe_add_item(dpg.add_text, 'Interval:', width=100)
                self.safe_add_item(dpg.add_combo, ['1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'], tag=f'interval_combo_{self.tab_id}', default_value='daily', width=80)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True, tag=f'tech_params_{self.tab_id}', show=False):
                self.safe_add_item(dpg.add_text, 'Time Period:', width=100)
                self.safe_add_item(dpg.add_input_int, tag=f'time_period_{self.tab_id}', default_value=14, width=60, min_value=1, max_value=200)
                self.safe_add_item(dpg.add_text, 'Series Type:', width=100)
                self.safe_add_item(dpg.add_combo, ['close', 'open', 'high', 'low'], tag=f'series_type_{self.tab_id}', default_value='close', width=80)
            with dpg.group(horizontal=True, tag=f'forex_params_{self.tab_id}', show=False):
                self.safe_add_item(dpg.add_text, 'From Currency:', width=100)
                self.safe_add_item(dpg.add_input_text, tag=f'from_currency_{self.tab_id}', default_value='USD', width=60)
                self.safe_add_item(dpg.add_text, 'To Currency:', width=100)
                self.safe_add_item(dpg.add_input_text, tag=f'to_currency_{self.tab_id}', default_value='EUR', width=60)
            self.safe_add_item(dpg.add_spacer, height=15)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_button, label='🔄 Fetch Data', tag=f'fetch_btn_{self.tab_id}', callback=self.fetch_data, width=120)
                self.safe_add_item(dpg.add_button, label='🧹 Clear', tag=f'clear_btn_{self.tab_id}', callback=self.clear_data, width=80)
                self.safe_add_item(dpg.add_checkbox, label='Auto Refresh (30s)', tag=f'auto_refresh_{self.tab_id}', callback=self.toggle_auto_refresh)
                self.safe_add_item(dpg.add_button, label='📋 Export CSV', tag=f'export_btn_{self.tab_id}', callback=self.export_data, width=120)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Status:', color=[150, 150, 150])
                self.safe_add_item(dpg.add_text, 'Ready', tag=f'status_text_{self.tab_id}', color=[100, 255, 100])
                self.safe_add_item(dpg.add_text, ' | Last Updated:', color=[150, 150, 150])
                self.safe_add_item(dpg.add_text, 'Never', tag=f'last_update_{self.tab_id}', color=[150, 150, 150])
            print('✅ DEBUG: create_control_panel() completed')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_control_panel(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')

    def create_data_display(self):
        """Create comprehensive data display area"""
        print('🔧 DEBUG: create_data_display() called')
        try:
            self.safe_add_item(dpg.add_text, '📈 Data Display', color=[255, 255, 100])
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.tab_bar(tag=f'display_tabs_{self.tab_id}'):
                with dpg.tab(label='📊 Overview', tag=f'overview_tab_{self.tab_id}'):
                    self.create_overview_display()
                with dpg.tab(label='📈 Time Series', tag=f'timeseries_tab_{self.tab_id}'):
                    self.create_timeseries_display()
                with dpg.tab(label='💼 Fundamentals', tag=f'fundamentals_tab_{self.tab_id}'):
                    self.create_fundamentals_display()
                with dpg.tab(label='📐 Technical', tag=f'technical_tab_{self.tab_id}'):
                    self.create_technical_display()
                with dpg.tab(label='🔍 Raw Data', tag=f'raw_tab_{self.tab_id}'):
                    self.create_raw_display()
                with dpg.tab(label='🔧 Provider Info', tag=f'provider_tab_{self.tab_id}'):
                    self.create_provider_display()
            print('✅ DEBUG: create_data_display() completed')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_data_display(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')

    def create_overview_display(self):
        """Create overview display for key metrics"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                with dpg.child_window(width=200, height=120, border=True):
                    self.safe_add_item(dpg.add_text, 'Current Price', color=[255, 255, 100])
                    self.safe_add_item(dpg.add_separator)
                    self.safe_add_item(dpg.add_text, 'N/A', tag=f'overview_price_{self.tab_id}', color=[100, 255, 100])
                    self.safe_add_item(dpg.add_text, 'Change: N/A', tag=f'overview_change_{self.tab_id}', color=[200, 200, 200])
                with dpg.child_window(width=200, height=120, border=True):
                    self.safe_add_item(dpg.add_text, 'Volume/Activity', color=[255, 255, 100])
                    self.safe_add_item(dpg.add_separator)
                    self.safe_add_item(dpg.add_text, 'N/A', tag=f'overview_volume_{self.tab_id}', color=[200, 200, 200])
                    self.safe_add_item(dpg.add_text, 'Avg: N/A', tag=f'overview_avg_volume_{self.tab_id}', color=[200, 200, 200])
                with dpg.child_window(width=200, height=120, border=True):
                    self.safe_add_item(dpg.add_text, 'Price Range', color=[255, 255, 100])
                    self.safe_add_item(dpg.add_separator)
                    self.safe_add_item(dpg.add_text, 'High: N/A', tag=f'overview_high_{self.tab_id}', color=[100, 255, 100])
                    self.safe_add_item(dpg.add_text, 'Low: N/A', tag=f'overview_low_{self.tab_id}', color=[255, 100, 100])
            self.safe_add_item(dpg.add_spacer, height=20)
            self.safe_add_item(dpg.add_text, '📋 Data Information', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            self.safe_add_item(dpg.add_spacer, height=5)
            with dpg.table(tag=f'overview_info_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True):
                dpg.add_table_column(label='Property')
                dpg.add_table_column(label='Value')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_overview_display(): {str(e)}')

    def create_timeseries_display(self):
        """Create time series data display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Show Last:')
                self.safe_add_item(dpg.add_combo, ['10', '25', '50', '100', 'All'], tag=f'timeseries_limit_{self.tab_id}', default_value='25', width=80)
                self.safe_add_item(dpg.add_button, label='🔄 Refresh View', callback=self.refresh_timeseries_view, width=120)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.table(tag=f'timeseries_table_{self.tab_id}', header_row=True, resizable=True, borders_innerH=True, borders_innerV=True, borders_outerH=True, borders_outerV=True, scrollY=True, height=400):
                dpg.add_table_column(label='Date/Time', width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label='Open', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='High', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Low', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Close', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Volume', width_fixed=True, init_width_or_weight=100)
        except Exception as e:
            print(f'❌ DEBUG: Error in create_timeseries_display(): {str(e)}')

    def create_fundamentals_display(self):
        """Create fundamentals data display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '🏢 Company Information', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'company_info_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=150):
                dpg.add_table_column(label='Property')
                dpg.add_table_column(label='Value')
            self.safe_add_item(dpg.add_spacer, height=15)
            self.safe_add_item(dpg.add_text, '📊 Financial Statements', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.tab_bar(tag=f'financial_tabs_{self.tab_id}'):
                with dpg.tab(label='Income Statement'):
                    with dpg.table(tag=f'income_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                        dpg.add_table_column(label='Item')
                        dpg.add_table_column(label='Value')
                with dpg.tab(label='Balance Sheet'):
                    with dpg.table(tag=f'balance_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                        dpg.add_table_column(label='Item')
                        dpg.add_table_column(label='Value')
                with dpg.tab(label='Cash Flow'):
                    with dpg.table(tag=f'cashflow_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                        dpg.add_table_column(label='Item')
                        dpg.add_table_column(label='Value')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_fundamentals_display(): {str(e)}')

    def create_technical_display(self):
        """Create technical analysis display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '📐 Technical Indicators', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'technical_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=300):
                dpg.add_table_column(label='Date/Time')
                dpg.add_table_column(label='Indicator')
                dpg.add_table_column(label='Value')
                dpg.add_table_column(label='Signal')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_technical_display(): {str(e)}')

    def create_raw_display(self):
        """Create raw data display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '🔍 Raw API Response', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            self.safe_add_item(dpg.add_spacer, height=5)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_button, label='📋 Copy to Clipboard', callback=self.copy_raw_data, width=150)
                self.safe_add_item(dpg.add_button, label='💾 Save to File', callback=self.save_raw_data, width=120)
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_input_text, tag=f'raw_data_display_{self.tab_id}', multiline=True, height=400, width=-1, readonly=True, default_value='No data loaded yet...')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_raw_display(): {str(e)}')

    def create_provider_display(self):
        """Create provider information display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '🔧 Provider Information', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'provider_info_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True):
                dpg.add_table_column(label='Property')
                dpg.add_table_column(label='Value')
            self.safe_add_item(dpg.add_spacer, height=15)
            self.safe_add_item(dpg.add_text, '📋 Available Endpoints', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'endpoints_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                dpg.add_table_column(label='Category')
                dpg.add_table_column(label='Endpoint')
                dpg.add_table_column(label='Status')
            self.populate_endpoints_table()
        except Exception as e:
            print(f'❌ DEBUG: Error in create_provider_display(): {str(e)}')

    def populate_endpoints_table(self):
        """Populate the endpoints table with available data types"""
        try:
            table_tag = f'endpoints_table_{self.tab_id}'
            if not dpg.does_item_exist(table_tag):
                return
            for category, endpoints in self.data_types.items():
                for endpoint_name, method_name in endpoints.items():
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text(category)
                        dpg.add_text(endpoint_name)
                        if hasattr(self.data_source_manager, method_name) if self.data_source_manager else False:
                            dpg.add_text('✅ Available', color=[100, 255, 100])
                        else:
                            dpg.add_text('❌ Not Available', color=[255, 100, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in populate_endpoints_table(): {str(e)}')

    def on_category_change(self, sender, app_data):
        """Handle category change to update data type options"""
        try:
            category = app_data
            data_type_combo = f'data_type_{self.tab_id}'
            if category in self.data_types:
                dpg.configure_item(data_type_combo, items=list(self.data_types[category].keys()))
                dpg.set_value(data_type_combo, list(self.data_types[category].keys())[0])
                self.update_parameter_visibility(category)
        except Exception as e:
            print(f'❌ DEBUG: Error in on_category_change(): {str(e)}')

    def update_parameter_visibility(self, category):
        """Update visibility of parameter groups based on selected category"""
        try:
            dpg.configure_item(f'tech_params_{self.tab_id}', show=False)
            dpg.configure_item(f'forex_params_{self.tab_id}', show=False)
            if category == 'Technical Indicators':
                dpg.configure_item(f'tech_params_{self.tab_id}', show=True)
            elif category == 'Forex':
                dpg.configure_item(f'forex_params_{self.tab_id}', show=True)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_parameter_visibility(): {str(e)}')

    def fetch_data(self):
        """Fetch data based on current selections"""
        try:
            if not self.data_source_manager:
                self.update_status('❌ Data Source Manager not available', [255, 100, 100])
                return
            category = dpg.get_value(f'data_category_{self.tab_id}')
            data_type = dpg.get_value(f'data_type_{self.tab_id}')
            symbol = dpg.get_value(f'symbol_input_{self.tab_id}').strip().upper()
            if not symbol and category not in ['Economic Indicators', 'Market Intelligence']:
                self.update_status('❌ Please enter a symbol', [255, 100, 100])
                return
            self.update_status('🔄 Fetching data...', [255, 255, 100])
            thread = threading.Thread(target=self._fetch_data_async, args=(category, data_type, symbol))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f'❌ DEBUG: Error in fetch_data(): {str(e)}')
            self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

    def _fetch_data_async(self, category: str, data_type: str, symbol: str):
        """Fetch data asynchronously"""
        try:
            print(f'🔧 DEBUG: Fetching {category} - {data_type} for {symbol}')
            if category not in self.data_types or data_type not in self.data_types[category]:
                self.update_status('❌ Invalid data type selection', [255, 100, 100])
                return
            method_name = self.data_types[category][data_type]
            if not hasattr(self.data_source_manager, method_name):
                self.update_status(f'❌ Method {method_name} not available', [255, 100, 100])
                return
            method = getattr(self.data_source_manager, method_name)
            params = self._prepare_method_parameters(category, data_type, symbol)
            if asyncio.iscoroutinefunction(method):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data = loop.run_until_complete(method(**params))
                finally:
                    loop.close()
            else:
                data = method(**params)
            print(f'🔧 DEBUG: Data fetch result: {(data.get('success', False) if isinstance(data, dict) else 'Unknown')}')
            if isinstance(data, dict) and data.get('success'):
                self.current_data = data
                self.update_all_displays(data, category, data_type, symbol)
                self.update_status('✅ Data loaded successfully', [100, 255, 100])
                self.last_refresh = datetime.now()
                dpg.set_value(f'last_update_{self.tab_id}', self.last_refresh.strftime('%H:%M:%S'))
            else:
                error_msg = data.get('error', 'Unknown error') if isinstance(data, dict) else str(data)
                self.update_status(f'❌ {error_msg}', [255, 100, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in _fetch_data_async(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
            self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

    def _prepare_method_parameters(self, category: str, data_type: str, symbol: str) -> Dict[str, Any]:
        """Prepare parameters for the API method call"""
        params = {}
        try:
            if symbol and category not in ['Economic Indicators', 'Market Intelligence', 'Commodities']:
                params['symbol'] = symbol
            time_series_methods = ['Time Series Daily', 'Time Series Intraday', 'Time Series Weekly', 'Time Series Monthly', 'Daily Adjusted', 'Weekly Adjusted', 'Monthly Adjusted', 'FX Daily', 'FX Intraday', 'FX Weekly', 'FX Monthly', 'Crypto Daily', 'Crypto Intraday', 'Digital Currency Weekly', 'Digital Currency Monthly']
            if data_type in time_series_methods:
                if dpg.does_item_exist(f'period_combo_{self.tab_id}'):
                    params['period'] = dpg.get_value(f'period_combo_{self.tab_id}')
                if dpg.does_item_exist(f'interval_combo_{self.tab_id}'):
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}')
            if category == 'Technical Indicators':
                if dpg.does_item_exist(f'time_period_{self.tab_id}'):
                    params['time_period'] = dpg.get_value(f'time_period_{self.tab_id}')
                if dpg.does_item_exist(f'series_type_{self.tab_id}'):
                    params['series_type'] = dpg.get_value(f'series_type_{self.tab_id}')
                if dpg.does_item_exist(f'interval_combo_{self.tab_id}'):
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}')
            elif category == 'Forex':
                if data_type == 'Currency Exchange Rate':
                    params['from_currency'] = dpg.get_value(f'from_currency_{self.tab_id}') if dpg.does_item_exist(f'from_currency_{self.tab_id}') else 'USD'
                    params['to_currency'] = dpg.get_value(f'to_currency_{self.tab_id}') if dpg.does_item_exist(f'to_currency_{self.tab_id}') else 'EUR'
                    params.pop('symbol', None)
                elif data_type in ['FX Daily', 'FX Intraday', 'FX Weekly', 'FX Monthly']:
                    params['from_symbol'] = dpg.get_value(f'from_currency_{self.tab_id}') if dpg.does_item_exist(f'from_currency_{self.tab_id}') else 'USD'
                    params['to_symbol'] = dpg.get_value(f'to_currency_{self.tab_id}') if dpg.does_item_exist(f'to_currency_{self.tab_id}') else 'EUR'
                    params.pop('symbol', None)
            elif category == 'Cryptocurrency':
                if data_type in ['Crypto Intraday', 'Digital Currency Weekly', 'Digital Currency Monthly']:
                    params['market'] = 'USD'
            elif category == 'Economic Indicators':
                params.pop('symbol', None)
                if data_type == 'Treasury Yield':
                    params['maturity'] = '10year'
                    params['interval'] = 'monthly'
                elif data_type in ['Real GDP', 'CPI', 'Federal Funds Rate']:
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}') if dpg.does_item_exist(f'interval_combo_{self.tab_id}') else 'monthly'
            elif category == 'Commodities':
                params.pop('symbol', None)
                if dpg.does_item_exist(f'interval_combo_{self.tab_id}'):
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}')
                else:
                    params['interval'] = 'monthly'
            elif category == 'Market Intelligence':
                if data_type == 'Top Gainers/Losers':
                    params.pop('symbol', None)
                elif data_type == 'News Sentiment':
                    if symbol:
                        params['tickers'] = symbol
                    params.pop('symbol', None)
                elif data_type == 'Insider Transactions':
                    pass
            fundamental_methods = ['Company Overview', 'Income Statement', 'Balance Sheet', 'Cash Flow', 'Earnings', 'Earnings Estimates', 'Dividends', 'Splits']
            if data_type in fundamental_methods:
                params = {k: v for k, v in params.items() if k == 'symbol'}
            stock_methods = ['Time Series Daily', 'Time Series Intraday', 'Time Series Weekly', 'Time Series Monthly', 'Daily Adjusted', 'Weekly Adjusted', 'Monthly Adjusted', 'Global Quote', 'Symbol Search']
            if data_type == 'Symbol Search':
                if symbol:
                    params = {'keywords': symbol}
                else:
                    params = {'keywords': 'apple'}
            print(f'🔧 DEBUG: Prepared parameters for {category}/{data_type}: {params}')
            return params
        except Exception as e:
            print(f'❌ DEBUG: Error preparing parameters: {str(e)}')
            return {'symbol': symbol} if symbol else {}

    def update_all_displays(self, data: Dict[str, Any], category: str, data_type: str, symbol: str):
        """Update all display tabs with fetched data"""
        try:
            self.update_overview_display(data, category, data_type, symbol)
            if 'data' in data and isinstance(data['data'], dict):
                self.update_timeseries_display(data['data'])
            if category == 'Fundamental Data':
                self.update_fundamentals_display(data, data_type)
            if category == 'Technical Indicators':
                self.update_technical_display(data, data_type)
            self.update_raw_display(data)
            self.update_provider_info(data)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_all_displays(): {str(e)}')

    def update_overview_display(self, data: Dict[str, Any], category: str, data_type: str, symbol: str):
        """Update overview display with key metrics"""
        try:
            price_value = 'N/A'
            change_value = 'N/A'
            volume_value = 'N/A'
            high_value = 'N/A'
            low_value = 'N/A'
            if category == 'Stock Data':
                if data_type == 'Global Quote' and 'data' in data:
                    quote_data = data['data']
                    price_value = f'${quote_data.get('price', 0):.2f}'
                    change_value = f'{quote_data.get('change', 0):.2f} ({quote_data.get('change_percent', '0%')})'
                    volume_value = f'{quote_data.get('volume', 0):,}'
                    high_value = f'${quote_data.get('high', 0):.2f}'
                    low_value = f'${quote_data.get('low', 0):.2f}'
                elif 'current_price' in data:
                    price_value = f'${data['current_price']:.2f}'
                elif 'data' in data and isinstance(data['data'], dict):
                    if 'close' in data['data'] and data['data']['close']:
                        price_value = f'${data['data']['close'][-1]:.2f}'
                        if 'high' in data['data'] and data['data']['high']:
                            high_value = f'${max(data['data']['high']):.2f}'
                        if 'low' in data['data'] and data['data']['low']:
                            low_value = f'${min(data['data']['low']):.2f}'
                        if 'volume' in data['data'] and data['data']['volume']:
                            avg_volume = sum(data['data']['volume']) // len(data['data']['volume'])
                            volume_value = f'{avg_volume:,}'
            elif category == 'Forex':
                if 'current_rate' in data:
                    price_value = f'{data['current_rate']:.4f}'
                elif 'data' in data and 'exchange_rate' in data['data']:
                    price_value = f'{data['data']['exchange_rate']:.4f}'
            elif category == 'Cryptocurrency':
                if 'current_price' in data:
                    price_value = f'${data['current_price']:.2f}'
            dpg.set_value(f'overview_price_{self.tab_id}', price_value)
            dpg.set_value(f'overview_change_{self.tab_id}', f'Change: {change_value}')
            dpg.set_value(f'overview_volume_{self.tab_id}', volume_value)
            dpg.set_value(f'overview_high_{self.tab_id}', f'High: {high_value}')
            dpg.set_value(f'overview_low_{self.tab_id}', f'Low: {low_value}')
            self.update_info_table(data, symbol, category, data_type)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_overview_display(): {str(e)}')

    def update_info_table(self, data: Dict[str, Any], symbol: str, category: str, data_type: str):
        """Update the overview info table"""
        try:
            table_tag = f'overview_info_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Symbol')
                dpg.add_text(symbol)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Category')
                dpg.add_text(category)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Data Type')
                dpg.add_text(data_type)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Source')
                dpg.add_text(data.get('source', 'Unknown'))
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Fetched At')
                dpg.add_text(data.get('fetched_at', 'Unknown'))
            if 'data' in data and isinstance(data['data'], dict):
                data_info = data['data']
                for key, value in data_info.items():
                    if key not in ['timestamps', 'open', 'high', 'low', 'close', 'volume'] and (not isinstance(value, list)):
                        with dpg.table_row(parent=table_tag):
                            dpg.add_text(key.replace('_', ' ').title())
                            dpg.add_text(str(value)[:50] + '...' if len(str(value)) > 50 else str(value))
        except Exception as e:
            print(f'❌ DEBUG: Error in update_info_table(): {str(e)}')

    def update_timeseries_display(self, data: Dict[str, Any]):
        """Update time series data table"""
        try:
            table_tag = f'timeseries_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            if not all((key in data for key in ['timestamps'])):
                return
            timestamps = data.get('timestamps', [])
            opens = data.get('open', [])
            highs = data.get('high', [])
            lows = data.get('low', [])
            closes = data.get('close', [])
            volumes = data.get('volume', [])
            limit_str = dpg.get_value(f'timeseries_limit_{self.tab_id}') if dpg.does_item_exist(f'timeseries_limit_{self.tab_id}') else '25'
            limit = len(timestamps) if limit_str == 'All' else min(int(limit_str), len(timestamps))
            for i in range(min(limit, len(timestamps))):
                idx = len(timestamps) - 1 - i
                with dpg.table_row(parent=table_tag):
                    dpg.add_text(timestamps[idx] if idx < len(timestamps) else 'N/A')
                    dpg.add_text(f'{opens[idx]:.2f}' if idx < len(opens) and opens[idx] else 'N/A')
                    dpg.add_text(f'{highs[idx]:.2f}' if idx < len(highs) and highs[idx] else 'N/A')
                    dpg.add_text(f'{lows[idx]:.2f}' if idx < len(lows) and lows[idx] else 'N/A')
                    dpg.add_text(f'{closes[idx]:.2f}' if idx < len(closes) and closes[idx] else 'N/A')
                    dpg.add_text(f'{volumes[idx]:,}' if idx < len(volumes) and volumes[idx] else 'N/A')
        except Exception as e:
            print(f'❌ DEBUG: Error in update_timeseries_display(): {str(e)}')

    def update_fundamentals_display(self, data: Dict[str, Any], data_type: str):
        """Update fundamentals display based on data type"""
        try:
            if data_type == 'Company Overview':
                self.update_company_info_table(data.get('data', {}))
            elif data_type == 'Income Statement':
                self.update_financial_table('income_table', data.get('data', {}))
            elif data_type == 'Balance Sheet':
                self.update_financial_table('balance_table', data.get('data', {}))
            elif data_type == 'Cash Flow':
                self.update_financial_table('cashflow_table', data.get('data', {}))
        except Exception as e:
            print(f'❌ DEBUG: Error in update_fundamentals_display(): {str(e)}')

    def update_company_info_table(self, data: Dict[str, Any]):
        """Update company information table"""
        try:
            table_tag = f'company_info_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            key_fields = ['Name', 'Symbol', 'Description', 'Exchange', 'Currency', 'Country', 'Sector', 'Industry', 'MarketCapitalization', 'PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'DividendYield', 'EPS', 'RevenuePerShareTTM', 'ProfitMargin', 'OperatingMarginTTM', 'ReturnOnAssetsTTM', 'ReturnOnEquityTTM']
            for field in key_fields:
                if field in data:
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text(field.replace('TTM', ' (TTM)'))
                        value = data[field]
                        if field == 'MarketCapitalization' and value.isdigit():
                            value = f'${int(value):,}'
                        elif field in ['PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'EPS'] and value != 'None':
                            try:
                                value = f'{float(value):.2f}'
                            except:
                                pass
                        dpg.add_text(str(value))
        except Exception as e:
            print(f'❌ DEBUG: Error in update_company_info_table(): {str(e)}')

    def update_financial_table(self, table_prefix: str, data: Dict[str, Any]):
        """Update financial statement table"""
        try:
            table_tag = f'{table_prefix}_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            for key, value in data.items():
                if key not in ['symbol', 'fiscalDateEnding', 'reportedCurrency']:
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text(key.replace('TTM', ' (TTM)'))
                        if isinstance(value, str) and value.isdigit():
                            formatted_value = f'${int(value):,}'
                        else:
                            formatted_value = str(value)
                        dpg.add_text(formatted_value)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_financial_table(): {str(e)}')

    def update_technical_display(self, data: Dict[str, Any], data_type: str):
        """Update technical analysis display"""
        try:
            table_tag = f'technical_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            if 'data' not in data:
                return
            tech_data = data['data']
            timestamps = tech_data.get('timestamps', [])
            for key, values in tech_data.items():
                if key != 'timestamps' and isinstance(values, list):
                    for i in range(min(10, len(values))):
                        idx = len(values) - 1 - i
                        if idx < len(timestamps):
                            with dpg.table_row(parent=table_tag):
                                dpg.add_text(timestamps[idx])
                                dpg.add_text(data_type + f' ({key})')
                                dpg.add_text(f'{values[idx]:.4f}' if isinstance(values[idx], (int, float)) else str(values[idx]))
                                signal = self.calculate_signal(key, values[idx], values[idx - 1] if idx > 0 else values[idx])
                                dpg.add_text(signal)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_technical_display(): {str(e)}')

    def calculate_signal(self, indicator: str, current: float, previous: float) -> str:
        """Calculate basic signal from indicator values"""
        try:
            if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)):
                return 'N/A'
            if indicator.upper() in ['RSI']:
                if current > 70:
                    return '🔴 Overbought'
                elif current < 30:
                    return '🟢 Oversold'
                else:
                    return '🟡 Neutral'
            elif 'MACD' in indicator.upper():
                if current > previous:
                    return '🟢 Bullish'
                elif current < previous:
                    return '🔴 Bearish'
                else:
                    return '🟡 Neutral'
            elif current > previous:
                return '⬆️ Rising'
            elif current < previous:
                return '⬇️ Falling'
            else:
                return '➡️ Flat'
        except Exception as e:
            return 'N/A'

    def update_raw_display(self, data: Dict[str, Any]):
        """Update raw data display"""
        try:
            import json
            raw_text = json.dumps(data, indent=2, default=str)
            dpg.set_value(f'raw_data_display_{self.tab_id}', raw_text)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_raw_display(): {str(e)}')

    def update_provider_info(self, data: Dict[str, Any]):
        """Update provider information"""
        try:
            table_tag = f'provider_info_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            provider_info = [('Provider', data.get('source', 'Unknown')), ('Status', '✅ Active' if data.get('success') else '❌ Error'), ('Data Points', str(len(data.get('data', {}).get('timestamps', []))) if 'data' in data else 'N/A'), ('Response Time', '< 1s'), ('Last Updated', data.get('fetched_at', 'Unknown'))]
            for key, value in provider_info:
                with dpg.table_row(parent=table_tag):
                    dpg.add_text(key)
                    dpg.add_text(value)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_provider_info(): {str(e)}')

    def refresh_timeseries_view(self):
        """Refresh the time series view with current data"""
        try:
            if self.current_data and 'data' in self.current_data:
                self.update_timeseries_display(self.current_data['data'])
        except Exception as e:
            print(f'❌ DEBUG: Error in refresh_timeseries_view(): {str(e)}')

    def copy_raw_data(self):
        """Copy raw data to clipboard"""
        try:
            if self.current_data:
                import json
                raw_text = json.dumps(self.current_data, indent=2, default=str)
                dpg.set_clipboard_text(raw_text)
                self.update_status('📋 Data copied to clipboard', [100, 255, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in copy_raw_data(): {str(e)}')
            self.update_status('❌ Failed to copy data', [255, 100, 100])

    def save_raw_data(self):
        """Save raw data to file"""
        try:
            if self.current_data:
                import json
                from datetime import datetime
                filename = f'financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json'
                with open(filename, 'w') as f:
                    json.dump(self.current_data, f, indent=2, default=str)
                self.update_status(f'💾 Data saved to {filename}', [100, 255, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in save_raw_data(): {str(e)}')
            self.update_status('❌ Failed to save data', [255, 100, 100])

    def export_data(self):
        """Export current data to CSV"""
        try:
            if not self.current_data or 'data' not in self.current_data:
                self.update_status('❌ No data to export', [255, 100, 100])
                return
            data = self.current_data['data']
            if 'timestamps' not in data:
                self.update_status('❌ No time series data to export', [255, 100, 100])
                return
            import csv
            from datetime import datetime
            filename = f'financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv'
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ['timestamp']
                for key in data.keys():
                    if key != 'timestamps':
                        headers.append(key)
                writer.writerow(headers)
                timestamps = data['timestamps']
                for i in range(len(timestamps)):
                    row = [timestamps[i]]
                    for key in data.keys():
                        if key != 'timestamps':
                            values = data[key]
                            row.append(values[i] if i < len(values) else '')
                    writer.writerow(row)
            self.update_status(f'📊 Data exported to {filename}', [100, 255, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in export_data(): {str(e)}')
            self.update_status('❌ Failed to export data', [255, 100, 100])

    def toggle_auto_refresh(self, sender, value):
        """Toggle auto refresh functionality"""
        try:
            self.auto_refresh = value
            if self.auto_refresh:
                self.update_status('🔄 Auto refresh enabled', [100, 255, 100])
                self.start_auto_refresh()
            else:
                self.update_status('⏹️ Auto refresh disabled', [200, 200, 200])
                self.stop_auto_refresh()
        except Exception as e:
            print(f'❌ DEBUG: Error in toggle_auto_refresh(): {str(e)}')

    def start_auto_refresh(self):
        """Start auto refresh thread"""
        try:
            if self.refresh_thread and self.refresh_thread.is_alive():
                return
            self._stop_refresh = False
            self.refresh_thread = threading.Thread(target=self._auto_refresh_worker)
            self.refresh_thread.daemon = True
            self.refresh_thread.start()
        except Exception as e:
            print(f'❌ DEBUG: Error in start_auto_refresh(): {str(e)}')

    def stop_auto_refresh(self):
        """Stop auto refresh thread"""
        try:
            self._stop_refresh = True
            if self.refresh_thread:
                self.refresh_thread.join(timeout=1.0)
        except Exception as e:
            print(f'❌ DEBUG: Error in stop_auto_refresh(): {str(e)}')

    def _auto_refresh_worker(self):
        """Auto refresh worker thread"""
        try:
            while not self._stop_refresh and self.auto_refresh:
                time.sleep(self.refresh_interval)
                if not self._stop_refresh and self.auto_refresh:
                    self.fetch_data()
        except Exception as e:
            print(f'❌ DEBUG: Error in _auto_refresh_worker(): {str(e)}')

    def clear_data(self):
        """Clear all displayed data"""
        try:
            self.current_data = {}
            for tag_suffix in ['price', 'change', 'volume', 'high', 'low']:
                tag = f'overview_{tag_suffix}_{self.tab_id}'
                if dpg.does_item_exist(tag):
                    dpg.set_value(tag, 'N/A')
            for table_name in ['overview_info_table', 'timeseries_table', 'company_info_table', 'income_table', 'balance_table', 'cashflow_table', 'technical_table']:
                table_tag = f'{table_name}_{self.tab_id}'
                if dpg.does_item_exist(table_tag):
                    children = dpg.get_item_children(table_tag, 1)
                    for child in children:
                        dpg.delete_item(child)
            dpg.set_value(f'raw_data_display_{self.tab_id}', 'No data loaded yet...')
            self.update_status('🧹 Data cleared', [200, 200, 200])
            dpg.set_value(f'last_update_{self.tab_id}', 'Never')
        except Exception as e:
            print(f'❌ DEBUG: Error in clear_data(): {str(e)}')

    def update_status(self, message: str, color: List[int]=None):
        """Update status message"""
        try:
            if color is None:
                color = [200, 200, 200]
            status_tag = f'status_text_{self.tab_id}'
            if dpg.does_item_exist(status_tag):
                dpg.set_value(status_tag, message)
                dpg.configure_item(status_tag, color=color)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_status(): {str(e)}')

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_auto_refresh()
            self.current_data = {}
            print('✅ DEBUG: Enhanced Data Viewer tab cleanup completed')
        except Exception as e:
            print(f'❌ DEBUG: Error during cleanup: {str(e)}')

def _fetch_data_async(self, category: str, data_type: str, symbol: str):
    """Fetch data asynchronously"""
    try:
        print(f'🔧 DEBUG: Fetching {category} - {data_type} for {symbol}')
        if category not in self.data_types or data_type not in self.data_types[category]:
            self.update_status('❌ Invalid data type selection', [255, 100, 100])
            return
        method_name = self.data_types[category][data_type]
        if not hasattr(self.data_source_manager, method_name):
            self.update_status(f'❌ Method {method_name} not available', [255, 100, 100])
            return
        method = getattr(self.data_source_manager, method_name)
        params = self._prepare_method_parameters(category, data_type, symbol)
        if asyncio.iscoroutinefunction(method):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(method(**params))
            finally:
                loop.close()
        else:
            data = method(**params)
        print(f'🔧 DEBUG: Data fetch result: {(data.get('success', False) if isinstance(data, dict) else 'Unknown')}')
        if isinstance(data, dict) and data.get('success'):
            self.current_data = data
            self.update_all_displays(data, category, data_type, symbol)
            self.update_status('✅ Data loaded successfully', [100, 255, 100])
            self.last_refresh = datetime.now()
            dpg.set_value(f'last_update_{self.tab_id}', self.last_refresh.strftime('%H:%M:%S'))
        else:
            error_msg = data.get('error', 'Unknown error') if isinstance(data, dict) else str(data)
            self.update_status(f'❌ {error_msg}', [255, 100, 100])
    except Exception as e:
        print(f'❌ DEBUG: Error in _fetch_data_async(): {str(e)}')
        print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
        self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

def get_company_news(ticker: str, end_date: str, start_date: str | None=None, limit: int=1000, api_key: str=None) -> list[CompanyNews]:
    """Fetch company news from cache or API."""
    cache_key = f'{ticker}_{start_date or 'none'}_{end_date}_{limit}'
    if (cached_data := _cache.get_company_news(cache_key)):
        return [CompanyNews(**news) for news in cached_data]
    headers = {}
    financial_api_key = api_key or os.environ.get('FINANCIAL_DATASETS_API_KEY')
    if financial_api_key:
        headers['X-API-KEY'] = financial_api_key
    all_news = []
    current_end_date = end_date
    while True:
        url = f'https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={current_end_date}'
        if start_date:
            url += f'&start_date={start_date}'
        url += f'&limit={limit}'
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            raise Exception(f'Error fetching data: {ticker} - {response.status_code} - {response.text}')
        data = response.json()
        response_model = CompanyNewsResponse(**data)
        company_news = response_model.news
        if not company_news:
            break
        all_news.extend(company_news)
        if not start_date or len(company_news) < limit:
            break
        current_end_date = min((news.date for news in company_news)).split('T')[0]
        if current_end_date <= start_date:
            break
    if not all_news:
        return []
    _cache.set_company_news(cache_key, [news.model_dump() for news in all_news])
    return all_news

class AlphaVantageWrapper:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.credentials = {'alpha_vantage_api_key': api_key}
        warnings.filterwarnings('ignore')

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def _validate_dates(self, start_date, end_date):
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        return (start_date, end_date)

    def get_equity_historical(self, **params) -> WrapperResponse:
        """Dynamic equity historical data fetcher"""
        try:
            defaults = {'interval': '1d', 'adjustment': 'splits_only', 'extended_hours': False}
            query_params = {**defaults, **params}
            if 'start_date' in query_params and 'end_date' in query_params:
                query_params['start_date'], query_params['end_date'] = self._validate_dates(query_params['start_date'], query_params['end_date'])
            query = AVEquityHistoricalFetcher.transform_query(query_params)
            raw_data = self._run_async(AVEquityHistoricalFetcher.aextract_data(query, self.credentials))
            transformed_data = AVEquityHistoricalFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            df['date'] = pd.to_datetime(df['date'])
            if 'symbol' not in df.columns:
                df.set_index('date', inplace=True)
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} records')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_historical_eps(self, **params) -> WrapperResponse:
        """Dynamic EPS data fetcher"""
        try:
            defaults = {'period': 'quarter', 'limit': None}
            query_params = {**defaults, **params}
            query = AVHistoricalEpsFetcher.transform_query(query_params)
            raw_data = self._run_async(AVHistoricalEpsFetcher.aextract_data(query, self.credentials))
            transformed_data = AVHistoricalEpsFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No EPS data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', ascending=False, inplace=True)
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} EPS records')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_etf_historical(self, **params) -> WrapperResponse:
        """Dynamic ETF data fetcher"""
        params.setdefault('extended_hours', False)
        return self.get_equity_historical(**params)

    def execute_query(self, data_type: str, **params) -> WrapperResponse:
        """Generic query executor"""
        method_map = {'equity': self.get_equity_historical, 'eps': self.get_historical_eps, 'etf': self.get_etf_historical}
        if data_type not in method_map:
            return WrapperResponse(success=False, error=f'Unknown data type: {data_type}')
        return method_map[data_type](**params)

    def test_connection(self) -> WrapperResponse:
        try:
            result = self.get_equity_historical(symbol='AAPL', start_date=datetime.now().date().replace(day=1), end_date=datetime.now().date(), interval='1d')
            if result.success:
                return WrapperResponse(success=True, message='Connection successful')
            else:
                return WrapperResponse(success=False, error='Connection failed')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    @staticmethod
    def get_schema() -> Dict:
        return {'equity_historical': {'required': ['symbol'], 'optional': {'start_date': 'YYYY-MM-DD or date object', 'end_date': 'YYYY-MM-DD or date object', 'interval': ['1m', '5m', '15m', '30m', '60m', '1d', '1W', '1M'], 'adjustment': ['splits_only', 'splits_and_dividends', 'unadjusted'], 'extended_hours': 'bool'}}, 'historical_eps': {'required': ['symbol'], 'optional': {'period': ['annual', 'quarter'], 'limit': 'int'}}, 'etf_historical': {'required': ['symbol'], 'optional': {'start_date': 'YYYY-MM-DD or date object', 'end_date': 'YYYY-MM-DD or date object', 'interval': ['1m', '5m', '15m', '30m', '60m', '1d', '1W', '1M'], 'adjustment': ['splits_only', 'splits_and_dividends', 'unadjusted']}}}

def _run_async(self, coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

class DebugIMFWrapper:
    """Debug IMF wrapper with extensive logging"""

    def __init__(self):
        self.base_url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'
        self.debug_log = []

    def log_debug(self, message: str):
        """Add debug message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        debug_msg = f'[{timestamp}] {message}'
        self.debug_log.append(debug_msg)
        print(debug_msg)

    def get_debug_log(self) -> str:
        """Get all debug messages"""
        return '\n'.join(self.debug_log[-20:])

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def _make_request(self, url: str) -> Dict:
        """Make async HTTP request with debug logging"""
        self.log_debug(f'Making request to: {url}')
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                self.log_debug('Session created, sending request...')
                async with session.get(url) as response:
                    self.log_debug(f'Response status: {response.status}')
                    self.log_debug(f'Response headers: {dict(response.headers)}')
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        self.log_debug(f'Content type: {content_type}')
                        if 'json' in content_type:
                            data = await response.json()
                            self.log_debug(f'JSON response keys: {(list(data.keys()) if isinstance(data, dict) else 'Not a dict')}')
                            return data
                        else:
                            text_data = await response.text()
                            self.log_debug(f'Text response (first 200 chars): {text_data[:200]}')
                            raise Exception(f'Expected JSON but got {content_type}')
                    else:
                        error_text = await response.text()
                        self.log_debug(f'Error response: {error_text[:200]}')
                        raise Exception(f'HTTP {response.status}: {response.reason}')
        except asyncio.TimeoutError:
            self.log_debug('Request timed out after 30 seconds')
            raise Exception('Request timeout')
        except aiohttp.ClientError as e:
            self.log_debug(f'Client error: {str(e)}')
            raise Exception(f'Network error: {str(e)}')
        except Exception as e:
            self.log_debug(f'Unexpected error: {str(e)}')
            raise

    def test_simple_connection(self) -> WrapperResponse:
        """Test basic connection to IMF API"""
        try:
            self.log_debug('Starting simple connection test...')
            test_urls = [f'{self.base_url}Dataflow', f'{self.base_url}CompactData/DOT/A.US.TXG_FOB_USD.CN?startPeriod=2022&endPeriod=2023', 'https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/A.US.TXG_FOB_USD.CN?startPeriod=2022&endPeriod=2023']
            for i, url in enumerate(test_urls):
                try:
                    self.log_debug(f'Testing URL {i + 1}: {url}')
                    response = self._run_async(self._make_request(url))
                    if response:
                        self.log_debug(f'URL {i + 1} SUCCESS - got response')
                        return WrapperResponse(success=True, message=f'Connection successful via URL {i + 1}', debug_info=self.get_debug_log())
                except Exception as e:
                    self.log_debug(f'URL {i + 1} FAILED: {str(e)}')
                    continue
            return WrapperResponse(success=False, error='All test URLs failed', debug_info=self.get_debug_log())
        except Exception as e:
            self.log_debug(f'Connection test exception: {str(e)}')
            return WrapperResponse(success=False, error=str(e), debug_info=self.get_debug_log())

    def get_direction_of_trade(self, **params) -> WrapperResponse:
        """Get bilateral trade data with multiple endpoint fallbacks"""
        try:
            self.log_debug('Starting direction of trade request...')
            defaults = {'country': 'US', 'counterpart': 'CN', 'direction': 'exports', 'frequency': 'A', 'start_date': '2022', 'end_date': '2023'}
            query_params = {**defaults, **params}
            self.log_debug(f'Query parameters: {query_params}')
            direction_map = {'exports': 'TXG_FOB_USD', 'imports': 'TMG_CIF_USD', 'balance': 'TBG_USD'}
            indicator = direction_map.get(query_params['direction'], 'TXG_FOB_USD')
            country = query_params['country']
            counterpart = query_params['counterpart']
            frequency = query_params['frequency']
            start_date = query_params['start_date']
            end_date = query_params['end_date']
            self.log_debug(f'Mapped indicator: {indicator}')
            url_templates = ['https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/{freq}.{country}.{indicator}.{counterpart}?startPeriod={start}&endPeriod={end}', 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/{freq}.{country}.{indicator}.{counterpart}?startPeriod={start}&endPeriod={end}', 'https://data.imf.org/api/data/DOT/{freq}.{country}.{indicator}.{counterpart}?startPeriod={start}&endPeriod={end}']
            for i, template in enumerate(url_templates):
                try:
                    url = template.format(freq=frequency, country=country, indicator=indicator, counterpart=counterpart, start=start_date, end=end_date)
                    self.log_debug(f'Trying URL template {i + 1}: {url}')
                    response = self._run_async(self._make_request(url))
                    self.log_debug(f'Got response from template {i + 1}, analyzing...')
                    result = self._parse_trade_response(response, query_params, indicator)
                    if result.success:
                        return result
                    else:
                        self.log_debug(f'Template {i + 1} parsing failed: {result.error}')
                except Exception as e:
                    self.log_debug(f'Template {i + 1} failed: {str(e)}')
                    continue
            self.log_debug('All URL templates failed, generating mock data for testing...')
            return self._generate_mock_trade_data(query_params)
        except Exception as e:
            self.log_debug(f'Exception in get_direction_of_trade: {str(e)}')
            return WrapperResponse(success=False, error=str(e), debug_info=self.get_debug_log())

    def _parse_trade_response(self, response, query_params, indicator) -> WrapperResponse:
        """Parse trade response with detailed logging"""
        try:
            if isinstance(response, dict):
                self.log_debug(f'Response top-level keys: {list(response.keys())}')
                if 'CompactData' in response:
                    return self._parse_sdmx_response(response, query_params, indicator)
                elif 'data' in response:
                    return self._parse_simple_response(response, query_params, indicator)
                elif 'ErrorDetails' in response:
                    error_details = response['ErrorDetails']
                    self.log_debug(f'API Error: {error_details}')
                    return WrapperResponse(success=False, error=f'IMF API Error: {error_details}')
                else:
                    self.log_debug('Unknown response format')
                    return WrapperResponse(success=False, error='Unknown response format')
            else:
                return WrapperResponse(success=False, error='Response is not a dictionary')
        except Exception as e:
            self.log_debug(f'Response parsing error: {str(e)}')
            return WrapperResponse(success=False, error=f'Parsing error: {str(e)}')

    def _parse_sdmx_response(self, response, query_params, indicator) -> WrapperResponse:
        """Parse SDMX format response"""
        try:
            compact_data = response['CompactData']
            self.log_debug(f'CompactData keys: {(list(compact_data.keys()) if isinstance(compact_data, dict) else 'Not a dict')}')
            dataset = compact_data.get('DataSet', {})
            series = dataset.get('Series', [])
            if not series:
                self.log_debug('No series data found in SDMX response')
                return WrapperResponse(success=False, error='No series data in response')
            return self._extract_trade_records(series, query_params, indicator)
        except Exception as e:
            return WrapperResponse(success=False, error=f'SDMX parsing error: {str(e)}')

    def _parse_simple_response(self, response, query_params, indicator) -> WrapperResponse:
        """Parse simple JSON response format"""
        try:
            data = response.get('data', [])
            self.log_debug(f'Simple response data length: {len(data)}')
            if not data:
                return WrapperResponse(success=False, error='No data in simple response')
            records = []
            for item in data:
                records.append({'date': item.get('date') or item.get('period'), 'country': query_params['country'], 'counterpart': query_params['counterpart'], 'direction': query_params['direction'], 'value': float(item.get('value', 0)), 'indicator': indicator})
            df = pd.DataFrame(records)
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} records')
        except Exception as e:
            return WrapperResponse(success=False, error=f'Simple parsing error: {str(e)}')

    def _extract_trade_records(self, series, query_params, indicator) -> WrapperResponse:
        """Extract records from series data"""
        try:
            if isinstance(series, dict):
                series = [series]
                self.log_debug('Converted single series dict to list')
            records = []
            for i, s in enumerate(series):
                self.log_debug(f'Processing series {i}: {(list(s.keys()) if isinstance(s, dict) else 'Not a dict')}')
                obs_list = s.get('Obs', [])
                if isinstance(obs_list, dict):
                    obs_list = [obs_list]
                self.log_debug(f'Series {i} has {len(obs_list)} observations')
                for j, obs in enumerate(obs_list):
                    time_period = obs.get('@TIME_PERIOD')
                    obs_value = obs.get('@OBS_VALUE')
                    self.log_debug(f'Obs {j}: TIME_PERIOD={time_period}, OBS_VALUE={obs_value}')
                    records.append({'date': time_period, 'country': query_params['country'], 'counterpart': query_params['counterpart'], 'direction': query_params['direction'], 'value': float(obs_value) if obs_value and obs_value != 'None' else 0, 'indicator': indicator})
            self.log_debug(f'Extracted {len(records)} records')
            if not records:
                return WrapperResponse(success=False, error='No valid records extracted')
            df = pd.DataFrame(records)
            try:
                df['date'] = pd.to_datetime(df['date'])
            except:
                self.log_debug('Date conversion failed, keeping as string')
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} trade records')
        except Exception as e:
            return WrapperResponse(success=False, error=f'Record extraction error: {str(e)}')

    def _generate_mock_trade_data(self, query_params) -> WrapperResponse:
        """Generate mock trade data when API is unavailable"""
        try:
            self.log_debug('Generating mock trade data for testing...')
            years = [query_params['start_date'], query_params['end_date']]
            if query_params['start_date'] != query_params['end_date']:
                start_year = int(query_params['start_date'])
                end_year = int(query_params['end_date'])
                years = list(range(start_year, end_year + 1))
            records = []
            base_value = 500000
            for year in years:
                variation = (hash(f'{year}{query_params['country']}{query_params['counterpart']}') % 200 - 100) / 100
                value = base_value * (1 + variation * 0.1)
                records.append({'date': f'{year}-01-01', 'country': query_params['country'], 'counterpart': query_params['counterpart'], 'direction': query_params['direction'], 'value': value, 'indicator': 'MOCK_DATA'})
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            return WrapperResponse(success=True, data=df, message=f'Generated {len(df)} mock trade records (API unavailable)', debug_info=self.get_debug_log())
        except Exception as e:
            return WrapperResponse(success=False, error=f'Mock data generation failed: {str(e)}')

    def execute_query(self, data_type: str, **params) -> WrapperResponse:
        """Generic query executor"""
        self.log_debug(f'Executing query: {data_type} with params: {params}')
        method_map = {'direction_of_trade': self.get_direction_of_trade, 'test_connection': self.test_simple_connection}
        if data_type not in method_map:
            return WrapperResponse(success=False, error=f'Unknown data type: {data_type}', debug_info=self.get_debug_log())
        return method_map[data_type](**params)

def _run_async(self, coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

class IMFWrapper:

    def __init__(self):
        warnings.filterwarnings('ignore')

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def _validate_dates(self, start_date, end_date):
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        return (start_date, end_date)

    def get_available_indicators(self, **params) -> WrapperResponse:
        """Search available IMF indicators"""
        try:
            defaults = {}
            query_params = {**defaults, **params}
            query = ImfAvailableIndicatorsFetcher.transform_query(query_params)
            raw_data = ImfAvailableIndicatorsFetcher.extract_data(query)
            transformed_data = ImfAvailableIndicatorsFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No indicators found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} indicators')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_direction_of_trade(self, **params) -> WrapperResponse:
        """Get bilateral trade flow data between countries"""
        try:
            defaults = {'direction': 'exports', 'frequency': 'annual'}
            query_params = {**defaults, **params}
            if 'start_date' in query_params and 'end_date' in query_params:
                query_params['start_date'], query_params['end_date'] = self._validate_dates(query_params['start_date'], query_params['end_date'])
            query = ImfDirectionOfTradeFetcher.transform_query(query_params)
            raw_data = self._run_async(ImfDirectionOfTradeFetcher.aextract_data(query, None))
            transformed_data = ImfDirectionOfTradeFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No trade data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            df['date'] = pd.to_datetime(df['date'])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} trade records')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_economic_indicators(self, **params) -> WrapperResponse:
        """Get economic indicators including IRFCL and FSI data"""
        try:
            defaults = {'symbol': 'irfcl_top_lines', 'frequency': 'quarter'}
            query_params = {**defaults, **params}
            if 'start_date' in query_params and 'end_date' in query_params:
                query_params['start_date'], query_params['end_date'] = self._validate_dates(query_params['start_date'], query_params['end_date'])
            query = ImfEconomicIndicatorsFetcher.transform_query(query_params)
            raw_data = self._run_async(ImfEconomicIndicatorsFetcher.aextract_data(query, None))
            transformed_data = ImfEconomicIndicatorsFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No economic data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            df['date'] = pd.to_datetime(df['date'])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} economic records')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_maritime_chokepoint_info(self, **params) -> WrapperResponse:
        """Get static information about global maritime chokepoints"""
        try:
            defaults = {}
            query_params = {**defaults, **params}
            query = ImfMaritimeChokePointInfoFetcher.transform_query(query_params)
            raw_data = self._run_async(ImfMaritimeChokePointInfoFetcher.aextract_data(query, None))
            transformed_data = ImfMaritimeChokePointInfoFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No chokepoint data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} chokepoints')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_maritime_chokepoint_volume(self, **params) -> WrapperResponse:
        """Get daily vessel transit data through maritime chokepoints"""
        try:
            defaults = {}
            query_params = {**defaults, **params}
            if 'start_date' in query_params and 'end_date' in query_params:
                query_params['start_date'], query_params['end_date'] = self._validate_dates(query_params['start_date'], query_params['end_date'])
            query = ImfMaritimeChokePointVolumeFetcher.transform_query(query_params)
            raw_data = self._run_async(ImfMaritimeChokePointVolumeFetcher.aextract_data(query, None))
            transformed_data = ImfMaritimeChokePointVolumeFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No chokepoint volume data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            df['date'] = pd.to_datetime(df['date'])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} volume records')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_port_info(self, **params) -> WrapperResponse:
        """Get static information about global ports"""
        try:
            defaults = {}
            query_params = {**defaults, **params}
            query = ImfPortInfoFetcher.transform_query(query_params)
            raw_data = self._run_async(ImfPortInfoFetcher.aextract_data(query, None))
            transformed_data = ImfPortInfoFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No port data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} ports')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def get_port_volume(self, **params) -> WrapperResponse:
        """Get daily port activity and trade volume data"""
        try:
            defaults = {}
            query_params = {**defaults, **params}
            if 'start_date' in query_params and 'end_date' in query_params:
                query_params['start_date'], query_params['end_date'] = self._validate_dates(query_params['start_date'], query_params['end_date'])
            query = ImfPortVolumeFetcher.transform_query(query_params)
            raw_data = self._run_async(ImfPortVolumeFetcher.aextract_data(query, None))
            transformed_data = ImfPortVolumeFetcher.transform_data(query, raw_data)
            if not transformed_data:
                return WrapperResponse(success=False, error='No port volume data found')
            df = pd.DataFrame([item.model_dump() for item in transformed_data])
            df['date'] = pd.to_datetime(df['date'])
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} port volume records')
        except Exception as e:
            return WrapperResponse(success=False, error=str(e))

    def execute_query(self, data_type: str, **params) -> WrapperResponse:
        """Generic query executor for IMF data"""
        method_map = {'available_indicators': self.get_available_indicators, 'direction_of_trade': self.get_direction_of_trade, 'economic_indicators': self.get_economic_indicators, 'maritime_chokepoint_info': self.get_maritime_chokepoint_info, 'maritime_chokepoint_volume': self.get_maritime_chokepoint_volume, 'port_info': self.get_port_info, 'port_volume': self.get_port_volume}
        if data_type not in method_map:
            return WrapperResponse(success=False, error=f'Unknown data type: {data_type}')
        return method_map[data_type](**params)

    @staticmethod
    def get_schema() -> Dict:
        return {'available_indicators': {'required': [], 'optional': {'query': 'str - search terms separated by semicolons'}, 'description': 'Search through IMF indicator catalog'}, 'direction_of_trade': {'required': [], 'optional': {'country': 'str - country names or ISO codes', 'counterpart': 'str - counterpart country names or ISO codes', 'direction': ['exports', 'imports', 'balance', 'all'], 'frequency': ['annual', 'quarter', 'month'], 'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}, 'description': 'Bilateral trade flows between countries'}, 'economic_indicators': {'required': [], 'optional': {'symbol': 'str - indicator symbol or preset (irfcl_top_lines, fsi_core, etc.)', 'country': 'str - country names or ISO codes', 'frequency': ['annual', 'quarter', 'month'], 'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}, 'description': 'Economic indicators including IRFCL and FSI data'}, 'maritime_chokepoint_info': {'required': [], 'optional': {'theme': ['dark', 'light']}, 'description': 'Static info about global maritime chokepoints'}, 'maritime_chokepoint_volume': {'required': [], 'optional': {'chokepoint': 'str - chokepoint name (suez_canal, panama_canal, etc.)', 'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}, 'description': 'Daily vessel transit data through chokepoints'}, 'port_info': {'required': [], 'optional': {'continent': ['north_america', 'europe', 'asia_pacific', 'south_america', 'africa'], 'country': 'str - 3-letter ISO country code', 'limit': 'int - number of results'}, 'description': 'Static information about global ports'}, 'port_volume': {'required': [], 'optional': {'port_code': 'str - port ID', 'country': 'str - 3-letter ISO country code', 'start_date': 'YYYY-MM-DD (min: 2019-01-01)', 'end_date': 'YYYY-MM-DD'}, 'description': 'Daily port activity and trade volume data'}}

def _run_async(self, coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

class SECDataUI:
    """DearPyGUI Interface for SEC Data"""

    def __init__(self):
        self.api = SECDataAPI()
        self.current_data = None

    def setup_ui(self):
        """Setup the main UI"""
        dpg.create_context()
        with dpg.window(label='SEC Data Terminal', tag='main_window'):
            dpg.add_text('🟢 Using Working SEC Headers', color=(0, 255, 0))
            dpg.add_separator()
            with dpg.tab_bar():
                with dpg.tab(label='CIK Map'):
                    dpg.add_text('Convert Symbol to CIK')
                    dpg.add_input_text(label='Symbol', tag='cik_symbol', default_value='TSLA')
                    dpg.add_button(label='Get CIK', callback=self.get_cik_callback)
                    dpg.add_text('', tag='cik_result')
                with dpg.tab(label='Company Filings'):
                    dpg.add_text('Get SEC Filings for Company')
                    dpg.add_input_text(label='Symbol', tag='filing_symbol', default_value='TSLA')
                    dpg.add_input_text(label='Form Type (optional)', tag='filing_form', default_value='10-K,10-Q')
                    dpg.add_input_int(label='Limit', tag='filing_limit', default_value=10)
                    dpg.add_button(label='Get Filings', callback=self.get_filings_callback)
                    with dpg.child_window(height=300, tag='filings_table'):
                        dpg.add_text('Filings will appear here...')
                with dpg.tab(label='Company Facts'):
                    dpg.add_text('Compare Company Facts')
                    dpg.add_input_text(label='Symbol (optional)', tag='facts_symbol', default_value='TSLA')
                    dpg.add_input_text(label='Fact', tag='facts_fact', default_value='Revenues')
                    dpg.add_input_int(label='Year (optional)', tag='facts_year', default_value=0)
                    dpg.add_button(label='Get Facts', callback=self.get_facts_callback)
                    with dpg.child_window(height=300, tag='facts_table'):
                        dpg.add_text('Facts will appear here...')
                with dpg.tab(label='Fails to Deliver'):
                    dpg.add_text('Get Fails-to-Deliver Data')
                    dpg.add_input_text(label='Symbol', tag='ftd_symbol', default_value='TSLA')
                    dpg.add_input_int(label='Reports Limit', tag='ftd_limit', default_value=12)
                    dpg.add_button(label='Get FTD Data', callback=self.get_ftd_callback)
                    with dpg.child_window(height=300, tag='ftd_table'):
                        dpg.add_text('FTD data will appear here...')
                with dpg.tab(label='Equity Search'):
                    dpg.add_text('Search Companies')
                    dpg.add_input_text(label='Search Query', tag='search_query', default_value='Tesla')
                    dpg.add_checkbox(label='Search Funds', tag='search_funds', default_value=False)
                    dpg.add_button(label='Search', callback=self.search_callback)
                    with dpg.child_window(height=300, tag='search_table'):
                        dpg.add_text('Search results will appear here...')
        dpg.create_viewport(title='SEC Data Terminal', width=1000, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window('main_window', True)

    def get_cik_callback(self):
        """Callback for CIK mapping"""
        symbol = dpg.get_value('cik_symbol')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_cik_map(symbol))
                if 'error' in result:
                    dpg.set_value('cik_result', f'Error: {result['error']}')
                else:
                    dpg.set_value('cik_result', f'Symbol: {result['symbol']} -> CIK: {result['cik']}')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def get_filings_callback(self):
        """Callback for company filings"""
        symbol = dpg.get_value('filing_symbol')
        form_type = dpg.get_value('filing_form') or None
        limit = dpg.get_value('filing_limit')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_company_filings(symbol=symbol, form_type=form_type, limit=limit))
                dpg.delete_item('filings_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='filings_table')
                else:
                    dpg.add_text(f'Company: {result['company_name']} (CIK: {result['cik']})', parent='filings_table')
                    dpg.add_separator(parent='filings_table')
                    filings = result['filings'][:10]
                    for filing in filings:
                        filing_text = f'Form: {filing.get('form', 'N/A')} | Date: {filing.get('filingDate', 'N/A')} | Document: {filing.get('primaryDocument', 'N/A')}'
                        dpg.add_text(filing_text, parent='filings_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def get_facts_callback(self):
        """Callback for company facts"""
        symbol = dpg.get_value('facts_symbol') or None
        fact = dpg.get_value('facts_fact')
        year = dpg.get_value('facts_year') or None

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_compare_company_facts(symbol=symbol, fact=fact, year=year))
                dpg.delete_item('facts_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='facts_table')
                else:
                    metadata = result['metadata']
                    dpg.add_text(f'Fact: {metadata.get('fact', 'N/A')}', parent='facts_table')
                    if 'company' in metadata:
                        dpg.add_text(f'Company: {metadata['company']}', parent='facts_table')
                    dpg.add_separator(parent='facts_table')
                    data = result['data'][:15]
                    for item in data:
                        if symbol:
                            fact_text = f'Value: {item.get('val', 'N/A')} | Period: {item.get('end', 'N/A')} | Filed: {item.get('filed', 'N/A')}'
                        else:
                            fact_text = f'Company: {item.get('symbol', 'N/A')} | Value: {item.get('val', 'N/A')}'
                        dpg.add_text(fact_text, parent='facts_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def get_ftd_callback(self):
        """Callback for FTD data"""
        symbol = dpg.get_value('ftd_symbol')
        limit = dpg.get_value('ftd_limit')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_equity_ftd(symbol, limit))
                dpg.delete_item('ftd_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='ftd_table')
                else:
                    dpg.add_text(f'Symbol: {result['symbol']} | Total Records: {result['count']}', parent='ftd_table')
                    dpg.add_separator(parent='ftd_table')
                    data = result['data'][:20]
                    for item in data:
                        ftd_text = f'Date: {item.get('date', 'N/A')} | Quantity: {item.get('quantity', 'N/A')} | Price: ${item.get('price', 'N/A')}'
                        dpg.add_text(ftd_text, parent='ftd_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def search_callback(self):
        """Callback for equity search"""
        query = dpg.get_value('search_query')
        is_fund = dpg.get_value('search_funds')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_equity_search(query, is_fund))
                dpg.delete_item('search_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='search_table')
                else:
                    dpg.add_text(f"Query: '{result['query']}' | Results: {result['count']}", parent='search_table')
                    dpg.add_separator(parent='search_table')
                    data = result['data'][:15]
                    for item in data:
                        if is_fund:
                            search_text = f'Symbol: {item.get('symbol', 'N/A')} | CIK: {item.get('cik', 'N/A')}'
                        else:
                            search_text = f'Symbol: {item.get('symbol', 'N/A')} | Name: {item.get('name', 'N/A')} | CIK: {item.get('cik', 'N/A')}'
                        dpg.add_text(search_text, parent='search_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def run(self):
        """Run the application"""
        self.setup_ui()
        dpg.start_dearpygui()
        dpg.destroy_context()

def run_async_task():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(self.api.get_equity_search(query, is_fund))
        dpg.delete_item('search_table', children_only=True)
        if 'error' in result:
            dpg.add_text(f'Error: {result['error']}', parent='search_table')
        else:
            dpg.add_text(f"Query: '{result['query']}' | Results: {result['count']}", parent='search_table')
            dpg.add_separator(parent='search_table')
            data = result['data'][:15]
            for item in data:
                if is_fund:
                    search_text = f'Symbol: {item.get('symbol', 'N/A')} | CIK: {item.get('cik', 'N/A')}'
                else:
                    search_text = f'Symbol: {item.get('symbol', 'N/A')} | Name: {item.get('name', 'N/A')} | CIK: {item.get('cik', 'N/A')}'
                dpg.add_text(search_text, parent='search_table')
    finally:
        loop.close()

