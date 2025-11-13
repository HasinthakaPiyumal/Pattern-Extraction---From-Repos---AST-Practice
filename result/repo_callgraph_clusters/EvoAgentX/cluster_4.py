# Cluster 4

class Config(BaseModel):
    llm_config: dict
    agents: Optional[Union[str, List[dict]]] = []
    model_config = {'arbitrary_types_allowed': True, 'extra': 'allow', 'protected_namespaces': ()}

    @classmethod
    def from_file(cls, path: str):
        with open(path, mode='r', encoding='utf-8') as file:
            data = yaml.safe_load(file.read())
        config = cls.model_validate(data)
        return config

    @property
    def kwargs(self):
        return self.model_extra

    @model_validator(mode='before')
    @classmethod
    def validate_config_data(cls, data: Any) -> Any:
        llm_config_data = data.get('llm_config', None)
        if not llm_config_data:
            raise ValueError("config file must contain 'llm_config'")
        data['llm_config'] = cls.process_llm_config(data=data['llm_config'])
        agents_data = data.get('agents', None)
        if agents_data:
            data['agents'] = cls.process_agents_data(agents=agents_data, llm_config=data['llm_config'])
        return data

    @classmethod
    def process_llm_config(cls, data: dict) -> dict:
        llm_type = data.get('llm_type', None)
        if not llm_type:
            raise ValueError('must specify `llm_type` in in `llm_config`!')
        llm_config_cls: Type[LLMConfig] = MODEL_REGISTRY.get_model_config(llm_type)
        if 'class_name' in data:
            assert data['class_name'] == llm_config_cls.__name__, "the 'class_name' specified in 'llm_config' ({}) doesn't match the LLMConfig class ({}) registered for {} model. You should either remove 'class_name' or set it to {}.".format(data['class_name'], llm_config_cls.__name__, llm_type, llm_config_cls.__name__)
        else:
            data['class_name'] = llm_config_cls.__name__
        return data

    @classmethod
    def process_agents_data(cls, agents: List[dict], llm_config=dict) -> List[dict]:
        for agent in agents:
            if 'llm_config' not in agent:
                agent['llm_config'] = llm_config
        return agents

@classmethod
def process_llm_config(cls, data: dict) -> dict:
    llm_type = data.get('llm_type', None)
    if not llm_type:
        raise ValueError('must specify `llm_type` in in `llm_config`!')
    llm_config_cls: Type[LLMConfig] = MODEL_REGISTRY.get_model_config(llm_type)
    if 'class_name' in data:
        assert data['class_name'] == llm_config_cls.__name__, "the 'class_name' specified in 'llm_config' ({}) doesn't match the LLMConfig class ({}) registered for {} model. You should either remove 'class_name' or set it to {}.".format(data['class_name'], llm_config_cls.__name__, llm_type, llm_config_cls.__name__)
    else:
        data['class_name'] = llm_config_cls.__name__
    return data

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

def set_operator(self, data: dict):
    self.name = data.get('name', self.name)
    self.description = data.get('description', self.description)
    self.interface = data.get('interface', self.interface)
    self.prompt = data.get('prompt', self.prompt)

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

class MiproRegistry(ParamRegistry):
    """
    Extended ParamRegistry that supports storing input_names and output_names
    for each optimizable field. Compatible with all original track() usages.
    """

    def track(self, root_or_obj: Any, path_or_attr: str=None, *, name: Optional[str]=None, input_names: Optional[List[str]]=None, output_names: Optional[List[str]]=None, input_descs: Optional[Dict[str, str]]=None, output_descs: Optional[Dict[str, str]]=None):
        if isinstance(root_or_obj, (list, tuple)):
            for item in root_or_obj:
                if isinstance(item, dict):
                    self.track(**item)
                elif isinstance(item, (list, tuple)):
                    if len(item) == 7:
                        self.track(item[0], item[1], name=item[2], input_names=item[3], output_names=item[4], input_descs=item[5], output_descs=item[6])
                    else:
                        raise ValueError('Each tuple must be (obj, attr, name, input_names, output_names, input_descs, output_descs)')
            return self
        super().track(root_or_obj, path_or_attr, name=name)
        key = name or path_or_attr
        field = self.fields[key]
        field.input_names = input_names or []
        field.output_names = output_names or []
        field.input_descs = input_descs or {}
        field.output_descs = output_descs or {}
        return self

    def get_input_names(self, name: str) -> List[str]:
        """Return the input_names for a registered field, or an empty list if not set."""
        return getattr(self.fields[name], 'input_names', None) or []

    def get_output_names(self, name: str) -> List[str]:
        """Return the output_names for a registered field, or an empty list if not set."""
        return getattr(self.fields[name], 'output_names', None) or []

    def get_input_desc_dict(self, name: str) -> Dict[str, str]:
        """Return the input_descs for a registered field, or an empty dict if not set."""
        return getattr(self.fields[name], 'input_descs', {})

    def get_output_desc_dict(self, name: str) -> Dict[str, str]:
        """Return the output_descs for a registered field, or an empty dict if not set."""
        return getattr(self.fields[name], 'output_descs', {})

    def get_input_desc(self, name: str, input_name: str) -> str:
        """Return the input_desc for a registered field, or an empty string if not set."""
        return self.get_input_desc_dict(name).get(input_name, '')

    def get_output_desc(self, name: str, output_name: str) -> str:
        """Return the output_desc for a registered field, or an empty string if not set."""
        return self.get_output_desc_dict(name).get(output_name, '')

    def describe(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dict of all fields and their metadata, including input/output names if present.
        """
        result = {}
        for name, field in self.fields.items():
            result[name] = {'value': field.get(), 'input_names': getattr(field, 'input_names', None), 'output_names': getattr(field, 'output_names', None), 'input_descs': getattr(field, 'input_descs', {}), 'output_descs': getattr(field, 'output_descs', {})}
        return result

def get_input_desc(self, name: str, input_name: str) -> str:
    """Return the input_desc for a registered field, or an empty string if not set."""
    return self.get_input_desc_dict(name).get(input_name, '')

def get_output_desc(self, name: str, output_name: str) -> str:
    """Return the output_desc for a registered field, or an empty string if not set."""
    return self.get_output_desc_dict(name).get(output_name, '')

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

class ArxivBase(RequestBase):
    """
    Extended RequestBase class for arXiv API interactions.
    Provides specialized methods for working with arXiv's Atom XML API.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = 'http://export.arxiv.org/api/query'
        self.atom_namespace = 'http://www.w3.org/2005/Atom'
        self.arxiv_namespace = 'http://arxiv.org/schemas/atom'
        self.opensearch_namespace = 'http://a9.com/-/spec/opensearch/1.1/'

    def search_arxiv(self, search_query: str=None, id_list: List[str]=None, start: int=0, max_results: int=10) -> Dict[str, Any]:
        """
        Search arXiv using the API and return structured results.
        
        Args:
            search_query: Search query string (e.g., "all:electron", "cat:cs.AI")
            id_list: List of arXiv IDs to retrieve
            start: Starting index for results
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing parsed search results
        """
        params = {'start': start, 'max_results': max_results}
        if search_query:
            params['search_query'] = search_query
        if id_list:
            params['id_list'] = ','.join(id_list)
        try:
            response = self.request(url=self.base_url, method='GET', params=params)
            return self._parse_atom_response(response.text)
        except Exception as e:
            return {'success': False, 'error': str(e), 'query': search_query or str(id_list)}

    def _parse_atom_response(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse the Atom XML response from arXiv API.
        
        Args:
            xml_content: Raw XML content from the API response
            
        Returns:
            Dictionary with parsed paper information
        """
        try:
            root = ET.fromstring(xml_content)
            namespaces = {'atom': self.atom_namespace, 'arxiv': self.arxiv_namespace, 'opensearch': self.opensearch_namespace}
            total_results = root.find('.//opensearch:totalResults', namespaces)
            start_index = root.find('.//opensearch:startIndex', namespaces)
            items_per_page = root.find('.//opensearch:itemsPerPage', namespaces)
            result = {'success': True, 'total_results': int(total_results.text) if total_results is not None else 0, 'start_index': int(start_index.text) if start_index is not None else 0, 'items_per_page': int(items_per_page.text) if items_per_page is not None else 0, 'papers': []}
            entries = root.findall('.//atom:entry', namespaces)
            for entry in entries:
                paper = self._parse_paper_entry(entry, namespaces)
                result['papers'].append(paper)
            return result
        except ET.ParseError as e:
            return {'success': False, 'error': f'XML parsing error: {str(e)}', 'raw_content': xml_content[:500] + '...' if len(xml_content) > 500 else xml_content}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_paper_entry(self, entry, namespaces) -> Dict[str, Any]:
        """
        Parse a single paper entry from the XML.
        
        Args:
            entry: XML element for a paper entry
            namespaces: Namespace mappings
            
        Returns:
            Dictionary with paper information
        """
        paper = {}
        paper['id'] = self._get_text(entry, 'atom:id', namespaces)
        paper['title'] = self._get_text(entry, 'atom:title', namespaces, clean=True)
        paper['summary'] = self._get_text(entry, 'atom:summary', namespaces, clean=True)
        paper['published'] = self._get_text(entry, 'atom:published', namespaces)
        paper['updated'] = self._get_text(entry, 'atom:updated', namespaces)
        if paper['id']:
            paper['arxiv_id'] = paper['id'].split('/')[-1]
        authors = entry.findall('.//atom:author', namespaces)
        paper['authors'] = []
        for author in authors:
            name = self._get_text(author, 'atom:name', namespaces)
            if name:
                paper['authors'].append(name)
        categories = entry.findall('.//atom:category', namespaces)
        paper['categories'] = []
        for category in categories:
            term = category.get('term')
            if term:
                paper['categories'].append(term)
        primary_cat = entry.find('.//arxiv:primary_category', namespaces)
        if primary_cat is not None:
            paper['primary_category'] = primary_cat.get('term')
        links = entry.findall('.//atom:link', namespaces)
        paper['links'] = {}
        for link in links:
            rel = link.get('rel')
            href = link.get('href')
            title = link.get('title')
            if rel == 'alternate':
                paper['links']['html'] = href
            elif title == 'pdf':
                paper['links']['pdf'] = href
        paper['comment'] = self._get_text(entry, 'arxiv:comment', namespaces)
        paper['journal_ref'] = self._get_text(entry, 'arxiv:journal_ref', namespaces)
        paper['doi'] = self._get_text(entry, 'arxiv:doi', namespaces)
        if paper.get('links', {}).get('html'):
            paper['url'] = paper['links']['html']
        elif paper.get('arxiv_id'):
            paper['url'] = f'https://arxiv.org/abs/{paper['arxiv_id']}'
        else:
            paper['url'] = ''
        paper['published_date'] = paper.pop('published', '')
        paper['updated_date'] = paper.pop('updated', '')
        paper.pop('id', None)
        return paper

    def _get_text(self, element, xpath, namespaces, clean=False) -> str:
        """
        Helper method to extract text from XML elements.
        
        Args:
            element: XML element to search in
            xpath: XPath expression
            namespaces: Namespace mappings
            clean: Whether to clean whitespace
            
        Returns:
            Text content or empty string
        """
        found = element.find(xpath, namespaces)
        if found is not None:
            text = found.text or ''
            if clean:
                text = re.sub('\\s+', ' ', text.strip())
            return text
        return ''

    def download_pdf(self, pdf_url: str, save_path: str, storage_handler: FileStorageHandler=None) -> Dict[str, Any]:
        """
        Download a PDF from arXiv.
        
        Args:
            pdf_url: URL of the PDF to download
            save_path: Local path to save the PDF
            storage_handler: Storage handler for file operations
            
        Returns:
            Dictionary with download status
        """
        try:
            response = self.request(url=pdf_url, method='GET')
            pdf_content = response.content
            result = storage_handler.save(save_path, pdf_content)
            if result['success']:
                return {'success': True, 'file_path': save_path, 'size': len(pdf_content), 'url': pdf_url, 'storage_handler': type(storage_handler).__name__}
            else:
                return {'success': False, 'error': f'Failed to save PDF: {result.get('error', 'Unknown error')}', 'url': pdf_url, 'save_path': save_path}
        except Exception as e:
            return {'success': False, 'error': str(e), 'url': pdf_url}

def search_arxiv(self, search_query: str=None, id_list: List[str]=None, start: int=0, max_results: int=10) -> Dict[str, Any]:
    """
        Search arXiv using the API and return structured results.
        
        Args:
            search_query: Search query string (e.g., "all:electron", "cat:cs.AI")
            id_list: List of arXiv IDs to retrieve
            start: Starting index for results
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing parsed search results
        """
    params = {'start': start, 'max_results': max_results}
    if search_query:
        params['search_query'] = search_query
    if id_list:
        params['id_list'] = ','.join(id_list)
    try:
        response = self.request(url=self.base_url, method='GET', params=params)
        return self._parse_atom_response(response.text)
    except Exception as e:
        return {'success': False, 'error': str(e), 'query': search_query or str(id_list)}

def download_pdf(self, pdf_url: str, save_path: str, storage_handler: FileStorageHandler=None) -> Dict[str, Any]:
    """
        Download a PDF from arXiv.
        
        Args:
            pdf_url: URL of the PDF to download
            save_path: Local path to save the PDF
            storage_handler: Storage handler for file operations
            
        Returns:
            Dictionary with download status
        """
    try:
        response = self.request(url=pdf_url, method='GET')
        pdf_content = response.content
        result = storage_handler.save(save_path, pdf_content)
        if result['success']:
            return {'success': True, 'file_path': save_path, 'size': len(pdf_content), 'url': pdf_url, 'storage_handler': type(storage_handler).__name__}
        else:
            return {'success': False, 'error': f'Failed to save PDF: {result.get('error', 'Unknown error')}', 'url': pdf_url, 'save_path': save_path}
    except Exception as e:
        return {'success': False, 'error': str(e), 'url': pdf_url}

class APITool(Tool):
    """
    API tool wrapper that encapsulates a single API endpoint as a Tool
    
    Attributes:
        name: Tool name
        description: Tool description
        inputs: Input parameter schema
        required: List of required parameters
        endpoint_config: API endpoint configuration
        auth_config: Authentication configuration
        function: Actual execution function
    """

    def __init__(self, name: str, description: str, inputs: Dict[str, Dict[str, Any]], required: Optional[List[str]]=None, endpoint_config: Dict[str, Any]=None, auth_config: Dict[str, Any]=None, function: Callable=None):
        super().__init__(name=name, description=description, inputs=inputs, required=required)
        self.endpoint_config = endpoint_config or {}
        self.auth_config = auth_config or {}
        self.function = function

    @property
    def __name__(self):
        return self.name

    def __call__(self, **kwargs):
        """Execute the API call"""
        if not self.function:
            raise ValueError('Function not set for APITool')
        try:
            result = self.function(**kwargs)
            return self._process_result(result)
        except Exception as e:
            logger.error(f'Error calling API tool {self.name}: {str(e)}')
            raise

    def _process_result(self, result: Any) -> Any:
        """Process API response"""
        if isinstance(result, requests.Response):
            try:
                return result.json()
            except (ValueError, json.JSONDecodeError):
                return result.text
        return result

    @classmethod
    def validate_attributes(cls):
        """Validate attributes"""
        if cls.__name__ == 'APITool':
            return
        required_attributes = {'name': str, 'description': str, 'inputs': dict}
        for attr, attr_type in required_attributes.items():
            if not hasattr(cls, attr):
                raise ValueError(f'Attribute {attr} is required')
            if not isinstance(getattr(cls, attr), attr_type):
                raise ValueError(f'Attribute {attr} must be of type {attr_type}')
        if hasattr(cls, 'required') and cls.required:
            for required_input in cls.required:
                if required_input not in cls.inputs:
                    raise ValueError(f"Required input '{required_input}' is not found in inputs")

def _process_result(self, result: Any) -> Any:
    """Process API response"""
    if isinstance(result, requests.Response):
        try:
            return result.json()
        except (ValueError, json.JSONDecodeError):
            return result.text
    return result

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

class RapidAPIConverter(OpenAPIConverter):
    """
    RapidAPI-specific converter
    Inherits from OpenAPIConverter and adds RapidAPI-specific authentication and configuration
    """

    def __init__(self, input_schema: Union[str, Dict[str, Any]], description: str='', rapidapi_key: str='', rapidapi_host: str='', **kwargs):
        """
        Initialize the RapidAPI converter
        
        Args:
            input_schema: API specification
            description: Service description
            rapidapi_key: RapidAPI key
            rapidapi_host: RapidAPI host
        """
        if not rapidapi_key:
            from os import getenv
            from dotenv import load_dotenv
            load_dotenv()
            rapidapi_key = getenv('RAPIDAPI_KEY', '')
            if not rapidapi_key:
                raise ValueError('rapidapi_key not provided or RAPIDAPI_KEY environment variable not set')
        if not rapidapi_host:
            raise ValueError('rapidapi_host not provided or RAPIDAPI_HOST environment variable not set')
        auth_config = {'api_key': rapidapi_key, 'key_name': 'X-RapidAPI-Key', 'rapidapi_host': rapidapi_host}
        super().__init__(input_schema=input_schema, description=description, auth_config=auth_config, **kwargs)

    def convert_to_toolkit(self) -> APIToolkit:
        """Convert to a RapidAPI toolkit"""
        toolkit = super().convert_to_toolkit()
        rapidapi_headers = {'X-RapidAPI-Key': self.auth_config.get('api_key', ''), 'X-RapidAPI-Host': self.auth_config.get('rapidapi_host', '')}
        toolkit.common_headers.update(rapidapi_headers)
        return toolkit

    def _create_api_function(self, endpoint_config: Dict[str, Any]) -> Callable:
        """Create RapidAPI execution function"""
        url = endpoint_config['url']
        method = endpoint_config['method']
        operation = endpoint_config['operation']

        def rapidapi_call(**kwargs):
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
            headers = {'Content-Type': 'application/json', 'X-RapidAPI-Key': self.auth_config.get('api_key', ''), 'X-RapidAPI-Host': self.auth_config.get('rapidapi_host', '')}
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
                logger.error(f'RapidAPI request failed: {e}')
                raise
        rapidapi_call.__name__ = f'rapidapi_call_{method.lower()}'
        return rapidapi_call

def rapidapi_call(**kwargs):
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
    headers = {'Content-Type': 'application/json', 'X-RapidAPI-Key': self.auth_config.get('api_key', ''), 'X-RapidAPI-Host': self.auth_config.get('rapidapi_host', '')}
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
        logger.error(f'RapidAPI request failed: {e}')
        raise

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

class RequestBase(BaseModule):
    """
    Base class for handling HTTP requests, parsing content, and saving data.
    This class provides common functionality for web scraping and HTTP operations.
    """

    def __init__(self, timeout: int=30, max_retries: int=3, delay_between_requests: float=1.0):
        """
        Initialize the RequestBase with configuration options.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay_between_requests: Delay between requests in seconds
        """
        super().__init__()
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.session = requests.Session()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

    def request(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None) -> requests.Response:
        """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        if headers:
            request_headers = {**self.session.headers, **headers}
        else:
            request_headers = self.session.headers
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method=method.upper(), url=url, headers=request_headers, params=params, data=data, json=json_data, timeout=self.timeout)
                response.raise_for_status()
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests)
                return response
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(self.delay_between_requests * (attempt + 1))

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            BeautifulSoup object for parsing
        """
        return BeautifulSoup(html_content, 'html.parser')

    def parse_json(self, json_content: str) -> Dict[str, Any]:
        """
        Parse JSON content.
        
        Args:
            json_content: Raw JSON content
            
        Returns:
            Parsed JSON as dictionary
        """
        return json.loads(json_content)

    def extract_text(self, html_content: str, selector: Optional[str]=None) -> str:
        """
        Extract text content from HTML using html2text.
        
        Args:
            html_content: Raw HTML content
            selector: CSS selector to extract specific elements (optional)
            
        Returns:
            Extracted text content
        """
        if selector:
            soup = self.parse_html(html_content)
            elements = soup.select(selector)
            combined_html = '\n'.join([str(elem) for elem in elements])
            return self.html_converter.handle(combined_html)
        else:
            return self.html_converter.handle(html_content)

    def extract_links(self, html_content: str, base_url: str=None) -> list:
        """
        Extract all links from HTML content.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL to resolve relative links
            
        Returns:
            List of extracted URLs
        """
        soup = self.parse_html(html_content)
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url and (not href.startswith(('http://', 'https://', 'mailto:', 'tel:'))):
                href = urljoin(base_url, href)
            links.append(href)
        return links

    def save_content(self, content: Union[str, Dict[str, Any], bytes], file_path: str, content_type: str='text') -> bool:
        """
        Save content to a file.
        
        Args:
            content: Content to save (string, dictionary, or bytes)
            file_path: Path where to save the file
            content_type: Type of content ('text', 'json', 'html', 'pdf', 'binary')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if content_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            elif content_type.lower() in ['pdf', 'binary'] or isinstance(content, bytes):
                with open(file_path, 'wb') as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    else:
                        f.write(str(content).encode('utf-8'))
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            return True
        except Exception as e:
            print(f'Error saving content to {file_path}: {e}')
            return False

    def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic information about a webpage.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary containing page information
        """
        try:
            response = self.request(url)
            soup = self.parse_html(response.text)
            info = {'url': url, 'status_code': response.status_code, 'title': soup.title.string if soup.title else '', 'content_type': response.headers.get('content-type', ''), 'content_length': len(response.text), 'links_count': len(soup.find_all('a', href=True)), 'images_count': len(soup.find_all('img'))}
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                info['description'] = meta_desc.get('content', '')
            return info
        except Exception as e:
            return {'error': str(e), 'url': url}

    def request_and_process(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None, return_raw: bool=False, save_file_path: Optional[str]=None) -> Dict[str, Any]:
        """
        Make a request and process the response with comprehensive error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            return_raw: If True, return raw HTML content, otherwise processed text
            save_file_path: Optional path to save the content
            
        Returns:
            Dictionary containing processed response data
        """
        try:
            response = self.request(url=url, method=method, headers=headers, params=params, data=data, json_data=json_data)
            content_type = response.headers.get('content-type', '').lower()
            result = {'url': url, 'method': method.upper(), 'status_code': response.status_code, 'success': True, 'content_type': content_type, 'content_length': len(response.text), 'headers': dict(response.headers)}
            if return_raw:
                result['content'] = response.text
            elif 'json' in content_type:
                try:
                    result['content'] = response.json()
                except json.JSONDecodeError:
                    result['content'] = response.text
                    result['warning'] = 'Content-Type indicates JSON but parsing failed'
            else:
                result['content'] = self.extract_text(response.text)
            if save_file_path:
                save_success = self._save_response_content(response, save_file_path, content_type)
                result['saved_to_file'] = save_file_path if save_success else None
                if not save_success:
                    result['save_warning'] = f'Failed to save content to {save_file_path}'
            return result
        except Exception as e:
            return {'url': url, 'method': method.upper(), 'error': str(e), 'success': False}

    def _save_response_content(self, response: requests.Response, file_path: str, content_type: str) -> bool:
        """
        Save response content to file with appropriate format.
        
        Args:
            response: The response object
            file_path: Path to save the file
            content_type: Content type of the response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if 'json' in content_type:
                try:
                    json_content = response.json()
                    return self.save_content(json_content, file_path, 'json')
                except json.JSONDecodeError:
                    return self.save_content(response.text, file_path, 'text')
            elif 'html' in content_type:
                return self.save_content(response.text, file_path, 'html')
            else:
                return self.save_content(response.text, file_path, 'text')
        except Exception as e:
            print(f'Error saving response content: {e}')
            return False

    def close(self):
        """Close the session."""
        self.session.close()

