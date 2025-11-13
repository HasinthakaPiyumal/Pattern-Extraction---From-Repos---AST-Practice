# Cluster 9

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

def _prepare_solutions(self, solutions: List[str]) -> Tuple[dict, str]:
    answer_mapping = {}
    solution_text = ''
    for index, solution in enumerate(solutions):
        answer_mapping[chr(65 + index)] = index
        solution_text += f'{chr(65 + index)}: \n{str(solution)}\n\n\n'
    return (answer_mapping, solution_text)

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

def _prepare_solutions(self, solutions: List[str]) -> Tuple[dict, str]:
    answer_mapping = {}
    solution_text = ''
    for index, solution in enumerate(solutions):
        answer_mapping[chr(65 + index)] = index
        solution_text += f'{chr(65 + index)}: \n{str(solution)}\n\n\n'
    return (answer_mapping, solution_text)

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

def print_results(self):
    """
        Print average score and standard deviation for all rounds.
        """
    self.avg_scores, self.stds = self.calculate_avg_and_std()
    for i, (avg_score, std) in enumerate(zip(self.avg_scores, self.stds), 1):
        logger.info(f'Round {i}: Average Score = {avg_score:.4f}, Standard Deviation = {std:.4f}')

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

def load_operators_description(self, operators: List[str], llm: BaseLLM) -> str:
    operators_description = ''
    for id, operator in enumerate(operators):
        operator_description = self._load_operator_description(id + 1, operator, llm)
        operators_description += f'{operator_description}\n'
    return operators_description

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

def create_result_data(self, round: int, score: float, avg_cost: float, total_cost: float) -> dict:
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {'round': round, 'score': score, 'avg_cost': avg_cost, 'total_cost': total_cost, 'time': now}

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

def _format_message(self, message: Message) -> Dict[str, Any]:
    """
        Format a Telegram message for consistent output.
        
        Args:
            message: Telegram message object
            
        Returns:
            dict: Formatted message data
        """
    return {'id': message.id, 'text': message.text or '', 'date': message.date.isoformat() if message.date else None, 'sender_id': message.sender_id, 'chat_id': message.chat_id, 'is_reply': message.reply_to_msg_id is not None, 'reply_to_msg_id': message.reply_to_msg_id, 'has_media': message.media is not None, 'media_type': type(message.media).__name__ if message.media else None}

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

def _qp_score(self, problem: str, text: str) -> float:
    qv = _tf_vector(_tokenize(problem))
    tv = _tf_vector(_tokenize(text))
    return _cosine_sim(qv, tv)

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

def _create_default_debater_agent(self) -> CustomizeAgent:
    """Create default debater CustomizeAgent (XML parsing thought/argument/answer)."""
    llm_config = random.choice(self.llm_config_pool) if self.llm_config_pool else self.llm_config
    return CustomizeAgent(name='DebaterAgent', description='Generate argument/rebuttal and optional answer per debate round.', prompt=DEBATER_AGENT_PROMPT, llm_config=llm_config, inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'transcript_text', 'type': 'str', 'description': 'Formatted debate transcript so far'}, {'name': 'role', 'type': 'str', 'description': 'Debater role/persona'}, {'name': 'agent_id', 'type': 'str', 'description': 'Debater id (string)'}, {'name': 'round_index', 'type': 'str', 'description': '1-based round index'}, {'name': 'total_rounds', 'type': 'str', 'description': 'Total rounds'}], outputs=[{'name': 'thought', 'type': 'str', 'description': 'Brief reasoning', 'required': True}, {'name': 'argument', 'type': 'str', 'description': 'Argument or rebuttal', 'required': True}, {'name': 'answer', 'type': 'str', 'description': 'Optional current answer', 'required': False}], parse_mode='xml')

def _create_default_judge_agent(self) -> CustomizeAgent:
    """Create default judge CustomizeAgent (XML parsing rationale/winning_agent_id/final_answer)."""
    llm_config = random.choice(self.llm_config_pool) if self.llm_config_pool else self.llm_config
    return CustomizeAgent(name='JudgeAgent', description='Deliver final decision and answer based on debate transcript.', prompt=JUDGE_AGENT_PROMPT, llm_config=llm_config, inputs=[{'name': 'problem', 'type': 'str', 'description': 'Problem statement'}, {'name': 'transcript_text', 'type': 'str', 'description': 'Formatted debate transcript'}, {'name': 'roles_text', 'type': 'str', 'description': 'Roles listing text'}], outputs=[{'name': 'rationale', 'type': 'str', 'description': 'Judging rationale', 'required': True}, {'name': 'winning_agent_id', 'type': 'str', 'description': 'Winning agent id (integer as string)', 'required': True}, {'name': 'final_answer', 'type': 'str', 'description': 'Final answer', 'required': True}], parse_mode='xml')

class Workflow:

    def __init__(self):
        self.system_prompt = 'You are a helpful assistant.'
        self.few_shot = 'Q: 1+1=?\nA: 2'
        self.sampler = Sampler()

    def execute(self):
        pass

    def run(self):
        prompt = f'{self.system_prompt}\n{self.few_shot}\nUser: Hi'
        return {'prompt': prompt, 'score': random.uniform(0, 1)}

