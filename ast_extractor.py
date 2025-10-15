import ast

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


def extract_structure(file_path,parent_path=""):
    tree = parse_python_file(file_path)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return {
        "file_name": file_path.replace(parent_path,""),
        "imports": analyzer.imports,
        "classes": analyzer.classes,
        "functions": analyzer.functions
    }
