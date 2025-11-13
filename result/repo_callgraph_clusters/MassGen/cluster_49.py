# Cluster 49

def unregister_tools_for_agent(tools: List[Dict[str, Any]], agent: ConversableAgent) -> None:
    """Unregister all tools from single agent."""
    for tool in tools:
        agent.update_tool_signature(tool_sig=tool, is_remove=True, silent_override=True)

def register_tools_for_agent(tools: List[Dict[str, Any]], agent: ConversableAgent) -> None:
    """Register all tools to single agent."""
    for tool in tools:
        agent.update_tool_signature(tool_sig=tool, is_remove=False, silent_override=True)

