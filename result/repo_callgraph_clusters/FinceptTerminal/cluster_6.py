# Cluster 6

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python econdb_data.py <command> <args>', 'commands': ['indicator <symbol> <country> [start_date] [end_date] [transform]', 'profile <country> [latest]', 'main <country> [start_date] [end_date] [frequency] [transform]', 'list-indicators', 'list-countries']}))
        sys.exit(1)
    command = sys.argv[1]
    try:
        if command == 'indicator':
            if len(sys.argv) < 4:
                print(json.dumps({'error': 'Usage: python econdb_data.py indicator <symbol> <country> [start_date] [end_date] [transform]'}))
                sys.exit(1)
            symbol = sys.argv[2]
            country = sys.argv[3]
            start_date = sys.argv[4] if len(sys.argv) > 4 else None
            end_date = sys.argv[5] if len(sys.argv) > 5 else None
            transform = sys.argv[6] if len(sys.argv) > 6 else None
            result = asyncio.run(get_economic_indicators(symbol, country, start_date, end_date, transform))
            print(json.dumps(result, indent=2))
        elif command == 'profile':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python econdb_data.py profile <country> [latest]'}))
                sys.exit(1)
            country = sys.argv[2]
            latest = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
            result = asyncio.run(get_country_profile(country, latest))
            print(json.dumps(result, indent=2))
        elif command == 'main':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python econdb_data.py main <country> [start_date] [end_date] [frequency] [transform]'}))
                sys.exit(1)
            country = sys.argv[2]
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            frequency = sys.argv[5] if len(sys.argv) > 5 else 'quarter'
            transform = sys.argv[6] if len(sys.argv) > 6 else 'toya'
            result = asyncio.run(get_main_indicators(country, start_date, end_date, frequency, transform))
            print(json.dumps(result, indent=2))
        elif command == 'list-indicators':
            result = asyncio.run(list_indicators())
            print(json.dumps(result, indent=2))
        elif command == 'list-countries':
            result = asyncio.run(list_countries())
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({'error': f'Unknown command: {command}'}))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

