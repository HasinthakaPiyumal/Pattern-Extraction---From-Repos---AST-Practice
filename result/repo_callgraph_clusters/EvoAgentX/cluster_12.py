# Cluster 12

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

@property
def size(self):
    """
        Get the total number of agents managed by this manager.
        """
    return len(self.agents)

class ActionGraph(BaseModule):
    name: str = Field(description='The name of the ActionGraph.')
    description: str = Field(description='The description of the ActionGraph.')
    llm_config: LLMConfig = Field(description='The config of LLM used to execute the ActionGraph.')

    def init_module(self):
        if self.llm_config:
            llm_cls = MODEL_REGISTRY.get_model(self.llm_config.llm_type)
            self._llm = llm_cls(config=self.llm_config)

    def execute(self, *args, **kwargs) -> dict:
        raise NotImplementedError(f'The execute function for {type(self).__name__} is not implemented!')

    def async_execute(self, *args, **kwargs) -> dict:
        raise NotImplementedError(f'The async_execute function for {type(self).__name__} is not implemented!')

    def get_graph_info(self, **kwargs) -> dict:
        """
        Get the information of the action graph, including all operators from the instance.
        """
        operators = {}
        for extra_name, extra_value in self.__pydantic_extra__.items():
            if isinstance(extra_value, Operator):
                operators[extra_name] = extra_value
        config = {'class_name': self.__class__.__name__, 'name': self.name, 'description': self.description, 'operators': {operator_name: {'class_name': operator.__class__.__name__, 'name': operator.name, 'description': operator.description, 'interface': operator.interface, 'prompt': operator.prompt} for operator_name, operator in operators.items()}}
        return config

    @classmethod
    def load_module(cls, path: str, llm_config: LLMConfig=None, **kwargs) -> Dict:
        """
        Load the ActionGraph from a file.
        """
        assert llm_config is not None, 'must provide `llm_config` when using `load_module` or `from_file` to load the ActionGraph from local storage'
        action_graph_data = super().load_module(path, **kwargs)
        action_graph_data['llm_config'] = llm_config.to_dict()
        return action_graph_data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> 'ActionGraph':
        """
        Create an ActionGraph from a dictionary.
        """
        class_name = data.get('class_name', None)
        if class_name:
            cls = MODULE_REGISTRY.get_module(class_name)
        operators_info = data.pop('operators', None)
        module = cls._create_instance(data)
        if operators_info:
            for extra_name, extra_value in module.__pydantic_extra__.items():
                if isinstance(extra_value, Operator) and extra_name in operators_info:
                    extra_value.set_operator(operators_info[extra_name])
        return module

    def save_module(self, path: str, ignore: List[str]=[], **kwargs):
        """
        Save the workflow graph to a module file.
        """
        logger.info('Saving {} to {}', self.__class__.__name__, path)
        config = self.get_graph_info()
        for ignore_key in ignore:
            config.pop(ignore_key, None)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return path

    def get_config(self) -> dict:
        """
        Get a dictionary containing all necessary configuration to recreate this action graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new ActionGraph instance
            with the same properties as this one.
        """
        config = self.get_graph_info()
        config['llm_config'] = self.llm_config.to_dict()
        return config

def get_config(self) -> dict:
    """
        Get a dictionary containing all necessary configuration to recreate this action graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new ActionGraph instance
            with the same properties as this one.
        """
    config = self.get_graph_info()
    config['llm_config'] = self.llm_config.to_dict()
    return config

class WorkFlowEdge(BaseModule):
    """
    Represents a directed edge in a workflow graph.
    
    Workflow edges connect tasks (nodes) in the workflow graph, establishing
    execution dependencies and data flow relationships. Each edge has a source
    node, target node, and optional priority to influence execution order.
    
    Attributes:
        source: Name of the source node (where the edge starts)
        target: Name of the target node (where the edge ends)
        priority: Numeric priority value for this edge (higher means higher priority)
    """
    source: str
    target: str
    priority: int = 0

    def __init__(self, edge_tuple: Optional[tuple]=(), **kwargs):
        """
        Initialize a WorkFlowEdge instance with either a tuple or keyword arguments.

        Parameters:
        ----------
            edge_tuple (tuple): a tuple containing the edge attributes in the format: (source, target, priority[optional]). 
                - source (str): the source of the edge. 
                - target (str): the target of the edge. 
                - priority (int, optional): The priority of the edge. Defaults to 0 if not provided.
            
            kwargs (dict): Key-value pairs specifying the edge attributes. These values will override those provided in `args` if both are supplied.

        Notes:
        ----------
            - Attributes provided via `kwargs` take precedence over those from the `args` tuple.
            - If `args` is empty or not provided, only `kwargs` will be used to initialize the instance.
        """
        data = self.init_from_tuple(edge_tuple)
        data.update(kwargs)
        super().__init__(**data)

    def init_from_tuple(self, edge_tuple: tuple) -> dict:
        if not edge_tuple:
            return {}
        keys = ['source', 'target', 'priority']
        data = {k: v for k, v in zip(keys, edge_tuple)}
        return data

    def compare_attrs(self):
        return (self.source, self.target, self.priority)

    def __eq__(self, other: 'WorkFlowEdge'):
        if not isinstance(other, WorkFlowEdge):
            return NotImplemented
        self_compare_attrs = self.compare_attrs()
        other_compare_attrs = other.compare_attrs()
        return all((self_attr == other_attr for self_attr, other_attr in zip(self_compare_attrs, other_compare_attrs)))

    def __hash__(self):
        return hash(self.compare_attrs())

def init_from_tuple(self, edge_tuple: tuple) -> dict:
    if not edge_tuple:
        return {}
    keys = ['source', 'target', 'priority']
    data = {k: v for k, v in zip(keys, edge_tuple)}
    return data

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

@property
def is_complete(self):
    leaf_nodes = [self.get_node(name) for name in self.find_end_nodes()]
    node_complete_list = [node.is_complete for node in leaf_nodes]
    if len(node_complete_list) == 0:
        return True
    if all(node_complete_list):
        return True
    return False

def pending(self, node: Union[str, WorkFlowNode]) -> bool:
    return self.set_node_status(node=node, new_state=WorkFlowNodeState.PENDING)

def running(self, node: Union[str, WorkFlowNode]) -> bool:
    return self.set_node_status(node=node, new_state=WorkFlowNodeState.RUNNING)

def completed(self, node: Union[str, WorkFlowNode]) -> bool:
    return self.set_node_status(node=node, new_state=WorkFlowNodeState.COMPLETED)

def failed(self, node: Union[str, WorkFlowNode]) -> bool:
    return self.set_node_status(node=node, new_state=WorkFlowNodeState.FAILED)

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

class SequentialWorkFlowGraph(WorkFlowGraph):
    """
    A linear workflow graph with a single path from start to end.

    Args:
        goal (str): The goal of the workflow.
        tasks (List[dict]): A list of tasks with their descriptions and inputs. Each task should have the following format:
            {
                "name": str,
                "description": str,
                "inputs": [{"name": str, "type": str, "required": bool, "description": str}, ...],
                "outputs": [{"name": str, "type": str, "required": bool, "description": str}, ...],
                "prompt": str, 
                "prompt_template": PromptTemplate, 
                "system_prompt" (optional): str, default is DEFAULT_SYSTEM_PROMPT,
                "output_parser" (optional): Type[ActionOutput],
                "parse_mode" (optional): str, default is "str" 
                "parse_func" (optional): Callable,
                "parse_title" (optional): str ,
                "tool_names" (optional): List[str] 
            }
    """

    def __init__(self, goal: str, tasks: List[dict], **kwargs):
        nodes = self._infer_nodes_from_tasks(tasks=tasks)
        edges = self._infer_edges_from_nodes(nodes=nodes)
        super().__init__(goal=goal, nodes=nodes, edges=edges, **kwargs)

    def _infer_nodes_from_tasks(self, tasks: List[dict]) -> List[WorkFlowNode]:
        nodes = [self._infer_node_from_task(task=task) for task in tasks]
        return nodes

    def _infer_node_from_task(self, task: dict) -> WorkFlowNode:
        node_name = task.get('name', None)
        if not node_name:
            raise ValueError('The `name` for the following task is required: {}'.format(task))
        node_description = task.get('description', None)
        if not node_description:
            raise ValueError('The `description` for the following task is required: {}'.format(task))
        agent_prompt = task.get('prompt', None)
        agent_prompt_template = task.get('prompt_template', None)
        if not agent_prompt and (not agent_prompt_template):
            raise ValueError('The `prompt` or `prompt_template` for the following task is required: {}'.format(task))
        inputs = task.get('inputs', [])
        outputs = task.get('outputs', [])
        agent_name = generate_dynamic_class_name(node_name + ' Agent')
        agent_description = node_description
        agent_system_prompt = task.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
        agent_output_parser = task.get('output_parser', None)
        agent_parse_mode = task.get('parse_mode', 'str')
        agent_parse_func = task.get('parse_func', None)
        agent_parse_title = task.get('parse_title', None)
        tool_names = task.get('tool_names', None)
        node = WorkFlowNode.from_dict({'name': node_name, 'description': node_description, 'inputs': inputs, 'outputs': outputs, 'agents': [{'name': agent_name, 'description': agent_description, 'prompt': agent_prompt, 'prompt_template': agent_prompt_template, 'system_prompt': agent_system_prompt, 'inputs': inputs, 'outputs': outputs, 'output_parser': agent_output_parser, 'parse_mode': agent_parse_mode, 'parse_func': agent_parse_func, 'parse_title': agent_parse_title, 'tool_names': tool_names}]})
        return node

    def get_graph_info(self, **kwargs) -> dict:
        """
        Get the information of the workflow graph.
        """
        config = {'class_name': self.__class__.__name__, 'goal': self.goal, 'tasks': [{'name': node.name, 'description': node.description, 'inputs': [param.to_dict(ignore=['class_name']) for param in node.inputs], 'outputs': [param.to_dict(ignore=['class_name']) for param in node.outputs], 'prompt': node.agents[0].get('prompt', None), 'prompt_template': node.agents[0].get('prompt_template', None).to_dict() if node.agents[0].get('prompt_template', None) else None, 'system_prompt': node.agents[0].get('system_prompt', None), 'parse_mode': node.agents[0].get('parse_mode', 'str'), 'parse_func': node.agents[0].get('parse_func', None).__name__ if node.agents[0].get('parse_func', None) else None, 'parse_title': node.agents[0].get('parse_title', None), 'tool_names': node.agents[0].get('tool_names', None)} for node in self.nodes]}
        return config

    def save_module(self, path: str, ignore: List[str]=[], **kwargs):
        """
        Save the workflow graph to a module file.
        """
        logger.info('Saving {} to {}', self.__class__.__name__, path)
        config = self.get_graph_info()
        for ignore_key in ignore:
            config.pop(ignore_key, None)
        make_parent_folder(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return path

    def get_config(self) -> Dict:
        """
        Get a dictionary containing all necessary configuration to recreate this workflow graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new SequentialWorkFlowGraph instance
            with the same properties as this one.
        """
        return self.get_graph_info()

def get_config(self) -> Dict:
    """
        Get a dictionary containing all necessary configuration to recreate this workflow graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new SequentialWorkFlowGraph instance
            with the same properties as this one.
        """
    return self.get_graph_info()

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

class PromptTuningModule(dspy.Module):
    """
    A prompt tuning module that manages interactions between predictors,
    parameter registry, and program functions.
    
    This module coordinates prompt optimization through:
    1. Maintaining a set of predictors for different tasks
    2. Synchronizing optimized parameters back to the program
    3. Executing the program with updated parameters
    
    Parameters
    ----------
    program : Union[Callable[..., dict], Callable[..., Awaitable[dict]]]
        The main program function to execute. Can be either synchronous or asynchronous.
        Must return a dictionary containing execution results.
    signature_dict : Dict[str, dspy.Signature]
        A mapping of task names to their corresponding DSPy signatures.
        Each signature defines the input/output structure for a specific task.
    registry : ParamRegistry
        A registry that maintains tunable parameters shared between
        predictors and the program.
    """

    @classmethod
    def from_registry(cls, program: Union[Callable[..., dict], Callable[..., Awaitable[dict]]], registry: ParamRegistry) -> 'PromptTuningModule':
        """
        Factory method to create a PromptTuningModule from a registry and program.
        
        This method:
        1. Creates signatures for each field in the registry
        2. Initializes a PromptTuningModule with the program and signatures
        3. Sets up predictors for each signature
        
        Parameters
        ----------
        program : Union[Callable[..., dict], Callable[..., Awaitable[dict]]]
            The main program function to execute
        registry : ParamRegistry
            Registry containing tunable parameters
            
        Returns
        -------
        PromptTuningModule
            A configured PromptTuningModule instance
            
        Examples
        --------
        >>> registry = ParamRegistry()
        >>> registry.register("task1", "What is {topic}?")
        >>> registry.register("task2", PromptTemplate(system="You are helpful.", user="{query}"))
        >>> def my_program(**kwargs) -> dict:
        ...     return {"result": "done"}
        >>> module = PromptTuningModule.from_registry(my_program, registry)
        """
        from .signature_utils import signature_from_registry
        signature_dict, signature_name2register_name = signature_from_registry(registry=registry)
        return cls(program=program, signature_dict=signature_dict, registry=registry, signature_name2register_name=signature_name2register_name)

    def __init__(self, program: Union[Callable[..., dict], Callable[..., Awaitable[dict]]], signature_dict: Dict[str, dspy.Signature], registry: ParamRegistry, signature_name2register_name: Dict[str, str]):
        """
        Initialize a PromptTuningModule instance.
        
        Parameters
        ----------
        program : Union[Callable[..., dict], Callable[..., Awaitable[dict]]]
            The main program function to execute
        signature_dict : Dict[str, dspy.Signature]
            Mapping of task names to signatures
        registry : ParamRegistry
            Parameter registry
        signature_name2register_name : Dict[str, str]
            Mapping of signature names to register names
        """
        super().__init__()
        self.program = program
        self.predicts = []
        seen = set()
        for name, signature in signature_dict.items():
            if name in seen:
                raise ValueError(f'Duplicate name {name} in signature_dict')
            seen.add(name)
            self.predicts.append(dspy.Predict(signature, name=name))
        self.registry = registry
        self.signature_name2register_name = signature_name2register_name

    def reset(self):
        """
        Reset the module to its initial state.
        """
        self.registry.reset()
        for predict in self.predicts:
            signature = predict.signature
            signature_name = signature.__name__
            register_name = self.signature_name2register_name[signature_name]
            register_element = self.registry.get(register_name)
            if isinstance(register_element, PromptTemplate):
                predict.signature.instructions = register_element.instruction
                predict.demos = register_element.demonstrations
            elif isinstance(register_element, str):
                predict.signature.instructions = register_element
                predict.demos = []
            else:
                logger.warning(f'Unsupported register element type: {type(register_element)}')
        return self

    def escape_braces(self, text):
        """
        Escape all braces in the text.
        
        Parameters
        ----------
        text : str
            Text that needs escaping
            
        Returns
        -------
        str
            Escaped text
        """

        def helper(s, start=0):
            result = ''
            i = start
            while i < len(s):
                if s[i] == '{':
                    inner, new_i = helper(s, i + 1)
                    result += '{{' + inner + '}}'
                    i = new_i
                elif s[i] == '}':
                    return (result, i + 1)
                else:
                    result += s[i]
                    i += 1
            return (result, i)
        escaped, _ = helper(text)
        return escaped

    def _validate_prompt(self, prompt: str, input_names: List[str], verbose: bool=True) -> str:
        """
        Validate if the generated prompt is valid. Currently only checks if required inputs are wrapped in braces.
        
        Parameters
        ----------
        prompt : str
            The prompt to validate
        input_names : List[str]
            List of required input names
        verbose : bool, optional
            Whether to show detailed information, defaults to True
            
        Returns
        -------
        str
            Validated and potentially modified prompt
        """
        modified_messages = []
        required_inputs = input_names
        missing_required_inputs = [name for name in required_inputs if f'{{{name}}}' not in prompt]
        if missing_required_inputs:
            input_values = '\n\n'.join([f'{name}: {{{name}}}' for name in missing_required_inputs])
            prompt += f'\n\nThe followings are some required input values: \n{input_values}'
            modified_messages.append(f'added missing inputs: {', '.join(missing_required_inputs)}')
        prompt = self.escape_braces(prompt)
        for name in input_names:
            prompt = prompt.replace(f'{{{{{name}}}}}', f'{{{name}}}')
        prompt = prompt.replace('{{{{', '{{').replace('}}}}', '}}')
        return prompt

    def get_field_type(self, field: Field) -> str:
        """
        Get the type of the field.
        
        Parameters
        ----------
        field : Field
            The field to get type from
            
        Returns
        -------
        str
            The field type
        """
        return field.json_schema_extra.get('__dspy_field_type') if field.json_schema_extra.get('__dspy_field_type') else None

    def is_prompt_template(self, register_name: str) -> bool:
        """
        Check if the register name is a prompt template.
        
        Parameters
        ----------
        register_name : str
            The register name to check
            
        Returns
        -------
        bool
            Whether it is a prompt template
        """
        return self.registry.get(register_name) is not None and isinstance(self.registry.get(register_name), PromptTemplate)

    def get_demos(self, demos: list) -> List[dict]:
        result = []
        for demo in demos:
            if isinstance(demo, dspy.Example):
                demo = demo.toDict()
            result.append(demo)
        return result

    def _inject_demos_to_string(self, instruction: str, demos: List[dict], input_names: List[str], output_names: List[str]) -> str:
        """
        Inject demos to the instruction.
        """
        if not demos:
            return instruction

        def _escape_braces(text: str) -> str:
            return text.replace('{', '{{').replace('}', '}}')

        def format_demo(demo: dict) -> str:
            demo_str = 'Inputs:\n'
            inputs = {name: demo.get(name, 'Not provided') for name in input_names}
            demo_str += '\n'.join([f'{name}:\n{_escape_braces(str(value))}' for name, value in inputs.items()])
            demo_str += '\n\nOutputs:\n'
            outputs = {name: demo.get(name, 'Not provided') for name in output_names}
            demo_str += '\n'.join([f'{name}:\n{_escape_braces(str(value))}' for name, value in outputs.items()])
            return demo_str
        demos_string = '\n\n'.join([f'Example {i + 1}:\n{format_demo(demo)}' for i, demo in enumerate(demos)])
        prompt = f'{instruction}\n\nThe following are some examples:\n{demos_string}'
        return prompt

    def sync_predict_inputs_to_program(self):
        """
        Synchronize current input values from all predictors back to the registry.
        
        This method ensures that any optimized parameters in the predictors' configurations
        are properly reflected in the registry, which in turn affects program execution.
        
        Synchronization process:
        1. Iterate through all predictors
        2. For each predictor, check its signature's input fields
        3. If a field has a value in the predictor's config, update the registry
        
        Note: Values in predictor configs take precedence as they may contain
        optimized values from recent tuning iterations.
        """
        for predict in self.predicts:
            signature = predict.signature
            instruction = signature.instructions
            demos = predict.demos
            input_names = [name for name, field in predict.signature.fields.items() if self.get_field_type(field) == 'input']
            output_names = [name for name, field in predict.signature.fields.items() if self.get_field_type(field) == 'output']
            signature_name = signature.__name__
            register_name = self.signature_name2register_name[signature_name]
            if self.is_prompt_template(register_name):
                prompt_template: PromptTemplate = self.registry.get(register_name)
                prompt_template.instruction = instruction
                prompt_template.demonstrations = self.get_demos(demos)
                self.registry.set(register_name, prompt_template)
            else:
                instruction = self._validate_prompt(instruction, input_names)
                prompt = self._inject_demos_to_string(instruction, self.get_demos(demos), input_names, output_names)
                self.registry.set(register_name, prompt)

    def constrcut_trace(self, execution_data: dict) -> dict:
        """
        Construct the trace of the execution.
        
        Parameters
        ----------
        execution_data : dict
            Execution data
            
        Returns
        -------
        dict
            Trace information
        """
        trace: List[dict] = []
        for predict in self.predicts:
            input_names = [name for name, field in predict.signature.fields.items() if self.get_field_type(field) == 'input']
            output_names = [name for name, field in predict.signature.fields.items() if self.get_field_type(field) == 'output']
            input_dict = {}
            output_dict = {}
            for name in input_names:
                if name not in execution_data:
                    logger.warning(f'Input {name} not found in execution data')
            for name in output_names:
                if name not in execution_data:
                    logger.warning(f'Output {name} not found in execution data')
            for name in input_names:
                if name in execution_data:
                    input_dict[name] = execution_data[name]
            for name in output_names:
                if name in execution_data:
                    output_dict[name] = execution_data[name]
            trace_tuple = (predict, input_dict, output_dict)
            trace.append(trace_tuple)
        return trace

    def forward(self, **kwargs) -> dict:
        """
        Execute the program with synchronized parameters and optional inputs.
        
        This method:
        1. Synchronizes optimized prompts back to the program via registry
        2. Executes the program (handles both sync and async functions)
        3. Validates and returns the program's output
        
        Parameters
        ----------
        **kwargs : dict
            Optional keyword arguments to pass to the program function
            
        Returns
        -------
        dict
            The program's execution results
            
        Raises
        ------
        ValueError
            If the program doesn't return a dictionary
        """
        self.sync_predict_inputs_to_program()
        if asyncio.iscoroutinefunction(self.program):
            output, execution_data = asyncio.run(self.program(**kwargs)) if kwargs else asyncio.run(self.program())
        else:
            output, execution_data = self.program(**kwargs) if kwargs else self.program()
        trace = self.constrcut_trace(execution_data)
        if dspy.settings.trace is not None:
            dspy_trace = dspy.settings.trace
            dspy_trace.extend(trace)
        return output

    def deepcopy(self):
        """
        Deep copy the module.
        
        This is a tweak to the default Python deepcopy that only deep copies `self.parameters()`,
        and for other attributes, we just do a shallow copy.
        
        Returns
        -------
        PromptTuningModule
            A deep copy of the module
        """
        try:
            new_instance = copy.deepcopy(self)
            setattr(new_instance, 'program', self.program)
            return new_instance
        except Exception:
            pass
        new_instance = self.__class__.__new__(self.__class__)
        for attr, value in self.__dict__.items():
            if isinstance(value, dspy.Module):
                setattr(new_instance, attr, value.deepcopy())
            else:
                try:
                    setattr(new_instance, attr, copy.deepcopy(value))
                except Exception:
                    try:
                        setattr(new_instance, attr, copy.copy(value))
                    except Exception:
                        setattr(new_instance, attr, value)
        setattr(new_instance, 'program', self.program)
        return new_instance

    def save(self, path, save_program=False):
        """Save the module.

        Save the module to a directory or a file. There are two modes:
        - `save_program=False`: Save only the state of the module to a json or pickle file, based on the value of
            the file extension.
        - `save_program=True`: Save the whole module to a directory via cloudpickle, which contains both the state and
            architecture of the model.

        We also save the dependency versions, so that the loaded model can check if there is a version mismatch on
        critical dependencies or DSPy version.

        Args:
            path (str): Path to the saved state file, which should be a .json or .pkl file when `save_program=False`,
                and a directory when `save_program=True`.
            save_program (bool): If True, save the whole module to a directory via cloudpickle, otherwise only save
                the state.
        """
        metadata = {}
        metadata['dependency_versions'] = get_dependency_versions()
        path = Path(path)
        if not path.is_dir():
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
        elif not path.exists():
            if not path.exists():
                path.mkdir(parents=True)
        if hasattr(self.program, 'save'):
            self.program.save(str(path))
            return
        if save_program:
            if path.suffix:
                raise ValueError(f'`path` must point to a directory without a suffix when `save_program=True`, but received: {path}')
            if path.exists() and (not path.is_dir()):
                raise NotADirectoryError(f"The path '{path}' exists but is not a directory.")
            try:
                with open(path / 'program.pkl', 'wb') as f:
                    cloudpickle.dump(self, f)
            except Exception as e:
                raise RuntimeError(f'Saving failed with error: {e}. Please remove the non-picklable attributes from your DSPy program, or consider using state-only saving by setting `save_program=False`.')
            with open(path / 'metadata.json', 'w') as f:
                ujson.dump(metadata, f, indent=4)
            return
        state = self.dump_state()
        state['metadata'] = metadata
        if path.suffix == '.json':
            try:
                with open(path, 'w') as f:
                    f.write(ujson.dumps(state, indent=4))
            except Exception as e:
                raise RuntimeError(f'Failed to save state to {path} with error: {e}. Your DSPy program may contain non json-serializable objects, please consider saving the state in .pkl by using `path` ending with `.pkl`, or saving the whole program by setting `save_program=True`.')
        elif path.suffix == '.pkl':
            with open(path, 'wb') as f:
                cloudpickle.dump(state, f)
        else:
            raise ValueError(f'`path` must end with `.json` or `.pkl` when `save_program=False`, but received: {path}')

    def load(self, path):
        """Load the saved module. You may also want to check out dspy.load, if you want to
        load an entire program, not just the state for an existing program.

        Args:
            path (str): Path to the saved state file, which should be a .json or a .pkl file
        """
        path = Path(path)
        if hasattr(self.program, 'load'):
            self.program.load(str(path))
            return
        if path.suffix == '.json':
            with open(path) as f:
                state = ujson.loads(f.read())
        elif path.suffix == '.pkl':
            with open(path, 'rb') as f:
                state = cloudpickle.load(f)
        else:
            raise ValueError(f'`path` must end with `.json` or `.pkl`, but received: {path}')
        dependency_versions = get_dependency_versions()
        saved_dependency_versions = state['metadata']['dependency_versions']
        for key, saved_version in saved_dependency_versions.items():
            if dependency_versions[key] != saved_version:
                logger.warning(f'There is a mismatch of {key} version between saved model and current environment. You saved with `{key}=={saved_version}`, but now you have `{key}=={dependency_versions[key]}`. This might cause errors or performance downgrade on the loaded model, please consider loading the model in the same environment as the saving environment.')
        self.load_state(state)
        self.sync_predict_inputs_to_program()

def helper(s, start=0):
    result = ''
    i = start
    while i < len(s):
        if s[i] == '{':
            inner, new_i = helper(s, i + 1)
            result += '{{' + inner + '}}'
            i = new_i
        elif s[i] == '}':
            return (result, i + 1)
        else:
            result += s[i]
            i += 1
    return (result, i)

def escape_braces(self, text):
    """
        Escape all braces in the text.
        
        Parameters
        ----------
        text : str
            Text that needs escaping
            
        Returns
        -------
        str
            Escaped text
        """

    def helper(s, start=0):
        result = ''
        i = start
        while i < len(s):
            if s[i] == '{':
                inner, new_i = helper(s, i + 1)
                result += '{{' + inner + '}}'
                i = new_i
            elif s[i] == '}':
                return (result, i + 1)
            else:
                result += s[i]
                i += 1
        return (result, i)
    escaped, _ = helper(text)
    return escaped

def get_demos(self, demos: list) -> List[dict]:
    result = []
    for demo in demos:
        if isinstance(demo, dspy.Example):
            demo = demo.toDict()
        result.append(demo)
    return result

class DataUtils:

    def __init__(self, root_path: str):
        self.root_path = root_path
        self.top_scores = []

    def load_results(self, path: str) -> list:
        result_path = os.path.join(path, 'results.json')
        if os.path.exists(result_path):
            with open(result_path, 'r') as json_file:
                try:
                    return json.load(json_file)
                except json.JSONDecodeError:
                    return []
        return []

    def get_top_rounds(self, sample: int, path=None, mode='Graph'):
        self._load_scores(path, mode)
        unique_rounds = set()
        unique_top_scores = []
        first_round = next((item for item in self.top_scores if item['round'] == 0), None)
        if first_round:
            unique_top_scores.append(first_round)
            unique_rounds.add(0)
        for item in self.top_scores:
            if item['round'] not in unique_rounds:
                unique_top_scores.append(item)
                unique_rounds.add(item['round'])
                if len(unique_top_scores) >= sample:
                    break
        return unique_top_scores

    def select_round(self, items):
        if not items:
            raise ValueError('Item list is empty.')
        sorted_items = sorted(items, key=lambda x: x['score'], reverse=True)
        scores = [item['score'] * 100 for item in sorted_items]
        probabilities = self._compute_probabilities(scores)
        logger.info(f'\nMixed probability distribution: {probabilities}')
        logger.info(f'\nSorted rounds: {sorted_items}')
        selected_index = np.random.choice(len(sorted_items), p=probabilities)
        logger.info(f'\nSelected index: {selected_index}, Selected item: {sorted_items[selected_index]}')
        return sorted_items[selected_index]

    def _compute_probabilities(self, scores, alpha=0.2, lambda_=0.3):
        scores = np.array(scores, dtype=np.float64)
        n = len(scores)
        if n == 0:
            raise ValueError('Score list is empty.')
        uniform_prob = np.full(n, 1.0 / n, dtype=np.float64)
        max_score = np.max(scores)
        shifted_scores = scores - max_score
        exp_weights = np.exp(alpha * shifted_scores)
        sum_exp_weights = np.sum(exp_weights)
        if sum_exp_weights == 0:
            raise ValueError('Sum of exponential weights is 0, cannot normalize.')
        score_prob = exp_weights / sum_exp_weights
        mixed_prob = lambda_ * uniform_prob + (1 - lambda_) * score_prob
        total_prob = np.sum(mixed_prob)
        if not np.isclose(total_prob, 1.0):
            mixed_prob = mixed_prob / total_prob
        return mixed_prob

    def load_log(self, cur_round, path=None, mode: str='Graph'):
        if mode == 'Graph':
            log_dir = os.path.join(self.root_path, f'round_{cur_round}', 'log.json')
        else:
            log_dir = path
        if not os.path.exists(log_dir):
            return ''
        logger.info(log_dir)
        data = load_json(log_dir, type='json')
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            data = list(data)
        if not data:
            return ''
        sample_size = min(3, len(data))
        random_samples = random.sample(data, sample_size)
        log = ''
        for sample in random_samples:
            log += json.dumps(sample, indent=4, ensure_ascii=False) + '\n\n'
        return log

    def get_results_file_path(self, graph_path: str) -> str:
        return os.path.join(graph_path, 'results.json')

    def create_result_data(self, round: int, score: float, avg_cost: float, total_cost: float) -> dict:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {'round': round, 'score': score, 'avg_cost': avg_cost, 'total_cost': total_cost, 'time': now}

    def save_results(self, json_file_path: str, data: list):
        save_json(data, json_file_path, type='json', use_indent=True)

    def _load_scores(self, path=None, mode='Graph'):
        if mode == 'Graph':
            rounds_dir = self.root_path
        else:
            rounds_dir = path
        result_file = os.path.join(rounds_dir, 'results.json')
        self.top_scores = []
        data = load_json(result_file, type='json')
        df = pd.DataFrame(data)
        scores_per_round = df.groupby('round')['score'].mean().to_dict()
        for round_number, average_score in scores_per_round.items():
            self.top_scores.append({'round': round_number, 'score': average_score})
        self.top_scores.sort(key=lambda x: x['score'], reverse=True)
        return self.top_scores

def get_top_rounds(self, sample: int, path=None, mode='Graph'):
    self._load_scores(path, mode)
    unique_rounds = set()
    unique_top_scores = []
    first_round = next((item for item in self.top_scores if item['round'] == 0), None)
    if first_round:
        unique_top_scores.append(first_round)
        unique_rounds.add(0)
    for item in self.top_scores:
        if item['round'] not in unique_rounds:
            unique_top_scores.append(item)
            unique_rounds.add(item['round'])
            if len(unique_top_scores) >= sample:
                break
    return unique_top_scores

def _compute_probabilities(self, scores, alpha=0.2, lambda_=0.3):
    scores = np.array(scores, dtype=np.float64)
    n = len(scores)
    if n == 0:
        raise ValueError('Score list is empty.')
    uniform_prob = np.full(n, 1.0 / n, dtype=np.float64)
    max_score = np.max(scores)
    shifted_scores = scores - max_score
    exp_weights = np.exp(alpha * shifted_scores)
    sum_exp_weights = np.sum(exp_weights)
    if sum_exp_weights == 0:
        raise ValueError('Sum of exponential weights is 0, cannot normalize.')
    score_prob = exp_weights / sum_exp_weights
    mixed_prob = lambda_ * uniform_prob + (1 - lambda_) * score_prob
    total_prob = np.sum(mixed_prob)
    if not np.isclose(total_prob, 1.0):
        mixed_prob = mixed_prob / total_prob
    return mixed_prob

class SearchSerpAPI(SearchBase):
    """
    SerpAPI search tool that provides access to multiple search engines including
    Google, Bing, Baidu, Yahoo, and DuckDuckGo through a unified interface.
    """
    api_key: Optional[str] = Field(default=None, description='SerpAPI authentication key')
    default_engine: Optional[str] = Field(default='google', description='Default search engine')
    default_location: Optional[str] = Field(default=None, description='Default geographic location')
    default_language: Optional[str] = Field(default='en', description='Default interface language')
    default_country: Optional[str] = Field(default='us', description='Default country code')
    enable_content_scraping: Optional[bool] = Field(default=True, description='Enable full content scraping')

    def __init__(self, name: str='SearchSerpAPI', num_search_pages: Optional[int]=5, max_content_words: Optional[int]=None, api_key: Optional[str]=None, default_engine: Optional[str]='google', default_location: Optional[str]=None, default_language: Optional[str]='en', default_country: Optional[str]='us', enable_content_scraping: Optional[bool]=True, **kwargs):
        """
        Initialize the SerpAPI Search tool.
        
        Args:
            name (str): Name of the tool
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            api_key (str): SerpAPI authentication key (can also use SERPAPI_KEY env var)
            default_engine (str): Default search engine (google, bing, baidu, yahoo, duckduckgo)
            default_location (str): Default geographic location for searches
            default_language (str): Default interface language
            default_country (str): Default country code
            enable_content_scraping (bool): Whether to scrape full page content
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, num_search_pages=num_search_pages, max_content_words=max_content_words, api_key=api_key, default_engine=default_engine, default_location=default_location, default_language=default_language, default_country=default_country, enable_content_scraping=enable_content_scraping, **kwargs)
        self.api_key = api_key or os.getenv('SERPAPI_KEY', '')
        self.base_url = 'https://serpapi.com/search.json'
        if not self.api_key:
            logger.warning('SerpAPI key not found. Set SERPAPI_KEY environment variable or pass api_key parameter.')

    def _build_serpapi_params(self, query: str, engine: str=None, location: str=None, language: str=None, country: str=None, search_type: str=None, num_results: int=None) -> Dict[str, Any]:
        """
        Build SerpAPI request parameters.
        
        Args:
            query (str): Search query
            engine (str): Search engine to use
            location (str): Geographic location
            language (str): Interface language
            country (str): Country code
            search_type (str): Type of search (web, images, news, shopping, maps)
            num_results (int): Number of results to retrieve
            
        Returns:
            Dict[str, Any]: SerpAPI request parameters
        """
        params = {'q': query, 'api_key': self.api_key, 'num': num_results or self.num_search_pages}
        if location or self.default_location:
            params['location'] = location or self.default_location
        if language or self.default_language:
            params['hl'] = language or self.default_language
        if country or self.default_country:
            params['gl'] = country or self.default_country
        if search_type and search_type != 'web':
            search_type_map = {'images': 'isch', 'news': 'nws', 'shopping': 'shop', 'maps': 'lcl'}
            if search_type in search_type_map:
                params['tbm'] = search_type_map[search_type]
        return params

    def _execute_serpapi_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute search using direct HTTP requests to SerpAPI.
        
        Args:
            params (Dict[str, Any]): Search parameters
            
        Returns:
            Dict[str, Any]: SerpAPI response data
            
        Raises:
            Exception: For API errors
        """
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise Exception(f'SerpAPI error: {data['error']}')
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f'SerpAPI request failed: {str(e)}')
        except Exception as e:
            raise Exception(f'SerpAPI search failed: {str(e)}')

    def _process_serpapi_results(self, serpapi_data: Dict[str, Any], max_content_words: int=None) -> Dict[str, Any]:
        """
        Process SerpAPI results into structured format with processed results + raw data.
        
        Args:
            serpapi_data (Dict[str, Any]): Raw SerpAPI response
            max_content_words (int): Maximum words per result content
            
        Returns:
            Dict[str, Any]: Structured response with processed results and raw data
        """
        processed_results = []
        if (knowledge_graph := serpapi_data.get('knowledge_graph', {})):
            if (description := knowledge_graph.get('description')):
                title = knowledge_graph.get('title', 'Unknown')
                content = f'**{title}**'
                if (kg_type := knowledge_graph.get('type')):
                    content += f' ({kg_type})'
                content += f'\n\n{description}'
                if (kg_list := knowledge_graph.get('list', {})):
                    content += '\n\n**Key Information:**'
                    for key, value in list(kg_list.items())[:5]:
                        if isinstance(value, list) and value:
                            formatted_key = key.replace('_', ' ').title()
                            formatted_value = ', '.join((str(v) for v in value[:3]))
                            content += f'\n• {formatted_key}: {formatted_value}'
                processed_results.append({'title': f'Knowledge: {title}', 'content': self._truncate_content(content, max_content_words or 200), 'url': knowledge_graph.get('source', {}).get('link', ''), 'type': 'knowledge_graph', 'priority': 1})
        for item in serpapi_data.get('organic_results', []):
            url = item.get('link', '')
            title = item.get('title', 'No Title')
            snippet = item.get('snippet', '')
            position = item.get('position', 0)
            result = {'title': title, 'content': self._truncate_content(snippet, max_content_words or 400), 'url': url, 'type': 'organic', 'priority': 2, 'position': position}
            if self.enable_content_scraping and url and url.startswith(('http://', 'https://')):
                try:
                    scraped_title, scraped_content = self._scrape_page(url)
                    if scraped_content and scraped_content.strip():
                        if scraped_title and scraped_title.strip():
                            result['title'] = scraped_title
                        result['site_content'] = self._truncate_content(scraped_content, max_content_words or 400)
                    else:
                        result['site_content'] = None
                except Exception as e:
                    logger.debug(f'Content scraping failed for {url}: {str(e)}')
                    result['site_content'] = None
            else:
                result['site_content'] = None
            if snippet or result.get('site_content'):
                processed_results.append(result)
        raw_data = {}
        raw_sections = ['local_results', 'news_results', 'shopping_results', 'related_questions', 'recipes_results', 'images_results']
        for section in raw_sections:
            if section in serpapi_data and serpapi_data[section]:
                if section == 'local_results':
                    places = serpapi_data[section].get('places', [])[:3]
                    if places:
                        raw_data[section] = {'places': places}
                else:
                    raw_data[section] = serpapi_data[section][:3]
        search_metadata = {}
        if (search_meta := serpapi_data.get('search_metadata', {})):
            search_metadata = {'query': search_meta.get('query', ''), 'location': search_meta.get('location', ''), 'total_results': search_meta.get('total_results', ''), 'search_time': search_meta.get('total_time_taken', '')}
        processed_results.sort(key=lambda x: (x.get('priority', 999), x.get('position', 0)))
        return {'results': processed_results, 'raw_data': raw_data if raw_data else None, 'search_metadata': search_metadata if search_metadata else None, 'error': None}

    def _handle_api_errors(self, error: Exception) -> str:
        """
        Handle SerpAPI specific errors with appropriate messages.
        
        Args:
            error (Exception): The exception that occurred
            
        Returns:
            str: User-friendly error message
        """
        error_str = str(error).lower()
        if 'api key' in error_str or 'unauthorized' in error_str:
            return 'Invalid or missing SerpAPI key. Please set SERPAPI_KEY environment variable.'
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            return 'SerpAPI rate limit exceeded. Please try again later.'
        elif 'quota' in error_str or 'credit' in error_str:
            return 'SerpAPI quota exceeded. Please check your plan limits.'
        elif 'timeout' in error_str:
            return 'SerpAPI request timeout. Please try again.'
        else:
            return f'SerpAPI error: {str(error)}'

    def search(self, query: str, num_search_pages: int=None, max_content_words: int=None, engine: str=None, location: str=None, language: str=None, country: str=None, search_type: str=None) -> Dict[str, Any]:
        """
        Search using SerpAPI with comprehensive parameter support.
        
        Args:
            query (str): The search query
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            engine (str): Search engine (google, bing, baidu, yahoo, duckduckgo)
            location (str): Geographic location for localized results
            language (str): Interface language (e.g., 'en', 'es', 'fr')
            country (str): Country code for country-specific results (e.g., 'us', 'uk')
            search_type (str): Type of search (web, images, news, shopping, maps)
            
        Returns:
            Dict[str, Any]: Contains search results and optional error message
        """
        num_search_pages = num_search_pages or self.num_search_pages
        max_content_words = max_content_words or self.max_content_words
        if not self.api_key:
            error_msg = 'SerpAPI key is required. Please set SERPAPI_KEY environment variable or pass api_key parameter. Get your key from: https://serpapi.com/'
            logger.error(error_msg)
            return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}
        try:
            search_engine = engine or self.default_engine
            logger.info(f'Searching {search_engine} via SerpAPI: {query}, num_results={num_search_pages}, max_content_words={max_content_words}')
            params = self._build_serpapi_params(query=query, engine=search_engine, location=location, language=language, country=country, search_type=search_type, num_results=num_search_pages)
            serpapi_data = self._execute_serpapi_search(params)
            response_data = self._process_serpapi_results(serpapi_data, max_content_words)
            logger.info(f'Successfully retrieved {len(response_data['results'])} processed results')
            return response_data
        except Exception as e:
            error_msg = self._handle_api_errors(e)
            logger.error(f'SerpAPI search failed: {error_msg}')
            return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}

