# Cluster 10

def read_readme(repo_root: Path) -> str:
    readme_files = [repo_root / 'README.md', repo_root / 'readme.md', repo_root / 'README', repo_root / 'Readme.md']
    for f in readme_files:
        if f.exists():
            return f.read_text(encoding='utf-8', errors='ignore')
    raise FileNotFoundError(f'README not found under {repo_root}')

# Node: exists
# Node: read_text
# Node: FileNotFoundError
def read_pom(repo_root: Path) -> str:
    pom_file = repo_root / 'pom.xml'
    if pom_file.exists():
        return pom_file.read_text(encoding='utf-8', errors='ignore')
    return ''

# Node: Path
# Node: resolve
def main() -> None:
    parser = argparse.ArgumentParser(description='Generate and evaluate repos with agents')
    parser.add_argument('--agent', required=True, help='Agent name under agent folder (e.g., metagpt)')
    parser.add_argument('--repo_root', required=True, help='Repo root directory')
    parser.add_argument('--repo', required=True, help='Target repo name under repo_scratch (e.g., Blog)')
    parser.add_argument('--workspace', default='/Volumes/T7/Real_Swe-bench/code', help='Workspace root path')
    parser.add_argument('--metagpt_config', default='', help='Optional MetaGPT config yaml path')
    parser.add_argument('--llm_model', default='', help='Override LLM model (e.g., gpt-4o-mini)')
    parser.add_argument('--llm_base_url', default='', help='Override LLM base URL (e.g., https://api.openai.com/v1)')
    parser.add_argument('--llm_api_key', default='', help='Override LLM API key (or rely on OPENAI_API_KEY)')
    parser.add_argument('--llm', help='Override LLM (e.g., gpt-5-mini)')
    parser.add_argument('--deepcode_openai_key', default='', help='OPENAI_API_KEY for DeepCode if not set in env')
    parser.add_argument('--run_tests', default=False, action='store_true', help='Run tests')
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    if args.repo.lower() == 'all':
        base_dir = workspace / args.repo_root
        if not base_dir.exists():
            raise FileNotFoundError(f'Base directory not found: {base_dir}')
        for entry in sorted((p.name for p in base_dir.iterdir() if p.is_dir())):
            process_single_repo(args, workspace, entry)
    else:
        process_single_repo(args, workspace, args.repo)

# Node: ArgumentParser
# Node: add_argument
# Node: parse_args
# Node: iterdir
# Node: is_dir
# Node: process_single_repo
# Node: dump
def find_file_recursive(root_path: str, filename: str, max_depth: int=5) -> Optional[str]:
    """Find a file recursively up to max_depth."""
    root_path_obj = Path(root_path)
    if (root_path_obj / filename).exists():
        return str(root_path_obj / filename)
    for path in root_path_obj.rglob(filename):
        try:
            rel_path = path.relative_to(root_path_obj)
            if len(rel_path.parts) <= max_depth + 1:
                return str(path)
        except ValueError:
            continue
    return None

