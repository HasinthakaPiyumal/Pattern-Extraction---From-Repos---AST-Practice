# Cluster 5

# Node: isinstance
# Node: copy
# Node: set
class TestStats:

    def test_get_stats(self, api_client):
        response = api_client.get('/stats')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'data' in result
        data = result['data']
        assert 'total_tasks' in data
        assert 'active_tasks' in data
        assert 'total_executions' in data
        assert 'successful_executions' in data
        assert 'failed_executions' in data
        assert isinstance(data['total_tasks'], int)
        assert isinstance(data['active_tasks'], int)
        assert isinstance(data['total_executions'], int)
        assert isinstance(data['successful_executions'], int)
        assert isinstance(data['failed_executions'], int)
        assert data['total_tasks'] >= 0
        assert data['active_tasks'] >= 0
        assert data['active_tasks'] <= data['total_tasks']
        assert data['total_executions'] >= 0
        assert data['successful_executions'] >= 0
        assert data['failed_executions'] >= 0
        assert data['successful_executions'] + data['failed_executions'] <= data['total_executions']

    def test_stats_increase_after_task_creation(self, api_client, sample_task_data, cleanup_tasks):
        initial_response = api_client.get('/stats')
        initial_stats = initial_response.json()['data']
        initial_total = initial_stats['total_tasks']
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        updated_response = api_client.get('/stats')
        updated_stats = updated_response.json()['data']
        assert updated_stats['total_tasks'] == initial_total + 1

    def test_stats_active_tasks_count(self, api_client, sample_task_data, cleanup_tasks):
        initial_response = api_client.get('/stats')
        initial_stats = initial_response.json()['data']
        initial_active = initial_stats['active_tasks']
        task_data = sample_task_data['file_cleanup']
        task_data['enabled'] = True
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        updated_response = api_client.get('/stats')
        updated_stats = updated_response.json()['data']
        assert updated_stats['active_tasks'] == initial_active + 1
        api_client.post(f'/tasks/{task_id}/toggle', data={'enabled': False})
        final_response = api_client.get('/stats')
        final_stats = final_response.json()['data']
        assert final_stats['active_tasks'] == initial_active

    @pytest.mark.slow
    def test_stats_execution_count(self, api_client, sample_task_data, cleanup_tasks):
        initial_response = api_client.get('/stats')
        initial_stats = initial_response.json()['data']
        initial_executions = initial_stats['total_executions']
        task_data = sample_task_data['data_summary']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        api_client.post(f'/tasks/{task_id}/execute')
        time.sleep(1)
        updated_response = api_client.get('/stats')
        updated_stats = updated_response.json()['data']
        assert updated_stats['total_executions'] >= initial_executions + 1

    def test_stats_after_task_deletion(self, api_client, sample_task_data):
        initial_response = api_client.get('/stats')
        initial_stats = initial_response.json()['data']
        initial_total = initial_stats['total_tasks']
        task_data = sample_task_data['data_backup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        after_create_response = api_client.get('/stats')
        after_create_stats = after_create_response.json()['data']
        assert after_create_stats['total_tasks'] == initial_total + 1
        api_client.delete(f'/tasks/{task_id}')
        final_response = api_client.get('/stats')
        final_stats = final_response.json()['data']
        assert final_stats['total_tasks'] == initial_total

def test_get_stats(self, api_client):
    response = api_client.get('/stats')
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert 'data' in result
    data = result['data']
    assert 'total_tasks' in data
    assert 'active_tasks' in data
    assert 'total_executions' in data
    assert 'successful_executions' in data
    assert 'failed_executions' in data
    assert isinstance(data['total_tasks'], int)
    assert isinstance(data['active_tasks'], int)
    assert isinstance(data['total_executions'], int)
    assert isinstance(data['successful_executions'], int)
    assert isinstance(data['failed_executions'], int)
    assert data['total_tasks'] >= 0
    assert data['active_tasks'] >= 0
    assert data['active_tasks'] <= data['total_tasks']
    assert data['total_executions'] >= 0
    assert data['successful_executions'] >= 0
    assert data['failed_executions'] >= 0
    assert data['successful_executions'] + data['failed_executions'] <= data['total_executions']

class TestStatsEdgeCases:

    def test_stats_with_no_tasks(self, api_client):
        response = api_client.get('/stats')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        data = result['data']
        for key in ['total_tasks', 'active_tasks', 'total_executions', 'successful_executions', 'failed_executions']:
            assert key in data
            assert data[key] >= 0

    def test_stats_response_format(self, api_client):
        response = api_client.get('/stats')
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        result = response.json()
        assert 'success' in result
        assert 'data' in result
        assert isinstance(result['data'], dict)
        required_fields = ['total_tasks', 'active_tasks', 'total_executions', 'successful_executions', 'failed_executions']
        for field in required_fields:
            assert field in result['data'], f'Lack of field: {field}'

def test_stats_response_format(self, api_client):
    response = api_client.get('/stats')
    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'application/json'
    result = response.json()
    assert 'success' in result
    assert 'data' in result
    assert isinstance(result['data'], dict)
    required_fields = ['total_tasks', 'active_tasks', 'total_executions', 'successful_executions', 'failed_executions']
    for field in required_fields:
        assert field in result['data'], f'Lack of field: {field}'

# Node: make_request
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

def test_health_response_format(self):
    response = requests.get(f'{self.BASE_URL}/health')
    data = response.json()
    required_fields = ['status', 'timestamp', 'version']
    for field in required_fields:
        assert field in data, f'Response is missing required field: {field}'
    assert isinstance(data['status'], str)
    assert isinstance(data['timestamp'], str)
    assert isinstance(data['version'], str)

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

class TestEmailStatus:
    """Test cases for GET /api/v1/mail/status/{mail_id} endpoint."""

    def test_get_status_success(self):
        """Test successfully retrieving status of sent email."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        assert send_response.status_code == 200
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['mail_id'] == mail_id
        assert 'status' in data
        assert data['status'] in ['pending', 'sent', 'failed', 'delivered', 'bounced']
        assert 'to' in data
        assert 'subject' in data
        assert 'sent_at' in data
        assert 'delivered_at' in data
        assert 'error' in data
        if data['sent_at']:
            datetime.fromisoformat(data['sent_at'].replace('Z', '+00:00'))

    def test_get_status_nonexistent_mail_id(self):
        """Test retrieving status with non-existent mail_id returns 404."""
        fake_mail_id = 'nonexistent-mail-id-12345'
        response = requests.get(f'{STATUS_URL}/{fake_mail_id}')
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data

    def test_get_status_invalid_mail_id_format(self):
        """Test retrieving status with invalid mail_id format."""
        invalid_mail_id = 'invalid@#$%'
        response = requests.get(f'{STATUS_URL}/{invalid_mail_id}')
        assert response.status_code in [400, 404]
        data = response.json()
        assert 'error' in data

    def test_get_status_empty_mail_id(self):
        """Test retrieving status with empty mail_id."""
        response = requests.get(f'{STATUS_URL}/')
        assert response.status_code in [400, 404, 405]

    def test_get_status_pending_email(self):
        """Test status of newly sent email should be pending or sent."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Pending Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] in ['pending', 'sent']

    def test_get_status_fields_presence(self):
        """Test that all required fields are present in status response."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Field Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        required_fields = ['mail_id', 'status', 'to', 'subject', 'sent_at', 'delivered_at', 'error']
        for field in required_fields:
            assert field in data

    def test_get_status_to_field_format(self):
        """Test that 'to' field is returned as a list."""
        send_payload = {'to': ['user1@example.com', 'user2@example.com'], 'subject': 'Multi-recipient Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['to'], list)
        assert len(data['to']) == 2

    def test_get_status_error_field_null_on_success(self):
        """Test that error field is null when email is successful."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Success Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        if data['status'] not in ['failed', 'bounced']:
            assert data['error'] is None or data['error'] == ''

    def test_get_status_multiple_queries_same_email(self):
        """Test querying same email status multiple times."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Multiple Query Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        for _ in range(3):
            response = requests.get(f'{STATUS_URL}/{mail_id}')
            assert response.status_code == 200
            data = response.json()
            assert data['mail_id'] == mail_id

    def test_get_status_different_emails(self):
        """Test querying status of different emails."""
        mail_ids = []
        for i in range(3):
            send_payload = {'to': [f'user{i}@example.com'], 'subject': f'Email {i}', 'body': f'Body {i}'}
            send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
            mail_ids.append(send_response.json()['mail_id'])
        for i, mail_id in enumerate(mail_ids):
            response = requests.get(f'{STATUS_URL}/{mail_id}')
            assert response.status_code == 200
            data = response.json()
            assert data['mail_id'] == mail_id
            assert data['subject'] == f'Email {i}'

def test_get_status_to_field_format(self):
    """Test that 'to' field is returned as a list."""
    send_payload = {'to': ['user1@example.com', 'user2@example.com'], 'subject': 'Multi-recipient Test', 'body': 'Test body'}
    send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
    mail_id = send_response.json()['mail_id']
    response = requests.get(f'{STATUS_URL}/{mail_id}')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data['to'], list)
    assert len(data['to']) == 2

def test_languages_contains_common_languages():
    """Test that response contains common languages"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    languages = data['languages']
    assert isinstance(languages, dict), 'Languages should be a dictionary'
    assert len(languages) > 0, 'Languages dictionary should not be empty'
    common_lang_codes = ['en', 'zh-cn', 'es', 'fr', 'de']
    found_languages = [lang for lang in common_lang_codes if lang in languages]
    assert len(found_languages) >= 3, f'Should contain at least 3 common languages, found: {found_languages}'
    print(f'✓ Test passed: Contains common languages ({len(found_languages)} found)')

def test_languages_response_structure():
    """Test the overall response structure"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert 'success' in data, "Response should contain 'success' field"
    assert 'languages' in data, "Response should contain 'languages' field"
    assert isinstance(data['success'], bool), "'success' should be boolean"
    assert isinstance(data['languages'], dict), "'languages' should be a dictionary"
    print(f'✓ Test passed: Response structure is correct')

class TestPagination:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        for i in range(30):
            payload = {'name': f'Item {i + 1:02d}', 'category': f'Category {i % 3 + 1}', 'score': 50 + i * 1.5}
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_pagination_first_page(self):
        response = requests.get(API_ENDPOINT, params={'page': 1, 'page_size': 10})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 10
        assert data['data']['pagination']['page'] == 1
        assert data['data']['pagination']['page_size'] == 10
        assert data['data']['pagination']['total_items'] >= 30

    def test_pagination_middle_page(self):
        response = requests.get(API_ENDPOINT, params={'page': 2, 'page_size': 10})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['pagination']['page'] == 2
        assert len(data['data']['items']) <= 10

    def test_pagination_last_page(self):
        first_response = requests.get(API_ENDPOINT, params={'page': 1, 'page_size': 10})
        total_pages = first_response.json()['data']['pagination']['total_pages']
        response = requests.get(API_ENDPOINT, params={'page': total_pages, 'page_size': 10})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['pagination']['page'] == total_pages

    def test_pagination_different_page_sizes(self):
        page_sizes = [5, 10, 20, 50]
        for page_size in page_sizes:
            response = requests.get(API_ENDPOINT, params={'page': 1, 'page_size': page_size})
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert len(data['data']['items']) <= page_size
            assert data['data']['pagination']['page_size'] == page_size

    def test_pagination_boundary_conditions(self):
        response = requests.get(API_ENDPOINT, params={'page': 0, 'page_size': 10})
        assert response.status_code in [200, 400]
        response = requests.get(API_ENDPOINT, params={'page': 9999, 'page_size': 10})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['data']['items'], list)

def test_pagination_boundary_conditions(self):
    response = requests.get(API_ENDPOINT, params={'page': 0, 'page_size': 10})
    assert response.status_code in [200, 400]
    response = requests.get(API_ENDPOINT, params={'page': 9999, 'page_size': 10})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data['data']['items'], list)

@pytest.mark.edge
def test_sql_injection_in_search(api_base_url, auth_headers):
    """Test that SQL injection attempts in search are handled safely"""
    sql_injection_queries = ["'; DROP TABLE files; --", "1' OR '1'='1", "' UNION SELECT * FROM users --", "<script>alert('xss')</script>"]
    for query in sql_injection_queries:
        resp = requests.get(f'{api_base_url}/files/search', params={'q': query}, headers=auth_headers, timeout=10)
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data.get('files', []), list)

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

@pytest.mark.api
def test_list_files(api_base_url, auth_headers, uploaded_file):
    """Test listing files"""
    resp = requests.get(f'{api_base_url}/files', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert 'files' in data
    assert isinstance(data['files'], list)
    assert 'page' in data
    assert 'page_size' in data
    assert 'total' in data

@pytest.mark.api
def test_search_files(api_base_url, auth_headers, uploaded_file):
    """Test searching files"""
    resp = requests.get(f'{api_base_url}/files/search?q=test', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert 'files' in data
    assert isinstance(data['files'], list)
    assert 'query' in data or 'q' in data or data

class TestScoreSubmission:
    """Test score submission functionality."""

    @pytest.mark.smoke
    @pytest.mark.leaderboard
    def test_submit_score_success(self, api_base_url, sample_score_data):
        """Test successful score submission."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True
        assert 'player_rank' in data
        assert data['score'] == sample_score_data['score']
        assert isinstance(data['player_rank'], int)
        assert data['player_rank'] >= 1

    def test_submit_score_with_room_id(self, api_base_url, sample_score_data):
        """Test score submission with room_id."""
        score_data = sample_score_data.copy()
        score_data['room_id'] = '00000000-0000-0000-0000-000000000000'
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True

    def test_submit_score_invalid_data(self, api_base_url):
        """Test score submission with invalid data."""
        invalid_data = {'player_id': 'invalid-uuid', 'player_name': '', 'score': -100, 'game_type': 'invalid'}
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=invalid_data)
        assert_response_error(response, 400)

    def test_submit_score_missing_fields(self, api_base_url):
        """Test score submission with missing required fields."""
        incomplete_data = {'player_id': '00000000-0000-0000-0000-000000000000', 'score': 1000}
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=incomplete_data)
        assert_response_error(response, 400)

    def test_submit_score_boundary_values(self, api_base_url, sample_score_data):
        """Test score submission with boundary values."""
        min_score_data = sample_score_data.copy()
        min_score_data['score'] = 0
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=min_score_data)
        assert_response_success(response, 200)
        large_score_data = sample_score_data.copy()
        large_score_data['score'] = 999999
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=large_score_data)
        assert_response_success(response, 200)
        negative_score_data = sample_score_data.copy()
        negative_score_data['score'] = -1
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=negative_score_data)
        assert_response_error(response, 400)

    def test_submit_score_different_game_types(self, api_base_url, sample_score_data):
        """Test score submission for different game types."""
        game_types = ['battle', 'coop', 'puzzle']
        for game_type in game_types:
            score_data = sample_score_data.copy()
            score_data['game_type'] = game_type
            score_data['player_id'] = f'00000000-0000-0000-0000-00000000000{game_types.index(game_type)}'
            response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
            assert_response_success(response, 200)
            data = response.json()
            assert data['success'] is True

