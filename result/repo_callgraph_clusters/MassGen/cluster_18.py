# Cluster 18

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

def create_research_config(model: str='gpt-4o', backend: str='openai') -> AgentConfig:
    """Create configuration for research tasks (web search enabled)."""
    return AgentConfig.for_research_task(model, backend)

def create_computational_config(model: str='gpt-4o', backend: str='openai') -> AgentConfig:
    """Create configuration for computational tasks (code execution enabled)."""
    return AgentConfig.for_computational_task(model, backend)

def create_expert_agent(domain: str, backend: LLMBackend, model: str='gpt-4o-mini') -> ConfigurableAgent:
    """Create an expert agent for a specific domain."""
    from .agent_config import AgentConfig
    config = AgentConfig.for_expert_domain(domain, model=model)
    return ConfigurableAgent(config=config, backend=backend)

def create_research_agent(backend: LLMBackend, model: str='gpt-4o-mini') -> ConfigurableAgent:
    """Create a research agent with web search capabilities."""
    from .agent_config import AgentConfig
    config = AgentConfig.for_research_task(model=model)
    return ConfigurableAgent(config=config, backend=backend)

def create_computational_agent(backend: LLMBackend, model: str='gpt-4o-mini') -> ConfigurableAgent:
    """Create a computational agent with code execution."""
    from .agent_config import AgentConfig
    config = AgentConfig.for_computational_task(model=model)
    return ConfigurableAgent(config=config, backend=backend)