def search(self, query: str, num_search_pages: int=None, max_content_words: int=None, engine: str=None, location: str=None, language: str=None, country: str=None, search_type: str=None) -> Dict[str, Any]:
    """
        Search using SerpAPI with comprehensive parameter support.
        
        Args:
            query (str): The search query
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            engine (str): Search engine (google, bing, baidu, yahoo, duckduckgo)
            location (str): Geographic location for localized results
            language (str): Interface language (e.g., 'en', 'es', 'fr')
            country (str): Country code for country-specific results (e.g., 'us', 'uk')
            search_type (str): Type of search (web, images, news, shopping, maps)
            
        Returns:
            Dict[str, Any]: Contains search results and optional error message
        """
    num_search_pages = num_search_pages or self.num_search_pages
    max_content_words = max_content_words or self.max_content_words
    if not self.api_key:
        error_msg = 'SerpAPI key is required. Please set SERPAPI_KEY environment variable or pass api_key parameter. Get your key from: https://serpapi.com/'
        logger.error(error_msg)
        return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}
    try:
        search_engine = engine or self.default_engine
        logger.info(f'Searching {search_engine} via SerpAPI: {query}, num_results={num_search_pages}, max_content_words={max_content_words}')
        params = self._build_serpapi_params(query=query, engine=search_engine, location=location, language=language, country=country, search_type=search_type, num_results=num_search_pages)
        serpapi_data = self._execute_serpapi_search(params)
        response_data = self._process_serpapi_results(serpapi_data, max_content_words)
        logger.info(f'Successfully retrieved {len(response_data['results'])} processed results')
        return response_data
    except Exception as e:
        error_msg = self._handle_api_errors(e)
        logger.error(f'SerpAPI search failed: {error_msg}')
        return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}

class SearchSerperAPI(SearchBase):
    """
    SerperAPI search tool that provides access to Google search results
    through a simple and efficient API interface.
    """
    api_key: Optional[str] = Field(default=None, description='SerperAPI authentication key')
    default_location: Optional[str] = Field(default=None, description='Default geographic location')
    default_language: Optional[str] = Field(default='en', description='Default interface language')
    default_country: Optional[str] = Field(default='us', description='Default country code')
    enable_content_scraping: Optional[bool] = Field(default=True, description='Enable full content scraping')

    def __init__(self, name: str='SearchSerperAPI', num_search_pages: Optional[int]=10, max_content_words: Optional[int]=None, api_key: Optional[str]=None, default_location: Optional[str]=None, default_language: Optional[str]='en', default_country: Optional[str]='us', enable_content_scraping: Optional[bool]=True, **kwargs):
        """
        Initialize the SerperAPI Search tool.
        
        Args:
            name (str): Name of the tool
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            api_key (str): SerperAPI authentication key (can also use SERPERAPI_KEY env var)
            default_location (str): Default geographic location for searches
            default_language (str): Default interface language
            default_country (str): Default country code
            enable_content_scraping (bool): Whether to scrape full page content
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, num_search_pages=num_search_pages, max_content_words=max_content_words, api_key=api_key, default_location=default_location, default_language=default_language, default_country=default_country, enable_content_scraping=enable_content_scraping, **kwargs)
        self.api_key = api_key or os.getenv('SERPERAPI_KEY', '')
        self.base_url = 'https://google.serper.dev/search'
        if not self.api_key:
            logger.warning('SerperAPI key not found. Set SERPERAPI_KEY environment variable or pass api_key parameter.')

    def _build_serperapi_payload(self, query: str, location: str=None, language: str=None, country: str=None, num_results: int=None) -> Dict[str, Any]:
        """
        Build SerperAPI request payload.
        
        Args:
            query (str): Search query
            location (str): Geographic location
            language (str): Interface language
            country (str): Country code
            num_results (int): Number of results to retrieve
            
        Returns:
            Dict[str, Any]: SerperAPI request payload
        """
        payload = {'q': query}
        if num_results:
            payload['num'] = num_results
        if location or self.default_location:
            payload['location'] = location or self.default_location
        if language or self.default_language:
            payload['hl'] = language or self.default_language
        if country or self.default_country:
            payload['gl'] = country or self.default_country
        return payload

    def _execute_serperapi_search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute search using direct HTTP POST requests to SerperAPI.
        
        Args:
            payload (Dict[str, Any]): Search payload
            
        Returns:
            Dict[str, Any]: SerperAPI response data
            
        Raises:
            Exception: For API errors
        """
        try:
            headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise Exception(f'SerperAPI error: {data['error']}')
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f'SerperAPI request failed: {str(e)}')
        except Exception as e:
            raise Exception(f'SerperAPI search failed: {str(e)}')

    def _process_serperapi_results(self, serperapi_data: Dict[str, Any], max_content_words: int=None) -> Dict[str, Any]:
        """
        Process SerperAPI results into structured format with processed results + raw data.
        
        Args:
            serperapi_data (Dict[str, Any]): Raw SerperAPI response
            max_content_words (int): Maximum words per result content
            
        Returns:
            Dict[str, Any]: Structured response with processed results and raw data
        """
        processed_results = []
        if (knowledge_graph := serperapi_data.get('knowledgeGraph', {})):
            if (description := knowledge_graph.get('description')):
                title = knowledge_graph.get('title', 'Unknown')
                content = f'**{title}**\n\n{description}'
                if (attributes := knowledge_graph.get('attributes', {})):
                    content += '\n\n**Key Information:**'
                    for key, value in list(attributes.items())[:5]:
                        formatted_key = key.replace('_', ' ').title()
                        content += f'\n• {formatted_key}: {value}'
                processed_results.append({'title': f'Knowledge: {title}', 'content': self._truncate_content(content, max_content_words or 200), 'url': knowledge_graph.get('descriptionLink', ''), 'type': 'knowledge_graph', 'priority': 1})
        for item in serperapi_data.get('organic', []):
            url = item.get('link', '')
            title = item.get('title', 'No Title')
            snippet = item.get('snippet', '')
            position = item.get('position', 0)
            result = {'title': title, 'content': self._truncate_content(snippet, max_content_words or 400), 'url': url, 'type': 'organic', 'priority': 2, 'position': position}
            if self.enable_content_scraping and url and url.startswith(('http://', 'https://')):
                try:
                    scraped_title, scraped_content = self._scrape_page(url)
                    if scraped_content and scraped_content.strip():
                        if scraped_title and scraped_title.strip():
                            result['title'] = scraped_title
                        result['site_content'] = self._truncate_content(scraped_content, max_content_words or 400)
                    else:
                        result['site_content'] = None
                except Exception as e:
                    logger.debug(f'Content scraping failed for {url}: {str(e)}')
                    result['site_content'] = None
            else:
                result['site_content'] = None
            if snippet or result.get('site_content'):
                processed_results.append(result)
        raw_data = {}
        raw_sections = ['relatedSearches']
        for section in raw_sections:
            if section in serperapi_data and serperapi_data[section]:
                raw_data[section] = serperapi_data[section][:5]
        search_metadata = {}
        if (search_params := serperapi_data.get('searchParameters', {})):
            search_metadata = {'query': search_params.get('q', ''), 'engine': search_params.get('engine', ''), 'type': search_params.get('type', ''), 'credits': serperapi_data.get('credits', 0)}
        processed_results.sort(key=lambda x: (x.get('priority', 999), x.get('position', 0)))
        return {'results': processed_results, 'raw_data': raw_data if raw_data else None, 'search_metadata': search_metadata if search_metadata else None, 'error': None}

    def _handle_api_errors(self, error: Exception) -> str:
        """
        Handle SerperAPI specific errors with appropriate messages.
        
        Args:
            error (Exception): The exception that occurred
            
        Returns:
            str: User-friendly error message
        """
        error_str = str(error).lower()
        if 'api key' in error_str or 'unauthorized' in error_str:
            return 'Invalid or missing SerperAPI key. Please set SERPERAPI_KEY environment variable.'
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            return 'SerperAPI rate limit exceeded. Please try again later.'
        elif 'quota' in error_str or 'credit' in error_str:
            return 'SerperAPI quota exceeded. Please check your plan limits.'
        elif 'timeout' in error_str:
            return 'SerperAPI request timeout. Please try again.'
        else:
            return f'SerperAPI error: {str(error)}'

    def search(self, query: str, num_search_pages: int=None, max_content_words: int=None, location: str=None, language: str=None, country: str=None) -> Dict[str, Any]:
        """
        Search using SerperAPI with comprehensive parameter support.
        
        Args:
            query (str): The search query
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            location (str): Geographic location for localized results
            language (str): Interface language (e.g., 'en', 'es', 'fr')
            country (str): Country code for country-specific results (e.g., 'us', 'uk')
            
        Returns:
            Dict[str, Any]: Contains search results and optional error message
        """
        num_search_pages = num_search_pages or self.num_search_pages
        max_content_words = max_content_words or self.max_content_words
        if not self.api_key:
            error_msg = 'SerperAPI key is required. Please set SERPERAPI_KEY environment variable or pass api_key parameter. Get your key from: https://serper.dev/'
            logger.error(error_msg)
            return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}
        try:
            logger.info(f'Searching SerperAPI: {query}, num_results={num_search_pages}, max_content_words={max_content_words}')
            payload = self._build_serperapi_payload(query=query, location=location, language=language, country=country, num_results=num_search_pages)
            serperapi_data = self._execute_serperapi_search(payload)
            response_data = self._process_serperapi_results(serperapi_data, max_content_words)
            logger.info(f'Successfully retrieved {len(response_data['results'])} processed results')
            return response_data
        except Exception as e:
            error_msg = self._handle_api_errors(e)
            logger.error(f'SerperAPI search failed: {error_msg}')
            return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}

def search(self, query: str, num_search_pages: int=None, max_content_words: int=None, location: str=None, language: str=None, country: str=None) -> Dict[str, Any]:
    """
        Search using SerperAPI with comprehensive parameter support.
        
        Args:
            query (str): The search query
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            location (str): Geographic location for localized results
            language (str): Interface language (e.g., 'en', 'es', 'fr')
            country (str): Country code for country-specific results (e.g., 'us', 'uk')
            
        Returns:
            Dict[str, Any]: Contains search results and optional error message
        """
    num_search_pages = num_search_pages or self.num_search_pages
    max_content_words = max_content_words or self.max_content_words
    if not self.api_key:
        error_msg = 'SerperAPI key is required. Please set SERPERAPI_KEY environment variable or pass api_key parameter. Get your key from: https://serper.dev/'
        logger.error(error_msg)
        return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}
    try:
        logger.info(f'Searching SerperAPI: {query}, num_results={num_search_pages}, max_content_words={max_content_words}')
        payload = self._build_serperapi_payload(query=query, location=location, language=language, country=country, num_results=num_search_pages)
        serperapi_data = self._execute_serperapi_search(payload)
        response_data = self._process_serperapi_results(serperapi_data, max_content_words)
        logger.info(f'Successfully retrieved {len(response_data['results'])} processed results')
        return response_data
    except Exception as e:
        error_msg = self._handle_api_errors(e)
        logger.error(f'SerperAPI search failed: {error_msg}')
        return {'results': [], 'raw_data': None, 'search_metadata': None, 'error': error_msg}

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

def get_evaluation_record_by_id(self, benchmark: Benchmark, example_id: str, eval_mode: str='test') -> Optional[dict]:
    """
        Get the evaluation record for a given example id.
        """
    example = benchmark.get_example_by_id(example_id=example_id, mode=eval_mode)
    return self.get_example_evaluation_record(benchmark=benchmark, example=example)

def _cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    if len(a) < len(b):
        a, b = (b, a)
    return sum((v * b.get(k, 0.0) for k, v in a.items()))

def _norm(d: Dict[str, float]) -> Dict[str, float]:
    s = sum((d.get(w, 0.0) for w in vocab)) or 1.0
    return {w: (d.get(w, 0.0) + eps) / (s + eps * len(vocab)) for w in vocab}

def _kl(X, Y):
    return sum((X[w] * math.log((X[w] + eps) / (Y[w] + eps)) for w in vocab))

def _insert_meta(table: str, colum: List[str]) -> str:
    """
    Generates SQL to insert metadata into a table.

    Attributes:
        table (str): The name of the table.
        colum (List[str]): List of column names.

    Returns:
        str: SQL statement for inserting data.
    """
    value_ = ', '.join(['?'] * len(colum))
    insert_string = f'\n    INSERT INTO {table} ({', '.join([f'"{c}"' for c in colum])})\n    VALUES ({value_})'
    return insert_string

class SEWWorkFlowScheme:
    """
    The scheme of the workflow for SEW optimizer.
    """

    def __init__(self, graph: SequentialWorkFlowGraph, **kwargs):
        self.graph = graph
        self.kwargs = kwargs

    def convert_to_scheme(self, scheme: str) -> str:
        """
        Transform the WorkflowGraph to the desired scheme.
        """
        if scheme not in VALID_SCHEMES:
            raise ValueError(f'Invalid scheme: {scheme}. The scheme should be one of {VALID_SCHEMES}.')
        if scheme == 'python':
            repr = self.get_workflow_python_repr()
        elif scheme == 'yaml':
            repr = self.get_workflow_yaml_repr()
        elif scheme == 'code':
            repr = self.get_workflow_code_repr()
        elif scheme == 'core':
            repr = self.get_workflow_core_repr()
        elif scheme == 'bpmn':
            repr = self.get_workflow_bpmn_repr()
        return repr

    def parse_from_scheme(self, scheme: str, repr: str) -> SequentialWorkFlowGraph:
        """
        Parse the SequentialWorkFlowGraph from the given scheme and representation.
        """
        if scheme not in VALID_SCHEMES:
            raise ValueError(f'Invalid scheme: {scheme}. The scheme should be one of {VALID_SCHEMES}.')
        if scheme == 'python':
            graph = self.parse_workflow_python_repr(repr)
        elif scheme == 'yaml':
            graph = self.parse_workflow_yaml_repr(repr)
        elif scheme == 'code':
            graph = self.parse_workflow_code_repr(repr)
        elif scheme == 'core':
            graph = self.parse_workflow_core_repr(repr)
        elif scheme == 'bpmn':
            graph = self.parse_workflow_bpmn_repr(repr)
        return graph

    def _get_workflow_repr_info(self) -> List[dict]:
        """
        Get the information for the workflow representation.
        """
        info = []
        for node in self.graph.nodes:
            task_name = node.name
            input_names = [param.name for param in node.inputs]
            output_names = [param.name for param in node.outputs]
            task_info = {'task_name': task_name, 'input_names': input_names, 'output_names': output_names}
            info.append(task_info)
        return info

    def _convert_to_func_name(self, name: str) -> str:
        """
        Convert the task name to the function name.
        """
        name = name.lower().strip()
        name = name.replace(' ', '_').replace('-', '_')
        name = ''.join((c for c in name if c.isalnum() or c == '_'))
        name = regex.sub('_+', '_', name)
        name = name.strip('_')
        return name

    def _convert_to_title(self, name: str) -> str:
        func_name = self._convert_to_func_name(name)
        words = func_name.split('_')
        return ' '.join((word.capitalize() for word in words))

    def get_workflow_python_repr(self) -> str:
        repr_info = self._get_workflow_repr_info()
        if not repr_info:
            return ''
        python_workflow_info = []
        for task_info in repr_info:
            name = self._convert_to_func_name(task_info['task_name'])
            input_names = [f'{input_name}' for input_name in task_info['input_names']]
            output_names = [f'{output_name}' for output_name in task_info['output_names']]
            python_workflow_info.append("{{'name': '{name}', 'args': {args}, 'outputs': {outputs}}}".format(name=name, args=input_names, outputs=output_names))
        python_workflow_repr = 'steps = [\n' + ',\n'.join(python_workflow_info) + '\n]'
        return python_workflow_repr

    def get_workflow_yaml_repr(self) -> str:
        repr_info = self._get_workflow_repr_info()
        if not repr_info:
            return ''
        yaml_workflow_info = []
        for task_info in repr_info:
            name = self._convert_to_func_name(task_info['task_name'])
            input_names = '\n'.join([f'    - {input_name}' for input_name in task_info['input_names']])
            output_names = '\n'.join([f'    - {output_name}' for output_name in task_info['output_names']])
            yaml_workflow_info.append('- name: {name}\n  args:\n{input_names}\n  outputs:\n{output_names}'.format(name=name, input_names=input_names, output_names=output_names))
        yaml_workflow_repr = '\n\n'.join(yaml_workflow_info)
        return yaml_workflow_repr

    def get_workflow_code_repr(self) -> str:
        repr_info = self._get_workflow_repr_info()
        if not repr_info:
            return ''
        workflow_lines = []
        for task_info in repr_info:
            name = self._convert_to_func_name(task_info['task_name'])
            inputs = ', '.join(task_info['input_names'])
            outputs = ', '.join(task_info['output_names'])
            line = f'{name}({inputs}) -> {outputs}'
            workflow_lines.append(line)
        workflow_repr = '\n'.join(workflow_lines)
        return workflow_repr

    def get_workflow_bpmn_repr(self) -> str:
        repr_info = self._get_workflow_repr_info()
        if not repr_info:
            return ''
        bpmn_lines = ['<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">', '<process id="software_dev_workflow" isExecutable="true">', '    <startEvent id="start" />']
        for i, task_info in enumerate(repr_info):
            task_name = self._convert_to_func_name(task_info['task_name'])
            task_title = self._convert_to_title(task_info['task_name'])
            bpmn_lines.append(f'    <task id="{task_name}" name="{task_title}" />')
        bpmn_lines.append('    <endEvent id="end" />')
        bpmn_lines.append('')
        bpmn_lines.append('    <!-- Workflow connections -->')
        if repr_info:
            first_task_id = self._convert_to_func_name(repr_info[0]['task_name'])
            bpmn_lines.append(f'    <sequenceFlow id="flow1" sourceRef="start" targetRef="{first_task_id}" />')
        for i in range(len(repr_info) - 1):
            source_id = self._convert_to_func_name(repr_info[i]['task_name'])
            target_id = self._convert_to_func_name(repr_info[i + 1]['task_name'])
            flow_num = i + 2
            bpmn_lines.append(f'    <sequenceFlow id="flow{flow_num}" sourceRef="{source_id}" targetRef="{target_id}" />')
        if repr_info:
            last_task_id = self._convert_to_func_name(repr_info[-1]['task_name'])
            flow_num = len(repr_info) + 1
            bpmn_lines.append(f'    <sequenceFlow id="flow{flow_num}" sourceRef="{last_task_id}" targetRef="end" />')
        bpmn_lines.append('</process>')
        bpmn_lines.append('</definitions>')
        return '\n'.join(bpmn_lines)

    def get_workflow_core_repr(self) -> str:
        repr_info = self._get_workflow_repr_info()
        if not repr_info:
            return ''
        workflow_lines = []
        for i, task_info in enumerate(repr_info, 1):
            task_name = self._convert_to_title(task_info['task_name'])
            next_step = i + 1
            line = f'Step {i}::: Process ::: {task_name}:::next::Step {next_step}'
            workflow_lines.append(line)
        last_step = len(repr_info) + 1
        workflow_lines.append(f'Step {last_step}::: Terminal ::: End of Workflow:::')
        return '\n'.join(workflow_lines)

    def _find_task_index(self, step: dict, graph_repr_info: List[dict]) -> int:
        """
        Find the index of the task in the original workflow graph. If the task is not found, return -1. 

        Args:
            step (dict): The step of the workflow.
            graph_repr_info (List[dict]): The information of the original workflow graph.
        
        Returns:
            int: The index of the task.
        """

        def _is_task_name_match(task_name: str, another_name: str) -> bool:
            return self._convert_to_func_name(task_name) == self._convert_to_func_name(another_name)

        def _is_task_inputs_match(task_inputs: List[str], another_inputs: List[str]) -> bool:
            return len(set(task_inputs) & set(another_inputs)) == len(task_inputs)

        def _is_task_outputs_match(task_outputs: List[str], another_outputs: List[str]) -> bool:
            return len(set(task_outputs) & set(another_outputs)) == len(task_outputs)
        for i, task in enumerate(graph_repr_info):
            if _is_task_name_match(task['task_name'], step['name']) and _is_task_inputs_match(task['input_names'], step['args']) and _is_task_outputs_match(task['output_names'], step['outputs']):
                return i
        return -1

    def create_workflow_graph_from_steps(self, steps: List[dict]) -> SequentialWorkFlowGraph:
        """
        Create a new workflow graph from the steps.
        Since both the inputs and outputs are provided, new tasks will be created in the new workflow graph. 
        It is used for the `python` `yaml` and `code` representations. 

        Args:
            steps (List[dict]): The steps of the workflow. The steps are in the format of:
                [
                    {
                        "name": str,
                        "args": List[str],
                        "outputs": List[str]
                    }
                ]
        
        Returns:
            SequentialWorkFlowGraph: The new workflow graph.
        """
        original_workflow_config = self.graph.get_graph_info()
        repr_info = self._get_workflow_repr_info()
        new_tasks = []
        for step in steps:
            task_index = self._find_task_index(step=step, graph_repr_info=repr_info)
            if task_index == -1:
                task_name = step['name']
                description = f'Task to {task_name.lower()}. '
                if step['args']:
                    description += f'Takes {', '.join(step['args'])} as input. '
                if step['outputs']:
                    description += f'Produces {', '.join(step['outputs'])} as output.'
                new_task = {'name': task_name, 'description': description, 'inputs': [{'name': input_name, 'type': 'str', 'description': f'Input parameter {input_name} for {task_name}'} for input_name in step['args']], 'outputs': [{'name': output_name, 'type': 'str', 'description': f'Output parameter {output_name} from {task_name}'} for output_name in step['outputs']], 'prompt': 'to be updated', 'llm_config': original_workflow_config['tasks'][0]['llm_config'], 'parse_mode': 'str'}
                new_tasks.append(new_task)
            else:
                new_tasks.append(deepcopy(original_workflow_config['tasks'][task_index]))
        new_workflow_config = {'goal': original_workflow_config['goal'], 'tasks': new_tasks}
        new_graph = SequentialWorkFlowGraph.from_dict(new_workflow_config)
        return new_graph

    def create_workflow_graph_from_task_names(self, task_names: Optional[List[str]]=None, task_titles: Optional[List[str]]=None) -> SequentialWorkFlowGraph:
        """
        Create a new workflow graph from the task names or titles. 
        Since only the task names or titles are provided, the tasks in the new workflow graph will be copied from the original workflow graph. 
        It is used for the `bpmn` and `core` representations. 

        Args:
            task_names (Optional[List[str]]): The names of the tasks.
            task_titles (Optional[List[str]]): The titles of the tasks.
        
        Returns:
            SequentialWorkFlowGraph: The new workflow graph.
        """
        if task_names:
            original_workflow_config = self.graph.get_graph_info()
            tasks = task_names
            original_tasks = {self._convert_to_func_name(task['name']): task for task in original_workflow_config['tasks']}
        elif task_titles:
            original_workflow_config = self.graph.get_graph_info()
            tasks = task_titles
            original_tasks = {self._convert_to_title(task['name']): task for task in original_workflow_config['tasks']}
        else:
            raise ValueError('No task names or titles provided.')
        new_tasks = []
        for task in tasks:
            if task not in original_tasks:
                raise ValueError(f'Task {task} not found in the original workflow.')
            new_tasks.append(deepcopy(original_tasks[task]))
        new_workflow_config = {'goal': original_workflow_config['goal'], 'tasks': new_tasks}
        new_graph = SequentialWorkFlowGraph.from_dict(new_workflow_config)
        return new_graph

    def parse_workflow_python_repr(self, repr: str) -> SequentialWorkFlowGraph:
        """
        Parse the workflow from the python representation. The input format is:
        steps = [
            {"name": task_name, "args": [input1, input2, ...],"outputs": [output1, output2, ...]}, 
            {"name": another_task_name, "args": [input1, input2, ...],"outputs": [output1, output2, ...]}, 
            ...
        ]
        """
        try:
            code_block = regex.search('```python\\s*(.*?)\\s*```', repr, regex.DOTALL)
            if not code_block:
                raise ValueError('No Python code block found in the representation')
            code_block = code_block.group(1).strip()
            steps = eval(code_block.replace('steps = ', '').strip())
            new_graph = self.create_workflow_graph_from_steps(steps=steps)
            return new_graph
        except Exception as e:
            logger.warning(f'Failed to parse workflow string: {e}. Return the original workflow.')
        return self.graph

    def parse_workflow_yaml_repr(self, repr: str) -> SequentialWorkFlowGraph:
        """
        Parse the workflow from the yaml representation. The input format is:
        - name: task_name
          args:
            - input1
            - input2
          outputs:
            - output1
        """
        try:
            match = regex.search('```yaml\\s*(.*?)\\s*```', repr, regex.DOTALL)
            if not match:
                raise ValueError('No YAML code block found in the representation')
            yaml_block = match.group(1).strip()
            steps = yaml.safe_load(yaml_block)
            new_graph = self.create_workflow_graph_from_steps(steps=steps)
            return new_graph
        except Exception as e:
            logger.warning(f'Failed to parse workflow string: {e}. Return the original workflow.')
        return self.graph

    def parse_workflow_code_repr(self, repr: str) -> SequentialWorkFlowGraph:
        """
        Parse the workflow from the code representation. 
        The input format is:
        task_name(input1, input2, ...) -> output1, output2, ...
        another_task_name(input1, input2, ...) -> output1, output2, ...
        ...
        """
        try:
            match = regex.search('```code\\s*(.*?)\\s*```', repr, regex.DOTALL)
            if not match:
                raise ValueError('No code block found in the representation')
            code_block = match.group(1).strip()
            lines = [line.strip() for line in code_block.split('\n') if line.strip() and '->' in line]
            steps = []
            for line in lines:
                line = regex.sub('^\\d+\\.\\s*', '', line)
                func_part, output_part = line.split('->')
                func_part = func_part.strip()
                name = func_part[:func_part.index('(')]
                args_str = func_part[func_part.index('(') + 1:func_part.rindex(')')]
                args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
                outputs = [out.strip() for out in output_part.split(',') if out.strip()]
                step = {'name': name, 'args': args, 'outputs': outputs}
                steps.append(step)
            if not steps:
                raise ValueError('No steps found in the workflow.')
            new_graph = self.create_workflow_graph_from_steps(steps=steps)
            return new_graph
        except Exception as e:
            logger.warning(f'Failed to parse workflow string: {e}. Return the original workflow.')
        return self.graph

    def parse_workflow_bpmn_repr(self, repr: str) -> SequentialWorkFlowGraph:
        """
        Parse the workflow from the BPMN XML representation.
        
        The input format is BPMN XML with:
        - task elements defining the tasks
        - sequenceFlow elements defining the order of tasks
        
        Will extract ordered task names from the sequence flows and create a workflow.
        """
        try:
            match = regex.search('```bpmn\\s*(.*?)\\s*```', repr, regex.DOTALL)
            if not match:
                raise ValueError('No BPMN code block found in the representation')
            bpmn_block = match.group(1).strip()
            root = ET.fromstring(bpmn_block)
            ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
            process = root.find('bpmn:process', ns) or root.find('process')
            if process is None:
                raise ValueError('No process element found in BPMN XML')
            tasks = {}
            for task in process.findall('bpmn:task', ns):
                tasks[task.get('id')] = task.get('name')
            flows = {}
            ordered_tasks = []
            current_ref = 'start'
            for flow in process.findall('bpmn:sequenceFlow', ns):
                flows[flow.get('sourceRef')] = flow.get('targetRef')
            while current_ref in flows:
                next_ref = flows[current_ref]
                if next_ref in tasks:
                    ordered_tasks.append(tasks[next_ref])
                current_ref = next_ref
            new_graph = self.create_workflow_graph_from_task_names(task_titles=ordered_tasks)
            return new_graph
        except Exception as e:
            logger.warning(f'Failed to parse BPMN workflow string: {e}. Return the original workflow.')
        return self.graph

    def parse_workflow_core_repr(self, repr: str) -> SequentialWorkFlowGraph:
        """
        Parse the workflow from the Core representation.
        
        The input format is:
        Step 1::: Process ::: Task Name:::next::Step 2
        Step 2::: Process ::: Another Task:::next::Step 3
        ...
        Step N::: Terminal ::: End of Workflow:::
        
        Will extract task names from Process steps and create a workflow.
        """
        try:
            match = regex.search('```core\\s*(.*?)\\s*```', repr, regex.DOTALL)
            if not match:
                raise ValueError('No core code block found in the representation')
            core_block = match.group(1).strip()
            lines = [line.strip() for line in core_block.split('\n') if line.strip()]
            flows = {}
            tasks = {}
            for line in lines:
                parts = line.split(':::')
                current_step = parts[0].strip()
                step_type = parts[1].strip()
                if step_type == 'Process':
                    task_title = parts[2].strip()
                    tasks[current_step] = task_title
                    if len(parts) > 3 and 'next' in parts[3]:
                        next_step = parts[3].split('::')[-1].strip()
                        flows[current_step] = next_step
                elif step_type == 'Terminal':
                    flows[current_step] = None
            ordered_tasks = []
            current_step = 'Step 1'
            while current_step in flows:
                if current_step in tasks:
                    ordered_tasks.append(tasks[current_step])
                current_step = flows[current_step]
            new_graph = self.create_workflow_graph_from_task_names(task_titles=ordered_tasks)
            return new_graph
        except Exception as e:
            logger.warning(f'Failed to parse Core workflow string: {e}. Return the original workflow.')
        return self.graph

