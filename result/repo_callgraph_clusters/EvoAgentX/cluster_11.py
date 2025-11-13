# Cluster 11

class MemoryAgent(Agent):
    memory_manager: Optional[MemoryManager] = Field(default=None, description='Manager for long-term memory operations')
    inputs: List[Dict] = Field(default_factory=list, description='Input specifications for the memory action')
    outputs: List[Dict] = Field(default_factory=list, description='Output specifications for the memory action')

    def __init__(self, name: str='MemoryAgent', description: str='An agent that uses long-term memory to provide context-aware responses', inputs: Optional[List[Dict]]=None, outputs: Optional[List[Dict]]=None, llm_config: Optional[OpenAILLMConfig]=None, storage_handler: Optional[StorageHandler]=None, rag_config: Optional[RAGConfig]=None, conversation_id: Optional[str]=None, system_prompt: Optional[str]=None, prompt: str='Based on the following context and user prompt, provide a relevant response:\n\nContext: {context}\n\nUser Prompt: {user_prompt}', **kwargs):
        inputs = inputs or []
        outputs = outputs or []
        super().__init__(name=name, description=description, llm_config=llm_config, system_prompt=system_prompt, storage_handler=storage_handler, inputs=inputs, outputs=outputs, **kwargs)
        self.long_term_memory = LongTermMemory(storage_handler=storage_handler, rag_config=rag_config, default_corpus_id=conversation_id)
        self.memory_manager = MemoryManager(memory=self.long_term_memory, llm=llm_config.get_llm() if llm_config else None, use_llm_management=True)
        self.inputs = inputs
        self.outputs = outputs
        self.actions = []
        self._action_map = {}
        memory_action = MemoryAction(name='MemoryAction', description='Action that processes user input with long-term memory context', prompt=prompt, inputs_format=MemoryActionInput, outputs_format=MemoryActionOutput)
        self.add_action(memory_action)

    def _create_output_message(self, action_output, action_name: str, action_input_data: Optional[Dict], prompt: str, return_msg_type: MessageType=MessageType.RESPONSE, **kwargs) -> Message:
        msg = super()._create_output_message(action_output=action_output, action_name=action_name, action_input_data=action_input_data, prompt=prompt, return_msg_type=return_msg_type, **kwargs)
        if action_input_data and 'user_prompt' in action_input_data:
            user_msg = Message(content=action_input_data['user_prompt'], msg_type=MessageType.REQUEST, conversation_id=msg.conversation_id)
            asyncio.create_task(self.memory_manager.handle_memory(action='add', data=user_msg))
        response_msg = Message(content=action_output.response if hasattr(action_output, 'response') else str(action_output), msg_type=MessageType.RESPONSE, conversation_id=msg.conversation_id)
        asyncio.create_task(self.memory_manager.handle_memory(action='add', data=response_msg))
        return msg

    async def async_execute(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[Dict]=None, return_msg_type: Optional[MessageType]=MessageType.RESPONSE, return_action_input_data: Optional[bool]=False, **kwargs) -> Union[Message, Tuple[Message, Dict]]:
        """
        Execute an action asynchronously with memory management.

        Args:
            action_name: Name of the action to execute
            msgs: Optional list of messages providing context
            action_input_data: Optional input data for the action
            return_msg_type: Message type for the return message
            return_action_input_data: Whether to return the action input data
            **kwargs: Additional parameters

        Returns:
            Message or tuple: The execution result, optionally with input data
        """
        action, action_input_data = self._prepare_execution(action_name=action_name, msgs=msgs, action_input_data=action_input_data, **kwargs)
        execution_results = await action.async_execute(llm=self.llm, inputs=action_input_data, sys_msg=self.system_prompt, return_prompt=True, memory_manager=self.memory_manager, **kwargs)
        action_output, prompt = execution_results
        message = self._create_output_message(action_output=action_output, prompt=prompt, action_name=action_name, return_msg_type=return_msg_type, action_input_data=action_input_data, **kwargs)
        if return_action_input_data:
            return (message, action_input_data)
        return message

    def execute(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[Dict]=None, return_msg_type: Optional[MessageType]=MessageType.RESPONSE, return_action_input_data: Optional[bool]=False, **kwargs) -> Union[Message, Tuple[Message, Dict]]:
        """
        Execute an action synchronously with memory management.

        Args:
            action_name: Name of the action to execute
            msgs: Optional list of messages providing context
            action_input_data: Optional input data for the action
            return_msg_type: Message type for the return message
            return_action_input_data: Whether to return the action input data
            **kwargs: Additional parameters

        Returns:
            Message or tuple: The execution result, optionally with input data
        """
        action, action_input_data = self._prepare_execution(action_name=action_name, msgs=msgs, action_input_data=action_input_data, **kwargs)
        execution_results = action.execute(llm=self.llm, inputs=action_input_data, sys_msg=self.system_prompt, return_prompt=True, memory_manager=self.memory_manager, **kwargs)
        action_output, prompt = execution_results
        message = self._create_output_message(action_output=action_output, prompt=prompt, action_name=action_name, return_msg_type=return_msg_type, action_input_data=action_input_data, **kwargs)
        if return_action_input_data:
            return (message, action_input_data)
        return message

    def chat(self, user_prompt: str, *, conversation_id: Optional[str]=None, top_k: Optional[int]=None, metadata_filters: Optional[dict]=None, return_message: bool=True, **kwargs):
        action_input_data = {'user_prompt': user_prompt, 'conversation_id': conversation_id or self._default_conversation_id(), 'top_k': top_k if top_k is not None else 3, 'metadata_filters': metadata_filters or {}}
        msg = self.execute(action_name='MemoryAction', action_input_data=action_input_data, return_msg_type=MessageType.RESPONSE, **kwargs)
        return msg if return_message else getattr(msg, 'content', None) or str(msg)

    async def async_chat(self, user_prompt: str, *, conversation_id: Optional[str]=None, top_k: Optional[int]=None, metadata_filters: Optional[dict]=None, return_message: bool=True, **kwargs):
        action_input_data = {'user_prompt': user_prompt, 'conversation_id': conversation_id or self._default_conversation_id(), 'top_k': top_k if top_k is not None else 3, 'metadata_filters': metadata_filters or {}}
        msg = await self.async_execute(action_name='MemoryAction', action_input_data=action_input_data, return_msg_type=MessageType.RESPONSE, **kwargs)
        return msg if return_message else getattr(msg, 'content', None) or str(msg)

    def _default_conversation_id(self) -> str:
        """
        Session scope: By default, a new uuid4() is returned (new session).
        User/global scope: Reuse LongTermMemory.default_corpus_id (stable namespace).
        Note: The final ID is still uniformly managed by MemoryAgent._prepare_execution() (which will override based on the scope).
        """
        scope = getattr(self, 'conversation_scope', 'session')
        if scope == 'session':
            return str(uuid4())
        return getattr(getattr(self, 'long_term_memory', None), 'default_corpus_id', None) or 'global_corpus'

    async def interactive_chat(self, conversation_id: Optional[str]=None, top_k: int=3, metadata_filters: Optional[dict]=None):
        """
        In interactive chat, each round of input will:
        1. Retrieve from memory
        2. Generate a response based on historical context
        3. Write the input/output to long-term memory and refresh the index 
        """
        conversation_id = conversation_id or self._default_conversation_id()
        metadata_filters = metadata_filters or {}
        print("💬 MemoryAgent has been started (type 'exit' to quit)\n")
        while True:
            user_prompt = input('You: ').strip()
            if user_prompt.lower() in ['exit', 'quit']:
                print('🔚 Conversation ended')
                break
            retrieved_memories = await self.memory_manager.handle_memory(action='search', user_prompt=user_prompt, top_k=top_k, metadata_filters=metadata_filters)
            context_texts = []
            for msg, _ in retrieved_memories:
                if hasattr(msg, 'content') and msg.content:
                    context_texts.append(msg.content)
            context_str = '\n'.join(context_texts)
            full_prompt = f'Context:\n{context_str}\n\nUser: {user_prompt}' if context_str else user_prompt
            msg = await self.async_chat(user_prompt=full_prompt, conversation_id=conversation_id, top_k=top_k, metadata_filters=metadata_filters)
            print(f'Agent: {msg.content}\n')
            if hasattr(self.memory_manager, 'handle_memory_flush'):
                await self.memory_manager.handle_memory_flush()
            else:
                await asyncio.sleep(0.1)

    def save_module(self, path: str, ignore: List[str]=['llm', 'llm_config', 'memory_manager'], **kwargs) -> str:
        """
        Save the agent's configuration to a JSON file, excluding memory_manager by default.

        Args:
            path: File path to save the configuration
            ignore: List of keys to exclude from the saved configuration
            **kwargs: Additional parameters for saving

        Returns:
            str: The path where the configuration was saved
        """
        return super().save_module(path=path, ignore=ignore, **kwargs)

    @classmethod
    def from_file(cls, path: str, llm_config: OpenAILLMConfig, storage_handler: Optional[StorageHandler]=None, rag_config: Optional[RAGConfig]=None, **kwargs) -> 'MemoryAgent':
        """
        Load a MemoryAgent from a JSON configuration file.

        Args:
            path: Path to the JSON configuration file
            llm_config: LLM configuration
            storage_handler: Optional storage handler
            rag_config: Optional RAG configuration
            **kwargs: Additional parameters

        Returns:
            MemoryAgent: The loaded agent instance
        """
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return cls(name=config.get('name', 'MemoryAgent'), description=config.get('description', 'An agent that uses long-term memory'), llm_config=llm_config, storage_handler=storage_handler, rag_config=rag_config, system_prompt=config.get('system_prompt'), prompt=config.get('prompt'), use_long_term_memory=config.get('use_long_term_memory', True), **kwargs)

def save_module(self, path: str, ignore: List[str]=['llm', 'llm_config', 'memory_manager'], **kwargs) -> str:
    """
        Save the agent's configuration to a JSON file, excluding memory_manager by default.

        Args:
            path: File path to save the configuration
            ignore: List of keys to exclude from the saved configuration
            **kwargs: Additional parameters for saving

        Returns:
            str: The path where the configuration was saved
        """
    return super().save_module(path=path, ignore=ignore, **kwargs)

class AgentManager(BaseModule):
    """
    Responsible for creating and managing all Agent objects required for workflow operation.

    Attributes:
        storage_handler (StorageHandler): Used to load and save agents from/to storage.
        agents (List[Agent]): A list to keep track of all managed Agent instances.
        agent_states (Dict[str, AgentState]): A dictionary to track the state of each Agent by name.
    """
    agents: List[Agent] = Field(default_factory=list)
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)
    storage_handler: Optional[StorageHandler] = None
    tools: Optional[List[Union[Toolkit, Tool]]] = None

    def init_module(self):
        self._lock = threading.Lock()
        self._state_conditions = {}
        if self.agents:
            for agent in self.agents:
                self.agent_states[agent.name] = self.agent_states.get(agent.name, AgentState.AVAILABLE)
                if agent.name not in self._state_conditions:
                    self._state_conditions[agent.name] = threading.Condition()
            self.check_agents()

    def check_agents(self):
        """Validate agent list integrity and state consistency.
        
        Performs thorough validation of the agent manager's internal state:
        1. Checks for duplicate agent names
        2. Verifies that agent states exist for all agents
        3. Ensures agent list and state dictionary sizes match
        """
        duplicate_agent_names = self.find_duplicate_agents(self.agents)
        if duplicate_agent_names:
            raise ValueError(f'The agents should be unique. Found duplicate agent names: {duplicate_agent_names}!')
        if len(self.agents) != len(self.agent_states):
            raise ValueError(f'The lengths of self.agents ({len(self.agents)}) and self.agent_states ({len(self.agent_states)}) are different!')
        missing_agents = self.find_missing_agent_states()
        if missing_agents:
            raise ValueError(f"The following agents' states were not found: {missing_agents}")

    def find_duplicate_agents(self, agents: List[Agent]) -> List[str]:
        unique_agent_names = set()
        duplicate_agent_names = set()
        for agent in agents:
            agent_name = agent.name
            if agent_name in unique_agent_names:
                duplicate_agent_names.add(agent_name)
            unique_agent_names.add(agent_name)
        return list(duplicate_agent_names)

    def find_missing_agent_states(self):
        missing_agents = [agent.name for agent in self.agents if agent.name not in self.agent_states]
        return missing_agents

    def list_agents(self) -> List[str]:
        return [agent.name for agent in self.agents]

    def has_agent(self, agent_name: str) -> bool:
        """Check if an agent with the given name exists in the manager.
        
        Args:
            agent_name: The name of the agent to check
            
        Returns:
            True if an agent with the given name exists, False otherwise
        """
        all_agent_names = self.list_agents()
        return agent_name in all_agent_names

    @property
    def size(self):
        """
        Get the total number of agents managed by this manager.
        """
        return len(self.agents)

    def load_agent(self, agent_name: str, **kwargs) -> Agent:
        """Load an agent from local storage through storage_handler.
        
        Retrieves agent data from storage and creates an Agent instance.
        
        Args:
            agent_name: The name of the agent to load
            **kwargs (Any): Additional parameters for agent creation
        
        Returns:
            Agent instance with data loaded from storage
        """
        if not self.storage_handler:
            raise ValueError('must provide ``self.storage_handler`` to use ``load_agent``')
        agent_data = self.storage_handler.load_agent(agent_name=agent_name)
        agent: Agent = self.create_customize_agent(agent_data=agent_data)
        return agent

    def load_all_agents(self, **kwargs):
        """Load all agents from storage and add them to the manager.
        
        Retrieves all available agents from storage and adds them to the
        managed agents collection.
        
        Args:
            **kwargs (Any): Additional parameters passed to storage handler
        """
        pass

    def update_tools(self, agent_data: dict) -> None:
        """
        Update agent_data with tools based on tool_names.
        
        Handles four scenarios:
        1. Neither tool_names nor tools exist: return directly
        2. Only tool_names exists: resolve tool_names to tools and set tools field
        3. Only tools exists: return directly (no action needed)
        4. Both exist: merge tool_names into existing tools (skip duplicates)
        
        Args:
            agent_data (dict): Agent configuration dictionary that may contain 'tool_names' and/or 'tools'
            
        Raises:
            ValueError: If tool_names exist but self.tools is None, or if requested tools are not found
        """
        tool_names = agent_data.get('tool_names', None)
        existing_tools = agent_data.get('tools', None)
        if not tool_names and (not existing_tools):
            return
        if not tool_names and existing_tools:
            return
        if self.tools is None:
            raise ValueError(f'Agent requires tools {tool_names}, but no tools are available in AgentManager. Please set self.tools before creating agents with tool_names.')
        tool_mapping = {}
        for tool in self.tools:
            tool_mapping[tool.name] = tool
        if tool_names and (not existing_tools):
            existing_tools = []
        if tool_names:
            existing_tool_names = {tool.name for tool in existing_tools}
            tools_to_add = []
            missing_tools = []
            for tool_name in tool_names:
                if tool_name in existing_tool_names:
                    continue
                if tool_name in tool_mapping:
                    tools_to_add.append(tool_mapping[tool_name])
                else:
                    missing_tools.append(tool_name)
            if missing_tools:
                available_tools = list(tool_mapping.keys())
                raise ValueError(f'The following tools are not available: {missing_tools}. Available tools: {available_tools}')
            if tools_to_add:
                agent_data['tools'] = list(existing_tools) + tools_to_add

    def create_customize_agent(self, agent_data: dict, llm_config: Optional[Union[LLMConfig, dict]]=None, **kwargs) -> CustomizeAgent:
        """
        create a customized agent from the provided `agent_data`. 

        Args:
            agent_data: The data used to create an Agent instance, must contain 'name', 'description' and 'prompt' keys.
            llm_config (Optional[LLMConfig]): The LLM configuration to be used for the agent. 
                It will be used as the default LLM for agents without a `llm_config` key. 
                If not provided, the `agent_data` should contain a `llm_config` key. 
                If provided and `agent_data` contains a `llm_config` key, the `llm_config` in `agent_data` will be used.  
            **kwargs (Any): Additional parameters for agent creation
        
        Returns:
            Agent: the instantiated agent instance.
        """
        agent_data = deepcopy(agent_data)
        agent_llm_config = agent_data.get('llm_config', llm_config)
        if not agent_data.get('is_human', False) and (not agent_llm_config):
            raise ValueError('`agent_data` should contain a `llm_config` key or `llm_config` should be provided.')
        if agent_llm_config:
            if isinstance(agent_llm_config, dict):
                agent_data['llm_config'] = agent_llm_config
            elif isinstance(agent_llm_config, LLMConfig):
                agent_data['llm_config'] = agent_llm_config.to_dict()
        self.update_tools(agent_data=agent_data)
        return CustomizeAgent.from_dict(data=agent_data)

    def get_agent_name(self, agent: Union[str, dict, Agent]) -> str:
        """Extract agent name from different agent representations.
        
        Handles different ways to specify an agent (string name, dictionary, or
        Agent instance) and extracts the agent name.
        
        Args:
            agent: Agent specified as a string name, dictionary with 'name' key,
                  or Agent instance
                  
        Returns:
            The extracted agent name as a string
        """
        if isinstance(agent, str):
            agent_name = agent
        elif isinstance(agent, dict):
            agent_name = agent['name']
        elif isinstance(agent, Agent):
            agent_name = agent.name
        else:
            raise ValueError(f'{type(agent)} is not a supported type for ``get_agent_name``. Supported types: [str, dict, Agent].')
        return agent_name

    def create_agent(self, agent: Union[str, dict, Agent], llm_config: Optional[LLMConfig]=None, **kwargs) -> Agent:
        if isinstance(agent, str):
            if self.storage_handler is None:
                if not self.has_agent(agent_name=agent):
                    raise ValueError(f'Agent ``{agent}`` does not exist! You should provide a dictionary or an Agent instance when ``self.storage_handler`` is not provided.')
                return self.get_agent(agent_name=agent)
            else:
                agent_instance = self.load_agent(agent_name=agent)
        elif isinstance(agent, dict):
            if not agent.get('is_human', False) and (llm_config is None and 'llm_config' not in agent):
                raise ValueError("When providing an agent as a dictionary, you must either include 'llm_config' in the dictionary or provide it as a parameter.")
            agent_instance = self.create_customize_agent(agent_data=agent, llm_config=llm_config, **kwargs)
        elif isinstance(agent, Agent):
            agent_instance = agent
        else:
            raise ValueError(f'{type(agent)} is not a supported input type of ``create_agent``. Supported types: [str, dict, Agent].')
        return agent_instance

    @atomic_method
    def add_agent(self, agent: Union[str, dict, Agent], llm_config: Optional[LLMConfig]=None, **kwargs):
        """
        add a single agent, ignore if the agent already exists (judged by the name of an agent).

        Args:
            agent: The agent to be added, specified as:
                - String: Agent name to load from storage
                - Dictionary: Agent specification to create a CustomizeAgent
                - Agent: Existing Agent instance to add directly
            llm_config (Optional[LLMConfig]): The LLM configuration to be used for the agent. Only used when the `agent` is a dictionary, used to create a CustomizeAgent. 
            **kwargs (Any): Additional parameters for agent creation
        """
        agent_name = self.get_agent_name(agent=agent)
        if self.has_agent(agent_name=agent_name):
            return
        agent_instance = self.create_agent(agent=agent, llm_config=llm_config, **kwargs)
        self.agents.append(agent_instance)
        self.agent_states[agent_instance.name] = AgentState.AVAILABLE
        if agent_instance.name not in self._state_conditions:
            self._state_conditions[agent_instance.name] = threading.Condition()
        self.check_agents()

    def add_agents(self, agents: List[Union[str, dict, Agent]], llm_config: Optional[LLMConfig]=None, **kwargs):
        """
        add several agents by using self.add_agent().
        """
        for agent in agents:
            self.add_agent(agent=agent, llm_config=llm_config, **kwargs)

    def add_agents_from_workflow(self, workflow_graph, llm_config: Optional[LLMConfig]=None, **kwargs):
        """
        Initialize agents from the nodes of a given WorkFlowGraph and add these agents to self.agents. 

        Args:
            workflow_graph (WorkFlowGraph): The workflow graph containing nodes with agents information.
            llm_config (Optional[LLMConfig]): The LLM configuration to be used for the agents.
            **kwargs (Any): Additional parameters passed to add_agent
        """
        from ..workflow.workflow_graph import WorkFlowGraph
        if not isinstance(workflow_graph, WorkFlowGraph):
            raise TypeError('workflow_graph must be an instance of WorkFlowGraph')
        for node in workflow_graph.nodes:
            if node.agents:
                for agent in node.agents:
                    self.add_agent(agent=agent, llm_config=llm_config, **kwargs)

    def update_agents_from_workflow(self, workflow_graph, llm_config: Optional[LLMConfig]=None, **kwargs):
        """
        Update agents from a given WorkFlowGraph.

        Args:
            workflow_graph (WorkFlowGraph): The workflow graph containing nodes with agents information.
            llm_config (Optional[LLMConfig]): The LLM configuration to be used for the agents.
            **kwargs: Additional parameters passed to update_agent
        """
        from ..workflow.workflow_graph import WorkFlowGraph
        if not isinstance(workflow_graph, WorkFlowGraph):
            raise TypeError('workflow_graph must be an instance of WorkFlowGraph')
        for node in workflow_graph.nodes:
            if node.agents:
                for agent in node.agents:
                    agent_name = self.get_agent_name(agent=agent)
                    if self.has_agent(agent_name=agent_name):
                        agent_llm_config = self.get_agent(agent_name).llm_config
                        self.update_agent(agent=agent, llm_config=agent_llm_config, **kwargs)
                    else:
                        self.add_agent(agent=agent, llm_config=llm_config, **kwargs)

    def get_agent(self, agent_name: str, **kwargs) -> Agent:
        """Retrieve an agent by its name from managed agents.
        
        Searches the list of managed agents for an agent with the specified name.
        
        Args:
            agent_name: The name of the agent to retrieve
            **kwargs (Any): Additional parameters (unused)
            
        Returns:
            The Agent instance with the specified name
        """
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        raise ValueError(f'Agent ``{agent_name}`` does not exists!')

    def update_agent(self, agent: Union[dict, Agent], llm_config: Optional[LLMConfig]=None, **kwargs):
        """
        Update an agent in the manager.

        Args:
            agent: The agent to be updated, specified as:
                - Dictionary: Agent specification to update a CustomizeAgent
                - Agent: Existing Agent instance to update
            llm_config (Optional[LLMConfig]): The LLM configuration to be used for the agent.
        """
        agent_name = self.get_agent_name(agent=agent)
        self.remove_agent(agent_name=agent_name)
        self.add_agent(agent=agent, llm_config=llm_config, **kwargs)

    @atomic_method
    def remove_agent(self, agent_name: str, remove_from_storage: bool=False, **kwargs):
        """
        Remove an agent from the manager and optionally from storage.
        
        Args:
            agent_name: The name of the agent to remove
            remove_from_storage: If True, also remove the agent from storage
            **kwargs (Any): Additional parameters passed to storage_handler.remove_agent
        """
        self.agents = [agent for agent in self.agents if agent.name != agent_name]
        self.agent_states.pop(agent_name, None)
        self._state_conditions.pop(agent_name, None)
        if remove_from_storage:
            self.storage_handler.remove_agent(agent_name=agent_name, **kwargs)
        self.check_agents()

    def get_agent_state(self, agent_name: str) -> AgentState:
        """
        Get the state of a specific agent by its name.

        Args:
            agent_name: The name of the agent.

        Returns:
            AgentState: The current state of the agent.
        """
        return self.agent_states[agent_name]

    @atomic_method
    def set_agent_state(self, agent_name: str, new_state: AgentState) -> bool:
        """
        Changes an agent's state and notifies any threads waiting on that agent's state.
        Thread-safe operation for coordinating multi-threaded agent execution.
        
        Args:
            agent_name: The name of the agent
            new_state: The new state to set
        
        Returns:
            True if the state was updated successfully, False otherwise
        """
        if agent_name in self.agent_states and isinstance(new_state, AgentState):
            if agent_name not in self._state_conditions:
                self._state_conditions[agent_name] = threading.Condition()
            with self._state_conditions[agent_name]:
                self.agent_states[agent_name] = new_state
                self._state_conditions[agent_name].notify_all()
            return True
        return False

    def get_all_agent_states(self) -> Dict[str, AgentState]:
        """Get the states of all managed agents.

        Returns:
            Dict[str, AgentState]: A dictionary mapping agent names to their states.
        """
        return self.agent_states

    @atomic_method
    def save_all_agents(self, **kwargs):
        """Save all managed agents to persistent storage.
                
        Args:
            **kwargs (Any): Additional parameters passed to the storage handler
        """
        pass

    @atomic_method
    def clear_agents(self):
        """
        Remove all agents from the manager.
        """
        self.agents = []
        self.agent_states = {}
        self._state_conditions = {}
        self.check_agents()

    def wait_for_agent_available(self, agent_name: str, timeout: Optional[float]=None) -> bool:
        """Wait for an agent to be available.
        
        Args:
            agent_name: The name of the agent to wait for
            timeout: Maximum time to wait in seconds, or None to wait indefinitely
            
        Returns:
            True if the agent became available, False if timed out
        """
        if agent_name not in self._state_conditions:
            self._state_conditions[agent_name] = threading.Condition()
        condition = self._state_conditions[agent_name]
        with condition:
            return condition.wait_for(lambda: self.agent_states.get(agent_name) == AgentState.AVAILABLE, timeout=timeout)

    def copy(self) -> 'AgentManager':
        """
        Create a shallow copy of the AgentManager.
        """
        return AgentManager(agents=self.agents, storage_handler=self.storage_handler)

def copy(self) -> 'AgentManager':
    """
        Create a shallow copy of the AgentManager.
        """
    return AgentManager(agents=self.agents, storage_handler=self.storage_handler)

class Agent(BaseModule):
    """
    Base class for all agents. 
    
    Attributes:
        name (str): Unique identifier for the agent
        description (str): Human-readable description of the agent's purpose
        llm_config (Optional[LLMConfig]): Configuration for the language model. If provided, a new LLM instance will be created. 
            Otherwise, the existing LLM instance specified in the `llm` field will be used.   
        llm (Optional[BaseLLM]): Language model instance. If provided, the existing LLM instance will be used. 
        agent_id (Optional[str]): Unique ID for the agent, auto-generated if not provided
        system_prompt (Optional[str]): System prompt for the Agent.
        actions (List[Action]): List of available actions
        n (Optional[int]): Number of latest messages used to provide context for action execution. It uses all the messages in short term memory by default. 
        is_human (bool): Whether this agent represents a human user
        version (int): Version number of the agent, default is 0. 
    """
    name: str
    description: str
    llm_config: Optional[LLMConfig] = None
    llm: Optional[BaseLLM] = None
    agent_id: Optional[str] = Field(default_factory=generate_id)
    system_prompt: Optional[str] = None
    short_term_memory: Optional[ShortTermMemory] = Field(default_factory=ShortTermMemory)
    use_long_term_memory: Optional[bool] = False
    storage_handler: Optional[StorageHandler] = None
    long_term_memory: Optional[LongTermMemory] = None
    long_term_memory_manager: Optional[MemoryManager] = None
    actions: List[Action] = Field(default=None)
    n: int = Field(default=None, description='number of latest messages used to provide context for action execution. It uses all the messages in short term memory by default.')
    is_human: bool = Field(default=False)
    version: int = 0

    def init_module(self):
        if not self.is_human:
            self.init_llm()
        if self.use_long_term_memory:
            self.init_long_term_memory()
        self.actions = [] if self.actions is None else self.actions
        self._action_map = {action.name: action for action in self.actions} if self.actions else dict()
        self._save_ignore_fields = ['llm', 'llm_config']
        self.init_context_extractor()

    def __call__(self, *args: Any, **kwargs: Any) -> Union[dict, Coroutine[Any, Any, dict]]:
        """Make the operator callable and automatically choose between sync and async execution."""
        try:
            asyncio.get_running_loop()
            return self.async_execute(*args, **kwargs)
        except RuntimeError:
            return self.execute(*args, **kwargs)

    def _prepare_execution(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[dict]=None, **kwargs) -> Tuple[Action, dict]:
        """Prepare for action execution by updating memory and getting inputs.
        
        Helper method used by both execute and aexecute methods.
        
        Args:
            action_name: The name of the action to execute
            msgs: Optional list of messages providing context for the action
            action_input_data: Optional pre-extracted input data for the action
            **kwargs: Additional workflow parameters
            
        Returns:
            Tuple containing the action object and input data
            
        Raises:
            AssertionError: If neither msgs nor action_input_data is provided
        """
        assert msgs is not None or action_input_data is not None, 'must provide either `msgs` or `action_input_data`'
        action = self.get_action(action_name=action_name)
        if msgs is not None:
            self.short_term_memory.add_messages(msgs)
        if action_input_data is not None:
            input_message = Message(content=action_input_data, next_actions=[action_name], msg_type=MessageType.INPUT, wf_goal=kwargs.get('wf_goal', None), wf_task=kwargs.get('wf_task', None), wf_task_desc=kwargs.get('wf_task_desc', None))
            self.short_term_memory.add_message(input_message)
        action_input_data = action_input_data or self.get_action_inputs(action=action)
        return (action, action_input_data)

    def _create_output_message(self, action_output, prompt: str, action_name: str, return_msg_type: Optional[MessageType]=MessageType.UNKNOWN, **kwargs) -> Message:
        """Create a message from execution results and update memory.
        
        Helper method used by both execute and aexecute methods.
        
        Args:
            action_output: The output from action execution
            prompt: The prompt used for execution
            action_name: The name of the executed action
            return_msg_type: Message type for the return message
            **kwargs: Additional workflow parameters
            
        Returns:
            Message object containing execution results
        """
        message = Message(content=action_output, agent=self.name, action=action_name, prompt=prompt, msg_type=return_msg_type, wf_goal=kwargs.get('wf_goal', None), wf_task=kwargs.get('wf_task', None), wf_task_desc=kwargs.get('wf_task_desc', None))
        self.short_term_memory.add_message(message)
        return message

    async def async_execute(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[dict]=None, return_msg_type: Optional[MessageType]=MessageType.UNKNOWN, return_action_input_data: Optional[bool]=False, **kwargs) -> Union[Message, Tuple[Message, dict]]:
        """Execute an action asynchronously with the given context and return results.

        This is the async version of the execute method, allowing it to perform actions
        based on the current conversation context.

        Args:
            action_name: The name of the action to execute
            msgs: Optional list of messages providing context for the action
            action_input_data: Optional pre-extracted input data for the action
            return_msg_type: Message type for the return message
            **kwargs (Any): Additional parameters, may include workflow information
        
        Returns:
            Message: A message containing the execution results
        """
        action, action_input_data = self._prepare_execution(action_name=action_name, msgs=msgs, action_input_data=action_input_data, **kwargs)
        async_execute_source = inspect.getsource(action.async_execute)
        if 'NotImplementedError' in async_execute_source:
            execution_results = action.execute(llm=self.llm, inputs=action_input_data, sys_msg=self.system_prompt, return_prompt=True, **kwargs)
        else:
            execution_results = await action.async_execute(llm=self.llm, inputs=action_input_data, sys_msg=self.system_prompt, return_prompt=True, **kwargs)
        action_output, prompt = execution_results
        message = self._create_output_message(action_output=action_output, prompt=prompt, action_name=action_name, return_msg_type=return_msg_type, **kwargs)
        if return_action_input_data:
            return (message, action_input_data)
        return message

    def execute(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[dict]=None, return_msg_type: Optional[MessageType]=MessageType.UNKNOWN, return_action_input_data: Optional[bool]=False, **kwargs) -> Union[Message, Tuple[Message, dict]]:
        """Execute an action with the given context and return results.

        This is the core method for agent functionality, allowing it to perform actions
        based on the current conversation context.

        Args:
            action_name: The name of the action to execute
            msgs: Optional list of messages providing context for the action
            action_input_data: Optional pre-extracted input data for the action
            return_msg_type: Message type for the return message
            **kwargs (Any): Additional parameters, may include workflow information
        
        Returns:
            Message: A message containing the execution results
        """
        action, action_input_data = self._prepare_execution(action_name=action_name, msgs=msgs, action_input_data=action_input_data, **kwargs)
        execution_results = action.execute(llm=self.llm, inputs=action_input_data, sys_msg=self.system_prompt, return_prompt=True, **kwargs)
        action_output, prompt = execution_results
        message = self._create_output_message(action_output=action_output, prompt=prompt, action_name=action_name, return_msg_type=return_msg_type, **kwargs)
        if return_action_input_data:
            return (message, action_input_data)
        return message

    def init_llm(self):
        """
        Initialize the language model for the agent.
        """
        if not self.is_human and (not self.llm_config and (not self.llm)):
            raise ValueError('must provide `llm_config` or `llm` when `is_human` is False')
        if not self.is_human and (self.llm_config or self.llm):
            if self.llm_config and (not self.llm):
                llm_cls = MODEL_REGISTRY.get_model(self.llm_config.llm_type)
                self.llm = llm_cls(config=self.llm_config)
            if self.llm:
                self.llm_config = self.llm.config

    def init_long_term_memory(self):
        """
        Initialize long-term memory components.
        """
        assert self.storage_handler is not None, 'must provide ``storage_handler`` when use_long_term_memory=True'
        if not self.long_term_memory:
            self.long_term_memory = LongTermMemory()
        if not self.long_term_memory_manager:
            self.long_term_memory_manager = MemoryManager(storage_handler=self.storage_handler, memory=self.long_term_memory)

    def init_context_extractor(self):
        """
        Initialize the context extraction action.
        """
        cext_action = ContextExtraction()
        self.cext_action_name = cext_action.name
        self.add_action(cext_action)

    def add_action(self, action: Type[Action]):
        """
        Add a new action to the agent's available actions.

        Args:
            action: The action instance to add
        """
        action_name = action.name
        if action_name in self._action_map:
            return
        self.actions.append(action)
        self._action_map[action_name] = action

    def check_action_name(self, action_name: str):
        """
        Check if an action name is valid for this agent.
                
        Args:
            action_name: Name of the action to check
        """
        if action_name not in self._action_map:
            raise KeyError(f"'{action_name}' is an invalid action for {self.name}! Available action names: {list(self._action_map.keys())}")

    def get_action(self, action_name: str) -> Action:
        """
        Retrieves the Action instance associated with the given name.
        
        Args:
            action_name: Name of the action to retrieve
            
        Returns:
            The Action instance with the specified name
        """
        self.check_action_name(action_name=action_name)
        return self._action_map[action_name]

    def get_action_name(self, action_cls: Type[Action]) -> str:
        """
        Searches through the agent's actions to find one matching the specified type.
        
        Args:
            action_cls: The Action class type to search for
            
        Returns:
            The name of the matching action
        """
        for name, action in self._action_map.items():
            if isinstance(action, action_cls):
                return name
        raise ValueError(f"Couldn't find an action that matches Type '{action_cls.__name__}'")

    def get_action_inputs(self, action: Action) -> Union[dict, None]:
        """
        Uses the context extraction action to determine appropriate inputs
        for the specified action based on the conversation history.
        
        Args:
            action: The action for which to extract inputs
            
        Returns:
            Dictionary of extracted input data, or None if extraction fails
        """
        context = self.short_term_memory.get(n=self.n)
        cext_action = self.get_action(self.cext_action_name)
        action_inputs = cext_action.execute(llm=self.llm, action=action, context=context)
        return action_inputs

    def get_all_actions(self) -> List[Action]:
        """Get all actions except the context extraction action.
        
        Returns:
            List of Action instances available for execution
        """
        actions = [action for action in self.actions if action.name != self.cext_action_name]
        return actions

    def get_agent_profile(self, action_names: List[str]=None) -> str:
        """Generate a human-readable profile of the agent and its capabilities.
        
        Args:
            action_names: Optional list of action names to include in the profile.
                          If None, all actions are included.
            
        Returns:
            A formatted string containing the agent profile
        """
        all_actions = self.get_all_actions()
        if action_names is None:
            action_descriptions = '\n'.join([f'  - {action.name}: {action.description}' for action in all_actions])
        else:
            action_descriptions = '\n'.join([f'  - {action.name}: {action.description}' for action in all_actions if action.name in action_names])
        profile = f'Agent Name: {self.name}\nDescription: {self.description}\nAvailable Actions:\n{action_descriptions}'
        return profile

    def clear_short_term_memory(self):
        """
        Remove all content from the agent's short-term memory.
        """
        pass

    def __eq__(self, other: 'Agent'):
        return self.agent_id == other.agent_id

    def __hash__(self):
        return self.agent_id

    def get_prompts(self) -> dict:
        """
        Get all the prompts of the agent.
        
        Returns:
            dict: A dictionary with keys in the format 'agent_name::action_name' and values
                containing the system_prompt and action prompt.
        """
        prompts = {}
        for action in self.get_all_actions():
            prompts[action.name] = {'system_prompt': self.system_prompt, 'prompt': action.prompt}
        return prompts

    def set_prompt(self, action_name: str, prompt: str, system_prompt: Optional[str]=None) -> bool:
        """
        Set the prompt for a specific action of this agent.
        
        Args:
            action_name: Name of the action whose prompt should be updated
            prompt: New prompt text to set for the action
            system_prompt: Optional new system prompt to set for the agent
            
        Returns:
            bool: True if the prompt was successfully updated, False otherwise
            
        Raises:
            KeyError: If the action_name does not exist for this agent
        """
        try:
            action = self.get_action(action_name)
            action.prompt = prompt
            if system_prompt is not None:
                self.system_prompt = system_prompt
            return True
        except KeyError:
            raise KeyError(f"Action '{action_name}' not found in agent '{self.name}'")

    def set_prompts(self, prompts: dict) -> bool:
        """
        Set the prompts for all actions of this agent.
        
        Args:
            prompts: A dictionary with keys in the format 'action_name' and values
                containing the system_prompt and action prompt.
        
        Returns:
            bool: True if the prompts were successfully updated, False otherwise
        """
        for action_name, prompt_data in prompts.items():
            if not isinstance(prompt_data, dict):
                raise ValueError(f"Invalid prompt data for action '{action_name}'. Expected a dictionary with 'prompt' and 'system_prompt' (optional) keys.")
            if 'prompt' not in prompt_data:
                raise ValueError(f"Missing 'prompt' key in prompt data for action '{action_name}'.")
            self.set_prompt(action_name, prompt_data['prompt'], prompt_data.get('system_prompt', None))
        return True

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """Save the agent to persistent storage.
                
        Args:
            path: Path where the agent should be saved
            ignore: List of field names to exclude from serialization
            **kwargs (Any): Additional parameters for the save operation
            
        Returns:
            The path where the agent was saved
        """
        ignore_fields = self._save_ignore_fields + ignore
        super().save_module(path=path, ignore=ignore_fields, **kwargs)

    @classmethod
    def load_module(cls, path: str, llm_config: LLMConfig=None, **kwargs) -> 'Agent':
        """
        load the agent from local storage. Must provide `llm_config` when loading the agent from local storage. 

        Args:
            path: The path of the file
            llm_config: The LLMConfig instance
        
        Returns:
            Agent: The loaded agent instance
        """
        agent = super().load_module(path=path, **kwargs)
        if llm_config is not None:
            agent['llm_config'] = llm_config.to_dict()
        return agent

    def get_config(self) -> dict:
        """
        Get a dictionary containing all necessary configuration to recreate this agent.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new Agent instance
            with the same properties as this one.
        """
        config = self.to_dict()
        return config