# Node: rglob
# Node: relative_to
def main():
    parser = argparse.ArgumentParser(description='Test DSR for repositories')
    parser.add_argument('--shard', type=int, nargs=2, metavar=('INDEX', 'TOTAL'), help='Shard index and total shards (0-indexed)')
    parser.add_argument('--output', type=str, default=RESULTS_FILE, help='Output JSON file')
    parser.add_argument('--port-base', type=int, default=8000, help='Base port for testing (default: 8000)')
    args = parser.parse_args()
    print('=' * 80)
    print('Testing DSR for All Repositories in repos (Nested Support)')
    if args.shard:
        print(f'Shard: {args.shard[0]}/{args.shard[1]}')
    print(f'Port Base: {args.port_base}')
    print('=' * 80)
    print()
    base_path = Path(BASE_DIR)
    all_repo_dirs = sorted([d.name for d in base_path.iterdir() if d.is_dir()])
    if args.shard:
        shard_idx, total_shards = args.shard
        chunk_size = (len(all_repo_dirs) + total_shards - 1) // total_shards
        start_idx = shard_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(all_repo_dirs))
        repo_dirs = all_repo_dirs[start_idx:end_idx]
    else:
        repo_dirs = all_repo_dirs
    all_results = {}
    total_dirs_count = len(repo_dirs)
    current_dir_idx = 0
    for repo_dir in repo_dirs:
        current_dir_idx += 1
        print(f'\n{'=' * 80}')
        print(f'[{current_dir_idx}/{total_dirs_count}] Testing directory: {repo_dir}')
        print(f'{'=' * 80}')
        dir_path = os.path.join(BASE_DIR, repo_dir)
        repos = sorted([d.name for d in Path(dir_path).iterdir() if d.is_dir()])
        dir_results = {}
        success_count = 0
        total_count = len(repos)
        for idx, repo_name in enumerate(repos, 1):
            print(f'-- Repo [{idx}/{total_count}]: {repo_name}')
            repo_path = os.path.join(dir_path, repo_name)
            success, message, repo_type = test_repository(repo_name, repo_path, args.port_base)
            dir_results[repo_name] = {'success': success, 'message': message, 'type': repo_type}
            if success:
                success_count += 1
                print(f'  ✓ {repo_name}')
            else:
                print(f'  ✗ {repo_name}: {message}')
        dsr = success_count / total_count if total_count > 0 else 0
        all_results[repo_dir] = {'total': total_count, 'success': success_count, 'failed': total_count - success_count, 'dsr': dsr, 'repositories': dir_results}
        print(f'\nDirectory DSR: {dsr:.4f} ({success_count}/{total_count})')
        output_data = {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'status': 'in_progress', 'results_by_directory': all_results}
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
    total_repos = sum((r['total'] for r in all_results.values()))
    total_success = sum((r['success'] for r in all_results.values()))
    overall_dsr = total_success / total_repos if total_repos > 0 else 0
    print('\n' + '=' * 80)
    print('OVERALL SUMMARY')
    print('=' * 80)
    print()
    for repo_dir in repo_dirs:
        if repo_dir in all_results:
            r = all_results[repo_dir]
            print(f'{repo_dir:<60} DSR: {r['dsr']:.4f} ({r['success']}/{r['total']})')
    print(f'\nTotal: {total_repos}, Success: {total_success}, DSR: {overall_dsr:.4f}')
    output_data['status'] = 'completed'
    output_data['total_repositories'] = total_repos
    output_data['total_success'] = total_success
    output_data['total_failed'] = total_repos - total_success
    output_data['overall_dsr'] = overall_dsr
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

# Node: min
# Node: test_repository
def read_readme(repo_root: Path) -> str:
    readme_files = [repo_root / 'README.md', repo_root / 'readme.md', repo_root / 'README', repo_root / 'Readme.md']
    for f in readme_files:
        if f.exists():
            return f.read_text(encoding='utf-8', errors='ignore')
    raise FileNotFoundError(f'README not found under {repo_root}')

def read_requirements(repo_root: Path) -> str:
    req_file = repo_root / 'requirements.txt'
    if req_file.exists():
        return req_file.read_text(encoding='utf-8', errors='ignore')
    return ''

def main() -> None:
    parser = argparse.ArgumentParser(description='Generate and evaluate repos with agents')
    parser.add_argument('--agent', required=True, help='Agent name under agent folder (e.g., metagpt)')
    parser.add_argument('--repo_root', required=True, help='Repo root directory')
    parser.add_argument('--repo', required=True, help='Target repo name under repo_scratch (e.g., Blog)')
    parser.add_argument('--workspace', default='/Volumes/T7/Real_Swe-bench/code', help='Workspace root path')
    parser.add_argument('--metagpt_config', default='', help='Optional MetaGPT config yaml path')
    parser.add_argument('--llm_model', default='', help='Override LLM model (e.g., gpt-4o-mini)')
    parser.add_argument('--llm_base_url', default='', help='Override LLM base URL (e.g., https://api.openai.com/v1)')
    parser.add_argument('--llm_api_key', default='', help='Override LLM API key (or rely on OPENAI_API_KEY)')
    parser.add_argument('--llm', help='Override LLM (e.g., gpt-5-mini)')
    parser.add_argument('--deepcode_openai_key', default='', help='OPENAI_API_KEY for DeepCode if not set in env')
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    if args.repo.lower() == 'all':
        base_dir = workspace / args.repo_root
        if not base_dir.exists():
            raise FileNotFoundError(f'Base directory not found: {base_dir}')
        for entry in sorted((p.name for p in base_dir.iterdir() if p.is_dir())):
            process_single_repo(args, workspace, entry)
    else:
        process_single_repo(args, workspace, args.repo)