@pytest.mark.smoke
@pytest.mark.leaderboard
def test_submit_score_success(self, api_base_url, sample_score_data):
    """Test successful score submission."""
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True
    assert 'player_rank' in data
    assert data['score'] == sample_score_data['score']
    assert isinstance(data['player_rank'], int)
    assert data['player_rank'] >= 1

# Node: assert_response_success
def test_submit_score_with_room_id(self, api_base_url, sample_score_data):
    """Test score submission with room_id."""
    score_data = sample_score_data.copy()
    score_data['room_id'] = '00000000-0000-0000-0000-000000000000'
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True

def test_submit_score_invalid_data(self, api_base_url):
    """Test score submission with invalid data."""
    invalid_data = {'player_id': 'invalid-uuid', 'player_name': '', 'score': -100, 'game_type': 'invalid'}
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=invalid_data)
    assert_response_error(response, 400)

# Node: assert_response_error
def test_submit_score_missing_fields(self, api_base_url):
    """Test score submission with missing required fields."""
    incomplete_data = {'player_id': '00000000-0000-0000-0000-000000000000', 'score': 1000}
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=incomplete_data)
    assert_response_error(response, 400)

def test_submit_score_boundary_values(self, api_base_url, sample_score_data):
    """Test score submission with boundary values."""
    min_score_data = sample_score_data.copy()
    min_score_data['score'] = 0
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=min_score_data)
    assert_response_success(response, 200)
    large_score_data = sample_score_data.copy()
    large_score_data['score'] = 999999
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=large_score_data)
    assert_response_success(response, 200)
    negative_score_data = sample_score_data.copy()
    negative_score_data['score'] = -1
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=negative_score_data)
    assert_response_error(response, 400)

