# Cluster 45

class MCPErrorHandler:
    """Standardized MCP error handling utilities."""

    @staticmethod
    def get_error_details(error: Exception, context: str | None=None, *, log: bool=False) -> tuple[str, str, str]:
        """Return standardized MCP error info and optionally log.

        Returns:
            Tuple of (log_type, user_message, error_category)
        """
        if isinstance(error, MCPConnectionError):
            details = ('connection error', 'MCP connection failed', 'connection')
        elif isinstance(error, MCPTimeoutError):
            details = ('timeout error', 'MCP session timeout', 'timeout')
        elif isinstance(error, MCPServerError):
            details = ('server error', 'MCP server error', 'server')
        elif isinstance(error, MCPValidationError):
            details = ('validation error', 'MCP validation failed', 'validation')
        elif isinstance(error, MCPAuthenticationError):
            details = ('authentication error', 'MCP authentication failed', 'auth')
        elif isinstance(error, MCPResourceError):
            details = ('resource error', 'MCP resource unavailable', 'resource')
        elif isinstance(error, MCPError):
            details = ('MCP error', 'MCP error', 'general')
        else:
            details = ('unexpected error', 'MCP connection failed', 'unknown')
        if log:
            log_type, user_message, error_category = details
            logger.warning(f'MCP {log_type}: {error}', extra={'context': context or 'none'})
        return details

    @staticmethod
    def is_transient_error(error: Exception) -> bool:
        """Determine if an error is transient and should be retried."""
        if isinstance(error, (MCPConnectionError, MCPTimeoutError)):
            return True
        elif isinstance(error, MCPServerError):
            error_str = str(error).lower()
            return any((keyword in error_str for keyword in ['timeout', 'connection', 'network', 'temporary', 'unavailable', '503', '502', '504', '500', 'retry']))
        elif isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return True
        elif isinstance(error, MCPResourceError):
            return True
        return False

    @staticmethod
    def log_error(error: Exception, context: str, level: str='auto', backend_name: str | None=None, agent_id: str | None=None) -> None:
        """Log MCP error with appropriate level and context."""
        log_type, user_message, error_category = MCPErrorHandler.get_error_details(error)
        if level == 'auto':
            level = 'warning' if error_category in ['connection', 'timeout', 'resource'] else 'error'
        log_message = f'MCP {log_type} during {context}: {error}'
        log_mcp_activity(backend_name, f'error ({level})', {'message': log_message}, agent_id=agent_id)

    @staticmethod
    def get_retry_delay(attempt: int, base_delay: float=DEFAULT_RETRY_BASE_DELAY) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        backoff_delay = base_delay * 2 ** attempt
        jitter = random.uniform(DEFAULT_RETRY_JITTER_MIN, DEFAULT_RETRY_JITTER_MAX) * backoff_delay
        return backoff_delay + jitter

    @staticmethod
    def is_auth_or_resource_error(error: Exception) -> bool:
        """Check if error is authentication or resource related (non-retryable)."""
        return isinstance(error, (MCPAuthenticationError, MCPResourceError))

@staticmethod
def get_retry_delay(attempt: int, base_delay: float=DEFAULT_RETRY_BASE_DELAY) -> float:
    """Calculate retry delay with exponential backoff and jitter."""
    backoff_delay = base_delay * 2 ** attempt
    jitter = random.uniform(DEFAULT_RETRY_JITTER_MIN, DEFAULT_RETRY_JITTER_MAX) * backoff_delay
    return backoff_delay + jitter

