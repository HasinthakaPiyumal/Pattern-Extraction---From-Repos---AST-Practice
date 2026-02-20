# Cluster 0

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
# Node: group
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
# Node: join
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

# Node: run_ms_agent
# Node: print_exc
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

# Node: create
# Node: LLMAgent
async def metagpt_start_command(repo_root: Path) -> str:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_meta_path = os.path.join(workspace_root, 'agent', 'MetaGPT')
    if agent_meta_path not in sys.path and os.path.isdir(agent_meta_path):
        sys.path.insert(0, agent_meta_path)
    from metagpt.roles.di.data_interpreter import DataInterpreter
    prompt = textwrap.dedent('\n        Analyze the project in {repo_root} and output a single shell command to start the app.\n        - Only output the command prefixed with START_COMMAND: and nothing else.\n        - Avoid backgrounding with &; emit the foreground command. Example format:\n          START_COMMAND: FLASK_APP=web_app flask run --host=0.0.0.0 --port=8000\n        ').strip()
    di = DataInterpreter()
    cwd = os.getcwd()
    result = None
    try:
        os.chdir(str(repo_root))
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                result = await di.run(prompt)
                break
            except Exception as e:
                err_text = str(e)
                if 'openai.InternalServerError' in err_text or '501page' in err_text:
                    try:
                        await asyncio.sleep(min(2 * attempt, 10))
                    except Exception:
                        pass
                    continue
                result = None
                break
        if result is None:
            simple_prompt = 'START_COMMAND:'
            try:
                result = await di.run(simple_prompt)
            except Exception:
                result = None
    finally:
        os.chdir(cwd)
    if result is None:
        result = ''
    if not isinstance(result, str):
        try:
            result = json.dumps(result)
        except Exception:
            result = str(result)
    m = re.search('START_COMMAND:\\s*(.+)', result)
    if not m:
        if (repo_root / 'app.py').exists():
            return 'python app.py'
        if (repo_root / 'manage.py').exists():
            return 'python manage.py runserver 0.0.0.0:8000'
        return 'python -m http.server 8000'
    return m.group(1).strip()

