# Cluster 21

def create_analytical_config(model: str='gpt-4o-mini', backend: str='openai') -> AgentConfig:
    """Create configuration for analytical tasks (no special tools)."""
    return AgentConfig.for_analytical_task(model, backend)