def run(self):
    prompt = f'{self.system_prompt}\n{self.few_shot}\nUser: Hi'
    return {'prompt': prompt, 'score': random.uniform(0, 1)}

class RandomSearchOptimizer(BaseCodeBlockOptimizer):

    def sample_cfg(self) -> Dict[str, Any]:
        return {'sampler_temperature': random.uniform(0.3, 1.3), 'sampler_top_p': random.uniform(0.5, 1.0), 'sys_prompt': random.choice(['You are a helpful assistant.', 'You are a super-concise assistant.'])}

    def update(self, cfg, score):
        pass

def sample_cfg(self) -> Dict[str, Any]:
    return {'sampler_temperature': random.uniform(0.3, 1.3), 'sampler_top_p': random.uniform(0.5, 1.0), 'sys_prompt': random.choice(['You are a helpful assistant.', 'You are a super-concise assistant.'])}

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

def sample_cfg(self):
    return {'sampler_temperature': random.uniform(0.3, 1.3), 'sampler_top_p': random.uniform(0.5, 1.0), 'sys_prompt': random.choice(['You are a helpful assistant.', 'You are a super-concise assistant.'])}

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

def compute_hash(self) -> str:
    """Compute a hash of the document text for deduplication."""
    return hashlib.sha256(self.text.encode()).hexdigest()

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

def sort_by_similarity(self, reverse: bool=True) -> List[Union[TextChunk, ImageChunk]]:
    """Sort chunks by similarity score (descending by default)."""
    return sorted([chunk for chunk in self.chunks if chunk.metadata.similarity_score is not None], key=lambda x: x.metadata.similarity_score, reverse=reverse)

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

def insert_output(self, output_list: list[str], pred_list: list[str]) -> dict:
    return {'question_id': self.question_id, 'contest_id': self.contest_id, 'contest_date': self.contest_date.isoformat(), 'difficulty': self.difficulty, 'function_name': self.function_name, 'code': self.code, 'input': self.input, 'output': self.output, 'id': self.id, 'problem_id': self.problem_id, 'numsteps': self.numsteps, 'output_list': output_list, 'pred_list': pred_list}

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

def insert_output(self, output_list: list[str], code_list: list[str]) -> dict:
    return {'question_title': self.question_title, 'question_content': self.question_content, 'platform': self.platform.value, 'question_id': self.question_id, 'contest_id': self.contest_id, 'contest_date': self.contest_date.isoformat(), 'starter_code': self.starter_code, 'difficulty': self.difficulty.value, 'output_list': output_list, 'code_list': code_list}

def codegen_metrics(samples_list, generations_list, k_list=[1, 5, 10, 20, 40, 50, 75, 100, 125, 150, 200, 500, 1000], num_process_evaluate=16, timeout=6, debug=False):
    samples_linear = []
    generations_linear = []
    remap_index = []
    results = defaultdict(list)
    metadatas = defaultdict(list)
    for idx, (sample, generation_list) in enumerate(zip(samples_list, generations_list)):
        assert isinstance(generation_list, list), generations_list[0]
        for generation in generation_list:
            assert isinstance(generation, str), generations_list[0]
            samples_linear.append(sample)
            generations_linear.append([generation])
            remap_index.append(idx)
    results_linear, metadatas_linear = evaluate_generations(samples_linear, generations_linear, debug=debug, num_process_evaluate=num_process_evaluate, timeout=timeout)
    for idx, sub_results in sorted(results_linear.items(), key=lambda x: x[0]):
        results[remap_index[idx]].append(sub_results[0])
    for idx, sub_metadatas in sorted(metadatas_linear.items(), key=lambda x: x[0]):
        metadatas[remap_index[idx]].append(sub_metadatas[0])
    metrics = compute_metrics_from_results(results, k_list=k_list)
    final_metadata = []
    for key in sorted(list(metadatas.keys())):
        final_metadata.append(metadatas[key])
    for i in range(len(final_metadata)):
        if type(final_metadata[i]) is not list:
            final_metadata[i] = [json.dumps(final_metadata[i])]
        else:
            final_metadata[i] = [json.dumps(x) for x in final_metadata[i]]
        assert len(final_metadata[i]) == len(generations_list[0]), f'len(final_metadata[i])={len(final_metadata[i])!r}'
    return [metrics, results, final_metadata]

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

def insert_output(self, output_list: list[str], pred_list: list[str]) -> dict:
    return {'question_title': self.question_title, 'question_content': self.question_content, 'question_id': self.question_id, 'contest_id': self.contest_id, 'contest_date': self.contest_date.isoformat(), 'difficulty': self.difficulty, 'output_list': output_list, 'pred_list': pred_list, 'test_id': self.test_id, 'function_name': self.function_name, 'starter_code': self.starter_code}

def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

def add_messages(self, messages: Union[Message, List[Message]]):
    """Add one or multiple messages."""
    if not isinstance(messages, list):
        messages = [messages]
    for msg in messages:
        self.add_message(msg)

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

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def get_timestamp(self):
    """获取当前日期用于文件命名"""
    return datetime.datetime.now().strftime('%Y%m%d')