def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
    """Save the agent to persistent storage.
                
        Args:
            path: Path where the agent should be saved
            ignore: List of field names to exclude from serialization
            **kwargs (Any): Additional parameters for the save operation
            
        Returns:
            The path where the agent was saved
        """
    ignore_fields = self._save_ignore_fields + ignore
    super().save_module(path=path, ignore=ignore_fields, **kwargs)

def default_llm_config():
    """
    Create default LLM configuration. Uses MockLLM in testing environments 
    or when OPENAI_API_KEY is not available.
    """
    is_testing = os.getenv('PYTEST_CURRENT_TEST') is not None or os.getenv('CI') is not None or OPENAI_API_KEY is None or (OPENAI_API_KEY.strip() == '')
    if is_testing:
        mock_config = MockLLMConfig(llm_type='MockLLM', model='mock-model', output_response=True)
        return MockLLM(mock_config)
    else:
        llm_config = OpenAILLMConfig(model='gpt-4o', openai_key=OPENAI_API_KEY, stream=True, output_response=True)
        return OpenAILLM(llm_config)

class HITLOutsideConversationAction(Action):
    """HITL Outside Conversation Action - support the conversation loop to modify the workflow json structure"""

    def __init__(self, name: str='HITLOutsideConversationAction', description: str='support the conversation loop to modify the workflow json structure', **kwargs):
        super().__init__(name=name, description=description, **kwargs)

    def execute(self, llm: BaseLLM, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        """synchronous execution entry"""
        try:
            loop = asyncio.get_running_loop()
            if loop:
                pass
            raise RuntimeError('Cannot use asyncio.run() in async context. Use async_execute directly.')
        except RuntimeError:
            return asyncio.run(self.async_execute(llm, inputs, hitl_manager, sys_msg=sys_msg, **kwargs))

    async def async_execute(self, llm: BaseLLM, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        """
        WorkFlow asynchronously execute the conversation loop to modify the workflow json structure
        Parameters:
            llm: the LLM model
            inputs: the input parameters
            hitl_manager: the HITLManager instance
            sys_msg: the system message
            **kwargs: the additional parameters
        Returns:
            result: the result of the conversation loop, with structure:
                {
                    "final_workflow": the final workflow instance,
                    "workflow_json": the final workflow json structure,
                    "hitl_decision": the HITLDecision of the conversation loop
                }
            prompt: the prompt of the conversation loop
        """
        workflow_json_path = inputs.get('workflow_json_path')
        existing_workflow = inputs.get('existing_workflow')
        workflow_json = None
        if workflow_json_path:
            workflow_json = self._load_workflow_info_from_json(workflow_json_path)
        elif existing_workflow:
            workflow_json = self._convert_workflow_to_json(existing_workflow)
        else:
            raise ValueError('must provide the workflow_json_path or existing_workflow parameter')
        workflow_json = await self._conversation_loop(llm, workflow_json, hitl_manager, **kwargs)
        final_workflow = self._instantiate_workflow(workflow_json, llm)
        result = {'final_workflow': final_workflow, 'workflow_json': workflow_json, 'hitl_decision': HITLDecision.CONTINUE}
        prompt = 'WorkFlow conversation loop finished'
        return (result, prompt)

    def _load_workflow_info_from_json(self, json_path: str) -> Any:
        """load the workflow info from the json file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'load the workflow info from the json file failed: {e}')
            raise

    def _convert_workflow_to_json(self, workflow) -> Any:
        """convert the workflow to json"""
        try:
            from ..workflow.workflow import WorkFlow
            if not isinstance(workflow, WorkFlow):
                raise TypeError('Expected WorkFlow instance')
            return workflow.graph.to_dict()
        except Exception as e:
            logger.error(f'convert the workflow to json failed: {e}')
            raise

    async def _conversation_loop(self, llm: BaseLLM, workflow_json: Dict[str, Any], hitl_manager: HITLManager, **kwargs) -> Dict[str, Any]:
        """simplified conversation loop - use GUI editor"""
        if not hitl_manager.is_active:
            raise ValueError('HITLManager is not active, please activate the HITLManager first')
        print('\n🎯 WorkFlow JSON editor')
        print('=' * 50)
        original_workflow_json = workflow_json
        while True:
            try:
                workflow_instance = self._instantiate_workflow(workflow_json, llm)
                del workflow_instance
                print('✅ WorkFlow structure validation successful!')
                print('\nplease choose the operation:')
                print('1. 📝 open the GUI editor(still in development)')
                print('2. 🤖 use the LLM to optimize')
                print('3. 📋 view the current JSON')
                print('4. ✅ finish the edit')
                print('5. ❌ exit')
                print('6. 🔄 reload the original JSON')
                choice = input('\nplease choose (1-5): ').strip()
                if choice == '1':
                    print('🚀 opening the GUI editor...')
                    editor = WorkFlowJSONEditorGUI(workflow_json)
                    edited_json = editor.edit_json()
                    if edited_json is not None:
                        workflow_json = edited_json
                        print('✅ JSON updated')
                    else:
                        print('❌ edit cancelled')
                elif choice == '2':
                    user_advice = input('please input the optimization advice (type q to cancel): ').strip()
                    if user_advice == 'q':
                        continue
                    workflow_json = await self._llm_optimize_workflow(llm, workflow_json, user_advice if user_advice else None)
                elif choice == '3':
                    print('\n📋 current JSON structure:')
                    print(json.dumps(workflow_json, indent=2, ensure_ascii=False))
                elif choice == '4':
                    print('✅ edit finished')
                    break
                elif choice == '5':
                    print('❌ exit the edit')
                    sys.exit()
                elif choice == '6':
                    workflow_json = original_workflow_json
                    print('✅ reload the original data')
                else:
                    print('❌ invalid choice, please try again')
            except Exception as e:
                print(f'❌ WorkFlow structure validation failed: {e}')
                print('please fix the JSON structure and try again')
                print('\nrepair options:')
                print('1. 📝 open the GUI editor to fix')
                print('2. 🔄 reload the original JSON')
                print('3. ❌ exit')
                fix_choice = input('please choose (1-3): ').strip()
                if fix_choice == '1':
                    editor = WorkFlowJSONEditorGUI(workflow_json)
                    edited_json = editor.edit_json()
                    if edited_json is not None:
                        workflow_json = edited_json
                elif fix_choice == '2':
                    workflow_json = original_workflow_json
                    print('⚠️ reload the original data')
                elif fix_choice == '3':
                    sys.exit()
        return workflow_json

    async def _llm_optimize_workflow(self, llm: BaseLLM, workflow_json: Dict[str, Any], user_advice: str=None) -> Dict[str, Any]:
        """let the LLM optimize the workflow structure"""
        print('🤖 let the LLM optimize the workflow structure...')
        optimization_prompt = f"\n        analyze the workflow and optimize it according to the user's advice and make it more reasonable and efficient, make sure to keep the original key of the json dict,and the original structure of the json dict:\n\n        current workflow structure:\n        {json.dumps(workflow_json, indent=2, ensure_ascii=False)}\n\n        user's advice:\n        {user_advice}\n\n        after the user's advice, please consider the following rules:\n        1. the description of the node is clear\n        2. the input and output parameters are reasonable\n        3. the dependency relationship between the nodes is correct\n        4. whether some nodes can be merged or split\n\n        please return the optimized json structure, keep the original format.\n        "
        messages = [{'role': 'system', 'content': 'You are a helpful assistant that can optimize the workflow json structure.'}, {'role': 'user', 'content': optimization_prompt}]
        try:
            response = await llm.single_generate_async(messages=messages, response_format={'type': 'json_object'})
            optimized_json = json.loads(response)
            print('✅ LLM optimization finished')
            return optimized_json
        except Exception as e:
            print(f'❌ LLM optimization failed: {e}')
            return workflow_json

    def _instantiate_workflow(self, workflow_json: Dict[str, Any], llm) -> Any:
        """try to instantiate the workflow"""
        try:
            from ..workflow.workflow import WorkFlow
            from ..workflow.workflow_graph import WorkFlowGraph
            graph = WorkFlowGraph.from_dict(workflow_json)
            workflow = WorkFlow(graph=graph, llm=llm)
            return workflow
        except Exception as e:
            logger.error(f'WorkFlow instantiation failed: {e}')
            raise

def _instantiate_workflow(self, workflow_json: Dict[str, Any], llm) -> Any:
    """try to instantiate the workflow"""
    try:
        from ..workflow.workflow import WorkFlow
        from ..workflow.workflow_graph import WorkFlowGraph
        graph = WorkFlowGraph.from_dict(workflow_json)
        workflow = WorkFlow(graph=graph, llm=llm)
        return workflow
    except Exception as e:
        logger.error(f'WorkFlow instantiation failed: {e}')
        raise

class Operator(BaseModule):
    name: str = Field(description='The name of the operator.')
    description: str = Field(description='The description of the operator.')
    llm: BaseLLM = Field(description='The LLM used to execute the operator.')
    outputs_format: Type[OperatorOutput] = Field(description="The structured content of the operator's output.")
    interface: Optional[str] = Field(description='The interface for calling the operator.')
    prompt: Optional[str] = Field(default='', description='The prompt for calling the operator.')

    def init_module(self):
        self._save_ignore_fields = ['llm']

    def __call__(self, *args: Any, **kwargs: Any) -> Union[dict, Coroutine[Any, Any, dict]]:
        """Make the operator callable and automatically choose between sync and async execution."""
        try:
            asyncio.get_running_loop()
            return self.async_execute(*args, **kwargs)
        except RuntimeError:
            return self.execute(*args, **kwargs)

    def execute(self, *args, **kwargs) -> dict:
        raise NotImplementedError(f'The execute function for {type(self).__name__} is not implemented!')

    async def async_execute(self, *args, **kwargs) -> dict:
        raise NotImplementedError(f'The execute function for {type(self).__name__} is not implemented!')

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        ignore_fields = self._save_ignore_fields + ignore
        super().save_module(path=path, ignore=ignore_fields, **kwargs)

    def get_prompt(self, **kwargs) -> str:
        return self.prompt

    def set_prompt(self, prompt: str):
        self.prompt = prompt

    def set_operator(self, data: dict):
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.interface = data.get('interface', self.interface)
        self.prompt = data.get('prompt', self.prompt)

def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
    ignore_fields = self._save_ignore_fields + ignore
    super().save_module(path=path, ignore=ignore_fields, **kwargs)

class WorkFlowManager(BaseModule):
    """
    Responsible for the scheduling and decision-making when executing a workflow. 

    Attributes:
        task_scheduler (TaskScheduler): Determines the next task(s) to execute based on the workflow graph and node states.
        action_scheduler (ActionScheduler): Determines the next action(s) to take for the selected task using an LLM.
    """
    llm: BaseLLM
    action_scheduler: ActionScheduler = Field(default_factory=ActionScheduler)
    task_scheduler: TaskScheduler = Field(default_factory=TaskScheduler)

    def init_module(self):
        self._save_ignore_fields = ['llm']

    async def schedule_next_task(self, graph: WorkFlowGraph, env: Environment=None, **kwargs) -> WorkFlowNode:
        """
        Return the next task to execute asynchronously.
        """
        execution_results = await self.task_scheduler.async_execute(llm=self.llm, graph=graph, env=env, return_prompt=True, **kwargs)
        if execution_results is None:
            return None
        scheduled_task, prompt, *other = execution_results
        message = Message(content=scheduled_task, agent=type(self).__name__, action=self.task_scheduler.name, prompt=prompt, msg_type=MessageType.COMMAND, wf_goal=graph.goal)
        env.update(message=message, state=TrajectoryState.COMPLETED)
        task: WorkFlowNode = graph.get_node(scheduled_task.task_name)
        return task

    async def schedule_next_action(self, goal: str, task: WorkFlowNode, agent_manager: AgentManager, env: Environment=None, **kwargs) -> NextAction:
        """
        Asynchronously return the next action to execute. If the task is completed, return None.
        """
        execution_results = await self.action_scheduler.async_execute(llm=self.llm, task=task, agent_manager=agent_manager, env=env, return_prompt=True, **kwargs)
        if execution_results is None:
            return None
        next_action, prompt, *_ = execution_results
        message = Message(content=next_action, agent=type(self).__name__, action=self.action_scheduler.name, prompt=prompt, msg_type=MessageType.COMMAND, wf_goal=goal, wf_task=task.name, wf_task_desc=task.description)
        env.update(message=message, state=TrajectoryState.COMPLETED)
        return next_action

    async def extract_output(self, graph: WorkFlowGraph, env: Environment, **kwargs) -> str:
        """
        Asynchronously extract output from the workflow execution.
        
        Args:
            graph (WorkFlowGraph): The workflow graph.
            env (Environment): The execution environment.
            
        Returns:
            str: The extracted output.
        """
        end_tasks = graph.find_end_nodes()
        end_task_predecesssors = sum([graph.get_node_predecessors(node=end_task) for end_task in end_tasks], [])
        candidate_taks_with_output = list(set(end_tasks) | set(end_task_predecesssors))
        candidate_msgs_with_output = []
        for task in candidate_taks_with_output:
            candidate_msgs_with_output.extend(env.get_task_messages(tasks=task, n=1))
        candidate_msgs_with_output = Message.sort_by_timestamp(messages=candidate_msgs_with_output)
        prompt = OUTPUT_EXTRACTION_PROMPT.format(goal=graph.goal, workflow_graph_representation=graph.get_workflow_description(), workflow_execution_results='\n\n'.join([str(msg) for msg in candidate_msgs_with_output]))
        llm_output: LLMOutputParser = await self.llm.async_generate(prompt=prompt)
        return llm_output.content

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        ignore_fields = self._save_ignore_fields + ignore
        super().save_module(path=path, ignore=ignore_fields, **kwargs)

def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
    ignore_fields = self._save_ignore_fields + ignore
    super().save_module(path=path, ignore=ignore_fields, **kwargs)

class CMDBase:
    """
    Base class for command execution with permission checking and cross-platform support.
    """

    def __init__(self, default_shell: str=None, storage_handler: FileStorageHandler=None):
        """
        Initialize CMDBase with system detection and shell configuration.
        
        Args:
            default_shell: Override default shell detection
            storage_handler: Storage handler for file operations
        """
        self.system = platform.system().lower()
        self.default_shell = default_shell or self._detect_default_shell()
        self.permission_cache = {}
        self.storage_handler = storage_handler

    def _detect_default_shell(self) -> str:
        """Detect the default shell for the current system."""
        if self.system == 'windows':
            return 'cmd'
        elif self.system == 'darwin':
            return 'bash'
        else:
            return 'bash'

    def _is_dangerous_command(self, command: str) -> Dict[str, Any]:
        """
        Check if a command is potentially dangerous.
        
        Args:
            command: The command to check
            
        Returns:
            Dictionary with danger assessment
        """
        dangerous_patterns = ['\\brm\\s+-rf\\b', '\\bdel\\s+/[sq]\\b', '\\bformat\\b', '\\bdd\\b', '\\bshutdown\\b', '\\breboot\\b', '\\binit\\s+[06]\\b', '\\bnetcat\\b', '\\bnc\\b', '\\bssh\\b', '\\bscp\\b', '\\bkill\\s+-9\\b', '\\btaskkill\\s+/f\\b', '\\bapt\\s+install\\b', '\\byum\\s+install\\b', '\\bbrew\\s+install\\b', '\\bchoco\\s+install\\b', '\\buseradd\\b', '\\buserdel\\b', '\\bpasswd\\b', '\\bmount\\b', '\\bumount\\b', '\\bchmod\\s+777\\b', '\\bchown\\s+root\\b']
        import re
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return {'is_dangerous': True, 'reason': f'Command matches dangerous pattern: {pattern}', 'risk_level': 'high'}
        if command_lower.startswith(('sudo ', 'runas ')):
            return {'is_dangerous': True, 'reason': 'Command requires elevated privileges', 'risk_level': 'high'}
        system_dirs = ['/etc/', '/usr/', '/var/', '/bin/', '/sbin/', 'C:\\Windows\\', 'C:\\Program Files\\']
        for sys_dir in system_dirs:
            if sys_dir in command:
                return {'is_dangerous': True, 'reason': f'Command operates on system directory: {sys_dir}', 'risk_level': 'medium'}
        return {'is_dangerous': False, 'risk_level': 'low'}

    def _request_permission(self, command: str, danger_assessment: Dict[str, Any]) -> bool:
        """
        Request permission from user to execute command.
        
        Args:
            command: The command to execute
            danger_assessment: Assessment of command danger
            
        Returns:
            True if permission granted, False otherwise
        """
        print(f'\n{'=' * 60}')
        print('🔒 PERMISSION REQUEST')
        print(f'{'=' * 60}')
        print(f'Command: {command}')
        print(f'System: {self.system}')
        print(f'Shell: {self.default_shell}')
        if danger_assessment['is_dangerous']:
            print(f'⚠️  WARNING: {danger_assessment['reason']}')
            print(f'Risk Level: {danger_assessment['risk_level'].upper()}')
        else:
            print('✅ Command appears safe')
        print('\nDo you want to execute this command?')
        print('Options:')
        print('  y/Y - Yes, execute the command')
        print('  n/N - No, do not execute')
        print('  [reason] - No, with explanation')
        print('  [empty] - No, without explanation')
        try:
            response = input('\nYour response: ').strip().lower()
            if response in ['y', 'yes']:
                print('✅ Permission granted. Executing command...')
                return True
            elif response in ['n', 'no', '']:
                print('❌ Permission denied.')
                return False
            else:
                print(f'❌ Permission denied. Reason: {response}')
                return False
        except KeyboardInterrupt:
            print('\n❌ Permission request cancelled by user.')
            return False

    def execute_command(self, command: str, timeout: int=30, cwd: str=None) -> Dict[str, Any]:
        """
        Execute a command with permission checking.
        
        Args:
            command: The command to execute
            timeout: Command timeout in seconds
            cwd: Working directory for command execution
            
        Returns:
            Dictionary with execution results
        """
        try:
            danger_assessment = self._is_dangerous_command(command)
            if not self._request_permission(command, danger_assessment):
                return {'success': False, 'error': 'Permission denied by user', 'command': command, 'stdout': '', 'stderr': '', 'return_code': None}
            if self.system == 'windows':
                if self.default_shell == 'cmd':
                    cmd_args = ['cmd', '/c', command]
                else:
                    cmd_args = ['powershell', '-Command', command]
            else:
                cmd_args = [self.default_shell, '-c', command]
            logger.info(f'Executing command: {command}')
            result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=timeout, cwd=cwd, shell=False)
            result_dict = {'success': result.returncode == 0, 'command': command, 'stdout': result.stdout, 'stderr': result.stderr, 'return_code': result.returncode, 'system': self.system, 'shell': self.default_shell}
            if self.storage_handler:
                result_dict['storage_handler'] = type(self.storage_handler).__name__
                result_dict['storage_base_path'] = str(self.storage_handler.base_path)
            return result_dict
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'Command timed out after {timeout} seconds', 'command': command, 'stdout': '', 'stderr': '', 'return_code': None}
        except Exception as e:
            return {'success': False, 'error': str(e), 'command': command, 'stdout': '', 'stderr': '', 'return_code': None}

def __init__(self, default_shell: str=None, storage_handler: FileStorageHandler=None):
    """
        Initialize CMDBase with system detection and shell configuration.
        
        Args:
            default_shell: Override default shell detection
            storage_handler: Storage handler for file operations
        """
    self.system = platform.system().lower()
    self.default_shell = default_shell or self._detect_default_shell()
    self.permission_cache = {}
    self.storage_handler = storage_handler

class MCPClient:

    def __init__(self, server_configs: Union[Dict[str, Any], List[Dict[str, Any]]], connect_timeout: float=120.0):
        if isinstance(server_configs, dict):
            self.server_configs = [server_configs]
        else:
            self.server_configs = server_configs
        self.event_loop = asyncio.new_event_loop()
        self.sessions: list[Client] = []
        self.mcp_tools: list[list[Any]] = []
        self.task = None
        self.thread_running = threading.Event()
        self.working_thread = threading.Thread(target=self._run_event, daemon=True)
        self.connect_timeout = connect_timeout
        self.tools = None
        self.tool_schemas = None
        self.tool_descriptions = None

    def _disconnect(self):
        if hasattr(self, 'shutdown_event') and self.shutdown_event:
            self.event_loop.call_soon_threadsafe(self.shutdown_event.set)
        if self.task and (not self.task.done()):
            self.event_loop.call_soon_threadsafe(self.task.cancel)
        if hasattr(self, 'working_thread') and self.working_thread.is_alive():
            self.working_thread.join(timeout=5)
        if hasattr(self, 'event_loop') and (not self.event_loop.is_closed()):
            self.event_loop.close()

    def _connect(self):
        self.working_thread.start()
        if not self.thread_running.wait(timeout=self.connect_timeout):
            self._disconnect()
            raise TimeoutError(f"Couldn't connect to the MCP server after {self.connect_timeout} seconds")

    def __enter__(self):
        self._connect()
        return self.get_toolkits()

    def __del__(self):
        try:
            self._disconnect()
        except Exception:
            pass

    def __exit__(self, exc_type, exc_value, traceback):
        self._disconnect()

    def _run_event(self):
        """Runs the event loop in a separate thread (for synchronous usage)."""
        print('Running event loop')
        asyncio.set_event_loop(self.event_loop)

        async def setup():
            try:
                async with AsyncExitStack() as stack:
                    connections = [await stack.enter_async_context(self._start_server(config)) for config in self.server_configs]
                    self.sessions, self.mcp_tools = [list(c) for c in zip(*connections)]
                    self.thread_running.set()
                    self.shutdown_event = asyncio.Event()
                    await self.shutdown_event.wait()
            except Exception as e:
                logger.error(f'Error in MCP event loop: {str(e)}')
                self.thread_running.set()
                raise
        self.task = self.event_loop.create_task(setup())
        try:
            self.event_loop.run_until_complete(self.task)
        except asyncio.CancelledError:
            logger.info('MCP client event loop was cancelled')
        except Exception as e:
            logger.error(f'Error in MCP event loop: {str(e)}')
        finally:
            if not self.event_loop.is_closed():
                self.event_loop.close()

    @asynccontextmanager
    async def _start_server(self, config: Dict[str, Any]):
        client = Client(config)
        async with client:
            tools = await client.list_tools()
            yield (client, tools)

    def create_tool(self, session: Client, mcp_tools: List[Any], config: Dict[str, Any]) -> Toolkit:

        def _sync_call_tool(name: str, **kwargs) -> Any:
            try:
                if 'arguments' in kwargs and len(kwargs) == 1:
                    arguments = kwargs['arguments']
                else:
                    arguments = kwargs
                logger.info(f'Calling MCP tool: {name} with arguments: {arguments}')
                future = asyncio.run_coroutine_threadsafe(session.call_tool(name, arguments), self.event_loop)
                result = future.result(timeout=30)
                logger.info(f'MCP tool {name} call completed successfully')
                return result
            except (TimeoutError, ClientError, McpError) as e:
                logger.error(f'Error calling MCP tool {name}: {str(e)}')
                raise
            except Exception as e:
                logger.error(f'Unexpected error calling MCP tool {name}: {str(e)}')
                raise
        all_tools = []
        for mcp_tool in mcp_tools:
            input_schema = getattr(mcp_tool, 'inputSchema', {})
            if not input_schema and hasattr(mcp_tool, 'input_schema'):
                input_schema = mcp_tool.input_schema
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])
            inputs = properties
            partial_func = partial(_sync_call_tool, mcp_tool.name)
            partial_func.__name__ = mcp_tool.name
            tool = MCPTool(name=mcp_tool.name, description=getattr(mcp_tool, 'description', None) or '', inputs=inputs, required=required, function=partial_func)
            all_tools.append(tool)
        tool_collection = Toolkit(name=next(iter(config.get('mcpServers').keys())), tools=all_tools)
        return tool_collection

    def get_toolkits(self) -> List[Toolkit]:
        """Return a list ofToolkits, one per server."""
        if not self.sessions:
            raise RuntimeError('Session not initialized')
        return [self.create_tool(session, tools, config) for session, tools, config in zip(self.sessions, self.mcp_tools, self.server_configs)]

def __enter__(self):
    self._connect()
    return self.get_toolkits()

class MCPToolkit:

    def __init__(self, servers: Optional[list[MCPClient]]=None, config_path: Optional[str]=None, config: Optional[dict[str, Any]]=None):
        parameters = []
        if config_path:
            parameters += self._from_config_file(config_path)
        if config:
            parameters += self._from_config(config)
        self.servers = []
        if parameters:
            self.servers.append(MCPClient(parameters))
        if servers:
            self.servers.extend(servers)
        failed_servers = []
        for server in self.servers:
            try:
                server._connect()
                logger.info('Successfully connected to MCP servers')
            except TimeoutError as e:
                logger.warning(f'Timeout connecting to MCP servers: {str(e)}. Some tools may not be available.')
                failed_servers.append(server)
            except Exception as e:
                logger.error(f'Error connecting to MCP servers: {str(e)}')
                failed_servers.append(server)
        for failed_server in failed_servers:
            if failed_server in self.servers:
                self.servers.remove(failed_server)

    def _from_config_file(self, config_path: str):
        try:
            with open(config_path, 'r') as f:
                server_configs = json.load(f)
            return self._from_config(server_configs)
        except FileNotFoundError:
            logger.error(f'Config file not found: {config_path}')
            return []
        except json.JSONDecodeError:
            logger.error(f'Invalid JSON in config file: {config_path}')
            return []

    def _from_config(self, server_configs: dict[str, Any]):
        if not isinstance(server_configs, dict):
            logger.error('Server configuration must be a dictionary')
            return []
        if 'mcpServers' not in server_configs:
            raise ValueError("Server configuration must contain 'mcpServers' key")
        server_list = []
        for server_name, server_config in server_configs['mcpServers'].items():
            individual_config = {'mcpServers': {server_name: server_config}}
            server_list.append(individual_config)
        return server_list

    def disconnect(self):
        for server in self.servers:
            try:
                server._disconnect()
            except Exception as e:
                logger.warning(f'Error disconnecting from MCP server: {str(e)}')
        self.servers.clear()

    def get_toolkits(self) -> List[Toolkit]:
        """Return a flattened list of all tools across all servers"""
        all_tools = []
        if not self.servers:
            logger.info('No MCP servers configured, returning empty toolkit list')
            return all_tools
        for server in self.servers:
            try:
                import threading
                import queue
                result_queue = queue.Queue()
                exception_queue = queue.Queue()

                def get_tools_with_timeout():
                    try:
                        tools = server.get_toolkits()
                        result_queue.put(tools)
                    except Exception as e:
                        exception_queue.put(e)
                thread = threading.Thread(target=get_tools_with_timeout)
                thread.daemon = True
                thread.start()
                thread.join(timeout=30)
                if thread.is_alive():
                    logger.warning('Timeout getting tools from MCP server after 30 seconds')
                    continue
                if not exception_queue.empty():
                    raise exception_queue.get()
                tools = result_queue.get()
                all_tools.extend(tools)
                logger.info(f'Added {len(tools)} tools from MCP server')
            except Exception as e:
                logger.error(f'Error getting tools from MCP server: {str(e)}')
        return all_tools

def get_tools_with_timeout():
    try:
        tools = server.get_toolkits()
        result_queue.put(tools)
    except Exception as e:
        exception_queue.put(e)

def handle_validation_result(validation_result: Dict) -> Dict | None:
    if validation_result['errors']:
        return {'error': f'Parameter validation failed: {'; '.join(validation_result['errors'])}'}
    if validation_result['warnings']:
        print(f'⚠️ Parameter warnings: {'; '.join(validation_result['warnings'])}')
        print('📝 Note: Continue with supported parameters only')
    return None

class Evaluator:
    """
    A class for evaluating the performance of a workflow.
    """

    def __init__(self, llm: BaseLLM, num_workers: int=1, agent_manager: Optional[AgentManager]=None, collate_func: Optional[Callable]=None, output_postprocess_func: Optional[Callable]=None, verbose: Optional[bool]=None, **kwargs):
        """
        Initialize the Evaluator.

        Args:
            llm (BaseLLM): The LLM to use for evaluation.
            num_workers (int): The number of parallel workers to use for evaluation. Default is 1. 
            agent_manager (AgentManager, optional): The agent manager used to construct the workflow. Only used when the workflow graph is a WorkFlowGraph.
            collate_func (Callable, optional): A function to collate the benchmark data. 
                It receives a single example from the benchmark and the output (which should be a dictionary) will serve as inputs  
                to the `execute` function of an WorkFlow (or ActionGraph) instance. 
                Note that the keys in the collated output should match the inputs of the workflow.
                The default is a lambda function that returns the example itself. 
            output_postprocess_func (Callable, optional): A function to postprocess the output of the workflow. 
                It receives the output of an WorkFlow instance (str) or an ActionGraph instance (dict) as input 
                and the output will be passed to the `evaluate` function of the benchmark. 
                The default is a lambda function that returns the output itself.
            verbose (bool, optional): Whether to print the evaluation progress.
        """
        self.llm = llm
        self.num_workers = num_workers
        self.agent_manager = agent_manager
        self._thread_agent_managers = {}
        self.collate_func = collate_func or (lambda x: x)
        self.output_postprocess_func = output_postprocess_func or (lambda x: x)
        self.verbose = verbose
        self._evaluation_records = {}
        self.kwargs = kwargs

    def _get_eval_data(self, benchmark: Benchmark, eval_mode: str='test', indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
        assert eval_mode in ['test', 'dev', 'train'], f"Invalid eval_mode: {eval_mode}. Choices: ['test', 'dev', 'train']"
        if eval_mode == 'test':
            data = benchmark.get_test_data(indices=indices, sample_k=sample_k, seed=seed)
        elif eval_mode == 'dev':
            data = benchmark.get_dev_data(indices=indices, sample_k=sample_k, seed=seed)
        else:
            data = benchmark.get_train_data(indices=indices, sample_k=sample_k, seed=seed)
        return data

    def evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], benchmark: Benchmark, eval_mode: str='test', indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None, verbose: Optional[bool]=None, update_agents: Optional[bool]=False, **kwargs) -> dict:
        """
        Evaluate the performance of the workflow on the benchmark.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate.
            benchmark (Benchmark): The benchmark to evaluate the workflow on.
            eval_mode (str): which split of the benchmark to evaluate the workflow on. Choices: ["test", "dev", "train"].
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
            verbose (bool, optional): Whether to print the evaluation progress. If not provided, the `self.verbose` will be used.
            update_agents (bool, optional): Whether to update the agents in the agent manager. Only used when the workflow graph is a WorkFlowGraph.
        Returns:
            dict: The average metrics of the workflow evaluation.
        """
        self._evaluation_records.clear()
        if isinstance(graph, WorkFlowGraph) and update_agents:
            if self.agent_manager is None:
                raise ValueError(f'`agent_manager` is not provided in {type(self).__name__}. Please provide an agent manager when evaluating a WorkFlowGraph.')
            self.agent_manager.update_agents_from_workflow(workflow_graph=graph, llm_config=self.llm.config, **kwargs)
        data = self._get_eval_data(benchmark=benchmark, eval_mode=eval_mode, indices=indices, sample_k=sample_k, seed=seed)
        results = self._evaluate_graph(graph=graph, data=data, benchmark=benchmark, verbose=verbose, **kwargs)
        return results

    def _execute_workflow_graph(self, graph: WorkFlowGraph, inputs: dict, return_trajectory: bool=False, **kwargs) -> Union[str, Tuple[str, List[Message]]]:
        """
        Execute the workflow graph and return the output.

        Args:
            graph (WorkFlowGraph): The workflow graph to execute
            inputs (dict): The inputs to the workflow graph
            **kwargs: Additional arguments for workflow graph execution

        Returns:
            str: The output of the workflow graph
        """
        if self.agent_manager is None:
            raise ValueError(f'`agent_manager` is not provided in {type(self).__name__}. Please provide an agent manager when evaluating a WorkFlowGraph.')
        graph_copy = WorkFlowGraph(goal=graph.goal, graph=graph)
        graph_copy.reset_graph()
        workflow = WorkFlow(llm=self.llm, graph=graph_copy, agent_manager=self.agent_manager, **kwargs)
        output: str = workflow.execute(inputs=inputs, **kwargs)
        if return_trajectory:
            return (output, workflow.environment.get())
        return output

    def _execute_action_graph(self, graph: ActionGraph, inputs: dict, **kwargs) -> dict:
        """
        Execute the action graph and return the output.

        Args:
            graph (ActionGraph): The action graph to execute
            inputs (dict): The inputs to the action graph
            **kwargs: Additional arguments for action graph execution

        Returns:
            dict: The output of the action graph
        """
        output: dict = graph.execute(**inputs, **kwargs)
        return output

    def _evaluate_single_example(self, graph: Union[WorkFlowGraph, ActionGraph], example: dict, benchmark: Benchmark, **kwargs) -> Optional[dict]:
        """
        Evaluate a single data example through the workflow and save the evaluation metrics to the evaluation records.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to execute
            example (dict): Single input data example
            **kwargs: Additional arguments for workflow execution

        Returns:
            Optional[dict]: Evaluation metrics for this example, None if failed
        """
        try:
            inputs: dict = self.collate_func(example)
            if not isinstance(inputs, dict):
                raise ValueError(f'The collate_func should return a dictionary. Got {type(inputs)}.')
            if isinstance(graph, ActionGraph):
                output: dict = self._execute_action_graph(graph=graph, inputs=inputs, **kwargs)
            elif isinstance(graph, WorkFlowGraph):
                workflow_graph_outputs = self._execute_workflow_graph(graph=graph, inputs=inputs, return_trajectory=True, **kwargs)
                output: str = workflow_graph_outputs[0]
                trajectory: List[Message] = workflow_graph_outputs[1]
            else:
                raise ValueError(f'Invalid workflow type: {type(graph)}. Must be WorkFlowGraph or ActionGraph.')
            output = self.output_postprocess_func(output)
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(prediction=output, label=label)
            example_id = benchmark.get_id(example=example)
            self._evaluation_records[example_id] = {'prediction': output, 'label': label, 'metrics': metrics}
            if isinstance(graph, WorkFlowGraph):
                self._evaluation_records[example_id]['trajectory'] = trajectory
        except Exception as e:
            logger.warning(f'Error evaluating example and set the metrics to None:\nExample: {example}\nError: {str(e)}')
            return None
        return metrics

    def _single_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> List[dict]:
        """
        Evaluate workflow on data using single thread.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate
            data (List[dict]): List of input data
            benchmark (Benchmark): The benchmark to evaluate the workflow on
            verbose (bool): Whether to show progress bar
            **kwargs: Additional arguments for workflow execution

        Returns:
            List[dict]: List of valid evaluation metrics
        """
        if not data:
            logger.warning('No data to evaluate. Return an empty list.')
            return []
        results = []
        if verbose:
            progress_bar = tqdm(data, desc='Evaluating workflow', total=len(data))
        for example in data:
            result = self._evaluate_single_example(graph, example, benchmark, **kwargs)
            results.append(result)
            if verbose:
                progress_bar.update(1)
        if verbose:
            progress_bar.close()
        return results

    def _create_new_agent_manager(self) -> AgentManager:
        """Create a new agent manager with the same configuration but new locks"""
        if self.agent_manager is None:
            return None
        new_manager = AgentManager(agents=self.agent_manager.agents, storage_handler=self.agent_manager.storage_handler)
        return new_manager

    def _get_thread_agent_manager(self) -> AgentManager:
        """Get or create thread-specific agent manager"""
        if self.agent_manager is None:
            return None
        thread_id = threading.get_ident()
        if thread_id not in self._thread_agent_managers:
            new_manager = self._create_new_agent_manager()
            self._thread_agent_managers[thread_id] = new_manager
        return self._thread_agent_managers[thread_id]

    def _evaluate_single_example_with_context(self, graph: Union[WorkFlowGraph, ActionGraph], example: dict, benchmark: Benchmark, **kwargs) -> Optional[dict]:
        """Wrapper that sets up thread-specific context before running evaluation"""
        thread_agent_manager = self._get_thread_agent_manager()
        if thread_agent_manager is None:
            return self._evaluate_single_example(graph, example, benchmark, **kwargs)
        original_agent_manager = self.agent_manager
        try:
            self.agent_manager = thread_agent_manager
            return self._evaluate_single_example(graph, example, benchmark, **kwargs)
        finally:
            self.agent_manager = original_agent_manager

    def _parallel_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> List[dict]:
        if not data:
            logger.warning('No data to evaluate. Return an empty list.')
            return []
        results = []
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(contextvars.copy_context().run, self._evaluate_single_example_with_context, graph, example, benchmark, **kwargs): example for example in data}
            if verbose:
                progress_bar = tqdm(desc='Evaluating workflow', total=len(futures))
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)
                if verbose:
                    progress_bar.update(1)
        if verbose:
            progress_bar.close()
        return results

    def _calculate_average_score(self, scores: List[dict]) -> dict:
        """
        Calculate the average score from a list of scores.

        Args:
            scores (List[dict]): List of evaluation scores

        Returns:
            dict: Average metrics
        """
        if not scores:
            logger.warning('No scores found. Return an empty dictionary.')
            return {}
        num_total_items = len(scores)
        first_valid_score = None
        for score in scores:
            if score is not None:
                first_valid_score = score
                break
        if first_valid_score is None:
            logger.warning('No valid scores found. Return an empty dictionary.')
            return {}
        return {k: sum((d[k] for d in scores if d is not None)) / num_total_items for k in first_valid_score}

    def _evaluate_graph(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> dict:
        """
        Evaluate the workflow on the data.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate
            data (List[dict]): List of input data to evaluate
            benchmark (Benchmark): The benchmark to evaluate the workflow on
            verbose (bool, optional): Whether to print the evaluation progress. If not provided, the `self.verbose` will be used.
            **kwargs: Additional arguments passed to workflow execution

        Returns:
            dict: The average metrics of the workflow evaluation
        """
        if not data:
            logger.warning('No data to evaluate. Return an empty dictionary.')
            return {}
        verbose = verbose if verbose is not None else self.verbose
        if self.num_workers > 1:
            results = self._parallel_evaluate(graph, data, benchmark, verbose, **kwargs)
        else:
            results = self._single_evaluate(graph, data, benchmark, verbose, **kwargs)
        return self._calculate_average_score(results)

    def get_example_evaluation_record(self, benchmark: Benchmark, example: Any) -> Optional[dict]:
        """
        Get the evaluation record for a given example.
        """
        example_id = benchmark.get_id(example=example)
        return self._evaluation_records.get(example_id, None)

    def get_evaluation_record_by_id(self, benchmark: Benchmark, example_id: str, eval_mode: str='test') -> Optional[dict]:
        """
        Get the evaluation record for a given example id.
        """
        example = benchmark.get_example_by_id(example_id=example_id, mode=eval_mode)
        return self.get_example_evaluation_record(benchmark=benchmark, example=example)

    def get_all_evaluation_records(self) -> dict:
        """
        Get all the evaluation records.
        """
        return self._evaluation_records.copy()

    async def async_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], benchmark: Benchmark, eval_mode: str='test', indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None, verbose: Optional[bool]=None, **kwargs) -> dict:
        """
        Asynchronously evaluate the performance of the workflow on the benchmark.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate.
            benchmark (Benchmark): The benchmark to evaluate the workflow on.
            eval_mode (str): which split of the benchmark to evaluate the workflow on. Choices: ["test", "dev", "train"].
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
            verbose (bool, optional): Whether to print the evaluation progress. If not provided, the `self.verbose` will be used.
        
        Returns:
            dict: The average metrics of the workflow evaluation.
        """
        self._evaluation_records.clear()
        data = self._get_eval_data(benchmark=benchmark, eval_mode=eval_mode, indices=indices, sample_k=sample_k, seed=seed)
        if not data:
            logger.warning('No data to evaluate. Return an empty dictionary.')
            return {}
        verbose = verbose if verbose is not None else self.verbose
        sem = asyncio.Semaphore(self.num_workers)

        async def process_with_semaphore(example):
            async with sem:
                try:
                    return await self._async_evaluate_single_example(graph=graph, example=example, benchmark=benchmark, **kwargs)
                except Exception as e:
                    logger.warning(f'Async evaluation failed for example with semaphore: {str(e)}')
                    return None
        tasks = [process_with_semaphore(example) for example in data]
        if verbose:
            results = await tqdm_asyncio.gather(*tasks, desc=f'Evaluating {benchmark.name}', total=len(data))
        else:
            results = await asyncio.gather(*tasks)
        return self._calculate_average_score(results)

    async def _async_evaluate_single_example(self, graph: Union[WorkFlowGraph, ActionGraph], example: dict, benchmark: Benchmark, **kwargs) -> Optional[dict]:
        """
        Asynchronously evaluate a single example. 
        """
        try:
            inputs: dict = self.collate_func(example)
            if not isinstance(inputs, dict):
                raise ValueError(f'The collate_func should return a dictionary. Got {type(inputs)}.')
            if isinstance(graph, ActionGraph):
                output: dict = await self._async_execute_action_graph(graph=graph, inputs=inputs, **kwargs)
            elif isinstance(graph, WorkFlowGraph):
                workflow_graph_outputs = await self._async_execute_workflow_graph(graph=graph, inputs=inputs, return_trajectory=True, **kwargs)
                output: str = workflow_graph_outputs[0]
                trajectory: List[Message] = workflow_graph_outputs[1]
            else:
                raise ValueError(f'Invalid workflow type: {type(graph)}. Must be WorkFlowGraph or ActionGraph.')
            output = self.output_postprocess_func(output)
            label = benchmark.get_label(example)
            if hasattr(benchmark, 'async_evaluate') and callable(getattr(benchmark, 'async_evaluate')):
                metrics = await benchmark.async_evaluate(prediction=output, label=label)
            else:
                metrics = benchmark.evaluate(prediction=output, label=label)
            example_id = benchmark.get_id(example=example)
            self._evaluation_records[example_id] = {'prediction': output, 'label': label, 'metrics': metrics}
            if isinstance(graph, WorkFlowGraph):
                self._evaluation_records[example_id]['trajectory'] = trajectory
        except Exception as e:
            logger.warning(f'Error evaluating example and set the metrics to None:\nExample: {example}\nError: {str(e)}')
            return None
        return metrics

    async def _async_execute_action_graph(self, graph: ActionGraph, inputs: dict, **kwargs) -> dict:
        """
        Asynchronously execute the action graph.
        """
        return await graph.async_execute(**inputs, **kwargs)

    async def _async_execute_workflow_graph(self, graph: WorkFlowGraph, inputs: dict, return_trajectory: bool=False, **kwargs) -> Union[str, Tuple[str, List[Message]]]:
        """
        Asynchronously execute the workflow graph.
        """
        if self.agent_manager is None:
            raise ValueError('`agent_manager` is not provided. Please provide an agent manager when evaluating a WorkFlowGraph.')
        graph_copy = WorkFlowGraph(goal=graph.goal, graph=graph)
        graph_copy.reset_graph()
        local_agent_manager = AgentManager(agents=self.agent_manager.agents, storage_handler=self.agent_manager.storage_handler)
        workflow = WorkFlow(llm=self.llm, graph=graph_copy, agent_manager=local_agent_manager, **kwargs)
        output: str = await workflow.async_execute(inputs=inputs, **kwargs)
        if return_trajectory:
            return (output, workflow.environment.get())
        return output

def _create_new_agent_manager(self) -> AgentManager:
    """Create a new agent manager with the same configuration but new locks"""
    if self.agent_manager is None:
        return None
    new_manager = AgentManager(agents=self.agent_manager.agents, storage_handler=self.agent_manager.storage_handler)
    return new_manager

class PruningPipeline:
    """可插拔剪枝流水线：质量剪枝(QP) → 多样性剪枝(DP) → 误解反驳(MR)。

    候选输入格式：List[{"agent_id": int, "text": str}]
    输出保留相同结构，并在条目中填充可选指标：qp_score、dup_removed 等。
    """

    def __init__(self, enable_qp: bool=True, enable_dp: bool=True, enable_mr: bool=False, qp_threshold: float=0.15, qp_top_k: Optional[int]=None, dp_similarity_threshold: float=0.92, dp_max_candidates: Optional[int]=None, mr_llm_config: Optional[LLMConfig]=None, min_keep_count: Optional[int]=None) -> None:
        self.enable_qp = enable_qp
        self.enable_dp = enable_dp
        self.enable_mr = enable_mr
        self.qp_threshold = qp_threshold
        self.qp_top_k = qp_top_k
        self.dp_similarity_threshold = dp_similarity_threshold
        self.dp_max_candidates = dp_max_candidates
        self.mr_llm_config = mr_llm_config
        self.min_keep_count = min_keep_count

    def _qp_score(self, problem: str, text: str) -> float:
        qv = _tf_vector(_tokenize(problem))
        tv = _tf_vector(_tokenize(text))
        return _cosine_sim(qv, tv)

    def _quality_prune(self, problem: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.enable_qp or len(candidates) <= 1:
            return candidates
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for c in candidates:
            s = self._qp_score(problem, c.get('text', ''))
            c = dict(c)
            c['qp_score'] = s
            scored.append((s, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        if self.qp_top_k is not None and self.qp_top_k > 0:
            scored = scored[:self.qp_top_k]
        kept = [c for s, c in scored if s >= self.qp_threshold]
        if not kept:
            kept = [scored[0][1]]
        if self.min_keep_count and len(kept) < self.min_keep_count:
            existing_ids = set((id(obj) for obj in kept))
            for _, c in scored:
                if id(c) not in existing_ids:
                    kept.append(c)
                if len(kept) >= self.min_keep_count:
                    break
        return kept

    def _diversity_prune(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.enable_dp or len(candidates) <= 1:
            return candidates
        vecs = [_tf_vector(_tokenize(c.get('text', ''))) for c in candidates]
        kept: List[int] = []
        for i, v in enumerate(vecs):
            diverse = True
            for j in kept:
                sim = _cosine_sim(v, vecs[j])
                if sim >= self.dp_similarity_threshold:
                    diverse = False
                    break
            if diverse:
                kept.append(i)
            if self.dp_max_candidates and len(kept) >= self.dp_max_candidates:
                break
        pruned = [candidates[i] for i in kept]
        if self.min_keep_count and len(pruned) < self.min_keep_count:
            ranked = sorted(range(len(candidates)), key=lambda idx: float(candidates[idx].get('qp_score') or 0.0), reverse=True)
            chosen = set(kept)
            for idx in ranked:
                if idx in chosen:
                    continue
                pruned.append(candidates[idx])
                chosen.add(idx)
                if len(pruned) >= self.min_keep_count:
                    break
        return pruned

    def _build_critic(self) -> Optional[CustomizeAgent]:
        if not self.mr_llm_config:
            return None
        prompt = '\nYou are a critical reviewer. Given a problem and a set of condensed candidate answers, identify common misunderstandings or mistakes, and propose a corrected consolidated answer.\n\nProblem:\n{problem}\n\nCandidates:\n{candidates_text}\n\nReturn XML:\n<response>\n  <issues>Common mistakes found</issues>\n  <rebuttal>How to fix them</rebuttal>\n  <corrected>Single corrected final answer</corrected>\n</response>\n            '.strip()
        inputs = [{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'candidates_text', 'type': 'str', 'description': 'Concatenated candidates'}]
        outputs = [{'name': 'issues', 'type': 'str', 'description': 'Common mistakes', 'required': True}, {'name': 'rebuttal', 'type': 'str', 'description': 'Corrections', 'required': True}, {'name': 'corrected', 'type': 'str', 'description': 'Corrected final answer', 'required': True}]
        return CustomizeAgent(name='CriticAgent', description='Detects misunderstandings and proposes corrected answer', prompt=prompt, llm_config=self.mr_llm_config, inputs=inputs, outputs=outputs, parse_mode='xml')

    def _misunderstanding_rebuttal(self, problem: str, candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, str]]]:
        if not self.enable_mr:
            return (candidates, None)
        critic = self._build_critic()
        if critic is None:
            return (candidates, None)
        concat = '\n\n'.join((f'#{c.get('agent_id')}: {c.get('text', '').strip()}' for c in candidates))
        msg = critic(inputs={'problem': problem, 'candidates_text': concat})
        st = msg.content.get_structured_data()
        for c in candidates:
            c['mr_issues'] = st.get('issues', '')
            c['mr_rebuttal'] = st.get('rebuttal', '')
        suggested = {'issues': st.get('issues', ''), 'rebuttal': st.get('rebuttal', ''), 'corrected': st.get('corrected', '')}
        return (candidates, suggested)

    def apply(self, problem: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """返回 {"candidates": pruned, "mr_suggested": optional}。"""
        step1 = self._quality_prune(problem, candidates)
        step2 = self._diversity_prune(step1)
        step3, suggested = self._misunderstanding_rebuttal(problem, step2)
        return {'candidates': step3, 'mr_suggested': suggested}

def _build_critic(self) -> Optional[CustomizeAgent]:
    if not self.mr_llm_config:
        return None
    prompt = '\nYou are a critical reviewer. Given a problem and a set of condensed candidate answers, identify common misunderstandings or mistakes, and propose a corrected consolidated answer.\n\nProblem:\n{problem}\n\nCandidates:\n{candidates_text}\n\nReturn XML:\n<response>\n  <issues>Common mistakes found</issues>\n  <rebuttal>How to fix them</rebuttal>\n  <corrected>Single corrected final answer</corrected>\n</response>\n            '.strip()
    inputs = [{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'candidates_text', 'type': 'str', 'description': 'Concatenated candidates'}]
    outputs = [{'name': 'issues', 'type': 'str', 'description': 'Common mistakes', 'required': True}, {'name': 'rebuttal', 'type': 'str', 'description': 'Corrections', 'required': True}, {'name': 'corrected', 'type': 'str', 'description': 'Corrected final answer', 'required': True}]
    return CustomizeAgent(name='CriticAgent', description='Detects misunderstandings and proposes corrected answer', prompt=prompt, llm_config=self.mr_llm_config, inputs=inputs, outputs=outputs, parse_mode='xml')

class MultiAgentDebateActionGraph(ActionGraph):
    """Multi-Agent Debate ActionGraph implementation (Google MAD style)."""
    name: str = 'MultiAgentDebate'
    description: str = 'Multi-agent debate workflow framework'
    llm_config: LLMConfig = Field(default_factory=lambda: OpenAILLMConfig(model='gpt-4o-mini', openai_key=os.getenv('OPENAI_API_KEY')), description='Default LLM configuration for all agents')
    debater_agents: Optional[List[CustomizeAgent]] = Field(default=None, description='Optional: multiple debater CustomizeAgents, randomly selected during execution')
    judge_agent: Optional[CustomizeAgent] = Field(default=None, description='Optional: judge CustomizeAgent, used for judging phase if provided')
    llm_config_pool: Optional[List[LLMConfig]] = Field(default=None, description='Optional: LLM configuration pool for random selection, provides choices for agents without specified models')
    group_graphs_enabled: bool = Field(default=False, description='Enable group graph mode: replace individual debaters with workflow graphs')
    group_graphs: Optional[List[ActionGraph]] = Field(default=None, description='When group graph mode is enabled, provide workflow graph list (length >= 1)')
    _sc_ensemble: Optional[QAScEnsemble] = None

    def init_module(self):
        """Initialize module (create LLM, construct reusable operators)."""
        super().init_module()
        if self.group_graphs_enabled and self.debater_agents:
            raise ValueError('Configuration conflict: cannot configure debater_agents when group_graphs_enabled is enabled.')
        if self.group_graphs_enabled and (not self.group_graphs or len(self.group_graphs) == 0):
            raise ValueError('Configuration error: must provide non-empty group_graphs list when group graph mode is enabled.')
        if not self.group_graphs_enabled and self.group_graphs:
            raise ValueError('Configuration error: provided group_graphs but did not enable group_graphs_enabled. Please enable both or remove group_graphs.')
        self._sc_ensemble = QAScEnsemble(self._llm)

    def _create_default_debater_agent(self) -> CustomizeAgent:
        """Create default debater CustomizeAgent (XML parsing thought/argument/answer)."""
        llm_config = random.choice(self.llm_config_pool) if self.llm_config_pool else self.llm_config
        return CustomizeAgent(name='DebaterAgent', description='Generate argument/rebuttal and optional answer per debate round.', prompt=DEBATER_AGENT_PROMPT, llm_config=llm_config, inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'transcript_text', 'type': 'str', 'description': 'Formatted debate transcript so far'}, {'name': 'role', 'type': 'str', 'description': 'Debater role/persona'}, {'name': 'agent_id', 'type': 'str', 'description': 'Debater id (string)'}, {'name': 'round_index', 'type': 'str', 'description': '1-based round index'}, {'name': 'total_rounds', 'type': 'str', 'description': 'Total rounds'}], outputs=[{'name': 'thought', 'type': 'str', 'description': 'Brief reasoning', 'required': True}, {'name': 'argument', 'type': 'str', 'description': 'Argument or rebuttal', 'required': True}, {'name': 'answer', 'type': 'str', 'description': 'Optional current answer', 'required': False}], parse_mode='xml')

    def _create_default_judge_agent(self) -> CustomizeAgent:
        """Create default judge CustomizeAgent (XML parsing rationale/winning_agent_id/final_answer)."""
        llm_config = random.choice(self.llm_config_pool) if self.llm_config_pool else self.llm_config
        return CustomizeAgent(name='JudgeAgent', description='Deliver final decision and answer based on debate transcript.', prompt=JUDGE_AGENT_PROMPT, llm_config=llm_config, inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'transcript_text', 'type': 'str', 'description': 'Formatted debate transcript'}, {'name': 'roles_text', 'type': 'str', 'description': 'Roles listing text'}], outputs=[{'name': 'rationale', 'type': 'str', 'description': 'Judging rationale', 'required': True}, {'name': 'winning_agent_id', 'type': 'str', 'description': 'Winning agent id (integer as string)', 'required': True}, {'name': 'final_answer', 'type': 'str', 'description': 'Final answer', 'required': True}], parse_mode='xml')

    def execute(self, problem: str, num_agents: int=3, num_rounds: int=3, judge_mode: str='llm_judge', personas: Optional[List[str]]=None, return_transcript: bool=True, agent_llm_configs: Optional[List[LLMConfig]]=None, enable_pruning: bool=False, pruning_qp_threshold: float=0.15, pruning_dp_similarity_threshold: float=0.92, pruning_enable_mr: bool=False, pruning_mr_llm_config: Optional[LLMConfig]=None, pruning_snapshot_mode: bool=False, transcript_mode: str='prev', **kwargs) -> dict:
        """Execute debate workflow (synchronous)."""
        state = self._setup_debate(problem, num_agents, num_rounds, personas, agent_llm_configs)
        transcript = self._run_debate_rounds(problem, state, transcript_mode)
        pruning_info = None
        pruning_debug = None
        pruning_rounds_debug: Optional[List[Dict[str, Any]]] = None
        if enable_pruning:
            min_keep = max(1, int(round(state['num_agents'] * 0.3)))
            pipeline = PruningPipeline(enable_qp=True, enable_dp=True, enable_mr=pruning_enable_mr, qp_threshold=pruning_qp_threshold, dp_similarity_threshold=pruning_dp_similarity_threshold, mr_llm_config=pruning_mr_llm_config, min_keep_count=min_keep)
            if pruning_snapshot_mode:
                pruning_rounds_debug = []
                for r in range(state['num_rounds']):
                    rcands = collect_round_candidates(transcript=transcript, num_agents=state['num_agents'], round_index=r)
                    info_r = pipeline.apply(problem=problem, candidates=rcands)
                    pruning_rounds_debug.append({'round': r, 'before_candidates': rcands, 'after_candidates': info_r.get('candidates', []), 'mr_suggested': info_r.get('mr_suggested')})
            candidates = collect_last_round_candidates(transcript=transcript, num_agents=state['num_agents'], last_round_index=state['num_rounds'] - 1)
            pruning_info = pipeline.apply(problem=problem, candidates=candidates)
            try:
                pruning_debug = {'before_candidates': candidates, 'after_candidates': pruning_info.get('candidates', []), 'mr_suggested': pruning_info.get('mr_suggested')}
            except Exception:
                pruning_debug = None
        consensus = self._generate_consensus(problem, state, transcript, judge_mode, pruning_info)
        result: Dict[str, Any] = {'final_answer': consensus['final_answer'], 'winner': consensus.get('winner'), 'rationale': consensus.get('rationale')}
        if return_transcript:
            result['transcript'] = transcript
        if enable_pruning and pruning_debug is not None:
            result['pruning'] = pruning_debug
        if enable_pruning and pruning_snapshot_mode and (pruning_rounds_debug is not None):
            result['pruning_rounds'] = pruning_rounds_debug
        return result

    async def async_execute(self, problem: str, num_agents: int=3, num_rounds: int=3, judge_mode: str='llm_judge', personas: Optional[List[str]]=None, return_transcript: bool=True, agent_llm_configs: Optional[List[LLMConfig]]=None, enable_pruning: bool=False, pruning_qp_threshold: float=0.15, pruning_dp_similarity_threshold: float=0.92, pruning_enable_mr: bool=False, pruning_mr_llm_config: Optional[LLMConfig]=None, pruning_snapshot_mode: bool=False, transcript_mode: str='prev', **kwargs) -> dict:
        """Execute debate workflow (asynchronous)."""
        state = self._setup_debate(problem, num_agents, num_rounds, personas, agent_llm_configs)
        transcript = await self._run_debate_rounds_async(problem, state, transcript_mode)
        pruning_info = None
        pruning_debug = None
        pruning_rounds_debug: Optional[List[Dict[str, Any]]] = None
        if enable_pruning:
            min_keep = max(1, int(round(state['num_agents'] * 0.3)))
            pipeline = PruningPipeline(enable_qp=True, enable_dp=True, enable_mr=pruning_enable_mr, qp_threshold=pruning_qp_threshold, dp_similarity_threshold=pruning_dp_similarity_threshold, mr_llm_config=pruning_mr_llm_config, min_keep_count=min_keep)
            if pruning_snapshot_mode:
                pruning_rounds_debug = []
                for r in range(state['num_rounds']):
                    rcands = collect_round_candidates(transcript=transcript, num_agents=state['num_agents'], round_index=r)
                    info_r = pipeline.apply(problem=problem, candidates=rcands)
                    pruning_rounds_debug.append({'round': r, 'before_candidates': rcands, 'after_candidates': info_r.get('candidates', []), 'mr_suggested': info_r.get('mr_suggested')})
            candidates = collect_last_round_candidates(transcript=transcript, num_agents=state['num_agents'], last_round_index=state['num_rounds'] - 1)
            pruning_info = pipeline.apply(problem=problem, candidates=candidates)
            try:
                pruning_debug = {'before_candidates': candidates, 'after_candidates': pruning_info.get('candidates', []), 'mr_suggested': pruning_info.get('mr_suggested')}
            except Exception:
                pruning_debug = None
        consensus = await self._generate_consensus_async(problem, state, transcript, judge_mode, pruning_info)
        result: Dict[str, Any] = {'final_answer': consensus['final_answer'], 'winner': consensus.get('winner')}
        if return_transcript:
            result['transcript'] = transcript
        if enable_pruning and pruning_debug is not None:
            result['pruning'] = pruning_debug
        if enable_pruning and pruning_snapshot_mode and (pruning_rounds_debug is not None):
            result['pruning_rounds'] = pruning_rounds_debug
        return result

    def _setup_debate(self, problem: str, num_agents: int, num_rounds: int, personas: Optional[List[str]], agent_llm_configs: Optional[List[LLMConfig]]=None) -> dict:
        """Setup debate environment."""
        if num_agents <= 1:
            raise ValueError('num_agents must be greater than 1')
        if num_rounds <= 0:
            raise ValueError('num_rounds must be positive')
        roles: List[str] = personas or get_default_personas(num_agents)
        agents_for_ids: List[CustomizeAgent] = self._prepare_runtime_debaters(num_agents, agent_llm_configs)
        state: Dict[str, Any] = {'problem': problem, 'num_agents': num_agents, 'num_rounds': num_rounds, 'roles': roles, 'agents': agents_for_ids}
        return state

    def _prepare_runtime_debaters(self, num_agents: int, agent_llm_configs: Optional[List[LLMConfig]]) -> List[CustomizeAgent]:
        """Select CustomizeAgent for each agent_id that remains unchanged throughout the debate.
        Priority:
        1) User explicitly passes debater_agents → cycle/truncate by length and assign to each position
        2) Pass agent_llm_configs → create default debater for each position
        3) Use llm_config_pool random selection → create default debater for each position (prioritized over default llm_config)
        4) Fallback to default llm_config
        """
        if self.group_graphs_enabled:
            return []
        if self.debater_agents:
            agents: List[CustomizeAgent] = []
            for i in range(num_agents):
                agents.append(self.debater_agents[i % len(self.debater_agents)])
            return agents
        if agent_llm_configs and len(agent_llm_configs) > 0:
            return [self._create_debater_agent_with_llm(agent_llm_configs[i % len(agent_llm_configs)]) for i in range(num_agents)]
        if self.llm_config_pool and len(self.llm_config_pool) > 0:
            return [self._create_debater_agent_with_llm(random.choice(self.llm_config_pool)) for _ in range(num_agents)]
        default_agent = self._create_default_debater_agent()
        return [default_agent for _ in range(num_agents)]

    def _create_debater_agent_with_llm(self, llm_cfg: LLMConfig) -> CustomizeAgent:
        """Create a debater agent with given LLM configuration that is consistent with default structure."""
        return CustomizeAgent(name='DebaterAgent', description='Generate argument/rebuttal and optional answer per debate round.', prompt=DEBATER_AGENT_PROMPT, llm_config=llm_cfg, inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'transcript_text', 'type': 'str', 'description': 'Formatted debate transcript so far'}, {'name': 'role', 'type': 'str', 'description': 'Debater role/persona'}, {'name': 'agent_id', 'type': 'str', 'description': 'Debater id (string)'}, {'name': 'round_index', 'type': 'str', 'description': '1-based round index'}, {'name': 'total_rounds', 'type': 'str', 'description': 'Total rounds'}], outputs=[{'name': 'thought', 'type': 'str', 'description': 'Brief reasoning', 'required': True}, {'name': 'argument', 'type': 'str', 'description': 'Argument or rebuttal', 'required': True}, {'name': 'answer', 'type': 'str', 'description': 'Optional current answer', 'required': False}], parse_mode='xml')

    def _run_debate_rounds(self, problem: str, state: dict, transcript_mode: str='prev') -> List[dict]:
        """Run debate rounds (synchronous). Return transcript.
        
        Args:
            transcript_mode: Control transcript range accessible to agents
                - "prev": Can only see n-1 round speeches (default)
                - "all": Can see all previous round speeches
        """
        transcript: List[dict] = []
        num_agents: int = state['num_agents']
        num_rounds: int = state['num_rounds']
        roles: List[str] = state['roles']
        for round_index in range(num_rounds):
            for agent_id in range(num_agents):
                if self.group_graphs_enabled and self.group_graphs:
                    graph = self.group_graphs[agent_id % len(self.group_graphs)]
                    transcript_text = self._get_transcript_for_agent(transcript, round_index, agent_id, transcript_mode, num_agents)
                    g_inputs = {'problem': problem, 'transcript_text': transcript_text, 'role': roles[agent_id], 'agent_id': str(agent_id), 'round_index': str(round_index + 1), 'total_rounds': str(num_rounds)}
                    g_out = graph.execute(**g_inputs)
                    structured = {'argument': g_out.get('argument', g_out.get('output', '')), 'answer': g_out.get('answer'), 'thought': g_out.get('thought', '')}
                else:
                    selected_agent: Optional[CustomizeAgent] = None
                    agents_for_ids: Optional[List[CustomizeAgent]] = state.get('agents')
                    if agents_for_ids:
                        selected_agent = agents_for_ids[agent_id]
                    elif self.debater_agents:
                        selected_agent = random.choice(self.debater_agents)
                    if selected_agent is not None:
                        try:
                            transcript_text = self._get_transcript_for_agent(transcript, round_index, agent_id, transcript_mode, num_agents)
                            inputs = {'problem': problem, 'transcript_text': transcript_text, 'role': roles[agent_id], 'agent_id': str(agent_id), 'round_index': str(round_index + 1), 'total_rounds': str(num_rounds)}
                            msg = selected_agent(inputs=inputs)
                            structured = msg.content.get_structured_data()
                        except Exception as e:
                            print(f'Agent execution error: {e}')
                            structured = {'argument': '', 'answer': '', 'thought': ''}
                    else:
                        transcript_text = self._get_transcript_for_agent(transcript, round_index, agent_id, transcript_mode, num_agents)
                        prompt = build_agent_prompt(problem=problem, transcript_text=transcript_text, role=roles[agent_id], agent_id=agent_id, round_index=round_index, total_rounds=num_rounds)
                        response = self._llm.generate(prompt=prompt, parser=DebateAgentOutput, parse_mode='xml')
                        structured = response.get_structured_data()
                transcript.append({'agent_id': agent_id, 'round': round_index, 'role': roles[agent_id], 'argument': structured.get('argument', ''), 'answer': structured.get('answer'), 'thought': structured.get('thought', '')})
                try:
                    arg_full = str(structured.get('argument', '')).strip()
                    ans_full = str(structured.get('answer') or '').strip()
                    print(f'[Round {round_index + 1}] Agent#{agent_id} ({roles[agent_id]})\nArgument: {arg_full}\nAnswer: {ans_full}\n')
                except Exception:
                    pass
        return transcript

    def _get_transcript_for_agent(self, transcript: List[dict], round_index: int, agent_id: int, transcript_mode: str, num_agents: int) -> str:
        """根据访问模式获取agent可以访问的transcript。
        
        Args:
            transcript: 完整的transcript
            round_index: 当前轮次索引
            agent_id: 当前agent的ID
            transcript_mode: 访问模式
                - "prev": 只能看到n-1轮次的发言（默认）
                - "all": 可以看到之前所有轮次的发言
            num_agents: agent总数
            
        Returns:
            str: 格式化后的transcript文本
        """
        if transcript_mode == 'prev':
            filtered_transcript = [t for t in transcript if t['round'] < round_index]
        elif transcript_mode == 'all':
            filtered_transcript = []
            for t in transcript:
                if t['round'] < round_index:
                    filtered_transcript.append(t)
                elif t['round'] == round_index and t['agent_id'] < agent_id:
                    filtered_transcript.append(t)
        else:
            filtered_transcript = [t for t in transcript if t['round'] < round_index]
        return format_transcript(filtered_transcript)

    async def _run_debate_rounds_async(self, problem: str, state: dict, transcript_mode: str='prev') -> List[dict]:
        """运行辩论轮次（异步）。返回 transcript。
        
        Args:
            transcript_mode: 控制agent可以访问的transcript范围
                - "prev": 只能看到n-1轮次的发言（默认）
                - "all": 可以看到之前所有轮次的发言
        """
        transcript: List[dict] = []
        num_agents: int = state['num_agents']
        num_rounds: int = state['num_rounds']
        roles: List[str] = state['roles']
        for round_index in range(num_rounds):
            if self.group_graphs_enabled and self.group_graphs:
                for agent_id in range(num_agents):
                    graph = self.group_graphs[agent_id % len(self.group_graphs)]
                    transcript_text = self._get_transcript_for_agent(transcript, round_index, agent_id, transcript_mode, num_agents)
                    g_inputs = {'problem': problem, 'transcript_text': transcript_text, 'role': roles[agent_id], 'agent_id': str(agent_id), 'round_index': str(round_index + 1), 'total_rounds': str(num_rounds)}
                    g_out = graph.execute(**g_inputs)
                    structured = {'argument': g_out.get('argument', g_out.get('output', '')), 'answer': g_out.get('answer'), 'thought': g_out.get('thought', '')}
                    transcript.append({'agent_id': agent_id, 'round': round_index, 'role': roles[agent_id], 'argument': structured.get('argument', ''), 'answer': structured.get('answer'), 'thought': structured.get('thought', '')})
                    try:
                        print(f'[Round {round_index + 1}] Agent#{agent_id} ({roles[agent_id]})\nArgument: {str(structured.get('argument', '')).strip()}\nAnswer: {str(structured.get('answer') or '').strip()}\n')
                    except Exception:
                        pass
            elif state.get('agents') or self.debater_agents or self.debater_agent is not None:
                import asyncio
                tasks = []
                id_list: List[int] = []
                for agent_id in range(num_agents):
                    agents_for_ids: Optional[List[CustomizeAgent]] = state.get('agents')
                    if agents_for_ids:
                        selected_agent = agents_for_ids[agent_id]
                    elif self.debater_agents:
                        selected_agent = random.choice(self.debater_agents)
                    else:
                        selected_agent = None
                    transcript_text = self._get_transcript_for_agent(transcript, round_index, agent_id, transcript_mode, num_agents)
                    inputs = {'problem': problem, 'transcript_text': transcript_text, 'role': roles[agent_id], 'agent_id': str(agent_id), 'round_index': str(round_index + 1), 'total_rounds': str(num_rounds)}
                    tasks.append(selected_agent(inputs=inputs))
                    id_list.append(agent_id)
                messages = await asyncio.gather(*tasks)
                for agent_id, msg in zip(id_list, messages):
                    structured = msg.content.get_structured_data()
                    transcript.append({'agent_id': agent_id, 'round': round_index, 'role': roles[agent_id], 'argument': structured.get('argument', ''), 'answer': structured.get('answer'), 'thought': structured.get('thought', '')})
                try:
                    for agent_id, msg in zip(id_list, messages):
                        st = msg.content.get_structured_data()
                        arg_full = str(st.get('argument', '')).strip()
                        ans_full = str(st.get('answer') or '').strip()
                        print(f'[Round {round_index + 1}] Agent#{agent_id} ({roles[agent_id]})\nArgument: {arg_full}\nAnswer: {ans_full}\n')
                except Exception:
                    pass
            else:
                prompts: List[Tuple[int, str]] = []
                for agent_id in range(num_agents):
                    transcript_text = self._get_transcript_for_agent(transcript, round_index, agent_id, transcript_mode, num_agents)
                    prompt = build_agent_prompt(problem=problem, transcript_text=transcript_text, role=roles[agent_id], agent_id=agent_id, round_index=round_index, total_rounds=num_rounds)
                    prompts.append((agent_id, prompt))
                results = await self._llm.batch_generate_async(batch_messages=[[{'role': 'user', 'content': p}] for _, p in prompts])
                parsed_list = self._llm.parse_generated_texts(texts=results, parser=DebateAgentOutput, parse_mode='xml')
                for (agent_id, _), parsed in zip(prompts, parsed_list):
                    structured = parsed.get_structured_data()
                    transcript.append({'agent_id': agent_id, 'round': round_index, 'role': roles[agent_id], 'argument': structured.get('argument', ''), 'answer': structured.get('answer'), 'thought': structured.get('thought', '')})
        return transcript

    def _generate_consensus(self, problem: str, state: dict, transcript: List[dict], judge_mode: str, pruning_info: Optional[Dict[str, Any]]=None) -> dict:
        """根据 judge 模式生成最终共识（同步）。"""
        if judge_mode == 'self_consistency':
            agent_final_answers = self._collect_agent_final_answers(state, transcript)
            if len(agent_final_answers) == 0:
                agent_final_answers = [t['argument'] for t in transcript if t.get('argument')]
            sc = self._sc_ensemble.execute(solutions=agent_final_answers)
            return {'final_answer': sc['response'], 'winner': None}
        if self.judge_agent is not None:
            roles_text = '\n'.join([f'#{i}: {r}' for i, r in enumerate(state['roles'])])
            inputs = {'problem': problem, 'transcript_text': format_transcript(transcript), 'roles_text': roles_text}
            if pruning_info and pruning_info.get('mr_suggested'):
                suggested = pruning_info['mr_suggested'].get('corrected', '')
                if suggested:
                    inputs['problem'] = problem + '\n\n(Consider corrected consolidation, if helpful.)'
            msg = self.judge_agent(inputs=inputs)
            jd = msg.content.get_structured_data()
        else:
            judge_prompt = build_judge_prompt(problem=problem, transcript_text=format_transcript(transcript), roles=state['roles'])
            judge_resp = self._llm.generate(prompt=judge_prompt, parser=DebateJudgeOutput, parse_mode='xml')
            jd = judge_resp.get_structured_data()
        winner_id = int(jd.get('winning_agent_id', 0))
        final_answer = jd.get('final_answer', '')
        winner_answer = self._get_winner_answer(transcript, winner_id, state['num_rounds'])
        return {'final_answer': final_answer, 'winner': winner_id, 'winner_answer': winner_answer, 'rationale': jd.get('rationale', '')}

    async def _generate_consensus_async(self, problem: str, state: dict, transcript: List[dict], judge_mode: str, pruning_info: Optional[Dict[str, Any]]=None) -> dict:
        """根据 judge 模式生成最终共识（异步）。"""
        if judge_mode == 'self_consistency':
            agent_final_answers = self._collect_agent_final_answers(state, transcript)
            if len(agent_final_answers) == 0:
                agent_final_answers = [t['argument'] for t in transcript if t.get('argument')]
            sc = await self._sc_ensemble.async_execute(solutions=agent_final_answers)
            return {'final_answer': sc['response'], 'winner': None}
        if self.judge_agent is not None:
            roles_text = '\n'.join([f'#{i}: {r}' for i, r in enumerate(state['roles'])])
            inputs = {'problem': problem, 'transcript_text': format_transcript(transcript), 'roles_text': roles_text}
            if pruning_info and pruning_info.get('mr_suggested'):
                suggested = pruning_info['mr_suggested'].get('corrected', '')
                if suggested:
                    inputs['problem'] = problem + '\n\n(Consider corrected consolidation, if helpful.)'
            msg = await self.judge_agent(inputs=inputs)
            jd = msg.content.get_structured_data()
        else:
            judge_prompt = build_judge_prompt(problem=problem, transcript_text=format_transcript(transcript), roles=state['roles'])
            judge_resp = await self._llm.async_generate(prompt=judge_prompt, parser=DebateJudgeOutput, parse_mode='xml')
            jd = judge_resp.get_structured_data()
        winner_id = int(jd.get('winning_agent_id', 0))
        final_answer = jd.get('final_answer', '')
        winner_answer = self._get_winner_answer(transcript, winner_id, state['num_rounds'])
        return {'final_answer': final_answer, 'winner': winner_id, 'winner_answer': winner_answer, 'rationale': jd.get('rationale', '')}

    def _collect_agent_final_answers(self, state: dict, transcript: List[dict]) -> List[str]:
        """收集每位辩手的最终答案（若有）。"""
        num_agents = state['num_agents']
        num_rounds = state['num_rounds']
        final_answers: List[str] = []
        for agent_id in range(num_agents):
            records = [t for t in transcript if t['agent_id'] == agent_id and t['round'] == num_rounds - 1]
            if len(records) == 0:
                continue
            ans = records[-1].get('answer')
            if ans and isinstance(ans, str) and (len(ans.strip()) > 0):
                final_answers.append(ans)
        return final_answers

    def _get_winner_answer(self, transcript: List[dict], winner_id: int, num_rounds: int) -> Optional[str]:
        """获取获胜者在最后一轮的答案。"""
        records = [t for t in transcript if t['agent_id'] == winner_id and t['round'] == num_rounds - 1]
        if len(records) == 0:
            return None
        answer = records[-1].get('answer')
        if answer and isinstance(answer, str) and (len(answer.strip()) > 0):
            return answer.strip()
        argument = records[-1].get('argument', '')
        return argument.strip() if argument else None

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """保存模块配置（直接保存agents，不保存llm_config_pool）"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        agent_pool_path = path.replace('.json', '_agents.json')
        if self.debater_agents:
            agent_data = []
            for i, agent in enumerate(self.debater_agents):
                agent_path = agent_pool_path.replace('.json', f'_{i}.json')
                agent.save_module(agent_path)
                agent_data.append({'name': agent.name, 'description': agent.description, 'file_path': agent_path})
            with open(agent_pool_path, 'w', encoding='utf-8') as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)
        judge_agent_path = path.replace('.json', '_judge.json')
        if self.judge_agent:
            self.judge_agent.save_module(judge_agent_path)
        config = {'llm_config': self._serialize_llm_config(self.llm_config), 'name': self.name, 'description': self.description, 'agent_pool_file': agent_pool_path if self.debater_agents else None, 'judge_agent_file': judge_agent_path if self.judge_agent else None}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f'模块配置已保存到: {path}')
        return path

    def get_config(self) -> dict:
        """获取当前模块的配置字典（不包含llm_config_pool）"""
        config = {'llm_config': self._serialize_llm_config(self.llm_config), 'name': self.name, 'description': self.description}
        if self.debater_agents:
            agent_data = []
            for agent in self.debater_agents:
                agent_info = {'name': agent.name, 'description': agent.description, 'config': agent.get_config()}
                agent_data.append(agent_info)
            config['debater_agents'] = agent_data
        if self.judge_agent:
            config['judge_agent'] = {'name': self.judge_agent.name, 'description': self.judge_agent.description, 'config': self.judge_agent.get_config()}
        return config

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> 'MultiAgentDebateActionGraph':
        """从配置字典创建MultiAgentDebateActionGraph实例（不重建llm_config_pool）"""
        instance = cls()
        if data.get('llm_config'):
            instance.llm_config = instance._deserialize_llm_config(data['llm_config'])
        if data.get('name'):
            instance.name = data['name']
        if data.get('description'):
            instance.description = data['description']
        if data.get('debater_agents'):
            agents = []
            for agent_info in data['debater_agents']:
                try:
                    agent_config = agent_info.get('config', {})
                    llm_config = instance._deserialize_llm_config(agent_config.get('llm_config'))
                    agent_config_clean = {k: v for k, v in agent_config.items() if k not in ['name', 'description', 'llm_config']}
                    agent = CustomizeAgent(name=agent_info['name'], description=agent_info['description'], llm_config=llm_config, **agent_config_clean)
                    agents.append(agent)
                except Exception as e:
                    print(f'警告: 重建agent {agent_info.get('name', 'unknown')}失败: {e}')
                    continue
            instance.debater_agents = agents
        if data.get('judge_agent'):
            try:
                judge_info = data['judge_agent']
                judge_config = judge_info.get('config', {})
                llm_config = instance._deserialize_llm_config(judge_config.get('llm_config'))
                judge_config_clean = {k: v for k, v in judge_config.items() if k not in ['name', 'description', 'llm_config']}
                instance.judge_agent = CustomizeAgent(name=judge_info['name'], description=judge_info['description'], llm_config=llm_config, **judge_config_clean)
            except Exception as e:
                print(f'警告: 重建judge agent失败: {e}')
        return instance

    @classmethod
    def load_module(cls, path: str, llm_config: LLMConfig=None, **kwargs) -> 'MultiAgentDebateActionGraph':
        """从文件加载MultiAgentDebateActionGraph实例（类方法，不重建llm_config_pool）"""
        if not os.path.exists(path):
            raise FileNotFoundError(f'模块配置文件不存在: {path}')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f'配置文件格式错误: {e}')
        except Exception as e:
            raise RuntimeError(f'读取配置文件失败: {e}')
        instance = cls()
        if config.get('llm_config'):
            try:
                instance.llm_config = instance._deserialize_llm_config(config['llm_config'])
            except Exception as e:
                print(f'警告: 重建llm_config失败: {e}')
        if config.get('name'):
            instance.name = config['name']
        if config.get('description'):
            instance.description = config['description']
        agent_pool_file = config.get('agent_pool_file')
        if agent_pool_file and os.path.exists(agent_pool_file):
            try:
                with open(agent_pool_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                agents = []
                for agent_info in agent_data:
                    try:
                        agent_path = agent_info.get('file_path')
                        if agent_path and os.path.exists(agent_path):
                            agent = CustomizeAgent.from_file(path=agent_path, llm_config=instance.llm_config or llm_config)
                            agents.append(agent)
                        else:
                            print(f'警告: agent文件不存在: {agent_path}')
                    except Exception as e:
                        print(f'警告: 加载agent {agent_info.get('name', 'unknown')}失败: {e}')
                        continue
                instance.debater_agents = agents
                print(f'从 {agent_pool_file} 加载了 {len(agents)} 个agents')
            except Exception as e:
                print(f'警告: 加载agent pool失败: {e}')
        judge_agent_file = config.get('judge_agent_file')
        if judge_agent_file and os.path.exists(judge_agent_file):
            try:
                instance.judge_agent = CustomizeAgent.from_file(path=judge_agent_file, llm_config=instance.llm_config or llm_config)
                print(f'从 {judge_agent_file} 加载了judge agent')
            except Exception as e:
                print(f'警告: 加载judge agent失败: {e}')
        print(f'从 {path} 加载了模块配置')
        return instance

    def _serialize_llm_config(self, llm_config) -> Optional[Dict[str, Any]]:
        """序列化LLM配置（只保存模型名称和基本参数）"""
        if not llm_config:
            return None
        config_info = {'model': llm_config.model if hasattr(llm_config, 'model') else None, 'temperature': llm_config.temperature if hasattr(llm_config, 'temperature') else None, 'config_type': type(llm_config).__name__}
        return config_info

    def _deserialize_llm_config(self, config_info: Optional[Dict[str, Any]]) -> Optional[LLMConfig]:
        """反序列化LLM配置（从环境变量重建）"""
        if not config_info:
            return None
        config_type = config_info.get('config_type', 'OpenAILLMConfig')
        if config_type == 'OpenAILLMConfig':
            from ...models.model_configs import OpenAILLMConfig
            return OpenAILLMConfig(model=config_info.get('model', 'gpt-4o-mini'), openai_key=os.getenv('OPENAI_API_KEY'))
        elif config_type == 'OpenRouterConfig':
            from ...models.model_configs import OpenRouterConfig
            return OpenRouterConfig(model=config_info.get('model', 'meta-llama/llama-3.1-70b-instruct'), openrouter_key=os.getenv('OPENROUTER_API_KEY'))
        return None

def _create_debater_agent_with_llm(self, llm_cfg: LLMConfig) -> CustomizeAgent:
    """Create a debater agent with given LLM configuration that is consistent with default structure."""
    return CustomizeAgent(name='DebaterAgent', description='Generate argument/rebuttal and optional answer per debate round.', prompt=DEBATER_AGENT_PROMPT, llm_config=llm_cfg, inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'transcript_text', 'type': 'str', 'description': 'Formatted debate transcript so far'}, {'name': 'role', 'type': 'str', 'description': 'Debater role/persona'}, {'name': 'agent_id', 'type': 'str', 'description': 'Debater id (string)'}, {'name': 'round_index', 'type': 'str', 'description': '1-based round index'}, {'name': 'total_rounds', 'type': 'str', 'description': 'Total rounds'}], outputs=[{'name': 'thought', 'type': 'str', 'description': 'Brief reasoning', 'required': True}, {'name': 'argument', 'type': 'str', 'description': 'Argument or rebuttal', 'required': True}, {'name': 'answer', 'type': 'str', 'description': 'Optional current answer', 'required': False}], parse_mode='xml')

