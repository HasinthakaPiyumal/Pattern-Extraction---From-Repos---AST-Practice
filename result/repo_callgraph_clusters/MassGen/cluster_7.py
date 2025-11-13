# Cluster 7

class TokenCostCalculator:
    """Unified token estimation and cost calculation."""
    PROVIDER_PRICING: Dict[str, Dict[str, ModelPricing]] = {'OpenAI': {'gpt-4o': ModelPricing(0.0025, 0.01, 128000, 16384), 'gpt-4o-mini': ModelPricing(0.00015, 0.0006, 128000, 16384), 'gpt-4-turbo': ModelPricing(0.01, 0.03, 128000, 4096), 'gpt-4': ModelPricing(0.03, 0.06, 8192, 8192), 'gpt-3.5-turbo': ModelPricing(0.0005, 0.0015, 16385, 4096), 'o1-preview': ModelPricing(0.015, 0.06, 128000, 32768), 'o1-mini': ModelPricing(0.003, 0.012, 128000, 65536), 'o3-mini': ModelPricing(0.0011, 0.0044, 200000, 100000)}, 'Anthropic': {'claude-3-5-sonnet': ModelPricing(0.003, 0.015, 200000, 8192), 'claude-3-5-haiku': ModelPricing(0.001, 0.005, 200000, 8192), 'claude-3-opus': ModelPricing(0.015, 0.075, 200000, 4096), 'claude-3-sonnet': ModelPricing(0.003, 0.015, 200000, 4096), 'claude-3-haiku': ModelPricing(0.00025, 0.00125, 200000, 4096)}, 'Google': {'gemini-2.0-flash-exp': ModelPricing(0.0, 0.0, 1048576, 8192), 'gemini-2.0-flash-thinking-exp': ModelPricing(0.0, 0.0, 32767, 8192), 'gemini-1.5-pro': ModelPricing(0.00125, 0.005, 2097152, 8192), 'gemini-1.5-flash': ModelPricing(7.5e-05, 0.0003, 1048576, 8192), 'gemini-1.5-flash-8b': ModelPricing(3.75e-05, 0.00015, 1048576, 8192), 'gemini-1.0-pro': ModelPricing(0.00025, 0.00125, 32760, 8192)}, 'Cerebras': {'llama3.3-70b': ModelPricing(0.00035, 0.00035, 128000, 8192), 'llama3.1-70b': ModelPricing(0.00035, 0.00035, 128000, 8192), 'llama3.1-8b': ModelPricing(1e-05, 1e-05, 128000, 8192)}, 'Together': {'meta-llama/Llama-3.3-70B-Instruct-Turbo': ModelPricing(0.00059, 0.00079, 128000, 32768), 'meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo': ModelPricing(0.00059, 0.00079, 128000, 32768), 'meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo': ModelPricing(0.00088, 0.00088, 130000, 4096), 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo': ModelPricing(0.00018, 0.00018, 131072, 65536), 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo': ModelPricing(6e-05, 6e-05, 131072, 16384), 'Qwen/QwQ-32B-Preview': ModelPricing(0.00015, 0.00015, 32768, 32768), 'Qwen/Qwen2.5-72B-Instruct-Turbo': ModelPricing(0.00012, 0.00012, 32768, 8192), 'mistralai/Mixtral-8x22B-Instruct-v0.1': ModelPricing(0.0009, 0.0009, 65536, 65536), 'deepseek-ai/deepseek-r1-distill-llama-70b': ModelPricing(0.00015, 0.00015, 65536, 8192)}, 'Fireworks': {'llama-3.3-70b': ModelPricing(0.0002, 0.0002, 128000, 16384), 'llama-3.1-405b': ModelPricing(0.0009, 0.0009, 131072, 16384), 'llama-3.1-70b': ModelPricing(0.0002, 0.0002, 131072, 16384), 'llama-3.1-8b': ModelPricing(2e-05, 2e-05, 131072, 16384), 'qwen2.5-72b': ModelPricing(0.0002, 0.0002, 32768, 16384)}, 'Groq': {'llama-3.3-70b-versatile': ModelPricing(0.00059, 0.00079, 128000, 32768), 'llama-3.1-70b-versatile': ModelPricing(0.00059, 0.00079, 131072, 8000), 'llama-3.1-8b-instant': ModelPricing(5e-05, 8e-05, 131072, 8000), 'mixtral-8x7b-32768': ModelPricing(0.00024, 0.00024, 32768, 32768)}, 'xAI': {'grok-2-latest': ModelPricing(0.005, 0.015, 131072, 131072), 'grok-2': ModelPricing(0.005, 0.015, 131072, 131072), 'grok-2-mini': ModelPricing(0.001, 0.003, 131072, 65536)}, 'DeepSeek': {'deepseek-reasoner': ModelPricing(0.00014, 0.0028, 163840, 8192), 'deepseek-chat': ModelPricing(0.00014, 0.00028, 64000, 8192)}}

    def __init__(self):
        """Initialize the calculator with optional tiktoken for accurate estimation."""
        self.tiktoken_encoder = None
        self._try_init_tiktoken()

    def _try_init_tiktoken(self):
        """Try to initialize tiktoken encoder for more accurate token counting."""
        try:
            import tiktoken
            self.tiktoken_encoder = tiktoken.get_encoding('cl100k_base')
            logger.debug('Tiktoken encoder initialized for accurate token counting')
        except ImportError:
            logger.debug('Tiktoken not available, using simple estimation')
        except Exception as e:
            logger.warning(f'Failed to initialize tiktoken: {e}')

    def estimate_tokens(self, text: Union[str, List[Dict[str, Any]]], method: str='auto') -> int:
        """
        Estimate token count for text or messages.

        Args:
            text: Text string or list of message dictionaries
            method: Estimation method ("tiktoken", "simple", "auto")

        Returns:
            Estimated token count
        """
        if isinstance(text, list):
            text = self._messages_to_text(text)
        if method == 'auto':
            if self.tiktoken_encoder:
                return self.estimate_tokens_tiktoken(text)
            else:
                return self.estimate_tokens_simple(text)
        elif method == 'tiktoken':
            return self.estimate_tokens_tiktoken(text)
        else:
            return self.estimate_tokens_simple(text)

    def estimate_tokens_tiktoken(self, text: str) -> int:
        """
        Estimate tokens using tiktoken (OpenAI's tokenizer).
        Most accurate for OpenAI models.

        Args:
            text: Text to estimate

        Returns:
            Token count
        """
        if not self.tiktoken_encoder:
            logger.warning('Tiktoken not available, falling back to simple estimation')
            return self.estimate_tokens_simple(text)
        try:
            tokens = self.tiktoken_encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f'Tiktoken encoding failed: {e}, using simple estimation')
            return self.estimate_tokens_simple(text)

    def estimate_tokens_simple(self, text: str) -> int:
        """
        Simple token estimation based on character/word count.
        Roughly 1 token ≈ 4 characters or 0.75 words.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        char_estimate = len(text) / 4
        words = text.split()
        word_estimate = len(words) / 0.75
        estimate = (char_estimate + word_estimate) / 2
        return int(estimate)

    def _messages_to_text(self, messages: List[Dict[str, Any]]) -> str:
        """Convert message list to text for token estimation."""
        text_parts = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if isinstance(content, str):
                text_parts.append(f'{role}: {content}')
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            text_parts.append(f'{role}: {item.get('text', '')}')
                        elif item.get('type') == 'tool_result':
                            text_parts.append(f'tool_result: {item.get('content', '')}')
                    else:
                        text_parts.append(f'{role}: {str(item)}')
            else:
                text_parts.append(f'{role}: {str(content)}')
            if 'tool_calls' in msg:
                tool_calls = msg['tool_calls']
                if isinstance(tool_calls, list):
                    for call in tool_calls:
                        text_parts.append(f'tool_call: {str(call)}')
        return '\n'.join(text_parts)

    def get_model_pricing(self, provider: str, model: str) -> Optional[ModelPricing]:
        """
        Get pricing information for a specific model.

        Args:
            provider: Provider name (e.g., "OpenAI", "Anthropic")
            model: Model name or identifier

        Returns:
            ModelPricing object or None if not found
        """
        provider = self._normalize_provider(provider)
        provider_models = self.PROVIDER_PRICING.get(provider, {})
        if model in provider_models:
            return provider_models[model]
        for model_key, pricing in provider_models.items():
            if model_key.lower() in model.lower() or model.lower() in model_key.lower():
                return pricing
        model_lower = model.lower()
        if 'gpt-4o' in model_lower and 'mini' in model_lower:
            return provider_models.get('gpt-4o-mini')
        elif 'gpt-4o' in model_lower:
            return provider_models.get('gpt-4o')
        elif 'gpt-4' in model_lower and 'turbo' in model_lower:
            return provider_models.get('gpt-4-turbo')
        elif 'gpt-4' in model_lower:
            return provider_models.get('gpt-4')
        elif 'gpt-3.5' in model_lower:
            return provider_models.get('gpt-3.5-turbo')
        elif 'claude-3-5-sonnet' in model_lower or 'claude-3.5-sonnet' in model_lower:
            return provider_models.get('claude-3-5-sonnet')
        elif 'claude-3-5-haiku' in model_lower or 'claude-3.5-haiku' in model_lower:
            return provider_models.get('claude-3-5-haiku')
        elif 'claude-3-opus' in model_lower:
            return provider_models.get('claude-3-opus')
        elif 'claude-3-sonnet' in model_lower:
            return provider_models.get('claude-3-sonnet')
        elif 'claude-3-haiku' in model_lower:
            return provider_models.get('claude-3-haiku')
        elif 'gemini-2' in model_lower and 'flash' in model_lower:
            return provider_models.get('gemini-2.0-flash-exp')
        elif 'gemini-1.5-pro' in model_lower:
            return provider_models.get('gemini-1.5-pro')
        elif 'gemini-1.5-flash' in model_lower:
            return provider_models.get('gemini-1.5-flash')
        logger.debug(f'No pricing found for {provider}/{model}')
        return None

    def _normalize_provider(self, provider: str) -> str:
        """Normalize provider name for lookup."""
        provider_map = {'openai': 'OpenAI', 'anthropic': 'Anthropic', 'claude': 'Anthropic', 'google': 'Google', 'gemini': 'Google', 'vertex': 'Google', 'cerebras': 'Cerebras', 'cerebras ai': 'Cerebras', 'together': 'Together', 'together ai': 'Together', 'fireworks': 'Fireworks', 'fireworks ai': 'Fireworks', 'groq': 'Groq', 'xai': 'xAI', 'x.ai': 'xAI', 'grok': 'xAI', 'deepseek': 'DeepSeek'}
        provider_lower = provider.lower()
        return provider_map.get(provider_lower, provider)

    def calculate_cost(self, input_tokens: int, output_tokens: int, provider: str, model: str) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: Provider name
            model: Model name

        Returns:
            Estimated cost in USD
        """
        pricing = self.get_model_pricing(provider, model)
        if not pricing:
            logger.debug(f'No pricing for {provider}/{model}, returning 0')
            return 0.0
        input_cost = input_tokens / 1000 * pricing.input_cost_per_1k
        output_cost = output_tokens / 1000 * pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        logger.debug(f'Cost calculation for {provider}/{model}: {input_tokens} input @ ${pricing.input_cost_per_1k}/1k = ${input_cost:.4f}, {output_tokens} output @ ${pricing.output_cost_per_1k}/1k = ${output_cost:.4f}, total = ${total_cost:.4f}')
        return total_cost

    def update_token_usage(self, usage: TokenUsage, messages: List[Dict[str, Any]], response_content: str, provider: str, model: str) -> TokenUsage:
        """
        Update token usage with new conversation turn.

        Args:
            usage: Existing TokenUsage to update
            messages: Input messages
            response_content: Response content
            provider: Provider name
            model: Model name

        Returns:
            Updated TokenUsage object
        """
        input_tokens = self.estimate_tokens(messages)
        output_tokens = self.estimate_tokens(response_content)
        cost = self.calculate_cost(input_tokens, output_tokens, provider, model)
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.estimated_cost += cost
        return usage

    def format_cost(self, cost: float) -> str:
        """Format cost for display."""
        if cost < 0.01:
            return f'${cost:.4f}'
        elif cost < 1.0:
            return f'${cost:.3f}'
        else:
            return f'${cost:.2f}'

    def format_usage_summary(self, usage: TokenUsage) -> str:
        """Format token usage summary for display."""
        return f'Tokens: {usage.input_tokens:,} input, {usage.output_tokens:,} output, Cost: {self.format_cost(usage.estimated_cost)}'

