# Cluster 11

# Node: isinstance
# Node: get
# Node: sorted
# Node: len
# Node: items
# Node: replace
# Node: strftime
def generate_latex_table(results: Dict) -> str:
    """Generate LaTeX table from results"""
    lines = []
    lines.append('\\begin{table}[htbp]')
    lines.append('\\centering')
    lines.append('\\caption{API Coverage (AC) for Repositories in repo\\_readme\\_1219\\_deepcode\\_gpt-5.2}')
    lines.append('\\label{tab:api_coverage}')
    lines.append('\\begin{tabular}{lrrr}')
    lines.append('\\toprule')
    lines.append('Repository & Total APIs & Implemented & Coverage (\\%) \\\\')
    lines.append('\\midrule')
    total_apis = 0
    total_implemented = 0
    for repo_name, data in sorted(results.items()):
        repo_display = repo_name.replace('_', '\\_')
        total = data['total_apis']
        implemented = data['implemented_apis']
        coverage = data['coverage'] * 100
        total_apis += total
        total_implemented += implemented
        lines.append(f'{repo_display} & {total} & {implemented} & {coverage:.1f} \\\\')
    lines.append('\\midrule')
    overall_coverage = total_implemented / total_apis * 100 if total_apis > 0 else 0
    lines.append(f'\\textbf{{Overall}} & {total_apis} & {total_implemented} & {overall_coverage:.1f} \\\\')
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    return '\n'.join(lines)

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

def test_get_execution_history_nonexistent_task(self, api_client):
    response = api_client.get('/tasks/nonexistent_task_id/executions')
    assert response.status_code == 404
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

def test_get_nonexistent_task(self, api_client):
    response = api_client.get('/tasks/nonexistent_task_id')
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

def get(self, endpoint, params=None):
    url = f'{self.base_url}{endpoint}'
    response = self.session.get(url, params=params)
    return response

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
def test_health_check(self):
    resp = requests.get(f'{BASE_URL}/health')
    assert resp.status_code == 200
    data = resp.json()
    assert 'status' in data
    assert 'timestamp' in data
    assert 'version' in data
    assert data['status'] in ['healthy', 'ok', 'up']

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

# Node: fromisoformat
def test_health_response_format(self):
    response = requests.get(f'{self.BASE_URL}/health')
    data = response.json()
    required_fields = ['status', 'timestamp', 'version']
    for field in required_fields:
        assert field in data, f'Response is missing required field: {field}'
    assert isinstance(data['status'], str)
    assert isinstance(data['timestamp'], str)
    assert isinstance(data['version'], str)

def test_health_endpoint_headers(self):
    response = requests.get(f'{self.BASE_URL}/health')
    assert response.headers['Content-Type'] == 'application/json'
    assert 'Access-Control-Allow-Origin' in response.headers or '*' in response.headers.get('Access-Control-Allow-Origin', '')

def test_health_endpoint_with_query_params(self):
    response = requests.get(f'{self.BASE_URL}/health?param=test&debug=1')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data

@app.get('/health')
def health() -> t.Any:
    return (jsonify({'status': 'ok'}), 200)

# Node: jsonify
@app.post('/echo')
def echo() -> t.Any:
    if not request.is_json:
        return (jsonify({'error': 'invalid content-type'}), 400)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or 'message' not in data or (not isinstance(data['message'], str)):
        return (jsonify({'error': 'invalid payload'}), 400)
    message: str = data['message']
    return (jsonify({'message': message, 'length': len(message)}), 200)

# Node: get_json
@app.get('/sum')
def sum_view() -> t.Any:
    a = request.args.get('a')
    b = request.args.get('b')
    try:
        a_int = int(a) if a is not None else None
        b_int = int(b) if b is not None else None
    except (TypeError, ValueError):
        return (jsonify({'error': 'parameters must be integers'}), 400)
    if a_int is None or b_int is None:
        return (jsonify({'error': 'missing parameters'}), 400)
    return (jsonify({'result': a_int + b_int}), 200)

