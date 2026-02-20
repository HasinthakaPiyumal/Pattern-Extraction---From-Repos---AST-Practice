import ast
import os
import re
import json
import argparse
import networkx as nx
import community as community_louvain
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum


class LanguageType(str, Enum):
    PYTHON = "python"
    JAVA = "java"


@dataclass(frozen=True)
class CallGraphConfig:
    language: LanguageType


def is_python_like(language: LanguageType) -> bool:
    return language == LanguageType.PYTHON


def is_java_like(language: LanguageType) -> bool:
    return language == LanguageType.JAVA

class FunctionCollector(ast.NodeVisitor):
    """Collect all top-level functions and class methods."""
    def __init__(self, filename):
        self.filename = filename
        self.functions = {}  # {full_func_name: node}
        self.class_defs = {}  # {full_class_name: node}
        self.class_stack = []  # Fix: track nested classes properly

    @property
    def current_class(self):
        return ".".join(self.class_stack) if self.class_stack else None

    def visit_ClassDef(self, node):
        class_name = f"{self.filename}:{self.current_class}.{node.name}" if self.current_class else f"{self.filename}:{node.name}"
        self.class_defs[class_name] = node

        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def _visit_function(self, node):
        if self.current_class:
            full_name = f"{self.filename}:{self.current_class}.{node.name}"
        else:
            full_name = f"{self.filename}:{node.name}"
        self.functions[full_name] = node
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    # Fix: handle async def functions
    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

class CallGraphVisitor(ast.NodeVisitor):
    """Collect function call edges for graph construction."""
    def __init__(self, filename):
        self.filename = filename
        self.current_function = None
        self.class_stack = []  # Fix: track nested classes properly
        self.calls = []

    @property
    def current_class(self):
        return ".".join(self.class_stack) if self.class_stack else None

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def _visit_function(self, node):
        if self.current_class:
            full_name = f"{self.filename}:{self.current_class}.{node.name}"
        else:
            full_name = f"{self.filename}:{node.name}"
        prev_function = self.current_function
        self.current_function = full_name
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    # Fix: handle async def functions
    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def visit_Call(self, node):
        if self.current_function:
            if isinstance(node.func, ast.Name):
                self.calls.append((self.current_function, node.func.id))
            elif isinstance(node.func, ast.Attribute):
                self.calls.append((self.current_function, node.func.attr))
        self.generic_visit(node)

def get_target_files(root_dir, language: LanguageType):
    if is_python_like(language):
        target_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py") or file.endswith(".ipynb"):
                    target_files.append(os.path.join(root, file))
        return target_files

    if is_java_like(language):
        target_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".java") or file.endswith(".class"):
                    target_files.append(os.path.join(root, file))
        return target_files

    raise ValueError(f"Unsupported language type: {language}")


def build_python_graph(py_files):
    G = nx.DiGraph()
    for file in py_files:
        if not file.endswith(".py"):
            continue
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


def _strip_ipython_magics(source: str) -> str:
    """Remove IPython magic (%) and shell (!) lines that break ast.parse."""
    cleaned_lines = []
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("%") or stripped.startswith("!"):
            cleaned_lines.append("\n")  # preserve line numbers
        else:
            cleaned_lines.append(line)
    return "".join(cleaned_lines)


def build_ipynb_graph(ipynb_files):
    G = nx.DiGraph()
    for file in ipynb_files:
        if not file.endswith(".ipynb"):
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                notebook = json.load(f)
            cells = notebook.get("cells", [])
            for idx, cell in enumerate(cells):
                if cell.get("cell_type") != "code":
                    continue
                source = "".join(cell.get("source", []))
                if not source.strip():
                    continue
                source = _strip_ipython_magics(source)
                cell_name = f"{file}:cell_{idx}"
                tree = ast.parse(source, filename=cell_name)
                visitor = CallGraphVisitor(cell_name)
                visitor.visit(tree)
                for caller, callee in visitor.calls:
                    G.add_edge(caller, callee)
        except Exception as e:
            print(f"Error parsing notebook {file}: {e}")
    return G


def build_java_class_graph(class_files):
    """Lightweight class dependency graph from .class constant pool descriptors."""
    G = nx.DiGraph()
    descriptor_pattern = re.compile(r"L([A-Za-z0-9_/$]+);")

    for file in class_files:
        # Fix: skip non-.class files so .java files aren't read as binary
        if not file.endswith(".class"):
            continue
        caller = f"{file}:{os.path.splitext(os.path.basename(file))[0]}"
        G.add_node(caller)
        try:
            with open(file, "rb") as f:
                blob = f.read().decode("latin1", errors="ignore")
            for ref in descriptor_pattern.findall(blob):
                callee = ref.replace("/", ".")
                if callee:
                    G.add_edge(caller, callee)
        except Exception as e:
            print(f"Error parsing class file {file}: {e}")

    return G


