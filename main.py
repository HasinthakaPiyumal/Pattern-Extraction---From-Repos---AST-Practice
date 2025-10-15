import os,json
from ast_extractor import extract_structure

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

    repo_path = "/home/hasinthaka/Documents/Experiments/Pattern Extraction - From Repos/X-AnyLabeling"
    output_file = "repo_structure.json"
    structure = extract_repo_structure(repo_path, extract_structure)
    save_structure_to_file(structure, output_file)
    for file, details in structure.items():
        print(f"File: {file}")
        print(f"Imports: {details['imports']}")
        print(f"Classes: {details['classes']}")
        print(f"Functions: {details['functions']}")
        print("-" * 40)
