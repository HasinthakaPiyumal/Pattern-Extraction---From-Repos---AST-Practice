# Cluster 4

def neo4j_vars_set() -> bool:
    return os.getenv('NEO4J_URI') is not None and os.getenv('NEO4J_USERNAME') is not None and (os.getenv('NEO4J_PASSWORD') is not None)

def test_agent_graph(tmp_path):
    twitter_channel = Channel()
    graph = AgentGraph()
    agent_0 = SocialAgent(agent_id=0, user_info=UserInfo(name='0'), channel=twitter_channel)
    agent_1 = SocialAgent(agent_id=1, user_info=UserInfo(name='1'), channel=twitter_channel)
    agent_2 = SocialAgent(agent_id=2, user_info=UserInfo(name='2'), channel=twitter_channel)
    graph.add_agent(agent_0)
    graph.add_agent(agent_1)
    graph.add_agent(agent_2)
    assert graph.get_num_nodes() == 3
    assert len(graph.agent_mappings) == 3
    graph.add_edge(0, 1)
    graph.add_edge(0, 2)
    assert graph.get_num_edges() == 2
    edges = graph.get_edges()
    assert len(edges) == 2
    assert edges[0] == (0, 1)
    assert edges[1] == (0, 2)
    img_path = osp.join(tmp_path, 'img.pdf')
    graph.visualize(img_path)
    assert osp.exists(img_path)
    agents = graph.get_agents()
    assert len(agents) == 3
    assert agents[0][0] == 0
    assert id(agents[0][1]) == id(agent_0)
    assert agents[1][0] == 1
    assert id(agents[1][1]) == id(agent_1)
    assert agents[2][0] == 2
    assert id(agents[2][1]) == id(agent_2)
    graph.remove_edge(0, 1)
    assert graph.get_num_edges() == 1
    graph.remove_agent(agent_0)
    assert len(graph.agent_mappings) == 2
    assert graph.get_num_nodes() == 2
    assert graph.get_num_edges() == 0
    graph.reset()
    assert len(graph.agent_mappings) == 0
    assert graph.get_num_nodes() == 0
    assert graph.get_num_edges() == 0

@pytest.mark.skipif(not neo4j_vars_set(), reason='One or more neo4j env variables are not set')
def test_agent_neo4j_graph():
    channel = Channel()
    graph = AgentGraph(backend='neo4j', neo4j_config=Neo4jConfig(uri=os.getenv('NEO4J_URI'), username=os.getenv('NEO4J_USERNAME'), password=os.getenv('NEO4J_PASSWORD')))
    agent_0 = SocialAgent(agent_id=0, user_info=UserInfo(name='0'), channel=channel)
    agent_1 = SocialAgent(agent_id=1, user_info=UserInfo(name='1'), channel=channel)
    agent_2 = SocialAgent(agent_id=2, user_info=UserInfo(name='2'), channel=channel)
    graph.add_agent(agent_0)
    graph.add_agent(agent_1)
    graph.add_agent(agent_2)
    assert graph.get_num_nodes() == 3
    assert len(graph.agent_mappings) == 3
    graph.add_edge(0, 1)
    graph.add_edge(0, 2)
    assert graph.get_num_edges() == 2
    edges = graph.get_edges()
    assert len(edges) == 2
    assert edges[0] == (0, 1)
    assert edges[1] == (0, 2)
    agents = graph.get_agents()
    assert len(agents) == 3
    assert agents[0][0] == 0
    assert id(agents[0][1]) == id(agent_0)
    assert agents[1][0] == 1
    assert id(agents[1][1]) == id(agent_1)
    assert agents[2][0] == 2
    assert id(agents[2][1]) == id(agent_2)
    graph.remove_edge(0, 1)
    assert graph.get_num_edges() == 1
    graph.remove_agent(agent_0)
    assert len(graph.agent_mappings) == 2
    assert graph.get_num_nodes() == 2
    assert graph.get_num_edges() == 0
    graph.reset()
    assert len(graph.agent_mappings) == 0
    assert graph.get_num_nodes() == 0
    assert graph.get_num_edges() == 0

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

def add_edge(self, agent_id_0: int, agent_id_1: int):
    try:
        self.graph.add_edge(agent_id_0, agent_id_1)
    except Exception:
        pass

def remove_edge(self, agent_id_0: int, agent_id_1: int):
    if self.backend == 'igraph':
        if self.graph.are_connected(agent_id_0, agent_id_1):
            self.graph.delete_edges([(agent_id_0, agent_id_1)])
    else:
        self.graph.remove_edge(agent_id_0, agent_id_1)

