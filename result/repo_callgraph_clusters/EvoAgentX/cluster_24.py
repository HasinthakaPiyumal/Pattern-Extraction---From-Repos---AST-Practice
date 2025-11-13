# Cluster 24

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

@wraps(original_execute)
def patched_execute(*args, **kwargs):
    result = original_execute(*args, **kwargs)
    return check_method_return('execute', result)

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

def wrapped_func(*args, **kwargs):
    if self.on_execute:
        self.on_execute(func, *args, **kwargs)
    return func(*args, **kwargs)

@wraps(func)
def wrapper(self, *args, **kwargs):
    context = getattr(self, '_lock', nullcontext())
    with context:
        return func(self, *args, **kwargs)

@wraps(func)
def wrapper(*args, **kwargs):
    return func(*args, **kwargs)

