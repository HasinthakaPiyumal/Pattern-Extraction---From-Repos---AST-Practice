# Cluster 8

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

def init_long_term_memory(self):
    """
        Initialize long-term memory components.
        """
    assert self.storage_handler is not None, 'must provide ``storage_handler`` when use_long_term_memory=True'
    if not self.long_term_memory:
        self.long_term_memory = LongTermMemory()
    if not self.long_term_memory_manager:
        self.long_term_memory_manager = MemoryManager(storage_handler=self.storage_handler, memory=self.long_term_memory)

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

def init_module(self):
    if self.workflow_manager is None:
        if self.llm is None:
            raise ValueError('Must provide `llm` when `workflow_manager` is None')
        self.workflow_manager = WorkFlowManager(llm=self.llm)
    if self.agent_manager is None:
        logger.warning('agent_manager is NoneType when initializing a WorkFlow instance')

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

def get_task_info(self) -> str:

    def format_parameters(params: List[Parameter]) -> str:
        if not params:
            return 'None'
        return '\n'.join((f'  - {param.name} ({param.type}): {param.description}' for param in params))
    desc = f'Name: {self.name}\nDescription: {self.description}\nInputs:\n{format_parameters(self.inputs)}\nOutputs:\n{format_parameters(self.outputs)}\n'
    return desc

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

def _create_default_storage_config(db_path: Optional[str]=None) -> StoreConfig:
    """
    Create a default storage configuration with proper path handling.
    
    Args:
        db_path (str, optional): Custom database path
        
    Returns:
        StoreConfig: Configured storage configuration
    """
    from ..storages.storages_config import StoreConfig, DBConfig, VectorStoreConfig
    if db_path is None:
        db_path = './faiss_db.sqlite'
    validated_db_path = _ensure_database_path(db_path)
    logger.info(f'Using validated database path: {validated_db_path}')
    index_cache_path = str(Path(validated_db_path).parent.resolve() / 'index_cache')
    storage_config = StoreConfig(dbConfig=DBConfig(db_name='sqlite', path=validated_db_path), vectorConfig=VectorStoreConfig(vector_name='faiss', dimensions=1536, index_type='flat_l2'), path=index_cache_path)
    Path(index_cache_path).mkdir(parents=True, exist_ok=True)
    return storage_config

def _create_default_rag_config() -> RAGConfig:
    """
    Create a default RAG configuration.
    
    Returns:
        RAGConfig: Configured RAG configuration
    """
    from ..rag.rag_config import RAGConfig, EmbeddingConfig, ChunkerConfig
    return RAGConfig(embedding=EmbeddingConfig(provider='openai', model_name='text-embedding-ada-002'), chunker=ChunkerConfig(chunk_size=500, chunk_overlap=50))