def build_java_source_graph(java_files):
    """Lightweight call graph for Java source based on regex extraction."""
    G = nx.DiGraph()
    class_pattern = re.compile(r"\bclass\s+([A-Za-z_][\w]*)\b")
    method_pattern = re.compile(
        r"\b(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:[\w<>\[\]]+\s+)+([A-Za-z_][\w]*)\s*\([^;{}]*\)\s*\{"
    )
    call_pattern = re.compile(r"\b([A-Za-z_][\w]*)\s*\(")

    for file in java_files:
        if not file.endswith(".java"):
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            class_match = class_pattern.search(content)
            class_name = class_match.group(1) if class_match else os.path.splitext(os.path.basename(file))[0]
            current_function = f"{file}:{class_name}.<init>"

            for line in content.splitlines():
                method_match = method_pattern.search(line)
                if method_match:
                    method_name = method_match.group(1)
                    if method_name != class_name:
                        current_function = f"{file}:{class_name}.{method_name}"

                for callee in call_pattern.findall(line):
                    if callee in {"if", "for", "while", "switch", "catch", "return", "new", "super", "this"}:
                        continue
                    G.add_edge(current_function, callee)
        except Exception as e:
            print(f"Error parsing Java source {file}: {e}")

    return G

def _resolve_callees(graph, all_defined_names):
    """Resolve bare callee names to fully-qualified names when a unique match exists.

    Without this, callees are bare (e.g. 'foo') while callers are qualified
    (e.g. 'file.py:Class.method'), creating disconnected nodes.
    """
    # Build lookup: bare_name -> set of qualified names
    bare_to_qualified = defaultdict(set)
    for qname in all_defined_names:
        # Extract the bare name from patterns like 'file:Class.method' or 'file:func'
        bare = qname.rsplit(".", 1)[-1] if "." in qname else qname.rsplit(":", 1)[-1]
        bare_to_qualified[bare].add(qname)

    resolved = nx.DiGraph()
    for caller, callee in graph.edges():
        matches = bare_to_qualified.get(callee, set())
        if len(matches) == 1:
            resolved.add_edge(caller, next(iter(matches)))
        else:
            # Keep original edge if ambiguous or no match
            resolved.add_edge(caller, callee)

    # Preserve isolated nodes
    for node in graph.nodes():
        if not resolved.has_node(node):
            resolved.add_node(node)

    return resolved


def build_call_graph(root_dir, config: CallGraphConfig):
    files = get_target_files(root_dir, config.language)

    if is_python_like(config.language):
        py_graph = build_python_graph(files)
        ipynb_graph = build_ipynb_graph(files)
        graph = nx.compose(py_graph, ipynb_graph)
    elif is_java_like(config.language):
        java_source_graph = build_java_source_graph(files)
        java_class_graph = build_java_class_graph(files)
        graph = nx.compose(java_source_graph, java_class_graph)
    else:
        raise ValueError(f"Unsupported language type: {config.language}")

    # Fix: resolve bare callee names to qualified names for better clustering
    all_defined_names = set(graph.nodes())
    return _resolve_callees(graph, all_defined_names)

def _collect_java_definitions(root_dir):
    """Collect Java class and method source code for cluster output."""
    all_functions = {}  # {qualified_name: source_string}
    all_classes = {}    # {qualified_name: source_string}
    class_pattern = re.compile(r"\bclass\s+([A-Za-z_][\w]*)\b")
    method_pattern = re.compile(
        r"\b(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:[\w<>\[\]]+\s+)+([A-Za-z_][\w]*)\s*\([^;{}]*\)\s*\{"
    )

    target_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".java"):
                target_files.append(os.path.join(root, file))

    for file in target_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            class_match = class_pattern.search(content)
            class_name = class_match.group(1) if class_match else os.path.splitext(os.path.basename(file))[0]
            qualified_class = f"{file}:{class_name}"
            all_classes[qualified_class] = content  # store entire file as class source

            for match in method_pattern.finditer(content):
                method_name = match.group(1)
                if method_name != class_name:
                    qualified_method = f"{file}:{class_name}.{method_name}"
                    # Extract method body (best-effort: from match to next closing brace at same indent)
                    all_functions[qualified_method] = None  # mark as known; source comes from class
        except Exception as e:
            print(f"Error collecting Java definitions from {file}: {e}")

    return all_functions, all_classes