@classmethod
def from_dict(cls, data: Dict[str, Any], **kwargs) -> 'MultiAgentDebateActionGraph':
    """从配置字典创建MultiAgentDebateActionGraph实例（不重建llm_config_pool）"""
    instance = cls()
    if data.get('llm_config'):
        instance.llm_config = instance._deserialize_llm_config(data['llm_config'])
    if data.get('name'):
        instance.name = data['name']
    if data.get('description'):
        instance.description = data['description']
    if data.get('debater_agents'):
        agents = []
        for agent_info in data['debater_agents']:
            try:
                agent_config = agent_info.get('config', {})
                llm_config = instance._deserialize_llm_config(agent_config.get('llm_config'))
                agent_config_clean = {k: v for k, v in agent_config.items() if k not in ['name', 'description', 'llm_config']}
                agent = CustomizeAgent(name=agent_info['name'], description=agent_info['description'], llm_config=llm_config, **agent_config_clean)
                agents.append(agent)
            except Exception as e:
                print(f'警告: 重建agent {agent_info.get('name', 'unknown')}失败: {e}')
                continue
        instance.debater_agents = agents
    if data.get('judge_agent'):
        try:
            judge_info = data['judge_agent']
            judge_config = judge_info.get('config', {})
            llm_config = instance._deserialize_llm_config(judge_config.get('llm_config'))
            judge_config_clean = {k: v for k, v in judge_config.items() if k not in ['name', 'description', 'llm_config']}
            instance.judge_agent = CustomizeAgent(name=judge_info['name'], description=judge_info['description'], llm_config=llm_config, **judge_config_clean)
        except Exception as e:
            print(f'警告: 重建judge agent失败: {e}')
    return instance