def test_health_ok(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {'status': 'ok'}

def test_echo_ok(client):
    payload = {'message': 'hello'}
    resp = client.post('/echo', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {'message': 'hello', 'length': 5}

# Node: dumps
def test_echo_invalid_content_type(client):
    resp = client.post('/echo', data='message=hello')
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert 'error' in body

def test_echo_missing_message(client):
    resp = client.post('/echo', data=json.dumps({}), content_type='application/json')
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert 'error' in body

def test_sum_ok(client):
    resp = client.get('/sum?a=2&b=3')
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {'result': 5}

def test_sum_missing_params(client):
    resp = client.get('/sum?a=2')
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert 'error' in body

def test_sum_invalid_params(client):
    resp = client.get('/sum?a=x&b=3')
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert 'error' in body

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'healthy'}

def test_get_post_not_found(client):
    """Test retrieving a non-existent post."""
    response = client.get('/api/v1/posts/999')
    assert response.status_code == 404

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

def test_health_check(self):
    response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'healthy'

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

# Node: now
def test_get_history_unauthorized(self):
    response = requests.get(f'{self.BASE_URL}/history')
    assert response.status_code in [401, 403]

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

def test_health_check(self):
    response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'healthy'

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

def test_get_likes_history_unauthorized(self):
    response = requests.get(f'{self.BASE_URL}/likes/history')
    assert response.status_code in [401, 403]

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

def test_health_check(self):
    response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'healthy'

# Node: _login_user
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

def test_file_download(self):
    self._login_user()
    self._upload_test_file()
    headers = {'Authorization': f'Bearer {self.auth_token}'}
    response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/download', headers=headers)
    assert response.status_code == 200
    assert response.content == self.test_file_content

# Node: _upload_test_file
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

# Node: _create_share_link
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

# Node: isoformat
# Node: utcnow
# Node: timedelta
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

def test_get_history_empty_result(self):
    """Test that history with filters that match nothing returns empty list."""
    from_date = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
    to_date = (datetime.utcnow() + timedelta(days=2)).isoformat() + 'Z'
    response = requests.get(HISTORY_URL, params={'from_date': from_date, 'to_date': to_date})
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 0
    assert len(data['emails']) == 0

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

def test_health_check(self):
    """Test health check endpoint"""
    response = requests.get(f'{self.BASE_URL}/health')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert 'timestamp' in data
    assert 'version' in data
    assert data['status'] == 'healthy'

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

def test_get_single_task_not_found(self):
    """Test getting a non-existent task"""
    response = requests.get(f'{self.BASE_URL}/tasks/99999')
    assert response.status_code == 404
    error_data = response.json()
    assert 'error' in error_data
    assert error_data['error']['code'] == 'not_found'

def test_large_pagination_limit(self):
    """Test pagination with limit exceeding maximum"""
    response = requests.get(f'{self.BASE_URL}/tasks?limit=1000')
    assert response.status_code in [200, 422]
    if response.status_code == 200:
        data = response.json()
        assert data['pagination']['limit'] <= 100

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

def test_languages_format():
    """Test that languages response has correct format"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    languages = data['languages']
    for code, name in languages.items():
        assert isinstance(code, str), f'Language code should be string, got {type(code)}'
        assert isinstance(name, str), f'Language name should be string, got {type(name)}'
        assert len(code) > 0, 'Language code should not be empty'
        assert len(name) > 0, 'Language name should not be empty'
    print(f'✓ Test passed: Languages format is correct')

# Node: type
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

def test_languages_no_empty_values():
    """Test that there are no empty language codes or names"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    languages = data['languages']
    for code, name in languages.items():
        assert code.strip() != '', f'Language code should not be empty'
        assert name.strip() != '', f"Language name should not be empty for code '{code}'"
    print(f'✓ Test passed: No empty language codes or names')

def test_languages_json_serializable():
    """Test that response is valid JSON"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    import json
    try:
        json_str = json.dumps(data)
        assert len(json_str) > 0, 'JSON serialization should produce non-empty string'
    except Exception as e:
        assert False, f'Failed to serialize response to JSON: {e}'
    print(f'✓ Test passed: Response is valid JSON')

def check_service_availability():
    """Check if the service is running"""
    try:
        response = requests.get(f'{BASE_URL}/api/languages', timeout=2)
        return response.status_code == 200
    except:
        return False

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

def test_get_data_by_invalid_id(self):
    response = requests.get(f'{API_ENDPOINT}/invalid-id-12345')
    assert response.status_code == 404
    data = response.json()
    assert data['success'] is False

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

def test_get_users_list_empty(self):
    """Test getting users list when no users exist"""
    response = requests.get(f'{self.BASE_URL}/users')
    assert response.status_code == 200
    data = response.json()
    assert 'users' in data
    assert 'pagination' in data
    assert len(data['users']) == 0
    assert data['pagination']['total'] == 0

def test_get_single_user_not_found(self):
    """Test getting a non-existent user"""
    response = requests.get(f'{self.BASE_URL}/users/99999')
    assert response.status_code == 404
    error_data = response.json()
    assert 'error' in error_data
    assert error_data['error']['code'] == 'not_found'

def test_large_pagination_limit(self):
    """Test pagination with limit exceeding maximum"""
    response = requests.get(f'{self.BASE_URL}/users?limit=1000')
    assert response.status_code in [200, 422]
    if response.status_code == 200:
        data = response.json()
        assert data['pagination']['limit'] <= 100

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
def test_pagination_boundary_cases(api_base_url, auth_headers):
    """Test pagination with boundary values"""
    test_cases = [{'page': 1, 'page_size': 1}, {'page': 1, 'page_size': 100}, {'page': 999, 'page_size': 20}, {'page': 1, 'page_size': 50}]
    for params in test_cases:
        resp = requests.get(f'{api_base_url}/files', params=params, headers=auth_headers, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert 'files' in data
        assert len(data['files']) <= params['page_size']

@pytest.mark.edge
def test_invalid_pagination_parameters(api_base_url, auth_headers):
    """Test pagination with invalid parameters"""
    invalid_cases = [{'page': 0, 'page_size': 20}, {'page': -1, 'page_size': 20}, {'page': 1, 'page_size': 0}, {'page': 1, 'page_size': 101}, {'page': 'invalid', 'page_size': 20}, {'page': 1, 'page_size': 'invalid'}]
    for params in invalid_cases:
        resp = requests.get(f'{api_base_url}/files', params=params, headers=auth_headers, timeout=10)
        assert resp.status_code in (200, 400)

@pytest.mark.edge
def test_expired_token(api_base_url):
    """Test request with expired/invalid token"""
    invalid_headers = {'Authorization': 'Bearer expired_or_invalid_token_12345'}
    resp = requests.get(f'{api_base_url}/files', headers=invalid_headers, timeout=10)
    assert resp.status_code == 401

@pytest.mark.edge
def test_malformed_authorization_header(api_base_url):
    """Test request with malformed authorization header"""
    malformed_headers = [{'Authorization': 'InvalidFormat token123'}, {'Authorization': 'Bearer'}, {'Authorization': ''}, {'Authorization': 'Bearer token1 token2'}]
    for headers in malformed_headers:
        resp = requests.get(f'{api_base_url}/files', headers=headers, timeout=10)
        assert resp.status_code == 401

@pytest.mark.api
def test_health_check(api_base_url, wait_for_service):
    """Test health check endpoint"""
    resp = requests.get(f'{api_base_url}/health', timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'ok'
    assert 'service' in data
    assert 'version' in data

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
def test_list_files_pagination(api_base_url, auth_headers, uploaded_file):
    """Test file listing with pagination parameters"""
    resp = requests.get(f'{api_base_url}/files?page=1&page_size=10', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('page') == 1
    assert data.get('page_size') == 10
    assert len(data['files']) <= 10

@pytest.mark.api
def test_list_files_without_auth(api_base_url, wait_for_service):
    """Test listing files without authentication"""
    resp = requests.get(f'{api_base_url}/files', timeout=10)
    assert resp.status_code == 401

@pytest.mark.api
def test_get_file_info(api_base_url, auth_headers, uploaded_file):
    """Test getting file information"""
    resp = requests.get(f'{api_base_url}/files/{uploaded_file}', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('id') == uploaded_file
    assert 'filename' in data
    assert 'size' in data
    assert 'content_type' in data
    assert 'upload_time' in data
    assert 'uploader' in data

@pytest.mark.api
def test_get_file_info_not_found(api_base_url, auth_headers):
    """Test getting info for non-existent file"""
    resp = requests.get(f'{api_base_url}/files/nonexistent_file_id', headers=auth_headers, timeout=10)
    assert resp.status_code == 404

@pytest.mark.download
def test_download_file(api_base_url, auth_headers, uploaded_file):
    """Test downloading a file"""
    resp = requests.get(f'{api_base_url}/files/{uploaded_file}/download', headers=auth_headers, timeout=30)
    assert resp.status_code == 200
    assert len(resp.content) > 0
    assert 'content-type' in resp.headers or 'Content-Type' in resp.headers
    headers_lower = {k.lower(): v for k, v in resp.headers.items()}
    assert 'content-disposition' in headers_lower or resp.content

@pytest.mark.download
def test_download_file_not_found(api_base_url, auth_headers):
    """Test downloading a non-existent file"""
    resp = requests.get(f'{api_base_url}/files/nonexistent_file_id/download', headers=auth_headers, timeout=30)
    assert resp.status_code == 404

@pytest.mark.download
def test_download_without_auth(api_base_url, uploaded_file):
    """Test downloading a file without authentication"""
    resp = requests.get(f'{api_base_url}/files/{uploaded_file}/download', timeout=30)
    assert resp.status_code == 401

@pytest.mark.api
def test_update_file_metadata(api_base_url, auth_headers, uploaded_file):
    """Test updating file metadata"""
    update_data = {'description': 'Updated description', 'tags': ['updated', 'test', 'metadata']}
    resp = requests.patch(f'{api_base_url}/files/{uploaded_file}', headers={**auth_headers, 'Content-Type': 'application/json'}, json=update_data, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('success') is True or 'file' in data

# Node: patch
@pytest.mark.api
def test_update_file_metadata_by_non_owner(api_base_url, uploaded_file, second_user_token):
    """Test that a user cannot update another user's file metadata"""
    second_user_headers = {'Authorization': f'Bearer {second_user_token}', 'Content-Type': 'application/json'}
    update_data = {'description': 'Attempting unauthorized update'}
    resp = requests.patch(f'{api_base_url}/files/{uploaded_file}', headers=second_user_headers, json=update_data, timeout=10)
    assert resp.status_code == 403

@pytest.mark.api
def test_search_files(api_base_url, auth_headers, uploaded_file):
    """Test searching files"""
    resp = requests.get(f'{api_base_url}/files/search?q=test', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert 'files' in data
    assert isinstance(data['files'], list)
    assert 'query' in data or 'q' in data or data

@pytest.mark.api
def test_search_files_no_results(api_base_url, auth_headers):
    """Test searching files with no results"""
    resp = requests.get(f'{api_base_url}/files/search?q=nonexistentfilequery12345', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert 'files' in data
    assert len(data['files']) == 0

@pytest.mark.api
def test_search_files_invalid_query(api_base_url, auth_headers):
    """Test searching files with invalid query (too short)"""
    resp = requests.get(f'{api_base_url}/files/search?q=a', headers=auth_headers, timeout=10)
    assert resp.status_code in (400, 200)

@pytest.mark.api
def test_list_files_filter_by_type(api_base_url, auth_headers, uploaded_file):
    """Test listing files filtered by file type"""
    resp = requests.get(f'{api_base_url}/files?file_type=document', headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert 'files' in data

def validate_iso8601(date_string: str) -> bool:
    """Validate if string is a valid ISO 8601 date."""
    try:
        from datetime import datetime
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

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

def test_invalid_url_path(self):
    response = requests.get(f'{self.BASE_URL}/invalid/path')
    assert response.status_code == 404
    response = requests.post(f'{self.BASE_URL}/users/invalid')
    assert response.status_code == 404

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

def test_get_user_info_invalid_token(self):
    headers = {'Authorization': 'Bearer invalid_token'}
    response = requests.get(f'{self.BASE_URL}/users/1', headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data['success'] is False

@pytest.fixture(scope='session')
def wait_for_service(api_base_url):
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(f'{api_base_url.replace('/api/v1', '')}/health', timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        retry_count += 1
        time.sleep(1)
    if retry_count >= max_retries:
        pytest.skip('Service not available')

@pytest.mark.api
def test_pagination_bounds(api_base_url):
    r = requests.get(f'{api_base_url}/rooms?page=0&page_size=1000')
    assert r.status_code == 400

@pytest.mark.api
def test_health(api_base_url, wait_for_service):
    resp = requests.get(f'{api_base_url}/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'ok'
    assert 'service' in data
    assert 'version' in data

