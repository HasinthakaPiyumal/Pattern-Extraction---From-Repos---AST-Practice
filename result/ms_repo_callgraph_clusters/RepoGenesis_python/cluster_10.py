# Cluster 10

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

