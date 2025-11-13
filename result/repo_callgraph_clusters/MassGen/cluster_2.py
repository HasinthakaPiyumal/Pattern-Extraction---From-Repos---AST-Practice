# Cluster 2

def create_rich_display(agent_ids: List[str], **kwargs) -> RichTerminalDisplay:
    """Create a RichTerminalDisplay instance.

    Args:
        agent_ids: List of agent IDs to display
        **kwargs: Configuration options for RichTerminalDisplay

    Returns:
        RichTerminalDisplay instance

    Raises:
        ImportError: If Rich library is not available
    """
    return RichTerminalDisplay(agent_ids, **kwargs)

