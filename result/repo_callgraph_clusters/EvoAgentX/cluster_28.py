# Cluster 28

class SequentialWorkFlowGraph(WorkFlowGraph):
    """
    A linear workflow graph with a single path from start to end.

    Args:
        goal (str): The goal of the workflow.
        tasks (List[dict]): A list of tasks with their descriptions and inputs. Each task should have the following format:
            {
                "name": str,
                "description": str,
                "inputs": [{"name": str, "type": str, "required": bool, "description": str}, ...],
                "outputs": [{"name": str, "type": str, "required": bool, "description": str}, ...],
                "prompt": str, 
                "prompt_template": PromptTemplate, 
                "system_prompt" (optional): str, default is DEFAULT_SYSTEM_PROMPT,
                "output_parser" (optional): Type[ActionOutput],
                "parse_mode" (optional): str, default is "str" 
                "parse_func" (optional): Callable,
                "parse_title" (optional): str ,
                "tool_names" (optional): List[str] 
            }
    """

    def __init__(self, goal: str, tasks: List[dict], **kwargs):
        nodes = self._infer_nodes_from_tasks(tasks=tasks)
        edges = self._infer_edges_from_nodes(nodes=nodes)
        super().__init__(goal=goal, nodes=nodes, edges=edges, **kwargs)

    def _infer_nodes_from_tasks(self, tasks: List[dict]) -> List[WorkFlowNode]:
        nodes = [self._infer_node_from_task(task=task) for task in tasks]
        return nodes

    def _infer_node_from_task(self, task: dict) -> WorkFlowNode:
        node_name = task.get('name', None)
        if not node_name:
            raise ValueError('The `name` for the following task is required: {}'.format(task))
        node_description = task.get('description', None)
        if not node_description:
            raise ValueError('The `description` for the following task is required: {}'.format(task))
        agent_prompt = task.get('prompt', None)
        agent_prompt_template = task.get('prompt_template', None)
        if not agent_prompt and (not agent_prompt_template):
            raise ValueError('The `prompt` or `prompt_template` for the following task is required: {}'.format(task))
        inputs = task.get('inputs', [])
        outputs = task.get('outputs', [])
        agent_name = generate_dynamic_class_name(node_name + ' Agent')
        agent_description = node_description
        agent_system_prompt = task.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
        agent_output_parser = task.get('output_parser', None)
        agent_parse_mode = task.get('parse_mode', 'str')
        agent_parse_func = task.get('parse_func', None)
        agent_parse_title = task.get('parse_title', None)
        tool_names = task.get('tool_names', None)
        node = WorkFlowNode.from_dict({'name': node_name, 'description': node_description, 'inputs': inputs, 'outputs': outputs, 'agents': [{'name': agent_name, 'description': agent_description, 'prompt': agent_prompt, 'prompt_template': agent_prompt_template, 'system_prompt': agent_system_prompt, 'inputs': inputs, 'outputs': outputs, 'output_parser': agent_output_parser, 'parse_mode': agent_parse_mode, 'parse_func': agent_parse_func, 'parse_title': agent_parse_title, 'tool_names': tool_names}]})
        return node

    def get_graph_info(self, **kwargs) -> dict:
        """
        Get the information of the workflow graph.
        """
        config = {'class_name': self.__class__.__name__, 'goal': self.goal, 'tasks': [{'name': node.name, 'description': node.description, 'inputs': [param.to_dict(ignore=['class_name']) for param in node.inputs], 'outputs': [param.to_dict(ignore=['class_name']) for param in node.outputs], 'prompt': node.agents[0].get('prompt', None), 'prompt_template': node.agents[0].get('prompt_template', None).to_dict() if node.agents[0].get('prompt_template', None) else None, 'system_prompt': node.agents[0].get('system_prompt', None), 'parse_mode': node.agents[0].get('parse_mode', 'str'), 'parse_func': node.agents[0].get('parse_func', None).__name__ if node.agents[0].get('parse_func', None) else None, 'parse_title': node.agents[0].get('parse_title', None), 'tool_names': node.agents[0].get('tool_names', None)} for node in self.nodes]}
        return config

    def save_module(self, path: str, ignore: List[str]=[], **kwargs):
        """
        Save the workflow graph to a module file.
        """
        logger.info('Saving {} to {}', self.__class__.__name__, path)
        config = self.get_graph_info()
        for ignore_key in ignore:
            config.pop(ignore_key, None)
        make_parent_folder(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return path

    def get_config(self) -> Dict:
        """
        Get a dictionary containing all necessary configuration to recreate this workflow graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new SequentialWorkFlowGraph instance
            with the same properties as this one.
        """
        return self.get_graph_info()

def _infer_nodes_from_tasks(self, tasks: List[dict]) -> List[WorkFlowNode]:
    nodes = [self._infer_node_from_task(task=task) for task in tasks]
    return nodes

