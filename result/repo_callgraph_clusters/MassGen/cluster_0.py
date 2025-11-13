# Cluster 0

def extract_slides_from_file(file_path):
    """Extract individual slides from a presentation file."""
    content = Path(file_path).read_text()
    slide_pattern = '(<!-- Slide \\d+: [^>]*>.*?)(?=<!-- Slide \\d+:|<!-- Navigation -->|$)'
    slides = re.findall(slide_pattern, content, re.DOTALL)
    return slides

def extract_head_section(file_path):
    """Extract head section from presentation file."""
    content = Path(file_path).read_text()
    head_pattern = '(<!DOCTYPE html>.*?</head>)'
    head_match = re.search(head_pattern, content, re.DOTALL)
    return head_match.group(1) if head_match else ''

def extract_navigation_section(file_path):
    """Extract navigation section from presentation file."""
    content = Path(file_path).read_text()
    nav_pattern = '(<!-- Navigation -->.*?</html>)'
    nav_match = re.search(nav_pattern, content, re.DOTALL)
    return nav_match.group(1) if nav_match else ''

def load_component(component_name):
    """Load a component file from the components directory."""
    component_path = Path(__file__).parent / 'components' / f'{component_name}.html'
    if component_path.exists():
        return component_path.read_text()
    else:
        print(f'Warning: Component {component_name} not found')
        return ''

class LinkValidator:
    """Validate links in documentation files."""

    def __init__(self, docs_path: Path, check_external: bool=False):
        self.docs_path = docs_path / 'source'
        self.check_external = check_external
        self.errors: List[Tuple[Path, str, str]] = []
        self.warnings: List[Tuple[Path, str, str]] = []

    def check_doc_reference(self, file_path: Path, ref: str):
        """Check if a :doc: reference is valid."""
        if ref.startswith('../'):
            target_path = (file_path.parent / ref).resolve()
        elif ref.startswith('/'):
            target_path = self.docs_path / ref.lstrip('/')
        else:
            target_path = file_path.parent / ref
        if not str(target_path).endswith('.rst'):
            target_path = Path(str(target_path) + '.rst')
        if not target_path.exists():
            self.errors.append((file_path, f':doc:`{ref}`', f'Referenced file does not exist: {target_path.relative_to(self.docs_path.parent)}'))
            return False
        return True

    def check_external_link(self, file_path: Path, url: str):
        """Check if an external link is valid (optional, slow)."""
        if not self.check_external:
            return True
        try:
            import requests
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                self.warnings.append((file_path, url, f'HTTP {response.status_code}'))
                return False
        except Exception as e:
            self.warnings.append((file_path, url, f'Connection error: {e}'))
            return False
        return True

    def scan_file(self, file_path: Path):
        """Scan a single file for links."""
        try:
            content = file_path.read_text()
            doc_refs = re.findall(':doc:`([^`]+)`', content)
            for ref in doc_refs:
                custom_match = re.match('(.+)<(.+)>', ref)
                if custom_match:
                    ref = custom_match.group(2).strip()
                self.check_doc_reference(file_path, ref)
            external_links = re.findall('`[^`]+<(https?://[^>]+)>`_', content)
            for url in external_links:
                if self.check_external:
                    self.check_external_link(file_path, url)
            standalone_urls = re.findall('https?://[^\\s<>`]+', content)
            for url in standalone_urls:
                if url not in external_links:
                    if self.check_external:
                        self.check_external_link(file_path, url)
        except Exception as e:
            self.errors.append((file_path, 'FILE', f'Error reading file: {e}'))

    def scan_all(self):
        """Scan all RST files."""
        rst_files = list(self.docs_path.rglob('*.rst'))
        print(f'Scanning {len(rst_files)} documentation files for broken links...')
        if self.check_external:
            print('(Including external link validation - this may take a while)')
        for file_path in rst_files:
            rel_path = file_path.relative_to(self.docs_path)
            print(f'  {rel_path}')
            self.scan_file(file_path)

    def generate_report(self, output_path: Path):
        """Generate validation report."""
        report_lines = []
        report_lines.append('# Documentation Link Validation Report')
        report_lines.append('')
        report_lines.append(f'**Date:** {Path(__file__).stat().st_mtime}')
        report_lines.append(f'**External Links Checked:** {self.check_external}')
        report_lines.append('')
        report_lines.append('## Summary')
        report_lines.append('')
        report_lines.append(f'- **Errors:** {len(self.errors)}')
        report_lines.append(f'- **Warnings:** {len(self.warnings)}')
        report_lines.append('')
        if self.errors:
            report_lines.append('## Errors (Broken Links)')
            report_lines.append('')
            by_file: Dict[Path, List[Tuple[str, str]]] = {}
            for file_path, link, error in self.errors:
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append((link, error))
            for file_path, issues in sorted(by_file.items()):
                rel_path = file_path.relative_to(self.docs_path)
                report_lines.append(f'### {rel_path}')
                report_lines.append('')
                for link, error in issues:
                    report_lines.append(f'- **Link:** `{link}`')
                    report_lines.append(f'  - **Error:** {error}')
                    report_lines.append('')
        if self.warnings:
            report_lines.append('## Warnings (External Links)')
            report_lines.append('')
            by_file: Dict[Path, List[Tuple[str, str]]] = {}
            for file_path, link, warning in self.warnings:
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append((link, warning))
            for file_path, issues in sorted(by_file.items()):
                rel_path = file_path.relative_to(self.docs_path)
                report_lines.append(f'### {rel_path}')
                report_lines.append('')
                for link, warning in issues:
                    report_lines.append(f'- **Link:** `{link}`')
                    report_lines.append(f'  - **Warning:** {warning}')
                    report_lines.append('')
        if not self.errors and (not self.warnings):
            report_lines.append('✓ No broken links detected!')
            report_lines.append('')
        report_lines.append('---')
        report_lines.append('')
        report_lines.append('*Generated by `scripts/validate_links.py`*')
        output_path.write_text('\n'.join(report_lines))
        print(f'\n✓ Report saved to {output_path}')

    def print_summary(self):
        """Print summary to console."""
        print('\n' + '=' * 60)
        print('LINK VALIDATION SUMMARY')
        print('=' * 60)
        if not self.errors and (not self.warnings):
            print('\n✓ All links are valid!')
        else:
            if self.errors:
                print(f'\n✗ {len(self.errors)} broken links found')
                print('\nTop files with errors:')
                by_file: Dict[Path, int] = {}
                for file_path, _, _ in self.errors:
                    by_file[file_path] = by_file.get(file_path, 0) + 1
                for file_path, count in sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]:
                    rel_path = file_path.relative_to(self.docs_path)
                    print(f'  {count:3d}  {rel_path}')
            if self.warnings:
                print(f'\n⚠ {len(self.warnings)} warnings (external links)')
        print('\n' + '=' * 60)

def check_doc_reference(self, file_path: Path, ref: str):
    """Check if a :doc: reference is valid."""
    if ref.startswith('../'):
        target_path = (file_path.parent / ref).resolve()
    elif ref.startswith('/'):
        target_path = self.docs_path / ref.lstrip('/')
    else:
        target_path = file_path.parent / ref
    if not str(target_path).endswith('.rst'):
        target_path = Path(str(target_path) + '.rst')
    if not target_path.exists():
        self.errors.append((file_path, f':doc:`{ref}`', f'Referenced file does not exist: {target_path.relative_to(self.docs_path.parent)}'))
        return False
    return True

def get_log_session_dir(turn: Optional[int]=None) -> Path:
    """Get the current log session directory.

    Args:
        turn: Optional turn number for multi-turn conversations

    Returns:
        Path to the log directory
    """
    global _LOG_SESSION_DIR, _LOG_BASE_SESSION_DIR, _CURRENT_TURN
    if _LOG_BASE_SESSION_DIR is None:
        cwd = Path.cwd()
        pyproject_file = cwd / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text()
                if 'name = "massgen"' in content:
                    pass
            except Exception:
                pass
        log_base_dir = Path('.massgen') / 'massgen_logs'
        log_base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        _LOG_BASE_SESSION_DIR = log_base_dir / f'log_{timestamp}'
        _LOG_BASE_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    if turn is not None and turn != _CURRENT_TURN:
        _CURRENT_TURN = turn
        _LOG_SESSION_DIR = None
    if _LOG_SESSION_DIR is None:
        if _CURRENT_TURN and _CURRENT_TURN > 0:
            _LOG_SESSION_DIR = _LOG_BASE_SESSION_DIR / f'turn_{_CURRENT_TURN}'
        else:
            _LOG_SESSION_DIR = _LOG_BASE_SESSION_DIR
        _LOG_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_SESSION_DIR

def load_env_file():
    """Load environment variables from .env files.

    Search order (later files override earlier ones):
    1. MassGen package .env (development fallback)
    2. User home ~/.massgen/.env (global user config)
    3. Current directory .env (project-specific, highest priority)
    """
    load_dotenv(Path(__file__).parent / '.env')
    load_dotenv(Path.home() / '.massgen' / '.env')
    load_dotenv()

def resolve_config_path(config_arg: Optional[str]) -> Optional[Path]:
    """Resolve config file with flexible syntax.

    Priority order:

    **If --config flag provided (highest priority):**
    1. @examples/NAME → Package examples (search configs directory)
    2. Absolute/relative paths (exact path as specified)
    3. Named configs in ~/.config/massgen/agents/

    **If NO --config flag (auto-discovery):**
    1. .massgen/config.yaml (project-level config in current directory)
    2. ~/.config/massgen/config.yaml (global default config)
    3. None → trigger config builder

    Args:
        config_arg: Config argument from --config flag (can be @examples/NAME, path, or None)

    Returns:
        Path to config file, or None if config builder should run

    Raises:
        ConfigurationError: If config file not found
    """
    if not config_arg:
        project_config = Path.cwd() / '.massgen' / 'config.yaml'
        if project_config.exists():
            return project_config
        global_config = Path.home() / '.config/massgen/config.yaml'
        if global_config.exists():
            return global_config
        return None
    if config_arg.startswith('@examples/'):
        name = config_arg[10:]
        try:
            from importlib.resources import files
            configs_root = files('massgen') / 'configs'
            for config_file in configs_root.rglob('*.yaml'):
                if name in config_file.name or name in str(config_file):
                    return Path(str(config_file))
            raise ConfigurationError(f"Config '{config_arg}' not found in package.\nUse --list-examples to see available configs.")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f'Error loading package config: {e}')
    path = Path(config_arg).expanduser()
    if path.exists():
        return path
    user_agents_dir = Path.home() / '.config/massgen/agents'
    user_config = user_agents_dir / f'{config_arg}.yaml'
    if user_config.exists():
        return user_config
    if not config_arg.endswith(('.yaml', '.yml')):
        user_config_with_ext = user_agents_dir / f'{config_arg}.yaml'
        if user_config_with_ext.exists():
            return user_config_with_ext
    raise ConfigurationError(f'Configuration file not found: {config_arg}\nSearched in:\n  - Current directory: {Path.cwd() / config_arg}\n  - User configs: {user_agents_dir / config_arg}.yaml\nUse --list-examples to see available package configs.')

def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file.

    Search order:
    1. Exact path as provided (absolute or relative to CWD)
    2. If just a filename, search in package's configs/ directory
    3. If a relative path, also try within package's configs/ directory

    Supports variable substitution: ${cwd} in any string will be replaced with the agent's cwd value.
    """
    path = Path(config_path)
    if path.exists():
        pass
    elif path.is_absolute():
        raise ConfigurationError(f'Configuration file not found: {config_path}')
    else:
        package_configs_dir = Path(__file__).parent / 'configs'
        candidate1 = package_configs_dir / path.name
        candidate2 = package_configs_dir / path
        if candidate1.exists():
            path = candidate1
        elif candidate2.exists():
            path = candidate2
        else:
            raise ConfigurationError(f'Configuration file not found: {config_path}\nSearched in:\n  - {Path.cwd() / config_path}\n  - {candidate1}\n  - {candidate2}')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ConfigurationError(f'Unsupported config file format: {path.suffix}')
    except Exception as e:
        raise ConfigurationError(f'Error reading config file: {e}')

def validate_context_paths(config: Dict[str, Any]) -> None:
    """Validate that all context paths in the config exist.

    Context paths can be either files or directories.
    File-level context paths allow access to specific files without exposing sibling files.
    Raises ConfigurationError with clear message if any paths don't exist.
    """
    orchestrator_cfg = config.get('orchestrator', {})
    context_paths = orchestrator_cfg.get('context_paths', [])
    missing_paths = []
    for context_path_config in context_paths:
        if isinstance(context_path_config, dict):
            path = context_path_config.get('path')
        else:
            path = context_path_config
        if path:
            path_obj = Path(path)
            if not path_obj.exists():
                missing_paths.append(path)
    if missing_paths:
        errors = ['Context paths not found:']
        for path in missing_paths:
            errors.append(f'  - {path}')
        errors.append('\nPlease update your configuration with valid paths.')
        raise ConfigurationError('\n'.join(errors))

def relocate_filesystem_paths(config: Dict[str, Any]) -> None:
    """Relocate filesystem paths (orchestrator paths and agent workspaces) to be under .massgen/ directory.

    Modifies the config in-place to ensure all MassGen state is organized
    under .massgen/ for clean project structure.
    """
    massgen_dir = Path('.massgen')
    orchestrator_cfg = config.get('orchestrator', {})
    if orchestrator_cfg:
        path_fields = ['snapshot_storage', 'agent_temporary_workspace', 'session_storage']
        for field in path_fields:
            if field in orchestrator_cfg:
                user_path = orchestrator_cfg[field]
                if Path(user_path).is_absolute() or user_path.startswith('.massgen/'):
                    continue
                orchestrator_cfg[field] = str(massgen_dir / user_path)
    agent_entries = [config['agent']] if 'agent' in config else config.get('agents', [])
    for agent_data in agent_entries:
        backend_config = agent_data.get('backend', {})
        if 'cwd' in backend_config:
            user_cwd = backend_config['cwd']
            if Path(user_cwd).is_absolute() or user_cwd.startswith('.massgen/'):
                continue
            backend_config['cwd'] = str(massgen_dir / 'workspaces' / user_cwd)

def load_previous_turns(session_info: Dict[str, Any], session_storage: str) -> List[Dict[str, Any]]:
    """
    Load previous turns from session storage.

    Returns:
        List of previous turn metadata dicts
    """
    session_id = session_info.get('session_id')
    if not session_id:
        return []
    session_dir = Path(session_storage) / session_id
    if not session_dir.exists():
        return []
    previous_turns = []
    turn_num = 1
    while True:
        turn_dir = session_dir / f'turn_{turn_num}'
        if not turn_dir.exists():
            break
        metadata_file = turn_dir / 'metadata.json'
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            workspace_path = (turn_dir / 'workspace').resolve()
            previous_turns.append({'turn': turn_num, 'path': str(workspace_path), 'task': metadata.get('task', ''), 'winning_agent': metadata.get('winning_agent', '')})
        turn_num += 1
    return previous_turns

class FilesystemManager:
    """
    Manages filesystem operations for backends with MCP filesystem support.

    This class handles:
    - Workspace directory lifecycle (creation, cleanup)
    - Snapshot storage and restoration for context sharing
    - Path management for MCP filesystem server configuration
    """

    def __init__(self, cwd: str, agent_temporary_workspace_parent: str=None, context_paths: List[Dict[str, Any]]=None, context_write_access_enabled: bool=False, enforce_read_before_delete: bool=True, enable_image_generation: bool=False, enable_mcp_command_line: bool=False, command_line_allowed_commands: List[str]=None, command_line_blocked_commands: List[str]=None, command_line_execution_mode: str='local', command_line_docker_image: str='massgen/mcp-runtime:latest', command_line_docker_memory_limit: Optional[str]=None, command_line_docker_cpu_limit: Optional[float]=None, command_line_docker_network_mode: str='none', enable_audio_generation: bool=False):
        """
        Initialize FilesystemManager.

        Args:
            cwd: Working directory path for the agent
            agent_temporary_workspace_parent: Parent directory for temporary workspaces
            context_paths: List of context path configurations for access control
            context_write_access_enabled: Whether write access is enabled for context paths
            enforce_read_before_delete: Whether to enforce read-before-delete policy for workspace files
            enable_image_generation: Whether to enable image generation tools
            enable_mcp_command_line: Whether to enable MCP command line execution tool
            command_line_allowed_commands: Whitelist of allowed command patterns (regex)
            command_line_blocked_commands: Blacklist of blocked command patterns (regex)
            command_line_execution_mode: Execution mode - "local" or "docker"
            command_line_docker_image: Docker image to use for containers
            command_line_docker_memory_limit: Memory limit for Docker containers (e.g., "2g")
            command_line_docker_cpu_limit: CPU limit for Docker containers (e.g., 2.0 for 2 CPUs)
            command_line_docker_network_mode: Network mode for Docker containers (none/bridge/host)
        """
        self.agent_id = None
        self.enable_image_generation = enable_image_generation
        self.enable_mcp_command_line = enable_mcp_command_line
        self.command_line_allowed_commands = command_line_allowed_commands
        self.command_line_blocked_commands = command_line_blocked_commands
        self.command_line_execution_mode = command_line_execution_mode
        self.command_line_docker_image = command_line_docker_image
        self.command_line_docker_memory_limit = command_line_docker_memory_limit
        self.command_line_docker_cpu_limit = command_line_docker_cpu_limit
        self.command_line_docker_network_mode = command_line_docker_network_mode
        self.docker_manager = None
        if enable_mcp_command_line and command_line_execution_mode == 'docker':
            from ._docker_manager import DockerManager
            self.docker_manager = DockerManager(image=command_line_docker_image, network_mode=command_line_docker_network_mode, memory_limit=command_line_docker_memory_limit, cpu_limit=command_line_docker_cpu_limit)
        self.enable_audio_generation = enable_audio_generation
        self.path_permission_manager = PathPermissionManager(context_write_access_enabled=context_write_access_enabled, enforce_read_before_delete=enforce_read_before_delete)
        if context_paths:
            self.path_permission_manager.add_context_paths(context_paths)
        self.agent_temporary_workspace_parent = agent_temporary_workspace_parent
        if self.agent_temporary_workspace_parent:
            temp_parent = self.agent_temporary_workspace_parent
            temp_parent_path = Path(temp_parent)
            if not temp_parent_path.is_absolute():
                temp_parent_path = temp_parent_path.resolve()
            self.agent_temporary_workspace_parent = temp_parent_path
            self.clear_temp_workspace()
        self.cwd = self._setup_workspace(cwd)
        self.path_permission_manager.add_path(self.cwd, Permission.WRITE, 'workspace')
        self.path_permission_manager.add_path(self.agent_temporary_workspace_parent, Permission.READ, 'temp_workspace')
        self.snapshot_storage = None
        self.agent_temporary_workspace = None
        self._using_temporary = False
        self._original_cwd = self.cwd

    def setup_orchestration_paths(self, agent_id: str, snapshot_storage: Optional[str]=None, agent_temporary_workspace: Optional[str]=None) -> None:
        """
        Setup orchestration-specific paths for snapshots and temporary workspace.
        Called by orchestrator to configure paths for this specific orchestration.

        Args:
            agent_id: The agent identifier for this orchestration
            snapshot_storage: Base path for storing workspace snapshots
            agent_temporary_workspace: Base path for temporary workspace during context sharing
        """
        logger.info(f'[FilesystemManager.setup_orchestration_paths] Called for agent_id={agent_id}, snapshot_storage={snapshot_storage}, agent_temporary_workspace={agent_temporary_workspace}')
        self.agent_id = agent_id
        if snapshot_storage and self.agent_id:
            self.snapshot_storage = Path(snapshot_storage) / self.agent_id
            self.snapshot_storage.mkdir(parents=True, exist_ok=True)
        if agent_temporary_workspace and self.agent_id:
            self.agent_temporary_workspace = self._setup_workspace(self.agent_temporary_workspace_parent / self.agent_id)
        if self.agent_id:
            log_session_dir = get_log_session_dir()
            if log_session_dir:
                agent_log_dir = log_session_dir / self.agent_id
                agent_log_dir.mkdir(parents=True, exist_ok=True)
        if self.docker_manager and self.agent_id:
            context_paths = self.path_permission_manager.get_context_paths()
            self.docker_manager.create_container(agent_id=self.agent_id, workspace_path=self.cwd, temp_workspace_path=self.agent_temporary_workspace_parent if self.agent_temporary_workspace_parent else None, context_paths=context_paths)
            logger.info(f'[FilesystemManager] Docker container created for agent {self.agent_id}')

    def update_backend_mcp_config(self, backend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update MCP server configuration with agent_id after it's available.

        This should be called by the backend after setup_orchestration_paths() sets agent_id.

        Args:
            backend_config: Backend configuration dict containing mcp_servers

        Returns:
            Updated backend configuration
        """
        if not self.enable_mcp_command_line or self.command_line_execution_mode != 'docker':
            return backend_config
        if not self.agent_id:
            logger.warning('[FilesystemManager] agent_id not set, cannot update MCP config for Docker mode')
            return backend_config
        mcp_servers = backend_config.get('mcp_servers', [])
        for server in mcp_servers:
            if isinstance(server, dict) and server.get('name') == 'command_line':
                args = server.get('args', [])
                if '--agent-id' not in args:
                    args.extend(['--agent-id', self.agent_id])
                    server['args'] = args
                    logger.info(f'[FilesystemManager] Updated command_line MCP server config with agent_id: {self.agent_id}')
                break
        return backend_config

    def _setup_workspace(self, cwd: str) -> Path:
        """Setup workspace directory, creating if needed and clearing existing files safely."""
        Path(cwd)
        workspace = Path(cwd).resolve()
        if not workspace.is_absolute():
            raise AssertionError('Workspace must be absolute')
        if workspace == Path('/') or len(workspace.parts) < 3:
            raise AssertionError(f'Refusing unsafe workspace path: {workspace}')
        workspace.mkdir(parents=True, exist_ok=True)
        if workspace.exists() and workspace.is_dir():
            for item in workspace.iterdir():
                if item.is_symlink():
                    logger.warning(f'[FilesystemManager.save_snapshot] Skipping symlink during clear: {item}')
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        return workspace

    def get_mcp_filesystem_config(self) -> Dict[str, Any]:
        """
        Generate MCP filesystem server configuration.

        Returns:
            Dictionary with MCP server configuration for filesystem access
        """
        paths = self.path_permission_manager.get_mcp_filesystem_paths()
        config = {'name': 'filesystem', 'type': 'stdio', 'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-filesystem'] + paths, 'cwd': str(self.cwd), 'exclude_tools': ['read_media_file']}
        return config

    def get_workspace_tools_mcp_config(self) -> Dict[str, Any]:
        """
        Generate workspace tools MCP server configuration.

        Returns:
            Dictionary with MCP server configuration for workspace tools (copy, delete, compare)
        """
        context_paths = self.path_permission_manager.get_context_paths()
        ','.join([cp['path'] for cp in context_paths])
        script_path = Path(wc_module.__file__).resolve()
        paths = self.path_permission_manager.get_mcp_filesystem_paths()
        env = {'FASTMCP_SHOW_CLI_BANNER': 'false'}
        config = {'name': 'workspace_tools', 'type': 'stdio', 'command': 'fastmcp', 'args': ['run', f'{script_path}:create_server'] + ['--', '--allowed-paths'] + paths, 'env': env, 'cwd': str(self.cwd)}
        if not self.enable_image_generation:
            config['exclude_tools'] = ['generate_and_store_image_with_input_images', 'generate_and_store_image_no_input_images']
        if not self.enable_audio_generation:
            if 'exclude_tools' not in config:
                config['exclude_tools'] = []
            config['exclude_tools'].extend(['generate_and_store_audio_with_input_audios', 'generate_and_store_audio_no_input_audios'])
        return config

    def get_command_line_mcp_config(self) -> Dict[str, Any]:
        """
        Generate command line execution MCP server configuration.

        Returns:
            Dictionary with MCP server configuration for command execution
            (supports bash on Unix/Mac, cmd/PowerShell on Windows, and Docker isolation)
        """
        script_path = Path(ce_module.__file__).resolve()
        paths = self.path_permission_manager.get_mcp_filesystem_paths()
        env = {'FASTMCP_SHOW_CLI_BANNER': 'false'}
        if 'DOCKER_HOST' in os.environ:
            env['DOCKER_HOST'] = os.environ['DOCKER_HOST']
        config = {'name': 'command_line', 'type': 'stdio', 'command': 'fastmcp', 'args': ['run', f'{script_path}:create_server', '--', '--allowed-paths'] + paths, 'env': env, 'cwd': str(self.cwd)}
        config['args'].extend(['--execution-mode', self.command_line_execution_mode])
        if self.command_line_execution_mode == 'docker' and self.agent_id:
            config['args'].extend(['--agent-id', self.agent_id])
        if self.command_line_allowed_commands:
            config['args'].extend(['--allowed-commands'] + self.command_line_allowed_commands)
        if self.command_line_blocked_commands:
            config['args'].extend(['--blocked-commands'] + self.command_line_blocked_commands)
        return config

    def inject_filesystem_mcp(self, backend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject filesystem and workspace tools MCP servers into backend configuration.

        Args:
            backend_config: Original backend configuration

        Returns:
            Modified configuration with MCP servers added
        """
        mcp_servers = backend_config.get('mcp_servers', [])
        if isinstance(mcp_servers, dict):
            existing_names = list(mcp_servers.keys())
            converted_servers = []
            for name, server_config in mcp_servers.items():
                if isinstance(server_config, dict):
                    server = server_config.copy()
                    server['name'] = name
                    converted_servers.append(server)
            mcp_servers = converted_servers
        elif isinstance(mcp_servers, list):
            existing_names = [server.get('name') for server in mcp_servers if isinstance(server, dict)]
        else:
            existing_names = []
            mcp_servers = []
        try:
            if 'filesystem' not in existing_names:
                mcp_servers.append(self.get_mcp_filesystem_config())
            else:
                logger.warning('[FilesystemManager.inject_filesystem_mcp] Custom filesystem MCP server already present')
            if 'workspace_tools' not in existing_names:
                mcp_servers.append(self.get_workspace_tools_mcp_config())
            else:
                logger.warning('[FilesystemManager.inject_filesystem_mcp] Custom workspace_tools MCP server already present')
            if self.enable_mcp_command_line and 'command_line' not in existing_names:
                mcp_servers.append(self.get_command_line_mcp_config())
            elif self.enable_mcp_command_line:
                logger.warning('[FilesystemManager.inject_filesystem_mcp] Custom command_line MCP server already present')
        except Exception as e:
            logger.warning(f'[FilesystemManager.inject_filesystem_mcp] Error checking existing MCP servers: {e}')
        backend_config['mcp_servers'] = mcp_servers
        return backend_config

    def inject_command_line_mcp(self, backend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject only the command_line MCP server into backend configuration.

        Used for NATIVE backends (like Claude Code) that have built-in filesystem tools
        but need the execute_command MCP tool when using docker mode for code execution.

        Args:
            backend_config: Original backend configuration

        Returns:
            Modified configuration with command_line MCP server added
        """
        mcp_servers = backend_config.get('mcp_servers', [])
        if isinstance(mcp_servers, dict):
            existing_names = list(mcp_servers.keys())
            converted_servers = []
            for name, server_config in mcp_servers.items():
                if isinstance(server_config, dict):
                    server = server_config.copy()
                    server['name'] = name
                    converted_servers.append(server)
            mcp_servers = converted_servers
        elif isinstance(mcp_servers, list):
            existing_names = [server.get('name') for server in mcp_servers if isinstance(server, dict)]
        else:
            existing_names = []
            mcp_servers = []
        try:
            if 'command_line' not in existing_names:
                mcp_servers.append(self.get_command_line_mcp_config())
                logger.info('[FilesystemManager.inject_command_line_mcp] Added command_line MCP server for docker mode')
            else:
                logger.warning('[FilesystemManager.inject_command_line_mcp] Custom command_line MCP server already present')
        except Exception as e:
            logger.warning(f'[FilesystemManager.inject_command_line_mcp] Error adding command_line MCP server: {e}')
        backend_config['mcp_servers'] = mcp_servers
        return backend_config

    def get_pre_tool_hooks(self) -> Dict[str, List]:
        """
        Get pre-tool hooks configuration for MCP clients.

        Returns:
            Dict mapping hook types to lists of hook functions
        """

        async def mcp_hook_wrapper(tool_name: str, tool_args: Dict[str, Any]) -> bool:
            """Wrapper to adapt our hook signature to MCP client expectations."""
            allowed, reason = await self.path_permission_manager.pre_tool_use_hook(tool_name, tool_args)
            if not allowed and reason:
                logger.warning(f'[FilesystemManager] Tool blocked: {tool_name} - {reason}')
            return allowed
        return {HookType.PRE_TOOL_USE: [mcp_hook_wrapper]}

    def get_claude_code_hooks_config(self) -> Dict[str, Any]:
        """
        Get Claude Agent SDK hooks configuration.

        Returns:
            Hooks configuration dict for ClaudeAgentOptions
        """
        return self.path_permission_manager.get_claude_code_hooks_config()

    def enable_write_access(self) -> None:
        """
        Enable write access for this filesystem manager.

        This should be called for final agents to allow them to modify
        files with write permissions in their context paths.
        """
        self.path_permission_manager.context_write_access_enabled = True
        logger.info('[FilesystemManager] Context write access enabled - agent can now modify files with write permissions')

    async def save_snapshot(self, timestamp: Optional[str]=None, is_final: bool=False) -> None:
        """
        Save a snapshot of the workspace. Always saves to snapshot_storage if available (keeping only most recent).
        Additionally saves to log directories if logging is enabled.
        Then, clear the workspace so it is ready for next execution.

        Args:
            timestamp: Optional timestamp to use for the snapshot directory (if not provided, generates one)
            is_final: If True, save as final snapshot for presentation

        TODO: reimplement without 'shutil' and 'os' operations for true async, though we may not need to worry about race conditions here since only one agent writes at a time
        """
        logger.info(f'[FilesystemManager.save_snapshot] Called for agent_id={self.agent_id}, is_final={is_final}, snapshot_storage={self.snapshot_storage}')
        source_dir = self.cwd
        source_path = Path(source_dir)
        if not source_path.exists() or not source_path.is_dir():
            logger.warning(f'[FilesystemManager] Source path invalid - exists: {source_path.exists()}, is_dir: {(source_path.is_dir() if source_path.exists() else False)}')
            return
        if not any(source_path.iterdir()):
            logger.warning(f'[FilesystemManager.save_snapshot] Source path {source_path} is empty, skipping snapshot')
            return
        try:
            if self.snapshot_storage:
                if self.snapshot_storage.exists():
                    shutil.rmtree(self.snapshot_storage)
                self.snapshot_storage.mkdir(parents=True, exist_ok=True)
                items_copied = 0
                for item in source_path.iterdir():
                    if item.is_symlink():
                        logger.warning(f'[FilesystemManager.save_snapshot] Skipping symlink: {item}')
                        continue
                    if item.is_file():
                        shutil.copy2(item, self.snapshot_storage / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, self.snapshot_storage / item.name)
                    items_copied += 1
                logger.info(f'[FilesystemManager] Saved snapshot with {items_copied} items to {self.snapshot_storage}')
            log_session_dir = get_log_session_dir()
            if log_session_dir and self.agent_id:
                if is_final:
                    dest_dir = log_session_dir / 'final' / self.agent_id / 'workspace'
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f'[FilesystemManager.save_snapshot] Final log snapshot dest_dir: {dest_dir}')
                else:
                    if not timestamp:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    dest_dir = log_session_dir / self.agent_id / timestamp / 'workspace'
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f'[FilesystemManager.save_snapshot] Regular log snapshot dest_dir: {dest_dir}')
                items_copied = 0
                for item in source_path.iterdir():
                    if item.is_symlink():
                        logger.warning(f'[FilesystemManager.save_snapshot] Skipping symlink: {item}')
                        continue
                    if item.is_file():
                        shutil.copy2(item, dest_dir / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, dest_dir / item.name, dirs_exist_ok=True)
                    items_copied += 1
                logger.info(f'[FilesystemManager] Saved {('final' if is_final else 'regular')} log snapshot with {items_copied} items to {dest_dir}')
        except Exception as e:
            logger.exception(f'[FilesystemManager.save_snapshot] Snapshot failed: {e}')
            return
        logger.info('[FilesystemManager] Snapshot saved successfully, workspace preserved for logs and debugging')

    def clear_workspace(self) -> None:
        """
        Clear the current workspace to prepare for a new agent execution.

        This should be called at the START of agent execution, not at the end,
        to preserve workspace contents for logging and debugging.
        """
        workspace_path = self.get_current_workspace()
        if not workspace_path.exists() or not workspace_path.is_dir():
            logger.debug(f'[FilesystemManager] Workspace does not exist or is not a directory: {workspace_path}')
            return
        if workspace_path == Path('/') or len(workspace_path.parts) < 3:
            logger.error(f'[FilesystemManager] Refusing to clear unsafe workspace path: {workspace_path}')
            return
        try:
            logger.info('[FilesystemManager] Clearing workspace at agent startup. Current contents:')
            items_to_clear = list(workspace_path.iterdir())
            for item in items_to_clear:
                logger.info(f' - {item}')
                if item.is_symlink():
                    logger.warning(f'[FilesystemManager] Skipping symlink during clear: {item}')
                    continue
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info('[FilesystemManager] Workspace cleared successfully, ready for new agent execution')
        except Exception as e:
            logger.error(f'[FilesystemManager] Failed to clear workspace: {e}')

    def clear_temp_workspace(self) -> None:
        """
        Clear the temporary workspace parent directory at orchestration startup.

        This clears the entire temp workspace parent (e.g., temp_workspaces/),
        removing all agent directories from previous runs to prevent cross-contamination.
        """
        if not self.agent_temporary_workspace_parent:
            logger.debug('[FilesystemManager] No temp workspace parent configured to clear')
            return
        if not self.agent_temporary_workspace_parent.exists():
            logger.debug(f'[FilesystemManager] Temp workspace parent does not exist: {self.agent_temporary_workspace_parent}')
            return
        if self.agent_temporary_workspace_parent == Path('/') or len(self.agent_temporary_workspace_parent.parts) < 3:
            logger.error(f'[FilesystemManager] Refusing to clear unsafe temp workspace parent path: {self.agent_temporary_workspace_parent}')
            return
        try:
            logger.info(f'[FilesystemManager] Clearing temp workspace parent at orchestration startup: {self.agent_temporary_workspace_parent}')
            items_to_clear = list(self.agent_temporary_workspace_parent.iterdir())
            for item in items_to_clear:
                logger.info(f' - Removing temp workspace item: {item}')
                if item.is_symlink():
                    logger.warning(f'[FilesystemManager] Skipping symlink during temp clear: {item}')
                    continue
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info('[FilesystemManager] Temp workspace parent cleared successfully')
        except Exception as e:
            logger.error(f'[FilesystemManager] Failed to clear temp workspace parent: {e}')

    async def copy_snapshots_to_temp_workspace(self, all_snapshots: Dict[str, Path], agent_mapping: Dict[str, str]) -> Optional[Path]:
        """
        Copy snapshots from multiple agents to temporary workspace for context sharing.

        This method is called by the orchestrator before starting an agent that needs context from others.
        It copies the latest snapshots from log directories to a temporary workspace.

        Args:
            all_snapshots: Dictionary mapping agent_id to snapshot path (from log directories)
            agent_mapping: Dictionary mapping real agent_id to anonymous agent_id

        Returns:
            Path to the temporary workspace with restored snapshots

        TODO: reimplement without 'shutil' and 'os' operations for true async
        """
        if not self.agent_temporary_workspace:
            return None
        if self.agent_temporary_workspace.exists():
            shutil.rmtree(self.agent_temporary_workspace)
        self.agent_temporary_workspace.mkdir(parents=True, exist_ok=True)
        for agent_id, snapshot_path in all_snapshots.items():
            if snapshot_path.exists() and snapshot_path.is_dir():
                anon_id = agent_mapping.get(agent_id, agent_id)
                dest_dir = self.agent_temporary_workspace / anon_id
                if any(snapshot_path.iterdir()):
                    shutil.copytree(snapshot_path, dest_dir, dirs_exist_ok=True)
        return self.agent_temporary_workspace

    def _log_workspace_contents(self, workspace_path: Path, workspace_name: str, context: str='') -> None:
        """
        Log the contents of a workspace directory for visibility.

        Args:
            workspace_path: Path to the workspace to log
            workspace_name: Human-readable name for the workspace
            context: Additional context (e.g., "before execution", "after execution")
        """
        if not workspace_path or not workspace_path.exists():
            logger.info(f'[FilesystemManager.{workspace_name}] {context} - Workspace does not exist: {workspace_path}')
            return
        try:
            files = list(workspace_path.rglob('*'))
            file_paths = [str(f.relative_to(workspace_path)) for f in files if f.is_file()]
            dir_paths = [str(f.relative_to(workspace_path)) for f in files if f.is_dir()]
            logger.info(f'[FilesystemManager.{workspace_name}] {context} - Workspace: {workspace_path}')
            if file_paths:
                logger.info(f'[FilesystemManager.{workspace_name}] {context} - Files ({len(file_paths)}): {file_paths}')
            if dir_paths:
                logger.info(f'[FilesystemManager.{workspace_name}] {context} - Directories ({len(dir_paths)}): {dir_paths}')
            if not file_paths and (not dir_paths):
                logger.info(f'[FilesystemManager.{workspace_name}] {context} - Empty workspace')
        except Exception as e:
            logger.warning(f'[FilesystemManager.{workspace_name}] {context} - Error reading workspace: {e}')

    def log_current_state(self, context: str='') -> None:
        """
        Log the current state of both main and temp workspaces.

        Args:
            context: Context for the logging (e.g., "before execution", "after answer")
        """
        agent_context = f'agent_id={self.agent_id}, {context}' if context else f'agent_id={self.agent_id}'
        self._log_workspace_contents(self.get_current_workspace(), 'main_workspace', agent_context)
        if self.agent_temporary_workspace:
            self._log_workspace_contents(self.agent_temporary_workspace, 'temp_workspace', agent_context)

    def set_temporary_workspace(self, use_temporary: bool=True) -> None:
        """
        Switch between main workspace and temporary workspace.

        Args:
            use_temporary: If True, use temporary workspace; if False, use main workspace
        """
        self._using_temporary = use_temporary
        if use_temporary and self.agent_temporary_workspace:
            self.cwd = self.agent_temporary_workspace
        else:
            self.cwd = self._original_cwd

    def get_current_workspace(self) -> Path:
        """
        Get the current active workspace path.

        Returns:
            Path to the current workspace
        """
        return self.cwd

    def cleanup(self) -> None:
        """Cleanup temporary resources (not the main workspace) and Docker containers."""
        if self.docker_manager and self.agent_id:
            self.docker_manager.cleanup(self.agent_id)
        p = self.agent_temporary_workspace
        if not p:
            return
        try:
            p = p.resolve()
            if not p.exists():
                return
            assert p.is_absolute(), 'Temporary workspace must be absolute'
            assert p.is_dir(), 'Temporary workspace must be a directory'
            if self.agent_temporary_workspace_parent:
                parent = Path(self.agent_temporary_workspace_parent).resolve()
                try:
                    p.relative_to(parent)
                except ValueError:
                    raise AssertionError(f'Refusing to delete workspace outside of parent: {p}')
            if p == Path('/') or len(p.parts) < 3:
                raise AssertionError(f'Unsafe path for deletion: {p}')
            shutil.rmtree(p)
        except Exception as e:
            logger.warning(f'[FilesystemManager] cleanup failed for {p}: {e}')

def get_workspace_tools_mcp_config(self) -> Dict[str, Any]:
    """
        Generate workspace tools MCP server configuration.

        Returns:
            Dictionary with MCP server configuration for workspace tools (copy, delete, compare)
        """
    context_paths = self.path_permission_manager.get_context_paths()
    ','.join([cp['path'] for cp in context_paths])
    script_path = Path(wc_module.__file__).resolve()
    paths = self.path_permission_manager.get_mcp_filesystem_paths()
    env = {'FASTMCP_SHOW_CLI_BANNER': 'false'}
    config = {'name': 'workspace_tools', 'type': 'stdio', 'command': 'fastmcp', 'args': ['run', f'{script_path}:create_server'] + ['--', '--allowed-paths'] + paths, 'env': env, 'cwd': str(self.cwd)}
    if not self.enable_image_generation:
        config['exclude_tools'] = ['generate_and_store_image_with_input_images', 'generate_and_store_image_no_input_images']
    if not self.enable_audio_generation:
        if 'exclude_tools' not in config:
            config['exclude_tools'] = []
        config['exclude_tools'].extend(['generate_and_store_audio_with_input_audios', 'generate_and_store_audio_no_input_audios'])
    return config

def get_command_line_mcp_config(self) -> Dict[str, Any]:
    """
        Generate command line execution MCP server configuration.

        Returns:
            Dictionary with MCP server configuration for command execution
            (supports bash on Unix/Mac, cmd/PowerShell on Windows, and Docker isolation)
        """
    script_path = Path(ce_module.__file__).resolve()
    paths = self.path_permission_manager.get_mcp_filesystem_paths()
    env = {'FASTMCP_SHOW_CLI_BANNER': 'false'}
    if 'DOCKER_HOST' in os.environ:
        env['DOCKER_HOST'] = os.environ['DOCKER_HOST']
    config = {'name': 'command_line', 'type': 'stdio', 'command': 'fastmcp', 'args': ['run', f'{script_path}:create_server', '--', '--allowed-paths'] + paths, 'env': env, 'cwd': str(self.cwd)}
    config['args'].extend(['--execution-mode', self.command_line_execution_mode])
    if self.command_line_execution_mode == 'docker' and self.agent_id:
        config['args'].extend(['--agent-id', self.agent_id])
    if self.command_line_allowed_commands:
        config['args'].extend(['--allowed-commands'] + self.command_line_allowed_commands)
    if self.command_line_blocked_commands:
        config['args'].extend(['--blocked-commands'] + self.command_line_blocked_commands)
    return config

def cleanup(self) -> None:
    """Cleanup temporary resources (not the main workspace) and Docker containers."""
    if self.docker_manager and self.agent_id:
        self.docker_manager.cleanup(self.agent_id)
    p = self.agent_temporary_workspace
    if not p:
        return
    try:
        p = p.resolve()
        if not p.exists():
            return
        assert p.is_absolute(), 'Temporary workspace must be absolute'
        assert p.is_dir(), 'Temporary workspace must be a directory'
        if self.agent_temporary_workspace_parent:
            parent = Path(self.agent_temporary_workspace_parent).resolve()
            try:
                p.relative_to(parent)
            except ValueError:
                raise AssertionError(f'Refusing to delete workspace outside of parent: {p}')
        if p == Path('/') or len(p.parts) < 3:
            raise AssertionError(f'Unsafe path for deletion: {p}')
        shutil.rmtree(p)
    except Exception as e:
        logger.warning(f'[FilesystemManager] cleanup failed for {p}: {e}')

def get_copy_file_pairs(allowed_paths: List[Path], source_base_path: str, destination_base_path: str='', include_patterns: Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None) -> List[Tuple[Path, Path]]:
    """
    Get all source->destination file pairs that would be copied by copy_files_batch.

    This function can be imported by the filesystem manager for permission validation.

    Args:
        allowed_paths: List of allowed base paths for validation
        source_base_path: Base path to copy from
        destination_base_path: Base path in workspace to copy to
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude

    Returns:
        List of (source_path, destination_path) tuples

    Raises:
        ValueError: If paths are invalid
    """
    if include_patterns is None:
        include_patterns = ['*']
    if exclude_patterns is None:
        exclude_patterns = []
    source_base = Path(source_base_path).resolve()
    if not source_base.exists():
        raise ValueError(f'Source base path does not exist: {source_base}')
    _validate_path_access(source_base, allowed_paths)
    if destination_base_path:
        if Path(destination_base_path).is_absolute():
            dest_base = Path(destination_base_path).resolve()
        else:
            dest_base = (Path.cwd() / destination_base_path).resolve()
    else:
        raise ValueError('destination_base_path is required for copy_files_batch')
    _validate_path_access(dest_base, allowed_paths)
    file_pairs = []
    for item in source_base.rglob('*'):
        if not item.is_file():
            continue
        rel_path = item.relative_to(source_base)
        rel_path_str = str(rel_path)
        included = any((fnmatch.fnmatch(rel_path_str, pattern) for pattern in include_patterns))
        if not included:
            continue
        excluded = any((fnmatch.fnmatch(rel_path_str, pattern) for pattern in exclude_patterns))
        if excluded:
            continue
        dest_file = (dest_base / rel_path).resolve()
        _validate_path_access(dest_file, allowed_paths)
        file_pairs.append((item, dest_file))
    return file_pairs

def _is_critical_path(path: Path, allowed_paths: List[Path]=None) -> bool:
    """
    Check if a path is a critical system file that should not be deleted.

    Critical paths include:
    - .git directories (version control)
    - .env files (environment variables)
    - .massgen directories (MassGen metadata) - UNLESS within an allowed workspace
    - node_modules (package dependencies)
    - venv/.venv (Python virtual environments)
    - __pycache__ (Python cache)
    - massgen_logs (logging)

    Args:
        path: Path to check
        allowed_paths: List of allowed base paths (workspaces). If provided and path
                      is within an allowed path, only check for critical patterns
                      within that workspace (not in parent paths).

    Returns:
        True if path is critical and should not be deleted

    Examples:
        # Outside workspace - blocks any .massgen in path
        _is_critical_path(Path("/home/.massgen/config"))  → True (blocked)

        # Inside workspace - allows user files even if parent has .massgen
        workspace = Path("/home/.massgen/workspaces/workspace1")
        _is_critical_path(Path("/home/.massgen/workspaces/workspace1/user_dir"), [workspace])  → False (allowed)
        _is_critical_path(Path("/home/.massgen/workspaces/workspace1/.git"), [workspace])  → True (blocked)
    """
    CRITICAL_PATTERNS = ['.git', '.env', '.massgen', 'node_modules', '__pycache__', '.venv', 'venv', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'massgen_logs']
    resolved_path = path.resolve()
    if allowed_paths:
        for allowed_path in allowed_paths:
            try:
                rel_path = resolved_path.relative_to(allowed_path.resolve())
                for part in rel_path.parts:
                    if part in CRITICAL_PATTERNS:
                        return True
                if resolved_path.name in CRITICAL_PATTERNS:
                    return True
                return False
            except ValueError:
                continue
    parts = resolved_path.parts
    for part in parts:
        if part in CRITICAL_PATTERNS:
            return True
    if resolved_path.name in CRITICAL_PATTERNS:
        return True
    return False

def _is_text_file(path: Path) -> bool:
    """
    Check if a file is likely a text file (not binary).

    Uses simple heuristic: try to read as text and check for null bytes.

    TODO: Handle multi-modal files once implemented.

    Args:
        path: Path to check

    Returns:
        True if file appears to be text
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            chunk = f.read(8192)
            if '\x00' in chunk:
                return False
        return True
    except (UnicodeDecodeError, OSError):
        return False

def _is_permission_path_root(path: Path, allowed_paths: List[Path]) -> bool:
    """
    Check if a path is exactly one of the permission path roots.

    This prevents deletion of workspace directories, context path roots, etc.,
    while still allowing deletion of files and subdirectories within them.

    Args:
        path: Path to check
        allowed_paths: List of allowed base paths (permission path roots)

    Returns:
        True if path is exactly a permission path root

    Examples (Unix/macOS):
        allowed_paths = [Path("/workspace1"), Path("/context")]
        _is_permission_path_root(Path("/workspace1"))              → True  (blocked)
        _is_permission_path_root(Path("/workspace1/file.txt"))    → False (allowed)
        _is_permission_path_root(Path("/workspace1/subdir"))      → False (allowed)
        _is_permission_path_root(Path("/context"))                → True  (blocked)
        _is_permission_path_root(Path("/context/config.yaml"))    → False (allowed)

    Examples (Windows):
        allowed_paths = [Path("C:\\workspace1"), Path("D:\\context")]
        _is_permission_path_root(Path("C:\\workspace1"))           → True  (blocked)
        _is_permission_path_root(Path("C:\\workspace1\\file.txt")) → False (allowed)
        _is_permission_path_root(Path("D:\\context"))             → True  (blocked)
        _is_permission_path_root(Path("D:\\context\\data.json"))  → False (allowed)
    """
    resolved_path = path.resolve()
    for allowed_path in allowed_paths:
        if resolved_path == allowed_path.resolve():
            return True
    return False

def _validate_and_resolve_paths(allowed_paths: List[Path], source_path: str, destination_path: str) -> tuple[Path, Path]:
    """
    Validate source and destination paths for copy operations.

    Args:
        allowed_paths: List of allowed base paths for validation
        source_path: Source file/directory path
        destination_path: Destination path in workspace

    Returns:
        Tuple of (resolved_source, resolved_destination)

    Raises:
        ValueError: If paths are invalid
    """
    try:
        source = Path(source_path).resolve()
        if not source.exists():
            raise ValueError(f'Source path does not exist: {source}')
        _validate_path_access(source, allowed_paths)
        if Path(destination_path).is_absolute():
            destination = Path(destination_path).resolve()
        else:
            destination = (Path.cwd() / destination_path).resolve()
        _validate_path_access(destination, allowed_paths)
        return (source, destination)
    except Exception as e:
        raise ValueError(f'Path validation failed: {e}')

@mcp.tool()
def copy_files_batch(source_base_path: str, destination_base_path: str='', include_patterns: Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None, overwrite: bool=False) -> Dict[str, Any]:
    """
        Copy multiple files with pattern matching and exclusions.

        This advanced tool allows copying multiple files at once with glob-style patterns
        for inclusion and exclusion, useful for copying entire directory structures
        while filtering out unwanted files.

        Args:
            source_base_path: Base path to copy from (must be absolute path)
            destination_base_path: Base destination path - can be:
                - Relative path: Resolved relative to your workspace (e.g., "project/output")
                - Absolute path: Must be within allowed directories for security
                - Empty string: Copy to workspace root
            include_patterns: List of glob patterns for files to include (default: ["*"])
            exclude_patterns: List of glob patterns for files to exclude (default: [])
            overwrite: Whether to overwrite existing files (default: False)

        Returns:
            Dictionary with batch copy operation results
        """
    if include_patterns is None:
        include_patterns = ['*']
    if exclude_patterns is None:
        exclude_patterns = []
    try:
        copied_files = []
        skipped_files = []
        errors = []
        file_pairs = get_copy_file_pairs(mcp.allowed_paths, source_base_path, destination_base_path, include_patterns, exclude_patterns)
        for source_file, dest_file in file_pairs:
            rel_path_str = str(source_file.relative_to(Path(source_base_path).resolve()))
            try:
                if dest_file.exists() and (not overwrite):
                    skipped_files.append({'path': rel_path_str, 'reason': 'destination exists (overwrite=false)'})
                    continue
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)
                copied_files.append({'source': str(source_file), 'destination': str(dest_file), 'relative_path': rel_path_str, 'size': dest_file.stat().st_size})
            except Exception as e:
                errors.append({'path': rel_path_str, 'error': str(e)})
        return {'success': True, 'operation': 'copy_files_batch', 'summary': {'copied': len(copied_files), 'skipped': len(skipped_files), 'errors': len(errors)}, 'details': {'copied_files': copied_files, 'skipped_files': skipped_files, 'errors': errors}}
    except Exception as e:
        return {'success': False, 'operation': 'copy_files_batch', 'error': str(e)}

@mcp.tool()
def delete_files_batch(base_path: str, include_patterns: Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None) -> Dict[str, Any]:
    """
        Delete multiple files matching patterns.

        This advanced tool allows deleting multiple files at once with glob-style patterns
        for inclusion and exclusion, useful for cleaning up entire directory structures
        while preserving specific files.

        Args:
            base_path: Base directory to search in - can be:
                - Relative path: Resolved relative to your workspace (e.g., "build")
                - Absolute path: Must be within allowed directories for security
            include_patterns: List of glob patterns for files to include (default: ["*"])
            exclude_patterns: List of glob patterns for files to exclude (default: [])

        Returns:
            Dictionary with batch deletion results including:
            - deleted: List of deleted files
            - skipped: List of skipped files (read-only or system files)
            - errors: List of errors encountered

        Security:
            - Requires WRITE permission on each file
            - Must be within allowed directories
            - System files (.git, .env, etc.) cannot be deleted
        """
    if include_patterns is None:
        include_patterns = ['*']
    if exclude_patterns is None:
        exclude_patterns = []
    try:
        deleted_files = []
        skipped_files = []
        errors = []
        if Path(base_path).is_absolute():
            base = Path(base_path).resolve()
        else:
            base = (Path.cwd() / base_path).resolve()
        if not base.exists():
            return {'success': False, 'operation': 'delete_files_batch', 'error': f'Base path does not exist: {base}'}
        _validate_path_access(base, mcp.allowed_paths)
        for item in base.rglob('*'):
            if not item.is_file():
                continue
            rel_path = item.relative_to(base)
            rel_path_str = str(rel_path)
            included = any((fnmatch.fnmatch(rel_path_str, pattern) for pattern in include_patterns))
            if not included:
                continue
            excluded = any((fnmatch.fnmatch(rel_path_str, pattern) for pattern in exclude_patterns))
            if excluded:
                continue
            try:
                if _is_critical_path(item, mcp.allowed_paths):
                    skipped_files.append({'path': rel_path_str, 'reason': 'system file (protected)'})
                    continue
                if _is_permission_path_root(item, mcp.allowed_paths):
                    skipped_files.append({'path': rel_path_str, 'reason': 'permission path root (protected)'})
                    continue
                _validate_path_access(item, mcp.allowed_paths)
                size = item.stat().st_size
                item.unlink()
                deleted_files.append({'path': str(item), 'relative_path': rel_path_str, 'size': size})
            except Exception as e:
                errors.append({'path': rel_path_str, 'error': str(e)})
        return {'success': True, 'operation': 'delete_files_batch', 'summary': {'deleted': len(deleted_files), 'skipped': len(skipped_files), 'errors': len(errors)}, 'details': {'deleted_files': deleted_files, 'skipped_files': skipped_files, 'errors': errors}}
    except Exception as e:
        return {'success': False, 'operation': 'delete_files_batch', 'error': str(e)}

@mcp.tool()
def compare_directories(dir1: str, dir2: str, show_content_diff: bool=False) -> Dict[str, Any]:
    """
        Compare two directories and show differences.

        This tool helps understand what changed between two workspaces or directory states,
        making it easier to review changes before deployment or understand agent modifications.

        Args:
            dir1: First directory path (absolute or relative to workspace)
            dir2: Second directory path (absolute or relative to workspace)
            show_content_diff: Whether to include unified diffs of different files (default: False)

        Returns:
            Dictionary with comparison results:
            - only_in_dir1: Files only in first directory
            - only_in_dir2: Files only in second directory
            - different: Files that exist in both but have different content
            - identical: Files that are identical
            - content_diffs: Optional unified diffs (if show_content_diff=True)

        Security:
            - Read-only operation, never modifies files
            - Both paths must be within allowed directories
        """
    try:
        path1 = Path(dir1).resolve() if Path(dir1).is_absolute() else (Path.cwd() / dir1).resolve()
        path2 = Path(dir2).resolve() if Path(dir2).is_absolute() else (Path.cwd() / dir2).resolve()
        _validate_path_access(path1, mcp.allowed_paths)
        _validate_path_access(path2, mcp.allowed_paths)
        if not path1.exists() or not path1.is_dir():
            return {'success': False, 'operation': 'compare_directories', 'error': f'First path is not a directory: {path1}'}
        if not path2.exists() or not path2.is_dir():
            return {'success': False, 'operation': 'compare_directories', 'error': f'Second path is not a directory: {path2}'}
        dcmp = filecmp.dircmp(str(path1), str(path2))
        result = {'success': True, 'operation': 'compare_directories', 'details': {'only_in_dir1': list(dcmp.left_only), 'only_in_dir2': list(dcmp.right_only), 'different': list(dcmp.diff_files), 'identical': list(dcmp.same_files)}}
        if show_content_diff and dcmp.diff_files:
            content_diffs = {}
            for filename in dcmp.diff_files:
                file1 = path1 / filename
                file2 = path2 / filename
                try:
                    if _is_text_file(file1) and _is_text_file(file2):
                        with open(file1) as f1, open(file2) as f2:
                            lines1 = f1.readlines()
                            lines2 = f2.readlines()
                        diff = list(difflib.unified_diff(lines1, lines2, fromfile=f'dir1/{filename}', tofile=f'dir2/{filename}', lineterm=''))
                        content_diffs[filename] = '\n'.join(diff[:100])
                except Exception as e:
                    content_diffs[filename] = f'Error generating diff: {e}'
            result['details']['content_diffs'] = content_diffs
        return result
    except Exception as e:
        return {'success': False, 'operation': 'compare_directories', 'error': str(e)}

@mcp.tool()
def compare_files(file1: str, file2: str, context_lines: int=3) -> Dict[str, Any]:
    """
        Compare two text files and show unified diff.

        This tool provides detailed line-by-line comparison of two files,
        making it easy to see exactly what changed between versions.

        Args:
            file1: First file path (absolute or relative to workspace)
            file2: Second file path (absolute or relative to workspace)
            context_lines: Number of context lines around changes (default: 3)

        Returns:
            Dictionary with comparison results:
            - identical: Boolean indicating if files are identical
            - diff: Unified diff output
            - stats: Statistics (lines added/removed/changed)

        Security:
            - Read-only operation, never modifies files
            - Both paths must be within allowed directories
            - Works best with text files
        """
    try:
        path1 = Path(file1).resolve() if Path(file1).is_absolute() else (Path.cwd() / file1).resolve()
        path2 = Path(file2).resolve() if Path(file2).is_absolute() else (Path.cwd() / file2).resolve()
        _validate_path_access(path1, mcp.allowed_paths)
        _validate_path_access(path2, mcp.allowed_paths)
        if not path1.exists() or not path1.is_file():
            return {'success': False, 'operation': 'compare_files', 'error': f'First path is not a file: {path1}'}
        if not path2.exists() or not path2.is_file():
            return {'success': False, 'operation': 'compare_files', 'error': f'Second path is not a file: {path2}'}
        try:
            with open(path1) as f1:
                lines1 = f1.readlines()
            with open(path2) as f2:
                lines2 = f2.readlines()
        except UnicodeDecodeError:
            return {'success': False, 'operation': 'compare_files', 'error': 'Files appear to be binary, not text'}
        diff = list(difflib.unified_diff(lines1, lines2, fromfile=str(path1), tofile=str(path2), lineterm='', n=context_lines))
        added = sum((1 for line in diff if line.startswith('+') and (not line.startswith('+++'))))
        removed = sum((1 for line in diff if line.startswith('-') and (not line.startswith('---'))))
        return {'success': True, 'operation': 'compare_files', 'details': {'identical': len(diff) == 0, 'diff': '\n'.join(diff[:500]), 'stats': {'added': added, 'removed': removed, 'changed': min(added, removed)}}}
    except Exception as e:
        return {'success': False, 'operation': 'compare_files', 'error': str(e)}

@mcp.tool()
def generate_and_store_image_with_input_images(base_image_paths: List[str], prompt: str='Create a variation of the provided images', model: str='gpt-4.1', n: int=1, storage_path: Optional[str]=None) -> Dict[str, Any]:
    """
        Create variations based on multiple input images using OpenAI's gpt-4.1 API.

        This tool generates image variations based on multiple base images using OpenAI's gpt-4.1 API
        and saves them to the workspace with automatic organization.

        Args:
            base_image_paths: List of paths to base images (PNG/JPEG files, less than 4MB)
                        - Relative path: Resolved relative to workspace
                        - Absolute path: Must be within allowed directories
            prompt: Text description for the variation (default: "Create a variation of the provided images")
            model: Model to use (default: "gpt-4.1")
            n: Number of variations to generate (default: 1)
            storage_path: Directory path where to save variations (optional)
                         - Relative path: Resolved relative to workspace
                         - Absolute path: Must be within allowed directories
                         - None/empty: Saves to workspace root

        Returns:
            Dictionary containing:
            - success: Whether operation succeeded
            - operation: "generate_and_store_image_with_input_images"
            - note: Note about usage
            - images: List of generated images with file paths and metadata
            - model: Model used for generation
            - prompt: The prompt used
            - total_images: Total number of images generated

        Examples:
            generate_and_store_image_with_input_images(["cat.png", "dog.png"], "Combine these animals")
            → Generates a variation combining both images

            generate_and_store_image_with_input_images(["art/logo.png", "art/icon.png"], "Create a unified design")
            → Generates variations based on both images

        Security:
            - Requires valid OpenAI API key
            - Input images must be valid image files less than 4MB
            - Files are saved to specified path within workspace
        """
    from datetime import datetime
    try:
        script_dir = Path(__file__).parent.parent.parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'}
        client = OpenAI(api_key=openai_api_key)
        content = [{'type': 'input_text', 'text': prompt}]
        validated_paths = []
        for image_path_str in base_image_paths:
            if Path(image_path_str).is_absolute():
                image_path = Path(image_path_str).resolve()
            else:
                image_path = (Path.cwd() / image_path_str).resolve()
            _validate_path_access(image_path, mcp.allowed_paths)
            if not image_path.exists():
                return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': f'Image file does not exist: {image_path}'}
            if image_path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
                return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': f'Image must be PNG or JPEG format: {image_path}'}
            file_size = image_path.stat().st_size
            if file_size > 4 * 1024 * 1024:
                return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': f'Image file too large (must be < 4MB): {image_path} is {file_size / (1024 * 1024):.2f}MB'}
            validated_paths.append(image_path)
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            mime_type = 'image/jpeg' if image_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png'
            content.append({'type': 'input_image', 'image_url': f'data:{mime_type};base64,{image_base64}'})
        if storage_path:
            if Path(storage_path).is_absolute():
                storage_dir = Path(storage_path).resolve()
            else:
                storage_dir = (Path.cwd() / storage_path).resolve()
        else:
            storage_dir = Path.cwd()
        _validate_path_access(storage_dir, mcp.allowed_paths)
        storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            response = client.responses.create(model=model, input=[{'role': 'user', 'content': content}], tools=[{'type': 'image_generation'}])
            image_generation_calls = [output for output in response.output if output.type == 'image_generation_call']
            all_variations = []
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            for idx, output in enumerate(image_generation_calls):
                if hasattr(output, 'result'):
                    image_base64 = output.result
                    image_bytes = base64.b64decode(image_base64)
                    if len(image_generation_calls) > 1:
                        filename = f'variation_{idx + 1}_{timestamp}.png'
                    else:
                        filename = f'variation_{timestamp}.png'
                    file_path = storage_dir / filename
                    file_path.write_bytes(image_bytes)
                    all_variations.append({'source_images': [str(p) for p in validated_paths], 'file_path': str(file_path), 'filename': filename, 'size': len(image_bytes), 'index': idx})
            if not all_variations:
                text_outputs = [output.content for output in response.output if hasattr(output, 'content')]
                if text_outputs:
                    return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': f'No images generated. Response: {' '.join(text_outputs)}'}
        except Exception as api_error:
            return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': f'OpenAI API error: {str(api_error)}'}
        return {'success': True, 'operation': 'generate_and_store_image_with_input_images', 'note': 'If no input images were provided, you must use generate_and_store_image_no_input_images tool.', 'images': all_variations, 'model': model, 'prompt': prompt, 'total_images': len(all_variations)}
    except Exception as e:
        return {'success': False, 'operation': 'generate_and_store_image_with_input_images', 'error': f'Failed to generate variations: {str(e)}'}

@mcp.tool()
def generate_and_store_audio_no_input_audios(prompt: str, model: str='gpt-4o-audio-preview', voice: str='alloy', audio_format: str='wav', storage_path: Optional[str]=None) -> Dict[str, Any]:
    """
        Generate audio from text using OpenAI's gpt-4o-audio-preview model and store it in the workspace.

        This tool generates audio speech from text prompts using OpenAI's audio generation API
        and saves the audio files to the workspace with automatic organization.

        Args:
            prompt: Text content to convert to audio speech
            model: Model to use for generation (default: "gpt-4o-audio-preview")
            voice: Voice to use for audio generation (default: "alloy")
                   Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
            audio_format: Audio format for output (default: "wav")
                         Options: "wav", "mp3", "opus", "aac", "flac"
            storage_path: Directory path where to save the audio (optional)
                         - Relative path: Resolved relative to workspace (e.g., "audio/generated")
                         - Absolute path: Must be within allowed directories
                         - None/empty: Saves to workspace root

        Returns:
            Dictionary containing:
            - success: Whether operation succeeded
            - operation: "generate_and_store_audio_no_input_audios"
            - audio_file: Generated audio file with path and metadata
            - model: Model used for generation
            - prompt: The prompt used for generation
            - voice: Voice used for generation
            - format: Audio format used

        Examples:
            generate_and_store_audio_no_input_audios("Is a golden retriever a good family dog?")
            → Generates and saves to: 20240115_143022_audio.wav

            generate_and_store_audio_no_input_audios("Hello world", voice="nova", audio_format="mp3")
            → Generates with nova voice and saves as: 20240115_143022_audio.mp3

        Security:
            - Requires valid OpenAI API key (automatically detected from .env or environment)
            - Files are saved to specified path within workspace
            - Path must be within allowed directories
        """
    from datetime import datetime
    try:
        script_dir = Path(__file__).parent.parent.parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {'success': False, 'operation': 'generate_and_store_audio_no_input_audios', 'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'}
        client = OpenAI(api_key=openai_api_key)
        if storage_path:
            if Path(storage_path).is_absolute():
                storage_dir = Path(storage_path).resolve()
            else:
                storage_dir = (Path.cwd() / storage_path).resolve()
        else:
            storage_dir = Path.cwd()
        _validate_path_access(storage_dir, mcp.allowed_paths)
        storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            completion = client.chat.completions.create(model=model, modalities=['text', 'audio'], audio={'voice': voice, 'format': audio_format}, messages=[{'role': 'user', 'content': prompt}])
            if not completion.choices[0].message.audio or not completion.choices[0].message.audio.data:
                return {'success': False, 'operation': 'generate_and_store_audio_no_input_audios', 'error': 'No audio data received from API'}
            audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_prompt = ''.join((c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_'))).strip()
            clean_prompt = clean_prompt.replace(' ', '_')
            filename = f'{timestamp}_{clean_prompt}.{audio_format}'
            file_path = storage_dir / filename
            file_path.write_bytes(audio_bytes)
            file_size = len(audio_bytes)
            text_response = completion.choices[0].message.content if completion.choices[0].message.content else None
            return {'success': True, 'operation': 'generate_and_store_audio_no_input_audios', 'audio_file': {'file_path': str(file_path), 'filename': filename, 'size': file_size, 'format': audio_format}, 'model': model, 'prompt': prompt, 'voice': voice, 'format': audio_format, 'text_response': text_response}
        except Exception as api_error:
            return {'success': False, 'operation': 'generate_and_store_audio_no_input_audios', 'error': f'OpenAI API error: {str(api_error)}'}
    except Exception as e:
        return {'success': False, 'operation': 'generate_and_store_audio_no_input_audios', 'error': f'Failed to generate or save audio: {str(e)}'}

@mcp.tool()
def generate_and_store_image_no_input_images(prompt: str, model: str='gpt-4.1', storage_path: Optional[str]=None) -> Dict[str, Any]:
    """
        Generate image using OpenAI's response with gpt-4.1 **WITHOUT ANY INPUT IMAGES** and store it in the workspace.

        This tool Generate image using OpenAI's response with gpt-4.1 **WITHOUT ANY INPUT IMAGES** and store it in the workspace.

        Args:
            prompt: Text description of the image to generate
            model: Model to use for generation (default: "gpt-4.1")
                   Options: "gpt-4.1"
            n: Number of images to generate (default: 1)
               - gpt-4.1: only 1
            storage_path: Directory path where to save the image (optional)
                         - Relative path: Resolved relative to workspace (e.g., "images/generated")
                         - Absolute path: Must be within allowed directories
                         - None/empty: Saves to workspace root

        Returns:
            Dictionary containing:
            - success: Whether operation succeeded
            - operation: "generate_and_store_image_no_input_images"
            - note: Note about operation
            - images: List of generated images with file paths and metadata
            - model: Model used for generation
            - prompt: The prompt used for generation
            - total_images: Total number of images generated and saved
            - images: List of generated images with file paths and metadata

        Examples:
            generate_and_store_image_no_input_images("a cat in space")
            → Generates and saves to: 20240115_143022_a_cat_in_space.png

            generate_and_store_image_no_input_images("sunset over mountains", storage_path="art/landscapes")
            → Generates and saves to: art/landscapes/20240115_143022_sunset_over_mountains.png

        Security:
            - Requires valid OpenAI API key (automatically detected from .env or environment)
            - Files are saved to specified path within workspace
            - Path must be within allowed directories

        Note:
            API key is automatically detected in this order:
            1. First checks .env file in current directory or parent directories
            2. Then checks environment variables
        """
    from datetime import datetime
    try:
        script_dir = Path(__file__).parent.parent.parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {'success': False, 'operation': 'generate_and_store_image', 'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'}
        client = OpenAI(api_key=openai_api_key)
        if storage_path:
            if Path(storage_path).is_absolute():
                storage_dir = Path(storage_path).resolve()
            else:
                storage_dir = (Path.cwd() / storage_path).resolve()
        else:
            storage_dir = Path.cwd()
        _validate_path_access(storage_dir, mcp.allowed_paths)
        storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            response = client.responses.create(model=model, input=prompt, tools=[{'type': 'image_generation'}])
            image_data = [output.result for output in response.output if output.type == 'image_generation_call']
            saved_images = []
            if image_data:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                clean_prompt = ''.join((c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_'))).strip()
                clean_prompt = clean_prompt.replace(' ', '_')
                for idx, image_base64 in enumerate(image_data):
                    image_bytes = base64.b64decode(image_base64)
                    if len(image_data) > 1:
                        filename = f'{timestamp}_{clean_prompt}_{idx + 1}.png'
                    else:
                        filename = f'{timestamp}_{clean_prompt}.png'
                    file_path = storage_dir / filename
                    file_path.write_bytes(image_bytes)
                    file_size = len(image_bytes)
                    saved_images.append({'file_path': str(file_path), 'filename': filename, 'size': file_size, 'index': idx})
            result = {'success': True, 'operation': 'generate_and_store_image_no_input_images', 'note': 'New images are generated and saved to the specified path.', 'images': saved_images, 'model': model, 'prompt': prompt, 'total_images': len(saved_images)}
            return result
        except Exception as api_error:
            print(f'OpenAI API error: {str(api_error)}')
            return {'success': False, 'operation': 'generate_and_store_image_no_input_images', 'error': f'OpenAI API error: {str(api_error)}'}
    except Exception as e:
        return {'success': False, 'operation': 'generate_and_store_image_no_input_images', 'error': f'Failed to generate or save image: {str(e)}'}

@mcp.tool()
def generate_text_with_input_audio(audio_paths: List[str], model: str='gpt-4o-transcribe') -> Dict[str, Any]:
    """
        Transcribe audio file(s) to text using OpenAI's Transcription API.

        This tool processes one or more audio files through OpenAI's Transcription API
        to extract the text content from the audio. Each file is processed separately.

        Args:
            audio_paths: List of paths to input audio files (WAV, MP3, M4A, etc.)
                        - Relative path: Resolved relative to workspace
                        - Absolute path: Must be within allowed directories
            model: Model to use (default: "gpt-4o-transcribe")

        Returns:
            Dictionary containing:
            - success: Whether operation succeeded
            - operation: "generate_text_with_input_audio"
            - transcriptions: List of transcription results for each file
            - audio_files: List of paths to the input audio files
            - model: Model used

        Examples:
            generate_text_with_input_audio(["recording.wav"])
            → Returns transcription for recording.wav

            generate_text_with_input_audio(["interview1.mp3", "interview2.mp3"])
            → Returns separate transcriptions for each file

        Security:
            - Requires valid OpenAI API key
            - All input audio files must exist and be readable
        """
    try:
        script_dir = Path(__file__).parent.parent.parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {'success': False, 'operation': 'generate_text_with_input_audio', 'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'}
        client = OpenAI(api_key=openai_api_key)
        validated_audio_paths = []
        audio_extensions = ['.wav', '.mp3', '.m4a', '.mp4', '.ogg', '.flac', '.aac', '.wma', '.opus']
        for audio_path_str in audio_paths:
            if Path(audio_path_str).is_absolute():
                audio_path = Path(audio_path_str).resolve()
            else:
                audio_path = (Path.cwd() / audio_path_str).resolve()
            _validate_path_access(audio_path, mcp.allowed_paths)
            if not audio_path.exists():
                return {'success': False, 'operation': 'generate_text_with_input_audio', 'error': f'Audio file does not exist: {audio_path}'}
            if audio_path.suffix.lower() not in audio_extensions:
                return {'success': False, 'operation': 'generate_text_with_input_audio', 'error': f'File does not appear to be an audio file: {audio_path}'}
            validated_audio_paths.append(audio_path)
        transcriptions = []
        for audio_path in validated_audio_paths:
            try:
                with open(audio_path, 'rb') as audio_file:
                    transcription = client.audio.transcriptions.create(model=model, file=audio_file, response_format='text')
                transcriptions.append({'file': str(audio_path), 'transcription': transcription})
            except Exception as api_error:
                return {'success': False, 'operation': 'generate_text_with_input_audio', 'error': f'Transcription API error for file {audio_path}: {str(api_error)}'}
        return {'success': True, 'operation': 'generate_text_with_input_audio', 'transcriptions': transcriptions, 'audio_files': [str(p) for p in validated_audio_paths], 'model': model}
    except Exception as e:
        return {'success': False, 'operation': 'generate_text_with_input_audio', 'error': f'Failed to transcribe audio: {str(e)}'}

@mcp.tool()
def convert_text_to_speech(input_text: str, model: str='gpt-4o-mini-tts', voice: str='alloy', instructions: Optional[str]=None, storage_path: Optional[str]=None, audio_format: str='mp3') -> Dict[str, Any]:
    """
        Convert text (transcription) directly to speech using OpenAI's TTS API with streaming response.

        This tool converts text directly to speech audio using OpenAI's Text-to-Speech API,
        designed specifically for converting transcriptions or any text content to spoken audio.
        Uses streaming response for efficient file handling.

        Args:
            input_text: The text content to convert to speech (e.g., transcription text)
            model: TTS model to use (default: "gpt-4o-mini-tts")
                   Options: "gpt-4o-mini-tts", "tts-1", "tts-1-hd"
            voice: Voice to use for speech synthesis (default: "alloy")
                   Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer", "coral", "sage"
            instructions: Optional speaking instructions for tone and style (e.g., "Speak in a cheerful tone")
            storage_path: Directory path where to save the audio file (optional)
                         - Relative path: Resolved relative to workspace
                         - Absolute path: Must be within allowed directories
                         - None/empty: Saves to workspace root
            audio_format: Output audio format (default: "mp3")
                         Options: "mp3", "opus", "aac", "flac", "wav", "pcm"

        Returns:
            Dictionary containing:
            - success: Whether operation succeeded
            - operation: "convert_text_to_speech"
            - audio_file: Generated audio file with path and metadata
            - model: TTS model used
            - voice: Voice used
            - format: Audio format used
            - text_length: Length of input text
            - instructions: Speaking instructions if provided

        Examples:
            convert_text_to_speech("Hello world, this is a test.")
            → Converts text to speech and saves as MP3

            convert_text_to_speech(
                "Today is a wonderful day to build something people love!",
                voice="coral",
                instructions="Speak in a cheerful and positive tone."
            )
            → Converts with specific voice and speaking instructions

        Security:
            - Requires valid OpenAI API key
            - Files are saved to specified path within workspace
            - Path must be within allowed directories
        """
    from datetime import datetime
    try:
        script_dir = Path(__file__).parent.parent.parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {'success': False, 'operation': 'convert_text_to_speech', 'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'}
        client = OpenAI(api_key=openai_api_key)
        if storage_path:
            if Path(storage_path).is_absolute():
                storage_dir = Path(storage_path).resolve()
            else:
                storage_dir = (Path.cwd() / storage_path).resolve()
        else:
            storage_dir = Path.cwd()
        _validate_path_access(storage_dir, mcp.allowed_paths)
        storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        clean_text = ''.join((c for c in input_text[:30] if c.isalnum() or c in (' ', '-', '_'))).strip()
        clean_text = clean_text.replace(' ', '_')
        filename = f'speech_{timestamp}_{clean_text}.{audio_format}'
        file_path = storage_dir / filename
        try:
            request_params = {'model': model, 'voice': voice, 'input': input_text}
            if instructions and model in ['gpt-4o-mini-tts']:
                request_params['instructions'] = instructions
            with client.audio.speech.with_streaming_response.create(**request_params) as response:
                response.stream_to_file(file_path)
            file_size = file_path.stat().st_size
            return {'success': True, 'operation': 'convert_text_to_speech', 'audio_file': {'file_path': str(file_path), 'filename': filename, 'size': file_size, 'format': audio_format}, 'model': model, 'voice': voice, 'format': audio_format, 'text_length': len(input_text), 'instructions': instructions if instructions else None}
        except Exception as api_error:
            return {'success': False, 'operation': 'convert_text_to_speech', 'error': f'OpenAI TTS API error: {str(api_error)}'}
    except Exception as e:
        return {'success': False, 'operation': 'convert_text_to_speech', 'error': f'Failed to convert text to speech: {str(e)}'}

@mcp.tool()
def generate_and_store_video_no_input_images(prompt: str, model: str='sora-2', seconds: int=4, storage_path: Optional[str]=None) -> Dict[str, Any]:
    """
        Generate a video from a text prompt using OpenAI's Sora-2 API.

        This tool generates a video based on a text prompt using OpenAI's Sora-2 API
        and saves it to the workspace with automatic organization.

        Args:
            prompt: Text description for the video to generate
            model: Model to use (default: "sora-2")
            storage_path: Directory path where to save the video (optional)
                         - Relative path: Resolved relative to workspace
                         - Absolute path: Must be within allowed directories
                         - None/empty: Saves to workspace root

        Returns:
            Dictionary containing:
            - success: Whether operation succeeded
            - operation: "generate_and_store_video_no_input_images"
            - video_path: Path to the saved video file
            - model: Model used for generation
            - prompt: The prompt used
            - duration: Time taken for generation in seconds

        Examples:
            generate_and_store_video_no_input_images("A cool cat on a motorcycle in the night")
            → Generates a video and saves to workspace root

            generate_and_store_video_no_input_images("Dancing robot", storage_path="videos/")
            → Generates a video and saves to videos/ directory

        Security:
            - Requires valid OpenAI API key with Sora-2 access
            - Files are saved to specified path within workspace
        """
    import time
    from datetime import datetime
    try:
        script_dir = Path(__file__).parent.parent.parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {'success': False, 'operation': 'generate_and_store_video_no_input_images', 'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'}
        client = OpenAI(api_key=openai_api_key)
        if storage_path:
            if Path(storage_path).is_absolute():
                storage_dir = Path(storage_path).resolve()
            else:
                storage_dir = (Path.cwd() / storage_path).resolve()
        else:
            storage_dir = Path.cwd()
        _validate_path_access(storage_dir, mcp.allowed_paths)
        storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            start_time = time.time()
            video = client.videos.create(model=model, prompt=prompt, seconds=str(seconds))
            getattr(video, 'progress', 0)
            while video.status in ('in_progress', 'queued'):
                video = client.videos.retrieve(video.id)
                getattr(video, 'progress', 0)
                time.sleep(2)
            if video.status == 'failed':
                message = getattr(getattr(video, 'error', None), 'message', 'Video generation failed')
                return {'success': False, 'operation': 'generate_and_store_video_no_input_images', 'error': message}
            content = client.videos.download_content(video.id, variant='video')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_prompt = ''.join((c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_'))).strip()
            clean_prompt = clean_prompt.replace(' ', '_')
            filename = f'{timestamp}_{clean_prompt}.mp4'
            file_path = storage_dir / filename
            content.write_to_file(str(file_path))
            duration = time.time() - start_time
            file_size = file_path.stat().st_size
            return {'success': True, 'operation': 'generate_and_store_video_no_input_images', 'video_path': str(file_path), 'filename': filename, 'size': file_size, 'model': model, 'prompt': prompt, 'duration': duration}
        except Exception as api_error:
            return {'success': False, 'operation': 'generate_and_store_video_no_input_images', 'error': f'OpenAI API error: {str(api_error)}'}
    except Exception as e:
        return {'success': False, 'operation': 'generate_and_store_video_no_input_images', 'error': f'Failed to generate or save video: {str(e)}'}

@dataclass
class ManagedPath:
    """Represents any managed path with its permissions and type."""
    path: Path
    permission: Permission
    path_type: str
    will_be_writable: bool = False
    is_file: bool = False
    protected_paths: List[Path] = None

    def __post_init__(self):
        """Initialize protected_paths as empty list if None."""
        if self.protected_paths is None:
            self.protected_paths = []

    def contains(self, check_path: Path) -> bool:
        """Check if this managed path contains the given path."""
        if self.is_file:
            return check_path.resolve() == self.path.resolve()
        try:
            check_path.resolve().relative_to(self.path.resolve())
            return True
        except ValueError:
            return False

    def is_protected(self, check_path: Path) -> bool:
        """Check if a path is in the protected paths list (immune from modification/deletion)."""
        if not self.protected_paths:
            return False
        resolved_check = check_path.resolve()
        for protected in self.protected_paths:
            resolved_protected = protected.resolve()
            if resolved_check == resolved_protected:
                return True
            try:
                resolved_check.relative_to(resolved_protected)
                return True
            except ValueError:
                continue
        return False

def contains(self, check_path: Path) -> bool:
    """Check if this managed path contains the given path."""
    if self.is_file:
        return check_path.resolve() == self.path.resolve()
    try:
        check_path.resolve().relative_to(self.path.resolve())
        return True
    except ValueError:
        return False

def is_protected(self, check_path: Path) -> bool:
    """Check if a path is in the protected paths list (immune from modification/deletion)."""
    if not self.protected_paths:
        return False
    resolved_check = check_path.resolve()
    for protected in self.protected_paths:
        resolved_protected = protected.resolve()
        if resolved_check == resolved_protected:
            return True
        try:
            resolved_check.relative_to(resolved_protected)
            return True
        except ValueError:
            continue
    return False

class PathPermissionManager:
    """
    Manages all filesystem paths and implements PreToolUse hook functionality similar to Claude Code,
    allowing us to intercept and validate tool calls based on some predefined rules (here, permissions).

    This manager handles all types of paths with unified permission control:
    - Workspace paths (typically write)
    - Temporary workspace paths (typically read-only)
    - Context paths (user-specified permissions)
    - Tool call validation (PreToolUse hook)
    - Path access control
    """
    DEFAULT_EXCLUDED_PATTERNS = ['.massgen', '.env', '.git', 'node_modules', '__pycache__', '.venv', 'venv', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.DS_Store', 'massgen_logs']

    def __init__(self, context_write_access_enabled: bool=False, enforce_read_before_delete: bool=True):
        """
        Initialize path permission manager.

        Args:
            context_write_access_enabled: Whether write access is enabled for context paths (workspace paths always
                have write access). If False, we change all context paths to read-only. Can be later updated with
                set_context_write_access_enabled(), in which case all existing context paths will be updated
                accordingly so that those that were "write" in YAML become writable again.
            enforce_read_before_delete: Whether to enforce read-before-delete policy for workspace files
        """
        self.managed_paths: List[ManagedPath] = []
        self.context_write_access_enabled = context_write_access_enabled
        self._permission_cache: Dict[Path, Permission] = {}
        self.file_operation_tracker = FileOperationTracker(enforce_read_before_delete=enforce_read_before_delete)
        logger.info(f'[PathPermissionManager] Initialized with context_write_access_enabled={context_write_access_enabled}, enforce_read_before_delete={enforce_read_before_delete}')

    def add_path(self, path: Path, permission: Permission, path_type: str) -> None:
        """
        Add a managed path.

        Args:
            path: Path to manage
            permission: Permission level for this path
            path_type: Type of path ("workspace", "temp_workspace", "context", etc.)
        """
        if not path.exists():
            if path_type == 'context':
                logger.warning(f'[PathPermissionManager] Context path does not exist: {path}')
                return
            else:
                logger.debug(f'[PathPermissionManager] Path will be created later: {path} ({path_type})')
        managed_path = ManagedPath(path=path.resolve(), permission=permission, path_type=path_type)
        self.managed_paths.append(managed_path)
        self._permission_cache.clear()
        logger.info(f'[PathPermissionManager] Added {path_type} path: {path} ({permission.value})')

    def get_context_paths(self) -> List[Dict[str, str]]:
        """
        Get context paths in configuration format for system prompts.

        Returns:
            List of context path dictionaries with path, permission, and will_be_writable flag
        """
        context_paths = []
        for mp in self.managed_paths:
            if mp.path_type == 'context':
                context_paths.append({'path': str(mp.path), 'permission': mp.permission.value, 'will_be_writable': mp.will_be_writable})
        return context_paths

    def set_context_write_access_enabled(self, enabled: bool) -> None:
        """
        Update write access setting for context paths and recalculate their permissions.
        Note: Workspace paths always have write access regardless of this setting.

        Args:
            enabled: Whether to enable write access for context paths
        """
        if self.context_write_access_enabled == enabled:
            return
        logger.info(f'[PathPermissionManager] Setting context_write_access_enabled to {enabled}')
        logger.info(f'[PathPermissionManager] Before update: self.managed_paths={self.managed_paths!r}')
        self.context_write_access_enabled = enabled
        for mp in self.managed_paths:
            if mp.path_type == 'context' and mp.will_be_writable:
                if enabled:
                    mp.permission = Permission.WRITE
                    logger.debug(f'[PathPermissionManager] Enabled write access for {mp.path}')
                else:
                    mp.permission = Permission.READ
                    logger.debug(f'[PathPermissionManager] Keeping read-only for {mp.path}')
        logger.info(f'[PathPermissionManager] Updated context path permissions based on context_write_access_enabled={enabled}, now is self.managed_paths={self.managed_paths!r}')
        self._permission_cache.clear()

    def add_context_paths(self, context_paths: List[Dict[str, Any]]) -> None:
        """
        Add context paths from configuration.

        Now supports both files and directories as context paths, with optional protected paths.

        Args:
            context_paths: List of context path configurations
                Format: [
                    {
                        "path": "C:/project/src",
                        "permission": "write",
                        "protected_paths": ["tests/do-not-touch/", "config.yaml"]  # Optional
                    },
                    {"path": "C:/project/logo.png", "permission": "read"}
                ]

        Note: During coordination, all context paths are read-only regardless of YAML settings.
              Only the final agent with context_write_access_enabled=True can write to paths marked as "write".
              Protected paths are ALWAYS read-only and immune from deletion, even if parent has write permission.
        """
        for config in context_paths:
            path_str = config.get('path', '')
            permission_str = config.get('permission', 'read')
            protected_paths_config = config.get('protected_paths', [])
            if not path_str:
                continue
            path = Path(path_str)
            if not path.exists():
                logger.warning(f'[PathPermissionManager] Context path does not exist: {path}')
                continue
            is_file = path.is_file()
            protected_paths = []
            for protected_str in protected_paths_config:
                protected_path = Path(protected_str)
                if not protected_path.is_absolute():
                    if is_file:
                        protected_path = (path.parent / protected_str).resolve()
                    else:
                        protected_path = (path / protected_str).resolve()
                else:
                    protected_path = protected_path.resolve()
                try:
                    if is_file:
                        protected_path.relative_to(path.parent.resolve())
                    else:
                        protected_path.relative_to(path.resolve())
                    protected_paths.append(protected_path)
                    logger.info(f'[PathPermissionManager] Added protected path: {protected_path}')
                except ValueError:
                    logger.warning(f'[PathPermissionManager] Protected path {protected_path} is not within context path {path}, skipping')
            if is_file:
                logger.info(f'[PathPermissionManager] Detected file context path: {path}')
                parent_dir = path.parent
                if not any((mp.path == parent_dir.resolve() and mp.path_type == 'file_context_parent' for mp in self.managed_paths)):
                    parent_managed = ManagedPath(path=parent_dir.resolve(), permission=Permission.READ, path_type='file_context_parent', will_be_writable=False, is_file=False)
                    self.managed_paths.append(parent_managed)
                    logger.debug(f'[PathPermissionManager] Added parent directory for file context: {parent_dir}')
            try:
                yaml_permission = Permission(permission_str.lower())
            except ValueError:
                logger.warning(f"[PathPermissionManager] Invalid permission '{permission_str}', using 'read'")
                yaml_permission = Permission.READ
            will_be_writable = yaml_permission == Permission.WRITE
            if self.context_write_access_enabled and will_be_writable:
                actual_permission = Permission.WRITE
                logger.debug(f'[PathPermissionManager] Final agent: context path {path} gets write permission')
            else:
                actual_permission = Permission.READ if will_be_writable else yaml_permission
                if will_be_writable:
                    logger.debug(f'[PathPermissionManager] Coordination agent: context path {path} read-only (will be writable later)')
            managed_path = ManagedPath(path=path.resolve(), permission=actual_permission, path_type='context', will_be_writable=will_be_writable, is_file=is_file, protected_paths=protected_paths)
            self.managed_paths.append(managed_path)
            self._permission_cache.clear()
            path_type_str = 'file' if is_file else 'directory'
            protected_count = len(protected_paths)
            logger.info(f'[PathPermissionManager] Added context {path_type_str}: {path} ({actual_permission.value}, will_be_writable: {will_be_writable}, protected_paths: {protected_count})')

    def add_previous_turn_paths(self, turn_paths: List[Dict[str, Any]]) -> None:
        """
        Add previous turn workspace paths for read access.
        These are tracked separately from regular context paths.

        Args:
            turn_paths: List of turn path configurations
                Format: [{"path": "/path/to/turn_1/workspace", "permission": "read"}, ...]
        """
        for config in turn_paths:
            path_str = config.get('path', '')
            if not path_str:
                continue
            path = Path(path_str).resolve()
            managed_path = ManagedPath(path=path, permission=Permission.READ, path_type='previous_turn', will_be_writable=False)
            self.managed_paths.append(managed_path)
            self._permission_cache.clear()
            logger.info(f'[PathPermissionManager] Added previous turn path: {path} (read-only)')

    def _is_excluded_path(self, path: Path) -> bool:
        """
        Check if a path matches any default excluded patterns.

        System files like .massgen/, .env, .git/ are always excluded from write access,
        EXCEPT when they are within a managed workspace path (which has explicit permissions).

        Args:
            path: Path to check

        Returns:
            True if path should be excluded from write access
        """
        for managed_path in self.managed_paths:
            if managed_path.path_type == 'workspace' and managed_path.contains(path):
                return False
        parts = path.parts
        for part in parts:
            if part in self.DEFAULT_EXCLUDED_PATTERNS:
                return True
        return False

    def get_permission(self, path: Path) -> Optional[Permission]:
        """
        Get permission level for a path.

        Now handles file-specific context paths correctly.

        Args:
            path: Path to check

        Returns:
            Permission level or None if path is not in context
        """
        resolved_path = path.resolve()
        if resolved_path in self._permission_cache:
            logger.debug(f'[PathPermissionManager] Permission cache hit for {resolved_path}: {self._permission_cache[resolved_path].value}')
            return self._permission_cache[resolved_path]
        if self._is_excluded_path(resolved_path):
            logger.info(f'[PathPermissionManager] Path {resolved_path} matches excluded pattern, forcing read-only')
            self._permission_cache[resolved_path] = Permission.READ
            return Permission.READ
        for managed_path in self.managed_paths:
            if managed_path.contains(resolved_path) and managed_path.is_protected(resolved_path):
                logger.info(f'[PathPermissionManager] Path {resolved_path} is protected, forcing read-only')
                self._permission_cache[resolved_path] = Permission.READ
                return Permission.READ
        file_paths = [mp for mp in self.managed_paths if mp.is_file]
        dir_paths = [mp for mp in self.managed_paths if not mp.is_file and mp.path_type != 'file_context_parent']
        for managed_path in file_paths:
            if managed_path.contains(resolved_path):
                logger.info(f'[PathPermissionManager] Found file-specific permission for {resolved_path}: {managed_path.permission.value} (from {managed_path.path}, type: {managed_path.path_type}, will_be_writable: {managed_path.will_be_writable})')
                self._permission_cache[resolved_path] = managed_path.permission
                return managed_path.permission
        sorted_dir_paths = sorted(dir_paths, key=lambda mp: len(mp.path.parts), reverse=True)
        for managed_path in sorted_dir_paths:
            if managed_path.contains(resolved_path) or managed_path.path == resolved_path:
                logger.info(f'[PathPermissionManager] Found permission for {resolved_path}: {managed_path.permission.value} (from {managed_path.path}, type: {managed_path.path_type}, will_be_writable: {managed_path.will_be_writable})')
                self._permission_cache[resolved_path] = managed_path.permission
                return managed_path.permission
        logger.debug(f'[PathPermissionManager] No permission found for {resolved_path} in managed paths: {[(str(mp.path), mp.permission.value, mp.path_type) for mp in self.managed_paths]}')
        return None

    async def pre_tool_use_hook(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        PreToolUse hook to validate tool calls based on permissions.

        This can be used directly with Claude Code SDK hooks or as validation
        for other backends that need manual tool call filtering.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
            - allowed: Whether the tool call should proceed
            - reason: Explanation if blocked (None if allowed)
        """
        if self._is_read_tool(tool_name):
            self._track_read_operation(tool_name, tool_args)
        if self._is_write_tool(tool_name):
            result = self._validate_write_tool(tool_name, tool_args)
            if result[0] and self._is_create_tool(tool_name):
                self._track_create_operation(tool_name, tool_args)
            return result
        if self._is_delete_tool(tool_name):
            return self._validate_delete_tool(tool_name, tool_args)
        command_tools = {'Bash', 'bash', 'shell', 'exec', 'execute_command'}
        if tool_name in command_tools:
            return self._validate_command_tool(tool_name, tool_args)
        return self._validate_file_context_access(tool_name, tool_args)

    def _is_write_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is a write operation using pattern matching.

        Main Claude Code tools: Bash, Glob, Grep, Read, Edit, MultiEdit, Write, WebFetch, WebSearch

        This catches various write tools including:
        - Claude Code: Write, Edit, MultiEdit, NotebookEdit, etc.
        - MCP filesystem: write_file, edit_file, create_directory, move_file
        - Any other tools with write/edit/create/move in the name

        Note: Delete operations are handled separately by _is_delete_tool
        """
        write_patterns = ['.*[Ww]rite.*', '.*[Ee]dit.*', '.*[Cc]reate.*', '.*[Mm]ove.*', '.*[Cc]opy.*']
        for pattern in write_patterns:
            if re.match(pattern, tool_name):
                return True
        return False

    def _is_read_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is a read operation that should be tracked.

        Uses substring matching to handle MCP prefixes (e.g., mcp__workspace_tools__compare_files)

        Tools that read file contents:
        - read/Read: File content reading (matches: Read, read_text_file, read_multimodal_files, etc.)
        - compare_files: File comparison
        - compare_directories: Directory comparison
        """
        tool_lower = tool_name.lower()
        read_keywords = ['compare_files', 'compare_directories']
        return any((keyword in tool_lower for keyword in read_keywords))

    def _is_delete_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is a delete operation.

        Tools that delete files:
        - delete_file: Single file deletion
        - delete_files_batch: Batch file deletion
        - Any tool with delete/remove in the name
        """
        delete_patterns = ['.*[Dd]elete.*', '.*[Rr]emove.*']
        for pattern in delete_patterns:
            if re.match(pattern, tool_name):
                return True
        return False

    def _is_create_tool(self, tool_name: str) -> bool:
        """
        Check if a tool creates new files (for tracking created files).

        Tools that create files:
        - Write: Creates new files
        - write_file: MCP filesystem write
        - create_directory: Creates directories
        """
        create_patterns = ['.*[Ww]rite.*', '.*[Cc]reate.*']
        for pattern in create_patterns:
            if re.match(pattern, tool_name):
                return True
        return False

    def _track_read_operation(self, tool_name: str, tool_args: Dict[str, Any]) -> None:
        """
        Track files that are read by the agent.

        Uses substring matching to handle MCP prefixes consistently.

        Args:
            tool_name: Name of the read tool
            tool_args: Arguments passed to the tool
        """
        tool_lower = tool_name.lower()
        if 'compare_files' in tool_lower:
            file1 = tool_args.get('file1') or tool_args.get('file_path1')
            file2 = tool_args.get('file2') or tool_args.get('file_path2')
            if file1:
                path1 = self._resolve_path_against_workspace(file1)
                self.file_operation_tracker.mark_as_read(Path(path1))
            if file2:
                path2 = self._resolve_path_against_workspace(file2)
                self.file_operation_tracker.mark_as_read(Path(path2))
        elif 'compare_directories' in tool_lower:
            if tool_args.get('show_content_diff'):
                pass
        elif 'read_multiple_files' in tool_lower:
            paths = tool_args.get('paths', [])
            for file_path in paths:
                resolved_path = self._resolve_path_against_workspace(file_path)
                self.file_operation_tracker.mark_as_read(Path(resolved_path))
        else:
            file_path = self._extract_file_path(tool_args)
            if file_path:
                resolved_path = self._resolve_path_against_workspace(file_path)
                self.file_operation_tracker.mark_as_read(Path(resolved_path))

    def _track_create_operation(self, tool_name: str, tool_args: Dict[str, Any]) -> None:
        """
        Track files that are created by the agent.

        Args:
            tool_name: Name of the create tool
            tool_args: Arguments passed to the tool
        """
        file_path = self._extract_file_path(tool_args)
        if file_path:
            resolved_path = self._resolve_path_against_workspace(file_path)
            self.file_operation_tracker.mark_as_created(Path(resolved_path))

    def _validate_delete_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate delete tool operations using read-before-delete policy.

        Args:
            tool_name: Name of the delete tool
            tool_args: Arguments passed to the tool

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        permission_result = self._validate_write_tool(tool_name, tool_args)
        if not permission_result[0]:
            return permission_result
        if tool_name == 'delete_files_batch':
            return self._validate_delete_files_batch(tool_args)
        file_path = self._extract_file_path(tool_args)
        if not file_path:
            return (True, None)
        resolved_path = self._resolve_path_against_workspace(file_path)
        path = Path(resolved_path)
        if path.is_dir():
            can_delete, reason = self.file_operation_tracker.can_delete_directory(path)
            if not can_delete:
                return (False, reason)
        else:
            can_delete, reason = self.file_operation_tracker.can_delete(path)
            if not can_delete:
                return (False, reason)
        return (True, None)

    def _validate_delete_files_batch(self, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate batch delete operations by checking all files that would be deleted.

        Args:
            tool_args: Arguments for delete_files_batch

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        try:
            base_path = tool_args.get('base_path')
            include_patterns = tool_args.get('include_patterns') or ['*']
            exclude_patterns = tool_args.get('exclude_patterns') or []
            if not base_path:
                return (False, 'delete_files_batch requires base_path')
            resolved_base = self._resolve_path_against_workspace(base_path)
            base = Path(resolved_base)
            if not base.exists():
                return (True, None)
            unread_files = []
            for item in base.rglob('*'):
                if not item.is_file():
                    continue
                rel_path = item.relative_to(base)
                rel_path_str = str(rel_path)
                included = any((fnmatch.fnmatch(rel_path_str, pattern) for pattern in include_patterns))
                if not included:
                    continue
                excluded = any((fnmatch.fnmatch(rel_path_str, pattern) for pattern in exclude_patterns))
                if excluded:
                    continue
                if not self.file_operation_tracker.was_read(item):
                    unread_files.append(rel_path_str)
            if unread_files:
                example_files = unread_files[:3]
                suffix = f' (and {len(unread_files) - 3} more)' if len(unread_files) > 3 else ''
                reason = f'Cannot delete {len(unread_files)} unread file(s). Examples: {', '.join(example_files)}{suffix}. Please read files before deletion using Read or read_multimodal_files.'
                logger.info(f'[PathPermissionManager] Blocking batch delete: {reason}')
                return (False, reason)
            return (True, None)
        except Exception as e:
            logger.error(f'[PathPermissionManager] Error validating batch delete: {e}')
            return (False, f'Batch delete validation failed: {e}')

    def _is_path_within_allowed_directories(self, path: Path) -> bool:
        """
        Check if a path is within any allowed directory (workspace or context paths).

        This enforces directory boundaries - paths outside managed directories are not allowed.

        Args:
            path: Path to check

        Returns:
            True if path is within allowed directories, False otherwise
        """
        resolved_path = path.resolve()
        for managed_path in self.managed_paths:
            if managed_path.path_type == 'file_context_parent':
                continue
            if managed_path.contains(resolved_path) or managed_path.path == resolved_path:
                return True
        return False

    def _validate_file_context_access(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate access for all file operations - enforces directory boundaries and permissions.

        This method ensures that:
        1. ALL file operations are restricted to workspace + context paths (directory boundary)
        2. Read/write permissions are enforced within allowed directories
        3. Sibling file access is prevented for file-specific context paths

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        file_path = self._extract_file_path(tool_args)
        if not file_path:
            return (True, None)
        file_path = self._resolve_path_against_workspace(file_path)
        path = Path(file_path).resolve()
        if not self._is_path_within_allowed_directories(path):
            logger.warning(f"[PathPermissionManager] BLOCKED: '{tool_name}' attempted to access path outside allowed directories: {path}")
            return (False, f"Access denied: '{path}' is outside allowed directories. Only workspace and context paths are accessible.")
        permission = self.get_permission(path)
        logger.debug(f"[PathPermissionManager] Validating '{tool_name}' on path: {path} with permission: {permission}")
        if permission is None:
            parent_paths = [mp for mp in self.managed_paths if mp.path_type == 'file_context_parent']
            for parent_mp in parent_paths:
                if parent_mp.contains(path):
                    return (False, f"Access denied: '{path}' is not an explicitly allowed file in this directory")
            return (True, None)
        return (True, None)

    def _validate_write_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate write tool access."""
        if tool_name == 'copy_files_batch':
            return self._validate_copy_files_batch(tool_args)
        file_path = self._extract_file_path(tool_args)
        if not file_path:
            return (True, None)
        file_path = self._resolve_path_against_workspace(file_path)
        path = Path(file_path).resolve()
        permission = self.get_permission(path)
        logger.debug(f"[PathPermissionManager] Validating write tool '{tool_name}' for path: {path} with permission: {permission}")
        if permission is None:
            parent_paths = [mp for mp in self.managed_paths if mp.path_type == 'file_context_parent']
            for parent_mp in parent_paths:
                if parent_mp.contains(path):
                    return (False, f"Access denied: '{path}' is not an explicitly allowed file in this directory")
            return (True, None)
        if permission == Permission.WRITE:
            return (True, None)
        else:
            return (False, f"No write permission for '{path}' (read-only context path)")

    def _resolve_path_against_workspace(self, path_str: str) -> str:
        """
        Resolve a path string against the workspace directory if it's relative.

        When MCP servers run with cwd set to workspace, they resolve relative paths
        against the workspace. This function does the same for validation purposes.

        Args:
            path_str: Path string that may be relative or absolute

        Returns:
            Absolute path string (resolved against workspace if relative)
        """
        if not path_str:
            return path_str
        if path_str.startswith('~'):
            path = Path(path_str).expanduser()
            return str(path)
        path = Path(path_str)
        if path.is_absolute():
            return path_str
        mcp_paths = self.get_mcp_filesystem_paths()
        if mcp_paths:
            workspace_path = Path(mcp_paths[0])
            resolved = workspace_path / path_str
            logger.debug(f"[PathPermissionManager] Resolved relative path '{path_str}' to '{resolved}'")
            return str(resolved)
        return path_str

    def _validate_copy_files_batch(self, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate copy_files_batch by checking all destination paths after globbing."""
        try:
            logger.debug(f'[PathPermissionManager] copy_files_batch validation - context_write_access_enabled: {self.context_write_access_enabled}')
            source_base_path = tool_args.get('source_base_path')
            destination_base_path = tool_args.get('destination_base_path', '')
            include_patterns = tool_args.get('include_patterns')
            exclude_patterns = tool_args.get('exclude_patterns')
            if not source_base_path:
                return (False, 'copy_files_batch requires source_base_path')
            destination_base_path = self._resolve_path_against_workspace(destination_base_path)
            file_pairs = get_copy_file_pairs(self.get_mcp_filesystem_paths(), source_base_path, destination_base_path, include_patterns, exclude_patterns)
            blocked_paths = []
            for source_file, dest_file in file_pairs:
                permission = self.get_permission(dest_file)
                logger.debug(f'[PathPermissionManager] copy_files_batch checking dest: {dest_file}, permission: {permission}')
                if permission == Permission.READ:
                    blocked_paths.append(str(dest_file))
            if blocked_paths:
                example_paths = blocked_paths[:3]
                suffix = f' (and {len(blocked_paths) - 3} more)' if len(blocked_paths) > 3 else ''
                return (False, f'No write permission for destination paths: {', '.join(example_paths)}{suffix}')
            return (True, None)
        except Exception as e:
            return (False, f'copy_files_batch validation failed: {e}')

    def _validate_command_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate command tool access.

        As of v0.0.20, only Claude Code supports execution.

        For Claude Code: Validates directory boundaries for all paths in Bash commands.
        This prevents access to paths outside workspace + context paths.

        """
        command = tool_args.get('command', '') or tool_args.get('cmd', '')
        dangerous_patterns = ['rm ', 'rm -', 'rmdir', 'del ', 'sudo ', 'su ', 'chmod ', 'chown ', 'format ', 'fdisk', 'mkfs']
        write_patterns = ['>', '>>', 'mv ', 'move ', 'cp ', 'copy ', 'touch ', 'mkdir ', 'echo ', 'sed -i', 'perl -i']
        for pattern in write_patterns:
            if pattern in command:
                target_file = self._extract_file_from_command(command, pattern)
                if target_file:
                    path = Path(target_file).resolve()
                    permission = self.get_permission(path)
                    if permission and permission == Permission.READ:
                        return (False, f'Command would modify read-only context path: {path}')
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return (False, f"Dangerous command pattern '{pattern}' is not allowed")
        if '$' in command:
            safe_vars = ['$?', '$#', '$$']
            has_unsafe_var = False
            if '$(' in command or '${' in command:
                has_unsafe_var = True
            elif any((c in command for c in ['$HOME', '$USER', '$TMPDIR', '$PWD', '$OLDPWD', '$PATH'])):
                has_unsafe_var = True
            else:
                import re
                if re.search('\\$[A-Za-z_][A-Za-z0-9_]*', command):
                    for safe in safe_vars:
                        command = command.replace(safe, '')
                    if re.search('\\$[A-Za-z_][A-Za-z0-9_]*', command):
                        has_unsafe_var = True
            if has_unsafe_var:
                return (False, 'Environment variables in Bash commands are not allowed (security risk: can reference paths outside workspace)')
        if '`' in command:
            return (False, 'Backtick command substitution is not allowed (security risk)')
        if '<(' in command or '>(' in command:
            return (False, 'Process substitution is not allowed (security risk)')
        paths = self._extract_paths_from_command(command)
        for path_str in paths:
            try:
                resolved_path_str = self._resolve_path_against_workspace(path_str)
                path = Path(resolved_path_str).resolve()
                if not self._is_path_within_allowed_directories(path):
                    logger.warning(f'[PathPermissionManager] BLOCKED Bash command accessing path outside allowed directories: {path} (from: {path_str})')
                    return (False, f"Access denied: Bash command references '{path_str}' which resolves to '{path}' outside allowed directories")
            except Exception as e:
                logger.debug(f"[PathPermissionManager] Could not validate path '{path_str}' in Bash command: {e}")
                continue
        return (True, None)

    def _extract_file_path(self, tool_args: Dict[str, Any]) -> Optional[str]:
        """Extract file path from tool arguments."""
        path_keys = ['file_path', 'path', 'filename', 'file', 'notebook_path', 'target', 'destination', 'destination_path', 'destination_base_path']
        for key in path_keys:
            if key in tool_args:
                return tool_args[key]
        return None

    def _extract_file_from_command(self, command: str, pattern: str) -> Optional[str]:
        """Try to extract target file from a command string."""
        if pattern in ['>', '>>']:
            parts = command.split(pattern)
            if len(parts) > 1:
                target = parts[1].strip().split()[0] if parts[1].strip() else None
                if target:
                    return target.strip('"\'')
        if pattern in ['mv ', 'cp ', 'move ', 'copy ']:
            parts = command.split()
            try:
                idx = parts.index(pattern.strip())
                if idx + 2 < len(parts):
                    return parts[idx + 2]
            except (ValueError, IndexError):
                pass
        if pattern in ['touch ', 'mkdir ', 'echo ']:
            parts = command.split()
            try:
                idx = parts.index(pattern.strip())
                if idx + 1 < len(parts):
                    return parts[idx + 1].strip('"\'')
            except (ValueError, IndexError):
                pass
        return None

    def _extract_paths_from_command(self, command: str) -> List[str]:
        """
        Extract all potential file/directory paths from a Bash command for validation.

        This is Claude Code specific - extracts paths to validate directory boundaries.
        Looks for both absolute paths (starting with /) and relative paths (including ../).

        Args:
            command: Bash command string

        Returns:
            List of path strings found in the command
        """
        import shlex
        paths = []
        try:
            tokens = shlex.split(command)
        except ValueError:
            tokens = command.split()
        for token in tokens:
            cleaned = token.strip('"\'').strip()
            if not cleaned:
                continue
            if cleaned.startswith('-'):
                continue
            if cleaned in ['&&', '||', '|', ';', '>']:
                continue
            if cleaned.startswith('/') or cleaned.startswith('~') or cleaned.startswith('../') or (cleaned == '..') or cleaned.startswith('./'):
                if '*' in cleaned or '?' in cleaned or '[' in cleaned:
                    base = cleaned.split('*')[0].split('?')[0].split('[')[0]
                    if base.endswith('/'):
                        base = base[:-1]
                    if base:
                        paths.append(base)
                else:
                    paths.append(cleaned)
        return paths

    def get_accessible_paths(self) -> List[Path]:
        """Get list of all accessible paths."""
        return [path.path for path in self.managed_paths]

    def get_mcp_filesystem_paths(self) -> List[str]:
        """
        Get all managed paths for MCP filesystem server configuration. Workspace path will be first.

        Only returns directories, as MCP filesystem server cannot accept file paths as arguments.
        For file context paths, the parent directory is already added with path_type="file_context_parent".

        Returns:
            List of directory path strings to include in MCP filesystem server args
        """
        workspace_paths = [str(mp.path) for mp in self.managed_paths if mp.path_type == 'workspace']
        other_paths = [str(mp.path) for mp in self.managed_paths if mp.path_type != 'workspace' and (not mp.is_file)]
        out = workspace_paths + other_paths
        return out

    def get_permission_summary(self) -> str:
        """Get a human-readable summary of permissions."""
        if not self.managed_paths:
            return 'No managed paths configured'
        lines = [f'Managed paths ({len(self.managed_paths)} total):']
        for managed_path in self.managed_paths:
            emoji = '📝' if managed_path.permission == Permission.WRITE else '👁️'
            lines.append(f'  {emoji} {managed_path.path} ({managed_path.permission.value}, {managed_path.path_type})')
        return '\n'.join(lines)

    async def validate_context_access(self, input_data: Dict[str, Any], tool_use_id: Optional[str], context: Any) -> Dict[str, Any]:
        """
        Claude Code SDK compatible hook function for PreToolUse.

        Args:
            input_data: Tool input data with 'tool_name' and 'tool_input'
            tool_use_id: Tool use identifier
            context: HookContext from claude_code_sdk

        Returns:
            Hook response dict with permission decision
        """
        logger.info(f'[PathPermissionManager] PreToolUse hook called for tool_use_id={tool_use_id}, input_data={input_data}')
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        allowed, reason = await self.pre_tool_use_hook(tool_name, tool_input)
        if not allowed:
            logger.warning(f'[PathPermissionManager] Blocked {tool_name}: {reason}')
            return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': reason or 'Access denied based on context path permissions'}}
        return {}

    def get_claude_code_hooks_config(self) -> Dict[str, Any]:
        """
        Get Claude Agent SDK hooks configuration.

        Returns:
            Hooks configuration dict for ClaudeAgentOptions
        """
        if not self.managed_paths:
            return {}
        try:
            from claude_agent_sdk import HookMatcher
        except ImportError:
            logger.warning('[PathPermissionManager] claude_agent_sdk not available, hooks disabled')
            return {}
        return {'PreToolUse': [HookMatcher(matcher='Read', hooks=[self.validate_context_access]), HookMatcher(matcher='Write', hooks=[self.validate_context_access]), HookMatcher(matcher='Edit', hooks=[self.validate_context_access]), HookMatcher(matcher='MultiEdit', hooks=[self.validate_context_access]), HookMatcher(matcher='NotebookEdit', hooks=[self.validate_context_access]), HookMatcher(matcher='Grep', hooks=[self.validate_context_access]), HookMatcher(matcher='Glob', hooks=[self.validate_context_access]), HookMatcher(matcher='LS', hooks=[self.validate_context_access]), HookMatcher(matcher='Bash', hooks=[self.validate_context_access])]}

def add_context_paths(self, context_paths: List[Dict[str, Any]]) -> None:
    """
        Add context paths from configuration.

        Now supports both files and directories as context paths, with optional protected paths.

        Args:
            context_paths: List of context path configurations
                Format: [
                    {
                        "path": "C:/project/src",
                        "permission": "write",
                        "protected_paths": ["tests/do-not-touch/", "config.yaml"]  # Optional
                    },
                    {"path": "C:/project/logo.png", "permission": "read"}
                ]

        Note: During coordination, all context paths are read-only regardless of YAML settings.
              Only the final agent with context_write_access_enabled=True can write to paths marked as "write".
              Protected paths are ALWAYS read-only and immune from deletion, even if parent has write permission.
        """
    for config in context_paths:
        path_str = config.get('path', '')
        permission_str = config.get('permission', 'read')
        protected_paths_config = config.get('protected_paths', [])
        if not path_str:
            continue
        path = Path(path_str)
        if not path.exists():
            logger.warning(f'[PathPermissionManager] Context path does not exist: {path}')
            continue
        is_file = path.is_file()
        protected_paths = []
        for protected_str in protected_paths_config:
            protected_path = Path(protected_str)
            if not protected_path.is_absolute():
                if is_file:
                    protected_path = (path.parent / protected_str).resolve()
                else:
                    protected_path = (path / protected_str).resolve()
            else:
                protected_path = protected_path.resolve()
            try:
                if is_file:
                    protected_path.relative_to(path.parent.resolve())
                else:
                    protected_path.relative_to(path.resolve())
                protected_paths.append(protected_path)
                logger.info(f'[PathPermissionManager] Added protected path: {protected_path}')
            except ValueError:
                logger.warning(f'[PathPermissionManager] Protected path {protected_path} is not within context path {path}, skipping')
        if is_file:
            logger.info(f'[PathPermissionManager] Detected file context path: {path}')
            parent_dir = path.parent
            if not any((mp.path == parent_dir.resolve() and mp.path_type == 'file_context_parent' for mp in self.managed_paths)):
                parent_managed = ManagedPath(path=parent_dir.resolve(), permission=Permission.READ, path_type='file_context_parent', will_be_writable=False, is_file=False)
                self.managed_paths.append(parent_managed)
                logger.debug(f'[PathPermissionManager] Added parent directory for file context: {parent_dir}')
        try:
            yaml_permission = Permission(permission_str.lower())
        except ValueError:
            logger.warning(f"[PathPermissionManager] Invalid permission '{permission_str}', using 'read'")
            yaml_permission = Permission.READ
        will_be_writable = yaml_permission == Permission.WRITE
        if self.context_write_access_enabled and will_be_writable:
            actual_permission = Permission.WRITE
            logger.debug(f'[PathPermissionManager] Final agent: context path {path} gets write permission')
        else:
            actual_permission = Permission.READ if will_be_writable else yaml_permission
            if will_be_writable:
                logger.debug(f'[PathPermissionManager] Coordination agent: context path {path} read-only (will be writable later)')
        managed_path = ManagedPath(path=path.resolve(), permission=actual_permission, path_type='context', will_be_writable=will_be_writable, is_file=is_file, protected_paths=protected_paths)
        self.managed_paths.append(managed_path)
        self._permission_cache.clear()
        path_type_str = 'file' if is_file else 'directory'
        protected_count = len(protected_paths)
        logger.info(f'[PathPermissionManager] Added context {path_type_str}: {path} ({actual_permission.value}, will_be_writable: {will_be_writable}, protected_paths: {protected_count})')

def add_previous_turn_paths(self, turn_paths: List[Dict[str, Any]]) -> None:
    """
        Add previous turn workspace paths for read access.
        These are tracked separately from regular context paths.

        Args:
            turn_paths: List of turn path configurations
                Format: [{"path": "/path/to/turn_1/workspace", "permission": "read"}, ...]
        """
    for config in turn_paths:
        path_str = config.get('path', '')
        if not path_str:
            continue
        path = Path(path_str).resolve()
        managed_path = ManagedPath(path=path, permission=Permission.READ, path_type='previous_turn', will_be_writable=False)
        self.managed_paths.append(managed_path)
        self._permission_cache.clear()
        logger.info(f'[PathPermissionManager] Added previous turn path: {path} (read-only)')

def _is_excluded_path(self, path: Path) -> bool:
    """
        Check if a path matches any default excluded patterns.

        System files like .massgen/, .env, .git/ are always excluded from write access,
        EXCEPT when they are within a managed workspace path (which has explicit permissions).

        Args:
            path: Path to check

        Returns:
            True if path should be excluded from write access
        """
    for managed_path in self.managed_paths:
        if managed_path.path_type == 'workspace' and managed_path.contains(path):
            return False
    parts = path.parts
    for part in parts:
        if part in self.DEFAULT_EXCLUDED_PATTERNS:
            return True
    return False

def _track_read_operation(self, tool_name: str, tool_args: Dict[str, Any]) -> None:
    """
        Track files that are read by the agent.

        Uses substring matching to handle MCP prefixes consistently.

        Args:
            tool_name: Name of the read tool
            tool_args: Arguments passed to the tool
        """
    tool_lower = tool_name.lower()
    if 'compare_files' in tool_lower:
        file1 = tool_args.get('file1') or tool_args.get('file_path1')
        file2 = tool_args.get('file2') or tool_args.get('file_path2')
        if file1:
            path1 = self._resolve_path_against_workspace(file1)
            self.file_operation_tracker.mark_as_read(Path(path1))
        if file2:
            path2 = self._resolve_path_against_workspace(file2)
            self.file_operation_tracker.mark_as_read(Path(path2))
    elif 'compare_directories' in tool_lower:
        if tool_args.get('show_content_diff'):
            pass
    elif 'read_multiple_files' in tool_lower:
        paths = tool_args.get('paths', [])
        for file_path in paths:
            resolved_path = self._resolve_path_against_workspace(file_path)
            self.file_operation_tracker.mark_as_read(Path(resolved_path))
    else:
        file_path = self._extract_file_path(tool_args)
        if file_path:
            resolved_path = self._resolve_path_against_workspace(file_path)
            self.file_operation_tracker.mark_as_read(Path(resolved_path))

def _track_create_operation(self, tool_name: str, tool_args: Dict[str, Any]) -> None:
    """
        Track files that are created by the agent.

        Args:
            tool_name: Name of the create tool
            tool_args: Arguments passed to the tool
        """
    file_path = self._extract_file_path(tool_args)
    if file_path:
        resolved_path = self._resolve_path_against_workspace(file_path)
        self.file_operation_tracker.mark_as_created(Path(resolved_path))

def _validate_delete_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
        Validate delete tool operations using read-before-delete policy.

        Args:
            tool_name: Name of the delete tool
            tool_args: Arguments passed to the tool

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
    permission_result = self._validate_write_tool(tool_name, tool_args)
    if not permission_result[0]:
        return permission_result
    if tool_name == 'delete_files_batch':
        return self._validate_delete_files_batch(tool_args)
    file_path = self._extract_file_path(tool_args)
    if not file_path:
        return (True, None)
    resolved_path = self._resolve_path_against_workspace(file_path)
    path = Path(resolved_path)
    if path.is_dir():
        can_delete, reason = self.file_operation_tracker.can_delete_directory(path)
        if not can_delete:
            return (False, reason)
    else:
        can_delete, reason = self.file_operation_tracker.can_delete(path)
        if not can_delete:
            return (False, reason)
    return (True, None)

def _is_path_within_allowed_directories(self, path: Path) -> bool:
    """
        Check if a path is within any allowed directory (workspace or context paths).

        This enforces directory boundaries - paths outside managed directories are not allowed.

        Args:
            path: Path to check

        Returns:
            True if path is within allowed directories, False otherwise
        """
    resolved_path = path.resolve()
    for managed_path in self.managed_paths:
        if managed_path.path_type == 'file_context_parent':
            continue
        if managed_path.contains(resolved_path) or managed_path.path == resolved_path:
            return True
    return False

def _validate_file_context_access(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
        Validate access for all file operations - enforces directory boundaries and permissions.

        This method ensures that:
        1. ALL file operations are restricted to workspace + context paths (directory boundary)
        2. Read/write permissions are enforced within allowed directories
        3. Sibling file access is prevented for file-specific context paths

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
    file_path = self._extract_file_path(tool_args)
    if not file_path:
        return (True, None)
    file_path = self._resolve_path_against_workspace(file_path)
    path = Path(file_path).resolve()
    if not self._is_path_within_allowed_directories(path):
        logger.warning(f"[PathPermissionManager] BLOCKED: '{tool_name}' attempted to access path outside allowed directories: {path}")
        return (False, f"Access denied: '{path}' is outside allowed directories. Only workspace and context paths are accessible.")
    permission = self.get_permission(path)
    logger.debug(f"[PathPermissionManager] Validating '{tool_name}' on path: {path} with permission: {permission}")
    if permission is None:
        parent_paths = [mp for mp in self.managed_paths if mp.path_type == 'file_context_parent']
        for parent_mp in parent_paths:
            if parent_mp.contains(path):
                return (False, f"Access denied: '{path}' is not an explicitly allowed file in this directory")
        return (True, None)
    return (True, None)

def _validate_write_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate write tool access."""
    if tool_name == 'copy_files_batch':
        return self._validate_copy_files_batch(tool_args)
    file_path = self._extract_file_path(tool_args)
    if not file_path:
        return (True, None)
    file_path = self._resolve_path_against_workspace(file_path)
    path = Path(file_path).resolve()
    permission = self.get_permission(path)
    logger.debug(f"[PathPermissionManager] Validating write tool '{tool_name}' for path: {path} with permission: {permission}")
    if permission is None:
        parent_paths = [mp for mp in self.managed_paths if mp.path_type == 'file_context_parent']
        for parent_mp in parent_paths:
            if parent_mp.contains(path):
                return (False, f"Access denied: '{path}' is not an explicitly allowed file in this directory")
        return (True, None)
    if permission == Permission.WRITE:
        return (True, None)
    else:
        return (False, f"No write permission for '{path}' (read-only context path)")

def _resolve_path_against_workspace(self, path_str: str) -> str:
    """
        Resolve a path string against the workspace directory if it's relative.

        When MCP servers run with cwd set to workspace, they resolve relative paths
        against the workspace. This function does the same for validation purposes.

        Args:
            path_str: Path string that may be relative or absolute

        Returns:
            Absolute path string (resolved against workspace if relative)
        """
    if not path_str:
        return path_str
    if path_str.startswith('~'):
        path = Path(path_str).expanduser()
        return str(path)
    path = Path(path_str)
    if path.is_absolute():
        return path_str
    mcp_paths = self.get_mcp_filesystem_paths()
    if mcp_paths:
        workspace_path = Path(mcp_paths[0])
        resolved = workspace_path / path_str
        logger.debug(f"[PathPermissionManager] Resolved relative path '{path_str}' to '{resolved}'")
        return str(resolved)
    return path_str

def _validate_copy_files_batch(self, tool_args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate copy_files_batch by checking all destination paths after globbing."""
    try:
        logger.debug(f'[PathPermissionManager] copy_files_batch validation - context_write_access_enabled: {self.context_write_access_enabled}')
        source_base_path = tool_args.get('source_base_path')
        destination_base_path = tool_args.get('destination_base_path', '')
        include_patterns = tool_args.get('include_patterns')
        exclude_patterns = tool_args.get('exclude_patterns')
        if not source_base_path:
            return (False, 'copy_files_batch requires source_base_path')
        destination_base_path = self._resolve_path_against_workspace(destination_base_path)
        file_pairs = get_copy_file_pairs(self.get_mcp_filesystem_paths(), source_base_path, destination_base_path, include_patterns, exclude_patterns)
        blocked_paths = []
        for source_file, dest_file in file_pairs:
            permission = self.get_permission(dest_file)
            logger.debug(f'[PathPermissionManager] copy_files_batch checking dest: {dest_file}, permission: {permission}')
            if permission == Permission.READ:
                blocked_paths.append(str(dest_file))
        if blocked_paths:
            example_paths = blocked_paths[:3]
            suffix = f' (and {len(blocked_paths) - 3} more)' if len(blocked_paths) > 3 else ''
            return (False, f'No write permission for destination paths: {', '.join(example_paths)}{suffix}')
        return (True, None)
    except Exception as e:
        return (False, f'copy_files_batch validation failed: {e}')

class FileOperationTracker:
    """
    Track file operations to enforce read-before-delete policy.

    This tracker maintains a set of files that have been read by the agent,
    allowing the system to prevent deletion of files that haven't been
    comprehended yet.
    """
    AUTO_GENERATED_PATTERNS = ['__pycache__', '.pyc', '.pyo', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.coverage', '*.egg-info', '.tox', '.nox', 'node_modules', '.next', '.nuxt', 'dist', 'build', '.DS_Store', 'Thumbs.db', '*.log', '*.swp', '*.swo', '*~']

    def __init__(self, enforce_read_before_delete: bool=True):
        """
        Initialize the file operation tracker.

        Args:
            enforce_read_before_delete: Whether to enforce read-before-delete policy
        """
        self._read_files: Set[Path] = set()
        self._created_files: Set[Path] = set()
        self.enforce_read_before_delete = enforce_read_before_delete
        logger.info(f'[FileOperationTracker] Initialized with enforce_read_before_delete={enforce_read_before_delete}')

    def mark_as_read(self, file_path: Path) -> None:
        """
        Mark a file as read/understood by the agent.

        This is called when the agent uses Read, read_multimodal_files,
        compare_files, or other tools that read file contents.

        Args:
            file_path: Path to the file that was read
        """
        resolved_path = file_path.resolve()
        self._read_files.add(resolved_path)
        logger.debug(f'[FileOperationTracker] Marked as read: {resolved_path}')

    def mark_as_created(self, file_path: Path) -> None:
        """
        Mark a file as created by the agent during this turn.

        Files created by the agent are exempt from read-before-delete requirements
        since the agent knows what it created.

        Args:
            file_path: Path to the file that was created
        """
        resolved_path = file_path.resolve()
        self._created_files.add(resolved_path)
        logger.debug(f'[FileOperationTracker] Marked as created: {resolved_path}')

    def was_read(self, file_path: Path) -> bool:
        """
        Check if a file was read by the agent.

        Args:
            file_path: Path to check

        Returns:
            True if the file was read or created by the agent
        """
        resolved_path = file_path.resolve()
        was_read = resolved_path in self._read_files
        was_created = resolved_path in self._created_files
        logger.debug(f'[FileOperationTracker] Checking read status for {resolved_path}: read={was_read}, created={was_created}')
        return was_read or was_created

    def _is_auto_generated(self, file_path: Path) -> bool:
        """
        Check if a file matches auto-generated patterns and is exempt from read-before-delete.

        Args:
            file_path: Path to check

        Returns:
            True if file is auto-generated and can be deleted without reading
        """
        path_str = str(file_path)
        path_parts = file_path.parts
        for pattern in self.AUTO_GENERATED_PATTERNS:
            if pattern in path_parts:
                return True
            if pattern.startswith('.') and (not pattern.startswith('.*')):
                if path_str.endswith(pattern):
                    return True
            if '*' in pattern:
                if fnmatch.fnmatch(file_path.name, pattern):
                    return True
        return False

    def can_delete(self, file_path: Path) -> tuple[bool, str | None]:
        """
        Check if a file can be deleted based on read-before-delete policy.

        Auto-generated files (like __pycache__, .pyc, etc.) are exempt from
        read-before-delete requirements.

        Args:
            file_path: Path to the file to check

        Returns:
            Tuple of (can_delete: bool, reason: Optional[str])
            - can_delete: Whether deletion is allowed
            - reason: Explanation if deletion is blocked (None if allowed)
        """
        if not self.enforce_read_before_delete:
            return (True, None)
        resolved_path = file_path.resolve()
        if not resolved_path.exists():
            return (True, None)
        if self._is_auto_generated(resolved_path):
            logger.debug(f'[FileOperationTracker] Allowing deletion of auto-generated file: {resolved_path}')
            return (True, None)
        if self.was_read(resolved_path):
            return (True, None)
        reason = f"Cannot delete '{resolved_path}': File must be read before deletion. Use read (including read_multimodal_files) or diff tools to view the file first."
        logger.info(f'[FileOperationTracker] Blocking deletion: {reason}')
        return (False, reason)

    def can_delete_directory(self, dir_path: Path) -> tuple[bool, str | None]:
        """
        Check if a directory can be deleted based on read-before-delete policy.

        For directories, we check if all files within have been read.
        Auto-generated files are exempt from read-before-delete requirements.

        Args:
            dir_path: Path to the directory to check

        Returns:
            Tuple of (can_delete: bool, reason: Optional[str])
            - can_delete: Whether deletion is allowed
            - reason: Explanation if deletion is blocked (None if allowed)
        """
        if not self.enforce_read_before_delete:
            return (True, None)
        resolved_dir = dir_path.resolve()
        if not resolved_dir.exists() or not resolved_dir.is_dir():
            return (True, None)
        unread_files = []
        for file_path in resolved_dir.rglob('*'):
            if file_path.is_file():
                if self._is_auto_generated(file_path):
                    continue
                if not self.was_read(file_path):
                    unread_files.append(str(file_path.relative_to(resolved_dir)))
        if unread_files:
            example_files = unread_files[:3]
            suffix = f' (and {len(unread_files) - 3} more)' if len(unread_files) > 3 else ''
            reason = f"Cannot delete directory '{resolved_dir}': Contains {len(unread_files)} unread file(s). Examples: {', '.join(example_files)}{suffix}. Please read files before deletion."
            logger.info(f'[FileOperationTracker] Blocking directory deletion: {reason}')
            return (False, reason)
        return (True, None)

    def clear(self) -> None:
        """
        Clear all tracked operations.

        This should be called at the start of each agent's turn to reset
        the tracker state.
        """
        read_count = len(self._read_files)
        created_count = len(self._created_files)
        self._read_files.clear()
        self._created_files.clear()
        logger.info(f'[FileOperationTracker] Cleared tracker (had {read_count} read files, {created_count} created files)')

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about tracked operations.

        Returns:
            Dictionary with tracking statistics
        """
        return {'read_files': len(self._read_files), 'created_files': len(self._created_files), 'total_tracked': len(self._read_files) + len(self._created_files)}

def was_read(self, file_path: Path) -> bool:
    """
        Check if a file was read by the agent.

        Args:
            file_path: Path to check

        Returns:
            True if the file was read or created by the agent
        """
    resolved_path = file_path.resolve()
    was_read = resolved_path in self._read_files
    was_created = resolved_path in self._created_files
    logger.debug(f'[FileOperationTracker] Checking read status for {resolved_path}: read={was_read}, created={was_created}')
    return was_read or was_created

@mcp.tool()
def execute_command(command: str, timeout: Optional[int]=None, work_dir: Optional[str]=None) -> Dict[str, Any]:
    """
        Execute a command line command.

        This tool allows executing any command line program including:
        - Python: execute_command("python script.py")
        - Node.js: execute_command("node app.js")
        - Tests: execute_command("pytest tests/")
        - Build tools: execute_command("npm run build")
        - Shell commands: execute_command("ls -la")

        The command is executed in a shell environment, so you can use shell features
        like pipes, redirection, and environment variables. On Windows, this uses
        cmd.exe; on Unix/Mac, this uses the default shell (typically bash).

        Args:
            command: The command to execute (required)
            timeout: Maximum execution time in seconds (default: 60)
                    Set to None for no timeout (use with caution)
            work_dir: Working directory for execution (relative to workspace)
                     If not specified, uses the current workspace directory

        Returns:
            Dictionary containing:
            - success: bool - True if exit code was 0
            - exit_code: int - Process exit code
            - stdout: str - Standard output from the command
            - stderr: str - Standard error from the command
            - execution_time: float - Time taken to execute in seconds
            - command: str - The command that was executed
            - work_dir: str - The working directory used

        Security:
            - Execution is confined to allowed paths
            - Timeout enforced to prevent infinite loops
            - Output size limited to prevent memory exhaustion
            - Basic sanitization against dangerous commands

        Examples:
            # Run Python script
            execute_command("python test.py")

            # Run tests with pytest
            execute_command("pytest tests/ -v")

            # Install package and run script
            execute_command("pip install requests && python scraper.py")

            # Check Python version
            execute_command("python --version")

            # List files
            execute_command("ls -la")  # Unix/Mac
            execute_command("dir")      # Windows
        """
    try:
        try:
            _sanitize_command(command)
        except ValueError as e:
            return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': str(e), 'execution_time': 0.0, 'command': command, 'work_dir': work_dir or str(Path.cwd())}
        try:
            _check_command_filters(command, mcp.allowed_commands, mcp.blocked_commands)
        except ValueError as e:
            return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': str(e), 'execution_time': 0.0, 'command': command, 'work_dir': work_dir or str(Path.cwd())}
        if timeout is None:
            timeout = mcp.default_timeout
        if work_dir:
            if Path(work_dir).is_absolute():
                work_path = Path(work_dir).resolve()
            else:
                work_path = (Path.cwd() / work_dir).resolve()
        else:
            work_path = Path.cwd()
        _validate_path_access(work_path, mcp.allowed_paths)
        if not work_path.exists():
            return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Working directory does not exist: {work_path}', 'execution_time': 0.0, 'command': command, 'work_dir': str(work_path)}
        if not work_path.is_dir():
            return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Working directory is not a directory: {work_path}', 'execution_time': 0.0, 'command': command, 'work_dir': str(work_path)}
        if mcp.execution_mode == 'docker':
            if not mcp.docker_client:
                return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': 'Docker mode enabled but docker_client not initialized', 'execution_time': 0.0, 'command': command, 'work_dir': str(work_path)}
            if not mcp.agent_id:
                return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': 'Docker mode requires agent_id to be set. This should be configured by the orchestrator.', 'execution_time': 0.0, 'command': command, 'work_dir': str(work_path)}
            try:
                container_name = f'massgen-{mcp.agent_id}'
                container = mcp.docker_client.containers.get(container_name)
                exec_config = {'cmd': ['/bin/sh', '-c', command], 'workdir': str(work_path), 'stdout': True, 'stderr': True}
                start_time = time.time()
                exit_code, output = container.exec_run(**exec_config)
                execution_time = time.time() - start_time
                output_str = output.decode('utf-8') if isinstance(output, bytes) else output
                if len(output_str) > mcp.max_output_size:
                    output_str = output_str[:mcp.max_output_size] + f'\n... (truncated, exceeded {mcp.max_output_size} bytes)'
                return {'success': exit_code == 0, 'exit_code': exit_code, 'stdout': output_str, 'stderr': '', 'execution_time': execution_time, 'command': command, 'work_dir': str(work_path)}
            except DockerException as e:
                return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Docker container error: {str(e)}', 'execution_time': 0.0, 'command': command, 'work_dir': str(work_path)}
            except Exception as e:
                return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Docker execution error: {str(e)}', 'execution_time': 0.0, 'command': command, 'work_dir': str(work_path)}
        else:
            env = _prepare_environment(work_path)
            start_time = time.time()
            try:
                result = subprocess.run(command, shell=True, cwd=str(work_path), timeout=timeout, capture_output=True, text=True, env=env)
                execution_time = time.time() - start_time
                stdout = result.stdout
                stderr = result.stderr
                if len(stdout) > mcp.max_output_size:
                    stdout = stdout[:mcp.max_output_size] + f'\n... (truncated, exceeded {mcp.max_output_size} bytes)'
                if len(stderr) > mcp.max_output_size:
                    stderr = stderr[:mcp.max_output_size] + f'\n... (truncated, exceeded {mcp.max_output_size} bytes)'
                return {'success': result.returncode == 0, 'exit_code': result.returncode, 'stdout': stdout, 'stderr': stderr, 'execution_time': execution_time, 'command': command, 'work_dir': str(work_path)}
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Command timed out after {timeout} seconds', 'execution_time': execution_time, 'command': command, 'work_dir': str(work_path)}
            except Exception as e:
                execution_time = time.time() - start_time
                return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Execution error: {str(e)}', 'execution_time': execution_time, 'command': command, 'work_dir': str(work_path)}
    except ValueError as e:
        return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Path validation error: {str(e)}', 'execution_time': 0.0, 'command': command, 'work_dir': work_dir or str(Path.cwd())}
    except Exception as e:
        return {'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Unexpected error: {str(e)}', 'execution_time': 0.0, 'command': command, 'work_dir': work_dir or str(Path.cwd())}

@dataclass
class MultimodalStreamChunk(BaseStreamChunk):
    """
    Stream chunk for multimodal content.

    This class handles streaming of media content including:
    - Images (JPEG, PNG, GIF, WebP)
    - Audio files (MP3, WAV, etc.)
    - Video files (MP4, WebM, etc.)
    - Documents (PDF, etc.)
    - Generic files

    Supports both complete media and streaming/chunked media delivery.

    Attributes:
        type: ChunkType enum value (typically MEDIA or MEDIA_PROGRESS)
        text_content: Optional text caption or description
        media_type: Type of media (IMAGE, AUDIO, VIDEO, etc.)
        media_encoding: How the media is encoded (BASE64, URL, etc.)
        media_data: The actual media data (URL string, base64 string, bytes, or file_id)
        media_metadata: Metadata about the media
        attachments: List of multiple attachments (for batch processing)
        progress_percentage: Progress percentage for large media (0-100)
        bytes_transferred: Number of bytes transferred so far
        total_bytes: Total bytes to transfer
        is_partial: True if this is part of a larger media stream
        chunk_index: Index of this chunk in the stream
        total_chunks: Total number of expected chunks
        source: Source identifier
        timestamp: When the chunk was created
        sequence_number: Sequence number for ordering
    """
    text_content: Optional[str] = None
    media_type: Optional[MediaType] = None
    media_encoding: Optional[MediaEncoding] = None
    media_data: Optional[Any] = None
    media_metadata: Optional[MediaMetadata] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    progress_percentage: Optional[float] = None
    bytes_transferred: Optional[int] = None
    total_bytes: Optional[int] = None
    is_partial: bool = False
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary with proper serialization.

        Handles enum conversion and special types like bytes and MediaMetadata.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if key == 'type' and isinstance(value, ChunkType):
                    result[key] = value.value
                elif isinstance(value, (MediaType, MediaEncoding)):
                    result[key] = value.value
                elif isinstance(value, MediaMetadata):
                    result[key] = value.to_dict()
                elif isinstance(value, bytes):
                    import base64
                    result[key] = base64.b64encode(value).decode('utf-8')
                else:
                    result[key] = value
        return result

    def validate(self) -> bool:
        """
        Validate multimodal chunk integrity.

        Checks that required fields are present based on chunk type.

        Returns:
            True if chunk is valid, False otherwise.
        """
        if self.type == ChunkType.MEDIA:
            return self.media_type is not None and self.media_encoding is not None and (self.media_data is not None)
        elif self.type == ChunkType.MEDIA_PROGRESS:
            return self.progress_percentage is not None
        elif self.type == ChunkType.ATTACHMENT:
            return self.media_data is not None or self.attachments is not None
        elif self.type == ChunkType.ATTACHMENT_COMPLETE:
            return True
        return True

    def is_complete(self) -> bool:
        """
        Check if media streaming is complete.

        For non-partial chunks, always returns True.
        For partial chunks, checks if this is the last chunk.

        Returns:
            True if media is complete, False if more chunks expected.
        """
        if not self.is_partial:
            return True
        if self.chunk_index is not None and self.total_chunks is not None:
            return self.chunk_index >= self.total_chunks - 1
        return False

    def get_progress(self) -> Optional[float]:
        """
        Get progress percentage.

        Calculates progress from either:
        - Explicit progress_percentage field
        - bytes_transferred / total_bytes
        - chunk_index / total_chunks

        Returns:
            Progress percentage (0-100) or None if not available.
        """
        if self.progress_percentage is not None:
            return self.progress_percentage
        if self.bytes_transferred is not None and self.total_bytes is not None and (self.total_bytes > 0):
            return self.bytes_transferred / self.total_bytes * 100
        if self.chunk_index is not None and self.total_chunks is not None and (self.total_chunks > 0):
            return (self.chunk_index + 1) / self.total_chunks * 100
        return None

    def __repr__(self) -> str:
        """String representation for debugging."""
        parts = [f'MultimodalStreamChunk(type={self.type.value}']
        if self.media_type:
            parts.append(f'media_type={self.media_type.value}')
        if self.media_encoding:
            parts.append(f'encoding={self.media_encoding.value}')
        if self.text_content:
            parts.append(f"text='{self.text_content[:30]}...'")
        if self.is_partial:
            parts.append(f'partial={self.chunk_index}/{self.total_chunks}')
        progress = self.get_progress()
        if progress is not None:
            parts.append(f'progress={progress:.1f}%')
        if self.source:
            parts.append(f"source='{self.source}'")
        return ', '.join(parts) + ')'

def to_dict(self) -> Dict[str, Any]:
    """
        Convert to dictionary with proper serialization.

        Handles enum conversion and special types like bytes and MediaMetadata.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
    result = {}
    for key, value in self.__dict__.items():
        if value is not None:
            if key == 'type' and isinstance(value, ChunkType):
                result[key] = value.value
            elif isinstance(value, (MediaType, MediaEncoding)):
                result[key] = value.value
            elif isinstance(value, MediaMetadata):
                result[key] = value.to_dict()
            elif isinstance(value, bytes):
                import base64
                result[key] = base64.b64encode(value).decode('utf-8')
            else:
                result[key] = value
    return result

class RichTerminalDisplay(TerminalDisplay):
    """Enhanced terminal display using Rich library for beautiful formatting."""

    def __init__(self, agent_ids: List[str], **kwargs: Any) -> None:
        """Initialize rich terminal display.

        Args:
            agent_ids: List of agent IDs to display
            **kwargs: Additional configuration options
                - theme: Color theme ('dark', 'light', 'cyberpunk') (default: 'dark')
                - refresh_rate: Display refresh rate in Hz (default: 4)
                - enable_syntax_highlighting: Enable code syntax highlighting (default: True)
                - max_content_lines: Base lines per agent column before scrolling (default: 8)
                - show_timestamps: Show timestamps for events (default: True)
                - enable_status_jump: Enable jumping to latest status when agent status changes (default: True)
                - truncate_web_search_on_status_change: Truncate web search content when status changes (default: True)
                - max_web_search_lines_on_status_change: Max web search lines to keep on status changes (default: 3)
                - enable_flush_output: Enable flush output for final answer display (default: True)
                - flush_char_delay: Delay between characters in flush output (default: 0.03)
                - flush_word_delay: Extra delay after punctuation in flush output (default: 0.08)
        """
        if not RICH_AVAILABLE:
            raise ImportError('Rich library is required for RichTerminalDisplay. Install with: pip install rich')
        super().__init__(agent_ids, **kwargs)
        self._terminal_performance = self._detect_terminal_performance()
        self.refresh_rate = self._get_adaptive_refresh_rate(kwargs.get('refresh_rate'))
        self.theme = kwargs.get('theme', 'dark')
        self.enable_syntax_highlighting = kwargs.get('enable_syntax_highlighting', True)
        self.max_content_lines = kwargs.get('max_content_lines', 8)
        self.max_line_length = kwargs.get('max_line_length', 100)
        self.show_timestamps = kwargs.get('show_timestamps', True)
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.terminal_size = self.console.size
        self.num_agents = len(agent_ids)
        self.fixed_column_width = max(20, self.terminal_size.width // self.num_agents - 1)
        self.agent_panel_height = max(10, self.terminal_size.height - 13)
        self.orchestrator = kwargs.get('orchestrator', None)
        self._resize_lock = threading.Lock()
        self._setup_resize_handler()
        self.live = None
        self._lock = threading.RLock()
        self._last_update = 0
        self._update_interval = self._get_adaptive_update_interval()
        self._last_full_refresh = 0
        self._full_refresh_interval = self._get_adaptive_full_refresh_interval()
        self._refresh_times: List[float] = []
        self._dropped_frames = 0
        self._performance_check_interval = 5.0
        self._refresh_executor = ThreadPoolExecutor(max_workers=min(len(agent_ids) * 2 + 8, 20))
        self._agent_panels_cache: Dict[str, Panel] = {}
        self._header_cache = None
        self._footer_cache = None
        self._layout_update_lock = threading.Lock()
        self._pending_updates: set[str] = set()
        self._shutdown_flag = False
        self._priority_updates: set[str] = set()
        self._status_update_executor = ThreadPoolExecutor(max_workers=4)
        self._setup_theme()
        self._keyboard_interactive_mode = kwargs.get('keyboard_interactive_mode', True)
        self._safe_keyboard_mode = kwargs.get('safe_keyboard_mode', False)
        self._key_handler = None
        self._input_thread = None
        self._stop_input_thread = False
        self._original_settings = None
        self._agent_selector_active = False
        self._stored_final_presentation = None
        self._stored_presentation_agent = None
        self._stored_vote_results = None
        self._final_presentation_active = False
        self._final_presentation_content = ''
        self._final_presentation_agent = None
        self._final_presentation_vote_results = None
        self.code_patterns = ['```(\\w+)?\\n(.*?)\\n```', '`([^`]+)`', 'def\\s+\\w+\\s*\\(', 'class\\s+\\w+\\s*[:(\\s]', 'import\\s+\\w+', 'from\\s+\\w+\\s+import']
        self.agent_progress = {agent_id: 0 for agent_id in agent_ids}
        self.agent_activity = {agent_id: 'waiting' for agent_id in agent_ids}
        self._last_agent_status = {agent_id: 'waiting' for agent_id in agent_ids}
        self._last_agent_activity = {agent_id: 'waiting' for agent_id in agent_ids}
        self._last_content_hash = {agent_id: '' for agent_id in agent_ids}
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._debounce_delay = self._get_adaptive_debounce_delay()
        self._critical_updates: set[str] = set()
        self._normal_updates: set[str] = set()
        self._decorative_updates: set[str] = set()
        self._important_content_types = {'presentation', 'status', 'tool', 'error'}
        self._status_change_keywords = {'completed', 'failed', 'waiting', 'error', 'voted', 'voting', 'tool', 'vote recorded'}
        self._important_event_keywords = {'completed', 'failed', 'voting', 'voted', 'final', 'error', 'started', 'coordination', 'tool', 'vote recorded'}
        self._status_jump_enabled = kwargs.get('enable_status_jump', True)
        self._web_search_truncate_on_status_change = kwargs.get('truncate_web_search_on_status_change', True)
        self._max_web_search_lines = kwargs.get('max_web_search_lines_on_status_change', 3)
        self._enable_flush_output = kwargs.get('enable_flush_output', True)
        self._flush_char_delay = kwargs.get('flush_char_delay', 0.03)
        self._flush_word_delay = kwargs.get('flush_word_delay', 0.08)
        from massgen.logger_config import get_log_session_dir
        log_session_dir = get_log_session_dir()
        self.output_dir = kwargs.get('output_dir', log_session_dir / 'agent_outputs')
        self.agent_files: Dict[str, Path] = {}
        self.system_status_file = None
        self._selected_agent = None
        self._setup_agent_files()
        self._text_buffers = {agent_id: '' for agent_id in agent_ids}
        self._max_buffer_length = self._get_adaptive_buffer_length()
        self._buffer_timeout = self._get_adaptive_buffer_timeout()
        self._buffer_timers = {agent_id: None for agent_id in agent_ids}
        self._update_batch = set()
        self._batch_timer = None
        self._batch_timeout = self._get_adaptive_batch_timeout()

    def _setup_resize_handler(self) -> None:
        """Setup SIGWINCH signal handler for terminal resize detection."""
        if not sys.stdin.isatty():
            return
        try:
            signal.signal(signal.SIGWINCH, self._handle_resize_signal)
        except (AttributeError, OSError):
            pass

    def _handle_resize_signal(self, signum: int, frame: Any) -> None:
        """Handle SIGWINCH signal when terminal is resized."""
        threading.Thread(target=self._handle_terminal_resize, daemon=True).start()

    def _handle_terminal_resize(self) -> None:
        """Handle terminal resize by recalculating layout and refreshing display."""
        with self._resize_lock:
            try:
                if self._terminal_performance['type'] == 'vscode':
                    time.sleep(0.05)
                new_size = self.console.size
                if new_size.width != self.terminal_size.width or new_size.height != self.terminal_size.height:
                    self.terminal_size = new_size
                    if self._terminal_performance['type'] == 'vscode':
                        time.sleep(0.02)
                    self._recalculate_layout()
                    self._invalidate_display_cache()
                    with self._lock:
                        self._pending_updates.add('header')
                        self._pending_updates.add('footer')
                        self._pending_updates.update(self.agent_ids)
                        self._schedule_async_update(force_update=True)
                    time.sleep(0.1)
            except Exception:
                pass

    def _recalculate_layout(self) -> None:
        """Recalculate layout dimensions based on current terminal size."""
        self.fixed_column_width = max(20, self.terminal_size.width // self.num_agents - 1)
        self.agent_panel_height = max(10, self.terminal_size.height - 13)

    def _invalidate_display_cache(self) -> None:
        """Invalidate all cached display components to force refresh."""
        self._agent_panels_cache.clear()
        self._header_cache = None
        self._footer_cache = None

    def _setup_agent_files(self) -> None:
        """Setup individual txt files for each agent and system status file."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        for agent_id in self.agent_ids:
            file_path = Path(self.output_dir) / f'{agent_id}.txt'
            self.agent_files[agent_id] = file_path
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'=== {agent_id.upper()} OUTPUT LOG ===\n\n')
        self.system_status_file = Path(self.output_dir) / 'system_status.txt'
        with open(str(self.system_status_file), 'w', encoding='utf-8') as f:
            f.write('=== SYSTEM STATUS LOG ===\n\n')

    def _detect_terminal_performance(self) -> Dict[str, Any]:
        """Detect terminal performance characteristics for adaptive refresh rates."""
        terminal_info = {'type': 'unknown', 'performance_tier': 'medium', 'supports_unicode': True, 'supports_color': True, 'buffer_size': 'normal'}
        try:
            term = os.environ.get('TERM', '').lower()
            term_program = os.environ.get('TERM_PROGRAM', '').lower()
            if 'iterm.app' in term_program or 'iterm' in term_program.lower():
                terminal_info['performance_tier'] = 'high'
                terminal_info['type'] = 'iterm'
                terminal_info['supports_unicode'] = True
            elif 'vscode' in term_program or 'code' in term_program or self._detect_vscode_terminal():
                terminal_info['performance_tier'] = 'medium'
                terminal_info['type'] = 'vscode'
                terminal_info['supports_unicode'] = True
                terminal_info['buffer_size'] = 'large'
                terminal_info['needs_flush_delay'] = True
                terminal_info['refresh_stabilization'] = True
            elif 'apple_terminal' in term_program or term_program == 'terminal':
                terminal_info['performance_tier'] = 'high'
                terminal_info['type'] = 'macos_terminal'
                terminal_info['supports_unicode'] = True
            elif 'xterm-256color' in term or 'alacritty' in term_program:
                terminal_info['performance_tier'] = 'high'
                terminal_info['type'] = 'modern'
            elif 'screen' in term or 'tmux' in term:
                terminal_info['performance_tier'] = 'low'
                terminal_info['type'] = 'multiplexer'
            elif 'xterm' in term:
                terminal_info['performance_tier'] = 'medium'
                terminal_info['type'] = 'xterm'
            elif term in ['dumb', 'vt100', 'vt220']:
                terminal_info['performance_tier'] = 'low'
                terminal_info['type'] = 'legacy'
                terminal_info['supports_unicode'] = False
            if os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_CLIENT'):
                if terminal_info['performance_tier'] == 'high':
                    terminal_info['performance_tier'] = 'medium'
                elif terminal_info['performance_tier'] == 'medium':
                    terminal_info['performance_tier'] = 'low'
            colorterm = os.environ.get('COLORTERM', '').lower()
            if colorterm in ['truecolor', '24bit']:
                terminal_info['supports_color'] = True
            elif not self.console.is_terminal or term == 'dumb':
                terminal_info['supports_color'] = False
        except Exception:
            terminal_info['performance_tier'] = 'low'
        return terminal_info

    def _detect_vscode_terminal(self) -> bool:
        """Additional VSCode terminal detection using multiple indicators."""
        try:
            vscode_indicators = ['VSCODE_INJECTION', 'VSCODE_PID', 'VSCODE_IPC_HOOK', 'VSCODE_IPC_HOOK_CLI', 'TERM_PROGRAM_VERSION']
            for indicator in vscode_indicators:
                if os.environ.get(indicator):
                    return True
            try:
                import psutil
                current_process = psutil.Process()
                parent = current_process.parent()
                if parent and ('code' in parent.name().lower() or 'vscode' in parent.name().lower()):
                    return True
            except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            term_program = os.environ.get('TERM_PROGRAM', '').lower()
            if term_program and any((pattern in term_program for pattern in ['code', 'vscode'])):
                return True
            return False
        except Exception:
            return False

    def _get_adaptive_refresh_rate(self, user_override: Optional[int]=None) -> int:
        """Get adaptive refresh rate based on terminal performance."""
        if user_override is not None:
            return user_override
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        if term_type == 'vscode':
            return 2
        refresh_rates = {'high': 10, 'medium': 5, 'low': 2}
        return refresh_rates.get(perf_tier, 8)

    def _get_adaptive_update_interval(self) -> float:
        """Get adaptive update interval based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        intervals = {'high': 0.02, 'medium': 0.05, 'low': 0.1}
        return intervals.get(perf_tier, 0.05)

    def _get_adaptive_full_refresh_interval(self) -> float:
        """Get adaptive full refresh interval based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        intervals = {'high': 0.1, 'medium': 0.2, 'low': 0.5}
        return intervals.get(perf_tier, 0.2)

    def _get_adaptive_debounce_delay(self) -> float:
        """Get adaptive debounce delay based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        delays = {'high': 0.01, 'medium': 0.03, 'low': 0.05}
        base_delay = delays.get(perf_tier, 0.03)
        if term_type in ['iterm', 'macos_terminal']:
            base_delay *= 2.0
        return base_delay

    def _get_adaptive_buffer_length(self) -> int:
        """Get adaptive buffer length based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        lengths = {'high': 800, 'medium': 500, 'low': 200}
        base_length = lengths.get(perf_tier, 500)
        if term_type in ['iterm', 'macos_terminal']:
            base_length = min(base_length, 400)
        return base_length

    def _get_adaptive_buffer_timeout(self) -> float:
        """Get adaptive buffer timeout based on terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        term_type = self._terminal_performance['type']
        timeouts = {'high': 0.5, 'medium': 1.0, 'low': 2.0}
        base_timeout = timeouts.get(perf_tier, 1.0)
        if term_type in ['iterm', 'macos_terminal']:
            base_timeout *= 1.5
        return base_timeout

    def _get_adaptive_batch_timeout(self) -> float:
        """Get adaptive batch timeout for update batching."""
        perf_tier = self._terminal_performance['performance_tier']
        timeouts = {'high': 0.05, 'medium': 0.1, 'low': 0.2}
        return timeouts.get(perf_tier, 0.1)

    def _monitor_performance(self) -> None:
        """Monitor refresh performance and adjust if needed."""
        time.time()
        if len(self._refresh_times) > 20:
            self._refresh_times = self._refresh_times[-20:]
        if len(self._refresh_times) >= 5:
            avg_refresh_time = sum(self._refresh_times) / len(self._refresh_times)
            expected_refresh_time = 1.0 / self.refresh_rate
            if avg_refresh_time > expected_refresh_time * 2:
                self._dropped_frames += 1
                if self._dropped_frames >= 3:
                    self.refresh_rate = max(2, int(self.refresh_rate * 0.7))
                    self._dropped_frames = 0
                    self._update_interval = 1.0 / self.refresh_rate
                    self._full_refresh_interval *= 1.5
                    if self.live and self.live.is_started:
                        try:
                            self.live.refresh_per_second = self.refresh_rate
                        except Exception:
                            self._fallback_to_simple_display()

    def _create_live_display_with_fallback(self) -> Optional[Live]:
        """Create Live display with terminal compatibility checks and fallback."""
        try:
            if not self._test_terminal_capabilities():
                self._fallback_to_simple_display()
                return None
            live_settings = self._get_adaptive_live_settings()
            live = Live(self._create_layout(), console=self.console, **live_settings)
            try:
                live.start()
                live.stop()
                return live
            except Exception:
                self._fallback_to_simple_display()
                return None
        except Exception:
            self._fallback_to_simple_display()
            return None

    def _test_terminal_capabilities(self) -> bool:
        """Test if terminal supports rich Live display features."""
        try:
            if not self.console.is_terminal:
                return False
            perf_tier = self._terminal_performance['performance_tier']
            term_type = self._terminal_performance['type']
            if term_type == 'legacy' or perf_tier == 'low':
                term = os.environ.get('TERM', '').lower()
                if term in ['dumb', 'vt100']:
                    return False
            if term_type in ['iterm', 'macos_terminal']:
                return True
            test_size = self.console.size
            if test_size.width < 20 or test_size.height < 10:
                return False
            return True
        except Exception:
            return False

    def _get_adaptive_live_settings(self) -> Dict[str, Any]:
        """Get Live display settings adapted to terminal performance."""
        perf_tier = self._terminal_performance['performance_tier']
        settings = {'refresh_per_second': self.refresh_rate, 'vertical_overflow': 'ellipsis', 'transient': False}
        if perf_tier == 'low':
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 3)
            settings['transient'] = True
        elif perf_tier == 'medium':
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 8)
        if self._terminal_performance['type'] == 'multiplexer':
            settings['auto_refresh'] = False
        if self._terminal_performance['type'] in ['iterm', 'macos_terminal']:
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 5)
            settings['transient'] = False
            settings['vertical_overflow'] = 'ellipsis'
        if self._terminal_performance['type'] == 'vscode':
            current_rate = settings['refresh_per_second']
            assert isinstance(current_rate, int)
            settings['refresh_per_second'] = min(current_rate, 6)
            settings['transient'] = False
            settings['vertical_overflow'] = 'ellipsis'
            settings['auto_refresh'] = True
        return settings

    def _fallback_to_simple_display(self) -> None:
        """Fallback to simple console output when Live display is not supported."""
        self._simple_display_mode = True
        try:
            self.console.print('\n[yellow]Terminal compatibility: Using simple display mode[/yellow]')
            self.console.print(f'[dim]Monitoring {len(self.agent_ids)} agents...[/dim]\n')
        except Exception:
            print('\nUsing simple display mode...')
            print(f'Monitoring {len(self.agent_ids)} agents...\n')
        return None

    def _update_display_safe(self) -> None:
        """Safely update display with fallback support and terminal-specific synchronization."""
        term_type = self._terminal_performance['type']
        use_safe_mode = term_type in ['iterm', 'macos_terminal', 'vscode']
        if term_type == 'vscode' and self._terminal_performance.get('refresh_stabilization'):
            time.sleep(0.01)
        try:
            if use_safe_mode:
                with self._layout_update_lock:
                    with self._lock:
                        if hasattr(self, '_simple_display_mode') and self._simple_display_mode:
                            self._update_simple_display()
                        else:
                            self._update_live_display_safe()
            else:
                with self._layout_update_lock:
                    if hasattr(self, '_simple_display_mode') and self._simple_display_mode:
                        self._update_simple_display()
                    else:
                        self._update_live_display()
        except Exception:
            self._fallback_to_simple_display()
        if term_type == 'vscode' and self._terminal_performance.get('needs_flush_delay'):
            time.sleep(0.005)

    def _update_simple_display(self) -> None:
        """Update display in simple mode without Live."""
        try:
            current_time = time.time()
            if not hasattr(self, '_last_simple_update'):
                self._last_simple_update = 0
            if current_time - self._last_simple_update > 2.0:
                status_line = f'[{time.strftime('%H:%M:%S')}] Agents: '
                for agent_id in self.agent_ids:
                    status = self.agent_status.get(agent_id, 'waiting')
                    status_line += f'{agent_id}:{status} '
                try:
                    self.console.print(f'\r{status_line[:80]}', end='')
                except Exception:
                    print(f'\r{status_line[:80]}', end='')
                self._last_simple_update = current_time
        except Exception:
            pass

    def _update_live_display(self) -> None:
        """Update Live display mode."""
        try:
            if self.live:
                self.live.update(self._create_layout())
        except Exception:
            self._fallback_to_simple_display()

    def _update_live_display_safe(self) -> None:
        """Update Live display mode with extra safety for macOS terminals."""
        try:
            if self.live and self.live.is_started:
                import time
                time.sleep(0.001)
                self.live.update(self._create_layout())
            elif self.live:
                try:
                    self.live.start()
                    self.live.update(self._create_layout())
                except Exception:
                    self._fallback_to_simple_display()
        except Exception:
            self._fallback_to_simple_display()

    def _setup_theme(self) -> None:
        """Setup color theme configuration."""
        unified_colors = {'primary': '#0066CC', 'secondary': '#4A90E2', 'success': '#00AA44', 'warning': '#CC6600', 'error': '#CC0000', 'info': '#6633CC', 'text': 'default', 'border': '#4A90E2', 'panel_style': '#4A90E2', 'header_style': 'bold #0066CC'}
        themes = {'dark': unified_colors.copy(), 'light': unified_colors.copy(), 'cyberpunk': {'primary': 'bright_magenta', 'secondary': 'bright_cyan', 'success': 'bright_green', 'warning': 'bright_yellow', 'error': 'bright_red', 'info': 'bright_blue', 'text': 'bright_white', 'border': 'bright_magenta', 'panel_style': 'bright_magenta', 'header_style': 'bold bright_magenta'}}
        self.colors = themes.get(self.theme, themes['dark'])
        if self._terminal_performance['type'] == 'vscode':
            vscode_adjustments = {'primary': '#0066CC', 'secondary': '#4A90E2', 'border': '#4A90E2', 'panel_style': '#4A90E2'}
            self.colors.update(vscode_adjustments)
            self._setup_vscode_emoji_fallbacks()

    def _setup_vscode_emoji_fallbacks(self) -> None:
        """Setup emoji fallbacks for VSCode terminal compatibility."""
        self._emoji_fallbacks = {'🚀': '>>', '🎯': '>', '💭': '...', '⚡': '!', '🎨': '*', '📝': '=', '✅': '[OK]', '❌': '[X]', '⭐': '*', '🔍': '?', '📊': '|'}
        if not self._terminal_performance.get('supports_unicode', True):
            self._use_emoji_fallbacks = True
        else:
            self._use_emoji_fallbacks = False

    def _safe_emoji(self, emoji: str) -> str:
        """Get safe emoji for current terminal, with VSCode fallbacks."""
        if self._terminal_performance['type'] == 'vscode' and self._use_emoji_fallbacks and (emoji in self._emoji_fallbacks):
            return self._emoji_fallbacks[emoji]
        return emoji

    def initialize(self, question: str, log_filename: Optional[str]=None) -> None:
        """Initialize the rich display with question and optional log file."""
        self.log_filename = log_filename
        self.question = question
        self.console.clear()
        from massgen.logger_config import suppress_console_logging
        suppress_console_logging()
        self._create_initial_display()
        if self._keyboard_interactive_mode:
            self._setup_keyboard_handler()
        self.live = self._create_live_display_with_fallback()
        if self.live:
            self.live.start()
        self._write_system_status()

    def _create_initial_display(self) -> None:
        """Create the initial welcome display."""
        welcome_text = Text()
        welcome_text.append('🚀 MassGen Coordination Dashboard 🚀\n', style=self.colors['header_style'])
        welcome_text.append(f'Multi-Agent System with {len(self.agent_ids)} agents\n', style=self.colors['primary'])
        if self.log_filename:
            welcome_text.append(f'📁 Log: {self.log_filename}\n', style=self.colors['info'])
        welcome_text.append(f'🎨 Theme: {self.theme.title()}', style=self.colors['secondary'])
        welcome_panel = Panel(welcome_text, box=DOUBLE, border_style=self.colors['border'], title='[bold]Welcome[/bold]', title_align='center')
        self.console.print(welcome_panel)
        self.console.print()

    def _create_layout(self) -> Layout:
        """Create the main layout structure with cached components."""
        layout = Layout()
        header = self._header_cache if self._header_cache else self._create_header()
        agent_columns = self._create_agent_columns_from_cache()
        footer = self._footer_cache if self._footer_cache else self._create_footer()
        if self._final_presentation_active:
            presentation_panel = self._create_final_presentation_panel()
            layout.split_column(Layout(presentation_panel, name='presentation'), Layout(footer, name='footer', size=8))
        else:
            layout.split_column(Layout(header, name='header', size=5), Layout(agent_columns, name='main'), Layout(footer, name='footer', size=8))
        return layout

    def _create_agent_columns_from_cache(self) -> Columns:
        """Create agent columns using cached panels with fixed widths."""
        agent_panels = []
        for agent_id in self.agent_ids:
            if agent_id in self._agent_panels_cache:
                agent_panels.append(self._agent_panels_cache[agent_id])
            else:
                panel = self._create_agent_panel(agent_id)
                self._agent_panels_cache[agent_id] = panel
                agent_panels.append(panel)
        return Columns(agent_panels, equal=False, expand=False, width=self.fixed_column_width)

    def _create_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append('🚀 MassGen Multi-Agent Coordination System', style=self.colors['header_style'])
        if hasattr(self, 'question'):
            header_text.append(f'\n💡 Question: {self.question}', style=self.colors['info'])
        return Panel(Align.center(header_text), box=ROUNDED, border_style=self.colors['border'], height=5)

    def _create_agent_columns(self) -> Columns:
        """Create columns for each agent with fixed widths."""
        agent_panels = []
        for agent_id in self.agent_ids:
            panel = self._create_agent_panel(agent_id)
            agent_panels.append(panel)
        return Columns(agent_panels, equal=False, expand=False, width=self.fixed_column_width)

    def _setup_keyboard_handler(self) -> None:
        """Setup keyboard handler for interactive agent selection."""
        try:
            self._agent_keys = {}
            for i, agent_id in enumerate(self.agent_ids):
                key = str(i + 1)
                self._agent_keys[key] = agent_id
            if self._keyboard_interactive_mode:
                self._start_input_thread()
        except ImportError:
            self._keyboard_interactive_mode = False

    def _start_input_thread(self) -> None:
        """Start background thread for keyboard input during Live mode."""
        if not sys.stdin.isatty():
            return
        self._stop_input_thread = False
        term_type = self._terminal_performance['type']
        if self._safe_keyboard_mode or term_type in ['iterm', 'macos_terminal']:
            self._input_thread = threading.Thread(target=self._input_thread_worker_safe, daemon=True)
            self._input_thread.start()
        else:
            try:
                self._input_thread = threading.Thread(target=self._input_thread_worker_improved, daemon=True)
                self._input_thread.start()
            except Exception:
                self._input_thread = threading.Thread(target=self._input_thread_worker_fallback, daemon=True)
                self._input_thread.start()

    def _input_thread_worker_improved(self) -> None:
        """Improved background thread worker that doesn't interfere with Rich rendering."""
        if not UNIX_TERMINAL_SUPPORT:
            return self._input_thread_worker_fallback()
        try:
            if sys.stdin.isatty():
                self._original_settings = termios.tcgetattr(sys.stdin.fileno())
                new_settings = termios.tcgetattr(sys.stdin.fileno())
                new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
                new_settings[6][termios.VMIN] = 0
                new_settings[6][termios.VTIME] = 1
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_settings)
            while not self._stop_input_thread:
                try:
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        char = sys.stdin.read(1)
                        if char:
                            self._handle_key_press(char)
                except (BlockingIOError, OSError):
                    continue
        except (KeyboardInterrupt, EOFError):
            pass
        except Exception:
            pass
        finally:
            self._restore_terminal_settings()

    def _input_thread_worker_fallback(self) -> None:
        """Fallback keyboard input method using simple polling without terminal mode changes."""
        import time
        self.console.print('\n[dim]Keyboard support active. Press keys during Live display:[/dim]')
        self.console.print("[dim]1-{} to open agent files, 's' for system status, 'q' to quit[/dim]\n".format(len(self.agent_ids)))
        try:
            while not self._stop_input_thread:
                time.sleep(0.1)
        except (KeyboardInterrupt, EOFError):
            pass
        except Exception:
            pass

    def _input_thread_worker_safe(self) -> None:
        """Completely safe keyboard input that never changes terminal settings."""
        try:
            while not self._stop_input_thread:
                time.sleep(0.5)
        except Exception:
            pass

    def _restore_terminal_settings(self) -> None:
        """Restore original terminal settings."""
        try:
            if UNIX_TERMINAL_SUPPORT and sys.stdin.isatty():
                if self._original_settings:
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
                    self._original_settings = None
                else:
                    try:
                        current = termios.tcgetattr(sys.stdin.fileno())
                        current[3] = current[3] | termios.ECHO | termios.ICANON
                        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, current)
                    except Exception:
                        pass
        except Exception:
            pass

    def _ensure_clean_keyboard_state(self) -> None:
        """Ensure clean keyboard state before starting agent selector."""
        self._stop_input_thread = True
        if self._input_thread and self._input_thread.is_alive():
            try:
                self._input_thread.join(timeout=0.5)
            except Exception:
                pass
        self._restore_terminal_settings()
        try:
            if UNIX_TERMINAL_SUPPORT and sys.stdin.isatty():
                termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass
        import time
        time.sleep(0.1)

    def _handle_key_press(self, key: str) -> None:
        """Handle key press events for agent selection."""
        if key in self._agent_keys:
            agent_id = self._agent_keys[key]
            self._open_agent_in_default_text_editor(agent_id)
        elif key == 's':
            self._open_system_status_in_default_text_editor()
        elif key == 'f':
            self._open_final_presentation_in_default_text_editor()
        elif key == 'q':
            self._stop_input_thread = True
            self._restore_terminal_settings()

    def _open_agent_in_default_text_editor(self, agent_id: str) -> None:
        """Open agent's txt file in default text editor."""
        if agent_id not in self.agent_files:
            return
        file_path = self.agent_files[agent_id]
        if not file_path.exists():
            return
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(file_path)], check=False)
            elif sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(file_path)], check=False)
            elif sys.platform == 'win32':
                subprocess.run(['start', str(file_path)], check=False, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_agent_in_external_app(agent_id)

    def _open_agent_in_vscode_new_window(self, agent_id: str) -> None:
        """Open agent's txt file in a new VS Code window."""
        if agent_id not in self.agent_files:
            return
        file_path = self.agent_files[agent_id]
        if not file_path.exists():
            return
        try:
            subprocess.run(['code', '--new-window', str(file_path)], check=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_agent_in_external_app(agent_id)

    def _open_system_status_in_default_text_editor(self) -> None:
        """Open system status file in default text editor."""
        if not self.system_status_file or not self.system_status_file.exists():
            return
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(self.system_status_file)], check=False)
            elif sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(self.system_status_file)], check=False)
            elif sys.platform == 'win32':
                subprocess.run(['start', str(self.system_status_file)], check=False, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_system_status_in_external_app()

    def _open_final_presentation_in_default_text_editor(self) -> None:
        """Open final presentation file in default text editor."""
        final_presentation_file = None
        if hasattr(self, '_final_presentation_file_path') and self._final_presentation_file_path:
            final_presentation_file = self._final_presentation_file_path
        elif hasattr(self, '_stored_presentation_agent') and self._stored_presentation_agent:
            agent_name = self._stored_presentation_agent
            final_presentation_file = self.output_dir / f'{agent_name}_final_presentation.txt'
        else:
            return
        if not final_presentation_file.exists():
            return
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(final_presentation_file)], check=False)
            elif sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(final_presentation_file)], check=False)
            elif sys.platform == 'win32':
                subprocess.run(['start', str(final_presentation_file)], check=False, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    def _open_system_status_in_vscode_new_window(self) -> None:
        """Open system status file in a new VS Code window."""
        if not self.system_status_file or not self.system_status_file.exists():
            return
        try:
            subprocess.run(['code', '--new-window', str(self.system_status_file)], check=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._open_system_status_in_external_app()

    def _open_agent_in_external_app(self, agent_id: str) -> None:
        """Open agent's txt file in external editor or terminal viewer."""
        if agent_id not in self.agent_files:
            return
        file_path = self.agent_files[agent_id]
        if not file_path.exists():
            return
        try:
            if sys.platform == 'darwin':
                editors = ['code', 'subl', 'atom', 'nano', 'vim', 'open']
                for editor in editors:
                    try:
                        if editor == 'open':
                            subprocess.run(['open', '-a', 'TextEdit', str(file_path)], check=False)
                        else:
                            subprocess.run([editor, str(file_path)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform.startswith('linux'):
                editors = ['code', 'gedit', 'kate', 'nano', 'vim', 'xdg-open']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(file_path)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform == 'win32':
                editors = ['code', 'notepad++', 'notepad']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(file_path)], check=False, shell=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
        except Exception:
            pass

    def _open_system_status_in_external_app(self) -> None:
        """Open system status file in external editor or terminal viewer."""
        if not self.system_status_file or not self.system_status_file.exists():
            return
        try:
            if sys.platform == 'darwin':
                editors = ['code', 'subl', 'atom', 'nano', 'vim', 'open']
                for editor in editors:
                    try:
                        if editor == 'open':
                            subprocess.run(['open', '-a', 'TextEdit', str(self.system_status_file)], check=False)
                        else:
                            subprocess.run([editor, str(self.system_status_file)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform.startswith('linux'):
                editors = ['code', 'gedit', 'kate', 'nano', 'vim', 'xdg-open']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(self.system_status_file)], check=False)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif sys.platform == 'win32':
                editors = ['code', 'notepad++', 'notepad']
                for editor in editors:
                    try:
                        subprocess.run([editor, str(self.system_status_file)], check=False, shell=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
        except Exception:
            pass

    def _show_agent_full_content(self, agent_id: str) -> None:
        """Display full content of selected agent from txt file."""
        if agent_id not in self.agent_files:
            return
        try:
            file_path = self.agent_files[agent_id]
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '[' in content:
                        content = content.replace('[', '\\[')
                self.console.print('\n' + '=' * 80 + '\n')
                header_text = Text()
                header_text.append(f'📄 {agent_id.upper()} - Full Content', style=self.colors['header_style'])
                header_text.append('\nPress any key to return to main view', style=self.colors['info'])
                header_panel = Panel(header_text, box=DOUBLE, border_style=self.colors['border'])
                content_panel = Panel(content, title=f'[bold]{agent_id.upper()} Output[/bold]', border_style=self.colors['border'], box=ROUNDED)
                self.console.print(header_panel)
                self.console.print(content_panel)
                input('Press Enter to return to agent selector...')
                self.console.print('\n' + '=' * 80 + '\n')
        except Exception:
            pass

    def show_agent_selector(self) -> None:
        """Show agent selector and handle user input."""
        if not self._keyboard_interactive_mode or not hasattr(self, '_agent_keys'):
            return
        if self._agent_selector_active:
            return
        self._agent_selector_active = True
        self._ensure_clean_keyboard_state()
        try:
            loop_count = 0
            while True:
                loop_count += 1
                options_text = Text()
                options_text.append("This is a system inspection interface for diving into the multi-agent collaboration behind the scenes in MassGen. It lets you examine each agent's original output and compare it to the final MassGen answer in terms of quality. You can explore the detailed communication, collaboration, voting, and decision-making process.\n", style=self.colors['text'])
                options_text.append('\n🎮 Select an agent to view full output:\n', style=self.colors['primary'])
                for key, agent_id in self._agent_keys.items():
                    options_text.append(f'  {key}: ', style=self.colors['warning'])
                    options_text.append('Inspect the original answer and working log of agent ', style=self.colors['text'])
                    options_text.append(f'{agent_id}\n', style=self.colors['warning'])
                options_text.append('  s: Inspect the orchestrator working log including the voting process\n', style=self.colors['warning'])
                options_text.append('  r: Display coordination table to see the full history of agent interactions and decisions\n', style=self.colors['warning'])
                if self._stored_final_presentation and self._stored_presentation_agent:
                    options_text.append(f'  f: Show final presentation from Selected Agent ({self._stored_presentation_agent})\n', style=self.colors['success'])
                options_text.append('  q: Quit Inspection\n', style=self.colors['info'])
                self.console.print(Panel(options_text, title='[bold]Agent Selector[/bold]', border_style=self.colors['border']))
                try:
                    choice = input('Enter your choice: ').strip().lower()
                    if choice in self._agent_keys:
                        self._show_agent_full_content(self._agent_keys[choice])
                    elif choice == 's':
                        self._show_system_status()
                    elif choice == 'r':
                        self.display_coordination_table()
                    elif choice == 'f' and self._stored_final_presentation:
                        self._redisplay_final_presentation()
                    elif choice == 'q':
                        break
                    else:
                        self.console.print(f'[{self.colors['error']}]Invalid choice. Please try again.[/{self.colors['error']}]')
                except KeyboardInterrupt:
                    break
        finally:
            self._agent_selector_active = True

    def _redisplay_final_presentation(self) -> None:
        """Redisplay the stored final presentation."""
        if not self._stored_final_presentation or not self._stored_presentation_agent:
            self.console.print(f'[{self.colors['error']}]No final presentation stored.[/{self.colors['error']}]')
            return
        self.console.print('\n' + '=' * 80 + '\n')
        self._display_final_presentation_content(self._stored_presentation_agent, self._stored_final_presentation)
        input('\nPress Enter to return to agent selector...')
        self.console.print('\n' + '=' * 80 + '\n')

    def _show_coordination_rounds_table(self) -> None:
        """Display the coordination rounds table with rich formatting."""
        self.display_coordination_table()

    def _show_system_status(self) -> None:
        """Display system status from txt file."""
        if not self.system_status_file or not self.system_status_file.exists():
            self.console.print(f'[{self.colors['error']}]System status file not found.[/{self.colors['error']}]')
            return
        try:
            with open(self.system_status_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '[' in content:
                    content = content.replace('[', '\\[')
            self.console.print('\n' + '=' * 80 + '\n')
            header_text = Text()
            header_text.append('📊 SYSTEM STATUS - Full Log', style=self.colors['header_style'])
            header_text.append('\nPress any key to return to agent selector', style=self.colors['info'])
            header_panel = Panel(header_text, box=DOUBLE, border_style=self.colors['border'])
            content_panel = Panel(content, title='[bold]System Status Log[/bold]', border_style=self.colors['border'], box=ROUNDED)
            self.console.print(header_panel)
            self.console.print(content_panel)
            input('Press Enter to return to agent selector...')
            self.console.print('\n' + '=' * 80 + '\n')
        except Exception as e:
            self.console.print(f'[{self.colors['error']}]Error reading system status file: {e}[/{self.colors['error']}]')

    def _create_agent_panel(self, agent_id: str) -> Panel:
        """Create a panel for a specific agent."""
        agent_content = self.agent_outputs.get(agent_id, [])
        status = self.agent_status.get(agent_id, 'waiting')
        activity = self.agent_activity.get(agent_id, 'waiting')
        content_text = Text()
        max_lines = max(0, self.agent_panel_height - 3)
        if not agent_content:
            content_text.append('No activity yet...', style=self.colors['text'])
        else:
            for line in agent_content[-max_lines:]:
                formatted_line = self._format_content_line(line)
                content_text.append(formatted_line)
                content_text.append('\n')
        status_emoji = self._get_status_emoji(status, activity)
        status_color = self._get_status_color(status)
        backend_name = self._get_backend_name(agent_id)
        title = f'{status_emoji} {agent_id.upper()}'
        if backend_name != 'Unknown':
            title += f' ({backend_name})'
        if self._keyboard_interactive_mode and hasattr(self, '_agent_keys'):
            agent_key = next((k for k, v in self._agent_keys.items() if v == agent_id), None)
            if agent_key:
                title += f' [Press {agent_key}]'
        return Panel(content_text, title=f'[{status_color}]{title}[/{status_color}]', border_style=status_color, box=ROUNDED, height=self.agent_panel_height, width=self.fixed_column_width)

    def _format_content_line(self, line: str) -> Text:
        """Format a content line with syntax highlighting and styling."""
        formatted = Text()
        if not line.strip():
            return formatted
        if self._is_web_search_content(line):
            return self._format_web_search_line(line)
        is_error_message = any((error_indicator in line for error_indicator in ['❌ Error:', 'Error:', 'Exception:', 'Traceback', '❌']))
        if len(line) > self.max_line_length and (not is_error_message):
            wrapped_lines = []
            remaining = line
            while len(remaining) > self.max_line_length:
                break_point = remaining[:self.max_line_length].rfind(' ')
                if break_point == -1:
                    break_point = self.max_line_length
                wrapped_lines.append(remaining[:break_point])
                remaining = remaining[break_point:].lstrip()
            if remaining:
                wrapped_lines.append(remaining)
            line = '\n'.join(wrapped_lines)
        if line.startswith('→'):
            formatted.append('→ ', style=self.colors['warning'])
            formatted.append(line[2:], style=self.colors['text'])
        elif line.startswith('🎤'):
            formatted.append('🎤 ', style=self.colors['success'])
            formatted.append(line[3:], style=f'bold {self.colors['success']}')
        elif line.startswith('⚡'):
            formatted.append('⚡ ', style=self.colors['warning'])
            if 'jumped to latest' in line:
                formatted.append(line[3:], style=f'bold {self.colors['info']}')
            else:
                formatted.append(line[3:], style=f'italic {self.colors['warning']}')
        elif self._is_code_content(line):
            if self.enable_syntax_highlighting:
                formatted = self._apply_syntax_highlighting(line)
            else:
                formatted.append(line, style=f'bold {self.colors['info']}')
        else:
            formatted.append(line, style=self.colors['text'])
        return formatted

    def _create_final_presentation_panel(self) -> Panel:
        """Create a panel for the final presentation display."""
        if not self._final_presentation_active:
            return None
        content_text = Text()
        if not self._final_presentation_content:
            content_text.append('No activity yet...', style=self.colors['text'])
        else:
            lines = self._final_presentation_content.split('\n')
            available_height = max(10, self.terminal_size.height - 16)
            display_lines = lines[-available_height:] if len(lines) > available_height else lines
            for line in display_lines:
                if line.strip():
                    formatted_line = self._format_content_line(line)
                    content_text.append(formatted_line)
                content_text.append('\n')
        title = f'🎤 Final Presentation from {self._final_presentation_agent}'
        if self._final_presentation_vote_results and self._final_presentation_vote_results.get('vote_counts'):
            vote_count = self._final_presentation_vote_results['vote_counts'].get(self._final_presentation_agent, 0)
            title += f' (Selected with {vote_count} votes)'
        title += ' [Press f]'
        return Panel(content_text, title=f'[{self.colors['success']}]{title}[/{self.colors['success']}]', border_style=self.colors['success'], box=DOUBLE, expand=True)

    def _format_presentation_content(self, content: str) -> Text:
        """Format presentation content with enhanced styling for orchestrator queries."""
        formatted = Text()
        lines = content.split('\n') if '\n' in content else [content]
        for line in lines:
            if not line.strip():
                formatted.append('\n')
                continue
            if line.startswith('**') and line.endswith('**'):
                clean_line = line.strip('*').strip()
                formatted.append(clean_line, style=f'bold {self.colors['success']}')
            elif line.startswith('- ') or line.startswith('• '):
                formatted.append(line[:2], style=self.colors['primary'])
                formatted.append(line[2:], style=self.colors['text'])
            elif line.startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                clean_header = line.lstrip('# ').strip()
                if header_level <= 2:
                    formatted.append(clean_header, style=f'bold {self.colors['header_style']}')
                else:
                    formatted.append(clean_header, style=f'bold {self.colors['primary']}')
            elif self._is_code_content(line):
                if self.enable_syntax_highlighting:
                    formatted.append(self._apply_syntax_highlighting(line))
                else:
                    formatted.append(line, style=f'bold {self.colors['info']}')
            else:
                formatted.append(line, style=self.colors['text'])
            if line != lines[-1]:
                formatted.append('\n')
        return formatted

    def _is_web_search_content(self, line: str) -> bool:
        """Check if content is from web search and needs special formatting."""
        web_search_indicators = ['[Provider Tool: Web Search]', '🔍 [Search Query]', '✅ [Provider Tool: Web Search]', '🔍 [Provider Tool: Web Search]']
        return any((indicator in line for indicator in web_search_indicators))

    def _format_web_search_line(self, line: str) -> Text:
        """Format web search content with better truncation and styling."""
        formatted = Text()
        if '[Provider Tool: Web Search] Starting search' in line:
            formatted.append('🔍 ', style=self.colors['info'])
            formatted.append('Web search starting...', style=self.colors['text'])
        elif '[Provider Tool: Web Search] Searching' in line:
            formatted.append('🔍 ', style=self.colors['warning'])
            formatted.append('Searching...', style=self.colors['text'])
        elif '[Provider Tool: Web Search] Search completed' in line:
            formatted.append('✅ ', style=self.colors['success'])
            formatted.append('Search completed', style=self.colors['text'])
        elif any((pattern in line for pattern in ['🔍 [Search Query]', 'Search Query:', '[Search Query]'])):
            query = None
            patterns = [('🔍 [Search Query]', ''), ('[Search Query]', ''), ('Search Query:', ''), ('Query:', '')]
            for pattern, _ in patterns:
                if pattern in line:
                    parts = line.split(pattern, 1)
                    if len(parts) > 1:
                        query = parts[1].strip().strip('\'"').strip()
                        break
            if query:
                formatted.append('🔍 Search: ', style=self.colors['info'])
                formatted.append(f'"{query}"', style=f'italic {self.colors['text']}')
            else:
                formatted.append('🔍 Search query', style=self.colors['info'])
        else:
            max_web_length = min(self.max_line_length // 2, 60)
            if len(line) > max_web_length:
                truncated = line[:max_web_length]
                for break_char in ['. ', '! ', '? ', ', ', ': ']:
                    last_break = truncated.rfind(break_char)
                    if last_break > max_web_length // 2:
                        truncated = truncated[:last_break + 1]
                        break
                line = truncated + '...'
            formatted.append(line, style=self.colors['text'])
        return formatted

    def _should_filter_content(self, content: str, content_type: str) -> bool:
        """Determine if content should be filtered out to reduce noise."""
        if content_type in ['status', 'presentation', 'error']:
            return False
        if len(content) > 1000 and self._is_web_search_content(content):
            url_count = content.count('http')
            technical_indicators = content.count('[') + content.count(']') + content.count('(') + content.count(')')
            if url_count > 5 or technical_indicators > len(content) * 0.1:
                return True
        return False

    def _should_filter_line(self, line: str) -> bool:
        """Determine if a specific line should be filtered out."""
        filter_patterns = ['^\\s*\\([^)]+\\)\\s*$', '^\\s*\\[[^\\]]+\\]\\s*$', '^\\s*https?://\\S+\\s*$', '^\\s*\\.\\.\\.\\s*$']
        for pattern in filter_patterns:
            if re.match(pattern, line):
                return True
        return False

    def _truncate_web_search_content(self, agent_id: str) -> None:
        """Truncate web search content when important status updates occur."""
        if agent_id not in self.agent_outputs or not self.agent_outputs[agent_id]:
            return
        content_lines = self.agent_outputs[agent_id]
        web_search_lines = []
        non_web_search_lines = []
        for line in content_lines:
            if self._is_web_search_content(line):
                web_search_lines.append(line)
            else:
                non_web_search_lines.append(line)
        if len(web_search_lines) > self._max_web_search_lines:
            truncated_web_search = web_search_lines[:1] + ['🔍 ... (web search content truncated due to status update) ...'] + web_search_lines[-(self._max_web_search_lines - 2):]
            recent_non_web = non_web_search_lines[-max(5, self.max_content_lines - len(truncated_web_search)):]
            self.agent_outputs[agent_id] = recent_non_web + truncated_web_search
        if len(web_search_lines) > self._max_web_search_lines:
            self.agent_outputs[agent_id].append('⚡  Status updated - jumped to latest')

    def _is_code_content(self, content: str) -> bool:
        """Check if content appears to be code."""
        for pattern in self.code_patterns:
            if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                return True
        return False

    def _apply_syntax_highlighting(self, content: str) -> Text:
        """Apply syntax highlighting to content."""
        try:
            language = self._detect_language(content)
            if language:
                return Text(content, style=f'bold {self.colors['info']}')
            else:
                return Text(content, style=f'bold {self.colors['info']}')
        except Exception:
            return Text(content, style=f'bold {self.colors['info']}')

    def _detect_language(self, content: str) -> Optional[str]:
        """Detect programming language from content."""
        content_lower = content.lower()
        if any((keyword in content_lower for keyword in ['def ', 'import ', 'class ', 'python'])):
            return 'python'
        elif any((keyword in content_lower for keyword in ['function', 'var ', 'let ', 'const '])):
            return 'javascript'
        elif any((keyword in content_lower for keyword in ['<', '>', 'html', 'div'])):
            return 'html'
        elif any((keyword in content_lower for keyword in ['{', '}', 'json'])):
            return 'json'
        return None

    def _get_status_emoji(self, status: str, activity: str) -> str:
        """Get emoji for agent status."""
        if status == 'working':
            return '🔄'
        elif status == 'completed':
            if 'voted' in activity.lower():
                return '🗳️'
            elif 'failed' in activity.lower():
                return '❌'
            else:
                return '✅'
        elif status == 'waiting':
            return '⏳'
        else:
            return '❓'

    def _get_status_color(self, status: str) -> str:
        """Get color for agent status."""
        status_colors = {'working': self.colors['warning'], 'completed': self.colors['success'], 'waiting': self.colors['info'], 'failed': self.colors['error']}
        return status_colors.get(status, self.colors['text'])

    def _get_backend_name(self, agent_id: str) -> str:
        """Get backend name for agent."""
        try:
            if hasattr(self, 'orchestrator') and self.orchestrator and hasattr(self.orchestrator, 'agents'):
                agent = self.orchestrator.agents.get(agent_id)
                if agent and hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                    return agent.backend.get_provider_name()
        except Exception:
            pass
        return 'Unknown'

    def _create_footer(self) -> Panel:
        """Create the footer panel with status and events."""
        footer_content = Text()
        footer_content.append('📊 Agent Status: ', style=self.colors['primary'])
        status_counts = {}
        for status in self.agent_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        status_parts = []
        for status, count in status_counts.items():
            emoji = self._get_status_emoji(status, status)
            status_parts.append(f'{emoji} {status.title()}: {count}')
        if self._final_presentation_active:
            status_parts.append('🎤 Final Presentation: Active')
        elif hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
            status_parts.append('🎤 Final Presentation: Complete')
        footer_content.append(' | '.join(status_parts), style=self.colors['text'])
        footer_content.append('\n')
        if self.orchestrator_events:
            footer_content.append('📋 Recent Events:\n', style=self.colors['primary'])
            recent_events = self.orchestrator_events[-3:]
            for event in recent_events:
                footer_content.append(f'  • {event}\n', style=self.colors['text'])
        if self.log_filename:
            footer_content.append(f'📁 Log: {self.log_filename}\n', style=self.colors['info'])
        if self._keyboard_interactive_mode and hasattr(self, '_agent_keys'):
            if self._safe_keyboard_mode:
                footer_content.append('📂 Safe Mode: Keyboard disabled to prevent rendering issues\n', style=self.colors['warning'])
                footer_content.append(f'Output files saved in: {self.output_dir}/', style=self.colors['info'])
            else:
                footer_content.append('🎮 Live Mode Hotkeys: Press 1-', style=self.colors['primary'])
                hotkeys = f"{len(self.agent_ids)} to open agent files in editor, 's' for system status"
                if hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
                    hotkeys += ", 'f' for final presentation"
                footer_content.append(hotkeys, style=self.colors['text'])
                footer_content.append(f'\n📂 Output files saved in: {self.output_dir}/', style=self.colors['info'])
        return Panel(footer_content, title='[bold]System Status [Press s][/bold]', border_style=self.colors['border'], box=ROUNDED)

    def update_agent_content(self, agent_id: str, content: str, content_type: str='thinking') -> None:
        """Update content for a specific agent with rich formatting and file output."""
        if agent_id not in self.agent_ids:
            return
        with self._lock:
            if agent_id not in self.agent_outputs:
                self.agent_outputs[agent_id] = []
            self._write_to_agent_file(agent_id, content, content_type)
            is_status_change = content_type in ['status', 'presentation', 'tool'] or any((keyword in content.lower() for keyword in self._status_change_keywords))
            if self._status_jump_enabled and is_status_change and self._web_search_truncate_on_status_change and self.agent_outputs[agent_id]:
                self._truncate_web_search_content(agent_id)
            if self._should_filter_content(content, content_type):
                return
            self._process_content_with_buffering(agent_id, content, content_type)
            self._categorize_update(agent_id, content_type, content)
            is_critical = content_type in ['tool', 'status', 'presentation', 'error'] or any((keyword in content.lower() for keyword in self._status_change_keywords))
            self._schedule_layered_update(agent_id, is_critical)

    def _process_content_with_buffering(self, agent_id: str, content: str, content_type: str) -> None:
        """Process content with buffering to accumulate text chunks."""
        if self._buffer_timers.get(agent_id):
            self._buffer_timers[agent_id].cancel()
            self._buffer_timers[agent_id] = None
        if content_type in ['tool', 'status', 'presentation', 'error'] or '\n' in content:
            self._flush_buffer(agent_id)
            if '\n' in content:
                for line in content.splitlines():
                    if line.strip() and (not self._should_filter_line(line)):
                        self.agent_outputs[agent_id].append(line)
            elif content.strip():
                self.agent_outputs[agent_id].append(content.strip())
            return
        self._text_buffers[agent_id] += content
        buffer = self._text_buffers[agent_id]
        if len(buffer) >= self._max_buffer_length:
            self._flush_buffer(agent_id)
            return
        self._set_buffer_timer(agent_id)

    def _flush_buffer(self, agent_id: str) -> None:
        """Flush the buffer for a specific agent."""
        if agent_id in self._text_buffers and self._text_buffers[agent_id]:
            buffer_content = self._text_buffers[agent_id].strip()
            if buffer_content:
                self.agent_outputs[agent_id].append(buffer_content)
            self._text_buffers[agent_id] = ''
        if self._buffer_timers.get(agent_id):
            self._buffer_timers[agent_id].cancel()
            self._buffer_timers[agent_id] = None

    def _set_buffer_timer(self, agent_id: str) -> None:
        """Set a timer to flush the buffer after a timeout."""
        if self._shutdown_flag:
            return
        if self._buffer_timers.get(agent_id):
            self._buffer_timers[agent_id].cancel()

        def timeout_flush() -> None:
            with self._lock:
                if agent_id in self._text_buffers and self._text_buffers[agent_id]:
                    self._flush_buffer(agent_id)
                    self._pending_updates.add(agent_id)
                    self._schedule_async_update(force_update=True)
        self._buffer_timers[agent_id] = threading.Timer(self._buffer_timeout, timeout_flush)
        self._buffer_timers[agent_id].start()

    def _write_to_agent_file(self, agent_id: str, content: str, content_type: str) -> None:
        """Write content to agent's individual txt file."""
        if agent_id not in self.agent_files:
            return
        if content_type == 'debug':
            return
        try:
            file_path = self.agent_files[agent_id]
            timestamp = time.strftime('%H:%M:%S')
            has_emoji = any((ord(char) > 127 and ord(char) in range(128512, 128591) or ord(char) in range(127744, 128511) or ord(char) in range(128640, 128767) or (ord(char) in range(9728, 9983)) or (ord(char) in range(9984, 10175)) for char in content))
            if has_emoji:
                formatted_content = f'\n[{timestamp}] {content}\n'
            else:
                formatted_content = f'{content}'
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(formatted_content)
        except Exception:
            pass

    def _write_system_status(self) -> None:
        """Write current system status to system status file - shows orchestrator events chronologically by time."""
        if not self.system_status_file:
            return
        try:
            with open(self.system_status_file, 'w', encoding='utf-8') as f:
                f.write('=== SYSTEM STATUS LOG ===\n\n')
                f.write('📊 Agent Status:\n')
                status_counts = {}
                for status in self.agent_status.values():
                    status_counts[status] = status_counts.get(status, 0) + 1
                for status, count in status_counts.items():
                    emoji = self._get_status_emoji(status, status)
                    f.write(f'  {emoji} {status.title()}: {count}\n')
                if self._final_presentation_active:
                    f.write('  🎤 Final Presentation: Active\n')
                elif hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
                    f.write('  🎤 Final Presentation: Complete\n')
                f.write('\n')
                f.write('📋 Orchestrator Events:\n')
                if self.orchestrator_events:
                    for event in self.orchestrator_events:
                        f.write(f'  • {event}\n')
                else:
                    f.write('  • No orchestrator events yet\n')
                f.write('\n')
        except Exception:
            pass

    def update_agent_status(self, agent_id: str, status: str) -> None:
        """Update status for a specific agent with rich indicators."""
        if agent_id not in self.agent_ids:
            return
        with self._lock:
            old_status = self.agent_status.get(agent_id, 'waiting')
            last_tracked_status = self._last_agent_status.get(agent_id, 'waiting')
            current_activity = self.agent_activity.get(agent_id, '')
            is_vote_status = 'voted' in status.lower() or 'voted' in current_activity.lower()
            should_update = old_status != status and last_tracked_status != status or is_vote_status
            if should_update:
                if self._status_jump_enabled and self._web_search_truncate_on_status_change and (old_status != status) and (agent_id in self.agent_outputs) and self.agent_outputs[agent_id]:
                    self._truncate_web_search_content(agent_id)
                super().update_agent_status(agent_id, status)
                self._last_agent_status[agent_id] = status
                self._priority_updates.add(agent_id)
                self._pending_updates.add(agent_id)
                self._pending_updates.add('footer')
                self._schedule_priority_update(agent_id)
                self._schedule_async_update(force_update=True)
                self._write_system_status()
            elif old_status != status:
                super().update_agent_status(agent_id, status)

    def add_orchestrator_event(self, event: str) -> None:
        """Add an orchestrator coordination event with timestamp."""
        with self._lock:
            if self.show_timestamps:
                timestamp = time.strftime('%H:%M:%S')
                formatted_event = f'[{timestamp}] {event}'
            else:
                formatted_event = event
            if hasattr(self, 'orchestrator_events') and self.orchestrator_events and (self.orchestrator_events[-1] == formatted_event):
                return
            super().add_orchestrator_event(formatted_event)
            if any((keyword in event.lower() for keyword in self._important_event_keywords)):
                self._pending_updates.add('footer')
                self._schedule_async_update(force_update=True)
                self._write_system_status()

    def display_vote_results(self, vote_results: Dict[str, Any]) -> None:
        """Display voting results in a formatted rich panel."""
        if not vote_results or not vote_results.get('vote_counts'):
            return
        self.live is not None
        if self.live:
            self.live.stop()
            self.live = None
        vote_counts = vote_results.get('vote_counts', {})
        voter_details = vote_results.get('voter_details', {})
        winner = vote_results.get('winner')
        is_tie = vote_results.get('is_tie', False)
        vote_content = Text()
        vote_content.append('📊 Vote Count:\n', style=self.colors['primary'])
        for agent_id, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True):
            winner_mark = '🏆' if agent_id == winner else '  '
            tie_mark = ' (tie-broken)' if is_tie and agent_id == winner else ''
            vote_content.append(f'   {winner_mark} {agent_id}: {count} vote{('s' if count != 1 else '')}{tie_mark}\n', style=self.colors['success'] if agent_id == winner else self.colors['text'])
        if voter_details:
            vote_content.append('\n🔍 Vote Details:\n', style=self.colors['primary'])
            for voted_for, voters in voter_details.items():
                vote_content.append(f'   → {voted_for}:\n', style=self.colors['info'])
                for voter_info in voters:
                    voter = voter_info['voter']
                    reason = voter_info['reason']
                    vote_content.append(f'     • {voter}: "{reason}"\n', style=self.colors['text'])
        agent_mapping = vote_results.get('agent_mapping', {})
        if agent_mapping:
            vote_content.append('\n🔀 Agent Mapping:\n', style=self.colors['primary'])
            for anon_id, real_id in sorted(agent_mapping.items()):
                vote_content.append(f'   {anon_id} → {real_id}\n', style=self.colors['info'])
        if is_tie:
            vote_content.append('\n⚖️  Tie broken by agent registration order\n', style=self.colors['warning'])
        total_votes = vote_results.get('total_votes', 0)
        agents_voted = vote_results.get('agents_voted', 0)
        vote_content.append(f'\n📈 Summary: {agents_voted}/{total_votes} agents voted', style=self.colors['info'])
        voting_panel = Panel(vote_content, title='[bold bright_cyan]🗳️  VOTING RESULTS[/bold bright_cyan]', border_style=self.colors['primary'], box=DOUBLE, expand=False)
        self.console.print(voting_panel)

    def display_coordination_table(self) -> None:
        """Display the coordination table showing the full coordination flow."""
        try:
            self.live is not None
            if self.live:
                self.live.stop()
                self.live = None
            if not hasattr(self, 'orchestrator') or not self.orchestrator:
                print('No orchestrator available for table generation')
                return
            tracker = getattr(self.orchestrator, 'coordination_tracker', None)
            if not tracker:
                print('No coordination tracker available')
                return
            events_data = [event.to_dict() for event in tracker.events]
            session_data = {'session_metadata': {'user_prompt': tracker.user_prompt, 'agent_ids': tracker.agent_ids, 'start_time': tracker.start_time, 'end_time': tracker.end_time, 'final_winner': tracker.final_winner}, 'events': events_data}
            from massgen.frontend.displays.create_coordination_table import CoordinationTableBuilder
            builder = CoordinationTableBuilder(session_data)
            result = builder.generate_rich_event_table()
            if result:
                legend, rich_table = result
                from rich.console import Console
                from rich.panel import Panel
                from rich.text import Text
                from massgen.frontend.displays.create_coordination_table import display_scrollable_content_macos, display_with_native_pager, get_optimal_display_method
                temp_console = Console()
                content = []
                title_text = Text()
                title_text.append('📊 COORDINATION TABLE', style='bold bright_green')
                title_text.append('\n\nNavigation: ↑/↓ or j/k to scroll, q to quit', style='dim cyan')
                title_panel = Panel(title_text, border_style='bright_blue', padding=(1, 2))
                content.append(title_panel)
                content.append('')
                content.append(rich_table)
                if legend:
                    content.append('')
                    content.append('')
                    content.append(legend)
                display_method = get_optimal_display_method()
                try:
                    if display_method == 'macos_simple':
                        display_scrollable_content_macos(temp_console, content, '📊 COORDINATION TABLE')
                    elif display_method == 'native_pager':
                        display_with_native_pager(temp_console, content, '📊 COORDINATION TABLE')
                    else:
                        with temp_console.pager(styles=True):
                            for item in content:
                                temp_console.print(item)
                except (KeyboardInterrupt, EOFError):
                    pass
                self.console.print('\n' + '=' * 80 + '\n')
            else:
                table_content = builder.generate_event_table()
                table_panel = Panel(table_content, title='[bold bright_green]📊 COORDINATION TABLE[/bold bright_green]', border_style=self.colors['success'], box=DOUBLE, expand=False)
                self.console.print('\n')
                self.console.print(table_panel)
                self.console.print()
        except Exception as e:
            print(f'Error displaying coordination table: {e}')
            import traceback
            traceback.print_exc()

    async def display_final_presentation(self, selected_agent: str, presentation_stream: Any, vote_results: Optional[Dict[str, Any]]=None) -> None:
        """Display final presentation with streaming box followed by clean final answer box."""
        if not selected_agent:
            return ''
        self._final_presentation_active = True
        self._final_presentation_content = ''
        self._final_presentation_agent = selected_agent
        self._final_presentation_vote_results = vote_results
        self._final_presentation_file_path = None
        self.console.print('\n')
        was_live = self.live is not None and self.live.is_started
        if not was_live:
            self.console.clear()
            self.live = Live(self._create_layout(), console=self.console, refresh_per_second=self.refresh_rate, vertical_overflow='ellipsis', transient=False)
            self.live.start()
        self._update_footer_cache()
        self._update_final_presentation_panel()
        presentation_content = ''
        chunk_count = 0
        presentation_file_path = self._initialize_final_presentation_file(selected_agent)
        self._final_presentation_file_path = presentation_file_path
        try:
            async for chunk in presentation_stream:
                chunk_count += 1
                content = getattr(chunk, 'content', '') or ''
                chunk_type = getattr(chunk, 'type', '')
                source = getattr(chunk, 'source', selected_agent)
                if chunk_type == 'debug':
                    continue
                if content:
                    if isinstance(content, list):
                        content = ' '.join((str(item) for item in content))
                    elif not isinstance(content, str):
                        content = str(content)
                    processed_content = self.process_reasoning_content(chunk_type, content, source)
                    self._final_presentation_content += processed_content
                    presentation_content += processed_content
                    if processed_content.strip():
                        truncated_content = processed_content.strip()[:150]
                        if len(processed_content.strip()) > 150:
                            truncated_content += '...'
                        self.add_orchestrator_event(f'🎤 {selected_agent}: {truncated_content}')
                    self._append_to_final_presentation_file(presentation_file_path, processed_content)
                    self._update_final_presentation_panel()
                else:
                    processed_content = self.process_reasoning_content(chunk_type, '', source)
                    if processed_content:
                        self._final_presentation_content += processed_content
                        presentation_content += processed_content
                        self._append_to_final_presentation_file(presentation_file_path, processed_content)
                        self._update_final_presentation_panel()
                if chunk_type == 'done':
                    break
        except Exception as e:
            error_msg = f'\n❌ Error during final presentation: {e}\n'
            self._final_presentation_content += error_msg
            self._update_final_presentation_panel()
            if hasattr(self, 'orchestrator') and self.orchestrator:
                try:
                    status = self.orchestrator.get_status()
                    if selected_agent in status.get('agent_states', {}):
                        stored_answer = status['agent_states'][selected_agent].get('answer', '')
                        if stored_answer:
                            fallback_msg = f'\n📋 Fallback to stored answer:\n{stored_answer}\n'
                            self._final_presentation_content += fallback_msg
                            presentation_content = stored_answer
                            self._update_final_presentation_panel()
                except Exception:
                    pass
        if presentation_content:
            self._stored_final_presentation = presentation_content
            self._stored_presentation_agent = selected_agent
            self._stored_vote_results = vote_results
            self._update_footer_cache()
        self._finalize_final_presentation_file(presentation_file_path)
        if self.live and self.live.is_started:
            self.live.stop()
            self.live = None
        self._final_presentation_active = False
        self._update_footer_cache()
        stats_text = Text()
        stats_text.append('✅ Presentation completed by ', style='bold green')
        stats_text.append(selected_agent, style=f'bold {self.colors['success']}')
        if chunk_count > 0:
            stats_text.append(f' | 📊 {chunk_count} chunks processed', style='dim')
        summary_panel = Panel(stats_text, border_style='green', box=ROUNDED, expand=True)
        self.console.print(summary_panel)
        return presentation_content

    def _format_multiline_content(self, content: str) -> Text:
        """Format multiline content for display in a panel."""
        formatted = Text()
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                formatted_line = self._format_content_line(line)
                formatted.append(formatted_line)
            formatted.append('\n')
        return formatted

    def show_final_answer(self, answer: str, vote_results: Dict[str, Any]=None, selected_agent: str=None):
        """Display the final coordinated answer prominently with voting results, final presentation, and agent selector."""
        with self._lock:
            self._flush_all_buffers()
        if self.live:
            self.live.stop()
            self.live = None
        if vote_results is None or selected_agent is None:
            try:
                if hasattr(self, 'orchestrator') and self.orchestrator:
                    status = self.orchestrator.get_status()
                    vote_results = vote_results or status.get('vote_results', {})
                    selected_agent = selected_agent or status.get('selected_agent')
            except Exception:
                pass
        with self._lock:
            for agent_id in self.agent_ids:
                self._pending_updates.add(agent_id)
            self._pending_updates.add('footer')
            self._schedule_async_update(force_update=True)
        time.sleep(0.5)
        self._force_display_final_vote_statuses()
        time.sleep(0.5)
        if vote_results and vote_results.get('vote_counts'):
            self.display_vote_results(vote_results)
            time.sleep(1.0)
        if selected_agent:
            selected_agent_text = Text(f'🏆 Selected agent: {selected_agent}', style=self.colors['success'])
        else:
            is_timeout = False
            if hasattr(self, 'orchestrator') and self.orchestrator:
                is_timeout = getattr(self.orchestrator, 'is_orchestrator_timeout', False)
            if is_timeout:
                selected_agent_text = Text()
                selected_agent_text.append('No agent selected\n', style=self.colors['warning'])
                selected_agent_text.append('The orchestrator timed out before any agent could complete voting or provide an answer.', style=self.colors['warning'])
            else:
                selected_agent_text = Text('No agent selected', style=self.colors['warning'])
        final_panel = Panel(Align.center(selected_agent_text), title='[bold bright_green]🎯 FINAL COORDINATED ANSWER[/bold bright_green]', border_style=self.colors['success'], box=DOUBLE, expand=False)
        self.console.print(final_panel)
        if selected_agent:
            selection_text = Text()
            selection_text.append(f'✅ Selected by: {selected_agent}', style=self.colors['success'])
            if vote_results and vote_results.get('vote_counts'):
                vote_summary = ', '.join([f'{agent}: {count}' for agent, count in vote_results['vote_counts'].items()])
                selection_text.append(f'\n🗳️ Vote results: {vote_summary}', style=self.colors['info'])
            selection_panel = Panel(selection_text, border_style=self.colors['info'], box=ROUNDED)
            self.console.print(selection_panel)
        if selected_agent and hasattr(self, 'orchestrator') and self.orchestrator:
            try:
                self._show_orchestrator_final_presentation(selected_agent, vote_results)
                time.sleep(1.0)
            except Exception as e:
                error_text = Text(f'❌ Error getting final presentation: {e}', style=self.colors['error'])
                self.console.print(error_text)
        if self._keyboard_interactive_mode and hasattr(self, '_agent_keys') and (not self._safe_keyboard_mode):
            self.show_agent_selector()

    def _display_answer_with_flush(self, answer: str) -> None:
        """Display answer with flush output effect - streaming character by character."""
        import sys
        import time
        char_delay = self._flush_char_delay
        word_delay = self._flush_word_delay
        line_delay = 0.2
        try:
            lines = answer.split('\n')
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    self.console.print()
                    continue
                for i, char in enumerate(line):
                    styled_char = Text(char, style=self.colors['text'])
                    self.console.print(styled_char, end='', highlight=False)
                    sys.stdout.flush()
                    if char in [' ', ',', ';']:
                        time.sleep(word_delay)
                    elif char in ['.', '!', '?', ':']:
                        time.sleep(word_delay * 2)
                    else:
                        time.sleep(char_delay)
                if line_idx < len(lines) - 1:
                    self.console.print()
                    time.sleep(line_delay)
            self.console.print()
        except KeyboardInterrupt:
            self.console.print(f'\n{Text(answer, style=self.colors['text'])}')
        except Exception:
            self.console.print(Text(answer, style=self.colors['text']))

    def _get_selected_agent_final_answer(self, selected_agent: str) -> str:
        """Get the final provided answer from the selected agent."""
        if not selected_agent:
            return ''
        try:
            if hasattr(self, 'orchestrator') and self.orchestrator:
                status = self.orchestrator.get_status()
                if hasattr(self.orchestrator, 'agent_states') and selected_agent in self.orchestrator.agent_states:
                    stored_answer = self.orchestrator.agent_states[selected_agent].answer
                    if stored_answer:
                        return stored_answer.replace('\\', '\n').replace('**', '').strip()
                if 'agent_states' in status and selected_agent in status['agent_states']:
                    agent_state = status['agent_states'][selected_agent]
                    if hasattr(agent_state, 'answer') and agent_state.answer:
                        return agent_state.answer.replace('\\', '\n').replace('**', '').strip()
                    elif isinstance(agent_state, dict) and 'answer' in agent_state:
                        return agent_state['answer'].replace('\\', '\n').replace('**', '').strip()
        except Exception:
            pass
        if selected_agent not in self.agent_outputs:
            return ''
        agent_output = self.agent_outputs[selected_agent]
        if not agent_output:
            return ''
        answer_lines = []
        for line in reversed(agent_output):
            line = line.strip()
            if not line:
                continue
            if any((marker in line for marker in ['⚡', '🔄', '✅', '🗳️', '❌', 'voted', '🔧', 'status'])):
                continue
            if any((marker in line.lower() for marker in ['final coordinated', 'coordination', 'voting'])):
                break
            answer_lines.insert(0, line)
            if len(answer_lines) >= 10 or len('\n'.join(answer_lines)) > 500:
                break
        if answer_lines:
            answer = '\n'.join(answer_lines).strip()
            answer = answer.replace('**', '').replace('##', '').strip()
            return answer
        return ''

    def _extract_presentation_content(self, selected_agent: str) -> str:
        """Extract presentation content from the selected agent's output."""
        if selected_agent not in self.agent_outputs:
            return ''
        agent_output = self.agent_outputs[selected_agent]
        presentation_lines = []
        collecting_presentation = False
        for line in agent_output:
            if '🎤' in line or 'presentation' in line.lower():
                collecting_presentation = True
                continue
            if not line.strip() or line.startswith('⚡') or line.startswith('🔄'):
                continue
            if collecting_presentation and line.strip():
                if any((marker in line for marker in ['✅', '🗳️', '🔄', '❌', 'voted', 'Final', 'coordination'])):
                    break
                presentation_lines.append(line.strip())
        if not presentation_lines and agent_output:
            for line in reversed(agent_output[-10:]):
                if line.strip() and (not line.startswith('⚡')) and (not line.startswith('🔄')) and (not any((marker in line for marker in ['voted', '🗳️', '✅', 'status']))):
                    presentation_lines.insert(0, line.strip())
                    if len(presentation_lines) >= 5:
                        break
        return '\n'.join(presentation_lines) if presentation_lines else ''

    def _display_final_presentation_content(self, selected_agent: str, presentation_content: str) -> None:
        """Display the final presentation content in a formatted panel with orchestrator query enhancements."""
        if not presentation_content.strip():
            return
        self._stored_final_presentation = presentation_content
        self._stored_presentation_agent = selected_agent
        header_text = Text()
        header_text.append(f'🎤 Final Presentation from {selected_agent}', style=self.colors['header_style'])
        header_panel = Panel(Align.center(header_text), border_style=self.colors['success'], box=DOUBLE, title='[bold]Final Presentation[/bold]')
        self.console.print(header_panel)
        self.console.print('=' * 60)
        content_text = Text()
        formatted_content = self._format_presentation_content(presentation_content)
        content_text.append(formatted_content)
        content_panel = Panel(content_text, title=f'[bold]{selected_agent.upper()} Final Presentation[/bold]', border_style=self.colors['primary'], box=ROUNDED, subtitle='[italic]Final presentation content[/italic]')
        self.console.print(content_panel)
        self.console.print('=' * 60)
        completion_text = Text()
        completion_text.append('✅ Final presentation completed successfully', style=self.colors['success'])
        completion_panel = Panel(Align.center(completion_text), border_style=self.colors['success'], box=ROUNDED)
        self.console.print(completion_panel)
        self._save_final_presentation_to_file(selected_agent, presentation_content)

    def _save_final_presentation_to_file(self, selected_agent: str, presentation_content: str) -> None:
        """Save the final presentation content to a text file in agent_outputs directory."""
        try:
            filename = f'final_presentation_{selected_agent}.txt'
            file_path = Path(self.output_dir) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'=== FINAL PRESENTATION FROM {selected_agent.upper()} ===\n')
                f.write(f'Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 60 + '\n\n')
                f.write(presentation_content)
                f.write('\n\n' + '=' * 60 + '\n')
                f.write('End of Final Presentation\n')
            latest_link = Path(self.output_dir) / f'final_presentation_{selected_agent}_latest.txt'
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(filename)
        except Exception:
            pass

    def _initialize_final_presentation_file(self, selected_agent: str) -> Path:
        """Initialize a new final presentation file and return the file path."""
        try:
            filename = f'final_presentation_{selected_agent}.txt'
            file_path = Path(self.output_dir) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'=== FINAL PRESENTATION FROM {selected_agent.upper()} ===\n')
                f.write(f'Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 60 + '\n\n')
            latest_link = Path(self.output_dir) / f'final_presentation_{selected_agent}_latest.txt'
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(filename)
            return file_path
        except Exception:
            return None

    def _append_to_final_presentation_file(self, file_path: Path, content: str) -> None:
        """Append content to the final presentation file."""
        try:
            if file_path and file_path.exists():
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    import os
                    os.fsync(f.fileno())
        except Exception:
            pass

    def _finalize_final_presentation_file(self, file_path: Path) -> None:
        """Add closing content to the final presentation file."""
        try:
            if file_path and file_path.exists():
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + '=' * 60 + '\n')
                    f.write('End of Final Presentation\n')
        except Exception:
            pass

    def _show_orchestrator_final_presentation(self, selected_agent: str, vote_results: Dict[str, Any]=None) -> None:
        """Show the final presentation from the orchestrator for the selected agent."""
        import time
        try:
            if not hasattr(self, 'orchestrator') or not self.orchestrator:
                return
            if hasattr(self.orchestrator, 'get_final_presentation'):
                import asyncio

                async def _get_and_display_presentation() -> None:
                    """Helper to get and display presentation asynchronously."""
                    try:
                        presentation_stream = self.orchestrator.get_final_presentation(selected_agent, vote_results)
                        await self.display_final_presentation(selected_agent, presentation_stream, vote_results)
                    except Exception:
                        raise
                import nest_asyncio
                nest_asyncio.apply()
                try:
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(_get_and_display_presentation())
                    time.sleep(0.5)
                except Exception:
                    try:
                        asyncio.run(_get_and_display_presentation())
                        time.sleep(0.5)
                    except Exception:
                        self._display_final_presentation_content(selected_agent, 'Unable to retrieve live presentation.')
            else:
                status = self.orchestrator.get_status()
                if selected_agent in status.get('agent_states', {}):
                    stored_answer = status['agent_states'][selected_agent].get('answer', '')
                    if stored_answer:
                        self._display_final_presentation_content(selected_agent, stored_answer)
                    else:
                        print('DEBUG: No stored answer found')
                else:
                    print(f'DEBUG: Agent {selected_agent} not found in agent_states')
        except Exception as e:
            error_text = Text(f'❌ Error in final presentation: {e}', style=self.colors['error'])
            self.console.print(error_text)

    def _force_display_final_vote_statuses(self) -> None:
        """Force display update to show all agents' final vote statuses."""
        with self._lock:
            for agent_id in self.agent_ids:
                self._pending_updates.add(agent_id)
            self._pending_updates.add('footer')
            self._schedule_async_update(force_update=True)
        import time
        time.sleep(0.3)

    def _flush_all_buffers(self) -> None:
        """Flush all text buffers to ensure no content is lost."""
        for agent_id in self.agent_ids:
            if agent_id in self._text_buffers and self._text_buffers[agent_id]:
                buffer_content = self._text_buffers[agent_id].strip()
                if buffer_content:
                    self.agent_outputs[agent_id].append(buffer_content)
                self._text_buffers[agent_id] = ''

    def cleanup(self) -> None:
        """Clean up display resources."""
        with self._lock:
            self._flush_all_buffers()
            if self.live:
                try:
                    self.live.stop()
                except Exception:
                    pass
                finally:
                    self.live = None
            self._stop_input_thread = True
            if self._input_thread and self._input_thread.is_alive():
                try:
                    self._input_thread.join(timeout=1.0)
                except Exception:
                    pass
            try:
                self._restore_terminal_settings()
            except Exception:
                pass
            self._agent_selector_active = False
            self._final_answer_shown = False
            try:
                signal.signal(signal.SIGWINCH, signal.SIG_DFL)
            except (AttributeError, OSError):
                pass
            if self._key_handler:
                try:
                    self._key_handler.stop()
                except Exception:
                    pass
            self._shutdown_flag = True
            for timer in self._debounce_timers.values():
                timer.cancel()
            self._debounce_timers.clear()
            for timer in self._buffer_timers.values():
                if timer:
                    timer.cancel()
            self._buffer_timers.clear()
            if self._batch_timer:
                self._batch_timer.cancel()
                self._batch_timer = None
            if hasattr(self, '_refresh_executor'):
                self._refresh_executor.shutdown(wait=True)
            if hasattr(self, '_status_update_executor'):
                self._status_update_executor.shutdown(wait=True)
            try:
                for agent_id, file_path in self.agent_files.items():
                    if file_path.exists():
                        with open(file_path, 'a', encoding='utf-8') as f:
                            f.write(f'\n=== SESSION ENDED at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n')
            except Exception:
                pass
        from massgen.logger_config import restore_console_logging
        restore_console_logging()

    def _schedule_priority_update(self, agent_id: str) -> None:
        """Schedule immediate priority update for critical agent status changes."""
        if self._shutdown_flag:
            return

        def priority_update() -> None:
            try:
                self._update_agent_panel_cache(agent_id)
                self._update_display_safe()
            except Exception:
                pass
        self._status_update_executor.submit(priority_update)

    def _categorize_update(self, agent_id: str, content_type: str, content: str) -> None:
        """Categorize update by priority for layered refresh strategy."""
        if content_type in ['status', 'error', 'tool'] or any((keyword in content.lower() for keyword in ['error', 'failed', 'completed', 'voted'])):
            self._critical_updates.add(agent_id)
            self._normal_updates.discard(agent_id)
            self._decorative_updates.discard(agent_id)
        elif content_type in ['thinking', 'presentation']:
            if agent_id not in self._critical_updates:
                self._normal_updates.add(agent_id)
                self._decorative_updates.discard(agent_id)
        elif agent_id not in self._critical_updates and agent_id not in self._normal_updates:
            self._decorative_updates.add(agent_id)

    def _schedule_layered_update(self, agent_id: str, is_critical: bool=False) -> None:
        """Schedule update using layered refresh strategy with intelligent batching."""
        if is_critical:
            self._flush_update_batch()
            self._pending_updates.add(agent_id)
            self._schedule_async_update(force_update=True)
        else:
            perf_tier = self._terminal_performance['performance_tier']
            if perf_tier == 'high':
                self._pending_updates.add(agent_id)
                self._schedule_async_update(force_update=False)
            else:
                self._add_to_update_batch(agent_id)

    def _schedule_delayed_update(self) -> None:
        """Schedule delayed update for non-critical content."""
        delay = self._debounce_delay * 2

        def delayed_update() -> None:
            if self._pending_updates:
                self._schedule_async_update(force_update=False)
        if 'delayed' in self._debounce_timers:
            self._debounce_timers['delayed'].cancel()
        self._debounce_timers['delayed'] = threading.Timer(delay, delayed_update)
        self._debounce_timers['delayed'].start()

    def _add_to_update_batch(self, agent_id: str) -> None:
        """Add update to batch for efficient processing."""
        self._update_batch.add(agent_id)
        if self._batch_timer:
            self._batch_timer.cancel()
        self._batch_timer = threading.Timer(self._batch_timeout, self._process_update_batch)
        self._batch_timer.start()

    def _process_update_batch(self) -> None:
        """Process accumulated batch of updates."""
        if self._update_batch:
            self._pending_updates.update(self._update_batch)
            self._update_batch.clear()
            self._schedule_async_update(force_update=False)

    def _flush_update_batch(self) -> None:
        """Immediately flush any pending batch updates."""
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None
        if self._update_batch:
            self._pending_updates.update(self._update_batch)
            self._update_batch.clear()

    def _schedule_async_update(self, force_update: bool=False):
        """Schedule asynchronous update with debouncing to prevent jitter."""
        current_time = time.time()
        if not force_update and self._should_skip_frame():
            return
        if current_time - self._last_full_refresh > self._full_refresh_interval:
            with self._lock:
                self._pending_updates.add('header')
                self._pending_updates.add('footer')
                self._pending_updates.update(self.agent_ids)
            self._last_full_refresh = current_time
        if force_update:
            self._last_update = current_time
            self._refresh_executor.submit(self._async_update_components)
            return
        if 'main' in self._debounce_timers:
            self._debounce_timers['main'].cancel()

        def debounced_update() -> None:
            current_time = time.time()
            time_since_last_update = current_time - self._last_update
            if time_since_last_update >= self._update_interval:
                self._last_update = current_time
                self._refresh_executor.submit(self._async_update_components)
        self._debounce_timers['main'] = threading.Timer(self._debounce_delay, debounced_update)
        self._debounce_timers['main'].start()

    def _should_skip_frame(self) -> bool:
        """Determine if we should skip this frame update to maintain stability."""
        term_type = self._terminal_performance['type']
        if term_type in ['iterm', 'macos_terminal']:
            if self._dropped_frames > 1:
                return True
            if hasattr(self._refresh_executor, '_work_queue') and self._refresh_executor._work_queue.qsize() > 2:
                return True
        return False

    def _async_update_components(self) -> None:
        """Asynchronously update only the components that have changed."""
        start_time = time.time()
        try:
            updates_to_process = None
            with self._lock:
                if self._pending_updates:
                    updates_to_process = self._pending_updates.copy()
                    self._pending_updates.clear()
            if not updates_to_process:
                return
            futures = []
            for update_id in updates_to_process:
                if update_id == 'header':
                    future = self._refresh_executor.submit(self._update_header_cache)
                    futures.append(future)
                elif update_id == 'footer':
                    future = self._refresh_executor.submit(self._update_footer_cache)
                    futures.append(future)
                elif update_id in self.agent_ids:
                    future = self._refresh_executor.submit(self._update_agent_panel_cache, update_id)
                    futures.append(future)
            for future in futures:
                future.result()
            self._update_display_safe()
        except Exception:
            pass
        finally:
            refresh_time = time.time() - start_time
            self._refresh_times.append(refresh_time)
            self._monitor_performance()

    def _update_header_cache(self) -> None:
        """Update the cached header panel."""
        try:
            self._header_cache = self._create_header()
        except Exception:
            pass

    def _update_footer_cache(self) -> None:
        """Update the cached footer panel."""
        try:
            self._footer_cache = self._create_footer()
        except Exception:
            pass

    def _update_agent_panel_cache(self, agent_id: str):
        """Update the cached panel for a specific agent."""
        try:
            self._agent_panels_cache[agent_id] = self._create_agent_panel(agent_id)
        except Exception:
            pass

    def _update_final_presentation_panel(self) -> None:
        """Update the live display to show the latest final presentation content."""
        try:
            if self.live and self.live.is_started:
                with self._lock:
                    self.live.update(self._create_layout())
        except Exception:
            pass

    def _refresh_display(self) -> None:
        """Override parent's refresh method to use async updates."""
        if self._pending_updates:
            self._schedule_async_update()

    def _is_content_important(self, content: str, content_type: str) -> bool:
        """Determine if content is important enough to trigger a display update."""
        if content_type in self._important_content_types:
            return True
        if any((keyword in content.lower() for keyword in self._status_change_keywords)):
            return True
        if any((keyword in content.lower() for keyword in ['error', 'exception', 'failed', 'timeout'])):
            return True
        return False

    def set_status_jump_enabled(self, enabled: bool):
        """Enable or disable status jumping functionality.

        Args:
            enabled: Whether to enable status jumping
        """
        with self._lock:
            self._status_jump_enabled = enabled

    def set_web_search_truncation(self, enabled: bool, max_lines: int=3):
        """Configure web search content truncation on status changes.

        Args:
            enabled: Whether to enable web search truncation
            max_lines: Maximum web search lines to keep when truncating
        """
        with self._lock:
            self._web_search_truncate_on_status_change = enabled
            self._max_web_search_lines = max_lines

    def set_flush_output(self, enabled: bool, char_delay: float=0.03, word_delay: float=0.08):
        """Configure flush output settings for final answer display.

        Args:
            enabled: Whether to enable flush output effect
            char_delay: Delay between characters in seconds
            word_delay: Extra delay after punctuation in seconds
        """
        with self._lock:
            self._enable_flush_output = enabled
            self._flush_char_delay = char_delay
            self._flush_word_delay = word_delay

def _setup_agent_files(self) -> None:
    """Setup individual txt files for each agent and system status file."""
    Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    for agent_id in self.agent_ids:
        file_path = Path(self.output_dir) / f'{agent_id}.txt'
        self.agent_files[agent_id] = file_path
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'=== {agent_id.upper()} OUTPUT LOG ===\n\n')
    self.system_status_file = Path(self.output_dir) / 'system_status.txt'
    with open(str(self.system_status_file), 'w', encoding='utf-8') as f:
        f.write('=== SYSTEM STATUS LOG ===\n\n')

def _input_thread_worker_safe(self) -> None:
    """Completely safe keyboard input that never changes terminal settings."""
    try:
        while not self._stop_input_thread:
            time.sleep(0.5)
    except Exception:
        pass

def _show_agent_full_content(self, agent_id: str) -> None:
    """Display full content of selected agent from txt file."""
    if agent_id not in self.agent_files:
        return
    try:
        file_path = self.agent_files[agent_id]
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '[' in content:
                    content = content.replace('[', '\\[')
            self.console.print('\n' + '=' * 80 + '\n')
            header_text = Text()
            header_text.append(f'📄 {agent_id.upper()} - Full Content', style=self.colors['header_style'])
            header_text.append('\nPress any key to return to main view', style=self.colors['info'])
            header_panel = Panel(header_text, box=DOUBLE, border_style=self.colors['border'])
            content_panel = Panel(content, title=f'[bold]{agent_id.upper()} Output[/bold]', border_style=self.colors['border'], box=ROUNDED)
            self.console.print(header_panel)
            self.console.print(content_panel)
            input('Press Enter to return to agent selector...')
            self.console.print('\n' + '=' * 80 + '\n')
    except Exception:
        pass

def _show_system_status(self) -> None:
    """Display system status from txt file."""
    if not self.system_status_file or not self.system_status_file.exists():
        self.console.print(f'[{self.colors['error']}]System status file not found.[/{self.colors['error']}]')
        return
    try:
        with open(self.system_status_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '[' in content:
                content = content.replace('[', '\\[')
        self.console.print('\n' + '=' * 80 + '\n')
        header_text = Text()
        header_text.append('📊 SYSTEM STATUS - Full Log', style=self.colors['header_style'])
        header_text.append('\nPress any key to return to agent selector', style=self.colors['info'])
        header_panel = Panel(header_text, box=DOUBLE, border_style=self.colors['border'])
        content_panel = Panel(content, title='[bold]System Status Log[/bold]', border_style=self.colors['border'], box=ROUNDED)
        self.console.print(header_panel)
        self.console.print(content_panel)
        input('Press Enter to return to agent selector...')
        self.console.print('\n' + '=' * 80 + '\n')
    except Exception as e:
        self.console.print(f'[{self.colors['error']}]Error reading system status file: {e}[/{self.colors['error']}]')

def _write_to_agent_file(self, agent_id: str, content: str, content_type: str) -> None:
    """Write content to agent's individual txt file."""
    if agent_id not in self.agent_files:
        return
    if content_type == 'debug':
        return
    try:
        file_path = self.agent_files[agent_id]
        timestamp = time.strftime('%H:%M:%S')
        has_emoji = any((ord(char) > 127 and ord(char) in range(128512, 128591) or ord(char) in range(127744, 128511) or ord(char) in range(128640, 128767) or (ord(char) in range(9728, 9983)) or (ord(char) in range(9984, 10175)) for char in content))
        if has_emoji:
            formatted_content = f'\n[{timestamp}] {content}\n'
        else:
            formatted_content = f'{content}'
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(formatted_content)
    except Exception:
        pass

def _write_system_status(self) -> None:
    """Write current system status to system status file - shows orchestrator events chronologically by time."""
    if not self.system_status_file:
        return
    try:
        with open(self.system_status_file, 'w', encoding='utf-8') as f:
            f.write('=== SYSTEM STATUS LOG ===\n\n')
            f.write('📊 Agent Status:\n')
            status_counts = {}
            for status in self.agent_status.values():
                status_counts[status] = status_counts.get(status, 0) + 1
            for status, count in status_counts.items():
                emoji = self._get_status_emoji(status, status)
                f.write(f'  {emoji} {status.title()}: {count}\n')
            if self._final_presentation_active:
                f.write('  🎤 Final Presentation: Active\n')
            elif hasattr(self, '_stored_final_presentation') and self._stored_final_presentation:
                f.write('  🎤 Final Presentation: Complete\n')
            f.write('\n')
            f.write('📋 Orchestrator Events:\n')
            if self.orchestrator_events:
                for event in self.orchestrator_events:
                    f.write(f'  • {event}\n')
            else:
                f.write('  • No orchestrator events yet\n')
            f.write('\n')
    except Exception:
        pass

def _save_final_presentation_to_file(self, selected_agent: str, presentation_content: str) -> None:
    """Save the final presentation content to a text file in agent_outputs directory."""
    try:
        filename = f'final_presentation_{selected_agent}.txt'
        file_path = Path(self.output_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'=== FINAL PRESENTATION FROM {selected_agent.upper()} ===\n')
            f.write(f'Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n')
            f.write('=' * 60 + '\n\n')
            f.write(presentation_content)
            f.write('\n\n' + '=' * 60 + '\n')
            f.write('End of Final Presentation\n')
        latest_link = Path(self.output_dir) / f'final_presentation_{selected_agent}_latest.txt'
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(filename)
    except Exception:
        pass

def _initialize_final_presentation_file(self, selected_agent: str) -> Path:
    """Initialize a new final presentation file and return the file path."""
    try:
        filename = f'final_presentation_{selected_agent}.txt'
        file_path = Path(self.output_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'=== FINAL PRESENTATION FROM {selected_agent.upper()} ===\n')
            f.write(f'Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n')
            f.write('=' * 60 + '\n\n')
        latest_link = Path(self.output_dir) / f'final_presentation_{selected_agent}_latest.txt'
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(filename)
        return file_path
    except Exception:
        return None

def _append_to_final_presentation_file(self, file_path: Path, content: str) -> None:
    """Append content to the final presentation file."""
    try:
        if file_path and file_path.exists():
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                import os
                os.fsync(f.fileno())
    except Exception:
        pass

def _finalize_final_presentation_file(self, file_path: Path) -> None:
    """Add closing content to the final presentation file."""
    try:
        if file_path and file_path.exists():
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n\n' + '=' * 60 + '\n')
                f.write('End of Final Presentation\n')
    except Exception:
        pass

class MCPBackend(LLMBackend):
    """Base backend class with MCP (Model Context Protocol) support."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        """Initialize backend with MCP support."""
        super().__init__(api_key, **kwargs)
        self.mcp_servers = self.config.get('mcp_servers', [])
        self.allowed_tools = kwargs.pop('allowed_tools', None)
        self.exclude_tools = kwargs.pop('exclude_tools', None)
        self._mcp_client: Optional[MCPClient] = None
        self._mcp_initialized = False
        self._mcp_tool_calls_count = 0
        self._mcp_tool_failures = 0
        self._mcp_function_names: set[str] = set()
        self._mcp_tools_circuit_breaker = None
        self._circuit_breakers_enabled = MCPCircuitBreaker is not None
        if self._circuit_breakers_enabled and self.mcp_servers:
            mcp_tools_config = MCPConfigHelper.build_circuit_breaker_config('mcp_tools') if MCPConfigHelper else None
            if mcp_tools_config:
                self._mcp_tools_circuit_breaker = MCPCircuitBreaker(mcp_tools_config)
                logger.info('Circuit breaker initialized for MCP tools')
            else:
                logger.warning('MCP tools circuit breaker config not available, disabling circuit breaker functionality')
                self._circuit_breakers_enabled = False
        elif not self.mcp_servers:
            self._circuit_breakers_enabled = False
        else:
            logger.warning('Circuit breakers not available - proceeding without circuit breaker protection')
        self._mcp_functions: Dict[str, Function] = {}
        self._stats_lock = asyncio.Lock()
        self._max_mcp_message_history = kwargs.pop('max_mcp_message_history', 200)
        self.backend_name = self.get_provider_name()
        self.agent_id = kwargs.get('agent_id', None)

    def supports_upload_files(self) -> bool:
        """Return True if the backend supports `upload_files` preprocessing."""
        return False

    @abstractmethod
    async def _process_stream(self, stream, all_params, agent_id: Optional[str]=None) -> AsyncGenerator[StreamChunk, None]:
        """Process stream."""

    async def _setup_mcp_tools(self) -> None:
        """Initialize MCP client for mcp_tools-based servers (stdio + streamable-http)."""
        if not self.mcp_servers or self._mcp_initialized:
            return
        try:
            normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers, backend_name=self.backend_name, agent_id=self.agent_id) if MCPSetupManager else []
            if not MCPSetupManager:
                logger.warning('MCPSetupManager not available')
                return
            mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers, backend_name=self.backend_name, agent_id=self.agent_id)
            if not mcp_tools_servers:
                logger.info('No stdio/streamable-http servers configured')
                return
            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker and MCPCircuitBreakerManager:
                filtered_servers = MCPCircuitBreakerManager.apply_circuit_breaker_filtering(mcp_tools_servers, self._mcp_tools_circuit_breaker, backend_name=self.backend_name, agent_id=self.agent_id)
                if not filtered_servers:
                    logger.warning('All MCP servers blocked by circuit breaker during setup')
                    return
                if len(filtered_servers) < len(mcp_tools_servers):
                    logger.info(f'Circuit breaker filtered {len(mcp_tools_servers) - len(filtered_servers)} servers during setup')
                servers_to_use = filtered_servers
            else:
                servers_to_use = mcp_tools_servers
            if not MCPResourceManager:
                logger.warning('MCPResourceManager not available')
                return
            self._mcp_client = await MCPResourceManager.setup_mcp_client(servers=servers_to_use, allowed_tools=self.allowed_tools, exclude_tools=self.exclude_tools, circuit_breaker=self._mcp_tools_circuit_breaker, timeout_seconds=400, backend_name=self.backend_name, agent_id=self.agent_id)
            if not self._mcp_client:
                self._mcp_initialized = False
                logger.warning('MCP client setup failed, falling back to no-MCP streaming')
                return
            self._mcp_functions.update(MCPResourceManager.convert_tools_to_functions(self._mcp_client, backend_name=self.backend_name, agent_id=self.agent_id, hook_manager=getattr(self, 'function_hook_manager', None)))
            self._mcp_initialized = True
            logger.info(f'Successfully initialized MCP sessions with {len(self._mcp_functions)} tools converted to functions')
            await self._record_mcp_circuit_breaker_success(servers_to_use)
        except Exception as e:
            self._record_mcp_circuit_breaker_failure(e, self.agent_id)
            logger.warning(f'Failed to setup MCP sessions: {e}')
            self._mcp_client = None
            self._mcp_initialized = False
            self._mcp_functions = {}

    async def _execute_mcp_function_with_retry(self, function_name: str, arguments_json: str, max_retries: int=3) -> Tuple[str, Any]:
        """Execute MCP function with exponential backoff retry logic."""
        if self.is_planning_mode_enabled():
            logger.info(f'[MCP] Planning mode enabled - blocking MCP tool execution: {function_name}')
            error_str = '🚫 [MCP] Planning mode active - MCP tools blocked during coordination'
            return (error_str, {'error': error_str, 'blocked_by': 'planning_mode', 'function_name': function_name})
        try:
            args = json.loads(arguments_json) if isinstance(arguments_json, str) else arguments_json
        except (json.JSONDecodeError, ValueError) as e:
            error_str = f'Error: Invalid JSON arguments: {e}'
            return (error_str, {'error': error_str})

        async def stats_callback(action: str) -> int:
            async with self._stats_lock:
                if action == 'increment_calls':
                    self._mcp_tool_calls_count += 1
                    return self._mcp_tool_calls_count
                elif action == 'increment_failures':
                    self._mcp_tool_failures += 1
                    return self._mcp_tool_failures
            return 0

        async def circuit_breaker_callback(event: str, error_msg: str='') -> None:
            if not (self._circuit_breakers_enabled and MCPCircuitBreakerManager and self._mcp_tools_circuit_breaker):
                return
            if event == 'failure':
                await MCPCircuitBreakerManager.record_event([], self._mcp_tools_circuit_breaker, 'failure', error_msg, backend_name=self.backend_name, agent_id=self.agent_id)
            else:
                await MCPCircuitBreakerManager.record_event([], self._mcp_tools_circuit_breaker, 'success', backend_name=self.backend_name, agent_id=self.agent_id)
        if not MCPExecutionManager:
            return ('Error: MCPExecutionManager unavailable', {'error': 'MCPExecutionManager unavailable'})
        result = await MCPExecutionManager.execute_function_with_retry(function_name=function_name, args=args, functions=self._mcp_functions, max_retries=max_retries, stats_callback=stats_callback, circuit_breaker_callback=circuit_breaker_callback, logger_instance=logger)
        if isinstance(result, dict) and 'error' in result:
            return (f'Error: {result['error']}', result)
        return (str(result), result)

    async def _process_upload_files(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process upload_files config entries and attach to messages.

        Supports these forms:

        - {"image_path": "..."}: image file path or HTTP/HTTPS URL
          - Local paths: loads and base64-encodes the image file
          - URLs: passed directly without encoding
          Supported formats: PNG, JPEG, WEBP, GIF, BMP, TIFF, HEIC (provider-dependent)

        - {"audio_path": "..."}: audio file path or HTTP/HTTPS URL
          - Local paths: loads and base64-encodes the audio file
          - URLs: fetched and base64-encoded (30s timeout, configurable size limit)
          Supported formats: WAV, MP3 (strictly validated)

        - {"video_path": "..."}: video file path or HTTP/HTTPS URL
          - Local paths: loads and base64-encodes the video file
          - URLs: passed directly without encoding, converted to video_url format
          Supported formats: MP4, AVI, MOV, WEBM (provider-dependent)

        - {"file_path": "..."}: document/code file for File Search (local path or URL)
          - Local paths: validated against supported extensions and size limits
          - URLs: queued for upload without local validation
          Supported extensions: .c, .cpp, .cs, .css, .doc, .docx, .html, .java, .js,
          .json, .md, .pdf, .php, .pptx, .py, .rb, .sh, .tex, .ts, .txt

        Note: Format support varies by provider (OpenAI, Qwen, vLLM, etc.). The implementation
        uses MIME type detection for automatic format handling.

        Audio/Video/Image uploads are limited by `media_max_file_size_mb` (default 64MB).
        File Search files are limited to 512MB. You can override limits via config or call parameters.

        Returns updated messages list with additional content items.
        """
        upload_entries = all_params.get('upload_files')
        if not upload_entries:
            return messages
        if not self.supports_upload_files():
            logger.debug('upload_files provided but backend %s does not support file uploads; ignoring', self.get_provider_name())
            all_params.pop('upload_files', None)
            return messages
        processed_messages = list(messages)
        extra_content: List[Dict[str, Any]] = []
        has_file_search_files = False
        for entry in upload_entries:
            if not isinstance(entry, dict):
                logger.warning('upload_files entry is not a dict: %s', entry)
                raise UploadFileError('Each upload_files entry must be a mapping')
            file_path_value = entry.get('file_path')
            if file_path_value:
                file_content = self._process_file_path_entry(file_path_value, all_params)
                if file_content:
                    extra_content.append(file_content)
                    has_file_search_files = True
                continue
            path_value = entry.get('image_path')
            if path_value:
                if path_value.startswith(('http://', 'https://')):
                    extra_content.append({'type': 'image', 'url': path_value})
                else:
                    resolved = self._resolve_local_path(path_value, all_params)
                    if not resolved.exists():
                        raise UploadFileError(f'File not found: {resolved}')
                    limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
                    self._validate_media_size(resolved, int(limit_mb))
                    encoded, mime_type = self._read_base64(resolved)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                    extra_content.append({'type': 'image', 'base64': encoded, 'mime_type': mime_type, 'source_path': str(resolved)})
                continue
            audio_path_value = entry.get('audio_path')
            if audio_path_value:
                if audio_path_value.startswith(('http://', 'https://')):
                    encoded, mime_type = await self._fetch_audio_url_as_base64(audio_path_value, all_params)
                    extra_content.append({'type': 'audio', 'base64': encoded, 'mime_type': mime_type})
                else:
                    resolved = self._resolve_local_path(audio_path_value, all_params)
                    if not resolved.exists():
                        raise UploadFileError(f'Audio file not found: {resolved}')
                    limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
                    self._validate_media_size(resolved, int(limit_mb))
                    encoded, mime_type = self._read_base64(resolved)
                    mime_lower = (mime_type or '').split(';')[0].strip().lower()
                    if mime_lower not in SUPPORTED_AUDIO_MIME_TYPES:
                        raise UploadFileError(f'Unsupported audio format for {resolved}. Supported formats: mp3, wav')
                    if mime_lower in {'audio/wav', 'audio/wave', 'audio/x-wav'}:
                        mime_type = 'audio/wav'
                    else:
                        mime_type = 'audio/mpeg'
                    extra_content.append({'type': 'audio', 'base64': encoded, 'mime_type': mime_type, 'source_path': str(resolved)})
                continue
            video_path_value = entry.get('video_path')
            if video_path_value:
                if video_path_value.startswith(('http://', 'https://')):
                    extra_content.append({'type': 'video_url', 'url': video_path_value})
                else:
                    resolved = self._resolve_local_path(video_path_value, all_params)
                    if not resolved.exists():
                        raise UploadFileError(f'Video file not found: {resolved}')
                    limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
                    self._validate_media_size(resolved, int(limit_mb))
                    encoded, mime_type = self._read_base64(resolved)
                    if not mime_type:
                        mime_type = 'video/mp4'
                    extra_content.append({'type': 'video', 'base64': encoded, 'mime_type': mime_type, 'source_path': str(resolved)})
                continue
            raise UploadFileError("upload_files entry must specify either 'image_path', 'audio_path', 'video_path', or 'file_path'")
        if not extra_content:
            return processed_messages
        if has_file_search_files:
            all_params['_has_file_search_files'] = True
        if processed_messages:
            last_message = processed_messages[-1].copy()
            last_content = last_message.get('content', [])
            if isinstance(last_content, str):
                last_content = [{'type': 'text', 'text': last_content}]
            elif isinstance(last_content, dict) and 'type' in last_content:
                last_content = [dict(last_content)]
            elif isinstance(last_content, list):
                if all((isinstance(item, str) for item in last_content)):
                    last_content = [{'type': 'text', 'text': item} for item in last_content]
                elif all((isinstance(item, dict) and 'type' in item and ('text' in item) for item in last_content)):
                    last_content = list(last_content)
                else:
                    last_content = []
            else:
                last_content = []
            last_content.extend(extra_content)
            last_message['content'] = last_content
            processed_messages[-1] = last_message
        else:
            processed_messages.append({'role': 'user', 'content': extra_content})
        all_params.pop('upload_files', None)
        return processed_messages

    def _process_file_path_entry(self, file_path_value: str, all_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process file path entry and validate against provider-specific restrictions.

        Note: This base implementation validates against OpenAI File Search extensions.
        Backends like Claude may have additional restrictions (e.g., only .pdf and .txt)
        and should perform provider-specific validation in their upload methods.
        """
        if file_path_value.startswith(('http://', 'https://')):
            logger.info(f'Queued file URL for File Search upload: {file_path_value}')
            return {'type': 'file_pending_upload', 'url': file_path_value, 'source': 'url'}
        resolved = Path(file_path_value).expanduser()
        if not resolved.is_absolute():
            cwd = all_params.get('cwd') or self.config.get('cwd')
            if cwd:
                resolved = Path(cwd).joinpath(resolved)
            else:
                resolved = resolved.resolve()
        if not resolved.exists():
            raise UploadFileError(f'File not found: {resolved}')
        file_ext = resolved.suffix.lower()
        if file_ext not in FILE_SEARCH_SUPPORTED_EXTENSIONS:
            raise UploadFileError(f'File type {file_ext} not supported by File Search. Supported types: {', '.join(sorted(FILE_SEARCH_SUPPORTED_EXTENSIONS))}')
        file_size = resolved.stat().st_size
        if file_size > FILE_SEARCH_MAX_FILE_SIZE:
            raise UploadFileError(f'File size {file_size / (1024 * 1024):.2f} MB exceeds File Search limit of {FILE_SEARCH_MAX_FILE_SIZE / (1024 * 1024):.0f} MB')
        mime_type, _ = mimetypes.guess_type(resolved.as_posix())
        if not mime_type:
            mime_type = 'application/octet-stream'
        logger.info(f'Queued local file for File Search upload: {resolved}')
        return {'type': 'file_pending_upload', 'path': str(resolved), 'mime_type': mime_type, 'source': 'local'}

    def _resolve_local_path(self, raw_path: str, all_params: Dict[str, Any]) -> Path:
        """Resolve a local path using cwd from all_params or config, mirroring file_path resolution."""
        resolved = Path(raw_path).expanduser()
        if not resolved.is_absolute():
            cwd = all_params.get('cwd') or self.config.get('cwd')
            if cwd:
                resolved = Path(cwd).joinpath(resolved)
            else:
                resolved = resolved.resolve()
        return resolved

    def _validate_media_size(self, path: Path, limit_mb: int) -> None:
        """Validate media file size against MB limit; raise UploadFileError if exceeded."""
        file_size = path.stat().st_size
        if file_size > limit_mb * 1024 * 1024:
            logger.warning(f'Media file too large: {file_size / (1024 * 1024):.2f} MB at {path} (limit {limit_mb} MB)')
            raise UploadFileError(f'Media file size {file_size / (1024 * 1024):.2f} MB exceeds limit of {limit_mb:.0f} MB: {path}')

    def _read_base64(self, path: Path) -> Tuple[str, str]:
        """Read file bytes and return (base64, guessed_mime_type)."""
        mime_type, _ = mimetypes.guess_type(path.as_posix())
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise UploadFileError(f'Failed to read file {path}: {exc}') from exc
        encoded = base64.b64encode(data).decode('utf-8')
        return (encoded, mime_type or '')

    async def _fetch_audio_url_as_base64(self, url: str, all_params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Fetch audio from URL and return (base64_encoded_data, mime_type).

        Currently supports: wav, mp3

        Args:
            url: HTTP/HTTPS URL to fetch audio from
            all_params: Parameters dict containing optional media_max_file_size_mb

        Returns:
            Tuple of (base64_encoded_string, mime_type)

        Raises:
            UploadFileError: If fetch fails, format is unsupported, or size exceeds limit
        """
        limit_mb = all_params.get('media_max_file_size_mb') or self.config.get('media_max_file_size_mb') or MEDIA_MAX_FILE_SIZE_MB
        max_size_bytes = int(limit_mb) * 1024 * 1024
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(url, timeout=30.0)
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise UploadFileError(f'Timeout (30s) while fetching audio from {url}') from exc
            except httpx.HTTPError as exc:
                raise UploadFileError(f'Failed to fetch audio from {url}: {exc}') from exc
            content_type = response.headers.get('Content-Type', '')
            mime_type = content_type.split(';')[0].strip().lower()
            if mime_type not in SUPPORTED_AUDIO_MIME_TYPES:
                guessed_mime, _ = mimetypes.guess_type(url)
                if guessed_mime and guessed_mime.lower() in SUPPORTED_AUDIO_MIME_TYPES:
                    mime_type = guessed_mime.lower()
                else:
                    raise UploadFileError(f'Unsupported audio format for {url}. Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}')
            if mime_type in {'audio/wav', 'audio/wave', 'audio/x-wav'}:
                mime_type = 'audio/wav'
            elif mime_type in {'audio/mpeg', 'audio/mp3'}:
                mime_type = 'audio/mpeg'
            audio_bytes = response.content
            if len(audio_bytes) > max_size_bytes:
                raise UploadFileError(f'Audio file size {len(audio_bytes) / (1024 * 1024):.2f} MB exceeds limit of {limit_mb} MB: {url}')
            encoded = base64.b64encode(audio_bytes).decode('utf-8')
            logger.info(f'Fetched and encoded audio from URL: {url} ({len(audio_bytes) / (1024 * 1024):.2f} MB, {mime_type})')
            return (encoded, mime_type)

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI Response API with unified MCP/non-MCP processing."""
        agent_id = kwargs.get('agent_id', None)
        log_backend_activity(self.get_provider_name(), 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        try:
            async with self:
                client = self._create_client(**kwargs)
                try:
                    use_mcp = bool(self._mcp_functions)
                    async for chunk in self.yield_mcp_status_chunks(use_mcp):
                        yield chunk
                    if use_mcp:
                        logger.info('Using recursive MCP execution mode')
                        current_messages = self._trim_message_history(messages.copy())
                        async for chunk in self._stream_with_mcp_tools(current_messages, tools, client, **kwargs):
                            yield chunk
                    else:
                        logger.info('Using no-MCP mode')
                        async for chunk in self._stream_without_mcp_tools(messages, tools, client, **kwargs):
                            yield chunk
                except Exception as e:
                    if isinstance(e, (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError)):
                        await self._record_mcp_circuit_breaker_failure(e, agent_id)
                        async for chunk in self._stream_handle_mcp_exceptions(e, messages, tools, client, **kwargs):
                            yield chunk
                    else:
                        logger.error(f'Streaming error: {e}')
                        yield StreamChunk(type='error', error=str(e))
                finally:
                    await self._cleanup_client(client)
        except Exception as e:
            try:
                client = self._create_client(**kwargs)
                if isinstance(e, (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError)):
                    async for chunk in self._stream_handle_mcp_exceptions(e, messages, tools, client, **kwargs):
                        yield chunk
                else:
                    if self.mcp_servers:
                        yield StreamChunk(type='mcp_status', status='mcp_unavailable', content=f'⚠️ [MCP] Setup failed; continuing without MCP ({e})', source='mcp_setup')
                    async for chunk in self._stream_without_mcp_tools(messages, tools, client, **kwargs):
                        yield chunk
            except Exception as inner_e:
                logger.error(f'Streaming error during MCP setup fallback: {inner_e}')
                yield StreamChunk(type='error', error=str(inner_e))
            finally:
                await self._cleanup_client(client)

    async def _stream_without_mcp_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Simple passthrough streaming without MCP processing."""
        agent_id = kwargs.get('agent_id', None)
        all_params = {**self.config, **kwargs}
        processed_messages = await self._process_upload_files(messages, all_params)
        api_params = await self.api_params_handler.build_api_params(processed_messages, tools, all_params)
        if 'tools' in api_params:
            non_mcp_tools = []
            for tool in api_params.get('tools', []):
                if tool.get('type') == 'function':
                    name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
                    if name and name in self._mcp_function_names:
                        continue
                elif tool.get('type') == 'mcp':
                    continue
                non_mcp_tools.append(tool)
            api_params['tools'] = non_mcp_tools
        if 'openai' in self.get_provider_name().lower():
            stream = await client.responses.create(**api_params)
        elif 'claude' in self.get_provider_name().lower():
            if 'betas' in api_params:
                stream = await client.beta.messages.create(**api_params)
            else:
                stream = await client.messages.create(**api_params)
        else:
            stream = await client.chat.completions.create(**api_params)
        async for chunk in self._process_stream(stream, all_params, agent_id):
            yield chunk

    async def _stream_handle_mcp_exceptions(self, error: Exception, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Handle MCP exceptions with fallback streaming."""
        'Handle MCP errors with specific messaging and fallback to non-MCP tools.'
        async with self._stats_lock:
            self._mcp_tool_failures += 1
            call_index_snapshot = self._mcp_tool_calls_count
        if MCPErrorHandler:
            log_type, user_message, _ = MCPErrorHandler.get_error_details(error)
        else:
            log_type, user_message = ('mcp_error', '[MCP] Error occurred')
        logger.warning(f'MCP tool call #{call_index_snapshot} failed - {log_type}: {error}')
        yield StreamChunk(type='mcp_status', status='mcp_tools_failed', content=f'MCP tool call failed (call #{call_index_snapshot}): {user_message}', source='mcp_error')
        yield StreamChunk(type='content', content=f'\n⚠️  {user_message} ({error}); continuing without MCP tools\n')
        async for chunk in self._stream_without_mcp_tools(messages, tools, client, **kwargs):
            yield chunk

    def _track_mcp_function_names(self, tools: List[Dict[str, Any]]) -> None:
        """Track MCP function names for fallback filtering."""
        for tool in tools:
            if tool.get('type') == 'function':
                name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
                if name:
                    self._mcp_function_names.add(name)

    async def _check_circuit_breaker_before_execution(self) -> bool:
        """Check circuit breaker status before executing MCP functions."""
        if not (self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker and MCPSetupManager and MCPCircuitBreakerManager):
            return True
        normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
        mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers)
        filtered_servers = MCPCircuitBreakerManager.apply_circuit_breaker_filtering(mcp_tools_servers, self._mcp_tools_circuit_breaker)
        if not filtered_servers:
            logger.warning('All MCP servers blocked by circuit breaker')
            return False
        return True

    async def _record_mcp_circuit_breaker_failure(self, error: Exception, agent_id: Optional[str]=None) -> None:
        """Record MCP failure for circuit breaker if enabled."""
        if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
            try:
                normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
                mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers)
                await MCPCircuitBreakerManager.record_event(mcp_tools_servers, self._mcp_tools_circuit_breaker, 'failure', error_message=str(error), backend_name=self.backend_name, agent_id=agent_id)
            except Exception as cb_error:
                logger.warning(f'Failed to record circuit breaker failure: {cb_error}')

    async def _record_mcp_circuit_breaker_success(self, servers_to_use: List[Dict[str, Any]]) -> None:
        """Record MCP success for circuit breaker if enabled."""
        if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker and self._mcp_client and MCPCircuitBreakerManager:
            try:
                connected_server_names = self._mcp_client.get_server_names() if hasattr(self._mcp_client, 'get_server_names') else []
                if connected_server_names:
                    connected_server_configs = [server for server in servers_to_use if server.get('name') in connected_server_names]
                    if connected_server_configs:
                        await MCPCircuitBreakerManager.record_event(connected_server_configs, self._mcp_tools_circuit_breaker, 'success', backend_name=self.backend_name, agent_id=self.agent_id)
            except Exception as cb_error:
                logger.warning(f'Failed to record circuit breaker success: {cb_error}')

    def _trim_message_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trim message history to prevent unbounded growth."""
        if MCPMessageManager:
            return MCPMessageManager.trim_message_history(messages, self._max_mcp_message_history)
        return messages

    async def cleanup_mcp(self) -> None:
        """Cleanup MCP connections."""
        if self._mcp_client and MCPResourceManager:
            await MCPResourceManager.cleanup_mcp_client(self._mcp_client, backend_name=self.backend_name, agent_id=self.agent_id)
            self._mcp_client = None
            self._mcp_initialized = False
            self._mcp_functions.clear()
            self._mcp_function_names.clear()

    async def __aenter__(self) -> 'MCPBackend':
        """Async context manager entry."""
        if MCPResourceManager:
            await MCPResourceManager.setup_mcp_context_manager(self, backend_name=self.backend_name, agent_id=self.agent_id)
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        """Async context manager exit with automatic resource cleanup."""
        if MCPResourceManager:
            await MCPResourceManager.cleanup_mcp_context_manager(self, logger_instance=logger, backend_name=self.backend_name, agent_id=self.agent_id)
        return False

    def get_mcp_server_count(self) -> int:
        """Get count of stdio/streamable-http servers."""
        if not (self.mcp_servers and MCPSetupManager):
            return 0
        normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
        mcp_tools_servers = MCPSetupManager.separate_stdio_streamable_servers(normalized_servers)
        return len(mcp_tools_servers)

    def yield_mcp_status_chunks(self, use_mcp: bool) -> AsyncGenerator[StreamChunk, None]:
        """Yield MCP status chunks for connection and availability."""

        async def _generator():
            if self.mcp_servers and (not use_mcp):
                yield StreamChunk(type='mcp_status', status='mcp_unavailable', content='⚠️ [MCP] Setup failed or no tools available; continuing without MCP', source='mcp_setup')
            if use_mcp and self.mcp_servers:
                server_count = self.get_mcp_server_count()
                if server_count > 0:
                    yield StreamChunk(type='mcp_status', status='mcp_connected', content=f'✅ [MCP] Connected to {server_count} servers', source='mcp_setup')
            if use_mcp:
                yield StreamChunk(type='mcp_status', status='mcp_tools_initiated', content=f'🔧 [MCP] {len(self._mcp_functions)} tools available', source='mcp_session')
        return _generator()

    def is_mcp_tool_call(self, tool_name: str) -> bool:
        """Check if a tool call is an MCP function."""
        return tool_name in self._mcp_functions

    def get_mcp_tools_formatted(self) -> List[Dict[str, Any]]:
        """Get MCP tools formatted for specific API format."""
        if not self._mcp_functions:
            return []
        mcp_tools = []
        mcp_tools = self.formatter.format_mcp_tools(self._mcp_functions)
        self._track_mcp_function_names(mcp_tools)
        return mcp_tools

def _process_file_path_entry(self, file_path_value: str, all_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process file path entry and validate against provider-specific restrictions.

        Note: This base implementation validates against OpenAI File Search extensions.
        Backends like Claude may have additional restrictions (e.g., only .pdf and .txt)
        and should perform provider-specific validation in their upload methods.
        """
    if file_path_value.startswith(('http://', 'https://')):
        logger.info(f'Queued file URL for File Search upload: {file_path_value}')
        return {'type': 'file_pending_upload', 'url': file_path_value, 'source': 'url'}
    resolved = Path(file_path_value).expanduser()
    if not resolved.is_absolute():
        cwd = all_params.get('cwd') or self.config.get('cwd')
        if cwd:
            resolved = Path(cwd).joinpath(resolved)
        else:
            resolved = resolved.resolve()
    if not resolved.exists():
        raise UploadFileError(f'File not found: {resolved}')
    file_ext = resolved.suffix.lower()
    if file_ext not in FILE_SEARCH_SUPPORTED_EXTENSIONS:
        raise UploadFileError(f'File type {file_ext} not supported by File Search. Supported types: {', '.join(sorted(FILE_SEARCH_SUPPORTED_EXTENSIONS))}')
    file_size = resolved.stat().st_size
    if file_size > FILE_SEARCH_MAX_FILE_SIZE:
        raise UploadFileError(f'File size {file_size / (1024 * 1024):.2f} MB exceeds File Search limit of {FILE_SEARCH_MAX_FILE_SIZE / (1024 * 1024):.0f} MB')
    mime_type, _ = mimetypes.guess_type(resolved.as_posix())
    if not mime_type:
        mime_type = 'application/octet-stream'
    logger.info(f'Queued local file for File Search upload: {resolved}')
    return {'type': 'file_pending_upload', 'path': str(resolved), 'mime_type': mime_type, 'source': 'local'}

def _resolve_local_path(self, raw_path: str, all_params: Dict[str, Any]) -> Path:
    """Resolve a local path using cwd from all_params or config, mirroring file_path resolution."""
    resolved = Path(raw_path).expanduser()
    if not resolved.is_absolute():
        cwd = all_params.get('cwd') or self.config.get('cwd')
        if cwd:
            resolved = Path(cwd).joinpath(resolved)
        else:
            resolved = resolved.resolve()
    return resolved

def _validate_media_size(self, path: Path, limit_mb: int) -> None:
    """Validate media file size against MB limit; raise UploadFileError if exceeded."""
    file_size = path.stat().st_size
    if file_size > limit_mb * 1024 * 1024:
        logger.warning(f'Media file too large: {file_size / (1024 * 1024):.2f} MB at {path} (limit {limit_mb} MB)')
        raise UploadFileError(f'Media file size {file_size / (1024 * 1024):.2f} MB exceeds limit of {limit_mb:.0f} MB: {path}')

def _read_base64(self, path: Path) -> Tuple[str, str]:
    """Read file bytes and return (base64, guessed_mime_type)."""
    mime_type, _ = mimetypes.guess_type(path.as_posix())
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise UploadFileError(f'Failed to read file {path}: {exc}') from exc
    encoded = base64.b64encode(data).decode('utf-8')
    return (encoded, mime_type or '')

class ClaudeCodeBackend(LLMBackend):
    """Claude Code backend using claude-code-sdk-python.

    Provides streaming interface to Claude Code with built-in tool execution
    capabilities and MassGen workflow tool integration. Uses ClaudeSDKClient
    for direct communication with Claude Code server.

    TODO (v0.0.14 Context Sharing Enhancement - See docs/dev_notes/v0.0.14-context.md):
    - Implement permission enforcement during file/workspace operations
    - Add execute_with_permissions() method to check permissions before operations
    - Integrate with PermissionManager for access control validation
    - Add audit logging for all file system access attempts
    - Enforce workspace boundaries based on agent permissions
    - Prevent unauthorized access to other agents' workspaces
    - Support permission-aware tool execution (Read, Write, Bash, etc.)
    """

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        """Initialize ClaudeCodeBackend.

        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env
                    var). If None, will attempt to use Claude subscription
                    authentication
            **kwargs: Additional configuration options including:
                - model: Claude model name
                - system_prompt: Base system prompt
                - allowed_tools: List of allowed tools
                - max_thinking_tokens: Maximum thinking tokens
                - cwd: Current working directory

        Note:
            Authentication is validated on first use. If neither API key nor
            subscription authentication is available, errors will surface when
            attempting to use the backend.
        """
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.use_subscription_auth = not bool(self.api_key)
        if self.api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.api_key
        if sys.platform == 'win32' and (not os.environ.get('CLAUDE_CODE_GIT_BASH_PATH')):
            import shutil
            bash_path = shutil.which('bash')
            if bash_path:
                os.environ['CLAUDE_CODE_GIT_BASH_PATH'] = bash_path
                print(f'[ClaudeCodeBackend] Set CLAUDE_CODE_GIT_BASH_PATH={bash_path}')
        if sys.platform == 'win32':
            self._setup_windows_subprocess_cleanup_suppression()
        self._client: Optional[Any] = None
        self._current_session_id: Optional[str] = None
        if not self.filesystem_manager:
            raise ValueError("Claude Code backend requires 'cwd' configuration for workspace management")
        self._cwd: str = str(Path(str(self.filesystem_manager.get_current_workspace())).resolve())
        self._pending_system_prompt: Optional[str] = None

    def _setup_windows_subprocess_cleanup_suppression(self):
        """Comprehensive Windows subprocess cleanup warning suppression."""
        warnings.filterwarnings('ignore', message='unclosed transport')
        warnings.filterwarnings('ignore', message='I/O operation on closed pipe')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed transport')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed event loop')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed <socket.socket')
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='coroutine')
        warnings.filterwarnings('ignore', message='Exception ignored in')
        warnings.filterwarnings('ignore', message='sys:1: ResourceWarning')
        warnings.filterwarnings('ignore', category=ResourceWarning, message='unclosed.*transport.*')
        warnings.filterwarnings('ignore', message='.*BaseSubprocessTransport.*')
        warnings.filterwarnings('ignore', message='.*_ProactorBasePipeTransport.*')
        warnings.filterwarnings('ignore', message='.*Event loop is closed.*')
        try:
            import asyncio.base_subprocess
            import asyncio.proactor_events
            original_subprocess_del = getattr(asyncio.base_subprocess.BaseSubprocessTransport, '__del__', None)
            original_pipe_del = getattr(asyncio.proactor_events._ProactorBasePipeTransport, '__del__', None)

            def silent_subprocess_del(self):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        if original_subprocess_del:
                            original_subprocess_del(self)
                except Exception:
                    pass

            def silent_pipe_del(self):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        if original_pipe_del:
                            original_pipe_del(self)
                except Exception:
                    pass
            if original_subprocess_del:
                asyncio.base_subprocess.BaseSubprocessTransport.__del__ = silent_subprocess_del
            if original_pipe_del:
                asyncio.proactor_events._ProactorBasePipeTransport.__del__ = silent_pipe_del
        except Exception:
            pass
        original_stderr = sys.stderr

        def suppress_exit_warnings():
            try:
                sys.stderr = open(os.devnull, 'w')
                import time
                time.sleep(0.3)
            except Exception:
                pass
            finally:
                try:
                    if sys.stderr != original_stderr:
                        sys.stderr.close()
                    sys.stderr = original_stderr
                except Exception:
                    pass
        atexit.register(suppress_exit_warnings)

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return 'claude_code'

    def get_filesystem_support(self) -> FilesystemSupport:
        """Claude Code has native filesystem support."""
        return FilesystemSupport.NATIVE

    def is_stateful(self) -> bool:
        """
        Claude Code backend is stateful - maintains conversation context.

        Returns:
            True - Claude Code maintains server-side session state
        """
        return True

    async def clear_history(self) -> None:
        """
        Clear Claude Code conversation history while preserving session.

        Uses the /clear slash command to clear conversation history without
        destroying the session, working directory, or other session state.
        """
        if self._client is None:
            return
        try:
            await self._client.query('/clear')
        except Exception as e:
            print(f'Warning: /clear command failed ({e}), falling back to full reset')
            await self.reset_state()

    async def reset_state(self) -> None:
        """
        Reset Claude Code backend state.

        Properly disconnects and clears the current session and client connection to start fresh.
        """
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self._current_session_id = None

    def update_token_usage_from_result_message(self, result_message) -> None:
        """Update token usage from Claude Code ResultMessage.

        Extracts actual token usage and cost data from Claude Code server
        response. This is more accurate than estimation-based methods.

        Args:
            result_message: ResultMessage from Claude Code with usage data
        """
        if ResultMessage is not None and (not isinstance(result_message, ResultMessage)):
            return
        if not hasattr(result_message, 'usage') or not hasattr(result_message, 'total_cost_usd'):
            return
        if result_message.usage:
            usage_data = result_message.usage
            input_tokens = usage_data.get('input_tokens', 0)
            output_tokens = usage_data.get('output_tokens', 0)
            self.token_usage.input_tokens += input_tokens
            self.token_usage.output_tokens += output_tokens
        if result_message.total_cost_usd is not None:
            self.token_usage.estimated_cost += result_message.total_cost_usd
        else:
            input_tokens = result_message.usage.get('input_tokens', 0) if result_message.usage else 0
            output_tokens = result_message.usage.get('output_tokens', 0) if result_message.usage else 0
            cost = self.calculate_cost(input_tokens, output_tokens, '', result_message)
            self.token_usage.estimated_cost += cost

    def update_token_usage(self, messages: List[Dict[str, Any]], response_content: str, model: str):
        """Update token usage tracking (fallback method).

        Only used when no ResultMessage available. Provides estimated token
        tracking for compatibility with base class interface. Should only be
        called when ResultMessage data is not available.

        Args:
            messages: List of conversation messages
            response_content: Generated response content
            model: Model name for cost calculation
        """
        input_text = '\n'.join([msg.get('content', '') for msg in messages])
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(response_content)
        self.token_usage.input_tokens += input_tokens
        self.token_usage.output_tokens += output_tokens
        cost = self.calculate_cost(input_tokens, output_tokens, model, result_message=None)
        self.token_usage.estimated_cost += cost

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by Claude Code.

        Returns maximum tool set available, with security enforced through
        disallowed_tools. Dangerous operations are blocked at the tool
        level, not by restricting tool access.

        Returns:
            List of all tool names that Claude Code provides natively
        """
        return ['Read', 'Write', 'Edit', 'MultiEdit', 'Bash', 'Grep', 'Glob', 'LS', 'WebSearch', 'WebFetch', 'Task', 'TodoWrite', 'NotebookEdit', 'NotebookRead', 'mcp__ide__getDiagnostics', 'mcp__ide__executeCode', 'ExitPlanMode']

    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID from server-side session management.

        Returns:
            Current session ID if available, None otherwise
        """
        return self._current_session_id

    def _build_system_prompt_with_workflow_tools(self, tools: List[Dict[str, Any]], base_system: Optional[str]=None) -> str:
        """Build system prompt that includes workflow tools information.

        Creates comprehensive system prompt that instructs Claude on tool
        usage, particularly for MassGen workflow coordination tools.

        Args:
            tools: List of available tools
            base_system: Base system prompt to extend (optional)

        Returns:
            Complete system prompt with tool instructions
        """
        system_parts = []
        if base_system:
            system_parts.append(base_system)
        command_line_execution_mode = self.config.get('command_line_execution_mode', 'local')
        if command_line_execution_mode == 'docker':
            system_parts.append('\n--- Code Execution Environment ---')
            system_parts.append('- Use the execute_command MCP tool for all command execution')
            system_parts.append('- The Bash tool is disabled in this mode')
            system_parts.append('- Do NOT use any git repository information you may see as part of a broader directory. All git information must come from the execute_command tool and be focused solely on the directories you were told to work in, not any parent directories.')
        if tools:
            workflow_tools = [t for t in tools if t.get('function', {}).get('name') in ['new_answer', 'vote']]
            if workflow_tools:
                system_parts.append('\n--- Coordination Actions ---')
                for tool in workflow_tools:
                    name = tool.get('function', {}).get('name', 'unknown')
                    description = tool.get('function', {}).get('description', 'No description')
                    system_parts.append(f'- {name}: {description}')
                    if name == 'new_answer':
                        system_parts.append('    Usage: {"tool_name": "new_answer", "arguments": {"content": "your improved answer. If any builtin tools were used, mention how they are used here."}}')
                    elif name == 'vote':
                        agent_id_enum = None
                        for t in tools:
                            if t.get('function', {}).get('name') == 'vote':
                                agent_id_param = t.get('function', {}).get('parameters', {}).get('properties', {}).get('agent_id', {})
                                if 'enum' in agent_id_param:
                                    agent_id_enum = agent_id_param['enum']
                                break
                        if agent_id_enum:
                            agent_list = ', '.join(agent_id_enum)
                            system_parts.append(f'    Usage: {{"tool_name": "vote", "arguments": {{"agent_id": "agent1", "reason": "explanation"}}}} // Choose agent_id from: {agent_list}')
                        else:
                            system_parts.append('    Usage: {"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}')
                system_parts.append('\n--- MassGen Coordination Instructions ---')
                system_parts.append('IMPORTANT: You must respond with a structured JSON decision at the end of your response.')
                system_parts.append('The JSON MUST be formatted as a strict JSON code block:')
                system_parts.append('1. Start with ```json on one line')
                system_parts.append('2. Include your JSON content (properly formatted)')
                system_parts.append('3. End with ``` on one line')
                system_parts.append('Example format:\n```json\n{"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}\n```')
                system_parts.append('The JSON block should be placed at the very end of your response, after your analysis.')
        return '\n'.join(system_parts)

    async def _log_backend_input(self, messages, system_prompt, tools, kwargs):
        """Log backend inputs using StreamChunk for visibility (enabled by default)."""
        if os.getenv('MASSGEN_LOG_BACKENDS', '1') == '0':
            return
        try:
            reset_mode = '🔄 RESET' if kwargs.get('reset_chat') else '💬 CONTINUE'
            tools_info = f'🔧 {len(tools)} tools' if tools else '🚫 No tools'
            debug_info = f'[BACKEND] {reset_mode} | {tools_info} | Session: {self._current_session_id}'
            if system_prompt and len(system_prompt) > 0:
                debug_info += f'\n[SYSTEM_FULL] {system_prompt}'
            yield StreamChunk(type='debug', content=debug_info, source='claude_code_backend')
        except Exception as e:
            yield StreamChunk(type='debug', content=f'[BACKEND_LOG_ERROR] {str(e)}', source='claude_code_backend')

    def extract_structured_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract structured JSON response for Claude Code format.

        Looks for JSON in the format:
        {"tool_name": "vote/new_answer", "arguments": {...}}

        Args:
            response_text: The full response text to search

        Returns:
            Extracted JSON dict if found, None otherwise
        """
        try:
            import re
            markdown_json_pattern = '```json\\s*(\\{.*?\\})\\s*```'
            markdown_matches = re.findall(markdown_json_pattern, response_text, re.DOTALL)
            for match in reversed(markdown_matches):
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            json_pattern = '\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)
            for match in reversed(json_matches):
                try:
                    cleaned_match = match.strip()
                    parsed = json.loads(cleaned_match)
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            brace_count = 0
            json_start = -1
            for i, char in enumerate(response_text):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start >= 0:
                        json_block = response_text[json_start:i + 1]
                        try:
                            parsed = json.loads(json_block)
                            if isinstance(parsed, dict) and 'tool_name' in parsed:
                                return parsed
                        except json.JSONDecodeError:
                            pass
                        json_start = -1
            lines = response_text.strip().split('\n')
            json_candidates = []
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('{') and stripped.endswith('}'):
                    json_candidates.append(stripped)
                elif stripped.startswith('{'):
                    json_text = stripped
                    for j in range(i + 1, len(lines)):
                        json_text += '\n' + lines[j].strip()
                        if lines[j].strip().endswith('}'):
                            json_candidates.append(json_text)
                            break
            for candidate in reversed(json_candidates):
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            return None
        except Exception:
            return None

    def _parse_workflow_tool_calls(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse workflow tool calls from text content.

        Searches for JSON-formatted tool calls in the response text and
        converts them to the standard tool call format used by MassGen.
        Uses the extract_structured_response method for robust JSON extraction.

        Args:
            text_content: Response text to search for tool calls

        Returns:
            List of unique tool call dictionaries in standard format
        """
        tool_calls = []
        structured_response = self.extract_structured_response(text_content)
        if structured_response and isinstance(structured_response, dict):
            tool_name = structured_response.get('tool_name')
            arguments = structured_response.get('arguments', {})
            if tool_name and isinstance(arguments, dict):
                tool_calls.append({'id': f'call_{uuid.uuid4().hex[:8]}', 'type': 'function', 'function': {'name': tool_name, 'arguments': arguments}})
                return tool_calls
        seen_calls = set()
        json_patterns = ['\\{"tool_name":\\s*"([^"]+)",\\s*"arguments":\\s*(\\{[^}]*\\})\\}', '\\{\\s*"tool_name"\\s*:\\s*"([^"]+)"\\s*,\\s*"arguments"\\s*:\\s*(\\{[^}]*\\})\\s*\\}']
        for pattern in json_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                tool_name = match.group(1)
                try:
                    arguments = json.loads(match.group(2))
                    call_signature = (tool_name, json.dumps(arguments, sort_keys=True))
                    if call_signature not in seen_calls:
                        seen_calls.add(call_signature)
                        tool_calls.append({'id': f'call_{uuid.uuid4().hex[:8]}', 'type': 'function', 'function': {'name': tool_name, 'arguments': arguments}})
                except json.JSONDecodeError:
                    continue
        return tool_calls

    def _build_claude_options(self, **options_kwargs) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions with provided parameters.

        Creates a secure configuration that allows ALL Claude Code tools while
        explicitly disallowing dangerous operations. This gives Claude Code
        maximum power while maintaining security.

        Important: Sets the Claude Code preset as the default system prompt to maintain
        v0.0.x behavior. In claude-agent-sdk v0.1.0+, system prompts default to empty,
        so we explicitly request the claude_code preset.

        When command_line_execution_mode is set to "docker", the Bash tool is disabled
        since execute_command provides all necessary command execution capabilities.

        Returns:
            ClaudeAgentOptions configured with provided parameters and
            security restrictions
        """
        options_kwargs.get('cwd', os.getcwd())
        permission_mode = options_kwargs.get('permission_mode', 'acceptEdits')
        allowed_tools = options_kwargs.get('allowed_tools', self.get_supported_builtin_tools())
        excluded_params = self.get_base_excluded_config_params() | {'api_key', 'allowed_tools', 'permission_mode'}
        cwd_option = Path(str(self.filesystem_manager.get_current_workspace())).resolve()
        self._cwd = str(cwd_option)
        hooks_config = self.filesystem_manager.get_claude_code_hooks_config()
        mcp_servers_dict = {}
        if 'mcp_servers' in options_kwargs:
            mcp_servers = options_kwargs['mcp_servers']
            if isinstance(mcp_servers, list):
                for server in mcp_servers:
                    if isinstance(server, dict) and 'name' in server:
                        server_config = {k: v for k, v in server.items() if k != 'name'}
                        mcp_servers_dict[server['name']] = server_config
            elif isinstance(mcp_servers, dict):
                mcp_servers_dict = mcp_servers
        options = {'cwd': cwd_option, 'resume': self.get_current_session_id(), 'permission_mode': permission_mode, 'allowed_tools': allowed_tools, **{k: v for k, v in options_kwargs.items() if k not in excluded_params}}
        if mcp_servers_dict:
            options['mcp_servers'] = mcp_servers_dict
        if 'system_prompt' not in options:
            options['system_prompt'] = {'type': 'preset', 'preset': 'claude_code'}
        if hooks_config:
            options['hooks'] = hooks_config

        async def can_use_tool(tool_name: str, tool_args: dict, context):
            """Auto-grant permissions for MCP tools."""
            if tool_name.startswith('mcp__'):
                return PermissionResultAllow(updated_input=tool_args)
            return None
        options['can_use_tool'] = can_use_tool
        return ClaudeAgentOptions(**options)

    def create_client(self, **options_kwargs) -> ClaudeSDKClient:
        """Create ClaudeSDKClient with configurable parameters.

        Args:
            **options_kwargs: ClaudeAgentOptions parameters

        Returns:
            ClaudeSDKClient instance
        """
        options = self._build_claude_options(**options_kwargs)
        self._client = ClaudeSDKClient(options)
        return self._client

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a response with tool calling support using claude-code-sdk.

        Properly handle messages and tools context for Claude Code.

        Args:
            messages: List of conversation messages
            tools: List of available tools (includes workflow tools)
            **kwargs: Additional options for client configuration

        Yields:
            StreamChunk objects with response content and metadata
        """
        agent_id = kwargs.get('agent_id', None)
        log_backend_activity(self.get_provider_name(), 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        all_params = {**self.config, **kwargs}
        if self._client is not None:
            client = self._client
        else:
            if 'disallowed_tools' not in all_params:
                all_params['disallowed_tools'] = ['Bash(rm*)', 'Bash(sudo*)', 'Bash(su*)', 'Bash(chmod*)', 'Bash(chown*)']
            command_line_execution_mode = all_params.get('command_line_execution_mode', 'local')
            if command_line_execution_mode == 'docker':
                disallowed_tools = list(all_params.get('disallowed_tools', []))
                bash_related_tools = ['Bash', 'BashOutput', 'KillShell']
                for tool in bash_related_tools:
                    if tool not in disallowed_tools:
                        disallowed_tools.append(tool)
                all_params['disallowed_tools'] = disallowed_tools
            system_msg = next((msg for msg in messages if msg.get('role') == 'system'), None)
            if system_msg:
                system_content = system_msg.get('content', '')
            else:
                system_content = ''
            workflow_system_prompt = self._build_system_prompt_with_workflow_tools(tools or [], system_content)
            if sys.platform == 'win32' and len(workflow_system_prompt) > 200:
                print('[ClaudeCodeBackend] Windows detected complex system prompt, using post-connection delivery')
                clean_params = {k: v for k, v in all_params.items() if k not in ['system_prompt']}
                client = self.create_client(**clean_params)
                self._pending_system_prompt = workflow_system_prompt
            else:
                try:
                    system_prompt_config = {'type': 'preset', 'preset': 'claude_code', 'append': workflow_system_prompt}
                    client = self.create_client(**{**all_params, 'system_prompt': system_prompt_config})
                    self._pending_system_prompt = None
                except Exception as create_error:
                    if sys.platform == 'win32':
                        clean_params = {k: v for k, v in all_params.items() if k not in ['system_prompt']}
                        client = self.create_client(**clean_params)
                        self._pending_system_prompt = workflow_system_prompt
                    else:
                        raise create_error
        if not client._transport:
            try:
                await client.connect()
                if hasattr(self, '_pending_system_prompt') and self._pending_system_prompt:
                    try:
                        system_command = f'/system {self._pending_system_prompt}'
                        await client.query(system_command)
                        async for response in client.receive_response():
                            if hasattr(response, 'subtype') and response.subtype == 'init':
                                break
                        yield StreamChunk(type='content', content='[SYSTEM] Applied system instructions at system level\n', source='claude_code')
                        self._pending_system_prompt = None
                    except Exception as sys_e:
                        yield StreamChunk(type='content', content=f'[SYSTEM] Warning: System-level delivery failed: {str(sys_e)}\n', source='claude_code')
            except Exception as e:
                yield StreamChunk(type='error', error=f'Failed to connect to Claude Code: {str(e)}', source='claude_code')
                return
        if 'workflow_system_prompt' in locals():
            async for debug_chunk in self._log_backend_input(messages, workflow_system_prompt, tools, kwargs):
                yield debug_chunk
        if not messages:
            log_stream_chunk('backend.claude_code', 'error', 'No messages provided to stream_with_tools', agent_id)
            yield StreamChunk(type='error', error='No messages provided to stream_with_tools', source='claude_code')
            return
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        if assistant_messages:
            log_stream_chunk('backend.claude_code', 'error', 'Claude Code backend cannot accept assistant messages - it maintains its own conversation history', agent_id)
            yield StreamChunk(type='error', error='Claude Code backend cannot accept assistant messages - it maintains its own conversation history', source='claude_code')
            return
        if not user_messages:
            log_stream_chunk('backend.claude_code', 'error', 'No user messages found to send to Claude Code', agent_id)
            yield StreamChunk(type='error', error='No user messages found to send to Claude Code', source='claude_code')
            return
        user_contents = []
        for user_msg in user_messages:
            content = user_msg.get('content', '').strip()
            if content:
                user_contents.append(content)
        if user_contents:
            combined_query = '\n\n'.join(user_contents)
            log_backend_agent_message(agent_id or 'default', 'SEND', {'system': workflow_system_prompt, 'user': combined_query}, backend_name=self.get_provider_name())
            await client.query(combined_query)
        else:
            log_stream_chunk('backend.claude_code', 'error', 'All user messages were empty', agent_id)
            yield StreamChunk(type='error', error='All user messages were empty', source='claude_code')
            return
        accumulated_content = ''
        try:
            async for message in client.receive_response():
                if isinstance(message, (AssistantMessage, UserMessage)):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            accumulated_content += block.text
                            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': block.text}, backend_name=self.get_provider_name())
                            log_stream_chunk('backend.claude_code', 'content', block.text, agent_id)
                            yield StreamChunk(type='content', content=block.text, source='claude_code')
                        elif isinstance(block, ToolUseBlock):
                            log_backend_activity(self.get_provider_name(), f'Builtin tool called: {block.name}', {'tool_id': block.id}, agent_id=agent_id)
                            log_stream_chunk('backend.claude_code', 'tool_use', {'name': block.name, 'input': block.input}, agent_id)
                            yield StreamChunk(type='content', content=f'🔧 {block.name}({block.input})', source='claude_code')
                        elif isinstance(block, ToolResultBlock):
                            status = '❌ Error' if block.is_error else '✅ Result'
                            log_stream_chunk('backend.claude_code', 'tool_result', {'is_error': block.is_error, 'content': block.content}, agent_id)
                            yield StreamChunk(type='content', content=f'🔧 Tool {status}: {block.content}', source='claude_code')
                    workflow_tool_calls = self._parse_workflow_tool_calls(accumulated_content)
                    if workflow_tool_calls:
                        log_stream_chunk('backend.claude_code', 'tool_calls', workflow_tool_calls, agent_id)
                        yield StreamChunk(type='tool_calls', tool_calls=workflow_tool_calls, source='claude_code')
                    log_stream_chunk('backend.claude_code', 'complete_message', accumulated_content[:200] if len(accumulated_content) > 200 else accumulated_content, agent_id)
                    yield StreamChunk(type='complete_message', complete_message={'role': 'assistant', 'content': accumulated_content}, source='claude_code')
                elif isinstance(message, SystemMessage):
                    self._track_session_info(message=message)
                    log_stream_chunk('backend.claude_code', 'backend_status', {'subtype': message.subtype, 'data': message.data}, agent_id)
                    yield StreamChunk(type='backend_status', status=message.subtype, content=json.dumps(message.data), source='claude_code')
                elif isinstance(message, ResultMessage):
                    self._track_session_info(message)
                    self.update_token_usage_from_result_message(message)
                    log_stream_chunk('backend.claude_code', 'complete_response', {'session_id': message.session_id, 'cost_usd': message.total_cost_usd}, agent_id)
                    yield StreamChunk(type='complete_response', complete_message={'session_id': message.session_id, 'duration_ms': message.duration_ms, 'cost_usd': message.total_cost_usd, 'usage': message.usage, 'is_error': message.is_error}, source='claude_code')
                    log_stream_chunk('backend.claude_code', 'done', None, agent_id)
                    yield StreamChunk(type='done', source='claude_code')
                    break
        except Exception as e:
            error_msg = str(e)
            if 'git-bash' in error_msg.lower() or 'bash.exe' in error_msg.lower():
                error_msg += '\n\nWindows Setup Required:\n1. Install Git Bash: https://git-scm.com/downloads/win\n2. Ensure git-bash is in PATH, or set: CLAUDE_CODE_GIT_BASH_PATH=C:\\Program Files\\Git\\bin\\bash.exe'
            elif 'exit code 1' in error_msg and 'win32' in str(sys.platform):
                error_msg += '\n\nThis may indicate missing git-bash on Windows. Please install Git Bash from https://git-scm.com/downloads/win'
            log_stream_chunk('backend.claude_code', 'error', error_msg, agent_id)
            yield StreamChunk(type='error', error=f'Claude Code streaming error: {str(error_msg)}', source='claude_code')

    def _track_session_info(self, message) -> None:
        """Track session information from Claude Code server responses.

        Extracts and stores session ID, working directory, and other session
        metadata from ResultMessage and SystemMessage responses to enable
        session continuation and state management across multiple interactions.

        Args:
            message: Message from Claude Code (ResultMessage or SystemMessage)
                    potentially containing session information
        """
        if ResultMessage is not None and isinstance(message, ResultMessage):
            if hasattr(message, 'session_id') and message.session_id:
                old_session_id = self._current_session_id
                self._current_session_id = message.session_id
        elif SystemMessage is not None and isinstance(message, SystemMessage):
            if hasattr(message, 'data') and isinstance(message.data, dict):
                if 'session_id' in message.data and message.data['session_id']:
                    old_session_id = self._current_session_id
                    self._current_session_id = message.data['session_id']
                    if old_session_id != self._current_session_id:
                        print(f'[ClaudeCodeBackend] Session ID from SystemMessage: {old_session_id} → {self._current_session_id}')
                if 'cwd' in message.data and message.data['cwd']:
                    self._cwd = message.data['cwd']

    async def disconnect(self):
        """Disconnect the ClaudeSDKClient and clean up resources.

        Properly closes the connection and resets internal state.
        Should be called when the backend is no longer needed.
        """
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            finally:
                self._client = None
                self._current_session_id = None

    def __del__(self):
        """Cleanup on destruction.

        Note: This won't work for async cleanup in practice.
        Use explicit disconnect() calls for proper resource cleanup.
        """

def suppress_exit_warnings():
    try:
        sys.stderr = open(os.devnull, 'w')
        import time
        time.sleep(0.3)
    except Exception:
        pass
    finally:
        try:
            if sys.stderr != original_stderr:
                sys.stderr.close()
            sys.stderr = original_stderr
        except Exception:
            pass

class CLIBackend(LLMBackend):
    """Abstract base class for CLI-based LLM backends."""

    def __init__(self, cli_command: str, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.cli_command = cli_command
        self.working_dir = kwargs.get('working_dir', Path.cwd())
        self.timeout = kwargs.get('timeout', 300)

    @abstractmethod
    def _build_command(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> List[str]:
        """Build the CLI command to execute.

        Args:
            messages: Conversation messages
            tools: Available tools
            **kwargs: Additional parameters

        Returns:
            List of command arguments for subprocess
        """

    @abstractmethod
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse CLI output into structured format.

        Args:
            output: Raw CLI output

        Returns:
            Parsed response data
        """

    async def _execute_cli_command(self, command: List[str]) -> str:
        """Execute CLI command asynchronously.

        Args:
            command: Command arguments

        Returns:
            Command output

        Raises:
            subprocess.CalledProcessError: If command fails
            asyncio.TimeoutError: If command times out
        """
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=self.working_dir)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                raise subprocess.CalledProcessError(process.returncode, command, error_msg)
            return stdout.decode('utf-8')
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise asyncio.TimeoutError(f'CLI command timed out after {self.timeout} seconds') from exc

    def _create_temp_file(self, content: str, suffix: str='.txt') -> Path:
        """Create a temporary file with content.

        Args:
            content: File content
            suffix: File suffix

        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            return Path(temp_file.name)

    def _format_messages_for_cli(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for CLI input.

        Args:
            messages: Conversation messages

        Returns:
            Formatted string for CLI
        """
        formatted_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                formatted_parts.append(f'System: {content}')
            elif role == 'user':
                formatted_parts.append(f'User: {content}')
            elif role == 'assistant':
                formatted_parts.append(f'Assistant: {content}')
        return '\n\n'.join(formatted_parts)

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response with tools support."""
        try:
            command = self._build_command(messages, tools, **kwargs)
            output = await self._execute_cli_command(command)
            parsed_response = self._parse_output(output)
            async for chunk in self._convert_to_stream_chunks(parsed_response):
                yield chunk
        except Exception as e:
            yield StreamChunk(type='error', error=f'CLI backend error: {str(e)}', source=self.__class__.__name__)

    async def _convert_to_stream_chunks(self, response: Dict[str, Any]) -> AsyncGenerator[StreamChunk, None]:
        """Convert parsed response to stream chunks.

        Args:
            response: Parsed response data

        Yields:
            StreamChunk objects
        """
        if 'content' in response and response['content']:
            yield StreamChunk(type='content', content=response['content'], source=self.__class__.__name__)
        if 'tool_calls' in response and response['tool_calls']:
            yield StreamChunk(type='tool_calls', tool_calls=response['tool_calls'], source=self.__class__.__name__)
        yield StreamChunk(type='complete_message', complete_message=response, source=self.__class__.__name__)
        yield StreamChunk(type='done', source=self.__class__.__name__)

    def get_token_usage(self) -> TokenUsage:
        """Get token usage statistics."""
        return self.token_usage

    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token for this provider."""
        return {'input': 0.0, 'output': 0.0}

    def get_model_name(self) -> str:
        """Get the model name being used."""
        return self.config.get('model', 'unknown')

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {'provider': self.__class__.__name__, 'cli_command': self.cli_command, 'model': self.get_model_name(), 'supports_tools': True, 'supports_streaming': True}

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return self.__class__.__name__

def _create_temp_file(self, content: str, suffix: str='.txt') -> Path:
    """Create a temporary file with content.

        Args:
            content: File content
            suffix: File suffix

        Returns:
            Path to temporary file
        """
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
        temp_file.write(content)
        return Path(temp_file.name)

class ClaudeBackend(MCPBackend):
    """Claude backend using Anthropic's Messages API with full multi-tool support."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.search_count = 0
        self.code_session_hours = 0.0
        self.formatter = ClaudeFormatter()
        self.api_params_handler = ClaudeAPIParamsHandler(self)
        self._uploaded_file_ids: List[str] = []

    def supports_upload_files(self) -> bool:
        """Claude Vision supports inline images; Files API handles PDFs and text docs."""
        return True

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Override to ensure Files API cleanup happens after streaming completes."""
        try:
            async for chunk in super().stream_with_tools(messages, tools, **kwargs):
                yield chunk
        finally:
            await self._cleanup_files_api_resources(**kwargs)

    async def _process_upload_files(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert upload_files entries into Claude-compatible multimodal content."""
        processed_messages = await super()._process_upload_files(messages, all_params)
        if not processed_messages:
            return processed_messages
        allowed_mime_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        max_image_size_bytes = 5 * 1024 * 1024
        for message in processed_messages:
            content = message.get('content')
            if not isinstance(content, list):
                continue
            converted_items: List[Dict[str, Any]] = []
            for item in content:
                if not isinstance(item, dict):
                    converted_items.append(item)
                    continue
                item_type = item.get('type')
                if item_type == 'file_pending_upload':
                    converted_items.append(item)
                    continue
                if item_type != 'image':
                    converted_items.append(item)
                    continue
                if 'source' in item and isinstance(item['source'], dict):
                    converted_items.append(item)
                    continue
                if 'base64' in item:
                    mime_type = (item.get('mime_type') or '').lower()
                    if mime_type not in allowed_mime_types:
                        raise UploadFileError(f'Unsupported Claude image MIME type: {mime_type or 'unknown'}')
                    try:
                        decoded = base64.b64decode(item['base64'], validate=True)
                    except binascii.Error as exc:
                        raise UploadFileError('Invalid base64 image data') from exc
                    if len(decoded) > max_image_size_bytes:
                        raise UploadFileError('Claude Vision image exceeds 5MB size limit')
                    converted_item = {key: value for key, value in item.items() if key not in {'base64', 'mime_type'}}
                    converted_item['type'] = 'image'
                    converted_item['source'] = {'type': 'base64', 'media_type': mime_type, 'data': item['base64']}
                    logger.debug('Converted base64 image for Claude Vision: %s', converted_item.get('source_path', 'inline'))
                    converted_items.append(converted_item)
                    continue
                if 'url' in item:
                    converted_item = {key: value for key, value in item.items() if key != 'url'}
                    converted_item['type'] = 'image'
                    converted_item['source'] = {'type': 'url', 'url': item['url']}
                    logger.debug('Converted URL image for Claude Vision: %s', item['url'])
                    converted_items.append(converted_item)
                    continue
                if 'file_id' in item:
                    converted_item = {key: value for key, value in item.items() if key != 'file_id'}
                    converted_item['type'] = 'image'
                    converted_item['source'] = {'type': 'file', 'file_id': item['file_id']}
                    logger.debug('Attached Claude file_id reference for image: %s', item['file_id'])
                    converted_items.append(converted_item)
                    continue
                converted_items.append(item)
            message['content'] = converted_items
        return processed_messages

    async def _upload_files_via_files_api(self, messages: List[Dict[str, Any]], client, agent_id: Optional[str]=None) -> List[Dict[str, Any]]:
        """Upload files via Claude Files API and replace pending markers with document blocks.

        Claude Files API only supports PDF and TXT files. Unsupported files are gracefully
        skipped and replaced with informative text notes to maintain workflow continuity.
        """
        CLAUDE_FILES_API_SUPPORTED_EXTENSIONS = {'.pdf', '.txt'}
        CLAUDE_FILES_API_SUPPORTED_MIME_TYPES = {'application/pdf', 'text/plain', 'text/txt'}
        file_locations: List[Tuple[int, int]] = []
        for msg_idx, message in enumerate(messages):
            content = message.get('content')
            if not isinstance(content, list):
                continue
            for item_idx, item in enumerate(content):
                if isinstance(item, dict) and item.get('type') == 'file_pending_upload':
                    file_locations.append((msg_idx, item_idx))
        if not file_locations:
            return messages
        httpx_client = None
        try:
            httpx_client = httpx.AsyncClient()
            uploaded_files: List[Tuple[int, int, str]] = []
            skipped_files: List[Tuple[int, int, str, str]] = []
            failed_uploads: List[Tuple[int, int, str, str]] = []
            for msg_idx, item_idx in file_locations:
                marker = messages[msg_idx]['content'][item_idx]
                source = marker.get('source')
                file_path = marker.get('path')
                url = marker.get('url')
                mime_type = marker.get('mime_type', 'application/octet-stream')
                filename_hint = marker.get('filename') or marker.get('name')
                file_ext = None
                filename = None
                if source == 'local' and file_path:
                    file_ext = Path(file_path).suffix.lower()
                    filename = Path(file_path).name
                    guessed_mime, _ = mimetypes.guess_type(file_path)
                    if guessed_mime:
                        mime_type = guessed_mime
                elif source == 'url' and url:
                    url_path = url.split('?')[0].split('#')[0]
                    file_ext = Path(url_path).suffix.lower()
                    filename = Path(url_path).name or url
                    if not filename_hint:
                        filename_hint = filename
                    guessed_mime, _ = mimetypes.guess_type(url_path)
                    if guessed_mime:
                        mime_type = guessed_mime
                is_supported = False
                skip_reason = None
                if file_ext and file_ext.lower() in CLAUDE_FILES_API_SUPPORTED_EXTENSIONS:
                    if mime_type and mime_type.lower() in CLAUDE_FILES_API_SUPPORTED_MIME_TYPES:
                        is_supported = True
                    else:
                        skip_reason = f"MIME type '{mime_type}' not supported (extension {file_ext} is valid)"
                else:
                    skip_reason = f"File extension '{file_ext or 'unknown'}' not supported"
                if not is_supported:
                    logger.warning(f'[Agent {agent_id or 'default'}] Skipping unsupported file for Claude Files API: {filename or file_path or url} - {skip_reason}. Only PDF and TXT files are supported.')
                    skipped_files.append((msg_idx, item_idx, filename or file_path or url or 'unknown', skip_reason))
                    continue
                try:
                    if source == 'local' and file_path:
                        path_obj = Path(file_path)
                        filename = path_obj.name
                        with open(file_path, 'rb') as f:
                            file_bytes = f.read()
                        uploaded_file = await client.beta.files.upload(file=(filename, file_bytes, mime_type))
                        file_id = getattr(uploaded_file, 'id', None)
                        if file_id:
                            self._uploaded_file_ids.append(file_id)
                            uploaded_files.append((msg_idx, item_idx, file_id))
                            logger.info(f'[Agent {agent_id or 'default'}] Uploaded local file via Files API: {filename} -> {file_id}')
                        else:
                            failure_reason = 'Claude Files API response missing file_id'
                            failed_uploads.append((msg_idx, item_idx, filename or filename_hint or file_path or 'unknown', failure_reason))
                            logger.warning(f'[Agent {agent_id or 'default'}] Failed to upload file via Files API: {failure_reason}')
                    elif source == 'url' and url:
                        response = await httpx_client.get(url, timeout=30.0)
                        response.raise_for_status()
                        max_size_bytes = 500 * 1024 * 1024
                        content_length = response.headers.get('Content-Length')
                        if content_length:
                            file_size = int(content_length)
                            if file_size > max_size_bytes:
                                raise UploadFileError(f'File size {file_size / (1024 * 1024):.2f} MB exceeds Claude Files API limit of 500 MB')
                        file_bytes = response.content
                        if len(file_bytes) > max_size_bytes:
                            raise UploadFileError(f'Downloaded file size {len(file_bytes) / (1024 * 1024):.2f} MB exceeds Claude Files API limit of 500 MB')
                        filename = url.split('/')[-1] or 'document'
                        uploaded_file = await client.beta.files.upload(file=(filename, file_bytes, mime_type))
                        file_id = getattr(uploaded_file, 'id', None)
                        if file_id:
                            self._uploaded_file_ids.append(file_id)
                            uploaded_files.append((msg_idx, item_idx, file_id))
                            logger.info(f'[Agent {agent_id or 'default'}] Uploaded URL file via Files API: {url} -> {file_id}')
                        else:
                            failure_reason = 'Claude Files API response missing file_id'
                            failed_uploads.append((msg_idx, item_idx, filename or filename_hint or url or 'unknown', failure_reason))
                            logger.warning(f'[Agent {agent_id or 'default'}] Failed to upload file via Files API: {failure_reason}')
                except Exception as upload_error:
                    logger.warning(f'[Agent {agent_id or 'default'}] Failed to upload file via Files API: {upload_error}')
                    failure_context = filename or filename_hint or file_path or url or 'unknown'
                    failed_uploads.append((msg_idx, item_idx, failure_context, str(upload_error)))
                    continue
        except Exception as e:
            logger.warning(f'[Agent {agent_id or 'default'}] Files API upload error: {e}')
            raise UploadFileError(f'Files API upload failed: {e}') from e
        finally:
            if httpx_client:
                await httpx_client.aclose()
        updated_messages = [msg.copy() for msg in messages]
        for msg_idx, item_idx, file_id in reversed(uploaded_files):
            content = updated_messages[msg_idx]['content']
            if isinstance(content, list):
                document_block = {'type': 'document', 'source': {'type': 'file', 'file_id': file_id}}
                new_content = content[:item_idx] + [document_block] + content[item_idx + 1:]
                updated_messages[msg_idx]['content'] = new_content
        for msg_idx, item_idx, filename, reason in reversed(skipped_files):
            content = updated_messages[msg_idx]['content']
            if isinstance(content, list):
                text_note = {'type': 'text', 'text': f"\n[Note: File '{filename}' was not uploaded to Claude Files API. Reason: {reason}. Claude Files API only supports PDF and TXT files.]\n"}
                new_content = content[:item_idx] + [text_note] + content[item_idx + 1:]
                updated_messages[msg_idx]['content'] = new_content
        for msg_idx, item_idx, filename, reason in reversed(failed_uploads):
            content = updated_messages[msg_idx]['content']
            if isinstance(content, list):
                text_note = {'type': 'text', 'text': f"\n[Note: File '{filename}' failed to upload to Claude Files API. Reason: {reason}.]\n"}
                new_content = content[:item_idx] + [text_note] + content[item_idx + 1:]
                updated_messages[msg_idx]['content'] = new_content
        self._ensure_no_pending_upload_markers(updated_messages)
        return updated_messages

    async def _cleanup_files_api_resources(self, **kwargs) -> None:
        """Clean up uploaded files via Files API."""
        if not self._uploaded_file_ids:
            return
        agent_id = kwargs.get('agent_id')
        logger.info(f'[Agent {agent_id or 'default'}] Cleaning up {len(self._uploaded_file_ids)} Files API resources...')
        client = None
        try:
            client = self._create_client(**kwargs)
            for file_id in self._uploaded_file_ids:
                try:
                    await client.beta.files.delete(file_id)
                    logger.debug(f'[Agent {agent_id or 'default'}] Deleted Files API file: {file_id}')
                except Exception as delete_error:
                    logger.warning(f'[Agent {agent_id or 'default'}] Failed to delete Files API file {file_id}: {delete_error}')
                    continue
            self._uploaded_file_ids.clear()
            logger.info(f'[Agent {agent_id or 'default'}] Files API cleanup completed')
        except Exception as e:
            logger.warning(f'[Agent {agent_id or 'default'}] Files API cleanup error: {e}')
        finally:
            if client and hasattr(client, 'aclose'):
                await client.aclose()

    def _ensure_no_pending_upload_markers(self, messages: List[Dict[str, Any]]) -> None:
        """Raise UploadFileError if any file_pending_upload markers remain."""
        if not messages:
            return
        for msg_idx, message in enumerate(messages):
            content = message.get('content')
            if not isinstance(content, list):
                continue
            for item_idx, item in enumerate(content):
                if isinstance(item, dict) and item.get('type') == 'file_pending_upload':
                    identifier = item.get('filename') or item.get('name') or item.get('path') or item.get('url') or 'unknown'
                    raise UploadFileError(f'Claude Files API upload left unresolved file_pending_upload marker (message {msg_idx}, item {item_idx}, source {identifier}).')

    async def _stream_without_mcp_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Override to integrate Files API uploads into non-MCP streaming."""
        agent_id = kwargs.get('agent_id', None)
        all_params = {**self.config, **kwargs}
        processed_messages = await self._process_upload_files(messages, all_params)
        if all_params.get('_has_file_search_files'):
            logger.info('Processing Files API uploads...')
            processed_messages = await self._upload_files_via_files_api(processed_messages, client, agent_id)
            all_params['_has_files_api_files'] = True
            all_params.pop('_has_file_search_files', None)
        self._ensure_no_pending_upload_markers(processed_messages)
        api_params = await self.api_params_handler.build_api_params(processed_messages, tools, all_params)
        if 'tools' in api_params:
            non_mcp_tools = []
            for tool in api_params.get('tools', []):
                if tool.get('type') == 'function':
                    name = tool.get('function', {}).get('name') if 'function' in tool else tool.get('name')
                    if name and name in self._mcp_function_names:
                        continue
                elif tool.get('type') == 'mcp':
                    continue
                non_mcp_tools.append(tool)
            if non_mcp_tools:
                api_params['tools'] = non_mcp_tools
            else:
                api_params.pop('tools', None)
        if 'betas' in api_params:
            stream = await client.beta.messages.create(**api_params)
        else:
            stream = await client.messages.create(**api_params)
        async for chunk in self._process_stream(stream, all_params, agent_id):
            yield chunk

    async def _stream_with_mcp_tools(self, current_messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Recursively stream responses, executing MCP function calls when detected."""
        all_params = {**self.config, **kwargs}
        if all_params.get('_has_file_search_files'):
            logger.info('Processing Files API uploads in MCP mode...')
            agent_id = kwargs.get('agent_id')
            current_messages = await self._upload_files_via_files_api(current_messages, client, agent_id)
            all_params['_has_files_api_files'] = True
            all_params.pop('_has_file_search_files', None)
        self._ensure_no_pending_upload_markers(current_messages)
        api_params = await self.api_params_handler.build_api_params(current_messages, tools, all_params)
        agent_id = kwargs.get('agent_id', None)
        if 'betas' in api_params:
            stream = await client.beta.messages.create(**api_params)
        else:
            stream = await client.messages.create(**api_params)
        content = ''
        current_tool_uses: Dict[str, Dict[str, Any]] = {}
        mcp_tool_calls: List[Dict[str, Any]] = []
        response_completed = False
        async for event in stream:
            try:
                if event.type == 'message_start':
                    continue
                elif event.type == 'content_block_start':
                    if hasattr(event, 'content_block'):
                        if event.content_block.type == 'tool_use':
                            tool_id = event.content_block.id
                            tool_name = event.content_block.name
                            current_tool_uses[tool_id] = {'id': tool_id, 'name': tool_name, 'input': '', 'index': getattr(event, 'index', None)}
                        elif event.content_block.type == 'server_tool_use':
                            tool_id = event.content_block.id
                            tool_name = event.content_block.name
                            current_tool_uses[tool_id] = {'id': tool_id, 'name': tool_name, 'input': '', 'index': getattr(event, 'index', None), 'server_side': True}
                            if tool_name == 'code_execution':
                                yield StreamChunk(type='content', content='\n💻 [Code Execution] Starting...\n')
                            elif tool_name == 'web_search':
                                yield StreamChunk(type='content', content='\n🔍 [Web Search] Starting search...\n')
                        elif event.content_block.type == 'code_execution_tool_result':
                            result_block = event.content_block
                            result_parts = []
                            if hasattr(result_block, 'stdout') and result_block.stdout:
                                result_parts.append(f'Output: {result_block.stdout.strip()}')
                            if hasattr(result_block, 'stderr') and result_block.stderr:
                                result_parts.append(f'Error: {result_block.stderr.strip()}')
                            if hasattr(result_block, 'return_code') and result_block.return_code != 0:
                                result_parts.append(f'Exit code: {result_block.return_code}')
                            if result_parts:
                                result_text = f'\n💻 [Code Execution Result]\n{chr(10).join(result_parts)}\n'
                                yield StreamChunk(type='content', content=result_text)
                elif event.type == 'content_block_delta':
                    if hasattr(event, 'delta'):
                        if event.delta.type == 'text_delta':
                            text_chunk = event.delta.text
                            content += text_chunk
                            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': text_chunk}, backend_name='claude')
                            log_stream_chunk('backend.claude', 'content', text_chunk, agent_id)
                            yield StreamChunk(type='content', content=text_chunk)
                        elif event.delta.type == 'input_json_delta':
                            if hasattr(event, 'index'):
                                for tool_id, tool_data in current_tool_uses.items():
                                    if tool_data.get('index') == event.index:
                                        partial_json = getattr(event.delta, 'partial_json', '')
                                        tool_data['input'] += partial_json
                                        break
                elif event.type == 'content_block_stop':
                    if hasattr(event, 'index'):
                        for tool_id, tool_data in current_tool_uses.items():
                            if tool_data.get('index') == event.index and tool_data.get('server_side'):
                                tool_name = tool_data.get('name', '')
                                tool_input = tool_data.get('input', '')
                                try:
                                    parsed_input = json.loads(tool_input) if tool_input else {}
                                except json.JSONDecodeError:
                                    parsed_input = {'raw_input': tool_input}
                                if tool_name == 'code_execution':
                                    code = parsed_input.get('code', '')
                                    if code:
                                        yield StreamChunk(type='content', content=f'💻 [Code] {code}\n')
                                    yield StreamChunk(type='content', content='✅ [Code Execution] Completed\n')
                                elif tool_name == 'web_search':
                                    query = parsed_input.get('query', '')
                                    if query:
                                        yield StreamChunk(type='content', content=f"🔍 [Query] '{query}'\n")
                                    yield StreamChunk(type='content', content='✅ [Web Search] Completed\n')
                                tool_data['processed'] = True
                                break
                elif event.type == 'message_delta':
                    pass
                elif event.type == 'message_stop':
                    non_mcp_tool_calls = []
                    if current_tool_uses:
                        for tool_use in current_tool_uses.values():
                            tool_name = tool_use.get('name', '')
                            is_server_side = tool_use.get('server_side', False)
                            if is_server_side:
                                continue
                            tool_input = tool_use.get('input', '')
                            try:
                                parsed_input = json.loads(tool_input) if tool_input else {}
                            except json.JSONDecodeError:
                                parsed_input = {'raw_input': tool_input}
                            if self.is_mcp_tool_call(tool_name):
                                mcp_tool_calls.append({'id': tool_use['id'], 'type': 'function', 'function': {'name': tool_name, 'arguments': parsed_input}})
                            else:
                                non_mcp_tool_calls.append({'id': tool_use['id'], 'type': 'function', 'function': {'name': tool_name, 'arguments': parsed_input}})
                    if non_mcp_tool_calls:
                        log_stream_chunk('backend.claude', 'tool_calls', non_mcp_tool_calls, agent_id)
                        yield StreamChunk(type='tool_calls', tool_calls=non_mcp_tool_calls)
                    response_completed = True
                    break
            except Exception as event_error:
                error_msg = f'Event processing error: {event_error}'
                log_stream_chunk('backend.claude', 'error', error_msg, agent_id)
                yield StreamChunk(type='error', error=error_msg)
                continue
        if response_completed and mcp_tool_calls:
            if not await self._check_circuit_breaker_before_execution():
                yield StreamChunk(type='mcp_status', status='mcp_blocked', content='⚠️ [MCP] All servers blocked by circuit breaker', source='circuit_breaker')
                yield StreamChunk(type='done')
                return
            updated_messages = current_messages.copy()
            assistant_content = []
            if content:
                assistant_content.append({'type': 'text', 'text': content})
            for tool_call in mcp_tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                tool_id = tool_call['id']
                assistant_content.append({'type': 'tool_use', 'id': tool_id, 'name': tool_name, 'input': tool_args})
            updated_messages.append({'role': 'assistant', 'content': assistant_content})
            for tool_call in mcp_tool_calls:
                function_name = tool_call['function']['name']
                yield StreamChunk(type='mcp_status', status='mcp_tool_called', content=f'🔧 [MCP Tool] Calling {function_name}...', source=f'mcp_{function_name}')
                try:
                    args_json = json.dumps(tool_call['function']['arguments']) if isinstance(tool_call['function'].get('arguments'), (dict, list)) else tool_call['function'].get('arguments', '{}')
                    result_list = await self._execute_mcp_function_with_retry(function_name, args_json)
                    if not result_list or (isinstance(result_list[0], str) and result_list[0].startswith('Error:')):
                        logger.warning(f'MCP function {function_name} failed after retries: {(result_list[0] if result_list else 'unknown error')}')
                        continue
                    result_str = result_list[0]
                    result_obj = result_list[1] if len(result_list) > 1 else None
                except Exception as e:
                    logger.error(f'Unexpected error in MCP function execution: {e}')
                    continue
                tool_result_msg = {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': tool_call['id'], 'content': result_str}]}
                updated_messages.append(tool_result_msg)
                yield StreamChunk(type='mcp_status', status='function_call', content=f'Arguments for Calling {function_name}: {json.dumps(tool_call['function'].get('arguments', {}))}', source=f'mcp_{function_name}')
                result_display = None
                try:
                    if hasattr(result_obj, 'content') and result_obj.content:
                        part = result_obj.content[0]
                        if hasattr(part, 'text'):
                            result_display = str(part.text)
                except Exception:
                    result_display = None
                if result_display:
                    yield StreamChunk(type='mcp_status', status='function_call_output', content=f'Results for Calling {function_name}: {result_display}', source=f'mcp_{function_name}')
                else:
                    yield StreamChunk(type='mcp_status', status='function_call_output', content=f'Results for Calling {function_name}: {result_str}', source=f'mcp_{function_name}')
                logger.info(f'Executed MCP function {function_name} (stdio/streamable-http)')
                yield StreamChunk(type='mcp_status', status='mcp_tool_response', content=f'✅ [MCP Tool] {function_name} completed', source=f'mcp_{function_name}')
            updated_messages = self._trim_message_history(updated_messages)
            async for chunk in self._stream_with_mcp_tools(updated_messages, tools, client, **kwargs):
                yield chunk
            return
        else:
            complete_message = {'role': 'assistant', 'content': content.strip()}
            log_stream_chunk('backend.claude', 'complete_message', complete_message, agent_id)
            yield StreamChunk(type='complete_message', complete_message=complete_message)
            yield StreamChunk(type='mcp_status', status='mcp_session_complete', content='✅ [MCP] Session completed', source='mcp_session')
            yield StreamChunk(type='done')
            return

    async def _process_stream(self, stream, all_params: Dict[str, Any], agent_id: Optional[str]) -> AsyncGenerator[StreamChunk, None]:
        """Process stream events and yield StreamChunks."""
        content_local = ''
        current_tool_uses_local: Dict[str, Dict[str, Any]] = {}
        async for chunk in stream:
            try:
                if chunk.type == 'message_start':
                    continue
                elif chunk.type == 'content_block_start':
                    if hasattr(chunk, 'content_block'):
                        if chunk.content_block.type == 'tool_use':
                            tool_id = chunk.content_block.id
                            tool_name = chunk.content_block.name
                            current_tool_uses_local[tool_id] = {'id': tool_id, 'name': tool_name, 'input': '', 'index': getattr(chunk, 'index', None)}
                        elif chunk.content_block.type == 'server_tool_use':
                            tool_id = chunk.content_block.id
                            tool_name = chunk.content_block.name
                            current_tool_uses_local[tool_id] = {'id': tool_id, 'name': tool_name, 'input': '', 'index': getattr(chunk, 'index', None), 'server_side': True}
                            if tool_name == 'code_execution':
                                yield StreamChunk(type='content', content='\n💻 [Code Execution] Starting...\n')
                            elif tool_name == 'web_search':
                                yield StreamChunk(type='content', content='\n🔍 [Web Search] Starting search...\n')
                        elif chunk.content_block.type == 'code_execution_tool_result':
                            result_block = chunk.content_block
                            result_parts = []
                            if hasattr(result_block, 'stdout') and result_block.stdout:
                                result_parts.append(f'Output: {result_block.stdout.strip()}')
                            if hasattr(result_block, 'stderr') and result_block.stderr:
                                result_parts.append(f'Error: {result_block.stderr.strip()}')
                            if hasattr(result_block, 'return_code') and result_block.return_code != 0:
                                result_parts.append(f'Exit code: {result_block.return_code}')
                            if result_parts:
                                result_text = f'\n💻 [Code Execution Result]\n{chr(10).join(result_parts)}\n'
                                yield StreamChunk(type='content', content=result_text)
                elif chunk.type == 'content_block_delta':
                    if hasattr(chunk, 'delta'):
                        if chunk.delta.type == 'text_delta':
                            text_chunk = chunk.delta.text
                            content_local += text_chunk
                            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': text_chunk}, backend_name='claude')
                            log_stream_chunk('backend.claude', 'content', text_chunk, agent_id)
                            yield StreamChunk(type='content', content=text_chunk)
                        elif chunk.delta.type == 'input_json_delta':
                            if hasattr(chunk, 'index'):
                                for tool_id, tool_data in current_tool_uses_local.items():
                                    if tool_data.get('index') == chunk.index:
                                        partial_json = getattr(chunk.delta, 'partial_json', '')
                                        tool_data['input'] += partial_json
                                        break
                elif chunk.type == 'content_block_stop':
                    if hasattr(chunk, 'index'):
                        for tool_id, tool_data in current_tool_uses_local.items():
                            if tool_data.get('index') == chunk.index and tool_data.get('server_side'):
                                tool_name = tool_data.get('name', '')
                                tool_input = tool_data.get('input', '')
                                try:
                                    parsed_input = json.loads(tool_input) if tool_input else {}
                                except json.JSONDecodeError:
                                    parsed_input = {'raw_input': tool_input}
                                if tool_name == 'code_execution':
                                    code = parsed_input.get('code', '')
                                    if code:
                                        yield StreamChunk(type='content', content=f'💻 [Code] {code}\n')
                                    yield StreamChunk(type='content', content='✅ [Code Execution] Completed\n')
                                elif tool_name == 'web_search':
                                    query = parsed_input.get('query', '')
                                    if query:
                                        yield StreamChunk(type='content', content=f"🔍 [Query] '{query}'\n")
                                    yield StreamChunk(type='content', content='✅ [Web Search] Completed\n')
                                tool_data['processed'] = True
                                break
                elif chunk.type == 'message_delta':
                    pass
                elif chunk.type == 'message_stop':
                    user_tool_calls = []
                    for tool_use in current_tool_uses_local.values():
                        tool_name = tool_use.get('name', '')
                        is_server_side = tool_use.get('server_side', False)
                        if not is_server_side and tool_name not in ['web_search', 'code_execution']:
                            tool_input = tool_use.get('input', '')
                            try:
                                parsed_input = json.loads(tool_input) if tool_input else {}
                            except json.JSONDecodeError:
                                parsed_input = {'raw_input': tool_input}
                            user_tool_calls.append({'id': tool_use['id'], 'type': 'function', 'function': {'name': tool_name, 'arguments': parsed_input}})
                    if user_tool_calls:
                        log_stream_chunk('backend.claude', 'tool_calls', user_tool_calls, agent_id)
                        yield StreamChunk(type='tool_calls', tool_calls=user_tool_calls)
                    complete_message = {'role': 'assistant', 'content': content_local.strip()}
                    if user_tool_calls:
                        complete_message['tool_calls'] = user_tool_calls
                    log_stream_chunk('backend.claude', 'complete_message', complete_message, agent_id)
                    yield StreamChunk(type='complete_message', complete_message=complete_message)
                    if all_params.get('enable_web_search', False):
                        self.search_count += 1
                    if all_params.get('enable_code_execution', False):
                        self.code_session_hours += 0.083
                    log_stream_chunk('backend.claude', 'done', None, agent_id)
                    yield StreamChunk(type='done')
                    return
            except Exception as event_error:
                error_msg = f'Event processing error: {event_error}'
                log_stream_chunk('backend.claude', 'error', error_msg, agent_id)
                yield StreamChunk(type='error', error=error_msg)
                continue

    async def _handle_mcp_error_and_fallback(self, error: Exception, api_params: Dict[str, Any], provider_tools: List[Dict[str, Any]], stream_func: Callable[[Dict[str, Any]], AsyncGenerator[StreamChunk, None]]) -> AsyncGenerator[StreamChunk, None]:
        """Handle MCP errors with user-friendly messaging and fallback to non-MCP tools."""
        async with self._stats_lock:
            self._mcp_tool_failures += 1
            call_index_snapshot = self._mcp_tool_calls_count
        if MCPErrorHandler:
            log_type, user_message, _ = MCPErrorHandler.get_error_details(error)
        else:
            log_type, user_message = ('mcp_error', '[MCP] Error occurred')
        logger.warning(f'MCP tool call #{call_index_snapshot} failed - {log_type}: {error}')
        yield StreamChunk(type='content', content=f'\n⚠️  {user_message} ({error}); continuing without MCP tools\n')
        fallback_params = dict(api_params)
        if 'tools' in fallback_params and self._mcp_functions:
            mcp_names = set(self._mcp_functions.keys())
            non_mcp_tools = []
            for tool in fallback_params['tools']:
                name = tool.get('name')
                if name in mcp_names:
                    continue
                non_mcp_tools.append(tool)
            fallback_params['tools'] = non_mcp_tools
        if provider_tools:
            if 'tools' not in fallback_params:
                fallback_params['tools'] = []
            fallback_params['tools'].extend(provider_tools)
        async for chunk in stream_func(fallback_params):
            yield chunk

    async def _execute_mcp_function_with_retry(self, function_name: str, arguments_json: str, max_retries: int=3) -> List[str | Any]:
        """Execute MCP function with Claude-specific formatting."""
        result_str, result_obj = await super()._execute_mcp_function_with_retry(function_name, arguments_json, max_retries)
        if result_str.startswith('Error:'):
            return [result_str]
        return [result_str, result_obj]

    def create_tool_result_message(self, tool_call: Dict[str, Any], result_content: str) -> Dict[str, Any]:
        """Create tool result message in Claude's expected format."""
        tool_call_id = self.extract_tool_call_id(tool_call)
        return {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': tool_call_id, 'content': result_content}]}

    def extract_tool_result_content(self, tool_result_message: Dict[str, Any]) -> str:
        """Extract content from Claude tool result message."""
        content = tool_result_message.get('content', [])
        if isinstance(content, list) and content:
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'tool_result':
                    return item.get('content', '')
        return ''

    def reset_tool_usage(self):
        """Reset tool usage tracking."""
        self.search_count = 0
        self.code_session_hours = 0.0
        super().reset_token_usage()

    def _create_client(self, **kwargs):
        return anthropic.AsyncAnthropic(api_key=self.api_key)

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return 'Claude'

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by Claude."""
        return ['web_search', 'code_execution']

    def get_filesystem_support(self) -> FilesystemSupport:
        """Claude supports filesystem through MCP servers."""
        return FilesystemSupport.MCP

def _ensure_no_pending_upload_markers(self, messages: List[Dict[str, Any]]) -> None:
    """Raise UploadFileError if any file_pending_upload markers remain."""
    if not messages:
        return
    for msg_idx, message in enumerate(messages):
        content = message.get('content')
        if not isinstance(content, list):
            continue
        for item_idx, item in enumerate(content):
            if isinstance(item, dict) and item.get('type') == 'file_pending_upload':
                identifier = item.get('filename') or item.get('name') or item.get('path') or item.get('url') or 'unknown'
                raise UploadFileError(f'Claude Files API upload left unresolved file_pending_upload marker (message {msg_idx}, item {item_idx}, source {identifier}).')

class MassLogManager:
    """
    Comprehensive logging system for the MassGen framework.

    Records all significant events including:
    - Agent state changes (working, voted, failed)
    - Answer updates and notifications
    - Voting events and consensus decisions
    - Phase transitions (collaboration, debate, consensus)
    - System metrics and performance data

    New organized structure:
    logs/
    └── YYYYMMDD_HHMMSS/
        ├── display/
        │   ├── agent_0.txt, agent_1.txt, ...  # Real-time display logs
        │   └── system.txt                     # System messages
        ├── answers/
        │   ├── agent_0.txt, agent_1.txt, ...  # Agent answer histories
        ├── votes/
        │   ├── agent_0.txt, agent_1.txt, ...  # Agent voting records
        ├── events.jsonl                       # Structured event log
        └── console.log                        # Python logging output
    """

    def __init__(self, log_dir: str='logs', session_id: Optional[str]=None, non_blocking: bool=False):
        """
        Initialize the logging system.

        Args:
            log_dir: Directory to save log files
            session_id: Unique identifier for this session
            non_blocking: If True, disable file logging to prevent hanging issues
        """
        self.base_log_dir = Path(log_dir)
        self.session_id = session_id or self._generate_session_id()
        self.non_blocking = non_blocking
        if self.non_blocking:
            print('⚠️  LOGGING: Non-blocking mode enabled - file logging disabled')
        self.session_dir = self.base_log_dir / self.session_id
        if not self.non_blocking:
            try:
                self.session_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f'Warning: Failed to create session directory, enabling non-blocking mode: {e}')
                self.non_blocking = True
        self.display_dir = self.session_dir / 'display'
        self.answers_dir = self.session_dir / 'answers'
        self.votes_dir = self.session_dir / 'votes'
        if not self.non_blocking:
            try:
                self.display_dir.mkdir(exist_ok=True)
                self.answers_dir.mkdir(exist_ok=True)
                self.votes_dir.mkdir(exist_ok=True)
            except Exception as e:
                print(f'Warning: Failed to create subdirectories, enabling non-blocking mode: {e}')
                self.non_blocking = True
        self.events_log_file = self.session_dir / 'events.jsonl'
        self.console_log_file = self.session_dir / 'console.log'
        self.system_log_file = self.display_dir / 'system.txt'
        self.log_entries: List[LogEntry] = []
        self.agent_logs: Dict[int, List[LogEntry]] = {}
        self.event_counters = {'answer_updates': 0, 'votes_cast': 0, 'consensus_reached': 0, 'debates_started': 0, 'agent_restarts': 0, 'notifications_sent': 0}
        self._lock = threading.Lock()
        self._setup_logging()
        if not self.non_blocking:
            self._initialize_system_log()
        self.log_event('session_started', data={'session_id': self.session_id, 'timestamp': time.time(), 'session_dir': str(self.session_dir), 'non_blocking_mode': self.non_blocking})

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f'{timestamp}'

    def _initialize_system_log(self):
        """Initialize the system log file with header."""
        if self.non_blocking:
            return
        try:
            with open(self.system_log_file, 'w', encoding='utf-8') as f:
                f.write('MassGen System Messages Log\n')
                f.write(f'Session ID: {self.session_id}\n')
                f.write(f'Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 80 + '\n\n')
        except Exception as e:
            print(f'Warning: Failed to initialize system log: {e}')

    def _setup_logging(self):
        """Set up file logging configuration."""
        if self.non_blocking:
            return
        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        try:
            self.session_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f'Warning: Failed to create session directory {self.session_dir}, skipping file logging: {e}')
            return
        console_log_handler = logging.FileHandler(self.console_log_file)
        console_log_handler.setFormatter(log_formatter)
        console_log_handler.setLevel(logging.DEBUG)
        mass_logger = logging.getLogger('massgen')
        mass_logger.addHandler(console_log_handler)
        mass_logger.setLevel(logging.DEBUG)
        mass_logger.propagate = False
        if not any((isinstance(h, logging.StreamHandler) for h in mass_logger.handlers)):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(logging.INFO)
            mass_logger.addHandler(console_handler)

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp to human-readable format."""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def _format_answer_record(self, record: AnswerRecord, agent_id: int) -> str:
        """Format an AnswerRecord into human-readable text."""
        timestamp_str = self._format_timestamp(record.timestamp)
        status_emoji = {'working': '🔄', 'voted': '✅', 'failed': '❌', 'unknown': '❓'}
        emoji = status_emoji.get(record.status, '��')
        return f'\n{emoji} UPDATE DETAILS\n🕒 Time: {timestamp_str}\n📊 Status: {record.status.upper()}\n📏 Length: {len(record.answer)} characters\n\n📄 Content:\n{record.answer}\n\n{'=' * 80}\n'

    def _format_vote_record(self, record: VoteRecord, agent_id: int) -> str:
        """Format a VoteRecord into human-readable text."""
        timestamp_str = self._format_timestamp(record.timestamp)
        reason_text = record.reason if record.reason else 'No reason provided'
        return f'\n🗳️ VOTE CAST\n🕒 Time: {timestamp_str}\n👤 Voter: Agent {record.voter_id}\n🎯 Target: Agent {record.target_id}\n\n📝 Reasoning:\n{reason_text}\n\n{'=' * 80}\n'

    def _write_agent_answers(self, agent_id: int, answer_records: List[AnswerRecord]):
        """Write agent's answer history to the answers folder."""
        if self.non_blocking:
            return
        try:
            answers_file = self.answers_dir / f'agent_{agent_id}.txt'
            with open(answers_file, 'w', encoding='utf-8') as f:
                f.write('=' * 80 + '\n')
                f.write(f'📝 MASSGEN AGENT {agent_id} - ANSWER HISTORY\n')
                f.write('=' * 80 + '\n')
                f.write(f'🆔 Session: {self.session_id}\n')
                f.write(f'📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                if answer_records:
                    total_chars = sum((len(record.answer) for record in answer_records))
                    avg_chars = total_chars / len(answer_records) if answer_records else 0
                    first_update = answer_records[0].timestamp if answer_records else 0
                    last_update = answer_records[-1].timestamp if answer_records else 0
                    duration = last_update - first_update if len(answer_records) > 1 else 0
                    f.write(f'📊 Total Updates: {len(answer_records)}\n')
                    f.write(f'📏 Total Characters: {total_chars:,}\n')
                    f.write(f'📈 Average Length: {avg_chars:.0f} chars\n')
                    if duration > 0:
                        duration_str = f'{duration / 60:.1f} minutes' if duration > 60 else f'{duration:.1f} seconds'
                        f.write(f'⏱️ Time Span: {duration_str}\n')
                else:
                    f.write('❌ No answer records found for this agent.\n')
                f.write('=' * 80 + '\n\n')
                if answer_records:
                    for i, record in enumerate(answer_records, 1):
                        elapsed = record.timestamp - (answer_records[0].timestamp if answer_records else record.timestamp)
                        elapsed_str = f'[+{elapsed / 60:.1f}m]' if elapsed > 60 else f'[+{elapsed:.1f}s]'
                        f.write(f'🔢 UPDATE #{i} {elapsed_str}\n')
                        f.write(self._format_answer_record(record, agent_id))
                        f.write('\n')
        except Exception as e:
            print(f'Warning: Failed to write answers for agent {agent_id}: {e}')

    def _write_agent_votes(self, agent_id: int, vote_records: List[VoteRecord]):
        """Write agent's vote history to the votes folder."""
        if self.non_blocking:
            return
        try:
            votes_file = self.votes_dir / f'agent_{agent_id}.txt'
            with open(votes_file, 'w', encoding='utf-8') as f:
                f.write('=' * 80 + '\n')
                f.write(f'🗳️ MASSGEN AGENT {agent_id} - VOTE HISTORY\n')
                f.write('=' * 80 + '\n')
                f.write(f'🆔 Session: {self.session_id}\n')
                f.write(f'📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                if vote_records:
                    vote_targets = {}
                    total_reason_chars = 0
                    for vote in vote_records:
                        vote_targets[vote.target_id] = vote_targets.get(vote.target_id, 0) + 1
                        total_reason_chars += len(vote.reason) if vote.reason else 0
                    most_voted_target = max(vote_targets.items(), key=lambda x: x[1]) if vote_targets else None
                    avg_reason_length = total_reason_chars / len(vote_records) if vote_records else 0
                    first_vote = vote_records[0].timestamp if vote_records else 0
                    last_vote = vote_records[-1].timestamp if vote_records else 0
                    voting_duration = last_vote - first_vote if len(vote_records) > 1 else 0
                    f.write(f'📊 Total Votes Cast: {len(vote_records)}\n')
                    f.write(f'🎯 Unique Targets: {len(vote_targets)}\n')
                    if most_voted_target:
                        f.write(f'👑 Most Voted For: Agent {most_voted_target[0]} ({most_voted_target[1]} votes)\n')
                    f.write(f'📝 Avg Reason Length: {avg_reason_length:.0f} chars\n')
                    if voting_duration > 0:
                        duration_str = f'{voting_duration / 60:.1f} minutes' if voting_duration > 60 else f'{voting_duration:.1f} seconds'
                        f.write(f'⏱️ Voting Duration: {duration_str}\n')
                else:
                    f.write('❌ No vote records found for this agent.\n')
                f.write('=' * 80 + '\n\n')
                if vote_records:
                    for i, record in enumerate(vote_records, 1):
                        elapsed = record.timestamp - (vote_records[0].timestamp if vote_records else record.timestamp)
                        elapsed_str = f'[+{elapsed / 60:.1f}m]' if elapsed > 60 else f'[+{elapsed:.1f}s]'
                        f.write(f'🗳️ VOTE #{i} {elapsed_str}\n')
                        f.write(self._format_vote_record(record, agent_id))
                        f.write('\n')
        except Exception as e:
            print(f'Warning: Failed to write votes for agent {agent_id}: {e}')

    def log_event(self, event_type: str, agent_id: Optional[int]=None, phase: str='unknown', data: Optional[Dict[str, Any]]=None):
        """
        Log a general system event.

        Args:
            event_type: Type of event (e.g., "session_started", "phase_change")
            agent_id: Agent ID if event is agent-specific
            phase: Current system phase
            data: Additional event data
        """
        with self._lock:
            entry = LogEntry(timestamp=time.time(), event_type=event_type, agent_id=agent_id, phase=phase, data=data or {}, session_id=self.session_id)
            self.log_entries.append(entry)
            if agent_id is not None:
                if agent_id not in self.agent_logs:
                    self.agent_logs[agent_id] = []
                self.agent_logs[agent_id].append(entry)
            self._write_log_entry(entry)

    def log_agent_answer_update(self, agent_id: int, answer: str, phase: str='unknown', orchestrator=None):
        """
        Log agent answer update with detailed information and immediately save to file.

        Args:
            agent_id: Agent ID
            answer: Updated answer content
            phase: Current workflow phase
            orchestrator: MassOrchestrator instance to get agent state data
        """
        data = {'answer': answer, 'answer_length': len(answer)}
        self.log_event('agent_answer_update', agent_id, phase, data)
        if orchestrator and agent_id in orchestrator.agent_states:
            agent_state = orchestrator.agent_states[agent_id]
            self._write_agent_answers(agent_id, agent_state.updated_answers)

    def log_agent_status_change(self, agent_id: int, old_status: str, new_status: str, phase: str='unknown'):
        """
        Log agent status change.

        Args:
            agent_id: Agent ID
            old_status: Previous status
            new_status: New status
            phase: Current workflow phase
        """
        data = {'old_status': old_status, 'new_status': new_status, 'status_change': f'{old_status} {new_status}'}
        self.log_event('agent_status_change', agent_id, phase, data)

    def log_system_state_snapshot(self, orchestrator, phase: str='unknown'):
        """
        Log a complete system state snapshot including all agent answers and voting status.

        Args:
            orchestrator: The MassOrchestrator instance
            phase: Current workflow phase
        """
        agent_states = {}
        all_agent_answers = {}
        vote_records = []
        for agent_id, agent_state in orchestrator.agent_states.items():
            agent_states[agent_id] = {'status': agent_state.status, 'curr_answer': agent_state.curr_answer, 'vote_target': agent_state.curr_vote.target_id if agent_state.curr_vote else None, 'execution_time': agent_state.execution_time, 'update_count': len(agent_state.updated_answers), 'seen_updates_timestamps': agent_state.seen_updates_timestamps}
            all_agent_answers[agent_id] = {'current_answer': agent_state.curr_answer, 'answer_history': [{'timestamp': update.timestamp, 'answer': update.answer, 'status': update.status} for update in agent_state.updated_answers]}
        for vote in orchestrator.votes:
            vote_records.append({'voter_id': vote.voter_id, 'target_id': vote.target_id, 'timestamp': vote.timestamp})
        vote_counts = Counter((vote.target_id for vote in orchestrator.votes))
        voting_status = {'vote_distribution': dict(vote_counts), 'total_votes_cast': len(orchestrator.votes), 'total_agents': len(orchestrator.agents), 'consensus_reached': orchestrator.system_state.consensus_reached, 'winning_agent_id': orchestrator.system_state.representative_agent_id, 'votes_needed_for_consensus': max(1, int(len(orchestrator.agents) * orchestrator.consensus_threshold))}
        system_snapshot = {'agent_states': agent_states, 'agent_answers': all_agent_answers, 'voting_records': vote_records, 'voting_status': voting_status, 'system_phase': phase, 'system_runtime': time.time() - orchestrator.system_state.start_time if orchestrator.system_state.start_time else 0}
        self.log_event('system_state_snapshot', phase=phase, data=system_snapshot)
        system_state_entry = {'timestamp': time.time(), 'event': 'system_state_snapshot', 'phase': phase, 'system_state': system_snapshot}
        for agent_id, agent_state in orchestrator.agent_states.items():
            self._write_agent_answers(agent_id, agent_state.updated_answers)
            self._write_agent_votes(agent_id, agent_state.cast_votes)
        for agent_id in orchestrator.agents.keys():
            self._write_agent_display_log(agent_id, system_state_entry)
        return system_snapshot

    def log_voting_event(self, voter_id: int, target_id: int, phase: str='unknown', reason: str='', orchestrator=None):
        """
        Log a voting event with detailed information and immediately save to file.

        Args:
            voter_id: ID of the agent casting the vote
            target_id: ID of the agent being voted for
            phase: Current workflow phase
            reason: Reason for the vote
            orchestrator: MassOrchestrator instance to get agent state data
        """
        with self._lock:
            self.event_counters['votes_cast'] += 1
        data = {'voter_id': voter_id, 'target_id': target_id, 'reason': reason, 'total_votes_cast': self.event_counters['votes_cast']}
        self.log_event('voting_event', voter_id, phase, data)
        if orchestrator and voter_id in orchestrator.agent_states:
            agent_state = orchestrator.agent_states[voter_id]
            self._write_agent_votes(voter_id, agent_state.cast_votes)

    def log_consensus_reached(self, winning_agent_id: int, vote_distribution: Dict[int, int], is_fallback: bool=False, phase: str='unknown'):
        """
        Log when consensus is reached.

        Args:
            winning_agent_id: ID of the winning agent
            vote_distribution: Dictionary of agent_id -> vote_count
            is_fallback: Whether this was a fallback consensus (timeout)
            phase: Current workflow phase
        """
        with self._lock:
            self.event_counters['consensus_reached'] += 1
        data = {'winning_agent_id': winning_agent_id, 'vote_distribution': vote_distribution, 'is_fallback': is_fallback, 'total_consensus_events': self.event_counters['consensus_reached']}
        self.log_event('consensus_reached', winning_agent_id, phase, data)
        consensus_entry = {'timestamp': time.time(), 'event': 'consensus_reached', 'phase': phase, 'winning_agent_id': winning_agent_id, 'vote_distribution': vote_distribution, 'is_fallback': is_fallback}
        for agent_id in vote_distribution.keys():
            self._write_agent_display_log(agent_id, consensus_entry)

    def log_phase_transition(self, old_phase: str, new_phase: str, additional_data: Dict[str, Any]=None):
        """
        Log system phase transitions.

        Args:
            old_phase: Previous phase
            new_phase: New phase
            additional_data: Additional context data
        """
        data = {'old_phase': old_phase, 'new_phase': new_phase, 'phase_transition': f'{old_phase} -> {new_phase}', **(additional_data or {})}
        self.log_event('phase_transition', phase=new_phase, data=data)

    def log_notification_sent(self, agent_id: int, notification_type: str, content_preview: str, phase: str='unknown'):
        """
        Log when a notification is sent to an agent.

        Args:
            agent_id: Target agent ID
            notification_type: Type of notification (update, debate, presentation, prompt)
            content_preview: Preview of notification content
            phase: Current workflow phase
        """
        with self._lock:
            self.event_counters['notifications_sent'] += 1
        data = {'notification_type': notification_type, 'content_preview': content_preview[:200] + '...' if len(content_preview) > 200 else content_preview, 'content_length': len(content_preview), 'total_notifications_sent': self.event_counters['notifications_sent']}
        self.log_event('notification_sent', agent_id, phase, data)
        notification_entry = {'timestamp': time.time(), 'event': 'notification_received', 'phase': phase, 'notification_type': notification_type, 'content': content_preview}
        self._write_agent_display_log(agent_id, notification_entry)

    def log_agent_restart(self, agent_id: int, reason: str, phase: str='unknown'):
        """
        Log when an agent is restarted.

        Args:
            agent_id: ID of the restarted agent
            reason: Reason for restart
            phase: Current workflow phase
        """
        with self._lock:
            self.event_counters['agent_restarts'] += 1
        data = {'restart_reason': reason, 'total_restarts': self.event_counters['agent_restarts']}
        self.log_event('agent_restart', agent_id, phase, data)
        restart_entry = {'timestamp': time.time(), 'event': 'agent_restarted', 'phase': phase, 'reason': reason}
        self._write_agent_display_log(agent_id, restart_entry)

    def log_debate_started(self, phase: str='unknown'):
        """
        Log when a debate phase starts.

        Args:
            phase: Current workflow phase
        """
        with self._lock:
            self.event_counters['debates_started'] += 1
        data = {'total_debates': self.event_counters['debates_started']}
        self.log_event('debate_started', phase=phase, data=data)

    def log_task_completion(self, final_solution: Dict[str, Any]):
        """
        Log task completion with final results.

        Args:
            final_solution: Complete final solution data
        """
        data = {'final_solution': final_solution, 'completion_timestamp': time.time()}
        self.log_event('task_completed', phase='completed', data=data)

    def _write_log_entry(self, entry: LogEntry):
        """Write a single log entry to the session JSONL file."""
        if self.non_blocking:
            return
        try:
            self.events_log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.events_log_file, 'a', buffering=1) as f:
                json_line = json.dumps(entry.to_dict(), default=str, ensure_ascii=False)
                f.write(json_line + '\n')
                f.flush()
        except Exception as e:
            print(f'Warning: Failed to write log entry: {e}')

    def _write_agent_display_log(self, agent_id: int, data: Dict[str, Any]):
        """Write agent-specific display log entry."""
        if self.non_blocking:
            return
        try:
            agent_log_file = self.display_dir / f'agent_{agent_id}.txt'
            agent_log_file.parent.mkdir(parents=True, exist_ok=True)
            if not agent_log_file.exists():
                with open(agent_log_file, 'w', encoding='utf-8') as f:
                    f.write(f'MassGen Agent {agent_id} Display Log\n')
                    f.write(f'Session: {self.session_id}\n')
                    f.write(f'Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                    f.write('=' * 80 + '\n\n')
            with open(agent_log_file, 'a', encoding='utf-8') as f:
                timestamp_str = self._format_timestamp(data.get('timestamp', time.time()))
                f.write(f'[{timestamp_str}] {data.get('event', 'unknown_event')}\n')
                for key, value in data.items():
                    if key not in ['timestamp', 'event']:
                        f.write(f'  {key}: {value}\n')
                f.write('\n')
                f.flush()
        except Exception as e:
            print(f'Warning: Failed to write agent display log: {e}')

    def _write_system_log(self, message: str):
        """Write a system message to the system log file."""
        if self.non_blocking:
            return
        try:
            with open(self.system_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%H:%M:%S')
                f.write(f'[{timestamp}] {message}\n')
                f.flush()
        except Exception as e:
            print(f'Error writing to system log: {e}')

    def get_agent_history(self, agent_id: int) -> List[LogEntry]:
        """Get complete history for a specific agent."""
        with self._lock:
            return self.agent_logs.get(agent_id, []).copy()

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        with self._lock:
            event_counts = {}
            agent_activities = {}
            for entry in self.log_entries:
                event_counts[entry.event_type] = event_counts.get(entry.event_type, 0) + 1
                if entry.agent_id is not None:
                    agent_id = entry.agent_id
                    if agent_id not in agent_activities:
                        agent_activities[agent_id] = []
                    agent_activities[agent_id].append({'timestamp': entry.timestamp, 'event_type': entry.event_type, 'phase': entry.phase})
            return {'session_id': self.session_id, 'total_events': len(self.log_entries), 'event_counts': event_counts, 'agents_involved': list(agent_activities.keys()), 'agent_activities': agent_activities, 'session_duration': self._calculate_session_duration(), 'log_files': {'session_dir': str(self.session_dir), 'events_log': str(self.events_log_file), 'console_log': str(self.console_log_file), 'display_dir': str(self.display_dir), 'answers_dir': str(self.answers_dir), 'votes_dir': str(self.votes_dir)}}

    def _calculate_session_duration(self) -> float:
        """Calculate total session duration."""
        if not self.log_entries:
            return 0.0
        start_time = min((entry.timestamp for entry in self.log_entries))
        end_time = max((entry.timestamp for entry in self.log_entries))
        return end_time - start_time

    def save_agent_states(self, orchestrator):
        """Save current agent states to answers and votes folders."""
        if self.non_blocking:
            return
        try:
            for agent_id, agent_state in orchestrator.agent_states.items():
                self._write_agent_answers(agent_id, agent_state.updated_answers)
                self._write_agent_votes(agent_id, agent_state.cast_votes)
        except Exception as e:
            print(f'Warning: Failed to save agent states: {e}')

    def cleanup(self):
        """Clean up and finalize the logging session."""
        self.log_event('session_ended', data={'end_timestamp': time.time(), 'total_events_logged': len(self.log_entries)})

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.

        Returns:
            Dictionary containing session metrics and statistics
        """
        with self._lock:
            total_events = len(self.log_entries)
            agent_event_counts = {}
            for agent_id, logs in self.agent_logs.items():
                agent_event_counts[agent_id] = len(logs)
            return {'session_id': self.session_id, 'total_events': total_events, 'event_counters': self.event_counters.copy(), 'agent_event_counts': agent_event_counts, 'total_agents': len(self.agent_logs), 'session_duration': time.time() - (self.log_entries[0].timestamp if self.log_entries else time.time())}

def _generate_session_id(self) -> str:
    """Generate a unique session ID."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{timestamp}'

def _initialize_system_log(self):
    """Initialize the system log file with header."""
    if self.non_blocking:
        return
    try:
        with open(self.system_log_file, 'w', encoding='utf-8') as f:
            f.write('MassGen System Messages Log\n')
            f.write(f'Session ID: {self.session_id}\n')
            f.write(f'Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
            f.write('=' * 80 + '\n\n')
    except Exception as e:
        print(f'Warning: Failed to initialize system log: {e}')

def _format_timestamp(self, timestamp: float) -> str:
    """Format timestamp to human-readable format."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def _format_answer_record(self, record: AnswerRecord, agent_id: int) -> str:
    """Format an AnswerRecord into human-readable text."""
    timestamp_str = self._format_timestamp(record.timestamp)
    status_emoji = {'working': '🔄', 'voted': '✅', 'failed': '❌', 'unknown': '❓'}
    emoji = status_emoji.get(record.status, '��')
    return f'\n{emoji} UPDATE DETAILS\n🕒 Time: {timestamp_str}\n📊 Status: {record.status.upper()}\n📏 Length: {len(record.answer)} characters\n\n📄 Content:\n{record.answer}\n\n{'=' * 80}\n'

def _format_vote_record(self, record: VoteRecord, agent_id: int) -> str:
    """Format a VoteRecord into human-readable text."""
    timestamp_str = self._format_timestamp(record.timestamp)
    reason_text = record.reason if record.reason else 'No reason provided'
    return f'\n🗳️ VOTE CAST\n🕒 Time: {timestamp_str}\n👤 Voter: Agent {record.voter_id}\n🎯 Target: Agent {record.target_id}\n\n📝 Reasoning:\n{reason_text}\n\n{'=' * 80}\n'

def _write_agent_answers(self, agent_id: int, answer_records: List[AnswerRecord]):
    """Write agent's answer history to the answers folder."""
    if self.non_blocking:
        return
    try:
        answers_file = self.answers_dir / f'agent_{agent_id}.txt'
        with open(answers_file, 'w', encoding='utf-8') as f:
            f.write('=' * 80 + '\n')
            f.write(f'📝 MASSGEN AGENT {agent_id} - ANSWER HISTORY\n')
            f.write('=' * 80 + '\n')
            f.write(f'🆔 Session: {self.session_id}\n')
            f.write(f'📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
            if answer_records:
                total_chars = sum((len(record.answer) for record in answer_records))
                avg_chars = total_chars / len(answer_records) if answer_records else 0
                first_update = answer_records[0].timestamp if answer_records else 0
                last_update = answer_records[-1].timestamp if answer_records else 0
                duration = last_update - first_update if len(answer_records) > 1 else 0
                f.write(f'📊 Total Updates: {len(answer_records)}\n')
                f.write(f'📏 Total Characters: {total_chars:,}\n')
                f.write(f'📈 Average Length: {avg_chars:.0f} chars\n')
                if duration > 0:
                    duration_str = f'{duration / 60:.1f} minutes' if duration > 60 else f'{duration:.1f} seconds'
                    f.write(f'⏱️ Time Span: {duration_str}\n')
            else:
                f.write('❌ No answer records found for this agent.\n')
            f.write('=' * 80 + '\n\n')
            if answer_records:
                for i, record in enumerate(answer_records, 1):
                    elapsed = record.timestamp - (answer_records[0].timestamp if answer_records else record.timestamp)
                    elapsed_str = f'[+{elapsed / 60:.1f}m]' if elapsed > 60 else f'[+{elapsed:.1f}s]'
                    f.write(f'🔢 UPDATE #{i} {elapsed_str}\n')
                    f.write(self._format_answer_record(record, agent_id))
                    f.write('\n')
    except Exception as e:
        print(f'Warning: Failed to write answers for agent {agent_id}: {e}')

def _write_agent_votes(self, agent_id: int, vote_records: List[VoteRecord]):
    """Write agent's vote history to the votes folder."""
    if self.non_blocking:
        return
    try:
        votes_file = self.votes_dir / f'agent_{agent_id}.txt'
        with open(votes_file, 'w', encoding='utf-8') as f:
            f.write('=' * 80 + '\n')
            f.write(f'🗳️ MASSGEN AGENT {agent_id} - VOTE HISTORY\n')
            f.write('=' * 80 + '\n')
            f.write(f'🆔 Session: {self.session_id}\n')
            f.write(f'📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
            if vote_records:
                vote_targets = {}
                total_reason_chars = 0
                for vote in vote_records:
                    vote_targets[vote.target_id] = vote_targets.get(vote.target_id, 0) + 1
                    total_reason_chars += len(vote.reason) if vote.reason else 0
                most_voted_target = max(vote_targets.items(), key=lambda x: x[1]) if vote_targets else None
                avg_reason_length = total_reason_chars / len(vote_records) if vote_records else 0
                first_vote = vote_records[0].timestamp if vote_records else 0
                last_vote = vote_records[-1].timestamp if vote_records else 0
                voting_duration = last_vote - first_vote if len(vote_records) > 1 else 0
                f.write(f'📊 Total Votes Cast: {len(vote_records)}\n')
                f.write(f'🎯 Unique Targets: {len(vote_targets)}\n')
                if most_voted_target:
                    f.write(f'👑 Most Voted For: Agent {most_voted_target[0]} ({most_voted_target[1]} votes)\n')
                f.write(f'📝 Avg Reason Length: {avg_reason_length:.0f} chars\n')
                if voting_duration > 0:
                    duration_str = f'{voting_duration / 60:.1f} minutes' if voting_duration > 60 else f'{voting_duration:.1f} seconds'
                    f.write(f'⏱️ Voting Duration: {duration_str}\n')
            else:
                f.write('❌ No vote records found for this agent.\n')
            f.write('=' * 80 + '\n\n')
            if vote_records:
                for i, record in enumerate(vote_records, 1):
                    elapsed = record.timestamp - (vote_records[0].timestamp if vote_records else record.timestamp)
                    elapsed_str = f'[+{elapsed / 60:.1f}m]' if elapsed > 60 else f'[+{elapsed:.1f}s]'
                    f.write(f'🗳️ VOTE #{i} {elapsed_str}\n')
                    f.write(self._format_vote_record(record, agent_id))
                    f.write('\n')
    except Exception as e:
        print(f'Warning: Failed to write votes for agent {agent_id}: {e}')

def _write_log_entry(self, entry: LogEntry):
    """Write a single log entry to the session JSONL file."""
    if self.non_blocking:
        return
    try:
        self.events_log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.events_log_file, 'a', buffering=1) as f:
            json_line = json.dumps(entry.to_dict(), default=str, ensure_ascii=False)
            f.write(json_line + '\n')
            f.flush()
    except Exception as e:
        print(f'Warning: Failed to write log entry: {e}')

def _write_agent_display_log(self, agent_id: int, data: Dict[str, Any]):
    """Write agent-specific display log entry."""
    if self.non_blocking:
        return
    try:
        agent_log_file = self.display_dir / f'agent_{agent_id}.txt'
        agent_log_file.parent.mkdir(parents=True, exist_ok=True)
        if not agent_log_file.exists():
            with open(agent_log_file, 'w', encoding='utf-8') as f:
                f.write(f'MassGen Agent {agent_id} Display Log\n')
                f.write(f'Session: {self.session_id}\n')
                f.write(f'Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 80 + '\n\n')
        with open(agent_log_file, 'a', encoding='utf-8') as f:
            timestamp_str = self._format_timestamp(data.get('timestamp', time.time()))
            f.write(f'[{timestamp_str}] {data.get('event', 'unknown_event')}\n')
            for key, value in data.items():
                if key not in ['timestamp', 'event']:
                    f.write(f'  {key}: {value}\n')
            f.write('\n')
            f.flush()
    except Exception as e:
        print(f'Warning: Failed to write agent display log: {e}')

def _write_system_log(self, message: str):
    """Write a system message to the system log file."""
    if self.non_blocking:
        return
    try:
        with open(self.system_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%H:%M:%S')
            f.write(f'[{timestamp}] {message}\n')
            f.flush()
    except Exception as e:
        print(f'Error writing to system log: {e}')

class MultiRegionDisplay:

    def __init__(self, display_enabled: bool=True, max_lines: int=10, save_logs: bool=True, answers_dir: Optional[str]=None):
        self.display_enabled = display_enabled
        self.max_lines = max_lines
        self.save_logs = save_logs
        self.answers_dir = answers_dir
        self.agent_outputs: Dict[int, str] = {}
        self.agent_models: Dict[int, str] = {}
        self.agent_statuses: Dict[int, str] = {}
        self.system_messages: List[str] = []
        self.start_time = time.time()
        self._lock = threading.RLock()
        self.current_phase = 'collaboration'
        self.vote_distribution: Dict[int, int] = {}
        self.consensus_reached = False
        self.representative_agent_id: Optional[int] = None
        self.debate_rounds: int = 0
        self._agent_vote_targets: Dict[int, Optional[int]] = {}
        self._agent_chat_rounds: Dict[int, int] = {}
        self._agent_update_counts: Dict[int, int] = {}
        self._agent_votes_cast: Dict[int, int] = {}
        self._display_cache = None
        self._last_agent_count = 0
        self._update_timer = None
        self._update_delay = 0.1
        self._display_updating = False
        self._pending_update = False
        self._ansi_pattern = re.compile('\\x1B(?:[@-Z\\\\-_]|\\[[0-?]*[ -/]*[@-~]|\\][^\\x07]*(?:\\x07|\\x1B\\\\)|[PX^_][^\\x1B]*\\x1B\\\\)')
        if self.save_logs:
            self._setup_logging()

    def _get_terminal_width(self):
        """Get terminal width with conservative fallback."""
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 120

    def _calculate_layout(self, num_agents: int):
        """
        Calculate all layout dimensions in one place for consistency.
        Returns: (col_width, total_width, terminal_width)
        """
        if self._display_cache is None or self._last_agent_count != num_agents:
            terminal_width = self._get_terminal_width()
            border_chars = num_agents + 1
            safety_margin = 10
            available_width = terminal_width - border_chars - safety_margin
            col_width = max(25, available_width // num_agents)
            total_width = col_width * num_agents + border_chars
            if total_width > terminal_width - 2:
                col_width = max(20, (terminal_width - border_chars - 4) // num_agents)
                total_width = col_width * num_agents + border_chars
            self._display_cache = {'col_width': col_width, 'total_width': total_width, 'terminal_width': terminal_width, 'num_agents': num_agents, 'border_chars': border_chars}
            self._last_agent_count = num_agents
        cache = self._display_cache
        return (cache['col_width'], cache['total_width'], cache['terminal_width'])

    def _get_display_width(self, text: str) -> int:
        """
        ROBUST: Calculate the actual display width of text with proper ANSI and Unicode handling.
        """
        if not text:
            return 0
        clean_text = self._ansi_pattern.sub('', text)
        width = 0
        i = 0
        while i < len(clean_text):
            char = clean_text[i]
            char_code = ord(char)
            if char_code < 32 or char_code == 127:
                i += 1
                continue
            if unicodedata.combining(char):
                i += 1
                continue
            char_width = self._get_char_width(char)
            width += char_width
            i += 1
        return width

    def _get_char_width(self, char: str) -> int:
        """
        ROBUST: Get the display width of a single character.
        """
        char_code = ord(char)
        if 32 <= char_code <= 126:
            return 1
        if 128512 <= char_code <= 128591 or 127744 <= char_code <= 128511 or 128640 <= char_code <= 128767 or (128768 <= char_code <= 128895) or (128896 <= char_code <= 129023) or (129024 <= char_code <= 129279) or (129280 <= char_code <= 129535) or (129536 <= char_code <= 129647) or (129648 <= char_code <= 129791) or (127462 <= char_code <= 127487) or (9728 <= char_code <= 9983) or (9984 <= char_code <= 10175) or (127136 <= char_code <= 127231) or (127232 <= char_code <= 127487):
            return 2
        east_asian_width = unicodedata.east_asian_width(char)
        if east_asian_width in ('F', 'W'):
            return 2
        elif east_asian_width in ('N', 'Na', 'H'):
            return 1
        elif east_asian_width == 'A':
            return 1
        return 1

    def _preserve_ansi_truncate(self, text: str, max_width: int) -> str:
        """
        ROBUST: Truncate text while preserving ANSI color codes and handling wide characters.
        """
        if max_width <= 0:
            return ''
        if max_width <= 1:
            return '…'
        segments = self._ansi_pattern.split(text)
        ansi_codes = self._ansi_pattern.findall(text)
        result = ''
        current_width = 0
        ansi_index = 0
        for i, segment in enumerate(segments):
            if i > 0 and ansi_index < len(ansi_codes):
                result += ansi_codes[ansi_index]
                ansi_index += 1
            for char in segment:
                char_width = self._get_char_width(char)
                if current_width + char_width > max_width - 1:
                    if current_width < max_width:
                        result += '…'
                    return result
                result += char
                current_width += char_width
        return result

    def _pad_to_width(self, text: str, target_width: int, align: str='left') -> str:
        """
        ROBUST: Pad text to exact target width with proper ANSI and Unicode handling.
        """
        if target_width <= 0:
            return ''
        current_width = self._get_display_width(text)
        if current_width > target_width:
            text = self._preserve_ansi_truncate(text, target_width)
            current_width = self._get_display_width(text)
        padding = target_width - current_width
        if padding <= 0:
            return text
        if align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + text + ' ' * right_pad
        elif align == 'right':
            return ' ' * padding + text
        else:
            return text + ' ' * padding

    def _create_bordered_line(self, content_parts: List[str], total_width: int) -> str:
        """
        ROBUST: Create a single bordered line with guaranteed correct width.
        """
        validated_parts = []
        for part in content_parts:
            if self._get_display_width(part) != self._display_cache['col_width']:
                part = self._pad_to_width(part, self._display_cache['col_width'], 'left')
            validated_parts.append(part)
        line = '│' + '│'.join(validated_parts) + '│'
        actual_width = self._get_display_width(line)
        expected_width = total_width
        if actual_width != expected_width:
            if actual_width > expected_width:
                clean_line = self._ansi_pattern.sub('', line)
                if len(clean_line) > expected_width:
                    clean_line = clean_line[:expected_width - 1] + '│'
                line = clean_line
            else:
                line += ' ' * (expected_width - actual_width)
        return line

    def _create_system_bordered_line(self, content: str, total_width: int) -> str:
        """
        ROBUST: Create a system section line with borders.
        """
        content_width = total_width - 2
        if content_width <= 0:
            return '│' + ' ' * max(0, total_width - 2) + '│'
        padded_content = self._pad_to_width(content, content_width, 'left')
        line = f'│{padded_content}│'
        actual_width = self._get_display_width(line)
        if actual_width != total_width:
            if actual_width < total_width:
                line += ' ' * (total_width - actual_width)
            elif actual_width > total_width:
                clean_line = self._ansi_pattern.sub('', line)
                if len(clean_line) > total_width:
                    clean_line = clean_line[:total_width - 1] + '│'
                line = clean_line
        return line

    def _invalidate_display_cache(self):
        """Reset display cache when terminal is resized."""
        self._display_cache = None

    def cleanup(self):
        """Clean up resources when display is no longer needed."""
        with self._lock:
            if self._update_timer:
                self._update_timer.cancel()
                self._update_timer = None
            self._pending_update = False
            self._display_updating = False

    def _clear_terminal_atomic(self):
        """Atomically clear terminal using proper ANSI sequences."""
        try:
            sys.stdout.write('\x1b[2J')
            sys.stdout.write('\x1b[H')
            sys.stdout.flush()
        except Exception:
            try:
                os.system('clear' if os.name == 'posix' else 'cls')
            except Exception:
                pass

    def _schedule_display_update(self):
        """Schedule a debounced display update to prevent rapid refreshes."""
        with self._lock:
            if self._update_timer:
                self._update_timer.cancel()
            self._pending_update = True
            self._update_timer = threading.Timer(self._update_delay, self._execute_display_update)
            self._update_timer.start()

    def _execute_display_update(self):
        """Execute the actual display update."""
        with self._lock:
            if not self._pending_update:
                return
            if self._display_updating:
                self._update_timer = threading.Timer(self._update_delay, self._execute_display_update)
                self._update_timer.start()
                return
            self._display_updating = True
            self._pending_update = False
        try:
            self._update_display_immediate()
        finally:
            with self._lock:
                self._display_updating = False

    def set_agent_model(self, agent_id: int, model_name: str):
        """Set the model name for a specific agent."""
        with self._lock:
            self.agent_models[agent_id] = model_name
            if agent_id not in self.agent_outputs:
                self.agent_outputs[agent_id] = ''

    def update_agent_status(self, agent_id: int, status: str):
        """Update agent status (working, voted, failed)."""
        with self._lock:
            old_status = self.agent_statuses.get(agent_id, 'unknown')
            self.agent_statuses[agent_id] = status
            if agent_id not in self.agent_outputs:
                self.agent_outputs[agent_id] = ''
            status_change_emoji = {'working': '🔄', 'voted': '✅', 'failed': '❌', 'unknown': '❓'}
            old_emoji = status_change_emoji.get(old_status, '❓')
            new_emoji = status_change_emoji.get(status, '❓')
            status_msg = f'{old_emoji}→{new_emoji} Agent {agent_id}: {old_status} → {status}'
            self.add_system_message(status_msg)

    def update_phase(self, old_phase: str, new_phase: str):
        """Update system phase."""
        with self._lock:
            self.current_phase = new_phase
            phase_msg = f'Phase: {old_phase} → {new_phase}'
            self.add_system_message(phase_msg)

    def update_vote_distribution(self, vote_dist: Dict[int, int]):
        """Update vote distribution."""
        with self._lock:
            self.vote_distribution = vote_dist.copy()

    def update_consensus_status(self, representative_id: int, vote_dist: Dict[int, int]):
        """Update when consensus is reached."""
        with self._lock:
            self.consensus_reached = True
            self.representative_agent_id = representative_id
            self.vote_distribution = vote_dist.copy()
            consensus_msg = f'🎉 CONSENSUS REACHED! Agent {representative_id} selected as representative'
            self.add_system_message(consensus_msg)

    def reset_consensus(self):
        """Reset consensus state for new debate round."""
        with self._lock:
            self.consensus_reached = False
            self.representative_agent_id = None
            self.vote_distribution.clear()

    def update_agent_vote_target(self, agent_id: int, target_id: Optional[int]):
        """Update which agent this agent voted for."""
        with self._lock:
            self._agent_vote_targets[agent_id] = target_id

    def update_agent_chat_round(self, agent_id: int, round_num: int):
        """Update the chat round for an agent."""
        with self._lock:
            self._agent_chat_rounds[agent_id] = round_num

    def update_agent_update_count(self, agent_id: int, count: int):
        """Update the update count for an agent."""
        with self._lock:
            self._agent_update_counts[agent_id] = count

    def update_agent_votes_cast(self, agent_id: int, votes_cast: int):
        """Update the number of votes cast by an agent."""
        with self._lock:
            self._agent_votes_cast[agent_id] = votes_cast

    def update_debate_rounds(self, rounds: int):
        """Update the debate rounds count."""
        with self._lock:
            self.debate_rounds = rounds

    def _setup_logging(self):
        """Set up the logging directory and initialize log files."""
        base_logs_dir = 'logs'
        os.makedirs(base_logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_logs_dir = os.path.join(base_logs_dir, timestamp, 'display')
        os.makedirs(self.session_logs_dir, exist_ok=True)
        self.agent_log_files = {}
        self.system_log_file = os.path.join(self.session_logs_dir, 'system.txt')
        with open(self.system_log_file, 'w', encoding='utf-8') as f:
            f.write('MassGen System Messages Log\n')
            f.write(f'Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
            f.write('=' * 80 + '\n\n')

    def _get_agent_log_file(self, agent_id: int) -> str:
        """Get or create the log file path for a specific agent."""
        if agent_id not in self.agent_log_files:
            self.agent_log_files[agent_id] = os.path.join(self.session_logs_dir, f'agent_{agent_id}.txt')
            with open(self.agent_log_files[agent_id], 'w', encoding='utf-8') as f:
                f.write(f'MassGen Agent {agent_id} Output Log\n')
                f.write(f'Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                f.write('=' * 80 + '\n\n')
        return self.agent_log_files[agent_id]

    def get_agent_log_path_for_display(self, agent_id: int) -> str:
        """Get the log file path for display purposes (clickable link)."""
        if not self.save_logs:
            return ''
        log_path = self._get_agent_log_file(agent_id)
        return log_path

    def get_agent_answer_path_for_display(self, agent_id: int) -> str:
        """Get the answer file path for display purposes (clickable link)."""
        if not self.save_logs or not self.answers_dir:
            return ''
        answer_file_path = os.path.join(self.answers_dir, f'agent_{agent_id}.txt')
        return answer_file_path

    def get_system_log_path_for_display(self) -> str:
        """Get the system log file path for display purposes (clickable link)."""
        if not self.save_logs:
            return ''
        return self.system_log_file

    def _write_agent_log(self, agent_id: int, content: str):
        """Write content to the agent's log file."""
        if not self.save_logs:
            return
        try:
            log_file = self._get_agent_log_file(agent_id)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(content)
                f.flush()
        except Exception as e:
            print(f'Error writing to agent {agent_id} log: {e}')

    def _write_system_log(self, message: str):
        """Write a system message to the system log file."""
        if not self.save_logs:
            return
        try:
            with open(self.system_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%H:%M:%S')
                f.write(f'[{timestamp}] {message}\n')
                f.flush()
        except Exception as e:
            print(f'Error writing to system log: {e}')

    def stream_output_sync(self, agent_id: int, content: str):
        """FIXED: Buffered streaming with debounced display updates."""
        if not self.display_enabled:
            return
        with self._lock:
            if agent_id not in self.agent_outputs:
                self.agent_outputs[agent_id] = ''
            display_content = content
            log_content = content
            if content.startswith('[CODE_DISPLAY_ONLY]'):
                display_content = content[len('[CODE_DISPLAY_ONLY]'):]
                log_content = ''
            elif content.startswith('[CODE_LOG_ONLY]'):
                display_content = ''
                log_content = content[len('[CODE_LOG_ONLY]'):]
            if display_content:
                self.agent_outputs[agent_id] += display_content
            if log_content:
                self._write_agent_log(agent_id, log_content)
            if display_content:
                self._schedule_display_update()

    def _handle_terminal_resize(self):
        """Handle terminal resize by resetting cached dimensions."""
        try:
            current_width = os.get_terminal_size().columns
            if self._display_cache and abs(current_width - self._display_cache['terminal_width']) > 2:
                self._invalidate_display_cache()
                return True
        except OSError:
            self._invalidate_display_cache()
            return True
        return False

    def add_system_message(self, message: str):
        """Add a system message with timestamp."""
        with self._lock:
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f'[{timestamp}] {message}'
            self.system_messages.append(formatted_message)
            if len(self.system_messages) > 20:
                self.system_messages = self.system_messages[-20:]
            self._write_system_log(formatted_message + '\n')

    def format_agent_notification(self, agent_id: int, notification_type: str, content: str):
        """Format agent notifications for display."""
        notification_emoji = {'update': '📢', 'debate': '🗣️', 'presentation': '🎯', 'prompt': '💡'}
        emoji = notification_emoji.get(notification_type, '📨')
        notification_msg = f'{emoji} Agent {agent_id} received {notification_type} notification'
        self.add_system_message(notification_msg)

    def _update_display_immediate(self):
        """Immediate display update - called by the debounced scheduler."""
        if not self.display_enabled:
            return
        try:
            self._handle_terminal_resize()
            self._clear_terminal_atomic()
            agent_ids = sorted(self.agent_outputs.keys())
            if not agent_ids:
                return
            num_agents = len(agent_ids)
            col_width, total_width, terminal_width = self._calculate_layout(num_agents)
        except Exception as e:
            print(f'Display error: {e}')
            for agent_id in sorted(self.agent_outputs.keys()):
                print(f'Agent {agent_id}: {self.agent_outputs[agent_id][-100:]}')
            return
        agent_lines = {}
        max_lines = 0
        for agent_id in agent_ids:
            lines = self.agent_outputs[agent_id].split('\n')
            if len(lines) > self.max_lines:
                lines = lines[-self.max_lines:]
            agent_lines[agent_id] = lines
            max_lines = max(max_lines, len(lines))
        border_line = '─' * total_width
        print('')
        BRIGHT_CYAN = '\x1b[96m'
        BRIGHT_GREEN = '\x1b[92m'
        BRIGHT_YELLOW = '\x1b[93m'
        BRIGHT_MAGENTA = '\x1b[95m'
        BRIGHT_RED = '\x1b[91m'
        BRIGHT_WHITE = '\x1b[97m'
        BOLD = '\x1b[1m'
        RESET = '\x1b[0m'
        header_top = f'{BRIGHT_CYAN}{BOLD}╔{'═' * (total_width - 2)}╗{RESET}'
        print(header_top)
        header_empty = f'{BRIGHT_CYAN}║{' ' * (total_width - 2)}║{RESET}'
        print(header_empty)
        title_text = '🚀 MassGen - Multi-Agent Scaling System 🚀'
        title_line_content = self._pad_to_width(title_text, total_width - 2, 'center')
        title_line = f'{BRIGHT_CYAN}║{BRIGHT_YELLOW}{BOLD}{title_line_content}{RESET}{BRIGHT_CYAN}║{RESET}'
        print(title_line)
        subtitle_text = '🔬 Advanced Agent Collaboration Framework'
        subtitle_line_content = self._pad_to_width(subtitle_text, total_width - 2, 'center')
        subtitle_line = f'{BRIGHT_CYAN}║{BRIGHT_GREEN}{subtitle_line_content}{RESET}{BRIGHT_CYAN}║{RESET}'
        print(subtitle_line)
        print(header_empty)
        header_bottom = f'{BRIGHT_CYAN}{BOLD}╚{'═' * (total_width - 2)}╝{RESET}'
        print(header_bottom)
        print(f'\n{border_line}')
        header_parts = []
        for agent_id in agent_ids:
            model_name = self.agent_models.get(agent_id, '')
            status = self.agent_statuses.get(agent_id, 'unknown')
            status_config = {'working': {'emoji': '🔄', 'color': BRIGHT_YELLOW}, 'voted': {'emoji': '✅', 'color': BRIGHT_GREEN}, 'failed': {'emoji': '❌', 'color': BRIGHT_RED}, 'unknown': {'emoji': '❓', 'color': BRIGHT_WHITE}}
            config = status_config.get(status, status_config['unknown'])
            emoji = config['emoji']
            status_color = config['color']
            if model_name:
                agent_header = f'{emoji} {BRIGHT_CYAN}Agent {agent_id}{RESET} {BRIGHT_MAGENTA}({model_name}){RESET} {status_color}[{status}]{RESET}'
            else:
                agent_header = f'{emoji} {BRIGHT_CYAN}Agent {agent_id}{RESET} {status_color}[{status}]{RESET}'
            header_content = self._pad_to_width(agent_header, col_width, 'center')
            if self._get_display_width(header_content) != col_width:
                simple_header = f'Agent {agent_id} [{status}]'
                header_content = self._pad_to_width(simple_header, col_width, 'center')
            header_parts.append(header_content)
        try:
            header_line = self._create_bordered_line(header_parts, total_width)
            print(header_line)
        except Exception:
            print('─' * total_width)
        state_parts = []
        for agent_id in agent_ids:
            chat_round = getattr(self, '_agent_chat_rounds', {}).get(agent_id, 0)
            vote_target = getattr(self, '_agent_vote_targets', {}).get(agent_id)
            update_count = getattr(self, '_agent_update_counts', {}).get(agent_id, 0)
            votes_cast = getattr(self, '_agent_votes_cast', {}).get(agent_id, 0)
            state_info = []
            state_info.append(f'{BRIGHT_WHITE}Round:{RESET} {BRIGHT_GREEN}{chat_round}{RESET}')
            state_info.append(f'{BRIGHT_WHITE}#Updates:{RESET} {BRIGHT_MAGENTA}{update_count}{RESET}')
            state_info.append(f'{BRIGHT_WHITE}#Votes:{RESET} {BRIGHT_CYAN}{votes_cast}{RESET}')
            if vote_target:
                state_info.append(f'{BRIGHT_WHITE}Vote →{RESET} {BRIGHT_GREEN}{vote_target}{RESET}')
            else:
                state_info.append(f'{BRIGHT_WHITE}Vote →{RESET} None')
            state_text = f'📊 {' | '.join(state_info)}'
            state_content = self._pad_to_width(state_text, col_width, 'center')
            state_parts.append(state_content)
        try:
            state_line = self._create_bordered_line(state_parts, total_width)
            print(state_line)
        except Exception:
            print('─' * total_width)
        if self.save_logs and (hasattr(self, 'session_logs_dir') or self.answers_dir):
            UNDERLINE = '\x1b[4m'
            link_parts = []
            for agent_id in agent_ids:
                answer_path = self.get_agent_answer_path_for_display(agent_id)
                if answer_path:
                    display_path = answer_path.replace(os.getcwd() + '/', '') if answer_path.startswith(os.getcwd()) else answer_path
                    prefix = '📄 Answers: '
                    max_path_len = max(10, col_width - self._get_display_width(prefix) - 8)
                    if len(display_path) > max_path_len:
                        display_path = '...' + display_path[-(max_path_len - 3):]
                    link_text = f'{prefix}{UNDERLINE}{display_path}{RESET}'
                    link_content = self._pad_to_width(link_text, col_width, 'center')
                else:
                    log_path = self.get_agent_log_path_for_display(agent_id)
                    if log_path:
                        display_path = log_path.replace(os.getcwd() + '/', '') if log_path.startswith(os.getcwd()) else log_path
                        prefix = '📁 Log: '
                        max_path_len = max(10, col_width - self._get_display_width(prefix) - 8)
                        if len(display_path) > max_path_len:
                            display_path = '...' + display_path[-(max_path_len - 3):]
                        link_text = f'{prefix}{UNDERLINE}{display_path}{RESET}'
                        link_content = self._pad_to_width(link_text, col_width, 'center')
                    else:
                        link_content = self._pad_to_width('', col_width, 'center')
                link_parts.append(link_content)
            try:
                log_line = self._create_bordered_line(link_parts, total_width)
                print(log_line)
            except Exception:
                print('─' * total_width)
        print(border_line)
        for line_idx in range(max_lines):
            content_parts = []
            for agent_id in agent_ids:
                lines = agent_lines[agent_id]
                content = lines[line_idx] if line_idx < len(lines) else ''
                padded_content = self._pad_to_width(content, col_width, 'left')
                content_parts.append(padded_content)
            try:
                content_line = self._create_bordered_line(content_parts, total_width)
                print(content_line)
            except Exception:
                simple_line = ' | '.join(content_parts)[:total_width - 4]
                simple_line = simple_line + ' ' * max(0, total_width - 4 - len(simple_line))
                print(f'│ {simple_line} │')
        if self.system_messages or self.current_phase or self.vote_distribution:
            print(f'\n{border_line}')
            phase_color = BRIGHT_YELLOW if self.current_phase == 'collaboration' else BRIGHT_GREEN
            consensus_color = BRIGHT_GREEN if self.consensus_reached else BRIGHT_RED
            consensus_text = '✅ YES' if self.consensus_reached else '❌ NO'
            system_state_info = []
            system_state_info.append(f'{BRIGHT_WHITE}Phase:{RESET} {phase_color}{self.current_phase.upper()}{RESET}')
            system_state_info.append(f'{BRIGHT_WHITE}Consensus:{RESET} {consensus_color}{consensus_text}{RESET}')
            system_state_info.append(f'{BRIGHT_WHITE}Debate Rounds:{RESET} {BRIGHT_CYAN}{self.debate_rounds}{RESET}')
            if self.representative_agent_id:
                system_state_info.append(f'{BRIGHT_WHITE}Representative Agent:{RESET} {BRIGHT_GREEN}{self.representative_agent_id}{RESET}')
            else:
                system_state_info.append(f'{BRIGHT_WHITE}Representative Agent:{RESET} None')
            system_header_text = f'{BRIGHT_CYAN}📋 SYSTEM STATE{RESET} - {' | '.join(system_state_info)}'
            system_header_line = self._create_system_bordered_line(system_header_text, total_width)
            print(system_header_line)
            if self.save_logs and hasattr(self, 'system_log_file'):
                system_log_path = self.get_system_log_path_for_display()
                if system_log_path:
                    UNDERLINE = '\x1b[4m'
                    display_path = system_log_path.replace(os.getcwd() + '/', '') if system_log_path.startswith(os.getcwd()) else system_log_path
                    prefix = '📁 Log: '
                    max_path_len = max(10, total_width - self._get_display_width(prefix) - 15)
                    if len(display_path) > max_path_len:
                        display_path = '...' + display_path[-(max_path_len - 3):]
                    system_link_text = f'{prefix}{UNDERLINE}{display_path}{RESET}'
                    system_link_line = self._create_system_bordered_line(system_link_text, total_width)
                    print(system_link_line)
            print(border_line)
            if self.consensus_reached and self.representative_agent_id is not None:
                consensus_msg = f'🎉 CONSENSUS REACHED! Representative: Agent {self.representative_agent_id}'
                consensus_line = self._create_system_bordered_line(consensus_msg, total_width)
                print(consensus_line)
            if self.vote_distribution:
                vote_msg = '📊  Vote Distribution: ' + ', '.join([f'Agent {k}→{v} votes' for k, v in self.vote_distribution.items()])
                max_content_width = total_width - 2
                if self._get_display_width(vote_msg) <= max_content_width:
                    vote_line = self._create_system_bordered_line(vote_msg, total_width)
                    print(vote_line)
                else:
                    vote_header = '📊  Vote Distribution:'
                    header_line = self._create_system_bordered_line(vote_header, total_width)
                    print(header_line)
                    for agent_id, votes in self.vote_distribution.items():
                        vote_detail = f'   Agent {agent_id}: {votes} votes'
                        detail_line = self._create_system_bordered_line(vote_detail, total_width)
                        print(detail_line)
            for message in self.system_messages:
                max_content_width = total_width - 2
                if self._get_display_width(message) <= max_content_width:
                    line = self._create_system_bordered_line(message, total_width)
                    print(line)
                else:
                    words = message.split()
                    current_line = ''
                    for word in words:
                        test_line = f'{current_line} {word}'.strip()
                        if self._get_display_width(test_line) > max_content_width:
                            if current_line.strip():
                                line = self._create_system_bordered_line(current_line.strip(), total_width)
                                print(line)
                            current_line = word
                        else:
                            current_line = test_line
                    if current_line.strip():
                        line = self._create_system_bordered_line(current_line.strip(), total_width)
                        print(line)
        print(border_line)
        sys.stdout.flush()

    def force_update_display(self):
        """Force an immediate display update (for status changes)."""
        with self._lock:
            if self._update_timer:
                self._update_timer.cancel()
            self._pending_update = True
        self._execute_display_update()

def _clear_terminal_atomic(self):
    """Atomically clear terminal using proper ANSI sequences."""
    try:
        sys.stdout.write('\x1b[2J')
        sys.stdout.write('\x1b[H')
        sys.stdout.flush()
    except Exception:
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
        except Exception:
            pass

def _setup_logging(self):
    """Set up the logging directory and initialize log files."""
    base_logs_dir = 'logs'
    os.makedirs(base_logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    self.session_logs_dir = os.path.join(base_logs_dir, timestamp, 'display')
    os.makedirs(self.session_logs_dir, exist_ok=True)
    self.agent_log_files = {}
    self.system_log_file = os.path.join(self.session_logs_dir, 'system.txt')
    with open(self.system_log_file, 'w', encoding='utf-8') as f:
        f.write('MassGen System Messages Log\n')
        f.write(f'Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
        f.write('=' * 80 + '\n\n')

def _get_agent_log_file(self, agent_id: int) -> str:
    """Get or create the log file path for a specific agent."""
    if agent_id not in self.agent_log_files:
        self.agent_log_files[agent_id] = os.path.join(self.session_logs_dir, f'agent_{agent_id}.txt')
        with open(self.agent_log_files[agent_id], 'w', encoding='utf-8') as f:
            f.write(f'MassGen Agent {agent_id} Output Log\n')
            f.write(f'Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
            f.write('=' * 80 + '\n\n')
    return self.agent_log_files[agent_id]

def get_agent_log_path_for_display(self, agent_id: int) -> str:
    """Get the log file path for display purposes (clickable link)."""
    if not self.save_logs:
        return ''
    log_path = self._get_agent_log_file(agent_id)
    return log_path

def _write_agent_log(self, agent_id: int, content: str):
    """Write content to the agent's log file."""
    if not self.save_logs:
        return
    try:
        log_file = self._get_agent_log_file(agent_id)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(content)
            f.flush()
    except Exception as e:
        print(f'Error writing to agent {agent_id} log: {e}')

def _write_system_log(self, message: str):
    """Write a system message to the system log file."""
    if not self.save_logs:
        return
    try:
        with open(self.system_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%H:%M:%S')
            f.write(f'[{timestamp}] {message}\n')
            f.flush()
    except Exception as e:
        print(f'Error writing to system log: {e}')

def add_system_message(self, message: str):
    """Add a system message with timestamp."""
    with self._lock:
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f'[{timestamp}] {message}'
        self.system_messages.append(formatted_message)
        if len(self.system_messages) > 20:
            self.system_messages = self.system_messages[-20:]
        self._write_system_log(formatted_message + '\n')

def load_config_from_yaml(config_path: Union[str, Path]) -> MassConfig:
    """
    Load MassGen configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        MassConfig object with loaded configuration

    Raises:
        ConfigurationError: If configuration is invalid or file cannot be loaded
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise ConfigurationError(f'Configuration file not found: {config_path}')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f'Invalid YAML format: {e}')
    except Exception as e:
        raise ConfigurationError(f'Failed to read configuration file: {e}')
    if not yaml_data:
        raise ConfigurationError('Empty configuration file')
    return _dict_to_config(yaml_data)

class MassAgent(ABC):
    """
    Abstract base class for all agents in the MassGen system.

    All agent implementations must inherit from this class and implement
    the required methods while following the standardized workflow.
    """

    def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
        """
        Initialize the agent with configuration parameters.

        Args:
            agent_id: Unique identifier for this agent
            orchestrator: Reference to the MassOrchestrator
            model_config: Configuration object containing model parameters (model, tools,
                         temperature, top_p, max_tokens, inference_timeout, max_retries, stream)
            stream_callback: Optional callback function for streaming chunks
            agent_type: Type of agent ("openai", "gemini", "grok") to determine backend
            **kwargs: Additional parameters specific to the agent implementation
        """
        self.agent_id = agent_id
        self.orchestrator = orchestrator
        self.state = AgentState(agent_id=agent_id)
        if model_config is None:
            model_config = ModelConfig()
        self.model = model_config.model
        self.agent_type = get_agent_type_from_model(self.model)
        process_message_impl_map = {'openai': oai.process_message, 'gemini': gemini.process_message, 'grok': grok.process_message}
        if self.agent_type not in process_message_impl_map:
            raise ValueError(f'Unknown agent type: {self.agent_type}. Available types: {list(process_message_impl_map.keys())}')
        self.process_message_impl = process_message_impl_map[self.agent_type]
        self.tools = model_config.tools
        self.max_retries = model_config.max_retries
        self.max_rounds = model_config.max_rounds
        self.max_tokens = model_config.max_tokens
        self.temperature = model_config.temperature
        self.top_p = model_config.top_p
        self.inference_timeout = model_config.inference_timeout
        self.stream = model_config.stream
        self.stream_callback = stream_callback
        self.kwargs = kwargs

    def process_message(self, messages: List[Dict[str, str]], tools: List[str]=None) -> AgentResponse:
        """
        Core LLM inference function for task processing.

        This method handles the actual LLM interaction using the agent's
        specific backend (OpenAI, Gemini, Grok, etc.) and returns a standardized response.
        All configuration parameters are stored as instance variables and accessed
        via self.model, self.tools, self.temperature, etc.

        Args:
            messages: List of messages in OpenAI format
            tools: List of tools to use

        Returns:
            AgentResponse containing the agent's response text, code, citations, etc.
        """
        config = {'model': self.model, 'max_retries': self.max_retries, 'max_tokens': self.max_tokens, 'temperature': self.temperature, 'top_p': self.top_p, 'api_key': None, 'stream': self.stream, 'stream_callback': self.stream_callback}
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.process_message_impl, messages=messages, tools=tools, **config)
                try:
                    result = future.result(timeout=self.inference_timeout)
                    return result
                except FutureTimeoutError:
                    timeout_msg = f'Agent {self.agent_id} timed out after {self.inference_timeout} seconds'
                    self.mark_failed(timeout_msg)
                    return AgentResponse(text=f'Agent processing timed out after {self.inference_timeout} seconds', code=[], citations=[], function_calls=[])
        except Exception as e:
            return AgentResponse(text=f'Error in {self.model} agent processing: {str(e)}', code=[], citations=[], function_calls=[])

    def add_answer(self, new_answer: str):
        """
        Record your work on the task: your analysis, approach, solution, and reasoning. Update when you solve the problem, find better solutions, or incorporate valuable insights from other agents.

        Args:
            answer: The new answer, which should be self-contained, complete, and ready to serve as the definitive final response.
        """
        self.orchestrator.notify_answer_update(self.agent_id, new_answer)
        return 'The new answer has been added.'

    def vote(self, agent_id: int, reason: str='', invalid_vote_options: List[int]=[]):
        """
        Vote for the representative agent, who you believe has found the correct solution.

        Args:
            agent_id: ID of the voted agent
            reason: Your full explanation of why you voted for this agent
            invalid_vote_options: The list of agent IDs that are invalid to vote for (have new updates)
        """
        if agent_id in invalid_vote_options:
            return f'Error: Voting for agent {agent_id} is not allowed as its answer has been updated!'
        self.orchestrator.cast_vote(self.agent_id, agent_id, reason)
        return f'Your vote for Agent {agent_id} has been cast.'

    def check_update(self) -> List[int]:
        """
        Check if there are any updates from other agents since this agent last saw them.
        """
        agents_with_update = set()
        for other_id, other_state in self.orchestrator.agent_states.items():
            if other_id != self.agent_id and other_state.updated_answers:
                for update in other_state.updated_answers:
                    last_seen = self.state.seen_updates_timestamps.get(other_id, 0)
                    if update.timestamp > last_seen:
                        self.state.seen_updates_timestamps[other_id] = update.timestamp
                        agents_with_update.add(other_id)
        return list(agents_with_update)

    def mark_failed(self, reason: str=''):
        """
        Mark this agent as failed.

        Args:
            reason: Optional reason for the failure
        """
        self.orchestrator.mark_agent_failed(self.agent_id, reason)

    def deduplicate_function_calls(self, function_calls: List[Dict]):
        """Deduplicate function calls by their name and arguments."""
        deduplicated_function_calls = []
        for func_call in function_calls:
            if func_call not in deduplicated_function_calls:
                deduplicated_function_calls.append(func_call)
        return deduplicated_function_calls

    def _execute_function_calls(self, function_calls: List[Dict], invalid_vote_options: List[int]=[]):
        """Execute function calls and return function outputs."""
        from .tools import register_tool
        function_outputs = []
        successful_called = []
        for func_call in function_calls:
            func_call_id = func_call.get('call_id')
            func_name = func_call.get('name')
            func_args = func_call.get('arguments', {})
            if isinstance(func_args, str):
                func_args = json.loads(func_args)
            try:
                if func_name == 'add_answer':
                    result = self.add_answer(func_args.get('new_answer', ''))
                elif func_name == 'vote':
                    result = self.vote(func_args.get('agent_id'), func_args.get('reason', ''), invalid_vote_options)
                elif func_name in register_tool:
                    result = register_tool[func_name](**func_args)
                else:
                    result = {'type': 'function_call_output', 'call_id': func_call_id, 'output': f"Error: Function '{func_name}' not found in tool mapping"}
                function_output = {'type': 'function_call_output', 'call_id': func_call_id, 'output': str(result)}
                function_outputs.append(function_output)
                successful_called.append(True)
            except Exception as e:
                error_output = {'type': 'function_call_output', 'call_id': func_call_id, 'output': f'Error executing function: {str(e)}'}
                function_outputs.append(error_output)
                successful_called.append(False)
                print(f'Error executing function {func_name}: {e}')
                with open('function_calls.txt', 'a') as f:
                    f.write(f'[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agent {self.agent_id} ({self.model}):\n')
                    f.write(f'{json.dumps(error_output, indent=2)}\n')
                    f.write(f'Successful called: {False}\n')
        return (function_outputs, successful_called)

    def _get_system_tools(self) -> List[Dict[str, Any]]:
        """
        The system tools available to this agent for orchestration:
        - add_answer: Your added new answer, which should be self-contained, complete, and ready to serve as the definitive final response.
        - vote: Vote for the representative agent, who you believe has found the correct solution.
        """
        add_answer_schema = {'type': 'function', 'name': 'add_answer', 'description': 'Add your new answer if you believe it is better than the current answers.', 'parameters': {'type': 'object', 'properties': {'new_answer': {'type': 'string', 'description': 'Your new answer, which should be self-contained, complete, and ready to serve as the definitive final response.'}}, 'required': ['new_answer']}}
        vote_schema = {'type': 'function', 'name': 'vote', 'description': 'Vote for the best agent to present final answer. Submit its agent_id (integer) and reason for your vote.', 'parameters': {'type': 'object', 'properties': {'agent_id': {'type': 'integer', 'description': 'The ID of the agent you believe has found the best answer that addresses the original message.'}, 'reason': {'type': 'string', 'description': 'Your full explanation of why you voted for this agent.'}}, 'required': ['agent_id', 'reason']}}
        available_options = [agent_id for agent_id, agent_state in self.orchestrator.agent_states.items() if agent_state.curr_answer]
        return [add_answer_schema, vote_schema] if available_options else [add_answer_schema]

    def _get_registered_tools(self) -> List[Dict[str, Any]]:
        """Return the tool schema for the tools that are available to this agent."""
        custom_tools = []
        from .tools import register_tool
        for tool_name, tool_func in register_tool.items():
            if tool_name in self.tools:
                tool_schema = function_to_json(tool_func)
                custom_tools.append(tool_schema)
        return custom_tools

    def _get_builtin_tools(self) -> List[Dict[str, Any]]:
        """
        Override the parent method due to the Gemini's limitation.
        Return the built-in tools that are available to Gemini models.
        live_search and code_execution are supported right now.
        However, the built-in tools and function call are not supported at the same time.
        """
        builtin_tools = []
        for tool in self.tools:
            if tool in ['live_search', 'code_execution']:
                builtin_tools.append(tool)
        return builtin_tools

    def _get_all_answers(self) -> List[str]:
        """Get all answers from all agents.
        Format:
        **Agent 1**: Answer 1
        **Agent 2**: Answer 2
        ...
        """
        agent_answers = []
        for agent_id, agent_state in self.orchestrator.agent_states.items():
            if agent_state.curr_answer:
                agent_answers.append(f'**Agent {agent_id}**: {agent_state.curr_answer}')
        return agent_answers

    def _get_all_votes(self) -> List[str]:
        """Get all votes from all agents.
        Format:
        **Vote for Agent 1**: Reason 1
        **Vote for Agent 2**: Reason 2
        ...
        """
        agent_votes = []
        for agent_id, agent_state in self.orchestrator.agent_states.items():
            if agent_state.curr_vote:
                agent_votes.append(f'**Vote for Agent {agent_state.curr_vote.target_id}**: {agent_state.curr_vote.reason}')
        return agent_votes

    def _get_task_input(self, task: TaskInput) -> str:
        """Get the initial task input as the user message. Return Both the current status and the task input."""
        if not self.state.curr_answer:
            status = 'initial'
            task_input = AGENT_ANSWER_MESSAGE.format(task=task.question, agent_answers='None') + 'There are no current answers right now. Please use your expertise and tools (if available) to provide a new answer and submit it using the `add_answer` tool first.'
            return (status, task_input)
        all_agent_answers = self._get_all_answers()
        all_agent_answers_str = '\n\n'.join(all_agent_answers)
        voted_agents = [agent_id for agent_id, agent_state in self.orchestrator.agent_states.items() if agent_state.curr_vote is not None]
        if len(voted_agents) == len(self.orchestrator.agent_states):
            all_agent_votes = self._get_all_votes()
            all_agent_votes_str = '\n\n'.join(all_agent_votes)
            status = 'debate'
            task_input = AGENT_ANSWER_AND_VOTE_MESSAGE.format(task=task.question, agent_answers=all_agent_answers_str, agent_votes=all_agent_votes_str)
        else:
            status = 'working'
            task_input = AGENT_ANSWER_MESSAGE.format(task=task.question, agent_answers=all_agent_answers_str)
        return (status, task_input)

    def _get_task_input_messages(self, user_input: str) -> List[Dict[str, str]]:
        """Get the task input messages for the agent."""
        return [{'role': 'system', 'content': SYSTEM_INSTRUCTION}, {'role': 'user', 'content': user_input}]

    def _get_curr_messages_and_tools(self, task: TaskInput):
        """Get the current messages and tools for the agent."""
        working_status, user_input = self._get_task_input(task)
        working_messages = self._get_task_input_messages(user_input)
        all_tools = []
        all_tools.extend(self._get_builtin_tools())
        all_tools.extend(self._get_registered_tools())
        all_tools.extend(self._get_system_tools())
        return (working_status, working_messages, all_tools)

    def work_on_task(self, task: TaskInput) -> List[Dict[str, str]]:
        """
        Work on the task with conversation continuation.

        Args:
            task: The task to work on
            messages: Current conversation history
            restart_instruction: Optional instruction for restarting work (e.g., updates from other agents)

        Returns:
            Updated conversation history including agent's work

        This method should be implemented by concrete agent classes.
        The agent continues the conversation until it votes or reaches max rounds.
        """
        curr_round = 0
        working_status, working_messages, all_tools = self._get_curr_messages_and_tools(task)
        while curr_round < self.max_rounds and self.state.status == 'working':
            try:
                result = self.process_message(messages=working_messages, tools=all_tools)
                agents_with_update = self.check_update()
                has_update = len(agents_with_update) > 0
                if result.text:
                    working_messages.append({'role': 'assistant', 'content': result.text})
                if result.function_calls:
                    result.function_calls = self.deduplicate_function_calls(result.function_calls)
                    function_outputs, successful_called = self._execute_function_calls(result.function_calls, invalid_vote_options=agents_with_update)
                    renew_conversation = False
                    for function_call, function_output, successful_called in zip(result.function_calls, function_outputs, successful_called):
                        if function_call.get('name') == 'add_answer' and successful_called:
                            renew_conversation = True
                            break
                        if function_call.get('name') == 'vote' and successful_called:
                            renew_conversation = True
                            break
                    if not renew_conversation:
                        for function_call, function_output in zip(result.function_calls, function_outputs):
                            working_messages.extend([function_call, function_output])
                    else:
                        working_status, working_messages, all_tools = self._get_curr_messages_and_tools(task)
                elif self.state.status == 'voted':
                    break
                elif has_update and working_status != 'initial':
                    working_status, working_messages, all_tools = self._get_curr_messages_and_tools(task)
                else:
                    working_messages.append({'role': 'user', 'content': 'Finish your work above by making a tool call of `vote` or `add_answer`. Make sure you actually call the tool.'})
                curr_round += 1
                self.state.chat_round += 1
                if self.state.status in ['voted', 'failed']:
                    break
            except Exception as e:
                print(f'❌ Agent {self.agent_id} error in round {self.state.chat_round}: {e}')
                if self.orchestrator:
                    self.orchestrator.mark_agent_failed(self.agent_id, str(e))
                self.state.chat_round += 1
                curr_round += 1
                break
        return working_messages

def _execute_function_calls(self, function_calls: List[Dict], invalid_vote_options: List[int]=[]):
    """Execute function calls and return function outputs."""
    from .tools import register_tool
    function_outputs = []
    successful_called = []
    for func_call in function_calls:
        func_call_id = func_call.get('call_id')
        func_name = func_call.get('name')
        func_args = func_call.get('arguments', {})
        if isinstance(func_args, str):
            func_args = json.loads(func_args)
        try:
            if func_name == 'add_answer':
                result = self.add_answer(func_args.get('new_answer', ''))
            elif func_name == 'vote':
                result = self.vote(func_args.get('agent_id'), func_args.get('reason', ''), invalid_vote_options)
            elif func_name in register_tool:
                result = register_tool[func_name](**func_args)
            else:
                result = {'type': 'function_call_output', 'call_id': func_call_id, 'output': f"Error: Function '{func_name}' not found in tool mapping"}
            function_output = {'type': 'function_call_output', 'call_id': func_call_id, 'output': str(result)}
            function_outputs.append(function_output)
            successful_called.append(True)
        except Exception as e:
            error_output = {'type': 'function_call_output', 'call_id': func_call_id, 'output': f'Error executing function: {str(e)}'}
            function_outputs.append(error_output)
            successful_called.append(False)
            print(f'Error executing function {func_name}: {e}')
            with open('function_calls.txt', 'a') as f:
                f.write(f'[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agent {self.agent_id} ({self.model}):\n')
                f.write(f'{json.dumps(error_output, indent=2)}\n')
                f.write(f'Successful called: {False}\n')
    return (function_outputs, successful_called)

def process_message(messages, model='gpt-4.1-mini', tools=None, max_retries=10, max_tokens=None, temperature=None, top_p=None, api_key=None, stream=False, stream_callback=None):
    """
    Generate content using OpenAI API with optional streaming support.

    Args:
        messages: List of messages in OpenAI format
        model: The OpenAI model to use
        tools: List of tools to use
        max_retries: Maximum number of retry attempts
        max_tokens: Maximum number of tokens in response
        temperature: Temperature for generation
        top_p: Top-p value for generation
        api_key: OpenAI API key (if None, will get from environment)
        stream: Whether to stream the response (default: False)
        stream_callback: Optional callback function for streaming chunks

    Returns:
        dict: {"text": text, "code": code, "citations": citations, "function_calls": function_calls}
    """
    'Internal function that contains all the processing logic.'
    if api_key is None:
        api_key_val = os.getenv('OPENAI_API_KEY')
    else:
        api_key_val = api_key
    if not api_key_val:
        raise ValueError('OPENAI_API_KEY not found in environment variables')
    client = OpenAI(api_key=api_key_val)
    formatted_tools = []
    if tools:
        for tool in tools:
            if isinstance(tool, dict):
                formatted_tools.append(tool)
            elif callable(tool):
                formatted_tools.append(function_to_json(tool))
            elif tool == 'live_search':
                formatted_tools.append({'type': 'web_search_preview'})
            elif tool == 'code_execution':
                formatted_tools.append({'type': 'code_interpreter', 'container': {'type': 'auto'}})
            else:
                raise ValueError(f'Invalid tool type: {type(tool)}')
    input_text = []
    instructions = ''
    for message in messages:
        if message.get('role', '') == 'system':
            instructions = message['content']
        else:
            if message.get('type', '') == 'function_call' and message.get('id', None) is not None:
                del message['id']
            input_text.append(message)
    completion = None
    retry = 0
    while retry < max_retries:
        try:
            model_name = model
            params = {'model': model_name, 'tools': formatted_tools if formatted_tools else None, 'instructions': instructions if instructions else None, 'input': input_text, 'max_output_tokens': max_tokens if max_tokens else None, 'stream': True if stream and stream_callback else False}
            if formatted_tools and any((tool.get('type') == 'code_interpreter' for tool in formatted_tools)):
                params['include'] = ['code_interpreter_call.outputs']
            if temperature is not None and (not model_name.startswith('o')):
                params['temperature'] = temperature
            if top_p is not None and (not model_name.startswith('o')):
                params['top_p'] = top_p
            if model_name.startswith('o'):
                if model_name.endswith('-low'):
                    params['reasoning'] = {'effort': 'low'}
                    model_name = model_name.replace('-low', '')
                elif model_name.endswith('-medium'):
                    params['reasoning'] = {'effort': 'medium'}
                    model_name = model_name.replace('-medium', '')
                elif model_name.endswith('-high'):
                    params['reasoning'] = {'effort': 'high'}
                    model_name = model_name.replace('-high', '')
                else:
                    params['reasoning'] = {'effort': 'low'}
            params['model'] = model_name
            response = client.responses.create(**params)
            completion = response
            break
        except Exception as e:
            print(f'Error on attempt {retry + 1}: {e}')
            retry += 1
            import time
            time.sleep(1.5)
    if completion is None:
        print(f'Failed to get completion after {max_retries} retries, returning empty response')
        return AgentResponse(text='', code=[], citations=[], function_calls=[])
    if stream and stream_callback:
        text = ''
        code = []
        citations = []
        function_calls = []
        code_lines_shown = 0
        current_code_chunk = ''
        truncation_message_sent = False
        current_function_call = None
        current_function_arguments = ''
        for chunk in completion:
            if hasattr(chunk, 'type'):
                if chunk.type == 'response.output_text.delta':
                    if hasattr(chunk, 'delta') and chunk.delta:
                        chunk_text = chunk.delta
                        text += chunk_text
                        try:
                            stream_callback(chunk_text)
                        except Exception as e:
                            print(f'Stream callback error: {e}')
                elif chunk.type == 'response.function_call_output.delta':
                    try:
                        stream_callback(f'\n🔧 {(chunk.delta if hasattr(chunk, 'delta') else 'Function call')}\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.function_call_output.done':
                    try:
                        stream_callback('\n🔧 Function call completed\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.code_interpreter_call.in_progress':
                    code_lines_shown = 0
                    current_code_chunk = ''
                    truncation_message_sent = False
                    try:
                        stream_callback('\n💻 Starting code execution...\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.code_interpreter_call_code.delta':
                    if hasattr(chunk, 'delta') and chunk.delta:
                        try:
                            current_code_chunk += chunk.delta
                            new_lines = chunk.delta.count('\n')
                            if code_lines_shown < 3:
                                stream_callback(chunk.delta)
                                code_lines_shown += new_lines
                                if code_lines_shown >= 3 and (not truncation_message_sent):
                                    stream_callback('\n[CODE_DISPLAY_ONLY]\n💻 ... (full code in log file)\n')
                                    truncation_message_sent = True
                            else:
                                stream_callback(f'[CODE_LOG_ONLY]{chunk.delta}')
                        except Exception as e:
                            print(f'Stream callback error: {e}')
                elif chunk.type == 'response.code_interpreter_call_code.done':
                    if current_code_chunk:
                        code.append(current_code_chunk)
                    try:
                        stream_callback('\n💻 Code writing completed\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.code_interpreter_call_execution.in_progress':
                    try:
                        stream_callback('\n💻 Executing code...\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.code_interpreter_call_execution.done':
                    try:
                        stream_callback('\n💻 Code execution completed\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.output_item.added':
                    if hasattr(chunk, 'item') and chunk.item:
                        if hasattr(chunk.item, 'type') and chunk.item.type == 'web_search_call':
                            try:
                                stream_callback('\n🔍 Starting web search...\n')
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                        elif hasattr(chunk.item, 'type') and chunk.item.type == 'reasoning':
                            try:
                                stream_callback('\n🧠 Reasoning in progress...\n')
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                        elif hasattr(chunk.item, 'type') and chunk.item.type == 'code_interpreter_call':
                            try:
                                stream_callback('\n💻 Code interpreter starting...\n')
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                        elif hasattr(chunk.item, 'type') and chunk.item.type == 'function_call':
                            function_call_data = {'type': 'function_call', 'name': getattr(chunk.item, 'name', None), 'arguments': getattr(chunk.item, 'arguments', None), 'call_id': getattr(chunk.item, 'call_id', None), 'id': getattr(chunk.item, 'id', None)}
                            function_calls.append(function_call_data)
                            current_function_call = function_call_data
                            current_function_arguments = ''
                            function_name = function_call_data.get('name', 'unknown')
                            try:
                                stream_callback(f"\n🔧 Calling function '{function_name}'...\n")
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                elif chunk.type == 'response.output_item.done':
                    if hasattr(chunk, 'item') and chunk.item:
                        if hasattr(chunk.item, 'type') and chunk.item.type == 'web_search_call':
                            if hasattr(chunk.item, 'action') and hasattr(chunk.item.action, 'query'):
                                search_query = chunk.item.action.query
                                if search_query:
                                    try:
                                        stream_callback(f'\n🔍 Completed search for: {search_query}\n')
                                    except Exception as e:
                                        print(f'Stream callback error: {e}')
                        elif hasattr(chunk.item, 'type') and chunk.item.type == 'reasoning':
                            try:
                                stream_callback('\n🧠 Reasoning completed\n')
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                        elif hasattr(chunk.item, 'type') and chunk.item.type == 'code_interpreter_call':
                            if hasattr(chunk.item, 'outputs') and chunk.item.outputs:
                                for output in chunk.item.outputs:
                                    if hasattr(output, 'get') and output.get('type') == 'logs':
                                        logs_content = output.get('logs')
                                        if logs_content:
                                            execution_result = f'\n[Code Execution Output]\n{logs_content}\n'
                                            text += execution_result
                                            try:
                                                stream_callback(execution_result)
                                            except Exception as e:
                                                print(f'Stream callback error: {e}')
                                    elif hasattr(output, 'type') and output.type == 'logs':
                                        if hasattr(output, 'logs') and output.logs:
                                            execution_result = f'\n[Code Execution Output]\n{output.logs}\n'
                                            text += execution_result
                                            try:
                                                stream_callback(execution_result)
                                            except Exception as e:
                                                print(f'Stream callback error: {e}')
                            try:
                                stream_callback('\n💻 Code interpreter completed\n')
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                        elif hasattr(chunk.item, 'type') and chunk.item.type == 'function_call':
                            if hasattr(chunk.item, 'arguments'):
                                for fc in function_calls:
                                    if fc.get('id') == getattr(chunk.item, 'id', None):
                                        fc['arguments'] = chunk.item.arguments
                                        break
                            if current_function_call and current_function_arguments:
                                current_function_call['arguments'] = current_function_arguments
                            current_function_call = None
                            current_function_arguments = ''
                            function_name = getattr(chunk.item, 'name', 'unknown')
                            try:
                                stream_callback(f"\n🔧 Function '{function_name}' completed\n")
                            except Exception as e:
                                print(f'Stream callback error: {e}')
                elif chunk.type == 'response.web_search_call.in_progress':
                    try:
                        stream_callback('\n🔍 Search in progress...\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.web_search_call.searching':
                    try:
                        stream_callback('\n🔍 Searching...\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.web_search_call.completed':
                    try:
                        stream_callback('\n🔍 Search completed\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.output_text.annotation.added':
                    if hasattr(chunk, 'annotation'):
                        citation_data = {'url': getattr(chunk.annotation, 'url', None), 'title': getattr(chunk.annotation, 'title', None), 'start_index': getattr(chunk.annotation, 'start_index', None), 'end_index': getattr(chunk.annotation, 'end_index', None)}
                        citations.append(citation_data)
                    try:
                        stream_callback('\n📚 Citation added\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.function_call_arguments.delta':
                    if hasattr(chunk, 'delta') and chunk.delta:
                        current_function_arguments += chunk.delta
                        try:
                            stream_callback(chunk.delta)
                        except Exception as e:
                            print(f'Stream callback error: {e}')
                elif chunk.type == 'response.function_call_arguments.done':
                    if hasattr(chunk, 'arguments') and hasattr(chunk, 'item_id'):
                        for fc in function_calls:
                            if fc.get('id') == chunk.item_id:
                                fc['arguments'] = chunk.arguments
                                break
                    if current_function_call and current_function_arguments:
                        current_function_call['arguments'] = current_function_arguments
                    current_function_call = None
                    current_function_arguments = ''
                    try:
                        stream_callback('\n🔧 Function arguments complete\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
                elif chunk.type == 'response.completed':
                    try:
                        stream_callback('\n✅ Response complete\n')
                    except Exception as e:
                        print(f'Stream callback error: {e}')
        result = AgentResponse(text=text, code=code, citations=citations, function_calls=function_calls)
    else:
        result = parse_completion(completion, add_citations=True)
    return result

def test_configuration_files():
    """Test that configuration files are valid."""
    print('🧪 Testing configuration files...')
    import yaml
    config_files = ['massgen/configs/claude_code_cli.yaml', 'massgen/configs/cli_backends_mixed.yaml']
    for config_file in config_files:
        if Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                assert config is not None, f'Config {config_file} should not be empty'
                print(f'✅ {config_file} is valid')
            except Exception as e:
                print(f'❌ {config_file} is invalid: {e}')
                raise
        else:
            print(f'⚠️  {config_file} not found, skipping')

@mcp.tool()
def get_birthdays() -> str:
    """Get this week's birthdays"""
    return "Mom's birthday tomorrow, Sis's birthday Friday"

@mcp.tool()
def server_status() -> str:
    """Server health check"""
    return f'✅ Healthy - {datetime.now().strftime('%H:%M:%S')}'

def test_orchestrator_initialization_with_context_sharing(test_workspace, mock_agents):
    """Test orchestrator initializes with context sharing parameters."""
    orchestrator = Orchestrator(agents=mock_agents, snapshot_storage=test_workspace['snapshot_storage'], agent_temporary_workspace=test_workspace['temp_workspace'])
    assert orchestrator._snapshot_storage == test_workspace['snapshot_storage']
    assert orchestrator._agent_temporary_workspace == test_workspace['temp_workspace']
    assert len(orchestrator._agent_id_mapping) == 3
    assert 'claude_code_1' in orchestrator._agent_id_mapping
    assert 'claude_code_2' in orchestrator._agent_id_mapping
    assert 'claude_code_3' in orchestrator._agent_id_mapping
    assert orchestrator._agent_id_mapping['claude_code_1'] == 'agent_1'
    assert orchestrator._agent_id_mapping['claude_code_2'] == 'agent_2'
    assert orchestrator._agent_id_mapping['claude_code_3'] == 'agent_3'
    assert Path(test_workspace['snapshot_storage']).exists()
    assert Path(test_workspace['temp_workspace']).exists()
    for agent_id in mock_agents.keys():
        snapshot_dir = Path(test_workspace['snapshot_storage']) / agent_id
        temp_dir = Path(test_workspace['temp_workspace']) / agent_id
        assert snapshot_dir.exists()
        assert temp_dir.exists()

def get_group_initial_message() -> Dict[str, Any] | None:
    """
    Create the initial system message for group chat.

    Returns:
        Dict with role and content for initial system message
    """
    initial_message = f'\n    CURRENT ANSWER from multiple agents for final response to a message is given.\n    Different agents may have different builtin tools and capabilities.\n    Does the best CURRENT ANSWER address the ORIGINAL MESSAGE well?\n\n    If CURRENT ANSWER is given, digest existing answers, combine their strengths, and do additional work to address their weaknesses.\n    if you think CURRENT ANSWER is good enough, you can also use it as your answer.\n\n    *Note*: The CURRENT TIME is **{time.strftime('%Y-%m-%d %H:%M:%S')}**.\n    '
    return {'role': 'system', 'content': initial_message}