def save_data(self, data, filename_prefix, description=''):
    """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
    try:
        timestamp = self.get_timestamp()
        filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
        filepath = self.output_dir / filename
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
        else:
            df = pd.DataFrame([data] if isinstance(data, dict) else data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f'✅ {description} 已保存: {filepath}')
        return str(filepath)
    except Exception as e:
        self.logger.error(f'❌ 保存{description}失败: {str(e)}')
        return None

def quick_fetch_catl_data():
    """
    快速抓取宁德时代数据的便捷函数（向后兼容）
    
    Returns:
        dict: 包含所有数据的字典
    """
    return fetch_stock_data('300750')

class StockChartGenerator:
    """股票技术分析图表生成器"""

    def __init__(self, symbol: str, output_dir: str='output'):
        """
        初始化图表生成器
        
        Args:
            symbol (str): 股票代码（如：300750、600519等）
            output_dir (str): 输出目录，默认为"output"
        """
        self.symbol = symbol
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stock_data = None
        self.processed_data = None

    def generate_mock_data(self) -> pd.DataFrame:
        """生成模拟股票数据用于演示"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        dates = [d for d in dates if d.weekday() < 5]
        np.random.seed(42)
        base_price = 1500 if self.symbol == '600519' else 100
        prices = []
        current_price = base_price
        for i in range(len(dates)):
            change = np.random.normal(0, 0.02)
            current_price = current_price * (1 + change)
            prices.append(current_price)
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            volatility = close * 0.03
            high = close + np.random.uniform(0, volatility)
            low = close - np.random.uniform(0, volatility)
            open_price = prices[i - 1] if i > 0 else close
            volume = np.random.randint(100000, 1000000)
            data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(close, 2), 'volume': volume})
        df = pd.DataFrame(data)
        print(f'生成了 {len(df)} 条模拟数据')
        return df

    def get_stock_data(self) -> pd.DataFrame:
        """获取股票数据"""
        if self.stock_data is not None:
            return self.stock_data
        try:
            import akshare as ak
            print(f'获取股票 {self.symbol} 的数据...')
            try:
                df = ak.stock_zh_a_hist(symbol=self.symbol, period='daily', adjust='qfq')
            except:
                try:
                    formatted_symbol = f'sh{self.symbol}' if self.symbol.startswith('6') else f'sz{self.symbol}'
                    df = ak.stock_zh_a_hist(symbol=formatted_symbol, period='daily', adjust='qfq')
                except:
                    print('获取真实数据失败，使用模拟数据...')
                    return self.generate_mock_data()
            if df.empty:
                return self.generate_mock_data()
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
            print(f'成功获取 {len(df)} 条真实数据')
            self.stock_data = df.tail(250)
            return self.stock_data
        except Exception as e:
            print(f'获取数据失败，使用模拟数据: {e}')
            return self.generate_mock_data()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = df.copy()
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - 100 / (1 + rs)
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + bb_std * 2
        df['BB_lower'] = df['BB_middle'] - bb_std * 2
        df = df.fillna(method='ffill').fillna(method='bfill')
        self.processed_data = df
        return df

    def create_technical_chart(self) -> Optional[str]:
        """创建技术分析图表"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig, axes = plt.subplots(4, 1, figsize=(15, 20))
            fig.suptitle(f'{self.symbol} 技术分析图表', fontsize=16, fontweight='bold')
            ax1 = axes[0]
            ax1.plot(df['date'], df['close'], label='收盘价', linewidth=2, color='blue')
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange')
            ax1.plot(df['date'], df['MA10'], label='MA10', alpha=0.8, color='green')
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='red')
            ax1.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.1, color='gray', label='布林带')
            ax1.plot(df['date'], df['BB_upper'], alpha=0.5, color='gray', linestyle='--')
            ax1.plot(df['date'], df['BB_lower'], alpha=0.5, color='gray', linestyle='--')
            ax1.set_title('价格走势与技术指标')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax2 = axes[1]
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
            ax3 = axes[2]
            ax3.plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
            ax3.fill_between(df['date'], 30, 70, alpha=0.1, color='yellow', label='正常区间')
            ax3.set_title('RSI指标')
            ax3.set_ylabel('RSI')
            ax3.set_ylim(0, 100)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax4 = axes[3]
            ax4.plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=2)
            ax4.plot(df['date'], df['MACD_signal'], label='信号线', color='red', linewidth=2)
            colors = ['red' if x > 0 else 'green' for x in df['MACD_histogram']]
            ax4.bar(df['date'], df['MACD_histogram'], color=colors, alpha=0.6, label='MACD柱状图')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax4.set_title('MACD指标')
            ax4.set_ylabel('MACD')
            ax4.set_xlabel('日期')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_technical_charts.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 技术分析图表已保存: {chart_path}')
            return str(chart_path)
        except ImportError:
            print('⚠️ matplotlib未安装，跳过图表生成')
            return None
        except Exception as e:
            print(f'❌ 生成技术分析图表失败: {e}')
            return None

    def create_candlestick_chart(self) -> Optional[str]:
        """创建K线图（蜡烛图）"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.patches import Rectangle
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').tail(60)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
            fig.suptitle(f'{self.symbol} K线图分析', fontsize=16, fontweight='bold')
            for i, row in df.iterrows():
                date = row['date']
                open_price = row['open']
                high_price = row['high']
                low_price = row['low']
                close_price = row['close']
                color = 'red' if close_price >= open_price else 'green'
                ax1.plot([date, date], [low_price, high_price], color='black', linewidth=1)
                body_height = abs(close_price - open_price)
                body_bottom = min(open_price, close_price)
                rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom), 0.6, body_height, facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
                ax1.add_patch(rect)
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange', linewidth=1.5)
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='blue', linewidth=1.5)
            ax1.set_title('K线图与移动平均线')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7, width=0.8)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.set_xlabel('日期')
            ax2.grid(True, alpha=0.3)
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_candlestick_chart.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 K线图已保存: {chart_path}')
            return str(chart_path)
        except Exception as e:
            print(f'❌ 生成K线图失败: {e}')
            return None

    def generate_all_charts(self) -> Dict[str, Optional[str]]:
        """生成所有类型的图表"""
        print(f'🚀 生成股票 {self.symbol} 的技术分析图表')
        print('=' * 60)
        print(f'📊 开始分析股票: {self.symbol}')
        print('🔄 获取股票数据...')
        df = self.get_stock_data()
        if df is None:
            print('❌ 无法获取数据')
            return {}
        print('🔢 计算技术指标...')
        self.calculate_indicators(df)
        chart_paths = {}
        print('📊 生成技术分析图表...')
        technical_path = self.create_technical_chart()
        if technical_path:
            chart_paths['technical'] = technical_path
        print('🕯️ 生成K线图...')
        candlestick_path = self.create_candlestick_chart()
        if candlestick_path:
            chart_paths['candlestick'] = candlestick_path
        if chart_paths:
            print(f'✅ 图表生成成功:')
            for chart_type, path in chart_paths.items():
                print(f'   {chart_type}: {os.path.abspath(path)}')
        else:
            print('❌ 图表生成失败')
        return chart_paths