def format_usage_summary(self, usage: TokenUsage) -> str:
    """Format token usage summary for display."""
    return f'Tokens: {usage.input_tokens:,} input, {usage.output_tokens:,} output, Cost: {self.format_cost(usage.estimated_cost)}'

class LLMBackend(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self.token_usage = TokenUsage()
        self._planning_mode_enabled: bool = False
        self.token_calculator = TokenCostCalculator()
        self.filesystem_manager = None
        cwd = kwargs.get('cwd')
        if cwd:
            filesystem_support = self.get_filesystem_support()
            if filesystem_support in (FilesystemSupport.MCP, FilesystemSupport.NATIVE):
                execution_mode = kwargs.get('command_line_execution_mode', 'local')
                if execution_mode not in ['local', 'docker']:
                    raise ValueError(f"Invalid command_line_execution_mode: '{execution_mode}'. Must be 'local' or 'docker'.")
                network_mode = kwargs.get('command_line_docker_network_mode', 'none')
                if network_mode not in ['none', 'bridge', 'host']:
                    raise ValueError(f"Invalid command_line_docker_network_mode: '{network_mode}'. Must be 'none', 'bridge', or 'host'.")
                filesystem_params = {'cwd': cwd, 'agent_temporary_workspace_parent': kwargs.get('agent_temporary_workspace'), 'context_paths': kwargs.get('context_paths', []), 'context_write_access_enabled': kwargs.get('context_write_access_enabled', False), 'enable_image_generation': kwargs.get('enable_image_generation', False), 'enable_mcp_command_line': kwargs.get('enable_mcp_command_line', False), 'command_line_allowed_commands': kwargs.get('command_line_allowed_commands'), 'command_line_blocked_commands': kwargs.get('command_line_blocked_commands'), 'command_line_execution_mode': execution_mode, 'command_line_docker_image': kwargs.get('command_line_docker_image', 'massgen/mcp-runtime:latest'), 'command_line_docker_memory_limit': kwargs.get('command_line_docker_memory_limit'), 'command_line_docker_cpu_limit': kwargs.get('command_line_docker_cpu_limit'), 'command_line_docker_network_mode': network_mode, 'enable_audio_generation': kwargs.get('enable_audio_generation', False)}
                self.filesystem_manager = FilesystemManager(**filesystem_params)
                if filesystem_support == FilesystemSupport.MCP:
                    self.config = self.filesystem_manager.inject_filesystem_mcp(kwargs)
                elif filesystem_support == FilesystemSupport.NATIVE and execution_mode == 'docker' and kwargs.get('enable_mcp_command_line', False):
                    self.config = self.filesystem_manager.inject_command_line_mcp(kwargs)
            elif filesystem_support == FilesystemSupport.NONE:
                raise ValueError(f"Backend {self.get_provider_name()} does not support filesystem operations. Remove 'cwd' from configuration.")
            if self.filesystem_manager:
                self._setup_permission_hooks()
        else:
            self.filesystem_manager = None
        self.formatter = None
        self.api_params_handler = None
        self.coordination_stage = None

    def _setup_permission_hooks(self):
        """Setup permission hooks for function-based backends (default behavior)."""
        self.function_hook_manager = FunctionHookManager()
        permission_hook = PathPermissionManagerHook(self.filesystem_manager.path_permission_manager)
        self.function_hook_manager.register_global_hook(HookType.PRE_CALL, permission_hook)

    @classmethod
    def get_base_excluded_config_params(cls) -> set:
        """
        Get set of config parameters that are universally handled by base class.

        These are parameters handled by the base class or orchestrator, not passed
        directly to backend implementations. Backends should extend this set with
        their own specific exclusions.

        Returns:
            Set of universal parameter names to exclude from backend options
        """
        return {'cwd', 'agent_temporary_workspace', 'context_paths', 'context_write_access_enabled', 'enable_image_generation', 'enable_mcp_command_line', 'command_line_allowed_commands', 'command_line_blocked_commands', 'command_line_execution_mode', 'command_line_docker_image', 'command_line_docker_memory_limit', 'command_line_docker_cpu_limit', 'command_line_docker_network_mode', 'type', 'agent_id', 'session_id', 'mcp_servers'}

    @abstractmethod
    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a response with tool calling support.

        Args:
            messages: Conversation messages
            tools: Available tools schema
            **kwargs: Additional provider-specific parameters including model

        Yields:
            StreamChunk: Standardized response chunks
        """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""

    def estimate_tokens(self, text: Union[str, List[Dict[str, Any]]], method: str='auto') -> int:
        """
        Estimate token count for text or messages.

        Args:
            text: Text string or list of message dictionaries
            method: Estimation method ("tiktoken", "simple", "auto")

        Returns:
            Estimated token count
        """
        return self.token_calculator.estimate_tokens(text, method)

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            Estimated cost in USD
        """
        provider = self.get_provider_name()
        return self.token_calculator.calculate_cost(input_tokens, output_tokens, provider, model)

    def update_token_usage(self, messages: List[Dict[str, Any]], response_content: str, model: str) -> TokenUsage:
        """
        Update token usage tracking.

        Args:
            messages: Input messages
            response_content: Response content
            model: Model name

        Returns:
            Updated TokenUsage object
        """
        provider = self.get_provider_name()
        self.token_usage = self.token_calculator.update_token_usage(self.token_usage, messages, response_content, provider, model)
        return self.token_usage

    def get_token_usage(self) -> TokenUsage:
        """Get current token usage."""
        return self.token_usage

    def reset_token_usage(self):
        """Reset token usage tracking."""
        self.token_usage = TokenUsage()

    def format_cost(self, cost: float=None) -> str:
        """Format cost for display."""
        if cost is None:
            cost = self.token_usage.estimated_cost
        return self.token_calculator.format_cost(cost)

    def format_usage_summary(self, usage: TokenUsage=None) -> str:
        """Format token usage summary for display."""
        if usage is None:
            usage = self.token_usage
        return self.token_calculator.format_usage_summary(usage)

    def get_filesystem_support(self) -> FilesystemSupport:
        """
        Get the type of filesystem support this backend provides.

        Returns:
            FilesystemSupport: The type of filesystem support
            - NONE: No filesystem capabilities
            - NATIVE: Built-in filesystem tools (like Claude Code)
            - MCP: Can use filesystem through MCP servers
        """
        return FilesystemSupport.NONE

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by this provider."""
        return []

    def extract_tool_name(self, tool_call: Dict[str, Any]) -> str:
        """
        Extract tool name from a tool call (handles multiple formats).

        Supports:
        - Chat Completions format: {"function": {"name": "...", ...}}
        - Response API format: {"name": "..."}
        - Claude native format: {"name": "..."}

        Args:
            tool_call: Tool call data structure from any backend

        Returns:
            Tool name string
        """
        if 'function' in tool_call:
            return tool_call.get('function', {}).get('name', 'unknown')
        elif 'name' in tool_call:
            return tool_call.get('name', 'unknown')
        return 'unknown'

    def extract_tool_arguments(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tool arguments from a tool call (handles multiple formats).

        Supports:
        - Chat Completions format: {"function": {"arguments": ...}}
        - Response API format: {"arguments": ...}
        - Claude native format: {"input": ...}

        Args:
            tool_call: Tool call data structure from any backend

        Returns:
            Tool arguments dictionary (parsed from JSON string if needed)
        """
        import json
        if 'function' in tool_call:
            args = tool_call.get('function', {}).get('arguments', {})
        elif 'input' in tool_call:
            args = tool_call.get('input', {})
        elif 'arguments' in tool_call:
            args = tool_call.get('arguments', {})
        else:
            args = {}
        if isinstance(args, str):
            try:
                return json.loads(args) if args.strip() else {}
            except (json.JSONDecodeError, ValueError):
                return {}
        return args if isinstance(args, dict) else {}

    def extract_tool_call_id(self, tool_call: Dict[str, Any]) -> str:
        """
        Extract tool call ID from a tool call (handles multiple formats).

        Supports:
        - Chat Completions format: {"id": "..."}
        - Response API format: {"call_id": "..."}
        - Claude native format: {"id": "..."}

        Args:
            tool_call: Tool call data structure from any backend

        Returns:
            Tool call ID string
        """
        if 'call_id' in tool_call:
            return tool_call.get('call_id', '')
        elif 'id' in tool_call:
            return tool_call.get('id', '')
        else:
            return ''

    def create_tool_result_message(self, tool_call: Dict[str, Any], result_content: str) -> Dict[str, Any]:
        """
        Create a tool result message in this backend's expected format.

        Args:
            tool_call: Original tool call data structure
            result_content: The result content to send back

        Returns:
            Tool result message in backend's expected format
        """
        tool_call_id = self.extract_tool_call_id(tool_call)
        return {'role': 'tool', 'tool_call_id': tool_call_id, 'content': result_content}

    def extract_tool_result_content(self, tool_result_message: Dict[str, Any]) -> str:
        """
        Extract the content/output from a tool result message in this backend's format.

        Args:
            tool_result_message: Tool result message created by this backend

        Returns:
            The content/output string from the message
        """
        return tool_result_message.get('content', '')

    def is_stateful(self) -> bool:
        """
        Check if this backend maintains conversation state across requests.

        Returns:
            True if backend is stateful (maintains context), False if stateless

        Stateless backends require full conversation history with each request.
        Stateful backends maintain context internally and only need new messages.
        """
        return False

    def clear_history(self) -> None:
        """
        Clear conversation history while maintaining session.

        For stateless backends, this is a no-op.
        For stateful backends, this clears conversation history but keeps session.
        """

    def reset_state(self) -> None:
        """
        Reset backend state for stateful backends.

        For stateless backends, this is a no-op.
        For stateful backends, this clears conversation history and session state.
        """
        pass

    def set_planning_mode(self, enabled: bool) -> None:
        """
        Enable or disable planning mode for this backend.

        When planning mode is enabled, MCP tools should be blocked to prevent
        execution during coordination phase.

        Args:
            enabled: True to enable planning mode (block MCP tools), False to disable
        """
        self._planning_mode_enabled = enabled

    def is_planning_mode_enabled(self) -> bool:
        """
        Check if planning mode is currently enabled.

        Returns:
            True if planning mode is enabled (MCP tools should be blocked)
        """
        return self._planning_mode_enabled

    async def _cleanup_client(self, client: Any) -> None:
        """Clean up OpenAI client resources."""
        try:
            if client is not None and hasattr(client, 'aclose'):
                await client.aclose()
        except Exception:
            pass

    def set_stage(self, stage: CoordinationStage) -> None:
        """
        Set the current coordination stage for the backend.

        Args:
            stage: CoordinationStage enum value
        """
        self.coordination_stage = stage

def format_cost(self, cost: float=None) -> str:
    """Format cost for display."""
    if cost is None:
        cost = self.token_usage.estimated_cost
    return self.token_calculator.format_cost(cost)