def _substitute_variables(obj: Any, variables: Dict[str, str]) -> Any:
    """Recursively substitute ${var} references in config with actual values.

    Args:
        obj: Config object (dict, list, str, or other)
        variables: Dict of variable names to values

    Returns:
        Config object with variables substituted
    """
    if isinstance(obj, dict):
        return {k: _substitute_variables(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_variables(item, variables) for item in obj]
    elif isinstance(obj, str):
        result = obj
        for var_name, var_value in variables.items():
            result = result.replace(f'${{{var_name}}}', var_value)
        return result
    else:
        return obj

def create_agents_from_config(config: Dict[str, Any], orchestrator_config: Optional[Dict[str, Any]]=None) -> Dict[str, ConfigurableAgent]:
    """Create agents from configuration."""
    agents = {}
    agent_entries = [config['agent']] if 'agent' in config else config.get('agents', None)
    if not agent_entries:
        raise ConfigurationError("Configuration must contain either 'agent' or 'agents' section")
    for i, agent_data in enumerate(agent_entries, start=1):
        backend_config = agent_data.get('backend', {})
        if 'cwd' in backend_config:
            variables = {'cwd': backend_config['cwd']}
            backend_config = _substitute_variables(backend_config, variables)
        backend_type = backend_config.get('type') or (get_backend_type_from_model(backend_config['model']) if 'model' in backend_config else None)
        if not backend_type:
            raise ConfigurationError('Backend type must be specified or inferrable from model')
        if orchestrator_config:
            if 'agent_temporary_workspace' in orchestrator_config:
                backend_config['agent_temporary_workspace'] = orchestrator_config['agent_temporary_workspace']
            if 'context_paths' in orchestrator_config:
                agent_context_paths = backend_config.get('context_paths', [])
                orchestrator_context_paths = orchestrator_config['context_paths']
                merged_paths = orchestrator_context_paths.copy()
                orchestrator_paths_set = {path.get('path') for path in orchestrator_context_paths}
                for agent_path in agent_context_paths:
                    if agent_path.get('path') not in orchestrator_paths_set:
                        merged_paths.append(agent_path)
                backend_config['context_paths'] = merged_paths
        backend = create_backend(backend_type, **backend_config)
        backend_params = {k: v for k, v in backend_config.items() if k != 'type'}
        backend_type_lower = backend_type.lower()
        if backend_type_lower == 'openai':
            agent_config = AgentConfig.create_openai_config(**backend_params)
        elif backend_type_lower == 'claude':
            agent_config = AgentConfig.create_claude_config(**backend_params)
        elif backend_type_lower == 'grok':
            agent_config = AgentConfig.create_grok_config(**backend_params)
        elif backend_type_lower == 'gemini':
            agent_config = AgentConfig.create_gemini_config(**backend_params)
        elif backend_type_lower == 'zai':
            agent_config = AgentConfig.create_zai_config(**backend_params)
        elif backend_type_lower == 'chatcompletion':
            agent_config = AgentConfig.create_chatcompletion_config(**backend_params)
        elif backend_type_lower == 'lmstudio':
            agent_config = AgentConfig.create_lmstudio_config(**backend_params)
        elif backend_type_lower == 'vllm':
            agent_config = AgentConfig.create_vllm_config(**backend_params)
        elif backend_type_lower == 'sglang':
            agent_config = AgentConfig.create_sglang_config(**backend_params)
        else:
            agent_config = AgentConfig(backend_params=backend_config)
        agent_config.agent_id = agent_data.get('id', f'agent{i}')
        system_msg = agent_data.get('system_message')
        if system_msg:
            if backend_type_lower == 'claude_code':
                agent_config.backend_params['append_system_prompt'] = system_msg
            else:
                agent_config.custom_system_instruction = system_msg
        agent = ConfigurableAgent(config=agent_config, backend=backend)
        agents[agent.config.agent_id] = agent
    return agents

def _validate_non_empty_string(value: Any, field_name: str) -> None:
    """Validate that value is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field_name} must be a non-empty string')

def _validate_string_length(value: str, max_length: int, field_name: str) -> None:
    """Validate string length."""
    if len(value) > max_length:
        raise ValueError(f'{field_name} too long: {len(value)} > {max_length} characters')

def validate_url(url: str, *, resolve_dns: bool=False, allow_private_ips: bool=False, allow_localhost: bool=False, allowed_hostnames: Optional[Set[str]]=None) -> bool:
    """
    Validate URL for security and correctness.

    Args:
        url: URL to validate
        resolve_dns: If True, resolve hostnames and validate the resulting IPs
        allow_private_ips: If True, do not block private/link-local/reserved ranges
        allow_localhost: If True, allow localhost/loopback addresses
        allowed_hostnames: Optional explicit allowlist for hostnames

    Returns:
        True if URL is valid and safe

    Raises:
        ValueError: If URL is invalid or potentially dangerous
    """
    if not url or not isinstance(url, str):
        raise ValueError('URL must be a non-empty string')
    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f'URL too long: {len(url)} > {MAX_URL_LENGTH} characters')
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise ValueError(f'Invalid URL format: {e}')
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f'Unsupported URL scheme: {parsed.scheme}. Only http and https are allowed.')
    if not parsed.hostname:
        raise ValueError('URL must include a hostname')
    hostname = parsed.hostname.lower()
    if allowed_hostnames and hostname in {h.lower() for h in allowed_hostnames}:
        pass
    else:
        if not allow_localhost and hostname in {'localhost', 'ip6-localhost'}:
            raise ValueError(f'Hostname not allowed for security reasons: {hostname}')
        ip_obj: Optional[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]
        try:
            ip_obj = ipaddress.ip_address(hostname)
        except ValueError:
            ip_obj = None

        def _is_forbidden_ip(ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
            if allow_private_ips:
                return False
            return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        if ip_obj is not None:
            if _is_forbidden_ip(ip_obj) and (not (allow_localhost and ip_obj.is_loopback)):
                raise ValueError(f'IP address not allowed for security reasons: {hostname}')
        elif resolve_dns:
            try:
                port_for_resolution = parsed.port if parsed.port is not None else 443 if parsed.scheme == 'https' else 80
                addrinfos = socket.getaddrinfo(hostname, port_for_resolution, proto=socket.IPPROTO_TCP)
                for ai in addrinfos:
                    sockaddr = ai[4]
                    ip_literal = sockaddr[0]
                    try:
                        resolved_ip = ipaddress.ip_address(ip_literal)
                        if _is_forbidden_ip(resolved_ip) and (not (allow_localhost and resolved_ip.is_loopback)):
                            raise ValueError(f'Resolved IP not allowed for security reasons: {hostname} -> {resolved_ip}')
                    except ValueError:
                        continue
            except socket.gaierror as e:
                raise ValueError(f"Failed to resolve hostname '{hostname}': {e}")
    if parsed.port is not None:
        if not 1 <= parsed.port <= 65535:
            raise ValueError(f'Invalid port number: {parsed.port}')
        dangerous_ports = {22, 23, 25, 53, 135, 139, 445, 1433, 1521, 3306, 3389, 5432, 6379}
        if parsed.port in dangerous_ports:
            raise ValueError(f'Port {parsed.port} is not allowed for security reasons')
    return True

def validate_tool_arguments(arguments: Dict[str, Any], max_depth: int=MAX_TOOL_ARG_DEPTH, max_size: int=MAX_TOOL_ARG_SIZE) -> Dict[str, Any]:
    """
    Validate tool arguments for security and size limits.

    Args:
        arguments: Tool arguments dictionary
        max_depth: Maximum nesting depth allowed
        max_size: Maximum total size of arguments (rough estimate)

    Returns:
        Validated arguments dictionary

    Raises:
        ValueError: If arguments are invalid or too large
    """
    if not isinstance(arguments, dict):
        raise ValueError('Tool arguments must be a dictionary')
    current_size = 0

    def _add_size(amount: int) -> None:
        nonlocal current_size
        current_size += amount
        if current_size > max_size:
            raise ValueError(f'Tool arguments too large: ~{current_size} > {max_size} bytes')

    def _size_for_primitive(value: Any) -> int:
        if value is None:
            return 4
        if isinstance(value, bool):
            return 4 if value else 5
        if isinstance(value, (int, float)):
            return len(str(value))
        if isinstance(value, str):
            return len(value) + 2
        return len(str(value)) + 2

    def _validate_value(value: Any, depth: int=0) -> Any:
        if depth > max_depth:
            raise ValueError(f'Tool arguments nested too deeply: {depth} > {max_depth}')
        if isinstance(value, dict):
            if len(value) > MAX_DICT_KEYS:
                raise ValueError(f'Dictionary too large: {len(value)} > {MAX_DICT_KEYS} keys')
            _add_size(2)
            validated: Dict[str, Any] = {}
            first = True
            for k, v in value.items():
                if not isinstance(k, str):
                    k = str(k)
                if not first:
                    _add_size(1)
                first = False
                _add_size(_size_for_primitive(k) + 1)
                validated[k] = _validate_value(v, depth + 1)
            return validated
        elif isinstance(value, list):
            if len(value) > MAX_LIST_ITEMS:
                raise ValueError(f'List too large: {len(value)} > {MAX_LIST_ITEMS} items')
            _add_size(2)
            validated_list = []
            for idx, item in enumerate(value):
                if idx > 0:
                    _add_size(1)
                validated_list.append(_validate_value(item, depth + 1))
            return validated_list
        elif isinstance(value, str):
            if len(value) > MAX_STRING_LENGTH:
                raise ValueError(f'String too long: {len(value)} > {MAX_STRING_LENGTH} characters')
            _add_size(_size_for_primitive(value))
            return value
        elif isinstance(value, (int, float, bool)) or value is None:
            _add_size(_size_for_primitive(value))
            return value
        else:
            str_value = str(value)
            if len(str_value) > MAX_STRING_LENGTH:
                raise ValueError(f'Value too large when converted to string: {len(str_value)} > {MAX_STRING_LENGTH}')
            _add_size(_size_for_primitive(str_value))
            return str_value
    return _validate_value(arguments)

def _add_size(amount: int) -> None:
    nonlocal current_size
    current_size += amount
    if current_size > max_size:
        raise ValueError(f'Tool arguments too large: ~{current_size} > {max_size} bytes')

def _validate_path_access(path: Path, allowed_paths: List[Path]) -> None:
    """
    Validate that a path is within allowed directories.

    Args:
        path: Path to validate
        allowed_paths: List of allowed base paths

    Raises:
        ValueError: If path is not within allowed directories
    """
    if not allowed_paths:
        return
    for allowed_path in allowed_paths:
        try:
            path.relative_to(allowed_path)
            return
        except ValueError:
            continue
    raise ValueError(f'Path not in allowed directories: {path}')

def _validate_path_access(path: Path, allowed_paths: List[Path]) -> None:
    """
    Validate that a path is within allowed directories.

    Args:
        path: Path to validate
        allowed_paths: List of allowed base paths

    Raises:
        ValueError: If path is not within allowed directories
    """
    if not allowed_paths:
        return
    for allowed_path in allowed_paths:
        try:
            path.relative_to(allowed_path)
            return
        except ValueError:
            continue
    raise ValueError(f'Path not in allowed directories: {path}')

def _sanitize_command(command: str) -> None:
    """
    Sanitize the command to prevent dangerous operations.

    Adapted from AG2's LocalCommandLineCodeExecutor.sanitize_command().
    This provides basic protection for users running commands outside Docker.

    Args:
        command: The command to sanitize

    Raises:
        ValueError: If dangerous command is detected
    """
    dangerous_patterns = [('\\brm\\s+-rf\\s+/', "Use of 'rm -rf /' is not allowed"), ('\\bmv\\b.*?\\s+/dev/null', 'Moving files to /dev/null is not allowed'), ('\\bdd\\b', "Use of 'dd' command is not allowed"), ('>\\s*/dev/sd[a-z][1-9]?', 'Overwriting disk blocks directly is not allowed'), (':\\(\\)\\{\\s*:\\|\\:&\\s*\\};:', 'Fork bombs are not allowed'), ('\\bsudo\\b', "Use of 'sudo' is not allowed"), ('\\bsu\\b', "Use of 'su' is not allowed"), ('\\bchown\\b', "Use of 'chown' is not allowed"), ('\\bchmod\\b', "Use of 'chmod' is not allowed")]
    for pattern, message in dangerous_patterns:
        if re.search(pattern, command):
            raise ValueError(f'Potentially dangerous command detected: {message}')

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

def _is_code_content(self, content: str) -> bool:
    """Check if content appears to be code."""
    for pattern in self.code_patterns:
        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
            return True
    return False

@dataclass
class AgentConfig:
    """Complete configuration for a single agent."""
    agent_id: int
    agent_type: str
    model_config: ModelConfig

    def __post_init__(self):
        """Validate agent configuration."""
        if self.agent_type not in ['openai', 'gemini', 'grok']:
            raise ValueError(f'Invalid agent_type: {self.agent_type}. Must be one of: openai, gemini, grok')

def __post_init__(self):
    """Validate agent configuration."""
    if self.agent_type not in ['openai', 'gemini', 'grok']:
        raise ValueError(f'Invalid agent_type: {self.agent_type}. Must be one of: openai, gemini, grok')

def create_agent(agent_type: str, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, **kwargs) -> MassAgent:
    """
    Factory function to create agents of different types.

    Args:
        agent_type: Type of agent ("openai", "gemini", "grok")
        agent_id: Unique identifier for the agent
        orchestrator: Reference to the MassOrchestrator
        model_config: Model configuration
        **kwargs: Additional arguments

    Returns:
        MassAgent instance of the specified type
    """
    agent_classes = {'openai': OpenAIMassAgent, 'gemini': GeminiMassAgent, 'grok': GrokMassAgent}
    if agent_type not in agent_classes:
        raise ValueError(f'Unknown agent type: {agent_type}. Available types: {list(agent_classes.keys())}')
    return agent_classes[agent_type](agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, **kwargs)

class AG2Adapter(AgentAdapter):
    """
    Adapter for AG2 (AutoGen) framework.

    Supports:
    - Single AG2 agents (ConversableAgent, AssistantAgent)
    - Function/tool calling
    - Code execution with multiple executor types:
      * LocalCommandLineCodeExecutor (local shell)
      * DockerCommandLineCodeExecutor (Docker containers)
      * JupyterCodeExecutor (Jupyter kernels)
      * YepCodeCodeExecutor (YepCode serverless)
    - Async execution with a_generate_reply
    - No human-in-the-loop (autonomous operation)

    Todos:
    - Group chat support with patterns (e.g., AutoPattern, DefaultPattern, etc.)
    - More tool support including MCP
    """

    def __init__(self, **kwargs):
        """
        Initialize AG2 adapter.

        The adapter receives the entire backend configuration from MassGen.
        It should contain EITHER 'agent_config' OR 'group_config' (not both).

        Args:
            **kwargs: Backend configuration containing either:
                - agent_config: Configuration for single AG2 agent
                - group_config: Configuration for AG2 GroupChat
        """
        super().__init__(**kwargs)
        setup_api_keys()
        self.agent_config = kwargs.get('agent_config')
        self.group_config = kwargs.get('group_config')
        if self.agent_config and self.group_config:
            raise ValueError("Backend configuration should contain EITHER 'agent_config' OR 'group_config', not both.")
        if not self.agent_config and (not self.group_config):
            raise ValueError("Backend configuration must contain either 'agent_config' for single agent or 'group_config' for GroupChat.")
        self.agent_id = None
        self._setup_agents()

    def _setup_agents(self):
        """Set up AG2 agents based on configuration."""
        if self.group_config:
            self._setup_group_chat()
        else:
            self._setup_single_agent()

    def _setup_single_agent(self):
        """Set up a single AG2 agent."""
        self.agent = setup_agent_from_config(self.agent_config)
        self.is_group_chat = False

    def _setup_group_chat(self):
        """Set up AG2 GroupChat with multiple agents and pattern."""
        if 'pattern' not in self.group_config:
            raise ValueError("group_config must include 'pattern' configuration")
        self.default_llm_config = self.group_config.get('llm_config')
        if not self.default_llm_config:
            raise ValueError("group_config must include 'llm_config' as default for all agents")
        agents = []
        agent_name_map = {}
        for agent_cfg in self.group_config.get('agents', []):
            agent = setup_agent_from_config(agent_cfg, default_llm_config=self.default_llm_config)
            agents.append(agent)
            agent_name_map[agent.name] = agent
        if not agents:
            raise ValueError('No valid agents configured for group chat')
        pattern_config = self.group_config['pattern']
        pattern_type = pattern_config.get('type')
        if not pattern_type:
            raise ValueError("pattern configuration must include 'type' field")
        if pattern_type not in SUPPORTED_GROUPCHAT_PATTERNS:
            raise NotImplementedError(f"Pattern type '{pattern_type}' not supported. Supported types: {', '.join(SUPPORTED_GROUPCHAT_PATTERNS)}")
        self.user_agent = self._setup_user_agent(user_agent_config=self.group_config.get('user_agent'), default_llm_config=self.default_llm_config)
        group_manager_args = self._setup_group_manager_args(pattern_config, self.default_llm_config)
        self.pattern = self._create_pattern(pattern_type, pattern_config, agents, agent_name_map, group_manager_args)
        self.agents = agents
        self.group_max_rounds = self.group_config.get('max_rounds', DEFAULT_MAX_ROUNDS)
        self.is_group_chat = True
        logger.info(f'[AG2Adapter] GroupChat setup complete with {len(agents)} agents and {pattern_type} pattern')

    def _setup_user_agent(self, user_agent_config: Any, default_llm_config: Any) -> ConversableAgent:
        """
        Set up user_agent for group chat.

        User agent makes final decisions and calls workflow tools.
        Its name MUST be "User" for termination condition to work.

        Args:
            user_agent_config: Optional user agent configuration from YAML
            default_llm_config: Default llm_config to use if not specified

        Returns:
            ConversableAgent with name "User"
        """
        if user_agent_config:
            user_agent = setup_agent_from_config(user_agent_config, default_llm_config=default_llm_config)
            if user_agent.name != 'User':
                raise ValueError(f"user_agent name must be 'User', got '{user_agent.name}' for termination condition to work")
            return user_agent
        else:
            return ConversableAgent(name='User', system_message=get_user_agent_default_system_message(), description=get_user_agent_default_description(), human_input_mode='NEVER', code_execution_config=False, llm_config=create_llm_config(default_llm_config))

    def _setup_group_manager_args(self, pattern_config: Dict[str, Any], default_llm_config: Any) -> Dict[str, Any]:
        """
        Set up group_manager_args for pattern.

        Args:
            pattern_config: Pattern configuration from YAML
            default_llm_config: Default llm_config to use if not specified

        Returns:
            Dict with llm_config and termination condition
        """
        group_manager_args = pattern_config.get('group_manager_args', {})
        if 'llm_config' not in group_manager_args:
            group_manager_args['llm_config'] = create_llm_config(default_llm_config)
        else:
            group_manager_args['llm_config'] = create_llm_config(group_manager_args['llm_config'])
        group_manager_args['is_termination_msg'] = lambda msg: msg.get('name') == self.user_agent.name and 'TERMINATE' in msg.get('content', '')
        return group_manager_args

    def _create_pattern(self, pattern_type: str, pattern_config: Dict[str, Any], agents: List[ConversableAgent], agent_name_map: Dict[str, ConversableAgent], group_manager_args: Dict[str, Any], *args) -> Any:
        """
        Create AG2 pattern based on type.

        Args:
            pattern_type: Type of pattern (currently only "auto")
            pattern_config: Pattern configuration from YAML
            agents: List of expert agents
            agent_name_map: Mapping from agent names to agent objects
            group_manager_args: Group manager configuration

        Returns:
            Pattern instance (AutoPattern)
        """
        initial_agent_name = pattern_config.get('initial_agent')
        if not initial_agent_name:
            raise ValueError('initial_agent must be specified in pattern configuration')
        if initial_agent_name not in agent_name_map:
            raise ValueError(f"initial_agent '{initial_agent_name}' not found in agents list")
        initial_agent = agent_name_map[initial_agent_name]
        extra_args = {k: v for k, v in pattern_config.items() if k not in ['type', 'initial_agent', 'group_manager_args']}
        if pattern_type == 'auto':
            return AutoPattern(initial_agent=initial_agent, agents=agents, user_agent=self.user_agent, group_manager_args=group_manager_args, **extra_args)
        else:
            raise NotImplementedError(f"Pattern type '{pattern_type}' not supported")

    async def _execute_single_agent(self, messages: List[Dict[str, Any]], agent: ConversableAgent) -> AsyncGenerator[StreamChunk, None]:
        """
        Execute single AG2 agent.

        Args:
            messages: Conversation messages
            agent_id: Agent ID for logging

        Returns:
            Tuple of (content, tool_calls)
        """
        result = await agent.a_generate_reply(messages)
        content = result.get('content', '') if isinstance(result, dict) else str(result)
        tool_calls = result.get('tool_calls') if isinstance(result, dict) else None
        log_backend_activity('ag2', 'Received response data from AG2', {'has_content': bool(content), 'content_length': len(content) if content else 0, 'has_tool_calls': bool(tool_calls), 'tool_count': len(tool_calls) if tool_calls else 0}, agent_id=self.agent_id)
        async for chunk in self.simulate_streaming(content, tool_calls):
            yield chunk

    async def _execute_group_chat(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """
        Execute AG2 group chat with pattern.

        Args:
            messages: Conversation messages
            agent_id: Agent ID for logging

        Returns:
            Tuple of (content, tool_calls)
        """
        for message in messages:
            message['name'] = 'User'
        response = await a_run_group_chat(pattern=self.pattern, messages=messages, max_rounds=self.group_max_rounds)
        last_group_chat_event_msgs = []

        def process_and_log_event(*args, **kwargs) -> None:
            """Process and log AG2 event, returning string representation."""
            line = ' '.join((str(arg) for arg in args))
            last_group_chat_event_msgs.append(line)
        async for event in response.events:
            last_group_chat_event_msgs.clear()
            event.print(f=process_and_log_event)
            formatted_message = '\n'.join(last_group_chat_event_msgs)
            log_backend_activity('ag2', 'Received response from AG2', {'message': formatted_message}, agent_id=self.agent_id)
            yield formatted_message

    async def _execute_group_chat_with_user_agent(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[StreamChunk, None]:
        messages_to_execute = []
        if self.coordination_stage == CoordinationStage.INITIAL_ANSWER:
            self.user_agent.update_system_message(get_user_agent_default_system_message())
            messages[0] = get_group_initial_message()
            async for event_msg in self._execute_group_chat(messages):
                yield StreamChunk(type='content', content=event_msg)
            results = list(self.user_agent._oai_messages.values())[0]
            self.user_agent.update_system_message(get_user_agent_tool_call_message())
            register_tools_for_agent(self.workflow_tools, self.user_agent)
            messages_to_execute = postprocess_group_chat_results(results)
        elif self.coordination_stage == CoordinationStage.ENFORCEMENT:
            register_tools_for_agent(self.workflow_tools, self.user_agent)
            messages_to_execute = messages
        elif self.coordination_stage == CoordinationStage.PRESENTATION:
            self.user_agent.update_system_message(messages[0]['content'])
            messages_to_execute = [messages[1]]
        async for chunk in self._execute_single_agent(messages=messages_to_execute, agent=self.user_agent):
            yield chunk

    async def execute_streaming(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from AG2 agent(s).

        Since AG2 doesn't support streaming, we simulate it.
        """
        try:
            self._register_tools(tools)
            agent_id = kwargs.get('agent_id')
            if agent_id:
                self.agent_id = agent_id
            log_backend_activity('ag2', 'Starting execute_streaming', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
            if self.is_group_chat:
                async for chunk in self._execute_group_chat_with_user_agent(messages):
                    yield chunk
            else:
                async for chunk in self._execute_single_agent(messages, self.agent):
                    yield chunk
            unregister_tools_for_agent(self.workflow_tools, self.user_agent)
        except Exception as e:
            logger.error(f'[AG2Adapter] Error in execute_streaming: {e}', exc_info=True)
            agent_id = kwargs.get('agent_id', 'ag2_agent')
            log_backend_activity('ag2', 'Error during execution', {'error': str(e), 'error_type': type(e).__name__}, agent_id=agent_id)
            yield StreamChunk(type='error', error=f'AG2 execution error: {str(e)}')

    def _register_tools(self, tools: List[Dict[str, Any]]) -> None:
        """
        Register tools with the agent(s).

        For single agent: Register all tools to the agent.

        For group chat:
        - Workflow tools (new_answer, vote) → register ONLY to user_agent
        - Other tools (MCP, etc.) → register to ALL expert agents (not user_agent)

        MassGen and AG2 both use OpenAI function format for tools.
        """
        if not tools:
            return
        if self.is_group_chat:
            self._register_tools_for_group_chat(tools)
        else:
            register_tools_for_agent(tools, self.agent)

    def _register_tools_for_group_chat(self, tools: List[Dict[str, Any]]) -> None:
        """Register tools to group chat agents based on type."""
        workflow_tools, other_tools = self._separate_workflow_and_other_tools(tools)
        for agent in self.agents:
            for tool in other_tools:
                register_tools_for_agent([tool], agent)
            if other_tools:
                logger.info(f"[AG2Adapter] Registered {len(other_tools)} non-workflow tools to agent '{agent.name}'")
        self.workflow_tools = workflow_tools

    def _separate_workflow_and_other_tools(self, tools: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Separate workflow tools from other tools.

        Args:
            tools: List of all tools

        Returns:
            Tuple of (workflow_tools, other_tools)
        """
        workflow_tools = []
        other_tools = []
        for tool in tools:
            tool_name = self._get_tool_name(tool)
            if tool_name in ['new_answer', 'vote']:
                workflow_tools.append(tool)
            else:
                other_tools.append(tool)
        if 'new_answer' in workflow_tools and 'vote' not in workflow_tools:
            raise ValueError("Both 'new_answer' and 'vote' workflow tools must be provided.")
        return (workflow_tools, other_tools)

def _setup_group_chat(self):
    """Set up AG2 GroupChat with multiple agents and pattern."""
    if 'pattern' not in self.group_config:
        raise ValueError("group_config must include 'pattern' configuration")
    self.default_llm_config = self.group_config.get('llm_config')
    if not self.default_llm_config:
        raise ValueError("group_config must include 'llm_config' as default for all agents")
    agents = []
    agent_name_map = {}
    for agent_cfg in self.group_config.get('agents', []):
        agent = setup_agent_from_config(agent_cfg, default_llm_config=self.default_llm_config)
        agents.append(agent)
        agent_name_map[agent.name] = agent
    if not agents:
        raise ValueError('No valid agents configured for group chat')
    pattern_config = self.group_config['pattern']
    pattern_type = pattern_config.get('type')
    if not pattern_type:
        raise ValueError("pattern configuration must include 'type' field")
    if pattern_type not in SUPPORTED_GROUPCHAT_PATTERNS:
        raise NotImplementedError(f"Pattern type '{pattern_type}' not supported. Supported types: {', '.join(SUPPORTED_GROUPCHAT_PATTERNS)}")
    self.user_agent = self._setup_user_agent(user_agent_config=self.group_config.get('user_agent'), default_llm_config=self.default_llm_config)
    group_manager_args = self._setup_group_manager_args(pattern_config, self.default_llm_config)
    self.pattern = self._create_pattern(pattern_type, pattern_config, agents, agent_name_map, group_manager_args)
    self.agents = agents
    self.group_max_rounds = self.group_config.get('max_rounds', DEFAULT_MAX_ROUNDS)
    self.is_group_chat = True
    logger.info(f'[AG2Adapter] GroupChat setup complete with {len(agents)} agents and {pattern_type} pattern')

def _setup_user_agent(self, user_agent_config: Any, default_llm_config: Any) -> ConversableAgent:
    """
        Set up user_agent for group chat.

        User agent makes final decisions and calls workflow tools.
        Its name MUST be "User" for termination condition to work.

        Args:
            user_agent_config: Optional user agent configuration from YAML
            default_llm_config: Default llm_config to use if not specified

        Returns:
            ConversableAgent with name "User"
        """
    if user_agent_config:
        user_agent = setup_agent_from_config(user_agent_config, default_llm_config=default_llm_config)
        if user_agent.name != 'User':
            raise ValueError(f"user_agent name must be 'User', got '{user_agent.name}' for termination condition to work")
        return user_agent
    else:
        return ConversableAgent(name='User', system_message=get_user_agent_default_system_message(), description=get_user_agent_default_description(), human_input_mode='NEVER', code_execution_config=False, llm_config=create_llm_config(default_llm_config))

def _setup_group_manager_args(self, pattern_config: Dict[str, Any], default_llm_config: Any) -> Dict[str, Any]:
    """
        Set up group_manager_args for pattern.

        Args:
            pattern_config: Pattern configuration from YAML
            default_llm_config: Default llm_config to use if not specified

        Returns:
            Dict with llm_config and termination condition
        """
    group_manager_args = pattern_config.get('group_manager_args', {})
    if 'llm_config' not in group_manager_args:
        group_manager_args['llm_config'] = create_llm_config(default_llm_config)
    else:
        group_manager_args['llm_config'] = create_llm_config(group_manager_args['llm_config'])
    group_manager_args['is_termination_msg'] = lambda msg: msg.get('name') == self.user_agent.name and 'TERMINATE' in msg.get('content', '')
    return group_manager_args

def _create_pattern(self, pattern_type: str, pattern_config: Dict[str, Any], agents: List[ConversableAgent], agent_name_map: Dict[str, ConversableAgent], group_manager_args: Dict[str, Any], *args) -> Any:
    """
        Create AG2 pattern based on type.

        Args:
            pattern_type: Type of pattern (currently only "auto")
            pattern_config: Pattern configuration from YAML
            agents: List of expert agents
            agent_name_map: Mapping from agent names to agent objects
            group_manager_args: Group manager configuration

        Returns:
            Pattern instance (AutoPattern)
        """
    initial_agent_name = pattern_config.get('initial_agent')
    if not initial_agent_name:
        raise ValueError('initial_agent must be specified in pattern configuration')
    if initial_agent_name not in agent_name_map:
        raise ValueError(f"initial_agent '{initial_agent_name}' not found in agents list")
    initial_agent = agent_name_map[initial_agent_name]
    extra_args = {k: v for k, v in pattern_config.items() if k not in ['type', 'initial_agent', 'group_manager_args']}
    if pattern_type == 'auto':
        return AutoPattern(initial_agent=initial_agent, agents=agents, user_agent=self.user_agent, group_manager_args=group_manager_args, **extra_args)
    else:
        raise NotImplementedError(f"Pattern type '{pattern_type}' not supported")

def _separate_workflow_and_other_tools(self, tools: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
        Separate workflow tools from other tools.

        Args:
            tools: List of all tools

        Returns:
            Tuple of (workflow_tools, other_tools)
        """
    workflow_tools = []
    other_tools = []
    for tool in tools:
        tool_name = self._get_tool_name(tool)
        if tool_name in ['new_answer', 'vote']:
            workflow_tools.append(tool)
        else:
            other_tools.append(tool)
    if 'new_answer' in workflow_tools and 'vote' not in workflow_tools:
        raise ValueError("Both 'new_answer' and 'vote' workflow tools must be provided.")
    return (workflow_tools, other_tools)

def validate_agent_config(cfg: Dict[str, Any], require_llm_config: bool=True) -> None:
    """
    Validate required fields in agent configuration.

    Args:
        cfg: Agent configuration dict
        require_llm_config: If True, llm_config is required. If False, it's optional.
    """
    if require_llm_config and 'llm_config' not in cfg:
        raise ValueError("Each AG2 agent configuration must include 'llm_config'.")
    if 'name' not in cfg:
        raise ValueError("Each AG2 agent configuration must include 'name'.")

def create_code_executor(executor_config: Dict[str, Any]) -> Any:
    """Create code executor from configuration."""
    executor_type = executor_config.get('type')
    if not executor_type:
        raise ValueError("code_execution_config.executor must include 'type' field")
    executor_params = {k: v for k, v in executor_config.items() if k != 'type'}
    if executor_type == 'LocalCommandLineCodeExecutor':
        from autogen.coding import LocalCommandLineCodeExecutor
        return LocalCommandLineCodeExecutor(**executor_params)
    elif executor_type == 'DockerCommandLineCodeExecutor':
        from autogen.coding import DockerCommandLineCodeExecutor
        return DockerCommandLineCodeExecutor(**executor_params)
    elif executor_type == 'YepCodeCodeExecutor':
        from autogen.coding import YepCodeCodeExecutor
        return YepCodeCodeExecutor(**executor_params)
    elif executor_type == 'JupyterCodeExecutor':
        from autogen.coding.jupyter import JupyterCodeExecutor
        return JupyterCodeExecutor(**executor_params)
    else:
        raise ValueError(f'Unsupported code executor type: {executor_type}. Supported types: LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor, YepCodeCodeExecutor, JupyterCodeExecutor')

def setup_agent_from_config(config: Dict[str, Any], default_llm_config: Any=None) -> ConversableAgent:
    """
    Set up a ConversableAgent from configuration.

    Args:
        config: Agent configuration dict
        default_llm_config: Default llm_config to use if agent doesn't provide one

    Returns:
        ConversableAgent or AssistantAgent instance
    """
    cfg = config.copy()
    has_llm_config = 'llm_config' in cfg
    validate_agent_config(cfg, require_llm_config=not default_llm_config)
    agent_type = cfg.pop('type', 'conversable')
    if has_llm_config:
        llm_config = create_llm_config(cfg.pop('llm_config'))
    elif default_llm_config:
        llm_config = create_llm_config(default_llm_config)
    else:
        raise ValueError('No llm_config provided for agent and no default_llm_config available')
    code_executor = None
    if 'code_execution_config' in cfg:
        code_exec_config = cfg.pop('code_execution_config')
        if 'executor' in code_exec_config:
            code_executor = create_code_executor(code_exec_config['executor'])
    agent_kwargs = build_agent_kwargs(cfg, llm_config, code_executor)
    if agent_type == 'assistant':
        return AssistantAgent(**agent_kwargs)
    elif agent_type == 'conversable':
        return ConversableAgent(**agent_kwargs)
    else:
        raise ValueError(f"Unsupported AG2 agent type: {agent_type}. Use 'assistant' or 'conversable' for ag2 agents.")

def test_create_llm_config_from_dict():
    """Test creating LLMConfig from dictionary."""
    config_dict = {'api_type': 'openai', 'model': 'gpt-4o', 'temperature': 0.7}
    llm_config = create_llm_config(config_dict)
    assert llm_config is not None
    assert hasattr(llm_config, 'config_list')

def test_create_llm_config_from_list():
    """Test creating LLMConfig from list of configs."""
    config_list = [{'api_type': 'openai', 'model': 'gpt-4o'}, {'api_type': 'google', 'model': 'gemini-pro'}]
    llm_config = create_llm_config(config_list)
    assert llm_config is not None
    assert hasattr(llm_config, 'config_list')