def connect_platform_channel(channel: Channel, agent_graph: AgentGraph | None=None) -> AgentGraph:
    for _, agent in agent_graph.get_agents():
        agent.channel = channel
        agent.env.action.channel = channel
    return agent_graph

class SocialAgent(ChatAgent):
    """Social Agent."""

    def __init__(self, agent_id: int, user_info: UserInfo, user_info_template: TextPrompt | None=None, channel: Channel | None=None, model: Optional[Union[BaseModelBackend, List[BaseModelBackend], ModelManager]]=None, agent_graph: 'AgentGraph'=None, available_actions: list[ActionType]=None, tools: Optional[List[Union[FunctionTool, Callable]]]=None, max_iteration: int=1, interview_record: bool=False):
        self.social_agent_id = agent_id
        self.user_info = user_info
        self.channel = channel or Channel()
        self.env = SocialEnvironment(SocialAction(agent_id, self.channel))
        if user_info_template is None:
            system_message_content = self.user_info.to_system_message()
        else:
            system_message_content = self.user_info.to_custom_system_message(user_info_template)
        system_message = BaseMessage.make_assistant_message(role_name='system', content=system_message_content)
        if not available_actions:
            agent_log.info('No available actions defined, using all actions.')
            self.action_tools = self.env.action.get_openai_function_list()
        else:
            all_tools = self.env.action.get_openai_function_list()
            all_possible_actions = [tool.func.__name__ for tool in all_tools]
            for action in available_actions:
                action_name = action.value if isinstance(action, ActionType) else action
                if action_name not in all_possible_actions:
                    agent_log.warning(f'Action {action_name} is not supported. Supported actions are: {', '.join(all_possible_actions)}')
            self.action_tools = [tool for tool in all_tools if tool.func.__name__ in [a.value if isinstance(a, ActionType) else a for a in available_actions]]
        all_tools = (tools or []) + (self.action_tools or [])
        super().__init__(system_message=system_message, model=model, scheduling_strategy='random_model', tools=all_tools)
        self.max_iteration = max_iteration
        self.interview_record = interview_record
        self.agent_graph = agent_graph
        self.test_prompt = '\nHelen is a successful writer who usually writes popular western novels. Now, she has an idea for a new novel that could really make a big impact. If it works out, it could greatly improve her career. But if it fails, she will have spent a lot of time and effort for nothing.\n\nWhat do you think Helen should do?'

    async def perform_action_by_llm(self):
        env_prompt = await self.env.to_text_prompt()
        user_msg = BaseMessage.make_user_message(role_name='User', content=f"Please perform social media actions after observing the platform environments. Notice that don't limit your actions for example to just like the posts. Here is your social media environment: {env_prompt}")
        try:
            agent_log.info(f'Agent {self.social_agent_id} observing environment: {env_prompt}')
            response = await self.astep(user_msg)
            for tool_call in response.info['tool_calls']:
                action_name = tool_call.tool_name
                args = tool_call.args
                agent_log.info(f'Agent {self.social_agent_id} performed action: {action_name} with args: {args}')
                if action_name not in ALL_SOCIAL_ACTIONS:
                    agent_log.info(f'Agent {self.social_agent_id} get the result: {tool_call.result}')
                return response
        except Exception as e:
            agent_log.error(f'Agent {self.social_agent_id} error: {e}')
            return e

    async def perform_test(self):
        """
        doing group polarization test for all agents.
        TODO: rewrite the function according to the ChatAgent.
        TODO: unify the test and interview function.
        """
        _ = BaseMessage.make_user_message(role_name='User', content='You are a twitter user.')
        openai_messages, num_tokens = self.memory.get_context()
        openai_messages = [{'role': self.system_message.role_name, 'content': self.system_message.content.split('# RESPONSE FORMAT')[0]}] + openai_messages + [{'role': 'user', 'content': self.test_prompt}]
        agent_log.info(f'Agent {self.social_agent_id}: {openai_messages}')
        response = await self._aget_model_response(openai_messages=openai_messages, num_tokens=num_tokens)
        content = response.output_messages[0].content
        agent_log.info(f'Agent {self.social_agent_id} receive response: {content}')
        return {'user_id': self.social_agent_id, 'prompt': openai_messages, 'content': content}

    async def perform_interview(self, interview_prompt: str):
        """
        Perform an interview with the agent.
        """
        user_msg = BaseMessage.make_user_message(role_name='User', content='You are a twitter user.')
        if self.interview_record:
            self.update_memory(message=user_msg, role=OpenAIBackendRole.SYSTEM)
        openai_messages, num_tokens = self.memory.get_context()
        openai_messages = [{'role': self.system_message.role_name, 'content': self.system_message.content.split('# RESPONSE FORMAT')[0]}] + openai_messages + [{'role': 'user', 'content': interview_prompt}]
        agent_log.info(f'Agent {self.social_agent_id}: {openai_messages}')
        response = await self._aget_model_response(openai_messages=openai_messages, num_tokens=num_tokens)
        content = response.output_messages[0].content
        if self.interview_record:
            self.update_memory(message=response.output_messages[0], role=OpenAIBackendRole.USER)
        agent_log.info(f'Agent {self.social_agent_id} receive response: {content}')
        interview_data = {'prompt': interview_prompt, 'response': content}
        result = await self.env.action.perform_action(interview_data, ActionType.INTERVIEW.value)
        return {'user_id': self.social_agent_id, 'prompt': openai_messages, 'content': content, 'success': result.get('success', False)}

    async def perform_action_by_hci(self) -> Any:
        print('Please choose one function to perform:')
        function_list = self.env.action.get_openai_function_list()
        for i in range(len(function_list)):
            agent_log.info(f'Agent {self.social_agent_id} function: {function_list[i].func.__name__}')
        selection = int(input('Enter your choice: '))
        if not 0 <= selection < len(function_list):
            agent_log.error(f'Agent {self.social_agent_id} invalid input.')
            return
        func = function_list[selection].func
        params = inspect.signature(func).parameters
        args = []
        for param in params.values():
            while True:
                try:
                    value = input(f'Enter value for {param.name}: ')
                    args.append(value)
                    break
                except ValueError:
                    agent_log.error('Invalid input, please enter an integer.')
        result = await func(*args)
        return result

    async def perform_action_by_data(self, func_name, *args, **kwargs) -> Any:
        func_name = func_name.value if isinstance(func_name, ActionType) else func_name
        function_list = self.env.action.get_openai_function_list()
        for i in range(len(function_list)):
            if function_list[i].func.__name__ == func_name:
                func = function_list[i].func
                result = await func(*args, **kwargs)
                self.update_memory(message=BaseMessage.make_user_message(role_name=OpenAIBackendRole.SYSTEM, content=f'Agent {self.social_agent_id} performed {func_name} with args: {args} and kwargs: {kwargs}and the result is {result}'), role=OpenAIBackendRole.SYSTEM)
                agent_log.info(f'Agent {self.social_agent_id}: {result}')
                return result
        raise ValueError(f'Function {func_name} not found in the list.')

    def perform_agent_graph_action(self, action_name: str, arguments: dict[str, Any]):
        """Remove edge if action is unfollow or add edge
        if action is follow to the agent graph.
        """
        if 'unfollow' in action_name:
            followee_id: int | None = arguments.get('followee_id', None)
            if followee_id is None:
                return
            self.agent_graph.remove_edge(self.social_agent_id, followee_id)
            agent_log.info(f'Agent {self.social_agent_id} unfollowed Agent {followee_id}')
        elif 'follow' in action_name:
            followee_id: int | None = arguments.get('followee_id', None)
            if followee_id is None:
                return
            self.agent_graph.add_edge(self.social_agent_id, followee_id)
            agent_log.info(f'Agent {self.social_agent_id} followed Agent {followee_id}')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(agent_id={self.social_agent_id}, model_type={self.model_type.value})'

def perform_agent_graph_action(self, action_name: str, arguments: dict[str, Any]):
    """Remove edge if action is unfollow or add edge
        if action is follow to the agent graph.
        """
    if 'unfollow' in action_name:
        followee_id: int | None = arguments.get('followee_id', None)
        if followee_id is None:
            return
        self.agent_graph.remove_edge(self.social_agent_id, followee_id)
        agent_log.info(f'Agent {self.social_agent_id} unfollowed Agent {followee_id}')
    elif 'follow' in action_name:
        followee_id: int | None = arguments.get('followee_id', None)
        if followee_id is None:
            return
        self.agent_graph.add_edge(self.social_agent_id, followee_id)
        agent_log.info(f'Agent {self.social_agent_id} followed Agent {followee_id}')