class GreedyLoggerOptimizer(BaseCodeBlockOptimizer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.best = None
        self.best_score = -float('inf') if self.maximize else float('inf')

    def sample_cfg(self):
        return {'sampler_temperature': random.uniform(0.3, 1.3), 'sampler_top_p': random.uniform(0.5, 1.0), 'sys_prompt': random.choice(['You are a helpful assistant.', 'You are a super-concise assistant.'])}

    def update(self, cfg, score):
        if self.maximize and score > self.best_score or (not self.maximize and score < self.best_score):
            self.best = cfg
            self.best_score = score
            print(f'[New Best] score={score:.3f} cfg={cfg}')

def update(self, cfg, score):
    if self.maximize and score > self.best_score or (not self.maximize and score < self.best_score):
        self.best = cfg
        self.best_score = score
        print(f'[New Best] score={score:.3f} cfg={cfg}')

class SEWOptimizer(Optimizer):
    graph: Union[SequentialWorkFlowGraph, ActionGraph] = Field(description='The workflow to optimize.')
    repr_scheme: str = Field(default='python', description='The scheme to represent the workflow.')
    optimize_mode: Literal['all', 'structure', 'prompt'] = Field(default='all', description='The mode to optimize the workflow.')
    order: Literal['zero-order', 'first-order'] = Field(default='zero-order', description='Whether to use zero-order (using hyper-mutation prompt) or first-order (using mutation prompt) optimization.')

    def init_module(self, **kwargs):
        self._snapshot: List[dict] = []
        self._prompt_breeder = SimplePromptBreeder(llm=self.llm)
        self._convergence_check_counter = 0
        self._best_score = float('-inf')
        if isinstance(self.graph, ActionGraph):
            if self.optimize_mode != 'prompt':
                raise ValueError(f'{type(self).__name__} only support prompt optimization when `graph` is an `ActionGraph`. The `optimize_mode` should be set to `prompt`, but got {self.optimize_mode}.')

    def optimize(self, dataset: Benchmark, **kwargs):
        if isinstance(self.graph, SequentialWorkFlowGraph):
            logger.info(f'Optimizing the {type(self.graph).__name__} workflow with {self.repr_scheme} representation.')
        elif isinstance(self.graph, ActionGraph):
            logger.info(f'Optimizing the {type(self.graph).__name__} graph ...')
        graph: Union[SequentialWorkFlowGraph, ActionGraph] = self.graph
        logger.info('Run initial evaluation on the original workflow ...')
        with suppress_logger_info():
            metrics = self.evaluate(dataset, eval_mode='dev', graph=graph)
        logger.info(f'Initial metrics: {metrics}')
        self.log_snapshot(graph=graph, metrics=metrics)
        for i in range(self.max_steps):
            try:
                graph = self.step()
                if (i + 1) % self.eval_every_n_steps == 0:
                    logger.info(f'Evaluate the workflow at step {i + 1} ...')
                    with suppress_logger_info():
                        metrics = self.evaluate(dataset, eval_mode='dev')
                    logger.info(f'Step {i + 1} metrics: {metrics}')
                    self.log_snapshot(graph=graph, metrics=metrics)
            except Exception as e:
                logger.warning(f'Error in step {i}: {e}. Skip this step.')
                continue
            if self.convergence_check():
                logger.info(f'Convergence check passed at step {i + 1}. Stop the optimization.')
                break
        if i == self.max_steps - 1:
            logger.info(f'Reach the maximum number of steps {self.max_steps}. Stop the optimization.')
        logger.info('Restore the best graph from the snapshot ...')
        self.restore_best_graph()

    def step(self, **kwargs) -> Union[SequentialWorkFlowGraph, ActionGraph]:
        """
        Take a step of optimization and return the optimized graph.
        """
        graph = self._select_graph_with_highest_score(return_metrics=False)
        if isinstance(graph, SequentialWorkFlowGraph):
            new_graph = self._workflow_graph_step(graph)
        elif isinstance(graph, ActionGraph):
            new_graph = self._action_graph_step(graph)
        else:
            raise ValueError(f'Invalid graph type: {type(graph)}. The graph should be an instance of `WorkFlowGraph` or `ActionGraph`.')
        return new_graph

    def evaluate(self, dataset: Benchmark, eval_mode: str='test', graph: Optional[Union[SequentialWorkFlowGraph, ActionGraph]]=None, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, **kwargs) -> dict:
        """
        Evaluate the workflow. If `graph` is provided, use the provided graph for evaluation. Otherwise, use the graph in the optimizer. 
        
        Args:
            dataset (Benchmark): The dataset to evaluate the workflow on.
            eval_mode (str): The evaluation mode. Choices: ["test", "dev", "train"].
            graph (Union[WorkFlowGraph, ActionGraph], optional): The graph to evaluate. If not provided, use the graph in the optimizer.
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
        
        Returns:
            dict: The metrics of the workflow evaluation.
        """
        graph = graph if graph is not None else self.graph
        metrics_list = []
        for i in range(self.eval_rounds):
            eval_info = [f'[{type(graph).__name__}]', f'Evaluation round {i + 1}/{self.eval_rounds}', f'Mode: {eval_mode}']
            if indices is not None:
                eval_info.append(f'Indices: {len(indices)} samples')
            if sample_k is not None:
                eval_info.append(f'Sample size: {sample_k}')
            logger.info(' | '.join(eval_info))
            metrics = self.evaluator.evaluate(graph=graph, benchmark=dataset, eval_mode=eval_mode, indices=indices, sample_k=sample_k, **kwargs)
            metrics_list.append(metrics)
        avg_metrics = self.evaluator._calculate_average_score(metrics_list)
        return avg_metrics

    def log_snapshot(self, graph: Union[SequentialWorkFlowGraph, ActionGraph], metrics: dict):
        if isinstance(graph, SequentialWorkFlowGraph):
            graph_info = graph.get_graph_info()
        elif isinstance(graph, ActionGraph):
            graph_info = graph
        else:
            raise ValueError(f'Invalid graph type: {type(graph)}. The graph should be an instance of `SequentialWorkFlowGraph` or `ActionGraph`.')
        self._snapshot.append({'index': len(self._snapshot), 'graph': deepcopy(graph_info), 'metrics': metrics})

    def _select_graph_with_highest_score(self, return_metrics: bool=False) -> Union[SequentialWorkFlowGraph, ActionGraph]:
        if len(self._snapshot) == 0:
            return self.graph
        snapshot_scores = [np.mean(list(snapshot['metrics'].values())) for snapshot in self._snapshot]
        best_index = np.argmax(snapshot_scores)
        if isinstance(self.graph, SequentialWorkFlowGraph):
            graph = SequentialWorkFlowGraph.from_dict(self._snapshot[best_index]['graph'])
        elif isinstance(self.graph, ActionGraph):
            graph = self._snapshot[best_index]['graph']
        else:
            raise ValueError(f'Invalid graph type: {type(self.graph)}. The graph should be an instance of `SequentialWorkFlowGraph` or `ActionGraph`.')
        if return_metrics:
            return (graph, self._snapshot[best_index]['metrics'])
        return graph

    def restore_best_graph(self):
        best_graph, best_metrics = self._select_graph_with_highest_score(return_metrics=True)
        logger.info(f'Restore the best graph from snapshot with metrics {best_metrics} ...')
        self.graph = best_graph

    def _wfg_structure_optimization_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
        """
        optinize the structure of the workflow graph and return the optimized graph.
        Args:
            graph (SequentialWorkFlowGraph): The workflow graph to optimize.
        
        Returns:
            SequentialWorkFlowGraph: The optimized workflow graph.  
        """
        graph_scheme = SEWWorkFlowScheme(graph=graph)
        graph_repr = graph_scheme.convert_to_scheme(scheme=self.repr_scheme)
        if self.repr_scheme == 'python':
            output_format = "\n\nALWAYS wrap the refined workflow in ```python\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'yaml':
            output_format = "\n\nALWAYS wrap the refined workflow in ```yaml\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'code':
            output_format = "\n\nALWAYS wrap the refined workflow in ```code\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'core':
            output_format = "\n\nALWAYS wrap the refined workflow in ```core\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'bpmn':
            output_format = "\n\nALWAYS wrap the refined workflow in ```bpmn\n``` format and DON'T include any other text within the code block!"
        else:
            raise ValueError(f'Invalid representation scheme: {self.repr_scheme}. The scheme should be one of {VALID_SCHEMES}.')
        prompt = 'Task Description: ' + graph.goal + '\n\nWorkflow Steps: ' + graph_repr + output_format
        new_graph_repr = self._prompt_breeder.generate_prompt(task_description=graph.goal, prompt=prompt, order=self.order)
        new_graph = graph_scheme.parse_from_scheme(scheme=self.repr_scheme, repr=new_graph_repr)
        return new_graph

    def _wfg_prompt_optimization_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
        task_description = graph.goal
        graph_scheme = SEWWorkFlowScheme(graph=graph)
        graph_repr = graph_scheme.convert_to_scheme(scheme=self.repr_scheme)
        graph_info = graph.get_graph_info()
        for i, task in enumerate(graph_info['tasks']):
            original_prompt = task['prompt']
            optimization_prompt = 'Task Description: ' + task_description + '\n\nWorkflow Steps:\n' + graph_repr + f'\n\nINSTRUCTION for the {i + 1}-th task:\n"""\n' + original_prompt + '\n"""'
            optimization_prompt += f'\n\nGiven the above information, please refine the instruction for the {i + 1}-th task.\n'
            optimization_prompt += 'Note that you should always use bracket (e.g. `{input_name}`) to wrap the inputs of the tasks in your refined instruction.\\n'
            optimization_prompt += "Only output the refined instruction and DON'T include any other text!"
            new_prompt = self._prompt_breeder.generate_prompt(task_description=task_description, prompt=optimization_prompt, order=self.order)
            graph_info['tasks'][i]['prompt'] = new_prompt
        new_graph = SequentialWorkFlowGraph.from_dict(graph_info)
        return new_graph

    def _workflow_graph_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
        if self.optimize_mode == 'structure' or self.optimize_mode == 'all':
            graph = self._wfg_structure_optimization_step(graph)
        if self.optimize_mode == 'prompt' or self.optimize_mode == 'all':
            graph = self._wfg_prompt_optimization_step(graph)
        return graph

    def _action_graph_prompt_optimization_step(self, graph: ActionGraph) -> ActionGraph:
        task_description = graph.description
        graph_info = graph.get_graph_info()
        graph_steps = inspect.getsource(getattr(graph, 'execute'))
        for operator_name, operator_info in graph_info['operators'].items():
            original_prompt = operator_info['prompt']
            optimization_prompt = 'Task Description: ' + task_description + '\n\nWorkflow Steps:\n' + graph_steps + f'\n\nINSTRUCTION for the `{operator_name}` operator:\n"""\n' + original_prompt + '\n"""'
            optimization_prompt += '\n\nThe interface of the operator is as follows:\n' + operator_info['interface']
            optimization_prompt += f'\n\nGiven the above information, please refine the instruction for the `{operator_name}` operator.\n'
            optimization_prompt += 'Note that you should always use bracket (e.g. `{input_name}`) to wrap the inputs of the operator in your refined instruction, '
            optimization_prompt += "and the input names should be EXACTLY the same as those defined in the interface. DON'T use bracket to wrap output names."
            optimization_prompt += "\nOnly output the refined instruction and DON'T include any other text!"
            new_prompt = self._prompt_breeder.generate_prompt(task_description=task_description, prompt=optimization_prompt, order=self.order)
            new_prompt = new_prompt.replace('"', '').strip()
            graph_info['operators'][operator_name]['prompt'] = new_prompt
        new_graph = ActionGraph.from_dict(graph_info)
        return new_graph

    def _action_graph_step(self, graph: ActionGraph) -> ActionGraph:
        if self.optimize_mode == 'prompt':
            graph = self._action_graph_prompt_optimization_step(graph)
        else:
            raise ValueError(f'{type(self).__name__} only support prompt optimization when `self.graph` is an `ActionGraph` instance. The `optimize_mode` should be set to `prompt`, but got {self.optimize_mode}.')
        return graph

    def convergence_check(self, **kwargs) -> bool:
        if not self._snapshot:
            logger.warning('No snapshots available for convergence check')
            return False
        scores = [np.mean(list(snapshot['metrics'].values())) for snapshot in self._snapshot]
        current_score = scores[-1]
        if current_score > self._best_score:
            self._best_score = current_score
            self._convergence_check_counter = 0
        else:
            self._convergence_check_counter += 1
        if self._convergence_check_counter >= self.convergence_threshold:
            logger.info(f'Early stopping triggered: No improvement for {self.convergence_threshold} iterations')
            return True
        return False

    def save(self, path: str, ignore: List[str]=[]):
        """
        Save the (optimized) workflow graph to a file. 

        Args:
            path (str): The path to save the workflow graph.
            ignore (List[str]): The keys to ignore when saving the workflow graph.
        """
        self.graph.save_module(path, ignore=ignore)

def optimize(self, dataset: Benchmark, **kwargs):
    if isinstance(self.graph, SequentialWorkFlowGraph):
        logger.info(f'Optimizing the {type(self.graph).__name__} workflow with {self.repr_scheme} representation.')
    elif isinstance(self.graph, ActionGraph):
        logger.info(f'Optimizing the {type(self.graph).__name__} graph ...')
    graph: Union[SequentialWorkFlowGraph, ActionGraph] = self.graph
    logger.info('Run initial evaluation on the original workflow ...')
    with suppress_logger_info():
        metrics = self.evaluate(dataset, eval_mode='dev', graph=graph)
    logger.info(f'Initial metrics: {metrics}')
    self.log_snapshot(graph=graph, metrics=metrics)
    for i in range(self.max_steps):
        try:
            graph = self.step()
            if (i + 1) % self.eval_every_n_steps == 0:
                logger.info(f'Evaluate the workflow at step {i + 1} ...')
                with suppress_logger_info():
                    metrics = self.evaluate(dataset, eval_mode='dev')
                logger.info(f'Step {i + 1} metrics: {metrics}')
                self.log_snapshot(graph=graph, metrics=metrics)
        except Exception as e:
            logger.warning(f'Error in step {i}: {e}. Skip this step.')
            continue
        if self.convergence_check():
            logger.info(f'Convergence check passed at step {i + 1}. Stop the optimization.')
            break
    if i == self.max_steps - 1:
        logger.info(f'Reach the maximum number of steps {self.max_steps}. Stop the optimization.')
    logger.info('Restore the best graph from the snapshot ...')
    self.restore_best_graph()

def save(self, path: str, ignore: List[str]=[]):
    """
        Save the (optimized) workflow graph to a file. 

        Args:
            path (str): The path to save the workflow graph.
            ignore (List[str]): The keys to ignore when saving the workflow graph.
        """
    self.graph.save_module(path, ignore=ignore)

class TextGradOptimizer(BaseModule):
    """Uses TextGrad to optimize agents' system prompts and instructions in a multi-agent workflow.
    For more information on TextGrad, see https://github.com/zou-group/textgrad.
    """
    graph: WorkFlowGraph = Field(description='The workflow to optimize.')
    optimize_mode: Literal['all', 'system_prompt', 'instruction'] = Field(default='all', description="The mode to optimize the workflow. 'all' optimizes both system prompts and instructions, 'system_prompt' only optimizes system prompts, and 'instruction' only optimizes instructions.")
    executor_llm: BaseLLM = Field(default=None, description='The LLM to use for execution.')
    optimizer_llm: BaseLLM = Field(default=None, description='The LLM to use for optimization.')
    batch_size: PositiveInt = Field(default=1, description='The batch size for optimization.')
    max_steps: PositiveInt = Field(default=10, description='The maximum number of optimization steps.')
    evaluator: Evaluator = Field(default=None, description='The evaluator to perform evaluation during optimization.')
    eval_every_n_steps: Optional[PositiveInt] = Field(default=None, description='Evaluate the workflow every `eval_every_n_steps` steps.')
    eval_rounds: PositiveInt = Field(default=1, description='The number of times to evaluate the performance.')
    eval_config: dict = Field(default={}, description='The configuration for evaluation. The keys are the arguments of `TextGradOptimizer.evaluate`.')
    save_interval: Optional[PositiveInt] = Field(default=None, description='Save the workflow every `save_interval` steps.')
    save_path: str = Field(default='./', description='The path to save the optimized workflow.')
    rollback: bool = Field(default=True, description='Whether to rollback to the best graph after each evaluation during optimization.')
    constraints: List[str] = Field(default=[], description="The constraints for optimization. e.g. ['They system prompt must not exceed 100 words.']")

    def init_module(self, **kwargs):
        self._validate_graph_compatibility(self.graph)
        self._snapshot: List[dict] = []
        self.output_lookup = self._create_output_lookup()

    def _init_textgrad(self, dataset: Benchmark, use_answers: bool=True):

        def disable_short_variable_value(self, n_words_offset: int=10):
            return self.value
        Variable.get_short_value = disable_short_variable_value
        self.optimizer_engine = TextGradEngine(self.optimizer_llm)
        if use_answers:
            if isinstance(dataset, CodingBenchmark):
                loss_prompt = CODE_LOSS_PROMPT
                role_descriptions = ['code snippet to evaluate', 'the task, the test result of the code snippet, and the correct code']
            else:
                loss_prompt = GENERAL_LOSS_PROMPT
                role_descriptions = ['response to evaluate', 'correct answer']
            evaluation_instruction = Variable(loss_prompt, requires_grad=False, role_description='evaluation instruction')
            self.loss_fn = MultiFieldEvaluation(evaluation_instruction, role_descriptions, self.optimizer_engine)
        else:
            loss_prompt = NO_ANSWER_LOSS_PROMPT
            evaluation_instruction = Variable(loss_prompt, requires_grad=False, role_description='evaluation instruction')
            self.loss_fn = TextLoss(evaluation_instruction, self.optimizer_engine)
        self._create_textgrad_agents()
        if self.optimize_mode == 'all':
            optimize_variables = self._get_all_system_prompts() + self._get_all_instructions()
        elif self.optimize_mode == 'system_prompt':
            optimize_variables = self._get_all_system_prompts()
        elif self.optimize_mode == 'instruction':
            optimize_variables = self._get_all_instructions()
        else:
            raise ValueError("Unsupported `optimize_mode`, should be one of 'all', 'system_prompt', 'instruction'.")
        OPTIMIZER_CONSTRAINTS.extend(self.constraints)
        self.textgrad_optimizer = TextualGradientDescent(parameters=optimize_variables, engine=self.optimizer_engine, constraints=OPTIMIZER_CONSTRAINTS, optimizer_system_prompt=OPTIMIZER_SYSTEM_PROMPT, in_context_examples=[PERSONAL_FINANCE_ADVISOR_EXAMPLE, FITNESS_COACH_EXAMPLE, CODE_REVIEW_EXAMPLE])

    def optimize(self, dataset: Benchmark, use_answers: bool=True, seed: Optional[int]=None) -> None:
        """Optimizes self.graph using `dataset`.
        
        Args:
            dataset (Benchmark): The dataset to use for optimization.
            use_answers (bool): Whether to use the answers (labels) in the training set for optimization.
                If False, `dataset`'s training set does not need to have answers.
                If `eval_every_n_steps` is set to None, we can optimize the workflow without any labeled data.
            seed (Optional[int]): The random seed to use for shuffling the data.
        """
        self._init_textgrad(dataset, use_answers)

        def iterator() -> Iterator[Tuple[List[dict[str, str]], Optional[List[Union[str, dict[str, str]]]]]]:
            epoch = 0
            while True:
                effective_seed = seed + epoch if seed is not None else None
                train_data = dataset.get_train_data(sample_k=len(dataset._train_data), seed=effective_seed)
                for i in range(0, len(train_data), self.batch_size):
                    batch = train_data[i:i + self.batch_size]
                    inputs = [self.evaluator.collate_func(x) for x in batch]
                    if use_answers:
                        labels = dataset.get_labels(batch)
                    else:
                        labels = None
                    yield (inputs, labels)
                epoch += 1
        data_iterator = iterator()
        for step in tqdm(range(self.max_steps)):
            inputs, labels = next(data_iterator)
            self.step(inputs, labels, dataset, use_answers)
            if self.eval_every_n_steps is not None and (step + 1) % self.eval_every_n_steps == 0:
                logger.info(f'Evaluating the workflow at step {step + 1} ...')
                with suppress_logger_info():
                    metrics = self.evaluate(dataset, **self.eval_config)
                self.log_snapshot(self.graph, metrics)
                logger.info(f'Step {step + 1} metrics: {metrics}')
                if self.rollback:
                    if len(self._snapshot) == 1:
                        best_snapshot = self._snapshot[-1]
                        best_average_score = np.mean(list(metrics.values()))
                    else:
                        current_average_score = np.mean(list(metrics.values()))
                        if current_average_score >= best_average_score:
                            best_snapshot = self._snapshot[-1]
                            best_average_score = current_average_score
                        else:
                            logger.info(f'Metrics are worse than the best snapshot which has {best_snapshot['metrics']}. Rolling back to the best snapshot.')
                            best_graph = WorkFlowGraph.from_dict(best_snapshot['graph'])
                            self.graph = best_graph
                            self._create_textgrad_agents()
            if self.save_interval is not None and (step + 1) % self.save_interval == 0:
                logger.info(f'Saving the workflow at step {step + 1} ...')
                self.save(os.path.join(self.save_path, f'{dataset.name}_textgrad_step_{step + 1}.json'))
        logger.info(f'Reached the maximum number of steps {self.max_steps}. Optimization has finished.')
        self.save(os.path.join(self.save_path, f'{dataset.name}_textgrad_final.json'))
        if len(self._snapshot) > 0:
            best_graph = self._select_graph_with_highest_score()
            self.save(os.path.join(self.save_path, f'{dataset.name}_textgrad_best.json'), graph=best_graph)

    def step(self, inputs: list[dict[str, str]], labels: Optional[list[Union[str, dict[str, str]]]], dataset: Benchmark, use_answers: bool=True) -> None:
        """Performs one optimization step using a batch of data."""
        losses = []
        logger.info('Executing workflow...')
        if use_answers:
            if labels is None:
                raise ValueError('Labels must be provided if `use_answers` is True.')
            for input, label in zip(inputs, labels, strict=True):
                output = self.forward(input)
                if isinstance(label, str):
                    label = Variable(label, requires_grad=False, role_description='correct answer for the query')
                elif isinstance(label, dict):
                    if not isinstance(dataset, CodingBenchmark):
                        raise ValueError('Label must be a string for non-coding benchmarks.')
                    end_node_name = self.graph.find_end_nodes()[0]
                    end_node = self.graph.get_node(end_node_name)
                    output_name = end_node.outputs[0].name
                    code = output.parsed_outputs[output_name]
                    label = self._format_code_label(code, label, dataset)
                    label = Variable(label, requires_grad=False, role_description='the task, the test result, and the correct code')
                loss = self.loss_fn([output, label])
                losses.append(loss)
        else:
            for input in inputs:
                output = self.forward(input)
                loss = self.loss_fn(output)
                losses.append(loss)
        total_loss = tg.sum(losses)
        logger.info('Computing gradients...')
        total_loss.backward(self.optimizer_engine)
        logger.info('Updating agents...')
        self.textgrad_optimizer.step()
        self.textgrad_optimizer.zero_grad()
        self._update_workflow_graph()
        logger.info('Agents updated')

    def forward(self, inputs: dict[str, str]) -> Variable:
        """Returns the final output from the workflow."""
        self._visited_nodes = set()
        end_node = self.graph.find_end_nodes()[0]
        input_variables = self._initial_inputs_to_variables(inputs)
        output = self._compute_node(end_node, input_variables)
        return output

    def evaluate(self, dataset: Benchmark, eval_mode: str='dev', graph: Optional[WorkFlowGraph]=None, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, **kwargs) -> dict:
        """Evaluate the workflow. If `graph` is provided, use the provided graph for evaluation. Otherwise, use the graph in the optimizer. 
        
        Args:
            dataset (Benchmark): The dataset to evaluate the workflow on.
            eval_mode (str): The evaluation mode. Choices: ["test", "dev", "train"].
            graph (WorkFlowGraph, optional): The graph to evaluate. If not provided, use the graph in the optimizer.
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
        
        Returns:
            dict: The metrics of the workflow evaluation.
        """
        if graph is None:
            graph = self.graph
        metrics_list = []
        for i in range(self.eval_rounds):
            eval_info = [f'[{type(graph).__name__}]', f'Evaluation round {i + 1}/{self.eval_rounds}', f'Mode: {eval_mode}']
            if indices is not None:
                eval_info.append(f'Indices: {len(indices)} samples')
            if sample_k is not None:
                eval_info.append(f'Sample size: {sample_k}')
            logger.info(' | '.join(eval_info))
            metrics = self.evaluator.evaluate(graph=graph, benchmark=dataset, eval_mode=eval_mode, indices=indices, sample_k=sample_k, update_agents=True, **kwargs)
            metrics_list.append(metrics)
        avg_metrics = self.evaluator._calculate_average_score(metrics_list)
        return avg_metrics

    def save(self, path: str, graph: Optional[WorkFlowGraph]=None, ignore: List[str]=[]) -> None:
        """Save the workflow graph containing the optimized prompts to a file. 

        Args:
            path (str): The path to save the workflow graph.
            graph (WorkFlowGraph, optional): The graph to save. If not provided, use the graph in the optimizer.
            ignore (List[str]): The keys to ignore when saving the workflow graph.
        """
        if graph is None:
            graph = self.graph
        graph.save_module(path, ignore=ignore)

    def log_snapshot(self, graph: WorkFlowGraph, metrics: dict) -> None:
        """Log the snapshot of the workflow."""
        self._snapshot.append({'index': len(self._snapshot), 'graph': deepcopy(graph.get_config()), 'metrics': metrics})

    def restore_best_graph(self) -> None:
        """Restore the best graph from the snapshot and set it to `self.graph`."""
        if len(self._snapshot) == 0:
            logger.info('No snapshot found. No graph to restore.')
            return
        best_graph, best_metrics = self._select_graph_with_highest_score(return_metrics=True)
        self.graph = best_graph
        logger.info(f'Restored the best graph from snapshot with metrics {best_metrics}')

    def _format_code_label(self, code: str, label: dict[str, str], dataset: CodingBenchmark) -> str:
        """Formats the label for coding tasks to include the task, the test result, and the correct code.

        Args:
            code: The code to evaluate.
            label: A dictionary with keys "task_id", "test", "entry_point", and "canonical_solution".
            dataset: A CodingBenchmark instance with `check_solution` method.
        
        Returns:
            The formatted label which includes the task, the test result, and the correct code.
        """
        task_id = label['task_id']
        prompt = dataset.get_example_by_id(task_id)['prompt']
        test = label['test']
        entry_point = label['entry_point']
        state, message = dataset.check_solution(task_id=task_id, solution=prompt + '\n' + code, test=test, entry_point=entry_point)
        if state != dataset.SUCCESS:
            message = message.replace('Solution', 'Failed Code')
        formatted_label = f'## Task:\n{prompt}\n\n## Result on test:\n{message}\n\n## Correct Solution:\n{label['canonical_solution']}'
        return formatted_label

    def _initial_inputs_to_variables(self, initial_inputs: dict[str, str]) -> dict[str, Variable]:
        """Converts inputs to the initial nodes to textgrad variables."""
        variables = {}
        initial_nodes = self.graph.find_initial_nodes()
        for initial_node in initial_nodes:
            for key, value in initial_inputs.items():
                for input in self.graph.get_node(initial_node).inputs:
                    if input.name == key:
                        initial_input_variable = Variable(value, requires_grad=False, role_description=input.description)
                        variables[key] = initial_input_variable
                        if len(variables) == len(initial_inputs):
                            return variables
        missing_inputs = set(initial_inputs.keys()) - set(variables.keys())
        raise ValueError(f'Initial inputs do not match the inputs of the initial nodes. Missing inputs: {missing_inputs}')

    def _compute_node(self, node: Union[str, WorkFlowNode], initial_inputs: dict[str, Variable]) -> Variable:
        """Computes the output of a node in the workflow graph by recursively computing the required inputs.

        Args:
            node: The node to compute the output of.
            initial_inputs: The initial inputs to the workflow that are not from any node in the workflow (e.g., user query).

        Returns:
            The output of the node as a textgrad.Variable.
        """
        if isinstance(node, str):
            node = self.graph.get_node(node)
        if node.name in self._visited_nodes:
            return node.textgrad_agent.last_output
        input_variables: dict[str, Variable] = {}
        input_node_names: set[str] = set()
        for input in node.inputs:
            if input.name in initial_inputs:
                input_variables[input.name] = initial_inputs[input.name]
            else:
                input_node_names.add(self.output_lookup[input.name])
        for node_name in input_node_names:
            input_variables[node_name] = self._compute_node(node_name, initial_inputs)
        output_variable = node.textgrad_agent(input_variables)
        self._visited_nodes.add(node.name)
        return output_variable

    def _create_textgrad_agent(self, node: Union[str, WorkFlowNode]) -> TextGradAgent:
        """Creates a textgrad agent for a given node in a WorkFlowGraph."""
        if isinstance(node, str):
            node = self.graph.get_node(node)
        if isinstance(node.agents[0], dict):
            agent_llm = node.agents[0].get('llm')
            agent_llm_config = node.agents[0].get('llm_config')
            if agent_llm is None and agent_llm_config is None:
                node.agents[0]['llm'] = self.executor_llm
            agent: Union[CustomizeAgent, Agent] = CustomizeAgent.from_dict(node.agents[0])
        else:
            raise ValueError(f"Unsupported agent type {type(node.agents[0])}. Expected 'dict'.")
        textgrad_agent = TextGradAgent(agent, self.optimize_mode)
        return textgrad_agent

    def _create_textgrad_agents(self):
        """Creates textgrad agents for all nodes in the workflow graph."""
        for node in self.graph.nodes:
            node.textgrad_agent = self._create_textgrad_agent(node)

    def _update_agent_prompts(self, agent_dict: dict[str, Any], system_prompt: str, instruction: str) -> dict[str, Any]:
        agent_dict['system_prompt'] = system_prompt
        if 'actions' in agent_dict:
            agent_dict['actions'][0]['prompt_template'] = self._update_agent_instructions(agent_dict['actions'][0]['prompt_template'], instruction)
        else:
            agent_dict['prompt_template'] = self._update_agent_instructions(agent_dict['prompt_template'], instruction)
        return agent_dict

    def _update_agent_instructions(self, prompt_template: Union[PromptTemplate, dict[str, str]], instruction: str) -> Union[PromptTemplate, dict[str, str]]:
        if isinstance(prompt_template, PromptTemplate):
            prompt_template.set_instruction(instruction)
        elif isinstance(prompt_template, dict):
            prompt_template['instruction'] = instruction
        else:
            raise ValueError(f"Unsupported prompt template type {type(prompt_template)}. Expected 'PromptTemplate' or 'dict'.")
        return prompt_template

    def _update_workflow_graph(self):
        """Updates the workflow graph with the latest prompts from the textgrad optimization."""
        for node in self.graph.nodes:
            if isinstance(node.agents[0], dict):
                node.agents[0] = self._update_agent_prompts(node.agents[0], node.textgrad_agent.system_prompt.value, node.textgrad_agent.instruction.value)
            else:
                raise ValueError(f"Unsupported agent type {type(node.agents[0])}. Expected 'dict'.")

    def _select_graph_with_highest_score(self, return_metrics: bool=False) -> Union[WorkFlowGraph, tuple[WorkFlowGraph, Optional[dict]]]:
        """Select the graph in `self._snapshot` with the highest score."""
        if len(self._snapshot) == 0:
            if return_metrics:
                return (self.graph, None)
            return self.graph
        snapshot_scores = [np.mean(list(snapshot['metrics'].values())) for snapshot in self._snapshot]
        best_index = np.argmax(snapshot_scores)
        graph = WorkFlowGraph.from_dict(self._snapshot[best_index]['graph'])
        if return_metrics:
            return (graph, self._snapshot[best_index]['metrics'])
        return graph

    def _get_all_system_prompts(self) -> List[Variable]:
        """Gets all system prompts from the textgrad agents."""
        system_prompts = []
        for node in self.graph.nodes:
            system_prompts.append(node.textgrad_agent.system_prompt)
        return system_prompts

    def _get_all_instructions(self) -> List[Variable]:
        """Gets all prompt templates from the textgrad agents."""
        instructions = []
        for node in self.graph.nodes:
            instructions.append(node.textgrad_agent.instruction)
        return instructions

    def _create_output_lookup(self) -> dict[str, str]:
        """Creates a lookup table for output names to node names."""
        output_name_to_node_name = {}
        for node in self.graph.nodes:
            for output in node.outputs:
                output_name_to_node_name[output.name] = node.name
        return output_name_to_node_name

    def _validate_graph_compatibility(self, graph: WorkFlowGraph) -> None:
        """Checks if the graph is compatible with the textgrad optimizer."""
        for node in graph.nodes:
            if len(node.agents) > 1:
                raise ValueError('TextGrad optimizer only supports workflows where every node only has a single agent.')
            else:
                agent = node.agents[0]
                if not isinstance(agent, dict):
                    raise ValueError(f"Unsupported agent type {type(agent)}. Expected 'dict'.")
                elif 'actions' in agent:
                    non_ContextExtraction_actions = [action for action in agent['actions'] if action['class_name'] != 'ContextExtraction']
                    if len(non_ContextExtraction_actions) > 1:
                        raise ValueError(f'TextGrad optimizer only supports workflows where every agent only has a single action. {agent['name']} has {len(non_ContextExtraction_actions)} actions.')
                    if 'prompt_template' not in non_ContextExtraction_actions[0]:
                        raise ValueError(f'Please provide a PromptTemplate for {agent['name']}.')
                elif 'prompt_template' not in agent:
                    raise ValueError(f'Please provide a PromptTemplate for {agent['name']}.')

def optimize(self, dataset: Benchmark, use_answers: bool=True, seed: Optional[int]=None) -> None:
    """Optimizes self.graph using `dataset`.
        
        Args:
            dataset (Benchmark): The dataset to use for optimization.
            use_answers (bool): Whether to use the answers (labels) in the training set for optimization.
                If False, `dataset`'s training set does not need to have answers.
                If `eval_every_n_steps` is set to None, we can optimize the workflow without any labeled data.
            seed (Optional[int]): The random seed to use for shuffling the data.
        """
    self._init_textgrad(dataset, use_answers)

    def iterator() -> Iterator[Tuple[List[dict[str, str]], Optional[List[Union[str, dict[str, str]]]]]]:
        epoch = 0
        while True:
            effective_seed = seed + epoch if seed is not None else None
            train_data = dataset.get_train_data(sample_k=len(dataset._train_data), seed=effective_seed)
            for i in range(0, len(train_data), self.batch_size):
                batch = train_data[i:i + self.batch_size]
                inputs = [self.evaluator.collate_func(x) for x in batch]
                if use_answers:
                    labels = dataset.get_labels(batch)
                else:
                    labels = None
                yield (inputs, labels)
            epoch += 1
    data_iterator = iterator()
    for step in tqdm(range(self.max_steps)):
        inputs, labels = next(data_iterator)
        self.step(inputs, labels, dataset, use_answers)
        if self.eval_every_n_steps is not None and (step + 1) % self.eval_every_n_steps == 0:
            logger.info(f'Evaluating the workflow at step {step + 1} ...')
            with suppress_logger_info():
                metrics = self.evaluate(dataset, **self.eval_config)
            self.log_snapshot(self.graph, metrics)
            logger.info(f'Step {step + 1} metrics: {metrics}')
            if self.rollback:
                if len(self._snapshot) == 1:
                    best_snapshot = self._snapshot[-1]
                    best_average_score = np.mean(list(metrics.values()))
                else:
                    current_average_score = np.mean(list(metrics.values()))
                    if current_average_score >= best_average_score:
                        best_snapshot = self._snapshot[-1]
                        best_average_score = current_average_score
                    else:
                        logger.info(f'Metrics are worse than the best snapshot which has {best_snapshot['metrics']}. Rolling back to the best snapshot.')
                        best_graph = WorkFlowGraph.from_dict(best_snapshot['graph'])
                        self.graph = best_graph
                        self._create_textgrad_agents()
        if self.save_interval is not None and (step + 1) % self.save_interval == 0:
            logger.info(f'Saving the workflow at step {step + 1} ...')
            self.save(os.path.join(self.save_path, f'{dataset.name}_textgrad_step_{step + 1}.json'))
    logger.info(f'Reached the maximum number of steps {self.max_steps}. Optimization has finished.')
    self.save(os.path.join(self.save_path, f'{dataset.name}_textgrad_final.json'))
    if len(self._snapshot) > 0:
        best_graph = self._select_graph_with_highest_score()
        self.save(os.path.join(self.save_path, f'{dataset.name}_textgrad_best.json'), graph=best_graph)

def save(self, path: str, graph: Optional[WorkFlowGraph]=None, ignore: List[str]=[]) -> None:
    """Save the workflow graph containing the optimized prompts to a file. 

        Args:
            path (str): The path to save the workflow graph.
            graph (WorkFlowGraph, optional): The graph to save. If not provided, use the graph in the optimizer.
            ignore (List[str]): The keys to ignore when saving the workflow graph.
        """
    if graph is None:
        graph = self.graph
    graph.save_module(path, ignore=ignore)

class MiproOptimizer(BaseOptimizer, MIPROv2):

    def __init__(self, registry: ParamRegistry, program: Callable, optimizer_llm: BaseLLM, evaluator: Optional[Callable]=None, eval_rounds: Optional[int]=1, metric_threshold: Optional[float]=None, max_bootstrapped_demos: int=4, max_labeled_demos: int=4, auto: Optional[Literal['light', 'medium', 'heavy']]='medium', max_steps: int=None, num_candidates: Optional[int]=None, num_threads: Optional[int]=None, max_errors: int=10, seed: int=9, init_temperature: float=0.5, track_stats: bool=True, save_path: Optional[str]=None, minibatch: bool=True, minibatch_size: int=35, minibatch_full_eval_steps: int=5, program_aware_proposer: bool=True, data_aware_proposer: bool=True, view_data_batch_size: int=10, tip_aware_proposer: bool=True, fewshot_aware_proposer: bool=True, requires_permission_to_run: bool=False, provide_traceback: Optional[bool]=None, verbose: bool=False, **kwargs):
        """
        Base MiproOptimizer class that supports plug-and-play usage. 

        Args: 
            registry (ParamRegistry): a ParamRegistry object that contains the parameters to optimize. 
            program (Callable): a program to optimize. Must be a callable object with save(path) and load(path) methods.
            optimizer_llm (BaseLLM): a language model to use for optimization. 
            evaluator (Optional[Callable]): a function that evaluates the performance of the program. 
                Required to have a `__call__(program, evalset, *kwargs) -> float` method that receives a program and a list of 
                examples from a benchmark's train/dev/test set and return a float score. Must also have a `metric(example, prediction) -> float` 
                method that evaluates a single example. If not provided, will construct a default evaluator using the benchmark's evaluate method.
            eval_rounds (Optional[int]): number of rounds to evaluate the program. Defaults to 1. 
            metric_threshold (Optional[float]): threshold for the metric score. If provided, only examples with scores above this threshold will be used as demonstrations. 
                If not provided, examples with scores above 0 will be used as demonstrations. 
            max_bootstrapped_demos (int): maximum number of bootstrapped demonstrations to use. Defaults to 4.
            max_labeled_demos (int): maximum number of labeled demonstrations to use. Defaults to 4.
            auto (Optional[Literal["light", "medium", "heavy"]]): automatic configuration mode. If set, will override num_candidates and max_steps. 
                "light": n=6, val_size=100; "medium": n=12, val_size=300; "heavy": n=18, val_size=1000. Defaults to "medium".
            max_steps (int): maximum number of optimization steps. Required if auto is None.
            num_candidates (Optional[int]): number of candidates to generate for each optimization step. Required if auto is None.
            num_threads (Optional[int]): number of threads to use for parallel evaluation. If None, will use single thread. Only used if evaluator is not provided. 
            max_errors (int): maximum number of errors allowed during evaluation before stopping. Defaults to 10.
            seed (int): random seed for reproducibility. Defaults to 9.
            init_temperature (float): initial temperature for instruction generation. Defaults to 0.5.
            track_stats (bool): whether to track optimization statistics. Defaults to True.
            save_path (Optional[str]): path to save optimization results. If None, results will not be saved.
            minibatch (bool): whether to use minibatch evaluation during optimization. Defaults to True.
            minibatch_size (int): size of minibatch for evaluation. Defaults to 35.
            minibatch_full_eval_steps (int): number of minibatch steps between full evaluations. Defaults to 5.
            program_aware_proposer (bool): whether to use program-aware instruction proposer. Defaults to True.
            data_aware_proposer (bool): whether to use data-aware instruction proposer. Defaults to True.
            view_data_batch_size (int): batch size for viewing data during instruction proposal. Defaults to 10.
            tip_aware_proposer (bool): whether to use tip-aware instruction proposer. Defaults to True.
            fewshot_aware_proposer (bool): whether to use fewshot-aware instruction proposer. Defaults to True.
            requires_permission_to_run (bool): whether to require user permission before running optimization. Defaults to False.
            provide_traceback (Optional[bool]): whether to provide traceback for evaluation errors. If None, will use default setting.
            **kwargs: additional keyword arguments to pass to the evaluator.

        Raises:
            TypeError: If program is not callable or evaluator doesn't return float
            ValueError: If program doesn't have required methods (save and load) or if evaluator doesn't have required methods
        """
        BaseOptimizer.__init__(self, registry=registry, program=program, evaluator=evaluator)
        self._validate_program(program=program)
        self.model = self._convert_to_dspy_module(registry, program)
        self.optimizer_llm = MiproLMWrapper(optimizer_llm)
        dspy.configure(lm=self.optimizer_llm)
        self.task_model = dspy.settings.lm
        self.prompt_model = dspy.settings.lm
        self.metric_threshold = metric_threshold
        self.metric_name = None
        self.teacher_settings = {'use_teacher': True}
        allowed_modes = {None, 'light', 'medium', 'heavy'}
        if auto not in allowed_modes:
            raise ValueError(f'Invalid value for auto: {auto}. Must be one of {allowed_modes}.')
        self.auto = auto
        self.num_fewshot_candidates = num_candidates
        self.num_instruct_candidates = num_candidates
        self.num_candidates = num_candidates
        self.init_temperature = init_temperature
        self.max_bootstrapped_demos = max_bootstrapped_demos
        self.max_labeled_demos = max_labeled_demos
        self.max_steps = max_steps
        self.num_threads = num_threads
        self.max_errors = max_errors
        self.track_stats = track_stats
        self.eval_rounds = eval_rounds
        self.save_path = save_path
        self.prompt_model_total_calls = 0
        self.total_calls = 0
        self.seed = seed
        self.rng = None
        self.minibatch = minibatch
        self.minibatch_size = minibatch_size
        self.minibatch_full_eval_steps = minibatch_full_eval_steps
        self.program_aware_proposer = program_aware_proposer
        self.data_aware_proposer = data_aware_proposer
        self.view_data_batch_size = view_data_batch_size
        self.tip_aware_proposer = tip_aware_proposer
        self.fewshot_aware_proposer = fewshot_aware_proposer
        self.requires_permission_to_run = requires_permission_to_run
        self.provide_traceback = provide_traceback
        self.verbose = verbose
        self.kwargs = kwargs

    def _validate_program(self, program: Callable):
        """
        Validate that the program meets the required interface.
        
        Args:
            program (Callable): The program to validate
            
        Raises:
            TypeError: If program is not callable
            ValueError: If program doesn't have required methods (save and load)
        """
        if not callable(program):
            raise TypeError('program must be callable')
        if not hasattr(program, 'save'):
            logger.warning('program does not have a `save(path=...)` method, will use the default save method in dspy.Module')
        else:
            save_sig = inspect.signature(program.save)
            save_params = list(save_sig.parameters.keys())
            if 'path' not in save_params:
                raise ValueError("program.save must accept a 'path' parameter")
        if not hasattr(program, 'load'):
            logger.warning('program does not have a `load(path=...)` method, will use the default load method in dspy.Module')
        else:
            load_sig = inspect.signature(program.load)
            load_params = list(load_sig.parameters.keys())
            if 'path' not in load_params:
                raise ValueError("program.load must accept a 'path' parameter")

    def _validate_evaluator(self, evaluator: Callable=None, benchmark: Benchmark=None, metric_name: Optional[str]=None) -> Callable:
        """
        Validate that the evaluator meets the required interface and wrap it with runtime checks.
        
        Args:
            evaluator (Callable): The evaluator to validate. 
                If provided, it must have a `__call__(program, evalset, *kwargs) -> float` method that receives a program and a list of examples from a benchmark's train/dev/test set and return a float score. 
                It must also have a `metric(example: dspy.Example, prediction: Any) -> float/int/bool` method that evaluates a single example. 
            benchmark (Benchmark): The benchmark to use for evaluation. Only used if evaluator is not provided. In this case, the evaluator will be constructed using the `evaluate` method (return a dictionary of scores) in the benchmark. 
            metric_name (Optional[str]): The name of the metric to use for evaluation. Only used if evaluator is not provided. It will be used to select the metric for optimization from the dictionary of scores returned by the benchmark's `evaluate` method. 
            
        Raises:
            TypeError: If evaluator is not callable or doesn't return float
            ValueError: If evaluator doesn't have required parameters
        """
        if evaluator is None:
            if not hasattr(benchmark, 'evaluate'):
                raise ValueError('`evaluator` is not provided and the benchmark does not have a `evaluate` method.')
            logger.info('`evaluator` is not provided. Will construct a default evaluator using the `evaluate` method in the benchmark.')
            evaluator = MiproEvaluator(benchmark=benchmark, num_threads=self.num_threads, max_errors=self.max_errors, display_progress=True, provide_traceback=self.provide_traceback, metric_name=metric_name, **self.kwargs)
        if not callable(evaluator):
            raise TypeError('evaluator must be callable, i.e., a function or a class with interface `__call__(program, evalset, *kwargs) -> float`')
        sig = inspect.signature(evaluator.__call__ if hasattr(evaluator, '__call__') else evaluator)
        params = list(sig.parameters.keys())
        if len(params) < 2:
            raise ValueError('evaluator must accept at least two parameters (program and evalset)')
        if sig.return_annotation != inspect.Signature.empty:
            if sig.return_annotation not in [float, int, bool]:
                raise TypeError('evaluator must return a float, int, or bool')
        if not hasattr(evaluator, 'metric'):
            raise ValueError('evaluator must have a `metric(example: dspy.Example, prediction: Any) -> float/int/bool` method')
        metric_sig = inspect.signature(evaluator.metric)
        metric_params = list(metric_sig.parameters.keys())
        if len(metric_params) < 2:
            raise ValueError('evaluator.metric must accept at least two parameters (example and prediction)')
        if metric_params[0] != 'example' or metric_params[1] != 'prediction':
            raise ValueError('evaluator.metric must have parameters in order: example, prediction')
        original_evaluator = evaluator.__call__ if hasattr(evaluator, '__call__') else evaluator

        @wraps(original_evaluator)
        def wrapped_evaluator(*args, **kwargs):
            result = original_evaluator(*args, **kwargs)
            if not isinstance(result, (float, int, bool)):
                raise TypeError(f'evaluator must return a float, int, or bool, got {type(result)}')
            return result
        if hasattr(evaluator, '__call__'):
            evaluator.__call__ = wrapped_evaluator
        else:

            class WrappedEvaluator:

                def __init__(self, func):
                    self._func = func

                def __call__(self, *args, **kwargs):
                    return wrapped_evaluator(*args, **kwargs)
            return WrappedEvaluator(evaluator)
        return evaluator

    def _convert_to_dspy_module(self, registry: ParamRegistry, program: Callable):
        if isinstance(program, dspy.Module):
            return program
        program = PromptTuningModule.from_registry(program=program, registry=registry)
        return program

    def optimize(self, dataset: Benchmark, metric_name: Optional[str]=None, **kwargs):
        """
        Optimize the program using the Mipro algorithm. 

        Args:
            dataset (Benchmark): a Benchmark object that contains the training and validation data. 
            metric_name (Optional[str]): the name of the metric to use for optimization. Only used when `self.evaluator` is not provided. 
                In this case, the evaluator will be constructed using the `evaluate` method (return a dictionary of scores) in the benchmark, 
                and the metric specified by `metric_name` will be used for optimization. If not provided, the average of all scores returned by the evaluator will be used. 
                If `self.evaluator` is provided, this argument will be ignored. 
            **kwargs: additional keyword arguments to pass to the evaluator. 
        """
        zeroshot_opt = self.max_bootstrapped_demos == 0 and self.max_labeled_demos == 0
        student = self.model
        num_trials = self.max_steps
        minibatch = self.minibatch
        self.metric_name = metric_name
        if self.auto is None and (self.num_candidates is not None and num_trials is None):
            raise ValueError(f"If auto is None, max_steps must also be provided. Given num_candidates={self.num_candidates}, we'd recommend setting max_steps to ~{self._set_num_trials_from_num_candidates(self.model, zeroshot_opt, self.num_candidates)}.")
        if self.auto is None and (self.num_candidates is None or num_trials is None):
            raise ValueError('If auto is None, num_candidates must also be provided.')
        if self.auto is not None and (self.num_candidates is not None or num_trials is not None):
            raise ValueError('If auto is not None, num_candidates and max_steps cannot be set, since they would be overrided by the auto settings. Please either set auto to None, or do not specify num_candidates and max_steps.')
        seed = self.seed
        self._set_random_seeds(seed)
        trainset, valset = self._set_and_validate_datasets(dataset=dataset)
        num_trials, valset, minibatch = self._set_hyperparams_from_run_mode(student, num_trials, minibatch, zeroshot_opt, valset)
        if self.auto:
            self._print_auto_run_settings(num_trials, minibatch, valset)
        if minibatch and self.minibatch_size > len(valset):
            raise ValueError(f'Minibatch size cannot exceed the size of the valset. Valset size: {len(valset)}.')
        if self.requires_permission_to_run:
            if not self._get_user_confirmation(student, num_trials, minibatch, self.minibatch_size, self.minibatch_full_eval_steps, valset, self.program_aware_proposer):
                logger.info('Compilation aborted by the user.')
                return student
        program = student.deepcopy()
        evaluator = self._validate_evaluator(evaluator=self.evaluator, benchmark=dataset, metric_name=metric_name)
        self.metric = evaluator.metric
        demo_candidates = self._bootstrap_fewshot_examples(program, trainset, seed, teacher=None)
        with suppress_cost_logging():
            instruction_candidates = self._propose_instructions(program, trainset, demo_candidates, self.view_data_batch_size, self.program_aware_proposer, self.data_aware_proposer, self.tip_aware_proposer, self.fewshot_aware_proposer)
        with suppress_cost_logging():
            best_program = self._optimize_prompt_parameters(program, instruction_candidates, demo_candidates, evaluator, valset, num_trials, minibatch, self.minibatch_size, self.minibatch_full_eval_steps, seed)
        if self.save_path:
            os.makedirs(self.save_path, exist_ok=True)
            self.best_program_path = os.path.join(self.save_path, 'best_program.json')
            best_program.save(self.best_program_path)
        self.model.reset()

    def restore_best_program(self):
        pass

    def _get_input_keys(self, dataset: Benchmark) -> Optional[List[str]]:
        input_keys = None
        if hasattr(dataset, 'get_input_keys'):
            candidate_input_keys = dataset.get_input_keys()
            if isinstance(candidate_input_keys, (list, tuple)) and all((isinstance(key, str) for key in candidate_input_keys)):
                input_keys = candidate_input_keys
        return input_keys

    def _set_and_validate_datasets(self, dataset: Benchmark):
        trainset = dataset.get_train_data()
        if not trainset:
            raise ValueError('No training data found in the dataset. Please set `_train_data` in the benchmark.')
        if trainset and (not isinstance(trainset[0], (dict, dspy.Example))):
            raise ValueError('Training set in the benchmark must be a list of dictionaries or dspy.Example objects.')
        valset = dataset.get_dev_data()
        if not valset:
            if len(trainset) < 2:
                raise ValueError('Training set in the benchmark must have at least 2 examples if no validation set is provided.')
            valset_size = min(1000, max(1, int(len(trainset) * 0.8)))
            cutoff = len(trainset) - valset_size
            valset = trainset[cutoff:]
            trainset = trainset[:cutoff]
        elif len(valset) < 1:
            raise ValueError('Validation set in the benchmark must have at least 1 example.')
        input_keys = self._get_input_keys(dataset)
        if input_keys is None:
            logger.warning('`get_input_keys` is not implemented in the benchmark. Will use all keys as input keys. This may cause unexpected behavior if the program does not use all the keys.')
            input_keys = trainset[0].keys()
        dspy_trainset = self._convert_benchmark_data_to_dspy_examples(trainset, input_keys)
        dspy_valset = self._convert_benchmark_data_to_dspy_examples(valset, input_keys)
        return (dspy_trainset, dspy_valset)

    def _convert_benchmark_data_to_dspy_examples(self, data: List[dict], input_keys: List[str]) -> List[dspy.Example]:
        """
        Convert the benchmark data to a list of dspy Example. This is required since the evaluator accepts a list of dspy Example. 
        """
        dspy_examples = [example.with_inputs(*input_keys) if isinstance(example, dspy.Example) else dspy.Example(**example).with_inputs(*input_keys) for example in data]
        return dspy_examples

    def _bootstrap_fewshot_examples(self, program: Any, trainset: List, seed: int, teacher: Any) -> Optional[List]:
        logger.info('==> STEP 1: BOOTSTRAP FEWSHOT EXAMPLES <==')
        if self.max_bootstrapped_demos > 0:
            logger.info('These will be used as few-shot example candidates for our program and for creating instructions.\n')
        else:
            logger.info('These will be used for informing instruction proposal.\n')
        logger.info(f'Bootstrapping N={self.num_fewshot_candidates} sets of demonstrations...')
        zeroshot = self.max_bootstrapped_demos == 0 and self.max_labeled_demos == 0
        try:
            with suppress_logger_info():
                demo_candidates = create_n_fewshot_demo_sets(student=program, num_candidate_sets=self.num_fewshot_candidates, trainset=trainset, max_labeled_demos=LABELED_FEWSHOT_EXAMPLES_IN_CONTEXT if zeroshot else self.max_labeled_demos, max_bootstrapped_demos=BOOTSTRAPPED_FEWSHOT_EXAMPLES_IN_CONTEXT if zeroshot else self.max_bootstrapped_demos, metric=self.metric, max_errors=self.max_errors, teacher=teacher, teacher_settings=self.teacher_settings, seed=seed, metric_threshold=self.metric_threshold, rng=self.rng)
        except Exception as e:
            logger.info(f'Error generating few-shot examples: {e}')
            logger.info('Running without few-shot examples.')
            demo_candidates = None
        return demo_candidates

    def _propose_instructions(self, program: Any, trainset: List, demo_candidates: Optional[List], view_data_batch_size: int, program_aware_proposer: bool, data_aware_proposer: bool, tip_aware_proposer: bool, fewshot_aware_proposer: bool) -> Dict[int, List[str]]:
        logger.info('==> STEP 2: PROPOSE INSTRUCTION CANDIDATES <==')
        logger.info('We will use the few-shot examples from the previous step, a generated dataset summary, a summary of the program code, and a randomly selected prompting tip to propose instructions.')
        proposer = GroundedProposer(program=program, trainset=trainset, prompt_model=self.prompt_model, view_data_batch_size=view_data_batch_size, program_aware=program_aware_proposer, use_dataset_summary=data_aware_proposer, use_task_demos=fewshot_aware_proposer, num_demos_in_context=BOOTSTRAPPED_FEWSHOT_EXAMPLES_IN_CONTEXT, use_tip=tip_aware_proposer, set_tip_randomly=tip_aware_proposer, use_instruct_history=False, set_history_randomly=False, verbose=self.verbose, rng=self.rng)
        logger.info(f'Proposing N={self.num_instruct_candidates} instructions...')
        instruction_candidates = proposer.propose_instructions_for_program(trainset=trainset, program=program, demo_candidates=demo_candidates, N=self.num_instruct_candidates, T=self.init_temperature, trial_logs={})
        for i, pred in enumerate(program.predicts):
            logger.info(f'Proposed Instructions for Predictor {i}:\n')
            instruction_candidates[i][0] = get_signature(pred).instructions
            for j, instruction in enumerate(instruction_candidates[i]):
                logger.info(f'{j}: {instruction}\n')
            logger.info('\n')
        return instruction_candidates

    def _optimize_prompt_parameters(self, program: Any, instruction_candidates: Dict[int, List[str]], demo_candidates: Optional[List], evaluator: Callable, valset: List, num_trials: int, minibatch: bool, minibatch_size: int, minibatch_full_eval_steps: int, seed: int) -> Optional[Any]:
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        logger.info('==> STEP 3: FINDING OPTIMAL PROMPT PARAMETERS <==')
        logger.info('We will evaluate the program over a series of trials with different combinations of instructions and few-shot examples to find the optimal combination using Bayesian Optimization.\n')
        run_additional_full_eval_at_end = 1 if num_trials % minibatch_full_eval_steps != 0 else 0
        adjusted_num_trials = int(num_trials + num_trials // minibatch_full_eval_steps + 1 + run_additional_full_eval_at_end if minibatch else num_trials)
        logger.info(f'== Trial {1} / {adjusted_num_trials} - Full Evaluation of Default Program ==')
        default_score = self.evaluate(evalset=valset, program=program, evaluator=evaluator, batch_size=len(valset))
        logger.info(f'Default program score: {default_score}\n')
        trial_logs = {}
        trial_logs[1] = {}
        trial_logs[1]['full_eval_program_path'] = save_candidate_program(program, self.save_path, -1)
        trial_logs[1]['full_eval_score'] = default_score
        trial_logs[1]['total_eval_calls_so_far'] = len(valset)
        trial_logs[1]['full_eval_program'] = program.deepcopy()
        best_score = default_score
        best_program = program.deepcopy()
        total_eval_calls = len(valset)
        score_data = [{'score': best_score, 'program': program.deepcopy(), 'full_eval': True}]
        param_score_dict = defaultdict(list)
        fully_evaled_param_combos = {}

        def objective(trial):
            nonlocal program, best_program, best_score, trial_logs, total_eval_calls, score_data
            trial_num = trial.number + 1
            if minibatch:
                logger.info(f'== Trial {trial_num} / {adjusted_num_trials} - Minibatch ==')
            else:
                logger.info(f'===== Trial {trial_num} / {num_trials} =====')
            trial_logs[trial_num] = {}
            candidate_program = program.deepcopy()
            chosen_params, raw_chosen_params = self._select_and_insert_instructions_and_demos(candidate_program, instruction_candidates, demo_candidates, trial, trial_logs, trial_num)
            if self.verbose:
                logger.info('Evaluating the following candidate program...\n')
                print_full_program(candidate_program)
            batch_size = minibatch_size if minibatch else len(valset)
            score = self.evaluate(evalset=valset, program=candidate_program, evaluator=evaluator, batch_size=batch_size)
            total_eval_calls += batch_size
            if not minibatch and score > best_score:
                best_score = score
                best_program = candidate_program.deepcopy()
                logger.info(f'{GREEN}Best full score so far!{ENDC} Score: {score}')
            score_data.append({'score': score, 'program': candidate_program, 'full_eval': batch_size >= len(valset)})
            if minibatch:
                self._log_minibatch_eval(score, best_score, batch_size, chosen_params, score_data, trial, adjusted_num_trials, trial_logs, trial_num, candidate_program, total_eval_calls)
            else:
                self._log_normal_eval(score, best_score, chosen_params, score_data, trial, num_trials, trial_logs, trial_num, valset, batch_size, candidate_program, total_eval_calls)
            categorical_key = ','.join(map(str, chosen_params))
            param_score_dict[categorical_key].append((score, candidate_program, raw_chosen_params))
            if minibatch and (trial_num % (minibatch_full_eval_steps + 1) == 0 or trial_num == adjusted_num_trials - 1):
                best_score, best_program, total_eval_calls = self._perform_full_evaluation(trial_num, adjusted_num_trials, param_score_dict, fully_evaled_param_combos, evaluator, valset, trial_logs, total_eval_calls, score_data, best_score, best_program, study, instruction_candidates, demo_candidates)
            return score
        sampler = optuna.samplers.TPESampler(seed=seed, multivariate=True)
        study = optuna.create_study(direction='maximize', sampler=sampler)
        default_params = {f'{i}_predictor_instruction': 0 for i in range(len(program.predicts))}
        if demo_candidates:
            default_params.update({f'{i}_predictor_demos': 0 for i in range(len(program.predicts))})
        trial = optuna.trial.create_trial(params=default_params, distributions=self._get_param_distributions(program, instruction_candidates, demo_candidates), value=default_score)
        study.add_trial(trial)
        study.optimize(objective, n_trials=num_trials)
        if best_program is not None and self.track_stats:
            best_program.trial_logs = trial_logs
            best_program.score = best_score
            best_program.prompt_model_total_calls = self.prompt_model_total_calls
            best_program.total_calls = self.total_calls
            sorted_candidate_programs = sorted(score_data, key=lambda x: x['score'], reverse=True)
            best_program.mb_candidate_programs = [score_data for score_data in sorted_candidate_programs if not score_data['full_eval']]
            best_program.candidate_programs = [score_data for score_data in sorted_candidate_programs if score_data['full_eval']]
        logger.info(f'Returning best identified program with score {best_score}!')
        return best_program

    def _select_and_insert_instructions_and_demos(self, candidate_program: Any, instruction_candidates: Dict[int, List[str]], demo_candidates: Optional[List], trial: optuna.trial.Trial, trial_logs: Dict, trial_num: int) -> List[str]:
        chosen_params = []
        raw_chosen_params = {}
        for i, predictor in enumerate(candidate_program.predictors()):
            instruction_idx = trial.suggest_categorical(f'{i}_predictor_instruction', range(len(instruction_candidates[i])))
            selected_instruction = instruction_candidates[i][instruction_idx]
            predictor.signature.instructions = selected_instruction
            trial_logs[trial_num][f'{i}_predictor_instruction'] = instruction_idx
            chosen_params.append(f'Predictor {i}: Instruction {instruction_idx}')
            raw_chosen_params[f'{i}_predictor_instruction'] = instruction_idx
            if demo_candidates:
                demos_idx = trial.suggest_categorical(f'{i}_predictor_demos', range(len(demo_candidates[i])))
                predictor.demos = demo_candidates[i][demos_idx]
                trial_logs[trial_num][f'{i}_predictor_demos'] = demos_idx
                chosen_params.append(f'Predictor {i}: Few-Shot Set {demos_idx}')
                raw_chosen_params[f'{i}_predictor_demos'] = instruction_idx
        return (chosen_params, raw_chosen_params)

    def _log_minibatch_eval(self, score, best_score, batch_size, chosen_params, score_data, trial, adjusted_num_trials, trial_logs, trial_num, candidate_program, total_eval_calls):
        trial_logs[trial_num]['mb_program_path'] = save_candidate_program(candidate_program, self.save_path, trial_num=trial_num, note='mb')
        trial_logs[trial_num]['mb_score'] = score
        trial_logs[trial_num]['total_eval_calls_so_far'] = total_eval_calls
        trial_logs[trial_num]['mb_program'] = candidate_program.deepcopy()
        logger.info(f'Score: {score} on minibatch of size {batch_size} with parameters {chosen_params}.')
        minibatch_scores = ', '.join([f'{s['score']}' for s in score_data if not s['full_eval']])
        logger.info(f'Minibatch scores so far: {'[' + minibatch_scores + ']'}')
        full_eval_scores = ', '.join([f'{s['score']}' for s in score_data if s['full_eval']])
        trajectory = '[' + full_eval_scores + ']'
        logger.info(f'Full eval scores so far: {trajectory}')
        logger.info(f'Best full score so far: {best_score}')
        logger.info(f'{'=' * len(f'== Trial {trial.number + 1} / {adjusted_num_trials} - Minibatch Evaluation ==')}\n\n')

    def _log_normal_eval(self, score, best_score, chosen_params, score_data, trial, num_trials, trial_logs, trial_num, valset, batch_size, candidate_program, total_eval_calls):
        trial_logs[trial_num]['full_eval_program_path'] = save_candidate_program(candidate_program, self.save_path, trial_num)
        trial_logs[trial_num]['full_eval_score'] = score
        trial_logs[trial_num]['total_eval_calls_so_far'] = total_eval_calls
        trial_logs[trial_num]['full_eval_program'] = candidate_program.deepcopy()
        logger.info(f'Score: {score} with parameters {chosen_params}.')
        full_eval_scores = ', '.join([f'{s['score']}' for s in score_data if s['full_eval']])
        logger.info(f'Scores so far: {'[' + full_eval_scores + ']'}')
        logger.info(f'Best score so far: {best_score}')
        logger.info(f'{'=' * len(f'===== Trial {trial.number + 1} / {num_trials} =====')}\n\n')

    def _perform_full_evaluation(self, trial_num: int, adjusted_num_trials: int, param_score_dict: Dict, fully_evaled_param_combos: Dict, evaluator: Callable, valset: List, trial_logs: Dict, total_eval_calls: int, score_data, best_score: float, best_program: Any, study: optuna.Study, instruction_candidates: List, demo_candidates: List):
        logger.info(f'===== Trial {trial_num + 1} / {adjusted_num_trials} - Full Evaluation =====')
        highest_mean_program, mean_score, combo_key, params = get_program_with_highest_avg_score(param_score_dict, fully_evaled_param_combos)
        logger.info(f'Doing full eval on next top averaging program (Avg Score: {mean_score}) from minibatch trials...')
        full_eval_score = self.evaluate(evalset=valset, program=highest_mean_program, evaluator=evaluator, batch_size=len(valset))
        score_data.append({'score': full_eval_score, 'program': highest_mean_program, 'full_eval': True})
        trial = optuna.trial.create_trial(params=params, distributions=self._get_param_distributions(best_program, instruction_candidates, demo_candidates), value=full_eval_score)
        study.add_trial(trial)
        fully_evaled_param_combos[combo_key] = {'program': highest_mean_program, 'score': full_eval_score}
        total_eval_calls += len(valset)
        trial_logs[trial_num + 1] = {}
        trial_logs[trial_num + 1]['total_eval_calls_so_far'] = total_eval_calls
        trial_logs[trial_num + 1]['full_eval_program_path'] = save_candidate_program(program=highest_mean_program, log_dir=self.save_path, trial_num=trial_num + 1, note='full_eval')
        trial_logs[trial_num + 1]['full_eval_program'] = highest_mean_program
        trial_logs[trial_num + 1]['full_eval_score'] = full_eval_score
        if full_eval_score > best_score:
            logger.info(f'{GREEN}New best full eval score!{ENDC} Score: {full_eval_score}')
            best_score = full_eval_score
            best_program = highest_mean_program.deepcopy()
        full_eval_scores = ', '.join([f'{s['score']}' for s in score_data if s['full_eval']])
        trajectory = '[' + full_eval_scores + ']'
        logger.info(f'Full eval scores so far: {trajectory}')
        logger.info(f'Best full score so far: {best_score}')
        logger.info(len(f'===== Full Eval {len(fully_evaled_param_combos) + 1} =====') * '=')
        logger.info('\n')
        return (best_score, best_program, total_eval_calls)

    def evaluate(self, evalset: Optional[List[dspy.Example]]=None, dataset: Optional[Benchmark]=None, eval_mode: Optional[str]='dev', program: Optional[PromptTuningModule]=None, evaluator: Optional[Callable]=None, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, batch_size: Optional[int]=None, **kwargs):
        if program is None:
            program = self.model
        if evaluator is None:
            evaluator = self._validate_evaluator(evaluator=self.evaluator, benchmark=dataset, metric_name=self.metric_name)
        if evalset is None:
            assert dataset is not None, 'Either `evalset` or `dataset` must be provided.'
            data_map = {'train': dataset.get_train_data, 'dev': dataset.get_dev_data, 'test': dataset.get_test_data}
            evaldata = data_map[eval_mode](indices=indices, sample_k=sample_k)
            if not evaldata:
                logger.warning(f'No data found for {eval_mode} set. Return 0.0.')
                return 0.0
            input_keys = self._get_input_keys(dataset=dataset)
            if not input_keys:
                input_keys = evaldata[0].keys()
            evalset = self._convert_benchmark_data_to_dspy_examples(evaldata, input_keys)
        batch_size = batch_size or len(evalset)
        score_list = []
        for _ in range(self.eval_rounds):
            score = eval_candidate_program(batch_size=batch_size, evalset=evalset, candidate_program=program, evaluator=evaluator, rng=self.rng)
            score_list.append(score)
        return sum(score_list) / len(score_list)

def _bootstrap_fewshot_examples(self, program: Any, trainset: List, seed: int, teacher: Any) -> Optional[List]:
    logger.info('==> STEP 1: BOOTSTRAP FEWSHOT EXAMPLES <==')
    if self.max_bootstrapped_demos > 0:
        logger.info('These will be used as few-shot example candidates for our program and for creating instructions.\n')
    else:
        logger.info('These will be used for informing instruction proposal.\n')
    logger.info(f'Bootstrapping N={self.num_fewshot_candidates} sets of demonstrations...')
    zeroshot = self.max_bootstrapped_demos == 0 and self.max_labeled_demos == 0
    try:
        with suppress_logger_info():
            demo_candidates = create_n_fewshot_demo_sets(student=program, num_candidate_sets=self.num_fewshot_candidates, trainset=trainset, max_labeled_demos=LABELED_FEWSHOT_EXAMPLES_IN_CONTEXT if zeroshot else self.max_labeled_demos, max_bootstrapped_demos=BOOTSTRAPPED_FEWSHOT_EXAMPLES_IN_CONTEXT if zeroshot else self.max_bootstrapped_demos, metric=self.metric, max_errors=self.max_errors, teacher=teacher, teacher_settings=self.teacher_settings, seed=seed, metric_threshold=self.metric_threshold, rng=self.rng)
    except Exception as e:
        logger.info(f'Error generating few-shot examples: {e}')
        logger.info('Running without few-shot examples.')
        demo_candidates = None
    return demo_candidates

class WorkFlowGraphProgram:

    def __init__(self, graph: WorkFlowGraph, agent_manager: AgentManager, executor_llm: BaseLLM, collate_func: Optional[Callable]=None, output_postprocess_func: Optional[Callable]=None):
        self.graph = graph
        self.agent_manager = agent_manager
        self.executor_llm = executor_llm
        self.collate_func = collate_func or (lambda x: x)
        self.output_postprocess_func = output_postprocess_func or (lambda x: x)

    def __call__(self, **input_data):
        new_config = deepcopy(self.graph.get_config())
        new_graph: WorkFlowGraph = WorkFlowGraph.from_dict(new_config)
        new_graph.reset_graph()
        use_teacher = dspy.settings.get('use_teacher', False)
        if use_teacher:
            new_graph, new_agent_manager = self.inject_teacher_settings(new_graph, self.agent_manager)
            workflow = WorkFlow(llm=self.executor_llm, graph=new_graph, agent_manager=new_agent_manager)
        else:
            workflow = WorkFlow(llm=self.executor_llm, graph=new_graph, agent_manager=self.agent_manager)
        output: str = workflow.execute(inputs=self.collate_func(input_data))
        output = self.output_postprocess_func(output)
        all_execution_data = workflow.environment.execution_data
        all_input_output_keys = self._extract_input_output_keys(new_graph)
        execution_data = {k: v for k, v in all_execution_data.items() if k in all_input_output_keys}
        return (output, execution_data)

    def inject_teacher_settings(self, graph: WorkFlowGraph, agent_manager: AgentManager):
        """
        Inject the teacher settings into the graph and agent manager.
        """
        optimizer_llm_config = dspy.settings.lm.model.config.to_dict()
        for node in graph.nodes:
            for agent in node.agents:
                agent['llm_config'] = optimizer_llm_config
        new_agent_manager = agent_manager.copy()
        new_agent_manager.clear_agents()
        new_agent_manager.add_agents_from_workflow(graph, llm_config=optimizer_llm_config)
        return (graph, new_agent_manager)

    def _extract_input_output_keys(self, graph: WorkFlowGraph) -> Set[str]:
        """
        Extract all the input and output keys from the graph.
        """
        all_input_output_keys = set()
        for node in graph.nodes:
            for inp in node.inputs:
                all_input_output_keys.add(inp.name)
            for out in node.outputs:
                all_input_output_keys.add(out.name)
            for agent in node.agents:
                for agent_inp in agent.get('inputs', []):
                    agent_inp_name = agent_inp.get('name', None)
                    if agent_inp_name:
                        all_input_output_keys.add(agent_inp_name)
                for agent_out in agent.get('outputs', []):
                    agent_out_name = agent_out.get('name', None)
                    if agent_out_name:
                        all_input_output_keys.add(agent_out_name)
        return all_input_output_keys

    def save(self, path: str):
        self.graph.save_module(path=path)

    def load(self, path: str):
        return WorkFlowGraph.from_file(path=path)

def save(self, path: str):
    self.graph.save_module(path=path)

def load(self, path: str):
    return WorkFlowGraph.from_file(path=path)

class BaseOptimizer(abc.ABC):

    def __init__(self, registry: ParamRegistry, program: Callable[..., Dict[str, Any]]=None, evaluator: Optional[Callable[..., Any]]=None):
        """
        Abstract base class for optimization routines.

        Parameters:
        - registry (ParamRegistry): parameter access layer
        - evaluator (Callable): function that evaluates the result dict and returns a float
        """
        self.program = program
        self.registry = registry
        self.program = program
        self.evaluator = evaluator

    def get_param(self, name: str) -> Any:
        """Retrieve the current value of a parameter by name."""
        return self.registry.get(name)

    def set_param(self, name: str, value: Any):
        """Set the value of a parameter by name."""
        self.registry.set(name, value)

    def param_names(self) -> List[str]:
        """Return the list of all registered parameter names."""
        return self.registry.names()

    def get_current_cfg(self) -> Dict[str, Any]:
        """Return current config as a dictionary."""
        return {name: self.get_param(name) for name in self.param_names()}

    def apply_cfg(self, cfg: Dict[str, Any]):
        """Apply a configuration dictionary to the registered parameters."""
        for k, v in cfg.items():
            if k in self.registry.fields:
                self.registry.set(k, v)

    @abc.abstractmethod
    def optimize(self):
        """
        Abstract optimization loop. Should be implemented by subclasses.

        Parameters:
        - program_entry: callable that runs the program and returns output dict

        Returns:
        - (best_cfg, history): best config found and full search history
        """
        if self.program is None:
            self.program = EntryPoint.get_entry()
        if self.program is None:
            raise RuntimeError('No entry function provided or registered.')
        print(f'Starting optimization from entry: {self.program.__name__}')
        raise NotImplementedError

@abc.abstractmethod
def optimize(self):
    """
        Abstract optimization loop. Should be implemented by subclasses.

        Parameters:
        - program_entry: callable that runs the program and returns output dict

        Returns:
        - (best_cfg, history): best config found and full search history
        """
    if self.program is None:
        self.program = EntryPoint.get_entry()
    if self.program is None:
        raise RuntimeError('No entry function provided or registered.')
    print(f'Starting optimization from entry: {self.program.__name__}')
    raise NotImplementedError

def timeout_handler(signum, frame):
    print('timeout occured: alarm went off')
    raise TimeoutException

class BaseConfig(BaseModule):
    """
    Base configuration class that serves as parent for all configuration classes.
    
    A config should inherit BaseConfig and specify the attributes and their types. 
    Otherwise this will be an empty config.
    """

    def save(self, path: str, **kwargs) -> str:
        """Save configuration to the specified path.
        
        Args:
            path: The file path to save the configuration
            **kwargs (Any): Additional keyword arguments passed to save_module method
        
        Returns:
            str: The path where the file was saved
        """
        return super().save_module(path, **kwargs)

    def get_config_params(self) -> List[str]:
        """Get a list of configuration parameters.
        
        Returns:
            List[str]: List of configuration parameter names, excluding 'class_name'
        """
        config_params = list(type(self).model_fields.keys())
        config_params.remove('class_name')
        return config_params

    def get_set_params(self, ignore: List[str]=[]) -> dict:
        """Get a dictionary of explicitly set parameters.
        
        Args:
            ignore: List of parameter names to ignore
        
        Returns:
            dict: Dictionary of explicitly set parameters, excluding 'class_name' and ignored parameters
        """
        explicitly_set_fields = {field: getattr(self, field) for field in self.model_fields_set}
        if self.kwargs:
            explicitly_set_fields.update(self.kwargs)
        for field in ignore:
            explicitly_set_fields.pop(field, None)
        explicitly_set_fields.pop('class_name', None)
        return explicitly_set_fields

def save(self, path: str, **kwargs) -> str:
    """Save configuration to the specified path.
        
        Args:
            path: The file path to save the configuration
            **kwargs (Any): Additional keyword arguments passed to save_module method
        
        Returns:
            str: The path where the file was saved
        """
    return super().save_module(path, **kwargs)

class Parser(BaseModule):

    @classmethod
    def parse(cls, content: str, **kwargs):
        """
        the method used to parse text into a Parser object. Use Parser.from_str to parse input by default. 
        Args:
            content: The content to parse
            **kwargs: Additional keyword arguments
        Returns:
            Parser: The parsed Parser object
        """
        return cls.from_str(content, **kwargs)

    def save(self, path: str, **kwargs) -> str:
        """
        Save the Parser object to a file.
        """
        super().save_module(path, **kwargs)

def save(self, path: str, **kwargs) -> str:
    """
        Save the Parser object to a file.
        """
    super().save_module(path, **kwargs)

@register_model(config_cls=SiliconFlowConfig, alias=['siliconflow'])
class SiliconFlowLLM(OpenAILLM):

    def init_model(self):
        config: SiliconFlowConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'siliconflow_key', 'output_response']

    def _init_client(self, config: SiliconFlowConfig):
        client = OpenAI(api_key=config.siliconflow_key, base_url='https://api.siliconflow.cn/v1')
        return client

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._completion_cost(self.response)
            else:
                output: str = response.choices[0].message.content
                cost = self._completion_cost(response)
                if output_response:
                    print(output)
            self._update_cost(cost=cost)
        except Exception as e:
            if 'account balance is insufficient' in str(e):
                print('Warning: Account balance insufficient. Please recharge your account.')
                return ''
            raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        model: str = self.config.model
        if model not in model_cost:
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
        if 'token_cost' in model_cost[model]:
            input_cost = input_tokens * model_cost[model]['token_cost'] / 1000000.0
            output_cost = output_tokens * model_cost[model]['token_cost'] / 1000000.0
        else:
            input_cost = input_tokens * model_cost[model]['input_token_cost'] / 1000000.0
            output_cost = output_tokens * model_cost[model]['output_token_cost'] / 1000000.0
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)

    def get_cost(self) -> dict:
        cost_info = {}
        try:
            tokens = self.response.usage
            if tokens.prompt_tokens == -1:
                cost_info['note'] = 'Token counts not available in stream mode'
                cost_info['prompt_tokens'] = 0
                cost_info['completion_tokens'] = 0
                cost_info['total_tokens'] = 0
            else:
                cost_info['prompt_tokens'] = tokens.prompt_tokens
                cost_info['completion_tokens'] = tokens.completion_tokens
                cost_info['total_tokens'] = tokens.total_tokens
        except Exception as e:
            print(f'Error during get_cost of SiliconFlow: {str(e)}')
            cost_info['error'] = str(e)
        return cost_info

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        output = ''
        last_chunk = None
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
            last_chunk = chunk
        if output_response:
            print('')
        if hasattr(last_chunk, 'usage'):
            self.response = last_chunk
        else:
            self.response = type('StreamResponse', (), {'usage': type('StreamUsage', (), {'prompt_tokens': -1, 'completion_tokens': -1, 'total_tokens': -1})})
        return output

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