def test_submit_score_different_game_types(self, api_base_url, sample_score_data):
    """Test score submission for different game types."""
    game_types = ['battle', 'coop', 'puzzle']
    for game_type in game_types:
        score_data = sample_score_data.copy()
        score_data['game_type'] = game_type
        score_data['player_id'] = f'00000000-0000-0000-0000-00000000000{game_types.index(game_type)}'
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True

# Node: index
class TestLeaderboardRetrieval:
    """Test leaderboard retrieval functionality."""

    def test_get_leaderboard_success(self, api_base_url):
        """Test successful leaderboard retrieval."""
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        assert 'leaderboard' in data
        assert 'time_range' in data
        assert 'game_type' in data
        assert 'total_players' in data
        assert isinstance(data['leaderboard'], list)
        assert isinstance(data['total_players'], int)

    def test_get_leaderboard_with_filters(self, api_base_url):
        """Test leaderboard retrieval with filters."""
        response = make_request('GET', f'{api_base_url}/leaderboard?game_type=battle')
        assert_response_success(response, 200)
        data = response.json()
        assert data['game_type'] == 'battle'
        time_ranges = ['daily', 'weekly', 'monthly', 'all']
        for time_range in time_ranges:
            response = make_request('GET', f'{api_base_url}/leaderboard?time_range={time_range}')
            assert_response_success(response, 200)
            data = response.json()
            assert data['time_range'] == time_range
        response = make_request('GET', f'{api_base_url}/leaderboard?limit=10')
        assert_response_success(response, 200)
        data = response.json()
        assert len(data['leaderboard']) <= 10

    def test_get_leaderboard_invalid_filters(self, api_base_url):
        """Test leaderboard retrieval with invalid filters."""
        response = make_request('GET', f'{api_base_url}/leaderboard?game_type=invalid')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/leaderboard?time_range=invalid')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/leaderboard?limit=2000')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/leaderboard?limit=-1')
        assert_response_error(response, 400)

    def test_get_leaderboard_ranking_order(self, api_base_url, sample_leaderboard_data):
        """Test that leaderboard returns scores in correct ranking order."""
        for i, score_data in enumerate(sample_leaderboard_data):
            response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
            assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        leaderboard = data['leaderboard']
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]['score'] >= leaderboard[i + 1]['score']
        for i, entry in enumerate(leaderboard):
            assert entry['rank'] == i + 1

    def test_get_leaderboard_entry_structure(self, api_base_url, sample_score_data):
        """Test that leaderboard entries have correct structure."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        leaderboard = data['leaderboard']
        if leaderboard:
            entry = leaderboard[0]
            assert 'rank' in entry
            assert 'player_id' in entry
            assert 'player_name' in entry
            assert 'score' in entry
            assert 'game_type' in entry
            assert 'updated_at' in entry
            assert isinstance(entry['rank'], int)
            assert validate_uuid(entry['player_id'])
            assert isinstance(entry['player_name'], str)
            assert isinstance(entry['score'], int)
            assert entry['game_type'] in ['battle', 'coop', 'puzzle']
            assert validate_iso8601(entry['updated_at'])

def test_get_leaderboard_success(self, api_base_url):
    """Test successful leaderboard retrieval."""
    response = make_request('GET', f'{api_base_url}/leaderboard')
    assert_response_success(response, 200)
    data = response.json()
    assert 'leaderboard' in data
    assert 'time_range' in data
    assert 'game_type' in data
    assert 'total_players' in data
    assert isinstance(data['leaderboard'], list)
    assert isinstance(data['total_players'], int)

def test_get_leaderboard_with_filters(self, api_base_url):
    """Test leaderboard retrieval with filters."""
    response = make_request('GET', f'{api_base_url}/leaderboard?game_type=battle')
    assert_response_success(response, 200)
    data = response.json()
    assert data['game_type'] == 'battle'
    time_ranges = ['daily', 'weekly', 'monthly', 'all']
    for time_range in time_ranges:
        response = make_request('GET', f'{api_base_url}/leaderboard?time_range={time_range}')
        assert_response_success(response, 200)
        data = response.json()
        assert data['time_range'] == time_range
    response = make_request('GET', f'{api_base_url}/leaderboard?limit=10')
    assert_response_success(response, 200)
    data = response.json()
    assert len(data['leaderboard']) <= 10

def test_get_leaderboard_invalid_filters(self, api_base_url):
    """Test leaderboard retrieval with invalid filters."""
    response = make_request('GET', f'{api_base_url}/leaderboard?game_type=invalid')
    assert_response_error(response, 400)
    response = make_request('GET', f'{api_base_url}/leaderboard?time_range=invalid')
    assert_response_error(response, 400)
    response = make_request('GET', f'{api_base_url}/leaderboard?limit=2000')
    assert_response_error(response, 400)
    response = make_request('GET', f'{api_base_url}/leaderboard?limit=-1')
    assert_response_error(response, 400)

def test_get_leaderboard_entry_structure(self, api_base_url, sample_score_data):
    """Test that leaderboard entries have correct structure."""
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/leaderboard')
    assert_response_success(response, 200)
    data = response.json()
    leaderboard = data['leaderboard']
    if leaderboard:
        entry = leaderboard[0]
        assert 'rank' in entry
        assert 'player_id' in entry
        assert 'player_name' in entry
        assert 'score' in entry
        assert 'game_type' in entry
        assert 'updated_at' in entry
        assert isinstance(entry['rank'], int)
        assert validate_uuid(entry['player_id'])
        assert isinstance(entry['player_name'], str)
        assert isinstance(entry['score'], int)
        assert entry['game_type'] in ['battle', 'coop', 'puzzle']
        assert validate_iso8601(entry['updated_at'])

# Node: validate_uuid
# Node: validate_iso8601
class TestPlayerRanking:
    """Test individual player ranking functionality."""

    def test_get_player_rank_success(self, api_base_url, sample_score_data):
        """Test successful player rank retrieval."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard/player/{sample_score_data['player_id']}')
        assert_response_success(response, 200)
        data = response.json()
        assert data['player_id'] == sample_score_data['player_id']
        assert data['player_name'] == sample_score_data['player_name']
        assert 'rank' in data
        assert 'score' in data
        assert 'game_type' in data
        assert 'updated_at' in data
        assert isinstance(data['rank'], int)
        assert data['rank'] >= 1
        assert data['score'] == sample_score_data['score']
        assert validate_iso8601(data['updated_at'])

    def test_get_player_rank_with_game_type(self, api_base_url, sample_score_data):
        """Test player rank retrieval with game_type filter."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard/player/{sample_score_data['player_id']}?game_type={sample_score_data['game_type']}')
        assert_response_success(response, 200)
        data = response.json()
        assert data['game_type'] == sample_score_data['game_type']

    def test_get_player_rank_invalid_uuid(self, api_base_url):
        """Test getting rank with invalid UUID."""
        invalid_uuid = 'invalid-uuid'
        response = make_request('GET', f'{api_base_url}/leaderboard/player/{invalid_uuid}')
        assert_response_error(response, 400)

    def test_get_player_rank_invalid_game_type(self, api_base_url, sample_score_data):
        """Test getting player rank with invalid game_type filter."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard/player/{sample_score_data['player_id']}?game_type=invalid')
        assert_response_error(response, 400)

