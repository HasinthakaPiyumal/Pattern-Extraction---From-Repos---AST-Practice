# Cluster 20

class BISAPI:
    """BIS SDMX API client with comprehensive coverage of all endpoints"""

    def __init__(self, base_url: str='https://stats.bis.org/api/v1', timeout: int=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self.known_flows = {'WS_EER': 'Effective exchange rates', 'WS_CBPOL': 'Central bank policy rates', 'WS_DT1': 'Debt securities', 'WS_LTINT': 'Long-term interest rates', 'WS_STINT': 'Short-term interest rates', 'WS_MON': 'Monetary aggregates', 'WS_XRU': 'Exchange rates', 'WS_CRD': 'Credit to the non-financial sector', 'WS_HP': 'House prices', 'WS_REER': 'Real effective exchange rates', 'WS_CUST': 'Customs and exchange controls', 'WS_FDI': 'Foreign direct investment', 'WS_CUR': 'Currency composition of official foreign exchange reserves'}
        self.user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36']

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self, endpoint_type: str='data') -> Dict[str, str]:
        """Get request headers with random user agent"""
        import random
        if endpoint_type == 'structure':
            accept_header = 'application/vnd.sdmx.structure+json;version=1.0.0,application/vnd.sdmx.structure+xml;version=2.1,application/xml'
        else:
            accept_header = 'application/vnd.sdmx.data+json;version=1.0.0,application/vnd.sdmx.genericdata+xml;version=2.1,application/xml'
        return {'User-Agent': random.choice(self.user_agents), 'Accept': accept_header, 'Accept-Encoding': 'gzip, deflate'}

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]]=None, endpoint_type: str='data') -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        if not self.session:
            raise BISError('Session not initialized. Use async with BISAPI()...')
        url = f'{self.base_url}/{endpoint}'
        headers = self._get_headers(endpoint_type)
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type or 'application/vnd.sdmx.data+json' in content_type:
                        data = await response.json()
                        return self._format_response(data, endpoint)
                    elif 'application/xml' in content_type or 'text/xml' in content_type:
                        text_data = await response.text()
                        return self._parse_xml_response(text_data, endpoint)
                    elif 'text/csv' in content_type:
                        text_data = await response.text()
                        return self._parse_csv_response(text_data, endpoint)
                    else:
                        try:
                            data = await response.json()
                            return self._format_response(data, endpoint)
                        except:
                            text_data = await response.text()
                            return {'success': True, 'data': text_data, 'content_type': content_type, 'endpoint': endpoint, 'params': params}
                else:
                    error_text = await response.text()
                    raise BISError(f'HTTP {response.status}: {error_text}', response.status, endpoint)
        except asyncio.TimeoutError:
            raise BISError(f'Request timeout after {self.timeout.total} seconds', None, endpoint)
        except aiohttp.ClientError as e:
            raise BISError(f'Network error: {str(e)}', None, endpoint)
        except Exception as e:
            raise BISError(f'Unexpected error: {str(e)}', None, endpoint)

    def _format_response(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """Format API response with metadata"""
        return {'success': True, 'data': data, 'endpoint': endpoint, 'timestamp': datetime.now().isoformat()}

    def _parse_xml_response(self, xml_data: str, endpoint: str) -> Dict[str, Any]:
        """Parse XML SDMX response"""
        try:
            root = ET.fromstring(xml_data)
            result = {'success': True, 'data': {'xml_raw': xml_data, 'root_tag': root.tag, 'namespaces': dict(root.attrib.items()) if hasattr(root, 'attrib') else {}}, 'endpoint': endpoint, 'format': 'xml'}
            series = root.findall('.//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Series')
            if series:
                result['data']['series_count'] = len(series)
                series_data = []
                for series_elem in series[:5]:
                    series_info = {}
                    for child in series_elem:
                        if child.tag.endswith('SeriesKey'):
                            series_info['key'] = {v.attrib.get('id'): v.text for v in child}
                        elif child.tag.endswith('Obs'):
                            obs_info = {v.attrib.get('id'): v.text for v in child}
                            series_info.setdefault('observations', []).append(obs_info)
                    series_data.append(series_info)
                result['data']['series_preview'] = series_data
            return result
        except ET.ParseError as e:
            return {'success': True, 'data': {'xml_raw': xml_data, 'parse_error': str(e)}, 'endpoint': endpoint, 'format': 'xml'}

    def _parse_csv_response(self, csv_data: str, endpoint: str) -> Dict[str, Any]:
        """Parse CSV response"""
        lines = csv_data.strip().split('\n')
        return {'success': True, 'data': {'csv_raw': csv_data, 'lines_count': len(lines), 'header': lines[0] if lines else '', 'preview': lines[:10]}, 'endpoint': endpoint, 'format': 'csv'}

    async def get_data(self, flow: str, key: str='all', start_period: Optional[str]=None, end_period: Optional[str]=None, first_n_observations: Optional[int]=None, last_n_observations: Optional[int]=None, detail: str='full') -> Dict[str, Any]:
        """
        Get statistical data for a specific flow and key combination

        Args:
            flow: Statistical domain (e.g., 'WS_EER', 'BIS,WS_EER,1.0')
            key: Data key identifying series (use 'all' for all data)
            start_period: Start period (ISO 8601 or SDMX format)
            end_period: End period (ISO 8601 or SDMX format)
            first_n_observations: Return first N observations from oldest
            last_n_observations: Return last N observations from newest
            detail: Detail level ('full', 'dataonly', 'serieskeysonly', 'nodata')
        """
        params = {}
        if start_period:
            params['startPeriod'] = start_period
        if end_period:
            params['endPeriod'] = end_period
        if first_n_observations:
            params['firstNObservations'] = first_n_observations
        if last_n_observations:
            params['lastNObservations'] = last_n_observations
        if detail != 'full':
            params['detail'] = detail
        encoded_flow = quote(flow, safe='')
        encoded_key = quote(key, safe='')
        endpoint = f'data/{encoded_flow}/{encoded_key}/all'
        return await self._make_request(endpoint, params)

    async def get_available_constraints(self, flow: str, key: str, component_id: str, mode: str='exact', references: str='none', start_period: Optional[str]=None, end_period: Optional[str]=None) -> Dict[str, Any]:
        """
        Get information about data availability for specific constraints

        Args:
            flow: Statistical domain
            key: Data key
            component_id: Dimension ID for availability info
            mode: 'exact' for current selection, 'available' for remaining valid options
            references: References to include ('none', 'all', etc.)
            start_period: Start period filter
            end_period: End period filter
        """
        params = {'mode': mode, 'references': references}
        if start_period:
            params['startPeriod'] = start_period
        if end_period:
            params['endPeriod'] = end_period
        encoded_flow = quote(flow, safe='')
        encoded_key = quote(key, safe='')
        endpoint = f'availableconstraint/{encoded_flow}/{encoded_key}/all/{component_id}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_data_structures(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """
        Get data structure definitions

        Args:
            agency_id: Maintenance agency (e.g., 'BIS', 'all')
            resource_id: Resource ID or 'all'
            version: Version or 'latest' or 'all'
            references: References to include
            detail: Structure detail level
        """
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'datastructure/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_dataflows(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get dataflow definitions (available datasets)"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'dataflow/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_categorisations(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get categorisation definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'categorisation/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_content_constraints(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get content constraint definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'contentconstraint/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_actual_constraints(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get actual constraint definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'actualconstraint/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_allowed_constraints(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get allowed constraint definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'allowedconstraint/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_structures(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get general structure definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'structure/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_concept_schemes(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get concept scheme definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'conceptscheme/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_codelists(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get codelist definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'codelist/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_category_schemes(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get category scheme definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'categoryscheme/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_hierarchical_codelists(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get hierarchical codelist definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'hierarchicalcodelist/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_agency_schemes(self, agency_id: str='all', resource_id: str='all', version: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get agency scheme definitions"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        endpoint = f'agencyscheme/{agency_id}/{resource_id}/{version}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_concepts(self, agency_id: str, resource_id: str, version: str, item_id: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get specific concepts from concept schemes"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        item_id = quote(item_id, safe='')
        endpoint = f'conceptscheme/{agency_id}/{resource_id}/{version}/{item_id}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_codes(self, agency_id: str, resource_id: str, version: str, item_id: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get specific codes from codelists"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        item_id = quote(item_id, safe='')
        endpoint = f'codelist/{agency_id}/{resource_id}/{version}/{item_id}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_categories(self, agency_id: str, resource_id: str, version: str, item_id: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get specific categories from category schemes"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        item_id = quote(item_id, safe='')
        endpoint = f'categoryscheme/{agency_id}/{resource_id}/{version}/{item_id}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_hierarchies(self, agency_id: str, resource_id: str, version: str, item_id: str='all', references: str='none', detail: str='full') -> Dict[str, Any]:
        """Get specific hierarchies from hierarchical codelists"""
        params = {'references': references, 'detail': detail}
        agency_id = quote(agency_id, safe='')
        resource_id = quote(resource_id, safe='')
        version = quote(version, safe='')
        item_id = quote(item_id, safe='')
        endpoint = f'hierarchicalcodelist/{agency_id}/{resource_id}/{version}/{item_id}'
        return await self._make_request(endpoint, params, 'structure')

    async def get_effective_exchange_rates(self, countries: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """
        Get effective exchange rates data (WS_EER)

        Args:
            countries: List of country codes (e.g., ['US', 'GB', 'JP'])
            start_period: Start period
            end_period: End period
            detail: Detail level
        """
        key = 'all'
        if countries:
            key = f'M.N.B.{'+'.join(countries)}'
        return await self.get_data(flow='WS_EER', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_central_bank_policy_rates(self, countries: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """
        Get central bank policy rates (WS_CBPOL)

        Args:
            countries: List of country codes
            start_period: Start period
            end_period: End period
            detail: Detail level
        """
        key = 'all'
        if countries:
            key = f'D.{'+'.join(countries)}'
        return await self.get_data(flow='WS_CBPOL', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_long_term_interest_rates(self, countries: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """Get long-term interest rates (WS_LTINT)"""
        key = 'all'
        if countries:
            key = f'M.{'+'.join(countries)}'
        return await self.get_data(flow='WS_LTINT', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_short_term_interest_rates(self, countries: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """Get short-term interest rates (WS_STINT)"""
        key = 'all'
        if countries:
            key = f'M.{'+'.join(countries)}'
        return await self.get_data(flow='WS_STINT', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_exchange_rates(self, currency_pairs: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """
        Get exchange rates (WS_XRU)

        Args:
            currency_pairs: List of currency pairs (e.g., ['USD', 'EUR', 'GBP'])
            start_period: Start period
            end_period: End period
            detail: Detail level
        """
        key = 'all'
        if currency_pairs:
            key = f'D.{'+'.join(currency_pairs)}'
        return await self.get_data(flow='WS_XRU', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_credit_to_non_financial_sector(self, countries: Optional[List[str]]=None, sectors: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """
        Get credit to non-financial sector (WS_CRD)

        Args:
            countries: List of country codes
            sectors: List of sectors
            start_period: Start period
            end_period: End period
            detail: Detail level
        """
        key = 'all'
        if countries and sectors:
            key = f'Q.{'+'.join(countries)}.{'+'.join(sectors)}'
        elif countries:
            key = f'Q.{'+'.join(countries)}'
        return await self.get_data(flow='WS_CRD', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_house_prices(self, countries: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None, detail: str='dataonly') -> Dict[str, Any]:
        """Get house price indices (WS_HP)"""
        key = 'all'
        if countries:
            key = f'Q.{'+'.join(countries)}'
        return await self.get_data(flow='WS_HP', key=key, start_period=start_period, end_period=end_period, detail=detail)

    async def get_available_datasets(self) -> Dict[str, Any]:
        """Get overview of all available dataflows (datasets)"""
        return await self.get_dataflows(agency_id='BIS', detail='allstubs')

    async def search_datasets(self, query: str, agency_id: str='BIS') -> Dict[str, Any]:
        """
        Search for datasets matching a query

        Args:
            query: Search term
            agency_id: Agency to search in
        """
        result = await self.get_dataflows(agency_id=agency_id, detail='full')
        if result.get('success') and 'data' in result:
            dataflows = result['data']
            matches = []
            if isinstance(dataflows, dict):
                for key, value in dataflows.items():
                    if query.lower() in str(value).lower():
                        matches.append({key: value})
            return {'success': True, 'data': {'query': query, 'matches': matches, 'total_matches': len(matches)}, 'endpoint': 'search'}
        return result

    async def get_economic_overview(self, countries: Optional[List[str]]=None, start_period: Optional[str]=None, end_period: Optional[str]=None) -> Dict[str, Any]:
        """
        Get comprehensive economic overview for countries

        Args:
            countries: List of country codes
            start_period: Start period
            end_period: End period
        """
        results = {}
        indicators = [('effective_exchange_rates', self.get_effective_exchange_rates), ('central_bank_policy_rates', self.get_central_bank_policy_rates), ('long_term_interest_rates', self.get_long_term_interest_rates), ('short_term_interest_rates', self.get_short_term_interest_rates), ('exchange_rates', self.get_exchange_rates), ('credit_to_non_financial_sector', self.get_credit_to_non_financial_sector)]
        for name, method in indicators:
            try:
                result = await method(countries=countries, start_period=start_period, end_period=end_period, detail='dataonly')
                results[name] = result
            except Exception as e:
                results[name] = {'success': False, 'error': str(e)}
        return {'success': True, 'data': {'economic_overview': results, 'countries': countries or ['all'], 'period': {'start': start_period or 'earliest', 'end': end_period or 'latest'}, 'indicators_requested': len(indicators), 'indicators_retrieved': len([r for r in results.values() if r.get('success', False)])}, 'endpoint': 'economic_overview'}

    async def get_dataset_metadata(self, flow: str) -> Dict[str, Any]:
        """
        Get comprehensive metadata for a specific dataset

        Args:
            flow: Data flow identifier (e.g., 'WS_EER')
        """
        results = {}
        try:
            dataflows = await self.get_dataflows(resource_id=flow)
            results['dataflow'] = dataflows
            structures = await self.get_data_structures(resource_id=flow)
            results['structure'] = structures
            sample_data = await self.get_data(flow=flow, detail='serieskeysonly', last_n_observations=5)
            results['sample_keys'] = sample_data
            return {'success': True, 'data': {'flow': flow, 'metadata': results, 'description': self.known_flows.get(flow, 'Unknown dataset')}, 'endpoint': 'dataset_metadata'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'endpoint': 'dataset_metadata'}

def __init__(self, base_url: str='https://stats.bis.org/api/v1', timeout: int=30):
    self.base_url = base_url.rstrip('/')
    self.timeout = aiohttp.ClientTimeout(total=timeout)
    self.session = None
    self.known_flows = {'WS_EER': 'Effective exchange rates', 'WS_CBPOL': 'Central bank policy rates', 'WS_DT1': 'Debt securities', 'WS_LTINT': 'Long-term interest rates', 'WS_STINT': 'Short-term interest rates', 'WS_MON': 'Monetary aggregates', 'WS_XRU': 'Exchange rates', 'WS_CRD': 'Credit to the non-financial sector', 'WS_HP': 'House prices', 'WS_REER': 'Real effective exchange rates', 'WS_CUST': 'Customs and exchange controls', 'WS_FDI': 'Foreign direct investment', 'WS_CUR': 'Currency composition of official foreign exchange reserves'}
    self.user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36']

class APIConfig:
    """Centralized API configuration"""
    API_BASE_URL = os.getenv('FINCEPT_API_URL', 'https://finceptbackend.share.zrok.io')
    FALLBACK_URLS = ['http://localhost:4500', 'https://api.fincept.in']
    API_VERSION = '2.1.0'
    REQUEST_TIMEOUT = 10
    CONNECTION_TIMEOUT = 5
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    REQUIRE_API_CONNECTION = True
    ALLOW_GUEST_FALLBACK = False
    CONFIG_DIR_NAME = '.fincept'
    CREDENTIALS_FILE = 'credentials.json'
    CACHE_FILE = 'cache.json'
    APP_NAME = 'Fincept Financial Terminal'
    APP_VERSION = '2.1.0'
    LOG_LEVEL = os.getenv('FINCEPT_LOG_LEVEL', 'INFO').upper()
    DEBUG_MODE = os.getenv('FINCEPT_DEBUG', 'false').lower() == 'true'
    _config_dir = None
    _credentials_path = None
    _cache_path = None

    def __init__(self):
        """Initialize configuration"""
        self._setup_directories()
        info('API configuration initialized', module='config', context={'api_url': self.get_api_url(), 'version': self.API_VERSION})

    @monitor_performance
    def _setup_directories(self):
        """Setup configuration directories"""
        with operation('setup_config_directories', module='config'):
            try:
                home_dir = Path.home()
                self._config_dir = home_dir / self.CONFIG_DIR_NAME
                self._config_dir.mkdir(exist_ok=True)
                self._credentials_path = self._config_dir / self.CREDENTIALS_FILE
                self._cache_path = self._config_dir / self.CACHE_FILE
                debug('Configuration directories setup completed', module='config', context={'config_dir': str(self._config_dir)})
            except Exception as e:
                error('Failed to setup configuration directories', module='config', context={'error': str(e)}, exc_info=True)
                raise

    @classmethod
    def get_api_url(cls) -> str:
        """Get the primary API URL"""
        url = cls.API_BASE_URL.rstrip('/')
        debug('Retrieved API URL', module='config', context={'url': url})
        return url

    @classmethod
    def get_full_url(cls, endpoint: str) -> str:
        """Get full URL for an endpoint"""
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        full_url = f'{cls.get_api_url()}{endpoint}'
        debug('Generated full URL', module='config', context={'endpoint': endpoint, 'full_url': full_url})
        return full_url

    @classmethod
    def get_fallback_urls(cls) -> List[str]:
        """Get list of fallback URLs"""
        urls = [url.rstrip('/') for url in cls.FALLBACK_URLS]
        debug('Retrieved fallback URLs', module='config', context={'count': len(urls)})
        return urls

    @classmethod
    def validate_configuration(cls) -> Dict[str, Any]:
        """Validate current configuration"""
        with operation('validate_configuration', module='config'):
            config_data = {'api_url': cls.get_api_url(), 'api_version': cls.API_VERSION, 'require_connection': cls.REQUIRE_API_CONNECTION, 'allow_guest_fallback': cls.ALLOW_GUEST_FALLBACK, 'request_timeout': cls.REQUEST_TIMEOUT, 'connection_timeout': cls.CONNECTION_TIMEOUT, 'max_retries': cls.MAX_RETRIES, 'debug_mode': cls.DEBUG_MODE, 'fallback_urls_count': len(cls.FALLBACK_URLS)}
            info('Configuration validated', module='config', context=config_data)
            return config_data

    @classmethod
    def set_api_url(cls, new_url: str):
        """Update API URL at runtime"""
        old_url = cls.API_BASE_URL
        cls.API_BASE_URL = new_url.rstrip('/')
        info('API URL updated', module='config', context={'old_url': old_url, 'new_url': cls.API_BASE_URL})

    @classmethod
    def set_debug_mode(cls, debug_enabled: bool):
        """Set debug mode"""
        old_debug = cls.DEBUG_MODE
        cls.DEBUG_MODE = debug_enabled
        set_debug_mode(debug_enabled)
        info('Debug mode changed', module='config', context={'old_debug': old_debug, 'new_debug': debug_enabled})

    @classmethod
    def set_strict_mode(cls, strict: bool):
        """Set strict API connection mode"""
        old_strict = cls.REQUIRE_API_CONNECTION
        cls.REQUIRE_API_CONNECTION = strict
        cls.ALLOW_GUEST_FALLBACK = not strict
        info('Strict mode changed', module='config', context={'old_strict': old_strict, 'new_strict': strict})

    def get_config_dir(self) -> Path:
        """Get configuration directory path"""
        return self._config_dir

    def get_credentials_path(self) -> Path:
        """Get credentials file path"""
        return self._credentials_path

    def get_cache_path(self) -> Path:
        """Get cache file path"""
        return self._cache_path

    @classmethod
    def get_request_headers(cls, api_key: Optional[str]=None) -> Dict[str, str]:
        """Get standard request headers"""
        headers = {'Content-Type': 'application/json', 'User-Agent': f'{cls.APP_NAME}/{cls.APP_VERSION}', 'Accept': 'application/json', 'X-API-Version': cls.API_VERSION}
        if api_key:
            headers['X-API-Key'] = api_key
        debug('Generated request headers', module='config', context={'has_api_key': bool(api_key)})
        return headers

    @classmethod
    def get_timeout_config(cls) -> Dict[str, float]:
        """Get timeout configuration"""
        timeout_config = {'connect': cls.CONNECTION_TIMEOUT, 'read': cls.REQUEST_TIMEOUT, 'total': cls.REQUEST_TIMEOUT + cls.CONNECTION_TIMEOUT}
        debug('Generated timeout configuration', module='config', context=timeout_config)
        return timeout_config

    def cleanup(self):
        """Cleanup configuration resources"""
        with operation('config_cleanup', module='config'):
            info('Configuration cleanup completed', module='config')

@classmethod
def get_api_url(cls) -> str:
    """Get the primary API URL"""
    url = cls.API_BASE_URL.rstrip('/')
    debug('Retrieved API URL', module='config', context={'url': url})
    return url

@classmethod
def get_fallback_urls(cls) -> List[str]:
    """Get list of fallback URLs"""
    urls = [url.rstrip('/') for url in cls.FALLBACK_URLS]
    debug('Retrieved fallback URLs', module='config', context={'count': len(urls)})
    return urls

@classmethod
def set_api_url(cls, new_url: str):
    """Update API URL at runtime"""
    old_url = cls.API_BASE_URL
    cls.API_BASE_URL = new_url.rstrip('/')
    info('API URL updated', module='config', context={'old_url': old_url, 'new_url': cls.API_BASE_URL})