def get_cost(self) -> dict:
    cost_info = {}
    try:
        tokens = self.response.usage
        if tokens.prompt_tokens == -1:
            cost_info['note'] = 'Token counts not available in stream mode'
            cost_info['prompt_tokens'] = 0
            cost_info['completion_tokens'] = 0
            cost_info['total_tokens'] = 0
        else:
            cost_info['prompt_tokens'] = tokens.prompt_tokens
            cost_info['completion_tokens'] = tokens.completion_tokens
            cost_info['total_tokens'] = tokens.total_tokens
    except Exception as e:
        print(f'Error during get_cost of SiliconFlow: {str(e)}')
        cost_info['error'] = str(e)
    return cost_info

@register_model(config_cls=OpenAILLMConfig, alias=['openai_llm'])
class OpenAILLM(BaseLLM):

    def init_model(self):
        config: OpenAILLMConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key']
        if self.config.model not in get_openai_model_cost():
            raise KeyError(f"'{self.config.model}' is not a valid OpenAI model name!")

    def _init_client(self, config: OpenAILLMConfig):
        client = OpenAI(api_key=config.openai_key)
        return client

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        return completion_params

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        """
        Process stream response and return the complete output.

        Args:
            response: The stream response from OpenAI
            output_response: Whether to print the response in real-time
            
        Returns:
            str: The complete output text
        """
        output = ''
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response, output_response: bool=False) -> str:
        """
        Process async stream response and return the complete output.
        
        Args:
            response (AsyncIterator[ChatCompletionChunk]): The async stream response from OpenAI
            output_response (bool): Whether to print the response in real-time
            
            
        Returns:
            str: The complete output text
        """
        output = ''
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
        output = response.choices[0].message.content
        if output_response:
            print(output)
        return output

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            isolated_client = self._init_client(self.config)
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: isolated_client.chat.completions.create(messages=messages, **completion_params))
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of OpenAILLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _stream_cost(self, messages: List[dict], output: str) -> Cost:
        model: str = self.config.model
        input_tokens = token_counter(model=model, messages=messages)
        output_tokens = token_counter(model=model, text=output)
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        input_cost, output_cost = cost_per_token(model=self.config.model, prompt_tokens=input_tokens, completion_tokens=output_tokens)
        cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
        return cost

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
    """
        Process stream response and return the complete output.

        Args:
            response: The stream response from OpenAI
            output_response: Whether to print the response in real-time
            
        Returns:
            str: The complete output text
        """
    output = ''
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            if output_response:
                print(content, end='', flush=True)
            output += content
    if output_response:
        print('')
    return output

