# Cluster 17

class InferenceAPIParamsHandler(ChatCompletionsAPIParamsHandler):
    """API params handler for InferenceBackend that excludes backend-specific parameters."""

    def get_excluded_params(self) -> Set[str]:
        """Get parameters to exclude from Chat Completions API calls, including backend-specific ones."""
        return super().get_excluded_params().union({'chat_template_kwargs', 'top_k', 'repetition_penalty', 'separate_reasoning'})

def get_excluded_params(self) -> Set[str]:
    """Get parameters to exclude from Chat Completions API calls, including backend-specific ones."""
    return super().get_excluded_params().union({'chat_template_kwargs', 'top_k', 'repetition_penalty', 'separate_reasoning'})

class ChatCompletionsAPIParamsHandler(APIParamsHandlerBase):
    """Handler for Chat Completions API parameters."""

    def get_excluded_params(self) -> Set[str]:
        """Get parameters to exclude from Chat Completions API calls."""
        return self.get_base_excluded_params().union({'base_url', 'enable_web_search', 'enable_code_interpreter', 'allowed_tools', 'exclude_tools'})

    def get_provider_tools(self, all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get provider tools for Chat Completions format."""
        provider_tools = []
        if all_params.get('enable_web_search', False):
            provider_tools.append({'type': 'function', 'function': {'name': 'web_search', 'description': 'Search the web for current or factual information', 'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', 'description': 'The search query to send to the web'}}, 'required': ['query']}}})
        if all_params.get('enable_code_interpreter', False):
            provider_tools.append({'type': 'code_interpreter', 'container': {'type': 'auto'}})
        return provider_tools

    def build_base_api_params(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build base API parameters for Chat Completions requests."""
        sanitized_messages = self._sanitize_messages_for_api(messages)
        converted_messages = self.formatter.format_messages(sanitized_messages)
        api_params = {'messages': converted_messages, 'stream': True}
        for key, value in all_params.items():
            if key not in self.get_excluded_params() and value is not None:
                api_params[key] = value
        return api_params

    async def build_api_params(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build Chat Completions API parameters."""
        if hasattr(self.backend, '_sanitize_messages_for_api'):
            messages = self._sanitize_messages_for_api(messages)
        converted_messages = self.formatter.format_messages(messages)
        api_params = {'messages': converted_messages, 'stream': True}
        excluded = self.get_excluded_params()
        for key, value in all_params.items():
            if key not in excluded and value is not None:
                api_params[key] = value
        combined_tools = []
        provider_tools = self.get_provider_tools(all_params)
        if provider_tools:
            combined_tools.extend(provider_tools)
        if tools:
            converted_tools = self.formatter.format_tools(tools)
            combined_tools.extend(converted_tools)
        mcp_tools = self.get_mcp_tools()
        if mcp_tools:
            combined_tools.extend(mcp_tools)
        if combined_tools:
            api_params['tools'] = combined_tools
        return api_params

    def _sanitize_messages_for_api(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure assistant tool_calls are valid per OpenAI Chat Completions rules:
        - For any assistant message with tool_calls, each tool_call.id must have a following
          tool message with matching tool_call_id in the subsequent history.
        - Remove any tool_calls lacking matching tool results; drop the whole assistant message
          if no valid tool_calls remain and it has no useful content.
        This prevents 400 wrong_api_format errors.
        """
        try:
            sanitized: List[Dict[str, Any]] = []
            len(messages)
            for i, msg in enumerate(messages):
                if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                    tool_calls = msg.get('tool_calls') or []
                    valid_tool_calls = []
                    for tc in tool_calls:
                        tc_id = tc.get('id')
                        if not tc_id:
                            continue
                        has_match = any((m.get('role') == 'tool' and m.get('tool_call_id') == tc_id for m in messages[i + 1:]))
                        if has_match:
                            fn = dict(tc.get('function', {}))
                            fn['arguments'] = self.formatter._serialize_tool_arguments(fn.get('arguments'))
                            valid_tc = dict(tc)
                            valid_tc['function'] = fn
                            valid_tool_calls.append(valid_tc)
                    if valid_tool_calls:
                        new_msg = dict(msg)
                        new_msg['tool_calls'] = valid_tool_calls
                        sanitized.append(new_msg)
                    elif msg.get('content'):
                        new_msg = {k: v for k, v in msg.items() if k != 'tool_calls'}
                        sanitized.append(new_msg)
                    else:
                        continue
                else:
                    sanitized.append(msg)
            return sanitized
        except Exception:
            return messages

def get_excluded_params(self) -> Set[str]:
    """Get parameters to exclude from Chat Completions API calls."""
    return self.get_base_excluded_params().union({'base_url', 'enable_web_search', 'enable_code_interpreter', 'allowed_tools', 'exclude_tools'})

def build_base_api_params(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
    """Build base API parameters for Chat Completions requests."""
    sanitized_messages = self._sanitize_messages_for_api(messages)
    converted_messages = self.formatter.format_messages(sanitized_messages)
    api_params = {'messages': converted_messages, 'stream': True}
    for key, value in all_params.items():
        if key not in self.get_excluded_params() and value is not None:
            api_params[key] = value
    return api_params

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

def build_base_api_params(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
    """Build base API parameters common to most backends."""
    api_params = {'stream': True}
    excluded = self.get_excluded_params()
    for key, value in all_params.items():
        if key not in excluded and value is not None:
            api_params[key] = value
    return api_params

class ClaudeAPIParamsHandler(APIParamsHandlerBase):
    """Handler for Claude API parameters."""

    def get_excluded_params(self) -> Set[str]:
        """Get parameters to exclude from Claude API calls."""
        return self.get_base_excluded_params().union({'enable_web_search', 'enable_code_execution', 'allowed_tools', 'exclude_tools', '_has_files_api_files'})

    def get_provider_tools(self, all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get provider tools for Claude format (server-side tools)."""
        provider_tools = []
        if all_params.get('enable_web_search', False):
            provider_tools.append({'type': 'web_search_20250305', 'name': 'web_search'})
        if all_params.get('enable_code_execution', False):
            provider_tools.append({'type': 'code_execution_20250522', 'name': 'code_execution'})
        return provider_tools

    async def build_api_params(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build Claude API parameters."""
        converted_messages, system_message = self.formatter.format_messages_and_system(messages)
        api_params: Dict[str, Any] = {'messages': converted_messages, 'stream': True}
        excluded = self.get_excluded_params()
        for key, value in all_params.items():
            if key not in excluded and value is not None:
                api_params[key] = value
        if 'max_tokens' not in api_params:
            api_params['max_tokens'] = 4096
        betas_list = []
        if all_params.get('enable_code_execution'):
            betas_list.append('code-execution-2025-05-22')
        if all_params.get('_has_files_api_files'):
            betas_list.append('files-api-2025-04-14')
        if betas_list:
            api_params['betas'] = betas_list
        all_params.pop('_has_files_api_files', None)
        if system_message:
            api_params['system'] = system_message
        combined_tools = []
        provider_tools = self.get_provider_tools(all_params)
        if provider_tools:
            combined_tools.extend(provider_tools)
        if tools:
            converted_tools = self.formatter.format_tools(tools)
            combined_tools.extend(converted_tools)
        mcp_tools = self.get_mcp_tools()
        if mcp_tools:
            combined_tools.extend(mcp_tools)
        if combined_tools:
            api_params['tools'] = combined_tools
        return api_params

def get_excluded_params(self) -> Set[str]:
    """Get parameters to exclude from Claude API calls."""
    return self.get_base_excluded_params().union({'enable_web_search', 'enable_code_execution', 'allowed_tools', 'exclude_tools', '_has_files_api_files'})

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

def get_excluded_params(self) -> Set[str]:
    """Get parameters to exclude from Response API calls."""
    return self.get_base_excluded_params().union({'enable_web_search', 'enable_code_interpreter', 'allowed_tools', 'exclude_tools', '_has_file_search_files'})