class BEAWrapper:
    """Comprehensive BEA API wrapper with fault tolerance"""

    def __init__(self, api_key: Optional[str]=None):
        self.api_key = api_key or os.environ.get('BEA_API_KEY', '')
        self.base_url = 'https://apps.bea.gov/api/data/'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept-Terminal/1.0'})

    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Centralized request handler with comprehensive error handling"""
        try:
            params['UserID'] = self.api_key
            params['method'] = method
            params['resultformat'] = 'JSON'
            if 'Year' not in params and method.startswith('GetData'):
                current_year = datetime.now().year
                params['Year'] = str(current_year)
            url = f'{self.base_url}?{urlencode(params)}'
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'BEAAPI' in data:
                if 'Error' in data['BEAAPI']:
                    error_desc = data['BEAAPI']['Error'].get('ErrorDesc', 'Unknown BEA API error')
                    return BEAError(method, error_desc).to_dict()
                results = data['BEAAPI'].get('Results', {})
                if method == 'GetDatasetList':
                    return {'success': True, 'endpoint': method, 'data': results.get('Dataset', []), 'timestamp': int(datetime.now().timestamp())}
                elif method == 'GetParameterList':
                    return {'success': True, 'endpoint': method, 'data': results.get('Parameter', []), 'dataset_name': params.get('DatasetName', ''), 'timestamp': int(datetime.now().timestamp())}
                elif method in ['GetParameterValues', 'GetParameterValuesFiltered']:
                    return {'success': True, 'endpoint': method, 'data': results.get('ParamValue', []), 'parameter': params.get('ParameterName', ''), 'dataset_name': params.get('DatasetName', ''), 'timestamp': int(datetime.now().timestamp())}
                else:
                    return {'success': True, 'endpoint': method, 'data': results.get('Data', []), 'dataset_name': params.get('DatasetName', ''), 'parameters': {k: v for k, v in params.items() if k not in ['UserID', 'method', 'resultformat']}, 'notes': results.get('Notes', []), 'statistics': results.get('Stat', []), 'dimensions': results.get('Dimensions', []), 'timestamp': int(datetime.now().timestamp())}
            return BEAError(method, 'Unexpected response format').to_dict()
        except requests.exceptions.RequestException as e:
            return BEAError(method, f'Network error: {str(e)}').to_dict()
        except json.JSONDecodeError as e:
            return BEAError(method, f'JSON decode error: {str(e)}').to_dict()
        except Exception as e:
            return BEAError(method, f'Unexpected error: {str(e)}').to_dict()

    def get_dataset_list(self) -> Dict[str, Any]:
        """Get list of all available datasets"""
        try:
            result = self._make_request('GetDatasetList', {})
            if result.get('success'):
                dataset_descriptions = {'NIPA': 'National Income and Product Accounts', 'NIUnderlyingDetail': 'NIPA Underlying Detail', 'FixedAssets': 'Fixed Assets', 'MNE': 'Multinational Enterprises', 'GDPbyIndustry': 'GDP by Industry', 'ITA': 'International Transactions', 'IIP': 'International Investment Position', 'InputOutput': 'Input-Output Accounts', 'UnderlyingGDPbyIndustry': 'GDP by Industry - Underlying Detail', 'IntlServTrade': 'International Services Trade', 'Regional': 'Regional Economic Accounts'}
                for dataset in result.get('data', []):
                    dataset_name = dataset.get('DatasetName', '')
                    if dataset_name in dataset_descriptions:
                        dataset['Description'] = dataset_descriptions[dataset_name]
            return result
        except Exception as e:
            return BEAError('GetDatasetList', str(e)).to_dict()

    def get_parameter_list(self, dataset_name: str) -> Dict[str, Any]:
        """Get list of parameters for a specific dataset"""
        try:
            if not dataset_name:
                return BEAError('GetParameterList', 'DatasetName is required').to_dict()
            params = {'DatasetName': dataset_name}
            result = self._make_request('GetParameterList', params)
            return result
        except Exception as e:
            return BEAError('GetParameterList', str(e)).to_dict()

    def get_parameter_values(self, dataset_name: str, parameter_name: str) -> Dict[str, Any]:
        """Get all possible values for a specific parameter"""
        try:
            if not dataset_name or not parameter_name:
                return BEAError('GetParameterValues', 'DatasetName and ParameterName are required').to_dict()
            params = {'DatasetName': dataset_name, 'ParameterName': parameter_name}
            result = self._make_request('GetParameterValues', params)
            return result
        except Exception as e:
            return BEAError('GetParameterValues', str(e)).to_dict()

    def get_parameter_values_filtered(self, dataset_name: str, parameter_name: str, target_parameter: str) -> Dict[str, Any]:
        """Get filtered parameter values based on another parameter"""
        try:
            if not dataset_name or not parameter_name or (not target_parameter):
                return BEAError('GetParameterValuesFiltered', 'DatasetName, ParameterName, and TargetParameter are required').to_dict()
            params = {'DatasetName': dataset_name, 'ParameterName': parameter_name, 'TargetParameter': target_parameter}
            result = self._make_request('GetParameterValuesFiltered', params)
            return result
        except Exception as e:
            return BEAError('GetParameterValuesFiltered', str(e)).to_dict()

    def get_nipa_data(self, table_name: str, frequency: str='A', year: str=None, year_range: str=None) -> Dict[str, Any]:
        """Get National Income and Product Accounts data"""
        try:
            if not table_name:
                return BEAError('NIPA', 'TableName is required').to_dict()
            params = {'DatasetName': 'NIPA', 'TableName': table_name, 'Frequency': frequency}
            if year:
                params['Year'] = year
            elif year_range:
                params['Year'] = year_range
            elif frequency == 'Q':
                params['Year'] = f'{datetime.now().year - 1}Q1,{datetime.now().year}Q4'
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('NIPA', str(e)).to_dict()

    def get_ni_underlying_detail(self, table_name: str, frequency: str='A', year: str=None) -> Dict[str, Any]:
        """Get NIPA Underlying Detail data"""
        try:
            if not table_name:
                return BEAError('NIUnderlyingDetail', 'TableName is required').to_dict()
            params = {'DatasetName': 'NIUnderlyingDetail', 'TableName': table_name, 'Frequency': frequency}
            if year:
                params['Year'] = year
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('NIUnderlyingDetail', str(e)).to_dict()

    def get_fixed_assets(self, table_name: str, year: str=None) -> Dict[str, Any]:
        """Get Fixed Assets data"""
        try:
            if not table_name:
                return BEAError('FixedAssets', 'TableName is required').to_dict()
            params = {'DatasetName': 'FixedAssets', 'TableName': table_name}
            if year:
                params['Year'] = year
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('FixedAssets', str(e)).to_dict()

    def get_mne_data(self, series_id: str=None, direction: str='Outward', classification: str='Country', year: str=None, country: str=None, industry: str=None, state: str=None, ownership_level: str=None, nonbank_affiliates_only: str=None, get_footnotes: str='No') -> Dict[str, Any]:
        """Get Multinational Enterprises data"""
        try:
            params = {'DatasetName': 'MNE'}
            if direction:
                params['DirectionOfInvestment'] = direction
            else:
                return BEAError('MNE', 'DirectionOfInvestment is required').to_dict()
            if series_id:
                params['SeriesID'] = series_id
            if classification:
                params['Classification'] = classification
            if year:
                params['Year'] = year
            if country:
                params['Country'] = country
            if industry:
                params['Industry'] = industry
            if state:
                params['State'] = state
            if ownership_level:
                params['OwnershipLevel'] = ownership_level
            if nonbank_affiliates_only:
                params['NonBankAffiliatesOnly'] = nonbank_affiliates_only
            if get_footnotes:
                params['GetFootnotes'] = get_footnotes
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('MNE', str(e)).to_dict()

    def get_gdp_by_industry(self, table_id: str, year: str=None, frequency: str='A', industry: str='ALL') -> Dict[str, Any]:
        """Get GDP by Industry data"""
        try:
            if not table_id:
                return BEAError('GDPbyIndustry', 'TableID is required').to_dict()
            params = {'DatasetName': 'GDPbyIndustry', 'TableID': table_id, 'Frequency': frequency, 'Year': year, 'Industry': industry}
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('GDPbyIndustry', str(e)).to_dict()

    def get_international_transactions(self, indicator: str=None, area_or_country: str='AllCountries', frequency: str='A', year: str=None) -> Dict[str, Any]:
        """Get International Transactions Accounts data"""
        try:
            params = {'DatasetName': 'ITA', 'AreaOrCountry': area_or_country, 'Frequency': frequency, 'Year': year}
            if indicator:
                params['Indicator'] = indicator
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('ITA', str(e)).to_dict()

    def get_international_investment_position(self, type_of_investment: str=None, component: str=None, frequency: str='A', year: str=None) -> Dict[str, Any]:
        """Get International Investment Position data"""
        try:
            params = {'DatasetName': 'IIP', 'Frequency': frequency, 'Year': year}
            if type_of_investment:
                params['TypeOfInvestment'] = type_of_investment
            if component:
                params['Component'] = component
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('IIP', str(e)).to_dict()

    def get_input_output(self, table_id: str, year: str=None) -> Dict[str, Any]:
        """Get Input-Output Accounts data"""
        try:
            if not table_id:
                return BEAError('InputOutput', 'TableID is required').to_dict()
            params = {'DatasetName': 'InputOutput', 'TableID': table_id}
            if year:
                params['Year'] = year
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('InputOutput', str(e)).to_dict()

    def get_underlying_gdp_by_industry(self, table_id: str, year: str=None, frequency: str='A', industry: str='ALL') -> Dict[str, Any]:
        """Get GDP by Industry - Underlying Detail data"""
        try:
            if not table_id:
                return BEAError('UnderlyingGDPbyIndustry', 'TableID is required').to_dict()
            params = {'DatasetName': 'UnderlyingGDPbyIndustry', 'TableID': table_id, 'Frequency': frequency, 'Year': year, 'Industry': industry}
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('UnderlyingGDPbyIndustry', str(e)).to_dict()

    def get_international_services_trade(self, type_of_service: str=None, trade_direction: str=None, affiliation: str=None, area_or_country: str='AllCountries', year: str=None) -> Dict[str, Any]:
        """Get International Services Trade data"""
        try:
            params = {'DatasetName': 'IntlServTrade', 'AreaOrCountry': area_or_country, 'Year': year}
            if type_of_service:
                params['TypeOfService'] = type_of_service
            if trade_direction:
                params['TradeDirection'] = trade_direction
            if affiliation:
                params['Affiliation'] = affiliation
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('IntlServTrade', str(e)).to_dict()

    def get_regional_data(self, table_name: str, line_code: str='ALL', geo_fips: str='STATE', year: str=None) -> Dict[str, Any]:
        """Get Regional Economic Accounts data"""
        try:
            if not table_name:
                return BEAError('Regional', 'TableName is required').to_dict()
            params = {'DatasetName': 'Regional', 'TableName': table_name, 'LineCode': line_code, 'GeoFIPS': geo_fips}
            if year:
                params['Year'] = year
            result = self._make_request('GetData', params)
            return result
        except Exception as e:
            return BEAError('Regional', str(e)).to_dict()

    def get_economic_overview(self, year: str=None) -> Dict[str, Any]:
        """Get comprehensive economic overview from multiple datasets"""
        result = {'success': True, 'overview_type': 'economic_overview', 'year': year or str(datetime.now().year), 'timestamp': int(datetime.now().timestamp()), 'datasets': {}, 'failed_datasets': []}
        overview_datasets = [('NIPA GDP', lambda: self.get_nipa_data('T10101', 'Q', year)), ('GDP by Industry', lambda: self.get_gdp_by_industry('1', year, 'A')), ('International Transactions', lambda: self.get_international_transactions('BalGds', 'AllCountries', 'A', year)), ('Regional Data', lambda: self.get_regional_data('SAINC1', '1', 'STATE', year))]
        overall_success = False
        for dataset_name, dataset_func in overview_datasets:
            try:
                dataset_result = dataset_func()
                result['datasets'][dataset_name] = dataset_result
                if dataset_result.get('success'):
                    overall_success = True
                else:
                    result['failed_datasets'].append({'dataset': dataset_name, 'error': dataset_result.get('error', 'Unknown error')})
            except Exception as e:
                result['failed_datasets'].append({'dataset': dataset_name, 'error': str(e)})
        result['success'] = overall_success
        return result

    def get_regional_snapshot(self, geo_fips: str='USA', year: str=None) -> Dict[str, Any]:
        """Get comprehensive regional economic snapshot"""
        result = {'success': True, 'snapshot_type': 'regional_snapshot', 'geo_fips': geo_fips, 'year': year or str(datetime.now().year), 'timestamp': int(datetime.now().timestamp()), 'datasets': {}, 'failed_datasets': []}
        regional_datasets = [('Personal Income', lambda: self.get_regional_data('SAINC1', '1', geo_fips, year)), ('GDP by State', lambda: self.get_regional_data('SAGDP2N', '2', geo_fips, year)), ('Real GDP', lambda: self.get_regional_data('SAGDP9N', '2', geo_fips, year))]
        overall_success = False
        for dataset_name, dataset_func in regional_datasets:
            try:
                dataset_result = dataset_func()
                result['datasets'][dataset_name] = dataset_result
                if dataset_result.get('success'):
                    overall_success = True
                else:
                    result['failed_datasets'].append({'dataset': dataset_name, 'error': dataset_result.get('error', 'Unknown error')})
            except Exception as e:
                result['failed_datasets'].append({'dataset': dataset_name, 'error': str(e)})
        result['success'] = overall_success
        return result

def get_economic_overview(self, year: str=None) -> Dict[str, Any]:
    """Get comprehensive economic overview from multiple datasets"""
    result = {'success': True, 'overview_type': 'economic_overview', 'year': year or str(datetime.now().year), 'timestamp': int(datetime.now().timestamp()), 'datasets': {}, 'failed_datasets': []}
    overview_datasets = [('NIPA GDP', lambda: self.get_nipa_data('T10101', 'Q', year)), ('GDP by Industry', lambda: self.get_gdp_by_industry('1', year, 'A')), ('International Transactions', lambda: self.get_international_transactions('BalGds', 'AllCountries', 'A', year)), ('Regional Data', lambda: self.get_regional_data('SAINC1', '1', 'STATE', year))]
    overall_success = False
    for dataset_name, dataset_func in overview_datasets:
        try:
            dataset_result = dataset_func()
            result['datasets'][dataset_name] = dataset_result
            if dataset_result.get('success'):
                overall_success = True
            else:
                result['failed_datasets'].append({'dataset': dataset_name, 'error': dataset_result.get('error', 'Unknown error')})
        except Exception as e:
            result['failed_datasets'].append({'dataset': dataset_name, 'error': str(e)})
    result['success'] = overall_success
    return result

def main():
    """CLI interface for BEA Data Fetcher"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python bea_data.py <command> <args>', 'available_commands': ['dataset_list', 'parameter_list <dataset_name>', 'parameter_values <dataset_name> <parameter_name>', 'parameter_values_filtered <dataset_name> <parameter_name> <target_parameter>', 'nipa <table_name> [frequency] [year]', 'ni_underlying <table_name> [frequency] [year]', 'fixed_assets <table_name> [year]', 'mne <direction> [classification] [year] [country] [industry] [state] [ownership_level] [nonbank_affiliates_only] [get_footnotes]', 'gdp_by_industry <table_id> [year] [frequency] [industry]', 'international_transactions [indicator] [area_or_country] [frequency] [year]', 'international_investment [type_of_investment] [component] [frequency] [year]', 'input_output <table_id> [year]', 'underlying_gdp_industry <table_id> [year] [frequency] [industry]', 'international_services [type_of_service] [trade_direction] [affiliation] [area_or_country] [year]', 'regional <table_name> [line_code] [geo_fips] [year]', 'economic_overview [year]', 'regional_snapshot [geo_fips] [year]']}))
        sys.exit(1)
    command = sys.argv[1]
    wrapper = BEAWrapper()
    try:
        if command == 'dataset_list':
            result = wrapper.get_dataset_list()
            print(json.dumps(result, indent=2))
        elif command == 'parameter_list':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py parameter_list <dataset_name>'}))
                sys.exit(1)
            dataset_name = sys.argv[2]
            result = wrapper.get_parameter_list(dataset_name)
            print(json.dumps(result, indent=2))
        elif command == 'parameter_values':
            if len(sys.argv) < 4:
                print(json.dumps({'error': 'Usage: python bea_data.py parameter_values <dataset_name> <parameter_name>'}))
                sys.exit(1)
            dataset_name = sys.argv[2]
            parameter_name = sys.argv[3]
            result = wrapper.get_parameter_values(dataset_name, parameter_name)
            print(json.dumps(result, indent=2))
        elif command == 'parameter_values_filtered':
            if len(sys.argv) < 5:
                print(json.dumps({'error': 'Usage: python bea_data.py parameter_values_filtered <dataset_name> <parameter_name> <target_parameter>'}))
                sys.exit(1)
            dataset_name = sys.argv[2]
            parameter_name = sys.argv[3]
            target_parameter = sys.argv[4]
            result = wrapper.get_parameter_values_filtered(dataset_name, parameter_name, target_parameter)
            print(json.dumps(result, indent=2))
        elif command == 'nipa':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py nipa <table_name> [frequency] [year]'}))
                sys.exit(1)
            table_name = sys.argv[2]
            frequency = sys.argv[3] if len(sys.argv) > 3 else 'A'
            year = sys.argv[4] if len(sys.argv) > 4 else None
            result = wrapper.get_nipa_data(table_name, frequency, year)
            print(json.dumps(result, indent=2))
        elif command == 'ni_underlying':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py ni_underlying <table_name> [frequency] [year]'}))
                sys.exit(1)
            table_name = sys.argv[2]
            frequency = sys.argv[3] if len(sys.argv) > 3 else 'A'
            year = sys.argv[4] if len(sys.argv) > 4 else None
            result = wrapper.get_ni_underlying_detail(table_name, frequency, year)
            print(json.dumps(result, indent=2))
        elif command == 'fixed_assets':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py fixed_assets <table_name> [year]'}))
                sys.exit(1)
            table_name = sys.argv[2]
            year = sys.argv[3] if len(sys.argv) > 3 else None
            result = wrapper.get_fixed_assets(table_name, year)
            print(json.dumps(result, indent=2))
        elif command == 'mne':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py mne <direction> [classification] [year] [country] [industry] [state] [ownership_level] [nonbank_affiliates_only] [get_footnotes]'}))
                sys.exit(1)
            direction = sys.argv[2]
            classification = sys.argv[3] if len(sys.argv) > 3 else 'Country'
            year = sys.argv[4] if len(sys.argv) > 4 else None
            country = sys.argv[5] if len(sys.argv) > 5 else None
            industry = sys.argv[6] if len(sys.argv) > 6 else None
            state = sys.argv[7] if len(sys.argv) > 7 else None
            ownership_level = sys.argv[8] if len(sys.argv) > 8 else None
            nonbank_affiliates_only = sys.argv[9] if len(sys.argv) > 9 else None
            get_footnotes = sys.argv[10] if len(sys.argv) > 10 else 'No'
            result = wrapper.get_mne_data(None, direction, classification, year, country, industry, state, ownership_level, nonbank_affiliates_only, get_footnotes)
            print(json.dumps(result, indent=2))
        elif command == 'gdp_by_industry':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py gdp_by_industry <table_id> [year] [frequency] [industry]'}))
                sys.exit(1)
            table_id = sys.argv[2]
            year = sys.argv[3] if len(sys.argv) > 3 else None
            frequency = sys.argv[4] if len(sys.argv) > 4 else 'A'
            industry = sys.argv[5] if len(sys.argv) > 5 else 'ALL'
            result = wrapper.get_gdp_by_industry(table_id, year, frequency, industry)
            print(json.dumps(result, indent=2))
        elif command == 'international_transactions':
            indicator = sys.argv[2] if len(sys.argv) > 2 else None
            area_or_country = sys.argv[3] if len(sys.argv) > 3 else 'AllCountries'
            frequency = sys.argv[4] if len(sys.argv) > 4 else 'A'
            year = sys.argv[5] if len(sys.argv) > 5 else None
            result = wrapper.get_international_transactions(indicator, area_or_country, frequency, year)
            print(json.dumps(result, indent=2))
        elif command == 'international_investment':
            type_of_investment = sys.argv[2] if len(sys.argv) > 2 else None
            component = sys.argv[3] if len(sys.argv) > 3 else None
            frequency = sys.argv[4] if len(sys.argv) > 4 else 'A'
            year = sys.argv[5] if len(sys.argv) > 5 else None
            result = wrapper.get_international_investment_position(type_of_investment, component, frequency, year)
            print(json.dumps(result, indent=2))
        elif command == 'input_output':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py input_output <table_id> [year]'}))
                sys.exit(1)
            table_id = sys.argv[2]
            year = sys.argv[3] if len(sys.argv) > 3 else None
            result = wrapper.get_input_output(table_id, year)
            print(json.dumps(result, indent=2))
        elif command == 'underlying_gdp_industry':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py underlying_gdp_industry <table_id> [year] [frequency] [industry]'}))
                sys.exit(1)
            table_id = sys.argv[2]
            year = sys.argv[3] if len(sys.argv) > 3 else None
            frequency = sys.argv[4] if len(sys.argv) > 4 else 'A'
            industry = sys.argv[5] if len(sys.argv) > 5 else 'ALL'
            result = wrapper.get_underlying_gdp_by_industry(table_id, year, frequency, industry)
            print(json.dumps(result, indent=2))
        elif command == 'international_services':
            type_of_service = sys.argv[2] if len(sys.argv) > 2 else None
            trade_direction = sys.argv[3] if len(sys.argv) > 3 else None
            affiliation = sys.argv[4] if len(sys.argv) > 4 else None
            area_or_country = sys.argv[5] if len(sys.argv) > 5 else 'AllCountries'
            year = sys.argv[6] if len(sys.argv) > 6 else None
            result = wrapper.get_international_services_trade(type_of_service, trade_direction, affiliation, area_or_country, year)
            print(json.dumps(result, indent=2))
        elif command == 'regional':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python bea_data.py regional <table_name> [line_code] [geo_fips] [year]'}))
                sys.exit(1)
            table_name = sys.argv[2]
            line_code = sys.argv[3] if len(sys.argv) > 3 else 'ALL'
            geo_fips = sys.argv[4] if len(sys.argv) > 4 else 'STATE'
            year = sys.argv[5] if len(sys.argv) > 5 else None
            result = wrapper.get_regional_data(table_name, line_code, geo_fips, year)
            print(json.dumps(result, indent=2))
        elif command == 'economic_overview':
            year = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_economic_overview(year)
            print(json.dumps(result, indent=2))
        elif command == 'regional_snapshot':
            geo_fips = sys.argv[2] if len(sys.argv) > 2 else 'USA'
            year = sys.argv[3] if len(sys.argv) > 3 else None
            result = wrapper.get_regional_snapshot(geo_fips, year)
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({'error': f'Unknown command: {command}', 'available_commands': ['dataset_list', 'parameter_list <dataset_name>', 'parameter_values <dataset_name> <parameter_name>', 'parameter_values_filtered <dataset_name> <parameter_name> <target_parameter>', 'nipa <table_name> [frequency] [year]', 'ni_underlying <table_name> [frequency] [year]', 'fixed_assets <table_name> [year]', 'mne <direction> [classification] [year] [country] [industry] [state] [ownership_level] [nonbank_affiliates_only] [get_footnotes]', 'gdp_by_industry <table_id> [year] [frequency] [industry]', 'international_transactions [indicator] [area_or_country] [frequency] [year]', 'international_investment [type_of_investment] [component] [frequency] [year]', 'input_output <table_id> [year]', 'underlying_gdp_industry <table_id> [year] [frequency] [industry]', 'international_services [type_of_service] [trade_direction] [affiliation] [area_or_country] [year]', 'regional <table_name> [line_code] [geo_fips] [year]', 'economic_overview [year]', 'regional_snapshot [geo_fips] [year]']}))
            sys.exit(1)
    except KeyboardInterrupt:
        print(json.dumps({'error': 'Operation cancelled by user'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': f'Unexpected error: {str(e)}'}))
        sys.exit(1)

def get_stats_list_by_keyword(keyword: str, limit: int=50) -> Dict[str, Any]:
    """
    Search statistical tables by keyword

    Args:
        keyword: Search keyword
        limit: Number of results to return

    Returns:
        JSON response with matching statistics
    """
    return get_stats_list(search_word=keyword, limit=limit)

def get_stats_list_by_ministry(stats_code: str, limit: int=100) -> Dict[str, Any]:
    """
    Get statistical tables by government ministry code

    Args:
        stats_code: Five-digit ministry code
        limit: Number of results to return

    Returns:
        JSON response with ministry statistics
    """
    return get_stats_list(stats_code=stats_code, limit=limit)

def get_stats_list_by_year(year: str, limit: int=100) -> Dict[str, Any]:
    """
    Get statistical tables by survey year

    Args:
        year: Survey year (e.g., "2020")
        limit: Number of results to return

    Returns:
        JSON response with year-specific statistics
    """
    return get_stats_list(survey_years=year, limit=limit)

def get_table_classifications(stats_data_id: str) -> Dict[str, Any]:
    """
    Get classification structure for a statistical table

    Args:
        stats_data_id: Unique ID of the statistical table

    Returns:
        JSON response with table classifications
    """
    meta_result = get_meta_info(stats_data_id)
    if meta_result['error']:
        return meta_result
    classifications = meta_result['data'].get('classifications', [])
    return {'data': classifications, 'metadata': {'source': 'e-Stat (Japan)', 'stats_data_id': stats_data_id, 'count': len(classifications), 'description': f'Classifications for table {stats_data_id}'}, 'error': None}

def get_all_data_for_table(stats_data_id: str) -> Dict[str, Any]:
    """
    Get all data for a statistical table (no filters)

    Args:
        stats_data_id: Unique ID of the statistical table

    Returns:
        JSON response with all table data
    """
    return get_stats_data(stats_data_id)

def get_data_by_area(stats_data_id: str, area_code: str) -> Dict[str, Any]:
    """
    Get statistical data for a specific area

    Args:
        stats_data_id: Unique ID of the statistical table
        area_code: Area/region code

    Returns:
        JSON response with area-specific data
    """
    return get_stats_data(stats_data_id, cd_area=area_code)

def get_data_by_time(stats_data_id: str, time_code: str) -> Dict[str, Any]:
    """
    Get statistical data for a specific time period

    Args:
        stats_data_id: Unique ID of the statistical table
        time_code: Time period code

    Returns:
        JSON response with time-specific data
    """
    return get_stats_data(stats_data_id, cd_time=time_code)

def search_statistics(keyword: str, limit: int=20) -> Dict[str, Any]:
    """
    Comprehensive search across all statistics

    Args:
        keyword: Search keyword
        limit: Number of results to return

    Returns:
        JSON response with search results
    """
    return get_stats_list(search_word=keyword, limit=limit)

def get_population_data(limit: int=10) -> Dict[str, Any]:
    """
    Get population-related statistics

    Args:
        limit: Number of results to return

    Returns:
        JSON response with population statistics
    """
    return get_stats_list(search_word='population', limit=limit)

def get_gdp_data(limit: int=10) -> Dict[str, Any]:
    """
    Get GDP-related statistics

    Args:
        limit: Number of results to return

    Returns:
        JSON response with GDP statistics
    """
    return get_stats_list(search_word='GDP', limit=limit)

def get_labor_data(limit: int=10) -> Dict[str, Any]:
    """
    Get labor/employment statistics

    Args:
        limit: Number of results to return

    Returns:
        JSON response with labor statistics
    """
    return get_stats_list(search_word='labor', limit=limit)

def get_table_summary(stats_data_id: str) -> Dict[str, Any]:
    """
    Get summary information about a statistical table

    Args:
        stats_data_id: Unique ID of the statistical table

    Returns:
        JSON response with table summary
    """
    try:
        meta_result = get_meta_info(stats_data_id)
        if meta_result['error']:
            return meta_result
        data_result = get_stats_data(stats_data_id, start_position=1)
        summary = {'metadata': meta_result['data'], 'sample_data': {'data_points_count': data_result['data'].get('data_values_count', 0), 'sample_values': data_result['data'].get('data_values', [])[:5] if data_result['data'] else []}}
        return {'data': summary, 'metadata': {'source': 'e-Stat (Japan)', 'stats_data_id': stats_data_id, 'description': f'Summary for statistical table {stats_data_id}'}, 'error': None}
    except Exception as e:
        return {'data': {}, 'metadata': {}, 'error': f'Error generating table summary: {str(e)}'}

def main():
    """CLI interface for e-Stat API"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python estat_japan_api.py <command> <args>', 'available_commands': ['stats-list [keyword] [limit]', 'stats-by-ministry <stats_code> [limit]', 'stats-by-year <year> [limit]', 'meta-info <stats_data_id>', 'classifications <stats_data_id>', 'stats-data <stats_data_id> [area_code] [time_code]', 'all-data <stats_data_id>', 'search <keyword> [limit]', 'population [limit]', 'gdp [limit]', 'labor [limit]', 'table-summary <stats_data_id>'], 'examples': ['python estat_japan_api.py stats-list population 10', 'python estat_japan_api.py stats-by-ministry 00200 5', 'python estat_japan_api.py meta-info 0003410379', 'python estat_japan_api.py stats-data 0003410379 00000 2020', 'python estat_japan_api.py search GDP 15', 'python estat_japan_api.py population 5', 'python estat_japan_api.py table-summary 0003410379'], 'note': 'Set ESTAT_APP_ID environment variable with your application ID from https://www.e-stat.go.jp/api/en/api-info/user-guide'}))
        sys.exit(1)
    command = sys.argv[1]
    try:
        if command == 'stats-list':
            keyword = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            result = get_stats_list(search_word=keyword, limit=limit)
        elif command == 'stats-by-ministry':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: stats-by-ministry <stats_code> [limit]'}))
                sys.exit(1)
            stats_code = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            result = get_stats_list_by_ministry(stats_code, limit)
        elif command == 'stats-by-year':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: stats-by-year <year> [limit]'}))
                sys.exit(1)
            year = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            result = get_stats_list_by_year(year, limit)
        elif command == 'meta-info':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: meta-info <stats_data_id>'}))
                sys.exit(1)
            stats_data_id = sys.argv[2]
            result = get_meta_info(stats_data_id)
        elif command == 'classifications':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: classifications <stats_data_id>'}))
                sys.exit(1)
            stats_data_id = sys.argv[2]
            result = get_table_classifications(stats_data_id)
        elif command == 'stats-data':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: stats-data <stats_data_id> [area_code] [time_code]'}))
                sys.exit(1)
            stats_data_id = sys.argv[2]
            area_code = sys.argv[3] if len(sys.argv) > 3 else None
            time_code = sys.argv[4] if len(sys.argv) > 4 else None
            result = get_stats_data(stats_data_id, cd_area=area_code, cd_time=time_code)
        elif command == 'all-data':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: all-data <stats_data_id>'}))
                sys.exit(1)
            stats_data_id = sys.argv[2]
            result = get_all_data_for_table(stats_data_id)
        elif command == 'search':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: search <keyword> [limit]'}))
                sys.exit(1)
            keyword = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            result = search_statistics(keyword, limit)
        elif command == 'population':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            result = get_population_data(limit)
        elif command == 'gdp':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            result = get_gdp_data(limit)
        elif command == 'labor':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            result = get_labor_data(limit)
        elif command == 'table-summary':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: table-summary <stats_data_id>'}))
                sys.exit(1)
            stats_data_id = sys.argv[2]
            result = get_table_summary(stats_data_id)
        else:
            result = {'error': f'Unknown command: {command}', 'available_commands': ['stats-list', 'stats-by-ministry', 'stats-by-year', 'meta-info', 'classifications', 'stats-data', 'all-data', 'search', 'population', 'gdp', 'labor', 'table-summary']}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': f'Command execution failed: {str(e)}', 'command': command, 'timestamp': datetime.now().isoformat()}))

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

def main():
    """Main function for CLI interface"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python imf_data.py <command> [args...]', 'commands': ['economic_indicators [countries] [symbols] [frequency] [start_date] [end_date] [sector]', 'direction_of_trade [countries] [counterparts] [direction] [frequency] [start_date] [end_date]', 'available_indicators [query]', 'comprehensive_economic_data [country] [start_date] [end_date]']}))
        sys.exit(1)
    command = sys.argv[1]
    wrapper = IMFDataWrapper()
    try:
        if command == 'economic_indicators':
            countries = sys.argv[2] if len(sys.argv) > 2 else None
            symbols = sys.argv[3] if len(sys.argv) > 3 else None
            frequency = sys.argv[4] if len(sys.argv) > 4 else 'quarter'
            start_date = sys.argv[5] if len(sys.argv) > 5 else None
            end_date = sys.argv[6] if len(sys.argv) > 6 else None
            sector = sys.argv[7] if len(sys.argv) > 7 else 'monetary_authorities'
            result = wrapper.get_economic_indicators(countries, symbols, frequency, start_date, end_date, sector)
        elif command == 'direction_of_trade':
            countries = sys.argv[2] if len(sys.argv) > 2 else None
            counterparts = sys.argv[3] if len(sys.argv) > 3 else None
            direction = sys.argv[4] if len(sys.argv) > 4 else 'all'
            frequency = sys.argv[5] if len(sys.argv) > 5 else 'quarter'
            start_date = sys.argv[6] if len(sys.argv) > 6 else None
            end_date = sys.argv[7] if len(sys.argv) > 7 else None
            result = wrapper.get_direction_of_trade(countries, counterparts, direction, frequency, start_date, end_date)
        elif command == 'available_indicators':
            query = sys.argv[2] if len(sys.argv) > 2 else None
            result = wrapper.get_available_indicators(query)
        elif command == 'comprehensive_economic_data':
            country = sys.argv[2] if len(sys.argv) > 2 else None
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            result = wrapper.get_comprehensive_economic_data(country, start_date, end_date)
        else:
            result = {'error': IMFError(command, f'Unknown command: {command}').to_dict()}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': IMFError(command, str(e)).to_dict()}, indent=2))

def get_country_financial_data(country: str) -> Dict[str, Any]:
    """11. Get comprehensive financial data (credit ratings + bond yields) for a country."""
    try:
        credit_data = get_credit_ratings(country)
        bond_data = get_government_bond_yields(country)
        result = {'country': country, 'timestamp': datetime.now().isoformat(), 'credit_ratings': credit_data, 'bond_yields': bond_data}
        credit_success = credit_data and 'error' not in credit_data
        bond_success = bond_data and 'error' not in bond_data
        result['summary'] = {'credit_ratings_available': credit_success, 'bond_yields_available': bond_success, 'overall_success': credit_success or bond_success}
        return result
    except Exception as e:
        return {'error': f'Failed to get comprehensive data for {country}: {str(e)}'}

def main():
    """Main Command-Line Interface entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python trading_economics_data.py <command> [args]', 'commands': ['test - Test API connection', 'ratings [country] - Get credit ratings (optional country)', "ratings_by_agency <agency> - Get ratings by agency (S&P, Moody's, Fitch)", 'ratings_history <country> [start_date] [end_date] - Historical ratings', 'rating_changes - Get recent rating changes', 'bonds [country] - Get bond yields (optional country)', 'bond <symbol> - Get specific bond data (e.g., US10Y)', 'us_treasuries - Get US Treasury yields', 'european_bonds - Get European bond yields', 'bond_history <symbol> [start_date] [end_date] - Historical bond yields', 'yield_curve <country> - Get yield curve data', 'country_data <country> - Get comprehensive country data', 'global_summary - Get global market summary', 'search_bonds <query> - Search for bonds', 'countries - Get supported countries', 'calendar - Get rating calendar'], 'examples': ['python trading_economics_data.py test', 'python trading_economics_data.py ratings Sweden', 'python trading_economics_data.py bond US10Y', 'python trading_economics_data.py country_data United States', 'python trading_economics_data.py ratings_history Sweden 2023-01-01 2023-12-31']}, indent=2))
        sys.exit(1)
    command = sys.argv[1].lower()
    result = {}
    try:
        if command == 'test':
            result = test_connection()
        elif command == 'ratings':
            country = sys.argv[2] if len(sys.argv) > 2 else None
            result = get_credit_ratings(country)
        elif command == 'ratings_by_agency':
            agency = sys.argv[2]
            result = get_credit_ratings_by_agency(agency)
        elif command == 'ratings_history':
            country = sys.argv[2]
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            result = get_historical_credit_ratings(country, start_date, end_date)
        elif command == 'rating_changes':
            result = get_rating_changes()
        elif command == 'bonds':
            country = sys.argv[2] if len(sys.argv) > 2 else None
            result = get_government_bond_yields(country)
        elif command == 'bond':
            symbol = sys.argv[2]
            result = get_bond_symbol(symbol)
        elif command == 'us_treasuries':
            result = get_us_treasury_yields()
        elif command == 'european_bonds':
            result = get_european_bond_yields()
        elif command == 'bond_history':
            symbol = sys.argv[2]
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            result = get_historical_bond_yields(symbol, start_date, end_date)
        elif command == 'yield_curve':
            country = sys.argv[2]
            result = get_yield_curve(country)
        elif command == 'country_data':
            country = ' '.join(sys.argv[2:])
            result = get_country_financial_data(country)
        elif command == 'global_summary':
            result = get_global_summary()
        elif command == 'search_bonds':
            query = ' '.join(sys.argv[2:])
            result = search_bonds(query)
        elif command == 'countries':
            result = get_supported_countries()
        elif command == 'calendar':
            result = get_rating_calendar()
        else:
            result = {'error': f'Unknown command: {command}'}
    except IndexError:
        result = {'error': 'Missing required arguments for command.'}
    except Exception as e:
        result = {'error': f'An unexpected error occurred: {str(e)}'}
    print(json.dumps(result, indent=2))

def main():
    """Main CLI entry point for ADB KIDB Data Fetcher"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python adb_data.py <command> <args>', 'available_commands': ['get_dataflows', 'get_codelists', 'get_dataflow_details <dataflow_code>', 'get_population <economy_code> [start_year] [end_year]', 'get_gdp <economy_code> [indicator] [start_year] [end_year]', 'get_multiple_indicators <economy_code> <indicator1,indicator2,...> [start_year] [end_year]', 'get_multiple_economies <indicator> <economy1,economy2,...> [start_year] [end_year]', 'get_financial <economy_code> [start_year] [end_year]', 'get_trade <economy_code> [start_year] [end_year]', 'search <keyword>'], 'examples': ['python adb_data.py get_dataflows', 'python adb_data.py get_population PHI 2010 2020', 'python adb_data.py get_gdp SGP NGDP_XDC 2015 2020', 'python adb_data.py get_multiple_indicators PHI NGDP_XDC,NGDPVA_XDC 2010 2020', 'python adb_data.py get_multiple_economies NGDP_XDC PHI,SGP,JPN 2015 2020', 'python adb_data.py search population']}))
        sys.exit(1)
    command = sys.argv[1]
    try:
        if command == 'get_dataflows':
            result = get_all_dataflows()
        elif command == 'get_codelists':
            result = get_all_codelists()
        elif command == 'get_dataflow_details':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: python adb_data.py get_dataflow_details <dataflow_code>'}))
                sys.exit(1)
            dataflow_code = sys.argv[2]
            result = get_dataflow_details(dataflow_code)
        elif command == 'get_population':
            economy = sys.argv[2] if len(sys.argv) > 2 else 'all'
            start_period = sys.argv[3] if len(sys.argv) > 3 else None
            end_period = sys.argv[4] if len(sys.argv) > 4 else None
            result = get_population_data(economy, start_period, end_period)
        elif command == 'get_gdp':
            economy = sys.argv[2] if len(sys.argv) > 2 else None
            indicator = sys.argv[3] if len(sys.argv) > 3 else 'NGDP_XDC'
            start_period = sys.argv[4] if len(sys.argv) > 4 else None
            end_period = sys.argv[5] if len(sys.argv) > 5 else None
            if not economy:
                print(json.dumps({'error': 'Economy code is required for GDP data'}))
                sys.exit(1)
            result = get_gdp_data(economy, indicator, start_period, end_period)
        elif command == 'get_multiple_indicators':
            economy = sys.argv[2] if len(sys.argv) > 2 else None
            indicators_str = sys.argv[3] if len(sys.argv) > 3 else None
            start_period = sys.argv[4] if len(sys.argv) > 4 else None
            end_period = sys.argv[5] if len(sys.argv) > 5 else None
            if not economy or not indicators_str:
                print(json.dumps({'error': 'Economy code and indicators are required'}))
                sys.exit(1)
            indicators = [ind.strip() for ind in indicators_str.split(',')]
            result = get_multiple_indicators(economy, indicators, start_period, end_period)
        elif command == 'get_multiple_economies':
            indicator = sys.argv[2] if len(sys.argv) > 2 else None
            economies_str = sys.argv[3] if len(sys.argv) > 3 else None
            start_period = sys.argv[4] if len(sys.argv) > 4 else None
            end_period = sys.argv[5] if len(sys.argv) > 5 else None
            if not indicator or not economies_str:
                print(json.dumps({'error': 'Indicator and economies are required'}))
                sys.exit(1)
            economies = [econ.strip() for econ in economies_str.split(',')]
            result = get_multiple_economies_data(indicator, economies, start_period, end_period)
        elif command == 'get_financial':
            economy = sys.argv[2] if len(sys.argv) > 2 else None
            start_period = sys.argv[3] if len(sys.argv) > 3 else None
            end_period = sys.argv[4] if len(sys.argv) > 4 else None
            if not economy:
                print(json.dumps({'error': 'Economy code is required for financial data'}))
                sys.exit(1)
            result = get_financial_indicators(economy, start_period, end_period)
        elif command == 'get_trade':
            economy = sys.argv[2] if len(sys.argv) > 2 else None
            start_period = sys.argv[3] if len(sys.argv) > 3 else None
            end_period = sys.argv[4] if len(sys.argv) > 4 else None
            if not economy:
                print(json.dumps({'error': 'Economy code is required for trade data'}))
                sys.exit(1)
            result = get_trade_data(economy, start_period, end_period)
        elif command == 'search':
            keyword = sys.argv[2] if len(sys.argv) > 2 else None
            if not keyword:
                print(json.dumps({'error': 'Search keyword is required'}))
                sys.exit(1)
            result = search_datasets(keyword)
        else:
            print(json.dumps({'error': f'Unknown command: {command}', 'available_commands': ['get_dataflows', 'get_codelists', 'get_dataflow_details', 'get_population', 'get_gdp', 'get_multiple_indicators', 'get_multiple_economies', 'get_financial', 'get_trade', 'search']}))
            sys.exit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': f'Command execution failed: {str(e)}', 'command': command, 'timestamp': datetime.now().isoformat()}))
        sys.exit(1)

class OpenRouterClient:
    """Enhanced OpenRouter API client with error handling and retries"""

    def __init__(self, api_key: Optional[str]=None, config: Optional[OpenRouterConfig]=None):
        self.config = config or OpenRouterConfig()
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError('API key required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.')

    def chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Send a chat completion request with retry logic"""
        url = f'{self.config.base_url}/chat/completions'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        payload = {'model': kwargs.get('model', self.config.model), 'messages': messages}
        payload.update(kwargs)
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(url=url, headers=headers, json=payload, timeout=self.config.timeout)
                if response.status_code == 429:
                    wait_time = int(response.headers.get('retry-after', attempt + 1))
                    print(f'Rate limited. Waiting {wait_time} seconds...')
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                result = response.json()
                if 'choices' not in result:
                    raise ValueError(f'Invalid response format: {result}')
                return result
            except requests.exceptions.RequestException as e:
                if attempt < self.config.max_retries - 1:
                    print(f'Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}')
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    print(f'Request failed after {self.config.max_retries} attempts: {e}')
                    raise
            except json.JSONDecodeError as e:
                print(f'Failed to decode response: {e}')
                print(f'Raw response: {response.text}')
                raise
        raise RuntimeError('Maximum retries exceeded')

    def print_chat_response(self, response: Dict[str, Any]):
        """Pretty print the chat response"""
        print(f'Response received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
        print('-' * 50)
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            message = choice.get('message', {})
            print(f'Model: {response.get('model', 'Unknown')}')
            print(f'Role: {message.get('role', 'Unknown')}')
            content = message.get('content', 'No content returned')
            print(f'Content: {content}')
            if 'usage' in response:
                usage = response['usage']
                print(f'Token usage - Prompt: {usage.get('prompt_tokens', 0)}, Completion: {usage.get('completion_tokens', 0)}, Total: {usage.get('total_tokens', 0)}')
        else:
            print('No valid response received')
            print(f'Full response: {json.dumps(response, indent=2)}')
        print('-' * 50)

def print_chat_response(self, response: Dict[str, Any]):
    """Pretty print the chat response"""
    print(f'Response received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
    print('-' * 50)
    if 'choices' in response and len(response['choices']) > 0:
        choice = response['choices'][0]
        message = choice.get('message', {})
        print(f'Model: {response.get('model', 'Unknown')}')
        print(f'Role: {message.get('role', 'Unknown')}')
        content = message.get('content', 'No content returned')
        print(f'Content: {content}')
        if 'usage' in response:
            usage = response['usage']
            print(f'Token usage - Prompt: {usage.get('prompt_tokens', 0)}, Completion: {usage.get('completion_tokens', 0)}, Total: {usage.get('total_tokens', 0)}')
    else:
        print('No valid response received')
        print(f'Full response: {json.dumps(response, indent=2)}')
    print('-' * 50)

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

class FinanceNotificationSystem:
    """Main notification system for finance terminal"""
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.config = NotificationConfig()
        self.rate_limiter = NotificationRateLimiter(self.config)
        self.metrics = NotificationMetrics()
        self.available = NOTIFYPY_AVAILABLE and self.config.enabled and (not self.config.silent_mode)
        if LOGGER_AVAILABLE:
            if self.available:
                info('Notification system initialized', module='notifications')
            else:
                warning('Notification system disabled or unavailable', module='notifications')

    def _create_notification(self, title: str, message: str, level: NotificationLevel) -> Optional[Notify]:
        """Create a notification object"""
        if not self.available:
            return None
        try:
            notification = Notify()
            notification.title = title
            notification.message = message
            notification.application_name = self.config.app_name
            if self.config.app_icon:
                notification.icon = self.config.app_icon
            return notification
        except Exception as e:
            if LOGGER_AVAILABLE:
                error(f'Failed to create notification: {e}', module='notifications')
            self.metrics.record_failed()
            return None

    def _send_notification(self, title: str, message: str, level: NotificationLevel, module: Optional[str]=None, **kwargs) -> bool:
        """Core notification sending method"""
        if level.value not in self.config.enabled_levels:
            return False
        if not self.rate_limiter.should_allow(title, message, level):
            self.metrics.record_rate_limited()
            if LOGGER_AVAILABLE and self.config.debug_notifications:
                debug(f'Rate limited notification: {title}', module='notifications')
            return False
        if module:
            tab_prefix = self.config.get_tab_prefix(module)
            title = f'{tab_prefix} {title}'
        if LOGGER_AVAILABLE:
            info(f'Sending notification: {title}', module='notifications', context={'level': level.value, 'source_module': module})
        notification = self._create_notification(title, message, level)
        if notification:
            try:
                notification.send()
                self.metrics.record_sent(level)
                return True
            except Exception as e:
                if LOGGER_AVAILABLE:
                    error(f'Failed to send notification: {e}', module='notifications')
                self.metrics.record_failed()
                return False
        return False

    def debug(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send debug notification"""
        if not self.config.debug_notifications:
            return False
        return self._send_notification(title, message, NotificationLevel.DEBUG, module, **kwargs)

    def info(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send info notification"""
        return self._send_notification(title, message, NotificationLevel.INFO, module, **kwargs)

    def success(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send success notification"""
        return self._send_notification(title, message, NotificationLevel.SUCCESS, module, **kwargs)

    def warning(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send warning notification"""
        return self._send_notification(title, message, NotificationLevel.WARNING, module, **kwargs)

    def error(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send error notification"""
        return self._send_notification(title, message, NotificationLevel.ERROR, module, **kwargs)

    def critical(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send critical notification"""
        return self._send_notification(title, message, NotificationLevel.CRITICAL, module, **kwargs)

    def trade_executed(self, symbol: str, action: str, quantity: int, price: float, module: Optional[str]='trading') -> bool:
        """Template for trade execution notifications"""
        title = 'Trade Executed'
        message = f'{action.upper()} {quantity} {symbol} @ ${price:.2f}'
        return self.success(title, message, module)

    def price_alert(self, symbol: str, current_price: float, target_price: float, condition: str, module: Optional[str]='alerts') -> bool:
        """Template for price alert notifications"""
        title = f'Price Alert: {symbol}'
        message = f'Price ${current_price:.2f} {condition} target ${target_price:.2f}'
        return self.warning(title, message, module)

    def connection_status(self, service: str, status: str, module: Optional[str]='api') -> bool:
        """Template for connection status notifications"""
        title = f'Connection {status.title()}'
        message = f'{service} connection is now {status.lower()}'
        if status.lower() in ['connected', 'restored']:
            return self.success(title, message, module)
        else:
            return self.error(title, message, module)

    def data_update(self, data_type: str, count: int, module: Optional[str]='market') -> bool:
        """Template for data update notifications"""
        title = 'Data Updated'
        message = f'{data_type}: {count} items updated'
        return self.info(title, message, module)

    def system_status(self, component: str, status: str, details: str='', module: Optional[str]='main') -> bool:
        """Template for system status notifications"""
        title = f'System {status.title()}'
        message = f'{component}: {details}' if details else component
        if status.lower() in ['started', 'ready', 'healthy']:
            return self.success(title, message, module)
        elif status.lower() in ['warning', 'degraded']:
            return self.warning(title, message, module)
        else:
            return self.error(title, message, module)

    def enable(self, enabled: bool=True):
        """Enable or disable notifications"""
        self.config.enabled = enabled
        self.available = NOTIFYPY_AVAILABLE and enabled and (not self.config.silent_mode)
        if LOGGER_AVAILABLE:
            status = 'enabled' if enabled else 'disabled'
            info(f'Notifications {status}', module='notifications')

    def set_silent_mode(self, silent: bool=True):
        """Enable or disable silent mode"""
        self.config.silent_mode = silent
        self.available = NOTIFYPY_AVAILABLE and self.config.enabled and (not silent)
        if LOGGER_AVAILABLE:
            mode = 'silent' if silent else 'normal'
            info(f'Notification mode: {mode}', module='notifications')

    def set_debug_notifications(self, enabled: bool=True):
        """Enable or disable debug notifications"""
        self.config.debug_notifications = enabled

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        stats = self.metrics.get_stats()
        stats.update({'config': {'enabled': self.config.enabled, 'silent_mode': self.config.silent_mode, 'available': self.available, 'rate_limiting': self.config.rate_limit_enabled, 'enabled_levels': list(self.config.enabled_levels)}})
        return stats

    def health_check(self) -> Dict[str, Any]:
        """Check notification system health"""
        try:
            if not NOTIFYPY_AVAILABLE:
                return {'status': 'unavailable', 'reason': 'notifypy not installed'}
            if not self.config.enabled:
                return {'status': 'disabled', 'reason': 'notifications disabled in config'}
            if self.config.silent_mode:
                return {'status': 'silent', 'reason': 'silent mode enabled'}
            test_title = 'Health Check'
            test_message = f'Notification system test at {datetime.now().strftime('%H:%M:%S')}'
            return {'status': 'healthy', 'available': self.available, 'stats': self.get_stats()}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def _create_notification(self, title: str, message: str, level: NotificationLevel) -> Optional[Notify]:
    """Create a notification object"""
    if not self.available:
        return None
    try:
        notification = Notify()
        notification.title = title
        notification.message = message
        notification.application_name = self.config.app_name
        if self.config.app_icon:
            notification.icon = self.config.app_icon
        return notification
    except Exception as e:
        if LOGGER_AVAILABLE:
            error(f'Failed to create notification: {e}', module='notifications')
        self.metrics.record_failed()
        return None

def _send_notification(self, title: str, message: str, level: NotificationLevel, module: Optional[str]=None, **kwargs) -> bool:
    """Core notification sending method"""
    if level.value not in self.config.enabled_levels:
        return False
    if not self.rate_limiter.should_allow(title, message, level):
        self.metrics.record_rate_limited()
        if LOGGER_AVAILABLE and self.config.debug_notifications:
            debug(f'Rate limited notification: {title}', module='notifications')
        return False
    if module:
        tab_prefix = self.config.get_tab_prefix(module)
        title = f'{tab_prefix} {title}'
    if LOGGER_AVAILABLE:
        info(f'Sending notification: {title}', module='notifications', context={'level': level.value, 'source_module': module})
    notification = self._create_notification(title, message, level)
    if notification:
        try:
            notification.send()
            self.metrics.record_sent(level)
            return True
        except Exception as e:
            if LOGGER_AVAILABLE:
                error(f'Failed to send notification: {e}', module='notifications')
            self.metrics.record_failed()
            return False
    return False

def de_shaw_hedge_fund_agent(state: AgentState, agent_id: str='de_shaw_hedge_fund_agent'):
    """
    D.E. Shaw: Computational finance, quantitative hedge fund
    Structure: Research → Computational Finance → Trading Systems → Risk Control → David Shaw Decision
    Philosophy: Scientific approach, computational methods, systematic strategies
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    de_shaw_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Research team computational analysis')
        metrics = get_financial_metrics(ticker, end_date, period='quarterly', limit=20, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'research_and_development'], end_date, period='quarterly', limit=20, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Research team analysis')
        research_team = research_team_computational_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Computational finance models')
        computational_finance = computational_finance_models(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Trading systems analysis')
        trading_systems = trading_systems_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk control systems')
        risk_control = risk_control_systems(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'David Shaw systematic decision')
        david_shaw_decision = david_shaw_systematic_decision(research_team, computational_finance, trading_systems, risk_control)
        total_score = computational_finance['score'] * 0.35 + research_team['score'] * 0.25 + trading_systems['score'] * 0.2 + risk_control['score'] * 0.2
        model_confidence = computational_finance.get('model_confidence', 0)
        if total_score >= 8.0 and model_confidence > 0.8:
            signal = 'bullish'
        elif total_score <= 3.5 or model_confidence < 0.4:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'research_team': research_team, 'computational_finance': computational_finance, 'trading_systems': trading_systems, 'risk_control': risk_control, 'david_shaw_decision': david_shaw_decision}
        de_shaw_output = generate_de_shaw_output(ticker, analysis_data, state, agent_id)
        de_shaw_analysis[ticker] = {'signal': de_shaw_output.signal, 'confidence': de_shaw_output.confidence, 'reasoning': de_shaw_output.reasoning, 'computational_models': de_shaw_output.computational_models}
        progress.update_status(agent_id, ticker, 'Done', analysis=de_shaw_output.reasoning)
    message = HumanMessage(content=json.dumps(de_shaw_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(de_shaw_analysis, 'D.E. Shaw')
    state['data']['analyst_signals'][agent_id] = de_shaw_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_de_shaw_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> DEShawSignal:
    """Generate DE Shaw's computational finance investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are D.E. Shaw's AI system, implementing David Shaw's computational finance approach:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Research Team: Computational analysis and quantitative research\n        - Computational Finance: Monte Carlo, SDE models, ML ensemble, options pricing\n        - Trading Systems: Algorithmic execution, HFT, market microstructure\n        - Risk Control: Advanced VaR, stress testing, correlation analysis\n        - David Shaw Systematic Decision: Scientific computational synthesis\n\n        PHILOSOPHY:\n        1. Computational Finance: Advanced mathematical and computational methods\n        2. Scientific Approach: Rigorous quantitative analysis and modeling\n        3. Systematic Strategies: Algorithm-driven investment decisions\n        4. Risk Management: Sophisticated risk control and hedging\n        5. Technology Edge: Cutting-edge computational infrastructure\n        6. Market Efficiency: Exploit computational advantages and inefficiencies\n        7. Diversification: Multiple uncorrelated computational strategies\n\n        REASONING STYLE:\n        - Reference computational models and mathematical analysis\n        - Discuss Monte Carlo simulations and stochastic processes\n        - Apply machine learning and statistical methods\n        - Consider execution algorithms and market microstructure\n        - Express confidence in computational edge and model validation\n        - Analyze risk-adjusted returns and Sharpe ratios\n        - Focus on systematic, repeatable investment processes\n\n        Return investment signal with computational model outputs and confidence metrics."), ('human', 'Apply D.E. Shaw\'s computational analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "computational_models": {{\n            "monte_carlo_probability": float,\n            "ml_ensemble_prediction": float,\n            "sde_model_score": float,\n            "risk_neutral_upside": float,\n            "model_confidence": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_de_shaw_signal():
        return DEShawSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', computational_models={'monte_carlo_probability': 0.5, 'ml_ensemble_prediction': 0.5, 'sde_model_score': 0.5, 'risk_neutral_upside': 0.0, 'model_confidence': 0.5})
    return call_llm(prompt=prompt, pydantic_model=DEShawSignal, agent_name=agent_id, state=state, default_factory=create_default_de_shaw_signal)

def david_einhorn_agent(state: AgentState, agent_id: str='david_einhorn_agent'):
    """
    David Einhorn: Short selling + value, forensic accounting
    Focus: Accounting irregularities, overvalued shorts, undervalued longs
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    einhorn_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Conducting forensic accounting analysis')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=5, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'operating_income', 'free_cash_flow', 'total_assets', 'current_assets', 'accounts_receivable', 'inventory', 'total_debt', 'shareholders_equity', 'depreciation'], end_date, period='annual', limit=5, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        accounting_quality = analyze_accounting_quality(financial_line_items)
        earnings_quality = analyze_earnings_vs_cash_flow(financial_line_items)
        valuation_vs_reality = analyze_valuation_disconnect(metrics, financial_line_items, market_cap)
        red_flags = identify_red_flags(financial_line_items)
        fundamental_value = calculate_fundamental_value(financial_line_items, market_cap)
        total_score = accounting_quality['score'] * 0.25 + earnings_quality['score'] * 0.25 + fundamental_value['score'] * 0.2 + valuation_vs_reality['score'] * 0.2 + red_flags['score'] * 0.1
        if total_score >= 7.5:
            signal = 'bullish'
        elif total_score <= 3.5:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'accounting_quality': accounting_quality, 'earnings_quality': earnings_quality, 'valuation_vs_reality': valuation_vs_reality, 'red_flags': red_flags, 'fundamental_value': fundamental_value}
        einhorn_output = generate_einhorn_output(ticker, analysis_data, state, agent_id)
        einhorn_analysis[ticker] = {'signal': einhorn_output.signal, 'confidence': einhorn_output.confidence, 'reasoning': einhorn_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=einhorn_output.reasoning)
    message = HumanMessage(content=json.dumps(einhorn_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(einhorn_analysis, 'David Einhorn Agent')
    state['data']['analyst_signals'][agent_id] = einhorn_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_einhorn_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> EinhornSignal:
    """Generate Einhorn-style forensic analysis decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are David Einhorn's AI agent, applying forensic accounting and value analysis:\n\n        1. Forensic accounting: Scrutinize financial statements for quality and red flags\n        2. Earnings quality: Compare earnings to cash flows, analyze accruals\n        3. Value vs. price: Identify disconnects between valuation and reality\n        4. Short candidates: Find overvalued companies with accounting issues\n        5. Long candidates: Find undervalued companies with clean accounting\n        6. Red flag detection: Identify warning signs of financial manipulation\n        7. Contrarian positioning: Take positions opposite to market sentiment\n\n        Reasoning style:\n        - Emphasize accounting quality and financial statement analysis\n        - Focus on earnings vs. cash flow divergences\n        - Identify specific red flags and warning signs\n        - Discuss valuation relative to fundamental reality\n        - Express skepticism toward popular stocks\n        - Provide detailed forensic analysis\n        - Consider both long and short opportunities\n\n        Return bullish for undervalued companies with clean accounting, bearish for overvalued companies with red flags."), ('human', 'Apply forensic accounting analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_einhorn_signal():
        return EinhornSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=EinhornSignal, agent_name=agent_id, state=state, default_factory=create_default_einhorn_signal)

def joel_greenblatt_agent(state: AgentState, agent_id: str='joel_greenblatt_agent'):
    """
    Joel Greenblatt: Magic formula (high ROC + low P/E)
    Focus: Systematic value investing, high returns on capital, cheap valuations
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    greenblatt_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Applying Magic Formula criteria')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=5, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'total_assets', 'current_assets', 'current_liabilities', 'total_debt', 'shareholders_equity', 'operating_income', 'interest_expense', 'free_cash_flow'], end_date, period='annual', limit=5, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        earnings_yield = calculate_earnings_yield(financial_line_items, market_cap)
        return_on_capital = calculate_return_on_capital(financial_line_items)
        magic_formula_rank = calculate_magic_formula_rank(earnings_yield, return_on_capital)
        business_quality = analyze_business_quality_greenblatt(metrics, financial_line_items)
        special_situations = analyze_special_situations(financial_line_items, market_cap)
        total_score = magic_formula_rank['score'] * 0.4 + earnings_yield['score'] * 0.25 + return_on_capital['score'] * 0.25 + business_quality['score'] * 0.1
        if total_score >= 8.0:
            signal = 'bullish'
        elif total_score <= 4.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'earnings_yield': earnings_yield, 'return_on_capital': return_on_capital, 'magic_formula_rank': magic_formula_rank, 'business_quality': business_quality, 'special_situations': special_situations}
        greenblatt_output = generate_greenblatt_output(ticker, analysis_data, state, agent_id)
        greenblatt_analysis[ticker] = {'signal': greenblatt_output.signal, 'confidence': greenblatt_output.confidence, 'reasoning': greenblatt_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=greenblatt_output.reasoning)
    message = HumanMessage(content=json.dumps(greenblatt_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(greenblatt_analysis, 'Joel Greenblatt Agent')
    state['data']['analyst_signals'][agent_id] = greenblatt_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_greenblatt_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> GreenblattSignal:
    """Generate Greenblatt-style Magic Formula investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Joel Greenblatt's AI agent, implementing the Magic Formula strategy:\n\n        1. Magic Formula: High return on invested capital + High earnings yield\n        2. Systematic approach: Remove emotion, follow the formula mechanically\n        3. Value investing: Buy good businesses at cheap prices\n        4. Special situations: Spinoffs, mergers, bankruptcies for extra returns\n        5. Long-term perspective: Hold for 2-3 years minimum\n        6. Diversification: Own 20-30 positions to reduce risk\n        7. Patience: Trust the process even during underperformance\n\n        Reasoning style:\n        - Emphasize quantitative Magic Formula metrics\n        - Focus on ROIC and earnings yield primarily\n        - Discuss systematic, mechanical approach\n        - Reference statistical advantages of the formula\n        - Consider special situations as bonus opportunities\n        - Express confidence in proven methodology\n        - Acknowledge short-term volatility but long-term outperformance\n\n        Return bullish for high Magic Formula scores (top quartile companies)."), ('human', 'Apply Magic Formula analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_greenblatt_signal():
        return GreenblattSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=GreenblattSignal, agent_name=agent_id, state=state, default_factory=create_default_greenblatt_signal)

def jean_marie_eveillard_agent(state: AgentState, agent_id: str='jean_marie_eveillard_agent'):
    """
    Jean-Marie Eveillard: Global value, capital preservation
    Focus: Downside protection, global diversification, conservative value
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    eveillard_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Analyzing capital preservation potential')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=6, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_assets', 'current_assets', 'current_liabilities', 'total_debt', 'shareholders_equity', 'cash_and_equivalents'], end_date, period='annual', limit=6, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        capital_preservation = analyze_capital_preservation(financial_line_items, market_cap)
        balance_sheet_quality = analyze_conservative_balance_sheet(financial_line_items)
        valuation_safety = analyze_valuation_margin_of_safety(metrics, financial_line_items, market_cap)
        business_predictability = analyze_business_predictability(financial_line_items)
        downside_protection = calculate_downside_protection(financial_line_items, market_cap)
        total_score = capital_preservation['score'] * 0.3 + balance_sheet_quality['score'] * 0.25 + downside_protection['score'] * 0.2 + valuation_safety['score'] * 0.15 + business_predictability['score'] * 0.1
        if total_score >= 8.5:
            signal = 'bullish'
        elif total_score <= 5.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'capital_preservation': capital_preservation, 'balance_sheet_quality': balance_sheet_quality, 'valuation_safety': valuation_safety, 'business_predictability': business_predictability, 'downside_protection': downside_protection}
        eveillard_output = generate_eveillard_output(ticker, analysis_data, state, agent_id)
        eveillard_analysis[ticker] = {'signal': eveillard_output.signal, 'confidence': eveillard_output.confidence, 'reasoning': eveillard_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=eveillard_output.reasoning)
    message = HumanMessage(content=json.dumps(eveillard_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(eveillard_analysis, 'Jean-Marie Eveillard Agent')
    state['data']['analyst_signals'][agent_id] = eveillard_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_eveillard_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> EveillardSignal:
    """Generate Eveillard-style capital preservation decision"""
    template = ChatPromptTemplate.from_messages([('system', 'You are Jean-Marie Eveillard\'s AI agent, applying global value investing with capital preservation focus:\n\n        1. Capital preservation: "Return of capital is more important than return on capital"\n        2. Conservative balance sheets: Low debt, strong liquidity, asset backing\n        3. Margin of safety: Buy with significant downside protection\n        4. Predictable businesses: Avoid complexity and volatility\n        5. Global perspective: Consider opportunities worldwide\n        6. Patient approach: Wait for exceptional opportunities\n        7. Risk awareness: Focus on what can go wrong\n\n        Reasoning style:\n        - Emphasize downside protection and risk management\n        - Focus on balance sheet strength and financial conservatism\n        - Discuss predictability and business simplicity\n        - Consider liquidation values and asset backing\n        - Express conservative skepticism\n        - Require substantial margin of safety\n        - Acknowledge when standards are not met\n\n        Return bullish only for exceptionally safe investments with strong downside protection and reasonable upside.'), ('human', 'Apply capital preservation analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_eveillard_signal():
        return EveillardSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=EveillardSignal, agent_name=agent_id, state=state, default_factory=create_default_eveillard_signal)

def marty_whitman_agent(state: AgentState, agent_id: str='marty_whitman_agent'):
    """
    Marty Whitman: Safe & cheap, asset-based investing
    Focus: Balance sheet analysis, asset values, financial safety
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    whitman_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Analyzing safe & cheap criteria')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=5, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'total_assets', 'current_assets', 'current_liabilities', 'total_debt', 'shareholders_equity', 'cash_and_equivalents', 'accounts_receivable', 'inventory', 'property_plant_equipment', 'goodwill'], end_date, period='annual', limit=5, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        asset_value_analysis = analyze_asset_values(financial_line_items, market_cap)
        financial_safety = analyze_financial_safety(financial_line_items)
        balance_sheet_strength = analyze_balance_sheet_quality(financial_line_items)
        safe_and_cheap = evaluate_safe_and_cheap_criteria(metrics, financial_line_items, market_cap)
        credit_worthiness = analyze_credit_worthiness(financial_line_items)
        total_score = asset_value_analysis['score'] * 0.3 + financial_safety['score'] * 0.25 + safe_and_cheap['score'] * 0.2 + balance_sheet_strength['score'] * 0.15 + credit_worthiness['score'] * 0.1
        if total_score >= 8.0:
            signal = 'bullish'
        elif total_score <= 4.5:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'asset_value_analysis': asset_value_analysis, 'financial_safety': financial_safety, 'balance_sheet_strength': balance_sheet_strength, 'safe_and_cheap': safe_and_cheap, 'credit_worthiness': credit_worthiness}
        whitman_output = generate_whitman_output(ticker, analysis_data, state, agent_id)
        whitman_analysis[ticker] = {'signal': whitman_output.signal, 'confidence': whitman_output.confidence, 'reasoning': whitman_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=whitman_output.reasoning)
    message = HumanMessage(content=json.dumps(whitman_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(whitman_analysis, 'Marty Whitman Agent')
    state['data']['analyst_signals'][agent_id] = whitman_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_whitman_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> WhitmanSignal:
    """Generate Whitman-style safe & cheap investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Marty Whitman's AI agent, applying safe & cheap asset-based investing:\n\n        1. Safe & Cheap: Both criteria must be met - financial safety AND attractive valuation\n        2. Asset-based analysis: Focus on balance sheet values and asset backing\n        3. Financial safety: Low debt, strong liquidity, conservative capital structure\n        4. Credit analysis: Evaluate creditworthiness and financial flexibility\n        5. Tangible value: Prefer tangible assets over intangibles and goodwill\n        6. Balance sheet focus: Income statement is secondary to balance sheet strength\n        7. Risk management: Downside protection through asset values\n\n        Reasoning style:\n        - Emphasize balance sheet analysis and asset values\n        - Focus on financial safety and conservative capital structure\n        - Discuss tangible asset backing and liquidation values\n        - Consider credit worthiness and debt capacity\n        - Apply rigorous safe & cheap criteria\n        - Express preference for asset-rich, debt-light companies\n        - Acknowledge when safety or cheapness criteria are not met\n\n        Return bullish only for companies that are both financially safe AND attractively cheap."), ('human', 'Apply safe & cheap asset-based analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_whitman_signal():
        return WhitmanSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=WhitmanSignal, agent_name=agent_id, state=state, default_factory=create_default_whitman_signal)

def charlie_munger_agent(state: AgentState, agent_id: str='charlie_munger_agent'):
    """
    Charlie Munger: Mental models, quality businesses, patience
    Focus: Multidisciplinary thinking, concentrated bets, long-term compounding
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    munger_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Applying multidisciplinary mental models')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=10, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'shareholders_equity', 'total_debt', 'retained_earnings', 'operating_margin', 'research_and_development', 'outstanding_shares', 'total_assets'], end_date, period='annual', limit=10, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        business_quality = analyze_mental_model_quality(metrics, financial_line_items)
        moat_durability = analyze_competitive_moat_durability(metrics, financial_line_items)
        management_rationality = analyze_management_rationality(financial_line_items)
        compound_growth = analyze_compounding_potential(financial_line_items)
        incentive_alignment = analyze_incentive_structures(financial_line_items)
        total_score = business_quality['score'] * 0.3 + moat_durability['score'] * 0.25 + management_rationality['score'] * 0.2 + compound_growth['score'] * 0.15 + incentive_alignment['score'] * 0.1
        if total_score >= 8.5:
            signal = 'bullish'
        elif total_score <= 3.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'business_quality': business_quality, 'moat_durability': moat_durability, 'management_rationality': management_rationality, 'compound_growth': compound_growth, 'incentive_alignment': incentive_alignment}
        munger_output = generate_munger_output(ticker, analysis_data, state, agent_id)
        munger_analysis[ticker] = {'signal': munger_output.signal, 'confidence': munger_output.confidence, 'reasoning': munger_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=munger_output.reasoning)
    message = HumanMessage(content=json.dumps(munger_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(munger_analysis, 'Charlie Munger Agent')
    state['data']['analyst_signals'][agent_id] = munger_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_munger_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> MungerSignal:
    """Generate Munger-style investment decision using mental models"""
    template = ChatPromptTemplate.from_messages([('system', 'You are Charlie Munger\'s AI agent, applying multidisciplinary mental models to investing:\n\n        1. Mental Models: Psychology, economics, math, physics applied to business analysis\n        2. Quality over quantity: "It\'s better to buy a wonderful company at a fair price"\n        3. Long-term compounding: "The first rule of compounding is to never interrupt it unnecessarily"\n        4. Rational management: Assess capital allocation and incentive alignment\n        5. Durable moats: Sustainable competitive advantages over decades\n        6. Concentrated bets: "Diversification is protection against ignorance"\n        7. Patience and discipline: Wait for exceptional opportunities\n\n        Reasoning style:\n        - Use multidisciplinary frameworks and analogies\n        - Emphasize long-term thinking and compounding\n        - Focus on business quality and management rationality\n        - Apply inverse thinking: "What could go wrong?"\n        - Reference mental models and psychological biases\n        - Express strong convictions when warranted\n        - Admit when outside circle of competence\n\n        Return bullish only for exceptional businesses with durable moats and rational management.'), ('human', 'Apply multidisciplinary mental models to analyze {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_munger_signal():
        return MungerSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=MungerSignal, agent_name=agent_id, state=state, default_factory=create_default_munger_signal)

def warren_buffett_agent(state: AgentState, agent_id: str='warren_buffett_agent'):
    """
    Warren Buffett: Buy wonderful companies at fair prices, hold forever
    Focus: Economic moats, predictable earnings, strong management, reasonable price
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    buffett_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Analyzing wonderful business qualities')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=10, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'retained_earnings', 'operating_margin', 'research_and_development', 'outstanding_shares'], end_date, period='annual', limit=10, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        moat_analysis = analyze_economic_moat(metrics, financial_line_items)
        earnings_predictability = analyze_earnings_predictability(financial_line_items)
        financial_strength = analyze_financial_fortress(metrics, financial_line_items)
        management_quality = analyze_capital_allocation(financial_line_items)
        valuation_analysis = buffett_valuation(financial_line_items, market_cap)
        total_score = moat_analysis['score'] * 0.3 + earnings_predictability['score'] * 0.25 + financial_strength['score'] * 0.2 + management_quality['score'] * 0.15 + valuation_analysis['score'] * 0.1
        if total_score >= 8.0:
            signal = 'bullish'
        elif total_score <= 4.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'moat_analysis': moat_analysis, 'earnings_predictability': earnings_predictability, 'financial_strength': financial_strength, 'management_quality': management_quality, 'valuation_analysis': valuation_analysis}
        buffett_output = generate_buffett_output(ticker, analysis_data, state, agent_id)
        buffett_analysis[ticker] = {'signal': buffett_output.signal, 'confidence': buffett_output.confidence, 'reasoning': buffett_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=buffett_output.reasoning)
    message = HumanMessage(content=json.dumps(buffett_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(buffett_analysis, 'Warren Buffett Agent')
    state['data']['analyst_signals'][agent_id] = buffett_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_buffett_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> BuffettSignal:
    """Generate Buffett-style investment decision"""
    template = ChatPromptTemplate.from_messages([('system', 'You are Warren Buffett\'s AI agent. Follow his investment philosophy:\n\n        1. "Buy wonderful companies at fair prices" - Seek businesses with durable competitive advantages\n        2. Economic moats: High ROE, pricing power, brand strength, network effects\n        3. Predictable earnings: Consistent profitability over many years\n        4. Financial fortress: Low debt, strong balance sheet, reliable cash flow\n        5. Quality management: Efficient capital allocation, shareholder-friendly\n        6. Long-term perspective: "Our favorite holding period is forever"\n        7. Circle of competence: Understand the business model completely\n\n        Reasoning style:\n        - Focus on business fundamentals, not market movements\n        - Emphasize competitive advantages and moats\n        - Discuss management quality and capital allocation\n        - Value predictability over growth\n        - Use homespun analogies and simple explanations\n        - Express high conviction for quality businesses\n\n        Return signal: bullish (wonderful business at fair price), neutral (good business, wrong price), bearish (poor business fundamentals)'), ('human', 'Analyze {ticker} using Buffett\'s criteria:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_buffett_signal():
        return BuffettSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=BuffettSignal, agent_name=agent_id, state=state, default_factory=create_default_buffett_signal)

def seth_klarman_agent(state: AgentState, agent_id: str='seth_klarman_agent'):
    """
    Seth Klarman: Absolute return, risk-first approach, contrarian
    Focus: Capital preservation, asymmetric risk/reward, distressed opportunities
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    klarman_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Analyzing downside protection')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=5, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'total_assets', 'current_assets', 'current_liabilities', 'total_debt', 'cash_and_equivalents', 'shareholders_equity', 'free_cash_flow', 'operating_income'], end_date, period='annual', limit=5, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        downside_protection = analyze_downside_protection(financial_line_items, market_cap)
        asymmetric_opportunity = analyze_asymmetric_risk_reward(metrics, financial_line_items, market_cap)
        contrarian_indicators = analyze_contrarian_opportunity(metrics, financial_line_items)
        balance_sheet_strength = analyze_balance_sheet_fortress(financial_line_items)
        margin_of_safety = calculate_klarman_margin_of_safety(financial_line_items, market_cap)
        total_score = downside_protection['score'] * 0.3 + balance_sheet_strength['score'] * 0.25 + margin_of_safety['score'] * 0.2 + asymmetric_opportunity['score'] * 0.15 + contrarian_indicators['score'] * 0.1
        if total_score >= 8.0:
            signal = 'bullish'
        elif total_score <= 4.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'downside_protection': downside_protection, 'asymmetric_opportunity': asymmetric_opportunity, 'contrarian_indicators': contrarian_indicators, 'balance_sheet_strength': balance_sheet_strength, 'margin_of_safety': margin_of_safety}
        klarman_output = generate_klarman_output(ticker, analysis_data, state, agent_id)
        klarman_analysis[ticker] = {'signal': klarman_output.signal, 'confidence': klarman_output.confidence, 'reasoning': klarman_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=klarman_output.reasoning)
    message = HumanMessage(content=json.dumps(klarman_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(klarman_analysis, 'Seth Klarman Agent')
    state['data']['analyst_signals'][agent_id] = klarman_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_klarman_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> KlarmanSignal:
    """Generate Klarman-style risk-first investment decision"""
    template = ChatPromptTemplate.from_messages([('system', 'You are Seth Klarman\'s AI agent, following absolute return value investing principles:\n\n        1. Risk first: "Return OF capital is more important than return ON capital"\n        2. Margin of safety: Buy with significant downside protection\n        3. Contrarian approach: Buy when others are selling\n        4. Asymmetric risk/reward: Limited downside, substantial upside\n        5. Balance sheet fortress: Strong financial position required\n        6. Patient opportunism: Wait for exceptional opportunities\n        7. Absolute return focus: Preserve capital above all else\n\n        Reasoning style:\n        - Emphasize downside protection and risk analysis first\n        - Focus on balance sheet strength and asset coverage\n        - Discuss margin of safety quantitatively\n        - Consider contrarian and distressed opportunities\n        - Express skepticism and conservatism\n        - Require exceptional risk/reward ratios\n        - Acknowledge when opportunities don\'t meet standards\n\n        Return bullish only for exceptional risk/reward opportunities with substantial downside protection.'), ('human', 'Apply risk-first value analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_klarman_signal():
        return KlarmanSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=KlarmanSignal, agent_name=agent_id, state=state, default_factory=create_default_klarman_signal)

def bill_miller_agent(state: AgentState, agent_id: str='bill_miller_agent'):
    """
    Bill Miller: Concentrated value, contrarian timing
    Focus: Technology value plays, contrarian bets, concentrated positions
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    miller_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Analyzing contrarian value opportunity')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=7, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_assets', 'shareholders_equity', 'total_debt', 'research_and_development', 'operating_income', 'outstanding_shares'], end_date, period='annual', limit=7, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        contrarian_opportunity = analyze_contrarian_setup(metrics, financial_line_items, market_cap)
        technology_value = analyze_technology_value_potential(financial_line_items, market_cap)
        long_term_drivers = analyze_long_term_growth_drivers(financial_line_items)
        market_misperception = identify_market_misperceptions(metrics, financial_line_items)
        concentration_worthiness = evaluate_concentration_candidate(metrics, financial_line_items, market_cap)
        total_score = contrarian_opportunity['score'] * 0.3 + concentration_worthiness['score'] * 0.25 + technology_value['score'] * 0.2 + long_term_drivers['score'] * 0.15 + market_misperception['score'] * 0.1
        if total_score >= 8.0:
            signal = 'bullish'
        elif total_score <= 4.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'contrarian_opportunity': contrarian_opportunity, 'technology_value': technology_value, 'long_term_drivers': long_term_drivers, 'market_misperception': market_misperception, 'concentration_worthiness': concentration_worthiness}
        miller_output = generate_miller_output(ticker, analysis_data, state, agent_id)
        miller_analysis[ticker] = {'signal': miller_output.signal, 'confidence': miller_output.confidence, 'reasoning': miller_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=miller_output.reasoning)
    message = HumanMessage(content=json.dumps(miller_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(miller_analysis, 'Bill Miller Agent')
    state['data']['analyst_signals'][agent_id] = miller_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_miller_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> MillerSignal:
    """Generate Miller-style contrarian value decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Bill Miller's AI agent, applying contrarian value investing with technology focus:\n\n        1. Contrarian timing: Buy when others are selling, especially in technology\n        2. Concentrated bets: Make large positions in high-conviction ideas\n        3. Technology value: Find undervalued technology and growth companies\n        4. Long-term perspective: Focus on 3-5 year value creation\n        5. Market misperceptions: Identify when market misprices quality companies\n        6. Fundamental analysis: Deep research into business models and competitive advantages\n        7. Patient opportunism: Wait for exceptional risk/reward opportunities\n\n        Reasoning style:\n        - Emphasize contrarian opportunities and market misperceptions\n        - Focus on technology companies trading at value multiples\n        - Discuss long-term growth drivers and competitive positioning\n        - Consider concentration worthiness and conviction level\n        - Express willingness to be different from consensus\n        - Analyze both current challenges and future potential\n        - Apply rigorous fundamental analysis\n\n        Return bullish for high-conviction contrarian opportunities with significant upside potential."), ('human', 'Apply contrarian value analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_miller_signal():
        return MillerSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=MillerSignal, agent_name=agent_id, state=state, default_factory=create_default_miller_signal)

def benjamin_graham_agent(state: AgentState, agent_id: str='benjamin_graham_agent'):
    """
    Benjamin Graham: Margin of safety, net-net stocks, mathematical approach
    Focus: Quantitative screens, asset protection, statistical cheapness
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    graham_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Applying Graham's quantitative screens")
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=5, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'total_assets', 'current_assets', 'current_liabilities', 'total_debt', 'cash_and_equivalents', 'inventory', 'accounts_receivable', 'shareholders_equity'], end_date, period='annual', limit=5, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        net_net_analysis = analyze_net_net_value(financial_line_items, market_cap)
        defensive_criteria = analyze_defensive_investor_criteria(metrics, financial_line_items)
        margin_of_safety = calculate_margin_of_safety(metrics, financial_line_items, market_cap)
        earnings_stability = analyze_earnings_stability(financial_line_items)
        asset_protection = analyze_asset_protection(financial_line_items, market_cap)
        total_score = net_net_analysis['score'] * 0.3 + defensive_criteria['score'] * 0.25 + margin_of_safety['score'] * 0.2 + earnings_stability['score'] * 0.15 + asset_protection['score'] * 0.1
        if total_score >= 7.0:
            signal = 'bullish'
        elif total_score <= 3.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'net_net_analysis': net_net_analysis, 'defensive_criteria': defensive_criteria, 'margin_of_safety': margin_of_safety, 'earnings_stability': earnings_stability, 'asset_protection': asset_protection}
        graham_output = generate_graham_output(ticker, analysis_data, state, agent_id)
        graham_analysis[ticker] = {'signal': graham_output.signal, 'confidence': graham_output.confidence, 'reasoning': graham_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=graham_output.reasoning)
    message = HumanMessage(content=json.dumps(graham_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(graham_analysis, 'Benjamin Graham Agent')
    state['data']['analyst_signals'][agent_id] = graham_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_graham_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> GrahamSignal:
    """Generate Graham-style systematic investment decision"""
    template = ChatPromptTemplate.from_messages([('system', 'You are Benjamin Graham\'s AI agent, the father of value investing. Follow his systematic approach:\n\n        1. Mathematical and quantitative analysis over speculation\n        2. Margin of safety: "Price is what you pay, value is what you get"\n        3. Net-net working capital for maximum safety\n        4. Defensive investor criteria: 10-point checklist\n        5. Asset protection: Focus on balance sheet strength\n        6. Earnings stability over growth\n        7. Systematic approach: Remove emotion from investing\n        8. Statistical cheapness: Buy groups of undervalued securities\n\n        Reasoning style:\n        - Emphasize quantitative metrics and ratios\n        - Focus on asset protection and balance sheet\n        - Stress margin of safety in every decision\n        - Use systematic, unemotional language\n        - Prefer statistical evidence over narratives\n        - Always consider downside protection first\n\n        Return bullish only for statistically cheap, safe companies with adequate margin of safety.'), ('human', 'Apply Graham\'s systematic analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_graham_signal():
        return GrahamSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=GrahamSignal, agent_name=agent_id, state=state, default_factory=create_default_graham_signal)

def howard_marks_agent(state: AgentState, agent_id: str='howard_marks_agent'):
    """
    Howard Marks: Second-level thinking, risk assessment, cycles
    Focus: Market psychology, risk-adjusted returns, contrarian positioning
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    marks_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Applying second-level thinking')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=7, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'total_assets', 'operating_margin', 'current_assets', 'current_liabilities'], end_date, period='annual', limit=7, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        risk_assessment = analyze_risk_factors(metrics, financial_line_items, market_cap)
        cycle_positioning = analyze_cycle_position(metrics, financial_line_items)
        second_level_thinking = apply_second_level_thinking(metrics, financial_line_items, market_cap)
        market_psychology = analyze_market_psychology_indicators(metrics, market_cap)
        asymmetric_returns = evaluate_asymmetric_opportunities(financial_line_items, market_cap)
        total_score = risk_assessment['score'] * 0.3 + second_level_thinking['score'] * 0.25 + asymmetric_returns['score'] * 0.2 + cycle_positioning['score'] * 0.15 + market_psychology['score'] * 0.1
        if total_score >= 7.5:
            signal = 'bullish'
        elif total_score <= 4.5:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'risk_assessment': risk_assessment, 'cycle_positioning': cycle_positioning, 'second_level_thinking': second_level_thinking, 'market_psychology': market_psychology, 'asymmetric_returns': asymmetric_returns}
        marks_output = generate_marks_output(ticker, analysis_data, state, agent_id)
        marks_analysis[ticker] = {'signal': marks_output.signal, 'confidence': marks_output.confidence, 'reasoning': marks_output.reasoning}
        progress.update_status(agent_id, ticker, 'Done', analysis=marks_output.reasoning)
    message = HumanMessage(content=json.dumps(marks_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(marks_analysis, 'Howard Marks Agent')
    state['data']['analyst_signals'][agent_id] = marks_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_marks_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> MarksSignal:
    """Generate Marks-style risk-aware investment decision"""
    template = ChatPromptTemplate.from_messages([('system', 'You are Howard Marks\' AI agent, applying sophisticated risk-aware value investing:\n\n        1. Second-level thinking: "What is the market not seeing?"\n        2. Risk assessment: "Risk is the probability of loss, not volatility"\n        3. Cycle awareness: Understand where we are in the cycle\n        4. Market psychology: Recognize euphoria and pessimism\n        5. Asymmetric opportunities: Limited downside, significant upside\n        6. Contrarian positioning: Buy when others are selling\n        7. Risk-adjusted returns: Focus on risk-adjusted, not absolute returns\n\n        Reasoning style:\n        - Emphasize risk analysis and downside protection\n        - Consider market psychology and sentiment\n        - Apply second-level thinking to find hidden opportunities\n        - Discuss cyclical positioning and timing\n        - Focus on asymmetric risk/reward profiles\n        - Express nuanced, probabilistic thinking\n        - Acknowledge uncertainty and multiple scenarios\n\n        Return bullish for asymmetric opportunities with limited downside and strong risk-adjusted returns.'), ('human', 'Apply second-level thinking and risk analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string"\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_marks_signal():
        return MarksSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral')
    return call_llm(prompt=prompt, pydantic_model=MarksSignal, agent_name=agent_id, state=state, default_factory=create_default_marks_signal)

def aqr_capital_hedge_fund_agent(state: AgentState, agent_id: str='aqr_capital_hedge_fund_agent'):
    """
    AQR Capital Management: Factor investing, value-momentum combination
    Structure: Academic Research → Factor Analysis → Portfolio Construction → Risk Management → Cliff Asness Decision
    Philosophy: Systematic factor investing, academic rigor, long-term evidence
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    aqr_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Academic research team analyzing factors')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=10, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'research_and_development'], end_date, period='annual', limit=10, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Academic research team analysis')
        academic_research = academic_research_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Factor analysis team')
        factor_analysis = factor_analysis_team(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Portfolio construction team')
        portfolio_construction = portfolio_construction_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk management analysis')
        risk_management = risk_management_analysis(metrics, financial_line_items)
        progress.update_status(agent_id, ticker, 'Cliff Asness systematic decision')
        cliff_asness_decision = cliff_asness_systematic_decision(academic_research, factor_analysis, portfolio_construction, risk_management)
        total_score = factor_analysis['score'] * 0.4 + academic_research['score'] * 0.25 + portfolio_construction['score'] * 0.2 + risk_management['score'] * 0.15
        factor_strength = factor_analysis.get('combined_factor_score', 0)
        if total_score >= 7.5 and factor_strength > 0.6:
            signal = 'bullish'
        elif total_score <= 4.0 or factor_strength < 0.3:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'academic_research': academic_research, 'factor_analysis': factor_analysis, 'portfolio_construction': portfolio_construction, 'risk_management': risk_management, 'cliff_asness_decision': cliff_asness_decision}
        aqr_output = generate_aqr_output(ticker, analysis_data, state, agent_id)
        aqr_analysis[ticker] = {'signal': aqr_output.signal, 'confidence': aqr_output.confidence, 'reasoning': aqr_output.reasoning, 'factor_exposures': aqr_output.factor_exposures}
        progress.update_status(agent_id, ticker, 'Done', analysis=aqr_output.reasoning)
    message = HumanMessage(content=json.dumps(aqr_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(aqr_analysis, 'AQR Capital Management')
    state['data']['analyst_signals'][agent_id] = aqr_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_aqr_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> AQRSignal:
    """Generate AQR's factor-based investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are AQR Capital Management's AI system, implementing Cliff Asness' factor investing approach:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Academic Research Team: Literature review and statistical validation\n        - Factor Analysis Team: Value, momentum, quality, and low-vol factor analysis\n        - Portfolio Construction Team: Position sizing and implementation\n        - Risk Management Team: Factor risk decomposition and drawdown control\n        - Cliff Asness Systematic Decision: Factor combination and timing\n\n        PHILOSOPHY:\n        1. Factor Investing: Systematic exposure to value, momentum, quality factors\n        2. Academic Rigor: Evidence-based investing with statistical validation\n        3. Factor Timing: Intelligent timing of factor exposures\n        4. Value-Momentum Combination: AQR's specialty in combining opposing factors\n        5. Risk Management: Sophisticated factor risk controls\n        6. Long-term Evidence: Focus on factors with decades of evidence\n        7. Implementation Focus: Minimize transaction costs and market impact\n\n        REASONING STYLE:\n        - Reference academic literature and statistical evidence\n        - Discuss factor exposures and loadings quantitatively\n        - Apply rigorous statistical testing and out-of-sample validation\n        - Consider factor timing and regime analysis\n        - Express confidence in factor persistence and literature consistency\n        - Analyze implementation costs and capacity constraints\n        - Focus on risk-adjusted returns and Sharpe ratios\n\n        Return investment signal with detailed factor exposure analysis."), ('human', 'Apply AQR\'s factor analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "factor_exposures": {{\n            "value": float,\n            "momentum": float,\n            "quality": float,\n            "low_volatility": float,\n            "profitability": float,\n            "combined_factor_score": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_aqr_signal():
        return AQRSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', factor_exposures={'value': 0.5, 'momentum': 0.5, 'quality': 0.5, 'low_volatility': 0.5, 'profitability': 0.5, 'combined_factor_score': 0.5})
    return call_llm(prompt=prompt, pydantic_model=AQRSignal, agent_name=agent_id, state=state, default_factory=create_default_aqr_signal)

def pershing_square_hedge_fund_agent(state: AgentState, agent_id: str='pershing_square_hedge_fund_agent'):
    """
    Pershing Square: Concentrated activist investing, high-conviction bets
    Structure: Research → Activism Strategy → Public Relations → Risk Management → Bill Ackman Decision
    Philosophy: Concentrated positions, activist value creation, public campaigns
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    pershing_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Research team fundamental analysis')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=8, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'research_and_development'], end_date, period='annual', limit=8, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Research team analysis')
        research_team = pershing_research_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Activism strategy team')
        activism_strategy = activism_strategy_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Public relations strategy')
        public_relations = public_relations_strategy_analysis(financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk management analysis')
        risk_management = pershing_risk_management_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Bill Ackman investment decision')
        ackman_decision = bill_ackman_investment_decision(research_team, activism_strategy, public_relations, risk_management)
        total_score = research_team['score'] * 0.35 + activism_strategy['score'] * 0.3 + risk_management['score'] * 0.2 + public_relations['score'] * 0.15
        conviction_level = ackman_decision.get('conviction_level', 0)
        if total_score >= 8.5 and conviction_level > 0.8:
            signal = 'bullish'
        elif total_score <= 4.0 or conviction_level < 0.3:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'research_team': research_team, 'activism_strategy': activism_strategy, 'public_relations': public_relations, 'risk_management': risk_management, 'ackman_decision': ackman_decision}
        pershing_output = generate_pershing_output(ticker, analysis_data, state, agent_id)
        pershing_analysis[ticker] = {'signal': pershing_output.signal, 'confidence': pershing_output.confidence, 'reasoning': pershing_output.reasoning, 'investment_thesis': pershing_output.investment_thesis}
        progress.update_status(agent_id, ticker, 'Done', analysis=pershing_output.reasoning)
    message = HumanMessage(content=json.dumps(pershing_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(pershing_analysis, 'Pershing Square')
    state['data']['analyst_signals'][agent_id] = pershing_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def pershing_risk_management_analysis(metrics: list, financial_line_items: list, market_cap: float) -> dict:
    """Pershing Square's risk management for concentrated positions"""
    score = 0
    details = []
    risk_factors = []
    if not metrics or not financial_line_items or (not market_cap):
        return {'score': 0, 'details': 'No risk data'}
    concentration_risk = assess_concentration_risk(market_cap)
    if concentration_risk < 0.3:
        score += 2
        details.append('Low concentration risk')
    elif concentration_risk > 0.7:
        risk_factors.append('High concentration risk')
        details.append('High concentration risk identified')
    liquidity_risk = assess_large_position_liquidity_risk(market_cap)
    if liquidity_risk < 0.2:
        score += 2
        details.append('Low liquidity risk for large positions')
    elif liquidity_risk > 0.6:
        risk_factors.append('Liquidity constraints')
    campaign_risk = assess_activist_campaign_risks(financial_line_items)
    if campaign_risk < 0.4:
        score += 1.5
        details.append('Low activist campaign risk')
    elif campaign_risk > 0.7:
        risk_factors.append('High campaign execution risk')
    regulatory_risk = assess_regulatory_and_legal_risks(market_cap)
    if regulatory_risk < 0.3:
        score += 1.5
        details.append('Low regulatory risk')
    elif regulatory_risk > 0.6:
        risk_factors.append('Regulatory concerns')
    reputational_risk = assess_reputational_risk_exposure(financial_line_items)
    if reputational_risk < 0.4:
        score += 1
        details.append('Low reputational risk')
    elif reputational_risk > 0.7:
        risk_factors.append('Reputational risk exposure')
    downside_protection = calculate_downside_protection(financial_line_items, market_cap)
    if downside_protection > 0.6:
        score += 2
        details.append('Strong downside protection')
    if risk_factors:
        details.append(f'Risk factors: {'; '.join(risk_factors)}')
    return {'score': score, 'details': '; '.join(details), 'risk_factors': risk_factors}

def generate_pershing_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> PershingSquareSignal:
    """Generate Pershing Square's concentrated activist investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Pershing Square's AI system, implementing Bill Ackman's concentrated activist approach:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Research Team: Deep fundamental analysis and intrinsic value calculation\n        - Activism Strategy Team: Board changes, strategic restructuring, operational improvements\n        - Public Relations Strategy: Media campaigns, shareholder communication, narrative building\n        - Risk Management: Concentration risk, liquidity risk, campaign execution risk\n        - Bill Ackman Investment Decision: High-conviction concentrated positioning\n\n        PHILOSOPHY:\n        1. Concentrated Investing: Large positions (10-25%) in high-conviction ideas\n        2. Activist Value Creation: Board changes, strategic improvements, operational efficiency\n        3. Public Campaigns: Media engagement and public pressure for change\n        4. Long-Term Value Creation: Multi-year investment horizons\n        5. Quality Businesses: Strong competitive positions with improvement potential\n        6. Intrinsic Value Focus: Significant discount to fair value required\n        7. ESG Integration: Environmental, social, and governance improvements\n\n        REASONING STYLE:\n        - Express high conviction and concentrated position rationale\n        - Discuss specific activist catalysts and value creation opportunities\n        - Reference intrinsic value calculations and margin of safety\n        - Consider public campaign strategy and media narrative\n        - Analyze management quality and governance improvements\n        - Assess timeline and expected returns from activist engagement\n        - Focus on asymmetric risk/reward from concentrated positions\n\n        Return investment signal with detailed investment thesis and activist strategy."), ('human', 'Apply Pershing Square\'s concentrated activist analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "investment_thesis": {{\n            "intrinsic_value_upside": float,\n            "activist_catalysts": ["string"],\n            "expected_timeline": "string",\n            "position_size_recommendation": "string",\n            "public_campaign_strategy": "string"\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_pershing_signal():
        return PershingSquareSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', investment_thesis={'intrinsic_value_upside': 0.0, 'activist_catalysts': [], 'expected_timeline': '12-24 months', 'position_size_recommendation': 'Pass', 'public_campaign_strategy': 'None'})
    return call_llm(prompt=prompt, pydantic_model=PershingSquareSignal, agent_name=agent_id, state=state, default_factory=create_default_pershing_signal)

def get_market_cap(ticker: str, end_date: str, api_key: str=None) -> float | None:
    """Fetch market cap from the API."""
    if end_date == datetime.datetime.now().strftime('%Y-%m-%d'):
        headers = {}
        financial_api_key = api_key or os.environ.get('FINANCIAL_DATASETS_API_KEY')
        if financial_api_key:
            headers['X-API-KEY'] = financial_api_key
        url = f'https://api.financialdatasets.ai/company/facts/?ticker={ticker}'
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            print(f'Error fetching company facts: {ticker} - {response.status_code}')
            return None
        data = response.json()
        response_model = CompanyFactsResponse(**data)
        return response_model.company_facts.market_cap
    financial_metrics = get_financial_metrics(ticker, end_date, api_key=api_key)
    if not financial_metrics:
        return None
    market_cap = financial_metrics[0].market_cap
    if not market_cap:
        return None
    return market_cap

class DataCache:
    """Redis-based caching for data feeds"""

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.default_ttl = CONFIG.agent.cache_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int]=None) -> bool:
        """Set cached data"""
        try:
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            return False

    def generate_key(self, source: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        param_str = json.dumps(params, sort_keys=True)
        return f'{source}:{hashlib.md5(param_str.encode()).hexdigest()}'

def set(self, key: str, value: Any, ttl: Optional[int]=None) -> bool:
    """Set cached data"""
    try:
        ttl = ttl or self.default_ttl
        return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        return False

def bridgewater_associates_agent(state: AgentState, agent_id: str='bridgewater_associates_agent'):
    """
    Bridgewater Associates: All Weather portfolio, economic machine principles
    Structure: Economic Research → Portfolio Construction → Risk Management → Ray Dalio Final Decision
    Philosophy: Diversification across economic environments, systematic risk parity
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    bridgewater_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Economic research team analyzing macro environment')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=10, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'interest_expense'], end_date, period='annual', limit=10, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Economic research team analysis')
        economic_research = economic_research_team_analysis(metrics, financial_line_items)
        progress.update_status(agent_id, ticker, 'Portfolio construction team analysis')
        portfolio_construction = portfolio_construction_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk management team analysis')
        risk_management = risk_management_team_analysis(financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'All Weather framework analysis')
        all_weather_analysis = all_weather_framework_analysis(metrics, financial_line_items)
        progress.update_status(agent_id, ticker, "Ray Dalio's synthesis and final decision")
        ray_dalio_synthesis = ray_dalio_final_decision(economic_research, portfolio_construction, risk_management, all_weather_analysis)
        total_score = economic_research['score'] * 0.3 + all_weather_analysis['score'] * 0.25 + risk_management['score'] * 0.25 + portfolio_construction['score'] * 0.2
        if total_score >= 7.5:
            signal = 'bullish'
        elif total_score <= 4.0:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'economic_research': economic_research, 'portfolio_construction': portfolio_construction, 'risk_management': risk_management, 'all_weather_analysis': all_weather_analysis, 'ray_dalio_synthesis': ray_dalio_synthesis}
        bridgewater_output = generate_bridgewater_output(ticker, analysis_data, state, agent_id)
        bridgewater_analysis[ticker] = {'signal': bridgewater_output.signal, 'confidence': bridgewater_output.confidence, 'reasoning': bridgewater_output.reasoning, 'all_weather_allocation': bridgewater_output.all_weather_allocation}
        progress.update_status(agent_id, ticker, 'Done', analysis=bridgewater_output.reasoning)
    message = HumanMessage(content=json.dumps(bridgewater_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(bridgewater_analysis, 'Bridgewater Associates')
    state['data']['analyst_signals'][agent_id] = bridgewater_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_bridgewater_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> BridgewaterSignal:
    """Generate Bridgewater's systematic investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Bridgewater Associates' AI system, implementing Ray Dalio's All Weather and economic machine principles:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Economic Research Team: Macro environment and debt cycle analysis\n        - Portfolio Construction Team: Risk-adjusted returns and diversification\n        - Risk Management Team: Comprehensive risk assessment\n        - All Weather Framework: Performance across four economic environments\n        - Ray Dalio Synthesis: Final decision integration\n\n        PHILOSOPHY:\n        1. All Weather: Balanced performance across economic environments (growth/inflation up/down)\n        2. Economic Machine: Understanding debt cycles and economic principles\n        3. Risk Parity: Equal risk contribution, not equal dollar allocation\n        4. Systematic Approach: Remove emotion, follow systematic principles\n        5. Diversification: True diversification across uncorrelated return streams\n        6. Transparency: Radical transparency in decision-making process\n\n        REASONING STYLE:\n        - Reference team analyses and organizational structure\n        - Apply economic machine principles to company analysis\n        - Consider All Weather framework and environmental balance\n        - Discuss risk parity and diversification benefits\n        - Synthesize multiple team perspectives\n        - Express systematic, principle-based reasoning\n        - Consider position sizing based on risk contribution\n\n        Return the investment signal with All Weather allocation recommendations."), ('human', 'Apply Bridgewater\'s systematic analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "all_weather_allocation": {{\n            "rising_growth_weight": float,\n            "falling_growth_weight": float,\n            "rising_inflation_weight": float,\n            "falling_inflation_weight": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_bridgewater_signal():
        return BridgewaterSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', all_weather_allocation={'rising_growth_weight': 0.25, 'falling_growth_weight': 0.25, 'rising_inflation_weight': 0.25, 'falling_inflation_weight': 0.25})
    return call_llm(prompt=prompt, pydantic_model=BridgewaterSignal, agent_name=agent_id, state=state, default_factory=create_default_bridgewater_signal)

def renaissance_technologies_agent(state: AgentState, agent_id: str='renaissance_technologies_agent'):
    """
    Renaissance Technologies: Pure quantitative, statistical arbitrage
    Structure: Signal Generation → Risk Models → Execution Optimization → Jim Simons Systematic Decision
    Philosophy: Mathematical models, statistical edges, high-frequency systematic trading
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    renaissance_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Signal generation algorithms analyzing patterns')
        metrics = get_financial_metrics(ticker, end_date, period='quarterly', limit=20, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_assets', 'shareholders_equity', 'operating_margin', 'total_debt', 'current_assets', 'current_liabilities', 'outstanding_shares'], end_date, period='quarterly', limit=20, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Signal generation team analysis')
        signal_generation = signal_generation_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk modeling team analysis')
        risk_modeling = risk_modeling_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Execution optimization analysis')
        execution_optimization = execution_optimization_analysis(financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Statistical arbitrage models')
        statistical_arbitrage = statistical_arbitrage_analysis(metrics, financial_line_items)
        progress.update_status(agent_id, ticker, 'Jim Simons systematic synthesis')
        simons_systematic_decision = simons_systematic_synthesis(signal_generation, risk_modeling, execution_optimization, statistical_arbitrage)
        total_score = signal_generation['score'] * 0.35 + statistical_arbitrage['score'] * 0.3 + risk_modeling['score'] * 0.2 + execution_optimization['score'] * 0.15
        if total_score >= 8.0 and signal_generation.get('statistical_significance', 0) > 0.95:
            signal = 'bullish'
        elif total_score <= 3.0 or signal_generation.get('statistical_significance', 0) < 0.6:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'signal_generation': signal_generation, 'risk_modeling': risk_modeling, 'execution_optimization': execution_optimization, 'statistical_arbitrage': statistical_arbitrage, 'simons_systematic_decision': simons_systematic_decision}
        renaissance_output = generate_renaissance_output(ticker, analysis_data, state, agent_id)
        renaissance_analysis[ticker] = {'signal': renaissance_output.signal, 'confidence': renaissance_output.confidence, 'reasoning': renaissance_output.reasoning, 'statistical_edge': renaissance_output.statistical_edge, 'signal_strength': renaissance_output.signal_strength}
        progress.update_status(agent_id, ticker, 'Done', analysis=renaissance_output.reasoning)
    message = HumanMessage(content=json.dumps(renaissance_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(renaissance_analysis, 'Renaissance Technologies')
    state['data']['analyst_signals'][agent_id] = renaissance_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_renaissance_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> RenaissanceSignal:
    """Generate Renaissance's systematic quantitative decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Renaissance Technologies' AI system, implementing Jim Simons' quantitative systematic approach:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Signal Generation Team: Mathematical pattern recognition and statistical signals\n        - Risk Modeling Team: Volatility, correlation, and factor risk analysis\n        - Execution Optimization Team: Market impact and transaction cost modeling\n        - Statistical Arbitrage Team: Pairs trading and mispricing detection\n        - Jim Simons Systematic Synthesis: Mathematical model integration\n\n        PHILOSOPHY:\n        1. Pure Quantitative: Mathematical models over fundamental analysis\n        2. Statistical Edge: Identify small, consistent statistical advantages\n        3. Systematic Execution: Remove human emotion and bias\n        4. High Frequency: Exploit short-term market inefficiencies\n        5. Risk Management: Sophisticated mathematical risk models\n        6. Diversification: Many small bets rather than few large ones\n        7. Continuous Learning: Models adapt and evolve systematically\n\n        REASONING STYLE:\n        - Reference mathematical models and statistical significance\n        - Discuss signal generation algorithms and pattern recognition\n        - Consider risk-adjusted returns and Sharpe ratios\n        - Apply systematic decision thresholds and confidence intervals\n        - Express reasoning in quantitative terms\n        - Acknowledge model limitations and uncertainty\n        - Focus on statistical edge and execution feasibility\n\n        Return the investment signal with statistical edge and signal strength metrics."), ('human', 'Apply Renaissance\'s quantitative systematic analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "statistical_edge": float (0-1),\n          "signal_strength": {{\n            "mean_reversion": float,\n            "momentum": float,\n            "statistical_arbitrage": float,\n            "risk_adjusted_return": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_renaissance_signal():
        return RenaissanceSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', statistical_edge=0.0, signal_strength={'mean_reversion': 0.0, 'momentum': 0.0, 'statistical_arbitrage': 0.0, 'risk_adjusted_return': 0.0})
    return call_llm(prompt=prompt, pydantic_model=RenaissanceSignal, agent_name=agent_id, state=state, default_factory=create_default_renaissance_signal)

def two_sigma_hedge_fund_agent(state: AgentState, agent_id: str='two_sigma_hedge_fund_agent'):
    """
    Two Sigma: Machine learning, data science
    Structure: Data Science → ML Engineering → Risk Models → Portfolio Optimization → Scientific Decision
    Philosophy: Data-driven, machine learning, scientific approach, technology focus
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    two_sigma_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Data science team feature engineering')
        metrics = get_financial_metrics(ticker, end_date, period='quarterly', limit=16, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'research_and_development'], end_date, period='quarterly', limit=16, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Data science team analysis')
        data_science_team = data_science_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'ML engineering team models')
        ml_engineering_team = ml_engineering_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk modeling team analysis')
        risk_modeling_team = risk_modeling_team_analysis(metrics, financial_line_items)
        progress.update_status(agent_id, ticker, 'Portfolio optimization analysis')
        portfolio_optimization = portfolio_optimization_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Scientific method synthesis')
        scientific_synthesis = scientific_method_synthesis(data_science_team, ml_engineering_team, risk_modeling_team, portfolio_optimization)
        total_score = ml_engineering_team['score'] * 0.35 + data_science_team['score'] * 0.25 + portfolio_optimization['score'] * 0.2 + risk_modeling_team['score'] * 0.2
        ml_confidence = ml_engineering_team.get('model_confidence', 0)
        if total_score >= 8.0 and ml_confidence > 0.75:
            signal = 'bullish'
        elif total_score <= 3.5 or ml_confidence < 0.4:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'data_science_team': data_science_team, 'ml_engineering_team': ml_engineering_team, 'risk_modeling_team': risk_modeling_team, 'portfolio_optimization': portfolio_optimization, 'scientific_synthesis': scientific_synthesis}
        two_sigma_output = generate_two_sigma_output(ticker, analysis_data, state, agent_id)
        two_sigma_analysis[ticker] = {'signal': two_sigma_output.signal, 'confidence': two_sigma_output.confidence, 'reasoning': two_sigma_output.reasoning, 'ml_model_predictions': two_sigma_output.ml_model_predictions}
        progress.update_status(agent_id, ticker, 'Done', analysis=two_sigma_output.reasoning)
    message = HumanMessage(content=json.dumps(two_sigma_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(two_sigma_analysis, 'Two Sigma')
    state['data']['analyst_signals'][agent_id] = two_sigma_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_two_sigma_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> TwoSigmaSignal:
    """Generate Two Sigma's machine learning investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Two Sigma's AI system, implementing scientific machine learning approach to investing:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Data Science Team: Feature engineering and alternative data integration\n        - ML Engineering Team: Ensemble models and prediction algorithms\n        - Risk Modeling Team: Value-at-Risk and factor risk analysis\n        - Portfolio Optimization Team: Mean-variance and transaction cost optimization\n        - Scientific Method Synthesis: Hypothesis testing and Bayesian inference\n\n        PHILOSOPHY:\n        1. Data-Driven Decisions: All investment decisions based on data and models\n        2. Machine Learning: Advanced ML algorithms for pattern recognition\n        3. Scientific Method: Hypothesis testing and statistical significance\n        4. Alternative Data: Integration of non-traditional data sources\n        5. Risk Management: Sophisticated quantitative risk models\n        6. Technology Focus: Cutting-edge technology and research\n        7. Academic Rigor: PhD-level research and peer review process\n\n        REASONING STYLE:\n        - Reference machine learning model predictions and confidence levels\n        - Discuss feature engineering and alternative data signals\n        - Apply statistical significance testing and confidence intervals\n        - Consider ensemble model predictions and cross-validation\n        - Express reasoning in probabilistic terms\n        - Acknowledge model limitations and overfitting risks\n        - Focus on scientific hypothesis testing framework\n\n        Return investment signal with ML model predictions and confidence metrics."), ('human', 'Apply Two Sigma\'s machine learning analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "ml_model_predictions": {{\n            "ensemble_prediction": float,\n            "model_confidence": float,\n            "random_forest": float,\n            "gradient_boosting": float,\n            "neural_network": float,\n            "lstm": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_two_sigma_signal():
        return TwoSigmaSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', ml_model_predictions={'ensemble_prediction': 0.5, 'model_confidence': 0.0, 'random_forest': 0.5, 'gradient_boosting': 0.5, 'neural_network': 0.5, 'lstm': 0.5})
    return call_llm(prompt=prompt, pydantic_model=TwoSigmaSignal, agent_name=agent_id, state=state, default_factory=create_default_two_sigma_signal)

def citadel_hedge_fund_agent(state: AgentState, agent_id: str='citadel_hedge_fund_agent'):
    """
    Citadel: Multi-strategy quantitative approach
    Structure: Fundamental Research → Quantitative Research → Global Macro → Trading → Ken Griffin Final Decision
    Philosophy: Multi-strategy approach, technological edge, risk management, market making
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    citadel_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Fundamental research team analyzing company')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=8, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'research_and_development'], end_date, period='annual', limit=8, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Fundamental research department')
        fundamental_research = fundamental_research_department(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Quantitative research department')
        quantitative_research = quantitative_research_department(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Global macro department')
        global_macro = global_macro_department(metrics, financial_line_items)
        progress.update_status(agent_id, ticker, 'Trading department analysis')
        trading_department = trading_department_analysis(financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Risk management oversight')
        risk_management = risk_management_oversight(financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, "Ken Griffin's multi-strategy synthesis")
        ken_griffin_decision = ken_griffin_multi_strategy_synthesis(fundamental_research, quantitative_research, global_macro, trading_department, risk_management)
        total_score = fundamental_research['score'] * 0.25 + quantitative_research['score'] * 0.25 + trading_department['score'] * 0.2 + global_macro['score'] * 0.15 + risk_management['score'] * 0.15
        if total_score >= 8.0 and ken_griffin_decision.get('risk_adjusted_return', 0) > 0.15:
            signal = 'bullish'
        elif total_score <= 4.0 or len(risk_management.get('risk_flags', [])) > 2:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'fundamental_research': fundamental_research, 'quantitative_research': quantitative_research, 'global_macro': global_macro, 'trading_department': trading_department, 'risk_management': risk_management, 'ken_griffin_decision': ken_griffin_decision}
        citadel_output = generate_citadel_output(ticker, analysis_data, state, agent_id)
        citadel_analysis[ticker] = {'signal': citadel_output.signal, 'confidence': citadel_output.confidence, 'reasoning': citadel_output.reasoning, 'strategy_allocation': citadel_output.strategy_allocation}
        progress.update_status(agent_id, ticker, 'Done', analysis=citadel_output.reasoning)
    message = HumanMessage(content=json.dumps(citadel_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(citadel_analysis, 'Citadel')
    state['data']['analyst_signals'][agent_id] = citadel_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_citadel_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> CitadelSignal:
    """Generate Citadel's multi-strategy investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Citadel's AI system, implementing Ken Griffin's multi-strategy hedge fund approach:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Fundamental Research Department: Deep value and quality analysis\n        - Quantitative Research Department: Factor models and statistical signals\n        - Global Macro Department: Economic cycle and currency analysis\n        - Trading Department: Liquidity, execution, and market making\n        - Risk Management: Comprehensive risk oversight\n        - Ken Griffin Multi-Strategy Synthesis: Integration across all platforms\n\n        PHILOSOPHY:\n        1. Multi-Strategy Approach: Diversify across equity long/short, quant, macro, market making\n        2. Technological Edge: Advanced technology and data analytics\n        3. Risk Management: Sophisticated risk controls and position sizing\n        4. Market Making: Provide liquidity while capturing spreads\n        5. Systematic Execution: Minimize market impact and transaction costs\n        6. Global Perspective: Opportunities across markets and asset classes\n        7. Performance Focus: Risk-adjusted returns and alpha generation\n\n        REASONING STYLE:\n        - Reference multiple departmental analyses and perspectives\n        - Integrate fundamental, quantitative, and macro insights\n        - Consider trading feasibility and execution efficiency\n        - Apply rigorous risk management overlay\n        - Discuss multi-strategy allocation and position sizing\n        - Express confidence in technological and analytical edge\n        - Consider market making and liquidity provision opportunities\n\n        Return investment signal with multi-strategy allocation recommendations."), ('human', 'Apply Citadel\'s multi-strategy analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "strategy_allocation": {{\n            "equity_long_short": float,\n            "quantitative": float,\n            "global_macro": float,\n            "market_making": float,\n            "convertible_arbitrage": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_citadel_signal():
        return CitadelSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', strategy_allocation={'equity_long_short': 0.4, 'quantitative': 0.25, 'global_macro': 0.15, 'market_making': 0.1, 'convertible_arbitrage': 0.1})
    return call_llm(prompt=prompt, pydantic_model=CitadelSignal, agent_name=agent_id, state=state, default_factory=create_default_citadel_signal)

def elliott_management_hedge_fund_agent(state: AgentState, agent_id: str='elliott_management_hedge_fund_agent'):
    """
    Elliott Management: Activist investing, event-driven strategies
    Structure: Research → Legal → Activism → Event-Driven → Paul Singer Decision
    Philosophy: Catalyst-driven value creation, shareholder activism, distressed opportunities
    """
    data = state['data']
    end_date = data['end_date']
    tickers = data['tickers']
    api_key = get_api_key_from_state(state, 'FINANCIAL_DATASETS_API_KEY')
    analysis_data = {}
    elliott_analysis = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, 'Research team analyzing activist opportunity')
        metrics = get_financial_metrics(ticker, end_date, period='annual', limit=6, api_key=api_key)
        financial_line_items = search_line_items(ticker, ['revenue', 'net_income', 'free_cash_flow', 'total_debt', 'shareholders_equity', 'operating_margin', 'total_assets', 'current_assets', 'current_liabilities', 'research_and_development'], end_date, period='annual', limit=6, api_key=api_key)
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        progress.update_status(agent_id, ticker, 'Research team fundamental analysis')
        research_team = research_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Legal team governance analysis')
        legal_team = legal_team_governance_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Activism team catalyst identification')
        activism_team = activism_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Event-driven team analysis')
        event_driven_team = event_driven_team_analysis(metrics, financial_line_items, market_cap)
        progress.update_status(agent_id, ticker, 'Paul Singer strategic decision')
        paul_singer_decision = paul_singer_strategic_decision(research_team, legal_team, activism_team, event_driven_team)
        total_score = activism_team['score'] * 0.35 + research_team['score'] * 0.25 + event_driven_team['score'] * 0.2 + legal_team['score'] * 0.2
        activist_potential = activism_team.get('activist_score', 0)
        if total_score >= 7.5 and activist_potential > 0.7:
            signal = 'bullish'
        elif total_score <= 4.0 or legal_team.get('governance_score', 0) < 0.3:
            signal = 'bearish'
        else:
            signal = 'neutral'
        analysis_data[ticker] = {'signal': signal, 'score': total_score, 'research_team': research_team, 'legal_team': legal_team, 'activism_team': activism_team, 'event_driven_team': event_driven_team, 'paul_singer_decision': paul_singer_decision}
        elliott_output = generate_elliott_output(ticker, analysis_data, state, agent_id)
        elliott_analysis[ticker] = {'signal': elliott_output.signal, 'confidence': elliott_output.confidence, 'reasoning': elliott_output.reasoning, 'activist_potential': elliott_output.activist_potential}
        progress.update_status(agent_id, ticker, 'Done', analysis=elliott_output.reasoning)
    message = HumanMessage(content=json.dumps(elliott_analysis), name=agent_id)
    if state['metadata']['show_reasoning']:
        show_agent_reasoning(elliott_analysis, 'Elliott Management')
    state['data']['analyst_signals'][agent_id] = elliott_analysis
    progress.update_status(agent_id, None, 'Done')
    return {'messages': [message], 'data': state['data']}

def generate_elliott_output(ticker: str, analysis_data: dict, state: AgentState, agent_id: str) -> ElliottSignal:
    """Generate Elliott Management's activist investment decision"""
    template = ChatPromptTemplate.from_messages([('system', "You are Elliott Management's AI system, implementing Paul Singer's activist hedge fund approach:\n\n        ORGANIZATIONAL STRUCTURE:\n        - Research Team: Fundamental analysis and hidden value identification\n        - Legal Team: Corporate governance and shareholder rights analysis\n        - Activism Team: Catalyst identification and campaign strategy\n        - Event-Driven Team: M&A, spin-offs, and special situations\n        - Paul Singer Strategic Decision: Overall campaign and value creation strategy\n\n        PHILOSOPHY:\n        1. Catalyst-Driven Investing: Focus on specific catalysts for value creation\n        2. Shareholder Activism: Active engagement to unlock shareholder value\n        3. Event-Driven Opportunities: M&A arbitrage, spin-offs, special situations\n        4. Governance Improvement: Board changes, management accountability\n        5. Strategic Alternatives: Spin-offs, divestitures, strategic sales\n        6. Operational Improvements: Margin expansion, cost reduction\n        7. Balance Sheet Optimization: Capital allocation, leverage, dividends\n\n        REASONING STYLE:\n        - Identify specific catalysts and value creation opportunities\n        - Assess management performance and governance issues\n        - Analyze strategic alternatives and operational improvements\n        - Consider campaign complexity and execution timeline\n        - Express conviction in activist value creation potential\n        - Discuss legal and governance framework for activism\n        - Focus on risk-adjusted returns from catalyst realization\n\n        Return investment signal with detailed activist potential analysis."), ('human', 'Apply Elliott Management\'s activist analysis to {ticker}:\n\n        {analysis_data}\n\n        Provide investment signal in JSON format:\n        {{\n          "signal": "bullish" | "bearish" | "neutral",\n          "confidence": float (0-100),\n          "reasoning": "string",\n          "activist_potential": {{\n            "catalyst_strength": float,\n            "campaign_complexity": float,\n            "expected_timeline": "string",\n            "value_creation_potential": float,\n            "governance_opportunity": float\n          }}\n        }}')])
    prompt = template.invoke({'analysis_data': json.dumps(analysis_data, indent=2), 'ticker': ticker})

    def create_default_elliott_signal():
        return ElliottSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', activist_potential={'catalyst_strength': 0.5, 'campaign_complexity': 0.5, 'expected_timeline': '12-18 months', 'value_creation_potential': 0.5, 'governance_opportunity': 0.5})
    return call_llm(prompt=prompt, pydantic_model=ElliottSignal, agent_name=agent_id, state=state, default_factory=create_default_elliott_signal)

class WebSocketClient:
    """WebSocket client for real-time data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None

    def connect(self, on_message=None, on_error=None, on_close=None):
        """Connect to WebSocket"""
        url = f'wss://ws.finnhub.io?token={self.api_key}'

        def on_open(ws):
            print('WebSocket connection opened')
        self.ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.run_forever()

    def subscribe(self, symbol: str, data_type: str='trade'):
        """Subscribe to real-time data"""
        if self.ws:
            message = json.dumps({'type': f'subscribe-{data_type}', 'symbol': symbol})
            self.ws.send(message)

    def unsubscribe(self, symbol: str, data_type: str='trade'):
        """Unsubscribe from real-time data"""
        if self.ws:
            message = json.dumps({'type': f'unsubscribe-{data_type}', 'symbol': symbol})
            self.ws.send(message)

def subscribe(self, symbol: str, data_type: str='trade'):
    """Subscribe to real-time data"""
    if self.ws:
        message = json.dumps({'type': f'subscribe-{data_type}', 'symbol': symbol})
        self.ws.send(message)

def unsubscribe(self, symbol: str, data_type: str='trade'):
    """Unsubscribe from real-time data"""
    if self.ws:
        message = json.dumps({'type': f'unsubscribe-{data_type}', 'symbol': symbol})
        self.ws.send(message)

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

