# Cluster 13

class ActionAgent(Agent):
    """
    ActionAgent is a specialized agent that executes a provided function directly without LLM.
    It creates an action that uses the provided function as the execution backbone.
    
    Attributes:
        name (str): The name of the agent.
        description (str): A description of the agent's purpose and capabilities.
        inputs (List[dict]): List of input specifications, where each dict contains:
            - name (str): Name of the input parameter
            - type (str): Type of the input
            - description (str): Description of what the input represents
            - required (bool, optional): Whether this input is required (default: True)
        outputs (List[dict]): List of output specifications, where each dict contains:
            - name (str): Name of the output field
            - type (str): Type of the output
            - description (str): Description of what the output represents
            - required (bool, optional): Whether this output is required (default: True)
        execute_func (Callable): The function to execute the agent.
        async_execute_func (Callable, Optional): Async version of the function. If not provided,
            an async wrapper will be automatically created around execute_func.
        llm_config (LLMConfig, optional): Configuration for the language model (minimal usage).
    """

    def __init__(self, name: str, description: str, inputs: List[dict], outputs: List[dict], execute_func: Callable, async_execute_func: Optional[Callable]=None, llm_config: Optional[LLMConfig]=None, **kwargs):
        if not callable(execute_func):
            raise ValueError('execute_func must be callable')
        if async_execute_func is not None and (not callable(async_execute_func)):
            raise ValueError('async_execute_func must be callable')
        self._validate_inputs_outputs(inputs, outputs)
        is_human = llm_config is None
        super().__init__(name=name, description=description, llm_config=llm_config, is_human=is_human, **kwargs)
        self.execute_func = execute_func
        self.async_execute_func = async_execute_func
        self.inputs = inputs
        self.outputs = outputs
        action = self._create_function_action_with_params(name, execute_func, async_execute_func, inputs, outputs)
        self.add_action(action)

    def init_llm(self):
        pass

    def _validate_inputs_outputs(self, inputs: List[dict], outputs: List[dict]):
        """Validate the structure of inputs and outputs."""
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        for i, input_field in enumerate(inputs):
            if not isinstance(input_field, dict):
                raise ValueError(f'Input field {i} must be a dictionary, got {type(input_field)}')
            required_keys = ['name', 'type', 'description']
            for key in required_keys:
                if key not in input_field:
                    raise ValueError(f"Input field {i} missing required key '{key}'")
            if not isinstance(input_field['name'], str):
                raise ValueError(f"Input field {i} 'name' must be a string, got {type(input_field['name'])}")
            if not isinstance(input_field['type'], str):
                raise ValueError(f"Input field {i} 'type' must be a string, got {type(input_field['type'])}")
            if not isinstance(input_field['description'], str):
                raise ValueError(f"Input field {i} 'description' must be a string, got {type(input_field['description'])}")
            input_names = [field['name'] for field in inputs]
            if len(input_names) != len(set(input_names)):
                raise ValueError(f'Duplicate input names found: {[name for name in input_names if input_names.count(name) > 1]}')
        for i, output_field in enumerate(outputs):
            if not isinstance(output_field, dict):
                raise ValueError(f'Output field {i} must be a dictionary, got {type(output_field)}')
            required_keys = ['name', 'type', 'description']
            for key in required_keys:
                if key not in output_field:
                    raise ValueError(f"Output field {i} missing required key '{key}'")
            if not isinstance(output_field['name'], str):
                raise ValueError(f"Output field {i} 'name' must be a string, got {type(output_field['name'])}")
            if not isinstance(output_field['type'], str):
                raise ValueError(f"Output field {i} 'type' must be a string, got {type(output_field['type'])}")
            if not isinstance(output_field['description'], str):
                raise ValueError(f"Output field {i} 'description' must be a string, got {type(output_field['description'])}")
            output_names = [field['name'] for field in outputs]
            if len(output_names) != len(set(output_names)):
                raise ValueError(f'Duplicate output names found: {[name for name in output_names if output_names.count(name) > 1]}')

    def _create_function_action_input_type(self, name: str, inputs: List[dict]) -> Type[ActionInput]:
        """Create ActionInput type from input specifications."""
        action_input_fields = {}
        for field in inputs:
            required = field.get('required', True)
            if required:
                action_input_fields[field['name']] = (str, Field(description=field['description']))
            else:
                action_input_fields[field['name']] = (Optional[str], Field(default=None, description=field['description']))
        action_input_type = create_model(self._get_unique_class_name(generate_dynamic_class_name(f'{name} action_input')), **action_input_fields, __base__=ActionInput)
        return action_input_type

    def _create_function_action_output_type(self, name: str, outputs: List[dict]) -> Type[ActionOutput]:
        """Create ActionOutput type from output specifications."""
        action_output_fields = {}
        for field in outputs:
            required = field.get('required', True)
            if required:
                action_output_fields[field['name']] = (Any, Field(description=field['description']))
            else:
                action_output_fields[field['name']] = (Optional[Any], Field(default=None, description=field['description']))
        action_output_type = create_model(self._get_unique_class_name(generate_dynamic_class_name(f'{name} action_output')), **action_output_fields, __base__=ActionOutput)
        return action_output_type

    def _create_execute_method(self, execute_func: Callable):
        """Create the execute method for the action."""

        def execute_method(action_self, llm=None, inputs=None, sys_msg=None, return_prompt=False, **kwargs):
            if inputs is None:
                inputs = {}
            required_inputs = action_self.inputs_format.get_required_input_names()
            missing_inputs = [input_name for input_name in required_inputs if input_name not in inputs]
            if missing_inputs:
                raise ValueError(f'Missing required inputs: {missing_inputs}')
            filtered_inputs = {}
            for input_name, input_value in inputs.items():
                if input_name in [field['name'] for field in self.inputs]:
                    filtered_inputs[input_name] = input_value
                else:
                    logger.warning(f"Unexpected input '{input_name}' provided")
            try:
                result = execute_func(**filtered_inputs)
            except Exception as e:
                try:
                    output_fields = action_self.outputs_format.get_attrs()
                    if 'error' in output_fields:
                        error_output = action_self.outputs_format(error=f'Function execution failed: {str(e)}')
                    elif len(output_fields) > 0:
                        first_field = output_fields[0]
                        error_output = action_self.outputs_format(**{first_field: f'Error: {str(e)}'})
                    else:
                        error_output = action_self.outputs_format()
                except Exception as create_error:
                    logger.error(f'Failed to create error output: {create_error}')
                    error_output = action_self.outputs_format()
                return (error_output, 'Function execution')
            if isinstance(result, dict):
                output = action_self.outputs_format(**result)
            else:
                output_fields = action_self.outputs_format.get_attrs()
                if len(output_fields) > 0:
                    first_field = output_fields[0]
                    output = action_self.outputs_format(**{first_field: result})
                else:
                    output = action_self.outputs_format()
            return (output, 'Function execution')
        return execute_method

    def _create_async_execute_method(self, async_execute_func: Callable, execute_func: Callable):
        """Create the async execute method for the action."""

        async def async_execute_method(action_self, llm=None, inputs=None, sys_msg=None, return_prompt=False, **kwargs):
            if inputs is None:
                inputs = {}
            required_inputs = action_self.inputs_format.get_required_input_names()
            missing_inputs = [input_name for input_name in required_inputs if input_name not in inputs]
            if missing_inputs:
                raise ValueError(f'Missing required inputs: {missing_inputs}')
            filtered_inputs = {}
            for input_name, input_value in inputs.items():
                if input_name in [field['name'] for field in self.inputs]:
                    filtered_inputs[input_name] = input_value
                else:
                    logger.warning(f"Unexpected input '{input_name}' provided")
            try:
                if async_execute_func is not None:
                    result = await async_execute_func(**filtered_inputs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: execute_func(**filtered_inputs))
            except Exception as e:
                try:
                    output_fields = action_self.outputs_format.get_attrs()
                    if 'error' in output_fields:
                        error_output = action_self.outputs_format(error=f'Async function execution failed: {str(e)}')
                    elif len(output_fields) > 0:
                        first_field = list(output_fields.keys())[0]
                        error_output = action_self.outputs_format(**{first_field: f'Error: {str(e)}'})
                    else:
                        error_output = action_self.outputs_format()
                except Exception as create_error:
                    logger.error(f'Failed to create error output: {create_error}')
                    error_output = action_self.outputs_format()
                return (error_output, 'Async function execution')
            if isinstance(result, dict):
                output = action_self.outputs_format(**result)
            else:
                output_fields = action_self.outputs_format.get_attrs()
                if len(output_fields) > 0:
                    first_field = output_fields[0]
                    output = action_self.outputs_format(**{first_field: result})
                else:
                    output = action_self.outputs_format()
            return (output, 'Async function execution')
        return async_execute_method

    def _create_function_action_with_params(self, name: str, execute_func: Callable, async_execute_func: Callable, inputs: List[dict], outputs: List[dict]) -> Action:
        """Create an action that executes the provided function with given parameters."""
        action_input_type = self._create_function_action_input_type(name, inputs)
        action_output_type = self._create_function_action_output_type(name, outputs)
        action_cls_name = self._get_unique_class_name(generate_dynamic_class_name(f'{name} function action'))
        function_action_cls = create_model(action_cls_name, __base__=Action)
        function_action = function_action_cls(name=action_cls_name, description=f'Executes {execute_func.__name__} function', inputs_format=action_input_type, outputs_format=action_output_type)
        execute_method = self._create_execute_method(execute_func)
        async_execute_method = self._create_async_execute_method(async_execute_func, execute_func)
        function_action.execute = execute_method.__get__(function_action, type(function_action))
        function_action.async_execute = async_execute_method.__get__(function_action, type(function_action))
        return function_action

    def _create_function_action(self, name: str, execute_func: Callable, async_execute_func: Callable, inputs: List[dict], outputs: List[dict]) -> Action:
        """Create an action that executes the provided function."""
        return self._create_function_action_with_params(name, execute_func, async_execute_func, inputs, outputs)

    def get_config(self) -> dict:
        """Get configuration for the ActionAgent."""
        config = super().get_config()
        config.update({'class_name': 'ActionAgent', 'execute_func_name': self.execute_func.__name__ if self.execute_func else None, 'async_execute_func_name': self.async_execute_func.__name__ if self.async_execute_func else None, 'inputs': self.inputs, 'outputs': self.outputs})
        return config

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """Save the ActionAgent configuration to a JSON file.
        
        Args:
            path: File path where the configuration should be saved
            ignore: List of keys to exclude from the saved configuration
            **kwargs (Any): Additional parameters for the save operation
            
        Returns:
            The path where the configuration was saved
        """
        config = self.get_config()
        config.update({'class_name': 'ActionAgent', 'execute_func_name': self.execute_func.__name__ if self.execute_func else None, 'async_execute_func_name': self.async_execute_func.__name__ if self.async_execute_func else None, 'inputs': self.inputs, 'outputs': self.outputs})
        for ignore_key in ignore:
            config.pop(ignore_key, None)
        make_parent_folder(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return path

    @classmethod
    def load_module(cls, path: str, llm_config: LLMConfig=None, **kwargs) -> 'ActionAgent':
        """Load the ActionAgent from a JSON file.
        
        Args:
            path: The path of the file
            llm_config: The LLMConfig instance (optional)
            **kwargs: Additional keyword arguments
            
        Returns:
            ActionAgent: The loaded agent instance
            
        Raises:
            KeyError: If required functions are not found in the registry
        """
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        execute_func_name = config.get('execute_func_name')
        async_execute_func_name = config.get('async_execute_func_name')
        execute_func = None
        async_execute_func = None
        if execute_func_name:
            if not ACTION_FUNCTION_REGISTRY.has_function(execute_func_name):
                raise KeyError(f"Function '{execute_func_name}' not found in registry. Please register it first.")
            execute_func = ACTION_FUNCTION_REGISTRY.get_function(execute_func_name)
        if async_execute_func_name:
            if not ACTION_FUNCTION_REGISTRY.has_function(async_execute_func_name):
                raise KeyError(f"Function '{async_execute_func_name}' not found in registry. Please register it first.")
            async_execute_func = ACTION_FUNCTION_REGISTRY.get_function(async_execute_func_name)
        agent = cls(name=config['name'], description=config['description'], inputs=config['inputs'], outputs=config['outputs'], execute_func=execute_func, async_execute_func=async_execute_func, llm_config=llm_config, **kwargs)
        return agent

    def __call__(self, inputs: dict=None, return_msg_type: MessageType=MessageType.UNKNOWN, **kwargs) -> Message:
        """
        Call the main function action.

        Args:
            inputs (dict): The inputs to the function action.
            return_msg_type (MessageType): The type of message to return.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            Message: The output of the function action.
        """
        inputs = inputs or {}
        return super().__call__(action_name=self.main_action_name, action_input_data=inputs, return_msg_type=return_msg_type, **kwargs)

    @property
    def main_action_name(self) -> str:
        """
        Get the name of the main function action for this agent.
        
        Returns:
            The name of the main function action
        """
        for action in self.actions:
            if action.name != self.cext_action_name:
                return action.name
        raise ValueError("Couldn't find the main action name!")

    def _get_unique_class_name(self, candidate_name: str) -> str:
        """
        Get a unique class name by checking if it already exists in the registry.
        If it does, append "Vx" to make it unique.
        """
        if not MODULE_REGISTRY.has_module(candidate_name):
            return candidate_name
        counter = 1
        while True:
            new_name = f'{candidate_name}V{counter}'
            if not MODULE_REGISTRY.has_module(new_name):
                return new_name
            counter += 1

def get_config(self) -> dict:
    """Get configuration for the ActionAgent."""
    config = super().get_config()
    config.update({'class_name': 'ActionAgent', 'execute_func_name': self.execute_func.__name__ if self.execute_func else None, 'async_execute_func_name': self.async_execute_func.__name__ if self.async_execute_func else None, 'inputs': self.inputs, 'outputs': self.outputs})
    return config

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

class WorkFlowNode(BaseModule):
    """
    Represents a node in a workflow graph.
    
    A workflow node represents a specific task in the workflow with its
    inputs, outputs, and execution metadata. It can have associated agents
    that execute the task and track its execution status.
    
    Attributes:
        name: A unique identifier for the task within a workflow
        description: Detailed description of what the task does
        inputs: List of input parameters required by the task
        outputs: List of output parameters produced by the task
        reason: Optional justification for this task's existence
        agents: Optional list of agents that can execute this task
        action_graph: Optional graph of actions to execute this task
        status: Current execution state of the task
    """
    name: str
    description: str
    inputs: List[Parameter]
    outputs: List[Parameter]
    reason: Optional[str] = None
    agents: Optional[List[Union[str, dict]]] = None
    action_graph: Optional[ActionGraph] = None
    status: Optional[WorkFlowNodeState] = WorkFlowNodeState.PENDING

    @field_validator('agents', mode='before')
    @classmethod
    def check_agent_format(cls, agents: List[Union[str, dict, Agent]]):
        if agents is None:
            return None
        validated_agents = []
        for agent in agents:
            if isinstance(agent, str):
                validated_agents.append(agent)
            elif isinstance(agent, Agent):
                validated_agents.append(agent.get_config())
            elif isinstance(agent, dict):
                assert 'name' in agent and 'description' in agent, 'must provide the name and description of an agent when specifying an agent with a dict.'
                validated_agents.append(agent)
        return validated_agents

    @model_validator(mode='after')
    @classmethod
    def check_action_graph(cls, instance: 'WorkFlowNode'):
        """
        Validates that:
        1. All required parameters of execute/async_execute methods are included in inputs
        2. The execute/async_execute methods return dictionaries
        3. All output parameters are present in the returned dictionaries
        """
        if instance.action_graph is None:
            return instance
        input_param_names = {param.name for param in instance.inputs if param.required}
        output_param_names = {param.name for param in instance.outputs if param.required}

        def check_method_signature(method, method_name):
            """Helper function to check method signature against input parameters"""
            method_source = inspect.getsource(method)
            if 'NotImplementedError' in method_source:
                return
            method_sig = inspect.signature(method)
            required_params = []
            for name, param in method_sig.parameters.items():
                if name != 'self' and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    if param.default == param.empty:
                        required_params.append(name)
            missing_inputs = set(required_params) - input_param_names
            if missing_inputs:
                raise ValueError(f'`{method_name}` method requires parameters that are not in `inputs`: {missing_inputs}')
        check_method_signature(instance.action_graph.execute, 'execute')
        check_method_signature(instance.action_graph.async_execute, 'async_execute')
        original_execute = instance.action_graph.execute
        original_async_execute = instance.action_graph.async_execute

        def check_method_return(method_name, result):
            if not isinstance(result, dict):
                raise TypeError(f'{method_name} must return a dictionary, got {type(result)}')
            missing_outputs = output_param_names - set(result.keys())
            if missing_outputs:
                raise ValueError(f'{method_name} return value is missing required outputs: {missing_outputs}')
            return result

        @wraps(original_execute)
        def patched_execute(*args, **kwargs):
            result = original_execute(*args, **kwargs)
            return check_method_return('execute', result)

        @wraps(original_async_execute)
        async def patched_async_execute(*args, **kwargs):
            result = await original_async_execute(*args, **kwargs)
            return check_method_return('async_execute', result)
        instance.action_graph.execute = patched_execute
        instance.action_graph.async_execute = patched_async_execute
        return instance

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
        for agent in data.get('agents', []):
            if isinstance(agent, dict) and 'parse_func' in agent and isinstance(agent['parse_func'], Callable):
                agent['parse_func'] = agent['parse_func'].__name__
        return data

    def get_agents(self) -> List[str]:
        """
        Return the names of all agents associated with this node.
        """
        agent_names = []
        if not self.agents:
            return []
        for agent in self.agents:
            if isinstance(agent, str):
                agent_names.append(agent)
            elif isinstance(agent, dict):
                agent_names.append(agent['name'])
            else:
                raise TypeError(f'{type(agent)} is an unknown agent type!')
        return agent_names

    def set_agents(self, agents: List[Union[str, dict]]):
        self.agents = agents

    def get_status(self) -> WorkFlowNodeState:
        return self.status

    def set_status(self, state: WorkFlowNodeState):
        self.status = state

    @property
    def is_complete(self) -> bool:
        return self.status == WorkFlowNodeState.COMPLETED

    def get_task_info(self) -> str:

        def format_parameters(params: List[Parameter]) -> str:
            if not params:
                return 'None'
            return '\n'.join((f'  - {param.name} ({param.type}): {param.description}' for param in params))
        desc = f'Name: {self.name}\nDescription: {self.description}\nInputs:\n{format_parameters(self.inputs)}\nOutputs:\n{format_parameters(self.outputs)}\n'
        return desc

    def get_input_names(self, required: bool=False) -> List[str]:
        if required:
            return [param.name for param in self.inputs if param.required]
        else:
            return [param.name for param in self.inputs]

    def get_output_names(self, required: bool=False) -> List[str]:
        if required:
            return [param.name for param in self.outputs if param.required]
        else:
            return [param.name for param in self.outputs]

@field_validator('agents', mode='before')
@classmethod
def check_agent_format(cls, agents: List[Union[str, dict, Agent]]):
    if agents is None:
        return None
    validated_agents = []
    for agent in agents:
        if isinstance(agent, str):
            validated_agents.append(agent)
        elif isinstance(agent, Agent):
            validated_agents.append(agent.get_config())
        elif isinstance(agent, dict):
            assert 'name' in agent and 'description' in agent, 'must provide the name and description of an agent when specifying an agent with a dict.'
            validated_agents.append(agent)
    return validated_agents

class WorkFlowGraph(BaseModule):
    """
    Represents a complete workflow as a directed graph.
    
    WorkFlowGraph models a workflow as a directed graph where nodes represent tasks
    and edges represent dependencies and data flow between tasks. It provides
    methods for constructing, validating, traversing, and executing workflows.
    
    The graph structure supports advanced features like detecting and handling loops,
    determining execution order, and tracking execution state.
    
    Attributes:
        goal: The high-level objective of this workflow
        nodes: List of WorkFlowNode instances representing tasks
        edges: List of WorkFlowEdge instances representing dependencies
        graph: Internal NetworkX MultiDiGraph or another WorkFlowGraph
    """
    goal: str
    nodes: Optional[List[WorkFlowNode]] = []
    edges: Optional[List[WorkFlowEdge]] = []
    graph: Optional[Union[MultiDiGraph, 'WorkFlowGraph']] = Field(default=None, exclude=True)

    def init_module(self):
        self._lock = threading.Lock()
        if not self.graph:
            self._init_from_nodes_and_edges(self.nodes, self.edges)
        elif isinstance(self.graph, MultiDiGraph):
            self._init_from_multidigraph(self.graph, self.nodes, self.edges)
        elif isinstance(self.graph, WorkFlowGraph):
            self._init_from_workflowgraph(self.graph, self.nodes, self.edges)
        else:
            raise TypeError(f'{type(self.graph)} is an unknown type for graph. Supported types: [MultiDiGraph, WorkFlowGraph]')
        self._validate_workflow_structure()
        self.update_graph()

    def update_graph(self):
        self._loops = self._find_all_loops()

    def _init_from_nodes_and_edges(self, nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
        """
        Initialize the WorkFlowGraph from a set of nodes and edges. 
        """
        if edges and (not nodes):
            raise ValueError('edges cannot be passed without nodes or a graph')
        self.nodes = []
        self.edges = []
        self.graph = MultiDiGraph()
        self.add_nodes(*nodes, update_graph=False)
        self.add_edges(*edges, update_graph=False)

    def _init_from_multidigraph(self, graph: MultiDiGraph, nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
        graph_nodes = [deepcopy(node_attrs['ref']) for _, node_attrs in graph.nodes(data=True)]
        graph_edges = [deepcopy(edge_attrs['ref']) for *_, edge_attrs in graph.edges(data=True)]
        graph_nodes = self.merge_nodes(graph_nodes, nodes)
        graph_edges = self.merge_edges(graph_edges, edges)
        self._init_from_nodes_and_edges(nodes=graph_nodes, edges=graph_edges)

    def _init_from_workflowgraph(self, graph: 'WorkFlowGraph', nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
        graph_nodes = deepcopy(graph.nodes)
        graph_edges = deepcopy(graph.edges)
        graph_nodes = self.merge_nodes(graph_nodes, nodes)
        graph_edges = self.merge_edges(graph_edges, edges)
        self._init_from_nodes_and_edges(nodes=graph_nodes, edges=graph_edges)

    def _validate_workflow_structure(self):
        isolated_nodes = list(nx.isolates(self.graph))
        if len(self.graph.nodes) > 1 and isolated_nodes:
            logger.warning(f'The workflow contains isolated nodes: {isolated_nodes}')
        initial_nodes = self.find_initial_nodes()
        if len(self.graph.nodes) > 1 and (not initial_nodes):
            error_message = 'There are no initial nodes in the workflow!'
            logger.error(error_message)
            raise ValueError(error_message)
        end_nodes = self.find_end_nodes()
        if len(self.graph.nodes) > 1 and (not end_nodes):
            logger.warning('There are no end nodes in the workflow')

    def find_initial_nodes(self) -> List[str]:
        initial_nodes = [node for node, in_degree in self.graph.in_degree() if in_degree == 0]
        return initial_nodes

    def find_end_nodes(self) -> List[str]:
        end_nodes = [node for node, out_degree in self.graph.out_degree() if out_degree == 0]
        return end_nodes

    def _find_loops(self, start_node: Union[str, WorkFlowNode]) -> Dict[str, list]:
        if isinstance(start_node, str):
            start_node = self.get_node(node_name=start_node)
        start_node_name = start_node.name
        loops = defaultdict(list)

        def dfs(current_node_name: str, path: List[str]):
            if current_node_name in path:
                loops[current_node_name].append(path[path.index(current_node_name):])
                return
            path.append(current_node_name)
            children = self.get_node_children(current_node_name)
            if children:
                for child in children:
                    dfs(child, path)
            path.pop()
        dfs(start_node_name, [])
        return loops

    def _find_all_loops(self) -> Dict[str, list]:
        initial_nodes = self.find_initial_nodes()
        if not initial_nodes:
            return {}

        def contain_loop(loops: List[List[str]], new_loop: List[str]):
            if not loops:
                return False
            return frozenset(new_loop) in [frozenset(loop) for loop in loops]
        all_loops = defaultdict(list)
        for initial_node in initial_nodes:
            loops_from_init_node = self._find_loops(initial_node)
            for start_node, loops in loops_from_init_node.items():
                for loop in loops:
                    if not contain_loop(all_loops[start_node], loop):
                        all_loops[start_node].append(loop)
        if len(all_loops) <= 1:
            return all_loops
        loop_to_start_nodes = defaultdict(dict)
        for start_node, loops in all_loops.items():
            for loop in loops:
                normalized_loop = frozenset(loop)
                loop_to_start_nodes[normalized_loop][start_node] = loop
        all_paths: List[List[str]] = []
        for initial_node in initial_nodes:
            all_paths.extend(self.get_all_paths_from_node(initial_node))

        def rank_nodes(nodes: List[str]):
            if len(nodes) == 1:
                return nodes[0]
            path_contain_nodes = None
            for path in all_paths:
                if all((node in path for node in nodes)):
                    path_contain_nodes = path
                    break
            if path_contain_nodes is None:
                raise ValueError(f"Couldn't find a path that contain nodes: {nodes}")
            node_indices = [path.index(node) for node in nodes]
            return nodes[node_indices.index(min(node_indices))]
        all_loops = defaultdict(list)
        for start_node_loop in loop_to_start_nodes.values():
            first_node = rank_nodes(list(start_node_loop.keys()))
            all_loops[first_node].append(start_node_loop[first_node])
        return all_loops

    def add_node(self, node: WorkFlowNode, update_graph: bool=True, **kwargs):
        if not isinstance(node, WorkFlowNode):
            raise ValueError(f'{node} is not a valid WorkFlowNode instance!')
        if self.node_exists(node.name):
            raise ValueError(f'Duplicate node names are not allowed! Found duplicate node name: {node.name}')
        self.nodes.append(node)
        self.graph.add_node(node.name, ref=node)
        if update_graph:
            self.update_graph()

    def add_edge(self, edge: WorkFlowEdge, update_graph: bool=True, **kwargs):
        if not isinstance(edge, WorkFlowEdge):
            raise ValueError(f'{edge} is not a valid WorkFlowEdge instance!')
        for attr, node_name in zip(['source', 'target'], [edge.source, edge.target]):
            if not self.node_exists(node_name):
                raise ValueError(f'{attr} node {node_name} does not exists!')
        if self.edge_exists(edge):
            raise ValueError(f'Duplicate edges are not allowed! Found duplicate edges: {edge}')
        source_node = self.get_node(edge.source)
        target_node = self.get_node(edge.target)
        source_output_names = set((param.name for param in source_node.outputs))
        target_input_names = set((param.name for param in target_node.inputs))
        if len(source_output_names & target_input_names) == 0:
            logger.warning(f'The edge ({edge.source}, {edge.target}) has no matching inputs and outputs! You may need to check the inputs and outputs of the nodes to ensure that at least one input of the target node is the output of the source node.')
        self.edges.append(edge)
        self.graph.add_edge(edge.source, edge.target, ref=edge)
        if update_graph:
            self.update_graph()

    def add_nodes(self, *nodes: WorkFlowNode, update_graph: bool=True, **kwargs):
        nodes: list = list(nodes)
        nodes.extend([kwargs.pop(var) for var in ['node', 'nodes'] if var in kwargs])
        for node in nodes:
            if isinstance(node, (tuple, list)):
                for n in node:
                    self.add_node(n, update_graph=update_graph, **kwargs)
            else:
                self.add_node(node, update_graph=update_graph, **kwargs)

    def add_edges(self, *edges: WorkFlowEdge, update_graph: bool=True, **kwargs):
        edges: list = list(edges)
        edges.extend([kwargs.pop(var) for var in ['edge', 'edges'] if var in kwargs])
        for edge in edges:
            if isinstance(edge, (tuple, list)):
                for e in edge:
                    self.add_edge(e, update_graph=update_graph, **kwargs)
            else:
                self.add_edge(edge, update_graph=update_graph, **kwargs)

    def node_exists(self, node: Union[str, WorkFlowNode]) -> bool:
        if isinstance(node, str):
            return node in self.graph.nodes
        elif isinstance(node, WorkFlowNode):
            return node.name in self.graph.nodes
        else:
            raise TypeError('node must be a str or WorkFlowNode instance')

    def _edge_exists(self, source: str, target: str, **attr_filters) -> bool:
        if not self.graph.has_edge(source, target):
            return False
        if attr_filters:
            for key, value in attr_filters.items():
                if key not in self.graph[source][target] or self.graph[source][target][key] != value:
                    return False
        return True

    def edge_exists(self, edge: Union[Tuple[str, str], WorkFlowEdge], **attr_filters) -> bool:
        """
        Check whether an edge exists in the workflow graph. The input `edge` can either be a tuple or a WorkFlowEdge instance.

        1. If a tuple is passed, it should be (source, target). The function will only determin whether there is an edge between the source node and the target node. 
        If attr_filters is passed, they will also be used to match the edge attributes. 
        2. If a WorkFlowEdge is passed, it will use the __eq__ method in WorkFlowEdge to determine 

        Parameters:
        ----------
            edge (Union[Tuple[str, str], WorkFlowEdge]):
                - If a tuple is provided, it should be in the format `(source, target)`. 
                The method will check whether there is an edge between the source and target nodes.
                If `attr_filters` are provided, they will be used to match edge attributes.
                - If a WorkFlowEdge instance is provided, the method will use the `__eq__` method in WorkFlowEdge 
                to determine whether the edge exists.

            attr_filters (dict, optional):
                Additional attributes to filter edges when `edge` is a tuple.

        Returns:
        -------
            bool: True if the edge exists and matches the filters (if provided); False otherwise.
        """
        if isinstance(edge, tuple):
            assert len(edge) == 2, 'edge must be a tuple (source, target) or WorkFlowEdge instance'
            source, target = edge
            return self._edge_exists(source, target, **attr_filters)
        elif isinstance(edge, WorkFlowEdge):
            return edge in self.edges
        else:
            raise TypeError('edge must be a tuple (source, target) or WorkFlowEdge instance')

    def is_loop_start(self, node: Union[str, WorkFlowNode]) -> bool:
        if len(self._loops) == 0:
            return False
        node_name = node if isinstance(node, str) else node.name
        return node_name in self._loops

    def is_loop_end(self, node: Union[str, WorkFlowNode]) -> bool:
        if len(self._loops) == 0:
            return False
        loop_end_nodes = set()
        node_name = node if isinstance(node, str) else node.name
        for loops in self._loops.values():
            loop_end_nodes.update([loop[-1] for loop in loops])
        return node_name in loop_end_nodes

    def find_loops_with_start_and_end(self, start_node: Union[str, WorkFlowNode], end_node: Union[str, WorkFlowNode]) -> List[List[str]]:
        if len(self._loops) == 0:
            return []
        start_node_name = start_node if isinstance(start_node, str) else start_node.name
        end_node_name = end_node if isinstance(end_node, str) else end_node.name
        if start_node_name not in self._loops:
            return []
        target = []
        for loop in self._loops[start_node_name]:
            if loop[-1] == end_node_name:
                target.append(loop)
        return target

    def merge_nodes(self, nodes: List[WorkFlowNode], new_nodes: List[WorkFlowNode]):
        node_names = {node.name for node in nodes}
        for node in new_nodes:
            if node.name in node_names:
                continue
            nodes.append(node)
        return nodes

    def merge_edges(self, edges: List[WorkFlowEdge], new_edges: List[WorkFlowEdge]):
        for edge in new_edges:
            if edge in edges:
                continue
            edges.append(edge)
        return edges

    def list_nodes(self) -> List[str]:
        """
        return the names of all nodes 
        """
        return [node.name for node in self.nodes]

    def get_node(self, node_name: str) -> WorkFlowNode:
        """
        return a WorkFlowNode instance based on its name.
        """
        if not self.node_exists(node=node_name):
            raise KeyError(f'{node_name} is an invalid node name. Currently available node names: {self.list_nodes()}')
        return self.graph.nodes[node_name]['ref']

    def get_node_status(self, node: Union[str, WorkFlowNode]) -> WorkFlowNodeState:
        if isinstance(node, str):
            node = self.get_node(node_name=node)
        return node.get_status()

    @property
    def is_complete(self):
        leaf_nodes = [self.get_node(name) for name in self.find_end_nodes()]
        node_complete_list = [node.is_complete for node in leaf_nodes]
        if len(node_complete_list) == 0:
            return True
        if all(node_complete_list):
            return True
        return False

    def reset_graph(self):
        """
        set the status of all nodes to pending
        """
        for node in self.nodes:
            node.set_status(WorkFlowNodeState.PENDING)

    def set_node_status(self, node: Union[str, WorkFlowNode], new_state: WorkFlowNodeState) -> bool:
        """
        Update the state of a specific node. 

        Args:
            node (Union[str, WorkFlowNode]): The name of a node or the node instance.
            new_state (WorkFlowNodeState): The new state to set.
        
        Returns:
            bool: True if the state was updated successfully, False otherwise.
        """
        flag = False
        try:
            if isinstance(node, str):
                node = self.get_node(node_name=node)
            node.set_status(new_state)
            flag = True
        except Exception as e:
            raise ValueError(f'An error occurs when setting node status: {e}')
        return flag

    def pending(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.PENDING)

    def running(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.RUNNING)

    def completed(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.COMPLETED)

    def failed(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.FAILED)

    def get_node_children(self, node: Union[str, WorkFlowNode]) -> List[str]:
        node_name = node if isinstance(node, str) else node.name
        if not self.node_exists(node=node):
            raise ValueError(f'Node `{node_name}` does not exists!')
        children = list(self.graph.successors(node_name))
        return children

    def get_node_predecessors(self, node: Union[str, WorkFlowNode]) -> List[str]:
        node_name = node if isinstance(node, str) else node.name
        if not self.node_exists(node=node):
            raise ValueError(f'Node `{node_name}` does not exists!')
        predecessors = list(self.graph.predecessors(node_name))
        return predecessors

    def get_uncomplete_initial_nodes(self) -> List[str]:
        initial_nodes = self.find_initial_nodes()
        are_initial_nodes_complete = [self.get_node(node_name).is_complete for node_name in initial_nodes]
        uncomplete_initial_nodes = []
        for node_name, is_complete in zip(initial_nodes, are_initial_nodes_complete):
            if not is_complete:
                uncomplete_initial_nodes.append(node_name)
        return uncomplete_initial_nodes

    def get_all_paths_from_node(self, start_node: Union[str, WorkFlowNode]) -> List[List[str]]:
        if isinstance(start_node, str):
            start_node = self.get_node(node_name=start_node)
        start_node_name = start_node.name
        all_paths = []
        visited = set()

        def dfs(current_node_name: str, path: List[str]):
            if current_node_name in visited:
                if path and len(self.get_node_children(path[-1])) == 1:
                    all_paths.append(path.copy())
                return
            path.append(current_node_name)
            visited.add(current_node_name)
            children = self.get_node_children(current_node_name)
            if not children:
                all_paths.append(path.copy())
            else:
                for child in children:
                    dfs(child, path)
            path.pop()
            visited.remove(current_node_name)
        dfs(start_node_name, [])
        return all_paths

    def find_completed_leaf_nodes(self, start_node: Union[str, WorkFlowNode]) -> List[str]:
        if isinstance(start_node, str):
            start_node = self.get_node(node_name=start_node)
        start_node_name = start_node.name
        paths_starting_from_node = self.get_all_paths_from_node(start_node=start_node_name)
        last_completed_nodes = []
        for path in paths_starting_from_node:
            if not path:
                continue
            completed_node = None
            for path_node in path:
                if self.get_node(path_node).is_complete:
                    completed_node = path_node
                else:
                    break
            if completed_node and completed_node not in last_completed_nodes:
                last_completed_nodes.append(completed_node)
        last_completed_nodes = last_completed_nodes[::-1]
        return last_completed_nodes

    def find_completed_leaf_nodes_start_from_initial_nodes(self) -> List[str]:
        initial_nodes = self.find_initial_nodes()
        completed_leaf_nodes = []
        for initial_node in initial_nodes:
            for complete_node in self.find_completed_leaf_nodes(start_node=initial_node):
                if complete_node not in completed_leaf_nodes:
                    completed_leaf_nodes.append(complete_node)
        return completed_leaf_nodes

    def get_all_children_nodes(self, nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        node_names = [node if isinstance(node, str) else node.name for node in nodes]
        children_nodes = []
        for node_name in node_names:
            for child in self.get_node_children(node_name):
                if child not in children_nodes:
                    children_nodes.append(child)
        return children_nodes

    def filter_completed_nodes(self, nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        """
        remove completed nodes from `nodes`
        """
        node_names = [node if isinstance(node, str) else node.name for node in nodes]
        uncompleted_nodes = []
        for node_name in node_names:
            if self.get_node(node_name).is_complete:
                continue
            uncompleted_nodes.append(node_name)
        return uncompleted_nodes

    def get_candidate_children_nodes(self, completed_nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        """
        Return the next set of possible tasks to execute. If there are no loops in the graph, consider only the uncompleted children. 
        If there exists loops, also consider the previous completed tasks.

        Args:
            completed_nodes (List[Union[str, WorkFlowNode]]): A list of completed nodes.
            
        Returns:
            List[str]: List of node names that are candidates for execution.
        """
        node_names = [node if isinstance(node, str) else node.name for node in completed_nodes]
        has_loop = len(self._loops) > 0
        if has_loop:
            uncompleted_children_nodes = []
            for node_name in node_names:
                children_nodes = self.get_all_children_nodes(nodes=[node_name])
                if self.is_loop_end(node=node_name):
                    current_uncompleted_children_nodes = []
                    for child in children_nodes:
                        if self.is_loop_start(node=child):
                            current_uncompleted_children_nodes.append(child)
                        else:
                            current_uncompleted_children_nodes.extend(self.filter_completed_nodes(nodes=[child]))
                else:
                    current_uncompleted_children_nodes = self.filter_completed_nodes(nodes=children_nodes)
                for child in current_uncompleted_children_nodes:
                    if child not in uncompleted_children_nodes:
                        uncompleted_children_nodes.append(child)
        else:
            children_nodes = self.get_all_children_nodes(nodes=node_names)
            uncompleted_children_nodes = self.filter_completed_nodes(nodes=children_nodes)
        return uncompleted_children_nodes

    def are_dependencies_complete(self, node_name: str) -> bool:
        """
        Check if all predecessors for a node are complete.

        Args:
            node_name (str): The name of the task/node to check.
        
        Returns:
            bool: True if all predecessors are complete, False otherwise.
        """
        has_loop = len(self._loops) > 0
        predecessors = self.get_node_predecessors(node=node_name)
        if has_loop and self.is_loop_start(node=node_name):
            flag = True
            for pre in predecessors:
                if self.is_loop_end(pre):
                    pass
                else:
                    flag &= self.get_node(pre).is_complete
        else:
            flag = all((self.get_node(pre).is_complete for pre in predecessors))
        return flag

    def filter_nodes_with_uncompleted_predecessors(self, nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        node_names = [node if isinstance(node, str) else node.name for node in nodes]
        nodes_with_completed_predecessors = []
        for node_name in node_names:
            if self.are_dependencies_complete(node_name=node_name):
                nodes_with_completed_predecessors.append(node_name)
        return nodes_with_completed_predecessors

    def get_next_candidate_nodes(self) -> List[str]:
        uncomplete_initial_nodes = self.get_uncomplete_initial_nodes()
        if len(uncomplete_initial_nodes) > 0:
            return uncomplete_initial_nodes
        completed_leaf_nodes = self.find_completed_leaf_nodes_start_from_initial_nodes()
        candidate_children_nodes = self.get_candidate_children_nodes(completed_nodes=completed_leaf_nodes)
        children_nodes_with_complete_predecessors = self.filter_nodes_with_uncompleted_predecessors(candidate_children_nodes)
        return children_nodes_with_complete_predecessors

    def next(self) -> List[WorkFlowNode]:
        if self.is_complete:
            return []
        candidate_node_names = self.get_next_candidate_nodes()
        candidate_tasks = [self.get_node(node_name=node_name) for node_name in candidate_node_names]
        return candidate_tasks

    def step(self, source_node: Union[str, WorkFlowNode], target_node: Union[str, WorkFlowNode]):
        if source_node is None:
            self.running(target_node)
            return
        source_node_name = source_node if isinstance(source_node, str) else source_node.name
        target_node_name = target_node if isinstance(target_node, str) else target_node.name
        source_node_status = self.get_node_status(source_node_name)
        if source_node_status != WorkFlowNodeState.COMPLETED:
            raise ValueError(f'The state of `source_node` should be WorkFlowNodeState.COMPLETED, but found {source_node_status}')
        if self.is_loop_end(source_node_name) and self.is_loop_start(target_node_name):
            loops = self.find_loops_with_start_and_end(start_node=target_node_name, end_node=source_node_name)
            loop_nodes = set(sum(loops, []))
            for loop_node in loop_nodes:
                self.pending(node=loop_node)
        if not self.edge_exists(edge=(source_node_name, target_node_name)):
            all_paths = self.get_all_paths_from_node(start_node=target_node_name)
            for path in all_paths:
                if source_node_name in path:
                    for node_name in path:
                        self.pending(node=node_name)
        self.running(node=target_node_name)

    def get_node_description(self, node: Union[str, WorkFlowNode]) -> str:
        if isinstance(node, str):
            node = self.get_node(node_name=node)

        def format_parameters(params: List[Parameter]) -> str:
            if not params:
                return '  - None'
            return '\n'.join((f'  - {param.name} ({param.type})' for param in params))

        def format_agents(agent_names: List[str]) -> str:
            if not agent_names:
                return 'None'
            return '\n'.join((f'  - {name}' for name in agent_names))

        def format_action_graph(action_graph: ActionGraph) -> str:
            if action_graph is None:
                return '  - None'
            return type(action_graph).__name__
        desc = f'Name: {node.name}\nInputs:\n{format_parameters(node.inputs)}\nOutputs:\n{format_parameters(node.outputs)}\nAgents:\n{format_agents(node.get_agents())}\nAction Graph:\n{format_action_graph(node.action_graph)}'
        return desc

    def display(self):
        """
        Display the workflow graph with node and edge attributes.
        Nodes are colored based on their status.
        """
        import matplotlib.pyplot as plt
        status_colors = {WorkFlowNodeState.PENDING: 'lightgray', WorkFlowNodeState.RUNNING: 'orange', WorkFlowNodeState.COMPLETED: 'green', WorkFlowNodeState.FAILED: 'red'}
        if not self.graph.nodes:
            print('Graph is empty. No nodes to display.')
            return
        node_colors = [status_colors.get(self.get_node_status(node), 'lightgray') for node in self.graph.nodes]
        node_labels = {node: self.get_node_description(data['ref']) for node, data in self.graph.nodes(data=True)}
        if len(self.graph.nodes) == 1:
            single_node = list(self.graph.nodes)[0]
            pos = {single_node: (0, 0)}
        else:
            pos = nx.shell_layout(self.graph)
        plt.figure(figsize=(12, 8))
        nx.draw(self.graph, pos, with_labels=False, node_color=node_colors, edge_color='black', node_size=1500, font_size=8, font_color='black', font_weight='bold')
        if len(self.graph.nodes) == 1:
            for node, (x, y) in pos.items():
                plt.text(x + 0.005, y, node_labels[node], ha='left', va='center', fontsize=9, bbox=dict(facecolor='white', alpha=0.7))
        else:
            y_positions = [y for _, y in pos.values()]
            y_min, y_max = (min(y_positions), max(y_positions))
            lower_third_boundary = y_min + (y_max - y_min) / 3
            text_offsets = {}
            for node, (x, y) in pos.items():
                if y < lower_third_boundary:
                    text_offsets[node] = (x - 0.2, y + 0.23)
                else:
                    text_offsets[node] = (x - 0.2, y - 0.23)
            for node, (x, y) in text_offsets.items():
                plt.text(x, y, node_labels[node], ha='left', va='center', fontsize=9, bbox=dict(facecolor='white', alpha=0.7))
        edge_labels = nx.get_edge_attributes(self.graph, 'priority')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', label=status.name, markersize=10, markerfacecolor=color) for status, color in status_colors.items()]
        plt.legend(handles=legend_elements, title='Workflow Node Status', loc='upper left', fontsize='medium')
        plt.title('Workflow Graph')
        plt.show()

    def get_workflow_description(self) -> str:

        def format_param_requirement(required: bool):
            return 'required' if required else 'optional'

        def format_parameters(params: List[Parameter]) -> str:
            if not params:
                return 'None'
            return '\n'.join((f'  - {param.name} ({param.type}, {format_param_requirement(param.required)}): {param.description}' for param in params))
        subtask_texts = []
        for node in self.nodes:
            text = f'Task Name: {node.name}\nDescription: {node.description}\nInputs:\n{format_parameters(node.inputs)}\nOutputs:\n{format_parameters(node.outputs)}'
            subtask_texts.append(text)
        workflow_desc = '\n\n'.join(subtask_texts)
        return workflow_desc

    def _infer_edges_from_nodes(self, nodes: List[WorkFlowNode]) -> List[WorkFlowEdge]:
        if not nodes:
            return []
        edges: List[WorkFlowEdge] = []
        for node in nodes:
            for another_node in nodes:
                if node.name == another_node.name:
                    continue
                node_output_params = [param.name for param in node.outputs]
                another_node_input_params = [param.name for param in another_node.inputs]
                if any([param in another_node_input_params for param in node_output_params]):
                    edges.append(WorkFlowEdge(edge_tuple=(node.name, another_node.name)))
        return edges

    def get_config(self) -> dict:
        """
        Get a dictionary containing all necessary configuration to recreate this workflow graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new WorkFlowGraph instance
            with the same properties as this one.
        """
        config = self.to_dict()
        config.pop('graph', None)
        return config

def _init_from_multidigraph(self, graph: MultiDiGraph, nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
    graph_nodes = [deepcopy(node_attrs['ref']) for _, node_attrs in graph.nodes(data=True)]
    graph_edges = [deepcopy(edge_attrs['ref']) for *_, edge_attrs in graph.edges(data=True)]
    graph_nodes = self.merge_nodes(graph_nodes, nodes)
    graph_edges = self.merge_edges(graph_edges, edges)
    self._init_from_nodes_and_edges(nodes=graph_nodes, edges=graph_edges)

def _init_from_workflowgraph(self, graph: 'WorkFlowGraph', nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
    graph_nodes = deepcopy(graph.nodes)
    graph_edges = deepcopy(graph.edges)
    graph_nodes = self.merge_nodes(graph_nodes, nodes)
    graph_edges = self.merge_edges(graph_edges, edges)
    self._init_from_nodes_and_edges(nodes=graph_nodes, edges=graph_edges)

class PromptTemplate(BaseModule):
    instruction: str = Field(description='The instruction that the LLM will follow.')
    context: Optional[str] = Field(default=None, description='Additional context that can help the LLM understand the instruction.')
    constraints: Optional[Union[List[str], str]] = Field(default=None, description='Constraints that the LLM must follow.')
    tools: Optional[List[Toolkit]] = Field(default=None, description='Tools that the LLM can use.')
    demonstrations: Optional[List[dict]] = Field(default=None, description='Examples of how to use the instruction.')
    history: Optional[List[Any]] = Field(default=None, description='History of the conversation between the user and the LLM.')

    def get_field_names(self) -> List[str]:
        return [name for name, _ in type(self).model_fields.items() if name != 'class_name']

    def get(self, key: str) -> Any:
        fields = self.get_field_names()
        if key not in fields:
            raise ValueError(f'Invalid key `{key}` for `{self.__class__.__name__}`. Valid keys are: {fields}')
        return getattr(self, key)

    def set(self, key: str, value: Any):
        fields = self.get_field_names()
        if key not in fields:
            raise ValueError(f'Invalid key `{key}` for `{self.__class__.__name__}`. Valid keys are: {fields}')
        setattr(self, key, value)

    def get_instruction(self) -> str:
        return self.instruction

    def get_demonstrations(self) -> List[Any]:
        return self.demonstrations

    def get_context(self) -> Optional[str]:
        return self.context

    def get_history(self) -> Optional[List[Any]]:
        return self.history

    def get_constraints(self) -> Optional[Union[List[str], str]]:
        return self.constraints

    def get_tools(self) -> Optional[List[str]]:
        return self.tools

    def set_instruction(self, instruction: str):
        self.set('instruction', instruction)

    def set_demonstrations(self, demonstrations: List[Any]):
        self.set('demonstrations', demonstrations)

    def set_context(self, context: str):
        self.set('context', context)

    def set_history(self, history: List[Any]):
        self.set('history', history)

    def set_constraints(self, constraints: Union[List[str], str]):
        self.set('constraints', constraints)

    def set_tools(self, tools: List[Toolkit]):
        self.set('tools', tools)

    def get_required_inputs_or_outputs(self, format: Type[LLMOutputParser]) -> List[str]:
        """
        Get the required fields of the format.
        """
        required_fields = []
        attrs = format.get_attrs()
        for field_name, field_info in format.model_fields.items():
            if field_name not in attrs:
                continue
            field_default = field_info.default
            if field_default is PydanticUndefined:
                required_fields.append(field_name)
        return required_fields

    def clear_placeholders(self, text: str) -> str:
        """
        Find all {xx} placeholders in the text, and replace them with `xx`,
        adding backticks only if not already present.
        """
        matches = set(regex.findall('(?<!\\{)\\{([^\\{\\},\\s]+)\\}(?!\\})', text))
        for field in matches:
            pattern = '(?<!\\{)\\{' + regex.escape(field) + '\\}(?!\\})'

            def replacer(match):
                start, end = (match.start(), match.end())
                before = text[start - 1] if start > 0 else ''
                after = text[end] if end < len(text) else ''
                replacement = field
                if before != '`':
                    replacement = '`' + replacement
                if after != '`':
                    replacement = replacement + '`'
                return replacement
            text = regex.sub(pattern, replacer, text)
        return text

    def check_required_inputs(self, inputs_format: Type[LLMOutputParser], values: dict):
        if inputs_format is None:
            return
        required_inputs = self.get_required_inputs_or_outputs(inputs_format)
        missing_required_inputs = [field for field in required_inputs if field not in values]
        if missing_required_inputs:
            logger.warning(f'Missing required inputs (without default values) for `{inputs_format.__name__}`: {missing_required_inputs}, will set them to empty strings.')

    def render_input_example(self, inputs_format: Type[LLMOutputParser], values: dict, missing_field_value: str='') -> str:
        if inputs_format is None and values is None:
            return ''
        if inputs_format is not None:
            fields = inputs_format.get_attrs()
            field_values = {field: values.get(field, missing_field_value) for field in fields}
        else:
            field_values = values
        return '\n'.join((f'[[ **{field}** ]]:\n{value}' for field, value in field_values.items()))

    def get_output_template(self, outputs_format: Type[LLMOutputParser], parse_mode: str='title', title_format: str='## {title}') -> str:
        if outputs_format is None:
            raise ValueError('`outputs_format` is required in `get_output_format`.')
        valid_modes = ['json', 'xml', 'title']
        if parse_mode not in valid_modes:
            raise ValueError(f'Invalid parse mode `{parse_mode}` for `{self.__class__.__name__}.get_output_template`. Valid modes are: {valid_modes}.')
        fields = outputs_format.get_attrs()
        required_fields = self.get_required_inputs_or_outputs(outputs_format)
        if parse_mode == 'json':
            json_template = '{{\n'
            for field in fields:
                json_template += f'    "{field}"'
                json_template += f': "{{{field}}}",\n' if field in required_fields else f' (Optional): "{{{field}}}",\n'
            json_template = json_template.rstrip(',\n') + '\n}}'
            output_template, output_keys = (json_template, fields)
        elif parse_mode == 'xml':
            xml_template = ''
            for field in fields:
                xml_template += f'<{field}>\n' if field in required_fields else f'<{field}> (Optional)\n'
                xml_template += f'{{{field}}}\n</{field}>\n'
            xml_template = xml_template.rstrip('\n')
            output_template, output_keys = (xml_template, fields)
        elif parse_mode == 'title':
            title_template = ''
            for field in fields:
                title_section = title_format.format(title=field)
                title_section += '\n' if field in required_fields else ' (Optional)\n'
                title_section += f'{{{field}}}\n\n'
                title_template += title_section
            title_template = title_template.rstrip('\n')
            output_template, output_keys = (title_template, fields)
        return (output_template, output_keys)

    def render_instruction(self) -> str:
        instruction_str = self.clear_placeholders(self.instruction)
        return f'### Instruction\nThis is the main task instruction you must follow:\n{instruction_str}\n'

    def render_context(self) -> str:
        if not self.context:
            return ''
        return f'### Context\nHere is some additional background information to help you understand the task:\n{self.context}\n'

    def render_tools(self) -> str:
        if not self.tools:
            return ''
        tools_schemas = [tool.get_tool_schemas() for tool in self.tools]
        tools_schemas = [j for i in tools_schemas for j in i]
        return TOOL_CALLING_TEMPLATE.format(tools_description=tools_schemas)

    def render_constraints(self) -> str:
        if not self.constraints:
            return ''
        if isinstance(self.constraints, list):
            constraints_str = '\n'.join((f'- {c}' for c in self.constraints))
        else:
            constraints_str = self.constraints
        return f'### Constraints\nYou must follow these rules or constraints when generating your output:\n{constraints_str}\n'

    def _render_system_message(self, system_prompt: Optional[str]=None) -> str:
        """
        Render the system message by combining system prompt, instruction, context, tools and constraints.
        """
        prompt_pieces = []
        if system_prompt:
            prompt_pieces.append(system_prompt + '\n')
        prompt_pieces.append(self.render_instruction())
        if self.context:
            prompt_pieces.append(self.render_context())
        if self.tools:
            prompt_pieces.append(self.render_tools())
        if self.constraints:
            prompt_pieces.append(self.render_constraints())
        return '\n'.join(prompt_pieces)

    def render_outputs(self, outputs_format: Type[LLMOutputParser], parse_mode: str='title', title_format: str='## {title}') -> str:
        if outputs_format is None or parse_mode in [None, 'str', 'custom'] or len(outputs_format.get_attrs()) == 0:
            return '### Outputs Format\nPlease generate a response that best fits the task instruction.\n'
        ouptut_template, output_keys = self.get_output_template(outputs_format, parse_mode=parse_mode, title_format=title_format)
        output_str = '### Outputs Format\nYou MUST strictly follow the following format when generating your output:\n\n'
        if parse_mode == 'json':
            output_str += 'Format your output in json format, such as:\n'
        elif parse_mode == 'xml':
            output_str += 'Format your output in xml format, such as:\n'
        elif parse_mode == 'title':
            output_str += 'Format your output in sectioned title format, such as:\n'
        example_values = {}
        for key in output_keys:
            field_info = outputs_format.model_fields.get(key)
            if field_info and field_info.description:
                example_values[key] = '[' + field_info.description + ']'
            else:
                example_values[key] = '[Your output here]'
        output_str += ouptut_template.format(**example_values)
        if '(Optional)' in ouptut_template:
            output_str += '\n\nNote: For optional fields, you can omit them in your output if they are not necessary.'
        output_str += '\n'
        return output_str

    def format(self, inputs_format: Optional[Type[LLMOutputParser]]=None, outputs_format: Optional[Type[LLMOutputParser]]=None, values: Optional[dict]=None, parse_mode: Optional[str]='title', title_format: Optional[str]='## {title}', output_format: Optional[str]=None, **kwargs) -> str:
        raise NotImplementedError(f'`format` method is not implemented for `{self.__class__.__name__}`.')

    def get_config(self) -> dict:
        return self.to_dict()

    def copy(self, **kwargs) -> 'PromptTemplate':
        """
        Create a deep-copied new PromptTemplate, optionally overriding fields with provided kwargs.
        """
        config = self.get_config()
        new_config = deepcopy(config)
        new_config = {k: kwargs.get(k, v) for k, v in new_config.items()}
        return self.__class__.from_dict(new_config)

def copy(self, **kwargs) -> 'PromptTemplate':
    """
        Create a deep-copied new PromptTemplate, optionally overriding fields with provided kwargs.
        """
    config = self.get_config()
    new_config = deepcopy(config)
    new_config = {k: kwargs.get(k, v) for k, v in new_config.items()}
    return self.__class__.from_dict(new_config)

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

def log_snapshot(self, graph: WorkFlowGraph, metrics: dict) -> None:
    """Log the snapshot of the workflow."""
    self._snapshot.append({'index': len(self._snapshot), 'graph': deepcopy(graph.get_config()), 'metrics': metrics})

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

class WorkFlowMiproOptimizer(MiproOptimizer):

    def __init__(self, graph: WorkFlowGraph, evaluator: Evaluator, optimizer_llm: Optional[BaseLLM]=None, **kwargs):
        """
        MiproOptimizer tailored for workflow graphs. 

        Args:
            graph (WorkFlowGraph): the workflow graph to optimize.
            evaluator (Evaluator): the evaluator to use for the optimization.
            optimizer_llm (BaseLLM): the LLM to use for the optimization. If None, will use the LLM model in the evaluator.
            **kwargs: additional keyword arguments to pass to the MiproOptimizer. Available options:
                - metric_threshold (Optional[int]): threshold for the metric score. If provided, only examples with scores above this threshold will be used as demonstrations.
                - max_bootstrapped_demos (int): maximum number of bootstrapped demonstrations to use. Defaults to 4.
                - max_labeled_demos (int): maximum number of labeled demonstrations to use. Defaults to 4.
                - auto (Optional[Literal["light", "medium", "heavy"]]): automatic configuration mode. If set, will override num_candidates and max_steps. 
                    "light": n=6, val_size=100; "medium": n=12, val_size=300; "heavy": n=18, val_size=1000. Defaults to "medium".
                - max_steps (int): maximum number of optimization steps. Required if auto is None.
                - num_candidates (Optional[int]): number of candidates to generate for each optimization step. Required if auto is None.
                - num_threads (Optional[int]): number of threads to use for parallel evaluation. If None, will use single thread.
                - max_errors (int): maximum number of errors allowed during evaluation before stopping. Defaults to 10.
                - seed (int): random seed for reproducibility. Defaults to 9.
                - init_temperature (float): initial temperature for instruction generation. Defaults to 0.5.
                - track_stats (bool): whether to track optimization statistics. Defaults to True.
                - save_path (Optional[str]): path to save optimization results. If None, results will not be saved.
                - minibatch (bool): whether to use minibatch evaluation during optimization. Defaults to True.
                - minibatch_size (int): size of minibatch for evaluation. Defaults to 35.
                - minibatch_full_eval_steps (int): number of minibatch steps between full evaluations. Defaults to 5.
                - program_aware_proposer (bool): whether to use program-aware instruction proposer. Defaults to True.
                - data_aware_proposer (bool): whether to use data-aware instruction proposer. Defaults to True.
                - view_data_batch_size (int): batch size for viewing data during instruction proposal. Defaults to 10.
                - tip_aware_proposer (bool): whether to use tip-aware instruction proposer. Defaults to True.
                - fewshot_aware_proposer (bool): whether to use fewshot-aware instruction proposer. Defaults to True.
                - requires_permission_to_run (bool): whether to require user permission before running optimization. Defaults to False.
                - provide_traceback (Optional[bool]): whether to provide traceback for evaluation errors. If None, will use default setting.
        """
        graph = self._validate_graph_compatibility(graph=graph)
        workflow_graph_program = WorkFlowGraphProgram(graph=graph, agent_manager=evaluator.agent_manager, executor_llm=evaluator.llm, collate_func=evaluator.collate_func, output_postprocess_func=evaluator.output_postprocess_func)
        registry = self._register_optimizable_parameters(program=workflow_graph_program)
        super().__init__(registry=registry, program=workflow_graph_program, optimizer_llm=optimizer_llm or evaluator.llm, evaluator=evaluator, **kwargs)

    def _validate_graph_compatibility(self, graph: WorkFlowGraph):
        """
        Check if the graph is compatible with the WorkFlowMipro optimizer. Also, convert the MiproPromptTemplate data to MiproPromptTemplate instances. 
        """
        for node in graph.nodes:
            if len(node.agents) > 1:
                raise ValueError('WorkFlowMiproOptimizer only supports workflows where every node only has a single agent.')
            else:
                agent = node.agents[0]
                if not isinstance(agent, dict):
                    raise ValueError(f"Unsupported agent type {type(agent)}. Expected 'dict'.")
                elif 'actions' in agent:
                    non_ContextExtraction_actions = [action for action in agent['actions'] if action['class_name'] != 'ContextExtraction']
                    if len(non_ContextExtraction_actions) > 1:
                        raise ValueError(f'WorkFlowMiproOptimizer only supports workflows where every agent only has a single action. {agent['name']} has {len(non_ContextExtraction_actions)} actions.')
                    if non_ContextExtraction_actions[0].get('prompt_template', None) is None:
                        logger.warning(f'{agent['name']} does not have a MiproPromptTemplate, its prompt will not be optimized.')
                    else:
                        prompt_template = non_ContextExtraction_actions[0]['prompt_template']
                        if isinstance(prompt_template, dict):
                            prompt_template = PromptTemplate.from_dict(prompt_template)
                        if isinstance(prompt_template, MiproPromptTemplate):
                            non_ContextExtraction_actions[0]['prompt_template'] = prompt_template
                        else:
                            logger.warning(f'{agent['name']} has a non-MiproPromptTemplate, its prompt will not be optimized. You should use `MiproPromptTemplate` to define the optimizable prompt.')
                elif agent.get('prompt_template', None) is None:
                    logger.warning(f'{agent['name']} does not have a MiproPromptTemplate, its prompt will not be optimized.')
                else:
                    prompt_template = agent['prompt_template']
                    if isinstance(prompt_template, dict):
                        prompt_template = PromptTemplate.from_dict(prompt_template)
                    if isinstance(prompt_template, MiproPromptTemplate):
                        agent['prompt_template'] = prompt_template
                    else:
                        logger.warning(f'{agent['name']} has a non-MiproPromptTemplate, its prompt will not be optimized. You should use `MiproPromptTemplate` to define the optimizable prompt.')
        return graph

    def _validate_evaluator(self, evaluator: Callable=None, benchmark: Benchmark=None, metric_name: str=None) -> Callable:
        if evaluator and isinstance(evaluator, Evaluator):
            evaluator = MiproEvaluatorWrapper(evaluator=evaluator, benchmark=benchmark, metric_name=metric_name)
        return super()._validate_evaluator(evaluator, benchmark, metric_name)

    def _register_optimizable_parameters(self, program: WorkFlowGraphProgram):
        registry = MiproRegistry()
        workflow_graph = program.graph
        for i, node in enumerate(workflow_graph.nodes):
            agent = node.agents[0]
            if 'actions' in agent:
                for j, action in enumerate(agent['actions']):
                    action_prompt_template = action.get('prompt_template', None)
                    if action_prompt_template and isinstance(action_prompt_template, MiproPromptTemplate):
                        registry.track(root_or_obj=program, path_or_attr=f"graph.nodes[{i}].agents[0]['actions'][{j}]['prompt_template']", name=f'{agent['name']}_prompt_template', input_names=node.get_input_names(), output_names=node.get_output_names())
            else:
                prompt_template = agent.get('prompt_template', None)
                if prompt_template and isinstance(prompt_template, MiproPromptTemplate):
                    registry.track(root_or_obj=program, path_or_attr=f"graph.nodes[{i}].agents[0]['prompt_template']", name=f'{agent['name']}_prompt_template', input_names=node.get_input_names(), output_names=node.get_output_names())
        if not registry.fields:
            raise ValueError('No optimizable parameters found in the workflow graph. Please check if the workflow graph is compatible with the WorkFlowMiproOptimizer. You should use `MiproPromptTemplate` to define the optimizable prompt.')
        return registry

def _validate_evaluator(self, evaluator: Callable=None, benchmark: Benchmark=None, metric_name: str=None) -> Callable:
    if evaluator and isinstance(evaluator, Evaluator):
        evaluator = MiproEvaluatorWrapper(evaluator=evaluator, benchmark=benchmark, metric_name=metric_name)
    return super()._validate_evaluator(evaluator, benchmark, metric_name)

class ShortTermMemory(BaseModule):
    """
    Short-term memory implementation.
    
    Stores only the most recent N messages (like a sliding window).
    Unlike BaseMemory/LongTermMemory, this is purely in-memory cache 
    and does not persist to storage_handler or vector DB.

    Attributes:
        buffer: Internal deque holding Message objects, capped at max_size.
        max_size: Maximum number of messages to retain.
        memory_id: Unique identifier for this memory instance.
        timestamp: Creation timestamp.
    """
    buffer: List[Message] = Field(default_factory=list, exclude=True)
    max_size: PositiveInt = Field(default=5, description='Maximum number of messages to keep in short-term memory')
    memory_id: str = Field(default_factory=generate_id)
    timestamp: str = Field(default_factory=get_timestamp)

    @field_validator('buffer', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure that the buffer is always a list, even if it is null in the JSON."""
        if v is None:
            return []
        return v

    def model_post_init(self, __context=None):
        """
        Pydantic V2 hook after model initialization.
        Convert buffer list → deque, enforce max_size.
        """
        self.buffer = deque(self.buffer, maxlen=self.max_size)

    @property
    def size(self) -> int:
        """Return current number of messages stored."""
        return len(self.buffer)

    def clear(self):
        """Clear all short-term memory."""
        self.buffer.clear()

    def add_message(self, message: Message):
        """Add a single message to short-term memory."""
        if not message:
            return
        self.buffer.append(message)

    def add_messages(self, messages: Union[Message, List[Message]]):
        """Add one or multiple messages."""
        if not isinstance(messages, list):
            messages = [messages]
        for msg in messages:
            self.add_message(msg)

    def get(self, n: Optional[int]=None) -> List[Message]:
        """
        Retrieve the most recent n messages (default: all).
        
        Args:
            n: Number of messages to return. If None, return all.
        
        Returns:
            List of Message objects, oldest → newest.
        """
        if n is None:
            return list(self.buffer)
        return list(self.buffer)[-n:]

    def get_last(self) -> Optional[Message]:
        """Return the latest message, or None if empty."""
        return self.buffer[-1] if self.buffer else None

@field_validator('buffer', mode='before')
@classmethod
def ensure_list(cls, v):
    """Ensure that the buffer is always a list, even if it is null in the JSON."""
    if v is None:
        return []
    return v

class ToyModule2(BaseModule):
    k4: Optional[str] = Field(default=None, description='name')
    k5: str = Field(description='key')
    k6: Optional[ToyTool] = Field(default=None)

    @field_validator('k4')
    @classmethod
    def validate_k4(cls, value):
        if value == 'k4_value':
            raise NotImplementedError('the method for "k4=k4_value" is not implemented!')
        return value

    def init_module(self):
        if self.k6 is None:
            if self.k4 is not None and self.k5 is not None:
                self.k6 = ToyTool(self.k4, self.k5)
            else:
                raise ValueError(f'either k4 and k5 is None!')

@field_validator('k4')
@classmethod
def validate_k4(cls, value):
    if value == 'k4_value':
        raise NotImplementedError('the method for "k4=k4_value" is not implemented!')
    return value

