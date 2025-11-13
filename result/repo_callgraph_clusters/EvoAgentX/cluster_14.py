# Cluster 14

class WorkFlowJSONEditorGUI:
    """GUI JSON Editor GUI based on tkinter"""

    def __init__(self, json_data: Dict[str, Any]):
        self.json_data = json_data
        self.result = None
        self.root = None

    def edit_json(self) -> Optional[Dict[str, Any]]:
        """start the json editor and return the modified data"""
        try:
            import tkinter as tk
            from tkinter import ttk, scrolledtext
        except ImportError:
            print('⚠️  tkinter is not available, use the text editor')
            return self._edit_json_text()
        self.root = tk.Tk()
        self.root.title('WorkFlow JSON Editor')
        self.root.geometry('800x600')
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        title_label = ttk.Label(main_frame, text='Edit WorkFlow JSON Structure', font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        ttk.Button(button_frame, text='📝 Format', command=self._format_json).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text='✅ Validate', command=self._validate_json).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text='🔄 Reset', command=self._reset_json).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text='📋 Copy', command=self._copy_json).pack(fill=tk.X, pady=2)
        ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(button_frame, text='Quick Operations:', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Button(button_frame, text='➕ Add Node', command=self._add_node_quick).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text='🔗 Add Edge', command=self._add_edge_quick).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text='📄 Template', command=self._insert_template).pack(fill=tk.X, pady=2)
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=60, height=30, font=('Consolas', 10))
        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.text_area.insert(tk.END, json.dumps(self.json_data, indent=2, ensure_ascii=False))
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(bottom_frame, text='💾 Save and Close', command=self._save_and_close).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text='❌ Cancel', command=self._cancel).pack(side=tk.LEFT, padx=(0, 5))
        self.status_label = ttk.Label(bottom_frame, text='Ready', foreground='green')
        self.status_label.pack(side=tk.RIGHT)
        self.root.mainloop()
        return self.result

    def _format_json(self):
        """format the json"""
        try:
            text = self.text_area.get(1.0, tk.END)
            data = json.loads(text)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, formatted)
            self.status_label.config(text='✅ Formatting completed', foreground='green')
        except json.JSONDecodeError as e:
            self.status_label.config(text=f'❌ JSON format error: {e}', foreground='red')

    def _validate_json(self):
        """validate the json"""
        try:
            text = self.text_area.get(1.0, tk.END)
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError('The root node must be a dictionary')
            if 'nodes' not in data or not isinstance(data['nodes'], list):
                raise ValueError('Must contain nodes array')
            node_names = set()
            for node in data['nodes']:
                if not isinstance(node, dict) or 'name' not in node:
                    raise ValueError('Each node must contain name field')
                name = node['name']
                if name in node_names:
                    raise ValueError(f'Node name duplicate: {name}')
                node_names.add(name)
            if 'edges' in data:
                for edge in data['edges']:
                    if not isinstance(edge, dict):
                        continue
                    source = edge.get('source')
                    target = edge.get('target')
                    if source and source not in node_names:
                        raise ValueError(f'The source node of the edge does not exist: {source}')
                    if target and target not in node_names:
                        raise ValueError(f'The target node of the edge does not exist: {target}')
            self.status_label.config(text='✅ JSON structure is valid', foreground='green')
        except (json.JSONDecodeError, ValueError) as e:
            self.status_label.config(text=f'❌ Validation failed: {e}', foreground='red')

    def _reset_json(self):
        """reset the json"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, json.dumps(self.json_data, indent=2, ensure_ascii=False))
        self.status_label.config(text='🔄 Reset', foreground='blue')

    def _copy_json(self):
        """copy the json to the clipboard"""
        try:
            text = self.text_area.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_label.config(text='📋 Copied to clipboard', foreground='blue')
        except Exception as e:
            self.status_label.config(text=f'❌ Copy failed: {e}', foreground='red')

    def _add_node_quick(self):
        """quick add node"""
        try:
            import tkinter.simpledialog as sd
            name = sd.askstring('Add Node', 'Node name:')
            if not name:
                return
            desc = sd.askstring('Add Node', 'Node description:')
            if not desc:
                desc = f'The description of the node {name}'
            node_template = {'class_name': 'WorkFlowNode', 'name': name, 'description': desc, 'inputs': [], 'outputs': [], 'agents': [], 'status': 'pending'}
            current_text = self.text_area.get(1.0, tk.END)
            try:
                data = json.loads(current_text)
                data.setdefault('nodes', []).append(node_template)
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
                self.status_label.config(text=f'✅ Added node: {name}', foreground='green')
            except json.JSONDecodeError:
                self.status_label.config(text='❌ Current JSON format error, cannot add node', foreground='red')
        except ImportError:
            self.status_label.config(text='❌ Cannot use dialog', foreground='red')

    def _add_edge_quick(self):
        """quick add edge"""
        try:
            import tkinter.simpledialog as sd
            current_text = self.text_area.get(1.0, tk.END)
            try:
                data = json.loads(current_text)
                nodes = data.get('nodes', [])
                node_names = [node.get('name') for node in nodes if node.get('name')]
                if len(node_names) < 2:
                    self.status_label.config(text='❌ At least 2 nodes are required to add edge', foreground='red')
                    return
                source = sd.askstring('Add Edge', f'Source node (optional: {', '.join(node_names)}):')
                if not source or source not in node_names:
                    self.status_label.config(text='❌ Source node invalid', foreground='red')
                    return
                target = sd.askstring('Add Edge', f'Target node (optional: {', '.join(node_names)}):')
                if not target or target not in node_names:
                    self.status_label.config(text='❌ Target node invalid', foreground='red')
                    return
                edge_template = {'class_name': 'WorkFlowEdge', 'source': source, 'target': target, 'priority': 0}
                data.setdefault('edges', []).append(edge_template)
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
                self.status_label.config(text=f'✅ Added edge: {source} -> {target}', foreground='green')
            except json.JSONDecodeError:
                self.status_label.config(text='❌ Current JSON format error, cannot add edge', foreground='red')
        except ImportError:
            self.status_label.config(text='❌ Cannot use dialog', foreground='red')

    def _insert_template(self):
        """insert template"""
        templates = {'Simple Node': {'class_name': 'WorkFlowNode', 'name': 'new_node', 'description': 'New node description', 'inputs': [{'class_name': 'Parameter', 'name': 'input1', 'type': 'string', 'description': 'Input parameter', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'output1', 'type': 'string', 'description': 'Output parameter', 'required': True}], 'agents': [], 'status': 'pending'}, 'CustomizeAgent': {'name': 'my_agent', 'description': 'Customize Agent', 'inputs': [{'name': 'input1', 'type': 'string', 'description': 'Input', 'required': True}], 'outputs': [{'name': 'output1', 'type': 'string', 'description': 'Output', 'required': True}], 'prompt': 'Process input: {input1}', 'parse_mode': 'str'}}
        template_window = tk.Toplevel(self.root)
        template_window.title('Select Template')
        template_window.geometry('400x300')
        ttk.Label(template_window, text='Select the template to insert:').pack(pady=10)
        template_listbox = tk.Listbox(template_window)
        template_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for template_name in templates.keys():
            template_listbox.insert(tk.END, template_name)

        def insert_selected():
            selection = template_listbox.curselection()
            if selection:
                template_name = template_listbox.get(selection[0])
                template_json = json.dumps(templates[template_name], indent=2, ensure_ascii=False)
                self.text_area.insert(tk.INSERT, f'\n{template_json}\n')
                self.status_label.config(text=f'✅ Inserted template: {template_name}', foreground='green')
                template_window.destroy()
        ttk.Button(template_window, text='Insert', command=insert_selected).pack(pady=10)
        ttk.Button(template_window, text='Cancel', command=template_window.destroy).pack()

    def _save_and_close(self):
        """save and close"""
        try:
            text = self.text_area.get(1.0, tk.END)
            self.result = json.loads(text)
            self.root.destroy()
        except json.JSONDecodeError as e:
            self.status_label.config(text=f'❌ JSON format error: {e}', foreground='red')

    def _cancel(self):
        """cancel"""
        self.result = None
        self.root.destroy()

    def _edit_json_text(self) -> Optional[Dict[str, Any]]:
        """use the text editor to edit the json (backup solution)"""
        import tempfile
        import subprocess
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(self.json_data, f, indent=2, ensure_ascii=False)
            temp_file = f.name
        try:
            print(f'📝 Opening file editor: {temp_file}')
            print('💡 Please save the file and close the editor after editing')
            if os.name == 'nt':
                subprocess.run(['notepad', temp_file])
            elif os.name == 'posix':
                subprocess.run(['nano', temp_file])
            with open(temp_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            return result
        except Exception as e:
            print(f'❌ Editor opening failed: {e}')
            return None
        finally:
            os.unlink(temp_file)

def edit_json(self) -> Optional[Dict[str, Any]]:
    """start the json editor and return the modified data"""
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext
    except ImportError:
        print('⚠️  tkinter is not available, use the text editor')
        return self._edit_json_text()
    self.root = tk.Tk()
    self.root.title('WorkFlow JSON Editor')
    self.root.geometry('800x600')
    main_frame = ttk.Frame(self.root, padding='10')
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    self.root.columnconfigure(0, weight=1)
    self.root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(1, weight=1)
    title_label = ttk.Label(main_frame, text='Edit WorkFlow JSON Structure', font=('Arial', 14, 'bold'))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
    ttk.Button(button_frame, text='📝 Format', command=self._format_json).pack(fill=tk.X, pady=2)
    ttk.Button(button_frame, text='✅ Validate', command=self._validate_json).pack(fill=tk.X, pady=2)
    ttk.Button(button_frame, text='🔄 Reset', command=self._reset_json).pack(fill=tk.X, pady=2)
    ttk.Button(button_frame, text='📋 Copy', command=self._copy_json).pack(fill=tk.X, pady=2)
    ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=10)
    ttk.Label(button_frame, text='Quick Operations:', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
    ttk.Button(button_frame, text='➕ Add Node', command=self._add_node_quick).pack(fill=tk.X, pady=2)
    ttk.Button(button_frame, text='🔗 Add Edge', command=self._add_edge_quick).pack(fill=tk.X, pady=2)
    ttk.Button(button_frame, text='📄 Template', command=self._insert_template).pack(fill=tk.X, pady=2)
    text_frame = ttk.Frame(main_frame)
    text_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)
    self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=60, height=30, font=('Consolas', 10))
    self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    self.text_area.insert(tk.END, json.dumps(self.json_data, indent=2, ensure_ascii=False))
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
    ttk.Button(bottom_frame, text='💾 Save and Close', command=self._save_and_close).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(bottom_frame, text='❌ Cancel', command=self._cancel).pack(side=tk.LEFT, padx=(0, 5))
    self.status_label = ttk.Label(bottom_frame, text='Ready', foreground='green')
    self.status_label.pack(side=tk.RIGHT)
    self.root.mainloop()
    return self.result

def _format_json(self):
    """format the json"""
    try:
        text = self.text_area.get(1.0, tk.END)
        data = json.loads(text)
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, formatted)
        self.status_label.config(text='✅ Formatting completed', foreground='green')
    except json.JSONDecodeError as e:
        self.status_label.config(text=f'❌ JSON format error: {e}', foreground='red')

def _validate_json(self):
    """validate the json"""
    try:
        text = self.text_area.get(1.0, tk.END)
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError('The root node must be a dictionary')
        if 'nodes' not in data or not isinstance(data['nodes'], list):
            raise ValueError('Must contain nodes array')
        node_names = set()
        for node in data['nodes']:
            if not isinstance(node, dict) or 'name' not in node:
                raise ValueError('Each node must contain name field')
            name = node['name']
            if name in node_names:
                raise ValueError(f'Node name duplicate: {name}')
            node_names.add(name)
        if 'edges' in data:
            for edge in data['edges']:
                if not isinstance(edge, dict):
                    continue
                source = edge.get('source')
                target = edge.get('target')
                if source and source not in node_names:
                    raise ValueError(f'The source node of the edge does not exist: {source}')
                if target and target not in node_names:
                    raise ValueError(f'The target node of the edge does not exist: {target}')
        self.status_label.config(text='✅ JSON structure is valid', foreground='green')
    except (json.JSONDecodeError, ValueError) as e:
        self.status_label.config(text=f'❌ Validation failed: {e}', foreground='red')

def _reset_json(self):
    """reset the json"""
    self.text_area.delete(1.0, tk.END)
    self.text_area.insert(tk.END, json.dumps(self.json_data, indent=2, ensure_ascii=False))
    self.status_label.config(text='🔄 Reset', foreground='blue')

def _copy_json(self):
    """copy the json to the clipboard"""
    try:
        text = self.text_area.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_label.config(text='📋 Copied to clipboard', foreground='blue')
    except Exception as e:
        self.status_label.config(text=f'❌ Copy failed: {e}', foreground='red')

def _add_node_quick(self):
    """quick add node"""
    try:
        import tkinter.simpledialog as sd
        name = sd.askstring('Add Node', 'Node name:')
        if not name:
            return
        desc = sd.askstring('Add Node', 'Node description:')
        if not desc:
            desc = f'The description of the node {name}'
        node_template = {'class_name': 'WorkFlowNode', 'name': name, 'description': desc, 'inputs': [], 'outputs': [], 'agents': [], 'status': 'pending'}
        current_text = self.text_area.get(1.0, tk.END)
        try:
            data = json.loads(current_text)
            data.setdefault('nodes', []).append(node_template)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            self.status_label.config(text=f'✅ Added node: {name}', foreground='green')
        except json.JSONDecodeError:
            self.status_label.config(text='❌ Current JSON format error, cannot add node', foreground='red')
    except ImportError:
        self.status_label.config(text='❌ Cannot use dialog', foreground='red')

def _add_edge_quick(self):
    """quick add edge"""
    try:
        import tkinter.simpledialog as sd
        current_text = self.text_area.get(1.0, tk.END)
        try:
            data = json.loads(current_text)
            nodes = data.get('nodes', [])
            node_names = [node.get('name') for node in nodes if node.get('name')]
            if len(node_names) < 2:
                self.status_label.config(text='❌ At least 2 nodes are required to add edge', foreground='red')
                return
            source = sd.askstring('Add Edge', f'Source node (optional: {', '.join(node_names)}):')
            if not source or source not in node_names:
                self.status_label.config(text='❌ Source node invalid', foreground='red')
                return
            target = sd.askstring('Add Edge', f'Target node (optional: {', '.join(node_names)}):')
            if not target or target not in node_names:
                self.status_label.config(text='❌ Target node invalid', foreground='red')
                return
            edge_template = {'class_name': 'WorkFlowEdge', 'source': source, 'target': target, 'priority': 0}
            data.setdefault('edges', []).append(edge_template)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            self.status_label.config(text=f'✅ Added edge: {source} -> {target}', foreground='green')
        except json.JSONDecodeError:
            self.status_label.config(text='❌ Current JSON format error, cannot add edge', foreground='red')
    except ImportError:
        self.status_label.config(text='❌ Cannot use dialog', foreground='red')

def _insert_template(self):
    """insert template"""
    templates = {'Simple Node': {'class_name': 'WorkFlowNode', 'name': 'new_node', 'description': 'New node description', 'inputs': [{'class_name': 'Parameter', 'name': 'input1', 'type': 'string', 'description': 'Input parameter', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'output1', 'type': 'string', 'description': 'Output parameter', 'required': True}], 'agents': [], 'status': 'pending'}, 'CustomizeAgent': {'name': 'my_agent', 'description': 'Customize Agent', 'inputs': [{'name': 'input1', 'type': 'string', 'description': 'Input', 'required': True}], 'outputs': [{'name': 'output1', 'type': 'string', 'description': 'Output', 'required': True}], 'prompt': 'Process input: {input1}', 'parse_mode': 'str'}}
    template_window = tk.Toplevel(self.root)
    template_window.title('Select Template')
    template_window.geometry('400x300')
    ttk.Label(template_window, text='Select the template to insert:').pack(pady=10)
    template_listbox = tk.Listbox(template_window)
    template_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for template_name in templates.keys():
        template_listbox.insert(tk.END, template_name)

    def insert_selected():
        selection = template_listbox.curselection()
        if selection:
            template_name = template_listbox.get(selection[0])
            template_json = json.dumps(templates[template_name], indent=2, ensure_ascii=False)
            self.text_area.insert(tk.INSERT, f'\n{template_json}\n')
            self.status_label.config(text=f'✅ Inserted template: {template_name}', foreground='green')
            template_window.destroy()
    ttk.Button(template_window, text='Insert', command=insert_selected).pack(pady=10)
    ttk.Button(template_window, text='Cancel', command=template_window.destroy).pack()

def insert_selected():
    selection = template_listbox.curselection()
    if selection:
        template_name = template_listbox.get(selection[0])
        template_json = json.dumps(templates[template_name], indent=2, ensure_ascii=False)
        self.text_area.insert(tk.INSERT, f'\n{template_json}\n')
        self.status_label.config(text=f'✅ Inserted template: {template_name}', foreground='green')
        template_window.destroy()

def _save_and_close(self):
    """save and close"""
    try:
        text = self.text_area.get(1.0, tk.END)
        self.result = json.loads(text)
        self.root.destroy()
    except json.JSONDecodeError as e:
        self.status_label.config(text=f'❌ JSON format error: {e}', foreground='red')

def _cancel(self):
    """cancel"""
    self.result = None
    self.root.destroy()

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

def is_loop_end(self, node: Union[str, WorkFlowNode]) -> bool:
    if len(self._loops) == 0:
        return False
    loop_end_nodes = set()
    node_name = node if isinstance(node, str) else node.name
    for loops in self._loops.values():
        loop_end_nodes.update([loop[-1] for loop in loops])
    return node_name in loop_end_nodes

class PyObjectId(ObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')

@classmethod
def __modify_schema__(cls, field_schema):
    field_schema.update(type='string')

class FaissDatabase(BaseModule):
    """
    A high-level interface for FAISS vector database operations.
    
    This class wraps the RAGEngine and StorageHandler to provide a unified interface
    for vector database operations including document ingestion, semantic search,
    and corpus management.
    
    Attributes:
        rag_engine (RAGEngine): The RAG engine for document processing and retrieval
        storage_handler (StorageHandler): The storage handler for persistence
        default_corpus_id (str): Default corpus ID for operations
        default_index_type (str): Default index type for vector operations
    """

    def __init__(self, storage_config: StoreConfig, rag_config: RAGConfig, default_corpus_id: str='default', default_index_type: str='vector', storage_handler: StorageHandler=None, file_handler: FileStorageHandler=None, **kwargs):
        """
        Initialize the FAISS database.
        
        Args:
            storage_config (StoreConfig): Configuration for storage backends
            rag_config (RAGConfig): Configuration for RAG pipeline
            default_corpus_id (str): Default corpus ID for operations
            default_index_type (str): Default index type for vector operations
            storage_handler (StorageHandler, optional): Storage handler for file operations
            **kwargs: Additional arguments for BaseModule
        """
        super().__init__(**kwargs)
        self.storage_handler = StorageHandler(storageConfig=storage_config)
        self.rag_engine = RAGEngine(config=rag_config, storage_handler=self.storage_handler)
        if storage_handler is None:
            storage_handler = LocalStorageHandler(base_path='./workplace/storage')
        self.file_storage_handler = storage_handler
        self.default_corpus_id = default_corpus_id
        self.default_index_type = default_index_type
        logger.info(f'Initialized FAISS database with corpus_id: {default_corpus_id}')

    def query(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Query the vector database with semantic search.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
        try:
            try:
                asyncio.get_running_loop()
                logger.info('Detected running event loop, using thread executor for query')
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._query_sync, query, corpus_id, top_k, similarity_threshold, metadata_filters)
                    return future.result()
            except RuntimeError:
                logger.info('No event loop detected, using direct query processing')
                return self._query_sync(query, corpus_id, top_k, similarity_threshold, metadata_filters)
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _query_sync(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Synchronous version of query that can be safely called from a thread.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            if corpus_id not in self.rag_engine.indices:
                logger.warning(f'Corpus {corpus_id} not found. Returning empty results.')
                return {'success': True, 'data': {'query': query, 'corpus_id': corpus_id, 'total_results': 0, 'results': []}}
            query_obj = Query(query_str=query, top_k=top_k, similarity_cutoff=similarity_threshold, metadata_filters=metadata_filters)
            results = self.rag_engine.query(query_obj, corpus_id=corpus_id)
            if not results or not results.corpus:
                logger.warning(f'Query returned no results for corpus {corpus_id}')
                return {'success': True, 'data': {'query': query, 'corpus_id': corpus_id, 'total_results': 0, 'results': []}}
            chunks = results.corpus.chunks if results.corpus.chunks else []
            formatted_results = {'query': query, 'corpus_id': corpus_id, 'total_results': len(chunks), 'results': []}
            for i, chunk in enumerate(chunks):
                score = results.scores[i] if results.scores and i < len(results.scores) else 0.0
                formatted_results['results'].append({'chunk_id': chunk.chunk_id, 'content': chunk.text, 'score': score, 'metadata': chunk.metadata.model_dump() if chunk.metadata else {}, 'doc_id': chunk.metadata.doc_id if chunk.metadata else None})
            logger.info(f'Query executed successfully. Found {len(formatted_results['results'])} results.')
            return {'success': True, 'data': formatted_results}
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _is_file_path(self, text: str) -> bool:
        """
        Check if a string appears to be a file path.
        
        Args:
            text (str): The string to check
            
        Returns:
            bool: True if the string looks like a file path
        """
        path_indicators = ['/', '\\', '.txt', '.pdf', '.md', '.doc', '.docx', '.csv', '.json', '.xml', '.html', '.htm']
        return any((indicator in text for indicator in path_indicators)) and os.path.exists(text)

    def _process_file_path(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
        """
        Process a file path and return Document objects.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
        try:
            try:
                asyncio.get_running_loop()
                logger.info(f'Detected running event loop, using thread executor for {file_path}')
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._process_file_path_sync, file_path, doc_index, metadata)
                    return future.result()
            except RuntimeError:
                logger.info(f'No event loop detected, using direct processing for {file_path}')
                return self._process_file_path_sync(file_path, doc_index, metadata)
        except Exception as e:
            logger.error(f'Failed to process file {file_path}: {str(e)}')
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
            document_metadata = DocumentMetadata(**doc_metadata)
            return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

    def _process_file_path_sync(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
        """
        Synchronous version of file processing that can be safely called from a thread.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
        try:
            if self.file_storage_handler:
                result = self.file_storage_handler.read(file_path)
                if result['success']:
                    file_content = result['content']
                else:
                    raise Exception(f'Failed to read file: {result.get('error', 'Unknown error')}')
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            temp_corpus_id = f'temp_file_{uuid4().hex[:8]}'
            temp_doc = Document(text=file_content, metadata=DocumentMetadata(source_file=file_path, doc_index=doc_index, insertion_time=datetime.now().isoformat()), doc_id=str(uuid4()))
            corpus = self.rag_engine.process_documents([temp_doc], corpus_id=temp_corpus_id)
            documents = []
            for chunk in corpus.chunks:
                doc_metadata = metadata.copy() if metadata else {}
                doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'original_chunk_id': chunk.chunk_id})
                document_metadata = DocumentMetadata(**doc_metadata)
                documents.append(Document(text=chunk.text, metadata=document_metadata, doc_id=chunk.chunk_id))
            self.rag_engine.clear(corpus_id=temp_corpus_id)
            logger.info(f'Processed file {file_path} into {len(documents)} chunks')
            return documents
        except Exception as e:
            logger.error(f'Failed to process file {file_path} in sync mode: {str(e)}')
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
            document_metadata = DocumentMetadata(**doc_metadata)
            return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

    def insert(self, documents: list, corpus_id: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, batch_size: int=100) -> Dict[str, Any]:
        """
        Insert documents into the vector database.
        
        Args:
            documents (Union[List[str], List[Dict[str, Any]]]): Documents to insert. 
                Strings can be either text content or file paths (if they look like paths and exist)
            corpus_id (str, optional): Corpus ID to insert into
            metadata (Dict[str, Any], optional): Additional metadata for all documents
            batch_size (int): Batch size for processing
            
        Returns:
            Dict[str, Any]: Insertion results
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            processed_docs = []
            file_paths_processed = []
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    if self._is_file_path(doc):
                        logger.info(f'Detected file path: {doc}')
                        file_docs = self._process_file_path(doc, i, metadata)
                        processed_docs.extend(file_docs)
                        file_paths_processed.append(doc)
                    else:
                        doc_metadata = metadata.copy() if metadata else {}
                        doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                        document_metadata = DocumentMetadata(**doc_metadata)
                        processed_docs.append(Document(text=doc, metadata=document_metadata, doc_id=str(uuid4())))
                elif isinstance(doc, dict):
                    doc_metadata = metadata.copy() if metadata else {}
                    doc_metadata.update(doc.get('metadata', {}))
                    doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                    document_metadata = DocumentMetadata(**doc_metadata)
                    processed_docs.append(Document(text=doc.get('text', ''), metadata=document_metadata, doc_id=doc.get('doc_id', str(uuid4()))))
            corpus = Corpus(corpus_id=corpus_id)
            total_processed = 0
            for i in range(0, len(processed_docs), batch_size):
                batch = processed_docs[i:i + batch_size]
                batch_corpus = self.rag_engine.chunker.chunk(batch)
                batch_corpus.corpus_id = corpus_id
                self.rag_engine.add(self.default_index_type, batch_corpus, corpus_id=corpus_id)
                corpus.chunks.extend(batch_corpus.chunks)
                total_processed += len(batch)
                logger.info(f'Processed batch {i // batch_size + 1}, total processed: {total_processed}')
            self.rag_engine.save(corpus_id=corpus_id, index_type=self.default_index_type)
            result = {'corpus_id': corpus_id, 'documents_inserted': len(documents), 'chunks_created': len(corpus.chunks), 'total_processed': total_processed, 'file_paths_processed': file_paths_processed}
            logger.info(f'Successfully inserted {len(documents)} documents into corpus {corpus_id}')
            if file_paths_processed:
                logger.info(f'Processed {len(file_paths_processed)} file paths: {file_paths_processed}')
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f'Insert failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def delete(self, corpus_id: Optional[str]=None, doc_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None, clear_all: bool=False) -> Dict[str, Any]:
        """
        Delete documents or chunks from the vector database.
        
        Args:
            corpus_id (str, optional): Corpus ID to delete from
            doc_ids (List[str], optional): Document IDs to delete
            metadata_filters (Dict[str, Any], optional): Metadata filters for deletion
            clear_all (bool): Whether to clear the entire corpus
            
        Returns:
            Dict[str, Any]: Deletion results
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            if clear_all:
                self.rag_engine.clear(corpus_id=corpus_id)
                logger.info(f'Cleared entire corpus: {corpus_id}')
                return {'success': True, 'data': {'operation': 'clear_all', 'corpus_id': corpus_id}}
            if corpus_id not in self.rag_engine.indices:
                logger.warning(f'Corpus {corpus_id} not found. Nothing to delete.')
                return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'Corpus not found, nothing to delete'}}
            if doc_ids or metadata_filters:
                self.rag_engine.delete(corpus_id=corpus_id, index_type=self.default_index_type, node_ids=doc_ids, metadata_filters=metadata_filters)
                result = {'corpus_id': corpus_id, 'operation': 'selective_delete', 'doc_ids': doc_ids, 'metadata_filters': metadata_filters}
                logger.info(f'Successfully deleted from corpus {corpus_id}')
                return {'success': True, 'data': result}
            else:
                logger.warning(f'No deletion criteria provided for corpus {corpus_id}')
                return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'No deletion criteria provided'}}
        except Exception as e:
            logger.error(f'Delete failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def list_corpora(self) -> Dict[str, Any]:
        """
        List all available corpora and their metadata.
        
        Returns:
            Dict[str, Any]: List of corpora with metadata
        """
        try:
            corpora = []
            for corpus_id, indices in self.rag_engine.indices.items():
                corpus_info = {'corpus_id': corpus_id, 'index_types': list(indices.keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
                corpora.append(corpus_info)
            return {'success': True, 'data': {'corpora': corpora, 'total': len(corpora)}}
        except Exception as e:
            logger.error(f'List corpora failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def get_stats(self, corpus_id: Optional[str]=None) -> Dict[str, Any]:
        """
        Get statistics about the database or a specific corpus.
        
        Args:
            corpus_id (str, optional): Corpus ID to get stats for
            
        Returns:
            Dict[str, Any]: Database statistics
        """
        try:
            if corpus_id:
                corpus_id = corpus_id or self.default_corpus_id
                stats = {'corpus_id': corpus_id, 'exists': corpus_id in self.rag_engine.indices, 'index_types': list(self.rag_engine.indices.get(corpus_id, {}).keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
                if corpus_id in self.rag_engine.indices:
                    vector_index = self.rag_engine.indices[corpus_id].get(self.default_index_type)
                    if vector_index and hasattr(vector_index, 'get_index'):
                        try:
                            index = vector_index.get_index()
                            if hasattr(index, 'vector_store'):
                                vector_store = index.vector_store
                                if hasattr(vector_store, 'faiss_index'):
                                    stats['vector_count'] = vector_store.faiss_index.ntotal
                                    stats['dimensions'] = vector_store.faiss_index.d
                        except Exception:
                            pass
                return {'success': True, 'data': stats}
            else:
                stats = {'total_corpora': len(self.rag_engine.indices), 'corpora': list(self.rag_engine.indices.keys()), 'embedding_model': self.rag_engine.config.embedding.model_name, 'vector_store_type': self.rag_engine.storage_handler.storageConfig.vectorConfig.vector_name if self.rag_engine.storage_handler.storageConfig.vectorConfig else None}
                return {'success': True, 'data': stats}
        except Exception as e:
            logger.error(f'Get stats failed: {str(e)}')
            return {'success': False, 'error': str(e)}

def delete(self, corpus_id: Optional[str]=None, doc_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None, clear_all: bool=False) -> Dict[str, Any]:
    """
        Delete documents or chunks from the vector database.
        
        Args:
            corpus_id (str, optional): Corpus ID to delete from
            doc_ids (List[str], optional): Document IDs to delete
            metadata_filters (Dict[str, Any], optional): Metadata filters for deletion
            clear_all (bool): Whether to clear the entire corpus
            
        Returns:
            Dict[str, Any]: Deletion results
        """
    try:
        corpus_id = corpus_id or self.default_corpus_id
        if clear_all:
            self.rag_engine.clear(corpus_id=corpus_id)
            logger.info(f'Cleared entire corpus: {corpus_id}')
            return {'success': True, 'data': {'operation': 'clear_all', 'corpus_id': corpus_id}}
        if corpus_id not in self.rag_engine.indices:
            logger.warning(f'Corpus {corpus_id} not found. Nothing to delete.')
            return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'Corpus not found, nothing to delete'}}
        if doc_ids or metadata_filters:
            self.rag_engine.delete(corpus_id=corpus_id, index_type=self.default_index_type, node_ids=doc_ids, metadata_filters=metadata_filters)
            result = {'corpus_id': corpus_id, 'operation': 'selective_delete', 'doc_ids': doc_ids, 'metadata_filters': metadata_filters}
            logger.info(f'Successfully deleted from corpus {corpus_id}')
            return {'success': True, 'data': result}
        else:
            logger.warning(f'No deletion criteria provided for corpus {corpus_id}')
            return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'No deletion criteria provided'}}
    except Exception as e:
        logger.error(f'Delete failed: {str(e)}')
        return {'success': False, 'error': str(e)}

class FaissInsertTool(Tool):
    """Tool for inserting documents into the FAISS vector database."""
    name: str = 'faiss_insert'
    description: str = 'Insert documents into the FAISS vector database with automatic chunking and embedding. Supports both text content and file paths - if a string looks like a file path and exists, it will automatically read and process the file content.'
    inputs: Dict[str, Dict[str, Any]] = {'documents': {'type': 'array', 'description': "Array of documents to insert. Can be strings (text content or file paths), or objects with 'text', 'metadata', and 'doc_id' fields. If a string contains path separators or file extensions and the file exists, it will be treated as a file path and its content will be read and processed."}, 'corpus_id': {'type': 'string', 'description': 'Optional corpus ID to insert into. If not provided, uses default corpus'}, 'metadata': {'type': 'object', 'description': "Optional metadata to add to all documents (e.g., {'source': 'file1.txt', 'category': 'research'})"}, 'batch_size': {'type': 'integer', 'description': 'Batch size for processing documents (default: 100)', 'default': 100}}
    required: Optional[List[str]] = ['documents']

    def __init__(self, faiss_database: FaissDatabase=None):
        super().__init__()
        self.faiss_database = faiss_database

    def __call__(self, documents: list, corpus_id: str=None, metadata: dict=None, batch_size: int=100) -> Dict[str, Any]:
        """Execute the insert operation."""
        return self.faiss_database.insert(documents=documents, corpus_id=corpus_id, metadata=metadata, batch_size=batch_size)

def __call__(self, documents: list, corpus_id: str=None, metadata: dict=None, batch_size: int=100) -> Dict[str, Any]:
    """Execute the insert operation."""
    return self.faiss_database.insert(documents=documents, corpus_id=corpus_id, metadata=metadata, batch_size=batch_size)

class FaissDeleteTool(Tool):
    """Tool for deleting documents from the FAISS vector database."""
    name: str = 'faiss_delete'
    description: str = 'Delete documents or chunks from the FAISS vector database. You can delete specific documents by ID, filter by metadata, or clear the entire corpus.'
    inputs: Dict[str, Dict[str, Any]] = {'corpus_id': {'type': 'string', 'description': 'Optional corpus ID to delete from. If not provided, uses default corpus'}, 'doc_ids': {'type': 'array', 'description': 'Optional list of document IDs to delete. Use this to delete specific documents', 'items': {'type': 'string'}}, 'metadata_filters': {'type': 'object', 'description': "Optional metadata filters to select documents for deletion (e.g., {'source': 'file1.txt'})"}, 'clear_all': {'type': 'boolean', 'description': 'Set to true to clear the entire corpus. WARNING: This will delete all documents in the corpus', 'default': False}}
    required: Optional[List[str]] = []

    def __init__(self, faiss_database: FaissDatabase=None):
        super().__init__()
        self.faiss_database = faiss_database

    def __call__(self, corpus_id: str=None, doc_ids: list=None, metadata_filters: dict=None, clear_all: bool=False) -> Dict[str, Any]:
        """Execute the delete operation."""
        return self.faiss_database.delete(corpus_id=corpus_id, doc_ids=doc_ids, metadata_filters=metadata_filters, clear_all=clear_all)

def __call__(self, corpus_id: str=None, doc_ids: list=None, metadata_filters: dict=None, clear_all: bool=False) -> Dict[str, Any]:
    """Execute the delete operation."""
    return self.faiss_database.delete(corpus_id=corpus_id, doc_ids=doc_ids, metadata_filters=metadata_filters, clear_all=clear_all)

class RapidAPIConverter(OpenAPIConverter):
    """
    RapidAPI-specific converter
    Inherits from OpenAPIConverter and adds RapidAPI-specific authentication and configuration
    """

    def __init__(self, input_schema: Union[str, Dict[str, Any]], description: str='', rapidapi_key: str='', rapidapi_host: str='', **kwargs):
        """
        Initialize the RapidAPI converter
        
        Args:
            input_schema: API specification
            description: Service description
            rapidapi_key: RapidAPI key
            rapidapi_host: RapidAPI host
        """
        if not rapidapi_key:
            from os import getenv
            from dotenv import load_dotenv
            load_dotenv()
            rapidapi_key = getenv('RAPIDAPI_KEY', '')
            if not rapidapi_key:
                raise ValueError('rapidapi_key not provided or RAPIDAPI_KEY environment variable not set')
        if not rapidapi_host:
            raise ValueError('rapidapi_host not provided or RAPIDAPI_HOST environment variable not set')
        auth_config = {'api_key': rapidapi_key, 'key_name': 'X-RapidAPI-Key', 'rapidapi_host': rapidapi_host}
        super().__init__(input_schema=input_schema, description=description, auth_config=auth_config, **kwargs)

    def convert_to_toolkit(self) -> APIToolkit:
        """Convert to a RapidAPI toolkit"""
        toolkit = super().convert_to_toolkit()
        rapidapi_headers = {'X-RapidAPI-Key': self.auth_config.get('api_key', ''), 'X-RapidAPI-Host': self.auth_config.get('rapidapi_host', '')}
        toolkit.common_headers.update(rapidapi_headers)
        return toolkit

    def _create_api_function(self, endpoint_config: Dict[str, Any]) -> Callable:
        """Create RapidAPI execution function"""
        url = endpoint_config['url']
        method = endpoint_config['method']
        operation = endpoint_config['operation']

        def rapidapi_call(**kwargs):
            path_params = {}
            query_params = {}
            body_data = {}
            parameters = operation.get('parameters', [])
            param_locations = {param['name']: param.get('in', 'query') for param in parameters}
            for key, value in kwargs.items():
                if value is None:
                    continue
                location = param_locations.get(key, 'body')
                if location == 'path':
                    path_params[key] = value
                elif location == 'query':
                    query_params[key] = value
                else:
                    body_data[key] = value
            final_url = url
            for param_name, param_value in path_params.items():
                final_url = final_url.replace(f'{{{param_name}}}', str(param_value))
            headers = {'Content-Type': 'application/json', 'X-RapidAPI-Key': self.auth_config.get('api_key', ''), 'X-RapidAPI-Host': self.auth_config.get('rapidapi_host', '')}
            try:
                if method in ['GET', 'DELETE']:
                    response = requests.request(method=method, url=final_url, params=query_params, headers=headers, timeout=30)
                else:
                    response = requests.request(method=method, url=final_url, params=query_params, json=body_data if body_data else None, headers=headers, timeout=30)
                response.raise_for_status()
                try:
                    return response.json()
                except (ValueError, json.JSONDecodeError):
                    return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f'RapidAPI request failed: {e}')
                raise
        rapidapi_call.__name__ = f'rapidapi_call_{method.lower()}'
        return rapidapi_call

def convert_to_toolkit(self) -> APIToolkit:
    """Convert to a RapidAPI toolkit"""
    toolkit = super().convert_to_toolkit()
    rapidapi_headers = {'X-RapidAPI-Key': self.auth_config.get('api_key', ''), 'X-RapidAPI-Host': self.auth_config.get('rapidapi_host', '')}
    toolkit.common_headers.update(rapidapi_headers)
    return toolkit

def create_openapi_toolkit(schema_path_or_dict: Union[str, Dict[str, Any]], service_name: str=None, auth_config: Dict[str, Any]=None) -> APIToolkit:
    """
    Convenience function: create an APIToolkit from an OpenAPI specification
    
    Args:
        schema_path_or_dict: OpenAPI specification file path or dictionary
        service_name: Service name (optional, will be extracted from the spec)
        auth_config: Authentication configuration
    
    Returns:
        APIToolkit: Created toolkit
    """
    converter = OpenAPIConverter(input_schema=schema_path_or_dict, description=service_name or '', auth_config=auth_config)
    return converter.convert_to_toolkit()

def create_rapidapi_toolkit(schema_path_or_dict: Union[str, Dict[str, Any]], rapidapi_key: str, rapidapi_host: str, service_name: str=None) -> APIToolkit:
    """
    Convenience function: create a RapidAPI toolkit
    
    Args:
        schema_path_or_dict: API specification file path or dictionary
        rapidapi_key: RapidAPI key
        rapidapi_host: RapidAPI host
        service_name: Service name (optional)
    
    Returns:
        APIToolkit: Created RapidAPI toolkit
    """
    converter = RapidAPIConverter(input_schema=schema_path_or_dict, description=service_name or '', rapidapi_key=rapidapi_key, rapidapi_host=rapidapi_host)
    return converter.convert_to_toolkit()

class PostgreSQLDatabase(DatabaseBase):
    """
    PostgreSQL database implementation with automatic initialization.
    Handles remote connections, existing local databases, and new local database creation.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, **kwargs):
        init_params = {'connection_string': connection_string, 'database_name': database_name}
        super().__init__(**init_params, **kwargs)
        self.local_path = Path(local_path) if local_path else None
        self.auto_save = auto_save
        self.connection_params = kwargs
        self.is_local_database = False
        self.conn = None
        self.cursor = None
        self.file_based_mode = False
        self.tables = {}
        if self._is_remote_connection():
            self._init_remote_database()
        elif self._is_existing_local_database():
            self._init_existing_local_database()
        else:
            self._init_new_local_database()

    def _is_remote_connection(self) -> bool:
        return self.connection_string and ('@' in self.connection_string or 'postgresql://' in self.connection_string)

    def _is_existing_local_database(self) -> bool:
        if not self.local_path:
            return False
        if not self.local_path.exists():
            return False
        db_info_file = self.local_path / 'db_info.json'
        return db_info_file.exists()

    def _init_remote_database(self):
        """Initialize remote PostgreSQL connection"""
        try:
            connection_params = self.connection_params.copy()
            connection_params.update({'connect_timeout': 5, 'options': '-c statement_timeout=5000'})
            self.conn = psycopg2.connect(self.connection_string, **connection_params)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if self.database_name:
                self.conn.set_isolation_level(0)
                self.cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (self.database_name,))
            self._is_initialized = True
            self.is_local_database = False
            self.file_based_mode = False
            logger.info(f'Connected to remote PostgreSQL: {self.database_name}')
        except Exception as e:
            logger.error(f'Failed to connect to remote PostgreSQL: {str(e)}')
            self._is_initialized = False
            logger.info('Falling back to local database mode')

    def _init_existing_local_database(self):
        """Initialize existing local file-based database"""
        try:
            if not self.database_name:
                self.database_name = self.local_path.name
            self._load_tables_from_files()
            self._is_initialized = True
            self.is_local_database = True
            self.file_based_mode = True
            logger.info(f'Loaded existing local file-based database from: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to load existing local database: {str(e)}')
            self._is_initialized = False
            logger.info('Falling back to new local database mode')
            self._init_new_local_database()

    def _init_new_local_database(self):
        """Initialize new local file-based database"""
        try:
            if not self.local_path:
                self.local_path = Path('./workplace/postgresql_local')
            self.local_path.mkdir(parents=True, exist_ok=True)
            if not self.database_name:
                self.database_name = self.local_path.name
            self._create_db_info_file()
            self._is_initialized = True
            self.is_local_database = True
            self.file_based_mode = True
            logger.info(f'Created new local file-based database at: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to create new local database: {str(e)}')
            self._is_initialized = False
            logger.info('Database initialization failed, but toolkit is still usable')

    def _create_db_info_file(self):
        """Create database info file"""
        try:
            db_info = {'database_name': self.database_name, 'created_at': time.time(), 'local_path': str(self.local_path.absolute()), 'auto_save': self.auto_save, 'version': '1.0', 'mode': 'file_based'}
            info_file = self.local_path / 'db_info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f'Failed to create db info file: {str(e)}')

    def _load_tables_from_files(self):
        """Load tables from JSON files"""
        try:
            for json_file in self.local_path.glob('*.json'):
                if json_file.name == 'db_info.json':
                    continue
                table_name = json_file.stem
                with open(json_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if not isinstance(loaded_data, list):
                        logger.warning(f'Table {table_name} file contains non-list data: {type(loaded_data)}, converting to empty list')
                        self.tables[table_name] = []
                    else:
                        self.tables[table_name] = loaded_data
        except Exception as e:
            logger.warning(f'Error loading tables from files: {str(e)}')

    def _save_table_to_file(self, table_name: str):
        """Save table data to JSON file"""
        try:
            if table_name in self.tables:
                table_file = self.local_path / f'{table_name}.json'
                with open(table_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tables[table_name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f'Error saving table {table_name}: {str(e)}')

    def _parse_sql_query(self, sql: str) -> Dict[str, Any]:
        """Enhanced SQL parser for file-based mode - now supports JOINs and complex queries"""
        sql = sql.strip()
        upper_sql = sql.upper()
        if upper_sql.startswith('CREATE TABLE'):
            match = re.search('CREATE TABLE (?:IF NOT EXISTS )?(\\w+) *\\((.*?)\\)', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                columns = match.group(2)
                col_defs = [c.strip() for c in columns.split(',') if c.strip()]
                col_names = [c.split()[0] for c in col_defs]
                return {'type': 'CREATE', 'table': table, 'columns': col_names}
        elif upper_sql.startswith('INSERT'):
            match = re.search('INSERT INTO (\\w+) *\\((.*?)\\) *VALUES', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                columns = [c.strip() for c in match.group(2).split(',')]
                values_match = re.search('VALUES\\s*(.*)', sql, re.IGNORECASE | re.DOTALL)
                if values_match:
                    values_str = values_match.group(1)
                    value_groups = re.findall('\\(([^)]+)\\)', values_str)
                    all_values = []
                    for group in value_groups:
                        values = [v.strip().strip('\'"') for v in group.split(',')]
                        all_values.append(values)
                    return {'type': 'INSERT', 'table': table, 'columns': columns, 'values': all_values}
        elif upper_sql.startswith('SELECT'):
            if 'JOIN' in upper_sql:
                match = re.search('SELECT (.*?) FROM (\\w+)(?:\\s+(\\w+))?\\s+(?:(\\w+)\\s+)?JOIN\\s+(\\w+)(?:\\s+(\\w+))?\\s+ON\\s+(.*?)(?: WHERE (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    columns = [c.strip() for c in match.group(1).split(',')]
                    table1 = match.group(2).lower()
                    alias1 = match.group(3)
                    join_type = match.group(4) or 'INNER'
                    table2 = match.group(5).lower()
                    alias2 = match.group(6)
                    join_condition = match.group(7)
                    where = match.group(8)
                    order_by = match.group(9)
                    limit = match.group(10)
                    return {'type': 'SELECT_JOIN', 'columns': columns, 'table1': table1, 'alias1': alias1, 'join_type': join_type, 'table2': table2, 'alias2': alias2, 'join_condition': join_condition, 'where': where, 'order_by': order_by, 'limit': limit}
                elif 'CROSS JOIN' in upper_sql:
                    match = re.search('SELECT (.*?) FROM (\\w+)(?:\\s+(\\w+))?\\s+CROSS\\s+JOIN\\s+(\\w+)(?:\\s+(\\w+))?(?: WHERE (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                    if match:
                        columns = [c.strip() for c in match.group(1).split(',')]
                        table1 = match.group(2).lower()
                        alias1 = match.group(3)
                        table2 = match.group(4).lower()
                        alias2 = match.group(5)
                        where = match.group(6)
                        order_by = match.group(7)
                        limit = match.group(8)
                        return {'type': 'SELECT_CROSS_JOIN', 'columns': columns, 'table1': table1, 'alias1': alias1, 'table2': table2, 'alias2': alias2, 'where': where, 'order_by': order_by, 'limit': limit}
            else:
                match = re.search('SELECT (.*?) FROM (\\w+)(?: WHERE (.*?))?(?: GROUP BY (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    columns = [c.strip() for c in match.group(1).split(',')]
                    table = match.group(2).lower()
                    where = match.group(3)
                    group_by = match.group(4)
                    order_by = match.group(5)
                    limit = match.group(6)
                    return {'type': 'SELECT', 'table': table, 'columns': columns, 'where': where, 'group_by': group_by, 'order_by': order_by, 'limit': limit}
        elif upper_sql.startswith('UPDATE'):
            match = re.search('UPDATE (\\w+) SET (.*?)(?: WHERE (.*?))?$', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                set_clause = match.group(2)
                where = match.group(3)
                return {'type': 'UPDATE', 'table': table, 'set': set_clause, 'where': where}
        elif upper_sql.startswith('DELETE'):
            match = re.search('DELETE FROM (\\w+)(?: WHERE (.*?))?', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                where = match.group(2)
                return {'type': 'DELETE', 'table': table, 'where': where}
        return {'type': 'UNKNOWN'}

    def _apply_where_filter(self, rows: List[Dict], where: str) -> List[Dict]:
        """Apply WHERE filter to rows"""
        if not where:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_where_filter: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_where_filter: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
        if m:
            col, op, val = (m.group(1), m.group(2), m.group(3))
            if op == '=':
                return [r for r in valid_rows if str(r.get(col, '')) == val]
            elif op == '>':
                try:
                    val_num = int(val)
                    return [r for r in valid_rows if int(r.get(col, 0)) > val_num]
                except ValueError:
                    pass
            elif op == '<':
                try:
                    val_num = int(val)
                    return [r for r in valid_rows if int(r.get(col, 0)) < val_num]
                except ValueError:
                    pass
        return valid_rows

    def _apply_column_selection(self, rows: List[Dict], columns: List[str]) -> List[Dict]:
        """Apply column selection to rows"""
        if columns == ['*']:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_column_selection: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_column_selection: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        filtered_rows = []
        for row in valid_rows:
            filtered_row = {}
            for col in columns:
                if col in row:
                    filtered_row[col] = row[col]
            filtered_rows.append(filtered_row)
        return filtered_rows

    def _apply_group_by(self, rows: List[Dict], group_by: str) -> List[Dict]:
        """Apply GROUP BY aggregation to rows"""
        if not group_by:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_group_by: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_group_by: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        group_col = group_by.strip()
        groups = {}
        for row in valid_rows:
            group_val = row.get(group_col, 'Unknown')
            if group_val not in groups:
                groups[group_val] = []
            groups[group_val].append(row)
        result = []
        for group_val, group_rows in groups.items():
            group_result = {group_col: group_val}
            group_result['employee_count'] = len(group_rows)
            salaries = [float(r.get('salary', 0)) for r in group_rows if r.get('salary') is not None]
            group_result['avg_salary'] = sum(salaries) / len(salaries) if salaries else 0
            group_result['max_salary'] = max(salaries) if salaries else 0
            result.append(group_result)
        return result

    def _execute_join_query(self, parsed: Dict) -> Dict[str, Any]:
        """Execute JOIN query in file-based mode"""
        try:
            table1 = parsed['table1']
            table2 = parsed['table2']
            columns = parsed['columns']
            join_condition = parsed['join_condition']
            where = parsed.get('where')
            rows1 = self.tables.get(table1, [])
            rows2 = self.tables.get(table2, [])
            if not isinstance(rows1, list):
                logger.warning(f'Table {table1} contains non-list data: {type(rows1)}')
                rows1 = []
            if not isinstance(rows2, list):
                logger.warning(f'Table {table2} contains non-list data: {type(rows2)}')
                rows2 = []
            join_match = re.match('(\\w+)\\.(\\w+)\\s*=\\s*(\\w+)\\.(\\w+)', join_condition)
            if not join_match:
                return {'error': 'Invalid join condition format'}
            col1, col2 = (join_match.group(2), join_match.group(4))
            result_rows = []
            for row1 in rows1:
                if not isinstance(row1, dict):
                    logger.warning(f'Skipping non-dict row1 in JOIN: {type(row1)}')
                    continue
                for row2 in rows2:
                    if not isinstance(row2, dict):
                        logger.warning(f'Skipping non-dict row2 in JOIN: {type(row2)}')
                        continue
                    if str(row1.get(col1, '')) == str(row2.get(col2, '')):
                        combined_row = {}
                        for col in columns:
                            if '.' in col:
                                table_alias, col_name = col.split('.', 1)
                                if table_alias == parsed.get('alias1') or table_alias == table1:
                                    combined_row[col] = row1.get(col_name, '')
                                elif table_alias == parsed.get('alias2') or table_alias == table2:
                                    combined_row[col] = row2.get(col_name, '')
                            elif col in row1:
                                combined_row[col] = row1[col]
                            elif col in row2:
                                combined_row[col] = row2[col]
                        result_rows.append(combined_row)
            if where:
                result_rows = self._apply_where_filter(result_rows, where)
            return result_rows
        except Exception as e:
            logger.error(f'Error executing JOIN query: {str(e)}')
            return {'error': str(e)}

    def _execute_cross_join_query(self, parsed: Dict) -> Dict[str, Any]:
        """Execute CROSS JOIN query in file-based mode"""
        try:
            table1 = parsed['table1']
            table2 = parsed['table2']
            columns = parsed['columns']
            where = parsed.get('where')
            rows1 = self.tables.get(table1, [])
            rows2 = self.tables.get(table2, [])
            if not isinstance(rows1, list):
                logger.warning(f'Table {table1} contains non-list data: {type(rows1)}')
                rows1 = []
            if not isinstance(rows2, list):
                logger.warning(f'Table {table2} contains non-list data: {type(rows2)}')
                rows2 = []
            result_rows = []
            for row1 in rows1:
                if not isinstance(row1, dict):
                    logger.warning(f'Skipping non-dict row1 in CROSS JOIN: {type(row1)}')
                    continue
                for row2 in rows2:
                    if not isinstance(row2, dict):
                        logger.warning(f'Skipping non-dict row2 in CROSS JOIN: {type(row2)}')
                        continue
                    combined_row = {}
                    for col in columns:
                        if '.' in col:
                            table_alias, col_name = col.split('.', 1)
                            if table_alias == parsed.get('alias1') or table_alias == table1:
                                combined_row[col] = row1.get(col_name, '')
                            elif table_alias == parsed.get('alias2') or table_alias == table2:
                                combined_row[col] = row2.get(col_name, '')
                        elif col in row1:
                            combined_row[col] = row1[col]
                        elif col in row2:
                            combined_row[col] = row2[col]
                    result_rows.append(combined_row)
            if where:
                result_rows = self._apply_where_filter(result_rows, where)
            return result_rows
        except Exception as e:
            logger.error(f'Error executing CROSS JOIN query: {str(e)}')
            return {'error': str(e)}

    def _get_database_type(self) -> DatabaseType:
        return DatabaseType.POSTGRESQL

    def connect(self) -> bool:
        return self._is_initialized

    def disconnect(self) -> bool:
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.cursor = None
                self._is_initialized = False
                logger.info('Disconnected from PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting: {str(e)}')
            return False

    def test_connection(self) -> bool:
        if self.file_based_mode:
            return self._is_initialized
        try:
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute('SELECT 1;')
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        if not self._is_initialized:
            return self.format_error_result('Database not initialized')
        if self.file_based_mode:
            return self._execute_file_based_query(query, query_type)
        if self.conn is None:
            return self.format_error_result('PostgreSQL server not available')
        start_time = time.time()
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if isinstance(query, str):
                    cur.execute(query)
                elif isinstance(query, dict):
                    sql = query.get('sql')
                    params = query.get('params', None)
                    if params:
                        cur.execute(sql, params)
                    else:
                        cur.execute(sql)
                elif isinstance(query, list):
                    for q in query:
                        if isinstance(q, str):
                            cur.execute(q)
                        elif isinstance(q, dict):
                            sql = q.get('sql')
                            params = q.get('params', None)
                            if params:
                                cur.execute(sql, params)
                            else:
                                cur.execute(sql)
                else:
                    return self.format_error_result('Unsupported query format', query_type)
                if cur.description:
                    result = cur.fetchall()
                else:
                    result = {'rowcount': cur.rowcount}
                self.conn.commit()
            execution_time = time.time() - start_time
            return self.format_query_result(result, query_type or QueryType.SELECT, execution_time=execution_time)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing PostgreSQL query: {str(e)}')
            try:
                if self.conn:
                    self.conn.rollback()
            except Exception as rollback_error:
                logger.warning(f'Error during rollback: {str(rollback_error)}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def _execute_file_based_query(self, query: Union[str, Dict, List], query_type: QueryType=None) -> Dict[str, Any]:
        """Execute query in file-based mode"""
        start_time = time.time()
        try:
            if isinstance(query, str):
                parsed = self._parse_sql_query(query)
                query_type = query_type or QueryType.SELECT
                if not isinstance(parsed, dict) or 'type' not in parsed:
                    logger.error(f'_execute_file_based_query: parsed is not a valid dict: {parsed}')
                    return self.format_error_result(f'Failed to parse SQL query: {query}', query_type)
                logger.debug(f'Executing {parsed['type']} query: {parsed}')
                if parsed['type'] == 'CREATE':
                    table_name = parsed['table']
                    columns = parsed.get('columns', ['id'])
                    if table_name not in self.tables:
                        self.tables[table_name] = []
                    if not isinstance(self.tables[table_name], list):
                        logger.warning(f'Reinitializing table {table_name} as list (was {type(self.tables[table_name])})')
                        self.tables[table_name] = []
                    self.tables[f'__schema__{table_name}'] = columns
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': 0}
                elif parsed['type'] == 'INSERT':
                    table_name = parsed['table']
                    columns = parsed['columns']
                    all_values = parsed['values']
                    if table_name not in self.tables:
                        self.tables[table_name] = []
                    if not isinstance(self.tables[table_name], list):
                        logger.warning(f'Reinitializing table {table_name} as list (was {type(self.tables[table_name])})')
                        self.tables[table_name] = []
                    valid_rows = 0
                    for values in all_values:
                        if len(values) != len(columns):
                            logger.warning(f'Skipping invalid row: {values} (expected {len(columns)} values, got {len(values)})')
                            continue
                        if not isinstance(values, list):
                            logger.warning(f'Skipping non-list values: {type(values)}')
                            continue
                        row = {col: val for col, val in zip(columns, values)}
                        row['id'] = len(self.tables[table_name]) + 1
                        self.tables[table_name].append(row)
                        valid_rows += 1
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': valid_rows}
                elif parsed['type'] == 'SELECT':
                    table_name = parsed['table']
                    columns = parsed['columns']
                    where = parsed.get('where')
                    group_by = parsed.get('group_by')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    logger.debug(f'SELECT query: table={table_name}, columns={columns}, where={where}, group_by={group_by}')
                    logger.debug(f'Rows from table: {type(rows)}, length={(len(rows) if isinstance(rows, list) else 'N/A')}')
                    if isinstance(rows, list) and rows:
                        logger.debug(f'First row type: {type(rows[0])}, content: {rows[0]}')
                    if where:
                        rows = self._apply_where_filter(rows, where)
                    if group_by:
                        result = self._apply_group_by(rows, group_by)
                    else:
                        result = {'data': self._apply_column_selection(rows, columns)}
                elif parsed['type'] == 'SELECT_JOIN':
                    logger.debug(f'Executing JOIN query: {parsed}')
                    join_result = self._execute_join_query(parsed)
                    if isinstance(join_result, dict) and 'error' in join_result:
                        result = {'error': join_result['error']}
                    else:
                        result = {'data': join_result}
                elif parsed['type'] == 'SELECT_CROSS_JOIN':
                    logger.debug(f'Executing CROSS JOIN query: {parsed}')
                    cross_join_result = self._execute_cross_join_query(parsed)
                    if isinstance(cross_join_result, dict) and 'error' in cross_join_result:
                        result = {'error': cross_join_result['error']}
                    else:
                        result = {'data': cross_join_result}
                elif parsed['type'] == 'UPDATE':
                    table_name = parsed['table']
                    set_clause = parsed['set']
                    where = parsed.get('where')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    updates = dict(re.findall("(\\w+) *= *'?([\\w@.\\- ]+)'?", set_clause))
                    count = 0
                    for r in rows:
                        if not isinstance(r, dict):
                            logger.warning(f'Skipping non-dict row in UPDATE: {type(r)}')
                            continue
                        match = True
                        if where:
                            m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
                            if m:
                                col, op, val = (m.group(1), m.group(2), m.group(3))
                                if op == '=' and str(r.get(col, '')) != val:
                                    match = False
                                elif op == '>' and int(r.get(col, 0)) <= int(val):
                                    match = False
                                elif op == '<' and int(r.get(col, 0)) >= int(val):
                                    match = False
                        if match:
                            r.update(updates)
                            count += 1
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': count}
                elif parsed['type'] == 'DELETE':
                    table_name = parsed['table']
                    where = parsed.get('where')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    if where:
                        m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
                        if m:
                            col, op, val = (m.group(1), m.group(2), m.group(3))
                            if op == '=':
                                new_rows = [r for r in rows if isinstance(r, dict) and str(r.get(col, '')) != val]
                            elif op == '>':
                                try:
                                    val_num = int(val)
                                    new_rows = [r for r in rows if isinstance(r, dict) and int(r.get(col, 0)) <= val_num]
                                except ValueError:
                                    new_rows = rows
                            else:
                                new_rows = rows
                            deleted_count = len(rows) - len(new_rows)
                            self.tables[table_name] = new_rows
                        else:
                            deleted_count = 0
                    else:
                        deleted_count = len(rows)
                        self.tables[table_name] = []
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': deleted_count}
                else:
                    return self.format_error_result('Unsupported query type in file-based mode', query_type)
                execution_time = time.time() - start_time
                return self.format_query_result(result, query_type, execution_time=execution_time)
            else:
                return self.format_error_result('Unsupported query format in file-based mode', query_type)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing file-based query: {str(e)}')
            logger.error(f'Query that caused error: {query}')
            logger.error(f'Query type: {query_type}')
            import traceback
            logger.error(f'Traceback: {traceback.format_exc()}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def get_database_info(self) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                info = {'database': self.database_name, 'user': 'file_based', 'table_count': len(self.tables), 'connection_string': 'file_based', 'is_connected': True, 'mode': 'file_based'}
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute('SELECT current_database() as database, current_user as user')
                    db_info = cur.fetchone()
                    cur.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'")
                    table_count = cur.fetchone()['table_count']
                info = {'database': db_info['database'], 'user': db_info['user'], 'table_count': table_count, 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def list_collections(self) -> List[str]:
        try:
            if self.file_based_mode:
                return list(self.tables.keys())
            if not self._is_initialized or self.conn is None:
                return []
            with self.conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = [row[0] for row in cur.fetchall()]
            return tables
        except Exception as e:
            logger.error(f'Error listing tables: {str(e)}')
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                if collection_name in self.tables:
                    row_count = len(self.tables[collection_name])
                    info = {'table_name': collection_name, 'row_count': row_count, 'columns': ['id']}
                else:
                    return self.format_error_result(f'Table {collection_name} not found')
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(f'SELECT COUNT(*) as row_count FROM {collection_name}')
                    row_count = cur.fetchone()['row_count']
                    cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                    columns = cur.fetchall()
                info = {'table_name': collection_name, 'row_count': row_count, 'columns': columns}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                if collection_name:
                    if collection_name in self.tables:
                        schema = {'id': 'integer'}
                        return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                    else:
                        return self.format_error_result(f'Table {collection_name} not found')
                else:
                    schemas = {}
                    for table_name in self.tables:
                        schemas[table_name] = {'id': 'integer'}
                    return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if collection_name:
                        cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                        columns = cur.fetchall()
                        schema = {col['column_name']: col['data_type'] for col in columns}
                        return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                    else:
                        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                        tables = [row[0] for row in cur.fetchall()]
                        schemas = {}
                        for table in tables:
                            cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (table,))
                            columns = cur.fetchall()
                            schemas[table] = {col['column_name']: col['data_type'] for col in columns}
                        return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_supported_query_types(self) -> List[QueryType]:
        return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP, QueryType.ALTER, QueryType.INDEX]

    def get_capabilities(self) -> Dict[str, Any]:
        base_capabilities = super().get_capabilities()
        base_capabilities.update({'supports_sql': True, 'supports_transactions': not self.file_based_mode, 'supports_indexing': not self.file_based_mode, 'schema_flexible': self.file_based_mode, 'file_based_mode': self.file_based_mode})
        return base_capabilities

def get_capabilities(self) -> Dict[str, Any]:
    base_capabilities = super().get_capabilities()
    base_capabilities.update({'supports_sql': True, 'supports_transactions': not self.file_based_mode, 'supports_indexing': not self.file_based_mode, 'schema_flexible': self.file_based_mode, 'file_based_mode': self.file_based_mode})
    return base_capabilities

class PostgreSQLInfoTool(Tool):
    name: str = 'postgresql_info'
    description: str = 'Get PostgreSQL database and table information.'
    inputs: Dict[str, Dict[str, str]] = {'info_type': {'type': 'string', 'description': 'Type of information (database, tables, table, schema, capabilities)'}, 'table_name': {'type': 'string', 'description': 'Table name for table-specific info (optional)'}}
    required: Optional[List[str]] = []

    def __init__(self, database: PostgreSQLDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, info_type: str='database', table_name: str=None) -> Dict[str, Any]:
        try:
            if not self.database:
                return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
            info_type = info_type.lower()
            if info_type == 'database':
                result = self.database.get_database_info()
            elif info_type == 'tables':
                tables = self.database.list_collections()
                result = {'success': True, 'data': tables, 'table_count': len(tables)}
            elif info_type == 'table' and table_name:
                result = self.database.get_collection_info(table_name)
            elif info_type == 'schema':
                result = self.database.get_schema(table_name)
            elif info_type == 'capabilities':
                result = {'success': True, 'data': self.database.get_capabilities()}
            else:
                return {'success': False, 'error': f'Invalid info type: {info_type}', 'data': None}
            return result
        except Exception as e:
            logger.error(f'Error in postgresql_info tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, info_type: str='database', table_name: str=None) -> Dict[str, Any]:
    try:
        if not self.database:
            return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
        info_type = info_type.lower()
        if info_type == 'database':
            result = self.database.get_database_info()
        elif info_type == 'tables':
            tables = self.database.list_collections()
            result = {'success': True, 'data': tables, 'table_count': len(tables)}
        elif info_type == 'table' and table_name:
            result = self.database.get_collection_info(table_name)
        elif info_type == 'schema':
            result = self.database.get_schema(table_name)
        elif info_type == 'capabilities':
            result = {'success': True, 'data': self.database.get_capabilities()}
        else:
            return {'success': False, 'error': f'Invalid info type: {info_type}', 'data': None}
        return result
    except Exception as e:
        logger.error(f'Error in postgresql_info tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class PostgreSQLToolkit(Toolkit):

    def __init__(self, name: str='PostgreSQLToolkit', connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, **kwargs):
        database = PostgreSQLDatabase(connection_string=connection_string, database_name=database_name, local_path=local_path, auto_save=auto_save, **kwargs)
        tools = [PostgreSQLExecuteTool(database=database), PostgreSQLFindTool(database=database), PostgreSQLUpdateTool(database=database), PostgreSQLCreateTool(database=database), PostgreSQLDeleteTool(database=database), PostgreSQLInfoTool(database=database)]
        super().__init__(name=name, tools=tools)
        self.database = database
        self.connection_string = connection_string
        self.database_name = database_name
        self.local_path = local_path
        self.auto_save = auto_save
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self):
        try:
            if self.database:
                self.database.disconnect()
                logger.info('Disconnected from PostgreSQL database')
        except Exception as e:
            logger.warning(f'Error during cleanup: {str(e)}')

    def get_capabilities(self) -> Dict[str, Any]:
        if self.database:
            capabilities = self.database.get_capabilities()
            capabilities.update({'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save})
            return capabilities
        return {'error': 'PostgreSQL database not initialized'}

    def connect(self) -> bool:
        return self.database.connect() if self.database else False

    def disconnect(self) -> bool:
        return self.database.disconnect() if self.database else False

    def test_connection(self) -> bool:
        return self.database.test_connection() if self.database else False

    def get_database(self) -> PostgreSQLDatabase:
        return self.database

    def get_local_info(self) -> Dict[str, Any]:
        return {'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'database_name': self.database_name, 'connection_string': self.connection_string} if self.database else {'error': 'Database not initialized'}

def get_capabilities(self) -> Dict[str, Any]:
    if self.database:
        capabilities = self.database.get_capabilities()
        capabilities.update({'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save})
        return capabilities
    return {'error': 'PostgreSQL database not initialized'}

class MongoDBDatabase(DatabaseBase):
    """
    MongoDB database implementation with automatic initialization.
    Handles remote connections, existing local databases, and new local database creation.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, read_only: bool=False, **kwargs):
        """
        Initialize MongoDB database with automatic detection and setup.
        
        Args:
            connection_string: MongoDB connection string (for remote)
            database_name: Name of the database
            local_path: Path for local file-based database
            auto_save: Automatically save changes to local files
            read_only: If True, only read operations are allowed (no insert, update, delete)
            **kwargs: Additional connection parameters
        """
        init_params = {'connection_string': connection_string, 'database_name': database_name}
        super().__init__(**init_params, **kwargs)
        self.local_path = Path(local_path) if local_path else None
        self.auto_save = auto_save
        self.read_only = read_only
        self.connection_params = kwargs
        self.is_local_database = False
        self.client = None
        self.database = None
        if self._is_remote_connection():
            self._init_remote_database()
        elif self._is_existing_local_database():
            self._init_existing_local_database()
        else:
            self._init_new_local_database()

    def _is_remote_connection(self) -> bool:
        """Check if this is a remote MongoDB connection"""
        return self.connection_string and (self.connection_string.startswith(('mongodb://', 'mongodb+srv://')) or 'localhost' in self.connection_string or '127.0.0.1' in self.connection_string)

    def _is_existing_local_database(self) -> bool:
        """Check if there's an existing local database"""
        if not self.local_path:
            return False
        if not self.local_path.exists():
            return False
        json_files = list(self.local_path.glob('*.json'))
        db_info_file = self.local_path / 'db_info.json'
        return len(json_files) > 0 or db_info_file.exists()

    def _init_remote_database(self):
        """Initialize remote MongoDB connection"""
        try:
            self.client = MongoClient(self.connection_string, **self.connection_params)
            self.client.admin.command('ping')
            if self.database_name:
                self.database = self.client[self.database_name]
            self._is_initialized = True
            self.is_local_database = False
            logger.info(f'Connected to remote MongoDB: {self.database_name}')
        except Exception as e:
            logger.error(f'Failed to connect to remote MongoDB: {str(e)}')
            self._is_initialized = False
            raise

    def _init_existing_local_database(self):
        """Initialize existing local database"""
        try:
            self.connection_string = 'mongodb://localhost:27017'
            self.client = MongoClient(self.connection_string, **self.connection_params)
            if not self.database_name:
                self.database_name = self.local_path.name
            self.database = self.client[self.database_name]
            self._load_local_collections()
            self._is_initialized = True
            self.is_local_database = True
            logger.info(f'Loaded existing local database from: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to load existing local database: {str(e)}')
            self._is_initialized = False
            raise

    def _init_new_local_database(self):
        """Initialize new local database"""
        try:
            if not self.local_path:
                self.local_path = Path('./mongodb_local')
            self.local_path.mkdir(parents=True, exist_ok=True)
            self.connection_string = 'mongodb://localhost:27017'
            self.client = MongoClient(self.connection_string, **self.connection_params)
            if not self.database_name:
                self.database_name = self.local_path.name
            self.database = self.client[self.database_name]
            self._create_db_info_file()
            self._is_initialized = True
            self.is_local_database = True
            logger.info(f'Created new local database at: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to create new local database: {str(e)}')
            self._is_initialized = False
            raise

    def _load_local_collections(self):
        """Load collections from local JSON files"""
        if not self.local_path or not self.local_path.exists():
            return
        json_files = [f for f in self.local_path.glob('*.json') if f.name != 'db_info.json']
        for json_file in json_files:
            collection_name = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    documents = [data]
                elif isinstance(data, list):
                    documents = data
                else:
                    continue
                if documents:
                    cleaned_documents = []
                    for doc in documents:
                        cleaned_doc = self._clean_document_for_insert(doc)
                        cleaned_documents.append(cleaned_doc)
                    collection = self.database[collection_name]
                    collection.drop()
                    if cleaned_documents:
                        collection.insert_many(cleaned_documents)
                        logger.info(f"Loaded {len(cleaned_documents)} documents into '{collection_name}'")
            except Exception as e:
                logger.warning(f'Failed to load collection from {json_file}: {str(e)}')

    def _clean_document_for_insert(self, doc: Dict) -> Dict:
        """Clean document by removing problematic MongoDB-specific fields"""
        if isinstance(doc, dict):
            cleaned = {}
            for key, value in doc.items():
                if key == '_id' and isinstance(value, dict) and ('$oid' in value):
                    continue
                elif isinstance(value, dict):
                    cleaned[key] = self._clean_document_for_insert(value)
                elif isinstance(value, list):
                    cleaned[key] = [self._clean_document_for_insert(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = value
            return cleaned
        return doc

    def _create_db_info_file(self):
        """Create database info file for new local database"""
        try:
            db_info = {'database_name': self.database_name, 'created_at': time.time(), 'local_path': str(self.local_path.absolute()), 'auto_save': self.auto_save, 'version': '1.0'}
            info_file = self.local_path / 'db_info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f'Failed to create db info file: {str(e)}')

    def _save_collection_to_file(self, collection_name: str):
        """Save collection to local JSON file"""
        if not self.is_local_database or not self.local_path:
            return
        try:
            collection = self.database[collection_name]
            documents = list(collection.find())
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            file_path = self.local_path / f'{collection_name}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved collection '{collection_name}' to {file_path}")
        except Exception as e:
            logger.warning(f"Failed to save collection '{collection_name}': {str(e)}")

    def _auto_save_if_needed(self, collection_name: str):
        """Auto-save collection if local database and auto_save is enabled"""
        if self.is_local_database and self.auto_save:
            self._save_collection_to_file(collection_name)

    def _get_database_type(self) -> DatabaseType:
        return DatabaseType.MONGODB

    def connect(self) -> bool:
        """Connection is already established in __init__"""
        return self._is_initialized

    def disconnect(self) -> bool:
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.database = None
                self._is_initialized = False
                logger.info('Disconnected from MongoDB')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting: {str(e)}')
            return False

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, collection_name: str=None, **kwargs) -> Dict[str, Any]:
        """Execute a query on MongoDB with automatic result handling"""
        if not self._is_initialized or self.database is None:
            return self.format_error_result('Database not connected')
        if not collection_name:
            return self.format_error_result('Collection name is required')
        start_time = time.time()
        try:
            collection = self.database[collection_name]
            if not query_type:
                query_type = self._infer_query_type(query)
            if self.read_only and query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP]:
                return self.format_error_result(f"Write operation '{query_type.value}' is not allowed in read-only mode. Only SELECT and AGGREGATE operations are permitted.", query_type, execution_time=time.time() - start_time)
            if query_type == QueryType.SELECT:
                result = self._execute_find(collection, query, **kwargs)
            elif query_type == QueryType.INSERT:
                result = self._execute_insert(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.UPDATE:
                result = self._execute_update(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.DELETE:
                result = self._execute_delete(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.AGGREGATE:
                result = self._execute_aggregate(collection, query, **kwargs)
            else:
                return self.format_error_result(f'Unsupported query type: {query_type}')
            execution_time = time.time() - start_time
            if isinstance(result, dict):
                result['execution_time'] = execution_time
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing MongoDB query: {str(e)}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def _infer_query_type(self, query: Union[str, Dict, List]) -> QueryType:
        """Infer query type from the query structure"""
        if isinstance(query, list):
            return QueryType.AGGREGATE
        elif isinstance(query, dict):
            if self.read_only:
                if 'insert' in query or 'insertOne' in query or 'insertMany' in query:
                    return QueryType.SELECT
                elif 'update' in query or 'updateOne' in query or 'updateMany' in query:
                    return QueryType.SELECT
                elif 'delete' in query or 'deleteOne' in query or 'deleteMany' in query:
                    return QueryType.SELECT
                elif 'create' in query or 'createCollection' in query:
                    return QueryType.SELECT
                elif 'drop' in query or 'dropCollection' in query:
                    return QueryType.SELECT
                else:
                    return QueryType.SELECT
            elif 'insert' in query or 'insertOne' in query or 'insertMany' in query:
                return QueryType.INSERT
            elif 'update' in query or 'updateOne' in query or 'updateMany' in query:
                return QueryType.UPDATE
            elif 'delete' in query or 'deleteOne' in query or 'deleteMany' in query:
                return QueryType.DELETE
            elif 'create' in query or 'createCollection' in query:
                return QueryType.CREATE
            elif 'drop' in query or 'dropCollection' in query:
                return QueryType.DROP
            else:
                return QueryType.SELECT
        elif isinstance(query, str):
            query_lower = query.lower().strip()
            if self.read_only:
                return QueryType.SELECT
            elif query_lower.startswith(('insert', 'create')):
                return QueryType.INSERT
            elif query_lower.startswith('update'):
                return QueryType.UPDATE
            elif query_lower.startswith('delete'):
                return QueryType.DELETE
            elif query_lower.startswith('drop'):
                return QueryType.DROP
            else:
                return QueryType.SELECT
        return QueryType.SELECT

    def _execute_find(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute find query"""
        try:
            if isinstance(query, str):
                if '=' in query:
                    field, value = query.split('=', 1)
                    query = {field.strip(): value.strip()}
                else:
                    query = {}
            filter_query = query.get('filter', query)
            projection = query.get('projection', {})
            sort = query.get('sort', None)
            limit = query.get('limit', kwargs.get('limit', 0))
            skip = query.get('skip', kwargs.get('skip', 0))
            cursor = collection.find(filter_query, projection)
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            results = []
            for doc in cursor:
                doc = json.loads(json_util.dumps(doc))
                results.append(doc)
            return self.format_query_result(results, QueryType.SELECT, collection_name=collection.name, filter_applied=filter_query)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.SELECT)

    def _execute_insert(self, collection, query: Union[Dict, List], **kwargs) -> Dict[str, Any]:
        """Execute insert operation"""
        try:
            if isinstance(query, dict):
                if 'document' in query:
                    document = query['document']
                else:
                    document = query
                result = collection.insert_one(document)
                return self.format_query_result({'inserted_id': str(result.inserted_id)}, QueryType.INSERT, collection_name=collection.name)
            elif isinstance(query, list):
                if all((isinstance(item, dict) for item in query)):
                    documents = query
                else:
                    documents = [{'documents': query}]
                result = collection.insert_many(documents)
                return self.format_query_result({'inserted_ids': [str(id) for id in result.inserted_ids]}, QueryType.INSERT, collection_name=collection.name)
            else:
                return self.format_error_result('Invalid insert query format', QueryType.INSERT)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.INSERT)

    def _execute_update(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute update operation"""
        try:
            filter_query = query.get('filter', {})
            update_query = query.get('update', {})
            upsert = query.get('upsert', False)
            multi = query.get('multi', False)
            if multi:
                result = collection.update_many(filter_query, update_query, upsert=upsert)
            else:
                result = collection.update_one(filter_query, update_query, upsert=upsert)
            return self.format_query_result({'matched_count': result.matched_count, 'modified_count': result.modified_count, 'upserted_id': str(result.upserted_id) if result.upserted_id else None}, QueryType.UPDATE, collection_name=collection.name)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.UPDATE)

    def _execute_delete(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute delete operation"""
        try:
            filter_query = query.get('filter', query)
            multi = query.get('multi', False)
            if multi:
                result = collection.delete_many(filter_query)
            else:
                result = collection.delete_one(filter_query)
            return self.format_query_result({'deleted_count': result.deleted_count}, QueryType.DELETE, collection_name=collection.name)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.DELETE)

    def _execute_aggregate(self, collection, pipeline: List, **kwargs) -> Dict[str, Any]:
        """Execute aggregation pipeline"""
        try:
            cursor = collection.aggregate(pipeline)
            results = []
            for doc in cursor:
                doc = json.loads(json_util.dumps(doc))
                results.append(doc)
            return self.format_query_result(results, QueryType.AGGREGATE, collection_name=collection.name, pipeline_stages=len(pipeline))
        except Exception as e:
            return self.format_error_result(str(e), QueryType.AGGREGATE)

    def get_database_info(self) -> Dict[str, Any]:
        """Get MongoDB database information"""
        try:
            if not self._is_initialized or self.database is None:
                return self.format_error_result('Database not connected')
            stats = self.database.command('dbStats')
            server_info = self.client.server_info()
            info = {'database_name': self.database_name, 'collections': stats.get('collections', 0), 'data_size': stats.get('dataSize', 0), 'storage_size': stats.get('storageSize', 0), 'indexes': stats.get('indexes', 0), 'index_size': stats.get('indexSize', 0), 'server_version': server_info.get('version', 'Unknown'), 'server_type': server_info.get('type', 'Unknown'), 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        try:
            if not self._is_initialized or self.database is None:
                return []
            return self.database.list_collection_names()
        except Exception as e:
            logger.error(f'Error listing collections: {str(e)}')
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection"""
        try:
            if not self._is_initialized or not self.database:
                return self.format_error_result('Database not connected')
            collection = self.database[collection_name]
            stats = self.database.command('collStats', collection_name)
            indexes = list(collection.list_indexes())
            sample_docs = list(collection.find().limit(5))
            info = {'collection_name': collection_name, 'document_count': stats.get('count', 0), 'data_size': stats.get('size', 0), 'storage_size': stats.get('storageSize', 0), 'index_count': stats.get('nindexes', 0), 'indexes': [{'name': idx['name'], 'keys': idx['key']} for idx in indexes], 'sample_documents': sample_docs[:2]}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        """Get schema information for database or specific collection"""
        try:
            if not self._is_initialized or not self.database:
                return self.format_error_result('Database not connected')
            if collection_name:
                collection = self.database[collection_name]
                sample_docs = list(collection.find().limit(100))
                if not sample_docs:
                    return self.format_query_result({'collection_name': collection_name, 'schema': {}, 'message': 'No documents found'}, QueryType.SELECT)
                schema = self._infer_schema_from_documents(sample_docs)
                return self.format_query_result({'collection_name': collection_name, 'schema': schema, 'sample_count': len(sample_docs)}, QueryType.SELECT)
            else:
                collections = self.list_collections()
                schemas = {}
                for coll_name in collections[:10]:
                    coll_schema = self.get_schema(coll_name)
                    if coll_schema.get('success'):
                        schemas[coll_name] = coll_schema.get('data', {}).get('schema', {})
                return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def _infer_schema_from_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Infer schema from a list of documents"""
        if not documents:
            return {}
        schema = {}
        for doc in documents:
            self._update_schema_from_document(schema, doc)
        return schema

    def _update_schema_from_document(self, schema: Dict, document: Dict, path: str=''):
        """Recursively update schema from a document"""
        for key, value in document.items():
            current_path = f'{path}.{key}' if path else key
            if isinstance(value, dict):
                if current_path not in schema:
                    schema[current_path] = {'type': 'object', 'fields': {}}
                self._update_schema_from_document(schema[current_path]['fields'], value, current_path)
            elif isinstance(value, list):
                if current_path not in schema:
                    schema[current_path] = {'type': 'array', 'element_types': set()}
                for item in value[:3]:
                    if isinstance(item, dict):
                        schema[current_path]['element_types'].add('object')
                    else:
                        schema[current_path]['element_types'].add(type(item).__name__)
                schema[current_path]['element_types'] = list(schema[current_path]['element_types'])
            elif current_path not in schema:
                schema[current_path] = {'type': type(value).__name__}
            elif schema[current_path]['type'] != type(value).__name__:
                schema[current_path]['type'] = 'mixed'

    def get_supported_query_types(self) -> List[QueryType]:
        """Get MongoDB-specific supported query types"""
        if self.read_only:
            return [QueryType.SELECT, QueryType.AGGREGATE]
        else:
            return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP, QueryType.AGGREGATE, QueryType.INDEX]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get MongoDB-specific capabilities"""
        base_capabilities = super().get_capabilities()
        base_capabilities.update({'supports_aggregation': True, 'supports_full_text_search': True, 'supports_geospatial_queries': True, 'supports_change_streams': True, 'supports_transactions': True, 'supports_indexing': True, 'document_oriented': True, 'schema_flexible': True, 'read_only': self.read_only, 'write_operations_allowed': not self.read_only})
        return base_capabilities

def get_capabilities(self) -> Dict[str, Any]:
    """Get MongoDB-specific capabilities"""
    base_capabilities = super().get_capabilities()
    base_capabilities.update({'supports_aggregation': True, 'supports_full_text_search': True, 'supports_geospatial_queries': True, 'supports_change_streams': True, 'supports_transactions': True, 'supports_indexing': True, 'document_oriented': True, 'schema_flexible': True, 'read_only': self.read_only, 'write_operations_allowed': not self.read_only})
    return base_capabilities

class MongoDBInfoTool(Tool):
    name: str = 'mongodb_info'
    description: str = 'Get MongoDB database and collection information'
    inputs: Dict[str, Dict[str, str]] = {'info_type': {'type': 'string', 'description': 'Type of information (database, collections, collection, schema, capabilities)'}, 'collection_name': {'type': 'string', 'description': 'Collection name for collection-specific info (optional)'}}
    required: Optional[List[str]] = []

    def __init__(self, database: MongoDBDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, info_type: str='database', collection_name: str=None) -> Dict[str, Any]:
        """Get MongoDB information"""
        try:
            if not self.database:
                return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
            info_type = info_type.lower()
            if info_type == 'database':
                result = self.database.get_database_info()
            elif info_type == 'collections':
                collections = self.database.list_collections()
                result = {'success': True, 'data': collections, 'collection_count': len(collections)}
            elif info_type == 'collection' and collection_name:
                result = self.database.get_collection_info(collection_name)
            elif info_type == 'schema':
                result = self.database.get_schema(collection_name)
            elif info_type == 'capabilities':
                result = {'success': True, 'data': self.database.get_capabilities()}
            else:
                return {'success': False, 'error': f'Invalid info type: {info_type}', 'data': None}
            if result['success']:
                logger.info(f'Successfully retrieved {info_type} information')
            else:
                logger.error(f'Failed to retrieve {info_type} information: {result.get('error', 'Unknown error')}')
            return result
        except Exception as e:
            logger.error(f'Error in mongodb_info tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, info_type: str='database', collection_name: str=None) -> Dict[str, Any]:
    """Get MongoDB information"""
    try:
        if not self.database:
            return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
        info_type = info_type.lower()
        if info_type == 'database':
            result = self.database.get_database_info()
        elif info_type == 'collections':
            collections = self.database.list_collections()
            result = {'success': True, 'data': collections, 'collection_count': len(collections)}
        elif info_type == 'collection' and collection_name:
            result = self.database.get_collection_info(collection_name)
        elif info_type == 'schema':
            result = self.database.get_schema(collection_name)
        elif info_type == 'capabilities':
            result = {'success': True, 'data': self.database.get_capabilities()}
        else:
            return {'success': False, 'error': f'Invalid info type: {info_type}', 'data': None}
        if result['success']:
            logger.info(f'Successfully retrieved {info_type} information')
        else:
            logger.error(f'Failed to retrieve {info_type} information: {result.get('error', 'Unknown error')}')
        return result
    except Exception as e:
        logger.error(f'Error in mongodb_info tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class MongoDBToolkit(Toolkit):
    """
    MongoDB-specific toolkit with simplified design.
    Automatically handles remote, local file-based, or new database creation.
    """

    def __init__(self, name: str='MongoDBToolkit', connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, read_only: bool=False, **kwargs):
        """
        Initialize the MongoDB toolkit.
        
        Args:
            name: Name of the toolkit
            connection_string: MongoDB connection string (for remote/existing)
            database_name: Name of the database to use
            local_path: Path for local file-based database
            auto_save: Automatically save changes to local files
            read_only: If True, only read operations are allowed (no insert, update, delete)
            **kwargs: Additional connection parameters
        """
        database = MongoDBDatabase(connection_string=connection_string, database_name=database_name, local_path=local_path, auto_save=auto_save, read_only=read_only, **kwargs)
        if read_only:
            tools = [MongoDBExecuteQueryTool(database=database), MongoDBFindTool(database=database), MongoDBInfoTool(database=database)]
        else:
            tools = [MongoDBExecuteQueryTool(database=database), MongoDBFindTool(database=database), MongoDBUpdateTool(database=database), MongoDBDeleteTool(database=database), MongoDBInfoTool(database=database)]
        super().__init__(name=name, tools=tools)
        self.database = database
        self.connection_string = connection_string
        self.database_name = database_name
        self.local_path = local_path
        self.auto_save = auto_save
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Cleanup function called when program exits"""
        try:
            if self.database.is_local_database and self.database.auto_save:
                logger.info('Auto-saving local database before exit...')
                collections = self.database.list_collections()
                for collection_name in collections:
                    self.database._save_collection_to_file(collection_name)
            if self.database:
                self.database.disconnect()
                logger.info('Disconnected from MongoDB database')
        except Exception as e:
            logger.warning(f'Error during cleanup: {str(e)}')

    def get_capabilities(self) -> Dict[str, Any]:
        """Get MongoDB-specific capabilities"""
        if self.database:
            capabilities = self.database.get_capabilities()
            capabilities.update({'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'read_only': self.database.read_only})
            return capabilities
        return {'error': 'MongoDB database not initialized'}

    def connect(self) -> bool:
        """Connect to MongoDB"""
        return self.database.connect() if self.database else False

    def disconnect(self) -> bool:
        """Disconnect from MongoDB"""
        return self.database.disconnect() if self.database else False

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        return self.database.test_connection() if self.database else False

    def get_database(self) -> MongoDBDatabase:
        """Get the underlying MongoDB database instance"""
        return self.database

    def get_local_info(self) -> Dict[str, Any]:
        """Get information about local database setup"""
        return {'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'read_only': self.database.read_only, 'database_name': self.database_name, 'connection_string': self.connection_string} if self.database else {'error': 'Database not initialized'}

def get_capabilities(self) -> Dict[str, Any]:
    """Get MongoDB-specific capabilities"""
    if self.database:
        capabilities = self.database.get_capabilities()
        capabilities.update({'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'read_only': self.database.read_only})
        return capabilities
    return {'error': 'MongoDB database not initialized'}

class FileStorageHandler(StorageBase):
    """
    Reference implementation showing all available _raw_xxx methods.
    This class serves as a template for developers creating new storage handlers.
    Concrete handlers only need to implement the _raw_xxx methods they need.
    """

    def __init__(self, base_path: str='.', **kwargs):
        """
        Initialize the storage handler.
        
        Args:
            base_path (str): Base directory for storage operations (default: current directory)
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(base_path=base_path, **kwargs)

    def create(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        return super().save(file_path, content, **kwargs)

    def read(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return super().read(file_path, **kwargs)

    def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        return super().list(path, max_depth, include_hidden)

    def delete(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return super().delete(file_path, **kwargs)

    def move(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return super().move(source, destination, **kwargs)

    def copy(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return super().copy(source, destination, **kwargs)

    def create_directory(self, path: str, **kwargs) -> Dict[str, Any]:
        return super().create_directory(path, **kwargs)

    @abstractmethod
    def _initialize_storage(self):
        """Initialize storage - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _delete_raw(self, path: str) -> bool:
        """Delete file or directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _exists_raw(self, path: str) -> bool:
        """Check if path exists - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _create_directory_raw(self, path: str) -> bool:
        """Create directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _list_raw(self, path: str=None, **kwargs) -> List[Dict[str, Any]]:
        """List files and directories - must be implemented by subclasses"""
        pass

    def create_file(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        return self.save(file_path, content, **kwargs)

    def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return self.read(file_path, **kwargs)

    def list_files(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        return self.list(path, max_depth, include_hidden)

    def delete_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return self.delete(file_path, **kwargs)

    def move_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return self.move(source, destination, **kwargs)

    def copy_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return self.copy(source, destination, **kwargs)

def delete(self, file_path: str, **kwargs) -> Dict[str, Any]:
    return super().delete(file_path, **kwargs)

def delete_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
    return self.delete(file_path, **kwargs)

class DeleteTool(Tool):
    name: str = 'delete'
    description: str = 'Delete a file or directory'
    inputs: Dict[str, Dict[str, str]] = {'path': {'type': 'string', 'description': 'Path to the file or directory to delete'}}
    required: Optional[List[str]] = ['path']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, path: str) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Args:
            path: Path to the file or directory to delete
            
        Returns:
            Dictionary containing the delete operation result
        """
        try:
            result = self.storage_handler.delete(path)
            return result
        except Exception as e:
            logger.error(f'Error in DeleteTool: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

def __call__(self, path: str) -> Dict[str, Any]:
    """
        Delete a file or directory.
        
        Args:
            path: Path to the file or directory to delete
            
        Returns:
            Dictionary containing the delete operation result
        """
    try:
        result = self.storage_handler.delete(path)
        return result
    except Exception as e:
        logger.error(f'Error in DeleteTool: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

class StorageHandler(BaseModule):
    """
    Implementation of a storage handler for managing various storage backends.
    
    StorageHandler provides an abstraction for reading and writing data (e.g., memory, agents, workflows).
    It supports multiple storage types, including database, vector, and graph storage, initialized via factories.
    """
    storageConfig: StoreConfig = Field(..., description='Configuration for all storage backends')
    storageDB: Optional[Union[DBStoreBase, Any]] = Field(None, description='Database storage backend')
    vector_store: Optional[Union[VectorStoreBase, Any]] = Field(None, description='Single vector storage backend')
    graph_store: Optional[Union[GraphStoreBase, Any]] = Field(None, description='Optional graph storage backend')

    def init_module(self):
        """
        Initialize all storage backends based on the provided configuration.
        Calls individual initialization methods for database, vector, and graph stores.
        """
        if self.storageConfig.path is not None or self.storageConfig.path != ':memory:' or (not self.storageConfig.path):
            os.makedirs(os.path.dirname(self.storageConfig.path), exist_ok=True)
        self._init_db_store()
        self._init_vector_store()
        self._init_graph_store()

    def _init_db_store(self):
        """
        Initialize the database storage backend using the DBStoreFactory.
        Sets the storageDB attribute with the created instance.
        """
        db_config = self.storageConfig.dbConfig
        self.storageDB = DBStoreFactory.create(db_config.db_name, db_config)

    def _init_vector_store(self):
        """
        Initialize the vector storage backend using the VectorStoreFactory.
        Sets the storageVector attribute if the configuration is provided.
        """
        vector_config = self.storageConfig.vectorConfig
        if vector_config is not None:
            if self.vector_store is not None:
                del self.vector_store
            vector_config_dict = vector_config.model_dump()
            self.vector_store = VectorStoreFactory().create(store_type=vector_config.vector_name, store_config=vector_config_dict)

    def _init_graph_store(self):
        """
        Initialize the graph storage backend using the GraphStoreFactory.
        Sets the storageGraph attribute if the configuration is provided.
        """
        graph_config = self.storageConfig.graphConfig
        if graph_config is not None:
            self.graph_store = GraphStoreFactory().create(store_type=graph_config.graph_name, store_config=graph_config.model_dump())

    def load(self, tables: Optional[List[str]]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load all data from the database storage.

        Attributes:
            tables (Optional[List[str]]): List of table names to load; if None, loads all tables.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary with table names as keys and lists of records as values. You should parse the values by yourself.
        """
        result = {}
        table_info = self.storageDB.col_info()
        if tables is None:
            tables_to_load = [t.value for t in TableType]
        else:
            tables_to_load = tables
        for table_name in tables_to_load:
            table_data = []
            if any((t['table_name'] == table_name for t in table_info)):
                cursor = self.storageDB.connection.cursor()
                cursor.execute(f'SELECT * FROM {table_name}')
                columns = next((t['columns'].keys() for t in table_info if t['table_name'] == table_name))
                rows = cursor.fetchall()
                table_data = [dict(zip(columns, row)) for row in rows]
            result[table_name] = table_data
        return result

    def save(self, data: Dict[str, Any], *args, **kwargs):
        """
        Save all provided data to the database storage.

        Attributes:
            data (Dict[str, Any]): Dictionary with table names as keys and lists of records to save.

        Raises:
            ValueError: If an unknown table name is provided.
        """
        for table_name, records in data.items():
            store_type = None
            for st in TableType:
                if st.value == table_name:
                    store_type = st
                    break
            if store_type is None:
                raise ValueError(f'Unknown table: {table_name}')
            for record in records:
                self.storageDB.insert(metadata=record, store_type=store_type, table=table_name)

    def parse_result(self, results: Dict[str, str], store: Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]) -> Dict[str, Any]:
        """
        Parse database results, converting JSON strings to Python objects where applicable.

        Attributes:
            results (Dict[str, str]): Raw database results with column names as keys.
            store (Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]): Pydantic model for validation.

        Returns:
            Dict[str, Any]: Parsed results with JSON strings deserialized to Python objects.
        """
        for k, v in store.model_fields.items():
            if v.annotation not in [Optional[str], str]:
                try:
                    results[k] = json.loads(results[k])
                except (json.JSONDecodeError, KeyError, TypeError):
                    results[k] = results.get(k)
        return results

    def load_memory(self, memory_id: str, table: Optional[str]=None, **kwargs) -> Dict[str, Any]:
        """
        Load a single long-term memory data.

        Attributes:
            memory_id (str): The ID of the long-term memory.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a LongTermMemory instance.
        """
        table = table or TableType.store_memory.value
        result = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
        if result is not None:
            result = self.parse_result(result, MemoryStore)
        return result

    def save_memory(self, memory_data: Dict[str, Any], table: Optional[str]=None, **kwargs):
        """
        Save or update a single memory.

        Attributes:
            memory_data (Dict[str, Any]): The long-term memory's data.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        """
        table = table or TableType.store_memory.value
        memory_id = memory_data.get('memory_id')
        if not memory_id:
            raise ValueError("Memory data must include a 'memory_id' field")
        existing = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
        if existing:
            self.storageDB.update(memory_id, new_metadata=memory_data, store_type='memory', table=table)
        else:
            self.storageDB.insert(metadata=memory_data, store_type='memory', table=table)

    def load_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single agent's data.

        Attributes:
            agent_name (str): The unique name of the agent to retrieve.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create an Agent instance, or None if not found.
        """
        table = table or TableType.store_agent.value
        result = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
        if result is not None:
            result = self.parse_result(result, AgentStore)
        return result

    def remove_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs):
        """
        Remove an agent from storage if the agent exists.

        Attributes:
            agent_name (str): The name of the agent to be deleted.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If the agent does not exist in the specified table.
        """
        table = table or TableType.store_agent.value
        success = self.storageDB.delete(agent_name, store_type='agent', table=table)
        if not success:
            raise ValueError(f'Agent with name {agent_name} not found in table {table}')

    def save_agent(self, agent_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a single agent's data.

        Attributes:
            agent_data (Dict[str, Any]): The agent's data, must include 'name' and 'content' keys.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_agent.value
        agent_name = agent_data.get('name')
        if not agent_name:
            raise ValueError("Agent data must include a 'name' field")
        existing = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
        if existing:
            self.storageDB.update(agent_name, new_metadata=agent_data, store_type='agent', table=table)
        else:
            self.storageDB.insert(metadata=agent_data, store_type='agent', table=table)

    def load_workflow(self, workflow_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single workflow's data.

        Attributes:
            workflow_id (str): The ID of the workflow.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a WorkFlow instance, or None if not found.
        """
        table = table or TableType.store_workflow.value
        result = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
        if result is not None:
            result = self.parse_result(result, WorkflowStore)
        return result

    def save_workflow(self, workflow_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a workflow's data.

        Attributes:
            workflow_data (Dict[str, Any]): The workflow's data, must include 'name' field.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_workflow.value
        workflow_id = workflow_data.get('name')
        if not workflow_id:
            raise ValueError("Workflow data must include a 'name' field")
        existing = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
        if existing:
            self.storageDB.update(workflow_id, new_metadata=workflow_data, store_type='workflow', table=table)
        else:
            self.storageDB.insert(metadata=workflow_data, store_type='workflow', table=table)

    def load_history(self, memory_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single history entry.

        Attributes:
            memory_id (str): The ID of the memory associated with the history entry.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Returns:
            Dict[str, Any]: The history data, or None if not found.
        """
        table = table or TableType.store_history.value
        result = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
        if result is not None:
            result = self.parse_result(result, HistoryStore)
        return result

    def save_history(self, history_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a single history entry.

        Attributes:
            history_data (Dict[str, Any]): The history data, must include 'memory_id' field.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Raises:
            ValueError: If 'memory_id' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_history.value
        memory_id = history_data.get('memory_id')
        if not memory_id:
            raise ValueError("History data must include a 'memory_id' field")
        existing = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
        if existing:
            result = HistoryStore.model_validate(self.parse_result(existing, HistoryStore))
            history_data['old_memory'] = result.old_memory
            self.storageDB.update(memory_id, new_metadata=history_data, store_type='history', table=table)
        else:
            self.storageDB.insert(metadata=history_data, store_type='history', table=table)

    def load_index(self, corpus_id: str, table: Optional[str]=None) -> Optional[Dict[str, Any]]:
        result = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
        if result is not None:
            result = self.parse_result(result, IndexStore)
        return result

    def save_index(self, index_data: Dict[str, Any], table: Optional[str]=None):
        corpus_id = index_data.get('corpus_id')
        if not corpus_id:
            raise ValueError("Index data must include an 'corpus_id' field")
        existing = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
        if existing:
            self.storageDB.update(corpus_id, new_metadata=index_data, store_type='indexing', table=table)
        else:
            self.storageDB.insert(metadata=index_data, store_type='indexing', table=table)

def save(self, data: Dict[str, Any], *args, **kwargs):
    """
        Save all provided data to the database storage.

        Attributes:
            data (Dict[str, Any]): Dictionary with table names as keys and lists of records to save.

        Raises:
            ValueError: If an unknown table name is provided.
        """
    for table_name, records in data.items():
        store_type = None
        for st in TableType:
            if st.value == table_name:
                store_type = st
                break
        if store_type is None:
            raise ValueError(f'Unknown table: {table_name}')
        for record in records:
            self.storageDB.insert(metadata=record, store_type=store_type, table=table_name)

def load_memory(self, memory_id: str, table: Optional[str]=None, **kwargs) -> Dict[str, Any]:
    """
        Load a single long-term memory data.

        Attributes:
            memory_id (str): The ID of the long-term memory.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a LongTermMemory instance.
        """
    table = table or TableType.store_memory.value
    result = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
    if result is not None:
        result = self.parse_result(result, MemoryStore)
    return result

def save_memory(self, memory_data: Dict[str, Any], table: Optional[str]=None, **kwargs):
    """
        Save or update a single memory.

        Attributes:
            memory_data (Dict[str, Any]): The long-term memory's data.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        """
    table = table or TableType.store_memory.value
    memory_id = memory_data.get('memory_id')
    if not memory_id:
        raise ValueError("Memory data must include a 'memory_id' field")
    existing = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
    if existing:
        self.storageDB.update(memory_id, new_metadata=memory_data, store_type='memory', table=table)
    else:
        self.storageDB.insert(metadata=memory_data, store_type='memory', table=table)

def load_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
    """
        Load a single agent's data.

        Attributes:
            agent_name (str): The unique name of the agent to retrieve.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create an Agent instance, or None if not found.
        """
    table = table or TableType.store_agent.value
    result = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
    if result is not None:
        result = self.parse_result(result, AgentStore)
    return result

def remove_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs):
    """
        Remove an agent from storage if the agent exists.

        Attributes:
            agent_name (str): The name of the agent to be deleted.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If the agent does not exist in the specified table.
        """
    table = table or TableType.store_agent.value
    success = self.storageDB.delete(agent_name, store_type='agent', table=table)
    if not success:
        raise ValueError(f'Agent with name {agent_name} not found in table {table}')

def save_agent(self, agent_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
    """
        Save or update a single agent's data.

        Attributes:
            agent_data (Dict[str, Any]): The agent's data, must include 'name' and 'content' keys.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
    table = table or TableType.store_agent.value
    agent_name = agent_data.get('name')
    if not agent_name:
        raise ValueError("Agent data must include a 'name' field")
    existing = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
    if existing:
        self.storageDB.update(agent_name, new_metadata=agent_data, store_type='agent', table=table)
    else:
        self.storageDB.insert(metadata=agent_data, store_type='agent', table=table)

def load_workflow(self, workflow_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
    """
        Load a single workflow's data.

        Attributes:
            workflow_id (str): The ID of the workflow.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a WorkFlow instance, or None if not found.
        """
    table = table or TableType.store_workflow.value
    result = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
    if result is not None:
        result = self.parse_result(result, WorkflowStore)
    return result

def save_workflow(self, workflow_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
    """
        Save or update a workflow's data.

        Attributes:
            workflow_data (Dict[str, Any]): The workflow's data, must include 'name' field.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
    table = table or TableType.store_workflow.value
    workflow_id = workflow_data.get('name')
    if not workflow_id:
        raise ValueError("Workflow data must include a 'name' field")
    existing = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
    if existing:
        self.storageDB.update(workflow_id, new_metadata=workflow_data, store_type='workflow', table=table)
    else:
        self.storageDB.insert(metadata=workflow_data, store_type='workflow', table=table)

def load_history(self, memory_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
    """
        Load a single history entry.

        Attributes:
            memory_id (str): The ID of the memory associated with the history entry.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Returns:
            Dict[str, Any]: The history data, or None if not found.
        """
    table = table or TableType.store_history.value
    result = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
    if result is not None:
        result = self.parse_result(result, HistoryStore)
    return result

def save_history(self, history_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
    """
        Save or update a single history entry.

        Attributes:
            history_data (Dict[str, Any]): The history data, must include 'memory_id' field.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Raises:
            ValueError: If 'memory_id' field is missing or if Pydantic validation fails.
        """
    table = table or TableType.store_history.value
    memory_id = history_data.get('memory_id')
    if not memory_id:
        raise ValueError("History data must include a 'memory_id' field")
    existing = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
    if existing:
        result = HistoryStore.model_validate(self.parse_result(existing, HistoryStore))
        history_data['old_memory'] = result.old_memory
        self.storageDB.update(memory_id, new_metadata=history_data, store_type='history', table=table)
    else:
        self.storageDB.insert(metadata=history_data, store_type='history', table=table)

def load_index(self, corpus_id: str, table: Optional[str]=None) -> Optional[Dict[str, Any]]:
    result = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
    if result is not None:
        result = self.parse_result(result, IndexStore)
    return result

def save_index(self, index_data: Dict[str, Any], table: Optional[str]=None):
    corpus_id = index_data.get('corpus_id')
    if not corpus_id:
        raise ValueError("Index data must include an 'corpus_id' field")
    existing = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
    if existing:
        self.storageDB.update(corpus_id, new_metadata=index_data, store_type='indexing', table=table)
    else:
        self.storageDB.insert(metadata=index_data, store_type='indexing', table=table)

class BaseConfig(BaseModule):
    """
    Base configuration class that serves as parent for all configuration classes.
    
    A config should inherit BaseConfig and specify the attributes and their types. 
    Otherwise this will be an empty config.
    """

    def save(self, path: str, **kwargs) -> str:
        """Save configuration to the specified path.
        
        Args:
            path: The file path to save the configuration
            **kwargs (Any): Additional keyword arguments passed to save_module method
        
        Returns:
            str: The path where the file was saved
        """
        return super().save_module(path, **kwargs)

    def get_config_params(self) -> List[str]:
        """Get a list of configuration parameters.
        
        Returns:
            List[str]: List of configuration parameter names, excluding 'class_name'
        """
        config_params = list(type(self).model_fields.keys())
        config_params.remove('class_name')
        return config_params

    def get_set_params(self, ignore: List[str]=[]) -> dict:
        """Get a dictionary of explicitly set parameters.
        
        Args:
            ignore: List of parameter names to ignore
        
        Returns:
            dict: Dictionary of explicitly set parameters, excluding 'class_name' and ignored parameters
        """
        explicitly_set_fields = {field: getattr(self, field) for field in self.model_fields_set}
        if self.kwargs:
            explicitly_set_fields.update(self.kwargs)
        for field in ignore:
            explicitly_set_fields.pop(field, None)
        explicitly_set_fields.pop('class_name', None)
        return explicitly_set_fields

def get_set_params(self, ignore: List[str]=[]) -> dict:
    """Get a dictionary of explicitly set parameters.
        
        Args:
            ignore: List of parameter names to ignore
        
        Returns:
            dict: Dictionary of explicitly set parameters, excluding 'class_name' and ignored parameters
        """
    explicitly_set_fields = {field: getattr(self, field) for field in self.model_fields_set}
    if self.kwargs:
        explicitly_set_fields.update(self.kwargs)
    for field in ignore:
        explicitly_set_fields.pop(field, None)
    explicitly_set_fields.pop('class_name', None)
    return explicitly_set_fields

class LLMOutputParser(Parser):
    """A basic parser for LLM-generated content.
    
    This parser stores the raw text generated by an LLM in the `.content` attribute
    and provides methods to extract structured data from this text using different
    parsing strategies.
    
    Attributes:
        content: The raw text generated by the LLM.
    """
    content: str = Field(default=None, exclude=True, description='the text generated by LLM')

    @classmethod
    def get_attrs(cls, return_type: bool=False) -> List[Union[str, tuple]]:
        """Returns the attributes of the LLMOutputParser class.
        
        Excludes ["class_name", "content"] by default.

        Args:
            return_type: Whether to return the type of the attributes along with their names.
        
        Returns:
            If `return_type` is True, returns a list of tuples where each tuple contains 
            the attribute name and its type. Otherwise, returns a list of attribute names.
        """
        attrs = []
        exclude_attrs = ['class_name', 'content']
        for field, field_info in cls.model_fields.items():
            if field not in exclude_attrs:
                if return_type:
                    field_type = get_type_name(field_info.annotation)
                    attrs.append((field, field_type))
                else:
                    attrs.append(field)
        return attrs

    @classmethod
    def get_attr_descriptions(cls) -> dict:
        """Returns the attributes and their descriptions.
        
        Returns:
            A dictionary mapping attribute names to their descriptions.
        """
        attrs = cls.get_attrs()
        results = {}
        for field_name, field_info in cls.model_fields.items():
            if field_name not in attrs:
                continue
            field_desc = field_info.description if field_info.description is not None else 'None'
            results[field_name] = field_desc
        return results

    @classmethod
    def get_content_data(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> dict:
        """Parses LLM-generated content into a dictionary.
        
        This method takes content from an LLM response and converts it to a structured
        dictionary based on the specified parsing mode.

        Args:
            content: The content to parse.
            parse_mode: The mode to parse the content. Must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. It will return a dictionary parsed from the first valid JSON string.
                - 'xml': Parses content using XML tags. It will return a dictionary parsed from the XML tags.
                - 'title': Parses content with Markdown-style headings.
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function.
            parse_func: The function to parse the content, only valid when parse_mode is 'custom'.
            **kwargs (Any): Additional arguments passed to the parsing function.
        
        Returns:
            The parsed content as a dictionary.
            
        Raises:
            ValueError: If parse_mode is invalid or if parse_func is not provided when parse_mode is 'custom'.
        """
        attrs = cls.get_attrs()
        if len(attrs) <= 0:
            return {}
        if parse_mode == 'str':
            parse_func = cls._parse_str_content
        elif parse_mode == 'json':
            parse_func = cls._parse_json_content
        elif parse_mode == 'xml':
            parse_func = cls._parse_xml_content
        elif parse_mode == 'title':
            parse_func = cls._parse_title_content
        elif parse_mode == 'custom':
            if parse_func is None:
                raise ValueError("`parse_func` must be provided when `parse_mode` is 'custom'.")
            signature = inspect.signature(parse_func)
            if 'content' not in signature.parameters:
                raise ValueError('`parse_func` must have an input argument `content`.')
            func_args = {}
            func_args['content'] = content
            for param_name, param in signature.parameters.items():
                if param_name == 'content':
                    continue
                if param_name in kwargs:
                    func_args[param_name] = kwargs[param_name]
            data = parse_func(**func_args)
            if not isinstance(data, dict):
                raise ValueError(f'The output of `parse_func` must be a dictionary, but found {type(data)}.')
            return data
        else:
            raise ValueError(f"Invalid value '{parse_mode}' detected for `parse_mode`. Available choices: {PARSER_VALID_MODE}")
        data = parse_func(content=content, **kwargs)
        return data

    @classmethod
    def _parse_str_content(cls, content: str, **kwargs) -> dict:
        """Parses content by setting all attributes to the raw content.
        
        Args:
            content: The content to parse.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping all attributes to the raw content.
        """
        attrs = cls.get_attrs()
        return {attr: content for attr in attrs}

    @classmethod
    def _parse_json_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting and parsing a JSON object. 
        If the content contains multiple JSON objects, only the first one will be used. 
        
        Args:
            content: The content containing a JSON object.
            **kwargs: Additional arguments (not used).
        
        Returns:
            The parsed JSON as a dictionary.
            
        Raises:
            ValueError: If the content doesn't contain a valid JSON object.
        """
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) > 0:
            json_str = extracted_json_list[0]
            try:
                data = yaml.safe_load(json_str)
                if not isinstance(data, dict):
                    if isinstance(data, list):
                        attrs = cls.get_attrs()
                        if len(attrs) == 1:
                            return {attrs[0]: data}
                        else:
                            raise ValueError('The generated content is a list of JSON strings, but the attribute name for the list is not specified. You should instruct the LLM to specify the attribute name for the list.')
                    else:
                        raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
            except Exception:
                raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
        else:
            raise ValueError(f'The following generated content does not contain JSON string!\n{content}')
        return data

    @classmethod
    def _parse_xml_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting values from XML tags.
        
        Each attribute of the parser is expected to be enclosed in XML tags
        with the attribute name as the tag name.
        
        Args:
            content: The content containing XML tags.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping attributes to their extracted values.
            
        Raises:
            ValueError: If the content is missing expected XML tags or if the
                        extracted values can't be converted to the expected types.
        """
        attrs_with_types: List[tuple] = cls.get_attrs(return_type=True)
        data = {}
        for attr, attr_type in attrs_with_types:
            attr_raw_value_list = parse_xml_from_text(text=content, label=attr)
            if len(attr_raw_value_list) > 0:
                attr_raw_value = attr_raw_value_list[0]
                try:
                    attr_value = parse_data_from_text(text=attr_raw_value, datatype=attr_type)
                except Exception:
                    raise ValueError(f'Cannot parse text: {attr_raw_value} into {attr_type} data!')
            else:
                raise ValueError(f'The following generated content does not contain xml label <{attr}>xxx</{attr}>!\n{content}')
            data[attr] = attr_value
        return data

    @classmethod
    def _parse_title_content(cls, content: str, title_format: str='## {title}', **kwargs) -> dict:
        """Parses content with markdown-style titles.
        
        Extracts sections from content that are divided by titles following
        the specified format described in `title_format`. The default format is "## {title}".
        For example:
        ```
        ## title1
        content1
        ## title2
        content2
        ```
        This content will be parsed into:
        ```
        {
            "title1": "content1",
            "title2": "content2"
        }
        ```
        Args:
            content: The content with title-divided sections.
            title_format: The format of the titles, default is "## {title}".
            **kwargs: Additional arguments (not used).

        Returns:
            A dictionary mapping title names to their section contents.
        """
        attrs: List[str] = cls.get_attrs()
        if not attrs:
            return {}
        output_titles = [title_format.format(title=attr) for attr in attrs]

        def is_output_title(text: str):
            for title in output_titles:
                if text.strip().lower().startswith(title.lower()):
                    return (True, title)
            return (False, None)
        data = {}
        current_output_name: str = None
        current_output_content: list = None
        for line in content.split('\n'):
            is_title, title = is_output_title(line)
            if is_title:
                if current_output_name is not None and current_output_content is not None:
                    data[current_output_name] = '\n'.join(current_output_content)
                current_output_content = []
                current_output_name = title.replace('#', '').strip()
                output_titles.remove(title)
            elif current_output_content is not None:
                current_output_content.append(line)
        if current_output_name is not None and current_output_content is not None:
            data[current_output_name] = '\n'.join(current_output_content)
        return data

    @classmethod
    def parse(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> 'LLMOutputParser':
        """Parses LLM-generated text into a structured parser instance.
        
        This is the main method for creating parser instances from LLM output.
        
        Args:
            content: The text generated by the LLM.
            parse_mode: The mode to parse the content, must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. Uses the first valid JSON string to create an instance of LLMOutputParser.
                - 'xml': Parses content using XML tags. Uses the XML tags to create an instance of LLMOutputParser.
                - 'title': Parses content with Markdown-style headings. Uses the Markdown-style headings to create an instance of LLMOutputParser. The default title format is "## {title}", you can change it by providing `title_format` parameter, which should be a string that contains `{title}` placeholder. 
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function. The `parse_func` must have a parameter named `content` and return a dictionary where the keys are the attribute names and the values are the parsed data. 
            parse_func: The function to parse the content, only valid when `parse_mode` is 'custom'.
            **kwargs (Any): Additional arguments passed to parsing functions, such as:
                - `title_format` for `parse_mode="title"`.
            
        Returns:
            An instance of LLMOutputParser containing the parsed data.
            
        Raises:
            ValueError: If parse_mode is invalid or if content is not a string.
        """
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
        if not isinstance(content, str):
            raise ValueError(f'The input to {cls.__name__}.parse should be a str, but found {type(content)}.')
        data = cls.get_content_data(content=content, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
        data.update({'content': content})
        parser = cls.from_dict(data, **kwargs)
        return parser

    def __str__(self) -> str:
        """
        Returns a string representation of the parser.
        """
        return self.to_str()

    def to_str(self, **kwargs) -> str:
        """
        Converts the parser to a string.
        """
        return self.content

    def get_structured_data(self) -> dict:
        """Extracts structured data from the parser.
        
        Returns:
            A dictionary containing only the defined attributes and their values,
            excluding metadata like class_name.
        """
        attrs = type(self).get_attrs()
        data = self.to_dict(ignore=['class_name'])
        structured_data = {key: value for key, value in data.items() if key in attrs}
        return structured_data

@classmethod
def parse(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> 'LLMOutputParser':
    """Parses LLM-generated text into a structured parser instance.
        
        This is the main method for creating parser instances from LLM output.
        
        Args:
            content: The text generated by the LLM.
            parse_mode: The mode to parse the content, must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. Uses the first valid JSON string to create an instance of LLMOutputParser.
                - 'xml': Parses content using XML tags. Uses the XML tags to create an instance of LLMOutputParser.
                - 'title': Parses content with Markdown-style headings. Uses the Markdown-style headings to create an instance of LLMOutputParser. The default title format is "## {title}", you can change it by providing `title_format` parameter, which should be a string that contains `{title}` placeholder. 
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function. The `parse_func` must have a parameter named `content` and return a dictionary where the keys are the attribute names and the values are the parsed data. 
            parse_func: The function to parse the content, only valid when `parse_mode` is 'custom'.
            **kwargs (Any): Additional arguments passed to parsing functions, such as:
                - `title_format` for `parse_mode="title"`.
            
        Returns:
            An instance of LLMOutputParser containing the parsed data.
            
        Raises:
            ValueError: If parse_mode is invalid or if content is not a string.
        """
    if parse_mode not in PARSER_VALID_MODE:
        raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
    if not isinstance(content, str):
        raise ValueError(f'The input to {cls.__name__}.parse should be a str, but found {type(content)}.')
    data = cls.get_content_data(content=content, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
    data.update({'content': content})
    parser = cls.from_dict(data, **kwargs)
    return parser

class DeleteMemories(Action):

    def __init__(self, name: str='DeleteMemories', description: str='Delete multiple memories by IDs', prompt: str='Delete the memories with IDs: {memory_ids}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or DeleteMemoriesInput
        outputs_format = outputs_format or DeleteMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> DeleteMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
        successes = memory.delete(action_input_data['memory_ids'])
        output = DeleteMemoriesOutput(successes=successes)
        if return_prompt:
            prompt = self.prompt.format(memory_ids=action_input_data['memory_ids'])
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> DeleteMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
    successes = memory.delete(action_input_data['memory_ids'])
    output = DeleteMemoriesOutput(successes=successes)
    if return_prompt:
        prompt = self.prompt.format(memory_ids=action_input_data['memory_ids'])
        return (output, prompt)
    return output

class DeleteMemories(Action):

    def __init__(self, name: str='DeleteMemories', description: str='Delete multiple memories by IDs', prompt: str='Delete the memories with IDs: {memory_ids}', inputs_format: ActionInput=None, outputs_format: ActionOutput=None, **kwargs):
        inputs_format = inputs_format or DeleteMemoriesInput
        outputs_format = outputs_format or DeleteMemoriesOutput
        super().__init__(name=name, description=description, prompt=prompt, inputs_format=inputs_format, outputs_format=outputs_format, **kwargs)

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> DeleteMemoriesOutput:
        if memory is None:
            raise ValueError('LongTermMemory instance required')
        action_input_attrs = self.inputs_format.get_attrs()
        action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
        successes = memory.delete(action_input_data['memory_ids'], delete_from_db=True)
        output = DeleteMemoriesOutput(successes=successes)
        if return_prompt:
            prompt = self.prompt.format(memory_ids=action_input_data['memory_ids'])
            return (output, prompt)
        return output

def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[Dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, memory: Optional[LongTermMemory]=None, **kwargs) -> DeleteMemoriesOutput:
    if memory is None:
        raise ValueError('LongTermMemory instance required')
    action_input_attrs = self.inputs_format.get_attrs()
    action_input_data = {attr: inputs.get(attr, []) for attr in action_input_attrs}
    successes = memory.delete(action_input_data['memory_ids'], delete_from_db=True)
    output = DeleteMemoriesOutput(successes=successes)
    if return_prompt:
        prompt = self.prompt.format(memory_ids=action_input_data['memory_ids'])
        return (output, prompt)
    return output