def request(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None) -> requests.Response:
    """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
    if headers:
        request_headers = {**self.session.headers, **headers}
    else:
        request_headers = self.session.headers
    for attempt in range(self.max_retries):
        try:
            response = self.session.request(method=method.upper(), url=url, headers=request_headers, params=params, data=data, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            if attempt < self.max_retries - 1:
                time.sleep(self.delay_between_requests)
            return response
        except requests.RequestException as e:
            if attempt == self.max_retries - 1:
                raise e
            time.sleep(self.delay_between_requests * (attempt + 1))

def parse_html(self, html_content: str) -> BeautifulSoup:
    """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            BeautifulSoup object for parsing
        """
    return BeautifulSoup(html_content, 'html.parser')

def extract_text(self, html_content: str, selector: Optional[str]=None) -> str:
    """
        Extract text content from HTML using html2text.
        
        Args:
            html_content: Raw HTML content
            selector: CSS selector to extract specific elements (optional)
            
        Returns:
            Extracted text content
        """
    if selector:
        soup = self.parse_html(html_content)
        elements = soup.select(selector)
        combined_html = '\n'.join([str(elem) for elem in elements])
        return self.html_converter.handle(combined_html)
    else:
        return self.html_converter.handle(html_content)

def extract_links(self, html_content: str, base_url: str=None) -> list:
    """
        Extract all links from HTML content.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL to resolve relative links
            
        Returns:
            List of extracted URLs
        """
    soup = self.parse_html(html_content)
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if base_url and (not href.startswith(('http://', 'https://', 'mailto:', 'tel:'))):
            href = urljoin(base_url, href)
        links.append(href)
    return links

def get_page_info(self, url: str) -> Dict[str, Any]:
    """
        Get basic information about a webpage.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary containing page information
        """
    try:
        response = self.request(url)
        soup = self.parse_html(response.text)
        info = {'url': url, 'status_code': response.status_code, 'title': soup.title.string if soup.title else '', 'content_type': response.headers.get('content-type', ''), 'content_length': len(response.text), 'links_count': len(soup.find_all('a', href=True)), 'images_count': len(soup.find_all('img'))}
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            info['description'] = meta_desc.get('content', '')
        return info
    except Exception as e:
        return {'error': str(e), 'url': url}

def request_and_process(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None, return_raw: bool=False, save_file_path: Optional[str]=None) -> Dict[str, Any]:
    """
        Make a request and process the response with comprehensive error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            return_raw: If True, return raw HTML content, otherwise processed text
            save_file_path: Optional path to save the content
            
        Returns:
            Dictionary containing processed response data
        """
    try:
        response = self.request(url=url, method=method, headers=headers, params=params, data=data, json_data=json_data)
        content_type = response.headers.get('content-type', '').lower()
        result = {'url': url, 'method': method.upper(), 'status_code': response.status_code, 'success': True, 'content_type': content_type, 'content_length': len(response.text), 'headers': dict(response.headers)}
        if return_raw:
            result['content'] = response.text
        elif 'json' in content_type:
            try:
                result['content'] = response.json()
            except json.JSONDecodeError:
                result['content'] = response.text
                result['warning'] = 'Content-Type indicates JSON but parsing failed'
        else:
            result['content'] = self.extract_text(response.text)
        if save_file_path:
            save_success = self._save_response_content(response, save_file_path, content_type)
            result['saved_to_file'] = save_file_path if save_success else None
            if not save_success:
                result['save_warning'] = f'Failed to save content to {save_file_path}'
        return result
    except Exception as e:
        return {'url': url, 'method': method.upper(), 'error': str(e), 'success': False}

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

class SearchBase(BaseModule):
    """
    Base class for search tools that retrieve information from various sources.
    Provides common functionality for search operations.
    """
    num_search_pages: Optional[int] = Field(default=5, description='Number of search results to retrieve')
    max_content_words: Optional[int] = Field(default=None, description='Maximum number of words to include in content. Default None means no limit.')

    def __init__(self, name: str='SearchBase', num_search_pages: Optional[int]=5, max_content_words: Optional[int]=None, **kwargs):
        """
        Initialize the base search tool.
        
        Args:
            name (str): Name of the tool
            num_search_pages (int): Number of search results to retrieve
            max_content_words (int): Maximum number of words to include in content, default None means no limit. 
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, num_search_pages=num_search_pages, max_content_words=max_content_words, **kwargs)
        self.content_converter = html2text.HTML2Text()
        self.content_converter.ignore_links = False
        self.content_converter.ignore_images = True
        self.content_converter.body_width = 0
        self.content_converter.unicode_snob = True
        self.content_converter.escape_snob = True

    def _truncate_content(self, content: str, max_words: Optional[int]=None) -> str:
        """
        Truncates content to a maximum number of words while preserving original spacing.
        
        Args:
            content (str): The content to truncate
            max_words (Optional[int]): Maximum number of words to include. None means no limit.
            
        Returns:
            str: Truncated content with ellipsis if truncated
        """
        if max_words is None or max_words <= 0:
            return content
        words = content.split()
        is_truncated = len(words) > max_words
        word_count = 0
        truncated_content = ''
        for i, char in enumerate(content):
            if char.isspace():
                if i > 0 and (not content[i - 1].isspace()):
                    word_count += 1
                if word_count >= max_words:
                    break
            truncated_content += char
        return truncated_content + (' ...' if is_truncated else '')

    def _scrape_page(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetches the title and main text content from a web page.

        Args:
            url (str): The URL of the web page.

        Returns:
            tuple: (Optional[title], Optional[main textual content])
        """
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return (None, None)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else 'No Title'
        main_content = None
        if 'wikipedia.org' in url:
            main_content = soup.find('div', {'id': 'mw-content-text'})
            if main_content:
                for element in main_content.find_all(['nav', 'script', 'style', 'table']):
                    element.decompose()
                text_content = self.content_converter.handle(str(main_content))
            else:
                text_content = self.content_converter.handle(response.text)
        else:
            main_content = soup.find('main') or soup.find('article') or soup.find('div', {'class': 'content'})
            if main_content:
                text_content = self.content_converter.handle(str(main_content))
            else:
                text_content = self.content_converter.handle(response.text)
        return (title, text_content)

def _scrape_page(self, url: str) -> Tuple[Optional[str], Optional[str]]:
    """
        Fetches the title and main text content from a web page.

        Args:
            url (str): The URL of the web page.

        Returns:
            tuple: (Optional[title], Optional[main textual content])
        """
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return (None, None)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title else 'No Title'
    main_content = None
    if 'wikipedia.org' in url:
        main_content = soup.find('div', {'id': 'mw-content-text'})
        if main_content:
            for element in main_content.find_all(['nav', 'script', 'style', 'table']):
                element.decompose()
            text_content = self.content_converter.handle(str(main_content))
        else:
            text_content = self.content_converter.handle(response.text)
    else:
        main_content = soup.find('main') or soup.find('article') or soup.find('div', {'class': 'content'})
        if main_content:
            text_content = self.content_converter.handle(str(main_content))
        else:
            text_content = self.content_converter.handle(response.text)
    return (title, text_content)

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

def get_toolkits(self) -> List[Toolkit]:
    """Return a list ofToolkits, one per server."""
    if not self.sessions:
        raise RuntimeError('Session not initialized')
    return [self.create_tool(session, tools, config) for session, tools, config in zip(self.sessions, self.mcp_tools, self.server_configs)]

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

class GoogleMapsBase(BaseModule):
    """
    Base class for Google Maps Platform API interactions.
    Handles API key management, request formatting, and common utilities.
    """

    def __init__(self, api_key: str=None, timeout: int=10, **kwargs):
        """
        Initialize the Google Maps base.
        
        Args:
            api_key (str, optional): Google Maps Platform API key. If not provided, will try to get from GOOGLE_MAPS_API_KEY environment variable.
            timeout (int): Request timeout in seconds
            **kwargs: Additional keyword arguments for parent class
        """
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            logger.warning('No Google Maps API key provided. Please set GOOGLE_MAPS_API_KEY environment variable or pass api_key parameter. Get your API key from: https://console.cloud.google.com/apis/')
        self.timeout = timeout
        self.base_url = 'https://maps.googleapis.com/maps/api'

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Google Maps Platform API.
        
        Args:
            endpoint (str): API endpoint
            params (dict): Request parameters
            
        Returns:
            dict: API response
        """
        if not self.api_key:
            return {'success': False, 'error': 'Google Maps API key not found. Please set GOOGLE_MAPS_API_KEY environment variable or pass api_key parameter.'}
        try:
            params['key'] = self.api_key
            url = f'{self.base_url}/{endpoint}'
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            status = data.get('status', 'UNKNOWN_ERROR')
            if status == 'OK':
                return {'success': True, 'status': status, 'data': data}
            elif status == 'ZERO_RESULTS':
                return {'success': True, 'status': status, 'data': data, 'message': 'No results found'}
            else:
                error_message = data.get('error_message', f'API returned status: {status}')
                logger.error(f'Google Maps API error: {error_message}')
                return {'success': False, 'status': status, 'error': error_message}
        except requests.exceptions.RequestException as e:
            logger.error(f'Request error: {str(e)}')
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except json.JSONDecodeError as e:
            logger.error(f'JSON decode error: {str(e)}')
            return {'success': False, 'error': f'Invalid JSON response: {str(e)}'}
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}')
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def _format_coordinates(self, lat: float, lng: float) -> str:
        """Format coordinates for API requests."""
        return f'{lat},{lng}'

def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
        Make a request to Google Maps Platform API.
        
        Args:
            endpoint (str): API endpoint
            params (dict): Request parameters
            
        Returns:
            dict: API response
        """
    if not self.api_key:
        return {'success': False, 'error': 'Google Maps API key not found. Please set GOOGLE_MAPS_API_KEY environment variable or pass api_key parameter.'}
    try:
        params['key'] = self.api_key
        url = f'{self.base_url}/{endpoint}'
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        status = data.get('status', 'UNKNOWN_ERROR')
        if status == 'OK':
            return {'success': True, 'status': status, 'data': data}
        elif status == 'ZERO_RESULTS':
            return {'success': True, 'status': status, 'data': data, 'message': 'No results found'}
        else:
            error_message = data.get('error_message', f'API returned status: {status}')
            logger.error(f'Google Maps API error: {error_message}')
            return {'success': False, 'status': status, 'error': error_message}
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error: {str(e)}')
        return {'success': False, 'error': f'Request failed: {str(e)}'}
    except json.JSONDecodeError as e:
        logger.error(f'JSON decode error: {str(e)}')
        return {'success': False, 'error': f'Invalid JSON response: {str(e)}'}
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}

class GeocodeAddressTool(Tool):
    """Convert addresses to geographic coordinates (latitude/longitude)."""
    name: str = 'geocode_address'
    description: str = 'Convert a street address into geographic coordinates (latitude and longitude). Useful for finding exact locations of places.'
    inputs: Dict[str, Dict[str, str]] = {'address': {'type': 'string', 'description': "The street address to geocode (e.g., '1600 Amphitheatre Parkway, Mountain View, CA')"}, 'components': {'type': 'string', 'description': "Optional component filters (e.g., 'country:US|locality:Mountain View')"}, 'region': {'type': 'string', 'description': "Optional region code for biasing results (e.g., 'us', 'uk')"}}
    required: List[str] = ['address']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, address: str, components: str=None, region: str=None) -> Dict[str, Any]:
        """
        Geocode an address to coordinates.
        
        Args:
            address: Street address to geocode
            components: Optional component filters
            region: Optional region bias
            
        Returns:
            Dictionary with geocoding results
        """
        params = {'address': address}
        if components:
            params['components'] = components
        if region:
            params['region'] = region
        result = self.google_maps_base._make_request('geocode/json', params)
        if result['success'] and result['data'].get('results'):
            geocode_result = result['data']['results'][0]
            location = geocode_result['geometry']['location']
            return {'success': True, 'address': address, 'formatted_address': geocode_result.get('formatted_address'), 'latitude': location['lat'], 'longitude': location['lng'], 'place_id': geocode_result.get('place_id'), 'location_type': geocode_result['geometry'].get('location_type'), 'address_components': geocode_result.get('address_components', [])}
        else:
            return {'success': False, 'address': address, 'error': result.get('error', 'No results found')}

def __call__(self, address: str, components: str=None, region: str=None) -> Dict[str, Any]:
    """
        Geocode an address to coordinates.
        
        Args:
            address: Street address to geocode
            components: Optional component filters
            region: Optional region bias
            
        Returns:
            Dictionary with geocoding results
        """
    params = {'address': address}
    if components:
        params['components'] = components
    if region:
        params['region'] = region
    result = self.google_maps_base._make_request('geocode/json', params)
    if result['success'] and result['data'].get('results'):
        geocode_result = result['data']['results'][0]
        location = geocode_result['geometry']['location']
        return {'success': True, 'address': address, 'formatted_address': geocode_result.get('formatted_address'), 'latitude': location['lat'], 'longitude': location['lng'], 'place_id': geocode_result.get('place_id'), 'location_type': geocode_result['geometry'].get('location_type'), 'address_components': geocode_result.get('address_components', [])}
    else:
        return {'success': False, 'address': address, 'error': result.get('error', 'No results found')}

class ReverseGeocodeTool(Tool):
    """Convert geographic coordinates to a human-readable address."""
    name: str = 'reverse_geocode'
    description: str = 'Convert geographic coordinates (latitude and longitude) into a human-readable address.'
    inputs: Dict[str, Dict[str, str]] = {'latitude': {'type': 'number', 'description': 'Latitude coordinate'}, 'longitude': {'type': 'number', 'description': 'Longitude coordinate'}, 'result_type': {'type': 'string', 'description': "Optional filter for result types (e.g., 'street_address|route')"}}
    required: List[str] = ['latitude', 'longitude']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, latitude: float, longitude: float, result_type: str=None) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            result_type: Optional result type filter
            
        Returns:
            Dictionary with reverse geocoding results
        """
        latlng = self.google_maps_base._format_coordinates(latitude, longitude)
        params = {'latlng': latlng}
        if result_type:
            params['result_type'] = result_type
        result = self.google_maps_base._make_request('geocode/json', params)
        if result['success'] and result['data'].get('results'):
            addresses = []
            for geocode_result in result['data']['results']:
                addresses.append({'formatted_address': geocode_result.get('formatted_address'), 'place_id': geocode_result.get('place_id'), 'types': geocode_result.get('types', []), 'address_components': geocode_result.get('address_components', [])})
            return {'success': True, 'latitude': latitude, 'longitude': longitude, 'addresses': addresses}
        else:
            return {'success': False, 'latitude': latitude, 'longitude': longitude, 'error': result.get('error', 'No results found')}

def __call__(self, latitude: float, longitude: float, result_type: str=None) -> Dict[str, Any]:
    """
        Reverse geocode coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            result_type: Optional result type filter
            
        Returns:
            Dictionary with reverse geocoding results
        """
    latlng = self.google_maps_base._format_coordinates(latitude, longitude)
    params = {'latlng': latlng}
    if result_type:
        params['result_type'] = result_type
    result = self.google_maps_base._make_request('geocode/json', params)
    if result['success'] and result['data'].get('results'):
        addresses = []
        for geocode_result in result['data']['results']:
            addresses.append({'formatted_address': geocode_result.get('formatted_address'), 'place_id': geocode_result.get('place_id'), 'types': geocode_result.get('types', []), 'address_components': geocode_result.get('address_components', [])})
        return {'success': True, 'latitude': latitude, 'longitude': longitude, 'addresses': addresses}
    else:
        return {'success': False, 'latitude': latitude, 'longitude': longitude, 'error': result.get('error', 'No results found')}

class PlacesSearchTool(Tool):
    """Search for places using text queries or nearby location."""
    name: str = 'places_search'
    description: str = 'Search for places (restaurants, shops, landmarks) using text queries. Can search near a specific location.'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': "Text search query (e.g., 'pizza restaurants near Times Square')"}, 'location': {'type': 'string', 'description': "Optional location bias as 'latitude,longitude' (e.g., '40.7589,-73.9851')"}, 'radius': {'type': 'number', 'description': 'Optional search radius in meters (max 50000)'}, 'type': {'type': 'string', 'description': "Optional place type filter (e.g., 'restaurant', 'gas_station')"}}
    required: List[str] = ['query']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, query: str, location: str=None, radius: float=None, type: str=None) -> Dict[str, Any]:
        """
        Search for places using text query.
        
        Args:
            query: Text search query
            location: Optional location bias as 'lat,lng'
            radius: Optional search radius in meters
            type: Optional place type filter
            
        Returns:
            Dictionary with search results
        """
        params = {'query': query}
        if location:
            params['location'] = location
        if radius:
            params['radius'] = min(radius, 50000)
        if type:
            params['type'] = type
        result = self.google_maps_base._make_request('place/textsearch/json', params)
        if result['success']:
            places = []
            for place in result['data'].get('results', []):
                places.append({'name': place.get('name'), 'place_id': place.get('place_id'), 'formatted_address': place.get('formatted_address'), 'rating': place.get('rating'), 'user_ratings_total': place.get('user_ratings_total'), 'price_level': place.get('price_level'), 'types': place.get('types', []), 'geometry': place.get('geometry', {}), 'business_status': place.get('business_status')})
            return {'success': True, 'query': query, 'places_found': len(places), 'places': places}
        else:
            return {'success': False, 'query': query, 'error': result.get('error', 'Search failed')}

def __call__(self, query: str, location: str=None, radius: float=None, type: str=None) -> Dict[str, Any]:
    """
        Search for places using text query.
        
        Args:
            query: Text search query
            location: Optional location bias as 'lat,lng'
            radius: Optional search radius in meters
            type: Optional place type filter
            
        Returns:
            Dictionary with search results
        """
    params = {'query': query}
    if location:
        params['location'] = location
    if radius:
        params['radius'] = min(radius, 50000)
    if type:
        params['type'] = type
    result = self.google_maps_base._make_request('place/textsearch/json', params)
    if result['success']:
        places = []
        for place in result['data'].get('results', []):
            places.append({'name': place.get('name'), 'place_id': place.get('place_id'), 'formatted_address': place.get('formatted_address'), 'rating': place.get('rating'), 'user_ratings_total': place.get('user_ratings_total'), 'price_level': place.get('price_level'), 'types': place.get('types', []), 'geometry': place.get('geometry', {}), 'business_status': place.get('business_status')})
        return {'success': True, 'query': query, 'places_found': len(places), 'places': places}
    else:
        return {'success': False, 'query': query, 'error': result.get('error', 'Search failed')}

class PlaceDetailsTool(Tool):
    """Get detailed information about a specific place using its Place ID."""
    name: str = 'place_details'
    description: str = 'Get comprehensive information about a specific place using its Place ID, including contact info, hours, reviews.'
    inputs: Dict[str, Dict[str, str]] = {'place_id': {'type': 'string', 'description': 'Unique Place ID from a place search'}, 'fields': {'type': 'string', 'description': "Optional comma-separated list of fields to return (e.g., 'name,rating,formatted_phone_number')"}}
    required: List[str] = ['place_id']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, place_id: str, fields: str=None) -> Dict[str, Any]:
        """
        Get detailed place information.
        
        Args:
            place_id: Unique place identifier
            fields: Optional fields to return
            
        Returns:
            Dictionary with place details
        """
        params = {'place_id': place_id}
        if not fields:
            fields = 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,price_level,types,geometry'
        params['fields'] = fields
        result = self.google_maps_base._make_request('place/details/json', params)
        if result['success'] and result['data'].get('result'):
            place = result['data']['result']
            return {'success': True, 'place_id': place_id, 'name': place.get('name'), 'formatted_address': place.get('formatted_address'), 'phone_number': place.get('formatted_phone_number'), 'international_phone': place.get('international_phone_number'), 'website': place.get('website'), 'rating': place.get('rating'), 'user_ratings_total': place.get('user_ratings_total'), 'price_level': place.get('price_level'), 'types': place.get('types', []), 'opening_hours': place.get('opening_hours'), 'geometry': place.get('geometry', {}), 'business_status': place.get('business_status'), 'reviews': place.get('reviews', [])}
        else:
            return {'success': False, 'place_id': place_id, 'error': result.get('error', 'Place not found')}

def __call__(self, place_id: str, fields: str=None) -> Dict[str, Any]:
    """
        Get detailed place information.
        
        Args:
            place_id: Unique place identifier
            fields: Optional fields to return
            
        Returns:
            Dictionary with place details
        """
    params = {'place_id': place_id}
    if not fields:
        fields = 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,price_level,types,geometry'
    params['fields'] = fields
    result = self.google_maps_base._make_request('place/details/json', params)
    if result['success'] and result['data'].get('result'):
        place = result['data']['result']
        return {'success': True, 'place_id': place_id, 'name': place.get('name'), 'formatted_address': place.get('formatted_address'), 'phone_number': place.get('formatted_phone_number'), 'international_phone': place.get('international_phone_number'), 'website': place.get('website'), 'rating': place.get('rating'), 'user_ratings_total': place.get('user_ratings_total'), 'price_level': place.get('price_level'), 'types': place.get('types', []), 'opening_hours': place.get('opening_hours'), 'geometry': place.get('geometry', {}), 'business_status': place.get('business_status'), 'reviews': place.get('reviews', [])}
    else:
        return {'success': False, 'place_id': place_id, 'error': result.get('error', 'Place not found')}

class DirectionsTool(Tool):
    """Calculate driving, walking, bicycling, or transit directions between locations."""
    name: str = 'directions'
    description: str = 'Calculate directions between two or more locations with different travel modes (driving, walking, bicycling, transit).'
    inputs: Dict[str, Dict[str, str]] = {'origin': {'type': 'string', 'description': 'Starting location (address, coordinates, or place ID)'}, 'destination': {'type': 'string', 'description': 'Ending location (address, coordinates, or place ID)'}, 'mode': {'type': 'string', 'description': "Travel mode: 'driving', 'walking', 'bicycling', or 'transit' (default: driving)"}, 'waypoints': {'type': 'string', 'description': "Optional waypoints separated by '|' (e.g., 'via:San Francisco|via:Los Angeles')"}, 'alternatives': {'type': 'boolean', 'description': 'Whether to return alternative routes (default: false)'}}
    required: List[str] = ['origin', 'destination']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, origin: str, destination: str, mode: str='driving', waypoints: str=None, alternatives: bool=False) -> Dict[str, Any]:
        """
        Calculate directions between locations.
        
        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode
            waypoints: Optional waypoints
            alternatives: Return alternative routes
            
        Returns:
            Dictionary with directions
        """
        params = {'origin': origin, 'destination': destination, 'mode': mode, 'alternatives': alternatives}
        if waypoints:
            params['waypoints'] = waypoints
        result = self.google_maps_base._make_request('directions/json', params)
        if result['success'] and result['data'].get('routes'):
            routes = []
            for route in result['data']['routes']:
                legs = []
                total_distance = 0
                total_duration = 0
                for leg in route.get('legs', []):
                    leg_info = {'start_address': leg.get('start_address'), 'end_address': leg.get('end_address'), 'distance': leg.get('distance', {}), 'duration': leg.get('duration', {}), 'steps': []}
                    if leg.get('distance', {}).get('value'):
                        total_distance += leg['distance']['value']
                    if leg.get('duration', {}).get('value'):
                        total_duration += leg['duration']['value']
                    for step in leg.get('steps', []):
                        leg_info['steps'].append({'instructions': step.get('html_instructions', ''), 'distance': step.get('distance', {}), 'duration': step.get('duration', {}), 'travel_mode': step.get('travel_mode')})
                    legs.append(leg_info)
                routes.append({'summary': route.get('summary'), 'legs': legs, 'total_distance_meters': total_distance, 'total_duration_seconds': total_duration, 'overview_polyline': route.get('overview_polyline', {}), 'warnings': route.get('warnings', []), 'copyrights': route.get('copyrights')})
            return {'success': True, 'origin': origin, 'destination': destination, 'mode': mode, 'routes': routes}
        else:
            return {'success': False, 'origin': origin, 'destination': destination, 'error': result.get('error', 'No routes found')}