def test_get_player_rank_success(self, api_base_url, sample_score_data):
    """Test successful player rank retrieval."""
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/leaderboard/player/{sample_score_data['player_id']}')
    assert_response_success(response, 200)
    data = response.json()
    assert data['player_id'] == sample_score_data['player_id']
    assert data['player_name'] == sample_score_data['player_name']
    assert 'rank' in data
    assert 'score' in data
    assert 'game_type' in data
    assert 'updated_at' in data
    assert isinstance(data['rank'], int)
    assert data['rank'] >= 1
    assert data['score'] == sample_score_data['score']
    assert validate_iso8601(data['updated_at'])

def test_get_player_rank_with_game_type(self, api_base_url, sample_score_data):
    """Test player rank retrieval with game_type filter."""
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/leaderboard/player/{sample_score_data['player_id']}?game_type={sample_score_data['game_type']}')
    assert_response_success(response, 200)
    data = response.json()
    assert data['game_type'] == sample_score_data['game_type']

def test_get_player_rank_invalid_uuid(self, api_base_url):
    """Test getting rank with invalid UUID."""
    invalid_uuid = 'invalid-uuid'
    response = make_request('GET', f'{api_base_url}/leaderboard/player/{invalid_uuid}')
    assert_response_error(response, 400)

def test_get_player_rank_invalid_game_type(self, api_base_url, sample_score_data):
    """Test getting player rank with invalid game_type filter."""
    response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/leaderboard/player/{sample_score_data['player_id']}?game_type=invalid')
    assert_response_error(response, 400)

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

class TestGameStateUpdate:
    """Test game state update functionality."""

    @pytest.mark.smoke
    @pytest.mark.game_state
    def test_update_game_state_success(self, api_base_url, sample_game_state):
        """Test successful game state update."""
        response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True
        assert 'game_state' in data
        assert 'room_status' in data
        assert data['room_status'] in ['playing', 'finished']

    def test_update_game_state_with_next_player(self, api_base_url, sample_game_state):
        """Test game state update with next player specified."""
        game_state = sample_game_state.copy()
        game_state['action'] = 'end_turn'
        response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True
        if 'next_player' in data:
            assert validate_uuid(data['next_player'])

    def test_update_game_state_game_over(self, api_base_url, sample_game_state):
        """Test game state update with game over action."""
        game_state = sample_game_state.copy()
        game_state['action'] = 'game_over'
        response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True
        assert data['room_status'] == 'finished'

    def test_update_game_state_invalid_data(self, api_base_url):
        """Test game state update with invalid data."""
        invalid_data = {'room_id': 'invalid-uuid', 'player_id': 'invalid-uuid', 'game_state': 'invalid-state', 'action': 'invalid-action', 'timestamp': 'invalid-timestamp'}
        response = make_request('POST', f'{api_base_url}/game/state', json=invalid_data)
        assert_response_error(response, 400)

    def test_update_game_state_missing_fields(self, api_base_url):
        """Test game state update with missing required fields."""
        incomplete_data = {'room_id': '00000000-0000-0000-0000-000000000000', 'player_id': '00000000-0000-0000-0000-000000000000'}
        response = make_request('POST', f'{api_base_url}/game/state', json=incomplete_data)
        assert_response_error(response, 400)

    def test_update_game_state_invalid_action(self, api_base_url, sample_game_state):
        """Test game state update with invalid action."""
        game_state = sample_game_state.copy()
        game_state['action'] = 'invalid_action'
        response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
        assert_response_error(response, 400)

    def test_update_game_state_invalid_timestamp(self, api_base_url, sample_game_state):
        """Test game state update with invalid timestamp."""
        game_state = sample_game_state.copy()
        game_state['timestamp'] = 'invalid-timestamp'
        response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
        assert_response_error(response, 400)

    def test_update_game_state_different_actions(self, api_base_url, sample_game_state):
        """Test game state update with different valid actions."""
        valid_actions = ['move', 'attack', 'defend', 'end_turn', 'game_over']
        for action in valid_actions:
            game_state = sample_game_state.copy()
            game_state['action'] = action
            response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
            assert_response_success(response, 200)
            data = response.json()
            assert data['success'] is True

@pytest.mark.smoke
@pytest.mark.game_state
def test_update_game_state_success(self, api_base_url, sample_game_state):
    """Test successful game state update."""
    response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True
    assert 'game_state' in data
    assert 'room_status' in data
    assert data['room_status'] in ['playing', 'finished']

def test_update_game_state_with_next_player(self, api_base_url, sample_game_state):
    """Test game state update with next player specified."""
    game_state = sample_game_state.copy()
    game_state['action'] = 'end_turn'
    response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True
    if 'next_player' in data:
        assert validate_uuid(data['next_player'])

def test_update_game_state_game_over(self, api_base_url, sample_game_state):
    """Test game state update with game over action."""
    game_state = sample_game_state.copy()
    game_state['action'] = 'game_over'
    response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True
    assert data['room_status'] == 'finished'

