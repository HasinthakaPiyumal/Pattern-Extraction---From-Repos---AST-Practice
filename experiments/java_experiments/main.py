import os,json
from ast_extractor_java import extract_structure

def get_java_file_list_from_repo(repo_path):
    python_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".java") or file.endswith(".class"):
                yield os.path.join(root, file)

    return python_files

def extract_repo_structure(repo_path, extractor,):
    repo_structure = {}
    for file_path in get_java_file_list_from_repo(repo_path):
        relative_path = os.path.relpath(file_path, repo_path)
        try:
            repo_structure[relative_path] = extractor(file_path, repo_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    return repo_structure

def save_structure_to_file(structure, output_file):
    with open(output_file, "w") as f:
        json.dump(structure, f, indent=4)

if __name__ == "__main__":

    repo_path = "repos/p-mart-Repository-Programs/Ant v1.1.0"
    output_file = "result/repo_structure_random_ai_pattern4.json"
    structure = extract_repo_structure(repo_path, extract_structure)
    save_structure_to_file(structure, output_file)
    for file, details in structure.items():
        print(f"01 File: ***************\n{file}")
        print(f"02 Imports: *****************\n{details['imports']}")
        print(f"03 Classes: *****************\n{details['classes']}")
        print(f"04 Functions: *****************\n{details['functions']}")
        print("=" * 120)