def generate_mock_data(self) -> pd.DataFrame:
    """生成模拟股票数据用于演示"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
    dates = [d for d in dates if d.weekday() < 5]
    np.random.seed(42)
    base_price = 1500 if self.symbol == '600519' else 100
    prices = []
    current_price = base_price
    for i in range(len(dates)):
        change = np.random.normal(0, 0.02)
        current_price = current_price * (1 + change)
        prices.append(current_price)
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        volatility = close * 0.03
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = prices[i - 1] if i > 0 else close
        volume = np.random.randint(100000, 1000000)
        data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(close, 2), 'volume': volume})
    df = pd.DataFrame(data)
    print(f'生成了 {len(df)} 条模拟数据')
    return df

def batch_generate_charts(symbols: List[str], output_base_dir: str='charts') -> Dict[str, Dict]:
    """
    批量生成多个股票的图表
    
    Args:
        symbols (List[str]): 股票代码列表
        output_base_dir (str): 基础输出目录
        
    Returns:
        Dict[str, Dict]: 每个股票的生成结果
        
    Example:
        symbols = ["300750", "600519", "000001"]
        results = batch_generate_charts(symbols)
    """
    results = {}
    print(f'🚀 批量生成 {len(symbols)} 个股票的图表')
    print('=' * 60)
    for i, symbol in enumerate(symbols, 1):
        print(f'\n📈 [{i}/{len(symbols)}] 处理股票: {symbol}')
        print('-' * 40)
        try:
            stock_output_dir = os.path.join(output_base_dir, f'stock_{symbol}')
            chart_paths = generate_stock_charts(symbol=symbol, output_dir=stock_output_dir, chart_types=['technical', 'candlestick'])
            results[symbol] = {'status': 'success', 'charts': chart_paths, 'output_dir': stock_output_dir}
        except Exception as e:
            print(f'❌ 生成失败: {e}')
            results[symbol] = {'status': 'failed', 'error': str(e), 'charts': {}, 'output_dir': None}
    print('\n' + '=' * 60)
    print('📋 批量生成结果汇总')
    print('=' * 60)
    success_count = 0
    for symbol, result in results.items():
        if result['status'] == 'success':
            success_count += 1
            print(f'✅ {symbol}: 成功生成 {len(result['charts'])} 个图表')
        else:
            print(f'❌ {symbol}: {result.get('error', '未知错误')}')
    print(f'\n🎉 批量生成完成: {success_count}/{len(symbols)} 成功')
    return results

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

def generate_html_from_existing_files(stock_code, timestamp=None):
    """Generate HTML report from existing markdown and chart files"""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d')
    base_dir, data_dir, report_dir, graphs_dir = get_directories(stock_code, timestamp)
    print(f'🔍 查找现有文件:')
    print(f'   报告目录: {report_dir}')
    print(f'   图表目录: {graphs_dir}')
    if not report_dir.exists():
        print(f'❌ 报告目录不存在: {report_dir}')
        return False
    if not graphs_dir.exists():
        print(f'⚠️  图表目录不存在: {graphs_dir}')
        graphs_dir = None
    return generate_html_report(stock_code, base_dir, report_dir, graphs_dir, timestamp)

def main():
    if len(sys.argv) < 2:
        stock_code = input('请输入股票代码 (如300750): ').strip()
    else:
        stock_code = sys.argv[1].strip()
    if not stock_code.isdigit():
        print('❌ 股票代码应为数字！')
        return
    timestamp = datetime.now().strftime('%Y%m%d')
    base_dir, data_dir, report_dir, graphs_dir = get_directories(stock_code, timestamp)
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    graphs_dir.mkdir(parents=True, exist_ok=True)
    if not check_data_exists(data_dir):
        print(f'\n[1] 拉取数据到: {data_dir}')
        fetch_stock_data(stock_code, output_dir=str(data_dir))
    else:
        print(f'\n[1] 跳过数据拉取 (数据已存在)')
    if not check_charts_exist(graphs_dir, stock_code):
        print(f'[2] 生成图表到: {graphs_dir}')
        generate_stock_charts(stock_code, output_dir=str(graphs_dir))
    else:
        print(f'[2] 跳过图表生成 (图表已存在)')
    print(f'[3] 生成报告到: {report_dir}')
    execute_workflow(stock_code, data_dir, report_dir, timestamp)
    print(f'\n[4] 生成HTML报告')
    html_success = generate_html_report(stock_code, base_dir, report_dir, graphs_dir, timestamp)
    if html_success:
        print('\n✅ 全部流程完成！包括HTML报告生成')
    else:
        print('\n✅ 主要流程完成！(HTML报告生成失败)')

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

class AddMemories(Action):

    def __init__(self, name: str='AddMemories', description: str='Add multiple messages to long-term memory', prompt: str='Add the following messages to memory: {messages}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or AddMemoriesInput
        outputs_format = outputs_format or AddMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> AddMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
        messages = [Message(content=msg.get('content', ''), action=msg.get('action'), wf_goal=msg.get('wf_goal'), timestamp=msg.get('timestamp', datetime.now().isoformat()), agent=msg.get('agent', 'user'), msg_type=msg.get('msg_type', MessageType.REQUEST), prompt=msg.get('prompt'), next_actions=msg.get('next_actions'), wf_task=msg.get('wf_task'), wf_task_desc=msg.get('wf_task_desc'), message_id=msg.get('message_id')) for msg in action_input_data['messages']]
        memory_ids = memory.add(messages)
        output = AddMemoriesOutput(memory_ids=memory_ids)
        if return_prompt:
            prompt = self.prompt.format(messages=[msg.model_dump() for msg in messages])
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> AddMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
    messages = [Message(content=msg.get('content', ''), action=msg.get('action'), wf_goal=msg.get('wf_goal'), timestamp=msg.get('timestamp', datetime.now().isoformat()), agent=msg.get('agent', 'user'), msg_type=msg.get('msg_type', MessageType.REQUEST), prompt=msg.get('prompt'), next_actions=msg.get('next_actions'), wf_task=msg.get('wf_task'), wf_task_desc=msg.get('wf_task_desc'), message_id=msg.get('message_id')) for msg in action_input_data['messages']]
    memory_ids = memory.add(messages)
    output = AddMemoriesOutput(memory_ids=memory_ids)
    if return_prompt:
        prompt = self.prompt.format(messages=[msg.model_dump() for msg in messages])
        return (output, prompt)
    return output

class UpdateMemories(Action):

    def __init__(self, name: str='UpdateMemories', description: str='Update multiple memories by IDs', prompt: str='Update the memories with the following data: {updates}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or UpdateMemoriesInput
        outputs_format = outputs_format or UpdateMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> UpdateMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
        updates = [(update['memory_id'], Message(content=update.get('content', ''), action=update.get('action'), wf_goal=update.get('wf_goal'), timestamp=update.get('timestamp', datetime.now().isoformat()), agent=update.get('agent', 'user'), msg_type=update.get('msg_type', MessageType.REQUEST), prompt=update.get('prompt'), next_actions=update.get('next_actions'), wf_task=update.get('wf_task'), wf_task_desc=update.get('wf_task_desc'), message_id=update.get('message_id'))) for update in action_input_data['updates']]
        successes = memory.update(updates)
        output = UpdateMemoriesOutput(successes=successes)
        if return_prompt:
            prompt = self.prompt.format(updates=[{'memory_id': mid, 'message': msg.model_dump()} for mid, msg in updates])
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> UpdateMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
    updates = [(update['memory_id'], Message(content=update.get('content', ''), action=update.get('action'), wf_goal=update.get('wf_goal'), timestamp=update.get('timestamp', datetime.now().isoformat()), agent=update.get('agent', 'user'), msg_type=update.get('msg_type', MessageType.REQUEST), prompt=update.get('prompt'), next_actions=update.get('next_actions'), wf_task=update.get('wf_task'), wf_task_desc=update.get('wf_task_desc'), message_id=update.get('message_id'))) for update in action_input_data['updates']]
    successes = memory.update(updates)
    output = UpdateMemoriesOutput(successes=successes)
    if return_prompt:
        prompt = self.prompt.format(updates=[{'memory_id': mid, 'message': msg.model_dump()} for mid, msg in updates])
        return (output, prompt)
    return output

class AddMemories(Action):

    def __init__(self, name: str='AddMemories', description: str='Add multiple messages to long-term memory', prompt: str='Add the following messages to memory: {messages}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or AddMemoriesInput
        outputs_format = outputs_format or AddMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> AddMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
        messages = [Message(content=msg.get('content', ''), action=msg.get('action'), wf_goal=msg.get('wf_goal'), timestamp=msg.get('timestamp', datetime.now().isoformat()), agent=msg.get('agent', 'user'), msg_type=msg.get('msg_type', MessageType.REQUEST), prompt=msg.get('prompt'), next_actions=msg.get('next_actions'), wf_task=msg.get('wf_task'), wf_task_desc=msg.get('wf_task_desc'), message_id=msg.get('message_id')) for msg in action_input_data['messages']]
        memory_ids = memory.add(messages)
        output = AddMemoriesOutput(memory_ids=memory_ids)
        if return_prompt:
            prompt = self.prompt.format(messages=[msg.model_dump() for msg in messages])
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> AddMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
    messages = [Message(content=msg.get('content', ''), action=msg.get('action'), wf_goal=msg.get('wf_goal'), timestamp=msg.get('timestamp', datetime.now().isoformat()), agent=msg.get('agent', 'user'), msg_type=msg.get('msg_type', MessageType.REQUEST), prompt=msg.get('prompt'), next_actions=msg.get('next_actions'), wf_task=msg.get('wf_task'), wf_task_desc=msg.get('wf_task_desc'), message_id=msg.get('message_id')) for msg in action_input_data['messages']]
    memory_ids = memory.add(messages)
    output = AddMemoriesOutput(memory_ids=memory_ids)
    if return_prompt:
        prompt = self.prompt.format(messages=[msg.model_dump() for msg in messages])
        return (output, prompt)
    return output

class UpdateMemories(Action):

    def __init__(self, name: str='UpdateMemories', description: str='Update multiple memories by IDs', prompt: str='Update the memories with the following data: {updates}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or UpdateMemoriesInput
        outputs_format = outputs_format or UpdateMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> UpdateMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
        updates = [(update['memory_id'], Message(content=update.get('content', ''), action=update.get('action'), wf_goal=update.get('wf_goal'), timestamp=update.get('timestamp', datetime.now().isoformat()), agent=update.get('agent', 'user'), msg_type=update.get('msg_type', MessageType.REQUEST), prompt=update.get('prompt'), next_actions=update.get('next_actions'), wf_task=update.get('wf_task'), wf_task_desc=update.get('wf_task_desc'), message_id=update.get('message_id'))) for update in action_input_data['updates']]
        successes = memory.update(updates)
        output = UpdateMemoriesOutput(successes=successes)
        if return_prompt:
            prompt = self.prompt.format(updates=[{'memory_id': mid, 'message': msg.model_dump()} for mid, msg in updates])
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> UpdateMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
    updates = [(update['memory_id'], Message(content=update.get('content', ''), action=update.get('action'), wf_goal=update.get('wf_goal'), timestamp=update.get('timestamp', datetime.now().isoformat()), agent=update.get('agent', 'user'), msg_type=update.get('msg_type', MessageType.REQUEST), prompt=update.get('prompt'), next_actions=update.get('next_actions'), wf_task=update.get('wf_task'), wf_task_desc=update.get('wf_task_desc'), message_id=update.get('message_id'))) for update in action_input_data['updates']]
    successes = memory.update(updates)
    output = UpdateMemoriesOutput(successes=successes)
    if return_prompt:
        prompt = self.prompt.format(updates=[{'memory_id': mid, 'message': msg.model_dump()} for mid, msg in updates])
        return (output, prompt)
    return output

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def get_timestamp(self):
    """获取当前日期用于文件命名"""
    return datetime.datetime.now().strftime('%Y%m%d')

def save_data(self, data, filename_prefix, description=''):
    """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
    try:
        timestamp = self.get_timestamp()
        filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
        filepath = self.output_dir / filename
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
        else:
            df = pd.DataFrame([data] if isinstance(data, dict) else data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f'✅ {description} 已保存: {filepath}')
        return str(filepath)
    except Exception as e:
        self.logger.error(f'❌ 保存{description}失败: {str(e)}')
        return None