def test_update_game_state_invalid_data(self, api_base_url):
    """Test game state update with invalid data."""
    invalid_data = {'room_id': 'invalid-uuid', 'player_id': 'invalid-uuid', 'game_state': 'invalid-state', 'action': 'invalid-action', 'timestamp': 'invalid-timestamp'}
    response = make_request('POST', f'{api_base_url}/game/state', json=invalid_data)
    assert_response_error(response, 400)

def test_update_game_state_missing_fields(self, api_base_url):
    """Test game state update with missing required fields."""
    incomplete_data = {'room_id': '00000000-0000-0000-0000-000000000000', 'player_id': '00000000-0000-0000-0000-000000000000'}
    response = make_request('POST', f'{api_base_url}/game/state', json=incomplete_data)
    assert_response_error(response, 400)

def test_update_game_state_invalid_action(self, api_base_url, sample_game_state):
    """Test game state update with invalid action."""
    game_state = sample_game_state.copy()
    game_state['action'] = 'invalid_action'
    response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
    assert_response_error(response, 400)

def test_update_game_state_invalid_timestamp(self, api_base_url, sample_game_state):
    """Test game state update with invalid timestamp."""
    game_state = sample_game_state.copy()
    game_state['timestamp'] = 'invalid-timestamp'
    response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
    assert_response_error(response, 400)

def test_update_game_state_different_actions(self, api_base_url, sample_game_state):
    """Test game state update with different valid actions."""
    valid_actions = ['move', 'attack', 'defend', 'end_turn', 'game_over']
    for action in valid_actions:
        game_state = sample_game_state.copy()
        game_state['action'] = action
        response = make_request('POST', f'{api_base_url}/game/state', json=game_state)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True

class TestGameStateRetrieval:
    """Test game state retrieval functionality."""

    def test_get_game_state_success(self, api_base_url, sample_game_state):
        """Test successful game state retrieval."""
        response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
        assert_response_success(response, 200)
        data = response.json()
        assert data['room_id'] == sample_game_state['room_id']
        assert 'game_state' in data
        assert 'current_player' in data
        assert 'status' in data
        assert 'last_updated' in data
        assert 'players' in data
        assert data['status'] in ['waiting', 'playing', 'finished']
        assert validate_uuid(data['current_player'])
        assert validate_iso8601(data['last_updated'])
        assert isinstance(data['players'], list)

    def test_get_game_state_nonexistent_room(self, api_base_url):
        """Test getting game state for non-existent room."""
        fake_room_id = '00000000-0000-0000-0000-000000000000'
        response = make_request('GET', f'{api_base_url}/game/state/{fake_room_id}')
        assert_response_error(response, 404)

    def test_get_game_state_invalid_uuid(self, api_base_url):
        """Test getting game state with invalid UUID."""
        invalid_uuid = 'invalid-uuid'
        response = make_request('GET', f'{api_base_url}/game/state/{invalid_uuid}')
        assert_response_error(response, 400)

    def test_get_game_state_structure(self, api_base_url, sample_game_state):
        """Test that retrieved game state has correct structure."""
        response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
        assert_response_success(response, 200)
        data = response.json()
        for player in data['players']:
            assert 'player_id' in player
            assert 'player_name' in player
            assert 'is_ready' in player
            assert validate_uuid(player['player_id'])
            assert isinstance(player['player_name'], str)
            assert isinstance(player['is_ready'], bool)

def test_get_game_state_success(self, api_base_url, sample_game_state):
    """Test successful game state retrieval."""
    response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
    assert_response_success(response, 200)
    data = response.json()
    assert data['room_id'] == sample_game_state['room_id']
    assert 'game_state' in data
    assert 'current_player' in data
    assert 'status' in data
    assert 'last_updated' in data
    assert 'players' in data
    assert data['status'] in ['waiting', 'playing', 'finished']
    assert validate_uuid(data['current_player'])
    assert validate_iso8601(data['last_updated'])
    assert isinstance(data['players'], list)

def test_get_game_state_nonexistent_room(self, api_base_url):
    """Test getting game state for non-existent room."""
    fake_room_id = '00000000-0000-0000-0000-000000000000'
    response = make_request('GET', f'{api_base_url}/game/state/{fake_room_id}')
    assert_response_error(response, 404)

def test_get_game_state_invalid_uuid(self, api_base_url):
    """Test getting game state with invalid UUID."""
    invalid_uuid = 'invalid-uuid'
    response = make_request('GET', f'{api_base_url}/game/state/{invalid_uuid}')
    assert_response_error(response, 400)

def test_get_game_state_structure(self, api_base_url, sample_game_state):
    """Test that retrieved game state has correct structure."""
    response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
    assert_response_success(response, 200)
    data = response.json()
    for player in data['players']:
        assert 'player_id' in player
        assert 'player_name' in player
        assert 'is_ready' in player
        assert validate_uuid(player['player_id'])
        assert isinstance(player['player_name'], str)
        assert isinstance(player['is_ready'], bool)

class TestPlayerReadyState:
    """Test player ready state functionality."""

    def test_set_player_ready_invalid_data(self, api_base_url):
        """Test setting player ready with invalid data."""
        invalid_data = {'room_id': 'invalid-uuid', 'player_id': 'invalid-uuid', 'is_ready': 'invalid-boolean'}
        response = make_request('POST', f'{api_base_url}/game/ready', json=invalid_data)
        assert_response_error(response, 400)

    def test_set_player_ready_missing_fields(self, api_base_url):
        """Test setting player ready with missing required fields."""
        incomplete_data = {'room_id': '00000000-0000-0000-0000-000000000000'}
        response = make_request('POST', f'{api_base_url}/game/ready', json=incomplete_data)
        assert_response_error(response, 400)

    def test_set_player_ready_nonexistent_room(self, api_base_url, sample_game_state):
        """Test setting player ready for non-existent room."""
        fake_room_id = '00000000-0000-0000-0000-000000000000'
        ready_data = {'room_id': fake_room_id, 'player_id': sample_game_state['player_id'], 'is_ready': True}
        response = make_request('POST', f'{api_base_url}/game/ready', json=ready_data)
        assert_response_error(response, 404)

    def test_set_player_ready_nonexistent_player(self, api_base_url, sample_game_state):
        """Test setting ready for non-existent player."""
        fake_player_id = '00000000-0000-0000-0000-000000000000'
        ready_data = {'room_id': sample_game_state['room_id'], 'player_id': fake_player_id, 'is_ready': True}
        response = make_request('POST', f'{api_base_url}/game/ready', json=ready_data)
        assert_response_error(response, 404)

def test_set_player_ready_invalid_data(self, api_base_url):
    """Test setting player ready with invalid data."""
    invalid_data = {'room_id': 'invalid-uuid', 'player_id': 'invalid-uuid', 'is_ready': 'invalid-boolean'}
    response = make_request('POST', f'{api_base_url}/game/ready', json=invalid_data)
    assert_response_error(response, 400)

def test_set_player_ready_missing_fields(self, api_base_url):
    """Test setting player ready with missing required fields."""
    incomplete_data = {'room_id': '00000000-0000-0000-0000-000000000000'}
    response = make_request('POST', f'{api_base_url}/game/ready', json=incomplete_data)
    assert_response_error(response, 400)