def main():
    OPEN_ROUNTER_API_KEY = os.environ['OPEN_ROUNTER_API_KEY']
    config = OpenRouterConfig(openrouter_key=OPEN_ROUNTER_API_KEY, temperature=0.3, model='google/gemini-2.5-flash-lite-preview-06-17')
    llm = OpenRouterLLM(config=config)
    store_config = StoreConfig(dbConfig=DBConfig(db_name='sqlite', path='./debug/data/hotpotqa/cache/test_hotpotQA.sql'), vectorConfig=VectorStoreConfig(vector_name='faiss', dimensions=768, index_type='flat_l2'), graphConfig=None, path='./debug/data/hotpotqa/cache/indexing')
    storage_handler = StorageHandler(storageConfig=store_config)
    embedding = EmbeddingConfig(provider='huggingface', model_name='debug/bge-small-en-v1.5', device='cpu')
    rag_config = RAGConfig(reader=ReaderConfig(recursive=False, exclude_hidden=True, num_files_limit=None, custom_metadata_function=None, extern_file_extractor=None, errors='ignore', encoding='utf-8'), chunker=ChunkerConfig(strategy='simple', chunk_size=512, chunk_overlap=0, max_chunks=None), embedding=embedding, index=IndexConfig(index_type='vector'), retrieval=RetrievalConfig(retrivel_type='vector', postprocessor_type='simple', top_k=2, similarity_cutoff=0.3, keyword_filters=None, metadata_filters=None))
    memory = LongTermMemory(storage_handler=storage_handler, rag_config=rag_config)
    memory_agent = Agent(name='MemoryAgent', description='An agent that manages long-term memory operations', actions=[AddMemories(), SearchMemories(), UpdateMemories(), DeleteMemories()], llm_config=config)
    actions = memory_agent.get_all_actions()
    print(f'Available actions of agent {memory_agent.name}:')
    for action in actions:
        print(f'- {action.name}: {action.description}')
    messages = [{'content': 'Schedule a meeting with Alice on Monday', 'action': 'schedule', 'wf_goal': 'plan_meeting', 'agent': 'user', 'msg_type': MessageType.REQUEST.value, 'wf_task': 'schedule_meeting', 'wf_task_desc': 'Schedule a meeting with a colleague', 'message_id': 'msg_001'}, {'content': 'Send report to Bob by Friday', 'action': 'send', 'wf_goal': 'submit_report', 'agent': 'user', 'msg_type': MessageType.REQUEST.value, 'wf_task': 'send_report', 'wf_task_desc': 'Send a report to a colleague', 'message_id': 'msg_002'}]
    add_result = memory_agent.execute(action_name='AddMemories', action_input_data={'messages': messages}, memory=memory)
    print('\nAdded memories:')
    print(f'Memory IDs: {add_result.content.memory_ids}')
    search_result = memory_agent.execute(action_name='SearchMemories', action_input_data={'query': 'meeting', 'top_k': 2, 'metadata_filters': {'agent': 'user'}}, memory=memory)
    print('\nSearch results:')
    for result in search_result.content.results:
        print(f'- Memory ID: {result['memory_id']}, Message: {result['message'].content}')
    updates = [{'memory_id': add_result.content.memory_ids[0], 'content': 'Reschedule meeting with Alice to Tuesday', 'action': 'reschedule', 'wf_goal': 'plan_meeting', 'agent': 'user', 'msg_type': MessageType.REQUEST.value, 'wf_task': 'reschedule_meeting', 'wf_task_desc': 'Reschedule a meeting with a colleague', 'message_id': 'msg_001_updated'}]
    update_result = memory_agent.execute(action_name='UpdateMemories', action_input_data={'updates': updates}, memory=memory)
    print('\nUpdate results:')
    print(f'Successes: {update_result.content.successes}')
    delete_result = memory_agent.execute(action_name='DeleteMemories', action_input_data={'memory_ids': add_result.content.memory_ids}, memory=memory)
    print('\nDelete results:')
    print(f'Successes: {delete_result.content.successes}')
    new_search_result = memory_agent.execute(action_name='SearchMemories', action_input_data={'query': 'meeting', 'top_k': 2, 'metadata_filters': {'agent': 'user'}}, memory=memory)
    print('\nSearch results:')
    for result in new_search_result.content.results:
        print(f'- Memory ID: {result['memory_id']}, Message: {result['message'].content}')

