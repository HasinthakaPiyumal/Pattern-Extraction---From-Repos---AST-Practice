# Cluster 11

@dataclass
class AgentConfig:
    """Configuration for MassGen agents using the proven binary decision framework.

    This configuration implements the simplified approach from input_cases_reference.md
    that eliminates perfectionism loops through clear binary decisions.

    Args:
        backend_params: Settings passed directly to LLM backend (includes tool enablement)
        message_templates: Custom message templates (None=default)
        agent_id: Optional agent identifier for this configuration
        custom_system_instruction: Additional system instruction prepended to evaluation message
        timeout_config: Timeout and resource limit configuration
        coordination_config: Coordination behavior configuration (e.g., planning mode)
        skip_coordination_rounds: Debug/test mode - skip voting rounds and go straight to final presentation (default: False)
    """
    backend_params: Dict[str, Any] = field(default_factory=dict)
    message_templates: Optional['MessageTemplates'] = None
    agent_id: Optional[str] = None
    _custom_system_instruction: Optional[str] = field(default=None, init=False)
    timeout_config: TimeoutConfig = field(default_factory=TimeoutConfig)
    coordination_config: CoordinationConfig = field(default_factory=CoordinationConfig)
    skip_coordination_rounds: bool = False

    @property
    def custom_system_instruction(self) -> Optional[str]:
        """
        DEPRECATED: Use backend-specific system prompt parameters instead.

        For Claude Code: use append_system_prompt or system_prompt in backend_params
        For other backends: use their respective system prompt parameters
        """
        if self._custom_system_instruction is not None:
            warnings.warn('custom_system_instruction is deprecated. Use backend-specific system prompt parameters instead (e.g., append_system_prompt for Claude Code)', DeprecationWarning, stacklevel=2)
        return self._custom_system_instruction

    @custom_system_instruction.setter
    def custom_system_instruction(self, value: Optional[str]) -> None:
        if value is not None:
            warnings.warn('custom_system_instruction is deprecated. Use backend-specific system prompt parameters instead (e.g., append_system_prompt for Claude Code)', DeprecationWarning, stacklevel=2)
        self._custom_system_instruction = value

    @classmethod
    def create_chatcompletion_config(cls, model: str='gpt-oss-120b', enable_web_search: bool=False, enable_code_interpreter: bool=False, **kwargs) -> 'AgentConfig':
        """Create ChatCompletion configuration following proven patterns.

        Args:
            model: Opensource Model Name
            enable_web_search: Enable web search via Responses API
            enable_code_interpreter: Enable code execution for computational tasks
            **kwargs: Additional backend parameters

        Examples:
            # Basic configuration
            config = AgentConfig.create_chatcompletion_config("gpt-oss-120b")

            # Research task with web search
            config = AgentConfig.create_chatcompletion_config("gpt-oss-120b", enable_web_search=True)

            # Computational task with code execution
            config = AgentConfig.create_chatcompletion_config("gpt-oss-120b", enable_code_interpreter=True)
        """
        backend_params = {'model': model, **kwargs}
        if enable_web_search:
            backend_params['enable_web_search'] = True
        if enable_code_interpreter:
            backend_params['enable_code_interpreter'] = True
        return cls(backend_params=backend_params)

    @classmethod
    def create_openai_config(cls, model: str='gpt-4o-mini', enable_web_search: bool=False, enable_code_interpreter: bool=False, **kwargs) -> 'AgentConfig':
        """Create OpenAI configuration following proven patterns.

        Args:
            model: OpenAI model name
            enable_web_search: Enable web search via Responses API
            enable_code_interpreter: Enable code execution for computational tasks
            **kwargs: Additional backend parameters

        Examples:
            # Basic configuration
            config = AgentConfig.create_openai_config("gpt-4o-mini")

            # Research task with web search
            config = AgentConfig.create_openai_config("gpt-4o", enable_web_search=True)

            # Computational task with code execution
            config = AgentConfig.create_openai_config("gpt-4o", enable_code_interpreter=True)
        """
        backend_params = {'model': model, **kwargs}
        if enable_web_search:
            backend_params['enable_web_search'] = True
        if enable_code_interpreter:
            backend_params['enable_code_interpreter'] = True
        return cls(backend_params=backend_params)

    @classmethod
    def create_claude_config(cls, model: str='claude-3-sonnet-20240229', enable_web_search: bool=False, enable_code_execution: bool=False, **kwargs) -> 'AgentConfig':
        """Create Anthropic Claude configuration.

        Args:
            model: Claude model name
            enable_web_search: Enable builtin web search tool
            enable_code_execution: Enable builtin code execution tool
            **kwargs: Additional backend parameters
        """
        backend_params = {'model': model, **kwargs}
        if enable_web_search:
            backend_params['enable_web_search'] = True
        if enable_code_execution:
            backend_params['enable_code_execution'] = True
        return cls(backend_params=backend_params)

    @classmethod
    def create_grok_config(cls, model: str='grok-2-1212', enable_web_search: bool=False, **kwargs) -> 'AgentConfig':
        """Create xAI Grok configuration.

        Args:
            model: Grok model name
            enable_web_search: Enable Live Search feature
            **kwargs: Additional backend parameters
        """
        backend_params = {'model': model, **kwargs}
        if enable_web_search:
            backend_params['enable_web_search'] = True
        return cls(backend_params=backend_params)

    @classmethod
    def create_lmstudio_config(cls, model: str='gpt-4o-mini', enable_web_search: bool=False, **kwargs) -> 'AgentConfig':
        """Create LM Studio configuration (OpenAI-compatible local server).

        Args:
            model: Local model name exposed by LM Studio
            enable_web_search: No builtin web search; kept for interface parity
            **kwargs: Additional backend parameters (e.g., base_url, api_key)
        """
        backend_params = {'model': model, **kwargs}
        if enable_web_search:
            backend_params['enable_web_search'] = True
        return cls(backend_params=backend_params)

    @classmethod
    def create_vllm_config(cls, model: str | None=None, **kwargs) -> 'AgentConfig':
        """Create vLLM configuration (OpenAI-compatible local server)."""
        backend_params = {'model': model, **kwargs}
        if model is None:
            raise ValueError('Model is required for vLLM configuration')
        return cls(backend_params=backend_params)

    @classmethod
    def create_sglang_config(cls, model: str | None=None, **kwargs) -> 'AgentConfig':
        """Create SGLang configuration (OpenAI-compatible local server)."""
        backend_params = {'model': model, **kwargs}
        if model is None:
            raise ValueError('Model is required for SGLang configuration')
        return cls(backend_params=backend_params)

    @classmethod
    def create_gemini_config(cls, model: str='gemini-2.5-flash', enable_web_search: bool=False, enable_code_execution: bool=False, **kwargs) -> 'AgentConfig':
        """Create Google Gemini configuration.

        Args:
            model: Gemini model name
            enable_web_search: Enable Google Search retrieval tool
            enable_code_execution: Enable code execution tool
            **kwargs: Additional backend parameters
        """
        backend_params = {'model': model, **kwargs}
        if enable_web_search:
            backend_params['enable_web_search'] = True
        if enable_code_execution:
            backend_params['enable_code_execution'] = True
        return cls(backend_params=backend_params)

    @classmethod
    def create_zai_config(cls, model: str='glm-4.5', base_url: str='https://api.z.ai/api/paas/v4/', **kwargs) -> 'AgentConfig':
        """Create ZAI configuration (OpenAI Chat Completions compatible).

        Args:
            model: ZAI model name (e.g., "glm-4.5")
            base_url: ZAI OpenAI-compatible API base URL
            **kwargs: Additional backend parameters (e.g., temperature, top_p)
        """
        backend_params = {'model': model, 'base_url': base_url, **kwargs}
        return cls(backend_params=backend_params)

    @classmethod
    def create_azure_openai_config(cls, deployment_name: str='gpt-4', endpoint: Optional[str]=None, api_key: Optional[str]=None, api_version: str='2024-02-15-preview', **kwargs) -> 'AgentConfig':
        """Create Azure OpenAI configuration.

        Args:
            deployment_name: Azure OpenAI deployment name (e.g., "gpt-4", "gpt-35-turbo")
            endpoint: Azure OpenAI endpoint URL (optional, uses AZURE_OPENAI_ENDPOINT env var)
            api_key: Azure OpenAI API key (optional, uses AZURE_OPENAI_API_KEY env var)
            api_version: Azure OpenAI API version (default: 2024-02-15-preview)
            **kwargs: Additional backend parameters (e.g., temperature, max_tokens)

        Examples:
            Basic configuration using environment variables::

                config = AgentConfig.create_azure_openai_config("gpt-4")

            Custom endpoint and API key::

                config = AgentConfig.create_azure_openai_config(
                    deployment_name="gpt-4-turbo",
                    endpoint="https://your-resource.openai.azure.com/",
                    api_key="your-api-key"
                )
        """
        backend_params = {'type': 'azure_openai', 'model': deployment_name, 'api_version': api_version, **kwargs}
        if endpoint:
            backend_params['base_url'] = endpoint
        if api_key:
            backend_params['api_key'] = api_key
        return cls(backend_params=backend_params)

    @classmethod
    def create_claude_code_config(cls, model: str='claude-sonnet-4-20250514', system_prompt: Optional[str]=None, allowed_tools: Optional[list]=None, disallowed_tools: Optional[list]=None, max_thinking_tokens: int=8000, cwd: Optional[str]=None, **kwargs) -> 'AgentConfig':
        """Create Claude Code Stream configuration using claude-code-sdk.

        This backend provides native integration with ALL Claude Code built-in tools
        by default, with security enforced through disallowed_tools. This gives maximum
        power while maintaining safety.

        Args:
            model: Claude model name (default: claude-sonnet-4-20250514)
            system_prompt: Custom system prompt for the agent
            allowed_tools: [LEGACY] List of allowed tools (use disallowed_tools instead)
            disallowed_tools: List of dangerous operations to block
                            (default: ["Bash(rm*)", "Bash(sudo*)", "Bash(su*)", "Bash(chmod*)", "Bash(chown*)"])
            max_thinking_tokens: Maximum tokens for internal thinking (default: 8000)
            cwd: Current working directory for file operations
            **kwargs: Additional backend parameters

        Examples:
            Maximum power configuration (recommended)::

                config = AgentConfig.create_claude_code_config()

            Custom security restrictions::

                config = AgentConfig.create_claude_code_config(
                    disallowed_tools=["Bash(rm*)", "Bash(sudo*)", "WebSearch"]
                )

            Development task with custom directory::

                config = AgentConfig.create_claude_code_config(
                    cwd="/path/to/project",
                    system_prompt="You are an expert developer assistant."
                )

            Legacy allowed_tools approach (not recommended)::

                config = AgentConfig.create_claude_code_config(
                    allowed_tools=["Read", "Write", "Edit", "Bash"]
                )
        """
        backend_params = {'model': model, **kwargs}
        if system_prompt:
            backend_params['system_prompt'] = system_prompt
        if allowed_tools:
            backend_params['allowed_tools'] = allowed_tools
        if disallowed_tools:
            backend_params['disallowed_tools'] = disallowed_tools
        if max_thinking_tokens != 8000:
            backend_params['max_thinking_tokens'] = max_thinking_tokens
        if cwd:
            backend_params['cwd'] = cwd
        return cls(backend_params=backend_params)

    def with_custom_instruction(self, instruction: str) -> 'AgentConfig':
        """Create a copy with custom system instruction."""
        import copy
        new_config = copy.deepcopy(self)
        new_config.custom_system_instruction = instruction
        return new_config

    def with_agent_id(self, agent_id: str) -> 'AgentConfig':
        """Create a copy with specified agent ID."""
        import copy
        new_config = copy.deepcopy(self)
        new_config.agent_id = agent_id
        return new_config

    @classmethod
    def for_research_task(cls, model: str='gpt-4o', backend: str='openai') -> 'AgentConfig':
        """Create configuration optimized for research tasks.

        Based on econometrics test success patterns:
        - Enables web search for literature review
        - Uses proven model defaults
        """
        if backend == 'openai':
            return cls.create_openai_config(model, enable_web_search=True)
        elif backend == 'grok':
            return cls.create_grok_config(model, enable_web_search=True)
        elif backend == 'claude':
            return cls.create_claude_config(model, enable_web_search=True)
        elif backend == 'gemini':
            return cls.create_gemini_config(model, enable_web_search=True)
        elif backend == 'claude_code':
            return cls.create_claude_code_config(model)
        else:
            raise ValueError(f'Research configuration not available for backend: {backend}')

    @classmethod
    def for_computational_task(cls, model: str='gpt-4o', backend: str='openai') -> 'AgentConfig':
        """Create configuration optimized for computational tasks.

        Based on Tower of Hanoi test success patterns:
        - Enables code execution for calculations
        - Uses proven model defaults
        """
        if backend == 'openai':
            return cls.create_openai_config(model, enable_code_interpreter=True)
        elif backend == 'claude':
            return cls.create_claude_config(model, enable_code_execution=True)
        elif backend == 'gemini':
            return cls.create_gemini_config(model, enable_code_execution=True)
        elif backend == 'claude_code':
            return cls.create_claude_code_config(model)
        else:
            raise ValueError(f'Computational configuration not available for backend: {backend}')

    @classmethod
    def for_analytical_task(cls, model: str='gpt-4o-mini', backend: str='openai') -> 'AgentConfig':
        """Create configuration optimized for analytical tasks.

        Based on general reasoning test patterns:
        - No special tools needed
        - Uses efficient model defaults
        """
        if backend == 'openai':
            return cls.create_openai_config(model)
        elif backend == 'claude':
            return cls.create_claude_config(model)
        elif backend == 'grok':
            return cls.create_grok_config(model)
        elif backend == 'gemini':
            return cls.create_gemini_config(model)
        elif backend == 'claude_code':
            return cls.create_claude_code_config(model)
        else:
            raise ValueError(f'Analytical configuration not available for backend: {backend}')

    @classmethod
    def for_expert_domain(cls, domain: str, expertise_level: str='expert', model: str='gpt-4o', backend: str='openai') -> 'AgentConfig':
        """Create configuration for domain expertise.

        Args:
            domain: Domain of expertise (e.g., "econometrics", "computer science")
            expertise_level: Level of expertise ("expert", "specialist", "researcher")
            model: Model to use
            backend: Backend provider
        """
        instruction = f'You are a {expertise_level} in {domain}. Apply your deep domain knowledge and methodological expertise when evaluating answers and providing solutions.'
        if backend == 'openai':
            config = cls.create_openai_config(model, enable_web_search=True)
        elif backend == 'grok':
            config = cls.create_grok_config(model, enable_web_search=True)
        elif backend == 'gemini':
            config = cls.create_gemini_config(model, enable_web_search=True)
        else:
            raise ValueError(f'Domain expert configuration not available for backend: {backend}')
        config.custom_system_instruction = instruction
        return config

    def build_conversation(self, task: str, agent_summaries: Optional[Dict[str, str]]=None, session_id: Optional[str]=None) -> Dict[str, Any]:
        """Build conversation using the proven MassGen approach.

        Returns complete conversation configuration ready for backend.
        Automatically determines Case 1 vs Case 2 based on agent_summaries.
        """
        from .message_templates import get_templates
        templates = self.message_templates or get_templates()
        valid_agent_ids = list(agent_summaries.keys()) if agent_summaries else None
        conversation = templates.build_initial_conversation(task=task, agent_summaries=agent_summaries, valid_agent_ids=valid_agent_ids)
        if self.custom_system_instruction:
            base_system = conversation['system_message']
            conversation['system_message'] = f'{self.custom_system_instruction}\n\n{base_system}'
        conversation.update({'backend_params': self.get_backend_params(), 'session_id': session_id, 'agent_id': self.agent_id})
        return conversation

    def add_enforcement_message(self, conversation_messages: list) -> list:
        """Add enforcement message to conversation (Case 3 handling).

        Args:
            conversation_messages: Existing conversation messages

        Returns:
            Updated conversation messages with enforcement
        """
        from .message_templates import get_templates
        templates = self.message_templates or get_templates()
        return templates.add_enforcement_message(conversation_messages)

    def continue_conversation(self, existing_messages: list, additional_message: Any=None, additional_message_role: str='user', enforce_tools: bool=False) -> Dict[str, Any]:
        """Continue an existing conversation (Cases 3 & 4).

        Args:
            existing_messages: Previous conversation messages
            additional_message: Additional message (str or dict for tool results)
            additional_message_role: Role for additional message ("user", "tool", "assistant")
            enforce_tools: Whether to add tool enforcement message

        Returns:
            Updated conversation configuration
        """
        messages = existing_messages.copy()
        if additional_message is not None:
            if isinstance(additional_message, dict):
                messages.append(additional_message)
            else:
                messages.append({'role': additional_message_role, 'content': str(additional_message)})
        if enforce_tools:
            messages = self.add_enforcement_message(messages)
        from .message_templates import get_templates
        templates = self.message_templates or get_templates()
        return {'messages': messages, 'tools': templates.get_standard_tools(), 'backend_params': self.get_backend_params(), 'session_id': None, 'agent_id': self.agent_id}

    def handle_case3_enforcement(self, existing_messages: list) -> Dict[str, Any]:
        """Handle Case 3: Non-workflow response requiring enforcement.

        Args:
            existing_messages: Messages from agent that didn't use tools

        Returns:
            Conversation with enforcement message added
        """
        return self.continue_conversation(existing_messages=existing_messages, enforce_tools=True)

    def add_tool_result(self, existing_messages: list, tool_call_id: str, result: str) -> Dict[str, Any]:
        """Add tool result to conversation.

        Args:
            existing_messages: Previous conversation messages
            tool_call_id: ID of the tool call this responds to
            result: Tool execution result (success or error)

        Returns:
            Conversation with tool result added
        """
        tool_message = {'role': 'tool', 'tool_call_id': tool_call_id, 'content': result}
        return self.continue_conversation(existing_messages=existing_messages, additional_message=tool_message)

    def handle_case4_error_recovery(self, existing_messages: list, clarification: Optional[str]=None) -> Dict[str, Any]:
        """Handle Case 4: Error recovery after tool failure.

        Args:
            existing_messages: Messages including tool error response
            clarification: Optional clarification message

        Returns:
            Conversation ready for retry
        """
        return self.continue_conversation(existing_messages=existing_messages, additional_message=clarification, additional_message_role='user', enforce_tools=False)

    def get_backend_params(self) -> Dict[str, Any]:
        """Get backend parameters (already includes tool enablement)."""
        return self.backend_params.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {'backend_params': self.backend_params, 'agent_id': self.agent_id, 'custom_system_instruction': self.custom_system_instruction, 'timeout_config': {'orchestrator_timeout_seconds': self.timeout_config.orchestrator_timeout_seconds}}
        result['coordination_config'] = {'enable_planning_mode': self.coordination_config.enable_planning_mode, 'planning_mode_instruction': self.coordination_config.planning_mode_instruction}
        if self.message_templates is not None:
            try:
                if hasattr(self.message_templates, '_template_overrides'):
                    overrides = self.message_templates._template_overrides
                    if all((not callable(v) for v in overrides.values())):
                        result['message_templates'] = overrides
                    else:
                        result['message_templates'] = '<contains_callable_functions>'
                else:
                    result['message_templates'] = '<custom_message_templates>'
            except (AttributeError, TypeError):
                result['message_templates'] = '<non_serializable>'
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary (for deserialization)."""
        backend_params = data.get('backend_params', {})
        agent_id = data.get('agent_id')
        custom_system_instruction = data.get('custom_system_instruction')
        timeout_config = TimeoutConfig()
        timeout_data = data.get('timeout_config', {})
        if timeout_data:
            timeout_config = TimeoutConfig(**timeout_data)
        coordination_config = CoordinationConfig()
        coordination_data = data.get('coordination_config', {})
        if coordination_data:
            coordination_config = CoordinationConfig(**coordination_data)
        message_templates = None
        template_data = data.get('message_templates')
        if isinstance(template_data, dict):
            from .message_templates import MessageTemplates
            message_templates = MessageTemplates(**template_data)
        return cls(backend_params=backend_params, message_templates=message_templates, agent_id=agent_id, custom_system_instruction=custom_system_instruction, timeout_config=timeout_config, coordination_config=coordination_config)

def with_custom_instruction(self, instruction: str) -> 'AgentConfig':
    """Create a copy with custom system instruction."""
    import copy
    new_config = copy.deepcopy(self)
    new_config.custom_system_instruction = instruction
    return new_config

def with_agent_id(self, agent_id: str) -> 'AgentConfig':
    """Create a copy with specified agent ID."""
    import copy
    new_config = copy.deepcopy(self)
    new_config.agent_id = agent_id
    return new_config

def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for serialization."""
    result = {'backend_params': self.backend_params, 'agent_id': self.agent_id, 'custom_system_instruction': self.custom_system_instruction, 'timeout_config': {'orchestrator_timeout_seconds': self.timeout_config.orchestrator_timeout_seconds}}
    result['coordination_config'] = {'enable_planning_mode': self.coordination_config.enable_planning_mode, 'planning_mode_instruction': self.coordination_config.planning_mode_instruction}
    if self.message_templates is not None:
        try:
            if hasattr(self.message_templates, '_template_overrides'):
                overrides = self.message_templates._template_overrides
                if all((not callable(v) for v in overrides.values())):
                    result['message_templates'] = overrides
                else:
                    result['message_templates'] = '<contains_callable_functions>'
            else:
                result['message_templates'] = '<custom_message_templates>'
        except (AttributeError, TypeError):
            result['message_templates'] = '<non_serializable>'
    return result

@dataclass
class AgentAnswer:
    """Represents an answer from an agent."""
    agent_id: str
    content: str
    timestamp: float

    @property
    def label(self) -> str:
        """Auto-generate label based on answer properties."""
        return getattr(self, '_label', 'unknown')

    @label.setter
    def label(self, value: str):
        self._label = value

@label.setter
def label(self, value: str):
    self._label = value

class CoordinationTracker:
    """
    Principled coordination tracking that simply records what happens.

    The orchestrator tells us exactly what occurred and when, without
    us having to infer or manage complex state transitions.
    """

    def __init__(self):
        self.events: List[CoordinationEvent] = []
        self.answers_by_agent: Dict[str, List[AgentAnswer]] = {}
        self.final_answers: Dict[str, AgentAnswer] = {}
        self.votes: List[AgentVote] = []
        self.current_iteration: int = 0
        self.agent_rounds: Dict[str, int] = {}
        self.agent_round_context: Dict[str, Dict[int, List[str]]] = {}
        self.iteration_available_labels: List[str] = []
        self.pending_agent_restarts: Dict[str, bool] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.agent_ids: List[str] = []
        self.final_winner: Optional[str] = None
        self.final_context: Optional[Dict[str, Any]] = None
        self.is_final_round: bool = False
        self.user_prompt: Optional[str] = None
        self.agent_context_labels: Dict[str, List[str]] = {}
        self.snapshot_mappings: Dict[str, Dict[str, Any]] = {}

    def _make_snapshot_path(self, kind: str, agent_id: str, timestamp: str) -> str:
        """Generate standardized snapshot paths.

        Args:
            kind: Type of snapshot ('answer', 'vote', 'final_answer', etc.)
            agent_id: The agent ID
            timestamp: The timestamp or 'final' for final answers

        Returns:
            The formatted path string
        """
        if kind == 'final_answer' and timestamp == 'final':
            return f'final/{agent_id}/answer.txt'
        if kind == 'answer':
            return f'{agent_id}/{timestamp}/answer.txt'
        if kind == 'vote':
            return f'{agent_id}/{timestamp}/vote.json'
        return f'{agent_id}/{timestamp}/{kind}.txt'

    def initialize_session(self, agent_ids: List[str], user_prompt: Optional[str]=None):
        """Initialize a new coordination session."""
        self.start_time = time.time()
        self.agent_ids = agent_ids.copy()
        self.answers_by_agent = {aid: [] for aid in agent_ids}
        self.user_prompt = user_prompt
        self.agent_rounds = {aid: 0 for aid in agent_ids}
        self.agent_round_context = {aid: {0: []} for aid in agent_ids}
        self.pending_agent_restarts = {aid: False for aid in agent_ids}
        self.agent_context_labels = {aid: [] for aid in agent_ids}
        self._add_event(EventType.SESSION_START, None, f'Started with agents: {agent_ids}')

    def get_anonymous_id(self, agent_id: str) -> str:
        """Get anonymous ID (agent1, agent2) for a full agent ID."""
        agent_num = self._get_agent_number(agent_id)
        return f'agent{agent_num}' if agent_num else agent_id

    def _get_agent_number(self, agent_id: str) -> Optional[int]:
        """Get the 1-based number for an agent (1, 2, 3, etc.)."""
        if agent_id in self.agent_ids:
            return self.agent_ids.index(agent_id) + 1
        return None

    def get_agent_context_labels(self, agent_id: str) -> List[str]:
        """Get the answer labels this agent can currently see."""
        return self.agent_context_labels.get(agent_id, []).copy()

    def get_latest_answer_label(self, agent_id: str) -> Optional[str]:
        """Get the latest answer label for an agent."""
        if agent_id in self.answers_by_agent and self.answers_by_agent[agent_id]:
            return self.answers_by_agent[agent_id][-1].label
        return None

    def get_agent_round(self, agent_id: str) -> int:
        """Get the current round for a specific agent."""
        return self.agent_rounds.get(agent_id, 0)

    @property
    def max_round(self) -> int:
        """Get the highest round number across all agents."""
        return max(self.agent_rounds.values()) if self.agent_rounds else 0

    def start_new_iteration(self):
        """Start a new coordination iteration."""
        self.current_iteration += 1
        self.iteration_available_labels = []
        for agent_id, answers_list in self.answers_by_agent.items():
            if answers_list:
                latest_answer = answers_list[-1]
                self.iteration_available_labels.append(latest_answer.label)
        self._add_event(EventType.ITERATION_START, None, f'Starting coordination iteration {self.current_iteration}', {'iteration': self.current_iteration, 'available_answers': self.iteration_available_labels.copy()})

    def end_iteration(self, reason: str, details: Dict[str, Any]=None):
        """Record how an iteration ended."""
        context = {'iteration': self.current_iteration, 'end_reason': reason, 'available_answers': self.iteration_available_labels.copy()}
        if details:
            context.update(details)
        self._add_event(EventType.ITERATION_END, None, f'Iteration {self.current_iteration} ended: {reason}', context)

    def set_user_prompt(self, prompt: str):
        """Set or update the user prompt."""
        self.user_prompt = prompt

    def change_status(self, agent_id: str, new_status: AgentStatus):
        """Record when an agent changes status."""
        self._add_event(EventType.STATUS_CHANGE, agent_id, f'Changed to status: {new_status.value}')

    def track_agent_context(self, agent_id: str, answers: Dict[str, str], conversation_history: Optional[Dict[str, Any]]=None, agent_full_context: Optional[str]=None, snapshot_dir: Optional[str]=None):
        """Record when an agent receives context.

        Args:
            agent_id: The agent receiving context
            answers: Dict of agent_id -> answer content
            conversation_history: Optional conversation history
            agent_full_context: Optional full context string/dict to save
            snapshot_dir: Optional directory path to save context.txt
        """
        answer_labels = []
        for answering_agent_id in answers.keys():
            if answering_agent_id in self.answers_by_agent and self.answers_by_agent[answering_agent_id]:
                latest_answer = self.answers_by_agent[answering_agent_id][-1]
                answer_labels.append(latest_answer.label)
        self.agent_context_labels[agent_id] = answer_labels.copy()
        anon_answering_agents = [self.get_anonymous_id(aid) for aid in answers.keys()]
        context = {'available_answers': anon_answering_agents, 'available_answer_labels': answer_labels.copy(), 'answer_count': len(answers), 'has_conversation_history': bool(conversation_history)}
        self._add_event(EventType.CONTEXT_RECEIVED, agent_id, f'Received context with {len(answers)} answers', context)

    def track_restart_signal(self, triggering_agent: str, agents_restarted: List[str]):
        """Record when a restart is triggered - but don't increment rounds yet."""
        for agent_id in agents_restarted:
            if True:
                self.pending_agent_restarts[agent_id] = True
        context = {'affected_agents': agents_restarted, 'triggering_agent': triggering_agent}
        self._add_event(EventType.RESTART_TRIGGERED, triggering_agent, f'Triggered restart affecting {len(agents_restarted)} agents', context)

    def complete_agent_restart(self, agent_id: str):
        """Record when an agent has completed its restart and increment their round.

        Args:
            agent_id: The agent that completed restart
        """
        if not self.pending_agent_restarts.get(agent_id, False):
            return
        self.pending_agent_restarts[agent_id] = False
        self.agent_rounds[agent_id] += 1
        new_round = self.agent_rounds[agent_id]
        if agent_id not in self.agent_round_context:
            self.agent_round_context[agent_id] = {}
        context = {'agent_round': new_round}
        self._add_event(EventType.RESTART_COMPLETED, agent_id, f'Completed restart - now in round {new_round}', context)

    def add_agent_answer(self, agent_id: str, answer: str, snapshot_timestamp: Optional[str]=None):
        """Record when an agent provides a new answer.

        Args:
            agent_id: ID of the agent
            answer: The answer content
            snapshot_timestamp: Timestamp of the filesystem snapshot (if any)
        """
        agent_answer = AgentAnswer(agent_id=agent_id, content=answer, timestamp=time.time())
        agent_num = self._get_agent_number(agent_id)
        answer_num = len(self.answers_by_agent[agent_id]) + 1
        label = f'agent{agent_num}.{answer_num}'
        agent_answer.label = label
        self.answers_by_agent[agent_id].append(agent_answer)
        if snapshot_timestamp:
            self.snapshot_mappings[label] = {'type': 'answer', 'label': label, 'agent_id': agent_id, 'timestamp': snapshot_timestamp, 'iteration': self.current_iteration, 'round': self.get_agent_round(agent_id), 'path': self._make_snapshot_path('answer', agent_id, snapshot_timestamp)}
        context = {'label': label}
        self._add_event(EventType.NEW_ANSWER, agent_id, f'Provided answer {label}', context)

    def add_agent_vote(self, agent_id: str, vote_data: Dict[str, Any], snapshot_timestamp: Optional[str]=None):
        """Record when an agent votes.

        Args:
            agent_id: ID of the voting agent
            vote_data: Dictionary with vote information
            snapshot_timestamp: Timestamp of the filesystem snapshot (if any)
        """
        voted_for = vote_data.get('voted_for') or vote_data.get('agent_id', 'unknown')
        reason = vote_data.get('reason', '')
        voter_anon_id = self.get_anonymous_id(agent_id)
        voted_for_label = 'unknown'
        if voted_for not in self.agent_ids:
            logger.warning(f'Vote from {agent_id} for unknown agent {voted_for}')
        if voted_for in self.agent_ids:
            voted_agent_answers = self.answers_by_agent.get(voted_for, [])
            if voted_agent_answers:
                voted_for_label = voted_agent_answers[-1].label
        vote = AgentVote(voter_id=agent_id, voted_for=voted_for, voted_for_label=voted_for_label, voter_anon_id=voter_anon_id, reason=reason, timestamp=time.time(), available_answers=self.iteration_available_labels.copy())
        self.votes.append(vote)
        if snapshot_timestamp:
            agent_num = self._get_agent_number(agent_id) or 0
            vote_num = len([v for v in self.votes if v.voter_id == agent_id])
            vote_label = f'agent{agent_num}.vote{vote_num}'
            self.snapshot_mappings[vote_label] = {'type': 'vote', 'label': vote_label, 'agent_id': agent_id, 'timestamp': snapshot_timestamp, 'voted_for': voted_for, 'voted_for_label': voted_for_label, 'iteration': self.current_iteration, 'round': self.get_agent_round(agent_id), 'path': self._make_snapshot_path('vote', agent_id, snapshot_timestamp)}
        context = {'voted_for': voted_for, 'voted_for_label': voted_for_label, 'reason': reason, 'available_answers': self.iteration_available_labels.copy()}
        self._add_event(EventType.VOTE_CAST, agent_id, f'Voted for {voted_for_label}', context)

    def set_final_agent(self, agent_id: str, vote_summary: str, all_answers: Dict[str, str]):
        """Record when final agent is selected."""
        self.final_winner = agent_id
        answer_labels = []
        answers_with_labels = {}
        for aid, answer_content in all_answers.items():
            if aid in self.answers_by_agent and self.answers_by_agent[aid]:
                if self.answers_by_agent[aid]:
                    latest_answer = self.answers_by_agent[aid][-1]
                    answer_labels.append(latest_answer.label)
                    answers_with_labels[latest_answer.label] = answer_content
        self.final_context = {'vote_summary': vote_summary, 'all_answers': answer_labels, 'answers_for_context': answers_with_labels}
        self._add_event(EventType.FINAL_AGENT_SELECTED, agent_id, 'Selected as final presenter', self.final_context)

    def set_final_answer(self, agent_id: str, final_answer: str, snapshot_timestamp: Optional[str]=None):
        """Record the final answer presentation.

        Args:
            agent_id: ID of the agent
            final_answer: The final answer content
            snapshot_timestamp: Timestamp of the filesystem snapshot (if any)
        """
        final_answer_obj = AgentAnswer(agent_id=agent_id, content=final_answer, timestamp=time.time())
        agent_num = self._get_agent_number(agent_id)
        label = f'agent{agent_num}.final'
        final_answer_obj.label = label
        self.final_answers[agent_id] = final_answer_obj
        if snapshot_timestamp:
            self.snapshot_mappings[label] = {'type': 'final_answer', 'label': label, 'agent_id': agent_id, 'timestamp': snapshot_timestamp, 'iteration': self.current_iteration, 'round': self.get_agent_round(agent_id), 'path': self._make_snapshot_path('final_answer', agent_id, snapshot_timestamp)}
        context = {'label': label, **(self.final_context or {})}
        self._add_event(EventType.FINAL_ANSWER, agent_id, f'Presented final answer {label}', context)

    def start_final_round(self, selected_agent_id: str):
        """Start the final presentation round."""
        self.is_final_round = True
        final_round = self.max_round + 1
        self.agent_rounds[selected_agent_id] = final_round
        self.final_winner = selected_agent_id
        self.change_status(selected_agent_id, AgentStatus.STREAMING)
        self._add_event(EventType.FINAL_ROUND_START, selected_agent_id, f'Starting final presentation round {final_round}', {'round_type': 'final', 'final_round': final_round})

    def track_agent_action(self, agent_id: str, action_type, details: str=''):
        """Track any agent action using ActionType enum."""
        if action_type == ActionType.NEW_ANSWER:
            self.add_agent_answer(agent_id, details)
        elif action_type == ActionType.VOTE:
            pass
        else:
            event_type = ACTION_TO_EVENT.get(action_type)
            if event_type is None:
                raise ValueError(f'Unsupported ActionType: {action_type}')
            message = f'{action_type.value.upper()}: {details}' if details else action_type.value.upper()
            self._add_event(event_type, agent_id, message)

    def _add_event(self, event_type: EventType, agent_id: Optional[str], details: str, context: Optional[Dict[str, Any]]=None):
        """Internal method to add an event."""
        if context is None:
            context = {}
        context = context.copy()
        context['iteration'] = self.current_iteration
        if agent_id:
            context['round'] = self.get_agent_round(agent_id)
        else:
            context['round'] = self.max_round
        event = CoordinationEvent(timestamp=time.time(), event_type=event_type, agent_id=agent_id, details=details, context=context)
        self.events.append(event)

    def _end_session(self):
        """Mark the end of the coordination session."""
        self.end_time = time.time()
        duration = self.end_time - (self.start_time or self.end_time)
        self._add_event(EventType.SESSION_END, None, f'Session completed in {duration:.1f}s')

    @property
    def all_answers(self) -> Dict[str, str]:
        """Get all answers as a label->content dictionary."""
        result = {}
        for answers in self.answers_by_agent.values():
            for answer in answers:
                result[answer.label] = answer.content
        for answer in self.final_answers.values():
            result[answer.label] = answer.content
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary statistics."""
        duration = (self.end_time or time.time()) - (self.start_time or time.time())
        restart_count = len([e for e in self.events if e.event_type == EventType.RESTART_TRIGGERED])
        return {'duration': duration, 'total_events': len(self.events), 'total_restarts': restart_count, 'total_answers': sum((len(answers) for answers in self.answers_by_agent.values())), 'final_winner': self.final_winner, 'agent_count': len(self.agent_ids)}

    def save_coordination_logs(self, log_dir):
        """Save all coordination data and create timeline visualization.

        Args:
            log_dir: Directory to save logs
            format_style: "old", "new", or "both" (default)
        """
        try:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            events_file = log_dir / 'coordination_events.json'
            with open(events_file, 'w', encoding='utf-8') as f:
                events_data = [event.to_dict() for event in self.events]
                session_data = {'session_metadata': {'user_prompt': self.user_prompt, 'agent_ids': self.agent_ids, 'start_time': self.start_time, 'end_time': self.end_time, 'final_winner': self.final_winner}, 'events': events_data}
                json.dump(session_data, f, indent=2, default=str)
            if self.snapshot_mappings:
                snapshot_mappings_file = log_dir / 'snapshot_mappings.json'
                with open(snapshot_mappings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.snapshot_mappings, f, indent=2, default=str)
            try:
                self._generate_coordination_table(log_dir, session_data)
            except Exception as e:
                logger.warning(f'Warning: Could not generate coordination table: {e}', exc_info=True)
        except Exception as e:
            logger.warning(f'Failed to save coordination logs: {e}', exc_info=True)

    def _generate_coordination_table(self, log_dir, session_data):
        """Generate coordination table using the create_coordination_table.py module."""
        try:
            from massgen.frontend.displays.create_coordination_table import CoordinationTableBuilder
            builder = CoordinationTableBuilder(session_data)
            table_content = builder.generate_event_table()
            table_file = log_dir / 'coordination_table.txt'
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(table_content)
            logger.info(f'Coordination table generated at {table_file}')
        except Exception as e:
            logger.warning(f'Error generating coordination table: {e}', exc_info=True)

    def _get_agent_id_from_label(self, label: str) -> str:
        """Extract agent_id from a label like 'agent1.1' or 'agent2.final'."""
        import re
        match = re.match('agent(\\d+)', label)
        if match:
            agent_num = int(match.group(1))
            if 0 < agent_num <= len(self.agent_ids):
                return self.agent_ids[agent_num - 1]
        return 'unknown'

    def _get_agent_display_name(self, agent_id: str) -> str:
        """Get display name for agent (Agent1, Agent2, etc.)."""
        agent_num = self._get_agent_number(agent_id)
        return f'Agent{agent_num}' if agent_num else agent_id

@property
def max_round(self) -> int:
    """Get the highest round number across all agents."""
    return max(self.agent_rounds.values()) if self.agent_rounds else 0

@property
def all_answers(self) -> Dict[str, str]:
    """Get all answers as a label->content dictionary."""
    result = {}
    for answers in self.answers_by_agent.values():
        for answer in answers:
            result[answer.label] = answer.content
    for answer in self.final_answers.values():
        result[answer.label] = answer.content
    return result

def create_backend(backend_type: str, **kwargs) -> Any:
    """Create backend instance from type and parameters.

    Supported backend types:
    - openai: OpenAI API (requires OPENAI_API_KEY)
    - grok: xAI Grok (requires XAI_API_KEY)
    - sglang: SGLang inference server (local)
    - claude: Anthropic Claude (requires ANTHROPIC_API_KEY)
    - gemini: Google Gemini (requires GOOGLE_API_KEY or GEMINI_API_KEY)
    - chatcompletion: OpenAI-compatible providers (auto-detects API key based on base_url)

    Supported backend with external dependencies:
    - ag2/autogen: AG2 (AutoGen) framework agents

    For chatcompletion backend, the following providers are auto-detected:
    - Cerebras AI (cerebras.ai) -> CEREBRAS_API_KEY
    - Together AI (together.ai/together.xyz) -> TOGETHER_API_KEY
    - Fireworks AI (fireworks.ai) -> FIREWORKS_API_KEY
    - Groq (groq.com) -> GROQ_API_KEY
    - Nebius AI Studio (studio.nebius.ai) -> NEBIUS_API_KEY
    - OpenRouter (openrouter.ai) -> OPENROUTER_API_KEY
    - POE (poe.com) -> POE_API_KEY
    - Qwen (dashscope.aliyuncs.com) -> QWEN_API_KEY

    External agent frameworks are supported via the adapter registry.
    """
    backend_type = backend_type.lower()
    from massgen.adapters import adapter_registry
    if backend_type in adapter_registry:
        from massgen.backend.external import ExternalAgentBackend
        return ExternalAgentBackend(adapter_type=backend_type, **kwargs)
    if backend_type == 'openai':
        api_key = kwargs.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ConfigurationError('OpenAI API key not found. Set OPENAI_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
        return ResponseBackend(api_key=api_key, **kwargs)
    elif backend_type == 'grok':
        api_key = kwargs.get('api_key') or os.getenv('XAI_API_KEY')
        if not api_key:
            raise ConfigurationError('Grok API key not found. Set XAI_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
        return GrokBackend(api_key=api_key, **kwargs)
    elif backend_type == 'claude':
        api_key = kwargs.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ConfigurationError('Claude API key not found. Set ANTHROPIC_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
        return ClaudeBackend(api_key=api_key, **kwargs)
    elif backend_type == 'gemini':
        api_key = kwargs.get('api_key') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ConfigurationError('Gemini API key not found. Set GOOGLE_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
        return GeminiBackend(api_key=api_key, **kwargs)
    elif backend_type == 'chatcompletion':
        api_key = kwargs.get('api_key')
        base_url = kwargs.get('base_url')
        if not api_key:
            if base_url and 'cerebras.ai' in base_url:
                api_key = os.getenv('CEREBRAS_API_KEY')
                if not api_key:
                    raise ConfigurationError('Cerebras AI API key not found. Set CEREBRAS_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'together.xyz' in base_url:
                api_key = os.getenv('TOGETHER_API_KEY')
                if not api_key:
                    raise ConfigurationError('Together AI API key not found. Set TOGETHER_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'fireworks.ai' in base_url:
                api_key = os.getenv('FIREWORKS_API_KEY')
                if not api_key:
                    raise ConfigurationError('Fireworks AI API key not found. Set FIREWORKS_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'groq.com' in base_url:
                api_key = os.getenv('GROQ_API_KEY')
                if not api_key:
                    raise ConfigurationError('Groq API key not found. Set GROQ_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'nebius.com' in base_url:
                api_key = os.getenv('NEBIUS_API_KEY')
                if not api_key:
                    raise ConfigurationError('Nebius AI Studio API key not found. Set NEBIUS_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'openrouter.ai' in base_url:
                api_key = os.getenv('OPENROUTER_API_KEY')
                if not api_key:
                    raise ConfigurationError('OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and ('z.ai' in base_url or 'bigmodel.cn' in base_url):
                api_key = os.getenv('ZAI_API_KEY')
                if not api_key:
                    raise ConfigurationError('ZAI API key not found. Set ZAI_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and ('moonshot.ai' in base_url or 'moonshot.cn' in base_url):
                api_key = os.getenv('MOONSHOT_API_KEY') or os.getenv('KIMI_API_KEY')
                if not api_key:
                    raise ConfigurationError('Kimi/Moonshot API key not found. Set MOONSHOT_API_KEY or KIMI_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'poe.com' in base_url:
                api_key = os.getenv('POE_API_KEY')
                if not api_key:
                    raise ConfigurationError('POE API key not found. Set POE_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
            elif base_url and 'aliyuncs.com' in base_url:
                api_key = os.getenv('QWEN_API_KEY')
                if not api_key:
                    raise ConfigurationError('Qwen API key not found. Set QWEN_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
        return ChatCompletionsBackend(api_key=api_key, **kwargs)
    elif backend_type == 'zai':
        api_key = kwargs.get('api_key') or os.getenv('ZAI_API_KEY')
        if not api_key:
            raise ConfigurationError('ZAI API key not found. Set ZAI_API_KEY environment variable.\nYou can add it to a .env file in:\n  - Current directory: .env\n  - Global config: ~/.massgen/.env')
        return ChatCompletionsBackend(api_key=api_key, **kwargs)
    elif backend_type == 'lmstudio':
        return LMStudioBackend(**kwargs)
    elif backend_type == 'vllm':
        return InferenceBackend(backend_type='vllm', **kwargs)
    elif backend_type == 'sglang':
        return InferenceBackend(backend_type='sglang', **kwargs)
    elif backend_type == 'claude_code':
        try:
            pass
        except ImportError:
            raise ConfigurationError('claude-code-sdk not found. Install with: pip install claude-code-sdk')
        return ClaudeCodeBackend(**kwargs)
    elif backend_type == 'azure_openai':
        api_key = kwargs.get('api_key') or os.getenv('AZURE_OPENAI_API_KEY')
        endpoint = kwargs.get('base_url') or os.getenv('AZURE_OPENAI_ENDPOINT')
        if not api_key:
            raise ConfigurationError('Azure OpenAI API key not found. Set AZURE_OPENAI_API_KEY or provide in config.')
        if not endpoint:
            raise ConfigurationError('Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT or provide base_url in config.')
        return AzureOpenAIBackend(**kwargs)
    else:
        raise ConfigurationError(f'Unsupported backend type: {backend_type}')

class MCPClient:
    """
    Unified MCP client for communicating with single or multiple MCP servers.
    Provides improved security, error handling, and async context management.

    Accepts a list of server configurations and automatically handles:
    - Consistent tool naming: Always uses prefixed names (mcp__server__tool)
    - Circuit breaker protection for all servers
    - Parallel connection for multi-server scenarios
    - Sequential connection for single-server scenarios
    """

    def __init__(self, server_configs: List[Dict[str, Any]], *, timeout_seconds: int=30, allowed_tools: Optional[List[str]]=None, exclude_tools: Optional[List[str]]=None, status_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]]=None, hooks: Optional[Dict[HookType, List[Callable[[str, Dict[str, Any]], Awaitable[bool]]]]]=None):
        """
        Initialize MCP client.

        Args:
            server_configs: List of server configuration dicts (always a list, even for single server)
            timeout_seconds: Timeout for operations in seconds
            allowed_tools: Optional list of tool names to include (if None, includes all)
            exclude_tools: Optional list of tool names to exclude (if None, excludes none)
            status_callback: Optional async callback for status updates
            hooks: Optional dict mapping hook types to lists of hook functions
        """
        self._server_configs = [MCPConfigValidator.validate_server_config(config) for config in server_configs]
        self.name = self._server_configs[0]['name']
        self.timeout_seconds = timeout_seconds
        self.allowed_tools = allowed_tools
        self.exclude_tools = exclude_tools
        self.status_callback = status_callback
        self.hooks = hooks or {}
        self._circuit_breaker = MCPCircuitBreaker()
        self._server_clients: Dict[str, _ServerClient] = {}
        for config in self._server_configs:
            self._server_clients[config['name']] = _ServerClient()
        self.tools: Dict[str, mcp_types.Tool] = {}
        self._tool_to_server: Dict[str, str] = {}
        self._initialized = False
        self._cleanup_done = False
        self._cleanup_lock = asyncio.Lock()
        self._context_managed = False

    @property
    def session(self) -> Optional[ClientSession]:
        """Return first server's session for backward compatibility."""
        if self._server_configs:
            first_server_name = self._server_configs[0]['name']
            server_client = self._server_clients.get(first_server_name)
            if server_client:
                return server_client.session
        return None

    def _get_server_session(self, server_name: str) -> ClientSession:
        """Get session for server, raising error if not connected."""
        server_client = self._server_clients.get(server_name)
        if not server_client or not server_client.session:
            raise MCPConnectionError(f"Server '{server_name}' not connected", server_name=server_name)
        return server_client.session

    async def connect(self) -> None:
        """Connect to MCP server(s) and discover capabilities with circuit breaker integration."""
        if self._initialized:
            return
        logger.info(f'Connecting to {len(self._server_configs)} MCP server(s)...')
        if self.status_callback:
            await self.status_callback('connecting', {'message': f'Connecting to {len(self._server_configs)} MCP server(s)', 'server_count': len(self._server_configs)})
        if len(self._server_configs) > 1:
            await self._connect_all_parallel()
        else:
            await self._connect_single()
        self._initialized = any((sc.initialized for sc in self._server_clients.values()))
        successful_count = len([sc for sc in self._server_clients.values() if sc.initialized])
        failed_count = len(self._server_configs) - successful_count
        if self.status_callback:
            await self.status_callback('connection_summary', {'message': f'Connected to {successful_count}/{len(self._server_configs)} server(s)' + (f' ({failed_count} failed)' if failed_count > 0 else ''), 'successful_count': successful_count, 'failed_count': failed_count, 'total_count': len(self._server_configs), 'tools_count': len(self.tools)})

    async def _connect_server(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Connect to a single server with circuit breaker integration.

        Returns:
            True on success, False on failure
        """
        server_client = self._server_clients[server_name]
        async with server_client.connection_lock:
            if self._circuit_breaker.should_skip_server(server_name):
                logger.warning(f'Skipping server {server_name} due to circuit breaker')
                server_client.connection_state = ConnectionState.FAILED
                return False
            server_client.connection_state = ConnectionState.CONNECTING
            try:
                server_client.manager_task = asyncio.create_task(self._run_manager(server_name, config))
                await asyncio.wait_for(server_client.connected_event.wait(), timeout=30.0)
                if not server_client.initialized or server_client.connection_state != ConnectionState.CONNECTED:
                    raise MCPConnectionError(f'Failed to connect to {server_name}')
                self._circuit_breaker.record_success(server_name)
                logger.info(f"✅ MCP server '{server_name}' connected successfully!")
                return True
            except Exception as e:
                self._circuit_breaker.record_failure(server_name)
                server_client.connection_state = ConnectionState.FAILED
                logger.error(f'Failed to connect to {server_name}: {e}')
                if server_client.manager_task and (not server_client.manager_task.done()):
                    server_client.disconnect_event.set()
                    try:
                        await asyncio.wait_for(server_client.manager_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Manager task for {server_name} didn't shutdown gracefully, cancelling")
                        server_client.manager_task.cancel()
                        try:
                            await server_client.manager_task
                        except asyncio.CancelledError:
                            pass
                    except Exception as cleanup_error:
                        logger.error(f'Error cleaning up manager task for {server_name}: {cleanup_error}')
                    finally:
                        server_client.manager_task = None
                return False

    async def _connect_single(self) -> None:
        """Connect to single server."""
        config = self._server_configs[0]
        server_name = config['name']
        success = await self._connect_server(server_name, config)
        if not success:
            raise MCPConnectionError(f'Failed to connect to {server_name}')

    async def _connect_all_parallel(self) -> None:
        """Connect to all servers in parallel."""
        tasks = [self._connect_server(c['name'], c) for c in self._server_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum((1 for r in results if r is True))
        logger.info(f'Connected to {successful}/{len(self._server_configs)} servers')

    def _create_transport_context(self, config: Dict[str, Any]):
        """Create the appropriate transport context manager based on config."""
        transport_type = config.get('type', 'stdio')
        server_name = config['name']
        if transport_type == 'stdio':
            command = config.get('command', [])
            args = config.get('args', [])
            logger.debug(f'Setting up stdio transport for {server_name}: command={command}, args={args}')
            if isinstance(command, str):
                full_command = prepare_command(command)
                if args:
                    full_command.extend(args)
            elif isinstance(command, list):
                full_command = command + (args or [])
            else:
                full_command = args or []
            if not full_command:
                raise MCPConnectionError(f'No command specified for stdio transport in {server_name}')
            env = config.get('env', {})
            if env:
                env = {**get_default_environment(), **env}
            else:
                env = get_default_environment()
            substituted_args = []
            for arg in full_command[1:] if len(full_command) > 1 else []:
                if isinstance(arg, str):
                    try:
                        substituted_args.append(substitute_env_variables(arg))
                    except ValueError as e:
                        raise MCPConnectionError(f'Environment variable substitution failed in args: {e}', server_name=server_name) from e
                else:
                    substituted_args.append(arg)
            for key, value in list(env.items()):
                if isinstance(value, str):
                    try:
                        env[key] = substitute_env_variables(value)
                    except ValueError as e:
                        raise MCPConnectionError(f'Environment variable substitution failed for {key}: {e}', server_name=server_name) from e
            cwd = config.get('cwd')
            server_params = StdioServerParameters(command=full_command[0], args=substituted_args, env=env, cwd=cwd)
            from ..logger_config import get_log_session_dir
            log_dir = get_log_session_dir()
            errlog_path = log_dir / f'mcp_{server_name}_stderr.log'
            errlog_file = open(errlog_path, 'w', encoding='utf-8')
            if not hasattr(self, '_errlog_files'):
                self._errlog_files = {}
            self._errlog_files[server_name] = errlog_file
            return stdio_client(server_params, errlog=errlog_file)
        elif transport_type == 'streamable-http':
            url = config['url']
            headers = config.get('headers', {})
            substituted_headers = {}
            for key, value in headers.items():
                if isinstance(value, str):
                    try:
                        substituted_headers[key] = substitute_env_variables(value)
                    except ValueError as e:
                        raise MCPConnectionError(f'Environment variable substitution failed in header {key}: {e}', server_name=server_name) from e
                else:
                    substituted_headers[key] = value
            timeout_raw = config.get('timeout', self.timeout_seconds)
            http_read_timeout_raw = config.get('http_read_timeout', 60 * 5)
            timeout = _ensure_timedelta(timeout_raw, self.timeout_seconds)
            http_read_timeout = _ensure_timedelta(http_read_timeout_raw, 60 * 5)
            return streamablehttp_client(url=url, headers=substituted_headers, timeout=timeout, sse_read_timeout=http_read_timeout)
        else:
            raise MCPConnectionError(f'Unsupported transport type: {transport_type}')

    async def _run_manager(self, server_name: str, config: Dict[str, Any]) -> None:
        """Background task that owns the transport and session contexts for a server."""
        server_client = self._server_clients[server_name]
        connection_successful = False
        try:
            transport_ctx = self._create_transport_context(config)
            async with transport_ctx as session_params:
                read, write = session_params[0:2]
                session_timeout_timedelta = _ensure_timedelta(self.timeout_seconds, 30.0)
                async with ClientSession(read, write, read_timeout_seconds=session_timeout_timedelta) as session:
                    server_client.session = session
                    await session.initialize()
                    await self._discover_capabilities(server_name, config)
                    server_client.initialized = True
                    server_client.connection_state = ConnectionState.CONNECTED
                    connection_successful = True
                    server_client.connected_event.set()
                    logger.info(f"✅ MCP server '{server_name}' connected successfully!")
                    if self.status_callback:
                        await self.status_callback('connected', {'server': server_name, 'message': f"Server '{server_name}' ready"})
                    await server_client.disconnect_event.wait()
        except Exception as e:
            logger.error(f'MCP manager error for {server_name}: {e}', exc_info=True)
            if self.status_callback:
                await self.status_callback('error', {'server': server_name, 'message': f"Failed to connect to MCP server '{server_name}': {e}", 'error': str(e)})
            if not server_client.connected_event.is_set():
                server_client.connected_event.set()
        finally:
            server_client.initialized = False
            server_client.session = None
            if not connection_successful:
                server_client.connection_state = ConnectionState.FAILED
                if not server_client.connected_event.is_set():
                    server_client.connected_event.set()
            else:
                server_client.connection_state = ConnectionState.DISCONNECTED

    async def _discover_capabilities(self, server_name: str, config: Dict[str, Any]) -> None:
        """Discover server capabilities (tools, resources, prompts) with name prefixing for multi-server."""
        logger.debug(f'Discovering capabilities for {server_name}')
        session = self._get_server_session(server_name)
        try:
            server_exclude = config.get('exclude_tools', [])
            combined_exclude = list(set((self.exclude_tools or []) + server_exclude))
            server_allowed = config.get('allowed_tools')
            combined_allowed = server_allowed if server_allowed is not None else self.allowed_tools
            available_tools = await session.list_tools()
            tools_list = getattr(available_tools, 'tools', []) if available_tools else []
            for tool in tools_list:
                if combined_exclude and tool.name in combined_exclude:
                    continue
                if combined_allowed is None or tool.name in combined_allowed:
                    prefixed_name = sanitize_tool_name(tool.name, server_name)
                    self.tools[prefixed_name] = tool
                    self._tool_to_server[prefixed_name] = server_name
            logger.info(f'Discovered capabilities for {server_name}: {len([t for t, s in self._tool_to_server.items() if s == server_name])} tools')
        except Exception as e:
            logger.error(f'Failed to discover server capabilities for {server_name}: {e}', exc_info=True)
            raise MCPConnectionError(f'Failed to discover server capabilities: {e}') from e

    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        if not self._initialized:
            return
        tasks = [self._disconnect_one(name, client) for name, client in self._server_clients.items() if client.connection_state != ConnectionState.DISCONNECTED]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._initialized = False

    async def _disconnect_one(self, server_name: str, server_client: _ServerClient) -> None:
        """Disconnect a single server."""
        server_client.connection_state = ConnectionState.DISCONNECTING
        if server_client.manager_task and (not server_client.manager_task.done()):
            server_client.disconnect_event.set()
            try:
                await asyncio.wait_for(server_client.manager_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Manager task for {server_name} didn't shutdown gracefully, cancelling")
                server_client.manager_task.cancel()
                try:
                    await server_client.manager_task
                except asyncio.CancelledError:
                    logger.debug(f'Manager task for {server_name} cancelled successfully')
            except Exception as e:
                logger.error(f'Error during manager task shutdown for {server_name}: {e}')
            finally:
                server_client.manager_task = None
        server_client.initialized = False
        server_client.connection_state = ConnectionState.DISCONNECTED

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool with validation and timeout handling.

        Args:
            tool_name: Name of the tool to call (always prefixed as mcp__server__toolname)
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPError: If tool is not available
            MCPConnectionError: If no active session
            MCPValidationError: If arguments are invalid
            MCPTimeoutError: If tool call times out
            MCPServerError: If tool execution fails
        """
        if tool_name not in self.tools:
            available_tools = list(self.tools.keys())
            raise MCPError(f"Tool '{tool_name}' not available", context={'available_tools': available_tools, 'total': len(available_tools)})
        try:
            validated_arguments = validate_tool_arguments(arguments)
        except ValueError as e:
            raise MCPValidationError(f'Invalid tool arguments: {e}', field='arguments', value=arguments, context={'tool_name': tool_name}) from e
        pre_tool_hooks = self.hooks.get(HookType.PRE_TOOL_USE, [])
        for hook in pre_tool_hooks:
            try:
                allowed = await hook(tool_name, validated_arguments)
                if not allowed:
                    raise MCPValidationError('Tool call blocked by pre-tool hook', field='tool_name', value=tool_name, context={'arguments': validated_arguments})
            except Exception as e:
                if isinstance(e, MCPValidationError):
                    raise
                logger.warning(f'Pre-tool hook error for {tool_name}: {e}', exc_info=True)
        server_name = self._tool_to_server.get(tool_name)
        if not server_name:
            raise MCPError(f"Tool '{tool_name}' not mapped to any server")
        original_tool_name = tool_name[len(f'mcp__{server_name}__'):]
        session = self._get_server_session(server_name)
        logger.debug(f'Calling tool {original_tool_name} on {server_name} with arguments: {validated_arguments}')
        if self.status_callback:
            await self.status_callback('tool_call_start', {'server': server_name, 'tool': original_tool_name, 'message': f"Calling tool '{original_tool_name}' on server '{server_name}'", 'arguments': validated_arguments})
        try:
            result = await asyncio.wait_for(session.call_tool(original_tool_name, validated_arguments), timeout=self.timeout_seconds)
            logger.debug(f'Tool {original_tool_name} completed successfully on {server_name}')
            if self.status_callback:
                await self.status_callback('tool_call_success', {'server': server_name, 'tool': original_tool_name, 'message': f"Tool '{original_tool_name}' executed successfully"})
            return result
        except asyncio.TimeoutError:
            if self.status_callback:
                await self.status_callback('tool_call_timeout', {'server': server_name, 'tool': original_tool_name, 'message': f"Tool '{original_tool_name}' timed out after {self.timeout_seconds} seconds", 'timeout': self.timeout_seconds})
            self._circuit_breaker.record_failure(server_name)
            raise MCPTimeoutError(f'Tool call timed out after {self.timeout_seconds} seconds', timeout_seconds=self.timeout_seconds, operation=f'call_tool({original_tool_name})', context={'tool_name': original_tool_name, 'server_name': server_name})
        except Exception as e:
            logger.error(f'Tool call failed for {original_tool_name} on {server_name}: {e}', exc_info=True)
            self._circuit_breaker.record_failure(server_name)
            if self.status_callback:
                await self.status_callback('tool_call_error', {'server': server_name, 'tool': original_tool_name, 'message': f"Tool '{original_tool_name}' failed: {e}", 'error': str(e)})
            raise MCPServerError(f'Tool call failed: {e}', server_name=server_name, context={'tool_name': original_tool_name, 'arguments': validated_arguments}) from e

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())

    def is_connected(self) -> bool:
        """Check if any servers are connected."""
        return self._initialized and any((sc.initialized for sc in self._server_clients.values()))

    def get_server_names(self) -> List[str]:
        """Get list of connected server names."""
        return [name for name, sc in self._server_clients.items() if sc.initialized]

    def get_active_sessions(self) -> List[ClientSession]:
        """Return active MCP ClientSession objects for all connected servers."""
        sessions = []
        for server_client in self._server_clients.values():
            if server_client.session is not None and server_client.initialized:
                sessions.append(server_client.session)
        return sessions

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all connected MCP servers.

        Returns:
            Dictionary mapping server names to health status
        """
        health_status = {}
        for server_name, server_client in self._server_clients.items():
            if not server_client.initialized or not server_client.session:
                health_status[server_name] = False
                continue
            try:
                await server_client.session.list_tools()
                health_status[server_name] = True
            except Exception as e:
                logger.warning(f'Health check failed for {server_name}: {e}')
                health_status[server_name] = False
        return health_status

    async def health_check(self) -> bool:
        """
        Perform a health check on all servers.

        Returns:
            True if all connected servers are healthy, False otherwise
        """
        health_status = await self.health_check_all()
        return all(health_status.values()) if health_status else False

    async def _reconnect_failed_servers(self, max_retries: int=3) -> Dict[str, bool]:
        """
        Attempt to reconnect any failed servers with circuit breaker integration.

        Args:
            max_retries: Maximum number of reconnection attempts per server

        Returns:
            Dictionary mapping server names to reconnection success status
        """
        health_status = await self.health_check_all()
        reconnect_results = {}
        for server_name, is_healthy in health_status.items():
            if not is_healthy:
                if self._circuit_breaker.should_skip_server(server_name):
                    logger.warning(f'Skipping reconnection for {server_name} due to circuit breaker')
                    reconnect_results[server_name] = False
                    continue
                logger.info(f'Attempting to reconnect failed server: {server_name}')
                config = next((c for c in self._server_configs if c['name'] == server_name), None)
                if not config:
                    reconnect_results[server_name] = False
                    continue
                success = False
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            await asyncio.sleep(1.0 * 2 ** attempt)
                        server_client = self._server_clients[server_name]
                        await self._disconnect_one(server_name, server_client)
                        server_client.connected_event = asyncio.Event()
                        server_client.disconnect_event = asyncio.Event()
                        server_client.manager_task = asyncio.create_task(self._run_manager(server_name, config))
                        await asyncio.wait_for(server_client.connected_event.wait(), timeout=30.0)
                        if server_client.initialized:
                            self._circuit_breaker.record_success(server_name)
                            success = True
                            logger.info(f'Successfully reconnected server: {server_name}')
                            break
                    except Exception as e:
                        logger.warning(f'Reconnection attempt {attempt + 1} failed for {server_name}: {e}')
                        self._circuit_breaker.record_failure(server_name)
                reconnect_results[server_name] = success
            else:
                reconnect_results[server_name] = True
        return reconnect_results

    async def reconnect(self, max_retries: int=3) -> bool:
        """
        Attempt to reconnect all servers with circuit breaker integration.

        Args:
            max_retries: Maximum number of reconnection attempts
                Uses exponential backoff between retries: 2s, 4s, 8s, 16s...

        Returns:
            True if all reconnections successful, False otherwise
        """
        results = await self._reconnect_failed_servers(max_retries)
        return all(results.values()) if results else False

    async def _cleanup(self) -> None:
        """Comprehensive cleanup of all resources."""
        async with self._cleanup_lock:
            if self._cleanup_done:
                return
            logger.debug('Starting cleanup for MCPClient')
            try:
                await self.disconnect()
                if hasattr(self, '_errlog_files'):
                    for server_name, errlog_file in self._errlog_files.items():
                        try:
                            errlog_file.close()
                        except Exception as e:
                            logger.debug(f'Error closing errlog file for {server_name}: {e}')
                    self._errlog_files.clear()
                self.tools.clear()
                self._tool_to_server.clear()
                self._cleanup_done = True
                logger.debug('Cleanup completed for MCPClient')
            except Exception as e:
                logger.error(f'Error during cleanup: {e}')
                raise

    async def __aenter__(self) -> 'MCPClient':
        """Async context manager entry."""
        self._context_managed = True
        await self.connect()
        return self

    async def __aexit__(self, _exc_type: Optional[type], _exc_val: Optional[BaseException], _exc_tb: Optional[TracebackType]) -> None:
        """Async context manager exit."""
        try:
            await self._cleanup()
        except Exception as e:
            logger.error(f'Error during context manager cleanup: {e}')
        finally:
            self._context_managed = False

    @classmethod
    async def create_and_connect(cls, server_configs: List[Dict[str, Any]], *, timeout_seconds: int=30, allowed_tools: Optional[List[str]]=None, exclude_tools: Optional[List[str]]=None) -> 'MCPClient':
        """
        Create and connect MCP client in one step.

        Args:
            server_configs: List of server configuration dictionaries
            timeout_seconds: Timeout for operations in seconds
            allowed_tools: Optional list of tool names to include
            exclude_tools: Optional list of tool names to exclude

        Returns:
            Connected MCPClient instance
        """
        client = cls(server_configs, timeout_seconds=timeout_seconds, allowed_tools=allowed_tools, exclude_tools=exclude_tools)
        await client.connect()
        return client

def is_connected(self) -> bool:
    """Check if any servers are connected."""
    return self._initialized and any((sc.initialized for sc in self._server_clients.values()))

def get_active_sessions(self) -> List[ClientSession]:
    """Return active MCP ClientSession objects for all connected servers."""
    sessions = []
    for server_client in self._server_clients.values():
        if server_client.session is not None and server_client.initialized:
            sessions.append(server_client.session)
    return sessions

class MCPCircuitBreaker:
    """
    Circuit breaker for MCP server failure handling.

    Provides consistent failure tracking and exponential backoff across all MCP integrations.
    Prevents repeated connection attempts to failing servers while allowing recovery.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig]=None, backend_name: Optional[str]=None, agent_id: Optional[str]=None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration. Uses default if None.
            backend_name: Name of the backend using this circuit breaker for logging context.
            agent_id: Optional agent ID for logging context.
        """
        self.config = config or CircuitBreakerConfig()
        self.backend_name = backend_name
        self.agent_id = agent_id
        self._server_status: Dict[str, ServerStatus] = {}

    def should_skip_server(self, server_name: str, agent_id: Optional[str]=None) -> bool:
        """
        Check if server should be skipped due to circuit breaker.

        Args:
            server_name: Name of the server to check

        Returns:
            True if server should be skipped, False otherwise
        """
        if server_name not in self._server_status:
            return False
        status = self._server_status[server_name]
        if status.failure_count < self.config.max_failures:
            return False
        current_time = time.monotonic()
        time_since_failure = current_time - status.last_failure_time
        backoff_time = self._calculate_backoff_time(status.failure_count)
        if time_since_failure > backoff_time:
            log_mcp_activity(self.backend_name, 'Circuit breaker reset for server', {'server_name': server_name, 'backoff_time_seconds': backoff_time}, agent_id=self.agent_id or agent_id)
            self._reset_server(server_name)
            return False
        return True

    def record_failure(self, server_name: str, agent_id: Optional[str]=None) -> None:
        """
        Record a server failure for circuit breaker.

        Args:
            server_name: Name of the server that failed
        """
        current_time = time.monotonic()
        if server_name not in self._server_status:
            self._server_status[server_name] = ServerStatus()
        status = self._server_status[server_name]
        status.failure_count += 1
        status.last_failure_time = current_time
        if status.failure_count >= self.config.max_failures:
            backoff_time = self._calculate_backoff_time(status.failure_count)
            log_mcp_activity(self.backend_name, 'Server circuit breaker opened', {'server_name': server_name, 'failure_count': status.failure_count, 'backoff_time_seconds': backoff_time}, agent_id=self.agent_id or agent_id)
        else:
            log_mcp_activity(self.backend_name, 'Server failure recorded', {'server_name': server_name, 'failure_count': status.failure_count, 'max_failures': self.config.max_failures}, agent_id=self.agent_id or agent_id)

    def record_success(self, server_name: str, agent_id: Optional[str]=None) -> None:
        """
        Record a successful connection, resetting failure count.

        Args:
            server_name: Name of the server that succeeded
        """
        if server_name in self._server_status:
            old_status = self._server_status[server_name]
            if old_status.failure_count > 0:
                log_mcp_activity(self.backend_name, 'Server recovered', {'server_name': server_name, 'previous_failure_count': old_status.failure_count}, agent_id=self.agent_id or agent_id)
            self._reset_server(server_name)

    def _reset_server(self, server_name: str) -> None:
        """Reset circuit breaker state for a specific server."""
        if server_name in self._server_status:
            del self._server_status[server_name]

    def _calculate_backoff_time(self, failure_count: int) -> float:
        """
        Calculate backoff time based on failure count.

        Args:
            failure_count: Number of failures

        Returns:
            Backoff time in seconds
        """
        if failure_count < self.config.max_failures:
            return 0.0
        exponent = failure_count - self.config.max_failures
        multiplier = min(self.config.backoff_multiplier ** exponent, self.config.max_backoff_multiplier)
        return self.config.reset_time_seconds * multiplier

    def __repr__(self) -> str:
        """String representation for debugging."""
        failing_count = len([s for s in self._server_status.values() if s.is_failing])
        total_servers = len(self._server_status)
        return f'MCPCircuitBreaker(failing={failing_count}/{total_servers}, config={self.config})'

def __repr__(self) -> str:
    """String representation for debugging."""
    failing_count = len([s for s in self._server_status.values() if s.is_failing])
    total_servers = len(self._server_status)
    return f'MCPCircuitBreaker(failing={failing_count}/{total_servers}, config={self.config})'

class DockerManager:
    """
    Manages Docker containers for isolated command execution.

    Each agent gets a persistent container for the orchestration session:
    - Volume mounts for workspace and context paths
    - Network isolation (configurable)
    - Resource limits (CPU, memory)
    - Commands executed via docker exec
    - State persists across turns (packages stay installed)
    """

    def __init__(self, image: str='massgen/mcp-runtime:latest', network_mode: str='none', memory_limit: Optional[str]=None, cpu_limit: Optional[float]=None):
        """
        Initialize Docker manager.

        Args:
            image: Docker image to use for containers
            network_mode: Network mode (none/bridge/host)
            memory_limit: Memory limit (e.g., "2g", "512m")
            cpu_limit: CPU limit (e.g., 2.0 for 2 CPUs)

        Raises:
            RuntimeError: If Docker is not available or cannot connect
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError('Docker Python library not available. Install with: pip install docker')
        self.image = image
        self.network_mode = network_mode
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        try:
            self.client = docker.from_env()
            self.client.ping()
            version_info = self.client.version()
            docker_version = version_info.get('Version', 'unknown')
            api_version = version_info.get('ApiVersion', 'unknown')
            logger.info('🐳 [Docker] Client initialized successfully')
            logger.info(f'    Docker version: {docker_version}')
            logger.info(f'    API version: {api_version}')
        except DockerException as e:
            logger.error(f'❌ [Docker] Failed to connect to Docker daemon: {e}')
            raise RuntimeError(f'Failed to connect to Docker: {e}')
        self.containers: Dict[str, Container] = {}

    def ensure_image_exists(self) -> None:
        """
        Ensure the Docker image exists locally.

        Pulls the image if not found locally.

        Raises:
            RuntimeError: If image cannot be pulled
        """
        try:
            self.client.images.get(self.image)
            logger.info(f"✅ [Docker] Image '{self.image}' found locally")
        except ImageNotFound:
            logger.info(f"📥 [Docker] Image '{self.image}' not found locally, pulling...")
            try:
                self.client.images.pull(self.image)
                logger.info(f"✅ [Docker] Successfully pulled image '{self.image}'")
            except DockerException as e:
                raise RuntimeError(f"Failed to pull Docker image '{self.image}': {e}")

    def create_container(self, agent_id: str, workspace_path: Path, temp_workspace_path: Optional[Path]=None, context_paths: Optional[List[Dict[str, Any]]]=None) -> str:
        """
        Create and start a persistent Docker container for an agent.

        The container runs for the entire orchestration session and maintains state
        across command executions (installed packages, generated files, etc.).

        IMPORTANT: Paths are mounted at the SAME location as on the host to maintain
        path transparency. The LLM sees identical paths whether in Docker or local mode.

        Args:
            agent_id: Unique identifier for the agent
            workspace_path: Path to agent's workspace (mounted at same path, read-write)
            temp_workspace_path: Path to shared temp workspace (mounted at same path, read-only)
            context_paths: List of context path dicts with 'path', 'permission', and optional 'name' keys
                          (each mounted at its host path)

        Returns:
            Container ID

        Raises:
            RuntimeError: If container creation fails
        """
        if agent_id in self.containers:
            logger.warning(f'⚠️ [Docker] Container for agent {agent_id} already exists')
            return self.containers[agent_id].id
        self.ensure_image_exists()
        container_name = f'massgen-{agent_id}'
        try:
            existing = self.client.containers.get(container_name)
            logger.warning(f"🔄 [Docker] Found existing container '{container_name}' (id: {existing.short_id}), removing it")
            existing.remove(force=True)
        except NotFound:
            pass
        except DockerException as e:
            logger.warning(f"⚠️ [Docker] Error checking for existing container '{container_name}': {e}")
        logger.info(f"🐳 [Docker] Creating container for agent '{agent_id}'")
        logger.info(f'    Image: {self.image}')
        logger.info(f'    Network: {self.network_mode}')
        if self.memory_limit:
            logger.info(f'    Memory limit: {self.memory_limit}')
        if self.cpu_limit:
            logger.info(f'    CPU limit: {self.cpu_limit} cores')
        volumes = {}
        mount_info = []
        workspace_path = workspace_path.resolve()
        volumes[str(workspace_path)] = {'bind': str(workspace_path), 'mode': 'rw'}
        mount_info.append(f'      {workspace_path} ← {workspace_path} (rw)')
        if temp_workspace_path:
            temp_workspace_path = temp_workspace_path.resolve()
            volumes[str(temp_workspace_path)] = {'bind': str(temp_workspace_path), 'mode': 'ro'}
            mount_info.append(f'      {temp_workspace_path} ← {temp_workspace_path} (ro)')
        if context_paths:
            for ctx_path_config in context_paths:
                ctx_path = Path(ctx_path_config['path']).resolve()
                permission = ctx_path_config.get('permission', 'read')
                mode = 'rw' if permission == 'write' else 'ro'
                volumes[str(ctx_path)] = {'bind': str(ctx_path), 'mode': mode}
                mount_info.append(f'      {ctx_path} ← {ctx_path} ({mode})')
        if mount_info:
            logger.info('    Volume mounts:')
            for mount_line in mount_info:
                logger.info(mount_line)
        resource_config = {}
        if self.memory_limit:
            resource_config['mem_limit'] = self.memory_limit
        if self.cpu_limit:
            resource_config['nano_cpus'] = int(self.cpu_limit * 1000000000.0)
        container_config = {'image': self.image, 'name': container_name, 'command': ['tail', '-f', '/dev/null'], 'detach': True, 'volumes': volumes, 'working_dir': str(workspace_path), 'network_mode': self.network_mode, 'auto_remove': False, 'stdin_open': True, 'tty': True, **resource_config}
        try:
            container = self.client.containers.run(**container_config)
            self.containers[agent_id] = container
            container.reload()
            status = container.status
            logger.info('✅ [Docker] Container created successfully')
            logger.info(f'    Container ID: {container.short_id}')
            logger.info(f'    Container name: {container_name}')
            logger.info(f'    Status: {status}')
            logger.debug(f'💡 [Docker] Inspect container: docker inspect {container.short_id}')
            logger.debug(f'💡 [Docker] View logs: docker logs {container.short_id}')
            logger.debug(f'💡 [Docker] Execute commands: docker exec -it {container.short_id} /bin/bash')
            return container.id
        except DockerException as e:
            logger.error(f'❌ [Docker] Failed to create container for agent {agent_id}: {e}')
            raise RuntimeError(f'Failed to create Docker container for agent {agent_id}: {e}')

    def get_container(self, agent_id: str) -> Optional[Container]:
        """
        Get container for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Container object or None if not found
        """
        return self.containers.get(agent_id)

    def exec_command(self, agent_id: str, command: str, workdir: Optional[str]=None, timeout: Optional[int]=None) -> Dict[str, Any]:
        """
        Execute a command inside the agent's container.

        Args:
            agent_id: Agent identifier
            command: Command to execute (as string, will be run in shell)
            workdir: Working directory (uses host path - same path is mounted in container)
            timeout: Command timeout in seconds (implemented using threading)

        Returns:
            Dictionary with:
            - success: bool (True if exit_code == 0)
            - exit_code: int
            - stdout: str
            - stderr: str (combined with stdout in Docker exec)
            - execution_time: float
            - command: str
            - work_dir: str

        Raises:
            ValueError: If container not found
            RuntimeError: If execution fails
        """
        container = self.containers.get(agent_id)
        if not container:
            raise ValueError(f'No container found for agent {agent_id}')
        effective_workdir = workdir if workdir else None
        try:
            exec_config = {'cmd': ['/bin/sh', '-c', command], 'stdout': True, 'stderr': True}
            if effective_workdir:
                exec_config['workdir'] = effective_workdir
            logger.debug(f'🔧 [Docker] Executing in container {container.short_id}: {command}')
            start_time = time.time()
            if timeout:
                result_container = {}
                exception_container = {}

                def run_exec():
                    try:
                        result_container['data'] = container.exec_run(**exec_config)
                    except Exception as e:
                        exception_container['error'] = e
                thread = threading.Thread(target=run_exec)
                thread.daemon = True
                thread.start()
                thread.join(timeout=timeout)
                execution_time = time.time() - start_time
                if thread.is_alive():
                    logger.warning(f'⚠️ [Docker] Command timed out after {timeout}s: {command}')
                    return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Command timed out after {timeout} seconds', 'execution_time': execution_time, 'command': command, 'work_dir': effective_workdir or '(container default)'}
                if 'error' in exception_container:
                    raise exception_container['error']
                exit_code, output = result_container['data']
            else:
                exit_code, output = container.exec_run(**exec_config)
                execution_time = time.time() - start_time
            output_str = output.decode('utf-8') if isinstance(output, bytes) else output
            if exit_code != 0:
                logger.debug(f'⚠️ [Docker] Command exited with code {exit_code}')
            return {'success': exit_code == 0, 'exit_code': exit_code, 'stdout': output_str, 'stderr': '', 'execution_time': execution_time, 'command': command, 'work_dir': effective_workdir or '(container default)'}
        except DockerException as e:
            logger.error(f'❌ [Docker] Failed to execute command in container: {e}')
            raise RuntimeError(f'Failed to execute command in container: {e}')

    def stop_container(self, agent_id: str, timeout: int=10) -> None:
        """
        Stop a container gracefully.

        Args:
            agent_id: Agent identifier
            timeout: Seconds to wait before killing

        Raises:
            ValueError: If container not found
        """
        container = self.containers.get(agent_id)
        if not container:
            raise ValueError(f'No container found for agent {agent_id}')
        try:
            logger.info(f'🛑 [Docker] Stopping container {container.short_id} for agent {agent_id}')
            container.stop(timeout=timeout)
            logger.info('✅ [Docker] Container stopped successfully')
        except DockerException as e:
            logger.error(f'❌ [Docker] Failed to stop container for agent {agent_id}: {e}')

    def remove_container(self, agent_id: str, force: bool=False) -> None:
        """
        Remove a container.

        Args:
            agent_id: Agent identifier
            force: Force removal even if running

        Raises:
            ValueError: If container not found
        """
        container = self.containers.get(agent_id)
        if not container:
            raise ValueError(f'No container found for agent {agent_id}')
        try:
            container_id = container.short_id
            logger.info(f'🗑️  [Docker] Removing container {container_id} for agent {agent_id}')
            container.remove(force=force)
            del self.containers[agent_id]
            logger.info('✅ [Docker] Container removed successfully')
        except DockerException as e:
            logger.error(f'❌ [Docker] Failed to remove container for agent {agent_id}: {e}')

    def cleanup(self, agent_id: Optional[str]=None) -> None:
        """
        Clean up containers.

        Args:
            agent_id: If provided, cleanup specific agent. Otherwise cleanup all.
        """
        if agent_id:
            if agent_id in self.containers:
                logger.info(f'🧹 [Docker] Cleaning up container for agent {agent_id}')
                try:
                    self.stop_container(agent_id)
                    self.remove_container(agent_id, force=True)
                except Exception as e:
                    logger.error(f'❌ [Docker] Error cleaning up container for agent {agent_id}: {e}')
        else:
            if self.containers:
                logger.info(f'🧹 [Docker] Cleaning up {len(self.containers)} container(s)')
            for aid in list(self.containers.keys()):
                try:
                    self.stop_container(aid)
                    self.remove_container(aid, force=True)
                except Exception as e:
                    logger.error(f'❌ [Docker] Error cleaning up container for agent {aid}: {e}')

    def log_container_info(self, agent_id: str) -> None:
        """
        Log detailed container information (useful for debugging).

        Args:
            agent_id: Agent identifier
        """
        container = self.containers.get(agent_id)
        if not container:
            logger.warning(f'⚠️ [Docker] No container found for agent {agent_id}')
            return
        try:
            container.reload()
            logger.info(f"📊 [Docker] Container information for agent '{agent_id}':")
            logger.info(f'    ID: {container.short_id}')
            logger.info(f'    Name: {container.name}')
            logger.info(f'    Status: {container.status}')
            logger.info(f'    Network: {self.network_mode}')
            if self.memory_limit:
                logger.info(f'    Memory limit: {self.memory_limit}')
            if self.cpu_limit:
                logger.info(f'    CPU limit: {self.cpu_limit} cores')
        except Exception as e:
            logger.warning(f'⚠️ [Docker] Could not log container info: {e}')

    def __del__(self):
        """Cleanup all containers on deletion."""
        try:
            if hasattr(self, 'containers') and self.containers:
                self.cleanup()
        except Exception:
            pass

def __del__(self):
    """Cleanup all containers on deletion."""
    try:
        if hasattr(self, 'containers') and self.containers:
            self.cleanup()
    except Exception:
        pass

class CoordinationUI:
    """Main coordination interface with display capabilities."""

    def __init__(self, display: Optional[BaseDisplay]=None, logger: Optional[Any]=None, display_type: str='terminal', enable_final_presentation: bool=False, **kwargs):
        """Initialize coordination UI.

        Args:
            display: Custom display instance (overrides display_type)
            logger: Custom logger instance
            display_type: Type of display ("terminal", "simple", "rich_terminal", "textual_terminal")
            enable_final_presentation: Whether to ask winning agent to present final answer
            **kwargs: Additional configuration passed to display/logger
        """
        self.enable_final_presentation = enable_final_presentation
        self.display = display
        self.logger = logger
        self.display_type = display_type
        self.config = kwargs
        self.agent_ids = []
        self.orchestrator = None
        self._flush_char_delay = 0.03
        self._answer_buffer = ''
        self._answer_timeout_task = None
        self._final_answer_shown = False

    def _process_reasoning_summary(self, chunk_type: str, summary_delta: str, source: str) -> str:
        """Process reasoning summary content using display's shared logic."""
        if self.display and hasattr(self.display, 'process_reasoning_content'):
            return self.display.process_reasoning_content(chunk_type, summary_delta, source)
        else:
            if chunk_type == 'reasoning_summary':
                summary_active_key = f'_summary_active_{source}'
                if not getattr(self, summary_active_key, False):
                    setattr(self, summary_active_key, True)
                    return f'📋 [Reasoning Summary]\n{summary_delta}\n'
                return summary_delta
            elif chunk_type == 'reasoning_summary_done':
                summary_active_key = f'_summary_active_{source}'
                if hasattr(self, summary_active_key):
                    setattr(self, summary_active_key, False)
            return summary_delta

    def _process_reasoning_content(self, chunk_type: str, reasoning_delta: str, source: str) -> str:
        """Process reasoning summary content using display's shared logic."""
        if self.display and hasattr(self.display, 'process_reasoning_content'):
            return self.display.process_reasoning_content(chunk_type, reasoning_delta, source)
        elif chunk_type == 'reasoning':
            reasoning_active_key = f'_reasoning_active_{source}'
            if not getattr(self, reasoning_active_key, False):
                setattr(self, reasoning_active_key, True)
                return f'🧠 [Reasoning Started]\n{reasoning_delta}\n'
            return reasoning_delta
        elif chunk_type == 'reasoning_done':
            reasoning_active_key = f'_reasoning_active_{source}'
            if hasattr(self, reasoning_active_key):
                setattr(self, reasoning_active_key, False)
            return reasoning_delta

    def __post_init__(self):
        """Post-initialization setup."""
        self._flush_word_delay = 0.08
        self._answer_buffer = ''
        self._answer_timeout_task = None
        self._final_answer_shown = False

    def reset(self):
        """Reset UI state for next coordination session."""
        if self.display:
            try:
                self.display.cleanup()
            except Exception:
                pass
            self.display = None
        self.agent_ids = []
        self.orchestrator = None
        if hasattr(self, '_answer_buffer'):
            self._answer_buffer = ''
        if hasattr(self, '_answer_timeout_task') and self._answer_timeout_task:
            self._answer_timeout_task.cancel()
            self._answer_timeout_task = None
        if hasattr(self, '_final_answer_shown'):
            self._final_answer_shown = False

    async def coordinate(self, orchestrator, question: str, agent_ids: Optional[List[str]]=None) -> str:
        """Coordinate agents with visual display.

        Args:
            orchestrator: MassGen orchestrator instance
            question: Question for coordination
            agent_ids: Optional list of agent IDs (auto-detected if not provided)

        Returns:
            Final coordinated response
        """
        selected_agent = ''
        vote_results = {}
        final_result = ''
        final_answer = ''
        if self.display is not None:
            self.display.cleanup()
        self.display = None
        self.orchestrator = orchestrator
        if agent_ids is None:
            self.agent_ids = list(orchestrator.agents.keys())
        else:
            self.agent_ids = agent_ids
        if self.display is None:
            if self.display_type == 'terminal':
                self.display = TerminalDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'simple':
                self.display = SimpleDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'rich_terminal':
                if not is_rich_available():
                    print('⚠️  Rich library not available. Falling back to terminal display.')
                    print('   Install with: pip install rich')
                    self.display = TerminalDisplay(self.agent_ids, **self.config)
                else:
                    self.display = RichTerminalDisplay(self.agent_ids, **self.config)
            else:
                raise ValueError(f'Unknown display type: {self.display_type}')
        self.display.orchestrator = orchestrator
        self._answer_buffer = ''
        self._answer_timeout_task = None
        self._final_answer_shown = False
        log_filename = None
        if self.logger:
            log_filename = self.logger.initialize_session(question, self.agent_ids)
            monitoring = self.logger.get_monitoring_commands()
            print(f'📁 Real-time log: {log_filename}')
            print(f'💡 Monitor with: {monitoring['tail']}')
            print()
        self.display.initialize(question, log_filename)
        selected_agent = None
        vote_results = {}
        try:
            full_response = ''
            final_answer = ''
            async for chunk in orchestrator.chat_simple(question):
                content = getattr(chunk, 'content', '') or ''
                source = getattr(chunk, 'source', None)
                chunk_type = getattr(chunk, 'type', '')
                if chunk_type == 'agent_status':
                    status = getattr(chunk, 'status', None)
                    if source and status:
                        self.display.update_agent_status(source, status)
                    continue
                elif chunk_type == 'debug':
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type == 'mcp_status':
                    if source and source in self.agent_ids:
                        self.display.update_agent_content(source, content, 'tool')
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                    if source:
                        reasoning_content = ''
                        if chunk_type == 'reasoning':
                            reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                            if reasoning_delta:
                                reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                        elif chunk_type == 'reasoning_done':
                            reasoning_text = getattr(chunk, 'reasoning_text', '')
                            if reasoning_text:
                                reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                            else:
                                reasoning_content = '\n🧠 [Reasoning Complete]\n'
                            self._process_reasoning_content(chunk_type, reasoning_content, source)
                            reasoning_active_key = '_reasoning_active'
                            if hasattr(self, reasoning_active_key):
                                delattr(self, reasoning_active_key)
                        elif chunk_type == 'reasoning_summary':
                            summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                            if summary_delta:
                                reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                        elif chunk_type == 'reasoning_summary_done':
                            summary_text = getattr(chunk, 'reasoning_summary_text', '')
                            if summary_text:
                                reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                            self._process_reasoning_summary(chunk_type, '', source)
                            summary_active_key = f'_summary_active_{source}'
                            if hasattr(self, summary_active_key):
                                delattr(self, summary_active_key)
                        if reasoning_content:
                            self.display.update_agent_content(source, reasoning_content, 'thinking')
                            if self.logger:
                                self.logger.log_agent_content(source, reasoning_content, 'reasoning')
                    continue
                if chunk_type == 'status' and 'presenting final answer' in content:
                    for attr_name in list(vars(self).keys()):
                        if attr_name.startswith('_summary_active_'):
                            delattr(self, attr_name)
                if content:
                    full_response += content
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk.type)
                    await self._process_content(source, content)
            status = orchestrator.get_status()
            vote_results = status.get('vote_results', {})
            selected_agent = status.get('selected_agent')
            if selected_agent is None:
                selected_agent = ''
            if self.enable_final_presentation and selected_agent and vote_results.get('vote_counts'):
                presentation_content = ''
                try:
                    async for chunk in orchestrator.get_final_presentation(selected_agent, vote_results):
                        content = getattr(chunk, 'content', '') or ''
                        chunk_type = getattr(chunk, 'type', '')
                        if chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                            source = getattr(chunk, 'source', selected_agent)
                            reasoning_content = ''
                            if chunk_type == 'reasoning':
                                reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                                if reasoning_delta:
                                    reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                            elif chunk_type == 'reasoning_done':
                                reasoning_text = getattr(chunk, 'reasoning_text', '')
                                if reasoning_text:
                                    reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                                else:
                                    reasoning_content = '\n🧠 [Reasoning Complete]\n'
                                self._process_reasoning_content(chunk_type, reasoning_content, source)
                                reasoning_active_key = '_reasoning_active'
                                if hasattr(self, reasoning_active_key):
                                    delattr(self, reasoning_active_key)
                            elif chunk_type == 'reasoning_summary':
                                summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                                if summary_delta:
                                    reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                            elif chunk_type == 'reasoning_summary_done':
                                summary_text = getattr(chunk, 'reasoning_summary_text', '')
                                if summary_text:
                                    reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                                self._process_reasoning_summary(chunk_type, '', source)
                                summary_active_key = f'_summary_active_{source}'
                                if hasattr(self, summary_active_key):
                                    delattr(self, summary_active_key)
                            if reasoning_content:
                                content = reasoning_content
                        if content:
                            if isinstance(content, list):
                                content = ' '.join((str(item) for item in content))
                            elif not isinstance(content, str):
                                content = str(content)
                            presentation_content += content
                            if self.logger:
                                self.logger.log_chunk(selected_agent, content, getattr(chunk, 'type', 'presentation'))
                            if self.display:
                                try:
                                    await self._process_content(selected_agent, content)
                                except Exception:
                                    pass
                            else:
                                print(content, end='', flush=True)
                except AttributeError:
                    presentation_content = ''
                final_answer = presentation_content
                time.sleep(1.5)
            orchestrator_final_answer = None
            if hasattr(orchestrator, '_final_presentation_content') and orchestrator._final_presentation_content:
                orchestrator_final_answer = orchestrator._final_presentation_content.strip()
            elif selected_agent and hasattr(orchestrator, 'agent_states') and (selected_agent in orchestrator.agent_states):
                stored_answer = orchestrator.agent_states[selected_agent].answer
                if stored_answer:
                    orchestrator_final_answer = stored_answer.replace('\\', '\n').replace('**', '').strip()
            final_result = orchestrator_final_answer if orchestrator_final_answer else final_answer if final_answer else full_response
            if self.logger:
                session_info = self.logger.finalize_session(final_result if 'final_result' in locals() else final_answer if 'final_answer' in locals() else '', success=True)
                print(f'💾 Session log: {session_info['filename']}')
                print(f'⏱️  Duration: {session_info['duration']:.1f}s | Chunks: {session_info['total_chunks']} | Events: {session_info['orchestrator_events']}')
            return final_result
        except Exception:
            if self.logger:
                self.logger.finalize_session('', success=False)
            raise
        finally:
            if hasattr(self, '_answer_timeout_task') and self._answer_timeout_task:
                try:
                    await asyncio.wait_for(self._answer_timeout_task, timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                        await self._flush_final_answer()
                    self._answer_timeout_task.cancel()
            if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                await self._flush_final_answer()
            await asyncio.sleep(0.1)
            if self.display:
                self.display.cleanup()
            if self.logger:
                session_info = self.logger.finalize_session(final_result if 'final_result' in locals() else final_answer if 'final_answer' in locals() else '', success=True)
                print(f'💾 Session log: {session_info['filename']}')
                print(f'⏱️  Duration: {session_info['duration']:.1f}s | Chunks: {session_info['total_chunks']} | Events: {session_info['orchestrator_events']}')

    async def coordinate_with_context(self, orchestrator, question: str, messages: List[Dict[str, Any]], agent_ids: Optional[List[str]]=None) -> str:
        """Coordinate agents with conversation context and visual display.

        Args:
            orchestrator: MassGen orchestrator instance
            question: Current question for coordination
            messages: Full conversation message history
            agent_ids: Optional list of agent IDs (auto-detected if not provided)

        Returns:
            Final coordinated response
        """
        selected_agent = ''
        vote_results = {}
        final_result = ''
        final_answer = ''
        if self.display is not None:
            self.display.cleanup()
        self.display = None
        self.orchestrator = orchestrator
        if agent_ids is None:
            self.agent_ids = list(orchestrator.agents.keys())
        else:
            self.agent_ids = agent_ids
        if self.display is None:
            if self.display_type == 'terminal':
                self.display = TerminalDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'simple':
                self.display = SimpleDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'rich_terminal':
                if not is_rich_available():
                    print('⚠️  Rich library not available. Falling back to terminal display.')
                    print('   Install with: pip install rich')
                    self.display = TerminalDisplay(self.agent_ids, **self.config)
                else:
                    self.display = RichTerminalDisplay(self.agent_ids, **self.config)
            else:
                raise ValueError(f'Unknown display type: {self.display_type}')
        self.display.orchestrator = orchestrator
        log_filename = None
        if self.logger:
            context_info = f'(with {len(messages) // 2} previous exchanges)' if len(messages) > 1 else ''
            session_question = f'{question} {context_info}'
            log_filename = self.logger.initialize_session(session_question, self.agent_ids)
            monitoring = self.logger.get_monitoring_commands()
            print(f'📁 Real-time log: {log_filename}')
            print(f'💡 Monitor with: {monitoring['tail']}')
            print()
        self.display.initialize(question, log_filename)
        selected_agent = None
        vote_results = {}
        orchestrator_final_answer = None
        try:
            full_response = ''
            final_answer = ''
            async for chunk in orchestrator.chat(messages):
                content = getattr(chunk, 'content', '') or ''
                source = getattr(chunk, 'source', None)
                chunk_type = getattr(chunk, 'type', '')
                if chunk_type == 'agent_status':
                    status = getattr(chunk, 'status', None)
                    if source and status:
                        self.display.update_agent_status(source, status)
                    continue
                elif chunk_type == 'debug':
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type == 'mcp_status':
                    if source and source in self.agent_ids:
                        self.display.update_agent_content(source, content, 'tool')
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                    if source:
                        reasoning_content = ''
                        if chunk_type == 'reasoning':
                            reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                            if reasoning_delta:
                                reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                        elif chunk_type == 'reasoning_done':
                            reasoning_text = getattr(chunk, 'reasoning_text', '')
                            if reasoning_text:
                                reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                            else:
                                reasoning_content = '\n🧠 [Reasoning Complete]\n'
                            self._process_reasoning_content(chunk_type, reasoning_content, source)
                            reasoning_active_key = '_reasoning_active'
                            if hasattr(self, reasoning_active_key):
                                delattr(self, reasoning_active_key)
                        elif chunk_type == 'reasoning_summary':
                            summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                            if summary_delta:
                                reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                        elif chunk_type == 'reasoning_summary_done':
                            summary_text = getattr(chunk, 'reasoning_summary_text', '')
                            if summary_text:
                                reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                            self._process_reasoning_summary(chunk_type, '', source)
                            summary_active_key = f'_summary_active_{source}'
                            if hasattr(self, summary_active_key):
                                delattr(self, summary_active_key)
                        if reasoning_content:
                            self.display.update_agent_content(source, reasoning_content, 'thinking')
                            if self.logger:
                                self.logger.log_agent_content(source, reasoning_content, 'reasoning')
                    continue
                if chunk_type == 'status' and 'presenting final answer' in content:
                    for attr_name in list(vars(self).keys()):
                        if attr_name.startswith('_summary_active_'):
                            delattr(self, attr_name)
                if content:
                    full_response += content
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk.type)
                    await self._process_content(source, content)
            status = orchestrator.get_status()
            vote_results = status.get('vote_results', {})
            selected_agent = status.get('selected_agent')
            if selected_agent is None:
                selected_agent = ''
            if self.enable_final_presentation and selected_agent and vote_results.get('vote_counts'):
                presentation_content = ''
                try:
                    async for chunk in orchestrator.get_final_presentation(selected_agent, vote_results):
                        content = getattr(chunk, 'content', '') or ''
                        chunk_type = getattr(chunk, 'type', '')
                        if chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                            source = getattr(chunk, 'source', selected_agent)
                            reasoning_content = ''
                            if chunk_type == 'reasoning':
                                reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                                if reasoning_delta:
                                    reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                            elif chunk_type == 'reasoning_done':
                                reasoning_text = getattr(chunk, 'reasoning_text', '')
                                if reasoning_text:
                                    reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                                else:
                                    reasoning_content = '\n🧠 [Reasoning Complete]\n'
                                self._process_reasoning_content(chunk_type, reasoning_content, source)
                                reasoning_active_key = '_reasoning_active'
                                if hasattr(self, reasoning_active_key):
                                    delattr(self, reasoning_active_key)
                            elif chunk_type == 'reasoning_summary':
                                summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                                if summary_delta:
                                    reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                            elif chunk_type == 'reasoning_summary_done':
                                summary_text = getattr(chunk, 'reasoning_summary_text', '')
                                if summary_text:
                                    reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                                self._process_reasoning_summary(chunk_type, '', source)
                                summary_active_key = f'_summary_active_{source}'
                                if hasattr(self, summary_active_key):
                                    delattr(self, summary_active_key)
                            if reasoning_content:
                                content = reasoning_content
                        if content:
                            if isinstance(content, list):
                                content = ' '.join((str(item) for item in content))
                            elif not isinstance(content, str):
                                content = str(content)
                            presentation_content += content
                            if self.logger:
                                self.logger.log_chunk(selected_agent, content, getattr(chunk, 'type', 'presentation'))
                            await self._process_content(selected_agent, content)
                            if getattr(chunk, 'type', '') == 'done':
                                break
                except Exception:
                    presentation_content = full_response
                final_answer = presentation_content
                time.sleep(1.5)
            orchestrator_final_answer = None
            if selected_agent and hasattr(orchestrator, 'agent_states') and (selected_agent in orchestrator.agent_states):
                stored_answer = orchestrator.agent_states[selected_agent].answer
                if stored_answer:
                    orchestrator_final_answer = stored_answer.replace('\\', '\n').replace('**', '').strip()
            final_result = orchestrator_final_answer if orchestrator_final_answer else final_answer if final_answer else full_response
            if self.logger:
                session_info = self.logger.finalize_session(final_result if 'final_result' in locals() else final_answer if 'final_answer' in locals() else '', success=True)
                print(f'💾 Session log: {session_info['filename']}')
                print(f'⏱️  Duration: {session_info['duration']:.1f}s | Chunks: {session_info['total_chunks']} | Events: {session_info['orchestrator_events']}')
            return final_result
        except Exception:
            if self.logger:
                self.logger.finalize_session('', success=False)
            raise
        finally:
            if hasattr(self, '_answer_timeout_task') and self._answer_timeout_task:
                try:
                    await asyncio.wait_for(self._answer_timeout_task, timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                        await self._flush_final_answer()
                    self._answer_timeout_task.cancel()
            if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                await self._flush_final_answer()
            await asyncio.sleep(0.1)
            if self.display:
                self.display.cleanup()

    def _display_vote_results(self, vote_results: Dict[str, Any]):
        """Display voting results in a formatted table."""
        print('\n🗳️  VOTING RESULTS')
        print('=' * 50)
        vote_counts = vote_results.get('vote_counts', {})
        voter_details = vote_results.get('voter_details', {})
        winner = vote_results.get('winner')
        is_tie = vote_results.get('is_tie', False)
        if vote_counts:
            print('\n📊 Vote Count:')
            for agent_id, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True):
                winner_mark = '🏆' if agent_id == winner else '  '
                tie_mark = ' (tie-broken)' if is_tie and agent_id == winner else ''
                print(f'   {winner_mark} {agent_id}: {count} vote{('s' if count != 1 else '')}{tie_mark}')
        if voter_details:
            print('\n🔍 Vote Details:')
            for voted_for, voters in voter_details.items():
                print(f'   → {voted_for}:')
                for voter_info in voters:
                    voter = voter_info['voter']
                    reason = voter_info['reason']
                    print(f'     • {voter}: "{reason}"')
        if is_tie:
            print('\n⚖️  Tie broken by agent registration order (orchestrator setup order)')
        total_votes = vote_results.get('total_votes', 0)
        agents_voted = vote_results.get('agents_voted', 0)
        print(f'\n📈 Summary: {agents_voted}/{total_votes} agents voted')
        print('=' * 50)

    async def _process_content(self, source: Optional[str], content: str):
        """Process content from coordination stream."""
        if source in self.agent_ids:
            await self._process_agent_content(source, content)
        elif source in ['coordination_hub', 'orchestrator'] or source is None:
            await self._process_orchestrator_content(content)
        if any((marker in content for marker in ['✅', '🗳️', '🔄', '❌'])):
            clean_line = content.replace('**', '').replace('##', '').strip()
            if clean_line and (not any((skip in clean_line for skip in ['result ignored', 'Starting', 'Agents Coordinating', 'Coordinating agents, please wait']))):
                event = f'🔄 {source}: {clean_line}' if source and source not in ['coordination_hub', 'orchestrator'] else f'🔄 {clean_line}'
                self.display.add_orchestrator_event(event)
                if self.logger:
                    self.logger.log_orchestrator_event(event)

    async def _process_agent_content(self, agent_id: str, content: str):
        """Process content from a specific agent."""
        current_status = self.display.get_agent_status(agent_id)
        if current_status not in ['working', 'completed']:
            self.display.update_agent_status(agent_id, 'working')
        if '🔧' in content or '🔄 Vote invalid' in content:
            content_type = 'tool' if '🔧' in content else 'status'
            self.display.update_agent_content(agent_id, content, content_type)
            if 'new_answer' in content or 'vote' in content:
                self.display.update_agent_status(agent_id, 'completed')
            if self.logger:
                self.logger.log_agent_content(agent_id, content, content_type)
        else:
            self.display.update_agent_content(agent_id, content, 'thinking')
            if self.logger:
                self.logger.log_agent_content(agent_id, content, 'thinking')

    async def _flush_final_answer(self):
        """Flush the buffered final answer after a timeout to prevent duplicate calls."""
        if self._final_answer_shown or not self._answer_buffer.strip():
            return
        status = self.orchestrator.get_status()
        selected_agent = status.get('selected_agent', 'Unknown')
        vote_results = status.get('vote_results', {})
        self._final_answer_shown = True
        self.display.show_final_answer(self._answer_buffer.strip(), vote_results=vote_results, selected_agent=selected_agent)

    async def _process_orchestrator_content(self, content: str):
        """Process content from orchestrator."""
        if 'Final Coordinated Answer' in content:
            pass
        elif any((marker in content for marker in ['✅', '🗳️', '🔄', '❌', '⚠️'])):
            clean_line = content.replace('**', '').replace('##', '').strip()
            if clean_line and (not any((skip in clean_line for skip in ['result ignored', 'Starting', 'Agents Coordinating', 'Coordinating agents, please wait']))):
                event = f'🔄 {clean_line}'
                self.display.add_orchestrator_event(event)
                if self.logger:
                    self.logger.log_orchestrator_event(event)
        elif 'Final Coordinated Answer' not in content and (not any((marker in content for marker in ['✅', '🗳️', '🎯', 'Starting', 'Agents Coordinating', '🔄', '**', 'result ignored', 'restart pending']))):
            clean_content = content.strip()
            if clean_content and (not clean_content.startswith('---')) and (not clean_content.startswith('*Coordinated by')):
                if self._answer_buffer:
                    self._answer_buffer += ' ' + clean_content
                else:
                    self._answer_buffer = clean_content
                if self._answer_timeout_task:
                    self._answer_timeout_task.cancel()
                self._answer_timeout_task = asyncio.create_task(self._schedule_final_answer_flush())
                status = self.orchestrator.get_status()
                selected_agent = status.get('selected_agent', 'Unknown')
                vote_results = status.get('vote_results', {})
                vote_counts = vote_results.get('vote_counts', {})
                is_tie = vote_results.get('is_tie', False)
                if self._answer_buffer == clean_content:
                    orchestrator_timeout = getattr(self.orchestrator, 'is_orchestrator_timeout', False)
                    if selected_agent == 'Unknown' or selected_agent is None:
                        if orchestrator_timeout:
                            if vote_counts:
                                max_votes = max(vote_counts.values())
                                tied_agents = [agent for agent, count in vote_counts.items() if count == max_votes]
                                timeout_selected_agent = tied_agents[0] if tied_agents else None
                                if timeout_selected_agent:
                                    vote_summary = ', '.join([f'{agent}: {count}' for agent, count in vote_counts.items()])
                                    tie_info = ' (tie-broken by registration order)' if len(tied_agents) > 1 else ''
                                    event = f'🎯 FINAL: {timeout_selected_agent} selected from partial votes ({vote_summary}{tie_info}) → orchestrator timeout → [buffering...]'
                                else:
                                    event = '🎯 FINAL: None selected → orchestrator timeout (no agents completed voting in time) → [buffering...]'
                            else:
                                event = '🎯 FINAL: None selected → orchestrator timeout (no agents completed voting in time) → [buffering...]'
                        else:
                            event = '🎯 FINAL: None selected → [buffering...]'
                    elif vote_counts:
                        vote_summary = ', '.join([f'{agent}: {count} vote{('s' if count != 1 else '')}' for agent, count in vote_counts.items()])
                        tie_info = ' (tie-broken by registration order)' if is_tie else ''
                        timeout_info = ' (despite timeout)' if orchestrator_timeout else ''
                        event = f'🎯 FINAL: {selected_agent} selected ({vote_summary}{tie_info}){timeout_info} → [buffering...]'
                    else:
                        timeout_info = ' (despite timeout)' if orchestrator_timeout else ''
                        event = f'🎯 FINAL: {selected_agent} selected{timeout_info} → [buffering...]'
                    self.display.add_orchestrator_event(event)
                    if self.logger:
                        self.logger.log_orchestrator_event(event)

    async def _schedule_final_answer_flush(self):
        """Schedule the final answer flush after a delay to collect all chunks."""
        await asyncio.sleep(0.5)
        await self._flush_final_answer()

    def _print_with_flush(self, content: str):
        """Print content chunks directly without character-by-character flushing."""
        try:
            print(content, end='', flush=True)
        except Exception:
            print(content, end='', flush=True)

def _process_reasoning_summary(self, chunk_type: str, summary_delta: str, source: str) -> str:
    """Process reasoning summary content using display's shared logic."""
    if self.display and hasattr(self.display, 'process_reasoning_content'):
        return self.display.process_reasoning_content(chunk_type, summary_delta, source)
    else:
        if chunk_type == 'reasoning_summary':
            summary_active_key = f'_summary_active_{source}'
            if not getattr(self, summary_active_key, False):
                setattr(self, summary_active_key, True)
                return f'📋 [Reasoning Summary]\n{summary_delta}\n'
            return summary_delta
        elif chunk_type == 'reasoning_summary_done':
            summary_active_key = f'_summary_active_{source}'
            if hasattr(self, summary_active_key):
                setattr(self, summary_active_key, False)
        return summary_delta

def _process_reasoning_content(self, chunk_type: str, reasoning_delta: str, source: str) -> str:
    """Process reasoning summary content using display's shared logic."""
    if self.display and hasattr(self.display, 'process_reasoning_content'):
        return self.display.process_reasoning_content(chunk_type, reasoning_delta, source)
    elif chunk_type == 'reasoning':
        reasoning_active_key = f'_reasoning_active_{source}'
        if not getattr(self, reasoning_active_key, False):
            setattr(self, reasoning_active_key, True)
            return f'🧠 [Reasoning Started]\n{reasoning_delta}\n'
        return reasoning_delta
    elif chunk_type == 'reasoning_done':
        reasoning_active_key = f'_reasoning_active_{source}'
        if hasattr(self, reasoning_active_key):
            setattr(self, reasoning_active_key, False)
        return reasoning_delta

class RichTerminalDisplay(TerminalDisplay):
    """Enhanced terminal display using Rich library for beautiful formatting."""

    def __init__(self, agent_ids: List[str], **kwargs: Any) -> None:
        """Initialize rich terminal display.

        Args:
            agent_ids: List of agent IDs to display
            **kwargs: Additional configuration options
                - theme: Color theme ('dark', 'light', 'cyberpunk') (default: 'dark')
                - refresh_rate: Display refresh rate in Hz (default: 4)
                - enable_syntax_highlighting: Enable code syntax highlighting (default: True)
                - max_content_lines: Base lines per agent column before scrolling (default: 8)
                - show_timestamps: Show timestamps for events (default: True)
                - enable_status_jump: Enable jumping to latest status when agent status changes (default: True)
                - truncate_web_search_on_status_change: Truncate web search content when status changes (default: True)
                - max_web_search_lines_on_status_change: Max web search lines to keep on status changes (default: 3)
                - enable_flush_output: Enable flush output for final answer display (default: True)
                - flush_char_delay: Delay between characters in flush output (default: 0.03)
                - flush_word_delay: Extra delay after punctuation in flush output (default: 0.08)
        """
        if not RICH_AVAILABLE:
            raise ImportError('Rich library is required for RichTerminalDisplay. Install with: pip install rich')
        super().__init__(agent_ids, **kwargs)
        self._terminal_performance = self._detect_terminal_performance()
        self.refresh_rate = self._get_adaptive_refresh_rate(kwargs.get('refresh_rate'))
        self.theme = kwargs.get('theme', 'dark')
        self.enable_syntax_highlighting = kwargs.get('enable_syntax_highlighting', True)
        self.max_content_lines = kwargs.get('max_content_lines', 8)
        self.max_line_length = kwargs.get('max_line_length', 100)
        self.show_timestamps = kwargs.get('show_timestamps', True)
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.terminal_size = self.console.size
        self.num_agents = len(agent_ids)
        self.fixed_column_width = max(20, self.terminal_size.width // self.num_agents - 1)
        self.agent_panel_height = max(10, self.terminal_size.height - 13)
        self.orchestrator = kwargs.get('orchestrator', None)
        self._resize_lock = threading.Lock()
        self._setup_resize_handler()
        self.live = None
        self._lock = threading.RLock()
        self._last_update = 0
        self._update_interval = self._get_adaptive_update_interval()
        self._last_full_refresh = 0
        self._full_refresh_interval = self._get_adaptive_full_refresh_interval()
        self._refresh_times: List[float] = []
        self._dropped_frames = 0
        self._performance_check_interval = 5.0
        self._refresh_executor = ThreadPoolExecutor(max_workers=min(len(agent_ids) * 2 + 8, 20))
        self._agent_panels_cache: Dict[str, Panel] = {}
        self._header_cache = None
        self._footer_cache = None
        self._layout_update_lock = threading.Lock()
        self._pending_updates: set[str] = set()
        self._shutdown_flag = False
        self._priority_updates: set[str] = set()
        self._status_update_executor = ThreadPoolExecutor(max_workers=4)
        self._setup_theme()
        self._keyboard_interactive_mode = kwargs.get('keyboard_interactive_mode', True)
        self._safe_keyboard_mode = kwargs.get('safe_keyboard_mode', False)
        self._key_handler = None
        self._input_thread = None
        self._stop_input_thread = False
        self._original_settings = None
        self._agent_selector_active = False
        self._stored_final_presentation = None
        self._stored_presentation_agent = None
        self._stored_vote_results = None
        self._final_presentation_active = False
        self._final_presentation_content = ''
        self._final_presentation_agent = None
        self._final_presentation_vote_results = None
        self.code_patterns = ['```(\\w+)?\\n(.*?)\\n```', '`([^`]+)`', 'def\\s+\\w+\\s*\\(', 'class\\s+\\w+\\s*[:(\\s]', 'import\\s+\\w+', 'from\\s+\\w+\\s+import']
        self.agent_progress = {agent_id: 0 for agent_id in agent_ids}
        self.agent_activity = {agent_id: 'waiting' for agent_id in agent_ids}
        self._last_agent_status = {agent_id: 'waiting' for agent_id in agent_ids}
        self._last_agent_activity = {agent_id: 'waiting' for agent_id in agent_ids}
        self._last_content_hash = {agent_id: '' for agent_id in agent_ids}
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._debounce_delay = self._get_adaptive_debounce_delay()
        self._critical_updates: set[str] = set()
        self._normal_updates: set[str] = set()
        self._decorative_updates: set[str] = set()
        self._important_content_types = {'presentation', 'status', 'tool', 'error'}
        self._status_change_keywords = {'completed', 'failed', 'waiting', 'error', 'voted', 'voting', 'tool', 'vote recorded'}
        self._important_event_keywords = {'completed', 'failed', 'voting', 'voted', 'final', 'error', 'started', 'coordination', 'tool', 'vote recorded'}
        self._status_jump_enabled = kwargs.get('enable_status_jump', True)
        self._web_search_truncate_on_status_change = kwargs.get('truncate_web_search_on_status_change', True)
        self._max_web_search_lines = kwargs.get('max_web_search_lines_on_status_change', 3)
        self._enable_flush_output = kwargs.get('enable_flush_output', True)
        self._flush_char_delay = kwargs.get('flush_char_delay', 0.03)
        self._flush_word_delay = kwargs.get('flush_word_delay', 0.08)
        from massgen.logger_config import get_log_session_dir
        log_session_dir = get_log_session_dir()
        self.output_dir = kwargs.get('output_dir', log_session_dir / 'agent_outputs')
        self.agent_files: Dict[str, Path] = {}
        self.system_status_file = None
        self._selected_agent = None
        self._setup_agent_files()
        self._text_buffers = {agent_id: '' for agent_id in agent_ids}
        self._max_buffer_length = self._get_adaptive_buffer_length()
        self._buffer_timeout = self._get_adaptive_buffer_timeout()
        self._buffer_timers = {agent_id: None for agent_id in agent_ids}
        self._update_batch = set()
        self._batch_timer = None
        self._batch_timeout = self._get_adaptive_batch_timeout()

    def _setup_resize_handler(self) -> None:
        """Setup SIGWINCH signal handler for terminal resize detection."""
        if not sys.stdin.isatty():
            return
        try:
            signal.signal(signal.SIGWINCH, self._handle_resize_signal)
        except (AttributeError, OSError):
            pass

    def _handle_resize_signal(self, signum: int, frame: Any) -> None:
        """Handle SIGWINCH signal when terminal is resized."""
        threading.Thread(target=self._handle_terminal_resize, daemon=True).start()

    def _handle_terminal_resize(self) -> None:
        """Handle terminal resize by recalculating layout and refreshing display."""
        with self._resize_lock:
            try:
                if self._terminal_performance['type'] == 'vscode':
                    time.sleep(0.05)
                new_size = self.console.size
                if new_size.width != self.terminal_size.width or new_size.height != self.terminal_size.height:
                    self.terminal_size = new_size
                    if self._terminal_performance['type'] == 'vscode':
                        time.sleep(0.02)
                    self._recalculate_layout()
                    self._invalidate_display_cache()
                    with self._lock:
                        self._pending_updates.add('header')
                        self._pending_updates.add('footer')
                        self._pending_updates.update(self.agent_ids)
                        self._schedule_async_update(force_update=True)
                    time.sleep(0.1)
            except Exception:
                pass

    def _recalculate_layout(self) -> None:
        """Recalculate layout dimensions based on current terminal size."""
        self.fixed_column_width = max(20, self.terminal_size.width // self.num_agents - 1)
        self.agent_panel_height = max(10, self.terminal_size.height - 13)

    def _invalidate_display_cache(self) -> None:
        """Invalidate all cached display components to force refresh."""
        self._agent_panels_cache.clear()
        self._header_cache = None
        self._footer_cache = None

    def _setup_agent_files(self) -> None:
        """Setup individual txt files for each agent and system status file."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        for agent_id in self.agent_ids:
            file_path = Path(self.output_dir) / f'{agent_id}.txt'
            self.agent_files[agent_id] = file_path
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'=== {agent_id.upper()} OUTPUT LOG ===\n\n')
        self.system_status_file = Path(self.output_dir) / 'system_status.txt'
        with open(str(self.system_status_file), 'w', encoding='utf-8') as f:
            f.write('=== SYSTEM STATUS LOG ===\n\n')

    def _detect_terminal_performance(self) -> Dict[str, Any]:
        """Detect terminal performance characteristics for adaptive refresh rates."""
        terminal_info = {'type': 'unknown', 'performance_tier': 'medium', 'supports_unicode': True, 'supports_color': True, 'buffer_size': 'normal'}
        try:
            term = os.environ.get('TERM', '').lower()
            term_program = os.environ.get('TERM_PROGRAM', '').lower()
            if 'iterm.app' in term_program or 'iterm' in term_program.lower():
                terminal_info['performance_tier'] = 'high'
                terminal_info['type'] = 'iterm'
                terminal_info['supports_unicode'] = True
            elif 'vscode' in term_program or 'code' in term_program or self._detect_vscode_terminal():
                terminal_info['performance_tier'] = 'medium'
                terminal_info['type'] = 'vscode'
                terminal_info['supports_unicode'] = True
                terminal_info['buffer_size'] = 'large'
                terminal_info['needs_flush_delay'] = True
                terminal_info['refresh_stabilization'] = True
            elif 'apple_terminal' in term_program or term_program == 'terminal':
                terminal_info['performance_tier'] = 'high'
                terminal_info['type'] = 'macos_terminal'
                terminal_info['supports_unicode'] = True
            elif 'xterm-256color' in term or 'alacritty' in term_program:
                terminal_info['performance_tier'] = 'high'
                terminal_info['type'] = 'modern'
            elif 'screen' in term or 'tmux' in term:
                terminal_info['performance_tier'] = 'low'
                terminal_info['type'] = 'multiplexer'
            elif 'xterm' in term:
                terminal_info['performance_tier'] = 'medium'
                terminal_info['type'] = 'xterm'
            elif term in ['dumb', 'vt100', 'vt220']:
                terminal_info['performance_tier'] = 'low'
                terminal_info['type'] = 'legacy'
                terminal_info['supports_unicode'] = False
            if os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_CLIENT'):
                if terminal_info['performance_tier'] == 'high':
                    terminal_info['performance_tier'] = 'medium'
                elif terminal_info['performance_tier'] == 'medium':
                    terminal_info['performance_tier'] = 'low'
            colorterm = os.environ.get('COLORTERM', '').lower()
            if colorterm in ['truecolor', '24bit']:
                terminal_info['supports_color'] = True
            elif not self.console.is_terminal or term == 'dumb':
                terminal_info['supports_color'] = False
        except Exception:
            terminal_info['performance_tier'] = 'low'
        return terminal_info

    def _detect_vscode_terminal(self) -> bool:
        """Additional VSCode terminal detection using multiple indicators."""
        try:
            vscode_indicators = ['VSCODE_INJECTION', 'VSCODE_PID', 'VSCODE_IPC_HOOK', 'VSCODE_IPC_HOOK_CLI', 'TERM_PROGRAM_VERSION']
            for indicator in vscode_indicators:
                if os.environ.get(indicator):
                    return True
            try:
                import psutil
                current_process = psutil.Process()
                parent = current_process.parent()
                if parent and ('code' in parent.name().lower() or 'vscode' in parent.name().lower()):
                    return True
            except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            term_program = os.environ.get('TERM_PROGRAM', '').lower()
            if term_program and any((pattern in term_program for pattern in ['code', 'vscode'])):
                return True
            return False
        except Exception:
            return False

    def _get_adaptive_refresh_rate(self, user_override: Optional[int]=None) -> int:
        """Get adaptive refresh rate based on terminal performance."""
        if user_override is not None:
            return user_override
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        if term_type == 'vscode':
            return 2
        refresh_rates = {'high': 10, 'medium': 5, 'low': 2}
        return refresh_rates.get(perf_tier, 8)

    def _get_adaptive_update_interval(self) -> float:
        """Get adaptive update interval based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        intervals = {'high': 0.02, 'medium': 0.05, 'low': 0.1}
        return intervals.get(perf_tier, 0.05)

    def _get_adaptive_full_refresh_interval(self) -> float:
        """Get adaptive full refresh interval based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        intervals = {'high': 0.1, 'medium': 0.2, 'low': 0.5}
        return intervals.get(perf_tier, 0.2)

    def _get_adaptive_debounce_delay(self) -> float:
        """Get adaptive debounce delay based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        delays = {'high': 0.01, 'medium': 0.03, 'low': 0.05}
        base_delay = delays.get(perf_tier, 0.03)
        if term_type in ['iterm', 'macos_terminal']:
            base_delay *= 2.0
        return base_delay

    def _get_adaptive_buffer_length(self) -> int:
        """Get adaptive buffer length based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        lengths = {'high': 800, 'medium': 500, 'low': 200}
        base_length = lengths.get(perf_tier, 500)
        if term_type in ['iterm', 'macos_terminal']:
            base_length = min(base_length, 400)
        return base_length

    def _get_adaptive_buffer_timeout(self) -> float:
        """Get adaptive buffer timeout based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        timeouts = {'high': 0.5, 'medium': 1.0, 'low': 2.0}
        base_timeout = timeouts.get(perf_tier, 1.0)
        if term_type in ['iterm', 'macos_terminal']:
            base_timeout *= 1.5
        return base_timeout

    def _get_adaptive_batch_timeout(self) -> float:
        """Get adaptive batch timeout for update batching."""
        perf_tier = self._terminal_performance['performance_tier']
        timeouts = {'high': 0.05, 'medium': 0.1, 'low': 0.2}
        return timeouts.get(perf_tier, 0.1)

    def _monitor_performance(self) -> None:
        """Monitor refresh performance and adjust if needed."""
        time.time()
        if len(self._refresh_times) > 20:
            self._refresh_times = self._refresh_times[-20:]
        if len(self._refresh_times) >= 5:
            avg_refresh_time = sum(self._refresh_times) / len(self._refresh_times)
            expected_refresh_time = 1.0 / self.refresh_rate
            if avg_refresh_time > expected_refresh_time * 2:
                self._dropped_frames += 1
                if self._dropped_frames >= 3:
                    self.refresh_rate = max(2, int(self.refresh_rate * 0.7))
                    self._dropped_frames = 0
                    self._update_interval = 1.0 / self.refresh_rate
                    self._full_refresh_interval *= 1.5
                    if self.live and self.live.is_started:
                        try:
                            self.live.refresh_per_second = self.refresh_rate
                        except Exception:
                            self._fallback_to_simple_display()

    def _create_live_display_with_fallback(self) -> Optional[Live]:
        """Create Live display with terminal compatibility checks and fallback."""
        try:
            if not self._test_terminal_capabilities():
                self._fallback_to_simple_display()
                return None
            live_settings = self._get_adaptive_live_settings()
            live = Live(self._create_layout(), console=self.console, **live_settings)
            try:
                live.start()
                live.stop()
                return live
            except Exception:
                self._fallback_to_simple_display()
                return None
        except Exception:
            self._fallback_to_simple_display()
            return None

    def _test_terminal_capabilities(self) -> bool:
        """Test if terminal supports rich Live display features."""
        try:
            if not self.console.is_terminal:
                return False
            perf_tier = self._terminal_performance['performance_tier']
            term_type = self._terminal_performance['type']
            if term_type == 'legacy' or perf_tier == 'low':
                term = os.environ.get('TERM', '').lower()
                if term in ['dumb', 'vt100']:
                    return False
            if term_type in ['iterm', 'macos_terminal']:
                return True
            test_size = self.console.size
            if test_size.width < 20 or test_size.height < 10:
                return False
            return True
        except Exception:
            return False

    def _get_adaptive_live_settings(self) -> Dict[str, Any]:
        """Get Live display settings adapted to terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        settings = {'refresh_per_second': self.refresh_rate, 'vertical_overflow': 'ellipsis', 'transient': False}
        if perf_tier == 'low':
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 3)
            settings['transient'] = True
        elif perf_tier == 'medium':
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 8)
        if self._terminal_performance['type'] == 'multiplexer':
            settings['auto_refresh'] = False
        if self._terminal_performance['type'] in ['iterm', 'macos_terminal']:
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 5)
            settings['transient'] = False
            settings['vertical_overflow'] = 'ellipsis'
        if self._terminal_performance['type'] == 'vscode':
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 6)
            settings['transient'] = False
            settings['vertical_overflow'] = 'ellipsis'
            settings['auto_refresh'] = True
        return settings

    def _fallback_to_simple_display(self) -> None:
        """Fallback to simple console output when Live display is not supported."""
        self._simple_display_mode = True
        try:
            self.console.print('\n[yellow]Terminal compatibility: Using simple display mode[/yellow]')
            self.console.print(f'[dim]Monitoring {len(self.agent_ids)} agents...[/dim]\n')
        except Exception:
            print('\nUsing simple display mode...')
            print(f'Monitoring {len(self.agent_ids)} agents...\n')
        return None

    def _update_display_safe(self) -> None:
        """Safely update display with fallback support and terminal-specific synchronization."""
        term_type = self._terminal_performance['type']
        use_safe_mode = term_type in ['iterm', 'macos_terminal', 'vscode']
        if term_type == 'vscode' and self._terminal_performance.get('refresh_stabilization'):
            time.sleep(0.01)
        try:
            if use_safe_mode:
                with self._layout_update_lock:
                    with self._lock:
                        if hasattr(self, '_simple_display_mode') and self._simple_display_mode:
                            self._update_simple_display()
                        else:
                            self._update_live_display_safe()
            else:
                with self._layout_update_lock:
                    if hasattr(self, '_simple_display_mode') and self._simple_display_mode:
                        self._update_simple_display()
                    else:
                        self._update_live_display()
        except Exception:
            self._fallback_to_simple_display()
        if term_type == 'vscode' and self._terminal_performance.get('needs_flush_delay'):
            time.sleep(0.005)

    def _update_simple_display(self) -> None:
        """Update display in simple mode without Live."""
        try:
            current_time = time.time()
            if not hasattr(self, '_last_simple_update'):
                self._last_simple_update = 0
            if current_time - self._last_simple_update > 2.0:
                status_line = f'[{time.strftime('%H:%M:%S')}] Agents: '
                for agent_id in self.agent_ids:
                    status = self.agent_status.get(agent_id, 'waiting')
                    status_line += f'{agent_id}:{status} '
                try:
                    self.console.print(f'\r{status_line[:80]}', end='')
                except Exception:
                    print(f'\r{status_line[:80]}', end='')
                self._last_simple_update = current_time
        except Exception:
            pass

    def _update_live_display(self) -> None:
        """Update Live display mode."""
        try:
            if self.live:
                self.live.update(self._create_layout())
        except Exception:
            self._fallback_to_simple_display()

    def _update_live_display_safe(self) -> None:
        """Update Live display mode with extra safety for macOS terminals."""
        try:
            if self.live and self.live.is_started:
                import time
                time.sleep(0.001)
                self.live.update(self._create_layout())
            elif self.live:
                try:
                    self.live.start()
                    self.live.update(self._create_layout())
                except Exception:
                    self._fallback_to_simple_display()
        except Exception:
            self._fallback_to_simple_display()

    def _setup_theme(self) -> None:
        """Setup color theme configuration."""
        unified_colors = {'primary': '#0066CC', 'secondary': '#4A90E2', 'success': '#00AA44', 'warning': '#CC6600', 'error': '#CC0000', 'info': '#6633CC', 'text': 'default', 'border': '#4A90E2', 'panel_style': '#4A90E2', 'header_style': 'bold #0066CC'}
        themes = {'dark': unified_colors.copy(), 'light': unified_colors.copy(), 'cyberpunk': {'primary': 'bright_magenta', 'secondary': 'bright_cyan', 'success': 'bright_green', 'warning': 'bright_yellow', 'error': 'bright_red', 'info': 'bright_blue', 'text': 'bright_white', 'border': 'bright_magenta', 'panel_style': 'bright_magenta', 'header_style': 'bold bright_magenta'}}
        self.colors = themes.get(self.theme, themes['dark'])
        if self._terminal_performance['type'] == 'vscode':
            vscode_adjustments = {'primary': '#0066CC', 'secondary': '#4A90E2', 'border': '#4A90E2', 'panel_style': '#4A90E2'}
            self.colors.update(vscode_adjustments)
            self._setup_vscode_emoji_fallbacks()

    def _setup_vscode_emoji_fallbacks(self) -> None:
        """Setup emoji fallbacks for VSCode terminal compatibility."""
        self._emoji_fallbacks = {'🚀': '>>', '🎯': '>', '💭': '...', '⚡': '!', '🎨': '*', '📝': '=', '✅': '[OK]', '❌': '[X]', '⭐': '*', '🔍': '?', '📊': '|'}
        if not self._terminal_performance.get('supports_unicode', True):
            self._use_emoji_fallbacks = True
        else:
            self._use_emoji_fallbacks = False

    def _safe_emoji(self, emoji: str) -> str:
        """Get safe emoji for current terminal, with VSCode fallbacks."""
        if self._terminal_performance['type'] == 'vscode' and self._use_emoji_fallbacks and (emoji in self._emoji_fallbacks):
            return self._emoji_fallbacks[emoji]
        return emoji

    def initialize(self, question: str, log_filename: Optional[str]=None) -> None:
        """Initialize the rich display with question and optional log file."""
        self.log_filename = log_filename
        self.question = question
        self.console.clear()
        from massgen.logger_config import suppress_console_logging
        suppress_console_logging()
        self._create_initial_display()
        if self._keyboard_interactive_mode:
            self._setup_keyboard_handler()
        self.live = self._create_live_display_with_fallback()
        if self.live:
            self.live.start()
        self._write_system_status()

    def _create_initial_display(self) -> None:
        """Create the initial welcome display."""
        welcome_text = Text()
        welcome_text.append('🚀 MassGen Coordination Dashboard 🚀\n', style=self.colors['header_style'])
        welcome_text.append(f'Multi-Agent System with {len(self.agent_ids)} agents\n', style=self.colors['primary'])
        if self.log_filename:
            welcome_text.append(f'📁 Log: {self.log_filename}\n', style=self.colors['info'])
        welcome_text.append(f'🎨 Theme: {self.theme.title()}', style=self.colors['secondary'])
        welcome_panel = Panel(welcome_text, box=DOUBLE, border_style=self.colors['border'], title='[bold]Welcome[/bold]', title_align='center')
        self.console.print(welcome_panel)
        self.console.print()

    def _create_layout(self) -> Layout:
        """Create the main layout structure with cached components."""
        layout = Layout()
        header = self._header_cache if self._header_cache else self._create_header()
        agent_columns = self._create_agent_columns_from_cache()
        footer = self._footer_cache if self._footer_cache else self._create_footer()
        if self._final_presentation_active:
            presentation_panel = self._create_final_presentation_panel()
            layout.split_column(Layout(presentation_panel, name='presentation'), Layout(footer, name='footer', size=8))
        else:
            layout.split_column(Layout(header, name='header', size=5), Layout(agent_columns, name='main'), Layout(footer, name='footer', size=8))
        return layout

    def _create_agent_columns_from_cache(self) -> Columns:
        """Create agent columns using cached panels with fixed widths."""
        agent_panels = []
        for agent_id in self.agent_ids:
            if agent_id in self._agent_panels_cache:
                agent_panels.append(self._agent_panels_cache[agent_id])
            else:
                panel = self._create_agent_panel(agent_id)
                self._agent_panels_cache[agent_id] = panel
                agent_panels.append(panel)
        return Columns(agent_panels, equal=False, expand=False, width=self.fixed_column_width)

    def _create_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append('🚀 MassGen Multi-Agent Coordination System', style=self.colors['header_style'])
        if hasattr(self, 'question'):
            header_text.append(f'\n💡 Question: {self.question}', style=self.colors['info'])
        return Panel(Align.center(header_text), box=ROUNDED, border_style=self.colors['border'], height=5)

    def _create_agent_columns(self) -> Columns:
        """Create columns for each agent with fixed widths."""
        agent_panels = []
        for agent_id in self.agent_ids:
            panel = self._create_agent_panel(agent_id)
            agent_panels.append(panel)
        return Columns(agent_panels, equal=False, expand=False, width=self.fixed_column_width)

    def _setup_keyboard_handler(self) -> None:
        """Setup keyboard handler for interactive agent selection."""
        try:
            self._agent_keys = {}
            for i, agent_id in enumerate(self.agent_ids):
                key = str(i + 1)
                self._agent_keys[key] = agent_id
            if self._keyboard_interactive_mode:
                self._start_input_thread()
        except ImportError:
            self._keyboard_interactive_mode = False

    def _start_input_thread(self) -> None:
        """Start background thread for keyboard input during Live mode."""
        if not sys.stdin.isatty():
            return
        self._stop_input_thread = False
        term_type = self._terminal_performance['type']
        if self._safe_keyboard_mode or term_type in ['iterm', 'macos_terminal']:
            self._input_thread = threading.Thread(target=self._input_thread_worker_safe, daemon=True)
            self._input_thread.start()
        else:
            try:
                self._input_thread = threading.Thread(target=self._input_thread_worker_improved, daemon=True)
                self._input_thread.start()
            except Exception:
                self._input_thread = threading.Thread(target=self._input_thread_worker_fallback, daemon=True)
                self._input_thread.start()

    def _input_thread_worker_improved(self) -> None:
        """Improved background thread worker that doesn't interfere with Rich rendering."""
        if not UNIX_TERMINAL_SUPPORT:
            return self._input_thread_worker_fallback()
        try:
            if sys.stdin.isatty():
                self._original_settings = termios.tcgetattr(sys.stdin.fileno())
                new_settings = termios.tcgetattr(sys.stdin.fileno())
                new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
                new_settings[6][termios.VMIN] = 0
                new_settings[6][termios.VTIME] = 1
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_settings)
            while not self._stop_input_thread:
                try:
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        char = sys.stdin.read(1)
                        if char:
                            self._handle_key_press(char)
                except (BlockingIOError, OSError):
                    continue
        except (KeyboardInterrupt, EOFError):
            pass
        except Exception:
            pass
        finally:
            self._restore_terminal_settings()

    def _input_thread_worker_fallback(self) -> None:
        """Fallback keyboard input method using simple polling without terminal mode changes."""
        import time
        self.console.print('\n[dim]Keyboard support active. Press keys during Live display:[/dim]')
        self.console.print("[dim]1-{} to open agent files, 's' for system status, 'q' to quit[/dim]\n".format(len(self.agent_ids)))
        try:
            while not self._stop_input_thread:
                time.sleep(0.1)
        except (KeyboardInterrupt, EOFError):
            pass
        except Exception:
            pass

    def _input_thread_worker_safe(self) -> None:
        """Completely safe keyboard input that never changes terminal settings."""
        try:
            while not self._stop_input_thread:
                time.sleep(0.5)
        except Exception:
            pass

    def _restore_terminal_settings(self) -> None:
        """Restore original terminal settings."""
        try:
            if UNIX_TERMINAL_SUPPORT and sys.stdin.isatty():
                if self._original_settings:
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
                    self._original_settings = None
                else:
                    try:
                        current = termios.tcgetattr(sys.stdin.fileno())
                        current[3] = current[3] | termios.ECHO | termios.ICANON
                        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, current)
                    except Exception:
                        pass
        except Exception:
            pass

    def _ensure_clean_keyboard_state(self) -> None:
        """Ensure clean keyboard state before starting agent selector."""
        self._stop_input_thread = True
        if self._input_thread and self._input_thread.is_alive():
            try:
                self._input_thread.join(timeout=0.5)
            except Exception:
                pass
        self._restore_terminal_settings()
        try:
            if UNIX_TERMINAL_SUPPORT and sys.stdin.isatty():
                termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass
        import time
        time.sleep(0.1)

    def _handle_key_press(self, key: str) -> None:
        """Handle key press events for agent selection."""
        if key in self._agent_keys:
            agent_id = self._agent_keys[key]
            self._open_agent_in_default_text_editor(agent_id)
        elif key == 's':
            self._open_system_status_in_default_text_editor()
        elif key == 'f':
            self._open_final_presentation_in_default_text_editor()
        elif key == 'q':
            self._stop_input_thread = True
            self._restore_terminal_settings()

    def _open_agent_in_default_text_editor(self, agent_id: str) -> None:
        """Open agent's txt file in default text editor."""
        if agent_id not in self.agent_files:
            return
        file_path = self.agent_files[agent_id]
        if not file_path.exists():
            return
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(file_path)], check=False)
            elif sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(file_path)], check=False)
            elif sys.platform == 'win32':
                subprocess.run(['start', str(file_path)], check=False, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_agent_in_external_app(agent_id)

    def _open_agent_in_vscode_new_window(self, agent_id: str) -> None:
        """Open agent's txt file in a new VS Code window."""
        if agent_id not in self.agent_files:
            return
        file_path = self.agent_files[agent_id]
        if not file_path.exists():
            return
        try:
            subprocess.run(['code', '--new-window', str(file_path)], check=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_agent_in_external_app(agent_id)

    def _open_system_status_in_default_text_editor(self) -> None:
        """Open system status file in default text editor."""
        if not self.system_status_file or not self.system_status_file.exists():
            return
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(self.system_status_file)], check=False)
            elif sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(self.system_status_file)], check=False)
            elif sys.platform == 'win32':
                subprocess.run(['start', str(self.system_status_file)], check=False, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_system_status_in_external_app()

    def _open_final_presentation_in_default_text_editor(self) -> None:
        """Open final presentation file in default text editor."""
        final_presentation_file = None
        if hasattr(self, '_final_presentation_file_path') and self._final_presentation_file_path:
            final_presentation_file = self._final_presentation_file_path
        elif hasattr(self, '_stored_presentation_agent') and self._stored_presentation_agent:
            agent_name = self._stored_presentation_agent
            final_presentation_file = self.output_dir / f'{agent_name}_final_presentation.txt'
        else:
            return
        if not final_presentation_file.exists():
            return
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(final_presentation_file)], check=False)
            elif sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(final_presentation_file)], check=False)
            elif sys.platform == 'win32':
                subprocess.run(['start', str(final_presentation_file)], check=False, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    def _open_system_status_in_vscode_new_window(self) -> None:
        """Open system status file in a new VS Code window."""
        if not self.system_status_file or not self.system_status_file.exists():
            return
        try:
            subprocess.run(['code', '--new-window', str(self.system_status_file)], check=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_system_status_in_external_app()

    def _open_agent_in_external_app(self, agent_id: str) -> None:
        """Open agent's txt file in external editor or terminal viewer."""
        if agent_id not in self.agent_files:
            return
        file_path = self.agent_files[agent_id]
        if not file_path.exists():
            return
        try:
            if sys.platform == 'darwin':
                editors = ['code', 'subl', 'atom', 'nano', 'vim', 'open']
                for editor in editors:
                    try:
                        if editor == 'open':
                            subprocess.run(['open', '-a', 'TextEdit', str(file_path)], check=False)
                        else:
                            subprocess.run([editor, str(file_path)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform.startswith('linux'):
                editors = ['code', 'gedit', 'kate', 'nano', 'vim', 'xdg-open']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(file_path)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform == 'win32':
                editors = ['code', 'notepad++', 'notepad']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(file_path)], check=False, shell=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
        except Exception:
            pass

    def _open_system_status_in_external_app(self) -> None:
        """Open system status file in external editor or terminal viewer."""
        if not self.system_status_file or not self.system_status_file.exists():
            return
        try:
            if sys.platform == 'darwin':
                editors = ['code', 'subl', 'atom', 'nano', 'vim', 'open']
                for editor in editors:
                    try:
                        if editor == 'open':
                            subprocess.run(['open', '-a', 'TextEdit', str(self.system_status_file)], check=False)
                        else:
                            subprocess.run([editor, str(self.system_status_file)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform.startswith('linux'):
                editors = ['code', 'gedit', 'kate', 'nano', 'vim', 'xdg-open']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(self.system_status_file)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform == 'win32':
                editors = ['code', 'notepad++', 'notepad']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(self.system_status_file)], check=False, shell=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
        except Exception:
            pass

    def _show_agent_full_content(self, agent_id: str) -> None:
        """Display full content of selected agent from txt file."""
        if agent_id not in self.agent_files:
            return
        try:
            file_path = self.agent_files[agent_id]
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '[' in content:
                        content = content.replace('[', '\\[')
                self.console.print('\n' + '=' * 80 + '\n')
                header_text = Text()
                header_text.append(f'📄 {agent_id.upper()} - Full Content', style=self.colors['header_style'])
                header_text.append('\nPress any key to return to main view', style=self.colors['info'])
                header_panel = Panel(header_text, box=DOUBLE, border_style=self.colors['border'])
                content_panel = Panel(content, title=f'[bold]{agent_id.upper()} Output[/bold]', border_style=self.colors['border'], box=ROUNDED)
                self.console.print(header_panel)
                self.console.print(content_panel)
                input('Press Enter to return to agent selector...')
                self.console.print('\n' + '=' * 80 + '\n')
        except Exception:
            pass

    def show_agent_selector(self) -> None:
        """Show agent selector and handle user input."""
        if not self._keyboard_interactive_mode or not hasattr(self, '_agent_keys'):
            return
        if self._agent_selector_active:
            return
        self._agent_selector_active = True
        self._ensure_clean_keyboard_state()
        try:
            loop_count = 0
            while True:
                loop_count += 1
                options_text = Text()
                options_text.append("This is a system inspection interface for diving into the multi-agent collaboration behind the scenes in MassGen. It lets you examine each agent's original output and compare it to the final MassGen answer in terms of quality. You can explore the detailed communication, collaboration, voting, and decision-making process.\n", style=self.colors['text'])
                options_text.append('\n🎮 Select an agent to view full output:\n', style=self.colors['primary'])
                for key, agent_id in self._agent_keys.items():
                    options_text.append(f'  {key}: ', style=self.colors['warning'])
                    options_text.append('Inspect the original answer and working log of agent ', style=self.colors['text'])
                    options_text.append(f'{agent_id}\n', style=self.colors['warning'])
                options_text.append('  s: Inspect the orchestrator working log including the voting process\n', style=self.colors['warning'])
                options_text.append('  r: Display coordination table to see the full history of agent interactions and decisions\n', style=self.colors['warning'])
                if self._stored_final_presentation and self._stored_presentation_agent:
                    options_text.append(f'  f: Show final presentation from Selected Agent ({self._stored_presentation_agent})\n', style=self.colors['success'])
                options_text.append('  q: Quit Inspection\n', style=self.colors['info'])
                self.console.print(Panel(options_text, title='[bold]Agent Selector[/bold]', border_style=self.colors['border']))
                try:
                    choice = input('Enter your choice: ').strip().lower()
                    if choice in self._agent_keys:
                        self._show_agent_full_content(self._agent_keys[choice])
                    elif choice == 's':
                        self._show_system_status()
                    elif choice == 'r':
                        self.display_coordination_table()
                    elif choice == 'f' and self._stored_final_presentation:
                        self._redisplay_final_presentation()
                    elif choice == 'q':
                        break
                    else:
                        self.console.print(f'[{self.colors['error']}]Invalid choice. Please try again.[/{self.colors['error']}]')
                except KeyboardInterrupt:
                    break
        finally:
            self._agent_selector_active = True

    def _redisplay_final_presentation(self) -> None:
        """Redisplay the stored final presentation."""
        if not self._stored_final_presentation or not self._stored_presentation_agent:
            self.console.print(f'[{self.colors['error']}]No final presentation stored.[/{self.colors['error']}]')
            return
        self.console.print('\n' + '=' * 80 + '\n')
        self._display_final_presentation_content(self._stored_presentation_agent, self._stored_final_presentation)
        input('\nPress Enter to return to agent selector...')
        self.console.print('\n' + '=' * 80 + '\n')

    def _show_coordination_rounds_table(self) -> None:
        """Display the coordination rounds table with rich formatting."""
        self.display_coordination_table()

    def _show_system_status(self) -> None:
        """Display system status from txt file."""
        if not self.system_status_file or not self.system_status_file.exists():
            self.console.print(f'[{self.colors['error']}]System status file not found.[/{self.colors['error']}]')
            return
        try:
            with open(self.system_status_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '[' in content:
                    content = content.replace('[', '\\[')
            self.console.print('\n' + '=' * 80 + '\n')
            header_text = Text()
            header_text.append('📊 SYSTEM STATUS - Full Log', style=self.colors['header_style'])
            header_text.append('\nPress any key to return to agent selector', style=self.colors['info'])
            header_panel = Panel(header_text, box=DOUBLE, border_style=self.colors['border'])
            content_panel = Panel(content, title='[bold]System Status Log[/bold]', border_style=self.colors['border'], box=ROUNDED)
            self.console.print(header_panel)
            self.console.print(content_panel)
            input('Press Enter to return to agent selector...')
            self.console.print('\n' + '=' * 80 + '\n')
        except Exception as e:
            self.console.print(f'[{self.colors['error']}]Error reading system status file: {e}[/{self.colors['error']}]')

    def _create_agent_panel(self, agent_id: str) -> Panel:
        """Create a panel for a specific agent."""
        agent_content = self.agent_outputs.get(agent_id, [])
        status = self.agent_status.get(agent_id, 'waiting')
        activity = self.agent_activity.get(agent_id, 'waiting')
        content_text = Text()
        max_lines = max(0, self.agent_panel_height - 3)
        if not agent_content:
            content_text.append('No activity yet...', style=self.colors['text'])
        else:
            for line in agent_content[-max_lines:]:
                formatted_line = self._format_content_line(line)
                content_text.append(formatted_line)
                content_text.append('\n')
        status_emoji = self._get_status_emoji(status, activity)
        status_color = self._get_status_color(status)
        backend_name = self._get_backend_name(agent_id)
        title = f'{status_emoji} {agent_id.upper()}'
        if backend_name != 'Unknown':
            title += f' ({backend_name})'
        if self._keyboard_interactive_mode and hasattr(self, '_agent_keys'):
            agent_key = next((k for k, v in self._agent_keys.items() if v == agent_id), None)
            if agent_key:
                title += f' [Press {agent_key}]'
        return Panel(content_text, title=f'[{status_color}]{title}[/{status_color}]', border_style=status_color, box=ROUNDED, height=self.agent_panel_height, width=self.fixed_column_width)

    def _format_content_line(self, line: str) -> Text:
        """Format a content line with syntax highlighting and styling."""
        formatted = Text()
        if not line.strip():
            return formatted
        if self._is_web_search_content(line):
            return self._format_web_search_line(line)
        is_error_message = any((error_indicator in line for error_indicator in ['❌ Error:', 'Error:', 'Exception:', 'Traceback', '❌']))
        if len(line) > self.max_line_length and (not is_error_message):
            wrapped_lines = []
            remaining = line
            while len(remaining) > self.max_line_length:
                break_point = remaining[:self.max_line_length].rfind(' ')
                if break_point == -1:
                    break_point = self.max_line_length
                wrapped_lines.append(remaining[:break_point])
                remaining = remaining[break_point:].lstrip()
            if remaining:
                wrapped_lines.append(remaining)
            line = '\n'.join(wrapped_lines)
        if line.startswith('→'):
            formatted.append('→ ', style=self.colors['warning'])
            formatted.append(line[2:], style=self.colors['text'])
        elif line.startswith('🎤'):
            formatted.append('🎤 ', style=self.colors['success'])
            formatted.append(line[3:], style=f'bold {self.colors['success']}')
        elif line.startswith('⚡'):
            formatted.append('⚡ ', style=self.colors['warning'])
            if 'jumped to latest' in line:
                formatted.append(line[3:], style=f'bold {self.colors['info']}')
            else:
                formatted.append(line[3:], style=f'italic {self.colors['warning']}')
        elif self._is_code_content(line):
            if self.enable_syntax_highlighting:
                formatted = self._apply_syntax_highlighting(line)
            else:
                formatted.append(line, style=f'bold {self.colors['info']}')
        else:
            formatted.append(line, style=self.colors['text'])
        return formatted

    def _create_final_presentation_panel(self) -> Panel:
        """Create a panel for the final presentation display."""
        if not self._final_presentation_active:
            return None
        content_text = Text()
        if not self._final_presentation_content:
            content_text.append('No activity yet...', style=self.colors['text'])
        else:
            lines = self._final_presentation_content.split('\n')
            available_height = max(10, self.terminal_size.height - 16)
            display_lines = lines[-available_height:] if len(lines) > available_height else lines
            for line in display_lines:
                if line.strip():
                    formatted_line = self._format_content_line(line)
                    content_text.append(formatted_line)
                content_text.append('\n')
        title = f'🎤 Final Presentation from {self._final_presentation_agent}'
        if self._final_presentation_vote_results and self._final_presentation_vote_results.get('vote_counts'):
            vote_count = self._final_presentation_vote_results['vote_counts'].get(self._final_presentation_agent, 0)
            title += f' (Selected with {vote_count} votes)'
        title += ' [Press f]'
        return Panel(content_text, title=f'[{self.colors['success']}]{title}[/{self.colors['success']}]', border_style=self.colors['success'], box=DOUBLE, expand=True)

    def _format_presentation_content(self, content: str) -> Text:
        """Format presentation content with enhanced styling for orchestrator queries."""
        formatted = Text()
        lines = content.split('\n') if '\n' in content else [content]
        for line in lines:
            if not line.strip():
                formatted.append('\n')
                continue
            if line.startswith('**') and line.endswith('**'):
                clean_line = line.strip('*').strip()
                formatted.append(clean_line, style=f'bold {self.colors['success']}')
            elif line.startswith('- ') or line.startswith('• '):
                formatted.append(line[:2], style=self.colors['primary'])
                formatted.append(line[2:], style=self.colors['text'])
            elif line.startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                clean_header = line.lstrip('# ').strip()
                if header_level <= 2:
                    formatted.append(clean_header, style=f'bold {self.colors['header_style']}')
                else:
                    formatted.append(clean_header, style=f'bold {self.colors['primary']}')
            elif self._is_code_content(line):
                if self.enable_syntax_highlighting:
                    formatted.append(self._apply_syntax_highlighting(line))
                else:
                    formatted.append(line, style=f'bold {self.colors['info']}')
            else:
                formatted.append(line, style=self.colors['text'])
            if line != lines[-1]:
                formatted.append('\n')
        return formatted

    def _is_web_search_content(self, line: str) -> bool:
        """Check if content is from web search and needs special formatting."""
        web_search_indicators = ['[Provider Tool: Web Search]', '🔍 [Search Query]', '✅ [Provider Tool: Web Search]', '🔍 [Provider Tool: Web Search]']
        return any((indicator in line for indicator in web_search_indicators))

    def _format_web_search_line(self, line: str) -> Text:
        """Format web search content with better truncation and styling."""
        formatted = Text()
        if '[Provider Tool: Web Search] Starting search' in line:
            formatted.append('🔍 ', style=self.colors['info'])
            formatted.append('Web search starting...', style=self.colors['text'])
        elif '[Provider Tool: Web Search] Searching' in line:
            formatted.append('🔍 ', style=self.colors['warning'])
            formatted.append('Searching...', style=self.colors['text'])
        elif '[Provider Tool: Web Search] Search completed' in line:
            formatted.append('✅ ', style=self.colors['success'])
            formatted.append('Search completed', style=self.colors['text'])
        elif any((pattern in line for pattern in ['🔍 [Search Query]', 'Search Query:', '[Search Query]'])):
            query = None
            patterns = [('🔍 [Search Query]', ''), ('[Search Query]', ''), ('Search Query:', ''), ('Query:', '')]
            for pattern, _ in patterns:
                if pattern in line:
                    parts = line.split(pattern, 1)
                    if len(parts) > 1:
                        query = parts[1].strip().strip('\'"').strip()
                        break
            if query:
                formatted.append('🔍 Search: ', style=self.colors['info'])
                formatted.append(f'"{query}"', style=f'italic {self.colors['text']}')
            else:
                formatted.append('🔍 Search query', style=self.colors['info'])
        else:
            max_web_length = min(self.max_line_length // 2, 60)
            if len(line) > max_web_length:
                truncated = line[:max_web_length]
                for break_char in ['. ', '! ', '? ', ', ', ': ']:
                    last_break = truncated.rfind(break_char)
                    if last_break > max_web_length // 2:
                        truncated = truncated[:last_break + 1]
                        break
                line = truncated + '...'
            formatted.append(line, style=self.colors['text'])
        return formatted

    def _should_filter_content(self, content: str, content_type: str) -> bool:
        """Determine if content should be filtered out to reduce noise."""
        if content_type in ['status', 'presentation', 'error']:
            return False
        if len(content) > 1000 and self._is_web_search_content(content):
            url_count = content.count('http')
            technical_indicators = content.count('[') + content.count(']') + content.count('(') + content.count(')')
            if url_count > 5 or technical_indicators > len(content) * 0.1:
                return True
        return False

    def _should_filter_line(self, line: str) -> bool:
        """Determine if a specific line should be filtered out."""
        filter_patterns = ['^\\s*\\([^)]+\\)\\s*$', '^\\s*\\[[^\\]]+\\]\\s*$', '^\\s*https?://\\S+\\s*$', '^\\s*\\.\\.\\.\\s*$']
        for pattern in filter_patterns:
            if re.match(pattern, line):
                return True
        return False

    def _truncate_web_search_content(self, agent_id: str) -> None:
        """Truncate web search content when important status updates occur."""
        if agent_id not in self.agent_outputs or not self.agent_outputs[agent_id]:
            return
        content_lines = self.agent_outputs[agent_id]
        web_search_lines = []
        non_web_search_lines = []
        for line in content_lines:
            if self._is_web_search_content(line):
                web_search_lines.append(line)
            else:
                non_web_search_lines.append(line)
        if len(web_search_lines) > self._max_web_search_lines:
            truncated_web_search = web_search_lines[:1] + ['🔍 ... (web search content truncated due to status update) ...'] + web_search_lines[-(self._max_web_search_lines - 2):]
            recent_non_web = non_web_search_lines[-max(5, self.max_content_lines - len(truncated_web_search)):]
            self.agent_outputs[agent_id] = recent_non_web + truncated_web_search
        if len(web_search_lines) > self._max_web_search_lines:
            self.agent_outputs[agent_id].append('⚡  Status updated - jumped to latest')

    def _is_code_content(self, content: str) -> bool:
        """Check if content appears to be code."""
        for pattern in self.code_patterns:
            if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                return True
        return False

    def _apply_syntax_highlighting(self, content: str) -> Text:
        """Apply syntax highlighting to content."""
        try:
            language = self._detect_language(content)
            if language:
                return Text(content, style=f'bold {self.colors['info']}')
            else:
                return Text(content, style=f'bold {self.colors['info']}')
        except Exception:
            return Text(content, style=f'bold {self.colors['info']}')

    def _detect_language(self, content: str) -> Optional[str]:
        """Detect programming language from content."""
        content_lower = content.lower()
        if any((keyword in content_lower for keyword in ['def ', 'import ', 'class ', 'python'])):
            return 'python'
        elif any((keyword in content_lower for keyword in ['function', 'var ', 'let ', 'const '])):
            return 'javascript'
        elif any((keyword in content_lower for keyword in ['<', '>', 'html', 'div'])):
            return 'html'
        elif any((keyword in content_lower for keyword in ['{', '}', 'json'])):
            return 'json'
        return None

    def _get_status_emoji(self, status: str, activity: str) -> str:
        """Get emoji for agent status."""
        if status == 'working':
            return '🔄'
        elif status == 'completed':
            if 'voted' in activity.lower():
                return '🗳️'
            elif 'failed' in activity.lower():
                return '❌'
            else:
                return '✅'
        elif status == 'waiting':
            return '⏳'
        else:
            return '❓'

    def _get_status_color(self, status: str) -> str:
        """Get color for agent status."""
        status_colors = {'working': self.colors['warning'], 'completed': self.colors['success'], 'waiting': self.colors['info'], 'failed': self.colors['error']}
        return status_colors.get(status, self.colors['text'])

    def _get_backend_name(self, agent_id: str) -> str:
        """Get backend name for agent."""
        try:
            if hasattr(self, 'orchestrator') and self.orchestrator and hasattr(self.orchestrator, 'agents'):
                agent = self.orchestrator.agents.get(agent_id)
                if agent and hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                    return agent.backend.get_provider_name()
        except Exception:
            pass
        return 'Unknown'

    def _create_footer(self) -> Panel:
        """Create the footer panel with status and events."""
        footer_content = Text()
        footer_content.append('📊 Agent Status: ', style=self.colors['primary'])
        status_counts = {}
        for status in self.agent_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        status_parts = []
        for status, count in status_counts.items():
            emoji = self._get_status_emoji(status, status)
            status_parts.append(f'{emoji} {status.title()}: {count}')
        if self._final_presentation_active:
            status_parts.append('🎤 Final Presentation: Active')
        elif hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
            status_parts.append('🎤 Final Presentation: Complete')
        footer_content.append(' | '.join(status_parts), style=self.colors['text'])
        footer_content.append('\n')
        if self.orchestrator_events:
            footer_content.append('📋 Recent Events:\n', style=self.colors['primary'])
            recent_events = self.orchestrator_events[-3:]
            for event in recent_events:
                footer_content.append(f'  • {event}\n', style=self.colors['text'])
        if self.log_filename:
            footer_content.append(f'📁 Log: {self.log_filename}\n', style=self.colors['info'])
        if self._keyboard_interactive_mode and hasattr(self, '_agent_keys'):
            if self._safe_keyboard_mode:
                footer_content.append('📂 Safe Mode: Keyboard disabled to prevent rendering issues\n', style=self.colors['warning'])
                footer_content.append(f'Output files saved in: {self.output_dir}/', style=self.colors['info'])
            else:
                footer_content.append('🎮 Live Mode Hotkeys: Press 1-', style=self.colors['primary'])
                hotkeys = f"{len(self.agent_ids)} to open agent files in editor, 's' for system status"
                if hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
                    hotkeys += ", 'f' for final presentation"
                footer_content.append(hotkeys, style=self.colors['text'])
                footer_content.append(f'\n📂 Output files saved in: {self.output_dir}/', style=self.colors['info'])
        return Panel(footer_content, title='[bold]System Status [Press s][/bold]', border_style=self.colors['border'], box=ROUNDED)

    def update_agent_content(self, agent_id: str, content: str, content_type: str='thinking') -> None:
        """Update content for a specific agent with rich formatting and file output."""
        if agent_id not in self.agent_ids:
            return
        with self._lock:
            if agent_id not in self.agent_outputs:
                self.agent_outputs[agent_id] = []
            self._write_to_agent_file(agent_id, content, content_type)
            is_status_change = content_type in ['status', 'presentation', 'tool'] or any((keyword in content.lower() for keyword in self._status_change_keywords))
            if self._status_jump_enabled and is_status_change and self._web_search_truncate_on_status_change and self.agent_outputs[agent_id]:
                self._truncate_web_search_content(agent_id)
            if self._should_filter_content(content, content_type):
                return
            self._process_content_with_buffering(agent_id, content, content_type)
            self._categorize_update(agent_id, content_type, content)
            is_critical = content_type in ['tool', 'status', 'presentation', 'error'] or any((keyword in content.lower() for keyword in self._status_change_keywords))
            self._schedule_layered_update(agent_id, is_critical)

    def _process_content_with_buffering(self, agent_id: str, content: str, content_type: str) -> None:
        """Process content with buffering to accumulate text chunks."""
        if self._buffer_timers.get(agent_id):
            self._buffer_timers[agent_id].cancel()
            self._buffer_timers[agent_id] = None
        if content_type in ['tool', 'status', 'presentation', 'error'] or '\n' in content:
            self._flush_buffer(agent_id)
            if '\n' in content:
                for line in content.splitlines():
                    if line.strip() and (not self._should_filter_line(line)):
                        self.agent_outputs[agent_id].append(line)
            elif content.strip():
                self.agent_outputs[agent_id].append(content.strip())
            return
        self._text_buffers[agent_id] += content
        buffer = self._text_buffers[agent_id]
        if len(buffer) >= self._max_buffer_length:
            self._flush_buffer(agent_id)
            return
        self._set_buffer_timer(agent_id)

    def _flush_buffer(self, agent_id: str) -> None:
        """Flush the buffer for a specific agent."""
        if agent_id in self._text_buffers and self._text_buffers[agent_id]:
            buffer_content = self._text_buffers[agent_id].strip()
            if buffer_content:
                self.agent_outputs[agent_id].append(buffer_content)
            self._text_buffers[agent_id] = ''
        if self._buffer_timers.get(agent_id):
            self._buffer_timers[agent_id].cancel()
            self._buffer_timers[agent_id] = None

    def _set_buffer_timer(self, agent_id: str) -> None:
        """Set a timer to flush the buffer after a timeout."""
        if self._shutdown_flag:
            return
        if self._buffer_timers.get(agent_id):
            self._buffer_timers[agent_id].cancel()

        def timeout_flush() -> None:
            with self._lock:
                if agent_id in self._text_buffers and self._text_buffers[agent_id]:
                    self._flush_buffer(agent_id)
                    self._pending_updates.add(agent_id)
                    self._schedule_async_update(force_update=True)
        self._buffer_timers[agent_id] = threading.Timer(self._buffer_timeout, timeout_flush)
        self._buffer_timers[agent_id].start()

    def _write_to_agent_file(self, agent_id: str, content: str, content_type: str) -> None:
        """Write content to agent's individual txt file."""
        if agent_id not in self.agent_files:
            return
        if content_type == 'debug':
            return
        try:
            file_path = self.agent_files[agent_id]
            timestamp = time.strftime('%H:%M:%S')
            has_emoji = any((ord(char) > 127 and ord(char) in range(128512, 128591) or ord(char) in range(127744, 128511) or ord(char) in range(128640, 128767) or (ord(char) in range(9728, 9983)) or (ord(char) in range(9984, 10175)) for char in content))
            if has_emoji:
                formatted_content = f'\n[{timestamp}] {content}\n'
            else:
                formatted_content = f'{content}'
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(formatted_content)
        except Exception:
            pass

    def _write_system_status(self) -> None:
        """Write current system status to system status file - shows orchestrator events chronologically by time."""
        if not self.system_status_file:
            return
        try:
            with open(self.system_status_file, 'w', encoding='utf-8') as f:
                f.write('=== SYSTEM STATUS LOG ===\n\n')
                f.write('📊 Agent Status:\n')
                status_counts = {}
                for status in self.agent_status.values():
                    status_counts[status] = status_counts.get(status, 0) + 1
                for status, count in status_counts.items():
                    emoji = self._get_status_emoji(status, status)
                    f.write(f'  {emoji} {status.title()}: {count}\n')
                if self._final_presentation_active:
                    f.write('  🎤 Final Presentation: Active\n')
                elif hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
                    f.write('  🎤 Final Presentation: Complete\n')
                f.write('\n')
                f.write('📋 Orchestrator Events:\n')
                if self.orchestrator_events:
                    for event in self.orchestrator_events:
                        f.write(f'  • {event}\n')
                else:
                    f.write('  • No orchestrator events yet\n')
                f.write('\n')
        except Exception:
            pass

    def update_agent_status(self, agent_id: str, status: str) -> None:
        """Update status for a specific agent with rich indicators."""
        if agent_id not in self.agent_ids:
            return
        with self._lock:
            old_status = self.agent_status.get(agent_id, 'waiting')
            last_tracked_status = self._last_agent_status.get(agent_id, 'waiting')
            current_activity = self.agent_activity.get(agent_id, '')
            is_vote_status = 'voted' in status.lower() or 'voted' in current_activity.lower()
            should_update = old_status != status and last_tracked_status != status or is_vote_status
            if should_update:
                if self._status_jump_enabled and self._web_search_truncate_on_status_change and (old_status != status) and (agent_id in self.agent_outputs) and self.agent_outputs[agent_id]:
                    self._truncate_web_search_content(agent_id)
                super().update_agent_status(agent_id, status)
                self._last_agent_status[agent_id] = status
                self._priority_updates.add(agent_id)
                self._pending_updates.add(agent_id)
                self._pending_updates.add('footer')
                self._schedule_priority_update(agent_id)
                self._schedule_async_update(force_update=True)
                self._write_system_status()
            elif old_status != status:
                super().update_agent_status(agent_id, status)

    def add_orchestrator_event(self, event: str) -> None:
        """Add an orchestrator coordination event with timestamp."""
        with self._lock:
            if self.show_timestamps:
                timestamp = time.strftime('%H:%M:%S')
                formatted_event = f'[{timestamp}] {event}'
            else:
                formatted_event = event
            if hasattr(self, 'orchestrator_events') and self.orchestrator_events and (self.orchestrator_events[-1] == formatted_event):
                return
            super().add_orchestrator_event(formatted_event)
            if any((keyword in event.lower() for keyword in self._important_event_keywords)):
                self._pending_updates.add('footer')
                self._schedule_async_update(force_update=True)
                self._write_system_status()

    def display_vote_results(self, vote_results: Dict[str, Any]) -> None:
        """Display voting results in a formatted rich panel."""
        if not vote_results or not vote_results.get('vote_counts'):
            return
        self.live is not None
        if self.live:
            self.live.stop()
            self.live = None
        vote_counts = vote_results.get('vote_counts', {})
        voter_details = vote_results.get('voter_details', {})
        winner = vote_results.get('winner')
        is_tie = vote_results.get('is_tie', False)
        vote_content = Text()
        vote_content.append('📊 Vote Count:\n', style=self.colors['primary'])
        for agent_id, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True):
            winner_mark = '🏆' if agent_id == winner else '  '
            tie_mark = ' (tie-broken)' if is_tie and agent_id == winner else ''
            vote_content.append(f'   {winner_mark} {agent_id}: {count} vote{('s' if count != 1 else '')}{tie_mark}\n', style=self.colors['success'] if agent_id == winner else self.colors['text'])
        if voter_details:
            vote_content.append('\n🔍 Vote Details:\n', style=self.colors['primary'])
            for voted_for, voters in voter_details.items():
                vote_content.append(f'   → {voted_for}:\n', style=self.colors['info'])
                for voter_info in voters:
                    voter = voter_info['voter']
                    reason = voter_info['reason']
                    vote_content.append(f'     • {voter}: "{reason}"\n', style=self.colors['text'])
        agent_mapping = vote_results.get('agent_mapping', {})
        if agent_mapping:
            vote_content.append('\n🔀 Agent Mapping:\n', style=self.colors['primary'])
            for anon_id, real_id in sorted(agent_mapping.items()):
                vote_content.append(f'   {anon_id} → {real_id}\n', style=self.colors['info'])
        if is_tie:
            vote_content.append('\n⚖️  Tie broken by agent registration order\n', style=self.colors['warning'])
        total_votes = vote_results.get('total_votes', 0)
        agents_voted = vote_results.get('agents_voted', 0)
        vote_content.append(f'\n📈 Summary: {agents_voted}/{total_votes} agents voted', style=self.colors['info'])
        voting_panel = Panel(vote_content, title='[bold bright_cyan]🗳️  VOTING RESULTS[/bold bright_cyan]', border_style=self.colors['primary'], box=DOUBLE, expand=False)
        self.console.print(voting_panel)

    def display_coordination_table(self) -> None:
        """Display the coordination table showing the full coordination flow."""
        try:
            self.live is not None
            if self.live:
                self.live.stop()
                self.live = None
            if not hasattr(self, 'orchestrator') or not self.orchestrator:
                print('No orchestrator available for table generation')
                return
            tracker = getattr(self.orchestrator, 'coordination_tracker', None)
            if not tracker:
                print('No coordination tracker available')
                return
            events_data = [event.to_dict() for event in tracker.events]
            session_data = {'session_metadata': {'user_prompt': tracker.user_prompt, 'agent_ids': tracker.agent_ids, 'start_time': tracker.start_time, 'end_time': tracker.end_time, 'final_winner': tracker.final_winner}, 'events': events_data}
            from massgen.frontend.displays.create_coordination_table import CoordinationTableBuilder
            builder = CoordinationTableBuilder(session_data)
            result = builder.generate_rich_event_table()
            if result:
                legend, rich_table = result
                from rich.console import Console
                from rich.panel import Panel
                from rich.text import Text
                from massgen.frontend.displays.create_coordination_table import display_scrollable_content_macos, display_with_native_pager, get_optimal_display_method
                temp_console = Console()
                content = []
                title_text = Text()
                title_text.append('📊 COORDINATION TABLE', style='bold bright_green')
                title_text.append('\n\nNavigation: ↑/↓ or j/k to scroll, q to quit', style='dim cyan')
                title_panel = Panel(title_text, border_style='bright_blue', padding=(1, 2))
                content.append(title_panel)
                content.append('')
                content.append(rich_table)
                if legend:
                    content.append('')
                    content.append('')
                    content.append(legend)
                display_method = get_optimal_display_method()
                try:
                    if display_method == 'macos_simple':
                        display_scrollable_content_macos(temp_console, content, '📊 COORDINATION TABLE')
                    elif display_method == 'native_pager':
                        display_with_native_pager(temp_console, content, '📊 COORDINATION TABLE')
                    else:
                        with temp_console.pager(styles=True):
                            for item in content:
                                temp_console.print(item)
                except (KeyboardInterrupt, EOFError):
                    pass
                self.console.print('\n' + '=' * 80 + '\n')
            else:
                table_content = builder.generate_event_table()
                table_panel = Panel(table_content, title='[bold bright_green]📊 COORDINATION TABLE[/bold bright_green]', border_style=self.colors['success'], box=DOUBLE, expand=False)
                self.console.print('\n')
                self.console.print(table_panel)
                self.console.print()
        except Exception as e:
            print(f'Error displaying coordination table: {e}')
            import traceback
            traceback.print_exc()

    async def display_final_presentation(self, selected_agent: str, presentation_stream: Any, vote_results: Optional[Dict[str, Any]]=None) -> None:
        """Display final presentation with streaming box followed by clean final answer box."""
        if not selected_agent:
            return ''
        self._final_presentation_active = True
        self._final_presentation_content = ''
        self._final_presentation_agent = selected_agent
        self._final_presentation_vote_results = vote_results
        self._final_presentation_file_path = None
        self.console.print('\n')
        was_live = self.live is not None and self.live.is_started
        if not was_live:
            self.console.clear()
            self.live = Live(self._create_layout(), console=self.console, refresh_per_second=self.refresh_rate, vertical_overflow='ellipsis', transient=False)
            self.live.start()
        self._update_footer_cache()
        self._update_final_presentation_panel()
        presentation_content = ''
        chunk_count = 0
        presentation_file_path = self._initialize_final_presentation_file(selected_agent)
        self._final_presentation_file_path = presentation_file_path
        try:
            async for chunk in presentation_stream:
                chunk_count += 1
                content = getattr(chunk, 'content', '') or ''
                chunk_type = getattr(chunk, 'type', '')
                source = getattr(chunk, 'source', selected_agent)
                if chunk_type == 'debug':
                    continue
                if content:
                    if isinstance(content, list):
                        content = ' '.join((str(item) for item in content))
                    elif not isinstance(content, str):
                        content = str(content)
                    processed_content = self.process_reasoning_content(chunk_type, content, source)
                    self._final_presentation_content += processed_content
                    presentation_content += processed_content
                    if processed_content.strip():
                        truncated_content = processed_content.strip()[:150]
                        if len(processed_content.strip()) > 150:
                            truncated_content += '...'
                        self.add_orchestrator_event(f'🎤 {selected_agent}: {truncated_content}')
                    self._append_to_final_presentation_file(presentation_file_path, processed_content)
                    self._update_final_presentation_panel()
                else:
                    processed_content = self.process_reasoning_content(chunk_type, '', source)
                    if processed_content:
                        self._final_presentation_content += processed_content
                        presentation_content += processed_content
                        self._append_to_final_presentation_file(presentation_file_path, processed_content)
                        self._update_final_presentation_panel()
                if chunk_type == 'done':
                    break
        except Exception as e:
            error_msg = f'\n❌ Error during final presentation: {e}\n'
            self._final_presentation_content += error_msg
            self._update_final_presentation_panel()
            if hasattr(self, 'orchestrator') and self.orchestrator:
                try:
                    status = self.orchestrator.get_status()
                    if selected_agent in status.get('agent_states', {}):
                        stored_answer = status['agent_states'][selected_agent].get('answer', '')
                        if stored_answer:
                            fallback_msg = f'\n📋 Fallback to stored answer:\n{stored_answer}\n'
                            self._final_presentation_content += fallback_msg
                            presentation_content = stored_answer
                            self._update_final_presentation_panel()
                except Exception:
                    pass
        if presentation_content:
            self._stored_final_presentation = presentation_content
            self._stored_presentation_agent = selected_agent
            self._stored_vote_results = vote_results
            self._update_footer_cache()
        self._finalize_final_presentation_file(presentation_file_path)
        if self.live and self.live.is_started:
            self.live.stop()
            self.live = None
        self._final_presentation_active = False
        self._update_footer_cache()
        stats_text = Text()
        stats_text.append('✅ Presentation completed by ', style='bold green')
        stats_text.append(selected_agent, style=f'bold {self.colors['success']}')
        if chunk_count > 0:
            stats_text.append(f' | 📊 {chunk_count} chunks processed', style='dim')
        summary_panel = Panel(stats_text, border_style='green', box=ROUNDED, expand=True)
        self.console.print(summary_panel)
        return presentation_content

    def _format_multiline_content(self, content: str) -> Text:
        """Format multiline content for display in a panel."""
        formatted = Text()
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                formatted_line = self._format_content_line(line)
                formatted.append(formatted_line)
            formatted.append('\n')
        return formatted

    def show_final_answer(self, answer: str, vote_results: Dict[str, Any]=None, selected_agent: str=None):
        """Display the final coordinated answer prominently with voting results, final presentation, and agent selector."""
        with self._lock:
            self._flush_all_buffers()
        if self.live:
            self.live.stop()
            self.live = None
        if vote_results is None or selected_agent is None:
            try:
                if hasattr(self, 'orchestrator') and self.orchestrator:
                    status = self.orchestrator.get_status()
                    vote_results = vote_results or status.get('vote_results', {})
                    selected_agent = selected_agent or status.get('selected_agent')
            except Exception:
                pass
        with self._lock:
            for agent_id in self.agent_ids:
                self._pending_updates.add(agent_id)
            self._pending_updates.add('footer')
            self._schedule_async_update(force_update=True)
        time.sleep(0.5)
        self._force_display_final_vote_statuses()
        time.sleep(0.5)
        if vote_results and vote_results.get('vote_counts'):
            self.display_vote_results(vote_results)
            time.sleep(1.0)
        if selected_agent:
            selected_agent_text = Text(f'🏆 Selected agent: {selected_agent}', style=self.colors['success'])
        else:
            is_timeout = False
            if hasattr(self, 'orchestrator') and self.orchestrator:
                is_timeout = getattr(self.orchestrator, 'is_orchestrator_timeout', False)
            if is_timeout:
                selected_agent_text = Text()
                selected_agent_text.append('No agent selected\n', style=self.colors['warning'])
                selected_agent_text.append('The orchestrator timed out before any agent could complete voting or provide an answer.', style=self.colors['warning'])
            else:
                selected_agent_text = Text('No agent selected', style=self.colors['warning'])
        final_panel = Panel(Align.center(selected_agent_text), title='[bold bright_green]🎯 FINAL COORDINATED ANSWER[/bold bright_green]', border_style=self.colors['success'], box=DOUBLE, expand=False)
        self.console.print(final_panel)
        if selected_agent:
            selection_text = Text()
            selection_text.append(f'✅ Selected by: {selected_agent}', style=self.colors['success'])
            if vote_results and vote_results.get('vote_counts'):
                vote_summary = ', '.join([f'{agent}: {count}' for agent, count in vote_results['vote_counts'].items()])
                selection_text.append(f'\n🗳️ Vote results: {vote_summary}', style=self.colors['info'])
            selection_panel = Panel(selection_text, border_style=self.colors['info'], box=ROUNDED)
            self.console.print(selection_panel)
        if selected_agent and hasattr(self, 'orchestrator') and self.orchestrator:
            try:
                self._show_orchestrator_final_presentation(selected_agent, vote_results)
                time.sleep(1.0)
            except Exception as e:
                error_text = Text(f'❌ Error getting final presentation: {e}', style=self.colors['error'])
                self.console.print(error_text)
        if self._keyboard_interactive_mode and hasattr(self, '_agent_keys') and (not self._safe_keyboard_mode):
            self.show_agent_selector()

    def _display_answer_with_flush(self, answer: str) -> None:
        """Display answer with flush output effect - streaming character by character."""
        import sys
        import time
        char_delay = self._flush_char_delay
        word_delay = self._flush_word_delay
        line_delay = 0.2
        try:
            lines = answer.split('\n')
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    self.console.print()
                    continue
                for i, char in enumerate(line):
                    styled_char = Text(char, style=self.colors['text'])
                    self.console.print(styled_char, end='', highlight=False)
                    sys.stdout.flush()
                    if char in [' ', ',', ';']:
                        time.sleep(word_delay)
                    elif char in ['.', '!', '?', ':']:
                        time.sleep(word_delay * 2)
                    else:
                        time.sleep(char_delay)
                if line_idx < len(lines) - 1:
                    self.console.print()
                    time.sleep(line_delay)
            self.console.print()
        except KeyboardInterrupt:
            self.console.print(f'\n{Text(answer, style=self.colors['text'])}')
        except Exception:
            self.console.print(Text(answer, style=self.colors['text']))

    def _get_selected_agent_final_answer(self, selected_agent: str) -> str:
        """Get the final provided answer from the selected agent."""
        if not selected_agent:
            return ''
        try:
            if hasattr(self, 'orchestrator') and self.orchestrator:
                status = self.orchestrator.get_status()
                if hasattr(self.orchestrator, 'agent_states') and selected_agent in self.orchestrator.agent_states:
                    stored_answer = self.orchestrator.agent_states[selected_agent].answer
                    if stored_answer:
                        return stored_answer.replace('\\', '\n').replace('**', '').strip()
                if 'agent_states' in status and selected_agent in status['agent_states']:
                    agent_state = status['agent_states'][selected_agent]
                    if hasattr(agent_state, 'answer') and agent_state.answer:
                        return agent_state.answer.replace('\\', '\n').replace('**', '').strip()
                    elif isinstance(agent_state, dict) and 'answer' in agent_state:
                        return agent_state['answer'].replace('\\', '\n').replace('**', '').strip()
        except Exception:
            pass
        if selected_agent not in self.agent_outputs:
            return ''
        agent_output = self.agent_outputs[selected_agent]
        if not agent_output:
            return ''
        answer_lines = []
        for line in reversed(agent_output):
            line = line.strip()
            if not line:
                continue
            if any((marker in line for marker in ['⚡', '🔄', '✅', '🗳️', '❌', 'voted', '🔧', 'status'])):
                continue
            if any((marker in line.lower() for marker in ['final coordinated', 'coordination', 'voting'])):
                break
            answer_lines.insert(0, line)
            if len(answer_lines) >= 10 or len('\n'.join(answer_lines)) > 500:
                break
        if answer_lines:
            answer = '\n'.join(answer_lines).strip()
            answer = answer.replace('**', '').replace('##', '').strip()
            return answer
        return ''

    def _extract_presentation_content(self, selected_agent: str) -> str:
        """Extract presentation content from the selected agent's output."""
        if selected_agent not in self.agent_outputs:
            return ''
        agent_output = self.agent_outputs[selected_agent]
        presentation_lines = []
        collecting_presentation = False
        for line in agent_output:
            if '🎤' in line or 'presentation' in line.lower():
                collecting_presentation = True
                continue
            if not line.strip() or line.startswith('⚡') or line.startswith('🔄'):
                continue
            if collecting_presentation and line.strip():
                if any((marker in line for marker in ['✅', '🗳️', '🔄', '❌', 'voted', 'Final', 'coordination'])):
                    break
                presentation_lines.append(line.strip())
        if not presentation_lines and agent_output:
            for line in reversed(agent_output[-10:]):
                if line.strip() and (not line.startswith('⚡')) and (not line.startswith('🔄')) and (not any((marker in line for marker in ['voted', '🗳️', '✅', 'status']))):
                    presentation_lines.insert(0, line.strip())
                    if len(presentation_lines) >= 5:
                        break
        return '\n'.join(presentation_lines) if presentation_lines else ''

    def _display_final_presentation_content(self, selected_agent: str, presentation_content: str) -> None:
        """Display the final presentation content in a formatted panel with orchestrator query enhancements."""
        if not presentation_content.strip():
            return
        self._stored_final_presentation = presentation_content
        self._stored_presentation_agent = selected_agent
        header_text = Text()
        header_text.append(f'🎤 Final Presentation from {selected_agent}', style=self.colors['header_style'])
        header_panel = Panel(Align.center(header_text), border_style=self.colors['success'], box=DOUBLE, title='[bold]Final Presentation[/bold]')
        self.console.print(header_panel)
        self.console.print('=' * 60)
        content_text = Text()
        formatted_content = self._format_presentation_content(presentation_content)
        content_text.append(formatted_content)
        content_panel = Panel(content_text, title=f'[bold]{selected_agent.upper()} Final Presentation[/bold]', border_style=self.colors['primary'], box=ROUNDED, subtitle='[italic]Final presentation content[/italic]')
        self.console.print(content_panel)
        self.console.print('=' * 60)
        completion_text = Text()
        completion_text.append('✅ Final presentation completed successfully', style=self.colors['success'])
        completion_panel = Panel(Align.center(completion_text), border_style=self.colors['success'], box=ROUNDED)
        self.console.print(completion_panel)
        self._save_final_presentation_to_file(selected_agent, presentation_content)

    def _save_final_presentation_to_file(self, selected_agent: str, presentation_content: str) -> None:
        """Save the final presentation content to a text file in agent_outputs directory."""
        try:
            filename = f'final_presentation_{selected_agent}.txt'
            file_path = Path(self.output_dir) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'=== FINAL PRESENTATION FROM {selected_agent.upper()} ===\n')
                f.write(f'Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 60 + '\n\n')
                f.write(presentation_content)
                f.write('\n\n' + '=' * 60 + '\n')
                f.write('End of Final Presentation\n')
            latest_link = Path(self.output_dir) / f'final_presentation_{selected_agent}_latest.txt'
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(filename)
        except Exception:
            pass

    def _initialize_final_presentation_file(self, selected_agent: str) -> Path:
        """Initialize a new final presentation file and return the file path."""
        try:
            filename = f'final_presentation_{selected_agent}.txt'
            file_path = Path(self.output_dir) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'=== FINAL PRESENTATION FROM {selected_agent.upper()} ===\n')
                f.write(f'Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 60 + '\n\n')
            latest_link = Path(self.output_dir) / f'final_presentation_{selected_agent}_latest.txt'
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(filename)
            return file_path
        except Exception:
            return None

    def _append_to_final_presentation_file(self, file_path: Path, content: str) -> None:
        """Append content to the final presentation file."""
        try:
            if file_path and file_path.exists():
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    import os
                    os.fsync(f.fileno())
        except Exception:
            pass

    def _finalize_final_presentation_file(self, file_path: Path) -> None:
        """Add closing content to the final presentation file."""
        try:
            if file_path and file_path.exists():
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + '=' * 60 + '\n')
                    f.write('End of Final Presentation\n')
        except Exception:
            pass

    def _show_orchestrator_final_presentation(self, selected_agent: str, vote_results: Dict[str, Any]=None) -> None:
        """Show the final presentation from the orchestrator for the selected agent."""
        import time
        try:
            if not hasattr(self, 'orchestrator') or not self.orchestrator:
                return
            if hasattr(self.orchestrator, 'get_final_presentation'):
                import asyncio

                async def _get_and_display_presentation() -> None:
                    """Helper to get and display presentation asynchronously."""
                    try:
                        presentation_stream = self.orchestrator.get_final_presentation(selected_agent, vote_results)
                        await self.display_final_presentation(selected_agent, presentation_stream, vote_results)
                    except Exception:
                        raise
                import nest_asyncio
                nest_asyncio.apply()
                try:
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(_get_and_display_presentation())
                    time.sleep(0.5)
                except Exception:
                    try:
                        asyncio.run(_get_and_display_presentation())
                        time.sleep(0.5)
                    except Exception:
                        self._display_final_presentation_content(selected_agent, 'Unable to retrieve live presentation.')
            else:
                status = self.orchestrator.get_status()
                if selected_agent in status.get('agent_states', {}):
                    stored_answer = status['agent_states'][selected_agent].get('answer', '')
                    if stored_answer:
                        self._display_final_presentation_content(selected_agent, stored_answer)
                    else:
                        print('DEBUG: No stored answer found')
                else:
                    print(f'DEBUG: Agent {selected_agent} not found in agent_states')
        except Exception as e:
            error_text = Text(f'❌ Error in final presentation: {e}', style=self.colors['error'])
            self.console.print(error_text)

    def _force_display_final_vote_statuses(self) -> None:
        """Force display update to show all agents' final vote statuses."""
        with self._lock:
            for agent_id in self.agent_ids:
                self._pending_updates.add(agent_id)
            self._pending_updates.add('footer')
            self._schedule_async_update(force_update=True)
        import time
        time.sleep(0.3)

    def _flush_all_buffers(self) -> None:
        """Flush all text buffers to ensure no content is lost."""
        for agent_id in self.agent_ids:
            if agent_id in self._text_buffers and self._text_buffers[agent_id]:
                buffer_content = self._text_buffers[agent_id].strip()
                if buffer_content:
                    self.agent_outputs[agent_id].append(buffer_content)
                self._text_buffers[agent_id] = ''

    def cleanup(self) -> None:
        """Clean up display resources."""
        with self._lock:
            self._flush_all_buffers()
            if self.live:
                try:
                    self.live.stop()
                except Exception:
                    pass
                finally:
                    self.live = None
            self._stop_input_thread = True
            if self._input_thread and self._input_thread.is_alive():
                try:
                    self._input_thread.join(timeout=1.0)
                except Exception:
                    pass
            try:
                self._restore_terminal_settings()
            except Exception:
                pass
            self._agent_selector_active = False
            self._final_answer_shown = False
            try:
                signal.signal(signal.SIGWINCH, signal.SIG_DFL)
            except (AttributeError, OSError):
                pass
            if self._key_handler:
                try:
                    self._key_handler.stop()
                except Exception:
                    pass
            self._shutdown_flag = True
            for timer in self._debounce_timers.values():
                timer.cancel()
            self._debounce_timers.clear()
            for timer in self._buffer_timers.values():
                if timer:
                    timer.cancel()
            self._buffer_timers.clear()
            if self._batch_timer:
                self._batch_timer.cancel()
                self._batch_timer = None
            if hasattr(self, '_refresh_executor'):
                self._refresh_executor.shutdown(wait=True)
            if hasattr(self, '_status_update_executor'):
                self._status_update_executor.shutdown(wait=True)
            try:
                for agent_id, file_path in self.agent_files.items():
                    if file_path.exists():
                        with open(file_path, 'a', encoding='utf-8') as f:
                            f.write(f'\n=== SESSION ENDED at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n')
            except Exception:
                pass
        from massgen.logger_config import restore_console_logging
        restore_console_logging()

    def _schedule_priority_update(self, agent_id: str) -> None:
        """Schedule immediate priority update for critical agent status changes."""
        if self._shutdown_flag:
            return

        def priority_update() -> None:
            try:
                self._update_agent_panel_cache(agent_id)
                self._update_display_safe()
            except Exception:
                pass
        self._status_update_executor.submit(priority_update)

    def _categorize_update(self, agent_id: str, content_type: str, content: str) -> None:
        """Categorize update by priority for layered refresh strategy."""
        if content_type in ['status', 'error', 'tool'] or any((keyword in content.lower() for keyword in ['error', 'failed', 'completed', 'voted'])):
            self._critical_updates.add(agent_id)
            self._normal_updates.discard(agent_id)
            self._decorative_updates.discard(agent_id)
        elif content_type in ['thinking', 'presentation']:
            if agent_id not in self._critical_updates:
                self._normal_updates.add(agent_id)
                self._decorative_updates.discard(agent_id)
        elif agent_id not in self._critical_updates and agent_id not in self._normal_updates:
            self._decorative_updates.add(agent_id)

    def _schedule_layered_update(self, agent_id: str, is_critical: bool=False) -> None:
        """Schedule update using layered refresh strategy with intelligent batching."""
        if is_critical:
            self._flush_update_batch()
            self._pending_updates.add(agent_id)
            self._schedule_async_update(force_update=True)
        else:
            perf_tier = self._terminal_performance['performance_tier']
            if perf_tier == 'high':
                self._pending_updates.add(agent_id)
                self._schedule_async_update(force_update=False)
            else:
                self._add_to_update_batch(agent_id)

    def _schedule_delayed_update(self) -> None:
        """Schedule delayed update for non-critical content."""
        delay = self._debounce_delay * 2

        def delayed_update() -> None:
            if self._pending_updates:
                self._schedule_async_update(force_update=False)
        if 'delayed' in self._debounce_timers:
            self._debounce_timers['delayed'].cancel()
        self._debounce_timers['delayed'] = threading.Timer(delay, delayed_update)
        self._debounce_timers['delayed'].start()

    def _add_to_update_batch(self, agent_id: str) -> None:
        """Add update to batch for efficient processing."""
        self._update_batch.add(agent_id)
        if self._batch_timer:
            self._batch_timer.cancel()
        self._batch_timer = threading.Timer(self._batch_timeout, self._process_update_batch)
        self._batch_timer.start()

    def _process_update_batch(self) -> None:
        """Process accumulated batch of updates."""
        if self._update_batch:
            self._pending_updates.update(self._update_batch)
            self._update_batch.clear()
            self._schedule_async_update(force_update=False)

    def _flush_update_batch(self) -> None:
        """Immediately flush any pending batch updates."""
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None
        if self._update_batch:
            self._pending_updates.update(self._update_batch)
            self._update_batch.clear()

    def _schedule_async_update(self, force_update: bool=False):
        """Schedule asynchronous update with debouncing to prevent jitter."""
        current_time = time.time()
        if not force_update and self._should_skip_frame():
            return
        if current_time - self._last_full_refresh > self._full_refresh_interval:
            with self._lock:
                self._pending_updates.add('header')
                self._pending_updates.add('footer')
                self._pending_updates.update(self.agent_ids)
            self._last_full_refresh = current_time
        if force_update:
            self._last_update = current_time
            self._refresh_executor.submit(self._async_update_components)
            return
        if 'main' in self._debounce_timers:
            self._debounce_timers['main'].cancel()

        def debounced_update() -> None:
            current_time = time.time()
            time_since_last_update = current_time - self._last_update
            if time_since_last_update >= self._update_interval:
                self._last_update = current_time
                self._refresh_executor.submit(self._async_update_components)
        self._debounce_timers['main'] = threading.Timer(self._debounce_delay, debounced_update)
        self._debounce_timers['main'].start()

    def _should_skip_frame(self) -> bool:
        """Determine if we should skip this frame update to maintain stability."""
        term_type = self._terminal_performance['type']
        if term_type in ['iterm', 'macos_terminal']:
            if self._dropped_frames > 1:
                return True
            if hasattr(self._refresh_executor, '_work_queue') and self._refresh_executor._work_queue.qsize() > 2:
                return True
        return False

    def _async_update_components(self) -> None:
        """Asynchronously update only the components that have changed."""
        start_time = time.time()
        try:
            updates_to_process = None
            with self._lock:
                if self._pending_updates:
                    updates_to_process = self._pending_updates.copy()
                    self._pending_updates.clear()
            if not updates_to_process:
                return
            futures = []
            for update_id in updates_to_process:
                if update_id == 'header':
                    future = self._refresh_executor.submit(self._update_header_cache)
                    futures.append(future)
                elif update_id == 'footer':
                    future = self._refresh_executor.submit(self._update_footer_cache)
                    futures.append(future)
                elif update_id in self.agent_ids:
                    future = self._refresh_executor.submit(self._update_agent_panel_cache, update_id)
                    futures.append(future)
            for future in futures:
                future.result()
            self._update_display_safe()
        except Exception:
            pass
        finally:
            refresh_time = time.time() - start_time
            self._refresh_times.append(refresh_time)
            self._monitor_performance()

    def _update_header_cache(self) -> None:
        """Update the cached header panel."""
        try:
            self._header_cache = self._create_header()
        except Exception:
            pass

    def _update_footer_cache(self) -> None:
        """Update the cached footer panel."""
        try:
            self._footer_cache = self._create_footer()
        except Exception:
            pass

    def _update_agent_panel_cache(self, agent_id: str):
        """Update the cached panel for a specific agent."""
        try:
            self._agent_panels_cache[agent_id] = self._create_agent_panel(agent_id)
        except Exception:
            pass

    def _update_final_presentation_panel(self) -> None:
        """Update the live display to show the latest final presentation content."""
        try:
            if self.live and self.live.is_started:
                with self._lock:
                    self.live.update(self._create_layout())
        except Exception:
            pass

    def _refresh_display(self) -> None:
        """Override parent's refresh method to use async updates."""
        if self._pending_updates:
            self._schedule_async_update()

    def _is_content_important(self, content: str, content_type: str) -> bool:
        """Determine if content is important enough to trigger a display update."""
        if content_type in self._important_content_types:
            return True
        if any((keyword in content.lower() for keyword in self._status_change_keywords)):
            return True
        if any((keyword in content.lower() for keyword in ['error', 'exception', 'failed', 'timeout'])):
            return True
        return False

    def set_status_jump_enabled(self, enabled: bool):
        """Enable or disable status jumping functionality.

        Args:
            enabled: Whether to enable status jumping
        """
        with self._lock:
            self._status_jump_enabled = enabled

    def set_web_search_truncation(self, enabled: bool, max_lines: int=3):
        """Configure web search content truncation on status changes.

        Args:
            enabled: Whether to enable web search truncation
            max_lines: Maximum web search lines to keep when truncating
        """
        with self._lock:
            self._web_search_truncate_on_status_change = enabled
            self._max_web_search_lines = max_lines

    def set_flush_output(self, enabled: bool, char_delay: float=0.03, word_delay: float=0.08):
        """Configure flush output settings for final answer display.

        Args:
            enabled: Whether to enable flush output effect
            char_delay: Delay between characters in seconds
            word_delay: Extra delay after punctuation in seconds
        """
        with self._lock:
            self._enable_flush_output = enabled
            self._flush_char_delay = char_delay
            self._flush_word_delay = word_delay

def _setup_resize_handler(self) -> None:
    """Setup SIGWINCH signal handler for terminal resize detection."""
    if not sys.stdin.isatty():
        return
    try:
        signal.signal(signal.SIGWINCH, self._handle_resize_signal)
    except (AttributeError, OSError):
        pass

def _update_simple_display(self) -> None:
    """Update display in simple mode without Live."""
    try:
        current_time = time.time()
        if not hasattr(self, '_last_simple_update'):
            self._last_simple_update = 0
        if current_time - self._last_simple_update > 2.0:
            status_line = f'[{time.strftime('%H:%M:%S')}] Agents: '
            for agent_id in self.agent_ids:
                status = self.agent_status.get(agent_id, 'waiting')
                status_line += f'{agent_id}:{status} '
            try:
                self.console.print(f'\r{status_line[:80]}', end='')
            except Exception:
                print(f'\r{status_line[:80]}', end='')
            self._last_simple_update = current_time
    except Exception:
        pass

def _input_thread_worker_improved(self) -> None:
    """Improved background thread worker that doesn't interfere with Rich rendering."""
    if not UNIX_TERMINAL_SUPPORT:
        return self._input_thread_worker_fallback()
    try:
        if sys.stdin.isatty():
            self._original_settings = termios.tcgetattr(sys.stdin.fileno())
            new_settings = termios.tcgetattr(sys.stdin.fileno())
            new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
            new_settings[6][termios.VMIN] = 0
            new_settings[6][termios.VTIME] = 1
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_settings)
        while not self._stop_input_thread:
            try:
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    char = sys.stdin.read(1)
                    if char:
                        self._handle_key_press(char)
            except (BlockingIOError, OSError):
                continue
    except (KeyboardInterrupt, EOFError):
        pass
    except Exception:
        pass
    finally:
        self._restore_terminal_settings()

def _restore_terminal_settings(self) -> None:
    """Restore original terminal settings."""
    try:
        if UNIX_TERMINAL_SUPPORT and sys.stdin.isatty():
            if self._original_settings:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
                self._original_settings = None
            else:
                try:
                    current = termios.tcgetattr(sys.stdin.fileno())
                    current[3] = current[3] | termios.ECHO | termios.ICANON
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, current)
                except Exception:
                    pass
    except Exception:
        pass

def _ensure_clean_keyboard_state(self) -> None:
    """Ensure clean keyboard state before starting agent selector."""
    self._stop_input_thread = True
    if self._input_thread and self._input_thread.is_alive():
        try:
            self._input_thread.join(timeout=0.5)
        except Exception:
            pass
    self._restore_terminal_settings()
    try:
        if UNIX_TERMINAL_SUPPORT and sys.stdin.isatty():
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass
    import time
    time.sleep(0.1)

def _handle_key_press(self, key: str) -> None:
    """Handle key press events for agent selection."""
    if key in self._agent_keys:
        agent_id = self._agent_keys[key]
        self._open_agent_in_default_text_editor(agent_id)
    elif key == 's':
        self._open_system_status_in_default_text_editor()
    elif key == 'f':
        self._open_final_presentation_in_default_text_editor()
    elif key == 'q':
        self._stop_input_thread = True
        self._restore_terminal_settings()

def show_final_answer(self, answer: str, vote_results: Dict[str, Any]=None, selected_agent: str=None):
    """Display the final coordinated answer prominently with voting results, final presentation, and agent selector."""
    with self._lock:
        self._flush_all_buffers()
    if self.live:
        self.live.stop()
        self.live = None
    if vote_results is None or selected_agent is None:
        try:
            if hasattr(self, 'orchestrator') and self.orchestrator:
                status = self.orchestrator.get_status()
                vote_results = vote_results or status.get('vote_results', {})
                selected_agent = selected_agent or status.get('selected_agent')
        except Exception:
            pass
    with self._lock:
        for agent_id in self.agent_ids:
            self._pending_updates.add(agent_id)
        self._pending_updates.add('footer')
        self._schedule_async_update(force_update=True)
    time.sleep(0.5)
    self._force_display_final_vote_statuses()
    time.sleep(0.5)
    if vote_results and vote_results.get('vote_counts'):
        self.display_vote_results(vote_results)
        time.sleep(1.0)
    if selected_agent:
        selected_agent_text = Text(f'🏆 Selected agent: {selected_agent}', style=self.colors['success'])
    else:
        is_timeout = False
        if hasattr(self, 'orchestrator') and self.orchestrator:
            is_timeout = getattr(self.orchestrator, 'is_orchestrator_timeout', False)
        if is_timeout:
            selected_agent_text = Text()
            selected_agent_text.append('No agent selected\n', style=self.colors['warning'])
            selected_agent_text.append('The orchestrator timed out before any agent could complete voting or provide an answer.', style=self.colors['warning'])
        else:
            selected_agent_text = Text('No agent selected', style=self.colors['warning'])
    final_panel = Panel(Align.center(selected_agent_text), title='[bold bright_green]🎯 FINAL COORDINATED ANSWER[/bold bright_green]', border_style=self.colors['success'], box=DOUBLE, expand=False)
    self.console.print(final_panel)
    if selected_agent:
        selection_text = Text()
        selection_text.append(f'✅ Selected by: {selected_agent}', style=self.colors['success'])
        if vote_results and vote_results.get('vote_counts'):
            vote_summary = ', '.join([f'{agent}: {count}' for agent, count in vote_results['vote_counts'].items()])
            selection_text.append(f'\n🗳️ Vote results: {vote_summary}', style=self.colors['info'])
        selection_panel = Panel(selection_text, border_style=self.colors['info'], box=ROUNDED)
        self.console.print(selection_panel)
    if selected_agent and hasattr(self, 'orchestrator') and self.orchestrator:
        try:
            self._show_orchestrator_final_presentation(selected_agent, vote_results)
            time.sleep(1.0)
        except Exception as e:
            error_text = Text(f'❌ Error getting final presentation: {e}', style=self.colors['error'])
            self.console.print(error_text)
    if self._keyboard_interactive_mode and hasattr(self, '_agent_keys') and (not self._safe_keyboard_mode):
        self.show_agent_selector()

def cleanup(self) -> None:
    """Clean up display resources."""
    with self._lock:
        self._flush_all_buffers()
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass
            finally:
                self.live = None
        self._stop_input_thread = True
        if self._input_thread and self._input_thread.is_alive():
            try:
                self._input_thread.join(timeout=1.0)
            except Exception:
                pass
        try:
            self._restore_terminal_settings()
        except Exception:
            pass
        self._agent_selector_active = False
        self._final_answer_shown = False
        try:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        except (AttributeError, OSError):
            pass
        if self._key_handler:
            try:
                self._key_handler.stop()
            except Exception:
                pass
        self._shutdown_flag = True
        for timer in self._debounce_timers.values():
            timer.cancel()
        self._debounce_timers.clear()
        for timer in self._buffer_timers.values():
            if timer:
                timer.cancel()
        self._buffer_timers.clear()
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None
        if hasattr(self, '_refresh_executor'):
            self._refresh_executor.shutdown(wait=True)
        if hasattr(self, '_status_update_executor'):
            self._status_update_executor.shutdown(wait=True)
        try:
            for agent_id, file_path in self.agent_files.items():
                if file_path.exists():
                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write(f'\n=== SESSION ENDED at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n')
        except Exception:
            pass
    from massgen.logger_config import restore_console_logging
    restore_console_logging()

def _should_skip_frame(self) -> bool:
    """Determine if we should skip this frame update to maintain stability."""
    term_type = self._terminal_performance['type']
    if term_type in ['iterm', 'macos_terminal']:
        if self._dropped_frames > 1:
            return True
        if hasattr(self._refresh_executor, '_work_queue') and self._refresh_executor._work_queue.qsize() > 2:
            return True
    return False

class BaseDisplay(ABC):
    """Abstract base class for MassGen coordination displays."""

    def __init__(self, agent_ids: List[str], **kwargs):
        """Initialize display with agent IDs and configuration."""
        self.agent_ids = agent_ids
        self.agent_outputs = {agent_id: [] for agent_id in agent_ids}
        self.agent_status = {agent_id: 'waiting' for agent_id in agent_ids}
        self.orchestrator_events = []
        self.config = kwargs

    @abstractmethod
    def initialize(self, question: str, log_filename: Optional[str]=None):
        """Initialize the display with question and optional log file."""

    @abstractmethod
    def update_agent_content(self, agent_id: str, content: str, content_type: str='thinking'):
        """Update content for a specific agent.

        Args:
            agent_id: The agent whose content to update
            content: The content to add/update
            content_type: Type of content ("thinking", "tool", "status")
        """

    @abstractmethod
    def update_agent_status(self, agent_id: str, status: str):
        """Update status for a specific agent.

        Args:
            agent_id: The agent whose status to update
            status: New status ("waiting", "working", "completed")
        """

    @abstractmethod
    def add_orchestrator_event(self, event: str):
        """Add an orchestrator coordination event.

        Args:
            event: The coordination event message
        """

    @abstractmethod
    def show_final_answer(self, answer: str, vote_results=None, selected_agent=None):
        """Display the final coordinated answer.

        Args:
            answer: The final coordinated answer
            vote_results: Dictionary of vote results (optional)
            selected_agent: The selected agent (optional)
        """

    @abstractmethod
    def cleanup(self):
        """Clean up display resources."""

    def get_agent_content(self, agent_id: str) -> List[str]:
        """Get all content for a specific agent."""
        return self.agent_outputs.get(agent_id, [])

    def get_agent_status(self, agent_id: str) -> str:
        """Get current status for a specific agent."""
        return self.agent_status.get(agent_id, 'unknown')

    def get_orchestrator_events(self) -> List[str]:
        """Get all orchestrator events."""
        return self.orchestrator_events.copy()

    def process_reasoning_content(self, chunk_type: str, content: str, source: str) -> str:
        """Process reasoning content and add prefixes as needed.

        Args:
            chunk_type: Type of the chunk (e.g., "reasoning_summary")
            content: The content to process
            source: The source agent/component

        Returns:
            Processed content with prefix if needed
        """
        if chunk_type == 'reasoning':
            reasoning_active_key = f'_reasoning_active_{source}'
            if not hasattr(self, reasoning_active_key) or not getattr(self, reasoning_active_key, False):
                setattr(self, reasoning_active_key, True)
                return f'🧠 [Reasoning Started]\n{content}\n'
            else:
                return content
        elif chunk_type == 'reasoning_done':
            reasoning_active_key = f'_reasoning_active_{source}'
            if hasattr(self, reasoning_active_key):
                setattr(self, reasoning_active_key, False)
            return '\n🧠 [Reasoning Complete]\n'
        elif chunk_type == 'reasoning_summary':
            summary_active_key = f'_summary_active_{source}'
            if not hasattr(self, summary_active_key) or not getattr(self, summary_active_key, False):
                setattr(self, summary_active_key, True)
                return f'📋 [Reasoning Summary]\n{content}\n'
            else:
                return content
        elif chunk_type == 'reasoning_summary_done':
            summary_active_key = f'_summary_active_{source}'
            if hasattr(self, summary_active_key):
                setattr(self, summary_active_key, False)
        return content

def process_reasoning_content(self, chunk_type: str, content: str, source: str) -> str:
    """Process reasoning content and add prefixes as needed.

        Args:
            chunk_type: Type of the chunk (e.g., "reasoning_summary")
            content: The content to process
            source: The source agent/component

        Returns:
            Processed content with prefix if needed
        """
    if chunk_type == 'reasoning':
        reasoning_active_key = f'_reasoning_active_{source}'
        if not hasattr(self, reasoning_active_key) or not getattr(self, reasoning_active_key, False):
            setattr(self, reasoning_active_key, True)
            return f'🧠 [Reasoning Started]\n{content}\n'
        else:
            return content
    elif chunk_type == 'reasoning_done':
        reasoning_active_key = f'_reasoning_active_{source}'
        if hasattr(self, reasoning_active_key):
            setattr(self, reasoning_active_key, False)
        return '\n🧠 [Reasoning Complete]\n'
    elif chunk_type == 'reasoning_summary':
        summary_active_key = f'_summary_active_{source}'
        if not hasattr(self, summary_active_key) or not getattr(self, summary_active_key, False):
            setattr(self, summary_active_key, True)
            return f'📋 [Reasoning Summary]\n{content}\n'
        else:
            return content
    elif chunk_type == 'reasoning_summary_done':
        summary_active_key = f'_summary_active_{source}'
        if hasattr(self, summary_active_key):
            setattr(self, summary_active_key, False)
    return content

class ChatCompletionsFormatter(FormatterBase):
    """Formatter for Chat Completions API format."""

    def format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert messages for Chat Completions API compatibility.

        Chat Completions API expects tool call arguments as JSON strings in conversation history,
        but they may be passed as objects from other parts of the system.
        """
        converted_messages = []
        for message in messages:
            converted_msg = dict(message)
            converted_msg = self._convert_multimodal_content(converted_msg)
            if message.get('role') == 'assistant' and 'tool_calls' in message:
                converted_tool_calls = []
                for tool_call in message['tool_calls']:
                    converted_call = dict(tool_call)
                    if 'function' in converted_call:
                        converted_function = dict(converted_call['function'])
                        arguments = converted_function.get('arguments')
                        if isinstance(arguments, dict):
                            converted_function['arguments'] = json.dumps(arguments)
                        elif arguments is None:
                            converted_function['arguments'] = '{}'
                        elif not isinstance(arguments, str):
                            converted_function['arguments'] = self._serialize_tool_arguments(arguments)
                        converted_call['function'] = converted_function
                    converted_tool_calls.append(converted_call)
                converted_msg['tool_calls'] = converted_tool_calls
            converted_messages.append(converted_msg)
        return converted_messages

    def _convert_multimodal_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert multimodal content to Chat Completions API format.
        """
        content = message.get('content')
        if not isinstance(content, list):
            return message
        converted_content = []
        for item in content:
            if not isinstance(item, dict):
                converted_content.append({'type': 'text', 'text': str(item)})
                continue
            item_type = item.get('type')
            if item_type == 'text':
                converted_content.append(item)
            elif item_type == 'image':
                converted_item = self._convert_image_content(item)
                if converted_item:
                    converted_content.append(converted_item)
            elif item_type == 'audio':
                converted_item = self._convert_audio_content(item)
                if converted_item:
                    converted_content.append(converted_item)
            elif item_type == 'video':
                converted_item = self._convert_video_content(item)
                if converted_item:
                    converted_content.append(converted_item)
            elif item_type == 'video_url':
                converted_item = self._convert_video_url_content(item)
                if converted_item:
                    converted_content.append(converted_item)
            elif item_type == 'file_pending_upload':
                continue
            elif item_type in ['image_url', 'input_audio', 'video_url']:
                converted_content.append(item)
            else:
                converted_content.append(item)
        message['content'] = converted_content
        return message

    def _convert_image_content(self, image_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert image content item to Chat Completions API format.

        Supports:
        - URL format: {"type": "image", "url": "https://..."}
        - Base64 format: {"type": "image", "base64": "...", "mime_type": "image/jpeg"}

        Returns Chat Completions format: {"type": "image_url", "image_url": {"url": "..."}}
        """
        if 'url' in image_item:
            return {'type': 'image_url', 'image_url': {'url': image_item['url']}}
        if 'base64' in image_item:
            mime_type = image_item.get('mime_type', 'image/jpeg')
            base64_data = image_item['base64']
            data_url = f'data:{mime_type};base64,{base64_data}'
            return {'type': 'image_url', 'image_url': {'url': data_url}}
        return None

    def _convert_audio_content(self, audio_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert audio content item to Chat Completions API format.

        Supports base64 format: {"type": "audio", "base64": "...", "mime_type": "audio/wav"}

        Returns Chat Completions format: {"type": "input_audio", "input_audio": {"data": "...", "format": "wav"}}
        """
        if 'base64' not in audio_item:
            return None
        base64_data = audio_item['base64']
        mime_type = audio_item.get('mime_type', 'audio/wav')
        audio_format = mime_type.split('/')[-1] if '/' in mime_type else 'wav'
        format_mapping = {'mpeg': 'mp3', 'x-wav': 'wav', 'wave': 'wav'}
        audio_format = format_mapping.get(audio_format, audio_format)
        return {'type': 'input_audio', 'input_audio': {'data': base64_data, 'format': audio_format}}

    def _convert_video_content(self, video_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert video content item to Chat Completions API format.

        Supports base64 format: {"type": "video", "base64": "...", "mime_type": "video/mp4"}

        Returns format: {"type": "video_url", "video_url": {"url": "data:video/...;base64,..."}}
        """
        if 'base64' not in video_item:
            return None
        base64_data = video_item['base64']
        mime_type = video_item.get('mime_type', 'video/mp4')
        data_url = f'data:{mime_type};base64,{base64_data}'
        return {'type': 'video_url', 'video_url': {'url': data_url}}

    def _convert_video_url_content(self, video_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert video URL content item to Chat Completions API format.

        Supports URL format: {"type": "video_url", "url": "https://..."}

        Returns format: {"type": "video_url", "video_url": {"url": "..."}}
        """
        if 'url' not in video_item:
            return None
        return {'type': 'video_url', 'video_url': {'url': video_item['url']}}

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools to Chat Completions format if needed.

        Response API format: {"type": "function", "name": ..., "description": ..., "parameters": ...}
        Chat Completions format: {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
        """
        if not tools:
            return tools
        converted_tools = []
        for tool in tools:
            if tool.get('type') == 'function':
                if 'function' in tool:
                    converted_tools.append(tool)
                elif 'name' in tool and 'description' in tool:
                    converted_tools.append({'type': 'function', 'function': {'name': tool['name'], 'description': tool['description'], 'parameters': tool.get('parameters', {})}})
                else:
                    converted_tools.append(tool)
            else:
                converted_tools.append(tool)
        return converted_tools

    def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Chat Completions format."""
        if not mcp_functions:
            return []
        converted_tools = []
        for mcp_function in mcp_functions.values():
            if hasattr(mcp_function, 'to_chat_completions_format'):
                tool = mcp_function.to_chat_completions_format()
            elif hasattr(mcp_function, 'to_openai_format'):
                tool = mcp_function.to_openai_format()
            else:
                tool = {'type': 'function', 'function': {'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'parameters': getattr(mcp_function, 'input_schema', {})}}
            converted_tools.append(tool)
        return converted_tools

def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert MCP tools to Chat Completions format."""
    if not mcp_functions:
        return []
    converted_tools = []
    for mcp_function in mcp_functions.values():
        if hasattr(mcp_function, 'to_chat_completions_format'):
            tool = mcp_function.to_chat_completions_format()
        elif hasattr(mcp_function, 'to_openai_format'):
            tool = mcp_function.to_openai_format()
        else:
            tool = {'type': 'function', 'function': {'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'parameters': getattr(mcp_function, 'input_schema', {})}}
        converted_tools.append(tool)
    return converted_tools

class ResponseFormatter(FormatterBase):
    """Formatter for Response API format with multimodal support."""

    def format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert messages from Chat Completions format to Response API format.

        Chat Completions tool message: {"role": "tool", "tool_call_id": "...", "content": "..."}
        Response API tool message: {"type": "function_call_output", "call_id": "...", "output": "..."}

        Also handles multimodal content conversion:
        - {"type": "text", "text": "..."} → {"type": "input_text", "text": "..."}
        - {"type": "image", "url": "..."} → {"type": "input_image", "image_url": "..."}
        - {"type": "image", "base64": "..."} → {"type": "input_image", "image_url": "data:image/...;base64,..."}

        Note: Assistant messages with tool_calls should not be in input - they're generated by the backend.
        """
        cleaned_messages = []
        for message in messages:
            if 'status' in message and 'role' not in message:
                cleaned_message = {k: v for k, v in message.items() if k != 'status'}
                cleaned_messages.append(cleaned_message)
            else:
                cleaned_messages.append(message)
        converted_messages = []
        for message in cleaned_messages:
            if message.get('role') == 'tool':
                converted_message = {'type': 'function_call_output', 'call_id': message.get('tool_call_id'), 'output': message.get('content', '')}
                converted_messages.append(converted_message)
            elif message.get('type') == 'function_call_output':
                converted_messages.append(message)
            elif message.get('role') == 'assistant' and 'tool_calls' in message:
                cleaned_message = {k: v for k, v in message.items() if k != 'tool_calls'}
                converted_messages.append(cleaned_message)
            else:
                converted_message = self._convert_multimodal_content(message.copy())
                converted_messages.append(converted_message)
        return converted_messages

    def _convert_multimodal_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert multimodal content to Response API format.

        Handles conversion of content arrays with text and image items:
        - text items: {"type": "text", "text": "..."} → {"type": "input_text", "text": "..."}
        - image URL: {"type": "image", "url": "..."} → {"type": "input_image", "image_url": "..."}
        - image base64: {"type": "image", "base64": "...", "mime_type": "..."} →
                        {"type": "input_image", "image_url": "data:image/...;base64,..."}
        - file: {"type": "file", "file_id": "..."} → {"type": "input_file", "file_id": "..."}

        Args:
            message: Message dictionary that may contain multimodal content

        Returns:
            Message with content converted to Response API format
        """
        content = message.get('content')
        if not isinstance(content, list):
            return message
        converted_content = []
        for item in content:
            if not isinstance(item, dict):
                converted_content.append({'type': 'input_text', 'text': str(item)})
                continue
            item_type = item.get('type')
            if item_type == 'text':
                converted_content.append({'type': 'input_text', 'text': item.get('text', '')})
            elif item_type == 'image':
                converted_item = self._convert_image_content(item)
                if converted_item:
                    converted_content.append(converted_item)
            elif item_type == 'file':
                converted_content.append({'type': 'input_file', 'file_id': item.get('file_id', '')})
            elif item_type == 'file_pending_upload':
                converted_content.append(item)
            elif item_type in ['input_text', 'input_image', 'input_file']:
                converted_content.append(item)
            else:
                converted_content.append(item)
        message['content'] = converted_content
        return message

    def _convert_image_content(self, image_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert image content item to Response API format.

        Supports:
        - URL format: {"type": "image", "url": "https://..."}
        - Base64 format: {"type": "image", "base64": "...", "mime_type": "image/jpeg"}
        - Image URL format: {"type": "image", "image_url": "..."} (already correct)

        Args:
            image_item: Image content item dictionary

        Returns:
            Converted image item in Response API format, or None if invalid
        """
        if 'image_url' in image_item:
            return {'type': 'input_image', 'image_url': image_item['image_url']}
        if 'url' in image_item:
            return {'type': 'input_image', 'image_url': image_item['url']}
        if 'base64' in image_item:
            mime_type = image_item.get('mime_type', 'image/jpeg')
            base64_data = image_item['base64']
            if not self._validate_base64_image(base64_data):
                return None
            data_url = f'data:{mime_type};base64,{base64_data}'
            return {'type': 'input_image', 'image_url': data_url}
        return None

    def _validate_base64_image(self, base64_data: str) -> bool:
        """
        Validate base64 image data.

        Checks:
        - Data is not empty
        - Data is valid base64 (basic check)
        - Data size is within limits (20MB)

        Args:
            base64_data: Base64 encoded image string

        Returns:
            True if valid, False otherwise
        """
        if not base64_data:
            return False
        max_base64_size = 27 * 1024 * 1024
        if len(base64_data) > max_base64_size:
            return False
        import re
        if not re.match('^[A-Za-z0-9+/]*={0,2}$', base64_data):
            return False
        return True

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools from Chat Completions format to Response API format if needed.

        Chat Completions format: {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
        Response API format: {"type": "function", "name": ..., "description": ..., "parameters": ...}
        """
        if not tools:
            return tools
        converted_tools = []
        for tool in tools:
            if tool.get('type') == 'function' and 'function' in tool:
                func = tool['function']
                converted_tools.append({'type': 'function', 'name': func['name'], 'description': func['description'], 'parameters': func.get('parameters', {})})
            else:
                converted_tools.append(tool)
        return converted_tools

    def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Response API format (OpenAI function declarations)."""
        if not mcp_functions:
            return []
        converted_tools = []
        for mcp_function in mcp_functions.values():
            if hasattr(mcp_function, 'to_openai_format'):
                tool = mcp_function.to_openai_format()
            else:
                tool = {'type': 'function', 'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'parameters': getattr(mcp_function, 'input_schema', {})}
            converted_tools.append(tool)
        return converted_tools

def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert MCP tools to Response API format (OpenAI function declarations)."""
    if not mcp_functions:
        return []
    converted_tools = []
    for mcp_function in mcp_functions.values():
        if hasattr(mcp_function, 'to_openai_format'):
            tool = mcp_function.to_openai_format()
        else:
            tool = {'type': 'function', 'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'parameters': getattr(mcp_function, 'input_schema', {})}
        converted_tools.append(tool)
    return converted_tools

class ClaudeFormatter(FormatterBase):
    """Formatter for Claude API format."""

    def format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted, _ = self.format_messages_and_system(messages)
        return formatted

    def format_messages_and_system(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
        """
        Convert messages to Claude's expected format.

        Handle different tool message formats and extract system message:
        - Chat Completions tool message: {"role": "tool", "tool_call_id": "...", "content": "..."}
        - Response API tool message: {"type": "function_call_output", "call_id": "...", "output": "..."}
        - System messages: Extract and return separately for top-level system parameter

        Returns:
            tuple: (converted_messages, system_message)
        """
        converted_messages = []
        system_message = ''
        for message in messages:
            if message.get('role') == 'system':
                system_message = message.get('content', '')
            elif message.get('role') == 'tool':
                converted_messages.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': message.get('tool_call_id'), 'content': message.get('content', '')}]})
            elif message.get('type') == 'function_call_output':
                converted_messages.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': message.get('call_id'), 'content': message.get('output', '')}]})
            elif message.get('role') == 'assistant' and 'tool_calls' in message:
                content = []
                if message.get('content'):
                    content.append({'type': 'text', 'text': message['content']})
                for tool_call in message['tool_calls']:
                    tool_name = self.extract_tool_name(tool_call)
                    tool_args = self.extract_tool_arguments(tool_call)
                    tool_id = self.extract_tool_call_id(tool_call)
                    content.append({'type': 'tool_use', 'id': tool_id, 'name': tool_name, 'input': tool_args})
                converted_messages.append({'role': 'assistant', 'content': content})
            elif message.get('role') in ['user', 'assistant']:
                converted_message = dict(message)
                if isinstance(converted_message.get('content'), str):
                    pass
                elif isinstance(converted_message.get('content'), list):
                    converted_message = self._convert_multimodal_content(converted_message)
                converted_messages.append(converted_message)
        return (converted_messages, system_message)

    def _convert_multimodal_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize multimodal content blocks to Claude's nested source structure."""
        content = message.get('content')
        if not isinstance(content, list):
            return message
        converted_items: List[Dict[str, Any]] = []
        for item in content:
            if not isinstance(item, dict):
                converted_items.append(item)
                continue
            item_type = item.get('type')
            if item_type in {'tool_result', 'tool_use', 'text', 'file_pending_upload'}:
                converted_items.append(item)
                continue
            if item_type not in {'image', 'document'}:
                converted_items.append(item)
                continue
            if isinstance(item.get('source'), dict):
                converted_items.append(item)
                continue
            if 'file_id' in item:
                normalized = {key: value for key, value in item.items() if key != 'file_id'}
                normalized['source'] = {'type': 'file', 'file_id': item['file_id']}
                converted_items.append(normalized)
                continue
            if 'base64' in item:
                media_type = item.get('mime_type') or item.get('media_type')
                normalized = {key: value for key, value in item.items() if key not in {'base64', 'mime_type', 'media_type'}}
                normalized['source'] = {'type': 'base64', 'media_type': media_type, 'data': item['base64']}
                converted_items.append(normalized)
                continue
            if 'url' in item:
                normalized = {key: value for key, value in item.items() if key != 'url'}
                normalized['source'] = {'type': 'url', 'url': item['url']}
                converted_items.append(normalized)
                continue
            converted_items.append(item)
        message['content'] = converted_items
        return message

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools to Claude's expected format.

        Input formats supported:
        - Response API format: {"type": "function", "name": ..., "description": ..., "parameters": ...}
        - Chat Completions format: {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}

        Claude format: {"type": "custom", "name": ..., "description": ..., "input_schema": ...}
        """
        if not tools:
            return tools
        converted_tools = []
        for tool in tools:
            if tool.get('type') == 'function':
                if 'function' in tool:
                    func = tool['function']
                    converted_tools.append({'type': 'custom', 'name': func['name'], 'description': func['description'], 'input_schema': func.get('parameters', {})})
                elif 'name' in tool and 'description' in tool:
                    converted_tools.append({'type': 'custom', 'name': tool['name'], 'description': tool['description'], 'input_schema': tool.get('parameters', {})})
                else:
                    converted_tools.append(tool)
            else:
                converted_tools.append(tool)
        return converted_tools

    def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Claude's custom tool format."""
        if not mcp_functions:
            return []
        converted_tools = []
        for mcp_function in mcp_functions.values():
            if hasattr(mcp_function, 'to_claude_format'):
                tool = mcp_function.to_claude_format()
            else:
                tool = {'type': 'custom', 'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'input_schema': getattr(mcp_function, 'input_schema', {})}
            converted_tools.append(tool)
        return converted_tools

def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert MCP tools to Claude's custom tool format."""
    if not mcp_functions:
        return []
    converted_tools = []
    for mcp_function in mcp_functions.values():
        if hasattr(mcp_function, 'to_claude_format'):
            tool = mcp_function.to_claude_format()
        else:
            tool = {'type': 'custom', 'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'input_schema': getattr(mcp_function, 'input_schema', {})}
        converted_tools.append(tool)
    return converted_tools

class AzureOpenAIBackend(LLMBackend):
    """Azure OpenAI backend using the official Azure OpenAI client.

    Supports Azure OpenAI deployments with proper Azure authentication and configuration.

    Environment Variables:
        AZURE_OPENAI_API_KEY: Azure OpenAI API key
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        AZURE_OPENAI_API_VERSION: Azure OpenAI API version (optional, defaults to 2024-12-01-preview)
    """

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('Azure OpenAI API key is required. Set AZURE_OPENAI_API_KEY environment variable or pass api_key parameter.')

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return 'Azure OpenAI'

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a response with tool calling support using Azure OpenAI.

        Args:
            messages: Conversation messages
            tools: Available tools schema
            **kwargs: Additional parameters including model (deployment name)
        """
        agent_id = kwargs.get('agent_id', None)
        log_backend_activity(self.get_provider_name(), 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        try:
            all_params = {**self.config, **kwargs}
            from openai import AsyncAzureOpenAI
            azure_endpoint = all_params.get('azure_endpoint') or all_params.get('base_url') or os.getenv('AZURE_OPENAI_ENDPOINT')
            api_version = all_params.get('api_version') or os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
            if not azure_endpoint:
                raise ValueError('Azure OpenAI endpoint URL is required. Set AZURE_OPENAI_ENDPOINT environment variable or pass azure_endpoint/base_url parameter.')
            if not api_version:
                raise ValueError('Azure OpenAI API version is required. Set AZURE_OPENAI_API_VERSION environment variable or pass api_version parameter.')
            if azure_endpoint.endswith('/'):
                azure_endpoint = azure_endpoint[:-1]
            self.client = AsyncAzureOpenAI(api_version=api_version, azure_endpoint=azure_endpoint, api_key=self.api_key)
            deployment_name = all_params.get('model')
            if not deployment_name:
                raise ValueError("Azure OpenAI requires a deployment name. Pass it as the 'model' parameter.")
            workflow_tools = [t for t in tools if t.get('function', {}).get('name') in ['new_answer', 'vote']] if tools else []
            has_workflow_tools = len(workflow_tools) > 0
            modified_messages = self._prepare_messages_with_workflow_tools(messages, workflow_tools) if has_workflow_tools else messages
            log_backend_agent_message(agent_id or 'default', 'SEND', {'messages': modified_messages, 'tools': len(tools) if tools else 0}, backend_name=self.get_provider_name())
            api_params = {'messages': modified_messages, 'model': deployment_name, 'stream': True}
            if tools and len(tools) > 0:
                converted_tools = self._convert_tools_format(tools)
                api_params['tools'] = converted_tools
            else:
                api_params['tool_choice'] = 'none'
            excluded_params = self.get_base_excluded_config_params() | {'model', 'messages', 'stream', 'tools'}
            for key, value in kwargs.items():
                if key not in excluded_params and value is not None:
                    api_params[key] = value
            stream = await self.client.chat.completions.create(**api_params)
            accumulated_content = ''
            complete_response = ''
            last_yield_type = None
            async for chunk in stream:
                converted = self._convert_chunk_to_stream_chunk(chunk)
                if converted.type == 'content' and converted.content:
                    accumulated_content += converted.content
                    complete_response += converted.content
                    if len(accumulated_content) >= 10 or ' ' in accumulated_content:
                        log_backend_agent_message(agent_id or 'default', 'RECV', {'content': accumulated_content}, backend_name=self.get_provider_name())
                        log_stream_chunk('backend.azure_openai', 'content', accumulated_content, agent_id)
                        yield StreamChunk(type='content', content=accumulated_content)
                        accumulated_content = ''
                elif converted.type != 'content':
                    if converted.type == 'error':
                        log_stream_chunk('backend.azure_openai', 'error', converted.error, agent_id)
                    elif converted.type == 'done':
                        log_stream_chunk('backend.azure_openai', 'done', None, agent_id)
                    last_yield_type = converted.type
                    yield converted
            if accumulated_content:
                log_backend_agent_message(agent_id or 'default', 'RECV', {'content': accumulated_content}, backend_name=self.get_provider_name())
                log_stream_chunk('backend.azure_openai', 'content', accumulated_content, agent_id)
                yield StreamChunk(type='content', content=accumulated_content)
            if has_workflow_tools:
                workflow_tool_calls = self._extract_workflow_tool_calls(complete_response)
                if workflow_tool_calls:
                    log_stream_chunk('backend.azure_openai', 'tool_calls', workflow_tool_calls, agent_id)
                    yield StreamChunk(type='tool_calls', tool_calls=workflow_tool_calls)
                    last_yield_type = 'tool_calls'
            if last_yield_type != 'done':
                log_stream_chunk('backend.azure_openai', 'done', None, agent_id)
                yield StreamChunk(type='done')
        except Exception as e:
            error_msg = f'Azure OpenAI API error: {str(e)}'
            log_stream_chunk('backend.azure_openai', 'error', error_msg, agent_id)
            yield StreamChunk(type='error', error=error_msg)

    def _prepare_messages_with_workflow_tools(self, messages: List[Dict[str, Any]], workflow_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages with workflow tool instructions."""
        if not workflow_tools:
            return messages
        system_message = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_message = msg
                break
        enhanced_system = self._build_workflow_tools_system_prompt(system_message.get('content', '') if system_message else '', workflow_tools)
        new_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                new_messages.append({'role': 'system', 'content': enhanced_system})
            else:
                new_messages.append(msg)
        return new_messages

    def _build_workflow_tools_system_prompt(self, base_system: str, workflow_tools: List[Dict[str, Any]]) -> str:
        """Build system prompt with workflow tool instructions."""
        system_parts = []
        if base_system:
            system_parts.append(base_system)
        if workflow_tools:
            system_parts.append('\n--- Available Tools ---')
            for tool in workflow_tools:
                name = tool.get('function', {}).get('name', 'unknown')
                description = tool.get('function', {}).get('description', 'No description')
                system_parts.append(f'- {name}: {description}')
                if name == 'new_answer':
                    system_parts.append('    Usage: {"tool_name": "new_answer", "arguments": {"content": "your answer"}}')
                elif name == 'vote':
                    agent_id_enum = None
                    for t in workflow_tools:
                        if t.get('function', {}).get('name') == 'vote':
                            agent_id_param = t.get('function', {}).get('parameters', {}).get('properties', {}).get('agent_id', {})
                            if 'enum' in agent_id_param:
                                agent_id_enum = agent_id_param['enum']
                            break
                    if agent_id_enum:
                        agent_list = ', '.join(agent_id_enum)
                        system_parts.append(f'    Usage: {{"tool_name": "vote", "arguments": {{"agent_id": "agent1", "reason": "explanation"}}}} // Choose agent_id from: {agent_list}')
                    else:
                        system_parts.append('    Usage: {"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}')
            system_parts.append('\n--- MassGen Workflow Instructions ---')
            system_parts.append('IMPORTANT: You must respond with a structured JSON decision at the end of your response.')
            system_parts.append('You must use the coordination tools (new_answer, vote) to participate in multi-agent workflows.')
            system_parts.append('The JSON MUST be formatted as a strict JSON code block:')
            system_parts.append('1. Start with ```json on one line')
            system_parts.append('2. Include your JSON content (properly formatted)')
            system_parts.append('3. End with ``` on one line')
            system_parts.append('Example format:\n```json\n{"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}\n```')
            system_parts.append('The JSON block should be placed at the very end of your response, after your analysis.')
        return '\n'.join(system_parts)

    def _extract_workflow_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract workflow tool calls from content."""
        try:
            import json
            import re
            markdown_json_pattern = '```json\\s*(\\{.*?\\})\\s*```'
            markdown_matches = re.findall(markdown_json_pattern, content, re.DOTALL)
            for match in reversed(markdown_matches):
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        tool_call = {'id': f'call_{hash(match) % 10000}', 'type': 'function', 'function': {'name': parsed['tool_name'], 'arguments': json.dumps(parsed['arguments'])}}
                        return [tool_call]
                except json.JSONDecodeError:
                    continue
            json_pattern = '\\{[^{}]*"tool_name"[^{}]*\\}'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            for match in json_matches:
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        tool_call = {'id': f'call_{hash(match) % 10000}', 'type': 'function', 'function': {'name': parsed['tool_name'], 'arguments': json.dumps(parsed['arguments'])}}
                        return [tool_call]
                except json.JSONDecodeError:
                    continue
            return []
        except Exception:
            return []

    def _convert_tools_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Azure OpenAI format if needed."""
        return tools

    def _convert_chunk_to_stream_chunk(self, chunk) -> StreamChunk:
        """Convert Azure OpenAI chunk to MassGen StreamChunk format."""
        try:
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, 'delta') and choice.delta:
                    delta = choice.delta
                    if hasattr(delta, 'content') and delta.content:
                        return StreamChunk(type='content', content=delta.content)
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        tool_call_text = ''
                        for tool_call in delta.tool_calls:
                            if hasattr(tool_call, 'function') and tool_call.function:
                                if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                    tool_call_text += tool_call.function.arguments
                        if tool_call_text:
                            return StreamChunk(type='content', content=tool_call_text)
                    if hasattr(choice, 'finish_reason') and choice.finish_reason:
                        if choice.finish_reason == 'stop':
                            return StreamChunk(type='done')
                        elif choice.finish_reason == 'tool_calls':
                            return StreamChunk(type='done')
            return StreamChunk(type='content', content='')
        except Exception as e:
            return StreamChunk(type='error', error=f'Error processing chunk: {str(e)}')

    def extract_tool_call_id(self, tool_call: Dict[str, Any]) -> str:
        """Extract tool call id from Chat Completions-style tool call."""
        return tool_call.get('id', '')

def _convert_chunk_to_stream_chunk(self, chunk) -> StreamChunk:
    """Convert Azure OpenAI chunk to MassGen StreamChunk format."""
    try:
        if hasattr(chunk, 'choices') and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and choice.delta:
                delta = choice.delta
                if hasattr(delta, 'content') and delta.content:
                    return StreamChunk(type='content', content=delta.content)
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    tool_call_text = ''
                    for tool_call in delta.tool_calls:
                        if hasattr(tool_call, 'function') and tool_call.function:
                            if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                tool_call_text += tool_call.function.arguments
                    if tool_call_text:
                        return StreamChunk(type='content', content=tool_call_text)
                if hasattr(choice, 'finish_reason') and choice.finish_reason:
                    if choice.finish_reason == 'stop':
                        return StreamChunk(type='done')
                    elif choice.finish_reason == 'tool_calls':
                        return StreamChunk(type='done')
        return StreamChunk(type='content', content='')
    except Exception as e:
        return StreamChunk(type='error', error=f'Error processing chunk: {str(e)}')

class MCPBackend(LLMBackend):
    """Base backend class with MCP (Model Context Protocol) support."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        """Initialize backend with MCP support."""
        super().__init__(api_key, **kwargs)
        self.mcp_servers = self.config.get('mcp_servers', [])
        self.allowed_tools = kwargs.pop('allowed_tools', None)
        self.exclude_tools = kwargs.pop('exclude_tools', None)
        self._mcp_client: Optional[MCPClient] = None
        self._mcp_initialized = False
        self._mcp_tool_calls_count = 0
        self._mcp_tool_failures = 0
        self._mcp_function_names: set[str] = set()
        self._mcp_tools_circuit_breaker = None
        self._circuit_breakers_enabled = MCPCircuitBreaker is not None
        if self._circuit_breakers_enabled and self.mcp_servers:
            mcp_tools_config = MCPConfigHelper.build_circuit_breaker_config('mcp_tools') if MCPConfigHelper else None
            if mcp_tools_config:
                self._mcp_tools_circuit_breaker = MCPCircuitBreaker(mcp_tools_config)
                logger.info('Circuit breaker initialized for MCP tools')
            else:
                logger.warning('MCP tools circuit breaker config not available, disabling circuit breaker functionality')
                self._circuit_breakers_enabled = False
        elif not self.mcp_servers:
            self._circuit_breakers_enabled = False
        else:
            logger.warning('Circuit breakers not available - proceeding without circuit breaker protection')
        self._mcp_functions: Dict[str, Function] = {}
        self._stats_lock = asyncio.Lock()
        self._max_mcp_message_history = kwargs.pop('max_mcp_message_history', 200)
        self.backend_name = self.get_provider_name()
        self.agent_id = kwargs.get('agent_id', None)

    def supports_upload_files(self) -> bool:
        """Return True if the backend supports `upload_files` preprocessing."""
        return False

    @abstractmethod
    async def _process_stream(self, stream, all_params, agent_id: Optional[str]=None) -> AsyncGenerator[StreamChunk, None]:
        """Process stream."""

    async def _setup_mcp_tools(self) -> None:
        """Initialize MCP client for mcp_tools-based servers (stdio + streamable-http)."""
        if not self.mcp_servers or self._mcp_initialized:
            return
        try:
            normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers, backend_name=self.backend_name, agent_id=self.agent_id) if MCPSetupManager else []
            if not MCPSetupManager:
                logger.warning('MCPSetupManager not available')
                return
            mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers, backend_name=self.backend_name, agent_id=self.agent_id)
            if not mcp_tools_servers:
                logger.info('No stdio/streamable-http servers configured')
                return
            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker and MCPCircuitBreakerManager:
                filtered_servers = MCPCircuitBreakerManager.apply_circuit_breaker_filtering(mcp_tools_servers, self._mcp_tools_circuit_breaker, backend_name=self.backend_name, agent_id=self.agent_id)
                if not filtered_servers:
                    logger.warning('All MCP servers blocked by circuit breaker during setup')
                    return
                if len(filtered_servers) < len(mcp_tools_servers):
                    logger.info(f'Circuit breaker filtered {len(mcp_tools_servers) - len(filtered_servers)} servers during setup')
                servers_to_use = filtered_servers
            else:
                servers_to_use = mcp_tools_servers
            if not MCPResourceManager:
                logger.warning('MCPResourceManager not available')
                return
            self._mcp_client = await MCPResourceManager.setup_mcp_client(servers=servers_to_use, allowed_tools=self.allowed_tools, exclude_tools=self.exclude_tools, circuit_breaker=self._mcp_tools_circuit_breaker, timeout_seconds=400, backend_name=self.backend_name, agent_id=self.agent_id)
            if not self._mcp_client:
                self._mcp_initialized = False
                logger.warning('MCP client setup failed, falling back to no-MCP streaming')
                return
            self._mcp_functions.update(MCPResourceManager.convert_tools_to_functions(self._mcp_client, backend_name=self.backend_name, agent_id=self.agent_id, hook_manager=getattr(self, 'function_hook_manager', None)))
            self._mcp_initialized = True
            logger.info(f'Successfully initialized MCP sessions with {len(self._mcp_functions)} tools converted to functions')
            await self._record_mcp_circuit_breaker_success(servers_to_use)
        except Exception as e:
            self._record_mcp_circuit_breaker_failure(e, self.agent_id)
            logger.warning(f'Failed to setup MCP sessions: {e}')
            self._mcp_client = None
            self._mcp_initialized = False
            self._mcp_functions = {}

    async def _execute_mcp_function_with_retry(self, function_name: str, arguments_json: str, max_retries: int=3) -> Tuple[str, Any]:
        """Execute MCP function with exponential backoff retry logic."""
        if self.is_planning_mode_enabled():
            logger.info(f'[MCP] Planning mode enabled - blocking MCP tool execution: {function_name}')
            error_str = '🚫 [MCP] Planning mode active - MCP tools blocked during coordination'
            return (error_str, {'error': error_str, 'blocked_by': 'planning_mode', 'function_name': function_name})
        try:
            args = json.loads(arguments_json) if isinstance(arguments_json, str) else arguments_json
        except (json.JSONDecodeError, ValueError) as e:
            error_str = f'Error: Invalid JSON arguments: {e}'
            return (error_str, {'error': error_str})

        async def stats_callback(action: str) -> int:
            async with self._stats_lock:
                if action == 'increment_calls':
                    self._mcp_tool_calls_count += 1
                    return self._mcp_tool_calls_count
                elif action == 'increment_failures':
                    self._mcp_tool_failures += 1
                    return self._mcp_tool_failures
            return 0

        async def circuit_breaker_callback(event: str, error_msg: str='') -> None:
            if not (self._circuit_breakers_enabled and MCPCircuitBreakerManager and self._mcp_tools_circuit_breaker):
                return
            if event == 'failure':
                await MCPCircuitBreakerManager.record_event([], self._mcp_tools_circuit_breaker, 'failure', error_msg, backend_name=self.backend_name, agent_id=self.agent_id)
            else:
                await MCPCircuitBreakerManager.record_event([], self._mcp_tools_circuit_breaker, 'success', backend_name=self.backend_name, agent_id=self.agent_id)
        if not MCPExecutionManager:
            return ('Error: MCPExecutionManager unavailable', {'error': 'MCPExecutionManager unavailable'})
        result = await MCPExecutionManager.execute_function_with_retry(function_name=function_name, args=args, functions=self._mcp_functions, max_retries=max_retries, stats_callback=stats_callback, circuit_breaker_callback=circuit_breaker_callback, logger_instance=logger)
        if isinstance(result, dict) and 'error' in result:
            return (f'Error: {result['error']}', result)
        return (str(result), result)

    async def _process_upload_files(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process upload_files config entries and attach to messages.

        Supports these forms:

        - {"image_path": "..."}: image file path or HTTP/HTTPS URL
          - Local paths: loads and base64-encodes the image file
          - URLs: passed directly without encoding
          Supported formats: PNG, JPEG, WEBP, GIF, BMP, TIFF, HEIC (provider-dependent)

        - {"audio_path": "..."}: audio file path or HTTP/HTTPS URL
          - Local paths: loads and base64-encodes the audio file
          - URLs: fetched and base64-encoded (30s timeout, configurable size limit)
          Supported formats: WAV, MP3 (strictly validated)

        - {"video_path": "..."}: video file path or HTTP/HTTPS URL
          - Local paths: loads and base64-encodes the video file
          - URLs: passed directly without encoding, converted to video_url format
          Supported formats: MP4, AVI, MOV, WEBM (provider-dependent)

        - {"file_path": "..."}: document/code file for File Search (local path or URL)
          - Local paths: validated against supported extensions and size limits
          - URLs: queued for upload without local validation
          Supported extensions: .c, .cpp, .cs, .css, .doc, .docx, .html, .java, .js,
          .json, .md, .pdf, .php, .pptx, .py, .rb, .sh, .tex, .ts, .txt

        Note: Format support varies by provider (OpenAI, Qwen, vLLM, etc.). The implementation
        uses MIME type detection for automatic format handling.

        Audio/Video/Image uploads are limited by `media_max_file_size_mb` (default 64MB).
        File Search files are limited to 512MB. You can override limits via config or call parameters.

        Returns updated messages list with additional content items.
        """
        upload_entries = all_params.get('upload_files')
        if not upload_entries:
            return messages
        if not self.supports_upload_files():
            logger.debug('upload_files provided but backend %s does not support file uploads; ignoring', self.get_provider_name())
            all_params.pop('upload_files', None)
            return messages
        processed_messages = list(messages)
        extra_content: List[Dict[str, Any]] = []
        has_file_search_files = False
        for entry in upload_entries:
            if not isinstance(entry, dict):
                logger.warning('upload_files entry is not a dict: %s', entry)
                raise UploadFileError('Each upload_files entry must be a mapping')
            file_path_value = entry.get('file_path')
            if file_path_value:
                file_content = self._process_file_path_entry(file_path_value, all_params)
                if file_content:
                    extra_content.append(file_content)
                    has_file_search_files = True
                continue
            path_value = entry.get('image_path')
            if path_value:
                if path_value.startswith(('http://', 'https://')):
                    extra_content.append({'type': 'image', 'url': path_value})
                else:
                    resolved = self._resolve_local_path(path_value, all_params)
                    if not resolved.exists():
                        raise UploadFileError(f'File not found: {resolved}')
                    limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
                    self._validate_media_size(resolved, int(limit_mb))
                    encoded, mime_type = self._read_base64(resolved)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                    extra_content.append({'type': 'image', 'base64': encoded, 'mime_type': mime_type, 'source_path': str(resolved)})
                continue
            audio_path_value = entry.get('audio_path')
            if audio_path_value:
                if audio_path_value.startswith(('http://', 'https://')):
                    encoded, mime_type = await self._fetch_audio_url_as_base64(audio_path_value, all_params)
                    extra_content.append({'type': 'audio', 'base64': encoded, 'mime_type': mime_type})
                else:
                    resolved = self._resolve_local_path(audio_path_value, all_params)
                    if not resolved.exists():
                        raise UploadFileError(f'Audio file not found: {resolved}')
                    limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
                    self._validate_media_size(resolved, int(limit_mb))
                    encoded, mime_type = self._read_base64(resolved)
                    mime_lower = (mime_type or '').split(';')[0].strip().lower()
                    if mime_lower not in SUPPORTED_AUDIO_MIME_TYPES:
                        raise UploadFileError(f'Unsupported audio format for {resolved}. Supported formats: mp3, wav')
                    if mime_lower in {'audio/wav', 'audio/wave', 'audio/x-wav'}:
                        mime_type = 'audio/wav'
                    else:
                        mime_type = 'audio/mpeg'
                    extra_content.append({'type': 'audio', 'base64': encoded, 'mime_type': mime_type, 'source_path': str(resolved)})
                continue
            video_path_value = entry.get('video_path')
            if video_path_value:
                if video_path_value.startswith(('http://', 'https://')):
                    extra_content.append({'type': 'video_url', 'url': video_path_value})
                else:
                    resolved = self._resolve_local_path(video_path_value, all_params)
                    if not resolved.exists():
                        raise UploadFileError(f'Video file not found: {resolved}')
                    limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
                    self._validate_media_size(resolved, int(limit_mb))
                    encoded, mime_type = self._read_base64(resolved)
                    if not mime_type:
                        mime_type = 'video/mp4'
                    extra_content.append({'type': 'video', 'base64': encoded, 'mime_type': mime_type, 'source_path': str(resolved)})
                continue
            raise UploadFileError("upload_files entry must specify either 'image_path', 'audio_path', 'video_path', or 'file_path'")
        if not extra_content:
            return processed_messages
        if has_file_search_files:
            all_params['_has_file_search_files'] = True
        if processed_messages:
            last_message = processed_messages[-1].copy()
            last_content = last_message.get('content', [])
            if isinstance(last_content, str):
                last_content = [{'type': 'text', 'text': last_content}]
            elif isinstance(last_content, dict) and 'type' in last_content:
                last_content = [dict(last_content)]
            elif isinstance(last_content, list):
                if all((isinstance(item, str) for item in last_content)):
                    last_content = [{'type': 'text', 'text': item} for item in last_content]
                elif all((isinstance(item, dict) and 'type' in item and ('text' in item) for item in last_content)):
                    last_content = list(last_content)
                else:
                    last_content = []
            else:
                last_content = []
            last_content.extend(extra_content)
            last_message['content'] = last_content
            processed_messages[-1] = last_message
        else:
            processed_messages.append({'role': 'user', 'content': extra_content})
        all_params.pop('upload_files', None)
        return processed_messages

    def _process_file_path_entry(self, file_path_value: str, all_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process file path entry and validate against provider-specific restrictions.

        Note: This base implementation validates against OpenAI File Search extensions.
        Backends like Claude may have additional restrictions (e.g., only .pdf and .txt)
        and should perform provider-specific validation in their upload methods.
        """
        if file_path_value.startswith(('http://', 'https://')):
            logger.info(f'Queued file URL for File Search upload: {file_path_value}')
            return {'type': 'file_pending_upload', 'url': file_path_value, 'source': 'url'}
        resolved = Path(file_path_value).expanduser()
        if not resolved.is_absolute():
            cwd = all_params.get('cwd') or self.config.get('cwd')
            if cwd:
                resolved = Path(cwd).joinpath(resolved)
            else:
                resolved = resolved.resolve()
        if not resolved.exists():
            raise UploadFileError(f'File not found: {resolved}')
        file_ext = resolved.suffix.lower()
        if file_ext not in FILE_SEARCH_SUPPORTED_EXTENSIONS:
            raise UploadFileError(f'File type {file_ext} not supported by File Search. Supported types: {', '.join(sorted(FILE_SEARCH_SUPPORTED_EXTENSIONS))}')
        file_size = resolved.stat().st_size
        if file_size > FILE_SEARCH_MAX_FILE_SIZE:
            raise UploadFileError(f'File size {file_size / (1024 * 1024):.2f} MB exceeds File Search limit of {FILE_SEARCH_MAX_FILE_SIZE / (1024 * 1024):.0f} MB')
        mime_type, _ = mimetypes.guess_type(resolved.as_posix())
        if not mime_type:
            mime_type = 'application/octet-stream'
        logger.info(f'Queued local file for File Search upload: {resolved}')
        return {'type': 'file_pending_upload', 'path': str(resolved), 'mime_type': mime_type, 'source': 'local'}

    def _resolve_local_path(self, raw_path: str, all_params: Dict[str, Any]) -> Path:
        """Resolve a local path using cwd from all_params or config, mirroring file_path resolution."""
        resolved = Path(raw_path).expanduser()
        if not resolved.is_absolute():
            cwd = all_params.get('cwd') or self.config.get('cwd')
            if cwd:
                resolved = Path(cwd).joinpath(resolved)
            else:
                resolved = resolved.resolve()
        return resolved

    def _validate_media_size(self, path: Path, limit_mb: int) -> None:
        """Validate media file size against MB limit; raise UploadFileError if exceeded."""
        file_size = path.stat().st_size
        if file_size > limit_mb * 1024 * 1024:
            logger.warning(f'Media file too large: {file_size / (1024 * 1024):.2f} MB at {path} (limit {limit_mb} MB)')
            raise UploadFileError(f'Media file size {file_size / (1024 * 1024):.2f} MB exceeds limit of {limit_mb:.0f} MB: {path}')

    def _read_base64(self, path: Path) -> Tuple[str, str]:
        """Read file bytes and return (base64, guessed_mime_type)."""
        mime_type, _ = mimetypes.guess_type(path.as_posix())
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise UploadFileError(f'Failed to read file {path}: {exc}') from exc
        encoded = base64.b64encode(data).decode('utf-8')
        return (encoded, mime_type or '')

    async def _fetch_audio_url_as_base64(self, url: str, all_params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Fetch audio from URL and return (base64_encoded_data, mime_type).

        Currently supports: wav, mp3

        Args:
            url: HTTP/HTTPS URL to fetch audio from
            all_params: Parameters dict containing optional media_max_file_size_mb

        Returns:
            Tuple of (base64_encoded_string, mime_type)

        Raises:
            UploadFileError: If fetch fails, format is unsupported, or size exceeds limit
        """
        limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
        max_size_bytes = int(limit_mb) * 1024 * 1024
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(url, timeout=30.0)
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise UploadFileError(f'Timeout (30s) while fetching audio from {url}') from exc
            except httpx.HTTPError as exc:
                raise UploadFileError(f'Failed to fetch audio from {url}: {exc}') from exc
            content_type = response.headers.get('Content-Type', '')
            mime_type = content_type.split(';')[0].strip().lower()
            if mime_type not in SUPPORTED_AUDIO_MIME_TYPES:
                guessed_mime, _ = mimetypes.guess_type(url)
                if guessed_mime and guessed_mime.lower() in SUPPORTED_AUDIO_MIME_TYPES:
                    mime_type = guessed_mime.lower()
                else:
                    raise UploadFileError(f'Unsupported audio format for {url}. Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}')
            if mime_type in {'audio/wav', 'audio/wave', 'audio/x-wav'}:
                mime_type = 'audio/wav'
            elif mime_type in {'audio/mpeg', 'audio/mp3'}:
                mime_type = 'audio/mpeg'
            audio_bytes = response.content
            if len(audio_bytes) > max_size_bytes:
                raise UploadFileError(f'Audio file size {len(audio_bytes) / (1024 * 1024):.2f} MB exceeds limit of {limit_mb} MB: {url}')
            encoded = base64.b64encode(audio_bytes).decode('utf-8')
            logger.info(f'Fetched and encoded audio from URL: {url} ({len(audio_bytes) / (1024 * 1024):.2f} MB, {mime_type})')
            return (encoded, mime_type)

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI Response API with unified MCP/non-MCP processing."""
        agent_id = kwargs.get('agent_id', None)
        log_backend_activity(self.get_provider_name(), 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        try:
            async with self:
                client = self._create_client(**kwargs)
                try:
                    use_mcp = bool(self._mcp_functions)
                    async for chunk in self.yield_mcp_status_chunks(use_mcp):
                        yield chunk
                    if use_mcp:
                        logger.info('Using recursive MCP execution mode')
                        current_messages = self._trim_message_history(messages.copy())
                        async for chunk in self._stream_with_mcp_tools(current_messages, tools, client, **kwargs):
                            yield chunk
                    else:
                        logger.info('Using no-MCP mode')
                        async for chunk in self._stream_without_mcp_tools(messages, tools, client, **kwargs):
                            yield chunk
                except Exception as e:
                    if isinstance(e, (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError)):
                        await self._record_mcp_circuit_breaker_failure(e, agent_id)
                        async for chunk in self._stream_handle_mcp_exceptions(e, messages, tools, client, **kwargs):
                            yield chunk
                    else:
                        logger.error(f'Streaming error: {e}')
                        yield StreamChunk(type='error', error=str(e))
                finally:
                    await self._cleanup_client(client)
        except Exception as e:
            try:
                client = self._create_client(**kwargs)
                if isinstance(e, (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError)):
                    async for chunk in self._stream_handle_mcp_exceptions(e, messages, tools, client, **kwargs):
                        yield chunk
                else:
                    if self.mcp_servers:
                        yield StreamChunk(type='mcp_status', status='mcp_unavailable', content=f'⚠️ [MCP] Setup failed; continuing without MCP ({e})', source='mcp_setup')
                    async for chunk in self._stream_without_mcp_tools(messages, tools, client, **kwargs):
                        yield chunk
            except Exception as inner_e:
                logger.error(f'Streaming error during MCP setup fallback: {inner_e}')
                yield StreamChunk(type='error', error=str(inner_e))
            finally:
                await self._cleanup_client(client)

    async def _stream_without_mcp_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Simple passthrough streaming without MCP processing."""
        agent_id = kwargs.get('agent_id', None)
        all_params = {**self.config, **kwargs}
        processed_messages = await self._process_upload_files(messages, all_params)
        api_params = await self.api_params_handler.build_api_params(processed_messages, tools, all_params)
        if 'tools' in api_params:
            non_mcp_tools = []
            for tool in api_params.get('tools', []):
                if tool.get('type') == 'function':
                    name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
                    if name and name in self._mcp_function_names:
                        continue
                elif tool.get('type') == 'mcp':
                    continue
                non_mcp_tools.append(tool)
            api_params['tools'] = non_mcp_tools
        if 'openai' in self.get_provider_name().lower():
            stream = await client.responses.create(**api_params)
        elif 'claude' in self.get_provider_name().lower():
            if 'betas' in api_params:
                stream = await client.beta.messages.create(**api_params)
            else:
                stream = await client.messages.create(**api_params)
        else:
            stream = await client.chat.completions.create(**api_params)
        async for chunk in self._process_stream(stream, all_params, agent_id):
            yield chunk

    async def _stream_handle_mcp_exceptions(self, error: Exception, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Handle MCP exceptions with fallback streaming."""
        'Handle MCP errors with specific messaging and fallback to non-MCP tools.'
        async with self._stats_lock:
            self._mcp_tool_failures += 1
            call_index_snapshot = self._mcp_tool_calls_count
        if MCPErrorHandler:
            log_type, user_message, _ = MCPErrorHandler.get_error_details(error)
        else:
            log_type, user_message = ('mcp_error', '[MCP] Error occurred')
        logger.warning(f'MCP tool call #{call_index_snapshot} failed - {log_type}: {error}')
        yield StreamChunk(type='mcp_status', status='mcp_tools_failed', content=f'MCP tool call failed (call #{call_index_snapshot}): {user_message}', source='mcp_error')
        yield StreamChunk(type='content', content=f'\n⚠️  {user_message} ({error}); continuing without MCP tools\n')
        async for chunk in self._stream_without_mcp_tools(messages, tools, client, **kwargs):
            yield chunk

    def _track_mcp_function_names(self, tools: List[Dict[str, Any]]) -> None:
        """Track MCP function names for fallback filtering."""
        for tool in tools:
            if tool.get('type') == 'function':
                name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
                if name:
                    self._mcp_function_names.add(name)

    async def _check_circuit_breaker_before_execution(self) -> bool:
        """Check circuit breaker status before executing MCP functions."""
        if not (self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker and MCPSetupManager and MCPCircuitBreakerManager):
            return True
        normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
        mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers)
        filtered_servers = MCPCircuitBreakerManager.apply_circuit_breaker_filtering(mcp_tools_servers, self._mcp_tools_circuit_breaker)
        if not filtered_servers:
            logger.warning('All MCP servers blocked by circuit breaker')
            return False
        return True

    async def _record_mcp_circuit_breaker_failure(self, error: Exception, agent_id: Optional[str]=None) -> None:
        """Record MCP failure for circuit breaker if enabled."""
        if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
            try:
                normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
                mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers)
                await MCPCircuitBreakerManager.record_event(mcp_tools_servers, self._mcp_tools_circuit_breaker, 'failure', error_message=str(error), backend_name=self.backend_name, agent_id=agent_id)
            except Exception as cb_error:
                logger.warning(f'Failed to record circuit breaker failure: {cb_error}')

    async def _record_mcp_circuit_breaker_success(self, servers_to_use: List[Dict[str, Any]]) -> None:
        """Record MCP success for circuit breaker if enabled."""
        if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker and self._mcp_client and MCPCircuitBreakerManager:
            try:
                connected_server_names = self._mcp_client.get_server_names() if hasattr(self._mcp_client, 'get_server_names') else []
                if connected_server_names:
                    connected_server_configs = [server for server in servers_to_use if server.get('name') in connected_server_names]
                    if connected_server_configs:
                        await MCPCircuitBreakerManager.record_event(connected_server_configs, self._mcp_tools_circuit_breaker, 'success', backend_name=self.backend_name, agent_id=self.agent_id)
            except Exception as cb_error:
                logger.warning(f'Failed to record circuit breaker success: {cb_error}')

    def _trim_message_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trim message history to prevent unbounded growth."""
        if MCPMessageManager:
            return MCPMessageManager.trim_message_history(messages, self._max_mcp_message_history)
        return messages

    async def cleanup_mcp(self) -> None:
        """Cleanup MCP connections."""
        if self._mcp_client and MCPResourceManager:
            await MCPResourceManager.cleanup_mcp_client(self._mcp_client, backend_name=self.backend_name, agent_id=self.agent_id)
            self._mcp_client = None
            self._mcp_initialized = False
            self._mcp_functions.clear()
            self._mcp_function_names.clear()

    async def __aenter__(self) -> 'MCPBackend':
        """Async context manager entry."""
        if MCPResourceManager:
            await MCPResourceManager.setup_mcp_context_manager(self, backend_name=self.backend_name, agent_id=self.agent_id)
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        """Async context manager exit with automatic resource cleanup."""
        if MCPResourceManager:
            await MCPResourceManager.cleanup_mcp_context_manager(self, logger_instance=logger, backend_name=self.backend_name, agent_id=self.agent_id)
        return False

    def get_mcp_server_count(self) -> int:
        """Get count of stdio/streamable-http servers."""
        if not (self.mcp_servers and MCPSetupManager):
            return 0
        normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
        mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers)
        return len(mcp_tools_servers)

    def yield_mcp_status_chunks(self, use_mcp: bool) -> AsyncGenerator[StreamChunk, None]:
        """Yield MCP status chunks for connection and availability."""

        async def _generator():
            if self.mcp_servers and (not use_mcp):
                yield StreamChunk(type='mcp_status', status='mcp_unavailable', content='⚠️ [MCP] Setup failed or no tools available; continuing without MCP', source='mcp_setup')
            if use_mcp and self.mcp_servers:
                server_count = self.get_mcp_server_count()
                if server_count > 0:
                    yield StreamChunk(type='mcp_status', status='mcp_connected', content=f'✅ [MCP] Connected to {server_count} servers', source='mcp_setup')
            if use_mcp:
                yield StreamChunk(type='mcp_status', status='mcp_tools_initiated', content=f'🔧 [MCP] {len(self._mcp_functions)} tools available', source='mcp_session')
        return _generator()

    def is_mcp_tool_call(self, tool_name: str) -> bool:
        """Check if a tool call is an MCP function."""
        return tool_name in self._mcp_functions

    def get_mcp_tools_formatted(self) -> List[Dict[str, Any]]:
        """Get MCP tools formatted for specific API format."""
        if not self._mcp_functions:
            return []
        mcp_tools = []
        mcp_tools = self.formatter.format_mcp_tools(self._mcp_functions)
        self._track_mcp_function_names(mcp_tools)
        return mcp_tools

def yield_mcp_status_chunks(self, use_mcp: bool) -> AsyncGenerator[StreamChunk, None]:
    """Yield MCP status chunks for connection and availability."""

    async def _generator():
        if self.mcp_servers and (not use_mcp):
            yield StreamChunk(type='mcp_status', status='mcp_unavailable', content='⚠️ [MCP] Setup failed or no tools available; continuing without MCP', source='mcp_setup')
        if use_mcp and self.mcp_servers:
            server_count = self.get_mcp_server_count()
            if server_count > 0:
                yield StreamChunk(type='mcp_status', status='mcp_connected', content=f'✅ [MCP] Connected to {server_count} servers', source='mcp_setup')
        if use_mcp:
            yield StreamChunk(type='mcp_status', status='mcp_tools_initiated', content=f'🔧 [MCP] {len(self._mcp_functions)} tools available', source='mcp_session')
    return _generator()

class ChatCompletionsBackend(MCPBackend):
    """Complete OpenAI-compatible Chat Completions API backend.

    Can be used directly with any OpenAI-compatible provider by setting provider name.
    Supports Cerebras AI, Together AI, Fireworks AI, DeepInfra, and other compatible providers.

    Environment Variables:
        Provider-specific API keys are automatically detected based on provider name.
        See ProviderRegistry.PROVIDERS for the complete list.

    """

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.backend_name = self.get_provider_name()
        self.formatter = ChatCompletionsFormatter()
        self.api_params_handler = ChatCompletionsAPIParamsHandler(self)

    def supports_upload_files(self) -> bool:
        """Chat Completions backend supports upload_files preprocessing."""
        return True

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI Response API with unified MCP/non-MCP processing."""
        async for chunk in super().stream_with_tools(messages, tools, **kwargs):
            yield chunk

    async def _stream_with_mcp_tools(self, current_messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Recursively stream MCP responses, executing function calls as needed."""
        all_params = {**self.config, **kwargs}
        api_params = await self.api_params_handler.build_api_params(current_messages, tools, all_params)
        provider_tools = self.api_params_handler.get_provider_tools(all_params)
        if provider_tools:
            if 'tools' not in api_params:
                api_params['tools'] = []
            api_params['tools'].extend(provider_tools)
        stream = await client.chat.completions.create(**api_params)
        captured_function_calls = []
        current_tool_calls = {}
        response_completed = False
        content = ''
        async for chunk in stream:
            try:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta
                        if getattr(delta, 'content', None):
                            content_chunk = delta.content
                            content += content_chunk
                            yield StreamChunk(type='content', content=content_chunk)
                        if getattr(delta, 'tool_calls', None):
                            for tool_call_delta in delta.tool_calls:
                                index = getattr(tool_call_delta, 'index', 0)
                                if index not in current_tool_calls:
                                    current_tool_calls[index] = {'id': '', 'function': {'name': '', 'arguments': ''}}
                                if getattr(tool_call_delta, 'id', None):
                                    current_tool_calls[index]['id'] = tool_call_delta.id
                                if hasattr(tool_call_delta, 'function') and tool_call_delta.function:
                                    if getattr(tool_call_delta.function, 'name', None):
                                        current_tool_calls[index]['function']['name'] = tool_call_delta.function.name
                                    if getattr(tool_call_delta.function, 'arguments', None):
                                        current_tool_calls[index]['function']['arguments'] += tool_call_delta.function.arguments
                    if getattr(choice, 'finish_reason', None):
                        if choice.finish_reason == 'tool_calls' and current_tool_calls:
                            final_tool_calls = []
                            for index in sorted(current_tool_calls.keys()):
                                call = current_tool_calls[index]
                                function_name = call['function']['name']
                                arguments_str = call['function']['arguments']
                                arguments_str_sanitized = arguments_str if arguments_str.strip() else '{}'
                                final_tool_calls.append({'id': call['id'], 'type': 'function', 'function': {'name': function_name, 'arguments': arguments_str_sanitized}})
                            for tool_call in final_tool_calls:
                                args_value = tool_call['function']['arguments']
                                if not isinstance(args_value, str):
                                    args_value = self.formatter._serialize_tool_arguments(args_value)
                                captured_function_calls.append({'call_id': tool_call['id'], 'name': tool_call['function']['name'], 'arguments': args_value})
                            yield StreamChunk(type='tool_calls', tool_calls=final_tool_calls)
                            response_completed = True
                            break
                        elif choice.finish_reason in ['stop', 'length']:
                            response_completed = True
                            yield StreamChunk(type='done')
                            return
            except Exception as chunk_error:
                yield StreamChunk(type='error', error=f'Chunk processing error: {chunk_error}')
                continue
        if captured_function_calls and response_completed:
            non_mcp_functions = [call for call in captured_function_calls if call['name'] not in self._mcp_functions]
            if non_mcp_functions:
                logger.info(f'Non-MCP function calls detected (will be ignored in MCP execution): {[call['name'] for call in non_mcp_functions]}')
            if not await self._check_circuit_breaker_before_execution():
                yield StreamChunk(type='mcp_status', status='mcp_blocked', content='⚠️ [MCP] All servers blocked by circuit breaker', source='circuit_breaker')
                yield StreamChunk(type='done')
                return
            mcp_functions_executed = False
            updated_messages = current_messages.copy()
            if self.is_planning_mode_enabled():
                logger.info('[MCP] Planning mode enabled - blocking all MCP tool execution')
                yield StreamChunk(type='mcp_status', status='planning_mode_blocked', content='🚫 [MCP] Planning mode active - MCP tools blocked during coordination', source='planning_mode')
                yield StreamChunk(type='done')
                return
            if captured_function_calls:
                all_tool_calls = []
                for call in captured_function_calls:
                    all_tool_calls.append({'id': call['call_id'], 'type': 'function', 'function': {'name': call['name'], 'arguments': self.formatter._serialize_tool_arguments(call['arguments'])}})
                if all_tool_calls:
                    assistant_message = {'role': 'assistant', 'content': content.strip() if content.strip() else None, 'tool_calls': all_tool_calls}
                    updated_messages.append(assistant_message)
            tool_results = []
            for call in captured_function_calls:
                function_name = call['name']
                if self.is_mcp_tool_call(function_name):
                    yield StreamChunk(type='mcp_status', status='mcp_tool_called', content=f'🔧 [MCP Tool] Calling {function_name}...', source=f'mcp_{function_name}')
                    tools_info = f' ({len(self._mcp_functions)} tools available)' if self._mcp_functions else ''
                    yield StreamChunk(type='mcp_status', status='mcp_tools_initiated', content=f'MCP tool call initiated (call #{self._mcp_tool_calls_count}){tools_info}: {function_name}', source=f'mcp_{function_name}')
                    try:
                        result_str, result_obj = await self._execute_mcp_function_with_retry(function_name, call['arguments'])
                        if isinstance(result_str, str) and result_str.startswith('Error:'):
                            logger.warning(f'MCP function {function_name} failed after retries: {result_str}')
                            tool_results.append({'tool_call_id': call['call_id'], 'content': result_str, 'success': False})
                        else:
                            yield StreamChunk(type='mcp_status', status='mcp_tools_success', content=f'MCP tool call succeeded (call #{self._mcp_tool_calls_count})', source=f'mcp_{function_name}')
                            tool_results.append({'tool_call_id': call['call_id'], 'content': result_str, 'success': True, 'result_obj': result_obj})
                    except Exception as e:
                        logger.error(f'Unexpected error in MCP function execution: {e}')
                        error_msg = f'Error executing {function_name}: {str(e)}'
                        tool_results.append({'tool_call_id': call['call_id'], 'content': error_msg, 'success': False})
                        continue
                    yield StreamChunk(type='mcp_status', status='function_call', content=f'Arguments for Calling {function_name}: {call['arguments']}', source=f'mcp_{function_name}')
                    logger.info(f'Executed MCP function {function_name} (stdio/streamable-http)')
                    mcp_functions_executed = True
                else:
                    logger.info(f'Non-MCP function {function_name} detected, creating placeholder response')
                    tool_results.append({'tool_call_id': call['call_id'], 'content': f'Function {function_name} is not available in this MCP session.', 'success': False})
            for result in tool_results:
                result_text = str(result['content'])
                if result.get('success') and hasattr(result.get('result_obj'), 'content') and result['result_obj'].content:
                    obj = result['result_obj']
                    if isinstance(obj.content, list) and len(obj.content) > 0:
                        first_item = obj.content[0]
                        if hasattr(first_item, 'text'):
                            result_text = first_item.text
                yield StreamChunk(type='mcp_status', status='function_call_output', content=f'Results for Calling {function_name}: {result_text}', source=f'mcp_{function_name}')
                function_output_msg = {'role': 'tool', 'tool_call_id': result['tool_call_id'], 'content': result['content']}
                updated_messages.append(function_output_msg)
                yield StreamChunk(type='mcp_status', status='mcp_tool_response', content=f'✅ [MCP Tool] {function_name} completed', source=f'mcp_{function_name}')
            if mcp_functions_executed:
                updated_messages = self._trim_message_history(updated_messages)
                async for chunk in self._stream_with_mcp_tools(updated_messages, tools, client, **kwargs):
                    yield chunk
            else:
                yield StreamChunk(type='done')
                return
        elif response_completed:
            yield StreamChunk(type='mcp_status', status='mcp_session_complete', content='✅ [MCP] Session completed', source='mcp_session')
            return

    async def _process_stream(self, stream, all_params, agent_id) -> AsyncGenerator[StreamChunk, None]:
        """Handle standard Chat Completions API streaming format with logging."""
        content = ''
        current_tool_calls = {}
        search_sources_used = 0
        provider_name = self.get_provider_name()
        enable_web_search = all_params.get('enable_web_search', False)
        log_prefix = f'backend.{provider_name.lower().replace(' ', '_')}'
        async for chunk in stream:
            try:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta
                        if getattr(delta, 'content', None):
                            reasoning_chunk = self._handle_reasoning_transition(log_prefix, agent_id)
                            if reasoning_chunk:
                                yield reasoning_chunk
                            content_chunk = delta.content
                            content += content_chunk
                            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': content_chunk}, backend_name=provider_name)
                            log_stream_chunk(log_prefix, 'content', content_chunk, agent_id)
                            yield StreamChunk(type='content', content=content_chunk)
                        if getattr(delta, 'reasoning_content', None):
                            reasoning_active_key = '_reasoning_active'
                            setattr(self, reasoning_active_key, True)
                            thinking_delta = getattr(delta, 'reasoning_content')
                            if thinking_delta:
                                log_stream_chunk(log_prefix, 'reasoning', thinking_delta, agent_id)
                                yield StreamChunk(type='reasoning', content=thinking_delta, reasoning_delta=thinking_delta)
                        if getattr(delta, 'tool_calls', None):
                            reasoning_chunk = self._handle_reasoning_transition(log_prefix, agent_id)
                            if reasoning_chunk:
                                yield reasoning_chunk
                            for tool_call_delta in delta.tool_calls:
                                index = getattr(tool_call_delta, 'index', 0)
                                if index not in current_tool_calls:
                                    current_tool_calls[index] = {'id': '', 'function': {'name': '', 'arguments': ''}}
                                if getattr(tool_call_delta, 'id', None):
                                    current_tool_calls[index]['id'] = tool_call_delta.id
                                if hasattr(tool_call_delta, 'function') and tool_call_delta.function:
                                    if getattr(tool_call_delta.function, 'name', None):
                                        current_tool_calls[index]['function']['name'] = tool_call_delta.function.name
                                    if getattr(tool_call_delta.function, 'arguments', None):
                                        current_tool_calls[index]['function']['arguments'] += tool_call_delta.function.arguments
                    if getattr(choice, 'finish_reason', None):
                        reasoning_chunk = self._handle_reasoning_transition(log_prefix, agent_id)
                        if reasoning_chunk:
                            yield reasoning_chunk
                        if choice.finish_reason == 'tool_calls' and current_tool_calls:
                            final_tool_calls = []
                            for index in sorted(current_tool_calls.keys()):
                                call = current_tool_calls[index]
                                function_name = call['function']['name']
                                arguments_str = call['function']['arguments']
                                arguments_str_sanitized = arguments_str if arguments_str.strip() else '{}'
                                final_tool_calls.append({'id': call['id'], 'type': 'function', 'function': {'name': function_name, 'arguments': arguments_str_sanitized}})
                            log_stream_chunk(log_prefix, 'tool_calls', final_tool_calls, agent_id)
                            yield StreamChunk(type='tool_calls', tool_calls=final_tool_calls)
                            complete_message = {'role': 'assistant', 'content': content.strip(), 'tool_calls': final_tool_calls}
                            yield StreamChunk(type='complete_message', complete_message=complete_message)
                            log_stream_chunk(log_prefix, 'done', None, agent_id)
                            yield StreamChunk(type='done')
                            return
                        elif choice.finish_reason in ['stop', 'length']:
                            if search_sources_used > 0:
                                search_complete_msg = f'\n✅ [Live Search Complete] Used {search_sources_used} sources\n'
                                log_stream_chunk(log_prefix, 'content', search_complete_msg, agent_id)
                                yield StreamChunk(type='content', content=search_complete_msg)
                            if hasattr(chunk, 'citations') and chunk.citations:
                                if enable_web_search:
                                    citation_text = '\n📚 **Citations:**\n'
                                    for i, citation in enumerate(chunk.citations, 1):
                                        citation_text += f'{i}. {citation}\n'
                                    log_stream_chunk(log_prefix, 'content', citation_text, agent_id)
                                    yield StreamChunk(type='content', content=citation_text)
                            complete_message = {'role': 'assistant', 'content': content.strip()}
                            yield StreamChunk(type='complete_message', complete_message=complete_message)
                            log_stream_chunk(log_prefix, 'done', None, agent_id)
                            yield StreamChunk(type='done')
                            return
                if hasattr(chunk, 'usage') and chunk.usage:
                    if getattr(chunk.usage, 'num_sources_used', 0) > 0:
                        search_sources_used = chunk.usage.num_sources_used
                        if enable_web_search:
                            search_msg = f'\n📊 [Live Search] Using {search_sources_used} sources for real-time data\n'
                            log_stream_chunk(log_prefix, 'content', search_msg, agent_id)
                            yield StreamChunk(type='content', content=search_msg)
            except Exception as chunk_error:
                error_msg = f'Chunk processing error: {chunk_error}'
                log_stream_chunk(log_prefix, 'error', error_msg, agent_id)
                yield StreamChunk(type='error', error=error_msg)
                continue
        log_stream_chunk(log_prefix, 'done', None, agent_id)
        yield StreamChunk(type='done')

    def create_tool_result_message(self, tool_call: Dict[str, Any], result_content: str) -> Dict[str, Any]:
        """Create tool result message for Chat Completions format."""
        tool_call_id = self.extract_tool_call_id(tool_call)
        return {'role': 'tool', 'tool_call_id': tool_call_id, 'content': result_content}

    def extract_tool_result_content(self, tool_result_message: Dict[str, Any]) -> str:
        """Extract content from Chat Completions tool result message."""
        return tool_result_message.get('content', '')

    def _convert_messages_for_mcp_chat_completions(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages for MCP Chat Completions format if needed."""
        converted_messages = []
        for message in messages:
            if message.get('type') == 'function_call_output':
                converted_message = {'role': 'tool', 'tool_call_id': message.get('call_id'), 'content': message.get('output', '')}
                converted_messages.append(converted_message)
            else:
                converted_messages.append(message.copy())
        return converted_messages

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        if 'provider' in self.config:
            return self.config['provider']
        elif 'provider_name' in self.config:
            return self.config['provider_name']
        base_url = self.config.get('base_url', '')
        if 'openai.com' in base_url:
            return 'OpenAI'
        elif 'cerebras.ai' in base_url:
            return 'Cerebras AI'
        elif 'together.xyz' in base_url:
            return 'Together AI'
        elif 'fireworks.ai' in base_url:
            return 'Fireworks AI'
        elif 'groq.com' in base_url:
            return 'Groq'
        elif 'openrouter.ai' in base_url:
            return 'OpenRouter'
        elif 'z.ai' in base_url or 'bigmodel.cn' in base_url:
            return 'ZAI'
        elif 'nebius.com' in base_url:
            return 'Nebius AI Studio'
        elif 'moonshot.ai' in base_url or 'moonshot.cn' in base_url:
            return 'Kimi'
        elif 'poe.com' in base_url:
            return 'POE'
        elif 'aliyuncs.com' in base_url:
            return 'Qwen'
        else:
            return 'ChatCompletion'

    def get_filesystem_support(self) -> FilesystemSupport:
        """Chat Completions supports filesystem through MCP servers."""
        return FilesystemSupport.MCP

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by this provider."""
        return []

    def _create_client(self, **kwargs) -> AsyncOpenAI:
        """Create OpenAI client with consistent configuration."""
        import openai
        all_params = {**self.config, **kwargs}
        base_url = all_params.get('base_url', 'https://api.openai.com/v1')
        return openai.AsyncOpenAI(api_key=self.api_key, base_url=base_url)

    def _handle_reasoning_transition(self, log_prefix: str, agent_id: Optional[str]) -> Optional[StreamChunk]:
        """Handle reasoning state transition and return StreamChunk if transition occurred."""
        reasoning_active_key = '_reasoning_active'
        if hasattr(self, reasoning_active_key):
            if getattr(self, reasoning_active_key) is True:
                setattr(self, reasoning_active_key, False)
                log_stream_chunk(log_prefix, 'reasoning_done', '', agent_id)
                return StreamChunk(type='reasoning_done', content='')
        return None

def _handle_reasoning_transition(self, log_prefix: str, agent_id: Optional[str]) -> Optional[StreamChunk]:
    """Handle reasoning state transition and return StreamChunk if transition occurred."""
    reasoning_active_key = '_reasoning_active'
    if hasattr(self, reasoning_active_key):
        if getattr(self, reasoning_active_key) is True:
            setattr(self, reasoning_active_key, False)
            log_stream_chunk(log_prefix, 'reasoning_done', '', agent_id)
            return StreamChunk(type='reasoning_done', content='')
    return None

class ExternalAgentBackend(LLMBackend):
    """
    Backend for integrating external agent frameworks through adapters.

    This backend acts as a bridge between MassGen's orchestration system
    and external agent frameworks like AG2 (AutoGen), LangChain, etc.
    """

    def __init__(self, adapter_type: str, api_key: Optional[str]=None, **kwargs):
        """
        Initialize external agent backend.

        Args:
            adapter_type: Framework/adapter type (e.g., "ag2", "langchain")
            api_key: Optional API key for frameworks that need it
            **kwargs: Framework-specific configuration
        """
        self.adapter_type = adapter_type.lower()
        if self.adapter_type not in adapter_registry:
            raise ValueError(f'Unsupported framework: {self.adapter_type}. Supported frameworks: {', '.join(adapter_registry.keys())}')
        adapter_class = adapter_registry[self.adapter_type]
        adapter_config = self._extract_adapter_config(kwargs)
        self.adapter = adapter_class(**adapter_config)
        super().__init__(api_key=api_key, **kwargs)

    def _extract_adapter_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract framework-specific configuration."""
        excluded_params = self.get_base_excluded_config_params()
        excluded_params.update({''})
        return {k: v for k, v in config.items() if k not in excluded_params}

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from external agent with tool support.

        Args:
            messages: Conversation messages
            tools: Available tools
            **kwargs: Additional parameters

        Yields:
            StreamChunk: Response chunks
        """
        if self.coordination_stage:
            self.adapter.set_stage(self.coordination_stage)
        async for chunk in self.adapter.execute_streaming(messages, tools, **kwargs):
            yield chunk

    def get_provider_name(self) -> str:
        """Get provider name."""
        return f'{self.adapter_type}'

    def get_filesystem_support(self) -> FilesystemSupport:
        """
        External agents typically use MCP for filesystem operations.

        Some frameworks may have their own filesystem tools, but we
        standardize on MCP for consistency.
        """
        if hasattr(self.adapter, 'get_filesystem_support'):
            return self.adapter.get_filesystem_support()
        return FilesystemSupport.MCP

    def is_stateful(self) -> bool:
        """Check if this backend maintains conversation state."""
        if hasattr(self.adapter, 'is_stateful'):
            return self.adapter.is_stateful()
        return False

    def clear_history(self) -> None:
        """Clear conversation history."""
        if hasattr(self.adapter, 'clear_history'):
            self.adapter.clear_history()

    def reset_state(self) -> None:
        """Reset backend state."""
        if hasattr(self.adapter, 'reset_state'):
            self.adapter.reset_state()

def is_stateful(self) -> bool:
    """Check if this backend maintains conversation state."""
    if hasattr(self.adapter, 'is_stateful'):
        return self.adapter.is_stateful()
    return False

def clear_history(self) -> None:
    """Clear conversation history."""
    if hasattr(self.adapter, 'clear_history'):
        self.adapter.clear_history()

def reset_state(self) -> None:
    """Reset backend state."""
    if hasattr(self.adapter, 'reset_state'):
        self.adapter.reset_state()

class ResponseBackend(MCPBackend):
    """Backend using the standard Response API format with multimodal support."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.formatter = ResponseFormatter()
        self.api_params_handler = ResponseAPIParamsHandler(self)
        self._pending_image_saves = []
        self._vector_store_ids: List[str] = []
        self._uploaded_file_ids: List[str] = []

    def supports_upload_files(self) -> bool:
        return True

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI Response API with unified MCP/non-MCP processing.

        Wraps parent implementation to ensure File Search cleanup happens after streaming completes.
        """
        try:
            async for chunk in super().stream_with_tools(messages, tools, **kwargs):
                yield chunk
        finally:
            await self._cleanup_file_search_if_needed(**kwargs)

    async def _cleanup_file_search_if_needed(self, **kwargs) -> None:
        """Cleanup File Search resources if needed."""
        if not (self._vector_store_ids or self._uploaded_file_ids):
            return
        agent_id = kwargs.get('agent_id')
        logger.info('Cleaning up File Search resources...')
        client = None
        try:
            client = self._create_client(**kwargs)
            await self._cleanup_file_search_resources(client, agent_id)
        except Exception as cleanup_error:
            logger.error(f'Error during File Search cleanup: {cleanup_error}', extra={'agent_id': agent_id})
        finally:
            if client and hasattr(client, 'aclose'):
                try:
                    await client.aclose()
                except Exception:
                    pass

    async def _stream_without_mcp_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        agent_id = kwargs.get('agent_id')
        all_params = {**self.config, **kwargs}
        processed_messages = await self._process_upload_files(messages, all_params)
        if all_params.get('_has_file_search_files'):
            logger.info('Processing File Search uploads...')
            processed_messages, vector_store_id = await self._upload_files_and_create_vector_store(processed_messages, client, agent_id)
            if vector_store_id:
                existing_ids = list(all_params.get('_file_search_vector_store_ids', []))
                existing_ids.append(vector_store_id)
                all_params['_file_search_vector_store_ids'] = existing_ids
                logger.info(f'File Search enabled with vector store: {vector_store_id}')
            all_params.pop('_has_file_search_files', None)
        api_params = await self.api_params_handler.build_api_params(processed_messages, tools, all_params)
        if 'tools' in api_params:
            non_mcp_tools = []
            for tool in api_params.get('tools', []):
                if tool.get('type') == 'function':
                    name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
                    if name and name in self._mcp_function_names:
                        continue
                elif tool.get('type') == 'mcp':
                    continue
                non_mcp_tools.append(tool)
            api_params['tools'] = non_mcp_tools
        stream = await client.responses.create(**api_params)
        async for chunk in self._process_stream(stream, all_params, agent_id):
            yield chunk

    async def _stream_with_mcp_tools(self, current_messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Recursively stream MCP responses, executing function calls as needed."""
        agent_id = kwargs.get('agent_id')
        all_params = {**self.config, **kwargs}
        if all_params.get('_has_file_search_files'):
            logger.info('Processing File Search uploads...')
            current_messages, vector_store_id = await self._upload_files_and_create_vector_store(current_messages, client, agent_id)
            if vector_store_id:
                existing_ids = list(all_params.get('_file_search_vector_store_ids', []))
                existing_ids.append(vector_store_id)
                all_params['_file_search_vector_store_ids'] = existing_ids
                logger.info(f'File Search enabled with vector store: {vector_store_id}')
            all_params.pop('_has_file_search_files', None)
        api_params = await self.api_params_handler.build_api_params(current_messages, tools, all_params)
        stream = await client.responses.create(**api_params)
        captured_function_calls = []
        current_function_call = None
        response_completed = False
        async for chunk in stream:
            if hasattr(chunk, 'type'):
                if chunk.type == 'response.output_item.added' and hasattr(chunk, 'item') and chunk.item and (getattr(chunk.item, 'type', None) == 'function_call'):
                    current_function_call = {'call_id': getattr(chunk.item, 'call_id', ''), 'name': getattr(chunk.item, 'name', ''), 'arguments': ''}
                    logger.info(f'Function call detected: {current_function_call['name']}')
                elif chunk.type == 'response.function_call_arguments.delta' and current_function_call is not None:
                    delta = getattr(chunk, 'delta', '')
                    current_function_call['arguments'] += delta
                elif chunk.type == 'response.output_item.done' and current_function_call is not None:
                    captured_function_calls.append(current_function_call)
                    current_function_call = None
                elif chunk.type == 'response.output_text.delta':
                    delta = getattr(chunk, 'delta', '')
                    yield TextStreamChunk(type=ChunkType.CONTENT, content=delta, source='response_api')
                else:
                    result = self._process_stream_chunk(chunk, agent_id)
                    yield result
                if chunk.type == 'response.completed':
                    response_completed = True
                    if captured_function_calls:
                        break
                    else:
                        yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                        return
        if captured_function_calls and response_completed:
            non_mcp_functions = [call for call in captured_function_calls if call['name'] not in self._mcp_functions]
            if non_mcp_functions:
                logger.info(f'Non-MCP function calls detected: {[call['name'] for call in non_mcp_functions]}. Ending MCP processing.')
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                return
            if not await super()._check_circuit_breaker_before_execution():
                logger.warning('All MCP servers blocked by circuit breaker')
                yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_blocked', content='⚠️ [MCP] All servers blocked by circuit breaker', source='circuit_breaker')
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                return
            mcp_functions_executed = False
            updated_messages = current_messages.copy()
            if self.is_planning_mode_enabled():
                logger.info('[MCP] Planning mode enabled - blocking all MCP tool execution')
                yield StreamChunk(type='mcp_status', status='planning_mode_blocked', content='🚫 [MCP] Planning mode active - MCP tools blocked during coordination', source='planning_mode')
                yield StreamChunk(type='done')
                return
            processed_call_ids = set()
            for call in captured_function_calls:
                function_name = call['name']
                if function_name in self._mcp_functions:
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_tool_called', content=f'🔧 [MCP Tool] Calling {function_name}...', source=f'mcp_{function_name}')
                    try:
                        result, result_obj = await super()._execute_mcp_function_with_retry(function_name, call['arguments'])
                        if isinstance(result, str) and result.startswith('Error:'):
                            logger.warning(f'MCP function {function_name} failed after retries: {result}')
                            function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': function_name, 'arguments': call['arguments']}
                            updated_messages.append(function_call_msg)
                            error_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': result}
                            updated_messages.append(error_output_msg)
                            processed_call_ids.add(call['call_id'])
                            mcp_functions_executed = True
                            continue
                    except Exception as e:
                        logger.error(f'Unexpected error in MCP function execution: {e}')
                        error_msg = f'Error executing {function_name}: {str(e)}'
                        function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': function_name, 'arguments': call['arguments']}
                        updated_messages.append(function_call_msg)
                        error_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': error_msg}
                        updated_messages.append(error_output_msg)
                        processed_call_ids.add(call['call_id'])
                        mcp_functions_executed = True
                        continue
                    function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': function_name, 'arguments': call['arguments']}
                    updated_messages.append(function_call_msg)
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='function_call', content=f'Arguments for Calling {function_name}: {call['arguments']}', source=f'mcp_{function_name}')
                    function_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': str(result)}
                    updated_messages.append(function_output_msg)
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='function_call_output', content=f'Results for Calling {function_name}: {str(result_obj.content[0].text)}', source=f'mcp_{function_name}')
                    logger.info(f'Executed MCP function {function_name} (stdio/streamable-http)')
                    processed_call_ids.add(call['call_id'])
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_tool_response', content=f'✅ [MCP Tool] {function_name} completed', source=f'mcp_{function_name}')
                    mcp_functions_executed = True
            for call in captured_function_calls:
                if call['call_id'] not in processed_call_ids:
                    logger.warning(f'Tool call {call['call_id']} for function {call['name']} was not processed - adding error result')
                    function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': call['name'], 'arguments': call['arguments']}
                    updated_messages.append(function_call_msg)
                    error_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': f'Error: Tool call {call['call_id']} for function {call['name']} was not processed. This may indicate a validation or execution error.'}
                    updated_messages.append(error_output_msg)
                    mcp_functions_executed = True
            if mcp_functions_executed:
                updated_messages = super()._trim_message_history(updated_messages)
                async for chunk in self._stream_with_mcp_tools(updated_messages, tools, client, **kwargs):
                    yield chunk
            else:
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                return
        elif response_completed:
            yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_session_complete', content='✅ [MCP] Session completed', source='mcp_session')
            yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
            return

    async def _upload_files_and_create_vector_store(self, messages: List[Dict[str, Any]], client: AsyncOpenAI, agent_id: Optional[str]=None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Upload file_pending_upload items and create a vector store."""
        try:
            pending_files: List[Dict[str, Any]] = []
            file_locations: List[Tuple[int, int]] = []
            for message_index, message in enumerate(messages):
                content = message.get('content')
                if not isinstance(content, list):
                    continue
                for item_index, item in enumerate(content):
                    if isinstance(item, dict) and item.get('type') == 'file_pending_upload':
                        pending_files.append(item)
                        file_locations.append((message_index, item_index))
            if not pending_files:
                return (messages, None)
            uploaded_file_ids: List[str] = []
            http_client: Optional[httpx.AsyncClient] = None
            try:
                for pending in pending_files:
                    source = pending.get('source')
                    if source == 'local':
                        path_str = pending.get('path')
                        if not path_str:
                            logger.warning('Missing local path for file_pending_upload entry')
                            continue
                        file_path = Path(path_str)
                        if not file_path.exists():
                            raise UploadFileError(f'File not found for upload: {file_path}')
                        try:
                            with file_path.open('rb') as file_handle:
                                uploaded_file = await client.files.create(purpose='assistants', file=file_handle)
                        except Exception as exc:
                            raise UploadFileError(f'Failed to upload file {file_path}: {exc}') from exc
                    elif source == 'url':
                        file_url = pending.get('url')
                        if not file_url:
                            logger.warning('Missing URL for file_pending_upload entry')
                            continue
                        parsed = urlparse(file_url)
                        if parsed.scheme not in {'http', 'https'}:
                            raise UploadFileError(f'Unsupported URL scheme for file upload: {file_url}')
                        if http_client is None:
                            http_client = httpx.AsyncClient()
                        try:
                            response = await http_client.get(file_url, timeout=30.0)
                            response.raise_for_status()
                        except httpx.HTTPError as exc:
                            raise UploadFileError(f'Failed to download file from URL {file_url}: {exc}') from exc
                        filename = Path(parsed.path).name or 'remote_file'
                        file_bytes = BytesIO(response.content)
                        try:
                            uploaded_file = await client.files.create(purpose='assistants', file=(filename, file_bytes))
                        except Exception as exc:
                            raise UploadFileError(f'Failed to upload file from URL {file_url}: {exc}') from exc
                    else:
                        raise UploadFileError(f'Unknown file_pending_upload source: {source}')
                    file_id = getattr(uploaded_file, 'id', None)
                    if not file_id:
                        raise UploadFileError('Uploaded file response missing ID')
                    uploaded_file_ids.append(file_id)
                    self._uploaded_file_ids.append(file_id)
                    logger.info(f'Uploaded file for File Search (file_id={file_id})')
            finally:
                if http_client is not None:
                    await http_client.aclose()
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            vector_store_name = f'massgen_file_search_{agent_id or 'default'}_{timestamp}'
            try:
                vector_store = await client.vector_stores.create(name=vector_store_name)
            except Exception as exc:
                raise UploadFileError(f'Failed to create vector store: {exc}') from exc
            vector_store_id = getattr(vector_store, 'id', None)
            if not vector_store_id:
                raise UploadFileError('Vector store response missing ID')
            self._vector_store_ids.append(vector_store_id)
            logger.info('Created vector store for File Search', extra={'vector_store_id': vector_store_id, 'file_count': len(uploaded_file_ids)})
            for file_id in uploaded_file_ids:
                try:
                    vs_file = await client.vector_stores.files.create_and_poll(vector_store_id=vector_store_id, file_id=file_id)
                    logger.info('File indexed and attached to vector store', extra={'vector_store_id': vector_store_id, 'file_id': file_id, 'status': getattr(vs_file, 'status', None)})
                except Exception as exc:
                    raise UploadFileError(f'Failed to attach and index file {file_id} to vector store {vector_store_id}: {exc}') from exc
            if uploaded_file_ids:
                logger.info('All files indexed for File Search; waiting 2s for vector store to stabilize', extra={'vector_store_id': vector_store_id, 'file_count': len(uploaded_file_ids)})
                await asyncio.sleep(2)
            updated_messages = []
            for message in messages:
                cloned = dict(message)
                if isinstance(message.get('content'), list):
                    cloned['content'] = [dict(item) if isinstance(item, dict) else item for item in message['content']]
                updated_messages.append(cloned)
            for message_index, item_index in reversed(file_locations):
                content_list = updated_messages[message_index].get('content')
                if isinstance(content_list, list):
                    content_list.pop(item_index)
                    if not content_list:
                        content_list.append({'type': 'text', 'text': '[Files uploaded for search integration]'})
            return (updated_messages, vector_store_id)
        except Exception as error:
            logger.warning(f'File Search upload failed: {error}. Continuing without file search.')
            return (messages, None)

    async def _cleanup_file_search_resources(self, client: AsyncOpenAI, agent_id: Optional[str]=None) -> None:
        """Clean up File Search vector stores and uploaded files."""
        for vector_store_id in list(self._vector_store_ids):
            try:
                await client.vector_stores.delete(vector_store_id)
                logger.info('Deleted File Search vector store', extra={'vector_store_id': vector_store_id, 'agent_id': agent_id})
            except Exception as exc:
                logger.warning(f'Failed to delete vector store {vector_store_id}: {exc}', extra={'agent_id': agent_id})
        for file_id in list(self._uploaded_file_ids):
            try:
                await client.files.delete(file_id)
                logger.debug('Deleted File Search uploaded file', extra={'file_id': file_id, 'agent_id': agent_id})
            except Exception as exc:
                logger.warning(f'Failed to delete file {file_id}: {exc}', extra={'agent_id': agent_id})
        self._vector_store_ids.clear()
        self._uploaded_file_ids.clear()

    def _convert_mcp_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools (stdio + streamable-http) to OpenAI function declarations."""
        if not self._mcp_functions:
            return []
        converted_tools = []
        for function in self._mcp_functions.values():
            converted_tools.append(function.to_openai_format())
        logger.debug(f'Converted {len(converted_tools)} MCP tools (stdio + streamable-http) to OpenAI format')
        return converted_tools

    async def _process_stream(self, stream, all_params, agent_id=None):
        async for chunk in stream:
            processed = self._process_stream_chunk(chunk, agent_id)
            if processed.type == 'complete_response':
                yield processed
                log_stream_chunk('backend.response', 'done', None, agent_id)
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
            else:
                yield processed

    def _process_stream_chunk(self, chunk, agent_id) -> Union[TextStreamChunk, StreamChunk]:
        """
        Process individual stream chunks and convert to appropriate chunk format.

        Returns TextStreamChunk for text/reasoning/tool content,
        or legacy StreamChunk for backward compatibility.
        """
        if not hasattr(chunk, 'type'):
            return StreamChunk(type='content', content='')
        chunk_type = chunk.type
        if chunk_type == 'response.output_text.delta' and hasattr(chunk, 'delta'):
            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': chunk.delta}, backend_name=self.get_provider_name())
            log_stream_chunk('backend.response', 'content', chunk.delta, agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content=chunk.delta, source='response_api')
        elif chunk_type == 'response.reasoning_text.delta' and hasattr(chunk, 'delta'):
            log_stream_chunk('backend.response', 'reasoning', chunk.delta, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING, content=f'🧠 [Reasoning] {chunk.delta}', reasoning_delta=chunk.delta, item_id=getattr(chunk, 'item_id', None), content_index=getattr(chunk, 'content_index', None), source='response_api')
        elif chunk_type == 'response.reasoning_text.done':
            reasoning_text = getattr(chunk, 'text', '')
            log_stream_chunk('backend.response', 'reasoning_done', reasoning_text, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING_DONE, content='\n🧠 [Reasoning Complete]\n', reasoning_text=reasoning_text, item_id=getattr(chunk, 'item_id', None), content_index=getattr(chunk, 'content_index', None), source='response_api')
        elif chunk_type == 'response.reasoning_summary_text.delta' and hasattr(chunk, 'delta'):
            log_stream_chunk('backend.response', 'reasoning_summary', chunk.delta, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING_SUMMARY, content=chunk.delta, reasoning_summary_delta=chunk.delta, item_id=getattr(chunk, 'item_id', None), summary_index=getattr(chunk, 'summary_index', None), source='response_api')
        elif chunk_type == 'response.reasoning_summary_text.done':
            summary_text = getattr(chunk, 'text', '')
            log_stream_chunk('backend.response', 'reasoning_summary_done', summary_text, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING_SUMMARY_DONE, content='\n📋 [Reasoning Summary Complete]\n', reasoning_summary_text=summary_text, item_id=getattr(chunk, 'item_id', None), summary_index=getattr(chunk, 'summary_index', None), source='response_api')
        elif chunk_type == 'response.file_search_call.in_progress':
            item_id = getattr(chunk, 'item_id', None)
            output_index = getattr(chunk, 'output_index', None)
            log_stream_chunk('backend.response', 'file_search', 'Starting file search', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n📁 [File Search] Starting search...', item_id=item_id, content_index=output_index, source='response_api')
        elif chunk_type == 'response.file_search_call.searching':
            item_id = getattr(chunk, 'item_id', None)
            output_index = getattr(chunk, 'output_index', None)
            queries = getattr(chunk, 'queries', None)
            query_text = ''
            if queries:
                try:
                    if isinstance(queries, (list, tuple)):
                        query_text = ', '.join((str(q) for q in queries if q))
                    else:
                        query_text = str(queries)
                except Exception:
                    query_text = ''
            message = '\n📁 [File Search] Searching...'
            if query_text:
                message += f' Query: {query_text}'
            log_stream_chunk('backend.response', 'file_search', f'Searching files{(f' for {query_text}' if query_text else '')}', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content=message, item_id=item_id, content_index=output_index, source='response_api')
        elif chunk_type == 'response.file_search_call.completed':
            item_id = getattr(chunk, 'item_id', None)
            output_index = getattr(chunk, 'output_index', None)
            results = getattr(chunk, 'results', None)
            if results is None:
                results = getattr(chunk, 'search_results', None)
            queries = getattr(chunk, 'queries', None)
            query_text = ''
            if queries:
                try:
                    if isinstance(queries, (list, tuple)):
                        query_text = ', '.join((str(q) for q in queries if q))
                    else:
                        query_text = str(queries)
                except Exception:
                    query_text = ''
            if results is not None:
                try:
                    result_count = len(results)
                except Exception:
                    result_count = None
            else:
                result_count = None
            message_parts = ['\n✅ [File Search] Completed']
            if query_text:
                message_parts.append(f'Query: {query_text}')
            if result_count is not None:
                message_parts.append(f'Results: {result_count}')
            message = ' '.join(message_parts)
            log_stream_chunk('backend.response', 'file_search', f'Completed file search{(f' for {query_text}' if query_text else '')}{(f' with {result_count} results' if result_count is not None else '')}', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content=message, item_id=item_id, content_index=output_index, source='response_api')
        elif chunk_type == 'response.web_search_call.in_progress':
            log_stream_chunk('backend.response', 'web_search', 'Starting search', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🔍 [Provider Tool: Web Search] Starting search...', source='response_api')
        elif chunk_type == 'response.web_search_call.searching':
            log_stream_chunk('backend.response', 'web_search', 'Searching', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🔍 [Provider Tool: Web Search] Searching...', source='response_api')
        elif chunk_type == 'response.web_search_call.completed':
            log_stream_chunk('backend.response', 'web_search', 'Search completed', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Provider Tool: Web Search] Search completed', source='response_api')
        elif chunk_type == 'response.code_interpreter_call.in_progress':
            log_stream_chunk('backend.response', 'code_interpreter', 'Starting execution', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n💻 [Provider Tool: Code Interpreter] Starting execution...', source='response_api')
        elif chunk_type == 'response.code_interpreter_call.executing':
            log_stream_chunk('backend.response', 'code_interpreter', 'Executing', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n💻 [Provider Tool: Code Interpreter] Executing...', source='response_api')
        elif chunk_type == 'response.code_interpreter_call.completed':
            log_stream_chunk('backend.response', 'code_interpreter', 'Execution completed', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Provider Tool: Code Interpreter] Execution completed', source='response_api')
        elif chunk_type == 'response.image_generation_call.in_progress':
            log_stream_chunk('backend.response', 'image_generation', 'Starting image generation', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🎨 [Provider Tool: Image Generation] Starting generation...', source='response_api')
        elif chunk_type == 'response.image_generation_call.generating':
            log_stream_chunk('backend.response', 'image_generation', 'Generating image', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🎨 [Provider Tool: Image Generation] Generating image...', source='response_api')
        elif chunk_type == 'response.image_generation_call.completed':
            log_stream_chunk('backend.response', 'image_generation', 'Image generation completed', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Provider Tool: Image Generation] Image generated successfully', source='response_api')
        elif chunk_type == 'image_generation.completed':
            if hasattr(chunk, 'b64_json'):
                log_stream_chunk('backend.response', 'image_generation', 'Image data received', agent_id)
                return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Image Generation] Image successfully created', source='response_api')
        elif chunk.type == 'response.output_item.done':
            if hasattr(chunk, 'item') and chunk.item:
                if hasattr(chunk.item, 'type') and chunk.item.type == 'web_search_call':
                    if hasattr(chunk.item, 'action') and 'query' in chunk.item.action:
                        search_query = chunk.item.action['query']
                        if search_query:
                            log_stream_chunk('backend.response', 'search_query', search_query, agent_id)
                            return TextStreamChunk(type=ChunkType.CONTENT, content=f"\n🔍 [Search Query] '{search_query}'\n", source='response_api')
                elif hasattr(chunk.item, 'type') and chunk.item.type == 'code_interpreter_call':
                    if hasattr(chunk.item, 'code') and chunk.item.code:
                        log_stream_chunk('backend.response', 'code_executed', chunk.item.code, agent_id)
                        return TextStreamChunk(type=ChunkType.CONTENT, content=f'💻 [Code Executed]\n```\n{chunk.item.code}\n```\n', source='response_api')
                    if hasattr(chunk.item, 'outputs') and chunk.item.outputs:
                        for output in chunk.item.outputs:
                            output_text = None
                            if hasattr(output, 'text') and output.text:
                                output_text = output.text
                            elif hasattr(output, 'content') and output.content:
                                output_text = output.content
                            elif hasattr(output, 'data') and output.data:
                                output_text = str(output.data)
                            elif isinstance(output, str):
                                output_text = output
                            elif isinstance(output, dict):
                                if 'text' in output:
                                    output_text = output['text']
                                elif 'content' in output:
                                    output_text = output['content']
                                elif 'data' in output:
                                    output_text = str(output['data'])
                            if output_text and output_text.strip():
                                log_stream_chunk('backend.response', 'code_result', output_text.strip(), agent_id)
                                return TextStreamChunk(type=ChunkType.CONTENT, content=f'📊 [Result] {output_text.strip()}\n', source='response_api')
                elif hasattr(chunk.item, 'type') and chunk.item.type == 'image_generation_call':
                    if hasattr(chunk.item, 'action') and chunk.item.action:
                        prompt = chunk.item.action.get('prompt', '')
                        size = chunk.item.action.get('size', '1024x1024')
                        if prompt:
                            log_stream_chunk('backend.response', 'image_prompt', prompt, agent_id)
                            return TextStreamChunk(type=ChunkType.CONTENT, content=f"\n🎨 [Image Generated] Prompt: '{prompt}' (Size: {size})\n", source='response_api')
        elif chunk_type == 'response.mcp_list_tools.started':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n🔧 [MCP] Listing available tools...', source='response_api')
        elif chunk_type == 'response.mcp_list_tools.completed':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n✅ [MCP] Tool listing completed', source='response_api')
        elif chunk_type == 'response.mcp_list_tools.failed':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n❌ [MCP] Tool listing failed', source='response_api')
        elif chunk_type == 'response.mcp_call.started':
            tool_name = getattr(chunk, 'tool_name', 'unknown')
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content=f"\n🔧 [MCP] Calling tool '{tool_name}'...", source='response_api')
        elif chunk_type == 'response.mcp_call.in_progress':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n⏳ [MCP] Tool execution in progress...', source='response_api')
        elif chunk_type == 'response.mcp_call.completed':
            tool_name = getattr(chunk, 'tool_name', 'unknown')
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content=f"\n✅ [MCP] Tool '{tool_name}' completed", source='response_api')
        elif chunk_type == 'response.mcp_call.failed':
            tool_name = getattr(chunk, 'tool_name', 'unknown')
            error_msg = getattr(chunk, 'error', 'unknown error')
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content=f"\n❌ [MCP] Tool '{tool_name}' failed: {error_msg}", source='response_api')
        elif chunk.type == 'response.completed':
            if hasattr(chunk, 'response'):
                response_dict = self._convert_to_dict(chunk.response)
                if isinstance(response_dict, dict) and 'output' in response_dict:
                    for item in response_dict['output']:
                        if item.get('type') == 'code_interpreter_call':
                            status = item.get('status', 'unknown')
                            code = item.get('code', '')
                            outputs = item.get('outputs')
                            content = f'\n🔧 Code Interpreter [{status.title()}]'
                            if code:
                                content += f': {code}'
                            if outputs:
                                content += f' → {outputs}'
                            log_stream_chunk('backend.response', 'code_interpreter_result', content, agent_id)
                            return TextStreamChunk(type=ChunkType.CONTENT, content=content, source='response_api')
                        elif item.get('type') == 'web_search_call':
                            status = item.get('status', 'unknown')
                            query = item.get('action', {}).get('query', '')
                            results = item.get('results')
                            if query:
                                content = f'\n🔧 Web Search [{status.title()}]: {query}'
                                if results:
                                    content += f' → Found {len(results)} results'
                                log_stream_chunk('backend.response', 'web_search_result', content, agent_id)
                                return TextStreamChunk(type=ChunkType.CONTENT, content=content, source='response_api')
                        elif item.get('type') == 'image_generation_call':
                            status = item.get('status', 'unknown')
                            action = item.get('action', {})
                            prompt = action.get('prompt', '')
                            size = action.get('size', '1024x1024')
                            if prompt:
                                content = f'\n🔧 Image Generation [{status.title()}]: {prompt} (Size: {size})'
                                log_stream_chunk('backend.response', 'image_generation_result', content, agent_id)
                                return TextStreamChunk(type=ChunkType.CONTENT, content=content, source='response_api')
                log_stream_chunk('backend.response', 'complete_response', 'Response completed', agent_id)
                return TextStreamChunk(type=ChunkType.COMPLETE_RESPONSE, response=response_dict, source='response_api')
        return StreamChunk(type='content', content='')

    def create_tool_result_message(self, tool_call: Dict[str, Any], result_content: str) -> Dict[str, Any]:
        """Create tool result message for OpenAI Responses API format."""
        tool_call_id = self.extract_tool_call_id(tool_call)
        return {'type': 'function_call_output', 'call_id': tool_call_id, 'output': result_content}

    def extract_tool_result_content(self, tool_result_message: Dict[str, Any]) -> str:
        """Extract content from OpenAI Responses API tool result message."""
        return tool_result_message.get('output', '')

    def _create_client(self, **kwargs) -> AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=self.api_key)

    def _convert_to_dict(self, obj) -> Dict[str, Any]:
        """Convert any object to dictionary with multiple fallback methods."""
        try:
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            else:
                return dict(obj)
        except Exception:
            return {key: getattr(obj, key, None) for key in dir(obj) if not key.startswith('_') and (not callable(getattr(obj, key, None)))}

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return 'OpenAI'

    def get_filesystem_support(self) -> FilesystemSupport:
        """OpenAI supports filesystem through MCP servers."""
        return FilesystemSupport.MCP

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by OpenAI."""
        return ['web_search', 'code_interpreter']

def _convert_to_dict(self, obj) -> Dict[str, Any]:
    """Convert any object to dictionary with multiple fallback methods."""
    try:
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        else:
            return dict(obj)
    except Exception:
        return {key: getattr(obj, key, None) for key in dir(obj) if not key.startswith('_') and (not callable(getattr(obj, key, None)))}

class MCPResponseExtractor:
    """
    Extracts MCP tool calls and responses from Gemini SDK stream chunks.

    This class parses the internal SDK chunks to capture:
    - function_call parts (tool invocations)
    - function_response parts (tool results)
    - Paired call-response data for tracking complete tool executions
    """

    def __init__(self):
        """Initialize the extractor with empty storage."""
        self.mcp_calls = []
        self.mcp_responses = []
        self.call_response_pairs = []
        self._pending_call = None

    def extract_function_call(self, function_call) -> Optional[Dict[str, Any]]:
        """
        Extract tool call information from SDK function_call object.

        Tries multiple methods to extract data from different SDK versions:
        1. Direct attributes (name, args)
        2. Dictionary-like interface (get method)
        3. __dict__ attributes
        4. Protobuf _pb attributes
        """
        tool_name = None
        tool_args = None
        tool_name = getattr(function_call, 'name', None)
        tool_args = getattr(function_call, 'args', None)
        if tool_name is None:
            try:
                if hasattr(function_call, 'get'):
                    tool_name = function_call.get('name', None)
                    tool_args = function_call.get('args', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_call, '__dict__'):
                    fc_dict = function_call.__dict__
                    tool_name = fc_dict.get('name', None)
                    tool_args = fc_dict.get('args', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_call, '_pb'):
                    pb = function_call._pb
                    if hasattr(pb, 'name'):
                        tool_name = pb.name
                    if hasattr(pb, 'args'):
                        tool_args = pb.args
            except Exception:
                pass
        if tool_name:
            call_data = {'name': tool_name, 'arguments': tool_args or {}, 'timestamp': time.time(), 'raw': str(function_call)[:200]}
            self.mcp_calls.append(call_data)
            self._pending_call = call_data
            return call_data
        return None

    def extract_function_response(self, function_response) -> Optional[Dict[str, Any]]:
        """
        Extract tool response information from SDK function_response object.

        Uses same extraction methods as function_call for consistency.
        """
        tool_name = None
        tool_response = None
        tool_name = getattr(function_response, 'name', None)
        tool_response = getattr(function_response, 'response', None)
        if tool_name is None:
            try:
                if hasattr(function_response, 'get'):
                    tool_name = function_response.get('name', None)
                    tool_response = function_response.get('response', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_response, '__dict__'):
                    fr_dict = function_response.__dict__
                    tool_name = fr_dict.get('name', None)
                    tool_response = fr_dict.get('response', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_response, '_pb'):
                    pb = function_response._pb
                    if hasattr(pb, 'name'):
                        tool_name = pb.name
                    if hasattr(pb, 'response'):
                        tool_response = pb.response
            except Exception:
                pass
        if tool_name:
            response_data = {'name': tool_name, 'response': tool_response or {}, 'timestamp': time.time(), 'raw': str(function_response)[:500]}
            self.mcp_responses.append(response_data)
            if self._pending_call and self._pending_call['name'] == tool_name:
                self.call_response_pairs.append({'call': self._pending_call, 'response': response_data, 'duration': response_data['timestamp'] - self._pending_call['timestamp'], 'paired_at': time.time()})
                self._pending_call = None
            return response_data
        return None

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all extracted MCP tool interactions.
        """
        return {'total_calls': len(self.mcp_calls), 'total_responses': len(self.mcp_responses), 'paired_interactions': len(self.call_response_pairs), 'pending_call': self._pending_call is not None, 'tool_names': list(set((call['name'] for call in self.mcp_calls))), 'average_duration': sum((pair['duration'] for pair in self.call_response_pairs)) / len(self.call_response_pairs) if self.call_response_pairs else 0}

    def clear(self):
        """Clear all stored data."""
        self.mcp_calls.clear()
        self.mcp_responses.clear()
        self.call_response_pairs.clear()
        self._pending_call = None

def extract_function_call(self, function_call) -> Optional[Dict[str, Any]]:
    """
        Extract tool call information from SDK function_call object.

        Tries multiple methods to extract data from different SDK versions:
        1. Direct attributes (name, args)
        2. Dictionary-like interface (get method)
        3. __dict__ attributes
        4. Protobuf _pb attributes
        """
    tool_name = None
    tool_args = None
    tool_name = getattr(function_call, 'name', None)
    tool_args = getattr(function_call, 'args', None)
    if tool_name is None:
        try:
            if hasattr(function_call, 'get'):
                tool_name = function_call.get('name', None)
                tool_args = function_call.get('args', None)
        except Exception:
            pass
    if tool_name is None:
        try:
            if hasattr(function_call, '__dict__'):
                fc_dict = function_call.__dict__
                tool_name = fc_dict.get('name', None)
                tool_args = fc_dict.get('args', None)
        except Exception:
            pass
    if tool_name is None:
        try:
            if hasattr(function_call, '_pb'):
                pb = function_call._pb
                if hasattr(pb, 'name'):
                    tool_name = pb.name
                if hasattr(pb, 'args'):
                    tool_args = pb.args
        except Exception:
            pass
    if tool_name:
        call_data = {'name': tool_name, 'arguments': tool_args or {}, 'timestamp': time.time(), 'raw': str(function_call)[:200]}
        self.mcp_calls.append(call_data)
        self._pending_call = call_data
        return call_data
    return None

def extract_function_response(self, function_response) -> Optional[Dict[str, Any]]:
    """
        Extract tool response information from SDK function_response object.

        Uses same extraction methods as function_call for consistency.
        """
    tool_name = None
    tool_response = None
    tool_name = getattr(function_response, 'name', None)
    tool_response = getattr(function_response, 'response', None)
    if tool_name is None:
        try:
            if hasattr(function_response, 'get'):
                tool_name = function_response.get('name', None)
                tool_response = function_response.get('response', None)
        except Exception:
            pass
    if tool_name is None:
        try:
            if hasattr(function_response, '__dict__'):
                fr_dict = function_response.__dict__
                tool_name = fr_dict.get('name', None)
                tool_response = fr_dict.get('response', None)
        except Exception:
            pass
    if tool_name is None:
        try:
            if hasattr(function_response, '_pb'):
                pb = function_response._pb
                if hasattr(pb, 'name'):
                    tool_name = pb.name
                if hasattr(pb, 'response'):
                    tool_response = pb.response
        except Exception:
            pass
    if tool_name:
        response_data = {'name': tool_name, 'response': tool_response or {}, 'timestamp': time.time(), 'raw': str(function_response)[:500]}
        self.mcp_responses.append(response_data)
        if self._pending_call and self._pending_call['name'] == tool_name:
            self.call_response_pairs.append({'call': self._pending_call, 'response': response_data, 'duration': response_data['timestamp'] - self._pending_call['timestamp'], 'paired_at': time.time()})
            self._pending_call = None
        return response_data
    return None

class ClaudeCodeBackend(LLMBackend):
    """Claude Code backend using claude-code-sdk-python.

    Provides streaming interface to Claude Code with built-in tool execution
    capabilities and MassGen workflow tool integration. Uses ClaudeSDKClient
    for direct communication with Claude Code server.

    TODO (v0.0.14 Context Sharing Enhancement - See docs/dev_notes/v0.0.14-context.md):
    - Implement permission enforcement during file/workspace operations
    - Add execute_with_permissions() method to check permissions before operations
    - Integrate with PermissionManager for access control validation
    - Add audit logging for all file system access attempts
    - Enforce workspace boundaries based on agent permissions
    - Prevent unauthorized access to other agents' workspaces
    - Support permission-aware tool execution (Read, Write, Bash, etc.)
    """

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        """Initialize ClaudeCodeBackend.

        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env
                    var). If None, will attempt to use Claude subscription
                    authentication
            **kwargs: Additional configuration options including:
                - model: Claude model name
                - system_prompt: Base system prompt
                - allowed_tools: List of allowed tools
                - max_thinking_tokens: Maximum thinking tokens
                - cwd: Current working directory

        Note:
            Authentication is validated on first use. If neither API key nor
            subscription authentication is available, errors will surface when
            attempting to use the backend.
        """
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.use_subscription_auth = not bool(self.api_key)
        if self.api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.api_key
        if sys.platform == 'win32' and (not os.environ.get('CLAUDE_CODE_GIT_BASH_PATH')):
            import shutil
            bash_path = shutil.which('bash')
            if bash_path:
                os.environ['CLAUDE_CODE_GIT_BASH_PATH'] = bash_path
                print(f'[ClaudeCodeBackend] Set CLAUDE_CODE_GIT_BASH_PATH={bash_path}')
        if sys.platform == 'win32':
            self._setup_windows_subprocess_cleanup_suppression()
        self._client: Optional[Any] = None
        self._current_session_id: Optional[str] = None
        if not self.filesystem_manager:
            raise ValueError("Claude Code backend requires 'cwd' configuration for workspace management")
        self._cwd: str = str(Path(str(self.filesystem_manager.get_current_workspace())).resolve())
        self._pending_system_prompt: Optional[str] = None

    def _setup_windows_subprocess_cleanup_suppression(self):
        """Comprehensive Windows subprocess cleanup warning suppression."""
        warnings.filterwarnings('ignore', message='unclosed transport')
        warnings.filterwarnings('ignore', message='I/O operation on closed pipe')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed transport')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed event loop')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed <socket.socket')
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='coroutine')
        warnings.filterwarnings('ignore', message='Exception ignored in')
        warnings.filterwarnings('ignore', message='sys:1: ResourceWarning')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed.*transport.*')
        warnings.filterwarnings('ignore', message='.*BaseSubprocessTransport.*')
        warnings.filterwarnings('ignore', message='.*_ProactorBasePipeTransport.*')
        warnings.filterwarnings('ignore', message='.*Event loop is closed.*')
        try:
            import asyncio.base_subprocess
            import asyncio.proactor_events
            original_subprocess_del = getattr(asyncio.base_subprocess.BaseSubprocessTransport, '__del__', None)
            original_pipe_del = getattr(asyncio.proactor_events._ProactorBasePipeTransport, '__del__', None)

            def silent_subprocess_del(self):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        if original_subprocess_del:
                            original_subprocess_del(self)
                except Exception:
                    pass

            def silent_pipe_del(self):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        if original_pipe_del:
                            original_pipe_del(self)
                except Exception:
                    pass
            if original_subprocess_del:
                asyncio.base_subprocess.BaseSubprocessTransport.__del__ = silent_subprocess_del
            if original_pipe_del:
                asyncio.proactor_events._ProactorBasePipeTransport.__del__ = silent_pipe_del
        except Exception:
            pass
        original_stderr = sys.stderr

        def suppress_exit_warnings():
            try:
                sys.stderr = open(os.devnull, 'w')
                import time
                time.sleep(0.3)
            except Exception:
                pass
            finally:
                try:
                    if sys.stderr != original_stderr:
                        sys.stderr.close()
                    sys.stderr = original_stderr
                except Exception:
                    pass
        atexit.register(suppress_exit_warnings)

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return 'claude_code'

    def get_filesystem_support(self) -> FilesystemSupport:
        """Claude Code has native filesystem support."""
        return FilesystemSupport.NATIVE

    def is_stateful(self) -> bool:
        """
        Claude Code backend is stateful - maintains conversation context.

        Returns:
            True - Claude Code maintains server-side session state
        """
        return True

    async def clear_history(self) -> None:
        """
        Clear Claude Code conversation history while preserving session.

        Uses the /clear slash command to clear conversation history without
        destroying the session, working directory, or other session state.
        """
        if self._client is None:
            return
        try:
            await self._client.query('/clear')
        except Exception as e:
            print(f'Warning: /clear command failed ({e}), falling back to full reset')
            await self.reset_state()

    async def reset_state(self) -> None:
        """
        Reset Claude Code backend state.

        Properly disconnects and clears the current session and client connection to start fresh.
        """
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self._current_session_id = None

    def update_token_usage_from_result_message(self, result_message) -> None:
        """Update token usage from Claude Code ResultMessage.

        Extracts actual token usage and cost data from Claude Code server
        response. This is more accurate than estimation-based methods.

        Args:
            result_message: ResultMessage from Claude Code with usage data
        """
        if ResultMessage is not None and (not isinstance(result_message, ResultMessage)):
            return
        if not hasattr(result_message, 'usage') or not hasattr(result_message, 'total_cost_usd'):
            return
        if result_message.usage:
            usage_data = result_message.usage
            input_tokens = usage_data.get('input_tokens', 0)
            output_tokens = usage_data.get('output_tokens', 0)
            self.token_usage.input_tokens += input_tokens
            self.token_usage.output_tokens += output_tokens
        if result_message.total_cost_usd is not None:
            self.token_usage.estimated_cost += result_message.total_cost_usd
        else:
            input_tokens = result_message.usage.get('input_tokens', 0) if result_message.usage else 0
            output_tokens = result_message.usage.get('output_tokens', 0) if result_message.usage else 0
            cost = self.calculate_cost(input_tokens, output_tokens, '', result_message)
            self.token_usage.estimated_cost += cost

    def update_token_usage(self, messages: List[Dict[str, Any]], response_content: str, model: str):
        """Update token usage tracking (fallback method).

        Only used when no ResultMessage available. Provides estimated token
        tracking for compatibility with base class interface. Should only be
        called when ResultMessage data is not available.

        Args:
            messages: List of conversation messages
            response_content: Generated response content
            model: Model name for cost calculation
        """
        input_text = '\n'.join([msg.get('content', '') for msg in messages])
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(response_content)
        self.token_usage.input_tokens += input_tokens
        self.token_usage.output_tokens += output_tokens
        cost = self.calculate_cost(input_tokens, output_tokens, model, result_message=None)
        self.token_usage.estimated_cost += cost

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by Claude Code.

        Returns maximum tool set available, with security enforced through
        disallowed_tools. Dangerous operations are blocked at the tool
        level, not by restricting tool access.

        Returns:
            List of all tool names that Claude Code provides natively
        """
        return ['Read', 'Write', 'Edit', 'MultiEdit', 'Bash', 'Grep', 'Glob', 'LS', 'WebSearch', 'WebFetch', 'Task', 'TodoWrite', 'NotebookEdit', 'NotebookRead', 'mcp__ide__getDiagnostics', 'mcp__ide__executeCode', 'ExitPlanMode']

    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID from server-side session management.

        Returns:
            Current session ID if available, None otherwise
        """
        return self._current_session_id

    def _build_system_prompt_with_workflow_tools(self, tools: List[Dict[str, Any]], base_system: Optional[str]=None) -> str:
        """Build system prompt that includes workflow tools information.

        Creates comprehensive system prompt that instructs Claude on tool
        usage, particularly for MassGen workflow coordination tools.

        Args:
            tools: List of available tools
            base_system: Base system prompt to extend (optional)

        Returns:
            Complete system prompt with tool instructions
        """
        system_parts = []
        if base_system:
            system_parts.append(base_system)
        command_line_execution_mode = self.config.get('command_line_execution_mode', 'local')
        if command_line_execution_mode == 'docker':
            system_parts.append('\n--- Code Execution Environment ---')
            system_parts.append('- Use the execute_command MCP tool for all command execution')
            system_parts.append('- The Bash tool is disabled in this mode')
            system_parts.append('- Do NOT use any git repository information you may see as part of a broader directory. All git information must come from the execute_command tool and be focused solely on the directories you were told to work in, not any parent directories.')
        if tools:
            workflow_tools = [t for t in tools if t.get('function', {}).get('name') in ['new_answer', 'vote']]
            if workflow_tools:
                system_parts.append('\n--- Coordination Actions ---')
                for tool in workflow_tools:
                    name = tool.get('function', {}).get('name', 'unknown')
                    description = tool.get('function', {}).get('description', 'No description')
                    system_parts.append(f'- {name}: {description}')
                    if name == 'new_answer':
                        system_parts.append('    Usage: {"tool_name": "new_answer", "arguments": {"content": "your improved answer. If any builtin tools were used, mention how they are used here."}}')
                    elif name == 'vote':
                        agent_id_enum = None
                        for t in tools:
                            if t.get('function', {}).get('name') == 'vote':
                                agent_id_param = t.get('function', {}).get('parameters', {}).get('properties', {}).get('agent_id', {})
                                if 'enum' in agent_id_param:
                                    agent_id_enum = agent_id_param['enum']
                                break
                        if agent_id_enum:
                            agent_list = ', '.join(agent_id_enum)
                            system_parts.append(f'    Usage: {{"tool_name": "vote", "arguments": {{"agent_id": "agent1", "reason": "explanation"}}}} // Choose agent_id from: {agent_list}')
                        else:
                            system_parts.append('    Usage: {"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}')
                system_parts.append('\n--- MassGen Coordination Instructions ---')
                system_parts.append('IMPORTANT: You must respond with a structured JSON decision at the end of your response.')
                system_parts.append('The JSON MUST be formatted as a strict JSON code block:')
                system_parts.append('1. Start with ```json on one line')
                system_parts.append('2. Include your JSON content (properly formatted)')
                system_parts.append('3. End with ``` on one line')
                system_parts.append('Example format:\n```json\n{"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}\n```')
                system_parts.append('The JSON block should be placed at the very end of your response, after your analysis.')
        return '\n'.join(system_parts)

    async def _log_backend_input(self, messages, system_prompt, tools, kwargs):
        """Log backend inputs using StreamChunk for visibility (enabled by default)."""
        if os.getenv('MASSGEN_LOG_BACKENDS', '1') == '0':
            return
        try:
            reset_mode = '🔄 RESET' if kwargs.get('reset_chat') else '💬 CONTINUE'
            tools_info = f'🔧 {len(tools)} tools' if tools else '🚫 No tools'
            debug_info = f'[BACKEND] {reset_mode} | {tools_info} | Session: {self._current_session_id}'
            if system_prompt and len(system_prompt) > 0:
                debug_info += f'\n[SYSTEM_FULL] {system_prompt}'
            yield StreamChunk(type='debug', content=debug_info, source='claude_code_backend')
        except Exception as e:
            yield StreamChunk(type='debug', content=f'[BACKEND_LOG_ERROR] {str(e)}', source='claude_code_backend')

    def extract_structured_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract structured JSON response for Claude Code format.

        Looks for JSON in the format:
        {"tool_name": "vote/new_answer", "arguments": {...}}

        Args:
            response_text: The full response text to search

        Returns:
            Extracted JSON dict if found, None otherwise
        """
        try:
            import re
            markdown_json_pattern = '```json\\s*(\\{.*?\\})\\s*```'
            markdown_matches = re.findall(markdown_json_pattern, response_text, re.DOTALL)
            for match in reversed(markdown_matches):
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            json_pattern = '\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)
            for match in reversed(json_matches):
                try:
                    cleaned_match = match.strip()
                    parsed = json.loads(cleaned_match)
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            brace_count = 0
            json_start = -1
            for i, char in enumerate(response_text):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start >= 0:
                        json_block = response_text[json_start:i + 1]
                        try:
                            parsed = json.loads(json_block)
                            if isinstance(parsed, dict) and 'tool_name' in parsed:
                                return parsed
                        except json.JSONDecodeError:
                            pass
                        json_start = -1
            lines = response_text.strip().split('\n')
            json_candidates = []
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('{') and stripped.endswith('}'):
                    json_candidates.append(stripped)
                elif stripped.startswith('{'):
                    json_text = stripped
                    for j in range(i + 1, len(lines)):
                        json_text += '\n' + lines[j].strip()
                        if lines[j].strip().endswith('}'):
                            json_candidates.append(json_text)
                            break
            for candidate in reversed(json_candidates):
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            return None
        except Exception:
            return None

    def _parse_workflow_tool_calls(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse workflow tool calls from text content.

        Searches for JSON-formatted tool calls in the response text and
        converts them to the standard tool call format used by MassGen.
        Uses the extract_structured_response method for robust JSON extraction.

        Args:
            text_content: Response text to search for tool calls

        Returns:
            List of unique tool call dictionaries in standard format
        """
        tool_calls = []
        structured_response = self.extract_structured_response(text_content)
        if structured_response and isinstance(structured_response, dict):
            tool_name = structured_response.get('tool_name')
            arguments = structured_response.get('arguments', {})
            if tool_name and isinstance(arguments, dict):
                tool_calls.append({'id': f'call_{uuid.uuid4().hex[:8]}', 'type': 'function', 'function': {'name': tool_name, 'arguments': arguments}})
                return tool_calls
        seen_calls = set()
        json_patterns = ['\\{"tool_name":\\s*"([^"]+)",\\s*"arguments":\\s*(\\{[^}]*\\})\\}', '\\{\\s*"tool_name"\\s*:\\s*"([^"]+)"\\s*,\\s*"arguments"\\s*:\\s*(\\{[^}]*\\})\\s*\\}']
        for pattern in json_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                tool_name = match.group(1)
                try:
                    arguments = json.loads(match.group(2))
                    call_signature = (tool_name, json.dumps(arguments, sort_keys=True))
                    if call_signature not in seen_calls:
                        seen_calls.add(call_signature)
                        tool_calls.append({'id': f'call_{uuid.uuid4().hex[:8]}', 'type': 'function', 'function': {'name': tool_name, 'arguments': arguments}})
                except json.JSONDecodeError:
                    continue
        return tool_calls

    def _build_claude_options(self, **options_kwargs) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions with provided parameters.

        Creates a secure configuration that allows ALL Claude Code tools while
        explicitly disallowing dangerous operations. This gives Claude Code
        maximum power while maintaining security.

        Important: Sets the Claude Code preset as the default system prompt to maintain
        v0.0.x behavior. In claude-agent-sdk v0.1.0+, system prompts default to empty,
        so we explicitly request the claude_code preset.

        When command_line_execution_mode is set to "docker", the Bash tool is disabled
        since execute_command provides all necessary command execution capabilities.

        Returns:
            ClaudeAgentOptions configured with provided parameters and
            security restrictions
        """
        options_kwargs.get('cwd', os.getcwd())
        permission_mode = options_kwargs.get('permission_mode', 'acceptEdits')
        allowed_tools = options_kwargs.get('allowed_tools', self.get_supported_builtin_tools())
        excluded_params = self.get_base_excluded_config_params() | {'api_key', 'allowed_tools', 'permission_mode'}
        cwd_option = Path(str(self.filesystem_manager.get_current_workspace())).resolve()
        self._cwd = str(cwd_option)
        hooks_config = self.filesystem_manager.get_claude_code_hooks_config()
        mcp_servers_dict = {}
        if 'mcp_servers' in options_kwargs:
            mcp_servers = options_kwargs['mcp_servers']
            if isinstance(mcp_servers, list):
                for server in mcp_servers:
                    if isinstance(server, dict) and 'name' in server:
                        server_config = {k: v for k, v in server.items() if k != 'name'}
                        mcp_servers_dict[server['name']] = server_config
            elif isinstance(mcp_servers, dict):
                mcp_servers_dict = mcp_servers
        options = {'cwd': cwd_option, 'resume': self.get_current_session_id(), 'permission_mode': permission_mode, 'allowed_tools': allowed_tools, **{k: v for k, v in options_kwargs.items() if k not in excluded_params}}
        if mcp_servers_dict:
            options['mcp_servers'] = mcp_servers_dict
        if 'system_prompt' not in options:
            options['system_prompt'] = {'type': 'preset', 'preset': 'claude_code'}
        if hooks_config:
            options['hooks'] = hooks_config

        async def can_use_tool(tool_name: str, tool_args: dict, context):
            """Auto-grant permissions for MCP tools."""
            if tool_name.startswith('mcp__'):
                return PermissionResultAllow(updated_input=tool_args)
            return None
        options['can_use_tool'] = can_use_tool
        return ClaudeAgentOptions(**options)

    def create_client(self, **options_kwargs) -> ClaudeSDKClient:
        """Create ClaudeSDKClient with configurable parameters.

        Args:
            **options_kwargs: ClaudeAgentOptions parameters

        Returns:
            ClaudeSDKClient instance
        """
        options = self._build_claude_options(**options_kwargs)
        self._client = ClaudeSDKClient(options)
        return self._client

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a response with tool calling support using claude-code-sdk.

        Properly handle messages and tools context for Claude Code.

        Args:
            messages: List of conversation messages
            tools: List of available tools (includes workflow tools)
            **kwargs: Additional options for client configuration

        Yields:
            StreamChunk objects with response content and metadata
        """
        agent_id = kwargs.get('agent_id', None)
        log_backend_activity(self.get_provider_name(), 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        all_params = {**self.config, **kwargs}
        if self._client is not None:
            client = self._client
        else:
            if 'disallowed_tools' not in all_params:
                all_params['disallowed_tools'] = ['Bash(rm*)', 'Bash(sudo*)', 'Bash(su*)', 'Bash(chmod*)', 'Bash(chown*)']
            command_line_execution_mode = all_params.get('command_line_execution_mode', 'local')
            if command_line_execution_mode == 'docker':
                disallowed_tools = list(all_params.get('disallowed_tools', []))
                bash_related_tools = ['Bash', 'BashOutput', 'KillShell']
                for tool in bash_related_tools:
                    if tool not in disallowed_tools:
                        disallowed_tools.append(tool)
                all_params['disallowed_tools'] = disallowed_tools
            system_msg = next((msg for msg in messages if msg.get('role') == 'system'), None)
            if system_msg:
                system_content = system_msg.get('content', '')
            else:
                system_content = ''
            workflow_system_prompt = self._build_system_prompt_with_workflow_tools(tools or [], system_content)
            if sys.platform == 'win32' and len(workflow_system_prompt) > 200:
                print('[ClaudeCodeBackend] Windows detected complex system prompt, using post-connection delivery')
                clean_params = {k: v for k, v in all_params.items() if k not in ['system_prompt']}
                client = self.create_client(**clean_params)
                self._pending_system_prompt = workflow_system_prompt
            else:
                try:
                    system_prompt_config = {'type': 'preset', 'preset': 'claude_code', 'append': workflow_system_prompt}
                    client = self.create_client(**{**all_params, 'system_prompt': system_prompt_config})
                    self._pending_system_prompt = None
                except Exception as create_error:
                    if sys.platform == 'win32':
                        clean_params = {k: v for k, v in all_params.items() if k not in ['system_prompt']}
                        client = self.create_client(**clean_params)
                        self._pending_system_prompt = workflow_system_prompt
                    else:
                        raise create_error
        if not client._transport:
            try:
                await client.connect()
                if hasattr(self, '_pending_system_prompt') and self._pending_system_prompt:
                    try:
                        system_command = f'/system {self._pending_system_prompt}'
                        await client.query(system_command)
                        async for response in client.receive_response():
                            if hasattr(response, 'subtype') and response.subtype == 'init':
                                break
                        yield StreamChunk(type='content', content='[SYSTEM] Applied system instructions at system level\n', source='claude_code')
                        self._pending_system_prompt = None
                    except Exception as sys_e:
                        yield StreamChunk(type='content', content=f'[SYSTEM] Warning: System-level delivery failed: {str(sys_e)}\n', source='claude_code')
            except Exception as e:
                yield StreamChunk(type='error', error=f'Failed to connect to Claude Code: {str(e)}', source='claude_code')
                return
        if 'workflow_system_prompt' in locals():
            async for debug_chunk in self._log_backend_input(messages, workflow_system_prompt, tools, kwargs):
                yield debug_chunk
        if not messages:
            log_stream_chunk('backend.claude_code', 'error', 'No messages provided to stream_with_tools', agent_id)
            yield StreamChunk(type='error', error='No messages provided to stream_with_tools', source='claude_code')
            return
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        if assistant_messages:
            log_stream_chunk('backend.claude_code', 'error', 'Claude Code backend cannot accept assistant messages - it maintains its own conversation history', agent_id)
            yield StreamChunk(type='error', error='Claude Code backend cannot accept assistant messages - it maintains its own conversation history', source='claude_code')
            return
        if not user_messages:
            log_stream_chunk('backend.claude_code', 'error', 'No user messages found to send to Claude Code', agent_id)
            yield StreamChunk(type='error', error='No user messages found to send to Claude Code', source='claude_code')
            return
        user_contents = []
        for user_msg in user_messages:
            content = user_msg.get('content', '').strip()
            if content:
                user_contents.append(content)
        if user_contents:
            combined_query = '\n\n'.join(user_contents)
            log_backend_agent_message(agent_id or 'default', 'SEND', {'system': workflow_system_prompt, 'user': combined_query}, backend_name=self.get_provider_name())
            await client.query(combined_query)
        else:
            log_stream_chunk('backend.claude_code', 'error', 'All user messages were empty', agent_id)
            yield StreamChunk(type='error', error='All user messages were empty', source='claude_code')
            return
        accumulated_content = ''
        try:
            async for message in client.receive_response():
                if isinstance(message, (AssistantMessage, UserMessage)):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            accumulated_content += block.text
                            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': block.text}, backend_name=self.get_provider_name())
                            log_stream_chunk('backend.claude_code', 'content', block.text, agent_id)
                            yield StreamChunk(type='content', content=block.text, source='claude_code')
                        elif isinstance(block, ToolUseBlock):
                            log_backend_activity(self.get_provider_name(), f'Builtin tool called: {block.name}', {'tool_id': block.id}, agent_id=agent_id)
                            log_stream_chunk('backend.claude_code', 'tool_use', {'name': block.name, 'input': block.input}, agent_id)
                            yield StreamChunk(type='content', content=f'🔧 {block.name}({block.input})', source='claude_code')
                        elif isinstance(block, ToolResultBlock):
                            status = '❌ Error' if block.is_error else '✅ Result'
                            log_stream_chunk('backend.claude_code', 'tool_result', {'is_error': block.is_error, 'content': block.content}, agent_id)
                            yield StreamChunk(type='content', content=f'🔧 Tool {status}: {block.content}', source='claude_code')
                    workflow_tool_calls = self._parse_workflow_tool_calls(accumulated_content)
                    if workflow_tool_calls:
                        log_stream_chunk('backend.claude_code', 'tool_calls', workflow_tool_calls, agent_id)
                        yield StreamChunk(type='tool_calls', tool_calls=workflow_tool_calls, source='claude_code')
                    log_stream_chunk('backend.claude_code', 'complete_message', accumulated_content[:200] if len(accumulated_content) > 200 else accumulated_content, agent_id)
                    yield StreamChunk(type='complete_message', complete_message={'role': 'assistant', 'content': accumulated_content}, source='claude_code')
                elif isinstance(message, SystemMessage):
                    self._track_session_info(message=message)
                    log_stream_chunk('backend.claude_code', 'backend_status', {'subtype': message.subtype, 'data': message.data}, agent_id)
                    yield StreamChunk(type='backend_status', status=message.subtype, content=json.dumps(message.data), source='claude_code')
                elif isinstance(message, ResultMessage):
                    self._track_session_info(message)
                    self.update_token_usage_from_result_message(message)
                    log_stream_chunk('backend.claude_code', 'complete_response', {'session_id': message.session_id, 'cost_usd': message.total_cost_usd}, agent_id)
                    yield StreamChunk(type='complete_response', complete_message={'session_id': message.session_id, 'duration_ms': message.duration_ms, 'cost_usd': message.total_cost_usd, 'usage': message.usage, 'is_error': message.is_error}, source='claude_code')
                    log_stream_chunk('backend.claude_code', 'done', None, agent_id)
                    yield StreamChunk(type='done', source='claude_code')
                    break
        except Exception as e:
            error_msg = str(e)
            if 'git-bash' in error_msg.lower() or 'bash.exe' in error_msg.lower():
                error_msg += '\n\nWindows Setup Required:\n1. Install Git Bash: https://git-scm.com/downloads/win\n2. Ensure git-bash is in PATH, or set: CLAUDE_CODE_GIT_BASH_PATH=C:\\Program Files\\Git\\bin\\bash.exe'
            elif 'exit code 1' in error_msg and 'win32' in str(sys.platform):
                error_msg += '\n\nThis may indicate missing git-bash on Windows. Please install Git Bash from https://git-scm.com/downloads/win'
            log_stream_chunk('backend.claude_code', 'error', error_msg, agent_id)
            yield StreamChunk(type='error', error=f'Claude Code streaming error: {str(error_msg)}', source='claude_code')

    def _track_session_info(self, message) -> None:
        """Track session information from Claude Code server responses.

        Extracts and stores session ID, working directory, and other session
        metadata from ResultMessage and SystemMessage responses to enable
        session continuation and state management across multiple interactions.

        Args:
            message: Message from Claude Code (ResultMessage or SystemMessage)
                    potentially containing session information
        """
        if ResultMessage is not None and isinstance(message, ResultMessage):
            if hasattr(message, 'session_id') and message.session_id:
                old_session_id = self._current_session_id
                self._current_session_id = message.session_id
        elif SystemMessage is not None and isinstance(message, SystemMessage):
            if hasattr(message, 'data') and isinstance(message.data, dict):
                if 'session_id' in message.data and message.data['session_id']:
                    old_session_id = self._current_session_id
                    self._current_session_id = message.data['session_id']
                    if old_session_id != self._current_session_id:
                        print(f'[ClaudeCodeBackend] Session ID from SystemMessage: {old_session_id} → {self._current_session_id}')
                if 'cwd' in message.data and message.data['cwd']:
                    self._cwd = message.data['cwd']

    async def disconnect(self):
        """Disconnect the ClaudeSDKClient and clean up resources.

        Properly closes the connection and resets internal state.
        Should be called when the backend is no longer needed.
        """
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            finally:
                self._client = None
                self._current_session_id = None

    def __del__(self):
        """Cleanup on destruction.

        Note: This won't work for async cleanup in practice.
        Use explicit disconnect() calls for proper resource cleanup.
        """

def _setup_windows_subprocess_cleanup_suppression(self):
    """Comprehensive Windows subprocess cleanup warning suppression."""
    warnings.filterwarnings('ignore', message='unclosed transport')
    warnings.filterwarnings('ignore', message='I/O operation on closed pipe')
    warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed transport')
    warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed event loop')
    warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed <socket.socket')
    warnings.filterwarnings('ignore', category=RuntimeWarning, message='coroutine')
    warnings.filterwarnings('ignore', message='Exception ignored in')
    warnings.filterwarnings('ignore', message='sys:1: ResourceWarning')
    warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed.*transport.*')
    warnings.filterwarnings('ignore', message='.*BaseSubprocessTransport.*')
    warnings.filterwarnings('ignore', message='.*_ProactorBasePipeTransport.*')
    warnings.filterwarnings('ignore', message='.*Event loop is closed.*')
    try:
        import asyncio.base_subprocess
        import asyncio.proactor_events
        original_subprocess_del = getattr(asyncio.base_subprocess.BaseSubprocessTransport, '__del__', None)
        original_pipe_del = getattr(asyncio.proactor_events._ProactorBasePipeTransport, '__del__', None)

        def silent_subprocess_del(self):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    if original_subprocess_del:
                        original_subprocess_del(self)
            except Exception:
                pass

        def silent_pipe_del(self):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    if original_pipe_del:
                        original_pipe_del(self)
            except Exception:
                pass
        if original_subprocess_del:
            asyncio.base_subprocess.BaseSubprocessTransport.__del__ = silent_subprocess_del
        if original_pipe_del:
            asyncio.proactor_events._ProactorBasePipeTransport.__del__ = silent_pipe_del
    except Exception:
        pass
    original_stderr = sys.stderr

    def suppress_exit_warnings():
        try:
            sys.stderr = open(os.devnull, 'w')
            import time
            time.sleep(0.3)
        except Exception:
            pass
        finally:
            try:
                if sys.stderr != original_stderr:
                    sys.stderr.close()
                sys.stderr = original_stderr
            except Exception:
                pass
    atexit.register(suppress_exit_warnings)

def function_to_json(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {str: 'string', int: 'integer', float: 'number', bool: 'boolean', list: 'array', dict: 'object', type(None): 'null'}
    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(f'Failed to get signature for function {func.__name__}: {str(e)}')
    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, 'string')
        except KeyError as e:
            raise KeyError(f'Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}')
        parameters[param.name] = {'type': param_type}
    required = [param.name for param in signature.parameters.values() if param.default == inspect._empty]
    return {'type': 'function', 'name': func.__name__, 'description': func.__doc__ or '', 'parameters': {'type': 'object', 'properties': parameters, 'required': required}}

class StreamingOrchestrator:

    def __init__(self, display_enabled: bool=True, stream_callback: Optional[Callable]=None, max_lines: int=10, save_logs: bool=True, answers_dir: Optional[str]=None):
        self.display = MultiRegionDisplay(display_enabled, max_lines, save_logs, answers_dir)
        self.stream_callback = stream_callback

    def stream_output(self, agent_id: int, content: str):
        """Streaming content - uses debounced updates."""
        self.display.stream_output_sync(agent_id, content)
        if self.stream_callback:
            try:
                self.stream_callback(agent_id, content)
            except Exception:
                pass

    def set_agent_model(self, agent_id: int, model_name: str):
        """Set agent model - immediate update."""
        self.display.set_agent_model(agent_id, model_name)
        self.display.force_update_display()

    def update_agent_status(self, agent_id: int, status: str):
        """Update agent status - immediate update for critical state changes."""
        self.display.update_agent_status(agent_id, status)
        self.display.force_update_display()

    def update_phase(self, old_phase: str, new_phase: str):
        """Update phase - immediate update for critical state changes."""
        self.display.update_phase(old_phase, new_phase)
        self.display.force_update_display()

    def update_vote_distribution(self, vote_dist: Dict[int, int]):
        """Update vote distribution - immediate update for critical state changes."""
        self.display.update_vote_distribution(vote_dist)
        self.display.force_update_display()

    def update_consensus_status(self, representative_id: int, vote_dist: Dict[int, int]):
        """Update consensus status - immediate update for critical state changes."""
        self.display.update_consensus_status(representative_id, vote_dist)
        self.display.force_update_display()

    def reset_consensus(self):
        """Reset consensus - immediate update for critical state changes."""
        self.display.reset_consensus()
        self.display.force_update_display()

    def add_system_message(self, message: str):
        """Add system message - immediate update for important messages."""
        self.display.add_system_message(message)
        self.display.force_update_display()

    def update_agent_vote_target(self, agent_id: int, target_id: Optional[int]):
        """Update agent vote target - immediate update for critical state changes."""
        self.display.update_agent_vote_target(agent_id, target_id)
        self.display.force_update_display()

    def update_agent_chat_round(self, agent_id: int, round_num: int):
        """Update agent chat round - debounced update."""
        self.display.update_agent_chat_round(agent_id, round_num)

    def update_agent_update_count(self, agent_id: int, count: int):
        """Update agent update count - debounced update."""
        self.display.update_agent_update_count(agent_id, count)

    def update_agent_votes_cast(self, agent_id: int, votes_cast: int):
        """Update agent votes cast - immediate update for vote-related changes."""
        self.display.update_agent_votes_cast(agent_id, votes_cast)
        self.display.force_update_display()

    def update_debate_rounds(self, rounds: int):
        """Update debate rounds - immediate update for critical state changes."""
        self.display.update_debate_rounds(rounds)
        self.display.force_update_display()

    def format_agent_notification(self, agent_id: int, notification_type: str, content: str):
        """Format agent notifications - immediate update for notifications."""
        self.display.format_agent_notification(agent_id, notification_type, content)
        self.display.force_update_display()

    def get_agent_log_path(self, agent_id: int) -> str:
        """Get the log file path for a specific agent."""
        return self.display.get_agent_log_path_for_display(agent_id)

    def get_agent_answer_path(self, agent_id: int) -> str:
        """Get the answer file path for a specific agent."""
        return self.display.get_agent_answer_path_for_display(agent_id)

    def get_system_log_path(self) -> str:
        """Get the system log file path."""
        return self.display.get_system_log_path_for_display()

    def cleanup(self):
        """Clean up resources when orchestrator is no longer needed."""
        self.display.cleanup()

def stream_output(self, agent_id: int, content: str):
    """Streaming content - uses debounced updates."""
    self.display.stream_output_sync(agent_id, content)
    if self.stream_callback:
        try:
            self.stream_callback(agent_id, content)
        except Exception:
            pass

class MassOrchestrator:
    """
    Central orchestrator for managing multiple agents in the MassGen framework, and logging for all events.

    Simplified workflow:
    1. Agents work on task (status: "working")
    2. When agents vote, they become "voted"
    3. When all votable agents have voted:
       - Check consensus
       - If consensus reached: select representative to present final answer
       - If no consensus: restart all agents for debate
    4. Representative presents final answer and system completes
    """

    def __init__(self, max_duration: int=600, consensus_threshold: float=0.0, max_debate_rounds: int=1, status_check_interval: float=2.0, thread_pool_timeout: int=5, streaming_orchestrator=None):
        """
        Initialize the orchestrator.

        Args:
            max_duration: Maximum duration for the entire task in seconds
            consensus_threshold: Fraction of agents that must agree for consensus (1.0 = unanimous)
            max_debate_rounds: Maximum number of debate rounds before fallback
            status_check_interval: Interval for checking agent status (seconds)
            thread_pool_timeout: Timeout for shutting down thread pool executor (seconds)
            streaming_orchestrator: Optional streaming orchestrator for real-time display
        """
        self.agents: Dict[int, Any] = {}
        self.agent_states: Dict[int, AgentState] = {}
        self.votes: List[VoteRecord] = []
        self.system_state = SystemState()
        self.max_duration = max_duration
        self.consensus_threshold = consensus_threshold
        self.max_debate_rounds = max_debate_rounds
        self.status_check_interval = status_check_interval
        self.thread_pool_timeout = thread_pool_timeout
        self.streaming_orchestrator = streaming_orchestrator
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self.communication_log: List[Dict[str, Any]] = []
        self.final_response: Optional[str] = None
        self.log_manager = get_log_manager()

    def register_agent(self, agent):
        """
        Register an agent with the orchestrator.

        Args:
            agent: MassAgent instance to register
        """
        with self._lock:
            self.agents[agent.agent_id] = agent
            self.agent_states[agent.agent_id] = agent.state
            agent.orchestrator = self

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an orchestrator event."""
        self.communication_log.append({'timestamp': time.time(), 'event_type': event_type, 'data': data})

    def update_agent_answer(self, agent_id: int, answer: str):
        """
        Update an agent's running answer.

        Args:
            agent_id: ID of the agent updating their answer
            answer: New answer content
        """
        with self._lock:
            if agent_id not in self.agent_states:
                raise ValueError(f'Agent {agent_id} not registered')
            old_answer_length = len(self.agent_states[agent_id].curr_answer)
            self.agent_states[agent_id].add_update(answer)
            preview = answer[:100] + '...' if len(answer) > 100 else answer
            print(f'📝 Agent {agent_id} answer updated ({old_answer_length} → {len(answer)} chars)')
            print(f'   🔍 {preview}')
            if self.log_manager:
                self.log_manager.log_agent_answer_update(agent_id=agent_id, answer=answer, phase=self.system_state.phase, orchestrator=self)
            self._log_event('answer_updated', {'agent_id': agent_id, 'answer': answer, 'timestamp': time.time()})

    def _get_current_vote_counts(self) -> Counter:
        """
        Get current vote counts based on agent states' vote_target.
        Returns Counter of agent_id -> vote_count for ALL agents (0 if no votes).
        """
        current_votes = []
        for agent_id, state in self.agent_states.items():
            if state.status == 'voted' and state.curr_vote is not None:
                current_votes.append(state.curr_vote.target_id)
        vote_counts = Counter(current_votes)
        for agent_id in self.agent_states.keys():
            if agent_id not in vote_counts:
                vote_counts[agent_id] = 0
        return vote_counts

    def _get_current_voted_agents_count(self) -> int:
        """
        Get count of agents who currently have status "voted".
        """
        return len([s for s in self.agent_states.values() if s.status == 'voted'])

    def _get_voting_status(self) -> Dict[str, Any]:
        """Get current voting status and distribution."""
        vote_counts = self._get_current_vote_counts()
        total_agents = len(self.agents)
        failed_agents = len([s for s in self.agent_states.values() if s.status == 'failed'])
        votable_agents = total_agents - failed_agents
        voted_agents = self._get_current_voted_agents_count()
        return {'vote_distribution': dict(vote_counts), 'total_agents': total_agents, 'failed_agents': failed_agents, 'votable_agents': votable_agents, 'voted_agents': voted_agents, 'votes_needed_for_consensus': max(1, int(votable_agents * self.consensus_threshold)), 'leading_agent': vote_counts.most_common(1)[0] if vote_counts else None}

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status information."""
        return {'phase': self.system_state.phase, 'consensus_reached': self.system_state.consensus_reached, 'agents': {agent_id: {'status': state.status, 'update_times': len(state.updated_answers), 'chat_round': state.chat_round, 'vote_target': state.curr_vote.target_id if state.curr_vote else None, 'execution_time': state.execution_time} for agent_id, state in self.agent_states.items()}, 'voting_status': self._get_voting_status(), 'runtime': time.time() - self.system_state.start_time if self.system_state.start_time else 0}

    def cast_vote(self, voter_id: int, target_id: int, reason: str=''):
        """
        Record a vote from one agent for another agent's solution.

        Args:
            voter_id: ID of the agent casting the vote
            target_id: ID of the agent being voted for
            reason: The reason for the vote (optional)
        """
        with self._lock:
            logger.info(f'🗳️ VOTING: Agent {voter_id} casting vote')
            print(f'🗳️  VOTE: Agent {voter_id} → Agent {target_id} ({self.system_state.phase})')
            if reason:
                print(f'   📝 Voting reason: {len(reason)} chars')
            if voter_id not in self.agent_states:
                logger.error(f'   ❌ Invalid voter: Agent {voter_id} not registered')
                raise ValueError(f'Voter agent {voter_id} not registered')
            if target_id not in self.agent_states:
                logger.error(f'   ❌ Invalid target: Agent {target_id} not registered')
                raise ValueError(f'Target agent {target_id} not registered')
            previous_vote = self.agent_states[voter_id].curr_vote
            if previous_vote:
                logger.info(f'   🔄 Agent {voter_id} changed vote from Agent {previous_vote.target_id} to Agent {target_id}')
            else:
                logger.info(f'   ✨ Agent {voter_id} new vote for Agent {target_id}')
            vote = VoteRecord(voter_id=voter_id, target_id=target_id, reason=reason, timestamp=time.time())
            self.votes.append(vote)
            old_status = self.agent_states[voter_id].status
            self.agent_states[voter_id].status = 'voted'
            self.agent_states[voter_id].curr_vote = vote
            self.agent_states[voter_id].cast_votes.append(vote)
            self.agent_states[voter_id].execution_end_time = time.time()
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_agent_status(voter_id, 'voted')
                self.streaming_orchestrator.update_agent_vote_target(voter_id, target_id)
                update_count = len(self.agent_states[voter_id].updated_answers)
                self.streaming_orchestrator.update_agent_update_count(voter_id, update_count)
                for agent_id, agent_state in self.agent_states.items():
                    vote_cast_count = len(agent_state.cast_votes)
                    self.streaming_orchestrator.update_agent_votes_cast(agent_id, vote_cast_count)
                vote_counts = self._get_current_vote_counts()
                self.streaming_orchestrator.update_vote_distribution(dict(vote_counts))
                vote_msg = f'👍 Agent {voter_id} voted for Agent {target_id}'
                self.streaming_orchestrator.add_system_message(vote_msg)
            if self.log_manager:
                self.log_manager.log_voting_event(voter_id=voter_id, target_id=target_id, phase=self.system_state.phase, reason=reason, orchestrator=self)
                self.log_manager.log_agent_status_change(agent_id=voter_id, old_status=old_status, new_status='voted', phase=self.system_state.phase)
            vote_counts = self._get_current_vote_counts()
            voted_agents_count = self._get_current_voted_agents_count()
            logger.info(f'   📊 Vote distribution: {dict(vote_counts)}')
            logger.info(f'   📈 Voting progress: {voted_agents_count}/{len(self.agent_states)} agents voted')
            total_agents = len(self.agent_states)
            votes_needed = max(1, int(total_agents * self.consensus_threshold))
            if vote_counts:
                leading_agent, leading_votes = vote_counts.most_common(1)[0]
                logger.info(f'   🏆 Leading: Agent {leading_agent} with {leading_votes} votes (need {votes_needed} for consensus)')
            self._log_event('vote_cast', {'voter_id': voter_id, 'target_id': target_id, 'timestamp': vote.timestamp, 'vote_distribution': dict(vote_counts), 'total_votes': voted_agents_count})

    def notify_answer_update(self, agent_id: int, answer: str):
        """
        Called when an agent updates their answer.
        This should restart all voted agents who haven't seen this update yet.
        """
        logger.info(f'📢 Agent {agent_id} updated answer')
        self.update_agent_answer(agent_id, answer)
        if self.streaming_orchestrator:
            answer_msg = f'📝 Agent {agent_id} updated answer ({len(answer)} chars)'
            self.streaming_orchestrator.add_system_message(answer_msg)
            update_count = len(self.agent_states[agent_id].updated_answers)
            self.streaming_orchestrator.update_agent_update_count(agent_id, update_count)
        with self._lock:
            restarted_agents = []
            time.time()
            for other_agent_id, state in self.agent_states.items():
                if other_agent_id != agent_id and state.status == 'voted':
                    state.status = 'working'
                    state.curr_vote = None
                    state.execution_start_time = time.time()
                    restarted_agents.append(other_agent_id)
                    logger.info(f'🔄 Agent {other_agent_id} restarted due to update from Agent {agent_id}')
                    if self.streaming_orchestrator:
                        self.streaming_orchestrator.update_agent_status(other_agent_id, 'working')
                        self.streaming_orchestrator.update_agent_vote_target(other_agent_id, None)
                        update_count = len(self.agent_states[other_agent_id].updated_answers)
                        self.streaming_orchestrator.update_agent_update_count(other_agent_id, update_count)
                        restart_msg = f'🔄 Agent {other_agent_id} restarted due to new update'
                        self.streaming_orchestrator.add_system_message(restart_msg)
                    if self.log_manager:
                        self.log_manager.log_agent_restart(agent_id=other_agent_id, reason=f'new_update_from_agent_{agent_id}', phase=self.system_state.phase)
            if restarted_agents:
                logger.info(f'🔄 Restarted agents: {restarted_agents}')
                if self.streaming_orchestrator:
                    vote_counts = self._get_current_vote_counts()
                    self.streaming_orchestrator.update_vote_distribution(dict(vote_counts))
                    for agent_id, agent_state in self.agent_states.items():
                        vote_cast_count = len(agent_state.cast_votes)
                        self.streaming_orchestrator.update_agent_votes_cast(agent_id, vote_cast_count)
            return restarted_agents

    def _check_consensus(self) -> bool:
        """
        Check if consensus has been reached based on current votes.
        Improved to handle edge cases and ensure proper consensus calculation.
        """
        with self._lock:
            total_agents = len(self.agents)
            failed_agents_count = len([s for s in self.agent_states.values() if s.status == 'failed'])
            votable_agents_count = total_agents - failed_agents_count
            if votable_agents_count == 0:
                logger.warning('⚠️ No votable agents available for consensus')
                return False
            if votable_agents_count == 1:
                working_agents = [aid for aid, state in self.agent_states.items() if state.status == 'working']
                if not working_agents:
                    votable_agent = [aid for aid, state in self.agent_states.items() if state.status != 'failed'][0]
                    logger.info(f'🎯 Single agent consensus: Agent {votable_agent}')
                    self._reach_consensus(votable_agent)
                    return True
                return False
            vote_counts = self._get_current_vote_counts()
            votes_needed = max(1, int(votable_agents_count * self.consensus_threshold))
            if vote_counts and vote_counts.most_common(1)[0][1] >= votes_needed:
                winning_agent_id = vote_counts.most_common(1)[0][0]
                winning_votes = vote_counts.most_common(1)[0][1]
                if self.agent_states[winning_agent_id].status == 'failed':
                    logger.warning(f'⚠️ Winning agent {winning_agent_id} has failed - recalculating')
                    return False
                logger.info(f'✅ Consensus reached: Agent {winning_agent_id} with {winning_votes}/{votable_agents_count} votes')
                self._reach_consensus(winning_agent_id)
                return True
            return False

    def mark_agent_failed(self, agent_id: int, reason: str=''):
        """
        Mark an agent as failed.

        Args:
            agent_id: ID of the agent to mark as failed
            reason: Optional reason for the failure
        """
        with self._lock:
            logger.info(f'💥 AGENT FAILURE: Agent {agent_id} marked as failed')
            print(f'      💥 MARK_FAILED: Agent {agent_id}')
            print(f'      📊 Current phase: {self.system_state.phase}')
            if agent_id not in self.agent_states:
                logger.error(f'   ❌ Invalid agent: Agent {agent_id} not registered')
                raise ValueError(f'Agent {agent_id} not registered')
            old_status = self.agent_states[agent_id].status
            self.agent_states[agent_id].status = 'failed'
            self.agent_states[agent_id].execution_end_time = time.time()
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_agent_status(agent_id, 'failed')
                failure_msg = f'💥 Agent {agent_id} failed: {reason}' if reason else f'💥 Agent {agent_id} failed'
                self.streaming_orchestrator.add_system_message(failure_msg)
            if self.log_manager:
                self.log_manager.log_agent_status_change(agent_id=agent_id, old_status=old_status, new_status='failed', phase=self.system_state.phase)
            self._log_event('agent_failed', {'agent_id': agent_id, 'reason': reason, 'timestamp': time.time(), 'old_status': old_status})
            status_counts = Counter((state.status for state in self.agent_states.values()))
            logger.info(f'   📊 Status distribution: {dict(status_counts)}')
            logger.info(f'   📈 Failed agents: {status_counts.get('failed', 0)}/{len(self.agent_states)} total')

    def _reach_consensus(self, winning_agent_id: int):
        """Mark consensus as reached and finalize the system."""
        old_phase = self.system_state.phase
        self.system_state.consensus_reached = True
        self.system_state.representative_agent_id = winning_agent_id
        self.system_state.phase = 'consensus'
        if self.streaming_orchestrator:
            vote_distribution = dict(self._get_current_vote_counts())
            self.streaming_orchestrator.update_consensus_status(winning_agent_id, vote_distribution)
            self.streaming_orchestrator.update_phase(old_phase, 'consensus')
        if self.log_manager:
            vote_distribution = dict(self._get_current_vote_counts())
            self.log_manager.log_consensus_reached(winning_agent_id=winning_agent_id, vote_distribution=vote_distribution, is_fallback=False, phase=self.system_state.phase)
            self.log_manager.log_phase_transition(old_phase=old_phase, new_phase='consensus', additional_data={'consensus_reached': True, 'winning_agent_id': winning_agent_id, 'is_fallback': False})
        self._log_event('consensus_reached', {'winning_agent_id': winning_agent_id, 'fallback_to_majority': False, 'final_vote_distribution': dict(self._get_current_vote_counts())})

    def export_detailed_session_log(self) -> Dict[str, Any]:
        """
        Export complete detailed session information for comprehensive analysis.
        Includes all outputs, metrics, and evaluation results.
        """
        session_log = {'session_metadata': {'session_id': f'mass_session_{int(self.system_state.start_time)}' if self.system_state.start_time else None, 'start_time': self.system_state.start_time, 'end_time': self.system_state.end_time, 'total_duration': self.system_state.end_time - self.system_state.start_time if self.system_state.start_time and self.system_state.end_time else None, 'timestamp': datetime.now().isoformat(), 'system_version': 'MassGen v1.0'}, 'task_information': {'question': self.system_state.task.question if self.system_state.task else None, 'task_id': self.system_state.task.task_id if self.system_state.task else None, 'context': self.system_state.task.context if self.system_state.task else None}, 'system_configuration': {'max_duration': self.max_duration, 'consensus_threshold': self.consensus_threshold, 'max_debate_rounds': self.max_debate_rounds, 'agents': [agent.model for agent in self.agents.values()]}, 'agent_details': {agent_id: {'status': state.status, 'updates_count': len(state.updated_answers), 'chat_length': len(state.chat_history), 'chat_round': state.chat_round, 'vote_target': state.curr_vote.target_id if state.curr_vote else None, 'execution_time': state.execution_time, 'execution_start_time': state.execution_start_time, 'execution_end_time': state.execution_end_time, 'updated_answers': [{'timestamp': update.timestamp, 'status': update.status, 'answer_length': len(update.answer)} for update in state.updated_answers]} for agent_id, state in self.agent_states.items()}, 'voting_analysis': {'vote_records': [{'voter_id': vote.voter_id, 'target_id': vote.target_id, 'timestamp': vote.timestamp, 'reason_length': len(vote.reason) if vote.reason else 0} for vote in self.votes], 'vote_timeline': [{'timestamp': vote.timestamp, 'event': f'Agent {vote.voter_id} → Agent {vote.target_id}'} for vote in self.votes]}, 'communication_log': self.communication_log, 'system_events': [{'timestamp': entry['timestamp'], 'event_type': entry['event_type'], 'data_summary': {k: len(v) if isinstance(v, (str, list, dict)) else v for k, v in entry['data'].items()}} for entry in self.communication_log]}
        return session_log

    def start_task(self, task: TaskInput):
        """
        Initialize the system for a new task and run the main workflow.

        Args:
            task: TaskInput containing the problem to solve

        Returns:
            response: Dict[str, Any] containing the final answer to the task's question, and relevant information
        """
        with self._lock:
            logger.info('🎯 ORCHESTRATOR: Starting new task')
            logger.info(f'   Task ID: {task.task_id}')
            logger.info(f'   Question preview: {task.question}')
            logger.info(f'   Registered agents: {list(self.agents.keys())}')
            logger.info(f'   Max duration: {self.max_duration}')
            logger.info(f'   Consensus threshold: {self.consensus_threshold}')
            self.system_state.task = task
            self.system_state.start_time = time.time()
            self.system_state.phase = 'collaboration'
            self.final_response = None
            for agent_id, agent in self.agents.items():
                agent.state = AgentState(agent_id=agent_id)
                self.agent_states[agent_id] = agent.state
                agent.state.chat_history = []
                if self.streaming_orchestrator:
                    self.streaming_orchestrator.set_agent_model(agent_id, agent.model)
                    self.streaming_orchestrator.update_agent_status(agent_id, 'working')
                    self.streaming_orchestrator.update_agent_update_count(agent_id, 0)
            self.votes.clear()
            self.communication_log.clear()
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_phase('unknown', 'collaboration')
                self.streaming_orchestrator.update_debate_rounds(0)
                init_msg = f'🚀 Starting MassGen task with {len(self.agents)} agents'
                self.streaming_orchestrator.add_system_message(init_msg)
            self._log_event('task_started', {'task_id': task.task_id, 'question': task.question})
            logger.info('✅ Task initialization completed successfully')
        return self._run_mass_workflow(task)

    def _run_mass_workflow(self, task: TaskInput) -> Dict[str, Any]:
        """
        Run the MassGen workflow with dynamic agent restart support:
        1. All agents work in parallel
        2. Agents restart when others share updates (if they had voted)
        3. When all have voted, check consensus
        4. If no consensus, restart all for debate
        5. If consensus, representative presents final answer
        """
        logger.info('🚀 Starting MassGen workflow')
        debate_rounds = 0
        start_time = time.time()
        while not self._stop_event.is_set():
            if time.time() - start_time > self.max_duration:
                logger.warning('⏰ Maximum duration reached - forcing consensus')
                self._force_consensus_by_timeout()
                self._present_final_answer(task)
                break
            logger.info(f'📢 Starting collaboration round {debate_rounds + 1}')
            self._run_all_agents_with_dynamic_restart(task)
            if self._all_agents_voted():
                logger.info('🗳️ All agents have voted - checking consensus')
                if self._check_consensus():
                    logger.info('🎉 Consensus reached!')
                    self._present_final_answer(task)
                    break
                else:
                    debate_rounds += 1
                    if self.streaming_orchestrator:
                        self.streaming_orchestrator.update_debate_rounds(debate_rounds)
                    if debate_rounds > self.max_debate_rounds:
                        logger.warning(f'⚠️ Maximum debate rounds ({self.max_debate_rounds}) reached')
                        self._force_consensus_by_timeout()
                        self._present_final_answer(task)
                        break
                    logger.info(f'🗣️ No consensus - starting debate round {debate_rounds}')
                    self._restart_all_agents_for_debate()
            else:
                time.sleep(self.status_check_interval)
        return self._finalize_session()

    def _run_all_agents_with_dynamic_restart(self, task: TaskInput):
        """
        Run all agents in parallel with support for dynamic restarts.
        This approach handles agents restarting mid-execution.
        """
        active_futures = {}
        executor = ThreadPoolExecutor(max_workers=len(self.agents))
        try:
            for agent_id in self.agents.keys():
                if self.agent_states[agent_id].status not in ['failed']:
                    self._start_agent_if_working(agent_id, task, executor, active_futures)
            while active_futures and (not self._all_agents_voted()):
                completed_futures = []
                for agent_id, future in list(active_futures.items()):
                    if future.done():
                        completed_futures.append(agent_id)
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f'❌ Agent {agent_id} failed: {e}')
                            self.mark_agent_failed(agent_id, str(e))
                for agent_id in completed_futures:
                    del active_futures[agent_id]
                for agent_id in self.agents.keys():
                    if agent_id not in active_futures and self.agent_states[agent_id].status == 'working':
                        self._start_agent_if_working(agent_id, task, executor, active_futures)
                time.sleep(0.1)
        finally:
            for future in active_futures.values():
                future.cancel()
            executor.shutdown(wait=True)

    def _start_agent_if_working(self, agent_id: int, task: TaskInput, executor: ThreadPoolExecutor, active_futures: Dict):
        """Start an agent if it's in working status and not already running."""
        if self.agent_states[agent_id].status == 'working' and agent_id not in active_futures:
            self.agent_states[agent_id].execution_start_time = time.time()
            future = executor.submit(self._run_single_agent, agent_id, task)
            active_futures[agent_id] = future
            logger.info(f'🤖 Agent {agent_id} started/restarted')

    def _run_single_agent(self, agent_id: int, task: TaskInput):
        """Run a single agent's work_on_task method."""
        agent = self.agents[agent_id]
        try:
            logger.info(f'🤖 Agent {agent_id} starting work')
            updated_messages = agent.work_on_task(task)
            self.agent_states[agent_id].chat_history.append(updated_messages)
            self.agent_states[agent_id].chat_round = agent.state.chat_round
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_agent_chat_round(agent_id, agent.state.chat_round)
                update_count = len(self.agent_states[agent_id].updated_answers)
                self.streaming_orchestrator.update_agent_update_count(agent_id, update_count)
            logger.info(f'✅ Agent {agent_id} completed work with status: {self.agent_states[agent_id].status}')
        except Exception as e:
            logger.error(f'❌ Agent {agent_id} failed: {e}')
            self.mark_agent_failed(agent_id, str(e))

    def _all_agents_voted(self) -> bool:
        """Check if all votable agents have voted."""
        votable_agents = [aid for aid, state in self.agent_states.items() if state.status not in ['failed']]
        voted_agents = [aid for aid, state in self.agent_states.items() if state.status == 'voted']
        return len(voted_agents) == len(votable_agents) and len(votable_agents) > 0

    def _restart_all_agents_for_debate(self):
        """
        Restart all agents for debate by resetting their status
        We don't clear vote target when restarting for debate as answers are not updated
        """
        logger.info('🔄 Restarting all agents for debate')
        with self._lock:
            if self.streaming_orchestrator:
                self.streaming_orchestrator.reset_consensus()
                self.streaming_orchestrator.update_phase(self.system_state.phase, 'collaboration')
                self.streaming_orchestrator.add_system_message('🗣️ Starting debate phase - no consensus reached')
            if self.log_manager:
                self.log_manager.log_debate_started(phase='collaboration')
                self.log_manager.log_phase_transition(old_phase=self.system_state.phase, new_phase='collaboration', additional_data={'reason': 'no_consensus_reached', 'debate_round': True})
            for agent_id, state in self.agent_states.items():
                if state.status not in ['failed']:
                    state.status
                    state.status = 'working'
                    if self.streaming_orchestrator:
                        self.streaming_orchestrator.update_agent_status(agent_id, 'working')
                    if self.log_manager:
                        self.log_manager.log_agent_restart(agent_id=agent_id, reason='debate_phase_restart', phase='collaboration')
            self.system_state.phase = 'collaboration'

    def _present_final_answer(self, task: TaskInput):
        """
        Run the final presentation by the representative agent.
        """
        representative_id = self.system_state.representative_agent_id
        if not representative_id:
            logger.error('No representative agent selected')
            return
        logger.info(f'🎯 Agent {representative_id} presenting final answer')
        try:
            representative_agent = self.agents[representative_id]
            _, user_input = representative_agent._get_task_input(task)
            messages = [{'role': 'system', 'content': "\nYou are given a task and multiple agents' answers and their votes.\nPlease incorporate these information and provide a final BEST answer to the original message.\n"}, {'role': 'user', 'content': user_input + '\nPlease provide the final BEST answer to the original message by incorporating these information.\nThe final answer must be self-contained, complete, well-sourced, compelling, and ready to serve as the definitive final response.\n'}]
            result = representative_agent.process_message(messages)
            self.final_response = result.text
            self.system_state.phase = 'completed'
            self.system_state.end_time = time.time()
            logger.info(f'✅ Final presentation completed by Agent {representative_id}')
        except Exception as e:
            logger.error(f'❌ Final presentation failed: {e}')
            self.final_response = f'Error in final presentation: {str(e)}'

    def _force_consensus_by_timeout(self):
        """
        Force consensus selection when maximum duration is reached.
        """
        logger.warning('⏰ Forcing consensus due to timeout')
        with self._lock:
            vote_counts = self._get_current_vote_counts()
            if vote_counts:
                winning_agent_id = vote_counts.most_common(1)[0][0]
                logger.info(f'   Selected Agent {winning_agent_id} with {vote_counts[winning_agent_id]} votes')
            else:
                working_agents = [aid for aid, state in self.agent_states.items() if state.status == 'working']
                winning_agent_id = working_agents[0] if working_agents else list(self.agents.keys())[0]
                logger.info(f'   No votes - selected Agent {winning_agent_id} as fallback')
            self._reach_consensus(winning_agent_id)

    def _finalize_session(self) -> Dict[str, Any]:
        """
        Finalize the session and return comprehensive results.
        """
        logger.info('🏁 Finalizing session')
        with self._lock:
            if not self.system_state.end_time:
                self.system_state.end_time = time.time()
            session_duration = self.system_state.end_time - self.system_state.start_time if self.system_state.start_time else 0
            if self.log_manager:
                self.log_manager.save_agent_states(self)
                self.log_manager.log_task_completion({'final_answer': self.final_response, 'consensus_reached': self.system_state.consensus_reached, 'representative_agent_id': self.system_state.representative_agent_id, 'session_duration': session_duration})
            result = {'answer': self.final_response or 'No final answer generated', 'consensus_reached': self.system_state.consensus_reached, 'representative_agent_id': self.system_state.representative_agent_id, 'session_duration': session_duration, 'summary': {'total_agents': len(self.agents), 'failed_agents': len([s for s in self.agent_states.values() if s.status == 'failed']), 'total_votes': len(self.votes), 'final_vote_distribution': dict(self._get_current_vote_counts())}, 'system_logs': self.export_detailed_session_log()}
            if self.log_manager and (not self.log_manager.non_blocking):
                try:
                    result_file = self.log_manager.session_dir / 'result.json'
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                    logger.info(f'💾 Result saved to {result_file}')
                except Exception as e:
                    logger.warning(f'⚠️ Failed to save result.json: {e}')
            logger.info(f'✅ Session completed in {session_duration:.2f} seconds')
            logger.info(f'   Consensus: {result['consensus_reached']}')
            logger.info(f'   Representative: Agent {result['representative_agent_id']}')
            return result

    def cleanup(self):
        """
        Clean up resources and stop all agents.
        """
        logger.info('🧹 Cleaning up orchestrator resources')
        self._stop_event.set()
        if self.log_manager and self.agent_states:
            try:
                self.log_manager.save_agent_states(self)
                logger.info('✅ Final agent states saved')
            except Exception as e:
                logger.warning(f'⚠️ Error saving final agent states: {e}')
        if self.log_manager:
            try:
                self.log_manager.cleanup()
                logger.info('✅ Log manager cleaned up')
            except Exception as e:
                logger.warning(f'⚠️ Error cleaning up log manager: {e}')
        if self.streaming_orchestrator:
            try:
                self.streaming_orchestrator.cleanup()
                logger.info('✅ Streaming orchestrator cleaned up')
            except Exception as e:
                logger.warning(f'⚠️ Error cleaning up streaming orchestrator: {e}')
        logger.info('✅ Orchestrator cleanup completed')

def _get_current_voted_agents_count(self) -> int:
    """
        Get count of agents who currently have status "voted".
        """
    return len([s for s in self.agent_states.values() if s.status == 'voted'])

def _run_all_agents_with_dynamic_restart(self, task: TaskInput):
    """
        Run all agents in parallel with support for dynamic restarts.
        This approach handles agents restarting mid-execution.
        """
    active_futures = {}
    executor = ThreadPoolExecutor(max_workers=len(self.agents))
    try:
        for agent_id in self.agents.keys():
            if self.agent_states[agent_id].status not in ['failed']:
                self._start_agent_if_working(agent_id, task, executor, active_futures)
        while active_futures and (not self._all_agents_voted()):
            completed_futures = []
            for agent_id, future in list(active_futures.items()):
                if future.done():
                    completed_futures.append(agent_id)
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f'❌ Agent {agent_id} failed: {e}')
                        self.mark_agent_failed(agent_id, str(e))
            for agent_id in completed_futures:
                del active_futures[agent_id]
            for agent_id in self.agents.keys():
                if agent_id not in active_futures and self.agent_states[agent_id].status == 'working':
                    self._start_agent_if_working(agent_id, task, executor, active_futures)
            time.sleep(0.1)
    finally:
        for future in active_futures.values():
            future.cancel()
        executor.shutdown(wait=True)

def parse_completion(completion, add_citations=True):
    """Parse the completion response from Gemini API using the official SDK."""
    text = ''
    code = []
    citations = []
    function_calls = []
    if hasattr(completion, 'candidates') and completion.candidates:
        candidate = completion.candidates[0]
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    text += part.text
                elif hasattr(part, 'executable_code') and part.executable_code:
                    if hasattr(part.executable_code, 'code') and part.executable_code.code:
                        code.append(part.executable_code.code)
                    elif hasattr(part.executable_code, 'language') and hasattr(part.executable_code, 'code'):
                        code.append(part.executable_code.code)
                elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                    if hasattr(part.code_execution_result, 'output') and part.code_execution_result.output:
                        text += f'\n[Code Output]\n{part.code_execution_result.output}\n'
                elif hasattr(part, 'function_call'):
                    if part.function_call:
                        func_name = getattr(part.function_call, 'name', 'unknown')
                        func_args = {}
                        call_id = getattr(part.function_call, 'id', generate_random_id())
                        if hasattr(part.function_call, 'args') and part.function_call.args:
                            if hasattr(part.function_call.args, '_pb'):
                                try:
                                    func_args = dict(part.function_call.args)
                                except Exception:
                                    func_args = {}
                            else:
                                func_args = part.function_call.args
                        function_calls.append({'type': 'function_call', 'call_id': call_id, 'name': func_name, 'arguments': func_args})
                elif hasattr(part, 'function_response'):
                    pass
    if hasattr(completion, 'candidates') and completion.candidates:
        candidate = completion.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            grounding = candidate.grounding_metadata
            if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                for chunk in grounding.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        web_chunk = chunk.web
                        citation = {'url': getattr(web_chunk, 'uri', ''), 'title': getattr(web_chunk, 'title', ''), 'start_index': -1, 'end_index': -1}
                        citations.append(citation)
            if hasattr(grounding, 'search_entry_point') and grounding.search_entry_point:
                entry_point = grounding.search_entry_point
                if hasattr(entry_point, 'rendered_content') and entry_point.rendered_content:
                    pass
    if add_citations:
        try:
            text = add_citations_to_response(completion)
        except Exception as e:
            print(f'[GEMINI] Error adding citations to text: {e}')
    return AgentResponse(text=text, code=code, citations=citations, function_calls=function_calls)

def process_message(messages, model='gemini-2.5-flash', tools=None, max_retries=10, max_tokens=None, temperature=None, top_p=None, api_key=None, stream=False, stream_callback=None):
    """
    Generate content using Gemini API with the official google.genai SDK.

    Args:
        messages: List of messages in OpenAI format
        model: The Gemini model to use
        tools: List of tools to use
        max_retries: Maximum number of retry attempts
        max_tokens: Maximum number of tokens in response
        temperature: Temperature for generation
        top_p: Top-p value for generation
        api_key: Gemini API key (if None, will get from environment)
        stream: Whether to stream the response (default: False)
        stream_callback: Function to call with each chunk when streaming (default: None)

    Returns:
        dict: {"text": text, "code": code, "citations": citations, "function_calls": function_calls}
    """
    'Internal function that contains all the processing logic.'
    if api_key is None:
        api_key_val = os.getenv('GEMINI_API_KEY')
    else:
        api_key_val = api_key
    if not api_key_val:
        raise ValueError('GEMINI_API_KEY not found in environment variables')
    client = genai.Client(api_key=api_key_val)
    gemini_messages = []
    system_instruction = None
    function_calls = {}
    for message in messages:
        role = message.get('role', None)
        content = message.get('content', None)
        if role == 'system':
            system_instruction = content
        elif role == 'user':
            gemini_messages.append(types.Content(role='user', parts=[types.Part(text=content)]))
        elif role == 'assistant':
            gemini_messages.append(types.Content(role='model', parts=[types.Part(text=content)]))
        elif message.get('type', None) == 'function_call':
            function_calls[message['call_id']] = message
        elif message.get('type', None) == 'function_call_output':
            func_name = function_calls[message['call_id']]['name']
            func_resp = message['output']
            function_response_part = types.Part.from_function_response(name=func_name, response={'result': func_resp})
            gemini_messages.append(types.Content(role='user', parts=[function_response_part]))
    generation_config = {}
    if temperature is not None:
        generation_config['temperature'] = temperature
    if top_p is not None:
        generation_config['top_p'] = top_p
    if max_tokens is not None:
        generation_config['max_output_tokens'] = max_tokens
    gemini_tools = []
    has_native_tools = False
    custom_functions = []
    if tools:
        for tool in tools:
            if 'live_search' == tool:
                gemini_tools.append(types.Tool(google_search=types.GoogleSearch()))
                has_native_tools = True
            elif 'code_execution' == tool:
                gemini_tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
                has_native_tools = True
            else:
                if hasattr(tool, 'function'):
                    function_declaration = tool['function']
                else:
                    function_declaration = copy.deepcopy(tool)
                    if 'type' in function_declaration:
                        del function_declaration['type']
                custom_functions.append(function_declaration)
    if custom_functions and has_native_tools:
        print("[WARNING] Gemini API doesn't support combining native tools with custom functions. Prioritizing built-in tools.")
    elif custom_functions and (not has_native_tools):
        gemini_tools.append(types.Tool(function_declarations=custom_functions))
    safety_settings = [types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE), types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE), types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE), types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE)]
    request_params = {'model': model, 'contents': gemini_messages, 'config': types.GenerateContentConfig(safety_settings=safety_settings, **generation_config)}
    if system_instruction:
        request_params['config'].system_instruction = types.Content(parts=[types.Part(text=system_instruction)])
    if gemini_tools:
        request_params['config'].tools = gemini_tools
    completion = None
    retry = 0
    while retry < max_retries:
        try:
            if stream and stream_callback:
                text = ''
                code = []
                citations = []
                function_calls = []
                code_lines_shown = 0
                truncation_message_sent = False
                stream_response = client.models.generate_content_stream(**request_params)
                for chunk in stream_response:
                    chunk_text_processed = False
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                        text += chunk_text
                        try:
                            stream_callback(chunk_text)
                            chunk_text_processed = True
                        except Exception as e:
                            print(f'Stream callback error: {e}')
                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text and (not chunk_text_processed):
                                    chunk_text = part.text
                                    text += chunk_text
                                    try:
                                        stream_callback(chunk_text)
                                        chunk_text_processed = True
                                    except Exception as e:
                                        print(f'Stream callback error: {e}')
                                elif hasattr(part, 'executable_code') and part.executable_code and hasattr(part.executable_code, 'code') and part.executable_code.code:
                                    code_text = part.executable_code.code
                                    code.append(code_text)
                                    code_lines = code_text.split('\n')
                                    if code_lines_shown == 0:
                                        try:
                                            stream_callback('\n💻 Starting code execution...\n')
                                        except Exception as e:
                                            print(f'Stream callback error: {e}')
                                    for line in code_lines:
                                        if code_lines_shown < 3:
                                            try:
                                                stream_callback(line + '\n')
                                                code_lines_shown += 1
                                            except Exception as e:
                                                print(f'Stream callback error: {e}')
                                        elif code_lines_shown == 3 and (not truncation_message_sent):
                                            try:
                                                stream_callback('\n[CODE_DISPLAY_ONLY]\n💻 ... (full code in log file)\n')
                                                truncation_message_sent = True
                                                code_lines_shown += 1
                                            except Exception as e:
                                                print(f'Stream callback error: {e}')
                                        else:
                                            try:
                                                stream_callback(f'[CODE_LOG_ONLY]{line}\n')
                                            except Exception as e:
                                                print(f'Stream callback error: {e}')
                                elif hasattr(part, 'function_call') and part.function_call:
                                    func_name = getattr(part.function_call, 'name', 'unknown')
                                    func_args = {}
                                    if hasattr(part.function_call, 'args') and part.function_call.args:
                                        if hasattr(part.function_call.args, '_pb'):
                                            try:
                                                func_args = dict(part.function_call.args)
                                            except Exception:
                                                func_args = {}
                                        else:
                                            func_args = part.function_call.args
                                    function_calls.append({'type': 'function_call', 'call_id': part.function_call.id, 'name': func_name, 'arguments': func_args})
                                    try:
                                        stream_callback(f'\n🔧 Calling {func_name}\n')
                                    except Exception as e:
                                        print(f'Stream callback error: {e}')
                                elif hasattr(part, 'function_response'):
                                    try:
                                        stream_callback('\n🔧 Function response received\n')
                                    except Exception as e:
                                        print(f'Stream callback error: {e}')
                                elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                                    if hasattr(part.code_execution_result, 'output') and part.code_execution_result.output:
                                        result_text = f'\n[Code Output]\n{part.code_execution_result.output}\n'
                                        text += result_text
                                        try:
                                            stream_callback(result_text)
                                        except Exception as e:
                                            print(f'Stream callback error: {e}')
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            grounding = candidate.grounding_metadata
                            if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                                for chunk_item in grounding.grounding_chunks:
                                    if hasattr(chunk_item, 'web') and chunk_item.web:
                                        web_chunk = chunk_item.web
                                        citation = {'url': getattr(web_chunk, 'uri', ''), 'title': getattr(web_chunk, 'title', ''), 'start_index': -1, 'end_index': -1}
                                        if citation not in citations:
                                            citations.append(citation)
                try:
                    stream_callback('\n✅ Generation finished\n')
                except Exception as e:
                    print(f'Stream callback error: {e}')
                return AgentResponse(text=text, code=code, citations=citations, function_calls=function_calls)
            else:
                completion = client.models.generate_content(**request_params)
            break
        except Exception as e:
            print(f'Error on attempt {retry + 1}: {e}')
            retry += 1
            time.sleep(1.5)
    if completion is None:
        print(f'Failed to get completion after {max_retries} retries, returning empty response')
        return AgentResponse(text='', code=[], citations=[], function_calls=[])
    result = parse_completion(completion, add_citations=True)
    return result

def process_message(messages, model='grok-3-mini', tools=None, max_retries=10, max_tokens=None, temperature=None, top_p=None, api_key=None, stream=False, stream_callback=None):
    """
    Generate content using Grok API with optional streaming support and custom tools.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model name to use (default: "grok-4")
        tools: List of tool definitions for function calling, each tool should be a dict with OpenAI-compatible format:
               [
                   {
                       "type": "function",
                       "function": {
                           "name": "function_name",
                           "description": "Function description",
                           "parameters": {
                               "type": "object",
                               "properties": {
                                   "param1": {"type": "string", "description": "Parameter description"},
                                   "param2": {"type": "number", "description": "Another parameter"}
                               },
                               "required": ["param1"]
                           }
                       }
                   }
               ]
        enable_search: Boolean to enable live search functionality (default: False)
        max_retries: Maximum number of retry attempts (default: 10)
        max_tokens: Maximum tokens in response (default: 32000)
        temperature: Sampling temperature (default: None)
        top_p: Top-p sampling parameter (default: None)
        api_key: XAI API key (default: None, uses environment variable)
        stream: Enable streaming response (default: False)
        stream_callback: Callback function for streaming (default: None)

    Returns:
        Dict with keys: 'text', 'code', 'citations', 'function_calls'

    Note:
        - For backward compatibility, tools=["live_search"] is still supported and will enable search
        - Function calls will be returned in the 'function_calls' key as a list of dicts with 'name' and 'arguments'
        - The 'arguments' field will contain the function arguments as returned by the model
    """
    'Internal function that contains all the processing logic.'
    if api_key is None:
        api_key_val = os.getenv('XAI_API_KEY')
    else:
        api_key_val = api_key
    if not api_key_val:
        raise ValueError('XAI_API_KEY not found in environment variables')
    client = Client(api_key=api_key_val)
    enable_search = False
    custom_tools = []
    if tools and isinstance(tools, list) and (len(tools) > 0):
        for tool in tools:
            if tool == 'live_search':
                enable_search = True
            elif isinstance(tool, str):
                continue
            else:
                custom_tools.append(tool)
    search_parameters = None
    if enable_search:
        search_parameters = SearchParameters(mode='auto', return_citations=True)
    api_tools = None
    if custom_tools and isinstance(custom_tools, list) and (len(custom_tools) > 0):
        api_tools = []
        for custom_tool in custom_tools:
            if isinstance(custom_tool, dict) and custom_tool.get('type') == 'function':
                if 'function' in custom_tool:
                    func_def = custom_tool['function']
                else:
                    func_def = custom_tool
                xai_tool = xai_tool_func(name=func_def['name'], description=func_def['description'], parameters=func_def['parameters'])
                api_tools.append(xai_tool)
            else:
                api_tools.append(custom_tool)

    def make_grok_request(stream=False):
        chat_params = {'model': model, 'search_parameters': search_parameters}
        if temperature is not None:
            chat_params['temperature'] = temperature
        if top_p is not None:
            chat_params['top_p'] = top_p
        if max_tokens is not None:
            chat_params['max_tokens'] = max_tokens
        if api_tools is not None:
            chat_params['tools'] = api_tools
        chat = client.chat.create(**chat_params)
        for message in messages:
            role = message.get('role', None)
            content = message.get('content', None)
            if role == 'system':
                chat.append(system(content))
            elif role == 'user':
                chat.append(user(content))
            elif role == 'assistant':
                chat.append(assistant(content))
            elif message.get('type', None) == 'function_call':
                pass
            elif message.get('type', None) == 'function_call_output':
                content = message.get('output', None)
                chat.append(tool_result(content))
        if stream:
            return chat.stream()
        else:
            return chat.sample()
    completion = None
    retry = 0
    while retry < max_retries:
        try:
            is_streaming = stream and stream_callback is not None
            completion = make_grok_request(stream=is_streaming)
            break
        except Exception as e:
            print(f'Error on attempt {retry + 1}: {e}')
            retry += 1
            import time
            time.sleep(1.5)
    if completion is None:
        print(f'Failed to get completion after {max_retries} retries, returning empty response')
        return AgentResponse(text='', code=[], citations=[], function_calls=[])
    if stream and stream_callback is not None:
        text = ''
        code = []
        citations = []
        function_calls = []
        thinking_count = 0
        has_shown_search_indicator = False
        try:
            has_delta_content = False
            for response, chunk in completion:
                delta_content = None
                if hasattr(chunk, 'choices') and chunk.choices and (len(chunk.choices) > 0):
                    choice = chunk.choices[0]
                    if hasattr(choice, 'content') and choice.content:
                        delta_content = choice.content
                elif hasattr(chunk, 'content') and chunk.content:
                    delta_content = chunk.content
                elif hasattr(chunk, 'text') and chunk.text:
                    delta_content = chunk.text
                if delta_content:
                    has_delta_content = True
                    if delta_content.strip() == 'Thinking...':
                        thinking_count += 1
                        if thinking_count == 3 and (not has_shown_search_indicator) and search_parameters:
                            try:
                                stream_callback('\n🧠 Thinking...\n')
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                            has_shown_search_indicator = True
                        try:
                            stream_callback(delta_content)
                        except Exception as e:
                            print(f'Stream callback error: {e}')
                    else:
                        text += delta_content
                        try:
                            stream_callback(delta_content)
                        except Exception as e:
                            print(f'Stream callback error: {e}')
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        if hasattr(tool_call, 'function'):
                            _func_call = {'type': 'function_call', 'call_id': tool_call.id, 'name': tool_call.function.name, 'arguments': tool_call.function.arguments}
                            if _func_call not in function_calls:
                                function_calls.append(_func_call)
                        elif hasattr(tool_call, 'name') and hasattr(tool_call, 'arguments'):
                            _func_call = {'type': 'function_call', 'call_id': tool_call.id, 'name': tool_call.name, 'arguments': tool_call.arguments}
                            if _func_call not in function_calls:
                                function_calls.append(_func_call)
                elif hasattr(response, 'choices') and response.choices:
                    for choice in response.choices:
                        if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                            for tool_call in choice.message.tool_calls:
                                if hasattr(tool_call, 'function'):
                                    _func_call = {'type': 'function_call', 'call_id': tool_call.id, 'name': tool_call.function.name, 'arguments': tool_call.function.arguments}
                                    if _func_call not in function_calls:
                                        function_calls.append(_func_call)
                                elif hasattr(tool_call, 'name') and hasattr(tool_call, 'arguments'):
                                    _func_call = {'type': 'function_call', 'call_id': tool_call.id, 'name': tool_call.name, 'arguments': tool_call.arguments}
                                    if _func_call not in function_calls:
                                        function_calls.append(_func_call)
                if hasattr(response, 'citations') and response.citations:
                    citations = []
                    for citation in response.citations:
                        citations.append({'url': citation, 'title': '', 'start_index': -1, 'end_index': -1})
                    if citations and enable_search and (stream_callback is not None):
                        try:
                            stream_callback(f'\n\n🔍 Found {len(citations)} web sources\n')
                        except Exception as e:
                            print(f'Stream callback error: {e}')
            if not has_delta_content:
                if text:
                    stream_callback(text)
                if function_calls:
                    for function_call in function_calls:
                        stream_callback(f'🔧 Calling function: {function_call['name']}\n')
                        stream_callback(f'🔧 Arguments: {json.dumps(function_call['arguments'], indent=4)}\n\n')
        except Exception:
            completion = make_grok_request(stream=False)
            result = parse_completion(completion, add_citations=True)
            return result
        result = AgentResponse(text=text, code=code, citations=citations, function_calls=function_calls)
    else:
        result = parse_completion(completion, add_citations=True)
    return result

def test_gemini_planning_mode():
    """Test that Gemini backend respects planning mode for MCP tool blocking."""
    print('🧪 Testing Gemini Backend Planning Mode...')
    print('=' * 50)
    agent_config = AgentConfig(backend_params={'backend_type': 'gemini', 'model': 'gemini-2.5-flash', 'api_key': 'dummy-key'})
    try:
        backend = GeminiBackend(config=agent_config)
        print('✅ Gemini backend created successfully')
    except Exception as e:
        print(f'❌ Failed to create Gemini backend: {e}')
        return False
    print('\n1. Testing planning mode flag...')
    assert not backend.is_planning_mode_enabled(), 'Planning mode should be disabled by default'
    print('✅ Planning mode disabled by default')
    backend.set_planning_mode(True)
    assert backend.is_planning_mode_enabled(), 'Planning mode should be enabled'
    print('✅ Planning mode can be enabled')
    backend.set_planning_mode(False)
    assert not backend.is_planning_mode_enabled(), 'Planning mode should be disabled'
    print('✅ Planning mode can be disabled')
    print('\n2. Testing Gemini backend inheritance...')
    assert hasattr(backend, 'set_planning_mode'), 'GeminiBackend should have set_planning_mode'
    assert hasattr(backend, 'is_planning_mode_enabled'), 'GeminiBackend should have is_planning_mode_enabled'
    print('✅ GeminiBackend has planning mode methods')
    print('\n🎉 All Gemini planning mode tests passed!')
    print('✅ Gemini backend respects planning mode flags')
    print('✅ MCP tool blocking should work during coordination phase')
    return True

def test_gemini_planning_mode_vs_other_backends():
    """Test that Gemini planning mode works differently from MCP-based backends."""
    print('\n🧪 Testing Gemini Planning Mode vs Other Backends...')
    print('=' * 55)
    backend = GeminiBackend(api_key='test-key')
    print("\n1. Testing Gemini's unique planning mode approach...")
    from massgen.backend.base import LLMBackend
    from massgen.backend.base_with_mcp import MCPBackend
    assert isinstance(backend, LLMBackend), 'Gemini should inherit from LLMBackend'
    assert not isinstance(backend, MCPBackend), 'Gemini should NOT inherit from MCPBackend'
    print('✅ Gemini has correct inheritance hierarchy')
    assert hasattr(backend, '_mcp_client'), 'Gemini should have _mcp_client attribute'
    assert hasattr(backend, '_setup_mcp_tools'), 'Gemini should have _setup_mcp_tools method'
    print('✅ Gemini has custom MCP implementation')
    backend.set_planning_mode(True)
    print('   Planning mode approach: Tool registration blocking (not execution blocking)')
    print(f'   Planning mode enabled: {backend.is_planning_mode_enabled()}')
    print('   Expected: MCP tools will not be registered in Gemini SDK config')
    has_mcp_execution_method = hasattr(backend, '_execute_mcp_function_with_retry')
    print(f'   Has MCPBackend execution method: {has_mcp_execution_method}')
    print('✅ Gemini uses tool registration blocking, not execution-time blocking')
    print('\n✅ Gemini planning mode approach is distinct and appropriate!')
    return True

def test_initialization_with_valid_adapter():
    """Test backend initialization with valid adapter type."""
    backend = ExternalAgentBackend(adapter_type='test')
    assert backend.adapter_type == 'test'
    assert isinstance(backend.adapter, SimpleTestAdapter)
    assert backend.get_provider_name() == 'test'

def test_initialization_with_invalid_adapter():
    """Test backend initialization with invalid adapter type."""
    with pytest.raises(ValueError) as exc_info:
        ExternalAgentBackend(adapter_type='nonexistent')
    assert 'Unsupported framework' in str(exc_info.value)
    assert 'nonexistent' in str(exc_info.value)

def test_adapter_type_case_insensitive():
    """Test that adapter type is case-insensitive."""
    backend1 = ExternalAgentBackend(adapter_type='TEST')
    backend2 = ExternalAgentBackend(adapter_type='Test')
    backend3 = ExternalAgentBackend(adapter_type='test')
    assert backend1.adapter_type == 'test'
    assert backend2.adapter_type == 'test'
    assert backend3.adapter_type == 'test'

def test_extract_adapter_config():
    """Test extraction of adapter-specific config."""
    backend = ExternalAgentBackend(adapter_type='test', type='test', agent_id='test_agent', session_id='session_1', custom_param='value', temperature=0.7)
    assert 'custom_param' in backend.adapter.config
    assert 'temperature' in backend.adapter.config
    assert 'type' not in backend.adapter.config
    assert 'agent_id' not in backend.adapter.config
    assert 'session_id' not in backend.adapter.config

def test_is_stateful_default():
    """Test stateful check with default adapter."""
    backend = ExternalAgentBackend(adapter_type='test')
    assert backend.is_stateful() is False

def test_clear_history():
    """Test clearing history."""
    backend = ExternalAgentBackend(adapter_type='test')
    backend.adapter._conversation_history = [{'role': 'user', 'content': 'test'}]
    backend.clear_history()
    assert len(backend.adapter._conversation_history) == 0

def test_reset_state():
    """Test resetting state."""
    backend = ExternalAgentBackend(adapter_type='test')
    backend.adapter._conversation_history = [{'role': 'user', 'content': 'test'}]
    backend.reset_state()
    assert len(backend.adapter._conversation_history) == 0

def test_get_final_presentation_method():
    from massgen.orchestrator import Orchestrator
    import inspect
    assert hasattr(Orchestrator, 'get_final_presentation')
    sig = inspect.signature(Orchestrator.get_final_presentation)
    assert list(sig.parameters.keys()) == ['self', 'selected_agent_id', 'vote_results']

class AgentAdapter(ABC):
    """
    Abstract base class for external agent adapters.

    Adapters handle:
    - Message format conversion between MassGen and external agents
    - Tool/function conversion and mapping
    - Streaming simulation for non-streaming agents
    - State management for stateful agents
    """

    def __init__(self, **kwargs):
        """Initialize adapter with agent-specific configuration."""
        self.config = kwargs
        self._conversation_history = []
        self.coordination_stage = None

    @abstractmethod
    async def execute_streaming(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response with tool support.

        This method must:
        1. Convert MassGen messages to agent format
        2. Convert MassGen tools to agent format
        3. Call the agent
        4. Convert response back to MassGen format
        5. Simulate streaming if agent doesn't support it

        Args:
            messages: MassGen format messages
            tools: MassGen format tools
            **kwargs: Additional parameters

        Yields:
            StreamChunk: Standardized response chunks

        """

    async def simulate_streaming(self, content: str, tool_calls: Optional[List[Dict[str, Any]]]=None, delay: float=0.01) -> AsyncGenerator[StreamChunk, None]:
        """
        Simulate streaming for agents that don't support it natively.

        Args:
            content: Complete response content
            tool_calls: Tool calls to include
            delay: Delay between chunks (seconds)

        Yields:
            StreamChunk: Simulated streaming chunks
        """
        if content:
            words = content.split()
            for i, word in enumerate(words):
                chunk_text = word + (' ' if i < len(words) - 1 else '')
                yield StreamChunk(type='content', content=chunk_text)
                await asyncio.sleep(delay)
        if tool_calls:
            yield StreamChunk(type='tool_calls', tool_calls=tool_calls)
        complete_message = {'role': 'assistant', 'content': content or ''}
        if tool_calls:
            complete_message['tool_calls'] = tool_calls
        yield StreamChunk(type='complete_message', complete_message=complete_message)
        yield StreamChunk(type='done')

    @staticmethod
    def _get_tool_name(tool: Dict[str, Any]) -> str:
        """
        Extract tool name from tool schema.

        Supports both formats:
        - {"type": "function", "function": {"name": "tool_name", ...}}
        - {"name": "tool_name", ...}
        """
        if 'function' in tool:
            return tool['function'].get('name', '')
        return tool.get('name', '')

    def convert_messages_from_massgen(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Convert MassGen messages to agent-specific format.

        Override this method for agent-specific conversion.

        Args:
            messages: List of MassGen format messages

        Returns:
            agent-specific message format
        """
        return messages

    def convert_response_to_massgen(self, response: Any) -> Dict[str, Any]:
        """
        Convert agent response to MassGen format.

        Override this method for agent-specific conversion.

        Args:
            response: agent-specific response

        Returns:
            MassGen format response with content and optional tool_calls
        """
        return {'content': str(response), 'tool_calls': None}

    def convert_tools_from_massgen(self, tools: List[Dict[str, Any]]) -> Any:
        """
        Convert MassGen tools to agent-specific format.

        Override this method for agent-specific conversion.

        Args:
            tools: List of MassGen format tools

        Returns:
            agent-specific tool format
        """
        return tools

    def is_stateful(self) -> bool:
        """
        Check if this adapter maintains conversation state.

        Override if your agent is stateless.
        """
        return False

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history.clear()

    def reset_state(self) -> None:
        """Reset adapter state."""
        self.clear_history()

    def set_stage(self, stage: CoordinationStage) -> None:
        """Set the coordination stage for the adapter, if applicable."""
        self.coordination_stage = stage

def reset_state(self) -> None:
    """Reset adapter state."""
    self.clear_history()

def test_convert_messages_default():
    """Test default message conversion (passthrough)."""
    adapter = MockAdapter()
    messages = [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hi'}]
    result = adapter.convert_messages_from_massgen(messages)
    assert result == messages

def test_convert_tools_default():
    """Test default tool conversion (passthrough)."""
    adapter = MockAdapter()
    tools = [{'type': 'function', 'function': {'name': 'search', 'description': 'Search tool'}}]
    result = adapter.convert_tools_from_massgen(tools)
    assert result == tools

def test_is_stateful_default():
    """Test default stateful behavior."""
    adapter = MockAdapter()
    assert adapter.is_stateful() is False

def test_clear_history():
    """Test clearing conversation history."""
    adapter = MockAdapter()
    adapter._conversation_history = [{'role': 'user', 'content': 'test'}]
    adapter.clear_history()
    assert len(adapter._conversation_history) == 0

def test_reset_state():
    """Test resetting adapter state."""
    adapter = MockAdapter()
    adapter._conversation_history = [{'role': 'user', 'content': 'test'}]
    adapter.reset_state()
    assert len(adapter._conversation_history) == 0

class APIParamsHandlerBase(ABC):
    """Abstract base class for API parameter handlers."""

    def __init__(self, backend_instance: Any):
        """Initialize the API params handler.

        Args:
            backend_instance: The backend instance containing necessary formatters and config
        """
        self.backend = backend_instance
        self.formatter = backend_instance.formatter

    @abstractmethod
    async def build_api_params(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build API parameters for the specific backend.

        Args:
            messages: List of messages in framework format
            tools: List of tools in framework format
            all_params: All parameters including config and runtime params

        Returns:
            Dictionary of API parameters ready for the backend
        """

    @abstractmethod
    def get_excluded_params(self) -> Set[str]:
        """Get backend-specific parameters to exclude from API calls."""

    @abstractmethod
    def get_provider_tools(self, all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get provider-specific tools based on parameters."""

    def get_base_excluded_params(self) -> Set[str]:
        """Get common parameters to exclude across all backends."""
        return {'upload_files', 'cwd', 'agent_temporary_workspace', 'context_paths', 'context_write_access_enabled', 'enable_image_generation', 'enable_mcp_command_line', 'command_line_allowed_commands', 'command_line_blocked_commands', 'command_line_execution_mode', 'command_line_docker_image', 'command_line_docker_memory_limit', 'command_line_docker_cpu_limit', 'command_line_docker_network_mode', 'enable_audio_generation', 'type', 'agent_id', 'session_id', 'mcp_servers'}

    def build_base_api_params(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build base API parameters common to most backends."""
        api_params = {'stream': True}
        excluded = self.get_excluded_params()
        for key, value in all_params.items():
            if key not in excluded and value is not None:
                api_params[key] = value
        return api_params

    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get MCP tools from backend if available."""
        if hasattr(self.backend, '_mcp_functions') and self.backend._mcp_functions:
            if hasattr(self.backend, 'get_mcp_tools_formatted'):
                return self.backend.get_mcp_tools_formatted()
        return []

def get_mcp_tools(self) -> List[Dict[str, Any]]:
    """Get MCP tools from backend if available."""
    if hasattr(self.backend, '_mcp_functions') and self.backend._mcp_functions:
        if hasattr(self.backend, 'get_mcp_tools_formatted'):
            return self.backend.get_mcp_tools_formatted()
    return []

class ResponseAPIParamsHandler(APIParamsHandlerBase):
    """Handler for Response API parameters."""

    def get_excluded_params(self) -> Set[str]:
        """Get parameters to exclude from Response API calls."""
        return self.get_base_excluded_params().union({'enable_web_search', 'enable_code_interpreter', 'allowed_tools', 'exclude_tools', '_has_file_search_files'})

    def get_provider_tools(self, all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get provider tools for Response API format."""
        provider_tools = []
        if all_params.get('enable_web_search', False):
            provider_tools.append({'type': 'web_search'})
        if all_params.get('enable_code_interpreter', False):
            provider_tools.append({'type': 'code_interpreter', 'container': {'type': 'auto'}})
        return provider_tools

    def _convert_mcp_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function format for Response API."""
        if not hasattr(self.backend, '_mcp_functions') or not self.backend._mcp_functions:
            return []
        converted_tools = []
        for function in self.backend._mcp_functions.values():
            converted_tools.append(function.to_openai_format())
        return converted_tools

    async def build_api_params(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build Response API parameters."""
        converted_messages = self.formatter.format_messages(messages)
        api_params = {'input': converted_messages, 'stream': True}
        excluded = self.get_excluded_params()
        for key, value in all_params.items():
            if key not in excluded and value is not None:
                if key == 'max_tokens':
                    api_params['max_output_tokens'] = value
                else:
                    api_params[key] = value
        combined_tools = api_params.setdefault('tools', [])
        provider_tools = self.get_provider_tools(all_params)
        if provider_tools:
            combined_tools.extend(provider_tools)
        if tools:
            converted_tools = self.formatter.format_tools(tools)
            combined_tools.extend(converted_tools)
        mcp_tools = self._convert_mcp_tools_to_openai_format()
        if mcp_tools:
            combined_tools.extend(mcp_tools)
        if combined_tools:
            api_params['tools'] = combined_tools
        vector_store_ids = all_params.get('_file_search_vector_store_ids')
        if vector_store_ids:
            if not isinstance(vector_store_ids, list):
                vector_store_ids = [vector_store_ids]
            file_search_tool_index = None
            for i, tool in enumerate(combined_tools):
                if tool.get('type') == 'file_search':
                    file_search_tool_index = i
                    break
            if file_search_tool_index is not None:
                combined_tools[file_search_tool_index]['vector_store_ids'] = vector_store_ids
            else:
                combined_tools.append({'type': 'file_search', 'vector_store_ids': vector_store_ids})
        return api_params

def _convert_mcp_tools_to_openai_format(self) -> List[Dict[str, Any]]:
    """Convert MCP tools to OpenAI function format for Response API."""
    if not hasattr(self.backend, '_mcp_functions') or not self.backend._mcp_functions:
        return []
    converted_tools = []
    for function in self.backend._mcp_functions.values():
        converted_tools.append(function.to_openai_format())
    return converted_tools

