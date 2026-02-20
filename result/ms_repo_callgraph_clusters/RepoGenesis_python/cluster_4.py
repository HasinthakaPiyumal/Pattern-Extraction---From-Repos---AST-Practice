# Cluster 4

# Node: print
# Node: lower
# Node: open
# Node: read
def search_implementation(repo_path: str, endpoint: Dict[str, str]) -> bool:
    """Search for implementation of an API endpoint in the codebase"""
    method = endpoint['method']
    path = endpoint['path']
    clean_path = re.sub('[{}<>:]', '', path)
    path_parts = [p for p in clean_path.split('/') if p and (not p.startswith(':'))]
    search_patterns = []
    search_patterns.append(f'@app.{method.lower()}')
    search_patterns.append(f'@router.{method.lower()}')
    search_patterns.append(f'@bp.{method.lower()}')
    search_patterns.append(f'methods=["{method}"')
    search_patterns.append(f"methods=['{method}'")
    for part in path_parts:
        search_patterns.append(f"'{part}'")
        search_patterns.append(f'"{part}"')
    search_patterns.append(f'@{method.title()}Mapping')
    search_patterns.extend(path_parts)
    extensions = ['.py', '.java', '.js', '.ts', '.kt']
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'target', 'build', 'test', 'tests', '.pytest_cache']]
        for file in files:
            if any((file.endswith(ext) for ext in extensions)):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in search_patterns:
                            if pattern and pattern in content:
                                if path in content or any((part in content for part in path_parts if len(part) > 3)):
                                    return True
                except Exception:
                    continue
    return False

# Node: sub
# Node: split
# Node: title
# Node: walk
# Node: endswith
def parse_repo_dirname(dirname: str) -> Dict[str, str]:
    """
    Parse repository directory name to extract metadata
    
    Expected format: repo_readme_MMDD_IDE_model_Language
    Example: repo_readme_1216_antigravity_gemini3pro_Java
    """
    parts = dirname.split('_')
    date_idx = None
    for i, part in enumerate(parts):
        if part.isdigit() and len(part) == 4:
            date_idx = i
            break
    if date_idx is None:
        return None
    date = parts[date_idx]
    language = None
    language_idx = None
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].lower() in ['java', 'python']:
            language = parts[i].capitalize()
            language_idx = i
            break
    if language is None:
        return None
    ide_model_parts = parts[date_idx + 1:language_idx]
    if not ide_model_parts:
        return None
    ide_raw = ide_model_parts[0].lower()
    if ide_raw == 'vscode':
        ide = 'Copilot'
    elif ide_raw == 'antigravity':
        ide = 'Antigravity'
    else:
        ide = ide_model_parts[0].capitalize()
    model = '_'.join(ide_model_parts[1:]) if len(ide_model_parts) > 1 else 'unknown'
    return {'date': date, 'ide': ide, 'model': model, 'language': language, 'full_name': dirname}

# Node: enumerate
# Node: isdigit
# Node: capitalize
# Node: values
def main():
    base_path = 'code/exps/repos_IDE'
    print('Starting API Coverage Calculation for repos_IDE...')
    print(f'Base path: {base_path}')
    results = calculate_ac_for_all_repos(base_path)
    output_json = 'code/api_coverage_ide_results.json'
    results_serializable = {f'{ide}|{model}|{language}': data for (ide, model, language), data in results.items()}
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)
    print(f'\n\nResults saved to: {output_json}')
    latex_table = generate_latex_table(results)
    output_tex = 'code/api_coverage_ide_table.tex'
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    print(f'LaTeX table saved to: {output_tex}')
    print('\n' + '=' * 80)
    print('SUMMARY')
    print('=' * 80)
    total_configs = len(results)
    total_apis = sum((data['total_apis'] for data in results.values()))
    total_implemented = sum((data['implemented_apis'] for data in results.values()))
    overall_ac = total_implemented / total_apis if total_apis > 0 else 0
    print(f'\nTotal configurations analyzed: {total_configs}')
    print(f'Total API endpoints found: {total_apis}')
    print(f'Total implemented: {total_implemented}')
    print(f'Overall API Coverage (AC): {overall_ac:.2%}')
    print('\n' + '=' * 80)
    print('BY CONFIGURATION')
    print('=' * 80)
    for (ide, model, language), data in sorted(results.items()):
        print(f'\n{ide} - {model} - {language}:')
        print(f'  Total APIs: {data['total_apis']}')
        print(f'  Implemented: {data['implemented_apis']}')
        print(f'  Coverage: {data['coverage']:.2%}')
        print(f'  Repositories: {len(data['repos'])}')
    print('\n' + latex_table)

# Node: calculate_ac_for_all_repos
# Node: generate_latex_table
# Node: write
def count_tests_ast(test_dir):
    """Count test functions in a directory using AST."""
    total_tests = 0
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py') and (file.startswith('test_') or file.endswith('_test.py')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=file_path)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                            total_tests += 1
                except Exception as e:
                    print(f'Error parsing {file_path}: {e}')
    return total_tests

# Node: parse
def find_files_recursive(root_dir, filename):
    """Recursively find all files with a given name in a directory."""
    matches = []
    for root, dirnames, filenames in os.walk(root_dir):
        if filename in filenames:
            matches.append(os.path.join(root, filename))
    return matches

def count_lines_and_tokens(directory):
    """Count files, lines of code, and estimate tokens."""
    total_files = 0
    total_lines = 0
    total_tokens = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                ext = os.path.splitext(file)[1]
                if ext not in ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h', '.sh', '.md']:
                    continue
                path = os.path.join(root, file)
                total_files += 1
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        total_lines += len(lines)
                        tokens = len(re.findall('\\w+|[^\\w\\s]', content))
                        total_tokens += tokens
                except Exception:
                    pass
    return (total_files, total_lines, total_tokens)

# Node: splitext
# Node: splitlines
def run_pytest(test_dir, answer_dir):
    """Run pytest and return the output."""
    print(f'Running tests in {test_dir}...')
    cmd = [sys.executable, '-m', 'pytest', test_dir, f'--cov={answer_dir}', '--cov-report=term-missing']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return (result.stdout + result.stderr, result.returncode)
    except subprocess.TimeoutExpired:
        return ('TIMEOUT', -1)

def search_implementation(repo_path: str, endpoint: Dict[str, str]) -> bool:
    """
    Search for implementation of an API endpoint in the codebase
    
    Args:
        repo_path: Path to repository
        endpoint: Endpoint dictionary with method, path, description
    
    Returns:
        True if endpoint appears to be implemented, False otherwise
    """
    method = endpoint['method']
    path = endpoint['path']
    description = endpoint['description']
    search_patterns = []
    clean_path = re.sub('[{}<>:]', '', path)
    path_parts = [p for p in clean_path.split('/') if p and (not p.startswith(':'))]
    if method == 'FEATURE':
        search_patterns.append(path.lower().replace(' ', '_'))
        search_patterns.append(path.lower().replace(' ', ''))
    else:
        search_patterns.append(f'@app.{method.lower()}')
        search_patterns.append(f'@router.{method.lower()}')
        search_patterns.append(f'@bp.{method.lower()}')
        search_patterns.append(f'methods=["{method}"')
        search_patterns.append(f"methods=['{method}'")
        for part in path_parts:
            search_patterns.append(f"'{part}'")
            search_patterns.append(f'"{part}"')
        search_patterns.append(f'app.{method.lower()}')
        search_patterns.append(f'router.{method.lower()}')
        search_patterns.append(f'@{method.title()}Mapping')
        search_patterns.extend(path_parts)
    extensions = ['.py', '.java', '.js', '.ts', '.kt']
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'target', 'build', 'test', 'tests', '.pytest_cache']]
        for file in files:
            if any((file.endswith(ext) for ext in extensions)):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in search_patterns:
                            if pattern and pattern in content:
                                if method != 'FEATURE':
                                    if path in content or any((part in content for part in path_parts if len(part) > 3)):
                                        return True
                                else:
                                    return True
                except Exception as e:
                    continue
    return False

def main():
    repo_base_path = 'code/exps/repos/repo_readme_1219_deepcode_gpt-5.2'
    print('Starting API Coverage Calculation...')
    print(f'Repository base path: {repo_base_path}')
    results = calculate_api_coverage(repo_base_path)
    output_json = 'code/api_coverage_results.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f'\n\nResults saved to: {output_json}')
    latex_table = generate_latex_table(results)
    output_tex = 'code/api_coverage_table.tex'
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    print(f'LaTeX table saved to: {output_tex}')
    print('\n' + '=' * 80)
    print('SUMMARY')
    print('=' * 80)
    total_apis = sum((r['total_apis'] for r in results.values()))
    total_implemented = sum((r['implemented_apis'] for r in results.values()))
    overall_ac = total_implemented / total_apis if total_apis > 0 else 0
    print(f'\nTotal repositories analyzed: {len(results)}')
    print(f'Total API endpoints found: {total_apis}')
    print(f'Total implemented: {total_implemented}')
    print(f'Overall API Coverage (AC): {overall_ac:.2%}')
    print('\n' + latex_table)

# Node: calculate_api_coverage
def count_tests_java(test_dir):
    """Count test methods in a directory using javalang AST."""
    total_tests = 0
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tree = javalang.parse.parse(content)
                    for path, node in tree.filter(javalang.tree.MethodDeclaration):
                        is_test = False
                        if node.annotations:
                            for annotation in node.annotations:
                                if annotation.name == 'Test' or annotation.name.endswith('.Test'):
                                    is_test = True
                                    break
                                if 'ParameterizedTest' in annotation.name:
                                    is_test = True
                                    break
                        if not is_test and node.name.startswith('test'):
                            if len(path) >= 2:
                                parent = path[-2]
                                if isinstance(parent, javalang.tree.ClassDeclaration):
                                    if parent.extends and 'TestCase' in parent.extends.name:
                                        is_test = True
                                    elif parent.name.endswith('Test'):
                                        is_test = True
                        if is_test:
                            total_tests += 1
                except Exception as e:
                    print(f'Error parsing {file_path}: {e}')
                    try:
                        matches_annotation = re.findall('@Test', content)
                        matches_junit3 = re.findall('public\\s+void\\s+test\\w+', content)
                        count = 0
                        if matches_annotation:
                            count = len(matches_annotation)
                        elif matches_junit3:
                            count = len(matches_junit3)
                        if count > 0:
                            total_tests += count
                    except Exception as regex_e:
                        pass
    return total_tests

# Node: filter
def find_file_recursive(root_dir, filename):
    """Recursively find the first occurrence of a file."""
    for root, _, files in os.walk(root_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

def parse_java_test_output(answer_dir, stdout):
    """Parse test results from Surefire XML reports or stdout."""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    xml_files = []
    for root, _, files in os.walk(answer_dir):
        if 'target' in root and 'surefire-reports' in root:
            for file in files:
                if file.endswith('.xml') and file.startswith('TEST-'):
                    xml_files.append(os.path.join(root, file))
    if xml_files:
        print(f'Found {len(xml_files)} Surefire XML reports.')
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                n_tests = int(root.attrib.get('tests', 0))
                n_failures = int(root.attrib.get('failures', 0))
                n_errors = int(root.attrib.get('errors', 0))
                n_skipped = int(root.attrib.get('skipped', 0))
                failed += n_failures + n_errors
                skipped += n_skipped
                passed += n_tests - n_failures - n_errors - n_skipped
            except Exception as e:
                print(f'Error parsing {xml_file}: {e}')
        return (passed, failed, skipped)
    print('No Surefire XML reports found. Parsing stdout...')
    matches = re.findall('Tests run: (\\d+), Failures: (\\d+), Errors: (\\d+), Skipped: (\\d+)', stdout)
    if matches:
        for match in matches:
            n_tests, n_failures, n_errors, n_skipped = map(int, match)
            failed += n_failures + n_errors
            skipped += n_skipped
            passed += n_tests - n_failures - n_errors - n_skipped
    return (passed, failed, skipped)

# Node: getroot
# Node: map
def count_lines_and_tokens_java(directory):
    """Count files, lines of code, and estimate tokens for Java."""
    total_files = 0
    total_lines = 0
    total_tokens = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                path = os.path.join(root, file)
                total_files += 1
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        total_lines += len(lines)
                        tokens = len(re.findall('\\w+|[^\\w\\s]', content))
                        total_tokens += tokens
                except Exception:
                    pass
    return (total_files, total_lines, total_tokens)

def fix_pom_java_version(answer_dir):
    """
    Updates pom.xml to use Java 17 if it's set to lower version.
    """
    pom_path = os.path.join(answer_dir, 'pom.xml')
    if os.path.exists(pom_path):
        with open(pom_path, 'r') as f:
            content = f.read()
        new_content = content.replace('<maven.compiler.source>11</maven.compiler.source>', '<maven.compiler.source>17</maven.compiler.source>')
        new_content = new_content.replace('<maven.compiler.target>11</maven.compiler.target>', '<maven.compiler.target>17</maven.compiler.target>')
        new_content = new_content.replace('<source>11</source>', '<source>17</source>')
        new_content = new_content.replace('<target>11</target>', '<target>17</target>')
        if content != new_content:
            print('Upgraded pom.xml to Java 17')
            with open(pom_path, 'w') as f:
                f.write(new_content)

def search_implementation(repo_path: str, endpoint: Dict[str, str]) -> bool:
    """Search for implementation of an API endpoint in the codebase"""
    method = endpoint['method']
    path = endpoint['path']
    clean_path = re.sub('[{}<>:]', '', path)
    path_parts = [p for p in clean_path.split('/') if p and (not p.startswith(':'))]
    search_patterns = []
    search_patterns.append(f'@app.{method.lower()}')
    search_patterns.append(f'@router.{method.lower()}')
    search_patterns.append(f'@bp.{method.lower()}')
    search_patterns.append(f'methods=["{method}"')
    search_patterns.append(f"methods=['{method}'")
    for part in path_parts:
        search_patterns.append(f"'{part}'")
        search_patterns.append(f'"{part}"')
    search_patterns.append(f'@{method.title()}Mapping')
    search_patterns.extend(path_parts)
    extensions = ['.py', '.java', '.js', '.ts', '.kt']
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'target', 'build', 'test', 'tests', '.pytest_cache']]
        for file in files:
            if any((file.endswith(ext) for ext in extensions)):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in search_patterns:
                            if pattern and pattern in content:
                                if path in content or any((part in content for part in path_parts if len(part) > 3)):
                                    return True
                except Exception:
                    continue
    return False

def parse_agent_dirname(dirname: str) -> Dict[str, str]:
    """
    Parse agent repository directory name to extract metadata
    
    Expected format: repo_readme_MMDD_agent_model_Language
    Examples:
      - repo_readme_1204_msagent_gpt-5-mini_Python
      - repo_readme_1212_deepcode_gpt-5-mini_Java
    """
    parts = dirname.split('_')
    date_idx = None
    for i, part in enumerate(parts):
        if part.isdigit() and len(part) == 4:
            date_idx = i
            break
    if date_idx is None:
        return None
    date = parts[date_idx]
    language = None
    language_idx = None
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].lower() in ['java', 'python']:
            language = parts[i].capitalize()
            language_idx = i
            break
    if language is None:
        return None
    agent_model_parts = parts[date_idx + 1:language_idx]
    if not agent_model_parts:
        return None
    agent_raw = agent_model_parts[0].lower()
    agent_map = {'msagent': 'MS-Agent', 'metagpt': 'MetaGPT', 'deepcode': 'DeepCode', 'qwen': 'Qwen-Agent'}
    agent = agent_map.get(agent_raw, agent_model_parts[0].capitalize())
    model = '_'.join(agent_model_parts[1:]) if len(agent_model_parts) > 1 else 'unknown'
    return {'date': date, 'agent': agent, 'model': model, 'language': language, 'full_name': dirname}

