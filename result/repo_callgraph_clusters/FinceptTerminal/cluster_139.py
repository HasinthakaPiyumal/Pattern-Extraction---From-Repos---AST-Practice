# Cluster 139

class GlobalNodeState:
    """Centralized state management for node system"""

    def __init__(self):
        self.node_outputs: Dict[str, Any] = {}
        self.node_connections: Dict[str, Dict[str, List[str]]] = {}
        self.node_registry: Dict[int, Dict[str, Any]] = {}
        self.link_registry: Dict[int, Tuple[str, str, str]] = {}
        self.execution_queue: queue.Queue = queue.Queue()
        self.execution_thread: Optional[threading.Thread] = None
        self.is_executing: bool = False
        self.cache: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = {}

    def clear(self):
        """Clear all state"""
        self.node_outputs.clear()
        self.node_connections.clear()
        self.node_registry.clear()
        self.link_registry.clear()
        self.cache.clear()
        self.performance_metrics.clear()
        self.is_executing = False

def __init__(self):
    self.node_outputs: Dict[str, Any] = {}
    self.node_connections: Dict[str, Dict[str, List[str]]] = {}
    self.node_registry: Dict[int, Dict[str, Any]] = {}
    self.link_registry: Dict[int, Tuple[str, str, str]] = {}
    self.execution_queue: queue.Queue = queue.Queue()
    self.execution_thread: Optional[threading.Thread] = None
    self.is_executing: bool = False
    self.cache: Dict[str, Any] = {}
    self.performance_metrics: Dict[str, Any] = {}

