# Cluster 6

class AgentGenerator(Agent):
    """
    An agent responsible for generating agents for a task. 
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else AGENT_GENERATOR['name']
        description = kwargs.pop('description') if 'description' in kwargs else AGENT_GENERATOR['description']
        system_prompt = kwargs.pop('system_prompt') if 'system_prompt' in kwargs else AGENT_GENERATOR['system_prompt']
        actions = kwargs.pop('actions') if 'actions' in kwargs else [AgentGeneration(tools=kwargs.pop('tools', []))]
        super().__init__(name=name, description=description, system_prompt=system_prompt, actions=actions, **kwargs)

    @property
    def agent_generation_action_name(self):
        return self.get_action_name(action_cls=AgentGeneration)

@property
def agent_generation_action_name(self):
    return self.get_action_name(action_cls=AgentGeneration)

class TaskPlanner(Agent):
    """An agent responsible for planning and decomposing high-level tasks into smaller sub-tasks.
    
    The TaskPlanner agent analyzes complex goals and breaks them down into a structured
    sequence of smaller, more manageable tasks. It serves as a critical component in the
    workflow by creating execution plans that other specialized agents can follow.
    
    Attributes:
        name (str): Name of the task planner agent, defaults to the value in TASK_PLANNER
        description (str): Description of the agent's purpose and capabilities, defaults to the value in TASK_PLANNER
        system_prompt (str): System prompt guiding the agent's behavior, defaults to the value in TASK_PLANNER
        actions (List[Action]): List of actions the agent can perform, defaults to [TaskPlanning()]
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else TASK_PLANNER['name']
        description = kwargs.pop('description') if 'description' in kwargs else TASK_PLANNER['description']
        system_prompt = kwargs.pop('system_prompt') if 'system_prompt' in kwargs else TASK_PLANNER['system_prompt']
        actions = kwargs.pop('actions') if 'actions' in kwargs else [TaskPlanning()]
        super().__init__(name=name, description=description, system_prompt=system_prompt, actions=actions, **kwargs)

    @property
    def task_planning_action_name(self):
        """Get the name of the TaskPlanning action associated with this agent.
        
        Returns:
            The name of the TaskPlanning action in this agent's action registry
        """
        return self.get_action_name(action_cls=TaskPlanning)

@property
def task_planning_action_name(self):
    """Get the name of the TaskPlanning action associated with this agent.
        
        Returns:
            The name of the TaskPlanning action in this agent's action registry
        """
    return self.get_action_name(action_cls=TaskPlanning)

