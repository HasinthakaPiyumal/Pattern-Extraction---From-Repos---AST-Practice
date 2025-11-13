# Cluster 25

class WorkFlowEdge(BaseModule):
    """
    Represents a directed edge in a workflow graph.
    
    Workflow edges connect tasks (nodes) in the workflow graph, establishing
    execution dependencies and data flow relationships. Each edge has a source
    node, target node, and optional priority to influence execution order.
    
    Attributes:
        source: Name of the source node (where the edge starts)
        target: Name of the target node (where the edge ends)
        priority: Numeric priority value for this edge (higher means higher priority)
    """
    source: str
    target: str
    priority: int = 0

    def __init__(self, edge_tuple: Optional[tuple]=(), **kwargs):
        """
        Initialize a WorkFlowEdge instance with either a tuple or keyword arguments.

        Parameters:
        ----------
            edge_tuple (tuple): a tuple containing the edge attributes in the format: (source, target, priority[optional]). 
                - source (str): the source of the edge. 
                - target (str): the target of the edge. 
                - priority (int, optional): The priority of the edge. Defaults to 0 if not provided.
            
            kwargs (dict): Key-value pairs specifying the edge attributes. These values will override those provided in `args` if both are supplied.

        Notes:
        ----------
            - Attributes provided via `kwargs` take precedence over those from the `args` tuple.
            - If `args` is empty or not provided, only `kwargs` will be used to initialize the instance.
        """
        data = self.init_from_tuple(edge_tuple)
        data.update(kwargs)
        super().__init__(**data)

    def init_from_tuple(self, edge_tuple: tuple) -> dict:
        if not edge_tuple:
            return {}
        keys = ['source', 'target', 'priority']
        data = {k: v for k, v in zip(keys, edge_tuple)}
        return data

    def compare_attrs(self):
        return (self.source, self.target, self.priority)

    def __eq__(self, other: 'WorkFlowEdge'):
        if not isinstance(other, WorkFlowEdge):
            return NotImplemented
        self_compare_attrs = self.compare_attrs()
        other_compare_attrs = other.compare_attrs()
        return all((self_attr == other_attr for self_attr, other_attr in zip(self_compare_attrs, other_compare_attrs)))

    def __hash__(self):
        return hash(self.compare_attrs())

def __eq__(self, other: 'WorkFlowEdge'):
    if not isinstance(other, WorkFlowEdge):
        return NotImplemented
    self_compare_attrs = self.compare_attrs()
    other_compare_attrs = other.compare_attrs()
    return all((self_attr == other_attr for self_attr, other_attr in zip(self_compare_attrs, other_compare_attrs)))

def __hash__(self):
    return hash(self.compare_attrs())

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