def parse_from_scheme(self, scheme: str, repr: str) -> SequentialWorkFlowGraph:
    """
        Parse the SequentialWorkFlowGraph from the given scheme and representation.
        """
    if scheme not in VALID_SCHEMES:
        raise ValueError(f'Invalid scheme: {scheme}. The scheme should be one of {VALID_SCHEMES}.')
    if scheme == 'python':
        graph = self.parse_workflow_python_repr(repr)
    elif scheme == 'yaml':
        graph = self.parse_workflow_yaml_repr(repr)
    elif scheme == 'code':
        graph = self.parse_workflow_code_repr(repr)
    elif scheme == 'core':
        graph = self.parse_workflow_core_repr(repr)
    elif scheme == 'bpmn':
        graph = self.parse_workflow_bpmn_repr(repr)
    return graph

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

class AFlowOptimizer(BaseModule):
    """
    AFlow Optimizer for workflow optimization.
    
    This optimizer iteratively improves workflows through multiple rounds of optimization
    using large language models. It evaluates workflow performance, identifies improvement
    opportunities, and applies optimizations based on experience and convergence metrics.
    
    Attributes:
        question_type: Type of task to optimize for (e.g., qa, match, code)
        graph_path: Path to the workflow graph directory (must contain graph.py and prompt.py)
        optimized_path: Path to save optimized workflows (defaults to graph_path)
        initial_round: Starting round number for optimization
        optimizer_llm: LLM used for generating optimizations
        executor_llm: LLM used for executing the workflow
        operators: List of operators available for optimization
        sample: Number of rounds to sample from for optimization
        max_rounds: Maximum number of optimization rounds to perform
        validation_rounds: Number of validation runs per optimization round
        eval_rounds: Number of evaluation runs for test mode
        check_convergence: Whether to check for optimization convergence
    """
    question_type: str = Field(description='The type of question to optimize the workflow for, e.g., qa, match, code, etc.')
    graph_path: str = Field(description='The folder of the workflow graph. This folder must contain a `graph.py` file that defines the workflow structure, and a `prompt.py` file that defines the prompt for the workflow.')
    optimized_path: str = Field(default=None, description='The path to save the optimized workflow. If not provided, the optimized path will be the same as the graph path.')
    initial_round: int = Field(default=0, description='The round number to start or continue optimization from. If not provided, will start from round 0 using the `graph.py` file in `graph_path`.')
    optimizer_llm: BaseLLM = Field(default=None, description='The LLM to use for optimization.')
    executor_llm: BaseLLM = Field(default=None, description='The LLM to use for execution.')
    operators: List[str] = Field(default_factory=lambda: list(OPERATOR_MAP.keys()), description='The operators to use for optimization. If not provided, will use all operators in OPERATOR_MAP.')
    sample: int = Field(default=4, description='The number of rounds to sample from the top scores.')
    max_rounds: int = Field(default=20, description='The maximum number of rounds to optimize the workflow.')
    validation_rounds: int = Field(default=5, description='Run the workflow for `validation_rounds` times to evaluate the performance on the validation set.')
    eval_rounds: int = Field(default=3, description='Run the workflow for `eval_rounds` times to evaluate the performance on the test set.')
    check_convergence: bool = Field(default=True, description='Whether to check for convergence.')

    def init_module(self, **kwargs):
        self.root_path = self.optimized_path or self.graph_path
        os.makedirs(self.root_path, exist_ok=True)
        self.graph_utils = GraphUtils(self.root_path)
        self.data_utils = DataUtils(self.root_path)
        self.evaluation_utils = EvaluationUtils(self.root_path)
        self.experience_utils = ExperienceUtils(self.root_path)
        self.convergence_utils = ConvergenceUtils(self.root_path)
        self.graph = None
        self.round = self.initial_round
        if self.round == 0:
            round_zero_path = os.path.join(self.root_path, f'round_{self.round}')
            os.makedirs(round_zero_path, exist_ok=True)
            shutil.copy2(os.path.join(self.graph_path, 'graph.py'), os.path.join(round_zero_path, 'graph.py'))
            shutil.copy2(os.path.join(self.graph_path, 'prompt.py'), os.path.join(round_zero_path, 'prompt.py'))
            self.graph_utils.update_prompt_import(os.path.join(round_zero_path, 'graph.py'), round_zero_path)
        if not os.path.exists(os.path.join(self.root_path, f'round_{self.round}')):
            raise ValueError(f'Round {self.round} does not exist in {self.root_path}')
        if self.optimizer_llm is None:
            raise ValueError('optimizer_llm is not provided')
        if self.executor_llm is None:
            self.executor_llm = self.optimizer_llm

    def optimize(self, benchmark: Benchmark):
        """Run the optimization process on the workflow.
        
        Performs multiple rounds of optimization, evaluating each round against
        the benchmark and checking for convergence. Continues until convergence
        is detected or the maximum number of rounds is reached.
        
        Args:
            benchmark: The benchmark to evaluate the workflow against
        """
        self.benchmark = benchmark
        for _ in range(self.max_rounds):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            score = loop.run_until_complete(self._execute_with_retry(self._optimize_graph))
            self.round += 1
            logger.info(f'Score for round {self.round}: {score}')
            if self._check_convergence():
                break
            if self.round >= self.max_rounds:
                logger.info(f'Max rounds reached: {self.max_rounds}, stopping optimization.')
                break

    def test(self, benchmark: Benchmark, test_rounds: List[int]=None):
        """Run the test evaluation on optimized workflows.
        
        Evaluates specified rounds (or the best round if none specified) against
        the benchmark multiple times and logs the results.
        
        Args:
            benchmark: The benchmark to evaluate against
            test_rounds: Specific round numbers to test, or None to use the best round
        """
        self.benchmark = benchmark
        if test_rounds is None:
            best_round = self._load_best_round()
            logger.info(f'No test rounds provided, using best round: {best_round}')
            test_rounds = [best_round]
        for _ in tqdm(range(self.eval_rounds)):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_test(test_rounds))

    async def _execute_with_retry(self, func: callable, max_retries: int=3) -> Any:
        retry_count = 0
        while retry_count < max_retries:
            try:
                return await func()
            except Exception as e:
                retry_count += 1
                logger.info(f'Error occurred: {e}. Retrying... (Attempt {retry_count}/{max_retries})')
                if retry_count == max_retries:
                    logger.info('Max retries reached.')
                    return None
                await asyncio.sleep(5 * retry_count)
        return None

    def _check_convergence(self) -> bool:
        if not self.check_convergence:
            return False
        converged, convergence_round, final_round = self.convergence_utils.check_convergence(top_k=3)
        if converged:
            logger.info(f'Convergence detected, occurred in round {convergence_round}, final round is {final_round}')
            self.convergence_utils.print_results()
            return True
        return False

    async def _optimize_graph(self) -> float:
        """Optimize the graph for one round"""
        validation_n = self.validation_rounds
        graph_path = self.root_path
        data = self.data_utils.load_results(graph_path)
        if self.round == 0:
            self.avg_score = await self._handle_initial_round(graph_path, validation_n, data)
        return await self._handle_optimization_round(graph_path, validation_n, data)

    async def _handle_initial_round(self, graph_path: str, validation_n: int, data: list) -> float:
        """Handle the initial round of optimization"""
        self.graph_utils.create_round_directory(graph_path, self.round)
        self.graph = self.graph_utils.load_graph(self.round, graph_path)
        return await self.evaluation_utils.evaluate_graph_async(self, validation_n, data, initial=True)

    async def _handle_optimization_round(self, graph_path: str, validation_n: int, data: list) -> float:
        directory = self.graph_utils.create_round_directory(graph_path, self.round + 1)
        while True:
            sample = self._get_optimization_sample()
            prompt, graph_load = self.graph_utils.read_graph_files(sample['round'], graph_path)
            graph = self.graph_utils.extract_solve_graph(graph_load)
            processed_experience = self.experience_utils.load_experience()
            experience = self.experience_utils.format_experience(processed_experience, sample['round'])
            operator_description = self.graph_utils.load_operators_description(self.operators, self.optimizer_llm)
            log_data = self.data_utils.load_log(sample['round'])
            graph_optimize_prompt = self.graph_utils.create_graph_optimize_prompt(experience, sample['score'], graph[0], prompt, operator_description, self.question_type, log_data)
            response = await self.optimizer_llm.async_generate(prompt=graph_optimize_prompt, parse_mode='str')
            print(response.content)
            try:
                parsed_response = GraphOptimizeOutput.parse(response.content, parse_mode='xml')
                response = parsed_response.get_structured_data()
            except Exception:
                response = self._parse_optimizer_llm_output(response.content, orig_graph=graph[0], orig_prompt=prompt)
            if self.experience_utils.check_modification(processed_experience, response['modification'], sample['round']):
                break
        avg_score = await self._evaluate_and_save_optimization_results(directory, response, sample, data, validation_n)
        return avg_score

    def _get_optimization_sample(self) -> dict:
        top_rounds = self.data_utils.get_top_rounds(self.sample)
        return self.data_utils.select_round(top_rounds)

    def _parse_optimizer_llm_output(self, content: str, orig_graph: str, orig_prompt: str) -> dict:
        response = {'modification': '', 'graph': '', 'prompt': ''}
        modification_pattern = '<modification>(.*?)</modification>'
        modification_match = re.search(modification_pattern, content, re.DOTALL)
        if modification_match:
            response['modification'] = modification_match.group(1).strip()
        code_block_pattern = '```(?:python)?(.*?)```'
        code_blocks = re.finditer(code_block_pattern, content, re.DOTALL)
        for block in code_blocks:
            code = block.group(1).strip()
            if 'class' in code or 'workflow' in code.lower():
                response['graph'] = code
            else:
                response['prompt'] = code
        if not response['graph'] and (not response['prompt']):
            response['modification'] = 'No modification due to error in LLM output'
            response['graph'] = orig_graph
            response['prompt'] = orig_prompt
        return response

    async def _evaluate_and_save_optimization_results(self, directory: str, response: dict, sample: dict, data: list, validation_n: int):
        self.graph_utils.write_graph_files(directory, response)
        experience = self.experience_utils.create_experience_data(sample, response['modification'])
        self.graph = self.graph_utils.load_graph(self.round + 1, self.root_path)
        avg_score = await self.evaluation_utils.evaluate_graph_async(self, validation_n, data, initial=False)
        self.experience_utils.update_experience(directory, experience, avg_score)
        return avg_score

    def _load_best_round(self) -> int:
        """Load the best round"""
        ranked_scores = self.data_utils._load_scores()
        return ranked_scores[0]['round']

    async def _run_test(self, test_rounds: List[int]):
        """Run test evaluation"""
        logger.info('Running test evaluation...')
        graph_path = self.root_path
        data = self.data_utils.load_results(graph_path)
        json_file_path = self.data_utils.get_results_file_path(graph_path)
        scores = []
        for round in test_rounds:
            logger.info(f'Running test for round {round}...')
            self.graph = self.graph_utils.load_graph(round, graph_path)
            score, avg_cost, total_cost = await self.evaluation_utils.evaluate_graph_test_async(self)
            scores.append(score)
            new_data = self.data_utils.create_result_data(round, score, avg_cost, total_cost)
            data.append(new_data)
            logger.info(f'Test round {round} score: {score}, avg_cost: {avg_cost}, total_cost: {total_cost}')
            self.data_utils.save_results(json_file_path, data)
        logger.info(f'Test round {round} avg_score: {np.mean(scores)}')
        return np.mean(scores)

def _load_best_round(self) -> int:
    """Load the best round"""
    ranked_scores = self.data_utils._load_scores()
    return ranked_scores[0]['round']

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

class MiproEvaluatorWrapper(MiproEvaluator):

    def __init__(self, evaluator: Evaluator, benchmark: Benchmark, metric_name: str=None, return_all_scores: bool=False, return_outputs: bool=False):
        self.evaluator = evaluator
        self.benchmark = benchmark
        self.metric_name = metric_name
        self.return_all_scores = return_all_scores
        self.return_outputs = return_outputs

    def metric(self, example: dspy.Example, prediction: Any, *args, **kwargs):
        return super().metric(example, prediction, *args, **kwargs)

    def __call__(self, program: PromptTuningModule, evalset: List[dspy.Example], **kwargs) -> float:
        program.sync_predict_inputs_to_program()
        return_all_scores = kwargs.get('return_all_scores', None) or self.return_all_scores
        return_outputs = kwargs.get('return_outputs', None) or self.return_outputs
        if isinstance(program, PromptTuningModule):
            graph = program.program.graph
        elif isinstance(program, WorkFlowGraphProgram):
            graph = program.graph
        else:
            raise ValueError(f'Invalid program type: {type(program)}. Must be PromptTuningModule or WorkFlowGraphProgram.')
        self.evaluator._evaluation_records.clear()
        self.evaluator.agent_manager.update_agents_from_workflow(workflow_graph=graph, llm_config=self.evaluator.llm.config, **kwargs)
        if isinstance(self.benchmark.get_train_data()[0], dspy.Example):
            data = evalset
        else:
            data = [example.toDict() for example in evalset]
        with suppress_logger_info():
            metrics = self.evaluator._evaluate_graph(graph=graph, data=data, benchmark=self.benchmark, verbose=True, **kwargs)
        if isinstance(metrics, dict):
            score = self._extract_score_from_dict(metrics)
        else:
            score = metrics
        all_scores, all_predictions = ([], [])
        for example in data:
            example_id = self.benchmark.get_id(example=example)
            evaluation_record = self.evaluator._evaluation_records.get(example_id, None)
            if evaluation_record is None:
                all_scores.append(0.0)
                all_predictions.append(None)
            else:
                example_metrics = evaluation_record['metrics']
                example_score = self._extract_score_from_dict(example_metrics) if isinstance(example_metrics, dict) else example_metrics
                all_scores.append(example_score)
                all_predictions.append(evaluation_record['prediction'])
        if return_all_scores and return_outputs:
            return (score, all_predictions, all_scores)
        if return_all_scores:
            return (score, all_scores)
        if return_outputs:
            return (score, all_predictions)
        return score

def __call__(self, program: PromptTuningModule, evalset: List[dspy.Example], **kwargs) -> float:
    program.sync_predict_inputs_to_program()
    return_all_scores = kwargs.get('return_all_scores', None) or self.return_all_scores
    return_outputs = kwargs.get('return_outputs', None) or self.return_outputs
    if isinstance(program, PromptTuningModule):
        graph = program.program.graph
    elif isinstance(program, WorkFlowGraphProgram):
        graph = program.graph
    else:
        raise ValueError(f'Invalid program type: {type(program)}. Must be PromptTuningModule or WorkFlowGraphProgram.')
    self.evaluator._evaluation_records.clear()
    self.evaluator.agent_manager.update_agents_from_workflow(workflow_graph=graph, llm_config=self.evaluator.llm.config, **kwargs)
    if isinstance(self.benchmark.get_train_data()[0], dspy.Example):
        data = evalset
    else:
        data = [example.toDict() for example in evalset]
    with suppress_logger_info():
        metrics = self.evaluator._evaluate_graph(graph=graph, data=data, benchmark=self.benchmark, verbose=True, **kwargs)
    if isinstance(metrics, dict):
        score = self._extract_score_from_dict(metrics)
    else:
        score = metrics
    all_scores, all_predictions = ([], [])
    for example in data:
        example_id = self.benchmark.get_id(example=example)
        evaluation_record = self.evaluator._evaluation_records.get(example_id, None)
        if evaluation_record is None:
            all_scores.append(0.0)
            all_predictions.append(None)
        else:
            example_metrics = evaluation_record['metrics']
            example_score = self._extract_score_from_dict(example_metrics) if isinstance(example_metrics, dict) else example_metrics
            all_scores.append(example_score)
            all_predictions.append(evaluation_record['prediction'])
    if return_all_scores and return_outputs:
        return (score, all_predictions, all_scores)
    if return_all_scores:
        return (score, all_scores)
    if return_outputs:
        return (score, all_predictions)
    return score

class Document(BaseModule):
    """A custom document class for managing documents in the RAG pipeline.

    Attributes:
        text (str): The full content of the document.
        doc_id (str): Unique identifier for the document.
        metadata (DocumentMetadata): Metadata including file info, creation date, etc.
        source (str): Source of the document (e.g., file path or URL).
        llama_doc (LlamaIndexDocument): Underlying LlamaIndex Document object.
    """

    def __init__(self, text: str, metadata: Optional[Union[Dict, DocumentMetadata]]=None, embedding: Optional[List[float]]=None, doc_id: Optional[str]=None, excluded_embed_metadata_keys: List[str]=DEAFULT_EXCLUDED, excluded_llm_metadata_keys: List[str]=DEAFULT_EXCLUDED, relationships: Dict[str, RelatedNodeInfo]={}, metadata_template: str='{key}: {value}', metadata_separator: str='\n', text_template: str='{metadata_str}\n\n{content}'):
        metadata = DocumentMetadata.model_validate(metadata) if isinstance(metadata, dict) else metadata or DocumentMetadata()
        super().__init__(text=text.strip(), doc_id=doc_id or str(uuid4()), metadata=metadata, embedding=embedding, excluded_embed_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_embed_metadata_keys)), excluded_llm_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_llm_metadata_keys)), relationships=relationships, metadata_template=metadata_template, metadata_separator=metadata_separator, text_template=text_template)
        self.metadata.word_count = len(self.text.split())

    def to_llama_document(self) -> LlamaIndexDocument:
        """Convert to LlamaIndex Document."""
        return LlamaIndexDocument(text=self.text, metadata=self.metadata.model_dump(), id_=self.doc_id, embedding=self.embedding, excluded_llm_metadata_keys=self.excluded_llm_metadata_keys, excluded_embed_metadata_keys=self.excluded_embed_metadata_keys, relationships=self.relationships, metadata_template=self.metadata_template, metadata_separator=self.metadata_separator, text_template=self.text_template)

    @classmethod
    def from_llama_document(cls, llama_doc: LlamaIndexDocument) -> 'Document':
        """Create Document from LlamaIndex Document."""
        metadata = DocumentMetadata.model_validate(llama_doc.metadata)
        return cls(text=llama_doc.text, metadata=metadata, doc_id=llama_doc.id_, embedding=llama_doc.embedding, excluded_llm_metadata_keys=llama_doc.excluded_llm_metadata_keys, excluded_embed_metadata_keys=llama_doc.excluded_llm_metadata_keys, relationships=llama_doc.relationships, metadata_template=llama_doc.metadata_template, metadata_separator=llama_doc.metadata_separator, text_template=llama_doc.text_template)

    def set_embedding(self, embedding: List[float]):
        """Set the embedding vector for the Document."""
        self.embedding = embedding

    def compute_hash(self) -> str:
        """Compute a hash of the document text for deduplication."""
        return hashlib.sha256(self.text.encode()).hexdigest()

    def get_fragment(self, max_length: int=100) -> str:
        """Return a fragment of the document text."""
        return self.text[:max_length] + '...' if len(self.text) > max_length else self.text

    def to_dict(self) -> Dict:
        """Convert document to dictionary for serialization."""
        return {'doc_id': self.doc_id, 'text': self.text, 'metadata': self.metadata.model_dump(), 'embedding': self.embedding, 'excluded_embed_metadata_keys': self.excluded_embed_metadata_keys, 'excluded_llm_metadata_keys': self.excluded_llm_metadata_keys, 'relationships': {str(k): v for k, v in self.relationships.items()}, 'metadata_template': self.metadata_template, 'metadata_separator': self.metadata_separator, 'text_template': self.text_template}

    def to_json(self, indent: int=2) -> str:
        """Convert document to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __str__(self) -> str:
        return f'Document(id={self.doc_id}, embedding={self.embedding}, metadata={self.metadata.model_dump()}fragment={self.get_fragment(max_length=300)})'

    def __repr__(self) -> str:
        return f'Document(doc_id={self.doc_id}, embedding={self.embedding}, metadata={self.metadata.model_dump()},fragment={self.get_fragment(max_length=300)})'

def get_fragment(self, max_length: int=100) -> str:
    """Return a fragment of the document text."""
    return self.text[:max_length] + '...' if len(self.text) > max_length else self.text

class TextChunk(BaseModule):
    """A single chunk of a document for RAG processing.

    Attributes:
        text (str): The content of the chunk.
        doc_id (str): ID of the parent document.
        chunk_id (str): Unique identifier for the chunk.
        metadata (ChunkMetadata): Metadata including chunk size, embedding, etc.
        llama_node (BaseNode): Underlying LlamaIndex Node object.
    """

    def __init__(self, text: str='', chunk_id: Optional[str]=None, embedding: Optional[List[float]]=None, start_char_idx: Optional[int]=None, end_char_idx: Optional[int]=None, excluded_embed_metadata_keys: List[str]=DEAFULT_EXCLUDED, excluded_llm_metadata_keys: List[str]=DEAFULT_EXCLUDED, text_template: str='{metadata_str}\n\n{content}', relationships: Dict[str, RelatedNodeInfo]={}, metadata: Optional[Union[Dict, ChunkMetadata]]=None):
        metadata = ChunkMetadata.model_validate(metadata) if isinstance(metadata, dict) else metadata or ChunkMetadata()
        super().__init__(text=text.strip(), chunk_id=chunk_id or str(uuid4()), embedding=embedding, start_char_idx=start_char_idx, end_char_idx=end_char_idx, excluded_embed_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_embed_metadata_keys)), excluded_llm_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_llm_metadata_keys)), text_template=text_template, relationships=relationships, metadata=metadata)
        self.metadata.word_count = len(self.text.split())

    def to_llama_node(self) -> Union[TextNode, Relation, EntityNode, ChunkNode]:
        """Convert to LlamaIndex Node."""
        relatiuonships = dict()
        for k, v in self.relationships.items():
            relatiuonships[k] = v if isinstance(v, RelatedNodeInfo) else RelatedNodeInfo.from_dict(v)
        cls = TextNode
        if self.metadata.graph_node is not None:
            class_name = self.metadata.graph_node.node_class_name.lower()
            if class_name == 'relation':
                cls = Relation(label=self.metadata.graph_node.label, source_id=self.metadata.graph_node.source_id, target_id=self.metadata.graph_node.target_id, properties={'metadata': json.dumps(self.metadata.graph_node.properties['metadata'])})
            elif class_name == 'entity':
                cls = EntityNode(label=self.metadata.graph_node.label, embedding=self.embedding, name=self.metadata.graph_node.node_name, properties={'triplet_source_id': self.metadata.graph_node.properties['triplet_source_id']})
            else:
                NotImplementedError()
            return cls
        else:
            metadata = self.metadata.model_dump()
            if 'class_name' in metadata:
                metadata.pop('class_name')
            return cls(text=self.text, metadata=metadata, id_=self.chunk_id, embedding=self.embedding, start_char_idx=self.start_char_idx, end_char_idx=self.end_char_idx, excluded_llm_metadata_keys=self.excluded_llm_metadata_keys, excluded_embed_metadata_keys=self.excluded_embed_metadata_keys, text_template=self.text_template, relationships=relatiuonships)

    @classmethod
    def from_llama_node(cls, node: Union[TextNode, Relation, EntityNode, ChunkNode]) -> 'Chunk':
        """Create Chunk from LlamaIndex Node."""
        if isinstance(node, TextNode):
            return cls(chunk_id=node.id_, text=node.text, metadata=ChunkMetadata.model_validate(node.metadata), embedding=node.embedding, start_char_idx=getattr(node, 'start_char_idx', None), end_char_idx=getattr(node, 'end_char_idx', None), excluded_embed_metadata_keys=node.excluded_embed_metadata_keys, excluded_llm_metadata_keys=node.excluded_llm_metadata_keys, text_template=node.text_template, relationships=node.relationships)
        elif isinstance(node, Relation):
            if 'class_name' in node.properties:
                node.properties.pop('class_name')
            properties = node.properties if isinstance(node.properties, dict) else node.properties.model_dump()
            graph_node = GraphNodeData(node_class_name='relation', label=node.label, source_id=node.source_id, target_id=node.target_id, properties={'metadata': properties})
            metadata = {'graph_node': graph_node}
            return cls(metadata=ChunkMetadata.model_validate(metadata))
        elif isinstance(node, EntityNode):
            graph_node = GraphNodeData(node_class_name='entity', label=node.label, node_name=node.name, properties={'triplet_source_id': node.properties['triplet_source_id']})
            metadata = {'graph_node': graph_node}
            return cls(embedding=node.embedding, metadata=ChunkMetadata.model_validate(metadata))
        elif isinstance(node, ChunkNode):
            graph_node = GraphNodeData(node_class_name='chunk', text=node.text, properties=node.properties, id_=node.id_)
            metadata = {'graph_node': graph_node}
            return cls(embedding=node.embedding, metadata=ChunkMetadata.model_validate(metadata))

    def get_fragment(self, max_length: int=100) -> str:
        """Return a fragment of the chunk text."""
        return self.text[:max_length] + '...' if len(self.text) > max_length else self.text

    def to_dict(self) -> Dict:
        """Convert chunk to dictionary for serialization."""
        relationships = dict()
        for k, v in self.relationships.items():
            relationships[k] = v.to_dict() if isinstance(v, RelatedNodeInfo) else v
        self.relationships = relationships
        return self.model_dump()

    def to_json(self, indent: int=2) -> str:
        """Convert chunk to JSON string."""
        return self.model_dump_json(indent=indent).strip()

    def __str__(self) -> str:
        return f'Chunk(id={self.chunk_id}, text={self.text}, chunking_strategy={self.metadata.chunking_strategy}, embedding={self.embedding}), start_char_idx={self.start_char_idx}, end_char_idx={self.end_char_idx}, excluded_embed_metadata_keys={self.excluded_embed_metadata_keys},excluded_llm_metadata_keys={self.excluded_llm_metadata_keys},text_template={self.text_template},metadata={self.metadata.model_dump()}'

    def __repr__(self) -> str:
        return f'Chunk(id={self.chunk_id}, text={self.text}, chunking_strategy={self.metadata.chunking_strategy}, embedding={self.embedding}), start_char_idx={self.start_char_idx}, end_char_idx={self.end_char_idx}, excluded_embed_metadata_keys={self.excluded_embed_metadata_keys},excluded_llm_metadata_keys={self.excluded_llm_metadata_keys},text_template={self.text_template},metadata={self.metadata.model_dump()}'

def get_fragment(self, max_length: int=100) -> str:
    """Return a fragment of the chunk text."""
    return self.text[:max_length] + '...' if len(self.text) > max_length else self.text

class Corpus(BaseModule):
    """A generic collection of document chunks for RAG processing.

    Attributes:
        corpus_id (str): The unique id for corpus.
        chunks (List[Union[TextChunk, ImageChunk]]): List of chunks in the corpus.
        chunk_index (Dict[str, Union[TextChunk, ImageChunk]]): Index of chunks by chunk_id for fast lookup.
        metadata (Optional[IndexMetadata]): the metadata for this corpus.
    """

    def __init__(self, chunks: Optional[List[Union[TextChunk, ImageChunk]]]=None, corpus_id: Optional[str]=None, metadata: Optional[Union[IndexMetadata, Dict]]=None):
        corpus_id = uuid4() if corpus_id is None else corpus_id
        chunks = [] if chunks is None else chunks
        chunk_index = {} if chunks is None else {chunk.chunk_id: chunk for chunk in chunks}
        if metadata is None:
            metadata = {}
        elif isinstance(metadata, IndexMetadata):
            metadata = metadata.model_dump()
        super().__init__(corpus_id=corpus_id, chunks=chunks, chunk_index=chunk_index, metadata=metadata)

    def to_llama_nodes(self) -> List[BaseNode]:
        """Convert to list of LlamaIndex Nodes."""
        if not self.chunks:
            self.chunks = []
        return [chunk.to_llama_node() for chunk in self.chunks]

    @classmethod
    def from_llama_nodes(cls, nodes: List[BaseNode]) -> 'Corpus':
        """Create a Corpus from a list of LlamaIndex Nodes.

        Args:
            nodes (List[BaseNode]): The LlamaIndex Nodes to convert.

        Returns:
            Corpus: A new Corpus instance.
        """
        chunks = []
        for node in nodes:
            if isinstance(node, ImageNode):
                chunks.append(ImageChunk.from_llama_node(node))
            else:
                chunks.append(TextChunk.from_llama_node(node))
        return cls(chunks)

    def add_chunk(self, batch_chunk: Union[TextChunk, ImageChunk, List[Union[TextChunk, ImageChunk]]]):
        """Add a batch chunk to the corpus and update index."""
        if not isinstance(batch_chunk, list):
            batch_chunk = [batch_chunk]
        for chunk in batch_chunk:
            self.chunks.append(chunk)
            self.chunk_index[chunk.chunk_id] = chunk

    def get_chunk(self, chunk_id: str) -> Optional[Union[TextChunk, ImageChunk]]:
        """Retrieve a chunk by its ID."""
        return self.chunk_index.get(chunk_id)

    def remove_chunk(self, chunk_id: str):
        """Remove a chunk by its ID."""
        self.chunks = [chunk for chunk in self.chunks if chunk.chunk_id != chunk_id]
        self.chunk_index.pop(chunk_id, None)

    def filter_by_doc_id(self, doc_id: str) -> List[Union[TextChunk, ImageChunk]]:
        """Filter chunks by parent document ID."""
        return [chunk for chunk in self.chunks if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id == doc_id]

    def filter_by_similarity(self, threshold: float) -> List[Union[TextChunk, ImageChunk]]:
        """Filter chunks by similarity score."""
        return [chunk for chunk in self.chunks if chunk.metadata.similarity_score and chunk.metadata.similarity_score >= threshold]

    def sort_by_similarity(self, reverse: bool=True) -> List[Union[TextChunk, ImageChunk]]:
        """Sort chunks by similarity score (descending by default)."""
        return sorted([chunk for chunk in self.chunks if chunk.metadata.similarity_score is not None], key=lambda x: x.metadata.similarity_score, reverse=reverse)

    def to_dict(self, round_trip=False) -> Dict:
        """Convert corpus to dictionary for serialization."""
        return [self.model_dump(round_trip=round_trip)]

    def to_json(self, indent: int=2, round_trip=True) -> str:
        """Convert corpus to JSON string."""
        return json.dumps(self.to_dict(round_trip), indent=indent, ensure_ascii=False)

    def to_jsonl(self, output_path: str, indent: int=0):
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in self.chunks:
                json_str = chunk.to_json(indent=None)
                if '\n' in json_str:
                    print(f'Chunk {chunk.chunk_id} contains newlines in JSON, which may break JSONL format.')
                f.write(json_str + '\n')

    @classmethod
    def from_jsonl(cls, input_path: str, corpus_id: Optional[str]=None) -> 'Corpus':
        chunks = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunk_dict = json.loads(line.strip())
                metadata = ChunkMetadata.model_validate(chunk_dict['metadata'])
                chunk = Chunk(chunk_id=chunk_dict['chunk_id'], text=chunk_dict['text'], metadata=metadata, embedding=chunk_dict['embedding'], start_char_idx=chunk_dict['start_char_idx'], end_char_idx=chunk_dict['end_char_idx'], excluded_embed_metadata_keys=chunk_dict['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_dict['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_dict['relationships'].items()})
                chunks.append(chunk)
        return cls(chunks=chunks, corpus_id=corpus_id)

    def __str__(self) -> str:
        stats = self.get_stats()
        return f'Corpus(chunks={stats['chunk_count']}, unique_docs={stats['unique_docs']}, avg_word_count={stats['avg_word_count']:.1f}, strategies={stats['strategies']})'

    def __repr__(self) -> str:
        return f'Corpus(chunks={len(self.chunks)}, chunk_index_keys={list(self.chunk_index.keys())})'

    def __len__(self) -> int:
        return len(self.chunks)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the corpus."""
        if not self.chunks:
            return {'chunk_count': 0, 'unique_docs': 0, 'avg_word_count': 0.0, 'strategies': set()}
        unique_docs = set()
        total_word_count = 0
        strategies = set()
        for chunk in self.chunks:
            if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id:
                unique_docs.add(chunk.metadata.doc_id)
            if hasattr(chunk.metadata, 'word_count') and chunk.metadata.word_count:
                total_word_count += chunk.metadata.word_count
            if hasattr(chunk.metadata, 'chunking_strategy') and chunk.metadata.chunking_strategy:
                strategies.add(chunk.metadata.chunking_strategy)
        avg_word_count = total_word_count / len(self.chunks) if self.chunks else 0.0
        return {'chunk_count': len(self.chunks), 'unique_docs': len(unique_docs), 'avg_word_count': avg_word_count, 'strategies': strategies}