def quick_fetch_catl_data():
    """
    快速抓取宁德时代数据的便捷函数（向后兼容）
    
    Returns:
        dict: 包含所有数据的字典
    """
    return fetch_stock_data('300750')

class StockChartGenerator:
    """股票技术分析图表生成器"""

    def __init__(self, symbol: str, output_dir: str='output'):
        """
        初始化图表生成器
        
        Args:
            symbol (str): 股票代码（如：300750、600519等）
            output_dir (str): 输出目录，默认为"output"
        """
        self.symbol = symbol
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stock_data = None
        self.processed_data = None

    def generate_mock_data(self) -> pd.DataFrame:
        """生成模拟股票数据用于演示"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        dates = [d for d in dates if d.weekday() < 5]
        np.random.seed(42)
        base_price = 1500 if self.symbol == '600519' else 100
        prices = []
        current_price = base_price
        for i in range(len(dates)):
            change = np.random.normal(0, 0.02)
            current_price = current_price * (1 + change)
            prices.append(current_price)
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            volatility = close * 0.03
            high = close + np.random.uniform(0, volatility)
            low = close - np.random.uniform(0, volatility)
            open_price = prices[i - 1] if i > 0 else close
            volume = np.random.randint(100000, 1000000)
            data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(close, 2), 'volume': volume})
        df = pd.DataFrame(data)
        print(f'生成了 {len(df)} 条模拟数据')
        return df

    def get_stock_data(self) -> pd.DataFrame:
        """获取股票数据"""
        if self.stock_data is not None:
            return self.stock_data
        try:
            import akshare as ak
            print(f'获取股票 {self.symbol} 的数据...')
            try:
                df = ak.stock_zh_a_hist(symbol=self.symbol, period='daily', adjust='qfq')
            except:
                try:
                    formatted_symbol = f'sh{self.symbol}' if self.symbol.startswith('6') else f'sz{self.symbol}'
                    df = ak.stock_zh_a_hist(symbol=formatted_symbol, period='daily', adjust='qfq')
                except:
                    print('获取真实数据失败，使用模拟数据...')
                    return self.generate_mock_data()
            if df.empty:
                return self.generate_mock_data()
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
            print(f'成功获取 {len(df)} 条真实数据')
            self.stock_data = df.tail(250)
            return self.stock_data
        except Exception as e:
            print(f'获取数据失败，使用模拟数据: {e}')
            return self.generate_mock_data()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = df.copy()
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - 100 / (1 + rs)
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + bb_std * 2
        df['BB_lower'] = df['BB_middle'] - bb_std * 2
        df = df.fillna(method='ffill').fillna(method='bfill')
        self.processed_data = df
        return df

    def create_technical_chart(self) -> Optional[str]:
        """创建技术分析图表"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig, axes = plt.subplots(4, 1, figsize=(15, 20))
            fig.suptitle(f'{self.symbol} 技术分析图表', fontsize=16, fontweight='bold')
            ax1 = axes[0]
            ax1.plot(df['date'], df['close'], label='收盘价', linewidth=2, color='blue')
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange')
            ax1.plot(df['date'], df['MA10'], label='MA10', alpha=0.8, color='green')
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='red')
            ax1.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.1, color='gray', label='布林带')
            ax1.plot(df['date'], df['BB_upper'], alpha=0.5, color='gray', linestyle='--')
            ax1.plot(df['date'], df['BB_lower'], alpha=0.5, color='gray', linestyle='--')
            ax1.set_title('价格走势与技术指标')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax2 = axes[1]
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
            ax3 = axes[2]
            ax3.plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
            ax3.fill_between(df['date'], 30, 70, alpha=0.1, color='yellow', label='正常区间')
            ax3.set_title('RSI指标')
            ax3.set_ylabel('RSI')
            ax3.set_ylim(0, 100)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax4 = axes[3]
            ax4.plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=2)
            ax4.plot(df['date'], df['MACD_signal'], label='信号线', color='red', linewidth=2)
            colors = ['red' if x > 0 else 'green' for x in df['MACD_histogram']]
            ax4.bar(df['date'], df['MACD_histogram'], color=colors, alpha=0.6, label='MACD柱状图')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax4.set_title('MACD指标')
            ax4.set_ylabel('MACD')
            ax4.set_xlabel('日期')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_technical_charts.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 技术分析图表已保存: {chart_path}')
            return str(chart_path)
        except ImportError:
            print('⚠️ matplotlib未安装，跳过图表生成')
            return None
        except Exception as e:
            print(f'❌ 生成技术分析图表失败: {e}')
            return None

    def create_candlestick_chart(self) -> Optional[str]:
        """创建K线图（蜡烛图）"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.patches import Rectangle
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').tail(60)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
            fig.suptitle(f'{self.symbol} K线图分析', fontsize=16, fontweight='bold')
            for i, row in df.iterrows():
                date = row['date']
                open_price = row['open']
                high_price = row['high']
                low_price = row['low']
                close_price = row['close']
                color = 'red' if close_price >= open_price else 'green'
                ax1.plot([date, date], [low_price, high_price], color='black', linewidth=1)
                body_height = abs(close_price - open_price)
                body_bottom = min(open_price, close_price)
                rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom), 0.6, body_height, facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
                ax1.add_patch(rect)
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange', linewidth=1.5)
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='blue', linewidth=1.5)
            ax1.set_title('K线图与移动平均线')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7, width=0.8)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.set_xlabel('日期')
            ax2.grid(True, alpha=0.3)
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_candlestick_chart.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 K线图已保存: {chart_path}')
            return str(chart_path)
        except Exception as e:
            print(f'❌ 生成K线图失败: {e}')
            return None

    def generate_all_charts(self) -> Dict[str, Optional[str]]:
        """生成所有类型的图表"""
        print(f'🚀 生成股票 {self.symbol} 的技术分析图表')
        print('=' * 60)
        print(f'📊 开始分析股票: {self.symbol}')
        print('🔄 获取股票数据...')
        df = self.get_stock_data()
        if df is None:
            print('❌ 无法获取数据')
            return {}
        print('🔢 计算技术指标...')
        self.calculate_indicators(df)
        chart_paths = {}
        print('📊 生成技术分析图表...')
        technical_path = self.create_technical_chart()
        if technical_path:
            chart_paths['technical'] = technical_path
        print('🕯️ 生成K线图...')
        candlestick_path = self.create_candlestick_chart()
        if candlestick_path:
            chart_paths['candlestick'] = candlestick_path
        if chart_paths:
            print(f'✅ 图表生成成功:')
            for chart_type, path in chart_paths.items():
                print(f'   {chart_type}: {os.path.abspath(path)}')
        else:
            print('❌ 图表生成失败')
        return chart_paths

def generate_mock_data(self) -> pd.DataFrame:
    """生成模拟股票数据用于演示"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
    dates = [d for d in dates if d.weekday() < 5]
    np.random.seed(42)
    base_price = 1500 if self.symbol == '600519' else 100
    prices = []
    current_price = base_price
    for i in range(len(dates)):
        change = np.random.normal(0, 0.02)
        current_price = current_price * (1 + change)
        prices.append(current_price)
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        volatility = close * 0.03
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = prices[i - 1] if i > 0 else close
        volume = np.random.randint(100000, 1000000)
        data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(close, 2), 'volume': volume})
    df = pd.DataFrame(data)
    print(f'生成了 {len(df)} 条模拟数据')
    return df