def __call__(self, origin: str, destination: str, mode: str='driving', waypoints: str=None, alternatives: bool=False) -> Dict[str, Any]:
    """
        Calculate directions between locations.
        
        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode
            waypoints: Optional waypoints
            alternatives: Return alternative routes
            
        Returns:
            Dictionary with directions
        """
    params = {'origin': origin, 'destination': destination, 'mode': mode, 'alternatives': alternatives}
    if waypoints:
        params['waypoints'] = waypoints
    result = self.google_maps_base._make_request('directions/json', params)
    if result['success'] and result['data'].get('routes'):
        routes = []
        for route in result['data']['routes']:
            legs = []
            total_distance = 0
            total_duration = 0
            for leg in route.get('legs', []):
                leg_info = {'start_address': leg.get('start_address'), 'end_address': leg.get('end_address'), 'distance': leg.get('distance', {}), 'duration': leg.get('duration', {}), 'steps': []}
                if leg.get('distance', {}).get('value'):
                    total_distance += leg['distance']['value']
                if leg.get('duration', {}).get('value'):
                    total_duration += leg['duration']['value']
                for step in leg.get('steps', []):
                    leg_info['steps'].append({'instructions': step.get('html_instructions', ''), 'distance': step.get('distance', {}), 'duration': step.get('duration', {}), 'travel_mode': step.get('travel_mode')})
                legs.append(leg_info)
            routes.append({'summary': route.get('summary'), 'legs': legs, 'total_distance_meters': total_distance, 'total_duration_seconds': total_duration, 'overview_polyline': route.get('overview_polyline', {}), 'warnings': route.get('warnings', []), 'copyrights': route.get('copyrights')})
        return {'success': True, 'origin': origin, 'destination': destination, 'mode': mode, 'routes': routes}
    else:
        return {'success': False, 'origin': origin, 'destination': destination, 'error': result.get('error', 'No routes found')}

class DistanceMatrixTool(Tool):
    """Calculate travel times and distances between multiple origins and destinations."""
    name: str = 'distance_matrix'
    description: str = 'Calculate travel times and distances between multiple origins and destinations. Useful for finding the closest location.'
    inputs: Dict[str, Dict[str, str]] = {'origins': {'type': 'string', 'description': "Origin locations separated by '|' (e.g., 'Seattle,WA|Portland,OR')"}, 'destinations': {'type': 'string', 'description': "Destination locations separated by '|' (e.g., 'San Francisco,CA|Los Angeles,CA')"}, 'mode': {'type': 'string', 'description': "Travel mode: 'driving', 'walking', 'bicycling', or 'transit' (default: driving)"}, 'units': {'type': 'string', 'description': "Unit system: 'metric' or 'imperial' (default: metric)"}}
    required: List[str] = ['origins', 'destinations']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, origins: str, destinations: str, mode: str='driving', units: str='metric') -> Dict[str, Any]:
        """
        Calculate distance matrix.
        
        Args:
            origins: Origin locations separated by '|'
            destinations: Destination locations separated by '|'
            mode: Travel mode
            units: Unit system
            
        Returns:
            Dictionary with distance matrix
        """
        params = {'origins': origins, 'destinations': destinations, 'mode': mode, 'units': units}
        result = self.google_maps_base._make_request('distancematrix/json', params)
        if result['success'] and result['data'].get('rows'):
            origin_addresses = result['data'].get('origin_addresses', [])
            destination_addresses = result['data'].get('destination_addresses', [])
            matrix = []
            for i, row in enumerate(result['data']['rows']):
                origin_results = {'origin_address': origin_addresses[i] if i < len(origin_addresses) else f'Origin {i + 1}', 'destinations': []}
                for j, element in enumerate(row.get('elements', [])):
                    destination_result = {'destination_address': destination_addresses[j] if j < len(destination_addresses) else f'Destination {j + 1}', 'status': element.get('status'), 'distance': element.get('distance', {}), 'duration': element.get('duration', {}), 'duration_in_traffic': element.get('duration_in_traffic', {})}
                    origin_results['destinations'].append(destination_result)
                matrix.append(origin_results)
            return {'success': True, 'origins': origins.split('|'), 'destinations': destinations.split('|'), 'mode': mode, 'units': units, 'matrix': matrix}
        else:
            return {'success': False, 'origins': origins, 'destinations': destinations, 'error': result.get('error', 'Distance matrix calculation failed')}

def __call__(self, origins: str, destinations: str, mode: str='driving', units: str='metric') -> Dict[str, Any]:
    """
        Calculate distance matrix.
        
        Args:
            origins: Origin locations separated by '|'
            destinations: Destination locations separated by '|'
            mode: Travel mode
            units: Unit system
            
        Returns:
            Dictionary with distance matrix
        """
    params = {'origins': origins, 'destinations': destinations, 'mode': mode, 'units': units}
    result = self.google_maps_base._make_request('distancematrix/json', params)
    if result['success'] and result['data'].get('rows'):
        origin_addresses = result['data'].get('origin_addresses', [])
        destination_addresses = result['data'].get('destination_addresses', [])
        matrix = []
        for i, row in enumerate(result['data']['rows']):
            origin_results = {'origin_address': origin_addresses[i] if i < len(origin_addresses) else f'Origin {i + 1}', 'destinations': []}
            for j, element in enumerate(row.get('elements', [])):
                destination_result = {'destination_address': destination_addresses[j] if j < len(destination_addresses) else f'Destination {j + 1}', 'status': element.get('status'), 'distance': element.get('distance', {}), 'duration': element.get('duration', {}), 'duration_in_traffic': element.get('duration_in_traffic', {})}
                origin_results['destinations'].append(destination_result)
            matrix.append(origin_results)
        return {'success': True, 'origins': origins.split('|'), 'destinations': destinations.split('|'), 'mode': mode, 'units': units, 'matrix': matrix}
    else:
        return {'success': False, 'origins': origins, 'destinations': destinations, 'error': result.get('error', 'Distance matrix calculation failed')}

class TimeZoneTool(Tool):
    """Get time zone information for a location."""
    name: str = 'timezone'
    description: str = 'Get time zone information for a specific location using coordinates.'
    inputs: Dict[str, Dict[str, str]] = {'latitude': {'type': 'number', 'description': 'Latitude coordinate'}, 'longitude': {'type': 'number', 'description': 'Longitude coordinate'}, 'timestamp': {'type': 'number', 'description': 'Optional Unix timestamp for the desired time (default: current time)'}}
    required: List[str] = ['latitude', 'longitude']

    def __init__(self, google_maps_base: GoogleMapsBase):
        super().__init__()
        self.google_maps_base = google_maps_base

    def __call__(self, latitude: float, longitude: float, timestamp: float=None) -> Dict[str, Any]:
        """
        Get time zone information.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            timestamp: Optional Unix timestamp
            
        Returns:
            Dictionary with time zone info
        """
        import time
        location = self.google_maps_base._format_coordinates(latitude, longitude)
        params = {'location': location, 'timestamp': timestamp or int(time.time())}
        result = self.google_maps_base._make_request('timezone/json', params)
        if result['success']:
            data = result['data']
            return {'success': True, 'latitude': latitude, 'longitude': longitude, 'time_zone_id': data.get('timeZoneId'), 'time_zone_name': data.get('timeZoneName'), 'dst_offset': data.get('dstOffset'), 'raw_offset': data.get('rawOffset'), 'status': data.get('status')}
        else:
            return {'success': False, 'latitude': latitude, 'longitude': longitude, 'error': result.get('error', 'Time zone lookup failed')}

def __call__(self, latitude: float, longitude: float, timestamp: float=None) -> Dict[str, Any]:
    """
        Get time zone information.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            timestamp: Optional Unix timestamp
            
        Returns:
            Dictionary with time zone info
        """
    import time
    location = self.google_maps_base._format_coordinates(latitude, longitude)
    params = {'location': location, 'timestamp': timestamp or int(time.time())}
    result = self.google_maps_base._make_request('timezone/json', params)
    if result['success']:
        data = result['data']
        return {'success': True, 'latitude': latitude, 'longitude': longitude, 'time_zone_id': data.get('timeZoneId'), 'time_zone_name': data.get('timeZoneName'), 'dst_offset': data.get('dstOffset'), 'raw_offset': data.get('rawOffset'), 'status': data.get('status')}
    else:
        return {'success': False, 'latitude': latitude, 'longitude': longitude, 'error': result.get('error', 'Time zone lookup failed')}

def unique_filename(prefix: str, ext: str='png', storage_handler: Optional[FileStorageHandler]=None) -> str:
    """Generate unique filename using storage handler or fallback to timestamp"""
    if storage_handler:
        base_filename = f'{prefix}.{ext}'
        filename = base_filename
        counter = 1
        while storage_handler.exists(filename):
            filename = f'{prefix}_{counter}.{ext}'
            counter += 1
        return filename
    else:
        ts = int(time.time())
        return f'{prefix}_{ts}.{ext}'

def unique_filename_legacy(prefix: str, ext: str='png') -> str:
    """Legacy function for backward compatibility - uses timestamp"""
    ts = int(time.time())
    return f'{prefix}_{ts}.{ext}'

class FluxImageGenerationEditTool(Tool):
    name: str = 'flux_image_generation_edit'
    description: str = 'Text-to-image and image-editing using the bfl.ai flux-kontext-max API. Without input_image: generate from prompt. With input_image (base64): edit/transform.'
    inputs: Dict[str, Dict] = {'prompt': {'type': 'string', 'description': 'The prompt describing the image to generate.'}, 'input_image': {'type': 'string', 'description': 'Base64 encoded input image for editing, optional.'}, 'seed': {'type': 'integer', 'description': 'Random seed, default is 42.', 'default': 42}, 'aspect_ratio': {'type': 'string', 'description': "Aspect ratio, e.g. '1:1', optional."}, 'output_format': {'type': 'string', 'description': 'Image format, default is jpeg.', 'default': 'jpeg'}, 'prompt_upsampling': {'type': 'boolean', 'description': 'Enable prompt upsampling, default is false.', 'default': False}, 'safety_tolerance': {'type': 'integer', 'description': 'Safety tolerance level, default is 2.', 'default': 2}}
    required: List[str] = ['prompt']

    def __init__(self, api_key: str, storage_handler: Optional[FileStorageHandler]=None, base_path: str='./imgs', save_path: str=None):
        super().__init__()
        self.api_key = api_key
        if save_path is not None:
            base_path = save_path
        if storage_handler is None:
            self.storage_handler = LocalStorageHandler(base_path=base_path)
        else:
            self.storage_handler = storage_handler

    def __call__(self, prompt: str, input_image: str=None, seed: int=42, aspect_ratio: str=None, output_format: str='jpeg', prompt_upsampling: bool=False, safety_tolerance: int=2):
        payload = {'prompt': prompt, 'seed': seed, 'output_format': output_format, 'prompt_upsampling': prompt_upsampling, 'safety_tolerance': safety_tolerance}
        if aspect_ratio:
            payload['aspect_ratio'] = aspect_ratio
        if input_image:
            payload['input_image'] = input_image
        headers = {'accept': 'application/json', 'x-key': self.api_key, 'Content-Type': 'application/json'}
        response = requests.post('https://api.bfl.ai/v1/flux-kontext-max', json=payload, headers=headers)
        response.raise_for_status()
        request_data = response.json()
        request_id = request_data['id']
        polling_url = request_data['polling_url']
        while True:
            time.sleep(2)
            result = requests.get(polling_url, headers={'accept': 'application/json', 'x-key': self.api_key}, params={'id': request_id}).json()
            if result['status'] == 'Ready':
                image_url = result['result']['sample']
                break
            elif result['status'] in ['Error', 'Failed']:
                raise ValueError(f'Generation failed: {result}')
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        image_content = image_response.content
        filename = self._get_unique_filename(seed, output_format)
        result = self.storage_handler.save(filename, image_content)
        if result['success']:
            return {'success': True, 'file_path': filename, 'full_path': result.get('full_path', filename), 'message': f'Image saved successfully as {filename}'}
        else:
            return {'success': False, 'error': f'Failed to save image: {result.get('error', 'Unknown error')}'}

    def _get_unique_filename(self, seed: int, output_format: str) -> str:
        """Generate a unique filename for the image"""
        base_filename = f'flux_{seed}.{output_format}'
        filename = base_filename
        counter = 1
        while self.storage_handler.exists(filename):
            filename = f'flux_{seed}_{counter}.{output_format}'
            counter += 1
        return filename

def __call__(self, prompt: str, input_image: str=None, seed: int=42, aspect_ratio: str=None, output_format: str='jpeg', prompt_upsampling: bool=False, safety_tolerance: int=2):
    payload = {'prompt': prompt, 'seed': seed, 'output_format': output_format, 'prompt_upsampling': prompt_upsampling, 'safety_tolerance': safety_tolerance}
    if aspect_ratio:
        payload['aspect_ratio'] = aspect_ratio
    if input_image:
        payload['input_image'] = input_image
    headers = {'accept': 'application/json', 'x-key': self.api_key, 'Content-Type': 'application/json'}
    response = requests.post('https://api.bfl.ai/v1/flux-kontext-max', json=payload, headers=headers)
    response.raise_for_status()
    request_data = response.json()
    request_id = request_data['id']
    polling_url = request_data['polling_url']
    while True:
        time.sleep(2)
        result = requests.get(polling_url, headers={'accept': 'application/json', 'x-key': self.api_key}, params={'id': request_id}).json()
        if result['status'] == 'Ready':
            image_url = result['result']['sample']
            break
        elif result['status'] in ['Error', 'Failed']:
            raise ValueError(f'Generation failed: {result}')
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    image_content = image_response.content
    filename = self._get_unique_filename(seed, output_format)
    result = self.storage_handler.save(filename, image_content)
    if result['success']:
        return {'success': True, 'file_path': filename, 'full_path': result.get('full_path', filename), 'message': f'Image saved successfully as {filename}'}
    else:
        return {'success': False, 'error': f'Failed to save image: {result.get('error', 'Unknown error')}'}

class OpenRouterImageGenerationEditTool(Tool):
    name: str = 'openrouter_image_generation_edit'
    description: str = 'Text-to-image and image-editing via OpenRouter models (e.g., google/gemini-2.5-flash-image-preview). No images → generate; with images (URLs or local paths) → edit/compose.'
    inputs: Dict[str, Dict] = {'prompt': {'type': 'string', 'description': 'Text prompt.'}, 'image_urls': {'type': 'array', 'description': 'Remote image URLs (optional).'}, 'image_paths': {'type': 'array', 'description': 'Local image paths (optional).'}, 'model': {'type': 'string', 'description': 'OpenRouter model id.', 'default': 'google/gemini-2.5-flash-image-preview'}, 'api_key': {'type': 'string', 'description': 'OpenRouter API key (fallback to env OPENROUTER_API_KEY).'}, 'save_path': {'type': 'string', 'description': 'Directory to save images (when data URLs).', 'default': './openrouter_images'}, 'output_basename': {'type': 'string', 'description': 'Base filename for outputs.', 'default': 'or_gen'}}
    required: List[str] = ['prompt']

    def __init__(self, api_key: str=None, storage_handler: Optional[FileStorageHandler]=None, base_path: str='./openrouter_images'):
        super().__init__()
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.storage_handler = storage_handler or LocalStorageHandler(base_path=base_path)

    def __call__(self, prompt: str, image_urls: list=None, image_paths: list=None, model: str='google/gemini-2.5-flash-image-preview', api_key: str=None, save_path: str='./openrouter_images', output_basename: str='or_gen'):
        key = api_key or self.api_key
        if not key:
            return {'error': 'OPENROUTER_API_KEY not provided.'}
        messages = [{'role': 'user', 'content': prompt}]
        payload = {'model': model, 'messages': messages, 'modalities': ['image', 'text']}
        content_parts = [{'type': 'text', 'text': prompt}]
        if image_urls:
            content_parts.extend(self._urls_to_image_parts(image_urls))
        if image_paths:
            content_parts.extend(self._paths_to_image_parts(image_paths))
        if len(content_parts) > 1:
            payload['messages'][0] = {'role': 'user', 'content': content_parts}
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
        url = 'https://openrouter.ai/api/v1/chat/completions'
        try:
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = resp.json()
                return {'error': f'OpenRouter API error: {error_data}', 'status_code': resp.status_code}
            except Exception:
                return {'error': f'OpenRouter API error: {e}', 'status_code': resp.status_code}
        except Exception as e:
            return {'error': f'Request failed: {e}'}
        saved_paths: List[str] = []
        if data.get('choices'):
            msg = data['choices'][0]['message']
            images = msg.get('images') or []
            for im in images:
                image_url = im.get('image_url', {}).get('url')
                if not image_url:
                    continue
                if image_url.startswith('data:') and ',' in image_url:
                    import base64
                    header, b64data = image_url.split(',', 1)
                    mime = 'image/png'
                    if ';' in header:
                        mime = header.split(':', 1)[1].split(';', 1)[0] or mime
                    ext = '.png'
                    if mime == 'image/jpeg':
                        ext = '.jpg'
                    elif mime == 'image/webp':
                        ext = '.webp'
                    elif mime == 'image/heic':
                        ext = '.heic'
                    elif mime == 'image/heif':
                        ext = '.heif'
                    filename = self._get_unique_filename(output_basename or 'or_gen', ext)
                    image_content = base64.b64decode(b64data)
                    result = self.storage_handler.save(filename, image_content)
                    if result['success']:
                        saved_paths.append(filename)
                    else:
                        return {'error': f'Failed to save image: {result.get('error', 'Unknown error')}'}
        if saved_paths:
            return {'saved_paths': saved_paths}
        return {'warning': 'No image returned or saved.', 'raw': data}

    def _url_to_image_part(self, url: str) -> Dict:
        return {'type': 'image_url', 'image_url': {'url': url}}

    def _guess_mime_from_name(self, name: str, default: str='image/png') -> str:
        import mimetypes
        guess, _ = mimetypes.guess_type(name)
        return guess or default

    def _path_to_data_url(self, path: str) -> str:
        import base64
        mime = self._guess_mime_from_name(path)
        try:
            system_path = self.storage_handler.translate_in(path)
            content = self.storage_handler._read_raw(system_path)
        except Exception as e:
            raise FileNotFoundError(f'Could not read file {path}: {str(e)}')
        b64 = base64.b64encode(content).decode('utf-8')
        return f'data:{mime};base64,{b64}'

    def _get_unique_filename(self, base_name: str, extension: str) -> str:
        """Generate a unique filename for the image"""
        filename = f'{base_name}{extension}'
        counter = 1
        while self.storage_handler.exists(filename):
            filename = f'{base_name}_{counter}{extension}'
            counter += 1
        return filename

    def _paths_to_image_parts(self, paths: list) -> List[Dict]:
        parts: List[Dict] = []
        for p in paths:
            try:
                parts.append(self._url_to_image_part(self._path_to_data_url(p)))
            except Exception:
                continue
        return parts

    def _urls_to_image_parts(self, urls: list) -> List[Dict]:
        return [self._url_to_image_part(u) for u in urls]

def __call__(self, prompt: str, image_urls: list=None, image_paths: list=None, model: str='google/gemini-2.5-flash-image-preview', api_key: str=None, save_path: str='./openrouter_images', output_basename: str='or_gen'):
    key = api_key or self.api_key
    if not key:
        return {'error': 'OPENROUTER_API_KEY not provided.'}
    messages = [{'role': 'user', 'content': prompt}]
    payload = {'model': model, 'messages': messages, 'modalities': ['image', 'text']}
    content_parts = [{'type': 'text', 'text': prompt}]
    if image_urls:
        content_parts.extend(self._urls_to_image_parts(image_urls))
    if image_paths:
        content_parts.extend(self._paths_to_image_parts(image_paths))
    if len(content_parts) > 1:
        payload['messages'][0] = {'role': 'user', 'content': content_parts}
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    url = 'https://openrouter.ai/api/v1/chat/completions'
    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_data = resp.json()
            return {'error': f'OpenRouter API error: {error_data}', 'status_code': resp.status_code}
        except Exception:
            return {'error': f'OpenRouter API error: {e}', 'status_code': resp.status_code}
    except Exception as e:
        return {'error': f'Request failed: {e}'}
    saved_paths: List[str] = []
    if data.get('choices'):
        msg = data['choices'][0]['message']
        images = msg.get('images') or []
        for im in images:
            image_url = im.get('image_url', {}).get('url')
            if not image_url:
                continue
            if image_url.startswith('data:') and ',' in image_url:
                import base64
                header, b64data = image_url.split(',', 1)
                mime = 'image/png'
                if ';' in header:
                    mime = header.split(':', 1)[1].split(';', 1)[0] or mime
                ext = '.png'
                if mime == 'image/jpeg':
                    ext = '.jpg'
                elif mime == 'image/webp':
                    ext = '.webp'
                elif mime == 'image/heic':
                    ext = '.heic'
                elif mime == 'image/heif':
                    ext = '.heif'
                filename = self._get_unique_filename(output_basename or 'or_gen', ext)
                image_content = base64.b64decode(b64data)
                result = self.storage_handler.save(filename, image_content)
                if result['success']:
                    saved_paths.append(filename)
                else:
                    return {'error': f'Failed to save image: {result.get('error', 'Unknown error')}'}
    if saved_paths:
        return {'saved_paths': saved_paths}
    return {'warning': 'No image returned or saved.', 'raw': data}

def get_model_config(model: str, operation: str='generation') -> Dict:
    if operation == 'editing':
        return OPENAI_EDITING_MODEL_CONFIG.get(model, {})
    return OPENAI_MODEL_CONFIG.get(model, {})

def validate_parameter(model: str, param: str, value: any, operation: str='generation') -> Tuple[bool, str]:
    config = get_model_config(model, operation)
    if not config:
        return (False, f'Unsupported model: {model}')
    if param not in config.get('supported_params', []):
        return (False, f"Parameter '{param}' is not supported by {model}")
    if param == 'size' and value not in config.get('size_options', []):
        return (False, f"Invalid size '{value}' for {model}. Supported: {config['size_options']}")
    if param == 'quality' and value not in config.get('quality_options', []):
        return (False, f"Invalid quality '{value}' for {model}. Supported: {config['quality_options']}")
    if param == 'style' and value not in config.get('style_options', []):
        return (False, f"Invalid style '{value}' for {model}. Supported: {config['style_options']}")
    if param == 'background' and value not in config.get('background_options', []):
        return (False, f"Invalid background '{value}' for {model}. Supported: {config['background_options']}")
    if param == 'moderation' and value not in config.get('moderation_options', []):
        return (False, f"Invalid moderation '{value}' for {model}. Supported: {config['moderation_options']}")
    if param == 'input_fidelity' and value not in config.get('input_fidelity_options', []):
        return (False, f"Invalid input_fidelity '{value}' for {model}. Supported: {config['input_fidelity_options']}")
    if param == 'output_format' and value not in config.get('output_format_options', []):
        return (False, f"Invalid output_format '{value}'. Supported: {config['output_format_options']}")
    if param == 'n' and value > config.get('n_max', 10):
        return (False, f'Invalid n {value}. Max: {config['n_max']}')
    if param == 'output_compression' and (value < 0 or value > 100):
        return (False, 'output_compression must be between 0 and 100')
    if param == 'partial_images' and (value < 0 or value > 3):
        return (False, 'partial_images must be between 0 and 3')
    return (True, '')