def __len__(self) -> int:
    return len(self.chunks)

class Query(BaseModule):
    """Represents a retrieval query."""
    query_str: str = Field(description='The query string.')
    top_k: Optional[int] = Field(default=None, description='Number of top results to retrieve.')
    custom_embedding_strs: Optional[List[str]] = Field(default=None, description='The List to store additional strings need to be embed with the query.')
    similarity_cutoff: Optional[float] = Field(default=None, description='Minimum similarity score.')
    keyword_filters: Optional[List[str]] = Field(default=None, description='Keywords to filter results.')
    metadata_filters: Optional[Dict[str, Any]] = Field(default=None, description='Additional metadata filters.')

    @property
    def embedding_strs(self) -> List[str]:
        """Use custom embedding strs if specified, otherwise use query str."""
        if self.custom_embedding_strs is None:
            if len(self.query_str) == 0:
                return []
            return [self.query_str]
        else:
            return self.custom_embedding_strs

    def to_QueryBundle(self):
        return QueryBundle(query_str=self.query_str, custom_embedding_strs=self.custom_embedding_strs)

@property
def embedding_strs(self) -> List[str]:
    """Use custom embedding strs if specified, otherwise use query str."""
    if self.custom_embedding_strs is None:
        if len(self.query_str) == 0:
            return []
        return [self.query_str]
    else:
        return self.custom_embedding_strs

def set_seed(seed: int):
    """
    Set random seeds for reproducibility across different libraries.
    
    Args:
        seed: The random seed value to use
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

class BIGBenchHard(Benchmark):
    """
    Benchmark class for BIGBenchHard dataset evaluation.
    
    BIGBenchHard is a subset of 23 challenging tasks from the BIG-bench evaluation suite.
    Each task example has the following structure:
    {
        "input": str,    # The input question/problem
        "target": str    # The expected answer/output
    }
    
    The benchmark supports automatic data splitting for training/validation purposes
    and evaluates predictions using exact match scoring.
    """

    def __init__(self, task: str, path: str=None, mode: str='all', dev_sample_num: int=0, seed: int=10, **kwargs):
        """
        Initialize BIGBenchHard benchmark.
        
        Args:
            task: The specific BIGBenchHard task name
            path: Path to store the dataset. Defaults to ~/.evoagentx/data/bigbenchhard/{task}
            mode: Data loading mode. Defaults to "all"
            dev_sample_num: Number of samples to use for dev set. If 0, all data goes to test set
            seed: Random seed for reproducibility. Defaults to 10
            **kwargs: Additional parameters for customization
            
        Raises:
            ValueError: If task is not a valid BIGBenchHard task name
        """
        if task not in ALL_TASKS:
            raise ValueError(f"Unknown task '{task}'. Available tasks: {list(ALL_TASKS.keys())}")
        self.task = task
        self.file_name = ALL_TASKS[task]
        self.dev_sample_num = dev_sample_num
        self.seed = seed
        path = os.path.expanduser(path or f'~/.evoagentx/data/bigbenchhard/{task}')
        super().__init__(name=f'BIGBenchHard-{self.task}', path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str) -> Optional[List[dict]]:
        """
        Load data from a specific file.
        
        Args:
            file_name: Name of the file to load
            
        Returns:
            List of loaded examples or None if file doesn't exist
        """
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_raw_bigbenchhard_data(task_name=self.task, save_folder=self.path)
        logger.info(f'Loading BIGBenchHard data from {file_path}...')
        data = load_json(path=file_path, type='json')
        return data.get('examples', [])

    def _load_data(self):
        """
        Load and split data according to mode and dev_sample_num settings.
        
        Data splitting logic:
        - If dev_sample_num > 0: randomly samples examples for dev set, rest go to test set
        - If dev_sample_num = 0: all data goes to test set for evaluation
        - No training data provided (BIGBenchHard is designed for few-shot evaluation)
        """
        task_data = self._load_data_from_file(file_name=self.file_name)
        if task_data is None:
            logger.warning(f'No data loaded for task {self.task}')
            self._train_data = []
            self._dev_data = []
            self._test_data = []
            return
        self._train_data = []
        if self.dev_sample_num > 0 and len(task_data) > self.dev_sample_num:
            logger.info(f'Sampling {self.dev_sample_num} examples for dev set, rest for test set.')
            if self.seed is not None:
                set_seed(self.seed)
            dev_subset = random.sample(task_data, self.dev_sample_num)
            self._dev_data = dev_subset
            self._test_data = [item for item in task_data if item not in dev_subset]
        elif self.dev_sample_num > 0:
            logger.warning(f'dev_sample_num ({self.dev_sample_num}) >= total data size ({len(task_data)}). Using all data for dev set, none for test set.')
            self._dev_data = task_data
            self._test_data = []
        else:
            logger.info('dev_sample_num is 0, using all data for test set.')
            self._dev_data = []
            self._test_data = task_data

    def get_input_keys(self) -> List[str]:
        """
        Return the input keys expected by the benchmark.
        
        Returns:
            List containing "input" as the key for the problem text
        """
        return ['input']

    def _get_label(self, example: Any) -> Any:
        """
        Extract the ground truth label from an example.
        
        Args:
            example: The benchmark example
            
        Returns:
            The target answer/label
        """
        return example['target']

    def _get_id(self, example: Any) -> Any:
        """
        Extract the unique identifier from an example.
        
        BIGBenchHard examples don't have explicit IDs, so we use input text as identifier.
        
        Args:
            example: The benchmark example
            
        Returns:
            The input text as a unique identifier
        """
        return example.get('input', None)

    def evaluate(self, prediction: Any, label: Any) -> dict:
        """
        Score a prediction against the ground truth label.
        
        Uses exact match scoring with task-specific handling for certain tasks.
        
        Args:
            prediction: The predicted answer
            label: The ground truth answer
            
        Returns:
            Dictionary containing the exact match score
        """
        if self.task == 'dyck_languages':
            em = prediction.replace(' ', '') == label.replace(' ', '')
            return {'em': em}
        else:
            em = exact_match_score(prediction=prediction, ground_truth=label)
            return {'em': em}

def _load_data(self):
    """
        Load and split data according to mode and dev_sample_num settings.
        
        Data splitting logic:
        - If dev_sample_num > 0: randomly samples examples for dev set, rest go to test set
        - If dev_sample_num = 0: all data goes to test set for evaluation
        - No training data provided (BIGBenchHard is designed for few-shot evaluation)
        """
    task_data = self._load_data_from_file(file_name=self.file_name)
    if task_data is None:
        logger.warning(f'No data loaded for task {self.task}')
        self._train_data = []
        self._dev_data = []
        self._test_data = []
        return
    self._train_data = []
    if self.dev_sample_num > 0 and len(task_data) > self.dev_sample_num:
        logger.info(f'Sampling {self.dev_sample_num} examples for dev set, rest for test set.')
        if self.seed is not None:
            set_seed(self.seed)
        dev_subset = random.sample(task_data, self.dev_sample_num)
        self._dev_data = dev_subset
        self._test_data = [item for item in task_data if item not in dev_subset]
    elif self.dev_sample_num > 0:
        logger.warning(f'dev_sample_num ({self.dev_sample_num}) >= total data size ({len(task_data)}). Using all data for dev set, none for test set.')
        self._dev_data = task_data
        self._test_data = []
    else:
        logger.info('dev_sample_num is 0, using all data for test set.')
        self._dev_data = []
        self._test_data = task_data

class RealMMRAG(Benchmark):
    """REAL-MM-RAG FinReport benchmark for multimodal retrieval evaluation.
    
    This benchmark contains financial report pages with associated queries,
    designed to test multimodal retrieval capabilities on real-world documents.
    """

    def __init__(self, path: str=None, mode: str='test', **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/real_mm_rag')
        self.dataset_file = Path(path) / 'real_mm_rag_finreport.json'
        self.images_dir = Path(path) / 'images'
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data(self):
        """Load the dataset from JSON file."""
        if not self.dataset_file.exists():
            download_real_mm_rag_data(save_dir=self.path)
        try:
            with open(self.dataset_file, 'r') as f:
                self._test_data = json.load(f)
            logger.info(f'Loaded {len(self._test_data)} samples from REAL-MM-RAG dataset')
        except Exception as e:
            logger.error(f'Failed to load dataset: {str(e)}')
            raise

    def _get_label(self, example: Any) -> Any:
        return example['answer']

    def _get_id(self, example: Any) -> Any:
        return example['id']

    def evaluate(self, prediction: Any, label: Any) -> dict:
        em = exact_match_score(prediction=prediction, ground_truth=label)
        f1 = f1_score(prediction=prediction, ground_truth=label)
        acc = acc_score(prediction=prediction, ground_truths=[label])
        return {'f1': f1, 'em': em, 'acc': acc}

    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get the raw dataset."""
        return self._test_data

    def get_sample(self, index: int) -> Dict[str, Any]:
        """Get a single sample by index.
        
        Args:
            index: Sample index
            
        Returns:
            Dict containing query, image_filename, answer, and rephrases
        """
        if index >= len(self._test_data):
            raise IndexError(f'Index {index} out of range for dataset size {len(self._test_data)}')
        sample = self._test_data[index]
        sample['image_path'] = str(self.images_dir / sample['image_filename'])
        return sample

    def get_samples(self, start: int=0, end: Optional[int]=None) -> List[Dict[str, Any]]:
        """Get a range of samples.
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive). If None, goes to end of dataset
            
        Returns:
            List of samples
        """
        end = end or len(self._test_data)
        samples = []
        for i in range(start, min(end, len(self._test_data))):
            samples.append(self.get_sample(i))
        return samples

    def get_random_samples(self, n: int, seed: int=42) -> List[Dict[str, Any]]:
        """Get n random samples from the dataset.
        
        Args:
            n: Number of samples to return
            seed: Random seed for reproducibility
            
        Returns:
            List of random samples
        """
        import random
        random.seed(seed)
        indices = random.sample(range(len(self._test_data)), min(n, len(self._test_data)))
        return [self.get_sample(i) for i in indices]

    def get_query_variations(self, sample: Dict[str, Any]) -> List[str]:
        """Get all query variations for a sample.
        
        Args:
            sample: A sample from the dataset
            
        Returns:
            List of query variations (original + 3 rephrase levels)
        """
        queries = [sample['query']]
        for level in ['rephrase_level_1', 'rephrase_level_2', 'rephrase_level_3']:
            if level in sample and sample[level]:
                queries.append(sample[level])
        return queries

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset statistics.
        
        Returns:
            Dictionary with dataset statistics
        """
        total_samples = len(self._test_data)
        has_rephrase_1 = sum((1 for s in self._test_data if s.get('rephrase_level_1')))
        has_rephrase_2 = sum((1 for s in self._test_data if s.get('rephrase_level_2')))
        has_rephrase_3 = sum((1 for s in self._test_data if s.get('rephrase_level_3')))
        unique_images = set((s['image_filename'] for s in self._test_data))
        return {'total_samples': total_samples, 'unique_images': len(unique_images), 'samples_with_rephrase_1': has_rephrase_1, 'samples_with_rephrase_2': has_rephrase_2, 'samples_with_rephrase_3': has_rephrase_3, 'avg_queries_per_image': total_samples / len(unique_images)}

def get_sample(self, index: int) -> Dict[str, Any]:
    """Get a single sample by index.
        
        Args:
            index: Sample index
            
        Returns:
            Dict containing query, image_filename, answer, and rephrases
        """
    if index >= len(self._test_data):
        raise IndexError(f'Index {index} out of range for dataset size {len(self._test_data)}')
    sample = self._test_data[index]
    sample['image_path'] = str(self.images_dir / sample['image_filename'])
    return sample

def get_samples(self, start: int=0, end: Optional[int]=None) -> List[Dict[str, Any]]:
    """Get a range of samples.
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive). If None, goes to end of dataset
            
        Returns:
            List of samples
        """
    end = end or len(self._test_data)
    samples = []
    for i in range(start, min(end, len(self._test_data))):
        samples.append(self.get_sample(i))
    return samples

def get_random_samples(self, n: int, seed: int=42) -> List[Dict[str, Any]]:
    """Get n random samples from the dataset.
        
        Args:
            n: Number of samples to return
            seed: Random seed for reproducibility
            
        Returns:
            List of random samples
        """
    import random
    random.seed(seed)
    indices = random.sample(range(len(self._test_data)), min(n, len(self._test_data)))
    return [self.get_sample(i) for i in indices]

def get_stats(self) -> Dict[str, Any]:
    """Get dataset statistics.
        
        Returns:
            Dictionary with dataset statistics
        """
    total_samples = len(self._test_data)
    has_rephrase_1 = sum((1 for s in self._test_data if s.get('rephrase_level_1')))
    has_rephrase_2 = sum((1 for s in self._test_data if s.get('rephrase_level_2')))
    has_rephrase_3 = sum((1 for s in self._test_data if s.get('rephrase_level_3')))
    unique_images = set((s['image_filename'] for s in self._test_data))
    return {'total_samples': total_samples, 'unique_images': len(unique_images), 'samples_with_rephrase_1': has_rephrase_1, 'samples_with_rephrase_2': has_rephrase_2, 'samples_with_rephrase_3': has_rephrase_3, 'avg_queries_per_image': total_samples / len(unique_images)}

class MATH(Benchmark):
    """Benchmark class for evaluating mathematical reasoning on the MATH dataset.
    
    MATH is a dataset of challenging competition mathematics problems,
    spanning various difficulty levels and subject areas. This class handles
    loading the dataset, extracting answers, evaluating solutions through
    symbolic and numerical comparisons, and computing accuracy metrics.
    
    The dataset includes problems across 7 subject areas (Algebra, Geometry, etc.)
    and 5 difficulty levels. Each problem contains LaTeX-formatted
    questions and solutions.
    
    Each MATH example has the following structure:
    {
        "id": "test-1", 
        "problem": "the problem", 
        "solution": "the solution",
        "level": "Level 1", # "Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Level ?"
        "type": "Algebra", # 'Geometry', 'Algebra', 'Intermediate Algebra', 'Counting & Probability', 'Precalculus', 'Number Theory', 'Prealgebra'
    }
    
    The benchmark evaluates answers using symbolic math equality checking
    and numerical approximation to handle equivalent mathematical expressions.
    """

    def __init__(self, path: str=None, mode: str='all', **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/math')
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data_from_folders(self, data_folder: str) -> List[dict]:
        if data_folder is None:
            return None
        data = []
        typ = 'train' if 'train' in data_folder else 'test'
        sub_data_folders = os.listdir(data_folder)
        i = 0
        logger.info(f'loading MATH data from {data_folder} ...')
        for sub_data_folder in sub_data_folders:
            if os.path.isdir(os.path.join(data_folder, sub_data_folder)):
                files = os.listdir(os.path.join(data_folder, sub_data_folder))
                for file in files:
                    if file.endswith('.json'):
                        example = {'id': f'{typ}-{i + 1}'}
                        example.update(load_json(os.path.join(data_folder, sub_data_folder, file), type='json'))
                        data.append(example)
                        i += 1
        return data

    def _load_data(self):
        if not os.path.exists(os.path.join(self.path, 'MATH')):
            download_raw_math_data(save_folder=self.path)
        data_folder = os.path.join(self.path, 'MATH')
        if self.mode == 'train' or self.mode == 'all':
            self._train_data = self._load_data_from_folders(data_folder=os.path.join(data_folder, 'train'))
        if self.mode == 'dev' or self.mode == 'all':
            self._dev_data = None
        if self.mode == 'test' or self.mode == 'all':
            self._test_data = self._load_data_from_folders(data_folder=os.path.join(data_folder, 'test'))

    def _get_label(self, example: Any) -> Any:
        return example['solution']

    def _get_id(self, example: Any) -> Any:
        return example['id']

    def extract_answer(self, text: str) -> str:
        pattern = '\\\\boxed{((?:[^{}]|{[^{}]*})*)}'
        boxed_matches = regex.findall(pattern, text, regex.DOTALL)
        if boxed_matches:
            return boxed_matches[-1].strip()
        sentence_end_pattern = '(?<!\\d)[.!?]\\s+'
        sentences = regex.split(sentence_end_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences[-1] if sentences else ''

    def math_equal(self, prediction: Any, reference: Any) -> bool:
        if str(prediction) == str(reference):
            return True
        try:
            if self.is_digit(prediction) and self.is_digit(reference):
                prediction = self.parse_digits(prediction)
                reference = self.parse_digits(reference)
                return isclose(prediction, reference, abs_tol=0.001)
        except Exception:
            pass
        try:
            return self.symbolic_equal(prediction, reference)
        except Exception:
            pass
        return False

    def is_digit(self, num: Any) -> bool:
        return self.parse_digits(num) is not None

    def parse_digits(self, num: Any) -> float:
        num = regex.sub(',', '', str(num))
        try:
            return float(num)
        except Exception:
            if num.endswith('%'):
                num = num[:-1]
                if num.endswith('\\'):
                    num = num[:-1]
                try:
                    return float(num) / 100
                except Exception:
                    pass
        return None

    def symbolic_equal(self, a: Any, b: Any) -> bool:

        def _parse(s: Any) -> Any:
            for f in [parse_latex, parse_expr]:
                try:
                    return f(s)
                except Exception:
                    pass
            return s
        a = _parse(a)
        b = _parse(b)
        try:
            if simplify(a - b) == 0:
                return True
        except Exception:
            pass
        try:
            if isclose(N(a), N(b), abs_tol=0.001):
                return True
        except Exception:
            pass
        return False

    def evaluate(self, prediction: Any, label: Any) -> dict:
        ground_truth_answer = self.extract_answer(label)
        predicted_answer = self.extract_answer(prediction)
        solve_rate = 1.0 if self.math_equal(predicted_answer, ground_truth_answer) else 0.0
        return {'solve_rate': solve_rate}

def math_equal(self, prediction: Any, reference: Any) -> bool:
    if str(prediction) == str(reference):
        return True
    try:
        if self.is_digit(prediction) and self.is_digit(reference):
            prediction = self.parse_digits(prediction)
            reference = self.parse_digits(reference)
            return isclose(prediction, reference, abs_tol=0.001)
    except Exception:
        pass
    try:
        return self.symbolic_equal(prediction, reference)
    except Exception:
        pass
    return False

def is_digit(self, num: Any) -> bool:
    return self.parse_digits(num) is not None

def symbolic_equal(self, a: Any, b: Any) -> bool:

    def _parse(s: Any) -> Any:
        for f in [parse_latex, parse_expr]:
            try:
                return f(s)
            except Exception:
                pass
        return s
    a = _parse(a)
    b = _parse(b)
    try:
        if simplify(a - b) == 0:
            return True
    except Exception:
        pass
    try:
        if isclose(N(a), N(b), abs_tol=0.001):
            return True
    except Exception:
        pass
    return False

def evaluate(self, prediction: Any, label: Any) -> dict:
    ground_truth_answer = self.extract_answer(label)
    predicted_answer = self.extract_answer(prediction)
    solve_rate = 1.0 if self.math_equal(predicted_answer, ground_truth_answer) else 0.0
    return {'solve_rate': solve_rate}

class Tokens(object):
    """A class to represent a list of tokenized text."""
    TEXT = 0
    TEXT_WS = 1
    SPAN = 2
    POS = 3
    LEMMA = 4
    NER = 5

    def __init__(self, data, annotators, opts=None):
        self.data = data
        self.annotators = annotators
        self.opts = opts or {}

    def __len__(self):
        """The number of tokens."""
        return len(self.data)

    def slice(self, i=None, j=None):
        """Return a view of the list of tokens from [i, j)."""
        new_tokens = copy.copy(self)
        new_tokens.data = self.data[i:j]
        return new_tokens

    def untokenize(self):
        """Returns the original text (with whitespace reinserted)."""
        return ''.join([t[self.TEXT_WS] for t in self.data]).strip()

    def words(self, uncased=False):
        """Returns a list of the text of each token

        Args:
            uncased: lower cases text
        """
        if uncased:
            return [t[self.TEXT].lower() for t in self.data]
        else:
            return [t[self.TEXT] for t in self.data]

    def offsets(self):
        """Returns a list of [start, end) character offsets of each token."""
        return [t[self.SPAN] for t in self.data]

    def pos(self):
        """Returns a list of part-of-speech tags of each token.
        Returns None if this annotation was not included.
        """
        if 'pos' not in self.annotators:
            return None
        return [t[self.POS] for t in self.data]

    def lemmas(self):
        """Returns a list of the lemmatized text of each token.
        Returns None if this annotation was not included.
        """
        if 'lemma' not in self.annotators:
            return None
        return [t[self.LEMMA] for t in self.data]

    def entities(self):
        """Returns a list of named-entity-recognition tags of each token.
        Returns None if this annotation was not included.
        """
        if 'ner' not in self.annotators:
            return None
        return [t[self.NER] for t in self.data]

    def ngrams(self, n=1, uncased=False, filter_fn=None, as_strings=True):
        """Returns a list of all ngrams from length 1 to n.

        Args:
            n: upper limit of ngram length
            uncased: lower cases text
            filter_fn: user function that takes in an ngram list and returns
              True or False to keep or not keep the ngram
            as_string: return the ngram as a string vs list
        """

        def _skip(gram):
            if not filter_fn:
                return False
            return filter_fn(gram)
        words = self.words(uncased)
        ngrams = [(s, e + 1) for s in range(len(words)) for e in range(s, min(s + n, len(words))) if not _skip(words[s:e + 1])]
        if as_strings:
            ngrams = ['{}'.format(' '.join(words[s:e])) for s, e in ngrams]
        return ngrams

    def entity_groups(self):
        """Group consecutive entity tokens with the same NER tag."""
        entities = self.entities()
        if not entities:
            return None
        non_ent = self.opts.get('non_ent', 'O')
        groups = []
        idx = 0
        while idx < len(entities):
            ner_tag = entities[idx]
            if ner_tag != non_ent:
                start = idx
                while idx < len(entities) and entities[idx] == ner_tag:
                    idx += 1
                groups.append((self.slice(start, idx).untokenize(), ner_tag))
            else:
                idx += 1
        return groups

def __len__(self):
    """The number of tokens."""
    return len(self.data)

def ngrams(self, n=1, uncased=False, filter_fn=None, as_strings=True):
    """Returns a list of all ngrams from length 1 to n.

        Args:
            n: upper limit of ngram length
            uncased: lower cases text
            filter_fn: user function that takes in an ngram list and returns
              True or False to keep or not keep the ngram
            as_string: return the ngram as a string vs list
        """

    def _skip(gram):
        if not filter_fn:
            return False
        return filter_fn(gram)
    words = self.words(uncased)
    ngrams = [(s, e + 1) for s in range(len(words)) for e in range(s, min(s + n, len(words))) if not _skip(words[s:e + 1])]
    if as_strings:
        ngrams = ['{}'.format(' '.join(words[s:e])) for s, e in ngrams]
    return ngrams

def has_answer(answers, text, match_type='string') -> bool:
    """Check if the text contains an answer string.
    If `match_type` is string, token matching is done between the text and answer.
    If `match_type` is regex, we search the whole text with the regex.
    """
    text = _normalize(text)
    tokenizer = SimpleTokenizer()
    if match_type == 'string':
        text = tokenizer.tokenize(text).words(uncased=True)
        for single_answer in answers:
            single_answer = _normalize(single_answer)
            single_answer = tokenizer.tokenize(single_answer)
            single_answer = single_answer.words(uncased=True)
            for i in range(0, len(text) - len(single_answer) + 1):
                if single_answer == text[i:i + len(single_answer)]:
                    return True
    elif match_type == 'regex':
        for single_answer in answers:
            single_answer = _normalize(single_answer)
            if regex_match(text, single_answer):
                return True
    return False

class Benchmark(ABC):
    """
    Abstract base class for defining benchmarks. This class provides methods to load,
    retrieve, and evaluate benchmark data, with train, dev, and test splits.
    """

    def __init__(self, name: str, path: str, mode: str='all', **kwargs):
        """
        Initializes the benchmark with a name and data path.
        
        Args:
            name (str): The name of the benchmark.
            path (str): The path to the dataset.
            mode (str): which type of data to load, choices: ["all", "train", "dev", "test"]
            **kwargs: Additional parameters for customization.
        """
        valid_mode = ['all', 'train', 'dev', 'test']
        assert mode in valid_mode, f'Invalid value for model: {mode}. Available choices: {valid_mode}'
        self.name = name
        self.path = path
        self.mode = mode
        self.kwargs = kwargs
        self._train_data: Optional[List[dict]] = None
        self._dev_data: Optional[List[dict]] = None
        self._test_data: Optional[List[dict]] = None
        self._load_data()

    @abstractmethod
    def _load_data(self):
        """
        Abstract method to load data from `self.path` and assign it to `_train_data`, `_dev_data`, and `_test_data` if applicable.
        """
        pass

    @abstractmethod
    def _get_id(self, example: Any) -> Any:
        """
        Abstract method to return the id for a given example.
        """
        pass

    @abstractmethod
    def _get_label(self, example: Any) -> Any:
        """
        Abstract method to return the ground-truth label for a given example.
        
        Args:
            example (Any): The input example for which the label is needed.
        
        Returns:
            Any: The ground-truth label associated with the example.
        """
        pass

    @abstractmethod
    def evaluate(self, prediction: Any, label: Any) -> dict:
        """
        Abstract method to evaluate a single prediction against the ground-truth label.
        
        Args:
            prediction (Any): The predicted output.
            label (Any): The actual ground-truth label.
        
        Returns:
            dict: A dictionary containing evaluation metrics.
        """
        pass

    async def async_evaluate(self, prediction: Any, label: Any) -> dict:
        """
        Asynchronous version of evaluate method that internally calls the synchronous evaluate.
        
        Args:
            prediction (Any): The predicted output.
            label (Any): The actual ground-truth label.
        
        Returns:
            dict: A dictionary containing evaluation metrics.
        """
        return await asyncio.to_thread(self.evaluate, prediction, label)

    def get_label(self, example: List[Any]) -> Any:
        return self._get_label(example=example)

    def get_labels(self, examples: List[Any]) -> List[Any]:
        return [self._get_label(example=example) for example in examples]

    def get_id(self, example: List[Any]) -> Any:
        return self._get_id(example=example)

    def get_ids(self, examples: List[Any]) -> List[Any]:
        return [self._get_id(example=example) for example in examples]

    def get_data_by_mode(self, mode: str='test') -> List[Any]:
        """
        Get the data from the benchmark by mode.
        """
        assert mode in ['train', 'dev', 'test'], f"Invalid value for mode: {mode}. Available choices: ['train', 'dev', 'test']"
        if mode == 'train':
            if self._train_data is None:
                logger.warning(f'Train data for benchmark {type(self).__name__} is not loaded or None. Return an empty list.')
                return []
            data = self._train_data
        elif mode == 'dev':
            if self._dev_data is None:
                logger.warning(f'Dev data for benchmark {type(self).__name__} is not loaded or None. Return an empty list.')
                return []
            data = self._dev_data
        else:
            if self._test_data is None:
                logger.warning(f'Test data for benchmark {type(self).__name__} is not loaded or None. Return an empty list.')
                return []
            data = self._test_data
        return data

    def get_example_by_id(self, example_id: Any, mode: str=None) -> Optional[Any]:
        """
        Get an example from the benchmark by its id.

        Args:
            example_id (Any): The id of the example to retrieve.
            mode (str): The mode to retrieve the example from, choices: ["train", "dev", "test", "all"]
        
        Returns:
            Optional[Any]: The example if found, otherwise None.
        """
        if mode is not None and mode not in ['train', 'dev', 'test', 'all']:
            raise ValueError(f"Invalid value for mode: {mode}. Available choices: ['train', 'dev', 'test', 'all']")
        if mode is None or mode == 'all':
            data = []
            if self._train_data is not None:
                data.extend(self._train_data)
            if self._dev_data is not None:
                data.extend(self._dev_data)
            if self._test_data is not None:
                data.extend(self._test_data)
        else:
            data = self.get_data_by_mode(mode=mode)
        for example in data:
            if self._get_id(example=example) == example_id:
                return example
        return None

    def get_example_by_index(self, index: int, mode: str='test') -> Optional[Any]:
        """
        Get an example from the benchmark by its index.

        Args:
            index (int): The index of the example to retrieve.
            mode (str): The mode to retrieve the example from, choices: ["train", "dev", "test"]
        
        Returns:
            Optional[Any]: The example if found, otherwise None.
        """
        data = self.get_data_by_mode(mode=mode)
        return data[index] if index < len(data) else None

    def _get_data(self, data: List[dict], indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
        """
        Retrieves a subset of data based on provided indices or a random sample.
        
        Args:
            data (List[dict]): The list of data examples.
            indices (List[int], optional): Specific indices of data to retrieve. Defaults to None.
            sample_k (int, optional): The number of random samples to retrieve. Defaults to None.
            seed (int, optional): The seed for random sampling. Defaults to None. If provided, the random sampling will be deterministic.
        Returns:
            List[dict]: The selected subset of data. If both `indices` and `sample_k` are None, it will return the original `data`.
        """
        if indices is None:
            indices = list(range(len(data)))
        if sample_k is not None:
            if seed is not None:
                random.seed(seed)
            indices = random.sample(indices, k=min(sample_k, len(indices)))
        return_data = [data[idx] for idx in indices]
        return return_data

    def get_train_data(self, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
        if self._train_data is None:
            logger.warning(f'Train data for benchmark {type(self).__name__} is not loaded or None. Return an empty list.')
            return []
        train_data = self._get_data(self._train_data, indices=indices, sample_k=sample_k, seed=seed)
        return train_data

    def get_dev_data(self, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
        if self._dev_data is None:
            logger.warning(f'Dev data for benchmark {type(self).__name__} is not loaded or None. Return an empty list.')
            return []
        dev_data = self._get_data(self._dev_data, indices=indices, sample_k=sample_k, seed=seed)
        return dev_data

    def get_test_data(self, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
        if self._test_data is None:
            logger.warning(f'Test data for benchmark {type(self).__name__} is not loaded or None. Return an empty list.')
            return []
        test_data = self._get_data(self._test_data, indices=indices, sample_k=sample_k, seed=seed)
        return test_data

def __init__(self, name: str, path: str, mode: str='all', **kwargs):
    """
        Initializes the benchmark with a name and data path.
        
        Args:
            name (str): The name of the benchmark.
            path (str): The path to the dataset.
            mode (str): which type of data to load, choices: ["all", "train", "dev", "test"]
            **kwargs: Additional parameters for customization.
        """
    valid_mode = ['all', 'train', 'dev', 'test']
    assert mode in valid_mode, f'Invalid value for model: {mode}. Available choices: {valid_mode}'
    self.name = name
    self.path = path
    self.mode = mode
    self.kwargs = kwargs
    self._train_data: Optional[List[dict]] = None
    self._dev_data: Optional[List[dict]] = None
    self._test_data: Optional[List[dict]] = None
    self._load_data()

def get_label(self, example: List[Any]) -> Any:
    return self._get_label(example=example)

def get_labels(self, examples: List[Any]) -> List[Any]:
    return [self._get_label(example=example) for example in examples]

def get_id(self, example: List[Any]) -> Any:
    return self._get_id(example=example)

def get_ids(self, examples: List[Any]) -> List[Any]:
    return [self._get_id(example=example) for example in examples]

def get_example_by_id(self, example_id: Any, mode: str=None) -> Optional[Any]:
    """
        Get an example from the benchmark by its id.

        Args:
            example_id (Any): The id of the example to retrieve.
            mode (str): The mode to retrieve the example from, choices: ["train", "dev", "test", "all"]
        
        Returns:
            Optional[Any]: The example if found, otherwise None.
        """
    if mode is not None and mode not in ['train', 'dev', 'test', 'all']:
        raise ValueError(f"Invalid value for mode: {mode}. Available choices: ['train', 'dev', 'test', 'all']")
    if mode is None or mode == 'all':
        data = []
        if self._train_data is not None:
            data.extend(self._train_data)
        if self._dev_data is not None:
            data.extend(self._dev_data)
        if self._test_data is not None:
            data.extend(self._test_data)
    else:
        data = self.get_data_by_mode(mode=mode)
    for example in data:
        if self._get_id(example=example) == example_id:
            return example
    return None

def get_example_by_index(self, index: int, mode: str='test') -> Optional[Any]:
    """
        Get an example from the benchmark by its index.

        Args:
            index (int): The index of the example to retrieve.
            mode (str): The mode to retrieve the example from, choices: ["train", "dev", "test"]
        
        Returns:
            Optional[Any]: The example if found, otherwise None.
        """
    data = self.get_data_by_mode(mode=mode)
    return data[index] if index < len(data) else None

def _get_data(self, data: List[dict], indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
    """
        Retrieves a subset of data based on provided indices or a random sample.
        
        Args:
            data (List[dict]): The list of data examples.
            indices (List[int], optional): Specific indices of data to retrieve. Defaults to None.
            sample_k (int, optional): The number of random samples to retrieve. Defaults to None.
            seed (int, optional): The seed for random sampling. Defaults to None. If provided, the random sampling will be deterministic.
        Returns:
            List[dict]: The selected subset of data. If both `indices` and `sample_k` are None, it will return the original `data`.
        """
    if indices is None:
        indices = list(range(len(data)))
    if sample_k is not None:
        if seed is not None:
            random.seed(seed)
        indices = random.sample(indices, k=min(sample_k, len(indices)))
    return_data = [data[idx] for idx in indices]
    return return_data

class CodingBenchmark(Benchmark):
    """
    Abstract base class for defining coding benchmarks. This class provides methods to check the solution code.
    """

    def __init__(self, name: str, path: str, mode: str='all', timeout: int=60, **kwargs):
        self.SUCCESS = 0
        self.FAILED = 1
        self.TIMEOUT = 2
        self.timeout = timeout
        super().__init__(name=name, path=path, mode=mode, **kwargs)

    def handle_special_cases(self, task_id: str, solution: str, test: str) -> bool:
        return (solution, test)

    def _check_evaluation_inputs(self, prediction: Any, label: Any) -> bool:
        """
        Check if the inputs are valid for evaluation.
        """
        assert isinstance(prediction, str) or isinstance(prediction, list), 'prediction must be a string or a list of strings, but got {}'.format(type(prediction))
        assert isinstance(label, dict) or isinstance(label, list), 'label must be a string or a list of strings, but got {}'.format(type(label))
        prediction = [prediction] if isinstance(prediction, str) else prediction
        label = [label] if isinstance(label, dict) else label
        return (prediction, label)

    def check_solution(self, task_id: str, solution: str, test: str, entry_point: Optional[str]=None, use_entrypoint_as_input: bool=True) -> Tuple[int, str]:
        """
        Execute the solution code and check if it passes the unit test.

        Args:
            task_id (str): The task id.
            solution (str): The solution code.
            test (str): The unit test code in HumanEval format. 
            entry_point (str): The entry point of the solution code.
        Returns:
            Tuple[int, str]: A tuple containing an integer indicating whether the solution passes the unit test (0: success, 1: failed, 2: timeout) and a string containing the success/error message.
        """
        solution = sanitize(solution, entrypoint=entry_point)
        try:
            global_dict = {'math': __import__('math'), 'hashlib': __import__('hashlib'), 're': __import__('re'), 'List': List, 'Dict': Dict, 'Tuple': Tuple, 'Optional': Optional, 'Any': Any}
            solution, test = self.handle_special_cases(task_id=task_id, solution=solution, test=test)
            exec(solution, global_dict)
            if entry_point not in global_dict:
                raise ValueError(f'Function {entry_point} not found in the solution code.')
            exec(test, global_dict)
            unit_test_func = global_dict['check']
            with timeout(seconds=self.timeout):
                if use_entrypoint_as_input:
                    unit_test_func(global_dict[entry_point])
                else:
                    unit_test_func()
            result = (self.SUCCESS, 'The solution passed the unit test.')
        except TimeoutException:
            result = (self.TIMEOUT, 'Execution timed out.')
        except Exception as e:
            error_msg = f'An error occurred: {e}\nSolution:\n{solution}\nTest:\n{test}'
            result = (self.FAILED, error_msg)
        return result

    def compute_pass_at_k(self, results: List[bool], k_list: List[int]) -> Dict[str, float]:
        """
        Compute the pass@k for the given results.
        """
        pass_at_k = {}
        n = len(results)
        c = sum(results)
        for k in k_list:
            if n >= k:
                pass_at_k[f'pass@{k}'] = float(estimate_pass_at_k(np.array([n]), np.array([c]), k)[0])
        return pass_at_k

def compute_pass_at_k(self, results: List[bool], k_list: List[int]) -> Dict[str, float]:
    """
        Compute the pass@k for the given results.
        """
    pass_at_k = {}
    n = len(results)
    c = sum(results)
    for k in k_list:
        if n >= k:
            pass_at_k[f'pass@{k}'] = float(estimate_pass_at_k(np.array([n]), np.array([c]), k)[0])
    return pass_at_k

@dataclass
class CodeExecutionProblem:
    question_id: str
    contest_id: str
    contest_date: datetime
    difficulty: str
    function_name: str
    code: str
    input: str
    output: str
    id: str
    problem_id: str
    numsteps: int

    def __post_init__(self):
        pass

    def insert_output(self, output_list: list[str], pred_list: list[str]) -> dict:
        return {'question_id': self.question_id, 'contest_id': self.contest_id, 'contest_date': self.contest_date.isoformat(), 'difficulty': self.difficulty, 'function_name': self.function_name, 'code': self.code, 'input': self.input, 'output': self.output, 'id': self.id, 'problem_id': self.problem_id, 'numsteps': self.numsteps, 'output_list': output_list, 'pred_list': pred_list}

    def insert_output_evaluation(self, output_list: list[str], code_list: list[str], graded_list: list[bool]) -> dict:
        output = self.insert_output(output_list, code_list)
        output['graded_list'] = graded_list
        output['pass@1'] = graded_list.count(True) / len(graded_list)
        return output

    def get_evaluation_sample(self) -> dict:
        return {'code': self.code, 'input': self.input, 'output': self.output}

def insert_output_evaluation(self, output_list: list[str], code_list: list[str], graded_list: list[bool]) -> dict:
    output = self.insert_output(output_list, code_list)
    output['graded_list'] = graded_list
    output['pass@1'] = graded_list.count(True) / len(graded_list)
    return output

def load_code_execution_dataset(release_version='release_v1', cache_dir: str=None) -> list[CodeExecutionProblem]:
    dataset = load_dataset('livecodebench/execution-v2', split='test', trust_remote_code=True, cache_dir=cache_dir)
    dataset = [CodeExecutionProblem(**p) for p in dataset]
    return dataset

@dataclass
class CodeGenerationProblem:
    question_title: str
    question_content: str
    platform: Platform
    question_id: str
    contest_id: str
    contest_date: datetime
    starter_code: str
    difficulty: Difficulty
    public_test_cases: list[Test]
    private_test_cases: list[Test]
    metadata: dict

    def __post_init__(self):
        self.platform = Platform(self.platform)
        self.difficulty = Difficulty(self.difficulty)
        self.contest_date = datetime.fromisoformat(self.contest_date)
        self.public_test_cases = json.loads(self.public_test_cases)
        self.public_test_cases = [Test(**t) for t in self.public_test_cases]
        try:
            self.private_test_cases = json.loads(self.private_test_cases)
        except Exception:
            self.private_test_cases = json.loads(pickle.loads(zlib.decompress(base64.b64decode(self.private_test_cases.encode('utf-8')))))
        self.private_test_cases = [Test(**t) for t in self.private_test_cases]
        self.metadata = json.loads(self.metadata)

    def insert_output(self, output_list: list[str], code_list: list[str]) -> dict:
        return {'question_title': self.question_title, 'question_content': self.question_content, 'platform': self.platform.value, 'question_id': self.question_id, 'contest_id': self.contest_id, 'contest_date': self.contest_date.isoformat(), 'starter_code': self.starter_code, 'difficulty': self.difficulty.value, 'output_list': output_list, 'code_list': code_list}

    def insert_output_evaluation(self, output_list: list[str], code_list: list[str], graded_list: list[bool], **kwargs) -> dict:
        output = self.insert_output(output_list, code_list)
        output['graded_list'] = graded_list
        output['pass@1'] = graded_list.count(True) / len(graded_list)
        for k, v in kwargs.items():
            output[k] = v
        return output

    def get_evaluation_sample(self):
        return {'input_output': json.dumps({'inputs': [t.input for t in self.public_test_cases + self.private_test_cases], 'outputs': [t.output for t in self.public_test_cases + self.private_test_cases], 'fn_name': self.metadata.get('func_name', None)})}

def insert_output_evaluation(self, output_list: list[str], code_list: list[str], graded_list: list[bool], **kwargs) -> dict:
    output = self.insert_output(output_list, code_list)
    output['graded_list'] = graded_list
    output['pass@1'] = graded_list.count(True) / len(graded_list)
    for k, v in kwargs.items():
        output[k] = v
    return output

def load_code_generation_dataset(release_version='release_v1', cache_dir: str=None, start_date=None, end_date=None) -> list[CodeGenerationProblem]:
    dataset = load_dataset('livecodebench/code_generation_lite', split='test', version_tag=release_version, trust_remote_code=True, cache_dir=cache_dir)
    dataset = [CodeGenerationProblem(**p) for p in dataset]
    if start_date is not None:
        p_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        dataset = [e for e in dataset if p_start_date <= e.contest_date]
    if end_date is not None:
        p_end_date = datetime.strptime(end_date, '%Y-%m-%d')
        dataset = [e for e in dataset if e.contest_date <= p_end_date]
    return dataset

def load_code_generation_dataset_not_fast(release_version='release_v1') -> list[CodeGenerationProblem]:
    dataset = load_dataset('livecodebench/code_generation', split='test')
    dataset = [CodeGenerationProblem(**p) for p in dataset]
    return dataset

@patch('builtins.open', mock_open(read_data=inputs))
@patch('sys.stdin', StringIO(inputs))
@patch('sys.stdin.readline', lambda *args: next(inputs_line_iterator))
@patch('sys.stdin.readlines', lambda *args: inputs.split('\n'))
@patch('sys.stdin.read', lambda *args: inputs)
def _inner_call_method(_method):
    try:
        return _method()
    except SystemExit:
        pass
    finally:
        pass

def estimate_pass_at_k(num_samples, num_correct, k):
    """Estimates pass@k of each problem and returns them in an array."""

    def estimator(n: int, c: int, k: int) -> float:
        """Calculates 1 - comb(n - c, k) / comb(n, k)."""
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))
    import itertools
    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)
    return np.array([estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)])

def compute_metrics_from_results(results, k_list=[1, 5]):
    total = []
    correct = []
    task_ids = []
    for task_id, res in results.items():
        all_correct = []
        for generation in res:
            gen = np.array(generation)
            all_correct.append(np.all(gen > 0))
        task_ids.append(task_id)
        total.append(len(all_correct))
        correct.append(sum(all_correct))
    total = np.array(total)
    correct = np.array(correct)
    ks = k_list
    detail_pass_at_k = {f'pass@{k}': estimate_pass_at_k(total, correct, k).tolist() for k in ks if (total >= k).all()}
    pass_at_k = {f'pass@{k}': estimate_pass_at_k(total, correct, k).mean() for k in ks if (total >= k).all()}
    detail_metrics = {k: dict(zip(task_ids, v)) for k, v in detail_pass_at_k.items()}
    pass_at_k['detail'] = detail_metrics
    return pass_at_k

def evaluate_score(args) -> list[bool]:
    gs, (c, i, o) = args
    execution_results = []
    for g in gs:
        if i in g:
            pass
        else:
            code_to_execute = f'{BASE_IMPORTS}\n{c}\nassert {o} == {g}'
            execution_results.append(check_execution_correctness(code_to_execute, 3))
    if len(execution_results) == 0:
        execution_results = [False] * len(gs)
    return execution_results

def code_execution_metrics(samples, generations):
    references = [(doc['code'], doc['input'], doc['output']) for doc in samples]
    with ProcessPoolExecutor() as executor:
        args_list = zip(generations, references)
        results = executor.map(evaluate_score, args_list)
    all_results = list(results)
    pass_at_1s = []
    for execution_result in all_results:
        c, n = (execution_result.count(True), len(execution_result))
        pass_at_1s.append(pass_at_k(n, c, 1))
    metrics = {'pass@1': sum(pass_at_1s) / len(pass_at_1s)}
    results = {}
    for i, r in enumerate(all_results):
        r_new = []
        for _r in r:
            r_new.append([_r])
        results[i] = r_new
    return [metrics, results]

@dataclass
class TestOutputPredictionProblem:
    question_title: str
    question_content: str
    question_id: str
    contest_id: str
    contest_date: datetime
    difficulty: str
    test: list[Test]
    starter_code: str
    function_name: str
    test_id: int

    def __post_init__(self):
        self.test = [Test(**t) for t in json.loads(self.test)]

    def insert_output(self, output_list: list[str], pred_list: list[str]) -> dict:
        return {'question_title': self.question_title, 'question_content': self.question_content, 'question_id': self.question_id, 'contest_id': self.contest_id, 'contest_date': self.contest_date.isoformat(), 'difficulty': self.difficulty, 'output_list': output_list, 'pred_list': pred_list, 'test_id': self.test_id, 'function_name': self.function_name, 'starter_code': self.starter_code}

    def insert_output_evaluation(self, output_list: list[str], code_list: list[str], graded_list: list[bool]) -> dict:
        output = self.insert_output(output_list, code_list)
        output['graded_list'] = graded_list
        output['pass@1'] = graded_list.count(True) / len(graded_list)
        return output

    def get_evaluation_sample(self) -> dict:
        return {'input': self.question_content, 'output': self.test[0].output}

def insert_output_evaluation(self, output_list: list[str], code_list: list[str], graded_list: list[bool]) -> dict:
    output = self.insert_output(output_list, code_list)
    output['graded_list'] = graded_list
    output['pass@1'] = graded_list.count(True) / len(graded_list)
    return output

def load_test_prediction_dataset(release_version='release_v1', cache_dir: str=None) -> list[TestOutputPredictionProblem]:
    dataset = load_dataset('livecodebench/test_generation', split='test', trust_remote_code=True, cache_dir=cache_dir)
    dataset = [TestOutputPredictionProblem(**d) for d in dataset]
    return dataset

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

class Message(BaseModule):
    """
    the base class for message. 

    Attributes: 
        content (Any): the content of the message, need to implement str() function. 
        agent (str): the sender of the message, normally set as the agent name.
        action (str): the trigger of the message, normally set as the action name.
        prompt (str): the prompt used to obtain the generated text. 
        next_actions (List[str]): the following actions. 
        msg_type (str): the type of the message, such as "request", "response", "command" etc. 
        wf_goal (str): the goal of the whole workflow. 
        wf_task (str): the name of a task in the workflow, i.e., the ``name`` of a WorkFlowNode instance. 
        wf_task_desc (str): the description of a task in the workflow, i.e., the ``description`` of a WorkFlowNode instance.
        message_id (str): the unique identifier of the message. 
        timestamp (str): the timestame of the message. 
    """
    content: Any
    agent: Optional[str] = None
    action: Optional[str] = None
    prompt: Optional[Union[str, List[dict]]] = None
    next_actions: Optional[List[str]] = None
    msg_type: Optional[MessageType] = MessageType.UNKNOWN
    wf_goal: Optional[str] = None
    wf_task: Optional[str] = None
    wf_task_desc: Optional[str] = None
    message_id: Optional[str] = Field(default_factory=generate_id)
    timestamp: Optional[str] = Field(default_factory=get_timestamp)
    conversation_id: Optional[str] = Field(default_factory=generate_id)

    def __str__(self) -> str:
        return self.to_str()

    def __eq__(self, other: 'Message'):
        return self.message_id == other.message_id

    def __hash__(self):
        return self.message_id

    def to_str(self) -> str:
        msg_part = []
        if self.timestamp:
            msg_part.append(f'[{self.timestamp}]')
        if self.agent:
            msg_part.append(f'Agent: {self.agent}')
        if self.msg_type and self.msg_type != MessageType.UNKNOWN:
            msg_part.append(f'Type: {self.msg_type}')
        if self.action:
            msg_part.append(f'Action: {self.action}')
        if self.wf_goal:
            msg_part.append(f'Goal: {self.wf_goal}')
        if self.wf_task:
            msg_part.append(f'Task: {self.wf_task} ({self.wf_task_desc or 'No description'})')
        if self.content:
            msg_part.append(f'Content: {str(self.content)}')
        msg = '\n'.join(msg_part)
        return msg

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        """
        Convert the Message to a dictionary for saving. 
        """
        data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
        if self.msg_type:
            data['msg_type'] = self.msg_type.value
        return data

    @model_validator(mode='before')
    @classmethod
    def validate_data(cls, data: Any) -> Any:
        if 'msg_type' in data and data['msg_type'] and isinstance(data['msg_type'], str):
            data['msg_type'] = MessageType(data['msg_type'])
        return data

    @classmethod
    def sort_by_timestamp(cls, messages: List['Message'], reverse: bool=False) -> List['Message']:
        """
        sort the messages based on the timestamp. 

        Args: 
            messages (List[Message]): the messages to be sorted. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
        messages.sort(key=lambda msg: datetime.strptime(msg.timestamp, '%Y-%m-%d %H:%M:%S'), reverse=reverse)
        return messages

    @classmethod
    def sort(cls, messages: List['Message'], key: Optional[Callable[['Message'], Any]]=None, reverse: bool=False) -> List['Message']:
        """
        sort the messages using key or timestamp (by default). 

        Args:
            messages (List[Message]): the messages to be sorted. 
            key (Optional[Callable[['Message'], Any]]): the function used to sort messages. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
        if key is None:
            return cls.sort_by_timestamp(messages, reverse=reverse)
        messages.sort(key=key, reverse=reverse)
        return messages

    @classmethod
    def merge(cls, messages: List[List['Message']], sort: bool=False, key: Optional[Callable[['Message'], Any]]=None, reverse: bool=False) -> List['Message']:
        """
        merge different message list. 

        Args:
            messages (List[List[Message]]): the message lists to be merged. 
            sort (bool): whether to sort the merged messages.
            key (Optional[Callable[['Message'], Any]]): the function used to sort messages. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
        merged_messages = sum(messages, [])
        if sort:
            merged_messages = cls.sort(merged_messages, key=key, reverse=reverse)
        return merged_messages