def batch_generate_charts(symbols: List[str], output_base_dir: str='charts') -> Dict[str, Dict]:
    """
    批量生成多个股票的图表
    
    Args:
        symbols (List[str]): 股票代码列表
        output_base_dir (str): 基础输出目录
        
    Returns:
        Dict[str, Dict]: 每个股票的生成结果
        
    Example:
        symbols = ["300750", "600519", "000001"]
        results = batch_generate_charts(symbols)
    """
    results = {}
    print(f'🚀 批量生成 {len(symbols)} 个股票的图表')
    print('=' * 60)
    for i, symbol in enumerate(symbols, 1):
        print(f'\n📈 [{i}/{len(symbols)}] 处理股票: {symbol}')
        print('-' * 40)
        try:
            stock_output_dir = os.path.join(output_base_dir, f'stock_{symbol}')
            chart_paths = generate_stock_charts(symbol=symbol, output_dir=stock_output_dir, chart_types=['technical', 'candlestick'])
            results[symbol] = {'status': 'success', 'charts': chart_paths, 'output_dir': stock_output_dir}
        except Exception as e:
            print(f'❌ 生成失败: {e}')
            results[symbol] = {'status': 'failed', 'error': str(e), 'charts': {}, 'output_dir': None}
    print('\n' + '=' * 60)
    print('📋 批量生成结果汇总')
    print('=' * 60)
    success_count = 0
    for symbol, result in results.items():
        if result['status'] == 'success':
            success_count += 1
            print(f'✅ {symbol}: 成功生成 {len(result['charts'])} 个图表')
        else:
            print(f'❌ {symbol}: {result.get('error', '未知错误')}')
    print(f'\n🎉 批量生成完成: {success_count}/{len(symbols)} 成功')
    return results

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

