import javalang
import networkx as nx


def parse_java_file(file_path):
    with open(file_path, "r") as f:
        source = f.read()
    return javalang.parse.parse(source)


class JavaCodeAnalyzer:
    def __init__(self):
        self.imports = []
        self.classes = []
        self.methods = []

    def analyze(self, tree):
        # Imports
        self.imports = [imp.path for imp in tree.imports]

        # Classes and methods
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            methods = [m.name for m in node.methods]
            self.classes.append({"class_name": node.name, "methods": methods})
            self.methods.extend([(node.name, m.name) for m in node.methods])


class JavaCallGraphBuilder:
    def __init__(self, filename):
        self.filename = filename
        self.G = nx.DiGraph()

    def build(self, tree):
        # Traverse all class and method nodes
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            for method in class_node.methods:
                current_method = f"{self.filename}:{class_node.name}.{method.name}"

                # Look for method invocations inside the method body
                if not method.body:
                    continue
                for path, node in method.filter(javalang.tree.MethodInvocation):
                    callee = node.member
                    self.G.add_edge(current_method, callee)

    def get_function_successors(self, analyzer):
        successors = {}
        for cls, func in analyzer.methods:
            key = f"{self.filename}:{cls}.{func}"
            try:
                successors[func] = list(self.G.successors(key))
            except:
                successors[func] = []
        return successors


def extract_structure(file_path, parent_path=""):
    tree = parse_java_file(file_path)

    analyzer = JavaCodeAnalyzer()
    analyzer.analyze(tree)

    call_graph = JavaCallGraphBuilder(file_path)
    call_graph.build(tree)

    function_successors = call_graph.get_function_successors(analyzer)

    return {
        "file_name": file_path.replace(parent_path, ""),
        "imports": analyzer.imports,
        "classes": analyzer.classes,
        "functions": function_successors,
    }
