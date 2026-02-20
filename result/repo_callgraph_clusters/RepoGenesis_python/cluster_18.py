# Cluster 18

# Node: json
# Node: post
# Node: put
# Node: delete
class TestTaskExecution:

    def test_manual_execute_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        response = api_client.post(f'/tasks/{task_id}/execute')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'data' in result
        data = result['data']
        assert 'execution_id' in data
        assert data['task_id'] == task_id
        assert data['status'] in ['running', 'completed', 'failed']
        assert 'started_at' in data

    def test_execute_disabled_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_backup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        response = api_client.post(f'/tasks/{task_id}/execute')
        assert response.status_code in [200, 400]
        result = response.json()
        if response.status_code == 200:
            assert result['success'] is True
            assert 'execution_id' in result['data']
        else:
            assert result['success'] is False

    def test_execute_nonexistent_task(self, api_client):
        response = api_client.post('/tasks/nonexistent_task_id/execute')
        assert response.status_code == 404
        result = response.json()
        assert result['success'] is False

    @pytest.mark.slow
    def test_concurrent_task_execution(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_summary']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        response1 = api_client.post(f'/tasks/{task_id}/execute')
        response2 = api_client.post(f'/tasks/{task_id}/execute')
        assert response1.status_code == 200
        assert response2.status_code == 200
        execution_id1 = response1.json()['data']['execution_id']
        execution_id2 = response2.json()['data']['execution_id']
        assert execution_id1 != execution_id2

def test_manual_execute_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    response = api_client.post(f'/tasks/{task_id}/execute')
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert 'data' in result
    data = result['data']
    assert 'execution_id' in data
    assert data['task_id'] == task_id
    assert data['status'] in ['running', 'completed', 'failed']
    assert 'started_at' in data

def test_execute_disabled_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_backup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    response = api_client.post(f'/tasks/{task_id}/execute')
    assert response.status_code in [200, 400]
    result = response.json()
    if response.status_code == 200:
        assert result['success'] is True
        assert 'execution_id' in result['data']
    else:
        assert result['success'] is False

def test_execute_nonexistent_task(self, api_client):
    response = api_client.post('/tasks/nonexistent_task_id/execute')
    assert response.status_code == 404
    result = response.json()
    assert result['success'] is False

@pytest.mark.slow
def test_concurrent_task_execution(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_summary']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    response1 = api_client.post(f'/tasks/{task_id}/execute')
    response2 = api_client.post(f'/tasks/{task_id}/execute')
    assert response1.status_code == 200
    assert response2.status_code == 200
    execution_id1 = response1.json()['data']['execution_id']
    execution_id2 = response2.json()['data']['execution_id']
    assert execution_id1 != execution_id2

class TestFileCleanupTask:

    def test_create_file_cleanup_task_with_full_config(self, api_client, cleanup_tasks):
        task_data = {'name': 'Clean log files', 'description': 'Clean log files older than 30 days', 'task_type': 'file_cleanup', 'schedule': '0 3 * * *', 'config': {'path': '/var/log/app', 'pattern': '*.log', 'days': 30}, 'enabled': True}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        assert result['success'] is True
        assert result['data']['task_type'] == 'file_cleanup'
        cleanup_tasks.append(result['data']['task_id'])

    def test_file_cleanup_task_missing_path(self, api_client):
        task_data = {'name': 'Clean tmp files', 'task_type': 'file_cleanup', 'schedule': '0 3 * * *', 'config': {'pattern': '*.tmp', 'days': 7}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code in [201, 400]
        if response.status_code == 400:
            result = response.json()
            assert result['success'] is False

    def test_file_cleanup_task_with_different_patterns(self, api_client, cleanup_tasks):
        patterns = ['*.tmp', '*.log', '*.bak', 'temp_*']
        for pattern in patterns:
            task_data = {'name': f'Clean {pattern} files', 'task_type': 'file_cleanup', 'schedule': '0 4 * * *', 'config': {'path': '/tmp', 'pattern': pattern, 'days': 7}}
            response = api_client.post('/tasks', data=task_data)
            assert response.status_code == 201
            result = response.json()
            cleanup_tasks.append(result['data']['task_id'])

def test_create_file_cleanup_task_with_full_config(self, api_client, cleanup_tasks):
    task_data = {'name': 'Clean log files', 'description': 'Clean log files older than 30 days', 'task_type': 'file_cleanup', 'schedule': '0 3 * * *', 'config': {'path': '/var/log/app', 'pattern': '*.log', 'days': 30}, 'enabled': True}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    assert result['success'] is True
    assert result['data']['task_type'] == 'file_cleanup'
    cleanup_tasks.append(result['data']['task_id'])

def test_file_cleanup_task_missing_path(self, api_client):
    task_data = {'name': 'Clean tmp files', 'task_type': 'file_cleanup', 'schedule': '0 3 * * *', 'config': {'pattern': '*.tmp', 'days': 7}}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code in [201, 400]
    if response.status_code == 400:
        result = response.json()
        assert result['success'] is False

def test_file_cleanup_task_with_different_patterns(self, api_client, cleanup_tasks):
    patterns = ['*.tmp', '*.log', '*.bak', 'temp_*']
    for pattern in patterns:
        task_data = {'name': f'Clean {pattern} files', 'task_type': 'file_cleanup', 'schedule': '0 4 * * *', 'config': {'path': '/tmp', 'pattern': pattern, 'days': 7}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result['data']['task_id'])

class TestDataSummaryTask:

    def test_create_data_summary_task_with_full_config(self, api_client, cleanup_tasks):
        task_data = {'name': 'Daily sales summary', 'description': 'Daily sales data summary', 'task_type': 'data_summary', 'schedule': '0 22 * * *', 'config': {'source': 'sales_records', 'target': 'daily_sales_summary'}, 'enabled': True}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        assert result['success'] is True
        assert result['data']['task_type'] == 'data_summary'
        cleanup_tasks.append(result['data']['task_id'])

    def test_data_summary_task_weekly_schedule(self, api_client, cleanup_tasks):
        task_data = {'name': 'Weekly report summary', 'task_type': 'data_summary', 'schedule': '0 9 * * 1', 'config': {'source': 'weekly_data', 'target': 'weekly_report'}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result['data']['task_id'])

    def test_data_summary_task_monthly_schedule(self, api_client, cleanup_tasks):
        task_data = {'name': 'Monthly report summary', 'task_type': 'data_summary', 'schedule': '0 0 1 * *', 'config': {'source': 'monthly_data', 'target': 'monthly_report'}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result['data']['task_id'])

def test_create_data_summary_task_with_full_config(self, api_client, cleanup_tasks):
    task_data = {'name': 'Daily sales summary', 'description': 'Daily sales data summary', 'task_type': 'data_summary', 'schedule': '0 22 * * *', 'config': {'source': 'sales_records', 'target': 'daily_sales_summary'}, 'enabled': True}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    assert result['success'] is True
    assert result['data']['task_type'] == 'data_summary'
    cleanup_tasks.append(result['data']['task_id'])

def test_data_summary_task_weekly_schedule(self, api_client, cleanup_tasks):
    task_data = {'name': 'Weekly report summary', 'task_type': 'data_summary', 'schedule': '0 9 * * 1', 'config': {'source': 'weekly_data', 'target': 'weekly_report'}}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    cleanup_tasks.append(result['data']['task_id'])

def test_data_summary_task_monthly_schedule(self, api_client, cleanup_tasks):
    task_data = {'name': 'Monthly report summary', 'task_type': 'data_summary', 'schedule': '0 0 1 * *', 'config': {'source': 'monthly_data', 'target': 'monthly_report'}}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    cleanup_tasks.append(result['data']['task_id'])

class TestDataBackupTask:

    def test_create_data_backup_task_with_full_config(self, api_client, cleanup_tasks):
        task_data = {'name': 'Database full backup', 'description': 'Daily database full backup at 2 AM', 'task_type': 'data_backup', 'schedule': '0 2 * * *', 'config': {'source': 'mysql_database', 'target': '/backup/mysql/full'}, 'enabled': True}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        assert result['success'] is True
        assert result['data']['task_type'] == 'data_backup'
        cleanup_tasks.append(result['data']['task_id'])

    def test_data_backup_task_incremental(self, api_client, cleanup_tasks):
        task_data = {'name': 'Incremental backup', 'task_type': 'data_backup', 'schedule': '0 */4 * * *', 'config': {'source': 'database', 'target': '/backup/incremental', 'backup_type': 'incremental'}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result['data']['task_id'])

    def test_data_backup_task_missing_target(self, api_client):
        task_data = {'name': 'Backup task', 'task_type': 'data_backup', 'schedule': '0 2 * * *', 'config': {'source': 'database'}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code in [201, 400]

def test_create_data_backup_task_with_full_config(self, api_client, cleanup_tasks):
    task_data = {'name': 'Database full backup', 'description': 'Daily database full backup at 2 AM', 'task_type': 'data_backup', 'schedule': '0 2 * * *', 'config': {'source': 'mysql_database', 'target': '/backup/mysql/full'}, 'enabled': True}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    assert result['success'] is True
    assert result['data']['task_type'] == 'data_backup'
    cleanup_tasks.append(result['data']['task_id'])

def test_data_backup_task_incremental(self, api_client, cleanup_tasks):
    task_data = {'name': 'Incremental backup', 'task_type': 'data_backup', 'schedule': '0 */4 * * *', 'config': {'source': 'database', 'target': '/backup/incremental', 'backup_type': 'incremental'}}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    cleanup_tasks.append(result['data']['task_id'])

def test_data_backup_task_missing_target(self, api_client):
    task_data = {'name': 'Backup task', 'task_type': 'data_backup', 'schedule': '0 2 * * *', 'config': {'source': 'database'}}
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code in [201, 400]

class TestTaskTypeValidation:

    def test_all_valid_task_types(self, api_client, cleanup_tasks):
        valid_types = ['file_cleanup', 'data_summary', 'data_backup']
        for task_type in valid_types:
            task_data = {'name': f'Test{task_type}', 'task_type': task_type, 'schedule': '0 0 * * *', 'config': {}}
            response = api_client.post('/tasks', data=task_data)
            assert response.status_code in [201, 400]
            if response.status_code == 201:
                result = response.json()
                cleanup_tasks.append(result['data']['task_id'])

    def test_invalid_task_types(self, api_client):
        invalid_types = ['invalid_type', 'file_delete', 'data_export', '', 'FILE_CLEANUP', 'file-cleanup']
        for task_type in invalid_types:
            task_data = {'name': 'Test task', 'task_type': task_type, 'schedule': '0 0 * * *', 'config': {}}
            response = api_client.post('/tasks', data=task_data)
            assert response.status_code == 400
            result = response.json()
            assert result['success'] is False

def test_all_valid_task_types(self, api_client, cleanup_tasks):
    valid_types = ['file_cleanup', 'data_summary', 'data_backup']
    for task_type in valid_types:
        task_data = {'name': f'Test{task_type}', 'task_type': task_type, 'schedule': '0 0 * * *', 'config': {}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            result = response.json()
            cleanup_tasks.append(result['data']['task_id'])

def test_invalid_task_types(self, api_client):
    invalid_types = ['invalid_type', 'file_delete', 'data_export', '', 'FILE_CLEANUP', 'file-cleanup']
    for task_type in invalid_types:
        task_data = {'name': 'Test task', 'task_type': task_type, 'schedule': '0 0 * * *', 'config': {}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 400
        result = response.json()
        assert result['success'] is False

class TestCronScheduleValidation:

    def test_valid_cron_expressions(self, api_client, cleanup_tasks):
        valid_crons = ['0 0 * * *', '0 */2 * * *', '30 3 * * 1', '0 0 1 * *', '*/5 * * * *', '0 9-17 * * 1-5']
        for cron in valid_crons:
            task_data = {'name': f'Test cron: {cron}', 'task_type': 'file_cleanup', 'schedule': cron, 'config': {'path': '/tmp', 'pattern': '*.tmp', 'days': 7}}
            response = api_client.post('/tasks', data=task_data)
            assert response.status_code == 201
            result = response.json()
            cleanup_tasks.append(result['data']['task_id'])

    def test_invalid_cron_expressions(self, api_client):
        invalid_crons = ['invalid', '* * * *', '60 0 * * *', '0 25 * * *', '0 0 32 * *', '0 0 * 13 *', '0 0 * * 7', '']
        for cron in invalid_crons:
            task_data = {'name': 'Test task', 'task_type': 'file_cleanup', 'schedule': cron, 'config': {'path': '/tmp', 'pattern': '*.tmp', 'days': 7}}
            response = api_client.post('/tasks', data=task_data)
            assert response.status_code == 400
            result = response.json()
            assert result['success'] is False

def test_valid_cron_expressions(self, api_client, cleanup_tasks):
    valid_crons = ['0 0 * * *', '0 */2 * * *', '30 3 * * 1', '0 0 1 * *', '*/5 * * * *', '0 9-17 * * 1-5']
    for cron in valid_crons:
        task_data = {'name': f'Test cron: {cron}', 'task_type': 'file_cleanup', 'schedule': cron, 'config': {'path': '/tmp', 'pattern': '*.tmp', 'days': 7}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result['data']['task_id'])

def test_invalid_cron_expressions(self, api_client):
    invalid_crons = ['invalid', '* * * *', '60 0 * * *', '0 25 * * *', '0 0 32 * *', '0 0 * 13 *', '0 0 * * 7', '']
    for cron in invalid_crons:
        task_data = {'name': 'Test task', 'task_type': 'file_cleanup', 'schedule': cron, 'config': {'path': '/tmp', 'pattern': '*.tmp', 'days': 7}}
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 400
        result = response.json()
        assert result['success'] is False

class TestTaskCreation:

    def test_create_file_cleanup_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201, f'Init task failed: {response.text}'
        result = response.json()
        assert result['success'] is True
        assert 'data' in result
        data = result['data']
        assert 'task_id' in data
        assert data['name'] == task_data['name']
        assert data['task_type'] == task_data['task_type']
        assert data['schedule'] == task_data['schedule']
        assert data['enabled'] is True
        assert 'created_at' in data
        cleanup_tasks.append(data['task_id'])

    def test_create_data_summary_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_summary']
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        assert result['success'] is True
        assert result['data']['task_type'] == 'data_summary'
        cleanup_tasks.append(result['data']['task_id'])

    def test_create_data_backup_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_backup']
        response = api_client.post('/tasks', data=task_data)
        assert response.status_code == 201
        result = response.json()
        assert result['success'] is True
        assert result['data']['task_type'] == 'data_backup'
        assert result['data']['enabled'] is False
        cleanup_tasks.append(result['data']['task_id'])

    def test_create_task_with_missing_required_fields(self, api_client):
        invalid_data = {'name': 'Test Task'}
        response = api_client.post('/tasks', data=invalid_data)
        assert response.status_code == 400
        result = response.json()
        assert result['success'] is False

    def test_create_task_with_invalid_task_type(self, api_client):
        invalid_data = {'name': 'Test Task', 'task_type': 'invalid_type', 'schedule': '0 0 * * *'}
        response = api_client.post('/tasks', data=invalid_data)
        assert response.status_code == 400
        result = response.json()
        assert result['success'] is False

    def test_create_task_with_invalid_cron(self, api_client):
        invalid_data = {'name': 'Test Task', 'task_type': 'file_cleanup', 'schedule': 'invalid cron'}
        response = api_client.post('/tasks', data=invalid_data)
        assert response.status_code == 400
        result = response.json()
        assert result['success'] is False

def test_create_file_cleanup_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201, f'Init task failed: {response.text}'
    result = response.json()
    assert result['success'] is True
    assert 'data' in result
    data = result['data']
    assert 'task_id' in data
    assert data['name'] == task_data['name']
    assert data['task_type'] == task_data['task_type']
    assert data['schedule'] == task_data['schedule']
    assert data['enabled'] is True
    assert 'created_at' in data
    cleanup_tasks.append(data['task_id'])

def test_create_data_summary_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_summary']
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    assert result['success'] is True
    assert result['data']['task_type'] == 'data_summary'
    cleanup_tasks.append(result['data']['task_id'])

def test_create_data_backup_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_backup']
    response = api_client.post('/tasks', data=task_data)
    assert response.status_code == 201
    result = response.json()
    assert result['success'] is True
    assert result['data']['task_type'] == 'data_backup'
    assert result['data']['enabled'] is False
    cleanup_tasks.append(result['data']['task_id'])

def test_create_task_with_missing_required_fields(self, api_client):
    invalid_data = {'name': 'Test Task'}
    response = api_client.post('/tasks', data=invalid_data)
    assert response.status_code == 400
    result = response.json()
    assert result['success'] is False

def test_create_task_with_invalid_task_type(self, api_client):
    invalid_data = {'name': 'Test Task', 'task_type': 'invalid_type', 'schedule': '0 0 * * *'}
    response = api_client.post('/tasks', data=invalid_data)
    assert response.status_code == 400
    result = response.json()
    assert result['success'] is False

def test_create_task_with_invalid_cron(self, api_client):
    invalid_data = {'name': 'Test Task', 'task_type': 'file_cleanup', 'schedule': 'invalid cron'}
    response = api_client.post('/tasks', data=invalid_data)
    assert response.status_code == 400
    result = response.json()
    assert result['success'] is False

class TestTaskRetrieval:

    def test_get_all_tasks(self, api_client, sample_task_data, cleanup_tasks):
        for task_type, task_data in sample_task_data.items():
            response = api_client.post('/tasks', data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()['data']['task_id'])
        response = api_client.get('/tasks')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'data' in result
        data = result['data']
        assert 'tasks' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
        assert len(data['tasks']) > 0

    def test_get_tasks_with_filter_by_type(self, api_client, sample_task_data, cleanup_tasks):
        for task_type, task_data in sample_task_data.items():
            response = api_client.post('/tasks', data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()['data']['task_id'])
        response = api_client.get('/tasks', params={'task_type': 'file_cleanup'})
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        tasks = result['data']['tasks']
        for task in tasks:
            assert task['task_type'] == 'file_cleanup'

    def test_get_tasks_with_filter_by_enabled(self, api_client, sample_task_data, cleanup_tasks):
        for task_type, task_data in sample_task_data.items():
            response = api_client.post('/tasks', data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()['data']['task_id'])
        response = api_client.get('/tasks', params={'enabled': True})
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        tasks = result['data']['tasks']
        for task in tasks:
            assert task['enabled'] is True

    def test_get_tasks_with_pagination(self, api_client):
        response = api_client.get('/tasks', params={'page': 1, 'page_size': 5})
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        data = result['data']
        assert data['page'] == 1
        assert data['page_size'] == 5
        assert len(data['tasks']) <= 5

    def test_get_task_by_id(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        assert create_response.status_code == 201
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        response = api_client.get(f'/tasks/{task_id}')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        data = result['data']
        assert data['task_id'] == task_id
        assert data['name'] == task_data['name']
        assert data['description'] == task_data['description']
        assert data['task_type'] == task_data['task_type']
        assert data['schedule'] == task_data['schedule']
        assert 'config' in data
        assert data['enabled'] is True
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_get_nonexistent_task(self, api_client):
        response = api_client.get('/tasks/nonexistent_task_id')
        assert response.status_code == 404
        result = response.json()
        assert result['success'] is False

def test_get_task_by_id(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    assert create_response.status_code == 201
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    response = api_client.get(f'/tasks/{task_id}')
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    data = result['data']
    assert data['task_id'] == task_id
    assert data['name'] == task_data['name']
    assert data['description'] == task_data['description']
    assert data['task_type'] == task_data['task_type']
    assert data['schedule'] == task_data['schedule']
    assert 'config' in data
    assert data['enabled'] is True
    assert 'created_at' in data
    assert 'updated_at' in data

class TestTaskUpdate:

    def test_update_task_name(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        update_data = {'name': 'Updated Task Name'}
        response = api_client.put(f'/tasks/{task_id}', data=update_data)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['data']['name'] == update_data['name']

    def test_update_task_schedule(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_summary']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        update_data = {'schedule': '0 1 * * *'}
        response = api_client.put(f'/tasks/{task_id}', data=update_data)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['data']['schedule'] == update_data['schedule']

    def test_update_task_config(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        update_data = {'config': {'path': '/tmp/new_path', 'pattern': '*.log', 'days': 30}}
        response = api_client.put(f'/tasks/{task_id}', data=update_data)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True

    def test_update_nonexistent_task(self, api_client):
        update_data = {'name': 'New name'}
        response = api_client.put('/tasks/nonexistent_task_id', data=update_data)
        assert response.status_code == 404
        result = response.json()
        assert result['success'] is False

def test_update_task_name(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    update_data = {'name': 'Updated Task Name'}
    response = api_client.put(f'/tasks/{task_id}', data=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert result['data']['name'] == update_data['name']

def test_update_task_schedule(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_summary']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    update_data = {'schedule': '0 1 * * *'}
    response = api_client.put(f'/tasks/{task_id}', data=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert result['data']['schedule'] == update_data['schedule']

def test_update_task_config(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    update_data = {'config': {'path': '/tmp/new_path', 'pattern': '*.log', 'days': 30}}
    response = api_client.put(f'/tasks/{task_id}', data=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True

def test_update_nonexistent_task(self, api_client):
    update_data = {'name': 'New name'}
    response = api_client.put('/tasks/nonexistent_task_id', data=update_data)
    assert response.status_code == 404
    result = response.json()
    assert result['success'] is False

class TestTaskDeletion:

    def test_delete_task(self, api_client, sample_task_data):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        response = api_client.delete(f'/tasks/{task_id}')
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        get_response = api_client.get(f'/tasks/{task_id}')
        assert get_response.status_code == 404

    def test_delete_nonexistent_task(self, api_client):
        response = api_client.delete('/tasks/nonexistent_task_id')
        assert response.status_code == 404
        result = response.json()
        assert result['success'] is False

def test_delete_task(self, api_client, sample_task_data):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    response = api_client.delete(f'/tasks/{task_id}')
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    get_response = api_client.get(f'/tasks/{task_id}')
    assert get_response.status_code == 404

def test_delete_nonexistent_task(self, api_client):
    response = api_client.delete('/tasks/nonexistent_task_id')
    assert response.status_code == 404
    result = response.json()
    assert result['success'] is False

class TestTaskToggle:

    def test_disable_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['file_cleanup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        toggle_data = {'enabled': False}
        response = api_client.post(f'/tasks/{task_id}/toggle', data=toggle_data)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['data']['enabled'] is False

    def test_enable_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data['data_backup']
        create_response = api_client.post('/tasks', data=task_data)
        task_id = create_response.json()['data']['task_id']
        cleanup_tasks.append(task_id)
        toggle_data = {'enabled': True}
        response = api_client.post(f'/tasks/{task_id}/toggle', data=toggle_data)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['data']['enabled'] is True

    def test_toggle_nonexistent_task(self, api_client):
        toggle_data = {'enabled': True}
        response = api_client.post('/tasks/nonexistent_task_id/toggle', data=toggle_data)
        assert response.status_code == 404
        result = response.json()
        assert result['success'] is False

def test_disable_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['file_cleanup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    toggle_data = {'enabled': False}
    response = api_client.post(f'/tasks/{task_id}/toggle', data=toggle_data)
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert result['data']['enabled'] is False

def test_enable_task(self, api_client, sample_task_data, cleanup_tasks):
    task_data = sample_task_data['data_backup']
    create_response = api_client.post('/tasks', data=task_data)
    task_id = create_response.json()['data']['task_id']
    cleanup_tasks.append(task_id)
    toggle_data = {'enabled': True}
    response = api_client.post(f'/tasks/{task_id}/toggle', data=toggle_data)
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert result['data']['enabled'] is True

def test_toggle_nonexistent_task(self, api_client):
    toggle_data = {'enabled': True}
    response = api_client.post('/tasks/nonexistent_task_id/toggle', data=toggle_data)
    assert response.status_code == 404
    result = response.json()
    assert result['success'] is False

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

@pytest.fixture(scope='session')
def check_server():
    max_retries = 5
    retry_delay = 2
    for i in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/stats', timeout=5)
            if response.status_code in [200, 404]:
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                pytest.fail(f'Server not running or inaccessible: {BASE_URL}\nPlease start the service first: python app.py')
    return True

# Node: fail
class APIClient:

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def get(self, endpoint, params=None):
        url = f'{self.base_url}{endpoint}'
        response = self.session.get(url, params=params)
        return response

    def post(self, endpoint, data=None):
        url = f'{self.base_url}{endpoint}'
        response = self.session.post(url, json=data)
        return response

    def put(self, endpoint, data=None):
        url = f'{self.base_url}{endpoint}'
        response = self.session.put(url, json=data)
        return response

    def delete(self, endpoint):
        url = f'{self.base_url}{endpoint}'
        response = self.session.delete(url)
        return response

def post(self, endpoint, data=None):
    url = f'{self.base_url}{endpoint}'
    response = self.session.post(url, json=data)
    return response

def put(self, endpoint, data=None):
    url = f'{self.base_url}{endpoint}'
    response = self.session.put(url, json=data)
    return response

def delete(self, endpoint):
    url = f'{self.base_url}{endpoint}'
    response = self.session.delete(url)
    return response

@pytest.fixture
def cleanup_tasks(api_client):
    created_task_ids = []
    yield created_task_ids
    for task_id in created_task_ids:
        try:
            api_client.delete(f'/tasks/{task_id}')
        except Exception:
            pass

class TestGameAPI:

    @pytest.mark.api
    def test_health_check(self):
        resp = requests.get(f'{BASE_URL}/health')
        assert resp.status_code == 200
        data = resp.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert data['status'] in ['healthy', 'ok', 'up']

    @pytest.mark.api
    def test_start_game_and_get_state(self):
        payload = {'player_x': 'alice', 'player_o': 'bob'}
        resp = requests.post(f'{BASE_URL}/games', json=payload, headers={'Content-Type': 'application/json'})
        if resp.status_code == 404:
            pytest.skip('Games endpoint not implemented')
        assert resp.status_code == 201
        game = resp.json()
        assert 'game_id' in game
        assert game['status'] == 'in_progress'
        assert game['next_player'] in ['X', 'O']
        assert isinstance(game['board'], list) and len(game['board']) == 3
        game_id = game['game_id']
        resp2 = requests.get(f'{BASE_URL}/games/{game_id}')
        assert resp2.status_code == 200
        state = resp2.json()
        assert state['game_id'] == game_id
        assert state['status'] in ['in_progress', 'finished', 'draw']

    @pytest.mark.api
    def test_make_moves_and_win(self):
        start = requests.post(f'{BASE_URL}/games', json={'player_x': 'x', 'player_o': 'o'})
        if start.status_code == 404:
            pytest.skip('Games endpoint not implemented')
        assert start.status_code == 201
        game_id = start.json()['game_id']
        moves = [('X', 0, 0), ('O', 1, 0), ('X', 0, 1), ('O', 1, 1), ('X', 0, 2)]
        last = None
        for player, row, col in moves:
            last = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': player, 'row': row, 'col': col}, headers={'Content-Type': 'application/json'})
            assert last.status_code in [200, 409], last.text
            if last.status_code == 409:
                pytest.skip('Move conflict behavior differs; skipping win flow')
        data = last.json()
        assert data['status'] in ['finished', 'draw']
        if data['status'] == 'finished':
            assert data.get('winner') == 'X'

    @pytest.mark.api
    def test_illegal_move_validation(self):
        start = requests.post(f'{BASE_URL}/games', json={'player_x': 'p1', 'player_o': 'p2'})
        if start.status_code == 404:
            pytest.skip('Games endpoint not implemented')
        game_id = start.json()['game_id']
        r1 = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': 'X', 'row': 0, 'col': 0})
        assert r1.status_code == 200
        r2 = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': 'O', 'row': 0, 'col': 0})
        assert r2.status_code in [409, 422]
        err = r2.json()
        assert 'error' in err

    @pytest.mark.api
    def test_reset_game(self):
        start = requests.post(f'{BASE_URL}/games', json={'player_x': 'p1', 'player_o': 'p2'})
        if start.status_code == 404:
            pytest.skip('Games endpoint not implemented')
        game_id = start.json()['game_id']
        r1 = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': 'X', 'row': 2, 'col': 2})
        assert r1.status_code == 200
        r2 = requests.post(f'{BASE_URL}/games/{game_id}/reset')
        assert r2.status_code in [200, 204]
        if r2.status_code == 200:
            data = r2.json()
            assert data['status'] == 'in_progress'
            assert data['board'] == [[None, None, None], [None, None, None], [None, None, None]]

    @pytest.mark.api
    def test_leaderboard(self):
        resp = requests.get(f'{BASE_URL}/leaderboard')
        if resp.status_code == 404:
            pytest.skip('Leaderboard endpoint not implemented')
        assert resp.status_code == 200
        data = resp.json()
        assert 'items' in data
        assert 'pagination' in data
        assert isinstance(data['items'], list)

    @pytest.mark.edge_case
    def test_invalid_json_request(self):
        resp = requests.post(f'{BASE_URL}/games', data='not-json', headers={'Content-Type': 'application/json'})
        assert resp.status_code in [400, 415]
        data = resp.json()
        assert 'error' in data

@pytest.mark.api
def test_make_moves_and_win(self):
    start = requests.post(f'{BASE_URL}/games', json={'player_x': 'x', 'player_o': 'o'})
    if start.status_code == 404:
        pytest.skip('Games endpoint not implemented')
    assert start.status_code == 201
    game_id = start.json()['game_id']
    moves = [('X', 0, 0), ('O', 1, 0), ('X', 0, 1), ('O', 1, 1), ('X', 0, 2)]
    last = None
    for player, row, col in moves:
        last = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': player, 'row': row, 'col': col}, headers={'Content-Type': 'application/json'})
        assert last.status_code in [200, 409], last.text
        if last.status_code == 409:
            pytest.skip('Move conflict behavior differs; skipping win flow')
    data = last.json()
    assert data['status'] in ['finished', 'draw']
    if data['status'] == 'finished':
        assert data.get('winner') == 'X'

@pytest.mark.api
def test_illegal_move_validation(self):
    start = requests.post(f'{BASE_URL}/games', json={'player_x': 'p1', 'player_o': 'p2'})
    if start.status_code == 404:
        pytest.skip('Games endpoint not implemented')
    game_id = start.json()['game_id']
    r1 = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': 'X', 'row': 0, 'col': 0})
    assert r1.status_code == 200
    r2 = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': 'O', 'row': 0, 'col': 0})
    assert r2.status_code in [409, 422]
    err = r2.json()
    assert 'error' in err

@pytest.mark.api
def test_reset_game(self):
    start = requests.post(f'{BASE_URL}/games', json={'player_x': 'p1', 'player_o': 'p2'})
    if start.status_code == 404:
        pytest.skip('Games endpoint not implemented')
    game_id = start.json()['game_id']
    r1 = requests.post(f'{BASE_URL}/games/{game_id}/moves', json={'player': 'X', 'row': 2, 'col': 2})
    assert r1.status_code == 200
    r2 = requests.post(f'{BASE_URL}/games/{game_id}/reset')
    assert r2.status_code in [200, 204]
    if r2.status_code == 200:
        data = r2.json()
        assert data['status'] == 'in_progress'
        assert data['board'] == [[None, None, None], [None, None, None], [None, None, None]]

@pytest.mark.edge_case
def test_invalid_json_request(self):
    resp = requests.post(f'{BASE_URL}/games', data='not-json', headers={'Content-Type': 'application/json'})
    assert resp.status_code in [400, 415]
    data = resp.json()
    assert 'error' in data

class TestConvertBatchEndpoint:
    BASE_URL = 'http://localhost:8000/api/v1'

    def setup_method(self):
        self.test_datasets = []
        csv_data = 'Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai'
        self.test_datasets.append({'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')})
        df = pd.DataFrame({'Product': ['ProductA', 'ProductB', 'ProductC'], 'Price': [100, 200, 300], 'Stock': [50, 30, 20]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        self.test_datasets.append({'source_format': 'excel', 'target_format': 'csv', 'data': excel_data})
        csv_data2 = 'Department,Number of People,Budget\nTechnology Department,10,100000\nSales Department,8,80000\nMarketing Department,5,50000'
        self.test_datasets.append({'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(csv_data2.encode('utf-8')).decode('utf-8')})

    def test_batch_conversion_sequential(self):
        payload = {'conversions': self.test_datasets, 'parallel': False}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=60)
        end_time = time.time()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'results' in data
        assert 'summary' in data
        assert len(data['results']) == len(self.test_datasets)
        summary = data['summary']
        assert summary['total_count'] == len(self.test_datasets)
        assert summary['success_count'] >= 0
        assert summary['failure_count'] >= 0
        assert summary['total_count'] == summary['success_count'] + summary['failure_count']
        assert summary['total_time'] > 0
        assert end_time - start_time < 45.0

    def test_batch_conversion_parallel(self):
        payload = {'conversions': self.test_datasets, 'parallel': True}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=60)
        end_time = time.time()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == len(self.test_datasets)
        parallel_time = end_time - start_time
        sequential_payload = {'conversions': self.test_datasets, 'parallel': False}
        seq_start = time.time()
        seq_response = requests.post(f'{self.BASE_URL}/convert/batch', json=sequential_payload, timeout=60)
        seq_end = time.time()
        sequential_time = seq_end - seq_start
        assert parallel_time <= sequential_time + 5.0

    def test_batch_conversion_with_failures(self):
        invalid_dataset = {'source_format': 'invalid_format', 'target_format': 'excel', 'data': base64.b64encode(b'test data').decode('utf-8')}
        test_datasets_with_failure = self.test_datasets + [invalid_dataset]
        payload = {'conversions': test_datasets_with_failure, 'parallel': False}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == len(test_datasets_with_failure)
        summary = data['summary']
        assert summary['total_count'] == len(test_datasets_with_failure)
        assert summary['success_count'] >= 0
        assert summary['failure_count'] > 0

    def test_batch_conversion_empty_list(self):
        payload = {'conversions': [], 'parallel': False}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=10)
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            assert summary.get('total_count', 0) == 0

    def test_batch_conversion_large_dataset(self):
        large_df = pd.DataFrame({f'col{i}': range(100) for i in range(50)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        large_datasets = []
        for i in range(3):
            large_datasets.append({'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data})
        payload = {'conversions': large_datasets, 'parallel': True}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=120)
        end_time = time.time()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        processing_time = end_time - start_time
        assert processing_time < 90.0
        summary = data['summary']
        assert summary['success_count'] == len(large_datasets)

    def test_batch_conversion_mixed_formats(self):
        mixed_datasets = [{'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode('a,b\n1,2'.encode('utf-8')).decode('utf-8')}, {'source_format': 'excel', 'target_format': 'pdf', 'data': self.test_datasets[1]['data']}, {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode('x,y,z\n1,2,3\n4,5,6'.encode('utf-8')).decode('utf-8')}]
        payload = {'conversions': mixed_datasets, 'parallel': False}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=45)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == len(mixed_datasets)
        for i, result in enumerate(data['results']):
            assert 'success' in result
            assert 'message' in result
            if result['success']:
                assert 'result' in result
                assert result['result'] != ''

    def test_batch_conversion_performance_comparison(self):
        test_data = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode('a,b,c\n1,2,3\n4,5,6'.encode('utf-8')).decode('utf-8')}
        single_start = time.time()
        for _ in range(3):
            response = requests.post(f'{self.BASE_URL}/convert', json=test_data, timeout=30)
            assert response.status_code == 200
        single_end = time.time()
        single_avg_time = (single_end - single_start) / 3
        batch_payload = {'conversions': [test_data, test_data, test_data], 'parallel': True}
        batch_start = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=batch_payload, timeout=60)
        batch_end = time.time()
        batch_time = batch_end - batch_start
        assert response.status_code == 200
        data = response.json()
        summary = data['summary']
        assert batch_time <= single_avg_time * 4
        assert summary['success_count'] == 3

def test_batch_conversion_sequential(self):
    payload = {'conversions': self.test_datasets, 'parallel': False}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=60)
    end_time = time.time()
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'results' in data
    assert 'summary' in data
    assert len(data['results']) == len(self.test_datasets)
    summary = data['summary']
    assert summary['total_count'] == len(self.test_datasets)
    assert summary['success_count'] >= 0
    assert summary['failure_count'] >= 0
    assert summary['total_count'] == summary['success_count'] + summary['failure_count']
    assert summary['total_time'] > 0
    assert end_time - start_time < 45.0

def test_batch_conversion_parallel(self):
    payload = {'conversions': self.test_datasets, 'parallel': True}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=60)
    end_time = time.time()
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['results']) == len(self.test_datasets)
    parallel_time = end_time - start_time
    sequential_payload = {'conversions': self.test_datasets, 'parallel': False}
    seq_start = time.time()
    seq_response = requests.post(f'{self.BASE_URL}/convert/batch', json=sequential_payload, timeout=60)
    seq_end = time.time()
    sequential_time = seq_end - seq_start
    assert parallel_time <= sequential_time + 5.0

def test_batch_conversion_empty_list(self):
    payload = {'conversions': [], 'parallel': False}
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=10)
    assert response.status_code in [200, 400, 422]
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        assert summary.get('total_count', 0) == 0

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

def intensive_workload():
    for i in range(20):
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.medium_excel_data}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            assert 'metadata' in data
            assert 'conversion_time' in data['metadata']
        time.sleep(0.1)

class TestConvertEndpoint:
    BASE_URL = 'http://localhost:8000/api/v1'
    SAMPLE_CSV_DATA = 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000\nWang Wu,28,Shenzhen,20000\nZhao Liu,35,Guangzhou,16000'
    SAMPLE_EXCEL_DATA = None

    def setup_method(self):
        df = pd.DataFrame({'Name': ['Zhang San', 'Li Si', 'Wang Wu', 'Zhao Liu'], 'Age': [25, 30, 28, 35], 'City': ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou'], 'Salary': [15000, 18000, 20000, 16000]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.SAMPLE_EXCEL_DATA = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_csv_to_excel_conversion(self):
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'result' in data
        assert data['result'] != ''
        assert 'metadata' in data
        assert data['metadata']['source_size'] > 0
        assert data['metadata']['target_size'] > 0
        assert data['metadata']['conversion_time'] > 0
        assert data['metadata']['rows_count'] == 4
        assert data['metadata']['columns_count'] == 4

    def test_excel_to_csv_conversion(self):
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.SAMPLE_EXCEL_DATA, 'options': {'encoding': 'utf-8', 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        result_data = base64.b64decode(data['result']).decode('utf-8')
        lines = result_data.strip().split('\n')
        assert len(lines) >= 2
        headers = lines[0].split(',')
        assert 'Name' in headers
        assert 'Age' in headers
        assert 'City' in headers
        assert 'Salary' in headers

    def test_excel_to_pdf_conversion(self):
        payload = {'source_format': 'excel', 'target_format': 'pdf', 'data': self.SAMPLE_EXCEL_DATA, 'options': {'encoding': 'utf-8', 'has_header': True, 'sheet_name': 'Sheet1'}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'result' in data
        result_data = base64.b64decode(data['result'])
        assert len(result_data) > 1000

    def test_csv_to_pdf_conversion(self):
        payload = {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True, 'delimiter': ','}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        result_data = base64.b64decode(data['result'])
        assert len(result_data) > 1000

    def test_invalid_format_conversion(self):
        payload = {'source_format': 'invalid', 'target_format': 'excel', 'data': base64.b64encode(b'test data').decode('utf-8')}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
        assert response.status_code in [400, 422]

    def test_empty_data_conversion(self):
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': '', 'options': {'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
        assert response.status_code in [200, 400]

    def test_large_file_conversion(self):
        large_data = pd.DataFrame({f'col{i}': range(1000) for i in range(20)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_data.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data, 'options': {'encoding': 'utf-8', 'has_header': True}}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=60)
        end_time = time.time()
        assert response.status_code == 200
        conversion_time = end_time - start_time
        assert conversion_time < 30.0
        data = response.json()
        assert data['success'] is True

    @pytest.mark.parametrize('encoding', ['utf-8', 'gbk', 'utf-16'])
    def test_different_encodings(self, encoding):
        test_data = 'name,age\nZhang San,25\nLi Si,30'
        try:
            encoded_data = test_data.encode(encoding)
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(encoded_data).decode('utf-8'), 'options': {'encoding': encoding, 'has_header': True}}
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
            assert response.status_code in [200, 400, 422]
        except UnicodeEncodeError:
            pytest.skip(f'encoding {encoding} does not support Chinese characters')

    def test_conversion_with_special_characters(self):
        special_data = 'name,description,symbol\nZhang San,contains @ and #,Beijing @ Shanghai # Shenzhen\nLi Si,contains $ and %,amount $1000 50%\nWang Wu,contains & and *,condition A&B quantity *2'
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(special_data.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

def test_excel_to_pdf_conversion(self):
    payload = {'source_format': 'excel', 'target_format': 'pdf', 'data': self.SAMPLE_EXCEL_DATA, 'options': {'encoding': 'utf-8', 'has_header': True, 'sheet_name': 'Sheet1'}}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'result' in data
    result_data = base64.b64decode(data['result'])
    assert len(result_data) > 1000

def test_empty_data_conversion(self):
    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': '', 'options': {'has_header': True}}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
    assert response.status_code in [200, 400]

def test_register_user(client):
    """Test user registration."""
    response = client.post('/api/v1/auth/register', json={'username': 'newuser', 'email': 'new@example.com', 'password': 'password123'})
    assert response.status_code == 201
    data = response.json()
    assert data['username'] == 'newuser'
    assert 'user_id' in data

def test_register_existing_user(client, test_user):
    """Test registering an existing user."""
    response = client.post('/api/v1/auth/register', json={'username': test_user['data']['username'], 'email': 'another@example.com', 'password': 'password123'})
    assert response.status_code == 400
    assert response.json()['detail'] == 'User already exists'

def test_login_user(client, test_user):
    """Test user login."""
    response = client.post('/api/v1/auth/login', json={'username': test_user['data']['username'], 'password': test_user['data']['password']})
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post('/api/v1/auth/login', json={'username': test_user['data']['username'], 'password': 'wrongpassword'})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid username or password'

def test_create_category(client, test_user):
    """Test creating a category."""
    response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Technology', 'description': 'Tech news and reviews'})
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'Technology'
    assert data['description'] == 'Tech news and reviews'

def test_create_category_unauthorized(client):
    """Test creating a category without authentication."""
    response = client.post('/api/v1/categories/', json={'name': 'Technology', 'description': 'Tech news and reviews'})
    assert response.status_code == 403

def test_get_categories(client, test_user):
    """Test retrieving categories."""
    client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Tech', 'description': 'Tech stuff'})
    response = client.get('/api/v1/categories/')
    assert response.status_code == 200
    data = response.json()
    assert len(data['categories']) >= 1
    assert data['categories'][0]['name'] == 'Tech'

def test_create_post(client, test_user):
    """Test creating a post."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Coding', 'description': 'Coding stuff'})
    category_id = cat_response.json()['id']
    response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'My First Post', 'content': 'This is the content.', 'excerpt': 'This is the excerpt.', 'category_id': category_id, 'status': 'published', 'tags': ['python', 'fastapi']})
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'My First Post'
    assert data['author_id'] == test_user['user'].id

def test_create_post_invalid_category(client, test_user):
    """Test creating a post with invalid category."""
    response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'My First Post', 'content': 'This is the content.', 'excerpt': 'This is the excerpt.', 'category_id': 999, 'status': 'published'})
    assert response.status_code == 404
    assert response.json()['detail'] == 'Category not found'

def test_get_posts(client, test_user):
    """Test retrieving posts list."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'News', 'description': 'News stuff'})
    category_id = cat_response.json()['id']
    client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'News Post', 'content': 'News content', 'excerpt': 'News excerpt', 'category_id': category_id, 'status': 'published'})
    response = client.get('/api/v1/posts/')
    assert response.status_code == 200
    data = response.json()
    assert len(data['posts']) >= 1
    assert data['posts'][0]['title'] == 'News Post'

def test_get_post_detail(client, test_user):
    """Test retrieving a single post."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Detail', 'description': 'Detail stuff'})
    category_id = cat_response.json()['id']
    post_response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Detail Post', 'content': 'Detail content', 'excerpt': 'Detail excerpt', 'category_id': category_id, 'status': 'published'})
    post_id = post_response.json()['id']
    response = client.get(f'/api/v1/posts/{post_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Detail Post'

def test_update_post(client, test_user):
    """Test updating a post."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Update', 'description': 'Update stuff'})
    category_id = cat_response.json()['id']
    post_response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Original Title', 'content': 'Original content', 'excerpt': 'Original excerpt', 'category_id': category_id, 'status': 'published'})
    post_id = post_response.json()['id']
    response = client.put(f'/api/v1/posts/{post_id}', headers=test_user['headers'], json={'title': 'Updated Title', 'content': 'Updated content', 'excerpt': 'Updated excerpt', 'category_id': category_id, 'status': 'published'})
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Updated Title'

def test_update_post_unauthorized(client, test_user, test_user_2):
    """Test updating another user's post."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Auth', 'description': 'Auth stuff'})
    category_id = cat_response.json()['id']
    post_response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'User 1 Post', 'content': 'Content', 'excerpt': 'Excerpt', 'category_id': category_id, 'status': 'published'})
    post_id = post_response.json()['id']
    response = client.put(f'/api/v1/posts/{post_id}', headers=test_user_2['headers'], json={'title': 'Hacked Title', 'content': 'Hacked content', 'excerpt': 'Hacked excerpt', 'category_id': category_id, 'status': 'published'})
    assert response.status_code == 403
    assert response.json()['detail'] == 'No permission to update this post'

def test_delete_post(client, test_user):
    """Test deleting a post."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Delete', 'description': 'Delete stuff'})
    category_id = cat_response.json()['id']
    post_response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Delete Post', 'content': 'Content', 'excerpt': 'Excerpt', 'category_id': category_id, 'status': 'published'})
    post_id = post_response.json()['id']
    response = client.delete(f'/api/v1/posts/{post_id}', headers=test_user['headers'])
    assert response.status_code == 200
    assert response.json()['message'] == 'Post deleted successfully'
    get_response = client.get(f'/api/v1/posts/{post_id}')
    assert get_response.status_code == 404

def test_delete_post_unauthorized(client, test_user, test_user_2):
    """Test deleting another user's post."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Delete Auth', 'description': 'Delete Auth stuff'})
    category_id = cat_response.json()['id']
    post_response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'User 1 Post', 'content': 'Content', 'excerpt': 'Excerpt', 'category_id': category_id, 'status': 'published'})
    post_id = post_response.json()['id']
    response = client.delete(f'/api/v1/posts/{post_id}', headers=test_user_2['headers'])
    assert response.status_code == 403
    assert response.json()['detail'] == 'No permission to delete this post'

def test_search_posts(client, test_user):
    """Test searching posts."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Search', 'description': 'Search stuff'})
    category_id = cat_response.json()['id']
    client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Python Tutorial', 'content': 'Learn Python', 'excerpt': 'Python', 'category_id': category_id, 'status': 'published'})
    client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Java Tutorial', 'content': 'Learn Java', 'excerpt': 'Java', 'category_id': category_id, 'status': 'published'})
    response = client.get('/api/v1/posts/?search=Python')
    assert response.status_code == 200
    data = response.json()
    assert len(data['posts']) == 1
    assert data['posts'][0]['title'] == 'Python Tutorial'

def test_filter_posts_by_category(client, test_user):
    """Test filtering posts by category."""
    cat1 = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Cat1', 'description': 'Cat1'}).json()
    cat2 = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Cat2', 'description': 'Cat2'}).json()
    client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Post 1', 'content': 'Content', 'excerpt': 'Excerpt', 'category_id': cat1['id'], 'status': 'published'})
    client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Post 2', 'content': 'Content', 'excerpt': 'Excerpt', 'category_id': cat2['id'], 'status': 'published'})
    response = client.get(f'/api/v1/posts/?category_id={cat1['id']}')
    assert response.status_code == 200
    data = response.json()
    assert len(data['posts']) == 1
    assert data['posts'][0]['title'] == 'Post 1'

def test_get_draft_post_unauthorized(client, test_user, test_user_2):
    """Test that non-authors cannot see draft posts."""
    cat_response = client.post('/api/v1/categories/', headers=test_user['headers'], json={'name': 'Draft', 'description': 'Draft stuff'})
    category_id = cat_response.json()['id']
    post_response = client.post('/api/v1/posts/', headers=test_user['headers'], json={'title': 'Draft Post', 'content': 'Content', 'excerpt': 'Excerpt', 'category_id': category_id, 'status': 'draft'})
    post_id = post_response.json()['id']
    response = client.get(f'/api/v1/posts/{post_id}', headers=test_user_2['headers'])
    assert response.status_code == 404

# Node: get_auth_headers
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

class TestWebPanAPI:
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = {'username': 'testuser', 'password': 'testpass123', 'email': 'test@example.com'}
        self.test_file_content = b'This is a test file content for WebPan API testing.'
        self.test_file_name = 'test_file.txt'

    def test_user_registration(self):
        response = self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'user_id' in data
        assert data['message'] == 'User registered successfully'

    def test_user_login(self):
        self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
        login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
        response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'token' in data
        assert 'user_id' in data
        assert 'expires_in' in data
        self.auth_token = data['token']

    def test_login_invalid_credentials(self):
        login_data = {'username': 'invalid_user', 'password': 'invalid_pass'}
        response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'AUTH_INVALID'

    def test_file_upload_single(self):
        self._login_user()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'file_id' in data
            assert data['filename'] == self.test_file_name
            assert data['size'] == len(self.test_file_content)
            assert 'upload_time' in data
            assert 'download_url' in data
            self.test_file_id = data['file_id']
        finally:
            os.unlink(temp_file_path)

    def test_file_upload_without_auth(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files)
            assert response.status_code == 401
            data = response.json()
            assert data['success'] is False
            assert data['error_code'] == 'AUTH_REQUIRED'
        finally:
            os.unlink(temp_file_path)

    def test_file_upload_multiple(self):
        self._login_user()
        temp_files = []
        file_names = ['file1.txt', 'file2.txt', 'file3.txt']
        try:
            for i, name in enumerate(file_names):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
                    content = f'Test content for {name}'.encode()
                    f.write(content)
                    temp_files.append((f.name, name, content))
            files = []
            for temp_path, name, _ in temp_files:
                files.append(('files', (name, open(temp_path, 'rb'), 'text/plain')))
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(f'{self.BASE_URL}/files/upload-multiple', files=files, headers=headers)
            for _, (_, file_obj, _) in enumerate(files):
                file_obj[1][1].close()
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert len(data['uploaded_files']) == 3
            assert len(data['failed_files']) == 0
            for uploaded_file in data['uploaded_files']:
                assert 'file_id' in uploaded_file
                assert uploaded_file['status'] == 'success'
        finally:
            for temp_path, _, _ in temp_files:
                os.unlink(temp_path)

    def test_file_download(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/download', headers=headers)
        assert response.status_code == 200
        assert response.content == self.test_file_content

    def test_file_download_not_found(self):
        self._login_user()
        fake_file_id = 'non-existent-file-id'
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files/{fake_file_id}/download', headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'FILE_NOT_FOUND'

    def test_file_info(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/info', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['file_id'] == self.test_file_id
        assert data['filename'] == self.test_file_name
        assert data['size'] == len(self.test_file_content)
        assert 'mime_type' in data
        assert 'upload_time' in data
        assert 'download_count' in data
        assert 'owner_id' in data

    def test_file_list(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'files' in data
        assert 'pagination' in data
        assert len(data['files']) >= 1
        pagination = data['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total' in pagination
        assert 'pages' in pagination

    def test_file_list_with_pagination(self):
        self._login_user()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        params = {'page': 1, 'limit': 5}
        response = self.session.get(f'{self.BASE_URL}/files', headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 5

    def test_file_delete(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.delete(f'{self.BASE_URL}/files/{self.test_file_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'message' in data
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/info', headers=headers)
        assert response.status_code == 404

    def test_file_rename(self):
        self._login_user()
        self._upload_test_file()
        new_name = 'renamed_file.txt'
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        data = {'new_name': new_name}
        response = self.session.put(f'{self.BASE_URL}/files/{self.test_file_id}/rename', json=data, headers=headers)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['new_filename'] == new_name
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/info', headers=headers)
        assert response.status_code == 200
        file_info = response.json()
        assert file_info['filename'] == new_name

    def test_file_share_create(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': True, 'expires_in': 3600}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'share_id' in data
        assert 'share_url' in data
        assert 'expires_at' in data
        assert 'access_count' in data
        self.test_share_id = data['share_id']

    def test_file_share_with_password(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': False, 'expires_in': 3600, 'password': 'sharepass123'}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'share_id' in data

    def test_share_access(self):
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        response = self.session.get(f'{self.BASE_URL}/share/{self.test_share_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'file_info' in data
        assert 'download_url' in data
        assert data['file_info']['filename'] == self.test_file_name

    def test_share_access_with_password(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': False, 'expires_in': 3600, 'password': 'sharepass123'}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        share_id = response.json()['share_id']
        response = self.session.get(f'{self.BASE_URL}/share/{share_id}')
        assert response.status_code == 401
        params = {'password': 'sharepass123'}
        response = self.session.get(f'{self.BASE_URL}/share/{share_id}', params=params)
        assert response.status_code == 200

    def test_share_delete(self):
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.delete(f'{self.BASE_URL}/share/{self.test_share_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        response = self.session.get(f'{self.BASE_URL}/share/{self.test_share_id}')
        assert response.status_code == 404

    def test_storage_quota(self):
        self._login_user()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/storage/quota', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'used_space' in data
        assert 'total_space' in data
        assert 'available_space' in data
        assert 'usage_percentage' in data
        assert data['used_space'] >= 0
        assert data['total_space'] > 0
        assert data['available_space'] >= 0
        assert 0 <= data['usage_percentage'] <= 100

    def test_file_upload_large_file(self):
        self._login_user()
        large_content = b'x' * (99 * 1024 * 1024)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(large_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('large_file.bin', f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            if response.status_code == 200:
                data = response.json()
                assert data['success'] is True
            else:
                data = response.json()
                assert data['success'] is False
                assert data['error_code'] in ['FILE_TOO_LARGE', 'QUOTA_EXCEEDED']
        finally:
            os.unlink(temp_file_path)

    def test_file_upload_oversized_file(self):
        self._login_user()
        oversized_content = b'x' * (101 * 1024 * 1024)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(oversized_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('oversized_file.bin', f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            assert response.status_code == 413
            data = response.json()
            assert data['success'] is False
            assert data['error_code'] == 'FILE_TOO_LARGE'
        finally:
            os.unlink(temp_file_path)

    def test_share_expired(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': True, 'expires_in': 1}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        share_id = response.json()['share_id']
        import time
        time.sleep(2)
        response = self.session.get(f'{self.BASE_URL}/share/{share_id}')
        assert response.status_code == 410
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'SHARE_EXPIRED'

    def _login_user(self):
        self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
        login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
        response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
        self.auth_token = response.json()['token']

    def _upload_test_file(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            self.test_file_id = response.json()['file_id']
        finally:
            os.unlink(temp_file_path)

    def _create_share_link(self):
        share_data = {'is_public': True, 'expires_in': 3600}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        self.test_share_id = response.json()['share_id']

def test_user_registration(self):
    response = self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'user_id' in data
    assert data['message'] == 'User registered successfully'

def test_user_login(self):
    self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
    login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
    response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'token' in data
    assert 'user_id' in data
    assert 'expires_in' in data
    self.auth_token = data['token']

def test_login_invalid_credentials(self):
    login_data = {'username': 'invalid_user', 'password': 'invalid_pass'}
    response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
    assert response.status_code == 401
    data = response.json()
    assert data['success'] is False
    assert data['error_code'] == 'AUTH_INVALID'

def test_file_share_create(self):
    self._login_user()
    self._upload_test_file()
    share_data = {'is_public': True, 'expires_in': 3600}
    headers = {'Authorization': f'Bearer {self.auth_token}'}
    response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'share_id' in data
    assert 'share_url' in data
    assert 'expires_at' in data
    assert 'access_count' in data
    self.test_share_id = data['share_id']

def test_file_share_with_password(self):
    self._login_user()
    self._upload_test_file()
    share_data = {'is_public': False, 'expires_in': 3600, 'password': 'sharepass123'}
    headers = {'Authorization': f'Bearer {self.auth_token}'}
    response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'share_id' in data

def _login_user(self):
    self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
    login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
    response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
    self.auth_token = response.json()['token']

def _create_share_link(self):
    share_data = {'is_public': True, 'expires_in': 3600}
    headers = {'Authorization': f'Bearer {self.auth_token}'}
    response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
    self.test_share_id = response.json()['share_id']

@pytest.fixture
def uploaded_file_id(authenticated_session: requests.Session, base_url: str, temp_file: str, test_file_name: str) -> str:
    with open(temp_file, 'rb') as f:
        files = {'file': (test_file_name, f, 'text/plain')}
        response = authenticated_session.post(f'{base_url}/files/upload', files=files)
    if response.status_code == 200:
        return response.json()['file_id']
    else:
        pytest.skip('Failed to upload test file')

@pytest.fixture
def share_link_id(authenticated_session: requests.Session, base_url: str, uploaded_file_id: str) -> str:
    share_data = {'is_public': True, 'expires_in': 3600}
    response = authenticated_session.post(f'{base_url}/files/{uploaded_file_id}/share', json=share_data)
    if response.status_code == 200:
        return response.json()['share_id']
    else:
        pytest.skip('Failed to create share link')

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

class TestSendSingleEmail:
    """Test cases for POST /api/v1/mail/send endpoint."""

    def test_send_email_success(self):
        """Test successfully sending a single email with all required fields."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'This is a test email body.'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data
        assert data['status'] in ['pending', 'sent']
        assert 'message' in data
        assert 'timestamp' in data
        datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

    def test_send_email_with_optional_fields(self):
        """Test sending email with all optional fields."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email with Optional Fields', 'body': 'Test body', 'from': 'sender@example.com', 'cc': ['cc@example.com'], 'bcc': ['bcc@example.com'], 'priority': 'high'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data
        assert data['status'] in ['pending', 'sent']

    def test_send_email_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        payload = {'to': ['user1@example.com', 'user2@example.com', 'user3@example.com'], 'subject': 'Test Multiple Recipients', 'body': 'Email to multiple recipients'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data

    def test_send_email_missing_required_field_to(self):
        """Test sending email without 'to' field returns 400."""
        payload = {'subject': 'Test Email', 'body': 'Test body'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'MISSING_FIELD'

    def test_send_email_missing_required_field_subject(self):
        """Test sending email without 'subject' field returns 400."""
        payload = {'to': ['user@example.com'], 'body': 'Test body'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'MISSING_FIELD'

    def test_send_email_missing_required_field_body(self):
        """Test sending email without 'body' field returns 400."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'MISSING_FIELD'

    def test_send_email_invalid_email_format(self):
        """Test sending email with invalid email address format."""
        payload = {'to': ['invalid-email'], 'subject': 'Test Email', 'body': 'Test body'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'INVALID_EMAIL'

    def test_send_email_empty_recipients(self):
        """Test sending email with empty recipients list."""
        payload = {'to': [], 'subject': 'Test Email', 'body': 'Test body'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_send_email_invalid_priority(self):
        """Test sending email with invalid priority value."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Test body', 'priority': 'invalid_priority'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'INVALID_PRIORITY'

    def test_send_email_valid_priority_values(self):
        """Test sending email with each valid priority value."""
        priorities = ['low', 'normal', 'high']
        for priority in priorities:
            payload = {'to': ['user@example.com'], 'subject': f'Test Email - {priority}', 'body': 'Test body', 'priority': priority}
            response = requests.post(SEND_EMAIL_URL, json=payload)
            assert response.status_code == 200
            data = response.json()
            assert 'mail_id' in data

    def test_send_email_with_cc_and_bcc(self):
        """Test sending email with CC and BCC recipients."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Test body', 'cc': ['cc1@example.com', 'cc2@example.com'], 'bcc': ['bcc1@example.com']}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data

    def test_send_email_empty_subject(self):
        """Test sending email with empty subject string."""
        payload = {'to': ['user@example.com'], 'subject': '', 'body': 'Test body'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_send_email_empty_body(self):
        """Test sending email with empty body string."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': ''}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_send_email_large_body(self):
        """Test sending email with large body exceeding 1MB limit."""
        large_body = 'x' * (1024 * 1024 + 1)
        payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': large_body}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

    def test_send_email_special_characters_in_subject(self):
        """Test sending email with special characters in subject."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email: Special Characters !@#$%^&*()', 'body': 'Test body'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data

    def test_send_email_unicode_content(self):
        """Test sending email with unicode content."""
        payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Hello World'}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data

def test_send_email_success(self):
    """Test successfully sending a single email with all required fields."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'This is a test email body.'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'mail_id' in data
    assert data['status'] in ['pending', 'sent']
    assert 'message' in data
    assert 'timestamp' in data
    datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

def test_send_email_with_optional_fields(self):
    """Test sending email with all optional fields."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email with Optional Fields', 'body': 'Test body', 'from': 'sender@example.com', 'cc': ['cc@example.com'], 'bcc': ['bcc@example.com'], 'priority': 'high'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'mail_id' in data
    assert data['status'] in ['pending', 'sent']

def test_send_email_multiple_recipients(self):
    """Test sending email to multiple recipients."""
    payload = {'to': ['user1@example.com', 'user2@example.com', 'user3@example.com'], 'subject': 'Test Multiple Recipients', 'body': 'Email to multiple recipients'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'mail_id' in data

def test_send_email_missing_required_field_to(self):
    """Test sending email without 'to' field returns 400."""
    payload = {'subject': 'Test Email', 'body': 'Test body'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert data['error'] == 'MISSING_FIELD'

def test_send_email_missing_required_field_subject(self):
    """Test sending email without 'subject' field returns 400."""
    payload = {'to': ['user@example.com'], 'body': 'Test body'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert data['error'] == 'MISSING_FIELD'

def test_send_email_missing_required_field_body(self):
    """Test sending email without 'body' field returns 400."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert data['error'] == 'MISSING_FIELD'

def test_send_email_invalid_email_format(self):
    """Test sending email with invalid email address format."""
    payload = {'to': ['invalid-email'], 'subject': 'Test Email', 'body': 'Test body'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert data['error'] == 'INVALID_EMAIL'

def test_send_email_empty_recipients(self):
    """Test sending email with empty recipients list."""
    payload = {'to': [], 'subject': 'Test Email', 'body': 'Test body'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

def test_send_email_invalid_priority(self):
    """Test sending email with invalid priority value."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Test body', 'priority': 'invalid_priority'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert data['error'] == 'INVALID_PRIORITY'

def test_send_email_valid_priority_values(self):
    """Test sending email with each valid priority value."""
    priorities = ['low', 'normal', 'high']
    for priority in priorities:
        payload = {'to': ['user@example.com'], 'subject': f'Test Email - {priority}', 'body': 'Test body', 'priority': priority}
        response = requests.post(SEND_EMAIL_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'mail_id' in data

def test_send_email_with_cc_and_bcc(self):
    """Test sending email with CC and BCC recipients."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Test body', 'cc': ['cc1@example.com', 'cc2@example.com'], 'bcc': ['bcc1@example.com']}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'mail_id' in data

def test_send_email_empty_subject(self):
    """Test sending email with empty subject string."""
    payload = {'to': ['user@example.com'], 'subject': '', 'body': 'Test body'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

def test_send_email_empty_body(self):
    """Test sending email with empty body string."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': ''}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

def test_send_email_large_body(self):
    """Test sending email with large body exceeding 1MB limit."""
    large_body = 'x' * (1024 * 1024 + 1)
    payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': large_body}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

def test_send_email_special_characters_in_subject(self):
    """Test sending email with special characters in subject."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email: Special Characters !@#$%^&*()', 'body': 'Test body'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'mail_id' in data

def test_send_email_unicode_content(self):
    """Test sending email with unicode content."""
    payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Hello World'}
    response = requests.post(SEND_EMAIL_URL, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'mail_id' in data

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

def _send(to=None, subject=None, body=None, **kwargs):
    payload = {'to': to or ['test@example.com'], 'subject': subject or 'Test Email', 'body': body or 'Test body'}
    payload.update(kwargs)
    response = requests.post(f'{BASE_URL}/api/v1/mail/send', json=payload)
    if response.status_code == 200:
        return response.json()['mail_id']
    return None

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

@pytest.fixture
def created_task(api_server, sample_task_data):
    """
    Fixture that creates a task and returns its data.
    The task is automatically cleaned up after the test.
    """
    response = requests.post(f'{api_server}/api/v1/tasks', json=sample_task_data, headers={'Content-Type': 'application/json'})
    if response.status_code != 201:
        pytest.skip('Failed to create test task')
    task_data = response.json()
    task_id = task_data['id']
    yield task_data
    try:
        requests.delete(f'{api_server}/api/v1/tasks/{task_id}')
    except requests.exceptions.RequestException:
        pass

@pytest.fixture
def created_tasks(api_server, sample_tasks_data):
    """
    Fixture that creates multiple tasks and returns their data.
    The tasks are automatically cleaned up after the test.
    """
    created_tasks = []
    for task_data in sample_tasks_data:
        response = requests.post(f'{api_server}/api/v1/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        if response.status_code == 201:
            created_tasks.append(response.json())
    yield created_tasks
    for task in created_tasks:
        try:
            requests.delete(f'{api_server}/api/v1/tasks/{task['id']}')
        except requests.exceptions.RequestException:
            pass

def test_localize_us_english():
    """Test localizing datetime for US English"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'America/New_York', 'locale': 'en_US'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Localization should succeed'
    assert 'formatted_datetime' in data, 'Formatted datetime should be present'
    assert data['timezone'] == 'America/New_York', 'Timezone should match'
    assert data['locale'] == 'en_US', 'Locale should match'
    assert len(data['formatted_datetime']) > 0, 'Formatted datetime should not be empty'
    print(f'✓ Test passed: US English localization')

def test_localize_chinese():
    """Test localizing datetime for Chinese"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'Asia/Shanghai', 'locale': 'zh_CN'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Localization should succeed'
    assert 'formatted_datetime' in data, 'Formatted datetime should be present'
    assert data['timezone'] == 'Asia/Shanghai', 'Timezone should match'
    assert data['locale'] == 'zh_CN', 'Locale should match'
    print(f'✓ Test passed: Chinese localization')

def test_localize_spanish():
    """Test localizing datetime for Spanish"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'Europe/Madrid', 'locale': 'es_ES'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Localization should succeed'
    assert 'formatted_datetime' in data, 'Formatted datetime should be present'
    assert data['timezone'] == 'Europe/Madrid', 'Timezone should match'
    assert data['locale'] == 'es_ES', 'Locale should match'
    print(f'✓ Test passed: Spanish localization')

def test_localize_japanese():
    """Test localizing datetime for Japanese"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'Asia/Tokyo', 'locale': 'ja_JP'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Localization should succeed'
    assert 'formatted_datetime' in data, 'Formatted datetime should be present'
    print(f'✓ Test passed: Japanese localization')

def test_localize_missing_required_field():
    """Test localization with missing required field"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'UTC'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Missing required field handled correctly')

def test_localize_invalid_datetime():
    """Test localization with invalid datetime"""
    payload = {'datetime': 'not-a-valid-datetime', 'timezone': 'UTC', 'locale': 'en_US'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail for invalid datetime'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Invalid datetime handled correctly')

def test_localize_invalid_timezone():
    """Test localization with invalid timezone"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'Invalid/Timezone', 'locale': 'en_US'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail for invalid timezone'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Invalid timezone handled correctly')

def test_localize_utc():
    """Test localizing datetime for UTC timezone"""
    payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'UTC', 'locale': 'en_GB'}
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Localization should succeed'
    assert 'formatted_datetime' in data, 'Formatted datetime should be present'
    assert data['timezone'] == 'UTC', 'Timezone should be UTC'
    print(f'✓ Test passed: UTC localization')

def test_localize_different_formats():
    """Test that different locales produce different formats"""
    us_payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'UTC', 'locale': 'en_US'}
    cn_payload = {'datetime': '2025-10-30T12:00:00', 'timezone': 'UTC', 'locale': 'zh_CN'}
    us_response = requests.post(LOCALIZE_ENDPOINT, json=us_payload)
    cn_response = requests.post(LOCALIZE_ENDPOINT, json=cn_payload)
    assert us_response.status_code == 200, 'US localization should succeed'
    assert cn_response.status_code == 200, 'CN localization should succeed'
    us_data = us_response.json()
    cn_data = cn_response.json()
    assert us_data['success'] == True, 'US localization should succeed'
    assert cn_data['success'] == True, 'CN localization should succeed'
    assert len(us_data['formatted_datetime']) > 0, 'US formatted datetime should not be empty'
    assert len(cn_data['formatted_datetime']) > 0, 'CN formatted datetime should not be empty'
    print(f'✓ Test passed: Different locale formats')

def test_translate_english_to_chinese():
    """Test translating English text to Chinese"""
    payload = {'text': 'Hello', 'source_lang': 'en', 'target_lang': 'zh-cn'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Translation should succeed'
    assert data['original_text'] == 'Hello', 'Original text should match'
    assert data['source_lang'] == 'en', "Source language should be 'en'"
    assert data['target_lang'] == 'zh-cn', "Target language should be 'zh-cn'"
    assert len(data['translated_text']) > 0, 'Translated text should not be empty'
    print(f'✓ Test passed: English to Chinese translation')

def test_translate_chinese_to_english():
    """Test translating Chinese text to English"""
    payload = {'text': '你好', 'source_lang': 'zh-cn', 'target_lang': 'en'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Translation should succeed'
    assert data['original_text'] == '你好', 'Original text should match'
    assert data['source_lang'] == 'zh-cn', "Source language should be 'zh-cn'"
    assert data['target_lang'] == 'en', "Target language should be 'en'"
    assert len(data['translated_text']) > 0, 'Translated text should not be empty'
    print(f'✓ Test passed: Chinese to English translation')

def test_translate_spanish_to_english():
    """Test translating Spanish text to English"""
    payload = {'text': 'Hola', 'source_lang': 'es', 'target_lang': 'en'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Translation should succeed'
    assert data['original_text'] == 'Hola', 'Original text should match'
    assert len(data['translated_text']) > 0, 'Translated text should not be empty'
    print(f'✓ Test passed: Spanish to English translation')

def test_translate_missing_required_field():
    """Test translation with missing required field"""
    payload = {'text': 'Hello', 'source_lang': 'en'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Missing required field handled correctly')

def test_translate_empty_text():
    """Test translation with empty text"""
    payload = {'text': '', 'source_lang': 'en', 'target_lang': 'zh-cn'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code in [200, 400], f'Expected 200 or 400, got {response.status_code}'
    data = response.json()
    if response.status_code == 400:
        assert data['success'] == False, 'Request should fail for empty text'
    print(f'✓ Test passed: Empty text handled correctly')

def test_translate_invalid_language_code():
    """Test translation with invalid language code"""
    payload = {'text': 'Hello', 'source_lang': 'invalid_lang', 'target_lang': 'en'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    data = response.json()
    assert 'success' in data, 'Response should contain success field'
    print(f'✓ Test passed: Invalid language code handled')

def test_translate_long_text():
    """Test translation with longer text"""
    payload = {'text': 'This is a longer text that contains multiple words and should be translated correctly.', 'source_lang': 'en', 'target_lang': 'es'}
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Translation should succeed'
    assert len(data['translated_text']) > 0, 'Translated text should not be empty'
    print(f'✓ Test passed: Long text translation')

def test_timezone_utc_to_shanghai():
    """Test converting UTC to Asia/Shanghai timezone"""
    payload = {'datetime': '2025-10-30T12:00:00', 'from_timezone': 'UTC', 'to_timezone': 'Asia/Shanghai'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Conversion should succeed'
    assert 'original_datetime' in data, 'Original datetime should be present'
    assert 'converted_datetime' in data, 'Converted datetime should be present'
    assert data['from_timezone'] == 'UTC', 'Source timezone should be UTC'
    assert data['to_timezone'] == 'Asia/Shanghai', 'Target timezone should be Asia/Shanghai'
    assert '20:00:00' in data['converted_datetime'] or '20' in data['converted_datetime'], 'Converted time should be 20:00 (12:00 + 8 hours)'
    print(f'✓ Test passed: UTC to Shanghai conversion')

def test_timezone_newyork_to_london():
    """Test converting America/New_York to Europe/London timezone"""
    payload = {'datetime': '2025-10-30T12:00:00', 'from_timezone': 'America/New_York', 'to_timezone': 'Europe/London'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Conversion should succeed'
    assert 'converted_datetime' in data, 'Converted datetime should be present'
    assert data['from_timezone'] == 'America/New_York', 'Source timezone should match'
    assert data['to_timezone'] == 'Europe/London', 'Target timezone should match'
    print(f'✓ Test passed: New York to London conversion')

def test_timezone_same_timezone():
    """Test converting within the same timezone"""
    payload = {'datetime': '2025-10-30T12:00:00', 'from_timezone': 'UTC', 'to_timezone': 'UTC'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Conversion should succeed'
    assert '12:00:00' in data['converted_datetime'] or '12' in data['converted_datetime'], 'Time should remain the same'
    print(f'✓ Test passed: Same timezone conversion')

def test_timezone_missing_required_field():
    """Test timezone conversion with missing required field"""
    payload = {'datetime': '2025-10-30T12:00:00', 'from_timezone': 'UTC'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Missing required field handled correctly')

def test_timezone_invalid_datetime_format():
    """Test timezone conversion with invalid datetime format"""
    payload = {'datetime': 'invalid-datetime', 'from_timezone': 'UTC', 'to_timezone': 'Asia/Shanghai'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail for invalid datetime'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Invalid datetime format handled correctly')

def test_timezone_invalid_timezone_name():
    """Test timezone conversion with invalid timezone name"""
    payload = {'datetime': '2025-10-30T12:00:00', 'from_timezone': 'Invalid/Timezone', 'to_timezone': 'UTC'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f'Expected error status code, got {response.status_code}'
    data = response.json()
    assert data['success'] == False, 'Request should fail for invalid timezone'
    assert 'error' in data, 'Error message should be present'
    print(f'✓ Test passed: Invalid timezone name handled correctly')

def test_timezone_edge_case_midnight():
    """Test timezone conversion at midnight"""
    payload = {'datetime': '2025-10-30T00:00:00', 'from_timezone': 'UTC', 'to_timezone': 'America/Los_Angeles'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Conversion should succeed'
    assert 'converted_datetime' in data, 'Converted datetime should be present'
    print(f'✓ Test passed: Midnight timezone conversion')

def test_timezone_cross_date():
    """Test timezone conversion that crosses date boundary"""
    payload = {'datetime': '2025-10-30T23:00:00', 'from_timezone': 'UTC', 'to_timezone': 'Pacific/Auckland'}
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Conversion should succeed'
    assert '31' in data['converted_datetime'] or '2025-10-31' in data['converted_datetime'], 'Date should advance to October 31'
    print(f'✓ Test passed: Cross-date timezone conversion')

class TestDataManagement:

    def test_add_data_success(self):
        payload = {'name': 'Python Programming', 'category': 'Programming', 'score': 95.5, 'description': 'A comprehensive guide to Python', 'tags': ['python', 'programming', 'tutorial']}
        response = requests.post(API_ENDPOINT, json=payload)
        assert response.status_code == 200 or response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['name'] == payload['name']
        assert data['data']['category'] == payload['category']
        assert data['data']['score'] == payload['score']
        assert 'id' in data['data']
        assert 'created_at' in data['data']

    def test_add_data_missing_required_field(self):
        payload = {'name': 'Incomplete Data'}
        response = requests.post(API_ENDPOINT, json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_get_data_by_id(self):
        payload = {'name': 'Test Data', 'category': 'Test', 'score': 80.0}
        create_response = requests.post(API_ENDPOINT, json=payload)
        created_id = create_response.json()['data']['id']
        response = requests.get(f'{API_ENDPOINT}/{created_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['id'] == created_id
        assert data['data']['name'] == payload['name']

    def test_get_data_by_invalid_id(self):
        response = requests.get(f'{API_ENDPOINT}/invalid-id-12345')
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False

    def test_delete_data(self):
        payload = {'name': 'To Be Deleted', 'category': 'Test', 'score': 50.0}
        create_response = requests.post(API_ENDPOINT, json=payload)
        created_id = create_response.json()['data']['id']
        response = requests.delete(f'{API_ENDPOINT}/{created_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        get_response = requests.get(f'{API_ENDPOINT}/{created_id}')
        assert get_response.status_code == 404

def test_add_data_success(self):
    payload = {'name': 'Python Programming', 'category': 'Programming', 'score': 95.5, 'description': 'A comprehensive guide to Python', 'tags': ['python', 'programming', 'tutorial']}
    response = requests.post(API_ENDPOINT, json=payload)
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data['success'] is True
    assert 'data' in data
    assert data['data']['name'] == payload['name']
    assert data['data']['category'] == payload['category']
    assert data['data']['score'] == payload['score']
    assert 'id' in data['data']
    assert 'created_at' in data['data']

def test_add_data_missing_required_field(self):
    payload = {'name': 'Incomplete Data'}
    response = requests.post(API_ENDPOINT, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False

def test_get_data_by_id(self):
    payload = {'name': 'Test Data', 'category': 'Test', 'score': 80.0}
    create_response = requests.post(API_ENDPOINT, json=payload)
    created_id = create_response.json()['data']['id']
    response = requests.get(f'{API_ENDPOINT}/{created_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['data']['id'] == created_id
    assert data['data']['name'] == payload['name']

def test_delete_data(self):
    payload = {'name': 'To Be Deleted', 'category': 'Test', 'score': 50.0}
    create_response = requests.post(API_ENDPOINT, json=payload)
    created_id = create_response.json()['data']['id']
    response = requests.delete(f'{API_ENDPOINT}/{created_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    get_response = requests.get(f'{API_ENDPOINT}/{created_id}')
    assert get_response.status_code == 404

class TestEdgeCases:

    def test_invalid_sort_field(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'invalid_field', 'sort_order': 'asc'})
        assert response.status_code in [200, 400]

    def test_invalid_sort_order(self):
        response = requests.get(API_ENDPOINT, params={'sort_by': 'name', 'sort_order': 'invalid_order'})
        assert response.status_code in [200, 400]

    def test_large_page_size(self):
        response = requests.get(API_ENDPOINT, params={'page': 1, 'page_size': 1000})
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']['items']) <= 100

    def test_empty_search_value(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'name', 'search_value': ''})
        assert response.status_code in [200, 400]

    def test_special_characters_in_fuzzy_search(self):
        payload = {'name': 'C++ Programming', 'category': 'Programming', 'score': 90.0}
        create_response = requests.post(API_ENDPOINT, json=payload)
        if create_response.status_code in [200, 201]:
            created_id = create_response.json()['data']['id']
            response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'C++', 'page_size': 100})
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            requests.delete(f'{API_ENDPOINT}/{created_id}')

def test_special_characters_in_fuzzy_search(self):
    payload = {'name': 'C++ Programming', 'category': 'Programming', 'score': 90.0}
    create_response = requests.post(API_ENDPOINT, json=payload)
    if create_response.status_code in [200, 201]:
        created_id = create_response.json()['data']['id']
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'C++', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        requests.delete(f'{API_ENDPOINT}/{created_id}')

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

def test_malformed_login_request(self):
    """Test handling of malformed login requests"""
    malformed_requests = ['{"username": "test", "password": "pass"', '{"username": "test", "password": "pass",}', '{"username": "test", "password": pass}', '{"username": "test" "password": "pass"}']
    for malformed_request in malformed_requests:
        response = requests.post(f'{self.BASE_URL}/auth/login', data=malformed_request, headers={'Content-Type': 'application/json'})
        assert response.status_code == 400

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

def test_strong_passwords(self):
    """Test acceptance of strong passwords"""
    strong_passwords = ['TestPass123!', 'MyStr0ng#Pass', 'ComplexP@ssw0rd', 'Secure123$Pass', 'StrongP@ss1!']
    for i, password in enumerate(strong_passwords):
        user_data = {'username': f'test_strong_password_{i}', 'email': f'strongpassword{i}@example.com', 'password': password, 'full_name': f'Strong Password User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_id = response.json()['id']
        requests.delete(f'{self.BASE_URL}/users/{user_id}')

def test_valid_usernames(self):
    """Test acceptance of valid usernames"""
    valid_usernames = ['user123', 'testuser', 'User123', 'test_user_123', 'user123test', 'a1b2c3', 'test123user']
    for i, username in enumerate(valid_usernames):
        user_data = {'username': username, 'email': f'validusername{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Valid Username User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_id = response.json()['id']
        requests.delete(f'{self.BASE_URL}/users/{user_id}')

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

@pytest.fixture
def created_user(api_base_url, sample_user_data):
    """Create a test user and return user data"""
    response = requests.post(f'{api_base_url}/users', json=sample_user_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 201:
        return response.json()
    else:
        pytest.fail(f'Failed to create test user: {response.text}')

@pytest.fixture
def created_admin_user(api_base_url, admin_user_data):
    """Create a test admin user and return user data"""
    response = requests.post(f'{api_base_url}/users', json=admin_user_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 201:
        return response.json()
    else:
        pytest.fail(f'Failed to create test admin user: {response.text}')

@pytest.fixture
def auth_token(api_base_url, created_user):
    """Get authentication token for a test user"""
    login_data = {'username': created_user['username'], 'password': 'TestPass123!'}
    response = requests.post(f'{api_base_url}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        pytest.fail(f'Failed to get auth token: {response.text}')

@pytest.fixture
def admin_auth_token(api_base_url, created_admin_user):
    """Get authentication token for a test admin user"""
    login_data = {'username': created_admin_user['username'], 'password': 'AdminPass123!'}
    response = requests.post(f'{api_base_url}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        pytest.fail(f'Failed to get admin auth token: {response.text}')

@pytest.mark.edge
def test_upload_large_file_within_limit(api_base_url, auth_headers):
    """Test uploading a file close to but within the size limit"""
    file_size = 5 * 1024 * 1024
    large_content = b'x' * file_size
    large_file = io.BytesIO(large_content)
    files = {'file': ('large_file.bin', large_file, 'application/octet-stream')}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=120)
    assert resp.status_code in (200, 201)
    if resp.status_code in (200, 201):
        file_id = resp.json().get('id')
        if file_id:
            requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)

# Node: BytesIO
@pytest.mark.edge
def test_special_characters_in_filename(api_base_url, auth_headers):
    """Test uploading files with special characters in filename"""
    special_filenames = ['file with spaces.txt', 'file-with-dashes.txt', 'file_with_underscores.txt', 'file.multiple.dots.txt', 'file(with)parentheses.txt', 'file[with]brackets.txt']
    uploaded_ids = []
    for filename in special_filenames:
        file_content = io.BytesIO(b'Test content for special filename')
        files = {'file': (filename, file_content, 'text/plain')}
        resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
        assert resp.status_code in (200, 201, 400)
        if resp.status_code in (200, 201):
            file_id = resp.json().get('id')
            if file_id:
                uploaded_ids.append(file_id)
    for file_id in uploaded_ids:
        try:
            requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
        except:
            pass

@pytest.mark.edge
def test_unicode_filename(api_base_url, auth_headers):
    """Test uploading files with Unicode characters in filename"""
    unicode_filenames = ['文档.txt', 'ファイル.txt', 'файл.txt', 'αρχείο.txt', 'café.txt', 'emoji_😀.txt']
    uploaded_ids = []
    for filename in unicode_filenames:
        file_content = io.BytesIO(b'Unicode filename test')
        files = {'file': (filename, file_content, 'text/plain')}
        resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
        assert resp.status_code in (200, 201, 400)
        if resp.status_code in (200, 201):
            file_id = resp.json().get('id')
            if file_id:
                uploaded_ids.append(file_id)
    for file_id in uploaded_ids:
        try:
            requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
        except:
            pass

@pytest.mark.edge
def test_path_traversal_in_filename(api_base_url, auth_headers):
    """Test that path traversal attempts in filename are blocked"""
    malicious_filenames = ['../../../etc/passwd', '..\\..\\..\\windows\\system32\\config\\sam', '../../../../root/.ssh/id_rsa']
    for filename in malicious_filenames:
        file_content = io.BytesIO(b'Malicious content')
        files = {'file': (filename, file_content, 'text/plain')}
        resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
        if resp.status_code in (200, 201):
            file_data = resp.json()
            saved_filename = file_data.get('filename', '')
            assert '..' not in saved_filename or '/' not in saved_filename or '\\' not in saved_filename
            file_id = file_data.get('id')
            if file_id:
                requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)

def upload_file(index):
    file_content = io.BytesIO(f'Concurrent upload test {index}'.encode())
    files = {'file': (f'concurrent_{index}.txt', file_content, 'text/plain')}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
    return resp

@pytest.mark.edge
def test_invalid_file_id_formats(api_base_url, auth_headers):
    """Test operations with invalid file ID formats"""
    invalid_ids = ['invalid-id', '../../etc/passwd', '<script>alert(1)</script>', "'; DROP TABLE files; --", '', 'a' * 1000]
    for file_id in invalid_ids:
        resp = requests.get(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
        assert resp.status_code in (400, 404)
        resp = requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
        assert resp.status_code in (400, 404)

@pytest.mark.edge
def test_very_long_description(api_base_url, auth_headers):
    """Test uploading file with very long description"""
    file_content = io.BytesIO(b'Test content')
    long_description = 'A' * 600
    files = {'file': ('test.txt', file_content, 'text/plain')}
    data = {'description': long_description}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, data=data, timeout=30)
    if resp.status_code in (200, 201):
        file_data = resp.json()
        assert 'description' in file_data
        file_id = file_data.get('id')
        if file_id:
            requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
    else:
        assert resp.status_code == 400

@pytest.mark.edge
def test_double_deletion(api_base_url, auth_headers, sample_text_file):
    """Test deleting the same file twice"""
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    upload_resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
    assert upload_resp.status_code in (200, 201)
    file_id = upload_resp.json().get('id')
    delete_resp1 = requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
    assert delete_resp1.status_code == 200
    delete_resp2 = requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
    assert delete_resp2.status_code == 404

@pytest.mark.edge
def test_access_deleted_file(api_base_url, auth_headers, sample_text_file):
    """Test accessing a file after it has been deleted"""
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    upload_resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
    assert upload_resp.status_code in (200, 201)
    file_id = upload_resp.json().get('id')
    delete_resp = requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
    assert delete_resp.status_code == 200
    info_resp = requests.get(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
    assert info_resp.status_code == 404
    download_resp = requests.get(f'{api_base_url}/files/{file_id}/download', headers=auth_headers, timeout=10)
    assert download_resp.status_code == 404

@pytest.mark.edge
def test_unsupported_file_type(api_base_url, auth_headers):
    """Test uploading an unsupported file type"""
    file_content = io.BytesIO(b'MZ\x90\x00')
    files = {'file': ('malicious.exe', file_content, 'application/x-msdownload')}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
    assert resp.status_code in (200, 201, 415)
    if resp.status_code in (200, 201):
        file_id = resp.json().get('id')
        if file_id:
            requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)

@pytest.mark.auth
def test_user_registration_invalid_username(api_base_url, wait_for_service):
    """Test user registration with invalid username"""
    invalid_credentials = [{'username': 'ab', 'password': 'ValidPass123!'}, {'username': 'a' * 50, 'password': 'ValidPass123!'}, {'username': 'user@invalid', 'password': 'ValidPass123!'}]
    for creds in invalid_credentials:
        resp = requests.post(f'{api_base_url}/auth/register', json=creds, timeout=10)
        assert resp.status_code == 400, f'Expected 400 for invalid username: {creds['username']}'

@pytest.mark.auth
def test_user_registration_duplicate(api_base_url, registered_user):
    """Test user registration with duplicate username"""
    resp = requests.post(f'{api_base_url}/auth/register', json=registered_user, timeout=10)
    assert resp.status_code == 409

@pytest.mark.auth
def test_user_login(api_base_url, registered_user):
    """Test user login with valid credentials"""
    resp = requests.post(f'{api_base_url}/auth/login', json=registered_user, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert 'access_token' in data
    assert data.get('token_type') == 'Bearer' or 'token_type' in data

@pytest.mark.auth
def test_user_login_invalid_credentials(api_base_url, registered_user):
    """Test user login with invalid credentials"""
    invalid_creds = {'username': registered_user['username'], 'password': 'WrongPassword123!'}
    resp = requests.post(f'{api_base_url}/auth/login', json=invalid_creds, timeout=10)
    assert resp.status_code == 401

@pytest.mark.upload
def test_upload_text_file(api_base_url, auth_headers, sample_text_file):
    """Test uploading a text file"""
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    data = {'description': 'Test text file upload', 'tags': 'test,text'}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, data=data, timeout=30)
    assert resp.status_code in (200, 201)
    file_data = resp.json()
    assert 'id' in file_data
    assert file_data.get('filename') == filename
    assert 'size' in file_data
    assert file_data['size'] > 0
    assert 'upload_time' in file_data
    assert 'uploader' in file_data
    file_id = file_data.get('id')
    if file_id:
        requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)

@pytest.mark.upload
def test_upload_pdf_file(api_base_url, auth_headers, sample_pdf_file):
    """Test uploading a PDF document"""
    file_obj, filename, content_type = sample_pdf_file
    files = {'file': (filename, file_obj, content_type)}
    data = {'description': 'Test PDF upload', 'tags': 'pdf,document,test'}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, data=data, timeout=30)
    assert resp.status_code in (200, 201)
    file_data = resp.json()
    assert 'id' in file_data
    assert file_data.get('filename') == filename
    file_id = file_data.get('id')
    if file_id:
        requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)

@pytest.mark.upload
def test_upload_without_auth(api_base_url, sample_text_file):
    """Test uploading a file without authentication"""
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    resp = requests.post(f'{api_base_url}/files', files=files, timeout=30)
    assert resp.status_code == 401

@pytest.mark.upload
def test_upload_empty_file(api_base_url, auth_headers):
    """Test uploading an empty file"""
    empty_file = io.BytesIO(b'')
    files = {'file': ('empty.txt', empty_file, 'text/plain')}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
    assert resp.status_code in (400, 201, 200)

@pytest.mark.api
def test_delete_file(api_base_url, auth_headers, sample_text_file):
    """Test deleting a file"""
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    upload_resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=30)
    assert upload_resp.status_code in (200, 201)
    file_id = upload_resp.json().get('id')
    delete_resp = requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert data.get('success') is True or 'success' in data

@pytest.mark.api
def test_delete_file_not_found(api_base_url, auth_headers):
    """Test deleting a non-existent file"""
    resp = requests.delete(f'{api_base_url}/files/nonexistent_file_id', headers=auth_headers, timeout=10)
    assert resp.status_code == 404

@pytest.mark.api
def test_delete_file_by_non_owner(api_base_url, auth_headers, uploaded_file, second_user_token):
    """Test that a user cannot delete another user's file"""
    second_user_headers = {'Authorization': f'Bearer {second_user_token}'}
    resp = requests.delete(f'{api_base_url}/files/{uploaded_file}', headers=second_user_headers, timeout=10)
    assert resp.status_code == 403

@pytest.fixture
def registered_user(api_base_url, wait_for_service, user_credentials):
    """Register a test user and return credentials"""
    try:
        resp = requests.post(f'{api_base_url}/auth/register', json=user_credentials, timeout=10)
        if resp.status_code in (201, 409):
            return user_credentials
    except Exception as e:
        pytest.fail(f'Failed to register user: {e}')
    return user_credentials

@pytest.fixture
def auth_token(api_base_url, registered_user):
    """Login and get authentication token"""
    resp = requests.post(f'{api_base_url}/auth/login', json=registered_user, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if 'access_token' in data:
            return data['access_token']
    pytest.fail(f'Login failed: {resp.status_code} {resp.text}')

@pytest.fixture
def sample_text_file():
    """Create a sample text file for upload testing"""
    content = b'This is a test file for File Relay service.\nLine 2\nLine 3'
    return (io.BytesIO(content), 'test_file.txt', 'text/plain')

@pytest.fixture
def sample_image_file():
    """Create a minimal PNG image file for testing"""
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return (io.BytesIO(png_data), 'test_image.png', 'image/png')

@pytest.fixture
def sample_pdf_file():
    """Create a minimal PDF file for testing"""
    pdf_data = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test PDF) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000317 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n409\n%%EOF\n'
    return (io.BytesIO(pdf_data), 'test_document.pdf', 'application/pdf')

@pytest.fixture
def uploaded_file(api_base_url, auth_headers, sample_text_file):
    """Upload a file and return its ID for testing"""
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    data = {'description': 'Test file for automated tests', 'tags': 'test,automation'}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, data=data, timeout=30)
    if resp.status_code in (200, 201):
        file_data = resp.json()
        file_id = file_data.get('id')
        if file_id:
            yield file_id
            try:
                requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)
            except:
                pass
        else:
            pytest.fail('File upload succeeded but no ID returned')
    else:
        pytest.fail(f'Failed to upload test file: {resp.status_code} {resp.text}')

def assert_response_error(response: requests.Response, expected_status: int):
    """Assert response is an error."""
    assert response.status_code == expected_status, f'Expected error {expected_status}, got {response.status_code}. Response: {response.text}'
    try:
        error_data = response.json()
        assert 'error' in error_data, "Error response should contain 'error' field"
        assert 'code' in error_data['error'], "Error should contain 'code' field"
        assert 'message' in error_data['error'], "Error should contain 'message' field"
    except json.JSONDecodeError:
        pytest.fail(f'Invalid JSON in error response: {response.text}')

class TestEdgeCases:
    BASE_URL = 'http://localhost:8080/api/v1'

    def test_register_empty_request_body(self):
        response = requests.post(f'{self.BASE_URL}/users/register', json={})
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'required' in data['message'].lower()

    def test_register_missing_required_fields(self):
        incomplete_user = {'username': 'testuser'}
        response = requests.post(f'{self.BASE_URL}/users/register', json=incomplete_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_register_username_too_long(self):
        long_username_user = {'username': 'a' * 21, 'email': 'test@example.com', 'password': 'password123'}
        response = requests.post(f'{self.BASE_URL}/users/register', json=long_username_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'username' in data['message'].lower()

    def test_register_username_too_short(self):
        short_username_user = {'username': 'ab', 'email': 'test@example.com', 'password': 'password123'}
        response = requests.post(f'{self.BASE_URL}/users/register', json=short_username_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'username' in data['message'].lower()

    def test_register_password_too_long(self):
        long_password_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'a' * 51}
        response = requests.post(f'{self.BASE_URL}/users/register', json=long_password_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'password' in data['message'].lower()

    def test_register_full_name_too_long(self):
        long_name_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123', 'full_name': 'a' * 101}
        response = requests.post(f'{self.BASE_URL}/users/register', json=long_name_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'full_name' in data['message'].lower()

    def test_register_special_characters_in_username(self):
        special_char_user = {'username': 'test@user#', 'email': 'test@example.com', 'password': 'password123'}
        response = requests.post(f'{self.BASE_URL}/users/register', json=special_char_user)
        assert response.status_code in [200, 400]
        data = response.json()
        if response.status_code == 400:
            assert data['success'] is False

    def test_login_empty_credentials(self):
        response = requests.post(f'{self.BASE_URL}/users/login', json={})
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_login_missing_password(self):
        login_data = {'username': 'testuser'}
        response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_get_user_info_nonexistent_user(self):
        test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123'}
        requests.post(f'{self.BASE_URL}/users/register', json=test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': test_user['username'], 'password': test_user['password']})
        token = login_response.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{self.BASE_URL}/users/99999', headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False

    def test_update_user_info_empty_body(self):
        test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123'}
        requests.post(f'{self.BASE_URL}/users/register', json=test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': test_user['username'], 'password': test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json={}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    def test_update_user_info_duplicate_email(self):
        user1 = {'username': 'user1', 'email': 'user1@example.com', 'password': 'password123'}
        user2 = {'username': 'user2', 'email': 'user2@example.com', 'password': 'password123'}
        requests.post(f'{self.BASE_URL}/users/register', json=user1)
        requests.post(f'{self.BASE_URL}/users/register', json=user2)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': user2['username'], 'password': user2['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        update_data = {'email': user1['email']}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'email' in data['message'].lower()

    def test_access_other_user_data(self):
        user1 = {'username': 'user1', 'email': 'user1@example.com', 'password': 'password123'}
        user2 = {'username': 'user2', 'email': 'user2@example.com', 'password': 'password123'}
        requests.post(f'{self.BASE_URL}/users/register', json=user1)
        requests.post(f'{self.BASE_URL}/users/register', json=user2)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': user1['username'], 'password': user1['password']})
        token = login_response.json()['data']['access_token']
        user1_id = login_response.json()['data']['user']['user_id']
        login_response2 = requests.post(f'{self.BASE_URL}/users/login', json={'username': user2['username'], 'password': user2['password']})
        user2_id = login_response2.json()['data']['user']['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{self.BASE_URL}/users/{user2_id}', headers=headers)
        assert response.status_code == 403
        data = response.json()
        assert data['success'] is False

    def test_malformed_json_request(self):
        response = requests.post(f'{self.BASE_URL}/users/register', data='invalid json', headers={'Content-Type': 'application/json'})
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_unsupported_http_methods(self):
        response = requests.get(f'{self.BASE_URL}/users/register')
        assert response.status_code == 405
        response = requests.put(f'{self.BASE_URL}/users/login')
        assert response.status_code == 405

    def test_invalid_url_path(self):
        response = requests.get(f'{self.BASE_URL}/invalid/path')
        assert response.status_code == 404
        response = requests.post(f'{self.BASE_URL}/users/invalid')
        assert response.status_code == 404

def test_register_empty_request_body(self):
    response = requests.post(f'{self.BASE_URL}/users/register', json={})
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'required' in data['message'].lower()

def test_register_missing_required_fields(self):
    incomplete_user = {'username': 'testuser'}
    response = requests.post(f'{self.BASE_URL}/users/register', json=incomplete_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False

def test_register_username_too_long(self):
    long_username_user = {'username': 'a' * 21, 'email': 'test@example.com', 'password': 'password123'}
    response = requests.post(f'{self.BASE_URL}/users/register', json=long_username_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'username' in data['message'].lower()

def test_register_username_too_short(self):
    short_username_user = {'username': 'ab', 'email': 'test@example.com', 'password': 'password123'}
    response = requests.post(f'{self.BASE_URL}/users/register', json=short_username_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'username' in data['message'].lower()

def test_register_password_too_long(self):
    long_password_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'a' * 51}
    response = requests.post(f'{self.BASE_URL}/users/register', json=long_password_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'password' in data['message'].lower()

def test_register_full_name_too_long(self):
    long_name_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123', 'full_name': 'a' * 101}
    response = requests.post(f'{self.BASE_URL}/users/register', json=long_name_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'full_name' in data['message'].lower()

def test_register_special_characters_in_username(self):
    special_char_user = {'username': 'test@user#', 'email': 'test@example.com', 'password': 'password123'}
    response = requests.post(f'{self.BASE_URL}/users/register', json=special_char_user)
    assert response.status_code in [200, 400]
    data = response.json()
    if response.status_code == 400:
        assert data['success'] is False

def test_login_empty_credentials(self):
    response = requests.post(f'{self.BASE_URL}/users/login', json={})
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False

def test_login_missing_password(self):
    login_data = {'username': 'testuser'}
    response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False

def test_get_user_info_nonexistent_user(self):
    test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123'}
    requests.post(f'{self.BASE_URL}/users/register', json=test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': test_user['username'], 'password': test_user['password']})
    token = login_response.json()['data']['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{self.BASE_URL}/users/99999', headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data['success'] is False

def test_update_user_info_empty_body(self):
    test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123'}
    requests.post(f'{self.BASE_URL}/users/register', json=test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': test_user['username'], 'password': test_user['password']})
    token = login_response.json()['data']['access_token']
    user_id = login_response.json()['data']['user']['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.put(f'{self.BASE_URL}/users/{user_id}', json={}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True

def test_update_user_info_duplicate_email(self):
    user1 = {'username': 'user1', 'email': 'user1@example.com', 'password': 'password123'}
    user2 = {'username': 'user2', 'email': 'user2@example.com', 'password': 'password123'}
    requests.post(f'{self.BASE_URL}/users/register', json=user1)
    requests.post(f'{self.BASE_URL}/users/register', json=user2)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': user2['username'], 'password': user2['password']})
    token = login_response.json()['data']['access_token']
    user_id = login_response.json()['data']['user']['user_id']
    update_data = {'email': user1['email']}
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'email' in data['message'].lower()

def test_access_other_user_data(self):
    user1 = {'username': 'user1', 'email': 'user1@example.com', 'password': 'password123'}
    user2 = {'username': 'user2', 'email': 'user2@example.com', 'password': 'password123'}
    requests.post(f'{self.BASE_URL}/users/register', json=user1)
    requests.post(f'{self.BASE_URL}/users/register', json=user2)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': user1['username'], 'password': user1['password']})
    token = login_response.json()['data']['access_token']
    user1_id = login_response.json()['data']['user']['user_id']
    login_response2 = requests.post(f'{self.BASE_URL}/users/login', json={'username': user2['username'], 'password': user2['password']})
    user2_id = login_response2.json()['data']['user']['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{self.BASE_URL}/users/{user2_id}', headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data['success'] is False

def test_malformed_json_request(self):
    response = requests.post(f'{self.BASE_URL}/users/register', data='invalid json', headers={'Content-Type': 'application/json'})
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False

def test_unsupported_http_methods(self):
    response = requests.get(f'{self.BASE_URL}/users/register')
    assert response.status_code == 405
    response = requests.put(f'{self.BASE_URL}/users/login')
    assert response.status_code == 405

class TestUserAPI:
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123', 'full_name': 'Test User'}
        self.access_token = None
        self.user_id = None

    def test_user_registration_success(self):
        response = requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert 'user_id' in data['data']
        assert data['data']['username'] == self.test_user['username']
        assert data['data']['email'] == self.test_user['email']
        assert data['data']['full_name'] == self.test_user['full_name']
        assert 'created_at' in data['data']
        self.user_id = data['data']['user_id']

    def test_user_registration_duplicate_username(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        response = requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'username' in data['message'].lower()

    def test_user_registration_invalid_email(self):
        invalid_user = self.test_user.copy()
        invalid_user['email'] = 'invalid-email'
        response = requests.post(f'{self.BASE_URL}/users/register', json=invalid_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'email' in data['message'].lower()

    def test_user_registration_short_password(self):
        invalid_user = self.test_user.copy()
        invalid_user['password'] = '123'
        response = requests.post(f'{self.BASE_URL}/users/register', json=invalid_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'password' in data['message'].lower()

    def test_user_login_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
        response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert data['data']['token_type'] == 'Bearer'
        assert 'expires_in' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['username'] == self.test_user['username']
        self.access_token = data['data']['access_token']
        self.user_id = data['data']['user']['user_id']

    def test_user_login_invalid_credentials(self):
        login_data = {'username': 'nonexistent', 'password': 'wrongpassword'}
        response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'credentials' in data['message'].lower() or 'invalid' in data['message'].lower()

    def test_get_user_info_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{self.BASE_URL}/users/{user_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['user_id'] == user_id
        assert data['data']['username'] == self.test_user['username']
        assert data['data']['email'] == self.test_user['email']
        assert data['data']['full_name'] == self.test_user['full_name']
        assert 'created_at' in data['data']
        assert 'updated_at' in data['data']

    def test_get_user_info_unauthorized(self):
        response = requests.get(f'{self.BASE_URL}/users/1')
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'authorization' in data['message'].lower() or 'token' in data['message'].lower()

    def test_get_user_info_invalid_token(self):
        headers = {'Authorization': 'Bearer invalid_token'}
        response = requests.get(f'{self.BASE_URL}/users/1', headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False

    def test_update_user_info_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        update_data = {'email': 'newemail@example.com', 'full_name': 'Updated Name'}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['email'] == update_data['email']
        assert data['data']['full_name'] == update_data['full_name']
        assert data['data']['username'] == self.test_user['username']
        assert 'updated_at' in data['data']

    def test_update_user_info_unauthorized(self):
        update_data = {'email': 'newemail@example.com'}
        response = requests.put(f'{self.BASE_URL}/users/1', json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False

    def test_update_user_info_invalid_email(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        update_data = {'email': 'invalid-email'}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'email' in data['message'].lower()

    def test_delete_user_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.delete(f'{self.BASE_URL}/users/{user_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        get_response = requests.get(f'{self.BASE_URL}/users/{user_id}', headers=headers)
        assert get_response.status_code == 404

    def test_delete_user_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/users/1')
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False

    def test_delete_nonexistent_user(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.delete(f'{self.BASE_URL}/users/99999', headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False

def test_user_registration_success(self):
    response = requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    assert response.status_code == 201
    data = response.json()
    assert data['success'] is True
    assert 'user_id' in data['data']
    assert data['data']['username'] == self.test_user['username']
    assert data['data']['email'] == self.test_user['email']
    assert data['data']['full_name'] == self.test_user['full_name']
    assert 'created_at' in data['data']
    self.user_id = data['data']['user_id']

def test_user_registration_duplicate_username(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    response = requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'username' in data['message'].lower()

def test_user_registration_invalid_email(self):
    invalid_user = self.test_user.copy()
    invalid_user['email'] = 'invalid-email'
    response = requests.post(f'{self.BASE_URL}/users/register', json=invalid_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'email' in data['message'].lower()

def test_user_registration_short_password(self):
    invalid_user = self.test_user.copy()
    invalid_user['password'] = '123'
    response = requests.post(f'{self.BASE_URL}/users/register', json=invalid_user)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'password' in data['message'].lower()

def test_user_login_success(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
    response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'access_token' in data['data']
    assert data['data']['token_type'] == 'Bearer'
    assert 'expires_in' in data['data']
    assert 'user' in data['data']
    assert data['data']['user']['username'] == self.test_user['username']
    self.access_token = data['data']['access_token']
    self.user_id = data['data']['user']['user_id']

def test_user_login_invalid_credentials(self):
    login_data = {'username': 'nonexistent', 'password': 'wrongpassword'}
    response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
    assert response.status_code == 401
    data = response.json()
    assert data['success'] is False
    assert 'credentials' in data['message'].lower() or 'invalid' in data['message'].lower()

def test_get_user_info_success(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
    token = login_response.json()['data']['access_token']
    user_id = login_response.json()['data']['user']['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{self.BASE_URL}/users/{user_id}', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['data']['user_id'] == user_id
    assert data['data']['username'] == self.test_user['username']
    assert data['data']['email'] == self.test_user['email']
    assert data['data']['full_name'] == self.test_user['full_name']
    assert 'created_at' in data['data']
    assert 'updated_at' in data['data']

def test_update_user_info_success(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
    token = login_response.json()['data']['access_token']
    user_id = login_response.json()['data']['user']['user_id']
    update_data = {'email': 'newemail@example.com', 'full_name': 'Updated Name'}
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['data']['email'] == update_data['email']
    assert data['data']['full_name'] == update_data['full_name']
    assert data['data']['username'] == self.test_user['username']
    assert 'updated_at' in data['data']

def test_update_user_info_unauthorized(self):
    update_data = {'email': 'newemail@example.com'}
    response = requests.put(f'{self.BASE_URL}/users/1', json=update_data)
    assert response.status_code == 401
    data = response.json()
    assert data['success'] is False

def test_update_user_info_invalid_email(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
    token = login_response.json()['data']['access_token']
    user_id = login_response.json()['data']['user']['user_id']
    update_data = {'email': 'invalid-email'}
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'email' in data['message'].lower()

def test_delete_user_success(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
    token = login_response.json()['data']['access_token']
    user_id = login_response.json()['data']['user']['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.delete(f'{self.BASE_URL}/users/{user_id}', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    get_response = requests.get(f'{self.BASE_URL}/users/{user_id}', headers=headers)
    assert get_response.status_code == 404

def test_delete_user_unauthorized(self):
    response = requests.delete(f'{self.BASE_URL}/users/1')
    assert response.status_code == 401
    data = response.json()
    assert data['success'] is False

def test_delete_nonexistent_user(self):
    requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
    login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
    token = login_response.json()['data']['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.delete(f'{self.BASE_URL}/users/99999', headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data['success'] is False

@pytest.fixture
def registered_user(api_base_url, test_user_data, wait_for_service):
    try:
        requests.delete(f'{api_base_url}/users/cleanup', timeout=5)
    except:
        pass
    response = requests.post(f'{api_base_url}/users/register', json=test_user_data)
    if response.status_code == 201:
        user_data = response.json()['data']
        return user_data
    elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
        login_response = requests.post(f'{api_base_url}/users/login', json={'username': test_user_data['username'], 'password': test_user_data['password']})
        if login_response.status_code == 200:
            return login_response.json()['data']['user']
    pytest.fail('Failed to register or login test user')

@pytest.fixture
def auth_token(api_base_url, test_user_data, wait_for_service):
    login_data = {'username': test_user_data['username'], 'password': test_user_data['password']}
    response = requests.post(f'{api_base_url}/users/login', json=login_data)
    if response.status_code == 200:
        return response.json()['data']['access_token']
    pytest.fail('Failed to get auth token')

@pytest.mark.api
def test_unauthorized_access(api_base_url):
    r = requests.post(f'{api_base_url}/rooms', json={'name': 'private'})
    assert r.status_code in (401, 403)

@pytest.mark.api
def test_duplicate_room_conflict(api_base_url, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
    name = 'unique_room'
    r1 = requests.post(f'{api_base_url}/rooms', json={'name': name}, headers=headers)
    assert r1.status_code in (201, 409)
    r2 = requests.post(f'{api_base_url}/rooms', json={'name': name}, headers=headers)
    assert r2.status_code == 409

@pytest.mark.api
def test_send_without_join_forbidden(api_base_url, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
    name = 'temp_room'
    cr = requests.post(f'{api_base_url}/rooms', json={'name': name}, headers=headers)
    if cr.status_code == 201:
        room_id = cr.json()['id']
    else:
        rooms = requests.get(f'{api_base_url}/rooms?page=1&page_size=100').json().get('rooms', [])
        room_id = next((r['id'] for r in rooms if r.get('name') == name), None)
    assert room_id
    s = requests.post(f'{api_base_url}/rooms/{room_id}/messages', json={'content': 'x'}, headers=headers)
    assert s.status_code == 403

# Node: next
@pytest.mark.api
def test_unicode_and_length_limits(api_base_url, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
    cr = requests.post(f'{api_base_url}/rooms', json={'name': 'i18n'}, headers=headers)
    room_id = cr.json().get('id') if cr.status_code == 201 else None
    if not room_id:
        rooms = requests.get(f'{api_base_url}/rooms').json().get('rooms', [])
        room_id = next((r['id'] for r in rooms if r.get('name') == 'i18n'), None)
    assert room_id
    requests.post(f'{api_base_url}/rooms/{room_id}/join', headers=headers)
    ok = requests.post(f'{api_base_url}/rooms/{room_id}/messages', json={'content': 'Hello, world 🌍'}, headers=headers)
    assert ok.status_code in (200, 201)
    too_long = 'a' * 1001
    bad = requests.post(f'{api_base_url}/rooms/{room_id}/messages', json={'content': too_long}, headers=headers)
    assert bad.status_code == 400

@pytest.fixture
def registered_user(api_base_url, wait_for_service, user_credentials):
    try:
        requests.post(f'{api_base_url}/auth/register', json=user_credentials, timeout=5)
    except Exception:
        pass
    return user_credentials

@pytest.fixture
def auth_token(api_base_url, registered_user):
    resp = requests.post(f'{api_base_url}/auth/login', json=registered_user)
    if resp.status_code == 200 and 'access_token' in resp.json():
        return resp.json()['access_token']
    pytest.skip(f'Login failed: {resp.status_code} {resp.text}')

@pytest.mark.api
def test_register_and_login(api_base_url, wait_for_service):
    creds = {'username': 'test_user_login', 'password': 'Password123!'}
    r1 = requests.post(f'{api_base_url}/auth/register', json=creds)
    assert r1.status_code in (201, 409)
    r2 = requests.post(f'{api_base_url}/auth/login', json=creds)
    assert r2.status_code == 200
    assert 'access_token' in r2.json()

@pytest.mark.api
def test_create_and_list_rooms(api_base_url, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
    room = {'name': 'general'}
    r = requests.post(f'{api_base_url}/rooms', json=room, headers=headers)
    assert r.status_code in (201, 409)
    q = requests.get(f'{api_base_url}/rooms?page=1&page_size=20')
    assert q.status_code == 200
    data = q.json()
    assert 'rooms' in data and isinstance(data['rooms'], list)

@pytest.mark.api
def test_join_leave_room_and_messaging_flow(api_base_url, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
    room_name = 'dev'
    cr = requests.post(f'{api_base_url}/rooms', json={'name': room_name}, headers=headers)
    if cr.status_code == 201:
        room_id = cr.json()['id']
    else:
        lst = requests.get(f'{api_base_url}/rooms?page=1&page_size=50').json()['rooms']
        room_id = next((r['id'] for r in lst if r.get('name') == room_name), None)
        assert room_id is not None
    j = requests.post(f'{api_base_url}/rooms/{room_id}/join', headers=headers)
    assert j.status_code in (200, 201)
    assert j.json().get('joined') is True
    msg = {'content': 'hello world'}
    s = requests.post(f'{api_base_url}/rooms/{room_id}/messages', json=msg, headers=headers)
    assert s.status_code in (200, 201)
    sent = s.json()
    assert sent.get('content') == 'hello world'
    assert sent.get('room_id') == room_id
    f = requests.get(f'{api_base_url}/rooms/{room_id}/messages?limit=50', headers=headers)
    assert f.status_code == 200
    messages = f.json().get('messages', [])
    assert any((m.get('content') == 'hello world' for m in messages))
    l = requests.post(f'{api_base_url}/rooms/{room_id}/leave', headers=headers)
    assert l.status_code in (200, 201)
    assert l.json().get('left') is True