def generate_html_from_existing_files(stock_code, timestamp=None):
    """Generate HTML report from existing markdown and chart files"""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d')
    base_dir, data_dir, report_dir, graphs_dir = get_directories(stock_code, timestamp)
    print(f'🔍 查找现有文件:')
    print(f'   报告目录: {report_dir}')
    print(f'   图表目录: {graphs_dir}')
    if not report_dir.exists():
        print(f'❌ 报告目录不存在: {report_dir}')
        return False
    if not graphs_dir.exists():
        print(f'⚠️  图表目录不存在: {graphs_dir}')
        graphs_dir = None
    return generate_html_report(stock_code, base_dir, report_dir, graphs_dir, timestamp)

def main():
    if len(sys.argv) < 2:
        stock_code = input('请输入股票代码 (如300750): ').strip()
    else:
        stock_code = sys.argv[1].strip()
    if not stock_code.isdigit():
        print('❌ 股票代码应为数字！')
        return
    timestamp = datetime.now().strftime('%Y%m%d')
    base_dir, data_dir, report_dir, graphs_dir = get_directories(stock_code, timestamp)
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    graphs_dir.mkdir(parents=True, exist_ok=True)
    if not check_data_exists(data_dir):
        print(f'\n[1] 拉取数据到: {data_dir}')
        fetch_stock_data(stock_code, output_dir=str(data_dir))
    else:
        print(f'\n[1] 跳过数据拉取 (数据已存在)')
    if not check_charts_exist(graphs_dir, stock_code):
        print(f'[2] 生成图表到: {graphs_dir}')
        generate_stock_charts(stock_code, output_dir=str(graphs_dir))
    else:
        print(f'[2] 跳过图表生成 (图表已存在)')
    print(f'[3] 生成报告到: {report_dir}')
    execute_workflow(stock_code, data_dir, report_dir, timestamp)
    print(f'\n[4] 生成HTML报告')
    html_success = generate_html_report(stock_code, base_dir, report_dir, graphs_dir, timestamp)
    if html_success:
        print('\n✅ 全部流程完成！包括HTML报告生成')
    else:
        print('\n✅ 主要流程完成！(HTML报告生成失败)')

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

