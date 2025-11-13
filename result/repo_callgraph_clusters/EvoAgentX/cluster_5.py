# Cluster 5

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

def _add_tools(self, tools: List[Toolkit]):
    self.get_action(self.customize_action_name).add_tools(tools)

@property
def action(self) -> Action:
    """
        Get the primary custom action for this agent.
        
        Returns:
            The primary custom action
        """
    return self.get_action(self.customize_action_name)

def get_customize_agent_info(self) -> dict:
    """
        Get the information of the customize agent.
        """
    customize_action = self.get_action(self.customize_action_name)
    action_input_params = customize_action.inputs_format.get_attrs()
    action_output_params = customize_action.outputs_format.get_attrs()
    config = {'class_name': 'CustomizeAgent', 'name': self.name, 'description': self.description, 'prompt': customize_action.prompt, 'prompt_template': customize_action.prompt_template.to_dict() if customize_action.prompt_template is not None else None, 'inputs': [{'name': field, 'type': self._action_input_types[field], 'description': field_info.description, 'required': self._action_input_required[field]} for field, field_info in customize_action.inputs_format.model_fields.items() if field in action_input_params], 'outputs': [{'name': field, 'type': self._action_output_types[field], 'description': field_info.description, 'required': self._action_output_required[field]} for field, field_info in customize_action.outputs_format.model_fields.items() if field in action_output_params], 'system_prompt': self.system_prompt, 'output_parser': self.output_parser.__name__ if self.output_parser is not None else None, 'parse_mode': self.parse_mode, 'parse_func': self.parse_func.__name__ if self.parse_func is not None else None, 'title_format': self.title_format, 'tool_names': [tool.name for tool in customize_action.tools] if customize_action.tools else [], 'max_tool_calls': self.max_tool_calls, 'custom_output_format': self.custom_output_format}
    return config

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

def get_tool_info(self):
    self.tool_info = [{tool.name: [s['function']['description'] for s in tool.get_tool_schemas()]} for tool in self.tools]

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

class OperatorOutput(LLMOutputParser):

    def to_str(self) -> str:
        return json.dumps(self.get_structured_data(), indent=4)

def to_str(self) -> str:
    return json.dumps(self.get_structured_data(), indent=4)

class Custom(Operator):

    def __init__(self, llm: BaseLLM, **kwargs):
        name = 'Custom'
        description = 'Generates anything based on customized input and instruction'
        interface = "custom(input: str, instruction: str) -> dict with key 'response' of type str"
        super().__init__(name=name, description=description, interface=interface, llm=llm, outputs_format=CustomOutput, **kwargs)

    def execute(self, input: str, instruction: str) -> dict:
        prompt = instruction + input
        response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='str')
        output = response.get_structured_data()
        return output

    async def async_execute(self, input: str, instruction: str) -> dict:
        prompt = instruction + input
        response = await self.llm.async_generate(prompt=prompt, parser=self.outputs_format, parse_mode='str')
        output = response.get_structured_data()
        return output

def execute(self, input: str, instruction: str) -> dict:
    prompt = instruction + input
    response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='str')
    output = response.get_structured_data()
    return output

class AnswerGenerate(Operator):

    def __init__(self, llm: BaseLLM, **kwargs):
        name = 'AnswerGenerate'
        description = "Generate step by step based on the input. The step by step thought process is in the field of 'thought', and the final answer is in the field of 'answer'."
        interface = "answer_generate(input: str) -> dict with key 'thought' of type str, 'answer' of type str"
        prompt = kwargs.pop('prompt', ANSWER_GENERATION_PROMPT)
        super().__init__(name=name, description=description, interface=interface, llm=llm, outputs_format=AnswerGenerateOutput, prompt=prompt, **kwargs)

    def execute(self, input: str) -> dict:
        prompt = self.prompt.format(input=input)
        response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
        return response.get_structured_data()

    async def async_execute(self, input: str) -> dict:
        prompt = self.prompt.format(input=input)
        response = await self.llm.async_generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
        return response.get_structured_data()

def execute(self, input: str) -> dict:
    prompt = self.prompt.format(input=input)
    response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
    return response.get_structured_data()

class QAScEnsemble(Operator):

    def __init__(self, llm: BaseLLM, **kwargs):
        name = 'QAScEnsemble'
        description = 'Uses self-consistency to select the solution that appears most frequently in the solution list, improve the selection to enhance the choice of the best solution.'
        interface = "sc_ensemble(solutions: List[str]) -> dict with key 'response' of type str"
        prompt = kwargs.pop('prompt', QA_SC_ENSEMBLE_PROMPT)
        super().__init__(name=name, description=description, interface=interface, llm=llm, outputs_format=ScEnsembleOutput, prompt=prompt, **kwargs)

    def _prepare_solutions(self, solutions: List[str]) -> Tuple[dict, str]:
        answer_mapping = {}
        solution_text = ''
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f'{chr(65 + index)}: \n{str(solution)}\n\n\n'
        return (answer_mapping, solution_text)

    def _process_response(self, response: LLMOutputParser, answer_mapping: dict, solutions: List[str]) -> dict:
        answer: str = response.get_structured_data().get('solution_letter', '')
        answer = answer.strip().upper()
        return {'response': solutions[answer_mapping[answer]]}

    def execute(self, solutions: List[str]) -> dict:
        answer_mapping, solution_text = self._prepare_solutions(solutions)
        prompt = self.prompt.format(solutions=solution_text)
        response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
        return self._process_response(response, answer_mapping, solutions)

    async def async_execute(self, solutions: List[str]) -> dict:
        answer_mapping, solution_text = self._prepare_solutions(solutions)
        prompt = self.prompt.format(solutions=solution_text)
        response = await self.llm.async_generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
        return self._process_response(response, answer_mapping, solutions)

def execute(self, solutions: List[str]) -> dict:
    answer_mapping, solution_text = self._prepare_solutions(solutions)
    prompt = self.prompt.format(solutions=solution_text)
    response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
    return self._process_response(response, answer_mapping, solutions)

class ScEnsemble(Operator):

    def __init__(self, llm: BaseLLM, **kwargs):
        name = 'ScEnsemble'
        description = 'Uses self-consistency to select the solution that appears most frequently in the solution list, improve the selection to enhance the choice of the best solution.'
        interface = "sc_ensemble(solutions: List[str], problem: str) -> dict with key 'response' of type str"
        prompt = kwargs.pop('prompt', SC_ENSEMBLE_PROMPT)
        super().__init__(name=name, description=description, interface=interface, llm=llm, outputs_format=ScEnsembleOutput, prompt=prompt, **kwargs)

    def _prepare_solutions(self, solutions: List[str]) -> Tuple[dict, str]:
        answer_mapping = {}
        solution_text = ''
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f'{chr(65 + index)}: \n{str(solution)}\n\n\n'
        return (answer_mapping, solution_text)

    def _process_response(self, response: LLMOutputParser, answer_mapping: dict, solutions: List[str]) -> dict:
        answer: str = response.get_structured_data().get('solution_letter', '')
        answer = answer.strip().upper()
        return {'response': solutions[answer_mapping[answer]]}

    def execute(self, solutions: List[str], problem: str) -> dict:
        answer_mapping, solution_text = self._prepare_solutions(solutions)
        prompt = self.prompt.format(problem=problem, solutions=solution_text)
        response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
        return self._process_response(response, answer_mapping, solutions)

    async def async_execute(self, solutions: List[str], problem: str) -> dict:
        answer_mapping, solution_text = self._prepare_solutions(solutions)
        prompt = self.prompt.format(problem=problem, solutions=solution_text)
        response = await self.llm.async_generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
        return self._process_response(response, answer_mapping, solutions)

def execute(self, solutions: List[str], problem: str) -> dict:
    answer_mapping, solution_text = self._prepare_solutions(solutions)
    prompt = self.prompt.format(problem=problem, solutions=solution_text)
    response = self.llm.generate(prompt=prompt, parser=self.outputs_format, parse_mode='xml')
    return self._process_response(response, answer_mapping, solutions)

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