def install_requirements(requirements_path):
    """Install dependencies from a requirements.txt file."""
    print(f'Installing requirements from {requirements_path}...')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
    except subprocess.CalledProcessError as e:
        print(f'Failed to install requirements from {requirements_path}: {e}')

# Node: check_call
def evaluate_repo(repo_name, answer_repo_path, test_repo_path):
    print(f'=== Evaluating {repo_name} ===')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest', 'pytest-cov', 'uvicorn', 'requests', 'fastapi', 'flask', 'django'])
    except subprocess.CalledProcessError as e:
        print(f'Warning: Failed to install global dependencies: {e}. Continuing assuming they are present or managed externally.')
    reqs = find_files_recursive(answer_repo_path, 'requirements.txt')
    for req in reqs:
        install_requirements(req)
    start_scripts = find_files_recursive(answer_repo_path, 'start.sh')
    service_process = None
    if start_scripts:
        start_scripts.sort(key=lambda x: len(x.split(os.sep)))
        script_to_run = start_scripts[0]
        service_process = start_service(script_to_run)
        print('Waiting 10 seconds for service to start...')
        time.sleep(10)
    else:
        print('No start.sh found!')
    test_reqs = find_files_recursive(test_repo_path, 'requirements.txt')
    for req in test_reqs:
        install_requirements(req)
    if os.path.abspath(answer_repo_path) != os.path.abspath(test_repo_path):
        print(f'Copying tests from {test_repo_path} to {answer_repo_path}...')
        tests_src = os.path.join(test_repo_path, 'tests')
        tests_dst = os.path.join(answer_repo_path, 'tests')
        if os.path.exists(tests_src):
            if os.path.exists(tests_dst):
                print(f'Removing existing tests at {tests_dst}...')
                subprocess.run(['rm', '-rf', tests_dst], check=True)
            subprocess.run(['cp', '-R', tests_src, answer_repo_path], check=True)
            print(f'Copied tests to {tests_dst}')
        else:
            print(f"Warning: No 'tests' directory found in {test_repo_path}")
    test_output, return_code = run_pytest(os.path.join(answer_repo_path, 'tests'), answer_repo_path)
    print('Test output:', test_output)
    print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
    if service_process:
        kill_process_group(service_process)
    passed, failed_pytest, coverage = parse_pytest_output(test_output)
    total_tests = count_tests_ast(os.path.join(test_repo_path, 'tests'))
    if total_tests == 0:
        print(f'Warning: AST found 0 tests in {test_repo_path}. Using pytest output count.')
        total_tests = passed + failed_pytest
        failed = failed_pytest
    else:
        pytest_total = passed + failed_pytest
        if total_tests < pytest_total:
            print(f'Note: AST count ({total_tests}) is lower than pytest total ({pytest_total}). This is likely due to parameterized tests.')
            total_tests = pytest_total
        failed = total_tests - passed
    pass_rate = passed / total_tests if total_tests > 0 else 0.0
    files, loc, tokens = count_lines_and_tokens(answer_repo_path)
    return {'repo': repo_name, 'pass_rate': pass_rate, 'passed': passed, 'failed': failed, 'coverage': coverage, 'files': files, 'loc': loc, 'tokens': tokens}

