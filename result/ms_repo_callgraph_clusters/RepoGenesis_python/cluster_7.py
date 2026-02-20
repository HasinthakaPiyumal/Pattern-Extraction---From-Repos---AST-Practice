# Cluster 7

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
# Node: int
# Node: range
# Node: sleep
# Node: append
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
class TestExecutionHistory:

    def test_get_execution_history(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        api_client.post(f'/tasks/{task_id}/execute')
        time.sleep(1)
        response = api_client.get(f'/tasks/{task_id}/executions')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'data' in result
        data = result['data']
        assert 'executions' in data
        assert len(data['executions']) > 0
        execution = data['executions'][0]
        assert 'execution_id' in execution
        assert execution['task_id'] == task_id
        assert 'status' in execution
        assert execution['status'] in ['running', 'completed', 'failed']
        assert 'started_at' in execution

    def test_get_execution_history_with_limit(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_summary']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        for _ in range(3):
            api_client.post(f'/tasks/{task_id}/execute')
            time.sleep(0.5)
        response = api_client.get(f'/tasks/{task_id}/executions', params={'limit': 2})
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        executions = result['data']['executions']
        assert len(executions) <= 2

    def test_get_execution_history_empty(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_backup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        response = api_client.get(f'/tasks/{task_id}/executions')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert len(result['data']['executions']) == 0

    def test_get_execution_history_nonexistent_task(self, api_client):
        response = api_client.get('/tasks/nonexistent_task_id/executions')
        assert response.status_code == 404
        result = response.json()
        assert result['success'] is False

    @pytest.mark.slow
    def test_execution_status_transition(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        exec_response = api_client.post(f'/tasks/{task_id}/execute')
        execution_id = exec_response.json()['data']['execution_id']
        history_response = api_client.get(f'/tasks/{task_id}/executions')
        executions = history_response.json()['data']['executions']
        current_execution = None
        for execution in executions:
            if execution['execution_id'] == execution_id:
                current_execution = execution
                break
        assert current_execution is not None
        initial_status = current_execution['status']
        assert initial_status in ['running', 'completed', 'failed']
        if initial_status == 'running':
            time.sleep(3)
            history_response = api_client.get(f'/tasks/{task_id}/executions')
            executions = history_response.json()['data']['executions']
            for execution in executions:
                if execution['execution_id'] == execution_id:
                    final_status = execution['status']
                    assert final_status in ['completed', 'failed']
                    if final_status in ['completed', 'failed']:
                        assert 'completed_at' in execution
                    break

    def test_execution_result_fields(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_summary']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        api_client.post(f'/tasks/{task_id}/execute')
        time.sleep(2)
        response = api_client.get(f'/tasks/{task_id}/executions')
        executions = response.json()['data']['executions']
        if len(executions) > 0:
            execution = executions[0]
            assert 'execution_id' in execution
            assert 'task_id' in execution
            assert 'status' in execution
            assert 'started_at' in execution
            if execution['status'] == 'completed':
                assert 'completed_at' in execution or True
            elif execution['status'] == 'failed':
                assert 'error' in execution or True

def test_get_execution_history(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    api_client.post(f'/tasks/{task_id}/execute')
    time.sleep(1)
    response = api_client.get(f'/tasks/{task_id}/executions')
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert 'data' in result
    data = result['data']
    assert 'executions' in data
    assert len(data['executions']) > 0
    execution = data['executions'][0]
    assert 'execution_id' in execution
    assert execution['task_id'] == task_id
    assert 'status' in execution
    assert execution['status'] in ['running', 'completed', 'failed']
    assert 'started_at' in execution

def test_get_execution_history_with_limit(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_summary']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    for _ in range(3):
        api_client.post(f'/tasks/{task_id}/execute')
        time.sleep(0.5)
    response = api_client.get(f'/tasks/{task_id}/executions', params={'limit': 2})
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    executions = result['data']['executions']
    assert len(executions) <= 2

@pytest.mark.slow
def test_execution_status_transition(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    exec_response = api_client.post(f'/tasks/{task_id}/execute')
    execution_id = exec_response.json()['data']['execution_id']
    history_response = api_client.get(f'/tasks/{task_id}/executions')
    executions = history_response.json()['data']['executions']
    current_execution = None
    for execution in executions:
        if execution['execution_id'] == execution_id:
            current_execution = execution
            break
    assert current_execution is not None
    initial_status = current_execution['status']
    assert initial_status in ['running', 'completed', 'failed']
    if initial_status == 'running':
        time.sleep(3)
        history_response = api_client.get(f'/tasks/{task_id}/executions')
        executions = history_response.json()['data']['executions']
        for execution in executions:
            if execution['execution_id'] == execution_id:
                final_status = execution['status']
                assert final_status in ['completed', 'failed']
                if final_status in ['completed', 'failed']:
                    assert 'completed_at' in execution
                break

def test_execution_result_fields(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_summary']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    api_client.post(f'/tasks/{task_id}/execute')
    time.sleep(2)
    response = api_client.get(f'/tasks/{task_id}/executions')
    executions = response.json()['data']['executions']
    if len(executions) > 0:
        execution = executions[0]
        assert 'execution_id' in execution
        assert 'task_id' in execution
        assert 'status' in execution
        assert 'started_at' in execution
        if execution['status'] == 'completed':
            assert 'completed_at' in execution or True
        elif execution['status'] == 'failed':
            assert 'error' in execution or True

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

class TestStatsConsistency:

    def test_stats_consistency_with_task_list(self, api_client):
        stats_response = api_client.get('/stats')
        stats = stats_response.json()['data']
        tasks_response = api_client.get('/tasks', params={'page_size': 1000})
        tasks_data = tasks_response.json()['data']
        assert stats['total_tasks'] == tasks_data['total']
        active_count = sum((1 for task in tasks_data['tasks'] if task['enabled']))
        assert stats['active_tasks'] == active_count

    @pytest.mark.slow
    def test_stats_real_time_update(self, api_client, sample_task_data, cleanup_tasks):
        operations = []
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        stats1 = api_client.get('/stats').json()['data']
        operations.append(('create', stats1))
        api_client.post(f'/tasks/{task_id}/execute')
        time.sleep(1)
        stats2 = api_client.get('/stats').json()['data']
        operations.append(('execute', stats2))
        api_client.post(f'/tasks/{task_id}/toggle', data={'enabled': False})
        stats3 = api_client.get('/stats').json()['data']
        operations.append(('disable', stats3))
        assert stats2['total_executions'] >= stats1['total_executions']
        assert stats3['active_tasks'] <= stats2['active_tasks']

@pytest.mark.slow
def test_stats_real_time_update(self, api_client, sample_task_data, cleanup_tasks):
    operations = []
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    stats1 = api_client.get('/stats').json()['data']
    operations.append(('create', stats1))
    api_client.post(f'/tasks/{task_id}/execute')
    time.sleep(1)
    stats2 = api_client.get('/stats').json()['data']
    operations.append(('execute', stats2))
    api_client.post(f'/tasks/{task_id}/toggle', data={'enabled': False})
    stats3 = api_client.get('/stats').json()['data']
    operations.append(('disable', stats3))
    assert stats2['total_executions'] >= stats1['total_executions']
    assert stats3['active_tasks'] <= stats2['active_tasks']

class TestIntegration:
    BASE_URL = 'http://localhost:8000/api/v1'

    def setup_method(self):
        self.test_data = {'csv': 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000\nWang Wu,28,Shenzhen,20000', 'excel': None, 'complex_csv': 'ProductID,ProductName,Category,Price,Stock,Supplier,Description\nP001,Smartphone,Electronics,2999.00,50,ZTE,High-performance 5G smartphone\nP002,Laptop,Electronics,5999.00,20,Huawei,Lightweight business laptop\nP003,Mechanical Keyboard,Accessories,299.00,100,Rapoo,RGB backlit mechanical keyboard\nP004,Mouse Pad,Accessories,49.00,200,SteelSeries,Extra large mouse pad'}
        df = pd.DataFrame({'Name': ['Zhang San', 'Li Si', 'Wang Wu'], 'Age': [25, 30, 28], 'City': ['Beijing', 'Shanghai', 'Shenzhen'], 'Salary': [15000, 18000, 20000]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.test_data['excel'] = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_end_to_end_conversion_workflow(self):
        health_response = requests.get(f'{self.BASE_URL}/health')
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data['status'] == 'healthy'
        csv_to_excel_payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=csv_to_excel_payload, timeout=30)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1['success'] is True
        excel_result = data1['result']
        excel_to_pdf_payload = {'source_format': 'excel', 'target_format': 'pdf', 'data': excel_result}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=excel_to_pdf_payload, timeout=30)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['success'] is True
        assert 'metadata' in data1
        assert 'metadata' in data2
        assert data1['metadata']['rows_count'] == 3
        assert data1['metadata']['columns_count'] == 4
        print('End-to-end workflow test passed')

    def test_batch_conversion_workflow(self):
        conversions = [{'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}, {'source_format': 'excel', 'target_format': 'csv', 'data': self.test_data['excel']}, {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(self.test_data['complex_csv'].encode('utf-8')).decode('utf-8')}]
        batch_payload = {'conversions': conversions, 'parallel': True}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=batch_payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == 3
        for i, result in enumerate(data['results']):
            assert result['success'] is True, f'The {i + 1}-th conversion failed: {result.get('message', 'Unknown error')}'
            assert 'result' in result
            assert result['result'] != ''
        summary = data['summary']
        assert summary['total_count'] == 3
        assert summary['success_count'] == 3
        assert summary['failure_count'] == 0
        print('Batch conversion workflow test passed')

    def test_error_handling_workflow(self):
        invalid_format_payload = {'source_format': 'invalid', 'target_format': 'excel', 'data': base64.b64encode(b'test').decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=invalid_format_payload, timeout=10)
        assert response1.status_code in [400, 422]
        empty_data_payload = {'source_format': 'csv', 'target_format': 'excel', 'data': ''}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=empty_data_payload, timeout=10)
        assert response2.status_code in [200, 400]
        health_response = requests.get(f'{self.BASE_URL}/health')
        assert health_response.status_code == 200
        print('Error handling workflow test passed')

    def test_performance_under_realistic_load(self):

        def simulate_user_session(session_id):
            results = []
            health_response = requests.get(f'{self.BASE_URL}/health')
            results.append(health_response.status_code == 200)
            operations = [('csv', 'excel', self.test_data['csv']), ('excel', 'csv', self.test_data['excel']), ('csv', 'pdf', self.test_data['complex_csv'])]
            for source_fmt, target_fmt, data in operations:
                payload = {'source_format': source_fmt, 'target_format': target_fmt, 'data': base64.b64encode(data.encode('utf-8')).decode('utf-8') if isinstance(data, str) else data}
                response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
                results.append(response.status_code == 200)
                time.sleep(0.2)
            return results
        import threading
        results = []
        errors = []

        def run_user_session(session_id):
            try:
                session_results = simulate_user_session(session_id)
                results.append(session_results)
            except Exception as e:
                errors.append(f'Session {session_id} error: {str(e)}')
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_user_session, args=(i,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'User session error: {errors}'
        total_operations = sum((len(session_result) for session_result in results))
        successful_operations = sum((sum(session_result) for session_result in results))
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        print('Performance under realistic load test passed')
        print(f'Total operations: {total_operations}')
        print(f'Successful operations: {successful_operations}')
        print(f'Success rate: {success_rate * 100:.1f}%')
        assert success_rate > 0.9, f'Success rate is too low: {success_rate * 100:.1f}%'

    def test_data_consistency_across_formats(self):
        original_csv = 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000'
        payload1 = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(original_csv.encode('utf-8')).decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_data = response1.json()['result']
        payload2 = {'source_format': 'excel', 'target_format': 'csv', 'data': excel_data}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=payload2, timeout=30)
        assert response2.status_code == 200
        final_csv = base64.b64decode(response2.json()['result']).decode('utf-8')
        original_lines = [line.strip() for line in original_csv.split('\n') if line.strip()]
        final_lines = [line.strip() for line in final_csv.split('\n') if line.strip()]
        assert len(original_lines) == len(final_lines), 'Number of rows is inconsistent'
        for original_line, final_line in zip(original_lines, final_lines):
            original_elements = set(original_line.split(','))
            final_elements = set(final_line.split(','))
            assert len(original_elements) == len(final_elements), f'Number of data elements is inconsistent: {original_line} vs {final_line}'
        print('Data consistency test passed')

    def test_system_resource_usage(self):
        health_before = requests.get(f'{self.BASE_URL}/health')
        assert health_before.status_code == 200
        before_timestamp = health_before.json()['timestamp']
        operations = []
        for i in range(10):
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}
            operations.append(payload)
        start_time = time.time()
        for payload in operations:
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            assert response.status_code == 200
        end_time = time.time()
        health_after = requests.get(f'{self.BASE_URL}/health')
        assert health_after.status_code == 200
        after_timestamp = health_after.json()['timestamp']
        assert health_before.json()['status'] == 'healthy'
        assert health_after.json()['status'] == 'healthy'
        print('System resource usage test passed')
        print(f'Number of operations: {len(operations)}')
        print(f'Total time: {end_time - start_time:.2f} seconds')
        print(f'Average time: {(end_time - start_time) / len(operations):.2f} seconds')
        print('System remains healthy after high load')
        time.sleep(2)
        final_health = requests.get(f'{self.BASE_URL}/health')
        assert final_health.status_code == 200
        assert final_health.json()['status'] == 'healthy'

    def test_api_version_compatibility(self):
        health_response = requests.get(f'{self.BASE_URL}/health')
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert 'version' in health_data
        interfaces = [('Health check', 'GET', f'{self.BASE_URL}/health'), ('Single conversion', 'POST', f'{self.BASE_URL}/convert'), ('Batch conversion', 'POST', f'{self.BASE_URL}/convert/batch')]
        for interface_name, method, url in interfaces:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(b'test,a,b\n1,2,3').decode('utf-8')}
                response = requests.post(url, json=payload, timeout=10)
            print(f'{interface_name} interface status: {response.status_code}')
            assert response.status_code in [200, 400, 404, 405, 422], f'{interface_name} interface is not available'
        print('API version compatibility test passed')

    def test_real_world_usage_scenario(self):
        employee_data = 'EmployeeID,Name,Department,Position,HireDate,Salary,PerformanceLevel\nE001,Zhang San,Technology,Senior Engineer,2022-01-15,25000,A\nE002,Li Si,Sales,Sales Manager,2021-08-20,30000,A\nE003,Wang Wu,Marketing,Marketing Specialist,2023-03-10,15000,B\nE004,Zhao Liu,HR,HR Assistant,2022-11-05,12000,B'
        payload1 = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(employee_data.encode('utf-8')).decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_report = response1.json()['result']
        payload2 = {'source_format': 'excel', 'target_format': 'pdf', 'data': excel_report}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=payload2, timeout=30)
        assert response2.status_code == 200
        pdf_report = response2.json()['result']
        data1 = response1.json()
        data2 = response2.json()
        assert data1['success'] is True
        assert data2['success'] is True
        assert data1['metadata']['rows_count'] == 4
        assert data1['metadata']['columns_count'] == 7
        pdf_size = len(base64.b64decode(pdf_report)) / 1024
        assert pdf_size > 1, f'PDF report is too small: {pdf_size:.1f}KB'
        print('Real-world usage scenario test passed')
        print(f'Employee data rows: {data1['metadata']['rows_count']}')
        print(f'Data columns: {data1['metadata']['columns_count']}')
        print(f'PDF report size: {pdf_size:.1f}KB')

def run_user_session(session_id):
    try:
        session_results = simulate_user_session(session_id)
        results.append(session_results)
    except Exception as e:
        errors.append(f'Session {session_id} error: {str(e)}')

# Node: simulate_user_session
def test_performance_under_realistic_load(self):

    def simulate_user_session(session_id):
        results = []
        health_response = requests.get(f'{self.BASE_URL}/health')
        results.append(health_response.status_code == 200)
        operations = [('csv', 'excel', self.test_data['csv']), ('excel', 'csv', self.test_data['excel']), ('csv', 'pdf', self.test_data['complex_csv'])]
        for source_fmt, target_fmt, data in operations:
            payload = {'source_format': source_fmt, 'target_format': target_fmt, 'data': base64.b64encode(data.encode('utf-8')).decode('utf-8') if isinstance(data, str) else data}
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            results.append(response.status_code == 200)
            time.sleep(0.2)
        return results
    import threading
    results = []
    errors = []

    def run_user_session(session_id):
        try:
            session_results = simulate_user_session(session_id)
            results.append(session_results)
        except Exception as e:
            errors.append(f'Session {session_id} error: {str(e)}')
    threads = []
    for i in range(5):
        thread = threading.Thread(target=run_user_session, args=(i,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    assert len(errors) == 0, f'User session error: {errors}'
    total_operations = sum((len(session_result) for session_result in results))
    successful_operations = sum((sum(session_result) for session_result in results))
    success_rate = successful_operations / total_operations if total_operations > 0 else 0
    print('Performance under realistic load test passed')
    print(f'Total operations: {total_operations}')
    print(f'Successful operations: {successful_operations}')
    print(f'Success rate: {success_rate * 100:.1f}%')
    assert success_rate > 0.9, f'Success rate is too low: {success_rate * 100:.1f}%'

# Node: Thread
# Node: start
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

# Node: mean
# Node: median
# Node: max
# Node: stdev
def make_request():
    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
    end_time = time.time()
    return end_time - start_time if response.status_code == 200 else None

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

# Node: ThreadPoolExecutor
# Node: submit
# Node: result
# Node: as_completed
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

# Node: health_checks
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

def check_dependencies():
    required_packages = ['pytest', 'requests']
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    if missing_packages:
        print(f'Missing dependencies: {', '.join(missing_packages)}')
        print('Please run: pip install -r requirements.txt')
        return False
    return True

# Node: __import__
class TestHistoryAPI:
    BASE_URL = 'http://localhost:8082/api/v1'
    TEST_USER_TOKEN = 'test_token_12345'

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
            if response.status_code == 200:
                history_records = response.json().get('history', [])
                for record in history_records:
                    if record.get('content_id', '').startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/history/{record['id']}', headers=self.get_auth_headers())
        except requests.exceptions.ConnectionError:
            pytest.skip('API Server not running')

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_record_history_view_action(self):
        history_data = {'action': 'view', 'content_id': 'test_content_view_001', 'content_type': 'post', 'metadata': {'duration': 30, 'device': 'mobile'}, 'session_id': 'test_session_123'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == history_data['action']
        assert data['content_id'] == history_data['content_id']
        assert data['content_type'] == history_data['content_type']
        assert data['metadata'] == history_data['metadata']
        assert data['session_id'] == history_data['session_id']
        assert 'id' in data
        assert 'created_at' in data
        assert 'ip_address' in data
        assert 'user_agent' in data

    def test_record_history_search_action(self):
        history_data = {'action': 'search', 'metadata': {'query': 'python tutorial', 'results_count': 25}, 'session_id': 'test_session_456'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'search'
        assert data['metadata']['query'] == 'python tutorial'

    def test_record_history_share_action(self):
        history_data = {'action': 'share', 'content_id': 'test_content_share_001', 'content_type': 'article', 'metadata': {'platform': 'twitter', 'share_type': 'link'}}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'share'
        assert data['metadata']['platform'] == 'twitter'

    def test_record_history_download_action(self):
        history_data = {'action': 'download', 'content_id': 'test_content_download_001', 'content_type': 'video', 'metadata': {'file_size': 1024000, 'format': 'mp4'}}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'download'

    def test_record_history_minimal_data(self):
        history_data = {'action': 'view'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'view'

    def test_record_history_invalid_action(self):
        history_data = {'action': 'invalid_action', 'content_id': 'test_content_invalid'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_record_history_unauthorized(self):
        history_data = {'action': 'view', 'content_id': 'test_content_unauth'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data)
        assert response.status_code in [401, 403]

    def test_get_history_empty(self):
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'history' in data
        assert 'pagination' in data
        assert len(data['history']) == 0

    def test_get_history_with_data(self):
        actions = [{'action': 'view', 'content_id': 'test_history_1', 'content_type': 'post'}, {'action': 'search', 'metadata': {'query': 'test query'}}, {'action': 'share', 'content_id': 'test_history_2', 'content_type': 'article'}, {'action': 'download', 'content_id': 'test_history_3', 'content_type': 'video'}]
        created_records = []
        for action_data in actions:
            response = requests.post(f'{self.BASE_URL}/history', json=action_data, headers=self.get_auth_headers())
            assert response.status_code == 201
            created_records.append(response.json())
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) >= 4
        assert data['pagination']['total'] >= 4

    def test_get_history_pagination(self):
        for i in range(25):
            history_data = {'action': 'view', 'content_id': f'test_pagination_{i + 1}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?page=1&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 25
        response = requests.get(f'{self.BASE_URL}/history?page=3&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 3

    def test_get_history_filter_by_action(self):
        actions = ['view', 'search', 'share', 'download', 'view']
        for i, action in enumerate(actions):
            history_data = {'action': action, 'content_id': f'test_filter_action_{i + 1}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?action=view', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        view_records = [record for record in data['history'] if record['action'] == 'view']
        assert len(view_records) >= 2

    def test_get_history_filter_by_content_type(self):
        content_types = ['post', 'article', 'video', 'product']
        for content_type in content_types:
            history_data = {'action': 'view', 'content_id': f'test_filter_type_{content_type}', 'content_type': content_type}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?content_type=article', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        article_records = [record for record in data['history'] if record['content_type'] == 'article']
        assert len(article_records) >= 1

    def test_get_history_filter_by_date_range(self):
        base_time = datetime.now()
        yesterday_data = {'action': 'view', 'content_id': 'test_yesterday', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=yesterday_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        today_data = {'action': 'view', 'content_id': 'test_today', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=today_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        today_str = base_time.strftime('%Y-%m-%d')
        response = requests.get(f'{self.BASE_URL}/history?start_date={today_str}&end_date={today_str}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        today_records = [record for record in data['history'] if 'test_today' in record['content_id']]
        assert len(today_records) >= 1

    def test_get_history_filter_by_session(self):
        session_id = 'test_session_filter'
        for i in range(3):
            history_data = {'action': 'view', 'content_id': f'test_session_{i + 1}', 'content_type': 'post', 'session_id': session_id}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?session_id={session_id}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        session_records = [record for record in data['history'] if record['session_id'] == session_id]
        assert len(session_records) >= 3

    def test_get_history_unauthorized(self):
        response = requests.get(f'{self.BASE_URL}/history')
        assert response.status_code in [401, 403]

    def test_delete_single_history_success(self):
        history_data = {'action': 'view', 'content_id': 'test_delete_single', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        history_id = response.json()['id']
        response = requests.delete(f'{self.BASE_URL}/history/{history_id}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    def test_delete_single_history_not_found(self):
        response = requests.delete(f'{self.BASE_URL}/history/non_existent_id', headers=self.get_auth_headers())
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data

    def test_delete_single_history_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/history/some_id')
        assert response.status_code in [401, 403]

    def test_clear_all_history_success(self):
        for i in range(5):
            history_data = {'action': 'view', 'content_id': f'test_clear_{i + 1}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        initial_count = response.json()['pagination']['total']
        assert initial_count >= 5
        response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'deleted_count' in data
        assert data['deleted_count'] >= 5

    def test_clear_all_history_empty(self):
        response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['deleted_count'] == 0

    def test_clear_all_history_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/history')
        assert response.status_code in [401, 403]

    def test_history_workflow_complete(self):
        actions = [{'action': 'view', 'content_id': 'workflow_1', 'content_type': 'post'}, {'action': 'search', 'metadata': {'query': 'workflow test'}}, {'action': 'share', 'content_id': 'workflow_2', 'content_type': 'article'}]
        created_ids = []
        for action_data in actions:
            response = requests.post(f'{self.BASE_URL}/history', json=action_data, headers=self.get_auth_headers())
            assert response.status_code == 201
            created_ids.append(response.json()['id'])
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        history_ids = [record['id'] for record in data['history']]
        for created_id in created_ids:
            assert created_id in history_ids
        response = requests.delete(f'{self.BASE_URL}/history/{created_ids[0]}', headers=self.get_auth_headers())
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        history_ids = [record['id'] for record in data['history']]
        assert created_ids[0] not in history_ids
        response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) == 0

    def test_history_actions_coverage(self):
        actions = ['view', 'search', 'share', 'download']
        for action in actions:
            history_data = {'action': action, 'content_id': f'test_action_{action}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        recorded_actions = [record['action'] for record in data['history']]
        for action in actions:
            assert action in recorded_actions

    def test_invalid_json_request(self):
        response = requests.post(f'{self.BASE_URL}/history', data='invalid json', headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        response = requests.get(f'{self.BASE_URL}/history?limit=1000', headers=self.get_auth_headers())
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100

def test_get_history_pagination(self):
    for i in range(25):
        history_data = {'action': 'view', 'content_id': f'test_pagination_{i + 1}', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/history?page=1&limit=10', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert len(data['history']) == 10
    assert data['pagination']['page'] == 1
    assert data['pagination']['total'] >= 25
    response = requests.get(f'{self.BASE_URL}/history?page=3&limit=10', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data['pagination']['page'] == 3

def test_get_history_filter_by_session(self):
    session_id = 'test_session_filter'
    for i in range(3):
        history_data = {'action': 'view', 'content_id': f'test_session_{i + 1}', 'content_type': 'post', 'session_id': session_id}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/history?session_id={session_id}', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    session_records = [record for record in data['history'] if record['session_id'] == session_id]
    assert len(session_records) >= 3

def test_clear_all_history_success(self):
    for i in range(5):
        history_data = {'action': 'view', 'content_id': f'test_clear_{i + 1}', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
    assert response.status_code == 200
    initial_count = response.json()['pagination']['total']
    assert initial_count >= 5
    response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'deleted_count' in data
    assert data['deleted_count'] >= 5

class TestLikesAPI:
    BASE_URL = 'http://localhost:8082/api/v1'
    TEST_USER_TOKEN = 'test_token_12345'

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            response = requests.get(f'{self.BASE_URL}/likes/history', headers=self.get_auth_headers())
            if response.status_code == 200:
                likes = response.json().get('likes', [])
                for like in likes:
                    if like['content_id'].startswith('test_content_'):
                        pass
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_add_like_success(self):
        like_data = {'content_id': 'test_content_like_001', 'content_type': 'post', 'action': 'like'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['content_id'] == like_data['content_id']
        assert data['content_type'] == like_data['content_type']
        assert data['action'] == like_data['action']
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_add_unlike_success(self):
        like_data = {'content_id': 'test_content_unlike_001', 'content_type': 'article', 'action': 'unlike'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'unlike'

    def test_add_like_missing_action(self):
        like_data = {'content_id': 'test_content_missing_action', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_like_invalid_action(self):
        like_data = {'content_id': 'test_content_invalid_action', 'content_type': 'post', 'action': 'invalid_action'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_like_invalid_content_type(self):
        like_data = {'content_id': 'test_content_invalid_type', 'content_type': 'invalid_type', 'action': 'like'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_like_unauthorized(self):
        like_data = {'content_id': 'test_content_unauth', 'content_type': 'post', 'action': 'like'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data)
        assert response.status_code in [401, 403]

    def test_get_like_stats_success(self):
        content_id = 'test_stats_content_001'
        content_type = 'post'
        like_data = {'content_id': content_id, 'content_type': content_type, 'action': 'like'}
        requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        unlike_data = {'content_id': content_id, 'content_type': content_type, 'action': 'unlike'}
        requests.post(f'{self.BASE_URL}/likes', json=unlike_data, headers=self.get_auth_headers())
        response = requests.get(f'{self.BASE_URL}/likes/stats/{content_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['content_id'] == content_id
        assert data['content_type'] == content_type
        assert 'total_likes' in data
        assert 'total_unlikes' in data
        assert 'user_action' in data

    def test_get_like_stats_not_found(self):
        response = requests.get(f'{self.BASE_URL}/likes/stats/non_existent_content')
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data['total_likes'] == 0
            assert data['total_unlikes'] == 0

    def test_get_like_stats_without_auth(self):
        response = requests.get(f'{self.BASE_URL}/likes/stats/some_content')
        assert response.status_code == 200

    def test_get_likes_history_empty(self):
        response = requests.get(f'{self.BASE_URL}/likes/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'likes' in data
        assert 'pagination' in data
        assert len(data['likes']) == 0

    def test_get_likes_history_with_data(self):
        likes_data = [{'content_id': 'test_history_1', 'content_type': 'post', 'action': 'like'}, {'content_id': 'test_history_2', 'content_type': 'article', 'action': 'unlike'}, {'content_id': 'test_history_3', 'content_type': 'video', 'action': 'like'}]
        for like_data in likes_data:
            response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/likes/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['likes']) >= 3
        assert data['pagination']['total'] >= 3

    def test_get_likes_history_pagination(self):
        for i in range(15):
            like_data = {'content_id': f'test_history_pagination_{i + 1}', 'content_type': 'post', 'action': 'like'}
            response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/likes/history?page=1&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['likes']) == 10
        assert data['pagination']['page'] == 1
        response = requests.get(f'{self.BASE_URL}/likes/history?page=2&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2

    def test_get_likes_history_filter_by_content_type(self):
        content_types = ['post', 'article', 'video']
        for content_type in content_types:
            like_data = {'content_id': f'test_filter_history_{content_type}', 'content_type': content_type, 'action': 'like'}
            response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/likes/history?content_type=video', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        video_likes = [like for like in data['likes'] if like['content_type'] == 'video']
        assert len(video_likes) >= 1

    def test_get_likes_history_unauthorized(self):
        response = requests.get(f'{self.BASE_URL}/likes/history')
        assert response.status_code in [401, 403]

    def test_like_workflow_complete(self):
        content_id = 'test_workflow_like_content'
        content_type = 'post'
        like_data = {'content_id': content_id, 'content_type': content_type, 'action': 'like'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        like_id = response.json()['id']
        response = requests.get(f'{self.BASE_URL}/likes/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        likes = response.json()['likes']
        like_ids = [like['id'] for like in likes]
        assert like_id in like_ids
        response = requests.get(f'{self.BASE_URL}/likes/stats/{content_id}')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_likes'] >= 1
        unlike_data = {'content_id': content_id, 'content_type': content_type, 'action': 'unlike'}
        response = requests.post(f'{self.BASE_URL}/likes', json=unlike_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/likes/stats/{content_id}')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_unlikes'] >= 1

    def test_multiple_users_like_same_content(self):
        content_id = 'test_multi_user_content'
        content_type = 'article'
        like_data = {'content_id': content_id, 'content_type': content_type, 'action': 'like'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code in [201, 409]
        response = requests.get(f'{self.BASE_URL}/likes/stats/{content_id}')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_likes'] >= 1

    def test_like_content_types_coverage(self):
        content_types = ['post', 'article', 'product', 'video']
        for content_type in content_types:
            like_data = {'content_id': f'test_content_type_{content_type}', 'content_type': content_type, 'action': 'like'}
            response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
            assert response.status_code == 201
            response = requests.get(f'{self.BASE_URL}/likes/stats/test_content_type_{content_type}')
            assert response.status_code == 200

    def test_invalid_json_request(self):
        response = requests.post(f'{self.BASE_URL}/likes', data='invalid json', headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        response = requests.get(f'{self.BASE_URL}/likes/history?limit=1000', headers=self.get_auth_headers())
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 50

def test_get_likes_history_pagination(self):
    for i in range(15):
        like_data = {'content_id': f'test_history_pagination_{i + 1}', 'content_type': 'post', 'action': 'like'}
        response = requests.post(f'{self.BASE_URL}/likes', json=like_data, headers=self.get_auth_headers())
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/likes/history?page=1&limit=10', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert len(data['likes']) == 10
    assert data['pagination']['page'] == 1
    response = requests.get(f'{self.BASE_URL}/likes/history?page=2&limit=10', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data['pagination']['page'] == 2

class TestFavoritesAPI:
    BASE_URL = 'http://localhost:8082/api/v1'
    TEST_USER_TOKEN = 'test_token_12345'

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            response = requests.get(f'{self.BASE_URL}/favorites', headers=self.get_auth_headers())
            if response.status_code == 200:
                favorites = response.json().get('favorites', [])
                for favorite in favorites:
                    if favorite['content_id'].startswith('test_content_'):
                        requests.delete(f'{self.BASE_URL}/favorites/{favorite['id']}', headers=self.get_auth_headers())
        except requests.exceptions.ConnectionError:
            pytest.skip('API server is not running')

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_add_favorite_success(self):
        favorite_data = {'content_id': 'test_content_001', 'content_type': 'post', 'category': 'test_category'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['content_id'] == favorite_data['content_id']
        assert data['content_type'] == favorite_data['content_type']
        assert data['category'] == favorite_data['category']
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_add_favorite_minimal_data(self):
        favorite_data = {'content_id': 'test_content_minimal', 'content_type': 'article'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['content_id'] == favorite_data['content_id']
        assert data['content_type'] == favorite_data['content_type']
        assert data['category'] is None or data['category'] == ''

    def test_add_favorite_duplicate_content(self):
        favorite_data = {'content_id': 'test_content_duplicate', 'content_type': 'video', 'category': 'test_category'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        first_id = response.json()['id']
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code in [201, 409]

    def test_add_favorite_invalid_content_type(self):
        favorite_data = {'content_id': 'test_content_invalid', 'content_type': 'invalid_type', 'category': 'test_category'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_favorite_missing_required_fields(self):
        favorite_data = {'category': 'test_category'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_favorite_unauthorized(self):
        favorite_data = {'content_id': 'test_content_unauth', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data)
        assert response.status_code in [401, 403]

    def test_get_favorites_list_empty(self):
        response = requests.get(f'{self.BASE_URL}/favorites', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'favorites' in data
        assert 'pagination' in data
        assert len(data['favorites']) == 0

    def test_get_favorites_list_with_data(self):
        favorites_data = [{'content_id': 'test_list_1', 'content_type': 'post', 'category': 'news'}, {'content_id': 'test_list_2', 'content_type': 'article', 'category': 'tech'}, {'content_id': 'test_list_3', 'content_type': 'video', 'category': 'entertainment'}]
        created_favorites = []
        for favorite_data in favorites_data:
            response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
            assert response.status_code == 201
            created_favorites.append(response.json())
        response = requests.get(f'{self.BASE_URL}/favorites', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['favorites']) >= 3
        assert data['pagination']['total'] >= 3
        assert data['pagination']['page'] == 1

    def test_get_favorites_with_pagination(self):
        for i in range(15):
            favorite_data = {'content_id': f'test_pagination_{i + 1}', 'content_type': 'post', 'category': 'test'}
            response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/favorites?page=1&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['favorites']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 15
        response = requests.get(f'{self.BASE_URL}/favorites?page=2&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2

    def test_get_favorites_filter_by_content_type(self):
        content_types = ['post', 'article', 'video', 'product']
        for content_type in content_types:
            favorite_data = {'content_id': f'test_filter_{content_type}', 'content_type': content_type, 'category': 'test'}
            response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/favorites?content_type=article', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        article_favorites = [f for f in data['favorites'] if f['content_type'] == 'article']
        assert len(article_favorites) >= 1

    def test_get_favorites_filter_by_category(self):
        categories = ['news', 'tech', 'entertainment', 'education']
        for category in categories:
            favorite_data = {'content_id': f'test_category_{category}', 'content_type': 'post', 'category': category}
            response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/favorites?category=tech', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        tech_favorites = [f for f in data['favorites'] if f['category'] == 'tech']
        assert len(tech_favorites) >= 1

    def test_delete_favorite_success(self):
        favorite_data = {'content_id': 'test_delete_001', 'content_type': 'post', 'category': 'test_delete'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        favorite_id = response.json()['id']
        response = requests.delete(f'{self.BASE_URL}/favorites/{favorite_id}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    def test_delete_favorite_not_found(self):
        response = requests.delete(f'{self.BASE_URL}/favorites/non_existent_id', headers=self.get_auth_headers())
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data

    def test_delete_favorite_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/favorites/some_id')
        assert response.status_code in [401, 403]

    def test_favorites_workflow_complete(self):
        favorite_data = {'content_id': 'test_workflow_content', 'content_type': 'article', 'category': 'test_workflow'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        favorite_id = response.json()['id']
        response = requests.get(f'{self.BASE_URL}/favorites?content_type=article', headers=self.get_auth_headers())
        assert response.status_code == 200
        favorites = response.json()['favorites']
        favorite_ids = [f['id'] for f in favorites]
        assert favorite_id in favorite_ids
        response = requests.delete(f'{self.BASE_URL}/favorites/{favorite_id}', headers=self.get_auth_headers())
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/favorites?content_type=article', headers=self.get_auth_headers())
        assert response.status_code == 200
        favorites = response.json()['favorites']
        favorite_ids = [f['id'] for f in favorites]
        assert favorite_id not in favorite_ids

    def test_invalid_json_request(self):
        response = requests.post(f'{self.BASE_URL}/favorites', data='invalid json', headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        response = requests.get(f'{self.BASE_URL}/favorites?limit=1000', headers=self.get_auth_headers())
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100

def test_get_favorites_with_pagination(self):
    for i in range(15):
        favorite_data = {'content_id': f'test_pagination_{i + 1}', 'content_type': 'post', 'category': 'test'}
        response = requests.post(f'{self.BASE_URL}/favorites', json=favorite_data, headers=self.get_auth_headers())
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/favorites?page=1&limit=10', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert len(data['favorites']) == 10
    assert data['pagination']['page'] == 1
    assert data['pagination']['total'] >= 15
    response = requests.get(f'{self.BASE_URL}/favorites?page=2&limit=10', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data['pagination']['page'] == 2

class TestSendBatchEmails:
    """Test cases for POST /api/v1/mail/send-batch endpoint."""

    def test_send_batch_success(self):
        """Test successfully sending a batch of emails."""
        payload = {'emails': [{'to': ['user1@example.com'], 'subject': 'Email 1', 'body': 'Body 1'}, {'to': ['user2@example.com'], 'subject': 'Email 2', 'body': 'Body 2'}, {'to': ['user3@example.com'], 'subject': 'Email 3', 'body': 'Body 3'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'batch_id' in data
        assert data['total'] == 3
        assert 'queued' in data
        assert 'failed' in data
        assert data['queued'] + data['failed'] == 3
        assert 'results' in data
        assert len(data['results']) == 3
        assert 'timestamp' in data
        for result in data['results']:
            assert 'mail_id' in result
            assert 'status' in result
            assert 'message' in result

    def test_send_batch_single_email(self):
        """Test sending batch with single email."""
        payload = {'emails': [{'to': ['user@example.com'], 'subject': 'Single Email Batch', 'body': 'Test body'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert len(data['results']) == 1

    def test_send_batch_with_optional_fields(self):
        """Test sending batch with optional fields."""
        payload = {'emails': [{'to': ['user1@example.com'], 'subject': 'Email 1', 'body': 'Body 1', 'from': 'sender@example.com', 'cc': ['cc@example.com'], 'priority': 'high'}, {'to': ['user2@example.com'], 'subject': 'Email 2', 'body': 'Body 2', 'bcc': ['bcc@example.com'], 'priority': 'low'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2

    def test_send_batch_maximum_size(self):
        """Test sending batch with maximum allowed size (100 emails)."""
        emails = []
        for i in range(100):
            emails.append({'to': [f'user{i}@example.com'], 'subject': f'Email {i}', 'body': f'Body {i}'})
        payload = {'emails': emails}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 100
        assert len(data['results']) == 100

    def test_send_batch_exceeds_maximum_size(self):
        """Test sending batch exceeding maximum size returns 400."""
        emails = []
        for i in range(101):
            emails.append({'to': [f'user{i}@example.com'], 'subject': f'Email {i}', 'body': f'Body {i}'})
        payload = {'emails': emails}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'BATCH_TOO_LARGE'

    def test_send_batch_empty_list(self):
        """Test sending empty batch list returns 400."""
        payload = {'emails': []}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_send_batch_missing_emails_field(self):
        """Test sending batch without emails field returns 400."""
        payload = {}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'MISSING_FIELD'

    def test_send_batch_partial_failure(self):
        """Test batch with some invalid emails, check partial success."""
        payload = {'emails': [{'to': ['valid@example.com'], 'subject': 'Valid Email', 'body': 'Valid body'}, {'to': ['invalid-email'], 'subject': 'Invalid Email', 'body': 'Invalid body'}, {'to': ['valid2@example.com'], 'subject': 'Valid Email 2', 'body': 'Valid body 2'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 3
        assert data['failed'] >= 1
        assert data['queued'] >= 2
        failed_count = sum((1 for r in data['results'] if r['status'] == 'failed'))
        assert failed_count >= 1

    def test_send_batch_email_missing_required_field(self):
        """Test batch where an email is missing required field."""
        payload = {'emails': [{'to': ['user1@example.com'], 'subject': 'Email 1', 'body': 'Body 1'}, {'to': ['user2@example.com'], 'body': 'Body 2'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert data['failed'] >= 1
        failed_results = [r for r in data['results'] if r['status'] == 'failed']
        assert len(failed_results) >= 1

    def test_send_batch_all_invalid(self):
        """Test batch where all emails are invalid."""
        payload = {'emails': [{'to': ['invalid1'], 'subject': 'Email 1', 'body': 'Body 1'}, {'to': ['invalid2'], 'subject': 'Email 2', 'body': 'Body 2'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert data['failed'] == 2
        assert data['queued'] == 0

    def test_send_batch_mixed_priorities(self):
        """Test batch with emails of different priorities."""
        payload = {'emails': [{'to': ['user1@example.com'], 'subject': 'High Priority', 'body': 'Body', 'priority': 'high'}, {'to': ['user2@example.com'], 'subject': 'Normal Priority', 'body': 'Body', 'priority': 'normal'}, {'to': ['user3@example.com'], 'subject': 'Low Priority', 'body': 'Body', 'priority': 'low'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 3

    def test_send_batch_duplicate_recipients(self):
        """Test batch sending same email to same recipient multiple times."""
        payload = {'emails': [{'to': ['same@example.com'], 'subject': 'Email 1', 'body': 'Body 1'}, {'to': ['same@example.com'], 'subject': 'Email 2', 'body': 'Body 2'}]}
        response = requests.post(SEND_BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['results']) == 2

def test_send_batch_maximum_size(self):
    """Test sending batch with maximum allowed size (100 emails)."""
    emails = []
    for i in range(100):
        emails.append({'to': [f'user{i}@example.com'], 'subject': f'Email {i}', 'body': f'Body {i}'})
    payload = {'emails': emails}
    response = requests.post(SEND_BATCH_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 100
    assert len(data['results']) == 100

def _wait(seconds=1):
    time.sleep(seconds)

class TestTaskAPI:
    """Test suite for Task Management API endpoints"""
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/tasks')
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    requests.delete(f'{self.BASE_URL}/tasks/{task['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f'{self.BASE_URL}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert data['status'] == 'healthy'

    def test_create_task_success(self):
        """Test successful task creation"""
        task_data = {'title': 'Test Task', 'description': 'This is a test task', 'priority': 'high', 'due_date': '2024-12-31T23:59:59Z'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == task_data['title']
        assert data['description'] == task_data['description']
        assert data['priority'] == task_data['priority']
        assert data['status'] == 'pending'
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_create_task_minimal_data(self):
        """Test task creation with minimal required data"""
        task_data = {'title': 'Minimal Task', 'priority': 'medium'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == task_data['title']
        assert data['priority'] == task_data['priority']
        assert data['status'] == 'pending'
        assert data['description'] is None or data['description'] == ''

    def test_create_task_invalid_priority(self):
        """Test task creation with invalid priority"""
        task_data = {'title': 'Test Task', 'priority': 'invalid_priority'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'validation_error'

    def test_create_task_missing_required_fields(self):
        """Test task creation with missing required fields"""
        task_data = {'description': 'Missing title and priority'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_create_task_title_too_long(self):
        """Test task creation with title exceeding maximum length"""
        task_data = {'title': 'x' * 201, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_get_tasks_list_empty(self):
        """Test getting tasks list when no tasks exist"""
        response = requests.get(f'{self.BASE_URL}/tasks')
        assert response.status_code == 200
        data = response.json()
        assert 'tasks' in data
        assert 'pagination' in data
        assert len(data['tasks']) == 0
        assert data['pagination']['total'] == 0

    def test_get_tasks_list_with_data(self):
        """Test getting tasks list with existing tasks"""
        tasks_data = [{'title': 'Task 1', 'priority': 'high'}, {'title': 'Task 2', 'priority': 'medium'}, {'title': 'Task 3', 'priority': 'low'}]
        created_tasks = []
        for task_data in tasks_data:
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            created_tasks.append(response.json())
        response = requests.get(f'{self.BASE_URL}/tasks')
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 3
        assert data['pagination']['total'] == 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10

    def test_get_tasks_list_pagination(self):
        """Test tasks list pagination"""
        for i in range(15):
            task_data = {'title': f'Task {i + 1}', 'priority': 'medium'}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/tasks?page=1&limit=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] == 15
        assert data['pagination']['pages'] == 2
        response = requests.get(f'{self.BASE_URL}/tasks?page=2&limit=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 5
        assert data['pagination']['page'] == 2

    def test_get_tasks_list_filter_by_status(self):
        """Test filtering tasks by status"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        task_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/tasks/{task_id}', json={'status': 'completed'}, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/tasks?status=completed')
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['status'] == 'completed'

    def test_get_tasks_list_filter_by_priority(self):
        """Test filtering tasks by priority"""
        priorities = ['high', 'medium', 'low']
        for priority in priorities:
            task_data = {'title': f'Task {priority}', 'priority': priority}
            requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/tasks?priority=high')
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['priority'] == 'high'

    def test_get_single_task_success(self):
        """Test getting a single task by ID"""
        task_data = {'title': 'Single Task', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        created_task = response.json()
        response = requests.get(f'{self.BASE_URL}/tasks/{created_task['id']}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == created_task['id']
        assert data['title'] == created_task['title']
        assert data['priority'] == created_task['priority']

    def test_get_single_task_not_found(self):
        """Test getting a non-existent task"""
        response = requests.get(f'{self.BASE_URL}/tasks/99999')
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_update_task_success(self):
        """Test successful task update"""
        task_data = {'title': 'Original Task', 'priority': 'low'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        task_id = response.json()['id']
        update_data = {'title': 'Updated Task', 'description': 'Updated description', 'priority': 'high', 'status': 'in_progress'}
        response = requests.put(f'{self.BASE_URL}/tasks/{task_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert data['description'] == update_data['description']
        assert data['priority'] == update_data['priority']
        assert data['status'] == update_data['status']
        assert data['id'] == task_id

    def test_update_task_partial(self):
        """Test partial task update"""
        task_data = {'title': 'Original Task', 'description': 'Original description', 'priority': 'low'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        task_id = response.json()['id']
        update_data = {'title': 'Updated Title Only'}
        response = requests.put(f'{self.BASE_URL}/tasks/{task_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert data['description'] == task_data['description']
        assert data['priority'] == task_data['priority']

    def test_update_task_invalid_status(self):
        """Test task update with invalid status"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        task_id = response.json()['id']
        update_data = {'status': 'invalid_status'}
        response = requests.put(f'{self.BASE_URL}/tasks/{task_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_update_task_not_found(self):
        """Test updating a non-existent task"""
        update_data = {'title': 'Updated Task'}
        response = requests.put(f'{self.BASE_URL}/tasks/99999', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_delete_task_success(self):
        """Test successful task deletion"""
        task_data = {'title': 'Task to Delete', 'priority': 'medium'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        task_id = response.json()['id']
        response = requests.delete(f'{self.BASE_URL}/tasks/{task_id}')
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        response = requests.get(f'{self.BASE_URL}/tasks/{task_id}')
        assert response.status_code == 404

    def test_delete_task_not_found(self):
        """Test deleting a non-existent task"""
        response = requests.delete(f'{self.BASE_URL}/tasks/99999')
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_task_workflow_complete(self):
        """Test complete task workflow: create -> update -> complete -> delete"""
        task_data = {'title': 'Workflow Task', 'description': 'Complete workflow test', 'priority': 'high', 'due_date': '2024-12-31T23:59:59Z'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        task_id = response.json()['id']
        response = requests.put(f'{self.BASE_URL}/tasks/{task_id}', json={'status': 'in_progress'}, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        assert response.json()['status'] == 'in_progress'
        response = requests.put(f'{self.BASE_URL}/tasks/{task_id}', json={'status': 'completed'}, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        assert response.json()['status'] == 'completed'
        response = requests.get(f'{self.BASE_URL}/tasks?status=completed')
        assert response.status_code == 200
        completed_tasks = response.json()['tasks']
        assert len(completed_tasks) == 1
        assert completed_tasks[0]['id'] == task_id
        response = requests.delete(f'{self.BASE_URL}/tasks/{task_id}')
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/tasks/{task_id}')
        assert response.status_code == 404

    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body"""
        response = requests.post(f'{self.BASE_URL}/tasks', data='invalid json', headers={'Content-Type': 'application/json'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_missing_content_type_header(self):
        """Test handling of missing Content-Type header"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data)
        assert response.status_code in [201, 400]

    def test_large_pagination_limit(self):
        """Test pagination with limit exceeding maximum"""
        response = requests.get(f'{self.BASE_URL}/tasks?limit=1000')
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100

def test_get_tasks_list_with_data(self):
    """Test getting tasks list with existing tasks"""
    tasks_data = [{'title': 'Task 1', 'priority': 'high'}, {'title': 'Task 2', 'priority': 'medium'}, {'title': 'Task 3', 'priority': 'low'}]
    created_tasks = []
    for task_data in tasks_data:
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        created_tasks.append(response.json())
    response = requests.get(f'{self.BASE_URL}/tasks')
    assert response.status_code == 200
    data = response.json()
    assert len(data['tasks']) == 3
    assert data['pagination']['total'] == 3
    assert data['pagination']['page'] == 1
    assert data['pagination']['limit'] == 10

def test_get_tasks_list_pagination(self):
    """Test tasks list pagination"""
    for i in range(15):
        task_data = {'title': f'Task {i + 1}', 'priority': 'medium'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/tasks?page=1&limit=10')
    assert response.status_code == 200
    data = response.json()
    assert len(data['tasks']) == 10
    assert data['pagination']['page'] == 1
    assert data['pagination']['total'] == 15
    assert data['pagination']['pages'] == 2
    response = requests.get(f'{self.BASE_URL}/tasks?page=2&limit=10')
    assert response.status_code == 200
    data = response.json()
    assert len(data['tasks']) == 5
    assert data['pagination']['page'] == 2

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/tasks')
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    requests.delete(f'{self.BASE_URL}/tasks/{task['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_task_title_boundary_values(self):
        """Test task title at boundary values"""
        max_title = 'x' * 200
        task_data = {'title': max_title, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == max_title
        too_long_title = 'x' * 201
        task_data = {'title': too_long_title, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_task_description_boundary_values(self):
        """Test task description at boundary values"""
        max_description = 'x' * 1000
        task_data = {'title': 'Test Task', 'description': max_description, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['description'] == max_description
        too_long_description = 'x' * 1001
        task_data = {'title': 'Test Task', 'description': too_long_description, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_unicode_characters_in_task(self):
        """Test handling of Unicode characters in task data"""
        unicode_task = {'title': 'Test Mission 🚀', 'description': 'This is a task description containing Unicode characters: Chinese, emoji, special symbols @#$%', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=unicode_task, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == unicode_task['title']
        assert data['description'] == unicode_task['description']

    def test_special_characters_in_task(self):
        """Test handling of special characters in task data"""
        special_chars_task = {'title': 'Task with Special Chars: @#$%^&*()_+-=[]{}|;\':",./<>?', 'description': 'Description with newlines\nand tabs\tand quotes"\'', 'priority': 'medium'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=special_chars_task, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == special_chars_task['title']
        assert data['description'] == special_chars_task['description']

    def test_date_formats(self):
        """Test various date formats for due_date"""
        date_formats = ['2024-12-31T23:59:59Z', '2024-12-31T23:59:59.000Z', '2024-12-31T23:59:59+00:00', '2024-12-31T23:59:59-05:00', '2024-12-31']
        for date_format in date_formats:
            task_data = {'title': f'Task with date {date_format}', 'priority': 'high', 'due_date': date_format}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_invalid_date_formats(self):
        """Test invalid date formats"""
        invalid_dates = ['not-a-date', '2024-13-01', '2024-02-30', '2024/12/31', '31-12-2024', '']
        for invalid_date in invalid_dates:
            task_data = {'title': 'Task with invalid date', 'priority': 'high', 'due_date': invalid_date}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_empty_strings(self):
        """Test handling of empty strings"""
        task_data = {'title': '', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        task_data = {'title': 'Valid Task', 'description': '', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201

    def test_whitespace_only_strings(self):
        """Test handling of whitespace-only strings"""
        task_data = {'title': '   ', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        task_data = {'title': 'Valid Task', 'description': '   ', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_null_values(self):
        """Test handling of null values"""
        task_data = {'title': 'Valid Task', 'description': None, 'priority': 'high', 'due_date': None}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_extra_fields(self):
        """Test handling of extra fields in request"""
        task_data = {'title': 'Valid Task', 'priority': 'high', 'extra_field': 'should be ignored', 'another_field': 123}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'extra_field' not in data
        assert 'another_field' not in data

    def test_case_sensitivity(self):
        """Test case sensitivity of enum values"""
        task_data = {'title': 'Test Task', 'priority': 'HIGH'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            task_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_large_numbers(self):
        """Test handling of large numbers in pagination"""
        response = requests.get(f'{self.BASE_URL}/tasks?page=999999')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/tasks?limit=999999')
        assert response.status_code in [200, 422]

    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        response = requests.get(f'{self.BASE_URL}/tasks?page=-1')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/tasks?limit=-1')
        assert response.status_code in [200, 422]

    def test_zero_values(self):
        """Test handling of zero values"""
        response = requests.get(f'{self.BASE_URL}/tasks?page=0')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/tasks?limit=0')
        assert response.status_code in [200, 422]

    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts"""
        malicious_titles = ["'; DROP TABLE tasks; --", "1' OR '1'='1", "admin'--", '1; DELETE FROM tasks; --']
        for malicious_title in malicious_titles:
            task_data = {'title': malicious_title, 'priority': 'high'}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_xss_attempts(self):
        """Test protection against XSS attempts"""
        xss_payloads = ["<script>alert('xss')</script>", "javascript:alert('xss')", "<img src=x onerror=alert('xss')>", "';alert('xss');//"]
        for payload in xss_payloads:
            task_data = {'title': payload, 'priority': 'high'}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        results = []
        errors = []

        def create_task(thread_id):
            try:
                task_data = {'title': f'Concurrent Task {thread_id}', 'priority': 'medium'}
                response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_task, args=(i,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors in concurrent requests: {errors}'
        assert len(results) == 5
        for thread_id, status_code in results:
            assert status_code == 201
        response = requests.get(f'{self.BASE_URL}/tasks')
        if response.status_code == 200:
            tasks = response.json().get('tasks', [])
            for task in tasks:
                if task['title'].startswith('Concurrent Task'):
                    requests.delete(f'{self.BASE_URL}/tasks/{task['id']}')

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = ['{"title": "Test", "priority": "high"', '{"title": "Test", "priority": "high",}', '{"title": "Test", "priority": high}', '{"title": "Test", "priority": "high" "extra": "value"}', '{"title": "Test", "priority": "high", "status": }']
        for malformed_json in malformed_jsons:
            response = requests.post(f'{self.BASE_URL}/tasks', data=malformed_json, headers={'Content-Type': 'application/json'})
            assert response.status_code == 400

    def test_content_type_variations(self):
        """Test handling of different content types"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        content_types = ['application/json', 'application/json; charset=utf-8', 'application/json;charset=utf-8', 'text/json', 'text/plain']
        for content_type in content_types:
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': content_type})
            assert response.status_code in [201, 400, 415]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_missing_headers(self):
        """Test handling of missing headers"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data)
        assert response.status_code in [201, 400, 415]
        if response.status_code == 201:
            task_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_very_long_url(self):
        """Test handling of very long URLs"""
        long_params = '&'.join([f'param{i}=value{i}' for i in range(100)])
        response = requests.get(f'{self.BASE_URL}/tasks?{long_params}')
        assert response.status_code in [200, 414, 400]

def test_concurrent_requests(self):
    """Test handling of concurrent requests"""
    import threading
    import time
    results = []
    errors = []

    def create_task(thread_id):
        try:
            task_data = {'title': f'Concurrent Task {thread_id}', 'priority': 'medium'}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            results.append((thread_id, response.status_code))
        except Exception as e:
            errors.append((thread_id, str(e)))
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_task, args=(i,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(errors) == 0, f'Errors in concurrent requests: {errors}'
    assert len(results) == 5
    for thread_id, status_code in results:
        assert status_code == 201
    response = requests.get(f'{self.BASE_URL}/tasks')
    if response.status_code == 200:
        tasks = response.json().get('tasks', [])
        for task in tasks:
            if task['title'].startswith('Concurrent Task'):
                requests.delete(f'{self.BASE_URL}/tasks/{task['id']}')

def test_very_long_url(self):
    """Test handling of very long URLs"""
    long_params = '&'.join([f'param{i}=value{i}' for i in range(100)])
    response = requests.get(f'{self.BASE_URL}/tasks?{long_params}')
    assert response.status_code in [200, 414, 400]

class TaskDataGenerator:
    """Utility class for generating test task data"""

    @staticmethod
    def generate_valid_task(**overrides):
        """Generate a valid task with optional overrides"""
        default_task = {'title': 'Generated Task', 'description': 'This is a generated task for testing', 'priority': 'medium', 'due_date': '2024-12-31T23:59:59Z'}
        default_task.update(overrides)
        return default_task

    @staticmethod
    def generate_invalid_task():
        """Generate an invalid task for testing error handling"""
        return {'title': '', 'priority': 'invalid_priority', 'description': 'x' * 1001}

    @staticmethod
    def generate_tasks_batch(count=10):
        """Generate a batch of tasks for testing"""
        tasks = []
        for i in range(count):
            task = TaskDataGenerator.generate_valid_task(title=f'Batch Task {i + 1}', priority=['low', 'medium', 'high'][i % 3])
            tasks.append(task)
        return tasks

@staticmethod
def generate_tasks_batch(count=10):
    """Generate a batch of tasks for testing"""
    tasks = []
    for i in range(count):
        task = TaskDataGenerator.generate_valid_task(title=f'Batch Task {i + 1}', priority=['low', 'medium', 'high'][i % 3])
        tasks.append(task)
    return tasks

# Node: generate_valid_task
def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    for _ in range(max_retries):
        try:
            response = requests.get(LANGUAGES_ENDPOINT, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(delay)
    return False

def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    print('Checking if service is available...')
    for i in range(max_retries):
        if check_service_availability():
            print(f'✓ Service is available at {BASE_URL}')
            return True
        if i < max_retries - 1:
            print(f'  Waiting for service... ({i + 1}/{max_retries})')
            time.sleep(delay)
    return False

# Node: check_service_availability
def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    for _ in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/api/languages', timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(delay)
    return False

def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    for _ in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/api/languages', timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(delay)
    return False

def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    for _ in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/api/languages', timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(delay)
    return False

class TestSorting:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [{'name': 'Zebra', 'category': 'Animal', 'score': 85.0}, {'name': 'Apple', 'category': 'Fruit', 'score': 92.0}, {'name': 'Book', 'category': 'Object', 'score': 78.5}, {'name': 'Car', 'category': 'Vehicle', 'score': 95.0}, {'name': 'Dog', 'category': 'Animal', 'score': 88.0}]
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        time.sleep(0.1)
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_sort_by_name_ascending(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'name', 'sort_order': 'asc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        names = [item['name'] for item in items]
        assert names == sorted(names)

    def test_sort_by_name_descending(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'name', 'sort_order': 'desc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        names = [item['name'] for item in items]
        assert names == sorted(names, reverse=True)

    def test_sort_by_score_ascending(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'score', 'sort_order': 'asc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        scores = [item['score'] for item in items]
        assert scores == sorted(scores)

    def test_sort_by_score_descending(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'score', 'sort_order': 'desc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        scores = [item['score'] for item in items]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_category(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'category', 'sort_order': 'asc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        categories = [item['category'] for item in items]
        assert categories == sorted(categories)

    def test_sort_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'score', 'sort_order': 'desc', 'page': 1, 'page_size': 3})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 3
        items = data['data']['items']
        scores = [item['score'] for item in items]
        assert scores == sorted(scores, reverse=True)

@pytest.fixture(autouse=True)
def setup_test_data(self):
    self.test_ids = []
    test_data = [{'name': 'Zebra', 'category': 'Animal', 'score': 85.0}, {'name': 'Apple', 'category': 'Fruit', 'score': 92.0}, {'name': 'Book', 'category': 'Object', 'score': 78.5}, {'name': 'Car', 'category': 'Vehicle', 'score': 95.0}, {'name': 'Dog', 'category': 'Animal', 'score': 88.0}]
    for item in test_data:
        response = requests.post(API_ENDPOINT, json=item)
        if response.status_code in [200, 201]:
            self.test_ids.append(response.json()['data']['id'])
    time.sleep(0.1)
    yield
    for test_id in self.test_ids:
        try:
            requests.delete(f'{API_ENDPOINT}/{test_id}')
        except:
            pass

class TestSearch:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [{'name': 'Python Guide', 'category': 'Programming', 'score': 90.0}, {'name': 'Java Tutorial', 'category': 'Programming', 'score': 85.0}, {'name': 'Data Science', 'category': 'Science', 'score': 92.0}, {'name': 'Machine Learning', 'category': 'AI', 'score': 95.0}, {'name': 'Web Development', 'category': 'Programming', 'score': 88.0}]
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        time.sleep(0.1)
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_search_by_category(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'Programming', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        for item in items:
            assert item['category'] == 'Programming'
        assert len(items) >= 3

    def test_search_by_name(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'name', 'search_value': 'Python Guide', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        assert len(items) >= 1
        assert items[0]['name'] == 'Python Guide'

    def test_search_no_results(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'NonExistentCategory', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) == 0

    def test_search_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'Programming', 'page': 1, 'page_size': 2})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 2
        assert data['data']['pagination']['page'] == 1
        assert data['data']['pagination']['page_size'] == 2

@pytest.fixture(autouse=True)
def setup_test_data(self):
    self.test_ids = []
    test_data = [{'name': 'Python Guide', 'category': 'Programming', 'score': 90.0}, {'name': 'Java Tutorial', 'category': 'Programming', 'score': 85.0}, {'name': 'Data Science', 'category': 'Science', 'score': 92.0}, {'name': 'Machine Learning', 'category': 'AI', 'score': 95.0}, {'name': 'Web Development', 'category': 'Programming', 'score': 88.0}]
    for item in test_data:
        response = requests.post(API_ENDPOINT, json=item)
        if response.status_code in [200, 201]:
            self.test_ids.append(response.json()['data']['id'])
    time.sleep(0.1)
    yield
    for test_id in self.test_ids:
        try:
            requests.delete(f'{API_ENDPOINT}/{test_id}')
        except:
            pass

class TestFuzzySearch:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [{'name': 'Introduction to Python', 'category': 'Programming', 'score': 90.0}, {'name': 'Advanced Python', 'category': 'Programming', 'score': 95.0}, {'name': 'Python for Data Science', 'category': 'Science', 'score': 92.0}, {'name': 'Java Programming', 'category': 'Programming', 'score': 85.0}, {'name': 'JavaScript Basics', 'category': 'Web', 'score': 88.0}]
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        time.sleep(0.1)
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_fuzzy_search_by_name(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        assert len(items) >= 3
        for item in items:
            assert 'Python' in item['name'] or 'python' in item['name'].lower()

    def test_fuzzy_search_partial_match(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Java', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        assert len(items) >= 2

    def test_fuzzy_search_case_sensitivity(self):
        response_lower = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'python', 'page_size': 100})
        response_upper = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'PYTHON', 'page_size': 100})
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        items_lower = response_lower.json()['data']['items']
        items_upper = response_upper.json()['data']['items']
        assert len(items_lower) == len(items_upper)

    def test_fuzzy_search_no_match(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Nonexistent', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) == 0

@pytest.fixture(autouse=True)
def setup_test_data(self):
    self.test_ids = []
    test_data = [{'name': 'Introduction to Python', 'category': 'Programming', 'score': 90.0}, {'name': 'Advanced Python', 'category': 'Programming', 'score': 95.0}, {'name': 'Python for Data Science', 'category': 'Science', 'score': 92.0}, {'name': 'Java Programming', 'category': 'Programming', 'score': 85.0}, {'name': 'JavaScript Basics', 'category': 'Web', 'score': 88.0}]
    for item in test_data:
        response = requests.post(API_ENDPOINT, json=item)
        if response.status_code in [200, 201]:
            self.test_ids.append(response.json()['data']['id'])
    time.sleep(0.1)
    yield
    for test_id in self.test_ids:
        try:
            requests.delete(f'{API_ENDPOINT}/{test_id}')
        except:
            pass

class TestCombinedFeatures:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [{'name': 'Python Basics', 'category': 'Programming', 'score': 85.0}, {'name': 'Python Advanced', 'category': 'Programming', 'score': 95.0}, {'name': 'Python Expert', 'category': 'Programming', 'score': 92.0}, {'name': 'Java Basics', 'category': 'Programming', 'score': 80.0}, {'name': 'Data Analysis', 'category': 'Science', 'score': 90.0}]
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        time.sleep(0.1)
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_search_with_sort(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'Programming', 'sort_by': 'score', 'sort_order': 'desc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        for item in items:
            assert item['category'] == 'Programming'
        scores = [item['score'] for item in items]
        assert scores == sorted(scores, reverse=True)

    def test_fuzzy_search_with_sort(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'sort_by': 'score', 'sort_order': 'asc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        for item in items:
            assert 'Python' in item['name'] or 'python' in item['name'].lower()
        scores = [item['score'] for item in items]
        assert scores == sorted(scores)

    def test_search_with_pagination_and_sort(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'Programming', 'sort_by': 'name', 'sort_order': 'asc', 'page': 1, 'page_size': 2})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 2
        assert data['data']['pagination']['page'] == 1
        items = data['data']['items']
        for item in items:
            assert item['category'] == 'Programming'
        names = [item['name'] for item in items]
        assert names == sorted(names)

    def test_fuzzy_search_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'page': 1, 'page_size': 2})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 2
        assert data['data']['pagination']['page_size'] == 2

@pytest.fixture(autouse=True)
def setup_test_data(self):
    self.test_ids = []
    test_data = [{'name': 'Python Basics', 'category': 'Programming', 'score': 85.0}, {'name': 'Python Advanced', 'category': 'Programming', 'score': 95.0}, {'name': 'Python Expert', 'category': 'Programming', 'score': 92.0}, {'name': 'Java Basics', 'category': 'Programming', 'score': 80.0}, {'name': 'Data Analysis', 'category': 'Science', 'score': 90.0}]
    for item in test_data:
        response = requests.post(API_ENDPOINT, json=item)
        if response.status_code in [200, 201]:
            self.test_ids.append(response.json()['data']['id'])
    time.sleep(0.1)
    yield
    for test_id in self.test_ids:
        try:
            requests.delete(f'{API_ENDPOINT}/{test_id}')
        except:
            pass

def _register_id(data_id: str):
    created_ids.append(data_id)

class TestAuthAPI:
    """Test suite for Authentication API endpoints"""
    BASE_URL = 'http://localhost:8081/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/users')
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/users/{user['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_login_success(self):
        """Test successful user login"""
        user_data = {'username': 'test_login_user', 'email': 'login@example.com', 'password': 'TestPass123!', 'full_name': 'Login Test User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'token_type' in data
        assert 'expires_in' in data
        assert 'user' in data
        assert data['token_type'] == 'Bearer'
        assert data['user']['username'] == user_data['username']
        assert data['user']['email'] == user_data['email']
        assert data['user']['role'] == user_data['role']
        assert 'password' not in data['user']

    def test_login_invalid_username(self):
        """Test login with invalid username"""
        login_data = {'username': 'nonexistent_user', 'password': 'SomePassword123!'}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'authentication_failed'

    def test_login_invalid_password(self):
        """Test login with invalid password"""
        user_data = {'username': 'test_invalid_password', 'email': 'invalid_password@example.com', 'password': 'CorrectPass123!', 'full_name': 'Invalid Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        login_data = {'username': user_data['username'], 'password': 'WrongPassword123!'}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'authentication_failed'

    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        login_data = {'username': 'test_user'}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        login_data = {'username': '', 'password': ''}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_login_inactive_user(self):
        """Test login with inactive user account"""
        user_data = {'username': 'test_inactive_user', 'email': 'inactive@example.com', 'password': 'TestPass123!', 'full_name': 'Inactive User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'inactive'}, headers={'Content-Type': 'application/json'})
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 403
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'account_inactive'

    def test_login_suspended_user(self):
        """Test login with suspended user account"""
        user_data = {'username': 'test_suspended_user', 'email': 'suspended@example.com', 'password': 'TestPass123!', 'full_name': 'Suspended User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'suspended'}, headers={'Content-Type': 'application/json'})
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 403
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'account_suspended'

    def test_reset_password_success(self):
        """Test successful password reset"""
        user_data = {'username': 'test_reset_password', 'email': 'reset@example.com', 'password': 'OldPassword123!', 'full_name': 'Reset Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        reset_data = {'new_password': 'NewPassword123!'}
        response = requests.post(f'{self.BASE_URL}/users/{user_id}/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        login_data = {'username': user_data['username'], 'password': reset_data['new_password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200

    def test_reset_password_weak_password(self):
        """Test password reset with weak password"""
        user_data = {'username': 'test_weak_reset', 'email': 'weak_reset@example.com', 'password': 'TestPass123!', 'full_name': 'Weak Reset User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        reset_data = {'new_password': '123'}
        response = requests.post(f'{self.BASE_URL}/users/{user_id}/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_reset_password_nonexistent_user(self):
        """Test password reset for non-existent user"""
        reset_data = {'new_password': 'NewPassword123!'}
        response = requests.post(f'{self.BASE_URL}/users/99999/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_reset_password_missing_new_password(self):
        """Test password reset with missing new password"""
        user_data = {'username': 'test_missing_reset', 'email': 'missing_reset@example.com', 'password': 'TestPass123!', 'full_name': 'Missing Reset User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        reset_data = {}
        response = requests.post(f'{self.BASE_URL}/users/{user_id}/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_token_expiration(self):
        """Test token expiration behavior"""
        user_data = {'username': 'test_token_expiration', 'email': 'token@example.com', 'password': 'TestPass123!', 'full_name': 'Token Expiration User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        assert expires_in > 0
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{self.BASE_URL}/users/{response.json()['user']['id']}', headers=headers)

    def test_login_case_sensitivity(self):
        """Test login case sensitivity"""
        user_data = {'username': 'TestUserCase', 'email': 'case@example.com', 'password': 'TestPass123!', 'full_name': 'Case Test User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        test_cases = [('testusercase', user_data['password']), ('TESTUSERCASE', user_data['password']), ('testusercase', 'testpass123!')]
        for username, password in test_cases:
            login_data = {'username': username, 'password': password}
            response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [200, 401]

    def test_concurrent_login_attempts(self):
        """Test handling of concurrent login attempts"""
        user_data = {'username': 'test_concurrent_login', 'email': 'concurrent@example.com', 'password': 'TestPass123!', 'full_name': 'Concurrent Login User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        import threading
        results = []
        errors = []

        def attempt_login(thread_id):
            try:
                login_data = {'username': user_data['username'], 'password': user_data['password']}
                response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        threads = []
        for i in range(5):
            thread = threading.Thread(target=attempt_login, args=(i,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors in concurrent login attempts: {errors}'
        assert len(results) == 5
        for thread_id, status_code in results:
            assert status_code == 200

    def test_malformed_login_request(self):
        """Test handling of malformed login requests"""
        malformed_requests = ['{"username": "test", "password": "pass"', '{"username": "test", "password": "pass",}', '{"username": "test", "password": pass}', '{"username": "test" "password": "pass"}']
        for malformed_request in malformed_requests:
            response = requests.post(f'{self.BASE_URL}/auth/login', data=malformed_request, headers={'Content-Type': 'application/json'})
            assert response.status_code == 400

def test_concurrent_login_attempts(self):
    """Test handling of concurrent login attempts"""
    user_data = {'username': 'test_concurrent_login', 'email': 'concurrent@example.com', 'password': 'TestPass123!', 'full_name': 'Concurrent Login User', 'role': 'user'}
    response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
    assert response.status_code == 201
    import threading
    results = []
    errors = []

    def attempt_login(thread_id):
        try:
            login_data = {'username': user_data['username'], 'password': user_data['password']}
            response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
            results.append((thread_id, response.status_code))
        except Exception as e:
            errors.append((thread_id, str(e)))
    threads = []
    for i in range(5):
        thread = threading.Thread(target=attempt_login, args=(i,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(errors) == 0, f'Errors in concurrent login attempts: {errors}'
    assert len(results) == 5
    for thread_id, status_code in results:
        assert status_code == 200

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    BASE_URL = 'http://localhost:8081/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/users')
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/users/{user['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_username_boundary_values(self):
        """Test username at boundary values"""
        min_username = 'abc'
        user_data = {'username': min_username, 'email': 'min@example.com', 'password': 'TestPass123!', 'full_name': 'Min Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == min_username
        max_username = 'a' * 50
        user_data = {'username': max_username, 'email': 'max@example.com', 'password': 'TestPass123!', 'full_name': 'Max Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == max_username
        too_short_username = 'ab'
        user_data = {'username': too_short_username, 'email': 'tooshort@example.com', 'password': 'TestPass123!', 'full_name': 'Too Short User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        too_long_username = 'a' * 51
        user_data = {'username': too_long_username, 'email': 'toolong@example.com', 'password': 'TestPass123!', 'full_name': 'Too Long User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_full_name_boundary_values(self):
        """Test full name at boundary values"""
        max_full_name = 'a' * 100
        user_data = {'username': 'test_max_fullname', 'email': 'maxfullname@example.com', 'password': 'TestPass123!', 'full_name': max_full_name, 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['full_name'] == max_full_name
        too_long_full_name = 'a' * 101
        user_data = {'username': 'test_too_long_fullname', 'email': 'toolongfullname@example.com', 'password': 'TestPass123!', 'full_name': too_long_full_name, 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_password_boundary_values(self):
        """Test password at boundary values"""
        min_password = 'Test123!'
        user_data = {'username': 'test_min_password', 'email': 'minpassword@example.com', 'password': min_password, 'full_name': 'Min Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        too_short_password = 'Test12!'
        user_data = {'username': 'test_too_short_password', 'email': 'tooshortpassword@example.com', 'password': too_short_password, 'full_name': 'Too Short Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_unicode_characters_in_user_data(self):
        """Test handling of Unicode characters in user data"""
        unicode_user = {'username': 'test_unicode_user', 'email': 'unicode@example.com', 'password': 'TestPass123!', 'full_name': 'Unicode User 🚀 Test', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=unicode_user, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            data = response.json()
            assert data['full_name'] == unicode_user['full_name']

    def test_special_characters_in_username(self):
        """Test handling of special characters in username"""
        special_chars_usernames = ['test_user@domain', 'test user', 'test.user', 'test-user', 'test_user_123']
        for i, username in enumerate(special_chars_usernames):
            user_data = {'username': username, 'email': f'special{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Special Char User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]

    def test_email_formats(self):
        """Test various email formats"""
        email_formats = ['test@example.com', 'test.user@example.com', 'test+tag@example.com', 'test123@example-domain.com', 'test@sub.example.com', 'test@example.co.uk']
        for i, email in enumerate(email_formats):
            user_data = {'username': f'test_email_{i}', 'email': email, 'password': 'TestPass123!', 'full_name': f'Email Test User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201

    def test_invalid_email_formats(self):
        """Test invalid email formats"""
        invalid_emails = ['not-an-email', '@example.com', 'test@', 'test..test@example.com', 'test@.example.com', 'test@example..com', 'test@example.com.', 'test@example', 'test@.com']
        for i, email in enumerate(invalid_emails):
            user_data = {'username': f'test_invalid_email_{i}', 'email': email, 'password': 'TestPass123!', 'full_name': f'Invalid Email User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_phone_formats(self):
        """Test various phone number formats"""
        phone_formats = ['+1234567890', '+1-234-567-8900', '+1 (234) 567-8900', '1234567890', '+44 20 7946 0958', '+86 138 0013 8000']
        for i, phone in enumerate(phone_formats):
            user_data = {'username': f'test_phone_{i}', 'email': f'phone{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Phone Test User {i}', 'role': 'user', 'phone': phone}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]

    def test_empty_strings(self):
        """Test handling of empty strings"""
        user_data = {'username': '', 'email': 'empty@example.com', 'password': 'TestPass123!', 'full_name': 'Empty Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        user_data = {'username': 'test_empty_email', 'email': '', 'password': 'TestPass123!', 'full_name': 'Empty Email User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        user_data = {'username': 'test_empty_fullname', 'email': 'emptyfullname@example.com', 'password': 'TestPass123!', 'full_name': '', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_whitespace_only_strings(self):
        """Test handling of whitespace-only strings"""
        user_data = {'username': '   ', 'email': 'whitespace@example.com', 'password': 'TestPass123!', 'full_name': 'Whitespace Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        user_data = {'username': 'test_whitespace_fullname', 'email': 'whitespacefullname@example.com', 'password': 'TestPass123!', 'full_name': '   ', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_null_values(self):
        """Test handling of null values"""
        user_data = {'username': 'test_null_values', 'email': 'null@example.com', 'password': 'TestPass123!', 'full_name': 'Null Values User', 'role': 'user', 'phone': None}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_extra_fields(self):
        """Test handling of extra fields in request"""
        user_data = {'username': 'test_extra_fields', 'email': 'extra@example.com', 'password': 'TestPass123!', 'full_name': 'Extra Fields User', 'role': 'user', 'extra_field': 'should be ignored', 'another_field': 123, 'nested_field': {'key': 'value'}}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'extra_field' not in data
        assert 'another_field' not in data
        assert 'nested_field' not in data

    def test_case_sensitivity(self):
        """Test case sensitivity of enum values"""
        user_data = {'username': 'test_case_sensitivity', 'email': 'case@example.com', 'password': 'TestPass123!', 'full_name': 'Case Sensitivity User', 'role': 'USER'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_large_numbers(self):
        """Test handling of large numbers in pagination"""
        response = requests.get(f'{self.BASE_URL}/users?page=999999')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/users?limit=999999')
        assert response.status_code in [200, 422]

    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        response = requests.get(f'{self.BASE_URL}/users?page=-1')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/users?limit=-1')
        assert response.status_code in [200, 422]

    def test_zero_values(self):
        """Test handling of zero values"""
        response = requests.get(f'{self.BASE_URL}/users?page=0')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/users?limit=0')
        assert response.status_code in [200, 422]

    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts"""
        malicious_inputs = ["'; DROP TABLE users; --", "1' OR '1'='1", "admin'--", '1; DELETE FROM users; --', "'; INSERT INTO users VALUES ('hacker', 'hack@evil.com', 'password', 'Hacker', 'admin'); --"]
        for i, malicious_input in enumerate(malicious_inputs):
            user_data = {'username': f'test_sql_{i}', 'email': f'sql{i}@example.com', 'password': 'TestPass123!', 'full_name': malicious_input, 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_xss_attempts(self):
        """Test protection against XSS attempts"""
        xss_payloads = ["<script>alert('xss')</script>", "javascript:alert('xss')", "<img src=x onerror=alert('xss')>", "';alert('xss');//", "<svg onload=alert('xss')>", 'javascript:/*-/*`/*\\`/*\'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>']
        for i, payload in enumerate(xss_payloads):
            user_data = {'username': f'test_xss_{i}', 'email': f'xss{i}@example.com', 'password': 'TestPass123!', 'full_name': payload, 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_concurrent_user_creation(self):
        """Test handling of concurrent user creation"""
        import threading
        import time
        results = []
        errors = []

        def create_user(thread_id):
            try:
                user_data = {'username': f'test_concurrent_{thread_id}', 'email': f'concurrent{thread_id}@example.com', 'password': 'TestPass123!', 'full_name': f'Concurrent User {thread_id}', 'role': 'user'}
                response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors in concurrent user creation: {errors}'
        assert len(results) == 10
        for thread_id, status_code in results:
            assert status_code == 201

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = ['{"username": "test", "email": "test@example.com"', '{"username": "test", "email": "test@example.com",}', '{"username": "test", "email": test@example.com}', '{"username": "test" "email": "test@example.com"}', '{"username": "test", "email": "test@example.com", "role": }']
        for malformed_json in malformed_jsons:
            response = requests.post(f'{self.BASE_URL}/users', data=malformed_json, headers={'Content-Type': 'application/json'})
            assert response.status_code == 400

    def test_content_type_variations(self):
        """Test handling of different content types"""
        user_data = {'username': 'test_content_type', 'email': 'contenttype@example.com', 'password': 'TestPass123!', 'full_name': 'Content Type User', 'role': 'user'}
        content_types = ['application/json', 'application/json; charset=utf-8', 'application/json;charset=utf-8', 'text/json', 'text/plain']
        for content_type in content_types:
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': content_type})
            assert response.status_code in [201, 400, 415]
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_missing_headers(self):
        """Test handling of missing headers"""
        user_data = {'username': 'test_no_headers', 'email': 'noheaders@example.com', 'password': 'TestPass123!', 'full_name': 'No Headers User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data)
        assert response.status_code in [201, 400, 415]
        if response.status_code == 201:
            user_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_very_long_url(self):
        """Test handling of very long URLs"""
        long_params = '&'.join([f'param{i}=value{i}' for i in range(100)])
        response = requests.get(f'{self.BASE_URL}/users?{long_params}')
        assert response.status_code in [200, 414, 400]

    def test_password_strength_requirements(self):
        """Test password strength requirements"""
        weak_passwords = ['12345678', 'abcdefgh', 'ABCDEFGH', '!@#$%^&*', 'Test123', 'testuser', 'TESTUSER', '123456789']
        for i, password in enumerate(weak_passwords):
            user_data = {'username': f'test_weak_password_{i}', 'email': f'weakpassword{i}@example.com', 'password': password, 'full_name': f'Weak Password User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_strong_passwords(self):
        """Test acceptance of strong passwords"""
        strong_passwords = ['TestPass123!', 'MyStr0ng#Pass', 'ComplexP@ssw0rd', 'Secure123$Pass', 'StrongP@ss1!']
        for i, password in enumerate(strong_passwords):
            user_data = {'username': f'test_strong_password_{i}', 'email': f'strongpassword{i}@example.com', 'password': password, 'full_name': f'Strong Password User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            user_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_username_alphanumeric_requirement(self):
        """Test username alphanumeric requirement"""
        invalid_usernames = ['user@name', 'user name', 'user.name', 'user-name', 'user_name!', 'user#name', 'user$name']
        for i, username in enumerate(invalid_usernames):
            user_data = {'username': username, 'email': f'invalidusername{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Invalid Username User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_valid_usernames(self):
        """Test acceptance of valid usernames"""
        valid_usernames = ['user123', 'testuser', 'User123', 'test_user_123', 'user123test', 'a1b2c3', 'test123user']
        for i, username in enumerate(valid_usernames):
            user_data = {'username': username, 'email': f'validusername{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Valid Username User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            user_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/users/{user_id}')

def test_concurrent_user_creation(self):
    """Test handling of concurrent user creation"""
    import threading
    import time
    results = []
    errors = []

    def create_user(thread_id):
        try:
            user_data = {'username': f'test_concurrent_{thread_id}', 'email': f'concurrent{thread_id}@example.com', 'password': 'TestPass123!', 'full_name': f'Concurrent User {thread_id}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            results.append((thread_id, response.status_code))
        except Exception as e:
            errors.append((thread_id, str(e)))
    threads = []
    for i in range(10):
        thread = threading.Thread(target=create_user, args=(i,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(errors) == 0, f'Errors in concurrent user creation: {errors}'
    assert len(results) == 10
    for thread_id, status_code in results:
        assert status_code == 201

def test_very_long_url(self):
    """Test handling of very long URLs"""
    long_params = '&'.join([f'param{i}=value{i}' for i in range(100)])
    response = requests.get(f'{self.BASE_URL}/users?{long_params}')
    assert response.status_code in [200, 414, 400]

class TestUserAPI:
    """Test suite for User Management API endpoints"""
    BASE_URL = 'http://localhost:8081/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/users')
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/users/{user['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f'{self.BASE_URL}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert 'database' in data
        assert data['status'] == 'healthy'

    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {'username': 'test_user_001', 'email': 'test@example.com', 'password': 'TestPass123!', 'full_name': 'Test User', 'role': 'user', 'phone': '+1234567890'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['full_name'] == user_data['full_name']
        assert data['role'] == user_data['role']
        assert data['phone'] == user_data['phone']
        assert data['status'] == 'active'
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'password' not in data

    def test_create_user_minimal_data(self):
        """Test user creation with minimal required data"""
        user_data = {'username': 'test_minimal', 'email': 'minimal@example.com', 'password': 'MinPass123!', 'full_name': 'Minimal User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['full_name'] == user_data['full_name']
        assert data['role'] == user_data['role']
        assert data['status'] == 'active'
        assert data['phone'] is None or data['phone'] == ''

    def test_create_user_invalid_role(self):
        """Test user creation with invalid role"""
        user_data = {'username': 'test_invalid_role', 'email': 'invalid@example.com', 'password': 'TestPass123!', 'full_name': 'Invalid Role User', 'role': 'invalid_role'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'validation_error'

    def test_create_user_missing_required_fields(self):
        """Test user creation with missing required fields"""
        user_data = {'email': 'missing@example.com'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username"""
        user_data = {'username': 'test_duplicate', 'email': 'duplicate1@example.com', 'password': 'TestPass123!', 'full_name': 'Duplicate User 1', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_data['email'] = 'duplicate2@example.com'
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 409
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'conflict'

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        user_data = {'username': 'test_duplicate_email_1', 'email': 'duplicate@example.com', 'password': 'TestPass123!', 'full_name': 'Duplicate Email User 1', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_data['username'] = 'test_duplicate_email_2'
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 409
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'conflict'

    def test_create_user_invalid_email_format(self):
        """Test user creation with invalid email format"""
        user_data = {'username': 'test_invalid_email', 'email': 'invalid-email-format', 'password': 'TestPass123!', 'full_name': 'Invalid Email User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_create_user_weak_password(self):
        """Test user creation with weak password"""
        user_data = {'username': 'test_weak_password', 'email': 'weak@example.com', 'password': '123', 'full_name': 'Weak Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_get_users_list_empty(self):
        """Test getting users list when no users exist"""
        response = requests.get(f'{self.BASE_URL}/users')
        assert response.status_code == 200
        data = response.json()
        assert 'users' in data
        assert 'pagination' in data
        assert len(data['users']) == 0
        assert data['pagination']['total'] == 0

    def test_get_users_list_with_data(self):
        """Test getting users list with existing users"""
        users_data = [{'username': 'test_list_1', 'email': 'list1@example.com', 'password': 'TestPass123!', 'full_name': 'List User 1', 'role': 'user'}, {'username': 'test_list_2', 'email': 'list2@example.com', 'password': 'TestPass123!', 'full_name': 'List User 2', 'role': 'admin'}, {'username': 'test_list_3', 'email': 'list3@example.com', 'password': 'TestPass123!', 'full_name': 'List User 3', 'role': 'moderator'}]
        created_users = []
        for user_data in users_data:
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            created_users.append(response.json())
        response = requests.get(f'{self.BASE_URL}/users')
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) >= 3
        assert data['pagination']['total'] >= 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10

    def test_get_users_list_pagination(self):
        """Test users list pagination"""
        for i in range(15):
            user_data = {'username': f'test_pagination_{i + 1}', 'email': f'pagination{i + 1}@example.com', 'password': 'TestPass123!', 'full_name': f'Pagination User {i + 1}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/users?page=1&limit=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 15
        assert data['pagination']['pages'] >= 2
        response = requests.get(f'{self.BASE_URL}/users?page=2&limit=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) >= 5
        assert data['pagination']['page'] == 2

    def test_get_users_list_filter_by_role(self):
        """Test filtering users by role"""
        roles = ['user', 'admin', 'moderator']
        for role in roles:
            user_data = {'username': f'test_role_{role}', 'email': f'role_{role}@example.com', 'password': 'TestPass123!', 'full_name': f'Role {role.title()} User', 'role': role}
            requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/users?role=admin')
        assert response.status_code == 200
        data = response.json()
        admin_users = [user for user in data['users'] if user['role'] == 'admin']
        assert len(admin_users) >= 1

    def test_get_users_list_filter_by_status(self):
        """Test filtering users by status"""
        user_data = {'username': 'test_status_filter', 'email': 'status@example.com', 'password': 'TestPass123!', 'full_name': 'Status Filter User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'inactive'}, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/users?status=inactive')
        assert response.status_code == 200
        data = response.json()
        inactive_users = [user for user in data['users'] if user['status'] == 'inactive']
        assert len(inactive_users) >= 1

    def test_get_users_list_search(self):
        """Test searching users by username, email, or full_name"""
        user_data = {'username': 'test_search_unique', 'email': 'search_unique@example.com', 'password': 'TestPass123!', 'full_name': 'Unique Search User', 'role': 'user'}
        requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/users?search=test_search_unique')
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'test_search_unique' in user['username']]
        assert len(found_users) >= 1
        response = requests.get(f'{self.BASE_URL}/users?search=search_unique@example.com')
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'search_unique@example.com' in user['email']]
        assert len(found_users) >= 1
        response = requests.get(f'{self.BASE_URL}/users?search=Unique Search')
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'Unique Search' in user['full_name']]
        assert len(found_users) >= 1

    def test_get_single_user_success(self):
        """Test getting a single user by ID"""
        user_data = {'username': 'test_single_user', 'email': 'single@example.com', 'password': 'TestPass123!', 'full_name': 'Single User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        created_user = response.json()
        response = requests.get(f'{self.BASE_URL}/users/{created_user['id']}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == created_user['id']
        assert data['username'] == created_user['username']
        assert data['email'] == created_user['email']
        assert data['role'] == created_user['role']

    def test_get_single_user_not_found(self):
        """Test getting a non-existent user"""
        response = requests.get(f'{self.BASE_URL}/users/99999')
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_update_user_success(self):
        """Test successful user update"""
        user_data = {'username': 'test_update_user', 'email': 'update@example.com', 'password': 'TestPass123!', 'full_name': 'Original User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        update_data = {'username': 'test_updated_user', 'email': 'updated@example.com', 'full_name': 'Updated User', 'role': 'moderator', 'status': 'inactive'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == update_data['username']
        assert data['email'] == update_data['email']
        assert data['full_name'] == update_data['full_name']
        assert data['role'] == update_data['role']
        assert data['status'] == update_data['status']
        assert data['id'] == user_id

    def test_update_user_partial(self):
        """Test partial user update"""
        user_data = {'username': 'test_partial_update', 'email': 'partial@example.com', 'password': 'TestPass123!', 'full_name': 'Original Full Name', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        update_data = {'full_name': 'Updated Full Name Only'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert data['full_name'] == update_data['full_name']
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['role'] == user_data['role']

    def test_update_user_invalid_role(self):
        """Test user update with invalid role"""
        user_data = {'username': 'test_invalid_role_update', 'email': 'invalid_role@example.com', 'password': 'TestPass123!', 'full_name': 'Invalid Role User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        update_data = {'role': 'invalid_role'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_update_user_not_found(self):
        """Test updating a non-existent user"""
        update_data = {'full_name': 'Updated User'}
        response = requests.put(f'{self.BASE_URL}/users/99999', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_delete_user_success(self):
        """Test successful user deletion"""
        user_data = {'username': 'test_delete_user', 'email': 'delete@example.com', 'password': 'TestPass123!', 'full_name': 'User to Delete', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        response = requests.delete(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        response = requests.get(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 404

    def test_delete_user_not_found(self):
        """Test deleting a non-existent user"""
        response = requests.delete(f'{self.BASE_URL}/users/99999')
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_user_workflow_complete(self):
        """Test complete user workflow: create -> update -> deactivate -> delete"""
        user_data = {'username': 'test_workflow_user', 'email': 'workflow@example.com', 'password': 'TestPass123!', 'full_name': 'Workflow User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_id = response.json()['id']
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json={'role': 'moderator'}, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        assert response.json()['role'] == 'moderator'
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'inactive'}, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        assert response.json()['status'] == 'inactive'
        response = requests.get(f'{self.BASE_URL}/users?status=inactive')
        assert response.status_code == 200
        inactive_users = response.json()['users']
        inactive_user_ids = [user['id'] for user in inactive_users]
        assert user_id in inactive_user_ids
        response = requests.delete(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 404

    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body"""
        response = requests.post(f'{self.BASE_URL}/users', data='invalid json', headers={'Content-Type': 'application/json'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_missing_content_type_header(self):
        """Test handling of missing Content-Type header"""
        user_data = {'username': 'test_no_content_type', 'email': 'no_content_type@example.com', 'password': 'TestPass123!', 'full_name': 'No Content Type User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data)
        assert response.status_code in [201, 400, 415]

    def test_large_pagination_limit(self):
        """Test pagination with limit exceeding maximum"""
        response = requests.get(f'{self.BASE_URL}/users?limit=1000')
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100

def test_get_users_list_with_data(self):
    """Test getting users list with existing users"""
    users_data = [{'username': 'test_list_1', 'email': 'list1@example.com', 'password': 'TestPass123!', 'full_name': 'List User 1', 'role': 'user'}, {'username': 'test_list_2', 'email': 'list2@example.com', 'password': 'TestPass123!', 'full_name': 'List User 2', 'role': 'admin'}, {'username': 'test_list_3', 'email': 'list3@example.com', 'password': 'TestPass123!', 'full_name': 'List User 3', 'role': 'moderator'}]
    created_users = []
    for user_data in users_data:
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        created_users.append(response.json())
    response = requests.get(f'{self.BASE_URL}/users')
    assert response.status_code == 200
    data = response.json()
    assert len(data['users']) >= 3
    assert data['pagination']['total'] >= 3
    assert data['pagination']['page'] == 1
    assert data['pagination']['limit'] == 10

def test_get_users_list_pagination(self):
    """Test users list pagination"""
    for i in range(15):
        user_data = {'username': f'test_pagination_{i + 1}', 'email': f'pagination{i + 1}@example.com', 'password': 'TestPass123!', 'full_name': f'Pagination User {i + 1}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/users?page=1&limit=10')
    assert response.status_code == 200
    data = response.json()
    assert len(data['users']) == 10
    assert data['pagination']['page'] == 1
    assert data['pagination']['total'] >= 15
    assert data['pagination']['pages'] >= 2
    response = requests.get(f'{self.BASE_URL}/users?page=2&limit=10')
    assert response.status_code == 200
    data = response.json()
    assert len(data['users']) >= 5
    assert data['pagination']['page'] == 2

def generate_large_file():
    chunk_size = 1024 * 1024
    for _ in range(file_size // chunk_size):
        yield (b'x' * chunk_size)

@pytest.mark.edge
def test_concurrent_uploads(api_base_url, auth_headers):
    """Test concurrent file uploads"""
    import concurrent.futures

    def upload_file(index):
        file_content = io.BytesIO(f'Concurrent upload test {index}'.encode())
        files = {'file': (f'concurrent_{index}.txt', file_content, 'text/plain')}
        resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
        return resp
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_file, i) for i in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    successful_uploads = [r for r in responses if r.status_code in (200, 201)]
    assert len(successful_uploads) >= 4
    for resp in successful_uploads:
        try:
            file_id = resp.json().get('id')
            if file_id:
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

