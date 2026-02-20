# Cluster 1

def ensure_conda_available() -> str:
    conda_exe = shutil.which('conda')
    if not conda_exe:
        raise RuntimeError('conda is required but was not found on PATH')
    return conda_exe

# Node: which
# Node: RuntimeError
def create_pytest_env(env_name: str, requirements_file: Optional[Path]) -> None:
    conda_exe = ensure_conda_available()
    subprocess.run([conda_exe, 'create', '-y', '-n', env_name, 'python=3.10'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run([conda_exe, 'run', '-n', env_name, 'python', '-m', 'pip', 'install', '--upgrade', 'pip', 'pytest'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if requirements_file and requirements_file.exists():
        subprocess.run([conda_exe, 'run', '-n', env_name, 'python', '-m', 'pip', 'install', '-r', str(requirements_file)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Node: ensure_conda_available
# Node: run
# Node: str
def metagpt_generate(repo_root: Path, readme_text: str, pom_text: str, run_tests: bool=False) -> None:
    import sys
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_meta_path = os.path.join(workspace_root, 'agent', 'MetaGPT')
    if agent_meta_path not in sys.path and os.path.isdir(agent_meta_path):
        sys.path.insert(0, agent_meta_path)
    from metagpt.software_company import generate_repo
    ensure_event_loop()
    idea = textwrap.dedent(f'\n        You are a senior Java software engineer tasked with implementing a complete software project.\n\n        Project Requirements:\n        README:\n        {readme_text}\n\n        POM.xml (reference):\n        {pom_text}\n\n        Your task:\n        1. Analyze the README and referenced POM to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (pom.xml is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use port specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port specified in the README.\n        7. Write production-ready, well-documented code.\n        8. Use Maven.\n\n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    generate_repo(idea=idea, project_name=repo_root.name, inc=False, project_path=str(repo_root), implement=True, run_tests=run_tests, code_review=True, n_round=5, investment=3.0)

# Node: dirname
# Node: abspath
# Node: isdir
# Node: insert
# Node: ensure_event_loop
# Node: strip
# Node: dedent
# Node: generate_repo
def deepcode_generate(repo_root: Path, readme_text: str, pom_text: str) -> None:
    """Use DeepCode workflows to synthesize code based on README into repo_root.
    Strategy:
    - Create an implementation plan file from the README in repo_root.
    - Invoke DeepCode CodeImplementationWorkflow in pure code mode targeting repo_root.
    - Move generated files from generate_code/ up to repo_root.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_deep_path = os.path.join(workspace_root, 'agent', 'DeepCode')
    if agent_deep_path not in sys.path and os.path.isdir(agent_deep_path):
        sys.path.insert(0, agent_deep_path)
    from workflows.code_implementation_workflow import CodeImplementationWorkflow
    repo_root.mkdir(parents=True, exist_ok=True)
    plan_path = repo_root / 'initial_plan.txt'
    plan_content = textwrap.dedent(f'\n        You are a senior Java software engineer tasked with implementing a complete software project.\n\n        Project Requirements:\n        README:\n        {readme_text}\n\n        POM.xml (reference):\n        {pom_text}\n\n        Your task:\n        1. Analyze the README and referenced POM to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (pom.xml is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use port specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port specified in the README.\n        7. Write production-ready, well-documented code.\n        8. Use Maven.\n\n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    plan_path.write_text(plan_content, encoding='utf-8')
    secrets_path = os.path.join(agent_deep_path, 'mcp_agent.secrets.yaml')
    config_path = os.path.join(agent_deep_path, 'mcp_agent.config.yaml')
    gen_dir = repo_root
    gen_dir.mkdir(parents=True, exist_ok=True)
    workflow = CodeImplementationWorkflow(config_path=secrets_path if os.path.isfile(secrets_path) else 'mcp_agent.secrets.yaml')
    cwd = os.getcwd()
    try:
        os.chdir(agent_deep_path)
        asyncio.run(workflow.run_workflow(plan_file_path=str(plan_path), target_directory=str(repo_root), pure_code_mode=True, enable_read_tools=True))
    finally:
        os.chdir(cwd)

# Node: mkdir
# Node: write_text
# Node: CodeImplementationWorkflow
# Node: isfile
# Node: getcwd
# Node: chdir
# Node: run_workflow
def qwen_agent_generate(repo_root: Path, readme_text: str, pom_text: str, args) -> None:
    """Use Qwen-Agent to synthesize code based on README into repo_root.
    Strategy:
    - Import Qwen-Agent from agent/Qwen-Agent.
    - Create an Assistant agent with code_interpreter tool.
    - Send a comprehensive prompt to implement the entire project per README.
    - Files will be generated in the current working directory (repo_root).
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_qwen_path = os.path.join(workspace_root, 'agent', 'Qwen-Agent')
    if agent_qwen_path not in sys.path and os.path.isdir(agent_qwen_path):
        sys.path.insert(0, agent_qwen_path)
    try:
        from qwen_agent.agents import Assistant
        from qwen_agent.utils.output_beautify import typewriter_print
    except ImportError as e:
        print(f'[qwen-agent] Failed to import Qwen-Agent: {e}')
        print('[qwen-agent] Creating placeholder files...')
        repo_root.mkdir(parents=True, exist_ok=True)
        marker = repo_root / 'AGENT.txt'
        marker.write_text('Generated by Qwen-Agent adapter (import failed)\n', encoding='utf-8')
        return
    repo_root.mkdir(parents=True, exist_ok=True)
    llm_cfg = None
    if args.llm_api_key:
        llm_cfg = {'model': args.llm, 'model_server': args.llm_base_url, 'api_key': args.llm_api_key}
    else:
        print('[qwen-agent] No API key found (DASHSCOPE_API_KEY or OPENAI_API_KEY)')
        print('[qwen-agent] Creating placeholder files...')
        marker = repo_root / 'AGENT.txt'
        marker.write_text('Generated by Qwen-Agent adapter (no API key)\n', encoding='utf-8')
        return
    system_instruction = textwrap.dedent(f'\n        You are a senior Java software engineer tasked with implementing a complete software project.\n        \n        Project Requirements:\n        README:\n        {readme_text}\n        \n        POM.xml (reference):\n        {pom_text}\n        \n        Your task:\n        1. Analyze the README and referenced POM to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (pom.xml is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use port specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port specified in the README.\n        7. Write production-ready, well-documented code.\n        8. Use Maven.\n        \n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    tools = ['code_interpreter']
    bot = Assistant(llm=llm_cfg, system_message=system_instruction, function_list=tools)
    implementation_prompt = textwrap.dedent(f'\n        Please implement the complete software project based on the README and POM requirements.\n        \n        Current working directory: {repo_root}\n        \n        Steps to follow:\n        1. First, analyze the requirements and create a project structure plan\n        2. Create all necessary directories using os.makedirs()\n        3. Implement all source code files with proper imports and dependencies\n        4. Create configuration files including pom.xml\n        5. Create a main entry point that can start the application\n        6. Test that the basic structure is correct\n        \n        Make sure to:\n        - Use proper file paths relative to current directory\n        - Include error handling and logging where appropriate\n        - Follow best practices for the technology stack\n        - Create a README.md with usage instructions\n        \n        Start implementing now!\n        ').strip()
    cwd = os.getcwd()
    try:
        os.chdir(str(repo_root))
        messages = [{'role': 'user', 'content': implementation_prompt}]
        response_text = ''
        print('[qwen-agent] Starting project implementation...')
        for response in bot.run(messages=messages):
            if isinstance(response, list) and response:
                for msg in response:
                    if msg.get('role') == 'assistant' and msg.get('content'):
                        content = msg['content']
                        response_text += content
                        print(content, end='', flush=True)
        print(f'\n[qwen-agent] Implementation completed in {repo_root}')
    except Exception as e:
        print(f'[qwen-agent] Error during implementation: {e}')
        marker = repo_root / 'AGENT.txt'
        marker.write_text(f'Generated by Qwen-Agent adapter (error: {e})\n', encoding='utf-8')
    finally:
        os.chdir(cwd)

# Node: Assistant
def ms_agent_generate(repo_root: Path, readme_text: str, pom_text: str, args) -> None:
    """Use MS-Agent to synthesize code based on README into repo_root.
    Strategy:
    - Import MS-Agent from agent/ms-agent.
    - Create an LLMAgent with code generation capabilities.
    - Send a comprehensive prompt to implement the entire project per README.
    - Files will be generated in the current working directory (repo_root).
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_ms_path = os.path.join(workspace_root, 'agent', 'ms-agent')
    if agent_ms_path not in sys.path and os.path.isdir(agent_ms_path):
        sys.path.insert(0, agent_ms_path)
    try:
        from ms_agent import LLMAgent
    except ImportError as e:
        print(f'[ms-agent] Failed to import MS-Agent: {e}')
        print('[ms-agent] Creating placeholder files...')
        repo_root.mkdir(parents=True, exist_ok=True)
        marker = repo_root / 'AGENT.txt'
        marker.write_text('Generated by MS-Agent adapter (import failed)\n', encoding='utf-8')
        return
    repo_root.mkdir(parents=True, exist_ok=True)
    implementation_prompt = textwrap.dedent(f'\n        You are a senior Java software engineer tasked with implementing a complete software project.\n\n        Project Requirements:\n        README:\n        {readme_text}\n\n        POM.xml (reference):\n        {pom_text}\n\n        Your task:\n        1. Analyze the README and referenced POM to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (pom.xml is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use port specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port specified in the README.\n        7. Write production-ready, well-documented code.\n        8. Use Maven.\n\n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    cwd = os.getcwd()
    try:
        os.chdir(str(repo_root))

        async def run_ms_agent():
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]]
            try:
                from omegaconf import OmegaConf
                config_dict = {'llm': {'service': 'openai', 'model': args.llm_model.strip()}, 'generation_config': {'temperature': 1, 'stream': True}, 'max_chat_round': 100, 'callbacks': []}
                if args.llm_api_key:
                    config_dict['llm']['openai_api_key'] = args.llm_api_key.strip()
                    api_key = args.llm_api_key
                    config_dict['llm']['openai_base_url'] = args.llm_base_url.strip()
                else:
                    raise RuntimeError('args.llm_api_key not provided')
                config = OmegaConf.create(config_dict)
                llm_agent = LLMAgent(config=config)
                print('[ms-agent] Starting project implementation...')
                result = await llm_agent.run(implementation_prompt)
                return result
            finally:
                sys.argv = original_argv
        result = asyncio.run(run_ms_agent())
        print(f'\n[ms-agent] Implementation completed in {repo_root}')
        if result:
            print(f'[ms-agent] Result summary: {str(result)[:200]}...')
    except Exception as e:
        print(f'[ms-agent] Error during implementation: {e}')
        import traceback
        traceback.print_exc()
        marker = repo_root / 'AGENT.txt'
        marker.write_text(f'Generated by MS-Agent adapter (error: {e})\n', encoding='utf-8')
    finally:
        os.chdir(cwd)

# Node: create
# Node: LLMAgent
# Node: run_ms_agent
# Node: print_exc
def start_service(command: str, repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')
    proc = subprocess.Popen(command, cwd=str(repo_root), env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc

# Node: setdefault
# Node: Popen
def run_pytest_in_env(env_name: str, repo_root: Path) -> Tuple[int, str]:
    conda_exe = ensure_conda_available()
    cmd = [conda_exe, 'run', '-n', env_name, 'pytest', '-q']
    proc = subprocess.run(cmd, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return (proc.returncode, proc.stdout)

def terminate_process(proc: Optional[subprocess.Popen]) -> None:
    if not proc:
        return
    if proc.poll() is None:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except Exception:
                pass

# Node: poll
# Node: terminate
# Node: wait
# Node: kill
def write_temp_metagpt_config(model: str, base_url: str, api_key: str) -> Path:
    """Write a minimal MetaGPT config2.yaml to a temp file and return its path."""
    content = textwrap.dedent(f'\n        llm:\n          api_type: "openai"\n          model: "{model}"\n          base_url: "{base_url}"\n          api_key: "{api_key}"\n        ').strip() + '\n'
    tmpdir = Path(tempfile.mkdtemp(prefix='metagpt_cfg_'))
    cfg = tmpdir / 'config2.yaml'
    cfg.write_text(content, encoding='utf-8')
    return cfg

# Node: mkdtemp
def git_backup_repo(workspace: Path, repo_root: Path, message: str) -> str:
    """Create a git commit backing up the repo_root subtree. Return commit id (HEAD).
    If there is nothing to commit, still return current HEAD.
    """
    rel = os.path.relpath(str(repo_root), str(workspace))
    subprocess.run(['git', 'add', '-A', '--', rel], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    commit = subprocess.run(['git', 'commit', '-m', message, '--no-gpg-sign'], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(workspace), text=True).strip()
    return head

# Node: relpath
# Node: check_output
def git_reset_to(workspace: Path, commit_id: str) -> None:
    result = subprocess.run(['git', 'reset', '--hard', commit_id], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'Failed to reset to commit {commit_id}: {result.stderr}')
    else:
        print('git reset result:', result.stdout)

def git_restore_path(workspace: Path, commit_id: str, rel_path: str) -> None:
    """Restore a specific path from a given commit into working tree.
    Prefer `git restore`, fallback to `git checkout` for older Git.
    """
    proc = subprocess.run(['git', 'restore', '--source', commit_id, '--', rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        subprocess.run(['git', 'checkout', commit_id, '--', rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def git_clean_path(workspace: Path, rel_path: str) -> None:
    """Remove untracked files/dirs only within a specific path.
    Keeps ignored files (does not use -x) to avoid deleting cache/artifacts elsewhere.
    """
    subprocess.run(['git', 'clean', '-fd', '--', rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def copy_repo_to_results(workspace: Path, repo_root: Path) -> Path:
    """Copy the entire repo subtree to <workspace>/results/<repo_root_basename> for later review."""
    results_dir = workspace / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    dest_dir = results_dir / repo_root.name
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(repo_root, dest_dir)
    return dest_dir

# Node: rmtree
# Node: copytree
def process_single_repo(args: argparse.Namespace, workspace: Path, repo_name: str) -> None:
    repo_root = workspace / args.repo_root / repo_name
    if not repo_root.exists():
        raise FileNotFoundError(f'Target directory not found: {repo_root}')
    readme_text = read_readme(repo_root)
    pom_text = read_pom(repo_root)
    service_proc: Optional[subprocess.Popen] = None
    env_name: Optional[str] = None
    backup_commit = git_backup_repo(workspace, repo_root, message=f'backup before metagpt for {repo_name}')
    tests_dir = repo_root / 'tests'
    if tests_dir.exists():
        shutil.rmtree(tests_dir)
    try:
        if args.agent.lower() == 'metagpt':
            if args.metagpt_config:
                os.environ.setdefault('METAGPT_CONFIG', str(Path(args.metagpt_config).resolve()))
            else:
                llm_model = args.llm_model.strip()
                llm_base_url = args.llm_base_url.strip()
                llm_api_key = args.llm_api_key.strip() or os.environ.get('OPENAI_API_KEY', '')
                if llm_model or llm_base_url or llm_api_key:
                    if not llm_model:
                        llm_model = 'gpt-4o-mini'
                    if not llm_base_url:
                        llm_base_url = 'https://api.openai.com/v1'
                    if not llm_api_key:
                        raise RuntimeError('OPENAI_API_KEY is not set and --llm_api_key not provided')
                    cfg_path = write_temp_metagpt_config(llm_model, llm_base_url, llm_api_key)
                    os.environ['METAGPT_CONFIG'] = str(cfg_path)
            metagpt_generate(repo_root, readme_text, pom_text, args.run_tests)
            print('metagpt_generate done')
            rel_repo = os.path.relpath(str(repo_root), str(workspace))
            tests_rel_path = os.path.join(rel_repo, 'tests')
            git_restore_path(workspace, backup_commit, tests_rel_path)
        elif args.agent.lower() == 'deepcode':
            if args.deepcode_openai_key and (not os.environ.get('OPENAI_API_KEY')):
                os.environ['OPENAI_API_KEY'] = args.deepcode_openai_key
            deepcode_generate(repo_root, readme_text, pom_text)
            start_cmd = 'python -m streamlit run app.py' if (repo_root / 'app.py').exists() else 'python -m http.server 8000'
        elif args.agent.lower() == 'qwen-agent':
            qwen_agent_generate(repo_root, readme_text, pom_text, args)
            if (repo_root / 'app.py').exists():
                start_cmd = 'python app.py'
            elif (repo_root / 'main.py').exists():
                start_cmd = 'python main.py'
            elif (repo_root / 'manage.py').exists():
                start_cmd = 'python manage.py runserver 0.0.0.0:8000'
            else:
                start_cmd = 'python -m http.server 8000'
        elif args.agent.lower() == 'ms-agent':
            raise NotImplementedError('USE PYTHONPATH=. openai_api_key=xxx openai_base_url=xxxx python ms_agent/cli/cli.py run --config projects/service --trust_remote_code true --repo /Volumes/T7/Real_Swe-bench/code/repo_readme_repeat to run ms-agent')
        else:
            raise NotImplementedError(f"Agent '{args.agent}' is not supported yet")
    finally:
        terminate_process(service_proc)
        if env_name:
            try:
                conda_exe = ensure_conda_available()
                subprocess.run([conda_exe, 'env', 'remove', '-y', '-n', env_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            except Exception:
                pass
        try:
            copy_repo_to_results(workspace, repo_root)
        except Exception:
            pass

# Node: read_readme
# Node: read_pom
# Node: git_backup_repo
# Node: write_temp_metagpt_config
# Node: metagpt_generate
# Node: git_restore_path
# Node: deepcode_generate
# Node: qwen_agent_generate
# Node: NotImplementedError
# Node: terminate_process
# Node: copy_repo_to_results
# Node: any
def kill_port(port: int):
    """Kill any process using the specified port."""
    try:
        result = subprocess.run(f'lsof -ti:{port}', shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except:
                    pass
    except:
        pass

def detect_repo_type(repo_path: str) -> Tuple[str, Optional[str]]:
    """
    Detect repository type and return (type, config_file_path).
    type is 'Java', 'Python', or 'Unknown'.
    """
    pom_path = find_file_recursive(repo_path, 'pom.xml')
    if pom_path:
        return ('Java', pom_path)
    req_path = find_file_recursive(repo_path, 'requirements.txt')
    if req_path:
        return ('Python', req_path)
    setup_path = find_file_recursive(repo_path, 'setup.py')
    if setup_path:
        return ('Python', setup_path)
    pyproject_path = find_file_recursive(repo_path, 'pyproject.toml')
    if pyproject_path:
        return ('Python', pyproject_path)
    return ('Unknown', None)

# Node: find_file_recursive
def test_java_repository(repo_name: str, repo_path: str, pom_path: str, port_base: int) -> bool:
    """Test Java repository deployment."""
    print(f'  [Java] Testing: {repo_name}')
    print(f'    [1/3] Installing dependencies (pom: {os.path.relpath(pom_path, repo_path)})...')
    pom_dir = os.path.dirname(pom_path)
    try:
        result = subprocess.run(['mvn', 'clean', 'install', '-DskipTests', '-q'], cwd=pom_dir, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f'    Maven build failed: {result.stderr[:200]}...')
            return (False, f'Maven build failed')
        print('    ✓ Dependencies installed')
    except subprocess.TimeoutExpired:
        return (False, 'Maven build timeout (>300s)')
    except Exception as e:
        return (False, f'Maven build error: {str(e)}')
    print(f'    [2/3] Starting server (Port range: {port_base}-{port_base + 10})...')
    for port in range(port_base, port_base + 10):
        kill_port(port)
    time.sleep(1)
    start_script = find_file_recursive(repo_path, 'start.sh', max_depth=5)
    if not start_script:
        return (False, 'start.sh not found (recursive)')
    start_dir = os.path.dirname(start_script)
    try:
        env = os.environ.copy()
        env['PORT'] = str(port_base)
        process = subprocess.Popen(['bash', 'start.sh'], cwd=start_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for i in range(20):
            time.sleep(1)
            poll = process.poll()
            if poll is not None:
                stdout, stderr = process.communicate()
                combined_output = stdout + stderr
                if any((pattern in combined_output for pattern in ['Started', 'Javalin started', 'Server started', 'Application started', 'Listening on', 'Tomcat started'])):
                    return (True, 'Server started successfully')
                if 'Address already in use' in combined_output or 'Port already in use' in combined_output:
                    return (True, 'Server deployable (port conflict)')
                return (False, f'Server exited with code {poll}')
        print('    ✓ Server running')
        try:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        except:
            pass
        return (True, 'Server started successfully')
    except Exception as e:
        return (False, f'Server start error: {str(e)}')
    finally:
        try:
            if 'process' in locals() and process.poll() is None:
                process.kill()
        except:
            pass
        for port in range(port_base, port_base + 10):
            kill_port(port)

# Node: kill_port
# Node: communicate
# Node: locals
def test_python_repository(repo_name: str, repo_path: str, req_path: str, port_base: int) -> bool:
    """Test Python repository deployment."""
    print(f'  [Python] Testing: {repo_name}')
    print(f'    [1/3] Installing dependencies (req: {os.path.relpath(req_path, repo_path)})...')
    req_filename = os.path.basename(req_path)
    req_dir = os.path.dirname(req_path)
    try:
        cmd = []
        if req_filename == 'requirements.txt':
            cmd = ['pip', 'install', '-q', '-r', req_filename]
        else:
            cmd = ['pip', 'install', '-q', '.']
        result = subprocess.run(cmd, cwd=req_dir, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return (False, 'Pip install failed')
        print('    ✓ Dependencies installed')
    except subprocess.TimeoutExpired:
        return (False, 'Pip install timeout (>120s)')
    except Exception as e:
        return (False, f'Pip install error: {str(e)}')
    print(f'    [2/3] Starting server (Port range: {port_base}-{port_base + 10})...')
    for port in range(port_base, port_base + 10):
        kill_port(port)
    time.sleep(1)
    start_script = find_file_recursive(repo_path, 'start.sh', max_depth=5)
    if not start_script:
        return (False, 'start.sh not found (recursive)')
    start_dir = os.path.dirname(start_script)
    try:
        env = os.environ.copy()
        env['PORT'] = str(port_base)
        process = subprocess.Popen(['bash', 'start.sh'], cwd=start_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for i in range(15):
            time.sleep(1)
            poll = process.poll()
            if poll is not None:
                stdout, stderr = process.communicate()
                combined_output = stdout + stderr
                if any((pattern in combined_output for pattern in ['Running on', 'Started', 'Uvicorn running', 'Application startup complete', 'Listening on', 'Accepting connections'])):
                    return (True, 'Server started successfully')
                if 'Address already in use' in combined_output or 'Port already in use' in combined_output:
                    return (True, 'Server deployable (port conflict)')
                return (False, f'Server exited with code {poll}')
        print('    ✓ Server running')
        try:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        except:
            pass
        return (True, 'Server started successfully')
    except Exception as e:
        return (False, f'Server start error: {str(e)}')
    finally:
        try:
            if 'process' in locals() and process.poll() is None:
                process.kill()
        except:
            pass
        for port in range(port_base, port_base + 10):
            kill_port(port)

# Node: basename
def ensure_conda_available() -> str:
    conda_exe = shutil.which('conda')
    if not conda_exe:
        raise RuntimeError('conda is required but was not found on PATH')
    return conda_exe

def create_pytest_env(env_name: str, requirements_file: Optional[Path]) -> None:
    conda_exe = ensure_conda_available()
    subprocess.run([conda_exe, 'create', '-y', '-n', env_name, 'python=3.10'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run([conda_exe, 'run', '-n', env_name, 'python', '-m', 'pip', 'install', '--upgrade', 'pip', 'pytest'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if requirements_file and requirements_file.exists():
        subprocess.run([conda_exe, 'run', '-n', env_name, 'python', '-m', 'pip', 'install', '-r', str(requirements_file)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def metagpt_generate(repo_root: Path, readme_text: str, requirements_text: str) -> None:
    import sys
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_meta_path = os.path.join(workspace_root, 'agent', 'MetaGPT')
    if agent_meta_path not in sys.path and os.path.isdir(agent_meta_path):
        sys.path.insert(0, agent_meta_path)
    from metagpt.software_company import generate_repo
    ensure_event_loop()
    idea = textwrap.dedent(f'\n        You are a senior software engineer tasked with implementing a complete software project.\n\n        Project Requirements:\n        README:\n        {readme_text}\n\n        requirements.txt (reference):\n        {requirements_text}\n\n        Your task:\n        1. Analyze the README and referenced requirements to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (requirements.txt is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use a common port (e.g., 8000) or the one specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port.\n        7. Write production-ready, well-documented code.\n\n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    generate_repo(idea=idea, project_name=repo_root.name, inc=False, project_path=str(repo_root), implement=True, run_tests=False, code_review=True, n_round=5, investment=3.0)

def deepcode_generate(repo_root: Path, readme_text: str, requirements_text: str) -> None:
    """Use DeepCode workflows to synthesize code based on README into repo_root.
    Strategy:
    - Create an implementation plan file from the README in repo_root.
    - Invoke DeepCode CodeImplementationWorkflow in pure code mode targeting repo_root.
    - Move generated files from generate_code/ up to repo_root.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_deep_path = os.path.join(workspace_root, 'agent', 'DeepCode')
    if agent_deep_path not in sys.path and os.path.isdir(agent_deep_path):
        sys.path.insert(0, agent_deep_path)
    from workflows.code_implementation_workflow import CodeImplementationWorkflow
    repo_root.mkdir(parents=True, exist_ok=True)
    plan_path = repo_root / 'initial_plan.txt'
    plan_content = textwrap.dedent(f'\n        You are a senior software engineer tasked with implementing a complete software project.\n\n        Project Requirements:\n        README:\n        {readme_text}\n\n        requirements.txt (reference):\n        {requirements_text}\n\n        Your task:\n        1. Analyze the README and referenced requirements to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (requirements.txt is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use a common port (e.g., 8000) or the one specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port.\n        7. Write production-ready, well-documented code.\n\n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    plan_path.write_text(plan_content, encoding='utf-8')
    secrets_path = os.path.join(agent_deep_path, 'mcp_agent.secrets.yaml')
    config_path = os.path.join(agent_deep_path, 'mcp_agent.config.yaml')
    if not os.path.isfile(config_path):
        print('[deepcode] WARNING: mcp_agent.config.yaml not found; DeepCode may use defaults')
    if not os.path.isfile(secrets_path):
        print('[deepcode] WARNING: mcp_agent.secrets.yaml not found; ensure LLM keys via env')
    if not os.environ.get('OPENAI_API_KEY'):
        print('[deepcode] WARNING: OPENAI_API_KEY not set; DeepCode may fail to call LLM')
    gen_dir = repo_root / 'generate_code'
    gen_dir.mkdir(parents=True, exist_ok=True)
    workflow = CodeImplementationWorkflow(config_path=secrets_path if os.path.isfile(secrets_path) else 'mcp_agent.secrets.yaml')
    cwd = os.getcwd()
    try:
        os.chdir(agent_deep_path)
        asyncio.run(workflow.run_workflow(plan_file_path=str(plan_path), target_directory=str(repo_root), pure_code_mode=True, enable_read_tools=False))
    finally:
        os.chdir(cwd)
    if gen_dir.exists() and gen_dir.is_dir():
        for root, dirs, files in os.walk(gen_dir):
            rel = os.path.relpath(root, str(gen_dir))
            dest_dir = repo_root / rel if rel != '.' else repo_root
            dest_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                src = Path(root) / f
                dst = dest_dir / f
                shutil.copy2(src, dst)

# Node: copy2
def qwen_agent_generate(repo_root: Path, readme_text: str, requirements_text: str, args) -> None:
    """Use Qwen-Agent to synthesize code based on README into repo_root.
    Strategy:
    - Import Qwen-Agent from agent/Qwen-Agent.
    - Create an Assistant agent with code_interpreter tool.
    - Send a comprehensive prompt to implement the entire project per README.
    - Files will be generated in the current working directory (repo_root).
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_qwen_path = os.path.join(workspace_root, 'agent', 'Qwen-Agent')
    if agent_qwen_path not in sys.path and os.path.isdir(agent_qwen_path):
        sys.path.insert(0, agent_qwen_path)
    try:
        from qwen_agent.agents import Assistant
        from qwen_agent.utils.output_beautify import typewriter_print
    except ImportError as e:
        print(f'[qwen-agent] Failed to import Qwen-Agent: {e}')
        print('[qwen-agent] Creating placeholder files...')
        repo_root.mkdir(parents=True, exist_ok=True)
        marker = repo_root / 'AGENT.txt'
        marker.write_text('Generated by Qwen-Agent adapter (import failed)\n', encoding='utf-8')
        return
    repo_root.mkdir(parents=True, exist_ok=True)
    llm_cfg = None
    if args.llm_api_key:
        llm_cfg = {'model': args.llm, 'model_server': args.llm_base_url, 'api_key': args.llm_api_key}
    else:
        print('[qwen-agent] No API key found (DASHSCOPE_API_KEY or OPENAI_API_KEY)')
        print('[qwen-agent] Creating placeholder files...')
        marker = repo_root / 'AGENT.txt'
        marker.write_text('Generated by Qwen-Agent adapter (no API key)\n', encoding='utf-8')
        return
    system_instruction = textwrap.dedent(f'\n        You are a senior software engineer tasked with implementing a complete software project.\n        \n        Project Requirements:\n        README:\n        {readme_text}\n        \n        requirements.txt (reference):\n        {requirements_text}\n        \n        Your task:\n        1. Analyze the README and referenced requirements to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (requirements.txt is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use a common port (e.g., 8000) or the one specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port.\n        7. Write production-ready, well-documented code.\n        \n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    tools = ['code_interpreter']
    bot = Assistant(llm=llm_cfg, system_message=system_instruction, function_list=tools)
    implementation_prompt = textwrap.dedent(f'\n        Please implement the complete software project based on the README and requirements.\n        \n        Current working directory: {repo_root}\n        \n        Steps to follow:\n        1. First, analyze the requirements and create a project structure plan\n        2. Create all necessary directories using os.makedirs()\n        3. Implement all source code files with proper imports and dependencies\n        4. Create configuration files including requirements.txt\n        5. Create a main entry point that can start the application\n        6. Test that the basic structure is correct\n        \n        Make sure to:\n        - Use proper file paths relative to current directory\n        - Include error handling and logging where appropriate\n        - Follow best practices for the technology stack\n        - Create a README.md with usage instructions\n        \n        Start implementing now!\n        ').strip()
    cwd = os.getcwd()
    try:
        os.chdir(str(repo_root))
        messages = [{'role': 'user', 'content': implementation_prompt}]
        response_text = ''
        print('[qwen-agent] Starting project implementation...')
        for response in bot.run(messages=messages):
            if isinstance(response, list) and response:
                for msg in response:
                    if msg.get('role') == 'assistant' and msg.get('content'):
                        content = msg['content']
                        response_text += content
                        print(content, end='', flush=True)
        print(f'\n[qwen-agent] Implementation completed in {repo_root}')
    except Exception as e:
        print(f'[qwen-agent] Error during implementation: {e}')
        marker = repo_root / 'AGENT.txt'
        marker.write_text(f'Generated by Qwen-Agent adapter (error: {e})\n', encoding='utf-8')
    finally:
        os.chdir(cwd)

def ms_agent_generate(repo_root: Path, readme_text: str, requirements_text: str, args) -> None:
    """Use MS-Agent to synthesize code based on README into repo_root.
    Strategy:
    - Import MS-Agent from agent/ms-agent.
    - Create an LLMAgent with code generation capabilities.
    - Send a comprehensive prompt to implement the entire project per README.
    - Files will be generated in the current working directory (repo_root).
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_ms_path = os.path.join(workspace_root, 'agent', 'ms-agent')
    if agent_ms_path not in sys.path and os.path.isdir(agent_ms_path):
        sys.path.insert(0, agent_ms_path)
    try:
        from ms_agent import LLMAgent
    except ImportError as e:
        print(f'[ms-agent] Failed to import MS-Agent: {e}')
        print('[ms-agent] Creating placeholder files...')
        repo_root.mkdir(parents=True, exist_ok=True)
        marker = repo_root / 'AGENT.txt'
        marker.write_text('Generated by MS-Agent adapter (import failed)\n', encoding='utf-8')
        return
    repo_root.mkdir(parents=True, exist_ok=True)
    implementation_prompt = textwrap.dedent(f'\n        You are a senior software engineer. Please implement a complete software project based on the following requirements.\n\n        Project Requirements:\n        README:\n        {readme_text}\n\n        requirements.txt (reference):\n        {requirements_text}\n\n        Your task:\n        1. Analyze the README and referenced requirements to understand the project requirements.\n        2. Design the complete project structure and architecture.\n        3. Implement ALL necessary files including:\n           - Main application files\n           - Configuration files\n           - Dependencies/requirements files (requirements.txt is required)\n           - Documentation files\n           - Any additional files needed for the project to run\n        4. Ensure the project can be started via a single shell command writen in a file named start.sh.\n        5. The generated start.sh MUST:\n            * Listen on 0.0.0.0\n            * Use a common port (e.g., 8000) or the one specified in the README\n            * Use ONLY the correct command for the detected framework\n        6. If a web service is expected, bind to 0.0.0.0 and use the port.\n        7. Write production-ready, well-documented code.\n\n        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.\n        ').strip()
    cwd = os.getcwd()
    try:
        os.chdir(str(repo_root))

        async def run_ms_agent():
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]]
            try:
                from omegaconf import OmegaConf
                config_dict = {'llm': {'service': 'openai', 'model': args.llm_model.strip()}, 'generation_config': {'temperature': 1, 'stream': True}, 'max_chat_round': 100, 'callbacks': []}
                if args.llm_api_key:
                    config_dict['llm']['openai_api_key'] = args.llm_api_key.strip()
                    api_key = args.llm_api_key
                    config_dict['llm']['openai_base_url'] = args.llm_base_url.strip()
                else:
                    raise RuntimeError('args.llm_api_key not provided')
                config = OmegaConf.create(config_dict)
                llm_agent = LLMAgent(config=config)
                print('[ms-agent] Starting project implementation...')
                result = await llm_agent.run(implementation_prompt)
                return result
            finally:
                sys.argv = original_argv
        result = asyncio.run(run_ms_agent())
        print(f'\n[ms-agent] Implementation completed in {repo_root}')
        if result:
            print(f'[ms-agent] Result summary: {str(result)[:200]}...')
    except Exception as e:
        print(f'[ms-agent] Error during implementation: {e}')
        import traceback
        traceback.print_exc()
        marker = repo_root / 'AGENT.txt'
        marker.write_text(f'Generated by MS-Agent adapter (error: {e})\n', encoding='utf-8')
    finally:
        os.chdir(cwd)

def start_service(command: str, repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')
    proc = subprocess.Popen(command, cwd=str(repo_root), env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc

def run_pytest_in_env(env_name: str, repo_root: Path) -> Tuple[int, str]:
    conda_exe = ensure_conda_available()
    cmd = [conda_exe, 'run', '-n', env_name, 'pytest', '-q']
    proc = subprocess.run(cmd, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return (proc.returncode, proc.stdout)

def terminate_process(proc: Optional[subprocess.Popen]) -> None:
    if not proc:
        return
    if proc.poll() is None:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except Exception:
                pass

def write_temp_metagpt_config(model: str, base_url: str, api_key: str) -> Path:
    """Write a minimal MetaGPT config2.yaml to a temp file and return its path."""
    content = textwrap.dedent(f'\n        llm:\n          api_type: "openai"\n          model: "{model}"\n          base_url: "{base_url}"\n          api_key: "{api_key}"\n        ').strip() + '\n'
    tmpdir = Path(tempfile.mkdtemp(prefix='metagpt_cfg_'))
    cfg = tmpdir / 'config2.yaml'
    cfg.write_text(content, encoding='utf-8')
    return cfg

def git_backup_repo(workspace: Path, repo_root: Path, message: str) -> str:
    """Create a git commit backing up the repo_root subtree. Return commit id (HEAD).
    If there is nothing to commit, still return current HEAD.
    """
    rel = os.path.relpath(str(repo_root), str(workspace))
    subprocess.run(['git', 'add', '-A', '--', rel], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    commit = subprocess.run(['git', 'commit', '-m', message, '--no-gpg-sign'], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(workspace), text=True).strip()
    return head

def git_reset_to(workspace: Path, commit_id: str) -> None:
    result = subprocess.run(['git', 'reset', '--hard', commit_id], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'Failed to reset to commit {commit_id}: {result.stderr}')
    else:
        print('git reset result:', result.stdout)

def git_restore_path(workspace: Path, commit_id: str, rel_path: str) -> None:
    """Restore a specific path from a given commit into working tree.
    Prefer `git restore`, fallback to `git checkout` for older Git.
    """
    proc = subprocess.run(['git', 'restore', '--source', commit_id, '--', rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        subprocess.run(['git', 'checkout', commit_id, '--', rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def git_clean_path(workspace: Path, rel_path: str) -> None:
    """Remove untracked files/dirs only within a specific path.
    Keeps ignored files (does not use -x) to avoid deleting cache/artifacts elsewhere.
    """
    subprocess.run(['git', 'clean', '-fd', '--', rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def copy_repo_to_results(workspace: Path, repo_root: Path) -> Path:
    """Copy the entire repo subtree to <workspace>/results/<repo_root_basename> for later review."""
    results_dir = workspace / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    dest_dir = results_dir / repo_root.name
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(repo_root, dest_dir)
    return dest_dir

def process_single_repo(args: argparse.Namespace, workspace: Path, repo_name: str) -> None:
    repo_root = workspace / args.repo_root / repo_name
    if not repo_root.exists():
        raise FileNotFoundError(f'Target directory not found: {repo_root}')
    readme_text = read_readme(repo_root)
    requirements_text = read_requirements(repo_root)
    service_proc: Optional[subprocess.Popen] = None
    env_name: Optional[str] = None
    backup_commit = git_backup_repo(workspace, repo_root, message=f'backup before metagpt for {repo_name}')
    tests_dir = repo_root / 'tests'
    if tests_dir.exists():
        shutil.rmtree(tests_dir)
    try:
        if args.agent.lower() == 'metagpt':
            if args.metagpt_config:
                os.environ.setdefault('METAGPT_CONFIG', str(Path(args.metagpt_config).resolve()))
            else:
                llm_model = args.llm_model.strip()
                llm_base_url = args.llm_base_url.strip()
                llm_api_key = args.llm_api_key.strip() or os.environ.get('OPENAI_API_KEY', '')
                if llm_model or llm_base_url or llm_api_key:
                    if not llm_model:
                        llm_model = 'gpt-4o-mini'
                    if not llm_base_url:
                        llm_base_url = 'https://api.openai.com/v1'
                    if not llm_api_key:
                        raise RuntimeError('OPENAI_API_KEY is not set and --llm_api_key not provided')
                    cfg_path = write_temp_metagpt_config(llm_model, llm_base_url, llm_api_key)
                    os.environ['METAGPT_CONFIG'] = str(cfg_path)
            metagpt_generate(repo_root, readme_text, requirements_text)
            print('metagpt_generate done')
            rel_repo = os.path.relpath(str(repo_root), str(workspace))
            tests_rel_path = os.path.join(rel_repo, 'tests')
            git_restore_path(workspace, backup_commit, tests_rel_path)
        elif args.agent.lower() == 'deepcode':
            if args.deepcode_openai_key and (not os.environ.get('OPENAI_API_KEY')):
                os.environ['OPENAI_API_KEY'] = args.deepcode_openai_key
            deepcode_generate(repo_root, readme_text, requirements_text)
            start_cmd = 'python -m streamlit run app.py' if (repo_root / 'app.py').exists() else 'python -m http.server 8000'
        elif args.agent.lower() == 'qwen-agent':
            qwen_agent_generate(repo_root, readme_text, requirements_text, args)
            if (repo_root / 'app.py').exists():
                start_cmd = 'python app.py'
            elif (repo_root / 'main.py').exists():
                start_cmd = 'python main.py'
            elif (repo_root / 'manage.py').exists():
                start_cmd = 'python manage.py runserver 0.0.0.0:8000'
            else:
                start_cmd = 'python -m http.server 8000'
        elif args.agent.lower() == 'ms-agent':
            raise NotImplementedError('USE PYTHONPATH=. openai_api_key=xxx openai_base_url=xxxx python ms_agent/cli/cli.py run --config projects/service --trust_remote_code true --repo /Volumes/T7/Real_Swe-bench/code/repo_readme_repeat to run ms-agent')
        else:
            raise NotImplementedError(f"Agent '{args.agent}' is not supported yet")
    finally:
        terminate_process(service_proc)
        if env_name:
            try:
                conda_exe = ensure_conda_available()
                subprocess.run([conda_exe, 'env', 'remove', '-y', '-n', env_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            except Exception:
                pass
        try:
            copy_repo_to_results(workspace, repo_root)
        except Exception:
            pass

# Node: read_requirements
def start_service(script_path):
    """Start the service using the start.sh script."""
    print(f'Starting service with {script_path}...')
    process = subprocess.Popen(['bash', script_path], cwd=os.path.dirname(script_path), preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def kill_process_group(process):
    """Kill the process group of the given process."""
    if process:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except Exception as e:
            print(f'Error killing process group: {e}')
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

# Node: killpg
# Node: getpgid
def run_pytest(test_dir, answer_dir):
    """Run pytest and return the output."""
    print(f'Running tests in {test_dir}...')
    cmd = [sys.executable, '-m', 'pytest', test_dir, f'--cov={answer_dir}', '--cov-report=term-missing']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return (result.stdout + result.stderr, result.returncode)
    except subprocess.TimeoutExpired:
        return ('TIMEOUT', -1)

def run_java_tests(test_dir, answer_dir):
    """Run tests using run_tests.sh or mvnw."""
    run_script = find_file_recursive(answer_dir, 'run_tests.sh')
    cmd = []
    cwd = answer_dir
    if run_script:
        print(f'Found test script: {run_script}')
        cmd = ['bash', run_script]
        cwd = os.path.dirname(run_script)
    else:
        mvnw = find_file_recursive(answer_dir, 'mvnw')
        if mvnw:
            print(f'Found mvnw: {mvnw}')
            cmd = [mvnw, 'clean', 'test']
            cwd = os.path.dirname(mvnw)
        else:
            print("No run_tests.sh or mvnw found. Trying 'mvn test'...")
            cmd = ['mvn', 'clean', 'test']
    print(f'Running tests with command: {' '.join(cmd)} in {cwd}')
    try:
        command = cmd[0]
        args = cmd[1:]
        child = pexpect.spawn(command, args, cwd=cwd, encoding='utf-8', timeout=600)
        output = []
        while True:
            index = child.expect([pexpect.EOF, pexpect.TIMEOUT, 'Press \\[r\\] to resume'], timeout=600)
            if child.before:
                output.append(child.before)
            if index == 0:
                break
            elif index == 1:
                output.append('\nTIMEOUT')
                break
            elif index == 2:
                if isinstance(child.after, str):
                    output.append(child.after)
                print("Detected interactive prompt. Sending 'r'...")
                child.sendline('r')
        full_output = ''.join(output)
        child.close()
        return (full_output, child.exitstatus)
    except Exception as e:
        return (str(e), -1)

# Node: spawn
# Node: expect
# Node: sendline
def start_service(answer_dir):
    """Find and run start.sh."""
    start_script = find_file_recursive(answer_dir, 'start.sh')
    if start_script:
        print(f'Starting service with {start_script}...')
        try:
            process = subprocess.Popen(['bash', start_script], cwd=os.path.dirname(start_script), preexec_fn=os.setsid, stdin=subprocess.DEVNULL)
            return process
        except Exception as e:
            print(f'Failed to start service: {e}')
    return None

def kill_process_group(process):
    if process:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

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

# Node: log_test
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

# Node: all
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

def run_user_session(session_id):
    try:
        session_results = simulate_user_session(session_id)
        results.append(session_results)
    except Exception as e:
        errors.append(f'Session {session_id} error: {str(e)}')

# Node: simulate_user_session
class TestHealthEndpoint:
    BASE_URL = 'http://localhost:8000/api/v1'

    def test_health_endpoint_available(self):
        try:
            response = requests.get(f'{self.BASE_URL}/health', timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'status' in data
            assert 'timestamp' in data
            assert 'version' in data
            assert data['status'] in ['healthy', 'unhealthy']
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except requests.exceptions.ConnectionError:
            pytest.fail('Unable to connect to the service, please ensure the service is started')

    def test_health_response_format(self):
        response = requests.get(f'{self.BASE_URL}/health')
        data = response.json()
        required_fields = ['status', 'timestamp', 'version']
        for field in required_fields:
            assert field in data, f'Response is missing required field: {field}'
        assert isinstance(data['status'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['version'], str)

    def test_health_endpoint_performance(self):
        start_time = time.time()
        response = requests.get(f'{self.BASE_URL}/health')
        end_time = time.time()
        response_time = end_time - start_time
        assert response_time < 1.0, f'Health check response time is too long: {response_time:.2f} seconds'
        assert response.status_code == 200

    def test_health_endpoint_concurrent_requests(self):
        import threading
        results = []
        errors = []

        def make_request():
            try:
                response = requests.get(f'{self.BASE_URL}/health', timeout=5)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors occurred during concurrent requests: {errors}'
        assert len(results) == 10
        assert all((status == 200 for status in results))

    def test_health_endpoint_headers(self):
        response = requests.get(f'{self.BASE_URL}/health')
        assert response.headers['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response.headers or '*' in response.headers.get('Access-Control-Allow-Origin', '')

    @pytest.mark.parametrize('invalid_method', ['POST', 'PUT', 'DELETE'])
    def test_health_endpoint_invalid_methods(self, invalid_method):
        response = requests.request(invalid_method, f'{self.BASE_URL}/health')
        assert response.status_code in [200, 405]

    def test_health_endpoint_with_query_params(self):
        response = requests.get(f'{self.BASE_URL}/health?param=test&debug=1')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data

def make_request():
    try:
        response = requests.get(f'{self.BASE_URL}/health', timeout=5)
        results.append(response.status_code)
    except Exception as e:
        errors.append(str(e))

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    BASE_URL = 'http://localhost:8080/api/v1'

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f'{self.BASE_URL}/tasks')
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    requests.delete(f'{self.BASE_URL}/tasks/{task['id']}')
        except requests.exceptions.ConnectionError:
            pytest.skip('API server not running')

    def test_task_title_boundary_values(self):
        """Test task title at boundary values"""
        max_title = 'x' * 200
        task_data = {'title': max_title, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == max_title
        too_long_title = 'x' * 201
        task_data = {'title': too_long_title, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_task_description_boundary_values(self):
        """Test task description at boundary values"""
        max_description = 'x' * 1000
        task_data = {'title': 'Test Task', 'description': max_description, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['description'] == max_description
        too_long_description = 'x' * 1001
        task_data = {'title': 'Test Task', 'description': too_long_description, 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422

    def test_unicode_characters_in_task(self):
        """Test handling of Unicode characters in task data"""
        unicode_task = {'title': 'Test Mission 🚀', 'description': 'This is a task description containing Unicode characters: Chinese, emoji, special symbols @#$%', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=unicode_task, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == unicode_task['title']
        assert data['description'] == unicode_task['description']

    def test_special_characters_in_task(self):
        """Test handling of special characters in task data"""
        special_chars_task = {'title': 'Task with Special Chars: @#$%^&*()_+-=[]{}|;\':",./<>?', 'description': 'Description with newlines\nand tabs\tand quotes"\'', 'priority': 'medium'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=special_chars_task, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == special_chars_task['title']
        assert data['description'] == special_chars_task['description']

    def test_date_formats(self):
        """Test various date formats for due_date"""
        date_formats = ['2024-12-31T23:59:59Z', '2024-12-31T23:59:59.000Z', '2024-12-31T23:59:59+00:00', '2024-12-31T23:59:59-05:00', '2024-12-31']
        for date_format in date_formats:
            task_data = {'title': f'Task with date {date_format}', 'priority': 'high', 'due_date': date_format}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_invalid_date_formats(self):
        """Test invalid date formats"""
        invalid_dates = ['not-a-date', '2024-13-01', '2024-02-30', '2024/12/31', '31-12-2024', '']
        for invalid_date in invalid_dates:
            task_data = {'title': 'Task with invalid date', 'priority': 'high', 'due_date': invalid_date}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422

    def test_empty_strings(self):
        """Test handling of empty strings"""
        task_data = {'title': '', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        task_data = {'title': 'Valid Task', 'description': '', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201

    def test_whitespace_only_strings(self):
        """Test handling of whitespace-only strings"""
        task_data = {'title': '   ', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        task_data = {'title': 'Valid Task', 'description': '   ', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_null_values(self):
        """Test handling of null values"""
        task_data = {'title': 'Valid Task', 'description': None, 'priority': 'high', 'due_date': None}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]

    def test_extra_fields(self):
        """Test handling of extra fields in request"""
        task_data = {'title': 'Valid Task', 'priority': 'high', 'extra_field': 'should be ignored', 'another_field': 123}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'extra_field' not in data
        assert 'another_field' not in data

    def test_case_sensitivity(self):
        """Test case sensitivity of enum values"""
        task_data = {'title': 'Test Task', 'priority': 'HIGH'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            task_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_large_numbers(self):
        """Test handling of large numbers in pagination"""
        response = requests.get(f'{self.BASE_URL}/tasks?page=999999')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/tasks?limit=999999')
        assert response.status_code in [200, 422]

    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        response = requests.get(f'{self.BASE_URL}/tasks?page=-1')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/tasks?limit=-1')
        assert response.status_code in [200, 422]

    def test_zero_values(self):
        """Test handling of zero values"""
        response = requests.get(f'{self.BASE_URL}/tasks?page=0')
        assert response.status_code in [200, 422]
        response = requests.get(f'{self.BASE_URL}/tasks?limit=0')
        assert response.status_code in [200, 422]

    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts"""
        malicious_titles = ["'; DROP TABLE tasks; --", "1' OR '1'='1", "admin'--", '1; DELETE FROM tasks; --']
        for malicious_title in malicious_titles:
            task_data = {'title': malicious_title, 'priority': 'high'}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_xss_attempts(self):
        """Test protection against XSS attempts"""
        xss_payloads = ["<script>alert('xss')</script>", "javascript:alert('xss')", "<img src=x onerror=alert('xss')>", "';alert('xss');//"]
        for payload in xss_payloads:
            task_data = {'title': payload, 'priority': 'high'}
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [201, 422]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        results = []
        errors = []

        def create_task(thread_id):
            try:
                task_data = {'title': f'Concurrent Task {thread_id}', 'priority': 'medium'}
                response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_task, args=(i,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors in concurrent requests: {errors}'
        assert len(results) == 5
        for thread_id, status_code in results:
            assert status_code == 201
        response = requests.get(f'{self.BASE_URL}/tasks')
        if response.status_code == 200:
            tasks = response.json().get('tasks', [])
            for task in tasks:
                if task['title'].startswith('Concurrent Task'):
                    requests.delete(f'{self.BASE_URL}/tasks/{task['id']}')

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = ['{"title": "Test", "priority": "high"', '{"title": "Test", "priority": "high",}', '{"title": "Test", "priority": high}', '{"title": "Test", "priority": "high" "extra": "value"}', '{"title": "Test", "priority": "high", "status": }']
        for malformed_json in malformed_jsons:
            response = requests.post(f'{self.BASE_URL}/tasks', data=malformed_json, headers={'Content-Type': 'application/json'})
            assert response.status_code == 400

    def test_content_type_variations(self):
        """Test handling of different content types"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        content_types = ['application/json', 'application/json; charset=utf-8', 'application/json;charset=utf-8', 'text/json', 'text/plain']
        for content_type in content_types:
            response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': content_type})
            assert response.status_code in [201, 400, 415]
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_missing_headers(self):
        """Test handling of missing headers"""
        task_data = {'title': 'Test Task', 'priority': 'high'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data)
        assert response.status_code in [201, 400, 415]
        if response.status_code == 201:
            task_id = response.json()['id']
            requests.delete(f'{self.BASE_URL}/tasks/{task_id}')

    def test_very_long_url(self):
        """Test handling of very long URLs"""
        long_params = '&'.join([f'param{i}=value{i}' for i in range(100)])
        response = requests.get(f'{self.BASE_URL}/tasks?{long_params}')
        assert response.status_code in [200, 414, 400]

def create_task(thread_id):
    try:
        task_data = {'title': f'Concurrent Task {thread_id}', 'priority': 'medium'}
        response = requests.post(f'{self.BASE_URL}/tasks', json=task_data, headers={'Content-Type': 'application/json'})
        results.append((thread_id, response.status_code))
    except Exception as e:
        errors.append((thread_id, str(e)))

class TestAuthAPI:
    """Test suite for Authentication API endpoints"""
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

    def test_login_success(self):
        """Test successful user login"""
        user_data = {'username': 'test_login_user', 'email': 'login@example.com', 'password': 'TestPass123!', 'full_name': 'Login Test User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'token_type' in data
        assert 'expires_in' in data
        assert 'user' in data
        assert data['token_type'] == 'Bearer'
        assert data['user']['username'] == user_data['username']
        assert data['user']['email'] == user_data['email']
        assert data['user']['role'] == user_data['role']
        assert 'password' not in data['user']

    def test_login_invalid_username(self):
        """Test login with invalid username"""
        login_data = {'username': 'nonexistent_user', 'password': 'SomePassword123!'}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'authentication_failed'

    def test_login_invalid_password(self):
        """Test login with invalid password"""
        user_data = {'username': 'test_invalid_password', 'email': 'invalid_password@example.com', 'password': 'CorrectPass123!', 'full_name': 'Invalid Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        login_data = {'username': user_data['username'], 'password': 'WrongPassword123!'}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'authentication_failed'

    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        login_data = {'username': 'test_user'}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        login_data = {'username': '', 'password': ''}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_login_inactive_user(self):
        """Test login with inactive user account"""
        user_data = {'username': 'test_inactive_user', 'email': 'inactive@example.com', 'password': 'TestPass123!', 'full_name': 'Inactive User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'inactive'}, headers={'Content-Type': 'application/json'})
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 403
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'account_inactive'

    def test_login_suspended_user(self):
        """Test login with suspended user account"""
        user_data = {'username': 'test_suspended_user', 'email': 'suspended@example.com', 'password': 'TestPass123!', 'full_name': 'Suspended User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        requests.put(f'{self.BASE_URL}/users/{user_id}', json={'status': 'suspended'}, headers={'Content-Type': 'application/json'})
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 403
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'account_suspended'

    def test_reset_password_success(self):
        """Test successful password reset"""
        user_data = {'username': 'test_reset_password', 'email': 'reset@example.com', 'password': 'OldPassword123!', 'full_name': 'Reset Password User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        reset_data = {'new_password': 'NewPassword123!'}
        response = requests.post(f'{self.BASE_URL}/users/{user_id}/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        login_data = {'username': user_data['username'], 'password': reset_data['new_password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200

    def test_reset_password_weak_password(self):
        """Test password reset with weak password"""
        user_data = {'username': 'test_weak_reset', 'email': 'weak_reset@example.com', 'password': 'TestPass123!', 'full_name': 'Weak Reset User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        reset_data = {'new_password': '123'}
        response = requests.post(f'{self.BASE_URL}/users/{user_id}/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_reset_password_nonexistent_user(self):
        """Test password reset for non-existent user"""
        reset_data = {'new_password': 'NewPassword123!'}
        response = requests.post(f'{self.BASE_URL}/users/99999/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'

    def test_reset_password_missing_new_password(self):
        """Test password reset with missing new password"""
        user_data = {'username': 'test_missing_reset', 'email': 'missing_reset@example.com', 'password': 'TestPass123!', 'full_name': 'Missing Reset User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        user_id = response.json()['id']
        reset_data = {}
        response = requests.post(f'{self.BASE_URL}/users/{user_id}/reset-password', json=reset_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_token_expiration(self):
        """Test token expiration behavior"""
        user_data = {'username': 'test_token_expiration', 'email': 'token@example.com', 'password': 'TestPass123!', 'full_name': 'Token Expiration User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        assert expires_in > 0
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{self.BASE_URL}/users/{response.json()['user']['id']}', headers=headers)

    def test_login_case_sensitivity(self):
        """Test login case sensitivity"""
        user_data = {'username': 'TestUserCase', 'email': 'case@example.com', 'password': 'TestPass123!', 'full_name': 'Case Test User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        test_cases = [('testusercase', user_data['password']), ('TESTUSERCASE', user_data['password']), ('testusercase', 'testpass123!')]
        for username, password in test_cases:
            login_data = {'username': username, 'password': password}
            response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
            assert response.status_code in [200, 401]

    def test_concurrent_login_attempts(self):
        """Test handling of concurrent login attempts"""
        user_data = {'username': 'test_concurrent_login', 'email': 'concurrent@example.com', 'password': 'TestPass123!', 'full_name': 'Concurrent Login User', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        import threading
        results = []
        errors = []

        def attempt_login(thread_id):
            try:
                login_data = {'username': user_data['username'], 'password': user_data['password']}
                response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        threads = []
        for i in range(5):
            thread = threading.Thread(target=attempt_login, args=(i,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors in concurrent login attempts: {errors}'
        assert len(results) == 5
        for thread_id, status_code in results:
            assert status_code == 200

    def test_malformed_login_request(self):
        """Test handling of malformed login requests"""
        malformed_requests = ['{"username": "test", "password": "pass"', '{"username": "test", "password": "pass",}', '{"username": "test", "password": pass}', '{"username": "test" "password": "pass"}']
        for malformed_request in malformed_requests:
            response = requests.post(f'{self.BASE_URL}/auth/login', data=malformed_request, headers={'Content-Type': 'application/json'})
            assert response.status_code == 400

def attempt_login(thread_id):
    try:
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = requests.post(f'{self.BASE_URL}/auth/login', json=login_data, headers={'Content-Type': 'application/json'})
        results.append((thread_id, response.status_code))
    except Exception as e:
        errors.append((thread_id, str(e)))

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

def create_user(thread_id):
    try:
        user_data = {'username': f'test_concurrent_{thread_id}', 'email': f'concurrent{thread_id}@example.com', 'password': 'TestPass123!', 'full_name': f'Concurrent User {thread_id}', 'role': 'user'}
        response = requests.post(f'{self.BASE_URL}/users', json=user_data, headers={'Content-Type': 'application/json'})
        results.append((thread_id, response.status_code))
    except Exception as e:
        errors.append((thread_id, str(e)))

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f'\n{'=' * 60}')
    print(f'Running: {description}')
    print(f'Command: {' '.join(cmd)}')
    print(f'{'=' * 60}')
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f'✅ {description} completed successfully')
        return True
    except subprocess.CalledProcessError as e:
        print(f'❌ {description} failed with exit code {e.returncode}')
        return False
    except FileNotFoundError:
        print(f'❌ Command not found: {cmd[0]}')
        return False

@pytest.fixture
def sample_player_data():
    """Sample player data for testing."""
    return {'player_id': str(uuid.uuid4()), 'player_name': 'TestPlayer'}

# Node: uuid4
@pytest.fixture
def sample_score_data():
    """Sample score submission data."""
    return {'player_id': str(uuid.uuid4()), 'player_name': 'ScorePlayer', 'score': 1500, 'game_type': 'battle'}

@pytest.fixture
def sample_game_state():
    """Sample game state data."""
    return {'room_id': str(uuid.uuid4()), 'player_id': str(uuid.uuid4()), 'game_state': {'board': [[0, 1, 0], [1, 0, 1], [0, 1, 0]], 'turn': 1, 'moves': 5}, 'action': 'move', 'timestamp': '2024-01-01T12:00:00Z'}

@pytest.fixture
def multiple_players():
    """Create multiple player data for testing."""
    return [{'player_id': str(uuid.uuid4()), 'player_name': f'Player{i}'} for i in range(1, 6)]

@pytest.fixture
def sample_leaderboard_data():
    """Sample leaderboard entries for testing."""
    return [{'player_id': str(uuid.uuid4()), 'player_name': 'TopPlayer1', 'score': 2000, 'game_type': 'battle'}, {'player_id': str(uuid.uuid4()), 'player_name': 'TopPlayer2', 'score': 1800, 'game_type': 'battle'}, {'player_id': str(uuid.uuid4()), 'player_name': 'CoopPlayer1', 'score': 1500, 'game_type': 'coop'}]

