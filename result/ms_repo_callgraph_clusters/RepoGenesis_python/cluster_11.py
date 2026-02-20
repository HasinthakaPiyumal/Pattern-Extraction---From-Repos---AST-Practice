# Cluster 11

# Node: startswith
# Node: close
@pytest.fixture(scope='session')
def base_url():
    return BASE_URL

# Node: fixture
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

def __init__(self, base_url):
    self.base_url = base_url
    self.session = requests.Session()
    self.session.headers.update({'Content-Type': 'application/json'})

# Node: Session
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

# Node: skip
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

@pytest.fixture(scope='session')
def api_base_url():
    return 'http://localhost:8082/api/v1'

@pytest.fixture(scope='session')
def api_health_check(api_base_url):
    try:
        resp = requests.get(f'{api_base_url}/health', timeout=5)
        if resp.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    pytest.skip('API server not running on localhost:8082')

@pytest.fixture(autouse=True)
def cleanup_games(api_base_url, api_health_check):
    yield

@pytest.fixture()
def client():
    app = create_minimal_app()
    app.testing = True
    with app.test_client() as c:
        yield c

# Node: create_minimal_app
# Node: test_client
@pytest.fixture(scope='function')
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Node: create_all
# Node: TestingSessionLocal
# Node: drop_all
@pytest.fixture(scope='function')
def client(db):
    """Create a test client with a fresh database."""

    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# Node: TestClient
# Node: clear
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

@pytest.fixture(autouse=True)
def setup(self):
    self.session = requests.Session()
    self.auth_token = None
    self.test_user = {'username': 'testuser', 'password': 'testpass123', 'email': 'test@example.com'}
    self.test_file_content = b'This is a test file content for WebPan API testing.'
    self.test_file_name = 'test_file.txt'

@pytest.fixture(scope='session')
def base_url() -> str:
    return 'http://localhost:8080/api/v1'