# Node: find_files_recursive
# Node: install_requirements
# Node: sort
# Node: start_service
# Node: run_pytest
# Node: kill_process_group
# Node: parse_pytest_output
# Node: count_tests_ast
# Node: count_lines_and_tokens
def main():
    parser = argparse.ArgumentParser(description='Evaluate repositories.')
    parser.add_argument('--answer_dir', default='/Volumes/T7/Real_Swe-bench/code/repo_readme_1128_msagent_answer')
    parser.add_argument('--test_dir', default='/Volumes/T7/Real_Swe-bench/code/repo_readme_test_oracle')
    parser.add_argument('--output', default='evaluation_results.json')
    parser.add_argument('--filter', help='Filter repos by name')
    args = parser.parse_args()
    results = []
    if not os.path.exists(args.answer_dir):
        print(f'Answer directory {args.answer_dir} does not exist.')
        return
    repos = [d for d in os.listdir(args.answer_dir) if os.path.isdir(os.path.join(args.answer_dir, d))]
    repos.sort()
    for repo in repos:
        if args.filter and args.filter not in repo:
            continue
        answer_repo_path = os.path.join(args.answer_dir, repo)
        test_repo_path = os.path.join(args.test_dir, repo)
        if not os.path.exists(test_repo_path):
            print(f'Test repo for {repo} not found at {test_repo_path}. Skipping.')
            continue
        try:
            metrics = evaluate_repo(repo, answer_repo_path, test_repo_path)
            results.append(metrics)
            print(f'Result for {repo}: {metrics}')
        except Exception as e:
            print(f'Error evaluating {repo}: {e}')
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f'Results saved to {args.output}')

# Node: evaluate_repo
def fix_test_structure(answer_dir):
    """
    Fixes the test structure if tests are in a 'tests' directory
    but Maven expects them in 'src/test/java'.
    """
    src_test_java = os.path.join(answer_dir, 'src', 'test', 'java')
    tests_dir = os.path.join(answer_dir, 'tests')
    if not os.path.exists(src_test_java) and os.path.exists(tests_dir):
        print(f"Detected 'tests' directory but no 'src/test/java'. Moving tests...")
        os.makedirs(src_test_java, exist_ok=True)
        subprocess.run(['cp', '-R', f'{tests_dir}/.', src_test_java], check=True)
        print(f'Moved tests from {tests_dir} to {src_test_java}')

# Node: makedirs
def evaluate_repo(repo_name, answer_repo_path, test_repo_path):
    print(f'=== Evaluating {repo_name} ===')
    service_process = start_service(answer_repo_path)
    if service_process:
        print('Waiting 15 seconds for service to start...')
        time.sleep(15)
    if os.path.abspath(answer_repo_path) != os.path.abspath(test_repo_path):
        print(f'Copying tests from {test_repo_path} to {answer_repo_path}...')
        src_test = os.path.join(test_repo_path, 'src', 'test')
        tests_dir = os.path.join(test_repo_path, 'tests')
        if os.path.exists(src_test):
            subprocess.run(['cp', '-R', src_test, os.path.join(answer_repo_path, 'src')], check=False)
        elif os.path.exists(tests_dir):
            subprocess.run(['cp', '-R', tests_dir, answer_repo_path], check=False)
    fix_test_structure(answer_repo_path)
    fix_pom_java_version(answer_repo_path)
    test_output, return_code = run_java_tests(test_repo_path, answer_repo_path)
    kill_process_group(service_process)
    passed, failed_xml, skipped = parse_java_test_output(answer_repo_path, test_output)
    test_src_dir = os.path.join(answer_repo_path, 'src', 'test')
    if not os.path.exists(test_src_dir):
        test_src_dir = answer_repo_path
    total_tests_ast = count_tests_java(test_src_dir)
    reported_total = passed + failed_xml + skipped
    if total_tests_ast > reported_total:
        print(f'Warning: AST counted {total_tests_ast} tests, but execution reported {reported_total}.')
        total_tests = total_tests_ast
        failed = total_tests - passed - skipped
    else:
        total_tests = reported_total
        failed = failed_xml
    pass_rate = passed / total_tests if total_tests > 0 else 0.0
    files, loc, tokens = count_lines_and_tokens_java(answer_repo_path)
    return {'repo': repo_name, 'pass_rate': pass_rate, 'passed': passed, 'failed': failed, 'skipped': skipped, 'files': files, 'loc': loc, 'tokens': tokens}

