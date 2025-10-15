import os,json
from ast_extractor import extract_structure
from call_graph_generator import build_call_graph

def get_python_file_list_from_repo(repo_path):
    python_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)

    return python_files

def extract_repo_structure(repo_path, extractor,):
    repo_structure = {}
    for file_path in get_python_file_list_from_repo(repo_path):
        relative_path = os.path.relpath(file_path, repo_path)
        repo_structure[relative_path] = extractor(file_path,repo_path)
    return repo_structure

def save_structure_to_file(structure, output_file):
    with open(output_file, "w") as f:
        json.dump(structure, f, indent=4)

if __name__ == "__main__":

    repo_path = "repos/Styleformer"
    output_file = "result/repo_structure_Styleformer.json"
    structure = extract_repo_structure(repo_path, extract_structure)
    call_graph = build_call_graph(repo_path)
    # structure["call_graph_edges"] = call_graph.edges()
    save_structure_to_file(structure, output_file)
    # print(call_graph.edges())
    for file, details in structure.items():
        print(f"01 File: ***************\n{file}")
        print(f"02 Imports: *****************\n{details['imports']}")
        print(f"03 Classes: *****************\n{details['classes']}")
        print(f"04 Functions: *****************\n{details['functions']}")
        # print(f"Call Graph Successors: \n{list(call_graph.successors(repo_path+file+":"+details['functions'][0])) if details['functions'] else []}")
        print("=" * 120)