def test_set_player_ready_nonexistent_room(self, api_base_url, sample_game_state):
    """Test setting player ready for non-existent room."""
    fake_room_id = '00000000-0000-0000-0000-000000000000'
    ready_data = {'room_id': fake_room_id, 'player_id': sample_game_state['player_id'], 'is_ready': True}
    response = make_request('POST', f'{api_base_url}/game/ready', json=ready_data)
    assert_response_error(response, 404)

def test_set_player_ready_nonexistent_player(self, api_base_url, sample_game_state):
    """Test setting ready for non-existent player."""
    fake_player_id = '00000000-0000-0000-0000-000000000000'
    ready_data = {'room_id': sample_game_state['room_id'], 'player_id': fake_player_id, 'is_ready': True}
    response = make_request('POST', f'{api_base_url}/game/ready', json=ready_data)
    assert_response_error(response, 404)

class TestGameStateIntegration:
    """Integration tests for game state functionality."""

    @pytest.mark.integration
    @pytest.mark.game_state
    def test_game_state_consistency(self, api_base_url, sample_game_state):
        """Test that game state updates are consistent."""
        response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
        assert_response_success(response, 200)
        retrieved_data = response.json()
        assert retrieved_data['room_id'] == sample_game_state['room_id']
        assert retrieved_data['status'] in ['waiting', 'playing', 'finished']

    def test_multiple_state_updates(self, api_base_url, sample_game_state):
        """Test multiple game state updates."""
        response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
        assert_response_success(response, 200)
        updated_state = sample_game_state.copy()
        updated_state['action'] = 'end_turn'
        updated_state['game_state']['turn'] = 2
        response = make_request('POST', f'{api_base_url}/game/state', json=updated_state)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
        assert_response_success(response, 200)
        data = response.json()
        assert data['room_id'] == sample_game_state['room_id']

    def test_game_state_with_complex_data(self, api_base_url, sample_game_state):
        """Test game state with complex nested data."""
        complex_state = sample_game_state.copy()
        complex_state['game_state'] = {'board': [[{'type': 'empty', 'value': 0}, {'type': 'player', 'value': 1}], [{'type': 'obstacle', 'value': -1}, {'type': 'empty', 'value': 0}]], 'players': [{'id': 'player1', 'position': [0, 1], 'health': 100}, {'id': 'player2', 'position': [1, 0], 'health': 80}], 'turn': 5, 'phase': 'combat', 'settings': {'time_limit': 30, 'difficulty': 'hard'}}
        response = make_request('POST', f'{api_base_url}/game/state', json=complex_state)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
        assert_response_success(response, 200)
        data = response.json()
        assert 'game_state' in data
        assert isinstance(data['game_state'], dict)

@pytest.mark.integration
@pytest.mark.game_state
def test_game_state_consistency(self, api_base_url, sample_game_state):
    """Test that game state updates are consistent."""
    response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
    assert_response_success(response, 200)
    retrieved_data = response.json()
    assert retrieved_data['room_id'] == sample_game_state['room_id']
    assert retrieved_data['status'] in ['waiting', 'playing', 'finished']

def test_multiple_state_updates(self, api_base_url, sample_game_state):
    """Test multiple game state updates."""
    response = make_request('POST', f'{api_base_url}/game/state', json=sample_game_state)
    assert_response_success(response, 200)
    updated_state = sample_game_state.copy()
    updated_state['action'] = 'end_turn'
    updated_state['game_state']['turn'] = 2
    response = make_request('POST', f'{api_base_url}/game/state', json=updated_state)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
    assert_response_success(response, 200)
    data = response.json()
    assert data['room_id'] == sample_game_state['room_id']

def test_game_state_with_complex_data(self, api_base_url, sample_game_state):
    """Test game state with complex nested data."""
    complex_state = sample_game_state.copy()
    complex_state['game_state'] = {'board': [[{'type': 'empty', 'value': 0}, {'type': 'player', 'value': 1}], [{'type': 'obstacle', 'value': -1}, {'type': 'empty', 'value': 0}]], 'players': [{'id': 'player1', 'position': [0, 1], 'health': 100}, {'id': 'player2', 'position': [1, 0], 'health': 80}], 'turn': 5, 'phase': 'combat', 'settings': {'time_limit': 30, 'difficulty': 'hard'}}
    response = make_request('POST', f'{api_base_url}/game/state', json=complex_state)
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/game/state/{sample_game_state['room_id']}')
    assert_response_success(response, 200)
    data = response.json()
    assert 'game_state' in data
    assert isinstance(data['game_state'], dict)

class TestRoomCreation:
    """Test room creation functionality."""

    @pytest.mark.smoke
    @pytest.mark.room_matching
    def test_create_room_success(self, api_base_url, sample_room_data):
        """Test successful room creation."""
        response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_data)
        assert_response_success(response, 201)
        data = response.json()
        assert 'room_id' in data
        assert validate_uuid(data['room_id'])
        assert data['room_name'] == sample_room_data['room_name']
        assert data['max_players'] == sample_room_data['max_players']
        assert data['current_players'] == 1
        assert data['game_type'] == sample_room_data['game_type']
        assert data['status'] == 'waiting'
        assert 'created_at' in data
        assert validate_iso8601(data['created_at'])
        assert 'creator_id' in data
        assert validate_uuid(data['creator_id'])

    def test_create_room_with_password(self, api_base_url, sample_room_with_password):
        """Test room creation with password."""
        response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_with_password)
        assert_response_success(response, 201)
        data = response.json()
        assert data['room_name'] == sample_room_with_password['room_name']
        assert data['max_players'] == sample_room_with_password['max_players']
        assert data['game_type'] == sample_room_with_password['game_type']

    def test_create_room_invalid_data(self, api_base_url):
        """Test room creation with invalid data."""
        invalid_data = {'room_name': '', 'max_players': 1, 'game_type': 'invalid'}
        response = make_request('POST', f'{api_base_url}/rooms', json=invalid_data)
        assert_response_error(response, 400)

    def test_create_room_missing_fields(self, api_base_url):
        """Test room creation with missing required fields."""
        incomplete_data = {'room_name': 'Test Room'}
        response = make_request('POST', f'{api_base_url}/rooms', json=incomplete_data)
        assert_response_error(response, 400)

    def test_create_room_max_players_boundary(self, api_base_url):
        """Test room creation with boundary values for max_players."""
        min_data = {'room_name': 'Min Room', 'max_players': 2, 'game_type': 'battle'}
        response = make_request('POST', f'{api_base_url}/rooms', json=min_data)
        assert_response_success(response, 201)
        max_data = {'room_name': 'Max Room', 'max_players': 8, 'game_type': 'battle'}
        response = make_request('POST', f'{api_base_url}/rooms', json=max_data)
        assert_response_success(response, 201)
        invalid_min = {'room_name': 'Invalid Min', 'max_players': 1, 'game_type': 'battle'}
        response = make_request('POST', f'{api_base_url}/rooms', json=invalid_min)
        assert_response_error(response, 400)
        invalid_max = {'room_name': 'Invalid Max', 'max_players': 9, 'game_type': 'battle'}
        response = make_request('POST', f'{api_base_url}/rooms', json=invalid_max)
        assert_response_error(response, 400)