def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
    output = response.choices[0].message.content
    if output_response:
        print(output)
    return output

@register_model(config_cls=OpenRouterConfig, alias=['openrouter'])
class OpenRouterLLM(BaseLLM):

    def init_model(self):
        config: OpenRouterConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'openrouter_key', 'openrouter_base', 'openrouter_model_base', 'output_response']

    def _init_client(self, config: OpenRouterConfig):
        client = OpenAI(api_key=config.openrouter_key, base_url=config.openrouter_base)
        return client

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        return completion_params

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        output = ''
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response, output_response: bool=False) -> str:
        output = ''
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
        output = response.choices[0].message.content
        if output_response:
            print(output)
        return output

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of OpenRouterLLM: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            isolated_client = self._init_client(self.config)
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: isolated_client.chat.completions.create(messages=messages, **completion_params))
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of OpenRouterLLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _stream_cost(self, messages: List[dict], output: str) -> Cost:
        model: str = self.config.model
        input_tokens = token_counter(model=model, messages=messages)
        output_tokens = token_counter(model=model, text=output)
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        input_cost_per_token, output_cost_per_token = self._get_cost()
        input_cost = input_tokens * input_cost_per_token
        output_cost = output_tokens * output_cost_per_token
        cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
        return cost

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

    def _get_cost(self):
        url = self.config.openrouter_model_base
        response = requests.get(url)
        data = response.json()
        for model in data['data']:
            if model['id'] == self.config.model:
                pricing = model.get('pricing', {})
                input_cost = float(pricing.get('prompt', 0))
                output_cost = float(pricing.get('completion', 0))
                return (input_cost, output_cost)
        return (0, 0)

def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
    output = ''
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            if output_response:
                print(content, end='', flush=True)
            output += content
    if output_response:
        print('')
    return output

def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
    output = response.choices[0].message.content
    if output_response:
        print(output)
    return output

def main():
    parser = argparse.ArgumentParser(description='Universal workflow executor (goal only)')
    parser.add_argument('--workflow', required=True, help='Path to workflow.json')
    parser.add_argument('--goal', required=True, help='The goal input')
    parser.add_argument('--output', help='Where to save the result')
    args = parser.parse_args()
    llm_config = OpenAILLMConfig(model='gpt-4o', openai_key=os.getenv('OPENAI_API_KEY'), stream=True, output_response=True, max_tokens=16000)
    llm = OpenAILLM(config=llm_config)
    workdir = os.path.dirname(args.workflow)
    tools = load_tools_from_json(workdir)
    wf_graph = WorkFlowGraph.from_file(args.workflow, llm_config=llm_config, tools=tools)
    agent_manager = AgentManager(tools=tools)
    agent_manager.add_agents_from_workflow(wf_graph, llm_config=llm_config)
    workflow = WorkFlow(graph=wf_graph, agent_manager=agent_manager, llm=llm)
    output = workflow.execute(inputs={'goal': args.goal})
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'✅ Output saved to {args.output}')
    else:
        print('====== Workflow Output ======')
        print(output)

def main():
    """Main function to run the HTML report generator."""
    import argparse
    parser = argparse.ArgumentParser(description='Generate HTML stock analysis report')
    parser.add_argument('output_path', help='Path for the generated HTML file')
    parser.add_argument('md_file', help='Path to the markdown file')
    parser.add_argument('technical_chart', help='Path to technical analysis chart')
    parser.add_argument('price_volume_chart', help='Path to price/volume chart')
    args = parser.parse_args()
    generator = HTMLGenerator(args.output_path)
    output_file = generator.generate_report(args.md_file, args.technical_chart, args.price_volume_chart)
    print(f'HTML report generated successfully: {output_file}')

def execute_workflow(stock_code, data_dir, report_dir, timestamp):
    """Execute the workflow with the given parameters"""
    try:
        workflow_file = 'workflow.json'
        if platform.system() == 'Windows':
            workflow_file = 'workflow_windows.json'
        workflow_graph = WorkFlowGraph.from_file(workflow_file, llm_config=llm.config, tools=tools)
        agent_manager = AgentManager(tools=tools)
        agent_manager.add_agents_from_workflow(workflow_graph, llm_config=llm.config)
        workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
        workflow.init_module()
        output_file = report_dir / f'text_report_{stock_code}_{timestamp}.md'
        past_report = report_dir / f'text_report_{stock_code}_{timestamp}_previous.md'
        goal = f'I need a daily trading decision for stock {stock_code}.\nAvailable funds: {available_funds} RMB\nCurrent positions: {current_positions} shares of {stock_code} at average price {average_price} RMB\nDate: {report_date}\nType of position: {position_type}\nData folder: {data_dir}\nPast report folder: {past_report}\n\nPlease read ALL files in the data folder and generate a comprehensive trading decision report in Chinese based on real data. Return the complete content.\n'
        output = workflow.execute({'goal': goal})
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f'Trading decision report saved to: {output_file}')
        except Exception as e:
            print(f'Error saving report: {e}')
    except Exception as e:
        print(f'Error executing workflow: {e}')
        import traceback
        traceback.print_exc()

def generate_html_report(stock_code, base_dir, report_dir, graphs_dir, timestamp):
    """Generate HTML report from markdown and charts"""
    try:
        from html_report_generator import HTMLGenerator
        md_file = report_dir / f'text_report_{stock_code}_{timestamp}.md'
        html_output = base_dir / datetime.now().strftime('%Y%m%d') / 'html_report' / f'report_{stock_code}_{timestamp}.html'
        technical_chart = graphs_dir / f'{stock_code}_technical_charts.png'
        price_volume_chart = graphs_dir / f'{stock_code}_candlestick_chart.png'
        if not md_file.exists():
            print(f'❌ Markdown file not found: {md_file}')
            return False
        if not technical_chart.exists():
            print(f'⚠️  Technical chart not found: {technical_chart}')
            technical_chart = ''
        if not price_volume_chart.exists():
            print(f'⚠️  Price/volume chart not found: {price_volume_chart}')
            price_volume_chart = ''
        print(f'[4] 生成HTML报告: {html_output}')
        generator = HTMLGenerator(str(html_output))
        output_file = generator.generate_report(str(md_file), str(technical_chart) if technical_chart else '', str(price_volume_chart) if price_volume_chart else '')
        print(f'✅ HTML报告生成成功: {output_file}')
        print(f'📁 资源文件夹: {Path(output_file).parent / 'assets'}')
        print(f'🌐 在浏览器中打开HTML文件查看报告')
        return True
    except Exception as e:
        print(f'❌ HTML报告生成失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    llm_config = OpenAILLMConfig(model='gpt-4o-mini-2024-07-18', openai_key=OPENAI_API_KEY, top_p=0.85, temperature=0.2, frequency_penalty=0.0, presence_penalty=0.0)
    llm = OpenAILLM(config=llm_config)
    sew_graph = SEWWorkFlowGraph(llm_config=llm_config)
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(sew_graph, llm_config=llm_config)
    humaneval = HumanEvalSplits()

    def collate_func(example: dict) -> dict:
        return {'question': example['prompt']}
    evaluator = Evaluator(llm=llm, agent_manager=agent_manager, collate_func=collate_func, num_workers=20, verbose=True)
    optimizer = SEWOptimizer(graph=sew_graph, evaluator=evaluator, llm=llm, max_steps=10, eval_rounds=1, repr_scheme='python', optimize_mode='prompt', order='zero-order')
    with suppress_logger_info():
        metrics = optimizer.evaluate(dataset=humaneval, eval_mode='test')
    print('Evaluation metrics: ', metrics)
    optimizer.optimize(dataset=humaneval)
    with suppress_logger_info():
        metrics = optimizer.evaluate(dataset=humaneval, eval_mode='test')
    print('Evaluation metrics: ', metrics)
    optimizer.save('debug/optimized_sew_workflow.json')

@register_parse_function
def custom_parse_func(content: str) -> str:
    return {'code': extract_code_blocks(content)[0]}

def build_sequential_workflow():
    llm_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY, stream=True, output_response=True)
    llm = OpenAILLM(llm_config)
    tasks = [{'name': 'Planning', 'description': 'Create a detailed plan for code generation', 'inputs': [{'name': 'problem', 'type': 'str', 'required': True, 'description': 'Description of the problem to be solved'}], 'outputs': [{'name': 'plan', 'type': 'str', 'required': True, 'description': 'Detailed plan with steps, components, and architecture'}], 'prompt': 'You are a software architect. Your task is to create a detailed implementation plan for the given problem.\n\nProblem: {problem}\n\nPlease provide a comprehensive implementation plan including:\n1. Problem breakdown\n2. Algorithm or approach selection\n3. Implementation steps\n4. Potential edge cases and solutions', 'parse_mode': 'str'}, {'name': 'Coding', 'description': 'Implement the code based on the implementation plan', 'inputs': [{'name': 'problem', 'type': 'str', 'required': True, 'description': 'Description of the problem to be solved'}, {'name': 'plan', 'type': 'str', 'required': True, 'description': 'Detailed implementation plan from the Planning phase'}], 'outputs': [{'name': 'code', 'type': 'str', 'required': True, 'description': 'Implemented code with explanations'}], 'prompt': 'You are a software developer. Your task is to implement the code based on the provided problem and implementation plan.\n\nProblem: {problem}\nImplementation Plan: {plan}\n\nPlease provide the implementation code with appropriate comments.', 'parse_mode': 'custom', 'parse_func': custom_parse_func, 'tool_names': ['FileToolkit']}]
    graph = SequentialWorkFlowGraph(goal='Generate code to solve programming problems', tasks=tasks)
    graph.save_module('debug/tool/sequential_workflow.json')
    graph = SequentialWorkFlowGraph.from_file('debug/tool/sequential_workflow.json')
    agent_manager = AgentManager(tools=[FileToolkit()])
    agent_manager.add_agents_from_workflow(graph, llm_config=llm_config)
    workflow = WorkFlow(graph=graph, agent_manager=agent_manager, llm=llm)
    output = workflow.execute(inputs={'problem': 'Write a function to find the longest palindromic substring in a given string. Save the code to local file: ./debug/test.py'})
    print('Workflow completed!')
    print('Workflow output:\n', output)

def main():
    llm_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
    llm = OpenAILLM(config=llm_config)
    benchmark = HotPotQA(mode='dev')
    workflow = QAActionGraph(llm_config=llm_config, description='This workflow aims to address multi-hop QA tasks.')

    def collate_func(example: dict) -> dict:
        """
        Args:
            example (dict): A dictionary containing the raw example data.

        Returns: 
            The expected input for the (custom) workflow.
        """
        problem = 'Question: {}\n\n'.format(example['question'])
        context_list = []
        for item in example['context']:
            context = 'Title: {}\nText: {}'.format(item[0], ' '.join([t.strip() for t in item[1]]))
            context_list.append(context)
        context = '\n\n'.join(context_list)
        problem += 'Context: {}\n\n'.format(context)
        problem += 'Answer:'
        return {'problem': problem}

    def output_postprocess_func(output: dict) -> dict:
        """
        Args:
            output (dict): The output from the workflow.

        Returns: 
            The processed output that can be used to compute the metrics. The output will be directly passed to the benchmark's `evaluate` method. 
        """
        return output['answer']
    evaluator = Evaluator(llm=llm, collate_func=collate_func, output_postprocess_func=output_postprocess_func, verbose=True, num_workers=3)
    with suppress_logger_info():
        results = evaluator.evaluate(graph=workflow, benchmark=benchmark, eval_mode='dev', sample_k=6)
    print('Evaluation metrics: ', results)

def demo_basic_functionality():
    """Demonstrate basic ActionAgent functionality."""
    print('1. Basic Functionality:')
    math_agent = ActionAgent(name='MathAgent', description='Performs mathematical operations', inputs=[{'name': 'a', 'type': 'int', 'description': 'First number', 'required': True}, {'name': 'b', 'type': 'int', 'description': 'Second number', 'required': True}], outputs=[{'name': 'result', 'type': 'int', 'description': 'Sum of the numbers', 'required': True}], execute_func=add_numbers)
    result = math_agent(inputs={'a': 5, 'b': 3})
    print(f'   Math Agent Result: {result.content.result}')

def demo_async_functionality():
    """Demonstrate async ActionAgent functionality."""
    print('\n2. Async Functionality:')

    async def run_async_demo():
        data_agent = ActionAgent(name='DataAgent', description='Fetches data from URLs', inputs=[{'name': 'url', 'type': 'str', 'description': 'URL to fetch', 'required': True}], outputs=[{'name': 'result', 'type': 'str', 'description': 'Fetched data', 'required': True}], execute_func=fetch_data_async, async_execute_func=fetch_data_async)
        result = await data_agent(inputs={'url': 'https://api.example.com'})
        print(f'   Data Agent Result: {result.content.result}')
    asyncio.run(run_async_demo())

def demo_error_handling():
    """Demonstrate ActionAgent error handling."""
    print('\n3. Error Handling:')
    divide_agent = ActionAgent(name='DivideAgent', description='Divides numbers with error handling', inputs=[{'name': 'a', 'type': 'int', 'description': 'Numerator', 'required': True}, {'name': 'b', 'type': 'int', 'description': 'Denominator', 'required': True}], outputs=[{'name': 'result', 'type': 'float', 'description': 'Quotient', 'required': False}, {'name': 'error', 'type': 'str', 'description': 'Error message if any', 'required': False}], execute_func=divide_numbers)
    result = divide_agent(inputs={'a': 10, 'b': 2})
    print(f'   Normal division: {result.content.result}')
    error_result = divide_agent(inputs={'a': 10, 'b': 0})
    print(f'   Division by zero: {error_result.content.error}')

def demo_validation():
    """Demonstrate ActionAgent for data validation."""
    print('\n4. Data Validation:')
    email_agent = ActionAgent(name='EmailValidator', description='Validates email addresses', inputs=[{'name': 'email', 'type': 'str', 'description': 'Email address to validate', 'required': True}], outputs=[{'name': 'email', 'type': 'str', 'description': 'Input email address', 'required': True}, {'name': 'is_valid', 'type': 'bool', 'description': 'Whether email is valid', 'required': True}, {'name': 'domain', 'type': 'str', 'description': 'Email domain', 'required': False}, {'name': 'validation_message', 'type': 'str', 'description': 'Validation result message', 'required': True}], execute_func=validate_email)
    test_emails = ['user@example.com', 'invalid-email', 'test@domain.co.uk']
    for email in test_emails:
        result = email_agent(inputs={'email': email})
        status = '✅' if result.content.is_valid else '❌'
        print(f'   {status} {result.content.email} → {result.content.validation_message}')

def demo_auto_async_wrapper():
    """Demonstrate ActionAgent with auto-generated async wrapper."""
    print('\n5. Auto Async Wrapper:')

    def multiply_numbers(x: int, y: int) -> int:
        """Multiply two numbers."""
        return x * y
    multiply_agent = ActionAgent(name='MultiplyAgent', description='Multiplies numbers', inputs=[{'name': 'x', 'type': 'int', 'description': 'First number', 'required': True}, {'name': 'y', 'type': 'int', 'description': 'Second number', 'required': True}], outputs=[{'name': 'result', 'type': 'int', 'description': 'Product of the numbers', 'required': True}], execute_func=multiply_numbers)

    async def run_async():
        result = await multiply_agent(inputs={'x': 6, 'y': 8})
        print(f'   Async multiply result: {result.content.result}')
    asyncio.run(run_async())

def demo_input_validation():
    """Demonstrate ActionAgent input validation."""
    print('\n7. Input Validation:')

    def add_numbers(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b
    agent = ActionAgent(name='ValidAgent', description='Valid agent', inputs=[{'name': 'a', 'type': 'int', 'description': 'First number', 'required': True}, {'name': 'b', 'type': 'int', 'description': 'Second number', 'required': True}], outputs=[{'name': 'result', 'type': 'int', 'description': 'Sum', 'required': True}], execute_func=add_numbers)
    try:
        result = agent(inputs={'a': 5, 'b': 3})
        print(f'   ✅ Valid inputs: {result.content.result}')
    except Exception as e:
        print(f'   ❌ Valid inputs failed: {e}')
    try:
        result = agent(inputs={'a': 5})
        print(f'   ❌ Should have failed for missing input, but got: {result}')
    except ValueError as e:
        print(f'   ✅ Correctly caught missing input error: {e}')

def demo_advanced_error_handling():
    """Demonstrate ActionAgent with advanced error handling scenarios."""
    print('\n9. Advanced Error Handling:')
    error_agent = ActionAgent(name='ErrorProneAgent', description='Tests various error scenarios', inputs=[{'name': 'input_data', 'type': 'any', 'description': 'Input data that may cause errors', 'required': True}], outputs=[{'name': 'input_type', 'type': 'str', 'description': 'Type of input data', 'required': False}, {'name': 'input_value', 'type': 'any', 'description': 'Input value', 'required': False}, {'name': 'processed', 'type': 'bool', 'description': 'Whether processing succeeded', 'required': False}, {'name': 'timestamp', 'type': 'float', 'description': 'Processing timestamp', 'required': False}, {'name': 'error', 'type': 'str', 'description': 'Error message if any', 'required': False}], execute_func=error_prone_function)
    test_cases = [{'input_data': 'normal'}, {'input_data': 'crash'}, {'input_data': None}, {'input_data': -5}, {'input_data': 2000}]
    for i, test_case in enumerate(test_cases, 1):
        try:
            result = error_agent(inputs=test_case)
            if hasattr(result.content, 'error'):
                print(f'   Test {i} error: {result.content.error}')
            else:
                print(f'   Test {i} success: {result.content.input_type} = {result.content.input_value}')
        except Exception as e:
            print(f'   Test {i} exception: {e}')

def demo_edge_cases():
    """Demonstrate ActionAgent edge cases."""
    print('\n10. Edge Cases:')
    no_input_agent = ActionAgent(name='NoInputAgent', description='Agent with no inputs', inputs=[], outputs=[{'name': 'message', 'type': 'str', 'description': 'Simple message', 'required': True}], execute_func=lambda: 'Hello from no-input agent')
    result = no_input_agent(inputs={})
    print(f'   No-input agent: {result.content.message}')
    unexpected_agent = ActionAgent(name='UnexpectedInputAgent', description='Agent that handles unexpected inputs', inputs=[{'name': 'a', 'type': 'int', 'description': 'First number', 'required': True}, {'name': 'b', 'type': 'int', 'description': 'Second number', 'required': True}], outputs=[{'name': 'result', 'type': 'int', 'description': 'Sum', 'required': True}], execute_func=add_numbers)
    result = unexpected_agent(inputs={'a': 5, 'b': 3, 'c': 10, 'd': 'extra'})
    print(f'   Unexpected inputs agent: {result.content.result}')

def demo_basic_workflow():
    """Demonstrate basic workflow without tools"""
    print('Basic Workflow Demo - Creating a Python Calculator Application')
    print('=' * 70)
    api_key = load_api_key()
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=api_key, stream=True, output_response=True, max_tokens=8000)
    llm = OpenAILLM(config=openai_config)
    goal = 'Create a simple Python calculator application'
    print(f'Goal: {goal}')
    wf_generator = WorkFlowGenerator(llm=llm)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)
    print('\nGenerated Workflow Structure:')
    workflow_graph.display()
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)
    workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
    print('\nExecuting workflow...')
    output = workflow.execute()
    print('Basic workflow completed successfully')
    print(f'\nOutput (first 500 chars):\n{str(output)[:500]}...')
    return output

def demo_toolkit_workflow():
    """Demonstrate workflow with CMDToolkit for file system operations"""
    print('\nToolkit Workflow Demo - Creating Project Structure with CMDToolkit')
    print('=' * 70)
    api_key = load_api_key()
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=api_key, stream=True, output_response=True, max_tokens=8000)
    llm = OpenAILLM(config=openai_config)
    goal = 'Create a folder structure for a Python project and show the file tree'
    tools = [CMDToolkit()]
    print(f'Goal: {goal}')
    print(f'Tools: {[tool.__class__.__name__ for tool in tools]}')
    wf_generator = WorkFlowGenerator(llm=llm, tools=tools)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)
    print('\nGenerated Workflow Structure with Tools:')
    workflow_graph.display()
    agent_manager = AgentManager(tools=tools)
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)
    workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
    print('\nExecuting workflow with CMDToolkit...')
    output = workflow.execute()
    print('Toolkit workflow completed successfully')
    print(f'\nOutput (first 800 chars):\n{str(output)[:800]}...')
    return output

def demo_workflow_save_load():
    """Demonstrate workflow save and load functionality"""
    print('\nWorkflow Save/Load Demo')
    print('=' * 70)
    api_key = load_api_key()
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=api_key, stream=True, output_response=True, max_tokens=8000)
    llm = OpenAILLM(config=openai_config)
    goal = 'Create a simple Python calculator application'
    wf_generator = WorkFlowGenerator(llm=llm)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)
    save_path = 'demo_workflow.json'
    workflow_graph.save_module(save_path)
    print(f'Workflow saved to: {save_path}')
    loaded_graph = WorkFlowGraph.from_file(save_path)
    print('Workflow loaded successfully')
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(loaded_graph, llm_config=openai_config)
    workflow = WorkFlow(graph=loaded_graph, agent_manager=agent_manager, llm=llm)
    print('Loaded workflow is executable')
    if os.path.exists(save_path):
        os.remove(save_path)
        print(f'Cleaned up temporary file: {save_path}')
    return loaded_graph

def main():
    """Main demonstration function"""
    print('EvoAgentX Workflow Demo with Tools')
    print('=' * 70)
    print('This demo showcases different workflow capabilities:')
    print('1. Basic workflow without tools')
    print('2. Workflow with CMDToolkit for file operations')
    print('3. Workflow save/load functionality')
    print('=' * 70)
    try:
        print('\n' + '=' * 70)
        print('DEMO 1: Basic Workflow')
        print('=' * 70)
        basic_output = demo_basic_workflow()
        print('\n' + '=' * 70)
        print('DEMO 2: Toolkit Workflow')
        print('=' * 70)
        toolkit_output = demo_toolkit_workflow()
        print('\n' + '=' * 70)
        print('DEMO 3: Workflow Save/Load')
        print('=' * 70)
        loaded_workflow = demo_workflow_save_load()
        print('\n' + '=' * 70)
        print('DEMO SUMMARY')
        print('=' * 70)
        print('Basic Workflow Demo: PASSED')
        print('Toolkit Workflow Demo: PASSED')
        print('Workflow Save/Load Demo: PASSED')
        print('\nAll demos completed successfully!')
        print('\nKey Features Demonstrated:')
        print('- Workflow generation from natural language goals')
        print('- Tool integration (CMDToolkit for file operations)')
        print('- Workflow visualization and management')
        print('- Agent creation and management')
        print('- Workflow persistence (save/load)')
        return 0
    except Exception as e:
        print(f'\nDemo failed with error: {str(e)}')
        import traceback
        traceback.print_exc()
        return 1

def test_MCP_server():
    mcp_Toolkit = MCPToolkit(config_path='examples/output/mcp_agent/mcp.config')
    tools = mcp_Toolkit.get_toolkits()
    mcp_agent = CustomizeAgent(name='MCPAgent', description='A MCP agent that can use the tools provided by the MCP server', prompt_template=StringTemplate(instruction="Do some operations based on the user's instruction."), llm_config=openai_config, inputs=[{'name': 'instruction', 'type': 'string', 'description': 'The goal you need to achieve'}], outputs=[{'name': 'result', 'type': 'string', 'description': 'The result of the operation'}], tools=tools)
    mcp_agent.save_module('examples/output/mcp_agent/mcp_agent.json')
    mcp_agent.load_module('examples/output/mcp_agent/mcp_agent.json', llm_config=openai_config, tools=tools)
    message = mcp_agent(inputs={'instruction': 'Summarize all the tools.'})
    print(f'Response from {mcp_agent.name}:')
    print(message.content.result)

@register_parse_function
def extract_code_blocks(content: str) -> dict:
    return {'code': util_extract_code_blocks(content)[0]}

def build_customize_agent():
    agent_data = {'name': 'FirstAgent', 'description': 'A simple agent that prints hello world', 'prompt': "Print 'hello world'", 'llm_config': model_config}
    agent = CustomizeAgent.from_dict(agent_data)
    message: Message = agent()
    print(f'Response from {agent.name}:')
    print(message.content.content)

def build_customize_agent_with_inputs():
    simple_agent = CustomizeAgent(name='SimpleAgent', description='A basic agent that responds to queries', prompt='Answer the following question: {question}', llm_config=model_config, inputs=[{'name': 'question', 'type': 'string', 'description': 'The question to answer'}])
    response = simple_agent(inputs={'question': 'What is a language model?'})
    print(f'Response from {simple_agent.name}:')
    print(response.content.content)

def build_customize_agent_with_inputs_and_outputs():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=model_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code'}], parse_mode='str')
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers'})
    print(f'Response from {code_writer.name}:')
    print(message.content.code)

def build_customize_agent_with_custom_parse_func():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=model_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code'}], parse_mode='custom', parse_func=lambda content: {'code': util_extract_code_blocks(content)[0]})
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers'})
    print(f'Response from {code_writer.name}:')
    print(message.content.code)

def build_customize_agent_with_prompt_template():
    agent = CustomizeAgent(name='FirstAgent', description='A simple agent that prints hello world', prompt_template=StringTemplate(instruction="Print 'hello world'"), llm_config=model_config)
    message = agent()
    print(f'Response from {agent.name}:')
    print(message.content.content)

def build_customize_agent_with_chat_prompt_template():
    agent = CustomizeAgent(name='FirstAgent', description='A simple agent that prints hello world', prompt_template=ChatTemplate(instruction="Print 'hello world'"), llm_config=model_config)
    message = agent()
    print(f'Response from {agent.name}:')
    print(message.content.content)

def build_customize_agent_with_inputs_and_outputs_and_prompt_template():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt_template=StringTemplate(instruction='Write Python code that implements the provided `requirement`'), llm_config=model_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code'}], parse_mode='custom', parse_func=lambda content: {'code': util_extract_code_blocks(content)[0]})
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers'})
    print(f'Response from {code_writer.name}:')
    print(message.content.code)

