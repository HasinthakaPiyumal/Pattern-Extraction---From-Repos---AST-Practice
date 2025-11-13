# Cluster 22

class DataGovHKWrapper:
    """
    Comprehensive wrapper for Data.gov.hk APIs
    """

    def __init__(self, language: str='en'):
        """
        Initialize the Data.gov.hk API wrapper

        Args:
            language: Language preference - 'en' (English), 'tc' (Traditional Chinese), 'sc' (Simplified Chinese)
        """
        self.language = language.lower()
        self.base_urls = {'en': 'https://data.gov.hk/en-data/api/3/action/', 'tc': 'https://data.gov.hk/tc-data/api/3/action/', 'sc': 'https://data.gov.hk/sc-data/api/3/action/'}
        self.historical_base_url = 'https://app.data.gov.hk'
        if self.language not in self.base_urls:
            raise ValueError(f"Unsupported language: {language}. Use 'en', 'tc', or 'sc'")
        self.base_url = self.base_urls[self.language]
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept-Terminal/1.0', 'Accept': 'application/json', 'Accept-Language': f'{self.language}-HK,{self.language};q=0.9,en;q=0.8'})
        self.timeout = 30

    def _make_ckan_request(self, endpoint: str, params: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Make a request to CKAN API endpoint

        Args:
            endpoint: CKAN action endpoint name
            params: Query parameters

        Returns:
            Standardized response dictionary
        """
        try:
            url = f'{self.base_url}{endpoint}'
            clean_params = {k: v for k, v in (params or {}).items() if v is not None}
            response = self.session.get(url, params=clean_params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                return {'data': data.get('result', []), 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint, 'language': self.language, 'last_updated': datetime.now().isoformat(), 'request_params': clean_params, 'help': data.get('help', '')}, 'error': None}
            else:
                return {'data': [], 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint, 'language': self.language, 'last_updated': datetime.now().isoformat(), 'request_params': clean_params}, 'error': data.get('error', {}).get('message', 'Unknown CKAN API error')}
        except requests.exceptions.Timeout:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint}, 'error': 'Request timeout. The API took too long to respond.'}
        except requests.exceptions.ConnectionError:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint}, 'error': 'Connection error. Unable to connect to Data.gov.hk API.'}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_messages = {400: 'Bad request. Invalid parameters.', 404: 'Endpoint not found.', 429: 'Rate limit exceeded. Please try again later.', 500: 'Internal server error.'}
            error_msg = error_messages.get(status_code, f'HTTP Error {status_code}')
            return {'data': [], 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint}, 'error': error_msg}
        except json.JSONDecodeError:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint}, 'error': 'Invalid JSON response from API.'}
        except Exception as e:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk CKAN API', 'endpoint': endpoint}, 'error': f'Unexpected error: {str(e)}'}

    def _make_historical_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Historical Archive API

        Args:
            params: Query parameters for historical archive

        Returns:
            Standardized response dictionary
        """
        try:
            url = f'{self.historical_base_url}/v1/historical-archive/list-files'
            clean_params = {k: v for k, v in params.items() if v is not None}
            response = self.session.get(url, params=clean_params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return {'data': data, 'metadata': {'source': 'Data.gov.hk Historical Archive API', 'endpoint': 'list-files', 'last_updated': datetime.now().isoformat(), 'request_params': clean_params}, 'error': None}
        except requests.exceptions.Timeout:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API', 'endpoint': 'list-files'}, 'error': 'Request timeout. The historical archive API took too long to respond.'}
        except requests.exceptions.ConnectionError:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API', 'endpoint': 'list-files'}, 'error': 'Connection error. Unable to connect to historical archive API.'}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_messages = {400: 'Bad request. Invalid date range or parameters.', 404: 'Historical archive endpoint not found.', 429: 'Rate limit exceeded. Please try again later.', 500: 'Internal server error in historical archive.'}
            error_msg = error_messages.get(status_code, f'HTTP Error {status_code}')
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API', 'endpoint': 'list-files'}, 'error': error_msg}
        except json.JSONDecodeError:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API', 'endpoint': 'list-files'}, 'error': 'Invalid JSON response from historical archive API.'}
        except Exception as e:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API', 'endpoint': 'list-files'}, 'error': f'Unexpected error: {str(e)}'}

    def _translate_text_if_needed(self, text: str) -> str:
        """
        Simple translation for common Chinese terms to English
        In a real implementation, you might use a translation service

        Args:
            text: Text to translate

        Returns:
            Translated text if it's Chinese, original text if English
        """
        if self.language == 'en':
            return text
        translations = {'環境': 'Environment', '交通': 'Transportation', '政府': 'Government', '經濟': 'Economy', '社會': 'Social', '教育': 'Education', '醫療': 'Healthcare', '房屋': 'Housing', '規劃': 'Planning', '統計': 'Statistics', '环境': 'Environment', '交通': 'Transportation', '政府': 'Government', '经济': 'Economy', '社会': 'Social', '教育': 'Education', '医疗': 'Healthcare', '房屋': 'Housing', '规划': 'Planning', '统计': 'Statistics'}
        return translations.get(text, text)

    def get_categories_list(self) -> Dict[str, Any]:
        """
        Get list of all available categories (groups)

        Returns:
            List of category names
        """
        return self._make_ckan_request('group_list')

    def get_category_details(self, category_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific category including datasets

        Args:
            category_id: Unique category identifier (e.g., 'environment', 'transport')

        Returns:
            Category details with datasets list
        """
        if not category_id:
            return {'data': {}, 'metadata': {'source': 'Data.gov.hk CKAN API'}, 'error': 'Category ID is required'}
        return self._make_ckan_request('group_show', {'id': category_id})

    def get_datasets_list(self, limit: Optional[int]=None, offset: Optional[int]=None) -> Dict[str, Any]:
        """
        Get list of all datasets (packages) with pagination

        Args:
            limit: Maximum number of datasets to return
            offset: Number of datasets to skip (for pagination)

        Returns:
            List of dataset names
        """
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        return self._make_ckan_request('package_list', params)

    def get_dataset_details(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get full metadata for a specific dataset

        Args:
            dataset_id: Unique dataset identifier or name

        Returns:
            Complete dataset metadata including resources, tags, etc.
        """
        if not dataset_id:
            return {'data': {}, 'metadata': {'source': 'Data.gov.hk CKAN API'}, 'error': 'Dataset ID is required'}
        return self._make_ckan_request('package_show', {'id': dataset_id})

    def get_historical_files(self, start_date: str, end_date: str, category: Optional[str]=None, format_filter: Optional[str]=None, search: Optional[str]=None, order: Optional[str]=None, skip: Optional[int]=None, max_results: Optional[int]=None) -> Dict[str, Any]:
        """
        Get historical data files within date range

        Args:
            start_date: Start date in YYYYMMDD format (required)
            end_date: End date in YYYYMMDD format (required)
            category: Category ID filter (optional)
            format_filter: File format extension (e.g., 'xls', 'csv') (optional)
            search: Keyword search for dataset names (optional)
            order: Sort order (optional)
            skip: Number of results to skip (optional)
            max_results: Maximum results to return (optional)

        Returns:
            List of historical files matching criteria
        """
        if not start_date or not end_date:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API'}, 'error': 'Both start_date and end_date are required in YYYYMMDD format'}
        if len(start_date) != 8 or len(end_date) != 8:
            return {'data': [], 'metadata': {'source': 'Data.gov.hk Historical Archive API'}, 'error': 'Dates must be in YYYYMMDD format'}
        params = {'start': start_date, 'end': end_date}
        if category:
            params['category'] = category
        if format_filter:
            params['format'] = format_filter
        if search:
            params['search'] = search
        if order:
            params['order'] = order
        if skip is not None:
            params['skip'] = skip
        if max_results is not None:
            params['max'] = max_results
        return self._make_historical_request(params)

    def get_catalogue_overview(self) -> Dict[str, Any]:
        """
        Get complete catalogue overview with categories and sample datasets

        Returns:
            Comprehensive catalogue data with categories and dataset counts
        """
        result = {'success': True, 'timestamp': datetime.now().isoformat(), 'catalogue': {}, 'failed_operations': []}
        try:
            categories_result = self.get_categories_list()
            if categories_result.get('error'):
                result['failed_operations'].append({'operation': 'get_categories_list', 'error': categories_result['error']})
                result['success'] = False
            else:
                categories = categories_result.get('data', [])
                result['catalogue']['categories'] = categories
                result['catalogue']['category_count'] = len(categories)
                sample_categories = categories[:5]
                category_details = {}
                for category_id in sample_categories:
                    try:
                        category_result = self.get_category_details(category_id)
                        if not category_result.get('error'):
                            category_details[category_id] = {'name': self._translate_text_if_needed(category_id), 'dataset_count': len(category_result.get('data', {}).get('packages', [])), 'details': category_result['data']}
                        else:
                            result['failed_operations'].append({'operation': f'get_category_details({category_id})', 'error': category_result['error']})
                    except Exception as e:
                        result['failed_operations'].append({'operation': f'get_category_details({category_id})', 'error': str(e)})
                result['catalogue']['sample_category_details'] = category_details
        except Exception as e:
            result['failed_operations'].append({'operation': 'get_categories_list', 'error': str(e)})
            result['success'] = False
        try:
            datasets_result = self.get_datasets_list(limit=10)
            if datasets_result.get('error'):
                result['failed_operations'].append({'operation': 'get_datasets_list', 'error': datasets_result['error']})
            else:
                result['catalogue']['sample_datasets'] = datasets_result.get('data', [])
        except Exception as e:
            result['failed_operations'].append({'operation': 'get_datasets_list', 'error': str(e)})
        result['metadata'] = {'source': 'Data.gov.hk API', 'language': self.language, 'operation': 'catalogue_overview', 'last_updated': datetime.now().isoformat()}
        return result

    def get_all_category_datasets(self, category_id: str) -> Dict[str, Any]:
        """
        Get all datasets within a specific category

        Args:
            category_id: Category identifier

        Returns:
            All datasets in the category with enhanced metadata
        """
        result = {'success': True, 'timestamp': datetime.now().isoformat(), 'category_id': category_id, 'datasets': {}, 'failed_datasets': []}
        try:
            category_result = self.get_category_details(category_id)
            if category_result.get('error'):
                return {'success': False, 'error': category_result['error'], 'category_id': category_id}
            category_data = category_result.get('data', {})
            packages = category_data.get('packages', [])
            result['category_info'] = {'name': self._translate_text_if_needed(category_id), 'title': category_data.get('title', category_id), 'description': category_data.get('description', ''), 'dataset_count': len(packages)}
            for package in packages:
                package_name = package.get('name', '')
                if package_name:
                    try:
                        dataset_result = self.get_dataset_details(package_name)
                        if not dataset_result.get('error'):
                            result['datasets'][package_name] = {'name': package_name, 'title': dataset_result['data'].get('title', ''), 'notes': dataset_result['data'].get('notes', ''), 'resources': dataset_result['data'].get('resources', []), 'tags': [tag.get('display_name', '') for tag in dataset_result['data'].get('tags', [])], 'metadata': dataset_result['data']}
                        else:
                            result['failed_datasets'].append({'dataset': package_name, 'error': dataset_result['error']})
                    except Exception as e:
                        result['failed_datasets'].append({'dataset': package_name, 'error': str(e)})
            result['success'] = len(result['failed_datasets']) < len(packages)
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve category datasets: {str(e)}', 'category_id': category_id}
        result['metadata'] = {'source': 'Data.gov.hk API', 'language': self.language, 'operation': 'get_all_category_datasets', 'last_updated': datetime.now().isoformat()}
        return result

def get_categories_list(self) -> Dict[str, Any]:
    """
        Get list of all available categories (groups)

        Returns:
            List of category names
        """
    return self._make_ckan_request('group_list')

def get_category_details(self, category_id: str) -> Dict[str, Any]:
    """
        Get detailed information about a specific category including datasets

        Args:
            category_id: Unique category identifier (e.g., 'environment', 'transport')

        Returns:
            Category details with datasets list
        """
    if not category_id:
        return {'data': {}, 'metadata': {'source': 'Data.gov.hk CKAN API'}, 'error': 'Category ID is required'}
    return self._make_ckan_request('group_show', {'id': category_id})

def get_datasets_list(self, limit: Optional[int]=None, offset: Optional[int]=None) -> Dict[str, Any]:
    """
        Get list of all datasets (packages) with pagination

        Args:
            limit: Maximum number of datasets to return
            offset: Number of datasets to skip (for pagination)

        Returns:
            List of dataset names
        """
    params = {}
    if limit is not None:
        params['limit'] = limit
    if offset is not None:
        params['offset'] = offset
    return self._make_ckan_request('package_list', params)

def get_dataset_details(self, dataset_id: str) -> Dict[str, Any]:
    """
        Get full metadata for a specific dataset

        Args:
            dataset_id: Unique dataset identifier or name

        Returns:
            Complete dataset metadata including resources, tags, etc.
        """
    if not dataset_id:
        return {'data': {}, 'metadata': {'source': 'Data.gov.hk CKAN API'}, 'error': 'Dataset ID is required'}
    return self._make_ckan_request('package_show', {'id': dataset_id})

