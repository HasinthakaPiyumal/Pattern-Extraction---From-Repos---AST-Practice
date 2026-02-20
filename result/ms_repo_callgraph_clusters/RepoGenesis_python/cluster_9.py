# Cluster 9

def start_service(command: str, repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')
    proc = subprocess.Popen(command, cwd=str(repo_root), env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc

# Node: setdefault
# Node: Popen
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
# Node: any
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
def start_service(command: str, repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')
    proc = subprocess.Popen(command, cwd=str(repo_root), env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc

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

