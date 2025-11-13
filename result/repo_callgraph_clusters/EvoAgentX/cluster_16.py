# Cluster 16

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

def init_module(self):
    self._lock = threading.Lock()
    self._state_conditions = {}
    if self.agents:
        for agent in self.agents:
            self.agent_states[agent.name] = self.agent_states.get(agent.name, AgentState.AVAILABLE)
            if agent.name not in self._state_conditions:
                self._state_conditions[agent.name] = threading.Condition()
        self.check_agents()

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

class WorkFlow(BaseModule):
    graph: WorkFlowGraph
    llm: Optional[BaseLLM] = None
    agent_manager: AgentManager = Field(default=None, description='Responsible for managing agents')
    workflow_manager: WorkFlowManager = Field(default=None, description='Responsible for task and action scheduling for workflow execution')
    environment: Environment = Field(default_factory=Environment)
    storage_handler: StorageHandler = None
    workflow_id: str = Field(default_factory=generate_id)
    version: int = 0
    max_execution_steps: int = Field(default=5, description='The maximum number of steps to complete a subtask (node) in the workflow')
    hitl_manager: HITLManager = Field(default=None, description='Responsible for HITL work management')

    def init_module(self):
        if self.workflow_manager is None:
            if self.llm is None:
                raise ValueError('Must provide `llm` when `workflow_manager` is None')
            self.workflow_manager = WorkFlowManager(llm=self.llm)
        if self.agent_manager is None:
            logger.warning('agent_manager is NoneType when initializing a WorkFlow instance')

    def execute(self, inputs: dict={}, **kwargs) -> str:
        """
        Synchronous wrapper for async_execute. Creates a new event loop and runs the async method.
        
        Args:
            inputs: Dictionary of inputs for workflow execution
            **kwargs (Any): Additional keyword arguments
            
        Returns:
            str: The output of the workflow execution
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_execute(inputs, **kwargs))
        finally:
            loop.close()

    async def async_execute(self, inputs: dict={}, **kwargs) -> str:
        """
        Asynchronously execute the workflow.
        
        Args:
            inputs: Dictionary of inputs for workflow execution
            **kwargs (Any): Additional keyword arguments
            
        Returns:
            str: The output of the workflow execution
        """
        goal = self.graph.goal
        inputs = self._prepare_inputs(inputs)
        if hasattr(self, 'hitl_manager') and self.hitl_manager is not None:
            self._prepare_hitl()
        self._validate_workflow_structure(inputs=inputs, **kwargs)
        inp_message = Message(content=inputs, msg_type=MessageType.INPUT, wf_goal=goal)
        self.environment.update(message=inp_message, state=TrajectoryState.COMPLETED)
        failed = False
        error_message = None
        while not self.graph.is_complete and (not failed):
            try:
                task: WorkFlowNode = await self.get_next_task()
                if task is None:
                    break
                logger.info(f'Executing subtask: {task.name}')
                await self.execute_task(task=task)
            except Exception as e:
                failed = True
                error_message = Message(content=f'An Error occurs when executing the workflow: {e}', msg_type=MessageType.ERROR, wf_goal=goal)
                self.environment.update(message=error_message, state=TrajectoryState.FAILED, error=str(e))
        if failed:
            logger.error(error_message.content)
            return 'Workflow Execution Failed'
        logger.info('Extracting WorkFlow Output ...')
        output: str = await self.workflow_manager.extract_output(graph=self.graph, env=self.environment)
        return output

    def _prepare_inputs(self, inputs: dict) -> dict:
        """
        Prepare the inputs for the workflow execution. Mainly determine whether the goal should be added to the inputs.
        """
        initial_node_names = self.graph.find_initial_nodes()
        initial_node_required_inputs = set()
        for initial_node_name in initial_node_names:
            initial_node = self.graph.get_node(initial_node_name)
            if initial_node.inputs:
                initial_node_required_inputs.update([inp.name for inp in initial_node.inputs if inp.required])
        if 'goal' in initial_node_required_inputs and 'goal' not in inputs:
            inputs.update({'goal': self.graph.goal})
        return inputs

    async def get_next_task(self) -> WorkFlowNode:
        task_execution_history = ' -> '.join(self.environment.task_execution_history)
        if not task_execution_history:
            task_execution_history = 'None'
        logger.info(f'Task Execution Trajectory: {task_execution_history}. Scheduling next subtask ...')
        task: WorkFlowNode = await self.workflow_manager.schedule_next_task(graph=self.graph, env=self.environment)
        logger.info(f'The next subtask to be executed is: {task.name}')
        return task

    async def execute_task(self, task: WorkFlowNode):
        """
        Asynchronously execute a workflow task.
        
        Args:
            task: The workflow node to execute
        """
        last_executed_task = self.environment.get_last_executed_task()
        self.graph.step(source_node=last_executed_task, target_node=task)
        next_action: NextAction = await self.workflow_manager.schedule_next_action(goal=self.graph.goal, task=task, agent_manager=self.agent_manager, env=self.environment)
        if next_action.action_graph is not None:
            await self._async_execute_task_by_action_graph(task=task, next_action=next_action)
        else:
            await self._async_execute_task_by_agents(task=task, next_action=next_action)
        self.graph.completed(node=task)

    async def _async_execute_task_by_action_graph(self, task: WorkFlowNode, next_action: NextAction):
        """
        Asynchronously execute a task using an action graph.
        
        Args:
            task: The workflow node to execute
            next_action: The next action to perform with its action graph
        """
        action_graph: ActionGraph = next_action.action_graph
        async_execute_source = inspect.getsource(action_graph.async_execute)
        if 'NotImplementedError' in async_execute_source:
            execute_function = action_graph.execute
            async_execute = False
        else:
            execute_function = action_graph.async_execute
            async_execute = True
        execute_signature = inspect.signature(execute_function)
        execute_params = {}
        action_input_data = self.environment.get_all_execution_data()
        for param_name, param_obj in execute_signature.parameters.items():
            if param_name in ['self', 'args', 'kwargs']:
                continue
            if param_name in action_input_data:
                execute_params[param_name] = action_input_data[param_name]
            elif param_obj.default is not param_obj.empty:
                execute_params[param_name] = param_obj.default
            else:
                execute_params[param_name] = None
        if async_execute:
            action_graph_output: dict = await action_graph.async_execute(**execute_params)
        else:
            action_graph_output: dict = action_graph.execute(**execute_params)
        message = Message(content=action_graph_output, action=action_graph.name, msg_type=MessageType.RESPONSE, wf_goal=self.graph.goal, wf_task=task.name, wf_task_desc=task.description)
        self.environment.update(message=message, state=TrajectoryState.COMPLETED)

    async def _async_execute_task_by_agents(self, task: WorkFlowNode, next_action: NextAction):
        """
        Asynchronously execute a task using agents.
        
        Args:
            task: The workflow node to execute
            next_action: The next action to perform using agents
        """
        num_execution = 0
        while next_action:
            if num_execution >= self.max_execution_steps:
                raise ValueError(f'Maximum number of steps ({self.max_execution_steps}) reached when executing {task.name}. Please check the workflow structure (e.g., inputs and outputs of the nodes and the agents) or increase the `max_execution_steps` parameter.')
            agent: Agent = self.agent_manager.get_agent(agent_name=next_action.agent)
            if not self.agent_manager.wait_for_agent_available(agent_name=agent.name, timeout=300):
                raise TimeoutError(f'Timeout waiting for agent {agent.name} to become available')
            self.agent_manager.set_agent_state(agent_name=next_action.agent, new_state=AgentState.RUNNING)
            try:
                message = await self._async_execute_action(task=task, agent=agent, next_action=next_action)
                self.environment.update(message=message, state=TrajectoryState.COMPLETED)
            finally:
                self.agent_manager.set_agent_state(agent_name=next_action.agent, new_state=AgentState.AVAILABLE)
            if self.is_task_completed(task=task):
                break
            next_action: NextAction = await self.workflow_manager.schedule_next_action(goal=self.graph.goal, task=task, agent_manager=self.agent_manager, env=self.environment)
            num_execution += 1

    async def _async_execute_action(self, task: WorkFlowNode, agent: Agent, next_action: NextAction) -> Message:
        """
        Asynchronously execute an action using an agent.
        """
        action_name = next_action.action
        all_execution_data = self.environment.get_all_execution_data()
        if hasattr(self, 'hitl_manager') and self.hitl_manager is not None:
            hitl_manager = self.hitl_manager
        else:
            hitl_manager = None
        action_inputs_format = agent.get_action(action_name).inputs_format
        action_input_data = {}
        if action_inputs_format:
            for input_name in action_inputs_format.get_attrs():
                if input_name in all_execution_data:
                    action_input_data[input_name] = all_execution_data[input_name]
            action_required_input_names = action_inputs_format.get_required_input_names()
            if not all((inp in action_input_data for inp in action_required_input_names)):
                predecessors = self.graph.get_node_predecessors(node=task)
                predecessors_messages = self.environment.get_task_messages(tasks=predecessors + [task.name], include_inputs=True)
                predecessors_messages = [message for message in predecessors_messages if message.msg_type in [MessageType.INPUT, MessageType.RESPONSE]]
                message, extracted_data = await agent.async_execute(action_name=action_name, msgs=predecessors_messages, return_msg_type=MessageType.RESPONSE, return_action_input_data=True, wf_goal=self.graph.goal, wf_task=task.name, wf_task_desc=task.description, hitl_manager=hitl_manager)
                self.environment.update_execution_data_from_context_extraction(extracted_data)
                return message
        message = await agent.async_execute(action_name=action_name, action_input_data=action_input_data, return_msg_type=MessageType.RESPONSE, wf_goal=self.graph.goal, wf_task=task.name, wf_task_desc=task.description, hitl_manager=hitl_manager)
        return message

    def is_task_completed(self, task: WorkFlowNode) -> bool:
        task_outputs = [output.name for output in task.outputs]
        current_execution_data = self.environment.get_all_execution_data()
        return all((output in current_execution_data for output in task_outputs))

    def _validate_workflow_structure(self, inputs: dict, **kwargs):
        input_names = set(inputs.keys())
        for node in self.graph.nodes:
            node_input_names = deepcopy(input_names)
            is_initial_node = True
            for name in self.graph.get_node_predecessors(node):
                is_initial_node = False
                predecessor = self.graph.get_node(name)
                node_input_names.update(predecessor.get_output_names())
            node_required_input_names = set(node.get_input_names(required=True))
            if not all((input_name in node_input_names for input_name in node_required_input_names)):
                missing_required_inputs = node_required_input_names - node_input_names
                if is_initial_node:
                    raise ValueError(f"The initial node '{node.name}' is missing required inputs: {list(missing_required_inputs)}. You should provide these inputs by specifying the `inputs={{'input_name': 'input_value'}}` parameter in the `execute` method, or return the valid inputs in the `collate_func` when using `Evaluator`.")
                else:
                    raise ValueError(f"The node '{node.name}' is missing required inputs: {list(missing_required_inputs)}. You may need to check the `inputs` and `outputs` of the nodes to ensure that all the required inputs of node '{node.name}' are provided by either its predecessors or the `inputs` parameter in the `execute` method.")
        for node in self.graph.nodes:
            for agent in node.agents:
                if hasattr(agent, 'forbidden_in_workflow') and agent.forbidden_in_workflow:
                    raise ValueError(f'The Agent of class {agent.__class__} is forbidden to be used in the workflow.')

    def _prepare_single_hitl_agent(self, agent: Agent, node: WorkFlowNode):
        """
        add complementary information and settings which need dynamically setting up to a single hitl agent
        For example, the `inputs_format` attribute, this needs a dynamical setting up.
        Up to Now, we only consider a HITL agent must be the only agent in its WorkFlowNode instance, this condition may be changed in the future
        Args:
            agent (Agent): a single HITL Agent instance 
            node (WorkFlowNode): a single WorkFlowNode instane which contains exactly the agent of previous param.
        """
        predecessors: List[str] = self.graph.get_node_predecessors(node)
        hitl_action = None
        for action in agent.actions:
            if action.inputs_format and action.outputs_format:
                continue
            elif hasattr(action, 'interaction_type'):
                hitl_action = action
                break
        if not hitl_action:
            raise ValueError(f'Can not find a HITL action in agent {agent}')
        hitl_inputs_data_fields = {}
        for predecessor in predecessors:
            predecessor_node = self.graph.get_node(predecessor)
            for param in predecessor_node.outputs:
                if param.required:
                    hitl_inputs_data_fields[param.name] = (str, Field(description=param.description))
                else:
                    hitl_inputs_data_fields[param.name] = (Optional[str], Field(description=param.description))
        inputs_format = create_model(agent._get_unique_class_name(generate_dynamic_class_name(hitl_action.class_name + ' action_input')), **hitl_inputs_data_fields or {}, __base__=ActionInput)
        successors: List[str] = self.graph.get_node_children(node)
        hitl_outputs_data_fields = {}
        if successors == []:
            raise ValueError('WorkFlowNode with a HITL Agent can not be set as the ending node.')
        for successor in successors:
            successor_node = self.graph.get_node(successor)
            for param in successor_node.inputs:
                if param.required:
                    hitl_outputs_data_fields[param.name] = (str, Field(description=param.description))
                else:
                    hitl_outputs_data_fields[param.name] = (Optional[str], Field(description=param.description))
        outputs_format = create_model(agent._get_unique_class_name(generate_dynamic_class_name(hitl_action.class_name + ' action_output')), **hitl_outputs_data_fields or {}, __base__=ActionOutput)
        hitl_action.inputs_format = inputs_format
        hitl_action.outputs_format = outputs_format
        if self.hitl_manager.hitl_input_output_mapping is None:
            raise ValueError('hitl_input_output_mapping attribute missing in HITLManager instance.')
        return

    def _prepare_hitl(self):
        """
        Prepare hitl settings before executing the WorkFlow
        """
        if self.hitl_manager is None:
            return
        hitl_agents: List[Agent] = []
        node_with_hitl_agents = []
        for node in self.graph.nodes:
            agents = node.agents
            found_hitl_agent = False
            for agent in agents:
                if isinstance(agent, dict):
                    agent = self.agent_manager.get_agent(self.agent_manager.get_agent_name(agent))
                elif isinstance(agent, str):
                    agent = self.agent_manager.get_agent(agent)
                elif isinstance(agent, Agent):
                    pass
                if isinstance(agent, HITLBaseAgent):
                    found_hitl_agent = True
                    if agent not in hitl_agents:
                        hitl_agents.append(agent)
            if found_hitl_agent:
                node_with_hitl_agents.append(node)
                found_hitl_agent = False
        if len(hitl_agents) != len(node_with_hitl_agents):
            raise ValueError('Incorrect WorkFlowNode definition: A HITL Agent must be the only agent in its WorkFlowNode instance')
        for agent, node in zip(hitl_agents, node_with_hitl_agents):
            self._prepare_single_hitl_agent(agent, node)
        return

def _prepare_hitl(self):
    """
        Prepare hitl settings before executing the WorkFlow
        """
    if self.hitl_manager is None:
        return
    hitl_agents: List[Agent] = []
    node_with_hitl_agents = []
    for node in self.graph.nodes:
        agents = node.agents
        found_hitl_agent = False
        for agent in agents:
            if isinstance(agent, dict):
                agent = self.agent_manager.get_agent(self.agent_manager.get_agent_name(agent))
            elif isinstance(agent, str):
                agent = self.agent_manager.get_agent(agent)
            elif isinstance(agent, Agent):
                pass
            if isinstance(agent, HITLBaseAgent):
                found_hitl_agent = True
                if agent not in hitl_agents:
                    hitl_agents.append(agent)
        if found_hitl_agent:
            node_with_hitl_agents.append(node)
            found_hitl_agent = False
    if len(hitl_agents) != len(node_with_hitl_agents):
        raise ValueError('Incorrect WorkFlowNode definition: A HITL Agent must be the only agent in its WorkFlowNode instance')
    for agent, node in zip(hitl_agents, node_with_hitl_agents):
        self._prepare_single_hitl_agent(agent, node)
    return

class SQLite(DBStoreBase):
    """
    SQLite implementation of the DBStoreBase interface.
    Provides methods for inserting, deleting, updating, and retrieving metadata in a SQLite database.
    Uses thread-safe operations with locking.
    """

    def __init__(self, path, *args, **kwargs) -> None:
        """
        Initialize the SQLite database connection.

        Attributes:
            path (str): Path to the SQLite database file.

        """
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()

    @check_db_format
    def insert_memory(self, metadata: MemoryStore, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Insert memory metadata into the specified table.

        Attributes:
            metadata (MemoryStore): The memory metadata to insert.
            store_type (str): The type of store (e.g., 'memory').
            table (Optional[str]): The table name; defaults to 'memory' if None.
        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = TableType.store_memory
                insert_string = _insert_meta(table, list(MemoryStore.model_fields.keys()))
                self.connection.execute(insert_string, tuple([json.dumps(meta) if not isinstance(meta, str) else meta for meta in metadata.model_dump().values()]))
                self.connection.commit()

    @check_db_format
    def insert_agent(self, metadata: AgentStore, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Insert agent metadata into the specified table.

        Attributes:
            metadata (AgentStore): The agent metadata to insert.
            store_type (str): The type of store (e.g., 'agent').
            table (Optional[str]): The table name; defaults to 'agent' if None.

        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = TableType.store_agent
                insert_string = _insert_meta(table, list(AgentStore.model_fields.keys()))
                self.connection.execute(insert_string, tuple([json.dumps(meta) if not isinstance(meta, str) else meta for meta in metadata.model_dump().values()]))
                self.connection.commit()

    @check_db_format
    def insert_workflow(self, metadata: WorkflowStore, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Insert workflow metadata into the specified table.

        Attributes:
            metadata (WorkflowStore): The workflow metadata to insert.
            store_type (str): The type of store (e.g., 'workflow').
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = TableType.store_workflow
                insert_string = _insert_meta(table, list(WorkflowStore.model_fields.keys()))
                self.connection.execute(insert_string, tuple([json.dumps(meta) if not isinstance(meta, str) else meta for meta in metadata.model_dump().values()]))
                self.connection.commit()

    @check_db_format
    def insert_history(self, metadata: HistoryStore, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Insert history metadata into the specified table.

        Attributes:
            metadata (HistoryStore): The history metadata to insert.
            store_type (str): The type of store (e.g., 'history').
            table (Optional[str]): The table name; defaults to 'history' if None.

        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = TableType.store_history
                insert_string = _insert_meta(table, list(HistoryStore.model_fields.keys()))
                self.connection.execute(insert_string, tuple([json.dumps(meta) if not isinstance(meta, str) else meta for meta in metadata.model_dump().values()]))
                self.connection.commit()

    @check_db_format
    def insert_index(self, metadata: IndexStore, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Insert index metadata into the specified table.

        Attributes:
            metadata (IndexStore): The index metadata to insert.
            store_type (str): The type of store (e.g., 'index').
            table (Optional[str]): The table name; defaults to 'index' if None.
        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = TableType.store_indexing
                insert_string = _insert_meta(table, list(IndexStore.model_fields.keys()))
                self.connection.execute(insert_string, tuple([json.dumps(meta) if not isinstance(meta, str) else meta for meta in metadata.model_dump().values()]))
                self.connection.commit()

    def insert(self, metadata: Dict, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Generic insert method that delegates to specific insert methods based on store_type.

        Attributes:
            metadata (Dict): The metadata to insert.
            store_type (str): The type of store (e.g., 'memory', 'agent').
            table (Optional[str]): The table name; defaults to store_type's default if None.

        """
        if store_type == TableType.store_memory:
            self.insert_memory(metadata, *args, store_type=store_type, table=table, **kwargs)
        elif store_type == TableType.store_agent:
            self.insert_agent(metadata, *args, store_type=store_type, table=table, **kwargs)
        elif store_type == TableType.store_workflow:
            self.insert_workflow(metadata, *args, store_type=store_type, table=table, **kwargs)
        elif store_type == TableType.store_history:
            self.insert_history(metadata, *args, store_type=store_type, table=table, **kwargs)
        elif store_type == TableType.store_indexing:
            self.insert_index(metadata, *args, store_type=store_type, table=table, **kwargs)
        else:
            raise ValueError('Invalid store_type provided.')

    def delete(self, metadata_id: str, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Delete metadata by its ID from the specified table.

        Attributes:
            metadata_id (str): The ID of the metadata to delete.
            store_type (str): The type of store (e.g., 'memory').
            table (Optional[str]): The table name; defaults to store_type's default if None.


        Returns:
            bool: True if deletion was successful, False if no record was found.
        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = getattr(TableType, store_type)
                try:
                    cursor = self.connection.cursor()
                    delete_query = f'DELETE FROM {table} WHERE {self._get_id_column(store_type)} = ?'
                    cursor.execute(delete_query, (metadata_id,))
                    self.connection.commit()
                    return cursor.rowcount > 0
                except sqlite3.OperationalError:
                    return False

    def update(self, metadata_id: str, new_metadata: Dict=None, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']]=None, table: Optional[str]=None, *args, **kwargs):
        """
        Update metadata by its ID in the specified table.

        Attributes:
            metadata_id (str): The ID of the metadata to update.
            new_metadata (Dict): The new metadata to apply.
            store_type (str): The type of store (e.g., 'memory').
            table (Optional[str]): The table name; defaults to store_type's default if None.


        Returns:
            bool: True if update was successful, False if no record was found.
        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = store_type
                if store_type == TableType.store_memory:
                    columns = list(MemoryStore.model_fields.keys())
                    new_metadata = MemoryStore.model_validate(new_metadata)
                elif store_type == TableType.store_agent:
                    columns = list(AgentStore.model_fields.keys())
                    new_metadata = AgentStore.model_validate(new_metadata)
                elif store_type == TableType.store_workflow:
                    columns = list(WorkflowStore.model_fields.keys())
                    new_metadata = WorkflowStore.model_validate(new_metadata)
                elif store_type == TableType.store_history:
                    columns = list(HistoryStore.model_fields.keys())
                    new_metadata = HistoryStore.model_validate(new_metadata)
                elif store_type == TableType.store_indexing:
                    columns = list(IndexStore.model_fields.keys())
                    new_metadata = IndexStore.model_validate(new_metadata)
                else:
                    raise ValueError('Invalid store_type provided.')
                set_clause = ', '.join([f'"{col}" = ?' for col in columns[1:]])
                update_query = f'UPDATE {table} SET {set_clause} WHERE "{columns[0]}" = ?'
                values = list([json.dumps(v) if not isinstance(v, str) else v for v in new_metadata.model_dump().values()])[1:] + [metadata_id]
                cursor = self.connection.cursor()
                cursor.execute(update_query, values)
                self.connection.commit()
                return cursor.rowcount > 0

    def get_by_id(self, metadata_id: str, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']], table: Optional[str]=None, *args, **kwargs):
        """
        Retrieve metadata by its ID from the specified table.

        Attributes:
            metadata_id (str): The ID of the metadata to retrieve.
            store_type (str): The type of store (e.g., 'store_memory').
            table (Optional[str]): The table name; defaults to store_type's default if None.


        Returns:
            Dict: The retrieved metadata as a dictionary, or None if not found.
        """
        with self._lock:
            with self.connection:
                if table is None:
                    table = store_type
                if store_type == TableType.store_memory:
                    columns = list(MemoryStore.model_fields.keys())
                elif store_type == TableType.store_agent:
                    columns = list(AgentStore.model_fields.keys())
                elif store_type == TableType.store_workflow:
                    columns = list(WorkflowStore.model_fields.keys())
                elif store_type == TableType.store_history:
                    columns = list(HistoryStore.model_fields.keys())
                elif store_type == TableType.store_indexing:
                    columns = list(IndexStore.model_fields.keys())
                else:
                    raise ValueError('Invalid store_type provided.')
                try:
                    cursor = self.connection.cursor()
                    select_query = f'SELECT * FROM {table} WHERE {columns[0]} = ?'
                    cursor.execute(select_query, (metadata_id,))
                    result = cursor.fetchone()
                    if result:
                        return dict(zip(columns, result))
                    return None
                except sqlite3.OperationalError:
                    return None

    def col_info(self):
        """
        Retrieve information about all tables in the database.

        Returns:
            List[Dict]: A list of dictionaries containing table names and their column information,
                        where columns is a dictionary mapping column names to their data types.
        """
        with self._lock:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                table_info = []
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f'PRAGMA table_info({table_name})')
                    columns = cursor.fetchall()
                    table_info.append({'table_name': table_name, 'columns': {col[1]: col[2] for col in columns}})
                return table_info

    def _get_id_column(self, store_type: Optional[Literal['memory', 'agent', 'workflow', 'history', 'indexing']]) -> str:
        """
        Helper method to get the primary key column name for a store type.

        Attributes:
            store_type (str): The type of store (e.g., 'memory').

        Returns:
            str: The name of the primary key column.

        Raises:
            ValueError: If store_type is invalid.
        """
        if store_type == TableType.store_memory:
            return list(MemoryStore.model_fields.keys())[0]
        elif store_type == TableType.store_agent:
            return list(AgentStore.model_fields.keys())[0]
        elif store_type == TableType.store_workflow:
            return list(WorkflowStore.model_fields.keys())[0]
        elif store_type == TableType.store_history:
            return list(HistoryStore.model_fields.keys())[0]
        elif store_type == TableType.store_indexing:
            return list(IndexStore.model_fields.keys())[0]
        else:
            raise ValueError('Invalid store_type provided.')

def __init__(self, path, *args, **kwargs) -> None:
    """
        Initialize the SQLite database connection.

        Attributes:
            path (str): Path to the SQLite database file.

        """
    self.connection = sqlite3.connect(path, check_same_thread=False)
    self._lock = threading.Lock()

class MiproEvaluator:

    def __init__(self, benchmark: Benchmark, num_threads: Optional[int]=None, display_progress: Optional[bool]=None, max_errors: int=5, return_all_scores: bool=False, return_outputs: bool=False, provide_traceback: bool=False, failure_score: float=0.0, metric_name: Optional[str]=None, **kwargs):
        self.benchmark = benchmark
        self.num_threads = num_threads
        self.display_progress = display_progress
        self.max_errors = max_errors
        self.return_all_scores = return_all_scores
        self.return_outputs = return_outputs
        self.provide_traceback = provide_traceback
        self.failure_score = failure_score
        self.metric_name = metric_name
        self.kwargs = kwargs
        self._log_counter = 0
        self._log_lock = threading.Lock()

    def _extract_score_from_dict(self, score_dict: Dict[str, float]) -> float:
        """Extract a single score from a dictionary of scores.
        
        Args:
            score_dict (Dict[str, float]): Dictionary containing metric scores
            
        Returns:
            float: The extracted score based on the following rules:
                1. If dict has only one score, return that score
                2. If metric_name is specified, return that metric's score
                3. Otherwise, return average of all scores
        """
        if len(score_dict) == 1:
            return list(score_dict.values())[0]
        elif self.metric_name is not None:
            return score_dict[self.metric_name]
        else:
            avg_score = sum(score_dict.values()) / len(score_dict)
            with self._log_lock:
                if self._log_counter == 0:
                    logger.info(f'`{type(self.benchmark)}.evaluate` returned a dictionary of scores, but no metric name was provided. Will return the average score across all metrics.')
                    self._log_counter += 1
            return avg_score

    def metric(self, example: dspy.Example, prediction: Any, *args, **kwargs):
        if isinstance(self.benchmark.get_train_data()[0], dspy.Example):
            score = self.benchmark.evaluate(prediction=prediction, label=self.benchmark.get_label(example))
        elif isinstance(self.benchmark.get_train_data()[0], dict):
            score = self.benchmark.evaluate(prediction=prediction, label=self.benchmark.get_label(example.toDict()))
        else:
            raise ValueError(f'Unsupported example type in `{type(self.benchmark)}`! Expected `dspy.Example` or `dict`, got {type(self.benchmark.get_train_data()[0])}')
        if isinstance(score, dict):
            score = self._extract_score_from_dict(score)
        return score

    def __call__(self, program: Callable, evalset: List[Any], **kwargs) -> float:
        return_all_scores = kwargs.get('return_all_scores', None) or self.return_all_scores
        return_outputs = kwargs.get('return_outputs', None) or self.return_outputs
        tqdm.tqdm._instances.clear()
        from ..core.callbacks import suppress_cost_logs
        current_suppress_cost = suppress_cost_logs.get()
        if self.num_threads and self.num_threads > 1:
            executor = ParallelExecutor(num_threads=self.num_threads, disable_progress_bar=not self.display_progress, max_errors=self.max_errors, provide_traceback=self.provide_traceback, compare_results=True)
        else:
            executor = None

        def process_item(example):
            token = suppress_cost_logs.set(current_suppress_cost)
            try:
                if not isinstance(example, dspy.Example):
                    raise ValueError(f'Example from benchmark must be a dspy.Example object, got {type(example)}')
                try:
                    prediction = program(**example.inputs())
                    score = self.metric(example, prediction)
                except Exception as e:
                    logger.error(f'Error evaluating example {example}: {e}')
                    return (None, self.failure_score)
                if hasattr(program, '_assert_failures'):
                    program._assert_failures += dspy.settings.get('assert_failures')
                if hasattr(program, '_suggest_failures'):
                    program._suggest_failures += dspy.settings.get('suggest_failures')
                return (prediction, score)
            finally:
                suppress_cost_logs.reset(token)
        if executor:
            results = executor.execute(process_item, evalset)
        else:
            results = []
            pbar = tqdm.tqdm(total=len(evalset), dynamic_ncols=True, disable=not self.display_progress, desc='Processing examples')
            for example in evalset:
                result = process_item(example)
                results.append(result)
                if result and result[1] is not None:
                    current_scores = [r[1] for r in results if r and r[1] is not None]
                    avg_score = sum(current_scores) / len(current_scores) if current_scores else 0
                    pbar.set_description(f'Average Metric: {avg_score:.2f}')
                pbar.update(1)
            pbar.close()
        assert len(evalset) == len(results)
        results = [(example, prediction, score) for example, (prediction, score) in zip(evalset, results)]
        ncorrect, ntotal = (sum((score for *_, score in results)), len(evalset))
        logger.info(f'Average Metric: {ncorrect} / {ntotal} ({round(100 * ncorrect / ntotal, 1)}%)')
        if return_all_scores and return_outputs:
            return (round(100 * ncorrect / ntotal, 2), results, [score for *_, score in results])
        if return_all_scores:
            return (round(100 * ncorrect / ntotal, 2), [score for *_, score in results])
        if return_outputs:
            return (round(100 * ncorrect / ntotal, 2), results)
        return round(100 * ncorrect / ntotal, 2)

def __init__(self, benchmark: Benchmark, num_threads: Optional[int]=None, display_progress: Optional[bool]=None, max_errors: int=5, return_all_scores: bool=False, return_outputs: bool=False, provide_traceback: bool=False, failure_score: float=0.0, metric_name: Optional[str]=None, **kwargs):
    self.benchmark = benchmark
    self.num_threads = num_threads
    self.display_progress = display_progress
    self.max_errors = max_errors
    self.return_all_scores = return_all_scores
    self.return_outputs = return_outputs
    self.provide_traceback = provide_traceback
    self.failure_score = failure_score
    self.metric_name = metric_name
    self.kwargs = kwargs
    self._log_counter = 0
    self._log_lock = threading.Lock()

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

def atomic(lock=None):
    """
    threading safe decorator, it can be used to decorate a function or receive a lock:
    1. directly decorate a function: @atomic 
    2. receive a lock: @atomic(lock=shared_lock)
    """
    lock = lock or threading.Lock()

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator if not callable(lock) else decorator(lock)

class CostManager:

    def __init__(self):
        self.total_input_tokens = {}
        self.total_output_tokens = {}
        self.total_tokens = {}
        self.total_input_cost = {}
        self.total_output_cost = {}
        self.total_cost = {}
        self._lock = threading.Lock()

    def compute_total_cost(self):
        total_tokens, total_cost = (0, 0.0)
        for _, value in self.total_tokens.items():
            total_tokens += value
        for _, value in self.total_cost.items():
            total_cost += value
        return (total_tokens, total_cost)

    @atomic_method
    def update_cost(self, cost: Cost, model: str):
        self.total_input_tokens[model] = self.total_input_tokens.get(model, 0) + cost.input_tokens
        self.total_output_tokens[model] = self.total_output_tokens.get(model, 0) + cost.output_tokens
        current_total_tokens = cost.input_tokens + cost.output_tokens
        self.total_tokens[model] = self.total_tokens.get(model, 0) + current_total_tokens
        self.total_input_cost[model] = self.total_input_cost.get(model, 0.0) + cost.input_cost
        self.total_output_cost[model] = self.total_output_cost.get(model, 0.0) + cost.output_cost
        current_total_cost = cost.input_cost + cost.output_cost
        self.total_cost[model] = self.total_cost.get(model, 0.0) + current_total_cost
        total_tokens, total_cost = self.compute_total_cost()
        if not suppress_cost_logs.get():
            logger.info(f'Total cost: ${total_cost:.3f} | Total tokens: {total_tokens} | Current cost: ${current_total_cost:.3f} | Current tokens: {current_total_tokens}')

    def display_cost(self):
        data = {'Model': [], 'Total Cost (USD)': [], 'Total Input Cost (USD)': [], 'Total Output Cost (USD)': [], 'Total Tokens': [], 'Total Input Tokens': [], 'Total Output Tokens': []}
        for model in self.total_tokens.keys():
            data['Model'].append(model)
            data['Total Cost (USD)'].append(round(self.total_cost[model], 4))
            data['Total Input Cost (USD)'].append(round(self.total_input_cost[model], 4))
            data['Total Output Cost (USD)'].append(round(self.total_output_cost[model], 4))
            data['Total Tokens'].append(self.total_tokens[model])
            data['Total Input Tokens'].append(self.total_input_tokens[model])
            data['Total Output Tokens'].append(self.total_output_tokens[model])
        df = pd.DataFrame(data)
        if len(df) > 1:
            summary = {'Model': 'TOTAL', 'Total Cost (USD)': df['Total Cost (USD)'].sum(), 'Total Input Cost (USD)': df['Total Input Cost (USD)'].sum(), 'Total Output Cost (USD)': df['Total Output Cost (USD)'].sum(), 'Total Tokens': df['Total Tokens'].sum(), 'Total Input Tokens': df['Total Input Tokens'].sum(), 'Total Output Tokens': df['Total Output Tokens'].sum()}
            df = df._append(summary, ignore_index=True)
        print(df.to_string(index=False))

    def get_total_cost(self):
        total_cost = 0.0
        for model in self.total_cost.keys():
            total_cost += self.total_cost[model]
        return total_cost

def __init__(self):
    self.total_input_tokens = {}
    self.total_output_tokens = {}
    self.total_tokens = {}
    self.total_input_cost = {}
    self.total_output_cost = {}
    self.total_cost = {}
    self._lock = threading.Lock()

class TestEvaluator(unittest.TestCase):

    def setUp(self):
        self.benchmark = Mock(spec=Benchmark)
        self.benchmark.get_test_data.return_value = [{'id': '1', 'input': 'test1'}, {'id': '2', 'input': 'test2'}]
        self.benchmark.get_id.side_effect = lambda example: example['id']
        self.benchmark.get_label.return_value = 'expected'
        self.benchmark.evaluate.return_value = {'accuracy': 1.0}
        self.llm = Mock(spec=BaseLLM)
        self.agent_manager = Mock(spec=AgentManager)
        self.workflow_graph = Mock(spec=WorkFlowGraph)
        self.action_graph = Mock(spec=ActionGraph)
        self.action_graph.execute.return_value = {'output': 'prediction'}
        self.evaluator = Evaluator(llm=self.llm, num_workers=1, agent_manager=self.agent_manager)

    @patch.object(Evaluator, '_execute_workflow_graph')
    def test_single_thread_evaluation_workflow_graph(self, mock_execute):
        mock_execute.return_value = ('workflow_graph_prediction', ['trajectory_data'])
        results = self.evaluator.evaluate(graph=self.workflow_graph, benchmark=self.benchmark, eval_mode='test')
        self.assertEqual(mock_execute.call_count, 2)
        self.assertEqual(results, {'accuracy': 1.0})
        self.assertEqual(len(self.evaluator.get_all_evaluation_records()), 2)

    def test_single_thread_evaluation_action_graph(self):
        results = self.evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='test')
        self.assertEqual(results, {'accuracy': 1.0})
        self.assertEqual(len(self.evaluator.get_all_evaluation_records()), 2)

    def test_evaluation_with_custom_collate(self):

        def collate_func(x):
            return {'processed_' + k: v for k, v in x.items()}
        evaluator = Evaluator(llm=self.llm, num_workers=1, collate_func=collate_func)
        evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='test')
        call_args = self.action_graph.execute.call_args_list[0][1]
        self.assertTrue(all((k.startswith('processed_') for k in call_args.keys())))

    def test_evaluation_with_output_postprocess(self):

        def postprocess_func(x):
            return x['output'].upper()
        evaluator = Evaluator(llm=self.llm, num_workers=1, output_postprocess_func=postprocess_func)
        evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='test')
        records = evaluator.get_all_evaluation_records()
        for record in records.values():
            self.assertEqual(record['prediction'], 'PREDICTION')

    def test_get_example_evaluation_record(self):
        self.evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='test')
        example = {'id': '1', 'input': 'test1'}
        record = self.evaluator.get_example_evaluation_record(self.benchmark, example)
        self.assertIsNotNone(record)
        self.assertEqual(record['prediction'], {'output': 'prediction'})
        self.assertEqual(record['label'], 'expected')
        self.assertEqual(record['metrics'], {'accuracy': 1.0})

    def test_invalid_eval_mode(self):
        with self.assertRaises(AssertionError):
            self.evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='invalid')

    def test_empty_data_evaluation(self):
        self.benchmark.get_test_data.return_value = []
        results = self.evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='test')
        self.assertEqual(results, {})
        self.assertEqual(len(self.evaluator.get_all_evaluation_records()), 0)

def test_invalid_eval_mode(self):
    with self.assertRaises(AssertionError):
        self.evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='invalid')

class TestModule(unittest.TestCase):

    def test_agent_manager(self):
        OPENAI_API_KEY = 'xxxxx'
        llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
        agent = Agent(name='Bob', description='Bob is an engineer. He excels in writing and reviewing codes for different projects.', system_prompt='You are an excellent engineer and you can solve diverse coding tasks.', llm_config=llm_config, actions=[{'name': 'WriteFileToDisk', 'description': 'save several files to local storage.', 'tools': [{'name': 'FileToolKit', 'tools': [{'name': 'WriteFile', 'description': 'Write file to disk', 'inputs': {}}]}]}])
        agent_manager = AgentManager()
        agent_manager.add_agents(agents=[agent, {'class_name': 'Agent', 'name': 'test_agent', 'description': 'test_agent_description', 'llm_config': llm_config}])
        self.assertEqual(agent_manager.size, 2)
        self.assertTrue(agent_manager.has_agent(agent_name='Bob'))
        num_agents = agent_manager.size
        agent_manager.add_agents(agents=[agent])
        self.assertEqual(agent_manager.size, num_agents)
        self.assertTrue(isinstance(agent_manager.get_agent('test_agent'), Agent))
        self.assertEqual(agent_manager.size, 2)
        agent_manager.add_agent({'name': 'custom_agent', 'description': 'custom_agent_desc', 'prompt': 'customize prompt', 'is_human': True})
        self.assertEqual(agent_manager.size, 3)
        self.assertTrue(isinstance(agent_manager.get_agent('custom_agent'), CustomizeAgent))
        agent_manager.remove_agent(agent_name='test_agent')
        self.assertEqual(agent_manager.size, 2)
        self.assertTrue(agent_manager.has_agent('Bob'))
        self.assertTrue(agent_manager.has_agent('custom_agent'))
        self.assertEqual(agent_manager.get_agent_state('Bob'), AgentState.AVAILABLE)
        agent_manager.set_agent_state(agent_name='Bob', new_state=AgentState.RUNNING)
        self.assertEqual(agent_manager.get_agent_state('Bob'), AgentState.RUNNING)
        agent_manager.clear_agents()
        self.assertEqual(agent_manager.size, 0)

def test_agent_manager(self):
    OPENAI_API_KEY = 'xxxxx'
    llm_config = LiteLLMConfig(model='gpt-4o-mini', openai_key=OPENAI_API_KEY)
    agent = Agent(name='Bob', description='Bob is an engineer. He excels in writing and reviewing codes for different projects.', system_prompt='You are an excellent engineer and you can solve diverse coding tasks.', llm_config=llm_config, actions=[{'name': 'WriteFileToDisk', 'description': 'save several files to local storage.', 'tools': [{'name': 'FileToolKit', 'tools': [{'name': 'WriteFile', 'description': 'Write file to disk', 'inputs': {}}]}]}])
    agent_manager = AgentManager()
    agent_manager.add_agents(agents=[agent, {'class_name': 'Agent', 'name': 'test_agent', 'description': 'test_agent_description', 'llm_config': llm_config}])
    self.assertEqual(agent_manager.size, 2)
    self.assertTrue(agent_manager.has_agent(agent_name='Bob'))
    num_agents = agent_manager.size
    agent_manager.add_agents(agents=[agent])
    self.assertEqual(agent_manager.size, num_agents)
    self.assertTrue(isinstance(agent_manager.get_agent('test_agent'), Agent))
    self.assertEqual(agent_manager.size, 2)
    agent_manager.add_agent({'name': 'custom_agent', 'description': 'custom_agent_desc', 'prompt': 'customize prompt', 'is_human': True})
    self.assertEqual(agent_manager.size, 3)
    self.assertTrue(isinstance(agent_manager.get_agent('custom_agent'), CustomizeAgent))
    agent_manager.remove_agent(agent_name='test_agent')
    self.assertEqual(agent_manager.size, 2)
    self.assertTrue(agent_manager.has_agent('Bob'))
    self.assertTrue(agent_manager.has_agent('custom_agent'))
    self.assertEqual(agent_manager.get_agent_state('Bob'), AgentState.AVAILABLE)
    agent_manager.set_agent_state(agent_name='Bob', new_state=AgentState.RUNNING)
    self.assertEqual(agent_manager.get_agent_state('Bob'), AgentState.RUNNING)
    agent_manager.clear_agents()
    self.assertEqual(agent_manager.size, 0)

class TestStorageHandler(unittest.TestCase):
    """
    Test suite for StorageHandler's database operations on Workflow, Agent, and History.
    Uses an in-memory SQLite database for isolated testing.
    """

    def setUp(self):
        """
        Set up the test environment by initializing StorageHandler with an in-memory SQLite database.
        """
        db_config = DBConfig(db_name='sqlite', path=':memory:')
        store_config = StoreConfig(dbConfig=db_config)
        self.storage = StorageHandler(storageConfig=store_config)
        self.agent_data = {'name': 'test_agent', 'content': {'role': 'assistant', 'settings': {'active': True}}, 'date': '2025-05-13'}
        self.workflow_data = {'name': 'test_workflow', 'content': {'class_name': 'WorkFlowGraph', 'goal': 'Generate html code for the Tetris game that can be played in the browser.', 'nodes': [{'class_name': 'WorkFlowNode', 'name': 'game_structure_design', 'description': "Create an outline of the Tetris game's structure, including the main game area, score display, and control buttons.", 'inputs': [{'class_name': 'Parameter', 'name': 'goal', 'type': 'string', 'description': "The user's goal in textual format.", 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure outlining the game area, score display, and buttons.', 'required': True}], 'reason': 'This sub-task establishes the foundational layout required for a functional Tetris game in HTML.', 'agents': [{'name': 'tetris_game_structure_agent', 'description': "This agent creates the basic HTML structure for the Tetris game, including the game area, score display, and control buttons based on the user's goal.", 'inputs': [{'name': 'goal', 'type': 'string', 'description': "The user's goal in textual format.", 'required': True}], 'outputs': [{'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure outlining the game area, score display, and buttons.', 'required': True}], 'prompt': "### Objective\nCreate the basic HTML structure for a Tetris game, incorporating the main game area, score display, and control buttons based on the user's goal.\n\n### Instructions\n1. Read the user's goal: <input>{goal}</input>\n2. Design the main game area where the Tetris pieces will fall.\n3. Create an element to display the current score.\n4. Include buttons to control the game (e.g., start, pause, reset).\n5. Assemble these elements into a coherent HTML structure that can be utilized in a web environment.\n6. Output the generated HTML structure.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for creating the HTML structure of the Tetris game.\n\n## html_structure\nThe basic HTML structure outlining the game area, score display, and buttons."}], 'status': 'pending'}, {'class_name': 'WorkFlowNode', 'name': 'style_application', 'description': 'Add CSS styles to the HTML structure for visual aesthetics and layout to make the game look visually appealing.', 'inputs': [{'class_name': 'Parameter', 'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure of the Tetris game.', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code that includes CSS for the Tetris game.', 'required': True}], 'reason': 'Styling is essential for enhancing the user experience and ensuring the game is visually organized and engaging.', 'agents': [{'name': 'css_style_application_agent', 'description': 'This agent applies CSS styles to the given HTML structure to create a visually appealing layout for the Tetris game.', 'inputs': [{'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure of the Tetris game.', 'required': True}], 'outputs': [{'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code that includes CSS for the Tetris game.', 'required': True}], 'prompt': '### Objective\nEnhance the provided HTML structure by applying CSS styles to create a visually appealing layout for the Tetris game.\n\n### Instructions\n1. Begin with the provided HTML structure: <input>{html_structure}</input>\n2. Analyze the elements in the HTML to decide the appropriate CSS styles that will enhance its appearance.\n3. Write CSS styles that cater to visual aesthetics such as colors, fonts, borders, and spacing.\n4. Integrate the CSS styles into the HTML structure properly.\n5. Ensure the output is a well-formatted HTML document that includes the applied CSS styles.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for achieving the objective.\n\n## styled_game\nThe styled HTML code that includes CSS for the Tetris game.'}], 'status': 'pending'}, {'class_name': 'WorkFlowNode', 'name': 'game_logic_implementation', 'description': 'Implement the JavaScript logic for the Tetris game, including piece movement, collision detection, and score tracking.', 'inputs': [{'class_name': 'Parameter', 'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code for the Tetris game.', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for a functional Tetris game.', 'required': True}], 'reason': 'This sub-task is crucial for making the game interactive and functional, allowing users to play.', 'agents': [{'name': 'tetris_logic_agent', 'description': 'This agent implements the JavaScript logic required for the Tetris game, ensuring piece movements, collision detection, and score tracking functionalities are properly integrated.', 'inputs': [{'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code for the Tetris game.', 'required': True}], 'outputs': [{'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for a functional Tetris game.', 'required': True}], 'prompt': "### Objective\nImplement the JavaScript logic for the Tetris game, ensuring functionalities for piece movement, collision detection, and score tracking are included in the output.\n\n### Instructions\n1. Analyze the styled HTML code provided: <input>{styled_game}</input>\n2. Develop JavaScript functions that handle the movement of Tetris pieces, including left, right, and rotation controls.\n3. Implement collision detection logic to ensure pieces do not fall through the bottom or collide with existing pieces.\n4. Create a scoring system that tracks the player's progress and updates the score based on cleared lines.\n5. Combine the JavaScript logic with the existing styled HTML to create a complete game code output.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for implementing the game logic for Tetris.\n\n## complete_game_code\nThe completed HTML, CSS, and JavaScript code for a functional Tetris game."}], 'status': 'pending'}, {'class_name': 'WorkFlowNode', 'name': 'testing_and_refinement', 'description': 'Test the generated Tetris game for bugs and usability issues, refining the code as necessary.', 'inputs': [{'class_name': 'Parameter', 'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for the Tetris game.', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'final_output', 'type': 'string', 'description': 'The final tested and refined code for the Tetris game.', 'required': True}], 'reason': 'Testing is vital to ensure that the game functions correctly across different browsers and provides a smooth user experience.', 'agents': [{'name': 'tetris_game_testing_agent', 'description': 'This agent tests the generated Tetris game code for functionality, identifies bugs, and provides refinements as needed to ensure smooth gameplay and usability.', 'inputs': [{'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for the Tetris game.', 'required': True}], 'outputs': [{'name': 'final_output', 'type': 'string', 'description': 'The final tested and refined code for the Tetris game.', 'required': True}], 'prompt': '### Objective\nTest the complete Tetris game code for bugs and usability issues, and refine the code as necessary for improved performance.\n\n### Instructions\n1. Load the complete game code: <input>{complete_game_code}</input> into a browser.\n2. Test the game functionality, focusing on user controls, collision detection, and game progression.\n3. Identify any bugs or usability issues that arise during testing.\n4. Document the identified issues and make necessary adjustments to the code to resolve them.\n5. Ensure that the final code adheres to best practices for HTML, CSS, and JavaScript.\n6. Output the refined and tested code as the final result.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for testing and refining the Tetris game code.\n\n## final_output\nThe final tested and refined code for the Tetris game.'}], 'status': 'pending'}], 'edges': [{'class_name': 'WorkFlowEdge', 'source': 'game_structure_design', 'target': 'style_application', 'priority': 0}, {'class_name': 'WorkFlowEdge', 'source': 'style_application', 'target': 'game_logic_implementation', 'priority': 0}, {'class_name': 'WorkFlowEdge', 'source': 'game_logic_implementation', 'target': 'testing_and_refinement', 'priority': 0}], 'graph': None}, 'date': '2025-05-13'}
        self.history_data = {'memory_id': 'mem_001', 'old_memory': 'Initial content', 'new_memory': 'Updated content', 'event': 'update', 'created_at': '2025-05-13T09:00:00', 'updated_at': '2025-05-13T09:30:00'}

    def test_save_and_load_agent(self):
        """
        Test saving and loading an agent, verifying data integrity and JSON parsing.
        """
        self.storage.save_agent(self.agent_data)
        self.storage.save_agent(self.agent_data, 'nihao')
        loaded = self.storage.load_agent('test_agent')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'test_agent')
        self.assertEqual(loaded['content'], self.agent_data['content'])
        self.assertEqual(loaded['date'], '2025-05-13')

    def test_save_and_load_workflow(self):
        """
        Test saving and loading a workflow, verifying data integrity and JSON parsing.
        """
        self.storage.save_workflow(self.workflow_data)
        loaded = self.storage.load_workflow('test_workflow')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'test_workflow')
        self.assertEqual(loaded['content'], self.workflow_data['content'])
        self.assertEqual(loaded['date'], '2025-05-13')

    def test_save_and_load_history(self):
        """
        Test saving and loading a history entry, verifying data integrity.
        """
        self.storage.save_history(self.history_data)
        loaded = self.storage.load_history('mem_001')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['memory_id'], 'mem_001')
        self.assertEqual(loaded['old_memory'], 'Initial content')
        self.assertEqual(loaded['new_memory'], 'Updated content')
        self.assertEqual(loaded['event'], 'update')
        self.assertEqual(loaded['created_at'], '2025-05-13T09:00:00')
        self.assertEqual(loaded['updated_at'], '2025-05-13T09:30:00')

    def test_load_non_existent_agent(self):
        """
        Test loading a non-existent agent returns None.
        """
        loaded = self.storage.load_agent('non_existent_agent')
        self.assertIsNone(loaded)

    def test_load_non_existent_workflow(self):
        """
        Test loading a non-existent workflow returns None.
        """
        loaded = self.storage.load_workflow('non_existent_workflow')
        self.assertIsNone(loaded)

    def test_load_non_existent_history(self):
        """
        Test loading a non-existent history entry returns None.
        """
        loaded = self.storage.load_history('non_existent_mem')
        self.assertIsNone(loaded)

    def test_save_invalid_agent(self):
        """
        Test saving an agent without a 'name' field raises ValueError.
        """
        invalid_data = {'content': {'role': 'assistant'}, 'date': '2025-05-13'}
        with self.assertRaises(ValueError):
            self.storage.save_agent(invalid_data)

    def test_save_invalid_workflow(self):
        """
        Test saving a workflow without a 'name' field raises ValueError.
        """
        invalid_data = {'content': {'steps': ['step1']}, 'date': '2025-05-13'}
        with self.assertRaises(ValueError):
            self.storage.save_workflow(invalid_data)

    def test_save_invalid_history(self):
        """
        Test saving a history entry without a 'memory_id' field raises ValueError.
        """
        invalid_data = {'old_memory': 'Initial', 'new_memory': 'Updated', 'event': 'update'}
        with self.assertRaises(ValueError):
            self.storage.save_history(invalid_data)

    def test_remove_agent(self):
        """
        Test removing an agent and verify it's no longer loadable.
        """
        self.storage.save_agent(self.agent_data)
        self.storage.remove_agent('test_agent')
        loaded = self.storage.load_agent('test_agent')
        self.assertIsNone(loaded)

    def test_remove_non_existent_agent(self):
        """
        Test removing a non-existent agent raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.storage.remove_agent('non_existent_agent')

    def test_update_agent(self):
        """
        Test updating an existing agent's data.
        """
        self.storage.save_agent(self.agent_data)
        updated_data = {'name': 'test_agent', 'content': {'role': 'admin', 'settings': {'active': False}}, 'date': '2025-05-14'}
        self.storage.save_agent(updated_data)
        loaded = self.storage.load_agent('test_agent')
        self.assertEqual(loaded['content'], updated_data['content'])
        self.assertEqual(loaded['date'], '2025-05-14')

    def test_update_workflow(self):
        """
        Test updating an existing workflow's data.
        """
        self.storage.save_workflow(self.workflow_data)
        updated_data = {'name': 'test_workflow', 'content': {'test': True}, 'date': '2025-05-15'}
        self.storage.save_workflow(updated_data)
        loaded = self.storage.load_workflow('test_workflow')
        self.assertEqual(loaded['content'], updated_data['content'])
        self.assertEqual(loaded['date'], '2025-05-15')

    def test_update_history(self):
        """
        Test updating an existing history entry.
        """
        self.storage.save_history(self.history_data)
        updated_data = {'memory_id': 'mem_001', 'old_memory': 'Initial content', 'new_memory': 'Further updated content', 'event': 'modify', 'created_at': '2025-05-13T09:00:00', 'updated_at': '2025-05-13T10:00:00'}
        self.storage.save_history(updated_data)
        loaded = self.storage.load_history('mem_001')
        self.assertEqual(loaded['new_memory'], 'Further updated content')
        self.assertEqual(loaded['event'], 'modify')
        self.assertEqual(loaded['updated_at'], '2025-05-13T10:00:00')

    def test_bulk_save_and_load(self):
        """
        Test saving multiple records to all tables and loading them.
        """
        agent_data2 = {'name': 'test_agent2', 'content': {'role': 'user', 'settings': {'active': True}}, 'date': '2025-05-13'}
        workflow_data2 = {'name': 'test_workflow2', 'content': {'steps': ['stepA', 'stepB'], 'config': {'timeout': 45}}, 'date': '2025-05-13'}
        history_data2 = {'memory_id': 'mem_002', 'old_memory': 'Old content', 'new_memory': 'New content', 'event': 'create', 'created_at': '2025-05-13T10:00:00', 'updated_at': '2025-05-13T10:00:00'}
        bulk_data = {TableType.store_agent.value: [self.agent_data, agent_data2], TableType.store_workflow.value: [self.workflow_data, workflow_data2], TableType.store_history.value: [self.history_data, history_data2]}
        self.storage.save(bulk_data)
        all_data = self.storage.load()
        self.assertIn(TableType.store_agent.value, all_data)
        self.assertIn(TableType.store_workflow.value, all_data)
        self.assertIn(TableType.store_history.value, all_data)
        self.assertEqual(len(all_data[TableType.store_agent.value]), 2)
        self.assertEqual(len(all_data[TableType.store_workflow.value]), 2)
        self.assertEqual(len(all_data[TableType.store_history.value]), 2)
        agent_names = [record['name'] for record in all_data[TableType.store_agent.value]]
        self.assertIn('test_agent', agent_names)
        self.assertIn('test_agent2', agent_names)
        workflow_names = [record['name'] for record in all_data[TableType.store_workflow.value]]
        self.assertIn('test_workflow', workflow_names)
        self.assertIn('test_workflow2', workflow_names)
        history_ids = [record['memory_id'] for record in all_data[TableType.store_history.value]]
        self.assertIn('mem_001', history_ids)
        self.assertIn('mem_002', history_ids)

    def test_save_invalid_table(self):
        """
        Test saving data to an unknown table raises ValueError.
        """
        invalid_data = {'unknown_table': [self.agent_data]}
        with self.assertRaises(ValueError):
            self.storage.save(invalid_data)

    def tearDown(self):
        """
        Clean up by closing the database connection.
        """
        self.storage.storageDB.connection.close()

def test_save_and_load_agent(self):
    """
        Test saving and loading an agent, verifying data integrity and JSON parsing.
        """
    self.storage.save_agent(self.agent_data)
    self.storage.save_agent(self.agent_data, 'nihao')
    loaded = self.storage.load_agent('test_agent')
    self.assertIsNotNone(loaded)
    self.assertEqual(loaded['name'], 'test_agent')
    self.assertEqual(loaded['content'], self.agent_data['content'])
    self.assertEqual(loaded['date'], '2025-05-13')

def test_save_and_load_workflow(self):
    """
        Test saving and loading a workflow, verifying data integrity and JSON parsing.
        """
    self.storage.save_workflow(self.workflow_data)
    loaded = self.storage.load_workflow('test_workflow')
    self.assertIsNotNone(loaded)
    self.assertEqual(loaded['name'], 'test_workflow')
    self.assertEqual(loaded['content'], self.workflow_data['content'])
    self.assertEqual(loaded['date'], '2025-05-13')

def test_save_and_load_history(self):
    """
        Test saving and loading a history entry, verifying data integrity.
        """
    self.storage.save_history(self.history_data)
    loaded = self.storage.load_history('mem_001')
    self.assertIsNotNone(loaded)
    self.assertEqual(loaded['memory_id'], 'mem_001')
    self.assertEqual(loaded['old_memory'], 'Initial content')
    self.assertEqual(loaded['new_memory'], 'Updated content')
    self.assertEqual(loaded['event'], 'update')
    self.assertEqual(loaded['created_at'], '2025-05-13T09:00:00')
    self.assertEqual(loaded['updated_at'], '2025-05-13T09:30:00')

def test_load_non_existent_agent(self):
    """
        Test loading a non-existent agent returns None.
        """
    loaded = self.storage.load_agent('non_existent_agent')
    self.assertIsNone(loaded)

def test_load_non_existent_workflow(self):
    """
        Test loading a non-existent workflow returns None.
        """
    loaded = self.storage.load_workflow('non_existent_workflow')
    self.assertIsNone(loaded)

def test_load_non_existent_history(self):
    """
        Test loading a non-existent history entry returns None.
        """
    loaded = self.storage.load_history('non_existent_mem')
    self.assertIsNone(loaded)

def test_save_invalid_agent(self):
    """
        Test saving an agent without a 'name' field raises ValueError.
        """
    invalid_data = {'content': {'role': 'assistant'}, 'date': '2025-05-13'}
    with self.assertRaises(ValueError):
        self.storage.save_agent(invalid_data)

def test_save_invalid_workflow(self):
    """
        Test saving a workflow without a 'name' field raises ValueError.
        """
    invalid_data = {'content': {'steps': ['step1']}, 'date': '2025-05-13'}
    with self.assertRaises(ValueError):
        self.storage.save_workflow(invalid_data)

def test_save_invalid_history(self):
    """
        Test saving a history entry without a 'memory_id' field raises ValueError.
        """
    invalid_data = {'old_memory': 'Initial', 'new_memory': 'Updated', 'event': 'update'}
    with self.assertRaises(ValueError):
        self.storage.save_history(invalid_data)

def test_remove_agent(self):
    """
        Test removing an agent and verify it's no longer loadable.
        """
    self.storage.save_agent(self.agent_data)
    self.storage.remove_agent('test_agent')
    loaded = self.storage.load_agent('test_agent')
    self.assertIsNone(loaded)

def test_remove_non_existent_agent(self):
    """
        Test removing a non-existent agent raises ValueError.
        """
    with self.assertRaises(ValueError):
        self.storage.remove_agent('non_existent_agent')

def test_update_agent(self):
    """
        Test updating an existing agent's data.
        """
    self.storage.save_agent(self.agent_data)
    updated_data = {'name': 'test_agent', 'content': {'role': 'admin', 'settings': {'active': False}}, 'date': '2025-05-14'}
    self.storage.save_agent(updated_data)
    loaded = self.storage.load_agent('test_agent')
    self.assertEqual(loaded['content'], updated_data['content'])
    self.assertEqual(loaded['date'], '2025-05-14')

def test_update_workflow(self):
    """
        Test updating an existing workflow's data.
        """
    self.storage.save_workflow(self.workflow_data)
    updated_data = {'name': 'test_workflow', 'content': {'test': True}, 'date': '2025-05-15'}
    self.storage.save_workflow(updated_data)
    loaded = self.storage.load_workflow('test_workflow')
    self.assertEqual(loaded['content'], updated_data['content'])
    self.assertEqual(loaded['date'], '2025-05-15')

def test_update_history(self):
    """
        Test updating an existing history entry.
        """
    self.storage.save_history(self.history_data)
    updated_data = {'memory_id': 'mem_001', 'old_memory': 'Initial content', 'new_memory': 'Further updated content', 'event': 'modify', 'created_at': '2025-05-13T09:00:00', 'updated_at': '2025-05-13T10:00:00'}
    self.storage.save_history(updated_data)
    loaded = self.storage.load_history('mem_001')
    self.assertEqual(loaded['new_memory'], 'Further updated content')
    self.assertEqual(loaded['event'], 'modify')
    self.assertEqual(loaded['updated_at'], '2025-05-13T10:00:00')

def test_save_invalid_table(self):
    """
        Test saving data to an unknown table raises ValueError.
        """
    invalid_data = {'unknown_table': [self.agent_data]}
    with self.assertRaises(ValueError):
        self.storage.save(invalid_data)