# Node: fix_test_structure
# Node: fix_pom_java_version
# Node: run_java_tests
# Node: parse_java_test_output
# Node: count_tests_java
# Node: count_lines_and_tokens_java
def main():
    parser = argparse.ArgumentParser(description='Evaluate Java repositories.')
    parser.add_argument('--answer_dir', required=True)
    parser.add_argument('--test_dir', required=True)
    parser.add_argument('--output', default='evaluation_results_java.json')
    parser.add_argument('--filter', help='Filter repos by name')
    args = parser.parse_args()
    results = []
    if not os.path.exists(args.answer_dir):
        print(f'Answer directory {args.answer_dir} does not exist.')
        return
    is_single_repo = os.path.exists(os.path.join(args.answer_dir, 'pom.xml')) or os.path.exists(os.path.join(args.answer_dir, 'src'))
    if is_single_repo:
        repos = [os.path.basename(args.answer_dir)]
        base_answer_dir = os.path.dirname(args.answer_dir)
        base_test_dir = os.path.dirname(args.test_dir)
    else:
        repos = [d for d in os.listdir(args.answer_dir) if os.path.isdir(os.path.join(args.answer_dir, d))]
        repos.sort()
        base_answer_dir = args.answer_dir
        base_test_dir = args.test_dir
    for repo in repos:
        if args.filter and args.filter not in repo:
            continue
        if is_single_repo:
            answer_repo_path = args.answer_dir
            test_repo_path = args.test_dir
        else:
            answer_repo_path = os.path.join(base_answer_dir, repo)
            test_repo_path = os.path.join(base_test_dir, repo)
        if not os.path.exists(test_repo_path):
            print(f'Test repo for {repo} not found at {test_repo_path}. Skipping.')
            continue
        try:
            metrics = evaluate_repo(repo, answer_repo_path, test_repo_path)
            results.append(metrics)
            print(f'Result for {repo}: {metrics}')
        except Exception as e:
            print(f'Error evaluating {repo}: {e}')
            import traceback
            traceback.print_exc()
    output_file = os.path.join('exps/evaluation_results', args.output)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'Results saved to {output_file}')

def main():
    """Main test runner"""
    try:
        response = requests.get(f'{BASE_URL}/', timeout=2)
        print(f'Service is reachable at {BASE_URL}\n')
    except requests.exceptions.RequestException as e:
        print(f'ERROR: Cannot reach service at {BASE_URL}')
        print(f'Please ensure the RBAC service is running on port 8080')
        print(f'Error: {e}')
        sys.exit(1)
    tester = RBACServiceTester(BASE_URL)
    repo_pass = tester.run_all_tests()
    sys.exit(0 if repo_pass == 1 else 1)

# Node: RBACServiceTester
# Node: run_all_tests
def main():
    parser = argparse.ArgumentParser(description='Blog CMS API Test Runner')
    parser.add_argument('--pattern', '-p', help='Test pattern (e.g., test_01_*)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Generate coverage report')
    parser.add_argument('--parallel', '-n', action='store_true', help='Run tests in parallel')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    args = parser.parse_args()
    if args.check_deps:
        if check_dependencies():
            print('All dependencies are installed')
            return 0
        else:
            return 1
    if not check_dependencies():
        return 1
    return run_tests(test_pattern=args.pattern, verbose=args.verbose, coverage=args.coverage, parallel=args.parallel)