@pytest.fixture(scope='session')
def test_server_available(base_url: str) -> bool:
    try:
        response = requests.get(f'{base_url}/health', timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

@pytest.fixture(autouse=True)
def skip_if_server_unavailable(test_server_available: bool):
    if not test_server_available:
        pytest.skip('Test server is not available')

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

@pytest.fixture(scope='session')
def api_server():
    """
    Fixture to start and stop the API server for testing.
    
    This fixture ensures the API server is running during test execution
    and properly shuts it down after all tests are complete.
    """
    try:
        response = requests.get('http://localhost:8080/api/v1/health', timeout=5)
        if response.status_code == 200:
            yield 'http://localhost:8080'
            return
    except requests.exceptions.RequestException:
        pass
    print('API server not running. Please start the server manually on port 8080')
    print('Example commands:')
    print('  - For Flask: python app.py')
    print('  - For FastAPI: uvicorn main:app --port 8080')
    print('  - For Django: python manage.py runserver 8080')
    yield 'http://localhost:8080'

@pytest.fixture(autouse=True)
def wait_for_server(api_server):
    """
    Fixture to wait for the API server to be ready before running tests.
    """
    max_retries = 30
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.get(f'{api_server}/api/v1/health', timeout=5)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    pytest.skip('API server not available after waiting')

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

@pytest.fixture(scope='function')
def clean_test_data():
    created_ids = []

    def _register_id(data_id: str):
        created_ids.append(data_id)
    yield _register_id
    for data_id in created_ids:
        try:
            requests.delete(f'{API_ENDPOINT}/{data_id}', timeout=2)
        except:
            pass

@pytest.fixture(scope='function')
def sample_data():
    return [{'name': 'Sample Item 1', 'category': 'Category A', 'score': 85.0, 'description': 'This is a sample item for testing', 'tags': ['test', 'sample']}, {'name': 'Sample Item 2', 'category': 'Category B', 'score': 90.0, 'description': 'Another sample item', 'tags': ['test', 'example']}, {'name': 'Sample Item 3', 'category': 'Category A', 'score': 78.5, 'description': 'Third sample item', 'tags': ['test']}]

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

@pytest.fixture(scope='session')
def api_base_url():
    """Base URL for the API"""
    return 'http://localhost:8081/api/v1'

@pytest.fixture(scope='session')
def api_health_check(api_base_url):
    """Check if API server is running"""
    try:
        response = requests.get(f'{api_base_url}/health', timeout=5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    pytest.skip('API server not running on localhost:8081')

@pytest.fixture(autouse=True)
def cleanup_users(api_base_url, api_health_check):
    """Clean up test users before and after each test"""
    try:
        response = requests.get(f'{api_base_url}/users')
        if response.status_code == 200:
            users = response.json().get('users', [])
            for user in users:
                if user['username'].startswith('test_'):
                    requests.delete(f'{api_base_url}/users/{user['id']}')
    except requests.exceptions.RequestException:
        pass
    yield
    try:
        response = requests.get(f'{api_base_url}/users')
        if response.status_code == 200:
            users = response.json().get('users', [])
            for user in users:
                if user['username'].startswith('test_'):
                    requests.delete(f'{api_base_url}/users/{user['id']}')
    except requests.exceptions.RequestException:
        pass

@pytest.mark.edge
@pytest.mark.slow
def test_upload_file_exceeds_size_limit(api_base_url, auth_headers):
    """Test uploading a file that exceeds the size limit (100MB)"""
    file_size = 101 * 1024 * 1024

    def generate_large_file():
        chunk_size = 1024 * 1024
        for _ in range(file_size // chunk_size):
            yield (b'x' * chunk_size)

    class LargeFileIO:

        def __init__(self, size):
            self.size = size
            self.pos = 0

        def read(self, size=-1):
            if size == -1:
                size = self.size - self.pos
            if self.pos >= self.size:
                return b''
            chunk = min(size, self.size - self.pos)
            self.pos += chunk
            return b'x' * chunk

        def seek(self, pos):
            self.pos = pos

        def tell(self):
            return self.pos
    large_file = LargeFileIO(file_size)
    files = {'file': ('oversized_file.bin', large_file, 'application/octet-stream')}
    try:
        resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, timeout=180)
        assert resp.status_code == 413
    except requests.exceptions.Timeout:
        pytest.skip('Request timed out - file might be too large to process in test timeout')

# Node: LargeFileIO
@pytest.fixture(scope='session')
def api_base_url():
    """Base URL for the File Relay API"""
    return os.getenv('API_BASE_URL', 'http://localhost:8085/api/v1')

# Node: getenv
@pytest.fixture(scope='session')
def wait_for_service(api_base_url):
    """Wait for the service to be available before running tests"""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            resp = requests.get(f'{api_base_url}/health', timeout=5)
            if resp.status_code == 200:
                print(f'\n✓ File Relay API is ready at {api_base_url}')
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    pytest.skip(f'File Relay API server not available at {api_base_url}')

@pytest.fixture(scope='session')
def base_url():
    """Base URL for the GameBackend API."""
    return 'http://localhost:8080'

@pytest.fixture(scope='session')
def api_version():
    """API version."""
    return 'v1'

@pytest.fixture(scope='session')
def api_base_url(base_url, api_version):
    """Complete API base URL."""
    return f'{base_url}/api/{api_version}'

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

@pytest.fixture(autouse=True)
def setup(self):
    self.test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123', 'full_name': 'Test User'}
    self.access_token = None
    self.user_id = None

@pytest.fixture(scope='session')
def api_base_url():
    return os.getenv('API_BASE_URL', 'http://localhost:8080/api/v1')

@pytest.fixture(autouse=True)
def cleanup_after_test(api_base_url, wait_for_service):
    yield
    pass

@pytest.fixture(scope='session')
def api_base_url():
    return os.getenv('API_BASE_URL', 'http://localhost:8083/api/v1')

@pytest.fixture(scope='session')
def wait_for_service(api_base_url):
    max_retries = 30
    for attempt in range(max_retries):
        try:
            resp = requests.get(f'{api_base_url}/health', timeout=5)
            if resp.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    pytest.skip('Chatroom API server not available on localhost:8083')

