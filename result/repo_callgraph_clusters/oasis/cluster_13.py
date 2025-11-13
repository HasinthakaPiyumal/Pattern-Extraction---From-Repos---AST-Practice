# Cluster 13

def connect_to_neo4j(config):
    return GraphDatabase.driver(config.uri, auth=(config.username, config.password))

def connect_to_neo4j(config):
    return GraphDatabase.driver(config.uri, auth=(config.username, config.password))

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

def __init__(self, nei4j_config: Neo4jConfig):
    self.driver = GraphDatabase.driver(nei4j_config.uri, auth=(nei4j_config.username, nei4j_config.password))
    self.driver.verify_connectivity()

