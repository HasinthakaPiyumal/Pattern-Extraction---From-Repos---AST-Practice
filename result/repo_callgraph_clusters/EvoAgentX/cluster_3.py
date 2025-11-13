# Cluster 3

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

class WorkFlowReviewer(Agent):
    """
    Placeholder for the Agent that is responsible for reviewing workflow plans and agents.
    """

    def execute(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[dict]=None, **kwargs) -> Message:
        raise NotImplementedError('WorkflowReviewer is not implemented yet.')

def execute(self, action_name: str, msgs: Optional[List[Message]]=None, action_input_data: Optional[dict]=None, **kwargs) -> Message:
    raise NotImplementedError('WorkflowReviewer is not implemented yet.')

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

def chat(self, user_prompt: str, *, conversation_id: Optional[str]=None, top_k: Optional[int]=None, metadata_filters: Optional[dict]=None, return_message: bool=True, **kwargs):
    action_input_data = {'user_prompt': user_prompt, 'conversation_id': conversation_id or self._default_conversation_id(), 'top_k': top_k if top_k is not None else 3, 'metadata_filters': metadata_filters or {}}
    msg = self.execute(action_name='MemoryAction', action_input_data=action_input_data, return_msg_type=MessageType.RESPONSE, **kwargs)
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

class MockLLM(BaseLLM):
    """Mock LLM implementation for testing purposes that passes pydantic type validation"""

    def __init__(self, config: MockLLMConfig=None, **kwargs):
        if config is None:
            config = MockLLMConfig(llm_type='MockLLM', model='mock-model', output_response=True)
        super().__init__(config, **kwargs)

    def init_model(self):
        """Initialize the mock model (no-op)"""
        pass

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        """Mock implementation of formulate_messages"""
        result = []
        for prompt in prompts:
            messages = []
            if system_messages:
                for sys_msg in system_messages:
                    messages.append({'role': 'system', 'content': sys_msg})
            messages.append({'role': 'user', 'content': prompt})
            result.append(messages)
        return result

    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """Mock implementation that returns a simple JSON response"""
        return '{"nodes": [], "edges": []}'

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """Mock implementation for batch generation"""
        return [self.single_generate(messages, **kwargs) for messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """Mock async implementation"""
        return self.single_generate(messages, **kwargs)

def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
    """Mock implementation for batch generation"""
    return [self.single_generate(messages, **kwargs) for messages in batch_messages]

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

class HITLOutsideConversationAgent(HITLBaseAgent):
    """HITL Outside Conversation Agent - support the conversation loop to modify the workflow json structure"""

    def __init__(self, name: str='HITLOutsideConversationAgent', description: str='support the conversation loop to modify the workflow json structure', **kwargs):
        super().__init__(name=name, description=description, is_human=True, **kwargs)
        self.forbidden_in_workflow = True
        action = HITLOutsideConversationAction()
        self.add_action(action)

    def get_hitl_agent_name(self) -> str:
        """get the HITL Agent name"""
        return self.name

    def execute(self, llm: BaseLLM, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        """
        redirect to the HITLOutsideConversationAction.execute
        """
        if hasattr(self, 'actions') and len(self.actions) > 0:
            if isinstance(self.actions[0], HITLOutsideConversationAction):
                return self.actions[0].execute(llm, inputs, hitl_manager, sys_msg, **kwargs)
            else:
                raise ValueError(f'The first action of {self.name} must be HITLOutsideConversationAction, but got {self.actions[0].__class__}')
        else:
            raise ValueError(f'The {self.name} has no action')

    async def async_execute(self, llm: BaseLLM, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        """
        redirect to the HITLOutsideConversationAction.async_execute
        """
        if hasattr(self, 'actions') and len(self.actions) > 0:
            if isinstance(self.actions[0], HITLOutsideConversationAction):
                return await self.actions[0].async_execute(llm, inputs, hitl_manager, sys_msg, **kwargs)
            else:
                raise ValueError(f'The first action of {self.name} must be HITLOutsideConversationAction, but got {self.actions[0].__class__}')
        else:
            raise ValueError(f'The {self.name} has no action')

    @property
    def conversation_action(self):
        """
        get the right conversation action
        """
        for action in self.actions:
            if isinstance(action, HITLOutsideConversationAction):
                return action
        raise ValueError(f'Action of class {HITLOutsideConversationAction.__name__} not found in {self}, please check the initialization of this Agent')

def execute(self, llm: BaseLLM, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
    """
        redirect to the HITLOutsideConversationAction.execute
        """
    if hasattr(self, 'actions') and len(self.actions) > 0:
        if isinstance(self.actions[0], HITLOutsideConversationAction):
            return self.actions[0].execute(llm, inputs, hitl_manager, sys_msg, **kwargs)
        else:
            raise ValueError(f'The first action of {self.name} must be HITLOutsideConversationAction, but got {self.actions[0].__class__}')
    else:
        raise ValueError(f'The {self.name} has no action')

@property
def conversation_action(self):
    """
        get the right conversation action
        """
    for action in self.actions:
        if isinstance(action, HITLOutsideConversationAction):
            return action
    raise ValueError(f'Action of class {HITLOutsideConversationAction.__name__} not found in {self}, please check the initialization of this Agent')

class HITLUserInputCollectorAgent(HITLBaseAgent):
    """HITL User Input Collector Agent - Collect user input for the HITL Interceptor"""

    def __init__(self, name: str=None, input_fields: dict=None, interaction_type: HITLInteractionType=HITLInteractionType.COLLECT_USER_INPUT, **kwargs):
        if name:
            agent_name = f'HITL_User_Input_Collector_{name}'
        else:
            pass
        super().__init__(name=agent_name, description='HITL User Input Collector - Collect predefined user inputs', is_human=True, **kwargs)
        self.interaction_type = interaction_type
        self.input_fields = input_fields or {}
        action_name_validated = False
        name_i = 0
        action_name = None
        while not action_name_validated:
            action_name = 'HITLUserInputCollectorAction' + f'_{name_i}'
            if MODULE_REGISTRY.has_module(action_name):
                continue
            else:
                action_name_validated = True
        action = HITLUserInputCollectorAction(name=action_name, agent_name=agent_name, interaction_type=interaction_type, input_fields=self.input_fields)
        self.add_action(action)

    def get_hitl_agent_name(self) -> str:
        """
        Get the name of the HITL agent. Useful when the name of HITL agent is generated dynamically.
        """
        return self.name

    def set_input_fields(self, input_fields: dict):
        """Set the input fields for user input collection"""
        self.input_fields = input_fields
        for action in self.actions:
            if isinstance(action, HITLUserInputCollectorAction):
                action.input_fields = input_fields

def set_input_fields(self, input_fields: dict):
    """Set the input fields for user input collection"""
    self.input_fields = input_fields
    for action in self.actions:
        if isinstance(action, HITLUserInputCollectorAction):
            action.input_fields = input_fields

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

def init_module(self):
    if self.task_planner is None:
        if self.llm is None:
            raise ValueError('Must provide `llm` when `task_planner` is None')
        self.task_planner = TaskPlanner(llm=self.llm)
    if self.agent_generator is None:
        if self.llm is None:
            raise ValueError('Must provide `llm` when `agent_generator` is None')
        self.agent_generator = AgentGenerator(llm=self.llm, tools=self.tools)

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

def execute(self, *args, **kwargs) -> dict:
    raise NotImplementedError(f'The execute function for {type(self).__name__} is not implemented!')

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

def init_module(self):
    if self.llm_config:
        llm_cls = MODEL_REGISTRY.get_model(self.llm_config.llm_type)
        self._llm = llm_cls(config=self.llm_config)

def execute(self, *args, **kwargs) -> dict:
    raise NotImplementedError(f'The execute function for {type(self).__name__} is not implemented!')

def async_execute(self, *args, **kwargs) -> dict:
    raise NotImplementedError(f'The async_execute function for {type(self).__name__} is not implemented!')

class TaskScheduler(Action):
    """
    Determines the next task to execute in a workflow.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name', None) if 'name' in kwargs else DEFAULT_TASK_SCHEDULER['name']
        description = kwargs.pop('description', None) if 'description' in kwargs else DEFAULT_TASK_SCHEDULER['description']
        prompt = kwargs.pop('prompt', None) if 'prompt' in kwargs else DEFAULT_TASK_SCHEDULER['prompt']
        super().__init__(name=name, description=description, prompt=prompt, outputs_format=TaskSchedulerOutput, **kwargs)
        self.max_num_turns = kwargs.get('max_num_turns', DEFAULT_TASK_SCHEDULER['max_num_turns'])

    def get_predecessor_tasks(self, graph: WorkFlowGraph, tasks: List[WorkFlowNode]) -> List[str]:
        predecessors = []
        for task in tasks:
            candidates = graph.get_node_predecessors(node=task)
            for candidate in candidates:
                if candidate not in predecessors:
                    predecessors.append(candidate)
        return predecessors

    def _handle_edge_cases(self, candidate_tasks: List[WorkFlowNode]) -> Union[TaskSchedulerOutput, None]:
        """
        Handle edge cases for task scheduling: Only one candidate task
        
        Args:
            candidate_tasks (List[WorkFlowNode]): List of candidate tasks to schedule      
            
        Returns:
            Either a TaskSchedulerOutput if a direct return is possible, or None if normal processing should continue
        """
        if len(candidate_tasks) == 1:
            task_name = candidate_tasks[0].name
            scheduled_task = TaskSchedulerOutput(decision='forward', task_name=task_name, reason=f"Only one candidate task '{task_name}' is available.")
            return scheduled_task
        return None

    def _prepare_execution(self, graph: WorkFlowGraph, env: Environment, candidate_tasks: List[WorkFlowNode]) -> Tuple[dict, str]:
        """
        Prepares common execution logic for both sync and async execute methods.
        This is only called when edge cases have been handled and we need to generate a prompt.
        
        Args:
            graph (WorkFlowGraph): The workflow graph.
            env (Environment): The execution environment.
            candidate_tasks (List[WorkFlowNode]): List of candidate tasks to schedule
            
        Returns:
            A tuple with prompt_inputs and prompt for LLM processing.
        """
        workflow_graph_representation = graph.get_workflow_description()
        execution_history = ' -> '.join(env.task_execution_history)
        predecessor_tasks = self.get_predecessor_tasks(graph=graph, tasks=candidate_tasks)
        execution_outputs = '\n\n'.join([str(msg) for msg in env.get_task_messages(tasks=predecessor_tasks)])
        candidate_tasks_info = '\n\n'.join([task.get_task_info() for task in candidate_tasks])
        prompt_inputs = {'workflow_graph_representation': workflow_graph_representation, 'execution_history': execution_history, 'execution_outputs': execution_outputs, 'candidate_tasks': candidate_tasks_info, 'max_num_turns': self.max_num_turns}
        prompt = self.prompt.format(**prompt_inputs)
        return (prompt_inputs, prompt)

    def execute(self, llm: Optional[BaseLLM]=None, graph: WorkFlowGraph=None, env: Environment=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> Union[TaskSchedulerOutput, Tuple[TaskSchedulerOutput, str]]:
        """
        Determine the next executable tasks.

        Args:
            llm (Optional[BaseLLM]): Language model to use for generation.
            graph (WorkFlowGraph): The workflow graph.
            env (Environment): The execution environment. 
            sys_msg (Optional[str]): Optional system message for the LLM.
            return_prompt (bool): Whether to return the prompt along with the output.
        
        Returns:
            Union[TaskSchedulerOutput, Tuple[TaskSchedulerOutput, str]]: The scheduled task and optionally the prompt.
        """
        assert graph is not None and env is not None, "must provide 'graph' and 'env' when executing TaskScheduler"
        candidate_tasks: List[WorkFlowNode] = graph.next()
        if not candidate_tasks:
            return None
        edge_case_result = self._handle_edge_cases(candidate_tasks)
        if edge_case_result is not None:
            return (edge_case_result, None) if return_prompt else edge_case_result
        _, prompt = self._prepare_execution(graph, env, candidate_tasks)
        scheduled_task = llm.generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format)
        if return_prompt:
            return (scheduled_task, prompt)
        return scheduled_task

    async def async_execute(self, llm: Optional[BaseLLM]=None, graph: WorkFlowGraph=None, env: Environment=None, sys_msg: Optional[str]=None, return_prompt: bool=False, **kwargs) -> Union[TaskSchedulerOutput, Tuple[TaskSchedulerOutput, str]]:
        """
        Asynchronously determine the next executable tasks.

        Args:
            llm (Optional[BaseLLM]): Language model to use for generation.
            graph (WorkFlowGraph): The workflow graph.
            env (Environment): The execution environment. 
            sys_msg (Optional[str]): Optional system message for the LLM.
            return_prompt (bool): Whether to return the prompt along with the output.
        
        Returns:
            Union[TaskSchedulerOutput, Tuple[TaskSchedulerOutput, str]]: The scheduled task and optionally the prompt.
        """
        assert graph is not None and env is not None, "must provide 'graph' and 'env' when executing TaskScheduler"
        candidate_tasks: List[WorkFlowNode] = graph.next()
        if not candidate_tasks:
            return None
        edge_case_result = self._handle_edge_cases(candidate_tasks)
        if edge_case_result is not None:
            return (edge_case_result, None) if return_prompt else edge_case_result
        _, prompt = self._prepare_execution(graph, env, candidate_tasks)
        scheduled_task = await llm.async_generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format)
        if return_prompt:
            return (scheduled_task, prompt)
        return scheduled_task

def get_predecessor_tasks(self, graph: WorkFlowGraph, tasks: List[WorkFlowNode]) -> List[str]:
    predecessors = []
    for task in tasks:
        candidates = graph.get_node_predecessors(node=task)
        for candidate in candidates:
            if candidate not in predecessors:
                predecessors.append(candidate)
    return predecessors

class NextAction(LLMOutputParser):
    agent: Optional[str] = Field(default=None, description='The name of the selected agent responsible for executing the next action in the workflow.')
    action: Optional[str] = Field(default=None, description='The name of the action that the selected agent will execute to continue progressing the subtask.')
    reason: Optional[str] = Field(default=None, description='The justification for selecting this agent and action, explaining how it contributes to subtask execution based on workflow requirements and execution history.')
    action_graph: Optional[ActionGraph] = Field(default=None, description='The predefined action graph to be executed.')

    def to_str(self, **kwargs) -> str:
        if self.agent is not None and self.action is not None:
            return f"Based on the tasks' execution results, the next action to be executed is the '{self.action}' action of '{self.agent}' agent."
        elif self.action_graph is not None:
            return f"The predefined action graph '{type(self.action_graph).__name__}' will be executed."
        else:
            raise ValueError('must provide either both agent (str) and action (str), or action_graph (ActionGraph).')

def to_str(self, **kwargs) -> str:
    if self.agent is not None and self.action is not None:
        return f"Based on the tasks' execution results, the next action to be executed is the '{self.action}' action of '{self.agent}' agent."
    elif self.action_graph is not None:
        return f"The predefined action graph '{type(self.action_graph).__name__}' will be executed."
    else:
        raise ValueError('must provide either both agent (str) and action (str), or action_graph (ActionGraph).')

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

def check_candidate_action(self, task_name: str, actions: List[str], agent_actions_map: Dict[str, List[str]]):
    unknown_actions = []
    merged_actions = set(chain.from_iterable(agent_actions_map.values()))
    for action in actions:
        if action not in merged_actions:
            unknown_actions.append(action)
    if unknown_actions:
        raise ValueError(f'Unknown actions: {unknown_actions} specified in the `next_actions`. All available actions defined for the task ({task_name}) are {merged_actions}.')

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

def check_method_return(method_name, result):
    if not isinstance(result, dict):
        raise TypeError(f'{method_name} must return a dictionary, got {type(result)}')
    missing_outputs = output_param_names - set(result.keys())
    if missing_outputs:
        raise ValueError(f'{method_name} return value is missing required outputs: {missing_outputs}')
    return result

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

def format_action_graph(action_graph: ActionGraph) -> str:
    if action_graph is None:
        return '  - None'
    return type(action_graph).__name__

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

def render_constraints(self) -> str:
    if not self.constraints:
        return ''
    if isinstance(self.constraints, list):
        constraints_str = '\n'.join((f'- {c}' for c in self.constraints))
    else:
        constraints_str = self.constraints
    return f'### Constraints\nYou must follow these rules or constraints when generating your output:\n{constraints_str}\n'

def format(self, inputs_format: Optional[Type[LLMOutputParser]]=None, outputs_format: Optional[Type[LLMOutputParser]]=None, values: Optional[dict]=None, parse_mode: Optional[str]='title', title_format: Optional[str]='## {title}', output_format: Optional[str]=None, **kwargs) -> str:
    raise NotImplementedError(f'`format` method is not implemented for `{self.__class__.__name__}`.')

class PyObjectId(ObjectId):

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(cls.validate, core_schema.str_schema())

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return ObjectId(v)

@classmethod
def validate(cls, v):
    if not ObjectId.is_valid(v):
        raise ValueError('Invalid ObjectId')
    return ObjectId(v)

class PyObjectId(ObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')

@classmethod
def validate(cls, v):
    if not ObjectId.is_valid(v):
        raise ValueError('Invalid ObjectId')
    return ObjectId(v)

class AgentConfig(BaseModel):
    """Base configuration for an LLM agent."""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key_env_var: Optional[str] = None
    system_prompt: Optional[str] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Temperature must be between 0 and 1')
        return v

@validator('temperature')
def validate_temperature(cls, v):
    if v < 0 or v > 1:
        raise ValueError('Temperature must be between 0 and 1')
    return v

def dfs_get_deps(node: Node, deps: Set[str]) -> None:
    for child in node.children:
        if child.type == NodeType.IDENTIFIER.value:
            deps.add(child.text.decode('utf8'))
        else:
            dfs_get_deps(child, deps)

def get_deps(nodes: List[Tuple[str, Node]]) -> Dict[str, Set[str]]:

    def dfs_get_deps(node: Node, deps: Set[str]) -> None:
        for child in node.children:
            if child.type == NodeType.IDENTIFIER.value:
                deps.add(child.text.decode('utf8'))
            else:
                dfs_get_deps(child, deps)
    name2deps = {}
    for name, node in nodes:
        deps = set()
        dfs_get_deps(node, deps)
        name2deps[name] = deps
    return name2deps

def check_input_placeholders(instruction: str, input_names: list[str], key: str):
    placeholders = set(re.findall('\\{(\\w+)\\}', instruction))
    input_names_set = set(input_names or [])
    missing = placeholders - input_names_set
    if missing:
        warnings.warn(f'[{key}] Missing input_names for placeholders in instruction: {missing}')

def _parse_type_node(node, names=None) -> Any:
    """Recursively parse an AST node representing a type annotation.

    This function converts Python's Abstract Syntax Tree (AST) nodes into actual Python types.
    It's used to parse type annotations in signature strings like "x: List[int] -> y: str".

    Examples:
        - For "x: int", the AST node represents 'int' and returns the int type
        - For "x: List[str]", it processes a subscript node to return typing.List[str]
        - For "x: Optional[int]", it handles the Union type to return Optional[int]
        - For "x: MyModule.CustomType", it processes attribute access to return the actual type

    Args:
        node: An AST node from Python's ast module, representing a type annotation.
            Common node types include:
            - ast.Name: Simple types like 'int', 'str'
            - ast.Attribute: Nested types like 'typing.List'
            - ast.Subscript: Generic types like 'List[int]'
        names: Optional dictionary mapping type names to their actual type objects.
            Defaults to Python's typing module contents plus NoneType.

    Returns:
        The actual Python type represented by the AST node.

    Raises:
        ValueError: If the AST node represents an unknown or invalid type annotation.
    """
    if names is None:
        names = dict(typing.__dict__)
        names['NoneType'] = type(None)

    def resolve_name(type_name: str):
        if type_name in names:
            return names[type_name]
        builtin_types = [int, str, float, bool, list, tuple, dict, set, frozenset, complex, bytes, bytearray]
        for t in builtin_types:
            if t.__name__ == type_name:
                return t
        try:
            mod = importlib.import_module(type_name)
            names[type_name] = mod
            return mod
        except ImportError:
            pass
        raise ValueError(f'Unknown name: {type_name}')
    if isinstance(node, ast.Module):
        if len(node.body) != 1:
            raise ValueError(f'Code is not syntactically valid: {ast.dump(node)}')
        return _parse_type_node(node.body[0], names)
    if isinstance(node, ast.Expr):
        return _parse_type_node(node.value, names)
    if isinstance(node, ast.Name):
        return resolve_name(node.id)
    if isinstance(node, ast.Attribute):
        base = _parse_type_node(node.value, names)
        attr_name = node.attr
        if hasattr(base, attr_name):
            return getattr(base, attr_name)
        else:
            raise ValueError(f'Unknown attribute: {attr_name} on {base}')
    if isinstance(node, ast.Subscript):
        base_type = _parse_type_node(node.value, names)
        slice_node = node.slice
        if isinstance(slice_node, ast.Index):
            slice_node = slice_node.value
        if isinstance(slice_node, ast.Tuple):
            arg_types = tuple((_parse_type_node(elt, names) for elt in slice_node.elts))
        else:
            arg_types = (_parse_type_node(slice_node, names),)
        if base_type is typing.Union:
            return typing.Union[arg_types]
        if base_type is typing.Optional:
            if len(arg_types) != 1:
                raise ValueError('Optional must have exactly one type argument')
            return typing.Optional[arg_types[0]]
        return base_type[arg_types]
    if isinstance(node, ast.Tuple):
        return tuple((_parse_type_node(elt, names) for elt in node.elts))
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and (node.func.id == 'Field'):
        keys = [kw.arg for kw in node.keywords]
        values = []
        for kw in node.keywords:
            if isinstance(kw.value, ast.Constant):
                values.append(kw.value.value)
            else:
                values.append(_parse_type_node(kw.value, names))
        return Field(**dict(zip(keys, values)))
    raise ValueError(f'Failed to parse string-base Signature due to unhandled AST node type in annotation: {ast.dump(node)}. Please consider using class-based DSPy Signatures instead.')

def _parse_signature(signature: str) -> Dict[str, Tuple[Type, Field]]:
    if signature.count('->') != 1:
        raise ValueError(f"Invalid signature format: '{signature}', must contain exactly one '->'.")
    inputs_str, outputs_str = signature.split('->')
    fields = {}
    for field_name, field_type in _parse_field_string(inputs_str):
        fields[field_name] = (field_type, InputField())
    for field_name, field_type in _parse_field_string(outputs_str):
        fields[field_name] = (field_type, OutputField())
    return fields

def make_signature(signature: Union[str, Dict[str, Tuple[type, FieldInfo]]], instructions: Optional[str]=None, signature_name: str='StringSignature', extra_fields: Optional[Dict[str, Tuple[type, FieldInfo]]]=None) -> Type[Signature]:
    """Create a new Signature subclass with the specified fields and instructions."""
    fields = _parse_signature(signature) if isinstance(signature, str) else signature
    fixed_fields = {}
    for name, type_field in fields.items():
        if not isinstance(name, str):
            raise ValueError(f'Field names must be strings, but received: {name}.')
        if isinstance(type_field, FieldInfo):
            type_ = type_field.annotation
            field = type_field
        else:
            if not isinstance(type_field, tuple):
                raise ValueError(f'Field values must be tuples, but received: {type_field}.')
            type_, field = type_field
        if type_ is None:
            type_ = str
        if not isinstance(type_, (type, typing._GenericAlias, types.GenericAlias, typing._SpecialForm)):
            raise ValueError(f'Field types must be types, but received: {type_} of type {type(type_)}.')
        if not isinstance(field, FieldInfo):
            raise ValueError(f'Field values must be Field instances, but received: {field}.')
        fixed_fields[name] = (type_, field)
    if extra_fields:
        fixed_fields.update(extra_fields)
    if instructions is None:
        sig = Signature(signature, '')
        instructions = _default_instructions(sig)
    return create_model(signature_name, __base__=Signature, __doc__=instructions, **fixed_fields)

def signature_from_registry(registry: MiproRegistry) -> Dict[str, Type[Signature]]:
    signature_dict = {}
    signature_name2register_name = {}
    for key in registry.names():
        registered_element: Union[str, PromptTemplate] = registry.get(key)
        input_names = registry.get_input_names(key)
        output_names = registry.get_output_names(key)
        sig = {}
        if isinstance(registered_element, str):
            instructions = registered_element
        elif isinstance(registered_element, PromptTemplate):
            instructions = registered_element.instruction
        check_input_placeholders(instructions, input_names, key)
        for name in input_names:
            input_desc = registry.get_input_desc(key, name)
            if input_desc:
                sig[name] = (str, InputField(desc=input_desc))
            else:
                sig[name] = (str, InputField(desc=f'The Input for prompt `{key}`.'))
        for name in output_names:
            output_desc = registry.get_output_desc(key, name)
            if output_desc:
                sig[name] = (str, OutputField(desc=output_desc))
            else:
                sig[name] = (str, OutputField(desc=f'The Output for prompt `{key}`.'))
        if is_valid_identifier(key):
            signature_name = f'{key}Signature'
        else:
            print(f'Warning: The key `{key}` is not a valid identifier, so we will add an underscore to it.')
            signature_name = f'DefaultSignature_{len(signature_dict)}'
        signature_class = make_signature(signature=sig, instructions=instructions, signature_name=signature_name)
        signature_class.__pydantic_extra__ = {'register_name': key}
        signature_dict[signature_name] = signature_class
        signature_name2register_name[signature_name] = key
    return (signature_dict, signature_name2register_name)

def build_signature_class(registry: ParamRegistry, input_descs: Optional[Dict[str, str]]=None, output_name: str='score', output_desc: str='Final evaluation score of the agent output', output_type: type=float):
    """
    unused function
    Dynamically builds a DSPy Signature class based on a parameter registry.
    
    This function creates a new DSPy Signature class that defines input and output fields
    based on the parameters in the registry. Each parameter becomes an input field in the
    signature, and an additional output field is added for the evaluation score.
    
    Parameters
    ----------
    registry : ParamRegistry
        Registry containing the tunable parameters that will become input fields
    input_descs : Optional[Dict[str, str]], default=None
        Optional descriptions for input parameters. Keys are parameter names,
        values are their descriptions. If not provided for a parameter,
        a default description will be generated.
    output_name : str, default="score"
        Name of the output field in the signature
    output_desc : str, default="Final evaluation score of the agent output"
        Description of the output field
    output_type : type, default=float
        Type annotation for the output field
        
    Returns
    -------
    type
        A new DSPy Signature subclass with dynamically defined input and output fields
        
    Examples
    --------
    >>> registry = ParamRegistry()
    >>> registry.register("temperature", 0.7)
    >>> signature = build_signature_class(
    ...     registry,
    ...     input_descs={"temperature": "Sampling temperature"}
    ... )
    """
    input_descs = input_descs or {}
    fields = registry.names()
    annotations = {}
    class_namespace = {'__doc__': 'Auto-generated signature class.'}
    for name in fields:
        annotations[name] = str
        class_namespace[name] = InputField(desc=input_descs.get(name, f'Tunable parameter: {name}'))
    annotations[output_name] = output_type
    class_namespace[output_name] = OutputField(desc=output_desc)
    class_namespace['__annotations__'] = annotations

    class PromptTuningSignature(Signature):
        __doc__ = class_namespace['__doc__']
        __annotations__ = annotations
        for k, v in class_namespace.items():
            if k not in ('__doc__', '__annotations__'):
                locals()[k] = v
    return PromptTuningSignature

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

def describe(self) -> Dict[str, Dict[str, Any]]:
    """
        Returns a dict of all fields and their metadata, including input/output names if present.
        """
    result = {}
    for name, field in self.fields.items():
        result[name] = {'value': field.get(), 'input_names': getattr(field, 'input_names', None), 'output_names': getattr(field, 'output_names', None), 'input_descs': getattr(field, 'input_descs', {}), 'output_descs': getattr(field, 'output_descs', {})}
    return result

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

def _load_operator_description(self, id: int, operator_name: str, llm: BaseLLM) -> str:
    if operator_name not in OPERATOR_MAP:
        raise ValueError(f'Operator {operator_name} not Found in OPERATOR_MAP! Available operators: {OPERATOR_MAP.keys()}')
    operator: Operator = OPERATOR_MAP[operator_name](llm=llm)
    return f'{id}. {operator_name}: {operator.description}, with interface {operator.interface}).'

class StorageBase(BaseModule, ABC):
    """
    Abstract base class for comprehensive storage operations supporting various file types.
    Provides unified interface for local and remote storage operations.
    """

    def __init__(self, base_path: str='.', **kwargs):
        """
        Initialize the StorageBase with configuration options.
        
        Args:
            base_path (str): Base directory for storage operations (default: current directory)
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(**kwargs)
        self.base_path = base_path
        self.appendable_formats = {'.txt': self._append_text, '.json': self._append_json, '.csv': self._append_csv, '.yaml': self._append_yaml, '.yml': self._append_yaml, '.pickle': self._append_pickle, '.xlsx': self._append_excel}
        self._initialize_storage()

    @abstractmethod
    def _initialize_storage(self):
        """
        Initialize storage-specific setup. Override in subclasses for storage-specific initialization.
        """
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
    def _list_raw(self, path: str=None, **kwargs) -> List[Dict[str, Any]]:
        """List files and directories - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _exists_raw(self, path: str) -> bool:
        """Check if path exists - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _create_directory_raw(self, path: str) -> bool:
        """Create directory - must be implemented by subclasses"""
        pass

    def translate_in(self, file_path: str) -> str:
        """
        Translate input file path by combining it with base_path.
        This method takes a user-provided path and converts it to the full system path.
        
        Args:
            file_path (str): User-provided file path (can be relative or absolute)
            
        Returns:
            str: Full system path combining base_path and file_path
        """
        if os.path.isabs(file_path):
            return file_path
        if hasattr(self, 'bucket_name') and hasattr(self, 'supabase'):
            if self.base_path.startswith('/'):
                clean_base = self.base_path.lstrip('/')
                if clean_base:
                    return f'{clean_base}/{file_path}'
                else:
                    return file_path
            else:
                return f'{self.base_path}/{file_path}'
        else:
            combined_path = os.path.join(self.base_path, file_path)
            normalized_path = os.path.normpath(combined_path)
            return normalized_path

    def translate_out(self, full_path: str) -> str:
        """
        Translate output full path by removing the base_path prefix.
        This method takes a full system path and converts it back to the user-relative path.
        
        Args:
            full_path (str): Full system path
            
        Returns:
            str: User-relative path with base_path removed
        """
        if self.base_path in ['.', '', None]:
            return full_path
        if hasattr(self, 'bucket_name') and hasattr(self, 'supabase'):
            if self.base_path.startswith('/'):
                clean_base = self.base_path.lstrip('/')
            else:
                clean_base = self.base_path
            if clean_base and full_path.startswith(f'{clean_base}/'):
                relative_path = full_path[len(f'{clean_base}/'):]
                return relative_path
            elif clean_base and full_path == clean_base:
                return ''
            else:
                return full_path
        else:
            base_abs = os.path.abspath(self.base_path)
            full_abs = os.path.abspath(full_path)
            if full_abs.startswith(base_abs):
                relative_path = full_abs[len(base_abs):]
                if relative_path.startswith(os.sep):
                    relative_path = relative_path[1:]
                return relative_path
            return full_path

    def get_file_type(self, file_path: str) -> str:
        """Get the file extension from a file path"""
        return Path(file_path).suffix.lower()

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive information about a file"""
        try:
            target_path = self.translate_in(file_path)
            if not self._exists_raw(target_path):
                return {'success': False, 'error': f'File {file_path} does not exist'}
            return {'success': True, 'file_path': target_path, 'file_name': Path(target_path).name, 'file_extension': Path(target_path).suffix.lower(), 'exists': True}
        except Exception as e:
            logger.error(f'Error getting file info for {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory"""
        try:
            target_path = self.translate_in(path)
            success = self._create_directory_raw(target_path)
            if success:
                return {'success': True, 'path': target_path, 'message': 'Directory created successfully'}
            else:
                return {'success': False, 'error': 'Failed to create directory', 'path': target_path}
        except Exception as e:
            logger.error(f'Error creating directory {path}: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

    def exists(self, path: str) -> bool:
        """Check if path exists"""
        target_path = self.translate_in(path)
        return self._exists_raw(target_path)

    def delete(self, path: str) -> Dict[str, Any]:
        """Delete file or directory"""
        try:
            target_path = self.translate_in(path)
            success = self._delete_raw(target_path)
            if success:
                return {'success': True, 'path': target_path, 'message': 'Deleted successfully'}
            else:
                return {'success': False, 'error': 'Failed to delete', 'path': target_path}
        except Exception as e:
            logger.error(f'Error deleting {path}: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

    def move(self, source: str, destination: str) -> Dict[str, Any]:
        """Move/rename file or directory"""
        try:
            resolved_source = self.translate_in(source)
            resolved_destination = self.translate_in(destination)
            content = self._read_raw(resolved_source)
            success = self._write_raw(resolved_destination, content)
            if success:
                self._delete_raw(resolved_source)
                return {'success': True, 'source': resolved_source, 'destination': resolved_destination, 'message': 'Moved successfully'}
            else:
                return {'success': False, 'error': 'Failed to write to destination', 'source': resolved_source, 'destination': resolved_destination}
        except Exception as e:
            logger.error(f'Error moving {source} to {destination}: {str(e)}')
            return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

    def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy file"""
        try:
            resolved_source = self.translate_in(source)
            resolved_destination = self.translate_in(destination)
            content = self._read_raw(resolved_source)
            success = self._write_raw(resolved_destination, content)
            if success:
                return {'success': True, 'source': resolved_source, 'destination': resolved_destination, 'message': 'Copied successfully'}
            else:
                return {'success': False, 'error': 'Failed to write to destination', 'source': resolved_source, 'destination': resolved_destination}
        except Exception as e:
            logger.error(f'Error copying {source} to {destination}: {str(e)}')
            return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

    def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        """List files and directories"""
        try:
            target_path = self.translate_in(path) if path else str(self.base_path)
            items = self._list_raw(target_path, max_depth=max_depth, include_hidden=include_hidden)
            return {'success': True, 'path': target_path, 'items': items, 'total_count': len(items)}
        except Exception as e:
            logger.error(f'Error listing {path}: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

    def save(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """
        Save content to a file with automatic format detection.
        This method replaces the old save method with the improved create_file logic.
        
        Args:
            file_path (str): Path where the file should be saved
            content (Any): Content to save to the file
            **kwargs: Additional arguments for file creation (encoding, format, etc.)
            
        Returns:
            Dict[str, Any]: Result of the operation with success status and details
        """
        try:
            file_extension = self.get_file_type(file_path)
            target_file_path = self.translate_in(file_path)
            if file_extension == '.json':
                return self._save_json(target_file_path, content, **kwargs)
            elif file_extension in ['.txt', '.md', '.log']:
                return self._save_text(target_file_path, content, **kwargs)
            elif file_extension == '.csv':
                return self._save_csv(target_file_path, content, **kwargs)
            elif file_extension in ['.yaml', '.yml']:
                return self._save_yaml(target_file_path, content, **kwargs)
            elif file_extension == '.xml':
                return self._save_xml(target_file_path, content, **kwargs)
            elif file_extension == '.xlsx':
                return self._save_excel(target_file_path, content, **kwargs)
            elif file_extension == '.pickle':
                return self._save_pickle(target_file_path, content, **kwargs)
            elif file_extension == '.pdf':
                return self._save_pdf(target_file_path, content, **kwargs)
            elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
                return self._save_image(target_file_path, content, **kwargs)
            else:
                if isinstance(content, str):
                    content_bytes = content.encode(kwargs.get('encoding', 'utf-8'))
                elif isinstance(content, bytes):
                    content_bytes = content
                else:
                    content_bytes = str(content).encode(kwargs.get('encoding', 'utf-8'))
                success = self._write_raw(target_file_path, content_bytes, **kwargs)
                if success:
                    return {'success': True, 'message': f"File '{file_path}' saved successfully", 'file_path': file_path, 'full_path': target_file_path, 'size': len(content_bytes)}
                else:
                    return {'success': False, 'message': f"Failed to save file '{file_path}'", 'file_path': file_path, 'full_path': target_file_path}
        except Exception as e:
            logger.error(f'Error saving file {file_path}: {str(e)}')
            return {'success': False, 'message': f'Error saving file: {str(e)}', 'file_path': file_path}

    def read(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read content from a file with automatic format detection"""
        try:
            target_file_path = self.translate_in(file_path)
            file_extension = Path(target_file_path).suffix.lower()
            if file_extension == '.json':
                return self._read_json(target_file_path, **kwargs)
            elif file_extension in ['.yaml', '.yml']:
                return self._read_yaml(target_file_path, **kwargs)
            elif file_extension == '.csv':
                return self._read_csv(target_file_path, **kwargs)
            elif file_extension == '.xlsx':
                return self._read_excel(target_file_path, **kwargs)
            elif file_extension == '.xml':
                return self._read_xml(target_file_path, **kwargs)
            elif file_extension == '.pickle':
                return self._read_pickle(target_file_path, **kwargs)
            elif file_extension == '.pdf':
                return self._read_pdf(target_file_path, **kwargs)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                return self._read_image(target_file_path, **kwargs)
            else:
                return self._read_text(target_file_path, **kwargs)
        except Exception as e:
            logger.error(f'Error reading {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def append(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to a file (only for supported formats)"""
        try:
            target_file_path = self.translate_in(file_path)
            file_extension = Path(target_file_path).suffix.lower()
            if file_extension in self.appendable_formats:
                return self.appendable_formats[file_extension](target_file_path, content, **kwargs)
            else:
                return {'success': False, 'error': f'Append not supported for {file_extension} files'}
        except Exception as e:
            logger.error(f'Error appending to {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_text(self, file_path: str, content: Any, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
        """Save text content to a file"""
        try:
            if isinstance(content, str):
                content_bytes = content.encode(encoding)
            else:
                content_bytes = str(content).encode(encoding)
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'File saved to {file_path}', 'file_path': file_path, 'content_length': len(content_bytes)}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving text file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_text(self, file_path: str, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
        """Read text content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content = content_bytes.decode(encoding)
            return {'success': True, 'content': content, 'file_path': file_path, 'content_length': len(content)}
        except Exception as e:
            logger.error(f'Error reading text file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_text(self, file_path: str, content: str, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
        """Append text content to a file"""
        try:
            content_bytes = str(content).encode(encoding)
            existing_bytes = b''
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
            combined_bytes = existing_bytes + content_bytes
            success = self._write_raw(file_path, combined_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to text file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_json(self, file_path: str, content: Any, indent: int=2, **kwargs) -> Dict[str, Any]:
        """Save JSON content to a file"""
        try:
            if isinstance(content, str):
                json.loads(content)
                json_content = content
            else:
                json_content = json.dumps(content, indent=indent, ensure_ascii=False)
            content_bytes = json_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'JSON file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving JSON file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_json(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read JSON content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            content = json.loads(content_str)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading JSON file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_json(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to JSON file (for arrays)"""
        try:
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_str = existing_bytes.decode('utf-8')
                existing_content = json.loads(existing_str)
            if isinstance(existing_content, list):
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            elif isinstance(existing_content, dict):
                if isinstance(content, dict):
                    existing_content.update(content)
                else:
                    return {'success': False, 'error': 'Cannot append non-dict to JSON dict'}
            else:
                existing_content = [existing_content]
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            json_content = json.dumps(existing_content, indent=2, ensure_ascii=False)
            content_bytes = json_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to JSON file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to JSON file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_csv(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save CSV content to a file - handles both raw CSV strings and structured data"""
        try:
            if not content:
                return {'success': False, 'error': 'No content to save'}
            from io import StringIO
            csv_buffer = StringIO()
            if isinstance(content, str):
                csv_content = content
                rows = content.count('\n')
            elif isinstance(content, list) and content and isinstance(content[0], dict):
                fieldnames = content[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(content)
                csv_content = csv_buffer.getvalue()
                rows = len(content)
            elif isinstance(content, list) and content and isinstance(content[0], list):
                writer = csv.writer(csv_buffer)
                writer.writerows(content)
                csv_content = csv_buffer.getvalue()
                rows = len(content)
            else:
                return {'success': False, 'error': 'CSV content must be a string, list of dictionaries, or list of lists'}
            content_bytes = csv_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'CSV file saved to {file_path}', 'file_path': file_path, 'rows': rows}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving CSV file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_csv(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read CSV content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            from io import StringIO
            reader = csv.DictReader(StringIO(content_str))
            content = list(reader)
            return {'success': True, 'content': content, 'file_path': file_path, 'rows': len(content)}
        except Exception as e:
            logger.error(f'Error reading CSV file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_csv(self, file_path: str, content: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Append content to CSV file"""
        try:
            if not content:
                return {'success': False, 'error': 'No content to append'}
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_str = existing_bytes.decode('utf-8')
                from io import StringIO
                reader = csv.DictReader(StringIO(existing_str))
                existing_content = list(reader)
            combined_content = existing_content + content
            from io import StringIO
            csv_buffer = StringIO()
            if combined_content:
                fieldnames = combined_content[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(combined_content)
            csv_content = csv_buffer.getvalue()
            content_bytes = csv_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to CSV file {file_path}', 'file_path': file_path, 'appended_rows': len(content)}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to CSV file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_yaml(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save YAML content to a file"""
        try:
            yaml_content = yaml.dump(content, default_flow_style=False, allow_unicode=True)
            content_bytes = yaml_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'YAML file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving YAML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_yaml(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read YAML content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            content = yaml.safe_load(content_str)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading YAML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_yaml(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to YAML file (for lists)"""
        try:
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_str = existing_bytes.decode('utf-8')
                existing_content = yaml.safe_load(existing_str) or []
            if isinstance(existing_content, list):
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            elif isinstance(existing_content, dict):
                if isinstance(content, dict):
                    existing_content.update(content)
                else:
                    return {'success': False, 'error': 'Cannot append non-dict to YAML dict'}
            else:
                existing_content = [existing_content]
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            yaml_content = yaml.dump(existing_content, default_flow_style=False, allow_unicode=True)
            content_bytes = yaml_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to YAML file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to YAML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_xml(self, file_path: str, content: Any, root_tag: str='root', **kwargs) -> Dict[str, Any]:
        """Save XML content to a file"""
        try:
            if isinstance(content, str):
                try:
                    ET.fromstring(content)
                    xml_content = content
                except ET.ParseError:
                    root = ET.Element(root_tag)
                    root.text = content
                    xml_content = ET.tostring(root, encoding='unicode')
            elif isinstance(content, dict):

                def dict_to_xml(data, root):
                    for key, value in data.items():
                        child = ET.SubElement(root, key)
                        if isinstance(value, dict):
                            dict_to_xml(value, child)
                        else:
                            child.text = str(value)
                root = ET.Element(root_tag)
                dict_to_xml(content, root)
                xml_content = ET.tostring(root, encoding='unicode')
            else:
                root = ET.Element(root_tag)
                root.text = str(content)
                xml_content = ET.tostring(root, encoding='unicode')
            content_bytes = xml_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'XML file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving XML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_xml(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read XML content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            root = ET.fromstring(content_str)

            def xml_to_dict(element):
                result = {}
                for child in element:
                    if len(child) == 0:
                        result[child.tag] = child.text
                    else:
                        result[child.tag] = xml_to_dict(child)
                return result
            content = xml_to_dict(root)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading XML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_excel(self, file_path: str, content: List[List[Any]], sheet_name: str='Sheet1', **kwargs) -> Dict[str, Any]:
        """Save Excel content to a file"""
        if not EXCEL_AVAILABLE:
            return {'success': False, 'error': 'openpyxl library not available'}
        try:
            from io import BytesIO
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = sheet_name
            for row in content:
                worksheet.append(row)
            buffer = BytesIO()
            workbook.save(buffer)
            content_bytes = buffer.getvalue()
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Excel file saved to {file_path}', 'file_path': file_path, 'rows': len(content)}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving Excel file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_excel(self, file_path: str, sheet_name: str=None, **kwargs) -> Dict[str, Any]:
        """Read Excel content from a file"""
        if not EXCEL_AVAILABLE:
            return {'success': False, 'error': 'openpyxl library not available'}
        try:
            from io import BytesIO
            content_bytes = self._read_raw(file_path, **kwargs)
            workbook = load_workbook(BytesIO(content_bytes), data_only=True)
            sheet_names = workbook.sheetnames
            if sheet_name is None:
                sheet_name = sheet_names[0]
            if sheet_name not in sheet_names:
                return {'success': False, 'error': f"Sheet '{sheet_name}' not found"}
            worksheet = workbook[sheet_name]
            content = []
            for row in worksheet.iter_rows(values_only=True):
                if any((cell is not None for cell in row)):
                    content.append(list(row))
            return {'success': True, 'content': content, 'file_path': file_path, 'sheet_name': sheet_name, 'rows': len(content)}
        except Exception as e:
            logger.error(f'Error reading Excel file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_excel(self, file_path: str, content: List[List[Any]], sheet_name: str=None, **kwargs) -> Dict[str, Any]:
        """Append content to Excel file"""
        if not EXCEL_AVAILABLE:
            return {'success': False, 'error': 'openpyxl library not available'}
        try:
            from io import BytesIO
            if not self._exists_raw(file_path):
                return self._save_excel(file_path, content, sheet_name or 'Sheet1', **kwargs)
            content_bytes = self._read_raw(file_path, **kwargs)
            workbook = load_workbook(BytesIO(content_bytes))
            sheet_names = workbook.sheetnames
            if sheet_name is None:
                sheet_name = sheet_names[0]
            if sheet_name not in sheet_names:
                return {'success': False, 'error': f"Sheet '{sheet_name}' not found"}
            worksheet = workbook[sheet_name]
            for row in content:
                worksheet.append(row)
            buffer = BytesIO()
            workbook.save(buffer)
            updated_bytes = buffer.getvalue()
            success = self._write_raw(file_path, updated_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to Excel file {file_path}', 'file_path': file_path, 'appended_rows': len(content)}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to Excel file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_pickle(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save pickle content to a file"""
        try:
            content_bytes = pickle.dumps(content)
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Pickle file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving pickle file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_pickle(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read pickle content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content = pickle.loads(content_bytes)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading pickle file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_pickle(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to pickle file (for lists)"""
        try:
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_content = pickle.loads(existing_bytes)
            if isinstance(existing_content, list):
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            elif isinstance(existing_content, dict):
                if isinstance(content, dict):
                    existing_content.update(content)
                elif isinstance(content, list):
                    existing_content['appended_list'] = content
                else:
                    existing_content['appended_value'] = content
            else:
                existing_content = [existing_content]
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            content_bytes = pickle.dumps(existing_content)
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to pickle file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to pickle file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_pdf(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Save content to a PDF file"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            paragraphs = content.split('\n')
            for para_text in paragraphs:
                if para_text.strip():
                    para = Paragraph(para_text, styles['Normal'])
                    story.append(para)
                    story.append(Spacer(1, 12))
                else:
                    story.append(Spacer(1, 12))
            doc.build(story)
            return {'success': True, 'message': f'PDF file saved to {file_path}', 'file_path': file_path}
        except ImportError:
            return {'success': False, 'error': 'reportlab library not available for PDF creation'}
        except Exception as e:
            logger.error(f'Error saving PDF file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_pdf(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read content from a PDF file"""
        if not PDF_AVAILABLE:
            return {'success': False, 'error': 'unstructured library not available'}
        try:
            doc = pymupdf.open(file_path)
            all_text = []
            for page in doc:
                text = page.get_text()
                all_text.append(text)
            text = '\n\n'.join(all_text)
            return {'success': True, 'content': text, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading PDF file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_image(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save image content to a file"""
        if not PILLOW_AVAILABLE:
            return {'success': False, 'error': 'Pillow library not available'}
        try:
            from io import BytesIO
            if hasattr(content, 'save') and callable(getattr(content, 'save', None)):
                buffer = BytesIO()
                content.save(buffer, format=content.format or 'PNG')
                content_bytes = buffer.getvalue()
                success = self._write_raw(file_path, content_bytes, **kwargs)
                if success:
                    return {'success': True, 'message': f'Image saved to {file_path}', 'file_path': file_path, 'format': content.format, 'size': content.size}
                else:
                    return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
            elif isinstance(content, bytes):
                success = self._write_raw(file_path, content, **kwargs)
                if success:
                    return {'success': True, 'message': f'Image saved to {file_path}', 'file_path': file_path}
                else:
                    return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
            elif isinstance(content, str) and Path(content).exists():
                with open(content, 'rb') as f:
                    content_bytes = f.read()
                success = self._write_raw(file_path, content_bytes, **kwargs)
                if success:
                    return {'success': True, 'message': f'Image copied from {content} to {file_path}', 'file_path': file_path}
                else:
                    return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Content must be a PIL Image object, binary data, or valid file path'}
        except Exception as e:
            logger.error(f'Error saving image file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_image(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read image and return PIL Image object"""
        if not PILLOW_AVAILABLE:
            return {'success': False, 'error': 'Pillow library not available'}
        try:
            from io import BytesIO
            content_bytes = self._read_raw(file_path, **kwargs)
            with Image.open(BytesIO(content_bytes)) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                metadata = {'format': img.format, 'mode': img.mode, 'size': img.size, 'width': img.width, 'height': img.height}
                return {'success': True, 'content': img, 'metadata': metadata, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading image file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _get_database_connection(self, db_type: str, connection_string: str) -> Any:
        """Placeholder for future database integration"""
        raise NotImplementedError('Database integration not yet implemented')

def _get_database_connection(self, db_type: str, connection_string: str) -> Any:
    """Placeholder for future database integration"""
    raise NotImplementedError('Database integration not yet implemented')

class HTTPRequestTool(Tool):
    """Universal HTTP request tool that handles all request methods and processing."""
    name: str = 'http_request'
    description: str = 'Make HTTP requests (GET, POST, PUT, DELETE, etc.) with automatic content processing and optional file saving'
    inputs: Dict[str, Dict[str, str]] = {'url': {'type': 'string', 'description': 'The URL to make the request to'}, 'method': {'type': 'string', 'description': 'HTTP method to use (GET, POST, PUT, DELETE, PATCH, etc.). Defaults to GET'}, 'headers': {'type': 'object', 'description': 'Optional headers to include in the request'}, 'params': {'type': 'object', 'description': 'Optional URL parameters to include in the request'}, 'data': {'type': 'object', 'description': 'Optional form data to send in the request body'}, 'json_data': {'type': 'object', 'description': 'Optional JSON data to send in the request body'}, 'return_raw': {'type': 'boolean', 'description': 'If true, return raw response content. If false (default), return processed content (HTML converted to text, JSON parsed, etc.)'}, 'save_file_path': {'type': 'string', 'description': 'Optional file path to save the response content'}}
    required: Optional[List[str]] = ['url']

    def __init__(self, request_base: RequestBase=None):
        super().__init__()
        self.request_base = request_base

    def __call__(self, url: str, method: str='GET', headers: dict=None, params: dict=None, data: dict=None, json_data: dict=None, return_raw: bool=False, save_file_path: str=None) -> Dict[str, Any]:
        """
        Make an HTTP request with comprehensive processing and error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Optional headers to include
            params: Optional URL parameters
            data: Optional form data to send
            json_data: Optional JSON data to send
            return_raw: If True, return raw content; if False, return processed content
            save_file_path: Optional path to save the response content
            
        Returns:
            Dictionary containing response data and metadata
        """
        return self.request_base.request_and_process(url=url, method=method, headers=headers, params=params, data=data, json_data=json_data, return_raw=return_raw, save_file_path=save_file_path)

def __call__(self, url: str, method: str='GET', headers: dict=None, params: dict=None, data: dict=None, json_data: dict=None, return_raw: bool=False, save_file_path: str=None) -> Dict[str, Any]:
    """
        Make an HTTP request with comprehensive processing and error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Optional headers to include
            params: Optional URL parameters
            data: Optional form data to send
            json_data: Optional JSON data to send
            return_raw: If True, return raw content; if False, return processed content
            save_file_path: Optional path to save the response content
            
        Returns:
            Dictionary containing response data and metadata
        """
    return self.request_base.request_and_process(url=url, method=method, headers=headers, params=params, data=data, json_data=json_data, return_raw=return_raw, save_file_path=save_file_path)

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

def __exit__(self, exc_type, exc_val, exc_tb):
    self.cleanup()

def _check_language(self, language: str) -> str:
    if language not in self.CODE_TYPE_MAPPING:
        raise ValueError(f'Unsupported language: {language}')
    return self.CODE_TYPE_MAPPING[language]

class DockerInterpreterToolkit(Toolkit):

    def __init__(self, name: str='DockerInterpreterToolkit', image_tag: Optional[str]=None, dockerfile_path: Optional[str]=None, require_confirm: bool=False, print_stdout: bool=True, print_stderr: bool=True, host_directory: str='', container_directory: str='/home/app/', container_command: str='tail -f /dev/null', tmp_directory: str='/tmp', storage_handler: FileStorageHandler=None, auto_cleanup: bool=True, auto_destroy: bool=True, **kwargs):
        if storage_handler is None:
            from .storage_handler import LocalStorageHandler
            storage_handler = LocalStorageHandler(base_path='./workplace/docker')
        docker_interpreter = DockerInterpreter(name='DockerInterpreter', image_tag=image_tag, dockerfile_path=dockerfile_path, require_confirm=require_confirm, print_stdout=print_stdout, print_stderr=print_stderr, host_directory=host_directory, container_directory=container_directory, container_command=container_command, tmp_directory=tmp_directory, storage_handler=storage_handler, auto_cleanup=auto_cleanup, auto_destroy=auto_destroy, **kwargs)
        tools = [DockerExecuteTool(docker_interpreter=docker_interpreter), DockerExecuteScriptTool(docker_interpreter=docker_interpreter)]
        super().__init__(name=name, tools=tools)
        self.docker_interpreter = docker_interpreter
        self.storage_handler = storage_handler
        self.auto_cleanup = auto_cleanup
        self.auto_destroy = auto_destroy

    def cleanup(self):
        """Clean up the Docker interpreter and storage handler."""
        try:
            if hasattr(self, 'auto_cleanup') and self.auto_cleanup:
                if hasattr(self, 'docker_interpreter') and self.docker_interpreter:
                    self.docker_interpreter.cleanup()
                if hasattr(self, 'storage_handler') and self.storage_handler:
                    try:
                        self.storage_handler.cleanup()
                    except Exception:
                        pass
        except Exception:
            pass

    def __del__(self):
        """Cleanup when toolkit is destroyed."""
        try:
            if hasattr(self, 'auto_destroy') and self.auto_destroy:
                self.cleanup()
        except Exception:
            pass

def cleanup(self):
    """Clean up the Docker interpreter and storage handler."""
    try:
        if hasattr(self, 'auto_cleanup') and self.auto_cleanup:
            if hasattr(self, 'docker_interpreter') and self.docker_interpreter:
                self.docker_interpreter.cleanup()
            if hasattr(self, 'storage_handler') and self.storage_handler:
                try:
                    self.storage_handler.cleanup()
                except Exception:
                    pass
    except Exception:
        pass

def __del__(self):
    """Cleanup when toolkit is destroyed."""
    try:
        if hasattr(self, 'auto_destroy') and self.auto_destroy:
            self.cleanup()
    except Exception:
        pass

class RSSBase(RequestBase):
    """
    Base class for RSS feed operations.
    Provides common functionality for fetching, parsing, and processing RSS feeds.
    """

    def __init__(self, timeout: int=30, max_retries: int=3, delay_between_requests: float=1.0):
        """
        Initialize the RSS base with configuration options.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay_between_requests: Delay between requests in seconds
        """
        super().__init__(timeout=timeout, max_retries=max_retries, delay_between_requests=delay_between_requests)

    def fetch_rss_feed(self, feed_url: str, max_entries: Optional[int]=10, fetch_webpage_content: bool=True) -> Dict[str, Any]:
        """
        Fetch and parse an RSS feed from a URL.
        
        Args:
            feed_url: URL of the RSS feed
            max_entries: Maximum number of entries to return (default: 10, None for all)
            fetch_webpage_content: Whether to fetch and extract content from article webpages (default: True)
            
        Returns:
            Dictionary containing parsed feed information
        """
        try:
            response = self.request(url=feed_url, method='GET')
            feed = feedparser.parse(response.content)
            if feed.bozo:
                logger.warning(f'RSS feed parsing warnings for {feed_url}: {feed.bozo_exception}')
            feed_info = {'success': True, 'feed_url': feed_url, 'title': getattr(feed.feed, 'title', 'Unknown'), 'description': getattr(feed.feed, 'description', ''), 'link': getattr(feed.feed, 'link', ''), 'language': getattr(feed.feed, 'language', ''), 'updated': getattr(feed.feed, 'updated', ''), 'generator': getattr(feed.feed, 'generator', ''), 'total_entries': len(feed.entries), 'entries': []}
            entries = feed.entries[:max_entries] if max_entries is not None else feed.entries
            for entry in entries:
                processed_entry = self._process_entry(entry, feed_url, fetch_webpage_content)
                feed_info['entries'].append(processed_entry)
            return feed_info
        except Exception as e:
            logger.error(f'Error fetching RSS feed from {feed_url}: {str(e)}')
            return {'success': False, 'error': str(e), 'feed_url': feed_url}

    def _process_entry(self, entry, base_url: str, fetch_webpage_content: bool=True) -> Dict[str, Any]:
        """
        Process a single RSS entry and extract relevant information.
        
        Args:
            entry: FeedParser entry object
            base_url: Base URL for resolving relative links
            fetch_webpage_content: Whether to fetch and extract content from the article webpage
            
        Returns:
            Dictionary with processed entry information
        """
        processed_entry = {'title': getattr(entry, 'title', ''), 'description': getattr(entry, 'description', ''), 'link': getattr(entry, 'link', ''), 'published': getattr(entry, 'published', ''), 'author': getattr(entry, 'author', ''), 'id': getattr(entry, 'id', ''), 'summary': getattr(entry, 'summary', ''), 'content': getattr(entry, 'content', []), 'tags': [], 'categories': [], 'enclosures': []}
        if processed_entry['link'] and (not processed_entry['link'].startswith(('http://', 'https://'))):
            processed_entry['link'] = urljoin(base_url, processed_entry['link'])
        if hasattr(entry, 'tags'):
            processed_entry['tags'] = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
        if hasattr(entry, 'category'):
            processed_entry['categories'] = [entry.category] if isinstance(entry.category, str) else entry.category
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                processed_entry['enclosures'].append({'url': getattr(enclosure, 'href', ''), 'type': getattr(enclosure, 'type', ''), 'length': getattr(enclosure, 'length', ''), 'title': getattr(enclosure, 'title', '')})
        processed_entry['published_parsed'] = self._parse_date(entry.published_parsed)
        processed_entry['title'] = self._clean_text(processed_entry['title'])
        processed_entry['description'] = self._clean_text(processed_entry['description'])
        processed_entry['summary'] = self._clean_text(processed_entry['summary'])
        if fetch_webpage_content and processed_entry['link']:
            result = self.request_and_process(url=processed_entry['link'], method='GET')
            if result.get('success') and result.get('content'):
                text_content = self._clean_text(result['content'])
                if len(text_content) > 10000:
                    text_content = text_content[:10000] + '... [Content truncated]'
                processed_entry['webpage_content'] = text_content
                processed_entry['webpage_content_fetched'] = True
            else:
                processed_entry['webpage_content_fetched'] = False
        else:
            processed_entry['webpage_content_fetched'] = False
        return processed_entry

    def _parse_date(self, date_tuple) -> Optional[str]:
        """
        Parse a date tuple from feedparser into ISO format string.
        
        Args:
            date_tuple: Date tuple from feedparser
            
        Returns:
            ISO format date string or None
        """
        if not date_tuple:
            return None
        try:
            dt = datetime(*date_tuple[:6])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        """
        Clean HTML tags and normalize whitespace in text.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text content
        """
        if not text:
            return ''
        text = re.sub('<[^>]+>', '', text)
        text = re.sub('\\s+', ' ', text.strip())
        return text

    def validate_rss_url(self, url: str) -> Dict[str, Any]:
        """
        Validate if a URL contains a valid RSS feed.
        
        Args:
            url: URL to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            response = self.request(url=url, method='GET')
            content = response.content
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                return {'success': False, 'error': 'Invalid XML content', 'url': url}
            is_rss = root.tag.endswith('rss') or root.tag.endswith('RDF')
            is_atom = root.tag.endswith('feed') or 'atom' in root.tag
            if is_rss or is_atom:
                return {'success': True, 'is_valid': True, 'feed_type': 'RSS' if is_rss else 'Atom', 'url': url, 'title': self._extract_feed_title(root)}
            else:
                return {'success': True, 'is_valid': False, 'error': 'Not a valid RSS or Atom feed', 'url': url}
        except Exception as e:
            return {'success': False, 'error': str(e), 'url': url}

    def _extract_feed_title(self, root) -> str:
        """
        Extract feed title from XML root element.
        
        Args:
            root: XML root element
            
        Returns:
            Feed title or empty string
        """
        title_selectors = ['.//title', './/channel/title', './/feed/title']
        for selector in title_selectors:
            title_elem = root.find(selector)
            if title_elem is not None and title_elem.text:
                return self._clean_text(title_elem.text)
        return ''

def _process_entry(self, entry, base_url: str, fetch_webpage_content: bool=True) -> Dict[str, Any]:
    """
        Process a single RSS entry and extract relevant information.
        
        Args:
            entry: FeedParser entry object
            base_url: Base URL for resolving relative links
            fetch_webpage_content: Whether to fetch and extract content from the article webpage
            
        Returns:
            Dictionary with processed entry information
        """
    processed_entry = {'title': getattr(entry, 'title', ''), 'description': getattr(entry, 'description', ''), 'link': getattr(entry, 'link', ''), 'published': getattr(entry, 'published', ''), 'author': getattr(entry, 'author', ''), 'id': getattr(entry, 'id', ''), 'summary': getattr(entry, 'summary', ''), 'content': getattr(entry, 'content', []), 'tags': [], 'categories': [], 'enclosures': []}
    if processed_entry['link'] and (not processed_entry['link'].startswith(('http://', 'https://'))):
        processed_entry['link'] = urljoin(base_url, processed_entry['link'])
    if hasattr(entry, 'tags'):
        processed_entry['tags'] = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
    if hasattr(entry, 'category'):
        processed_entry['categories'] = [entry.category] if isinstance(entry.category, str) else entry.category
    if hasattr(entry, 'enclosures'):
        for enclosure in entry.enclosures:
            processed_entry['enclosures'].append({'url': getattr(enclosure, 'href', ''), 'type': getattr(enclosure, 'type', ''), 'length': getattr(enclosure, 'length', ''), 'title': getattr(enclosure, 'title', '')})
    processed_entry['published_parsed'] = self._parse_date(entry.published_parsed)
    processed_entry['title'] = self._clean_text(processed_entry['title'])
    processed_entry['description'] = self._clean_text(processed_entry['description'])
    processed_entry['summary'] = self._clean_text(processed_entry['summary'])
    if fetch_webpage_content and processed_entry['link']:
        result = self.request_and_process(url=processed_entry['link'], method='GET')
        if result.get('success') and result.get('content'):
            text_content = self._clean_text(result['content'])
            if len(text_content) > 10000:
                text_content = text_content[:10000] + '... [Content truncated]'
            processed_entry['webpage_content'] = text_content
            processed_entry['webpage_content_fetched'] = True
        else:
            processed_entry['webpage_content_fetched'] = False
    else:
        processed_entry['webpage_content_fetched'] = False
    return processed_entry

def _extract_feed_title(self, root) -> str:
    """
        Extract feed title from XML root element.
        
        Args:
            root: XML root element
            
        Returns:
            Feed title or empty string
        """
    title_selectors = ['.//title', './/channel/title', './/feed/title']
    for selector in title_selectors:
        title_elem = root.find(selector)
        if title_elem is not None and title_elem.text:
            return self._clean_text(title_elem.text)
    return ''

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

class Tool(BaseModule):
    name: str
    description: str
    inputs: Dict[str, Dict[str, Any]]
    required: Optional[List[str]] = None
    '\n    inputs: {"input_name": {"type": "string", "description": "input description"}, ...}\n    '

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.validate_attributes()

    def get_tool_schema(self) -> Dict:
        return {'type': 'function', 'function': {'name': self.name, 'description': self.description, 'parameters': {'type': 'object', 'properties': self.inputs, 'required': self.required}}}

    @classmethod
    def validate_attributes(cls):
        required_attributes = {'name': str, 'description': str, 'inputs': dict}
        json_to_python = {'string': str, 'integer': int, 'number': float, 'boolean': bool, 'object': dict, 'array': list}
        for attr, attr_type in required_attributes.items():
            if not hasattr(cls, attr):
                raise ValueError(f'Attribute {attr} is required')
            if not isinstance(getattr(cls, attr), attr_type):
                raise ValueError(f'Attribute {attr} must be of type {attr_type}')
        for input_name, input_content in cls.inputs.items():
            if not isinstance(input_content, dict):
                raise ValueError(f"Input '{input_name}' must be a dictionary")
            if 'type' not in input_content or 'description' not in input_content:
                raise ValueError(f"Input '{input_name}' must have 'type' and 'description'")
            if input_content['type'] not in ALLOWED_TYPES:
                raise ValueError(f"Input '{input_name}' must have a valid type, should be one of {ALLOWED_TYPES}")
            call_signature = inspect.signature(cls.__call__)
            if input_name not in call_signature.parameters:
                raise ValueError(f"Input '{input_name}' is not found in __call__")
            if call_signature.parameters[input_name].annotation != json_to_python[input_content['type']]:
                raise ValueError(f"Input '{input_name}' has a type mismatch in __call__")
        if cls.required:
            for required_input in cls.required:
                if required_input not in cls.inputs:
                    raise ValueError(f"Required input '{required_input}' is not found in inputs")

    def __call__(self, **kwargs):
        raise NotImplementedError('All tools must implement __call__')

@classmethod
def validate_attributes(cls):
    required_attributes = {'name': str, 'description': str, 'inputs': dict}
    json_to_python = {'string': str, 'integer': int, 'number': float, 'boolean': bool, 'object': dict, 'array': list}
    for attr, attr_type in required_attributes.items():
        if not hasattr(cls, attr):
            raise ValueError(f'Attribute {attr} is required')
        if not isinstance(getattr(cls, attr), attr_type):
            raise ValueError(f'Attribute {attr} must be of type {attr_type}')
    for input_name, input_content in cls.inputs.items():
        if not isinstance(input_content, dict):
            raise ValueError(f"Input '{input_name}' must be a dictionary")
        if 'type' not in input_content or 'description' not in input_content:
            raise ValueError(f"Input '{input_name}' must have 'type' and 'description'")
        if input_content['type'] not in ALLOWED_TYPES:
            raise ValueError(f"Input '{input_name}' must have a valid type, should be one of {ALLOWED_TYPES}")
        call_signature = inspect.signature(cls.__call__)
        if input_name not in call_signature.parameters:
            raise ValueError(f"Input '{input_name}' is not found in __call__")
        if call_signature.parameters[input_name].annotation != json_to_python[input_content['type']]:
            raise ValueError(f"Input '{input_name}' has a type mismatch in __call__")
    if cls.required:
        for required_input in cls.required:
            if required_input not in cls.inputs:
                raise ValueError(f"Required input '{required_input}' is not found in inputs")

def __call__(self, **kwargs):
    raise NotImplementedError('All tools must implement __call__')

class Toolkit(BaseModule):
    name: str
    tools: List[Tool]

    def get_tool_names(self) -> List[str]:
        return [tool.name for tool in self.tools]

    def get_tool_descriptions(self) -> List[str]:
        return [tool.description for tool in self.tools]

    def get_tool_inputs(self) -> List[Dict]:
        return [tool.inputs for tool in self.tools]

    def add_tool(self, tool: Tool):
        self.tools.append(tool)

    def remove_tool(self, tool_name: str):
        self.tools = [tool for tool in self.tools if tool.name != tool_name]

    def get_tool(self, tool_name: str) -> Tool:
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        raise ValueError(f"Tool '{tool_name}' not found")

    def get_tools(self) -> List[Tool]:
        return self.tools

    def get_tool_schemas(self) -> List[Dict]:
        return [tool.get_tool_schema() for tool in self.tools]

def get_tool(self, tool_name: str) -> Tool:
    for tool in self.tools:
        if tool.name == tool_name:
            return tool
    raise ValueError(f"Tool '{tool_name}' not found")

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

class DatabaseBase(ABC):
    """
    Abstract base class for database operations.
    Provides a common interface for different database types.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, **kwargs):
        """
        Initialize the database base.
        
        Args:
            connection_string: Database connection string
            database_name: Name of the database to use
            **kwargs: Additional connection parameters
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.connection_params = kwargs
        self.db_type = self._get_database_type()
        self.connection = None
        self._is_initialized = False
        if connection_string:
            self.connect()

    @abstractmethod
    def _get_database_type(self) -> DatabaseType:
        """Return the database type"""
        pass

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the database.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the database connection is working.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        pass

    @abstractmethod
    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        """
        Execute a query on the database.
        
        Args:
            query: The query to execute (string for SQL, dict/list for NoSQL)
            query_type: Type of query being executed
            **kwargs: Additional query parameters
            
        Returns:
            Dict containing query results and metadata
        """
        pass

    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.
        
        Returns:
            Dict containing database information
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collections/tables in the database.
        
        Returns:
            List of collection/table names
        """
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a specific collection/table.
        
        Args:
            collection_name: Name of the collection/table
            
        Returns:
            Dict containing collection/table information
        """
        pass

    @abstractmethod
    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        """
        Get the schema/structure of the database or a specific collection.
        
        Args:
            collection_name: Name of the collection/table (optional)
            
        Returns:
            Dict containing schema information
        """
        pass

    def validate_query(self, query: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Validate a query before execution.
        
        Args:
            query: The query to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            if isinstance(query, str):
                if not query.strip():
                    return {'valid': False, 'error': 'Query cannot be empty'}
            elif isinstance(query, (dict, list)):
                if not query:
                    return {'valid': False, 'error': 'Query cannot be empty'}
            else:
                return {'valid': False, 'error': f'Unsupported query type: {type(query)}'}
            return {'valid': True, 'error': None}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def format_query_result(self, data: Any, query_type: QueryType, execution_time: float=None, **kwargs) -> Dict[str, Any]:
        """
        Format query results into a standard structure.
        
        Args:
            data: Raw query results
            query_type: Type of query that was executed
            execution_time: Time taken to execute the query
            **kwargs: Additional metadata
            
        Returns:
            Dict containing formatted results
        """
        return {'success': True, 'data': data, 'query_type': query_type.value if query_type else None, 'execution_time': execution_time, 'row_count': len(data) if isinstance(data, (list, tuple)) else 1, 'metadata': kwargs}

    def format_error_result(self, error: str, query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        """
        Format error results into a standard structure.
        
        Args:
            error: Error message
            query_type: Type of query that failed
            **kwargs: Additional error metadata
            
        Returns:
            Dict containing formatted error results
        """
        return {'success': False, 'error': error, 'query_type': query_type.value if query_type else None, 'data': None, 'execution_time': None, 'row_count': 0, 'metadata': kwargs}

    def get_supported_query_types(self) -> List[QueryType]:
        """
        Get list of supported query types for this database.
        
        Returns:
            List of supported QueryType enums
        """
        return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP]

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get database capabilities and features.
        
        Returns:
            Dict containing database capabilities
        """
        return {'database_type': self.db_type.value, 'supports_sql': False, 'supports_aggregation': False, 'supports_full_text_search': False, 'supports_vector_search': False, 'supports_transactions': False, 'supports_indexing': True, 'supported_query_types': [qt.value for qt in self.get_supported_query_types()], 'connection_info': {'is_connected': self.connection is not None, 'database_name': self.database_name}}

    def __enter__(self):
        """Context manager entry"""
        if not self.connection:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.disconnect()
        except Exception:
            pass

def validate_query(self, query: Union[str, Dict, List]) -> Dict[str, Any]:
    """
        Validate a query before execution.
        
        Args:
            query: The query to validate
            
        Returns:
            Dict containing validation results
        """
    try:
        if isinstance(query, str):
            if not query.strip():
                return {'valid': False, 'error': 'Query cannot be empty'}
        elif isinstance(query, (dict, list)):
            if not query:
                return {'valid': False, 'error': 'Query cannot be empty'}
        else:
            return {'valid': False, 'error': f'Unsupported query type: {type(query)}'}
        return {'valid': True, 'error': None}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def format_query_result(self, data: Any, query_type: QueryType, execution_time: float=None, **kwargs) -> Dict[str, Any]:
    """
        Format query results into a standard structure.
        
        Args:
            data: Raw query results
            query_type: Type of query that was executed
            execution_time: Time taken to execute the query
            **kwargs: Additional metadata
            
        Returns:
            Dict containing formatted results
        """
    return {'success': True, 'data': data, 'query_type': query_type.value if query_type else None, 'execution_time': execution_time, 'row_count': len(data) if isinstance(data, (list, tuple)) else 1, 'metadata': kwargs}

class MCPTool(Tool):
    name: str = 'MCPTool'
    description: str = 'MCP tool wrapper'
    inputs: Dict[str, Dict[str, Any]] = {}
    required: Optional[List[str]] = None
    function: Callable = None

    def __init__(self, name: str, description: str, inputs: Dict[str, Dict[str, str]], required: Optional[List[str]]=None, function: Callable=None):
        super().__init__(name=name, description=description, inputs=inputs, required=required)
        self.function = function

    @property
    def __name__(self):
        return self.name

    def __call__(self, **kwargs):
        if not self.function:
            raise ValueError('Function not set for MCPTool')
        result = self.function(**kwargs)
        return self._convert_result(result)

    def _convert_result(self, result: Any) -> Any:
        """
        Convert MCP tool results to JSON-serializable format.
        Handles complex objects like Anthropic's TextContent, ImageContent, etc.
        """
        if result is None:
            return None
        if isinstance(result, (str, int, float, bool)):
            return result
        if isinstance(result, list):
            return [self._convert_result(item) for item in result]
        if isinstance(result, dict):
            return {key: self._convert_result(value) for key, value in result.items()}
        obj_type = type(result).__name__
        if obj_type == 'TextContent':
            if hasattr(result, 'text'):
                return result.text
            elif hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
        elif obj_type in ['ImageContent', 'ToolUseContent', 'ToolResultContent']:
            if hasattr(result, '__dict__'):
                return self._convert_result(result.__dict__)
            else:
                return str(result)
        if hasattr(result, 'text'):
            return result.text
        elif hasattr(result, 'content'):
            return result.content
        if hasattr(result, '__dict__'):
            return self._convert_result(result.__dict__)
        return str(result)

    @classmethod
    def validate_attributes(cls):
        required_attributes = {'name': str, 'description': str, 'inputs': dict}
        for attr, attr_type in required_attributes.items():
            if not hasattr(cls, attr):
                raise ValueError(f'Attribute {attr} is required')
            if not isinstance(getattr(cls, attr), attr_type):
                raise ValueError(f'Attribute {attr} must be of type {attr_type}')
        if cls.required:
            for required_input in cls.required:
                if required_input not in cls.inputs:
                    raise ValueError(f"Required input '{required_input}' is not found in inputs")

def __call__(self, **kwargs):
    if not self.function:
        raise ValueError('Function not set for MCPTool')
    result = self.function(**kwargs)
    return self._convert_result(result)

def _convert_result(self, result: Any) -> Any:
    """
        Convert MCP tool results to JSON-serializable format.
        Handles complex objects like Anthropic's TextContent, ImageContent, etc.
        """
    if result is None:
        return None
    if isinstance(result, (str, int, float, bool)):
        return result
    if isinstance(result, list):
        return [self._convert_result(item) for item in result]
    if isinstance(result, dict):
        return {key: self._convert_result(value) for key, value in result.items()}
    obj_type = type(result).__name__
    if obj_type == 'TextContent':
        if hasattr(result, 'text'):
            return result.text
        elif hasattr(result, 'content'):
            return result.content
        else:
            return str(result)
    elif obj_type in ['ImageContent', 'ToolUseContent', 'ToolResultContent']:
        if hasattr(result, '__dict__'):
            return self._convert_result(result.__dict__)
        else:
            return str(result)
    if hasattr(result, 'text'):
        return result.text
    elif hasattr(result, 'content'):
        return result.content
    if hasattr(result, '__dict__'):
        return self._convert_result(result.__dict__)
    return str(result)

@classmethod
def validate_attributes(cls):
    required_attributes = {'name': str, 'description': str, 'inputs': dict}
    for attr, attr_type in required_attributes.items():
        if not hasattr(cls, attr):
            raise ValueError(f'Attribute {attr} is required')
        if not isinstance(getattr(cls, attr), attr_type):
            raise ValueError(f'Attribute {attr} must be of type {attr_type}')
    if cls.required:
        for required_input in cls.required:
            if required_input not in cls.inputs:
                raise ValueError(f"Required input '{required_input}' is not found in inputs")

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

class TelegramBase(BaseModule):
    """
    Base class for Telegram API interactions.
    Handles client management, authentication, and common utilities.
    """

    def __init__(self, api_id: str=None, api_hash: str=None, phone: str=None, **kwargs):
        """
        Initialize the Telegram base.
        
        Args:
            api_id (str, optional): Telegram API ID. If not provided, will try to get from TELEGRAM_API_ID environment variable.
            api_hash (str, optional): Telegram API Hash. If not provided, will try to get from TELEGRAM_API_HASH environment variable.
            phone (str, optional): Phone number for authentication. If not provided, will try to get from TELEGRAM_PHONE environment variable.
            **kwargs: Additional keyword arguments for parent class
        """
        super().__init__(**kwargs)
        self.api_id = api_id or os.getenv('TELEGRAM_API_ID')
        self.api_hash = api_hash or os.getenv('TELEGRAM_API_HASH')
        self.phone = phone or os.getenv('TELEGRAM_PHONE')
        if not self.api_id or not self.api_hash:
            logger.warning('No Telegram API credentials provided. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables or pass api_id and api_hash parameters. Get your credentials from: https://my.telegram.org/apps')

    def _get_client(self) -> TelegramClient:
        """
        Create and return a Telegram client instance.
        
        Returns:
            TelegramClient: Configured Telegram client
        """
        if not self.api_id or not self.api_hash:
            raise ValueError('Telegram API credentials not found. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables.')
        client = TelegramClient(SESSION_NAME, self.api_id, self.api_hash)
        return client

    def _format_message(self, message: Message) -> Dict[str, Any]:
        """
        Format a Telegram message for consistent output.
        
        Args:
            message: Telegram message object
            
        Returns:
            dict: Formatted message data
        """
        return {'id': message.id, 'text': message.text or '', 'date': message.date.isoformat() if message.date else None, 'sender_id': message.sender_id, 'chat_id': message.chat_id, 'is_reply': message.reply_to_msg_id is not None, 'reply_to_msg_id': message.reply_to_msg_id, 'has_media': message.media is not None, 'media_type': type(message.media).__name__ if message.media else None}

    def _format_chat(self, chat) -> Dict[str, Any]:
        """
        Format a Telegram chat for consistent output.
        
        Args:
            chat: Telegram chat object
            
        Returns:
            dict: Formatted chat data
        """
        chat_type = 'unknown'
        title = 'Unknown'
        if isinstance(chat, User):
            chat_type = 'user'
            title = f'{chat.first_name or ''} {chat.last_name or ''}'.strip() or chat.username or 'Unknown User'
        elif isinstance(chat, Chat):
            chat_type = 'group'
            title = chat.title or 'Unknown Group'
        elif isinstance(chat, Channel):
            chat_type = 'channel' if chat.broadcast else 'supergroup'
            title = chat.title or 'Unknown Channel'
        return {'id': chat.id, 'title': title, 'type': chat_type, 'username': getattr(chat, 'username', None)}

    def _run_async(self, coro):
        """
        Run an async coroutine, handling both sync and async contexts.
        
        Args:
            coro: Async coroutine to run
            
        Returns:
            Result of the coroutine
        """
        try:
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            except RuntimeError:
                return asyncio.run(coro)
        except Exception as e:
            return {'success': False, 'error': f'Failed to execute async operation: {str(e)}'}

def _get_client(self) -> TelegramClient:
    """
        Create and return a Telegram client instance.
        
        Returns:
            TelegramClient: Configured Telegram client
        """
    if not self.api_id or not self.api_hash:
        raise ValueError('Telegram API credentials not found. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables.')
    client = TelegramClient(SESSION_NAME, self.api_id, self.api_hash)
    return client

def _format_chat(self, chat) -> Dict[str, Any]:
    """
        Format a Telegram chat for consistent output.
        
        Args:
            chat: Telegram chat object
            
        Returns:
            dict: Formatted chat data
        """
    chat_type = 'unknown'
    title = 'Unknown'
    if isinstance(chat, User):
        chat_type = 'user'
        title = f'{chat.first_name or ''} {chat.last_name or ''}'.strip() or chat.username or 'Unknown User'
    elif isinstance(chat, Chat):
        chat_type = 'group'
        title = chat.title or 'Unknown Group'
    elif isinstance(chat, Channel):
        chat_type = 'channel' if chat.broadcast else 'supergroup'
        title = chat.title or 'Unknown Channel'
    return {'id': chat.id, 'title': title, 'type': chat_type, 'username': getattr(chat, 'username', None)}

def _js_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    vocab = set(p.keys()) | set(q.keys())
    eps = 1e-09

    def _norm(d: Dict[str, float]) -> Dict[str, float]:
        s = sum((d.get(w, 0.0) for w in vocab)) or 1.0
        return {w: (d.get(w, 0.0) + eps) / (s + eps * len(vocab)) for w in vocab}
    P = _norm(p)
    Q = _norm(q)
    M = {w: 0.5 * (P[w] + Q[w]) for w in vocab}

    def _kl(X, Y):
        return sum((X[w] * math.log((X[w] + eps) / (Y[w] + eps)) for w in vocab))
    return 0.5 * _kl(P, M) + 0.5 * _kl(Q, M)

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

def _serialize_llm_config(self, llm_config) -> Optional[Dict[str, Any]]:
    """序列化LLM配置（只保存模型名称和基本参数）"""
    if not llm_config:
        return None
    config_info = {'model': llm_config.model if hasattr(llm_config, 'model') else None, 'temperature': llm_config.temperature if hasattr(llm_config, 'temperature') else None, 'config_type': type(llm_config).__name__}
    return config_info

class VectorStoreFactory:
    """Factory for creating vector stores."""

    def create(self, store_type: str, store_config: Dict[str, Any]=None) -> VectorStore:
        store_config = store_config or {}
        if store_type == VectorStoreType.FAISS:
            dimensions = store_config.get('dimensions')
            if not dimensions or not isinstance(dimensions, int):
                raise ValueError('FAISS requires a valid dimension')
            vector_store = FaissVectorStoreWrapper(**store_config)
        else:
            raise ValueError(f'Unsupported vector store type: {store_type}')
        logger.info(f'Created vector store: {store_type}')
        return vector_store

def create(self, store_type: str, store_config: Dict[str, Any]=None) -> VectorStore:
    store_config = store_config or {}
    if store_type == VectorStoreType.FAISS:
        dimensions = store_config.get('dimensions')
        if not dimensions or not isinstance(dimensions, int):
            raise ValueError('FAISS requires a valid dimension')
        vector_store = FaissVectorStoreWrapper(**store_config)
    else:
        raise ValueError(f'Unsupported vector store type: {store_type}')
    logger.info(f'Created vector store: {store_type}')
    return vector_store

class FaissVectorStoreWrapper(VectorStoreBase):
    """Wrapper for FAISS vector store."""

    def __init__(self, dimensions: int=1536, metrics: Union[Literal['flat_l2', 'ivf_flat']]='flat_l2', **kwargs):
        self.dimensions = dimensions
        self.metrics = metrics
        self.faiss_index = self._create_index()
        self.vector_store = FaissMapVectorStore(faiss_index=faiss.IndexIDMap2(self.faiss_index))

    def _create_index(self) -> faiss.Index:
        if self.metrics == 'flat_l2':
            return faiss.IndexFlatL2(self.dimensions)
        elif self.metrics == 'ivf_flat':
            quantizer = faiss.IndexFlatL2(self.dimensions)
            return faiss.IndexIVFFlat(quantizer, self.dimensions, 100)
        else:
            raise ValueError(f'Unsupported FAISS index type: {self.metrics}')

    def get_vector_store(self) -> FaissMapVectorStore:
        return self.vector_store

    async def aload(self, node: BaseNode) -> None:
        """
        Asynchronously load a single node into the FAISS vector store.

        Checks if a node with the same ID already exists in the FAISS vector store. If it does not exist,
        inserts the node with its embedding. Handles both Chunk and BaseNode types.

        Args:
            node (Union[Chunk, BaseNode]): The node to load, either a Chunk or a LlamaIndex BaseNode.
        """
        try:
            if not isinstance(node, BaseNode):
                raise ValueError(f'Unsupported node type: {type(node)}. Must be Chunk or BaseNode.')
            node_id = node.id if hasattr(node, 'id') else node.id_
            existing_ids = self.vector_store._node_id_to_faiss_id_map
            if node_id in existing_ids:
                logger.info(f'Node with ID {node_id} already exists in FAISS vector store, skipping insertion.')
                return
            self.vector_store.add([node])
            logger.info(f'Inserted node with ID {node_id} into FAISS vector store.')
        except Exception as e:
            logger.error(f'Failed to load node with ID {node_id} into FAISS vector store: {str(e)}')
            raise

def _create_index(self) -> faiss.Index:
    if self.metrics == 'flat_l2':
        return faiss.IndexFlatL2(self.dimensions)
    elif self.metrics == 'ivf_flat':
        quantizer = faiss.IndexFlatL2(self.dimensions)
        return faiss.IndexIVFFlat(quantizer, self.dimensions, 100)
    else:
        raise ValueError(f'Unsupported FAISS index type: {self.metrics}')

class DBStoreFactory:
    """
    Factory class for creating database store instances based on provider and configuration.
    Maps provider names to specific database store classes.
    """
    provider_to_class = {'sqlite': 'evoagentx.storages.db_stores.sqlite.SQLite', 'posgre_sql': 'evoagentx.storages.db_stores.posgre_sql.'}

    @classmethod
    def create(cls, provider_name: str, config: DBConfig):
        """
        Create a database store instance for the specified provider.

        Attributes:
            provider_name (str): Name of the database provider (e.g., 'sqlite', 'posgre_sql').
            config (DBConfig): Configuration for the database store.

        Returns:
            DBStoreBase: An instance of the database store.

        Raises:
            ValueError: If the provider is not supported.
        """
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            if not isinstance(config, dict):
                config = config.model_dump()
            db_store_class = load_class(class_type)
            return db_store_class(**config)
        else:
            raise ValueError(f'Unsupported Database provider: {provider_name}')

@classmethod
def create(cls, provider_name: str, config: DBConfig):
    """
        Create a database store instance for the specified provider.

        Attributes:
            provider_name (str): Name of the database provider (e.g., 'sqlite', 'posgre_sql').
            config (DBConfig): Configuration for the database store.

        Returns:
            DBStoreBase: An instance of the database store.

        Raises:
            ValueError: If the provider is not supported.
        """
    class_type = cls.provider_to_class.get(provider_name)
    if class_type:
        if not isinstance(config, dict):
            config = config.model_dump()
        db_store_class = load_class(class_type)
        return db_store_class(**config)
    else:
        raise ValueError(f'Unsupported Database provider: {provider_name}')

def _create_table(table: str, column: List[str]) -> str:
    """
    Generates SQL to create a table with the specified columns.
    The first column is set as the PRIMARY KEY.

    Attributes:
        table (str): The name of the table to create.
        column (List[str]): List of column names.

    Returns:
        str: SQL statement to create the table.
    """
    if not column:
        raise ValueError('Column list cannot be empty')
    column_defs = [f'"{column[0]}" TEXT PRIMARY KEY'] + [f'"{col}" TEXT' for col in column[1:]]
    table_column = ', '.join(column_defs)
    table_sql = f'CREATE TABLE IF NOT EXISTS {table} (\n        {table_column}\n    )'
    return table_sql

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

class GraphStoreBase(ABC):
    """Base interface for graph stores."""

    @abstractmethod
    def get_graph_store(self) -> GraphStore:
        """Return the LlamaIndex-compatible graph store."""
        pass

    @property
    def supports_vector_queries(self):
        NotImplementedError()

    @abstractmethod
    def clear(self) -> None:
        """Clear the node and relation in the graph database."""
        pass

    @abstractmethod
    def aload(self) -> None:
        """Asynchronously load a single node into the graph database."""
        pass

    @abstractmethod
    def build_kv_store(self) -> Dict:
        """Exported all the nodes and relations from graph database into python Dict for saving to file or database."""
        pass

@property
def supports_vector_queries(self):
    NotImplementedError()

class GraphStoreFactory:
    """Factory for creating graph stores."""

    def create(self, store_type: str, store_config: Dict[str, Any]=None) -> GraphStore:
        """Create a graph store based on configuration.
        
        Args:
            store_type (str): The type of graph store (e.g., 'neo4j').
            store_config (Dict[str, Any], optional): Store configuration.
            
        Returns:
            GraphStore: A LlamaIndex-compatible graph store.
            
        Raises:
            ValueError: If the store type or configuration is invalid.
        """
        store_config = store_config or {}
        if store_type == GraphStoreType.NEO4J.value:
            required_fields = ['uri', 'username', 'password']
            if not all((field in store_config for field in required_fields)):
                raise ValueError('Neo4j requires uri, username, and password')
            graph_store = Neo4jGraphStoreWrapper(**store_config)
        else:
            raise ValueError(f'Unsupported graph store type: {store_type}')
        logger.info(f'Created graph store: {store_type}')
        return graph_store

def create(self, store_type: str, store_config: Dict[str, Any]=None) -> GraphStore:
    """Create a graph store based on configuration.
        
        Args:
            store_type (str): The type of graph store (e.g., 'neo4j').
            store_config (Dict[str, Any], optional): Store configuration.
            
        Returns:
            GraphStore: A LlamaIndex-compatible graph store.
            
        Raises:
            ValueError: If the store type or configuration is invalid.
        """
    store_config = store_config or {}
    if store_type == GraphStoreType.NEO4J.value:
        required_fields = ['uri', 'username', 'password']
        if not all((field in store_config for field in required_fields)):
            raise ValueError('Neo4j requires uri, username, and password')
        graph_store = Neo4jGraphStoreWrapper(**store_config)
    else:
        raise ValueError(f'Unsupported graph store type: {store_type}')
    logger.info(f'Created graph store: {store_type}')
    return graph_store

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

def __init__(self, uri: str, username: str, password: str, database: str='neo4j', **kwargs):
    try:
        self.graph_store = BasicNeo4jStore(url=uri, username=username, password=password, database=database)
    except Exception as e:
        raise ValueError(f'Failed to connect to Neo4j: {str(e)}')
    self.verify_version()

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

def set(self, name: str, value: Any):
    self.fields[name].set(value)

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

def getter():
    return parent[leaf] if isinstance(parent, (list, dict)) else getattr(parent, leaf)

def setter(v):
    if isinstance(parent, (list, dict)):
        parent[leaf] = v
    else:
        setattr(parent, leaf, v)

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

def _apply_cfg(self, cfg: Dict[str, Any]):
    for k, v in cfg.items():
        if k in self.registry.fields:
            self.registry.set(k, v)

def bind_cfg(obj: Any, cfg: Dict[str, Any]) -> None:
    """Recursively write *cfg* values into (potentially nested) attributes
    of *obj*.  Key like "a.b.c" becomes obj.a.b.c = value.
    """
    for key, val in cfg.items():
        parts = key.split('.')
        cur = obj
        for part in parts[:-1]:
            cur = getattr(cur, part)
        setattr(cur, parts[-1], val)

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

def _is_task_inputs_match(task_inputs: List[str], another_inputs: List[str]) -> bool:
    return len(set(task_inputs) & set(another_inputs)) == len(task_inputs)

def _is_task_outputs_match(task_outputs: List[str], another_outputs: List[str]) -> bool:
    return len(set(task_outputs) & set(another_outputs)) == len(task_outputs)

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

def init_module(self, **kwargs):
    self._snapshot: List[dict] = []
    self._prompt_breeder = SimplePromptBreeder(llm=self.llm)
    self._convergence_check_counter = 0
    self._best_score = float('-inf')
    if isinstance(self.graph, ActionGraph):
        if self.optimize_mode != 'prompt':
            raise ValueError(f'{type(self).__name__} only support prompt optimization when `graph` is an `ActionGraph`. The `optimize_mode` should be set to `prompt`, but got {self.optimize_mode}.')

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

def restore_best_graph(self):
    best_graph, best_metrics = self._select_graph_with_highest_score(return_metrics=True)
    logger.info(f'Restore the best graph from snapshot with metrics {best_metrics} ...')
    self.graph = best_graph

def _action_graph_step(self, graph: ActionGraph) -> ActionGraph:
    if self.optimize_mode == 'prompt':
        graph = self._action_graph_prompt_optimization_step(graph)
    else:
        raise ValueError(f'{type(self).__name__} only support prompt optimization when `self.graph` is an `ActionGraph` instance. The `optimize_mode` should be set to `prompt`, but got {self.optimize_mode}.')
    return graph

class TextGradAgent:
    """An agent that takes textgrad.Variable inputs and returns a textgrad.Variable response.
    This class is used to replace EvoAgentX Agent in WorkFlowGraph to allow TextGrad optimization.
    """

    def __init__(self, agent: Agent, optimize_mode: Literal['all', 'system_prompt', 'instruction']='all'):
        self.name = agent.name
        require_grad = {'all': {'system_prompt': True, 'instruction': True}, 'system_prompt': {'system_prompt': True, 'instruction': False}, 'instruction': {'system_prompt': False, 'instruction': True}}
        system_prompt_require_grad = require_grad[optimize_mode]['system_prompt']
        instruction_require_grad = require_grad[optimize_mode]['instruction']
        self.system_prompt = Variable(agent.system_prompt, requires_grad=system_prompt_require_grad, role_description=f"{self.name}'s system prompt")
        self.instruction = Variable(agent.actions[0].prompt_template.instruction, requires_grad=instruction_require_grad, role_description=f"{self.name}'s instruction prompt")
        self._agent_call = CustomAgentCall(agent)
        self.forward = StringBasedFunction(self._agent_call, agent.description)
        self.output_description = ' and '.join(agent.actions[0].outputs_format.get_attr_descriptions().values())
        self.last_output = None

    def __call__(self, inputs: dict[str, Variable]) -> Variable:
        """Given textgrad.Variable inputs, generates a textgrad.Variable output."""
        forward_inputs: dict[str, Variable] = {'instruction': self.instruction, 'system_prompt': self.system_prompt, **inputs}
        output_variable = self.forward(forward_inputs, self.output_description)
        output_variable.parsed_outputs = self._agent_call.last_outputs
        self.last_output = output_variable
        return output_variable

def __init__(self, agent: Agent, optimize_mode: Literal['all', 'system_prompt', 'instruction']='all'):
    self.name = agent.name
    require_grad = {'all': {'system_prompt': True, 'instruction': True}, 'system_prompt': {'system_prompt': True, 'instruction': False}, 'instruction': {'system_prompt': False, 'instruction': True}}
    system_prompt_require_grad = require_grad[optimize_mode]['system_prompt']
    instruction_require_grad = require_grad[optimize_mode]['instruction']
    self.system_prompt = Variable(agent.system_prompt, requires_grad=system_prompt_require_grad, role_description=f"{self.name}'s system prompt")
    self.instruction = Variable(agent.actions[0].prompt_template.instruction, requires_grad=instruction_require_grad, role_description=f"{self.name}'s instruction prompt")
    self._agent_call = CustomAgentCall(agent)
    self.forward = StringBasedFunction(self._agent_call, agent.description)
    self.output_description = ' and '.join(agent.actions[0].outputs_format.get_attr_descriptions().values())
    self.last_output = None

def __call__(self, inputs: dict[str, Variable]) -> Variable:
    """Given textgrad.Variable inputs, generates a textgrad.Variable output."""
    forward_inputs: dict[str, Variable] = {'instruction': self.instruction, 'system_prompt': self.system_prompt, **inputs}
    output_variable = self.forward(forward_inputs, self.output_description)
    output_variable.parsed_outputs = self._agent_call.last_outputs
    self.last_output = output_variable
    return output_variable

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

def restore_best_graph(self) -> None:
    """Restore the best graph from the snapshot and set it to `self.graph`."""
    if len(self._snapshot) == 0:
        logger.info('No snapshot found. No graph to restore.')
        return
    best_graph, best_metrics = self._select_graph_with_highest_score(return_metrics=True)
    self.graph = best_graph
    logger.info(f'Restored the best graph from snapshot with metrics {best_metrics}')

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

class Optimizer(BaseModule):
    graph: Union[WorkFlowGraph, ActionGraph] = Field(description='The workflow to optimize.')
    evaluator: Evaluator = Field(description='The evaluator to use for optimization.')
    llm: BaseLLM = Field(default=None, description='The LLM to use for optimization and evaluation.')
    max_steps: int = Field(default=5, description='The maximum number of optimization steps to take.')
    eval_every_n_steps: int = Field(default=1, description='Evaluate the workflow every `eval_every_n_steps` steps.')
    eval_rounds: int = Field(default=1, description='Run evaluation for `eval_rounds` times and compute the average score.')
    convergence_threshold: int = Field(default=5, description='If the optimization has not improved the score for `convergence_threshold` steps, the optimization will be stopped.')

    def optimize(self, dataset: Benchmark, **kwargs):
        """
        Optimize the workflow.
        """
        raise NotImplementedError(f'``optimize`` function for {type(self).__name__} is not implemented!')

    def step(self, **kwargs):
        """
        Take a step of optimization.
        """
        raise NotImplementedError(f'``step`` function for {type(self).__name__} is not implemented!')

    def evaluate(self, dataset: Benchmark, eval_mode: str='test', graph: Optional[Union[WorkFlowGraph, ActionGraph]]=None, **kwargs) -> dict:
        """
        Evaluate the workflow. If `graph` is provided, use the provided graph for evaluation. Otherwise, use the graph in the optimizer.
        """
        raise NotImplementedError(f'``evaluate`` function for {type(self).__name__} is not implemented!')

    def convergence_check(self, *args, **kwargs) -> bool:
        """
        Check if the optimization has converged.
        """
        raise NotImplementedError(f'``convergence_check`` function for {type(self).__name__} is not implemented!')

def optimize(self, dataset: Benchmark, **kwargs):
    """
        Optimize the workflow.
        """
    raise NotImplementedError(f'``optimize`` function for {type(self).__name__} is not implemented!')

def step(self, **kwargs):
    """
        Take a step of optimization.
        """
    raise NotImplementedError(f'``step`` function for {type(self).__name__} is not implemented!')

def evaluate(self, dataset: Benchmark, eval_mode: str='test', graph: Optional[Union[WorkFlowGraph, ActionGraph]]=None, **kwargs) -> dict:
    """
        Evaluate the workflow. If `graph` is provided, use the provided graph for evaluation. Otherwise, use the graph in the optimizer.
        """
    raise NotImplementedError(f'``evaluate`` function for {type(self).__name__} is not implemented!')

def convergence_check(self, *args, **kwargs) -> bool:
    """
        Check if the optimization has converged.
        """
    raise NotImplementedError(f'``convergence_check`` function for {type(self).__name__} is not implemented!')

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

@wraps(original_evaluator)
def wrapped_evaluator(*args, **kwargs):
    result = original_evaluator(*args, **kwargs)
    if not isinstance(result, (float, int, bool)):
        raise TypeError(f'evaluator must return a float, int, or bool, got {type(result)}')
    return result

def _convert_to_dspy_module(self, registry: ParamRegistry, program: Callable):
    if isinstance(program, dspy.Module):
        return program
    program = PromptTuningModule.from_registry(program=program, registry=registry)
    return program

def _get_input_keys(self, dataset: Benchmark) -> Optional[List[str]]:
    input_keys = None
    if hasattr(dataset, 'get_input_keys'):
        candidate_input_keys = dataset.get_input_keys()
        if isinstance(candidate_input_keys, (list, tuple)) and all((isinstance(key, str) for key in candidate_input_keys)):
            input_keys = candidate_input_keys
    return input_keys

def _convert_benchmark_data_to_dspy_examples(self, data: List[dict], input_keys: List[str]) -> List[dspy.Example]:
    """
        Convert the benchmark data to a list of dspy Example. This is required since the evaluator accepts a list of dspy Example. 
        """
    dspy_examples = [example.with_inputs(*input_keys) if isinstance(example, dspy.Example) else dspy.Example(**example).with_inputs(*input_keys) for example in data]
    return dspy_examples

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

def metric(self, example: dspy.Example, prediction: Any, *args, **kwargs):
    return super().metric(example, prediction, *args, **kwargs)

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

def set_param(self, name: str, value: Any):
    """Set the value of a parameter by name."""
    self.registry.set(name, value)

def param_names(self) -> List[str]:
    """Return the list of all registered parameter names."""
    return self.registry.names()

def apply_cfg(self, cfg: Dict[str, Any]):
    """Apply a configuration dictionary to the registered parameters."""
    for k, v in cfg.items():
        if k in self.registry.fields:
            self.registry.set(k, v)

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

class OptimizableField:
    """
    Represents a parameter that can be optimized.

    This class encapsulates a runtime attribute using dynamic getter and setter
    functions. It allows the parameter to be exposed and manipulated by an external
    optimizer. An initial snapshot of the field can be stored and later used to reset
    the field to its original value.
    """

    def __init__(self, name: str, getter: Callable[[], Any], setter: Callable[[Any], None]):
        """
        Initialize an OptimizableField instance.

        Parameters
        ----------
        name : str
            The alias used to register the field in the registry.
        getter : Callable[[], Any]
            A function that returns the current value of the field.
        setter : Callable[[Any], None]
            A function that sets a new value to the field.
        """
        self.name = name
        self._get = getter
        self._set = setter
        self._initial_value = None

    def get(self) -> Any:
        """
        Retrieve the current value of the field.

        Returns
        -------
        Any
            The current value of the field.
        """
        return self._get()

    def set(self, value: Any) -> None:
        """
        Update the field with a new value.

        Parameters
        ----------
        value : Any
            The new value to assign to the field.
        """
        self._set(value)

    def init_snapshot(self) -> None:
        """
        Capture a snapshot of the current field value.

        This method stores a deep copy of the current field value so that it
        can be restored later using `reset()`.
        """
        current = self.get()
        self._initial_value = safe_deepcopy(current)

    def reset(self) -> None:
        """
        Reset the field to its initial value.

        If the current value object defines a `__reset__()` method, it will be
        called to perform the reset. Otherwise, the field is reset to the deep-copied
        initial value stored by `init_snapshot()`.

        Raises
        ------
        ValueError
            If `init_snapshot()` has not been called before `reset()`.
        """
        current = self.get()
        if self._initial_value is None:
            raise ValueError(f"Field '{self.name}' has no snapshot. Call init_snapshot() first.")
        if hasattr(current, '__reset__') and callable(current.__reset__):
            current.__reset__()
        else:
            self.set(safe_deepcopy(self._initial_value))

def init_snapshot(self) -> None:
    """
        Capture a snapshot of the current field value.

        This method stores a deep copy of the current field value so that it
        can be restored later using `reset()`.
        """
    current = self.get()
    self._initial_value = safe_deepcopy(current)

def reset(self) -> None:
    """
        Reset the field to its initial value.

        If the current value object defines a `__reset__()` method, it will be
        called to perform the reset. Otherwise, the field is reset to the deep-copied
        initial value stored by `init_snapshot()`.

        Raises
        ------
        ValueError
            If `init_snapshot()` has not been called before `reset()`.
        """
    current = self.get()
    if self._initial_value is None:
        raise ValueError(f"Field '{self.name}' has no snapshot. Call init_snapshot() first.")
    if hasattr(current, '__reset__') and callable(current.__reset__):
        current.__reset__()
    else:
        self.set(safe_deepcopy(self._initial_value))

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

def get_field(self, name: str) -> OptimizableField:
    """Retrieve the OptimizableField object by name."""
    if name not in self.fields:
        raise ValueError(f"Field '{name}' is not registered.")
    else:
        return self.fields[name]

def set(self, name: str, value: Any):
    """Set the value of a registered field by name."""
    self.fields[name].set(value)

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

def getter():
    return parent[leaf] if isinstance(parent, (list, dict)) else getattr(parent, leaf)

def setter(v):
    if isinstance(parent, (list, dict)):
        parent[leaf] = v
    else:
        setattr(parent, leaf, v)

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

def safe_deepcopy(obj):
    """
    Safely attempt to deep copy any Python object, with graceful fallback behavior.

    This function performs a standard `copy.deepcopy` when possible. If that fails
    (e.g., due to the presence of uncopyable components such as file handles, threads,
    or custom classes that don't support deep copying), it falls back to a more resilient strategy:

    1. Attempts to create a blank instance of the object's class using `__new__`.
    2. Recursively copies all attributes found in the object's `__dict__`, using:
    - `safe_deepcopy` for deep recursive copy,
    - `copy.copy` as a shallow fallback,
    - or the original reference as a last resort.
    3. If the object has no `__dict__` or cannot be instantiated, returns the original object.

    Parameters:
        obj (Any): The object to be deep copied.

    Returns:
        Any: A deep copy of the input object if possible, or a best-effort fallback copy.
    
    Warnings:
        Issues a `warnings.warn()` message whenever:
        - The deep copy fails and fallback mechanisms are used.
        - An attribute copy fails and falls back to a shallower or direct reference.
        - The class cannot be re-instantiated and the original reference is returned.

    Notes:
        - This function is intended for robust copying in systems where user-defined objects,
        templates, or agents may not support strict deep copying.
        - It is not guaranteed to preserve identity semantics or copy objects with `__slots__`.
        - For critical correctness or mutation isolation, ensure your objects are deepcopy-compatible.

    Example:
        >>> obj = CustomObject()
        >>> obj_copy = safe_deepcopy(obj)
    """
    try:
        return copy.deepcopy(obj)
    except Exception:
        warnings.warn(f'Failed to deepcopy {obj.__class__.__name__}. Falling back to advanced handling.')
        pass
    try:
        new_instance = obj.__class__.__new__(obj.__class__)
    except Exception:
        warnings.warn(f'Failed to create a blank instance of {obj.__class__.__name__}. Falling back to reference.')
        return obj
    for attr, value in getattr(obj, '__dict__', {}).items():
        try:
            setattr(new_instance, attr, safe_deepcopy(value))
        except Exception:
            try:
                warnings.warn(f'Failed to copy {attr} of {obj.__class__.__name__}. Falling back to shallow copy.')
                setattr(new_instance, attr, copy.copy(value))
            except Exception:
                warnings.warn(f'Failed to copy {attr} of {obj.__class__.__name__}. Falling back to reference.')
                setattr(new_instance, attr, value)
    return new_instance

class PromptTemplateRegister(ParamRegistry):
    """
    Unused Class
    Enhanced parameter registry that supports directly registering PromptTemplate instances
    or prompt strings as a single optimizable object.
    """

    def track(self, root_or_obj: Any, path_or_attr: str, *, name: str | None=None):
        if isinstance(root_or_obj, (list, tuple)):
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
        try:
            value = getattr(root_or_obj, path_or_attr)
        except AttributeError:
            return super().track(root_or_obj, path_or_attr, name=name)
        if isinstance(value, (str, PromptTemplate)):
            field = OptimizableField(key, getter=lambda: getattr(root_or_obj, path_or_attr), setter=lambda v: setattr(root_or_obj, path_or_attr, v))
            self.register_field(field)
            return self
        return super().track(root_or_obj, path_or_attr, name=name)

def track(self, root_or_obj: Any, path_or_attr: str, *, name: str | None=None):
    if isinstance(root_or_obj, (list, tuple)):
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
    try:
        value = getattr(root_or_obj, path_or_attr)
    except AttributeError:
        return super().track(root_or_obj, path_or_attr, name=name)
    if isinstance(value, (str, PromptTemplate)):
        field = OptimizableField(key, getter=lambda: getattr(root_or_obj, path_or_attr), setter=lambda v: setattr(root_or_obj, path_or_attr, v))
        self.register_field(field)
        return self
    return super().track(root_or_obj, path_or_attr, name=name)

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

def add_chunk(self, batch_chunk: Union[TextChunk, ImageChunk, List[Union[TextChunk, ImageChunk]]]):
    """Add a batch chunk to the corpus and update index."""
    if not isinstance(batch_chunk, list):
        batch_chunk = [batch_chunk]
    for chunk in batch_chunk:
        self.chunks.append(chunk)
        self.chunk_index[chunk.chunk_id] = chunk

def filter_by_doc_id(self, doc_id: str) -> List[Union[TextChunk, ImageChunk]]:
    """Filter chunks by parent document ID."""
    return [chunk for chunk in self.chunks if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id == doc_id]

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

class EmbeddingProvider(str, Enum):
    OPENAI = 'openai'
    AZURE_OPENAI = 'azure_openai'
    HUGGINGFACE = 'huggingface'
    OLLAMA = 'ollama'
    VOYAGE = 'voyage'

    @classmethod
    def validate_model(cls, provider: str, model_name: str) -> bool:
        """Validate if the model is supported for the given provider.

        Args:
            provider (str): The embedding provider (e.g., 'openai', 'huggingface', 'ollama').
            model_name (str): The name of the embedding model to validate.

        Returns:
            bool: True if the model is supported or provider is 'custom', False otherwise.

        Raises:
            ValueError: If the provider is invalid.
        """
        if provider not in SUPPORTED_MODELS:
            raise ValueError(f'Unsupported provider: {provider}')
        if provider == 'huggingface':
            if os.path.exists(model_name):
                return True
            return model_name in SUPPORTED_MODELS.get(provider, [])
        return model_name in SUPPORTED_MODELS.get(provider, [])

@classmethod
def validate_model(cls, provider: str, model_name: str) -> bool:
    """Validate if the model is supported for the given provider.

        Args:
            provider (str): The embedding provider (e.g., 'openai', 'huggingface', 'ollama').
            model_name (str): The name of the embedding model to validate.

        Returns:
            bool: True if the model is supported or provider is 'custom', False otherwise.

        Raises:
            ValueError: If the provider is invalid.
        """
    if provider not in SUPPORTED_MODELS:
        raise ValueError(f'Unsupported provider: {provider}')
    if provider == 'huggingface':
        if os.path.exists(model_name):
            return True
        return model_name in SUPPORTED_MODELS.get(provider, [])
    return model_name in SUPPORTED_MODELS.get(provider, [])

class BaseEmbeddingWrapper:
    """Base interface for embedding wrappers."""

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        raise NotImplementedError()

    def validate_model(self, provider: EmbeddingProvider, model_name: str) -> bool:
        """Validate if the model is supported for the given provider.

        Args:
            provider (EmbeddingProvider): The embedding provider.
            model_name (str): The name of the embedding model to validate.

        Returns:
            bool: True if the model is supported, False otherwise.
        """
        return EmbeddingProvider.validate_model(provider, model_name)

    @property
    def dimensions(self) -> int:
        raise NotImplementedError()

def get_embedding_model(self) -> BaseEmbedding:
    """Return the LlamaIndex-compatible embedding model."""
    raise NotImplementedError()

@property
def dimensions(self) -> int:
    raise NotImplementedError()

class VoyageEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for Voyage AI embedding models."""

    def __init__(self, model_name: str='voyage-multimodal-3', api_key: str=None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key or os.getenv('VOYAGE_API_KEY')
        self.kwargs = kwargs
        if not self.api_key:
            raise ValueError('Voyage API key is required. Set VOYAGE_API_KEY environment variable or pass api_key parameter.')
        self._embedding_model = VoyageEmbedding(model_name=model_name, api_key=self.api_key, **kwargs)
        logger.info(f'Voyage embedding wrapper initialized with model: {model_name}')

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        return self._embedding_model

    def validate_model(self, provider: EmbeddingProvider, model_name: str) -> bool:
        """Validate if the model is supported for Voyage AI.
        
        Args:
            provider (EmbeddingProvider): The embedding provider.
            model_name (str): The name of the embedding model to validate.
            
        Returns:
            bool: True if the model is supported, False otherwise.
        """
        supported_models = ['voyage-multimodal-3']
        return model_name in supported_models

    @property
    def dimensions(self) -> int:
        """Return the embedding dimension."""
        return self._embedding_model.dimension

def __init__(self, model_name: str='voyage-multimodal-3', api_key: str=None, **kwargs):
    self.model_name = model_name
    self.api_key = api_key or os.getenv('VOYAGE_API_KEY')
    self.kwargs = kwargs
    if not self.api_key:
        raise ValueError('Voyage API key is required. Set VOYAGE_API_KEY environment variable or pass api_key parameter.')
    self._embedding_model = VoyageEmbedding(model_name=model_name, api_key=self.api_key, **kwargs)
    logger.info(f'Voyage embedding wrapper initialized with model: {model_name}')

class EmbeddingFactory:
    """Factory for creating embedding models based on configuration."""

    def create(self, provider: EmbeddingProvider, model_config: Dict[str, Any]=None) -> BaseEmbeddingWrapper:
        """Create an embedding model based on the provider and configuration.
        
        Args:
            provider (EmbeddingProvider): The embedding provider (e.g., OpenAI, HuggingFace, Ollama).
            model_config (Dict[str, Any], optional): Configuration for the embedding model.
            
        Returns:
            BaseEmbeddingWrapper: A LlamaIndex-compatible embedding model wrapper.
            
        Raises:
            ValueError: If the provider or configuration is invalid.
        """
        model_config = model_config or {}
        model_config.pop('provider')
        if provider == EmbeddingProvider.OPENAI:
            wrapper = OpenAIEmbeddingWrapper(**model_config)
        elif provider == EmbeddingProvider.AZURE_OPENAI:
            wrapper = AzureOpenAIEmbeddingWrapper(**model_config)
        elif provider == EmbeddingProvider.HUGGINGFACE:
            wrapper = HuggingFaceEmbeddingWrapper(**model_config)
        elif provider == EmbeddingProvider.OLLAMA:
            wrapper = OllamaEmbeddingWrapper(**model_config)
        elif provider == EmbeddingProvider.VOYAGE:
            wrapper = VoyageEmbeddingWrapper(**model_config)
        else:
            raise ValueError(f'Unsupported embedding provider: {provider}')
        logger.info(f'Created embedding model for provider: {provider}')
        return wrapper

def create(self, provider: EmbeddingProvider, model_config: Dict[str, Any]=None) -> BaseEmbeddingWrapper:
    """Create an embedding model based on the provider and configuration.
        
        Args:
            provider (EmbeddingProvider): The embedding provider (e.g., OpenAI, HuggingFace, Ollama).
            model_config (Dict[str, Any], optional): Configuration for the embedding model.
            
        Returns:
            BaseEmbeddingWrapper: A LlamaIndex-compatible embedding model wrapper.
            
        Raises:
            ValueError: If the provider or configuration is invalid.
        """
    model_config = model_config or {}
    model_config.pop('provider')
    if provider == EmbeddingProvider.OPENAI:
        wrapper = OpenAIEmbeddingWrapper(**model_config)
    elif provider == EmbeddingProvider.AZURE_OPENAI:
        wrapper = AzureOpenAIEmbeddingWrapper(**model_config)
    elif provider == EmbeddingProvider.HUGGINGFACE:
        wrapper = HuggingFaceEmbeddingWrapper(**model_config)
    elif provider == EmbeddingProvider.OLLAMA:
        wrapper = OllamaEmbeddingWrapper(**model_config)
    elif provider == EmbeddingProvider.VOYAGE:
        wrapper = VoyageEmbeddingWrapper(**model_config)
    else:
        raise ValueError(f'Unsupported embedding provider: {provider}')
    logger.info(f'Created embedding model for provider: {provider}')
    return wrapper

class RetrieverFactory:
    """Factory for creating retrievers."""

    def create(self, retriever_type: str, llm: Optional[BaseLLM]=None, index: Optional[BaseIndex]=None, graph_store: Optional[GraphStore]=None, embed_model: Optional[BaseEmbedding]=None, query: Optional[Query]=None, storage_handler: Optional[StorageHandler]=None, chunk_class=None) -> BaseRetrieverWrapper:
        """Create a retriever based on configuration."""
        if retriever_type == RetrieverType.VECTOR.value:
            if not index:
                raise ValueError('Index required for vector retriever')
            retriever = VectorRetriever(index=index, top_k=query.top_k if query else 5, chunk_class=chunk_class)
        elif retriever_type == RetrieverType.GRAPH.value:
            if not (graph_store and embed_model and llm):
                raise ValueError('Graph store, embed model and llm model required for graph retriever')
            retriever = GraphRetriever(llm=llm, graph_store=graph_store, embed_model=embed_model, vector_store=storage_handler.vector_store, top_k=query.top_k if query else 5)
        else:
            raise ValueError(f'Unsupported retriever type: {retriever_type}')
        logger.info(f'Created retriever: {retriever_type}')
        return retriever

def create(self, retriever_type: str, llm: Optional[BaseLLM]=None, index: Optional[BaseIndex]=None, graph_store: Optional[GraphStore]=None, embed_model: Optional[BaseEmbedding]=None, query: Optional[Query]=None, storage_handler: Optional[StorageHandler]=None, chunk_class=None) -> BaseRetrieverWrapper:
    """Create a retriever based on configuration."""
    if retriever_type == RetrieverType.VECTOR.value:
        if not index:
            raise ValueError('Index required for vector retriever')
        retriever = VectorRetriever(index=index, top_k=query.top_k if query else 5, chunk_class=chunk_class)
    elif retriever_type == RetrieverType.GRAPH.value:
        if not (graph_store and embed_model and llm):
            raise ValueError('Graph store, embed model and llm model required for graph retriever')
        retriever = GraphRetriever(llm=llm, graph_store=graph_store, embed_model=embed_model, vector_store=storage_handler.vector_store, top_k=query.top_k if query else 5)
    else:
        raise ValueError(f'Unsupported retriever type: {retriever_type}')
    logger.info(f'Created retriever: {retriever_type}')
    return retriever

class BaseQueryTransform(ABC):

    @abstractmethod
    def _run(self, query: Query, metadata: Dict) -> Query:
        """The Main run logic for Transform"""

    def run(self, query_or_str: Union[str, Query], metadata: Optional[Dict]=None) -> Query:
        """Run query transform."""
        metadata = metadata or {}
        if isinstance(query_or_str, str):
            query = Query(query_str=query_or_str, custom_embedding_strs=[query_or_str])
        else:
            query = query_or_str
        return self._run(query, metadata=metadata)

    def __call__(self, query_bundle_or_str: Union[str, Query], metadata: Optional[Dict]=None) -> Query:
        """Run query processor."""
        return self.run(query_bundle_or_str, metadata=metadata)

def run(self, query_or_str: Union[str, Query], metadata: Optional[Dict]=None) -> Query:
    """Run query transform."""
    metadata = metadata or {}
    if isinstance(query_or_str, str):
        query = Query(query_str=query_or_str, custom_embedding_strs=[query_or_str])
    else:
        query = query_or_str
    return self._run(query, metadata=metadata)

class LLamaIndexReader:
    """A universal file reader based on LlamaIndex's SimpleDirectoryReader.

    This class provides a flexible interface for loading documents from files or directories,
    supporting various formats (e.g., PDF, Word, Markdown) with customizable filtering and metadata.

    Attributes:
        recursive (bool): Whether to recursively load files from directories.
        exclude_hidden (bool): Whether to exclude hidden files (starting with '.').
        num_workers (Optional[int]): Number of worker threads for parallel loading.
        num_files_limits (Optional[int]): Maximum number of files to load.
        custom_metadata_function (Optional[Callable]): Custom function to extract metadata.
        extern_file_extractor (Optional[Dict]): Custom file extractors for specific file types.
        errors (str): Error handling strategy for file reading (e.g., 'ignore', 'strict').
        encoding (str): File encoding (default: 'utf-8').
    """

    def __init__(self, recursive: bool=False, exclude_hidden: bool=True, num_workers: Optional[int]=None, num_files_limits: Optional[int]=None, custom_metadata_function: Optional[Callable]=None, extern_file_extractor: Optional[Dict]=None, errors: str='ignore', encoding: str='utf-8'):
        self.recursive = recursive
        self.exclude_hidden = exclude_hidden
        self.num_workers = num_workers
        self.num_files_limits = num_files_limits
        self.custom_metadata_function = custom_metadata_function
        self.extern_file_extractor = extern_file_extractor
        self.errors = errors
        self.encoding = encoding

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and convert a path to a Path object.

        Args:
            path: A string or Path object representing a file or directory.

        Returns:
            Path: A validated Path object.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the path is invalid.
        """
        path = Path(path)
        if not path.exists():
            logger.error(f'Path does not exist: {path}')
            raise FileNotFoundError(f'Path does not exist: {path}')
        return path

    def _check_input(self, input_data: Union[str, List, Tuple], is_file: bool=True) -> Union[List[Path], Path]:
        """Check input to a list of Path objects or a single Path for directories.

        Args:
            input_data: A string, list, or tuple of file/directory paths.
            is_file: Whether to treat input as file paths (True) or directory (False).

        Returns:
            Union[List[Path], Path]: Valied file paths or directory path.

        Raises:
            ValueError: If input type is invalid.
        """
        if isinstance(input_data, str):
            return self._validate_path(input_data)
        elif isinstance(input_data, (list, tuple)):
            if is_file:
                return [self._validate_path(p) for p in input_data]
            else:
                return self._validate_path(input_data[0])
        else:
            logger.error(f'Invalid input type: {type(input_data)}')
            raise ValueError(f'Invalid input type: {type(input_data)}')

    def load(self, file_paths: Union[str, List, Tuple], exclude_files: Optional[Union[str, List, Tuple]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple]]=None, merge_by_file: bool=False, show_progress: bool=False, use_async: bool=False) -> List[Document]:
        """Load documents from files or directories.

        Args:
            file_paths: A string, list, or tuple of file paths or a directory path.
            exclude_files: Files to exclude from loading.
            filter_file_by_suffix: File extensions to include (e.g., ['.pdf', '.docx']).

        Returns:
            List[Document]: List of loaded documents.

        Raises:
            FileNotFoundError: If input paths are invalid.
            RuntimeError: If document loading fails.
        """
        try:
            input_files = None
            input_dir = None
            if isinstance(file_paths, (list, tuple)):
                input_files = self._check_input(file_paths, is_file=True)
            else:
                path = self._check_input(file_paths, is_file=False)
                if path.is_dir():
                    input_dir = path
                else:
                    input_files = [path]
            exclude_files = self._check_input(exclude_files, is_file=True) if exclude_files else None
            filter_file_by_suffix = list(filter_file_by_suffix) if isinstance(filter_file_by_suffix, (list, tuple)) else [filter_file_by_suffix] if isinstance(filter_file_by_suffix, str) else None
            reader = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files, exclude=exclude_files, exclude_hidden=self.exclude_hidden, recursive=self.recursive, required_exts=filter_file_by_suffix, num_files_limit=self.num_files_limits, file_metadata=self.custom_metadata_function, file_extractor=self.extern_file_extractor, encoding=self.encoding, errors=self.errors)
            llama_docs = asyncio.run(reader.aload_data(show_progress=show_progress, num_workers=self.num_workers)) if use_async else reader.load_data(show_progress=show_progress)
            if merge_by_file:
                file_to_docs = {}
                for doc in llama_docs:
                    file_path = doc.metadata.get('file_path', '')
                    if file_path not in file_to_docs:
                        file_to_docs[file_path] = []
                    file_to_docs[file_path].append(doc)
                documents = []
                for file_path, docs in file_to_docs.items():
                    combined_text = '\n'.join((doc.text for doc in docs))
                    combined = docs[0].copy()
                    combined.text_resource.text = combined_text
                    combined.metadata['page_count'] = len(docs)
                    documents.append(Document.from_llama_document(combined))
            else:
                documents = [Document.from_llama_document(doc) for doc in llama_docs]
            logger.info(f'Loaded {len(documents)} documents')
            return documents
        except Exception as e:
            logger.error(f'Failed to load documents: {str(e)}')
            raise RuntimeError(f'Failed to load documents: {str(e)}')

def _check_input(self, input_data: Union[str, List, Tuple], is_file: bool=True) -> Union[List[Path], Path]:
    """Check input to a list of Path objects or a single Path for directories.

        Args:
            input_data: A string, list, or tuple of file/directory paths.
            is_file: Whether to treat input as file paths (True) or directory (False).

        Returns:
            Union[List[Path], Path]: Valied file paths or directory path.

        Raises:
            ValueError: If input type is invalid.
        """
    if isinstance(input_data, str):
        return self._validate_path(input_data)
    elif isinstance(input_data, (list, tuple)):
        if is_file:
            return [self._validate_path(p) for p in input_data]
        else:
            return self._validate_path(input_data[0])
    else:
        logger.error(f'Invalid input type: {type(input_data)}')
        raise ValueError(f'Invalid input type: {type(input_data)}')

class MultimodalReader:
    """An efficient image file reader for multimodal RAG.

    This class provides interface for loading images from files or directories,
    supporting various image formats with path-based lazy loading.

    Attributes:
        recursive (bool): Whether to recursively read directories.
        exclude_hidden (bool): Whether to exclude hidden files (starting with '.').
        num_files_limits (Optional[int]): Maximum number of files to read.
        errors (str): Error handling strategy for file reading (e.g., 'ignore', 'strict').
    """

    def __init__(self, recursive: bool=False, exclude_hidden: bool=True, num_files_limits: Optional[int]=None, errors: str='ignore'):
        self.recursive = recursive
        self.exclude_hidden = exclude_hidden
        self.num_files_limits = num_files_limits
        self.errors = errors

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and convert a path to a Path object.

        Args:
            path: A string or Path object representing a file or directory.

        Returns:
            Path: A validated Path object.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the path is invalid.
        """
        path = Path(path)
        if not path.exists():
            logger.error(f'Path does not exist: {path}')
            raise FileNotFoundError(f'Path does not exist: {path}')
        return path

    def _check_input(self, input_data: Union[str, List, Tuple], is_file: bool=True) -> Union[List[Path], Path]:
        """Check input to a list of Path objects or a single Path for directories.

        Args:
            input_data: A string, list, or tuple of file/directory paths.
            is_file: Whether to treat input as file paths (True) or directory (False).

        Returns:
            Union[List[Path], Path]: Valid file paths or directory path.

        Raises:
            ValueError: If input type is invalid.
        """
        if isinstance(input_data, str):
            return self._validate_path(input_data)
        elif isinstance(input_data, (list, tuple)):
            if is_file:
                return [self._validate_path(p) for p in input_data]
            else:
                return self._validate_path(input_data[0])
        else:
            logger.error(f'Invalid input type: {type(input_data)}')
            raise ValueError(f'Invalid input type: {type(input_data)}')

    def load(self, file_paths: Union[str, List, Tuple], exclude_files: Optional[Union[str, List, Tuple]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple]]=None, merge_by_file: bool=False, show_progress: bool=False) -> List[ImageDocument]:
        """Load images from files or directories.

        Args:
            file_paths: A string, list, or tuple of file paths or a directory path.
            exclude_files: Files to exclude from loading.
            filter_file_by_suffix: File extensions to include (e.g., ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']).
            merge_by_file: Whether to merge documents by file (unused for images, kept for compatibility).

        Returns:
            List[ImageDocument]: List of loaded ImageDocuments.

        Raises:
            FileNotFoundError: If input paths are invalid.
            RuntimeError: If image loading fails.
        """
        try:
            input_files = None
            input_dir = None
            if isinstance(file_paths, (list, tuple)):
                input_files = self._check_input(file_paths, is_file=True)
            else:
                path = self._check_input(file_paths, is_file=False)
                if path.is_dir():
                    input_dir = path
                else:
                    input_files = [path]
            exclude_files = self._check_input(exclude_files, is_file=True) if exclude_files else None
            filter_file_by_suffix = list(filter_file_by_suffix) if isinstance(filter_file_by_suffix, (list, tuple)) else [filter_file_by_suffix] if isinstance(filter_file_by_suffix, str) else None
            all_files = []
            if input_files:
                all_files = input_files
            elif input_dir:
                pattern = '**/*' if self.recursive else '*'
                all_files = [f for f in input_dir.glob(pattern) if f.is_file()]
                if self.exclude_hidden:
                    all_files = [f for f in all_files if not f.name.startswith('.')]
            if exclude_files:
                exclude_names = {f.name for f in exclude_files}
                all_files = [f for f in all_files if f.name not in exclude_names]
            if filter_file_by_suffix:
                all_files = [f for f in all_files if f.suffix.lower() in filter_file_by_suffix]
            if self.num_files_limits:
                all_files = all_files[:self.num_files_limits]
            documents = []
            for file_path in all_files:
                if show_progress:
                    logger.info(f'Processing: {file_path.name}')
                try:
                    if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                        img_doc = self._process_image(file_path)
                        if img_doc:
                            documents.append(img_doc)
                except Exception as e:
                    logger.error(f'Failed to process {file_path}: {str(e)}')
                    if self.errors == 'strict':
                        raise
            logger.info(f'Loaded {len(documents)} image documents')
            return documents
        except Exception as e:
            logger.error(f'Failed to load documents: {str(e)}')
            raise RuntimeError(f'Failed to load documents: {str(e)}')

    def _process_image(self, file_path: Path) -> ImageDocument:
        """Process a single image file."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format or 'Unknown'
            document = ImageDocument(text='', image=None, image_path=str(file_path), image_mimetype=f'image/{format_name.lower()}', metadata={'file_path': str(file_path), 'file_name': file_path.name, 'file_type': file_path.suffix, 'file_size': file_path.stat().st_size, 'creation_date': str(file_path.stat().st_ctime), 'last_modified_date': str(file_path.stat().st_mtime)})
            return document
        except Exception as e:
            logger.error(f'Failed to process image {file_path}: {str(e)}')
            if self.errors == 'strict':
                raise
            return None

def _check_input(self, input_data: Union[str, List, Tuple], is_file: bool=True) -> Union[List[Path], Path]:
    """Check input to a list of Path objects or a single Path for directories.

        Args:
            input_data: A string, list, or tuple of file/directory paths.
            is_file: Whether to treat input as file paths (True) or directory (False).

        Returns:
            Union[List[Path], Path]: Valid file paths or directory path.

        Raises:
            ValueError: If input type is invalid.
        """
    if isinstance(input_data, str):
        return self._validate_path(input_data)
    elif isinstance(input_data, (list, tuple)):
        if is_file:
            return [self._validate_path(p) for p in input_data]
        else:
            return self._validate_path(input_data[0])
    else:
        logger.error(f'Invalid input type: {type(input_data)}')
        raise ValueError(f'Invalid input type: {type(input_data)}')

class IndexFactory:
    """Factory for creating LlamaIndex indices."""

    def create(self, index_type: IndexType, embed_model: BaseEmbedding, storage_handler: StorageHandler, index_config: Dict[str, Any]=None, llm: Optional[BaseLLM]=None) -> BaseIndexWrapper:
        """Create an index based on configuration.
        
        Args:
            index_type (IndexType): The type of index to create.
            embed_model (BaseEmbedding): Embedding model for the index.
            storage_context (StorageContext): Storage context for persistence.
            index_config (Dict[str, Any], optional): Index-specific configuration.
            node_parser (Any, optional): Node parser (unused, kept for compatibility).
            
        Returns:
            BaseIndexWrapper: A wrapped LlamaIndex index.
            
        Raises:
            ValueError: If the index type or configuration is invalid.
        """
        index_config = index_config or {}
        if index_type == IndexType.VECTOR:
            index = VectorIndexing(embed_model=embed_model, storage_handler=storage_handler, index_config=index_config)
        elif index_type == IndexType.GRAPH:
            index = GraphIndexing(embed_model=embed_model, storage_handler=storage_handler, index_config=index_config, llm=llm)
        elif index_type == IndexType.SUMMARY:
            raise NotImplementedError()
        elif index_type == IndexType.TREE:
            raise NotImplementedError()
        else:
            raise ValueError(f'Unsupported index type: {index_type}')
        logger.info(f'Created index: {index_type}')
        return index

def create(self, index_type: IndexType, embed_model: BaseEmbedding, storage_handler: StorageHandler, index_config: Dict[str, Any]=None, llm: Optional[BaseLLM]=None) -> BaseIndexWrapper:
    """Create an index based on configuration.
        
        Args:
            index_type (IndexType): The type of index to create.
            embed_model (BaseEmbedding): Embedding model for the index.
            storage_context (StorageContext): Storage context for persistence.
            index_config (Dict[str, Any], optional): Index-specific configuration.
            node_parser (Any, optional): Node parser (unused, kept for compatibility).
            
        Returns:
            BaseIndexWrapper: A wrapped LlamaIndex index.
            
        Raises:
            ValueError: If the index type or configuration is invalid.
        """
    index_config = index_config or {}
    if index_type == IndexType.VECTOR:
        index = VectorIndexing(embed_model=embed_model, storage_handler=storage_handler, index_config=index_config)
    elif index_type == IndexType.GRAPH:
        index = GraphIndexing(embed_model=embed_model, storage_handler=storage_handler, index_config=index_config, llm=llm)
    elif index_type == IndexType.SUMMARY:
        raise NotImplementedError()
    elif index_type == IndexType.TREE:
        raise NotImplementedError()
    else:
        raise ValueError(f'Unsupported index type: {index_type}')
    logger.info(f'Created index: {index_type}')
    return index

class ChunkFactory:
    """Factory for creating chunkers based on configuration."""

    def create(self, strategy: ChunkingStrategy, embed_model: BaseEmbedding=None, chunker_config: Dict[str, Any]=None) -> BaseChunker:
        """Create a chunker based on strategy and configuration.
        
        Args:
            strategy (ChunkingStrategy): The chunking strategy.
            embed_model (BaseEmbedding, optional): Embedding model for semantic chunking.
            chunker_config (Dict[str, Any], optional): Chunker configuration.
            
        Returns:
            BaseChunker: A chunker instance.
            
        Raises:
            ValueError: If the strategy or configuration is invalid.
        """
        chunker_config = chunker_config or {}
        if strategy == ChunkingStrategy.SIMPLE:
            chunker = SimpleChunker(chunk_size=chunker_config.get('chunk_size', 1024), chunk_overlap=chunker_config.get('chunk_overlap', 20), max_workers=chunker_config.get('max_workers', 2))
        elif strategy == ChunkingStrategy.SEMANTIC:
            if not embed_model:
                raise ValueError('Embed model required for semantic chunking')
            chunker = SemanticChunker(embed_model=embed_model, similarity_threshold=chunker_config.get('similarity_threshold', 0.7), max_workers=chunker_config.get('max_workers', 2))
        elif strategy == ChunkingStrategy.HIERARCHICAL:
            chunker = HierarchicalChunker(chunk_sizes=chunker_config.get('chunk_sizes', [2048, 512, 128]), chunk_overlap=chunker_config.get('chunk_overlap', 20))
        else:
            raise ValueError(f'Unsupported chunking strategy: {strategy}')
        logger.info(f'Created chunker for strategy: {strategy}')
        return chunker

def create(self, strategy: ChunkingStrategy, embed_model: BaseEmbedding=None, chunker_config: Dict[str, Any]=None) -> BaseChunker:
    """Create a chunker based on strategy and configuration.
        
        Args:
            strategy (ChunkingStrategy): The chunking strategy.
            embed_model (BaseEmbedding, optional): Embedding model for semantic chunking.
            chunker_config (Dict[str, Any], optional): Chunker configuration.
            
        Returns:
            BaseChunker: A chunker instance.
            
        Raises:
            ValueError: If the strategy or configuration is invalid.
        """
    chunker_config = chunker_config or {}
    if strategy == ChunkingStrategy.SIMPLE:
        chunker = SimpleChunker(chunk_size=chunker_config.get('chunk_size', 1024), chunk_overlap=chunker_config.get('chunk_overlap', 20), max_workers=chunker_config.get('max_workers', 2))
    elif strategy == ChunkingStrategy.SEMANTIC:
        if not embed_model:
            raise ValueError('Embed model required for semantic chunking')
        chunker = SemanticChunker(embed_model=embed_model, similarity_threshold=chunker_config.get('similarity_threshold', 0.7), max_workers=chunker_config.get('max_workers', 2))
    elif strategy == ChunkingStrategy.HIERARCHICAL:
        chunker = HierarchicalChunker(chunk_sizes=chunker_config.get('chunk_sizes', [2048, 512, 128]), chunk_overlap=chunker_config.get('chunk_overlap', 20))
    else:
        raise ValueError(f'Unsupported chunking strategy: {strategy}')
    logger.info(f'Created chunker for strategy: {strategy}')
    return chunker

class PostprocessorFactory:
    """Factory for creating post-processors."""

    def create(self, postprocessor_type: str, query: Optional[Query]=None) -> BasePostprocessor:
        """Create a post-processor based on configuration.
        
        Args:
            postprocessor_type (str): Type of post-processor (e.g., 'simple', 'bge').
            query (Query, optional): Query for configuration.
            
        Returns:
            BasePostprocessor: A post-processor instance.
            
        Raises:
            ValueError: If the post-processor type or configuration is invalid.
        """
        if postprocessor_type == RerankerType.SIMPLE:
            if not query:
                raise ValueError('Query required for reranker')
            postprocessor = SimpleReranker(similarity_cutoff=query.similarity_cutoff, keyword_filters=query.keyword_filters)
        else:
            raise ValueError(f'Unsupported post-processor type: {postprocessor_type}')
        logger.info(f'Created post-processor: {postprocessor_type}')
        return postprocessor

def create(self, postprocessor_type: str, query: Optional[Query]=None) -> BasePostprocessor:
    """Create a post-processor based on configuration.
        
        Args:
            postprocessor_type (str): Type of post-processor (e.g., 'simple', 'bge').
            query (Query, optional): Query for configuration.
            
        Returns:
            BasePostprocessor: A post-processor instance.
            
        Raises:
            ValueError: If the post-processor type or configuration is invalid.
        """
    if postprocessor_type == RerankerType.SIMPLE:
        if not query:
            raise ValueError('Query required for reranker')
        postprocessor = SimpleReranker(similarity_cutoff=query.similarity_cutoff, keyword_filters=query.keyword_filters)
    else:
        raise ValueError(f'Unsupported post-processor type: {postprocessor_type}')
    logger.info(f'Created post-processor: {postprocessor_type}')
    return postprocessor

def evaluate_workflow_graph(prediction: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """Evaluate F1 score for graph workflow."""
    pred_nodes = set(prediction.get('nodes', []))
    true_nodes = set(ground_truth.get('nodes', []))
    pred_edges = set((tuple(edge) for edge in prediction.get('edges', [])))
    true_edges = set((tuple(edge) for edge in ground_truth.get('edges', [])))
    node_precision = len(pred_nodes & true_nodes) / len(pred_nodes) if pred_nodes else 0
    node_recall = len(pred_nodes & true_nodes) / len(true_nodes) if true_nodes else 0
    edge_precision = len(pred_edges & true_edges) / len(pred_edges) if pred_edges else 0
    edge_recall = len(pred_edges & true_edges) / len(true_edges) if true_edges else 0
    node_f1 = 2 * (node_precision * node_recall) / (node_precision + node_recall) if node_precision + node_recall > 0 else 0
    edge_f1 = 2 * (edge_precision * edge_recall) / (edge_precision + edge_recall) if edge_precision + edge_recall > 0 else 0
    return (node_f1 + edge_f1) / 2

class LiveCodeBench(CodingBenchmark):
    """Benchmark class for evaluating LLM capabilities on real-world programming tasks.
    
    LiveCodeBench provides a framework for evaluating different scenarios of code-related tasks:
    1. Code Generation: generating code from problem descriptions
    2. Test Output Prediction: predicting test outputs given test code
    3. Code Execution: generating code that executes correctly
    
    The benchmark supports different evaluation modes, metrics, and can be customized
    with various parameters like timeouts, sample dates, and processing options.
    
    Attributes:
        k: An integer or list of integers specifying which pass@k metrics to compute
        version: Release version of the dataset to use
        num_process: Number of processes to use for evaluation
        start_date: Filter problems to those after this date
        end_date: Filter problems to those before this date
        scenario: Type of programming task to evaluate ("code_generation", 
                  "test_output_prediction", or "code_execution")
        use_cot_for_execution: Whether to use chain-of-thought processing for code execution
    """

    def __init__(self, path: str=None, mode: str='all', timeout: int=60, k: Union[int, list]=1, num_process: int=6, scenario: str='code_generation', version: str='release_latest', start_date: str=None, end_date: str=None, use_cot_for_execution: bool=False, **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/livecodebench')
        self.k = k
        self.version = version
        self.num_process = num_process
        self.start_date = start_date
        self.end_date = end_date
        self.scenario = scenario
        self.use_cot_for_execution = use_cot_for_execution
        assert scenario in VALID_SCENARIO, f'Invalid scenario: {scenario}. Available choices: {VALID_SCENARIO}.'
        super().__init__(name=type(self).__name__, path=path, mode=mode, timeout=timeout, **kwargs)

    def _load_data(self):
        if self.mode == 'train' or self.mode == 'all':
            self._train_data = None
        if self.mode == 'dev' or self.mode == 'all':
            self._dev_data = None
        if self.mode == 'test' or self.mode == 'all':
            self._test_data = self._load_test_data()

    def _load_test_data(self):
        if self.scenario == 'code_generation':
            logger.info(f'Loading code generation dataset from {self.path} with version {self.version}.')
            data: List[CodeGenerationProblem] = load_code_generation_dataset(release_version=self.version, cache_dir=self.path, start_date=self.start_date, end_date=self.end_date)
        elif self.scenario == 'test_output_prediction':
            logger.info(f'Loading test output prediction dataset from {self.path}.')
            data: List[TestOutputPredictionProblem] = load_test_prediction_dataset(cache_dir=self.path)
        elif self.scenario == 'code_execution':
            logger.info(f'Loading code execution dataset from {self.path}.')
            data: List[CodeExecutionProblem] = load_code_execution_dataset(cache_dir=self.path)
        else:
            raise ValueError(f'Invalid scenario: {self.scenario}. Available choices: {VALID_SCENARIO}.')
        return data

    def _get_id(self, example: Union[CodeGenerationProblem, TestOutputPredictionProblem]) -> str:
        return example.question_id

    def _get_label(self, example: Union[CodeGenerationProblem, TestOutputPredictionProblem]) -> dict:
        return example.get_evaluation_sample()

    def evaluate(self, prediction: Any, label: Any) -> dict:
        """
        Evaluate the solution code.

        Args:
            prediction (str | List[str]): The solution code(s).
            label (dict | List[dict]): The test cases and expected outputs. 

        Returns:
            dict: The evaluation metrics (pass@k).
        """
        prediction, label = self._check_evaluation_inputs(prediction, label)
        k_list = [self.k] if isinstance(self.k, int) else self.k
        if self.scenario == 'code_generation':
            solutions: List[str] = [extract_code_blocks(pred)[0] for pred in prediction]
            metrics, results, metadatas = codegen_metrics(samples_list=label, generations_list=[solutions], k_list=k_list, num_process_evaluate=self.num_process, timeout=self.timeout)
        elif self.scenario == 'test_output_prediction':
            pred_outputs = [extract_test_output_code(pred) for pred in prediction]
            metrics, results = test_output_metrics(samples=label, generations=[pred_outputs], k_list=k_list)
        elif self.scenario == 'code_execution':
            pred_outputs = [extract_execution_code(pred, self.use_cot_for_execution) for pred in prediction]
            metrics, results = code_execution_metrics(samples=label, generations=[pred_outputs])
        else:
            raise ValueError(f'Invalid scenario: {self.scenario}. Available choices: {VALID_SCENARIO}.')
        pass_at_k = {f'pass@{k}': float(metrics[f'pass@{k}']) for k in k_list}
        return pass_at_k

def _load_test_data(self):
    if self.scenario == 'code_generation':
        logger.info(f'Loading code generation dataset from {self.path} with version {self.version}.')
        data: List[CodeGenerationProblem] = load_code_generation_dataset(release_version=self.version, cache_dir=self.path, start_date=self.start_date, end_date=self.end_date)
    elif self.scenario == 'test_output_prediction':
        logger.info(f'Loading test output prediction dataset from {self.path}.')
        data: List[TestOutputPredictionProblem] = load_test_prediction_dataset(cache_dir=self.path)
    elif self.scenario == 'code_execution':
        logger.info(f'Loading code execution dataset from {self.path}.')
        data: List[CodeExecutionProblem] = load_code_execution_dataset(cache_dir=self.path)
    else:
        raise ValueError(f'Invalid scenario: {self.scenario}. Available choices: {VALID_SCENARIO}.')
    return data

def evaluate(self, prediction: Any, label: Any) -> dict:
    """
        Evaluate the solution code.

        Args:
            prediction (str | List[str]): The solution code(s).
            label (dict | List[dict]): The test cases and expected outputs. 

        Returns:
            dict: The evaluation metrics (pass@k).
        """
    prediction, label = self._check_evaluation_inputs(prediction, label)
    k_list = [self.k] if isinstance(self.k, int) else self.k
    if self.scenario == 'code_generation':
        solutions: List[str] = [extract_code_blocks(pred)[0] for pred in prediction]
        metrics, results, metadatas = codegen_metrics(samples_list=label, generations_list=[solutions], k_list=k_list, num_process_evaluate=self.num_process, timeout=self.timeout)
    elif self.scenario == 'test_output_prediction':
        pred_outputs = [extract_test_output_code(pred) for pred in prediction]
        metrics, results = test_output_metrics(samples=label, generations=[pred_outputs], k_list=k_list)
    elif self.scenario == 'code_execution':
        pred_outputs = [extract_execution_code(pred, self.use_cot_for_execution) for pred in prediction]
        metrics, results = code_execution_metrics(samples=label, generations=[pred_outputs])
    else:
        raise ValueError(f'Invalid scenario: {self.scenario}. Available choices: {VALID_SCENARIO}.')
    pass_at_k = {f'pass@{k}': float(metrics[f'pass@{k}']) for k in k_list}
    return pass_at_k

def remove_punc(text: str) -> str:
    exclude = set(string.punctuation)
    return ''.join((ch for ch in text if ch not in exclude))

def exact_match_score(prediction: str, ground_truth: str) -> float:
    assert isinstance(ground_truth, str), f'ground_truth must be a string, but got {type(ground_truth)}'
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))

def f1_score(prediction: str, ground_truth: str) -> float:
    assert isinstance(ground_truth, str), f'ground_truth must be a string, but got {type(ground_truth)}'
    normalized_prediction = normalize_answer(prediction)
    normalized_ground_truth = normalize_answer(ground_truth)
    ZERO_METRIC = (0, 0, 0)
    if normalized_prediction in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC[0]
    if normalized_ground_truth in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC[0]
    prediction_tokens = normalized_prediction.split()
    ground_truth_tokens = normalized_ground_truth.split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return ZERO_METRIC[0]
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return f1

def acc_score(prediction: str, ground_truths: List[str]) -> float:
    assert isinstance(ground_truths, list), f'ground_truths must be a list, but got {type(ground_truths)}'
    return float(has_answer(answers=ground_truths, text=prediction, match_type='string'))

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

def get_function(compiled_sol, fn_name: str):
    try:
        assert hasattr(compiled_sol, fn_name)
        return getattr(compiled_sol, fn_name)
    except Exception:
        return

def truncatefn(s, length=300):
    if isinstance(s, str):
        pass
    else:
        s = str(s)
    if len(s) <= length:
        return s
    return s[:length // 2] + '...(truncated) ...' + s[-length // 2:]

def call_method(method, inputs):
    if isinstance(inputs, list):
        inputs = '\n'.join(inputs)
    inputs_line_iterator = iter(inputs.split('\n'))

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
    return _inner_call_method(method)

class Callback:
    """
    a base class for callbacks 
    """

    def on_error(self, exception, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        try:
            result = self.run(*args, **kwargs)
        except Exception as e:
            self.on_error(e, *args, kwargs)
            raise e
        return result

    def run(self, *args, **kwargs):
        raise NotImplementedError(f'run is not implemented for {type(self).__name__}!')

def run(self, *args, **kwargs):
    raise NotImplementedError(f'run is not implemented for {type(self).__name__}!')

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

def _ensure_callbacks(self):
    if not hasattr(self.local_data, 'callbacks'):
        self.local_data.callbacks = {}

@contextmanager
def suppress_cost_logging():
    """Thread-safe context manager: only suppresses cost-related logs without affecting other info-level logs"""
    token = suppress_cost_logs.set(True)
    try:
        yield
    finally:
        suppress_cost_logs.reset(token)

def get_error_message(errors: List[Union[ValidationError, Exception]]) -> str:
    if not isinstance(errors, list):
        errors = [errors]
    validation_errors, exceptions = ([], [])
    for error in errors:
        if isinstance(error, ValidationError):
            validation_errors.append(error)
        else:
            exceptions.append(error)
    message = ''
    if len(validation_errors) > 0:
        message += f' >>>>>>>> {len(validation_errors)} Validation Errors: <<<<<<<<\n\n'
        message += '\n\n'.join([str(error) for error in validation_errors])
    if len(exceptions) > 0:
        if len(message) > 0:
            message += '\n\n'
        message += f'>>>>>>>> {len(exceptions)} Exception Errors: <<<<<<<<\n\n'
        message += '\n\n'.join([str(type(error).__name__) + ': ' + str(error) for error in exceptions])
    return message

class ModuleRegistry:

    def __init__(self):
        self.module_dict = {}

    def register_module(self, cls_name: str, cls):
        if cls_name in self.module_dict:
            raise ValueError(f'Found duplicate module: `{cls_name}`!')
        self.module_dict[cls_name] = cls

    def get_module(self, cls_name: str):
        if cls_name not in self.module_dict:
            raise ValueError(f'module `{cls_name}` not Found!')
        return self.module_dict[cls_name]

    def has_module(self, cls_name: str) -> bool:
        return cls_name in self.module_dict

def register_module(self, cls_name: str, cls):
    if cls_name in self.module_dict:
        raise ValueError(f'Found duplicate module: `{cls_name}`!')
    self.module_dict[cls_name] = cls

def get_module(self, cls_name: str):
    if cls_name not in self.module_dict:
        raise ValueError(f'module `{cls_name}` not Found!')
    return self.module_dict[cls_name]

def register_module(cls_name, cls):
    MODULE_REGISTRY.register_module(cls_name=cls_name, cls=cls)

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

def register(self, key: str, model_cls, config_cls):
    if key in self.models:
        raise ValueError(f"model name '{key}' is already registered!")
    self.models[key] = model_cls
    self.model_configs[key] = config_cls

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

@model_validator(mode='before')
@classmethod
def validate_data(cls, data: Any) -> Any:
    if 'msg_type' in data and data['msg_type'] and isinstance(data['msg_type'], str):
        data['msg_type'] = MessageType(data['msg_type'])
    return data

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

class MetaModule(ModelMetaclass):
    """
    MetaModule is a metaclass that automatically registers all subclasses of BaseModule.

    
    Attributes:
        No public attributes
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        """
        Creates a new class and registers it in MODULE_REGISTRY.
        
        Args:
            mcs: The metaclass itself
            name: The name of the class being created
            bases: Tuple of base classes
            namespace: Dictionary containing the class attributes and methods
            **kwargs: Additional keyword arguments
        
        Returns:
            The created class object
        """
        cls = super().__new__(mcs, name, bases, namespace)
        register_module(name, cls)
        return cls

def __new__(mcs, name, bases, namespace, **kwargs):
    """
        Creates a new class and registers it in MODULE_REGISTRY.
        
        Args:
            mcs: The metaclass itself
            name: The name of the class being created
            bases: Tuple of base classes
            namespace: Dictionary containing the class attributes and methods
            **kwargs: Additional keyword arguments
        
        Returns:
            The created class object
        """
    cls = super().__new__(mcs, name, bases, namespace)
    register_module(name, cls)
    return cls

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

def create_llm_instance(llm_config: LLMConfig) -> BaseLLM:
    llm_cls = MODEL_REGISTRY.get_model(llm_config.llm_type)
    llm = llm_cls(config=llm_config)
    return llm

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

def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
    return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

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

def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
    return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

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

@register_model(config_cls=LiteLLMConfig, alias=['litellm'])
class LiteLLM(OpenAILLM):

    def init_model(self):
        """
        Initialize the model based on the configuration.
        """
        if self.config.llm_type != 'LiteLLM':
            raise ValueError("llm_type must be 'LiteLLM'")
        self.model = self.config.model
        self.api_base = self.config.api_base
        self.api_key = self.config.api_key
        company = infer_litellm_company_from_model(self.model)
        if self.config.is_local or company == 'local':
            if not self.api_base:
                raise ValueError('api_base is required for local models in LiteLLMConfig')
            litellm.api_base = self.api_base
            litellm.api_key = self.api_key
        elif company == 'openai':
            if not self.config.openai_key:
                raise ValueError('OpenAI API key is required for OpenAI models. You should set `openai_key` in LiteLLMConfig')
            os.environ['OPENAI_API_KEY'] = self.config.openai_key
        elif company == 'azure':
            if not self.config.azure_key or not self.config.azure_endpoint:
                raise ValueError('Azure OpenAI key and endpoint are required for Azure models. You should set `azure_key` and `azure_endpoint` in LiteLLMConfig')
            os.environ['AZURE_API_KEY'] = self.config.azure_key
            os.environ['AZURE_API_BASE'] = self.config.azure_endpoint
            if self.config.api_version:
                os.environ['AZURE_API_VERSION'] = self.config.api_version
        elif company == 'deepseek':
            if not self.config.deepseek_key:
                raise ValueError('DeepSeek API key is required for DeepSeek models. You should set `deepseek_key` in LiteLLMConfig')
            os.environ['DEEPSEEK_API_KEY'] = self.config.deepseek_key
        elif company == 'anthropic':
            if not self.config.anthropic_key:
                raise ValueError('Anthropic API key is required for Anthropic models. You should set `anthropic_key` in LiteLLMConfig')
            os.environ['ANTHROPIC_API_KEY'] = self.config.anthropic_key
        elif company == 'gemini':
            if not self.config.gemini_key:
                raise ValueError('Gemini API key is required for Gemini models. You should set `gemini_key` in LiteLLMConfig')
            os.environ['GEMINI_API_KEY'] = self.config.gemini_key
        elif company == 'meta_llama':
            if not self.config.meta_llama_key:
                raise ValueError('Meta Llama API key is required for Meta Llama models. You should set `meta_llama_key` in LiteLLMConfig')
            os.environ['LLAMA_API_KEY'] = self.config.meta_llama_key
        elif company == 'openrouter':
            if not self.config.openrouter_key:
                raise ValueError('OpenRouter API key is required for OpenRouter models. You should set `openrouter_key` in LiteLLMConfig. You can also set `openrouter_base` in LiteLLMConfig to use a custom base URL [optional]')
            os.environ['OPENROUTER_API_KEY'] = self.config.openrouter_key
            os.environ['OPENROUTER_API_BASE'] = self.config.openrouter_base
        elif company == 'perplexity':
            if not self.config.perplexity_key:
                raise ValueError('Perplexity API key is required for Perplexity models. You should set `perplexity_key` in LiteLLMConfig')
            os.environ['PERPLEXITYAI_API_KEY'] = self.config.perplexity_key
        elif company == 'groq':
            if not self.config.groq_key:
                raise ValueError('Groq API key is required for Groq models. You should set `groq_key` in LiteLLMConfig')
            os.environ['GROQ_API_KEY'] = self.config.groq_key
        else:
            raise ValueError(f'Unsupported company: {company}')
        self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key', 'api_base', 'is_local', 'azure_endpoint', 'azure_key', 'api_version', 'api_key']

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        if self.config.is_local:
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
        return super()._compute_cost(input_tokens, output_tokens)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response using the completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            company = infer_litellm_company_from_model(self.model)
            if self.config.is_local or company == 'local':
                completion_params['api_base'] = self.api_base
            elif company == 'azure':
                completion_params['api_base'] = self.config.azure_endpoint
                completion_params['api_version'] = self.config.api_version
                completion_params['api_key'] = self.config.azure_key
            response = completion(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response=response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """
        Generate responses for a batch of messages.

        Args: 
            batch_messages (List[List[dict]]): A list of message lists, where each sublist represents a conversation.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            List[str]: A list of responses for each conversation.
        """
        results = []
        for messages in batch_messages:
            response = self.single_generate(messages, **kwargs)
            results.append(response)
        return results

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response using the async completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            company = infer_litellm_company_from_model(self.model)
            if self.config.is_local or company == 'local':
                completion_params['api_base'] = self.api_base
            elif company == 'azure':
                completion_params['api_base'] = self.config.azure_endpoint
                completion_params['api_version'] = self.config.api_version
                completion_params['api_key'] = self.config.azure_key
            response = await acompletion(messages=messages, **completion_params)
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response=response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async: {str(e)}')
        return output

def init_model(self):
    """
        Initialize the model based on the configuration.
        """
    if self.config.llm_type != 'LiteLLM':
        raise ValueError("llm_type must be 'LiteLLM'")
    self.model = self.config.model
    self.api_base = self.config.api_base
    self.api_key = self.config.api_key
    company = infer_litellm_company_from_model(self.model)
    if self.config.is_local or company == 'local':
        if not self.api_base:
            raise ValueError('api_base is required for local models in LiteLLMConfig')
        litellm.api_base = self.api_base
        litellm.api_key = self.api_key
    elif company == 'openai':
        if not self.config.openai_key:
            raise ValueError('OpenAI API key is required for OpenAI models. You should set `openai_key` in LiteLLMConfig')
        os.environ['OPENAI_API_KEY'] = self.config.openai_key
    elif company == 'azure':
        if not self.config.azure_key or not self.config.azure_endpoint:
            raise ValueError('Azure OpenAI key and endpoint are required for Azure models. You should set `azure_key` and `azure_endpoint` in LiteLLMConfig')
        os.environ['AZURE_API_KEY'] = self.config.azure_key
        os.environ['AZURE_API_BASE'] = self.config.azure_endpoint
        if self.config.api_version:
            os.environ['AZURE_API_VERSION'] = self.config.api_version
    elif company == 'deepseek':
        if not self.config.deepseek_key:
            raise ValueError('DeepSeek API key is required for DeepSeek models. You should set `deepseek_key` in LiteLLMConfig')
        os.environ['DEEPSEEK_API_KEY'] = self.config.deepseek_key
    elif company == 'anthropic':
        if not self.config.anthropic_key:
            raise ValueError('Anthropic API key is required for Anthropic models. You should set `anthropic_key` in LiteLLMConfig')
        os.environ['ANTHROPIC_API_KEY'] = self.config.anthropic_key
    elif company == 'gemini':
        if not self.config.gemini_key:
            raise ValueError('Gemini API key is required for Gemini models. You should set `gemini_key` in LiteLLMConfig')
        os.environ['GEMINI_API_KEY'] = self.config.gemini_key
    elif company == 'meta_llama':
        if not self.config.meta_llama_key:
            raise ValueError('Meta Llama API key is required for Meta Llama models. You should set `meta_llama_key` in LiteLLMConfig')
        os.environ['LLAMA_API_KEY'] = self.config.meta_llama_key
    elif company == 'openrouter':
        if not self.config.openrouter_key:
            raise ValueError('OpenRouter API key is required for OpenRouter models. You should set `openrouter_key` in LiteLLMConfig. You can also set `openrouter_base` in LiteLLMConfig to use a custom base URL [optional]')
        os.environ['OPENROUTER_API_KEY'] = self.config.openrouter_key
        os.environ['OPENROUTER_API_BASE'] = self.config.openrouter_base
    elif company == 'perplexity':
        if not self.config.perplexity_key:
            raise ValueError('Perplexity API key is required for Perplexity models. You should set `perplexity_key` in LiteLLMConfig')
        os.environ['PERPLEXITYAI_API_KEY'] = self.config.perplexity_key
    elif company == 'groq':
        if not self.config.groq_key:
            raise ValueError('Groq API key is required for Groq models. You should set `groq_key` in LiteLLMConfig')
        os.environ['GROQ_API_KEY'] = self.config.groq_key
    else:
        raise ValueError(f'Unsupported company: {company}')
    self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key', 'api_base', 'is_local', 'azure_endpoint', 'azure_key', 'api_version', 'api_key']

def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
    """
        Generate responses for a batch of messages.

        Args: 
            batch_messages (List[List[dict]]): A list of message lists, where each sublist represents a conversation.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            List[str]: A list of responses for each conversation.
        """
    results = []
    for messages in batch_messages:
        response = self.single_generate(messages, **kwargs)
        results.append(response)
    return results

class GeneratedAgent(BaseModule):
    """
    Representation of a generated agent with validation capabilities.
    """
    name: str
    description: str
    inputs: List[Parameter]
    outputs: List[Parameter]
    prompt: str
    tool_names: Optional[List[str]] = None

    @classmethod
    def find_output_name(cls, text: str, outputs: List[str]):

        def sim(t1: str, t2: str):
            t1_words = normalize_text(t1).split()
            t2_words = normalize_text(t2).split()
            return len(set(t1_words) & set(t2_words))
        similarities = [sim(text, output) for output in outputs]
        max_sim = max(similarities)
        return outputs[similarities.index(max_sim)]

    @model_validator(mode='after')
    @classmethod
    def validate_prompt(cls, agent: 'GeneratedAgent'):
        """Validate and fix the agent's prompt template.
        
        This validator ensures that:
        1. All input parameters are properly referenced in the prompt
        2. Input references use the correct format with braces
        3. All output sections match the defined output parameters
        
        If there are mismatches in the output sections, it attempts to
        fix them by finding the most similar output name.
        
        Args:
            agent: The GeneratedAgent instance to validate.
            
        Returns:
            The validated and potentially modified GeneratedAgent.
            
        Raises:
            ValueError: If inputs are missing from the prompt or output sections don't match the defined outputs.
        """
        input_names = [inp.name for inp in agent.inputs]
        prompt_has_inputs = [name in agent.prompt for name in input_names]
        if not all(prompt_has_inputs):
            missing_input_names = [name for name, has_input in zip(input_names, prompt_has_inputs) if not has_input]
            raise ValueError(f'The prompt miss inputs: {missing_input_names}')
        pattern = '### Instructions(.*?)### Output Format'
        prompt = agent.prompt

        def replace_with_braces(match):
            instructions = match.group(1)
            for name in input_names:
                instructions = re.sub(f'<input>{{*\\b{re.escape(name)}\\b}}*</input>', f'<input>{{{name}}}</input>', instructions)
            return '### Instructions' + instructions + '### Output Format'
        modified_prompt = re.sub(pattern, replace_with_braces, prompt, flags=re.DOTALL)
        agent.prompt = modified_prompt
        prompt = agent.prompt
        pattern = '### Output Format(.*)'
        outputs_names = [out.name for out in agent.outputs]

        def fix_output_names(match):
            output_format = match.group(1)
            matches = re.findall('## ([^\\n#]+)', output_format, flags=re.DOTALL)
            generated_outputs = [m.strip() for m in matches if m.strip() != 'Thought']
            if len(generated_outputs) != len(outputs_names):
                raise ValueError(f"The number of outputs in the prompt is different from that defined in the `outputs` field of the agent. The outputs in the prompt are: {generated_outputs}, while the outputs from the agent's `outputs` field are: {outputs_names}")
            for generated_output in generated_outputs:
                if generated_output not in outputs_names:
                    most_similar_output_name = cls.find_output_name(text=generated_output, outputs=outputs_names)
                    output_format = output_format.replace(generated_output, most_similar_output_name)
                    logger.warning(f"Couldn't find output name in prompt ('{generated_output}') in agent's outputs. Replace it with the most similar agent output: '{most_similar_output_name}'")
            return '### Output Format' + output_format
        modified_prompt = re.sub(pattern, fix_output_names, prompt, flags=re.DOTALL)
        agent.prompt = modified_prompt
        return agent

def sim(t1: str, t2: str):
    t1_words = normalize_text(t1).split()
    t2_words = normalize_text(t2).split()
    return len(set(t1_words) & set(t2_words))

@model_validator(mode='after')
@classmethod
def validate_prompt(cls, agent: 'GeneratedAgent'):
    """Validate and fix the agent's prompt template.
        
        This validator ensures that:
        1. All input parameters are properly referenced in the prompt
        2. Input references use the correct format with braces
        3. All output sections match the defined output parameters
        
        If there are mismatches in the output sections, it attempts to
        fix them by finding the most similar output name.
        
        Args:
            agent: The GeneratedAgent instance to validate.
            
        Returns:
            The validated and potentially modified GeneratedAgent.
            
        Raises:
            ValueError: If inputs are missing from the prompt or output sections don't match the defined outputs.
        """
    input_names = [inp.name for inp in agent.inputs]
    prompt_has_inputs = [name in agent.prompt for name in input_names]
    if not all(prompt_has_inputs):
        missing_input_names = [name for name, has_input in zip(input_names, prompt_has_inputs) if not has_input]
        raise ValueError(f'The prompt miss inputs: {missing_input_names}')
    pattern = '### Instructions(.*?)### Output Format'
    prompt = agent.prompt

    def replace_with_braces(match):
        instructions = match.group(1)
        for name in input_names:
            instructions = re.sub(f'<input>{{*\\b{re.escape(name)}\\b}}*</input>', f'<input>{{{name}}}</input>', instructions)
        return '### Instructions' + instructions + '### Output Format'
    modified_prompt = re.sub(pattern, replace_with_braces, prompt, flags=re.DOTALL)
    agent.prompt = modified_prompt
    prompt = agent.prompt
    pattern = '### Output Format(.*)'
    outputs_names = [out.name for out in agent.outputs]

    def fix_output_names(match):
        output_format = match.group(1)
        matches = re.findall('## ([^\\n#]+)', output_format, flags=re.DOTALL)
        generated_outputs = [m.strip() for m in matches if m.strip() != 'Thought']
        if len(generated_outputs) != len(outputs_names):
            raise ValueError(f"The number of outputs in the prompt is different from that defined in the `outputs` field of the agent. The outputs in the prompt are: {generated_outputs}, while the outputs from the agent's `outputs` field are: {outputs_names}")
        for generated_output in generated_outputs:
            if generated_output not in outputs_names:
                most_similar_output_name = cls.find_output_name(text=generated_output, outputs=outputs_names)
                output_format = output_format.replace(generated_output, most_similar_output_name)
                logger.warning(f"Couldn't find output name in prompt ('{generated_output}') in agent's outputs. Replace it with the most similar agent output: '{most_similar_output_name}'")
        return '### Output Format' + output_format
    modified_prompt = re.sub(pattern, fix_output_names, prompt, flags=re.DOTALL)
    agent.prompt = modified_prompt
    return agent

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

@register_action_function
def divide_numbers(a: int, b: int) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b

def semantic_similarity(text1, text2):
    """Calculate semantic similarity"""
    text1_norm = normalize_text(text1)
    text2_norm = normalize_text(text2)
    words1 = set(text1_norm.split())
    words2 = set(text2_norm.split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0

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

def test_cycle_detection(self):
    """Test cycle detection in a workflow."""
    loops = self.cycle_graph._find_all_loops()
    self.assertTrue(loops)
    self.assertTrue(self.cycle_graph.is_loop_start('Task2'))
    self.assertTrue(self.cycle_graph.is_loop_end('Task3'))

def get_tool(name, key):
    return ToyTool(name, key)

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

def init_module(self):
    if self.k6 is None:
        if self.k4 is not None and self.k5 is not None:
            self.k6 = ToyTool(self.k4, self.k5)
        else:
            raise ValueError(f'either k4 and k5 is None!')

