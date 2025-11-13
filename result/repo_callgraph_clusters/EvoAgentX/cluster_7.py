# Cluster 7

class MemoryAction(Action):

    def __init__(self, name: str='MemoryAction', description: str='Action that processes user input with long-term memory context', prompt: str='Based on the following context and user prompt, provide a relevant response:\n\nContext: {context}\n\nUser Prompt: {user_prompt}\n\n', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or MemoryActionInput
        outputs_format = outputs_format or MemoryActionOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: BaseLLM | None=None, inputs: Dict | None=None, sys_msg: str | None=None, return_prompt: bool=False, memory_manager: Optional[MemoryManager]=None, **kwargs) -> Parser | Tuple[Parser | str] | None:
        return asyncio.run(self.async_execute(llm, inputs, sys_msg, return_prompt, memory_manager, **kwargs))

    async def async_execute(self, llm: Optional['BaseLLM']=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory_manager: Optional[MemoryManager]=None, **kwargs) -> Union[MemoryActionOutput, tuple]:
        if not memory_manager:
            logger.error('MemoryManager is required for MemoryAction execution')
            raise ValueError('MemoryManager is required for MemoryAction')
        action_input = self.inputs_format(**inputs)
        user_prompt = action_input.user_prompt
        conversation_id = action_input.conversation_id
        if not conversation_id:
            conversation_id = str(uuid4())
            logger.warning('No conversation_id provided; generated a new UUID4 for this session')
        top_k = action_input.top_k
        metadata_filters = action_input.metadata_filters
        message = await memory_manager.create_conversation_message(user_prompt=user_prompt, conversation_id=conversation_id, top_k=top_k, metadata_filters=metadata_filters)
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: getattr(action_input, attr, 'undefined') for attr in action_input_attrs}
        action_input_data['context'] = message.content
        prompt = self.prompt.format(**action_input_data)
        logger.info(f'The New Created Message by LongTermMemory:\n\n{prompt}')
        output = await llm.async_generate(prompt=prompt, system_message=sys_msg, parser=self.outputs_format, parse_mode='str')
        response_message = Message(content=output.content, msg_type=MessageType.RESPONSE, timestamp=datetime.now().isoformat(), conversation_id=conversation_id, memory_ids=message.memory_ids)
        memory_ids = await memory_manager.handle_memory(action='add', data=response_message)
        final_output = self.outputs_format(response=output.content, memory_ids=memory_ids)
        if return_prompt:
            return (final_output, prompt)
        return final_output

def execute(self, llm: BaseLLM | None=None, inputs: Dict | None=None, sys_msg: str | None=None, return_prompt: bool=False, memory_manager: Optional[MemoryManager]=None, **kwargs) -> Parser | Tuple[Parser | str] | None:
    return asyncio.run(self.async_execute(llm, inputs, sys_msg, return_prompt, memory_manager, **kwargs))

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

def _create_output_message(self, action_output, action_name: str, action_input_data: Optional[Dict], prompt: str, return_msg_type: MessageType=MessageType.RESPONSE, **kwargs) -> Message:
    msg = super()._create_output_message(action_output=action_output, action_name=action_name, action_input_data=action_input_data, prompt=prompt, return_msg_type=return_msg_type, **kwargs)
    if action_input_data and 'user_prompt' in action_input_data:
        user_msg = Message(content=action_input_data['user_prompt'], msg_type=MessageType.REQUEST, conversation_id=msg.conversation_id)
        asyncio.create_task(self.memory_manager.handle_memory(action='add', data=user_msg))
    response_msg = Message(content=action_output.response if hasattr(action_output, 'response') else str(action_output), msg_type=MessageType.RESPONSE, conversation_id=msg.conversation_id)
    asyncio.create_task(self.memory_manager.handle_memory(action='add', data=response_msg))
    return msg

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