def collect_all_definitions(root_dir, config: CallGraphConfig):
    """Return dicts for functions and classes with their AST/source nodes."""
    all_functions = {}
    all_classes = {}

    target_files = get_target_files(root_dir, config.language)

    if is_python_like(config.language):
        for file in target_files:
            if file.endswith(".py"):
                with open(file, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=file)
                        collector = FunctionCollector(file)
                        collector.visit(tree)
                        all_functions.update(collector.functions)
                        all_classes.update(collector.class_defs)
                    except Exception as e:
                        print(f"Error parsing {file}: {e}")

            elif file.endswith(".ipynb"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        notebook = json.load(f)
                    cells = notebook.get("cells", [])
                    for idx, cell in enumerate(cells):
                        if cell.get("cell_type") != "code":
                            continue
                        source = "".join(cell.get("source", []))
                        if not source.strip():
                            continue
                        source = _strip_ipython_magics(source)
                        pseudo_file = f"{file}:cell_{idx}"
                        tree = ast.parse(source, filename=pseudo_file)
                        collector = FunctionCollector(pseudo_file)
                        collector.visit(tree)
                        all_functions.update(collector.functions)
                        all_classes.update(collector.class_defs)
                except Exception as e:
                    print(f"Error parsing notebook {file}: {e}")

    elif is_java_like(config.language):
        # Fix: collect Java definitions so cluster output contains actual code
        all_functions, all_classes = _collect_java_definitions(root_dir)

    return all_functions, all_classes

def cluster_and_save_code(repo_path, config: CallGraphConfig):
    # Fix: use os.path.basename to handle trailing slashes safely
    repo_name = os.path.basename(repo_path.rstrip("/"))
    output_dir = f"result/ms_repo_callgraph_clusters/{repo_name}_{config.language.value}"
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Build graph
    graph = build_call_graph(repo_path, config)
    if graph.number_of_nodes() == 0:
        print(f"No nodes found for {repo_path} ({config.language.value})")
        return

    graph_undirected = graph.to_undirected()
    if graph_undirected.number_of_edges() == 0:
        partition = {node: idx for idx, node in enumerate(graph_undirected.nodes())}
    else:
        partition = community_louvain.best_partition(graph_undirected)

    # Step 2: Collect all functions and classes
    all_functions, all_classes = collect_all_definitions(repo_path, config)

    # Step 3: Build cluster mapping
    clusters = defaultdict(list)
    for node, cluster_id in partition.items():
        clusters[cluster_id].append(node)

    # Fix: use correct file extension per language
    cluster_ext = ".java" if is_java_like(config.language) else ".py"

    # Build prefix lookup for efficient class-method matching
    class_prefix_map = {}
    for class_name in all_classes:
        class_prefix_map[class_name + "."] = class_name

    # Step 4: Write cluster files
    for cluster_id, nodes in clusters.items():
        file_path = os.path.join(output_dir, f"cluster_{cluster_id}{cluster_ext}")
        written_classes = set()  # Avoid duplicate class writing

        with open(file_path, "w", encoding="utf-8") as out:
            out.write(f"// Cluster {cluster_id}\n\n" if is_java_like(config.language) else f"# Cluster {cluster_id}\n\n")

            for node_name in nodes:
                # If it's a class method, include the entire class
                for prefix, class_name in class_prefix_map.items():
                    if node_name.startswith(prefix) and class_name not in written_classes:
                        class_source = all_classes[class_name]
                        if is_java_like(config.language):
                            # Java: class_source is the raw file content string
                            out.write(class_source + "\n\n")
                        else:
                            try:
                                source = ast.unparse(class_source)
                                out.write(source + "\n\n")
                            except Exception:
                                out.write(f"# Could not unparse {class_name}\n\n")
                        written_classes.add(class_name)

                # If it's a standalone function
                if node_name in all_functions:
                    func_value = all_functions[node_name]
                    if func_value is None:
                        # Java method — source already written via class
                        pass
                    else:
                        try:
                            source = ast.unparse(func_value)
                            out.write(source + "\n\n")
                        except Exception:
                            out.write(f"# Could not unparse {node_name}\n\n")
                else:
                    # Unresolved node reference
                    comment = "//" if is_java_like(config.language) else "#"
                    out.write(f"{comment} Node: {node_name}\n")

        print(f"✅ cluster_{cluster_id}{cluster_ext} saved with {len(nodes)} entries")

    print("\nAll cluster code files are in:", output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate call graphs and clustered code by language type")
    parser.add_argument(
        "--language",
        type=str,
        choices=[lang.value for lang in LanguageType],
        default=LanguageType.PYTHON.value,
        help="Language type for call graph generation",
    )
    parser.add_argument(
        "--repos-dir",
        type=str,
        default="repos/cloned_ms_repos",
        help="Directory containing repositories",
    )
    args = parser.parse_args()

    config = CallGraphConfig(language=LanguageType(args.language))

    cloned_repo_dir = args.repos_dir
    for repo_name in os.listdir(cloned_repo_dir):
        repo_path = os.path.join(cloned_repo_dir, repo_name)
        if os.path.isdir(repo_path):
            print(f"\nProcessing repository: {repo_name} [{config.language.value}]")
            cluster_and_save_code(repo_path, config)

    print("\nAll repositories processed.")
    print("=" * 120)