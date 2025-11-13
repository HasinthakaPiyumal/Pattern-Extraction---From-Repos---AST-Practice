# Cluster 27

class WorkFlowGraph(BaseModule):
    """
    Represents a complete workflow as a directed graph.
    
    WorkFlowGraph models a workflow as a directed graph where nodes represent tasks
    and edges represent dependencies and data flow between tasks. It provides
    methods for constructing, validating, traversing, and executing workflows.
    
    The graph structure supports advanced features like detecting and handling loops,
    determining execution order, and tracking execution state.
    
    Attributes:
        goal: The high-level objective of this workflow
        nodes: List of WorkFlowNode instances representing tasks
        edges: List of WorkFlowEdge instances representing dependencies
        graph: Internal NetworkX MultiDiGraph or another WorkFlowGraph
    """
    goal: str
    nodes: Optional[List[WorkFlowNode]] = []
    edges: Optional[List[WorkFlowEdge]] = []
    graph: Optional[Union[MultiDiGraph, 'WorkFlowGraph']] = Field(default=None, exclude=True)

    def init_module(self):
        self._lock = threading.Lock()
        if not self.graph:
            self._init_from_nodes_and_edges(self.nodes, self.edges)
        elif isinstance(self.graph, MultiDiGraph):
            self._init_from_multidigraph(self.graph, self.nodes, self.edges)
        elif isinstance(self.graph, WorkFlowGraph):
            self._init_from_workflowgraph(self.graph, self.nodes, self.edges)
        else:
            raise TypeError(f'{type(self.graph)} is an unknown type for graph. Supported types: [MultiDiGraph, WorkFlowGraph]')
        self._validate_workflow_structure()
        self.update_graph()

    def update_graph(self):
        self._loops = self._find_all_loops()

    def _init_from_nodes_and_edges(self, nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
        """
        Initialize the WorkFlowGraph from a set of nodes and edges. 
        """
        if edges and (not nodes):
            raise ValueError('edges cannot be passed without nodes or a graph')
        self.nodes = []
        self.edges = []
        self.graph = MultiDiGraph()
        self.add_nodes(*nodes, update_graph=False)
        self.add_edges(*edges, update_graph=False)

    def _init_from_multidigraph(self, graph: MultiDiGraph, nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
        graph_nodes = [deepcopy(node_attrs['ref']) for _, node_attrs in graph.nodes(data=True)]
        graph_edges = [deepcopy(edge_attrs['ref']) for *_, edge_attrs in graph.edges(data=True)]
        graph_nodes = self.merge_nodes(graph_nodes, nodes)
        graph_edges = self.merge_edges(graph_edges, edges)
        self._init_from_nodes_and_edges(nodes=graph_nodes, edges=graph_edges)

    def _init_from_workflowgraph(self, graph: 'WorkFlowGraph', nodes: List[WorkFlowNode]=[], edges: List[WorkFlowEdge]=[]):
        graph_nodes = deepcopy(graph.nodes)
        graph_edges = deepcopy(graph.edges)
        graph_nodes = self.merge_nodes(graph_nodes, nodes)
        graph_edges = self.merge_edges(graph_edges, edges)
        self._init_from_nodes_and_edges(nodes=graph_nodes, edges=graph_edges)

    def _validate_workflow_structure(self):
        isolated_nodes = list(nx.isolates(self.graph))
        if len(self.graph.nodes) > 1 and isolated_nodes:
            logger.warning(f'The workflow contains isolated nodes: {isolated_nodes}')
        initial_nodes = self.find_initial_nodes()
        if len(self.graph.nodes) > 1 and (not initial_nodes):
            error_message = 'There are no initial nodes in the workflow!'
            logger.error(error_message)
            raise ValueError(error_message)
        end_nodes = self.find_end_nodes()
        if len(self.graph.nodes) > 1 and (not end_nodes):
            logger.warning('There are no end nodes in the workflow')

    def find_initial_nodes(self) -> List[str]:
        initial_nodes = [node for node, in_degree in self.graph.in_degree() if in_degree == 0]
        return initial_nodes

    def find_end_nodes(self) -> List[str]:
        end_nodes = [node for node, out_degree in self.graph.out_degree() if out_degree == 0]
        return end_nodes

    def _find_loops(self, start_node: Union[str, WorkFlowNode]) -> Dict[str, list]:
        if isinstance(start_node, str):
            start_node = self.get_node(node_name=start_node)
        start_node_name = start_node.name
        loops = defaultdict(list)

        def dfs(current_node_name: str, path: List[str]):
            if current_node_name in path:
                loops[current_node_name].append(path[path.index(current_node_name):])
                return
            path.append(current_node_name)
            children = self.get_node_children(current_node_name)
            if children:
                for child in children:
                    dfs(child, path)
            path.pop()
        dfs(start_node_name, [])
        return loops

    def _find_all_loops(self) -> Dict[str, list]:
        initial_nodes = self.find_initial_nodes()
        if not initial_nodes:
            return {}

        def contain_loop(loops: List[List[str]], new_loop: List[str]):
            if not loops:
                return False
            return frozenset(new_loop) in [frozenset(loop) for loop in loops]
        all_loops = defaultdict(list)
        for initial_node in initial_nodes:
            loops_from_init_node = self._find_loops(initial_node)
            for start_node, loops in loops_from_init_node.items():
                for loop in loops:
                    if not contain_loop(all_loops[start_node], loop):
                        all_loops[start_node].append(loop)
        if len(all_loops) <= 1:
            return all_loops
        loop_to_start_nodes = defaultdict(dict)
        for start_node, loops in all_loops.items():
            for loop in loops:
                normalized_loop = frozenset(loop)
                loop_to_start_nodes[normalized_loop][start_node] = loop
        all_paths: List[List[str]] = []
        for initial_node in initial_nodes:
            all_paths.extend(self.get_all_paths_from_node(initial_node))

        def rank_nodes(nodes: List[str]):
            if len(nodes) == 1:
                return nodes[0]
            path_contain_nodes = None
            for path in all_paths:
                if all((node in path for node in nodes)):
                    path_contain_nodes = path
                    break
            if path_contain_nodes is None:
                raise ValueError(f"Couldn't find a path that contain nodes: {nodes}")
            node_indices = [path.index(node) for node in nodes]
            return nodes[node_indices.index(min(node_indices))]
        all_loops = defaultdict(list)
        for start_node_loop in loop_to_start_nodes.values():
            first_node = rank_nodes(list(start_node_loop.keys()))
            all_loops[first_node].append(start_node_loop[first_node])
        return all_loops

    def add_node(self, node: WorkFlowNode, update_graph: bool=True, **kwargs):
        if not isinstance(node, WorkFlowNode):
            raise ValueError(f'{node} is not a valid WorkFlowNode instance!')
        if self.node_exists(node.name):
            raise ValueError(f'Duplicate node names are not allowed! Found duplicate node name: {node.name}')
        self.nodes.append(node)
        self.graph.add_node(node.name, ref=node)
        if update_graph:
            self.update_graph()

    def add_edge(self, edge: WorkFlowEdge, update_graph: bool=True, **kwargs):
        if not isinstance(edge, WorkFlowEdge):
            raise ValueError(f'{edge} is not a valid WorkFlowEdge instance!')
        for attr, node_name in zip(['source', 'target'], [edge.source, edge.target]):
            if not self.node_exists(node_name):
                raise ValueError(f'{attr} node {node_name} does not exists!')
        if self.edge_exists(edge):
            raise ValueError(f'Duplicate edges are not allowed! Found duplicate edges: {edge}')
        source_node = self.get_node(edge.source)
        target_node = self.get_node(edge.target)
        source_output_names = set((param.name for param in source_node.outputs))
        target_input_names = set((param.name for param in target_node.inputs))
        if len(source_output_names & target_input_names) == 0:
            logger.warning(f'The edge ({edge.source}, {edge.target}) has no matching inputs and outputs! You may need to check the inputs and outputs of the nodes to ensure that at least one input of the target node is the output of the source node.')
        self.edges.append(edge)
        self.graph.add_edge(edge.source, edge.target, ref=edge)
        if update_graph:
            self.update_graph()

    def add_nodes(self, *nodes: WorkFlowNode, update_graph: bool=True, **kwargs):
        nodes: list = list(nodes)
        nodes.extend([kwargs.pop(var) for var in ['node', 'nodes'] if var in kwargs])
        for node in nodes:
            if isinstance(node, (tuple, list)):
                for n in node:
                    self.add_node(n, update_graph=update_graph, **kwargs)
            else:
                self.add_node(node, update_graph=update_graph, **kwargs)

    def add_edges(self, *edges: WorkFlowEdge, update_graph: bool=True, **kwargs):
        edges: list = list(edges)
        edges.extend([kwargs.pop(var) for var in ['edge', 'edges'] if var in kwargs])
        for edge in edges:
            if isinstance(edge, (tuple, list)):
                for e in edge:
                    self.add_edge(e, update_graph=update_graph, **kwargs)
            else:
                self.add_edge(edge, update_graph=update_graph, **kwargs)

    def node_exists(self, node: Union[str, WorkFlowNode]) -> bool:
        if isinstance(node, str):
            return node in self.graph.nodes
        elif isinstance(node, WorkFlowNode):
            return node.name in self.graph.nodes
        else:
            raise TypeError('node must be a str or WorkFlowNode instance')

    def _edge_exists(self, source: str, target: str, **attr_filters) -> bool:
        if not self.graph.has_edge(source, target):
            return False
        if attr_filters:
            for key, value in attr_filters.items():
                if key not in self.graph[source][target] or self.graph[source][target][key] != value:
                    return False
        return True

    def edge_exists(self, edge: Union[Tuple[str, str], WorkFlowEdge], **attr_filters) -> bool:
        """
        Check whether an edge exists in the workflow graph. The input `edge` can either be a tuple or a WorkFlowEdge instance.

        1. If a tuple is passed, it should be (source, target). The function will only determin whether there is an edge between the source node and the target node. 
        If attr_filters is passed, they will also be used to match the edge attributes. 
        2. If a WorkFlowEdge is passed, it will use the __eq__ method in WorkFlowEdge to determine 

        Parameters:
        ----------
            edge (Union[Tuple[str, str], WorkFlowEdge]):
                - If a tuple is provided, it should be in the format `(source, target)`. 
                The method will check whether there is an edge between the source and target nodes.
                If `attr_filters` are provided, they will be used to match edge attributes.
                - If a WorkFlowEdge instance is provided, the method will use the `__eq__` method in WorkFlowEdge 
                to determine whether the edge exists.

            attr_filters (dict, optional):
                Additional attributes to filter edges when `edge` is a tuple.

        Returns:
        -------
            bool: True if the edge exists and matches the filters (if provided); False otherwise.
        """
        if isinstance(edge, tuple):
            assert len(edge) == 2, 'edge must be a tuple (source, target) or WorkFlowEdge instance'
            source, target = edge
            return self._edge_exists(source, target, **attr_filters)
        elif isinstance(edge, WorkFlowEdge):
            return edge in self.edges
        else:
            raise TypeError('edge must be a tuple (source, target) or WorkFlowEdge instance')

    def is_loop_start(self, node: Union[str, WorkFlowNode]) -> bool:
        if len(self._loops) == 0:
            return False
        node_name = node if isinstance(node, str) else node.name
        return node_name in self._loops

    def is_loop_end(self, node: Union[str, WorkFlowNode]) -> bool:
        if len(self._loops) == 0:
            return False
        loop_end_nodes = set()
        node_name = node if isinstance(node, str) else node.name
        for loops in self._loops.values():
            loop_end_nodes.update([loop[-1] for loop in loops])
        return node_name in loop_end_nodes

    def find_loops_with_start_and_end(self, start_node: Union[str, WorkFlowNode], end_node: Union[str, WorkFlowNode]) -> List[List[str]]:
        if len(self._loops) == 0:
            return []
        start_node_name = start_node if isinstance(start_node, str) else start_node.name
        end_node_name = end_node if isinstance(end_node, str) else end_node.name
        if start_node_name not in self._loops:
            return []
        target = []
        for loop in self._loops[start_node_name]:
            if loop[-1] == end_node_name:
                target.append(loop)
        return target

    def merge_nodes(self, nodes: List[WorkFlowNode], new_nodes: List[WorkFlowNode]):
        node_names = {node.name for node in nodes}
        for node in new_nodes:
            if node.name in node_names:
                continue
            nodes.append(node)
        return nodes

    def merge_edges(self, edges: List[WorkFlowEdge], new_edges: List[WorkFlowEdge]):
        for edge in new_edges:
            if edge in edges:
                continue
            edges.append(edge)
        return edges

    def list_nodes(self) -> List[str]:
        """
        return the names of all nodes 
        """
        return [node.name for node in self.nodes]

    def get_node(self, node_name: str) -> WorkFlowNode:
        """
        return a WorkFlowNode instance based on its name.
        """
        if not self.node_exists(node=node_name):
            raise KeyError(f'{node_name} is an invalid node name. Currently available node names: {self.list_nodes()}')
        return self.graph.nodes[node_name]['ref']

    def get_node_status(self, node: Union[str, WorkFlowNode]) -> WorkFlowNodeState:
        if isinstance(node, str):
            node = self.get_node(node_name=node)
        return node.get_status()

    @property
    def is_complete(self):
        leaf_nodes = [self.get_node(name) for name in self.find_end_nodes()]
        node_complete_list = [node.is_complete for node in leaf_nodes]
        if len(node_complete_list) == 0:
            return True
        if all(node_complete_list):
            return True
        return False

    def reset_graph(self):
        """
        set the status of all nodes to pending
        """
        for node in self.nodes:
            node.set_status(WorkFlowNodeState.PENDING)

    def set_node_status(self, node: Union[str, WorkFlowNode], new_state: WorkFlowNodeState) -> bool:
        """
        Update the state of a specific node. 

        Args:
            node (Union[str, WorkFlowNode]): The name of a node or the node instance.
            new_state (WorkFlowNodeState): The new state to set.
        
        Returns:
            bool: True if the state was updated successfully, False otherwise.
        """
        flag = False
        try:
            if isinstance(node, str):
                node = self.get_node(node_name=node)
            node.set_status(new_state)
            flag = True
        except Exception as e:
            raise ValueError(f'An error occurs when setting node status: {e}')
        return flag

    def pending(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.PENDING)

    def running(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.RUNNING)

    def completed(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.COMPLETED)

    def failed(self, node: Union[str, WorkFlowNode]) -> bool:
        return self.set_node_status(node=node, new_state=WorkFlowNodeState.FAILED)

    def get_node_children(self, node: Union[str, WorkFlowNode]) -> List[str]:
        node_name = node if isinstance(node, str) else node.name
        if not self.node_exists(node=node):
            raise ValueError(f'Node `{node_name}` does not exists!')
        children = list(self.graph.successors(node_name))
        return children

    def get_node_predecessors(self, node: Union[str, WorkFlowNode]) -> List[str]:
        node_name = node if isinstance(node, str) else node.name
        if not self.node_exists(node=node):
            raise ValueError(f'Node `{node_name}` does not exists!')
        predecessors = list(self.graph.predecessors(node_name))
        return predecessors

    def get_uncomplete_initial_nodes(self) -> List[str]:
        initial_nodes = self.find_initial_nodes()
        are_initial_nodes_complete = [self.get_node(node_name).is_complete for node_name in initial_nodes]
        uncomplete_initial_nodes = []
        for node_name, is_complete in zip(initial_nodes, are_initial_nodes_complete):
            if not is_complete:
                uncomplete_initial_nodes.append(node_name)
        return uncomplete_initial_nodes

    def get_all_paths_from_node(self, start_node: Union[str, WorkFlowNode]) -> List[List[str]]:
        if isinstance(start_node, str):
            start_node = self.get_node(node_name=start_node)
        start_node_name = start_node.name
        all_paths = []
        visited = set()

        def dfs(current_node_name: str, path: List[str]):
            if current_node_name in visited:
                if path and len(self.get_node_children(path[-1])) == 1:
                    all_paths.append(path.copy())
                return
            path.append(current_node_name)
            visited.add(current_node_name)
            children = self.get_node_children(current_node_name)
            if not children:
                all_paths.append(path.copy())
            else:
                for child in children:
                    dfs(child, path)
            path.pop()
            visited.remove(current_node_name)
        dfs(start_node_name, [])
        return all_paths

    def find_completed_leaf_nodes(self, start_node: Union[str, WorkFlowNode]) -> List[str]:
        if isinstance(start_node, str):
            start_node = self.get_node(node_name=start_node)
        start_node_name = start_node.name
        paths_starting_from_node = self.get_all_paths_from_node(start_node=start_node_name)
        last_completed_nodes = []
        for path in paths_starting_from_node:
            if not path:
                continue
            completed_node = None
            for path_node in path:
                if self.get_node(path_node).is_complete:
                    completed_node = path_node
                else:
                    break
            if completed_node and completed_node not in last_completed_nodes:
                last_completed_nodes.append(completed_node)
        last_completed_nodes = last_completed_nodes[::-1]
        return last_completed_nodes

    def find_completed_leaf_nodes_start_from_initial_nodes(self) -> List[str]:
        initial_nodes = self.find_initial_nodes()
        completed_leaf_nodes = []
        for initial_node in initial_nodes:
            for complete_node in self.find_completed_leaf_nodes(start_node=initial_node):
                if complete_node not in completed_leaf_nodes:
                    completed_leaf_nodes.append(complete_node)
        return completed_leaf_nodes

    def get_all_children_nodes(self, nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        node_names = [node if isinstance(node, str) else node.name for node in nodes]
        children_nodes = []
        for node_name in node_names:
            for child in self.get_node_children(node_name):
                if child not in children_nodes:
                    children_nodes.append(child)
        return children_nodes

    def filter_completed_nodes(self, nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        """
        remove completed nodes from `nodes`
        """
        node_names = [node if isinstance(node, str) else node.name for node in nodes]
        uncompleted_nodes = []
        for node_name in node_names:
            if self.get_node(node_name).is_complete:
                continue
            uncompleted_nodes.append(node_name)
        return uncompleted_nodes

    def get_candidate_children_nodes(self, completed_nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        """
        Return the next set of possible tasks to execute. If there are no loops in the graph, consider only the uncompleted children. 
        If there exists loops, also consider the previous completed tasks.

        Args:
            completed_nodes (List[Union[str, WorkFlowNode]]): A list of completed nodes.
            
        Returns:
            List[str]: List of node names that are candidates for execution.
        """
        node_names = [node if isinstance(node, str) else node.name for node in completed_nodes]
        has_loop = len(self._loops) > 0
        if has_loop:
            uncompleted_children_nodes = []
            for node_name in node_names:
                children_nodes = self.get_all_children_nodes(nodes=[node_name])
                if self.is_loop_end(node=node_name):
                    current_uncompleted_children_nodes = []
                    for child in children_nodes:
                        if self.is_loop_start(node=child):
                            current_uncompleted_children_nodes.append(child)
                        else:
                            current_uncompleted_children_nodes.extend(self.filter_completed_nodes(nodes=[child]))
                else:
                    current_uncompleted_children_nodes = self.filter_completed_nodes(nodes=children_nodes)
                for child in current_uncompleted_children_nodes:
                    if child not in uncompleted_children_nodes:
                        uncompleted_children_nodes.append(child)
        else:
            children_nodes = self.get_all_children_nodes(nodes=node_names)
            uncompleted_children_nodes = self.filter_completed_nodes(nodes=children_nodes)
        return uncompleted_children_nodes

    def are_dependencies_complete(self, node_name: str) -> bool:
        """
        Check if all predecessors for a node are complete.

        Args:
            node_name (str): The name of the task/node to check.
        
        Returns:
            bool: True if all predecessors are complete, False otherwise.
        """
        has_loop = len(self._loops) > 0
        predecessors = self.get_node_predecessors(node=node_name)
        if has_loop and self.is_loop_start(node=node_name):
            flag = True
            for pre in predecessors:
                if self.is_loop_end(pre):
                    pass
                else:
                    flag &= self.get_node(pre).is_complete
        else:
            flag = all((self.get_node(pre).is_complete for pre in predecessors))
        return flag

    def filter_nodes_with_uncompleted_predecessors(self, nodes: List[Union[str, WorkFlowNode]]) -> List[str]:
        node_names = [node if isinstance(node, str) else node.name for node in nodes]
        nodes_with_completed_predecessors = []
        for node_name in node_names:
            if self.are_dependencies_complete(node_name=node_name):
                nodes_with_completed_predecessors.append(node_name)
        return nodes_with_completed_predecessors

    def get_next_candidate_nodes(self) -> List[str]:
        uncomplete_initial_nodes = self.get_uncomplete_initial_nodes()
        if len(uncomplete_initial_nodes) > 0:
            return uncomplete_initial_nodes
        completed_leaf_nodes = self.find_completed_leaf_nodes_start_from_initial_nodes()
        candidate_children_nodes = self.get_candidate_children_nodes(completed_nodes=completed_leaf_nodes)
        children_nodes_with_complete_predecessors = self.filter_nodes_with_uncompleted_predecessors(candidate_children_nodes)
        return children_nodes_with_complete_predecessors

    def next(self) -> List[WorkFlowNode]:
        if self.is_complete:
            return []
        candidate_node_names = self.get_next_candidate_nodes()
        candidate_tasks = [self.get_node(node_name=node_name) for node_name in candidate_node_names]
        return candidate_tasks

    def step(self, source_node: Union[str, WorkFlowNode], target_node: Union[str, WorkFlowNode]):
        if source_node is None:
            self.running(target_node)
            return
        source_node_name = source_node if isinstance(source_node, str) else source_node.name
        target_node_name = target_node if isinstance(target_node, str) else target_node.name
        source_node_status = self.get_node_status(source_node_name)
        if source_node_status != WorkFlowNodeState.COMPLETED:
            raise ValueError(f'The state of `source_node` should be WorkFlowNodeState.COMPLETED, but found {source_node_status}')
        if self.is_loop_end(source_node_name) and self.is_loop_start(target_node_name):
            loops = self.find_loops_with_start_and_end(start_node=target_node_name, end_node=source_node_name)
            loop_nodes = set(sum(loops, []))
            for loop_node in loop_nodes:
                self.pending(node=loop_node)
        if not self.edge_exists(edge=(source_node_name, target_node_name)):
            all_paths = self.get_all_paths_from_node(start_node=target_node_name)
            for path in all_paths:
                if source_node_name in path:
                    for node_name in path:
                        self.pending(node=node_name)
        self.running(node=target_node_name)

    def get_node_description(self, node: Union[str, WorkFlowNode]) -> str:
        if isinstance(node, str):
            node = self.get_node(node_name=node)

        def format_parameters(params: List[Parameter]) -> str:
            if not params:
                return '  - None'
            return '\n'.join((f'  - {param.name} ({param.type})' for param in params))

        def format_agents(agent_names: List[str]) -> str:
            if not agent_names:
                return 'None'
            return '\n'.join((f'  - {name}' for name in agent_names))

        def format_action_graph(action_graph: ActionGraph) -> str:
            if action_graph is None:
                return '  - None'
            return type(action_graph).__name__
        desc = f'Name: {node.name}\nInputs:\n{format_parameters(node.inputs)}\nOutputs:\n{format_parameters(node.outputs)}\nAgents:\n{format_agents(node.get_agents())}\nAction Graph:\n{format_action_graph(node.action_graph)}'
        return desc

    def display(self):
        """
        Display the workflow graph with node and edge attributes.
        Nodes are colored based on their status.
        """
        import matplotlib.pyplot as plt
        status_colors = {WorkFlowNodeState.PENDING: 'lightgray', WorkFlowNodeState.RUNNING: 'orange', WorkFlowNodeState.COMPLETED: 'green', WorkFlowNodeState.FAILED: 'red'}
        if not self.graph.nodes:
            print('Graph is empty. No nodes to display.')
            return
        node_colors = [status_colors.get(self.get_node_status(node), 'lightgray') for node in self.graph.nodes]
        node_labels = {node: self.get_node_description(data['ref']) for node, data in self.graph.nodes(data=True)}
        if len(self.graph.nodes) == 1:
            single_node = list(self.graph.nodes)[0]
            pos = {single_node: (0, 0)}
        else:
            pos = nx.shell_layout(self.graph)
        plt.figure(figsize=(12, 8))
        nx.draw(self.graph, pos, with_labels=False, node_color=node_colors, edge_color='black', node_size=1500, font_size=8, font_color='black', font_weight='bold')
        if len(self.graph.nodes) == 1:
            for node, (x, y) in pos.items():
                plt.text(x + 0.005, y, node_labels[node], ha='left', va='center', fontsize=9, bbox=dict(facecolor='white', alpha=0.7))
        else:
            y_positions = [y for _, y in pos.values()]
            y_min, y_max = (min(y_positions), max(y_positions))
            lower_third_boundary = y_min + (y_max - y_min) / 3
            text_offsets = {}
            for node, (x, y) in pos.items():
                if y < lower_third_boundary:
                    text_offsets[node] = (x - 0.2, y + 0.23)
                else:
                    text_offsets[node] = (x - 0.2, y - 0.23)
            for node, (x, y) in text_offsets.items():
                plt.text(x, y, node_labels[node], ha='left', va='center', fontsize=9, bbox=dict(facecolor='white', alpha=0.7))
        edge_labels = nx.get_edge_attributes(self.graph, 'priority')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', label=status.name, markersize=10, markerfacecolor=color) for status, color in status_colors.items()]
        plt.legend(handles=legend_elements, title='Workflow Node Status', loc='upper left', fontsize='medium')
        plt.title('Workflow Graph')
        plt.show()

    def get_workflow_description(self) -> str:

        def format_param_requirement(required: bool):
            return 'required' if required else 'optional'

        def format_parameters(params: List[Parameter]) -> str:
            if not params:
                return 'None'
            return '\n'.join((f'  - {param.name} ({param.type}, {format_param_requirement(param.required)}): {param.description}' for param in params))
        subtask_texts = []
        for node in self.nodes:
            text = f'Task Name: {node.name}\nDescription: {node.description}\nInputs:\n{format_parameters(node.inputs)}\nOutputs:\n{format_parameters(node.outputs)}'
            subtask_texts.append(text)
        workflow_desc = '\n\n'.join(subtask_texts)
        return workflow_desc

    def _infer_edges_from_nodes(self, nodes: List[WorkFlowNode]) -> List[WorkFlowEdge]:
        if not nodes:
            return []
        edges: List[WorkFlowEdge] = []
        for node in nodes:
            for another_node in nodes:
                if node.name == another_node.name:
                    continue
                node_output_params = [param.name for param in node.outputs]
                another_node_input_params = [param.name for param in another_node.inputs]
                if any([param in another_node_input_params for param in node_output_params]):
                    edges.append(WorkFlowEdge(edge_tuple=(node.name, another_node.name)))
        return edges

    def get_config(self) -> dict:
        """
        Get a dictionary containing all necessary configuration to recreate this workflow graph.
        
        Returns:
            dict: A configuration dictionary that can be used to initialize a new WorkFlowGraph instance
            with the same properties as this one.
        """
        config = self.to_dict()
        config.pop('graph', None)
        return config

def find_end_nodes(self) -> List[str]:
    end_nodes = [node for node, out_degree in self.graph.out_degree() if out_degree == 0]
    return end_nodes

