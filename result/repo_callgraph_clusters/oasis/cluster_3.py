# Cluster 3

class Database:

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def get_score_comment_id(self, comment_id):
        cursor = self.conn.cursor()
        '\n        Query the score of a specific comment by comment ID (likes minus\n        dislikes).\n        '
        query = '\n        SELECT (num_likes - num_dislikes) AS score\n        FROM comment\n        WHERE comment_id = ?\n        '
        cursor.execute(query, (comment_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

def __init__(self, db_path):
    self.conn = sqlite3.connect(db_path)

def get_score_comment_id(self, comment_id):
    cursor = self.conn.cursor()
    '\n        Query the score of a specific comment by comment ID (likes minus\n        dislikes).\n        '
    query = '\n        SELECT (num_likes - num_dislikes) AS score\n        FROM comment\n        WHERE comment_id = ?\n        '
    cursor.execute(query, (comment_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

def connect_to_sqlite(db_path):
    return sqlite3.connect(db_path)

def main(sqlite_db_path):
    neo4j_driver = connect_to_neo4j(neo4j_config)
    sqlite_conn = connect_to_sqlite(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()
    with neo4j_driver.session() as session:
        sqlite_cursor.execute('SELECT user_id, user_name, name, bio, created_at FROM user ORDER BY created_at')
        for row in sqlite_cursor:
            user_id, user_name, name, bio, created_at = row
            info_dict = {'user_name': user_name, 'name': name, 'bio': bio}
            print('info_dict:\n', info_dict)
            session.execute_write(create_user_node, user_id, info_dict, created_at)
        sqlite_cursor.execute('SELECT follower_id, followee_id, created_at FROM follow ORDER BY created_at')
        for row in sqlite_cursor:
            follower_id, followee_id, created_at = row
            print(f'follower_id:{follower_id}, followee_id:{followee_id}, created_at:{created_at}')
            session.execute_write(create_follow_relationship, follower_id, followee_id, created_at)
    sqlite_conn.close()
    neo4j_driver.close()

def connect_to_sqlite(db_path):
    return sqlite3.connect(db_path)

def main(sqlite_db_path):
    neo4j_driver = connect_to_neo4j(neo4j_config)
    sqlite_conn = connect_to_sqlite(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute('SELECT user_id, created_at, action, info FROM trace ORDER BY created_at')
    with neo4j_driver.session() as session:
        for row in sqlite_cursor:
            user_id, created_at, action, info = row
            info_dict = json.loads(info)
            if action == 'sign_up':
                session.execute_write(create_user_node, user_id, info_dict, created_at)
            elif action == 'follow':
                follow_id = int(info_dict['follow_id'])
                timestamp = int(info_dict['time_stamp'])
                session.execute_write(create_follow_relationship, user_id, follow_id, created_at, timestamp)
    sqlite_conn.close()
    neo4j_driver.close()

def test_user_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user (agent_id, user_name, name, bio, created_at, num_followings, num_followers) VALUES (?, ?, ?, ?, ?, ?, ?)', (2, 'testuser', 'Test User', 'A test user', '2024-04-21 22:02:42', 0, 0))
    conn.commit()
    cursor.execute("SELECT * FROM user WHERE user_name = 'testuser'")
    user = cursor.fetchone()
    assert user is not None
    assert user[1] == 2
    assert user[2] == 'testuser'
    assert user[3] == 'Test User'
    assert user[4] == 'A test user'
    assert user[5] == '2024-04-21 22:02:42'
    assert user[6] == 0
    assert user[7] == 0
    cursor.execute('UPDATE user SET name = ? WHERE user_name = ?', ('Updated User', 'testuser'))
    conn.commit()
    cursor.execute("SELECT * FROM user WHERE user_name = 'testuser'")
    user = cursor.fetchone()
    assert user[3] == 'Updated User'
    cursor.execute('INSERT INTO user (agent_id, user_name, name, bio, created_at, num_followings, num_followers) VALUES (?, ?, ?, ?, ?, ?, ?)', (1, 'testuser_2', 'Test User_2', 'Another user', '2024-05-21 22:02:42', 0, 0))
    conn.commit()
    expected_result = [{'user_id': 1, 'agent_id': 2, 'user_name': 'testuser', 'name': 'Updated User', 'bio': 'A test user', 'created_at': '2024-04-21 22:02:42', 'num_followings': 0, 'num_followers': 0}, {'user_id': 2, 'agent_id': 1, 'user_name': 'testuser_2', 'name': 'Test User_2', 'bio': 'Another user', 'created_at': '2024-05-21 22:02:42', 'num_followings': 0, 'num_followers': 0}]
    actual_result = fetch_table_from_db(cursor, 'user')
    assert actual_result == expected_result, 'The fetched data does not match.'
    cursor.execute('INSERT INTO user (agent_id, user_name, name, bio, created_at, num_followings, num_followers) VALUES (?, ?, ?, ?, ?, ?, ?)', (3, 'testuser_3', 'Test User_3', 'Third user', '2024-05-21 22:02:42', 0, 0))
    conn.commit()
    cursor.execute("DELETE FROM user WHERE user_name = 'testuser_3'")
    conn.commit()
    cursor.execute("SELECT * FROM user WHERE user_name = 'testuser_3'")
    assert cursor.fetchone() is None

def test_post_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO post (user_id, content, created_at, num_likes, num_dislikes, num_shares, num_reports) VALUES (?, ?, ?, ?, ?, ?, ?)', (1, 'This is a test post', '2024-04-21 22:02:42', 0, 1, 2, 0))
    conn.commit()
    cursor.execute("SELECT * FROM post WHERE content = 'This is a test post'")
    post = cursor.fetchone()
    assert post is not None
    assert post[1] == 1
    assert post[3] == 'This is a test post'
    assert post[5] == '2024-04-21 22:02:42'
    assert post[6] == 0
    assert post[7] == 1
    assert post[8] == 2
    assert post[9] == 0
    cursor.execute('UPDATE post SET content = ? WHERE content = ?', ('Updated post', 'This is a test post'))
    conn.commit()
    expected_result = [{'post_id': 1, 'user_id': 1, 'original_post_id': None, 'content': 'Updated post', 'quote_content': None, 'created_at': '2024-04-21 22:02:42', 'num_likes': 0, 'num_dislikes': 1, 'num_shares': 2, 'num_reports': 0}]
    actual_result = fetch_table_from_db(cursor, 'post')
    assert actual_result == expected_result, 'The fetched data does not match.'
    cursor.execute("SELECT * FROM post WHERE content = 'Updated post'")
    post = cursor.fetchone()
    assert post[3] == 'Updated post'
    cursor.execute("DELETE FROM post WHERE content = 'Updated post'")
    conn.commit()
    cursor.execute("SELECT * FROM post WHERE content = 'Updated post'")
    assert cursor.fetchone() is None

def test_follow_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO follow (follower_id, followee_id, created_at) VALUES (?, ?, ?)', (1, 2, '2024-04-21 22:02:42'))
    conn.commit()
    cursor.execute('SELECT * FROM follow WHERE follower_id = 1 AND followee_id = 2')
    follow = cursor.fetchone()
    assert follow is not None
    assert follow[1] == 1
    assert follow[2] == 2
    assert follow[3] == '2024-04-21 22:02:42'
    cursor.execute('DELETE FROM follow WHERE follower_id = 1 AND followee_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM follow WHERE follower_id = 1 AND followee_id = 2')
    assert cursor.fetchone() is None

def test_mute_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO mute (muter_id, mutee_id, created_at) VALUES (?, ?, ?)', (1, 2, '2024-04-21 22:02:42'))
    conn.commit()
    cursor.execute('SELECT * FROM mute WHERE muter_id = 1 AND mutee_id = 2')
    mute = cursor.fetchone()
    assert mute is not None
    assert mute[1] == 1
    assert mute[2] == 2
    assert mute[3] == '2024-04-21 22:02:42'
    cursor.execute('DELETE FROM mute WHERE muter_id = 1 AND mutee_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM mute WHERE muter_id = 1 AND mutee_id = 2')
    assert cursor.fetchone() is None

def test_like_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO like (user_id, post_id, created_at) VALUES (?, ?, ?)', (1, 2, '2024-04-21 22:02:42'))
    conn.commit()
    cursor.execute('SELECT * FROM like WHERE user_id = 1 AND post_id = 2')
    like = cursor.fetchone()
    assert like is not None
    assert like[1] == 1
    assert like[2] == 2
    assert like[3] == '2024-04-21 22:02:42'
    cursor.execute('DELETE FROM like WHERE user_id = 1 AND post_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM like WHERE user_id = 1 AND post_id = 2')
    assert cursor.fetchone() is None

def test_dislike_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO dislike (user_id, post_id, created_at) VALUES (?, ?, ?)', (1, 2, '2024-04-21 22:02:42'))
    conn.commit()
    cursor.execute('SELECT * FROM dislike WHERE user_id = 1 AND post_id = 2')
    dislike = cursor.fetchone()
    assert dislike is not None
    assert dislike[1] == 1
    assert dislike[2] == 2
    assert dislike[3] == '2024-04-21 22:02:42'
    cursor.execute('DELETE FROM dislike WHERE user_id = 1 AND post_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM like WHERE user_id = 1 AND post_id = 2')
    assert cursor.fetchone() is None

def test_trace_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    cursor.execute('INSERT INTO trace (user_id, created_at, action, info) VALUES (?, ?, ?, ?)', (1, created_at, 'test_action', 'test_info'))
    conn.commit()
    cursor.execute('SELECT * FROM trace WHERE user_id = 1 AND created_at = ?', (created_at,))
    trace = cursor.fetchone()
    assert trace is not None
    assert trace[0] == 1
    assert trace[1] == created_at
    assert trace[2] == 'test_action'
    assert trace[3] == 'test_info'
    expected_result = [{'user_id': 1, 'created_at': created_at, 'action': 'test_action', 'info': 'test_info'}]
    actual_result = fetch_table_from_db(cursor, 'trace')
    assert actual_result == expected_result
    cursor.execute('DELETE FROM trace WHERE user_id = 1 AND created_at = ?', (created_at,))
    conn.commit()
    cursor.execute('SELECT * FROM trace WHERE user_id = 1 AND created_at = ?', (created_at,))
    assert cursor.fetchone() is None

def test_rec_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO rec (user_id, post_id) VALUES (?, ?)', (2, 2))
    cursor.execute('INSERT INTO rec (user_id, post_id) VALUES (?, ?)', (2, 3))
    cursor.execute('INSERT INTO rec (user_id, post_id) VALUES (?, ?)', (1, 3))
    conn.commit()
    cursor.execute('SELECT * FROM rec WHERE user_id = ? AND post_id = ?', (2, 2))
    record = cursor.fetchone()
    assert record is not None
    assert record[0] == 2
    assert record[1] == 2
    cursor.execute('SELECT * FROM rec WHERE user_id = ? AND post_id = ?', (2, 3))
    record = cursor.fetchone()
    assert record is not None
    assert record[0] == 2
    assert record[1] == 3
    assert fetch_rec_table_as_matrix(cursor) == [[3], [2, 3]]
    cursor.execute('DELETE FROM rec WHERE user_id = 2 AND post_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM rec WHERE user_id = 2 AND post_id = 2')
    assert cursor.fetchone() is None

def test_comment_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comment (post_id, user_id, content, created_at) VALUES (?, ?, ?, ?)', (1, 2, 'This is a test comment', '2024-04-21 22:05:00'))
    conn.commit()
    cursor.execute("SELECT * FROM comment WHERE content = 'This is a test comment'")
    comment = cursor.fetchone()
    assert comment is not None, 'Comment insertion failed.'
    assert comment[1] == 1, 'Post ID mismatch.'
    assert comment[2] == 2, 'User ID mismatch.'
    assert comment[3] == 'This is a test comment', 'Content mismatch.'
    assert comment[4] == '2024-04-21 22:05:00', 'Created at mismatch.'
    assert comment[5] == 0, 'Likes count mismatch.'
    assert comment[6] == 0, 'Dislikes count mismatch.'
    cursor.execute('UPDATE comment SET content = ? WHERE content = ?', ('Updated comment', 'This is a test comment'))
    conn.commit()
    expected_result = [{'comment_id': 1, 'post_id': 1, 'user_id': 2, 'content': 'Updated comment', 'created_at': '2024-04-21 22:05:00', 'num_likes': 0, 'num_dislikes': 0}]
    actual_result = fetch_table_from_db(cursor, 'comment')
    assert actual_result == expected_result, 'The fetched data does not match.'
    cursor.execute("SELECT * FROM comment WHERE content = 'Updated comment'")
    comment = cursor.fetchone()
    assert comment[3] == 'Updated comment', 'Comment update failed.'
    cursor.execute("DELETE FROM comment WHERE content = 'Updated comment'")
    conn.commit()
    cursor.execute("SELECT * FROM comment WHERE content = 'Updated comment'")
    assert cursor.fetchone() is None, 'Comment deletion failed.'

def test_comment_like_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comment_like (user_id, comment_id, created_at) VALUES (?, ?, ?)', (1, 2, '2024-04-21 22:05:00'))
    conn.commit()
    cursor.execute('SELECT * FROM comment_like WHERE user_id = 1 AND comment_id = 2')
    comment_like = cursor.fetchone()
    assert comment_like is not None, 'Comment like insertion failed.'
    assert comment_like[1] == 1, 'User ID mismatch.'
    assert comment_like[2] == 2, 'Comment ID mismatch.'
    assert comment_like[3] == '2024-04-21 22:05:00', 'Created at mismatch.'
    cursor.execute('DELETE FROM comment_like WHERE user_id = 1 AND comment_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM comment_like WHERE user_id = 1 AND comment_id = 2')
    assert cursor.fetchone() is None, 'Comment like deletion failed.'

def test_comment_dislike_operations():
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comment_dislike (user_id, comment_id, created_at) VALUES (?, ?, ?)', (1, 2, '2024-04-21 22:05:00'))
    conn.commit()
    cursor.execute('SELECT * FROM comment_dislike WHERE user_id = 1 AND comment_id = 2')
    comment_dislike = cursor.fetchone()
    assert comment_dislike is not None, 'Comment dislike insertion failed.'
    assert comment_dislike[1] == 1, 'User ID mismatch.'
    assert comment_dislike[2] == 2, 'Comment ID mismatch.'
    assert comment_dislike[3] == '2024-04-21 22:05:00', 'Created at mismatch.'
    cursor.execute('DELETE FROM comment_dislike WHERE user_id = 1 AND comment_id = 2')
    conn.commit()
    cursor.execute('SELECT * FROM comment_dislike WHERE user_id = 1 AND comment_id = 2')
    assert cursor.fetchone() is None, 'Comment dislike deletion failed.'

def test_multi_signup():
    if os.path.exists(test_db_filepath):
        os.remove(test_db_filepath)
    N = 100
    create_db(test_db_filepath)
    db = sqlite3.connect(test_db_filepath, check_same_thread=False)
    db_cursor = db.cursor()
    user_insert_query = 'INSERT INTO user (agent_id, user_name, name, bio, created_at, num_followings, num_followers) VALUES (?, ?, ?, ?, ?, ?, ?)'
    for i in range(N):
        db_cursor.execute(user_insert_query, (i, i, i, i, datetime.now(), 0, 0))
        db.commit()
    db_cursor.execute('SELECT * FROM user')
    users = db_cursor.fetchall()
    assert len(users) == N

class Neo4jHandler:

    def __init__(self, nei4j_config: Neo4jConfig):
        self.driver = GraphDatabase.driver(nei4j_config.uri, auth=(nei4j_config.username, nei4j_config.password))
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_agent(self, agent_id: int):
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_agent, agent_id)

    def delete_agent(self, agent_id: int):
        with self.driver.session() as session:
            session.write_transaction(self._delete_agent_and_relationships, agent_id)

    def get_number_of_nodes(self) -> int:
        with self.driver.session() as session:
            return session.read_transaction(self._get_number_of_nodes)

    def get_number_of_edges(self) -> int:
        with self.driver.session() as session:
            return session.read_transaction(self._get_number_of_edges)

    def add_edge(self, src_agent_id: int, dst_agent_id: int):
        with self.driver.session() as session:
            session.write_transaction(self._add_and_return_edge, src_agent_id, dst_agent_id)

    def remove_edge(self, src_agent_id: int, dst_agent_id: int):
        with self.driver.session() as session:
            session.write_transaction(self._remove_and_return_edge, src_agent_id, dst_agent_id)

    def get_all_nodes(self) -> list[int]:
        with self.driver.session() as session:
            return session.read_transaction(self._get_all_nodes)

    def get_all_edges(self) -> list[tuple[int, int]]:
        with self.driver.session() as session:
            return session.read_transaction(self._get_all_edges)

    def reset_graph(self):
        with self.driver.session() as session:
            session.write_transaction(self._reset_graph)

    @staticmethod
    def _create_and_return_agent(tx: Any, agent_id: int):
        query = '\n        CREATE (a:Agent {id: $agent_id})\n        RETURN a\n        '
        result = tx.run(query, agent_id=agent_id)
        return result.single()

    @staticmethod
    def _delete_agent_and_relationships(tx: Any, agent_id: int):
        query = '\n        MATCH (a:Agent {id: $agent_id})\n        DETACH DELETE a\n        RETURN count(a) AS deleted\n        '
        result = tx.run(query, agent_id=agent_id)
        return result.single()

    @staticmethod
    def _add_and_return_edge(tx: Any, src_agent_id: int, dst_agent_id: int):
        query = '\n        MATCH (a:Agent {id: $src_agent_id}), (b:Agent {id: $dst_agent_id})\n        CREATE (a)-[r:FOLLOW]->(b)\n        RETURN r\n        '
        result = tx.run(query, src_agent_id=src_agent_id, dst_agent_id=dst_agent_id)
        return result.single()

    @staticmethod
    def _remove_and_return_edge(tx: Any, src_agent_id: int, dst_agent_id: int):
        query = '\n        MATCH (a:Agent {id: $src_agent_id})\n        MATCH (b:Agent {id: $dst_agent_id})\n        MATCH (a)-[r:FOLLOW]->(b)\n        DELETE r\n        RETURN count(r) AS deleted\n        '
        result = tx.run(query, src_agent_id=src_agent_id, dst_agent_id=dst_agent_id)
        return result.single()

    @staticmethod
    def _get_number_of_nodes(tx: Any) -> int:
        query = '\n        MATCH (n)\n        RETURN count(n) AS num_nodes\n        '
        result = tx.run(query)
        return result.single()['num_nodes']

    @staticmethod
    def _get_number_of_edges(tx: Any) -> int:
        query = '\n        MATCH ()-[r]->()\n        RETURN count(r) AS num_edges\n        '
        result = tx.run(query)
        return result.single()['num_edges']

    @staticmethod
    def _get_all_nodes(tx: Any) -> list[int]:
        query = '\n        MATCH (a:Agent)\n        RETURN a.id AS agent_id\n        '
        result = tx.run(query)
        return [record['agent_id'] for record in result]

    @staticmethod
    def _get_all_edges(tx: Any) -> list[tuple[int, int]]:
        query = '\n        MATCH (a:Agent)-[r:FOLLOW]->(b:Agent)\n        RETURN a.id AS src_agent_id, b.id AS dst_agent_id\n        '
        result = tx.run(query)
        return [(record['src_agent_id'], record['dst_agent_id']) for record in result]

    @staticmethod
    def _reset_graph(tx: Any):
        query = '\n        MATCH (n)\n        DETACH DELETE n\n        '
        tx.run(query)

def close(self):
    self.driver.close()

class AgentGraph:
    """AgentGraph class to manage the social graph of agents."""

    def __init__(self, backend: Literal['igraph', 'neo4j']='igraph', neo4j_config: Neo4jConfig | None=None):
        self.backend = backend
        if self.backend == 'igraph':
            self.graph = ig.Graph(directed=True)
        else:
            assert neo4j_config is not None
            assert neo4j_config.is_valid()
            self.graph = Neo4jHandler(neo4j_config)
        self.agent_mappings: dict[int, SocialAgent] = {}

    def reset(self):
        if self.backend == 'igraph':
            self.graph = ig.Graph(directed=True)
        else:
            self.graph.reset_graph()
        self.agent_mappings: dict[int, SocialAgent] = {}

    def add_agent(self, agent: SocialAgent):
        if self.backend == 'igraph':
            self.graph.add_vertex(agent.social_agent_id)
        else:
            self.graph.create_agent(agent.social_agent_id)
        self.agent_mappings[agent.social_agent_id] = agent

    def add_edge(self, agent_id_0: int, agent_id_1: int):
        try:
            self.graph.add_edge(agent_id_0, agent_id_1)
        except Exception:
            pass

    def remove_agent(self, agent: SocialAgent):
        if self.backend == 'igraph':
            self.graph.delete_vertices(agent.social_agent_id)
        else:
            self.graph.delete_agent(agent.social_agent_id)
        del self.agent_mappings[agent.social_agent_id]

    def remove_edge(self, agent_id_0: int, agent_id_1: int):
        if self.backend == 'igraph':
            if self.graph.are_connected(agent_id_0, agent_id_1):
                self.graph.delete_edges([(agent_id_0, agent_id_1)])
        else:
            self.graph.remove_edge(agent_id_0, agent_id_1)

    def get_agent(self, agent_id: int) -> SocialAgent:
        return self.agent_mappings[agent_id]

    def get_agents(self, agent_ids: list[int]=None) -> list[tuple[int, SocialAgent]]:
        if agent_ids:
            return [(agent_id, self.get_agent(agent_id)) for agent_id in agent_ids]
        if self.backend == 'igraph':
            return [(node.index, self.agent_mappings[node.index]) for node in self.graph.vs]
        else:
            return [(agent_id, self.agent_mappings[agent_id]) for agent_id in self.graph.get_all_nodes()]

    def get_edges(self) -> list[tuple[int, int]]:
        if self.backend == 'igraph':
            return [(edge.source, edge.target) for edge in self.graph.es]
        else:
            return self.graph.get_all_edges()

    def get_num_nodes(self) -> int:
        if self.backend == 'igraph':
            return self.graph.vcount()
        else:
            return self.graph.get_number_of_nodes()

    def get_num_edges(self) -> int:
        if self.backend == 'igraph':
            return self.graph.ecount()
        else:
            return self.graph.get_number_of_edges()

    def close(self) -> None:
        if self.backend == 'neo4j':
            self.graph.close()

    def visualize(self, path: str, vertex_size: int=20, edge_arrow_size: float=0.5, with_labels: bool=True, vertex_color: str='#f74f1b', vertex_frame_width: int=2, width: int=1000, height: int=1000):
        if self.backend == 'neo4j':
            raise ValueError('Neo4j backend does not support visualization.')
        layout = self.graph.layout('auto')
        if with_labels:
            labels = [node_id for node_id, _ in self.get_agents()]
        else:
            labels = None
        ig.plot(self.graph, target=path, layout=layout, vertex_label=labels, vertex_size=vertex_size, vertex_color=vertex_color, edge_arrow_size=edge_arrow_size, vertex_frame_width=vertex_frame_width, bbox=(width, height))

def close(self) -> None:
    if self.backend == 'neo4j':
        self.graph.close()

def create_db(db_path: str | None=None):
    """Create the database if it does not exist. A :obj:`twitter.db`
    file will be automatically created  in the :obj:`data` directory.
    """
    schema_dir = get_schema_dir_path()
    if db_path is None:
        db_path = get_db_path()
    print('db_path', db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        user_sql_path = osp.join(schema_dir, USER_SCHEMA_SQL)
        with open(user_sql_path, 'r') as sql_file:
            user_sql_script = sql_file.read()
        cursor.executescript(user_sql_script)
        post_sql_path = osp.join(schema_dir, POST_SCHEMA_SQL)
        with open(post_sql_path, 'r') as sql_file:
            post_sql_script = sql_file.read()
        cursor.executescript(post_sql_script)
        follow_sql_path = osp.join(schema_dir, FOLLOW_SCHEMA_SQL)
        with open(follow_sql_path, 'r') as sql_file:
            follow_sql_script = sql_file.read()
        cursor.executescript(follow_sql_script)
        mute_sql_path = osp.join(schema_dir, MUTE_SCHEMA_SQL)
        with open(mute_sql_path, 'r') as sql_file:
            mute_sql_script = sql_file.read()
        cursor.executescript(mute_sql_script)
        like_sql_path = osp.join(schema_dir, LIKE_SCHEMA_SQL)
        with open(like_sql_path, 'r') as sql_file:
            like_sql_script = sql_file.read()
        cursor.executescript(like_sql_script)
        dislike_sql_path = osp.join(schema_dir, DISLIKE_SCHEMA_SQL)
        with open(dislike_sql_path, 'r') as sql_file:
            dislike_sql_script = sql_file.read()
        cursor.executescript(dislike_sql_script)
        report_sql_path = osp.join(schema_dir, REPORT_SCHEAM_SQL)
        with open(report_sql_path, 'r') as sql_file:
            report_sql_script = sql_file.read()
        cursor.executescript(report_sql_script)
        trace_sql_path = osp.join(schema_dir, TRACE_SCHEMA_SQL)
        with open(trace_sql_path, 'r') as sql_file:
            trace_sql_script = sql_file.read()
        cursor.executescript(trace_sql_script)
        rec_sql_path = osp.join(schema_dir, REC_SCHEMA_SQL)
        with open(rec_sql_path, 'r') as sql_file:
            rec_sql_script = sql_file.read()
        cursor.executescript(rec_sql_script)
        comment_sql_path = osp.join(schema_dir, COMMENT_SCHEMA_SQL)
        with open(comment_sql_path, 'r') as sql_file:
            comment_sql_script = sql_file.read()
        cursor.executescript(comment_sql_script)
        comment_like_sql_path = osp.join(schema_dir, COMMENT_LIKE_SCHEMA_SQL)
        with open(comment_like_sql_path, 'r') as sql_file:
            comment_like_sql_script = sql_file.read()
        cursor.executescript(comment_like_sql_script)
        comment_dislike_sql_path = osp.join(schema_dir, COMMENT_DISLIKE_SCHEMA_SQL)
        with open(comment_dislike_sql_path, 'r') as sql_file:
            comment_dislike_sql_script = sql_file.read()
        cursor.executescript(comment_dislike_sql_script)
        product_sql_path = osp.join(schema_dir, PRODUCT_SCHEMA_SQL)
        with open(product_sql_path, 'r') as sql_file:
            product_sql_script = sql_file.read()
        cursor.executescript(product_sql_script)
        group_sql_path = osp.join(schema_dir, GROUP_SCHEMA_SQL)
        with open(group_sql_path, 'r') as sql_file:
            group_sql_script = sql_file.read()
        cursor.executescript(group_sql_script)
        group_member_sql_path = osp.join(schema_dir, GROUP_MEMBER_SCHEMA_SQL)
        with open(group_member_sql_path, 'r') as sql_file:
            group_member_sql_script = sql_file.read()
        cursor.executescript(group_member_sql_script)
        group_message_sql_path = osp.join(schema_dir, GROUP_MESSAGE_SCHEMA_SQL)
        with open(group_message_sql_path, 'r') as sql_file:
            group_message_sql_script = sql_file.read()
        cursor.executescript(group_message_sql_script)
        conn.commit()
    except sqlite3.Error as e:
        print(f'An error occurred while creating tables: {e}')
    return (conn, cursor)

def print_db_tables_summary():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        if table_name not in TABLE_NAMES:
            continue
        print(f'Table: {table_name}')
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        print('- Columns:', column_names)
        cursor.execute(f'PRAGMA foreign_key_list({table_name})')
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            print('- Foreign Keys:')
            for fk in foreign_keys:
                print(f'    {fk[2]} references {fk[3]}({fk[4]}) on update {fk[5]} on delete {fk[6]}')
        else:
            print('  No foreign keys.')
        cursor.execute(f'SELECT * FROM {table_name} LIMIT 5;')
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        print()
    conn.close()

def fetch_table_from_db(cursor: sqlite3.Cursor, table_name: str) -> List[Dict[str, Any]]:
    cursor.execute(f'SELECT * FROM {table_name}')
    columns = [description[0] for description in cursor.description]
    data_dicts = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return data_dicts

def fetch_rec_table_as_matrix(cursor: sqlite3.Cursor) -> List[List[int]]:
    cursor.execute('SELECT user_id FROM user ORDER BY user_id')
    user_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute('SELECT user_id, post_id FROM rec ORDER BY user_id, post_id')
    rec_rows = cursor.fetchall()
    user_posts = {user_id: [] for user_id in user_ids}
    for user_id, post_id in rec_rows:
        if user_id in user_posts:
            user_posts[user_id].append(post_id)
    matrix = [user_posts[user_id] for user_id in user_ids]
    return matrix

class PlatformUtils:

    def __init__(self, db, db_cursor, start_time, sandbox_clock, show_score, recsys_type, report_threshold=1):
        self.db = db
        self.db_cursor = db_cursor
        self.start_time = start_time
        self.sandbox_clock = sandbox_clock
        self.show_score = show_score
        self.recsys_type = recsys_type
        self.report_threshold = report_threshold

    @staticmethod
    def _not_signup_error_message(agent_id):
        return {'success': False, 'error': f'Agent {agent_id} has not signed up and does not have a user id.'}

    def _execute_db_command(self, command, args=(), commit=False):
        self.db_cursor.execute(command, args)
        if commit:
            self.db.commit()
        return self.db_cursor

    def _execute_many_db_command(self, command, args_list, commit=False):
        self.db_cursor.executemany(command, args_list)
        if commit:
            self.db.commit()
        return self.db_cursor

    def _check_agent_userid(self, agent_id):
        try:
            user_query = 'SELECT user_id FROM user WHERE agent_id = ?'
            results = self._execute_db_command(user_query, (agent_id,))
            first_row = results.fetchone()
            if first_row:
                user_id = first_row[0]
                return user_id
            else:
                return None
        except Exception as e:
            print(f'Error querying user_id for agent_id {agent_id}: {e}')
            return None

    def _add_comments_to_posts(self, posts_results):
        posts = []
        for row in posts_results:
            post_id, user_id, original_post_id, content, quote_content, created_at, num_likes, num_dislikes, num_shares = row
            post_type_result = self._get_post_type(post_id)
            if post_type_result is None:
                continue
            original_user_id_query = 'SELECT user_id FROM post WHERE post_id = ?'
            if post_type_result['type'] == 'repost':
                self.db_cursor.execute(original_user_id_query, (original_post_id,))
                original_user_id = self.db_cursor.fetchone()[0]
                original_post_id = post_id
                post_id = post_type_result['root_post_id']
                self.db_cursor.execute('SELECT content, quote_content, created_at, num_likes, num_dislikes, num_shares, num_reports FROM post WHERE post_id = ?', (post_id,))
                original_post_result = self.db_cursor.fetchone()
                content, quote_content, created_at, num_likes, num_dislikes, num_shares, num_reports = original_post_result
                post_content = f'User {user_id} reposted a post from User {original_user_id}. Repost content: {content}. '
            elif post_type_result['type'] == 'quote':
                self.db_cursor.execute(original_user_id_query, (original_post_id,))
                original_user_id = self.db_cursor.fetchone()[0]
                post_content = f'User {user_id} quoted a post from User {original_user_id}. Quote content: {quote_content}. Original Content: {content}'
            elif post_type_result['type'] == 'common':
                post_content = content
                self.db_cursor.execute('SELECT num_reports FROM post WHERE post_id = ?', (post_id,))
                num_reports = self.db_cursor.fetchone()[0]
            self.db_cursor.execute('SELECT comment_id, post_id, user_id, content, created_at, num_likes, num_dislikes FROM comment WHERE post_id = ?', (post_id,))
            comments_results = self.db_cursor.fetchall()
            comments = [{'comment_id': comment_id, 'post_id': post_id, 'user_id': user_id, 'content': content, 'created_at': created_at, **({'score': num_likes - num_dislikes} if self.show_score else {'num_likes': num_likes, 'num_dislikes': num_dislikes})} for comment_id, post_id, user_id, content, created_at, num_likes, num_dislikes in comments_results]
            if num_reports >= self.report_threshold:
                warning_message = f'[Warning: This post has been reported {num_reports} times]'
                post_content = f'{warning_message}\n{post_content}'
            posts.append({'post_id': post_id if post_type_result['type'] != 'repost' else original_post_id, 'user_id': user_id, 'content': post_content, 'created_at': created_at, **({'score': num_likes - num_dislikes} if self.show_score else {'num_likes': num_likes, 'num_dislikes': num_dislikes}), 'num_shares': num_shares, 'num_reports': num_reports, 'comments': comments})
        return posts

    def _record_trace(self, user_id, action_type, action_info, current_time=None):
        """If, in addition to the trace, the operation function also records
        time in other tables of the database, use the time of entering
        the operation function for consistency.

        Pass in current_time to make, for example, the created_at in the post
        table exactly the same as the time in the trace table.

        If only the trace table needs to record time, use the entry time into
        _record_trace as the time for the trace record.
        """
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        trace_insert_query = 'INSERT INTO trace (user_id, created_at, action, info) VALUES (?, ?, ?, ?)'
        action_info_str = json.dumps(action_info)
        self._execute_db_command(trace_insert_query, (user_id, current_time, action_type, action_info_str), commit=True)

    def _check_self_post_rating(self, post_id, user_id):
        self_like_check_query = 'SELECT user_id FROM post WHERE post_id = ?'
        self._execute_db_command(self_like_check_query, (post_id,))
        result = self.db_cursor.fetchone()
        if result and result[0] == user_id:
            error_message = 'Users are not allowed to like/dislike their own posts.'
            return {'success': False, 'error': error_message}
        else:
            return None

    def _check_self_comment_rating(self, comment_id, user_id):
        self_like_check_query = 'SELECT user_id FROM comment WHERE comment_id = ?'
        self._execute_db_command(self_like_check_query, (comment_id,))
        result = self.db_cursor.fetchone()
        if result and result[0] == user_id:
            error_message = 'Users are not allowed to like/dislike their own comments.'
            return {'success': False, 'error': error_message}
        else:
            return None

    def _get_post_type(self, post_id: int):
        query = 'SELECT original_post_id, quote_content FROM post WHERE post_id = ?'
        self._execute_db_command(query, (post_id,))
        result = self.db_cursor.fetchone()
        if not result:
            return None
        original_post_id, quote_content = result
        if original_post_id is None:
            return {'type': 'common', 'root_post_id': None}
        elif quote_content is None:
            return {'type': 'repost', 'root_post_id': original_post_id}
        else:
            return {'type': 'quote', 'root_post_id': original_post_id}

def _execute_db_command(self, command, args=(), commit=False):
    self.db_cursor.execute(command, args)
    if commit:
        self.db.commit()
    return self.db_cursor

def _execute_many_db_command(self, command, args_list, commit=False):
    self.db_cursor.executemany(command, args_list)
    if commit:
        self.db.commit()
    return self.db_cursor

def _check_agent_userid(self, agent_id):
    try:
        user_query = 'SELECT user_id FROM user WHERE agent_id = ?'
        results = self._execute_db_command(user_query, (agent_id,))
        first_row = results.fetchone()
        if first_row:
            user_id = first_row[0]
            return user_id
        else:
            return None
    except Exception as e:
        print(f'Error querying user_id for agent_id {agent_id}: {e}')
        return None

def _add_comments_to_posts(self, posts_results):
    posts = []
    for row in posts_results:
        post_id, user_id, original_post_id, content, quote_content, created_at, num_likes, num_dislikes, num_shares = row
        post_type_result = self._get_post_type(post_id)
        if post_type_result is None:
            continue
        original_user_id_query = 'SELECT user_id FROM post WHERE post_id = ?'
        if post_type_result['type'] == 'repost':
            self.db_cursor.execute(original_user_id_query, (original_post_id,))
            original_user_id = self.db_cursor.fetchone()[0]
            original_post_id = post_id
            post_id = post_type_result['root_post_id']
            self.db_cursor.execute('SELECT content, quote_content, created_at, num_likes, num_dislikes, num_shares, num_reports FROM post WHERE post_id = ?', (post_id,))
            original_post_result = self.db_cursor.fetchone()
            content, quote_content, created_at, num_likes, num_dislikes, num_shares, num_reports = original_post_result
            post_content = f'User {user_id} reposted a post from User {original_user_id}. Repost content: {content}. '
        elif post_type_result['type'] == 'quote':
            self.db_cursor.execute(original_user_id_query, (original_post_id,))
            original_user_id = self.db_cursor.fetchone()[0]
            post_content = f'User {user_id} quoted a post from User {original_user_id}. Quote content: {quote_content}. Original Content: {content}'
        elif post_type_result['type'] == 'common':
            post_content = content
            self.db_cursor.execute('SELECT num_reports FROM post WHERE post_id = ?', (post_id,))
            num_reports = self.db_cursor.fetchone()[0]
        self.db_cursor.execute('SELECT comment_id, post_id, user_id, content, created_at, num_likes, num_dislikes FROM comment WHERE post_id = ?', (post_id,))
        comments_results = self.db_cursor.fetchall()
        comments = [{'comment_id': comment_id, 'post_id': post_id, 'user_id': user_id, 'content': content, 'created_at': created_at, **({'score': num_likes - num_dislikes} if self.show_score else {'num_likes': num_likes, 'num_dislikes': num_dislikes})} for comment_id, post_id, user_id, content, created_at, num_likes, num_dislikes in comments_results]
        if num_reports >= self.report_threshold:
            warning_message = f'[Warning: This post has been reported {num_reports} times]'
            post_content = f'{warning_message}\n{post_content}'
        posts.append({'post_id': post_id if post_type_result['type'] != 'repost' else original_post_id, 'user_id': user_id, 'content': post_content, 'created_at': created_at, **({'score': num_likes - num_dislikes} if self.show_score else {'num_likes': num_likes, 'num_dislikes': num_dislikes}), 'num_shares': num_shares, 'num_reports': num_reports, 'comments': comments})
    return posts

def _record_trace(self, user_id, action_type, action_info, current_time=None):
    """If, in addition to the trace, the operation function also records
        time in other tables of the database, use the time of entering
        the operation function for consistency.

        Pass in current_time to make, for example, the created_at in the post
        table exactly the same as the time in the trace table.

        If only the trace table needs to record time, use the entry time into
        _record_trace as the time for the trace record.
        """
    if self.recsys_type == RecsysType.REDDIT:
        current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
    else:
        current_time = self.sandbox_clock.get_time_step()
    trace_insert_query = 'INSERT INTO trace (user_id, created_at, action, info) VALUES (?, ?, ?, ?)'
    action_info_str = json.dumps(action_info)
    self._execute_db_command(trace_insert_query, (user_id, current_time, action_type, action_info_str), commit=True)

def _check_self_post_rating(self, post_id, user_id):
    self_like_check_query = 'SELECT user_id FROM post WHERE post_id = ?'
    self._execute_db_command(self_like_check_query, (post_id,))
    result = self.db_cursor.fetchone()
    if result and result[0] == user_id:
        error_message = 'Users are not allowed to like/dislike their own posts.'
        return {'success': False, 'error': error_message}
    else:
        return None

def _check_self_comment_rating(self, comment_id, user_id):
    self_like_check_query = 'SELECT user_id FROM comment WHERE comment_id = ?'
    self._execute_db_command(self_like_check_query, (comment_id,))
    result = self.db_cursor.fetchone()
    if result and result[0] == user_id:
        error_message = 'Users are not allowed to like/dislike their own comments.'
        return {'success': False, 'error': error_message}
    else:
        return None

def _get_post_type(self, post_id: int):
    query = 'SELECT original_post_id, quote_content FROM post WHERE post_id = ?'
    self._execute_db_command(query, (post_id,))
    result = self.db_cursor.fetchone()
    if not result:
        return None
    original_post_id, quote_content = result
    if original_post_id is None:
        return {'type': 'common', 'root_post_id': None}
    elif quote_content is None:
        return {'type': 'repost', 'root_post_id': original_post_id}
    else:
        return {'type': 'quote', 'root_post_id': original_post_id}

def print_db_contents(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_log.info('Tables:' + ' '.join([str(table[0]) for table in tables]))
    for table_name in tables:
        table_log.info(f'\nTable: {table_name[0]}')
        cursor.execute(f'PRAGMA table_info({table_name[0]})')
        columns = cursor.fetchall()
        table_log.info('Columns:')
        for col in columns:
            table_log.info(f'  {col[1]} ({col[2]})')
        cursor.execute(f'SELECT * FROM {table_name[0]}')
        rows = cursor.fetchall()
        table_log.info('Contents:')
        for row in rows:
            table_log.info(' ' + ', '.join((str(item) for item in row)))
    conn.close()

class Clock:
    """Clock used for the sandbox."""

    def __init__(self, k: int=1):
        self.real_start_time = datetime.now()
        self.k = k
        self.time_step = 0

    def time_transfer(self, now_time: datetime, start_time: datetime) -> datetime:
        time_diff = now_time - self.real_start_time
        adjusted_diff = self.k * time_diff
        adjusted_time = start_time + adjusted_diff
        return adjusted_time

    def get_time_step(self) -> str:
        return str(self.time_step)

def __init__(self, k: int=1):
    self.real_start_time = datetime.now()
    self.k = k
    self.time_step = 0