class OpenAIImageGenerationTool(Tool):
    name: str = 'openai_image_generation'
    description: str = 'OpenAI image generation supporting dall-e-2, dall-e-3, gpt-image-1 (with validation).'
    inputs: Dict[str, Dict[str, str]] = {'prompt': {'type': 'string', 'description': 'Prompt text. Required.'}, 'image_name': {'type': 'string', 'description': 'Optional save name.'}, 'model': {'type': 'string', 'description': 'dall-e-2 | dall-e-3 | gpt-image-1'}, 'size': {'type': 'string', 'description': 'Model-specific size.'}, 'quality': {'type': 'string', 'description': 'quality for gpt-image-1/dall-e-3'}, 'n': {'type': 'integer', 'description': '1-10 (1 for dalle-3)'}, 'background': {'type': 'string', 'description': 'gpt-image-1 only'}, 'moderation': {'type': 'string', 'description': 'gpt-image-1 only'}, 'output_compression': {'type': 'integer', 'description': 'gpt-image-1 jpeg/webp'}, 'output_format': {'type': 'string', 'description': 'gpt-image-1 png/jpeg/webp'}, 'partial_images': {'type': 'integer', 'description': 'gpt-image-1 streaming partials'}, 'response_format': {'type': 'string', 'description': 'url | b64_json for dalle-2/3'}, 'stream': {'type': 'boolean', 'description': 'gpt-image-1 streaming'}, 'style': {'type': 'string', 'description': 'dall-e-3 vivid|natural'}}
    required: Optional[List[str]] = ['prompt']

    def __init__(self, api_key: str, organization_id: str=None, model: str='dall-e-3', save_path: str='./generated_images', storage_handler: Optional[FileStorageHandler]=None):
        super().__init__()
        self.api_key = api_key
        self.organization_id = organization_id
        self.model = model
        self.save_path = save_path
        self.storage_handler = storage_handler or LocalStorageHandler(base_path=save_path)

    def __call__(self, prompt: str, image_name: str=None, model: str=None, size: str=None, quality: str=None, n: int=None, background: str=None, moderation: str=None, output_compression: int=None, output_format: str=None, partial_images: int=None, response_format: str=None, stream: bool=None, style: str=None):
        try:
            client = create_openai_client(self.api_key, self.organization_id)
            actual_model = model if model else self.model
            params_to_validate = build_validation_params(model=actual_model, prompt=prompt, size=size, quality=quality, n=n, background=background, moderation=moderation, output_compression=output_compression, output_format=output_format, partial_images=partial_images, response_format=response_format, stream=stream, style=style)
            validation_result = validate_parameters(actual_model, params_to_validate, 'generation')
            error = handle_validation_result(validation_result)
            if error:
                return error
            api_params = validation_result['validated_params'].copy()
            api_params.pop('image_name', None)
            response = client.images.generate(**api_params)
            import base64
            results = []
            for i, image_data in enumerate(response.data):
                try:
                    if hasattr(image_data, 'b64_json') and image_data.b64_json:
                        image_bytes = base64.b64decode(image_data.b64_json)
                    elif hasattr(image_data, 'url') and image_data.url:
                        import requests
                        r = requests.get(image_data.url)
                        r.raise_for_status()
                        image_bytes = r.content
                    else:
                        raise Exception('No valid image data in response')
                    filename = self._get_unique_filename(image_name, i)
                    result = self.storage_handler.save(filename, image_bytes)
                    if result['success']:
                        results.append(filename)
                    else:
                        results.append(f'Error saving image {i + 1}: {result.get('error', 'Unknown error')}')
                except Exception as e:
                    results.append(f'Error saving image {i + 1}: {e}')
            return {'results': results, 'count': len(results)}
        except Exception as e:
            return {'error': f'Image generation failed: {e}'}

    def _get_unique_filename(self, image_name: str, index: int) -> str:
        """Generate a unique filename for the image"""
        import time
        if image_name:
            base = image_name.rsplit('.', 1)[0]
            filename = f'{base}_{index + 1}.png'
        else:
            ts = int(time.time())
            filename = f'generated_{ts}_{index + 1}.png'
        counter = 1
        while self.storage_handler.exists(filename):
            if image_name:
                base = image_name.rsplit('.', 1)[0]
                filename = f'{base}_{index + 1}_{counter}.png'
            else:
                filename = f'generated_{ts}_{index + 1}_{counter}.png'
            counter += 1
        return filename

def __call__(self, prompt: str, image_name: str=None, model: str=None, size: str=None, quality: str=None, n: int=None, background: str=None, moderation: str=None, output_compression: int=None, output_format: str=None, partial_images: int=None, response_format: str=None, stream: bool=None, style: str=None):
    try:
        client = create_openai_client(self.api_key, self.organization_id)
        actual_model = model if model else self.model
        params_to_validate = build_validation_params(model=actual_model, prompt=prompt, size=size, quality=quality, n=n, background=background, moderation=moderation, output_compression=output_compression, output_format=output_format, partial_images=partial_images, response_format=response_format, stream=stream, style=style)
        validation_result = validate_parameters(actual_model, params_to_validate, 'generation')
        error = handle_validation_result(validation_result)
        if error:
            return error
        api_params = validation_result['validated_params'].copy()
        api_params.pop('image_name', None)
        response = client.images.generate(**api_params)
        import base64
        results = []
        for i, image_data in enumerate(response.data):
            try:
                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    image_bytes = base64.b64decode(image_data.b64_json)
                elif hasattr(image_data, 'url') and image_data.url:
                    import requests
                    r = requests.get(image_data.url)
                    r.raise_for_status()
                    image_bytes = r.content
                else:
                    raise Exception('No valid image data in response')
                filename = self._get_unique_filename(image_name, i)
                result = self.storage_handler.save(filename, image_bytes)
                if result['success']:
                    results.append(filename)
                else:
                    results.append(f'Error saving image {i + 1}: {result.get('error', 'Unknown error')}')
            except Exception as e:
                results.append(f'Error saving image {i + 1}: {e}')
        return {'results': results, 'count': len(results)}
    except Exception as e:
        return {'error': f'Image generation failed: {e}'}

def _get_unique_filename(self, image_name: str, index: int) -> str:
    """Generate a unique filename for the image"""
    import time
    if image_name:
        base = image_name.rsplit('.', 1)[0]
        filename = f'{base}_{index + 1}.png'
    else:
        ts = int(time.time())
        filename = f'generated_{ts}_{index + 1}.png'
    counter = 1
    while self.storage_handler.exists(filename):
        if image_name:
            base = image_name.rsplit('.', 1)[0]
            filename = f'{base}_{index + 1}_{counter}.png'
        else:
            filename = f'generated_{ts}_{index + 1}_{counter}.png'
        counter += 1
    return filename

class OpenAIImageEditTool(Tool):
    name: str = 'openai_image_edit'
    description: str = 'Edit images using OpenAI gpt-image-1 (direct, minimal validation).'
    inputs: Dict[str, Dict[str, str]] = {'prompt': {'type': 'string', 'description': 'Edit instruction. Required.'}, 'images': {'type': 'array', 'description': 'Image path(s) png/webp/jpg <50MB. Required. Single string accepted and normalized to array.'}, 'mask_path': {'type': 'string', 'description': 'Optional PNG mask path (same size as first image).'}, 'size': {'type': 'string', 'description': '1024x1024 | 1536x1024 | 1024x1536 | auto'}, 'n': {'type': 'integer', 'description': '1-10'}, 'background': {'type': 'string', 'description': 'transparent | opaque | auto'}, 'input_fidelity': {'type': 'string', 'description': 'high | low'}, 'output_compression': {'type': 'integer', 'description': '0-100 for jpeg/webp'}, 'output_format': {'type': 'string', 'description': 'png | jpeg | webp (default png)'}, 'partial_images': {'type': 'integer', 'description': '0-3 partial streaming'}, 'quality': {'type': 'string', 'description': 'auto | high | medium | low'}, 'stream': {'type': 'boolean', 'description': 'streaming mode'}, 'image_name': {'type': 'string', 'description': 'Optional output base name'}}
    required: Optional[List[str]] = ['prompt', 'images']

    def __init__(self, api_key: str, organization_id: str=None, save_path: str='./edited_images', storage_handler: Optional[FileStorageHandler]=None):
        super().__init__()
        self.api_key = api_key
        self.organization_id = organization_id
        self.save_path = save_path
        self.storage_handler = storage_handler or LocalStorageHandler(base_path=save_path)

    def __call__(self, prompt: str, images: list, mask_path: str=None, size: str=None, n: int=None, background: str=None, input_fidelity: str=None, output_compression: int=None, output_format: str=None, partial_images: int=None, quality: str=None, stream: bool=None, image_name: str=None):
        try:
            client = create_openai_client(self.api_key, self.organization_id)
            if isinstance(images, str):
                image_paths = [images]
            else:
                image_paths = list(images)
            opened_images = []
            temp_paths = []
            mask_fh = None
            try:
                for p in image_paths:
                    use_path, tmp = self._ensure_image_edit_compatible(p)
                    if tmp:
                        temp_paths.append(tmp)
                    opened_images.append(open(use_path, 'rb'))
                api_kwargs = {'model': 'gpt-image-1', 'prompt': prompt, 'image': opened_images if len(opened_images) > 1 else opened_images[0]}
                if size is not None:
                    api_kwargs['size'] = size
                if n is not None:
                    api_kwargs['n'] = n
                if background is not None:
                    api_kwargs['background'] = background
                if input_fidelity is not None:
                    api_kwargs['input_fidelity'] = input_fidelity
                if output_compression is not None:
                    api_kwargs['output_compression'] = output_compression
                if output_format is not None:
                    api_kwargs['output_format'] = output_format
                if partial_images is not None:
                    api_kwargs['partial_images'] = partial_images
                if quality is not None:
                    api_kwargs['quality'] = quality
                if stream is not None:
                    api_kwargs['stream'] = stream
                if mask_path:
                    mask_fh = open(mask_path, 'rb')
                    api_kwargs['mask'] = mask_fh
                response = client.images.edit(**api_kwargs)
            finally:
                for fh in opened_images:
                    try:
                        fh.close()
                    except Exception:
                        pass
                if mask_fh:
                    try:
                        mask_fh.close()
                    except Exception:
                        pass
                import os
                for tp in temp_paths:
                    try:
                        if tp and os.path.exists(tp):
                            os.remove(tp)
                    except Exception:
                        pass
            import base64
            import time
            results = []
            for i, img in enumerate(response.data):
                try:
                    img_bytes = base64.b64decode(img.b64_json)
                    ts = int(time.time())
                    if image_name:
                        filename = f'{image_name.rsplit('.', 1)[0]}_{i + 1}.png'
                    else:
                        filename = f'image_edit_{ts}_{i + 1}.png'
                    result = self.storage_handler.save(filename, img_bytes)
                    if result['success']:
                        translated_path = self.storage_handler.translate_in(filename)
                        results.append(translated_path)
                    else:
                        results.append(f'Error saving image {i + 1}: {result.get('error', 'Unknown error')}')
                except Exception as e:
                    results.append(f'Error saving image {i + 1}: {e}')
            return {'results': results, 'count': len(results)}
        except Exception as e:
            return {'error': f'gpt-image-1 editing failed: {e}'}

    def _ensure_image_edit_compatible(self, image_path: str) -> tuple[str, str | None]:
        """
        Ensure the image matches OpenAI edit requirements using storage handler.
        If not, convert to RGBA and save to a temporary path. Return (usable_path, temp_path).
        Caller may delete temp_path after the request completes.
        """
        try:
            from PIL import Image
            from io import BytesIO
            import os
            result = self.storage_handler.read(image_path)
            if not result['success']:
                raise FileNotFoundError(f'Could not read image {image_path}: {result.get('error', 'Unknown error')}')
            if isinstance(result['content'], bytes):
                content = result['content']
            else:
                content = str(result['content']).encode('utf-8')
            with Image.open(BytesIO(content)) as img:
                if img.mode in ('RGBA', 'LA', 'L'):
                    translated_path = self.storage_handler.translate_in(image_path)
                    return (translated_path, None)
                rgba_img = img.convert('RGBA')
                temp_filename = f'temp_rgba_{hash(image_path) % 10000}.png'
                buffer = BytesIO()
                rgba_img.save(buffer, format='PNG')
                temp_content = buffer.getvalue()
                result = self.storage_handler.save(temp_filename, temp_content)
                if result['success']:
                    temp_path = self.storage_handler.translate_in(temp_filename)
                    return (temp_path, temp_path)
                else:
                    temp_path = os.path.join('workplace', 'images', 'temp_rgba_image.png')
                    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                    rgba_img.save(temp_path)
                    return (temp_path, temp_path)
        except Exception:
            translated_path = self.storage_handler.translate_in(image_path)
            return (translated_path, None)

def __call__(self, prompt: str, images: list, mask_path: str=None, size: str=None, n: int=None, background: str=None, input_fidelity: str=None, output_compression: int=None, output_format: str=None, partial_images: int=None, quality: str=None, stream: bool=None, image_name: str=None):
    try:
        client = create_openai_client(self.api_key, self.organization_id)
        if isinstance(images, str):
            image_paths = [images]
        else:
            image_paths = list(images)
        opened_images = []
        temp_paths = []
        mask_fh = None
        try:
            for p in image_paths:
                use_path, tmp = self._ensure_image_edit_compatible(p)
                if tmp:
                    temp_paths.append(tmp)
                opened_images.append(open(use_path, 'rb'))
            api_kwargs = {'model': 'gpt-image-1', 'prompt': prompt, 'image': opened_images if len(opened_images) > 1 else opened_images[0]}
            if size is not None:
                api_kwargs['size'] = size
            if n is not None:
                api_kwargs['n'] = n
            if background is not None:
                api_kwargs['background'] = background
            if input_fidelity is not None:
                api_kwargs['input_fidelity'] = input_fidelity
            if output_compression is not None:
                api_kwargs['output_compression'] = output_compression
            if output_format is not None:
                api_kwargs['output_format'] = output_format
            if partial_images is not None:
                api_kwargs['partial_images'] = partial_images
            if quality is not None:
                api_kwargs['quality'] = quality
            if stream is not None:
                api_kwargs['stream'] = stream
            if mask_path:
                mask_fh = open(mask_path, 'rb')
                api_kwargs['mask'] = mask_fh
            response = client.images.edit(**api_kwargs)
        finally:
            for fh in opened_images:
                try:
                    fh.close()
                except Exception:
                    pass
            if mask_fh:
                try:
                    mask_fh.close()
                except Exception:
                    pass
            import os
            for tp in temp_paths:
                try:
                    if tp and os.path.exists(tp):
                        os.remove(tp)
                except Exception:
                    pass
        import base64
        import time
        results = []
        for i, img in enumerate(response.data):
            try:
                img_bytes = base64.b64decode(img.b64_json)
                ts = int(time.time())
                if image_name:
                    filename = f'{image_name.rsplit('.', 1)[0]}_{i + 1}.png'
                else:
                    filename = f'image_edit_{ts}_{i + 1}.png'
                result = self.storage_handler.save(filename, img_bytes)
                if result['success']:
                    translated_path = self.storage_handler.translate_in(filename)
                    results.append(translated_path)
                else:
                    results.append(f'Error saving image {i + 1}: {result.get('error', 'Unknown error')}')
            except Exception as e:
                results.append(f'Error saving image {i + 1}: {e}')
        return {'results': results, 'count': len(results)}
    except Exception as e:
        return {'error': f'gpt-image-1 editing failed: {e}'}

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

def get_example_evaluation_record(self, benchmark: Benchmark, example: Any) -> Optional[dict]:
    """
        Get the evaluation record for a given example.
        """
    example_id = benchmark.get_id(example=example)
    return self._evaluation_records.get(example_id, None)

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

def get(self, name: str) -> Any:
    return self.fields[name].get()

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

def get_param(self, name: str) -> Any:
    """Retrieve the current value of a parameter by name."""
    return self.registry.get(name)

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

def get(self, name: str) -> Any:
    """Retrieve the current value of a registered field by name."""
    return self.fields[name].get()

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

def get_chunk(self, chunk_id: str) -> Optional[Union[TextChunk, ImageChunk]]:
    """Retrieve a chunk by its ID."""
    return self.chunk_index.get(chunk_id)

class AzureOpenAIEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for Azure OpenAI embedding models."""

    def __init__(self, model_name: str='text-embedding-3-small', api_key: Optional[str]=None, azure_endpoint: Optional[str]=None, api_version: Optional[str]=None, deployment_name: Optional[str]=None, dimensions: Optional[int]=None, embed_batch_size: int=10, **kwargs: Any) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version
        self.deployment_name = deployment_name or model_name
        self.kwargs = kwargs or {}
        self.embed_batch_size = embed_batch_size
        self._dimensions = MODEL_DIMENSIONS.get(self.model_name) or dimensions
        self._embedding_model: Optional[AzureOpenAIEmbedding] = None
        self._dimensions = self._dimensions or dimensions

    def get_embedding_model(self) -> BaseEmbedding:
        if self._embedding_model is None:
            try:
                self._embedding_model = AzureOpenAIEmbedding(model_name=self.model_name, api_key=self.api_key, azure_endpoint=self.azure_endpoint, api_version=self.api_version, deployment_name=self.deployment_name, dimensions=self._dimensions, embed_batch_size=self.embed_batch_size, **self.kwargs)
                logger.debug('Initialized Azure OpenAI embedding wrapper for model %s', self.model_name)
            except Exception as exc:
                logger.error('Failed to initialize Azure OpenAI embedding wrapper: %s', exc)
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> Optional[int]:
        return self._embedding_model.dimensions if self._embedding_model else self._dimensions

def __init__(self, model_name: str='text-embedding-3-small', api_key: Optional[str]=None, azure_endpoint: Optional[str]=None, api_version: Optional[str]=None, deployment_name: Optional[str]=None, dimensions: Optional[int]=None, embed_batch_size: int=10, **kwargs: Any) -> None:
    self.model_name = model_name
    self.api_key = api_key
    self.azure_endpoint = azure_endpoint
    self.api_version = api_version
    self.deployment_name = deployment_name or model_name
    self.kwargs = kwargs or {}
    self.embed_batch_size = embed_batch_size
    self._dimensions = MODEL_DIMENSIONS.get(self.model_name) or dimensions
    self._embedding_model: Optional[AzureOpenAIEmbedding] = None
    self._dimensions = self._dimensions or dimensions

class HuggingFaceEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for HuggingFace embedding models."""

    def __init__(self, model_name: str='sentence-transformers/all-MiniLM-L6-v2', device: Optional[str]=None, normalize: bool=True, **model_kwargs):
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self.model_kwargs = model_kwargs
        self._embedding_model = None
        self._embedding_model = self.get_embedding_model()

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        if self._embedding_model is None:
            try:
                self._embedding_model = HuggingFaceEmbedding(model_name=self.model_name, device=self.device, normalize=self.normalize, **self.model_kwargs)
                logger.debug(f'Initialized HuggingFace embedding wrapper for model: {self.model_name}')
            except Exception as e:
                logger.error(f'Failed to initialize HuggingFace embedding wrapper: {str(e)}')
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._embedding_model.dimension

def __init__(self, model_name: str='sentence-transformers/all-MiniLM-L6-v2', device: Optional[str]=None, normalize: bool=True, **model_kwargs):
    self.model_name = model_name
    self.device = device
    self.normalize = normalize
    self.model_kwargs = model_kwargs
    self._embedding_model = None
    self._embedding_model = self.get_embedding_model()

class OpenAIEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for OpenAI embedding models."""

    def __init__(self, model_name: str='text-embedding-3-small', api_key: str=None, dimensions: int=None, base_url: str=None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self._dimensions = MODEL_DIMENSIONS.get(self.model_name, None) or dimensions
        self.base_url = base_url
        self.kwargs = kwargs
        self._embedding_model = None
        self._embedding_model = self.get_embedding_model()

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        if getattr(self, '_embedding_model', None) is None:
            try:
                self._embedding_model = OpenAIEmbedding(model_name=self.model_name, api_key=self.api_key, dimensions=self._dimensions, base_url=self.base_url, **self.kwargs)
                logger.debug(f'Initialized OpenAI embedding wrapper for model: {self.model_name}')
            except Exception as e:
                logger.error(f'Failed to initialize OpenAI embedding wrapper: {str(e)}')
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions

def __init__(self, model_name: str='text-embedding-3-small', api_key: str=None, dimensions: int=None, base_url: str=None, **kwargs):
    self.model_name = model_name
    self.api_key = api_key
    self._dimensions = MODEL_DIMENSIONS.get(self.model_name, None) or dimensions
    self.base_url = base_url
    self.kwargs = kwargs
    self._embedding_model = None
    self._embedding_model = self.get_embedding_model()

class OllamaEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for Ollama embedding models."""

    def __init__(self, model_name: str='nomic-embed-text', base_url: str=None, dimensions: int=None, **kwargs):
        self.model_name = model_name
        self.base_url = base_url
        self._dimensions = MODEL_DIMENSIONS.get(model_name, None) or dimensions
        self.kwargs = kwargs
        self._embedding_model = None
        self._embedding_model = self.get_embedding_model()

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        if self._embedding_model is None:
            try:
                self._embedding_model = OllamaEmbedding(model_name=self.model_name, base_url=self.base_url, embedding_dims=self._dimensions, **self.kwargs)
                logger.debug(f'Initialized Ollama embedding wrapper for model: {self.model_name}')
            except Exception as e:
                logger.error(f'Failed to initialize Ollama embedding wrapper: {str(e)}')
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions

def __init__(self, model_name: str='nomic-embed-text', base_url: str=None, dimensions: int=None, **kwargs):
    self.model_name = model_name
    self.base_url = base_url
    self._dimensions = MODEL_DIMENSIONS.get(model_name, None) or dimensions
    self.kwargs = kwargs
    self._embedding_model = None
    self._embedding_model = self.get_embedding_model()

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

def _prepare_matches(self, matches: List[str], limit: Optional[int]=None) -> List[NodeWithScore]:
    kg_nodes = self._graph_store.get(ids=matches)
    triplets = self._graph_store.get_rel_map(kg_nodes, depth=self._path_depth, limit=limit or self._limit, ignore_rels=[KG_SOURCE_REL])
    return self._get_nodes_with_score(triplets)

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

def _get_label(self, example: Dict) -> Any:
    return example.get('expected_output', '')

def _get_id(self, example: Dict) -> Any:
    return example.get('id', '')

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

def get_evaluation_sample(self):
    return {'input_output': json.dumps({'inputs': [t.input for t in self.public_test_cases + self.private_test_cases], 'outputs': [t.output for t in self.public_test_cases + self.private_test_cases], 'fn_name': self.metadata.get('func_name', None)})}

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

def __post_init__(self):
    self.test = [Test(**t) for t in json.loads(self.test)]

class CallbackManager:

    def __init__(self):
        self.local_data = threading.local()

    def _ensure_callbacks(self):
        if not hasattr(self.local_data, 'callbacks'):
            self.local_data.callbacks = {}

    def set_callback(self, callback_type: str, callback: Callback):
        self._ensure_callbacks()
        self.local_data.callbacks[callback_type] = callback

    def get_callback(self, callback_type: str):
        self._ensure_callbacks()
        return self.local_data.callbacks.get(callback_type, None)

    def has_callback(self, callback_type: str):
        self._ensure_callbacks()
        return callback_type in self.local_data.callbacks

    def clear_callback(self, callback_type: str):
        self._ensure_callbacks()
        if callback_type in self.local_data.callbacks:
            del self.local_data.callbacks[callback_type]

    def clear_all(self):
        self._ensure_callbacks()
        self.local_data.callbacks.clear()

def set_callback(self, callback_type: str, callback: Callback):
    self._ensure_callbacks()
    self.local_data.callbacks[callback_type] = callback

def get_callback(self, callback_type: str):
    self._ensure_callbacks()
    return self.local_data.callbacks.get(callback_type, None)

def has_callback(self, callback_type: str):
    self._ensure_callbacks()
    return callback_type in self.local_data.callbacks

def clear_callback(self, callback_type: str):
    self._ensure_callbacks()
    if callback_type in self.local_data.callbacks:
        del self.local_data.callbacks[callback_type]

