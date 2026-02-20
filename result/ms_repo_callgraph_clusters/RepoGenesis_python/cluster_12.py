# Cluster 12

def test_repository(repo_name: str, repo_path: str, port_base: int) -> Tuple[bool, str, str]:
    """
    Test repository deployment.
    Returns (success: bool, message: str, repo_type: str)
    """
    repo_type, config_path = detect_repo_type(repo_path)
    if repo_type == 'Java':
        success, message = test_java_repository(repo_name, repo_path, config_path, port_base)
        return (success, message, 'Java')
    elif repo_type == 'Python':
        success, message = test_python_repository(repo_name, repo_path, config_path, port_base)
        return (success, message, 'Python')
    else:
        return (False, 'Unknown or missing build config', 'Unknown')

# Node: detect_repo_type
# Node: test_java_repository
# Node: test_python_repository