@classmethod
def sort_by_timestamp(cls, messages: List['Message'], reverse: bool=False) -> List['Message']:
    """
        sort the messages based on the timestamp. 

        Args: 
            messages (List[Message]): the messages to be sorted. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
    messages.sort(key=lambda msg: datetime.strptime(msg.timestamp, '%Y-%m-%d %H:%M:%S'), reverse=reverse)
    return messages

@classmethod
def merge(cls, messages: List[List['Message']], sort: bool=False, key: Optional[Callable[['Message'], Any]]=None, reverse: bool=False) -> List['Message']:
    """
        merge different message list. 

        Args:
            messages (List[List[Message]]): the message lists to be merged. 
            sort (bool): whether to sort the merged messages.
            key (Optional[Callable[['Message'], Any]]): the function used to sort messages. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
    merged_messages = sum(messages, [])
    if sort:
        merged_messages = cls.sort(merged_messages, key=key, reverse=reverse)
    return merged_messages

class BaseModule(BaseModel, metaclass=MetaModule):
    """
    Base module class that serves as the foundation for all modules in the EvoAgentX framework.
    
    This class provides serialization/deserialization capabilities, supports creating instances from
    dictionaries, JSON, or files, and exporting instances to these formats.
    
    Attributes:
        class_name: The class name, defaults to None but is automatically set during subclass initialization
        model_config: Pydantic model configuration that controls type matching and behavior
    """
    class_name: str = None
    model_config = {'arbitrary_types_allowed': True, 'extra': 'allow', 'protected_namespaces': (), 'validate_assignment': False}

    def __init_subclass__(cls, **kwargs):
        """
        Subclass initialization method that automatically sets the class_name attribute.
        
        Args:
            cls (Type): The subclass being initialized
            **kwargs (Any): Additional keyword arguments
        """
        super().__init_subclass__(**kwargs)
        cls.class_name = cls.__name__

    def __init__(self, **kwargs):
        """
        Initializes a BaseModule instance.
        
        Args:
            **kwargs (Any): Keyword arguments used to initialize the instance
        
        Raises:
            ValidationError: When parameter validation fails
            Exception: When other errors occur during initialization
        """
        try:
            for field_name, _ in type(self).model_fields.items():
                field_value = kwargs.get(field_name, None)
                if field_value:
                    kwargs[field_name] = self._process_data(field_value)
            super().__init__(**kwargs)
            self.init_module()
        except (ValidationError, Exception) as e:
            exception_handler = callback_manager.get_callback('exception_buffer')
            if exception_handler is None:
                error_message = get_base_module_init_error_message(cls=self.__class__, data=kwargs, errors=e)
                logger.error(error_message)
                raise
            else:
                exception_handler.add(e)

    def init_module(self):
        """
        Module initialization method that subclasses can override to provide additional initialization logic.
        """
        pass

    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        
        Returns:
            str: String representation of the object
        """
        return self.to_str()

    @property
    def kwargs(self) -> dict:
        """
        Returns the extra fields of the model.
        
        Returns:
            dict: Dictionary containing all extra keyword arguments
        """
        return self.model_extra

    @classmethod
    def _create_instance(cls, data: Dict[str, Any]) -> 'BaseModule':
        """
        Internal method for creating an instance from a dictionary.
        
        Args:
            data: Dictionary containing instance data
        
        Returns:
            BaseModule: The created instance
        """
        processed_data = {k: cls._process_data(v) for k, v in data.items()}
        return cls.model_validate(processed_data)

    @classmethod
    def _process_data(cls, data: Any) -> Any:
        """
        Recursive method for processing data, with special handling for dictionaries containing class_name.
        
        Args:
            data: Data to be processed
        
        Returns:
            Processed data
        """
        if isinstance(data, dict):
            if 'class_name' in data:
                sub_class = MODULE_REGISTRY.get_module(data.get('class_name'))
                return sub_class._create_instance(data)
            else:
                return {k: cls._process_data(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [cls._process_data(x) for x in data]
        else:
            return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> 'BaseModule':
        """
        Instantiate the BaseModule from a dictionary.
        
        Args:
            data: Dictionary containing instance data
            **kwargs (Any): Additional keyword arguments, can include log to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            Exception: When errors occur during initialization
        """
        use_logger = kwargs.get('log', True)
        with exception_buffer() as buffer:
            try:
                class_name = data.get('class_name', None)
                if class_name:
                    cls = MODULE_REGISTRY.get_module(class_name)
                module = cls._create_instance(data)
                if len(buffer.exceptions) > 0:
                    error_message = get_base_module_init_error_message(cls, data, buffer.exceptions)
                    if use_logger:
                        logger.error(error_message)
                    raise Exception(get_error_message(buffer.exceptions))
            finally:
                pass
        return module

    @classmethod
    def from_json(cls, content: str, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a JSON string.
        
        This method uses yaml.safe_load to parse the JSON string into a Python object,
        which supports more flexible parsing than standard json.loads (including handling
        single quotes, trailing commas, etc). The parsed data is then passed to from_dict
        to create the instance.
        
        Args:
            content: JSON string
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input is not a valid JSON string
        """
        use_logger = kwargs.get('log', True)
        try:
            data = yaml.safe_load(content)
        except Exception:
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        if not isinstance(data, (list, dict)):
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        return cls.from_dict(data, log=use_logger)

    @classmethod
    def from_str(cls, content: str, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a string that may contain JSON.
        
        This method is more forgiving than `from_json` as it can extract valid JSON
        objects embedded within larger text. It uses `parse_json_from_text` to extract 
        all potential JSON strings from the input text, then tries to create an instance 
        from each extracted JSON string until successful.
        
        Args:
            content: Text that may contain JSON strings
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input does not contain valid JSON strings or the JSON is incompatible with the class
        """
        use_logger = kwargs.get('log', True)
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) == 0:
            error_message = f'The input to {cls.__name__}.from_str does not contain any valid JSON str.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        module = None
        for json_str in extracted_json_list:
            try:
                module = cls.from_json(json_str, log=False)
            except Exception:
                continue
            break
        if module is None:
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_str either does not contain a valide JSON str, or the JSON str is incomplete or incompatable (incorrect variables or types) with {cls.__name__}.'
            error_message += f'\nInput:\n{content}'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        return module

    @classmethod
    def load_module(cls, path: str, **kwargs) -> dict:
        """
        Load the values for a module from a file.
        
        By default, it opens the specified file and uses `yaml.safe_load` to parse its contents 
        into a Python object (typically a dictionary).
        
        Args:
            path: The path of the file
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            dict: The JSON object instantiated from the file
        """
        with open(path, mode='r', encoding='utf-8') as file:
            content = yaml.safe_load(file.read())
        return content

    @classmethod
    def from_file(cls, path: str, load_function: Callable=None, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a file.
        
        This method reads and parses a file into a data structure, then creates
        a module instance from that data. It first verifies that the file exists,
        then uses either the provided `load_function` or the default `load_module`
        method to read and parse the file content, and finally calls `from_dict`
        to create the instance.
        
        Args:
            path: The path of the file
            load_function: The function used to load the data, takes a file path as input and returns a JSON object
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the file does not exist
        """
        use_logger = kwargs.get('log', True)
        if not os.path.exists(path):
            error_message = f'File "{path}" does not exist!'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        function = load_function or cls.load_module
        content = function(path, **kwargs)
        module = cls.from_dict(content, log=use_logger)
        return module

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        """
        Convert the BaseModule to a dictionary.
        
        Args:
            exclude_none: Whether to exclude fields with None values
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            dict: Dictionary containing the object data
        """
        data = {}
        for field_name, _ in type(self).model_fields.items():
            if field_name in ignore:
                continue
            field_value = getattr(self, field_name, None)
            if exclude_none and field_value is None:
                continue
            if isinstance(field_value, BaseModule):
                data[field_name] = field_value.to_dict(exclude_none=exclude_none, ignore=ignore)
            elif isinstance(field_value, list):
                data[field_name] = [item.to_dict(exclude_none=exclude_none, ignore=ignore) if isinstance(item, BaseModule) else item for item in field_value]
            elif isinstance(field_value, dict):
                data[field_name] = {key: value.to_dict(exclude_none=exclude_none, ignore=ignore) if isinstance(value, BaseModule) else value for key, value in field_value.items()}
            else:
                data[field_name] = field_value
        return data

    def to_json(self, use_indent: bool=False, ignore: List[str]=[], **kwargs) -> str:
        """
        Convert the BaseModule to a JSON string.
        
        Args:
            use_indent: Whether to use indentation
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The JSON string
        """
        if use_indent:
            kwargs['indent'] = kwargs.get('indent', 4)
        else:
            kwargs.pop('indent', None)
        if kwargs.get('default', None) is None:
            kwargs['default'] = custom_serializer
        data = self.to_dict(exclude_none=True)
        for ignore_field in ignore:
            data.pop(ignore_field, None)
        return json.dumps(data, **kwargs)

    def to_str(self, **kwargs) -> str:
        """
        Convert the BaseModule to a string. Use .to_json to output JSON string by default.
        
        Args:
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The string
        """
        return self.to_json(use_indent=False)

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """
        Save the BaseModule to a file.
        
        This method will set non-serializable objects to None by default.
        If you want to save non-serializable objects, override this method.
        Remember to also override the `load_module` function to ensure the loaded
        object can be correctly parsed by `cls.from_dict`.
        
        Args:
            path: The path to save the file
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The path where the file is saved, same as the input path
        """
        logger.info('Saving {} to {}', self.__class__.__name__, path)
        return save_json(self.to_json(use_indent=True, default=lambda x: None, ignore=ignore), path=path)

    def deepcopy(self):
        """Deep copy the module.

        This is a tweak to the default python deepcopy that only deep copies `self.parameters()`, and for other
        attributes, we just do the shallow copy.
        """
        try:
            return copy.deepcopy(self)
        except Exception:
            pass
        new_instance = self.__class__.__new__(self.__class__)
        for attr, value in self.__dict__.items():
            if isinstance(value, BaseModule):
                setattr(new_instance, attr, value.deepcopy())
            else:
                try:
                    setattr(new_instance, attr, copy.deepcopy(value))
                except Exception:
                    logging.warning(f"Failed to deep copy attribute '{attr}' of {self.__class__.__name__}, falling back to shallow copy or reference copy.")
                    try:
                        setattr(new_instance, attr, copy.copy(value))
                    except Exception:
                        setattr(new_instance, attr, value)
        return new_instance

@classmethod
def from_str(cls, content: str, **kwargs) -> 'BaseModule':
    """
        Construct the BaseModule from a string that may contain JSON.
        
        This method is more forgiving than `from_json` as it can extract valid JSON
        objects embedded within larger text. It uses `parse_json_from_text` to extract 
        all potential JSON strings from the input text, then tries to create an instance 
        from each extracted JSON string until successful.
        
        Args:
            content: Text that may contain JSON strings
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input does not contain valid JSON strings or the JSON is incompatible with the class
        """
    use_logger = kwargs.get('log', True)
    extracted_json_list = parse_json_from_text(content)
    if len(extracted_json_list) == 0:
        error_message = f'The input to {cls.__name__}.from_str does not contain any valid JSON str.'
        if use_logger:
            logger.error(error_message)
        raise ValueError(error_message)
    module = None
    for json_str in extracted_json_list:
        try:
            module = cls.from_json(json_str, log=False)
        except Exception:
            continue
        break
    if module is None:
        error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_str either does not contain a valide JSON str, or the JSON str is incomplete or incompatable (incorrect variables or types) with {cls.__name__}.'
        error_message += f'\nInput:\n{content}'
        if use_logger:
            logger.error(error_message)
        raise ValueError(error_message)
    return module

class BaseMemory(BaseModule):
    """Base class for memory implementations in the EvoAgentX framework.
    
    BaseMemory provides core functionality for storing, retrieving, and 
    filtering messages. It maintains a chronological list of messages while 
    also providing indices for efficient retrieval by action or workflow goal.
    
    Attributes:
        messages: List of stored Message objects.
        memory_id: Unique identifier for this memory instance.
        timestamp: Creation timestamp of this memory instance.
        capacity: Maximum number of messages that can be stored, or None for unlimited.
    """
    messages: List[Message] = Field(default_factory=list)
    memory_id: str = Field(default_factory=generate_id)
    timestamp: str = Field(default_factory=get_timestamp)
    capacity: Optional[PositiveInt] = Field(default=None, description='maximum of messages, None means there is no limit to the message number')

    def init_module(self):
        """Initialize memory indices.
        
        Creates default dictionaries for indexing messages by action and workflow goal.
        """
        self._by_action = defaultdict(list)
        self._by_wf_goal = defaultdict(list)

    @property
    def size(self) -> int:
        """Returns the current number of messages in memory.
        
        Returns:
            int: Number of messages currently stored.
        """
        return len(self.messages)

    def clear(self):
        """Clear all messages from memory.
        
        Removes all messages and resets all indices.
        """
        self.messages.clear()
        self._by_action.clear()
        self._by_wf_goal.clear()

    def remove_message(self, message: Message):
        """Remove a single message from memory.
        
        Removes the specified message from the main message list and all indices.
        If the message is not found in memory, no action is taken.
        
        Args:
            message: The message to be removed. The message will be removed from 
                   self.messages, self._by_action, and self._by_wf_goal.
        """
        if not message:
            return
        if message not in self.messages:
            return
        safe_remove(self.messages, message)
        if self._by_action and (not message.action):
            safe_remove(self._by_action[message.action], message)
        if self._by_wf_goal and (not message.wf_goal):
            safe_remove(self._by_wf_goal[message.wf_goal], message)

    def add_message(self, message: Message):
        """Store a single message in memory.
        
        Adds the message to the main list and relevant indices if it's not already stored.
        
        Args:
            message (Message): the message to be stored. 
        """
        if not message:
            return
        if message in self.messages:
            return
        self.messages.append(message)
        if self._by_action and (not message.action):
            self._by_action[message.action].append(message)
        if self._by_wf_goal and (not message.wf_goal):
            self._by_wf_goal[message.wf_goal].append(message)

    def add_messages(self, messages: Union[Message, List[Message]], **kwargs):
        """
        store (a) message(s) to the memory. 

        Args:
            messages (Union[Message, List[Message]]): the input messages can be a single message or a list of message.
        """
        if not isinstance(messages, list):
            messages = [messages]
        for message in messages:
            self.add_message(message)

    def get(self, n: int=None, **kwargs) -> List[Message]:
        """Retrieve recent messages from memory.
        
        Returns the most recent messages, up to the specified limit.
        
        Args: 
            n: The maximum number of messages to return. If None, returns all messages.
            **kwargs (Any): Additional parameters (unused in base implementation).
            
        Returns:
            A list of Message objects, ordered from oldest to newest.
            
        Raises:
            AssertionError: If n is negative.
        """
        assert n is None or n >= 0, 'n must be None or a positive int'
        messages = self.messages if n is None else self.messages[-n:]
        return messages

    def get_by_type(self, data: Dict[str, list], key: str, n: int=None, **kwargs) -> List[Message]:
        """
        Retrieve a list of Message objects from a given data dictionary `data` based on a specified type `key`.

        This function looks up the value associated with `key` in the `data` dictionary, which should be a list of messages. It then returns a subset of these messages according to the specified parameters.
        If `n` is provided, it limits the number of messages returned; otherwise, it may return the entire list. Additional keyword arguments (**kwargs) can be used to further filter or process the resulting messages.

        Args:
            data (Dict[str, list]): A dictionary where keys are type strings and values are lists of messages.
            key (str): The key in `data` identifying the specific list of messages to retrieve.
            n (int, optional): The maximum number of messages to return. If not provided, all messages under the given `key` may be returned.
            **kwargs (Any): Additional parameters for filtering or processing the messages.

        Returns:
            List[Message]: A list of messages corresponding to the given `key`, possibly filtered or truncated according to `n` and other provided keyword arguments.
        """
        if not data or key not in data:
            return []
        assert n is None or n >= 0, 'n must be None or a positive int'
        messages = data[key] if n is None else data[key][-n:]
        return messages

    def get_by_action(self, actions: Union[str, List[str]], n: int=None, **kwargs) -> List[Message]:
        """
        return messages triggered by `actions` in the memory. 

        Args:
            actions: A single action name or list of action names to filter by.
            n: Maximum number of messages to return per action. If None, returns all matching messages.
            **kwargs (Any): Additional parameters (unused in base implementation).
            
        Returns:
            A list of Message objects, sorted by timestamp.
        """
        if isinstance(actions, str):
            actions = [actions]
        messages = []
        for action in actions:
            messages.extend(self.get_by_type(self._by_action, key=action, n=n, **kwargs))
        messages = Message.sort_by_timestamp(messages)
        return messages

    def get_by_wf_goal(self, wf_goals: Union[str, List[str]], n: int=None, **kwargs) -> List[Message]:
        """
        return messages related to `wf_goals` in the memory. 

        Args:
            wf_goals: A single workflow goal or list of workflow goals to filter by.
            n: Maximum number of messages to return per workflow goal. If None, returns all matching messages.
            **kwargs (Any): Additional parameters (unused in base implementation).
            
        Returns:
            A list of Message objects, sorted by timestamp.
        """
        if isinstance(wf_goals, str):
            wf_goals = [wf_goals]
        messages = []
        for wf_goal in wf_goals:
            messages.append(self.get_by_type(self._by_wf_goal, key=wf_goal, n=n, **kwargs))
        messages = Message.sort_by_timestamp(messages)
        return messages

@property
def size(self) -> int:
    """Returns the current number of messages in memory.
        
        Returns:
            int: Number of messages currently stored.
        """
    return len(self.messages)

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

def get_completion_params(self, **kwargs):
    completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
    completion_params = self.update_completion_params(completion_params, kwargs)
    return completion_params

@register_model(config_cls=AliyunLLMConfig, alias=['aliyun_llm'])
class AliyunLLM(BaseLLM):

    def init_model(self):
        """
        Initialize the DashScope Generation client.
        """
        config: AliyunLLMConfig = self.config
        if not config.aliyun_api_key:
            raise ValueError('Aliyun API key is required. You should set `aliyun_api_key` in AliyunLLMConfig')
        os.environ['DASHSCOPE_API_KEY'] = config.aliyun_api_key
        dashscope.api_key = config.aliyun_api_key
        self._client = Generation()
        self._default_ignore_fields = ['llm_type', 'output_response', 'aliyun_api_key', 'aliyun_access_key_id', 'aliyun_access_key_secret', 'model_name']

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        """
        Format messages for the Aliyun model.
        
        Args:
            prompts (List[str]): List of user prompts.
            system_messages (Optional[List[str]]): Optional list of system messages.
            
        Returns:
            List[List[dict]]: Formatted messages for the model.
        """
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
        """
        Update completion parameters with new values.
        
        Args:
            params1 (dict): Base parameters.
            params2 (dict): New parameters to update with.
            
        Returns:
            dict: Updated parameters.
        """
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        """
        Get completion parameters for the model.
        
        Returns:
            dict: Parameters for model completion.
        """
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        completion_params['model'] = self.config.model
        return completion_params

    def get_stream_output(self, response: Any, output_response: bool=True) -> str:
        """
        Process streaming response from the model.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        output = ''
        try:
            for chunk in response:
                if not hasattr(chunk, 'output') or chunk.output is None:
                    error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                    raise ValueError(f'Model stream chunk error: {error_msg}')
                if hasattr(chunk.output, 'text'):
                    content = chunk.output.text
                elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                    content = chunk.output.choices[0].message.content
                else:
                    continue
                if content:
                    if output_response:
                        print(content, end='', flush=True)
                    output += content
        except Exception as e:
            print(f'Error processing stream: {str(e)}')
            if not output:
                raise RuntimeError(f'Failed to process stream response: {str(e)}')
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response: Any, output_response: bool=False) -> str:
        """
        Process streaming response asynchronously.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        output = ''
        try:
            async for chunk in response:
                if not hasattr(chunk, 'output') or chunk.output is None:
                    error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                    raise ValueError(f'Model stream chunk error: {error_msg}')
                if hasattr(chunk.output, 'text'):
                    content = chunk.output.text
                elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                    content = chunk.output.choices[0].message.content
                else:
                    continue
                if content:
                    if output_response:
                        print(content, end='', flush=True)
                    output += content
        except Exception as e:
            print(f'Error processing async stream: {str(e)}')
            if not output:
                raise RuntimeError(f'Failed to process async stream response: {str(e)}')
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: Any, output_response: bool=True) -> str:
        """
        Process non-streaming response from the model.
        
        Args:
            response: The response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        try:
            if not hasattr(response, 'output') or response.output is None:
                error_msg = getattr(response, 'message', 'Invalid response format from model')
                raise ValueError(f'Model response error: {error_msg}')
            if hasattr(response.output, 'text'):
                output = response.output.text
            elif hasattr(response.output, 'choices') and response.output.choices:
                output = response.output.choices[0].message.content
            else:
                raise ValueError('Unexpected response format')
            if output_response:
                print(output)
            return output
        except Exception as e:
            raise RuntimeError(f'Error processing completion response: {str(e)}')

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response from the model.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for generation.
            
        Returns:
            str: The generated response.
        """
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.call(messages=messages, **completion_params)
            if response is None:
                raise RuntimeError('Received empty response from model')
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(response)
            else:
                output = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
            return output
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of AliyunLLM: {str(e)}')

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """
        Generate responses for a batch of messages.
        
        Args:
            batch_messages (List[List[dict]]): List of conversation histories.
            **kwargs: Additional parameters for generation.
            
        Returns:
            List[str]: List of generated responses.
        """
        if not isinstance(batch_messages, list) or not batch_messages:
            raise ValueError('batch_messages must be a non-empty list of message lists')
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """
        Asynchronously generate a single response.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for the generation.
            
        Returns:
            str: The generated response.
        """
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self._client.call(messages=messages, **completion_params))
            if stream:
                output = await self.get_stream_output_async(response, output_response=output_response)
                cost = self._stream_cost(response)
            else:
                output = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
            return output
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of AliyunLLM: {str(e)}')

    def _completion_cost(self, response: Any) -> Cost:
        """cost"""
        try:
            if not response:
                return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                elif hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                elif hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
            if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
                if hasattr(response.output, 'text'):
                    output_tokens = len(response.output.text.split()) * 1.3
                elif hasattr(response.output, 'choices') and response.output.choices:
                    output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
            total_cost = self._estimate_cost(input_tokens, output_tokens)
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
        except Exception as e:
            logger.warning(f'Error computing completion cost: {str(e)}')
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

    def _stream_cost(self, response: Any) -> Cost:
        """cost"""
        try:
            if not response:
                return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                elif hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                elif hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
            if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
                if hasattr(response.output, 'text'):
                    output_tokens = len(response.output.text.split()) * 1.3
                elif hasattr(response.output, 'choices') and response.output.choices:
                    output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
            total_cost = self._estimate_cost(input_tokens, output_tokens)
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
        except Exception as e:
            logger.warning(f'Error computing stream cost: {str(e)}')
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """cost
        
        """
        model = self.config.model.lower()
        if 'turbo' in model:
            input_cost = input_tokens / 1000 * 0.0005
            output_cost = output_tokens / 1000 * 0.001
        elif 'max' in model:
            input_cost = input_tokens / 1000 * 0.002
            output_cost = output_tokens / 1000 * 0.004
        else:
            input_cost = input_tokens / 1000 * 0.001
            output_cost = output_tokens / 1000 * 0.002
        return input_cost + output_cost

    def _update_cost(self, cost: Cost):
        """
        Update the cost manager with the new cost.
        
        Args:
            cost (Cost): The cost to update.
        """
        try:
            cost_manager.update_cost(cost=cost, model=self.config.model)
        except Exception as e:
            logger.warning(f'Error updating cost: {str(e)}')