# Node: check_dependencies
# Node: run_tests
def main():
    parser = argparse.ArgumentParser(description='WebPan API Test Runner')
    parser.add_argument('--type', choices=['all', 'auth', 'upload', 'download', 'share', 'storage', 'unit', 'integration', 'fast', 'slow'], default='all', help='Type of tests to run')
    parser.add_argument('--quiet', action='store_true', help='Run tests in quiet mode')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML test report')
    args = parser.parse_args()
    cmd = ['python', '-m', 'pytest']
    if not args.quiet:
        cmd.append('-v')
    if args.coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
    if args.html_report:
        cmd.extend(['--html=test_report.html', '--self-contained-html'])
    if args.type == 'auth':
        cmd.extend(['-m', 'auth'])
    elif args.type == 'upload':
        cmd.extend(['-m', 'upload'])
    elif args.type == 'download':
        cmd.extend(['-m', 'download'])
    elif args.type == 'share':
        cmd.extend(['-m', 'share'])
    elif args.type == 'storage':
        cmd.extend(['-m', 'storage'])
    elif args.type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif args.type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif args.type == 'fast':
        cmd.extend(['-m', 'not slow'])
    elif args.type == 'slow':
        cmd.extend(['-m', 'slow'])
    else:
        cmd.append('.')
    cmd.append('.')
    print(f'Running WebPan API tests...')
    print(f'Command: {' '.join(cmd)}')
    print('-' * 50)
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print('\n✅ All tests passed!')
        else:
            print('\n❌ Some tests failed!')
        return result.returncode
    except KeyboardInterrupt:
        print('\n⚠️  Test execution interrupted by user')
        return 1
    except Exception as e:
        print(f'\n💥 Error running tests: {e}')
        return 1

@pytest.mark.skipif(jsonschema is None, reason='jsonschema is required for contract validation')
def test_readme_present_and_sections():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    assert os.path.exists(readme_path), 'README.md must exist'
    content = open(readme_path, 'r', encoding='utf-8').read()
    required_sections = ['Service Information', 'Interface Overview', 'Input and Output Schemas', 'Evaluation Metrics', 'Testing Instructions']
    for section in required_sections:
        assert section in content, f'README should include section: {section}'

class LargeFileIO:

    def __init__(self, size):
        self.size = size
        self.pos = 0

    def read(self, size=-1):
        if size == -1:
            size = self.size - self.pos
        if self.pos >= self.size:
            return b''
        chunk = min(size, self.size - self.pos)
        self.pos += chunk
        return b'x' * chunk

    def seek(self, pos):
        self.pos = pos

    def tell(self):
        return self.pos

def read(self, size=-1):
    if size == -1:
        size = self.size - self.pos
    if self.pos >= self.size:
        return b''
    chunk = min(size, self.size - self.pos)
    self.pos += chunk
    return b'x' * chunk

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='GameBackend API Test Runner')
    parser.add_argument('command', choices=['all', 'room', 'leaderboard', 'game-state', 'smoke', 'integration', 'unit', 'coverage', 'parallel', 'lint', 'format'], help='Test command to run')
    parser.add_argument('--test', help='Run specific test file or function')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies before running tests')
    args = parser.parse_args()
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
    tests_dir = Path(__file__).parent
    os.chdir(tests_dir)
    success = True
    if args.command == 'all':
        success = run_all_tests()
    elif args.command == 'room':
        success = run_room_matching_tests()
    elif args.command == 'leaderboard':
        success = run_leaderboard_tests()
    elif args.command == 'game-state':
        success = run_game_state_tests()
    elif args.command == 'smoke':
        success = run_smoke_tests()
    elif args.command == 'integration':
        success = run_integration_tests()
    elif args.command == 'unit':
        success = run_unit_tests()
    elif args.command == 'coverage':
        success = run_with_coverage()
    elif args.command == 'parallel':
        success = run_parallel_tests()
    elif args.command == 'lint':
        success = lint_code()
    elif args.command == 'format':
        success = format_code()
    if args.test:
        success = run_specific_test(args.test)
    if success:
        print(f'\n{'=' * 60}')
        print('🎉 All operations completed successfully!')
        print(f'{'=' * 60}')
        sys.exit(0)
    else:
        print(f'\n{'=' * 60}')
        print('💥 Some operations failed!')
        print(f'{'=' * 60}')
        sys.exit(1)

# Node: run_room_matching_tests
# Node: run_leaderboard_tests
# Node: run_game_state_tests
# Node: run_smoke_tests
# Node: run_integration_tests
# Node: run_unit_tests
# Node: run_with_coverage
# Node: run_parallel_tests
# Node: lint_code
# Node: format_code
# Node: run_specific_test