# Node: DataInterpreter
# Node: min
def run_pytest_in_env(env_name: str, repo_root: Path) -> Tuple[int, str]:
    conda_exe = ensure_conda_available()
    cmd = [conda_exe, 'run', '-n', env_name, 'pytest', '-q']
    proc = subprocess.run(cmd, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return (proc.returncode, proc.stdout)

def write_temp_metagpt_config(model: str, base_url: str, api_key: str) -> Path:
    """Write a minimal MetaGPT config2.yaml to a temp file and return its path."""
    content = textwrap.dedent(f'\n        llm:\n          api_type: "openai"\n          model: "{model}"\n          base_url: "{base_url}"\n          api_key: "{api_key}"\n        ').strip() + '\n'
    tmpdir = Path(tempfile.mkdtemp(prefix='metagpt_cfg_'))
    cfg = tmpdir / 'config2.yaml'
    cfg.write_text(content, encoding='utf-8')
    return cfg

# Node: Path
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
# Node: resolve
# Node: write_temp_metagpt_config
# Node: metagpt_generate
# Node: git_restore_path
# Node: deepcode_generate
# Node: qwen_agent_generate
# Node: NotImplementedError
# Node: terminate_process
# Node: copy_repo_to_results
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
def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """Extract API endpoints and features from README.md"""
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    endpoints = []
    pattern1 = re.compile('(GET|POST|PUT|DELETE|PATCH)\\s+(/[^\\s\\-]+)\\s*[-:]?\\s*(.+?)(?:\\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    table_pattern = re.compile('\\|\\s*(GET|POST|PUT|DELETE|PATCH)\\s*\\|\\s*([^\\|]+?)\\s*\\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({'method': match.group(1).upper(), 'path': path, 'description': ''})
    code_blocks = re.findall('```[\\w]*\\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f'{ep['method']}:{ep['path']}'
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    return unique_endpoints

# Node: compile
# Node: finditer
# Node: upper
# Node: findall
# Node: add
# Node: extend
def calculate_ac_for_all_repos(base_path: str) -> Dict:
    """Calculate API Coverage for all repositories in repos_IDE"""
    repo_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and (not d.startswith('.'))]
    results_by_config = defaultdict(lambda: {'repos': [], 'total_apis': 0, 'implemented_apis': 0, 'coverage': 0.0})
    all_results = {}
    for repo_dir in sorted(repo_dirs):
        config_path = os.path.join(base_path, repo_dir)
        config_info = parse_repo_dirname(repo_dir)
        if not config_info:
            print(f'Skipping invalid directory name: {repo_dir}')
            continue
        print(f'\n{'=' * 80}')
        print(f'Processing Configuration: {repo_dir}')
        print(f'  IDE: {config_info['ide']}')
        print(f'  Model: {config_info['model']}')
        print(f'  Language: {config_info['language']}')
        print(f'{'=' * 80}')
        repos = [r for r in os.listdir(config_path) if os.path.isdir(os.path.join(config_path, r)) and (not r.startswith('.'))]
        config_key = (config_info['ide'], config_info['model'], config_info['language'])
        for repo_name in sorted(repos):
            repo_path = os.path.join(config_path, repo_name)
            readme_path = os.path.join(repo_path, 'README.md')
            print(f'  Analyzing: {repo_name}')
            endpoints = extract_api_endpoints_from_readme(readme_path)
            if len(endpoints) == 0:
                print(f'    No API endpoints found')
                continue
            implemented = 0
            for endpoint in endpoints:
                if search_implementation(repo_path, endpoint):
                    implemented += 1
            coverage = implemented / len(endpoints) if len(endpoints) > 0 else 0.0
            print(f'    APIs: {implemented}/{len(endpoints)} = {coverage:.2%}')
            repo_result = {'repo_name': repo_name, 'total_apis': len(endpoints), 'implemented_apis': implemented, 'coverage': coverage}
            results_by_config[config_key]['repos'].append(repo_result)
            results_by_config[config_key]['total_apis'] += len(endpoints)
            results_by_config[config_key]['implemented_apis'] += implemented
        if results_by_config[config_key]['total_apis'] > 0:
            results_by_config[config_key]['coverage'] = results_by_config[config_key]['implemented_apis'] / results_by_config[config_key]['total_apis']
    return dict(results_by_config)

# Node: listdir
# Node: defaultdict
# Node: parse_repo_dirname
# Node: extract_api_endpoints_from_readme
# Node: search_implementation
# Node: dict
def generate_latex_table(results: Dict) -> str:
    """Generate LaTeX table similar to DSR table format"""
    lines = []
    lines.append('\\begin{table}[t]')
    lines.append('\\centering')
    lines.append('\\caption{API Coverage (AC) across IDE-model configurations. Results demonstrate API implementation completeness across 9 IDE-model-language combinations.}')
    lines.append('\\label{tab:ac_comprehensive}')
    lines.append('\\resizebox{\\columnwidth}{!}{%')
    lines.append('\\begin{tabular}{llccc}')
    lines.append('\\toprule')
    lines.append('\\textbf{IDE} & \\textbf{Model} & \\textbf{Language} & \\textbf{Implemented/Total} & \\textbf{AC} \\\\')
    lines.append('\\midrule')
    by_ide = defaultdict(list)
    for (ide, model, language), data in sorted(results.items()):
        by_ide[ide].append((model, language, data))
    total_apis = sum((data['total_apis'] for data in results.values()))
    total_implemented = sum((data['implemented_apis'] for data in results.values()))
    overall_ac = total_implemented / total_apis * 100 if total_apis > 0 else 0
    first_ide = True
    for ide, configs in sorted(by_ide.items()):
        if not first_ide:
            lines.append('\\midrule')
        first_ide = False
        configs = sorted(configs, key=lambda x: (x[0], x[1]))
        num_rows = len(configs)
        for idx, (model, language, data) in enumerate(configs):
            total = data['total_apis']
            implemented = data['implemented_apis']
            ac = data['coverage'] * 100
            model_display = model.replace('_', ' ').replace('-', ' ')
            if 'gpt' in model.lower() and '5' in model:
                if 'mini' in model.lower():
                    model_display = 'GPT-5 Mini'
                elif '5.1' in model or '51' in model:
                    model_display = 'GPT-5.1 Codex'
                else:
                    model_display = model_display.upper()
            elif 'claude' in model.lower():
                if '4' in model and '5' in model:
                    model_display = 'Claude 4.5 Sonnet'
                else:
                    model_display = 'Claude ' + model.replace('claude', '').strip('_- ')
            elif 'gemini' in model.lower():
                if 'low' in model.lower():
                    model_display = 'Gemini 3 Pro (Low)'
                elif '3' in model and 'pro' in model.lower():
                    model_display = 'Gemini 3 Pro'
                else:
                    model_display = 'Gemini ' + model.replace('gemini', '').strip('_- ').replace('3pro', '3 Pro')
            elif 'grok' in model.lower():
                model_display = 'Grok'
            else:
                model_display = ' '.join((word.capitalize() for word in model_display.split()))
            if idx == 0:
                lines.append(f'\\multirow{{{num_rows}}}{{*}}{{{ide}}} & {model_display} & {language} & {implemented}/{total} & {ac:.2f}\\% \\\\')
            else:
                lines.append(f'& {model_display} & {language} & {implemented}/{total} & {ac:.2f}\\% \\\\')
    lines.append('\\midrule')
    lines.append(f'\\multicolumn{{3}}{{l}}{{\\textbf{{Overall}}}} & \\textbf{{{total_implemented}/{total_apis}}} & \\textbf{{{overall_ac:.2f}\\%}} \\\\')
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('}')
    lines.append('\\end{table}')
    return '\n'.join(lines)

# Node: dump
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

async def metagpt_start_command(repo_root: Path) -> str:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_meta_path = os.path.join(workspace_root, 'agent', 'MetaGPT')
    if agent_meta_path not in sys.path and os.path.isdir(agent_meta_path):
        sys.path.insert(0, agent_meta_path)
    from metagpt.roles.di.data_interpreter import DataInterpreter
    prompt = textwrap.dedent('\n        Analyze the project in {repo_root} and output a single shell command to start the app.\n        - Only output the command prefixed with START_COMMAND: and nothing else.\n        - Avoid backgrounding with &; emit the foreground command. Example format:\n          START_COMMAND: FLASK_APP=web_app flask run --host=0.0.0.0 --port=8000\n        ').strip()
    di = DataInterpreter()
    cwd = os.getcwd()
    result = None
    try:
        os.chdir(str(repo_root))
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                result = await di.run(prompt)
                break
            except Exception as e:
                err_text = str(e)
                if 'openai.InternalServerError' in err_text or '501page' in err_text:
                    try:
                        await asyncio.sleep(min(2 * attempt, 10))
                    except Exception:
                        pass
                    continue
                result = None
                break
        if result is None:
            simple_prompt = 'START_COMMAND:'
            try:
                result = await di.run(simple_prompt)
            except Exception:
                result = None
    finally:
        os.chdir(cwd)
    if result is None:
        result = ''
    if not isinstance(result, str):
        try:
            result = json.dumps(result)
        except Exception:
            result = str(result)
    m = re.search('START_COMMAND:\\s*(.+)', result)
    if not m:
        if (repo_root / 'app.py').exists():
            return 'python app.py'
        if (repo_root / 'manage.py').exists():
            return 'python manage.py runserver 0.0.0.0:8000'
        return 'python -m http.server 8000'
    return m.group(1).strip()

def run_pytest_in_env(env_name: str, repo_root: Path) -> Tuple[int, str]:
    conda_exe = ensure_conda_available()
    cmd = [conda_exe, 'run', '-n', env_name, 'pytest', '-q']
    proc = subprocess.run(cmd, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return (proc.returncode, proc.stdout)

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
def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """
    Extract API endpoints and features from README.md
    
    Returns:
        List of dictionaries containing endpoint information:
        [{
            'method': 'GET/POST/PUT/DELETE',
            'path': '/api/...',
            'description': '...'
        }]
    """
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    endpoints = []
    pattern1 = re.compile('(GET|POST|PUT|DELETE|PATCH)\\s+(/[^\\s\\-]+)\\s*[-:]?\\s*(.+?)(?:\\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    table_pattern = re.compile('\\|\\s*(GET|POST|PUT|DELETE|PATCH)\\s*\\|\\s*([^\\|]+?)\\s*\\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({'method': match.group(1).upper(), 'path': path, 'description': ''})
    code_blocks = re.findall('```[\\w]*\\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    feature_pattern = re.compile('[-*]\\s+([A-Z][A-Za-z\\s]+(?:Check|Login|Register|Create|Update|Delete|Get|List|Manage|Service|API))', re.MULTILINE)
    features = feature_pattern.findall(content)
    for feature in features:
        feature_clean = feature.strip()
        if len(endpoints) == 0:
            endpoints.append({'method': 'FEATURE', 'path': feature_clean, 'description': feature_clean})
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f'{ep['method']}:{ep['path']}'
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    return unique_endpoints

def calculate_api_coverage(repo_base_path: str) -> Dict:
    """
    Calculate API coverage for all repositories in the base path
    
    Returns:
        Dictionary with repository names as keys and coverage data as values
    """
    results = {}
    repos = sorted([d for d in os.listdir(repo_base_path) if os.path.isdir(os.path.join(repo_base_path, d)) and (not d.startswith('.'))])
    for repo_name in repos:
        repo_path = os.path.join(repo_base_path, repo_name)
        readme_path = os.path.join(repo_path, 'README.md')
        print(f'\n{'=' * 80}')
        print(f'Processing: {repo_name}')
        print(f'{'=' * 80}')
        endpoints = extract_api_endpoints_from_readme(readme_path)
        print(f'Found {len(endpoints)} API endpoints/features in README')
        if len(endpoints) == 0:
            results[repo_name] = {'total_apis': 0, 'implemented_apis': 0, 'coverage': 0.0, 'endpoints': [], 'note': 'No API endpoints found in README'}
            continue
        implemented = []
        not_implemented = []
        for i, endpoint in enumerate(endpoints, 1):
            print(f'  [{i}/{len(endpoints)}] Checking: {endpoint['method']} {endpoint['path']}')
            is_implemented = search_implementation(repo_path, endpoint)
            if is_implemented:
                implemented.append(endpoint)
                print(f'    ✓ FOUND')
            else:
                not_implemented.append(endpoint)
                print(f'    ✗ NOT FOUND')
        coverage = len(implemented) / len(endpoints) if len(endpoints) > 0 else 0.0
        results[repo_name] = {'total_apis': len(endpoints), 'implemented_apis': len(implemented), 'coverage': coverage, 'endpoints': {'implemented': implemented, 'not_implemented': not_implemented}}
        print(f'\nCoverage: {len(implemented)}/{len(endpoints)} = {coverage:.2%}')
    return results

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

def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """Extract API endpoints and features from README.md"""
    if not os.path.exists(readme_path):
        return []
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    endpoints = []
    pattern1 = re.compile('(GET|POST|PUT|DELETE|PATCH)\\s+(/[^\\s\\-]+)\\s*[-:]?\\s*(.+?)(?:\\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    table_pattern = re.compile('\\|\\s*(GET|POST|PUT|DELETE|PATCH)\\s*\\|\\s*([^\\|]+?)\\s*\\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({'method': match.group(1).upper(), 'path': path, 'description': ''})
    code_blocks = re.findall('```[\\w]*\\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({'method': match.group(1).upper(), 'path': match.group(2).strip(), 'description': match.group(3).strip()})
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f'{ep['method']}:{ep['path']}'
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    return unique_endpoints

def calculate_ac_for_agents(base_path: str) -> Dict:
    """Calculate API Coverage for all agent repositories"""
    repo_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and (not d.startswith('.'))]
    results_by_config = defaultdict(lambda: {'repos': [], 'total_apis': 0, 'implemented_apis': 0, 'coverage': 0.0})
    for repo_dir in sorted(repo_dirs):
        config_path = os.path.join(base_path, repo_dir)
        config_info = parse_agent_dirname(repo_dir)
        if not config_info:
            print(f'Skipping invalid directory name: {repo_dir}')
            continue
        print(f'\n{'=' * 80}')
        print(f'Processing: {repo_dir}')
        print(f'  Agent: {config_info['agent']}')
        print(f'  Model: {config_info['model']}')
        print(f'  Language: {config_info['language']}')
        print(f'{'=' * 80}')
        repos = [r for r in os.listdir(config_path) if os.path.isdir(os.path.join(config_path, r)) and (not r.startswith('.'))]
        config_key = (config_info['agent'], config_info['model'], config_info['language'])
        for repo_name in sorted(repos):
            repo_path = os.path.join(config_path, repo_name)
            readme_path = os.path.join(repo_path, 'README.md')
            if not os.path.exists(readme_path):
                code_dir = os.path.dirname(os.path.dirname(base_path))
                if config_info['language'] == 'Python':
                    verified_readme = os.path.join(code_dir, 'repo_readme_verified_python_no_t', repo_name, 'README.md')
                elif config_info['language'] == 'Java':
                    verified_readme = os.path.join(code_dir, 'repo_readme_verified_java_no_t_with_p', repo_name, 'README.md')
                else:
                    verified_readme = None
                if verified_readme and os.path.exists(verified_readme):
                    readme_path = verified_readme
                    print(f'  Analyzing: {repo_name} (using verified README)')
                else:
                    print(f'  Analyzing: {repo_name} (no README found)')
            else:
                print(f'  Analyzing: {repo_name}')
            endpoints = extract_api_endpoints_from_readme(readme_path)
            if len(endpoints) == 0:
                print(f'    No API endpoints found')
                continue
            implemented = 0
            for endpoint in endpoints:
                if search_implementation(repo_path, endpoint):
                    implemented += 1
            coverage = implemented / len(endpoints) if len(endpoints) > 0 else 0.0
            print(f'    APIs: {implemented}/{len(endpoints)} = {coverage:.2%}')
            repo_result = {'repo_name': repo_name, 'total_apis': len(endpoints), 'implemented_apis': implemented, 'coverage': coverage}
            results_by_config[config_key]['repos'].append(repo_result)
            results_by_config[config_key]['total_apis'] += len(endpoints)
            results_by_config[config_key]['implemented_apis'] += implemented
        if results_by_config[config_key]['total_apis'] > 0:
            results_by_config[config_key]['coverage'] = results_by_config[config_key]['implemented_apis'] / results_by_config[config_key]['total_apis']
    return dict(results_by_config)

# Node: parse_agent_dirname
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

def run_tests(test_pattern=None, verbose=False, coverage=False, parallel=False):
    cmd = ['python', '-m', 'pytest']
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append('test_blog_api.py')
    if verbose:
        cmd.extend(['-v', '-s'])
    if coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term-missing'])
    if parallel:
        cmd.extend(['-n', 'auto'])
    cmd.extend(['--tb=short', '--strict-markers', '--disable-warnings', '--color=yes', '--durations=10'])
    print(f'Running command: {' '.join(cmd)}')
    print('-' * 50)
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print('\nTest interrupted by user')
        return 1
    except Exception as e:
        print(f'Running test failed: {e}')
        return 1

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

# Node: run_tests
def run_tests(test_type: str='all', verbose: bool=True, coverage: bool=False):
    cmd = ['python', '-m', 'pytest']
    if verbose:
        cmd.append('-v')
    if coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
    if test_type == 'auth':
        cmd.extend(['-m', 'auth'])
    elif test_type == 'upload':
        cmd.extend(['-m', 'upload'])
    elif test_type == 'download':
        cmd.extend(['-m', 'download'])
    elif test_type == 'share':
        cmd.extend(['-m', 'share'])
    elif test_type == 'storage':
        cmd.extend(['-m', 'storage'])
    elif test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'fast':
        cmd.extend(['-m', 'not slow'])
    elif test_type == 'slow':
        cmd.extend(['-m', 'slow'])
    else:
        cmd.append('.')
    cmd.append('.')
    print(f'Running command: {' '.join(cmd)}')
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print('\nTest execution interrupted by user')
        return 1
    except Exception as e:
        print(f'Error running tests: {e}')
        return 1

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

# Node: skipif
@pytest.mark.skipif(jsonschema is None, reason='jsonschema is required for contract validation')
def test_json_schemas_are_valid_json():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    text = open(readme_path, 'r', encoding='utf-8').read()
    code_blocks = re.findall('```json\\n([\\s\\S]*?)\\n```', text)
    assert code_blocks, 'At least one JSON schema code block is required'
    for block in code_blocks:
        schema = json.loads(block)
        assert isinstance(schema, dict), 'Schema must be a JSON object'
        assert '$schema' in schema, 'Each schema should declare $schema'

# Node: loads
@pytest.mark.skipif(requests is None or jsonschema is None, reason='requests and jsonschema required')
def test_healthcheck_contract_or_skip_if_unavailable():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    text = open(readme_path, 'r', encoding='utf-8').read()
    blocks = re.findall('1\\) HealthCheck Output Schema\\n```json\\n([\\s\\S]*?)\\n```', text)
    assert blocks, 'HealthCheck output schema must be documented'
    schema = json.loads(blocks[0])
    url = f'{BASE_URL}/health'
    try:
        resp = requests.get(url, timeout=2)
    except Exception:
        pytest.skip('Service not available; skipping live contract check')
    assert resp.status_code == 200
    payload = resp.json()
    jsonschema.validate(instance=payload, schema=schema)

# Node: validate
@pytest.mark.skipif(requests is None or jsonschema is None, reason='requests and jsonschema required')
def test_auth_flow_contract_shapes_defined():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    text = open(readme_path, 'r', encoding='utf-8').read()
    reg_in = re.findall('2\\) RegisterUser Input Schema\\n```json\\n([\\s\\S]*?)\\n```', text)
    reg_out = re.findall('RegisterUser Output Schema\\n```json\\n([\\s\\S]*?)\\n```', text)
    log_in = re.findall('3\\) LoginUser Input Schema\\n```json\\n([\\s\\S]*?)\\n```', text)
    log_out = re.findall('LoginUser Output Schema\\n```json\\n([\\s\\S]*?)\\n```', text)
    for name, blocks in {'RegisterUser Input': reg_in, 'RegisterUser Output': reg_out, 'LoginUser Input': log_in, 'LoginUser Output': log_out}.items():
        assert blocks, f'Missing schema block: {name}'
        json.loads(blocks[0])

def _load_schema_by_title(readme_text: str, heading_regex: str) -> Dict[str, Any]:
    blocks = re.findall(heading_regex + '\\n```json\\n([\\s\\S]*?)\\n```', readme_text)
    assert blocks, f'Schema not found for heading regex: {heading_regex}'
    return json.loads(blocks[0])

@pytest.mark.skipif(requests is None or jsonschema is None, reason='requests and jsonschema required')
def test_message_contract_schemas_present():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    text = open(readme_path, 'r', encoding='utf-8').read()
    send_in = _load_schema_by_title(text, '4\\) SendMessage Input Schema')
    send_out = _load_schema_by_title(text, 'SendMessage Output Schema')
    list_out = _load_schema_by_title(text, '5\\) ListMessages Output Schema')
    assert send_in.get('type') == 'object'
    assert send_out.get('type') == 'object'
    assert list_out.get('type') == 'object'

# Node: _load_schema_by_title
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