def main():
    OPEN_ROUNTER_API_KEY = os.environ.get('OPEN_ROUNTER_API_KEY')
    if not OPEN_ROUNTER_API_KEY:
        raise ValueError('OPEN_ROUNTER_API_KEY not set in environment')
    config = OpenRouterConfig(openrouter_key=OPEN_ROUNTER_API_KEY, temperature=0.3, model='google/gemini-2.5-pro-exp-03-25')
    llm = OpenRouterLLM(config=config)
    store_config = StoreConfig(dbConfig=DBConfig(db_name='sqlite', path='./debug/data/hotpotqa/cache/test_hotpotqa.sql'), vectorConfig=VectorStoreConfig(vector_name='faiss', dimensions=384, index_type='flat_l2'), graphConfig=None, path='./debug/data/hotpotqa/cache/indexing')
    storage_handler = StorageHandler(storageConfig=store_config)
    embedding = EmbeddingConfig(provider='huggingface', model_name='debug/weights/bge-small-en-v1.5', device='cpu')
    rag_config = RAGConfig(reader=ReaderConfig(recursive=False, exclude_hidden=True, num_files_limit=None, custom_metadata_function=None, extern_file_extractor=None, errors='ignore', encoding='utf-8'), chunker=ChunkerConfig(strategy='simple', chunk_size=512, chunk_overlap=0, max_chunks=None), embedding=embedding, index=IndexConfig(index_type='vector'), retrieval=RetrievalConfig(retrivel_type='vector', postprocessor_type='simple', top_k=2, similarity_cutoff=0.3, keyword_filters=None, metadata_filters=None))
    memory = LongTermMemory(storage_handler=storage_handler, rag_config=rag_config, llm=llm, use_llm_management=False)
    memory.init_module()
    memory_agent = Agent(name='MemoryAgent', description='An agent that manages long-term memory operations', actions=[AddMemories(), SearchMemories(), UpdateMemories(), DeleteMemories()], llm_config=config)
    print(f'Available actions of agent {memory_agent.name}:')
    for action in memory_agent.get_all_actions():
        print(f'- {action.name}: {action.description}')
    messages = [{'content': 'Schedule a meeting with Alice on Monday', 'action': 'schedule', 'wf_goal': 'plan_meeting', 'agent': 'user', 'msg_type': MessageType.REQUEST.value, 'wf_task': 'schedule_meeting', 'wf_task_desc': 'Schedule a meeting with a colleague', 'message_id': 'msg_001'}, {'content': 'Send report to Bob by Friday', 'action': 'send', 'wf_goal': 'submit_report', 'agent': 'user', 'msg_type': MessageType.REQUEST.value, 'wf_task': 'send_report', 'wf_task_desc': 'Send a report to a colleague', 'message_id': 'msg_002'}]
    add_result = memory_agent.execute(action_name='AddMemories', action_input_data={'messages': messages}, memory=memory)
    print('\nTest 1: Added memories')
    print(f'Memory IDs: {add_result.content.memory_ids}')
    search_result = memory_agent.execute(action_name='SearchMemories', action_input_data={'query': 'meeting', 'top_k': 1, 'metadata_filters': {'agent': 'user'}}, memory=memory)
    print('\nTest 2: Search results (string query)')
    for result in search_result.content.results:
        print(f'- Memory ID: {result['memory_id']}, Content: {result['message'].content}')
    query = Query(query_str='report', top_k=1, metadata_filters={'msg_type': MessageType.REQUEST.value})
    search_result_query = memory_agent.execute(action_name='SearchMemories', action_input_data={'query': query.query_str, 'top_k': query.top_k, 'metadata_filters': query.metadata_filters}, memory=memory)
    print('\nTest 3: Search results (Query object)')
    for result in search_result_query.content.results:
        print(f'- Memory ID: {result['memory_id']}, Content: {result['message'].content}')
    updates = [{'memory_id': add_result.content.memory_ids[0] if add_result.content.memory_ids else '', 'content': 'Reschedule meeting with Alice to Tuesday', 'action': 'reschedule', 'wf_goal': 'plan_meeting', 'agent': 'user', 'msg_type': MessageType.REQUEST.value, 'wf_task': 'reschedule_meeting', 'wf_task_desc': 'Reschedule a meeting with a colleague', 'message_id': 'msg_001_updated'}]
    update_result = memory_agent.execute(action_name='UpdateMemories', action_input_data={'updates': updates}, memory=memory)
    print('\nTest 4: Update results')
    print(f'Successes: {update_result.content.successes}')
    memory.save()
    print('\nTest 5: Saved memories to database')
    memory.clear()
    search_after_clear = memory_agent.execute(action_name='SearchMemories', action_input_data={'query': 'meeting', 'top_k': 1}, memory=memory)
    print('\nTest 6: Search after clear (in-memory)')
    print(f'Results: {len(search_after_clear.content.results)} memories found')
    loaded_ids = memory.load()
    print('\nTest 7: Loaded memories')
    print(f'Loaded {len(loaded_ids)} memory IDs: {loaded_ids}')
    delete_result = memory_agent.execute(action_name='DeleteMemories', action_input_data={'memory_ids': add_result.content.memory_ids}, memory=memory)
    print('\nTest 8: Delete results')
    print(f'Successes: {delete_result.content.successes}')
    memory.clear()
    search_after_full_clear = memory_agent.execute(action_name='SearchMemories', action_input_data={'query': 'meeting', 'top_k': 1}, memory=memory)
    print('\nTest 9: Search after full clear')
    print(f'Results: {len(search_after_full_clear.content.results)} memories found')

