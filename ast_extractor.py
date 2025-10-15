import ast
import networkx as nx

def parse_python_file(file_path):
    with open(file_path, "r") as f:
        source = f.read()
    return ast.parse(source)

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        self.classes.append({"class_name": node.name, "methods": methods})
        self.generic_visit(node)

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


def extract_structure(file_path,parent_path=""):
    G = nx.DiGraph()
    tree = parse_python_file(file_path)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    visitor = CallGraphVisitor(file_path)
    visitor.visit(tree)
    for caller, callee in visitor.calls:
        G.add_edge(caller, callee)
    function_successors = {}
    for file in analyzer.functions:
        try:
            function_successors[file] = list(G.successors(f"{file_path}:{file}"))
        except:
            function_successors[file] = []
    return {
        "file_name": file_path.replace(parent_path,""),
        "imports": analyzer.imports,
        "classes": analyzer.classes,
        "functions": function_successors
    }