@pytest.mark.smoke
@pytest.mark.room_matching
def test_create_room_success(self, api_base_url, sample_room_data):
    """Test successful room creation."""
    response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_data)
    assert_response_success(response, 201)
    data = response.json()
    assert 'room_id' in data
    assert validate_uuid(data['room_id'])
    assert data['room_name'] == sample_room_data['room_name']
    assert data['max_players'] == sample_room_data['max_players']
    assert data['current_players'] == 1
    assert data['game_type'] == sample_room_data['game_type']
    assert data['status'] == 'waiting'
    assert 'created_at' in data
    assert validate_iso8601(data['created_at'])
    assert 'creator_id' in data
    assert validate_uuid(data['creator_id'])

def test_create_room_with_password(self, api_base_url, sample_room_with_password):
    """Test room creation with password."""
    response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_with_password)
    assert_response_success(response, 201)
    data = response.json()
    assert data['room_name'] == sample_room_with_password['room_name']
    assert data['max_players'] == sample_room_with_password['max_players']
    assert data['game_type'] == sample_room_with_password['game_type']

def test_create_room_invalid_data(self, api_base_url):
    """Test room creation with invalid data."""
    invalid_data = {'room_name': '', 'max_players': 1, 'game_type': 'invalid'}
    response = make_request('POST', f'{api_base_url}/rooms', json=invalid_data)
    assert_response_error(response, 400)

def test_create_room_missing_fields(self, api_base_url):
    """Test room creation with missing required fields."""
    incomplete_data = {'room_name': 'Test Room'}
    response = make_request('POST', f'{api_base_url}/rooms', json=incomplete_data)
    assert_response_error(response, 400)

def test_create_room_max_players_boundary(self, api_base_url):
    """Test room creation with boundary values for max_players."""
    min_data = {'room_name': 'Min Room', 'max_players': 2, 'game_type': 'battle'}
    response = make_request('POST', f'{api_base_url}/rooms', json=min_data)
    assert_response_success(response, 201)
    max_data = {'room_name': 'Max Room', 'max_players': 8, 'game_type': 'battle'}
    response = make_request('POST', f'{api_base_url}/rooms', json=max_data)
    assert_response_success(response, 201)
    invalid_min = {'room_name': 'Invalid Min', 'max_players': 1, 'game_type': 'battle'}
    response = make_request('POST', f'{api_base_url}/rooms', json=invalid_min)
    assert_response_error(response, 400)
    invalid_max = {'room_name': 'Invalid Max', 'max_players': 9, 'game_type': 'battle'}
    response = make_request('POST', f'{api_base_url}/rooms', json=invalid_max)
    assert_response_error(response, 400)

class TestRoomJoining:
    """Test room joining functionality."""

    @pytest.mark.smoke
    @pytest.mark.room_matching
    def test_join_room_success(self, api_base_url, created_room, sample_player_data):
        """Test successful room joining."""
        if not created_room:
            pytest.skip('No room created for testing')
        join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
        response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True
        assert 'room_info' in data
        room_info = data['room_info']
        assert room_info['room_id'] == created_room['room_id']
        assert room_info['current_players'] == 2
        assert len(room_info['players']) == 2
        player_ids = [p['player_id'] for p in room_info['players']]
        assert sample_player_data['player_id'] in player_ids

    def test_join_room_with_password(self, api_base_url, sample_room_with_password, sample_player_data):
        """Test joining room with correct password."""
        room_response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_with_password)
        assert_response_success(room_response, 201)
        room_data = room_response.json()
        join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name'], 'password': sample_room_with_password['password']}
        response = make_request('POST', f'{api_base_url}/rooms/{room_data['room_id']}/join', json=join_data)
        assert_response_success(response, 200)

    def test_join_room_wrong_password(self, api_base_url, sample_room_with_password, sample_player_data):
        """Test joining room with wrong password."""
        room_response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_with_password)
        assert_response_success(room_response, 201)
        room_data = room_response.json()
        join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name'], 'password': 'wrongpassword'}
        response = make_request('POST', f'{api_base_url}/rooms/{room_data['room_id']}/join', json=join_data)
        assert_response_error(response, 403)

    def test_join_nonexistent_room(self, api_base_url, sample_player_data):
        """Test joining non-existent room."""
        fake_room_id = '00000000-0000-0000-0000-000000000000'
        join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
        response = make_request('POST', f'{api_base_url}/rooms/{fake_room_id}/join', json=join_data)
        assert_response_error(response, 404)

    @pytest.mark.integration
    @pytest.mark.room_matching
    def test_join_full_room(self, api_base_url, sample_room_data, multiple_players):
        """Test joining a full room."""
        room_data = {'room_name': 'Full Room', 'max_players': 2, 'game_type': 'battle'}
        room_response = make_request('POST', f'{api_base_url}/rooms', json=room_data)
        assert_response_success(room_response, 201)
        room = room_response.json()
        join_data = {'player_id': multiple_players[0]['player_id'], 'player_name': multiple_players[0]['player_name']}
        response = make_request('POST', f'{api_base_url}/rooms/{room['room_id']}/join', json=join_data)
        assert_response_success(response, 200)
        join_data = {'player_id': multiple_players[1]['player_id'], 'player_name': multiple_players[1]['player_name']}
        response = make_request('POST', f'{api_base_url}/rooms/{room['room_id']}/join', json=join_data)
        assert_response_error(response, 409)

    def test_join_room_already_joined(self, api_base_url, created_room, sample_player_data):
        """Test joining room when already joined."""
        if not created_room:
            pytest.skip('No room created for testing')
        join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
        response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
        assert_response_success(response, 200)
        response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
        assert_response_error(response, 409)

@pytest.mark.smoke
@pytest.mark.room_matching
def test_join_room_success(self, api_base_url, created_room, sample_player_data):
    """Test successful room joining."""
    if not created_room:
        pytest.skip('No room created for testing')
    join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
    response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True
    assert 'room_info' in data
    room_info = data['room_info']
    assert room_info['room_id'] == created_room['room_id']
    assert room_info['current_players'] == 2
    assert len(room_info['players']) == 2
    player_ids = [p['player_id'] for p in room_info['players']]
    assert sample_player_data['player_id'] in player_ids

def test_join_room_with_password(self, api_base_url, sample_room_with_password, sample_player_data):
    """Test joining room with correct password."""
    room_response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_with_password)
    assert_response_success(room_response, 201)
    room_data = room_response.json()
    join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name'], 'password': sample_room_with_password['password']}
    response = make_request('POST', f'{api_base_url}/rooms/{room_data['room_id']}/join', json=join_data)
    assert_response_success(response, 200)

def test_join_room_wrong_password(self, api_base_url, sample_room_with_password, sample_player_data):
    """Test joining room with wrong password."""
    room_response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_with_password)
    assert_response_success(room_response, 201)
    room_data = room_response.json()
    join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name'], 'password': 'wrongpassword'}
    response = make_request('POST', f'{api_base_url}/rooms/{room_data['room_id']}/join', json=join_data)
    assert_response_error(response, 403)

def test_join_nonexistent_room(self, api_base_url, sample_player_data):
    """Test joining non-existent room."""
    fake_room_id = '00000000-0000-0000-0000-000000000000'
    join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
    response = make_request('POST', f'{api_base_url}/rooms/{fake_room_id}/join', json=join_data)
    assert_response_error(response, 404)

