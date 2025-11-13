# Cluster 9

class IMFDataWrapper:
    """Modular IMF data wrapper with fault-tolerant endpoints"""

    def __init__(self):
        self.base_url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept-Terminal/1.0'})
        self.country_to_code = {'united_states': 'US', 'usa': 'US', 'united_kingdom': 'GB', 'uk': 'GB', 'great_britain': 'GB', 'china': 'CN', 'japan': 'JP', 'germany': 'DE', 'france': 'FR', 'india': 'IN', 'italy': 'IT', 'canada': 'CA', 'south_korea': 'KR', 'russia': 'RU', 'brazil': 'BR', 'australia': 'AU', 'spain': 'ES', 'mexico': 'MX', 'indonesia': 'ID', 'netherlands': 'NL', 'saudi_arabia': 'SA', 'turkey': 'TR', 'switzerland': 'CH', 'poland': 'PL', 'sweden': 'SE', 'belgium': 'BE', 'argentina': 'AR', 'ireland': 'IE', 'austria': 'AT', 'norway': 'NO', 'israel': 'IL', 'united_arab_emirates': 'AE', 'uae': 'AE', 'egypt': 'EG', 'south_africa': 'ZA', 'denmark': 'DK', 'singapore': 'SG', 'malaysia': 'MY', 'philippines': 'PH', 'thailand': 'TH', 'nigeria': 'NG', 'pakistan': 'PK', 'chile': 'CL', 'finland': 'FI', 'romania': 'RO', 'czech_republic': 'CZ', 'portugal': 'PT', 'iraq': 'IQ', 'peru': 'PE', 'greece': 'GR', 'new_zealand': 'NZ', 'qatar': 'QA', 'algeria': 'DZ', 'hungary': 'HU', 'kazakhstan': 'KZ', 'kuwait': 'KW', 'morocco': 'MA', 'ukraine': 'UA', 'slovakia': 'SK', 'ecuador': 'EC', 'vietnam': 'VN', 'bangladesh': 'BD', 'angola': 'AO', 'azerbaijan': 'AZ', 'czechia': 'CZ', 'kenya': 'KE', 'omani': 'OM', 'azerbaijan': 'AZ', 'az': 'AZ', 'sri_lanka': 'LK', 'luxembourg': 'LU', 'panama': 'PA', 'uruguay': 'UY', 'myanmar': 'MM', 'burma': 'MM', 'costa_rica': 'CR', 'lithuania': 'LT', 'slovenia': 'SI', 'belarus': 'BY', 'uzbekistan': 'UZ', 'bulgaria': 'BG', 'croatia': 'HR', 'lebanon': 'LB', 'guatemala': 'GT', 'tanzania': 'TZ', 'ethiopia': 'ET', 'ghana': 'GH', 'ivory_coast': 'CI', "côte_d'ivoire": 'CI', 'dominican_republic': 'DO', 'austria': 'AT', 'serbia': 'RS', 'ecuador': 'EC', 'bolivia': 'BO', 'uzbekistan': 'UZ', 'cameroon': 'CM', 'turkmenistan': 'TM', 'yemen': 'YE', 'paraguay': 'PY', 'senegal': 'SN', 'zambia': 'ZM', 'papua_new_guinea': 'PG', 'libya': 'LY', 'honduras': 'HN', 'congo': 'CG', 'bulgaria': 'BG', 'congo': 'CD', 'niger': 'NE', 'mozambique': 'MZ', 'benin': 'BJ', 'guinea': 'GN', 'kyrgyzstan': 'KG', 'zimbabwe': 'ZW', 'tunisia': 'TN', 'somalia': 'SO', 'mali': 'ML', 'nicaragua': 'NI', 'madagascar': 'MG', 'cameroon': 'CM', 'angola': 'AO', 'mali': 'ML', 'cambodia': 'KH', 'nepal': 'NP', 'jordan': 'JO', 'laos': 'LA', 'honduras': 'HN', 'georgia': 'GE', 'papua_new_guinea': 'PG', 'cambodia': 'KH', 'jordan': 'JO', 'laos': 'LA', 'congo': 'CG', 'somalia': 'SO', 'mali': 'ML', 'nicaragua': 'NI', 'kyrgyzstan': 'KG', 'madagascar': 'MG', 'north_macedonia': 'MK', 'macedonia': 'MK', 'botswana': 'BW', 'albania': 'AL', 'namibia': 'NA', 'gabon': 'GA', 'lesotho': 'LS', 'burkina_faso': 'BF', 'mongolia': 'MN', 'armenia': 'AM', 'fiji': 'FJ', 'haiti': 'HT', 'brunei': 'BN', 'montenegro': 'ME', 'suriname': 'SR', 'bhutan': 'BT', 'guyana': 'GY', 'south_sudan': 'SS', 'eritrea': 'ER', 'gambia': 'GM', 'djibouti': 'DJ', 'timor_leste': 'TL', 'east_timor': 'TL', 'seychelles': 'SC', 'antigua_and_barbuda': 'AG', 'belize': 'BZ', 'grenada': 'GD', 'st_vincent_and_the_grenadines': 'VC', 'st_kitts_and_nevis': 'KN', 'dominica': 'DM', 'samoa': 'WS', 'vanuatu': 'VU', 'sao_tome_and_principe': 'ST', 'comoros': 'KM', 'tonga': 'TO', 'micronesia': 'FM', 'palau': 'PW', 'marshall_islands': 'MH', 'kiribati': 'KI', 'tuvalu': 'TV', 'nauru': 'NR'}
        self.irfcl_presets = {'irfcl_top_lines': 'RAF_USD,RAFA_USD,RAFAFX_USD,RAOFA_USD,RAPFA_USD,RAFAIMF_USD,RAFASDR_USD,RAFAGOLD_USD,RACFA_USD,RAMDCD_USD,RAMFIFC_USD,RAMSR_USD', 'reserve_assets': 'RAF_USD,RAFA_USD,RAFAFX_USD,RAOFA_USD,RAPFA_USD,RAFAIMF_USD,RAFASDR_USD,RAFAGOLD_USD', 'gold_reserves': 'RAFAGOLD_USD,RAFAGOLDV_OZT', 'derivative_assets': 'RAMFDA_USD'}
        self.fsi_presets = ['fsi_core', 'fsi_core_underlying', 'fsi_other', 'fsi_encouraged_set', 'fsi_balance_sheets', 'fsi_all']
        self.trade_indicators = {'exports': 'TXG_FOB_USD', 'imports': 'TMG_CIF_USD', 'balance': 'TBG_USD', 'all': 'TXG_FOB_USD+TMG_CIF_USD+TBG_USD'}
        self.frequency_map = {'annual': 'A', 'yearly': 'A', 'a': 'A', 'quarter': 'Q', 'quarterly': 'Q', 'q': 'Q', 'month': 'M', 'monthly': 'M', 'm': 'M'}
        self.sector_map = {'government': 'S1311', 'central_bank': 'S121', 'monetary_authorities': 'S1X', 'all': ''}
        self.trade_titles = {'TXG_FOB_USD': 'Goods, Value of Exports, Free on board (FOB), US Dollars', 'TMG_CIF_USD': 'Goods, Value of Imports, Cost, Insurance, Freight (CIF), US Dollars', 'TBG_USD': 'Goods, Value of Trade Balance, US Dollars'}

    def _normalize_country(self, country: str) -> str:
        """Normalize country name to ISO code"""
        if not country:
            return ''
        country_lower = country.lower().strip().replace(' ', '_')
        if country_lower in self.country_to_code:
            return self.country_to_code[country_lower]
        if len(country) == 2 and country.isupper():
            return country
        for mapped_name, code in self.country_to_code.items():
            if mapped_name in country_lower or country_lower in mapped_name:
                return code
        return country.upper()

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f'HTTP request failed: {str(e)}')
        except json.JSONDecodeError as e:
            raise Exception(f'JSON decode error: {str(e)}')

    def _adjust_date_by_frequency(self, date_str: str, frequency: str, is_start: bool=True) -> str:
        """Adjust date based on frequency like OpenBB does"""
        if not date_str:
            return ''
        try:
            date = pd.to_datetime(date_str)
            freq = self.frequency_map.get(frequency.lower(), 'Q')
            if freq == 'Q':
                if is_start:
                    date = date.to_period('Q').start_time
                else:
                    date = date.to_period('Q').end_time
            elif freq == 'A':
                if is_start:
                    date = date.to_period('A').start_time
                else:
                    date = date.to_period('A').end_time
            elif is_start:
                date = date.to_period('M').start_time
            else:
                date = date.to_period('M').end_time
            return date.strftime('%Y-%m-%d')
        except:
            return date_str

    def get_economic_indicators(self, countries: Optional[str]=None, symbols: Optional[str]=None, frequency: Optional[str]='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None, sector: Optional[str]='monetary_authorities') -> Dict[str, Any]:
        """Get economic indicators data (IRFCL and FSI)"""
        try:
            if not countries:
                countries = 'all'
            if not symbols:
                symbols = 'irfcl_top_lines'
            if countries.lower() != 'all':
                country_list = [c.strip() for c in countries.split(',')]
                normalized_countries = '+'.join([self._normalize_country(c) for c in country_list if self._normalize_country(c)])
            else:
                normalized_countries = ''
            if symbols in self.irfcl_presets:
                indicator_symbols = self.irfcl_presets[symbols].replace(',', '+')
            elif symbols in self.fsi_presets:
                indicator_symbols = symbols
            else:
                symbol_list = [s.strip().upper() for s in symbols.split(',')]
                indicator_symbols = '+'.join(symbol_list)
            freq_code = self.frequency_map.get(frequency.lower(), 'Q')
            sector_code = self.sector_map.get(sector.lower(), '')
            if start_date:
                start_date = self._adjust_date_by_frequency(start_date, frequency, True)
            if end_date:
                end_date = self._adjust_date_by_frequency(end_date, frequency, False)
            date_range = f'?startPeriod={start_date}&endPeriod={end_date}' if start_date and end_date else ''
            if symbols in self.irfcl_presets or not any((p in symbols for p in self.fsi_presets)):
                url = f'{self.base_url}CompactData/IRFCL/{freq_code}.{normalized_countries}.{indicator_symbols}.{sector_code}{date_range}'
            else:
                url = f'{self.base_url}CompactData/FSI/{freq_code}.{normalized_countries}.{indicator_symbols}{date_range}'
            response_data = self._make_request(url)
            if 'ErrorDetails' in response_data:
                error_msg = response_data['ErrorDetails'].get('Message', 'Unknown IMF API error')
                return {'error': IMFError('economic_indicators', error_msg).to_dict()}
            series_data = response_data.get('CompactData', {}).get('DataSet', {}).get('Series', [])
            if not series_data:
                return {'error': IMFError('economic_indicators', 'No data found for the specified parameters').to_dict()}
            if isinstance(series_data, dict):
                series_data = [series_data]
            processed_data = []
            for series in series_data:
                if 'Obs' not in series:
                    continue
                metadata = {k.replace('@', '').lower(): v for k, v in series.items() if k != 'Obs'}
                indicator = metadata.get('indicator', '')
                country_code = metadata.get('ref_area', '')
                observations = series['Obs']
                if isinstance(observations, dict):
                    observations = [observations]
                for obs in observations:
                    date_str = obs.get('@TIME_PERIOD', '')
                    value = obs.get('@OBS_VALUE')
                    if value is not None:
                        try:
                            value = float(value)
                        except:
                            value = None
                    country_name = country_code
                    for name, code in self.country_to_code.items():
                        if code == country_code:
                            country_name = name.replace('_', ' ').title()
                            break
                    data_point = {'date': date_str, 'symbol': indicator, 'country': country_name, 'country_code': country_code, 'value': value, 'frequency': frequency, 'sector': sector}
                    if metadata.get('unit_mult'):
                        data_point['scale'] = metadata['unit_mult']
                    if metadata.get('ref_sector'):
                        data_point['reference_sector'] = metadata['ref_sector']
                    processed_data.append(data_point)
            return {'success': True, 'data': processed_data, 'parameters': {'countries': countries, 'symbols': symbols, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date, 'sector': sector}}
        except Exception as e:
            return {'error': IMFError('economic_indicators', str(e)).to_dict()}

    def get_direction_of_trade(self, countries: Optional[str]=None, counterparts: Optional[str]=None, direction: Optional[str]='all', frequency: Optional[str]='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get direction of trade data (exports, imports, balance)"""
        try:
            if not countries:
                countries = 'all'
            if not counterparts:
                counterparts = 'all'
            if not direction:
                direction = 'all'
            if countries.lower() == 'all' and counterparts.lower() == 'all':
                return {'error': IMFError('direction_of_trade', "Both country and counterpart cannot be 'all'").to_dict()}
            if countries.lower() != 'all':
                country_list = [c.strip() for c in countries.split(',')]
                normalized_countries = '+'.join([self._normalize_country(c) for c in country_list if self._normalize_country(c)])
            else:
                normalized_countries = ''
            if counterparts.lower() != 'all':
                counterpart_list = [c.strip() for c in counterparts.split(',')]
                normalized_counterparts = '+'.join([self._normalize_country(c) for c in counterpart_list if self._normalize_country(c)])
            else:
                normalized_counterparts = ''
            indicator_code = self.trade_indicators.get(direction.lower(), 'TXG_FOB_USD+TMG_CIF_USD+TBG_USD')
            freq_code = self.frequency_map.get(frequency.lower(), 'Q')
            if start_date:
                start_date = self._adjust_date_by_frequency(start_date, frequency, True)
            if end_date:
                end_date = self._adjust_date_by_frequency(end_date, frequency, False)
            date_range = f'?startPeriod={start_date}&endPeriod={end_date}' if start_date and end_date else ''
            url = f'{self.base_url}CompactData/DOT/{freq_code}.{normalized_countries}.{indicator_code}.{normalized_counterparts}{date_range}'
            response_data = self._make_request(url)
            if 'ErrorDetails' in response_data:
                error_msg = response_data['ErrorDetails'].get('Message', 'Unknown IMF API error')
                return {'error': IMFError('direction_of_trade', error_msg).to_dict()}
            series_data = response_data.get('CompactData', {}).get('DataSet', {}).get('Series', [])
            if not series_data:
                return {'error': IMFError('direction_of_trade', 'No trade data found for the specified parameters').to_dict()}
            if isinstance(series_data, dict):
                series_data = [series_data]
            processed_data = []
            for series in series_data:
                if 'Obs' not in series:
                    continue
                metadata = {k.replace('@', '').lower(): v for k, v in series.items() if k != 'Obs'}
                indicator = metadata.get('indicator', '')
                country_code = metadata.get('ref_area', '')
                counterpart_code = metadata.get('counterpart_area', '')
                observations = series['Obs']
                if isinstance(observations, dict):
                    observations = [observations]
                for obs in observations:
                    date_str = obs.get('@TIME_PERIOD', '')
                    value = obs.get('@OBS_VALUE')
                    if value is not None:
                        try:
                            value = float(value)
                        except:
                            value = None
                    if value is None:
                        continue
                    country_name = country_code
                    counterpart_name = counterpart_code
                    for name, code in self.country_to_code.items():
                        if code == country_code:
                            country_name = name.replace('_', ' ').title()
                        if code == counterpart_code:
                            counterpart_name = name.replace('_', ' ').title()
                    data_point = {'date': date_str, 'symbol': indicator, 'country': country_name, 'country_code': country_code, 'counterpart': counterpart_name, 'counterpart_code': counterpart_code, 'value': value, 'frequency': frequency, 'direction': direction, 'title': self.trade_titles.get(indicator, indicator)}
                    if metadata.get('unit_mult'):
                        data_point['scale'] = metadata['unit_mult']
                    processed_data.append(data_point)
            return {'success': True, 'data': processed_data, 'parameters': {'countries': countries, 'counterparts': counterparts, 'direction': direction, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}}
        except Exception as e:
            return {'error': IMFError('direction_of_trade', str(e)).to_dict()}

    def get_available_indicators(self, query: Optional[str]=None) -> Dict[str, Any]:
        """Get list of available IMF indicators"""
        try:
            indicators = [{'symbol': 'RAF_USD', 'name': 'Total Reserves', 'dataset': 'IRFCL', 'description': 'Total reserves excluding gold'}, {'symbol': 'RAFA_USD', 'name': 'Foreign Exchange Reserves', 'dataset': 'IRFCL', 'description': 'Foreign exchange reserves'}, {'symbol': 'RAFAGOLD_USD', 'name': 'Gold Reserves', 'dataset': 'IRFCL', 'description': 'Gold reserves'}, {'symbol': 'RAFAIMF_USD', 'name': 'IMF Reserves', 'dataset': 'IRFCL', 'description': 'Reserves position in the IMF'}, {'symbol': 'RAFASDR_USD', 'name': 'SDR Holdings', 'dataset': 'IRFCL', 'description': 'Special Drawing Rights'}, {'symbol': 'RAMFDA_USD', 'name': 'Derivative Assets', 'dataset': 'IRFCL', 'description': 'Net derivative assets'}, {'symbol': 'FSI_CAPR', 'name': 'Capital Adequacy Ratio', 'dataset': 'FSI', 'description': 'Regulatory capital to risk-weighted assets'}, {'symbol': 'FSI_NPL', 'name': 'Non-Performing Loans', 'dataset': 'FSI', 'description': 'Non-performing loans to total gross loans'}, {'symbol': 'FSI_ROA', 'name': 'Return on Assets', 'dataset': 'FSI', 'description': 'Return on assets'}, {'symbol': 'FSI_ROE', 'name': 'Return on Equity', 'dataset': 'FSI', 'description': 'Return on equity'}, {'symbol': 'TXG_FOB_USD', 'name': 'Exports', 'dataset': 'DOT', 'description': 'Goods, Value of Exports, Free on board (FOB)'}, {'symbol': 'TMG_CIF_USD', 'name': 'Imports', 'dataset': 'DOT', 'description': 'Goods, Value of Imports, Cost, Insurance, Freight (CIF)'}, {'symbol': 'TBG_USD', 'name': 'Trade Balance', 'dataset': 'DOT', 'description': 'Goods, Value of Trade Balance'}]
            if query:
                query_terms = [term.strip().lower() for term in query.split(';')]
                filtered_indicators = []
                for indicator in indicators:
                    indicator_text = f'{indicator['symbol']} {indicator['name']} {indicator['description']}'.lower()
                    if all((term in indicator_text for term in query_terms)):
                        filtered_indicators.append(indicator)
                indicators = filtered_indicators
            return {'success': True, 'data': indicators, 'count': len(indicators), 'parameters': {'query': query}}
        except Exception as e:
            return {'error': IMFError('available_indicators', str(e)).to_dict()}

    def get_comprehensive_economic_data(self, country: str, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get comprehensive economic data for a country"""
        try:
            if not country:
                return {'error': IMFError('comprehensive_economic_data', 'Country parameter is required').to_dict()}
            results = {}
            reserves_result = self.get_economic_indicators(countries=country, symbols='irfcl_top_lines', frequency='quarter', start_date=start_date, end_date=end_date)
            results['reserves'] = reserves_result
            trade_result = self.get_direction_of_trade(countries=country, counterparts='all', direction='all', frequency='quarter', start_date=start_date, end_date=end_date)
            results['trade'] = trade_result
            indicators_result = self.get_available_indicators()
            results['available_indicators'] = indicators_result
            has_data = any((result.get('success') and result.get('data') for result in results.values()))
            if not has_data:
                return {'error': IMFError('comprehensive_economic_data', 'No data found for the specified country').to_dict()}
            return {'success': True, 'data': results, 'parameters': {'country': country, 'start_date': start_date, 'end_date': end_date}}
        except Exception as e:
            return {'error': IMFError('comprehensive_economic_data', str(e)).to_dict()}

def _adjust_date_by_frequency(self, date_str: str, frequency: str, is_start: bool=True) -> str:
    """Adjust date based on frequency like OpenBB does"""
    if not date_str:
        return ''
    try:
        date = pd.to_datetime(date_str)
        freq = self.frequency_map.get(frequency.lower(), 'Q')
        if freq == 'Q':
            if is_start:
                date = date.to_period('Q').start_time
            else:
                date = date.to_period('Q').end_time
        elif freq == 'A':
            if is_start:
                date = date.to_period('A').start_time
            else:
                date = date.to_period('A').end_time
        elif is_start:
            date = date.to_period('M').start_time
        else:
            date = date.to_period('M').end_time
        return date.strftime('%Y-%m-%d')
    except:
        return date_str

class OECDWrapper:
    """Modular OECD API wrapper with fault tolerance"""

    def __init__(self, cache_dir: Optional[str]=None):
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser('~'), '.oecd_cache')
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        self.session = self._get_legacy_session()

    def _get_legacy_session(self):
        """Create a custom session for OECD compatibility"""
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 4
        session = requests.Session()
        session.mount('https://', self.CustomHttpAdapter(ctx))
        return session

    class CustomHttpAdapter(requests.adapters.HTTPAdapter):
        """Transport adapter that allows us to use custom ssl_context."""

        def __init__(self, ssl_context=None, **kwargs):
            self.ssl_context = ssl_context
            super().__init__(**kwargs)

        def init_poolmanager(self, connections, maxsize, block=False):
            self.poolmanager = urllib3.poolmanager.PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=self.ssl_context)

    def _make_request(self, url: str, method: str='GET', params: Optional[Dict]=None, format_type: str='csv', api_version: str='v1') -> Dict[str, Any]:
        """Make HTTP request with comprehensive error handling"""
        try:
            headers = {'Accept-Language': 'en', 'Accept-Encoding': 'gzip, deflate'}
            if format_type == 'json':
                if api_version == 'v2':
                    headers['Accept'] = 'application/vnd.sdmx.data+json; charset=utf-8; version=2'
                else:
                    headers['Accept'] = 'application/vnd.sdmx.data+json; charset=utf-8; version=1.0'
            elif format_type == 'xml':
                headers['Accept'] = 'application/vnd.sdmx.structurespecificdata+xml; charset=utf-8; version=2.1'
            elif format_type == 'csv':
                headers['Accept'] = 'application/vnd.sdmx.data+csv; charset=utf-8'
            else:
                headers['Accept'] = 'application/vnd.sdmx.data+csv; charset=utf-8'
                if params is None:
                    params = {}
                params['format'] = 'csvfile'
            response = self.session.request(method=method, url=url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            if 'json' in content_type or format_type == 'json':
                try:
                    return {'success': True, 'data': response.text, 'format': 'json'}
                except Exception as e:
                    return {'error': f'JSON parsing error: {str(e)}', 'json_error': True}
            elif 'xml' in content_type or format_type == 'xml':
                try:
                    return {'success': True, 'data': response.text, 'format': 'xml'}
                except Exception as e:
                    return {'error': f'XML parsing error: {str(e)}', 'xml_error': True}
            else:
                try:
                    return {'success': True, 'data': response.text, 'format': 'csv'}
                except Exception as e:
                    return {'error': f'Response parsing error: {str(e)}', 'response_error': True}
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout', 'timeout': True, 'status_code': None}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error', 'connection_error': True, 'status_code': None}
        except requests.exceptions.HTTPError as e:
            response = locals().get('response')
            if response is None:
                return {'error': f'HTTP error: {e}', 'http_error': True, 'status_code': None}
            if response.status_code == 404:
                return {'error': 'Data not found', 'not_found': True, 'status_code': response.status_code}
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded', 'rate_limit_error': True, 'status_code': response.status_code}
            else:
                return {'error': f'HTTP error: {e}', 'http_error': True, 'status_code': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request error: {e}', 'request_error': True, 'status_code': None}
        except Exception as e:
            return {'error': f'Unexpected error: {e}', 'general_error': True, 'status_code': None}

    def _parse_xml_to_dataframe(self, xml_string: str) -> pd.DataFrame:
        """Parse the OECD XML and return a dataframe."""
        try:
            root = fromstring(xml_string)
            namespaces = {'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message', 'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic'}
            data = []
            for series in root.findall('.//generic:Series', namespaces=namespaces):
                series_data = {}
                for value in series.findall('.//generic:Value', namespaces=namespaces):
                    series_data[value.get('id')] = value.get('value')
                for obs in series.findall('./generic:Obs', namespaces=namespaces):
                    obs_data = series_data.copy()
                    obs_data['TIME_PERIOD'] = obs.find('./generic:ObsDimension', namespaces=namespaces).get('value')
                    obs_data['VALUE'] = obs.find('./generic:ObsValue', namespaces=namespaces).get('value')
                    data.append(obs_data)
            return pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f'Failed to parse XML: {str(e)}')

    def _oecd_date_to_python_date(self, input_date: Union[str, int]) -> date:
        """Date formatter helper."""
        input_date = str(input_date)
        if 'Q' in input_date:
            return pd.to_datetime(input_date).to_period('Q').start_time.date()
        if len(input_date) == 4:
            return date(int(input_date), 1, 1)
        if len(input_date) == 7:
            return pd.to_datetime(input_date).to_period('M').start_time.date()
        raise ValueError('Date not in expected format')

    def _country_string(self, countries: str, country_mapping: Dict[str, str]) -> str:
        """Convert list of countries to OECD codes"""
        if countries == 'all':
            return ''
        country_list = countries.split(',')
        return '+'.join([country_mapping.get(country.lower(), country) for country in country_list])

    def get_gdp_real(self, countries: str='united_states', frequency: str='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get real GDP data"""
        try:
            if frequency not in ['quarter', 'annual']:
                return OECDError('gdp_real', f'Invalid frequency: {frequency}. Must be quarter or annual').to_dict()
            if not start_date:
                start_date = '2020-01-01' if countries == 'all' else '1947-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = 'Q' if frequency == 'quarter' else 'A'
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.NAD/DSD_NAMAIN1@DF_QNA/1.0/{country_codes}.{freq_code}..S1..B1GQ.VOBP...EUR+_T+GBP+USD+JPY.XDC'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr = f'{freq_code}..{country_codes}.S1..B1GQ.VOBP...XDC'
                url_v1 = f'{SDMX_V1_BASE}data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA,1.0/{filter_expr}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                return OECDError('gdp_real', result['error'], result.get('status_code')).to_dict()
            try:
                df = pd.read_csv(StringIO(result['data'])).get(['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])
                if df.empty:
                    return OECDError('gdp_real', 'No data found for the given parameters').to_dict()
                df = df.rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})

                def apply_country_map(x):
                    v = CODE_TO_COUNTRY_GDP.get(x, x)
                    v = v.replace('_', ' ').title()
                    return v.replace('Oecd', 'OECD')
                df['country'] = df['country'].apply(apply_country_map)
                df['date'] = df['date'].apply(self._oecd_date_to_python_date)
                df = df[(df['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (df['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                df['value'] = (df['value'].astype(float) * 1000000).astype('int64')
                df = df.sort_values(by=['date', 'value'], ascending=[True, False])
                df['date'] = df['date'].astype(str)
                result_data = df.replace({np.nan: None}).to_dict(orient='records')
                return {'success': True, 'endpoint': 'gdp_real', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('gdp_real', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('gdp_real', str(e)).to_dict()

    def get_consumer_price_index(self, countries: str='united_states', expenditure: str='total', frequency: str='monthly', units: str='index', harmonized: bool=False, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get Consumer Price Index data"""
        try:
            if frequency not in ['monthly', 'quarter', 'annual']:
                return OECDError('cpi', f'Invalid frequency: {frequency}').to_dict()
            if units not in ['index', 'yoy', 'mom']:
                return OECDError('cpi', f'Invalid units: {units}').to_dict()
            if not start_date:
                start_date = '1950-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            methodology = 'HICP' if harmonized else 'N'
            freq_code = 'M' if frequency == 'monthly' else 'Q' if frequency == 'quarter' else 'A'
            unit_code = {'index': 'IX', 'yoy': 'PA', 'mom': 'PC'}[units]
            expenditure_code = '' if expenditure == 'all' else EXPENDITURE_DICT.get(expenditure, '')
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_CPI)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.TPS/DSD_PRICES@DF_PRICES_ALL/1.0/{country_codes}.{freq_code}.{methodology}.CPI.{unit_code}.{expenditure_code}.N'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr = f'{country_codes}.{freq_code}.{methodology}.CPI.{unit_code}.{expenditure_code}.N'
                url_v1 = f'{SDMX_V1_BASE}data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/{filter_expr}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                return OECDError('cpi', result['error'], result.get('status_code')).to_dict()
            try:
                if result['format'] == 'xml':
                    data = self._parse_xml_to_dataframe(result['data'])
                else:
                    data = pd.read_csv(StringIO(result['data']))
                query_filter = f"METHODOLOGY=='{methodology}' & UNIT_MEASURE=='{unit_code}' & FREQ=='{freq_code}'"
                if country_codes:
                    if '+' in country_codes:
                        country_list = country_codes.split('+')
                        country_conditions = ' or '.join([f"REF_AREA=='{c}'" for c in country_list])
                        query_filter += f' & ({country_conditions})'
                    else:
                        query_filter += f" & REF_AREA=='{country_codes}'"
                if expenditure_code:
                    query_filter += f" & EXPENDITURE=='{expenditure_code}'"
                if hasattr(data, 'query'):
                    data = data.query(query_filter).reset_index(drop=True)
                if hasattr(data, 'rename'):
                    data = data[['REF_AREA', 'TIME_PERIOD', 'VALUE', 'EXPENDITURE']].rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'VALUE': 'value', 'EXPENDITURE': 'expenditure'})
                data['country'] = data['country'].map(CODE_TO_COUNTRY_CPI)
                if expenditure_code:
                    reverse_expenditure = {v: k for k, v in EXPENDITURE_DICT.items()}
                    data['expenditure'] = data['expenditure'].map(reverse_expenditure)
                data['date'] = data['date'].apply(self._oecd_date_to_python_date)
                data = data[(data['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (data['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                data['date'] = data['date'].astype(str)
                if units in ('yoy', 'mom'):
                    data['value'] = data['value'].astype(float) / 100
                result_data = data.fillna('N/A').replace('N/A', None).to_dict(orient='records')
                return {'success': True, 'endpoint': 'consumer_price_index', 'parameters': {'countries': countries, 'expenditure': expenditure, 'frequency': frequency, 'units': units, 'harmonized': harmonized, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('cpi', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('cpi', str(e)).to_dict()

    def get_gdp_forecast(self, countries: str='united_states', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get GDP forecast data from OECD - Economic Outlook forecasts"""
        try:
            current_year = date.today().year
            if not start_date:
                start_date = f'{current_year - 1}-01-01'
            if not end_date:
                end_date = f'{current_year + 2}-12-31'
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AEO/DSD_EO@DF_EO/1.0/FORECAST.{country_codes}.AUSGRO.SRWGPAGDP._Z._T.XDC'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr = f'FORECAST.{country_codes}.AUSGRO.SRWGPAGDP._Z._T.XDC'
                url_v1 = f'{SDMX_V1_BASE}data/OECD.SDD.STD,AEO,DSD_EO@DF_EO,1.0/{filter_expr}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                url_v2_alt = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AEO/DSD_EO@DF_EO/1.0/{country_codes}.STP.AUSGRO.SRWGPAGDP._Z._T.XDC'
                result = self._make_request(url_v2_alt, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return {'success': False, 'endpoint': 'gdp_forecast', 'error': f'OECD forecast API structure has changed or endpoint unavailable. Original error: {result['error']}. Note: GDP forecast data may require a different API endpoint or is no longer publicly available.', 'parameters': {'countries': countries, 'start_date': start_date, 'end_date': end_date, 'note': 'Forecast functionality is currently unavailable due to OECD API changes'}, 'suggestion': 'Consider using historical GDP data and external forecast sources', 'status_code': result.get('status_code'), 'timestamp': int(datetime.now().timestamp())}
            try:
                df = pd.read_csv(StringIO(result['data']))
                if df.empty:
                    return OECDError('gdp_forecast', 'No forecast data available').to_dict()
                if 'OBS_VALUE' in df.columns:
                    df = df[['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE']].rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})

                    def apply_country_map(x):
                        v = CODE_TO_COUNTRY_GDP.get(x, x)
                        return v.replace('_', ' ').title() if v else x
                    df['country'] = df['country'].apply(apply_country_map)
                    df['date'] = df['date'].apply(self._oecd_date_to_python_date)
                    df = df[(df['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (df['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                    df['date'] = df['date'].astype(str)
                    df['value'] = df['value'].astype(float) * 1000000
                    df = df.sort_values(by=['date', 'country'])
                    result_data = df.replace({np.nan: None}).to_dict(orient='records')
                else:
                    result_data = []
                return {'success': True, 'endpoint': 'gdp_forecast', 'source': 'OECD', 'parameters': {'countries': countries, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('gdp_forecast', f'Failed to process forecast data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('gdp_forecast', str(e)).to_dict()

    def get_unemployment(self, countries: str='united_states', frequency: str='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get unemployment rate data from OECD"""
        try:
            if frequency not in ['quarter', 'annual', 'monthly']:
                return OECDError('unemployment', f'Invalid frequency: {frequency}').to_dict()
            if not start_date:
                start_date = '2000-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = {'monthly': 'M', 'quarter': 'Q', 'annual': 'A'}[frequency]
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AES@DF_AES/1.0/{country_codes}.{freq_code}.LRUN64TT.ST.A.SA'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr1 = f'{country_codes}.{freq_code}.LRUN64TT.ST.A.SA'
                url_v1_1 = f'{SDMX_V1_BASE}data/OECD.SDD.STD,AES,AES@DF_AES,1.0/{filter_expr1}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1_1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                url_v2_alt = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AES@DF_AES/1.0/{country_codes}.{freq_code}.LRUNTTTT.ST.A.SA'
                result = self._make_request(url_v2_alt, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return {'success': False, 'endpoint': 'unemployment', 'error': f'OECD unemployment API structure has changed or endpoint unavailable. Original error: {result['error']}. Note: Unemployment data may require a different API endpoint or is no longer publicly available.', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date, 'note': 'Unemployment functionality is currently unavailable due to OECD API changes'}, 'suggestion': 'Consider using alternative sources for unemployment data (e.g., World Bank, FRED)', 'status_code': result.get('status_code'), 'timestamp': int(datetime.now().timestamp())}
            try:
                df = pd.read_csv(StringIO(result['data']))
                if df.empty:
                    return OECDError('unemployment', 'No unemployment data available').to_dict()
                if 'OBS_VALUE' in df.columns:
                    df = df[['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE']].rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})

                    def apply_country_map(x):
                        v = CODE_TO_COUNTRY_GDP.get(x, x)
                        return v.replace('_', ' ').title() if v else x
                    df['country'] = df['country'].apply(apply_country_map)
                    df['date'] = df['date'].apply(self._oecd_date_to_python_date)
                    df = df[(df['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (df['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                    df['date'] = df['date'].astype(str)
                    df['value'] = df['value'].astype(float)
                    df = df.sort_values(by=['date', 'country'])
                    result_data = df.replace({np.nan: None}).to_dict(orient='records')
                else:
                    result_data = []
                return {'success': True, 'endpoint': 'unemployment', 'source': 'OECD', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('unemployment', f'Failed to process unemployment data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('unemployment', str(e)).to_dict()

    def get_economic_summary(self, country: str='united_states', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get comprehensive economic summary for a country"""
        result = {'success': True, 'country': country, 'start_date': start_date, 'end_date': end_date, 'timestamp': int(datetime.now().timestamp()), 'endpoints': {}, 'failed_endpoints': []}
        endpoints = [('gdp_real', lambda: self.get_gdp_real(countries=country, start_date=start_date, end_date=end_date)), ('cpi', lambda: self.get_consumer_price_index(countries=country, start_date=start_date, end_date=end_date)), ('gdp_forecast', lambda: self.get_gdp_forecast(countries=country, start_date=start_date, end_date=end_date)), ('unemployment', lambda: self.get_unemployment(countries=country, start_date=start_date, end_date=end_date))]
        overall_success = False
        for endpoint_name, endpoint_func in endpoints:
            try:
                endpoint_result = endpoint_func()
                result['endpoints'][endpoint_name] = endpoint_result
                if endpoint_result.get('success'):
                    overall_success = True
                else:
                    result['failed_endpoints'].append({'endpoint': endpoint_name, 'error': endpoint_result.get('error', 'Unknown error')})
            except Exception as e:
                result['failed_endpoints'].append({'endpoint': endpoint_name, 'error': str(e)})
        result['success'] = overall_success
        return result

    def get_country_list(self) -> Dict[str, Any]:
        """Get list of available countries"""
        try:
            return {'success': True, 'endpoint': 'country_list', 'available_countries': {'gdp': list(COUNTRY_TO_CODE_GDP.keys()), 'cpi': list(COUNTRY_TO_CODE_CPI.keys())}, 'country_codes': {'gdp': COUNTRY_TO_CODE_GDP, 'cpi': COUNTRY_TO_CODE_CPI}, 'expenditure_categories': list(EXPENDITURE_DICT.keys()), 'timestamp': int(datetime.now().timestamp())}
        except Exception as e:
            return OECDError('country_list', str(e)).to_dict()

    def get_interest_rates(self, countries: str='united_states', frequency: str='monthly', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get short-term interest rates data from OECD"""
        try:
            if frequency not in ['monthly', 'quarter', 'annual']:
                return OECDError('interest_rates', f'Invalid frequency: {frequency}').to_dict()
            if not start_date:
                start_date = '2000-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = {'monthly': 'M', 'quarter': 'Q', 'annual': 'A'}[frequency]
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/MEI/DP_LIVE/1.0/{country_codes}.{freq_code}.IR3TIB.ST.A'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return OECDError('interest_rates', result['error'], result.get('status_code')).to_dict()
            try:
                if result['format'] == 'xml':
                    data = self._parse_xml_to_dataframe(result['data'])
                else:
                    data = pd.read_csv(StringIO(result['data']))
                result_data = []
                return {'success': True, 'endpoint': 'interest_rates', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('interest_rates', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('interest_rates', str(e)).to_dict()

    def get_trade_balance(self, countries: str='united_states', frequency: str='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get trade balance data from OECD"""
        try:
            if frequency not in ['monthly', 'quarter', 'annual']:
                return OECDError('trade_balance', f'Invalid frequency: {frequency}').to_dict()
            if not start_date:
                start_date = '2000-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = {'monthly': 'M', 'quarter': 'Q', 'annual': 'A'}[frequency]
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/BOP/DSD_BOP6@DF_BAL,1.0/{country_codes}.{freq_code}.B6_GI.NMBK_SV.DD._T._T._T._T.XDC'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return OECDError('trade_balance', result['error'], result.get('status_code')).to_dict()
            try:
                if result['format'] == 'xml':
                    data = self._parse_xml_to_dataframe(result['data'])
                else:
                    data = pd.read_csv(StringIO(result['data']))
                result_data = []
                return {'success': True, 'endpoint': 'trade_balance', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('trade_balance', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('trade_balance', str(e)).to_dict()

def _oecd_date_to_python_date(self, input_date: Union[str, int]) -> date:
    """Date formatter helper."""
    input_date = str(input_date)
    if 'Q' in input_date:
        return pd.to_datetime(input_date).to_period('Q').start_time.date()
    if len(input_date) == 4:
        return date(int(input_date), 1, 1)
    if len(input_date) == 7:
        return pd.to_datetime(input_date).to_period('M').start_time.date()
    raise ValueError('Date not in expected format')

class ManualDataProvider(DataProvider):
    """Manual data input provider"""

    def __init__(self):
        self.price_data = {}
        self.economic_data = {}

    def add_price_data(self, symbol: str, data: pd.DataFrame):
        """Add price data manually"""
        self.price_data[symbol] = data

    def add_economic_data(self, indicator: str, data: pd.DataFrame):
        """Add economic data manually"""
        self.economic_data[indicator] = data

    def get_price_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Retrieve price data for symbols"""
        result_data = {}
        for symbol in symbols:
            if symbol in self.price_data:
                data = self.price_data[symbol].copy()
                data = self._filter_by_date(data, start_date, end_date)
                result_data[symbol] = data
        return result_data

    def get_economic_data(self, indicators: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Retrieve economic data"""
        result_data = {}
        for indicator in indicators:
            if indicator in self.economic_data:
                data = self.economic_data[indicator].copy()
                data = self._filter_by_date(data, start_date, end_date)
                result_data[indicator] = data
        return result_data

    def _filter_by_date(self, data: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """Filter data by date range"""
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            mask = (data['date'] >= start_date) & (data['date'] <= end_date)
            return data[mask]
        return data

def _filter_by_date(self, data: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Filter data by date range"""
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'])
        mask = (data['date'] >= start_date) & (data['date'] <= end_date)
        return data[mask]
    return data

class DataValidator:
    """Data validation and quality checks"""

    @staticmethod
    def validate_schema(data: pd.DataFrame, schema: DataSchema) -> Tuple[bool, List[str]]:
        """Validate data against schema"""
        errors = []
        for col in schema.required_columns:
            if col not in data.columns:
                errors.append(f'Missing required column: {col}')
        if len(data) < schema.min_observations:
            errors.append(f'Insufficient data: {len(data)} < {schema.min_observations}')
        for col in schema.numeric_columns:
            if col in data.columns:
                missing_ratio = data[col].isnull().sum() / len(data)
                if missing_ratio > schema.max_missing_ratio:
                    errors.append(f'Too much missing data in {col}: {missing_ratio:.2%}')
        for col in schema.date_columns:
            if col in data.columns:
                try:
                    pd.to_datetime(data[col])
                except:
                    errors.append(f'Invalid date format in column: {col}')
        return (len(errors) == 0, errors)

    @staticmethod
    def check_data_quality(data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        quality_report = {'total_rows': len(data), 'total_columns': len(data.columns), 'missing_data': {}, 'duplicates': 0, 'outliers': {}, 'data_types': {}}
        for col in data.columns:
            missing_count = data[col].isnull().sum()
            quality_report['missing_data'][col] = {'count': missing_count, 'percentage': missing_count / len(data) * 100}
        quality_report['duplicates'] = data.duplicated().sum()
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if not data[col].isnull().all():
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()
                quality_report['outliers'][col] = outliers
        quality_report['data_types'] = dict(data.dtypes)
        return quality_report

@staticmethod
def validate_schema(data: pd.DataFrame, schema: DataSchema) -> Tuple[bool, List[str]]:
    """Validate data against schema"""
    errors = []
    for col in schema.required_columns:
        if col not in data.columns:
            errors.append(f'Missing required column: {col}')
    if len(data) < schema.min_observations:
        errors.append(f'Insufficient data: {len(data)} < {schema.min_observations}')
    for col in schema.numeric_columns:
        if col in data.columns:
            missing_ratio = data[col].isnull().sum() / len(data)
            if missing_ratio > schema.max_missing_ratio:
                errors.append(f'Too much missing data in {col}: {missing_ratio:.2%}')
    for col in schema.date_columns:
        if col in data.columns:
            try:
                pd.to_datetime(data[col])
            except:
                errors.append(f'Invalid date format in column: {col}')
    return (len(errors) == 0, errors)

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

def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df['Date'] = pd.to_datetime(df['time'])
    df.set_index('Date', inplace=True)
    numeric_cols = ['open', 'close', 'high', 'low', 'volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.sort_index(inplace=True)
    return df

class AlpacaWrapper:
    """Complete wrapper for Alpaca trading and data operations"""

    def __init__(self, api_key: str=None, secret_key: str=None, paper: bool=True):
        self.api_key = api_key or os.getenv('ALPACA_API_KEY')
        self.secret_key = secret_key or os.getenv('ALPACA_SECRET_KEY')
        if not self.api_key or not self.secret_key:
            raise ValueError('API keys must be provided or set as environment variables')
        self.paper = paper
        try:
            self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper)
            self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            self.stream = StockDataStream(self.api_key, self.secret_key)
            logger.info(f'Initialized Alpaca clients (Paper: {paper})')
        except Exception as e:
            logger.error(f'Failed to initialize Alpaca clients: {e}')
            raise

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f'Failed to get market status: {e}')
            return False

    def get_market_clock(self) -> Dict:
        """Get detailed market status"""
        try:
            clock = self.trading_client.get_clock()
            return {'is_open': clock.is_open, 'timestamp': clock.timestamp, 'next_open': clock.next_open, 'next_close': clock.next_close}
        except Exception as e:
            logger.error(f'Failed to get market clock: {e}')
            return {}

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {'equity': float(account.equity), 'buying_power': float(account.buying_power), 'cash': float(account.cash), 'portfolio_value': float(account.portfolio_value), 'day_trade_count': int(account.daytrade_count), 'pattern_day_trader': account.pattern_day_trader}
        except Exception as e:
            logger.error(f'Failed to get account info: {e}')
            return {}

    def get_positions(self) -> pd.DataFrame:
        """Get all positions as DataFrame"""
        try:
            positions = self.trading_client.get_all_positions()
            if not positions:
                return pd.DataFrame()
            data = []
            for pos in positions:
                data.append({'symbol': pos.symbol, 'qty': float(pos.qty), 'market_value': float(pos.market_value), 'cost_basis': float(pos.cost_basis), 'unrealized_pl': float(pos.unrealized_pl), 'unrealized_plpc': float(pos.unrealized_plpc), 'avg_entry_price': float(pos.avg_entry_price), 'side': pos.side})
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f'Failed to get positions: {e}')
            return pd.DataFrame()

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get specific position"""
        try:
            pos = self.trading_client.get_open_position(symbol)
            return {'symbol': pos.symbol, 'qty': float(pos.qty), 'market_value': float(pos.market_value), 'avg_entry_price': float(pos.avg_entry_price), 'unrealized_pl': float(pos.unrealized_pl), 'unrealized_plpc': float(pos.unrealized_plpc), 'cost_basis': float(pos.cost_basis)}
        except Exception as e:
            logger.warning(f'No position found for {symbol}: {e}')
            return None

    def buy(self, symbol: str, qty: Union[int, float], order_type: str='market', limit_price: float=None, stop_price: float=None, extended_hours: bool=False) -> Optional[str]:
        """Place buy order"""
        return self._place_order(symbol, qty, OrderSide.BUY, order_type, limit_price, stop_price, extended_hours)

    def sell(self, symbol: str, qty: Union[int, float], order_type: str='market', limit_price: float=None, stop_price: float=None, extended_hours: bool=False) -> Optional[str]:
        """Place sell order"""
        return self._place_order(symbol, qty, OrderSide.SELL, order_type, limit_price, stop_price, extended_hours)

    def _place_order(self, symbol: str, qty: Union[int, float], side: OrderSide, order_type: str, limit_price: float=None, stop_price: float=None, extended_hours: bool=False) -> Optional[str]:
        """Internal order placement with improved error handling"""
        try:
            if not extended_hours and (not self.is_market_open()):
                logger.warning('Market is closed. Use extended_hours=True for after-hours trading')
            order_type = order_type.lower()
            if order_type == 'market':
                request = MarketOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, extended_hours=extended_hours)
            elif order_type == 'limit':
                if limit_price is None:
                    raise ValueError('limit_price required for limit orders')
                request = LimitOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, limit_price=limit_price, extended_hours=extended_hours)
            elif order_type == 'stop':
                if stop_price is None:
                    raise ValueError('stop_price required for stop orders')
                request = StopOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, stop_price=stop_price)
            elif order_type == 'stop_limit':
                if limit_price is None or stop_price is None:
                    raise ValueError('Both limit_price and stop_price required for stop-limit orders')
                request = StopLimitOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, limit_price=limit_price, stop_price=stop_price)
            else:
                raise ValueError(f'Unsupported order type: {order_type}')
            order = self.trading_client.submit_order(request)
            logger.info(f'Order placed: {order.id} - {side.value} {qty} {symbol}')
            return order.id
        except Exception as e:
            logger.error(f'Failed to place order: {e}')
            return None

    def place_trailing_stop(self, symbol: str, qty: Union[int, float], side: OrderSide, trail_percent: float=None, trail_price: float=None) -> Optional[str]:
        """Place trailing stop order"""
        try:
            if trail_percent is None and trail_price is None:
                raise ValueError('Either trail_percent or trail_price must be specified')
            request = TrailingStopOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.GTC, trail_percent=trail_percent, trail_price=trail_price)
            order = self.trading_client.submit_order(request)
            logger.info(f'Trailing stop order placed: {order.id}')
            return order.id
        except Exception as e:
            logger.error(f'Failed to place trailing stop order: {e}')
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order by ID"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f'Order cancelled: {order_id}')
            return True
        except Exception as e:
            logger.error(f'Failed to cancel order {order_id}: {e}')
            return False

    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            self.trading_client.cancel_orders()
            logger.info('All orders cancelled')
            return True
        except Exception as e:
            logger.error(f'Failed to cancel all orders: {e}')
            return False

    def get_orders(self, status: str='all', symbols: List[str]=None, limit: int=100) -> pd.DataFrame:
        """Get order history with improved filtering"""
        try:
            status_map = {'all': QueryOrderStatus.ALL, 'open': QueryOrderStatus.OPEN, 'closed': QueryOrderStatus.CLOSED, 'filled': QueryOrderStatus.CLOSED, 'cancelled': QueryOrderStatus.CANCELED}
            req = GetOrdersRequest(status=status_map.get(status.lower(), QueryOrderStatus.ALL), symbols=symbols, limit=limit)
            orders = self.trading_client.get_orders(req)
            if not orders:
                return pd.DataFrame()
            data = []
            for order in orders:
                data.append({'id': order.id, 'symbol': order.symbol, 'qty': float(order.qty), 'side': order.side.value, 'order_type': order.order_type.value, 'status': order.status.value, 'created_at': order.created_at, 'filled_price': float(order.filled_avg_price) if order.filled_avg_price else None, 'filled_qty': float(order.filled_qty) if order.filled_qty else 0, 'limit_price': float(order.limit_price) if order.limit_price else None, 'stop_price': float(order.stop_price) if order.stop_price else None})
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f'Failed to get orders: {e}')
            return pd.DataFrame()

    def close_position(self, symbol: str, qty: Optional[Union[int, float]]=None) -> bool:
        """Close specific position (all or partial)"""
        try:
            if qty:
                from alpaca.trading.requests import ClosePositionRequest
                self.trading_client.close_position(symbol, close_options=ClosePositionRequest(qty=str(qty)))
            else:
                self.trading_client.close_position(symbol)
            logger.info(f'Position closed for {symbol}')
            return True
        except Exception as e:
            logger.error(f'Failed to close position for {symbol}: {e}')
            return False

    def close_all_positions(self) -> bool:
        """Close all positions"""
        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            logger.info('All positions closed')
            return True
        except Exception as e:
            logger.error(f'Failed to close all positions: {e}')
            return False

    def get_bars(self, symbols: Union[str, List[str]], timeframe: str='1Day', start: datetime=None, end: datetime=None, limit: int=1000) -> pd.DataFrame:
        """Get historical bar data with improved timeframe handling"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            if start is None:
                start = datetime.now() - timedelta(days=365)
            tf_map = {'1Min': TimeFrame(1, TimeFrameUnit.Minute), '5Min': TimeFrame(5, TimeFrameUnit.Minute), '15Min': TimeFrame(15, TimeFrameUnit.Minute), '30Min': TimeFrame(30, TimeFrameUnit.Minute), '1Hour': TimeFrame(1, TimeFrameUnit.Hour), '4Hour': TimeFrame(4, TimeFrameUnit.Hour), '1Day': TimeFrame(1, TimeFrameUnit.Day), '1Week': TimeFrame(1, TimeFrameUnit.Week), '1Month': TimeFrame(1, TimeFrameUnit.Month)}
            timeframe_obj = tf_map.get(timeframe)
            if timeframe_obj is None:
                raise ValueError(f'Unsupported timeframe: {timeframe}')
            request = StockBarsRequest(symbol_or_symbols=symbols, timeframe=timeframe_obj, start=start, end=end, limit=limit)
            bars = self.data_client.get_stock_bars(request)
            return bars.df
        except Exception as e:
            logger.error(f'Failed to get bars: {e}')
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        try:
            bars = self.data_client.get_stock_latest_bar([symbol])
            return float(bars[symbol].close)
        except Exception as e:
            logger.error(f'Failed to get latest price for {symbol}: {e}')
            return None

    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest bid/ask quote"""
        try:
            quote = self.data_client.get_stock_latest_quote([symbol])
            q = quote[symbol]
            return {'symbol': symbol, 'bid': float(q.bid_price), 'ask': float(q.ask_price), 'bid_size': int(q.bid_size), 'ask_size': int(q.ask_size), 'timestamp': q.timestamp}
        except Exception as e:
            logger.error(f'Failed to get latest quote for {symbol}: {e}')
            return None

    def get_quotes(self, symbols: Union[str, List[str]], start: datetime=None, limit: int=1000) -> pd.DataFrame:
        """Get historical quote data"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            if start is None:
                start = datetime.now() - timedelta(days=1)
            request = StockQuotesRequest(symbol_or_symbols=symbols, start=start, limit=limit)
            quotes = self.data_client.get_stock_quotes(request)
            return quotes.df
        except Exception as e:
            logger.error(f'Failed to get quotes: {e}')
            return pd.DataFrame()

    def get_trades(self, symbols: Union[str, List[str]], start: datetime=None, limit: int=1000) -> pd.DataFrame:
        """Get historical trade data"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            if start is None:
                start = datetime.now() - timedelta(days=1)
            request = StockTradesRequest(symbol_or_symbols=symbols, start=start, limit=limit)
            trades = self.data_client.get_stock_trades(request)
            return trades.df
        except Exception as e:
            logger.error(f'Failed to get trades: {e}')
            return pd.DataFrame()

    def get_portfolio_history(self, period: str='1M', timeframe: str='1D') -> pd.DataFrame:
        """Get portfolio performance history"""
        try:
            history = self.trading_client.get_portfolio_history(period=period, timeframe=timeframe)
            data = {'timestamp': history.timestamp, 'equity': history.equity, 'profit_loss': history.profit_loss, 'profit_loss_pct': history.profit_loss_pct}
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            return df.set_index('timestamp')
        except Exception as e:
            logger.error(f'Failed to get portfolio history: {e}')
            return pd.DataFrame()

    def start_stream(self, symbols: List[str], on_bar=None, on_trade=None, on_quote=None):
        """Start real-time data stream"""
        try:
            if on_bar:
                self.stream.subscribe_bars(on_bar, *symbols)
            if on_trade:
                self.stream.subscribe_trades(on_trade, *symbols)
            if on_quote:
                self.stream.subscribe_quotes(on_quote, *symbols)
            logger.info(f'Starting stream for {symbols}')
            self.stream.run()
        except Exception as e:
            logger.error(f'Failed to start stream: {e}')

    def stop_stream(self):
        """Stop real-time data stream"""
        try:
            self.stream.stop()
            logger.info('Stream stopped')
        except Exception as e:
            logger.error(f'Failed to stop stream: {e}')

    def get_watchlist(self, watchlist_id: str=None) -> pd.DataFrame:
        """Get watchlist"""
        try:
            if watchlist_id:
                watchlist = self.trading_client.get_watchlist_by_id(watchlist_id)
            else:
                watchlists = self.trading_client.get_watchlists()
                if not watchlists:
                    return pd.DataFrame()
                watchlist = watchlists[0]
            symbols = [asset.symbol for asset in watchlist.assets]
            return pd.DataFrame({'symbol': symbols})
        except Exception as e:
            logger.error(f'Failed to get watchlist: {e}')
            return pd.DataFrame()

def get_portfolio_history(self, period: str='1M', timeframe: str='1D') -> pd.DataFrame:
    """Get portfolio performance history"""
    try:
        history = self.trading_client.get_portfolio_history(period=period, timeframe=timeframe)
        data = {'timestamp': history.timestamp, 'equity': history.equity, 'profit_loss': history.profit_loss, 'profit_loss_pct': history.profit_loss_pct}
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df.set_index('timestamp')
    except Exception as e:
        logger.error(f'Failed to get portfolio history: {e}')
        return pd.DataFrame()

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

def execute_query(self, data_type: str, **params) -> WrapperResponse:
    """Generic query executor"""
    method_map = {'equity': self.get_equity_historical, 'eps': self.get_historical_eps, 'etf': self.get_etf_historical}
    if data_type not in method_map:
        return WrapperResponse(success=False, error=f'Unknown data type: {data_type}')
    return method_map[data_type](**params)

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

class DebugIMFGUI:

    def __init__(self):
        self.imf_wrapper = DebugIMFWrapper()
        self.current_data = None

    def setup_gui(self):
        dpg.create_context()
        with dpg.window(label='Debug IMF Data Terminal', tag='main_window'):
            with dpg.group(horizontal=True):
                dpg.add_text('IMF Data Provider (Debug Mode)')
                dpg.add_button(label='Test Connection', callback=self.test_connection)
                dpg.add_button(label='Clear Debug', callback=self.clear_debug)
            dpg.add_text('', tag='connection_status')
            dpg.add_separator()
            dpg.add_text('Direction of Trade Parameters:')
            with dpg.group(horizontal=True):
                dpg.add_text('Country:')
                dpg.add_input_text(tag='country', default_value='US', width=80)
                dpg.add_text('Counterpart:')
                dpg.add_input_text(tag='counterpart', default_value='CN', width=80)
            with dpg.group(horizontal=True):
                dpg.add_text('Direction:')
                dpg.add_combo(['exports', 'imports', 'balance'], tag='direction', default_value='exports', width=100)
                dpg.add_text('Frequency:')
                dpg.add_combo(['A', 'Q', 'M'], tag='frequency', default_value='A', width=60)
            with dpg.group(horizontal=True):
                dpg.add_text('Start Year:')
                dpg.add_input_text(tag='start_date', default_value='2022', width=80)
                dpg.add_text('End Year:')
                dpg.add_input_text(tag='end_date', default_value='2023', width=80)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label='Get Trade Data', callback=self.get_trade_data)
                dpg.add_button(label='Export CSV', callback=self.export_csv)
                dpg.add_button(label='Clear Data', callback=self.clear_data)
            dpg.add_separator()
            dpg.add_text('Status:')
            dpg.add_text('', tag='status_text')
            dpg.add_separator()
            dpg.add_text('Debug Log:')
            dpg.add_input_text(tag='debug_log', multiline=True, height=200, width=750, readonly=True)
            dpg.add_separator()
            dpg.add_text('Data Preview:')
            with dpg.table(header_row=True, tag='data_table', height=200):
                pass
            dpg.add_text('Summary:')
            dpg.add_text('', tag='data_summary')
        dpg.create_viewport(title='Debug IMF Terminal', width=800, height=800)
        dpg.setup_dearpygui()
        dpg.set_primary_window('main_window', True)
        dpg.show_viewport()

    def clear_debug(self):
        self.imf_wrapper.debug_log = []
        dpg.set_value('debug_log', '')

    def update_debug_display(self):
        debug_text = self.imf_wrapper.get_debug_log()
        dpg.set_value('debug_log', debug_text)

    def test_connection(self):
        try:
            dpg.set_value('connection_status', 'Testing connection...')
            result = self.imf_wrapper.test_simple_connection()
            if result.success:
                dpg.set_value('connection_status', '✓ Connection successful')
            else:
                dpg.set_value('connection_status', f'✗ Connection failed: {result.error}')
            self.update_debug_display()
        except Exception as e:
            dpg.set_value('connection_status', f'✗ Test error: {str(e)}')
            self.update_debug_display()

    def get_trade_data(self):
        try:
            params = {'country': dpg.get_value('country'), 'counterpart': dpg.get_value('counterpart'), 'direction': dpg.get_value('direction'), 'frequency': dpg.get_value('frequency'), 'start_date': dpg.get_value('start_date'), 'end_date': dpg.get_value('end_date')}
            dpg.set_value('status_text', 'Fetching trade data...')
            result = self.imf_wrapper.get_direction_of_trade(**params)
            if result.success:
                self.current_data = result.data
                self._display_data(result.data)
                dpg.set_value('status_text', f'✓ {result.message}')
                self._update_summary(result.data)
            else:
                dpg.set_value('status_text', f'✗ {result.error}')
            self.update_debug_display()
        except Exception as e:
            dpg.set_value('status_text', f'✗ Error: {str(e)}')
            self.update_debug_display()

    def export_csv(self):
        if self.current_data is None:
            dpg.set_value('status_text', 'No data to export')
            return
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'imf_debug_{timestamp}.csv'
            self.current_data.to_csv(filename, index=False)
            dpg.set_value('status_text', f'✓ Exported to {filename}')
        except Exception as e:
            dpg.set_value('status_text', f'✗ Export error: {str(e)}')

    def clear_data(self):
        self.current_data = None
        dpg.delete_item('data_table', children_only=True)
        dpg.set_value('data_summary', '')
        dpg.set_value('status_text', 'Data cleared')

    def _display_data(self, df: pd.DataFrame):
        dpg.delete_item('data_table', children_only=True)
        if df is None or df.empty:
            return
        columns = list(df.columns)
        for col in columns:
            dpg.add_table_column(label=col, parent='data_table')
        display_df = df.head(20)
        for _, row in display_df.iterrows():
            with dpg.table_row(parent='data_table'):
                for col in columns:
                    value = str(row[col])
                    if len(value) > 15:
                        value = value[:12] + '...'
                    dpg.add_text(value)

    def _update_summary(self, df: pd.DataFrame):
        if df is None or df.empty:
            return
        summary = f'Rows: {len(df)}, Columns: {len(df.columns)}\n'
        summary += f'Columns: {', '.join(df.columns)}\n'
        if 'date' in df.columns:
            summary += f'Date range: {df['date'].min()} to {df['date'].max()}\n'
        if 'value' in df.columns:
            summary += f'Value range: {df['value'].min():.2f} to {df['value'].max():.2f}'
        dpg.set_value('data_summary', summary)

    def run(self):
        self.setup_gui()
        dpg.start_dearpygui()
        dpg.destroy_context()

def update_debug_display(self):
    debug_text = self.imf_wrapper.get_debug_log()
    dpg.set_value('debug_log', debug_text)

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