def main():
    base_path = 'code/exps/repos'
    print('Starting API Coverage Calculation for Open-Source Agents...')
    print(f'Base path: {base_path}')
    results = calculate_ac_for_agents(base_path)
    output_json = 'code/api_coverage_agents_results.json'
    results_serializable = {f'{agent}|{model}|{language}': data for (agent, model, language), data in results.items()}
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)
    print(f'\n\nResults saved to: {output_json}')
    latex_table = generate_latex_table(results)
    output_tex = 'code/api_coverage_agents_table.tex'
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    print(f'LaTeX table saved to: {output_tex}')
    print('\n' + '=' * 80)
    print('SUMMARY')
    print('=' * 80)
    total_configs = len(results)
    total_apis = sum((data['total_apis'] for data in results.values()))
    total_implemented = sum((data['implemented_apis'] for data in results.values()))
    overall_ac = total_implemented / total_apis if total_apis > 0 else 0
    print(f'\nTotal configurations analyzed: {total_configs}')
    print(f'Total API endpoints found: {total_apis}')
    print(f'Total implemented: {total_implemented}')
    print(f'Overall API Coverage (AC): {overall_ac:.2%}')
    print('\n' + '=' * 80)
    print('BY CONFIGURATION')
    print('=' * 80)
    for (agent, model, language), data in sorted(results.items()):
        print(f'\n{agent} - {model} - {language}:')
        print(f'  Total APIs: {data['total_apis']}')
        print(f'  Implemented: {data['implemented_apis']}')
        print(f'  Coverage: {data['coverage']:.2%}')
        print(f'  Repositories: {len(data['repos'])}')
    print('\n' + latex_table)

