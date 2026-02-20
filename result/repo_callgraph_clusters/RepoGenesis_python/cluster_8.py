# Cluster 8

# Node: copy
# Node: make_request
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