def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
    """
        Format messages for the Aliyun model.
        
        Args:
            prompts (List[str]): List of user prompts.
            system_messages (Optional[List[str]]): Optional list of system messages.
            
        Returns:
            List[List[dict]]: Formatted messages for the model.
        """
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

def get_completion_params(self, **kwargs):
    """
        Get completion parameters for the model.
        
        Returns:
            dict: Parameters for model completion.
        """
    completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
    completion_params = self.update_completion_params(completion_params, kwargs)
    completion_params['model'] = self.config.model
    return completion_params

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

def get_completion_params(self, **kwargs):
    completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
    completion_params = self.update_completion_params(completion_params, kwargs)
    return completion_params

class HumanEvalSplits(HumanEval):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        num_dev_samples = int(len(self._test_data) * 0.2)
        random_indices = np.random.permutation(len(self._test_data))
        self._dev_data = [self._test_data[i] for i in random_indices[:num_dev_samples]]
        self._test_data = [self._test_data[i] for i in random_indices[num_dev_samples:]]

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    num_dev_samples = int(len(self._test_data) * 0.2)
    random_indices = np.random.permutation(len(self._test_data))
    self._dev_data = [self._test_data[i] for i in random_indices[:num_dev_samples]]
    self._test_data = [self._test_data[i] for i in random_indices[num_dev_samples:]]

class MathSplits(MATH):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._test_data))
        full_test_data = self._test_data
        self._train_data = [full_test_data[idx] for idx in permutation[:100]]
        self._test_data = [full_test_data[idx] for idx in permutation[100:200]]

    def get_input_keys(self):
        return ['problem']

    def evaluate(self, prediction: Any, label: Any) -> dict:
        return super().evaluate(prediction, label)

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._test_data))
    full_test_data = self._test_data
    self._train_data = [full_test_data[idx] for idx in permutation[:100]]
    self._test_data = [full_test_data[idx] for idx in permutation[100:200]]

def evaluate(self, prediction: Any, label: Any) -> dict:
    return super().evaluate(prediction, label)

class MathSplits(MATH):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._test_data))
        full_test_data = self._test_data
        self._train_data = [full_test_data[idx] for idx in permutation[:100]]
        self._test_data = [full_test_data[idx] for idx in permutation[100:200]]

    def get_input_keys(self):
        return ['problem']

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._test_data))
    full_test_data = self._test_data
    self._train_data = [full_test_data[idx] for idx in permutation[:100]]
    self._test_data = [full_test_data[idx] for idx in permutation[100:200]]

class MBPPSplits(MBPP):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._test_data))
        full_test_data = self._test_data
        self._train_data = [full_test_data[idx] for idx in permutation[:10]]
        self._dev_data = [full_test_data[idx] for idx in permutation[10:50]]
        self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._test_data))
    full_test_data = self._test_data
    self._train_data = [full_test_data[idx] for idx in permutation[:10]]
    self._dev_data = [full_test_data[idx] for idx in permutation[10:50]]
    self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

class MathSplits(MATH):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._test_data))
        full_test_data = self._test_data
        self._train_data = [full_test_data[idx] for idx in permutation[:10]]
        self._dev_data = [full_test_data[idx] for idx in permutation[10:50]]
        self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._test_data))
    full_test_data = self._test_data
    self._train_data = [full_test_data[idx] for idx in permutation[:10]]
    self._dev_data = [full_test_data[idx] for idx in permutation[10:50]]
    self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

class HotPotQASplits(HotPotQA):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._dev_data))
        full_test_data = self._dev_data
        self._train_data = [full_test_data[idx] for idx in permutation[:10]]
        self._dev_data = [full_test_data[idx] for idx in permutation[10:50]]
        self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._dev_data))
    full_test_data = self._dev_data
    self._train_data = [full_test_data[idx] for idx in permutation[:10]]
    self._dev_data = [full_test_data[idx] for idx in permutation[10:50]]
    self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

class HotPotQASplits(HotPotQA):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._dev_data))
        full_test_data = self._dev_data
        self._dev_data = [full_test_data[idx] for idx in permutation[:50]]
        self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

    async def async_evaluate(self, graph: Callable, example: Any) -> float:
        prompt = example['question']
        paragraphs = [item[1] for item in example['context'] if isinstance(item[1], list)]
        context_str = '\n'.join((' '.join(paragraph) for paragraph in paragraphs))
        inputs = f'Context: {context_str}\n\nQuestion: {prompt}\n\nAnswer:'
        solution = await graph(inputs)
        label = self._get_label(example)
        metrics = await super().async_evaluate(prediction=solution, label=label)
        return metrics['f1']

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._dev_data))
    full_test_data = self._dev_data
    self._dev_data = [full_test_data[idx] for idx in permutation[:50]]
    self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

class MBPPSplits(AFlowMBPP):

    def _load_data(self):
        mbpp_test_data = MBPP().get_test_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(mbpp_test_data))
        dev_data_task_ids = [mbpp_test_data[idx]['task_id'] for idx in permutation[:50]]
        test_data_task_ids = [mbpp_test_data[idx]['task_id'] for idx in permutation[50:150]]
        super()._load_data()
        full_data = self._dev_data + self._test_data
        self._dev_data = [example for example in full_data if example['task_id'] in dev_data_task_ids]
        self._test_data = [example for example in full_data if example['task_id'] in test_data_task_ids]

def _load_data(self):
    mbpp_test_data = MBPP().get_test_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(mbpp_test_data))
    dev_data_task_ids = [mbpp_test_data[idx]['task_id'] for idx in permutation[:50]]
    test_data_task_ids = [mbpp_test_data[idx]['task_id'] for idx in permutation[50:150]]
    super()._load_data()
    full_data = self._dev_data + self._test_data
    self._dev_data = [example for example in full_data if example['task_id'] in dev_data_task_ids]
    self._test_data = [example for example in full_data if example['task_id'] in test_data_task_ids]

class MathSplits(MATH):

    def _load_data(self):
        super()._load_data()
        import numpy as np
        np.random.seed(42)
        permutation = np.random.permutation(len(self._test_data))
        full_test_data = self._test_data
        self._dev_data = [full_test_data[idx] for idx in permutation[:50]]
        self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

    async def async_evaluate(self, graph: Callable, example: Any) -> float:
        problem = example['problem']
        label = self._get_label(example)
        output = await graph(problem)
        metrics = await super().async_evaluate(prediction=output, label=label)
        return metrics['solve_rate']

def _load_data(self):
    super()._load_data()
    import numpy as np
    np.random.seed(42)
    permutation = np.random.permutation(len(self._test_data))
    full_test_data = self._test_data
    self._dev_data = [full_test_data[idx] for idx in permutation[:50]]
    self._test_data = [full_test_data[idx] for idx in permutation[50:150]]

def evaluate_retrieval(retrieved_chunks: List[Chunk], supporting_facts: List[List], top_k: int) -> Dict[str, float]:
    """Evaluate retrieved chunks against supporting facts."""
    relevant = {(fact[0], fact[1]) for fact in supporting_facts}
    retrieved = []
    for chunk in retrieved_chunks[:top_k]:
        title = chunk.metadata.title
        sentence_idx = int(chunk.metadata.doc_id)
        retrieved.append((title, sentence_idx))
    hits = sum((1 for r in retrieved if r in relevant))
    precision = hits / top_k if top_k > 0 else 0.0
    recall = hits / len(relevant) if len(relevant) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0.0
    mrr = 0.0
    for rank, r in enumerate(retrieved, 1):
        if r in relevant:
            mrr = 1.0 / rank
            break
    hit = 1.0 if hits > 0 else 0.0
    intersection = set(((r[0], r[1]) for r in retrieved)) & relevant
    union = set(((r[0], r[1]) for r in retrieved)) | relevant
    jaccard = len(intersection) / len(union) if union else 0.0
    return {'precision@k': precision, 'recall@k': recall, 'f1@k': f1, 'mrr': mrr, 'hit@k': hit, 'jaccard': jaccard}

def collate_func(example: dict) -> dict:
    user_msg = [m['content'] for m in example['messages'] if m['role'] == 'user'][-1]
    assistant_msgs = [m['content'] for m in example['messages'] if m['role'] == 'assistant']
    example_workflow = assistant_msgs[-2] if len(assistant_msgs) >= 2 else ''
    prompt = f'{user_msg}\n\nPlease strictly output in the following format:\n<thought>Your reasoning process</thought>\n<answer>\nNode:\n1: ...\n2: ...\nEdge: (START,1) (1,2) ... (n,END)\n</answer>\nImportant notes:\n1. Carefully analyze task dependencies, some steps can be executed in parallel\n2. Ensure edge connections correctly reflect task dependencies\n3. Node count should match task complexity\n4. Use (START,1) for start, (n,END) for end\nExample:\n{example_workflow}\nOnly output your workflow, no extra content.'
    return {'problem': prompt}

def get_topological_features():
    """Calculate topological sorting and features"""
    queue = deque([node for node in node_ids if in_degree[node] == 0])
    topo_order = []
    visited = set()
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        topo_order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    features = {'node_count': len(node_ids), 'edge_count': len(edges), 'max_depth': len(topo_order), 'avg_branching': sum((len(graph[node]) for node in node_ids)) / len(node_ids) if node_ids else 0, 'parallel_paths': sum((1 for node in node_ids if len(graph[node]) > 1)), 'sequential_paths': sum((1 for node in node_ids if len(graph[node]) == 1))}
    return (features, topo_order)

def structural_similarity(pred_nodes, pred_edges, label_nodes, label_edges):
    """Calculate graph structure similarity"""
    try:
        pred_features, pred_topo = build_graph_structure(pred_nodes, pred_edges)
        label_features, label_topo = build_graph_structure(label_nodes, label_edges)
        feature_similarity = 0
        total_features = 0
        for key in pred_features:
            if key in label_features:
                pred_val = pred_features[key]
                label_val = label_features[key]
                if pred_val == 0 and label_val == 0:
                    similarity = 1.0
                elif pred_val == 0 or label_val == 0:
                    similarity = 0.0
                else:
                    similarity = min(pred_val, label_val) / max(pred_val, label_val)
                feature_similarity += similarity
                total_features += 1
        avg_feature_similarity = feature_similarity / total_features if total_features > 0 else 0.0
        topo_similarity = 0
        if pred_topo and label_topo:
            common_nodes = set(pred_topo) & set(label_topo)
            if common_nodes:
                pred_positions = {node: i for i, node in enumerate(pred_topo)}
                label_positions = {node: i for i, node in enumerate(label_topo)}
                position_diffs = []
                for node in common_nodes:
                    diff = abs(pred_positions[node] - label_positions[node])
                    position_diffs.append(diff)
                if position_diffs:
                    avg_diff = sum(position_diffs) / len(position_diffs)
                    max_possible_diff = max(len(pred_topo), len(label_topo))
                    topo_similarity = 1.0 - avg_diff / max_possible_diff
        return 0.6 * avg_feature_similarity + 0.4 * topo_similarity
    except Exception as e:
        print(f'Error calculating structural similarity: {e}')
        return 0.0

def improved_f1(set_pred, set_label, similarity_threshold=0.7):
    """Improved F1 calculation considering semantic similarity"""
    if not set_pred or not set_label:
        return 0.0
    exact_matches = len(set_pred & set_label)
    semantic_matches = 0
    for pred_item in set_pred:
        if pred_item in set_label:
            continue
        for label_item in set_label:
            if label_item in set_pred:
                continue
            if semantic_similarity(pred_item, label_item) >= similarity_threshold:
                semantic_matches += 1
                break
    total_matches = exact_matches + semantic_matches
    precision = total_matches / len(set_pred) if set_pred else 0.0
    recall = total_matches / len(set_label) if set_label else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

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

def test_empty_data_evaluation(self):
    self.benchmark.get_test_data.return_value = []
    results = self.evaluator.evaluate(graph=self.action_graph, benchmark=self.benchmark, eval_mode='test')
    self.assertEqual(results, {})
    self.assertEqual(len(self.evaluator.get_all_evaluation_records()), 0)

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

class TestWorkFlowEditor(unittest.IsolatedAsyncioTestCase):
    """Test the WorkFlowEditor class"""

    def setUp(self):
        """Test preparation"""
        os.environ['PYTEST_CURRENT_TEST'] = 'test_workflow_editor.py::TestWorkFlowEditor'
        self.temp_dir = tempfile.mkdtemp()
        self.test_workflow_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'output', 'tetris_game', 'workflow_demo_4o_mini.json')
        if not os.path.exists(self.test_workflow_file):
            self.test_workflow_file = os.path.join(self.temp_dir, 'test_workflow.json')
            test_workflow = {'nodes': [{'name': 'node1', 'type': 'start'}, {'name': 'node2', 'type': 'process'}, {'name': 'node3', 'type': 'end'}], 'edges': [{'source': 'node1', 'target': 'node2'}, {'source': 'node2', 'target': 'node3'}]}
            with open(self.test_workflow_file, 'w', encoding='utf-8') as f:
                json.dump(test_workflow, f, indent=2, ensure_ascii=False)
        self.test_instruction = 'delete the last node which is not useful in our case'
        with open(self.test_workflow_file, 'r', encoding='utf-8') as f:
            original_workflow = json.load(f)
        self.expected_optimized_workflow = original_workflow.copy()
        if self.expected_optimized_workflow['nodes']:
            last_node = self.expected_optimized_workflow['nodes'][-1]
            self.expected_optimized_workflow['nodes'] = self.expected_optimized_workflow['nodes'][:-1]
            self.expected_optimized_workflow['edges'] = [edge for edge in self.expected_optimized_workflow['edges'] if edge['target'] != last_node['name'] and edge['source'] != last_node['name']]

    def tearDown(self):
        """Test cleanup"""
        if 'PYTEST_CURRENT_TEST' in os.environ:
            del os.environ['PYTEST_CURRENT_TEST']
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_workflow_editor_instantiation(self):
        """Test the instantiation of the WorkFlowEditor class"""
        editor = WorkFlowEditor(save_dir=self.temp_dir)
        self.assertIsInstance(editor, WorkFlowEditor)
        self.assertEqual(editor.save_dir, self.temp_dir)
        self.assertEqual(editor.max_retries, 3)
        self.assertIsNotNone(editor.llm)
        custom_mock_llm = MockLLM()
        editor_custom = WorkFlowEditor(save_dir=self.temp_dir, llm=custom_mock_llm, max_retries=5)
        self.assertIsInstance(editor_custom, WorkFlowEditor)
        self.assertEqual(editor_custom.save_dir, self.temp_dir)
        self.assertEqual(editor_custom.max_retries, 5)
        self.assertEqual(editor_custom.llm, custom_mock_llm)

    @patch('evoagentx.workflow.workflow.WorkFlow')
    @patch('evoagentx.workflow.workflow_graph.WorkFlowGraph')
    async def test_edit_workflow_without_new_file_path(self, mock_workflow_graph, mock_workflow):
        """Test the edit_workflow method (without providing the new_file_path parameter)"""
        mock_workflow_graph.from_dict.return_value = MagicMock()
        mock_workflow.return_value = MagicMock()
        editor = WorkFlowEditor(save_dir=self.temp_dir)
        custom_mock_llm = MockLLM()

        async def mock_generate_async(messages, **kwargs):
            return json.dumps(self.expected_optimized_workflow)
        custom_mock_llm.single_generate_async = mock_generate_async
        editor.llm = custom_mock_llm
        result = await editor.edit_workflow(file_path=self.test_workflow_file, instruction=self.test_instruction)
        self.assertIsInstance(result, WorkFlowEditorReturn)
        self.assertEqual(result.status, 'success')
        self.assertIsNotNone(result.workflow_json)
        self.assertIsNotNone(result.workflow_json_path)
        self.assertIsNone(result.error_message)
        self.assertTrue(os.path.exists(result.workflow_json_path))
        self.assertIn('new_json_for__', os.path.basename(result.workflow_json_path))
        self.assertTrue(result.workflow_json_path.endswith('.json'))
        with open(result.workflow_json_path, 'r', encoding='utf-8') as f:
            saved_json = json.load(f)
        self.assertEqual(saved_json, self.expected_optimized_workflow)
        if os.path.exists(result.workflow_json_path):
            os.remove(result.workflow_json_path)

    @patch('evoagentx.workflow.workflow.WorkFlow')
    @patch('evoagentx.workflow.workflow_graph.WorkFlowGraph')
    async def test_edit_workflow_with_new_file_path(self, mock_workflow_graph, mock_workflow):
        """Test the edit_workflow method (with the new_file_path parameter)"""
        mock_workflow_graph.from_dict.return_value = MagicMock()
        mock_workflow.return_value = MagicMock()
        editor = WorkFlowEditor(save_dir=self.temp_dir)
        custom_mock_llm = MockLLM()

        async def mock_generate_async(messages, **kwargs):
            return json.dumps(self.expected_optimized_workflow)
        custom_mock_llm.single_generate_async = mock_generate_async
        editor.llm = custom_mock_llm
        temp_file_name = 'test_optimized_workflow.json'
        temp_file_path = os.path.join(self.temp_dir, temp_file_name)
        result = await editor.edit_workflow(file_path=self.test_workflow_file, instruction=self.test_instruction, new_file_path=temp_file_name)
        self.assertIsInstance(result, WorkFlowEditorReturn)
        self.assertEqual(result.status, 'success')
        self.assertIsNotNone(result.workflow_json)
        self.assertEqual(result.workflow_json_path, temp_file_path)
        self.assertIsNone(result.error_message)
        self.assertTrue(os.path.exists(result.workflow_json_path))
        with open(result.workflow_json_path, 'r', encoding='utf-8') as f:
            saved_json = json.load(f)
        self.assertEqual(saved_json, self.expected_optimized_workflow)
        if os.path.exists(result.workflow_json_path):
            os.remove(result.workflow_json_path)

    @patch('evoagentx.workflow.workflow.WorkFlow')
    @patch('evoagentx.workflow.workflow_graph.WorkFlowGraph')
    async def test_edit_workflow_llm_failure(self, mock_workflow_graph, mock_workflow):
        """Test the edit_workflow method when the LLM fails"""
        editor = WorkFlowEditor(save_dir=self.temp_dir)
        custom_mock_llm = MockLLM()

        async def mock_generate_async_failure(messages, **kwargs):
            raise Exception('LLM failure')
        custom_mock_llm.single_generate_async = mock_generate_async_failure
        editor.llm = custom_mock_llm
        result = await editor.edit_workflow(file_path=self.test_workflow_file, instruction=self.test_instruction)
        self.assertIsInstance(result, WorkFlowEditorReturn)
        self.assertEqual(result.status, 'failed')
        self.assertIsNone(result.workflow_json)
        self.assertIsNone(result.workflow_json_path)
        self.assertEqual(result.error_message, 'LLM optimization failed')

    @patch('evoagentx.workflow.workflow.WorkFlow')
    @patch('evoagentx.workflow.workflow_graph.WorkFlowGraph')
    async def test_edit_workflow_invalid_json_structure(self, mock_workflow_graph, mock_workflow):
        """Test the edit_workflow method when the workflow JSON structure validation fails"""
        editor = WorkFlowEditor(save_dir=self.temp_dir)
        custom_mock_llm = MockLLM()

        async def mock_generate_async_invalid(messages, **kwargs):
            return json.dumps({'invalid': 'structure'})
        custom_mock_llm.single_generate_async = mock_generate_async_invalid
        editor.llm = custom_mock_llm
        mock_workflow_graph.from_dict.side_effect = Exception('Invalid structure')
        result = await editor.edit_workflow(file_path=self.test_workflow_file, instruction=self.test_instruction)
        self.assertIsInstance(result, WorkFlowEditorReturn)
        self.assertEqual(result.status, 'failed')
        self.assertIsNone(result.workflow_json)
        self.assertIsNone(result.workflow_json_path)
        self.assertEqual(result.error_message, 'Workflow json structure check failed')

    async def test_edit_workflow_invalid_file_path(self):
        """Test the edit_workflow method when providing an invalid file path"""
        editor = WorkFlowEditor(save_dir=self.temp_dir)
        invalid_path = '/non_existent_directory/test.json'
        with self.assertRaises(FileNotFoundError):
            await editor.edit_workflow(file_path=self.test_workflow_file, instruction=self.test_instruction, new_file_path=invalid_path)

def test_workflow_editor_instantiation(self):
    """Test the instantiation of the WorkFlowEditor class"""
    editor = WorkFlowEditor(save_dir=self.temp_dir)
    self.assertIsInstance(editor, WorkFlowEditor)
    self.assertEqual(editor.save_dir, self.temp_dir)
    self.assertEqual(editor.max_retries, 3)
    self.assertIsNotNone(editor.llm)
    custom_mock_llm = MockLLM()
    editor_custom = WorkFlowEditor(save_dir=self.temp_dir, llm=custom_mock_llm, max_retries=5)
    self.assertIsInstance(editor_custom, WorkFlowEditor)
    self.assertEqual(editor_custom.save_dir, self.temp_dir)
    self.assertEqual(editor_custom.max_retries, 5)
    self.assertEqual(editor_custom.llm, custom_mock_llm)

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

