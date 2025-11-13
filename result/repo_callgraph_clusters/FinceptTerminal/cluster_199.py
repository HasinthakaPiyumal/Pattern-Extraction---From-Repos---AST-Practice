# Cluster 199

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

def __init__(self, api_key: str):
    self.api_key = api_key
    self.credentials = {'alpha_vantage_api_key': api_key}
    warnings.filterwarnings('ignore')

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

def __init__(self):
    warnings.filterwarnings('ignore')

