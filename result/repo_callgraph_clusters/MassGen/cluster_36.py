# Cluster 36

def create_streaming_display(display_enabled: bool=True, stream_callback: Optional[Callable]=None, max_lines: int=10, save_logs: bool=True, answers_dir: Optional[str]=None) -> StreamingOrchestrator:
    """Create a streaming orchestrator with display capabilities."""
    return StreamingOrchestrator(display_enabled, stream_callback, max_lines, save_logs, answers_dir)

