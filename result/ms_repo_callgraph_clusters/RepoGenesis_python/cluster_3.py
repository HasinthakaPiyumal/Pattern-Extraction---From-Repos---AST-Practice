# Cluster 3

@pytest.mark.timeout(30)
def test_list_initial_users():
    r = requests.get(url('/users/'), timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

# Node: url
# Node: timeout
@pytest.mark.timeout(30)
def test_crud_flow_create_get_update_delete():
    c = requests.post(url('/users/'), json=create_user_payload(), timeout=10)
    assert c.status_code in (200, 201)
    created = c.json()
    assert set(['id', 'name', 'email', 'password']).issubset(created.keys())
    user_id = created['id']
    g = requests.get(url(f'/users/{user_id}'), timeout=10)
    assert g.status_code == 200
    got = g.json()
    assert got['id'] == user_id and got['email'] == 'alice@example.com'
    u = requests.put(url(f'/users/{user_id}'), json={'name': 'Alice-2', 'email': 'alice2@example.com'}, timeout=10)
    assert u.status_code == 200
    assert u.json().get('message') == 'User updated successfully'
    d = requests.delete(url(f'/users/{user_id}'), timeout=10)
    assert d.status_code == 200
    assert d.json().get('message') == 'User deleted successfully'
    g2 = requests.get(url(f'/users/{user_id}'), timeout=10)
    assert g2.status_code == 404
    assert g2.json().get('detail') == 'User not found'

# Node: create_user_payload
# Node: issubset
# Node: keys
# Node: parametrize
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

@pytest.mark.parametrize('invalid_method', ['POST', 'PUT', 'DELETE'])
def test_health_endpoint_invalid_methods(self, invalid_method):
    response = requests.request(invalid_method, f'{self.BASE_URL}/health')
    assert response.status_code in [200, 405]

# Node: request
@pytest.mark.timeout(30)
def test_index_serves_form():
    r = requests.get(url('/'), timeout=10)
    assert_html_page(r)
    assert 'rock-paper-scissors app' in r.text.lower()
    assert '<form action="/results" method="POST"' in r.text or '<form action="/results" method="post"' in r.text
    assert 'name="choice"' in r.text
    for opt in ('rock', 'paper', 'scissors'):
        assert f'value="{opt}"' in r.text

# Node: assert_html_page
@pytest.mark.timeout(30)
@pytest.mark.parametrize('choice', ['rock', 'paper', 'scissors'])
def test_results_get_with_valid_choice(choice):
    r = requests.get(url(f'/results?choice={choice}'), timeout=10)
    assert_html_page(r)
    assert f'You chose: {choice}' in r.text
    assert re.search('The computer chose: (rock|paper|scissors)', r.text) is not None
    assert 'Results:' in r.text

@pytest.mark.timeout(30)
def test_results_get_with_invalid_choice_defaults_to_rock():
    r = requests.get(url('/results?choice=invalid'), timeout=10)
    assert_html_page(r)
    assert 'You chose: rock' in r.text

@pytest.mark.timeout(30)
@pytest.mark.parametrize('choice', ['rock', 'paper', 'scissors'])
def test_results_post_with_valid_choice(choice):
    r = requests.post(url('/results'), data={'choice': choice}, timeout=10)
    assert_html_page(r)
    assert f'You chose: {choice}' in r.text
    assert re.search('The computer chose: (rock|paper|scissors)', r.text) is not None
    assert 'Results:' in r.text

@pytest.mark.timeout(30)
def test_results_post_without_choice_defaults_to_rock():
    r = requests.post(url('/results'), data={}, timeout=10)
    assert_html_page(r)
    assert 'You chose: rock' in r.text

def create_person(payload: Dict[str, str]):
    return requests.post(url('/people'), json=payload, timeout=10)

def get_person(person_id: str):
    return requests.get(url(f'/people/{person_id}'), timeout=10)

def delete_person(person_id: str, etag: str):
    headers = {'If-Match': etag}
    return requests.delete(url(f'/people/{person_id}'), headers=headers, timeout=10)

@pytest.mark.timeout(30)
def test_people_collection_get_blackbox():
    r = requests.get(url('/people'), timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data.get('_items'), list)

@pytest.mark.timeout(60)
def test_people_crud_with_etag_blackbox():
    payload = {'firstname': 'Ada', 'lastname': 'Lovelace', 'role': 'admin'}
    created = create_person(payload)
    assert created.status_code in (201, 200), created.text
    body = created.json()
    person_id = body.get('_id') or body.get('id')
    assert person_id is not None
    etag = created.headers.get('ETag') or body.get('_etag')
    assert etag, f'missing ETag header/body: headers={created.headers} body={body}'
    got = get_person(str(person_id))
    assert got.status_code == 200, got.text
    b2 = got.json()
    assert (b2.get('_id') or b2.get('id')) == person_id
    etag2 = got.headers.get('ETag') or b2.get('_etag')
    assert etag2
    upd_missing = requests.put(url(f'/people/{person_id}'), json={'role': 'user'}, timeout=10)
    assert upd_missing.status_code in (428, 400, 412)
    upd = update_person(str(person_id), {'role': 'user'}, etag2)
    assert upd.status_code == 200, upd.text
    b3 = upd.json()
    assert b3.get('role') == 'user'
    etag3 = upd.headers.get('ETag') or b3.get('_etag')
    assert etag3 and etag3 != etag2
    del_missing = requests.delete(url(f'/people/{person_id}'), timeout=10)
    assert del_missing.status_code in (428, 400, 412)
    dele = delete_person(str(person_id), etag3)
    assert dele.status_code in (204, 200)
    after = get_person(str(person_id))
    assert after.status_code in (404, 410)

# Node: create_person
# Node: get_person
# Node: update_person
# Node: delete_person
def register_user(payload: Dict[str, str]):
    return requests.post(url('/api/v1/auth/register/'), json=payload, timeout=10)

def obtain_token(username: str, password: str):
    return requests.post(url('/api/v1/auth/token/'), json={'username': username, 'password': password}, timeout=10)

def auth_headers(username: str, password: str) -> Dict[str, str]:
    tok = obtain_token(username, password)
    assert tok.status_code == 200, tok.text
    access = tok.json()['access']
    return {'Authorization': f'Bearer {access}'}

# Node: obtain_token
@pytest.mark.timeout(30)
def test_register_and_obtain_token_blackbox():
    payload = {'username': 'alice_bb', 'password': 'StrongPassw0rd!', 'password2': 'StrongPassw0rd!', 'email': 'alice_bb@example.com', 'first_name': 'Alice', 'last_name': 'Tester'}
    r = register_user(payload)
    assert r.status_code in (201, 400), r.text
    if r.status_code == 400:
        pass
    t = obtain_token(payload['username'], payload['password'])
    assert t.status_code == 200, t.text
    body = t.json()
    assert body.get('access') and body.get('refresh')

# Node: register_user
@pytest.mark.timeout(60)
def test_movies_crud_flow_blackbox():
    username = 'bob_bb'
    password = 'StrongPassw0rd!'
    register_user({'username': username, 'password': password, 'password2': password, 'email': f'{username}@example.com', 'first_name': 'Bob', 'last_name': 'Tester'})
    headers = auth_headers(username, password)
    anon = requests.get(url('/api/v1/movies/'), timeout=10)
    assert anon.status_code in (401, 403)
    lst = requests.get(url('/api/v1/movies/'), headers=headers, timeout=10)
    assert lst.status_code == 200, lst.text
    data = lst.json()
    assert {'count', 'results'}.issubset(data.keys())
    create_payload = {'title': 'Inception', 'genre': 'Sci-Fi', 'year': 2010}
    created = requests.post(url('/api/v1/movies/'), json=create_payload, headers=headers, timeout=10)
    assert created.status_code in (201, 200), created.text
    movie = created.json()
    movie_id = movie['id']
    assert movie['title'] == 'Inception'
    got = requests.get(url(f'/api/v1/movies/{movie_id}/'), headers=headers, timeout=10)
    assert got.status_code == 200, got.text
    assert got.json()['id'] == movie_id
    upd_payload = {'title': 'Inception 2', 'genre': 'Sci-Fi', 'year': 2012}
    upd = requests.put(url(f'/api/v1/movies/{movie_id}/'), json=upd_payload, headers=headers, timeout=10)
    assert upd.status_code == 200, upd.text
    assert upd.json()['title'] == 'Inception 2'
    flt = requests.get(url('/api/v1/movies/?title=incep'), headers=headers, timeout=10)
    assert flt.status_code == 200, flt.text
    assert flt.json()['count'] >= 1
    dele = requests.delete(url(f'/api/v1/movies/{movie_id}/'), headers=headers, timeout=10)
    assert dele.status_code in (204, 200), dele.text
    lst2 = requests.get(url('/api/v1/movies/'), headers=headers, timeout=10)
    assert lst2.status_code == 200

# Node: auth_headers
def test_languages_english_present():
    """Test that English is always present in supported languages"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    languages = data['languages']
    has_english = any((code.lower() in ['en', 'english'] for code in languages.keys()))
    assert has_english, 'English should be in supported languages'
    print(f'✓ Test passed: English is present in supported languages')

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

def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling."""
    try:
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.RequestException as e:
        pytest.fail(f'Request failed: {e}')