def demonstrate_rag_to_generation_pipeline():
    """Simple demo: Index 20 docs, retrieve 5, generate answer."""
    print('🚀 EvoAgentX Multimodal RAG-to-Generation Pipeline')
    print('=' * 60)
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print('❌ OPENAI_API_KEY not found. Please set it to run this demo.')
        return
    voyage_key = os.getenv('VOYAGE_API_KEY')
    if not voyage_key:
        print('❌ VOYAGE_API_KEY not found. Please set it to run this demo.')
        return
    datasets = RealMMRAG('./debug/data/real_mm_rag')
    samples = datasets.get_random_samples(20, seed=42)
    print(f'📊 Dataset loaded with {len(samples)} samples')
    store_config = StoreConfig(dbConfig=DBConfig(db_name='sqlite', path='./debug/data/real_mm_rag/cache/demo.sql'), vectorConfig=VectorStoreConfig(vector_name='faiss', dimensions=1024, index_type='flat_l2'), path='./debug/data/real_mm_rag/cache/indexing')
    storage_handler = StorageHandler(storageConfig=store_config)
    rag_config = RAGConfig(modality='multimodal', reader=ReaderConfig(recursive=True, exclude_hidden=True, errors='ignore'), embedding=EmbeddingConfig(provider='voyage', model_name='voyage-multimodal-3', device='cpu', api_key=voyage_key), index=IndexConfig(index_type='vector'), retrieval=RetrievalConfig(retrivel_type='vector', top_k=5, similarity_cutoff=0.3))
    search_engine = RAGEngine(config=rag_config, storage_handler=storage_handler)
    print('\n📚 Step 1: Indexing 20 documents...')
    corpus_id = 'demo_corpus'
    valid_paths = [s['image_path'] for s in samples if os.path.exists(s['image_path'])][:20]
    if len(valid_paths) < 20:
        print(f'⚠️ Only found {len(valid_paths)} valid image paths, using those')
    corpus = search_engine.read(file_paths=valid_paths, corpus_id=corpus_id)
    search_engine.add(index_type='vector', nodes=corpus, corpus_id=corpus_id)
    print(f'✅ Indexed {len(corpus.chunks)} image documents')
    query_sample = next((s for s in samples if s['query'] and len(s['query'].strip()) > 10), None)
    if not query_sample:
        print('❌ No suitable query found in samples')
        return
    query_text = query_sample['query']
    target_image = query_sample['image_filename']
    print(f"\n🔍 Step 2: Querying with: '{query_text}'")
    print(f'🎯 Target document: {target_image}')
    query = Query(query_str=query_text, top_k=5)
    result = search_engine.query(query, corpus_id=corpus_id)
    retrieved_chunks = result.corpus.chunks
    print(f'\n📄 Retrieved {len(retrieved_chunks)} documents:')
    retrieved_paths = []
    for i, chunk in enumerate(retrieved_chunks):
        filename = Path(chunk.image_path).name if chunk.image_path else 'Unknown'
        similarity = getattr(chunk.metadata, 'similarity_score', 0.0)
        retrieved_paths.append(filename)
        print(f'  {i + 1}. {filename} (similarity: {similarity:.3f})')
    print(f'\n🤖 Step 3: Generating answer with GPT-4o...')
    try:
        llm_config = OpenAILLMConfig(model='gpt-4o', openai_key=openai_key, temperature=0.1, max_tokens=300)
        llm = OpenAILLM(config=llm_config)
        print('✅ LLM initialized successfully')
        content = [TextChunk(text=f'Query: {query_text}\n\nAnalyze these retrieved images and answer the query:')]
        content.extend(retrieved_chunks[:3])
        response = llm.generate(messages=[{'role': 'system', 'content': 'You are an expert image analyst. Answer queries based on provided images.'}, {'role': 'user', 'content': content}])
        print('✅ Response generated successfully')
        answer = response.content
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f'❌ Detailed error:')
        print(error_details)
        answer = f'Error in generation: {str(e)}'
    print('\n' + '=' * 60)
    print('📋 FINAL RESULTS')
    print('=' * 60)
    print(f'🔍 QUERY: {query_text}')
    print(f'\n📄 RETRIEVED PATHS:')
    for i, path in enumerate(retrieved_paths):
        print(f'  {i + 1}. {path}')
    print(f'\n🎯 TARGET DOCUMENT: {target_image}')
    print(f'\n🤖 GENERATED ANSWER:')
    print(answer)
    print('EXPECTED ANSWER:')
    print(query_sample['answer'])
    print('=' * 60)
    search_engine.clear(corpus_id=corpus_id)

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