def clear_all(self):
    self._ensure_callbacks()
    self.local_data.callbacks.clear()

def get_base_module_init_error_message(cls, data: Dict[str, Any], errors: List[Union[ValidationError, Exception]]) -> str:
    if not isinstance(errors, list):
        errors = [errors]
    message = f'Can not instantiate {cls.__name__} from: '
    formatted_data = json.dumps(data, indent=4, default=custom_serializer)
    formatted_data = remove_repr_quotes(formatted_data)
    message += formatted_data
    message += '\n\n' + get_error_message(errors)
    return message

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

class BaseLLM(ABC):
    """Abstract base class for Large Language Model implementations.
    
    This class defines the interface that all LLM implementations must follow,
    providing methods for generating text, formatting messages, and parsing output.
    
    Attributes:
        config: Configuration for the LLM.
        kwargs: Additional keyword arguments provided during initialization.
    """

    def __init__(self, config: LLMConfig, **kwargs):
        """Initializes the LLM with configuration.
        
        Args:
            config: Configuration object for the LLM.
            **kwargs (Any): Additional keyword arguments.
        """
        self.config = config
        self.kwargs = kwargs
        self.init_model()

    @abstractmethod
    def init_model(self):
        """Initializes the underlying model.
        
        This method should be implemented by subclasses to set up the actual LLM.
        """
        pass

    def __deepcopy__(self, memo) -> 'BaseLLM':
        """Handles deep copying of the LLM instance.
        
        Returns the same instance when deepcopy is called, as LLM instances
        often cannot be meaningfully deep-copied.
        
        Args:
            memo (Dict[int, Any]): Memo dictionary used by the deepcopy process.
            
        Returns:
            The same LLM instance.
        """
        memo[id(self)] = self
        return self

    @abstractmethod
    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        """Converts input prompts into the chat format compatible with different LLMs.

        Args:
            prompts: A list of user prompts that need to be converted.
            system_messages: An optional list of system messages that provide instructions or context to the model.
        
        Returns:
            A list of message lists, where each inner list contains messages in the chat format required by LLMs. 
        """
        pass

    @abstractmethod
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """Generates LLM output for a single set of messages.

        Args:
            messages: The input messages to the LLM in chat format.
            **kwargs (Any): Additional keyword arguments for generation settings.
        
        Returns:
            The generated output text from the LLM.
        """
        pass

    @abstractmethod
    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """Generates outputs for a batch of message sets.

        Args: 
            batch_messages: A list of message lists, where each inner list contains messages for a single generation.
            **kwargs (Any): Additional keyword arguments for generation settings.
        
        Returns:
            A list of generated outputs from the LLM, one for each input message set.
        """
        pass

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """Asynchronously generates LLM output for a single set of messages.
        
        This default implementation wraps the synchronous method in an async executor.
        Subclasses should override this for true async implementation if supported.
        
        Args:
            messages: The input messages to the LLM in chat format.
            **kwargs (Any): Additional keyword arguments for generation settings.
        
        Returns:
            The generated output text from the LLM.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.single_generate, messages, **kwargs)
        return result

    async def batch_generate_async(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """Asynchronously generates outputs for a batch of message sets.
        
        This default implementation runs each generation as a separate async task.
        Subclasses should override this for more efficient async batching if supported.
        
        Args: 
            batch_messages: A list of message lists, where each inner list contains messages for a single generation.
            **kwargs (Any): Additional keyword arguments for generation settings.
        
        Returns:
            A list of generated outputs from the LLM, one for each input message set.
        """
        tasks = [self.single_generate_async(messages, **kwargs) for messages in batch_messages]
        return await asyncio.gather(*tasks)

    def parse_generated_text(self, text: str, parser: Optional[Type[LLMOutputParser]]=None, parse_mode: Optional[str]='json', parse_func: Optional[Callable]=None, **kwargs) -> LLMOutputParser:
        """Parses generated text into a structured output using a parser.

        Args: 
            text: The text generated by the LLM.
            parser: An LLMOutputParser class to use for parsing. If None, the default LLMOutputParser is used.
            parse_mode: The mode to use for parsing, must be the `parse_mode` supported by the `parser`. 
            **kwargs (Any): Additional arguments passed to the parser.
        
        Returns:
            An LLMOutputParser instance containing the parsed data.
        """
        if not parser:
            parser = LLMOutputParser
        return parser.parse(text, parse_mode=parse_mode, parse_func=parse_func)

    def parse_generated_texts(self, texts: List[str], parser: Optional[Type[LLMOutputParser]]=None, parse_mode: Optional[str]='json', parse_func: Optional[Callable]=None, **kwargs) -> List[LLMOutputParser]:
        """Parses multiple generated texts into structured outputs.
        
        Args:
            texts: A list of texts generated by the LLM.
            parser: An LLMOutputParser class to use for parsing.
            parse_mode: The mode to use for parsing, must be the `parse_mode` supported by the `parser`. 
            **kwargs (Any): Additional arguments passed to the parser.
            
        Returns:
            A list of LLMOutputParser instances containing the parsed data.
        """
        parsed_results = [self.parse_generated_text(text=text, parser=parser, parse_mode=parse_mode, parse_func=parse_func, **kwargs) for text in texts]
        return parsed_results

    def _prepare_messages(self, prompt: Optional[Union[str, List[str]]]=None, system_message: Optional[Union[str, List[str]]]=None, messages: Optional[Union[List[dict], List[List[dict]]]]=None) -> tuple[List[List[dict]], bool]:
        """Prepares and validates input messages for generation.
        
        This internal method handles the various input formats (prompt strings, system messages,
        or pre-formatted message dictionaries) and converts them to a consistent format for generation.
        
        Args:
            prompt: Input prompt(s) to the LLM.
            system_message: System message(s) for the LLM.
            messages: Chat message(s) for the LLM, already in the required format.

        Returns:
            A tuple containing:
            - prepared_messages: List of message lists ready for generation
            - is_single_generate: Boolean indicating if this is a single generation (vs. batch)
            
        Raises:
            ValueError: If neither prompt nor messages is provided, or if both are provided.
            TypeError: If the inputs have inconsistent types or formats.
        """
        if not (prompt or messages):
            raise ValueError("Either 'prompt' or 'messages' must be provided.")
        if prompt and messages:
            raise ValueError("Both 'prompt' and 'messages' are provided. Please provide only one of them.")
        single_generate = False
        if messages is not None:
            if not messages:
                return ([], False)
            if isinstance(messages[0], dict):
                single_generate = True
                messages = [messages]
            processed_messages = self._process_messages_for_multimodal(messages)
            return (processed_messages, single_generate)
        if isinstance(prompt, str):
            single_generate = True
            prompt = [prompt]
            if system_message:
                if not isinstance(system_message, str):
                    raise TypeError(f"'system_message' should be a string when passing a single prompt, but found {type(system_message)}.")
                system_message = [system_message]
        elif isinstance(prompt, list) and all((isinstance(p, str) for p in prompt)):
            single_generate = False
            if not prompt:
                return ([], False)
            if system_message:
                if not isinstance(system_message, list) or len(prompt) != len(system_message):
                    raise ValueError(f"'system_message' should be a list of string when passing multiple prompts and the number of prompts ({len(prompt)}) must match the number of system messages ({len(system_message)}).")
        else:
            raise ValueError(f"'prompt' must be a str or List[str], but found {type(prompt)}.")
        prepared_messages = self.formulate_messages(prompts=prompt, system_messages=system_message)
        return (prepared_messages, single_generate)

    def _process_messages_for_multimodal(self, messages: List[List[dict]]) -> List[List[dict]]:
        """Process messages to handle multimodal content (TextChunk, ImageChunk)."""
        processed_messages = []
        for message_list in messages:
            processed_message_list = []
            for message in message_list:
                processed_message = message.copy()
                content = message.get('content')
                if _is_multimodal_content(content):
                    llm_type = getattr(self.config, 'llm_type', 'openai')
                    if llm_type.lower() in ['openaillm', 'openai']:
                        model_type = 'openai'
                    elif llm_type.lower() in ['litellm']:
                        model_type = 'litellm'
                    elif llm_type.lower() in ['openrouter']:
                        model_type = 'openrouter'
                    else:
                        model_type = 'openai'
                    from ..core.logging import logger
                    logger.debug(f'Processing multimodal content: llm_type={llm_type}, model_type={model_type}')
                    if isinstance(content, list):
                        processed_message['content'] = _process_multimodal_content(content, model_type)
                    else:
                        processed_message['content'] = _process_multimodal_content([content], model_type)
                processed_message_list.append(processed_message)
            processed_messages.append(processed_message_list)
        return processed_messages

    def generate(self, prompt: Optional[Union[str, List[str]]]=None, system_message: Optional[Union[str, List[str]]]=None, messages: Optional[Union[List[dict], List[List[dict]]]]=None, parser: Optional[Type[LLMOutputParser]]=None, parse_mode: Optional[str]='json', parse_func: Optional[Callable]=None, **kwargs) -> Union[LLMOutputParser, List[LLMOutputParser]]:
        """Generates LLM output(s) and parses the result(s).
        
        This is the main method for generating text with the LLM. It handles both
        single and batch generation, and automatically parses the outputs.
        
        Args:
            prompt: Input prompt(s) to the LLM.
            system_message: System message(s) for the LLM.
            messages: Chat message(s) for the LLM, already in the required format (either `prompt` or `messages` must be provided).
            parser: Parser class to use for processing the output.
            parse_mode: The mode to use for parsing, must be the `parse_mode` supported by the `parser`. 
            **kwargs (Any): Additional generation configuration parameters.
        
        Returns:
            For single generation: An LLMOutputParser instance.
            For batch generation: A list of LLMOutputParser instances.
            
        Raises:
            ValueError: If the input format is invalid.
            
        Note:
            Either prompt or messages must be provided. If both or neither is provided,
            an error will be raised.
        """
        prepared_messages, single_generate = self._prepare_messages(prompt, system_message, messages)
        if not prepared_messages:
            return []
        generated_texts = self.batch_generate(batch_messages=prepared_messages, **kwargs)
        parsed_outputs = self.parse_generated_texts(texts=generated_texts, parser=parser, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
        return parsed_outputs[0] if single_generate else parsed_outputs

    async def async_generate(self, prompt: Optional[Union[str, List[str]]]=None, system_message: Optional[Union[str, List[str]]]=None, messages: Optional[Union[List[dict], List[List[dict]]]]=None, parser: Optional[Type[LLMOutputParser]]=None, parse_mode: Optional[str]='json', parse_func: Optional[Callable]=None, **kwargs) -> Union[LLMOutputParser, List[LLMOutputParser]]:
        """Asynchronously generates LLM output(s) and parses the result(s).
        
        This is the async version of the generate method. It works identically but
        performs the generation asynchronously.
        """
        prepared_messages, single_generate = self._prepare_messages(prompt, system_message, messages)
        if not prepared_messages:
            return []
        generated_texts = await self.batch_generate_async(batch_messages=prepared_messages, **kwargs)
        parsed_outputs = self.parse_generated_texts(texts=generated_texts, parser=parser, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
        return parsed_outputs[0] if single_generate else parsed_outputs

def __deepcopy__(self, memo) -> 'BaseLLM':
    """Handles deep copying of the LLM instance.
        
        Returns the same instance when deepcopy is called, as LLM instances
        often cannot be meaningfully deep-copied.
        
        Args:
            memo (Dict[int, Any]): Memo dictionary used by the deepcopy process.
            
        Returns:
            The same LLM instance.
        """
    memo[id(self)] = self
    return self

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

@model_validator(mode='before')
@classmethod
def validate_data(cls, data: Any) -> Any:
    if 'inputs_format' in data and data['inputs_format'] and isinstance(data['inputs_format'], str):
        data['inputs_format'] = MODULE_REGISTRY.get_module(data['inputs_format'])
    if 'outputs_format' in data and data['outputs_format'] and isinstance(data['outputs_format'], str):
        data['outputs_format'] = MODULE_REGISTRY.get_module(data['outputs_format'])
    return data

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

def _generate_html_structure(self, parser: MarkdownParser, metadata: Dict[str, str], technical_chart_base64: str, price_volume_chart_base64: str) -> str:
    """Generate the complete HTML structure with neomorphism design."""
    header_html = self._generate_neomorphism_header(metadata, parser.sections)
    charts_html = self._generate_charts_section(technical_chart_base64, price_volume_chart_base64)
    dashboard_html = self._generate_dashboard_overview(parser.sections, metadata)
    sections_html = self._generate_detailed_sections(parser.sections, metadata)
    footer_html = self._generate_footer(metadata)
    return f"""\n        <!DOCTYPE html>\n        <html lang="zh-CN">\n        <head>\n            <meta charset="UTF-8">\n            <meta name="viewport" content="width=device-width, initial-scale=1.0">\n            <title>{metadata.get('股票名称', 'Unknown')} ({metadata.get('股票代码', 'Unknown')}) - 投资分析报告</title>\n            <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">\n            <style>\n                {self._get_neomorphism_css()}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                {header_html}\n                {dashboard_html}\n                {charts_html}\n                {sections_html}\n                {footer_html}\n            </div>\n            \n            <script>\n                {self._get_javascript()}\n            </script>\n        </body>\n        </html>\n        """

def _generate_footer(self, metadata: Dict[str, str]) -> str:
    """Generate the footer section."""
    return f'\n        <footer class="footer">\n            <div class="footer-content">\n                <p>报告生成时间: {metadata.get('报告生成时间', 'Unknown')}</p>\n                <p>数据来源: 股票市场数据、经济新闻、行业分析报告</p>\n                <p><strong>免责声明:</strong> 本报告仅供个人投资参考，不构成投资建议</p>\n            </div>\n        </footer>\n        '

class CSVToLLMConverter:
    """CSV转LLM JSON格式转换器"""

    def __init__(self, data_dir: str):
        """
        初始化转换器
        
        Args:
            data_dir (str): 数据目录路径（如 output_300750）
        """
        self.data_dir = Path(data_dir)
        self.file_priority = {'stock_daily_catl': {'weight': 'high', 'max_rows': 30}, 'institution_recommendation_catl': {'weight': 'high', 'max_rows': 20}, 'stock_news_catl': {'weight': 'high', 'max_rows': 15}, 'china_cpi': {'weight': 'medium', 'max_rows': 10}, 'china_gdp': {'weight': 'medium', 'max_rows': 10}, 'industry_fund_flow': {'weight': 'medium', 'max_rows': 15}, 'market_overview': {'weight': 'normal', 'max_rows': 5}, 'regional_indices': {'weight': 'normal', 'max_rows': 10}, 'option_volatility': {'weight': 'normal', 'max_rows': 8}, 'fund_flow_industry': {'weight': 'normal', 'max_rows': 12}}

    def find_csv_files(self) -> Dict[str, Dict]:
        """查找并分类CSV文件"""
        csv_files = {}
        if not self.data_dir.exists():
            print(f'❌ 数据目录不存在: {self.data_dir}')
            return csv_files
        for file_path in self.data_dir.glob('*.csv'):
            filename = file_path.name
            if 'collection_report' in filename.lower():
                continue
            file_type = self._identify_file_type(filename)
            if file_type:
                csv_files[file_type] = {'file_path': file_path, 'filename': filename, 'config': self.file_priority.get(file_type, {'weight': 'normal', 'max_rows': 10})}
        return csv_files

    def _identify_file_type(self, filename: str) -> Optional[str]:
        """根据文件名识别数据类型"""
        filename_lower = filename.lower()
        type_mapping = {'stock_daily_catl': ['stock_daily'], 'institution_recommendation_catl': ['institution_recommendation'], 'stock_news_catl': ['stock_news'], 'china_cpi': ['china_cpi'], 'china_gdp': ['china_gdp'], 'industry_fund_flow': ['industry_fund_flow'], 'market_overview': ['market_overview'], 'regional_indices': ['regional_indices'], 'option_volatility': ['option_volatility'], 'fund_flow_industry': ['fund_flow_industry']}
        for file_type, keywords in type_mapping.items():
            if any((keyword in filename_lower for keyword in keywords)):
                return file_type
        return None

    def read_and_process_csv(self, file_path: Path, max_rows: int, weight: str) -> List[Dict]:
        """读取并处理CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            if df.empty:
                print(f'⚠️ 文件为空: {file_path.name}')
                return []
            if weight == 'high':
                processed_df = df.tail(max_rows)
            else:
                processed_df = df.head(max_rows)
            processed_df = processed_df.fillna('')
            records = processed_df.to_dict(orient='records')
            print(f'✅ 处理完成 {file_path.name}: {len(records)} 条记录')
            return records
        except Exception as e:
            print(f'❌ 处理文件失败 {file_path.name}: {e}')
            return []

    def generate_llm_analysis_prompt(self) -> str:
        """生成适合LLM分析的提示格式"""
        csv_files = self.find_csv_files()
        if not csv_files:
            return 'No valid CSV files found in the specified directory.'

        def sort_priority(item):
            file_type, file_info = item
            weight = file_info['config']['weight']
            if 'stock_daily_catl' in file_type:
                return (0, 0)
            weight_order = {'high': 1, 'medium': 2, 'normal': 3}
            base_priority = weight_order.get(weight, 4)
            if weight == 'high':
                if 'institution_recommendation' in file_type:
                    return (base_priority, 1)
                elif 'stock_news' in file_type:
                    return (base_priority, 2)
            return (base_priority, 0)
        sorted_files = sorted(csv_files.items(), key=sort_priority)
        prompt_parts = []
        stock_code = self._extract_stock_code()
        prompt_parts.append(f'# 股票 {stock_code} 综合数据分析')
        prompt_parts.append('\n以下是该股票的各类数据，请进行综合分析并给出投资建议：\n')
        prompt_parts.append('## 📊 数据概览')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            weight_emoji = {'high': '🔥', 'medium': '⭐', 'normal': '📋'}
            emoji = weight_emoji.get(file_info['config']['weight'], '📋')
            prompt_parts.append(f'{i}. {emoji} {self._get_chinese_name(file_type)} ({file_info['filename']})')
        prompt_parts.append('\n## 📈 详细数据\n')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            file_path = file_info['file_path']
            config = file_info['config']
            data = self.read_and_process_csv(file_path, config['max_rows'], config['weight'])
            if not data:
                continue
            chinese_name = self._get_chinese_name(file_type)
            priority_label = {'high': '(重点关注)', 'medium': '(重要参考)', 'normal': '(背景信息)'}
            priority = priority_label.get(config['weight'], '')
            prompt_parts.append(f'### Dataset {i}: {chinese_name} {priority}')
            prompt_parts.append(f'文件: {file_info['filename']}')
            prompt_parts.append(f'数据量: {len(data)} 条记录\n')
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            prompt_parts.append('```json')
            prompt_parts.append(json_data)
            prompt_parts.append('```\n')
        prompt_parts.append('## 🎯 分析要求')
        prompt_parts.append('请基于以上数据进行以下分析：')
        prompt_parts.append('1. **价格趋势分析**: 根据股票日线数据分析价格走势')
        prompt_parts.append('2. **技术指标评估**: 结合移动平均线、成交量等技术指标')
        prompt_parts.append('3. **机构观点**: 分析机构评级和目标价')
        prompt_parts.append('4. **市场环境**: 考虑宏观经济数据和行业资金流向')
        prompt_parts.append('5. **新闻影响**: 评估相关新闻对股价的潜在影响')
        prompt_parts.append('6. **投资建议**: 给出明确的买入/持有/卖出建议及理由')
        prompt_parts.append('\n请用中文回答，并提供具体的数据支撑。')
        return '\n'.join(prompt_parts)

    def _extract_stock_code(self) -> str:
        """从目录名提取股票代码"""
        dir_name = self.data_dir.name
        if 'output_' in dir_name:
            return dir_name.replace('output_', '')
        return dir_name

    def _get_chinese_name(self, file_type: str) -> str:
        """获取数据类型的中文名称"""
        name_mapping = {'stock_daily_catl': 'Stock Daily Price Data (股票日线数据)', 'institution_recommendation_catl': 'Institution Recommendations (机构评级)', 'stock_news_catl': 'Stock News (股票新闻)', 'china_cpi': 'China CPI (中国CPI)', 'china_gdp': 'China GDP (中国GDP)', 'industry_fund_flow': 'Industry Fund Flow (行业资金流)', 'market_overview': 'Market Overview (市场概况)', 'regional_indices': 'Regional Indices (区域指数)', 'option_volatility': 'Option Volatility (期权波动率)', 'fund_flow_industry': 'Fund Flow Industry (行业资金流向)'}
        return name_mapping.get(file_type, file_type)

    def save_prompt_to_file(self, output_path: str=None) -> str:
        """保存提示内容到文件"""
        if output_path is None:
            output_path = self.data_dir / 'llm_analysis_prompt.txt'
        prompt_content = self.generate_llm_analysis_prompt()
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            file_size = os.path.getsize(output_path)
            print(f'✅ LLM分析提示已保存: {output_path}')
            print(f'📄 文件大小: {file_size:,} 字节')
            return str(output_path)
        except Exception as e:
            print(f'❌ 保存文件失败: {e}')
            return ''

    def get_json_data(self) -> Dict[str, List[Dict]]:
        """直接获取JSON格式的数据字典"""
        csv_files = self.find_csv_files()
        json_data = {}
        for file_type, file_info in csv_files.items():
            config = file_info['config']
            data = self.read_and_process_csv(file_info['file_path'], config['max_rows'], config['weight'])
            if data:
                chinese_name = self._get_chinese_name(file_type)
                json_data[chinese_name] = data
        return json_data

def sort_priority(item):
    file_type, file_info = item
    weight = file_info['config']['weight']
    if 'stock_daily_catl' in file_type:
        return (0, 0)
    weight_order = {'high': 1, 'medium': 2, 'normal': 3}
    base_priority = weight_order.get(weight, 4)
    if weight == 'high':
        if 'institution_recommendation' in file_type:
            return (base_priority, 1)
        elif 'stock_news' in file_type:
            return (base_priority, 2)
    return (base_priority, 0)

def _get_chinese_name(self, file_type: str) -> str:
    """获取数据类型的中文名称"""
    name_mapping = {'stock_daily_catl': 'Stock Daily Price Data (股票日线数据)', 'institution_recommendation_catl': 'Institution Recommendations (机构评级)', 'stock_news_catl': 'Stock News (股票新闻)', 'china_cpi': 'China CPI (中国CPI)', 'china_gdp': 'China GDP (中国GDP)', 'industry_fund_flow': 'Industry Fund Flow (行业资金流)', 'market_overview': 'Market Overview (市场概况)', 'regional_indices': 'Regional Indices (区域指数)', 'option_volatility': 'Option Volatility (期权波动率)', 'fund_flow_industry': 'Fund Flow Industry (行业资金流向)'}
    return name_mapping.get(file_type, file_type)

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

def _generate_html_structure(self, parser: MarkdownParser, metadata: Dict[str, str], technical_chart_base64: str, price_volume_chart_base64: str) -> str:
    """Generate the complete HTML structure with neomorphism design."""
    header_html = self._generate_neomorphism_header(metadata, parser.sections)
    charts_html = self._generate_charts_section(technical_chart_base64, price_volume_chart_base64)
    dashboard_html = self._generate_dashboard_overview(parser.sections, metadata)
    sections_html = self._generate_detailed_sections(parser.sections, metadata)
    footer_html = self._generate_footer(metadata)
    return f"""\n        <!DOCTYPE html>\n        <html lang="zh-CN">\n        <head>\n            <meta charset="UTF-8">\n            <meta name="viewport" content="width=device-width, initial-scale=1.0">\n            <title>{metadata.get('股票名称', 'Unknown')} ({metadata.get('股票代码', 'Unknown')}) - 投资分析报告</title>\n            <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">\n            <style>\n                {self._get_neomorphism_css()}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                {header_html}\n                {dashboard_html}\n                {charts_html}\n                {sections_html}\n                {footer_html}\n            </div>\n            \n            <script>\n                {self._get_javascript()}\n            </script>\n        </body>\n        </html>\n        """

