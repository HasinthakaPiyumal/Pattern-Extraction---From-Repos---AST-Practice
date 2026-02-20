# Cluster 3

def parse_pytest_summary(output: str) -> Tuple[int, int, int]:
    """
    Returns (passed, failed, errors) based on pytest short summary lines.
    """
    passed = failed = errors = 0
    m = re.search('=+\\s*(.+?)\\s*=+', output)
    if m:
        segment = m.group(1)
        m_pass = re.search('(\\d+)\\s+passed', segment)
        m_fail = re.search('(\\d+)\\s+failed', segment)
        m_err = re.search('(\\d+)\\s+error', segment)
        if m_pass:
            passed = int(m_pass.group(1))
        if m_fail:
            failed = int(m_fail.group(1))
        if m_err:
            errors = int(m_err.group(1))
    return (passed, failed, errors)

# Node: search
# Node: group
# Node: int
def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """Extract API endpoints and features from README.md"""
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    endpoints = []
    pattern1 = re.compile('(GET|POST|PUT|DELETE|PATCH)\\s+(/[^\\s\\-]+)\\s*[-:]?\\s*(.+?)(?:\\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    table_pattern = re.compile('\\|\\s*(GET|POST|PUT|DELETE|PATCH)\\s*\\|\\s*([^\\|]+?)\\s*\\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({'method': match.group(1).upper(), 'path': path, 'description': ''})
    code_blocks = re.findall('```[\\w]*\\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f'{ep['method']}:{ep['path']}'
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    return unique_endpoints

# Node: compile
# Node: finditer
# Node: upper
# Node: set
# Node: add
def parse_pytest_summary(output: str) -> Tuple[int, int, int]:
    """
    Returns (passed, failed, errors) based on pytest short summary lines.
    """
    passed = failed = errors = 0
    m = re.search('=+\\s*(.+?)\\s*=+', output)
    if m:
        segment = m.group(1)
        m_pass = re.search('(\\d+)\\s+passed', segment)
        m_fail = re.search('(\\d+)\\s+failed', segment)
        m_err = re.search('(\\d+)\\s+error', segment)
        if m_pass:
            passed = int(m_pass.group(1))
        if m_fail:
            failed = int(m_fail.group(1))
        if m_err:
            errors = int(m_err.group(1))
    return (passed, failed, errors)

def parse_pytest_output(output):
    """Parse pytest output for pass/fail counts and coverage."""
    passed = 0
    failed = 0
    coverage = 0.0
    match = re.search('(\\d+) passed', output)
    if match:
        passed = int(match.group(1))
    match = re.search('(\\d+) failed', output)
    if match:
        failed = int(match.group(1))
    cov_match = re.search('TOTAL\\s+\\d+\\s+\\d+\\s+(\\d+)%', output)
    if cov_match:
        coverage = float(cov_match.group(1))
    return (passed, failed, coverage)

# Node: float
def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """
    Extract API endpoints and features from README.md
    
    Returns:
        List of dictionaries containing endpoint information:
        [{
            'method': 'GET/POST/PUT/DELETE',
            'path': '/api/...',
            'description': '...'
        }]
    """
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    endpoints = []
    pattern1 = re.compile('(GET|POST|PUT|DELETE|PATCH)\\s+(/[^\\s\\-]+)\\s*[-:]?\\s*(.+?)(?:\\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    table_pattern = re.compile('\\|\\s*(GET|POST|PUT|DELETE|PATCH)\\s*\\|\\s*([^\\|]+?)\\s*\\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({'method': match.group(1).upper(), 'path': path, 'description': ''})
    code_blocks = re.findall('```[\\w]*\\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    feature_pattern = re.compile('[-*]\\s+([A-Z][A-Za-z\\s]+(?:Check|Login|Register|Create|Update|Delete|Get|List|Manage|Service|API))', re.MULTILINE)
    features = feature_pattern.findall(content)
    for feature in features:
        feature_clean = feature.strip()
        if len(endpoints) == 0:
            endpoints.append({'method': 'FEATURE', 'path': feature_clean, 'description': feature_clean})
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f'{ep['method']}:{ep['path']}'
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    return unique_endpoints

def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """Extract API endpoints and features from README.md"""
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    endpoints = []
    pattern1 = re.compile('(GET|POST|PUT|DELETE|PATCH)\\s+(/[^\\s\\-]+)\\s*[-:]?\\s*(.+?)(?:\\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    table_pattern = re.compile('\\|\\s*(GET|POST|PUT|DELETE|PATCH)\\s*\\|\\s*([^\\|]+?)\\s*\\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({'method': match.group(1).upper(), 'path': path, 'description': ''})
    code_blocks = re.findall('```[\\w]*\\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f'{ep['method']}:{ep['path']}'
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    return unique_endpoints

# Node: time
class TestPerformance:
    BASE_URL = 'http://localhost:8000/api/v1'

    def setup_method(self):
        self.medium_df = pd.DataFrame({f'col{i}': range(1000) for i in range(10)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.medium_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.medium_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        self.small_csv_data = base64.b64encode('Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai\nWang Wu,28,Shenzhen'.encode('utf-8')).decode('utf-8')

    def test_single_conversion_performance(self):
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.medium_excel_data}
        times = []
        for _ in range(10):
            start_time = time.time()
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            end_time = time.time()
            assert response.status_code == 200
            times.append(end_time - start_time)
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        print('Single conversion performance statistics:')
        print(f'Average time: {avg_time:.2f} seconds')
        print(f'Median time: {median_time:.2f} seconds')
        print(f'Minimum time: {min_time:.2f} seconds')
        print(f'Maximum time: {max_time:.2f} seconds')
        print(f'Standard deviation: {std_dev:.2f} seconds')
        assert avg_time < 5.0, f'Average conversion time is too long: {avg_time:.2f} seconds'
        assert max_time < 10.0, f'Maximum conversion time is too long: {max_time:.2f} seconds'
        assert std_dev < 2.0, f'Conversion time stability is poor: {std_dev:.2f} seconds'

    def test_concurrent_requests_performance(self):

        def make_request(request_id):
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
            start_time = time.time()
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            end_time = time.time()
            return {'request_id': request_id, 'success': response.status_code == 200, 'response_time': end_time - start_time}
        concurrency_levels = [5, 10, 20]
        results = {}
        for concurrency in concurrency_levels:
            print(f'\nTesting concurrency level: {concurrency}')
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrency)]
                responses = [future.result() for future in as_completed(futures)]
            end_time = time.time()
            response_times = [r['response_time'] for r in responses if r['success']]
            success_count = sum((1 for r in responses if r['success']))
            results[concurrency] = {'total_requests': len(responses), 'success_count': success_count, 'avg_response_time': statistics.mean(response_times) if response_times else 0, 'total_time': end_time - start_time}
            print(f'Successful requests: {success_count}/{len(responses)}')
            print(f'Average response time: {results[concurrency]['avg_response_time']:.2f} seconds')
            print(f'Total time: {results[concurrency]['total_time']:.2f} seconds')
            assert success_count >= concurrency * 0.8, f'Concurrent request success rate is too low: {success_count}/{concurrency}'
        if len(results) >= 2:
            time_5 = results[5]['total_time']
            time_10 = results[10]['total_time']
            assert time_10 < time_5 * 3.0, f'Concurrency scalability is poor: 10 concurrency time {time_10:.2f} seconds vs 5 concurrency expected upper limit {time_5 * 3.0:.2f} seconds'

    def test_memory_usage_stability(self):

        def continuous_requests(duration_seconds=30):
            end_time = time.time() + duration_seconds
            request_count = 0
            errors = []
            while time.time() < end_time:
                try:
                    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
                    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
                    if response.status_code != 200:
                        errors.append(f'Request failed: {response.status_code}')
                    request_count += 1
                    time.sleep(0.1)
                except Exception as e:
                    errors.append(str(e))
                    time.sleep(0.1)
            return (request_count, errors)
        request_count, errors = continuous_requests(30)
        print(f'\nContinuous requests test results:')
        print(f'Total requests: {request_count}')
        print(f'Errors: {len(errors)}')
        print(f'Error rate: {len(errors) / request_count * 100:.2f}%' if request_count > 0 else 'Error rate: N/A')
        assert request_count > 0, 'Failed to send any requests'
        assert len(errors) / request_count < 0.1, f'Error rate is too high: {len(errors)}/{request_count}'

    def test_health_check_under_load(self):

        def load_generator():
            end_time = time.time() + 20
            while time.time() < end_time:
                payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
                requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
                time.sleep(0.2)

        def health_checks():
            health_times = []
            end_time = time.time() + 20
            while time.time() < end_time:
                start_time = time.time()
                response = requests.get(f'{self.BASE_URL}/health', timeout=5)
                end_time = time.time()
                health_times.append(end_time - start_time)
                assert response.status_code == 200
                time.sleep(0.5)
            return health_times
        load_thread = threading.Thread(target=load_generator)
        load_thread.start()
        health_response_times = health_checks()
        load_thread.join()
        avg_health_time = statistics.mean(health_response_times)
        max_health_time = max(health_response_times)
        print('Health check performance under load:')
        print(f'Average response time: {avg_health_time:.3f} seconds')
        print(f'Maximum response time: {max_health_time:.3f} seconds')
        assert avg_health_time < 1.0, f'Health check response is too slow under load: {avg_health_time:.3f} seconds'
        assert max_health_time < 2.0, f'Maximum health check response time is too long under load: {max_health_time:.3f} seconds'

    def test_large_file_performance(self):
        large_df = pd.DataFrame({f'col{i}': range(5000) for i in range(20)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=120)
        end_time = time.time()
        assert response.status_code == 200
        conversion_time = end_time - start_time
        print('Large file conversion performance:')
        print(f'Conversion time: {conversion_time:.2f} seconds')
        print(f'File size: {len(large_excel_data) * 3 / 4 / 1024:.1f} KB')
        assert conversion_time < 60.0, f'Large file conversion time is too long: {conversion_time:.2f} seconds'
        data = response.json()
        assert data['success'] is True

    def test_response_time_distribution(self):

        def make_request():
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
            start_time = time.time()
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
            end_time = time.time()
            return end_time - start_time if response.status_code == 200 else None
        response_times = []
        for _ in range(50):
            time_taken = make_request()
            if time_taken is not None:
                response_times.append(time_taken)
        if response_times:
            sorted_times = sorted(response_times)
            print('Response time distribution:')
            print(f'Average: {statistics.mean(response_times):.3f} seconds')
            print(f'Median: {statistics.median(response_times):.3f} seconds')
            print(f'90th percentile: {sorted_times[int(len(sorted_times) * 0.9)]:.3f} seconds')
            print(f'95th percentile: {sorted_times[int(len(sorted_times) * 0.95)]:.3f} seconds')
            print(f'99th percentile: {sorted_times[int(len(sorted_times) * 0.99)]:.3f} seconds')
            assert statistics.mean(response_times) < 3.0, 'Average response time is too long'
            assert sorted_times[int(len(sorted_times) * 0.95)] < 5.0, '95th percentile response time is too long'

    def test_resource_cleanup_verification(self):

        def intensive_workload():
            for i in range(20):
                payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.medium_excel_data}
                response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    assert 'metadata' in data
                    assert 'conversion_time' in data['metadata']
                time.sleep(0.1)
        start_time = time.time()
        health_before = requests.get(f'{self.BASE_URL}/health', timeout=5)
        assert health_before.status_code == 200
        intensive_workload()
        health_after = requests.get(f'{self.BASE_URL}/health', timeout=5)
        assert health_after.status_code == 200
        end_time = time.time()
        print('Resource cleanup verification:')
        print(f'Workload execution time: {end_time - start_time:.2f} seconds')
        print('Service remains healthy after high load')
        health_data_before = health_before.json()
        health_data_after = health_after.json()
        assert health_data_before['status'] == 'healthy'
        assert health_data_after['status'] == 'healthy'

def make_request():
    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
    end_time = time.time()
    return end_time - start_time if response.status_code == 200 else None

def load_generator():
    end_time = time.time() + 20
    while time.time() < end_time:
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
        requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
        time.sleep(0.2)

def test_resource_cleanup_verification(self):

    def intensive_workload():
        for i in range(20):
            payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.medium_excel_data}
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                assert 'metadata' in data
                assert 'conversion_time' in data['metadata']
            time.sleep(0.1)
    start_time = time.time()
    health_before = requests.get(f'{self.BASE_URL}/health', timeout=5)
    assert health_before.status_code == 200
    intensive_workload()
    health_after = requests.get(f'{self.BASE_URL}/health', timeout=5)
    assert health_after.status_code == 200
    end_time = time.time()
    print('Resource cleanup verification:')
    print(f'Workload execution time: {end_time - start_time:.2f} seconds')
    print('Service remains healthy after high load')
    health_data_before = health_before.json()
    health_data_after = health_after.json()
    assert health_data_before['status'] == 'healthy'
    assert health_data_after['status'] == 'healthy'

# Node: intensive_workload
class TestHealthEndpoint:
    BASE_URL = 'http://localhost:8000/api/v1'

    def test_health_endpoint_available(self):
        try:
            response = requests.get(f'{self.BASE_URL}/health', timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'status' in data
            assert 'timestamp' in data
            assert 'version' in data
            assert data['status'] in ['healthy', 'unhealthy']
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except requests.exceptions.ConnectionError:
            pytest.fail('Unable to connect to the service, please ensure the service is started')

    def test_health_response_format(self):
        response = requests.get(f'{self.BASE_URL}/health')
        data = response.json()
        required_fields = ['status', 'timestamp', 'version']
        for field in required_fields:
            assert field in data, f'Response is missing required field: {field}'
        assert isinstance(data['status'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['version'], str)

    def test_health_endpoint_performance(self):
        start_time = time.time()
        response = requests.get(f'{self.BASE_URL}/health')
        end_time = time.time()
        response_time = end_time - start_time
        assert response_time < 1.0, f'Health check response time is too long: {response_time:.2f} seconds'
        assert response.status_code == 200

    def test_health_endpoint_concurrent_requests(self):
        import threading
        results = []
        errors = []

        def make_request():
            try:
                response = requests.get(f'{self.BASE_URL}/health', timeout=5)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors occurred during concurrent requests: {errors}'
        assert len(results) == 10
        assert all((status == 200 for status in results))

    def test_health_endpoint_headers(self):
        response = requests.get(f'{self.BASE_URL}/health')
        assert response.headers['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response.headers or '*' in response.headers.get('Access-Control-Allow-Origin', '')

    @pytest.mark.parametrize('invalid_method', ['POST', 'PUT', 'DELETE'])
    def test_health_endpoint_invalid_methods(self, invalid_method):
        response = requests.request(invalid_method, f'{self.BASE_URL}/health')
        assert response.status_code in [200, 405]

    def test_health_endpoint_with_query_params(self):
        response = requests.get(f'{self.BASE_URL}/health?param=test&debug=1')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data

def test_health_endpoint_performance(self):
    start_time = time.time()
    response = requests.get(f'{self.BASE_URL}/health')
    end_time = time.time()
    response_time = end_time - start_time
    assert response_time < 1.0, f'Health check response time is too long: {response_time:.2f} seconds'
    assert response.status_code == 200

@pytest.fixture
def test_user(db):
    """Create a test user and return authentication headers."""
    user_data = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123'}
    hashed_password = get_password_hash(user_data['password'])
    user = User(username=user_data['username'], email=user_data['email'], hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_user_access_token(user.id)
    headers = {'Authorization': f'Bearer {access_token}'}
    return {'user': user, 'headers': headers, 'data': user_data}

# Node: get_password_hash
# Node: User
# Node: commit
# Node: refresh
# Node: create_user_access_token
@pytest.fixture
def test_user_2(db):
    """Create a second test user for permission testing."""
    user_data = {'username': 'testuser2', 'email': 'test2@example.com', 'password': 'password123'}
    hashed_password = get_password_hash(user_data['password'])
    user = User(username=user_data['username'], email=user_data['email'], hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_user_access_token(user.id)
    headers = {'Authorization': f'Bearer {access_token}'}
    return {'user': user, 'headers': headers, 'data': user_data}

class TestEmailHistory:
    """Test cases for GET /api/v1/mail/history endpoint."""

    def test_get_history_success(self):
        """Test successfully retrieving email history."""
        response = requests.get(HISTORY_URL)
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'limit' in data
        assert 'offset' in data
        assert 'emails' in data
        assert isinstance(data['emails'], list)

    def test_get_history_with_limit(self):
        """Test retrieving history with limit parameter."""
        limit = 10
        response = requests.get(HISTORY_URL, params={'limit': limit})
        assert response.status_code == 200
        data = response.json()
        assert data['limit'] == limit
        assert len(data['emails']) <= limit

    def test_get_history_with_offset(self):
        """Test retrieving history with offset parameter."""
        response1 = requests.get(HISTORY_URL, params={'limit': 5, 'offset': 0})
        assert response1.status_code == 200
        data1 = response1.json()
        response2 = requests.get(HISTORY_URL, params={'limit': 5, 'offset': 5})
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['offset'] == 5
        if len(data1['emails']) == 5 and len(data2['emails']) > 0:
            assert data1['emails'][0]['mail_id'] != data2['emails'][0]['mail_id']

    def test_get_history_default_limit(self):
        """Test that default limit is 50."""
        response = requests.get(HISTORY_URL)
        assert response.status_code == 200
        data = response.json()
        assert data['limit'] == 50
        assert len(data['emails']) <= 50

    def test_get_history_max_limit(self):
        """Test that maximum limit is 100."""
        response = requests.get(HISTORY_URL, params={'limit': 150})
        assert response.status_code == 200
        data = response.json()
        assert data['limit'] <= 100

    def test_get_history_invalid_limit(self):
        """Test retrieving history with invalid limit returns 400."""
        response = requests.get(HISTORY_URL, params={'limit': -1})
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_get_history_invalid_offset(self):
        """Test retrieving history with invalid offset returns 400."""
        response = requests.get(HISTORY_URL, params={'offset': -1})
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_get_history_filter_by_status(self):
        """Test filtering history by status."""
        statuses = ['pending', 'sent', 'failed', 'delivered', 'bounced']
        for status in statuses:
            response = requests.get(HISTORY_URL, params={'status': status})
            assert response.status_code == 200
            data = response.json()
            for email in data['emails']:
                assert email['status'] == status

    def test_get_history_invalid_status(self):
        """Test filtering with invalid status returns 400."""
        response = requests.get(HISTORY_URL, params={'status': 'invalid_status'})
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_get_history_filter_by_date_range(self):
        """Test filtering history by date range."""
        send_payload = {'to': ['test@example.com'], 'subject': 'Date Range Test', 'body': 'Test body'}
        requests.post(SEND_EMAIL_URL, json=send_payload)
        to_date = datetime.utcnow().isoformat() + 'Z'
        from_date = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        response = requests.get(HISTORY_URL, params={'from_date': from_date, 'to_date': to_date})
        assert response.status_code == 200
        data = response.json()
        assert 'emails' in data

    def test_get_history_invalid_date_format(self):
        """Test filtering with invalid date format returns 400."""
        response = requests.get(HISTORY_URL, params={'from_date': 'invalid-date'})
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_get_history_from_date_after_to_date(self):
        """Test filtering with from_date after to_date returns 400."""
        to_date = (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z'
        from_date = datetime.utcnow().isoformat() + 'Z'
        response = requests.get(HISTORY_URL, params={'from_date': from_date, 'to_date': to_date})
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_get_history_email_fields(self):
        """Test that each email in history has required fields."""
        send_payload = {'to': ['test@example.com'], 'subject': 'Field Test', 'body': 'Test body'}
        requests.post(SEND_EMAIL_URL, json=send_payload)
        response = requests.get(HISTORY_URL, params={'limit': 1})
        assert response.status_code == 200
        data = response.json()
        if len(data['emails']) > 0:
            email = data['emails'][0]
            required_fields = ['mail_id', 'to', 'subject', 'status', 'sent_at', 'delivered_at']
            for field in required_fields:
                assert field in email

    def test_get_history_empty_result(self):
        """Test that history with filters that match nothing returns empty list."""
        from_date = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        to_date = (datetime.utcnow() + timedelta(days=2)).isoformat() + 'Z'
        response = requests.get(HISTORY_URL, params={'from_date': from_date, 'to_date': to_date})
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0
        assert len(data['emails']) == 0

    def test_get_history_pagination(self):
        """Test pagination through email history."""
        response1 = requests.get(HISTORY_URL, params={'limit': 10, 'offset': 0})
        assert response1.status_code == 200
        data1 = response1.json()
        total = data1['total']
        if total > 10:
            response2 = requests.get(HISTORY_URL, params={'limit': 10, 'offset': 10})
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2['total'] == total
            if len(data2['emails']) > 0:
                ids1 = [e['mail_id'] for e in data1['emails']]
                ids2 = [e['mail_id'] for e in data2['emails']]
                assert len(set(ids1) & set(ids2)) == 0

    def test_get_history_combined_filters(self):
        """Test using multiple filters together."""
        params = {'limit': 20, 'offset': 0, 'status': 'sent'}
        response = requests.get(HISTORY_URL, params=params)
        assert response.status_code == 200
        data = response.json()
        assert data['limit'] == 20
        assert data['offset'] == 0
        for email in data['emails']:
            assert email['status'] == 'sent'

    def test_get_history_ordering(self):
        """Test that emails are ordered by sent_at timestamp (most recent first)."""
        response = requests.get(HISTORY_URL, params={'limit': 10})
        assert response.status_code == 200
        data = response.json()
        if len(data['emails']) >= 2:
            for i in range(len(data['emails']) - 1):
                time1 = data['emails'][i]['sent_at']
                time2 = data['emails'][i + 1]['sent_at']
                if time1 and time2:
                    dt1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
                    dt2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
                    assert dt1 >= dt2

def test_get_history_pagination(self):
    """Test pagination through email history."""
    response1 = requests.get(HISTORY_URL, params={'limit': 10, 'offset': 0})
    assert response1.status_code == 200
    data1 = response1.json()
    total = data1['total']
    if total > 10:
        response2 = requests.get(HISTORY_URL, params={'limit': 10, 'offset': 10})
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['total'] == total
        if len(data2['emails']) > 0:
            ids1 = [e['mail_id'] for e in data1['emails']]
            ids2 = [e['mail_id'] for e in data2['emails']]
            assert len(set(ids1) & set(ids2)) == 0

@pytest.mark.edge
def test_multiple_files_same_name(api_base_url, auth_headers):
    """Test uploading multiple files with the same name"""
    filename = 'duplicate_name.txt'
    uploaded_ids = []
    for i in range(3):
        file_content = io.BytesIO(f'Content {i}'.encode())
        files = {'file': (filename, file_content, 'text/plain')}
        resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
        assert resp.status_code in (200, 201)
        file_id = resp.json().get('id')
        uploaded_ids.append(file_id)
    assert len(uploaded_ids) == len(set(uploaded_ids))
    for file_id in uploaded_ids:
        try:
            requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
        except:
            pass

@pytest.mark.auth
def test_user_registration(api_base_url, wait_for_service):
    """Test user registration with valid credentials"""
    import time
    credentials = {'username': f'new_user_{int(time.time() * 1000)}', 'password': 'ValidPass123!'}
    resp = requests.post(f'{api_base_url}/auth/register', json=credentials, timeout=10)
    assert resp.status_code in (201, 409)
    if resp.status_code == 201:
        data = resp.json()
        assert 'id' in data
        assert data.get('username') == credentials['username']
        assert 'created_at' in data

@pytest.mark.auth
def test_user_registration_invalid_password(api_base_url, wait_for_service):
    """Test user registration with invalid password"""
    import time
    credentials = {'username': f'test_user_{int(time.time() * 1000)}', 'password': 'short'}
    resp = requests.post(f'{api_base_url}/auth/register', json=credentials, timeout=10)
    assert resp.status_code == 400

@pytest.fixture
def user_credentials():
    """Generate unique test user credentials"""
    timestamp = int(time.time() * 1000)
    return {'username': f'test_user_{timestamp}', 'password': 'TestPass123!'}

@pytest.fixture
def second_user_token(api_base_url, wait_for_service):
    """Create and authenticate a second user for permission testing"""
    timestamp = int(time.time() * 1000)
    credentials = {'username': f'test_user_2_{timestamp}', 'password': 'TestPass456!'}
    reg_resp = requests.post(f'{api_base_url}/auth/register', json=credentials, timeout=10)
    if reg_resp.status_code not in (201, 409):
        pytest.fail(f'Failed to register second user: {reg_resp.status_code}')
    login_resp = requests.post(f'{api_base_url}/auth/login', json=credentials, timeout=10)
    if login_resp.status_code == 200:
        data = login_resp.json()
        if 'access_token' in data:
            return data['access_token']
    pytest.fail(f'Failed to login second user: {login_resp.status_code}')

class TestLeaderboardIntegration:
    """Integration tests for leaderboard functionality."""

    @pytest.mark.integration
    @pytest.mark.leaderboard
    def test_score_update_affects_ranking(self, api_base_url, sample_score_data):
        """Test that updating a score affects the player's ranking."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        initial_rank = response.json()['player_rank']
        higher_score_data = sample_score_data.copy()
        higher_score_data['score'] = sample_score_data['score'] + 1000
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=higher_score_data)
        assert_response_success(response, 200)
        new_rank = response.json()['player_rank']
        assert new_rank <= initial_rank

    def test_multiple_players_ranking(self, api_base_url, sample_leaderboard_data):
        """Test ranking with multiple players."""
        for score_data in sample_leaderboard_data:
            response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
            assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        leaderboard = data['leaderboard']
        submitted_player_ids = {score_data['player_id'] for score_data in sample_leaderboard_data}
        leaderboard_player_ids = {entry['player_id'] for entry in leaderboard}
        assert submitted_player_ids.issubset(leaderboard_player_ids)

    def test_game_type_separation(self, api_base_url, sample_leaderboard_data):
        """Test that different game types have separate leaderboards."""
        for score_data in sample_leaderboard_data:
            response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
            assert_response_success(response, 200)
        game_types = set((score_data['game_type'] for score_data in sample_leaderboard_data))
        for game_type in game_types:
            response = make_request('GET', f'{api_base_url}/leaderboard?game_type={game_type}')
            assert_response_success(response, 200)
            data = response.json()
            leaderboard = data['leaderboard']
            for entry in leaderboard:
                assert entry['game_type'] == game_type

def test_game_type_separation(self, api_base_url, sample_leaderboard_data):
    """Test that different game types have separate leaderboards."""
    for score_data in sample_leaderboard_data:
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
        assert_response_success(response, 200)
    game_types = set((score_data['game_type'] for score_data in sample_leaderboard_data))
    for game_type in game_types:
        response = make_request('GET', f'{api_base_url}/leaderboard?game_type={game_type}')
        assert_response_success(response, 200)
        data = response.json()
        leaderboard = data['leaderboard']
        for entry in leaderboard:
            assert entry['game_type'] == game_type