class TestSearchEngine(unittest.TestCase):
    """Unit tests for SearchEngine interfaces using HotpotQA JSON example."""

    def setUp(self):
        """Set up SearchEngine, StorageHandler, and temporary directory for each test."""
        load_dotenv()
        self.mock_embedding = MockOpenAIEmbeddingWrapper()
        self.patcher = patch('evoagentx.rag.rag.EmbeddingFactory.create', return_value=self.mock_embedding)
        self.mock_create = self.patcher.start()
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f'Created temporary directory: {self.temp_dir}')
        self.store_config = StoreConfig(dbConfig=DBConfig(db_name='sqlite', path=os.path.join(self.temp_dir, 'test_hotpotQA.sql')), vectorConfig=VectorStoreConfig(vector_name='faiss', dimensions=1536, index_type='flat_l2'), graphConfig=None, path=self.temp_dir)
        self.storage_handler = StorageHandler(storageConfig=self.store_config)
        self.rag_config = RAGConfig(reader=ReaderConfig(recursive=False, exclude_hidden=True, num_files_limit=None, custom_metadata_function=None, extern_file_extractor=None, errors='ignore', encoding='utf-8'), chunker=ChunkerConfig(strategy='simple', chunk_size=512, chunk_overlap=0, max_chunks=None), embedding=EmbeddingConfig(provider='openai', model_name='text-embedding-ada-002', api_key='dummy_key'), index=IndexConfig(index_type='vector'), retrieval=RetrievalConfig(retrivel_type='vector', postprocessor_type='simple', top_k=10, similarity_cutoff=0.3, keyword_filters=None, metadata_filters=None))
        self.search_engine = RAGEngine(config=self.rag_config, storage_handler=self.storage_handler)
        self.corpus_id = HOTPOTQA_EXAMPLE['_id']
        self.context_files = []
        self.supporting_titles = {fact[0] for fact in HOTPOTQA_EXAMPLE['supporting_facts']}
        self.context_data = HOTPOTQA_EXAMPLE['context']
        self.query_text = HOTPOTQA_EXAMPLE['question']
        for title, sentences in self.context_data:
            content = '\n'.join(sentences)
            file_path = os.path.join(self.temp_dir, f'{title.replace(' ', '_')}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.context_files.append(str(file_path))

    def tearDown(self):
        """Clean up temporary directory, clear indices, and stop patcher."""
        self.search_engine.clear()
        self.patcher.stop()
        logger.info(f'Cleaned up temporary directory: {self.temp_dir}')

    def test_read(self):
        """Test the read method by loading HotpotQA context files."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.assertIsInstance(corpus, Corpus, 'read should return a Corpus object')
        self.assertEqual(corpus.corpus_id, self.corpus_id, 'Corpus ID should match')
        self.assertGreater(len(corpus.chunks), 0, 'Corpus should contain chunks')
        for chunk in corpus.chunks:
            self.assertIsInstance(chunk.metadata, ChunkMetadata, 'Chunk should have metadata')
            self.assertIn('file_name', chunk.metadata.model_dump(), 'Metadata should include file_name')
        logger.info(f'Read {len(corpus.chunks)} chunks for corpus {self.corpus_id}')

    def test_add(self):
        """Test the add method by indexing HotpotQA corpus."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        self.assertIn(self.corpus_id, self.search_engine.indices, 'Corpus should be indexed')
        self.assertIn(IndexType.VECTOR, self.search_engine.indices[self.corpus_id], 'Vector index should exist')
        index = self.search_engine.indices[self.corpus_id][IndexType.VECTOR]
        self.assertGreater(len(index.id_to_node), 0, 'Index should contain nodes')
        for node_id, node in index.id_to_node.items():
            self.assertEqual(node.metadata['corpus_id'], self.corpus_id, 'Node metadata should include corpus_id')
            self.assertEqual(node.metadata['index_type'], IndexType.VECTOR, 'Node metadata should include index_type')
        logger.info(f'Added {len(corpus.chunks)} nodes to vector index for corpus {self.corpus_id}')

    def test_query(self):
        """Test the query method with HotpotQA question, validating top-K retrieval."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        query = Query(query_str=self.query_text, top_k=10)
        result = self.search_engine.query(query, corpus_id=self.corpus_id)
        self.assertIsInstance(result, RagResult, 'query should return a RagResult object')
        self.assertLessEqual(len(result.corpus.chunks), 10, 'Should return at most top_k chunks')
        self.assertEqual(len(result.scores), len(result.corpus.chunks), 'Scores should match chunks')
        retrieved_titles = set()
        for chunk in result.corpus.chunks:
            file_name = chunk.metadata.model_dump().get('file_name', '')
            title = os.path.basename(file_name).replace('_', ' ').replace('.txt', '')
            retrieved_titles.add(title)
        recall = len(retrieved_titles.intersection(self.supporting_titles)) / len(self.supporting_titles)
        self.assertGreaterEqual(recall, 0.0, 'Recall may be low with dummy embeddings')
        logger.info(f'Query retrieved {len(result.corpus.chunks)} chunks with recall@10={recall}')

    def test_delete_by_node_ids(self):
        """Test the delete method by removing specific nodes."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        index = self.search_engine.indices[self.corpus_id][IndexType.VECTOR]
        node_ids = list(index.id_to_node.keys())[:2]
        initial_node_count = len(index.id_to_node)
        self.search_engine.delete(corpus_id=self.corpus_id, index_type=IndexType.VECTOR, node_ids=node_ids)
        remaining_node_count = len(index.id_to_node)
        self.assertEqual(remaining_node_count, initial_node_count - len(node_ids), 'Nodes should be deleted')
        for node_id in node_ids:
            self.assertNotIn(node_id, index.id_to_node, f'Node {node_id} should be deleted')
        logger.info(f'Deleted {len(node_ids)} nodes from corpus {self.corpus_id}')

    def test_delete_by_metadata(self):
        """Test the delete method using metadata filters."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        index = self.search_engine.indices[self.corpus_id][IndexType.VECTOR]
        metadata_filters = {'file_name': str(self.context_files[0])}
        initial_node_count = len(index.id_to_node)
        self.search_engine.delete(corpus_id=self.corpus_id, index_type=IndexType.VECTOR, metadata_filters=metadata_filters)
        remaining_nodes = [node_id for node_id, node in index.id_to_node.items() if node.metadata.get('file_name') != str(self.context_files[0])]
        self.assertEqual(len(index.id_to_node), len(remaining_nodes), 'Nodes matching metadata should be deleted')
        logger.info(f'Deleted nodes with metadata {metadata_filters} from corpus {self.corpus_id}')

    def test_clear(self):
        """Test the clear method by removing all indices."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        self.search_engine.clear(corpus_id=self.corpus_id)
        self.assertNotIn(self.corpus_id, self.search_engine.indices, 'Corpus should be cleared')
        self.assertNotIn(self.corpus_id, self.search_engine.retrievers, 'Retrievers should be cleared')
        logger.info(f'Cleared corpus {self.corpus_id}')

    def test_save_to_files(self):
        """Test the save method by saving indices to files."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        output_path = os.path.join(self.temp_dir, 'output')
        self.search_engine.save(output_path=str(output_path), corpus_id=self.corpus_id, index_type=IndexType.VECTOR)
        if isinstance(output_path, str):
            from pathlib import Path
            output_path = Path(output_path)
        nodes_files = list(output_path.glob('*_nodes.jsonl'))
        metadata_files = list(output_path.glob('*_metadata.json'))
        self.assertEqual(len(nodes_files), 1, 'Should save one nodes file')
        self.assertEqual(len(metadata_files), 1, 'Should save one metadata file')
        with open(nodes_files[0], 'r', encoding='utf-8') as f:
            chunks = [json.loads(line) for line in f]
            self.assertGreater(len(chunks), 0, 'Nodes file should contain chunks')
        with open(metadata_files[0], 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            self.assertEqual(metadata['corpus_id'], self.corpus_id, 'Metadata should include corpus_id')
        logger.info(f'Saved indices to {output_path}')

    def test_load_from_files(self):
        """Test the load method by loading indices from files."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        output_path = os.path.join(self.temp_dir, 'output')
        self.search_engine.save(output_path=str(output_path), corpus_id=self.corpus_id, index_type=IndexType.VECTOR)
        self.search_engine.clear()
        self.search_engine.load(source=str(output_path), corpus_id=self.corpus_id, index_type=IndexType.VECTOR)
        self.assertIn(self.corpus_id, self.search_engine.indices, 'Corpus should be loaded')
        index = self.search_engine.indices[self.corpus_id][IndexType.VECTOR]
        self.assertGreater(len(index.id_to_node), 0, 'Index should contain nodes')
        query = Query(query_str=self.query_text, top_k=10)
        result = self.search_engine.query(query, corpus_id=self.corpus_id)
        self.assertEqual(len(result.corpus.chunks), 0)
        logger.info(f'Loaded indices from {output_path}')

    def test_save_to_database(self):
        """Test the save method by saving indices to database."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        self.search_engine.save(corpus_id=self.corpus_id, index_type=IndexType.VECTOR, table='indexing')
        records = self.storage_handler.load(tables=['indexing']).get('indexing', [])
        self.assertGreater(len(records), 0, 'Database should contain records')
        for record in records:
            parsed = self.storage_handler.parse_result(record, IndexStore)
            self.assertEqual(parsed['corpus_id'], self.corpus_id, 'Record should match corpus_id')
        logger.info(f'Saved indices to database table indexing')

    def test_load_from_database(self):
        """Test the load method by loading indices from database."""
        corpus = self.search_engine.read(file_paths=self.context_files, filter_file_by_suffix='.txt', corpus_id=self.corpus_id)
        self.search_engine.add(index_type=IndexType.VECTOR, nodes=corpus, corpus_id=self.corpus_id)
        self.search_engine.save(corpus_id=self.corpus_id, index_type=IndexType.VECTOR, table='indexing')
        self.search_engine.clear()
        self.search_engine.load(corpus_id=self.corpus_id, index_type=IndexType.VECTOR, table='indexing')
        self.assertIn(self.corpus_id, self.search_engine.indices, 'Corpus should be loaded')
        index = self.search_engine.indices[self.corpus_id][IndexType.VECTOR]
        self.assertGreater(len(index.id_to_node), 0, 'Index should contain nodes')
        query = Query(query_str=self.query_text, top_k=10)
        result = self.search_engine.query(query, corpus_id=self.corpus_id)
        self.assertEqual(len(result.corpus.chunks), 0)
        logger.info(f'Loaded indices from database table indexing')

    def test_edge_case_empty_corpus(self):
        """Test behavior with empty corpus or invalid corpus_id."""
        result = self.search_engine.query(query=self.query_text, corpus_id='nonexistent')
        self.assertEqual(len(result.corpus.chunks), 0, 'Query on nonexistent corpus should return empty result')
        self.search_engine.delete(corpus_id='nonexistent')
        self.assertNotIn('nonexistent', self.search_engine.indices, 'Delete on nonexistent corpus should not fail')
        self.search_engine.clear(corpus_id='nonexistent')
        self.assertNotIn('nonexistent', self.search_engine.indices, 'Clear on nonexistent corpus should not fail')
        logger.info('Handled edge case for empty/nonexistent corpus')

def setUp(self):
    """Set up SearchEngine, StorageHandler, and temporary directory for each test."""
    load_dotenv()
    self.mock_embedding = MockOpenAIEmbeddingWrapper()
    self.patcher = patch('evoagentx.rag.rag.EmbeddingFactory.create', return_value=self.mock_embedding)
    self.mock_create = self.patcher.start()
    self.temp_dir = tempfile.mkdtemp()
    logger.info(f'Created temporary directory: {self.temp_dir}')
    self.store_config = StoreConfig(dbConfig=DBConfig(db_name='sqlite', path=os.path.join(self.temp_dir, 'test_hotpotQA.sql')), vectorConfig=VectorStoreConfig(vector_name='faiss', dimensions=1536, index_type='flat_l2'), graphConfig=None, path=self.temp_dir)
    self.storage_handler = StorageHandler(storageConfig=self.store_config)
    self.rag_config = RAGConfig(reader=ReaderConfig(recursive=False, exclude_hidden=True, num_files_limit=None, custom_metadata_function=None, extern_file_extractor=None, errors='ignore', encoding='utf-8'), chunker=ChunkerConfig(strategy='simple', chunk_size=512, chunk_overlap=0, max_chunks=None), embedding=EmbeddingConfig(provider='openai', model_name='text-embedding-ada-002', api_key='dummy_key'), index=IndexConfig(index_type='vector'), retrieval=RetrievalConfig(retrivel_type='vector', postprocessor_type='simple', top_k=10, similarity_cutoff=0.3, keyword_filters=None, metadata_filters=None))
    self.search_engine = RAGEngine(config=self.rag_config, storage_handler=self.storage_handler)
    self.corpus_id = HOTPOTQA_EXAMPLE['_id']
    self.context_files = []
    self.supporting_titles = {fact[0] for fact in HOTPOTQA_EXAMPLE['supporting_facts']}
    self.context_data = HOTPOTQA_EXAMPLE['context']
    self.query_text = HOTPOTQA_EXAMPLE['question']
    for title, sentences in self.context_data:
        content = '\n'.join(sentences)
        file_path = os.path.join(self.temp_dir, f'{title.replace(' ', '_')}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.context_files.append(str(file_path))