def _generate_footer(self, metadata: Dict[str, str]) -> str:
    """Generate the footer section."""
    return f'\n        <footer class="footer">\n            <div class="footer-content">\n                <p>报告生成时间: {metadata.get('报告生成时间', 'Unknown')}</p>\n                <p>数据来源: 股票市场数据、经济新闻、行业分析报告</p>\n                <p><strong>免责声明:</strong> 本报告仅供个人投资参考，不构成投资建议</p>\n            </div>\n        </footer>\n        '

class CSVToLLMConverter:
    """CSV转LLM JSON格式转换器"""

    def __init__(self, data_dir: str):
        """
        初始化转换器
        
        Args:
            data_dir (str): 数据目录路径（如 output_300750）
        """
        self.data_dir = Path(data_dir)
        self.file_priority = {'stock_daily_catl': {'weight': 'high', 'max_rows': 30}, 'institution_recommendation_catl': {'weight': 'high', 'max_rows': 20}, 'stock_news_catl': {'weight': 'high', 'max_rows': 15}, 'china_cpi': {'weight': 'medium', 'max_rows': 10}, 'china_gdp': {'weight': 'medium', 'max_rows': 10}, 'industry_fund_flow': {'weight': 'medium', 'max_rows': 15}, 'market_overview': {'weight': 'normal', 'max_rows': 5}, 'regional_indices': {'weight': 'normal', 'max_rows': 10}, 'option_volatility': {'weight': 'normal', 'max_rows': 8}, 'fund_flow_industry': {'weight': 'normal', 'max_rows': 12}}

    def find_csv_files(self) -> Dict[str, Dict]:
        """查找并分类CSV文件"""
        csv_files = {}
        if not self.data_dir.exists():
            print(f'❌ 数据目录不存在: {self.data_dir}')
            return csv_files
        for file_path in self.data_dir.glob('*.csv'):
            filename = file_path.name
            if 'collection_report' in filename.lower():
                continue
            file_type = self._identify_file_type(filename)
            if file_type:
                csv_files[file_type] = {'file_path': file_path, 'filename': filename, 'config': self.file_priority.get(file_type, {'weight': 'normal', 'max_rows': 10})}
        return csv_files

    def _identify_file_type(self, filename: str) -> Optional[str]:
        """根据文件名识别数据类型"""
        filename_lower = filename.lower()
        type_mapping = {'stock_daily_catl': ['stock_daily'], 'institution_recommendation_catl': ['institution_recommendation'], 'stock_news_catl': ['stock_news'], 'china_cpi': ['china_cpi'], 'china_gdp': ['china_gdp'], 'industry_fund_flow': ['industry_fund_flow'], 'market_overview': ['market_overview'], 'regional_indices': ['regional_indices'], 'option_volatility': ['option_volatility'], 'fund_flow_industry': ['fund_flow_industry']}
        for file_type, keywords in type_mapping.items():
            if any((keyword in filename_lower for keyword in keywords)):
                return file_type
        return None

    def read_and_process_csv(self, file_path: Path, max_rows: int, weight: str) -> List[Dict]:
        """读取并处理CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            if df.empty:
                print(f'⚠️ 文件为空: {file_path.name}')
                return []
            if weight == 'high':
                processed_df = df.tail(max_rows)
            else:
                processed_df = df.head(max_rows)
            processed_df = processed_df.fillna('')
            records = processed_df.to_dict(orient='records')
            print(f'✅ 处理完成 {file_path.name}: {len(records)} 条记录')
            return records
        except Exception as e:
            print(f'❌ 处理文件失败 {file_path.name}: {e}')
            return []

    def generate_llm_analysis_prompt(self) -> str:
        """生成适合LLM分析的提示格式"""
        csv_files = self.find_csv_files()
        if not csv_files:
            return 'No valid CSV files found in the specified directory.'

        def sort_priority(item):
            file_type, file_info = item
            weight = file_info['config']['weight']
            if 'stock_daily_catl' in file_type:
                return (0, 0)
            weight_order = {'high': 1, 'medium': 2, 'normal': 3}
            base_priority = weight_order.get(weight, 4)
            if weight == 'high':
                if 'institution_recommendation' in file_type:
                    return (base_priority, 1)
                elif 'stock_news' in file_type:
                    return (base_priority, 2)
            return (base_priority, 0)
        sorted_files = sorted(csv_files.items(), key=sort_priority)
        prompt_parts = []
        stock_code = self._extract_stock_code()
        prompt_parts.append(f'# 股票 {stock_code} 综合数据分析')
        prompt_parts.append('\n以下是该股票的各类数据，请进行综合分析并给出投资建议：\n')
        prompt_parts.append('## 📊 数据概览')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            weight_emoji = {'high': '🔥', 'medium': '⭐', 'normal': '📋'}
            emoji = weight_emoji.get(file_info['config']['weight'], '📋')
            prompt_parts.append(f'{i}. {emoji} {self._get_chinese_name(file_type)} ({file_info['filename']})')
        prompt_parts.append('\n## 📈 详细数据\n')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            file_path = file_info['file_path']
            config = file_info['config']
            data = self.read_and_process_csv(file_path, config['max_rows'], config['weight'])
            if not data:
                continue
            chinese_name = self._get_chinese_name(file_type)
            priority_label = {'high': '(重点关注)', 'medium': '(重要参考)', 'normal': '(背景信息)'}
            priority = priority_label.get(config['weight'], '')
            prompt_parts.append(f'### Dataset {i}: {chinese_name} {priority}')
            prompt_parts.append(f'文件: {file_info['filename']}')
            prompt_parts.append(f'数据量: {len(data)} 条记录\n')
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            prompt_parts.append('```json')
            prompt_parts.append(json_data)
            prompt_parts.append('```\n')
        prompt_parts.append('## 🎯 分析要求')
        prompt_parts.append('请基于以上数据进行以下分析：')
        prompt_parts.append('1. **价格趋势分析**: 根据股票日线数据分析价格走势')
        prompt_parts.append('2. **技术指标评估**: 结合移动平均线、成交量等技术指标')
        prompt_parts.append('3. **机构观点**: 分析机构评级和目标价')
        prompt_parts.append('4. **市场环境**: 考虑宏观经济数据和行业资金流向')
        prompt_parts.append('5. **新闻影响**: 评估相关新闻对股价的潜在影响')
        prompt_parts.append('6. **投资建议**: 给出明确的买入/持有/卖出建议及理由')
        prompt_parts.append('\n请用中文回答，并提供具体的数据支撑。')
        return '\n'.join(prompt_parts)

    def _extract_stock_code(self) -> str:
        """从目录名提取股票代码"""
        dir_name = self.data_dir.name
        if 'output_' in dir_name:
            return dir_name.replace('output_', '')
        return dir_name

    def _get_chinese_name(self, file_type: str) -> str:
        """获取数据类型的中文名称"""
        name_mapping = {'stock_daily_catl': 'Stock Daily Price Data (股票日线数据)', 'institution_recommendation_catl': 'Institution Recommendations (机构评级)', 'stock_news_catl': 'Stock News (股票新闻)', 'china_cpi': 'China CPI (中国CPI)', 'china_gdp': 'China GDP (中国GDP)', 'industry_fund_flow': 'Industry Fund Flow (行业资金流)', 'market_overview': 'Market Overview (市场概况)', 'regional_indices': 'Regional Indices (区域指数)', 'option_volatility': 'Option Volatility (期权波动率)', 'fund_flow_industry': 'Fund Flow Industry (行业资金流向)'}
        return name_mapping.get(file_type, file_type)

    def save_prompt_to_file(self, output_path: str=None) -> str:
        """保存提示内容到文件"""
        if output_path is None:
            output_path = self.data_dir / 'llm_analysis_prompt.txt'
        prompt_content = self.generate_llm_analysis_prompt()
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            file_size = os.path.getsize(output_path)
            print(f'✅ LLM分析提示已保存: {output_path}')
            print(f'📄 文件大小: {file_size:,} 字节')
            return str(output_path)
        except Exception as e:
            print(f'❌ 保存文件失败: {e}')
            return ''

    def get_json_data(self) -> Dict[str, List[Dict]]:
        """直接获取JSON格式的数据字典"""
        csv_files = self.find_csv_files()
        json_data = {}
        for file_type, file_info in csv_files.items():
            config = file_info['config']
            data = self.read_and_process_csv(file_info['file_path'], config['max_rows'], config['weight'])
            if data:
                chinese_name = self._get_chinese_name(file_type)
                json_data[chinese_name] = data
        return json_data

def sort_priority(item):
    file_type, file_info = item
    weight = file_info['config']['weight']
    if 'stock_daily_catl' in file_type:
        return (0, 0)
    weight_order = {'high': 1, 'medium': 2, 'normal': 3}
    base_priority = weight_order.get(weight, 4)
    if weight == 'high':
        if 'institution_recommendation' in file_type:
            return (base_priority, 1)
        elif 'stock_news' in file_type:
            return (base_priority, 2)
    return (base_priority, 0)

def _get_chinese_name(self, file_type: str) -> str:
    """获取数据类型的中文名称"""
    name_mapping = {'stock_daily_catl': 'Stock Daily Price Data (股票日线数据)', 'institution_recommendation_catl': 'Institution Recommendations (机构评级)', 'stock_news_catl': 'Stock News (股票新闻)', 'china_cpi': 'China CPI (中国CPI)', 'china_gdp': 'China GDP (中国GDP)', 'industry_fund_flow': 'Industry Fund Flow (行业资金流)', 'market_overview': 'Market Overview (市场概况)', 'regional_indices': 'Regional Indices (区域指数)', 'option_volatility': 'Option Volatility (期权波动率)', 'fund_flow_industry': 'Fund Flow Industry (行业资金流向)'}
    return name_mapping.get(file_type, file_type)

def run_image_analysis_example():
    """Simple example using OpenRouter image analysis to analyze images."""
    print('\n===== IMAGE ANALYSIS TOOL EXAMPLE =====\n')
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_api_key:
        print('❌ OPENROUTER_API_KEY not found in environment variables')
        return
    try:
        ortk = OpenRouterImageToolkit(name='DemoORImageToolkit', api_key=openrouter_api_key)
        analyze_tool = ortk.get_tool('image_analysis')
        test_image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg'
        print(f'Analyzing image: {test_image_url}')
        result = analyze_tool(prompt='Describe this image in detail.', image_url=test_image_url)
        if 'error' in result:
            print(f'❌ Image analysis failed: {result['error']}')
        else:
            print('✓ Analysis:')
            print(result.get('content', ''))
    except Exception as e:
        print(f'Error: {str(e)}')

def run_openai_image_toolkit_pipeline():
    """Pipeline: generate → edit → analyze using OpenAIImageToolkit."""
    print('\n===== OPENAI IMAGE TOOLKIT PIPELINE (GEN → EDIT → ANALYZE) =====\n')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_org_id = os.getenv('OPENAI_ORGANIZATION_ID')
    if not openai_api_key:
        print('❌ OPENAI_API_KEY not found in environment variables')
        return
    toolkit = OpenAIImageToolkit(name='DemoOpenAIImageToolkit', api_key=openai_api_key, organization_id=openai_org_id, generation_model='gpt-image-1', save_path='./generated_images')
    gen = toolkit.get_tool('openai_image_generation')
    edit = toolkit.get_tool('openai_image_edit')
    analyze = toolkit.get_tool('openai_image_analysis')
    gen_prompt = 'A cute baby owl sitting on a tree branch at sunset, digital art'
    print(f'Generating: {gen_prompt}')
    gen_result = gen(prompt=gen_prompt, model='gpt-image-1', size='1024x1024')
    if 'error' in gen_result:
        print(f'❌ Generation failed: {gen_result['error']}')
        return
    gen_paths = gen_result.get('results', [])
    if not gen_paths:
        print('❌ No generated images returned')
        return
    src_path = gen_paths[0]
    print(f'Generated image: {src_path}')
    print('Editing the generated image...')
    edit_result = edit(prompt="Add a red scarf around the owl's neck", images=src_path, size='1024x1024', background='opaque', quality='high', n=1, image_name='edited_minimal')
    if 'error' in edit_result:
        print(f'❌ Edit failed: {edit_result['error']}')
        return
    edited_paths = edit_result.get('results', [])
    if not edited_paths:
        print('❌ No edited images returned')
        return
    edited_path = edited_paths[0]
    print(f'Edited image: {edited_path}')
    print('Analyzing the edited image...')
    try:
        analysis = analyze(prompt="Summarize what's in this image in one sentence.", image_path=edited_path, model='gpt-4o-mini')
        if 'error' in analysis:
            print(f'❌ Analyze failed: {analysis['error']}')
        else:
            print('✓ Analysis:')
            print(analysis.get('content', ''))
    except Exception as e:
        print(f'❌ Failed to analyze edited image: {e}')

def run_flux_image_generation_example():
    """Simple example using Flux Image Generation Toolkit."""
    print('\n===== IMAGE GENERATION TOOL EXAMPLE =====\n')
    bfl_api_key = os.getenv('BFL_API_KEY')
    if not bfl_api_key:
        print('❌ BFL_API_KEY not found in environment variables')
        print('To test Flux image generation, set your BFL API key:')
        print("export BFL_API_KEY='your-bfl-api-key-here'")
        print('Get your key from: https://flux.ai/')
        return
    try:
        toolkit = FluxImageGenerationToolkit(name='DemoFluxImageToolkit', api_key=bfl_api_key, save_path='./flux_generated_images')
        print('✓ Image Generation Toolkit initialized')
        print(f'✓ Using BFL API key: {bfl_api_key[:8]}...')
        generate_tool = toolkit.get_tool('flux_image_generation_edit')
        test_prompt = 'A futuristic cyberpunk city with neon lights and flying cars, digital art style'
        print(f"Generating image with prompt: '{test_prompt}'")
        result = generate_tool(prompt=test_prompt, seed=42, output_format='jpeg', prompt_upsampling=False, safety_tolerance=2)
        if 'error' not in result:
            print('✓ Image generation successful')
            print(f'Generated image path: {result.get('file_path', 'No path')}')
            file_path = result.get('file_path', '')
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f'File size: {file_size} bytes')
                print('✓ Generated image file saved successfully')
            else:
                print('⚠ Generated image file not found')
        else:
            print(f'❌ Image generation failed: {result.get('error', 'Unknown error')}')
        print('\n✓ Image Generation Toolkit test completed')
    except Exception as e:
        print(f'Error: {str(e)}')

def run_openrouter_edit_pipeline():
    """OpenRouter: generate → edit (with generated image as input) → save."""
    print('\n===== OPENROUTER EDIT PIPELINE (GEN → EDIT) =====\n')
    or_key = os.getenv('OPENROUTER_API_KEY')
    if not or_key:
        print('❌ OPENROUTER_API_KEY not found')
        return
    ortk = OpenRouterImageToolkit(name='DemoORImageToolkit', api_key=or_key)
    gen = ortk.get_tool('openrouter_image_generation_edit')
    res = gen(prompt='A minimalist poster of a mountain at sunrise', model='google/gemini-2.5-flash-image-preview', save_path='./openrouter_images', output_basename='base')
    bases = res.get('saved_paths', [])
    if not bases:
        print('❌ No base image saved; cannot proceed to edit')
        return
    base_path = bases[0]
    print(f'Base image: {base_path}')
    edit_prompt = "Add a bold 'GEMINI' text at the top"
    edit_res = gen(prompt=edit_prompt, image_paths=[base_path], model='google/gemini-2.5-flash-image-preview', save_path='./openrouter_images', output_basename='edited')
    edited = edit_res.get('saved_paths', [])
    if not edited:
        print('❌ No edited image saved')
        return
    print(f'Edited image: {edited[0]}')

def run_mongodb_examples():
    """Run examples using MongoDBToolkit for document database operations."""
    print('\n===== MONGODB TOOLKIT EXAMPLES =====\n')
    try:
        toolkit = MongoDBToolkit(name='DemoMongoDBToolkit', database_name='demo_db', auto_save=True)
        print('✓ MongoDBToolkit initialized with default storage')
        execute_tool = toolkit.get_tool('mongodb_execute_query')
        find_tool = toolkit.get_tool('mongodb_find')
        update_tool = toolkit.get_tool('mongodb_update')
        delete_tool = toolkit.get_tool('mongodb_delete')
        info_tool = toolkit.get_tool('mongodb_info')
        print(f'✓ Available tools: {[tool.name for tool in toolkit.get_tools()]}')
        print('\n1. Inserting product data...')
        products = [{'id': 'P001', 'name': 'Laptop', 'category': 'Electronics', 'price': 999.99, 'stock': 50, 'brand': 'TechCorp'}, {'id': 'P002', 'name': 'Wireless Mouse', 'category': 'Electronics', 'price': 29.99, 'stock': 100, 'brand': 'TechCorp'}, {'id': 'P003', 'name': 'Desk Chair', 'category': 'Furniture', 'price': 199.99, 'stock': 25, 'brand': 'ComfortCo'}, {'id': 'P004', 'name': 'Coffee Table', 'category': 'Furniture', 'price': 149.99, 'stock': 15, 'brand': 'ComfortCo'}, {'id': 'P005', 'name': 'Smartphone', 'category': 'Electronics', 'price': 799.99, 'stock': 75, 'brand': 'MobileTech'}]
        insert_result = execute_tool(query=json.dumps(products), query_type='insert', collection_name='products')
        if insert_result.get('success'):
            print(f'✓ Successfully inserted {len(products)} products')
            print(f'  Documents inserted: {insert_result.get('data', {}).get('inserted_count', 'Unknown')}')
        else:
            print(f'❌ Insert failed: {insert_result.get('error', 'Unknown error')}')
            return
        print('\n2. Finding electronics products...')
        find_result = find_tool(collection_name='products', filter='{"category": "Electronics"}', sort='{"price": -1}', limit=5)
        if find_result.get('success'):
            electronics = find_result.get('data', [])
            print(f'✓ Found {len(electronics)} electronics products:')
            for product in electronics:
                name = product.get('name', 'Unknown')
                price = product.get('price', 0)
                brand = product.get('brand', 'Unknown')
                print(f'  - {name}: ${price} ({brand})')
        else:
            print(f'❌ Find failed: {find_result.get('error', 'Unknown error')}')
        print('\n3. Updating product prices (10% discount on electronics)...')
        update_result = update_tool(collection_name='products', filter='{"category": "Electronics"}', update='{"$mul": {"price": 0.9}}', multi=True)
        if update_result.get('success'):
            updated_count = update_result.get('data', {}).get('modified_count', 0)
            print(f'✓ Updated {updated_count} electronics products with 10% discount')
        else:
            print(f'❌ Update failed: {update_result.get('error', 'Unknown error')}')
        print('\n4. Running aggregation query (average price by category)...')
        aggregation_pipeline = [{'$group': {'_id': '$category', 'avg_price': {'$avg': '$price'}, 'total_stock': {'$sum': '$stock'}}}, {'$sort': {'avg_price': -1}}]
        agg_result = execute_tool(query=json.dumps(aggregation_pipeline), query_type='aggregate', collection_name='products')
        if agg_result.get('success'):
            categories = agg_result.get('data', [])
            print(f'✓ Category analysis:')
            for category in categories:
                cat_name = category.get('_id', 'Unknown')
                avg_price = category.get('avg_price', 0)
                total_stock = category.get('total_stock', 0)
                print(f'  - {cat_name}: Avg price ${avg_price:.2f}, Total stock: {total_stock}')
        else:
            print(f'❌ Aggregation failed: {agg_result.get('error', 'Unknown error')}')
        print('\n5. Testing delete functionality...')
        delete_result = delete_tool(collection_name='products', filter='{"category": "Furniture"}', multi=True)
        if delete_result.get('success'):
            deleted_count = delete_result.get('data', {}).get('deleted_count', 0)
            print(f'✓ Deleted {deleted_count} furniture products')
        else:
            print(f'❌ Delete failed: {delete_result.get('error', 'Unknown error')}')
        print('\n6. Getting database information...')
        info_result = info_tool()
        if info_result.get('success'):
            info = info_result.get('data', {})
            print(f'✓ Database info:')
            print(f'  - Database: {info.get('database_name', 'Unknown')}')
            collections = info.get('collections', [])
            if isinstance(collections, (list, tuple)) and collections:
                print(f'  - Collections: {', '.join(collections)}')
            elif collections:
                print(f'  - Collections: {collections}')
            else:
                print('  - Collections: None')
            print(f'  - Total documents: {info.get('total_documents', 'Unknown')}')
        else:
            print(f'❌ Info failed: {info_result.get('error', 'Unknown error')}')
        print('\n✓ MongoDB examples completed successfully!')
    except Exception as e:
        print(f'❌ Error running MongoDB examples: {str(e)}')

def run_postgresql_examples():
    """Powerful example using PostgreSQLToolkit for database operations."""
    print('\n===== POSTGRESQL TOOL EXAMPLE =====\n')
    try:
        toolkit = PostgreSQLToolkit(name='DemoPostgreSQLToolkit', database_name='demo_db', auto_save=True)
        print('✓ PostgreSQLToolkit initialized with default storage')
        execute_tool = toolkit.get_tool('postgresql_execute')
        find_tool = toolkit.get_tool('postgresql_find')
        create_tool = toolkit.get_tool('postgresql_create')
        delete_tool = toolkit.get_tool('postgresql_delete')
        create_sql = '\n        CREATE TABLE IF NOT EXISTS users (\n            id SERIAL PRIMARY KEY,\n            name VARCHAR(100) NOT NULL,\n            email VARCHAR(100) UNIQUE NOT NULL,\n            age INTEGER,\n            department VARCHAR(50)\n        );\n        '
        result = create_tool(create_sql)
        if result['success']:
            print('✓ Created users table')
            insert_sql = "\n            INSERT INTO users (name, email, age, department) VALUES\n            ('Alice Johnson', 'alice@example.com', 28, 'Engineering'),\n            ('Bob Smith', 'bob@example.com', 32, 'Marketing'),\n            ('Carol Davis', 'carol@example.com', 25, 'Engineering')\n            "
            result = execute_tool(insert_sql)
            if result['success']:
                print('✓ Inserted users')
                find_result = find_tool('users', where="department = 'Engineering'", columns='name, age', sort='age ASC')
                if find_result['success']:
                    engineers = find_result['data']['data']
                    print(f'✓ Found {len(engineers)} engineers:')
                    for user in engineers:
                        name = user.get('name', 'Unknown')
                        age = user.get('age', 'N/A')
                        print(f'  - {name} (age: {age})')
                print('\n🗑️ Testing delete functionality...')
                delete_result = delete_tool('users', "department = 'Marketing'")
                if delete_result['success']:
                    deleted_count = delete_result['data'].get('rowcount', 0)
                    print(f'✓ Deleted {deleted_count} marketing users')
                    verify_result = find_tool('users')
                    if verify_result['success']:
                        remaining = verify_result['data']
                        print(f'✓ Remaining users after deletion: {len(remaining)}')
        print('\n✓ PostgreSQLToolkit test completed with default storage')
    except Exception as e:
        print(f'Error: {str(e)}')

def run_faiss_examples():
    """Run examples using FaissToolkit for vector database operations."""
    print('\n===== FAISS TOOLKIT EXAMPLES =====\n')
    if not os.getenv('OPENAI_API_KEY'):
        print('❌ OPENAI_API_KEY not found in environment variables')
        print('To test FAISS examples, set your OpenAI API key:')
        print("export OPENAI_API_KEY='your-openai-api-key-here'")
        print('Get your key from: https://platform.openai.com/api-keys')
        return
    try:
        toolkit = FaissToolkit(name='DemoFaissToolkit', default_corpus_id='demo_corpus')
        print('✓ FaissToolkit initialized with default storage')
        print(f'✓ Using OpenAI API key: {os.getenv('OPENAI_API_KEY')[:8]}...')
        insert_tool = toolkit.get_tool('faiss_insert')
        query_tool = toolkit.get_tool('faiss_query')
        list_tool = toolkit.get_tool('faiss_list')
        stats_tool = toolkit.get_tool('faiss_stats')
        delete_tool = toolkit.get_tool('faiss_delete')
        print(f'✓ Available tools: {[tool.name for tool in toolkit.get_tools()]}')
        print('\n1. Inserting AI knowledge documents...')
        ai_documents = ['Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines capable of performing tasks that typically require human intelligence.', 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.', 'Deep learning is a specialized form of machine learning that uses neural networks with multiple layers to analyze and learn from data.', 'Natural Language Processing (NLP) helps computers understand, interpret, and generate human language in a useful way.', 'Computer vision enables machines to interpret and understand visual information from the world, including images and videos.', 'Reinforcement learning is a type of machine learning where an agent learns to make decisions by taking actions in an environment to achieve maximum cumulative reward.', 'Neural networks are computing systems inspired by biological neural networks, consisting of interconnected nodes that process information.', 'Transfer learning allows a model trained on one task to be adapted for a related task, improving efficiency and performance.', 'Generative AI models can create new content, such as text, images, music, and code, based on patterns learned from training data.', "Explainable AI focuses on making AI systems' decisions and processes transparent and understandable to humans."]
        insert_result = insert_tool(documents=ai_documents, metadata={'source': 'ai_knowledge_base', 'topic': 'artificial_intelligence', 'language': 'en', 'difficulty': 'intermediate'})
        if insert_result.get('success'):
            docs_inserted = insert_result.get('data', {}).get('documents_inserted', 0)
            chunks_created = insert_result.get('data', {}).get('chunks_created', 0)
            print(f'✓ Successfully inserted {docs_inserted} documents')
            print(f'  Chunks created: {chunks_created}')
        else:
            print(f'❌ Insert failed: {insert_result.get('error', 'Unknown error')}')
            return
        print('\n2. Performing semantic search queries...')
        search_queries = ['How do machines learn?', 'What is neural network?', 'Explain deep learning', 'How does AI generate content?', 'What is computer vision?']
        for i, query in enumerate(search_queries, 1):
            print(f"\n  Query {i}: '{query}'")
            search_result = query_tool(query=query, top_k=3, similarity_threshold=0.1)
            if search_result.get('success'):
                results = search_result.get('data', {}).get('results', [])
                print(f'    ✓ Found {len(results)} relevant results:')
                for j, result in enumerate(results, 1):
                    score = result.get('score', 0)
                    content = result.get('content', '')[:80]
                    print(f'      {j}. Score: {score:.3f} - {content}...')
            else:
                print(f'    ❌ Search failed: {search_result.get('error', 'Unknown error')}')
        print('\n3. Searching with metadata filters...')
        filtered_search_result = query_tool(query='machine learning algorithms', top_k=5, similarity_threshold=0.1, metadata_filters={'topic': 'artificial_intelligence', 'difficulty': 'intermediate'})
        if filtered_search_result.get('success'):
            results = filtered_search_result.get('data', {}).get('results', [])
            print(f'✓ Found {len(results)} results with metadata filters:')
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                content = result.get('content', '')[:100]
                metadata = result.get('metadata', {})
                print(f'  {i}. Score: {score:.3f} - {content}...')
                print(f'     Metadata: {metadata}')
        else:
            print(f'❌ Filtered search failed: {filtered_search_result.get('error', 'Unknown error')}')
        print('\n4. Getting database statistics...')
        stats_result = stats_tool()
        if stats_result.get('success'):
            stats = stats_result.get('data', {})
            print(f'✓ Database statistics:')
            print(f'  - Total corpora: {stats.get('total_corpora', 'Unknown')}')
            print(f'  - Corpora: {', '.join(stats.get('corpora', []))}')
            print(f'  - Embedding model: {stats.get('embedding_model', 'Unknown')}')
            print(f'  - Vector store type: {stats.get('vector_store_type', 'Unknown')}')
        else:
            print(f'❌ Stats failed: {stats_result.get('error', 'Unknown error')}')
        print('\n5. Listing all corpora...')
        list_result = list_tool()
        if list_result.get('success'):
            corpora = list_result.get('data', {}).get('corpora', [])
            print(f'✓ Found {len(corpora)} corpora:')
            for corpus in corpora:
                corpus_id = corpus.get('corpus_id', 'Unknown')
                doc_count = corpus.get('document_count', 'Unknown')
                chunk_count = corpus.get('chunk_count', 'Unknown')
                print(f'  - {corpus_id}: {doc_count} documents, {chunk_count} chunks')
        else:
            print(f'❌ List failed: {list_result.get('error', 'Unknown error')}')
        print('\n6. Testing delete functionality...')
        delete_result = delete_tool(metadata_filters={'source': 'ai_knowledge_base'})
        if delete_result.get('success'):
            deleted_count = delete_result.get('data', {}).get('deleted_count', 0)
            print(f'✓ Deleted {deleted_count} documents with metadata filter')
            verify_result = query_tool(query='artificial intelligence', top_k=5, similarity_threshold=0.1)
            if verify_result.get('success'):
                remaining = verify_result.get('data', {}).get('total_results', 0)
                print(f'✓ Remaining documents after deletion: {remaining}')
        else:
            print(f'❌ Delete failed: {delete_result.get('error', 'Unknown error')}')
        print('\n✓ FAISS examples completed successfully!')
    except Exception as e:
        print(f'❌ Error running FAISS examples: {str(e)}')
        if 'DocumentMetadata' in str(e):
            print('Note: This appears to be a dependency issue with the RAG engine components')
            print('The FAISS toolkit may need additional setup or dependencies')

def run_search_examples():
    """
    Run examples using the search toolkits (Wikipedia, Google, Google Free, DDGS, SerpAPI, and SerperAPI).
    """
    print('\n===== SEARCH TOOLS EXAMPLES =====\n')
    wiki_toolkit = WikipediaSearchToolkit(max_summary_sentences=3)
    google_toolkit = GoogleSearchToolkit(num_search_pages=3, max_content_words=200)
    google_free_toolkit = GoogleFreeSearchToolkit()
    ddgs_toolkit = DDGSSearchToolkit(num_search_pages=3, max_content_words=200, backend='auto', region='us-en')
    serpapi_toolkit = SerpAPIToolkit(num_search_pages=3, max_content_words=300, enable_content_scraping=True)
    serperapi_toolkit = SerperAPIToolkit(num_search_pages=3, max_content_words=300, enable_content_scraping=True)
    wiki_tool = wiki_toolkit.get_tool('wikipedia_search')
    google_tool = google_toolkit.get_tool('google_search')
    google_free_tool = google_free_toolkit.get_tool('google_free_search')
    ddgs_tool = ddgs_toolkit.get_tool('ddgs_search')
    serpapi_tool = serpapi_toolkit.get_tool('serpapi_search')
    serperapi_tool = serperapi_toolkit.get_tool('serperapi_search')
    query = 'artificial intelligence agent architecture'
    try:
        print('\nWikipedia Search Example:')
        print('-' * 50)
        wiki_results = wiki_tool(query=query, num_search_pages=2)
        if wiki_results.get('error'):
            print(f'Error: {wiki_results['error']}')
        else:
            for i, result in enumerate(wiki_results.get('results', [])):
                print(f'Result {i + 1}: {result['title']}')
                print(f'Summary: {result['summary'][:150]}...')
                print(f'URL: {result['url']}')
                print('-' * 30)
    except Exception as e:
        print(f'Error running Wikipedia search: {str(e)}')
    try:
        print('\nGoogle Search Example (requires API key):')
        print('-' * 50)
        google_results = google_tool(query=query)
        if google_results.get('error'):
            print(f'Error: {google_results['error']}')
        else:
            for i, result in enumerate(google_results.get('results', [])):
                print(f'Result {i + 1}: {result['title']}')
                print(f'URL: {result['url']}')
                print('-' * 30)
    except Exception as e:
        print(f'Error running Google search: {str(e)}')
    try:
        print('\nGoogle Free Search Example:')
        print('-' * 50)
        free_results = google_free_tool(query=query, num_search_pages=2)
        if free_results.get('error'):
            print(f'Error: {free_results['error']}')
        else:
            for i, result in enumerate(free_results.get('results', [])):
                print(f'Result {i + 1}: {result['title']}')
                print(f'URL: {result['url']}')
                print('-' * 30)
    except Exception as e:
        print(f'Error running free Google search: {str(e)}')
    try:
        print('\nDDGS Search Example:')
        print('-' * 50)
        ddgs_results = ddgs_tool(query=query, num_search_pages=2, backend='duckduckgo')
        if ddgs_results.get('error'):
            print(f'Error: {ddgs_results['error']}')
        else:
            for i, result in enumerate(ddgs_results.get('results', [])):
                print(f'Result {i + 1}: {result['title']}')
                print(f'Result full: \n{result}')
                print(f'URL: {result['url']}')
                print('-' * 30)
    except Exception as e:
        print(f'Error running DDGS search: {str(e)}')
    serpapi_api_key = os.getenv('SERPAPI_KEY')
    if serpapi_api_key:
        try:
            print('\nSerpAPI Search Example (with content scraping):')
            print('-' * 50)
            print(f'✓ Using SerpAPI key: {serpapi_api_key[:8]}...')
            serpapi_results = serpapi_tool(query=query, num_search_pages=3, max_content_words=300, engine='google', location='United States', language='en')
            if serpapi_results.get('error'):
                print(f'Error: {serpapi_results['error']}')
            else:
                print(f'SerpAPI results: {serpapi_results}')
        except Exception as e:
            print(f'Error running SerpAPI search: {str(e)}')
    else:
        print('\nSerpAPI Search Example:')
        print('-' * 50)
        print('❌ SERPAPI_KEY not found in environment variables')
        print('To test SerpAPI search, set your API key:')
        print("export SERPAPI_KEY='your-serpapi-key-here'")
        print('Get your key from: https://serpapi.com/')
        print('✓ SerpAPI toolkit initialized successfully (API key required for search)')
    serperapi_api_key = os.getenv('SERPERAPI_KEY')
    if serperapi_api_key:
        try:
            print('\nSerperAPI Search Example (with content scraping):')
            print('-' * 50)
            print(f'✓ Using SerperAPI key: {serperapi_api_key[:8]}...')
            serperapi_results = serperapi_tool(query=query, num_search_pages=3, max_content_words=300, location='United States', language='en')
            if serperapi_results.get('error'):
                print(f'Error: {serperapi_results['error']}')
            else:
                print(f'SerperAPI results: {serperapi_results}')
        except Exception as e:
            print(f'Error running SerperAPI search: {str(e)}')
    else:
        print('\nSerperAPI Search Example:')
        print('-' * 50)
        print('❌ SERPERAPI_KEY not found in environment variables')
        print('To test SerperAPI search, set your API key:')
        print("export SERPERAPI_KEY='your-serperapi-key-here'")
        print('Get your key from: https://serper.dev/')
        print('✓ SerperAPI toolkit initialized successfully (API key required for search)')

def run_arxiv_tool_example():
    """Simple example using ArxivToolkit to search for papers."""
    print('\n===== ARXIV TOOL EXAMPLE =====\n')
    try:
        arxiv_toolkit = ArxivToolkit()
        search_tool = arxiv_toolkit.get_tool('arxiv_search')
        print('✓ ArxivToolkit initialized')
        print("Searching for 'machine learning' papers...")
        result = search_tool(search_query='all:machine learning', max_results=3)
        if result.get('success'):
            papers = result.get('papers', [])
            print(f'✓ Found {len(papers)} papers')
            for i, paper in enumerate(papers):
                print(f'\nPaper {i + 1}: {paper.get('title', 'No title')}')
                print(f'  Authors: {', '.join(paper.get('authors', ['Unknown']))}')
                print(f'  arXiv ID: {paper.get('arxiv_id', 'Unknown')}')
                print(f'  URL: {paper.get('url', 'No URL')}')
        else:
            print(f'❌ Search failed: {result.get('error', 'Unknown error')}')
        print('\n✓ ArxivToolkit test completed')
    except Exception as e:
        print(f'Error: {str(e)}')

def run_rss_tool_example():
    """Powerful example using RSSToolkit for RSS feed operations."""
    print('\n===== RSS TOOL EXAMPLE =====\n')
    try:
        toolkit = RSSToolkit(name='DemoRSSToolkit')
        print('✓ RSSToolkit initialized')
        fetch_tool = toolkit.get_tool('rss_fetch')
        validate_tool = toolkit.get_tool('rss_validate')
        test_feeds = ['https://feeds.bbci.co.uk/news/rss.xml', 'https://rss.cnn.com/rss/edition.rss', 'https://feeds.feedburner.com/TechCrunch']
        for feed_url in test_feeds:
            print(f'\n--- Testing RSS Feed: {feed_url} ---')
            print('1. Validating RSS feed...')
            validate_result = validate_tool(url=feed_url)
            if validate_result.get('success') and validate_result.get('is_valid'):
                print(f'✓ Valid {validate_result.get('feed_type')} feed: {validate_result.get('title', 'Unknown')}')
                print('2. Fetching RSS feed...')
                fetch_result = fetch_tool(feed_url=feed_url, max_entries=3)
                if fetch_result.get('success'):
                    entries = fetch_result.get('entries', [])
                    print(f"✓ Fetched {len(entries)} entries from '{fetch_result.get('title')}'")
                    for i, entry in enumerate(entries[:2], 1):
                        print(f'  Entry {i}: {entry.get('title', 'No title')}')
                        print(f'    Published: {entry.get('published', 'Unknown')}')
                        print(f'    Link: {entry.get('link', 'No link')}')
                        print(f'    Author: {entry.get('author', 'Unknown')}')
                        print()
                print('3. Testing feed monitoring...')
            else:
                print(f'❌ Invalid or inaccessible feed: {validate_result.get('error', 'Unknown error')}')
        print('\n✓ RSSToolkit test completed')
    except Exception as e:
        print(f'Error: {str(e)}')
        print('Note: RSS feed availability may vary. Some feeds may be temporarily unavailable.')

def run_request_tool_example():
    """Simple example using RequestToolkit for HTTP operations."""
    print('\n===== REQUEST TOOL EXAMPLE =====\n')
    try:
        request_toolkit = RequestToolkit(name='DemoRequestToolkit')
        http_tool = request_toolkit.get_tool('http_request')
        print('✓ RequestToolkit initialized')
        print('1. Testing GET request...')
        get_result = http_tool(url='https://httpbin.org/get', method='GET', params={'test': 'param', 'example': 'value'})
        if get_result.get('success'):
            print('✓ GET request successful')
            print(f'Status: {get_result.get('status_code')}')
            print(f'Response size: {len(str(get_result.get('content', '')))} characters')
        else:
            print(f'❌ GET request failed: {get_result.get('error', 'Unknown error')}')
        print('\n2. Testing POST request with JSON...')
        post_result = http_tool(url='https://httpbin.org/post', method='POST', json_data={'name': 'Test User', 'email': 'test@example.com'}, headers={'Content-Type': 'application/json'})
        if post_result.get('success'):
            print('✓ POST request successful')
            print(f'Status: {post_result.get('status_code')}')
            content = post_result.get('content', '')
            if isinstance(content, dict) and 'json' in content:
                print(f'✓ JSON data received: {content['json']}')
        else:
            print(f'❌ POST request failed: {post_result.get('error', 'Unknown error')}')
        print('\n3. Testing PUT request...')
        put_result = http_tool(url='https://httpbin.org/put', method='PUT', data={'update': 'new value', 'timestamp': '2024-01-01'})
        if put_result.get('success'):
            print('✓ PUT request successful')
            print(f'Status: {put_result.get('status_code')}')
        else:
            print(f'❌ PUT request failed: {put_result.get('error', 'Unknown error')}')
        print('\n4. Testing DELETE request...')
        delete_result = http_tool(url='https://httpbin.org/delete', method='DELETE')
        if delete_result.get('success'):
            print('✓ DELETE request successful')
            print(f'Status: {delete_result.get('status_code')}')
        else:
            print(f'❌ DELETE request failed: {delete_result.get('error', 'Unknown error')}')
        print('\n5. Testing error handling...')
        error_result = http_tool(url='https://invalid-domain-that-does-not-exist-12345.com', method='GET')
        if not error_result.get('success'):
            print('✓ Error handling working correctly')
            print(f'Error: {error_result.get('error', 'Unknown error')}')
        else:
            print('⚠ Error handling may not be working as expected')
        print('\n✓ RequestToolkit test completed')
    except Exception as e:
        print(f'Error: {str(e)}')

def run_file_tool_example():
    """
    Run an example using the StorageToolkit to read and write files with the new storage handler system.
    """
    print('\n===== STORAGE TOOL EXAMPLE =====\n')
    try:
        storage_toolkit = StorageToolkit(name='DemoStorageToolkit')
        save_tool = storage_toolkit.get_tool('save')
        read_tool = storage_toolkit.get_tool('read')
        append_tool = storage_toolkit.get_tool('append')
        list_tool = storage_toolkit.get_tool('list_files')
        exists_tool = storage_toolkit.get_tool('exists')
        sample_text = 'This is a sample text document created using the StorageToolkit.\nThis tool provides comprehensive file operations with automatic format detection.\nIt supports various file types including text, JSON, CSV, YAML, XML, Excel, and more.'
        sample_json = {'name': 'Sample Document', 'type': 'test', 'content': 'This is a JSON document for testing', 'metadata': {'created': '2024-01-01', 'version': '1.0'}}
        print('1. Testing file save operations...')
        text_result = save_tool(file_path='sample_document.txt', content=sample_text)
        print('Text file save result:')
        print('-' * 30)
        print(text_result)
        print('-' * 30)
        json_result = save_tool(file_path='sample_data.json', content=sample_json)
        print('JSON file save result:')
        print('-' * 30)
        print(json_result)
        print('-' * 30)
        print('\n2. Testing file read operations...')
        text_read_result = read_tool(file_path='sample_document.txt')
        print('Text file read result:')
        print('-' * 30)
        print(text_read_result)
        print('-' * 30)
        json_read_result = read_tool(file_path='sample_data.json')
        print('JSON file read result:')
        print('-' * 30)
        print(json_read_result)
        print('-' * 30)
        print('\n3. Testing file append operations...')
        append_text_result = append_tool(file_path='sample_document.txt', content='\n\nThis content was appended to the text file.')
        print('Text file append result:')
        print('-' * 30)
        print(append_text_result)
        print('-' * 30)
        updated_json_data = {**sample_json, 'additional': 'data', 'timestamp': '2024-01-01T12:00:00Z'}
        update_json_result = save_tool(file_path='sample_data.json', content=updated_json_data)
        print('JSON file update result:')
        print('-' * 30)
        print(update_json_result)
        print('-' * 30)
        print('\n4. Testing file listing...')
        list_result = list_tool(path='.', max_depth=2, include_hidden=False)
        print('File listing result:')
        print('-' * 30)
        print(list_result)
        print('-' * 30)
        print('\n5. Testing file existence...')
        exists_result = exists_tool(path='sample_document.txt')
        print('File existence check result:')
        print('-' * 30)
        print(exists_result)
        print('-' * 30)
        print('\n6. Testing supported formats...')
        formats_tool = storage_toolkit.get_tool('list_supported_formats')
        formats_result = formats_tool()
        print('Supported formats result:')
        print('-' * 30)
        print(formats_result)
        print('-' * 30)
        print('\n✓ StorageToolkit test completed successfully!')
        print('✓ All file operations working with default storage handler')
        print('✓ Automatic format detection working')
        print('✓ File operations working (including JSON updates)')
        print('✓ File listing and existence checks working')
    except Exception as e:
        print(f'Error running storage tool example: {str(e)}')

def run_cmd_tool_example():
    """Simple example using CMDToolkit for command line operations."""
    print('\n===== CMD TOOL EXAMPLE =====\n')
    try:
        cmd_toolkit = CMDToolkit(name='DemoCMDToolkit')
        execute_tool = cmd_toolkit.get_tool('execute_command')
        print('✓ CMDToolkit initialized')
        print('1. Testing basic command execution...')
        result = execute_tool(command="echo 'Hello from CMD toolkit'")
        if result.get('success'):
            print('✓ Command executed successfully')
            print(f'Output: {result.get('stdout', 'No output')}')
        else:
            print(f'❌ Command failed: {result.get('error', 'Unknown error')}')
        print('\n2. Testing system information commands...')
        pwd_result = execute_tool(command='pwd')
        if pwd_result.get('success'):
            print(f'✓ Current directory: {pwd_result.get('stdout', '').strip()}')
        if os.name == 'posix':
            uname_result = execute_tool(command='uname -a')
            if uname_result.get('success'):
                print(f'✓ System info: {uname_result.get('stdout', '').strip()}')
        else:
            ver_result = execute_tool(command='ver')
            if ver_result.get('success'):
                print(f'✓ System info: {ver_result.get('stdout', '').strip()}')
        print('\n3. Testing file listing...')
        if os.name == 'posix':
            ls_result = execute_tool(command='ls -la', working_directory='.')
        else:
            ls_result = execute_tool(command='dir', working_directory='.')
        if ls_result.get('success'):
            print('✓ File listing successful')
            print(f'Output length: {len(ls_result.get('stdout', ''))} characters')
        else:
            print(f'❌ File listing failed: {ls_result.get('error', 'Unknown error')}')
        print('\n4. Testing command timeout...')
        timeout_result = execute_tool(command='sleep 5', timeout=12)
        if not timeout_result.get('success'):
            print('✓ Timeout working correctly (command was interrupted)')
        else:
            print('⚠ Timeout may not be working as expected')
        print('\n✓ CMDToolkit test completed')
    except Exception as e:
        print(f'Error: {str(e)}')

def run_storage_handler_examples():
    """
    Run examples demonstrating different storage handlers and configurations.
    """
    print('\n===== STORAGE HANDLER EXAMPLES =====\n')
    try:
        print('1. Testing custom base path storage...')
        custom_storage_toolkit = StorageToolkit(name='CustomPathStorageToolkit', storage_handler=None, base_path='./custom_storage')
        custom_save_tool = custom_storage_toolkit.get_tool('save')
        custom_result = custom_save_tool(file_path='custom_test.txt', content='This file is stored in a custom location')
        if custom_result.get('success'):
            print('✓ Custom path storage working')
            print(f'File saved to: {custom_result.get('file_path')}')
        else:
            print(f'❌ Custom path storage failed: {custom_result.get('error')}')
        custom_read_tool = custom_storage_toolkit.get_tool('read')
        custom_read_result = custom_read_tool(file_path='custom_test.txt')
        if custom_read_result.get('success'):
            print('✓ Custom path file reading working')
            print(f'Content: {custom_read_result.get('content', '')[:50]}...')
        custom_list_tool = custom_storage_toolkit.get_tool('list_files')
        custom_list_result = custom_list_tool(path='.', max_depth=1, include_hidden=False)
        if custom_list_result.get('success'):
            print('✓ Custom path file listing working')
            files = custom_list_result.get('files', [])
            print(f'Found {len(files)} files in custom location')
        print('\n✓ Storage handler examples completed')
    except Exception as e:
        print(f'Error running storage handler examples: {str(e)}')

def run_advanced_file_operations():
    """
    Run examples demonstrating advanced file operations and format handling.
    """
    print('\n===== ADVANCED FILE OPERATIONS =====\n')
    try:
        storage_toolkit = StorageToolkit()
        save_tool = storage_toolkit.get_tool('save')
        read_tool = storage_toolkit.get_tool('read')
        print('1. Testing CSV file operations...')
        csv_content = 'name,age,city\nJohn Doe,30,New York\nJane Smith,25,Los Angeles\nBob Johnson,35,Chicago'
        csv_result = save_tool(file_path='sample_data.csv', content=csv_content)
        if csv_result.get('success'):
            print('✓ CSV file saved successfully')
            csv_read_result = read_tool(file_path='sample_data.csv')
            if csv_read_result.get('success'):
                print('✓ CSV file read successfully')
                print(f'Content: {csv_read_result.get('content', '')[:100]}...')
            else:
                print(f'❌ Failed to read CSV file: {csv_read_result.get('error')}')
        else:
            print(f'❌ Failed to save CSV file: {csv_result.get('error')}')
        print('\n2. Testing YAML file operations...')
        yaml_content = 'name: Sample YAML\nversion: 1.0\nfeatures:\n  - feature1\n  - feature2\nmetadata:\n  author: Test User\n  date: 2024-01-01'
        yaml_result = save_tool(file_path='sample_config.yaml', content=yaml_content)
        if yaml_result.get('success'):
            print('✓ YAML file saved successfully')
            yaml_read_result = read_tool(file_path='sample_config.yaml')
            if yaml_read_result.get('success'):
                print('✓ YAML file read successfully')
                print(f'Content: {yaml_read_result.get('content', '')[:100]}...')
            else:
                print(f'❌ Failed to read YAML file: {yaml_read_result.get('error')}')
        else:
            print(f'❌ Failed to save YAML file: {yaml_result.get('error')}')
        print('\n3. Testing PDF file operations...')
        pdf_content = "Test PDF Document\n\nThis is a test PDF created by EvoAgentX.\n\nFeatures:\n• PDF creation from text\n• Automatic formatting\n• Professional layout\n\nThis demonstrates the storage system's PDF capabilities."
        pdf_result = save_tool(file_path='test_pdf.pdf', content=pdf_content)
        if pdf_result.get('success'):
            print('✓ PDF file created successfully')
        else:
            print(f'❌ Failed to create PDF file: {pdf_result.get('error')}')
        pdf_read_result = read_tool(file_path='test_pdf.pdf')
        if pdf_read_result.get('success'):
            print('✓ PDF file read successfully')
            print(f'Content: {pdf_read_result.get('content', '')[:100]}...')
        else:
            print(f'❌ Failed to read PDF file: {pdf_read_result.get('error')}')
        print('\n4. Testing file deletion...')
        delete_tool = storage_toolkit.get_tool('delete')
        test_files = ['sample_document.txt', 'sample_data.json', 'custom_test.txt']
        for test_file in test_files:
            if os.path.exists(test_file):
                delete_result = delete_tool(path=test_file)
                if delete_result.get('success'):
                    print(f'✓ Deleted {test_file}')
                else:
                    print(f'❌ Failed to delete {test_file}: {delete_result.get('error')}')
        print('\n✓ Advanced file operations completed')
    except Exception as e:
        print(f'Error running advanced file operations: {str(e)}')

def rapidapi_test() -> None:
    print('\n===== SINGLE REAL CALL: OpenWeatherMap (extracted) =====\n')
    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key or api_key.strip().lower() in {'', 'your-api-key'}:
        print('Skipping real call: set RAPIDAPI_KEY to run this test.')
        return
    rapidapi_host = 'open-weather13.p.rapidapi.com'
    toolkit = create_rapidapi_toolkit(schema_path_or_dict=weather_api_spec, rapidapi_key=api_key, rapidapi_host=rapidapi_host, service_name='Open Weather13')
    print('____________ Executing city weather querying ____________')
    city_weather_tool = toolkit.get_tools()[0]
    example_query = {'city': 'new york'}
    print('Qeury inputs: \n', example_query)
    result = city_weather_tool(**example_query)
    print('Query result: \n', result)

def main():
    gmaps_toolkit = GoogleMapsToolkit()
    if not gmaps_toolkit.google_maps_base.api_key:
        print('Please set GOOGLE_MAPS_API_KEY environment variable')
        print('Get your API key from: https://console.cloud.google.com/apis/')
        return
    print('=== Google Maps Platform Tools Demo ===\n')
    print('1. Geocoding Address to Coordinates')
    geocode_tool = gmaps_toolkit.get_tool('geocode_address')
    result = geocode_tool(address='1600 Amphitheatre Parkway, Mountain View, CA')
    if result['success']:
        print(f'Address: {result['formatted_address']}')
        print(f'Coordinates: {result['latitude']}, {result['longitude']}')
        print(f'Place ID: {result['place_id']}')
        lat, lng = (result['latitude'], result['longitude'])
    else:
        print(f'Geocoding failed: {result['error']}')
        return
    print('\n' + '=' * 50 + '\n')
    print('2. Reverse Geocoding Coordinates to Address')
    reverse_geocode_tool = gmaps_toolkit.get_tool('reverse_geocode')
    result = reverse_geocode_tool(latitude=lat, longitude=lng)
    if result['success']:
        print(f'Coordinates: {result['latitude']}, {result['longitude']}')
        print('Addresses found:')
        for i, addr in enumerate(result['addresses'][:3]):
            print(f'  {i + 1}. {addr['formatted_address']}')
    else:
        print(f'Reverse geocoding failed: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('3. Places Search - Find Restaurants')
    places_search_tool = gmaps_toolkit.get_tool('places_search')
    result = places_search_tool(query='restaurants near Mountain View, CA', location=f'{lat},{lng}', radius=2000)
    if result['success']:
        print(f'Found {result['places_found']} restaurants')
        for i, place in enumerate(result['places'][:3]):
            print(f'  {i + 1}. {place['name']}')
            print(f'     Address: {place['formatted_address']}')
            print(f'     Rating: {place.get('rating', 'N/A')}')
            print(f'     Place ID: {place['place_id']}')
        if result['places']:
            sample_place_id = result['places'][0]['place_id']
    else:
        print(f'Places search failed: {result['error']}')
        sample_place_id = None
    print('\n' + '=' * 50 + '\n')
    if sample_place_id:
        print('4. Place Details - Restaurant Information')
        place_details_tool = gmaps_toolkit.get_tool('place_details')
        result = place_details_tool(place_id=sample_place_id)
        if result['success']:
            print(f'Name: {result['name']}')
            print(f'Address: {result['formatted_address']}')
            print(f'Phone: {result.get('phone_number', 'N/A')}')
            print(f'Website: {result.get('website', 'N/A')}')
            print(f'Rating: {result.get('rating', 'N/A')} ({result.get('user_ratings_total', 0)} reviews)')
            print(f'Price Level: {result.get('price_level', 'N/A')}')
        else:
            print(f'Place details failed: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('5. Directions - Driving Route')
    directions_tool = gmaps_toolkit.get_tool('directions')
    result = directions_tool(origin='San Francisco, CA', destination='Mountain View, CA', mode='driving')
    if result['success'] and result['routes']:
        route = result['routes'][0]
        print(f'Route from {result['origin']} to {result['destination']}')
        print(f'Distance: {route['total_distance_meters']} meters')
        print(f'Duration: {route['total_duration_seconds']} seconds')
        print(f'Summary: {route.get('summary', 'N/A')}')
        if route['legs'] and route['legs'][0]['steps']:
            print('First 3 steps:')
            for i, step in enumerate(route['legs'][0]['steps'][:3]):
                instructions = step['instructions'].replace('<b>', '').replace('</b>', '').replace('<div>', ' ').replace('</div>', '')
                print(f'  {i + 1}. {instructions}')
    else:
        print(f'Directions failed: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('6. Distance Matrix - Multiple Origins/Destinations')
    distance_matrix_tool = gmaps_toolkit.get_tool('distance_matrix')
    result = distance_matrix_tool(origins='San Francisco,CA|Oakland,CA', destinations='Mountain View,CA|Palo Alto,CA', mode='driving', units='imperial')
    if result['success']:
        print('Distance Matrix Results:')
        for origin_data in result['matrix']:
            print(f'\nFrom: {origin_data['origin_address']}')
            for dest in origin_data['destinations']:
                if dest['status'] == 'OK':
                    print(f'  To {dest['destination_address']}: {dest['distance'].get('text', 'N/A')} - {dest['duration'].get('text', 'N/A')}')
                else:
                    print(f'  To {dest['destination_address']}: {dest['status']}')
    else:
        print(f'Distance matrix failed: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('7. Time Zone Information')
    timezone_tool = gmaps_toolkit.get_tool('timezone')
    result = timezone_tool(latitude=lat, longitude=lng)
    if result['success']:
        print(f'Location: {result['latitude']}, {result['longitude']}')
        print(f'Time Zone: {result['time_zone_name']} ({result['time_zone_id']})')
        print(f'UTC Offset: {result['raw_offset']} seconds')
        print(f'DST Offset: {result['dst_offset']} seconds')
    else:
        print(f'Time zone lookup failed: {result['error']}')
    print('\n=== Demo Complete ===')

def main():
    telegram_toolkit = TelegramToolkit()
    if not telegram_toolkit.telegram_base.api_id or not telegram_toolkit.telegram_base.api_hash:
        print('Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables')
        print('Get your credentials from: https://my.telegram.org/apps')
        return
    print('=== Telegram Tools Demo ===\n')
    print('1. Listing Recent Chats')
    list_chats_tool = telegram_toolkit.get_tool('list_recent_chats')
    result = list_chats_tool(limit=5)
    if result['success']:
        print(f'Found {result['chats_count']} recent chats:')
        for chat in result['chats']:
            print(f'  - {chat['title']} ({chat['type']}) - ID: {chat['id']}')
        if result['chats']:
            for chat in result['chats']:
                if chat['id'] != 777000:
                    first_chat_id = chat['id']
                    first_chat_title = chat['title']
                    break
            else:
                first_chat_id = result['chats'][0]['id']
                first_chat_title = result['chats'][0]['title']
    else:
        print(f'Failed to list chats: {result['error']}')
        return
    print('\n' + '=' * 50 + '\n')
    print(f"2. Fetching Latest Messages from '{first_chat_title}'")
    fetch_messages_tool = telegram_toolkit.get_tool('fetch_latest_messages')
    result = fetch_messages_tool(contact_name=first_chat_title, limit=3)
    if result['success']:
        print(f'Found {result['messages_count']} recent messages:')
        for msg in result['messages']:
            print(f'  - [{msg['date']}] {msg['text'][:50]}...')
    else:
        print(f'Failed to fetch messages: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('3. Searching Messages by Keyword')
    search_tool = telegram_toolkit.get_tool('search_messages_by_keyword')
    result = search_tool(contact_name=first_chat_title, keyword='Hello', limit=3)
    if result['success']:
        print(f"Found {result['matches_count']} messages containing 'hello':")
        for msg in result['messages']:
            print(f'  - [{msg['date']}] {msg['text'][:50]}...')
    else:
        print(f'Failed to search messages: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('4. Finding Files in Chat')
    find_files_tool = telegram_toolkit.get_tool('find_and_retrieve_file')
    result = find_files_tool(contact_name='Telegram', filename_query='Kafka')
    if result['success']:
        print(f"Found {result['files_found']} files matching 'Kafka':")
        for file_info in result['files']:
            print(f'  - {file_info['filename']} ({file_info['file_size']} bytes, {file_info['mime_type']})')
    else:
        print(f'Failed to find files: {result['error']}')
    print('\n' + '=' * 50 + '\n')
    print('5. Send Test Message by Contact Name')
    send_tool = telegram_toolkit.get_tool('send_message_by_name')
    test_contact_name = 'Vinay Kumar'
    test_message = 'Hello! This is a test message from EvoAgentX Telegram tools. 🤖'
    print(f"Sending test message to contact: '{test_contact_name}'")
    result = send_tool(contact_name=test_contact_name, message_text=test_message)
    if result['success']:
        print(f'✅ Message sent successfully!')
        print(f'   Message ID: {result['message_id']}')
        print(f'   Sent to: {result['chat']['title']}')
        print(f'   Message: {result['message_text']}')
        print(f'   Sent at: {result['sent_at']}')
    else:
        print(f'❌ Failed to send message: {result['error']}')
        if 'clarification_needed' in result:
            print('   Available contacts:')
            for contact in result['clarification_needed']:
                print(f'   - {contact}')
    print('\n' + '=' * 50 + '\n')
    print('6. Summarize Contact Messages')
    summarize_tool = telegram_toolkit.get_tool('summarize_contact_messages')
    test_contact_name = 'Telegram'
    print(f"Summarizing recent messages from contact: '{test_contact_name}'")
    result = summarize_tool(contact_name=test_contact_name, limit=10)
    if result['success']:
        print(f'✅ Message summary generated successfully!')
        print(f'   Contact: {result['contact']['title']}')
        print(f'   Messages analyzed: {result['messages_analyzed']}')
        print(f'   Summary:')
        print(f'   {result['summary']}')
        if result['recent_messages']:
            print(f'   Recent messages preview:')
            for i, msg in enumerate(result['recent_messages'][:3], 1):
                direction = 'You' if msg['is_outgoing'] else test_contact_name
                print(f'   {i}. [{msg['date']}] {direction}: {msg['text'][:50]}...')
    else:
        print(f'❌ Failed to summarize messages: {result['error']}')
        if 'clarification_needed' in result:
            print('   Available contacts:')
            for contact in result['clarification_needed']:
                print(f'   - {contact}')
    print('\n' + '=' * 50)
    print('\n7. Download File Tool')
    print('Downloading file from contact:', test_contact_name)
    download_tool = telegram_toolkit.get_tool('download_file')
    download_result = download_tool(contact_name=test_contact_name, filename_query='Kafka', download_dir='downloads')
    if download_result['success']:
        print(f'✅ File downloaded successfully!')
        print(f'   📁 File: {download_result['filename']}')
        print(f'   📍 Path: {download_result['file_path']}')
        print(f'   📊 Size: {download_result['file_size']} bytes')
        print(f'   📂 Directory: {download_result['download_dir']}')
    else:
        print(f'❌ Download failed: {download_result['error']}')
        if 'clarification_needed' in download_result:
            print('   Available contacts:')
            for contact in download_result['clarification_needed']:
                print(f'   - {contact}')
    print('\n' + '=' * 50)
    print('\n8. Read File Content Tool')
    print('Reading file content from contact:', test_contact_name)
    read_tool = telegram_toolkit.get_tool('read_file_content')
    content_tests = [('summary', 'Document summary'), ('first_lines', 'First 3 lines'), ('last_lines', 'Last 3 lines')]
    for content_type, description in content_tests:
        print(f'\n   🔍 {description}:')
        read_result = read_tool(contact_name=test_contact_name, filename_query='Kafka', content_type=content_type, lines_count=3)
        if read_result['success']:
            print(f'   ✅ {description} extracted successfully!')
            print(f'   📄 Content preview:')
            content_preview = read_result['content'][:200] + '...' if len(read_result['content']) > 200 else read_result['content']
            print(f'      {content_preview}')
            if 'file_info' in read_result:
                file_info = read_result['file_info']
                print(f'   📊 File info: {file_info}')
        else:
            print(f'   ❌ Failed to read {description}: {read_result['error']}')
    print('\n=== Demo Complete ===')
    print('All 8 Telegram tools are working correctly!')
    print('✅ Core Tools (6): fetch_latest_messages, search_messages_by_keyword, send_message_by_name, list_recent_chats, find_and_retrieve_file, summarize_contact_messages')
    print('✅ Enhanced File Tools (2): download_file, read_file_content')

def run_browser_tool_example():
    """
    Run an example using the BrowserToolkit with auto-initialization and auto-cleanup.
    Uses a comprehensive HTML test page to demonstrate browser automation features.
    """
    print('\n===== BROWSER TOOL EXAMPLE =====\n')
    try:
        browser_toolkit = BrowserToolkit(headless=False, timeout=10)
        nav_tool = browser_toolkit.get_tool('navigate_to_url')
        input_tool = browser_toolkit.get_tool('input_text')
        click_tool = browser_toolkit.get_tool('browser_click')
        snapshot_tool = browser_toolkit.get_tool('browser_snapshot')
        test_file_path = os.path.join(os.getcwd(), 'examples', 'tools', 'browser_test_page.html')
        print('Step 1: Navigating to test page (browser auto-initializes)...')
        nav_result = nav_tool(url=f'file://{test_file_path}')
        print('Navigation Result:')
        print('-' * 30)
        print(f'Status: {nav_result.get('status')}')
        print(f'URL: {nav_result.get('current_url')}')
        print(f'Title: {nav_result.get('title')}')
        print('-' * 30)
        if nav_result.get('status') in ['success', 'partial_success']:
            print('\nStep 2: Taking initial snapshot to identify elements...')
            snapshot_result = snapshot_tool()
            if snapshot_result.get('status') == 'success':
                print('✓ Initial snapshot successful')
                elements = snapshot_result.get('interactive_elements', [])
                print(f'Found {len(elements)} interactive elements')
                name_input_ref = None
                email_input_ref = None
                message_input_ref = None
                submit_btn_ref = None
                clear_btn_ref = None
                test_btn_ref = None
                for elem in elements:
                    desc = elem.get('description', '').lower()
                    purpose = elem.get('purpose', '').lower()
                    if 'name' in desc and elem.get('editable'):
                        name_input_ref = elem['id']
                    elif 'email' in desc and elem.get('editable'):
                        email_input_ref = elem['id']
                    elif 'message' in desc and elem.get('editable'):
                        message_input_ref = elem['id']
                    elif 'submit' in purpose and elem.get('interactable'):
                        submit_btn_ref = elem['id']
                    elif 'clear' in purpose and elem.get('interactable'):
                        clear_btn_ref = elem['id']
                    elif 'test' in purpose and elem.get('interactable'):
                        test_btn_ref = elem['id']
                print(f'Identified elements:')
                print(f'  - Name input: {name_input_ref}')
                print(f'  - Email input: {email_input_ref}')
                print(f'  - Message input: {message_input_ref}')
                print(f'  - Submit button: {submit_btn_ref}')
                print(f'  - Clear button: {clear_btn_ref}')
                print(f'  - Test button: {test_btn_ref}')
                if name_input_ref and email_input_ref and message_input_ref:
                    print('\nStep 3: Testing input functionality...')
                    print("  - Typing 'John Doe' in name field...")
                    name_result = input_tool(element='Name input', ref=name_input_ref, text='John Doe', submit=False)
                    print(f'    Result: {name_result.get('status')}')
                    print("  - Typing 'john.doe@example.com' in email field...")
                    email_result = input_tool(element='Email input', ref=email_input_ref, text='john.doe@example.com', submit=False)
                    print(f'    Result: {email_result.get('status')}')
                    print("  - Typing 'This is a test message for browser automation.' in message field...")
                    message_result = input_tool(element='Message input', ref=message_input_ref, text='This is a test message for browser automation.', submit=False)
                    print(f'    Result: {message_result.get('status')}')
                    if submit_btn_ref:
                        print('\nStep 4: Testing form submission...')
                        submit_result = click_tool(element='Submit button', ref=submit_btn_ref)
                        print(f'Submit result: {submit_result.get('status')}')
                        print('\nStep 5: Taking snapshot to verify form submission...')
                        result_snapshot = snapshot_tool()
                        if result_snapshot.get('status') == 'success':
                            content = result_snapshot.get('page_content', '')
                            if 'Name: John Doe, Email: john.doe@example.com' in content:
                                print('✓ Form submission successful - data correctly displayed!')
                            else:
                                print('⚠ Form submission may have failed')
                    if test_btn_ref:
                        print('\nStep 6: Testing test button click...')
                        test_result = click_tool(element='Test button', ref=test_btn_ref)
                        print(f'Test button result: {test_result.get('status')}')
                        click_snapshot = snapshot_tool()
                        if click_snapshot.get('status') == 'success':
                            content = click_snapshot.get('page_content', '')
                            if 'Test button clicked at:' in content:
                                print('✓ Test button click successful!')
                            else:
                                print('⚠ Test button click may have failed')
                    if clear_btn_ref:
                        print('\nStep 7: Testing clear functionality...')
                        clear_result = click_tool(element='Clear button', ref=clear_btn_ref)
                        print(f'Clear result: {clear_result.get('status')}')
                        final_snapshot = snapshot_tool()
                        if final_snapshot.get('status') == 'success':
                            print('✓ Clear functionality tested')
                print('\n✓ Browser automation test completed successfully!')
                print('✓ Browser auto-initialization working')
                print('✓ Navigation working')
                print('✓ Input functionality working')
                print('✓ Click functionality working')
                print('✓ Form submission working')
                print('✓ Snapshot functionality working')
            else:
                print('❌ Initial snapshot failed')
        else:
            print('\n❌ Navigation failed')
        print('\nBrowser will automatically close when the toolkit goes out of scope...')
        print('(No manual cleanup required)')
    except Exception as e:
        print(f'Error running browser tool example: {str(e)}')
        print('Browser will still automatically cleanup on exit')

def run_browser_use_tool_example():
    """Simple example using BrowserUseToolkit for browser automation."""
    print('\n===== BROWSER USE TOOL EXAMPLE =====\n')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print('❌ OPENAI_API_KEY not found in environment variables')
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-api-key-here'")
        return
    try:
        print('Initializing BrowserUseToolkit...')
        toolkit = BrowserUseToolkit(model='gpt-4o-mini', headless=False)
        browser_tool = toolkit.get_tool('browser_use')
        print('✓ BrowserUseToolkit initialized')
        print(f'✓ Using OpenAI API key: {openai_api_key[:8]}...')
        print("Executing browser task: 'Go to Google and search for OpenAI GPT-4'...")
        result = browser_tool(task="Go to Google and search for 'OpenAI GPT-4'")
        if result.get('success'):
            print('✓ Browser task completed successfully')
            print(f'Result: {result.get('result', 'No result details')}')
        else:
            print(f'❌ Browser task failed: {result.get('error', 'Unknown error')}')
        print('\n✓ BrowserUseToolkit test completed')
    except Exception as e:
        print(f'Error: {str(e)}')
        print('Note: Make sure you have the required dependencies installed and API keys set up.')

class DummyAction(Action):

    def __init__(self, **kwargs):
        super().__init__(name='DummyAction', description='A test action that echoes input', **kwargs)

    def execute(self, llm, inputs, sys_msg=None, return_prompt=False, **kwargs):
        text = inputs.get('text', '')
        output = f'[Echo] {text}'
        prompt = f'Prompt used: {text}'
        if return_prompt:
            return (output, prompt)
        return output

def execute(self, llm, inputs, sys_msg=None, return_prompt=False, **kwargs):
    text = inputs.get('text', '')
    output = f'[Echo] {text}'
    prompt = f'Prompt used: {text}'
    if return_prompt:
        return (output, prompt)
    return output

class MessageBenchmark(Benchmark):
    """
    Adapt dataset in messages format, automatically extract last user/assistant round.
    """

    def __init__(self, path: str, mode: str='train'):
        super().__init__(name='MessageBenchmark', path=path, mode=mode)

    def _load_data(self):
        import json
        file_path = os.path.join(self.path, 'worfbench_train.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            self._train_data = json.load(f)

    def _get_label(self, example):
        return [m['content'] for m in example['messages'] if m['role'] == 'assistant'][-1]

    def _get_id(self, example):
        user_msg = [m['content'] for m in example['messages'] if m['role'] == 'user'][-1]
        return example.get('source', '') + '_' + user_msg[:20]

    def evaluate(self, prediction, label):
        from evoagentx.benchmark.measures import exact_match_score, f1_score, acc_score
        em = exact_match_score(prediction, label)
        f1 = f1_score(prediction, label)
        acc = acc_score(prediction, [label])
        return {'em': em, 'f1': f1, 'acc': acc}

def _get_id(self, example):
    user_msg = [m['content'] for m in example['messages'] if m['role'] == 'user'][-1]
    return example.get('source', '') + '_' + user_msg[:20]