def build_customize_agent_with_tools():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt_template=StringTemplate(instruction='Write Python code that implements the provided `requirement` and save the code to the provided `file_path`'), llm_config=model_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}, {'name': 'file_path', 'type': 'string', 'description': 'The path to save the code'}], tools=[FileToolkit()])
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers', 'file_path': 'examples/output/test_code.py'})
    print(f'Response from {code_writer.name}:')
    print(message.content.content)

def build_customize_agent_with_MCP(config_path):
    mcp_Toolkit = MCPToolkit(config_path=config_path)
    tools = mcp_Toolkit.get_toolkits()
    customize_agent = CustomizeAgent(name='MCPToolUser', description='Do some tasks using the tools', prompt_template=StringTemplate(instruction='Do some tasks using the tools'), llm_config=model_config, inputs=[{'name': 'instruction', 'type': 'string', 'description': 'The instruction to the tool user'}], outputs=[{'name': 'result', 'type': 'string', 'description': 'The result of the task'}, {'name': 'tool_calls', 'type': 'string', 'description': 'The tool calls used to get the result (if any)'}], tools=tools)
    message = customize_agent(inputs={'instruction': 'Summarize all your tools.'})
    print(f'Response from {customize_agent.name}:')
    print(message.content)

def build_customize_agent_with_custom_parse_and_format():
    """Test case demonstrating custom parse function and output format with XML."""

    def custom_xml_parser(content: str) -> dict:
        """Custom parser that extracts data from XML-like format."""
        result = {}
        for field in ['name', 'age', 'occupation']:
            start_tag = f'<{field}>'
            end_tag = f'</{field}>'
            try:
                start_idx = content.index(start_tag) + len(start_tag)
                end_idx = content.index(end_tag)
                result[field] = content[start_idx:end_idx].strip()
            except ValueError:
                result[field] = ''
        return result
    person_info_agent = CustomizeAgent(name='PersonInfoExtractor', description='Extracts structured person information in XML format', prompt_template=StringTemplate(instruction='Extract information about the following person: `person_description`'), llm_config=model_config, inputs=[{'name': 'person_description', 'type': 'string', 'description': 'Description of the person'}], outputs=[{'name': 'name', 'type': 'string', 'description': "Person's name"}, {'name': 'age', 'type': 'string', 'description': "Person's age"}, {'name': 'occupation', 'type': 'string', 'description': "Person's occupation"}], parse_mode='custom', parse_func=custom_xml_parser, custom_output_format="Please format your response in XML tags:\n<name>person's name</name>\n<age>person's age</age>\n<occupation>person's occupation</occupation>")
    message = person_info_agent(inputs={'person_description': 'John is a 35-year-old software engineer who loves coding.'})
    print(f'Response from {person_info_agent.name}:')
    print('Name:', message.content.name)
    print('Age:', message.content.age)
    print('Occupation:', message.content.occupation)

def build_customize_agent_with_json_parse():
    """Test case demonstrating JSON parse mode for structured data extraction."""
    print('Test case: build_customize_agent_with_json_parse')
    recipe_analyzer = CustomizeAgent(name='RecipeAnalyzer', description='Analyzes recipe information and returns structured data', prompt='Analyze the following recipe and extract key information.\nRecipe: {recipe_text}\n\nPlease format your response as a JSON object with the following structure (all on one line):\n{{\'name\': \'Recipe name\', \'prep_time_minutes\': "12", \'ingredients\': [\'ingredient1\', \'ingredient2\', ...], \'difficulty\': \'easy|medium|hard\'}}', llm_config=model_config, inputs=[{'name': 'recipe_text', 'type': 'string', 'description': 'The recipe text to analyze'}], outputs=[{'name': 'name', 'type': 'string', 'description': 'Name of the recipe'}, {'name': 'prep_time_minutes', 'type': 'string', 'description': 'Preparation time in minutes'}, {'name': 'ingredients', 'type': 'list', 'description': 'List of ingredients'}, {'name': 'difficulty', 'type': 'string', 'description': 'Difficulty level of the recipe'}], parse_mode='json')
    sample_recipe = '\n    Classic Chocolate Chip Cookies\n    \n    Mix 2 1/4 cups flour, 1 cup butter, 3/4 cup sugar, 2 eggs, \n    1 tsp vanilla extract, and 2 cups chocolate chips. \n    Bake at 375°F for 10-12 minutes.\n    Total prep time: 25 minutes.\n    '
    message = recipe_analyzer(inputs={'recipe_text': sample_recipe})
    print(f'\nResponse from {recipe_analyzer.name}:')
    print('Recipe Name:', message.content.name)
    print('Prep Time:', message.content.prep_time_minutes, 'minutes')
    print('Ingredients:', ', '.join(message.content.ingredients))
    print('Difficulty:', message.content.difficulty)

def test_str_parse_mode():
    """Test case demonstrating string parse mode."""
    print('\nTest case: test_str_parse_mode')
    simple_agent = CustomizeAgent(name='SimpleGreeter', description='A simple agent that generates greetings', prompt='Generate a greeting for {name}', llm_config=model_config, inputs=[{'name': 'name', 'type': 'string', 'description': 'The name to greet'}], outputs=[{'name': 'greeting', 'type': 'string', 'description': 'The generated greeting'}], parse_mode='str')
    message = simple_agent(inputs={'name': 'Alice'})
    print(f'Response from {simple_agent.name}:')
    print('Raw content:', message.content.content)
    print('Greeting field:', message.content.greeting)

def test_title_parse_mode():
    """Test case demonstrating title parse mode."""
    print('\nTest case: test_title_parse_mode')
    report_agent = CustomizeAgent(name='ReportGenerator', description='Generates a structured report', prompt='Create a report about {topic} with summary and analysis sections, less than 200 words, section title format: ### title', llm_config=model_config, inputs=[{'name': 'topic', 'type': 'string', 'description': 'The topic to analyze'}], outputs=[{'name': 'summary', 'type': 'string', 'description': 'Brief summary'}, {'name': 'analysis', 'type': 'string', 'description': 'Detailed analysis'}], parse_mode='title', title_format='### {title}')
    message = report_agent(inputs={'topic': 'Artificial Intelligence'})
    print(f'Response from {report_agent.name}:')
    print('Summary:', message.content.summary)
    print('Analysis:', message.content.analysis)

def test_xml_parse_mode():
    """Test case demonstrating XML parse mode."""
    print('\nTest case: test_xml_parse_mode')
    extractor_agent = CustomizeAgent(name='DataExtractor', description='Extracts structured data', prompt='Extract key information from this text: {text}\n        Format your response using XML tags for each field.\n        Example format:\n        The people mentioned are: <people>John and Jane</people>\n        The places mentioned are: <places>New York and London</places>', llm_config=model_config, inputs=[{'name': 'text', 'type': 'string', 'description': 'The text to extract information from'}], outputs=[{'name': 'people', 'type': 'string', 'description': 'Names of people mentioned'}, {'name': 'places', 'type': 'string', 'description': 'Locations mentioned'}], parse_mode='xml')
    sample_text = 'John and Jane visited New York and London last summer.'
    message = extractor_agent(inputs={'text': sample_text})
    print(f'Response from {extractor_agent.name}:')
    print('People:', message.content.people)
    print('Places:', message.content.places)

def test_str_parse_mode_with_template():
    """Test case demonstrating string parse mode with PromptTemplate."""
    print('\nTest case: test_str_parse_mode_with_template')
    simple_agent = CustomizeAgent(name='SimpleGreeter', description='A simple agent that generates greetings', prompt_template=StringTemplate(instruction='Generate a friendly greeting for the provided `name`', constraints=['Keep the greeting concise and friendly', 'Use proper capitalization']), llm_config=model_config, inputs=[{'name': 'name', 'type': 'string', 'description': 'The name to greet'}], outputs=[{'name': 'greeting', 'type': 'string', 'description': 'The generated greeting'}], parse_mode='str')
    message = simple_agent(inputs={'name': 'Alice'})
    print(f'Response from {simple_agent.name}:')
    print('Raw content:', message.content.content)
    print('Greeting field:', message.content.greeting)

def test_title_parse_mode_with_template():
    """Test case demonstrating title parse mode with PromptTemplate."""
    print('\nTest case: test_title_parse_mode_with_template')
    report_agent = CustomizeAgent(name='ReportGenerator', description='Generates a structured report', prompt_template=StringTemplate(instruction='Create a comprehensive report about the provided `topic`', constraints=['Keep each section under 100 words', 'Use professional language', 'Be specific and factual'], context='You are a professional report writer with expertise in creating concise, informative reports.'), llm_config=model_config, inputs=[{'name': 'topic', 'type': 'string', 'description': 'The topic to analyze'}], outputs=[{'name': 'summary', 'type': 'string', 'description': 'Brief summary of key points'}, {'name': 'analysis', 'type': 'string', 'description': 'Detailed analysis and implications'}], parse_mode='title', title_format='### {title}')
    message = report_agent(inputs={'topic': 'Artificial Intelligence'})
    print(f'Response from {report_agent.name}:')
    print('Summary:', message.content.summary)
    print('Analysis:', message.content.analysis)

def test_xml_parse_mode_with_template():
    """Test case demonstrating XML parse mode with PromptTemplate."""
    print('\nTest case: test_xml_parse_mode_with_template')
    extractor_agent = CustomizeAgent(name='DataExtractor', description='Extracts structured data', prompt_template=StringTemplate(instruction='Extract key information from the provided `text`', context='You are an expert at extracting structured information from text.', constraints=['Use XML tags to structure the output', 'Extract all relevant people and places', 'Maintain original spelling of names'], demonstrations=[{'text': 'Sarah and Mike went to Paris.', 'output': 'Found the following information:\n                    <people>Sarah and Mike</people>\n                    <places>Paris</places>'}]), llm_config=model_config, inputs=[{'name': 'text', 'type': 'string', 'description': 'The text to extract information from'}], outputs=[{'name': 'people', 'type': 'string', 'description': 'Names of people mentioned'}, {'name': 'places', 'type': 'string', 'description': 'Locations mentioned'}], parse_mode='xml')
    sample_text = 'John and Jane visited New York and London last summer.'
    message = extractor_agent(inputs={'text': sample_text})
    print(f'Response from {extractor_agent.name}:')
    print('People:', message.content.people)
    print('Places:', message.content.places)

def main(goal=None):
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY, stream=True, output_response=True, max_tokens=16000)
    llm = OpenAILLM(config=openai_config)
    goal = "Read and analyze the candidate's pdf resume at examples/output/direction/test_pdf.pdf, and recommend one future PHD directions based on the resume. You should provide a list of 5 review papers about the topic for the candidate to learn more about this direction as well."
    helper_prompt = 'The input is one parameter called "goal", and the output is a markdown report. \n    You should firstly read the pdf resume and summarize the background and recommend one future PHD direction based on the resume.\n    Then you should find 3 trending Review Papers about the topic by searching the keyword on arxiv (by searching web instead of using your out-dated training data) and provide the link of the papers.\n    Lastly you should summarize all the information and provide a detailed markdown report.\n    If you cannot find the papers, you should say "I cannot find the papers".\n    '
    goal += helper_prompt
    mcp_Toolkit = MCPToolkit(config_path=mcp_config_path)
    tools = mcp_Toolkit.get_toolkits()
    tools.append(FileToolkit())
    workflow_graph: WorkFlowGraph = WorkFlowGraph.from_file(module_save_path)
    agent_manager = AgentManager(tools=tools)
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)
    workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
    output = workflow.execute()
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'Direction recommendations have been saved to {output_file}')
    except Exception as e:
        print(f'Error saving direction recommendations: {e}')
    print(output)

def main():
    openai_config = OpenAILLMConfig(model='gpt-4o', openai_key=OPENAI_API_KEY, stream=True, output_response=True, max_tokens=16000)
    llm = OpenAILLM(config=openai_config)
    keywords = 'medical, multiagent'
    max_results = 10
    date_from = '2024-01-01'
    categories = ['cs.AI', 'cs.LG']
    search_constraints = f'\n    Search constraints:\n    - Query keywords: {keywords}\n    - Max results: {max_results}\n    - Date from: {date_from}\n    - Categories: {', '.join(categories)}\n    '
    goal = f'Create a daily research paper recommendation assistant that takes user keywords and pushes new relevant papers with summaries.\n\n    The assistant should:\n    1. Use the ArxivToolkit to search for the latest papers using the given keywords.\n    2. Apply the following search constraints:\n    {search_constraints}\n    3. Summarize the search results.\n    4. Compile the summaries into a well-formatted Markdown digest.\n\n    ### Output\n    daily_paper_digest\n    '
    target_directory = 'EvoAgentX/examples/output/paper_push'
    module_save_path = os.path.join(target_directory, 'paper_push_workflow.json')
    result_path = os.path.join(target_directory, 'daily_paper_digest.md')
    os.makedirs(target_directory, exist_ok=True)
    arxiv_toolkit = ArxivToolkit()
    tools = [arxiv_toolkit, FileToolkit()]
    wf_generator = WorkFlowGenerator(llm=llm, tools=tools)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)
    workflow_graph.save_module(module_save_path)
    workflow_graph.display()
    agent_manager = AgentManager(tools=tools)
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)
    workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
    output = workflow.execute()
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f'✅ Your file has been saved to：{result_path}')
    print('📬 You can run this script everyday to obtain daily recommendation')

def main():
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY, stream=True, output_response=True, max_tokens=16000)
    llm = OpenAILLM(config=openai_config)
    goal = 'Generate html code for the Tetris game that can be played in the browser.'
    target_directory = 'examples/output/tetris_game'
    wf_generator = WorkFlowGenerator(llm=llm)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)
    workflow_graph.display()
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)
    workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
    output = workflow.execute()
    verification_llm_config = LiteLLMConfig(model='anthropic/claude-3-7-sonnet-20250219', anthropic_key=ANTHROPIC_API_KEY, stream=True, output_response=True, max_tokens=20000)
    verification_llm = LiteLLM(config=verification_llm_config)
    code_verifier = CodeVerification()
    output = code_verifier.execute(llm=verification_llm, inputs={'requirements': goal, 'code': output}).verified_code
    os.makedirs(target_directory, exist_ok=True)
    code_blocks = extract_code_blocks(output)
    if len(code_blocks) == 1:
        file_path = os.path.join(target_directory, 'index.html')
        with open(file_path, 'w') as f:
            f.write(code_blocks[0])
        print(f'You can open this HTML file in a browser to play the Tetris game: {file_path}')
        return
    code_extractor = CodeExtraction()
    results = code_extractor.execute(llm=llm, inputs={'code_string': output, 'target_directory': target_directory})
    print(f'Extracted {len(results.extracted_files)} files:')
    for filename, path in results.extracted_files.items():
        print(f'  - {filename}: {path}')
    if results.main_file:
        print(f'\nMain file: {results.main_file}')
        file_type = os.path.splitext(results.main_file)[1].lower()
        if file_type == '.html':
            print(f'You can open this HTML file in a browser to play the Tetris game')
        else:
            print(f'This is the main entry point for your application')

def main():
    if len(sys.argv) != 5:
        print('Usage: python generate_report.py <output_path> <md_file> <technical_chart> <price_volume_chart>')
        print('Example: python generate_report.py reports/300750_report.html 300750/reports/output_300750_20250725.md charts/technical.png charts/price_volume.png')
        sys.exit(1)
    output_path = sys.argv[1]
    md_file = sys.argv[2]
    technical_chart = sys.argv[3]
    price_volume_chart = sys.argv[4]
    if not os.path.exists(md_file):
        print(f'Error: Markdown file not found: {md_file}')
        sys.exit(1)
    if not os.path.exists(technical_chart):
        print(f'Warning: Technical chart not found: {technical_chart}')
        technical_chart = ''
    if not os.path.exists(price_volume_chart):
        print(f'Warning: Price/volume chart not found: {price_volume_chart}')
        price_volume_chart = ''
    try:
        generator = HTMLGenerator(output_path)
        output_file = generator.generate_report(md_file, technical_chart, price_volume_chart)
        print(f'✅ HTML report generated successfully: {output_file}')
        print(f'📁 Assets folder: {Path(output_file).parent / 'assets'}')
        print(f'🌐 Open the HTML file in your browser to view the report')
    except Exception as e:
        print(f'❌ Error generating report: {e}')
        sys.exit(1)

def main():
    """Main function to run the HTML report generator."""
    import argparse
    parser = argparse.ArgumentParser(description='Generate HTML stock analysis report')
    parser.add_argument('output_path', help='Path for the generated HTML file')
    parser.add_argument('md_file', help='Path to the markdown file')
    parser.add_argument('technical_chart', help='Path to technical analysis chart')
    parser.add_argument('price_volume_chart', help='Path to price/volume chart')
    args = parser.parse_args()
    generator = HTMLGenerator(args.output_path)
    output_file = generator.generate_report(args.md_file, args.technical_chart, args.price_volume_chart)
    print(f'HTML report generated successfully: {output_file}')

def generate_workflow():
    """Generate a new workflow (commented out for future use)"""
    wf_generator = WorkFlowGenerator(llm=llm, tools=tools)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=WORKFLOW_GOAL, retry=5)
    workflow_graph.save_module(module_save_path)
    return workflow_graph

def execute_workflow(stock_code, data_dir, report_dir, timestamp):
    """Execute the workflow with the given parameters"""
    try:
        workflow_graph: WorkFlowGraph = WorkFlowGraph.from_file(module_save_path)
        agent_manager = AgentManager(tools=tools)
        agent_manager.add_agents_from_workflow(workflow_graph, llm_config=llm.config)
        workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
        workflow.init_module()
        output_file = report_dir / f'text_report_{stock_code}_{timestamp}.md'
        past_report = report_dir / f'text_report_{stock_code}_{timestamp}_previous.md'
        goal = f'I need a daily trading decision for stock {stock_code}.\nAvailable funds: {available_funds} RMB\nCurrent positions: {current_positions} shares of {stock_code} at average price {average_price} RMB\nDate: {report_date}\nType of position: {position_type}\nData folder: {data_dir}\nPast report folder: {past_report}\n\nPlease read ALL files in the data folder and generate a comprehensive trading decision report in Chinese based on real data. Return the complete content.\n'
        output = workflow.execute({'goal': goal})
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f'Trading decision report saved to: {output_file}')
        except Exception as e:
            print(f'Error saving report: {e}')
    except Exception as e:
        print(f'Error executing workflow: {e}')
        import traceback
        traceback.print_exc()

def generate_html_report(stock_code, base_dir, report_dir, graphs_dir, timestamp):
    """Generate HTML report from markdown and charts"""
    try:
        from html_report_generator import HTMLGenerator
        md_file = report_dir / f'text_report_{stock_code}_{timestamp}.md'
        html_output = base_dir / datetime.now().strftime('%Y%m%d') / 'html_report' / f'report_{stock_code}_{timestamp}.html'
        technical_chart = graphs_dir / f'{stock_code}_technical_charts.png'
        price_volume_chart = graphs_dir / f'{stock_code}_candlestick_chart.png'
        if not md_file.exists():
            print(f'❌ Markdown file not found: {md_file}')
            return False
        if not technical_chart.exists():
            print(f'⚠️  Technical chart not found: {technical_chart}')
            technical_chart = ''
        if not price_volume_chart.exists():
            print(f'⚠️  Price/volume chart not found: {price_volume_chart}')
            price_volume_chart = ''
        print(f'[4] 生成HTML报告: {html_output}')
        generator = HTMLGenerator(str(html_output))
        output_file = generator.generate_report(str(md_file), str(technical_chart) if technical_chart else '', str(price_volume_chart) if price_volume_chart else '')
        print(f'✅ HTML报告生成成功: {output_file}')
        print(f'📁 资源文件夹: {Path(output_file).parent / 'assets'}')
        print(f'🌐 在浏览器中打开HTML文件查看报告')
        return True
    except Exception as e:
        print(f'❌ HTML报告生成失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def run_optimized_debate():
    """Run optimized debate: select most suitable model based on role characteristics"""
    print('=== Optimized Debate: Intelligent Role-Model Matching ===')
    roles, models, mapping = create_role_model_mapping()
    selected_roles = ['Analyst', 'Innovator', 'Skeptic', 'Advocate', 'Mediator']
    agents = []
    for role in selected_roles:
        model_name, temp_adjust = mapping[role]
        model_config = models[model_name]
        agent = create_optimized_agent(role, roles[role], model_config, temp_adjust)
        agents.append(agent)
    graph = MultiAgentDebateActionGraph(debater_agents=agents, llm_config=agents[0].llm_config if agents else None)
    result = graph.execute(problem='Should we invest heavily in AI research? Give a final Yes/No with reasons.', num_agents=5, num_rounds=3, judge_mode='llm_judge', return_transcript=True)
    print('Final Answer:', result.get('final_answer'))
    print('Winner:', result.get('winner'))
    if result.get('winner_answer'):
        print('Winner Answer:', result.get('winner_answer'))
    print('\nRole-Model Matching Strategy:')
    for i, agent in enumerate(agents):
        model_name = agent.llm_config.model if hasattr(agent.llm_config, 'model') else 'Unknown'
        temp = agent.llm_config.temperature if hasattr(agent.llm_config, 'temperature') else 'Unknown'
        print(f'  {agent.name}: {model_name} (Temperature: {temp}) - {roles[agent.name]}')

def main():
    """Main function"""
    print('MultiAgentDebate Advanced Example - Dynamic Role-Model Mapping')
    print('=' * 60)
    if not os.getenv('OPENAI_API_KEY'):
        print('Warning: OPENAI_API_KEY environment variable not set')
    if not os.getenv('OPENROUTER_API_KEY'):
        print('Warning: OPENROUTER_API_KEY environment variable not set')
    run_optimized_debate()

def run_self_consistency_example():
    llm_config = get_llm_config()
    debate = MultiAgentDebateActionGraph(name='MAD Minimal', description='Minimal runnable example for multi-agent debate', llm_config=llm_config)
    fixed_problem = 'How many labeled trees on 10 vertices are there such that vertex 1 has degree exactly 4? Return only the final integer.'
    result = debate.execute(problem=fixed_problem, num_agents=3, num_rounds=5, judge_mode='self_consistency', return_transcript=True)
    print('=== Example: Self-Consistency (Fixed Answer) ===')
    print('Final Answer:', result.get('final_answer'))
    print('Winner:', result.get('winner'))
    print('\nTranscript:')
    for turn in result.get('transcript', []):
        print(f'[Round {turn['round']}] Agent#{turn['agent_id']} ({turn['role']})\nArgument: {turn.get('argument', '').strip()}\nAnswer: {str(turn.get('answer') or '').strip()}\n')

def run_llm_judge_example():
    llm_config = get_llm_config()
    debate = MultiAgentDebateActionGraph(name='MAD Minimal', description='Minimal runnable example for multi-agent debate', llm_config=llm_config)
    open_problem = 'Should AI agent service engineers be required to take an algorithms exam to validate their competencies? Return a final Yes/No and up to five concise reasons, assuming responsibilities include tool/function orchestration, workflow design, RAG integration, evaluation/telemetry, reliability/safety, and rapid delivery.'
    result = debate.execute(problem=open_problem, num_agents=5, num_rounds=5, judge_mode='llm_judge', return_transcript=True)
    print('=== Example: LLM Judge (Open Question) ===')
    print('Final Answer:', result.get('final_answer'))
    print('Winner:', result.get('winner'))
    print('\nTranscript:')
    for turn in result.get('transcript', []):
        print(f'[Round {turn['round']}] Agent#{turn['agent_id']} ({turn['role']})\nArgument: {turn.get('argument', '').strip()}\nAnswer: {str(turn.get('answer') or '').strip()}\n')

def create_sample_agents():
    """Create sample agents"""
    agents = []
    agent1 = CustomizeAgent(name='OptimistAgent', description='Optimistic debater who always sees the positive side of problems', prompt='You are an optimistic debater. Please analyze the problem from a positive perspective: {problem}', llm_config=OpenAILLMConfig(model='gpt-4o-mini', openai_key=os.getenv('OPENAI_API_KEY')), inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem'}], outputs=[{'name': 'argument', 'type': 'str', 'description': 'Argument'}], parse_mode='title')
    agents.append(agent1)
    agent2 = CustomizeAgent(name='PessimistAgent', description='Pessimistic debater who always sees the negative side of problems', prompt='You are a pessimistic debater. Please analyze the problem from a negative perspective: {problem}', llm_config=OpenAILLMConfig(model='gpt-4o-mini', openai_key=os.getenv('OPENAI_API_KEY')), inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem'}], outputs=[{'name': 'argument', 'type': 'str', 'description': 'Argument'}], parse_mode='title')
    agents.append(agent2)
    return agents

def demo_save_and_load():
    """Demonstrate save and load functionality"""
    print('=== Demonstrate Save and Load Functionality ===')
    agents = create_sample_agents()
    graph = MultiAgentDebateActionGraph(name='Demo Debate', description='Demo debate graph', debater_agents=agents, llm_config=agents[0].llm_config if agents else None)
    print('\n1. Get current configuration...')
    config = graph.get_config()
    print(f'Configuration contains {len(config)} fields')
    print(f'Number of agents: {len(config.get('debater_agents', []))}')
    print('\n2. Save configuration to file...')
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        save_path = graph.save_module(temp_path)
        print(f'Configuration saved to temporary file: {save_path}')
    except Exception as e:
        print(f'Failed to save to temp file: {e}')
        files_dir = 'examples/multi_agent_debate/files'
        os.makedirs(files_dir, exist_ok=True)
        save_path = graph.save_module(os.path.join(files_dir, 'demo_debate_config.json'))
        print(f'Configuration saved to files directory: {save_path}')
    print('\n3. Create new instance from configuration dictionary...')
    new_graph_from_dict = MultiAgentDebateActionGraph.from_dict(config)
    print(f'New instance name: {new_graph_from_dict.name}')
    print(f'New instance agent count: {len(new_graph_from_dict.debater_agents or [])}')
    print('\n4. Load new instance from file...')
    new_graph_from_file = MultiAgentDebateActionGraph.load_module(save_path)
    print(f'Loaded instance name: {new_graph_from_file.name}')
    print(f'Loaded instance agent count: {len(new_graph_from_file.debater_agents or [])}')
    print('\n5. Load configuration to existing instance...')
    empty_graph = MultiAgentDebateActionGraph()
    empty_graph.load_module(save_path)
    print(f'Loaded instance name: {empty_graph.name}')
    print(f'Loaded agent count: {len(empty_graph.debater_agents or [])}')
    return save_path

def main():
    """Main function to run all image tool examples"""
    print('===== IMAGE TOOL EXAMPLES =====')
    print('\n===== ALL IMAGE TOOL EXAMPLES COMPLETED =====')

def main():
    """Main function to run all database tool examples."""
    print('===== DATABASE TOOLS EXAMPLES =====\n')
    run_mongodb_examples()
    run_postgresql_examples()
    run_faiss_examples()
    print('\n===== ALL DATABASE EXAMPLES COMPLETED =====')

def main():
    """Main function to run all search and request examples"""
    print('===== SEARCH AND REQUEST TOOLS EXAMPLES =====')
    run_search_examples()
    run_arxiv_tool_example()
    run_rss_tool_example()
    run_request_tool_example()
    print('\n===== ALL SEARCH AND REQUEST EXAMPLES COMPLETED =====')

def main():
    """Main function to run all file system examples"""
    print('===== FILE SYSTEM TOOLS EXAMPLES =====')
    run_advanced_file_operations()
    print('\n===== ALL FILE SYSTEM EXAMPLES COMPLETED =====')

def main() -> None:
    """Main function to run condensed converter examples"""
    print('===== API CONVERTER EXAMPLES (CONDENSED) =====')
    rapidapi_test()
    print('\n===== ALL CONDENSED CONVERTER TESTS COMPLETED =====')

def main():
    """Main function to run MCP examples"""
    print('===== MCP TOOL INTEGRATION EXAMPLES =====\n')
    run_mcp_example()
    print('\n===== ALL MCP TOOL EXAMPLES COMPLETED =====')

def main():
    """Main function to run all browser tool examples"""
    print('===== BROWSER TOOL EXAMPLES =====')
    run_browser_tool_example()
    run_browser_use_tool_example()

def run_python_interpreter_examples():
    """Run all examples using the Python InterpreterToolkit"""
    print('\n===== PYTHON INTERPRETER EXAMPLES =====\n')
    interpreter_toolkit = PythonInterpreterToolkit(project_path=os.getcwd(), directory_names=['examples', 'evoagentx'], allowed_imports={'os', 'sys', 'time', 'datetime', 'math', 'random', 'platform', 'matplotlib.pyplot', 'numpy'})
    interpreter = interpreter_toolkit.python_interpreter
    run_simple_hello_world(interpreter)
    run_math_example(interpreter)
    run_platform_info(interpreter)
    run_script_execution(interpreter)
    run_dynamic_code_generation(interpreter)
    run_visualization_example(interpreter)

def run_docker_interpreter_examples():
    """Run all examples using the Docker InterpreterToolkit"""
    print('\n===== DOCKER INTERPRETER EXAMPLES =====\n')
    print('Running Docker interpreter examples...')
    try:
        interpreter_toolkit = DockerInterpreterToolkit(image_tag='python:3.9-slim', print_stdout=True, print_stderr=True, container_directory='/app')
        interpreter = interpreter_toolkit.docker_interpreter
        run_simple_hello_world(interpreter)
        run_math_example(interpreter)
        run_platform_info(interpreter)
        run_script_execution(interpreter)
        run_dynamic_code_generation(interpreter)
    except Exception as e:
        print(f'Error running Docker interpreter examples: {str(e)}')
        print('Make sure Docker is installed and running on your system.')
        print('You may need to pull the python:3.9-slim image first using: docker pull python:3.9-slim')

def main():
    """Main function to run interpreter examples"""
    print('===== CODE INTERPRETER EXAMPLES =====')
    run_python_interpreter_examples()
    run_docker_interpreter_examples()
    print('\n===== ALL INTERPRETER EXAMPLES COMPLETED =====')

def main():
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY, stream=True, output_response=False)
    executor_llm = OpenAILLM(config=openai_config)
    optimizer_config = OpenAILLMConfig(model='gpt-4o', openai_key=OPENAI_API_KEY, stream=True, output_response=False)
    optimizer_llm = OpenAILLM(config=optimizer_config)
    benchmark = MathSplits()
    program = CustomProgram(model=executor_llm)
    registry = MiproRegistry()
    registry.track(program, 'prompt', input_names=['problem'], output_names=['solution'])
    optimizer = MiproOptimizer(registry=registry, program=program, optimizer_llm=optimizer_llm, max_bootstrapped_demos=4, max_labeled_demos=4, num_threads=20, eval_rounds=1, auto='medium', save_path='examples/output/mipro/math_plug_and_play')
    logger.info('Optimizing program...')
    optimizer.optimize(dataset=benchmark)
    optimizer.restore_best_program()
    logger.info('Evaluating program on test set...')
    with suppress_logger_info():
        results = optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (after optimization): {results}')

def main():
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY, stream=True, output_response=False)
    executor_llm = OpenAILLM(config=openai_config)
    optimizer_config = OpenAILLMConfig(model='gpt-4o', openai_key=OPENAI_API_KEY, stream=True, output_response=False)
    optimizer_llm = OpenAILLM(config=optimizer_config)
    benchmark = MathSplits()
    workflow_graph: SequentialWorkFlowGraph = SequentialWorkFlowGraph.from_dict(math_graph_data)
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)
    evaluator = Evaluator(llm=executor_llm, agent_manager=agent_manager, collate_func=collate_func, num_workers=20, verbose=True)
    optimizer = WorkFlowMiproOptimizer(graph=workflow_graph, evaluator=evaluator, optimizer_llm=optimizer_llm, max_bootstrapped_demos=4, max_labeled_demos=4, eval_rounds=1, auto='medium', save_path='examples/output/mipro/math_mipro')
    logger.info('Optimizing workflow...')
    optimizer.optimize(dataset=benchmark)
    from pdb import set_trace
    set_trace()
    optimizer.restore_best_program()
    logger.info('Evaluating program on test set...')
    with suppress_logger_info():
        results = optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (after optimization): {results}')

def main():
    executor_config = OpenAILLMConfig(model='gpt-4o-mini')
    executor_llm = OpenAILLM(config=executor_config)
    optimizer_config = OpenAILLMConfig(model='gpt-4o')
    optimizer_llm = OpenAILLM(config=optimizer_config)
    benchmark = MBPPSplits()
    workflow_graph = SequentialWorkFlowGraph.from_dict(mbpp_graph_data)
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, executor_llm.config)
    evaluator = Evaluator(llm=executor_llm, agent_manager=agent_manager, collate_func=collate_func, num_workers=20, verbose=True)
    textgrad_optimizer = TextGradOptimizer(graph=workflow_graph, optimize_mode='system_prompt', executor_llm=executor_llm, optimizer_llm=optimizer_llm, batch_size=3, max_steps=20, evaluator=evaluator, eval_every_n_steps=1, eval_rounds=1, save_interval=None, save_path='./', rollback=True, constraints=[])
    logger.info('Evaluating workflow on test set...')
    with suppress_logger_info():
        results = textgrad_optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info('Evaluation metrics (before optimization): ', results)
    logger.info('Optimizing workflow...')
    textgrad_optimizer.optimize(benchmark, seed=8)
    textgrad_optimizer.restore_best_graph()
    logger.info('Evaluating workflow on test set...')
    with suppress_logger_info():
        results = textgrad_optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (after optimization): {results}')

def main():
    executor_config = OpenAILLMConfig(model='gpt-4o-mini')
    executor_llm = OpenAILLM(config=executor_config)
    optimizer_config = OpenAILLMConfig(model='gpt-4o')
    optimizer_llm = OpenAILLM(config=optimizer_config)
    benchmark = MathSplits()
    workflow_graph = SequentialWorkFlowGraph.from_dict(math_graph_data)
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, executor_llm.config)
    evaluator = Evaluator(llm=executor_llm, agent_manager=agent_manager, collate_func=collate_func, num_workers=20, verbose=True)
    textgrad_optimizer = TextGradOptimizer(graph=workflow_graph, optimize_mode='all', executor_llm=executor_llm, optimizer_llm=optimizer_llm, batch_size=3, max_steps=20, evaluator=evaluator, eval_every_n_steps=1, eval_rounds=1, save_interval=None, save_path='./', rollback=True, constraints=[])
    logger.info('Evaluating workflow on test set...')
    with suppress_logger_info():
        results = textgrad_optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (before optimization): {results}')
    logger.info('Optimizing workflow...')
    textgrad_optimizer.optimize(benchmark, seed=8)
    textgrad_optimizer.restore_best_graph()
    logger.info('Evaluating workflow on test set...')
    with suppress_logger_info():
        results = textgrad_optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (after optimization): {results}')

def main():
    executor_config = OpenAILLMConfig(model='gpt-4o-mini')
    executor_llm = OpenAILLM(config=executor_config)
    optimizer_config = OpenAILLMConfig(model='gpt-4o')
    optimizer_llm = OpenAILLM(config=optimizer_config)
    benchmark = HotPotQASplits()
    workflow_graph = SequentialWorkFlowGraph.from_dict(hotpotqa_graph_data)
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, executor_llm.config)
    evaluator = Evaluator(llm=executor_llm, agent_manager=agent_manager, collate_func=collate_func, num_workers=20, verbose=True)
    textgrad_optimizer = TextGradOptimizer(graph=workflow_graph, optimize_mode='all', executor_llm=executor_llm, optimizer_llm=optimizer_llm, batch_size=3, max_steps=20, evaluator=evaluator, eval_every_n_steps=1, eval_rounds=1, save_interval=None, save_path='./', rollback=True, constraints=[])
    logger.info('Evaluating workflow on test set...')
    with suppress_logger_info():
        results = textgrad_optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (before optimization): {results}')
    logger.info('Optimizing workflow...')
    textgrad_optimizer.optimize(benchmark, seed=8)
    textgrad_optimizer.restore_best_graph()
    logger.info('Evaluating workflow on test set...')
    with suppress_logger_info():
        results = textgrad_optimizer.evaluate(dataset=benchmark, eval_mode='test')
    logger.info(f'Evaluation metrics (after optimization): {results}')

def main():
    claude_config = LiteLLMConfig(model='anthropic/claude-3-5-sonnet-20240620', anthropic_key=ANTHROPIC_API_KEY)
    optimizer_llm = LiteLLM(config=claude_config)
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
    executor_llm = OpenAILLM(config=openai_config)
    hotpotqa = HotPotQASplits()
    optimizer = AFlowOptimizer(graph_path='examples/aflow/hotpotqa', optimized_path='examples/aflow/hotpotqa/optimized', optimizer_llm=optimizer_llm, executor_llm=executor_llm, validation_rounds=3, eval_rounds=3, max_rounds=20, **EXPERIMENTAL_CONFIG['hotpotqa'])
    optimizer.optimize(hotpotqa)
    optimizer.test(hotpotqa)

def main():
    claude_config = LiteLLMConfig(model='anthropic/claude-3-5-sonnet-20240620', anthropic_key=ANTHROPIC_API_KEY)
    optimizer_llm = LiteLLM(config=claude_config)
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
    executor_llm = OpenAILLM(config=openai_config)
    mbpp = MBPPSplits()
    optimizer = AFlowOptimizer(graph_path='examples/aflow/code_generation', optimized_path='examples/aflow/mbpp/optimized', optimizer_llm=optimizer_llm, executor_llm=executor_llm, validation_rounds=3, eval_rounds=3, max_rounds=20, **EXPERIMENTAL_CONFIG['mbpp'])
    optimizer.optimize(mbpp)
    optimizer.test(mbpp)

def main():
    claude_config = LiteLLMConfig(model='anthropic/claude-3-5-sonnet-20240620', anthropic_key=ANTHROPIC_API_KEY)
    optimizer_llm = LiteLLM(config=claude_config)
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
    executor_llm = OpenAILLM(config=openai_config)
    humaneval = AFlowHumanEval()
    optimizer = AFlowOptimizer(graph_path='examples/aflow/code_generation', optimized_path='examples/aflow/humaneval/optimized', optimizer_llm=optimizer_llm, executor_llm=executor_llm, validation_rounds=5, eval_rounds=3, max_rounds=20, **EXPERIMENTAL_CONFIG['humaneval'])
    optimizer.optimize(humaneval)
    optimizer.test(humaneval)

def main():
    claude_config = LiteLLMConfig(model='anthropic/claude-3-5-sonnet-20240620', anthropic_key=ANTHROPIC_API_KEY)
    optimizer_llm = LiteLLM(config=claude_config)
    openai_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
    executor_llm = OpenAILLM(config=openai_config)
    math = MathSplits()
    optimizer = AFlowOptimizer(graph_path='examples/aflow/math', optimized_path='examples/aflow/math/optimized', optimizer_llm=optimizer_llm, executor_llm=executor_llm, validation_rounds=3, eval_rounds=3, max_rounds=20, **EXPERIMENTAL_CONFIG['math'])
    optimizer.optimize(math)
    optimizer.test(math)