@pytest.mark.integration
@pytest.mark.room_matching
def test_join_full_room(self, api_base_url, sample_room_data, multiple_players):
    """Test joining a full room."""
    room_data = {'room_name': 'Full Room', 'max_players': 2, 'game_type': 'battle'}
    room_response = make_request('POST', f'{api_base_url}/rooms', json=room_data)
    assert_response_success(room_response, 201)
    room = room_response.json()
    join_data = {'player_id': multiple_players[0]['player_id'], 'player_name': multiple_players[0]['player_name']}
    response = make_request('POST', f'{api_base_url}/rooms/{room['room_id']}/join', json=join_data)
    assert_response_success(response, 200)
    join_data = {'player_id': multiple_players[1]['player_id'], 'player_name': multiple_players[1]['player_name']}
    response = make_request('POST', f'{api_base_url}/rooms/{room['room_id']}/join', json=join_data)
    assert_response_error(response, 409)

def test_join_room_already_joined(self, api_base_url, created_room, sample_player_data):
    """Test joining room when already joined."""
    if not created_room:
        pytest.skip('No room created for testing')
    join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
    response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
    assert_response_success(response, 200)
    response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
    assert_response_error(response, 409)

class TestRoomListing:
    """Test room listing functionality."""

    def test_get_rooms_success(self, api_base_url):
        """Test successful room listing."""
        response = make_request('GET', f'{api_base_url}/rooms')
        assert_response_success(response, 200)
        data = response.json()
        assert 'rooms' in data
        assert 'pagination' in data
        assert isinstance(data['rooms'], list)
        pagination = data['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total' in pagination
        assert 'total_pages' in pagination

    def test_get_rooms_with_filters(self, api_base_url):
        """Test room listing with filters."""
        response = make_request('GET', f'{api_base_url}/rooms?game_type=battle')
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/rooms?status=waiting')
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/rooms?page=1&limit=5')
        assert_response_success(response, 200)
        data = response.json()
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 5

    def test_get_rooms_invalid_filters(self, api_base_url):
        """Test room listing with invalid filters."""
        response = make_request('GET', f'{api_base_url}/rooms?game_type=invalid')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/rooms?status=invalid')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/rooms?page=0')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/rooms?limit=0')
        assert_response_error(response, 400)

def test_get_rooms_success(self, api_base_url):
    """Test successful room listing."""
    response = make_request('GET', f'{api_base_url}/rooms')
    assert_response_success(response, 200)
    data = response.json()
    assert 'rooms' in data
    assert 'pagination' in data
    assert isinstance(data['rooms'], list)
    pagination = data['pagination']
    assert 'page' in pagination
    assert 'limit' in pagination
    assert 'total' in pagination
    assert 'total_pages' in pagination

def test_get_rooms_with_filters(self, api_base_url):
    """Test room listing with filters."""
    response = make_request('GET', f'{api_base_url}/rooms?game_type=battle')
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/rooms?status=waiting')
    assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/rooms?page=1&limit=5')
    assert_response_success(response, 200)
    data = response.json()
    assert data['pagination']['page'] == 1
    assert data['pagination']['limit'] == 5

def test_get_rooms_invalid_filters(self, api_base_url):
    """Test room listing with invalid filters."""
    response = make_request('GET', f'{api_base_url}/rooms?game_type=invalid')
    assert_response_error(response, 400)
    response = make_request('GET', f'{api_base_url}/rooms?status=invalid')
    assert_response_error(response, 400)
    response = make_request('GET', f'{api_base_url}/rooms?page=0')
    assert_response_error(response, 400)
    response = make_request('GET', f'{api_base_url}/rooms?limit=0')
    assert_response_error(response, 400)

class TestRoomLeaving:
    """Test room leaving functionality."""

    def test_leave_room_success(self, api_base_url, joined_room):
        """Test successful room leaving."""
        if not joined_room:
            pytest.skip('No joined room for testing')
        leave_data = {'player_id': joined_room['player']['player_id']}
        response = make_request('POST', f'{api_base_url}/rooms/{joined_room['room']['room_id']}/leave', json=leave_data)
        assert_response_success(response, 200)
        data = response.json()
        assert data['success'] is True

    def test_leave_nonexistent_room(self, api_base_url, sample_player_data):
        """Test leaving non-existent room."""
        fake_room_id = '00000000-0000-0000-0000-000000000000'
        leave_data = {'player_id': sample_player_data['player_id']}
        response = make_request('POST', f'{api_base_url}/rooms/{fake_room_id}/leave', json=leave_data)
        assert_response_error(response, 404)

    def test_leave_room_not_joined(self, api_base_url, created_room, sample_player_data):
        """Test leaving room when not joined."""
        if not created_room:
            pytest.skip('No room created for testing')
        leave_data = {'player_id': sample_player_data['player_id']}
        response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/leave', json=leave_data)
        assert_response_error(response, 404)

    def test_leave_room_missing_player_id(self, api_base_url, created_room):
        """Test leaving room with missing player_id."""
        if not created_room:
            pytest.skip('No room created for testing')
        leave_data = {}
        response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/leave', json=leave_data)
        assert_response_error(response, 400)

def test_leave_room_success(self, api_base_url, joined_room):
    """Test successful room leaving."""
    if not joined_room:
        pytest.skip('No joined room for testing')
    leave_data = {'player_id': joined_room['player']['player_id']}
    response = make_request('POST', f'{api_base_url}/rooms/{joined_room['room']['room_id']}/leave', json=leave_data)
    assert_response_success(response, 200)
    data = response.json()
    assert data['success'] is True

def test_leave_nonexistent_room(self, api_base_url, sample_player_data):
    """Test leaving non-existent room."""
    fake_room_id = '00000000-0000-0000-0000-000000000000'
    leave_data = {'player_id': sample_player_data['player_id']}
    response = make_request('POST', f'{api_base_url}/rooms/{fake_room_id}/leave', json=leave_data)
    assert_response_error(response, 404)

def test_leave_room_not_joined(self, api_base_url, created_room, sample_player_data):
    """Test leaving room when not joined."""
    if not created_room:
        pytest.skip('No room created for testing')
    leave_data = {'player_id': sample_player_data['player_id']}
    response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/leave', json=leave_data)
    assert_response_error(response, 404)

def test_leave_room_missing_player_id(self, api_base_url, created_room):
    """Test leaving room with missing player_id."""
    if not created_room:
        pytest.skip('No room created for testing')
    leave_data = {}
    response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/leave', json=leave_data)
    assert_response_error(response, 400)

@pytest.fixture
def created_room(api_base_url, sample_room_data):
    """Create a room for testing and return room data."""
    try:
        response = make_request('POST', f'{api_base_url}/rooms', json=sample_room_data)
        if response.status_code == 201:
            return response.json()
    except Exception:
        pass
    return None

@pytest.fixture
def joined_room(api_base_url, created_room, sample_player_data):
    """Create a room and join it with a player."""
    if not created_room:
        return None
    try:
        join_data = {'player_id': sample_player_data['player_id'], 'player_name': sample_player_data['player_name']}
        response = make_request('POST', f'{api_base_url}/rooms/{created_room['room_id']}/join', json=join_data)
        if response.status_code == 200:
            return {'room': created_room, 'player': sample_player_data, 'join_response': response.json()}
    except Exception:
        pass
    return None