class TestWorkFlowManager(unittest.TestCase):

    def setUp(self):
        self.mock_llm = Mock(spec=BaseLLM)
        self.mock_llm.generate = Mock()
        self.mock_llm.async_generate = AsyncMock()
        self.task_output = TaskSchedulerOutput(decision='forward', task_name='Task2', reason='This is the next logical step')
        self.action_output = NextAction(agent='TestAgent', action='TestAction', reason='This is the appropriate action')
        self.mock_llm.generate.return_value = self.task_output
        self.mock_llm.async_generate.return_value = self.task_output
        self.workflow_manager = WorkFlowManager(llm=self.mock_llm)
        self.create_test_workflow()
        self.env = Environment()

    def create_test_workflow(self):
        """Create a test workflow with 3 tasks in sequence"""
        task1 = WorkFlowNode(name='Task1', description='First task', inputs=[Parameter(name='input1', type='string', description='Input 1')], outputs=[Parameter(name='output1', type='string', description='Output 1')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        task2 = WorkFlowNode(name='Task2', description='Second task', inputs=[Parameter(name='output1', type='string', description='Output from Task1')], outputs=[Parameter(name='output2', type='string', description='Output 2')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        task3 = WorkFlowNode(name='Task3', description='Third task', inputs=[Parameter(name='output2', type='string', description='Output from Task2')], outputs=[Parameter(name='final_output', type='string', description='Final output')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        edge1 = WorkFlowEdge(source='Task1', target='Task2')
        edge2 = WorkFlowEdge(source='Task2', target='Task3')
        self.workflow = WorkFlowGraph(goal='Test Workflow', nodes=[task1, task2, task3], edges=[edge1, edge2])

    def test_workflow_initialization(self):
        """Test that the workflow manager is correctly initialized"""
        self.assertIsNotNone(self.workflow_manager)
        self.assertEqual(self.mock_llm, self.workflow_manager.llm)
        self.assertIsNotNone(self.workflow_manager.task_scheduler)
        self.assertIsNotNone(self.workflow_manager.action_scheduler)

    @pytest.mark.asyncio
    @patch('evoagentx.workflow.workflow_manager.TaskScheduler.async_execute')
    async def test_sync_task_scheduling_with_single_task(self, mock_task_scheduler_execute):
        """Test that the task scheduler correctly handles the case of a single candidate task"""
        single_task_output = TaskSchedulerOutput(decision='forward', task_name='Task2', reason='Only one candidate task is available')
        mock_task_scheduler_execute.return_value = single_task_output
        self.workflow.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        task = await self.workflow_manager.schedule_next_task(graph=self.workflow, env=self.env)
        self.assertEqual('Task2', task.name)
        mock_task_scheduler_execute.assert_called_once()
        self.assertEqual(1, len(self.env.trajectory))
        message = self.env.trajectory[0].message
        self.assertIsInstance(message.content, TaskSchedulerOutput)
        self.assertEqual('Task2', message.content.task_name)
        self.assertEqual(MessageType.COMMAND, message.msg_type)

    @pytest.mark.asyncio
    @patch('evoagentx.workflow.workflow_manager.ActionScheduler.async_execute')
    async def test_action_scheduling(self, mock_action_scheduler_execute):
        """Test scheduling the next action for a task"""
        mock_action_scheduler_execute.return_value = (self.action_output, 'mock prompt')
        task = self.workflow.get_node('Task1')
        mock_agent_manager = Mock()
        action = await self.workflow_manager.schedule_next_action(goal='Test Goal', task=task, agent_manager=mock_agent_manager, env=self.env)
        self.assertEqual(self.action_output, action)
        mock_action_scheduler_execute.assert_called_once()
        self.assertEqual(1, len(self.env.trajectory))
        message = self.env.trajectory[0].message
        self.assertIsInstance(message.content, NextAction)
        self.assertEqual('TestAgent', message.content.agent)
        self.assertEqual('TestAction', message.content.action)
        self.assertEqual(MessageType.COMMAND, message.msg_type)

    @pytest.mark.asyncio
    async def test_async_task_scheduling(self):
        """Test async task scheduling with multiple candidate tasks"""
        self.mock_llm.async_generate.return_value = self.task_output
        task = await self.workflow_manager.schedule_next_task(graph=self.workflow, env=self.env)
        self.assertIsNotNone(task)
        self.assertEqual('Task2', task.name)
        self.assertEqual(1, len(self.env.trajectory))
        message = self.env.trajectory[0].message
        self.assertEqual(self.task_output, message.content)
        self.assertEqual(TrajectoryState.COMPLETED, self.env.trajectory[0].status)

    @pytest.mark.asyncio
    async def test_async_action_scheduling(self):
        """Test async action scheduling"""
        self.mock_llm.async_generate.return_value = self.action_output
        task = self.workflow.get_node('Task1')
        mock_agent_manager = Mock()
        action = await self.workflow_manager.schedule_next_action(goal='Test Goal', task=task, agent_manager=mock_agent_manager, env=self.env)
        self.assertIsNotNone(action)
        self.assertEqual('TestAgent', action.agent)
        self.assertEqual('TestAction', action.action)
        self.assertEqual(1, len(self.env.trajectory))
        message = self.env.trajectory[0].message
        self.assertEqual(self.action_output, message.content)
        self.assertEqual(TrajectoryState.COMPLETED, self.env.trajectory[0].status)

    @pytest.mark.asyncio
    async def test_output_extraction(self):
        """Test extracting the output from the workflow execution"""
        output_parser = MockLLMOutputParser()
        self.mock_llm.async_generate.return_value = output_parser
        self.workflow.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        self.workflow.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
        self.workflow.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
        for task_name in ['Task1', 'Task2', 'Task3']:
            message = Message(content='Task output', agent='TestAgent', action='TestAction', prompt='Test prompt', msg_type=MessageType.RESPONSE, wf_goal='Test Workflow', wf_task=task_name)
            self.env.update(message=message, state=TrajectoryState.COMPLETED)
        output = await self.workflow_manager.extract_output(graph=self.workflow, env=self.env)
        self.assertEqual('Test output', output)
        self.mock_llm.async_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_edge_case_handling(self):
        """Test edge case handling in workflow management"""
        self.workflow.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        self.workflow.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
        self.workflow.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
        task = await self.workflow_manager.schedule_next_task(graph=self.workflow, env=self.env)
        self.assertIsNone(task)
        self.workflow.reset_graph()
        task_no_agents = WorkFlowNode(name='TaskNoAgents', description='Task with no agents', inputs=[], outputs=[], agents=[], status=WorkFlowNodeState.PENDING)
        mock_agent_manager = Mock()
        with self.assertRaises(ValueError):
            await self.workflow_manager.schedule_next_action(goal='Test Goal', task=task_no_agents, agent_manager=mock_agent_manager, env=self.env)

def test_workflow_initialization(self):
    """Test that the workflow manager is correctly initialized"""
    self.assertIsNotNone(self.workflow_manager)
    self.assertEqual(self.mock_llm, self.workflow_manager.llm)
    self.assertIsNotNone(self.workflow_manager.task_scheduler)
    self.assertIsNotNone(self.workflow_manager.action_scheduler)

class TestWorkFlowGraph(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.task1 = WorkFlowNode(name='Task1', description='First task', inputs=[Parameter(name='input1', type='string', description='Input 1')], outputs=[Parameter(name='output1', type='string', description='Output 1')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        self.task2 = WorkFlowNode(name='Task2', description='Second task', inputs=[Parameter(name='output1', type='string', description='Output from Task1')], outputs=[Parameter(name='output2', type='string', description='Output 2')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        self.task3 = WorkFlowNode(name='Task3', description='Third task', inputs=[Parameter(name='output2', type='string', description='Output from Task2')], outputs=[Parameter(name='final_output', type='string', description='Final output')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        self.task4 = WorkFlowNode(name='Task4', description='Fourth task (join)', inputs=[Parameter(name='output2', type='string', description='Output from Task2'), Parameter(name='final_output', type='string', description='Output from Task3')], outputs=[Parameter(name='result', type='string', description='Final result')], agents=['TestAgent'], status=WorkFlowNodeState.PENDING)
        self.linear_graph = WorkFlowGraph(goal='Simple Linear Workflow', nodes=[self.task1, self.task2, self.task3], edges=[WorkFlowEdge(source='Task1', target='Task2'), WorkFlowEdge(source='Task2', target='Task3')])
        self.fork_join_graph = WorkFlowGraph(goal='Fork-Join Workflow', nodes=[self.task1, self.task2, self.task3, self.task4], edges=[WorkFlowEdge(source='Task1', target='Task2'), WorkFlowEdge(source='Task2', target='Task3'), WorkFlowEdge(source='Task2', target='Task4'), WorkFlowEdge(source='Task3', target='Task4')])
        self.cycle_graph = WorkFlowGraph(goal='Workflow with Cycle', nodes=[self.task1, self.task2, self.task3], edges=[WorkFlowEdge(source='Task1', target='Task2'), WorkFlowEdge(source='Task2', target='Task3'), WorkFlowEdge(source='Task3', target='Task2')])

    def test_graph_initialization(self):
        """Test that graph is correctly initialized with nodes and edges."""
        self.assertEqual(3, len(self.linear_graph.nodes))
        self.assertEqual(2, len(self.linear_graph.edges))
        self.assertEqual('Task1', self.linear_graph.nodes[0].name)
        self.assertEqual('Task2', self.linear_graph.nodes[1].name)
        self.assertEqual('Task3', self.linear_graph.nodes[2].name)
        edge_pairs = [(edge.source, edge.target) for edge in self.linear_graph.edges]
        self.assertIn(('Task1', 'Task2'), edge_pairs)
        self.assertIn(('Task2', 'Task3'), edge_pairs)

    def test_find_initial_nodes(self):
        """Test finding initial nodes in a workflow."""
        initial_nodes = self.linear_graph.find_initial_nodes()
        self.assertEqual(1, len(initial_nodes))
        self.assertEqual('Task1', initial_nodes[0])
        initial_nodes = self.fork_join_graph.find_initial_nodes()
        self.assertEqual(1, len(initial_nodes))
        self.assertEqual('Task1', initial_nodes[0])
        initial_nodes = self.cycle_graph.find_initial_nodes()
        self.assertEqual(1, len(initial_nodes))

    def test_find_end_nodes(self):
        """Test finding end nodes in a workflow."""
        end_nodes = self.linear_graph.find_end_nodes()
        self.assertEqual(1, len(end_nodes))
        self.assertEqual('Task3', end_nodes[0])
        end_nodes = self.fork_join_graph.find_end_nodes()
        self.assertEqual(1, len(end_nodes))
        self.assertEqual('Task4', end_nodes[0])
        end_nodes = self.cycle_graph.find_end_nodes()
        self.assertEqual(0, len(end_nodes))

    def test_next_execution(self):
        """Test the 'next' method to determine the next executable tasks."""
        next_tasks = self.linear_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task1', next_tasks[0].name)
        self.linear_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        next_tasks = self.linear_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task2', next_tasks[0].name)
        self.linear_graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
        next_tasks = self.linear_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task3', next_tasks[0].name)
        self.linear_graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
        next_tasks = self.linear_graph.next()
        self.assertEqual(0, len(next_tasks))

    def test_fork_join_execution(self):
        """Test execution in a fork-join workflow."""
        next_tasks = self.fork_join_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task1', next_tasks[0].name)
        self.fork_join_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        next_tasks = self.fork_join_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task2', next_tasks[0].name)
        self.fork_join_graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
        next_tasks = self.fork_join_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task3', next_tasks[0].name)
        self.fork_join_graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
        next_tasks = self.fork_join_graph.next()
        self.assertEqual(1, len(next_tasks))
        self.assertEqual('Task4', next_tasks[0].name)
        self.fork_join_graph.set_node_status('Task4', WorkFlowNodeState.COMPLETED)
        next_tasks = self.fork_join_graph.next()
        self.assertEqual(0, len(next_tasks))

    def test_cycle_detection(self):
        """Test cycle detection in a workflow."""
        loops = self.cycle_graph._find_all_loops()
        self.assertTrue(loops)
        self.assertTrue(self.cycle_graph.is_loop_start('Task2'))
        self.assertTrue(self.cycle_graph.is_loop_end('Task3'))

    def test_node_status_management(self):
        """Test node status management."""
        self.assertEqual(WorkFlowNodeState.PENDING, self.linear_graph.get_node_status('Task1'))
        self.linear_graph.set_node_status('Task1', WorkFlowNodeState.RUNNING)
        self.assertEqual(WorkFlowNodeState.RUNNING, self.linear_graph.get_node_status('Task1'))
        self.assertTrue(self.linear_graph.running('Task1'))
        self.linear_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        self.assertEqual(WorkFlowNodeState.COMPLETED, self.linear_graph.get_node_status('Task1'))
        self.assertTrue(self.linear_graph.completed('Task1'))
        self.linear_graph.set_node_status('Task1', WorkFlowNodeState.FAILED)
        self.assertEqual(WorkFlowNodeState.FAILED, self.linear_graph.get_node_status('Task1'))
        self.assertTrue(self.linear_graph.failed('Task1'))

    def test_graph_reset(self):
        """Test resetting the graph to initial state."""
        for node in self.linear_graph.nodes:
            self.linear_graph.set_node_status(node.name, WorkFlowNodeState.COMPLETED)
        for node in self.linear_graph.nodes:
            self.assertEqual(WorkFlowNodeState.COMPLETED, node.status)
        self.linear_graph.reset_graph()
        for node in self.linear_graph.nodes:
            self.assertEqual(WorkFlowNodeState.PENDING, node.status)

    def test_graph_dependency_checking(self):
        """Test checking dependencies between nodes."""
        self.assertFalse(self.linear_graph.are_dependencies_complete('Task2'))
        self.linear_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        self.assertTrue(self.linear_graph.are_dependencies_complete('Task2'))
        self.assertFalse(self.fork_join_graph.are_dependencies_complete('Task4'))
        self.fork_join_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
        self.fork_join_graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
        self.assertFalse(self.fork_join_graph.are_dependencies_complete('Task4'))
        self.fork_join_graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
        self.assertTrue(self.fork_join_graph.are_dependencies_complete('Task4'))

def test_graph_initialization(self):
    """Test that graph is correctly initialized with nodes and edges."""
    self.assertEqual(3, len(self.linear_graph.nodes))
    self.assertEqual(2, len(self.linear_graph.edges))
    self.assertEqual('Task1', self.linear_graph.nodes[0].name)
    self.assertEqual('Task2', self.linear_graph.nodes[1].name)
    self.assertEqual('Task3', self.linear_graph.nodes[2].name)
    edge_pairs = [(edge.source, edge.target) for edge in self.linear_graph.edges]
    self.assertIn(('Task1', 'Task2'), edge_pairs)
    self.assertIn(('Task2', 'Task3'), edge_pairs)

def test_find_end_nodes(self):
    """Test finding end nodes in a workflow."""
    end_nodes = self.linear_graph.find_end_nodes()
    self.assertEqual(1, len(end_nodes))
    self.assertEqual('Task3', end_nodes[0])
    end_nodes = self.fork_join_graph.find_end_nodes()
    self.assertEqual(1, len(end_nodes))
    self.assertEqual('Task4', end_nodes[0])
    end_nodes = self.cycle_graph.find_end_nodes()
    self.assertEqual(0, len(end_nodes))

def test_next_execution(self):
    """Test the 'next' method to determine the next executable tasks."""
    next_tasks = self.linear_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task1', next_tasks[0].name)
    self.linear_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
    next_tasks = self.linear_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task2', next_tasks[0].name)
    self.linear_graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
    next_tasks = self.linear_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task3', next_tasks[0].name)
    self.linear_graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
    next_tasks = self.linear_graph.next()
    self.assertEqual(0, len(next_tasks))

def test_fork_join_execution(self):
    """Test execution in a fork-join workflow."""
    next_tasks = self.fork_join_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task1', next_tasks[0].name)
    self.fork_join_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
    next_tasks = self.fork_join_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task2', next_tasks[0].name)
    self.fork_join_graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
    next_tasks = self.fork_join_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task3', next_tasks[0].name)
    self.fork_join_graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
    next_tasks = self.fork_join_graph.next()
    self.assertEqual(1, len(next_tasks))
    self.assertEqual('Task4', next_tasks[0].name)
    self.fork_join_graph.set_node_status('Task4', WorkFlowNodeState.COMPLETED)
    next_tasks = self.fork_join_graph.next()
    self.assertEqual(0, len(next_tasks))

def test_node_status_management(self):
    """Test node status management."""
    self.assertEqual(WorkFlowNodeState.PENDING, self.linear_graph.get_node_status('Task1'))
    self.linear_graph.set_node_status('Task1', WorkFlowNodeState.RUNNING)
    self.assertEqual(WorkFlowNodeState.RUNNING, self.linear_graph.get_node_status('Task1'))
    self.assertTrue(self.linear_graph.running('Task1'))
    self.linear_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
    self.assertEqual(WorkFlowNodeState.COMPLETED, self.linear_graph.get_node_status('Task1'))
    self.assertTrue(self.linear_graph.completed('Task1'))
    self.linear_graph.set_node_status('Task1', WorkFlowNodeState.FAILED)
    self.assertEqual(WorkFlowNodeState.FAILED, self.linear_graph.get_node_status('Task1'))
    self.assertTrue(self.linear_graph.failed('Task1'))

def test_graph_reset(self):
    """Test resetting the graph to initial state."""
    for node in self.linear_graph.nodes:
        self.linear_graph.set_node_status(node.name, WorkFlowNodeState.COMPLETED)
    for node in self.linear_graph.nodes:
        self.assertEqual(WorkFlowNodeState.COMPLETED, node.status)
    self.linear_graph.reset_graph()
    for node in self.linear_graph.nodes:
        self.assertEqual(WorkFlowNodeState.PENDING, node.status)

def test_graph_dependency_checking(self):
    """Test checking dependencies between nodes."""
    self.assertFalse(self.linear_graph.are_dependencies_complete('Task2'))
    self.linear_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
    self.assertTrue(self.linear_graph.are_dependencies_complete('Task2'))
    self.assertFalse(self.fork_join_graph.are_dependencies_complete('Task4'))
    self.fork_join_graph.set_node_status('Task1', WorkFlowNodeState.COMPLETED)
    self.fork_join_graph.set_node_status('Task2', WorkFlowNodeState.COMPLETED)
    self.assertFalse(self.fork_join_graph.are_dependencies_complete('Task4'))
    self.fork_join_graph.set_node_status('Task3', WorkFlowNodeState.COMPLETED)
    self.assertTrue(self.fork_join_graph.are_dependencies_complete('Task4'))

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

class TestMBPP(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = load_json(path='tests/data/benchmark/mbpp_samples.json', type='json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        test_file = os.path.join(self.temp_dir, 'sanitized-mbpp.json')
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        save_json(self.sample_data, test_file, type='json')

    @patch('evoagentx.benchmark.mbpp.download_raw_mbpp_data')
    def test_load_data(self, mock_download):
        self.create_test_files()
        benchmark = MBPP(path=self.temp_dir)
        self.assertEqual(len(benchmark.get_train_data()), 0)
        self.assertEqual(len(benchmark.get_dev_data()), 0)
        self.assertEqual(len(benchmark.get_test_data()), 10)
        self.assertEqual(mock_download.call_count, 0)

    def test_get_label(self):
        self.create_test_files()
        benchmark = MBPP(path=self.temp_dir, mode='test')
        example = benchmark.get_test_data()[0]
        label = benchmark.get_label(example)
        self.assertTrue(isinstance(label, dict))
        self.assertEqual(label['task_id'], self.sample_data[0]['task_id'])
        self.assertEqual(label['canonical_solution'], self.sample_data[0]['code'])
        for i, example in enumerate(benchmark.get_test_data()):
            label = benchmark.get_label(example)
            self.assertTrue(isinstance(label, dict))
            self.assertEqual(label['task_id'], self.sample_data[i]['task_id'])
            self.assertEqual(label['canonical_solution'], self.sample_data[i]['code'])
            entry_point = label['entry_point']
            test = label['test']
            self.assertTrue(all((entry_point in assert_str for assert_str in self.sample_data[i]['test_list'])))
            self.assertTrue(all((assert_str in test for assert_str in self.sample_data[i]['test_list'])))

    def test_evaluate(self):
        self.create_test_files()
        benchmark = MBPP(path=self.temp_dir, mode='test')
        test_data = benchmark.get_test_data()
        for example in test_data:
            prediction = example['canonical_solution']
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(prediction, label)
            self.assertEqual(len(metrics), 1)
            self.assertTrue('pass@1' in metrics)
            self.assertTrue(metrics['pass@1'] == 1.0)

@patch('evoagentx.benchmark.mbpp.download_raw_mbpp_data')
def test_load_data(self, mock_download):
    self.create_test_files()
    benchmark = MBPP(path=self.temp_dir)
    self.assertEqual(len(benchmark.get_train_data()), 0)
    self.assertEqual(len(benchmark.get_dev_data()), 0)
    self.assertEqual(len(benchmark.get_test_data()), 10)
    self.assertEqual(mock_download.call_count, 0)

def test_get_label(self):
    self.create_test_files()
    benchmark = MBPP(path=self.temp_dir, mode='test')
    example = benchmark.get_test_data()[0]
    label = benchmark.get_label(example)
    self.assertTrue(isinstance(label, dict))
    self.assertEqual(label['task_id'], self.sample_data[0]['task_id'])
    self.assertEqual(label['canonical_solution'], self.sample_data[0]['code'])
    for i, example in enumerate(benchmark.get_test_data()):
        label = benchmark.get_label(example)
        self.assertTrue(isinstance(label, dict))
        self.assertEqual(label['task_id'], self.sample_data[i]['task_id'])
        self.assertEqual(label['canonical_solution'], self.sample_data[i]['code'])
        entry_point = label['entry_point']
        test = label['test']
        self.assertTrue(all((entry_point in assert_str for assert_str in self.sample_data[i]['test_list'])))
        self.assertTrue(all((assert_str in test for assert_str in self.sample_data[i]['test_list'])))

def test_evaluate(self):
    self.create_test_files()
    benchmark = MBPP(path=self.temp_dir, mode='test')
    test_data = benchmark.get_test_data()
    for example in test_data:
        prediction = example['canonical_solution']
        label = benchmark.get_label(example)
        metrics = benchmark.evaluate(prediction, label)
        self.assertEqual(len(metrics), 1)
        self.assertTrue('pass@1' in metrics)
        self.assertTrue(metrics['pass@1'] == 1.0)

class TestHotPotQA(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = [{'_id': 'test_id_1', 'question': 'What is the capital of France?', 'answer': 'Paris', 'context': [['France', ['Paris is the capital of France.', 'It is a beautiful city.']]], 'supporting_facts': [['France', 0]], 'type': 'comparison', 'level': 'medium'}, {'_id': 'test_id_2', 'question': 'Who wrote Romeo and Juliet?', 'answer': 'William Shakespeare', 'context': [['Shakespeare', ['William Shakespeare wrote many plays.', 'Romeo and Juliet is one of them.']]], 'supporting_facts': [['Shakespeare', 0]], 'type': 'bridge', 'level': 'easy'}]

    def tearDown(self):
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)

    def create_test_file(self, filename, data):
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return filepath

    @patch('evoagentx.benchmark.hotpotqa.download_raw_hotpotqa_data')
    def test_load_data(self, mock_download):
        self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
        benchmark = HotPotQA(path=self.temp_dir, mode='dev')
        self.assertEqual(len(benchmark.get_dev_data()), 2)
        self.assertEqual(mock_download.call_count, 0)

    def test_get_label(self):
        self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
        benchmark = HotPotQA(path=self.temp_dir, mode='dev')
        example = self.sample_data[0]
        self.assertEqual(benchmark._get_label(example), 'Paris')

    def test_get_id(self):
        self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
        benchmark = HotPotQA(path=self.temp_dir, mode='dev')
        example = self.sample_data[0]
        self.assertEqual(benchmark._get_id(example), 'test_id_1')

    def test_evaluate(self):
        self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
        benchmark = HotPotQA(path=self.temp_dir, mode='dev')
        result = benchmark.evaluate(prediction='Paris', label='Paris')
        self.assertEqual(result['em'], 1.0)
        self.assertEqual(result['f1'], 1.0)
        self.assertEqual(result['acc'], 1.0)
        result = benchmark.evaluate(prediction='in Paris, France', label='Paris')
        self.assertEqual(result['em'], 0.0)
        self.assertTrue(abs(result['f1'] - 0.5) < 1e-05)
        self.assertEqual(result['acc'], 1.0)
        result = benchmark.evaluate(prediction='London', label='Paris')
        self.assertEqual(result['em'], 0.0)
        self.assertEqual(result['f1'], 0.0)
        self.assertEqual(result['acc'], 0.0)

    def test_data_sampling(self):
        self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
        benchmark = HotPotQA(path=self.temp_dir, mode='dev')
        sampled_data = benchmark.get_dev_data(sample_k=1)
        self.assertEqual(len(sampled_data), 1)
        specific_data = benchmark.get_dev_data(indices=[0])
        self.assertEqual(len(specific_data), 1)
        self.assertEqual(specific_data[0]['_id'], self.sample_data[0]['_id'])

@patch('evoagentx.benchmark.hotpotqa.download_raw_hotpotqa_data')
def test_load_data(self, mock_download):
    self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
    benchmark = HotPotQA(path=self.temp_dir, mode='dev')
    self.assertEqual(len(benchmark.get_dev_data()), 2)
    self.assertEqual(mock_download.call_count, 0)

def test_get_label(self):
    self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
    benchmark = HotPotQA(path=self.temp_dir, mode='dev')
    example = self.sample_data[0]
    self.assertEqual(benchmark._get_label(example), 'Paris')

def test_get_id(self):
    self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
    benchmark = HotPotQA(path=self.temp_dir, mode='dev')
    example = self.sample_data[0]
    self.assertEqual(benchmark._get_id(example), 'test_id_1')

def test_evaluate(self):
    self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
    benchmark = HotPotQA(path=self.temp_dir, mode='dev')
    result = benchmark.evaluate(prediction='Paris', label='Paris')
    self.assertEqual(result['em'], 1.0)
    self.assertEqual(result['f1'], 1.0)
    self.assertEqual(result['acc'], 1.0)
    result = benchmark.evaluate(prediction='in Paris, France', label='Paris')
    self.assertEqual(result['em'], 0.0)
    self.assertTrue(abs(result['f1'] - 0.5) < 1e-05)
    self.assertEqual(result['acc'], 1.0)
    result = benchmark.evaluate(prediction='London', label='Paris')
    self.assertEqual(result['em'], 0.0)
    self.assertEqual(result['f1'], 0.0)
    self.assertEqual(result['acc'], 0.0)

def test_data_sampling(self):
    self.create_test_file('hotpot_dev_distractor_v1.json', self.sample_data)
    benchmark = HotPotQA(path=self.temp_dir, mode='dev')
    sampled_data = benchmark.get_dev_data(sample_k=1)
    self.assertEqual(len(sampled_data), 1)
    specific_data = benchmark.get_dev_data(indices=[0])
    self.assertEqual(len(specific_data), 1)
    self.assertEqual(specific_data[0]['_id'], self.sample_data[0]['_id'])

class TestAFlowHotPotQA(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = [{'_id': 'test_id_1', 'question': 'What is the capital of France?', 'answer': 'Paris', 'context': [['France', ['Paris is the capital of France.', 'It is a beautiful city.']]], 'supporting_facts': [['France', 0]], 'type': 'comparison', 'level': 'medium'}]

    def tearDown(self):
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)

    @patch('evoagentx.benchmark.hotpotqa.download_aflow_benchmark_data')
    def test_aflow_load_data(self, mock_download):
        filepath = os.path.join(self.temp_dir, 'hotpotqa_test.jsonl')
        with open(filepath, 'w') as f:
            for item in self.sample_data:
                f.write(json.dumps(item) + '\n')
        benchmark = AFlowHotPotQA(path=self.temp_dir, mode='test')
        self.assertEqual(mock_download.call_count, 0)

@patch('evoagentx.benchmark.hotpotqa.download_aflow_benchmark_data')
def test_aflow_load_data(self, mock_download):
    filepath = os.path.join(self.temp_dir, 'hotpotqa_test.jsonl')
    with open(filepath, 'w') as f:
        for item in self.sample_data:
            f.write(json.dumps(item) + '\n')
    benchmark = AFlowHotPotQA(path=self.temp_dir, mode='test')
    self.assertEqual(mock_download.call_count, 0)

class TestNQ(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = [{'question': 'What is the capital of France?', 'answers': ['Paris']}, {'question': 'Who wrote Romeo and Juliet?', 'answers': ['William Shakespeare']}]

    def tearDown(self):
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)

    def create_test_file(self, filename, data):
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', newline='') as f:
            for example in data:
                f.write('{}\t{}\n'.format(example['question'], example['answers']))
        return filepath

    @patch('evoagentx.benchmark.nq.download_raw_nq_data')
    def test_load_data(self, mock_download):
        self.create_test_file('nq-train.qa.csv', self.sample_data)
        self.create_test_file('nq-dev.qa.csv', self.sample_data)
        self.create_test_file('nq-test.qa.csv', self.sample_data)
        benchmark = NQ(path=self.temp_dir)
        self.assertEqual(len(benchmark.get_train_data()), 2)
        self.assertEqual(len(benchmark.get_dev_data()), 2)
        self.assertEqual(len(benchmark.get_test_data()), 2)
        self.assertEqual(mock_download.call_count, 0)

    def test_get_label(self):
        self.create_test_file('nq-train.qa.csv', self.sample_data)
        benchmark = NQ(path=self.temp_dir, mode='train')
        example = benchmark.get_train_data()[0]
        self.assertEqual(benchmark.get_label(example), ['Paris'])
        self.assertEqual(benchmark.get_id(example), 'train-1')

    def test_evaluate(self):
        self.create_test_file('nq-train.qa.csv', self.sample_data)
        benchmark = NQ(path=self.temp_dir, mode='train')
        result = benchmark.evaluate(prediction='Paris', label=['Paris'])
        self.assertEqual(result['em'], 1.0)
        self.assertEqual(result['f1'], 1.0)
        self.assertEqual(result['acc'], 1.0)
        result = benchmark.evaluate(prediction='in Paris, France', label=['Paris'])
        self.assertEqual(result['em'], 0.0)
        self.assertTrue(abs(result['f1'] - 0.5) < 1e-05)
        self.assertEqual(result['acc'], 1.0)
        result = benchmark.evaluate(prediction='London', label=['Paris'])
        self.assertEqual(result['em'], 0.0)
        self.assertEqual(result['f1'], 0.0)
        self.assertEqual(result['acc'], 0.0)

@patch('evoagentx.benchmark.nq.download_raw_nq_data')
def test_load_data(self, mock_download):
    self.create_test_file('nq-train.qa.csv', self.sample_data)
    self.create_test_file('nq-dev.qa.csv', self.sample_data)
    self.create_test_file('nq-test.qa.csv', self.sample_data)
    benchmark = NQ(path=self.temp_dir)
    self.assertEqual(len(benchmark.get_train_data()), 2)
    self.assertEqual(len(benchmark.get_dev_data()), 2)
    self.assertEqual(len(benchmark.get_test_data()), 2)
    self.assertEqual(mock_download.call_count, 0)

def test_get_label(self):
    self.create_test_file('nq-train.qa.csv', self.sample_data)
    benchmark = NQ(path=self.temp_dir, mode='train')
    example = benchmark.get_train_data()[0]
    self.assertEqual(benchmark.get_label(example), ['Paris'])
    self.assertEqual(benchmark.get_id(example), 'train-1')

def test_evaluate(self):
    self.create_test_file('nq-train.qa.csv', self.sample_data)
    benchmark = NQ(path=self.temp_dir, mode='train')
    result = benchmark.evaluate(prediction='Paris', label=['Paris'])
    self.assertEqual(result['em'], 1.0)
    self.assertEqual(result['f1'], 1.0)
    self.assertEqual(result['acc'], 1.0)
    result = benchmark.evaluate(prediction='in Paris, France', label=['Paris'])
    self.assertEqual(result['em'], 0.0)
    self.assertTrue(abs(result['f1'] - 0.5) < 1e-05)
    self.assertEqual(result['acc'], 1.0)
    result = benchmark.evaluate(prediction='London', label=['Paris'])
    self.assertEqual(result['em'], 0.0)
    self.assertEqual(result['f1'], 0.0)
    self.assertEqual(result['acc'], 0.0)

class TestHumanEval(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = load_json(path='tests/data/benchmark/humaneval_samples.jsonl', type='jsonl')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        test_file = os.path.join(self.temp_dir, 'HumanEval.jsonl')
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        save_json(self.sample_data, test_file, type='jsonl')

    @patch('evoagentx.benchmark.humaneval.download_raw_humaneval_data')
    def test_load_data(self, mock_download):
        self.create_test_files()
        benchmark = HumanEval(path=self.temp_dir)
        self.assertEqual(len(benchmark.get_train_data()), 0)
        self.assertEqual(len(benchmark.get_dev_data()), 0)
        self.assertEqual(len(benchmark.get_test_data()), 10)
        self.assertEqual(mock_download.call_count, 0)

    def test_get_label(self):
        self.create_test_files()
        benchmark = HumanEval(path=self.temp_dir, mode='test')
        example = benchmark.get_test_data()[0]
        label = benchmark.get_label(example)
        self.assertTrue(isinstance(label, dict))
        self.assertEqual(label['task_id'], self.sample_data[0]['task_id'])
        self.assertEqual(label['canonical_solution'], self.sample_data[0]['canonical_solution'])
        self.assertEqual(label['test'], self.sample_data[0]['test'])
        self.assertEqual(label['entry_point'], self.sample_data[0]['entry_point'])

    def test_evaluate(self):
        self.create_test_files()
        benchmark = HumanEval(path=self.temp_dir, mode='test')
        test_data = benchmark.get_test_data()
        for example in test_data:
            prediction = example['prompt'] + example['canonical_solution']
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(prediction, label)
            self.assertEqual(len(metrics), 1)
            self.assertTrue('pass@1' in metrics)
            self.assertEqual(metrics['pass@1'], 1.0)

@patch('evoagentx.benchmark.humaneval.download_raw_humaneval_data')
def test_load_data(self, mock_download):
    self.create_test_files()
    benchmark = HumanEval(path=self.temp_dir)
    self.assertEqual(len(benchmark.get_train_data()), 0)
    self.assertEqual(len(benchmark.get_dev_data()), 0)
    self.assertEqual(len(benchmark.get_test_data()), 10)
    self.assertEqual(mock_download.call_count, 0)

def test_get_label(self):
    self.create_test_files()
    benchmark = HumanEval(path=self.temp_dir, mode='test')
    example = benchmark.get_test_data()[0]
    label = benchmark.get_label(example)
    self.assertTrue(isinstance(label, dict))
    self.assertEqual(label['task_id'], self.sample_data[0]['task_id'])
    self.assertEqual(label['canonical_solution'], self.sample_data[0]['canonical_solution'])
    self.assertEqual(label['test'], self.sample_data[0]['test'])
    self.assertEqual(label['entry_point'], self.sample_data[0]['entry_point'])

def test_evaluate(self):
    self.create_test_files()
    benchmark = HumanEval(path=self.temp_dir, mode='test')
    test_data = benchmark.get_test_data()
    for example in test_data:
        prediction = example['prompt'] + example['canonical_solution']
        label = benchmark.get_label(example)
        metrics = benchmark.evaluate(prediction, label)
        self.assertEqual(len(metrics), 1)
        self.assertTrue('pass@1' in metrics)
        self.assertEqual(metrics['pass@1'], 1.0)

class TestMath(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data1 = {'problem': 'We roll a fair 6-sided die 5 times.  What is the probability that we get a 6 in at most 2 of the rolls?', 'level': 'Level 5', 'type': 'Counting & Probability', 'solution': "The number of ways to roll exactly 2 6's is $\\binom{5}{2}5^3$, since there are $\\binom{5}{2}$ choices for which of the two dice are 6, and there are 5 choices for each of the other 3 dice. Similarly, the number of ways to roll exactly 1 6 is $\\binom{5}{1}5^4$, and the number of ways to roll no 6's is $\\binom{5}{0}5^5$. So the probability is \\[\\frac{\\binom{5}{2}5^3+\\binom{5}{1}5^4+\\binom{5}{0}5^5}{6^5}=\\boxed{\\frac{625}{648}}.\\]"}
        self.sample_data2 = {'problem': 'When counting from $3$ to $201$, $53$ is the $51^\\mathrm{st}$ number counted. When counting backwards from $201$ to $3$, $53$ is the $n^\\mathrm{th}$ number counted. What is $n$?', 'level': 'Level 2', 'type': 'Counting & Probability', 'solution': 'Note that $n$ is equal to the number of integers between $53$ and $201$, inclusive. Thus, $n=201-53+1=\\boxed{149}$.'}

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        train_file = os.path.join(self.temp_dir, 'MATH', 'train', 'Counting & Probability', 'sample1.json')
        os.makedirs(os.path.dirname(train_file), exist_ok=True)
        save_json(self.sample_data1, train_file, type='json')
        test_file = os.path.join(self.temp_dir, 'MATH', 'test', 'Counting & Probability', 'sample1.json')
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        save_json(self.sample_data2, test_file, type='json')

    @patch('evoagentx.benchmark.math_benchmark.download_raw_math_data')
    def test_load_data(self, mock_download):
        self.create_test_files()
        benchmark = MATH(path=self.temp_dir)
        self.assertEqual(len(benchmark.get_train_data()), 1)
        self.assertEqual(len(benchmark.get_dev_data()), 0)
        self.assertEqual(len(benchmark.get_test_data()), 1)
        self.assertEqual(mock_download.call_count, 0)

    def test_get_label(self):
        self.create_test_files()
        benchmark = MATH(path=self.temp_dir, mode='train')
        example = benchmark.get_train_data()[0]
        self.assertEqual(benchmark.get_label(example), self.sample_data1['solution'])
        self.assertEqual(benchmark.get_id(example), 'train-1')

    def test_extract_answer(self):
        self.create_test_files()
        benchmark = MATH(path=self.temp_dir, mode='train')
        example = benchmark.get_train_data()[0]
        self.assertEqual(benchmark.extract_answer(example['solution']), '\\frac{625}{648}')

    def test_evaluate(self):
        self.create_test_files()
        benchmark = MATH(path=self.temp_dir, mode='train')
        example = benchmark.get_train_data()[0]
        prediction = benchmark.extract_answer(example['solution'])
        self.assertEqual(str(prediction), str('\\frac{625}{648}'))
        self.assertTrue(benchmark.math_equal(prediction, '\\frac{625}{648}'))
        self.assertFalse(benchmark.math_equal(prediction, '\\frac{625}{649}'))
        self.assertFalse(benchmark.is_digit(prediction))
        self.assertFalse(benchmark.is_digit('\\frac{625}{648}'))
        self.assertTrue(benchmark.symbolic_equal(prediction, '\\frac{625}{648}'))
        self.assertFalse(benchmark.symbolic_equal(prediction, '\\frac{625}{649}'))
        self.assertEqual(benchmark.evaluate(example['solution'], '\\frac{625}{648}'), {'solve_rate': 1.0})
        self.assertEqual(benchmark.evaluate(example['solution'], '\\frac{625}{649}'), {'solve_rate': 0.0})

@patch('evoagentx.benchmark.math_benchmark.download_raw_math_data')
def test_load_data(self, mock_download):
    self.create_test_files()
    benchmark = MATH(path=self.temp_dir)
    self.assertEqual(len(benchmark.get_train_data()), 1)
    self.assertEqual(len(benchmark.get_dev_data()), 0)
    self.assertEqual(len(benchmark.get_test_data()), 1)
    self.assertEqual(mock_download.call_count, 0)

def test_get_label(self):
    self.create_test_files()
    benchmark = MATH(path=self.temp_dir, mode='train')
    example = benchmark.get_train_data()[0]
    self.assertEqual(benchmark.get_label(example), self.sample_data1['solution'])
    self.assertEqual(benchmark.get_id(example), 'train-1')

def test_extract_answer(self):
    self.create_test_files()
    benchmark = MATH(path=self.temp_dir, mode='train')
    example = benchmark.get_train_data()[0]
    self.assertEqual(benchmark.extract_answer(example['solution']), '\\frac{625}{648}')

def test_evaluate(self):
    self.create_test_files()
    benchmark = MATH(path=self.temp_dir, mode='train')
    example = benchmark.get_train_data()[0]
    prediction = benchmark.extract_answer(example['solution'])
    self.assertEqual(str(prediction), str('\\frac{625}{648}'))
    self.assertTrue(benchmark.math_equal(prediction, '\\frac{625}{648}'))
    self.assertFalse(benchmark.math_equal(prediction, '\\frac{625}{649}'))
    self.assertFalse(benchmark.is_digit(prediction))
    self.assertFalse(benchmark.is_digit('\\frac{625}{648}'))
    self.assertTrue(benchmark.symbolic_equal(prediction, '\\frac{625}{648}'))
    self.assertFalse(benchmark.symbolic_equal(prediction, '\\frac{625}{649}'))
    self.assertEqual(benchmark.evaluate(example['solution'], '\\frac{625}{648}'), {'solve_rate': 1.0})
    self.assertEqual(benchmark.evaluate(example['solution'], '\\frac{625}{649}'), {'solve_rate': 0.0})

class TestGSM8K(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = [{'question': "Janet’s ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?", 'answer': 'Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs a day.\nShe makes 9 * 2 = $<<9*2=18>>18 every day at the farmer’s market.\n#### 18'}, {'question': 'A robe takes 2 bolts of blue fiber and half that much white fiber.  How many bolts in total does it take?', 'answer': 'It takes 2/2=<<2/2=1>>1 bolt of white fiber\nSo the total amount of fabric is 2+1=<<2+1=3>>3 bolts of fabric\n#### 3'}]

    def tearDown(self):
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)

    def create_test_file(self, filename, data):
        filepath = os.path.join(self.temp_dir, filename)
        save_json(data=data, path=filepath, type='jsonl')
        return filepath

    @patch('evoagentx.benchmark.gsm8k.download_raw_gsm8k_data')
    def test_load_data(self, mock_download):
        self.create_test_file('train.jsonl', self.sample_data)
        self.create_test_file('test.jsonl', self.sample_data)
        benchmark = GSM8K(path=self.temp_dir)
        self.assertEqual(len(benchmark.get_train_data()), 2)
        self.assertEqual(len(benchmark.get_dev_data()), 0)
        self.assertEqual(len(benchmark.get_test_data()), 2)
        self.assertEqual(mock_download.call_count, 0)

    def test_get_label(self):
        self.create_test_file('train.jsonl', self.sample_data)
        benchmark = GSM8K(path=self.temp_dir, mode='train')
        example = benchmark.get_train_data()[0]
        self.assertEqual(benchmark.get_label(example), self.sample_data[0]['answer'])
        self.assertEqual(benchmark.get_id(example), 'train-1')

    def test_extract_last_number(self):
        self.create_test_file('train.jsonl', self.sample_data)
        benchmark = GSM8K(path=self.temp_dir)
        self.assertEqual(benchmark.extract_last_number(benchmark.get_train_data()[0]['answer']), 18)
        self.assertEqual(benchmark.extract_last_number(benchmark.get_train_data()[1]['answer']), 3)
        self.assertEqual(benchmark.extract_last_number('The answer is123.45'), 123.45)
        self.assertEqual(benchmark.extract_last_number('The answer is: xxx123.45'), 123.45)
        self.assertEqual(benchmark.extract_last_number('The answer is:\n123.45'), 123.45)
        self.assertEqual(benchmark.extract_last_number('The answer is:\n #### 123.45'), 123.45)

    def test_evaluate(self):
        self.create_test_file('train.jsonl', self.sample_data)
        benchmark = GSM8K(path=self.temp_dir, mode='train')
        result = benchmark.evaluate(prediction='18', label=self.sample_data[0]['answer'])
        self.assertEqual(result['solve_rate'], 1.0)
        result = benchmark.evaluate(prediction='reasoning process, ####18', label=self.sample_data[0]['answer'])
        self.assertEqual(result['solve_rate'], 1.0)
        result = benchmark.evaluate(prediction='wrong answer 111', label=self.sample_data[0]['answer'])
        self.assertEqual(result['solve_rate'], 0.0)

@patch('evoagentx.benchmark.gsm8k.download_raw_gsm8k_data')
def test_load_data(self, mock_download):
    self.create_test_file('train.jsonl', self.sample_data)
    self.create_test_file('test.jsonl', self.sample_data)
    benchmark = GSM8K(path=self.temp_dir)
    self.assertEqual(len(benchmark.get_train_data()), 2)
    self.assertEqual(len(benchmark.get_dev_data()), 0)
    self.assertEqual(len(benchmark.get_test_data()), 2)
    self.assertEqual(mock_download.call_count, 0)

def test_get_label(self):
    self.create_test_file('train.jsonl', self.sample_data)
    benchmark = GSM8K(path=self.temp_dir, mode='train')
    example = benchmark.get_train_data()[0]
    self.assertEqual(benchmark.get_label(example), self.sample_data[0]['answer'])
    self.assertEqual(benchmark.get_id(example), 'train-1')

def test_extract_last_number(self):
    self.create_test_file('train.jsonl', self.sample_data)
    benchmark = GSM8K(path=self.temp_dir)
    self.assertEqual(benchmark.extract_last_number(benchmark.get_train_data()[0]['answer']), 18)
    self.assertEqual(benchmark.extract_last_number(benchmark.get_train_data()[1]['answer']), 3)
    self.assertEqual(benchmark.extract_last_number('The answer is123.45'), 123.45)
    self.assertEqual(benchmark.extract_last_number('The answer is: xxx123.45'), 123.45)
    self.assertEqual(benchmark.extract_last_number('The answer is:\n123.45'), 123.45)
    self.assertEqual(benchmark.extract_last_number('The answer is:\n #### 123.45'), 123.45)

def test_evaluate(self):
    self.create_test_file('train.jsonl', self.sample_data)
    benchmark = GSM8K(path=self.temp_dir, mode='train')
    result = benchmark.evaluate(prediction='18', label=self.sample_data[0]['answer'])
    self.assertEqual(result['solve_rate'], 1.0)
    result = benchmark.evaluate(prediction='reasoning process, ####18', label=self.sample_data[0]['answer'])
    self.assertEqual(result['solve_rate'], 1.0)
    result = benchmark.evaluate(prediction='wrong answer 111', label=self.sample_data[0]['answer'])
    self.assertEqual(result['solve_rate'], 0.0)

class TestLiveCodeBench(unittest.TestCase):

    def setUp(self):
        self.codegen_samples = load_from_disk('tests/data/benchmark/lcb_codegen_samples')
        self.codegen_solutions = [codegen_solution, codegen_solution2, codegen_solution3]
        self.test_output_prediction_samples = load_from_disk('tests/data/benchmark/lcb_outputprediction_samples')
        self.test_output_prediction_solutions = [test_output_prediction_solution1, test_output_prediction_solution2, test_output_prediction_solution3]
        self.code_execution_samples = load_from_disk('tests/data/benchmark/lcb_codeexecution_samples')
        self.code_execution_solutions = [code_execution_solution1, code_execution_solution2, code_execution_solution3]

    @patch('evoagentx.benchmark.livecodebench.load_code_generation_dataset')
    def test_code_generation(self, mock_load_dataset):
        mock_load_dataset.return_value = [CodeGenerationProblem(**p) for p in self.codegen_samples]
        benchmark = LiveCodeBench(scenario='code_generation', version='release_v1')
        test_data = benchmark.get_test_data()
        self.assertEqual(len(test_data), len(self.codegen_samples))
        self.assertEqual(mock_load_dataset.call_count, 1)
        for example, solution in zip(test_data, self.codegen_solutions):
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(solution, label)
            self.assertEqual(metrics, {'pass@1': 1.0})

    @patch('evoagentx.benchmark.livecodebench.load_test_prediction_dataset')
    def test_test_output_prediction(self, mock_load_dataset):
        mock_load_dataset.return_value = [TestOutputPredictionProblem(**p) for p in self.test_output_prediction_samples]
        benchmark = LiveCodeBench(scenario='test_output_prediction')
        test_data = benchmark.get_test_data()
        self.assertEqual(len(test_data), len(self.test_output_prediction_samples))
        self.assertEqual(mock_load_dataset.call_count, 1)
        for example, solution in zip(test_data, self.test_output_prediction_solutions):
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(solution, label)
            self.assertEqual(metrics, {'pass@1': 1.0})

    @patch('evoagentx.benchmark.livecodebench.load_code_execution_dataset')
    def test_code_execution(self, mock_load_dataset):
        mock_load_dataset.return_value = [CodeExecutionProblem(**p) for p in self.code_execution_samples]
        benchmark = LiveCodeBench(scenario='code_execution')
        test_data = benchmark.get_test_data()
        self.assertEqual(len(test_data), len(self.code_execution_samples))
        self.assertEqual(mock_load_dataset.call_count, 1)
        for example, solution in zip(test_data, self.code_execution_solutions):
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(solution, label)
            self.assertEqual(metrics, {'pass@1': 1.0})

@patch('evoagentx.benchmark.livecodebench.load_code_generation_dataset')
def test_code_generation(self, mock_load_dataset):
    mock_load_dataset.return_value = [CodeGenerationProblem(**p) for p in self.codegen_samples]
    benchmark = LiveCodeBench(scenario='code_generation', version='release_v1')
    test_data = benchmark.get_test_data()
    self.assertEqual(len(test_data), len(self.codegen_samples))
    self.assertEqual(mock_load_dataset.call_count, 1)
    for example, solution in zip(test_data, self.codegen_solutions):
        label = benchmark.get_label(example)
        metrics = benchmark.evaluate(solution, label)
        self.assertEqual(metrics, {'pass@1': 1.0})

@patch('evoagentx.benchmark.livecodebench.load_test_prediction_dataset')
def test_test_output_prediction(self, mock_load_dataset):
    mock_load_dataset.return_value = [TestOutputPredictionProblem(**p) for p in self.test_output_prediction_samples]
    benchmark = LiveCodeBench(scenario='test_output_prediction')
    test_data = benchmark.get_test_data()
    self.assertEqual(len(test_data), len(self.test_output_prediction_samples))
    self.assertEqual(mock_load_dataset.call_count, 1)
    for example, solution in zip(test_data, self.test_output_prediction_solutions):
        label = benchmark.get_label(example)
        metrics = benchmark.evaluate(solution, label)
        self.assertEqual(metrics, {'pass@1': 1.0})

@patch('evoagentx.benchmark.livecodebench.load_code_execution_dataset')
def test_code_execution(self, mock_load_dataset):
    mock_load_dataset.return_value = [CodeExecutionProblem(**p) for p in self.code_execution_samples]
    benchmark = LiveCodeBench(scenario='code_execution')
    test_data = benchmark.get_test_data()
    self.assertEqual(len(test_data), len(self.code_execution_samples))
    self.assertEqual(mock_load_dataset.call_count, 1)
    for example, solution in zip(test_data, self.code_execution_solutions):
        label = benchmark.get_label(example)
        metrics = benchmark.evaluate(solution, label)
        self.assertEqual(metrics, {'pass@1': 1.0})

class TestModule(unittest.TestCase):

    def setUp(self):
        self.save_file = 'tests/core/saved_module.json'

    def test_initialization(self):
        module1 = ToyModule(k1=100)
        self.assertEqual(module1.k1, 100)
        self.assertEqual(module1.k3, [1, 2])
        module12 = ToyModule(k1=100, k3=[200, 300])
        self.assertEqual(module12.k3, [200, 300])
        module2 = ToyModule2(k4='k4_value_valid', k5='k5_value')
        self.assertEqual(module2.k4, 'k4_value_valid')
        self.assertEqual(module2.k5, 'k5_value')
        self.assertEqual(module2.k6.name, 'k4_value_valid')
        self.assertEqual(module2.k6.key, 'k5_value')
        module3 = ToyModule3(k7=module1, k8=10, k9=module2)
        self.assertEqual(module3.k7, module1)
        self.assertEqual(module3.k9, module2)

    def test_from_dict(self):
        module = ToyModule3.from_dict({'k7': {'k1': 'k1_value', 'k3': [100, 200]}, 'k8': 10, 'k9': ToyModule2(k4='k4_value_valid', k5='k5_value')})
        self.assertEqual(module.k7.k1, 'k1_value')
        self.assertEqual(module.k7.k3, [100, 200])
        self.assertEqual(module.k8, 10)
        self.assertEqual(module.k9.k6.name, 'k4_value_valid')
        self.assertEqual(module.k9.k6.key, 'k5_value')

    def test_from_json(self):
        json_data = '\n        {\n            "k7": {\n                "k1": "k1_value", \n                "k3": [100, 200], \n            },\n            "k8": 10, \n            "k9": {\n                "k4": "k4_value_valid", \n                "k5": "k5_value", \n            }\n        }\n        '
        module = ToyModule3.from_json(json_data)
        self.assertEqual(module.k7.k1, 'k1_value')
        self.assertEqual(module.k7.k3, [100, 200])
        self.assertEqual(module.k8, 10)
        self.assertEqual(module.k9.k6.name, 'k4_value_valid')
        self.assertEqual(module.k9.k6.key, 'k5_value')

    def test_from_str(self):
        str_data = '\n        there might be some text before the json data. \n\n        an irrelevant json data:\n        {\n            "k1": "k1",\n            "k3": 11, \n        }\n\n        true json data: \n        {\n            "k7": {\n                "k1": "k1_value", \n                "k3": [100, 200], \n            },\n            "k8": 10, \n            "k9": {\n                "k4": "k4_value_valid", \n                "k5": "k5_value", \n            }\n        }\n        \n        some text after the json data. \n        '
        module = ToyModule3.from_str(str_data)
        self.assertEqual(module.k7.k1, 'k1_value')
        self.assertEqual(module.k7.k3, [100, 200])
        self.assertEqual(module.k8, 10)
        self.assertEqual(module.k9.k6.name, 'k4_value_valid')
        self.assertEqual(module.k9.k6.key, 'k5_value')

    def test_save_module(self):
        module1 = ToyModule(k1='k1_value', k3=[100, 200])
        module2 = ToyModule2(k4='k4_value_valid', k5='k5_value')
        module3 = ToyModule3(k7=module1, k8=10, k9=module2)
        module3.save_module(self.save_file, use_indent=True)
        self.assertTrue(os.path.exists(self.save_file))
        module = ToyModule3.from_file(self.save_file)
        self.assertEqual(module.k7.k1, 'k1_value')
        self.assertEqual(module.k7.k3, [100, 200])
        self.assertEqual(module.k8, 10)
        self.assertEqual(module.k9.k6.name, 'k4_value_valid')
        self.assertEqual(module.k9.k6.key, 'k5_value')

    def test_subclass(self):
        d1 = {'k10': [{'k1': 'k1_value'}], 'k11': [{'k4': 'k4_valid_value1', 'k5': 'k5_value1'}, {'k4': 'k4_valid_value2', 'k5': 'k5_value2'}], 'k12': {'key': {'k7': {'k1': 'k1_value2'}, 'k8': 11, 'k9': {'k4': 'k4_valid_value3', 'k5': 'k5_value3'}}}}
        module = ToyModule4.from_dict(d1)
        self.assertTrue(isinstance(module.k10[0], ToyModule) and module.k10[0].class_name == 'ToyModule')
        self.assertTrue(isinstance(module.k11[0], ToyModule2) and isinstance(module.k11[1], ToyModule2) and (module.k11[0].class_name == 'ToyModule2') and (module.k11[1].class_name == 'ToyModule2'))
        self.assertTrue(isinstance(module.k12['key'], ToyModule3) and module.k12['key'].class_name == 'ToyModule3')
        self.assertTrue(isinstance(module.k12['key'].k7, ToyModule) and module.k12['key'].k7.class_name == 'ToyModule')
        self.assertTrue(isinstance(module.k12['key'].k9, ToyModule2) and module.k12['key'].k9.class_name == 'ToyModule2')
        d2 = {'k10': [{'k1': 'k1_value'}], 'k11': [{'class_name': 'ToyModule2SubClass', 'k4': 'k4_valid_value1', 'k5': 'k5_value1'}, {'k4': 'k4_valid_value2', 'k5': 'k5_value2'}], 'k12': {'key': {'k7': {'class_name': 'ToyModuleSubClass', 'k1': 'k1_value2'}, 'k8': 11, 'k9': {'k4': 'k4_valid_value3', 'k5': 'k5_value3'}}}, 'k13': {'key2': 0}}
        module = ToyModule4.from_dict(d2)
        self.assertTrue(isinstance(module.k10[0], ToyModule) and module.k10[0].class_name == 'ToyModule')
        self.assertTrue(isinstance(module.k11[0], ToyModule2SubClass) and isinstance(module.k11[1], ToyModule2) and (module.k11[0].class_name == 'ToyModule2SubClass') and (module.k11[1].class_name == 'ToyModule2'))
        self.assertEqual(module.k11[0].test2_subclass_variable, 0)
        self.assertTrue(isinstance(module.k12['key'], ToyModule3) and module.k12['key'].class_name == 'ToyModule3')
        self.assertTrue(isinstance(module.k12['key'].k7, ToyModuleSubClass) and module.k12['key'].k7.class_name == 'ToyModuleSubClass')
        self.assertTrue(isinstance(module.k12['key'].k9, ToyModule2) and module.k12['key'].k9.class_name == 'ToyModule2')
        self.assertTrue(isinstance(module.k13, dict))

    def test_subclass_from_init(self):
        test2_instance = ToyModule2(k4='k4_valid_value1', k5='k5_value1')
        test4_instance = ToyModule4(k10=[{'k1': 'k1_value'}], k11=[test2_instance, {'k4': 'k4_valid_value2', 'k5': 'k5_valid_value2'}, {'class_name': 'ToyModule2SubClass', 'k4': 'k4_valid_value3', 'k5': 'k5_value3', 'test2_subclass_variable': 888}], k12={'key': {'class_name': 'ToyModule3SubClass', 'k7': {'class_name': 'ToyModuleSubClass', 'k1': 'k1_value2'}, 'k8': 11, 'k9': {'k4': 'k4_valid_value4', 'k5': 'k5_value4'}}}, k13={'key2': 999})
        self.assertEqual(test4_instance.k10[0].k1, 'k1_value')
        self.assertTrue(isinstance(test4_instance.k11[0], ToyModule2))
        self.assertTrue(isinstance(test4_instance.k11[2], ToyModule2SubClass))
        self.assertEqual(test4_instance.k11[2].test2_subclass_variable, 888)
        self.assertTrue(isinstance(test4_instance.k12['key'], ToyModule3SubClass))
        self.assertTrue(isinstance(test4_instance.k12['key'].k7, ToyModuleSubClass))

    def tearDown(self):
        if os.path.exists(self.save_file):
            os.remove(self.save_file)

def test_initialization(self):
    module1 = ToyModule(k1=100)
    self.assertEqual(module1.k1, 100)
    self.assertEqual(module1.k3, [1, 2])
    module12 = ToyModule(k1=100, k3=[200, 300])
    self.assertEqual(module12.k3, [200, 300])
    module2 = ToyModule2(k4='k4_value_valid', k5='k5_value')
    self.assertEqual(module2.k4, 'k4_value_valid')
    self.assertEqual(module2.k5, 'k5_value')
    self.assertEqual(module2.k6.name, 'k4_value_valid')
    self.assertEqual(module2.k6.key, 'k5_value')
    module3 = ToyModule3(k7=module1, k8=10, k9=module2)
    self.assertEqual(module3.k7, module1)
    self.assertEqual(module3.k9, module2)

def test_from_dict(self):
    module = ToyModule3.from_dict({'k7': {'k1': 'k1_value', 'k3': [100, 200]}, 'k8': 10, 'k9': ToyModule2(k4='k4_value_valid', k5='k5_value')})
    self.assertEqual(module.k7.k1, 'k1_value')
    self.assertEqual(module.k7.k3, [100, 200])
    self.assertEqual(module.k8, 10)
    self.assertEqual(module.k9.k6.name, 'k4_value_valid')
    self.assertEqual(module.k9.k6.key, 'k5_value')

def test_from_json(self):
    json_data = '\n        {\n            "k7": {\n                "k1": "k1_value", \n                "k3": [100, 200], \n            },\n            "k8": 10, \n            "k9": {\n                "k4": "k4_value_valid", \n                "k5": "k5_value", \n            }\n        }\n        '
    module = ToyModule3.from_json(json_data)
    self.assertEqual(module.k7.k1, 'k1_value')
    self.assertEqual(module.k7.k3, [100, 200])
    self.assertEqual(module.k8, 10)
    self.assertEqual(module.k9.k6.name, 'k4_value_valid')
    self.assertEqual(module.k9.k6.key, 'k5_value')

def test_from_str(self):
    str_data = '\n        there might be some text before the json data. \n\n        an irrelevant json data:\n        {\n            "k1": "k1",\n            "k3": 11, \n        }\n\n        true json data: \n        {\n            "k7": {\n                "k1": "k1_value", \n                "k3": [100, 200], \n            },\n            "k8": 10, \n            "k9": {\n                "k4": "k4_value_valid", \n                "k5": "k5_value", \n            }\n        }\n        \n        some text after the json data. \n        '
    module = ToyModule3.from_str(str_data)
    self.assertEqual(module.k7.k1, 'k1_value')
    self.assertEqual(module.k7.k3, [100, 200])
    self.assertEqual(module.k8, 10)
    self.assertEqual(module.k9.k6.name, 'k4_value_valid')
    self.assertEqual(module.k9.k6.key, 'k5_value')

def test_save_module(self):
    module1 = ToyModule(k1='k1_value', k3=[100, 200])
    module2 = ToyModule2(k4='k4_value_valid', k5='k5_value')
    module3 = ToyModule3(k7=module1, k8=10, k9=module2)
    module3.save_module(self.save_file, use_indent=True)
    self.assertTrue(os.path.exists(self.save_file))
    module = ToyModule3.from_file(self.save_file)
    self.assertEqual(module.k7.k1, 'k1_value')
    self.assertEqual(module.k7.k3, [100, 200])
    self.assertEqual(module.k8, 10)
    self.assertEqual(module.k9.k6.name, 'k4_value_valid')
    self.assertEqual(module.k9.k6.key, 'k5_value')

def test_subclass(self):
    d1 = {'k10': [{'k1': 'k1_value'}], 'k11': [{'k4': 'k4_valid_value1', 'k5': 'k5_value1'}, {'k4': 'k4_valid_value2', 'k5': 'k5_value2'}], 'k12': {'key': {'k7': {'k1': 'k1_value2'}, 'k8': 11, 'k9': {'k4': 'k4_valid_value3', 'k5': 'k5_value3'}}}}
    module = ToyModule4.from_dict(d1)
    self.assertTrue(isinstance(module.k10[0], ToyModule) and module.k10[0].class_name == 'ToyModule')
    self.assertTrue(isinstance(module.k11[0], ToyModule2) and isinstance(module.k11[1], ToyModule2) and (module.k11[0].class_name == 'ToyModule2') and (module.k11[1].class_name == 'ToyModule2'))
    self.assertTrue(isinstance(module.k12['key'], ToyModule3) and module.k12['key'].class_name == 'ToyModule3')
    self.assertTrue(isinstance(module.k12['key'].k7, ToyModule) and module.k12['key'].k7.class_name == 'ToyModule')
    self.assertTrue(isinstance(module.k12['key'].k9, ToyModule2) and module.k12['key'].k9.class_name == 'ToyModule2')
    d2 = {'k10': [{'k1': 'k1_value'}], 'k11': [{'class_name': 'ToyModule2SubClass', 'k4': 'k4_valid_value1', 'k5': 'k5_value1'}, {'k4': 'k4_valid_value2', 'k5': 'k5_value2'}], 'k12': {'key': {'k7': {'class_name': 'ToyModuleSubClass', 'k1': 'k1_value2'}, 'k8': 11, 'k9': {'k4': 'k4_valid_value3', 'k5': 'k5_value3'}}}, 'k13': {'key2': 0}}
    module = ToyModule4.from_dict(d2)
    self.assertTrue(isinstance(module.k10[0], ToyModule) and module.k10[0].class_name == 'ToyModule')
    self.assertTrue(isinstance(module.k11[0], ToyModule2SubClass) and isinstance(module.k11[1], ToyModule2) and (module.k11[0].class_name == 'ToyModule2SubClass') and (module.k11[1].class_name == 'ToyModule2'))
    self.assertEqual(module.k11[0].test2_subclass_variable, 0)
    self.assertTrue(isinstance(module.k12['key'], ToyModule3) and module.k12['key'].class_name == 'ToyModule3')
    self.assertTrue(isinstance(module.k12['key'].k7, ToyModuleSubClass) and module.k12['key'].k7.class_name == 'ToyModuleSubClass')
    self.assertTrue(isinstance(module.k12['key'].k9, ToyModule2) and module.k12['key'].k9.class_name == 'ToyModule2')
    self.assertTrue(isinstance(module.k13, dict))

def test_subclass_from_init(self):
    test2_instance = ToyModule2(k4='k4_valid_value1', k5='k5_value1')
    test4_instance = ToyModule4(k10=[{'k1': 'k1_value'}], k11=[test2_instance, {'k4': 'k4_valid_value2', 'k5': 'k5_valid_value2'}, {'class_name': 'ToyModule2SubClass', 'k4': 'k4_valid_value3', 'k5': 'k5_value3', 'test2_subclass_variable': 888}], k12={'key': {'class_name': 'ToyModule3SubClass', 'k7': {'class_name': 'ToyModuleSubClass', 'k1': 'k1_value2'}, 'k8': 11, 'k9': {'k4': 'k4_valid_value4', 'k5': 'k5_value4'}}}, k13={'key2': 999})
    self.assertEqual(test4_instance.k10[0].k1, 'k1_value')
    self.assertTrue(isinstance(test4_instance.k11[0], ToyModule2))
    self.assertTrue(isinstance(test4_instance.k11[2], ToyModule2SubClass))
    self.assertEqual(test4_instance.k11[2].test2_subclass_variable, 888)
    self.assertTrue(isinstance(test4_instance.k12['key'], ToyModule3SubClass))
    self.assertTrue(isinstance(test4_instance.k12['key'].k7, ToyModuleSubClass))

class TestModule(unittest.TestCase):

    def test_base_config(self):
        config = ToyConfig(var1='test', var2=['test2', 'test3'])
        config_params = config.get_config_params()
        self.assertEqual(len(config_params), 3)
        self.assertTrue('var1' in config_params)
        self.assertTrue('var2' in config_params)
        self.assertTrue('var3' in config_params)
        set_params = config.get_set_params(ignore=['var2'])
        self.assertEqual(len(set_params), 1)
        self.assertEqual(set_params['var1'], 'test')

def test_base_config(self):
    config = ToyConfig(var1='test', var2=['test2', 'test3'])
    config_params = config.get_config_params()
    self.assertEqual(len(config_params), 3)
    self.assertTrue('var1' in config_params)
    self.assertTrue('var2' in config_params)
    self.assertTrue('var3' in config_params)
    set_params = config.get_set_params(ignore=['var2'])
    self.assertEqual(len(set_params), 1)
    self.assertEqual(set_params['var1'], 'test')

class TestModule(unittest.TestCase):

    def test_message(self):
        m1 = Message(content='test_content', agent='agent1', action='action1', next_actions=['action2'], msg_type=MessageType.REQUEST)
        time.sleep(5)
        m2 = Message(content=ToyContent(content='test_content2'), agent='agent2', action='action3', msg_type=MessageType.RESPONSE)
        time.sleep(5)
        m3 = Message(content='test_content', agent='agent1', action='action1', next_actions=['action2'], msg_type=MessageType.REQUEST)
        self.assertTrue(m3 != m1)
        m3_message_id = m3.message_id
        m3.message_id = m1.message_id
        self.assertTrue(m1 == m3)
        m3.message_id = m3_message_id
        message_str = str(m2)
        self.assertTrue('Content: test_content2' in message_str)
        sorted_message_based_on_timestamp = Message.sort([m3, m2, m1])
        self.assertEqual(sorted_message_based_on_timestamp[0].message_id, m1.message_id)
        self.assertEqual(sorted_message_based_on_timestamp[1].message_id, m2.message_id)
        self.assertEqual(sorted_message_based_on_timestamp[2].message_id, m3.message_id)
        merged_message = Message.merge([[m3], [m1, m2]], sort=True)
        self.assertEqual(merged_message[0].message_id, m1.message_id)
        self.assertEqual(merged_message[1].message_id, m2.message_id)
        self.assertEqual(merged_message[2].message_id, m3.message_id)

def test_message(self):
    m1 = Message(content='test_content', agent='agent1', action='action1', next_actions=['action2'], msg_type=MessageType.REQUEST)
    time.sleep(5)
    m2 = Message(content=ToyContent(content='test_content2'), agent='agent2', action='action3', msg_type=MessageType.RESPONSE)
    time.sleep(5)
    m3 = Message(content='test_content', agent='agent1', action='action1', next_actions=['action2'], msg_type=MessageType.REQUEST)
    self.assertTrue(m3 != m1)
    m3_message_id = m3.message_id
    m3.message_id = m1.message_id
    self.assertTrue(m1 == m3)
    m3.message_id = m3_message_id
    message_str = str(m2)
    self.assertTrue('Content: test_content2' in message_str)
    sorted_message_based_on_timestamp = Message.sort([m3, m2, m1])
    self.assertEqual(sorted_message_based_on_timestamp[0].message_id, m1.message_id)
    self.assertEqual(sorted_message_based_on_timestamp[1].message_id, m2.message_id)
    self.assertEqual(sorted_message_based_on_timestamp[2].message_id, m3.message_id)
    merged_message = Message.merge([[m3], [m1, m2]], sort=True)
    self.assertEqual(merged_message[0].message_id, m1.message_id)
    self.assertEqual(merged_message[1].message_id, m2.message_id)
    self.assertEqual(merged_message[2].message_id, m3.message_id)

