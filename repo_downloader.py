# @title Fast Parallel GitHub Cloner
import json
import os
import subprocess
import concurrent.futures

clone_dir = "repos/cloned_repos"
json_file = "data/finalized-repost.json"

os.makedirs(clone_dir, exist_ok=True)

with open(json_file, "r") as f:
    repo_list = json.load(f)

def clone_repo(git_url):
    repo_name = git_url.split("/")[-1]
    dest_path = os.path.join(clone_dir, repo_name)

    if os.path.exists(dest_path):
        return f"✅ {repo_name} already exists, skipping."

    # Run git clone with shallow depth and quiet output
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", git_url, dest_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if result.returncode == 0:
        return f"✅ Cloned {repo_name}"
    else:
        return f"❌ Failed {repo_name}"

# Run clones in parallel threads (Colab CPU handles I/O well)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = []
    for repo in repo_list:
        git_url = repo.get("svn_url")
        if git_url:
            futures.append(executor.submit(clone_repo, git_url))

    for future in concurrent.futures.as_completed(futures):
        print(future.result())