def configure_llm() -> LiteLLM:
    """1. LLM Configuration - Using LiteLLM with Azure OpenAI"""
    cfg = LiteLLMConfig(model='azure/' + os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'), azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'), azure_key=os.getenv('AZURE_OPENAI_KEY'), api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview'), stream=True, output_response=True, max_tokens=16000, temperature=0.7)
    return LiteLLM(config=cfg)

def generate_plan(llm: LiteLLM, goal: str, output_dir: str):
    """2.1 Generate task planning"""
    wait_for_user_confirmation('task planning generation')
    print('Starting task planning generation...')
    wf = WorkFlowGenerator(llm=llm)
    plan = wf.generate_plan(goal=goal)
    save_intermediate_result(plan, 'plan', output_dir)
    print(f'Task planning completed, containing {len(plan.sub_tasks)} sub-tasks')
    return plan

def build_workflow_from_plan(llm: LiteLLM, goal: str, plan, output_dir: str):
    """2.2 Build workflow from plan"""
    wait_for_user_confirmation('workflow graph construction')
    print('Starting workflow graph construction...')
    wf = WorkFlowGenerator(llm=llm)
    workflow = wf.build_workflow_from_plan(goal=goal, plan=plan)
    save_intermediate_result(workflow, 'workflow_structure', output_dir)
    print(f'Workflow graph construction completed, containing {len(workflow.nodes)} nodes and {len(workflow.edges)} edges')
    return workflow

def generate_agents_for_workflow(llm: LiteLLM, goal: str, workflow: WorkFlowGraph, output_dir: str):
    """2.3 Generate agents for workflow"""
    wait_for_user_confirmation('agent generation for workflow')
    print('Starting agent generation for workflow...')
    wf = WorkFlowGenerator(llm=llm)
    workflow_with_agents = wf.generate_agents(goal=goal, workflow=workflow)
    save_intermediate_result(workflow_with_agents, 'workflow_with_agents', output_dir)
    print('Agent generation completed')
    return workflow_with_agents

def generate_workflow_step_by_step(llm: LiteLLM, goal: str, output_dir: str) -> WorkFlowGraph:
    """2. Generate and display workflow step by step"""
    print(f'Starting step-by-step workflow generation, goal: {goal}')
    print(f'Intermediate results will be saved to: {output_dir}')
    plan = generate_plan(llm, goal, output_dir)
    workflow = build_workflow_from_plan(llm, goal, plan, output_dir)
    workflow_with_agents = generate_agents_for_workflow(llm, goal, workflow, output_dir)
    workflow_with_agents.display()
    save_intermediate_result(workflow_with_agents, 'final_workflow', output_dir)
    print('Workflow generation completed!')
    return workflow_with_agents

def execute_workflow(llm: LiteLLM, graph: WorkFlowGraph, goal: str, target_dir: str):
    """3. Register Agents and execute workflow"""
    wait_for_user_confirmation('workflow execution')
    print('Starting workflow execution...')
    cfg = llm.config
    mgr = AgentManager()
    mgr.add_agents_from_workflow(graph, llm_config=cfg)
    workflow = WorkFlow(graph=graph, agent_manager=mgr, llm=llm)
    output = workflow.execute()
    print('Workflow execution completed')
    return output

def main():
    goal = 'Generate html code for the Tetris game that can be played in the browser.'
    target_dir = 'examples/output/tetris_game'
    output_dir = 'examples/output/workflow_intermediates'
    wait_for_user_confirmation('LLM configuration')
    llm = configure_llm()
    graph = generate_workflow_step_by_step(llm, goal, output_dir)
    output = execute_workflow(llm, graph, goal, target_dir)
    verify_and_extract_code(llm, goal, output, target_dir)
    print(f'\nComplete Tetris game has been generated to directory: {target_dir}')

def build_customize_agent():
    agent_data = {'name': 'FirstAgent', 'description': 'A simple agent that prints hello world', 'prompt': "Print 'hello world'", 'llm_config': openrouter_config}
    agent = CustomizeAgent.from_dict(agent_data)
    message: Message = agent()
    print(f'Response from {agent.name}:')
    print(message.content.content)

def build_customize_agent_with_inputs():
    simple_agent = CustomizeAgent(name='SimpleAgent', description='A basic agent that responds to queries', prompt='Answer the following question: {question}', llm_config=openrouter_config, inputs=[{'name': 'question', 'type': 'string', 'description': 'The question to answer'}])
    response = simple_agent(inputs={'question': 'What is a language model?'})
    print(f'Response from {simple_agent.name}:')
    print(response.content.content)

def build_customize_agent_with_inputs_and_outputs():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=openrouter_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code'}], parse_mode='str')
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers'})
    print(f'Response from {code_writer.name}:')
    print(message.content.code)

def build_customize_agent_with_custom_parse_func():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=openrouter_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code'}], parse_mode='custom', parse_func=lambda content: {'code': extract_code_blocks(content)[0]})
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers'})
    print(f'Response from {code_writer.name}:')
    print(message.content.code)

def build_customize_agent_with_prompt_template():
    agent = CustomizeAgent(name='FirstAgent', description='A simple agent that prints hello world', prompt_template=StringTemplate(instruction="Print 'hello world'"), llm_config=openrouter_config)
    message = agent()
    print(f'Response from {agent.name}:')
    print(message.content.content)

def build_customize_agent_with_inputs_and_outputs_and_prompt_template():
    code_writer = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt_template=StringTemplate(instruction='Write Python code that implements the provided `requirement`'), llm_config=openrouter_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement'}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code'}], parse_mode='custom', parse_func=lambda content: {'code': extract_code_blocks(content)[0]})
    message = code_writer(inputs={'requirement': 'Write a function that returns the sum of two numbers'})
    print(f'Response from {code_writer.name}:')
    print(message.content.code)

class TestModule(unittest.TestCase):

    def setUp(self):
        self.save_file = 'tests/agents/saved_agent.json'

    def test_initialization(self):
        agent_data = {'name': 'test_agent', 'description': 'test_agent_description', 'llm_config': {'class_name': 'LiteLLMConfig', 'model': 'gpt-4o-mini', 'openai_key': 'xxxxx'}, 'actions': [{'class_name': 'Action', 'name': 'test_action_name', 'description': 'test_action_desc', 'prompt': 'test_action_prompt'}]}
        agent = Agent.from_dict(agent_data)
        self.assertEqual(agent.llm_config.model, 'gpt-4o-mini')
        self.assertTrue(isinstance(agent.llm, LiteLLM))
        self.assertTrue(isinstance(agent.actions[0], Action))
        self.assertTrue(len(agent.get_all_actions()) == 1)
        action = agent.get_action('test_action_name')
        self.assertEqual(action.name, 'test_action_name')
        self.assertEqual(action.description, 'test_action_desc')
        prompts = agent.get_prompts()
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts['test_action_name']['system_prompt'], None)
        self.assertEqual(prompts['test_action_name']['prompt'], 'test_action_prompt')
        agent.set_prompt('test_action_name', 'new_test_action_prompt', 'new_system_prompt')
        self.assertTrue(agent.system_prompt, 'new_system_prompt')
        self.assertEqual(agent.get_action('test_action_name').prompt, 'new_test_action_prompt')
        agent.set_prompts({'test_action_name': {'system_prompt': 'new_system_prompt_v2', 'prompt': 'new_test_action_prompt_v2'}})
        self.assertTrue(agent.system_prompt, 'new_system_prompt_v2')
        self.assertEqual(agent.get_action('test_action_name').prompt, 'new_test_action_prompt_v2')
        agent2 = Agent.from_dict(agent_data)
        agent_list = [agent]
        self.assertTrue(agent2 not in agent_list)
        self.assertTrue(agent2 != agent)
        agent2_id = agent2.agent_id
        agent2.agent_id = agent.agent_id
        self.assertTrue(agent2 in agent_list)
        self.assertTrue(agent2 == agent)
        agent2.agent_id = agent2_id

    def test_save_agent(self):
        llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key='xxxxx')
        agent = Agent(name='Bob', description='Bob is an engineer. He excels in writing and reviewing codes for different projects.', system_prompt='You are an excellent engineer and you can solve diverse coding tasks.', llm_config=llm_config, actions=[{'name': 'WriteFileToDisk', 'description': 'save several files to local storage.', 'tools': [{'name': 'FileToolKit', 'tools': [{'name': 'WriteFile', 'description': 'Write file to disk', 'inputs': {}}]}]}])
        agent.save_module(path=self.save_file)
        loaded_agent = Agent.from_file(path=self.save_file, llm_config=llm_config)
        self.assertEqual(agent, loaded_agent)

    def tearDown(self):
        if os.path.exists(self.save_file):
            os.remove(self.save_file)

def test_save_agent(self):
    llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key='xxxxx')
    agent = Agent(name='Bob', description='Bob is an engineer. He excels in writing and reviewing codes for different projects.', system_prompt='You are an excellent engineer and you can solve diverse coding tasks.', llm_config=llm_config, actions=[{'name': 'WriteFileToDisk', 'description': 'save several files to local storage.', 'tools': [{'name': 'FileToolKit', 'tools': [{'name': 'WriteFile', 'description': 'Write file to disk', 'inputs': {}}]}]}])
    agent.save_module(path=self.save_file)
    loaded_agent = Agent.from_file(path=self.save_file, llm_config=llm_config)
    self.assertEqual(agent, loaded_agent)

@register_parse_function
def customize_parse_func(content: str) -> dict:
    return {'code': extract_code_blocks(content)[0]}

class TestModule(unittest.TestCase):

    def setUp(self):
        self.save_files = ['tests/agents/saved_customize_agent.json', 'tests/agents/saved_customize_agent_with_inputs.json', 'tests/agents/saved_customize_agent_with_outputs.json', 'tests/agents/saved_customize_agent_with_inputs_outputs.json', 'tests/agents/saved_customize_agent_with_parser.json']

    @patch('evoagentx.models.litellm_model.LiteLLM.single_generate')
    def test_simple_agent(self, mock_generate):
        mock_generate.return_value = 'Hello, world!'
        llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key='xxxxx')
        simple_agent = CustomizeAgent(name='Simple Agent', description='A simple agent that prints hello world', prompt='You are a simple agent that prints hello world.', llm_config=llm_config)
        self.assertEqual(simple_agent.name, 'Simple Agent')
        self.assertEqual(simple_agent.prompt, 'You are a simple agent that prints hello world.')
        self.assertEqual(simple_agent.customize_action_name, 'SimpleAgentAction')
        self.assertEqual(simple_agent.get_prompts()['SimpleAgentAction']['prompt'], 'You are a simple agent that prints hello world.')
        self.assertEqual(len(simple_agent.action.inputs_format.get_attrs()), 0)
        self.assertEqual(len(simple_agent.action.outputs_format.get_attrs()), 0)
        simple_agent.save_module(self.save_files[0])
        new_agent: CustomizeAgent = CustomizeAgent.from_file(self.save_files[0], llm_config=llm_config)
        self.assertEqual(new_agent.name, 'Simple Agent')
        self.assertEqual(len(new_agent.action.inputs_format.get_attrs()), 0)
        self.assertEqual(len(new_agent.action.outputs_format.get_attrs()), 0)
        msg = new_agent()
        self.assertTrue(isinstance(msg, Message))
        self.assertEqual(msg.msg_type, MessageType.UNKNOWN)
        self.assertEqual(msg.content.content, 'Hello, world!')

    @patch('evoagentx.models.litellm_model.LiteLLM.single_generate')
    def test_agent_with_inputs_and_outputs(self, mock_generate):
        mock_generate.return_value = "```python\nprint('Hello, world!')```"
        llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key='xxxxx')
        agent_with_inputs = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=llm_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement', 'required': True}])
        self.assertEqual(len(agent_with_inputs.action.inputs_format.get_attrs()), 1)
        self.assertEqual(len(agent_with_inputs.action.outputs_format.get_attrs()), 0)
        agent_with_inputs.save_module(self.save_files[1])
        new_agent_with_inputs: CustomizeAgent = CustomizeAgent.from_file(self.save_files[1], llm_config=llm_config)
        self.assertEqual(len(new_agent_with_inputs.action.inputs_format.get_attrs()), 1)
        self.assertEqual(len(new_agent_with_inputs.action.outputs_format.get_attrs()), 0)
        msg = new_agent_with_inputs(inputs={'requirement': 'Write Python code that prints hello world'}, return_msg_type=MessageType.RESPONSE)
        self.assertEqual(msg.msg_type, MessageType.RESPONSE)
        self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
        agent_with_outputs = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: Write Python code that prints hello world', llm_config=llm_config, outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code', 'required': True}], parse_mode='custom', parse_func=customize_parse_func, title_format='## {title}')
        self.assertEqual(len(agent_with_outputs.action.inputs_format.get_attrs()), 0)
        self.assertEqual(len(agent_with_outputs.action.outputs_format.get_attrs()), 1)
        agent_with_outputs.save_module(self.save_files[2])
        new_agent_with_outputs: CustomizeAgent = CustomizeAgent.from_file(self.save_files[2], llm_config=llm_config)
        self.assertEqual(len(new_agent_with_outputs.action.inputs_format.get_attrs()), 0)
        self.assertEqual(len(new_agent_with_outputs.action.outputs_format.get_attrs()), 1)
        self.assertEqual(new_agent_with_outputs.parse_func.__name__, 'customize_parse_func')
        msg = new_agent_with_outputs(return_msg_type=MessageType.RESPONSE)
        self.assertEqual(msg.msg_type, MessageType.RESPONSE)
        self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
        self.assertEqual(msg.content.code, "print('Hello, world!')")
        agent_with_inputs_outputs = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=llm_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement', 'required': True}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code', 'required': True}], parse_mode='custom', parse_func=customize_parse_func)
        self.assertEqual(len(agent_with_inputs_outputs.action.inputs_format.get_attrs()), 1)
        self.assertEqual(len(agent_with_inputs_outputs.action.outputs_format.get_attrs()), 1)
        agent_with_inputs_outputs.save_module(self.save_files[3])
        new_agent_with_inputs_outputs: CustomizeAgent = CustomizeAgent.from_file(self.save_files[3], llm_config=llm_config)
        self.assertEqual(len(new_agent_with_inputs_outputs.action.inputs_format.get_attrs()), 1)
        self.assertEqual(len(new_agent_with_inputs_outputs.action.outputs_format.get_attrs()), 1)
        msg = new_agent_with_inputs_outputs(inputs={'requirement': 'Write Python code that prints hello world'}, return_msg_type=MessageType.RESPONSE)
        self.assertEqual(msg.msg_type, MessageType.RESPONSE)
        self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
        self.assertEqual(msg.content.code, "print('Hello, world!')")
        agent_with_parser = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=llm_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement', 'required': True}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code', 'required': True}, {'name': 'explanation', 'type': 'string', 'description': 'The explanation of the generated Python code', 'required': True}], output_parser=CodeWriterActionOutput, parse_mode='custom', parse_func=customize_parse_func)
        self.assertEqual(agent_with_parser.action.outputs_format.__name__, 'CodeWriterActionOutput')
        agent_with_parser.save_module(self.save_files[4])
        new_agent_with_parser: CustomizeAgent = CustomizeAgent.from_file(self.save_files[4], llm_config=llm_config)
        self.assertEqual(new_agent_with_parser.action.outputs_format.__name__, 'CodeWriterActionOutput')
        msg = new_agent_with_parser(inputs={'requirement': 'Write Python code that prints hello world'}, return_msg_type=MessageType.RESPONSE)
        self.assertEqual(msg.msg_type, MessageType.RESPONSE)
        self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
        self.assertEqual(msg.content.code, "print('Hello, world!')")

    def tearDown(self):
        for file in self.save_files:
            if os.path.exists(file):
                os.remove(file)

@patch('evoagentx.models.litellm_model.LiteLLM.single_generate')
def test_agent_with_inputs_and_outputs(self, mock_generate):
    mock_generate.return_value = "```python\nprint('Hello, world!')```"
    llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key='xxxxx')
    agent_with_inputs = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=llm_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement', 'required': True}])
    self.assertEqual(len(agent_with_inputs.action.inputs_format.get_attrs()), 1)
    self.assertEqual(len(agent_with_inputs.action.outputs_format.get_attrs()), 0)
    agent_with_inputs.save_module(self.save_files[1])
    new_agent_with_inputs: CustomizeAgent = CustomizeAgent.from_file(self.save_files[1], llm_config=llm_config)
    self.assertEqual(len(new_agent_with_inputs.action.inputs_format.get_attrs()), 1)
    self.assertEqual(len(new_agent_with_inputs.action.outputs_format.get_attrs()), 0)
    msg = new_agent_with_inputs(inputs={'requirement': 'Write Python code that prints hello world'}, return_msg_type=MessageType.RESPONSE)
    self.assertEqual(msg.msg_type, MessageType.RESPONSE)
    self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
    agent_with_outputs = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: Write Python code that prints hello world', llm_config=llm_config, outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code', 'required': True}], parse_mode='custom', parse_func=customize_parse_func, title_format='## {title}')
    self.assertEqual(len(agent_with_outputs.action.inputs_format.get_attrs()), 0)
    self.assertEqual(len(agent_with_outputs.action.outputs_format.get_attrs()), 1)
    agent_with_outputs.save_module(self.save_files[2])
    new_agent_with_outputs: CustomizeAgent = CustomizeAgent.from_file(self.save_files[2], llm_config=llm_config)
    self.assertEqual(len(new_agent_with_outputs.action.inputs_format.get_attrs()), 0)
    self.assertEqual(len(new_agent_with_outputs.action.outputs_format.get_attrs()), 1)
    self.assertEqual(new_agent_with_outputs.parse_func.__name__, 'customize_parse_func')
    msg = new_agent_with_outputs(return_msg_type=MessageType.RESPONSE)
    self.assertEqual(msg.msg_type, MessageType.RESPONSE)
    self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
    self.assertEqual(msg.content.code, "print('Hello, world!')")
    agent_with_inputs_outputs = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=llm_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement', 'required': True}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code', 'required': True}], parse_mode='custom', parse_func=customize_parse_func)
    self.assertEqual(len(agent_with_inputs_outputs.action.inputs_format.get_attrs()), 1)
    self.assertEqual(len(agent_with_inputs_outputs.action.outputs_format.get_attrs()), 1)
    agent_with_inputs_outputs.save_module(self.save_files[3])
    new_agent_with_inputs_outputs: CustomizeAgent = CustomizeAgent.from_file(self.save_files[3], llm_config=llm_config)
    self.assertEqual(len(new_agent_with_inputs_outputs.action.inputs_format.get_attrs()), 1)
    self.assertEqual(len(new_agent_with_inputs_outputs.action.outputs_format.get_attrs()), 1)
    msg = new_agent_with_inputs_outputs(inputs={'requirement': 'Write Python code that prints hello world'}, return_msg_type=MessageType.RESPONSE)
    self.assertEqual(msg.msg_type, MessageType.RESPONSE)
    self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
    self.assertEqual(msg.content.code, "print('Hello, world!')")
    agent_with_parser = CustomizeAgent(name='CodeWriter', description='Writes Python code based on requirements', prompt='Write Python code that implements the following requirement: {requirement}', llm_config=llm_config, inputs=[{'name': 'requirement', 'type': 'string', 'description': 'The coding requirement', 'required': True}], outputs=[{'name': 'code', 'type': 'string', 'description': 'The generated Python code', 'required': True}, {'name': 'explanation', 'type': 'string', 'description': 'The explanation of the generated Python code', 'required': True}], output_parser=CodeWriterActionOutput, parse_mode='custom', parse_func=customize_parse_func)
    self.assertEqual(agent_with_parser.action.outputs_format.__name__, 'CodeWriterActionOutput')
    agent_with_parser.save_module(self.save_files[4])
    new_agent_with_parser: CustomizeAgent = CustomizeAgent.from_file(self.save_files[4], llm_config=llm_config)
    self.assertEqual(new_agent_with_parser.action.outputs_format.__name__, 'CodeWriterActionOutput')
    msg = new_agent_with_parser(inputs={'requirement': 'Write Python code that prints hello world'}, return_msg_type=MessageType.RESPONSE)
    self.assertEqual(msg.msg_type, MessageType.RESPONSE)
    self.assertEqual(msg.content.content, "```python\nprint('Hello, world!')```")
    self.assertEqual(msg.content.code, "print('Hello, world!')")

class TestModule(unittest.TestCase):

    def setUp(self):
        self.llm_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key='XXX')
        self.sample_tasks = [{'name': 'Task1', 'description': 'First task in the sequence', 'inputs': [{'name': 'input1', 'type': 'string', 'required': True, 'description': 'Input for Task1'}], 'outputs': [{'name': 'output1', 'type': 'string', 'required': True, 'description': 'Output from Task1'}], 'prompt': 'Execute Task1'}, {'name': 'Task2', 'description': 'Second task in the sequence', 'inputs': [{'name': 'output1', 'type': 'string', 'required': True, 'description': 'Input from Task1'}], 'outputs': [{'name': 'output2', 'type': 'string', 'required': True, 'description': 'Output from Task2'}], 'prompt': 'Execute Task2'}, {'name': 'Task3', 'description': 'Third task in the sequence', 'inputs': [{'name': 'output2', 'type': 'string', 'required': True, 'description': 'Input from Task2'}], 'outputs': [{'name': 'final_output', 'type': 'string', 'required': True, 'description': 'Final output'}], 'prompt': 'Execute Task3', 'parse_mode': 'custom', 'parse_func': custom_parse_func}]

    def tearDown(self):
        if os.path.exists('tests/workflow/test_workflow.json'):
            os.remove('tests/workflow/test_workflow.json')

    def test_sequential_workflow_graph_creation(self):
        """Test that a sequential workflow graph is created correctly."""
        graph = SequentialWorkFlowGraph(goal='Test Workflow', tasks=self.sample_tasks)
        self.assertEqual('Test Workflow', graph.goal)
        self.assertEqual(3, len(graph.nodes))
        self.assertEqual(2, len(graph.edges))
        node_names = [node.name for node in graph.nodes]
        self.assertListEqual(['Task1', 'Task2', 'Task3'], node_names)
        edge_connections = [(edge.source, edge.target) for edge in graph.edges]
        self.assertIn(('Task1', 'Task2'), edge_connections)
        self.assertIn(('Task2', 'Task3'), edge_connections)

    def test_sequential_workflow_node_properties(self):
        """Test that nodes in the workflow have correct properties."""
        graph = SequentialWorkFlowGraph(goal='Test Workflow', tasks=self.sample_tasks)
        node1 = graph.get_node('Task1')
        self.assertEqual('Task1', node1.name)
        self.assertEqual('First task in the sequence', node1.description)
        self.assertEqual(1, len(node1.inputs))
        self.assertEqual(1, len(node1.outputs))
        self.assertEqual('input1', node1.inputs[0].name)
        self.assertEqual('output1', node1.outputs[0].name)
        self.assertTrue(len(node1.agents) > 0)
        agent = node1.agents[0]
        self.assertEqual('Execute Task1', agent.get('prompt'))
        node3 = graph.get_node('Task3')
        self.assertEqual('custom', node3.agents[0]['parse_mode'])
        self.assertEqual(custom_parse_func, node3.agents[0]['parse_func'])

    def test_sequential_workflow_execution_flow(self):
        """Test the execution flow of a sequential workflow."""
        graph = SequentialWorkFlowGraph(goal='Test Workflow', tasks=self.sample_tasks)
        for node in graph.nodes:
            self.assertEqual(WorkFlowNodeState.PENDING, node.status)
        next_nodes = graph.next()
        self.assertEqual(1, len(next_nodes))
        self.assertEqual('Task1', next_nodes[0].name)
        graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        next_nodes = graph.next()
        self.assertEqual(1, len(next_nodes))
        self.assertEqual('Task2', next_nodes[0].name)
        graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
        next_nodes = graph.next()
        self.assertEqual(1, len(next_nodes))
        self.assertEqual('Task3', next_nodes[0].name)
        graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
        self.assertTrue(graph.is_complete)
        next_nodes = graph.next()
        self.assertEqual(0, len(next_nodes))

    def test_sequential_workflow_save_and_load(self):
        """Test saving and loading a sequential workflow."""
        graph = SequentialWorkFlowGraph(goal='Test Workflow', tasks=self.sample_tasks)
        save_path = 'tests/workflow/test_workflow.json'
        graph.save_module(save_path)
        self.assertTrue(os.path.exists(save_path))
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual('SequentialWorkFlowGraph', saved_data['class_name'])
        self.assertEqual('Test Workflow', saved_data['goal'])
        self.assertEqual(3, len(saved_data['tasks']))
        self.assertEqual('custom_parse_func', saved_data['tasks'][2]['parse_func'])
        task_names = [task['name'] for task in saved_data['tasks']]
        self.assertListEqual(['Task1', 'Task2', 'Task3'], task_names)
        loaded_graph: SequentialWorkFlowGraph = SequentialWorkFlowGraph.from_file(save_path)
        self.assertEqual('Test Workflow', loaded_graph.goal)
        self.assertEqual(3, len(loaded_graph.nodes))
        self.assertEqual('custom_parse_func', loaded_graph.get_node('Task3').agents[0]['parse_func'])

    def test_node_status_management(self):
        """Test that node status can be properly managed."""
        graph = SequentialWorkFlowGraph(goal='Test Workflow', tasks=self.sample_tasks)
        self.assertEqual(WorkFlowNodeState.PENDING, graph.get_node_status('Task1'))
        graph.set_node_status('Task1', WorkFlowNodeState.RUNNING)
        self.assertEqual(WorkFlowNodeState.RUNNING, graph.get_node_status('Task1'))
        self.assertTrue(graph.running('Task1'))
        graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        self.assertEqual(WorkFlowNodeState.COMPLETED, graph.get_node_status('Task1'))
        self.assertTrue(graph.completed('Task1'))
        graph.set_node_status('Task2', WorkFlowNodeState.FAILED)
        self.assertEqual(WorkFlowNodeState.FAILED, graph.get_node_status('Task2'))
        self.assertTrue(graph.failed('Task2'))

    def test_graph_reset(self):
        """Test that the graph can be reset to initial state."""
        graph = SequentialWorkFlowGraph(goal='Test Workflow', tasks=self.sample_tasks)
        for node in graph.nodes:
            graph.set_node_status(node.name, WorkFlowNodeState.COMPLETED)
        for node in graph.nodes:
            self.assertEqual(WorkFlowNodeState.COMPLETED, node.status)
        graph.reset_graph()
        for node in graph.nodes:
            self.assertEqual(WorkFlowNodeState.PENDING, node.status)

def setUp(self):
    self.llm_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key='XXX')
    self.sample_tasks = [{'name': 'Task1', 'description': 'First task in the sequence', 'inputs': [{'name': 'input1', 'type': 'string', 'required': True, 'description': 'Input for Task1'}], 'outputs': [{'name': 'output1', 'type': 'string', 'required': True, 'description': 'Output from Task1'}], 'prompt': 'Execute Task1'}, {'name': 'Task2', 'description': 'Second task in the sequence', 'inputs': [{'name': 'output1', 'type': 'string', 'required': True, 'description': 'Input from Task1'}], 'outputs': [{'name': 'output2', 'type': 'string', 'required': True, 'description': 'Output from Task2'}], 'prompt': 'Execute Task2'}, {'name': 'Task3', 'description': 'Third task in the sequence', 'inputs': [{'name': 'output2', 'type': 'string', 'required': True, 'description': 'Input from Task2'}], 'outputs': [{'name': 'final_output', 'type': 'string', 'required': True, 'description': 'Final output'}], 'prompt': 'Execute Task3', 'parse_mode': 'custom', 'parse_func': custom_parse_func}]

class TestModule(unittest.TestCase):

    def setUp(self):
        self.llm_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key='XXX')
        self.qa_action_graph = QAActionGraph(llm_config=self.llm_config, name='QAActionGraph', description='This workflow aims to address multi-hop QA tasks.')

    @patch('evoagentx.workflow.operators.AnswerGenerate.execute')
    @patch('evoagentx.workflow.operators.QAScEnsemble.execute')
    def test_execute(self, mock_sc_ensemble, mock_answer_generate):
        """Test execute method with mocked operators"""
        mock_answer_generate.return_value = {'answer': 'This is a mocked answer'}
        mock_sc_ensemble.return_value = {'response': 'final answer'}
        result = self.qa_action_graph.execute(problem='This is a test problem.')
        self.assertTrue(mock_answer_generate.called)
        self.assertTrue(mock_sc_ensemble.called)
        self.assertEqual(result['answer'], 'final answer')

    @pytest.mark.asyncio
    @patch('evoagentx.workflow.operators.AnswerGenerate.async_execute')
    @patch('evoagentx.workflow.operators.QAScEnsemble.async_execute')
    async def test_async_execute(self, mock_sc_ensemble, mock_answer_generate):
        """Test async_execute method with mocked async operators"""
        mock_answer_generate.return_value = {'answer': 'This is a mocked async answer'}
        mock_sc_ensemble.return_value = {'response': 'final async answer'}
        result = await self.qa_action_graph.async_execute(problem='This is a test async problem.')
        self.assertTrue(mock_answer_generate.called)
        self.assertTrue(mock_sc_ensemble.called)
        self.assertEqual(result['answer'], 'final async answer')

    def test_get_graph_info(self):
        graph_info = self.qa_action_graph.get_graph_info()
        self.assertEqual(graph_info['name'], 'QAActionGraph')
        self.assertEqual(graph_info['description'], 'This workflow aims to address multi-hop QA tasks.')
        self.assertEqual(len(graph_info['operators']), 2)
        self.assertEqual(graph_info['operators']['answer_generate']['name'], 'AnswerGenerate')
        self.assertEqual(graph_info['operators']['sc_ensemble']['name'], 'QAScEnsemble')

    def test_from_dict(self):
        graph_info = self.qa_action_graph.get_graph_info()
        graph_info['operators']['answer_generate']['prompt'] = 'This is a mocked prompt'
        graph_info['llm_config'] = self.llm_config.to_dict()
        loaded_graph = ActionGraph.from_dict(graph_info)
        self.assertEqual(loaded_graph.name, 'QAActionGraph')
        self.assertEqual(loaded_graph.description, 'This workflow aims to address multi-hop QA tasks.')
        self.assertEqual(loaded_graph.answer_generate.name, 'AnswerGenerate')
        self.assertEqual(loaded_graph.answer_generate.prompt, 'This is a mocked prompt')
        self.assertEqual(loaded_graph.sc_ensemble.name, 'QAScEnsemble')

    def test_save_and_load(self):
        self.qa_action_graph.save_module('tests/src/workflow/saved_qa_action_graph.json')
        loaded_graph = ActionGraph.from_file('tests/src/workflow/saved_qa_action_graph.json', llm_config=self.llm_config)
        self.assertEqual(loaded_graph.name, 'QAActionGraph')
        self.assertEqual(loaded_graph.description, 'This workflow aims to address multi-hop QA tasks.')
        self.assertEqual(loaded_graph.answer_generate.name, 'AnswerGenerate')
        self.assertEqual(loaded_graph.sc_ensemble.name, 'QAScEnsemble')

    def tearDown(self):
        if os.path.exists('tests/src/workflow/saved_qa_action_graph.json'):
            os.remove('tests/src/workflow/saved_qa_action_graph.json')

def setUp(self):
    self.llm_config = OpenAILLMConfig(model='gpt-4o-mini', openai_key='XXX')
    self.qa_action_graph = QAActionGraph(llm_config=self.llm_config, name='QAActionGraph', description='This workflow aims to address multi-hop QA tasks.')

def test_save_and_load(self):
    self.qa_action_graph.save_module('tests/src/workflow/saved_qa_action_graph.json')
    loaded_graph = ActionGraph.from_file('tests/src/workflow/saved_qa_action_graph.json', llm_config=self.llm_config)
    self.assertEqual(loaded_graph.name, 'QAActionGraph')
    self.assertEqual(loaded_graph.description, 'This workflow aims to address multi-hop QA tasks.')
    self.assertEqual(loaded_graph.answer_generate.name, 'AnswerGenerate')
    self.assertEqual(loaded_graph.sc_ensemble.name, 'QAScEnsemble')

class TestModule(unittest.TestCase):

    def setUp(self):
        self.model = OpenAILLM(config=OpenAILLMConfig(model='gpt-4o-mini', openai_key='XXX'))
        self.graph = SEWWorkFlowGraph(llm=self.model)
        self.scheme = SEWWorkFlowScheme(self.graph)
    '\n    def test_python_scheme(self):\n\n        repr = self.scheme.convert_to_scheme(scheme="python")\n        new_graph = self.scheme.parse_workflow_python_repr("```python\n" + repr + "\n```")\n        self.assertEqual(len(new_graph.nodes), len(self.graph.nodes))\n        self.assertEqual(len(new_graph.edges), len(self.graph.edges))\n        self.assertFalse(new_graph == self.graph)\n\n        # test empty repr \n        new_graph = self.scheme.parse_workflow_python_repr("")\n        self.assertEqual(new_graph, self.graph)\n\n        # test invalid repr \n        new_graph = self.scheme.parse_workflow_python_repr("invalid repr")\n        self.assertEqual(new_graph, self.graph)\n\n        # test create new graph  \n        steps = eval(repr.replace("steps = ", "").strip())\n        new_steps = steps + [{"name": "test", "args": ["test_input", "code"], "outputs": ["test_output"]}]\n        new_repr = "steps = " + str(new_steps)\n        new_graph = self.scheme.parse_workflow_python_repr("```python\n" + new_repr + "\n```")\n        new_graph_info = new_graph.get_graph_info() \n        self.assertEqual(len(new_graph_info["tasks"]), 3) \n        self.assertEqual(new_graph_info["tasks"][-1]["name"], "test") \n        new_task_inputs = [input_info["name"] for input_info in new_graph_info["tasks"][-1]["inputs"]]\n        self.assertEqual(new_task_inputs, ["test_input", "code"])\n        new_task_outputs = [output_info["name"] for output_info in new_graph_info["tasks"][-1]["outputs"]]\n        self.assertEqual(new_task_outputs, ["test_output"])\n        self.assertFalse(new_graph == self.graph)\n    '

    def test_yaml_scheme(self):
        repr = self.scheme.convert_to_scheme(scheme='yaml')
        new_graph = self.scheme.parse_workflow_yaml_repr('```yaml\n' + repr + '\n```')
        self.assertEqual(len(new_graph.nodes), len(self.graph.nodes))
        self.assertEqual(len(new_graph.edges), len(self.graph.edges))
        self.assertFalse(new_graph == self.graph)
        new_graph = self.scheme.parse_workflow_yaml_repr('')
        self.assertEqual(new_graph, self.graph)
        new_graph = self.scheme.parse_workflow_yaml_repr('invalid repr')
        self.assertEqual(new_graph, self.graph)

    def test_code_scheme(self):
        repr = self.scheme.convert_to_scheme(scheme='code')
        new_graph = self.scheme.parse_workflow_code_repr('```code\n' + repr + '\n```')
        self.assertEqual(len(new_graph.nodes), len(self.graph.nodes))
        self.assertEqual(len(new_graph.edges), len(self.graph.edges))
        self.assertFalse(new_graph == self.graph)
        new_graph = self.scheme.parse_workflow_code_repr('')
        self.assertEqual(new_graph, self.graph)
        new_graph = self.scheme.parse_workflow_code_repr('invalid repr')
        self.assertEqual(new_graph, self.graph)

    def test_bpmn_scheme(self):
        repr = self.scheme.convert_to_scheme(scheme='bpmn')
        new_graph = self.scheme.parse_workflow_bpmn_repr('```bpmn\n' + repr + '\n```')
        self.assertEqual(len(new_graph.nodes), len(self.graph.nodes))
        self.assertEqual(len(new_graph.edges), len(self.graph.edges))
        self.assertFalse(new_graph == self.graph)
        new_graph = self.scheme.parse_workflow_bpmn_repr('')
        self.assertEqual(new_graph, self.graph)
        new_graph = self.scheme.parse_workflow_bpmn_repr('invalid repr')
        self.assertEqual(new_graph, self.graph)

    def test_core_scheme(self):
        repr = self.scheme.convert_to_scheme(scheme='core')
        new_graph = self.scheme.parse_workflow_core_repr('```core\n' + repr + '\n```')
        self.assertEqual(len(new_graph.nodes), len(self.graph.nodes))
        self.assertEqual(len(new_graph.edges), len(self.graph.edges))
        self.assertFalse(new_graph == self.graph)
        new_graph = self.scheme.parse_workflow_core_repr('')
        self.assertEqual(new_graph, self.graph)
        new_graph = self.scheme.parse_workflow_core_repr('invalid repr')
        self.assertEqual(new_graph, self.graph)

def setUp(self):
    self.model = OpenAILLM(config=OpenAILLMConfig(model='gpt-4o-mini', openai_key='XXX'))
    self.graph = SEWWorkFlowGraph(llm=self.model)
    self.scheme = SEWWorkFlowScheme(self.graph)

def test_openai_generation(mocker):
    mocker.patch('openai.resources.chat.completions.Completions.create', mock_openai_completions_create)
    model_name = 'gpt-4o-mini'
    config = OpenAILLMConfig(model=model_name, openai_key='mock_openai_key', output_response=False)
    model = OpenAILLM(config)
    prompt = 'what is the capital city of China. Only output the answer.'
    system_prompt = 'You are an expert in geography'
    output = model.generate(prompt=prompt, system_message=system_prompt)
    assert isinstance(output, LLMOutputParser)
    assert output.content == 'Beijing'
    assert str(output) == 'Beijing'
    assert cost_manager.total_tokens[model_name] == 23
    output = model.generate(prompt=[prompt], system_message=[system_prompt])
    assert isinstance(output, list) and isinstance(output[0], LLMOutputParser)
    assert output[0].content == 'Beijing'
    assert str(output[0]) == 'Beijing'
    assert cost_manager.total_tokens[model_name] == 23 * 2
    output = model.generate(messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}])
    assert isinstance(output, LLMOutputParser)
    assert output.content == 'Beijing'
    assert str(output) == 'Beijing'
    assert cost_manager.total_tokens[model_name] == 23 * 3
    output = model.generate(messages=[[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]])
    assert isinstance(output, list) and isinstance(output[0], LLMOutputParser)
    assert output[0].content == 'Beijing'
    assert str(output[0]) == 'Beijing'
    assert cost_manager.total_tokens[model_name] == 23 * 4
    output = model.generate(prompt=prompt, system_message=system_prompt, stream=True)
    assert isinstance(output, LLMOutputParser)
    assert output.content == 'Beijing'
    assert str(output) == 'Beijing'
    assert cost_manager.total_tokens[model_name] > 23 * 4

