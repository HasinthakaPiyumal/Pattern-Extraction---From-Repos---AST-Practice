# Cluster 42

def get_session_manager(session_id: str, headless: bool=False, timeout: int=30) -> Optional[BrowserSessionManager]:
    """
    Get or create a browser session for the given session ID.
    """
    return _session_state.get_or_create_session(session_id, headless, timeout)