class ActionScheduler(Action):
    """
    Determines the next action(s) to execute for a given task using an LLM.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name', None) if 'name' in kwargs else DEFAULT_ACTION_SCHEDULER['name']
        description = kwargs.pop('description', None) if 'description' in kwargs else DEFAULT_ACTION_SCHEDULER['description']
        prompt = kwargs.pop('prompt', None) if 'prompt' in kwargs else DEFAULT_ACTION_SCHEDULER['prompt']
        super().__init__(name=name, description=description, prompt=prompt, outputs_format=NextAction, **kwargs)

    def format_task_input_data(self, data: dict) -> str:
        info_list = []
        for key, value in data.items():
            info_list.append('## {}\n{}'.format(key, value))
        return '\n\n'.join(info_list)

    def check_candidate_action(self, task_name: str, actions: List[str], agent_actions_map: Dict[str, List[str]]):
        unknown_actions = []
        merged_actions = set(chain.from_iterable(agent_actions_map.values()))
        for action in actions:
            if action not in merged_actions:
                unknown_actions.append(action)
        if unknown_actions:
            raise ValueError(f'Unknown actions: {unknown_actions} specified in the `next_actions`. All available actions defined for the task ({task_name}) are {merged_actions}.')

    def get_agent_action_pairs(self, action: str, agent_actions_map: Dict[str, List[str]]) -> List[Tuple[str, str]]:
        pairs = []
        for agent, actions in agent_actions_map.items():
            if action in actions:
                pairs.append((agent, action))
        return pairs

    def _prepare_action_execution(self, task: WorkFlowNode, agent_manager: AgentManager, env: Environment) -> Union[Tuple[NextAction, None], Tuple[None, dict, str]]:
        """
        Prepares common execution logic for both sync and async execute methods.
        
        Args:
            task (WorkFlowNode): The task for which to schedule an action.
            agent_manager (AgentManager): The agent manager providing the agents.
            env (Environment): The execution environment.
            
        Returns:
            Either a tuple with a scheduled action and None if a direct return is possible,
            or a tuple with None, prompt_inputs, and prompt if LLM processing is needed.
        """
        if task.action_graph is not None:
            next_action = NextAction(action_graph=task.action_graph)
            return (next_action, None)
        task_agent_names = task.get_agents()
        if not task_agent_names:
            raise ValueError(f"The task '{task.name}' does not provide any agents for execution!")
        task_agents = [agent_manager.get_agent(name) for name in task_agent_names]
        task_agent_actions_map = {agent.name: [action.name for action in agent.get_all_actions()] for agent in task_agents}
        next_action = None
        candidate_agent_actions = defaultdict(set)
        task_execution_messages = env.get_task_messages(task.name)
        if task_execution_messages and task_execution_messages[-1].next_actions:
            predefined_next_actions = task_execution_messages[-1].next_actions
            self.check_candidate_action(task.name, predefined_next_actions, task_agent_actions_map)
            if len(predefined_next_actions) == 1:
                predefined_next_action = predefined_next_actions[0]
                agent_action_pairs = self.get_agent_action_pairs(predefined_next_action, task_agent_actions_map)
                if len(agent_action_pairs) == 1:
                    next_action = NextAction(agent=agent_action_pairs[0][0], action=agent_action_pairs[0][1], reason=f'Selected because task history indicates a single predefined next action: {predefined_next_action}')
                else:
                    for agent, action in agent_action_pairs:
                        candidate_agent_actions[agent].add(action)
            else:
                for predefined_next_action in predefined_next_actions:
                    agent_action_pairs = self.get_agent_action_pairs(predefined_next_action, task_agent_actions_map)
                    for agent, action in agent_action_pairs:
                        candidate_agent_actions[agent].add(action)
        if not next_action and len(task_agent_names) == 1 and (len(task_agent_actions_map[task_agent_names[0]]) == 1):
            task_agent_name = task_agent_names[0]
            task_action_name = task_agent_actions_map[task_agent_name][0]
            next_action = NextAction(agent=task_agent_name, action=task_action_name, reason=f"Only one agent ('{task_agent_name}') is available, and it has only one action ('{task_action_name}'), making it the obvious choice.")
        if next_action is not None:
            return (next_action, None)
        candidate_agent_actions = candidate_agent_actions or task_agent_actions_map
        agent_actions_info = '\n\n'.join([agent.get_agent_profile(action_names=candidate_agent_actions[agent.name]) for agent in task_agents if agent.name in candidate_agent_actions])
        task_info = task.get_task_info()
        task_input_names = [param.name for param in task.inputs]
        task_input_data: dict = env.get_execution_data(task_input_names)
        task_input_data_info = self.format_task_input_data(data=task_input_data)
        task_execution_history = '\n\n'.join([str(msg) for msg in task_execution_messages])
        prompt_inputs = {'task_info': task_info, 'task_inputs': task_input_data_info, 'task_execution_history': task_execution_history, 'agent_action_list': agent_actions_info}
        prompt = self.prompt.format(**prompt_inputs)
        return (None, prompt_inputs, prompt)

    def execute(self, llm: Optional[BaseLLM]=None, task: WorkFlowNode=None, agent_manager: AgentManager=None, env: Environment=None, sys_msg: Optional[str]=None, return_prompt: bool=True, **kwargs) -> Union[NextAction, Tuple[NextAction, str]]:
        """
        Determine the next actions to take for the given task. 
        If the last message stored in ``next_actions`` specifies the ``next_actions``, choose an action from these actions to execute.

        Args:
            llm (Optional[BaseLLM]): Language model to use for generation.
            task (WorkFlowNode): The task for which to schedule an action.
            agent_manager (AgentManager): The agent manager providing the agents.
            env (Environment): The execution environment.
            sys_msg (Optional[str]): Optional system message for the LLM.
            return_prompt (bool): Whether to return the prompt along with the output.
            
        Returns:
            Union[NextAction, Tuple[NextAction, str]]: The scheduled action and optionally the prompt.
        """
        result = self._prepare_action_execution(task=task, agent_manager=agent_manager, env=env)
        if result[0] is not None:
            next_action, _ = result
            return (next_action, None) if return_prompt else next_action
        _, _, prompt = result
        next_action = llm.generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format)
        if return_prompt:
            return (next_action, prompt)
        return next_action

    async def async_execute(self, llm: Optional[BaseLLM]=None, task: WorkFlowNode=None, agent_manager: AgentManager=None, env: Environment=None, sys_msg: Optional[str]=None, return_prompt: bool=True, **kwargs) -> Union[NextAction, Tuple[NextAction, str]]:
        """
        Asynchronously determine the next actions to take for the given task.
        If the last message stored in ``next_actions`` specifies the ``next_actions``, choose an action from these actions to execute.

        Args:
            llm (Optional[BaseLLM]): Language model to use for generation.
            task (WorkFlowNode): The task for which to schedule an action.
            agent_manager (AgentManager): The agent manager providing the agents.
            env (Environment): The execution environment.
            sys_msg (Optional[str]): Optional system message for the LLM.
            return_prompt (bool): Whether to return the prompt along with the output.
            
        Returns:
            Union[NextAction, Tuple[NextAction, str]]: The scheduled action and optionally the prompt.
        """
        result = self._prepare_action_execution(task=task, agent_manager=agent_manager, env=env)
        if result[0] is not None:
            next_action, _ = result
            return (next_action, None) if return_prompt else next_action
        _, _, prompt = result
        next_action = await llm.async_generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format)
        if return_prompt:
            return (next_action, prompt)
        return next_action

def format_task_input_data(self, data: dict) -> str:
    info_list = []
    for key, value in data.items():
        info_list.append('## {}\n{}'.format(key, value))
    return '\n\n'.join(info_list)

def get_agent_action_pairs(self, action: str, agent_actions_map: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    pairs = []
    for agent, actions in agent_actions_map.items():
        if action in actions:
            pairs.append((agent, action))
    return pairs

def execute(self, llm: Optional[BaseLLM]=None, task: WorkFlowNode=None, agent_manager: AgentManager=None, env: Environment=None, sys_msg: Optional[str]=None, return_prompt: bool=True, **kwargs) -> Union[NextAction, Tuple[NextAction, str]]:
    """
        Determine the next actions to take for the given task. 
        If the last message stored in ``next_actions`` specifies the ``next_actions``, choose an action from these actions to execute.

        Args:
            llm (Optional[BaseLLM]): Language model to use for generation.
            task (WorkFlowNode): The task for which to schedule an action.
            agent_manager (AgentManager): The agent manager providing the agents.
            env (Environment): The execution environment.
            sys_msg (Optional[str]): Optional system message for the LLM.
            return_prompt (bool): Whether to return the prompt along with the output.
            
        Returns:
            Union[NextAction, Tuple[NextAction, str]]: The scheduled action and optionally the prompt.
        """
    result = self._prepare_action_execution(task=task, agent_manager=agent_manager, env=env)
    if result[0] is not None:
        next_action, _ = result
        return (next_action, None) if return_prompt else next_action
    _, _, prompt = result
    next_action = llm.generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format)
    if return_prompt:
        return (next_action, prompt)
    return next_action

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

def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
    data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
    for agent in data.get('agents', []):
        if isinstance(agent, dict) and 'parse_func' in agent and isinstance(agent['parse_func'], Callable):
            agent['parse_func'] = agent['parse_func'].__name__
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

def _edge_exists(self, source: str, target: str, **attr_filters) -> bool:
    if not self.graph.has_edge(source, target):
        return False
    if attr_filters:
        for key, value in attr_filters.items():
            if key not in self.graph[source][target] or self.graph[source][target][key] != value:
                return False
    return True

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

def get_graph_info(self, **kwargs) -> dict:
    """
        Get the information of the workflow graph.
        """
    config = {'class_name': self.__class__.__name__, 'goal': self.goal, 'tasks': [{'name': node.name, 'description': node.description, 'inputs': [param.to_dict(ignore=['class_name']) for param in node.inputs], 'outputs': [param.to_dict(ignore=['class_name']) for param in node.outputs], 'prompt': node.agents[0].get('prompt', None), 'prompt_template': node.agents[0].get('prompt_template', None).to_dict() if node.agents[0].get('prompt_template', None) else None, 'system_prompt': node.agents[0].get('system_prompt', None), 'parse_mode': node.agents[0].get('parse_mode', 'str'), 'parse_func': node.agents[0].get('parse_func', None).__name__ if node.agents[0].get('parse_func', None) else None, 'parse_title': node.agents[0].get('parse_title', None), 'tool_names': node.agents[0].get('tool_names', None)} for node in self.nodes]}
    return config

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

def get_field_names(self) -> List[str]:
    return [name for name, _ in type(self).model_fields.items() if name != 'class_name']

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

def render_tools(self) -> str:
    if not self.tools:
        return ''
    tools_schemas = [tool.get_tool_schemas() for tool in self.tools]
    tools_schemas = [j for i in tools_schemas for j in i]
    return TOOL_CALLING_TEMPLATE.format(tools_description=tools_schemas)

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

def get_config(self) -> dict:
    return self.to_dict()

class StringTemplate(PromptTemplate):

    def render_demonstrations(self, inputs_format: Type[LLMOutputParser], outputs_format: Type[LLMOutputParser], parse_mode: str, title_format: str=None, custom_output_format: str=None, **kwargs) -> str:
        if not self.demonstrations:
            return ''
        if inputs_format is None or outputs_format is None:
            raise ValueError('`inputs_format` and `outputs_format` are required in `render_demonstrations`.')
        if len(inputs_format.get_attrs()) == 0 or len(outputs_format.get_attrs()) == 0:
            raise ValueError('`inputs_format` and `outputs_format` must have at least one attribute.')
        demo_str_list = []
        for i, demo in enumerate(self.demonstrations):
            demo_str = f'Example {i + 1}:\n'
            demo_str += '### Inputs\n'
            input_fields = inputs_format.get_attrs()
            input_values = {field: demo.get(field, 'Not provided') for field in input_fields}
            demo_str += self.render_input_example(inputs_format, input_values, missing_field_value='Not provided')
            demo_str += '\n\n'
            demo_str += '### Outputs\n'
            output_fields = outputs_format.get_attrs()
            output_values = {field: demo.get(field, 'Not provided') for field in output_fields}
            if custom_output_format is not None or parse_mode in [None, 'str', 'custom']:
                output_str = '\n'.join((f'{field}:\n{value}' for field, value in output_values.items()))
            else:
                output_template, output_keys = self.get_output_template(outputs_format, parse_mode=parse_mode, title_format=title_format)
                output_str = output_template.format(**output_values)
                output_str = output_str.replace('(Optional)', '')
            demo_str += output_str
            demo_str_list.append(demo_str)
        result = '### Examples\n' + '\n\n'.join(demo_str_list) + '\n\n=== End of Examples ===\n'
        return result

    def render_history(self) -> str:
        result = '### History\n{history}'.format(history=self.history)
        return result

    def render_inputs(self, inputs_format: Type[LLMOutputParser], values: dict) -> str:
        if inputs_format is None and values is None or (inputs_format is not None and len(inputs_format.get_attrs()) == 0):
            return ''
        self.check_required_inputs(inputs_format, values)
        input_str = '### Inputs\nThese are the input values provided by the user (with input names emplasized):\n'
        input_str += self.render_input_example(inputs_format, values, missing_field_value='Not provided')
        input_str += '\n'
        return input_str

    def format(self, system_prompt: Optional[str]=None, values: Optional[dict]=None, inputs_format: Optional[Type[LLMOutputParser]]=None, outputs_format: Optional[Type[LLMOutputParser]]=None, parse_mode: Optional[str]='title', title_format: Optional[str]='## {title}', custom_output_format: Optional[str]=None, **kwargs) -> str:
        """
        Format the prompt template.

        Convert the prompt template into a prompt string. 
        It will sequentially concatenate the following sections (if provided): instruction, context, tools, constraints, demonstrations, history, inputs and outputs.

        Args: 
            values (Optional[dict]): The values to be used to render the inputs. 
            inputs_format (Optional[Type[LLMOutputParser]]): Define the input variables. If provided, it will be used to extract inputs (specified in `inputs_format`) from `values` and use them to render the inputs section. 
                Otherwise, will use all fields in `values` (if provided) directly to render the inputs section. 
            outputs_format (Optional[Type[LLMOutputParser]]): Define the output variables. If provided, it will be used to construct the output format based on `parse_mode`. 
                Otherwise, a default output format will be used. 
            parse_mode (Optional[str]): The mode to parse the outputs, chosen from ["json", "xml", "title", "str", "custom"]. It will be used to construct the output format if `outputs_format` is provided. 
                Moreover, if `parse_mode` is "title", `title_format` will be used to format the title of the outputs. 
            title_format (Optional[str]): The format to format the title of the outputs. Default is "## {title}". Only used when `parse_mode` is "title".
            custom_output_format (Optional[str]): User-specified output format. If provided, it will be directly used in the `Outputs Format` section of the prompt. Otherwise, the output format will be constructed from `outputs_format` and `parse_mode`. 
            **kwargs: Additional keyword arguments. 
        
        Returns: 
            str: The formatted prompt string.
        """
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f'Invalid parse mode `{parse_mode}` for `{self.__class__.__name__}.format`. Valid modes are: {PARSER_VALID_MODE}.')
        prompt_pieces = []
        prompt_pieces.append(self._render_system_message(system_prompt))
        if self.demonstrations:
            prompt_pieces.append(self.render_demonstrations(inputs_format=inputs_format, outputs_format=outputs_format, parse_mode=parse_mode, title_format=title_format, custom_output_format=custom_output_format))
        if self.history:
            prompt_pieces.append(self.render_history())
        if inputs_format or values:
            prompt_pieces.append('-' * 20)
            prompt_pieces.append(self.render_inputs(inputs_format, values))
        if custom_output_format:
            prompt_pieces.append(f'### Outputs Format\n{custom_output_format}')
        else:
            prompt_pieces.append(self.render_outputs(outputs_format, parse_mode, title_format))
        prompt_pieces = [piece for piece in prompt_pieces if piece]
        prompt = '\n'.join(prompt_pieces)
        return prompt.strip()

def render_demonstrations(self, inputs_format: Type[LLMOutputParser], outputs_format: Type[LLMOutputParser], parse_mode: str, title_format: str=None, custom_output_format: str=None, **kwargs) -> str:
    if not self.demonstrations:
        return ''
    if inputs_format is None or outputs_format is None:
        raise ValueError('`inputs_format` and `outputs_format` are required in `render_demonstrations`.')
    if len(inputs_format.get_attrs()) == 0 or len(outputs_format.get_attrs()) == 0:
        raise ValueError('`inputs_format` and `outputs_format` must have at least one attribute.')
    demo_str_list = []
    for i, demo in enumerate(self.demonstrations):
        demo_str = f'Example {i + 1}:\n'
        demo_str += '### Inputs\n'
        input_fields = inputs_format.get_attrs()
        input_values = {field: demo.get(field, 'Not provided') for field in input_fields}
        demo_str += self.render_input_example(inputs_format, input_values, missing_field_value='Not provided')
        demo_str += '\n\n'
        demo_str += '### Outputs\n'
        output_fields = outputs_format.get_attrs()
        output_values = {field: demo.get(field, 'Not provided') for field in output_fields}
        if custom_output_format is not None or parse_mode in [None, 'str', 'custom']:
            output_str = '\n'.join((f'{field}:\n{value}' for field, value in output_values.items()))
        else:
            output_template, output_keys = self.get_output_template(outputs_format, parse_mode=parse_mode, title_format=title_format)
            output_str = output_template.format(**output_values)
            output_str = output_str.replace('(Optional)', '')
        demo_str += output_str
        demo_str_list.append(demo_str)
    result = '### Examples\n' + '\n\n'.join(demo_str_list) + '\n\n=== End of Examples ===\n'
    return result

def render_history(self) -> str:
    result = '### History\n{history}'.format(history=self.history)
    return result

def render_inputs(self, inputs_format: Type[LLMOutputParser], values: dict) -> str:
    if inputs_format is None and values is None or (inputs_format is not None and len(inputs_format.get_attrs()) == 0):
        return ''
    self.check_required_inputs(inputs_format, values)
    input_str = '### Inputs\nThese are the input values provided by the user (with input names emplasized):\n'
    input_str += self.render_input_example(inputs_format, values, missing_field_value='Not provided')
    input_str += '\n'
    return input_str

class ChatTemplate(StringTemplate):

    def _create_message(self, role: str, content: str) -> dict:
        """Create a message dictionary with role and content."""
        return {'role': role, 'content': content}

    def render_demonstrations(self, inputs_format: Type[LLMOutputParser], outputs_format: Type[LLMOutputParser], parse_mode: str, title_format: str=None, custom_output_format: str=None) -> List[dict]:
        """
        Render demonstrations as alternating user and assistant messages.
        """
        if not self.demonstrations:
            return []
        if inputs_format is None or outputs_format is None:
            raise ValueError('`inputs_format` and `outputs_format` are required in `render_demonstrations`.')
        if len(inputs_format.get_attrs()) == 0 or len(outputs_format.get_attrs()) == 0:
            raise ValueError('`inputs_format` and `outputs_format` must have at least one attribute.')
        messages = []
        for demo in self.demonstrations:
            input_fields = inputs_format.get_attrs()
            input_values = {field: demo.get(field, 'Not provided') for field in input_fields}
            user_content = self.render_input_example(inputs_format, input_values, missing_field_value='Not provided')
            messages.append(self._create_message('user', user_content))
            output_fields = outputs_format.get_attrs()
            output_values = {field: demo.get(field, 'Not provided') for field in output_fields}
            if custom_output_format is not None or parse_mode in [None, 'str', 'custom']:
                assistant_content = '\n'.join((f'{field}:\n{value}' for field, value in output_values.items()))
            else:
                output_template, output_keys = self.get_output_template(outputs_format, parse_mode=parse_mode, title_format=title_format)
                assistant_content = output_template.format(**output_values)
                assistant_content = assistant_content.replace('(Optional)', '')
            messages.append(self._create_message('assistant', assistant_content))
        return messages

    def render_inputs(self, inputs_format: Optional[Type[LLMOutputParser]], values: Optional[dict]) -> str:
        if inputs_format is None and values is None or (inputs_format is not None and len(inputs_format.get_attrs()) == 0):
            return ''
        self.check_required_inputs(inputs_format, values)
        input_str = '### Inputs\n'
        input_str += self.render_input_example(inputs_format, values, missing_field_value='Not provided')
        input_str += '\n'
        return input_str

    def render_current_user_message(self, values: Optional[dict], inputs_format: Optional[Type[LLMOutputParser]], outputs_format: Optional[Type[LLMOutputParser]], parse_mode: str, title_format: str, custom_output_format: Optional[str]=None) -> str:
        """Render the current user input message."""
        input_pieces = []
        if inputs_format or values:
            input_pieces.append(self.render_inputs(inputs_format, values))
        if custom_output_format:
            input_pieces.append(f'### Outputs Format\n{custom_output_format}')
        else:
            input_pieces.append(self.render_outputs(outputs_format, parse_mode, title_format))
        input_pieces = [piece for piece in input_pieces if piece]
        user_message = '\n'.join(input_pieces)
        return user_message.strip()

    def format(self, system_prompt: Optional[str]=None, values: Optional[dict]=None, inputs_format: Optional[Type[LLMOutputParser]]=None, outputs_format: Optional[Type[LLMOutputParser]]=None, parse_mode: Optional[str]='title', title_format: Optional[str]='## {title}', custom_output_format: Optional[str]=None, **kwargs) -> List[dict]:
        """
        Format the prompt template into a list of chat messages.
        
        The messages will be formatted in the following order:
        1. System message (containing system prompt, instruction, context, tools, and constraints)
        2. Few-shot examples (if provided in demonstrations)
        3. Conversation history (if provided)
        4. Current user input (with input values and output format requirements)
        
        Args:
            system_prompt (Optional[str]): Additional system prompt to prepend to the template.
            values (Optional[dict]): The values to be used to render the inputs.
            inputs_format (Optional[Type[LLMOutputParser]]): Define the input variables.
            outputs_format (Optional[Type[LLMOutputParser]]): Define the output variables.
            parse_mode (Optional[str]): The mode to parse the outputs.
            title_format (Optional[str]): The format to format the title of the outputs.
            custom_output_format (Optional[str]): User-specified output format.
            **kwargs: Additional keyword arguments.
            
        Returns:
            List[dict]: A list of chat messages in the format:
            [
                {"role": "system", "content": system_message},
                # Begin few-shot examples
                {"role": "user", "content": few_shot_example_1_input},
                {"role": "assistant", "content": few_shot_example_1_output},
                ...
                # End few-shot examples
                {"role": "user", "content": current_input},
            ]
        """
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f'Invalid parse mode `{parse_mode}` for `{self.__class__.__name__}.prompt`. Valid modes are: {PARSER_VALID_MODE}.')
        messages = []
        system_content = self._render_system_message(system_prompt)
        messages.append(self._create_message('system', system_content))
        if self.demonstrations:
            messages.extend(self.render_demonstrations(inputs_format=inputs_format, outputs_format=outputs_format, parse_mode=parse_mode, title_format=title_format, custom_output_format=custom_output_format))
        current_input = self.render_current_user_message(values=values, inputs_format=inputs_format, outputs_format=outputs_format, parse_mode=parse_mode, title_format=title_format, custom_output_format=custom_output_format)
        messages.append(self._create_message('user', current_input))
        return messages

def render_demonstrations(self, inputs_format: Type[LLMOutputParser], outputs_format: Type[LLMOutputParser], parse_mode: str, title_format: str=None, custom_output_format: str=None) -> List[dict]:
    """
        Render demonstrations as alternating user and assistant messages.
        """
    if not self.demonstrations:
        return []
    if inputs_format is None or outputs_format is None:
        raise ValueError('`inputs_format` and `outputs_format` are required in `render_demonstrations`.')
    if len(inputs_format.get_attrs()) == 0 or len(outputs_format.get_attrs()) == 0:
        raise ValueError('`inputs_format` and `outputs_format` must have at least one attribute.')
    messages = []
    for demo in self.demonstrations:
        input_fields = inputs_format.get_attrs()
        input_values = {field: demo.get(field, 'Not provided') for field in input_fields}
        user_content = self.render_input_example(inputs_format, input_values, missing_field_value='Not provided')
        messages.append(self._create_message('user', user_content))
        output_fields = outputs_format.get_attrs()
        output_values = {field: demo.get(field, 'Not provided') for field in output_fields}
        if custom_output_format is not None or parse_mode in [None, 'str', 'custom']:
            assistant_content = '\n'.join((f'{field}:\n{value}' for field, value in output_values.items()))
        else:
            output_template, output_keys = self.get_output_template(outputs_format, parse_mode=parse_mode, title_format=title_format)
            assistant_content = output_template.format(**output_values)
            assistant_content = assistant_content.replace('(Optional)', '')
        messages.append(self._create_message('assistant', assistant_content))
    return messages

def render_inputs(self, inputs_format: Optional[Type[LLMOutputParser]], values: Optional[dict]) -> str:
    if inputs_format is None and values is None or (inputs_format is not None and len(inputs_format.get_attrs()) == 0):
        return ''
    self.check_required_inputs(inputs_format, values)
    input_str = '### Inputs\n'
    input_str += self.render_input_example(inputs_format, values, missing_field_value='Not provided')
    input_str += '\n'
    return input_str

def build_agent_prompt(problem: str, transcript_text: str, role: str, agent_id: int, round_index: int, total_rounds: int) -> str:
    """Construct agent prompt (XML-structured output)."""
    return DEBATER_AGENT_PROMPT.format(agent_id=agent_id, role=role, round_index=round_index + 1, total_rounds=total_rounds, problem=problem, transcript_text=transcript_text)

def build_judge_prompt(problem: str, transcript_text: str, roles: list) -> str:
    """Construct judge prompt (XML-structured output)."""
    roles_text = '\n'.join([f'#{i}: {r}' for i, r in enumerate(roles)])
    return JUDGE_AGENT_PROMPT.format(problem=problem, roles_text=roles_text, transcript_text=transcript_text)

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

def format_demo(demo: dict) -> str:
    demo_str = 'Inputs:\n'
    inputs = {name: demo.get(name, 'Not provided') for name in input_names}
    demo_str += '\n'.join([f'{name}:\n{_escape_braces(str(value))}' for name, value in inputs.items()])
    demo_str += '\n\nOutputs:\n'
    outputs = {name: demo.get(name, 'Not provided') for name in output_names}
    demo_str += '\n'.join([f'{name}:\n{_escape_braces(str(value))}' for name, value in outputs.items()])
    return demo_str

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

class ExperienceUtils:

    def __init__(self, root_path: str):
        self.root_path = root_path

    def load_experience(self, path=None, mode: str='Graph'):
        if mode == 'Graph':
            rounds_dir = self.root_path
        else:
            rounds_dir = path
        experience_data = defaultdict(lambda: {'score': None, 'success': {}, 'failure': {}})
        for round_dir in os.listdir(rounds_dir):
            if os.path.isdir(os.path.join(rounds_dir, round_dir)) and round_dir.startswith('round_'):
                round_path = os.path.join(rounds_dir, round_dir)
                try:
                    round_number = int(round_dir.split('_')[1])
                    json_file_path = os.path.join(round_path, 'experience.json')
                    if os.path.exists(json_file_path):
                        data = load_json(json_file_path, type='json')
                        father_node = data['father node']
                        if experience_data[father_node]['score'] is None:
                            experience_data[father_node]['score'] = data['before']
                        if data['succeed']:
                            experience_data[father_node]['success'][round_number] = {'modification': data['modification'], 'score': data['after']}
                        else:
                            experience_data[father_node]['failure'][round_number] = {'modification': data['modification'], 'score': data['after']}
                except Exception as e:
                    logger.info(f'Error processing {round_dir}: {str(e)}')
        experience_data = dict(experience_data)
        output_path = os.path.join(rounds_dir, 'processed_experience.json')
        save_json(experience_data, output_path, type='json', use_indent=True)
        return experience_data

    def format_experience(self, processed_experience, sample_round):
        experience_data = processed_experience.get(sample_round)
        if experience_data:
            experience = f'Original Score: {experience_data['score']}\n'
            experience += 'These are some conclusions drawn from experience:\n\n'
            for key, value in experience_data['failure'].items():
                experience += f'-Absolutely prohibit {value['modification']} (Score: {value['score']})\n'
            for key, value in experience_data['success'].items():
                experience += f'-Absolutely prohibit {value['modification']} \n'
            experience += '\n\nNote: Take into account past failures and avoid repeating the same mistakes, as these failures indicate that these approaches are ineffective. You must fundamentally change your way of thinking, rather than simply using more advanced Python syntax like for, if, else, etc., or modifying the prompt.'
        else:
            experience = f'No experience data found for round {sample_round}.'
        return experience

    def check_modification(self, processed_experience, modification, sample_round):
        experience_data = processed_experience.get(sample_round)
        if experience_data:
            for key, value in experience_data['failure'].items():
                if value['modification'] == modification:
                    return False
            for key, value in experience_data['success'].items():
                if value['modification'] == modification:
                    return False
            return True
        else:
            return True

    def create_experience_data(self, sample, modification):
        return {'father node': sample['round'], 'modification': modification, 'before': sample['score'], 'after': None, 'succeed': None}

    def update_experience(self, directory, experience, avg_score):
        experience['after'] = avg_score
        experience['succeed'] = bool(avg_score > experience['before'])
        save_json(experience, os.path.join(directory, 'experience.json'), type='json', use_indent=True)

def format_experience(self, processed_experience, sample_round):
    experience_data = processed_experience.get(sample_round)
    if experience_data:
        experience = f'Original Score: {experience_data['score']}\n'
        experience += 'These are some conclusions drawn from experience:\n\n'
        for key, value in experience_data['failure'].items():
            experience += f'-Absolutely prohibit {value['modification']} (Score: {value['score']})\n'
        for key, value in experience_data['success'].items():
            experience += f'-Absolutely prohibit {value['modification']} \n'
        experience += '\n\nNote: Take into account past failures and avoid repeating the same mistakes, as these failures indicate that these approaches are ineffective. You must fundamentally change your way of thinking, rather than simply using more advanced Python syntax like for, if, else, etc., or modifying the prompt.'
    else:
        experience = f'No experience data found for round {sample_round}.'
    return experience

def check_modification(self, processed_experience, modification, sample_round):
    experience_data = processed_experience.get(sample_round)
    if experience_data:
        for key, value in experience_data['failure'].items():
            if value['modification'] == modification:
                return False
        for key, value in experience_data['success'].items():
            if value['modification'] == modification:
                return False
        return True
    else:
        return True

class GraphUtils:

    def __init__(self, root_path: str):
        self.root_path = root_path

    def create_round_directory(self, graph_path: str, round_number: int) -> str:
        directory = os.path.join(graph_path, f'round_{round_number}')
        os.makedirs(directory, exist_ok=True)
        return directory

    def load_graph(self, round_number: int, workflows_path: str):
        workflows_path = workflows_path.replace('\\', '.').replace('/', '.')
        graph_module_name = f'{workflows_path}.round_{round_number}.graph'
        try:
            graph_module = __import__(graph_module_name, fromlist=[''])
            graph_class = getattr(graph_module, 'Workflow')
            return graph_class
        except ImportError as e:
            logger.info(f'Error loading graph for round {round_number}: {e}')
            raise

    def read_graph_files(self, round_number: int, workflows_path: str):
        prompt_file_path = os.path.join(workflows_path, f'round_{round_number}', 'prompt.py')
        graph_file_path = os.path.join(workflows_path, f'round_{round_number}', 'graph.py')
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as file:
                prompt_content = file.read()
            with open(graph_file_path, 'r', encoding='utf-8') as file:
                graph_content = file.read()
        except FileNotFoundError as e:
            logger.info(f'Error: File not found for round {round_number}: {e}')
            raise
        except Exception as e:
            logger.info(f'Error loading prompt for round {round_number}: {e}')
            raise
        return (prompt_content, graph_content)

    def extract_solve_graph(self, graph_load: str) -> List[str]:
        pattern = 'class Workflow:.+'
        return re.findall(pattern, graph_load, re.DOTALL)

    def load_operators_description(self, operators: List[str], llm: BaseLLM) -> str:
        operators_description = ''
        for id, operator in enumerate(operators):
            operator_description = self._load_operator_description(id + 1, operator, llm)
            operators_description += f'{operator_description}\n'
        return operators_description

    def _load_operator_description(self, id: int, operator_name: str, llm: BaseLLM) -> str:
        if operator_name not in OPERATOR_MAP:
            raise ValueError(f'Operator {operator_name} not Found in OPERATOR_MAP! Available operators: {OPERATOR_MAP.keys()}')
        operator: Operator = OPERATOR_MAP[operator_name](llm=llm)
        return f'{id}. {operator_name}: {operator.description}, with interface {operator.interface}).'

    def create_graph_optimize_prompt(self, experience: str, score: float, graph: str, prompt: str, operator_description: str, type: str, log_data: str) -> str:
        graph_input = WORKFLOW_INPUT.format(experience=experience, score=score, graph=graph, prompt=prompt, operator_description=operator_description, type=type, log=log_data)
        graph_system = WORKFLOW_OPTIMIZE_PROMPT.format(type=type)
        return graph_input + WORKFLOW_CUSTOM_USE + graph_system

    def get_graph_optimize_response(self, graph_optimize_node):
        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                response = graph_optimize_node.instruct_content.model_dump()
                return response
            except Exception as e:
                retries += 1
                logger.info(f'Error generating prediction: {e}. Retrying... ({retries}/{max_retries})')
                if retries == max_retries:
                    logger.info('Maximum retries reached. Skipping this sample.')
                    break
                traceback.print_exc()
                time.sleep(5)
        return None

    def write_graph_files(self, directory: str, response: dict):
        graph = WORKFLOW_TEMPLATE.format(graph=response['graph'])
        with open(os.path.join(directory, 'graph.py'), 'w', encoding='utf-8') as file:
            file.write(graph)
        with open(os.path.join(directory, 'prompt.py'), 'w', encoding='utf-8') as file:
            prompt = response['prompt'].replace('prompt_custom.', '')
            file.write(prompt)
        with open(os.path.join(directory, '__init__.py'), 'w', encoding='utf-8') as file:
            file.write('')
        self.update_prompt_import(os.path.join(directory, 'graph.py'), directory)

    def update_prompt_import(self, graph_file: str, prompt_folder: str):
        project_root = Path(os.getcwd())
        prompt_folder_path = Path(prompt_folder)
        if not prompt_folder_path.is_absolute():
            prompt_folder_full_path = Path(os.path.join(project_root, prompt_folder))
            if not prompt_folder_full_path.exists():
                raise ValueError(f'Prompt folder {prompt_folder_full_path} does not exist!')
            prompt_folder_path = prompt_folder_full_path
        try:
            relative_path = prompt_folder_path.relative_to(project_root)
        except ValueError:
            raise ValueError(f'Prompt folder {prompt_folder} must be within the project directory')
        import_path = str(relative_path).replace(os.sep, '.')
        if import_path.startswith('.'):
            import_path = import_path[1:]
        with open(graph_file, 'r', encoding='utf-8') as file:
            graph_content = file.read()
        pattern = 'import .*?\\.prompt as prompt_custom'
        replacement = f'import {import_path}.prompt as prompt_custom'
        new_content = re.sub(pattern, replacement, graph_content)
        with open(graph_file, 'w', encoding='utf-8') as file:
            file.write(new_content)

def create_graph_optimize_prompt(self, experience: str, score: float, graph: str, prompt: str, operator_description: str, type: str, log_data: str) -> str:
    graph_input = WORKFLOW_INPUT.format(experience=experience, score=score, graph=graph, prompt=prompt, operator_description=operator_description, type=type, log=log_data)
    graph_system = WORKFLOW_OPTIMIZE_PROMPT.format(type=type)
    return graph_input + WORKFLOW_CUSTOM_USE + graph_system

class OpenAPIConverter(BaseAPIConverter):
    """
    OpenAPI (Swagger) specification converter
    """

    def convert_to_toolkit(self) -> APIToolkit:
        """Convert OpenAPI specification to APIToolkit"""
        service_name = self.input_schema.get('info', {}).get('title', 'API Service')
        base_url = self._get_base_url()
        tools = []
        paths = self.input_schema.get('paths', {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    tool = self._create_tool_from_operation(path, method, operation, base_url)
                    if tool:
                        tools.append(tool)
        return APIToolkit(name=service_name, tools=tools, base_url=base_url, auth_config=self.auth_config, common_headers={'Content-Type': 'application/json'})

    def _get_base_url(self) -> str:
        """Get base URL from the OpenAPI specification"""
        servers = self.input_schema.get('servers', [])
        if servers:
            return servers[0].get('url', '')
        host = self.input_schema.get('host', '')
        base_path = self.input_schema.get('basePath', '')
        schemes = self.input_schema.get('schemes', ['https'])
        if host:
            return f'{schemes[0]}://{host}{base_path}'
        return ''

    def _create_tool_from_operation(self, path: str, method: str, operation: Dict[str, Any], base_url: str) -> Optional[APITool]:
        """Create a tool from an OpenAPI operation"""
        try:
            operation_id = operation.get('operationId')
            if not operation_id:
                clean_path = path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
                operation_id = f'{method.lower()}_{clean_path}'
            inputs, required = self._extract_openapi_parameters(operation)
            api_function = self._create_api_function({'url': base_url + path, 'method': method.upper(), 'operation': operation})
            return APITool(name=operation_id, description=operation.get('summary', operation.get('description', '')), inputs=inputs, required=required, endpoint_config={'url': base_url + path, 'method': method.upper(), 'operation': operation}, auth_config=self.auth_config, function=api_function)
        except Exception as e:
            logger.warning(f'Failed to create tool for {method.upper()} {path}: {e}')
            return None

    def _extract_openapi_parameters(self, operation: Dict[str, Any]) -> tuple:
        """Extract parameters from an OpenAPI operation"""
        inputs = {}
        required = []
        parameters = operation.get('parameters', [])
        for param in parameters:
            param_name = param.get('name', '')
            param_schema = param.get('schema', {})
            param_type = param_schema.get('type', 'string')
            inputs[param_name] = {'type': param_type, 'description': param.get('description', '')}
            if param.get('required', False):
                required.append(param_name)
        request_body = operation.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            for media_type, media_schema in content.items():
                if 'application/json' in media_type:
                    schema = media_schema.get('schema', {})
                    properties = schema.get('properties', {})
                    for prop_name, prop_schema in properties.items():
                        inputs[prop_name] = {'type': prop_schema.get('type', 'string'), 'description': prop_schema.get('description', '')}
                        if prop_name in schema.get('required', []):
                            required.append(prop_name)
        return (inputs, required)

    def _create_api_function(self, endpoint_config: Dict[str, Any]) -> Callable:
        """Create OpenAPI execution function"""
        url = endpoint_config['url']
        method = endpoint_config['method']
        operation = endpoint_config['operation']

        def api_call(**kwargs):
            path_params = {}
            query_params = {}
            body_data = {}
            parameters = operation.get('parameters', [])
            param_locations = {param['name']: param.get('in', 'query') for param in parameters}
            for key, value in kwargs.items():
                if value is None:
                    continue
                location = param_locations.get(key, 'body')
                if location == 'path':
                    path_params[key] = value
                elif location == 'query':
                    query_params[key] = value
                else:
                    body_data[key] = value
            final_url = url
            for param_name, param_value in path_params.items():
                final_url = final_url.replace(f'{{{param_name}}}', str(param_value))
            headers = {'Content-Type': 'application/json'}
            if hasattr(self, 'auth_config') and self.auth_config:
                if 'api_key' in self.auth_config:
                    key_name = self.auth_config.get('key_name', 'X-API-Key')
                    headers[key_name] = self.auth_config['api_key']
            try:
                if method in ['GET', 'DELETE']:
                    response = requests.request(method=method, url=final_url, params=query_params, headers=headers, timeout=30)
                else:
                    response = requests.request(method=method, url=final_url, params=query_params, json=body_data if body_data else None, headers=headers, timeout=30)
                response.raise_for_status()
                try:
                    return response.json()
                except (ValueError, json.JSONDecodeError):
                    return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f'API request failed: {e}')
                raise
        api_call.__name__ = f'api_call_{method.lower()}'
        return api_call

def _extract_openapi_parameters(self, operation: Dict[str, Any]) -> tuple:
    """Extract parameters from an OpenAPI operation"""
    inputs = {}
    required = []
    parameters = operation.get('parameters', [])
    for param in parameters:
        param_name = param.get('name', '')
        param_schema = param.get('schema', {})
        param_type = param_schema.get('type', 'string')
        inputs[param_name] = {'type': param_type, 'description': param.get('description', '')}
        if param.get('required', False):
            required.append(param_name)
    request_body = operation.get('requestBody', {})
    if request_body:
        content = request_body.get('content', {})
        for media_type, media_schema in content.items():
            if 'application/json' in media_type:
                schema = media_schema.get('schema', {})
                properties = schema.get('properties', {})
                for prop_name, prop_schema in properties.items():
                    inputs[prop_name] = {'type': prop_schema.get('type', 'string'), 'description': prop_schema.get('description', '')}
                    if prop_name in schema.get('required', []):
                        required.append(prop_name)
    return (inputs, required)

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

class BrowserBase(BaseModule):
    """
    A tool for interacting with web browsers using Selenium.
    Allows agents to navigate to URLs, interact with elements, extract information,
    and more from web pages.
    
    Key Features:
    - Auto-initialization: Browser is automatically initialized when any method is first called
    - Auto-cleanup: Browser is automatically closed when the instance is destroyed
    - No manual initialization or cleanup required
    """
    timeout: int = Field(default=10, description='Default timeout in seconds for browser operations')
    browser_type: str = Field(default='chrome', description="Type of browser to use ('chrome', 'firefox', 'safari', 'edge')")
    headless: bool = Field(default=False, description='Whether to run the browser in headless mode')
    user_data_dir: Optional[str] = Field(default=None, description='User data directory for persistent browser sessions')

    def __init__(self, name: str='Browser Tool', browser_type: str='chrome', headless: bool=False, timeout: int=10, **kwargs):
        """
        Initialize the browser tool with Selenium WebDriver.
        
        Args:
            name (str): Name of the tool
            browser_type (str): Type of browser to use ('chrome', 'firefox', 'safari', 'edge')
            headless (bool): Whether to run the browser in headless mode
            timeout (int): Default timeout in seconds for browser operations
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, timeout=timeout, browser_type=browser_type, headless=headless, **kwargs)
        self.driver = None
        self.element_references = {}

    def _check_driver_initialized(self) -> Union[None, Dict[str, Any]]:
        """
        Check if the browser driver is initialized. If not, initialize it automatically.
        
        Returns:
            Union[None, Dict[str, Any]]: None if driver is initialized, error response if initialization fails
        """
        if not self.driver:
            init_result = self.initialize_browser()
            if init_result['status'] == 'error':
                return init_result
        return None

    def _get_selector_by_type(self, selector_type: str) -> Union[str, Dict[str, Any]]:
        """
        Get the Selenium By selector for the given selector type.
        
        Args:
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            
        Returns:
            Union[str, Dict[str, Any]]: The By selector or error response
        """
        by_type = SELECTOR_MAP.get(selector_type.lower())
        if not by_type:
            return {'status': 'error', 'message': f'Invalid selector type: {selector_type}'}
        return by_type

    def _wait_for_page_load(self, timeout: Optional[int]=None) -> bool:
        """
        Wait for the page to load completely.
        
        Args:
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            bool: True if page loaded, False if timed out
        """
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            return True
        except TimeoutException:
            return False

    def _parse_element_reference(self, ref: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse an element reference into selector type and selector.
        
        Args:
            ref (str): Element reference ID from the page snapshot
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: 
                (selector_type, selector, error_message) - error_message is None if successful
        """
        if not self.element_references:
            return (None, None, 'No page snapshot available. Use browser_snapshot or navigate_to_url first.')
        stored_ref = self.element_references.get(ref)
        if not stored_ref:
            return (None, None, f"Element reference '{ref}' not found. Use browser_snapshot or navigate_to_url first.")
        if ':' in stored_ref:
            ref_parts = stored_ref.split(':', 1)
            if len(ref_parts) != 2:
                return (None, None, f'Invalid stored reference format: {stored_ref}')
            selector_type, selector = ref_parts
            return (selector_type, selector, None)
        return (None, None, f'Invalid stored reference format: {stored_ref}')

    def _find_element_with_wait(self, by_type: str, selector: str, timeout: Optional[int]=None, wait_condition=EC.presence_of_element_located) -> Tuple[Optional[Any], Optional[str]]:
        """
        Find an element on the page with wait condition.
        
        Args:
            by_type (str): Selenium By selector type
            selector (str): The selector string
            timeout (int, optional): Custom timeout for this operation
            wait_condition: The EC condition to wait for
            
        Returns:
            Tuple[Optional[Any], Optional[str]]: (element, error_message) - error_message is None if successful
        """
        timeout = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(wait_condition((by_type, selector)))
            return (element, None)
        except TimeoutException:
            return (None, f'Element not found or condition not met with selector: {selector}')
        except Exception as e:
            logger.error(f'Error finding element {selector}: {str(e)}')
            return (None, str(e))

    def _handle_function_params(self, function_params: Optional[list], function_name: str, param_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract parameters from nested function_params format.
        
        Args:
            function_params (list, optional): Nested function parameters
            function_name (str): The function name to look for
            param_mapping (Dict[str, str]): Mapping of parameter names
            
        Returns:
            Dict[str, Any]: Extracted parameters
        """
        result = {}
        if not function_params:
            return result
        for param in function_params:
            fn_name = param.get('function_name', '')
            if fn_name == function_name or fn_name in param_mapping.get('alt_names', []):
                args = param.get('function_args', {})
                for param_name, result_name in param_mapping.items():
                    if param_name == 'alt_names':
                        continue
                    if param_name in args:
                        result[result_name] = args[param_name]
                break
        return result

    def initialize_browser(self, function_params: list=None) -> Dict[str, Any]:
        """
        Start or restart a browser session. This method is called automatically when needed.
        
        Note: This method is now called automatically by other browser methods when the browser
        is not initialized. Manual initialization is no longer required.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "initialize_browser", "function_args": {}}]
           
        Args:
            function_params (list, optional): Nested function parameters
        
        Returns:
            Dict[str, Any]: Status information about the browser initialization
        """
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f'Error closing existing browser session: {str(e)}')
            options = None
            if self.browser_type == 'chrome':
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-gpu-sandbox')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    logger.info(f'Using user data directory: {self.user_data_dir}')
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            elif self.browser_type == 'firefox':
                from selenium.webdriver.firefox.options import Options
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=options)
            elif self.browser_type == 'safari':
                self.driver = webdriver.Safari()
            elif self.browser_type == 'edge':
                from selenium.webdriver.edge.options import Options
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-gpu-sandbox')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    logger.info(f'Using user data directory: {self.user_data_dir}')
                self.driver = webdriver.Edge(options=options)
            else:
                return {'status': 'error', 'message': f'Unsupported browser type: {self.browser_type}'}
            self.driver.set_page_load_timeout(self.timeout)
            return {'status': 'success', 'message': f'Browser {self.browser_type} initialized successfully'}
        except Exception as e:
            logger.error(f'Error initializing browser: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def navigate_to_url(self, url: str=None, timeout: int=None, function_params: list=None) -> Dict[str, Any]:
        """
        Navigate to a URL and capture a snapshot of the page. This provides element references used for interaction.
        
        This function supports multiple parameter styles:
        1. Standard style: url parameter
        2. Nested function_params style:
           function_params=[{"function_name": "navigate_to_url", "function_args": {"url": "..."}}]
        
        Args:
            url (str, optional): The complete URL (with https://) to navigate to
            timeout (int, optional): Custom timeout in seconds (default: 10)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Information about the navigation result and page snapshot
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params and (not url):
            params = self._handle_function_params(function_params, 'navigate_to_url', {'url': 'url', 'timeout': 'timeout', 'alt_names': ['browser_navigate']})
            url = params.get('url')
            timeout = params.get('timeout', timeout)
        if not url:
            return {'status': 'error', 'message': 'URL parameter is required'}
        timeout = timeout or self.timeout
        try:
            self.driver.get(url)
            page_loaded = self._wait_for_page_load(timeout)
            if not page_loaded:
                logger.warning(f'Page load timeout for URL: {url}, but continuing with snapshot')
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] == 'success':
                return {'status': 'success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
            else:
                return {'status': 'partial_success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot')}
        except TimeoutException:
            return {'status': 'timeout', 'message': f'Timed out loading URL: {url}'}
        except Exception as e:
            logger.error(f'Error navigating to URL {url}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def find_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Find an element on the current page and return information about it.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found element
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'Element not found with {selector_type}: {selector}'}
            element_properties = self._extract_element_properties(element, selector)
            return {'status': 'success', 'element': element_properties}
        except Exception as e:
            logger.error(f'Error finding element {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _extract_element_properties(self, element, selector: str) -> Dict[str, Any]:
        """
        Extract common properties from a WebElement.
        
        Args:
            element: The Selenium WebElement
            selector (str): The selector used to find the element (for error messages)
            
        Returns:
            Dict[str, Any]: Element properties
        """
        element_properties = {'text': element.text, 'tag_name': element.tag_name, 'is_displayed': element.is_displayed(), 'is_enabled': element.is_enabled()}
        for attr in ['href', 'id', 'class']:
            try:
                value = element.get_attribute(attr)
                if value:
                    element_properties[attr] = value
            except StaleElementReferenceException:
                logger.warning(f'Element became stale when trying to get {attr} attribute for {selector}')
            except Exception as e:
                logger.warning(f'Could not get {attr} attribute for {selector}: {str(e)}')
        return element_properties

    def find_multiple_elements(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Find multiple elements on the current page and return information about them.
        
        Args:
            selector (str): The selector to find the elements
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found elements
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'No elements found with {selector_type}: {selector}'}
            elements = self.driver.find_elements(by_type, selector)
            elements_properties = []
            for idx, element in enumerate(elements):
                try:
                    element_properties = self._extract_element_properties(element, f'{selector}[{idx}]')
                    element_properties['index'] = idx
                    elements_properties.append(element_properties)
                except StaleElementReferenceException:
                    logger.warning(f'Element {idx} became stale while extracting properties')
                except Exception as e:
                    logger.warning(f'Error extracting properties for element {idx}: {str(e)}')
            return {'status': 'success', 'count': len(elements_properties), 'elements': elements_properties}
        except Exception as e:
            logger.error(f'Error finding elements {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def click_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Click on an element on the current page.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Result of the click operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.element_to_be_clickable)
            if error:
                return {'status': 'not_found', 'message': f'Element not clickable with {selector_type}: {selector}'}
            element.click()
            page_loaded = self._wait_for_page_load(timeout)
            if not page_loaded:
                return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'selector': selector, 'current_url': self.driver.current_url}
            return {'status': 'success', 'message': f'Clicked element with {selector_type}: {selector}', 'current_url': self.driver.current_url, 'title': self.driver.title}
        except Exception as e:
            logger.error(f'Error clicking element {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def input_text(self, element: str=None, ref: str=None, text: str=None, submit: bool=False, slowly: bool=True, function_params: list=None) -> Dict[str, Any]:
        """
        Type text into a form field, search box, or other input element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. Use browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID), text
        2. Nested function_params style:
           function_params=[{"function_name": "browser_type", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of the element (e.g., 'Search field', 'Username input')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            text (str, optional): Text to input into the element
            submit (bool): Press Enter after typing to submit forms (default: false)
            slowly (bool): Type one character at a time to trigger JS events (default: true)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the text input operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params:
            params = self._handle_function_params(function_params, 'input_text', {'element': 'element', 'ref': 'ref', 'text': 'text', 'submit': 'submit', 'slowly': 'slowly', 'alt_names': ['browser_type']})
            element = params.get('element', element)
            ref = params.get('ref', ref)
            text = params.get('text', text)
            if 'submit' in params:
                submit = params['submit']
            if 'slowly' in params:
                slowly = params['slowly']
        if not ref or not text:
            return {'status': 'error', 'message': 'Both ref and text parameters are required'}
        selector_type, selector, error = self._parse_element_reference(ref)
        if error:
            return {'status': 'error', 'message': error}
        element_desc = element or ref
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
            if error:
                return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
            web_element.clear()
            if slowly:
                for char in text:
                    web_element.send_keys(char)
                    time.sleep(0.05)
            else:
                web_element.send_keys(text)
            if submit:
                from selenium.webdriver.common.keys import Keys
                web_element.send_keys(Keys.ENTER)
                page_loaded = self._wait_for_page_load(self.timeout)
                if not page_loaded:
                    self.browser_snapshot()
                    return {'status': 'partial_success', 'message': 'Text entered and submitted, but page load timed out', 'element': element_desc, 'text': text}
                snapshot_result = self.browser_snapshot()
                if snapshot_result['status'] != 'success':
                    logger.warning(f'Failed to capture snapshot after form submission: {snapshot_result.get('message')}')
            return {'status': 'success', 'message': f'Successfully input text into {element_desc}' + (' and submitted' if submit else ''), 'element': element_desc, 'text': text}
        except TimeoutException:
            return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
        except Exception as e:
            logger.error(f'Error inputting text to element {element_desc}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def get_page_content(self) -> Dict[str, Any]:
        """
        Get the current page title, URL and body content.
        
        Returns:
            Dict[str, Any]: Information about the current page
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            body_content = self.driver.execute_script('\n                var body = document.body;\n                return body ? body.outerHTML : "";\n            ')
            element_summary = self.driver.execute_script('\n                // Get common interactive elements\n                var summary = {\n                    links: [],\n                    buttons: [],\n                    inputs: [],\n                    forms: []\n                };\n                \n                // Get links\n                var links = document.querySelectorAll(\'a\');\n                for (var i = 0; i < Math.min(links.length, 20); i++) {\n                    var link = links[i];\n                    summary.links.push({\n                        text: link.textContent.trim().substring(0, 50),\n                        href: link.getAttribute(\'href\'),\n                        id: link.id,\n                        class: link.className\n                    });\n                }\n                \n                // Get buttons\n                var buttons = document.querySelectorAll(\'button, input[type="button"], input[type="submit"]\');\n                for (var i = 0; i < Math.min(buttons.length, 20); i++) {\n                    var button = buttons[i];\n                    summary.buttons.push({\n                        text: button.textContent ? button.textContent.trim().substring(0, 50) : button.value,\n                        id: button.id,\n                        class: button.className,\n                        type: button.type\n                    });\n                }\n                \n                // Get inputs\n                var inputs = document.querySelectorAll(\'input:not([type="button"]):not([type="submit"]), textarea, select\');\n                for (var i = 0; i < Math.min(inputs.length, 20); i++) {\n                    var input = inputs[i];\n                    summary.inputs.push({\n                        type: input.type,\n                        name: input.name,\n                        id: input.id,\n                        placeholder: input.placeholder\n                    });\n                }\n                \n                // Get forms\n                var forms = document.querySelectorAll(\'form\');\n                for (var i = 0; i < Math.min(forms.length, 10); i++) {\n                    var form = forms[i];\n                    summary.forms.push({\n                        id: form.id,\n                        action: form.action,\n                        method: form.method\n                    });\n                }\n                \n                return summary;\n            ')
            return {'status': 'success', 'title': title, 'url': current_url, 'body_content': body_content, 'element_summary': element_summary}
        except Exception as e:
            logger.error(f'Error getting page content: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def switch_to_frame(self, frame_reference: str, reference_type: str='index') -> Dict[str, Any]:
        """
        Switch to a frame on the page.
        
        Args:
            frame_reference (str): Reference to the frame (index, name, or ID)
            reference_type (str): Type of reference ('index', 'name', 'id', 'element')
            
        Returns:
            Dict[str, Any]: Result of the frame switch operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            if reference_type == 'index':
                try:
                    index = int(frame_reference)
                    self.driver.switch_to.frame(index)
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid frame index: {frame_reference}'}
            elif reference_type == 'name' or reference_type == 'id':
                self.driver.switch_to.frame(frame_reference)
            elif reference_type == 'element':
                selector_parts = frame_reference.split(':', 1)
                if len(selector_parts) != 2:
                    return {'status': 'error', 'message': "Element reference must be in format 'selector_type:selector'"}
                selector_type, selector = selector_parts
                element_result = self.find_element(selector, selector_type)
                if element_result['status'] != 'success':
                    return {'status': 'error', 'message': f'Could not find frame element: {element_result['message']}'}
                selector_map = {'css': By.CSS_SELECTOR, 'xpath': By.XPATH, 'id': By.ID, 'class': By.CLASS_NAME, 'name': By.NAME, 'tag': By.TAG_NAME}
                by_type = selector_map.get(selector_type.lower())
                element = self.driver.find_element(by_type, selector)
                self.driver.switch_to.frame(element)
            else:
                return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
            return {'status': 'success', 'message': f'Switched to frame using {reference_type}: {frame_reference}'}
        except Exception as e:
            logger.error(f'Error switching to frame {frame_reference}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def switch_to_window(self, window_reference: str, reference_type: str='index') -> Dict[str, Any]:
        """
        Switch to a window or tab.
        
        Args:
            window_reference (str): Reference to the window (index, handle, or title)
            reference_type (str): Type of reference ('index', 'handle', 'title')
            
        Returns:
            Dict[str, Any]: Result of the window switch operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            window_handles = self.driver.window_handles
            if not window_handles:
                return {'status': 'error', 'message': 'No window handles available'}
            if reference_type == 'index':
                try:
                    index = int(window_reference)
                    if index < 0 or index >= len(window_handles):
                        return {'status': 'error', 'message': f'Window index out of range: {index}'}
                    self.driver.switch_to.window(window_handles[index])
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid window index: {window_reference}'}
            elif reference_type == 'handle':
                if window_reference not in window_handles:
                    return {'status': 'error', 'message': f'Window handle not found: {window_reference}'}
                self.driver.switch_to.window(window_reference)
            elif reference_type == 'title':
                current_handle = self.driver.current_window_handle
                window_found = False
                for handle in window_handles:
                    try:
                        self.driver.switch_to.window(handle)
                        if self.driver.title == window_reference:
                            window_found = True
                            break
                    except Exception:
                        pass
                if not window_found:
                    self.driver.switch_to.window(current_handle)
                    return {'status': 'error', 'message': f"No window with title '{window_reference}' found"}
            else:
                return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
            return {'status': 'success', 'message': f'Switched to window using {reference_type}: {window_reference}', 'title': self.driver.title, 'url': self.driver.current_url}
        except Exception as e:
            logger.error(f'Error switching to window {window_reference}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def select_dropdown_option(self, select_selector: str, option_value: str, select_by: str='value', selector_type: str='css') -> Dict[str, Any]:
        """
        Select an option from a dropdown
        select_by can be 'value', 'text', or 'index'
        
        Args:
            select_selector (str): The selector to find the dropdown element
            option_value (str): The value to select (depends on select_by)
            select_by (str): Method to select by ('value', 'text', 'index')
            selector_type (str): Type of selector for the dropdown
            
        Returns:
            Dict[str, Any]: Result of the selection operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            from selenium.webdriver.support.ui import Select
            by_type = self._get_selector_by_type(selector_type)
            if isinstance(by_type, dict):
                return by_type
            element, error = self._find_element_with_wait(by_type, select_selector, self.timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'Dropdown element not found with {selector_type}: {select_selector}'}
            select = Select(element)
            if select_by.lower() == 'value':
                select.select_by_value(option_value)
            elif select_by.lower() == 'text':
                select.select_by_visible_text(option_value)
            elif select_by.lower() == 'index':
                try:
                    select.select_by_index(int(option_value))
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid index value: {option_value}. Must be an integer.'}
            else:
                return {'status': 'error', 'message': f'Invalid select_by option: {select_by}'}
            return {'status': 'success', 'message': f'Selected option with {select_by}: {option_value}'}
        except Exception as e:
            logger.error(f'Error selecting dropdown option: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def close_browser(self) -> Dict[str, Any]:
        """
        Close the browser and end the session. Call this when you're done to free resources.
        
        Returns:
            Dict[str, Any]: Status of the browser closure
        """
        if not self.driver:
            return {'status': 'success', 'message': 'Browser already closed'}
        try:
            self.driver.quit()
            self.driver = None
            return {'status': 'success', 'message': 'Browser closed successfully'}
        except Exception as e:
            logger.error(f'Error closing browser: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def browser_click(self, element: str=None, ref: str=None, function_params: list=None) -> Dict[str, Any]:
        """
        Click on a button, link, or other clickable element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. You MUST call browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        Common usage pattern:
        1. First get a snapshot: browser_snapshot() or navigate_to_url()
        2. Find the element reference (e.g. 'e0', 'e1') from the snapshot's interactive_elements
        3. Use that reference to click: browser_click(element='Login button', ref='e0')
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID)
        2. Nested function_params style:
           function_params=[{"function_name": "browser_click", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of what you're clicking (e.g., 'Login button', 'Next page link')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the click operation with detailed feedback
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params and (not ref):
            params = self._handle_function_params(function_params, 'browser_click', {'element': 'element', 'ref': 'ref'})
            element = params.get('element', element)
            ref = params.get('ref', ref)
        if not ref:
            return {'status': 'error', 'message': 'Element reference (ref) parameter is required. You must first call browser_snapshot() or navigate_to_url() to get element references.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to get page elements', "2. Find the element reference (e.g. 'e0') in the response's interactive_elements", "3. Use that reference to click: browser_click(element='Button name', ref='e0')"]}
        if not self.element_references:
            return {'status': 'error', 'message': 'No element references found. You must first capture a page snapshot.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to capture the page state', '2. Use the element references returned in the snapshot']}
        selector_type, selector, error = self._parse_element_reference(ref)
        if error:
            return {'status': 'error', 'message': error, 'help': "Make sure you're using a valid element reference from a recent snapshot"}
        element_desc = element or ref
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            try:
                element_exists = self.driver.find_element(by_type, selector)
            except Exception:
                return {'status': 'not_found', 'message': f'Element not found: {element_desc}', 'suggestion': 'The page may have changed. Try getting a new snapshot with browser_snapshot()'}
            web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
            if error:
                try:
                    is_visible = element_exists.is_displayed()
                    is_enabled = element_exists.is_enabled()
                    element_tag = element_exists.tag_name
                    element_classes = element_exists.get_attribute('class')
                    return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'element_state': {'visible': is_visible, 'enabled': is_enabled, 'tag': element_tag, 'classes': element_classes}, 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
                except Exception:
                    return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
            web_element.click()
            page_loaded = self._wait_for_page_load(self.timeout)
            if not page_loaded:
                snapshot_result = self.browser_snapshot()
                return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'element': element_desc, 'current_url': self.driver.current_url, 'snapshot': snapshot_result if snapshot_result['status'] == 'success' else None, 'suggestion': 'The page might still be loading. You may want to wait and take another snapshot.'}
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] == 'success':
                return {'status': 'success', 'message': f'Successfully clicked on {element_desc}', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
            else:
                return {'status': 'success', 'message': f'Successfully clicked on {element_desc} but snapshot failed', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot'), 'suggestion': 'You may want to take another snapshot with browser_snapshot()'}
        except TimeoutException:
            return {'status': 'timeout', 'message': f'Timed out waiting for element to be clickable: {element_desc}', 'suggestion': 'The element might be taking too long to load or become clickable'}
        except Exception as e:
            logger.error(f'Error clicking element: {str(e)}')
            return {'status': 'error', 'message': str(e), 'element': element_desc, 'suggestion': 'Try getting a new snapshot of the page with browser_snapshot()'}

    def _classify_element_interactivity(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an element's interactivity based on its properties.
        This method contains all rules for determining if an element is interactive or editable.
        
        Args:
            element_data (Dict[str, Any]): Element data including properties, attributes, etc.
            
        Returns:
            Dict[str, Any]: Element data with interactivity classifications added
        """
        element_data['interactable'] = False
        element_data['editable'] = False
        tag_name = element_data.get('properties', {}).get('tag', '').upper()
        role = element_data.get('attributes', {}).get('role', '').lower()
        is_disabled = element_data.get('attributes', {}).get('disabled') is not None or element_data.get('attributes', {}).get('aria-disabled') == 'true' or element_data.get('attributes', {}).get('aria-hidden') == 'true'
        is_visible = element_data.get('visible', True)
        if not is_disabled and is_visible:
            interactive_tags = {'A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'DETAILS', 'AUDIO', 'VIDEO', 'IFRAME', 'EMBED', 'OBJECT', 'SUMMARY', 'MENU'}
            interactive_roles = {'button', 'link', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'searchbox', 'slider', 'spinbutton', 'switch', 'tab', 'textbox', 'combobox', 'listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'toolbar', 'tree', 'treegrid'}
            has_interactive_attrs = any([element_data.get('attributes', {}).get(attr) is not None for attr in ['onclick', 'onkeydown', 'onkeyup', 'onmousedown', 'onmouseup', 'tabindex']])
            element_data['interactable'] = tag_name in interactive_tags or role in interactive_roles or has_interactive_attrs
            editable_input_types = {'text', 'search', 'email', 'number', 'tel', 'url', 'password'}
            editable_roles = {'textbox', 'searchbox', 'spinbutton'}
            element_data['editable'] = tag_name == 'INPUT' and element_data.get('attributes', {}).get('type', 'text').lower() in editable_input_types or tag_name == 'TEXTAREA' or element_data.get('attributes', {}).get('contenteditable') == 'true' or (role in editable_roles)
        return element_data

    def _process_accessibility_tree(self, accessibility_tree):
        """
        Process the accessibility tree to extract all elements and store their references.
        
        This method processes all elements in the page structure, assigns unique IDs,
        and stores their selectors for later interaction.
        
        Args:
            accessibility_tree (dict): The accessibility tree from JavaScript
            
        Returns:
            list: A list of all elements with their IDs and properties
        """
        all_elements = []

        def extract_elements(node, path='', index=0):
            if not node:
                return index
            current_path = path + '/' + (node.get('name') or node.get('role') or 'element')
            element_id = f'e{index}'
            element_info = {'id': element_id, 'description': current_path.strip('/'), 'purpose': node.get('semantic_info', {}).get('purpose', ''), 'label': node.get('semantic_info', {}).get('label', ''), 'category': node.get('semantic_info', {}).get('category', ''), 'isPrimary': node.get('semantic_info', {}).get('isPrimary', False), 'visible': node.get('visible', True), 'properties': node.get('properties', {}), 'attributes': node.get('attributes', {})}
            if 'all_refs' in node:
                self.element_references[element_id] = node['all_refs'][0]
            element_info = self._classify_element_interactivity(element_info)
            all_elements.append(element_info)
            index += 1
            for child in node.get('children', []):
                index = extract_elements(child, current_path, index)
            return index
        extract_elements(accessibility_tree)
        return all_elements

    def browser_snapshot(self, function_params: list=None) -> Dict[str, Any]:
        """
        Capture a fresh snapshot of the current page with all interactive elements. 
        Use after page state changes not caused by navigation or clicking.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_snapshot", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The accessibility snapshot of the page with interactive elements
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            accessibility_tree = self.driver.execute_script("\n                function getAccessibilityTree(node, depth = 0, maxDepth = 10) {\n                    if (!node || depth > maxDepth) return null;\n                    \n                    let result = {\n                        role: node.role || node.tagName,\n                        name: node.name || '',\n                        type: node.type || '',\n                        value: node.value || '',\n                        description: node.description || '',\n                        properties: {},\n                        visible: isElementVisible(node)\n                    };\n                    \n                    // Helper function for element visibility\n                    function isElementVisible(element) {\n                        if (!element.getBoundingClientRect) return true;\n                        const style = window.getComputedStyle(element);\n                        const rect = element.getBoundingClientRect();\n                        \n                        // Check basic visibility\n                        const isVisible = style.display !== 'none' && \n                                        style.visibility !== 'hidden' && \n                                        style.opacity !== '0' &&\n                                        rect.width > 0 && \n                                        rect.height > 0;\n                                        \n                        // Check if element is in viewport\n                        const isInViewport = rect.top >= 0 &&\n                                           rect.left >= 0 &&\n                                           rect.bottom <= window.innerHeight &&\n                                           rect.right <= window.innerWidth;\n                                           \n                        return isVisible && isInViewport;\n                    }\n                    \n                    // Add text content\n                    if (node.textContent) {\n                        result.text_content = node.textContent.trim();\n                    }\n\n                    // Add identifier properties for references\n                    if (node.id) result.properties.id = node.id;\n                    if (node.className) result.properties.class = node.className;\n                    if (node.tagName) result.properties.tag = node.tagName.toLowerCase();\n                    \n                    // Add attributes\n                    if (node.attributes) {\n                        result.attributes = {};\n                        for (let attr of node.attributes) {\n                            result.attributes[attr.name] = attr.value;\n                        }\n                    }\n\n                    // Add custom ref property that combines selector types\n                    let refs = [];\n                    // Store all possible selectors, but don't use them as primary ref\n                    if (node.id) refs.push(`id:${node.id}`);\n                    if (node.className && typeof node.className === 'string') \n                        refs.push(`class:${node.className}`);\n                    if (node.tagName) refs.push(`tag:${node.tagName.toLowerCase()}`);\n                    \n                    // For inputs, add name attribute\n                    if (node.getAttribute && node.getAttribute('name')) {\n                        result.properties.name = node.getAttribute('name');\n                        refs.push(`name:${node.getAttribute('name')}`);\n                    }\n                    \n                    // Create XPath and CSS selectors\n                    try {\n                        // CSS selector\n                        let cssPath = getCssPath(node);\n                        if (cssPath) refs.push(`css:${cssPath}`);\n                        \n                        // XPath\n                        let xpath = getXPath(node);\n                        if (xpath) refs.push(`xpath:${xpath}`);\n                    } catch (e) {}\n                    \n                    // Store all refs but don't set primary ref here\n                    if (refs.length > 0) {\n                        result.all_refs = refs;\n                    }\n\n                    // Add semantic information about the element\n                    result.semantic_info = {\n                        // What the element represents\n                        purpose: (function() {\n                            if (node.tagName === 'INPUT') {\n                                if (node.type === 'submit') return 'submit button';\n                                if (node.type === 'search') return 'search box';\n                                if (node.type === 'text') return 'text input';\n                                return `${node.type || 'text'} input`;\n                            }\n                            if (node.tagName === 'BUTTON') return 'button';\n                            if (node.tagName === 'A') return 'link';\n                            if (node.tagName === 'SELECT') return 'dropdown';\n                            if (node.tagName === 'TEXTAREA') return 'text area';\n                            if (node.getAttribute('role')) return node.getAttribute('role');\n                            return 'interactive element';\n                        })(),\n                        \n                        // The visible or accessible text\n                        label: (function() {\n                            return node.getAttribute('aria-label') ||\n                                   node.getAttribute('title') ||\n                                   node.getAttribute('placeholder') ||\n                                   node.getAttribute('alt') ||\n                                   (node.tagName === 'INPUT' ? node.value : node.textContent.trim());\n                        })(),\n                        \n                        // Is this a primary action?\n                        isPrimary: !!(\n                            node.classList.contains('primary') ||\n                            node.getAttribute('aria-label')?.toLowerCase().includes('search') ||\n                            node.getAttribute('title')?.toLowerCase().includes('search') ||\n                            node.type === 'search' ||\n                            node.getAttribute('role') === 'main' ||\n                            node.id?.toLowerCase().includes('main') ||\n                            node.classList.contains('main')\n                        ),\n                        \n                        // Basic category\n                        category: (function() {\n                            if (node.type === 'search' || \n                                node.getAttribute('role') === 'searchbox') return 'search';\n                            if (node.type === 'submit' || \n                                node.tagName === 'BUTTON' ||\n                                node.getAttribute('role') === 'button') return 'action';\n                            if (node.tagName === 'A' ||\n                                node.getAttribute('role') === 'link') return 'navigation';\n                            if (node.tagName === 'INPUT' || \n                                node.tagName === 'TEXTAREA' ||\n                                node.getAttribute('role') === 'textbox') return 'input';\n                            if (node.tagName === 'SELECT' ||\n                                ['listbox', 'combobox'].includes(node.getAttribute('role'))) return 'selection';\n                            return 'interactive';\n                        })()\n                    };\n                    \n                    // Process children\n                    result.children = [];\n                    if (node.children) {\n                        for (let i = 0; i < node.children.length; i++) {\n                            const childTree = getAccessibilityTree(node.children[i], depth + 1, maxDepth);\n                            if (childTree) {\n                                result.children.push(childTree);\n                            }\n                        }\n                    }\n                    \n                    return result;\n                }\n                \n                return getAccessibilityTree(document.body);\n            ")
            all_elements = self._process_accessibility_tree(accessibility_tree)
            page_content = html2text.html2text(self.driver.page_source)
            return {'status': 'success', 'title': title, 'url': current_url, 'accessibility_tree': accessibility_tree, 'page_content': page_content, 'interactive_elements': [e for e in all_elements if e.get('interactable') or e.get('editable')]}
        except Exception as e:
            logger.error(f'Error generating accessibility snapshot: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def browser_console_messages(self, function_params: list=None) -> Dict[str, Any]:
        """
        Retrieve JavaScript console messages (logs, warnings, errors) from the browser for debugging.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_console_messages", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The console messages including logs, warnings and errors
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            logs = self._collect_browser_logs()
            return {'status': 'success', 'console_messages': logs}
        except Exception as e:
            logger.error(f'Error retrieving console messages: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _collect_browser_logs(self) -> List[Dict[str, Any]]:
        """
        Collect logs from both the browser driver and JavaScript console.
        
        Returns:
            List[Dict[str, Any]]: Combined logs from both sources
        """
        logs = []
        try:
            browser_logs = self.driver.get_log('browser')
            for log in browser_logs:
                level = log.get('level', '').upper()
                if level == 'SEVERE':
                    level = 'ERROR'
                elif level == 'INFO':
                    level = 'LOG'
                logs.append({'level': level, 'message': log.get('message', ''), 'timestamp': log.get('timestamp', '')})
        except Exception as log_error:
            logs.append({'level': 'WARNING', 'message': f'Could not retrieve browser logs: {str(log_error)}', 'timestamp': ''})
        try:
            self.driver.execute_script("\n                if (!window._consoleLogs) {\n                    window._consoleLogs = [];\n                    \n                    // Store original console methods\n                    const originalConsole = {\n                        log: console.log,\n                        info: console.info,\n                        warn: console.warn,\n                        error: console.error,\n                        debug: console.debug\n                    };\n                    \n                    // Helper function to add message with proper level\n                    function addMessage(level, args) {\n                        window._consoleLogs.push({\n                            level: level.toUpperCase(),\n                            message: Array.from(args).join(' '),\n                            timestamp: new Date().toISOString()\n                        });\n                    }\n                    \n                    // Override console methods to capture logs\n                    console.log = function() {\n                        addMessage('LOG', arguments);\n                        originalConsole.log.apply(console, arguments);\n                    };\n                    \n                    console.info = function() {\n                        addMessage('INFO', arguments);\n                        originalConsole.info.apply(console, arguments);\n                    };\n                    \n                    console.warn = function() {\n                        addMessage('WARN', arguments);\n                        originalConsole.warn.apply(console, arguments);\n                    };\n                    \n                    console.error = function() {\n                        addMessage('ERROR', arguments);\n                        originalConsole.error.apply(console, arguments);\n                    };\n                    \n                    console.debug = function() {\n                        addMessage('DEBUG', arguments);\n                        originalConsole.debug.apply(console, arguments);\n                    };\n                }\n            ")
            time.sleep(2)
            js_logs = self.driver.execute_script('return window._consoleLogs || [];')
            for log in js_logs:
                if log not in logs:
                    logs.append(log)
        except Exception as js_error:
            logs.append({'level': 'WARNING', 'message': f'Could not retrieve JavaScript console logs: {str(js_error)}', 'timestamp': ''})
        return logs

    def __del__(self):
        """
        Destructor to automatically close the browser when the instance is destroyed.
        """
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.info('Browser automatically closed on cleanup')
            except Exception as e:
                logger.warning(f'Error during automatic browser cleanup: {str(e)}')

def _handle_function_params(self, function_params: Optional[list], function_name: str, param_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
        Extract parameters from nested function_params format.
        
        Args:
            function_params (list, optional): Nested function parameters
            function_name (str): The function name to look for
            param_mapping (Dict[str, str]): Mapping of parameter names
            
        Returns:
            Dict[str, Any]: Extracted parameters
        """
    result = {}
    if not function_params:
        return result
    for param in function_params:
        fn_name = param.get('function_name', '')
        if fn_name == function_name or fn_name in param_mapping.get('alt_names', []):
            args = param.get('function_args', {})
            for param_name, result_name in param_mapping.items():
                if param_name == 'alt_names':
                    continue
                if param_name in args:
                    result[result_name] = args[param_name]
            break
    return result

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

def validate_parameters(model: str, params: Dict, operation: str='generation') -> Dict:
    validated_params = {}
    warnings = []
    errors = []
    for param, value in params.items():
        if value is None:
            continue
        ok, msg = validate_parameter(model, param, value, operation)
        if ok:
            validated_params[param] = value
        elif 'not supported' in msg:
            warnings.append(msg)
        else:
            errors.append(msg)
    return {'validated_params': validated_params, 'warnings': warnings, 'errors': errors}

def build_validation_params(**kwargs) -> Dict:
    return {k: v for k, v in kwargs.items() if v is not None}

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

class SimplePromptBreeder:

    def __init__(self, llm: BaseLLM, **kwargs):
        self.llm = llm
        self.kwargs = kwargs

    def generate_mutation_prompt(self, task_description: str, **kwargs) -> str:
        """
        Generate the mutation prompt for optimization.
        """
        thinking_style = random.choice(thinking_styles)
        hyper_mutation_prompt = thinking_style + '\n\nProblem Description: ' + task_description + '.\n' + 'Output: '
        mutation_prompt = self.llm.generate(prompt=hyper_mutation_prompt, system_message='You are a helpful assistant').content
        return mutation_prompt

    def get_mutation_prompt(self, task_description: str, order: Literal['zero-order', 'first-order'], **kwargs) -> str:
        """
        Get the mutation prompt for optimization.
        """
        if order == 'zero-order':
            mutation_prompt = self.generate_mutation_prompt(task_description=task_description)
        elif order == 'first-order':
            mutation_prompt = random.choice(mutation_prompts)
        else:
            raise ValueError(f"Invalid order: {order}. The order should be either 'zero-order' or 'first-order'.")
        return mutation_prompt

    def generate_prompt(self, task_description: str, prompt: str, order: Literal['zero-order', 'first-order'], **kwargs) -> str:
        """
        Generate the prompt for optimization. 
        
        Args:
            task_description (str): The description of the task, normally the goal of the workflow. 
            prompt (str): The prompt to optimize.
            order (Literal["zero-order", "first-order"]): The order of the mutation prompt.
        
        Returns:
            str: The optimized prompt.
        """
        mutation_prompt = self.get_mutation_prompt(task_description=task_description, order=order)
        prompt = mutation_prompt + '\n\nINSTRUCTION:\n\n' + prompt
        new_prompt = self.llm.generate(prompt=prompt, system_message='You are a helpful assistant').content
        return new_prompt

def generate_prompt(self, task_description: str, prompt: str, order: Literal['zero-order', 'first-order'], **kwargs) -> str:
    """
        Generate the prompt for optimization. 
        
        Args:
            task_description (str): The description of the task, normally the goal of the workflow. 
            prompt (str): The prompt to optimize.
            order (Literal["zero-order", "first-order"]): The order of the mutation prompt.
        
        Returns:
            str: The optimized prompt.
        """
    mutation_prompt = self.get_mutation_prompt(task_description=task_description, order=order)
    prompt = mutation_prompt + '\n\nINSTRUCTION:\n\n' + prompt
    new_prompt = self.llm.generate(prompt=prompt, system_message='You are a helpful assistant').content
    return new_prompt

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

class TextGradEngine(EngineLM):

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def generate(self, prompt: str, system_prompt: str=None, **kwargs):
        with suppress_logger_info():
            response = self.llm.generate(prompt, system_prompt=system_prompt, **kwargs)
            return response.content

    def __call__(self, prompt: str, **kwargs):
        return self.generate(prompt, **kwargs)

def generate(self, prompt: str, system_prompt: str=None, **kwargs):
    with suppress_logger_info():
        response = self.llm.generate(prompt, system_prompt=system_prompt, **kwargs)
        return response.content

def __call__(self, prompt: str, **kwargs):
    return self.generate(prompt, **kwargs)

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

def forward(self, prompt=None, messages=None, **kwargs):
    response = self.model.generate(prompt=prompt, messages=messages, **kwargs)
    return [response.content]

def generate(self, *args, **kwargs):
    return self.model.generate(*args, **kwargs)

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

def to_dict(self) -> Dict:
    """Convert document to dictionary for serialization."""
    return {'doc_id': self.doc_id, 'text': self.text, 'metadata': self.metadata.model_dump(), 'embedding': self.embedding, 'excluded_embed_metadata_keys': self.excluded_embed_metadata_keys, 'excluded_llm_metadata_keys': self.excluded_llm_metadata_keys, 'relationships': {str(k): v for k, v in self.relationships.items()}, 'metadata_template': self.metadata_template, 'metadata_separator': self.metadata_separator, 'text_template': self.text_template}

def to_json(self, indent: int=2) -> str:
    """Convert document to JSON string."""
    return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

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

def to_json(self, indent: int=2, round_trip=True) -> str:
    """Convert corpus to JSON string."""
    return json.dumps(self.to_dict(round_trip), indent=indent, ensure_ascii=False)

class BasicLLMSynonymRetriever(BasePGRetriever):

    def __init__(self, graph_store: PropertyGraphStore, include_text: bool=True, include_properties: bool=False, synonym_prompt: str=DEFAULT_SYNONYM_EXPAND_TEMPLATE, max_keywords: int=10, path_depth: int=2, limit: int=30, output_parsing_fn: Optional[Callable]=None, llm: Optional[BaseLLM]=None, **kwargs: Any) -> None:
        self._llm = llm
        self._synonym_prompt = synonym_prompt
        self._output_parsing_fn = output_parsing_fn
        self._max_keywords = max_keywords
        self._path_depth = path_depth
        self._limit = limit
        super().__init__(graph_store=graph_store, include_text=include_text, include_properties=include_properties, **kwargs)

    def _parse_llm_output(self, output: str) -> List[str]:
        if self._output_parsing_fn:
            matches = self._output_parsing_fn(output)
        else:
            matches = output.strip().split('^')
        return [x.strip().capitalize().replace(' ', '_') for x in matches if x.strip()]

    def _prepare_matches(self, matches: List[str], limit: Optional[int]=None) -> List[NodeWithScore]:
        kg_nodes = self._graph_store.get(ids=matches)
        triplets = self._graph_store.get_rel_map(kg_nodes, depth=self._path_depth, limit=limit or self._limit, ignore_rels=[KG_SOURCE_REL])
        return self._get_nodes_with_score(triplets)

    async def _aprepare_matches(self, matches: List[str], limit: Optional[int]=None) -> List[NodeWithScore]:
        kg_nodes = await self._graph_store.aget(ids=matches)
        triplets = await self._graph_store.aget_rel_map(kg_nodes, depth=self._path_depth, limit=limit or self._limit, ignore_rels=[KG_SOURCE_REL])
        return self._get_nodes_with_score(triplets)

    def retrieve_from_graph(self, query_bundle: Query, limit: Optional[int]=None) -> List[NodeWithScore]:
        synonym_prompt = self._synonym_prompt.format_map({'max_keywords': self._max_keywords, 'query_str': query_bundle.query_str})
        response = self._llm.generate(prompt=synonym_prompt, parse_mode='str')
        matches = self._parse_llm_output(response.content)
        logger.info(f'{self.__class__.__name__}, synonym words from llm: {matches}')
        return self._prepare_matches(matches, limit=limit or self._limit)

    async def aretrieve_from_graph(self, query_bundle: Query, limit: Optional[int]=None) -> List[NodeWithScore]:
        synonym_prompt = self._synonym_prompt.format_map({'max_keywords': self._limit, 'query_str': query_bundle.query_str})
        response = await self._llm.async_generate(prompt=synonym_prompt, parse_mode='str')
        matches = self._parse_llm_output(response.content)
        logger.info(f'{self.__class__.__name__}: query: {query_bundle.query_str} \nsynonym words from llm: {matches}')
        return await self._aprepare_matches(matches, limit=limit or self._limit)

def retrieve_from_graph(self, query_bundle: Query, limit: Optional[int]=None) -> List[NodeWithScore]:
    synonym_prompt = self._synonym_prompt.format_map({'max_keywords': self._max_keywords, 'query_str': query_bundle.query_str})
    response = self._llm.generate(prompt=synonym_prompt, parse_mode='str')
    matches = self._parse_llm_output(response.content)
    logger.info(f'{self.__class__.__name__}, synonym words from llm: {matches}')
    return self._prepare_matches(matches, limit=limit or self._limit)

class HyDETransform(BaseQueryTransform):
    """
    Hypothetical Document Embeddings (HyDE) query transform.

    This class implements the HyDE technique for improving dense retrieval, as described in
    `Precise Zero-Shot Dense Retrieval without Relevance Labels` (https://arxiv.org/abs/2212.10496).
    It uses a language model to generate a hypothetical document (answer) for a given query, which
    is then used to create embedding strings for enhanced retrieval.

    Attributes:
        _llm (BaseLLM): The language model used to generate hypothetical documents.
        _hyde_prompt (Union[str, Template]): The prompt template for generating hypothetical documents.
        _include_original (bool): Whether to include the original query's embedding strings in the output.
    """

    def __init__(self, llm: BaseLLM, hyde_prompt: Optional[Union[str, Template]]=None, include_original: bool=True) -> None:
        """
        Initialize the HyDETransform.

        Args:
            llm (BaseLLM): The language model for generating hypothetical documents.
            hyde_prompt (Optional[Union[str, Template]]): Custom prompt template for HyDE generation.
                Defaults to DEFAULT_HYDE_PROMPT if not provided.
            include_original (bool): Whether to include the original query's embedding strings
                alongside the hypothetical document. Defaults to True.
        """
        self._llm = llm
        self._hyde_prompt = hyde_prompt or DEFAULT_HYDE_PROMPT
        self._include_original = include_original

    def _run(self, query: Query, metadata: Dict) -> Query:
        """
        Transform a query by generating a hypothetical document and updating embedding strings.

        This method uses the LLM to generate a hypothetical answer to the query, which is then
        used as an embedding string for retrieval. If include_original is True, the original
        query's embedding strings are also retained.

        Args:
            query (Query): The input query to transform.
            metadata (Dict): Additional metadata associated with the query (not used in this implementation).

        Returns:
            Query: A new Query instance with updated embedding strings, including the hypothetical document.
        """
        query_str = query.query_str
        instruction = self._hyde_prompt.format_map({'query': query_str})
        hypothetical_doc = self._llm.generate(prompt=instruction, system_message=HYDE_SYSTEM_IMPLE_).content
        embedding_strs = [hypothetical_doc]
        if self._include_original:
            embedding_strs.extend(query.embedding_strs)
        tmp_query = query.deepcopy()
        tmp_query.custom_embedding_strs = embedding_strs
        return tmp_query

def _run(self, query: Query, metadata: Dict) -> Query:
    """
        Transform a query by generating a hypothetical document and updating embedding strings.

        This method uses the LLM to generate a hypothetical answer to the query, which is then
        used as an embedding string for retrieval. If include_original is True, the original
        query's embedding strings are also retained.

        Args:
            query (Query): The input query to transform.
            metadata (Dict): Additional metadata associated with the query (not used in this implementation).

        Returns:
            Query: A new Query instance with updated embedding strings, including the hypothetical document.
        """
    query_str = query.query_str
    instruction = self._hyde_prompt.format_map({'query': query_str})
    hypothetical_doc = self._llm.generate(prompt=instruction, system_message=HYDE_SYSTEM_IMPLE_).content
    embedding_strs = [hypothetical_doc]
    if self._include_original:
        embedding_strs.extend(query.embedding_strs)
    tmp_query = query.deepcopy()
    tmp_query.custom_embedding_strs = embedding_strs
    return tmp_query

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

def _check_evaluation_inputs(self, prediction: Any, label: Any) -> bool:
    """
        Check if the inputs are valid for evaluation.
        """
    assert isinstance(prediction, str) or isinstance(prediction, list), 'prediction must be a string or a list of strings, but got {}'.format(type(prediction))
    assert isinstance(label, dict) or isinstance(label, list), 'label must be a string or a list of strings, but got {}'.format(type(label))
    prediction = [prediction] if isinstance(prediction, str) else prediction
    label = [label] if isinstance(label, dict) else label
    return (prediction, label)

def get_type_name(typ):
    origin = get_origin(typ)
    if origin is None:
        return getattr(typ, '__name__', str(typ))
    if origin is Union:
        args = get_args(typ)
        return ' | '.join((get_type_name(arg) for arg in args))
    if origin is type:
        return f'Type[{get_type_name(args[0])}]' if args else 'Type[Any]'
    if origin in (list, tuple):
        args = get_args(typ)
        return f'{origin.__name__}[{', '.join((get_type_name(arg) for arg in args))}]'
    if origin is dict:
        key_type, value_type = get_args(typ)
        return f'dict[{get_type_name(key_type)}, {get_type_name(value_type)}]'
    return str(origin)

def get_pydantic_field_types(model: Type[BaseModel]) -> Dict[str, Union[str, dict]]:
    field_types = {}
    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation
        if hasattr(field_type, 'model_fields'):
            field_types[field_name] = get_pydantic_field_types(field_type)
        else:
            type_name = get_type_name(field_type)
            field_types[field_name] = type_name
    return field_types

def get_pydantic_required_field_types(model: Type[BaseModel]) -> Dict[str, str]:
    required_field_types = {}
    for field_name, field_info in model.model_fields.items():
        if not field_info.is_required():
            continue
        if field_info.default is not PydanticUndefined or field_info.default_factory is not None:
            continue
        field_type = field_info.annotation
        type_name = get_type_name(field_type)
        required_field_types[field_name] = type_name
    return required_field_types

def format_pydantic_field_types(field_types: Dict[str, str]) -> str:
    output = ', '.join((f'"{field_name}": {field_type}' for field_name, field_type in field_types.items()))
    output = '{' + output + '}'
    return output

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

def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
    """
        Convert the Message to a dictionary for saving. 
        """
    data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
    if self.msg_type:
        data['msg_type'] = self.msg_type.value
    return data

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

def compute_total_cost(self):
    total_tokens, total_cost = (0, 0.0)
    for _, value in self.total_tokens.items():
        total_tokens += value
    for _, value in self.total_cost.items():
        total_cost += value
    return (total_tokens, total_cost)

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

def update_completion_params(self, params1: dict, params2: dict) -> dict:
    config_params: list = self.config.get_config_params()
    for key, value in params2.items():
        if key in self._default_ignore_fields:
            continue
        if key not in config_params:
            continue
        params1[key] = value
    return params1

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

def update_completion_params(self, params1: dict, params2: dict) -> dict:
    config_params: list = self.config.get_config_params()
    for key, value in params2.items():
        if key in self._default_ignore_fields:
            continue
        if key not in config_params:
            continue
        params1[key] = value
    return params1

class LLMOutputParser(Parser):
    """A basic parser for LLM-generated content.
    
    This parser stores the raw text generated by an LLM in the `.content` attribute
    and provides methods to extract structured data from this text using different
    parsing strategies.
    
    Attributes:
        content: The raw text generated by the LLM.
    """
    content: str = Field(default=None, exclude=True, description='the text generated by LLM')

    @classmethod
    def get_attrs(cls, return_type: bool=False) -> List[Union[str, tuple]]:
        """Returns the attributes of the LLMOutputParser class.
        
        Excludes ["class_name", "content"] by default.

        Args:
            return_type: Whether to return the type of the attributes along with their names.
        
        Returns:
            If `return_type` is True, returns a list of tuples where each tuple contains 
            the attribute name and its type. Otherwise, returns a list of attribute names.
        """
        attrs = []
        exclude_attrs = ['class_name', 'content']
        for field, field_info in cls.model_fields.items():
            if field not in exclude_attrs:
                if return_type:
                    field_type = get_type_name(field_info.annotation)
                    attrs.append((field, field_type))
                else:
                    attrs.append(field)
        return attrs

    @classmethod
    def get_attr_descriptions(cls) -> dict:
        """Returns the attributes and their descriptions.
        
        Returns:
            A dictionary mapping attribute names to their descriptions.
        """
        attrs = cls.get_attrs()
        results = {}
        for field_name, field_info in cls.model_fields.items():
            if field_name not in attrs:
                continue
            field_desc = field_info.description if field_info.description is not None else 'None'
            results[field_name] = field_desc
        return results

    @classmethod
    def get_content_data(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> dict:
        """Parses LLM-generated content into a dictionary.
        
        This method takes content from an LLM response and converts it to a structured
        dictionary based on the specified parsing mode.

        Args:
            content: The content to parse.
            parse_mode: The mode to parse the content. Must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. It will return a dictionary parsed from the first valid JSON string.
                - 'xml': Parses content using XML tags. It will return a dictionary parsed from the XML tags.
                - 'title': Parses content with Markdown-style headings.
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function.
            parse_func: The function to parse the content, only valid when parse_mode is 'custom'.
            **kwargs (Any): Additional arguments passed to the parsing function.
        
        Returns:
            The parsed content as a dictionary.
            
        Raises:
            ValueError: If parse_mode is invalid or if parse_func is not provided when parse_mode is 'custom'.
        """
        attrs = cls.get_attrs()
        if len(attrs) <= 0:
            return {}
        if parse_mode == 'str':
            parse_func = cls._parse_str_content
        elif parse_mode == 'json':
            parse_func = cls._parse_json_content
        elif parse_mode == 'xml':
            parse_func = cls._parse_xml_content
        elif parse_mode == 'title':
            parse_func = cls._parse_title_content
        elif parse_mode == 'custom':
            if parse_func is None:
                raise ValueError("`parse_func` must be provided when `parse_mode` is 'custom'.")
            signature = inspect.signature(parse_func)
            if 'content' not in signature.parameters:
                raise ValueError('`parse_func` must have an input argument `content`.')
            func_args = {}
            func_args['content'] = content
            for param_name, param in signature.parameters.items():
                if param_name == 'content':
                    continue
                if param_name in kwargs:
                    func_args[param_name] = kwargs[param_name]
            data = parse_func(**func_args)
            if not isinstance(data, dict):
                raise ValueError(f'The output of `parse_func` must be a dictionary, but found {type(data)}.')
            return data
        else:
            raise ValueError(f"Invalid value '{parse_mode}' detected for `parse_mode`. Available choices: {PARSER_VALID_MODE}")
        data = parse_func(content=content, **kwargs)
        return data

    @classmethod
    def _parse_str_content(cls, content: str, **kwargs) -> dict:
        """Parses content by setting all attributes to the raw content.
        
        Args:
            content: The content to parse.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping all attributes to the raw content.
        """
        attrs = cls.get_attrs()
        return {attr: content for attr in attrs}

    @classmethod
    def _parse_json_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting and parsing a JSON object. 
        If the content contains multiple JSON objects, only the first one will be used. 
        
        Args:
            content: The content containing a JSON object.
            **kwargs: Additional arguments (not used).
        
        Returns:
            The parsed JSON as a dictionary.
            
        Raises:
            ValueError: If the content doesn't contain a valid JSON object.
        """
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) > 0:
            json_str = extracted_json_list[0]
            try:
                data = yaml.safe_load(json_str)
                if not isinstance(data, dict):
                    if isinstance(data, list):
                        attrs = cls.get_attrs()
                        if len(attrs) == 1:
                            return {attrs[0]: data}
                        else:
                            raise ValueError('The generated content is a list of JSON strings, but the attribute name for the list is not specified. You should instruct the LLM to specify the attribute name for the list.')
                    else:
                        raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
            except Exception:
                raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
        else:
            raise ValueError(f'The following generated content does not contain JSON string!\n{content}')
        return data

    @classmethod
    def _parse_xml_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting values from XML tags.
        
        Each attribute of the parser is expected to be enclosed in XML tags
        with the attribute name as the tag name.
        
        Args:
            content: The content containing XML tags.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping attributes to their extracted values.
            
        Raises:
            ValueError: If the content is missing expected XML tags or if the
                        extracted values can't be converted to the expected types.
        """
        attrs_with_types: List[tuple] = cls.get_attrs(return_type=True)
        data = {}
        for attr, attr_type in attrs_with_types:
            attr_raw_value_list = parse_xml_from_text(text=content, label=attr)
            if len(attr_raw_value_list) > 0:
                attr_raw_value = attr_raw_value_list[0]
                try:
                    attr_value = parse_data_from_text(text=attr_raw_value, datatype=attr_type)
                except Exception:
                    raise ValueError(f'Cannot parse text: {attr_raw_value} into {attr_type} data!')
            else:
                raise ValueError(f'The following generated content does not contain xml label <{attr}>xxx</{attr}>!\n{content}')
            data[attr] = attr_value
        return data

    @classmethod
    def _parse_title_content(cls, content: str, title_format: str='## {title}', **kwargs) -> dict:
        """Parses content with markdown-style titles.
        
        Extracts sections from content that are divided by titles following
        the specified format described in `title_format`. The default format is "## {title}".
        For example:
        ```
        ## title1
        content1
        ## title2
        content2
        ```
        This content will be parsed into:
        ```
        {
            "title1": "content1",
            "title2": "content2"
        }
        ```
        Args:
            content: The content with title-divided sections.
            title_format: The format of the titles, default is "## {title}".
            **kwargs: Additional arguments (not used).

        Returns:
            A dictionary mapping title names to their section contents.
        """
        attrs: List[str] = cls.get_attrs()
        if not attrs:
            return {}
        output_titles = [title_format.format(title=attr) for attr in attrs]

        def is_output_title(text: str):
            for title in output_titles:
                if text.strip().lower().startswith(title.lower()):
                    return (True, title)
            return (False, None)
        data = {}
        current_output_name: str = None
        current_output_content: list = None
        for line in content.split('\n'):
            is_title, title = is_output_title(line)
            if is_title:
                if current_output_name is not None and current_output_content is not None:
                    data[current_output_name] = '\n'.join(current_output_content)
                current_output_content = []
                current_output_name = title.replace('#', '').strip()
                output_titles.remove(title)
            elif current_output_content is not None:
                current_output_content.append(line)
        if current_output_name is not None and current_output_content is not None:
            data[current_output_name] = '\n'.join(current_output_content)
        return data

    @classmethod
    def parse(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> 'LLMOutputParser':
        """Parses LLM-generated text into a structured parser instance.
        
        This is the main method for creating parser instances from LLM output.
        
        Args:
            content: The text generated by the LLM.
            parse_mode: The mode to parse the content, must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. Uses the first valid JSON string to create an instance of LLMOutputParser.
                - 'xml': Parses content using XML tags. Uses the XML tags to create an instance of LLMOutputParser.
                - 'title': Parses content with Markdown-style headings. Uses the Markdown-style headings to create an instance of LLMOutputParser. The default title format is "## {title}", you can change it by providing `title_format` parameter, which should be a string that contains `{title}` placeholder. 
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function. The `parse_func` must have a parameter named `content` and return a dictionary where the keys are the attribute names and the values are the parsed data. 
            parse_func: The function to parse the content, only valid when `parse_mode` is 'custom'.
            **kwargs (Any): Additional arguments passed to parsing functions, such as:
                - `title_format` for `parse_mode="title"`.
            
        Returns:
            An instance of LLMOutputParser containing the parsed data.
            
        Raises:
            ValueError: If parse_mode is invalid or if content is not a string.
        """
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
        if not isinstance(content, str):
            raise ValueError(f'The input to {cls.__name__}.parse should be a str, but found {type(content)}.')
        data = cls.get_content_data(content=content, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
        data.update({'content': content})
        parser = cls.from_dict(data, **kwargs)
        return parser

    def __str__(self) -> str:
        """
        Returns a string representation of the parser.
        """
        return self.to_str()

    def to_str(self, **kwargs) -> str:
        """
        Converts the parser to a string.
        """
        return self.content

    def get_structured_data(self) -> dict:
        """Extracts structured data from the parser.
        
        Returns:
            A dictionary containing only the defined attributes and their values,
            excluding metadata like class_name.
        """
        attrs = type(self).get_attrs()
        data = self.to_dict(ignore=['class_name'])
        structured_data = {key: value for key, value in data.items() if key in attrs}
        return structured_data

@classmethod
def get_attrs(cls, return_type: bool=False) -> List[Union[str, tuple]]:
    """Returns the attributes of the LLMOutputParser class.
        
        Excludes ["class_name", "content"] by default.

        Args:
            return_type: Whether to return the type of the attributes along with their names.
        
        Returns:
            If `return_type` is True, returns a list of tuples where each tuple contains 
            the attribute name and its type. Otherwise, returns a list of attribute names.
        """
    attrs = []
    exclude_attrs = ['class_name', 'content']
    for field, field_info in cls.model_fields.items():
        if field not in exclude_attrs:
            if return_type:
                field_type = get_type_name(field_info.annotation)
                attrs.append((field, field_type))
            else:
                attrs.append(field)
    return attrs

@classmethod
def get_attr_descriptions(cls) -> dict:
    """Returns the attributes and their descriptions.
        
        Returns:
            A dictionary mapping attribute names to their descriptions.
        """
    attrs = cls.get_attrs()
    results = {}
    for field_name, field_info in cls.model_fields.items():
        if field_name not in attrs:
            continue
        field_desc = field_info.description if field_info.description is not None else 'None'
        results[field_name] = field_desc
    return results

@classmethod
def get_content_data(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> dict:
    """Parses LLM-generated content into a dictionary.
        
        This method takes content from an LLM response and converts it to a structured
        dictionary based on the specified parsing mode.

        Args:
            content: The content to parse.
            parse_mode: The mode to parse the content. Must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. It will return a dictionary parsed from the first valid JSON string.
                - 'xml': Parses content using XML tags. It will return a dictionary parsed from the XML tags.
                - 'title': Parses content with Markdown-style headings.
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function.
            parse_func: The function to parse the content, only valid when parse_mode is 'custom'.
            **kwargs (Any): Additional arguments passed to the parsing function.
        
        Returns:
            The parsed content as a dictionary.
            
        Raises:
            ValueError: If parse_mode is invalid or if parse_func is not provided when parse_mode is 'custom'.
        """
    attrs = cls.get_attrs()
    if len(attrs) <= 0:
        return {}
    if parse_mode == 'str':
        parse_func = cls._parse_str_content
    elif parse_mode == 'json':
        parse_func = cls._parse_json_content
    elif parse_mode == 'xml':
        parse_func = cls._parse_xml_content
    elif parse_mode == 'title':
        parse_func = cls._parse_title_content
    elif parse_mode == 'custom':
        if parse_func is None:
            raise ValueError("`parse_func` must be provided when `parse_mode` is 'custom'.")
        signature = inspect.signature(parse_func)
        if 'content' not in signature.parameters:
            raise ValueError('`parse_func` must have an input argument `content`.')
        func_args = {}
        func_args['content'] = content
        for param_name, param in signature.parameters.items():
            if param_name == 'content':
                continue
            if param_name in kwargs:
                func_args[param_name] = kwargs[param_name]
        data = parse_func(**func_args)
        if not isinstance(data, dict):
            raise ValueError(f'The output of `parse_func` must be a dictionary, but found {type(data)}.')
        return data
    else:
        raise ValueError(f"Invalid value '{parse_mode}' detected for `parse_mode`. Available choices: {PARSER_VALID_MODE}")
    data = parse_func(content=content, **kwargs)
    return data

@classmethod
def _parse_str_content(cls, content: str, **kwargs) -> dict:
    """Parses content by setting all attributes to the raw content.
        
        Args:
            content: The content to parse.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping all attributes to the raw content.
        """
    attrs = cls.get_attrs()
    return {attr: content for attr in attrs}

def get_structured_data(self) -> dict:
    """Extracts structured data from the parser.
        
        Returns:
            A dictionary containing only the defined attributes and their values,
            excluding metadata like class_name.
        """
    attrs = type(self).get_attrs()
    data = self.to_dict(ignore=['class_name'])
    structured_data = {key: value for key, value in data.items() if key in attrs}
    return structured_data

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

class AgentGeneration(Action):
    """
    Action for generating agent specifications for workflow tasks.
    
    This action analyzes task requirements and generates appropriate agent
    specifications, including their prompts, inputs, and outputs. It can either
    select from existing agents or create new ones tailored to the task.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else AGENT_GENERATION_ACTION['name']
        description = kwargs.pop('description') if 'description' in kwargs else AGENT_GENERATION_ACTION['description']
        prompt = kwargs.pop('prompt') if 'prompt' in kwargs else AGENT_GENERATION_ACTION['prompt']
        inputs_format = kwargs.pop('inputs_format', None) or AgentGenerationInput
        outputs_format = kwargs.pop('outputs_format', None) or AgentGenerationOutput
        tools = kwargs.pop('tools', None)
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)
        self.tools = tools

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> AgentGenerationOutput:
        """Execute the agent generation process.
        
        This method uses the provided language model to generate agent specifications
        based on the workflow context and task requirements.
        
        Args:
            llm: The language model to use for generation.
            inputs: Input data containing workflow and task information.
            sys_msg: Optional system message for the language model.
            return_prompt: Whether to return both the generated agents and the prompt used.
            **kwargs: Additional keyword arguments.
            
        Returns:
            If return_prompt is False (default): The generated agents output.
            If return_prompt is True: A tuple of (generated agents, prompt used).
            
        Raises:
            ValueError: If the inputs are None or empty.
        """
        if not inputs:
            logger.error('AgentGeneration action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to AgentGeneration action is None or empty.')
        inputs_format: AgentGenerationInput = self.inputs_format
        outputs_format: AgentGenerationOutput = self.outputs_format
        prompt_params_names = inputs_format.get_attrs()
        prompt_params_values = {param: inputs.get(param, '') for param in prompt_params_names}
        if self.tools:
            tool_description = [{tool.name: [s['function']['description'] for s in tool.get_tool_schemas()]} for tool in self.tools]
            prompt_params_values['tools'] = AGENT_GENERATION_TOOLS_PROMPT.format(tools_description=tool_description)
        prompt = self.prompt.format(**prompt_params_values)
        agents = llm.generate(prompt=prompt, system_message=sys_msg, parser=outputs_format, parse_mode='json')
        if return_prompt:
            return (agents, prompt)
        return agents

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> AgentGenerationOutput:
    """Execute the agent generation process.
        
        This method uses the provided language model to generate agent specifications
        based on the workflow context and task requirements.
        
        Args:
            llm: The language model to use for generation.
            inputs: Input data containing workflow and task information.
            sys_msg: Optional system message for the language model.
            return_prompt: Whether to return both the generated agents and the prompt used.
            **kwargs: Additional keyword arguments.
            
        Returns:
            If return_prompt is False (default): The generated agents output.
            If return_prompt is True: A tuple of (generated agents, prompt used).
            
        Raises:
            ValueError: If the inputs are None or empty.
        """
    if not inputs:
        logger.error('AgentGeneration action received invalid `inputs`: None or empty.')
        raise ValueError('The `inputs` to AgentGeneration action is None or empty.')
    inputs_format: AgentGenerationInput = self.inputs_format
    outputs_format: AgentGenerationOutput = self.outputs_format
    prompt_params_names = inputs_format.get_attrs()
    prompt_params_values = {param: inputs.get(param, '') for param in prompt_params_names}
    if self.tools:
        tool_description = [{tool.name: [s['function']['description'] for s in tool.get_tool_schemas()]} for tool in self.tools]
        prompt_params_values['tools'] = AGENT_GENERATION_TOOLS_PROMPT.format(tools_description=tool_description)
    prompt = self.prompt.format(**prompt_params_values)
    agents = llm.generate(prompt=prompt, system_message=sys_msg, parser=outputs_format, parse_mode='json')
    if return_prompt:
        return (agents, prompt)
    return agents

class CodeExtraction(Action):
    """
    An action that extracts and organizes code blocks from text.
    
    This action uses an LLM to analyze text containing code blocks, extract them,
    suggest appropriate filenames, and save them to a specified directory. It can
    also identify which file is likely the main entry point based on heuristics.
    
    Attributes:
        name: The name of the action.
        description: A description of what the action does.
        prompt: The prompt template used by the action.
        inputs_format: The expected format of inputs to this action.
        outputs_format: The format of the action's output.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else CODE_EXTRACTION['name']
        description = kwargs.pop('description') if 'description' in kwargs else CODE_EXTRACTION['description']
        prompt = kwargs.pop('prompt') if 'prompt' in kwargs else CODE_EXTRACTION['prompt']
        inputs_format = kwargs.pop('inputs_format', None) or CodeExtractionInput
        outputs_format = kwargs.pop('outputs_format', None) or CodeExtractionOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def identify_main_file(self, saved_files: Dict[str, str]) -> Optional[str]:
        """Identify the main file from the saved files based on content and file type.
        
        This method uses a combination of common filename conventions and content
        analysis to determine which file is likely the main entry point of a project.
        
        Args:
            saved_files: Dictionary mapping filenames to their full paths
            
        Returns:
            Path to the main file if found, None otherwise
            
        """
        main_file_priorities = ['index.html', 'main.py', 'app.py', 'index.js', 'main.js', 'app.js', 'Main.java', 'main.cpp', 'main.c', 'main.go', 'index.php', 'Program.cs']
        for main_file in main_file_priorities:
            if main_file in saved_files:
                return saved_files[main_file]
        html_files = {k: v for k, v in saved_files.items() if k.endswith('.html')}
        if html_files:
            return next(iter(html_files.values()))
        py_files = {k: v for k, v in saved_files.items() if k.endswith('.py')}
        if py_files:
            for filename, path in py_files.items():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "if __name__ == '__main__'" in content or 'if __name__ == "__main__"' in content:
                        return path
            if py_files:
                return next(iter(py_files.values()))
        java_files = {k: v for k, v in saved_files.items() if k.endswith('.java')}
        if java_files:
            for filename, path in java_files.items():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'public static void main' in content:
                        return path
            if java_files:
                return next(iter(java_files.values()))
        js_files = {k: v for k, v in saved_files.items() if k.endswith('.js')}
        if js_files:
            return next(iter(js_files.values()))
        if saved_files:
            return next(iter(saved_files.values()))
        return None

    def save_code_blocks(self, code_blocks: List[Dict], target_directory: str) -> Dict[str, str]:
        """Save code blocks to files in the target directory.
        
        Creates the target directory if it doesn't exist and saves each code block
        to a file with an appropriate name, handling filename conflicts.
        
        Args:
            code_blocks: List of dictionaries containing code block information
            target_directory: Directory path where files should be saved
            
        Returns:
            Dictionary mapping filenames to their full paths
        """
        os.makedirs(target_directory, exist_ok=True)
        saved_files = {}
        for block in code_blocks:
            filename = block.get('filename', 'unknown.txt')
            content = block.get('content', '')
            if not content.strip():
                continue
            base_filename = filename
            counter = 1
            while filename in saved_files:
                name_parts = base_filename.split('.')
                if len(name_parts) > 1:
                    filename = f'{'.'.join(name_parts[:-1])}_{counter}.{name_parts[-1]}'
                else:
                    filename = f'{base_filename}_{counter}'
                counter += 1
            file_path = os.path.join(target_directory, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files[filename] = file_path
        return saved_files

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> CodeExtractionOutput:
        """Execute the CodeExtraction action.
        
        Extracts code blocks from the provided text using the specified LLM,
        saves them to the target directory, and identifies the main file.
        
        Args:
            llm: The LLM to use for code extraction
            inputs: Dictionary containing:
                - code_string: The string with code blocks to extract
                - target_directory: Where to save the files
                - project_name: Optional project folder name
            sys_msg: Optional system message override for the LLM
            return_prompt: Whether to return the prompt along with the result
            **kwargs (Any): Additional keyword arguments
            
        Returns:
            CodeExtractionOutput with extracted file information
        """
        if not llm:
            error_msg = 'CodeExtraction action requires an LLM.'
            return CodeExtractionOutput(extracted_files={}, error=error_msg)
        if not inputs:
            error_msg = 'CodeExtraction action received invalid `inputs`: None or empty.'
            return CodeExtractionOutput(extracted_files={}, error=error_msg)
        code_string = inputs.get('code_string', '')
        target_directory = inputs.get('target_directory', '')
        project_name = inputs.get('project_name', None)
        if not code_string:
            error_msg = 'No code string provided.'
            return CodeExtractionOutput(extracted_files={}, error=error_msg)
        if not target_directory:
            error_msg = 'No target directory provided.'
            return CodeExtractionOutput(extracted_files={}, error=error_msg)
        if project_name:
            project_dir = os.path.join(target_directory, project_name)
        else:
            project_dir = target_directory
        try:
            prompt_params = {'code_string': code_string}
            system_message = CODE_EXTRACTION['system_prompt'] if sys_msg is None else sys_msg
            llm_response: CodeBlockList = llm.generate(prompt=self.prompt.format(**prompt_params), system_message=system_message, parser=CodeBlockList, parse_mode='json')
            code_blocks = llm_response.get_structured_data().get('code_blocks', [])
            saved_files = self.save_code_blocks(code_blocks, project_dir)
            main_file = self.identify_main_file(saved_files)
            result = CodeExtractionOutput(extracted_files=saved_files, main_file=main_file)
            if return_prompt:
                return (result, self.prompt.format(**prompt_params))
            return result
        except Exception as e:
            error_msg = f'Error extracting code: {str(e)}'
            return CodeExtractionOutput(extracted_files={}, error=error_msg)

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> CodeExtractionOutput:
    """Execute the CodeExtraction action.
        
        Extracts code blocks from the provided text using the specified LLM,
        saves them to the target directory, and identifies the main file.
        
        Args:
            llm: The LLM to use for code extraction
            inputs: Dictionary containing:
                - code_string: The string with code blocks to extract
                - target_directory: Where to save the files
                - project_name: Optional project folder name
            sys_msg: Optional system message override for the LLM
            return_prompt: Whether to return the prompt along with the result
            **kwargs (Any): Additional keyword arguments
            
        Returns:
            CodeExtractionOutput with extracted file information
        """
    if not llm:
        error_msg = 'CodeExtraction action requires an LLM.'
        return CodeExtractionOutput(extracted_files={}, error=error_msg)
    if not inputs:
        error_msg = 'CodeExtraction action received invalid `inputs`: None or empty.'
        return CodeExtractionOutput(extracted_files={}, error=error_msg)
    code_string = inputs.get('code_string', '')
    target_directory = inputs.get('target_directory', '')
    project_name = inputs.get('project_name', None)
    if not code_string:
        error_msg = 'No code string provided.'
        return CodeExtractionOutput(extracted_files={}, error=error_msg)
    if not target_directory:
        error_msg = 'No target directory provided.'
        return CodeExtractionOutput(extracted_files={}, error=error_msg)
    if project_name:
        project_dir = os.path.join(target_directory, project_name)
    else:
        project_dir = target_directory
    try:
        prompt_params = {'code_string': code_string}
        system_message = CODE_EXTRACTION['system_prompt'] if sys_msg is None else sys_msg
        llm_response: CodeBlockList = llm.generate(prompt=self.prompt.format(**prompt_params), system_message=system_message, parser=CodeBlockList, parse_mode='json')
        code_blocks = llm_response.get_structured_data().get('code_blocks', [])
        saved_files = self.save_code_blocks(code_blocks, project_dir)
        main_file = self.identify_main_file(saved_files)
        result = CodeExtractionOutput(extracted_files=saved_files, main_file=main_file)
        if return_prompt:
            return (result, self.prompt.format(**prompt_params))
        return result
    except Exception as e:
        error_msg = f'Error extracting code: {str(e)}'
        return CodeExtractionOutput(extracted_files={}, error=error_msg)

class ActionInput(LLMOutputParser):
    """Input specification and parsing for actions.
    
    This class defines the input requirements for actions and provides methods
    to generate structured input specifications. It inherits from LLMOutputParser 
    to allow parsing of LLM outputs into structured inputs for actions.
    
    Notes:
        Parameters in ActionInput should be defined in Pydantic Field format.
        For optional variables, use format: 
        var: Optional[int] = Field(default=None, description="xxx")
        Remember to add `default=None` for optional parameters.
    """

    @classmethod
    def get_input_specification(cls, ignore_fields: List[str]=[]) -> str:
        """Generate a JSON specification of the input requirements.
        
        Examines the class fields and produces a structured specification of
        the input parameters, including their types, descriptions, and whether
        they are required.
        
        Args:
            ignore_fields (List[str]): List of field names to exclude from the specification.
            
        Returns:
            A JSON string containing the input specification, or an empty string
            if no fields are defined or all are ignored.
        """
        fields_info = {}
        attrs = cls.get_attrs()
        for field_name, field_info in cls.model_fields.items():
            if field_name in ignore_fields:
                continue
            if field_name not in attrs:
                continue
            field_type = get_type_name(field_info.annotation)
            field_desc = field_info.description if field_info.description is not None else None
            field_default = str(field_info.default) if field_info.default is not PydanticUndefined else None
            field_required = True if field_default is None else False
            description = field_type + ', '
            if field_desc is not None:
                description += field_desc.strip() + ', '
            description += 'required' if field_required else 'optional'
            if field_default is not None:
                description += ', Default value: ' + field_default
            fields_info[field_name] = description
        if len(fields_info) == 0:
            return ''
        fields_info_str = json.dumps(fields_info, indent=4)
        return fields_info_str

    @classmethod
    def get_required_input_names(cls) -> List[str]:
        """Get a list of all required input parameter names.
        
        Returns:
            List[str]: Names of all parameters that are required (don't have default values).
        """
        required_fields = []
        attrs = cls.get_attrs()
        for field_name, field_info in cls.model_fields.items():
            if field_name not in attrs:
                continue
            field_default = field_info.default
            if field_default is PydanticUndefined:
                required_fields.append(field_name)
        return required_fields

@classmethod
def get_input_specification(cls, ignore_fields: List[str]=[]) -> str:
    """Generate a JSON specification of the input requirements.
        
        Examines the class fields and produces a structured specification of
        the input parameters, including their types, descriptions, and whether
        they are required.
        
        Args:
            ignore_fields (List[str]): List of field names to exclude from the specification.
            
        Returns:
            A JSON string containing the input specification, or an empty string
            if no fields are defined or all are ignored.
        """
    fields_info = {}
    attrs = cls.get_attrs()
    for field_name, field_info in cls.model_fields.items():
        if field_name in ignore_fields:
            continue
        if field_name not in attrs:
            continue
        field_type = get_type_name(field_info.annotation)
        field_desc = field_info.description if field_info.description is not None else None
        field_default = str(field_info.default) if field_info.default is not PydanticUndefined else None
        field_required = True if field_default is None else False
        description = field_type + ', '
        if field_desc is not None:
            description += field_desc.strip() + ', '
        description += 'required' if field_required else 'optional'
        if field_default is not None:
            description += ', Default value: ' + field_default
        fields_info[field_name] = description
    if len(fields_info) == 0:
        return ''
    fields_info_str = json.dumps(fields_info, indent=4)
    return fields_info_str

@classmethod
def get_required_input_names(cls) -> List[str]:
    """Get a list of all required input parameter names.
        
        Returns:
            List[str]: Names of all parameters that are required (don't have default values).
        """
    required_fields = []
    attrs = cls.get_attrs()
    for field_name, field_info in cls.model_fields.items():
        if field_name not in attrs:
            continue
        field_default = field_info.default
        if field_default is PydanticUndefined:
            required_fields.append(field_name)
    return required_fields

class ActionOutput(LLMOutputParser):
    """Output representation for actions.
    
    This class handles the structured output of actions, providing methods
    to convert the output to structured data. It inherits from LLMOutputParser
    to support parsing of LLM outputs into structured action results.
    """

    def to_str(self) -> str:
        """Convert the output to a formatted JSON string.
        
        Returns:
            A pretty-printed JSON string representation of the structured data.
        """
        return json.dumps(self.get_structured_data(), indent=4)

def to_str(self) -> str:
    """Convert the output to a formatted JSON string.
        
        Returns:
            A pretty-printed JSON string representation of the structured data.
        """
    return json.dumps(self.get_structured_data(), indent=4)

class Action(BaseModule):
    """Base class for all actions in the EvoAgentX framework.
    
    Actions represent discrete operations that can be performed by agents.
    They define inputs, outputs, and execution behavior, and can optionally
    use tools to accomplish their tasks.
    
    Attributes:
        name (str): Unique identifier for the action.
        description (str): Human-readable description of what the action does.
        prompt (Optional[str]): Optional prompt template for this action.
        tools (Optional[List[Toolkit]]): Optional list of tools that can be used by this action.
        inputs_format (Optional[Type[ActionInput]]): Optional class defining the expected input structure.
        outputs_format (Optional[Type[Parser]]): Optional class defining the expected output structure.
    """
    name: str
    description: str
    prompt: Optional[str] = None
    prompt_template: Optional[PromptTemplate] = None
    tools: Optional[List[Toolkit]] = None
    inputs_format: Optional[Type[ActionInput]] = None
    outputs_format: Optional[Type[Parser]] = None

    def init_module(self):
        """Initialize the action module.
        
        This method is called after the action is instantiated.
        Subclasses can override this to perform custom initialization.
        """
        pass

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        """
        Convert the action to a dictionary for saving.  
        """
        data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
        if self.inputs_format:
            data['inputs_format'] = self.inputs_format.__name__
        if self.outputs_format:
            data['outputs_format'] = self.outputs_format.__name__
        return data

    @model_validator(mode='before')
    @classmethod
    def validate_data(cls, data: Any) -> Any:
        if 'inputs_format' in data and data['inputs_format'] and isinstance(data['inputs_format'], str):
            data['inputs_format'] = MODULE_REGISTRY.get_module(data['inputs_format'])
        if 'outputs_format' in data and data['outputs_format'] and isinstance(data['outputs_format'], str):
            data['outputs_format'] = MODULE_REGISTRY.get_module(data['outputs_format'])
        return data

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> Optional[Union[Parser, Tuple[Parser, str]]]:
        """Execute the action to produce a result.
        
        This is the main entry point for executing an action. Subclasses must
        implement this method to define the action's behavior.

        Args:
            llm (Optional[BaseLLM]): The LLM used to execute the action.
            inputs (Optional[dict]): Input data for the action execution. The input data should be a dictionary that matches the input format of the provided prompt. 
                For example, if the prompt contains a variable `{input_var}`, the `inputs` dictionary should have a key `input_var`, otherwise the variable will be set to empty string. 
            sys_msg (Optional[str]): Optional system message for the LLM.
            return_prompt (bool): Whether to return the complete prompt passed to the LLM.
            **kwargs (Any): Additional keyword arguments for the execution.
        
        Returns:
            If `return_prompt` is False, the method returns a Parser object containing the structured result of the action.
            If `return_prompt` is True, the method returns a tuple containing the Parser object and the complete prompt passed to the LLM.
        """
        raise NotImplementedError(f'`execute` function of {type(self).__name__} is not implemented!')

    async def async_execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> Optional[Union[Parser, Tuple[Parser, str]]]:
        """
        Asynchronous execution of the action.
        
        This method is the asynchronous counterpart of the `execute` method.
        It allows the action to be executed asynchronously using an LLM.
        """
        raise NotImplementedError(f'`async_execute` function of {type(self).__name__} is not implemented!')

def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
    """
        Convert the action to a dictionary for saving.  
        """
    data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
    if self.inputs_format:
        data['inputs_format'] = self.inputs_format.__name__
    if self.outputs_format:
        data['outputs_format'] = self.outputs_format.__name__
    return data

class ContextExtraction(Action):
    """Action for extracting structured inputs from context.
    
    This action analyzes a conversation context to extract relevant information
    that can be used as inputs for other actions. It uses the LLM to interpret
    unstructured contextual information and format it according to the target
    action's input requirements.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else CONTEXT_EXTRACTION['name']
        description = kwargs.pop('description') if 'description' in kwargs else CONTEXT_EXTRACTION['description']
        super().__init__(name=name, description=description, **kwargs)

    def get_context_from_messages(self, messages: List[Message]) -> str:
        str_context = '\n\n'.join([str(msg) for msg in messages])
        return str_context

    def execute(self, llm: Optional[BaseLLM]=None, action: Action=None, context: List[Message]=None, **kwargs) -> Union[dict, None]:
        """Extract structured inputs for an action from conversation context.
        
        This method uses the LLM to analyze the conversation context and extract
        information that matches the input requirements of the target action.
        
        Args:
            llm: The language model to use for extraction.
            action: The target action whose input requirements (`inputs_format`) define what to extract.
            context: List of messages providing the conversation context.
            **kwargs: Additional keyword arguments.
            
        Returns:
            A dictionary containing the extracted inputs for the target action,
            or None if extraction is not possible (e.g., if the action doesn't
            require inputs or if context is missing).
        """
        if action is None or context is None:
            return None
        action_inputs_cls: Type[ActionInput] = action.inputs_format
        if action_inputs_cls is None:
            return None
        action_inputs_desc = action_inputs_cls.get_input_specification()
        str_context = self.get_context_from_messages(messages=context)
        if not action_inputs_desc or not str_context:
            return None
        prompt = CONTEXT_EXTRACTION['prompt'].format(context=str_context, action_name=action.name, action_description=action.description, action_inputs=action_inputs_desc)
        action_inputs = llm.generate(prompt=prompt, system_message=CONTEXT_EXTRACTION['system_prompt'], parser=action_inputs_cls)
        action_inputs_data = action_inputs.get_structured_data()
        return action_inputs_data

def execute(self, llm: Optional[BaseLLM]=None, action: Action=None, context: List[Message]=None, **kwargs) -> Union[dict, None]:
    """Extract structured inputs for an action from conversation context.
        
        This method uses the LLM to analyze the conversation context and extract
        information that matches the input requirements of the target action.
        
        Args:
            llm: The language model to use for extraction.
            action: The target action whose input requirements (`inputs_format`) define what to extract.
            context: List of messages providing the conversation context.
            **kwargs: Additional keyword arguments.
            
        Returns:
            A dictionary containing the extracted inputs for the target action,
            or None if extraction is not possible (e.g., if the action doesn't
            require inputs or if context is missing).
        """
    if action is None or context is None:
        return None
    action_inputs_cls: Type[ActionInput] = action.inputs_format
    if action_inputs_cls is None:
        return None
    action_inputs_desc = action_inputs_cls.get_input_specification()
    str_context = self.get_context_from_messages(messages=context)
    if not action_inputs_desc or not str_context:
        return None
    prompt = CONTEXT_EXTRACTION['prompt'].format(context=str_context, action_name=action.name, action_description=action.description, action_inputs=action_inputs_desc)
    action_inputs = llm.generate(prompt=prompt, system_message=CONTEXT_EXTRACTION['system_prompt'], parser=action_inputs_cls)
    action_inputs_data = action_inputs.get_structured_data()
    return action_inputs_data

class CodeVerification(Action):

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else CODE_VERIFICATION_ACTION['name']
        description = kwargs.pop('description') if 'description' in kwargs else CODE_VERIFICATION_ACTION['description']
        prompt = kwargs.pop('prompt') if 'prompt' in kwargs else CODE_VERIFICATION_ACTION['prompt']
        inputs_format = kwargs.pop('inputs_format', None) or CodeVerificationInput
        outputs_format = kwargs.pop('outputs_format', None) or CodeVerificationOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> CodeVerificationOutput:
        if not inputs:
            logger.error('CodeVerification action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to CodeVerification action is None or empty.')
        prompt_params_names = ['code', 'requirements']
        prompt_params_values = {param: inputs.get(param, 'Not Provided') for param in prompt_params_names}
        prompt = self.prompt.format(**prompt_params_values)
        response = llm.generate(prompt=prompt, system_message=sys_msg)
        try:
            verification_result = self.outputs_format.parse(response.content, parse_mode='title')
        except Exception:
            try:
                code_blocks = extract_code_blocks(response.content, return_type=True)
                code = '\n\n'.join([f'```{code_type}\n{code}\n```' for code_type, code in code_blocks])
                verification_result = self.outputs_format(verified_code=code)
            except Exception:
                raise ValueError(f'Failed to extract code blocks from the response: {response.content}')
        if return_prompt:
            return (verification_result, prompt)
        return verification_result

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> CodeVerificationOutput:
    if not inputs:
        logger.error('CodeVerification action received invalid `inputs`: None or empty.')
        raise ValueError('The `inputs` to CodeVerification action is None or empty.')
    prompt_params_names = ['code', 'requirements']
    prompt_params_values = {param: inputs.get(param, 'Not Provided') for param in prompt_params_names}
    prompt = self.prompt.format(**prompt_params_values)
    response = llm.generate(prompt=prompt, system_message=sys_msg)
    try:
        verification_result = self.outputs_format.parse(response.content, parse_mode='title')
    except Exception:
        try:
            code_blocks = extract_code_blocks(response.content, return_type=True)
            code = '\n\n'.join([f'```{code_type}\n{code}\n```' for code_type, code in code_blocks])
            verification_result = self.outputs_format(verified_code=code)
        except Exception:
            raise ValueError(f'Failed to extract code blocks from the response: {response.content}')
    if return_prompt:
        return (verification_result, prompt)
    return verification_result

class TaskPlanning(Action):
    """
    Action for planning a series of tasks to achieve a goal.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else TASK_PLANNING_ACTION['name']
        description = kwargs.pop('description') if 'description' in kwargs else TASK_PLANNING_ACTION['description']
        prompt = kwargs.pop('prompt') if 'prompt' in kwargs else TASK_PLANNING_ACTION['prompt']
        inputs_format = kwargs.pop('inputs_format', None) or TaskPlanningInput
        outputs_format = kwargs.pop('outputs_format', None) or TaskPlanningOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> TaskPlanningOutput:
        """Execute the task planning process.
        
        This method uses the provided language model to generate a structured
        plan of sub-tasks based on the user's goal and any additional context.
        
        Args:
            llm: The language model to use for planning.
            inputs: Input data containing the goal and optional context.
            sys_msg: Optional system message for the language model.
            return_prompt: Whether to return both the task plan and the prompt used.
            **kwargs: Additional keyword arguments.
            
        Returns:
            If return_prompt is False (default): The generated task plan.
            If return_prompt is True: A tuple of (task plan, prompt used).
            
        Raises:
            ValueError: If the inputs are None or empty.
        """
        if not inputs:
            logger.error('TaskPlanning action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to TaskPlanning action is None or empty.')
        prompt_params_names = ['goal', 'history', 'suggestion']
        prompt_params_values = {param: inputs.get(param, '') for param in prompt_params_names}
        prompt = self.prompt.format(**prompt_params_values)
        task_plan = llm.generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format, parse_mode='json')
        if return_prompt:
            return (task_plan, prompt)
        return task_plan

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> TaskPlanningOutput:
    """Execute the task planning process.
        
        This method uses the provided language model to generate a structured
        plan of sub-tasks based on the user's goal and any additional context.
        
        Args:
            llm: The language model to use for planning.
            inputs: Input data containing the goal and optional context.
            sys_msg: Optional system message for the language model.
            return_prompt: Whether to return both the task plan and the prompt used.
            **kwargs: Additional keyword arguments.
            
        Returns:
            If return_prompt is False (default): The generated task plan.
            If return_prompt is True: A tuple of (task plan, prompt used).
            
        Raises:
            ValueError: If the inputs are None or empty.
        """
    if not inputs:
        logger.error('TaskPlanning action received invalid `inputs`: None or empty.')
        raise ValueError('The `inputs` to TaskPlanning action is None or empty.')
    prompt_params_names = ['goal', 'history', 'suggestion']
    prompt_params_values = {param: inputs.get(param, '') for param in prompt_params_names}
    prompt = self.prompt.format(**prompt_params_values)
    task_plan = llm.generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format, parse_mode='json')
    if return_prompt:
        return (task_plan, prompt)
    return task_plan

class HTMLGenerator:
    """Generates the HTML report with neomorphism styling and optimized layout."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.assets_dir = self.output_path.parent / 'assets'
        self.assets_dir.mkdir(exist_ok=True)

    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64字符串"""
        try:
            if not image_path or not os.path.exists(image_path):
                return ''
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f'⚠️ 无法读取图片 {image_path}: {e}')
            return ''

    def _get_latest_close_price(self, stock_code: str, timestamp: str) -> str:
        """从股票日线数据CSV文件中读取最新的收盘价"""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_daily_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                print(f'⚠️ 股票日线数据文件不存在: {csv_path}')
                return 'N/A'
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 2:
                print(f'⚠️ 股票日线数据文件为空或格式错误: {csv_path}')
                return 'N/A'
            last_line = lines[-1].strip()
            if not last_line:
                last_line = lines[-2].strip()
            fields = last_line.split(',')
            if len(fields) >= 6:
                close_price = fields[5]
                return close_price
            else:
                print(f'⚠️ 股票日线数据格式错误: {last_line}')
                return 'N/A'
        except Exception as e:
            print(f'⚠️ 读取股票收盘价失败: {e}')
            return 'N/A'

    def generate_report(self, md_file_path: str, technical_chart_path: str, price_volume_chart_path: str) -> str:
        """Generate the complete HTML report with base64 encoded images."""
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        parser = MarkdownParser(md_content)
        metadata = parser.get_metadata()
        technical_chart_base64 = self.encode_image_to_base64(technical_chart_path)
        price_volume_chart_base64 = self.encode_image_to_base64(price_volume_chart_path)
        html_content = self._generate_html_structure(parser, metadata, technical_chart_base64, price_volume_chart_base64)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(self.output_path)

    def _read_news_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read news data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_news_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            news_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    news_data.append({'新闻标题': row.get('新闻标题', ''), '来源': row.get('文章来源', ''), '发布时间': row.get('发布时间', ''), '影响程度': '中', '解读': row.get('新闻内容', '')[:100] + '...' if len(row.get('新闻内容', '')) > 100 else row.get('新闻内容', ''), '链接': row.get('新闻链接', '')})
            news_data.sort(key=lambda x: x['发布时间'], reverse=True)
            return news_data[:10]
        except Exception as e:
            print(f'Error reading news CSV: {e}')
            return []

    def _read_ratings_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read institution rating data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/institution_recommendation_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            ratings_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ratings_data.append({'机构名称': row.get('评级机构', ''), '评级': row.get('最新评级', ''), '目标价': row.get('目标价', '-'), '评级日期': row.get('评级日期', ''), '分析师': row.get('分析师', '不详')})
            ratings_data.sort(key=lambda x: x['评级日期'], reverse=True)
            return ratings_data[:10]
        except Exception as e:
            print(f'Error reading ratings CSV: {e}')
            return []

    def _generate_fundamentals_section_from_csv(self, metadata: Dict[str, str]) -> str:
        """Generate fundamentals section content directly from CSV files."""
        if not metadata:
            return ''
        stock_code = metadata.get('股票代码', '300750')
        timestamp = metadata.get('日期', '')
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d')
        else:
            import re
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', timestamp)
            if date_match:
                year, month, day = date_match.groups()
                timestamp = f'{year}{month}{day}'
            else:
                timestamp = datetime.now().strftime('%Y%m%d')
        news_data = self._read_news_from_csv(stock_code, timestamp)
        ratings_data = self._read_ratings_from_csv(stock_code, timestamp)
        print(f'Debug: Stock code: {stock_code}, Timestamp: {timestamp}')
        print(f'Debug: Found {len(news_data)} news items')
        print(f'Debug: Found {len(ratings_data)} rating items')
        news_html = ''
        if news_data:
            news_headers = ['新闻标题', '来源', '发布时间', '影响程度', '解读', '链接']
            news_rows = []
            for news in news_data:
                news_rows.append([news['新闻标题'], news['来源'], news['发布时间'], news['影响程度'], news['解读'], news['链接']])
            news_table_data = {'headers': news_headers, 'rows': news_rows}
            news_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.1 最新新闻动态</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(news_table_data)}\n                </div>\n            </div>\n            '
        ratings_html = ''
        if ratings_data:
            ratings_headers = ['机构名称', '评级', '目标价', '评级日期', '分析师']
            ratings_rows = []
            for rating in ratings_data:
                ratings_rows.append([rating['机构名称'], rating['评级'], rating['目标价'], rating['评级日期'], rating['分析师']])
            ratings_table_data = {'headers': ratings_headers, 'rows': ratings_rows}
            ratings_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.2 机构评级汇总</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(ratings_table_data)}\n                </div>\n            </div>\n            '
        return news_html + ratings_html

    def _generate_html_structure(self, parser: MarkdownParser, metadata: Dict[str, str], technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the complete HTML structure with neomorphism design."""
        header_html = self._generate_neomorphism_header(metadata, parser.sections)
        charts_html = self._generate_charts_section(technical_chart_base64, price_volume_chart_base64)
        dashboard_html = self._generate_dashboard_overview(parser.sections, metadata)
        sections_html = self._generate_detailed_sections(parser.sections, metadata)
        footer_html = self._generate_footer(metadata)
        return f"""\n        <!DOCTYPE html>\n        <html lang="zh-CN">\n        <head>\n            <meta charset="UTF-8">\n            <meta name="viewport" content="width=device-width, initial-scale=1.0">\n            <title>{metadata.get('股票名称', 'Unknown')} ({metadata.get('股票代码', 'Unknown')}) - 投资分析报告</title>\n            <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">\n            <style>\n                {self._get_neomorphism_css()}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                {header_html}\n                {dashboard_html}\n                {charts_html}\n                {sections_html}\n                {footer_html}\n            </div>\n            \n            <script>\n                {self._get_javascript()}\n            </script>\n        </body>\n        </html>\n        """

    def _generate_neomorphism_header(self, metadata: Dict[str, str], sections: Dict[str, Any]) -> str:
        """Generate the neomorphism-style header exactly like the reference image."""
        stock_name = metadata.get('股票名称', 'Unknown')
        stock_code = metadata.get('股票代码', 'Unknown')
        now = datetime.now()
        date = now.strftime('%Y年%m月%d日')
        time = now.strftime('%H:%M:%S')
        current_price = 'N/A'
        if stock_code != 'Unknown':
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', date)
            if date_match:
                timestamp = f'{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}'
                current_price = self._get_latest_close_price(stock_code, timestamp)
        if current_price == 'N/A' and '当前持仓' in metadata:
            holding_info = metadata['当前持仓']
            if '平均成本' in holding_info:
                price_match = re.search('平均成本\\s*(\\d+(?:\\.\\d+)?)', holding_info)
                if price_match:
                    current_price = price_match.group(1)
        return f'\n            <div class="main-header">\n                <h1 class="main-title">{stock_name}({stock_code})</h1>\n                <p class="main-subtitle">新拟态风格投资分析报告</p>\n                \n                <div class="header-info-cards">\n                    <div class="info-card">\n                        <div class="info-icon">📅</div>\n                        <span>{date}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">🕐</div>\n                        <span>{time}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">📊</div>\n                        <span>当前价格: ¥{current_price}</span>\n                    </div>\n                </div>\n            </div>\n        '

    def _generate_dashboard_overview(self, sections: Dict[str, Any], metadata: Dict[str, str]) -> str:
        """Generate a dashboard overview with key metrics extracted from actual report data."""
        investment_advice = '持有'
        investment_reason = '基于技术分析和基本面评估的专业建议'
        risk_level = '中等'
        confidence_level = '中等'
        target_price = '285'
        stop_price = '270'
        expected_return = '2%'
        strategy_period = '短期持仓'
        trading_section = sections.get('一、交易操作决策', {})
        if trading_section:
            subsections = trading_section.get('subsections', {})
            core_decision = subsections.get('1.1 核心决策', {})
            if core_decision:
                tables = core_decision.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            investment_advice = row[1] if row[1] else investment_advice
                            investment_reason = row[2] if row[2] else investment_reason
                            risk_level = row[3] if row[3] else risk_level
            price_targets = subsections.get('1.3 价格目标', {})
            if price_targets:
                tables = price_targets.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            target_price = str(row[1]).replace('RMB', '').replace(' ', '') if row[1] else target_price
                            stop_price = str(row[2]).replace('RMB', '').replace(' ', '') if row[2] else stop_price
                            expected_return = str(row[3]) if row[3] else expected_return
        risk_section = sections.get('五、风险评估', {})
        if risk_section:
            subsections = risk_section.get('subsections', {})
            risk_factors = subsections.get('5.1 风险因素', {})
            if risk_factors:
                tables = risk_factors.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    risk_levels = []
                    for row in rows:
                        if len(row) >= 2 and row[1]:
                            risk_levels.append(row[1])
                    if risk_levels:
                        high_count = risk_levels.count('高')
                        mid_count = risk_levels.count('中')
                        low_count = risk_levels.count('低')
                        if high_count > mid_count and high_count > low_count:
                            risk_level = '高'
                        elif mid_count >= high_count and mid_count >= low_count:
                            risk_level = '中等'
                        else:
                            risk_level = '低'
        advice_section = sections.get('七、投资建议', {})
        if advice_section:
            subsections = advice_section.get('subsections', {})
            short_term = subsections.get('7.1 短期操作建议', {})
            if short_term:
                text_content = short_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    return_match = re.search('预期收益[：:]\\s*([0-9.]+%)', content_text)
                    if return_match:
                        expected_return = return_match.group(1)
            long_term = subsections.get('7.2 中长期策略', {})
            if long_term:
                text_content = long_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    period_match = re.search('持有周期[：:]\\s*([^。\\n]+)', content_text)
                    if period_match:
                        period = period_match.group(1).strip()
                        if '月' in period or '年' in period:
                            strategy_period = '中长期持仓'
                        else:
                            strategy_period = '短期持仓'
        if investment_advice in ['买入', '强烈买入']:
            confidence_level = '高'
        elif investment_advice in ['卖出', '强烈卖出']:
            confidence_level = '低'
        elif investment_advice in ['部分卖出', '部分买入']:
            confidence_level = '中等'
        else:
            confidence_level = '中等'
        target_price = re.sub('[^0-9.]', '', str(target_price))
        stop_price = re.sub('[^0-9.]', '', str(stop_price))
        return f'\n            <div class="analysis-summary">\n                <div class="summary-card">\n                    <div class="card-icon green">\n                        <i class="icon">👍</i>\n                    </div>\n                    <h3>投资建议</h3>\n                    <div class="main-value">{investment_advice}</div>\n                    <div class="sub-text">{investment_reason[:50]}{('...' if len(investment_reason) > 50 else '')}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon blue">\n                        <i class="icon">🎯</i>\n                    </div>\n                    <h3>价格目标</h3>\n                    <div class="price-targets">\n                        <div class="price-item">\n                            <span class="label">目标价</span>\n                            <span class="value">¥{target_price}</span>\n                        </div>\n                        <div class="price-item">\n                            <span class="label">止损价</span>\n                            <span class="value">¥{stop_price}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">预期收益: {expected_return}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon orange">\n                        <i class="icon">🛡️</i>\n                    </div>\n                    <h3>风险评估</h3>\n                    <div class="risk-levels">\n                        <div class="risk-item">\n                            <span class="label">风险级别</span>\n                            <span class="value">{risk_level}</span>\n                        </div>\n                        <div class="risk-item">\n                            <span class="label">信心级别</span>\n                            <span class="value">{confidence_level}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">{strategy_period}</div>\n                </div>\n            </div>\n        '

    def _get_neomorphism_css(self) -> str:
        """Get the enhanced neomorphism CSS styles for the report."""
        return "\n        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');\n        \n        * {\n            margin: 0;\n            padding: 0;\n            box-sizing: border-box;\n        }\n        \n        body {\n            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\n            line-height: 1.6;\n            color: #2d3748;\n            background: #e0e5ec;\n            min-height: 100vh;\n        }\n        \n        .container {\n            max-width: 1200px;\n            margin: 0 auto;\n            padding: 40px 20px;\n        }\n        \n        /* Main Header Styles - Like Reference Image */\n        .main-header {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 60px 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 60px #bebebe, -20px -20px 60px #ffffff;\n            text-align: center;\n        }\n        \n        .main-title {\n            font-size: 3rem;\n            font-weight: 800;\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            -webkit-background-clip: text;\n            -webkit-text-fill-color: transparent;\n            background-clip: text;\n            margin-bottom: 15px;\n        }\n        \n        .main-subtitle {\n            font-size: 1.2rem;\n            color: #64748b;\n            font-weight: 500;\n            margin-bottom: 40px;\n        }\n        \n        .header-info-cards {\n            display: flex;\n            justify-content: center;\n            gap: 30px;\n            flex-wrap: wrap;\n        }\n        \n        .info-card {\n            display: flex;\n            align-items: center;\n            gap: 10px;\n            background: #e0e5ec;\n            padding: 15px 25px;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .info-card:hover {\n            transform: translateY(-2px);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        .info-icon {\n            font-size: 1.2rem;\n        }\n        \n        .info-card span {\n            font-weight: 600;\n            color: #2d3748;\n            font-size: 0.9rem;\n        }\n        \n        /* Analysis Summary - Like Reference Image */\n        .analysis-summary {\n            display: grid;\n            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));\n            gap: 30px;\n            margin-bottom: 30px;\n        }\n        \n        .summary-card {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            text-align: center;\n            transition: all 0.3s ease;\n        }\n        \n        .summary-card:hover {\n            transform: translateY(-5px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .card-icon {\n            width: 80px;\n            height: 80px;\n            border-radius: 20px;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            margin: 0 auto 20px auto;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .card-icon.green {\n            background: linear-gradient(135deg, #10b981, #059669);\n        }\n        \n        .card-icon.blue {\n            background: linear-gradient(135deg, #3b82f6, #1d4ed8);\n        }\n        \n        .card-icon.orange {\n            background: linear-gradient(135deg, #f59e0b, #d97706);\n        }\n        \n        .card-icon .icon {\n            font-size: 2.5rem;\n        }\n        \n        .summary-card h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n            margin-bottom: 20px;\n        }\n        \n        .main-value {\n            font-size: 2.5rem;\n            font-weight: 800;\n            color: #10b981;\n            margin-bottom: 15px;\n        }\n        \n        .sub-text {\n            font-size: 0.9rem;\n            color: #6b7280;\n            font-weight: 500;\n            line-height: 1.4;\n        }\n        \n        .price-targets, .risk-levels {\n            display: flex;\n            justify-content: space-around;\n            gap: 20px;\n            margin: 20px 0;\n        }\n        \n        .price-item, .risk-item {\n            background: #e0e5ec;\n            padding: 15px 20px;\n            border-radius: 15px;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n            text-align: center;\n            flex: 1;\n        }\n        \n        .price-item .label, .risk-item .label {\n            font-size: 0.8rem;\n            color: #6b7280;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            margin-bottom: 8px;\n            display: block;\n        }\n        \n        .price-item .value, .risk-item .value {\n            font-size: 1.5rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Chart Section Styles - Neomorphism Frames */\n        .chart-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-section:hover {\n            transform: translateY(-3px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .chart-header {\n            display: flex;\n            align-items: center;\n            gap: 12px;\n            margin-bottom: 25px;\n            padding-bottom: 15px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .chart-icon {\n            font-size: 1.8rem;\n        }\n        \n        .chart-header h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        .chart-container {\n            background: #e0e5ec;\n            border-radius: 20px;\n            padding: 20px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n            text-align: center;\n        }\n        \n        .chart-container img {\n            max-width: 100%;\n            height: auto;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-container img:hover {\n            transform: scale(1.02);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        /* Detail Sections */\n        .detail-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .section-header {\n            display: flex;\n            align-items: center;\n            gap: 16px;\n            margin-bottom: 30px;\n            padding-bottom: 20px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .section-icon {\n            width: 50px;\n            height: 50px;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            font-size: 1.5rem;\n        }\n        \n        .section-title {\n            font-size: 1.6rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Subsections */\n        .subsection {\n            margin-bottom: 25px;\n            padding: 20px;\n            background: #e0e5ec;\n            border-radius: 15px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n        }\n        \n        .subsection-title {\n            font-size: 1.2rem;\n            font-weight: 600;\n            color: #2d3748;\n            margin-bottom: 15px;\n            display: flex;\n            align-items: center;\n            gap: 8px;\n        }\n        \n        /* Tables */\n        .table-container {\n            overflow: hidden;\n            border-radius: 15px;\n            margin: 20px 0;\n            background: #e0e5ec;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n        }\n        \n        .data-table {\n            width: 100%;\n            border-collapse: collapse;\n        }\n        \n        .data-table th {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            color: white;\n            padding: 15px;\n            text-align: left;\n            font-weight: 600;\n            font-size: 0.9rem;\n            border: none;\n        }\n        \n        .data-table td {\n            padding: 15px;\n            border-bottom: 1px solid rgba(190, 190, 190, 0.2);\n            font-size: 0.9rem;\n            color: #2d3748;\n            background: #e0e5ec;\n        }\n        \n        .data-table tr:nth-child(even) td {\n            background: rgba(255, 255, 255, 0.3);\n        }\n        \n        .data-table tr:hover td {\n            background: rgba(102, 126, 234, 0.1);\n        }\n        \n        /* Scrollable table container for news and ratings */\n        .scrollable-table-container {\n            max-height: 400px;\n            overflow-y: auto;\n            overflow-x: hidden;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            padding: 5px;\n            margin: 10px 0;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar {\n            width: 8px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        \n        /* Status badges */\n        .status-badge {\n            padding: 8px 16px;\n            border-radius: 20px;\n            font-size: 0.8rem;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            display: inline-block;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .status-买入, .status-增持50股, .status-增持50100股 {\n            background: #10b981;\n            color: white;\n        }\n        \n        .status-卖出 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .status-持有 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-高 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .risk-中, .risk-中等 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-低 {\n            background: #10b981;\n            color: white;\n        }\n        \n        /* Links */\n        .news-title-link, .news-link {\n            color: #667eea;\n            text-decoration: none;\n            font-weight: 500;\n            transition: all 0.3s ease;\n        }\n        \n        .news-title-link:hover, .news-link:hover {\n            color: #5a67d8;\n            text-decoration: underline;\n        }\n        \n        /* Lists */\n        ul {\n            margin: 15px 0;\n            padding-left: 25px;\n        }\n        \n        li {\n            margin-bottom: 8px;\n            color: #2d3748;\n        }\n        \n        /* Footer */\n        .footer {\n            background: #2d3748;\n            color: white;\n            padding: 30px;\n            text-align: center;\n            border-radius: 20px;\n            margin-top: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .footer-content p {\n            margin-bottom: 8px;\n            opacity: 0.9;\n        }\n        \n        /* Responsive Design */\n        @media (max-width: 768px) {\n            .container {\n                padding: 20px 10px;\n            }\n            \n            .main-header {\n                padding: 40px 20px;\n            }\n            \n            .main-title {\n                font-size: 2.2rem;\n            }\n            \n            .header-info-cards {\n                flex-direction: column;\n                align-items: center;\n                gap: 15px;\n            }\n            \n            .info-card {\n                width: 100%;\n                max-width: 300px;\n                justify-content: center;\n            }\n            \n            .analysis-summary {\n                grid-template-columns: 1fr;\n            }\n            \n            .price-targets, .risk-levels {\n                flex-direction: column;\n                gap: 15px;\n            }\n            \n            .chart-section {\n                padding: 25px 15px;\n            }\n        }\n        \n        /* Animations */\n        @keyframes fadeInUp {\n            from {\n                opacity: 0;\n                transform: translateY(30px);\n            }\n            to {\n                opacity: 1;\n                transform: translateY(0);\n            }\n        }\n        \n        .detail-section, .chart-section, .analysis-summary {\n            animation: fadeInUp 0.6s ease forwards;\n        }\n        \n        /* Custom scrollbar */\n        ::-webkit-scrollbar {\n            width: 12px;\n        }\n        \n        ::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 10px;\n        }\n        \n        ::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 10px;\n            border: 2px solid #e0e5ec;\n        }\n        \n        ::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        "

    def _get_section_icon(self, section_name: str) -> str:
        """Get appropriate icon for section based on name."""
        section_lower = section_name.lower()
        if '交易' in section_lower or '决策' in section_lower:
            return '💼'
        elif '市场' in section_lower or '环境' in section_lower:
            return '🌍'
        elif '技术' in section_lower or '分析' in section_lower:
            return '📈'
        elif '基本面' in section_lower or '资讯' in section_lower:
            return '📰'
        elif '风险' in section_lower or '评估' in section_lower:
            return '🛡️'
        elif '历史' in section_lower or '表现' in section_lower:
            return '📊'
        elif '投资' in section_lower or '建议' in section_lower:
            return '💡'
        else:
            return '📄'

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the charts section with neomorphism styling."""
        if not technical_chart_base64 and (not price_volume_chart_base64):
            return ''
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📊</div>\n                        <h3>K线图技术分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n                    </div>\n                </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📈</div>\n                        <h3>技术指标综合分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n                    </div>\n                </div>\n            ')
        return ''.join(charts_html)

    def _generate_detailed_sections(self, sections, metadata: Dict[str, str]=None) -> str:
        """Generate detailed analysis sections with optimized layout."""
        sections_html = []
        section_order = ['1. 交易操作决策', '2. 市场环境分析', '3. 技术分析', '4. 基本面分析（资讯动向）', '5. 风险评估', '6. 历史表现回顾', '7. 投资建议']
        for section_key in section_order:
            if section_key in sections:
                section_data = sections[section_key]
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        for section_key, section_data in sections.items():
            if section_key not in section_order:
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        return ''.join(sections_html)

    def _generate_subsection(self, subsection_name: str, subsection_data: Dict[str, Any]) -> str:
        """Generate a single subsection."""
        content_parts = []
        for table in subsection_data.get('tables', []):
            content_parts.append(self._generate_table(table))
        for list_items in subsection_data.get('lists', []):
            content_parts.append(self._generate_list(list_items))
        if subsection_data.get('text'):
            content_parts.append(self._generate_text_content(subsection_data['text']))
        return f'\n        <div class="subsection">\n            <h3 class="subsection-title"><i class="fas fa-caret-right"></i> {subsection_name}</h3>\n            {''.join(content_parts)}\n        </div>\n        '

    def _generate_table(self, table_data: Dict[str, Any]) -> str:
        """Generate HTML table from table data."""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        if not headers:
            return ''
        is_news_table = any((keyword in ' '.join(headers).lower() for keyword in ['新闻', 'news', '标题', 'title']))
        has_link_column = any((keyword in ' '.join(headers).lower() for keyword in ['链接', 'url', 'link']))
        header_html = '<tr>' + ''.join((f'<th>{header}</th>' for header in headers)) + '</tr>'
        rows_html = []
        for row in rows:
            cells_html = []
            for i, cell in enumerate(row):
                header_name = headers[i].lower()
                if any((keyword in header_name for keyword in ['决策', '操作建议', '决策类型'])):
                    cell_class = cell.replace(' ', '').replace('-', '').replace('股', '')
                    cells_html.append(f'<td><span class="status-badge status-{cell_class}">{cell}</span></td>')
                elif any((keyword in header_name for keyword in ['风险等级', '等级', '风险级别'])):
                    cells_html.append(f'<td><span class="status-badge risk-{cell}">{cell}</span></td>')
                elif is_news_table and has_link_column and any((keyword in header_name for keyword in ['新闻标题', '标题', 'title'])):
                    link_index = None
                    for j, header in enumerate(headers):
                        if any((keyword in header.lower() for keyword in ['链接', 'url', 'link'])):
                            link_index = j
                            break
                    if link_index is not None and link_index < len(row):
                        link_url = row[link_index]
                        if link_url and link_url.lower() not in ['n/a', '-', 'na', ''] and ('http://' in link_url.lower() or 'https://' in link_url.lower()):
                            cells_html.append(f'<td><a href="{link_url}" target="_blank" class="news-title-link">{cell}</a></td>')
                        else:
                            cells_html.append(f'<td>{cell}</td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                elif any((keyword in header_name for keyword in ['链接', 'url', 'link'])):
                    if cell and cell.lower() not in ['n/a', '-', 'na', ''] and ('http://' in cell.lower() or 'https://' in cell.lower()):
                        cells_html.append(f'<td><a href="{cell}" target="_blank" class="news-link">{cell}</a></td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                else:
                    cells_html.append(f'<td>{cell}</td>')
            rows_html.append('<tr>' + ''.join(cells_html) + '</tr>')
        return f'\n        <div class="table-container">\n            <table class="data-table">\n                <thead>{header_html}</thead>\n                <tbody>{''.join(rows_html)}</tbody>\n            </table>\n        </div>\n        '

    def _generate_list(self, list_items: List[str]) -> str:
        """Generate HTML list from list items."""
        items_html = ''.join((f'<li>{item}</li>' for item in list_items))
        return f'<ul style="margin: 1rem 0; padding-left: 2rem;">{items_html}</ul>'

    def _generate_text_content(self, text_lines: List[str]) -> str:
        """Generate HTML from text content."""
        filtered_lines = []
        for line in text_lines:
            if line and (not line.startswith('---')):
                line = re.sub('\\*\\*(.*?)\\*\\*', '<strong>\\1</strong>', line)
                line = re.sub('\\*(.*?)\\*', '<em>\\1</em>', line)
                filtered_lines.append(line)
        if not filtered_lines:
            return ''
        return f'<div style="margin: 1rem 0; line-height: 1.6;">{'<br>'.join(filtered_lines)}</div>'

    def _generate_section_content(self, section_data: Dict[str, Any]) -> str:
        """Generate content for a report section with subsections."""
        content_html = []
        subsections = section_data.get('subsections', {})
        for subsection_name, subsection_data in subsections.items():
            content_html.append(self._generate_subsection(subsection_name, subsection_data))
        return ''.join(content_html)

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the enhanced charts section exactly like reference report."""
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-line"></i>\n                </div>\n                K线图技术分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n            </div>\n        </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-bar"></i>\n                </div>\n                技术指标综合分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n            </div>\n        </div>\n            ')
        return ''.join(charts_html)

    def _generate_footer(self, metadata: Dict[str, str]) -> str:
        """Generate the footer section."""
        return f'\n        <footer class="footer">\n            <div class="footer-content">\n                <p>报告生成时间: {metadata.get('报告生成时间', 'Unknown')}</p>\n                <p>数据来源: 股票市场数据、经济新闻、行业分析报告</p>\n                <p><strong>免责声明:</strong> 本报告仅供个人投资参考，不构成投资建议</p>\n            </div>\n        </footer>\n        '

    def _get_javascript(self) -> str:
        """Get the JavaScript for interactivity."""
        return "\n        // Intersection Observer for smooth animations\n        const observerOptions = {\n            threshold: 0.1,\n            rootMargin: '0px 0px -50px 0px'\n        };\n        \n        const observer = new IntersectionObserver((entries) => {\n            entries.forEach(entry => {\n                if (entry.isIntersecting) {\n                    entry.target.style.opacity = '1';\n                    entry.target.style.transform = 'translateY(0)';\n                }\n            });\n        }, observerOptions);\n        \n        // Initialize when DOM is ready\n        document.addEventListener('DOMContentLoaded', () => {\n            // Observe all sections for animations\n            const sections = document.querySelectorAll('.detail-section, .chart-section, .analysis-summary');\n            sections.forEach(section => {\n                observer.observe(section);\n            });\n            \n            // Add hover effects to tables\n            const tables = document.querySelectorAll('.data-table');\n            tables.forEach(table => {\n                const rows = table.querySelectorAll('tbody tr');\n                rows.forEach(row => {\n                    row.addEventListener('mouseenter', () => {\n                        row.style.transform = 'scale(1.01)';\n                        row.style.transition = 'transform 0.2s ease';\n                    });\n                    row.addEventListener('mouseleave', () => {\n                        row.style.transform = 'scale(1)';\n                    });\n                });\n            });\n            \n            // Add smooth hover effects to cards\n            const cards = document.querySelectorAll('.info-card, .summary-card');\n            cards.forEach(card => {\n                card.addEventListener('mouseenter', () => {\n                    card.style.transition = 'all 0.3s ease';\n                });\n            });\n        });\n        "

def _generate_section_content(self, section_data: Dict[str, Any]) -> str:
    """Generate content for a report section with subsections."""
    content_html = []
    subsections = section_data.get('subsections', {})
    for subsection_name, subsection_data in subsections.items():
        content_html.append(self._generate_subsection(subsection_name, subsection_data))
    return ''.join(content_html)

class SearchMemories(Action):

    def __init__(self, name: str='SearchMemories', description: str='Search memories by query and metadata filters', prompt: str='Search memories with query: {query}, filters: {metadata_filters}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or SearchMemoriesInput
        outputs_format = outputs_format or SearchMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> SearchMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, None) for attr in action_input_attrs}
        results = memory.search(query=action_input_data['query'], n=action_input_data['top_k'], metadata_filters=action_input_data['metadata_filters'])
        output = SearchMemoriesOutput(results=[{'message': msg.model_dump(), 'memory_id': mid} for msg, mid in results])
        if return_prompt:
            prompt = self.prompt.format(query=action_input_data['query'], metadata_filters=action_input_data['metadata_filters'] or {})
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> SearchMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, None) for attr in action_input_attrs}
    results = memory.search(query=action_input_data['query'], n=action_input_data['top_k'], metadata_filters=action_input_data['metadata_filters'])
    output = SearchMemoriesOutput(results=[{'message': msg.model_dump(), 'memory_id': mid} for msg, mid in results])
    if return_prompt:
        prompt = self.prompt.format(query=action_input_data['query'], metadata_filters=action_input_data['metadata_filters'] or {})
        return (output, prompt)
    return output

class SearchMemories(Action):

    def __init__(self, name: str='SearchMemories', description: str='Search memories by query and metadata filters', prompt: str='Search memories with query: {query}, filters: {metadata_filters}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or SearchMemoriesInput
        outputs_format = outputs_format or SearchMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> SearchMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, None) for attr in action_input_attrs}
        results = memory.search(query=action_input_data['query'], n=action_input_data['top_k'], metadata_filters=action_input_data['metadata_filters'])
        output = SearchMemoriesOutput(results=[{'message': msg.model_dump(), 'memory_id': mid} for msg, mid in results])
        if return_prompt:
            prompt = self.prompt.format(query=action_input_data['query'], metadata_filters=action_input_data['metadata_filters'] or {})
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> SearchMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, None) for attr in action_input_attrs}
    results = memory.search(query=action_input_data['query'], n=action_input_data['top_k'], metadata_filters=action_input_data['metadata_filters'])
    output = SearchMemoriesOutput(results=[{'message': msg.model_dump(), 'memory_id': mid} for msg, mid in results])
    if return_prompt:
        prompt = self.prompt.format(query=action_input_data['query'], metadata_filters=action_input_data['metadata_filters'] or {})
        return (output, prompt)
    return output

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

class DummyEmailSendAction(Action):

    def __init__(self, name: str='EmailSendAction', description: str='A dummy action that send a email to use with extracted data', prompt: str='Send a email to the user with the extracted data', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format: ActionInput = inputs_format or EmailSendActionInput
        outputs_format: ActionOutput = outputs_format or EmailSendActionOuput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> EmailSendActionOuput:
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, 'undefined') for attr in action_input_attrs}
        prompt = self.prompt.format(**action_input_data)
        output: EmailSendActionOuput = EmailSendActionOuput(send_action_result=f'Email sent to user with extracted data: {action_input_data['human_verified_data']}')
        if return_prompt:
            return (output, prompt)
        return output

    async def async_execute(self, llm: Optional[BaseLLM]=None, inputs: dict=None, sys_msg: str=None, return_prompt: bool=False, **kwargs) -> EmailSendActionOuput:
        return self.execute(llm, inputs, sys_msg, return_prompt, **kwargs)

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> EmailSendActionOuput:
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, 'undefined') for attr in action_input_attrs}
    prompt = self.prompt.format(**action_input_data)
    output: EmailSendActionOuput = EmailSendActionOuput(send_action_result=f'Email sent to user with extracted data: {action_input_data['human_verified_data']}')
    if return_prompt:
        return (output, prompt)
    return output

class HTMLGenerator:
    """Generates the HTML report with neomorphism styling and optimized layout."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.assets_dir = self.output_path.parent / 'assets'
        self.assets_dir.mkdir(exist_ok=True)

    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64字符串"""
        try:
            if not image_path or not os.path.exists(image_path):
                return ''
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f'⚠️ 无法读取图片 {image_path}: {e}')
            return ''

    def _get_latest_close_price(self, stock_code: str, timestamp: str) -> str:
        """从股票日线数据CSV文件中读取最新的收盘价"""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_daily_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                print(f'⚠️ 股票日线数据文件不存在: {csv_path}')
                return 'N/A'
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 2:
                print(f'⚠️ 股票日线数据文件为空或格式错误: {csv_path}')
                return 'N/A'
            last_line = lines[-1].strip()
            if not last_line:
                last_line = lines[-2].strip()
            fields = last_line.split(',')
            if len(fields) >= 6:
                close_price = fields[5]
                return close_price
            else:
                print(f'⚠️ 股票日线数据格式错误: {last_line}')
                return 'N/A'
        except Exception as e:
            print(f'⚠️ 读取股票收盘价失败: {e}')
            return 'N/A'

    def generate_report(self, md_file_path: str, technical_chart_path: str, price_volume_chart_path: str) -> str:
        """Generate the complete HTML report with base64 encoded images."""
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        parser = MarkdownParser(md_content)
        metadata = parser.get_metadata()
        technical_chart_base64 = self.encode_image_to_base64(technical_chart_path)
        price_volume_chart_base64 = self.encode_image_to_base64(price_volume_chart_path)
        html_content = self._generate_html_structure(parser, metadata, technical_chart_base64, price_volume_chart_base64)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(self.output_path)

    def _read_news_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read news data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_news_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            news_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    news_data.append({'新闻标题': row.get('新闻标题', ''), '来源': row.get('文章来源', ''), '发布时间': row.get('发布时间', ''), '影响程度': '中', '解读': row.get('新闻内容', '')[:100] + '...' if len(row.get('新闻内容', '')) > 100 else row.get('新闻内容', ''), '链接': row.get('新闻链接', '')})
            news_data.sort(key=lambda x: x['发布时间'], reverse=True)
            return news_data[:10]
        except Exception as e:
            print(f'Error reading news CSV: {e}')
            return []

    def _read_ratings_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read institution rating data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/institution_recommendation_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            ratings_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ratings_data.append({'机构名称': row.get('评级机构', ''), '评级': row.get('最新评级', ''), '目标价': row.get('目标价', '-'), '评级日期': row.get('评级日期', ''), '分析师': row.get('分析师', '不详')})
            ratings_data.sort(key=lambda x: x['评级日期'], reverse=True)
            return ratings_data[:10]
        except Exception as e:
            print(f'Error reading ratings CSV: {e}')
            return []

    def _generate_fundamentals_section_from_csv(self, metadata: Dict[str, str]) -> str:
        """Generate fundamentals section content directly from CSV files."""
        if not metadata:
            return ''
        stock_code = metadata.get('股票代码', '300750')
        timestamp = metadata.get('日期', '')
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d')
        else:
            import re
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', timestamp)
            if date_match:
                year, month, day = date_match.groups()
                timestamp = f'{year}{month}{day}'
            else:
                timestamp = datetime.now().strftime('%Y%m%d')
        news_data = self._read_news_from_csv(stock_code, timestamp)
        ratings_data = self._read_ratings_from_csv(stock_code, timestamp)
        print(f'Debug: Stock code: {stock_code}, Timestamp: {timestamp}')
        print(f'Debug: Found {len(news_data)} news items')
        print(f'Debug: Found {len(ratings_data)} rating items')
        news_html = ''
        if news_data:
            news_headers = ['新闻标题', '来源', '发布时间', '影响程度', '解读', '链接']
            news_rows = []
            for news in news_data:
                news_rows.append([news['新闻标题'], news['来源'], news['发布时间'], news['影响程度'], news['解读'], news['链接']])
            news_table_data = {'headers': news_headers, 'rows': news_rows}
            news_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.1 最新新闻动态</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(news_table_data)}\n                </div>\n            </div>\n            '
        ratings_html = ''
        if ratings_data:
            ratings_headers = ['机构名称', '评级', '目标价', '评级日期', '分析师']
            ratings_rows = []
            for rating in ratings_data:
                ratings_rows.append([rating['机构名称'], rating['评级'], rating['目标价'], rating['评级日期'], rating['分析师']])
            ratings_table_data = {'headers': ratings_headers, 'rows': ratings_rows}
            ratings_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.2 机构评级汇总</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(ratings_table_data)}\n                </div>\n            </div>\n            '
        return news_html + ratings_html

    def _generate_html_structure(self, parser: MarkdownParser, metadata: Dict[str, str], technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the complete HTML structure with neomorphism design."""
        header_html = self._generate_neomorphism_header(metadata, parser.sections)
        charts_html = self._generate_charts_section(technical_chart_base64, price_volume_chart_base64)
        dashboard_html = self._generate_dashboard_overview(parser.sections, metadata)
        sections_html = self._generate_detailed_sections(parser.sections, metadata)
        footer_html = self._generate_footer(metadata)
        return f"""\n        <!DOCTYPE html>\n        <html lang="zh-CN">\n        <head>\n            <meta charset="UTF-8">\n            <meta name="viewport" content="width=device-width, initial-scale=1.0">\n            <title>{metadata.get('股票名称', 'Unknown')} ({metadata.get('股票代码', 'Unknown')}) - 投资分析报告</title>\n            <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">\n            <style>\n                {self._get_neomorphism_css()}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                {header_html}\n                {dashboard_html}\n                {charts_html}\n                {sections_html}\n                {footer_html}\n            </div>\n            \n            <script>\n                {self._get_javascript()}\n            </script>\n        </body>\n        </html>\n        """

    def _generate_neomorphism_header(self, metadata: Dict[str, str], sections: Dict[str, Any]) -> str:
        """Generate the neomorphism-style header exactly like the reference image."""
        stock_name = metadata.get('股票名称', 'Unknown')
        stock_code = metadata.get('股票代码', 'Unknown')
        now = datetime.now()
        date = now.strftime('%Y年%m月%d日')
        time = now.strftime('%H:%M:%S')
        current_price = 'N/A'
        if stock_code != 'Unknown':
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', date)
            if date_match:
                timestamp = f'{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}'
                current_price = self._get_latest_close_price(stock_code, timestamp)
        if current_price == 'N/A' and '当前持仓' in metadata:
            holding_info = metadata['当前持仓']
            if '平均成本' in holding_info:
                price_match = re.search('平均成本\\s*(\\d+(?:\\.\\d+)?)', holding_info)
                if price_match:
                    current_price = price_match.group(1)
        return f'\n            <div class="main-header">\n                <h1 class="main-title">{stock_name}({stock_code})</h1>\n                <p class="main-subtitle">新拟态风格投资分析报告</p>\n                \n                <div class="header-info-cards">\n                    <div class="info-card">\n                        <div class="info-icon">📅</div>\n                        <span>{date}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">🕐</div>\n                        <span>{time}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">📊</div>\n                        <span>当前价格: ¥{current_price}</span>\n                    </div>\n                </div>\n            </div>\n        '

    def _generate_dashboard_overview(self, sections: Dict[str, Any], metadata: Dict[str, str]) -> str:
        """Generate a dashboard overview with key metrics extracted from actual report data."""
        investment_advice = '持有'
        investment_reason = '基于技术分析和基本面评估的专业建议'
        risk_level = '中等'
        confidence_level = '中等'
        target_price = '285'
        stop_price = '270'
        expected_return = '2%'
        strategy_period = '短期持仓'
        trading_section = sections.get('一、交易操作决策', {})
        if trading_section:
            subsections = trading_section.get('subsections', {})
            core_decision = subsections.get('1.1 核心决策', {})
            if core_decision:
                tables = core_decision.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            investment_advice = row[1] if row[1] else investment_advice
                            investment_reason = row[2] if row[2] else investment_reason
                            risk_level = row[3] if row[3] else risk_level
            price_targets = subsections.get('1.3 价格目标', {})
            if price_targets:
                tables = price_targets.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            target_price = str(row[1]).replace('RMB', '').replace(' ', '') if row[1] else target_price
                            stop_price = str(row[2]).replace('RMB', '').replace(' ', '') if row[2] else stop_price
                            expected_return = str(row[3]) if row[3] else expected_return
        risk_section = sections.get('五、风险评估', {})
        if risk_section:
            subsections = risk_section.get('subsections', {})
            risk_factors = subsections.get('5.1 风险因素', {})
            if risk_factors:
                tables = risk_factors.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    risk_levels = []
                    for row in rows:
                        if len(row) >= 2 and row[1]:
                            risk_levels.append(row[1])
                    if risk_levels:
                        high_count = risk_levels.count('高')
                        mid_count = risk_levels.count('中')
                        low_count = risk_levels.count('低')
                        if high_count > mid_count and high_count > low_count:
                            risk_level = '高'
                        elif mid_count >= high_count and mid_count >= low_count:
                            risk_level = '中等'
                        else:
                            risk_level = '低'
        advice_section = sections.get('七、投资建议', {})
        if advice_section:
            subsections = advice_section.get('subsections', {})
            short_term = subsections.get('7.1 短期操作建议', {})
            if short_term:
                text_content = short_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    return_match = re.search('预期收益[：:]\\s*([0-9.]+%)', content_text)
                    if return_match:
                        expected_return = return_match.group(1)
            long_term = subsections.get('7.2 中长期策略', {})
            if long_term:
                text_content = long_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    period_match = re.search('持有周期[：:]\\s*([^。\\n]+)', content_text)
                    if period_match:
                        period = period_match.group(1).strip()
                        if '月' in period or '年' in period:
                            strategy_period = '中长期持仓'
                        else:
                            strategy_period = '短期持仓'
        if investment_advice in ['买入', '强烈买入']:
            confidence_level = '高'
        elif investment_advice in ['卖出', '强烈卖出']:
            confidence_level = '低'
        elif investment_advice in ['部分卖出', '部分买入']:
            confidence_level = '中等'
        else:
            confidence_level = '中等'
        target_price = re.sub('[^0-9.]', '', str(target_price))
        stop_price = re.sub('[^0-9.]', '', str(stop_price))
        return f'\n            <div class="analysis-summary">\n                <div class="summary-card">\n                    <div class="card-icon green">\n                        <i class="icon">👍</i>\n                    </div>\n                    <h3>投资建议</h3>\n                    <div class="main-value">{investment_advice}</div>\n                    <div class="sub-text">{investment_reason[:50]}{('...' if len(investment_reason) > 50 else '')}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon blue">\n                        <i class="icon">🎯</i>\n                    </div>\n                    <h3>价格目标</h3>\n                    <div class="price-targets">\n                        <div class="price-item">\n                            <span class="label">目标价</span>\n                            <span class="value">¥{target_price}</span>\n                        </div>\n                        <div class="price-item">\n                            <span class="label">止损价</span>\n                            <span class="value">¥{stop_price}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">预期收益: {expected_return}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon orange">\n                        <i class="icon">🛡️</i>\n                    </div>\n                    <h3>风险评估</h3>\n                    <div class="risk-levels">\n                        <div class="risk-item">\n                            <span class="label">风险级别</span>\n                            <span class="value">{risk_level}</span>\n                        </div>\n                        <div class="risk-item">\n                            <span class="label">信心级别</span>\n                            <span class="value">{confidence_level}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">{strategy_period}</div>\n                </div>\n            </div>\n        '

    def _get_neomorphism_css(self) -> str:
        """Get the enhanced neomorphism CSS styles for the report."""
        return "\n        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');\n        \n        * {\n            margin: 0;\n            padding: 0;\n            box-sizing: border-box;\n        }\n        \n        body {\n            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\n            line-height: 1.6;\n            color: #2d3748;\n            background: #e0e5ec;\n            min-height: 100vh;\n        }\n        \n        .container {\n            max-width: 1200px;\n            margin: 0 auto;\n            padding: 40px 20px;\n        }\n        \n        /* Main Header Styles - Like Reference Image */\n        .main-header {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 60px 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 60px #bebebe, -20px -20px 60px #ffffff;\n            text-align: center;\n        }\n        \n        .main-title {\n            font-size: 3rem;\n            font-weight: 800;\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            -webkit-background-clip: text;\n            -webkit-text-fill-color: transparent;\n            background-clip: text;\n            margin-bottom: 15px;\n        }\n        \n        .main-subtitle {\n            font-size: 1.2rem;\n            color: #64748b;\n            font-weight: 500;\n            margin-bottom: 40px;\n        }\n        \n        .header-info-cards {\n            display: flex;\n            justify-content: center;\n            gap: 30px;\n            flex-wrap: wrap;\n        }\n        \n        .info-card {\n            display: flex;\n            align-items: center;\n            gap: 10px;\n            background: #e0e5ec;\n            padding: 15px 25px;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .info-card:hover {\n            transform: translateY(-2px);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        .info-icon {\n            font-size: 1.2rem;\n        }\n        \n        .info-card span {\n            font-weight: 600;\n            color: #2d3748;\n            font-size: 0.9rem;\n        }\n        \n        /* Analysis Summary - Like Reference Image */\n        .analysis-summary {\n            display: grid;\n            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));\n            gap: 30px;\n            margin-bottom: 30px;\n        }\n        \n        .summary-card {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            text-align: center;\n            transition: all 0.3s ease;\n        }\n        \n        .summary-card:hover {\n            transform: translateY(-5px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .card-icon {\n            width: 80px;\n            height: 80px;\n            border-radius: 20px;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            margin: 0 auto 20px auto;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .card-icon.green {\n            background: linear-gradient(135deg, #10b981, #059669);\n        }\n        \n        .card-icon.blue {\n            background: linear-gradient(135deg, #3b82f6, #1d4ed8);\n        }\n        \n        .card-icon.orange {\n            background: linear-gradient(135deg, #f59e0b, #d97706);\n        }\n        \n        .card-icon .icon {\n            font-size: 2.5rem;\n        }\n        \n        .summary-card h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n            margin-bottom: 20px;\n        }\n        \n        .main-value {\n            font-size: 2.5rem;\n            font-weight: 800;\n            color: #10b981;\n            margin-bottom: 15px;\n        }\n        \n        .sub-text {\n            font-size: 0.9rem;\n            color: #6b7280;\n            font-weight: 500;\n            line-height: 1.4;\n        }\n        \n        .price-targets, .risk-levels {\n            display: flex;\n            justify-content: space-around;\n            gap: 20px;\n            margin: 20px 0;\n        }\n        \n        .price-item, .risk-item {\n            background: #e0e5ec;\n            padding: 15px 20px;\n            border-radius: 15px;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n            text-align: center;\n            flex: 1;\n        }\n        \n        .price-item .label, .risk-item .label {\n            font-size: 0.8rem;\n            color: #6b7280;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            margin-bottom: 8px;\n            display: block;\n        }\n        \n        .price-item .value, .risk-item .value {\n            font-size: 1.5rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Chart Section Styles - Neomorphism Frames */\n        .chart-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-section:hover {\n            transform: translateY(-3px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .chart-header {\n            display: flex;\n            align-items: center;\n            gap: 12px;\n            margin-bottom: 25px;\n            padding-bottom: 15px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .chart-icon {\n            font-size: 1.8rem;\n        }\n        \n        .chart-header h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        .chart-container {\n            background: #e0e5ec;\n            border-radius: 20px;\n            padding: 20px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n            text-align: center;\n        }\n        \n        .chart-container img {\n            max-width: 100%;\n            height: auto;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-container img:hover {\n            transform: scale(1.02);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        /* Detail Sections */\n        .detail-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .section-header {\n            display: flex;\n            align-items: center;\n            gap: 16px;\n            margin-bottom: 30px;\n            padding-bottom: 20px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .section-icon {\n            width: 50px;\n            height: 50px;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            font-size: 1.5rem;\n        }\n        \n        .section-title {\n            font-size: 1.6rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Subsections */\n        .subsection {\n            margin-bottom: 25px;\n            padding: 20px;\n            background: #e0e5ec;\n            border-radius: 15px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n        }\n        \n        .subsection-title {\n            font-size: 1.2rem;\n            font-weight: 600;\n            color: #2d3748;\n            margin-bottom: 15px;\n            display: flex;\n            align-items: center;\n            gap: 8px;\n        }\n        \n        /* Tables */\n        .table-container {\n            overflow: hidden;\n            border-radius: 15px;\n            margin: 20px 0;\n            background: #e0e5ec;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n        }\n        \n        .data-table {\n            width: 100%;\n            border-collapse: collapse;\n        }\n        \n        .data-table th {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            color: white;\n            padding: 15px;\n            text-align: left;\n            font-weight: 600;\n            font-size: 0.9rem;\n            border: none;\n        }\n        \n        .data-table td {\n            padding: 15px;\n            border-bottom: 1px solid rgba(190, 190, 190, 0.2);\n            font-size: 0.9rem;\n            color: #2d3748;\n            background: #e0e5ec;\n        }\n        \n        .data-table tr:nth-child(even) td {\n            background: rgba(255, 255, 255, 0.3);\n        }\n        \n        .data-table tr:hover td {\n            background: rgba(102, 126, 234, 0.1);\n        }\n        \n        /* Scrollable table container for news and ratings */\n        .scrollable-table-container {\n            max-height: 400px;\n            overflow-y: auto;\n            overflow-x: hidden;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            padding: 5px;\n            margin: 10px 0;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar {\n            width: 8px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        \n        /* Status badges */\n        .status-badge {\n            padding: 8px 16px;\n            border-radius: 20px;\n            font-size: 0.8rem;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            display: inline-block;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .status-买入, .status-增持50股, .status-增持50100股 {\n            background: #10b981;\n            color: white;\n        }\n        \n        .status-卖出 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .status-持有 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-高 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .risk-中, .risk-中等 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-低 {\n            background: #10b981;\n            color: white;\n        }\n        \n        /* Links */\n        .news-title-link, .news-link {\n            color: #667eea;\n            text-decoration: none;\n            font-weight: 500;\n            transition: all 0.3s ease;\n        }\n        \n        .news-title-link:hover, .news-link:hover {\n            color: #5a67d8;\n            text-decoration: underline;\n        }\n        \n        /* Lists */\n        ul {\n            margin: 15px 0;\n            padding-left: 25px;\n        }\n        \n        li {\n            margin-bottom: 8px;\n            color: #2d3748;\n        }\n        \n        /* Footer */\n        .footer {\n            background: #2d3748;\n            color: white;\n            padding: 30px;\n            text-align: center;\n            border-radius: 20px;\n            margin-top: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .footer-content p {\n            margin-bottom: 8px;\n            opacity: 0.9;\n        }\n        \n        /* Responsive Design */\n        @media (max-width: 768px) {\n            .container {\n                padding: 20px 10px;\n            }\n            \n            .main-header {\n                padding: 40px 20px;\n            }\n            \n            .main-title {\n                font-size: 2.2rem;\n            }\n            \n            .header-info-cards {\n                flex-direction: column;\n                align-items: center;\n                gap: 15px;\n            }\n            \n            .info-card {\n                width: 100%;\n                max-width: 300px;\n                justify-content: center;\n            }\n            \n            .analysis-summary {\n                grid-template-columns: 1fr;\n            }\n            \n            .price-targets, .risk-levels {\n                flex-direction: column;\n                gap: 15px;\n            }\n            \n            .chart-section {\n                padding: 25px 15px;\n            }\n        }\n        \n        /* Animations */\n        @keyframes fadeInUp {\n            from {\n                opacity: 0;\n                transform: translateY(30px);\n            }\n            to {\n                opacity: 1;\n                transform: translateY(0);\n            }\n        }\n        \n        .detail-section, .chart-section, .analysis-summary {\n            animation: fadeInUp 0.6s ease forwards;\n        }\n        \n        /* Custom scrollbar */\n        ::-webkit-scrollbar {\n            width: 12px;\n        }\n        \n        ::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 10px;\n        }\n        \n        ::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 10px;\n            border: 2px solid #e0e5ec;\n        }\n        \n        ::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        "

    def _get_section_icon(self, section_name: str) -> str:
        """Get appropriate icon for section based on name."""
        section_lower = section_name.lower()
        if '交易' in section_lower or '决策' in section_lower:
            return '💼'
        elif '市场' in section_lower or '环境' in section_lower:
            return '🌍'
        elif '技术' in section_lower or '分析' in section_lower:
            return '📈'
        elif '基本面' in section_lower or '资讯' in section_lower:
            return '📰'
        elif '风险' in section_lower or '评估' in section_lower:
            return '🛡️'
        elif '历史' in section_lower or '表现' in section_lower:
            return '📊'
        elif '投资' in section_lower or '建议' in section_lower:
            return '💡'
        else:
            return '📄'

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the charts section with neomorphism styling."""
        if not technical_chart_base64 and (not price_volume_chart_base64):
            return ''
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📊</div>\n                        <h3>K线图技术分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n                    </div>\n                </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📈</div>\n                        <h3>技术指标综合分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n                    </div>\n                </div>\n            ')
        return ''.join(charts_html)

    def _generate_detailed_sections(self, sections, metadata: Dict[str, str]=None) -> str:
        """Generate detailed analysis sections with optimized layout."""
        sections_html = []
        section_order = ['1. 交易操作决策', '2. 市场环境分析', '3. 技术分析', '4. 基本面分析（资讯动向）', '5. 风险评估', '6. 历史表现回顾', '7. 投资建议']
        for section_key in section_order:
            if section_key in sections:
                section_data = sections[section_key]
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        for section_key, section_data in sections.items():
            if section_key not in section_order:
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        return ''.join(sections_html)

    def _generate_subsection(self, subsection_name: str, subsection_data: Dict[str, Any]) -> str:
        """Generate a single subsection."""
        content_parts = []
        for table in subsection_data.get('tables', []):
            content_parts.append(self._generate_table(table))
        for list_items in subsection_data.get('lists', []):
            content_parts.append(self._generate_list(list_items))
        if subsection_data.get('text'):
            content_parts.append(self._generate_text_content(subsection_data['text']))
        return f'\n        <div class="subsection">\n            <h3 class="subsection-title"><i class="fas fa-caret-right"></i> {subsection_name}</h3>\n            {''.join(content_parts)}\n        </div>\n        '

    def _generate_table(self, table_data: Dict[str, Any]) -> str:
        """Generate HTML table from table data."""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        if not headers:
            return ''
        is_news_table = any((keyword in ' '.join(headers).lower() for keyword in ['新闻', 'news', '标题', 'title']))
        has_link_column = any((keyword in ' '.join(headers).lower() for keyword in ['链接', 'url', 'link']))
        header_html = '<tr>' + ''.join((f'<th>{header}</th>' for header in headers)) + '</tr>'
        rows_html = []
        for row in rows:
            cells_html = []
            for i, cell in enumerate(row):
                header_name = headers[i].lower()
                if any((keyword in header_name for keyword in ['决策', '操作建议', '决策类型'])):
                    cell_class = cell.replace(' ', '').replace('-', '').replace('股', '')
                    cells_html.append(f'<td><span class="status-badge status-{cell_class}">{cell}</span></td>')
                elif any((keyword in header_name for keyword in ['风险等级', '等级', '风险级别'])):
                    cells_html.append(f'<td><span class="status-badge risk-{cell}">{cell}</span></td>')
                elif is_news_table and has_link_column and any((keyword in header_name for keyword in ['新闻标题', '标题', 'title'])):
                    link_index = None
                    for j, header in enumerate(headers):
                        if any((keyword in header.lower() for keyword in ['链接', 'url', 'link'])):
                            link_index = j
                            break
                    if link_index is not None and link_index < len(row):
                        link_url = row[link_index]
                        if link_url and link_url.lower() not in ['n/a', '-', 'na', ''] and ('http://' in link_url.lower() or 'https://' in link_url.lower()):
                            cells_html.append(f'<td><a href="{link_url}" target="_blank" class="news-title-link">{cell}</a></td>')
                        else:
                            cells_html.append(f'<td>{cell}</td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                elif any((keyword in header_name for keyword in ['链接', 'url', 'link'])):
                    if cell and cell.lower() not in ['n/a', '-', 'na', ''] and ('http://' in cell.lower() or 'https://' in cell.lower()):
                        cells_html.append(f'<td><a href="{cell}" target="_blank" class="news-link">{cell}</a></td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                else:
                    cells_html.append(f'<td>{cell}</td>')
            rows_html.append('<tr>' + ''.join(cells_html) + '</tr>')
        return f'\n        <div class="table-container">\n            <table class="data-table">\n                <thead>{header_html}</thead>\n                <tbody>{''.join(rows_html)}</tbody>\n            </table>\n        </div>\n        '

    def _generate_list(self, list_items: List[str]) -> str:
        """Generate HTML list from list items."""
        items_html = ''.join((f'<li>{item}</li>' for item in list_items))
        return f'<ul style="margin: 1rem 0; padding-left: 2rem;">{items_html}</ul>'

    def _generate_text_content(self, text_lines: List[str]) -> str:
        """Generate HTML from text content."""
        filtered_lines = []
        for line in text_lines:
            if line and (not line.startswith('---')):
                line = re.sub('\\*\\*(.*?)\\*\\*', '<strong>\\1</strong>', line)
                line = re.sub('\\*(.*?)\\*', '<em>\\1</em>', line)
                filtered_lines.append(line)
        if not filtered_lines:
            return ''
        return f'<div style="margin: 1rem 0; line-height: 1.6;">{'<br>'.join(filtered_lines)}</div>'

    def _generate_section_content(self, section_data: Dict[str, Any]) -> str:
        """Generate content for a report section with subsections."""
        content_html = []
        subsections = section_data.get('subsections', {})
        for subsection_name, subsection_data in subsections.items():
            content_html.append(self._generate_subsection(subsection_name, subsection_data))
        return ''.join(content_html)

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the enhanced charts section exactly like reference report."""
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-line"></i>\n                </div>\n                K线图技术分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n            </div>\n        </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-bar"></i>\n                </div>\n                技术指标综合分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n            </div>\n        </div>\n            ')
        return ''.join(charts_html)

    def _generate_footer(self, metadata: Dict[str, str]) -> str:
        """Generate the footer section."""
        return f'\n        <footer class="footer">\n            <div class="footer-content">\n                <p>报告生成时间: {metadata.get('报告生成时间', 'Unknown')}</p>\n                <p>数据来源: 股票市场数据、经济新闻、行业分析报告</p>\n                <p><strong>免责声明:</strong> 本报告仅供个人投资参考，不构成投资建议</p>\n            </div>\n        </footer>\n        '

    def _get_javascript(self) -> str:
        """Get the JavaScript for interactivity."""
        return "\n        // Intersection Observer for smooth animations\n        const observerOptions = {\n            threshold: 0.1,\n            rootMargin: '0px 0px -50px 0px'\n        };\n        \n        const observer = new IntersectionObserver((entries) => {\n            entries.forEach(entry => {\n                if (entry.isIntersecting) {\n                    entry.target.style.opacity = '1';\n                    entry.target.style.transform = 'translateY(0)';\n                }\n            });\n        }, observerOptions);\n        \n        // Initialize when DOM is ready\n        document.addEventListener('DOMContentLoaded', () => {\n            // Observe all sections for animations\n            const sections = document.querySelectorAll('.detail-section, .chart-section, .analysis-summary');\n            sections.forEach(section => {\n                observer.observe(section);\n            });\n            \n            // Add hover effects to tables\n            const tables = document.querySelectorAll('.data-table');\n            tables.forEach(table => {\n                const rows = table.querySelectorAll('tbody tr');\n                rows.forEach(row => {\n                    row.addEventListener('mouseenter', () => {\n                        row.style.transform = 'scale(1.01)';\n                        row.style.transition = 'transform 0.2s ease';\n                    });\n                    row.addEventListener('mouseleave', () => {\n                        row.style.transform = 'scale(1)';\n                    });\n                });\n            });\n            \n            // Add smooth hover effects to cards\n            const cards = document.querySelectorAll('.info-card, .summary-card');\n            cards.forEach(card => {\n                card.addEventListener('mouseenter', () => {\n                    card.style.transition = 'all 0.3s ease';\n                });\n            });\n        });\n        "

def _generate_section_content(self, section_data: Dict[str, Any]) -> str:
    """Generate content for a report section with subsections."""
    content_html = []
    subsections = section_data.get('subsections', {})
    for subsection_name, subsection_data in subsections.items():
        content_html.append(self._generate_subsection(subsection_name, subsection_data))
    return ''.join(content_html)

def demo_error_handling():
    """Demonstrate error handling"""
    print('\n=== Demonstrate Error Handling ===')
    print('\n1. Try to load non-existent file...')
    try:
        MultiAgentDebateActionGraph.load_module('nonexistent_file.json')
    except FileNotFoundError as e:
        print(f'Expected error: {e}')
    print('\n2. Try to create instance from invalid dictionary...')
    try:
        invalid_config = {'invalid_field': 'invalid_value'}
        MultiAgentDebateActionGraph.from_dict(invalid_config)
        print('Successfully created instance (using default values)')
    except Exception as e:
        print(f'Error: {e}')

class CustomProgram:

    def __init__(self, model: OpenAILLM):
        self.model = model
        self.prompt = "Let's think step by step to answer the math question: {problem}"

    def save(self, path: str):
        params = {'prompt': self.prompt}
        with open(path, 'w') as f:
            json.dump(params, f)

    def load(self, path: str):
        with open(path, 'r') as f:
            params = json.load(f)
            self.prompt = params['prompt']

    def __call__(self, problem: str) -> Tuple[str, dict]:
        prompt = self.prompt.format(problem=problem)
        response = self.model.generate(prompt=prompt)
        solution = response.content
        return (solution, {'problem': problem, 'solution': solution})

def __call__(self, problem: str) -> Tuple[str, dict]:
    prompt = self.prompt.format(problem=problem)
    response = self.model.generate(prompt=prompt)
    solution = response.content
    return (solution, {'problem': problem, 'solution': solution})

def collate_func(example: dict) -> dict:
    context_list = []
    for item in example['context']:
        context = 'Title: {}\nText: {}'.format(item[0], ' '.join([t.strip() for t in item[1]]))
        context_list.append(context)
    context = '\n\n'.join(context_list)
    problem = 'Context: {}\n\nQuestion: {}\n\nAnswer:'.format(context, example['question'])
    return {'problem': problem}

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

def collate_func(x):
    return {'processed_' + k: v for k, v in x.items()}