# Node: calculate_ac_for_agents
class RBACServiceTester:
    """Test class for RBAC Service API"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name: str, passed: bool, message: str=''):
        """Log test result"""
        status = 'PASS' if passed else 'FAIL'
        result = {'test_name': test_name, 'status': status, 'message': message}
        self.test_results.append(result)
        if passed:
            self.passed += 1
            print(f'✓ {test_name}')
        else:
            self.failed += 1
            print(f'✗ {test_name}: {message}')

    def test_create_role(self):
        """Test Case 1: Create a new role"""
        test_name = 'test_create_role'
        try:
            response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': 'admin'}, timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return None
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return None
            if 'role_id' not in data or 'role_name' not in data:
                self.log_test(test_name, False, 'Missing required fields in response')
                return None
            if data['role_name'] != 'admin':
                self.log_test(test_name, False, f"Expected role_name 'admin', got {data['role_name']}")
                return None
            self.log_test(test_name, True)
            return data['role_id']
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return None

    def test_create_multiple_roles(self):
        """Test Case 2: Create multiple roles"""
        test_name = 'test_create_multiple_roles'
        roles = ['editor', 'viewer', 'moderator']
        role_ids = {}
        try:
            for role_name in roles:
                response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': role_name}, timeout=5)
                if response.status_code != 200:
                    self.log_test(test_name, False, f"Failed to create role '{role_name}'")
                    return None
                data = response.json()
                if data.get('status') != 'success':
                    self.log_test(test_name, False, f"Failed to create role '{role_name}'")
                    return None
                role_ids[role_name] = data['role_id']
            self.log_test(test_name, True)
            return role_ids
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return None

    def test_assign_permissions_to_role(self, role_id: str):
        """Test Case 3: Assign permissions to a role"""
        test_name = 'test_assign_permissions_to_role'
        if not role_id:
            self.log_test(test_name, False, 'No role_id provided (dependency failed)')
            return False
        try:
            permissions = ['read', 'write', 'delete']
            response = requests.post(f'{self.base_url}{API_PREFIX}/roles/{role_id}/permissions', json={'permissions': permissions}, timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            if data.get('role_id') != role_id:
                self.log_test(test_name, False, 'Role ID mismatch')
                return False
            returned_permissions = data.get('permissions', [])
            if not all((p in returned_permissions for p in permissions)):
                self.log_test(test_name, False, 'Not all permissions were assigned')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_assign_role_to_user(self, role_ids: List[str], user_id: str='user123'):
        """Test Case 4: Assign roles to a user"""
        test_name = 'test_assign_role_to_user'
        if not role_ids:
            self.log_test(test_name, False, 'No role_ids provided (dependency failed)')
            return False
        try:
            response = requests.post(f'{self.base_url}{API_PREFIX}/users/{user_id}/roles', json={'role_ids': role_ids}, timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            if data.get('user_id') != user_id:
                self.log_test(test_name, False, 'User ID mismatch')
                return False
            returned_role_ids = data.get('role_ids', [])
            if not all((rid in returned_role_ids for rid in role_ids)):
                self.log_test(test_name, False, 'Not all roles were assigned')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_check_user_permissions(self, user_id: str, expected_permissions: List[str]):
        """Test Case 5: Check user permissions"""
        test_name = 'test_check_user_permissions'
        try:
            response = requests.get(f'{self.base_url}{API_PREFIX}/users/{user_id}/permissions', timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            if data.get('user_id') != user_id:
                self.log_test(test_name, False, 'User ID mismatch')
                return False
            permissions = data.get('permissions', [])
            if not all((p in permissions for p in expected_permissions)):
                self.log_test(test_name, False, f'Missing permissions. Expected: {expected_permissions}, Got: {permissions}')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_multiple_roles_permissions(self):
        """Test Case 6: User with multiple roles gets combined permissions"""
        test_name = 'test_multiple_roles_permissions'
        try:
            role1_response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': 'role1'}, timeout=5)
            role1_id = role1_response.json()['role_id']
            role2_response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': 'role2'}, timeout=5)
            role2_id = role2_response.json()['role_id']
            requests.post(f'{self.base_url}{API_PREFIX}/roles/{role1_id}/permissions', json={'permissions': ['read', 'write']}, timeout=5)
            requests.post(f'{self.base_url}{API_PREFIX}/roles/{role2_id}/permissions', json={'permissions': ['delete', 'admin']}, timeout=5)
            user_id = 'multi_role_user'
            requests.post(f'{self.base_url}{API_PREFIX}/users/{user_id}/roles', json={'role_ids': [role1_id, role2_id]}, timeout=5)
            response = requests.get(f'{self.base_url}{API_PREFIX}/users/{user_id}/permissions', timeout=5)
            permissions = response.json().get('permissions', [])
            expected = ['read', 'write', 'delete', 'admin']
            if not all((p in permissions for p in expected)):
                self.log_test(test_name, False, f'Missing permissions. Expected: {expected}, Got: {permissions}')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_duplicate_role_error(self):
        """Test Case 7: Creating duplicate role should fail"""
        test_name = 'test_duplicate_role_error'
        try:
            role_name = 'duplicate_role'
            response1 = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': role_name}, timeout=5)
            if response1.status_code != 200:
                self.log_test(test_name, False, 'Failed to create first role')
                return False
            response2 = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': role_name}, timeout=5)
            if response2.status_code == 200:
                data = response2.json()
                if data.get('status') == 'success':
                    self.log_test(test_name, False, 'Duplicate role was allowed')
                    return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_invalid_role_id(self):
        """Test Case 8: Assigning permissions to non-existent role should fail"""
        test_name = 'test_invalid_role_id'
        try:
            response = requests.post(f'{self.base_url}{API_PREFIX}/roles/nonexistent_role_id/permissions', json={'permissions': ['read']}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test(test_name, False, 'Non-existent role_id was accepted')
                    return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_user_without_roles(self):
        """Test Case 9: User without roles should have no permissions"""
        test_name = 'test_user_without_roles'
        try:
            user_id = 'user_no_roles'
            response = requests.get(f'{self.base_url}{API_PREFIX}/users/{user_id}/permissions', timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            permissions = data.get('permissions', [])
            if len(permissions) != 0:
                self.log_test(test_name, False, f'User without roles should have no permissions, got {permissions}')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def print_summary(self):
        """Print test summary and metrics"""
        total = self.passed + self.failed
        pass_rate = self.passed / total * 100 if total > 0 else 0
        repo_pass = 1 if self.failed == 0 else 0
        print('\n' + '=' * 60)
        print('TEST SUMMARY')
        print('=' * 60)
        print(f'Total Tests: {total}')
        print(f'Passed: {self.passed}')
        print(f'Failed: {self.failed}')
        print(f'\nMetrics:')
        print(f'  Test Case Pass Rate: {pass_rate:.2f}%')
        print(f'  Repository Pass Rate: {repo_pass}')
        print('=' * 60)
        return repo_pass

    def run_all_tests(self):
        """Run all test cases in sequence"""
        print('Starting RBAC Service Tests...')
        print(f'Testing service at: {self.base_url}\n')
        admin_role_id = self.test_create_role()
        role_ids_dict = self.test_create_multiple_roles()
        if admin_role_id:
            self.test_assign_permissions_to_role(admin_role_id)
        if role_ids_dict and 'editor' in role_ids_dict:
            editor_role_id = role_ids_dict['editor']
            requests.post(f'{self.base_url}{API_PREFIX}/roles/{editor_role_id}/permissions', json={'permissions': ['read', 'write']}, timeout=5)
            self.test_assign_role_to_user([editor_role_id], 'test_user_1')
            self.test_check_user_permissions('test_user_1', ['read', 'write'])
        self.test_multiple_roles_permissions()
        self.test_duplicate_role_error()
        self.test_invalid_role_id()
        self.test_user_without_roles()
        repo_pass = self.print_summary()
        return repo_pass

def log_test(self, test_name: str, passed: bool, message: str=''):
    """Log test result"""
    status = 'PASS' if passed else 'FAIL'
    result = {'test_name': test_name, 'status': status, 'message': message}
    self.test_results.append(result)
    if passed:
        self.passed += 1
        print(f'✓ {test_name}')
    else:
        self.failed += 1
        print(f'✗ {test_name}: {message}')

def print_summary(self):
    """Print test summary and metrics"""
    total = self.passed + self.failed
    pass_rate = self.passed / total * 100 if total > 0 else 0
    repo_pass = 1 if self.failed == 0 else 0
    print('\n' + '=' * 60)
    print('TEST SUMMARY')
    print('=' * 60)
    print(f'Total Tests: {total}')
    print(f'Passed: {self.passed}')
    print(f'Failed: {self.failed}')
    print(f'\nMetrics:')
    print(f'  Test Case Pass Rate: {pass_rate:.2f}%')
    print(f'  Repository Pass Rate: {repo_pass}')
    print('=' * 60)
    return repo_pass

class TestIntegration:
    BASE_URL = 'http://localhost:8000/api/v1'

    def setup_method(self):
        self.test_data = {'csv': 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000\nWang Wu,28,Shenzhen,20000', 'excel': None, 'complex_csv': 'ProductID,ProductName,Category,Price,Stock,Supplier,Description\nP001,Smartphone,Electronics,2999.00,50,ZTE,High-performance 5G smartphone\nP002,Laptop,Electronics,5999.00,20,Huawei,Lightweight business laptop\nP003,Mechanical Keyboard,Accessories,299.00,100,Rapoo,RGB backlit mechanical keyboard\nP004,Mouse Pad,Accessories,49.00,200,SteelSeries,Extra large mouse pad'}
        df = pd.DataFrame({'Name': ['Zhang San', 'Li Si', 'Wang Wu'], 'Age': [25, 30, 28], 'City': ['Beijing', 'Shanghai', 'Shenzhen'], 'Salary': [15000, 18000, 20000]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.test_data['excel'] = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_end_to_end_conversion_workflow(self):
        health_response = requests.get(f'{self.BASE_URL}/health')
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data['status'] == 'healthy'
        csv_to_excel_payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=csv_to_excel_payload, timeout=30)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1['success'] is True
        excel_result = data1['result']
        excel_to_pdf_payload = {'source_format': 'excel', 'target_format': 'pdf', 'data': excel_result}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=excel_to_pdf_payload, timeout=30)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['success'] is True
        assert 'metadata' in data1
        assert 'metadata' in data2
        assert data1['metadata']['rows_count'] == 3
        assert data1['metadata']['columns_count'] == 4
        print('End-to-end workflow test passed')

    def test_batch_conversion_workflow(self):
        conversions = [{'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}, {'source_format': 'excel', 'target_format': 'csv', 'data': self.test_data['excel']}, {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(self.test_data['complex_csv'].encode('utf-8')).decode('utf-8')}]
        batch_payload = {'conversions': conversions, 'parallel': True}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=batch_payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == 3
        for i, result in enumerate(data['results']):
            assert result['success'] is True, f'The {i + 1}-th conversion failed: {result.get('message', 'Unknown error')}'
            assert 'result' in result
            assert result['result'] != ''
        summary = data['summary']
        assert summary['total_count'] == 3
        assert summary['success_count'] == 3
        assert summary['failure_count'] == 0
        print('Batch conversion workflow test passed')

    def test_error_handling_workflow(self):
        invalid_format_payload = {'source_format': 'invalid', 'target_format': 'excel', 'data': base64.b64encode(b'test').decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=invalid_format_payload, timeout=10)
        assert response1.status_code in [400, 422]
        empty_data_payload = {'source_format': 'csv', 'target_format': 'excel', 'data': ''}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=empty_data_payload, timeout=10)
        assert response2.status_code in [200, 400]
        health_response = requests.get(f'{self.BASE_URL}/health')
        assert health_response.status_code == 200
        print('Error handling workflow test passed')

    def test_performance_under_realistic_load(self):

        def simulate_user_session(session_id):
            results = []
            health_response = requests.get(f'{self.BASE_URL}/health')
            results.append(health_response.status_code == 200)
            operations = [('csv', 'excel', self.test_data['csv']), ('excel', 'csv', self.test_data['excel']), ('csv', 'pdf', self.test_data['complex_csv'])]
            for source_fmt, target_fmt, data in operations:
                payload = {'source_format': source_fmt, 'target_format': target_fmt, 'data': base64.b64encode(data.encode('utf-8')).decode('utf-8') if isinstance(data, str) else data}
                response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
                results.append(response.status_code == 200)
                time.sleep(0.2)
            return results
        import threading
        results = []
        errors = []

        def run_user_session(session_id):
            try:
                session_results = simulate_user_session(session_id)
                results.append(session_results)
            except Exception as e:
                errors.append(f'Session {session_id} error: {str(e)}')
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_user_session, args=(i,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'User session error: {errors}'
        total_operations = sum((len(session_result) for session_result in results))
        successful_operations = sum((sum(session_result) for session_result in results))
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        print('Performance under realistic load test passed')
        print(f'Total operations: {total_operations}')
        print(f'Successful operations: {successful_operations}')
        print(f'Success rate: {success_rate * 100:.1f}%')
        assert success_rate > 0.9, f'Success rate is too low: {success_rate * 100:.1f}%'

    def test_data_consistency_across_formats(self):
        original_csv = 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000'
        payload1 = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(original_csv.encode('utf-8')).decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_data = response1.json()['result']
        payload2 = {'source_format': 'excel', 'target_format': 'csv', 'data': excel_data}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=payload2, timeout=30)
        assert response2.status_code == 200
        final_csv = base64.b64decode(response2.json()['result']).decode('utf-8')
        original_lines = [line.strip() for line in original_csv.split('\n') if line.strip()]
        final_lines = [line.strip() for line in final_csv.split('\n') if line.strip()]
        assert len(original_lines) == len(final_lines), 'Number of rows is inconsistent'
        for original_line, final_line in zip(original_lines, final_lines):
            original_elements = set(original_line.split(','))
            final_elements = set(final_line.split(','))
            assert len(original_elements) == len(final_elements), f'Number of data elements is inconsistent: {original_line} vs {final_line}'
        print('Data consistency test passed')

    def test_system_resource_usage(self):
        health_before = requests.get(f'{self.BASE_URL}/health')
        assert health_before.status_code == 200
        before_timestamp = health_before.json()['timestamp']
        operations = []
        for i in range(10):
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}
            operations.append(payload)
        start_time = time.time()
        for payload in operations:
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            assert response.status_code == 200
        end_time = time.time()
        health_after = requests.get(f'{self.BASE_URL}/health')
        assert health_after.status_code == 200
        after_timestamp = health_after.json()['timestamp']
        assert health_before.json()['status'] == 'healthy'
        assert health_after.json()['status'] == 'healthy'
        print('System resource usage test passed')
        print(f'Number of operations: {len(operations)}')
        print(f'Total time: {end_time - start_time:.2f} seconds')
        print(f'Average time: {(end_time - start_time) / len(operations):.2f} seconds')
        print('System remains healthy after high load')
        time.sleep(2)
        final_health = requests.get(f'{self.BASE_URL}/health')
        assert final_health.status_code == 200
        assert final_health.json()['status'] == 'healthy'

    def test_api_version_compatibility(self):
        health_response = requests.get(f'{self.BASE_URL}/health')
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert 'version' in health_data
        interfaces = [('Health check', 'GET', f'{self.BASE_URL}/health'), ('Single conversion', 'POST', f'{self.BASE_URL}/convert'), ('Batch conversion', 'POST', f'{self.BASE_URL}/convert/batch')]
        for interface_name, method, url in interfaces:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(b'test,a,b\n1,2,3').decode('utf-8')}
                response = requests.post(url, json=payload, timeout=10)
            print(f'{interface_name} interface status: {response.status_code}')
            assert response.status_code in [200, 400, 404, 405, 422], f'{interface_name} interface is not available'
        print('API version compatibility test passed')

    def test_real_world_usage_scenario(self):
        employee_data = 'EmployeeID,Name,Department,Position,HireDate,Salary,PerformanceLevel\nE001,Zhang San,Technology,Senior Engineer,2022-01-15,25000,A\nE002,Li Si,Sales,Sales Manager,2021-08-20,30000,A\nE003,Wang Wu,Marketing,Marketing Specialist,2023-03-10,15000,B\nE004,Zhao Liu,HR,HR Assistant,2022-11-05,12000,B'
        payload1 = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(employee_data.encode('utf-8')).decode('utf-8')}
        response1 = requests.post(f'{self.BASE_URL}/convert', json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_report = response1.json()['result']
        payload2 = {'source_format': 'excel', 'target_format': 'pdf', 'data': excel_report}
        response2 = requests.post(f'{self.BASE_URL}/convert', json=payload2, timeout=30)
        assert response2.status_code == 200
        pdf_report = response2.json()['result']
        data1 = response1.json()
        data2 = response2.json()
        assert data1['success'] is True
        assert data2['success'] is True
        assert data1['metadata']['rows_count'] == 4
        assert data1['metadata']['columns_count'] == 7
        pdf_size = len(base64.b64decode(pdf_report)) / 1024
        assert pdf_size > 1, f'PDF report is too small: {pdf_size:.1f}KB'
        print('Real-world usage scenario test passed')
        print(f'Employee data rows: {data1['metadata']['rows_count']}')
        print(f'Data columns: {data1['metadata']['columns_count']}')
        print(f'PDF report size: {pdf_size:.1f}KB')

def setup_method(self):
    self.test_data = {'csv': 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000\nWang Wu,28,Shenzhen,20000', 'excel': None, 'complex_csv': 'ProductID,ProductName,Category,Price,Stock,Supplier,Description\nP001,Smartphone,Electronics,2999.00,50,ZTE,High-performance 5G smartphone\nP002,Laptop,Electronics,5999.00,20,Huawei,Lightweight business laptop\nP003,Mechanical Keyboard,Accessories,299.00,100,Rapoo,RGB backlit mechanical keyboard\nP004,Mouse Pad,Accessories,49.00,200,SteelSeries,Extra large mouse pad'}
    df = pd.DataFrame({'Name': ['Zhang San', 'Li Si', 'Wang Wu'], 'Age': [25, 30, 28], 'City': ['Beijing', 'Shanghai', 'Shenzhen'], 'Salary': [15000, 18000, 20000]})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            self.test_data['excel'] = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)

# Node: DataFrame
# Node: NamedTemporaryFile
# Node: to_excel
# Node: decode
# Node: b64encode
# Node: unlink
def test_end_to_end_conversion_workflow(self):
    health_response = requests.get(f'{self.BASE_URL}/health')
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data['status'] == 'healthy'
    csv_to_excel_payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}
    response1 = requests.post(f'{self.BASE_URL}/convert', json=csv_to_excel_payload, timeout=30)
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1['success'] is True
    excel_result = data1['result']
    excel_to_pdf_payload = {'source_format': 'excel', 'target_format': 'pdf', 'data': excel_result}
    response2 = requests.post(f'{self.BASE_URL}/convert', json=excel_to_pdf_payload, timeout=30)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2['success'] is True
    assert 'metadata' in data1
    assert 'metadata' in data2
    assert data1['metadata']['rows_count'] == 3
    assert data1['metadata']['columns_count'] == 4
    print('End-to-end workflow test passed')

# Node: encode
def test_batch_conversion_workflow(self):
    conversions = [{'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}, {'source_format': 'excel', 'target_format': 'csv', 'data': self.test_data['excel']}, {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(self.test_data['complex_csv'].encode('utf-8')).decode('utf-8')}]
    batch_payload = {'conversions': conversions, 'parallel': True}
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=batch_payload, timeout=60)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['results']) == 3
    for i, result in enumerate(data['results']):
        assert result['success'] is True, f'The {i + 1}-th conversion failed: {result.get('message', 'Unknown error')}'
        assert 'result' in result
        assert result['result'] != ''
    summary = data['summary']
    assert summary['total_count'] == 3
    assert summary['success_count'] == 3
    assert summary['failure_count'] == 0
    print('Batch conversion workflow test passed')

def test_error_handling_workflow(self):
    invalid_format_payload = {'source_format': 'invalid', 'target_format': 'excel', 'data': base64.b64encode(b'test').decode('utf-8')}
    response1 = requests.post(f'{self.BASE_URL}/convert', json=invalid_format_payload, timeout=10)
    assert response1.status_code in [400, 422]
    empty_data_payload = {'source_format': 'csv', 'target_format': 'excel', 'data': ''}
    response2 = requests.post(f'{self.BASE_URL}/convert', json=empty_data_payload, timeout=10)
    assert response2.status_code in [200, 400]
    health_response = requests.get(f'{self.BASE_URL}/health')
    assert health_response.status_code == 200
    print('Error handling workflow test passed')

def simulate_user_session(session_id):
    results = []
    health_response = requests.get(f'{self.BASE_URL}/health')
    results.append(health_response.status_code == 200)
    operations = [('csv', 'excel', self.test_data['csv']), ('excel', 'csv', self.test_data['excel']), ('csv', 'pdf', self.test_data['complex_csv'])]
    for source_fmt, target_fmt, data in operations:
        payload = {'source_format': source_fmt, 'target_format': target_fmt, 'data': base64.b64encode(data.encode('utf-8')).decode('utf-8') if isinstance(data, str) else data}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        results.append(response.status_code == 200)
        time.sleep(0.2)
    return results

def test_data_consistency_across_formats(self):
    original_csv = 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000'
    payload1 = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(original_csv.encode('utf-8')).decode('utf-8')}
    response1 = requests.post(f'{self.BASE_URL}/convert', json=payload1, timeout=30)
    assert response1.status_code == 200
    excel_data = response1.json()['result']
    payload2 = {'source_format': 'excel', 'target_format': 'csv', 'data': excel_data}
    response2 = requests.post(f'{self.BASE_URL}/convert', json=payload2, timeout=30)
    assert response2.status_code == 200
    final_csv = base64.b64decode(response2.json()['result']).decode('utf-8')
    original_lines = [line.strip() for line in original_csv.split('\n') if line.strip()]
    final_lines = [line.strip() for line in final_csv.split('\n') if line.strip()]
    assert len(original_lines) == len(final_lines), 'Number of rows is inconsistent'
    for original_line, final_line in zip(original_lines, final_lines):
        original_elements = set(original_line.split(','))
        final_elements = set(final_line.split(','))
        assert len(original_elements) == len(final_elements), f'Number of data elements is inconsistent: {original_line} vs {final_line}'
    print('Data consistency test passed')

# Node: b64decode
# Node: zip
def test_system_resource_usage(self):
    health_before = requests.get(f'{self.BASE_URL}/health')
    assert health_before.status_code == 200
    before_timestamp = health_before.json()['timestamp']
    operations = []
    for i in range(10):
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.test_data['csv'].encode('utf-8')).decode('utf-8')}
        operations.append(payload)
    start_time = time.time()
    for payload in operations:
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
    end_time = time.time()
    health_after = requests.get(f'{self.BASE_URL}/health')
    assert health_after.status_code == 200
    after_timestamp = health_after.json()['timestamp']
    assert health_before.json()['status'] == 'healthy'
    assert health_after.json()['status'] == 'healthy'
    print('System resource usage test passed')
    print(f'Number of operations: {len(operations)}')
    print(f'Total time: {end_time - start_time:.2f} seconds')
    print(f'Average time: {(end_time - start_time) / len(operations):.2f} seconds')
    print('System remains healthy after high load')
    time.sleep(2)
    final_health = requests.get(f'{self.BASE_URL}/health')
    assert final_health.status_code == 200
    assert final_health.json()['status'] == 'healthy'

def test_api_version_compatibility(self):
    health_response = requests.get(f'{self.BASE_URL}/health')
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert 'version' in health_data
    interfaces = [('Health check', 'GET', f'{self.BASE_URL}/health'), ('Single conversion', 'POST', f'{self.BASE_URL}/convert'), ('Batch conversion', 'POST', f'{self.BASE_URL}/convert/batch')]
    for interface_name, method, url in interfaces:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(b'test,a,b\n1,2,3').decode('utf-8')}
            response = requests.post(url, json=payload, timeout=10)
        print(f'{interface_name} interface status: {response.status_code}')
        assert response.status_code in [200, 400, 404, 405, 422], f'{interface_name} interface is not available'
    print('API version compatibility test passed')

def test_real_world_usage_scenario(self):
    employee_data = 'EmployeeID,Name,Department,Position,HireDate,Salary,PerformanceLevel\nE001,Zhang San,Technology,Senior Engineer,2022-01-15,25000,A\nE002,Li Si,Sales,Sales Manager,2021-08-20,30000,A\nE003,Wang Wu,Marketing,Marketing Specialist,2023-03-10,15000,B\nE004,Zhao Liu,HR,HR Assistant,2022-11-05,12000,B'
    payload1 = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(employee_data.encode('utf-8')).decode('utf-8')}
    response1 = requests.post(f'{self.BASE_URL}/convert', json=payload1, timeout=30)
    assert response1.status_code == 200
    excel_report = response1.json()['result']
    payload2 = {'source_format': 'excel', 'target_format': 'pdf', 'data': excel_report}
    response2 = requests.post(f'{self.BASE_URL}/convert', json=payload2, timeout=30)
    assert response2.status_code == 200
    pdf_report = response2.json()['result']
    data1 = response1.json()
    data2 = response2.json()
    assert data1['success'] is True
    assert data2['success'] is True
    assert data1['metadata']['rows_count'] == 4
    assert data1['metadata']['columns_count'] == 7
    pdf_size = len(base64.b64decode(pdf_report)) / 1024
    assert pdf_size > 1, f'PDF report is too small: {pdf_size:.1f}KB'
    print('Real-world usage scenario test passed')
    print(f'Employee data rows: {data1['metadata']['rows_count']}')
    print(f'Data columns: {data1['metadata']['columns_count']}')
    print(f'PDF report size: {pdf_size:.1f}KB')

class TestConvertBatchEndpoint:
    BASE_URL = 'http://localhost:8000/api/v1'

    def setup_method(self):
        self.test_datasets = []
        csv_data = 'Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai'
        self.test_datasets.append({'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')})
        df = pd.DataFrame({'Product': ['ProductA', 'ProductB', 'ProductC'], 'Price': [100, 200, 300], 'Stock': [50, 30, 20]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        self.test_datasets.append({'source_format': 'excel', 'target_format': 'csv', 'data': excel_data})
        csv_data2 = 'Department,Number of People,Budget\nTechnology Department,10,100000\nSales Department,8,80000\nMarketing Department,5,50000'
        self.test_datasets.append({'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(csv_data2.encode('utf-8')).decode('utf-8')})

    def test_batch_conversion_sequential(self):
        payload = {'conversions': self.test_datasets, 'parallel': False}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=60)
        end_time = time.time()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'results' in data
        assert 'summary' in data
        assert len(data['results']) == len(self.test_datasets)
        summary = data['summary']
        assert summary['total_count'] == len(self.test_datasets)
        assert summary['success_count'] >= 0
        assert summary['failure_count'] >= 0
        assert summary['total_count'] == summary['success_count'] + summary['failure_count']
        assert summary['total_time'] > 0
        assert end_time - start_time < 45.0

    def test_batch_conversion_parallel(self):
        payload = {'conversions': self.test_datasets, 'parallel': True}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=60)
        end_time = time.time()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == len(self.test_datasets)
        parallel_time = end_time - start_time
        sequential_payload = {'conversions': self.test_datasets, 'parallel': False}
        seq_start = time.time()
        seq_response = requests.post(f'{self.BASE_URL}/convert/batch', json=sequential_payload, timeout=60)
        seq_end = time.time()
        sequential_time = seq_end - seq_start
        assert parallel_time <= sequential_time + 5.0

    def test_batch_conversion_with_failures(self):
        invalid_dataset = {'source_format': 'invalid_format', 'target_format': 'excel', 'data': base64.b64encode(b'test data').decode('utf-8')}
        test_datasets_with_failure = self.test_datasets + [invalid_dataset]
        payload = {'conversions': test_datasets_with_failure, 'parallel': False}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == len(test_datasets_with_failure)
        summary = data['summary']
        assert summary['total_count'] == len(test_datasets_with_failure)
        assert summary['success_count'] >= 0
        assert summary['failure_count'] > 0

    def test_batch_conversion_empty_list(self):
        payload = {'conversions': [], 'parallel': False}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=10)
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            assert summary.get('total_count', 0) == 0

    def test_batch_conversion_large_dataset(self):
        large_df = pd.DataFrame({f'col{i}': range(100) for i in range(50)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        large_datasets = []
        for i in range(3):
            large_datasets.append({'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data})
        payload = {'conversions': large_datasets, 'parallel': True}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=120)
        end_time = time.time()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        processing_time = end_time - start_time
        assert processing_time < 90.0
        summary = data['summary']
        assert summary['success_count'] == len(large_datasets)

    def test_batch_conversion_mixed_formats(self):
        mixed_datasets = [{'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode('a,b\n1,2'.encode('utf-8')).decode('utf-8')}, {'source_format': 'excel', 'target_format': 'pdf', 'data': self.test_datasets[1]['data']}, {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode('x,y,z\n1,2,3\n4,5,6'.encode('utf-8')).decode('utf-8')}]
        payload = {'conversions': mixed_datasets, 'parallel': False}
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=45)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['results']) == len(mixed_datasets)
        for i, result in enumerate(data['results']):
            assert 'success' in result
            assert 'message' in result
            if result['success']:
                assert 'result' in result
                assert result['result'] != ''

    def test_batch_conversion_performance_comparison(self):
        test_data = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode('a,b,c\n1,2,3\n4,5,6'.encode('utf-8')).decode('utf-8')}
        single_start = time.time()
        for _ in range(3):
            response = requests.post(f'{self.BASE_URL}/convert', json=test_data, timeout=30)
            assert response.status_code == 200
        single_end = time.time()
        single_avg_time = (single_end - single_start) / 3
        batch_payload = {'conversions': [test_data, test_data, test_data], 'parallel': True}
        batch_start = time.time()
        response = requests.post(f'{self.BASE_URL}/convert/batch', json=batch_payload, timeout=60)
        batch_end = time.time()
        batch_time = batch_end - batch_start
        assert response.status_code == 200
        data = response.json()
        summary = data['summary']
        assert batch_time <= single_avg_time * 4
        assert summary['success_count'] == 3

def setup_method(self):
    self.test_datasets = []
    csv_data = 'Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai'
    self.test_datasets.append({'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')})
    df = pd.DataFrame({'Product': ['ProductA', 'ProductB', 'ProductC'], 'Price': [100, 200, 300], 'Stock': [50, 30, 20]})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            excel_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
    self.test_datasets.append({'source_format': 'excel', 'target_format': 'csv', 'data': excel_data})
    csv_data2 = 'Department,Number of People,Budget\nTechnology Department,10,100000\nSales Department,8,80000\nMarketing Department,5,50000'
    self.test_datasets.append({'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(csv_data2.encode('utf-8')).decode('utf-8')})

def test_batch_conversion_with_failures(self):
    invalid_dataset = {'source_format': 'invalid_format', 'target_format': 'excel', 'data': base64.b64encode(b'test data').decode('utf-8')}
    test_datasets_with_failure = self.test_datasets + [invalid_dataset]
    payload = {'conversions': test_datasets_with_failure, 'parallel': False}
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['results']) == len(test_datasets_with_failure)
    summary = data['summary']
    assert summary['total_count'] == len(test_datasets_with_failure)
    assert summary['success_count'] >= 0
    assert summary['failure_count'] > 0

def test_batch_conversion_large_dataset(self):
    large_df = pd.DataFrame({f'col{i}': range(100) for i in range(50)})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        large_df.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            large_excel_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
    large_datasets = []
    for i in range(3):
        large_datasets.append({'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data})
    payload = {'conversions': large_datasets, 'parallel': True}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=120)
    end_time = time.time()
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    processing_time = end_time - start_time
    assert processing_time < 90.0
    summary = data['summary']
    assert summary['success_count'] == len(large_datasets)

def test_batch_conversion_mixed_formats(self):
    mixed_datasets = [{'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode('a,b\n1,2'.encode('utf-8')).decode('utf-8')}, {'source_format': 'excel', 'target_format': 'pdf', 'data': self.test_datasets[1]['data']}, {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode('x,y,z\n1,2,3\n4,5,6'.encode('utf-8')).decode('utf-8')}]
    payload = {'conversions': mixed_datasets, 'parallel': False}
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=payload, timeout=45)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['results']) == len(mixed_datasets)
    for i, result in enumerate(data['results']):
        assert 'success' in result
        assert 'message' in result
        if result['success']:
            assert 'result' in result
            assert result['result'] != ''

def test_batch_conversion_performance_comparison(self):
    test_data = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode('a,b,c\n1,2,3\n4,5,6'.encode('utf-8')).decode('utf-8')}
    single_start = time.time()
    for _ in range(3):
        response = requests.post(f'{self.BASE_URL}/convert', json=test_data, timeout=30)
        assert response.status_code == 200
    single_end = time.time()
    single_avg_time = (single_end - single_start) / 3
    batch_payload = {'conversions': [test_data, test_data, test_data], 'parallel': True}
    batch_start = time.time()
    response = requests.post(f'{self.BASE_URL}/convert/batch', json=batch_payload, timeout=60)
    batch_end = time.time()
    batch_time = batch_end - batch_start
    assert response.status_code == 200
    data = response.json()
    summary = data['summary']
    assert batch_time <= single_avg_time * 4
    assert summary['success_count'] == 3

class TestPerformance:
    BASE_URL = 'http://localhost:8000/api/v1'

    def setup_method(self):
        self.medium_df = pd.DataFrame({f'col{i}': range(1000) for i in range(10)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.medium_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.medium_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        self.small_csv_data = base64.b64encode('Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai\nWang Wu,28,Shenzhen'.encode('utf-8')).decode('utf-8')

    def test_single_conversion_performance(self):
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.medium_excel_data}
        times = []
        for _ in range(10):
            start_time = time.time()
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            end_time = time.time()
            assert response.status_code == 200
            times.append(end_time - start_time)
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        print('Single conversion performance statistics:')
        print(f'Average time: {avg_time:.2f} seconds')
        print(f'Median time: {median_time:.2f} seconds')
        print(f'Minimum time: {min_time:.2f} seconds')
        print(f'Maximum time: {max_time:.2f} seconds')
        print(f'Standard deviation: {std_dev:.2f} seconds')
        assert avg_time < 5.0, f'Average conversion time is too long: {avg_time:.2f} seconds'
        assert max_time < 10.0, f'Maximum conversion time is too long: {max_time:.2f} seconds'
        assert std_dev < 2.0, f'Conversion time stability is poor: {std_dev:.2f} seconds'

    def test_concurrent_requests_performance(self):

        def make_request(request_id):
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
            start_time = time.time()
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
            end_time = time.time()
            return {'request_id': request_id, 'success': response.status_code == 200, 'response_time': end_time - start_time}
        concurrency_levels = [5, 10, 20]
        results = {}
        for concurrency in concurrency_levels:
            print(f'\nTesting concurrency level: {concurrency}')
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrency)]
                responses = [future.result() for future in as_completed(futures)]
            end_time = time.time()
            response_times = [r['response_time'] for r in responses if r['success']]
            success_count = sum((1 for r in responses if r['success']))
            results[concurrency] = {'total_requests': len(responses), 'success_count': success_count, 'avg_response_time': statistics.mean(response_times) if response_times else 0, 'total_time': end_time - start_time}
            print(f'Successful requests: {success_count}/{len(responses)}')
            print(f'Average response time: {results[concurrency]['avg_response_time']:.2f} seconds')
            print(f'Total time: {results[concurrency]['total_time']:.2f} seconds')
            assert success_count >= concurrency * 0.8, f'Concurrent request success rate is too low: {success_count}/{concurrency}'
        if len(results) >= 2:
            time_5 = results[5]['total_time']
            time_10 = results[10]['total_time']
            assert time_10 < time_5 * 3.0, f'Concurrency scalability is poor: 10 concurrency time {time_10:.2f} seconds vs 5 concurrency expected upper limit {time_5 * 3.0:.2f} seconds'

    def test_memory_usage_stability(self):

        def continuous_requests(duration_seconds=30):
            end_time = time.time() + duration_seconds
            request_count = 0
            errors = []
            while time.time() < end_time:
                try:
                    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
                    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
                    if response.status_code != 200:
                        errors.append(f'Request failed: {response.status_code}')
                    request_count += 1
                    time.sleep(0.1)
                except Exception as e:
                    errors.append(str(e))
                    time.sleep(0.1)
            return (request_count, errors)
        request_count, errors = continuous_requests(30)
        print(f'\nContinuous requests test results:')
        print(f'Total requests: {request_count}')
        print(f'Errors: {len(errors)}')
        print(f'Error rate: {len(errors) / request_count * 100:.2f}%' if request_count > 0 else 'Error rate: N/A')
        assert request_count > 0, 'Failed to send any requests'
        assert len(errors) / request_count < 0.1, f'Error rate is too high: {len(errors)}/{request_count}'

    def test_health_check_under_load(self):

        def load_generator():
            end_time = time.time() + 20
            while time.time() < end_time:
                payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
                requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
                time.sleep(0.2)

        def health_checks():
            health_times = []
            end_time = time.time() + 20
            while time.time() < end_time:
                start_time = time.time()
                response = requests.get(f'{self.BASE_URL}/health', timeout=5)
                end_time = time.time()
                health_times.append(end_time - start_time)
                assert response.status_code == 200
                time.sleep(0.5)
            return health_times
        load_thread = threading.Thread(target=load_generator)
        load_thread.start()
        health_response_times = health_checks()
        load_thread.join()
        avg_health_time = statistics.mean(health_response_times)
        max_health_time = max(health_response_times)
        print('Health check performance under load:')
        print(f'Average response time: {avg_health_time:.3f} seconds')
        print(f'Maximum response time: {max_health_time:.3f} seconds')
        assert avg_health_time < 1.0, f'Health check response is too slow under load: {avg_health_time:.3f} seconds'
        assert max_health_time < 2.0, f'Maximum health check response time is too long under load: {max_health_time:.3f} seconds'

    def test_large_file_performance(self):
        large_df = pd.DataFrame({f'col{i}': range(5000) for i in range(20)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=120)
        end_time = time.time()
        assert response.status_code == 200
        conversion_time = end_time - start_time
        print('Large file conversion performance:')
        print(f'Conversion time: {conversion_time:.2f} seconds')
        print(f'File size: {len(large_excel_data) * 3 / 4 / 1024:.1f} KB')
        assert conversion_time < 60.0, f'Large file conversion time is too long: {conversion_time:.2f} seconds'
        data = response.json()
        assert data['success'] is True

    def test_response_time_distribution(self):

        def make_request():
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
            start_time = time.time()
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
            end_time = time.time()
            return end_time - start_time if response.status_code == 200 else None
        response_times = []
        for _ in range(50):
            time_taken = make_request()
            if time_taken is not None:
                response_times.append(time_taken)
        if response_times:
            sorted_times = sorted(response_times)
            print('Response time distribution:')
            print(f'Average: {statistics.mean(response_times):.3f} seconds')
            print(f'Median: {statistics.median(response_times):.3f} seconds')
            print(f'90th percentile: {sorted_times[int(len(sorted_times) * 0.9)]:.3f} seconds')
            print(f'95th percentile: {sorted_times[int(len(sorted_times) * 0.95)]:.3f} seconds')
            print(f'99th percentile: {sorted_times[int(len(sorted_times) * 0.99)]:.3f} seconds')
            assert statistics.mean(response_times) < 3.0, 'Average response time is too long'
            assert sorted_times[int(len(sorted_times) * 0.95)] < 5.0, '95th percentile response time is too long'

    def test_resource_cleanup_verification(self):

        def intensive_workload():
            for i in range(20):
                payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.medium_excel_data}
                response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    assert 'metadata' in data
                    assert 'conversion_time' in data['metadata']
                time.sleep(0.1)
        start_time = time.time()
        health_before = requests.get(f'{self.BASE_URL}/health', timeout=5)
        assert health_before.status_code == 200
        intensive_workload()
        health_after = requests.get(f'{self.BASE_URL}/health', timeout=5)
        assert health_after.status_code == 200
        end_time = time.time()
        print('Resource cleanup verification:')
        print(f'Workload execution time: {end_time - start_time:.2f} seconds')
        print('Service remains healthy after high load')
        health_data_before = health_before.json()
        health_data_after = health_after.json()
        assert health_data_before['status'] == 'healthy'
        assert health_data_after['status'] == 'healthy'

def setup_method(self):
    self.medium_df = pd.DataFrame({f'col{i}': range(1000) for i in range(10)})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        self.medium_df.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            self.medium_excel_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
    self.small_csv_data = base64.b64encode('Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai\nWang Wu,28,Shenzhen'.encode('utf-8')).decode('utf-8')

def test_memory_usage_stability(self):

    def continuous_requests(duration_seconds=30):
        end_time = time.time() + duration_seconds
        request_count = 0
        errors = []
        while time.time() < end_time:
            try:
                payload = {'source_format': 'csv', 'target_format': 'excel', 'data': self.small_csv_data}
                response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
                if response.status_code != 200:
                    errors.append(f'Request failed: {response.status_code}')
                request_count += 1
                time.sleep(0.1)
            except Exception as e:
                errors.append(str(e))
                time.sleep(0.1)
        return (request_count, errors)
    request_count, errors = continuous_requests(30)
    print(f'\nContinuous requests test results:')
    print(f'Total requests: {request_count}')
    print(f'Errors: {len(errors)}')
    print(f'Error rate: {len(errors) / request_count * 100:.2f}%' if request_count > 0 else 'Error rate: N/A')
    assert request_count > 0, 'Failed to send any requests'
    assert len(errors) / request_count < 0.1, f'Error rate is too high: {len(errors)}/{request_count}'

# Node: continuous_requests
def test_large_file_performance(self):
    large_df = pd.DataFrame({f'col{i}': range(5000) for i in range(20)})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        large_df.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            large_excel_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
    payload = {'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=120)
    end_time = time.time()
    assert response.status_code == 200
    conversion_time = end_time - start_time
    print('Large file conversion performance:')
    print(f'Conversion time: {conversion_time:.2f} seconds')
    print(f'File size: {len(large_excel_data) * 3 / 4 / 1024:.1f} KB')
    assert conversion_time < 60.0, f'Large file conversion time is too long: {conversion_time:.2f} seconds'
    data = response.json()
    assert data['success'] is True

class TestConvertEndpoint:
    BASE_URL = 'http://localhost:8000/api/v1'
    SAMPLE_CSV_DATA = 'Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000\nWang Wu,28,Shenzhen,20000\nZhao Liu,35,Guangzhou,16000'
    SAMPLE_EXCEL_DATA = None

    def setup_method(self):
        df = pd.DataFrame({'Name': ['Zhang San', 'Li Si', 'Wang Wu', 'Zhao Liu'], 'Age': [25, 30, 28, 35], 'City': ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou'], 'Salary': [15000, 18000, 20000, 16000]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.SAMPLE_EXCEL_DATA = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_csv_to_excel_conversion(self):
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'result' in data
        assert data['result'] != ''
        assert 'metadata' in data
        assert data['metadata']['source_size'] > 0
        assert data['metadata']['target_size'] > 0
        assert data['metadata']['conversion_time'] > 0
        assert data['metadata']['rows_count'] == 4
        assert data['metadata']['columns_count'] == 4

    def test_excel_to_csv_conversion(self):
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.SAMPLE_EXCEL_DATA, 'options': {'encoding': 'utf-8', 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        result_data = base64.b64decode(data['result']).decode('utf-8')
        lines = result_data.strip().split('\n')
        assert len(lines) >= 2
        headers = lines[0].split(',')
        assert 'Name' in headers
        assert 'Age' in headers
        assert 'City' in headers
        assert 'Salary' in headers

    def test_excel_to_pdf_conversion(self):
        payload = {'source_format': 'excel', 'target_format': 'pdf', 'data': self.SAMPLE_EXCEL_DATA, 'options': {'encoding': 'utf-8', 'has_header': True, 'sheet_name': 'Sheet1'}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'result' in data
        result_data = base64.b64decode(data['result'])
        assert len(result_data) > 1000

    def test_csv_to_pdf_conversion(self):
        payload = {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True, 'delimiter': ','}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        result_data = base64.b64decode(data['result'])
        assert len(result_data) > 1000

    def test_invalid_format_conversion(self):
        payload = {'source_format': 'invalid', 'target_format': 'excel', 'data': base64.b64encode(b'test data').decode('utf-8')}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
        assert response.status_code in [400, 422]

    def test_empty_data_conversion(self):
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': '', 'options': {'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
        assert response.status_code in [200, 400]

    def test_large_file_conversion(self):
        large_data = pd.DataFrame({f'col{i}': range(1000) for i in range(20)})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_data.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        payload = {'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data, 'options': {'encoding': 'utf-8', 'has_header': True}}
        start_time = time.time()
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=60)
        end_time = time.time()
        assert response.status_code == 200
        conversion_time = end_time - start_time
        assert conversion_time < 30.0
        data = response.json()
        assert data['success'] is True

    @pytest.mark.parametrize('encoding', ['utf-8', 'gbk', 'utf-16'])
    def test_different_encodings(self, encoding):
        test_data = 'name,age\nZhang San,25\nLi Si,30'
        try:
            encoded_data = test_data.encode(encoding)
            payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(encoded_data).decode('utf-8'), 'options': {'encoding': encoding, 'has_header': True}}
            response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
            assert response.status_code in [200, 400, 422]
        except UnicodeEncodeError:
            pytest.skip(f'encoding {encoding} does not support Chinese characters')

    def test_conversion_with_special_characters(self):
        special_data = 'name,description,symbol\nZhang San,contains @ and #,Beijing @ Shanghai # Shenzhen\nLi Si,contains $ and %,amount $1000 50%\nWang Wu,contains & and *,condition A&B quantity *2'
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(special_data.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

def setup_method(self):
    df = pd.DataFrame({'Name': ['Zhang San', 'Li Si', 'Wang Wu', 'Zhao Liu'], 'Age': [25, 30, 28, 35], 'City': ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou'], 'Salary': [15000, 18000, 20000, 16000]})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            self.SAMPLE_EXCEL_DATA = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)

def test_csv_to_excel_conversion(self):
    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True}}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'result' in data
    assert data['result'] != ''
    assert 'metadata' in data
    assert data['metadata']['source_size'] > 0
    assert data['metadata']['target_size'] > 0
    assert data['metadata']['conversion_time'] > 0
    assert data['metadata']['rows_count'] == 4
    assert data['metadata']['columns_count'] == 4

def test_excel_to_csv_conversion(self):
    payload = {'source_format': 'excel', 'target_format': 'csv', 'data': self.SAMPLE_EXCEL_DATA, 'options': {'encoding': 'utf-8', 'has_header': True}}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    result_data = base64.b64decode(data['result']).decode('utf-8')
    lines = result_data.strip().split('\n')
    assert len(lines) >= 2
    headers = lines[0].split(',')
    assert 'Name' in headers
    assert 'Age' in headers
    assert 'City' in headers
    assert 'Salary' in headers

def test_csv_to_pdf_conversion(self):
    payload = {'source_format': 'csv', 'target_format': 'pdf', 'data': base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True, 'delimiter': ','}}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    result_data = base64.b64decode(data['result'])
    assert len(result_data) > 1000

def test_invalid_format_conversion(self):
    payload = {'source_format': 'invalid', 'target_format': 'excel', 'data': base64.b64encode(b'test data').decode('utf-8')}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=10)
    assert response.status_code in [400, 422]

def test_large_file_conversion(self):
    large_data = pd.DataFrame({f'col{i}': range(1000) for i in range(20)})
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        large_data.to_excel(tmp.name, index=False, engine='openpyxl')
        with open(tmp.name, 'rb') as f:
            large_excel_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
    payload = {'source_format': 'excel', 'target_format': 'csv', 'data': large_excel_data, 'options': {'encoding': 'utf-8', 'has_header': True}}
    start_time = time.time()
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=60)
    end_time = time.time()
    assert response.status_code == 200
    conversion_time = end_time - start_time
    assert conversion_time < 30.0
    data = response.json()
    assert data['success'] is True

@pytest.mark.parametrize('encoding', ['utf-8', 'gbk', 'utf-16'])
def test_different_encodings(self, encoding):
    test_data = 'name,age\nZhang San,25\nLi Si,30'
    try:
        encoded_data = test_data.encode(encoding)
        payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(encoded_data).decode('utf-8'), 'options': {'encoding': encoding, 'has_header': True}}
        response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
        assert response.status_code in [200, 400, 422]
    except UnicodeEncodeError:
        pytest.skip(f'encoding {encoding} does not support Chinese characters')

def test_conversion_with_special_characters(self):
    special_data = 'name,description,symbol\nZhang San,contains @ and #,Beijing @ Shanghai # Shenzhen\nLi Si,contains $ and %,amount $1000 50%\nWang Wu,contains & and *,condition A&B quantity *2'
    payload = {'source_format': 'csv', 'target_format': 'excel', 'data': base64.b64encode(special_data.encode('utf-8')).decode('utf-8'), 'options': {'encoding': 'utf-8', 'has_header': True}}
    response = requests.post(f'{self.BASE_URL}/convert', json=payload, timeout=15)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True

def assert_html_page(r: requests.Response) -> None:
    assert r.status_code == 200
    text = r.text.lower()
    assert '<html' in text or '<!doctype html' in text

class TestHistoryAPI:
    BASE_URL = 'http://localhost:8082/api/v1'
    TEST_USER_TOKEN = 'test_token_12345'

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
            if response.status_code == 200:
                history_records = response.json().get('history', [])
                for record in history_records:
                    if record.get('content_id', '').startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/history/{record['id']}', headers=self.get_auth_headers())
        except requests.exceptions.ConnectionError:
            pytest.skip('API Server not running')

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f'{self.BASE_URL.replace('/api/v1', '')}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_record_history_view_action(self):
        history_data = {'action': 'view', 'content_id': 'test_content_view_001', 'content_type': 'post', 'metadata': {'duration': 30, 'device': 'mobile'}, 'session_id': 'test_session_123'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == history_data['action']
        assert data['content_id'] == history_data['content_id']
        assert data['content_type'] == history_data['content_type']
        assert data['metadata'] == history_data['metadata']
        assert data['session_id'] == history_data['session_id']
        assert 'id' in data
        assert 'created_at' in data
        assert 'ip_address' in data
        assert 'user_agent' in data

    def test_record_history_search_action(self):
        history_data = {'action': 'search', 'metadata': {'query': 'python tutorial', 'results_count': 25}, 'session_id': 'test_session_456'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'search'
        assert data['metadata']['query'] == 'python tutorial'

    def test_record_history_share_action(self):
        history_data = {'action': 'share', 'content_id': 'test_content_share_001', 'content_type': 'article', 'metadata': {'platform': 'twitter', 'share_type': 'link'}}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'share'
        assert data['metadata']['platform'] == 'twitter'

    def test_record_history_download_action(self):
        history_data = {'action': 'download', 'content_id': 'test_content_download_001', 'content_type': 'video', 'metadata': {'file_size': 1024000, 'format': 'mp4'}}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'download'

    def test_record_history_minimal_data(self):
        history_data = {'action': 'view'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'view'

    def test_record_history_invalid_action(self):
        history_data = {'action': 'invalid_action', 'content_id': 'test_content_invalid'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_record_history_unauthorized(self):
        history_data = {'action': 'view', 'content_id': 'test_content_unauth'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data)
        assert response.status_code in [401, 403]

    def test_get_history_empty(self):
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'history' in data
        assert 'pagination' in data
        assert len(data['history']) == 0

    def test_get_history_with_data(self):
        actions = [{'action': 'view', 'content_id': 'test_history_1', 'content_type': 'post'}, {'action': 'search', 'metadata': {'query': 'test query'}}, {'action': 'share', 'content_id': 'test_history_2', 'content_type': 'article'}, {'action': 'download', 'content_id': 'test_history_3', 'content_type': 'video'}]
        created_records = []
        for action_data in actions:
            response = requests.post(f'{self.BASE_URL}/history', json=action_data, headers=self.get_auth_headers())
            assert response.status_code == 201
            created_records.append(response.json())
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) >= 4
        assert data['pagination']['total'] >= 4

    def test_get_history_pagination(self):
        for i in range(25):
            history_data = {'action': 'view', 'content_id': f'test_pagination_{i + 1}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?page=1&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 25
        response = requests.get(f'{self.BASE_URL}/history?page=3&limit=10', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 3

    def test_get_history_filter_by_action(self):
        actions = ['view', 'search', 'share', 'download', 'view']
        for i, action in enumerate(actions):
            history_data = {'action': action, 'content_id': f'test_filter_action_{i + 1}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?action=view', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        view_records = [record for record in data['history'] if record['action'] == 'view']
        assert len(view_records) >= 2

    def test_get_history_filter_by_content_type(self):
        content_types = ['post', 'article', 'video', 'product']
        for content_type in content_types:
            history_data = {'action': 'view', 'content_id': f'test_filter_type_{content_type}', 'content_type': content_type}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?content_type=article', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        article_records = [record for record in data['history'] if record['content_type'] == 'article']
        assert len(article_records) >= 1

    def test_get_history_filter_by_date_range(self):
        base_time = datetime.now()
        yesterday_data = {'action': 'view', 'content_id': 'test_yesterday', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=yesterday_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        today_data = {'action': 'view', 'content_id': 'test_today', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=today_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        today_str = base_time.strftime('%Y-%m-%d')
        response = requests.get(f'{self.BASE_URL}/history?start_date={today_str}&end_date={today_str}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        today_records = [record for record in data['history'] if 'test_today' in record['content_id']]
        assert len(today_records) >= 1

    def test_get_history_filter_by_session(self):
        session_id = 'test_session_filter'
        for i in range(3):
            history_data = {'action': 'view', 'content_id': f'test_session_{i + 1}', 'content_type': 'post', 'session_id': session_id}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history?session_id={session_id}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        session_records = [record for record in data['history'] if record['session_id'] == session_id]
        assert len(session_records) >= 3

    def test_get_history_unauthorized(self):
        response = requests.get(f'{self.BASE_URL}/history')
        assert response.status_code in [401, 403]

    def test_delete_single_history_success(self):
        history_data = {'action': 'view', 'content_id': 'test_delete_single', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
        history_id = response.json()['id']
        response = requests.delete(f'{self.BASE_URL}/history/{history_id}', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    def test_delete_single_history_not_found(self):
        response = requests.delete(f'{self.BASE_URL}/history/non_existent_id', headers=self.get_auth_headers())
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data

    def test_delete_single_history_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/history/some_id')
        assert response.status_code in [401, 403]

    def test_clear_all_history_success(self):
        for i in range(5):
            history_data = {'action': 'view', 'content_id': f'test_clear_{i + 1}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        initial_count = response.json()['pagination']['total']
        assert initial_count >= 5
        response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'deleted_count' in data
        assert data['deleted_count'] >= 5

    def test_clear_all_history_empty(self):
        response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['deleted_count'] == 0

    def test_clear_all_history_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/history')
        assert response.status_code in [401, 403]

    def test_history_workflow_complete(self):
        actions = [{'action': 'view', 'content_id': 'workflow_1', 'content_type': 'post'}, {'action': 'search', 'metadata': {'query': 'workflow test'}}, {'action': 'share', 'content_id': 'workflow_2', 'content_type': 'article'}]
        created_ids = []
        for action_data in actions:
            response = requests.post(f'{self.BASE_URL}/history', json=action_data, headers=self.get_auth_headers())
            assert response.status_code == 201
            created_ids.append(response.json()['id'])
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        history_ids = [record['id'] for record in data['history']]
        for created_id in created_ids:
            assert created_id in history_ids
        response = requests.delete(f'{self.BASE_URL}/history/{created_ids[0]}', headers=self.get_auth_headers())
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        history_ids = [record['id'] for record in data['history']]
        assert created_ids[0] not in history_ids
        response = requests.delete(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) == 0

    def test_history_actions_coverage(self):
        actions = ['view', 'search', 'share', 'download']
        for action in actions:
            history_data = {'action': action, 'content_id': f'test_action_{action}', 'content_type': 'post'}
            response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/history', headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        recorded_actions = [record['action'] for record in data['history']]
        for action in actions:
            assert action in recorded_actions

    def test_invalid_json_request(self):
        response = requests.post(f'{self.BASE_URL}/history', data='invalid json', headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        response = requests.get(f'{self.BASE_URL}/history?limit=1000', headers=self.get_auth_headers())
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100

def test_get_history_filter_by_action(self):
    actions = ['view', 'search', 'share', 'download', 'view']
    for i, action in enumerate(actions):
        history_data = {'action': action, 'content_id': f'test_filter_action_{i + 1}', 'content_type': 'post'}
        response = requests.post(f'{self.BASE_URL}/history', json=history_data, headers=self.get_auth_headers())
        assert response.status_code == 201
    response = requests.get(f'{self.BASE_URL}/history?action=view', headers=self.get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    view_records = [record for record in data['history'] if record['action'] == 'view']
    assert len(view_records) >= 2

class TestWebPanAPI:
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = {'username': 'testuser', 'password': 'testpass123', 'email': 'test@example.com'}
        self.test_file_content = b'This is a test file content for WebPan API testing.'
        self.test_file_name = 'test_file.txt'

    def test_user_registration(self):
        response = self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'user_id' in data
        assert data['message'] == 'User registered successfully'

    def test_user_login(self):
        self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
        login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
        response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'token' in data
        assert 'user_id' in data
        assert 'expires_in' in data
        self.auth_token = data['token']

    def test_login_invalid_credentials(self):
        login_data = {'username': 'invalid_user', 'password': 'invalid_pass'}
        response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'AUTH_INVALID'

    def test_file_upload_single(self):
        self._login_user()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'file_id' in data
            assert data['filename'] == self.test_file_name
            assert data['size'] == len(self.test_file_content)
            assert 'upload_time' in data
            assert 'download_url' in data
            self.test_file_id = data['file_id']
        finally:
            os.unlink(temp_file_path)

    def test_file_upload_without_auth(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files)
            assert response.status_code == 401
            data = response.json()
            assert data['success'] is False
            assert data['error_code'] == 'AUTH_REQUIRED'
        finally:
            os.unlink(temp_file_path)

    def test_file_upload_multiple(self):
        self._login_user()
        temp_files = []
        file_names = ['file1.txt', 'file2.txt', 'file3.txt']
        try:
            for i, name in enumerate(file_names):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
                    content = f'Test content for {name}'.encode()
                    f.write(content)
                    temp_files.append((f.name, name, content))
            files = []
            for temp_path, name, _ in temp_files:
                files.append(('files', (name, open(temp_path, 'rb'), 'text/plain')))
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(f'{self.BASE_URL}/files/upload-multiple', files=files, headers=headers)
            for _, (_, file_obj, _) in enumerate(files):
                file_obj[1][1].close()
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert len(data['uploaded_files']) == 3
            assert len(data['failed_files']) == 0
            for uploaded_file in data['uploaded_files']:
                assert 'file_id' in uploaded_file
                assert uploaded_file['status'] == 'success'
        finally:
            for temp_path, _, _ in temp_files:
                os.unlink(temp_path)

    def test_file_download(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/download', headers=headers)
        assert response.status_code == 200
        assert response.content == self.test_file_content

    def test_file_download_not_found(self):
        self._login_user()
        fake_file_id = 'non-existent-file-id'
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files/{fake_file_id}/download', headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'FILE_NOT_FOUND'

    def test_file_info(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/info', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['file_id'] == self.test_file_id
        assert data['filename'] == self.test_file_name
        assert data['size'] == len(self.test_file_content)
        assert 'mime_type' in data
        assert 'upload_time' in data
        assert 'download_count' in data
        assert 'owner_id' in data

    def test_file_list(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/files', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'files' in data
        assert 'pagination' in data
        assert len(data['files']) >= 1
        pagination = data['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total' in pagination
        assert 'pages' in pagination

    def test_file_list_with_pagination(self):
        self._login_user()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        params = {'page': 1, 'limit': 5}
        response = self.session.get(f'{self.BASE_URL}/files', headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 5

    def test_file_delete(self):
        self._login_user()
        self._upload_test_file()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.delete(f'{self.BASE_URL}/files/{self.test_file_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'message' in data
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/info', headers=headers)
        assert response.status_code == 404

    def test_file_rename(self):
        self._login_user()
        self._upload_test_file()
        new_name = 'renamed_file.txt'
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        data = {'new_name': new_name}
        response = self.session.put(f'{self.BASE_URL}/files/{self.test_file_id}/rename', json=data, headers=headers)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['new_filename'] == new_name
        response = self.session.get(f'{self.BASE_URL}/files/{self.test_file_id}/info', headers=headers)
        assert response.status_code == 200
        file_info = response.json()
        assert file_info['filename'] == new_name

    def test_file_share_create(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': True, 'expires_in': 3600}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'share_id' in data
        assert 'share_url' in data
        assert 'expires_at' in data
        assert 'access_count' in data
        self.test_share_id = data['share_id']

    def test_file_share_with_password(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': False, 'expires_in': 3600, 'password': 'sharepass123'}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'share_id' in data

    def test_share_access(self):
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        response = self.session.get(f'{self.BASE_URL}/share/{self.test_share_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'file_info' in data
        assert 'download_url' in data
        assert data['file_info']['filename'] == self.test_file_name

    def test_share_access_with_password(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': False, 'expires_in': 3600, 'password': 'sharepass123'}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        share_id = response.json()['share_id']
        response = self.session.get(f'{self.BASE_URL}/share/{share_id}')
        assert response.status_code == 401
        params = {'password': 'sharepass123'}
        response = self.session.get(f'{self.BASE_URL}/share/{share_id}', params=params)
        assert response.status_code == 200

    def test_share_delete(self):
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.delete(f'{self.BASE_URL}/share/{self.test_share_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        response = self.session.get(f'{self.BASE_URL}/share/{self.test_share_id}')
        assert response.status_code == 404

    def test_storage_quota(self):
        self._login_user()
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(f'{self.BASE_URL}/storage/quota', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'used_space' in data
        assert 'total_space' in data
        assert 'available_space' in data
        assert 'usage_percentage' in data
        assert data['used_space'] >= 0
        assert data['total_space'] > 0
        assert data['available_space'] >= 0
        assert 0 <= data['usage_percentage'] <= 100

    def test_file_upload_large_file(self):
        self._login_user()
        large_content = b'x' * (99 * 1024 * 1024)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(large_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('large_file.bin', f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            if response.status_code == 200:
                data = response.json()
                assert data['success'] is True
            else:
                data = response.json()
                assert data['success'] is False
                assert data['error_code'] in ['FILE_TOO_LARGE', 'QUOTA_EXCEEDED']
        finally:
            os.unlink(temp_file_path)

    def test_file_upload_oversized_file(self):
        self._login_user()
        oversized_content = b'x' * (101 * 1024 * 1024)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(oversized_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('oversized_file.bin', f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            assert response.status_code == 413
            data = response.json()
            assert data['success'] is False
            assert data['error_code'] == 'FILE_TOO_LARGE'
        finally:
            os.unlink(temp_file_path)

    def test_share_expired(self):
        self._login_user()
        self._upload_test_file()
        share_data = {'is_public': True, 'expires_in': 1}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        share_id = response.json()['share_id']
        import time
        time.sleep(2)
        response = self.session.get(f'{self.BASE_URL}/share/{share_id}')
        assert response.status_code == 410
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'SHARE_EXPIRED'

    def _login_user(self):
        self.session.post(f'{self.BASE_URL}/auth/register', json=self.test_user)
        login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
        response = self.session.post(f'{self.BASE_URL}/auth/login', json=login_data)
        self.auth_token = response.json()['token']

    def _upload_test_file(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
            self.test_file_id = response.json()['file_id']
        finally:
            os.unlink(temp_file_path)

    def _create_share_link(self):
        share_data = {'is_public': True, 'expires_in': 3600}
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/{self.test_file_id}/share', json=share_data, headers=headers)
        self.test_share_id = response.json()['share_id']

def test_file_upload_single(self):
    self._login_user()
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(self.test_file_content)
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': (self.test_file_name, f, 'text/plain')}
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'file_id' in data
        assert data['filename'] == self.test_file_name
        assert data['size'] == len(self.test_file_content)
        assert 'upload_time' in data
        assert 'download_url' in data
        self.test_file_id = data['file_id']
    finally:
        os.unlink(temp_file_path)

def test_file_upload_without_auth(self):
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(self.test_file_content)
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': (self.test_file_name, f, 'text/plain')}
            response = self.session.post(f'{self.BASE_URL}/files/upload', files=files)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'AUTH_REQUIRED'
    finally:
        os.unlink(temp_file_path)

def test_file_upload_multiple(self):
    self._login_user()
    temp_files = []
    file_names = ['file1.txt', 'file2.txt', 'file3.txt']
    try:
        for i, name in enumerate(file_names):
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
                content = f'Test content for {name}'.encode()
                f.write(content)
                temp_files.append((f.name, name, content))
        files = []
        for temp_path, name, _ in temp_files:
            files.append(('files', (name, open(temp_path, 'rb'), 'text/plain')))
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.post(f'{self.BASE_URL}/files/upload-multiple', files=files, headers=headers)
        for _, (_, file_obj, _) in enumerate(files):
            file_obj[1][1].close()
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['uploaded_files']) == 3
        assert len(data['failed_files']) == 0
        for uploaded_file in data['uploaded_files']:
            assert 'file_id' in uploaded_file
            assert uploaded_file['status'] == 'success'
    finally:
        for temp_path, _, _ in temp_files:
            os.unlink(temp_path)

def test_file_upload_large_file(self):
    self._login_user()
    large_content = b'x' * (99 * 1024 * 1024)
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
        f.write(large_content)
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('large_file.bin', f, 'application/octet-stream')}
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert data['success'] is True
        else:
            data = response.json()
            assert data['success'] is False
            assert data['error_code'] in ['FILE_TOO_LARGE', 'QUOTA_EXCEEDED']
    finally:
        os.unlink(temp_file_path)

def test_file_upload_oversized_file(self):
    self._login_user()
    oversized_content = b'x' * (101 * 1024 * 1024)
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
        f.write(oversized_content)
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('oversized_file.bin', f, 'application/octet-stream')}
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
        assert response.status_code == 413
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'FILE_TOO_LARGE'
    finally:
        os.unlink(temp_file_path)

def _upload_test_file(self):
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(self.test_file_content)
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': (self.test_file_name, f, 'text/plain')}
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(f'{self.BASE_URL}/files/upload', files=files, headers=headers)
        self.test_file_id = response.json()['file_id']
    finally:
        os.unlink(temp_file_path)

@pytest.fixture
def temp_file(test_file_content: bytes, test_file_name: str) -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(test_file_content)
        temp_file_path = f.name
    yield temp_file_path
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

class TestEmailStatus:
    """Test cases for GET /api/v1/mail/status/{mail_id} endpoint."""

    def test_get_status_success(self):
        """Test successfully retrieving status of sent email."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Test Email', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        assert send_response.status_code == 200
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['mail_id'] == mail_id
        assert 'status' in data
        assert data['status'] in ['pending', 'sent', 'failed', 'delivered', 'bounced']
        assert 'to' in data
        assert 'subject' in data
        assert 'sent_at' in data
        assert 'delivered_at' in data
        assert 'error' in data
        if data['sent_at']:
            datetime.fromisoformat(data['sent_at'].replace('Z', '+00:00'))

    def test_get_status_nonexistent_mail_id(self):
        """Test retrieving status with non-existent mail_id returns 404."""
        fake_mail_id = 'nonexistent-mail-id-12345'
        response = requests.get(f'{STATUS_URL}/{fake_mail_id}')
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data

    def test_get_status_invalid_mail_id_format(self):
        """Test retrieving status with invalid mail_id format."""
        invalid_mail_id = 'invalid@#$%'
        response = requests.get(f'{STATUS_URL}/{invalid_mail_id}')
        assert response.status_code in [400, 404]
        data = response.json()
        assert 'error' in data

    def test_get_status_empty_mail_id(self):
        """Test retrieving status with empty mail_id."""
        response = requests.get(f'{STATUS_URL}/')
        assert response.status_code in [400, 404, 405]

    def test_get_status_pending_email(self):
        """Test status of newly sent email should be pending or sent."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Pending Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] in ['pending', 'sent']

    def test_get_status_fields_presence(self):
        """Test that all required fields are present in status response."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Field Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        required_fields = ['mail_id', 'status', 'to', 'subject', 'sent_at', 'delivered_at', 'error']
        for field in required_fields:
            assert field in data

    def test_get_status_to_field_format(self):
        """Test that 'to' field is returned as a list."""
        send_payload = {'to': ['user1@example.com', 'user2@example.com'], 'subject': 'Multi-recipient Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['to'], list)
        assert len(data['to']) == 2

    def test_get_status_error_field_null_on_success(self):
        """Test that error field is null when email is successful."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Success Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        if data['status'] not in ['failed', 'bounced']:
            assert data['error'] is None or data['error'] == ''

    def test_get_status_multiple_queries_same_email(self):
        """Test querying same email status multiple times."""
        send_payload = {'to': ['user@example.com'], 'subject': 'Multiple Query Test', 'body': 'Test body'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()['mail_id']
        for _ in range(3):
            response = requests.get(f'{STATUS_URL}/{mail_id}')
            assert response.status_code == 200
            data = response.json()
            assert data['mail_id'] == mail_id

    def test_get_status_different_emails(self):
        """Test querying status of different emails."""
        mail_ids = []
        for i in range(3):
            send_payload = {'to': [f'user{i}@example.com'], 'subject': f'Email {i}', 'body': f'Body {i}'}
            send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
            mail_ids.append(send_response.json()['mail_id'])
        for i, mail_id in enumerate(mail_ids):
            response = requests.get(f'{STATUS_URL}/{mail_id}')
            assert response.status_code == 200
            data = response.json()
            assert data['mail_id'] == mail_id
            assert data['subject'] == f'Email {i}'

def test_get_status_different_emails(self):
    """Test querying status of different emails."""
    mail_ids = []
    for i in range(3):
        send_payload = {'to': [f'user{i}@example.com'], 'subject': f'Email {i}', 'body': f'Body {i}'}
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_ids.append(send_response.json()['mail_id'])
    for i, mail_id in enumerate(mail_ids):
        response = requests.get(f'{STATUS_URL}/{mail_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['mail_id'] == mail_id
        assert data['subject'] == f'Email {i}'

def test_languages_get_request():
    """Test GET request to languages endpoint"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    assert data['success'] == True, 'Request should succeed'
    assert 'languages' in data, 'Languages should be present in response'
    print(f'✓ Test passed: GET request to languages endpoint')

def test_languages_consistency():
    """Test that multiple requests return consistent results"""
    response1 = requests.get(LANGUAGES_ENDPOINT)
    response2 = requests.get(LANGUAGES_ENDPOINT)
    assert response1.status_code == 200, 'First request should succeed'
    assert response2.status_code == 200, 'Second request should succeed'
    data1 = response1.json()
    data2 = response2.json()
    assert data1['success'] == data2['success'], 'Success status should be consistent'
    assert len(data1['languages']) == len(data2['languages']), 'Number of languages should be consistent'
    print(f'✓ Test passed: Responses are consistent')

def test_languages_count():
    """Test that a reasonable number of languages are supported"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    data = response.json()
    languages = data['languages']
    lang_count = len(languages)
    assert lang_count >= 5, f'Should support at least 5 languages, got {lang_count}'
    assert lang_count <= 200, f'Language count seems unreasonable: {lang_count}'
    print(f'✓ Test passed: Reasonable number of languages ({lang_count})')

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f'\n{'=' * 70}')
    print(f'Running: {test_file}')
    print('=' * 70)
    try:
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.stderr:
            print('STDERR:', result.stderr)
        output = result.stdout
        passed = 0
        failed = 0
        for line in output.split('\n'):
            if 'passed' in line and 'failed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if 'passed' in parts[i + 1] if i + 1 < len(parts) else False:
                            passed = int(part)
                        elif 'failed' in parts[i + 1] if i + 1 < len(parts) else False:
                            failed = int(part)
        if passed == 0 and failed == 0:
            if result.returncode == 0:
                with open(test_file, 'r') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                    passed = test_count
            else:
                with open(test_file, 'r') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                    failed = test_count
        return {'file': test_file, 'passed': passed, 'failed': failed, 'exit_code': result.returncode, 'success': result.returncode == 0}
    except subprocess.TimeoutExpired:
        print(f'✗ Test timeout: {test_file}')
        return {'file': test_file, 'passed': 0, 'failed': 1, 'exit_code': -1, 'success': False}
    except Exception as e:
        print(f'✗ Error running test: {e}')
        return {'file': test_file, 'passed': 0, 'failed': 1, 'exit_code': -1, 'success': False}

# Node: count
def print_summary(results, metrics):
    """Print test summary and metrics"""
    print('\n' + '=' * 70)
    print('TEST SUMMARY')
    print('=' * 70)
    for result in results:
        status = '✓ PASS' if result['success'] else '✗ FAIL'
        print(f'{status} | {result['file']}')
        print(f'       | Passed: {result['passed']}, Failed: {result['failed']}')
    print('\n' + '=' * 70)
    print('METRICS')
    print('=' * 70)
    print(f'Test Case Pass Rate:')
    print(f'  - Total Tests: {metrics['total_tests']}')
    print(f'  - Passed: {metrics['total_passed']}')
    print(f'  - Failed: {metrics['total_failed']}')
    print(f'  - Pass Rate: {metrics['test_pass_rate']:.2f}%')
    print()
    print(f'Repository Pass Rate:')
    print(f'  - Total Test Files: {metrics['repos_total']}')
    print(f'  - Passed: {metrics['repos_passed']}')
    print(f'  - Failed: {metrics['repos_total'] - metrics['repos_passed']}')
    print(f'  - Pass Rate: {metrics['repo_pass_rate']:.2f}%')
    print('=' * 70)

class TestFuzzySearch:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [{'name': 'Introduction to Python', 'category': 'Programming', 'score': 90.0}, {'name': 'Advanced Python', 'category': 'Programming', 'score': 95.0}, {'name': 'Python for Data Science', 'category': 'Science', 'score': 92.0}, {'name': 'Java Programming', 'category': 'Programming', 'score': 85.0}, {'name': 'JavaScript Basics', 'category': 'Web', 'score': 88.0}]
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        time.sleep(0.1)
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_fuzzy_search_by_name(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        assert len(items) >= 3
        for item in items:
            assert 'Python' in item['name'] or 'python' in item['name'].lower()

    def test_fuzzy_search_partial_match(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Java', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        assert len(items) >= 2

    def test_fuzzy_search_case_sensitivity(self):
        response_lower = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'python', 'page_size': 100})
        response_upper = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'PYTHON', 'page_size': 100})
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        items_lower = response_lower.json()['data']['items']
        items_upper = response_upper.json()['data']['items']
        assert len(items_lower) == len(items_upper)

    def test_fuzzy_search_no_match(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Nonexistent', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) == 0

def test_fuzzy_search_by_name(self):
    response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'page_size': 100})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    items = data['data']['items']
    assert len(items) >= 3
    for item in items:
        assert 'Python' in item['name'] or 'python' in item['name'].lower()

class TestCombinedFeatures:

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [{'name': 'Python Basics', 'category': 'Programming', 'score': 85.0}, {'name': 'Python Advanced', 'category': 'Programming', 'score': 95.0}, {'name': 'Python Expert', 'category': 'Programming', 'score': 92.0}, {'name': 'Java Basics', 'category': 'Programming', 'score': 80.0}, {'name': 'Data Analysis', 'category': 'Science', 'score': 90.0}]
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()['data']['id'])
        time.sleep(0.1)
        yield
        for test_id in self.test_ids:
            try:
                requests.delete(f'{API_ENDPOINT}/{test_id}')
            except:
                pass

    def test_search_with_sort(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'Programming', 'sort_by': 'score', 'sort_order': 'desc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        for item in items:
            assert item['category'] == 'Programming'
        scores = [item['score'] for item in items]
        assert scores == sorted(scores, reverse=True)

    def test_fuzzy_search_with_sort(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'sort_by': 'score', 'sort_order': 'asc', 'page_size': 100})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        items = data['data']['items']
        for item in items:
            assert 'Python' in item['name'] or 'python' in item['name'].lower()
        scores = [item['score'] for item in items]
        assert scores == sorted(scores)

    def test_search_with_pagination_and_sort(self):
        response = requests.get(API_ENDPOINT, params={'search_field': 'category', 'search_value': 'Programming', 'sort_by': 'name', 'sort_order': 'asc', 'page': 1, 'page_size': 2})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 2
        assert data['data']['pagination']['page'] == 1
        items = data['data']['items']
        for item in items:
            assert item['category'] == 'Programming'
        names = [item['name'] for item in items]
        assert names == sorted(names)

    def test_fuzzy_search_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'page': 1, 'page_size': 2})
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']['items']) <= 2
        assert data['data']['pagination']['page_size'] == 2

def test_fuzzy_search_with_sort(self):
    response = requests.get(API_ENDPOINT, params={'fuzzy_field': 'name', 'fuzzy_value': 'Python', 'sort_by': 'score', 'sort_order': 'asc', 'page_size': 100})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    items = data['data']['items']
    for item in items:
        assert 'Python' in item['name'] or 'python' in item['name'].lower()
    scores = [item['score'] for item in items]
    assert scores == sorted(scores)

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    BASE_URL = 'http://localhost:8081/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/users')
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/users/{user['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_username_boundary_values(self):
        """Test username at boundary values"""
        min_username = 'abc'
        user_data = {'username': min_username, 'email': 'min@example.com', 'password': 'TestPass123!', 'full_name': 'Min Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == min_username
        max_username = 'a' * 50
        user_data = {'username': max_username, 'email': 'max@example.com', 'password': 'TestPass123!', 'full_name': 'Max Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == max_username
        too_short_username = 'ab'
        user_data = {'username': too_short_username, 'email': 'tooshort@example.com', 'password': 'TestPass123!', 'full_name': 'Too Short User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        too_long_username = 'a' * 51
        user_data = {'username': too_long_username, 'email': 'toolong@example.com', 'password': 'TestPass123!', 'full_name': 'Too Long User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_full_name_boundary_values(self):
        """Test full name at boundary values"""
        max_full_name = 'a' * 100
        user_data = {'username': 'test_max_fullname', 'email': 'maxfullname@example.com', 'password': 'TestPass123!', 'full_name': max_full_name, 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['full_name'] == max_full_name
        too_long_full_name = 'a' * 101
        user_data = {'username': 'test_too_long_fullname', 'email': 'toolongfullname@example.com', 'password': 'TestPass123!', 'full_name': too_long_full_name, 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_password_boundary_values(self):
        """Test password at boundary values"""
        min_password = 'Test123!'
        user_data = {'username': 'test_min_password', 'email': 'minpassword@example.com', 'password': min_password, 'full_name': 'Min Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        too_short_password = 'Test12!'
        user_data = {'username': 'test_too_short_password', 'email': 'tooshortpassword@example.com', 'password': too_short_password, 'full_name': 'Too Short Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_unicode_characters_in_user_data(self):
        """Test handling of Unicode characters in user data"""
        unicode_user = {'username': 'test_unicode_user', 'email': 'unicode@example.com', 'password': 'TestPass123!', 'full_name': 'Unicode User 🚀 Test', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=unicode_user, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            data = response.json()
            assert data['full_name'] == unicode_user['full_name']

    def test_special_characters_in_username(self):
        """Test handling of special characters in username"""
        special_chars_usernames = ['test_user@domain', 'test user', 'test.user', 'test-user', 'test_user_123']
        for i, username in enumerate(special_chars_usernames):
            user_data = {'username': username, 'email': f'special{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Special Char User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]

    def test_email_formats(self):
        """Test various email formats"""
        email_formats = ['test@example.com', 'test.user@example.com', 'test+tag@example.com', 'test123@example-domain.com', 'test@sub.example.com', 'test@example.co.uk']
        for i, email in enumerate(email_formats):
            user_data = {'username': f'test_email_{i}', 'email': email, 'password': 'TestPass123!', 'full_name': f'Email Test User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201

    def test_invalid_email_formats(self):
        """Test invalid email formats"""
        invalid_emails = ['not-an-email', '@example.com', 'test@', 'test..test@example.com', 'test@.example.com', 'test@example..com', 'test@example.com.', 'test@example', 'test@.com']
        for i, email in enumerate(invalid_emails):
            user_data = {'username': f'test_invalid_email_{i}', 'email': email, 'password': 'TestPass123!', 'full_name': f'Invalid Email User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_phone_formats(self):
        """Test various phone number formats"""
        phone_formats = ['+1234567890', '+1-234-567-8900', '+1 (234) 567-8900', '1234567890', '+44 20 7946 0958', '+86 138 0013 8000']
        for i, phone in enumerate(phone_formats):
            user_data = {'username': f'test_phone_{i}', 'email': f'phone{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Phone Test User {i}', 'role': 'user', 'phone': phone}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]

    def test_empty_strings(self):
        """Test handling of empty strings"""
        user_data = {'username': '', 'email': 'empty@example.com', 'password': 'TestPass123!', 'full_name': 'Empty Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        user_data = {'username': 'test_empty_email', 'email': '', 'password': 'TestPass123!', 'full_name': 'Empty Email User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        user_data = {'username': 'test_empty_fullname', 'email': 'emptyfullname@example.com', 'password': 'TestPass123!', 'full_name': '', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_whitespace_only_strings(self):
        """Test handling of whitespace-only strings"""
        user_data = {'username': '   ', 'email': 'whitespace@example.com', 'password': 'TestPass123!', 'full_name': 'Whitespace Username User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        user_data = {'username': 'test_whitespace_fullname', 'email': 'whitespacefullname@example.com', 'password': 'TestPass123!', 'full_name': '   ', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_null_values(self):
        """Test handling of null values"""
        user_data = {'username': 'test_null_values', 'email': 'null@example.com', 'password': 'TestPass123!', 'full_name': 'Null Values User', 'role': 'user', 'phone': None}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_extra_fields(self):
        """Test handling of extra fields in request"""
        user_data = {'username': 'test_extra_fields', 'email': 'extra@example.com', 'password': 'TestPass123!', 'full_name': 'Extra Fields User', 'role': 'user', 'extra_field': 'should be ignored', 'another_field': 123, 'nested_field': {'key': 'value'}}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'extra_field' not in data
        assert 'another_field' not in data
        assert 'nested_field' not in data

    def test_case_sensitivity(self):
        """Test case sensitivity of enum values"""
        user_data = {'username': 'test_case_sensitivity', 'email': 'case@example.com', 'password': 'TestPass123!', 'full_name': 'Case Sensitivity User', 'role': 'USER'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_large_numbers(self):
        """Test handling of large numbers in pagination"""
        response = requests.get(f'{self.BASE_URL}/users?page=999999')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/users?limit=999999')
        assert response.status_code in [200, 422]

    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        response = requests.get(f'{self.BASE_URL}/users?page=-1')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/users?limit=-1')
        assert response.status_code in [200, 422]

    def test_zero_values(self):
        """Test handling of zero values"""
        response = requests.get(f'{self.BASE_URL}/users?page=0')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/users?limit=0')
        assert response.status_code in [200, 422]

    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts"""
        malicious_inputs = ["'; DROP TABLE users; --", "1' OR '1'='1", "admin'--", '1; DELETE FROM users; --', "'; INSERT INTO users VALUES ('hacker', 'hack@evil.com', 'password', 'Hacker', 'admin'); --"]
        for i, malicious_input in enumerate(malicious_inputs):
            user_data = {'username': f'test_sql_{i}', 'email': f'sql{i}@example.com', 'password': 'TestPass123!', 'full_name': malicious_input, 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_xss_attempts(self):
        """Test protection against XSS attempts"""
        xss_payloads = ["<script>alert('xss')</script>", "javascript:alert('xss')", "<img src=x onerror=alert('xss')>", "';alert('xss');//", "<svg onload=alert('xss')>", 'javascript:/*-/*`/*\\`/*\'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>']
        for i, payload in enumerate(xss_payloads):
            user_data = {'username': f'test_xss_{i}', 'email': f'xss{i}@example.com', 'password': 'TestPass123!', 'full_name': payload, 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_concurrent_user_creation(self):
        """Test handling of concurrent user creation"""
        import threading
        import time
        results = []
        errors = []

        def create_user(thread_id):
            try:
                user_data = {'username': f'test_concurrent_{thread_id}', 'email': f'concurrent{thread_id}@example.com', 'password': 'TestPass123!', 'full_name': f'Concurrent User {thread_id}', 'role': 'user'}
                response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors in concurrent user creation: {errors}'
        assert len(results) == 10
        for thread_id, status_code in results:
            assert status_code == 201

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = ['{"username": "test", "email": "test@example.com"', '{"username": "test", "email": "test@example.com",}', '{"username": "test", "email": test@example.com}', '{"username": "test" "email": "test@example.com"}', '{"username": "test", "email": "test@example.com", "role": }']
        for malformed_json in malformed_jsons:
            response = requests.post(f'{self.BASE_URL}/users', data=malformed_json, headers={'Content-Type': 'application/json'})
            assert response.status_code == 400

    def test_content_type_variations(self):
        """Test handling of different content types"""
        user_data = {'username': 'test_content_type', 'email': 'contenttype@example.com', 'password': 'TestPass123!', 'full_name': 'Content Type User', 'role': 'user'}
        content_types = ['application/json', 'application/json; charset=utf-8', 'application/json;charset=utf-8', 'text/json', 'text/plain']
        for content_type in content_types:
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': content_type})
            assert response.status_code in [201, 400, 415]
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_missing_headers(self):
        """Test handling of missing headers"""
        user_data = {'username': 'test_no_headers', 'email': 'noheaders@example.com', 'password': 'TestPass123!', 'full_name': 'No Headers User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data)
        assert response.status_code in [201, 400, 415]
        if response.status_code == 201:
            user_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_very_long_url(self):
        """Test handling of very long URLs"""
        long_params = '&'.join([f'param{i}=value{i}' for i in range(100)])
        response = requests.get(f'{self.BASE_URL}/users?{long_params}')
        assert response.status_code in [200, 414, 400]

    def test_password_strength_requirements(self):
        """Test password strength requirements"""
        weak_passwords = ['12345678', 'abcdefgh', 'ABCDEFGH', '!@#$%^&*', 'Test123', 'testuser', 'TESTUSER', '123456789']
        for i, password in enumerate(weak_passwords):
            user_data = {'username': f'test_weak_password_{i}', 'email': f'weakpassword{i}@example.com', 'password': password, 'full_name': f'Weak Password User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_strong_passwords(self):
        """Test acceptance of strong passwords"""
        strong_passwords = ['TestPass123!', 'MyStr0ng#Pass', 'ComplexP@ssw0rd', 'Secure123$Pass', 'StrongP@ss1!']
        for i, password in enumerate(strong_passwords):
            user_data = {'username': f'test_strong_password_{i}', 'email': f'strongpassword{i}@example.com', 'password': password, 'full_name': f'Strong Password User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            user_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/users/{user_id}')

    def test_username_alphanumeric_requirement(self):
        """Test username alphanumeric requirement"""
        invalid_usernames = ['user@name', 'user name', 'user.name', 'user-name', 'user_name!', 'user#name', 'user$name']
        for i, username in enumerate(invalid_usernames):
            user_data = {'username': username, 'email': f'invalidusername{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Invalid Username User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_valid_usernames(self):
        """Test acceptance of valid usernames"""
        valid_usernames = ['user123', 'testuser', 'User123', 'test_user_123', 'user123test', 'a1b2c3', 'test123user']
        for i, username in enumerate(valid_usernames):
            user_data = {'username': username, 'email': f'validusername{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Valid Username User {i}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            user_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/users/{user_id}')

def test_special_characters_in_username(self):
    """Test handling of special characters in username"""
    special_chars_usernames = ['test_user@domain', 'test user', 'test.user', 'test-user', 'test_user_123']
    for i, username in enumerate(special_chars_usernames):
        user_data = {'username': username, 'email': f'special{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Special Char User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

def test_email_formats(self):
    """Test various email formats"""
    email_formats = ['test@example.com', 'test.user@example.com', 'test+tag@example.com', 'test123@example-domain.com', 'test@sub.example.com', 'test@example.co.uk']
    for i, email in enumerate(email_formats):
        user_data = {'username': f'test_email_{i}', 'email': email, 'password': 'TestPass123!', 'full_name': f'Email Test User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201

def test_invalid_email_formats(self):
    """Test invalid email formats"""
    invalid_emails = ['not-an-email', '@example.com', 'test@', 'test..test@example.com', 'test@.example.com', 'test@example..com', 'test@example.com.', 'test@example', 'test@.com']
    for i, email in enumerate(invalid_emails):
        user_data = {'username': f'test_invalid_email_{i}', 'email': email, 'password': 'TestPass123!', 'full_name': f'Invalid Email User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

def test_phone_formats(self):
    """Test various phone number formats"""
    phone_formats = ['+1234567890', '+1-234-567-8900', '+1 (234) 567-8900', '1234567890', '+44 20 7946 0958', '+86 138 0013 8000']
    for i, phone in enumerate(phone_formats):
        user_data = {'username': f'test_phone_{i}', 'email': f'phone{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Phone Test User {i}', 'role': 'user', 'phone': phone}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

def test_password_strength_requirements(self):
    """Test password strength requirements"""
    weak_passwords = ['12345678', 'abcdefgh', 'ABCDEFGH', '!@#$%^&*', 'Test123', 'testuser', 'TESTUSER', '123456789']
    for i, password in enumerate(weak_passwords):
        user_data = {'username': f'test_weak_password_{i}', 'email': f'weakpassword{i}@example.com', 'password': password, 'full_name': f'Weak Password User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

def test_username_alphanumeric_requirement(self):
    """Test username alphanumeric requirement"""
    invalid_usernames = ['user@name', 'user name', 'user.name', 'user-name', 'user_name!', 'user#name', 'user$name']
    for i, username in enumerate(invalid_usernames):
        user_data = {'username': username, 'email': f'invalidusername{i}@example.com', 'password': 'TestPass123!', 'full_name': f'Invalid Username User {i}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

class TestUserAPI:
    """Test suite for User Management API endpoints"""
    BASE_URL = 'http://localhost:8081/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/users')
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f'{self.BASE_URL}/users/{user['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f'{self.BASE_URL}/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert 'database' in data
        assert data['status'] == 'healthy'

    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {'username': 'test_user_001', 'email': 'test@example.com', 'password': 'TestPass123!', 'full_name': 'Test User', 'role': 'user', 'phone': '+1234567890'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['full_name'] == user_data['full_name']
        assert data['role'] == user_data['role']
        assert data['phone'] == user_data['phone']
        assert data['status'] == 'active'
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'password' not in data

    def test_create_user_minimal_data(self):
        """Test user creation with minimal required data"""
        user_data = {'username': 'test_minimal', 'email': 'minimal@example.com', 'password': 'MinPass123!', 'full_name': 'Minimal User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['full_name'] == user_data['full_name']
        assert data['role'] == user_data['role']
        assert data['status'] == 'active'
        assert data['phone'] is None or data['phone'] == ''

    def test_create_user_invalid_role(self):
        """Test user creation with invalid role"""
        user_data = {'username': 'test_invalid_role', 'email': 'invalid@example.com', 'password': 'TestPass123!', 'full_name': 'Invalid Role User', 'role': 'invalid_role'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'validation_error'

    def test_create_user_missing_required_fields(self):
        """Test user creation with missing required fields"""
        user_data = {'email': 'missing@example.com'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username"""
        user_data = {'username': 'test_duplicate', 'email': 'duplicate1@example.com', 'password': 'TestPass123!', 'full_name': 'Duplicate User 1', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_data['email'] = 'duplicate2@example.com'
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 409
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'conflict'

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        user_data = {'username': 'test_duplicate_email_1', 'email': 'duplicate@example.com', 'password': 'TestPass123!', 'full_name': 'Duplicate Email User 1', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_data['username'] = 'test_duplicate_email_2'
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 409
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'conflict'

    def test_create_user_invalid_email_format(self):
        """Test user creation with invalid email format"""
        user_data = {'username': 'test_invalid_email', 'email': 'invalid-email-format', 'password': 'TestPass123!', 'full_name': 'Invalid Email User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_create_user_weak_password(self):
        """Test user creation with weak password"""
        user_data = {'username': 'test_weak_password', 'email': 'weak@example.com', 'password': '123', 'full_name': 'Weak Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_get_users_list_empty(self):
        """Test getting users list when no users exist"""
        response = requests.get(f'{self.BASE_URL}/users')
        assert response.status_code == 200
        data = response.json()
        assert 'users' in data
        assert 'pagination' in data
        assert len(data['users']) == 0
        assert data['pagination']['total'] == 0

    def test_get_users_list_with_data(self):
        """Test getting users list with existing users"""
        users_data = [{'username': 'test_list_1', 'email': 'list1@example.com', 'password': 'TestPass123!', 'full_name': 'List User 1', 'role': 'user'}, {'username': 'test_list_2', 'email': 'list2@example.com', 'password': 'TestPass123!', 'full_name': 'List User 2', 'role': 'admin'}, {'username': 'test_list_3', 'email': 'list3@example.com', 'password': 'TestPass123!', 'full_name': 'List User 3', 'role': 'moderator'}]
        created_users = []
        for user_data in users_data:
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            created_users.append(response.json())
        response = requests.get(f'{self.BASE_URL}/users')
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) >= 3
        assert data['pagination']['total'] >= 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10

    def test_get_users_list_pagination(self):
        """Test users list pagination"""
        for i in range(15):
            user_data = {'username': f'test_pagination_{i + 1}', 'email': f'pagination{i + 1}@example.com', 'password': 'TestPass123!', 'full_name': f'Pagination User {i + 1}', 'role': 'user'}
            response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
        response = requests.get(f'{self.BASE_URL}/users?page=1&limit=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 15
        assert data['pagination']['pages'] >= 2
        response = requests.get(f'{self.BASE_URL}/users?page=2&limit=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) >= 5
        assert data['pagination']['page'] == 2

    def test_get_users_list_filter_by_role(self):
        """Test filtering users by role"""
        roles = ['user', 'admin', 'moderator']
        for role in roles:
            user_data = {'username': f'test_role_{role}', 'email': f'role_{role}@example.com', 'password': 'TestPass123!', 'full_name': f'Role {role.title()} User', 'role': role}
            requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/users?role=admin')
        assert response.status_code == 200
        data = response.json()
        admin_users = [user for user in data['users'] if user['role'] == 'admin']
        assert len(admin_users) >= 1

    def test_get_users_list_filter_by_status(self):
        """Test filtering users by status"""
        user_data = {'username': 'test_status_filter', 'email': 'status@example.com', 'password': 'TestPass123!', 'full_name': 'Status Filter User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'inactive'}, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/users?status=inactive')
        assert response.status_code == 200
        data = response.json()
        inactive_users = [user for user in data['users'] if user['status'] == 'inactive']
        assert len(inactive_users) >= 1

    def test_get_users_list_search(self):
        """Test searching users by username, email, or full_name"""
        user_data = {'username': 'test_search_unique', 'email': 'search_unique@example.com', 'password': 'TestPass123!', 'full_name': 'Unique Search User', 'role': 'user'}
        requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        response = requests.get(f'{self.BASE_URL}/users?search=test_search_unique')
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'test_search_unique' in user['username']]
        assert len(found_users) >= 1
        response = requests.get(f'{self.BASE_URL}/users?search=search_unique@example.com')
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'search_unique@example.com' in user['email']]
        assert len(found_users) >= 1
        response = requests.get(f'{self.BASE_URL}/users?search=Unique Search')
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'Unique Search' in user['full_name']]
        assert len(found_users) >= 1

    def test_get_single_user_success(self):
        """Test getting a single user by ID"""
        user_data = {'username': 'test_single_user', 'email': 'single@example.com', 'password': 'TestPass123!', 'full_name': 'Single User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        created_user = response.json()
        response = requests.get(f'{self.BASE_URL}/users/{created_user['id']}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == created_user['id']
        assert data['username'] == created_user['username']
        assert data['email'] == created_user['email']
        assert data['role'] == created_user['role']

    def test_get_single_user_not_found(self):
        """Test getting a non-existent user"""
        response = requests.get(f'{self.BASE_URL}/users/99999')
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_update_user_success(self):
        """Test successful user update"""
        user_data = {'username': 'test_update_user', 'email': 'update@example.com', 'password': 'TestPass123!', 'full_name': 'Original User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        update_data = {'username': 'test_updated_user', 'email': 'updated@example.com', 'full_name': 'Updated User', 'role': 'moderator', 'status': 'inactive'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == update_data['username']
        assert data['email'] == update_data['email']
        assert data['full_name'] == update_data['full_name']
        assert data['role'] == update_data['role']
        assert data['status'] == update_data['status']
        assert data['id'] == user_id

    def test_update_user_partial(self):
        """Test partial user update"""
        user_data = {'username': 'test_partial_update', 'email': 'partial@example.com', 'password': 'TestPass123!', 'full_name': 'Original Full Name', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        update_data = {'full_name': 'Updated Full Name Only'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert data['full_name'] == update_data['full_name']
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['role'] == user_data['role']

    def test_update_user_invalid_role(self):
        """Test user update with invalid role"""
        user_data = {'username': 'test_invalid_role_update', 'email': 'invalid_role@example.com', 'password': 'TestPass123!', 'full_name': 'Invalid Role User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        update_data = {'role': 'invalid_role'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_update_user_not_found(self):
        """Test updating a non-existent user"""
        update_data = {'full_name': 'Updated User'}
        response = requests.put(f'{self.BASE_URL}/users/99999', json=update_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_delete_user_success(self):
        """Test successful user deletion"""
        user_data = {'username': 'test_delete_user', 'email': 'delete@example.com', 'password': 'TestPass123!', 'full_name': 'User to Delete', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        response = requests.delete(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        response = requests.get(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 404

    def test_delete_user_not_found(self):
        """Test deleting a non-existent user"""
        response = requests.delete(f'{self.BASE_URL}/users/99999')
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_user_workflow_complete(self):
        """Test complete user workflow: create -> update -> deactivate -> delete"""
        user_data = {'username': 'test_workflow_user', 'email': 'workflow@example.com', 'password': 'TestPass123!', 'full_name': 'Workflow User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_id = response.json()['id']
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json={'role': 'moderator'}, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        assert response.json()['role'] == 'moderator'
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'inactive'}, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        assert response.json()['status'] == 'inactive'
        response = requests.get(f'{self.BASE_URL}/users?status=inactive')
        assert response.status_code == 200
        inactive_users = response.json()['users']
        inactive_user_ids = [user['id'] for user in inactive_users]
        assert user_id in inactive_user_ids
        response = requests.delete(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 200
        response = requests.get(f'{self.BASE_URL}/users/{user_id}')
        assert response.status_code == 404

    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body"""
        response = requests.post(f'{self.BASE_URL}/users', data='invalid json', headers={'Content-Type': 'application/json'})
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_missing_content_type_header(self):
        """Test handling of missing Content-Type header"""
        user_data = {'username': 'test_no_content_type', 'email': 'no_content_type@example.com', 'password': 'TestPass123!', 'full_name': 'No Content Type User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data)
        assert response.status_code in [201, 400, 415]

    def test_large_pagination_limit(self):
        """Test pagination with limit exceeding maximum"""
        response = requests.get(f'{self.BASE_URL}/users?limit=1000')
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100

def test_get_users_list_filter_by_role(self):
    """Test filtering users by role"""
    roles = ['user', 'admin', 'moderator']
    for role in roles:
        user_data = {'username': f'test_role_{role}', 'email': f'role_{role}@example.com', 'password': 'TestPass123!', 'full_name': f'Role {role.title()} User', 'role': role}
        requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
    response = requests.get(f'{self.BASE_URL}/users?role=admin')
    assert response.status_code == 200
    data = response.json()
    admin_users = [user for user in data['users'] if user['role'] == 'admin']
    assert len(admin_users) >= 1

@pytest.mark.upload
def test_upload_image_file(api_base_url, auth_headers, sample_image_file):
    """Test uploading an image file"""
    file_obj, filename, content_type = sample_image_file
    files = {'file': (filename, file_obj, content_type)}
    data = {'description': 'Test image upload'}
    resp = requests.post(f'{api_base_url}/files', headers=auth_headers, files=files, data=data, timeout=30)
    assert resp.status_code in (200, 201)
    file_data = resp.json()
    assert 'id' in file_data
    assert file_data.get('filename') == filename
    assert 'image' in file_data.get('content_type', '').lower() or filename.endswith('.png')
    file_id = file_data.get('id')
    if file_id:
        requests.delete(f'{api_base_url}/files/{file_id}', headers=auth_headers, timeout=10)

class TestLeaderboardRetrieval:
    """Test leaderboard retrieval functionality."""

    def test_get_leaderboard_success(self, api_base_url):
        """Test successful leaderboard retrieval."""
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        assert 'leaderboard' in data
        assert 'time_range' in data
        assert 'game_type' in data
        assert 'total_players' in data
        assert isinstance(data['leaderboard'], list)
        assert isinstance(data['total_players'], int)

    def test_get_leaderboard_with_filters(self, api_base_url):
        """Test leaderboard retrieval with filters."""
        response = make_request('GET', f'{api_base_url}/leaderboard?game_type=battle')
        assert_response_success(response, 200)
        data = response.json()
        assert data['game_type'] == 'battle'
        time_ranges = ['daily', 'weekly', 'monthly', 'all']
        for time_range in time_ranges:
            response = make_request('GET', f'{api_base_url}/leaderboard?time_range={time_range}')
            assert_response_success(response, 200)
            data = response.json()
            assert data['time_range'] == time_range
        response = make_request('GET', f'{api_base_url}/leaderboard?limit=10')
        assert_response_success(response, 200)
        data = response.json()
        assert len(data['leaderboard']) <= 10

    def test_get_leaderboard_invalid_filters(self, api_base_url):
        """Test leaderboard retrieval with invalid filters."""
        response = make_request('GET', f'{api_base_url}/leaderboard?game_type=invalid')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/leaderboard?time_range=invalid')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/leaderboard?limit=2000')
        assert_response_error(response, 400)
        response = make_request('GET', f'{api_base_url}/leaderboard?limit=-1')
        assert_response_error(response, 400)

    def test_get_leaderboard_ranking_order(self, api_base_url, sample_leaderboard_data):
        """Test that leaderboard returns scores in correct ranking order."""
        for i, score_data in enumerate(sample_leaderboard_data):
            response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
            assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        leaderboard = data['leaderboard']
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]['score'] >= leaderboard[i + 1]['score']
        for i, entry in enumerate(leaderboard):
            assert entry['rank'] == i + 1

    def test_get_leaderboard_entry_structure(self, api_base_url, sample_score_data):
        """Test that leaderboard entries have correct structure."""
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=sample_score_data)
        assert_response_success(response, 200)
        response = make_request('GET', f'{api_base_url}/leaderboard')
        assert_response_success(response, 200)
        data = response.json()
        leaderboard = data['leaderboard']
        if leaderboard:
            entry = leaderboard[0]
            assert 'rank' in entry
            assert 'player_id' in entry
            assert 'player_name' in entry
            assert 'score' in entry
            assert 'game_type' in entry
            assert 'updated_at' in entry
            assert isinstance(entry['rank'], int)
            assert validate_uuid(entry['player_id'])
            assert isinstance(entry['player_name'], str)
            assert isinstance(entry['score'], int)
            assert entry['game_type'] in ['battle', 'coop', 'puzzle']
            assert validate_iso8601(entry['updated_at'])

def test_get_leaderboard_ranking_order(self, api_base_url, sample_leaderboard_data):
    """Test that leaderboard returns scores in correct ranking order."""
    for i, score_data in enumerate(sample_leaderboard_data):
        response = make_request('POST', f'{api_base_url}/leaderboard/score', json=score_data)
        assert_response_success(response, 200)
    response = make_request('GET', f'{api_base_url}/leaderboard')
    assert_response_success(response, 200)
    data = response.json()
    leaderboard = data['leaderboard']
    if len(leaderboard) > 1:
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]['score'] >= leaderboard[i + 1]['score']
    for i, entry in enumerate(leaderboard):
        assert entry['rank'] == i + 1

def check_dependencies():
    """Check if required dependencies are installed."""
    print('Checking dependencies...')
    try:
        import pytest
        import requests
        print('✅ Core dependencies found')
        return True
    except ImportError as e:
        print(f'❌ Missing dependency: {e}')
        print('Please install dependencies with: pip install -r requirements.txt')
        return False

class TestUserAPI:
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_user = {'username': 'testuser', 'email': 'test@example.com', 'password': 'password123', 'full_name': 'Test User'}
        self.access_token = None
        self.user_id = None

    def test_user_registration_success(self):
        response = requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert 'user_id' in data['data']
        assert data['data']['username'] == self.test_user['username']
        assert data['data']['email'] == self.test_user['email']
        assert data['data']['full_name'] == self.test_user['full_name']
        assert 'created_at' in data['data']
        self.user_id = data['data']['user_id']

    def test_user_registration_duplicate_username(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        response = requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'username' in data['message'].lower()

    def test_user_registration_invalid_email(self):
        invalid_user = self.test_user.copy()
        invalid_user['email'] = 'invalid-email'
        response = requests.post(f'{self.BASE_URL}/users/register', json=invalid_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'email' in data['message'].lower()

    def test_user_registration_short_password(self):
        invalid_user = self.test_user.copy()
        invalid_user['password'] = '123'
        response = requests.post(f'{self.BASE_URL}/users/register', json=invalid_user)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'password' in data['message'].lower()

    def test_user_login_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_data = {'username': self.test_user['username'], 'password': self.test_user['password']}
        response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert data['data']['token_type'] == 'Bearer'
        assert 'expires_in' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['username'] == self.test_user['username']
        self.access_token = data['data']['access_token']
        self.user_id = data['data']['user']['user_id']

    def test_user_login_invalid_credentials(self):
        login_data = {'username': 'nonexistent', 'password': 'wrongpassword'}
        response = requests.post(f'{self.BASE_URL}/users/login', json=login_data)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'credentials' in data['message'].lower() or 'invalid' in data['message'].lower()

    def test_get_user_info_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{self.BASE_URL}/users/{user_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['user_id'] == user_id
        assert data['data']['username'] == self.test_user['username']
        assert data['data']['email'] == self.test_user['email']
        assert data['data']['full_name'] == self.test_user['full_name']
        assert 'created_at' in data['data']
        assert 'updated_at' in data['data']

    def test_get_user_info_unauthorized(self):
        response = requests.get(f'{self.BASE_URL}/users/1')
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'authorization' in data['message'].lower() or 'token' in data['message'].lower()

    def test_get_user_info_invalid_token(self):
        headers = {'Authorization': 'Bearer invalid_token'}
        response = requests.get(f'{self.BASE_URL}/users/1', headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False

    def test_update_user_info_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        update_data = {'email': 'newemail@example.com', 'full_name': 'Updated Name'}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['email'] == update_data['email']
        assert data['data']['full_name'] == update_data['full_name']
        assert data['data']['username'] == self.test_user['username']
        assert 'updated_at' in data['data']

    def test_update_user_info_unauthorized(self):
        update_data = {'email': 'newemail@example.com'}
        response = requests.put(f'{self.BASE_URL}/users/1', json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False

    def test_update_user_info_invalid_email(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        update_data = {'email': 'invalid-email'}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.put(f'{self.BASE_URL}/users/{user_id}', json=update_data, headers=headers)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'email' in data['message'].lower()

    def test_delete_user_success(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.delete(f'{self.BASE_URL}/users/{user_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        get_response = requests.get(f'{self.BASE_URL}/users/{user_id}', headers=headers)
        assert get_response.status_code == 404

    def test_delete_user_unauthorized(self):
        response = requests.delete(f'{self.BASE_URL}/users/1')
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False

    def test_delete_nonexistent_user(self):
        requests.post(f'{self.BASE_URL}/users/register', json=self.test_user)
        login_response = requests.post(f'{self.BASE_URL}/users/login', json={'username': self.test_user['username'], 'password': self.test_user['password']})
        token = login_response.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.delete(f'{self.BASE_URL}/users/99999', headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False

def test_get_user_info_unauthorized(self):
    response = requests.get(f'{self.BASE_URL}/users/1')
    assert response.status_code == 401
    data = response.json()
    assert data['success'] is False
    assert 'authorization' in data['message'].lower() or 'token' in data['message'].lower()

