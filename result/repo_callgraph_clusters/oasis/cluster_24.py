# Cluster 24

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

def add_agent(self, agent: SocialAgent):
    if self.backend == 'igraph':
        self.graph.add_vertex(agent.social_agent_id)
    else:
        self.graph.create_agent(agent.social_agent_id)
    self.agent_mappings[agent.social_agent_id] = agent

