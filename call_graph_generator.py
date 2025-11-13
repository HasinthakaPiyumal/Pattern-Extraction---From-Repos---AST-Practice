import ast
import os
import networkx as nx
import community as community_louvain
from collections import defaultdict

class FunctionCollector(ast.NodeVisitor):
    """Collect all top-level functions and class methods."""
    def __init__(self, filename):
        self.filename = filename
        self.functions = {}  # {full_func_name: node}
        self.class_defs = {}  # {full_class_name: node}
        self.current_class = None

    def visit_ClassDef(self, node):
        class_name = f"{self.filename}:{node.name}"
        self.class_defs[class_name] = node

        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        if self.current_class:
            # Class method
            full_name = f"{self.filename}:{self.current_class}.{node.name}"
        else:
            # Top-level function
            full_name = f"{self.filename}:{node.name}"
        self.functions[full_name] = node
        self.generic_visit(node)

class CallGraphVisitor(ast.NodeVisitor):
    """Collect function call edges for graph construction."""
    def __init__(self, filename):
        self.filename = filename
        self.current_function = None
        self.current_class = None
        self.calls = []

    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        if self.current_class:
            full_name = f"{self.filename}:{self.current_class}.{node.name}"
        else:
            full_name = f"{self.filename}:{node.name}"
        prev_function = self.current_function
        self.current_function = full_name
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_Call(self, node):
        if self.current_function:
            if isinstance(node.func, ast.Name):
                self.calls.append((self.current_function, node.func.id))
            elif isinstance(node.func, ast.Attribute):
                self.calls.append((self.current_function, node.func.attr))
        self.generic_visit(node)

def get_py_files(root_dir):
    py_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files

def build_call_graph(root_dir):
    G = nx.DiGraph()
    for file in get_py_files(root_dir):
        with open(file, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=file)
                visitor = CallGraphVisitor(file)
                visitor.visit(tree)
                for caller, callee in visitor.calls:
                    G.add_edge(caller, callee)
            except Exception as e:
                print(f"Error parsing {file}: {e}")
    return G

def collect_all_definitions(root_dir):
    """Return dicts for functions and classes with their AST nodes."""
    all_functions = {}
    all_classes = {}
    for file in get_py_files(root_dir):
        with open(file, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=file)
                collector = FunctionCollector(file)
                collector.visit(tree)
                all_functions.update(collector.functions)
                all_classes.update(collector.class_defs)
            except Exception as e:
                print(f"Error parsing {file}: {e}")
    return all_functions, all_classes

def cluster_and_save_code(repo_path):
    output_dir = f"result/repo_callgraph_clusters/{repo_path.split('/')[-1]}"
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Build graph
    graph = build_call_graph(repo_path)
    graph_undirected = graph.to_undirected()
    partition = community_louvain.best_partition(graph_undirected)

    # Step 2: Collect all functions and classes
    all_functions, all_classes = collect_all_definitions(repo_path)

    # Step 3: Build cluster mapping
    clusters = defaultdict(list)
    for node, cluster_id in partition.items():
        clusters[cluster_id].append(node)

    # Step 4: Write cluster files
    for cluster_id, nodes in clusters.items():
        file_path = os.path.join(output_dir, f"cluster_{cluster_id}.py")
        written_classes = set()  # Avoid duplicate class writing

        with open(file_path, "w", encoding="utf-8") as out:
            out.write(f"# Cluster {cluster_id}\n\n")

            for node_name in nodes:
                # If it's a class method, include the entire class
                for class_name, class_node in all_classes.items():
                    if node_name.startswith(class_name + ".") and class_name not in written_classes:
                        try:
                            source = ast.unparse(class_node)
                            out.write(source + "\n\n")
                            written_classes.add(class_name)
                        except Exception:
                            out.write(f"# Could not unparse {class_name}\n\n")

                # If it's a standalone function
                if node_name in all_functions:
                    try:
                        source = ast.unparse(all_functions[node_name])
                        out.write(source + "\n\n")
                    except Exception:
                        out.write(f"# Could not unparse {node_name}\n\n")

        print(f"✅ cluster_{cluster_id}.py saved with {len(nodes)} entries")

    print("\nAll cluster code files are in:", output_dir)


if __name__ == "__main__":
    cloned_repo_dir = "repos/cloned_repos"
    for repo_name in os.listdir(cloned_repo_dir):
        repo_path = os.path.join(cloned_repo_dir, repo_name)
        if os.path.isdir(repo_path):
            print(f"\nProcessing repository: {repo_name}")
            cluster_and_save_code(repo_path)

    print("\nAll repositories processed.")
    print("=" * 120)