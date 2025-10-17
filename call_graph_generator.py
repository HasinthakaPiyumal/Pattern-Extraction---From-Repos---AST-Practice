import ast
import os
import networkx as nx
import community as community_louvain
class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.current_function = None
        self.calls = []

    def visit_FunctionDef(self, node):
        prev_function = self.current_function
        self.current_function = f"{self.filename}:{node.name}"
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
            tree = ast.parse(f.read(), filename=file)
            visitor = CallGraphVisitor(file)
            visitor.visit(tree)
            for caller, callee in visitor.calls:
                G.add_edge(caller, callee)
    return G

if __name__ == "__main__":
    repo_path = "repos/sample"
    graph = build_call_graph(repo_path)

    graph_undirected = graph.to_undirected()
    partition = community_louvain.best_partition(graph_undirected)

    from collections import defaultdict
    clusters = defaultdict(list)
    for node, cluster_id in partition.items():
        clusters[cluster_id].append(node)
    output_dir = "call_graph_output"
    for cluster_id, nodes in clusters.items():
        print(f"Cluster {cluster_id}:")
        for node in nodes:
            print(f"  - {node}")
        print()
    # print("Call Graph:")
    # for caller, callee in graph.edges():
    #     print(f"{caller} -> {callee}")
    #     print(f"  Successors: {list(graph.successors(caller))}")
