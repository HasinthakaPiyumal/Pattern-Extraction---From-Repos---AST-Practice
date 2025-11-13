# Cluster 10

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

def init_module(self):
    if not self.is_human:
        self.init_llm()
    if self.use_long_term_memory:
        self.init_long_term_memory()
    self.actions = [] if self.actions is None else self.actions
    self._action_map = {action.name: action for action in self.actions} if self.actions else dict()
    self._save_ignore_fields = ['llm', 'llm_config']
    self.init_context_extractor()

def check_action_name(self, action_name: str):
    """
        Check if an action name is valid for this agent.
                
        Args:
            action_name: Name of the action to check
        """
    if action_name not in self._action_map:
        raise KeyError(f"'{action_name}' is an invalid action for {self.name}! Available action names: {list(self._action_map.keys())}")

class CustomizeAgent(Agent):
    """
    CustomizeAgent provides a flexible framework for creating specialized LLM-powered agents without 
    writing custom code. It enables the creation of agents with well-defined inputs and outputs, 
    custom prompt templates, and configurable parsing strategies. 
    
    Attributes:
        name (str): The name of the agent.
        description (str): A description of the agent's purpose and capabilities.
        prompt_template (PromptTemplate, optional): The prompt template that will be used for the agent's primary action. 
        prompt (str, optional): The prompt template that will be used for the agent's primary action.
            Should contain placeholders in the format `{input_name}` for each input parameter.
        llm_config (LLMConfig, optional): Configuration for the language model.
        inputs (List[dict], optional): List of input specifications, where each dict (e.g., `{"name": str, "type": str, "description": str, ["required": bool]}`) contains:
            - name (str): Name of the input parameter
            - type (str): Type of the input
            - description (str): Description of what the input represents
            - required (bool, optional): Whether this input is required (default: True)
        outputs (List[dict], optional): List of output specifications, where each dict (e.g., `{"name": str, "type": str, "description": str, ["required": bool]}`) contains:
            - name (str): Name of the output field
            - type (str): Type of the output
            - description (str): Description of what the output represents
            - required (bool, optional): Whether this output is required (default: True)
        system_prompt (str, optional): The system prompt for the LLM. Defaults to DEFAULT_SYSTEM_PROMPT.
        output_parser (Type[ActionOutput], optional): A custom class for parsing the LLM's output.
            Must be a subclass of ActionOutput.
        parse_mode (str, optional): Mode for parsing LLM output. Options are:
            - "title": Parse outputs using section titles (default)
            - "str": Parse as plain text
            - "json": Parse as JSON
            - "xml": Parse as XML
            - "custom": Use a custom parsing function
        parse_func (Callable, optional): Custom function for parsing LLM output when parse_mode is "custom".
            Must accept a "content" parameter and return a dictionary.
        title_format (str, optional): Format string for title parsing mode with {title} placeholder.
            Default is "## {title}".
        tools (list[Toolkit], optional): List of tools to be used by the agent.
        max_tool_calls (int, optional): Maximum number of tool calls. Defaults to 5. 
        custom_output_format (str, optional): Specify the output format. Only used when `prompt_template` is used. 
            If not provided, the output format will be constructed from the `outputs` specification and `parse_mode`. 
    """

    def __init__(self, name: str, description: str, prompt: Optional[str]=None, prompt_template: Optional[PromptTemplate]=None, llm_config: Optional[LLMConfig]=None, inputs: Optional[List[dict]]=None, outputs: Optional[List[dict]]=None, system_prompt: Optional[str]=None, output_parser: Optional[Type[ActionOutput]]=None, parse_mode: Optional[str]='title', parse_func: Optional[Callable]=None, title_format: Optional[str]=None, tools: Optional[List[Union[Toolkit, Tool]]]=None, max_tool_calls: Optional[int]=5, custom_output_format: Optional[str]=None, **kwargs):
        system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        inputs = inputs or []
        outputs = outputs or []
        if tools is not None:
            raw_tool_map = {tool.name: tool for tool in tools}
            tools = [tool if isinstance(tool, Toolkit) else Toolkit(name=tool.name, tools=[tool]) for tool in tools]
        else:
            raw_tool_map = None
        if prompt is not None and prompt_template is not None:
            logger.warning('Both `prompt` and `prompt_template` are provided in `CustomizeAgent`. `prompt_template` will be used.')
            prompt = None
        if isinstance(parse_func, str):
            if not PARSE_FUNCTION_REGISTRY.has_function(parse_func):
                raise ValueError(f'parse function `{parse_func}` is not registered! To instantiate a CustomizeAgent from a file, you should use decorator `@register_parse_function` to register the parse function.')
            parse_func = PARSE_FUNCTION_REGISTRY.get_function(parse_func)
        if isinstance(output_parser, str):
            output_parser = MODULE_REGISTRY.get_module(output_parser)
        if parse_mode == 'title' and title_format is None:
            title_format = '## {title}'
        self.validate_data(prompt=prompt, prompt_template=prompt_template, inputs=inputs, outputs=outputs, output_parser=output_parser, parse_mode=parse_mode, parse_func=parse_func, title_format=title_format)
        customize_action = self.create_customize_action(name=name, desc=description, prompt=prompt, prompt_template=prompt_template, inputs=inputs, outputs=outputs, parse_mode=parse_mode, parse_func=parse_func, output_parser=output_parser, title_format=title_format, custom_output_format=custom_output_format, tools=tools, max_tool_calls=max_tool_calls)
        super().__init__(name=name, description=description, llm_config=llm_config, system_prompt=system_prompt, actions=[customize_action], **kwargs)
        self._store_inputs_outputs_info(inputs, outputs, raw_tool_map)
        self.output_parser = output_parser
        self.parse_mode = parse_mode
        self.parse_func = parse_func
        self.title_format = title_format
        self.tools = tools
        self.max_tool_calls = max_tool_calls
        self.custom_output_format = custom_output_format

    def _add_tools(self, tools: List[Toolkit]):
        self.get_action(self.customize_action_name).add_tools(tools)

    @property
    def customize_action_name(self) -> str:
        """
        Get the name of the primary custom action for this agent.
        
        Returns:
            The name of the primary custom action
        """
        for action in self.actions:
            if action.name != self.cext_action_name:
                return action.name
        raise ValueError("Couldn't find the customize action name!")

    @property
    def action(self) -> Action:
        """
        Get the primary custom action for this agent.
        
        Returns:
            The primary custom action
        """
        return self.get_action(self.customize_action_name)

    @property
    def prompt(self) -> str:
        """
        Get the prompt for the primary custom action.
        
        Returns:
            The prompt for the primary custom action
        """
        return self.action.prompt

    @property
    def prompt_template(self) -> PromptTemplate:
        """
        Get the prompt template for the primary custom action.
        
        Returns:
            The prompt template for the primary custom action
        """
        return self.action.prompt_template

    def validate_data(self, prompt: str, prompt_template: PromptTemplate, inputs: List[dict], outputs: List[dict], output_parser: Type[ActionOutput], parse_mode: str, parse_func: Callable, title_format: str):
        if prompt is None and prompt_template is None:
            raise ValueError('`prompt` or `prompt_template` is required when creating a CustomizeAgent.')
        if prompt_template is None and inputs:
            all_input_names = [input_item['name'] for input_item in inputs]
            inputs_names_not_in_prompt = [name for name in all_input_names if f'{{{name}}}' not in prompt]
            if inputs_names_not_in_prompt:
                raise KeyError(f'The following inputs are not found in the prompt: {inputs_names_not_in_prompt}.')
        if output_parser is not None:
            self._check_output_parser(outputs, output_parser)
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
        if parse_mode == 'custom':
            if parse_func is None:
                raise ValueError("`parse_func` (a callable function with an input argument `content`) must be provided when `parse_mode` is 'custom'.")
        if parse_func is not None:
            if not callable(parse_func):
                raise ValueError('`parse_func` must be a callable function with an input argument `content`.')
            signature = inspect.signature(parse_func)
            if 'content' not in signature.parameters:
                raise ValueError('`parse_func` must have an input argument `content`.')
            if not PARSE_FUNCTION_REGISTRY.has_function(parse_func.__name__):
                logger.warning(f"parse function `{parse_func.__name__}` is not registered. This can cause issues when loading the agent from a file. It is recommended to register the parse function using `register_parse_function`:\nfrom evoagentx.core.registry import register_parse_function\n@register_parse_function\ndef {parse_func.__name__}(content: str) -> dict:\n    return {{'output_name': output_value}}")
        if title_format is not None:
            if parse_mode != 'title':
                logger.warning(f"`title_format` will not be used because `parse_mode` is '{parse_mode}', not 'title'. Set `parse_mode='title'` to use title formatting.")
            if '{title}' not in title_format:
                raise ValueError('`title_format` must contain the placeholder `{title}`.')

    def create_customize_action(self, name: str, desc: str, prompt: str, prompt_template: PromptTemplate, inputs: List[dict], outputs: List[dict], parse_mode: str, parse_func: Optional[Callable]=None, output_parser: Optional[ActionOutput]=None, title_format: Optional[str]='## {title}', custom_output_format: Optional[str]=None, tools: Optional[List[Toolkit]]=None, max_tool_calls: Optional[int]=5) -> Action:
        """Create a custom action based on the provided specifications.
        
        This method dynamically generates an Action class and instance with:
        - Input parameters defined by the inputs specification
        - Output format defined by the outputs specification
        - Custom execution logic using the customize_action_execute function
        - If tools is provided, returns a CustomizeAction action instead
        
        Args:
            name: Base name for the action
            desc: Description of the action
            prompt: Prompt template for the action
            prompt_template: Prompt template for the action
            inputs: List of input field specifications
            outputs: List of output field specifications
            parse_mode: Mode to use for parsing LLM output
            parse_func: Optional custom parsing function
            output_parser: Optional custom output parser class
            tools: Optional list of tools
            
        Returns:
            A newly created Action instance
        """
        assert prompt is not None or prompt_template is not None, 'must provide `prompt` or `prompt_template` when creating CustomizeAgent'
        action_input_fields = {}
        for field in inputs:
            required = field.get('required', True)
            if required:
                action_input_fields[field['name']] = (str, Field(description=field['description']))
            else:
                action_input_fields[field['name']] = (Optional[str], Field(default=None, description=field['description']))
        action_input_type = create_model(self._get_unique_class_name(generate_dynamic_class_name(name + ' action_input')), **action_input_fields, __base__=ActionInput)
        if output_parser is None:
            action_output_fields = {}
            for field in outputs:
                required = field.get('required', True)
                if required:
                    action_output_fields[field['name']] = (Any, Field(description=field['description']))
                else:
                    action_output_fields[field['name']] = (Optional[Any], Field(default=None, description=field['description']))
            action_output_type = create_model(self._get_unique_class_name(generate_dynamic_class_name(name + ' action_output')), **action_output_fields, __base__=ActionOutput)
        else:
            action_output_type = output_parser
        action_cls_name = self._get_unique_class_name(generate_dynamic_class_name(name + ' action'))
        customize_action_cls = create_model(action_cls_name, __base__=CustomizeAction)
        customize_action = customize_action_cls(name=action_cls_name, description=desc, prompt=prompt, prompt_template=prompt_template, inputs_format=action_input_type, outputs_format=action_output_type, parse_mode=parse_mode, parse_func=parse_func, title_format=title_format, custom_output_format=custom_output_format, max_tool_try=max_tool_calls, tools=tools)
        return customize_action

    def _check_output_parser(self, outputs: List[dict], output_parser: Type[ActionOutput]):
        if output_parser is not None:
            if not isinstance(output_parser, type):
                raise TypeError(f'output_parser must be a class, but got {type(output_parser).__name__}')
            if not issubclass(output_parser, ActionOutput):
                raise ValueError(f'`output_parser` must be a class and a subclass of `ActionOutput`, but got `{output_parser.__name__}`.')
        output_parser_fields = output_parser.get_attrs()
        all_output_names = [output_item['name'] for output_item in outputs]
        for field in output_parser_fields:
            if field not in all_output_names:
                raise ValueError(f'The output parser `{output_parser.__name__}` is not compatible with the `outputs`.\nThe output parser fields: {output_parser_fields}.\nThe outputs: {all_output_names}.\nAll the fields in the output parser must be present in the outputs.')

    def _store_inputs_outputs_info(self, inputs: List[dict], outputs: List[dict], tool_map: Dict[str, Union[Toolkit, Tool]]):
        self._action_input_types, self._action_input_required = ({}, {})
        for field in inputs:
            required = field.get('required', True)
            self._action_input_types[field['name']] = field['type']
            self._action_input_required[field['name']] = required
        self._action_output_types, self._action_output_required = ({}, {})
        for field in outputs:
            required = field.get('required', True)
            self._action_output_types[field['name']] = field['type']
            self._action_output_required[field['name']] = required
        self._raw_tool_map = tool_map

    def __call__(self, inputs: dict=None, return_msg_type: MessageType=MessageType.UNKNOWN, **kwargs) -> Message:
        """
        Call the customize action.

        Args:
            inputs (dict): The inputs to the customize action.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            ActionOutput: The output of the customize action.
        """
        inputs = inputs or {}
        return super().__call__(action_name=self.customize_action_name, action_input_data=inputs, return_msg_type=return_msg_type, **kwargs)

    def get_customize_agent_info(self) -> dict:
        """
        Get the information of the customize agent.
        """
        customize_action = self.get_action(self.customize_action_name)
        action_input_params = customize_action.inputs_format.get_attrs()
        action_output_params = customize_action.outputs_format.get_attrs()
        config = {'class_name': 'CustomizeAgent', 'name': self.name, 'description': self.description, 'prompt': customize_action.prompt, 'prompt_template': customize_action.prompt_template.to_dict() if customize_action.prompt_template is not None else None, 'inputs': [{'name': field, 'type': self._action_input_types[field], 'description': field_info.description, 'required': self._action_input_required[field]} for field, field_info in customize_action.inputs_format.model_fields.items() if field in action_input_params], 'outputs': [{'name': field, 'type': self._action_output_types[field], 'description': field_info.description, 'required': self._action_output_required[field]} for field, field_info in customize_action.outputs_format.model_fields.items() if field in action_output_params], 'system_prompt': self.system_prompt, 'output_parser': self.output_parser.__name__ if self.output_parser is not None else None, 'parse_mode': self.parse_mode, 'parse_func': self.parse_func.__name__ if self.parse_func is not None else None, 'title_format': self.title_format, 'tool_names': [tool.name for tool in customize_action.tools] if customize_action.tools else [], 'max_tool_calls': self.max_tool_calls, 'custom_output_format': self.custom_output_format}
        return config

    @classmethod
    def load_module(cls, path: str, llm_config: LLMConfig=None, tools: List[Union[Toolkit, Tool]]=None, **kwargs) -> 'CustomizeAgent':
        """
        load the agent from local storage. Must provide `llm_config` when loading the agent from local storage. 
            If tools is provided, tool_names must also be provided. 

        Args:
            path: The path of the file
            llm_config: The LLMConfig instance
            tool_names: List of tool names to be used by the agent. If provided,
            tool_dict: Dictionary mapping tool names to Tool instances. Required when tool_names is provided.

        Returns:
            CustomizeAgent: The loaded agent instance
        """
        match_dict = {}
        agent = super().load_module(path=path, llm_config=llm_config, **kwargs)
        if tools:
            match_dict = {tool.name: tool for tool in tools}
        if agent.get('tool_names', None):
            assert tools is not None, 'must provide `tools: List[Union[Toolkit, Tool]]` when using `load_module` or `from_file` to load the agent from local storage and `tool_names` is not None or empty'
            added_tools = [match_dict[tool_name] for tool_name in agent['tool_names']]
            agent['tools'] = [tool if isinstance(tool, Toolkit) else Toolkit(name=tool.name, tools=[tool]) for tool in added_tools]
        return agent

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """Save the customize agent's configuration to a JSON file.
        
        Args:
            path: File path where the configuration should be saved
            ignore: List of keys to exclude from the saved configuration
            **kwargs (Any): Additional parameters for the save operation
            
        Returns:
            The path where the configuration was saved
        """
        config = self.get_customize_agent_info()
        for ignore_key in ignore:
            config.pop(ignore_key, None)
        make_parent_folder(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return path

    def _get_unique_class_name(self, candidate_name: str) -> str:
        """
        Get a unique class name by checking if it already exists in the registry.
        If it does, append "Vx" to make it unique.
        """
        if not MODULE_REGISTRY.has_module(candidate_name):
            return candidate_name
        i = 1
        while True:
            unique_name = f'{candidate_name}V{i}'
            if not MODULE_REGISTRY.has_module(unique_name):
                break
            i += 1
        return unique_name

    def get_config(self) -> dict:
        """
        Get a dictionary containing all necessary configuration to recreate this agent.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new Agent instance
            with the same properties as this one.
        """
        config = self.get_customize_agent_info()
        config['llm_config'] = self.llm_config.to_dict()
        tool_names = config.pop('tool_names', None)
        if tool_names:
            config['tools'] = [self._raw_tool_map[name] for name in tool_names]
        return config

def validate_data(self, prompt: str, prompt_template: PromptTemplate, inputs: List[dict], outputs: List[dict], output_parser: Type[ActionOutput], parse_mode: str, parse_func: Callable, title_format: str):
    if prompt is None and prompt_template is None:
        raise ValueError('`prompt` or `prompt_template` is required when creating a CustomizeAgent.')
    if prompt_template is None and inputs:
        all_input_names = [input_item['name'] for input_item in inputs]
        inputs_names_not_in_prompt = [name for name in all_input_names if f'{{{name}}}' not in prompt]
        if inputs_names_not_in_prompt:
            raise KeyError(f'The following inputs are not found in the prompt: {inputs_names_not_in_prompt}.')
    if output_parser is not None:
        self._check_output_parser(outputs, output_parser)
    if parse_mode not in PARSER_VALID_MODE:
        raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
    if parse_mode == 'custom':
        if parse_func is None:
            raise ValueError("`parse_func` (a callable function with an input argument `content`) must be provided when `parse_mode` is 'custom'.")
    if parse_func is not None:
        if not callable(parse_func):
            raise ValueError('`parse_func` must be a callable function with an input argument `content`.')
        signature = inspect.signature(parse_func)
        if 'content' not in signature.parameters:
            raise ValueError('`parse_func` must have an input argument `content`.')
        if not PARSE_FUNCTION_REGISTRY.has_function(parse_func.__name__):
            logger.warning(f"parse function `{parse_func.__name__}` is not registered. This can cause issues when loading the agent from a file. It is recommended to register the parse function using `register_parse_function`:\nfrom evoagentx.core.registry import register_parse_function\n@register_parse_function\ndef {parse_func.__name__}(content: str) -> dict:\n    return {{'output_name': output_value}}")
    if title_format is not None:
        if parse_mode != 'title':
            logger.warning(f"`title_format` will not be used because `parse_mode` is '{parse_mode}', not 'title'. Set `parse_mode='title'` to use title formatting.")
        if '{title}' not in title_format:
            raise ValueError('`title_format` must contain the placeholder `{title}`.')

class HITLManager(BaseModule):
    """
    HITL Manager - Manages Human-in-the-Loop interactions
    It must be instancialized and add as a parameter to the WorkFlow instance like: workflow = WorkFlow(graph=graph, llm=llm, agent_manager=AgentManager(agents=agents), hitl_manager=hitl_manager)
    """
    active: bool = Field(default=False, description='Whether HITL is currently active')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self.hitl_input_output_mapping = {}

    def init_module(self):
        """Module initialization"""
        self._pending_requests: Dict[str, asyncio.Future] = {}

    def activate(self):
        """activate HITL feature"""
        self.active = True
        logger.info('HITL feature activated')

    def deactivate(self):
        """deactivate HITL feature"""
        self.active = False
        logger.info('HITL feature deactivated')

    @property
    def is_active(self) -> bool:
        return self.active

    async def request_approval(self, task_name: str, agent_name: str, action_name: str, interaction_type: HITLInteractionType, mode: HITLMode, action_inputs_data: dict=None, execution_result=None, workflow_goal: str=None, display_context: Dict=None, timeout: float=1800.0) -> HITLResponse:
        """Request human approval"""
        if not self.active:
            return HITLResponse(request_id='auto_approved', decision=HITLDecision.APPROVE, feedback='HITL not active, auto-approved')
        context = HITLContext(task_name=task_name, agent_name=agent_name, action_name=action_name, workflow_goal=workflow_goal, action_inputs=action_inputs_data or {}, execution_result=execution_result, display_context=display_context or {})
        prompt_message = self._generate_prompt_message(interaction_type, mode, context)
        request = HITLRequest(interaction_type=interaction_type, mode=mode, context=context, prompt_message=prompt_message)
        future = asyncio.Future()
        self._pending_requests[request.request_id] = future
        try:
            response = await self._handle_cli_interaction(request, timeout)
            future.set_result(response)
            return response
        except asyncio.TimeoutError:
            response = HITLResponse(request_id=request.request_id, decision=HITLDecision.REJECT, feedback='Timeout: No human response received')
            future.set_result(response)
            return response
        finally:
            self._pending_requests.pop(request.request_id, None)

    async def _handle_cli_interaction(self, request: HITLRequest, timeout: float) -> HITLResponse:
        """handle cli interaction"""
        print('\n' + '=' * 80)
        print('🔔 Human-in-the-Loop approval request')
        print('=' * 80)
        print(request.prompt_message)
        print('=' * 80)
        try:
            if request.interaction_type == HITLInteractionType.APPROVE_REJECT:
                return await self._handle_approve_reject(request)
            elif request.interaction_type == HITLInteractionType.REVIEW_EDIT_STATE:
                return await self._handle_review_edit(request)
            elif request.interaction_type == HITLInteractionType.REVIEW_TOOL_CALLS:
                return await self._handle_tool_calls(request)
            elif request.interaction_type == HITLInteractionType.MULTI_TURN_CONVERSATION:
                return await self._handle_conversation(request)
            else:
                return HITLResponse(request_id=request.request_id, decision=HITLDecision.REJECT, feedback='Unknown interaction type')
        except Exception as e:
            logger.error(f'CLI interaction error: {e}')
            return HITLResponse(request_id=request.request_id, decision=HITLDecision.REJECT, feedback=f'Error: {str(e)}')

    async def _handle_approve_reject(self, request: HITLRequest) -> HITLResponse:
        """handle approve/reject"""

        def get_user_input():
            while True:
                choice = input('\nPlease select [a]pprove / [r]eject: ').lower().strip()
                if choice in ['a', 'approve']:
                    return HITLDecision.APPROVE
                elif choice in ['r', 'reject']:
                    return HITLDecision.REJECT
                print("Invalid input, please input 'a' or 'r'")
        loop = asyncio.get_event_loop()
        decision = await loop.run_in_executor(None, get_user_input)
        feedback = ''
        if decision == HITLDecision.REJECT:

            def get_feedback():
                return input('Please provide the reason for rejection (optional): ').strip()
            feedback = await loop.run_in_executor(None, get_feedback)
        return HITLResponse(request_id=request.request_id, decision=decision, feedback=feedback if feedback else None)

    async def _handle_review_edit(self, request: HITLRequest) -> HITLResponse:
        """handle review edit"""
        raise NotImplementedError('Not implemented HITL type: HITLInteractionType.REVIEW_EDIT_STATE')

    async def _handle_tool_calls(self, request: HITLRequest) -> HITLResponse:
        """handle tool calls review"""
        raise NotImplementedError('Not implemented HITL type: HITLInteractionType.REVIEW_TOOL_CALLS')

    async def _handle_conversation(self, request: HITLRequest) -> HITLResponse:
        """handle multi-turn conversation"""
        raise NotImplementedError('Not implemented HITL type: HITLInteractionType.MULTI_TURN_CONVERSATION')

    def _generate_prompt_message(self, interaction_type: HITLInteractionType, mode: HITLMode, context: HITLContext) -> str:
        """generate prompt message"""
        base_info = f'\nTask: {context.task_name}\nAgent: {context.agent_name}\nAction: {context.action_name}\nWorkflow Goal: {context.workflow_goal or 'N/A'}\nMode: {('Pre-Execution Approval' if mode == HITLMode.PRE_EXECUTION else 'Post-Execution Review')}\n'
        if mode == HITLMode.PRE_EXECUTION:
            base_info += f'\nparameters to be executed:\n{json.dumps(context.action_inputs, ensure_ascii=False, indent=2)}'
        else:
            base_info += f'\nexecution_result:\n{(json.dumps(context.execution_result, ensure_ascii=False, indent=2) if context.execution_result else 'None')}'
        return base_info

    async def request_user_input(self, task_name: str, agent_name: str, action_name: str, input_fields: dict, workflow_goal: str=None, display_context: dict=None, timeout: float=3600.0) -> HITLResponse:
        """Request user input based on predefined fields"""
        if not self.active:
            return HITLResponse(request_id='auto_approved', decision=HITLDecision.CONTINUE, modified_content={}, feedback='HITL not active, returning empty input')
        context = HITLContext(task_name=task_name, agent_name=agent_name, action_name=action_name, workflow_goal=workflow_goal, action_inputs={'input_fields': input_fields}, execution_result=None, display_context=display_context or {})
        prompt_message = self._generate_user_input_prompt_message(context, input_fields)
        request = HITLRequest(interaction_type=HITLInteractionType.COLLECT_USER_INPUT, mode=HITLMode.PRE_EXECUTION, context=context, prompt_message=prompt_message)
        future = asyncio.Future()
        self._pending_requests[request.request_id] = future
        try:
            response = await self._handle_user_input_collection(request, input_fields, timeout)
            future.set_result(response)
            return response
        except asyncio.TimeoutError:
            response = HITLResponse(request_id=request.request_id, decision=HITLDecision.REJECT, feedback='Timeout: No user input received')
            future.set_result(response)
            return response
        finally:
            self._pending_requests.pop(request.request_id, None)

    async def _handle_user_input_collection(self, request: HITLRequest, input_fields: dict, timeout: float) -> HITLResponse:
        """Handle user input collection"""
        print('\n' + '=' * 80)
        print('📝 User input collection request')
        print('=' * 80)
        print(request.prompt_message)
        print('=' * 80)
        try:

            def get_user_inputs():
                collected_inputs = {}
                print('\nPlease provide the following inputs:')
                for field_name, field_info in input_fields.items():
                    field_type = field_info.get('type', 'string')
                    description = field_info.get('description', '')
                    required = field_info.get('required', True)
                    default_value = field_info.get('default', None)
                    while True:
                        prompt_text = f'\n{field_name}'
                        if description:
                            prompt_text += f' ({description})'
                        if not required:
                            prompt_text += ' [optional]'
                        if default_value is not None:
                            prompt_text += f' [default: {default_value}]'
                        prompt_text += ': '
                        user_input = input(prompt_text).strip()
                        if not user_input:
                            if not required and default_value is not None:
                                user_input = str(default_value)
                            elif not required:
                                user_input = ''
                            else:
                                print(f"Field '{field_name}' is required, please provide input.")
                                continue
                        try:
                            if field_type == 'int':
                                collected_inputs[field_name] = str(user_input) if user_input else None
                            elif field_type == 'float':
                                collected_inputs[field_name] = str(user_input) if user_input else None
                            elif field_type == 'bool':
                                collected_inputs[field_name] = user_input.lower() in ['true', '1', 'yes', 'y'] if user_input else None
                            else:
                                collected_inputs[field_name] = user_input
                            break
                        except ValueError:
                            print(f"Input format error, field '{field_name}' needs {field_type} type value.")
                            continue
                print('\nCollected inputs:')
                for field_name, value in collected_inputs.items():
                    print(f'  {field_name}: {value}')
                while True:
                    confirm = input('\nConfirm these inputs? [y]es / [n]o / [r]etry: ').lower().strip()
                    if confirm in ['y', 'yes']:
                        return collected_inputs
                    elif confirm in ['n', 'no']:
                        sys.exit()
                    elif confirm in ['r', 'retry']:
                        return get_user_inputs()
                    else:
                        print("Invalid input, please input 'y', 'n' or 'r'")
            loop = asyncio.get_event_loop()
            collected_data = await loop.run_in_executor(None, get_user_inputs)
            if collected_data is not None:
                return HITLResponse(request_id=request.request_id, decision=HITLDecision.CONTINUE, modified_content=collected_data, feedback='User input collection completed')
            else:
                return HITLResponse(request_id=request.request_id, decision=HITLDecision.REJECT, feedback='User cancelled input')
        except Exception as e:
            logger.error(f'User input collection error: {e}')
            return HITLResponse(request_id=request.request_id, decision=HITLDecision.REJECT, feedback=f'Error: {str(e)}')

    def _generate_user_input_prompt_message(self, context: HITLContext, input_fields: dict) -> str:
        """Generate prompt message for user input collection"""
        base_info = f'\nTask: {context.task_name}\nAgent: {context.agent_name}\nAction: {context.action_name}\nWorkflow Goal: {context.workflow_goal or 'N/A'}\n\nUser input fields to be collected:\n'
        for field_name, field_info in input_fields.items():
            field_type = field_info.get('type', 'string')
            description = field_info.get('description', '')
            required = field_info.get('required', True)
            default_value = field_info.get('default', None)
            base_info += f'\n- {field_name} ({field_type})'
            if description:
                base_info += f': {description}'
            if not required:
                base_info += ' [optional]'
            if default_value is not None:
                base_info += f' [default: {default_value}]'
        return base_info

def _generate_prompt_message(self, interaction_type: HITLInteractionType, mode: HITLMode, context: HITLContext) -> str:
    """generate prompt message"""
    base_info = f'\nTask: {context.task_name}\nAgent: {context.agent_name}\nAction: {context.action_name}\nWorkflow Goal: {context.workflow_goal or 'N/A'}\nMode: {('Pre-Execution Approval' if mode == HITLMode.PRE_EXECUTION else 'Post-Execution Review')}\n'
    if mode == HITLMode.PRE_EXECUTION:
        base_info += f'\nparameters to be executed:\n{json.dumps(context.action_inputs, ensure_ascii=False, indent=2)}'
    else:
        base_info += f'\nexecution_result:\n{(json.dumps(context.execution_result, ensure_ascii=False, indent=2) if context.execution_result else 'None')}'
    return base_info

class WorkFlowGenerator(BaseModule):
    """
    Automated workflow generation system based on high-level goals.
    
    The WorkFlowGenerator is responsible for creating complete workflow graphs
    from high-level goals or task descriptions. It breaks down the goal into
    subtasks, creates the necessary dependency connections between tasks,
    and assigns or generates appropriate agents for each task.
    
    Attributes:
        llm: Language model used for generation and planning
        task_planner: Component responsible for breaking down goals into subtasks
        agent_generator: Component responsible for agent assignment or creation
        workflow_reviewer: Component for reviewing and improving workflows
        num_turns: Number of refinement iterations for the workflow
    """
    llm: Optional[BaseLLM] = None
    task_planner: Optional[TaskPlanner] = Field(default=None, description='Responsible for breaking down the high-level task into manageable sub-tasks.')
    agent_generator: Optional[AgentGenerator] = Field(default=None, description='Assigns or generates the appropriate agent(s) to handle each sub-task.')
    workflow_reviewer: Optional[WorkFlowReviewer] = Field(default=None, description='Provides feedback and reflections to improve the generated workflow.')
    num_turns: Optional[PositiveInt] = Field(default=0, description='Specifies the number of refinement iterations for the generated workflow.')
    tools: Optional[List[Toolkit]] = Field(default=None, description='A list of tools that can be used in the workflow.')

    def init_module(self):
        if self.task_planner is None:
            if self.llm is None:
                raise ValueError('Must provide `llm` when `task_planner` is None')
            self.task_planner = TaskPlanner(llm=self.llm)
        if self.agent_generator is None:
            if self.llm is None:
                raise ValueError('Must provide `llm` when `agent_generator` is None')
            self.agent_generator = AgentGenerator(llm=self.llm, tools=self.tools)

    def get_tool_info(self):
        self.tool_info = [{tool.name: [s['function']['description'] for s in tool.get_tool_schemas()]} for tool in self.tools]

    def _execute_with_retry(self, operation_name: str, operation, retries_left: int=1, **kwargs):
        """Helper method to execute operations with retry logic.
        
        Args:
            operation_name: Name of the operation for logging
            operation: Callable that performs the operation
            retries_left: Number of retry attempts remaining
            **kwargs: Additional arguments to pass to the operation
            
        Returns:
            Tuple of (operation_result, number_of_retries_used)
            
        Raises:
            ValueError: If operation fails after all retries are exhausted
        """
        cur_retries = 0
        while cur_retries <= retries_left:
            try:
                logger.info(f'{operation_name} (attempt {cur_retries + 1}/{retries_left + 1}) ...')
                result = operation(**kwargs)
                return (result, cur_retries)
            except Exception as e:
                if cur_retries == retries_left:
                    raise ValueError(f'Failed to {operation_name} after {cur_retries + 1} attempts.\nError: {e}')
                sleep_time = 2 ** cur_retries
                logger.error(f'Failed to {operation_name} in {cur_retries + 1} attempts. Retry after {sleep_time} seconds.\nError: {e}')
                time.sleep(sleep_time)
                cur_retries += 1

    def generate_workflow(self, goal: str, existing_agents: Optional[List[Agent]]=None, retry: int=1, **kwargs) -> WorkFlowGraph:
        if not goal or len(goal.strip()) < 10:
            raise ValueError('Goal must be at least 10 characters and descriptive')
        plan_history, plan_suggestion = ('', '')
        cur_retries = 0
        plan, added_retries = self._execute_with_retry(operation_name='Generating a workflow plan', operation=self.generate_plan, retries_left=retry, goal=goal, history=plan_history, suggestion=plan_suggestion)
        cur_retries += added_retries
        workflow, added_retries = self._execute_with_retry(operation_name='Building workflow from plan', operation=self.build_workflow_from_plan, retries_left=retry - cur_retries, goal=goal, plan=plan)
        cur_retries += added_retries
        logger.info('Validating initial workflow structure...')
        workflow._validate_workflow_structure()
        logger.info(f'Successfully generate the following workflow:\n{workflow.get_workflow_description()}')
        logger.info('Generating agents for the workflow ...')
        workflow, added_retries = self._execute_with_retry(operation_name='Generating agents for the workflow', operation=self.generate_agents, retries_left=retry - cur_retries, goal=goal, workflow=workflow, existing_agents=existing_agents)
        logger.info('Validating workflow after agent generation...')
        workflow._validate_workflow_structure()
        for node in workflow.nodes:
            if not node.agents:
                raise ValueError(f'Node {node.name} has no agents assigned after agent generation')
        return workflow

    def generate_plan(self, goal: str, history: Optional[str]=None, suggestion: Optional[str]=None) -> TaskPlanningOutput:
        history = '' if history is None else history
        suggestion = '' if suggestion is None else suggestion
        task_planner: TaskPlanner = self.task_planner
        task_planning_action_data = {'goal': goal, 'history': history, 'suggestion': suggestion}
        task_planning_action_name = task_planner.task_planning_action_name
        message: Message = task_planner.execute(action_name=task_planning_action_name, action_input_data=task_planning_action_data, return_msg_type=MessageType.REQUEST)
        return message.content

    def generate_agents(self, goal: str, workflow: WorkFlowGraph, existing_agents: Optional[List[Agent]]=None) -> WorkFlowGraph:
        agent_generator: AgentGenerator = self.agent_generator
        workflow_desc = workflow.get_workflow_description()
        agent_generation_action_name = agent_generator.agent_generation_action_name
        for subtask in workflow.nodes:
            subtask_fields = ['name', 'description', 'reason', 'inputs', 'outputs']
            subtask_data = {key: value for key, value in subtask.to_dict(ignore=['class_name']).items() if key in subtask_fields}
            subtask_desc = json.dumps(subtask_data, indent=4)
            agent_generation_action_data = {'goal': goal, 'workflow': workflow_desc, 'task': subtask_desc}
            logger.info(f'Generating agents for subtask: {subtask_data['name']}')
            agents: AgentGenerationOutput = agent_generator.execute(action_name=agent_generation_action_name, action_input_data=agent_generation_action_data, return_msg_type=MessageType.RESPONSE).content
            generated_agents = []
            for agent in agents.generated_agents:
                agent_dict = agent.to_dict(ignore=['class_name'])
                generated_agents.append(agent_dict)
            subtask.set_agents(agents=generated_agents)
        return workflow

    def build_workflow_from_plan(self, goal: str, plan: TaskPlanningOutput) -> WorkFlowGraph:
        nodes: List[WorkFlowNode] = plan.sub_tasks
        edges: List[WorkFlowEdge] = []
        for node in nodes:
            for another_node in nodes:
                if node.name == another_node.name:
                    continue
                node_output_params = [param.name for param in node.outputs]
                another_node_input_params = [param.name for param in another_node.inputs]
                if any([param in another_node_input_params for param in node_output_params]):
                    edges.append(WorkFlowEdge(edge_tuple=(node.name, another_node.name)))
        workflow = WorkFlowGraph(goal=goal, nodes=nodes, edges=edges)
        return workflow

def generate_plan(self, goal: str, history: Optional[str]=None, suggestion: Optional[str]=None) -> TaskPlanningOutput:
    history = '' if history is None else history
    suggestion = '' if suggestion is None else suggestion
    task_planner: TaskPlanner = self.task_planner
    task_planning_action_data = {'goal': goal, 'history': history, 'suggestion': suggestion}
    task_planning_action_name = task_planner.task_planning_action_name
    message: Message = task_planner.execute(action_name=task_planning_action_name, action_input_data=task_planning_action_data, return_msg_type=MessageType.REQUEST)
    return message.content

class Environment(BaseModule):
    """
    Responsible for storing and managing intermediate states of execution.
    """
    trajectory: List[TrajectoryStep] = Field(default_factory=list)
    task_execution_history: List[str] = Field(default_factory=list)
    execution_data: dict = Field(default_factory=dict)

    def update(self, message: Message, state: TrajectoryState=None, error: str=None, **kwargs):
        """
        Add a message to the shared memory and optionally to a specific task's message list.

        Args:
            message (Message): The message to be added.
            task_name (str, optional): The name of the task this message is related to. If None, the message is considered global.
        """
        state = state or TrajectoryState.COMPLETED
        step = TrajectoryStep(message=message, status=state, error=error)
        self.trajectory.append(step)
        self.update_task_execution_history(message=message)
        self.update_execution_data(message=message)

    def update_task_execution_history(self, message: Message):
        if message.wf_task is not None and message.msg_type in [MessageType.RESPONSE]:
            if not self.task_execution_history or message.wf_task != self.task_execution_history[-1]:
                self.task_execution_history.append(message.wf_task)

    def update_execution_data(self, message: Message):
        if isinstance(message.content, LLMOutputParser):
            data = message.content.get_structured_data()
            self.execution_data.update(data)
        if isinstance(message.content, dict):
            data = message.content
            self.execution_data.update(data)

    def update_execution_data_from_context_extraction(self, extracted_data: dict):
        for key, value in extracted_data.items():
            if key not in self.execution_data:
                self.execution_data[key] = value

    def get_task_messages(self, tasks: Union[str, List[str]], n: int=None, include_inputs: bool=False, **kwargs) -> List[Message]:
        """
        Retrieve all messages related to specified tasks

        Returns:
            List[Message]: A list of messages related to the task.
        """
        if isinstance(tasks, str):
            tasks = [tasks]
        message_list = []
        for step in self.trajectory:
            message = step.message
            if message.wf_task is not None and message.wf_task in tasks:
                message_list.append(message)
            if include_inputs and message.msg_type == MessageType.INPUT and (message not in message_list):
                message_list.append(message)
        message_list = message_list if n is None else message_list[-n:]
        return message_list

    def get(self, n: int=None) -> List[Message]:
        """
        return the most recent n messages
        """
        assert n is None or n >= 0, 'n must be None or a positive int'
        all_messages = [step.message for step in self.trajectory]
        messages = all_messages if n is None else all_messages[-n:]
        return messages

    def get_last_executed_task(self) -> str:
        if self.task_execution_history:
            return self.task_execution_history[-1]
        return None

    def get_all_execution_data(self) -> dict:
        return self.execution_data

    def get_execution_data(self, params: Union[str, List[str]]) -> dict:
        if isinstance(params, str):
            params = [params]
        data = {}
        for param in params:
            if param not in self.execution_data:
                raise KeyError(f"Couldn't find execution data with key '{param}'. Available execution data: {list(self.execution_data.keys())}")
            data[param] = self.execution_data[param]
        return data

def get_execution_data(self, params: Union[str, List[str]]) -> dict:
    if isinstance(params, str):
        params = [params]
    data = {}
    for param in params:
        if param not in self.execution_data:
            raise KeyError(f"Couldn't find execution data with key '{param}'. Available execution data: {list(self.execution_data.keys())}")
        data[param] = self.execution_data[param]
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

def contain_loop(loops: List[List[str]], new_loop: List[str]):
    if not loops:
        return False
    return frozenset(new_loop) in [frozenset(loop) for loop in loops]

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

class ConvergenceUtils:

    def __init__(self, root_path):
        self.root_path = root_path
        self.data = None
        self.rounds = None
        self.avg_scores, self.stds = (None, None)

    def load_data(self, root_path):
        """
        Read JSON file, create a new file if it doesn't exist, then return the data.
        """
        rounds_dir = self.root_path
        result_file = os.path.join(rounds_dir, 'results.json')
        os.makedirs(rounds_dir, exist_ok=True)
        if not os.path.exists(result_file):
            with open(result_file, 'w') as file:
                json.dump([], file)
        with open(result_file, 'r') as file:
            return json.load(file)

    def process_rounds(self):
        """
        Organize data by round, return a dictionary of scores by round.
        """
        self.data = self.load_data(root_path=self.root_path)
        rounds = {}
        for entry in self.data:
            round_number = entry['round']
            score = entry['score']
            if round_number not in rounds:
                rounds[round_number] = []
            rounds[round_number].append(score)
        return rounds

    def calculate_avg_and_std(self):
        """
        Calculate average score and standard deviation for each round, return two lists: average scores and standard deviations.
        """
        self.rounds = self.process_rounds()
        sorted_rounds = sorted(self.rounds.items(), key=lambda x: x[0])
        avg_scores = []
        stds = []
        for round_number, scores in sorted_rounds:
            avg_scores.append(np.mean(scores))
            stds.append(np.std(scores))
        return (avg_scores, stds)

    def check_convergence(self, top_k=3, z=0, consecutive_rounds=5):
        """
        Check for convergence. z is the z-score corresponding to the confidence level.
        consecutive_rounds is the number of consecutive rounds that must meet the stop condition.
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        if len(self.avg_scores) < top_k + 1:
            return (False, None, None)
        convergence_count = 0
        previous_y = None
        sigma_y_previous = None
        for i in range(len(self.avg_scores)):
            top_k_indices = np.argsort(self.avg_scores[:i + 1])[::-1][:top_k]
            top_k_scores = [self.avg_scores[j] for j in top_k_indices]
            top_k_stds = [self.stds[j] for j in top_k_indices]
            y_current = np.mean(top_k_scores)
            sigma_y_current = np.sqrt(np.sum([s ** 2 for s in top_k_stds]) / top_k ** 2)
            if previous_y is not None:
                delta_y = y_current - previous_y
                sigma_delta_y = np.sqrt(sigma_y_current ** 2 + sigma_y_previous ** 2)
                if abs(delta_y) <= z * sigma_delta_y:
                    convergence_count += 1
                    if convergence_count >= consecutive_rounds:
                        return (True, i - consecutive_rounds + 1, i)
                else:
                    convergence_count = 0
            previous_y = y_current
            sigma_y_previous = sigma_y_current
        return (False, None, None)

    def print_results(self):
        """
        Print average score and standard deviation for all rounds.
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        for i, (avg_score, std) in enumerate(zip(self.avg_scores, self.stds), 1):
            logger.info(f'Round {i}: Average Score = {avg_score:.4f}, Standard Deviation = {std:.4f}')

def check_convergence(self, top_k=3, z=0, consecutive_rounds=5):
    """
        Check for convergence. z is the z-score corresponding to the confidence level.
        consecutive_rounds is the number of consecutive rounds that must meet the stop condition.
        """
    self.avg_scores, self.stds = self.calculate_avg_and_std()
    if len(self.avg_scores) < top_k + 1:
        return (False, None, None)
    convergence_count = 0
    previous_y = None
    sigma_y_previous = None
    for i in range(len(self.avg_scores)):
        top_k_indices = np.argsort(self.avg_scores[:i + 1])[::-1][:top_k]
        top_k_scores = [self.avg_scores[j] for j in top_k_indices]
        top_k_stds = [self.stds[j] for j in top_k_indices]
        y_current = np.mean(top_k_scores)
        sigma_y_current = np.sqrt(np.sum([s ** 2 for s in top_k_stds]) / top_k ** 2)
        if previous_y is not None:
            delta_y = y_current - previous_y
            sigma_delta_y = np.sqrt(sigma_y_current ** 2 + sigma_y_previous ** 2)
            if abs(delta_y) <= z * sigma_delta_y:
                convergence_count += 1
                if convergence_count >= consecutive_rounds:
                    return (True, i - consecutive_rounds + 1, i)
            else:
                convergence_count = 0
        previous_y = y_current
        sigma_y_previous = sigma_y_current
    return (False, None, None)

class BrowserUseBase(BaseModule):
    """
    Base class for Browser Use interactions.
    Handles LLM setup, browser configuration, and async agent execution.
    """

    def __init__(self, model: str='gpt-4o-mini', api_key: str=os.getenv('OPENAI_API_KEY'), browser_type: str='chromium', headless: bool=True, **kwargs):
        """
        Initialize the BrowserUse base.
        
        Args:
            model: LLM model to use (gpt-4o-mini, claude-3-5-sonnet, etc.)
            api_key: API key for the LLM (if not in environment)
            browser_type: Browser type (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
        """
        super().__init__(**kwargs)
        try:
            from browser_use import Agent
            from browser_use.llm import ChatOpenAI, ChatAnthropic
            self.Agent = Agent
            self.ChatOpenAI = ChatOpenAI
            self.ChatAnthropic = ChatAnthropic
        except ImportError:
            try:
                from browser_use_py310x import Agent
                from browser_use_py310x.llm import ChatOpenAI, ChatAnthropic
                self.Agent = Agent
                self.ChatOpenAI = ChatOpenAI
                self.ChatAnthropic = ChatAnthropic
            except ImportError as e:
                logger.error('browser-use package not installed. For Python 3.11+: pip install browser-use, For Python 3.10: pip install browser-use-py310x')
                raise ImportError(f'browser-use package required: {e}')
        self.model = model
        self.api_key = api_key
        self.browser_type = browser_type
        self.headless = headless
        self.llm = self._setup_llm()
        self.browser_config = {'browser_type': browser_type, 'headless': headless}

    def _setup_llm(self):
        """Setup the appropriate LLM based on model name."""
        try:
            if 'gpt' in self.model.lower() or 'openai' in self.model.lower():
                kwargs = {'model': self.model}
                if self.api_key:
                    kwargs['api_key'] = self.api_key
                return self.ChatOpenAI(**kwargs)
            elif 'claude' in self.model.lower() or 'anthropic' in self.model.lower():
                kwargs = {'model': self.model}
                if self.api_key:
                    kwargs['api_key'] = self.api_key
                return self.ChatAnthropic(**kwargs)
            else:
                logger.warning(f'Unknown model {self.model}, defaulting to OpenAI')
                return self.ChatOpenAI(model=self.model)
        except Exception as e:
            logger.error(f'Failed to setup LLM: {e}')
            raise

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a browser task using the Browser Use agent.
        
        Args:
            task: The task description for the browser agent
            
        Returns:
            Dictionary containing task results
        """
        try:
            agent = self.Agent(task=task, llm=self.llm, **self.browser_config)
            logger.info(f'Executing browser task: {task}')
            result = await agent.run()
            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f'Browser task failed: {e}')
            return {'success': False, 'error': str(e)}

    def execute_task_sync(self, task: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_task.
        
        Args:
            task: The task description for the browser agent
            
        Returns:
            Dictionary containing task results
        """
        try:
            return asyncio.run(self.execute_task(task))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            task_coro = self.execute_task(task)
            return loop.run_until_complete(task_coro)

def _setup_llm(self):
    """Setup the appropriate LLM based on model name."""
    try:
        if 'gpt' in self.model.lower() or 'openai' in self.model.lower():
            kwargs = {'model': self.model}
            if self.api_key:
                kwargs['api_key'] = self.api_key
            return self.ChatOpenAI(**kwargs)
        elif 'claude' in self.model.lower() or 'anthropic' in self.model.lower():
            kwargs = {'model': self.model}
            if self.api_key:
                kwargs['api_key'] = self.api_key
            return self.ChatAnthropic(**kwargs)
        else:
            logger.warning(f'Unknown model {self.model}, defaulting to OpenAI')
            return self.ChatOpenAI(model=self.model)
    except Exception as e:
        logger.error(f'Failed to setup LLM: {e}')
        raise

class DockerInterpreter(BaseInterpreter):
    """
    A Docker-based interpreter for executing Python, Bash, and R scripts in an isolated environment.
    """
    CODE_EXECUTE_CMD_MAPPING: ClassVar[Dict[str, str]] = {'python': 'python {file_name}'}
    CODE_TYPE_MAPPING: ClassVar[Dict[str, str]] = {'python': 'python', 'py3': 'python', 'python3': 'python', 'py': 'python'}
    require_confirm: bool = Field(default=False, description='Whether to require confirmation before executing code')
    print_stdout: bool = Field(default=True, description='Whether to print stdout')
    print_stderr: bool = Field(default=True, description='Whether to print stderr')
    host_directory: str = Field(default='', description='The path to the host directory to use for the container')
    container_directory: str = Field(default='/home/app/', description='The directory to use for the container')
    container_command: str = Field(default='tail -f /dev/null', description='The command to use for the container')
    tmp_directory: str = Field(default='/tmp', description='The directory to use for the container')
    image_tag: Optional[str] = Field(default=None, description='The Docker image tag to use')
    dockerfile_path: Optional[str] = Field(default=None, description='Path to the Dockerfile to build')
    auto_cleanup: bool = Field(default=True, description='Whether to automatically cleanup container on cleanup() call')
    auto_destroy: bool = Field(default=True, description='Whether to automatically cleanup container on object destruction')

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, name: str='DockerInterpreter', image_tag: Optional[str]=None, dockerfile_path: Optional[str]=None, require_confirm: bool=False, print_stdout: bool=True, print_stderr: bool=True, host_directory: str='', container_directory: str='/home/app/', container_command: str='tail -f /dev/null', tmp_directory: str='/tmp', storage_handler: FileStorageHandler=None, auto_cleanup: bool=True, auto_destroy: bool=True, **data):
        """
        Initialize a Docker-based interpreter for executing code in an isolated environment.
        
        Args:
            name (str): The name of the interpreter
            image_tag (str, optional): The Docker image tag to use. Must be provided if dockerfile_path is not.
            dockerfile_path (str, optional): Path to the Dockerfile to build. Must be provided if image_tag is not.
            require_confirm (bool): Whether to require confirmation before executing code
            print_stdout (bool): Whether to print stdout from code execution
            print_stderr (bool): Whether to print stderr from code execution
            host_directory (str): The path to the host directory to mount in the container
            container_directory (str): The target directory inside the container
            container_command (str): The command to run in the container
            tmp_directory (str): The temporary directory to use for file creation in the container
            **data: Additional data to pass to the parent class
        """
        super().__init__(name=name, **data)
        self.require_confirm = require_confirm
        self.print_stdout = print_stdout
        self.print_stderr = print_stderr
        self.host_directory = host_directory
        self.container_directory = container_directory
        self.container_command = container_command
        self.tmp_directory = tmp_directory
        self.client = docker.from_env()
        self.container = None
        self.image_tag = image_tag
        self.dockerfile_path = dockerfile_path
        self.storage_handler = storage_handler
        self.auto_cleanup = auto_cleanup
        self.auto_destroy = auto_destroy
        self._initialize_if_needed()
        if self.host_directory:
            self._upload_directory_to_container(self.host_directory)

    def __del__(self):
        try:
            if hasattr(self, 'auto_destroy') and self.auto_destroy and hasattr(self, 'container') and (self.container is not None):
                self.container.remove(force=True)
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Explicitly clean up the container and Docker client."""
        if self.auto_cleanup:
            try:
                if hasattr(self, 'container') and self.container is not None:
                    self.container.remove(force=True)
                    self.container = None
            except Exception:
                pass
            try:
                if hasattr(self, 'client') and self.client is not None:
                    self.client.close()
                    self.client = None
            except Exception:
                pass

    def _initialize_if_needed(self):
        image_tag = self.image_tag
        dockerfile_path = self.dockerfile_path
        if image_tag:
            try:
                self.client.images.get(image_tag)
            except Exception as e:
                raise ValueError(f'Image provided in image_tag but not found: {e}')
        else:
            if not dockerfile_path:
                raise ValueError('dockerfile_path or image_tag must be provided to build the image')
            dockerfile_path = Path(dockerfile_path)
            if not dockerfile_path.exists():
                raise FileNotFoundError(f'Dockerfile not found at provided path: {dockerfile_path}')
            dockerfile_dir = dockerfile_path.parent
            self.client.images.build(path=str(dockerfile_dir), tag=image_tag, rm=True, buildargs={})
        try:
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f'Docker daemon is not running: {e}')
        self.container = self.client.containers.run(image_tag, detach=True, command=self.container_command, working_dir=self.container_directory)

    def _upload_directory_to_container(self, host_directory: str):
        """
        Uploads all files and directories from the given host directory to the container directory.

        :param host_directory: Path to the local directory containing files to upload.
        :param container_directory: Target directory inside the container (defaults to self.container_directory).
        """
        host_directory = Path(host_directory).resolve()
        if not host_directory.exists() or not host_directory.is_dir():
            raise FileNotFoundError(f'Directory not found: {host_directory}')
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            for file_path in host_directory.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(host_directory)
                    target_path = Path(self.container_directory) / relative_path
                    tarinfo = tarfile.TarInfo(name=str(target_path.relative_to(self.container_directory)))
                    tarinfo.size = file_path.stat().st_size
                    with open(file_path, 'rb') as f:
                        tar.addfile(tarinfo, f)
        tar_stream.seek(0)
        if self.container is None:
            raise RuntimeError('Container is not initialized.')
        self.container.put_archive(self.container_directory, tar_stream)

    def _create_file_in_container(self, content: str) -> Path:
        filename = str(uuid.uuid4())
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content.encode('utf-8'))
            tar.addfile(tarinfo, io.BytesIO(content.encode('utf-8')))
        tar_stream.seek(0)
        if self.container is None:
            raise RuntimeError('Container is not initialized.')
        try:
            self.container.put_archive(self.tmp_directory, tar_stream)
        except Exception as e:
            raise RuntimeError(f'Failed to create file in container: {e}')
        return Path(f'{self.tmp_directory}/{filename}')

    def _run_file_in_container(self, file: Path, language: str) -> str:
        """Execute a file in the container with timeout and security checks."""
        if not self.container:
            raise RuntimeError('Container is not initialized')
        container_info = self.client.api.inspect_container(self.container.id)
        if not container_info['State']['Running']:
            raise RuntimeError('Container is not running')
        language = self._check_language(language)
        command = shlex.split(self.CODE_EXECUTE_CMD_MAPPING[language].format(file_name=file.as_posix()))
        if self.container is None:
            raise RuntimeError('Container is not initialized.')
        result = self.container.exec_run(command, demux=True)
        stdout, stderr = result.output
        if self.print_stdout and stdout:
            print(stdout.decode())
        if self.print_stderr and stderr:
            print(stderr.decode())
        stdout_str = stdout.decode() if stdout else ''
        stderr_str = stderr.decode() if stderr else ''
        return stdout_str + stderr_str

    def execute(self, code: str, language: str) -> str:
        """
        Executes code in a Docker container.
        
        Args:
            code (str): The code to execute
            language (str): The programming language to use
            
        Returns:
            str: The execution output
            
        Raises:
            RuntimeError: If container is not properly initialized or execution fails
            ValueError: If code content is invalid or exceeds limits
        """
        if not code or not code.strip():
            raise ValueError('Code content cannot be empty')
        if not self.container:
            raise RuntimeError('Container is not initialized')
        try:
            container_info = self.client.api.inspect_container(self.container.id)
            if not container_info['State']['Running']:
                raise RuntimeError('Container is not running')
        except Exception as e:
            raise RuntimeError(f'Failed to check container status: {e}')
        if self.host_directory:
            code = f"import sys; sys.path.insert(0, '{self.container_directory}');" + code
        language = self._check_language(language)
        if self.require_confirm:
            confirmation = input(f'Confirm execution of {language} code? [Y/n]: ')
            if confirmation.lower() not in ['y', 'yes', '']:
                raise RuntimeError('Execution aborted by user.')
        try:
            file_path = self._create_file_in_container(code)
            return self._run_file_in_container(file_path, language)
        except Exception as e:
            raise RuntimeError(f'Code execution failed: {e}')
        finally:
            try:
                if hasattr(self, 'container') and self.container:
                    self.container.exec_run(f'rm -f {file_path}')
            except Exception:
                pass

    def execute_script(self, file_path: str, language: str=None) -> str:
        """
        Reads code from a file and executes it in a Docker container.
        
        Args:
            file_path (str): The path to the script file to execute
            language (str, optional): The programming language of the code. If None, will be determined from the file extension.
                                    
        Returns:
            str: The execution output
            
        Raises:
            FileNotFoundError: If the script file does not exist
            RuntimeError: If container is not properly initialized or execution fails
            ValueError: If file content is invalid or exceeds limits
        """
        result = self.storage_handler.read(file_path)
        if result['success']:
            code = result['content']
        else:
            raise RuntimeError(f"Could not read file '{file_path}': {result.get('error', 'Unknown error')}")
        return self.execute(code, language)

    def _check_language(self, language: str) -> str:
        if language not in self.CODE_TYPE_MAPPING:
            raise ValueError(f'Unsupported language: {language}')
        return self.CODE_TYPE_MAPPING[language]

def execute_script(self, file_path: str, language: str=None) -> str:
    """
        Reads code from a file and executes it in a Docker container.
        
        Args:
            file_path (str): The path to the script file to execute
            language (str, optional): The programming language of the code. If None, will be determined from the file extension.
                                    
        Returns:
            str: The execution output
            
        Raises:
            FileNotFoundError: If the script file does not exist
            RuntimeError: If container is not properly initialized or execution fails
            ValueError: If file content is invalid or exceeds limits
        """
    result = self.storage_handler.read(file_path)
    if result['success']:
        code = result['content']
    else:
        raise RuntimeError(f"Could not read file '{file_path}': {result.get('error', 'Unknown error')}")
    return self.execute(code, language)

class PythonInterpreter(BaseInterpreter):
    project_path: Optional[str] = Field(default='.', description='Path to the project directory')
    directory_names: Optional[List[str]] = Field(default_factory=list, description='List of directory names to check for imports')
    allowed_imports: Optional[Set[str]] = Field(default_factory=set, description='Set of allowed imports')

    def __init__(self, name: str='PythonInterpreter', project_path: Optional[str]='.', directory_names: Optional[List[str]]=[], allowed_imports: Optional[Set[str]]=None, storage_handler: FileStorageHandler=None, **kwargs):
        """
        Initialize a Python interpreter for executing code in a controlled environment.
        
        Args:
            name (str): The name of the interpreter
            project_path (Optional[str]): Path to the project directory for module resolution
            directory_names (Optional[List[str]]): List of directory names to check for imports
            allowed_imports (Optional[Set[str]]): Set of allowed module imports to enforce security
            storage_handler (Optional[FileStorageHandler]): Storage handler for file operations
            **kwargs: Additional data to pass to the parent class
        """
        super().__init__(name=name, project_path=project_path, directory_names=directory_names, allowed_imports=allowed_imports, **kwargs)
        self.allowed_imports = allowed_imports or set()
        self.namespace = {}
        self.visited_modules = {}
        if storage_handler is None:
            from .storage_handler import LocalStorageHandler
            self.storage_handler = LocalStorageHandler(base_path='./workplace/interpreter')
        else:
            self.storage_handler = storage_handler

    def _get_file_and_folder_names(self, target_path: str) -> List[str]:
        """Retrieves the names of files and folders (without extensions) in a given directory.
        Args:
            target_path (str): Path to the target directory.
        Returns:
            List[str]: List of file and folder names (excluding extensions).
        """
        names = []
        for item in os.listdir(target_path):
            name, _ = os.path.splitext(item)
            names.append(name)
        return names

    def _extract_definitions(self, module_name: str, path: str, potential_names: Optional[Set[str]]=None) -> List[str]:
        """Extracts function and class definitions from a module file while ensuring safety.
        Args:
            module_name (str): The name of the module.
            path (str): The file path of the module.
            potential_names (Optional[Set[str]]): The specific functions/classes to import (for ImportFrom).
        Returns:
            List[str]: A list of violations found during analysis. An empty list indicates no issues.
        """
        if path in self.namespace:
            return []
        try:
            module_spec = importlib.util.spec_from_file_location(module_name, path)
            loaded_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(loaded_module)
            self.namespace[module_name] = loaded_module
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            return [''.join(traceback.format_exception(exc_type, exc_value, exc_tb))]
        result = self.storage_handler.read(path)
        if result['success']:
            code = result['content']
        else:
            raise FileNotFoundError(f'Could not read file {path}: {result.get('error', 'Unknown error')}')
        violations = self._analyze_code(code)
        if violations:
            return violations
        tree = ast.parse(code)
        available_symbols = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                available_symbols[node.name] = node
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if potential_names is None:
                for name in available_symbols:
                    if hasattr(module, name):
                        self.namespace[name] = getattr(module, name)
            else:
                for name in potential_names:
                    if name in available_symbols and hasattr(module, name):
                        self.namespace[name] = getattr(module, name)
                    else:
                        violations.append(f"Function or class '{name}' not found in {module_name}")
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            return [''.join(traceback.format_exception(exc_type, exc_value, exc_tb))]
        return violations

    def _check_project(self, module: Union[ast.Import, ast.ImportFrom]) -> List[str]:
        """Checks and imports a local project module while ensuring safety.

        Args:
            module (Union[ast.Import, ast.ImportFrom]): The AST import node representing the module.

        Returns:
            List[str]: A list of violations found during analysis.
        """
        if isinstance(module, ast.Import):
            module_name = module.name
            potential_names = None
        else:
            module_name = module.module
            potential_names = {name.name for name in module.names}
        if len(module_name.split('.')) > 1:
            module_path = os.path.join(self.project_path, *module_name.split('.')) + '.py'
        else:
            module_path = os.path.join(self.project_path, module_name + '.py')
        if os.path.exists(module_path):
            violations = self._extract_definitions(module_name, module_path, potential_names)
        else:
            return [f'Module not found: {module_name}']
        if violations:
            return violations
        try:
            module_spec = importlib.util.spec_from_file_location(module_name, module_path)
            loaded_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(loaded_module)
            self.namespace[module_name] = loaded_module
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            return [''.join(traceback.format_exception(exc_type, exc_value, exc_tb))]
        return violations

    def _execute_import(self, import_module: ast.Import) -> List[str]:
        """Processes an import statement, verifying permissions and adding modules to the namespace.

        Args:
            import_module (ast.Import): The AST node representing an import statement.

        Returns:
            List[str]: A list of violations found during import handling.
        """
        violations = []
        for module in import_module.names:
            if module.name.split('.')[0] in self.directory_names:
                violations += self._check_project(module)
                continue
            if module.name not in self.allowed_imports:
                violations.append(f'Unauthorized import: {module.name}')
                return violations
            try:
                alias = module.asname or module.name
                imported_module = importlib.import_module(module.name)
                self.namespace[alias] = imported_module
            except ImportError:
                exc_type, exc_value, exc_tb = sys.exc_info()
                violations.append(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        return violations

    def _execute_import_from(self, import_from: ast.ImportFrom) -> List[str]:
        """Processes a 'from module import name' statement, ensuring safety and adding modules to the namespace.

        Args:
            import_from (ast.ImportFrom): The AST node representing an 'import from' statement.

        Returns:
            List[str]: A list of violations found during import handling.
        """
        if import_from.module is None:
            return ["'from . import' is not supported."]
        if import_from.module.split('.')[0] in self.directory_names:
            return self._check_project(import_from)
        if import_from.module not in self.allowed_imports:
            return [f'Unauthorized import: {import_from.module}']
        try:
            for import_name in import_from.names:
                imported_module = importlib.import_module(import_from.module)
                alias = import_name.asname or import_name.name
                self.namespace[alias] = getattr(imported_module, import_name.name)
            return []
        except ImportError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            return [''.join(traceback.format_exception(exc_type, exc_value, exc_tb))]

    def _analyze_code(self, code: str) -> List[str]:
        """Parses and analyzes the code for import violations before execution.

        Args:
            code (str): The raw Python code to analyze.

        Returns:
            List[str]: A list of violations detected in the code.
        """
        violations = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    violations += self._execute_import(node)
                elif isinstance(node, ast.ImportFrom):
                    violations += self._execute_import_from(node)
        except SyntaxError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            violations.append(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        return violations

    def execute(self, code: str, language: str='python') -> str:
        """
        Analyzes and executes the provided Python code in a controlled environment.
        
        NOTE: This method only returns content printed to stdout during execution.
        It does not return any values from the code itself. To see results, use
        print statements in your code.
        
        WARNING: This method uses Python's exec() function internally, which executes
        code with full privileges. While safety checks are performed, there is still
        a security risk. Do not use with untrusted code.

        Args:
            code (str): The Python code to execute.
            language (str, optional): The programming language of the code. Defaults to "python".

        Returns:
            str: The output of the executed code (printed content only), or a list of violations if found.
        """
        if language.lower() != 'python':
            return f'Error: This interpreter only supports Python language. Received: {language}'
        self.visited_modules = {}
        self.namespace = {}
        if not self.project_path:
            raise ValueError('Project path (project_path) is not set')
        if not os.path.exists(self.project_path):
            raise ValueError(f"Project path '{self.project_path}' does not exist")
        if not os.path.isdir(self.project_path):
            raise ValueError(f"Project path '{self.project_path}' is not a directory")
        os.chdir(self.project_path)
        sys.path.insert(0, self.project_path)
        if self.allowed_imports:
            violations = self._analyze_code(code)
            if violations:
                return '\n'.join(violations)
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            try:
                exec(code, {'__builtins__': __builtins__})
            except Exception:
                exc_type, exc_value, exc_tb = sys.exc_info()
                error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
                return error_msg
        return stdout_capture.getvalue().strip()

    def execute_script(self, file_path: str, language: str='python') -> str:
        """
        Reads Python code from a file and executes it using the `execute` method.
        
        NOTE: This method only returns content printed to stdout during execution.
        It does not return any values from the code itself. To see results, use
        print statements in your code.
        
        WARNING: This method uses Python's exec() function internally, which executes
        code with full privileges. While safety checks are performed, there is still
        a security risk. Do not use with untrusted code.

        Args:
            file_path (str): The path to the Python file to be executed.
            language (str, optional): The programming language of the code. Defaults to "python".

        Returns:
            str: The output of the executed code (printed content only), or an error message if the execution fails.
        """
        result = self.storage_handler.read(file_path)
        if result['success']:
            code = result['content']
        else:
            return f"Error: Could not read file '{file_path}': {result.get('error', 'Unknown error')}"
        return self.execute(code, language)

def execute_script(self, file_path: str, language: str='python') -> str:
    """
        Reads Python code from a file and executes it using the `execute` method.
        
        NOTE: This method only returns content printed to stdout during execution.
        It does not return any values from the code itself. To see results, use
        print statements in your code.
        
        WARNING: This method uses Python's exec() function internally, which executes
        code with full privileges. While safety checks are performed, there is still
        a security risk. Do not use with untrusted code.

        Args:
            file_path (str): The path to the Python file to be executed.
            language (str, optional): The programming language of the code. Defaults to "python".

        Returns:
            str: The output of the executed code (printed content only), or an error message if the execution fails.
        """
    result = self.storage_handler.read(file_path)
    if result['success']:
        code = result['content']
    else:
        return f"Error: Could not read file '{file_path}': {result.get('error', 'Unknown error')}"
    return self.execute(code, language)

class FaissDatabase(BaseModule):
    """
    A high-level interface for FAISS vector database operations.
    
    This class wraps the RAGEngine and StorageHandler to provide a unified interface
    for vector database operations including document ingestion, semantic search,
    and corpus management.
    
    Attributes:
        rag_engine (RAGEngine): The RAG engine for document processing and retrieval
        storage_handler (StorageHandler): The storage handler for persistence
        default_corpus_id (str): Default corpus ID for operations
        default_index_type (str): Default index type for vector operations
    """

    def __init__(self, storage_config: StoreConfig, rag_config: RAGConfig, default_corpus_id: str='default', default_index_type: str='vector', storage_handler: StorageHandler=None, file_handler: FileStorageHandler=None, **kwargs):
        """
        Initialize the FAISS database.
        
        Args:
            storage_config (StoreConfig): Configuration for storage backends
            rag_config (RAGConfig): Configuration for RAG pipeline
            default_corpus_id (str): Default corpus ID for operations
            default_index_type (str): Default index type for vector operations
            storage_handler (StorageHandler, optional): Storage handler for file operations
            **kwargs: Additional arguments for BaseModule
        """
        super().__init__(**kwargs)
        self.storage_handler = StorageHandler(storageConfig=storage_config)
        self.rag_engine = RAGEngine(config=rag_config, storage_handler=self.storage_handler)
        if storage_handler is None:
            storage_handler = LocalStorageHandler(base_path='./workplace/storage')
        self.file_storage_handler = storage_handler
        self.default_corpus_id = default_corpus_id
        self.default_index_type = default_index_type
        logger.info(f'Initialized FAISS database with corpus_id: {default_corpus_id}')

    def query(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Query the vector database with semantic search.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
        try:
            try:
                asyncio.get_running_loop()
                logger.info('Detected running event loop, using thread executor for query')
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._query_sync, query, corpus_id, top_k, similarity_threshold, metadata_filters)
                    return future.result()
            except RuntimeError:
                logger.info('No event loop detected, using direct query processing')
                return self._query_sync(query, corpus_id, top_k, similarity_threshold, metadata_filters)
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _query_sync(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Synchronous version of query that can be safely called from a thread.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            if corpus_id not in self.rag_engine.indices:
                logger.warning(f'Corpus {corpus_id} not found. Returning empty results.')
                return {'success': True, 'data': {'query': query, 'corpus_id': corpus_id, 'total_results': 0, 'results': []}}
            query_obj = Query(query_str=query, top_k=top_k, similarity_cutoff=similarity_threshold, metadata_filters=metadata_filters)
            results = self.rag_engine.query(query_obj, corpus_id=corpus_id)
            if not results or not results.corpus:
                logger.warning(f'Query returned no results for corpus {corpus_id}')
                return {'success': True, 'data': {'query': query, 'corpus_id': corpus_id, 'total_results': 0, 'results': []}}
            chunks = results.corpus.chunks if results.corpus.chunks else []
            formatted_results = {'query': query, 'corpus_id': corpus_id, 'total_results': len(chunks), 'results': []}
            for i, chunk in enumerate(chunks):
                score = results.scores[i] if results.scores and i < len(results.scores) else 0.0
                formatted_results['results'].append({'chunk_id': chunk.chunk_id, 'content': chunk.text, 'score': score, 'metadata': chunk.metadata.model_dump() if chunk.metadata else {}, 'doc_id': chunk.metadata.doc_id if chunk.metadata else None})
            logger.info(f'Query executed successfully. Found {len(formatted_results['results'])} results.')
            return {'success': True, 'data': formatted_results}
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _is_file_path(self, text: str) -> bool:
        """
        Check if a string appears to be a file path.
        
        Args:
            text (str): The string to check
            
        Returns:
            bool: True if the string looks like a file path
        """
        path_indicators = ['/', '\\', '.txt', '.pdf', '.md', '.doc', '.docx', '.csv', '.json', '.xml', '.html', '.htm']
        return any((indicator in text for indicator in path_indicators)) and os.path.exists(text)

    def _process_file_path(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
        """
        Process a file path and return Document objects.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
        try:
            try:
                asyncio.get_running_loop()
                logger.info(f'Detected running event loop, using thread executor for {file_path}')
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._process_file_path_sync, file_path, doc_index, metadata)
                    return future.result()
            except RuntimeError:
                logger.info(f'No event loop detected, using direct processing for {file_path}')
                return self._process_file_path_sync(file_path, doc_index, metadata)
        except Exception as e:
            logger.error(f'Failed to process file {file_path}: {str(e)}')
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
            document_metadata = DocumentMetadata(**doc_metadata)
            return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

    def _process_file_path_sync(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
        """
        Synchronous version of file processing that can be safely called from a thread.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
        try:
            if self.file_storage_handler:
                result = self.file_storage_handler.read(file_path)
                if result['success']:
                    file_content = result['content']
                else:
                    raise Exception(f'Failed to read file: {result.get('error', 'Unknown error')}')
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            temp_corpus_id = f'temp_file_{uuid4().hex[:8]}'
            temp_doc = Document(text=file_content, metadata=DocumentMetadata(source_file=file_path, doc_index=doc_index, insertion_time=datetime.now().isoformat()), doc_id=str(uuid4()))
            corpus = self.rag_engine.process_documents([temp_doc], corpus_id=temp_corpus_id)
            documents = []
            for chunk in corpus.chunks:
                doc_metadata = metadata.copy() if metadata else {}
                doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'original_chunk_id': chunk.chunk_id})
                document_metadata = DocumentMetadata(**doc_metadata)
                documents.append(Document(text=chunk.text, metadata=document_metadata, doc_id=chunk.chunk_id))
            self.rag_engine.clear(corpus_id=temp_corpus_id)
            logger.info(f'Processed file {file_path} into {len(documents)} chunks')
            return documents
        except Exception as e:
            logger.error(f'Failed to process file {file_path} in sync mode: {str(e)}')
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
            document_metadata = DocumentMetadata(**doc_metadata)
            return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

    def insert(self, documents: list, corpus_id: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, batch_size: int=100) -> Dict[str, Any]:
        """
        Insert documents into the vector database.
        
        Args:
            documents (Union[List[str], List[Dict[str, Any]]]): Documents to insert. 
                Strings can be either text content or file paths (if they look like paths and exist)
            corpus_id (str, optional): Corpus ID to insert into
            metadata (Dict[str, Any], optional): Additional metadata for all documents
            batch_size (int): Batch size for processing
            
        Returns:
            Dict[str, Any]: Insertion results
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            processed_docs = []
            file_paths_processed = []
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    if self._is_file_path(doc):
                        logger.info(f'Detected file path: {doc}')
                        file_docs = self._process_file_path(doc, i, metadata)
                        processed_docs.extend(file_docs)
                        file_paths_processed.append(doc)
                    else:
                        doc_metadata = metadata.copy() if metadata else {}
                        doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                        document_metadata = DocumentMetadata(**doc_metadata)
                        processed_docs.append(Document(text=doc, metadata=document_metadata, doc_id=str(uuid4())))
                elif isinstance(doc, dict):
                    doc_metadata = metadata.copy() if metadata else {}
                    doc_metadata.update(doc.get('metadata', {}))
                    doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                    document_metadata = DocumentMetadata(**doc_metadata)
                    processed_docs.append(Document(text=doc.get('text', ''), metadata=document_metadata, doc_id=doc.get('doc_id', str(uuid4()))))
            corpus = Corpus(corpus_id=corpus_id)
            total_processed = 0
            for i in range(0, len(processed_docs), batch_size):
                batch = processed_docs[i:i + batch_size]
                batch_corpus = self.rag_engine.chunker.chunk(batch)
                batch_corpus.corpus_id = corpus_id
                self.rag_engine.add(self.default_index_type, batch_corpus, corpus_id=corpus_id)
                corpus.chunks.extend(batch_corpus.chunks)
                total_processed += len(batch)
                logger.info(f'Processed batch {i // batch_size + 1}, total processed: {total_processed}')
            self.rag_engine.save(corpus_id=corpus_id, index_type=self.default_index_type)
            result = {'corpus_id': corpus_id, 'documents_inserted': len(documents), 'chunks_created': len(corpus.chunks), 'total_processed': total_processed, 'file_paths_processed': file_paths_processed}
            logger.info(f'Successfully inserted {len(documents)} documents into corpus {corpus_id}')
            if file_paths_processed:
                logger.info(f'Processed {len(file_paths_processed)} file paths: {file_paths_processed}')
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f'Insert failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def delete(self, corpus_id: Optional[str]=None, doc_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None, clear_all: bool=False) -> Dict[str, Any]:
        """
        Delete documents or chunks from the vector database.
        
        Args:
            corpus_id (str, optional): Corpus ID to delete from
            doc_ids (List[str], optional): Document IDs to delete
            metadata_filters (Dict[str, Any], optional): Metadata filters for deletion
            clear_all (bool): Whether to clear the entire corpus
            
        Returns:
            Dict[str, Any]: Deletion results
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            if clear_all:
                self.rag_engine.clear(corpus_id=corpus_id)
                logger.info(f'Cleared entire corpus: {corpus_id}')
                return {'success': True, 'data': {'operation': 'clear_all', 'corpus_id': corpus_id}}
            if corpus_id not in self.rag_engine.indices:
                logger.warning(f'Corpus {corpus_id} not found. Nothing to delete.')
                return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'Corpus not found, nothing to delete'}}
            if doc_ids or metadata_filters:
                self.rag_engine.delete(corpus_id=corpus_id, index_type=self.default_index_type, node_ids=doc_ids, metadata_filters=metadata_filters)
                result = {'corpus_id': corpus_id, 'operation': 'selective_delete', 'doc_ids': doc_ids, 'metadata_filters': metadata_filters}
                logger.info(f'Successfully deleted from corpus {corpus_id}')
                return {'success': True, 'data': result}
            else:
                logger.warning(f'No deletion criteria provided for corpus {corpus_id}')
                return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'No deletion criteria provided'}}
        except Exception as e:
            logger.error(f'Delete failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def list_corpora(self) -> Dict[str, Any]:
        """
        List all available corpora and their metadata.
        
        Returns:
            Dict[str, Any]: List of corpora with metadata
        """
        try:
            corpora = []
            for corpus_id, indices in self.rag_engine.indices.items():
                corpus_info = {'corpus_id': corpus_id, 'index_types': list(indices.keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
                corpora.append(corpus_info)
            return {'success': True, 'data': {'corpora': corpora, 'total': len(corpora)}}
        except Exception as e:
            logger.error(f'List corpora failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def get_stats(self, corpus_id: Optional[str]=None) -> Dict[str, Any]:
        """
        Get statistics about the database or a specific corpus.
        
        Args:
            corpus_id (str, optional): Corpus ID to get stats for
            
        Returns:
            Dict[str, Any]: Database statistics
        """
        try:
            if corpus_id:
                corpus_id = corpus_id or self.default_corpus_id
                stats = {'corpus_id': corpus_id, 'exists': corpus_id in self.rag_engine.indices, 'index_types': list(self.rag_engine.indices.get(corpus_id, {}).keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
                if corpus_id in self.rag_engine.indices:
                    vector_index = self.rag_engine.indices[corpus_id].get(self.default_index_type)
                    if vector_index and hasattr(vector_index, 'get_index'):
                        try:
                            index = vector_index.get_index()
                            if hasattr(index, 'vector_store'):
                                vector_store = index.vector_store
                                if hasattr(vector_store, 'faiss_index'):
                                    stats['vector_count'] = vector_store.faiss_index.ntotal
                                    stats['dimensions'] = vector_store.faiss_index.d
                        except Exception:
                            pass
                return {'success': True, 'data': stats}
            else:
                stats = {'total_corpora': len(self.rag_engine.indices), 'corpora': list(self.rag_engine.indices.keys()), 'embedding_model': self.rag_engine.config.embedding.model_name, 'vector_store_type': self.rag_engine.storage_handler.storageConfig.vectorConfig.vector_name if self.rag_engine.storage_handler.storageConfig.vectorConfig else None}
                return {'success': True, 'data': stats}
        except Exception as e:
            logger.error(f'Get stats failed: {str(e)}')
            return {'success': False, 'error': str(e)}

def list_corpora(self) -> Dict[str, Any]:
    """
        List all available corpora and their metadata.
        
        Returns:
            Dict[str, Any]: List of corpora with metadata
        """
    try:
        corpora = []
        for corpus_id, indices in self.rag_engine.indices.items():
            corpus_info = {'corpus_id': corpus_id, 'index_types': list(indices.keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
            corpora.append(corpus_info)
        return {'success': True, 'data': {'corpora': corpora, 'total': len(corpora)}}
    except Exception as e:
        logger.error(f'List corpora failed: {str(e)}')
        return {'success': False, 'error': str(e)}

def get_stats(self, corpus_id: Optional[str]=None) -> Dict[str, Any]:
    """
        Get statistics about the database or a specific corpus.
        
        Args:
            corpus_id (str, optional): Corpus ID to get stats for
            
        Returns:
            Dict[str, Any]: Database statistics
        """
    try:
        if corpus_id:
            corpus_id = corpus_id or self.default_corpus_id
            stats = {'corpus_id': corpus_id, 'exists': corpus_id in self.rag_engine.indices, 'index_types': list(self.rag_engine.indices.get(corpus_id, {}).keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
            if corpus_id in self.rag_engine.indices:
                vector_index = self.rag_engine.indices[corpus_id].get(self.default_index_type)
                if vector_index and hasattr(vector_index, 'get_index'):
                    try:
                        index = vector_index.get_index()
                        if hasattr(index, 'vector_store'):
                            vector_store = index.vector_store
                            if hasattr(vector_store, 'faiss_index'):
                                stats['vector_count'] = vector_store.faiss_index.ntotal
                                stats['dimensions'] = vector_store.faiss_index.d
                    except Exception:
                        pass
            return {'success': True, 'data': stats}
        else:
            stats = {'total_corpora': len(self.rag_engine.indices), 'corpora': list(self.rag_engine.indices.keys()), 'embedding_model': self.rag_engine.config.embedding.model_name, 'vector_store_type': self.rag_engine.storage_handler.storageConfig.vectorConfig.vector_name if self.rag_engine.storage_handler.storageConfig.vectorConfig else None}
            return {'success': True, 'data': stats}
    except Exception as e:
        logger.error(f'Get stats failed: {str(e)}')
        return {'success': False, 'error': str(e)}

class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL-specific connection management"""

    def __init__(self, connection_string: str, **kwargs):
        super().__init__(connection_string, **kwargs)
        self.conn = None

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(self.connection_string, **self.connection_params)
            self._is_connected = True
            logger.info('Successfully connected to PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Failed to connect to PostgreSQL: {str(e)}')
            self._is_connected = False
            return False

    def disconnect(self) -> bool:
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self._is_connected = False
                logger.info('Disconnected from PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting from PostgreSQL: {str(e)}')
            return False

    def test_connection(self) -> bool:
        try:
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute('SELECT 1;')
                return True
            return False
        except Exception:
            return False

def test_connection(self) -> bool:
    try:
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute('SELECT 1;')
            return True
        return False
    except Exception:
        return False

class PostgreSQLDatabase(DatabaseBase):
    """
    PostgreSQL database implementation with automatic initialization.
    Handles remote connections, existing local databases, and new local database creation.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, **kwargs):
        init_params = {'connection_string': connection_string, 'database_name': database_name}
        super().__init__(**init_params, **kwargs)
        self.local_path = Path(local_path) if local_path else None
        self.auto_save = auto_save
        self.connection_params = kwargs
        self.is_local_database = False
        self.conn = None
        self.cursor = None
        self.file_based_mode = False
        self.tables = {}
        if self._is_remote_connection():
            self._init_remote_database()
        elif self._is_existing_local_database():
            self._init_existing_local_database()
        else:
            self._init_new_local_database()

    def _is_remote_connection(self) -> bool:
        return self.connection_string and ('@' in self.connection_string or 'postgresql://' in self.connection_string)

    def _is_existing_local_database(self) -> bool:
        if not self.local_path:
            return False
        if not self.local_path.exists():
            return False
        db_info_file = self.local_path / 'db_info.json'
        return db_info_file.exists()

    def _init_remote_database(self):
        """Initialize remote PostgreSQL connection"""
        try:
            connection_params = self.connection_params.copy()
            connection_params.update({'connect_timeout': 5, 'options': '-c statement_timeout=5000'})
            self.conn = psycopg2.connect(self.connection_string, **connection_params)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if self.database_name:
                self.conn.set_isolation_level(0)
                self.cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (self.database_name,))
            self._is_initialized = True
            self.is_local_database = False
            self.file_based_mode = False
            logger.info(f'Connected to remote PostgreSQL: {self.database_name}')
        except Exception as e:
            logger.error(f'Failed to connect to remote PostgreSQL: {str(e)}')
            self._is_initialized = False
            logger.info('Falling back to local database mode')

    def _init_existing_local_database(self):
        """Initialize existing local file-based database"""
        try:
            if not self.database_name:
                self.database_name = self.local_path.name
            self._load_tables_from_files()
            self._is_initialized = True
            self.is_local_database = True
            self.file_based_mode = True
            logger.info(f'Loaded existing local file-based database from: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to load existing local database: {str(e)}')
            self._is_initialized = False
            logger.info('Falling back to new local database mode')
            self._init_new_local_database()

    def _init_new_local_database(self):
        """Initialize new local file-based database"""
        try:
            if not self.local_path:
                self.local_path = Path('./workplace/postgresql_local')
            self.local_path.mkdir(parents=True, exist_ok=True)
            if not self.database_name:
                self.database_name = self.local_path.name
            self._create_db_info_file()
            self._is_initialized = True
            self.is_local_database = True
            self.file_based_mode = True
            logger.info(f'Created new local file-based database at: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to create new local database: {str(e)}')
            self._is_initialized = False
            logger.info('Database initialization failed, but toolkit is still usable')

    def _create_db_info_file(self):
        """Create database info file"""
        try:
            db_info = {'database_name': self.database_name, 'created_at': time.time(), 'local_path': str(self.local_path.absolute()), 'auto_save': self.auto_save, 'version': '1.0', 'mode': 'file_based'}
            info_file = self.local_path / 'db_info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f'Failed to create db info file: {str(e)}')

    def _load_tables_from_files(self):
        """Load tables from JSON files"""
        try:
            for json_file in self.local_path.glob('*.json'):
                if json_file.name == 'db_info.json':
                    continue
                table_name = json_file.stem
                with open(json_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if not isinstance(loaded_data, list):
                        logger.warning(f'Table {table_name} file contains non-list data: {type(loaded_data)}, converting to empty list')
                        self.tables[table_name] = []
                    else:
                        self.tables[table_name] = loaded_data
        except Exception as e:
            logger.warning(f'Error loading tables from files: {str(e)}')

    def _save_table_to_file(self, table_name: str):
        """Save table data to JSON file"""
        try:
            if table_name in self.tables:
                table_file = self.local_path / f'{table_name}.json'
                with open(table_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tables[table_name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f'Error saving table {table_name}: {str(e)}')

    def _parse_sql_query(self, sql: str) -> Dict[str, Any]:
        """Enhanced SQL parser for file-based mode - now supports JOINs and complex queries"""
        sql = sql.strip()
        upper_sql = sql.upper()
        if upper_sql.startswith('CREATE TABLE'):
            match = re.search('CREATE TABLE (?:IF NOT EXISTS )?(\\w+) *\\((.*?)\\)', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                columns = match.group(2)
                col_defs = [c.strip() for c in columns.split(',') if c.strip()]
                col_names = [c.split()[0] for c in col_defs]
                return {'type': 'CREATE', 'table': table, 'columns': col_names}
        elif upper_sql.startswith('INSERT'):
            match = re.search('INSERT INTO (\\w+) *\\((.*?)\\) *VALUES', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                columns = [c.strip() for c in match.group(2).split(',')]
                values_match = re.search('VALUES\\s*(.*)', sql, re.IGNORECASE | re.DOTALL)
                if values_match:
                    values_str = values_match.group(1)
                    value_groups = re.findall('\\(([^)]+)\\)', values_str)
                    all_values = []
                    for group in value_groups:
                        values = [v.strip().strip('\'"') for v in group.split(',')]
                        all_values.append(values)
                    return {'type': 'INSERT', 'table': table, 'columns': columns, 'values': all_values}
        elif upper_sql.startswith('SELECT'):
            if 'JOIN' in upper_sql:
                match = re.search('SELECT (.*?) FROM (\\w+)(?:\\s+(\\w+))?\\s+(?:(\\w+)\\s+)?JOIN\\s+(\\w+)(?:\\s+(\\w+))?\\s+ON\\s+(.*?)(?: WHERE (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    columns = [c.strip() for c in match.group(1).split(',')]
                    table1 = match.group(2).lower()
                    alias1 = match.group(3)
                    join_type = match.group(4) or 'INNER'
                    table2 = match.group(5).lower()
                    alias2 = match.group(6)
                    join_condition = match.group(7)
                    where = match.group(8)
                    order_by = match.group(9)
                    limit = match.group(10)
                    return {'type': 'SELECT_JOIN', 'columns': columns, 'table1': table1, 'alias1': alias1, 'join_type': join_type, 'table2': table2, 'alias2': alias2, 'join_condition': join_condition, 'where': where, 'order_by': order_by, 'limit': limit}
                elif 'CROSS JOIN' in upper_sql:
                    match = re.search('SELECT (.*?) FROM (\\w+)(?:\\s+(\\w+))?\\s+CROSS\\s+JOIN\\s+(\\w+)(?:\\s+(\\w+))?(?: WHERE (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                    if match:
                        columns = [c.strip() for c in match.group(1).split(',')]
                        table1 = match.group(2).lower()
                        alias1 = match.group(3)
                        table2 = match.group(4).lower()
                        alias2 = match.group(5)
                        where = match.group(6)
                        order_by = match.group(7)
                        limit = match.group(8)
                        return {'type': 'SELECT_CROSS_JOIN', 'columns': columns, 'table1': table1, 'alias1': alias1, 'table2': table2, 'alias2': alias2, 'where': where, 'order_by': order_by, 'limit': limit}
            else:
                match = re.search('SELECT (.*?) FROM (\\w+)(?: WHERE (.*?))?(?: GROUP BY (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    columns = [c.strip() for c in match.group(1).split(',')]
                    table = match.group(2).lower()
                    where = match.group(3)
                    group_by = match.group(4)
                    order_by = match.group(5)
                    limit = match.group(6)
                    return {'type': 'SELECT', 'table': table, 'columns': columns, 'where': where, 'group_by': group_by, 'order_by': order_by, 'limit': limit}
        elif upper_sql.startswith('UPDATE'):
            match = re.search('UPDATE (\\w+) SET (.*?)(?: WHERE (.*?))?$', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                set_clause = match.group(2)
                where = match.group(3)
                return {'type': 'UPDATE', 'table': table, 'set': set_clause, 'where': where}
        elif upper_sql.startswith('DELETE'):
            match = re.search('DELETE FROM (\\w+)(?: WHERE (.*?))?', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                where = match.group(2)
                return {'type': 'DELETE', 'table': table, 'where': where}
        return {'type': 'UNKNOWN'}

    def _apply_where_filter(self, rows: List[Dict], where: str) -> List[Dict]:
        """Apply WHERE filter to rows"""
        if not where:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_where_filter: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_where_filter: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
        if m:
            col, op, val = (m.group(1), m.group(2), m.group(3))
            if op == '=':
                return [r for r in valid_rows if str(r.get(col, '')) == val]
            elif op == '>':
                try:
                    val_num = int(val)
                    return [r for r in valid_rows if int(r.get(col, 0)) > val_num]
                except ValueError:
                    pass
            elif op == '<':
                try:
                    val_num = int(val)
                    return [r for r in valid_rows if int(r.get(col, 0)) < val_num]
                except ValueError:
                    pass
        return valid_rows

    def _apply_column_selection(self, rows: List[Dict], columns: List[str]) -> List[Dict]:
        """Apply column selection to rows"""
        if columns == ['*']:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_column_selection: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_column_selection: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        filtered_rows = []
        for row in valid_rows:
            filtered_row = {}
            for col in columns:
                if col in row:
                    filtered_row[col] = row[col]
            filtered_rows.append(filtered_row)
        return filtered_rows

    def _apply_group_by(self, rows: List[Dict], group_by: str) -> List[Dict]:
        """Apply GROUP BY aggregation to rows"""
        if not group_by:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_group_by: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_group_by: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        group_col = group_by.strip()
        groups = {}
        for row in valid_rows:
            group_val = row.get(group_col, 'Unknown')
            if group_val not in groups:
                groups[group_val] = []
            groups[group_val].append(row)
        result = []
        for group_val, group_rows in groups.items():
            group_result = {group_col: group_val}
            group_result['employee_count'] = len(group_rows)
            salaries = [float(r.get('salary', 0)) for r in group_rows if r.get('salary') is not None]
            group_result['avg_salary'] = sum(salaries) / len(salaries) if salaries else 0
            group_result['max_salary'] = max(salaries) if salaries else 0
            result.append(group_result)
        return result

    def _execute_join_query(self, parsed: Dict) -> Dict[str, Any]:
        """Execute JOIN query in file-based mode"""
        try:
            table1 = parsed['table1']
            table2 = parsed['table2']
            columns = parsed['columns']
            join_condition = parsed['join_condition']
            where = parsed.get('where')
            rows1 = self.tables.get(table1, [])
            rows2 = self.tables.get(table2, [])
            if not isinstance(rows1, list):
                logger.warning(f'Table {table1} contains non-list data: {type(rows1)}')
                rows1 = []
            if not isinstance(rows2, list):
                logger.warning(f'Table {table2} contains non-list data: {type(rows2)}')
                rows2 = []
            join_match = re.match('(\\w+)\\.(\\w+)\\s*=\\s*(\\w+)\\.(\\w+)', join_condition)
            if not join_match:
                return {'error': 'Invalid join condition format'}
            col1, col2 = (join_match.group(2), join_match.group(4))
            result_rows = []
            for row1 in rows1:
                if not isinstance(row1, dict):
                    logger.warning(f'Skipping non-dict row1 in JOIN: {type(row1)}')
                    continue
                for row2 in rows2:
                    if not isinstance(row2, dict):
                        logger.warning(f'Skipping non-dict row2 in JOIN: {type(row2)}')
                        continue
                    if str(row1.get(col1, '')) == str(row2.get(col2, '')):
                        combined_row = {}
                        for col in columns:
                            if '.' in col:
                                table_alias, col_name = col.split('.', 1)
                                if table_alias == parsed.get('alias1') or table_alias == table1:
                                    combined_row[col] = row1.get(col_name, '')
                                elif table_alias == parsed.get('alias2') or table_alias == table2:
                                    combined_row[col] = row2.get(col_name, '')
                            elif col in row1:
                                combined_row[col] = row1[col]
                            elif col in row2:
                                combined_row[col] = row2[col]
                        result_rows.append(combined_row)
            if where:
                result_rows = self._apply_where_filter(result_rows, where)
            return result_rows
        except Exception as e:
            logger.error(f'Error executing JOIN query: {str(e)}')
            return {'error': str(e)}

    def _execute_cross_join_query(self, parsed: Dict) -> Dict[str, Any]:
        """Execute CROSS JOIN query in file-based mode"""
        try:
            table1 = parsed['table1']
            table2 = parsed['table2']
            columns = parsed['columns']
            where = parsed.get('where')
            rows1 = self.tables.get(table1, [])
            rows2 = self.tables.get(table2, [])
            if not isinstance(rows1, list):
                logger.warning(f'Table {table1} contains non-list data: {type(rows1)}')
                rows1 = []
            if not isinstance(rows2, list):
                logger.warning(f'Table {table2} contains non-list data: {type(rows2)}')
                rows2 = []
            result_rows = []
            for row1 in rows1:
                if not isinstance(row1, dict):
                    logger.warning(f'Skipping non-dict row1 in CROSS JOIN: {type(row1)}')
                    continue
                for row2 in rows2:
                    if not isinstance(row2, dict):
                        logger.warning(f'Skipping non-dict row2 in CROSS JOIN: {type(row2)}')
                        continue
                    combined_row = {}
                    for col in columns:
                        if '.' in col:
                            table_alias, col_name = col.split('.', 1)
                            if table_alias == parsed.get('alias1') or table_alias == table1:
                                combined_row[col] = row1.get(col_name, '')
                            elif table_alias == parsed.get('alias2') or table_alias == table2:
                                combined_row[col] = row2.get(col_name, '')
                        elif col in row1:
                            combined_row[col] = row1[col]
                        elif col in row2:
                            combined_row[col] = row2[col]
                    result_rows.append(combined_row)
            if where:
                result_rows = self._apply_where_filter(result_rows, where)
            return result_rows
        except Exception as e:
            logger.error(f'Error executing CROSS JOIN query: {str(e)}')
            return {'error': str(e)}

    def _get_database_type(self) -> DatabaseType:
        return DatabaseType.POSTGRESQL

    def connect(self) -> bool:
        return self._is_initialized

    def disconnect(self) -> bool:
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.cursor = None
                self._is_initialized = False
                logger.info('Disconnected from PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting: {str(e)}')
            return False

    def test_connection(self) -> bool:
        if self.file_based_mode:
            return self._is_initialized
        try:
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute('SELECT 1;')
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        if not self._is_initialized:
            return self.format_error_result('Database not initialized')
        if self.file_based_mode:
            return self._execute_file_based_query(query, query_type)
        if self.conn is None:
            return self.format_error_result('PostgreSQL server not available')
        start_time = time.time()
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if isinstance(query, str):
                    cur.execute(query)
                elif isinstance(query, dict):
                    sql = query.get('sql')
                    params = query.get('params', None)
                    if params:
                        cur.execute(sql, params)
                    else:
                        cur.execute(sql)
                elif isinstance(query, list):
                    for q in query:
                        if isinstance(q, str):
                            cur.execute(q)
                        elif isinstance(q, dict):
                            sql = q.get('sql')
                            params = q.get('params', None)
                            if params:
                                cur.execute(sql, params)
                            else:
                                cur.execute(sql)
                else:
                    return self.format_error_result('Unsupported query format', query_type)
                if cur.description:
                    result = cur.fetchall()
                else:
                    result = {'rowcount': cur.rowcount}
                self.conn.commit()
            execution_time = time.time() - start_time
            return self.format_query_result(result, query_type or QueryType.SELECT, execution_time=execution_time)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing PostgreSQL query: {str(e)}')
            try:
                if self.conn:
                    self.conn.rollback()
            except Exception as rollback_error:
                logger.warning(f'Error during rollback: {str(rollback_error)}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def _execute_file_based_query(self, query: Union[str, Dict, List], query_type: QueryType=None) -> Dict[str, Any]:
        """Execute query in file-based mode"""
        start_time = time.time()
        try:
            if isinstance(query, str):
                parsed = self._parse_sql_query(query)
                query_type = query_type or QueryType.SELECT
                if not isinstance(parsed, dict) or 'type' not in parsed:
                    logger.error(f'_execute_file_based_query: parsed is not a valid dict: {parsed}')
                    return self.format_error_result(f'Failed to parse SQL query: {query}', query_type)
                logger.debug(f'Executing {parsed['type']} query: {parsed}')
                if parsed['type'] == 'CREATE':
                    table_name = parsed['table']
                    columns = parsed.get('columns', ['id'])
                    if table_name not in self.tables:
                        self.tables[table_name] = []
                    if not isinstance(self.tables[table_name], list):
                        logger.warning(f'Reinitializing table {table_name} as list (was {type(self.tables[table_name])})')
                        self.tables[table_name] = []
                    self.tables[f'__schema__{table_name}'] = columns
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': 0}
                elif parsed['type'] == 'INSERT':
                    table_name = parsed['table']
                    columns = parsed['columns']
                    all_values = parsed['values']
                    if table_name not in self.tables:
                        self.tables[table_name] = []
                    if not isinstance(self.tables[table_name], list):
                        logger.warning(f'Reinitializing table {table_name} as list (was {type(self.tables[table_name])})')
                        self.tables[table_name] = []
                    valid_rows = 0
                    for values in all_values:
                        if len(values) != len(columns):
                            logger.warning(f'Skipping invalid row: {values} (expected {len(columns)} values, got {len(values)})')
                            continue
                        if not isinstance(values, list):
                            logger.warning(f'Skipping non-list values: {type(values)}')
                            continue
                        row = {col: val for col, val in zip(columns, values)}
                        row['id'] = len(self.tables[table_name]) + 1
                        self.tables[table_name].append(row)
                        valid_rows += 1
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': valid_rows}
                elif parsed['type'] == 'SELECT':
                    table_name = parsed['table']
                    columns = parsed['columns']
                    where = parsed.get('where')
                    group_by = parsed.get('group_by')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    logger.debug(f'SELECT query: table={table_name}, columns={columns}, where={where}, group_by={group_by}')
                    logger.debug(f'Rows from table: {type(rows)}, length={(len(rows) if isinstance(rows, list) else 'N/A')}')
                    if isinstance(rows, list) and rows:
                        logger.debug(f'First row type: {type(rows[0])}, content: {rows[0]}')
                    if where:
                        rows = self._apply_where_filter(rows, where)
                    if group_by:
                        result = self._apply_group_by(rows, group_by)
                    else:
                        result = {'data': self._apply_column_selection(rows, columns)}
                elif parsed['type'] == 'SELECT_JOIN':
                    logger.debug(f'Executing JOIN query: {parsed}')
                    join_result = self._execute_join_query(parsed)
                    if isinstance(join_result, dict) and 'error' in join_result:
                        result = {'error': join_result['error']}
                    else:
                        result = {'data': join_result}
                elif parsed['type'] == 'SELECT_CROSS_JOIN':
                    logger.debug(f'Executing CROSS JOIN query: {parsed}')
                    cross_join_result = self._execute_cross_join_query(parsed)
                    if isinstance(cross_join_result, dict) and 'error' in cross_join_result:
                        result = {'error': cross_join_result['error']}
                    else:
                        result = {'data': cross_join_result}
                elif parsed['type'] == 'UPDATE':
                    table_name = parsed['table']
                    set_clause = parsed['set']
                    where = parsed.get('where')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    updates = dict(re.findall("(\\w+) *= *'?([\\w@.\\- ]+)'?", set_clause))
                    count = 0
                    for r in rows:
                        if not isinstance(r, dict):
                            logger.warning(f'Skipping non-dict row in UPDATE: {type(r)}')
                            continue
                        match = True
                        if where:
                            m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
                            if m:
                                col, op, val = (m.group(1), m.group(2), m.group(3))
                                if op == '=' and str(r.get(col, '')) != val:
                                    match = False
                                elif op == '>' and int(r.get(col, 0)) <= int(val):
                                    match = False
                                elif op == '<' and int(r.get(col, 0)) >= int(val):
                                    match = False
                        if match:
                            r.update(updates)
                            count += 1
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': count}
                elif parsed['type'] == 'DELETE':
                    table_name = parsed['table']
                    where = parsed.get('where')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    if where:
                        m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
                        if m:
                            col, op, val = (m.group(1), m.group(2), m.group(3))
                            if op == '=':
                                new_rows = [r for r in rows if isinstance(r, dict) and str(r.get(col, '')) != val]
                            elif op == '>':
                                try:
                                    val_num = int(val)
                                    new_rows = [r for r in rows if isinstance(r, dict) and int(r.get(col, 0)) <= val_num]
                                except ValueError:
                                    new_rows = rows
                            else:
                                new_rows = rows
                            deleted_count = len(rows) - len(new_rows)
                            self.tables[table_name] = new_rows
                        else:
                            deleted_count = 0
                    else:
                        deleted_count = len(rows)
                        self.tables[table_name] = []
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': deleted_count}
                else:
                    return self.format_error_result('Unsupported query type in file-based mode', query_type)
                execution_time = time.time() - start_time
                return self.format_query_result(result, query_type, execution_time=execution_time)
            else:
                return self.format_error_result('Unsupported query format in file-based mode', query_type)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing file-based query: {str(e)}')
            logger.error(f'Query that caused error: {query}')
            logger.error(f'Query type: {query_type}')
            import traceback
            logger.error(f'Traceback: {traceback.format_exc()}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def get_database_info(self) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                info = {'database': self.database_name, 'user': 'file_based', 'table_count': len(self.tables), 'connection_string': 'file_based', 'is_connected': True, 'mode': 'file_based'}
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute('SELECT current_database() as database, current_user as user')
                    db_info = cur.fetchone()
                    cur.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'")
                    table_count = cur.fetchone()['table_count']
                info = {'database': db_info['database'], 'user': db_info['user'], 'table_count': table_count, 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def list_collections(self) -> List[str]:
        try:
            if self.file_based_mode:
                return list(self.tables.keys())
            if not self._is_initialized or self.conn is None:
                return []
            with self.conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = [row[0] for row in cur.fetchall()]
            return tables
        except Exception as e:
            logger.error(f'Error listing tables: {str(e)}')
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                if collection_name in self.tables:
                    row_count = len(self.tables[collection_name])
                    info = {'table_name': collection_name, 'row_count': row_count, 'columns': ['id']}
                else:
                    return self.format_error_result(f'Table {collection_name} not found')
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(f'SELECT COUNT(*) as row_count FROM {collection_name}')
                    row_count = cur.fetchone()['row_count']
                    cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                    columns = cur.fetchall()
                info = {'table_name': collection_name, 'row_count': row_count, 'columns': columns}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                if collection_name:
                    if collection_name in self.tables:
                        schema = {'id': 'integer'}
                        return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                    else:
                        return self.format_error_result(f'Table {collection_name} not found')
                else:
                    schemas = {}
                    for table_name in self.tables:
                        schemas[table_name] = {'id': 'integer'}
                    return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if collection_name:
                        cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                        columns = cur.fetchall()
                        schema = {col['column_name']: col['data_type'] for col in columns}
                        return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                    else:
                        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                        tables = [row[0] for row in cur.fetchall()]
                        schemas = {}
                        for table in tables:
                            cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (table,))
                            columns = cur.fetchall()
                            schemas[table] = {col['column_name']: col['data_type'] for col in columns}
                        return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_supported_query_types(self) -> List[QueryType]:
        return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP, QueryType.ALTER, QueryType.INDEX]

    def get_capabilities(self) -> Dict[str, Any]:
        base_capabilities = super().get_capabilities()
        base_capabilities.update({'supports_sql': True, 'supports_transactions': not self.file_based_mode, 'supports_indexing': not self.file_based_mode, 'schema_flexible': self.file_based_mode, 'file_based_mode': self.file_based_mode})
        return base_capabilities

def test_connection(self) -> bool:
    if self.file_based_mode:
        return self._is_initialized
    try:
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute('SELECT 1;')
            return True
        return False
    except Exception:
        return False

def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
    if not self._is_initialized:
        return self.format_error_result('Database not initialized')
    if self.file_based_mode:
        return self._execute_file_based_query(query, query_type)
    if self.conn is None:
        return self.format_error_result('PostgreSQL server not available')
    start_time = time.time()
    try:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if isinstance(query, str):
                cur.execute(query)
            elif isinstance(query, dict):
                sql = query.get('sql')
                params = query.get('params', None)
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
            elif isinstance(query, list):
                for q in query:
                    if isinstance(q, str):
                        cur.execute(q)
                    elif isinstance(q, dict):
                        sql = q.get('sql')
                        params = q.get('params', None)
                        if params:
                            cur.execute(sql, params)
                        else:
                            cur.execute(sql)
            else:
                return self.format_error_result('Unsupported query format', query_type)
            if cur.description:
                result = cur.fetchall()
            else:
                result = {'rowcount': cur.rowcount}
            self.conn.commit()
        execution_time = time.time() - start_time
        return self.format_query_result(result, query_type or QueryType.SELECT, execution_time=execution_time)
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f'Error executing PostgreSQL query: {str(e)}')
        try:
            if self.conn:
                self.conn.rollback()
        except Exception as rollback_error:
            logger.warning(f'Error during rollback: {str(rollback_error)}')
        return self.format_error_result(str(e), query_type, execution_time=execution_time)

def get_database_info(self) -> Dict[str, Any]:
    try:
        if not self._is_initialized:
            return self.format_error_result('Database not initialized')
        if self.file_based_mode:
            info = {'database': self.database_name, 'user': 'file_based', 'table_count': len(self.tables), 'connection_string': 'file_based', 'is_connected': True, 'mode': 'file_based'}
        else:
            if self.conn is None:
                return self.format_error_result('PostgreSQL server not available')
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT current_database() as database, current_user as user')
                db_info = cur.fetchone()
                cur.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cur.fetchone()['table_count']
            info = {'database': db_info['database'], 'user': db_info['user'], 'table_count': table_count, 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
        return self.format_query_result(info, QueryType.SELECT)
    except Exception as e:
        return self.format_error_result(str(e))

def list_collections(self) -> List[str]:
    try:
        if self.file_based_mode:
            return list(self.tables.keys())
        if not self._is_initialized or self.conn is None:
            return []
        with self.conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        logger.error(f'Error listing tables: {str(e)}')
        return []

def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
    try:
        if not self._is_initialized:
            return self.format_error_result('Database not initialized')
        if self.file_based_mode:
            if collection_name in self.tables:
                row_count = len(self.tables[collection_name])
                info = {'table_name': collection_name, 'row_count': row_count, 'columns': ['id']}
            else:
                return self.format_error_result(f'Table {collection_name} not found')
        else:
            if self.conn is None:
                return self.format_error_result('PostgreSQL server not available')
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f'SELECT COUNT(*) as row_count FROM {collection_name}')
                row_count = cur.fetchone()['row_count']
                cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                columns = cur.fetchall()
            info = {'table_name': collection_name, 'row_count': row_count, 'columns': columns}
        return self.format_query_result(info, QueryType.SELECT)
    except Exception as e:
        return self.format_error_result(str(e))

def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
    try:
        if not self._is_initialized:
            return self.format_error_result('Database not initialized')
        if self.file_based_mode:
            if collection_name:
                if collection_name in self.tables:
                    schema = {'id': 'integer'}
                    return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                else:
                    return self.format_error_result(f'Table {collection_name} not found')
            else:
                schemas = {}
                for table_name in self.tables:
                    schemas[table_name] = {'id': 'integer'}
                return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        else:
            if self.conn is None:
                return self.format_error_result('PostgreSQL server not available')
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if collection_name:
                    cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                    columns = cur.fetchall()
                    schema = {col['column_name']: col['data_type'] for col in columns}
                    return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                else:
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    tables = [row[0] for row in cur.fetchall()]
                    schemas = {}
                    for table in tables:
                        cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (table,))
                        columns = cur.fetchall()
                        schemas[table] = {col['column_name']: col['data_type'] for col in columns}
                    return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
    except Exception as e:
        return self.format_error_result(str(e))

class MongoDBDatabase(DatabaseBase):
    """
    MongoDB database implementation with automatic initialization.
    Handles remote connections, existing local databases, and new local database creation.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, read_only: bool=False, **kwargs):
        """
        Initialize MongoDB database with automatic detection and setup.
        
        Args:
            connection_string: MongoDB connection string (for remote)
            database_name: Name of the database
            local_path: Path for local file-based database
            auto_save: Automatically save changes to local files
            read_only: If True, only read operations are allowed (no insert, update, delete)
            **kwargs: Additional connection parameters
        """
        init_params = {'connection_string': connection_string, 'database_name': database_name}
        super().__init__(**init_params, **kwargs)
        self.local_path = Path(local_path) if local_path else None
        self.auto_save = auto_save
        self.read_only = read_only
        self.connection_params = kwargs
        self.is_local_database = False
        self.client = None
        self.database = None
        if self._is_remote_connection():
            self._init_remote_database()
        elif self._is_existing_local_database():
            self._init_existing_local_database()
        else:
            self._init_new_local_database()

    def _is_remote_connection(self) -> bool:
        """Check if this is a remote MongoDB connection"""
        return self.connection_string and (self.connection_string.startswith(('mongodb://', 'mongodb+srv://')) or 'localhost' in self.connection_string or '127.0.0.1' in self.connection_string)

    def _is_existing_local_database(self) -> bool:
        """Check if there's an existing local database"""
        if not self.local_path:
            return False
        if not self.local_path.exists():
            return False
        json_files = list(self.local_path.glob('*.json'))
        db_info_file = self.local_path / 'db_info.json'
        return len(json_files) > 0 or db_info_file.exists()

    def _init_remote_database(self):
        """Initialize remote MongoDB connection"""
        try:
            self.client = MongoClient(self.connection_string, **self.connection_params)
            self.client.admin.command('ping')
            if self.database_name:
                self.database = self.client[self.database_name]
            self._is_initialized = True
            self.is_local_database = False
            logger.info(f'Connected to remote MongoDB: {self.database_name}')
        except Exception as e:
            logger.error(f'Failed to connect to remote MongoDB: {str(e)}')
            self._is_initialized = False
            raise

    def _init_existing_local_database(self):
        """Initialize existing local database"""
        try:
            self.connection_string = 'mongodb://localhost:27017'
            self.client = MongoClient(self.connection_string, **self.connection_params)
            if not self.database_name:
                self.database_name = self.local_path.name
            self.database = self.client[self.database_name]
            self._load_local_collections()
            self._is_initialized = True
            self.is_local_database = True
            logger.info(f'Loaded existing local database from: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to load existing local database: {str(e)}')
            self._is_initialized = False
            raise

    def _init_new_local_database(self):
        """Initialize new local database"""
        try:
            if not self.local_path:
                self.local_path = Path('./mongodb_local')
            self.local_path.mkdir(parents=True, exist_ok=True)
            self.connection_string = 'mongodb://localhost:27017'
            self.client = MongoClient(self.connection_string, **self.connection_params)
            if not self.database_name:
                self.database_name = self.local_path.name
            self.database = self.client[self.database_name]
            self._create_db_info_file()
            self._is_initialized = True
            self.is_local_database = True
            logger.info(f'Created new local database at: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to create new local database: {str(e)}')
            self._is_initialized = False
            raise

    def _load_local_collections(self):
        """Load collections from local JSON files"""
        if not self.local_path or not self.local_path.exists():
            return
        json_files = [f for f in self.local_path.glob('*.json') if f.name != 'db_info.json']
        for json_file in json_files:
            collection_name = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    documents = [data]
                elif isinstance(data, list):
                    documents = data
                else:
                    continue
                if documents:
                    cleaned_documents = []
                    for doc in documents:
                        cleaned_doc = self._clean_document_for_insert(doc)
                        cleaned_documents.append(cleaned_doc)
                    collection = self.database[collection_name]
                    collection.drop()
                    if cleaned_documents:
                        collection.insert_many(cleaned_documents)
                        logger.info(f"Loaded {len(cleaned_documents)} documents into '{collection_name}'")
            except Exception as e:
                logger.warning(f'Failed to load collection from {json_file}: {str(e)}')

    def _clean_document_for_insert(self, doc: Dict) -> Dict:
        """Clean document by removing problematic MongoDB-specific fields"""
        if isinstance(doc, dict):
            cleaned = {}
            for key, value in doc.items():
                if key == '_id' and isinstance(value, dict) and ('$oid' in value):
                    continue
                elif isinstance(value, dict):
                    cleaned[key] = self._clean_document_for_insert(value)
                elif isinstance(value, list):
                    cleaned[key] = [self._clean_document_for_insert(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = value
            return cleaned
        return doc

    def _create_db_info_file(self):
        """Create database info file for new local database"""
        try:
            db_info = {'database_name': self.database_name, 'created_at': time.time(), 'local_path': str(self.local_path.absolute()), 'auto_save': self.auto_save, 'version': '1.0'}
            info_file = self.local_path / 'db_info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f'Failed to create db info file: {str(e)}')

    def _save_collection_to_file(self, collection_name: str):
        """Save collection to local JSON file"""
        if not self.is_local_database or not self.local_path:
            return
        try:
            collection = self.database[collection_name]
            documents = list(collection.find())
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            file_path = self.local_path / f'{collection_name}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved collection '{collection_name}' to {file_path}")
        except Exception as e:
            logger.warning(f"Failed to save collection '{collection_name}': {str(e)}")

    def _auto_save_if_needed(self, collection_name: str):
        """Auto-save collection if local database and auto_save is enabled"""
        if self.is_local_database and self.auto_save:
            self._save_collection_to_file(collection_name)

    def _get_database_type(self) -> DatabaseType:
        return DatabaseType.MONGODB

    def connect(self) -> bool:
        """Connection is already established in __init__"""
        return self._is_initialized

    def disconnect(self) -> bool:
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.database = None
                self._is_initialized = False
                logger.info('Disconnected from MongoDB')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting: {str(e)}')
            return False

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, collection_name: str=None, **kwargs) -> Dict[str, Any]:
        """Execute a query on MongoDB with automatic result handling"""
        if not self._is_initialized or self.database is None:
            return self.format_error_result('Database not connected')
        if not collection_name:
            return self.format_error_result('Collection name is required')
        start_time = time.time()
        try:
            collection = self.database[collection_name]
            if not query_type:
                query_type = self._infer_query_type(query)
            if self.read_only and query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP]:
                return self.format_error_result(f"Write operation '{query_type.value}' is not allowed in read-only mode. Only SELECT and AGGREGATE operations are permitted.", query_type, execution_time=time.time() - start_time)
            if query_type == QueryType.SELECT:
                result = self._execute_find(collection, query, **kwargs)
            elif query_type == QueryType.INSERT:
                result = self._execute_insert(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.UPDATE:
                result = self._execute_update(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.DELETE:
                result = self._execute_delete(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.AGGREGATE:
                result = self._execute_aggregate(collection, query, **kwargs)
            else:
                return self.format_error_result(f'Unsupported query type: {query_type}')
            execution_time = time.time() - start_time
            if isinstance(result, dict):
                result['execution_time'] = execution_time
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing MongoDB query: {str(e)}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def _infer_query_type(self, query: Union[str, Dict, List]) -> QueryType:
        """Infer query type from the query structure"""
        if isinstance(query, list):
            return QueryType.AGGREGATE
        elif isinstance(query, dict):
            if self.read_only:
                if 'insert' in query or 'insertOne' in query or 'insertMany' in query:
                    return QueryType.SELECT
                elif 'update' in query or 'updateOne' in query or 'updateMany' in query:
                    return QueryType.SELECT
                elif 'delete' in query or 'deleteOne' in query or 'deleteMany' in query:
                    return QueryType.SELECT
                elif 'create' in query or 'createCollection' in query:
                    return QueryType.SELECT
                elif 'drop' in query or 'dropCollection' in query:
                    return QueryType.SELECT
                else:
                    return QueryType.SELECT
            elif 'insert' in query or 'insertOne' in query or 'insertMany' in query:
                return QueryType.INSERT
            elif 'update' in query or 'updateOne' in query or 'updateMany' in query:
                return QueryType.UPDATE
            elif 'delete' in query or 'deleteOne' in query or 'deleteMany' in query:
                return QueryType.DELETE
            elif 'create' in query or 'createCollection' in query:
                return QueryType.CREATE
            elif 'drop' in query or 'dropCollection' in query:
                return QueryType.DROP
            else:
                return QueryType.SELECT
        elif isinstance(query, str):
            query_lower = query.lower().strip()
            if self.read_only:
                return QueryType.SELECT
            elif query_lower.startswith(('insert', 'create')):
                return QueryType.INSERT
            elif query_lower.startswith('update'):
                return QueryType.UPDATE
            elif query_lower.startswith('delete'):
                return QueryType.DELETE
            elif query_lower.startswith('drop'):
                return QueryType.DROP
            else:
                return QueryType.SELECT
        return QueryType.SELECT

    def _execute_find(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute find query"""
        try:
            if isinstance(query, str):
                if '=' in query:
                    field, value = query.split('=', 1)
                    query = {field.strip(): value.strip()}
                else:
                    query = {}
            filter_query = query.get('filter', query)
            projection = query.get('projection', {})
            sort = query.get('sort', None)
            limit = query.get('limit', kwargs.get('limit', 0))
            skip = query.get('skip', kwargs.get('skip', 0))
            cursor = collection.find(filter_query, projection)
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            results = []
            for doc in cursor:
                doc = json.loads(json_util.dumps(doc))
                results.append(doc)
            return self.format_query_result(results, QueryType.SELECT, collection_name=collection.name, filter_applied=filter_query)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.SELECT)

    def _execute_insert(self, collection, query: Union[Dict, List], **kwargs) -> Dict[str, Any]:
        """Execute insert operation"""
        try:
            if isinstance(query, dict):
                if 'document' in query:
                    document = query['document']
                else:
                    document = query
                result = collection.insert_one(document)
                return self.format_query_result({'inserted_id': str(result.inserted_id)}, QueryType.INSERT, collection_name=collection.name)
            elif isinstance(query, list):
                if all((isinstance(item, dict) for item in query)):
                    documents = query
                else:
                    documents = [{'documents': query}]
                result = collection.insert_many(documents)
                return self.format_query_result({'inserted_ids': [str(id) for id in result.inserted_ids]}, QueryType.INSERT, collection_name=collection.name)
            else:
                return self.format_error_result('Invalid insert query format', QueryType.INSERT)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.INSERT)

    def _execute_update(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute update operation"""
        try:
            filter_query = query.get('filter', {})
            update_query = query.get('update', {})
            upsert = query.get('upsert', False)
            multi = query.get('multi', False)
            if multi:
                result = collection.update_many(filter_query, update_query, upsert=upsert)
            else:
                result = collection.update_one(filter_query, update_query, upsert=upsert)
            return self.format_query_result({'matched_count': result.matched_count, 'modified_count': result.modified_count, 'upserted_id': str(result.upserted_id) if result.upserted_id else None}, QueryType.UPDATE, collection_name=collection.name)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.UPDATE)

    def _execute_delete(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute delete operation"""
        try:
            filter_query = query.get('filter', query)
            multi = query.get('multi', False)
            if multi:
                result = collection.delete_many(filter_query)
            else:
                result = collection.delete_one(filter_query)
            return self.format_query_result({'deleted_count': result.deleted_count}, QueryType.DELETE, collection_name=collection.name)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.DELETE)

    def _execute_aggregate(self, collection, pipeline: List, **kwargs) -> Dict[str, Any]:
        """Execute aggregation pipeline"""
        try:
            cursor = collection.aggregate(pipeline)
            results = []
            for doc in cursor:
                doc = json.loads(json_util.dumps(doc))
                results.append(doc)
            return self.format_query_result(results, QueryType.AGGREGATE, collection_name=collection.name, pipeline_stages=len(pipeline))
        except Exception as e:
            return self.format_error_result(str(e), QueryType.AGGREGATE)

    def get_database_info(self) -> Dict[str, Any]:
        """Get MongoDB database information"""
        try:
            if not self._is_initialized or self.database is None:
                return self.format_error_result('Database not connected')
            stats = self.database.command('dbStats')
            server_info = self.client.server_info()
            info = {'database_name': self.database_name, 'collections': stats.get('collections', 0), 'data_size': stats.get('dataSize', 0), 'storage_size': stats.get('storageSize', 0), 'indexes': stats.get('indexes', 0), 'index_size': stats.get('indexSize', 0), 'server_version': server_info.get('version', 'Unknown'), 'server_type': server_info.get('type', 'Unknown'), 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        try:
            if not self._is_initialized or self.database is None:
                return []
            return self.database.list_collection_names()
        except Exception as e:
            logger.error(f'Error listing collections: {str(e)}')
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection"""
        try:
            if not self._is_initialized or not self.database:
                return self.format_error_result('Database not connected')
            collection = self.database[collection_name]
            stats = self.database.command('collStats', collection_name)
            indexes = list(collection.list_indexes())
            sample_docs = list(collection.find().limit(5))
            info = {'collection_name': collection_name, 'document_count': stats.get('count', 0), 'data_size': stats.get('size', 0), 'storage_size': stats.get('storageSize', 0), 'index_count': stats.get('nindexes', 0), 'indexes': [{'name': idx['name'], 'keys': idx['key']} for idx in indexes], 'sample_documents': sample_docs[:2]}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        """Get schema information for database or specific collection"""
        try:
            if not self._is_initialized or not self.database:
                return self.format_error_result('Database not connected')
            if collection_name:
                collection = self.database[collection_name]
                sample_docs = list(collection.find().limit(100))
                if not sample_docs:
                    return self.format_query_result({'collection_name': collection_name, 'schema': {}, 'message': 'No documents found'}, QueryType.SELECT)
                schema = self._infer_schema_from_documents(sample_docs)
                return self.format_query_result({'collection_name': collection_name, 'schema': schema, 'sample_count': len(sample_docs)}, QueryType.SELECT)
            else:
                collections = self.list_collections()
                schemas = {}
                for coll_name in collections[:10]:
                    coll_schema = self.get_schema(coll_name)
                    if coll_schema.get('success'):
                        schemas[coll_name] = coll_schema.get('data', {}).get('schema', {})
                return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def _infer_schema_from_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Infer schema from a list of documents"""
        if not documents:
            return {}
        schema = {}
        for doc in documents:
            self._update_schema_from_document(schema, doc)
        return schema

    def _update_schema_from_document(self, schema: Dict, document: Dict, path: str=''):
        """Recursively update schema from a document"""
        for key, value in document.items():
            current_path = f'{path}.{key}' if path else key
            if isinstance(value, dict):
                if current_path not in schema:
                    schema[current_path] = {'type': 'object', 'fields': {}}
                self._update_schema_from_document(schema[current_path]['fields'], value, current_path)
            elif isinstance(value, list):
                if current_path not in schema:
                    schema[current_path] = {'type': 'array', 'element_types': set()}
                for item in value[:3]:
                    if isinstance(item, dict):
                        schema[current_path]['element_types'].add('object')
                    else:
                        schema[current_path]['element_types'].add(type(item).__name__)
                schema[current_path]['element_types'] = list(schema[current_path]['element_types'])
            elif current_path not in schema:
                schema[current_path] = {'type': type(value).__name__}
            elif schema[current_path]['type'] != type(value).__name__:
                schema[current_path]['type'] = 'mixed'

    def get_supported_query_types(self) -> List[QueryType]:
        """Get MongoDB-specific supported query types"""
        if self.read_only:
            return [QueryType.SELECT, QueryType.AGGREGATE]
        else:
            return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP, QueryType.AGGREGATE, QueryType.INDEX]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get MongoDB-specific capabilities"""
        base_capabilities = super().get_capabilities()
        base_capabilities.update({'supports_aggregation': True, 'supports_full_text_search': True, 'supports_geospatial_queries': True, 'supports_change_streams': True, 'supports_transactions': True, 'supports_indexing': True, 'document_oriented': True, 'schema_flexible': True, 'read_only': self.read_only, 'write_operations_allowed': not self.read_only})
        return base_capabilities

def _save_collection_to_file(self, collection_name: str):
    """Save collection to local JSON file"""
    if not self.is_local_database or not self.local_path:
        return
    try:
        collection = self.database[collection_name]
        documents = list(collection.find())
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        file_path = self.local_path / f'{collection_name}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False, default=str)
        logger.debug(f"Saved collection '{collection_name}' to {file_path}")
    except Exception as e:
        logger.warning(f"Failed to save collection '{collection_name}': {str(e)}")

def _execute_find(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
    """Execute find query"""
    try:
        if isinstance(query, str):
            if '=' in query:
                field, value = query.split('=', 1)
                query = {field.strip(): value.strip()}
            else:
                query = {}
        filter_query = query.get('filter', query)
        projection = query.get('projection', {})
        sort = query.get('sort', None)
        limit = query.get('limit', kwargs.get('limit', 0))
        skip = query.get('skip', kwargs.get('skip', 0))
        cursor = collection.find(filter_query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        results = []
        for doc in cursor:
            doc = json.loads(json_util.dumps(doc))
            results.append(doc)
        return self.format_query_result(results, QueryType.SELECT, collection_name=collection.name, filter_applied=filter_query)
    except Exception as e:
        return self.format_error_result(str(e), QueryType.SELECT)

def _execute_insert(self, collection, query: Union[Dict, List], **kwargs) -> Dict[str, Any]:
    """Execute insert operation"""
    try:
        if isinstance(query, dict):
            if 'document' in query:
                document = query['document']
            else:
                document = query
            result = collection.insert_one(document)
            return self.format_query_result({'inserted_id': str(result.inserted_id)}, QueryType.INSERT, collection_name=collection.name)
        elif isinstance(query, list):
            if all((isinstance(item, dict) for item in query)):
                documents = query
            else:
                documents = [{'documents': query}]
            result = collection.insert_many(documents)
            return self.format_query_result({'inserted_ids': [str(id) for id in result.inserted_ids]}, QueryType.INSERT, collection_name=collection.name)
        else:
            return self.format_error_result('Invalid insert query format', QueryType.INSERT)
    except Exception as e:
        return self.format_error_result(str(e), QueryType.INSERT)

def _execute_update(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
    """Execute update operation"""
    try:
        filter_query = query.get('filter', {})
        update_query = query.get('update', {})
        upsert = query.get('upsert', False)
        multi = query.get('multi', False)
        if multi:
            result = collection.update_many(filter_query, update_query, upsert=upsert)
        else:
            result = collection.update_one(filter_query, update_query, upsert=upsert)
        return self.format_query_result({'matched_count': result.matched_count, 'modified_count': result.modified_count, 'upserted_id': str(result.upserted_id) if result.upserted_id else None}, QueryType.UPDATE, collection_name=collection.name)
    except Exception as e:
        return self.format_error_result(str(e), QueryType.UPDATE)

def _execute_delete(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
    """Execute delete operation"""
    try:
        filter_query = query.get('filter', query)
        multi = query.get('multi', False)
        if multi:
            result = collection.delete_many(filter_query)
        else:
            result = collection.delete_one(filter_query)
        return self.format_query_result({'deleted_count': result.deleted_count}, QueryType.DELETE, collection_name=collection.name)
    except Exception as e:
        return self.format_error_result(str(e), QueryType.DELETE)

def _execute_aggregate(self, collection, pipeline: List, **kwargs) -> Dict[str, Any]:
    """Execute aggregation pipeline"""
    try:
        cursor = collection.aggregate(pipeline)
        results = []
        for doc in cursor:
            doc = json.loads(json_util.dumps(doc))
            results.append(doc)
        return self.format_query_result(results, QueryType.AGGREGATE, collection_name=collection.name, pipeline_stages=len(pipeline))
    except Exception as e:
        return self.format_error_result(str(e), QueryType.AGGREGATE)

def get_database_info(self) -> Dict[str, Any]:
    """Get MongoDB database information"""
    try:
        if not self._is_initialized or self.database is None:
            return self.format_error_result('Database not connected')
        stats = self.database.command('dbStats')
        server_info = self.client.server_info()
        info = {'database_name': self.database_name, 'collections': stats.get('collections', 0), 'data_size': stats.get('dataSize', 0), 'storage_size': stats.get('storageSize', 0), 'indexes': stats.get('indexes', 0), 'index_size': stats.get('indexSize', 0), 'server_version': server_info.get('version', 'Unknown'), 'server_type': server_info.get('type', 'Unknown'), 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
        return self.format_query_result(info, QueryType.SELECT)
    except Exception as e:
        return self.format_error_result(str(e))

def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
    """Get information about a specific collection"""
    try:
        if not self._is_initialized or not self.database:
            return self.format_error_result('Database not connected')
        collection = self.database[collection_name]
        stats = self.database.command('collStats', collection_name)
        indexes = list(collection.list_indexes())
        sample_docs = list(collection.find().limit(5))
        info = {'collection_name': collection_name, 'document_count': stats.get('count', 0), 'data_size': stats.get('size', 0), 'storage_size': stats.get('storageSize', 0), 'index_count': stats.get('nindexes', 0), 'indexes': [{'name': idx['name'], 'keys': idx['key']} for idx in indexes], 'sample_documents': sample_docs[:2]}
        return self.format_query_result(info, QueryType.SELECT)
    except Exception as e:
        return self.format_error_result(str(e))

def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
    """Get schema information for database or specific collection"""
    try:
        if not self._is_initialized or not self.database:
            return self.format_error_result('Database not connected')
        if collection_name:
            collection = self.database[collection_name]
            sample_docs = list(collection.find().limit(100))
            if not sample_docs:
                return self.format_query_result({'collection_name': collection_name, 'schema': {}, 'message': 'No documents found'}, QueryType.SELECT)
            schema = self._infer_schema_from_documents(sample_docs)
            return self.format_query_result({'collection_name': collection_name, 'schema': schema, 'sample_count': len(sample_docs)}, QueryType.SELECT)
        else:
            collections = self.list_collections()
            schemas = {}
            for coll_name in collections[:10]:
                coll_schema = self.get_schema(coll_name)
                if coll_schema.get('success'):
                    schemas[coll_name] = coll_schema.get('data', {}).get('schema', {})
            return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
    except Exception as e:
        return self.format_error_result(str(e))

class SearchGoogleFree(SearchBase):
    """
    Free Google Search tool that doesn't require API keys.
    """

    def __init__(self, name: str='GoogleFreeSearch', num_search_pages: Optional[int]=5, max_content_words: Optional[int]=None, **kwargs):
        """
        Initialize the Free Google Search tool.
        
        Args:
            name (str): Name of the tool
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, num_search_pages=num_search_pages, max_content_words=max_content_words, **kwargs)

    def search(self, query: str, num_search_pages: int=None, max_content_words: int=None) -> Dict[str, Any]:
        """
        Searches Google for the given query and retrieves content from multiple pages.

        Args:
            query (str): The search query.
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content, None means no limit

        Returns:
            Dict[str, Any]: Contains a list of search results and optional error message.
        """
        num_search_pages = num_search_pages or self.num_search_pages
        max_content_words = max_content_words or self.max_content_words
        results = []
        try:
            logger.info(f'Searching Google (Free) for: {query}, num_results={num_search_pages}, max_content_words={max_content_words}')
            search_results = list(google_f_search(query, num_results=num_search_pages))
            if not search_results:
                return {'results': [], 'error': 'No search results found.'}
            logger.info(f'Found {len(search_results)} search results')
            for url in search_results:
                try:
                    title, content = self._scrape_page(url)
                    if content:
                        display_content = self._truncate_content(content, max_content_words)
                        results.append({'title': title, 'content': display_content, 'url': url})
                except Exception as e:
                    logger.warning(f'Error processing URL {url}: {str(e)}')
                    continue
            return {'results': results, 'error': None}
        except Exception as e:
            logger.error(f'Error in free Google search: {str(e)}')
            return {'results': [], 'error': str(e)}

def search(self, query: str, num_search_pages: int=None, max_content_words: int=None) -> Dict[str, Any]:
    """
        Searches Google for the given query and retrieves content from multiple pages.

        Args:
            query (str): The search query.
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content, None means no limit

        Returns:
            Dict[str, Any]: Contains a list of search results and optional error message.
        """
    num_search_pages = num_search_pages or self.num_search_pages
    max_content_words = max_content_words or self.max_content_words
    results = []
    try:
        logger.info(f'Searching Google (Free) for: {query}, num_results={num_search_pages}, max_content_words={max_content_words}')
        search_results = list(google_f_search(query, num_results=num_search_pages))
        if not search_results:
            return {'results': [], 'error': 'No search results found.'}
        logger.info(f'Found {len(search_results)} search results')
        for url in search_results:
            try:
                title, content = self._scrape_page(url)
                if content:
                    display_content = self._truncate_content(content, max_content_words)
                    results.append({'title': title, 'content': display_content, 'url': url})
            except Exception as e:
                logger.warning(f'Error processing URL {url}: {str(e)}')
                continue
        return {'results': results, 'error': None}
    except Exception as e:
        logger.error(f'Error in free Google search: {str(e)}')
        return {'results': [], 'error': str(e)}

class FileStorageHandler(StorageBase):
    """
    Reference implementation showing all available _raw_xxx methods.
    This class serves as a template for developers creating new storage handlers.
    Concrete handlers only need to implement the _raw_xxx methods they need.
    """

    def __init__(self, base_path: str='.', **kwargs):
        """
        Initialize the storage handler.
        
        Args:
            base_path (str): Base directory for storage operations (default: current directory)
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(base_path=base_path, **kwargs)

    def create(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        return super().save(file_path, content, **kwargs)

    def read(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return super().read(file_path, **kwargs)

    def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        return super().list(path, max_depth, include_hidden)

    def delete(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return super().delete(file_path, **kwargs)

    def move(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return super().move(source, destination, **kwargs)

    def copy(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return super().copy(source, destination, **kwargs)

    def create_directory(self, path: str, **kwargs) -> Dict[str, Any]:
        return super().create_directory(path, **kwargs)

    @abstractmethod
    def _initialize_storage(self):
        """Initialize storage - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _delete_raw(self, path: str) -> bool:
        """Delete file or directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _exists_raw(self, path: str) -> bool:
        """Check if path exists - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _create_directory_raw(self, path: str) -> bool:
        """Create directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _list_raw(self, path: str=None, **kwargs) -> List[Dict[str, Any]]:
        """List files and directories - must be implemented by subclasses"""
        pass

    def create_file(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        return self.save(file_path, content, **kwargs)

    def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return self.read(file_path, **kwargs)

    def list_files(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        return self.list(path, max_depth, include_hidden)

    def delete_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return self.delete(file_path, **kwargs)

    def move_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return self.move(source, destination, **kwargs)

    def copy_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return self.copy(source, destination, **kwargs)

def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
    return super().list(path, max_depth, include_hidden)

def list_files(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
    return self.list(path, max_depth, include_hidden)

class SupabaseStorageHandler(FileStorageHandler):
    """
    Supabase remote storage implementation.
    Provides file operations via Supabase Storage API with environment-based configuration.
    """

    def __init__(self, bucket_name: str=None, base_path: str='/', **kwargs):
        """
        Initialize Supabase storage handler.
        
        Args:
            bucket_name: Supabase storage bucket name (default: from environment or "default")
            base_path: Base path for storage operations (default: "/")
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(base_path=base_path, **kwargs)
        self.bucket_name = bucket_name or os.getenv('SUPABASE_BUCKET_STORAGE') or 'default'
        self.supabase_url = os.getenv('SUPABASE_URL_STORAGE')
        self.supabase_key = os.getenv('SUPABASE_KEY_STORAGE')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError('Supabase configuration not found in environment variables. Please set SUPABASE_URL/SUPABASE_KEY environment variables.')
        try:
            from supabase import create_client, Client
            logger.info(f'Creating Supabase client with URL: {self.supabase_url[:30]}...')
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info(f'Successfully initialized Supabase client for bucket: {bucket_name}')
        except ImportError:
            raise ImportError('Supabase Python client not installed. Please install it with: pip install supabase')
        except Exception as e:
            logger.error(f'Failed to initialize Supabase client: {str(e)}')
            raise Exception(f'Failed to initialize Supabase client: {str(e)}')
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize remote storage - verify bucket exists and is accessible"""
        if not hasattr(self, 'bucket_name') or not hasattr(self, 'supabase'):
            return
        try:
            logger.info(f'Testing bucket access for: {self.bucket_name}')
            self.supabase.storage.from_(self.bucket_name).list()
            logger.info(f'Successfully connected to Supabase bucket: {self.bucket_name}')
        except Exception as e:
            logger.warning(f'Could not verify bucket access: {str(e)}')

    def translate_in(self, file_path: str) -> str:
        """Resolve file path for remote storage"""
        if self.base_path == '/':
            return file_path.lstrip('/')
        else:
            return super().translate_in(file_path)

    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content from Supabase Storage"""
        try:
            file_path = path.lstrip('/')
            response = self.supabase.storage.from_(self.bucket_name).download(file_path)
            if isinstance(response, bytes):
                return response
            else:
                return bytes(response) if response else b''
        except Exception as e:
            logger.error(f'Error reading file {path} from Supabase: {str(e)}')
            raise

    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content to Supabase Storage with smart insert/update logic"""
        try:
            file_path = path.lstrip('/')
            file_exists = self._exists_raw(file_path)
            if file_exists:
                logger.info(f'File {file_path} exists, using update method')
                response = self.supabase.storage.from_(self.bucket_name).update(path=file_path, file=content, file_options={'content-type': kwargs.get('content_type', 'application/octet-stream'), 'upsert': 'true'})
            else:
                logger.info(f"File {file_path} doesn't exist, using upload method")
                response = self.supabase.storage.from_(self.bucket_name).upload(path=file_path, file=content, file_options={'content-type': kwargs.get('content_type', 'application/octet-stream')})
            if response and (not isinstance(response, dict) or response.get('error') is None):
                operation = 'updated' if file_exists else 'uploaded'
                logger.info(f'Successfully {operation} file to Supabase: {file_path}')
                return True
            else:
                logger.error(f'Operation failed: {response}')
                return False
        except Exception as e:
            logger.error(f'Error writing file {path} to Supabase: {str(e)}')
            return False

    def _delete_raw(self, path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            file_path = path.lstrip('/')
            response = self.supabase.storage.from_(self.bucket_name).remove([file_path])
            if response is not None:
                if isinstance(response, list):
                    logger.info(f'Successfully deleted file from Supabase: {file_path}')
                    return True
                elif isinstance(response, dict) and response.get('error') is None:
                    logger.info(f'Successfully deleted file from Supabase: {file_path}')
                    return True
                else:
                    logger.error(f'Deletion failed: {response}')
                    return False
            else:
                logger.error(f'Deletion failed: {response}')
                return False
        except Exception as e:
            logger.error(f'Error deleting {path} from Supabase: {str(e)}')
            return False

    def _list_raw(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> List[Dict[str, Any]]:
        """List files in Supabase Storage"""
        try:
            list_path = (path or self.base_path).lstrip('/')
            response = self.supabase.storage.from_(self.bucket_name).list(list_path)
            items = []
            if response and isinstance(response, list):
                for item in response:
                    if not include_hidden and item.get('name', '').startswith('.'):
                        continue
                    full_path = f'{list_path}/{item['name']}' if list_path else item['name']
                    items.append({'name': item.get('name', ''), 'path': full_path, 'type': 'directory' if item.get('metadata', {}).get('mimetype') == 'application/x-directory' else 'file', 'size_bytes': item.get('metadata', {}).get('size', 0), 'size_mb': round(item.get('metadata', {}).get('size', 0) / (1024 * 1024), 2), 'modified_time': item.get('updated_at', ''), 'extension': Path(item.get('name', '')).suffix.lower(), 'is_hidden': item.get('name', '').startswith('.'), 'mime_type': item.get('metadata', {}).get('mimetype', '')})
            return items
        except Exception as e:
            logger.error(f'Error listing directory {path} from Supabase: {str(e)}')
            return []

    def _exists_raw(self, path: str) -> bool:
        """Check if path exists in Supabase Storage"""
        try:
            file_path = path.lstrip('/')
            parent_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            if not parent_dir:
                parent_dir = ''
            try:
                response = self.supabase.storage.from_(self.bucket_name).list(parent_dir)
                if response and isinstance(response, list):
                    for item in response:
                        if item.get('name') == file_name:
                            return True
                return False
            except Exception as e:
                logger.warning(f'Error listing directory {parent_dir}: {str(e)}')
                return False
        except Exception as e:
            logger.warning(f'Error checking if file {path} exists: {str(e)}')
            return False

    def _create_directory_raw(self, path: str) -> bool:
        """Create directory in Supabase Storage"""
        try:
            dir_path = path.lstrip('/')
            placeholder_content = b'# Directory placeholder'
            placeholder_path = f'{dir_path}/.placeholder'
            response = self.supabase.storage.from_(self.bucket_name).upload(path=placeholder_path, file=placeholder_content, file_options={'content-type': 'text/plain'})
            if response and (not isinstance(response, dict)) or response.get('error') is None:
                return True
            else:
                logger.error(f'Directory creation failed: {response}')
                return False
        except Exception as e:
            logger.error(f'Error creating directory {path} in Supabase: {str(e)}')
            return False

def _initialize_storage(self):
    """Initialize remote storage - verify bucket exists and is accessible"""
    if not hasattr(self, 'bucket_name') or not hasattr(self, 'supabase'):
        return
    try:
        logger.info(f'Testing bucket access for: {self.bucket_name}')
        self.supabase.storage.from_(self.bucket_name).list()
        logger.info(f'Successfully connected to Supabase bucket: {self.bucket_name}')
    except Exception as e:
        logger.warning(f'Could not verify bucket access: {str(e)}')

def _exists_raw(self, path: str) -> bool:
    """Check if path exists in Supabase Storage"""
    try:
        file_path = path.lstrip('/')
        parent_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        if not parent_dir:
            parent_dir = ''
        try:
            response = self.supabase.storage.from_(self.bucket_name).list(parent_dir)
            if response and isinstance(response, list):
                for item in response:
                    if item.get('name') == file_name:
                        return True
            return False
        except Exception as e:
            logger.warning(f'Error listing directory {parent_dir}: {str(e)}')
            return False
    except Exception as e:
        logger.warning(f'Error checking if file {path} exists: {str(e)}')
        return False

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

def _tf_vector(tokens: List[str]) -> Dict[str, float]:
    vec: Dict[str, float] = {}
    for t in tokens:
        vec[t] = vec.get(t, 0.0) + 1.0
    norm = math.sqrt(sum((v * v for v in vec.values()))) or 1.0
    for k in list(vec.keys()):
        vec[k] /= norm
    return vec

class StorageHandler(BaseModule):
    """
    Implementation of a storage handler for managing various storage backends.
    
    StorageHandler provides an abstraction for reading and writing data (e.g., memory, agents, workflows).
    It supports multiple storage types, including database, vector, and graph storage, initialized via factories.
    """
    storageConfig: StoreConfig = Field(..., description='Configuration for all storage backends')
    storageDB: Optional[Union[DBStoreBase, Any]] = Field(None, description='Database storage backend')
    vector_store: Optional[Union[VectorStoreBase, Any]] = Field(None, description='Single vector storage backend')
    graph_store: Optional[Union[GraphStoreBase, Any]] = Field(None, description='Optional graph storage backend')

    def init_module(self):
        """
        Initialize all storage backends based on the provided configuration.
        Calls individual initialization methods for database, vector, and graph stores.
        """
        if self.storageConfig.path is not None or self.storageConfig.path != ':memory:' or (not self.storageConfig.path):
            os.makedirs(os.path.dirname(self.storageConfig.path), exist_ok=True)
        self._init_db_store()
        self._init_vector_store()
        self._init_graph_store()

    def _init_db_store(self):
        """
        Initialize the database storage backend using the DBStoreFactory.
        Sets the storageDB attribute with the created instance.
        """
        db_config = self.storageConfig.dbConfig
        self.storageDB = DBStoreFactory.create(db_config.db_name, db_config)

    def _init_vector_store(self):
        """
        Initialize the vector storage backend using the VectorStoreFactory.
        Sets the storageVector attribute if the configuration is provided.
        """
        vector_config = self.storageConfig.vectorConfig
        if vector_config is not None:
            if self.vector_store is not None:
                del self.vector_store
            vector_config_dict = vector_config.model_dump()
            self.vector_store = VectorStoreFactory().create(store_type=vector_config.vector_name, store_config=vector_config_dict)

    def _init_graph_store(self):
        """
        Initialize the graph storage backend using the GraphStoreFactory.
        Sets the storageGraph attribute if the configuration is provided.
        """
        graph_config = self.storageConfig.graphConfig
        if graph_config is not None:
            self.graph_store = GraphStoreFactory().create(store_type=graph_config.graph_name, store_config=graph_config.model_dump())

    def load(self, tables: Optional[List[str]]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load all data from the database storage.

        Attributes:
            tables (Optional[List[str]]): List of table names to load; if None, loads all tables.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary with table names as keys and lists of records as values. You should parse the values by yourself.
        """
        result = {}
        table_info = self.storageDB.col_info()
        if tables is None:
            tables_to_load = [t.value for t in TableType]
        else:
            tables_to_load = tables
        for table_name in tables_to_load:
            table_data = []
            if any((t['table_name'] == table_name for t in table_info)):
                cursor = self.storageDB.connection.cursor()
                cursor.execute(f'SELECT * FROM {table_name}')
                columns = next((t['columns'].keys() for t in table_info if t['table_name'] == table_name))
                rows = cursor.fetchall()
                table_data = [dict(zip(columns, row)) for row in rows]
            result[table_name] = table_data
        return result

    def save(self, data: Dict[str, Any], *args, **kwargs):
        """
        Save all provided data to the database storage.

        Attributes:
            data (Dict[str, Any]): Dictionary with table names as keys and lists of records to save.

        Raises:
            ValueError: If an unknown table name is provided.
        """
        for table_name, records in data.items():
            store_type = None
            for st in TableType:
                if st.value == table_name:
                    store_type = st
                    break
            if store_type is None:
                raise ValueError(f'Unknown table: {table_name}')
            for record in records:
                self.storageDB.insert(metadata=record, store_type=store_type, table=table_name)

    def parse_result(self, results: Dict[str, str], store: Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]) -> Dict[str, Any]:
        """
        Parse database results, converting JSON strings to Python objects where applicable.

        Attributes:
            results (Dict[str, str]): Raw database results with column names as keys.
            store (Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]): Pydantic model for validation.

        Returns:
            Dict[str, Any]: Parsed results with JSON strings deserialized to Python objects.
        """
        for k, v in store.model_fields.items():
            if v.annotation not in [Optional[str], str]:
                try:
                    results[k] = json.loads(results[k])
                except (json.JSONDecodeError, KeyError, TypeError):
                    results[k] = results.get(k)
        return results

    def load_memory(self, memory_id: str, table: Optional[str]=None, **kwargs) -> Dict[str, Any]:
        """
        Load a single long-term memory data.

        Attributes:
            memory_id (str): The ID of the long-term memory.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a LongTermMemory instance.
        """
        table = table or TableType.store_memory.value
        result = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
        if result is not None:
            result = self.parse_result(result, MemoryStore)
        return result

    def save_memory(self, memory_data: Dict[str, Any], table: Optional[str]=None, **kwargs):
        """
        Save or update a single memory.

        Attributes:
            memory_data (Dict[str, Any]): The long-term memory's data.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        """
        table = table or TableType.store_memory.value
        memory_id = memory_data.get('memory_id')
        if not memory_id:
            raise ValueError("Memory data must include a 'memory_id' field")
        existing = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
        if existing:
            self.storageDB.update(memory_id, new_metadata=memory_data, store_type='memory', table=table)
        else:
            self.storageDB.insert(metadata=memory_data, store_type='memory', table=table)

    def load_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single agent's data.

        Attributes:
            agent_name (str): The unique name of the agent to retrieve.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create an Agent instance, or None if not found.
        """
        table = table or TableType.store_agent.value
        result = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
        if result is not None:
            result = self.parse_result(result, AgentStore)
        return result

    def remove_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs):
        """
        Remove an agent from storage if the agent exists.

        Attributes:
            agent_name (str): The name of the agent to be deleted.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If the agent does not exist in the specified table.
        """
        table = table or TableType.store_agent.value
        success = self.storageDB.delete(agent_name, store_type='agent', table=table)
        if not success:
            raise ValueError(f'Agent with name {agent_name} not found in table {table}')

    def save_agent(self, agent_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a single agent's data.

        Attributes:
            agent_data (Dict[str, Any]): The agent's data, must include 'name' and 'content' keys.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_agent.value
        agent_name = agent_data.get('name')
        if not agent_name:
            raise ValueError("Agent data must include a 'name' field")
        existing = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
        if existing:
            self.storageDB.update(agent_name, new_metadata=agent_data, store_type='agent', table=table)
        else:
            self.storageDB.insert(metadata=agent_data, store_type='agent', table=table)

    def load_workflow(self, workflow_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single workflow's data.

        Attributes:
            workflow_id (str): The ID of the workflow.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a WorkFlow instance, or None if not found.
        """
        table = table or TableType.store_workflow.value
        result = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
        if result is not None:
            result = self.parse_result(result, WorkflowStore)
        return result

    def save_workflow(self, workflow_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a workflow's data.

        Attributes:
            workflow_data (Dict[str, Any]): The workflow's data, must include 'name' field.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_workflow.value
        workflow_id = workflow_data.get('name')
        if not workflow_id:
            raise ValueError("Workflow data must include a 'name' field")
        existing = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
        if existing:
            self.storageDB.update(workflow_id, new_metadata=workflow_data, store_type='workflow', table=table)
        else:
            self.storageDB.insert(metadata=workflow_data, store_type='workflow', table=table)

    def load_history(self, memory_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single history entry.

        Attributes:
            memory_id (str): The ID of the memory associated with the history entry.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Returns:
            Dict[str, Any]: The history data, or None if not found.
        """
        table = table or TableType.store_history.value
        result = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
        if result is not None:
            result = self.parse_result(result, HistoryStore)
        return result

    def save_history(self, history_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a single history entry.

        Attributes:
            history_data (Dict[str, Any]): The history data, must include 'memory_id' field.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Raises:
            ValueError: If 'memory_id' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_history.value
        memory_id = history_data.get('memory_id')
        if not memory_id:
            raise ValueError("History data must include a 'memory_id' field")
        existing = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
        if existing:
            result = HistoryStore.model_validate(self.parse_result(existing, HistoryStore))
            history_data['old_memory'] = result.old_memory
            self.storageDB.update(memory_id, new_metadata=history_data, store_type='history', table=table)
        else:
            self.storageDB.insert(metadata=history_data, store_type='history', table=table)

    def load_index(self, corpus_id: str, table: Optional[str]=None) -> Optional[Dict[str, Any]]:
        result = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
        if result is not None:
            result = self.parse_result(result, IndexStore)
        return result

    def save_index(self, index_data: Dict[str, Any], table: Optional[str]=None):
        corpus_id = index_data.get('corpus_id')
        if not corpus_id:
            raise ValueError("Index data must include an 'corpus_id' field")
        existing = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
        if existing:
            self.storageDB.update(corpus_id, new_metadata=index_data, store_type='indexing', table=table)
        else:
            self.storageDB.insert(metadata=index_data, store_type='indexing', table=table)

def init_module(self):
    """
        Initialize all storage backends based on the provided configuration.
        Calls individual initialization methods for database, vector, and graph stores.
        """
    if self.storageConfig.path is not None or self.storageConfig.path != ':memory:' or (not self.storageConfig.path):
        os.makedirs(os.path.dirname(self.storageConfig.path), exist_ok=True)
    self._init_db_store()
    self._init_vector_store()
    self._init_graph_store()

def _init_vector_store(self):
    """
        Initialize the vector storage backend using the VectorStoreFactory.
        Sets the storageVector attribute if the configuration is provided.
        """
    vector_config = self.storageConfig.vectorConfig
    if vector_config is not None:
        if self.vector_store is not None:
            del self.vector_store
        vector_config_dict = vector_config.model_dump()
        self.vector_store = VectorStoreFactory().create(store_type=vector_config.vector_name, store_config=vector_config_dict)

def _init_graph_store(self):
    """
        Initialize the graph storage backend using the GraphStoreFactory.
        Sets the storageGraph attribute if the configuration is provided.
        """
    graph_config = self.storageConfig.graphConfig
    if graph_config is not None:
        self.graph_store = GraphStoreFactory().create(store_type=graph_config.graph_name, store_config=graph_config.model_dump())

def load(self, tables: Optional[List[str]]=None, *args, **kwargs) -> Dict[str, Any]:
    """
        Load all data from the database storage.

        Attributes:
            tables (Optional[List[str]]): List of table names to load; if None, loads all tables.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary with table names as keys and lists of records as values. You should parse the values by yourself.
        """
    result = {}
    table_info = self.storageDB.col_info()
    if tables is None:
        tables_to_load = [t.value for t in TableType]
    else:
        tables_to_load = tables
    for table_name in tables_to_load:
        table_data = []
        if any((t['table_name'] == table_name for t in table_info)):
            cursor = self.storageDB.connection.cursor()
            cursor.execute(f'SELECT * FROM {table_name}')
            columns = next((t['columns'].keys() for t in table_info if t['table_name'] == table_name))
            rows = cursor.fetchall()
            table_data = [dict(zip(columns, row)) for row in rows]
        result[table_name] = table_data
    return result

@wraps(func)
def worker(self, metadata, *args, **kwargs):
    table = kwargs.get('table', None)
    store_type = kwargs.get('store_type')
    if table is None:
        table = store_type
    if store_type == TableType.store_memory:
        column = list(MemoryStore.model_fields.keys())
        metadata = MemoryStore.model_validate(metadata)
    elif store_type == TableType.store_agent:
        column = list(AgentStore.model_fields.keys())
        metadata = AgentStore.model_validate(metadata)
    elif store_type == TableType.store_workflow:
        column = list(WorkflowStore.model_fields.keys())
        metadata = WorkflowStore.model_validate(metadata)
    elif store_type == TableType.store_history:
        column = list(HistoryStore.model_fields.keys())
        metadata = HistoryStore.model_validate(metadata, strict=False)
    elif store_type == TableType.store_indexing:
        column = list(IndexStore.model_fields.keys())
        metadata = IndexStore.model_validate(metadata, strict=False)
    else:
        raise ValueError('The value of store type is not valid.')
    table_column = _create_table(table, column)
    with self._lock:
        with self.connection:
            self.connection.execute(table_column)
            self.connection.commit()
    kwargs['metadata'] = metadata
    return func(self, *args, **kwargs)

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

class BasicNeo4jStore(Neo4jPropertyGraphStore):

    def __init__(self, username: str, password: str, url: str, database: str | None='neo4j', refresh_schema: bool=True, sanitize_query_output: bool=True, enhanced_schema: bool=False, create_indexes: bool=True, timeout: float | None=None, **neo4j_kwargs: Any) -> None:
        super().__init__(username, password, url, database, refresh_schema, sanitize_query_output, enhanced_schema, create_indexes, timeout, **neo4j_kwargs)

    def upsert_nodes(self, nodes: List[LabelledNode]) -> None:
        entity_dicts: List[dict] = []
        chunk_dicts: List[dict] = []
        for item in nodes:
            if isinstance(item, EntityNode):
                entity_dicts.append({**item.model_dump(), 'id': item.id})
            elif isinstance(item, ChunkNode):
                chunk_dicts.append({**item.model_dump(), 'id': item.id})
            else:
                pass
        if chunk_dicts:
            for index in range(0, len(chunk_dicts), CHUNK_SIZE):
                chunked_params = chunk_dicts[index:index + CHUNK_SIZE]
                self.structured_query(f"\n                    UNWIND $data AS row\n                    MERGE (c:{BASE_NODE_LABEL} {{id: row.id}})\n                    SET c.text = row.text, c:Chunk\n                    WITH c, row\n                    SET c += row.properties\n                    WITH c, row.embedding AS embedding\n                    WHERE embedding IS NOT NULL\n                    CALL db.create.setNodeVectorProperty(c, 'embedding', embedding)\n                    RETURN count(*)\n                    ", param_map={'data': chunked_params})
        if entity_dicts:
            for index in range(0, len(entity_dicts), CHUNK_SIZE):
                chunked_params = entity_dicts[index:index + CHUNK_SIZE]
                self.structured_query(f"\n                    UNWIND $data AS row\n                    MERGE (e:{BASE_NODE_LABEL} {{id: row.id}})\n                    SET e += apoc.map.clean(row.properties, [], [])\n                    SET e.name = row.name, e:`{BASE_ENTITY_LABEL}`\n                    WITH e, row\n                    CALL apoc.create.addLabels(e, [row.label])\n                    YIELD node\n                    WITH e, row\n                    CALL (e, row) {{\n                        WITH e, row\n                        WHERE row.embedding IS NOT NULL\n                        CALL db.create.setNodeVectorProperty(e, 'embedding', row.embedding)\n                        RETURN count(*) AS count\n                    }}\n                    WITH e, row WHERE row.properties.triplet_source_id IS NOT NULL\n                    MERGE (c:{BASE_NODE_LABEL} {{id: row.properties.triplet_source_id}})\n                    MERGE (e)<-[:MENTIONS]-(c)\n                    ", param_map={'data': chunked_params})

    def upsert_relations(self, relations: List[Relation]) -> None:
        """Add relations."""
        params = [r.model_dump() for r in relations]
        for index in range(0, len(params), CHUNK_SIZE):
            chunked_params = params[index:index + CHUNK_SIZE]
            self.structured_query(f'\n                UNWIND $data AS row\n                MERGE (source: {BASE_NODE_LABEL} {{id: row.source_id}})\n                ON CREATE SET source:Chunk\n                MERGE (target: {BASE_NODE_LABEL} {{id: row.target_id}})\n                ON CREATE SET target:Chunk\n                WITH source, target, row\n                CALL apoc.merge.relationship(source, row.label, {{}}, row.properties, target) YIELD rel\n                RETURN count(*)\n                ', param_map={'data': chunked_params})

def upsert_nodes(self, nodes: List[LabelledNode]) -> None:
    entity_dicts: List[dict] = []
    chunk_dicts: List[dict] = []
    for item in nodes:
        if isinstance(item, EntityNode):
            entity_dicts.append({**item.model_dump(), 'id': item.id})
        elif isinstance(item, ChunkNode):
            chunk_dicts.append({**item.model_dump(), 'id': item.id})
        else:
            pass
    if chunk_dicts:
        for index in range(0, len(chunk_dicts), CHUNK_SIZE):
            chunked_params = chunk_dicts[index:index + CHUNK_SIZE]
            self.structured_query(f"\n                    UNWIND $data AS row\n                    MERGE (c:{BASE_NODE_LABEL} {{id: row.id}})\n                    SET c.text = row.text, c:Chunk\n                    WITH c, row\n                    SET c += row.properties\n                    WITH c, row.embedding AS embedding\n                    WHERE embedding IS NOT NULL\n                    CALL db.create.setNodeVectorProperty(c, 'embedding', embedding)\n                    RETURN count(*)\n                    ", param_map={'data': chunked_params})
    if entity_dicts:
        for index in range(0, len(entity_dicts), CHUNK_SIZE):
            chunked_params = entity_dicts[index:index + CHUNK_SIZE]
            self.structured_query(f"\n                    UNWIND $data AS row\n                    MERGE (e:{BASE_NODE_LABEL} {{id: row.id}})\n                    SET e += apoc.map.clean(row.properties, [], [])\n                    SET e.name = row.name, e:`{BASE_ENTITY_LABEL}`\n                    WITH e, row\n                    CALL apoc.create.addLabels(e, [row.label])\n                    YIELD node\n                    WITH e, row\n                    CALL (e, row) {{\n                        WITH e, row\n                        WHERE row.embedding IS NOT NULL\n                        CALL db.create.setNodeVectorProperty(e, 'embedding', row.embedding)\n                        RETURN count(*) AS count\n                    }}\n                    WITH e, row WHERE row.properties.triplet_source_id IS NOT NULL\n                    MERGE (c:{BASE_NODE_LABEL} {{id: row.properties.triplet_source_id}})\n                    MERGE (e)<-[:MENTIONS]-(c)\n                    ", param_map={'data': chunked_params})

def upsert_relations(self, relations: List[Relation]) -> None:
    """Add relations."""
    params = [r.model_dump() for r in relations]
    for index in range(0, len(params), CHUNK_SIZE):
        chunked_params = params[index:index + CHUNK_SIZE]
        self.structured_query(f'\n                UNWIND $data AS row\n                MERGE (source: {BASE_NODE_LABEL} {{id: row.source_id}})\n                ON CREATE SET source:Chunk\n                MERGE (target: {BASE_NODE_LABEL} {{id: row.target_id}})\n                ON CREATE SET target:Chunk\n                WITH source, target, row\n                CALL apoc.merge.relationship(source, row.label, {{}}, row.properties, target) YIELD rel\n                RETURN count(*)\n                ', param_map={'data': chunked_params})

class Neo4jGraphStoreWrapper(GraphStoreBase):
    """Wrapper for Neo4j graph store."""

    def __init__(self, uri: str, username: str, password: str, database: str='neo4j', **kwargs):
        try:
            self.graph_store = BasicNeo4jStore(url=uri, username=username, password=password, database=database)
        except Exception as e:
            raise ValueError(f'Failed to connect to Neo4j: {str(e)}')
        self.verify_version()

    def get_graph_store(self) -> PropertyGraphStore:
        return self.graph_store

    @property
    def supports_vector_queries(self):
        return self.graph_store.supports_vector_queries and self.graph_store._supports_vector_index

    def verify_version(self):
        """
        Check if the connected Neo4j database version supports vector indexing
        without specifying embedding dimension.

        Queries the Neo4j database to retrieve its version and compares it
        against a target version (5.23.0) that is known to support vector
        indexing. 
        """
        db_data = self.graph_store.structured_query('CALL dbms.components()')
        version = db_data[0]['versions'][0]
        if 'aura' in version:
            version_tuple = (*map(int, version.split('-')[0].split('.')), 0)
        else:
            version_tuple = tuple(map(int, version.split('.')))
        target_version = (5, 23, 0)
        if version_tuple >= target_version:
            self.graph_store._supports_vector_index = True
        else:
            self.graph_store._supports_vector_index = False
            logger.warning(f'The version of Neo4j server is {version_tuple}, which is less than {target_version}. Disable the vector indexing.')

    def clear(self) -> None:
        """
        Clear the node and relation in the neo4j graph database.
        """
        with self.graph_store.client.session() as session:
            session.run('MATCH (n) DETACH DELETE n')
            session.run('CALL apoc.schema.assert({}, {})')

    async def aload(self, node: Union[LabelledNode, Relation, BaseNode]) -> None:
        """
        Asynchronously load a single node into the Neo4j graph database.

        Checks if a node with the same ID already exists in the database. If it does not exist,
        inserts the node as either an EntityNode or ChunkNode based on its type. Handles metadata
        and embeddings appropriately.

        Args:
            node (Union[LabelledNode, Relation, BaseNode]): The node/relation to load, either a Chunk or a LlamaIndex BaseNode.
        """
        try:
            if not isinstance(node, (BaseNode, EntityNode, ChunkNode, Relation)):
                raise ValueError(f'Unsupported node type: {type(node)}. Must be BaseNode, EntityNode, ChunkNode, Relation.')
            if isinstance(node, (EntityNode, ChunkNode)):
                self.graph_store.upsert_nodes([node])
            elif isinstance(node, BaseNode):
                self.graph_store.upsert_llama_nodes([node])
            elif isinstance(node, Relation):
                self.graph_store.upsert_relations([node])
            if self.graph_store.supports_structured_queries:
                self.graph_store.get_schema(refresh=True)
        except Exception as e:
            logger.error(f'Failed to load node with ID {node.id} into Neo4j: {str(e)}')
            raise

    def build_kv_store(self) -> Sequence[Union[LabelledNode, EntityNode, ChunkNode, Relation]]:
        """
        Build a kv_store from neo4j database.
        Returns a dictionary where:
        - Key: node ID
        - Value: Node object (EntityNode, ChunkNode, Relation)
        """
        try:
            cur_sanitize_query_output = self.graph_store.sanitize_query_output
            self.graph_store.sanitize_query_output = False
            nodes_query = f'\n                MATCH (n:{BASE_NODE_LABEL})\n                RETURN n.id AS name, labels(n) AS labels,\n                       n.text AS text,\n                       n.embedding AS embedding,\n                       properties(n) AS properties\n            '
            nodes_result = self.graph_store.structured_query(nodes_query)
            nodes = []
            for record in nodes_result:
                labels = record['labels']
                node_dict = {'id': record['name'], 'labels': labels, 'embedding': record['embedding'], 'properties': record['properties']}
                if 'Chunk' in labels:
                    if node_dict['properties']['_node_type'] == 'TextNode':
                        content = json.loads(node_dict['properties']['_node_content'])
                        content['metadata'] = json.loads(content['metadata']['metadata'])
                        node = TextNode(**content)
                    nodes.append(node)
                elif BASE_ENTITY_LABEL in labels:
                    node_dict['name'] = record['name'] or record['id']
                    node_dict['label'] = [label for label in labels if label not in [BASE_NODE_LABEL, BASE_ENTITY_LABEL]][0] if any((label not in [BASE_NODE_LABEL, BASE_ENTITY_LABEL] for label in labels)) else 'entity'
                    node = EntityNode(name=node_dict['name'], label=node_dict['label'], embedding=node_dict['embedding'], properties={'triplet_source_id': node_dict['properties']['triplet_source_id']})
                    nodes.append(node)
                else:
                    logger.warning(f'Skipping node with id {record['id']} due to unsupported labels: {labels}')
                    continue
            relations_query = 'MATCH ()-[r]->() RETURN type(r) AS label, startNode(r).id AS source_id, endNode(r).id AS target_id, properties(r) AS properties'
            relations_result = self.graph_store.structured_query(relations_query)
            relations = [Relation(label=record['label'], source_id=record['source_id'], target_id=record['target_id'], properties=json.loads(record['properties'].get('metadata', {})) if isinstance(record['properties'].get('metadata', {}), str) else record['properties'].get('metadata', {})) for record in relations_result]
            self.graph_store.sanitize_query_output = cur_sanitize_query_output
            logger.info(f'Exported {len(nodes)} nodes and {len(relations)} relations from Neo4j graph store')
            return nodes + relations
        except Exception as e:
            logger.error(f'Failed to export Neo4j graph store: {str(e)}')
            raise

def verify_version(self):
    """
        Check if the connected Neo4j database version supports vector indexing
        without specifying embedding dimension.

        Queries the Neo4j database to retrieve its version and compares it
        against a target version (5.23.0) that is known to support vector
        indexing. 
        """
    db_data = self.graph_store.structured_query('CALL dbms.components()')
    version = db_data[0]['versions'][0]
    if 'aura' in version:
        version_tuple = (*map(int, version.split('-')[0].split('.')), 0)
    else:
        version_tuple = tuple(map(int, version.split('.')))
    target_version = (5, 23, 0)
    if version_tuple >= target_version:
        self.graph_store._supports_vector_index = True
    else:
        self.graph_store._supports_vector_index = False
        logger.warning(f'The version of Neo4j server is {version_tuple}, which is less than {target_version}. Disable the vector indexing.')

def build_kv_store(self) -> Sequence[Union[LabelledNode, EntityNode, ChunkNode, Relation]]:
    """
        Build a kv_store from neo4j database.
        Returns a dictionary where:
        - Key: node ID
        - Value: Node object (EntityNode, ChunkNode, Relation)
        """
    try:
        cur_sanitize_query_output = self.graph_store.sanitize_query_output
        self.graph_store.sanitize_query_output = False
        nodes_query = f'\n                MATCH (n:{BASE_NODE_LABEL})\n                RETURN n.id AS name, labels(n) AS labels,\n                       n.text AS text,\n                       n.embedding AS embedding,\n                       properties(n) AS properties\n            '
        nodes_result = self.graph_store.structured_query(nodes_query)
        nodes = []
        for record in nodes_result:
            labels = record['labels']
            node_dict = {'id': record['name'], 'labels': labels, 'embedding': record['embedding'], 'properties': record['properties']}
            if 'Chunk' in labels:
                if node_dict['properties']['_node_type'] == 'TextNode':
                    content = json.loads(node_dict['properties']['_node_content'])
                    content['metadata'] = json.loads(content['metadata']['metadata'])
                    node = TextNode(**content)
                nodes.append(node)
            elif BASE_ENTITY_LABEL in labels:
                node_dict['name'] = record['name'] or record['id']
                node_dict['label'] = [label for label in labels if label not in [BASE_NODE_LABEL, BASE_ENTITY_LABEL]][0] if any((label not in [BASE_NODE_LABEL, BASE_ENTITY_LABEL] for label in labels)) else 'entity'
                node = EntityNode(name=node_dict['name'], label=node_dict['label'], embedding=node_dict['embedding'], properties={'triplet_source_id': node_dict['properties']['triplet_source_id']})
                nodes.append(node)
            else:
                logger.warning(f'Skipping node with id {record['id']} due to unsupported labels: {labels}')
                continue
        relations_query = 'MATCH ()-[r]->() RETURN type(r) AS label, startNode(r).id AS source_id, endNode(r).id AS target_id, properties(r) AS properties'
        relations_result = self.graph_store.structured_query(relations_query)
        relations = [Relation(label=record['label'], source_id=record['source_id'], target_id=record['target_id'], properties=json.loads(record['properties'].get('metadata', {})) if isinstance(record['properties'].get('metadata', {}), str) else record['properties'].get('metadata', {})) for record in relations_result]
        self.graph_store.sanitize_query_output = cur_sanitize_query_output
        logger.info(f'Exported {len(nodes)} nodes and {len(relations)} relations from Neo4j graph store')
        return nodes + relations
    except Exception as e:
        logger.error(f'Failed to export Neo4j graph store: {str(e)}')
        raise

class PromptRegistry:
    """Central registry for all runtime-patchable fields."""

    def __init__(self) -> None:
        self.fields: Dict[str, OptimizableField] = {}

    def register_field(self, field: OptimizableField):
        self.fields[field.name] = field

    def get(self, name: str) -> Any:
        return self.fields[name].get()

    def set(self, name: str, value: Any):
        self.fields[name].set(value)

    def names(self) -> List[str]:
        return list(self.fields.keys())

    def register_path(self, root: Any, path: str, *, name: str | None=None):
        """用类似 'encoder.layers[3].dropout_p' 的字符串一次性注册。"""
        key = name or path.split('.')[-1]
        parent, leaf = self._walk(root, path)

        def getter():
            return parent[leaf] if isinstance(parent, (list, dict)) else getattr(parent, leaf)

        def setter(v):
            if isinstance(parent, (list, dict)):
                parent[leaf] = v
            else:
                setattr(parent, leaf, v)
        field = OptimizableField(key, getter, setter)
        self.register_field(field)
        return field

    def _walk(self, root, path: str, create_missing=False):
        cur = root
        parts = path.split('.')
        for part in parts[:-1]:
            m = _INDEX_RE.match(part)
            if m:
                attr, idx = m.groups()
                cur = getattr(cur, attr) if attr else cur
                idx = idx.strip()
                if idx.startswith("'") and idx.endswith("'") or (idx.startswith('"') and idx.endswith('"')):
                    idx = idx[1:-1]
                elif idx.isdigit():
                    idx = int(idx)
                cur = cur[idx]
            else:
                cur = getattr(cur, part)
        leaf = parts[-1]
        m = _INDEX_RE.match(leaf)
        if m:
            attr, idx = m.groups()
            parent = getattr(cur, attr) if attr else cur
            idx = idx.strip()
            if idx.startswith("'") and idx.endswith("'") or (idx.startswith('"') and idx.endswith('"')):
                idx = idx[1:-1]
            elif idx.isdigit():
                idx = int(idx)
            return (parent, idx)
        return (cur, leaf)

def names(self) -> List[str]:
    return list(self.fields.keys())

class BaseCodeBlockOptimizer(abc.ABC):
    """
    Abstract optimiser that:
      • performs sequential trials
      • writes sampled cfg back to runtime via PromptRegistry
      • validates that registered names appear in CodeBlock signature
    """

    def __init__(self, registry: PromptRegistry, metric: str, maximize: bool=True, max_trials: int=30):
        self.registry = registry
        self.metric = metric
        self.maximize = maximize
        self.max_trials = max_trials

    @abc.abstractmethod
    def sample_cfg(self) -> Dict[str, Any]:
        """Return a cfg dict (may include subset of registry names)."""

    @abc.abstractmethod
    def update(self, cfg: Dict[str, Any], score: float):
        """Update internal optimiser state."""

    def _apply_cfg(self, cfg: Dict[str, Any]):
        for k, v in cfg.items():
            if k in self.registry.fields:
                self.registry.set(k, v)

    def _check_codeblock_compat(self, code_block: CodeBlock):
        sig = inspect.signature(code_block._func)
        params = sig.parameters.values()
        has_kwargs = any((p.kind == inspect.Parameter.VAR_KEYWORD for p in params))
        accepts_cfg_dict = 'cfg' in sig.parameters
        if has_kwargs or accepts_cfg_dict:
            return
        allowed_keys = set(sig.parameters)
        unknown = set(self.registry.names()) - allowed_keys
        if unknown:
            import warnings
            warnings.warn(f'PromptRegistry fields {unknown} are not present in {code_block.name}() signature; they will be ignored.')

    def run(self, code_block: CodeBlock, evaluator: Callable[[Dict[str, Any], Any], float]) -> Tuple[Dict[str, Any], List[Tuple[Dict[str, Any], float]]]:
        self._check_codeblock_compat(code_block)
        best_cfg, best_score = (None, -float('inf') if self.maximize else float('inf'))
        history: List[Tuple[Dict[str, Any], float]] = []
        for _ in range(self.max_trials):
            cfg = self.sample_cfg()
            self._apply_cfg(cfg)
            result = code_block.run(cfg)
            score = evaluator(cfg, result)
            self.update(cfg, score)
            history.append((cfg, score))
            better = score > best_score if self.maximize else score < best_score
            if better:
                best_cfg, best_score = (cfg, score)
        return (best_cfg, history)

def _check_codeblock_compat(self, code_block: CodeBlock):
    sig = inspect.signature(code_block._func)
    params = sig.parameters.values()
    has_kwargs = any((p.kind == inspect.Parameter.VAR_KEYWORD for p in params))
    accepts_cfg_dict = 'cfg' in sig.parameters
    if has_kwargs or accepts_cfg_dict:
        return
    allowed_keys = set(sig.parameters)
    unknown = set(self.registry.names()) - allowed_keys
    if unknown:
        import warnings
        warnings.warn(f'PromptRegistry fields {unknown} are not present in {code_block.name}() signature; they will be ignored.')

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

class CustomAgentCall:
    """A custom agent call with textgrad.Variable inputs and output."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.last_outputs: dict[str, str] = dict()

    def __call__(self, instruction: Variable, system_prompt: Variable, **inputs: Variable) -> Variable:
        action = self.agent.actions[0]
        input_names = action.inputs_format.get_attrs()
        agent_inputs = {}
        for key, input_variable in inputs.items():
            if key in input_names:
                agent_inputs[key] = input_variable.value
            else:
                parsed_inputs: dict[str, str] = {k: v for k, v in input_variable.parsed_outputs.items() if k in input_names}
                agent_inputs.update(parsed_inputs)
        with suppress_logger_info():
            outputs = self.agent.execute(action_name=action.name, action_input_data=agent_inputs).content
        self.last_outputs = outputs.to_dict()
        return outputs.content

def __init__(self, agent: Agent):
    self.agent = agent
    self.last_outputs: dict[str, str] = dict()

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

class EvopromptOptimizer(BaseOptimizer):
    """
    Base class for evolutionary prompt optimization algorithms.
    
    This optimizer uses evolutionary algorithms to improve prompts in multi-agent workflows.
    It supports both node-based and combination-based evolution strategies.
    """

    def __init__(self, registry: ParamRegistry, program: Callable, population_size: int, iterations: int, llm_config: OpenAILLMConfig, concurrency_limit: int=10, combination_sample_size: int=None, enable_logging: bool=True, log_dir: str=None, enable_early_stopping: bool=True, early_stopping_patience: int=3):
        """
        Initialize the EvoPrompt optimizer.

        Args:
            registry: Parameter registry for tracking prompt nodes
            program: The program/workflow to optimize
            population_size: Size of the evolution population
            iterations: Number of evolution iterations
            llm_config: Configuration for the LLM used in evolution
            concurrency_limit: Maximum concurrent API calls
            combination_sample_size: Sample size for combination evaluation
            enable_logging: Whether to enable detailed logging
            log_dir: Directory for saving logs
            enable_early_stopping: Whether to enable early stopping
            early_stopping_patience: Number of generations to wait before stopping
        """
        super().__init__(registry=registry, program=program)
        self.population_size = population_size
        self.iterations = iterations
        self.llm_config = llm_config
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.combination_sample_size = combination_sample_size
        self.enable_logging = enable_logging
        self.log_dir_base = log_dir
        self.log_dir = None
        self.enable_early_stopping = enable_early_stopping
        self.early_stopping_patience = early_stopping_patience
        self._best_score_so_far = -float('inf')
        self._generations_without_improvement = 0
        self._eval_cache = {}
        self.node_populations: Dict[str, List[str]] = {}
        self.node_scores: Dict[str, List[float]] = {}
        self.best_scores_per_gen: Dict[str, Dict[str, float]] = {}
        self.avg_scores_per_gen: Dict[str, Dict[str, float]] = {}
        self.best_combo_scores_per_gen: Dict[str, float] = {}
        self.avg_combo_scores_per_gen: Dict[str, float] = {}
        self.paraphrase_agent = CustomizeAgent(name='ParaphraseAgent', description='An agent that paraphrases a given instruction.', prompt='Task: Generate a semantically equivalent but differently worded version of the user-provided instruction.\n                    \nNow, please process the following instruction:\nInput: {instruction}\n\nPlease provide the paraphrased version in the following format:\n\n## paraphrased_instruction\n[Your paraphrased version here]', llm_config=self.llm_config, inputs=[{'name': 'instruction', 'type': 'string', 'description': 'The instruction to paraphrase.'}], outputs=[{'name': 'paraphrased_instruction', 'type': 'string', 'description': 'The paraphrased instruction.'}], parse_mode='title')

    def _setup_logging_directory(self, benchmark: BIGBenchHard):
        """
        Set up logging directory for evolution tracking.
        
        Args:
            benchmark: The benchmark instance containing task information
        """
        if not self.enable_logging or self.log_dir:
            return
        task_name = benchmark.task if hasattr(benchmark, 'task') else 'unknown_task'
        if self.log_dir_base is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            algo_name = self.__class__.__name__.replace('Optimizer', '')
            self.log_dir = f'node_evolution_logs_{algo_name}_{self.llm_config.model}_{task_name}_{timestamp}'
        else:
            self.log_dir = self.log_dir_base
        os.makedirs(self.log_dir, exist_ok=True)
        logger.info(f'Logging enabled. Log files will be saved to: {self.log_dir}')

    def _log_generation_summary(self, generation: int, operation: str='Evolution'):
        """
        Log detailed summary of each generation's population and scores.
        
        Args:
            generation: The current generation number
            operation: Type of operation (Evolution, Initial, etc.)
        """
        if not self.enable_logging:
            return
        filename = f'generation_{generation:02d}_{operation.lower()}.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Node_Name', 'Individual_ID', 'Prompt_Text', 'Fitness_Score', 'Status', 'Rank_in_Node', 'Generation', 'Timestamp'])
            timestamp = datetime.now().isoformat()
            for node_name in self.node_populations.keys():
                node_pop = self.node_populations.get(node_name, [])
                node_scores = self.node_scores.get(node_name, [])
                if not node_pop:
                    continue
                sorted_indices = sorted(range(len(node_scores)), key=lambda i: node_scores[i], reverse=True)
                for rank, idx in enumerate(sorted_indices, 1):
                    prompt = node_pop[idx]
                    score = node_scores[idx]
                    status = 'Best' if rank == 1 else 'Survivor' if rank <= self.population_size else 'Eliminated'
                    writer.writerow([node_name, f'{node_name}_{idx}', prompt[:200] + '...' if len(prompt) > 200 else prompt, f'{score:.6f}', status, rank, generation, timestamp])

    def _log_detailed_evaluation(self, generation: int, combinations: List[Dict[str, str]], combination_scores: List[float]):
        if not self.enable_logging:
            return
        filename = f'combo_evaluation_gen_{generation:02d}.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            node_names = list(combinations[0].keys()) if combinations else []
            header = ['Combination_ID', 'Average_Score']
            for node_name in node_names:
                header.append(f'{node_name}_Prompt_Preview')
            header.extend(['Generation', 'Timestamp'])
            writer.writerow(header)
            timestamp = datetime.now().isoformat()
            for combo_id, (combination, avg_score) in enumerate(zip(combinations, combination_scores)):
                try:
                    row = [f'combo_{combo_id}', f'{avg_score:.6f}']
                    for node_name in node_names:
                        prompt = combination[node_name]
                        row.append(prompt[:50] + '...' if len(prompt) > 50 else prompt)
                    row.extend([generation, timestamp])
                    writer.writerow(row)
                except Exception as e:
                    logger.error(f'Error logging evaluation for combination {combo_id}: {e}')

    def _create_single_metric_plot(self, metric_name: str, generations: List[int], best_scores: List[float], avg_scores: List[float], algorithm_name: str, plot_dir: str):
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(generations, best_scores, marker='o', linestyle='-', linewidth=2, markersize=8, label='Best Score')
        ax.plot(generations, avg_scores, marker='x', linestyle='--', linewidth=2, markersize=8, label='Average Score')
        title = f"Performance for '{metric_name}' ({algorithm_name})"
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Fitness Score', fontsize=12)
        ax.set_xticks(generations)
        ax.set_xticklabels([f'Gen {g}' for g in generations], rotation=45, ha='right')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        safe_metric_name = re.sub('[^a-zA-Z0-9_-]', '_', metric_name)
        filename = f'performance_plot_{safe_metric_name}.png'
        filepath = os.path.join(plot_dir, filename)
        try:
            plt.savefig(filepath, dpi=200, bbox_inches='tight')
        except Exception as e:
            logger.error(f'Failed to save individual plot for {metric_name}: {e}')
        finally:
            plt.close(fig)

    def _plot_and_save_performance_graph(self, algorithm_name: str):
        if not self.enable_logging or plt is None:
            if plt is None:
                logger.warning('Matplotlib not found, skipping plot generation.')
            return
        if not self.best_scores_per_gen and (not self.best_combo_scores_per_gen):
            logger.warning('No performance data to plot.')
            return
        plt.style.use('seaborn-v0_8-whitegrid')
        all_gen_keys = set(self.best_scores_per_gen.keys()) | set(self.best_combo_scores_per_gen.keys())
        generations = sorted([int(re.search('\\d+', gen).group()) for gen in all_gen_keys if re.search('\\d+', gen)])
        fig_combined, ax_combined = plt.subplots(figsize=(16, 9))
        if self.best_combo_scores_per_gen:
            combo_best = [self.best_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            combo_avg = [self.avg_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            ax_combined.plot(generations, combo_best, marker='*', linestyle='-', linewidth=2.5, markersize=10, label='Best Combination Score (Overall)')
            ax_combined.plot(generations, combo_avg, marker='D', linestyle='--', linewidth=2.5, markersize=8, label='Average Combination Score (Overall)')
        all_node_metrics = set()
        for gen_data in self.best_scores_per_gen.values():
            all_node_metrics.update(gen_data.keys())
        for metric in sorted(list(all_node_metrics)):
            best_scores = [self.best_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            avg_scores = [self.avg_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            ax_combined.plot(generations, best_scores, marker='o', linestyle='-', alpha=0.7, label=f'Best Score ({metric})')
            ax_combined.plot(generations, avg_scores, marker='x', linestyle='--', alpha=0.7, label=f'Average Score ({metric})')
        ax_combined.set_title(f'Overall Performance Evolution ({algorithm_name})', fontsize=18, weight='bold')
        ax_combined.set_xlabel('Generation', fontsize=14)
        ax_combined.set_ylabel('Fitness Score', fontsize=14)
        ax_combined.set_xticks(generations)
        ax_combined.set_xticklabels([f'Gen {g}' for g in generations], rotation=45, ha='right')
        handles, labels = ax_combined.get_legend_handles_labels()
        combo_indices = [i for i, label in enumerate(labels) if 'Combination' in label]
        node_indices = [i for i, label in enumerate(labels) if 'Combination' not in label]
        ax_combined.legend([handles[i] for i in combo_indices + node_indices], [labels[i] for i in combo_indices + node_indices], loc='best', fontsize=10)
        ax_combined.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        combined_filepath = os.path.join(self.log_dir, 'performance_summary_OVERALL.png')
        try:
            plt.savefig(combined_filepath, dpi=300, bbox_inches='tight')
            logger.info(f'Overall performance plot saved to: {combined_filepath}')
        except Exception as e:
            logger.error(f'Failed to save overall performance plot: {e}')
        finally:
            plt.close(fig_combined)
        individual_plot_dir = os.path.join(self.log_dir, 'individual_plots')
        os.makedirs(individual_plot_dir, exist_ok=True)
        for metric in sorted(list(all_node_metrics)):
            best_scores = [self.best_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            avg_scores = [self.avg_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            self._create_single_metric_plot(metric, generations, best_scores, avg_scores, algorithm_name, individual_plot_dir)
        if self.best_combo_scores_per_gen:
            combo_best = [self.best_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            combo_avg = [self.avg_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            self._create_single_metric_plot('Combination', generations, combo_best, combo_avg, algorithm_name, individual_plot_dir)
        logger.info(f'Individual performance plots saved to: {individual_plot_dir}')

    def _log_optimization_summary(self, algorithm_name: str, best_config: Dict[str, str], test_accuracy: float=None):
        if not self.enable_logging:
            return
        filename = f'optimization_summary_{algorithm_name.lower()}.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', 'Timestamp'])
            timestamp = datetime.now().isoformat()
            writer.writerow(['Algorithm', algorithm_name, timestamp])
            writer.writerow(['Population_Size', self.population_size, timestamp])
            writer.writerow(['Iterations', self.iterations, timestamp])
            writer.writerow(['Combination_Sample_Size', self.combination_sample_size, timestamp])
            writer.writerow(['Early_Stopping_Enabled', self.enable_early_stopping, timestamp])
            if self.enable_early_stopping:
                writer.writerow(['Early_Stopping_Patience', self.early_stopping_patience, timestamp])
            if test_accuracy is not None:
                writer.writerow(['Final_Test_Accuracy', f'{test_accuracy:.6f}', timestamp])
            for node_name, prompt in best_config.items():
                writer.writerow([f'Best_{node_name}', prompt, timestamp])
            for gen_name in self.best_scores_per_gen.keys():
                for metric_name, best_score in self.best_scores_per_gen[gen_name].items():
                    writer.writerow([f'{gen_name}_{metric_name}_Best', f'{best_score:.6f}', timestamp])
                if gen_name in self.avg_scores_per_gen:
                    for metric_name, avg_score in self.avg_scores_per_gen[gen_name].items():
                        writer.writerow([f'{gen_name}_{metric_name}_Avg', f'{avg_score:.6f}', timestamp])
        self._plot_and_save_performance_graph(algorithm_name)
        try:
            self._save_best_config_json(best_config)
        except Exception as e:
            logger.error(f'Failed to save best_config.json: {e}')

    def _save_best_config_json(self, best_config: Dict[str, str], filename: str='best_config.json') -> None:
        """
        Save the best configuration to a JSON file in the log directory.

        This is a convenience artifact for downstream automation to reload and
        apply the optimized prompt set without parsing CSVs.

        Note: optimize() already applies the best config to the in-memory
        program. This JSON is intended for persistence and later reuse.
        """
        if not self.enable_logging:
            return
        if not self.log_dir:
            return
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(best_config, f, ensure_ascii=False, indent=2)
        logger.info(f'Best config JSON saved to: {filepath}')

    def load_and_apply_config(self, path: str) -> Dict[str, str]:
        """
        Load a JSON best_config from disk and apply it to the registered program.

        Returns the loaded configuration dictionary.
        """
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        self.apply_cfg(cfg)
        logger.info(f'Applied configuration from JSON: {path}')
        return cfg

    async def _log_evaluation_details(self, benchmark: BIGBenchHard, dataset: List[Dict], predictions: List[str], scores: List[float], eval_mode: str, accuracy: float, correct_count: int, total_count: int):
        if not self.enable_logging:
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'evaluation_testset_{eval_mode}_{timestamp}.csv'
        filepath = os.path.join(self.log_dir, filename)
        logger.info(f'Logging detailed evaluation results to {filepath}')
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Overall_Accuracy', f'{accuracy:.6f}'])
            writer.writerow(['Correct_Count', correct_count])
            writer.writerow(['Total_Count', total_count])
            writer.writerow([])
            writer.writerow(['example_id', 'input_text', 'prediction', 'ground_truth', 'score'])
            for i, example in enumerate(dataset):
                example_id = benchmark._get_id(example)
                input_text = example.get('input', '')
                label = benchmark.get_label(example)
                writer.writerow([example_id, input_text[:200] + '...' if len(input_text) > 200 else input_text, predictions[i], label, scores[i]])

    def _log_generation(self, generation: int, combos_with_scores: List[tuple]):
        """
        Log generation data for combination-based evolution.
        """
        if not self.enable_logging:
            return
        filename = f'combo_generation_{generation:02d}_log.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ['Combination_ID', 'Combination_Score', 'Node_Name', 'Prompt_Text', 'Generation', 'Timestamp']
            writer.writerow(header)
            timestamp = datetime.now().isoformat()
            sorted_combos = sorted(combos_with_scores, key=lambda x: x[1], reverse=True)
            for combo_rank, (combination, avg_score) in enumerate(sorted_combos):
                combo_id = f'combo_rank_{combo_rank + 1}'
                for node_name, prompt_text in combination.items():
                    writer.writerow([combo_id, f'{avg_score:.6f}', node_name, prompt_text[:200] + '...' if len(prompt_text) > 200 else prompt_text, generation, timestamp])

    async def _evaluate_combination_list(self, combinations: List[Dict], benchmark: BIGBenchHard, dev_set: list) -> List[float]:
        if not combinations:
            return []
        eval_dev_set = dev_set[:50] if len(dev_set) > 50 else dev_set
        all_scores = []
        pbar = aio_tqdm(total=len(combinations), desc='Evaluating batch', leave=False)
        for combo in combinations:
            tasks = [self._evaluate_combination_on_example(combo, benchmark, ex) for ex in eval_dev_set]
            example_scores = await asyncio.gather(*tasks)
            avg_score = sum(example_scores) / len(example_scores) if example_scores else 0.0
            all_scores.append(avg_score)
            pbar.update(1)
        pbar.close()
        return all_scores

    def _generate_combinations(self, node_populations: Dict[str, List[str]]) -> List[Dict[str, str]]:
        node_names = list(node_populations.keys())
        node_prompts = [node_populations[node] for node in node_names]
        total_possible = np.prod([len(p) for p in node_prompts if p]) if all((p for p in node_prompts)) else 0
        if total_possible == 0:
            logger.warning('Cannot generate combinations, one or more node populations are empty.')
            return []
        if self.combination_sample_size is None:
            target_size = min(self.population_size, int(total_possible), 200)
        else:
            target_size = min(self.combination_sample_size, int(total_possible))
        logger.info(f'Total possible combinations: {total_possible}, sampling: {target_size}')
        if target_size >= total_possible:
            all_combinations = []
            for combination in itertools.product(*node_prompts):
                combo_dict = {node_names[i]: combination[i] for i in range(len(node_names))}
                all_combinations.append(combo_dict)
            return all_combinations
        sampled_combinations = []
        sampled_keys = set()
        max_attempts = target_size * 5
        attempts = 0
        while len(sampled_combinations) < target_size and attempts < max_attempts:
            combination = {name: random.choice(prompts) for name, prompts in node_populations.items()}
            combo_key = tuple(sorted(combination.items()))
            if combo_key not in sampled_keys:
                sampled_combinations.append(combination)
                sampled_keys.add(combo_key)
            attempts += 1
        logger.info(f'Generated {len(sampled_combinations)} unique combinations')
        return sampled_combinations

    async def _evaluate_combination_on_example(self, combination: Dict[str, str], benchmark: BIGBenchHard, example: Dict) -> float:
        combo_key = tuple(sorted(combination.items()))
        example_key = str(hash(str(example)))
        cache_key = hash((combo_key, example_key))
        if not hasattr(self, '_eval_cache'):
            self._eval_cache = {}
        if cache_key in self._eval_cache:
            return self._eval_cache[cache_key]
        async with self.semaphore:
            try:
                original_config = self.get_current_cfg()
                self.apply_cfg(combination)
                inputs = {k: v for k, v in example.items() if k in benchmark.get_input_keys()}
                prediction, _ = await asyncio.to_thread(self.program, **inputs)
                label = benchmark.get_label(example)
                score_dict = benchmark.evaluate(prediction, label)
                score = score_dict.get('em', 0.0)
                self.apply_cfg(original_config)
                self._eval_cache[cache_key] = score
                if len(self._eval_cache) > 5000:
                    keys_to_del = list(self._eval_cache.keys())[:1000]
                    for key in keys_to_del:
                        del self._eval_cache[key]
                return score
            except Exception as e:
                logger.error(f'Error evaluating combination: {e}')
                return 0.0

    async def _evaluate_combinations_and_update_node_scores(self, combinations: List[Dict[str, str]], benchmark: BIGBenchHard, dev_set: list) -> List[float]:
        eval_dev_set = dev_set[:50] if len(dev_set) > 50 else dev_set
        combination_scores = []
        print(f'Evaluating {len(combinations)} combinations on {len(eval_dev_set)} examples...')
        combo_pbar = aio_tqdm(total=len(combinations), desc='Evaluating Combinations')
        for combination in combinations:
            tasks = [self._evaluate_combination_on_example(combination, benchmark, ex) for ex in eval_dev_set]
            example_scores = await asyncio.gather(*tasks)
            avg_score = sum(example_scores) / len(example_scores) if example_scores else 0.0
            combination_scores.append(avg_score)
            combo_pbar.update(1)
        combo_pbar.close()
        for node_name in self.node_populations.keys():
            self.node_scores[node_name] = [0.0] * len(self.node_populations[node_name])
            for prompt_idx, prompt in enumerate(self.node_populations[node_name]):
                participating_scores = [combo_score for combo_idx, combo_score in enumerate(combination_scores) if combinations[combo_idx].get(node_name) == prompt]
                if participating_scores:
                    self.node_scores[node_name][prompt_idx] = sum(participating_scores) / len(participating_scores)
                else:
                    self.node_scores[node_name][prompt_idx] = 0.0
        return combination_scores

    async def _perform_paraphrase(self, prompt: str) -> str:
        async with self.semaphore:
            output = await asyncio.to_thread(self.paraphrase_agent, inputs={'instruction': prompt})
            return output.content.paraphrased_instruction.strip()

    async def _perform_evolution(self, agent: Callable, inputs: Dict[str, str]) -> str:
        async with self.semaphore:
            output = await asyncio.to_thread(agent, inputs=inputs)
            if hasattr(output.content, 'evolved_prompt'):
                return output.content.evolved_prompt.strip()
            return str(output.content).strip()

    async def _initialize_node_populations(self, initial_config: Dict[str, any]):
        for node_name, initial_value in initial_config.items():
            node_population = []
            if isinstance(initial_value, list):
                provided_size = len(initial_value)
                if self.population_size < provided_size:
                    logger.info(f"Node '{node_name}': Provided population ({provided_size}) is larger than target size ({self.population_size}). Randomly sampling.")
                    node_population = random.sample(initial_value, self.population_size)
                elif self.population_size == provided_size:
                    logger.info(f"Node '{node_name}': Provided population size ({provided_size}) matches target size. Using directly.")
                    node_population = list(initial_value)
                else:
                    logger.info(f"Node '{node_name}': Target population size ({self.population_size}) is larger than provided ({provided_size}). Expanding.")
                    node_population = list(initial_value)
                    num_to_generate = self.population_size - provided_size
                    source_prompts_for_generation = random.choices(initial_value, k=num_to_generate)
                    paraphrase_tasks = [self._perform_paraphrase(prompt) for prompt in source_prompts_for_generation]
                    new_prompts = await aio_tqdm.gather(*paraphrase_tasks, desc=f'Expanding population for {node_name}')
                    node_population.extend(new_prompts)
            elif isinstance(initial_value, str):
                logger.info(f"Node '{node_name}': Generating population from a single initial prompt.")
                node_population = [initial_value]
                if self.population_size > 1:
                    num_to_generate = self.population_size - 1
                    paraphrase_tasks = [self._perform_paraphrase(initial_value) for _ in range(num_to_generate)]
                    new_prompts = await aio_tqdm.gather(*paraphrase_tasks, desc=f'Generating initial population for {node_name}')
                    node_population.extend(new_prompts)
            else:
                raise TypeError(f"Unsupported type for tracked parameter '{node_name}': {type(initial_value)}. Must be str or list.")
            self.node_populations[node_name] = node_population
            self.node_scores[node_name] = [0.0] * self.population_size

    async def evaluate(self, benchmark: BIGBenchHard, eval_mode: str='test') -> Dict[str, float]:
        """
        Evaluates the optimized program on a specified dataset.

        Args:
            benchmark (BIGBenchHard): The benchmark instance containing the data.
            eval_mode (str): The evaluation mode, either "test" or "dev".

        Returns:
            Dict[str, float]: A dictionary containing evaluation metrics.
        """
        logger.info(f"--- Evaluating optimized program on '{eval_mode}' set ---")
        dataset = benchmark.get_test_data() if eval_mode == 'test' else benchmark.get_dev_data()
        if not dataset:
            logger.warning(f"No data found for '{eval_mode}' set. Returning empty results.")
            return {}

        async def evaluate_example(example: Dict) -> tuple[float, str]:
            prediction, _ = await asyncio.to_thread(self.program, input=example['input'])
            score_dict = benchmark.evaluate(prediction, benchmark.get_label(example))
            score = score_dict.get('em', 0.0)
            return (score, prediction)
        tasks = [evaluate_example(ex) for ex in dataset]
        results = await aio_tqdm.gather(*tasks, desc=f'Evaluating on {eval_mode.capitalize()} Set')
        scores, predictions = zip(*results) if results else ([], [])
        correct_count = sum(scores)
        total_count = len(dataset)
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        logger.info(f'{eval_mode.capitalize()} Set Accuracy: {accuracy:.4f} ({int(correct_count)}/{total_count})')
        if self.enable_logging:
            await self._log_evaluation_details(benchmark, dataset, predictions, scores, eval_mode, accuracy, int(correct_count), total_count)
        return {'accuracy': accuracy}

def _generate_combinations(self, node_populations: Dict[str, List[str]]) -> List[Dict[str, str]]:
    node_names = list(node_populations.keys())
    node_prompts = [node_populations[node] for node in node_names]
    total_possible = np.prod([len(p) for p in node_prompts if p]) if all((p for p in node_prompts)) else 0
    if total_possible == 0:
        logger.warning('Cannot generate combinations, one or more node populations are empty.')
        return []
    if self.combination_sample_size is None:
        target_size = min(self.population_size, int(total_possible), 200)
    else:
        target_size = min(self.combination_sample_size, int(total_possible))
    logger.info(f'Total possible combinations: {total_possible}, sampling: {target_size}')
    if target_size >= total_possible:
        all_combinations = []
        for combination in itertools.product(*node_prompts):
            combo_dict = {node_names[i]: combination[i] for i in range(len(node_names))}
            all_combinations.append(combo_dict)
        return all_combinations
    sampled_combinations = []
    sampled_keys = set()
    max_attempts = target_size * 5
    attempts = 0
    while len(sampled_combinations) < target_size and attempts < max_attempts:
        combination = {name: random.choice(prompts) for name, prompts in node_populations.items()}
        combo_key = tuple(sorted(combination.items()))
        if combo_key not in sampled_keys:
            sampled_combinations.append(combination)
            sampled_keys.add(combo_key)
        attempts += 1
    logger.info(f'Generated {len(sampled_combinations)} unique combinations')
    return sampled_combinations

class MiproLMWrapper(LM):
    """
    A wrapper class for the LLM model. It converts the BaseLLM model in EvoAgentX to a dspy.LM object. 
    """

    def __init__(self, model: BaseLLM, model_type: Literal['chat', 'text']='chat', temperature: float=0.0, max_tokens: int=4000, cache: bool=True, cache_in_memory: bool=True, callbacks: Optional[List[BaseCallback]]=None, num_retries: int=3, provider=None, finetuning_model: Optional[str]=None, launch_kwargs: Optional[dict[str, Any]]=None, train_kwargs: Optional[dict[str, Any]]=None, **kwargs):
        self.model = model
        self.model_type = model_type
        self.cache = cache
        self.cache_in_memory = cache_in_memory
        self.callbacks = callbacks or []
        self.history = []
        self.provider = provider or Provider()
        self.num_retries = num_retries
        self.finetuning_model = finetuning_model
        self.launch_kwargs = launch_kwargs or {}
        self.train_kwargs = train_kwargs or {}
        self.kwargs = dict(temperature=temperature, max_tokens=max_tokens, **kwargs)

    def forward(self, prompt=None, messages=None, **kwargs):
        response = self.model.generate(prompt=prompt, messages=messages, **kwargs)
        return [response.content]

    def __call__(self, prompt=None, messages=None, **kwargs):
        return self.forward(prompt=prompt, messages=messages, **kwargs)

    def copy(self, **kwargs):
        new_config = deepcopy(self.model.config)
        new_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
            if key in self.kwargs or not hasattr(self, key):
                new_kwargs[key] = value
        new_model = self.model.__class__(config=new_config)
        return MiproLMWrapper(new_model, **new_kwargs)

    def generate(self, *args, **kwargs):
        return self.model.generate(*args, **kwargs)

    async def async_generate(self, *args, **kwargs):
        return await self.model.async_generate(*args, **kwargs)

def __init__(self, model: BaseLLM, model_type: Literal['chat', 'text']='chat', temperature: float=0.0, max_tokens: int=4000, cache: bool=True, cache_in_memory: bool=True, callbacks: Optional[List[BaseCallback]]=None, num_retries: int=3, provider=None, finetuning_model: Optional[str]=None, launch_kwargs: Optional[dict[str, Any]]=None, train_kwargs: Optional[dict[str, Any]]=None, **kwargs):
    self.model = model
    self.model_type = model_type
    self.cache = cache
    self.cache_in_memory = cache_in_memory
    self.callbacks = callbacks or []
    self.history = []
    self.provider = provider or Provider()
    self.num_retries = num_retries
    self.finetuning_model = finetuning_model
    self.launch_kwargs = launch_kwargs or {}
    self.train_kwargs = train_kwargs or {}
    self.kwargs = dict(temperature=temperature, max_tokens=max_tokens, **kwargs)

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

class OptimizeParam:
    """
    Class-based decorator for registering tunable optimization parameters.

    Supports:
    - Decorating functions with parameters and optional execution callbacks.
    - Functions without parameters can be registered for execution callbacks only.
    - Automatic deduplication and selective parameter registration.
    """
    _targets: List[Tuple[Callable, List[str], Optional[Callable]]] = []

    def __init__(self, *params: str, on_execute: Optional[Callable]=None):
        """
        :param params: parameter paths to register (optional)
        :param on_execute: optional callback triggered when the decorated function executes,
                           signature: callback(func: Callable, *args, **kwargs)
        """
        self.param_names = list(params)
        self.on_execute = on_execute

    def __call__(self, func: Callable):
        self._targets = [t for t in self._targets if t[0] != func]

        def wrapped_func(*args, **kwargs):
            if self.on_execute:
                self.on_execute(func, *args, **kwargs)
            return func(*args, **kwargs)
        self._targets.append((wrapped_func, self.param_names, self.on_execute))
        return wrapped_func

    @classmethod
    def register_all(cls, program_instance: Any, registry: ParamRegistry, verbose: bool=False):
        """
        Register all decorated functions' parameters on the given program instance.
        Functions without parameter paths are skipped for parameter registration.
        """
        seen = set(registry.names())
        for _, param_names, _ in cls._targets:
            if not param_names:
                continue
            for name in param_names:
                if name in seen:
                    if verbose:
                        print(f'[OptParam] Skipped already registered: {name}')
                else:
                    seen.add(name)
                    registry.track(program_instance, name)
                    if verbose:
                        print(f'[OptParam] Registered from decorator: {name}')

    @classmethod
    def get_all(cls) -> List[Tuple[Callable, List[str], Optional[Callable]]]:
        """Return all decorated functions along with their parameters and callbacks."""
        return cls._targets

    @classmethod
    def get_decorated_functions(cls) -> List[Callable]:
        """Return all wrapped decorated functions."""
        return [t[0] for t in cls._targets]

    @classmethod
    def get_params_for_func(cls, func: Callable) -> List[str]:
        """Return the list of parameter paths registered for a specific function."""
        for f, params, _ in cls._targets:
            if f == func:
                return params
        return []

def __init__(self, *params: str, on_execute: Optional[Callable]=None):
    """
        :param params: parameter paths to register (optional)
        :param on_execute: optional callback triggered when the decorated function executes,
                           signature: callback(func: Callable, *args, **kwargs)
        """
    self.param_names = list(params)
    self.on_execute = on_execute

class ParamRegistry:
    """
    Central registry for all parameters that can be exposed to optimization.

    Allows dynamic binding and tracking of runtime attributes via dot-paths,
    dictionary keys, or list indices. Provides getter/setter access to all
    registered parameters for optimizers.
    """

    def __init__(self) -> None:
        """Initialize an empty registry of optimizable fields."""
        self.fields: Dict[str, OptimizableField] = {}

    def register_field(self, field: OptimizableField):
        """Manually register an OptimizableField with its alias name."""
        field.init_snapshot()
        self.fields[field.name] = field

    def get(self, name: str) -> Any:
        """Retrieve the current value of a registered field by name."""
        return self.fields[name].get()

    def get_field(self, name: str) -> OptimizableField:
        """Retrieve the OptimizableField object by name."""
        if name not in self.fields:
            raise ValueError(f"Field '{name}' is not registered.")
        else:
            return self.fields[name]

    def set(self, name: str, value: Any):
        """Set the value of a registered field by name."""
        self.fields[name].set(value)

    def names(self) -> List[str]:
        """Return a list of all registered field names (aliases)."""
        return list(self.fields.keys())

    def reset(self):
        """Roll back all registered fields to their initial values."""
        for field in self.fields.values():
            field.reset()

    def reset_field(self, name: str):
        """Roll back a registered field to its initial value."""
        self.fields[name].reset()

    def track(self, root_or_obj: Any, path_or_attr: str, *, name: str | None=None):
        """
        Register a parameter to be optimized. Supports both nested paths and direct attributes.

        Parameters:
        - root_or_obj (Any): the base object or container
        - path_or_attr (str): a path like 'prompt.template' or a direct attribute like 'template'
        - name (str | None): optional alias for this parameter

        Supported formats:
        - registry.track(program, "prompt.template")              # nested attribute
        - registry.track(program, "metadata['style']")           # dictionary key
        - registry.track(program, "components[2].prefix")        # list index
        - registry.track(program.prompt, "template")             # direct object + attribute
        - registry.track([
            (program, "prompt.template"),
            (program, "metadata['style']", "style"),
            (program.prompt, "prefix", "prompt_prefix")
          ])                                                    # batch registration
        - registry.track(program, "prompt.template").track(program, "prompt.prefix")  # chained calls
        
        - registry.track(program, "prompt_template_obj")  # register a prompt_template instance

        Returns:
        - self (PromptRegistry): for chaining
        """
        if isinstance(root_or_obj, list | tuple):
            for item in root_or_obj:
                if len(item) == 2:
                    self.track(item[0], item[1])
                elif len(item) == 3:
                    self.track(item[0], item[1], name=item[2])
            return self
        if '.' in path_or_attr or '[' in path_or_attr:
            return self._track_path(root_or_obj, path_or_attr, name)
        else:
            key = name or path_or_attr

            def getter():
                return getattr(root_or_obj, path_or_attr)

            def setter(v):
                setattr(root_or_obj, path_or_attr, v)
            field = OptimizableField(key, getter, setter)
            if key in self.fields:
                import warnings
                warnings.warn(f"Field '{key}' is already registered. Overwriting.")
            self.register_field(field)
            return self

    def _track_path(self, root: Any, path: str, name: str | None=None):
        """
        Internal helper that registers a nested field (via dot path, index, or key)
        as an OptimizableField by dynamically creating getter and setter functions.

        Parameters:
        - root (Any): the root object to start walking from
        - path (str): dot-separated path supporting list/dict access
        - name (Optional[str]): alias for the parameter (defaults to last path segment)

        Returns:
        - self
        """
        key = name if name is not None else path
        parent, leaf = self._walk(root, path)

        def getter():
            return parent[leaf] if isinstance(parent, (list, dict)) else getattr(parent, leaf)

        def setter(v):
            if isinstance(parent, (list, dict)):
                parent[leaf] = v
            else:
                setattr(parent, leaf, v)
        field = OptimizableField(key, getter, setter)
        self.register_field(field)
        return self

    def _walk(self, root, path: str):
        """
        Internal helper to resolve a dot-separated path string into its parent container
        and the leaf attribute/key/index for assignment or retrieval.

        Supports:
        - Nested attributes: e.g. "a.b.c"
        - Dict key access: e.g. "config['key']"
        - List index access: e.g. "layers[0]"

        Parameters:
        - root (Any): root object to walk from
        - path (str): path string to resolve
        - create_missing (bool): unused placeholder for future extensions

        Returns:
        - (parent, leaf): where parent[leaf] or getattr(parent, leaf) is the target
        """
        cur = root
        parts = []
        for match in _PATH_RE.finditer(path):
            attr, idx, key = match.groups()
            if attr:
                parts.append(attr)
            elif idx:
                parts.append(int(idx))
            elif key:
                parts.append(key)
        for part in parts[:-1]:
            if isinstance(part, int):
                cur = cur[part]
            else:
                cur = getattr(cur, part) if hasattr(cur, part) else cur[part]
        leaf = parts[-1]
        parent = cur
        return (parent, leaf)

    def _walk_old(self, root, path: str):
        """
        Unused Function
        Internal helper to resolve a dot-separated path string into its parent container
        and the leaf attribute/key/index for assignment or retrieval.

        Supports:
        - Nested attributes: e.g. "a.b.c"
        - Dict key access: e.g. "config['key']"
        - List index access: e.g. "layers[0]"

        Parameters:
        - root (Any): root object to walk from
        - path (str): path string to resolve
        - create_missing (bool): unused placeholder for future extensions

        Returns:
        - (parent, leaf): where parent[leaf] or getattr(parent, leaf) is the target
        """
        cur = root
        parts = path.split('.')
        for part in parts[:-1]:
            m = _INDEX_RE.match(part)
            if m:
                attr, idx = m.groups()
                cur = getattr(cur, attr) if attr else cur
                idx = idx.strip()
                if idx.startswith("'") and idx.endswith("'") or (idx.startswith('"') and idx.endswith('"')):
                    idx = idx[1:-1]
                elif idx.isdigit():
                    idx = int(idx)
                cur = cur[idx]
            else:
                cur = getattr(cur, part)
        leaf = parts[-1]
        m = _INDEX_RE.match(leaf)
        if m:
            attr, idx = m.groups()
            parent = getattr(cur, attr) if attr else cur
            idx = idx.strip()
            if idx.startswith("'") and idx.endswith("'") or (idx.startswith('"') and idx.endswith('"')):
                idx = idx[1:-1]
            elif idx.isdigit():
                idx = int(idx)
            return (parent, idx)
        return (cur, leaf)

def names(self) -> List[str]:
    """Return a list of all registered field names (aliases)."""
    return list(self.fields.keys())

class RAGEngine:

    def __init__(self, config: RAGConfig, storage_handler: StorageHandler, llm: Optional[BaseLLM]=None):
        self.config = config
        self.storage_handler = storage_handler
        self.embedding_factory = EmbeddingFactory()
        self.index_factory = IndexFactory()
        self.chunk_factory = ChunkFactory()
        self.retriever_factory = RetrieverFactory()
        self.postprocessor_factory = PostprocessorFactory()
        self.llm = llm
        logger.info(f'RAGEngine modality config: {self.config.modality}')
        if self.config.modality == 'multimodal':
            self.chunk_class = ImageChunk
        else:
            self.chunk_class = TextChunk
        if self.config.modality == 'multimodal':
            self.reader = MultimodalReader(recursive=self.config.reader.recursive, exclude_hidden=self.config.reader.exclude_hidden, num_files_limits=self.config.reader.num_files_limit, errors=self.config.reader.errors)
        else:
            self.reader = LLamaIndexReader(recursive=self.config.reader.recursive, exclude_hidden=self.config.reader.exclude_hidden, num_workers=self.config.num_workers, num_files_limits=self.config.reader.num_files_limit, custom_metadata_function=self.config.reader.custom_metadata_function, extern_file_extractor=self.config.reader.extern_file_extractor, errors=self.config.reader.errors, encoding=self.config.reader.encoding)
        self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
        if self.storage_handler.vector_store is not None and self.embed_model.dimensions is not None:
            if self.storage_handler.storageConfig.vectorConfig.dimensions != self.embed_model.dimensions:
                logger.warning('The dimensions in vector_store is not equal with embed_model. Reiniliaze vector_store.')
                self.storage_handler.storageConfig.vectorConfig.dimensions = self.embed_model.dimensions
                self.storage_handler._init_vector_store()
        if self.config.modality == 'multimodal':
            self.chunker = None
        else:
            self.chunker = self.chunk_factory.create(strategy=self.config.chunker.strategy, embed_model=self.embed_model.get_embedding_model(), chunker_config={'chunk_size': self.config.chunker.chunk_size, 'chunk_overlap': self.config.chunker.chunk_overlap, 'max_chunks': self.config.chunker.max_chunks})
        self.indices: Dict[str, Dict[str, BaseIndexWrapper]] = {}
        self.retrievers: Dict[str, Dict[str, BaseRetrieverWrapper]] = {}

    def read(self, file_paths: Union[Sequence[str], str], exclude_files: Optional[Union[str, List, Tuple, Sequence]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple, Sequence]]=None, merge_by_file: bool=False, show_progress: bool=False, corpus_id: str=None) -> Corpus:
        """Load and chunk documents from files.

        Reads files from specified paths, processes them into documents, and chunks them into a Corpus.

        Args:
            file_paths (Union[Sequence[str], str]): Path(s) to files or directories.
            exclude_files (Optional[Union[str, List, Tuple, Sequence]]): Files to exclude.
            filter_file_by_suffix (Optional[Union[str, List, Tuple, Sequence]]): Filter files by suffix (e.g., '.pdf').
            merge_by_file (bool): Merge documents by file.
            show_progress (bool): Show loading progress.
            corpus_id (Optional[str]): Identifier for the corpus. Defaults to a UUID if None.

        Returns:
            Corpus: The chunked corpus containing processed document chunks.

        Raises:
            Exception: If document reading or chunking fails.
        """
        try:
            corpus_id = corpus_id or str(uuid4())
            documents = self.reader.load(file_paths=file_paths, exclude_files=exclude_files, filter_file_by_suffix=filter_file_by_suffix, merge_by_file=merge_by_file, show_progress=show_progress)
            if self.config.modality == 'multimodal':
                image_chunks = []
                for doc in documents:
                    image_path = getattr(doc, 'image_path', None) or doc.metadata.get('file_path')
                    image_mimetype = getattr(doc, 'image_mimetype', None)
                    image_chunk = self.chunk_class(image_path=image_path, image_mimetype=image_mimetype, chunk_id=doc.metadata.get('file_name', f'img_{len(image_chunks)}'), metadata=ChunkMetadata(doc_id=doc.metadata.get('file_name', f'doc_{len(image_chunks)}'), corpus_id=corpus_id, **doc.metadata))
                    image_chunks.append(image_chunk)
                corpus = Corpus(chunks=image_chunks, corpus_id=corpus_id)
                logger.info(f'Read {len(documents)} multimodal documents (no chunking) for corpus {corpus_id}')
            else:
                corpus = self.chunker.chunk(documents)
                corpus.corpus_id = corpus_id
                logger.info(f'Read {len(documents)} documents and created {len(corpus.chunks)} chunks for corpus {corpus_id}')
            return corpus
        except Exception as e:
            logger.error(f'Failed to read documents for corpus {corpus_id}: {str(e)}')
            raise

    def add(self, index_type: str, nodes: Union[Corpus, List[NodeWithScore], List[TextNode], List[ImageNode]], corpus_id: str=None) -> None:
        """Add nodes to an index for a specific corpus.

        Initializes an index if it doesn't exist and inserts nodes, updating metadata with corpus_id and index_type.

        Args:
            index_type (str): Type of index (e.g., VECTOR, GRAPH).
            nodes (Union[Corpus, List[NodeWithScore], List[TextNode]]): Nodes or Corpus to add.
            corpus_id (str, optional): Identifier for the corpus. Defaults to a UUID if None.

        Return:
            return a sequence with id of each added node.
            
        Raises:
            Exception: If index creation or node insertion fails.
        """
        try:
            corpus_id = corpus_id or str(uuid4())
            if corpus_id not in self.indices:
                self.indices[corpus_id] = {}
                self.retrievers[corpus_id] = {}
            if index_type not in self.indices[corpus_id]:
                index = self.index_factory.create(index_type=index_type, embed_model=self.embed_model.get_embedding_model(), storage_handler=self.storage_handler, index_config=self.config.index.model_dump(exclude_unset=True) if self.config.index else {}, llm=self.llm)
                self.indices[corpus_id][index_type] = index
                self.retrievers[corpus_id][index_type] = self.retriever_factory.create(retriever_type=self.config.retrieval.retrivel_type, llm=self.llm, index=index.get_index(), graph_store=index.get_index().storage_context.graph_store, embed_model=self.embed_model.get_embedding_model(), query=Query(query_str='', top_k=self.config.retrieval.top_k if self.config.retrieval else 5), storage_handler=self.storage_handler, chunk_class=self.chunk_class)
            nodes_to_insert = nodes.to_llama_nodes() if isinstance(nodes, Corpus) else nodes
            for node in nodes_to_insert:
                node.metadata.update({'corpus_id': corpus_id, 'index_type': index_type})
            nodes_ids = self.indices[corpus_id][index_type].insert_nodes(nodes_to_insert)
            logger.info(f'Added {len(nodes_to_insert)} nodes to {index_type} index for corpus {corpus_id}')
            return nodes_ids
        except Exception as e:
            logger.error(f'Failed to add nodes to {index_type} index for corpus {corpus_id}: {str(e)}')
            return []

    def delete(self, corpus_id: str, index_type: Optional[str]=None, node_ids: Optional[Union[str, List[str]]]=None, metadata_filters: Optional[Dict[str, Any]]=None) -> None:
        """Delete nodes or an entire index from a corpus.

        Removes specific nodes by ID or metadata filters, or deletes the entire index if no filters are provided.

        Args:
            corpus_id (str): Identifier for the corpus.
            index_type (Optional[IndexType]): Specific index type to delete from. If None, affects all indices.
            node_ids (Union[str, Optional[List[str]]]): List of node IDs to delete.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion.

        Raises:
            Exception: If deletion fails.
        """
        try:
            if corpus_id not in self.indices:
                logger.warning(f'No indices found for corpus {corpus_id}')
                return
            target_indices = [index_type] if index_type else self.indices[corpus_id].keys()
            for idx_type in list(target_indices):
                if idx_type not in self.indices[corpus_id]:
                    logger.warning(f'Index type {idx_type} not found for corpus {corpus_id}')
                    continue
                index = self.indices[corpus_id][idx_type]
                if node_ids or metadata_filters:
                    node_ids_list = [node_ids] if isinstance(node_ids, str) else node_ids
                    index.delete_nodes(node_ids=node_ids_list, metadata_filters=metadata_filters)
                    logger.info(f'Deleted nodes from {idx_type} index for corpus {corpus_id}')
                else:
                    index.clear()
                    del self.indices[corpus_id][idx_type]
                    del self.retrievers[corpus_id][idx_type]
                    logger.info(f'Deleted entire {idx_type} index for corpus {corpus_id}')
            if not self.indices[corpus_id]:
                del self.indices[corpus_id]
                del self.retrievers[corpus_id]
                logger.info(f'Removed empty corpus {corpus_id}')
        except Exception as e:
            logger.error(f'Failed to delete from corpus {corpus_id}, index {index_type}: {str(e)}')
            raise

    def clear(self, corpus_id: Optional[str]=None) -> None:
        """Clear all indices for a specific corpus or all corpora.

        Args:
            corpus_id (Optional[str]): Specific corpus to clear. If None, clears all corpora.

        Raises:
            Exception: If clearing fails.
        """
        try:
            target_corpora = [corpus_id] if corpus_id else list(self.indices.keys())
            for cid in target_corpora:
                if cid not in self.indices:
                    logger.warning(f'No indices found for corpus {cid}')
                    continue
                for idx_type in list(self.indices[cid].keys()):
                    index = self.indices[cid][idx_type]
                    index.clear()
                    del self.indices[cid][idx_type]
                    del self.retrievers[cid][idx_type]
                    logger.info(f'Cleared {idx_type} index for corpus {cid}')
                del self.indices[cid]
                del self.retrievers[cid]
                logger.info(f'Cleared corpus {cid}')
        except Exception as e:
            logger.error(f'Failed to clear indices for corpus {corpus_id or 'all'}: {str(e)}')
            raise

    def save(self, output_path: Optional[str]=None, corpus_id: Optional[str]=None, index_type: Optional[str]=None, table: Optional[str]=None, graph_exported: bool=False) -> None:
        """Save indices to files or database.

        Serializes corpus chunks to JSONL files and metadata to JSON files if output_path is provided,
        or saves to the SQLite database via StorageHandler if output_path is None.

        Args:
            output_path (Optional[str]): Directory to save JSONL and JSON files. If None, saves to database.
            corpus_id (Optional[str]): Specific corpus to save. If None, saves all corpora.
            index_type (Optional[str]): Specific index type to save. If None, saves all indices.
            table (Optional[str]): Database table name for index data. Defaults to 'indexing' if None.
            graph_exported (bool): If True, export graph nodes and relations for graph indices. Defaults to False.

        Raises:
            Exception: If saving fails or file operations encounter errors.
        """
        try:
            target_corpora = [corpus_id] if corpus_id else list(self.indices.keys())
            table = table or 'indexing'
            for cid in target_corpora:
                if cid not in self.indices:
                    logger.warning(f'No indices found for corpus {cid}')
                    continue
                target_indices = [index_type] if index_type and index_type in self.indices[cid] else self.indices[cid].keys()
                for idx_type in target_indices:
                    index = self.indices[cid][idx_type]
                    if idx_type == IndexType.GRAPH and (not graph_exported):
                        logger.warning(f'Skipping save for graph index {idx_type} in corpus {cid} as graph_exported is False')
                        continue
                    if idx_type == IndexType.GRAPH and graph_exported:
                        index.build_kv_store()
                    chunks = [self.chunk_class.from_llama_node(node_data) for node_id, node_data in index.id_to_node.items()]
                    corpus = Corpus(chunks=chunks, corpus_id=cid)
                    vector_config = self.storage_handler.storageConfig.vectorConfig.model_dump() if self.storage_handler.storageConfig.vectorConfig else {}
                    graph_config = self.storage_handler.storageConfig.graphConfig.model_dump() if self.storage_handler.storageConfig.graphConfig else {}
                    metadata = IndexMetadata(corpus_id=cid, index_type=idx_type, collection_name=vector_config.get('qdrant_collection_name', 'default_collection'), dimension=self.embed_model.dimensions, vector_db_type=vector_config.get('vector_name', None), graph_db_type=graph_config.get('graph_name', None), embedding_model_name=self.config.embedding.model_name, date=str(datetime.now()))
                    if output_path:
                        os.makedirs(output_path, exist_ok=True)
                        safe_cid = ''.join((c if c.isalnum() or c in ['-', '_'] else '_' for c in cid))
                        safe_idx_type = ''.join((c if c.isalnum() or c in ['-', '_'] else '_' for c in idx_type))
                        nodes_file = os.path.join(output_path, f'{safe_cid}_{safe_idx_type}_nodes.jsonl')
                        metadata_file = os.path.join(output_path, f'{safe_cid}_{safe_idx_type}_metadata.json')
                        corpus.to_jsonl(nodes_file, indent=0)
                        logger.info(f'Saved {len(corpus.chunks)} chunks to {nodes_file}')
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)
                        logger.info(f'Saved metadata to {metadata_file}')
                    else:
                        index_data = {'corpus_id': cid, 'content': corpus.model_dump(), 'date': str(datetime.now()), 'metadata': metadata.model_dump()}
                        self.storage_handler.save_index(index_data, table=table)
                        logger.info(f'Saved {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} to database table {table}')
        except Exception as e:
            logger.error(f'Failed to save indices for corpus {corpus_id or 'all'}: {str(e)}')
            raise

    def load(self, source: Optional[str]=None, corpus_id: Optional[str]=None, index_type: Optional[str]=None, table: Optional[str]=None) -> None:
        """Load indices from files or database.

        Reconstructs indices and retrievers from JSONL/JSON files or SQLite database records.
        Validates the embedding model name and dimension before reinitializing the embedding model.

        Args:
            source (Optional[str]): Directory containing JSONL/JSON files. If None, loads from database.
            corpus_id (Optional[str]): Specific corpus to load. If None, loads all corpora.
            index_type (Optional[str]): Specific index type to load. If None, loads all indices.
            table (Optional[str]): Database table name for index data. Defaults to 'indexing' if None.

        Returns:
            The Sequence with id of loaded chunk.
        
        Raises:
            Exception: If loading fails due to file or database errors, invalid data, or unsupported embedding model/dimension.
        
        Warning:
            Try to call this function may cause some Bugs, when you load the nodes from file or database storage systems at twice. 
            Because All the indexing share the same storage backend from storageHandler.
            For example:
            The vector database (.e.g Faiss) can insert again, even thougt there is a same node.
        """
        try:
            table = table or 'indexing'
            config_dimension = self.storage_handler.storageConfig.vectorConfig.dimensions
            loaded_chunk_ids: List[str] = []
            if source:
                if not os.path.exists(source):
                    logger.error(f'Source directory {source} does not exist')
                    raise FileNotFoundError(f'Source directory {source} does not exist')
                for file_name in os.listdir(source):
                    if not file_name.endswith('_metadata.json'):
                        continue
                    parts = file_name.split('_')
                    if len(parts) < 3:
                        logger.warning(f'Skipping invalid metadata file: {file_name}')
                        continue
                    cid = '_'.join(parts[:-2])
                    idx_type = parts[-2]
                    if corpus_id and corpus_id != cid or (index_type and index_type != idx_type):
                        continue
                    metadata_file = os.path.join(source, file_name)
                    nodes_file = os.path.join(source, f'{cid}_{idx_type}_nodes.jsonl')
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = IndexMetadata.model_validate(json.load(f))
                    if not self.embed_model.validate_model(self.config.embedding.provider, metadata.embedding_model_name):
                        raise ValueError(f"Embedding model '{metadata.embedding_model_name}' is not supported by provider '{self.config.embedding.provider}'. Supported models: {EmbeddingProvider.SUPPORTED_MODELS.get(self.config.embedding.provider, [])}")
                    if metadata.dimension != config_dimension:
                        raise ValueError(f'Embedding dimension {metadata.dimension} in metadata does not match configured dimension {config_dimension}.')
                    if not os.path.exists(nodes_file):
                        logger.warning(f'Nodes file {nodes_file} not found for metadata {metadata_file}')
                        continue
                    corpus = Corpus.from_jsonl(nodes_file, corpus_id=cid)
                    if metadata.embedding_model_name != self.config.embedding.model_name:
                        logger.info(f'Reinitializing embedding model to {metadata.embedding_model_name}')
                        self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
                    chunk_ids = self._load_index(corpus, cid, idx_type)
                    loaded_chunk_ids.extend(chunk_ids)
                    logger.info(f'Loaded {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} from {nodes_file}')
            else:
                records = self.storage_handler.load(tables=[table]).get(table, [])
                if not records:
                    logger.warning(f'No records found in table {table}')
                    return
                for record in records:
                    parsed = self.storage_handler.parse_result(record, IndexStore)
                    cid = parsed['corpus_id']
                    idx_type = parsed['metadata']['index_type']
                    if corpus_id and corpus_id != cid or (index_type and index_type != idx_type):
                        continue
                    chunks = []
                    for chunk_data in parsed['content']['chunks']:
                        metadata = ChunkMetadata.model_validate(chunk_data['metadata'])
                        if self.config.modality == 'multimodal':
                            chunk = ImageChunk(chunk_id=chunk_data['chunk_id'], image_path=chunk_data['image_path'], image_mimetype=chunk_data.get('image_mimetype'), metadata=metadata, embedding=chunk_data['embedding'], excluded_embed_metadata_keys=chunk_data['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_data['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_data['relationships'].items()})
                        else:
                            chunk = TextChunk(chunk_id=chunk_data['chunk_id'], text=chunk_data['text'], metadata=metadata, embedding=chunk_data['embedding'], start_char_idx=chunk_data['start_char_idx'], end_char_idx=chunk_data['end_char_idx'], excluded_embed_metadata_keys=chunk_data['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_data['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_data['relationships'].items()})
                        chunks.append(chunk)
                    corpus = Corpus(chunks=chunks, corpus_id=cid, metadata=IndexMetadata.model_validate(parsed['metadata']))
                    metadata = IndexMetadata.model_validate(parsed['metadata'])
                    if not self.embed_model.validate_model(self.config.embedding.provider, metadata.embedding_model_name):
                        raise ValueError(f"Embedding model '{metadata.embedding_model_name}' is not supported by provider '{self.config.embedding.provider}'. Supported models: {EmbeddingProvider.SUPPORTED_MODELS.get(self.config.embedding.provider, [])}")
                    if metadata.dimension != config_dimension:
                        raise ValueError(f'Embedding dimension {metadata.dimension} in metadata does not match configured dimension {config_dimension}.')
                    if metadata.embedding_model_name != self.config.embedding.model_name:
                        logger.info(f'Reinitializing embedding model to {metadata.embedding_model_name}')
                        self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
                    chunk_ids = self._load_index(corpus, cid, idx_type)
                    loaded_chunk_ids.extend(chunk_ids)
                    logger.info(f'Loaded {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} from database table {table}')
            return loaded_chunk_ids
        except Exception as e:
            logger.error(f'Failed to load indices: {str(e)}')
            raise

    def _load_index(self, corpus: Corpus, corpus_id: str, index_type: str) -> Sequence[str]:
        """Helper method to load an index and its retriever."""
        try:
            if corpus_id not in self.indices:
                self.indices[corpus_id] = {}
                self.retrievers[corpus_id] = {}
            if index_type not in self.indices[corpus_id]:
                index = self.index_factory.create(index_type=index_type, embed_model=self.embed_model.get_embedding_model(), storage_handler=self.storage_handler, index_config=self.config.index.model_dump(exclude_unset=True) if self.config.index else {}, llm=self.llm)
                self.indices[corpus_id][index_type] = index
                retriever_type = RetrieverType.GRAPH if index_type == IndexType.GRAPH else RetrieverType.VECTOR
                self.retrievers[corpus_id][index_type] = self.retriever_factory.create(retriever_type=retriever_type, llm=self.llm, index=index.get_index(), graph_store=index.get_index().storage_context.graph_store, embed_model=self.embed_model.get_embedding_model(), query=Query(query_str='', top_k=self.config.retrieval.top_k if self.config.retrieval else 5), storage_handler=self.storage_handler)
            nodes = corpus.to_llama_nodes()
            for node in nodes:
                node.metadata.update({'corpus_id': corpus_id, 'index_type': index_type})
            chunk_ids = self.indices[corpus_id][index_type].load(nodes)
            logger.info(f'Inserted {len(nodes)} nodes into {index_type} index for corpus {corpus_id}')
            return chunk_ids
        except Exception as e:
            logger.error(f'Failed to load index for corpus {corpus_id}, index_type {index_type}: {str(e)}')
            raise

    async def aget(self, corpus_id: str, index_type: str, node_ids: List[str]) -> List[Union[TextChunk, ImageChunk]]:
        """Retrieve chunks by node_ids from the index."""
        try:
            chunks = await self.indices[corpus_id][index_type].get(node_ids=node_ids)
            logger.info(f'Retrieved {len(chunks)} chunks for node_ids: {node_ids}')
            return chunks
        except Exception as e:
            logger.error(f'Failed to get chunks: {str(e)}')
            return []

    async def query_async(self, query: Union[str, Query], corpus_id: Optional[str]=None, query_transforms: Optional[List]=None) -> RagResult:
        """Execute a query across indices and return processed results asynchronously.

        Performs query preprocessing, asynchronous retrieval, and post-processing.

        Args:
            query (Union[str, Query]): Query string or Query object.
            corpus_id (Optional[str]): Specific corpus to query. If None, queries all corpora.
            query_transforms (Optional[List]): Query Transforms is used to augment query in pre-processing.

        Returns:
            RagResult: Retrieved chunks with scores and metadata.

        Raises:
            Exception: If query processing fails.
        """
        try:
            if isinstance(query, str):
                query = Query(query_str=query, top_k=self.config.retrieval.top_k)
            if not self.indices or (corpus_id and corpus_id not in self.indices):
                logger.warning(f'No indices found for corpus {corpus_id or 'any'}')
                return RagResult(corpus=Corpus(chunks=[]), scores=[], metadata={'query': query.query_str})
            if query_transforms and query_transforms is not None:
                for t in query_transforms:
                    query = t(query)
            results = []
            target_corpora = [corpus_id] if corpus_id else self.indices.keys()
            tasks = []
            for cid in target_corpora:
                for idx_type, retriever in self.retrievers[cid].items():
                    if query.metadata_filters and query.metadata_filters.get('index_type') and (query.metadata_filters['index_type'] != idx_type):
                        continue
                    task = retriever.aretrieve(Query(query_str=query.query_str, top_k=query.top_k or self.config.retrieval.top_k, similarity_cutoff=query.similarity_cutoff, keyword_filters=query.keyword_filters, metadata_filters=query.metadata_filters))
                    tasks.append((task, cid, idx_type))
            retrieval_tasks = [task for task, _, _ in tasks]
            retrieval_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
            for (_, cid, idx_type), result in zip(tasks, retrieval_results):
                if isinstance(result, Exception):
                    logger.error(f'Retrieval failed for {idx_type} in corpus {cid}: {str(result)}')
                else:
                    results.append(result)
                    logger.info(f'Retrieved {len(result.corpus.chunks)} chunks from {idx_type} retriever for corpus {cid}')
            if not results:
                return RagResult(corpus=Corpus(chunks=[]), scores=[], metadata={'query': query.query_str})
            query.similarity_cutoff = self.config.retrieval.similarity_cutoff if query.similarity_cutoff is None else query.similarity_cutoff
            query.keyword_filters = self.config.retrieval.keyword_filters if query.keyword_filters is None else query.keyword_filters
            postprocessor = self.postprocessor_factory.create(self.config.retrieval.postprocessor_type, query=query)
            final_result = postprocessor.postprocess(query, results)
            if query.metadata_filters:
                final_result.corpus.chunks = [chunk for chunk in final_result.corpus.chunks if all((chunk.metadata.model_dump().get(k) == v for k, v in query.metadata_filters.items()))]
                final_result.scores = [chunk.metadata.similarity_score for chunk in final_result.corpus.chunks]
                logger.info(f'Applied metadata filters, retained {len(final_result.corpus.chunks)} chunks')
            logger.info(f'Query returned {len(final_result.corpus.chunks)} chunks after post-processing')
            return final_result
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            raise

    def query(self, query: Union[str, Query], corpus_id: Optional[str]=None, query_transforms: Optional[List]=None) -> RagResult:
        """Synchronous wrapper for the async query method."""
        return asyncio.run(self.query_async(query, corpus_id, query_transforms))

def __init__(self, config: RAGConfig, storage_handler: StorageHandler, llm: Optional[BaseLLM]=None):
    self.config = config
    self.storage_handler = storage_handler
    self.embedding_factory = EmbeddingFactory()
    self.index_factory = IndexFactory()
    self.chunk_factory = ChunkFactory()
    self.retriever_factory = RetrieverFactory()
    self.postprocessor_factory = PostprocessorFactory()
    self.llm = llm
    logger.info(f'RAGEngine modality config: {self.config.modality}')
    if self.config.modality == 'multimodal':
        self.chunk_class = ImageChunk
    else:
        self.chunk_class = TextChunk
    if self.config.modality == 'multimodal':
        self.reader = MultimodalReader(recursive=self.config.reader.recursive, exclude_hidden=self.config.reader.exclude_hidden, num_files_limits=self.config.reader.num_files_limit, errors=self.config.reader.errors)
    else:
        self.reader = LLamaIndexReader(recursive=self.config.reader.recursive, exclude_hidden=self.config.reader.exclude_hidden, num_workers=self.config.num_workers, num_files_limits=self.config.reader.num_files_limit, custom_metadata_function=self.config.reader.custom_metadata_function, extern_file_extractor=self.config.reader.extern_file_extractor, errors=self.config.reader.errors, encoding=self.config.reader.encoding)
    self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
    if self.storage_handler.vector_store is not None and self.embed_model.dimensions is not None:
        if self.storage_handler.storageConfig.vectorConfig.dimensions != self.embed_model.dimensions:
            logger.warning('The dimensions in vector_store is not equal with embed_model. Reiniliaze vector_store.')
            self.storage_handler.storageConfig.vectorConfig.dimensions = self.embed_model.dimensions
            self.storage_handler._init_vector_store()
    if self.config.modality == 'multimodal':
        self.chunker = None
    else:
        self.chunker = self.chunk_factory.create(strategy=self.config.chunker.strategy, embed_model=self.embed_model.get_embedding_model(), chunker_config={'chunk_size': self.config.chunker.chunk_size, 'chunk_overlap': self.config.chunker.chunk_overlap, 'max_chunks': self.config.chunker.max_chunks})
    self.indices: Dict[str, Dict[str, BaseIndexWrapper]] = {}
    self.retrievers: Dict[str, Dict[str, BaseRetrieverWrapper]] = {}

def delete(self, corpus_id: str, index_type: Optional[str]=None, node_ids: Optional[Union[str, List[str]]]=None, metadata_filters: Optional[Dict[str, Any]]=None) -> None:
    """Delete nodes or an entire index from a corpus.

        Removes specific nodes by ID or metadata filters, or deletes the entire index if no filters are provided.

        Args:
            corpus_id (str): Identifier for the corpus.
            index_type (Optional[IndexType]): Specific index type to delete from. If None, affects all indices.
            node_ids (Union[str, Optional[List[str]]]): List of node IDs to delete.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion.

        Raises:
            Exception: If deletion fails.
        """
    try:
        if corpus_id not in self.indices:
            logger.warning(f'No indices found for corpus {corpus_id}')
            return
        target_indices = [index_type] if index_type else self.indices[corpus_id].keys()
        for idx_type in list(target_indices):
            if idx_type not in self.indices[corpus_id]:
                logger.warning(f'Index type {idx_type} not found for corpus {corpus_id}')
                continue
            index = self.indices[corpus_id][idx_type]
            if node_ids or metadata_filters:
                node_ids_list = [node_ids] if isinstance(node_ids, str) else node_ids
                index.delete_nodes(node_ids=node_ids_list, metadata_filters=metadata_filters)
                logger.info(f'Deleted nodes from {idx_type} index for corpus {corpus_id}')
            else:
                index.clear()
                del self.indices[corpus_id][idx_type]
                del self.retrievers[corpus_id][idx_type]
                logger.info(f'Deleted entire {idx_type} index for corpus {corpus_id}')
        if not self.indices[corpus_id]:
            del self.indices[corpus_id]
            del self.retrievers[corpus_id]
            logger.info(f'Removed empty corpus {corpus_id}')
    except Exception as e:
        logger.error(f'Failed to delete from corpus {corpus_id}, index {index_type}: {str(e)}')
        raise

def clear(self, corpus_id: Optional[str]=None) -> None:
    """Clear all indices for a specific corpus or all corpora.

        Args:
            corpus_id (Optional[str]): Specific corpus to clear. If None, clears all corpora.

        Raises:
            Exception: If clearing fails.
        """
    try:
        target_corpora = [corpus_id] if corpus_id else list(self.indices.keys())
        for cid in target_corpora:
            if cid not in self.indices:
                logger.warning(f'No indices found for corpus {cid}')
                continue
            for idx_type in list(self.indices[cid].keys()):
                index = self.indices[cid][idx_type]
                index.clear()
                del self.indices[cid][idx_type]
                del self.retrievers[cid][idx_type]
                logger.info(f'Cleared {idx_type} index for corpus {cid}')
            del self.indices[cid]
            del self.retrievers[cid]
            logger.info(f'Cleared corpus {cid}')
    except Exception as e:
        logger.error(f'Failed to clear indices for corpus {corpus_id or 'all'}: {str(e)}')
        raise

def save(self, output_path: Optional[str]=None, corpus_id: Optional[str]=None, index_type: Optional[str]=None, table: Optional[str]=None, graph_exported: bool=False) -> None:
    """Save indices to files or database.

        Serializes corpus chunks to JSONL files and metadata to JSON files if output_path is provided,
        or saves to the SQLite database via StorageHandler if output_path is None.

        Args:
            output_path (Optional[str]): Directory to save JSONL and JSON files. If None, saves to database.
            corpus_id (Optional[str]): Specific corpus to save. If None, saves all corpora.
            index_type (Optional[str]): Specific index type to save. If None, saves all indices.
            table (Optional[str]): Database table name for index data. Defaults to 'indexing' if None.
            graph_exported (bool): If True, export graph nodes and relations for graph indices. Defaults to False.

        Raises:
            Exception: If saving fails or file operations encounter errors.
        """
    try:
        target_corpora = [corpus_id] if corpus_id else list(self.indices.keys())
        table = table or 'indexing'
        for cid in target_corpora:
            if cid not in self.indices:
                logger.warning(f'No indices found for corpus {cid}')
                continue
            target_indices = [index_type] if index_type and index_type in self.indices[cid] else self.indices[cid].keys()
            for idx_type in target_indices:
                index = self.indices[cid][idx_type]
                if idx_type == IndexType.GRAPH and (not graph_exported):
                    logger.warning(f'Skipping save for graph index {idx_type} in corpus {cid} as graph_exported is False')
                    continue
                if idx_type == IndexType.GRAPH and graph_exported:
                    index.build_kv_store()
                chunks = [self.chunk_class.from_llama_node(node_data) for node_id, node_data in index.id_to_node.items()]
                corpus = Corpus(chunks=chunks, corpus_id=cid)
                vector_config = self.storage_handler.storageConfig.vectorConfig.model_dump() if self.storage_handler.storageConfig.vectorConfig else {}
                graph_config = self.storage_handler.storageConfig.graphConfig.model_dump() if self.storage_handler.storageConfig.graphConfig else {}
                metadata = IndexMetadata(corpus_id=cid, index_type=idx_type, collection_name=vector_config.get('qdrant_collection_name', 'default_collection'), dimension=self.embed_model.dimensions, vector_db_type=vector_config.get('vector_name', None), graph_db_type=graph_config.get('graph_name', None), embedding_model_name=self.config.embedding.model_name, date=str(datetime.now()))
                if output_path:
                    os.makedirs(output_path, exist_ok=True)
                    safe_cid = ''.join((c if c.isalnum() or c in ['-', '_'] else '_' for c in cid))
                    safe_idx_type = ''.join((c if c.isalnum() or c in ['-', '_'] else '_' for c in idx_type))
                    nodes_file = os.path.join(output_path, f'{safe_cid}_{safe_idx_type}_nodes.jsonl')
                    metadata_file = os.path.join(output_path, f'{safe_cid}_{safe_idx_type}_metadata.json')
                    corpus.to_jsonl(nodes_file, indent=0)
                    logger.info(f'Saved {len(corpus.chunks)} chunks to {nodes_file}')
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)
                    logger.info(f'Saved metadata to {metadata_file}')
                else:
                    index_data = {'corpus_id': cid, 'content': corpus.model_dump(), 'date': str(datetime.now()), 'metadata': metadata.model_dump()}
                    self.storage_handler.save_index(index_data, table=table)
                    logger.info(f'Saved {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} to database table {table}')
    except Exception as e:
        logger.error(f'Failed to save indices for corpus {corpus_id or 'all'}: {str(e)}')
        raise

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

def to_llama_document(self) -> LlamaIndexDocument:
    """Convert to LlamaIndex Document."""
    return LlamaIndexDocument(text=self.text, metadata=self.metadata.model_dump(), id_=self.doc_id, embedding=self.embedding, excluded_llm_metadata_keys=self.excluded_llm_metadata_keys, excluded_embed_metadata_keys=self.excluded_embed_metadata_keys, relationships=self.relationships, metadata_template=self.metadata_template, metadata_separator=self.metadata_separator, text_template=self.text_template)

def __str__(self) -> str:
    return f'Document(id={self.doc_id}, embedding={self.embedding}, metadata={self.metadata.model_dump()}fragment={self.get_fragment(max_length=300)})'

def __repr__(self) -> str:
    return f'Document(doc_id={self.doc_id}, embedding={self.embedding}, metadata={self.metadata.model_dump()},fragment={self.get_fragment(max_length=300)})'

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

def to_dict(self) -> Dict:
    """Convert chunk to dictionary for serialization."""
    relationships = dict()
    for k, v in self.relationships.items():
        relationships[k] = v.to_dict() if isinstance(v, RelatedNodeInfo) else v
    self.relationships = relationships
    return self.model_dump()

def __str__(self) -> str:
    return f'Chunk(id={self.chunk_id}, text={self.text}, chunking_strategy={self.metadata.chunking_strategy}, embedding={self.embedding}), start_char_idx={self.start_char_idx}, end_char_idx={self.end_char_idx}, excluded_embed_metadata_keys={self.excluded_embed_metadata_keys},excluded_llm_metadata_keys={self.excluded_llm_metadata_keys},text_template={self.text_template},metadata={self.metadata.model_dump()}'

def __repr__(self) -> str:
    return f'Chunk(id={self.chunk_id}, text={self.text}, chunking_strategy={self.metadata.chunking_strategy}, embedding={self.embedding}), start_char_idx={self.start_char_idx}, end_char_idx={self.end_char_idx}, excluded_embed_metadata_keys={self.excluded_embed_metadata_keys},excluded_llm_metadata_keys={self.excluded_llm_metadata_keys},text_template={self.text_template},metadata={self.metadata.model_dump()}'

class ImageChunk(BaseModule):
    """An image-based chunk with lazy loading.
    
    Attributes:
        image_path (str): Path to the image file.
        image_mimetype (Optional[str]): MIME type of the image.
        chunk_id (str): Unique identifier for the chunk.
        metadata (ChunkMetadata): Metadata including embedding, similarity scores, etc.
    """

    def __init__(self, image_path: str, image_mimetype: Optional[str]=None, chunk_id: Optional[str]=None, embedding: Optional[List[float]]=None, excluded_embed_metadata_keys: List[str]=DEAFULT_EXCLUDED, excluded_llm_metadata_keys: List[str]=DEAFULT_EXCLUDED, text_template: str='{metadata_str}\n\n{content}', relationships: Dict[str, RelatedNodeInfo]={}, metadata: Optional[Union[Dict, ChunkMetadata]]=None):
        metadata = ChunkMetadata.model_validate(metadata) if isinstance(metadata, dict) else metadata or ChunkMetadata()
        super().__init__(image_path=image_path, image_mimetype=image_mimetype, chunk_id=chunk_id or str(uuid4()), embedding=embedding, excluded_embed_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_embed_metadata_keys)), excluded_llm_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_llm_metadata_keys)), text_template=text_template, relationships=relationships, metadata=metadata)
        self._cached_image = None

    def get_image(self):
        """Load PIL Image on-demand with caching."""
        if self._cached_image is None:
            from PIL import Image
            try:
                logger.debug(f'Loading image from path: {self.image_path}')
                if not self.image_path:
                    logger.error('Image path is None or empty!')
                    return None
                self._cached_image = Image.open(self.image_path)
                logger.debug(f'Successfully loaded image from {self.image_path}')
            except Exception as e:
                logger.error(f'Failed to load image from {self.image_path}: {str(e)}')
                return None
        return self._cached_image

    def get_image_bytes(self, format: str='PNG') -> Optional[bytes]:
        """Get image as bytes for embedding or processing."""
        import io
        image = self.get_image()
        if image is None:
            return None
        img_bytes = io.BytesIO()
        image.save(img_bytes, format=format)
        return img_bytes.getvalue()

    def to_llama_node(self) -> ImageNode:
        """Convert to LlamaIndex ImageNode with on-demand image loading."""
        relationships = dict()
        for k, v in self.relationships.items():
            relationships[k] = v if isinstance(v, RelatedNodeInfo) else RelatedNodeInfo.from_dict(v)
        return ImageNode(image=None, image_path=self.image_path, image_mimetype=self.image_mimetype, metadata=self.metadata.model_dump(), id_=self.chunk_id, embedding=self.embedding, excluded_llm_metadata_keys=self.excluded_llm_metadata_keys, excluded_embed_metadata_keys=self.excluded_embed_metadata_keys, text_template=self.text_template, relationships=relationships)

    @classmethod
    def from_llama_node(cls, node: ImageNode) -> 'ImageChunk':
        """Create ImageChunk from LlamaIndex ImageNode."""
        metadata = ChunkMetadata.model_validate(node.metadata)
        logger.debug(f'Creating ImageChunk from ImageNode - image_path: {node.image_path}')
        return cls(chunk_id=node.id_, image_path=node.image_path, image_mimetype=node.image_mimetype, metadata=metadata, embedding=node.embedding, excluded_embed_metadata_keys=node.excluded_embed_metadata_keys, excluded_llm_metadata_keys=node.excluded_llm_metadata_keys, text_template=node.text_template, relationships=node.relationships)

def to_llama_node(self) -> ImageNode:
    """Convert to LlamaIndex ImageNode with on-demand image loading."""
    relationships = dict()
    for k, v in self.relationships.items():
        relationships[k] = v if isinstance(v, RelatedNodeInfo) else RelatedNodeInfo.from_dict(v)
    return ImageNode(image=None, image_path=self.image_path, image_mimetype=self.image_mimetype, metadata=self.metadata.model_dump(), id_=self.chunk_id, embedding=self.embedding, excluded_llm_metadata_keys=self.excluded_llm_metadata_keys, excluded_embed_metadata_keys=self.excluded_embed_metadata_keys, text_template=self.text_template, relationships=relationships)

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

def to_dict(self, round_trip=False) -> Dict:
    """Convert corpus to dictionary for serialization."""
    return [self.model_dump(round_trip=round_trip)]

def __repr__(self) -> str:
    return f'Corpus(chunks={len(self.chunks)}, chunk_index_keys={list(self.chunk_index.keys())})'

class VectorIndexing(BaseIndexWrapper):
    """Wrapper for LlamaIndex VectorStoreIndex."""

    def __init__(self, embed_model: BaseEmbedding, storage_handler: StorageHandler, index_config: Dict[str, Any]=None):
        super().__init__()
        self.index_type = IndexType.VECTOR
        self.embed_model = embed_model
        self.storage_handler = storage_handler
        self._create_storage_context()
        self.id_to_node = dict()
        self.index_config = index_config or {}
        try:
            self.index = VectorStoreIndex(nodes=[], embed_model=self.embed_model, storage_context=self.storage_context, show_progress=self.index_config.get('show_progress', False))
        except Exception as e:
            logger.error(f'Failed to initialize VectorStoreIndex: {str(e)}')
            raise

    def _create_storage_context(self):
        assert self.storage_handler.vector_store is not None, "VectorIndexing must init a vector backend in 'storageHandler'"
        self.storage_context = StorageContext.from_defaults(vector_store=self.storage_handler.vector_store.get_vector_store())

    def get_index(self) -> VectorStoreIndex:
        return self.index

    def insert_nodes(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Insert or update nodes into the vector index.

        Converts Chunk objects to LlamaIndex nodes, serializes metadata as JSON strings, and inserts
        them into the VectorStoreIndex. Nodes are cached in id_to_node for quick access.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to insert, either Chunk or BaseNode.
        
        Returns:

        """
        try:
            filtered_nodes = []
            for node in nodes:
                llama_node = node.to_llama_node() if isinstance(node, Chunk) else node
                node_id = llama_node.id if hasattr(llama_node, 'id') else llama_node.id_
                if node_id in self.id_to_node:
                    self.delete_nodes([node_id])
                    logger.info(f'Find the same node in vector database: {node_id}. Update it.')
                filtered_nodes.extend([llama_node])
            nodes_with_embedding = self.index._get_node_with_embedding(nodes=filtered_nodes)
            for node in nodes_with_embedding:
                self.id_to_node[node.node_id] = node.model_copy()
            self.index.insert_nodes(nodes_with_embedding)
            logger.info(f'Inserted {len(nodes_with_embedding)} nodes into VectorStoreIndex')
            return list([n.node_id for n in filtered_nodes])
        except Exception as e:
            logger.error(f'Failed to insert nodes: {str(e)}')
            return []

    def delete_nodes(self, node_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None) -> None:
        """
        Delete nodes from the vector index based on node IDs or metadata filters.

        Removes specified nodes from the index and the id_to_node cache. If metadata_filters are
        provided, nodes matching the filters are deleted.

        Args:
            node_ids (Optional[List[str]]): List of node IDs to delete. Defaults to None.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion. Defaults to None.
        """
        try:
            if node_ids:
                for node_id in node_ids:
                    if node_id in self.id_to_node:
                        self.index.delete_nodes([node_id], delete_from_docstore=False)
                        if self.index.storage_context.docstore._kvstore._collections_mappings.get(node_id, None) is not None:
                            self.index.storage_context.docstore._kvstore._collections_mappings.pop(node_id)
                        self.id_to_node.pop(node_id)
                        logger.info(f'Deleted node {node_id} from VectorStoreIndex')
            elif metadata_filters:
                nodes_to_delete = []
                for node_id, node in self.id_to_node.items():
                    if all((node.metadata.get(k) == v for k, v in metadata_filters.items())):
                        nodes_to_delete.append(node_id)
                if nodes_to_delete:
                    self.index.delete_nodes(nodes_to_delete, delete_from_docstore=True)
                    for node_id in nodes_to_delete:
                        del self.id_to_node[node_id]
                    logger.info(f'Deleted {len(nodes_to_delete)} nodes matching metadata filters from VectorStoreIndex')
            else:
                logger.warning('No node_ids or metadata_filters provided for deletion')
        except Exception as e:
            logger.error(f'Failed to delete nodes: {str(e)}')
            raise

    async def aload(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Asynchronously load nodes into the vector index and its backend store.

        Caches nodes in id_to_node and loads them into the FAISS vector store, ensuring
        no duplicates are inserted by relying on the backend's duplicate checking.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): The nodes to load.

        Returns:
            chunk_ids (List[str]): The id of loaded chunk.
        """
        try:
            node_ids = self.insert_nodes(nodes)
            return node_ids
        except Exception as e:
            logger.error(f'Failed to load nodes into VectorStoreIndex: {str(e)}')
            raise

    def load(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Synchronously load nodes into the vector index.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): The nodes to load.
        """
        return asyncio.run(self.aload(nodes))

    def clear(self) -> None:
        """
        Clear all nodes from the vector index and its cache.

        Deletes all nodes from the VectorStoreIndex and clears the id_to_node cache.
        """
        try:
            node_ids = list(self.id_to_node.keys())
            self.index.delete_nodes(node_ids, delete_from_docstore=False)
            self.id_to_node.clear()
            self.index.storage_context.docstore._kvstore._collections_mappings.clear()
            logger.info('Cleared all nodes from VectorStoreIndex')
        except Exception as e:
            logger.error(f'Failed to clear index: {str(e)}')
            raise

    async def _get(self, node_id: str) -> Optional[Chunk]:
        """Get a node by node_id from cache or vector store."""
        try:
            node = self.id_to_node.get(node_id, None)
            if node:
                if isinstance(node, Chunk):
                    return node.model_copy()
                return Chunk.from_llama_node(node)
            logger.warning(f'Node with ID {node_id} not found in cache or vector store')
            return None
        except Exception as e:
            logger.error(f'Failed to get node {node_id}: {str(e)}')
            return None

    async def get(self, node_ids: Sequence[str]) -> List[Chunk]:
        """Get nodes by node_ids from cache or vector store."""
        try:
            nodes = await asyncio.gather(*[self._get(node) for node in node_ids])
            nodes = [node for node in nodes if node is not None]
            logger.info(f'Retrieved {len(nodes)} nodes for node_ids: {node_ids}')
            return nodes
        except Exception as e:
            logger.error(f'Failed to get nodes: {str(e)}')
            return []

def delete_nodes(self, node_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None) -> None:
    """
        Delete nodes from the vector index based on node IDs or metadata filters.

        Removes specified nodes from the index and the id_to_node cache. If metadata_filters are
        provided, nodes matching the filters are deleted.

        Args:
            node_ids (Optional[List[str]]): List of node IDs to delete. Defaults to None.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion. Defaults to None.
        """
    try:
        if node_ids:
            for node_id in node_ids:
                if node_id in self.id_to_node:
                    self.index.delete_nodes([node_id], delete_from_docstore=False)
                    if self.index.storage_context.docstore._kvstore._collections_mappings.get(node_id, None) is not None:
                        self.index.storage_context.docstore._kvstore._collections_mappings.pop(node_id)
                    self.id_to_node.pop(node_id)
                    logger.info(f'Deleted node {node_id} from VectorStoreIndex')
        elif metadata_filters:
            nodes_to_delete = []
            for node_id, node in self.id_to_node.items():
                if all((node.metadata.get(k) == v for k, v in metadata_filters.items())):
                    nodes_to_delete.append(node_id)
            if nodes_to_delete:
                self.index.delete_nodes(nodes_to_delete, delete_from_docstore=True)
                for node_id in nodes_to_delete:
                    del self.id_to_node[node_id]
                logger.info(f'Deleted {len(nodes_to_delete)} nodes matching metadata filters from VectorStoreIndex')
        else:
            logger.warning('No node_ids or metadata_filters provided for deletion')
    except Exception as e:
        logger.error(f'Failed to delete nodes: {str(e)}')
        raise

def clear(self) -> None:
    """
        Clear all nodes from the vector index and its cache.

        Deletes all nodes from the VectorStoreIndex and clears the id_to_node cache.
        """
    try:
        node_ids = list(self.id_to_node.keys())
        self.index.delete_nodes(node_ids, delete_from_docstore=False)
        self.id_to_node.clear()
        self.index.storage_context.docstore._kvstore._collections_mappings.clear()
        logger.info('Cleared all nodes from VectorStoreIndex')
    except Exception as e:
        logger.error(f'Failed to clear index: {str(e)}')
        raise

class GraphIndexing(BaseIndexWrapper):
    """Wrapper for LlamaIndex PropertyGraphIndex."""

    def __init__(self, embed_model: BaseEmbedding, storage_handler: StorageHandler, llm: BaseLLM, index_config: Dict[str, Any]=None) -> None:
        super().__init__()
        self.index_type = IndexType.GRAPH
        self._embed_model = embed_model
        self.storage_handler = storage_handler
        self._create_storage_context()
        self.id_to_node = dict()
        self.index_config = index_config or {}
        assert isinstance(llm, BaseLLM), 'The LLM model should be an instance class.'
        kg_extractor = BasicGraphExtractLLM(llm=llm, num_workers=self.index_config.get('num_workers', 4))
        try:
            vector_store = self.storage_handler.vector_store.get_vector_store() if self.storage_handler.vector_store is not None else None
            self.index = PropertyGraphIndex(nodes=[], kg_extractors=[kg_extractor, ImplicitPathExtractor()], embed_model=self._embed_model, vector_store=vector_store if not self.storage_handler.graph_store.supports_vector_queries else None, property_graph_store=self.storage_context.graph_store, storage_context=self.storage_context, show_progress=self.index_config.get('show_progress', False), use_async=self.index_config.get('use_async', True))
        except Exception as e:
            logger.error(f'Failed to initialize {self.__class__}: {str(e)}')
            raise

    def get_index(self) -> PropertyGraphIndex:
        return self.index

    def _create_storage_context(self):
        """Create the LlamaIndex-compatible storage context."""
        super()._create_storage_context()
        assert self.storage_handler.graph_store is not None, "GraphIndexing must init a graph backend in 'storageHandler'"
        self.storage_context = StorageContext.from_defaults(graph_store=self.storage_handler.graph_store.get_graph_store())

    def insert_nodes(self, nodes: List[Union[Chunk, BaseNode]]):
        """
        Insert or update nodes into the graph index.

        Converts Chunk objects to LlamaIndex nodes, serializes metadata as JSON strings,
        and inserts them into the PropertyGraphIndex. Nodes are cached in id_to_node for
        quick access.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to insert, either Chunk or BaseNode.
        """
        try:
            filtered_nodes = [node.to_llama_node() if isinstance(node, Chunk) else node for node in nodes]
            for node in filtered_nodes:
                node.metadata = {'metadata': json.dumps(node.metadata)}
            nodes = self.index._insert_nodes(filtered_nodes)
            logger.info(f'Inserted {len(nodes)} nodes into PropertyGraphIndex')
            return list([node.node_id for node in nodes])
        except Exception as e:
            logger.error(f'Failed to insert nodes: {str(e)}')
            return []

    def delete_nodes(self, node_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None):
        """
        Delete nodes from the graph index based on node IDs or metadata filters.

        Removes specified nodes from the index and the id_to_node cache. If metadata_filters
        are provided, nodes matching the filters are deleted.

        Args:
            node_ids (Optional[List[str]]): List of node IDs to delete. Defaults to None.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion. Defaults to None.
        """
        try:
            if node_ids:
                for node_id in node_ids:
                    if node_id in self.id_to_node:
                        self.index.delete_nodes([node_id])
                        self.id_to_node.pop(node_id)
                        logger.info(f'Deleted node {node_id} from PropertyGraphIndex')
            elif metadata_filters:
                nodes_to_delete = []
                for node_id, node in self.id_to_node.items():
                    if all((node.metadata.get(k) == v for k, v in metadata_filters.items())):
                        nodes_to_delete.append(node_id)
                if nodes_to_delete:
                    self.index.delete_nodes(nodes_to_delete)
                    for node_id in nodes_to_delete:
                        self.id_to_node.pop(node_id)
                    logger.info(f'Deleted {len(nodes_to_delete)} nodes matching metadata filters from PropertyGraphIndex')
            else:
                logger.warning('No node_ids or metadata_filters provided for deletion')
        except Exception as e:
            logger.error(f'Failed to delete nodes: {str(e)}')
            raise

    async def aload(self, nodes: List[Union[Chunk, BaseNode, LabelledNode, Relation, EntityNode, ChunkNode]]) -> Sequence[str]:
        """
        Asynchronously load nodes into the graph index and its backend stores.

        Caches nodes in the id_to_node dictionary and loads them into the graph and optionally
        vector stores, ensuring no duplicates by relying on the backend's duplicate checking.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to load, either Chunk or BaseNode.
        """
        try:
            chunk_ids = self.insert_nodes(nodes)
            return chunk_ids
        except Exception as e:
            logger.error(f'Failed to load nodes: {str(e)}')

    def load(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Synchronously load nodes into the graph index.

        Wraps the asynchronous aload method to provide a synchronous interface for loading nodes.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to load, either Chunk or BaseNode.

        """
        return asyncio.run(self.aload(nodes))

    def build_kv_store(self) -> None:
        """
        Match all the nodes and relations into python Dict.
        """
        for node in self.storage_handler.graph_store.build_kv_store():
            self.id_to_node[str(uuid4())] = node

    def clear(self):
        """
        Clear all nodes from the graph index and its cache.

        Deletes all nodes from the PropertyGraphIndex and clears the id_to_node cache.
        """
        try:
            self.storage_handler.graph_store.clear()
            self.id_to_node.clear()
            logger.info('Cleared all nodes from PropertyGraphIndex')
        except Exception as e:
            logger.error(f'Failed to clear index: {str(e)}')
            raise

    async def _get(self, node_id: str) -> Optional[Chunk]:
        """Get a node by node_id from cache or vector store."""
        try:
            node = self.storage_handler.graph_store.get(ids=[node_id])
            if node:
                if isinstance(node, Chunk):
                    return node.model_copy()
                return Chunk.from_llama_node(node)
            logger.warning(f'Node with ID {node_id} not found in cache or vector store')
            return None
        except Exception as e:
            logger.error(f'Failed to get node {node_id}: {str(e)}')
            return None

    async def get(self, node_ids: Sequence[str]) -> List[Chunk]:
        """Get nodes by node_ids from cache or vector store."""
        try:
            nodes = await asyncio.gather(*[self._get(node) for node in node_ids])
            nodes = [node for node in nodes if node is not None]
            logger.info(f'Retrieved {len(nodes)} nodes for node_ids: {node_ids}')
            return nodes
        except Exception as e:
            logger.error(f'Failed to get nodes: {str(e)}')
            return []

def insert_nodes(self, nodes: List[Union[Chunk, BaseNode]]):
    """
        Insert or update nodes into the graph index.

        Converts Chunk objects to LlamaIndex nodes, serializes metadata as JSON strings,
        and inserts them into the PropertyGraphIndex. Nodes are cached in id_to_node for
        quick access.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to insert, either Chunk or BaseNode.
        """
    try:
        filtered_nodes = [node.to_llama_node() if isinstance(node, Chunk) else node for node in nodes]
        for node in filtered_nodes:
            node.metadata = {'metadata': json.dumps(node.metadata)}
        nodes = self.index._insert_nodes(filtered_nodes)
        logger.info(f'Inserted {len(nodes)} nodes into PropertyGraphIndex')
        return list([node.node_id for node in nodes])
    except Exception as e:
        logger.error(f'Failed to insert nodes: {str(e)}')
        return []

def delete_nodes(self, node_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None):
    """
        Delete nodes from the graph index based on node IDs or metadata filters.

        Removes specified nodes from the index and the id_to_node cache. If metadata_filters
        are provided, nodes matching the filters are deleted.

        Args:
            node_ids (Optional[List[str]]): List of node IDs to delete. Defaults to None.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion. Defaults to None.
        """
    try:
        if node_ids:
            for node_id in node_ids:
                if node_id in self.id_to_node:
                    self.index.delete_nodes([node_id])
                    self.id_to_node.pop(node_id)
                    logger.info(f'Deleted node {node_id} from PropertyGraphIndex')
        elif metadata_filters:
            nodes_to_delete = []
            for node_id, node in self.id_to_node.items():
                if all((node.metadata.get(k) == v for k, v in metadata_filters.items())):
                    nodes_to_delete.append(node_id)
            if nodes_to_delete:
                self.index.delete_nodes(nodes_to_delete)
                for node_id in nodes_to_delete:
                    self.id_to_node.pop(node_id)
                logger.info(f'Deleted {len(nodes_to_delete)} nodes matching metadata filters from PropertyGraphIndex')
        else:
            logger.warning('No node_ids or metadata_filters provided for deletion')
    except Exception as e:
        logger.error(f'Failed to delete nodes: {str(e)}')
        raise

def build_kv_store(self) -> None:
    """
        Match all the nodes and relations into python Dict.
        """
    for node in self.storage_handler.graph_store.build_kv_store():
        self.id_to_node[str(uuid4())] = node

class HierarchicalChunker(BaseChunker):
    """Enhanced hierarchical chunker with dynamic hierarchy level assignment.

    Creates a multi-level hierarchy of chunks with full node relationships:
    - SOURCE: The source document.
    - PREVIOUS/NEXT: Sequential nodes in the document.
    - PARENT/CHILD: Hierarchical relationships.

    Supports custom level parsers or default chunk sizes, with dynamic hierarchy level
    assignment based on node parser IDs. Uses multi-threading and async parsing.

    Attributes:
        level_parsers (Dict[str, BaseChunker]): Custom parsers for each hierarchy level.
        chunk_sizes (List[int]): Chunk sizes for default parsers (e.g., [2048, 512, 128]).
        chunk_overlap (int): Overlap between adjacent chunks.
        parser (HierarchicalNodeParser): LlamaIndex parser for hierarchical chunking.
        include_metadata (bool): Whether to include metadata in nodes.
        include_prev_next_rel (bool): Whether to include previous/next node relationships.
        max_workers (int): Maximum number of threads for parallel processing.
        parser_to_level (Dict[str, int]): Mapping of node_parser_id to hierarchy level.
    """

    def __init__(self, level_parsers: Dict[str, BaseChunker]=None, chunk_sizes: Optional[List[int]]=None, chunk_overlap: int=20, include_metadata: bool=True, include_prev_next_rel: bool=True, max_workers: int=4):
        """Initialize the HierarchicalChunker.

        Args:
            level_parsers (Dict[str, BaseChunker], optional): Custom parsers for hierarchy levels.
            chunk_sizes (List[int], optional): Chunk sizes for default parsers (default: [2048, 512, 128]).
            chunk_overlap (int): Overlap between adjacent chunks (default: 20).
            include_metadata (bool): Include metadata in nodes (default: True).
            include_prev_next_rel (bool): Include prev/next relationships (default: True).
            max_workers (int): Maximum number of threads for parallel processing (default: 4).
        """
        self.level_parsers = level_parsers or {}
        self.chunk_sizes = chunk_sizes or [2048, 512, 128]
        self.chunk_overlap = chunk_overlap
        self.include_metadata = include_metadata
        self.include_prev_next_rel = include_prev_next_rel
        self.max_workers = max_workers
        node_parser_ids = None
        node_parser_map = None
        if not self.level_parsers:
            node_parser_ids = [f'chunk_size_{size}' for size in self.chunk_sizes]
            node_parser_map = {node_id: SimpleChunker(chunk_size=size, chunk_overlap=chunk_overlap, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel).parser for size, node_id in zip(self.chunk_sizes, node_parser_ids)}
        else:
            if chunk_sizes is not None:
                raise ValueError('If level_parsers is provided, chunk_sizes should be None.')
            node_parser_ids = list(self.level_parsers.keys())
            node_parser_map = {k: v.parser for k, v in self.level_parsers.items()}
        self.parser_to_level = {pid: idx + 1 for idx, pid in enumerate(node_parser_ids)}
        self.parser = HierarchicalNodeParser.from_defaults(chunk_sizes=None, chunk_overlap=self.chunk_overlap, node_parser_ids=node_parser_ids, node_parser_map=node_parser_map, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel)

    def _process_document(self, doc: Document, custom_metadata: Dict=None) -> List[Chunk]:
        """Process a single document into chunks in a thread.

        Args:
            doc (Document): The document to chunk.
            custom_metadata (Dict, optional): User-defined metadata for sections.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
        try:
            llama_doc = doc.to_llama_document()
            llama_doc.metadata['doc_id'] = doc.doc_id
            nodes = self.parser.get_nodes_from_documents([llama_doc])
            chunks = []
            for i, node in enumerate(nodes):
                chunk = Chunk.from_llama_node(node)
                chunk.metadata.chunking_strategy = ChunkingStrategy.HIERARCHICAL
                chunks.extend([chunk])
            logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
            return chunks
        except Exception as e:
            logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
            return []

    def chunk(self, documents: List[Document], **kwargs) -> Corpus:
        """Chunk documents using hierarchical strategy with dynamic chunk size adjustment.

        Args:
            documents (List[Document]): List of Document objects to chunk.
            **kwargs: Additional parameters, e.g., custom_metadata for section titles.

        Returns:
            Corpus: A collection of hierarchically organized chunks.
        """
        if not documents:
            logger.info('No documents provided, returning empty Corpus')
            return Corpus(chunks=[])
        chunks = []
        custom_metadata = kwargs.get('custom_metadata', {})
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_doc = {executor.submit(self._process_document, doc, custom_metadata): doc for doc in documents}
            for future in future_to_doc:
                doc = future_to_doc[future]
                try:
                    chunks.extend(future.result())
                except Exception as e:
                    logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
        logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
        return Corpus(chunks=chunks)

def __init__(self, level_parsers: Dict[str, BaseChunker]=None, chunk_sizes: Optional[List[int]]=None, chunk_overlap: int=20, include_metadata: bool=True, include_prev_next_rel: bool=True, max_workers: int=4):
    """Initialize the HierarchicalChunker.

        Args:
            level_parsers (Dict[str, BaseChunker], optional): Custom parsers for hierarchy levels.
            chunk_sizes (List[int], optional): Chunk sizes for default parsers (default: [2048, 512, 128]).
            chunk_overlap (int): Overlap between adjacent chunks (default: 20).
            include_metadata (bool): Include metadata in nodes (default: True).
            include_prev_next_rel (bool): Include prev/next relationships (default: True).
            max_workers (int): Maximum number of threads for parallel processing (default: 4).
        """
    self.level_parsers = level_parsers or {}
    self.chunk_sizes = chunk_sizes or [2048, 512, 128]
    self.chunk_overlap = chunk_overlap
    self.include_metadata = include_metadata
    self.include_prev_next_rel = include_prev_next_rel
    self.max_workers = max_workers
    node_parser_ids = None
    node_parser_map = None
    if not self.level_parsers:
        node_parser_ids = [f'chunk_size_{size}' for size in self.chunk_sizes]
        node_parser_map = {node_id: SimpleChunker(chunk_size=size, chunk_overlap=chunk_overlap, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel).parser for size, node_id in zip(self.chunk_sizes, node_parser_ids)}
    else:
        if chunk_sizes is not None:
            raise ValueError('If level_parsers is provided, chunk_sizes should be None.')
        node_parser_ids = list(self.level_parsers.keys())
        node_parser_map = {k: v.parser for k, v in self.level_parsers.items()}
    self.parser_to_level = {pid: idx + 1 for idx, pid in enumerate(node_parser_ids)}
    self.parser = HierarchicalNodeParser.from_defaults(chunk_sizes=None, chunk_overlap=self.chunk_overlap, node_parser_ids=node_parser_ids, node_parser_map=node_parser_map, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel)

class WorfBench(Benchmark):
    """
    WorfBench evaluation class for assessing LLM agents on complex workflow generation tasks.
    Assumed data structure:
    {
        "id": str,
        "task": str,
        "context": list of dicts (e.g., [{"title": str, "content": list of str}]),
        "expected_output": str or dict (sequence or graph),
        "type": str,
        "level": str
    }
    """

    def __init__(self, path: str=None, mode: str='test', **kwargs):
        path = os.path.expanduser(path or '~/.worfbench/data')
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str) -> Dict:
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_worfbench_data(dataset='worfbench', save_folder=self.path)
        if not os.path.exists(file_path):
            logger.error(f'File {file_path} still does not exist after download attempt!')
            return None
        logger.info(f'Loading WorfBench data from {file_path} ...')
        data = load_json(path=file_path, type='json')
        if data is None:
            logger.error(f'Failed to load data from {file_path}')
            return None
        return data

    def _load_data(self) -> None:
        if self.mode in ['train', 'dev']:
            self._train_data = self._load_data_from_file(file_name=WORFBENCH_FILES_MAP['train'])
            if self.mode == 'dev':
                if self._train_data:
                    random.seed(42)
                    keys = list(self._train_data.keys())
                    n_dev = len(self._train_data[keys[0]]) // 10 or 1
                    indices = list(range(len(self._train_data[keys[0]])))
                    random.shuffle(indices)
                    self._train_data = {k: [v[i] for i in indices[:n_dev]] for k, v in self._train_data.items()}
        if self.mode == 'test':
            self._test_data = self._load_data_from_file(file_name=WORFBENCH_FILES_MAP['test'])

    def _get_label(self, example: Dict) -> Any:
        return example.get('expected_output', '')

    def _get_id(self, example: Dict) -> Any:
        return example.get('id', '')

    def evaluate(self, prediction: Any, label: Any) -> Dict:
        if isinstance(prediction, list) and isinstance(label, list):
            f1 = evaluate_workflow_sequence(prediction, label)
        elif isinstance(prediction, dict) and isinstance(label, dict):
            f1 = evaluate_workflow_graph(prediction, label)
        else:
            f1 = f1_score(prediction=str(prediction), ground_truth=str(label))
        em = exact_match_score(prediction=prediction, ground_truth=label)
        acc = acc_score(prediction=prediction, ground_truths=[label])
        return {'em': em, 'f1': f1, 'acc': acc}

    async def async_evaluate(self, graph: Callable, example: Dict) -> float:
        task = example.get('task', '')
        context = '\n'.join((f'{ctx.get('title', '')}: {' '.join(ctx.get('content', []))}' for ctx in example.get('context', []) if isinstance(ctx, dict)))
        inputs = f'Task: {task}\nContext: {context}\nGenerate workflow:\nAnswer:'
        try:
            generated_workflow = await graph(inputs)
        except Exception as e:
            logger.error(f'Error generating workflow: {e}')
            generated_workflow = ''
        label = self._get_label(example)
        metrics = self.evaluate(prediction=generated_workflow, label=label)
        return metrics['f1']

def _load_data(self) -> None:
    if self.mode in ['train', 'dev']:
        self._train_data = self._load_data_from_file(file_name=WORFBENCH_FILES_MAP['train'])
        if self.mode == 'dev':
            if self._train_data:
                random.seed(42)
                keys = list(self._train_data.keys())
                n_dev = len(self._train_data[keys[0]]) // 10 or 1
                indices = list(range(len(self._train_data[keys[0]])))
                random.shuffle(indices)
                self._train_data = {k: [v[i] for i in indices[:n_dev]] for k, v in self._train_data.items()}
    if self.mode == 'test':
        self._test_data = self._load_data_from_file(file_name=WORFBENCH_FILES_MAP['test'])

def estimator(n: int, c: int, k: int) -> float:
    """Calculates 1 - comb(n - c, k) / comb(n, k)."""
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

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

def get_config_params(self) -> List[str]:
    """Get a list of configuration parameters.
        
        Returns:
            List[str]: List of configuration parameter names, excluding 'class_name'
        """
    config_params = list(type(self).model_fields.keys())
    config_params.remove('class_name')
    return config_params

def custom_serializer(obj: Any):
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode()
    if isinstance(obj, (datetime, date)):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, 'read') and hasattr(obj, 'name'):
        return f'<FileObject name={getattr(obj, 'name', 'unknown')}>'
    if callable(obj):
        return obj.__name__
    if hasattr(obj, '__class__'):
        return obj.__repr__() if hasattr(obj, '__repr__') else obj.__class__.__name__
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')

class ModelRegistry:

    def __init__(self):
        self.models = {}
        self.model_configs = {}

    def register(self, key: str, model_cls, config_cls):
        if key in self.models:
            raise ValueError(f"model name '{key}' is already registered!")
        self.models[key] = model_cls
        self.model_configs[key] = config_cls

    def key_error_message(self, key: str):
        error_message = f'`{key}` is not a registered model name. Currently availabel model names: {self.get_model_names()}. If `{key}` is a customized model, you should use @register_model({key}) to register the model.'
        return error_message

    def get_model(self, key: str):
        model = self.models.get(key, None)
        if model is None:
            raise KeyError(self.key_error_message(key))
        return model

    def get_model_config(self, key: str):
        config = self.model_configs.get(key, None)
        if config is None:
            raise KeyError(self.key_error_message(key))
        return config

    def get_model_names(self):
        return list(self.models.keys())

def get_model_names(self):
    return list(self.models.keys())

class ParseFunctionRegistry:

    def __init__(self):
        self.functions = {}

    def register(self, func_name: str, func):
        """Register a function with a given name.
        
        Args:
            func_name: The name to register the function under
            func (Callable): The function to register
            
        Raises:
            ValueError: If a function with the same name is already registered
        """
        if func_name in self.functions:
            raise ValueError(f"Function name '{func_name}' is already registered!")
        self.functions[func_name] = func

    def get_function(self, func_name: str) -> callable:
        """Get a registered function by name.
        
        Args:
            func_name: The name of the function to retrieve
            
        Returns:
            Callable: The registered function
            
        Raises:
            KeyError: If no function with the given name is registered
        """
        if func_name not in self.functions:
            available_funcs = list(self.functions.keys())
            raise KeyError(f"Function '{func_name}' not found! Available functions: {available_funcs}")
        return self.functions[func_name]

    def has_function(self, func_name: str) -> bool:
        """Check if a function name is registered.
        
        Args:
            func_name: The name to check
            
        Returns:
            True if the function name is registered, False otherwise
        """
        return func_name in self.functions

def get_function(self, func_name: str) -> callable:
    """Get a registered function by name.
        
        Args:
            func_name: The name of the function to retrieve
            
        Returns:
            Callable: The registered function
            
        Raises:
            KeyError: If no function with the given name is registered
        """
    if func_name not in self.functions:
        available_funcs = list(self.functions.keys())
        raise KeyError(f"Function '{func_name}' not found! Available functions: {available_funcs}")
    return self.functions[func_name]

class ActionFunctionRegistry:

    def __init__(self):
        self.functions = {}

    def register(self, func_name: str, func):
        """Register a function with a given name.
        
        Args:
            func_name: The name to register the function under
            func (Callable): The function to register
            
        Raises:
            ValueError: If a function with the same name is already registered
        """
        if func_name in self.functions:
            raise ValueError(f"Function name '{func_name}' is already registered!")
        self.functions[func_name] = func

    def get_function(self, func_name: str) -> callable:
        """Get a registered function by name.
        
        Args:
            func_name: The name of the function to retrieve
            
        Returns:
            Callable: The registered function
            
        Raises:
            KeyError: If no function with the given name is registered
        """
        if func_name not in self.functions:
            available_funcs = list(self.functions.keys())
            raise KeyError(f"Function '{func_name}' not found! Available functions: {available_funcs}")
        return self.functions[func_name]

    def has_function(self, func_name: str) -> bool:
        """Check if a function name is registered.
        
        Args:
            func_name: The name to check
            
        Returns:
            True if the function name is registered, False otherwise
        """
        return func_name in self.functions

def get_function(self, func_name: str) -> callable:
    """Get a registered function by name.
        
        Args:
            func_name: The name of the function to retrieve
            
        Returns:
            Callable: The registered function
            
        Raises:
            KeyError: If no function with the given name is registered
        """
    if func_name not in self.functions:
        available_funcs = list(self.functions.keys())
        raise KeyError(f"Function '{func_name}' not found! Available functions: {available_funcs}")
    return self.functions[func_name]

class LongTermMemory(BaseMemory):
    """
    Manages long-term storage and retrieval of memories, integrating with RAGEngine for indexing
    and StorageHandler for persistence.
    """
    storage_handler: StorageHandler = Field(..., description='Handler for persistent storage')
    rag_config: RAGConfig = Field(..., description='Configuration for RAG engine')
    rag_engine: RAGEngine = Field(default=None, description='RAG engine for indexing and retrieval')
    memory_table: str = Field(default='memory', description='Database table for storing memories')
    default_corpus_id: Optional[str] = Field(default=None, description='Default corpus ID for memory indexing')

    def init_module(self):
        """Initialize the RAG engine and memory indices."""
        super().init_module()
        if self.rag_engine is None:
            self.rag_engine = RAGEngine(config=self.rag_config, storage_handler=self.storage_handler)
        if self.default_corpus_id is None:
            self.default_corpus_id = str(uuid4())
        logger.info(f'Initialized LongTermMemory with corpus_id {self.default_corpus_id}')

    def _create_memory_chunk(self, message: Message, memory_id: str) -> Chunk:
        """Convert a Message to a Chunk for RAG indexing."""
        metadata = ChunkMetadata(corpus_id=self.default_corpus_id, memory_id=memory_id, timestamp=message.timestamp, action=message.action, wf_goal=message.wf_goal, agent=message.agent, msg_type=message.msg_type.value if message.msg_type else None, prompt=message.prompt, next_actions=message.next_actions, wf_task=message.wf_task, wf_task_desc=message.wf_task_desc, message_id=message.message_id, content=json.dumps(message.content))
        return Chunk(chunk_id=memory_id, text=str(message.content), metadata=metadata, start_char_idx=0, end_char_idx=len(str(message.content)))

    def _chunk_to_message(self, chunk: Chunk) -> Message:
        """Convert a Chunk to a Message object."""
        return Message(content=chunk.metadata.content, action=chunk.metadata.action, wf_goal=chunk.metadata.wf_goal, timestamp=chunk.metadata.timestamp, agent=chunk.metadata.agent, msg_type=chunk.metadata.msg_type, prompt=chunk.metadata.prompt, next_actions=chunk.metadata.next_actions, wf_task=chunk.metadata.wf_task, wf_task_desc=chunk.metadata.wf_task_desc, message_id=chunk.metadata.message_id)

    def add(self, messages: Union[Message, str, List[Union[Message, str]]]) -> List[str]:
        """Store messages in memory and index them in RAGEngine, returning memory_ids."""
        if not isinstance(messages, list):
            messages = [messages]
        messages = [Message(content=msg) if isinstance(msg, str) else msg for msg in messages]
        messages = [msg for msg in messages if msg.content]
        if not messages:
            logger.warning('No valid messages to add')
            return []
        existing_hashes = {record['content_hash'] for record in self.storage_handler.load(tables=[self.memory_table]).get(self.memory_table, []) if 'content_hash' in record}
        memory_ids = [str(uuid4()) for _ in messages]
        final_messages = []
        final_memory_ids = []
        final_chunks = []
        for msg, memory_id in zip(messages, memory_ids):
            content_hash = hashlib.sha256(str(msg.content).encode()).hexdigest()
            if content_hash in existing_hashes:
                logger.info(f'Duplicate message found (hash): {msg.content[:50]}...')
                existing_id = next((r['memory_id'] for r in self.storage_handler.load(tables=[self.memory_table]).get(self.memory_table, []) if r.get('content_hash') == content_hash), None)
                if existing_id:
                    final_memory_ids.append(existing_id)
                    continue
            final_messages.append(msg)
            final_memory_ids.append(memory_id)
            chunk = self._create_memory_chunk(msg, memory_id)
            chunk.metadata.content_hash = content_hash
            final_chunks.append(chunk)
        if not final_chunks:
            logger.info('No messages added after deduplication')
            return final_memory_ids
        for msg in final_messages:
            super().add_message(msg)
        corpus = Corpus(chunks=final_chunks, corpus_id=self.default_corpus_id)
        chunk_ids = self.rag_engine.add(index_type=self.rag_config.index.index_type, nodes=corpus, corpus_id=self.default_corpus_id)
        if not chunk_ids:
            logger.error('Failed to index memories')
            return final_memory_ids
        return final_memory_ids

    async def get(self, memory_ids: Union[str, List[str]], return_chunk: bool=True) -> List[Tuple[Union[Chunk, Message], str]]:
        """Retrieve memories by memory_ids, returning (Message/Chunk, memory_id) tuples."""
        if not isinstance(memory_ids, list):
            memory_ids = [memory_ids]
        if not memory_ids:
            logger.warning('No memory_ids provided for get')
            return []
        try:
            chunks = await self.rag_engine.aget(corpus_id=self.default_corpus_id, index_type=self.rag_config.index.index_type, node_ids=memory_ids)
            results = [(self._chunk_to_message(chunk), chunk.metadata.memory_id) if not return_chunk else (chunk, chunk.metadata.memory_id) for chunk in chunks if chunk]
            logger.info(f'Retrieved {len(results)} memories for memory_ids: {memory_ids}')
            return results
        except Exception as e:
            logger.error(f'Failed to get memories: {str(e)}')
            return []

    def delete(self, memory_ids: Union[str, List[str]]) -> List[bool]:
        """Delete memories by memory_ids, returning success status for each."""
        if not isinstance(memory_ids, list):
            memory_ids = [memory_ids]
        if not memory_ids:
            logger.warning('No memory_ids provided for deletion')
            return []
        successes = [False] * len(memory_ids)
        valid_memory_ids = []
        existing_chunks = asyncio.run(self.get(memory_ids, return_chunk=True))
        for idx, (chunk, mid) in enumerate(existing_chunks):
            if chunk:
                valid_memory_ids.append(mid)
                super().remove_message(self._chunk_to_message(chunk))
                successes[idx] = True
        if not valid_memory_ids:
            logger.info('No memories found for deletion')
            return successes
        self.rag_engine.delete(corpus_id=self.default_corpus_id, index_type=self.rag_config.index.index_type, node_ids=valid_memory_ids)
        return successes

    def update(self, updates: Union[Tuple[str, Union[Message, str]], List[Tuple[str, Union[Message, str]]]]) -> List[bool]:
        """Update memories with new content, returning success status for each."""
        if not isinstance(updates, list):
            updates = [updates]
        updates = [(mid, Message(content=msg) if isinstance(msg, str) else msg) for mid, msg in updates]
        updates_dict = {mid: msg for mid, msg in updates if msg.content}
        if not updates_dict:
            logger.warning('No valid updates provided')
            return []
        memory_ids = list(updates_dict.keys())
        existing_memories = asyncio.run(self.get(memory_ids, return_chunk=False))
        existing_dict = {mid: msg for msg, mid in existing_memories}
        successes = [False] * len(updates)
        final_updates = []
        final_memory_ids = []
        for mid, msg in updates_dict.items():
            if mid not in existing_dict:
                logger.warning(f'No memory found with memory_id {mid}')
                continue
            final_updates.append((mid, msg))
            final_memory_ids.append(mid)
            successes[memory_ids.index(mid)] = True
            super().remove_message(existing_dict[mid])
        if not final_updates:
            logger.info('No memories updated')
            return successes
        chunks = [self._create_memory_chunk(msg, mid) for mid, msg in final_updates]
        for msg in [msg for _, msg in final_updates]:
            super().add_message(msg)
        corpus = Corpus(chunks=chunks, corpus_id=self.default_corpus_id)
        chunk_ids = self.rag_engine.add(index_type=self.rag_config.index.index_type, nodes=corpus, corpus_id=self.default_corpus_id)
        if not chunk_ids:
            logger.error(f'Failed to update memories in RAG index: {final_memory_ids}')
            return [False] * len(updates)
        return successes

    async def search_async(self, query: Union[str, Query], n: Optional[int]=None, metadata_filters: Optional[Dict]=None, return_chunk=False) -> List[Tuple[Message, str]]:
        """Retrieve messages from RAG index asynchronously based on a query, returning messages and memory_ids."""
        if isinstance(query, str):
            query_obj = Query(query_str=query, top_k=n or self.rag_config.retrieval.top_k, metadata_filters=metadata_filters or {})
        else:
            query_obj = query
            query_obj.top_k = n or self.rag_config.retrieval.top_k
            if metadata_filters:
                query_obj.metadata_filters = {**query_obj.metadata_filters, **metadata_filters} if query_obj.metadata_filters else metadata_filters
        try:
            result: RagResult = await self.rag_engine.query_async(query_obj, corpus_id=self.default_corpus_id)
            if return_chunk:
                return [(chunk, chunk.metadata.memory_id) for chunk in result.corpus.chunks]
            else:
                messages = [(self._chunk_to_message(chunk), chunk.metadata.memory_id) for chunk in result.corpus.chunks]
            logger.info(f'Retrieved {len(messages)} memories for query: {query_obj.query_str}')
            return messages[:n] if n else messages
        except Exception as e:
            logger.error(f'Failed to search memories: {str(e)}')
            return []

    def search(self, query: Union[str, Query], n: Optional[int]=None, metadata_filters: Optional[Dict]=None) -> List[Tuple[Message, str]]:
        """Synchronous wrapper for searching memories."""
        return asyncio.run(self.search_async(query, n, metadata_filters))

    def clear(self) -> None:
        """Clear all messages and indices."""
        super().clear()
        self.rag_engine.clear(corpus_id=self.default_corpus_id)
        logger.info(f'Cleared LongTermMemory with corpus_id {self.default_corpus_id}')

    def save(self, save_path: Optional[str]=None) -> None:
        """Save all indices and memory data to database."""
        self.rag_engine.save(output_path=save_path, corpus_id=self.default_corpus_id, table=self.memory_table)

    def load(self, save_path: Optional[str]=None) -> List[str]:
        """Load memory data from database and reconstruct indices, returning memory_ids."""
        return self.rag_engine.load(source=save_path, corpus_id=self.default_corpus_id, table=self.memory_table)

def delete(self, memory_ids: Union[str, List[str]]) -> List[bool]:
    """Delete memories by memory_ids, returning success status for each."""
    if not isinstance(memory_ids, list):
        memory_ids = [memory_ids]
    if not memory_ids:
        logger.warning('No memory_ids provided for deletion')
        return []
    successes = [False] * len(memory_ids)
    valid_memory_ids = []
    existing_chunks = asyncio.run(self.get(memory_ids, return_chunk=True))
    for idx, (chunk, mid) in enumerate(existing_chunks):
        if chunk:
            valid_memory_ids.append(mid)
            super().remove_message(self._chunk_to_message(chunk))
            successes[idx] = True
    if not valid_memory_ids:
        logger.info('No memories found for deletion')
        return successes
    self.rag_engine.delete(corpus_id=self.default_corpus_id, index_type=self.rag_config.index.index_type, node_ids=valid_memory_ids)
    return successes

def update(self, updates: Union[Tuple[str, Union[Message, str]], List[Tuple[str, Union[Message, str]]]]) -> List[bool]:
    """Update memories with new content, returning success status for each."""
    if not isinstance(updates, list):
        updates = [updates]
    updates = [(mid, Message(content=msg) if isinstance(msg, str) else msg) for mid, msg in updates]
    updates_dict = {mid: msg for mid, msg in updates if msg.content}
    if not updates_dict:
        logger.warning('No valid updates provided')
        return []
    memory_ids = list(updates_dict.keys())
    existing_memories = asyncio.run(self.get(memory_ids, return_chunk=False))
    existing_dict = {mid: msg for msg, mid in existing_memories}
    successes = [False] * len(updates)
    final_updates = []
    final_memory_ids = []
    for mid, msg in updates_dict.items():
        if mid not in existing_dict:
            logger.warning(f'No memory found with memory_id {mid}')
            continue
        final_updates.append((mid, msg))
        final_memory_ids.append(mid)
        successes[memory_ids.index(mid)] = True
        super().remove_message(existing_dict[mid])
    if not final_updates:
        logger.info('No memories updated')
        return successes
    chunks = [self._create_memory_chunk(msg, mid) for mid, msg in final_updates]
    for msg in [msg for _, msg in final_updates]:
        super().add_message(msg)
    corpus = Corpus(chunks=chunks, corpus_id=self.default_corpus_id)
    chunk_ids = self.rag_engine.add(index_type=self.rag_config.index.index_type, nodes=corpus, corpus_id=self.default_corpus_id)
    if not chunk_ids:
        logger.error(f'Failed to update memories in RAG index: {final_memory_ids}')
        return [False] * len(updates)
    return successes

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

def get_total_cost(self):
    total_cost = 0.0
    for model in self.total_cost.keys():
        total_cost += self.total_cost[model]
    return total_cost

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

def init_model(self):
    config: SiliconFlowConfig = self.config
    self._client = self._init_client(config)
    self._default_ignore_fields = ['llm_type', 'siliconflow_key', 'output_response']

def _update_cost(self, cost: Cost):
    cost_manager.update_cost(cost=cost, model=self.config.model)

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

def init_model(self):
    config: OpenAILLMConfig = self.config
    self._client = self._init_client(config)
    self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key']
    if self.config.model not in get_openai_model_cost():
        raise KeyError(f"'{self.config.model}' is not a valid OpenAI model name!")

def _update_cost(self, cost: Cost):
    cost_manager.update_cost(cost=cost, model=self.config.model)

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

def init_model(self):
    config: OpenRouterConfig = self.config
    self._client = self._init_client(config)
    self._default_ignore_fields = ['llm_type', 'openrouter_key', 'openrouter_base', 'openrouter_model_base', 'output_response']

def _update_cost(self, cost: Cost):
    cost_manager.update_cost(cost=cost, model=self.config.model)

class CustomizeAction(Action):
    parse_mode: Optional[str] = Field(default='title', description="the parse mode of the action, must be one of: ['title', 'str', 'json', 'xml', 'custom']")
    parse_func: Optional[Callable] = Field(default=None, exclude=True, description='the function to parse the LLM output. It receives the LLM output and returns a dict.')
    title_format: Optional[str] = Field(default='## {title}', exclude=True, description="the format of the title. It is used when the `parse_mode` is 'title'.")
    custom_output_format: Optional[str] = Field(default=None, exclude=True, description='the format of the output. It is used when the `prompt_template` is provided.')
    tools: Optional[List[Toolkit]] = Field(default=None, description='The tools that the action can use')
    conversation: Optional[Message] = Field(default=None, description='Current conversation state')
    max_tool_try: int = Field(default=2, description='Maximum number of tool calling attempts allowed')

    def __init__(self, **kwargs):
        name = kwargs.pop('name', 'CustomizeAction')
        description = kwargs.pop('description', 'Customized action that can use tools to accomplish its task')
        super().__init__(name=name, description=description, **kwargs)
        if not self.prompt and (not self.prompt_template):
            raise ValueError('`prompt` or `prompt_template` is required when creating CustomizeAction action')
        if self.prompt and self.prompt_template:
            logger.warning('Both `prompt` and `prompt_template` are provided for CustomizeAction action. Prioritizing `prompt_template` and ignoring `prompt`.')
        if self.tools:
            self.tools_caller = {}
            self.add_tools(self.tools)

    def prepare_action_prompt(self, inputs: Optional[dict]=None, system_prompt: Optional[str]=None, **kwargs) -> Union[str, List[dict]]:
        """Prepare prompt for action execution.
        
        This helper function transforms the input dictionary into a formatted prompt
        for the language model, handling different prompting modes.
        
        Args:
            inputs: Dictionary of input parameters
            system_prompt: Optional system prompt to include
            
        Returns:
            Union[str, List[dict]]: Formatted prompt ready for LLM (string or chat messages)
            
        Raises:
            TypeError: If an input value type is not supported
            ValueError: If neither prompt nor prompt_template is available
        """
        if inputs is None:
            inputs = {}
        prompt_params_names = self.inputs_format.get_attrs()
        prompt_params_values = {}
        for param in prompt_params_names:
            value = inputs.get(param, '')
            if isinstance(value, str):
                prompt_params_values[param] = value
            elif isinstance(value, (dict, list)):
                prompt_params_values[param] = json.dumps(value, indent=4)
            else:
                raise TypeError(f'The input type {type(value)} is invalid! Valid types: [str, dict, list].')
        if self.prompt:
            prompt = self.prompt.format(**prompt_params_values) if prompt_params_values else self.prompt
            if self.tools:
                tools_schemas = [j['function'] for i in [tool.get_tool_schemas() for tool in self.tools] for j in i]
                prompt += '\n\n' + TOOL_CALLING_TEMPLATE.format(tools_description=tools_schemas)
            return prompt
        else:
            if self.tools:
                self.prompt_template.set_tools(self.tools)
            return self.prompt_template.format(system_prompt=system_prompt, values=prompt_params_values, inputs_format=self.inputs_format, outputs_format=self.outputs_format, parse_mode=self.parse_mode, title_format=self.title_format, custom_output_format=self.custom_output_format, tools=self.tools)

    def prepare_extraction_prompt(self, llm_output_content: str) -> str:
        """Prepare extraction prompt for fallback extraction when parsing fails.
        
        Args:
            self: The action instance
            llm_output_content: Raw output content from LLM
            
        Returns:
            str: Formatted extraction prompt
        """
        attr_descriptions: dict = self.outputs_format.get_attr_descriptions()
        output_description_list = []
        for i, (name, desc) in enumerate(attr_descriptions.items()):
            output_description_list.append(f'{i + 1}. {name}\nDescription: {desc}')
        output_description = '\n\n'.join(output_description_list)
        return OUTPUT_EXTRACTION_PROMPT.format(text=llm_output_content, output_description=output_description)

    def _get_unique_class_name(self, candidate_name: str) -> str:
        """
        Get a unique class name by checking if it already exists in the registry.
        If it does, append "Vx" to make it unique.
        """
        if not MODULE_REGISTRY.has_module(candidate_name):
            return candidate_name
        i = 1
        while True:
            unique_name = f'{candidate_name}V{i}'
            if not MODULE_REGISTRY.has_module(unique_name):
                break
            i += 1
        return unique_name

    def add_tools(self, tools: Union[Toolkit, List[Toolkit]]):
        if not tools:
            return
        if isinstance(tools, Toolkit):
            tools = [tools]
        if not all((isinstance(tool, Toolkit) for tool in tools)):
            raise TypeError('`tools` must be a Toolkit or list of Toolkit instances.')
        if not self.tools:
            self.tools_caller = {}
            self.tools = []
        for toolkit in tools:
            try:
                tool_callers = toolkit.get_tools()
                if not isinstance(tool_callers, list):
                    logger.warning(f"Expected list of tool functions from '{toolkit.name}.get_tools()', got {type(tool_callers)}.")
                    continue
                valid_tools_count = 0
                valid_tools_names, valid_tool_callers = ([], [])
                for tool_caller in tool_callers:
                    tool_caller_name = getattr(tool_caller, 'name', None)
                    if not tool_caller_name or not callable(tool_caller):
                        logger.warning(f"Invalid tool function in '{toolkit.name}': missing name or not callable.")
                        continue
                    if tool_caller_name in self.tools_caller:
                        logger.warning(f"Duplicate tool function '{tool_caller_name}' detected. Overwriting previous function.")
                    valid_tools_count += 1
                    valid_tools_names.append(tool_caller_name)
                    valid_tool_callers.append(tool_caller)
                if valid_tools_count == 0:
                    logger.info(f"No valid tools found in toolkit '{toolkit.name}'. Skipping.")
                    continue
                if valid_tools_count > 0 and all((name in self.tools_caller for name in valid_tools_names)):
                    logger.info(f"All tools from toolkit '{toolkit.name}' are already added. Skipping.")
                    continue
                if valid_tools_count > 0:
                    self.tools_caller.update({name: caller for name, caller in zip(valid_tools_names, valid_tool_callers)})
                existing_toolkit_names = {tkt.name for tkt in self.tools}
                if valid_tools_count > 0 and toolkit.name not in existing_toolkit_names:
                    self.tools.append(toolkit)
                if valid_tools_count > 0:
                    logger.info(f"Added toolkit '{toolkit.name}' with {valid_tools_count} valid tools in {self.name}: {valid_tools_names}.")
            except Exception as e:
                logger.error(f"Failed to load tools from toolkit '{toolkit.name}': {e}")

    def _extract_tool_calls(self, llm_output: str, llm: Optional[BaseLLM]=None) -> List[dict]:
        pattern = '<ToolCalling>\\s*(.*?)\\s*</ToolCalling>'
        matches = re.findall(pattern, llm_output, re.DOTALL)
        if not matches:
            return []
        parsed_tool_calls = []
        for match_content in matches:
            try:
                json_content = match_content.strip()
                json_list = parse_json_from_text(json_content)
                if not json_list:
                    logger.warning('No valid JSON found in ToolCalling block')
                    continue
                parsed_tool_call = json.loads(json_list[0])
                if isinstance(parsed_tool_call, dict):
                    parsed_tool_calls.append(parsed_tool_call)
                elif isinstance(parsed_tool_call, list):
                    parsed_tool_calls.extend(parsed_tool_call)
                else:
                    logger.warning(f'Invalid tool call format: {parsed_tool_call}')
                    continue
            except (json.JSONDecodeError, IndexError) as e:
                logger.warning(f'Failed to parse tool calls from LLM output: {e}')
                if llm is not None:
                    retry_prompt = TOOL_CALLING_RETRY_PROMPT.format(text=match_content)
                    try:
                        fixed_output = llm.generate(prompt=retry_prompt).content.strip()
                        logger.info(f'Retrying tool call parse with fixed output:\n{fixed_output}')
                        fixed_list = parse_json_from_text(fixed_output)
                        if fixed_list:
                            parsed_tool_call = json.loads(fixed_list[0])
                            if isinstance(parsed_tool_call, dict):
                                parsed_tool_calls.append(parsed_tool_call)
                        elif isinstance(parsed_tool_call, list):
                            parsed_tool_calls.extend(parsed_tool_call)
                    except Exception as retry_err:
                        logger.error(f'Retry failed: {retry_err}')
                        continue
            else:
                continue
        return parsed_tool_calls

    def _extract_output(self, llm_output: Any, llm: BaseLLM=None, **kwargs):
        llm_output_content = getattr(llm_output, 'content', str(llm_output))
        output_attrs = self.outputs_format.get_attrs()
        if not output_attrs:
            output = self.outputs_format.parse(content=llm_output_content)
            return output
        try:
            parsed_output = self.outputs_format.parse(content=llm_output_content, parse_mode=self.parse_mode, parse_func=getattr(self, 'parse_func', None), title_format=getattr(self, 'title_format', '## {title}'))
            return parsed_output
        except Exception as e:
            logger.info(f"Failed to parse with action's parse settings: {e}")
            logger.info('Falling back to using LLM to extract outputs...')
            extraction_prompt = self.prepare_extraction_prompt(llm_output_content)
            llm_extracted_output: LLMOutputParser = llm.generate(prompt=extraction_prompt)
            llm_extracted_data: dict = parse_json_from_llm_output(llm_extracted_output.content)
            output = self.outputs_format.from_dict(llm_extracted_data)
            return output

    async def _async_extract_output(self, llm_output: Any, llm: BaseLLM=None, **kwargs):
        llm_output_content = getattr(llm_output, 'content', str(llm_output))
        output_attrs = self.outputs_format.get_attrs()
        if not output_attrs:
            output = self.outputs_format.parse(content=llm_output_content)
            return output
        try:
            parsed_output = self.outputs_format.parse(content=llm_output_content, parse_mode=self.parse_mode, parse_func=getattr(self, 'parse_func', None), title_format=getattr(self, 'title_format', '## {title}'))
            return parsed_output
        except Exception as e:
            logger.info(f"Failed to parse with action's parse settings: {e}")
            logger.info('Falling back to using LLM to extract outputs...')
            extraction_prompt = self.prepare_extraction_prompt(llm_output_content)
            llm_extracted_output = await llm.async_generate(prompt=extraction_prompt)
            llm_extracted_data: dict = parse_json_from_llm_output(llm_extracted_output.content)
            output = self.outputs_format.from_dict(llm_extracted_data)
            return output

    def _call_single_tool(self, function_param: dict) -> tuple:
        try:
            function_name = function_param.get('function_name')
            function_args = function_param.get('function_args') or {}
            if not function_name:
                return (None, 'No function name provided')
            callable_fn = self.tools_caller.get(function_name)
            if not callable(callable_fn):
                return (None, f"Function '{function_name}' not found or not callable")
            print('_____________________ Start Function Calling _____________________')
            print(f'Executing function calling: {function_name} with parameters: {function_args}')
            result = callable_fn(**function_args)
            return (result, None)
        except Exception as e:
            logger.error(f'Error executing tool {function_name}: {e}')
            return (None, f'Error executing tool {function_name}: {str(e)}')

    def _calling_tools(self, tool_call_args: List[dict]) -> dict:
        errors = []
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_tool = {executor.submit(self._call_single_tool, param): param for param in tool_call_args}
            for future in concurrent.futures.as_completed(future_to_tool):
                result, error = future.result()
                if error:
                    errors.append(error)
                if result is not None:
                    results.append(result)
        return {'result': results, 'error': errors}

    async def _async_call_single_tool(self, function_param: dict) -> tuple:
        try:
            function_name = function_param.get('function_name')
            function_args = function_param.get('function_args') or {}
            if not function_name:
                return (None, 'No function name provided')
            callable_fn = self.tools_caller.get(function_name)
            if not callable(callable_fn):
                return (None, f"Function '{function_name}' not found or not callable")
            print('_____________________ Start Function Calling _____________________')
            print(f'Executing function calling: {function_name} with parameters: {function_args}')
            if inspect.iscoroutinefunction(callable_fn):
                result = await callable_fn(**function_args)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: callable_fn(**function_args))
            return (result, None)
        except Exception as e:
            logger.error(f'Error executing tool {function_name}: {e}')
            return (None, f'Error executing tool {function_name}: {str(e)}')

    async def _async_calling_tools(self, tool_call_args: List[dict]) -> dict:
        tasks = [self._async_call_single_tool(param) for param in tool_call_args]
        results_with_errors = await asyncio.gather(*tasks)
        results = [res for res, err in results_with_errors if err is None and res is not None]
        errors = [err for _, err in results_with_errors if err is not None]
        return {'result': results, 'error': errors}

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, time_out=0, **kwargs):
        input_attributes: dict = self.inputs_format.get_attr_descriptions()
        if not inputs and input_attributes:
            logger.error('CustomizeAction action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to CustomizeAction action is None or empty.')
        if inputs is None:
            inputs = {}
        final_llm_response = None
        if self.prompt_template:
            if isinstance(self.prompt_template, ChatTemplate):
                conversation = self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)
            elif isinstance(self.prompt_template, StringTemplate):
                conversation = [{'role': 'system', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
            else:
                raise ValueError(f'`prompt_template` must be a StringTemplate or ChatTemplate instance, but got {type(self.prompt_template)}')
        else:
            conversation = [{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
        prompt_params_values = {k: inputs.get(k, '') for k in input_attributes.keys()}
        while True:
            if time_out > self.max_tool_try:
                current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
                content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
                if return_prompt:
                    return (self._extract_output(content_to_extract, llm=llm), current_prompt)
                return self._extract_output(content_to_extract, llm=llm)
            time_out += 1
            llm_response = llm.generate(messages=conversation)
            conversation.append({'role': 'assistant', 'content': llm_response.content})
            final_llm_response = llm_response
            tool_call_args = self._extract_tool_calls(llm_response.content)
            if not tool_call_args:
                break
            logger.info('Extracted tool call args:')
            logger.info(json.dumps(tool_call_args, indent=4))
            results = self._calling_tools(tool_call_args)
            logger.info('Tool call results:')
            logger.info(json.dumps(results, indent=4))
            conversation.append({'role': 'assistant', 'content': TOOL_CALLING_HISTORY_PROMPT.format(iteration_number=time_out, tool_call_args=f'{tool_call_args}', results=f'{results}')})
        current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
        content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
        if return_prompt:
            return (self._extract_output(content_to_extract, llm=llm), current_prompt)
        return self._extract_output(content_to_extract, llm=llm)

    async def async_execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, time_out=0, **kwargs):
        input_attributes: dict = self.inputs_format.get_attr_descriptions()
        if not inputs and input_attributes:
            logger.error('CustomizeAction action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to CustomizeAction action is None or empty.')
        if inputs is None:
            inputs = {}
        final_llm_response = None
        if self.prompt_template:
            if isinstance(self.prompt_template, ChatTemplate):
                conversation = self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)
            elif isinstance(self.prompt_template, StringTemplate):
                conversation = [{'role': 'system', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
            else:
                raise ValueError(f'`prompt_template` must be a StringTemplate or ChatTemplate instance, but got {type(self.prompt_template)}')
        else:
            conversation = [{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
        prompt_params_values = {k: inputs.get(k, '') for k in input_attributes.keys()}
        while True:
            if time_out > self.max_tool_try:
                current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
                content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
                if return_prompt:
                    return (await self._async_extract_output(content_to_extract, llm=llm), current_prompt)
                return await self._async_extract_output(content_to_extract, llm=llm)
            time_out += 1
            llm_response = await llm.async_generate(messages=conversation)
            conversation.append({'role': 'assistant', 'content': llm_response.content})
            final_llm_response = llm_response
            tool_call_args = self._extract_tool_calls(llm_response.content)
            if not tool_call_args:
                break
            logger.info('Extracted tool call args:')
            logger.info(json.dumps(tool_call_args, indent=4))
            results = self._calling_tools(tool_call_args)
            logger.info('Tool call results:')
            try:
                logger.info(json.dumps(results, indent=4))
            except Exception:
                logger.info(str(results))
            conversation.append({'role': 'assistant', 'content': TOOL_CALLING_HISTORY_PROMPT.format(iteration_number=time_out, tool_call_args=f'{tool_call_args}', results=f'{results}')})
        current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
        content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
        if return_prompt:
            return (await self._async_extract_output(content_to_extract, llm=llm), current_prompt)
        return await self._async_extract_output(content_to_extract, llm=llm)

def add_tools(self, tools: Union[Toolkit, List[Toolkit]]):
    if not tools:
        return
    if isinstance(tools, Toolkit):
        tools = [tools]
    if not all((isinstance(tool, Toolkit) for tool in tools)):
        raise TypeError('`tools` must be a Toolkit or list of Toolkit instances.')
    if not self.tools:
        self.tools_caller = {}
        self.tools = []
    for toolkit in tools:
        try:
            tool_callers = toolkit.get_tools()
            if not isinstance(tool_callers, list):
                logger.warning(f"Expected list of tool functions from '{toolkit.name}.get_tools()', got {type(tool_callers)}.")
                continue
            valid_tools_count = 0
            valid_tools_names, valid_tool_callers = ([], [])
            for tool_caller in tool_callers:
                tool_caller_name = getattr(tool_caller, 'name', None)
                if not tool_caller_name or not callable(tool_caller):
                    logger.warning(f"Invalid tool function in '{toolkit.name}': missing name or not callable.")
                    continue
                if tool_caller_name in self.tools_caller:
                    logger.warning(f"Duplicate tool function '{tool_caller_name}' detected. Overwriting previous function.")
                valid_tools_count += 1
                valid_tools_names.append(tool_caller_name)
                valid_tool_callers.append(tool_caller)
            if valid_tools_count == 0:
                logger.info(f"No valid tools found in toolkit '{toolkit.name}'. Skipping.")
                continue
            if valid_tools_count > 0 and all((name in self.tools_caller for name in valid_tools_names)):
                logger.info(f"All tools from toolkit '{toolkit.name}' are already added. Skipping.")
                continue
            if valid_tools_count > 0:
                self.tools_caller.update({name: caller for name, caller in zip(valid_tools_names, valid_tool_callers)})
            existing_toolkit_names = {tkt.name for tkt in self.tools}
            if valid_tools_count > 0 and toolkit.name not in existing_toolkit_names:
                self.tools.append(toolkit)
            if valid_tools_count > 0:
                logger.info(f"Added toolkit '{toolkit.name}' with {valid_tools_count} valid tools in {self.name}: {valid_tools_names}.")
        except Exception as e:
            logger.error(f"Failed to load tools from toolkit '{toolkit.name}': {e}")

def fetch_single_data_type(stock_code, data_type):
    """
    抓取指定股票的单一类型数据
    
    Args:
        stock_code (str): 股票代码
        data_type (str): 数据类型 ('stock_daily', 'cpi', 'gdp', 'industry_fund', 
                                   'news', 'market_summary', 'indices', 'volatility', 'rating')
        
    Returns:
        pandas.DataFrame: 抓取的数据
    """
    fetcher = StockDataFetcher(stock_code=stock_code)
    data_map = {'stock_daily': fetcher.fetch_stock_daily, 'cpi': fetcher.fetch_china_cpi, 'gdp': fetcher.fetch_china_gdp, 'industry_fund': fetcher.fetch_industry_fund_flow, 'news': fetcher.fetch_stock_news, 'market_summary': fetcher.fetch_market_summary, 'indices': fetcher.fetch_market_indices, 'volatility': fetcher.fetch_option_volatility, 'rating': fetcher.fetch_institution_recommendation}
    if data_type in data_map:
        result = data_map[data_type]()
        if result is not None:
            filename_mapping = {'stock_daily': 'stock_daily_catl', 'cpi': 'china_cpi', 'gdp': 'china_gdp_yearly', 'industry_fund': 'industry_fund_flow', 'news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'indices': 'market_indices', 'volatility': 'option_volatility_50etf', 'rating': 'institution_recommendation_catl'}
            fetcher.save_data(result, filename_mapping[data_type], f'{data_type}数据')
        return result
    else:
        print(f'❌ 不支持的数据类型: {data_type}')
        print(f'支持的类型: {list(data_map.keys())}')
        return None

def fetch_single_data_type(stock_code, data_type):
    """
    抓取指定股票的单一类型数据
    
    Args:
        stock_code (str): 股票代码
        data_type (str): 数据类型 ('stock_daily', 'cpi', 'gdp', 'industry_fund', 
                                   'news', 'market_summary', 'indices', 'volatility', 'rating')
        
    Returns:
        pandas.DataFrame: 抓取的数据
    """
    fetcher = StockDataFetcher(stock_code=stock_code)
    data_map = {'stock_daily': fetcher.fetch_stock_daily, 'cpi': fetcher.fetch_china_cpi, 'gdp': fetcher.fetch_china_gdp, 'industry_fund': fetcher.fetch_industry_fund_flow, 'news': fetcher.fetch_stock_news, 'market_summary': fetcher.fetch_market_summary, 'indices': fetcher.fetch_market_indices, 'volatility': fetcher.fetch_option_volatility, 'rating': fetcher.fetch_institution_recommendation}
    if data_type in data_map:
        result = data_map[data_type]()
        if result is not None:
            filename_mapping = {'stock_daily': 'stock_daily_catl', 'cpi': 'china_cpi', 'gdp': 'china_gdp_yearly', 'industry_fund': 'industry_fund_flow', 'news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'indices': 'market_indices', 'volatility': 'option_volatility_50etf', 'rating': 'institution_recommendation_catl'}
            fetcher.save_data(result, filename_mapping[data_type], f'{data_type}数据')
        return result
    else:
        print(f'❌ 不支持的数据类型: {data_type}')
        print(f'支持的类型: {list(data_map.keys())}')
        return None

def run_simple_hello_world(interpreter):
    """
    Run a simple Hello World example using the provided interpreter.
    
    Args:
        interpreter: An instance of a code interpreter
    """
    code = '\nprint("Hello, World!")\nprint("This code is running inside a secure Python interpreter.")\n'
    result = interpreter.execute(code, 'python')
    print('\nSimple Hello World Result:')
    print('-' * 50)
    print(result)
    print('-' * 50)

def run_math_example(interpreter):
    """
    Run a math example using the provided interpreter.
    
    Args:
        interpreter: An instance of a code interpreter
    """
    code = '\nprint("Running math operations...")\n\n# Using math library\nimport math\nprint(f"The value of pi is: {math.pi:.4f}")\nprint(f"The square root of 16 is: {math.sqrt(16)}")\nprint(f"The value of e is: {math.e:.4f}")\n'
    result = interpreter.execute(code, 'python')
    print('\nMath Example Result:')
    print('-' * 50)
    print(result)
    print('-' * 50)

def run_platform_info(interpreter):
    """
    Run a platform info example using the provided interpreter.
    
    Args:
        interpreter: An instance of a code interpreter
    """
    code = '\nprint("Getting platform information...")\n\n# System information\nimport platform\nimport sys\n\nprint(f"Python version: {platform.python_version()}")\nprint(f"Platform: {platform.system()} {platform.release()}")\nprint(f"Processor: {platform.processor()}")\nprint(f"Implementation: {platform.python_implementation()}")\n'
    result = interpreter.execute(code, 'python')
    print('\nPlatform Info Result:')
    print('-' * 50)
    print(result)
    print('-' * 50)

def run_dynamic_code_generation(interpreter):
    """
    Run an example that demonstrates dynamic code generation and execution.
    
    Args:
        interpreter: An instance of a code interpreter
    """
    code = '\nprint("Generating and executing code dynamically...")\n\n# Generate a function definition\nfunction_code = \'\'\'\ndef calculate_factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    else:\n        return n * calculate_factorial(n-1)\n\'\'\'\n\n# Execute the generated code to define the function\nexec(function_code)\n\n# Now use the dynamically defined function\nfor i in range(1, 6):\n    print(f"Factorial of {i} is {calculate_factorial(i)}")\n'
    result = interpreter.execute(code, 'python')
    print('\nDynamic Code Generation Result:')
    print('-' * 50)
    print(result)
    print('-' * 50)

def run_visualization_example(interpreter):
    """
    Run an example that would generate a visualization if matplotlib was allowed.
    This demonstrates handling imports that might not be allowed.
    
    Args:
        interpreter: An instance of a code interpreter
    """
    code = '\nprint("Attempting to create a simple visualization...")\n\ntry:\n    import matplotlib.pyplot as plt\n    import numpy as np\n    \n    # Generate some data\n    x = np.linspace(0, 10, 100)\n    y = np.sin(x)\n    \n    # Create a plot\n    plt.figure(figsize=(8, 4))\n    plt.plot(x, y)\n    plt.title("Sine Wave")\n    plt.xlabel("x")\n    plt.ylabel("sin(x)")\n    plt.grid(True)\n    \n    # Save the plot (would work if matplotlib was available)\n    plt.savefig("examples/output/sine_wave.png")\n    plt.close()\n    \n    print("Visualization created and saved as \'examples/output/sine_wave.png\'")\nexcept ImportError as e:\n    print(f"Import error: {e}")\n    print("Note: This example requires matplotlib to be in the allowed_imports.")\n'
    result = interpreter.execute(code, 'python')
    print('\nVisualization Example Result:')
    print('-' * 50)
    print(result)
    print('-' * 50)