def __call__(self, *args: Any, **kwargs: Any) -> Union[dict, Coroutine[Any, Any, dict]]:
    """Make the operator callable and automatically choose between sync and async execution."""
    try:
        asyncio.get_running_loop()
        return self.async_execute(*args, **kwargs)
    except RuntimeError:
        return self.execute(*args, **kwargs)

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

def execute(self, llm: BaseLLM, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
    """synchronous execution entry"""
    try:
        loop = asyncio.get_running_loop()
        if loop:
            pass
        raise RuntimeError('Cannot use asyncio.run() in async context. Use async_execute directly.')
    except RuntimeError:
        return asyncio.run(self.async_execute(llm, inputs, hitl_manager, sys_msg=sys_msg, **kwargs))

class HITLInterceptorAction(Action):
    """HITL Interceptor Action"""

    def __init__(self, target_agent_name: str, target_action_name: str, name: str=None, description: str='A pre-defined action to proceed the Human-In-The-Loop', interaction_type: HITLInteractionType=HITLInteractionType.APPROVE_REJECT, mode: HITLMode=HITLMode.PRE_EXECUTION, **kwargs):
        if not name:
            name = f'hitl_intercept_{target_agent_name}_{target_action_name}_mode_{mode.value}_action'
        super().__init__(name=name, description=description, **kwargs)
        self.target_agent_name = target_agent_name
        self.target_action_name = target_action_name
        self.interaction_type = interaction_type
        self.mode = mode

    def execute(self, llm, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        try:
            loop = asyncio.get_running_loop()
            if loop:
                pass
            raise RuntimeError('Cannot use asyncio.run() in async context. Use async_execute directly.')
        except RuntimeError:
            return asyncio.run(self.async_execute(llm, inputs, hitl_manager, sys_msg=sys_msg, **kwargs))

    async def async_execute(self, llm, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        """
        Asynchronous execution of HITL Interceptor
        """
        task_name = kwargs.get('wf_task', 'Unknown Task')
        workflow_goal = kwargs.get('wf_goal', None)
        response = await hitl_manager.request_approval(task_name=task_name, agent_name=self.target_agent_name, action_name=self.target_action_name, interaction_type=self.interaction_type, mode=self.mode, action_inputs_data=inputs, workflow_goal=workflow_goal)
        result = {'hitl_decision': response.decision, 'target_agent': self.target_agent_name, 'target_action': self.target_action_name, 'hitl_feedback': response.feedback}
        for output_name in self.outputs_format.get_attrs():
            try:
                result |= {output_name: inputs[hitl_manager.hitl_input_output_mapping[output_name]]}
            except Exception as e:
                logger.exception(e)
        prompt = f'HITL Interceptor executed for {self.target_agent_name}.{self.target_action_name}'
        if result['hitl_decision'] == HITLDecision.APPROVE:
            prompt += '\nHITL approved, the action will be executed'
            return (result, prompt)
        elif result['hitl_decision'] == HITLDecision.REJECT:
            prompt += '\nHITL rejected, the action will not be executed'
            sys.exit()

def execute(self, llm, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
    try:
        loop = asyncio.get_running_loop()
        if loop:
            pass
        raise RuntimeError('Cannot use asyncio.run() in async context. Use async_execute directly.')
    except RuntimeError:
        return asyncio.run(self.async_execute(llm, inputs, hitl_manager, sys_msg=sys_msg, **kwargs))

class HITLUserInputCollectorAction(Action):
    """HITL User Input Collector Action - Collect user input for the HITL Interceptor"""

    def __init__(self, name: str=None, agent_name: str=None, description: str='A pre-defined action to collect user input for the HITL Interceptor', interaction_type: HITLInteractionType=HITLInteractionType.COLLECT_USER_INPUT, input_fields: dict=None, **kwargs):
        if not name:
            pass
        super().__init__(name=name, description=description, **kwargs)
        self.interaction_type = interaction_type
        self.input_fields = input_fields or {}
        self.agent_name = agent_name

    def execute(self, llm, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        try:
            loop = asyncio.get_running_loop()
            if loop:
                pass
            raise RuntimeError('Cannot use asyncio.run() in async context. Use async_execute directly.')
        except RuntimeError:
            return asyncio.run(self.async_execute(llm, inputs, hitl_manager, sys_msg=sys_msg, **kwargs))

    async def async_execute(self, llm, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
        """
        Asynchronous execution of HITL User Input Collector
        """
        task_name = kwargs.get('wf_task', 'Unknown Task')
        workflow_goal = kwargs.get('wf_goal', None)
        response = await hitl_manager.request_user_input(task_name=task_name, agent_name=self.agent_name, action_name=self.name, input_fields=self.input_fields, workflow_goal=workflow_goal)
        result = {'hitl_decision': response.decision, 'collected_user_input': response.modified_content or {}, 'hitl_feedback': response.feedback}
        if self.outputs_format:
            for output_name in self.outputs_format.get_attrs():
                if output_name in response.modified_content:
                    result[output_name] = response.modified_content[output_name]
        prompt = f'HITL User Input Collector executed: {self.name}'
        if result['hitl_decision'] == HITLDecision.CONTINUE:
            prompt += f'\nUser input collection completed: {result['collected_user_input']}'
            return (result, prompt)
        elif result['hitl_decision'] == HITLDecision.REJECT:
            prompt += '\nUser cancelled input or error occurred'
            sys.exit()

def execute(self, llm, inputs: dict, hitl_manager: HITLManager, sys_msg: str=None, **kwargs) -> Tuple[dict, str]:
    try:
        loop = asyncio.get_running_loop()
        if loop:
            pass
        raise RuntimeError('Cannot use asyncio.run() in async context. Use async_execute directly.')
    except RuntimeError:
        return asyncio.run(self.async_execute(llm, inputs, hitl_manager, sys_msg=sys_msg, **kwargs))

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

def __call__(self, *args: Any, **kwargs: Any) -> Union[dict, Coroutine[Any, Any, dict]]:
    """Make the operator callable and automatically choose between sync and async execution."""
    try:
        asyncio.get_running_loop()
        return self.async_execute(*args, **kwargs)
    except RuntimeError:
        return self.execute(*args, **kwargs)

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

def disconnect(self):
    for server in self.servers:
        try:
            server._disconnect()
        except Exception as e:
            logger.warning(f'Error disconnecting from MCP server: {str(e)}')
    self.servers.clear()

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

def clear(self) -> None:
    """
        Clear the node and relation in the neo4j graph database.
        """
    with self.graph_store.client.session() as session:
        session.run('MATCH (n) DETACH DELETE n')
        session.run('CALL apoc.schema.assert({}, {})')

class CodeBlock:
    """
    Parameters
    ----------
    name : str
        逻辑名（日志、调试友好）
    func : Callable[[dict], Any]
        普通同步函数，输入 cfg 字典
    """

    def __init__(self, name: str, func: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self._func = func

    def run(self, cfg: Dict[str, Any]) -> Any:
        """同步执行封装的函数。"""
        return self._func(cfg)

    def __call__(self, cfg: Dict[str, Any]) -> Any:
        return self.run(cfg)

    def __repr__(self):
        return f'<CodeBlock {self.name} (sync)>'

def __call__(self, cfg: Dict[str, Any]) -> Any:
    return self.run(cfg)

def main():
    flow = Workflow()
    registry = PromptRegistry()
    registry.register_path(flow, 'system_prompt', name='sys_prompt')
    registry.register_path(flow, 'sampler.temperature')
    registry.register_path(flow, 'sampler.top_p')
    code_block = CodeBlock('run_workflow', lambda cfg: flow.run())

    def evaluator(cfg, result) -> float:
        return result['score']
    opt = RandomSearchOptimizer(registry, metric='score', max_trials=10)
    best_cfg, history = opt.run(code_block, evaluator)
    print('\n=== Trial history ===')
    for i, (cfg, score) in enumerate(history, 1):
        print(f'{i:02d}: score={score:.3f}, cfg={cfg}')
    print('\n=== Best ===')
    print(best_cfg)

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

def query(self, query: Union[str, Query], corpus_id: Optional[str]=None, query_transforms: Optional[List]=None) -> RagResult:
    """Synchronous wrapper for the async query method."""
    return asyncio.run(self.query_async(query, corpus_id, query_transforms))

class VoyageEmbedding(BaseEmbedding):
    """Voyage AI multimodal embedding model compatible with LlamaIndex BaseEmbedding."""
    api_key: str = ''
    client: Optional[voyageai.AsyncClient] = None
    model_name: str = 'voyage-multimodal-3'
    embed_batch_size: int = 10
    _dimension: Optional[int] = None

    def __init__(self, model_name: str='voyage-multimodal-3', api_key: str=None, **kwargs):
        api_key = api_key or os.getenv('VOYAGE_API_KEY') or ''
        if not api_key:
            raise ValueError('Voyage API key is required. Set VOYAGE_API_KEY environment variable or pass api_key parameter.')
        super().__init__(model_name=model_name, embed_batch_size=10, api_key=api_key)
        self.client = voyageai.AsyncClient(api_key=api_key)
        if 'voyage-multimodal-3' in model_name:
            self._dimension = 1024
        else:
            self._dimension = 1024
        logger.debug(f'Initialized Voyage embedding model: {model_name}')

    async def _async_embed_documents(self, documents: List[Any]) -> List[List[float]]:
        """Async method to embed documents (images or text)."""
        try:
            inputs = []
            for doc in documents:
                if isinstance(doc, str):
                    inputs.append({'content': [{'type': 'text', 'text': doc}]})
                elif isinstance(doc, Image.Image):
                    inputs.append([doc])
                elif hasattr(doc, 'get_image'):
                    image = doc.get_image()
                    if image:
                        inputs.append([image])
                    else:
                        raise ValueError(f'Could not load image from document: {doc}')
                else:
                    inputs.append([doc])
            result = await self.client.multimodal_embed(inputs=inputs, model=self.model_name, input_type='document')
            return result.embeddings
        except Exception as e:
            logger.error(f'Error embedding documents with Voyage: {str(e)}')
            raise

    async def _async_embed_query(self, query: Union[str, Dict, List]) -> List[float]:
        """Async method to embed a query."""
        try:
            if isinstance(query, str):
                formatted_query = {'content': [{'type': 'text', 'text': query}]}
            elif isinstance(query, dict):
                formatted_query = query
            elif isinstance(query, list):
                formatted_query = {'content': query}
            else:
                formatted_query = {'content': [{'type': 'text', 'text': str(query)}]}
            result = await self.client.multimodal_embed(inputs=[formatted_query], model=self.model_name, input_type='query')
            return result.embeddings[0]
        except Exception as e:
            logger.error(f'Error embedding query with Voyage: {str(e)}')
            raise

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query string (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._async_embed_query(query))

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a text string (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._async_embed_documents([text]))[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._async_embed_documents(texts))

    def _get_image_embedding(self, image_node) -> List[float]:
        """Get embedding for an ImageNode."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._async_embed_documents([image_node]))[0]

    def get_image_embedding(self, image: Union[Image.Image, Any]) -> List[float]:
        """Get embedding for an image."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._async_embed_documents([image]))[0]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Asynchronous query embedding."""
        return await self._async_embed_query(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Asynchronous text embedding."""
        return (await self._async_embed_documents([text]))[0]

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Asynchronous batch text embedding."""
        return await self._async_embed_documents(texts)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

def _get_query_embedding(self, query: str) -> List[float]:
    """Get embedding for a query string (sync wrapper)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(self._async_embed_query(query))

def _get_text_embedding(self, text: str) -> List[float]:
    """Get embedding for a text string (sync wrapper)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(self._async_embed_documents([text]))[0]

def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts (sync wrapper)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(self._async_embed_documents(texts))

def _get_image_embedding(self, image_node) -> List[float]:
    """Get embedding for an ImageNode."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(self._async_embed_documents([image_node]))[0]

def get_image_embedding(self, image: Union[Image.Image, Any]) -> List[float]:
    """Get embedding for an image."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(self._async_embed_documents([image]))[0]

class BasicGraphExtractLLM(TransformComponent):
    """
    A TransformComponent for extracting knowledge graph triplets using an LLM without tool-calling capabilities.

    This class performs two-stage extraction:
    1. Entity extraction: Identifies named entities and their types (e.g., Person, Organization).
    2. Relation extraction: Identifies directed relationships between extracted entities.

    The extracted entities and relations are stored in the node's metadata for use in LlamaIndex's PropertyGraphIndex.

    Attributes:
        llm (BaseLLM): The language model for entity and relation extraction.
        entity_extract_prompt (str): Prompt template for entity extraction.
        relation_extract_prompt (str): Prompt template for relation extraction.
        num_workers (int): Number of workers for parallel processing of nodes.
    """
    llm: BaseLLM
    entity_extract_prompt: str
    relation_extract_prompt: str
    num_workers: int

    def __init__(self, llm: BaseLLM, entity_extract_prompt: Optional[str]=None, relation_extract_prompt: Optional[str]=None, num_workers: int=4):
        """
        Initialize the BasicGraphExtractLLM.

        Args:
            llm (BaseLLM): The language model to use for extraction.
            entity_extract_prompt (Optional[str]): Custom prompt for entity extraction. Defaults to ENTITY_EXTRACT_PROMPT.
            relation_extract_prompt (Optional[str]): Custom prompt for relation extraction. Defaults to RELATION_EXTRACT_PROMPT.
            num_workers (int): Number of workers for parallel node processing. Defaults to 4.
        """
        super().__init__(llm=llm, entity_extract_prompt=entity_extract_prompt or ENTITY_EXTRACT_PROMPT, relation_extract_prompt=relation_extract_prompt or RELATION_EXTRACT_PROMPT, num_workers=num_workers)

    async def _aextract(self, node: BaseNode) -> BaseNode:
        """
        Asynchronously extract entities and relations from a single node.

        This method performs two LLM calls:
        1. Extracts entities and their types using the entity_extract_prompt.
        2. Extracts relations between entities using the relation_extract_prompt.

        The results are stored in the node's metadata under KG_NODES_KEY and KG_RELATIONS_KEY.

        Args:
            node (BaseNode): The node containing text to process.

        Returns:
            BaseNode: The node with updated metadata containing extracted entities and relations.

        Raises:
            AssertionError: If the node lacks a 'text' attribute.
            ValueError: If JSON parsing of LLM output fails (handled with empty fallback).
        """
        assert hasattr(node, 'text'), "Node must have a 'text' attribute"
        text = node.get_content(metadata_mode=MetadataMode.LLM)
        try:
            extract_prompt = self.entity_extract_prompt.replace('{text}', text)
            llm_response = await self.llm.async_generate(prompt=extract_prompt, parse_mode='json')
            json_string = llm_response.content.strip()
            entity_label_mapping = {entity_dict['name']: entity_dict['type'] for entity_dict in LLMOutputParser._parse_json_content(json_string)['entities']}
            relation_extract_prompt = self.relation_extract_prompt.replace('{text}', text).replace('{entities_json}', json_string)
            llm_response = self.llm.generate(prompt=relation_extract_prompt, parse_mode='json')
            triples = LLMOutputParser._parse_json_content(llm_response.content.strip())['graph']
        except ValueError as e:
            logger.warning(f'Failed to parse LLM output for node {node.node_id}: {str(e)}. Returning empty triples.')
            entity_label_mapping = {}
            triples = []
        logger.info(f'Extracted triples from chunk: {triples}')
        existing_nodes = node.metadata.pop(KG_NODES_KEY, [])
        existing_relations = node.metadata.pop(KG_RELATIONS_KEY, [])
        metadata = node.metadata.copy()
        for triple in triples:
            subj, rel, obj = (triple['source'], triple['relation'], triple['target'])
            subj = subj.capitalize().replace(' ', '_')
            rel = rel.lower().replace(' ', '_')
            obj = obj.capitalize().replace(' ', '_')
            subj_node = EntityNode(name=subj, label=entity_label_mapping.get(subj, 'entity'))
            obj_node = EntityNode(name=obj, label=entity_label_mapping.get(obj, 'entity'))
            rel_node = Relation(label=rel, source_id=subj_node.id, target_id=obj_node.id, properties=metadata)
            existing_nodes.extend([subj_node, obj_node])
            existing_relations.append(rel_node)
        node.metadata[KG_NODES_KEY] = existing_nodes
        node.metadata[KG_RELATIONS_KEY] = existing_relations
        return node

    def __call__(self, nodes: Sequence[BaseNode], show_progress: bool=False, **kwargs: Any) -> Sequence[BaseNode]:
        """
        Synchronously extract triples from a sequence of nodes.

        This method wraps the asynchronous acall method for synchronous execution.

        Args:
            nodes (Sequence[BaseNode]): The nodes to process.
            show_progress (bool): Whether to display a progress bar. Defaults to False.
            **kwargs: Additional keyword arguments passed to acall.

        Returns:
            Sequence[BaseNode]: The processed nodes with updated metadata.
        """
        return asyncio.run(self.acall(nodes, show_progress=show_progress, **kwargs))

    async def acall(self, nodes: Sequence[BaseNode], show_progress: bool=False, **kwargs: Any) -> Sequence[BaseNode]:
        """
        Asynchronously extract triples from a sequence of nodes.

        This method processes nodes in parallel using run_jobs for efficiency.

        Args:
            nodes (Sequence[BaseNode]): The nodes to process.
            show_progress (bool): Whether to display a progress bar. Defaults to False.
            **kwargs: Additional keyword arguments passed to run_jobs.

        Returns:
            Sequence[BaseNode]: The processed nodes with updated metadata.
        """
        jobs = [self._aextract(node, **kwargs) for node in nodes]
        return await run_jobs(jobs, workers=self.num_workers, show_progress=show_progress, desc='Extracting paths from text')

    @classmethod
    def class_name(cls) -> str:
        return 'BasicGraphExtractLLM'

def __call__(self, nodes: Sequence[BaseNode], show_progress: bool=False, **kwargs: Any) -> Sequence[BaseNode]:
    """
        Synchronously extract triples from a sequence of nodes.

        This method wraps the asynchronous acall method for synchronous execution.

        Args:
            nodes (Sequence[BaseNode]): The nodes to process.
            show_progress (bool): Whether to display a progress bar. Defaults to False.
            **kwargs: Additional keyword arguments passed to acall.

        Returns:
            Sequence[BaseNode]: The processed nodes with updated metadata.
        """
    return asyncio.run(self.acall(nodes, show_progress=show_progress, **kwargs))

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

def __call__(self, query_bundle_or_str: Union[str, Query], metadata: Optional[Dict]=None) -> Query:
    """Run query processor."""
    return self.run(query_bundle_or_str, metadata=metadata)

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

def load(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
    """
        Synchronously load nodes into the vector index.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): The nodes to load.
        """
    return asyncio.run(self.aload(nodes))

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

def load(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
    """
        Synchronously load nodes into the graph index.

        Wraps the asynchronous aload method to provide a synchronous interface for loading nodes.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to load, either Chunk or BaseNode.

        """
    return asyncio.run(self.aload(nodes))

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

def __call__(self, *args, **kwargs):
    try:
        result = self.run(*args, **kwargs)
    except Exception as e:
        self.on_error(e, *args, kwargs)
        raise e
    return result

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

def search(self, query: Union[str, Query], n: Optional[int]=None, metadata_filters: Optional[Dict]=None) -> List[Tuple[Message, str]]:
    """Synchronous wrapper for searching memories."""
    return asyncio.run(self.search_async(query, n, metadata_filters))

