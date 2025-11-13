# Cluster 20

def generate_user_profile(age, gender, mbti, profession, topics):
    prompt = prompt_tem.format(age=age, gender=gender, mbti=mbti, profession=profession, topics=topics)
    user = rag.gen(prompt)
    user_dict = user.dict()
    user_dict['topics'] = topics
    return user_dict

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

def visualize(self, path: str, vertex_size: int=20, edge_arrow_size: float=0.5, with_labels: bool=True, vertex_color: str='#f74f1b', vertex_frame_width: int=2, width: int=1000, height: int=1000):
    if self.backend == 'neo4j':
        raise ValueError('Neo4j backend does not support visualization.')
    layout = self.graph.layout('auto')
    if with_labels:
        labels = [node_id for node_id, _ in self.get_agents()]
    else:
        labels = None
    ig.plot(self.graph, target=path, layout=layout, vertex_label=labels, vertex_size=vertex_size, vertex_color=vertex_color, edge_arrow_size=edge_arrow_size, vertex_frame_width=vertex_frame_width, bbox=(width, height))

def get_twhin_tokenizer():
    global twhin_tokenizer
    if twhin_tokenizer is None:
        from transformers import AutoTokenizer
        twhin_tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path='Twitter/twhin-bert-base', model_max_length=512)
    return twhin_tokenizer

def get_twhin_model(device):
    global twhin_model
    if twhin_model is None:
        from transformers import AutoModel
        twhin_model = AutoModel.from_pretrained(pretrained_model_name_or_path='Twitter/twhin-bert-base').to(device)
    return twhin_model

def load_model(model_name):
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if model_name == 'paraphrase-MiniLM-L6-v2':
            return SentenceTransformer(model_name, device=device, cache_folder='./models')
        elif model_name == 'Twitter/twhin-bert-base':
            twhin_tokenizer = get_twhin_tokenizer()
            twhin_model = get_twhin_model(device)
            return (twhin_tokenizer, twhin_model)
        else:
            raise ValueError(f'Unknown model name: {model_name}')
    except Exception as e:
        raise Exception(f'Failed to load the model: {model_name}') from e

def get_recsys_model(recsys_type: str=None):
    if recsys_type == RecsysType.TWITTER.value:
        model = load_model('paraphrase-MiniLM-L6-v2')
        return model
    elif recsys_type == RecsysType.TWHIN.value:
        twhin_tokenizer, twhin_model = load_model('Twitter/twhin-bert-base')
        models = (twhin_tokenizer, twhin_model)
        return models
    elif recsys_type == RecsysType.REDDIT.value or recsys_type == RecsysType.RANDOM.value:
        return None
    else:
        raise ValueError(f'Unknown recsys type: {recsys_type}')

@torch.no_grad()
def process_batch(model: AutoModel, tokenizer: AutoTokenizer, batch_texts: List[str]):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    inputs = tokenizer(batch_texts, return_tensors='pt', padding=True, truncation=True)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    outputs = model(**inputs)
    return outputs.pooler_output

@dataclass
class UserInfo:
    user_name: str | None = None
    name: str | None = None
    description: str | None = None
    profile: dict[str, Any] | None = None
    recsys_type: str = 'twitter'
    is_controllable: bool = False

    def to_custom_system_message(self, user_info_template: TextPrompt) -> str:
        required_keys = user_info_template.key_words
        info_keys = set(self.profile.keys())
        missing = required_keys - info_keys
        extra = info_keys - required_keys
        if missing:
            raise ValueError(f'Missing required keys in UserInfo.profile: {missing}')
        if extra:
            warnings.warn(f'Extra keys not used in UserInfo.profile: {extra}')
        return user_info_template.format(**self.profile)

    def to_system_message(self) -> str:
        if self.recsys_type != 'reddit':
            return self.to_twitter_system_message()
        else:
            return self.to_reddit_system_message()

    def to_twitter_system_message(self) -> str:
        name_string = ''
        description_string = ''
        if self.name is not None:
            name_string = f'Your name is {self.name}.'
        if self.profile is None:
            description = name_string
        elif 'other_info' not in self.profile:
            description = name_string
        elif 'user_profile' in self.profile['other_info']:
            if self.profile['other_info']['user_profile'] is not None:
                user_profile = self.profile['other_info']['user_profile']
                description_string = f'Your have profile: {user_profile}.'
                description = f'{name_string}\n{description_string}'
        system_content = f"\n# OBJECTIVE\nYou're a Twitter user, and I'll present you with some posts. After you see the posts, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n        "
        return system_content

    def to_reddit_system_message(self) -> str:
        name_string = ''
        description_string = ''
        if self.name is not None:
            name_string = f'Your name is {self.name}.'
        if self.profile is None:
            description = name_string
        elif 'other_info' not in self.profile:
            description = name_string
        elif 'user_profile' in self.profile['other_info']:
            if self.profile['other_info']['user_profile'] is not None:
                user_profile = self.profile['other_info']['user_profile']
                description_string = f'Your have profile: {user_profile}.'
                description = f'{name_string}\n{description_string}'
                print(self.profile['other_info'])
                description += f'You are a {self.profile['other_info']['gender']}, {self.profile['other_info']['age']} years old, with an MBTI personality type of {self.profile['other_info']['mbti']} from {self.profile['other_info']['country']}.'
        system_content = f"\n# OBJECTIVE\nYou're a Reddit user, and I'll present you with some tweets. After you see the tweets, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n"
        return system_content

def to_custom_system_message(self, user_info_template: TextPrompt) -> str:
    required_keys = user_info_template.key_words
    info_keys = set(self.profile.keys())
    missing = required_keys - info_keys
    extra = info_keys - required_keys
    if missing:
        raise ValueError(f'Missing required keys in UserInfo.profile: {missing}')
    if extra:
        warnings.warn(f'Extra keys not used in UserInfo.profile: {extra}')
    return user_info_template.format(**self.profile)

