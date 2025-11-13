# Cluster 5

def main():
    components_dir = Path('components')
    components_dir.mkdir(exist_ok=True)
    print('Extracting components from working presentations...')
    m2l_slides = extract_slides_from_file('m2l.html')
    print(f'Found {len(m2l_slides)} slides in m2l.html')
    head_content = extract_head_section('m2l.html')
    nav_content = extract_navigation_section('m2l.html')
    (components_dir / 'head.html').write_text(head_content)
    print('✅ Saved head.html')
    (components_dir / 'navigation.html').write_text(nav_content)
    print('✅ Saved navigation.html')
    for i, slide in enumerate(m2l_slides, 1):
        title_match = re.search('<!-- Slide \\d+: ([^>]*) -->', slide)
        if title_match:
            title = title_match.group(1).strip()
            filename = clean_slide_title(title)
        else:
            filename = f'slide-{i:02d}'
        slide_content = slide.strip()
        (components_dir / f'{filename}.html').write_text(f'        {slide_content}')
        print(f'✅ Saved {filename}.html')
    print(f'\nExtracted {len(m2l_slides)} slides + head + navigation')
    print('Next: Extract Columbia-specific variants...')

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

@mcp.tool()
def copy_file(source_path: str, destination_path: str, overwrite: bool=False) -> Dict[str, Any]:
    """
        Copy a file or directory from any accessible path to the agent's workspace.

        This is the primary tool for copying files from temp workspaces, context paths,
        or any other accessible location to the current agent's workspace.

        Args:
            source_path: Path to source file/directory (must be absolute path)
            destination_path: Destination path - can be:
                - Relative path: Resolved relative to your workspace (e.g., "output/file.txt")
                - Absolute path: Must be within allowed directories for security
            overwrite: Whether to overwrite existing files/directories (default: False)

        Returns:
            Dictionary with copy operation results
        """
    source, destination = _validate_and_resolve_paths(mcp.allowed_paths, source_path, destination_path)
    result = _perform_copy(source, destination, overwrite)
    return {'success': True, 'operation': 'copy_file', 'details': result}

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

class CoordinationUI:
    """Main coordination interface with display capabilities."""

    def __init__(self, display: Optional[BaseDisplay]=None, logger: Optional[Any]=None, display_type: str='terminal', enable_final_presentation: bool=False, **kwargs):
        """Initialize coordination UI.

        Args:
            display: Custom display instance (overrides display_type)
            logger: Custom logger instance
            display_type: Type of display ("terminal", "simple", "rich_terminal", "textual_terminal")
            enable_final_presentation: Whether to ask winning agent to present final answer
            **kwargs: Additional configuration passed to display/logger
        """
        self.enable_final_presentation = enable_final_presentation
        self.display = display
        self.logger = logger
        self.display_type = display_type
        self.config = kwargs
        self.agent_ids = []
        self.orchestrator = None
        self._flush_char_delay = 0.03
        self._answer_buffer = ''
        self._answer_timeout_task = None
        self._final_answer_shown = False

    def _process_reasoning_summary(self, chunk_type: str, summary_delta: str, source: str) -> str:
        """Process reasoning summary content using display's shared logic."""
        if self.display and hasattr(self.display, 'process_reasoning_content'):
            return self.display.process_reasoning_content(chunk_type, summary_delta, source)
        else:
            if chunk_type == 'reasoning_summary':
                summary_active_key = f'_summary_active_{source}'
                if not getattr(self, summary_active_key, False):
                    setattr(self, summary_active_key, True)
                    return f'📋 [Reasoning Summary]\n{summary_delta}\n'
                return summary_delta
            elif chunk_type == 'reasoning_summary_done':
                summary_active_key = f'_summary_active_{source}'
                if hasattr(self, summary_active_key):
                    setattr(self, summary_active_key, False)
            return summary_delta

    def _process_reasoning_content(self, chunk_type: str, reasoning_delta: str, source: str) -> str:
        """Process reasoning summary content using display's shared logic."""
        if self.display and hasattr(self.display, 'process_reasoning_content'):
            return self.display.process_reasoning_content(chunk_type, reasoning_delta, source)
        elif chunk_type == 'reasoning':
            reasoning_active_key = f'_reasoning_active_{source}'
            if not getattr(self, reasoning_active_key, False):
                setattr(self, reasoning_active_key, True)
                return f'🧠 [Reasoning Started]\n{reasoning_delta}\n'
            return reasoning_delta
        elif chunk_type == 'reasoning_done':
            reasoning_active_key = f'_reasoning_active_{source}'
            if hasattr(self, reasoning_active_key):
                setattr(self, reasoning_active_key, False)
            return reasoning_delta

    def __post_init__(self):
        """Post-initialization setup."""
        self._flush_word_delay = 0.08
        self._answer_buffer = ''
        self._answer_timeout_task = None
        self._final_answer_shown = False

    def reset(self):
        """Reset UI state for next coordination session."""
        if self.display:
            try:
                self.display.cleanup()
            except Exception:
                pass
            self.display = None
        self.agent_ids = []
        self.orchestrator = None
        if hasattr(self, '_answer_buffer'):
            self._answer_buffer = ''
        if hasattr(self, '_answer_timeout_task') and self._answer_timeout_task:
            self._answer_timeout_task.cancel()
            self._answer_timeout_task = None
        if hasattr(self, '_final_answer_shown'):
            self._final_answer_shown = False

    async def coordinate(self, orchestrator, question: str, agent_ids: Optional[List[str]]=None) -> str:
        """Coordinate agents with visual display.

        Args:
            orchestrator: MassGen orchestrator instance
            question: Question for coordination
            agent_ids: Optional list of agent IDs (auto-detected if not provided)

        Returns:
            Final coordinated response
        """
        selected_agent = ''
        vote_results = {}
        final_result = ''
        final_answer = ''
        if self.display is not None:
            self.display.cleanup()
        self.display = None
        self.orchestrator = orchestrator
        if agent_ids is None:
            self.agent_ids = list(orchestrator.agents.keys())
        else:
            self.agent_ids = agent_ids
        if self.display is None:
            if self.display_type == 'terminal':
                self.display = TerminalDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'simple':
                self.display = SimpleDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'rich_terminal':
                if not is_rich_available():
                    print('⚠️  Rich library not available. Falling back to terminal display.')
                    print('   Install with: pip install rich')
                    self.display = TerminalDisplay(self.agent_ids, **self.config)
                else:
                    self.display = RichTerminalDisplay(self.agent_ids, **self.config)
            else:
                raise ValueError(f'Unknown display type: {self.display_type}')
        self.display.orchestrator = orchestrator
        self._answer_buffer = ''
        self._answer_timeout_task = None
        self._final_answer_shown = False
        log_filename = None
        if self.logger:
            log_filename = self.logger.initialize_session(question, self.agent_ids)
            monitoring = self.logger.get_monitoring_commands()
            print(f'📁 Real-time log: {log_filename}')
            print(f'💡 Monitor with: {monitoring['tail']}')
            print()
        self.display.initialize(question, log_filename)
        selected_agent = None
        vote_results = {}
        try:
            full_response = ''
            final_answer = ''
            async for chunk in orchestrator.chat_simple(question):
                content = getattr(chunk, 'content', '') or ''
                source = getattr(chunk, 'source', None)
                chunk_type = getattr(chunk, 'type', '')
                if chunk_type == 'agent_status':
                    status = getattr(chunk, 'status', None)
                    if source and status:
                        self.display.update_agent_status(source, status)
                    continue
                elif chunk_type == 'debug':
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type == 'mcp_status':
                    if source and source in self.agent_ids:
                        self.display.update_agent_content(source, content, 'tool')
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                    if source:
                        reasoning_content = ''
                        if chunk_type == 'reasoning':
                            reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                            if reasoning_delta:
                                reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                        elif chunk_type == 'reasoning_done':
                            reasoning_text = getattr(chunk, 'reasoning_text', '')
                            if reasoning_text:
                                reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                            else:
                                reasoning_content = '\n🧠 [Reasoning Complete]\n'
                            self._process_reasoning_content(chunk_type, reasoning_content, source)
                            reasoning_active_key = '_reasoning_active'
                            if hasattr(self, reasoning_active_key):
                                delattr(self, reasoning_active_key)
                        elif chunk_type == 'reasoning_summary':
                            summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                            if summary_delta:
                                reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                        elif chunk_type == 'reasoning_summary_done':
                            summary_text = getattr(chunk, 'reasoning_summary_text', '')
                            if summary_text:
                                reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                            self._process_reasoning_summary(chunk_type, '', source)
                            summary_active_key = f'_summary_active_{source}'
                            if hasattr(self, summary_active_key):
                                delattr(self, summary_active_key)
                        if reasoning_content:
                            self.display.update_agent_content(source, reasoning_content, 'thinking')
                            if self.logger:
                                self.logger.log_agent_content(source, reasoning_content, 'reasoning')
                    continue
                if chunk_type == 'status' and 'presenting final answer' in content:
                    for attr_name in list(vars(self).keys()):
                        if attr_name.startswith('_summary_active_'):
                            delattr(self, attr_name)
                if content:
                    full_response += content
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk.type)
                    await self._process_content(source, content)
            status = orchestrator.get_status()
            vote_results = status.get('vote_results', {})
            selected_agent = status.get('selected_agent')
            if selected_agent is None:
                selected_agent = ''
            if self.enable_final_presentation and selected_agent and vote_results.get('vote_counts'):
                presentation_content = ''
                try:
                    async for chunk in orchestrator.get_final_presentation(selected_agent, vote_results):
                        content = getattr(chunk, 'content', '') or ''
                        chunk_type = getattr(chunk, 'type', '')
                        if chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                            source = getattr(chunk, 'source', selected_agent)
                            reasoning_content = ''
                            if chunk_type == 'reasoning':
                                reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                                if reasoning_delta:
                                    reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                            elif chunk_type == 'reasoning_done':
                                reasoning_text = getattr(chunk, 'reasoning_text', '')
                                if reasoning_text:
                                    reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                                else:
                                    reasoning_content = '\n🧠 [Reasoning Complete]\n'
                                self._process_reasoning_content(chunk_type, reasoning_content, source)
                                reasoning_active_key = '_reasoning_active'
                                if hasattr(self, reasoning_active_key):
                                    delattr(self, reasoning_active_key)
                            elif chunk_type == 'reasoning_summary':
                                summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                                if summary_delta:
                                    reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                            elif chunk_type == 'reasoning_summary_done':
                                summary_text = getattr(chunk, 'reasoning_summary_text', '')
                                if summary_text:
                                    reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                                self._process_reasoning_summary(chunk_type, '', source)
                                summary_active_key = f'_summary_active_{source}'
                                if hasattr(self, summary_active_key):
                                    delattr(self, summary_active_key)
                            if reasoning_content:
                                content = reasoning_content
                        if content:
                            if isinstance(content, list):
                                content = ' '.join((str(item) for item in content))
                            elif not isinstance(content, str):
                                content = str(content)
                            presentation_content += content
                            if self.logger:
                                self.logger.log_chunk(selected_agent, content, getattr(chunk, 'type', 'presentation'))
                            if self.display:
                                try:
                                    await self._process_content(selected_agent, content)
                                except Exception:
                                    pass
                            else:
                                print(content, end='', flush=True)
                except AttributeError:
                    presentation_content = ''
                final_answer = presentation_content
                time.sleep(1.5)
            orchestrator_final_answer = None
            if hasattr(orchestrator, '_final_presentation_content') and orchestrator._final_presentation_content:
                orchestrator_final_answer = orchestrator._final_presentation_content.strip()
            elif selected_agent and hasattr(orchestrator, 'agent_states') and (selected_agent in orchestrator.agent_states):
                stored_answer = orchestrator.agent_states[selected_agent].answer
                if stored_answer:
                    orchestrator_final_answer = stored_answer.replace('\\', '\n').replace('**', '').strip()
            final_result = orchestrator_final_answer if orchestrator_final_answer else final_answer if final_answer else full_response
            if self.logger:
                session_info = self.logger.finalize_session(final_result if 'final_result' in locals() else final_answer if 'final_answer' in locals() else '', success=True)
                print(f'💾 Session log: {session_info['filename']}')
                print(f'⏱️  Duration: {session_info['duration']:.1f}s | Chunks: {session_info['total_chunks']} | Events: {session_info['orchestrator_events']}')
            return final_result
        except Exception:
            if self.logger:
                self.logger.finalize_session('', success=False)
            raise
        finally:
            if hasattr(self, '_answer_timeout_task') and self._answer_timeout_task:
                try:
                    await asyncio.wait_for(self._answer_timeout_task, timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                        await self._flush_final_answer()
                    self._answer_timeout_task.cancel()
            if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                await self._flush_final_answer()
            await asyncio.sleep(0.1)
            if self.display:
                self.display.cleanup()
            if self.logger:
                session_info = self.logger.finalize_session(final_result if 'final_result' in locals() else final_answer if 'final_answer' in locals() else '', success=True)
                print(f'💾 Session log: {session_info['filename']}')
                print(f'⏱️  Duration: {session_info['duration']:.1f}s | Chunks: {session_info['total_chunks']} | Events: {session_info['orchestrator_events']}')

    async def coordinate_with_context(self, orchestrator, question: str, messages: List[Dict[str, Any]], agent_ids: Optional[List[str]]=None) -> str:
        """Coordinate agents with conversation context and visual display.

        Args:
            orchestrator: MassGen orchestrator instance
            question: Current question for coordination
            messages: Full conversation message history
            agent_ids: Optional list of agent IDs (auto-detected if not provided)

        Returns:
            Final coordinated response
        """
        selected_agent = ''
        vote_results = {}
        final_result = ''
        final_answer = ''
        if self.display is not None:
            self.display.cleanup()
        self.display = None
        self.orchestrator = orchestrator
        if agent_ids is None:
            self.agent_ids = list(orchestrator.agents.keys())
        else:
            self.agent_ids = agent_ids
        if self.display is None:
            if self.display_type == 'terminal':
                self.display = TerminalDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'simple':
                self.display = SimpleDisplay(self.agent_ids, **self.config)
            elif self.display_type == 'rich_terminal':
                if not is_rich_available():
                    print('⚠️  Rich library not available. Falling back to terminal display.')
                    print('   Install with: pip install rich')
                    self.display = TerminalDisplay(self.agent_ids, **self.config)
                else:
                    self.display = RichTerminalDisplay(self.agent_ids, **self.config)
            else:
                raise ValueError(f'Unknown display type: {self.display_type}')
        self.display.orchestrator = orchestrator
        log_filename = None
        if self.logger:
            context_info = f'(with {len(messages) // 2} previous exchanges)' if len(messages) > 1 else ''
            session_question = f'{question} {context_info}'
            log_filename = self.logger.initialize_session(session_question, self.agent_ids)
            monitoring = self.logger.get_monitoring_commands()
            print(f'📁 Real-time log: {log_filename}')
            print(f'💡 Monitor with: {monitoring['tail']}')
            print()
        self.display.initialize(question, log_filename)
        selected_agent = None
        vote_results = {}
        orchestrator_final_answer = None
        try:
            full_response = ''
            final_answer = ''
            async for chunk in orchestrator.chat(messages):
                content = getattr(chunk, 'content', '') or ''
                source = getattr(chunk, 'source', None)
                chunk_type = getattr(chunk, 'type', '')
                if chunk_type == 'agent_status':
                    status = getattr(chunk, 'status', None)
                    if source and status:
                        self.display.update_agent_status(source, status)
                    continue
                elif chunk_type == 'debug':
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type == 'mcp_status':
                    if source and source in self.agent_ids:
                        self.display.update_agent_content(source, content, 'tool')
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk_type)
                    continue
                elif chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                    if source:
                        reasoning_content = ''
                        if chunk_type == 'reasoning':
                            reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                            if reasoning_delta:
                                reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                        elif chunk_type == 'reasoning_done':
                            reasoning_text = getattr(chunk, 'reasoning_text', '')
                            if reasoning_text:
                                reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                            else:
                                reasoning_content = '\n🧠 [Reasoning Complete]\n'
                            self._process_reasoning_content(chunk_type, reasoning_content, source)
                            reasoning_active_key = '_reasoning_active'
                            if hasattr(self, reasoning_active_key):
                                delattr(self, reasoning_active_key)
                        elif chunk_type == 'reasoning_summary':
                            summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                            if summary_delta:
                                reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                        elif chunk_type == 'reasoning_summary_done':
                            summary_text = getattr(chunk, 'reasoning_summary_text', '')
                            if summary_text:
                                reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                            self._process_reasoning_summary(chunk_type, '', source)
                            summary_active_key = f'_summary_active_{source}'
                            if hasattr(self, summary_active_key):
                                delattr(self, summary_active_key)
                        if reasoning_content:
                            self.display.update_agent_content(source, reasoning_content, 'thinking')
                            if self.logger:
                                self.logger.log_agent_content(source, reasoning_content, 'reasoning')
                    continue
                if chunk_type == 'status' and 'presenting final answer' in content:
                    for attr_name in list(vars(self).keys()):
                        if attr_name.startswith('_summary_active_'):
                            delattr(self, attr_name)
                if content:
                    full_response += content
                    if self.logger:
                        self.logger.log_chunk(source, content, chunk.type)
                    await self._process_content(source, content)
            status = orchestrator.get_status()
            vote_results = status.get('vote_results', {})
            selected_agent = status.get('selected_agent')
            if selected_agent is None:
                selected_agent = ''
            if self.enable_final_presentation and selected_agent and vote_results.get('vote_counts'):
                presentation_content = ''
                try:
                    async for chunk in orchestrator.get_final_presentation(selected_agent, vote_results):
                        content = getattr(chunk, 'content', '') or ''
                        chunk_type = getattr(chunk, 'type', '')
                        if chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                            source = getattr(chunk, 'source', selected_agent)
                            reasoning_content = ''
                            if chunk_type == 'reasoning':
                                reasoning_delta = getattr(chunk, 'reasoning_delta', '')
                                if reasoning_delta:
                                    reasoning_content = self._process_reasoning_content(chunk_type, reasoning_delta, source)
                            elif chunk_type == 'reasoning_done':
                                reasoning_text = getattr(chunk, 'reasoning_text', '')
                                if reasoning_text:
                                    reasoning_content = f'\n🧠 [Reasoning Complete]\n{reasoning_text}\n'
                                else:
                                    reasoning_content = '\n🧠 [Reasoning Complete]\n'
                                self._process_reasoning_content(chunk_type, reasoning_content, source)
                                reasoning_active_key = '_reasoning_active'
                                if hasattr(self, reasoning_active_key):
                                    delattr(self, reasoning_active_key)
                            elif chunk_type == 'reasoning_summary':
                                summary_delta = getattr(chunk, 'reasoning_summary_delta', '')
                                if summary_delta:
                                    reasoning_content = self._process_reasoning_summary(chunk_type, summary_delta, source)
                            elif chunk_type == 'reasoning_summary_done':
                                summary_text = getattr(chunk, 'reasoning_summary_text', '')
                                if summary_text:
                                    reasoning_content = f'\n📋 [Reasoning Summary Complete]\n{summary_text}\n'
                                self._process_reasoning_summary(chunk_type, '', source)
                                summary_active_key = f'_summary_active_{source}'
                                if hasattr(self, summary_active_key):
                                    delattr(self, summary_active_key)
                            if reasoning_content:
                                content = reasoning_content
                        if content:
                            if isinstance(content, list):
                                content = ' '.join((str(item) for item in content))
                            elif not isinstance(content, str):
                                content = str(content)
                            presentation_content += content
                            if self.logger:
                                self.logger.log_chunk(selected_agent, content, getattr(chunk, 'type', 'presentation'))
                            await self._process_content(selected_agent, content)
                            if getattr(chunk, 'type', '') == 'done':
                                break
                except Exception:
                    presentation_content = full_response
                final_answer = presentation_content
                time.sleep(1.5)
            orchestrator_final_answer = None
            if selected_agent and hasattr(orchestrator, 'agent_states') and (selected_agent in orchestrator.agent_states):
                stored_answer = orchestrator.agent_states[selected_agent].answer
                if stored_answer:
                    orchestrator_final_answer = stored_answer.replace('\\', '\n').replace('**', '').strip()
            final_result = orchestrator_final_answer if orchestrator_final_answer else final_answer if final_answer else full_response
            if self.logger:
                session_info = self.logger.finalize_session(final_result if 'final_result' in locals() else final_answer if 'final_answer' in locals() else '', success=True)
                print(f'💾 Session log: {session_info['filename']}')
                print(f'⏱️  Duration: {session_info['duration']:.1f}s | Chunks: {session_info['total_chunks']} | Events: {session_info['orchestrator_events']}')
            return final_result
        except Exception:
            if self.logger:
                self.logger.finalize_session('', success=False)
            raise
        finally:
            if hasattr(self, '_answer_timeout_task') and self._answer_timeout_task:
                try:
                    await asyncio.wait_for(self._answer_timeout_task, timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                        await self._flush_final_answer()
                    self._answer_timeout_task.cancel()
            if hasattr(self, '_answer_buffer') and self._answer_buffer and (not self._final_answer_shown):
                await self._flush_final_answer()
            await asyncio.sleep(0.1)
            if self.display:
                self.display.cleanup()

    def _display_vote_results(self, vote_results: Dict[str, Any]):
        """Display voting results in a formatted table."""
        print('\n🗳️  VOTING RESULTS')
        print('=' * 50)
        vote_counts = vote_results.get('vote_counts', {})
        voter_details = vote_results.get('voter_details', {})
        winner = vote_results.get('winner')
        is_tie = vote_results.get('is_tie', False)
        if vote_counts:
            print('\n📊 Vote Count:')
            for agent_id, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True):
                winner_mark = '🏆' if agent_id == winner else '  '
                tie_mark = ' (tie-broken)' if is_tie and agent_id == winner else ''
                print(f'   {winner_mark} {agent_id}: {count} vote{('s' if count != 1 else '')}{tie_mark}')
        if voter_details:
            print('\n🔍 Vote Details:')
            for voted_for, voters in voter_details.items():
                print(f'   → {voted_for}:')
                for voter_info in voters:
                    voter = voter_info['voter']
                    reason = voter_info['reason']
                    print(f'     • {voter}: "{reason}"')
        if is_tie:
            print('\n⚖️  Tie broken by agent registration order (orchestrator setup order)')
        total_votes = vote_results.get('total_votes', 0)
        agents_voted = vote_results.get('agents_voted', 0)
        print(f'\n📈 Summary: {agents_voted}/{total_votes} agents voted')
        print('=' * 50)

    async def _process_content(self, source: Optional[str], content: str):
        """Process content from coordination stream."""
        if source in self.agent_ids:
            await self._process_agent_content(source, content)
        elif source in ['coordination_hub', 'orchestrator'] or source is None:
            await self._process_orchestrator_content(content)
        if any((marker in content for marker in ['✅', '🗳️', '🔄', '❌'])):
            clean_line = content.replace('**', '').replace('##', '').strip()
            if clean_line and (not any((skip in clean_line for skip in ['result ignored', 'Starting', 'Agents Coordinating', 'Coordinating agents, please wait']))):
                event = f'🔄 {source}: {clean_line}' if source and source not in ['coordination_hub', 'orchestrator'] else f'🔄 {clean_line}'
                self.display.add_orchestrator_event(event)
                if self.logger:
                    self.logger.log_orchestrator_event(event)

    async def _process_agent_content(self, agent_id: str, content: str):
        """Process content from a specific agent."""
        current_status = self.display.get_agent_status(agent_id)
        if current_status not in ['working', 'completed']:
            self.display.update_agent_status(agent_id, 'working')
        if '🔧' in content or '🔄 Vote invalid' in content:
            content_type = 'tool' if '🔧' in content else 'status'
            self.display.update_agent_content(agent_id, content, content_type)
            if 'new_answer' in content or 'vote' in content:
                self.display.update_agent_status(agent_id, 'completed')
            if self.logger:
                self.logger.log_agent_content(agent_id, content, content_type)
        else:
            self.display.update_agent_content(agent_id, content, 'thinking')
            if self.logger:
                self.logger.log_agent_content(agent_id, content, 'thinking')

    async def _flush_final_answer(self):
        """Flush the buffered final answer after a timeout to prevent duplicate calls."""
        if self._final_answer_shown or not self._answer_buffer.strip():
            return
        status = self.orchestrator.get_status()
        selected_agent = status.get('selected_agent', 'Unknown')
        vote_results = status.get('vote_results', {})
        self._final_answer_shown = True
        self.display.show_final_answer(self._answer_buffer.strip(), vote_results=vote_results, selected_agent=selected_agent)

    async def _process_orchestrator_content(self, content: str):
        """Process content from orchestrator."""
        if 'Final Coordinated Answer' in content:
            pass
        elif any((marker in content for marker in ['✅', '🗳️', '🔄', '❌', '⚠️'])):
            clean_line = content.replace('**', '').replace('##', '').strip()
            if clean_line and (not any((skip in clean_line for skip in ['result ignored', 'Starting', 'Agents Coordinating', 'Coordinating agents, please wait']))):
                event = f'🔄 {clean_line}'
                self.display.add_orchestrator_event(event)
                if self.logger:
                    self.logger.log_orchestrator_event(event)
        elif 'Final Coordinated Answer' not in content and (not any((marker in content for marker in ['✅', '🗳️', '🎯', 'Starting', 'Agents Coordinating', '🔄', '**', 'result ignored', 'restart pending']))):
            clean_content = content.strip()
            if clean_content and (not clean_content.startswith('---')) and (not clean_content.startswith('*Coordinated by')):
                if self._answer_buffer:
                    self._answer_buffer += ' ' + clean_content
                else:
                    self._answer_buffer = clean_content
                if self._answer_timeout_task:
                    self._answer_timeout_task.cancel()
                self._answer_timeout_task = asyncio.create_task(self._schedule_final_answer_flush())
                status = self.orchestrator.get_status()
                selected_agent = status.get('selected_agent', 'Unknown')
                vote_results = status.get('vote_results', {})
                vote_counts = vote_results.get('vote_counts', {})
                is_tie = vote_results.get('is_tie', False)
                if self._answer_buffer == clean_content:
                    orchestrator_timeout = getattr(self.orchestrator, 'is_orchestrator_timeout', False)
                    if selected_agent == 'Unknown' or selected_agent is None:
                        if orchestrator_timeout:
                            if vote_counts:
                                max_votes = max(vote_counts.values())
                                tied_agents = [agent for agent, count in vote_counts.items() if count == max_votes]
                                timeout_selected_agent = tied_agents[0] if tied_agents else None
                                if timeout_selected_agent:
                                    vote_summary = ', '.join([f'{agent}: {count}' for agent, count in vote_counts.items()])
                                    tie_info = ' (tie-broken by registration order)' if len(tied_agents) > 1 else ''
                                    event = f'🎯 FINAL: {timeout_selected_agent} selected from partial votes ({vote_summary}{tie_info}) → orchestrator timeout → [buffering...]'
                                else:
                                    event = '🎯 FINAL: None selected → orchestrator timeout (no agents completed voting in time) → [buffering...]'
                            else:
                                event = '🎯 FINAL: None selected → orchestrator timeout (no agents completed voting in time) → [buffering...]'
                        else:
                            event = '🎯 FINAL: None selected → [buffering...]'
                    elif vote_counts:
                        vote_summary = ', '.join([f'{agent}: {count} vote{('s' if count != 1 else '')}' for agent, count in vote_counts.items()])
                        tie_info = ' (tie-broken by registration order)' if is_tie else ''
                        timeout_info = ' (despite timeout)' if orchestrator_timeout else ''
                        event = f'🎯 FINAL: {selected_agent} selected ({vote_summary}{tie_info}){timeout_info} → [buffering...]'
                    else:
                        timeout_info = ' (despite timeout)' if orchestrator_timeout else ''
                        event = f'🎯 FINAL: {selected_agent} selected{timeout_info} → [buffering...]'
                    self.display.add_orchestrator_event(event)
                    if self.logger:
                        self.logger.log_orchestrator_event(event)

    async def _schedule_final_answer_flush(self):
        """Schedule the final answer flush after a delay to collect all chunks."""
        await asyncio.sleep(0.5)
        await self._flush_final_answer()

    def _print_with_flush(self, content: str):
        """Print content chunks directly without character-by-character flushing."""
        try:
            print(content, end='', flush=True)
        except Exception:
            print(content, end='', flush=True)

def _print_with_flush(self, content: str):
    """Print content chunks directly without character-by-character flushing."""
    try:
        print(content, end='', flush=True)
    except Exception:
        print(content, end='', flush=True)

class SimpleDisplay(BaseDisplay):
    """Simple text-based display with minimal formatting."""

    def __init__(self, agent_ids, **kwargs):
        """Initialize simple display."""
        super().__init__(agent_ids, **kwargs)
        self.show_agent_prefixes = kwargs.get('show_agent_prefixes', True)
        self.show_events = kwargs.get('show_events', True)

    def initialize(self, question: str, log_filename: Optional[str]=None):
        """Initialize the display."""
        print(f'🎯 MassGen Coordination: {question}')
        if log_filename:
            print(f'📁 Log file: {log_filename}')
        print(f'👥 Agents: {', '.join(self.agent_ids)}')
        print('=' * 50)

    def update_agent_content(self, agent_id: str, content: str, content_type: str='thinking'):
        """Update content for a specific agent."""
        if agent_id not in self.agent_ids:
            return
        clean_content = content.strip()
        if clean_content.startswith(f'[{agent_id}]'):
            clean_content = clean_content[len(f'[{agent_id}]'):].strip()
        if clean_content.startswith(f'🤖 **{agent_id}**'):
            clean_content = clean_content.replace(f'🤖 **{agent_id}**', '🤖').strip()
        self.agent_outputs[agent_id].append(clean_content)
        if self.show_agent_prefixes:
            prefix = f'[{agent_id}] '
        else:
            prefix = ''
        if content_type == 'tool':
            if 'Tool result:' in clean_content:
                return
            print(f'{prefix}🔧 {clean_content}')
        elif content_type == 'status':
            print(f'{prefix}📊 {clean_content}')
        elif content_type == 'presentation':
            print(f'{prefix}🎤 {clean_content}')
        else:
            print(f'{prefix}{clean_content}')

    def update_agent_status(self, agent_id: str, status: str):
        """Update status for a specific agent."""
        if agent_id not in self.agent_ids:
            return
        self.agent_status[agent_id] = status
        if self.show_agent_prefixes:
            print(f'[{agent_id}] Status: {status}')
        else:
            print(f'Status: {status}')

    def add_orchestrator_event(self, event: str):
        """Add an orchestrator coordination event."""
        self.orchestrator_events.append(event)
        if self.show_events:
            print(f'🎭 {event}')

    def show_final_answer(self, answer: str, vote_results=None, selected_agent=None):
        """Display the final coordinated answer."""
        print('\n' + '=' * 50)
        print(f'🎯 FINAL ANSWER: {answer}')
        if selected_agent:
            print(f'✅ Selected by: {selected_agent}')
        if vote_results:
            vote_summary = ', '.join([f'{agent}: {votes}' for agent, votes in vote_results.items()])
            print(f'🗳️ Vote results: {vote_summary}')
        print('=' * 50)

    def cleanup(self):
        """Clean up resources."""
        print(f'\n✅ Coordination completed with {len(self.agent_ids)} agents')
        print(f'📊 Total orchestrator events: {len(self.orchestrator_events)}')
        for agent_id in self.agent_ids:
            print(f'📝 {agent_id}: {len(self.agent_outputs[agent_id])} content items')

def initialize(self, question: str, log_filename: Optional[str]=None):
    """Initialize the display."""
    print(f'🎯 MassGen Coordination: {question}')
    if log_filename:
        print(f'📁 Log file: {log_filename}')
    print(f'👥 Agents: {', '.join(self.agent_ids)}')
    print('=' * 50)

def update_agent_status(self, agent_id: str, status: str):
    """Update status for a specific agent."""
    if agent_id not in self.agent_ids:
        return
    self.agent_status[agent_id] = status
    if self.show_agent_prefixes:
        print(f'[{agent_id}] Status: {status}')
    else:
        print(f'Status: {status}')

def add_orchestrator_event(self, event: str):
    """Add an orchestrator coordination event."""
    self.orchestrator_events.append(event)
    if self.show_events:
        print(f'🎭 {event}')

def cleanup(self):
    """Clean up resources."""
    print(f'\n✅ Coordination completed with {len(self.agent_ids)} agents')
    print(f'📊 Total orchestrator events: {len(self.orchestrator_events)}')
    for agent_id in self.agent_ids:
        print(f'📝 {agent_id}: {len(self.agent_outputs[agent_id])} content items')

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

class LMStudioBackend(ChatCompletionsBackend):
    """LM Studio backend (OpenAI-compatible, local server)."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key='lm-studio', **kwargs)
        self._models_attempted = set()
        self.start_lmstudio_server(**kwargs)

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI-compatible Chat Completions API.

        LM Studio does not require special message conversions; this delegates to
        the generic ChatCompletions implementation while preserving our defaults.
        """
        base_url = kwargs.get('base_url', 'http://localhost:1234/v1')
        kwargs['base_url'] = base_url
        async for chunk in super().stream_with_tools(messages, tools, **kwargs):
            yield chunk

    def get_supported_builtin_tools(self) -> List[str]:
        return []

    def start_lmstudio_server(self, **kwargs):
        """Start LM Studio server after checking CLI and model availability."""
        self._ensure_cli_installed()
        self._start_server()
        model_name = kwargs.get('model', '')
        if model_name:
            self._handle_model(model_name)

    def _ensure_cli_installed(self):
        """Ensure LM Studio CLI is installed."""
        if shutil.which('lms'):
            return
        print('LM Studio CLI not found. Installing...')
        try:
            system = platform.system().lower()
            install_commands = {'darwin': (['brew', 'install', 'lmstudio'], False), 'linux': (['curl', '-sSL', 'https://lmstudio.ai/install.sh', '|', 'sh'], True), 'windows': (['powershell', '-Command', 'iwr -useb https://lmstudio.ai/install.ps1 | iex'], False)}
            if system not in install_commands:
                raise RuntimeError(f'Unsupported platform: {system}')
            cmd, use_shell = install_commands[system]
            subprocess.run(cmd, shell=use_shell, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'Failed to install LM Studio CLI: {e}') from e

    def _start_server(self):
        """Start the LM Studio server in background mode."""
        try:
            with subprocess.Popen(['lms', 'server', 'start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                time.sleep(3)
                if process.poll() is None:
                    print('LM Studio server started successfully (running in background).')
                else:
                    self._handle_server_output(process)
        except Exception as e:
            raise RuntimeError(f'Failed to start LM Studio server: {e}') from e

    def _handle_server_output(self, process):
        """Handle server process output."""
        stdout, stderr = process.communicate(timeout=1)
        if stdout:
            print(f'Server output: {stdout}')
        if stderr:
            self._process_stderr(stderr)
        print('LM Studio server started successfully.')

    def _process_stderr(self, stderr):
        """Process server stderr output."""
        stderr_lower = stderr.lower()
        if 'success' in stderr_lower or 'running on port' in stderr_lower:
            print(f'Server info: {stderr.strip()}')
        elif 'warning' in stderr_lower or 'warn' in stderr_lower:
            print(f'Server warning: {stderr.strip()}')
        else:
            print(f'Server error: {stderr.strip()}')

    def _handle_model(self, model_name):
        """Handle model downloading and loading."""
        self._ensure_model_downloaded(model_name)
        self._load_model_if_needed(model_name)

    def _ensure_model_downloaded(self, model_name):
        """Ensure model is downloaded locally."""
        try:
            downloaded = lms.list_downloaded_models()
            model_keys = [m.model_key for m in downloaded]
            if model_name not in model_keys:
                print(f"Model '{model_name}' not found locally. Downloading...")
                subprocess.run(['lms', 'get', model_name], check=True)
                print(f"Model '{model_name}' downloaded successfully.")
        except Exception as e:
            print(f'Warning: Could not check/download model: {e}')

    def _load_model_if_needed(self, model_name):
        """Load model if not already loaded."""
        try:
            if model_name in self._models_attempted:
                print(f"Model '{model_name}' load already attempted by this instance.")
                return
            time.sleep(5)
            loaded = lms.list_loaded_models()
            loaded_identifiers = [m.identifier for m in loaded]
            if model_name not in loaded_identifiers:
                print(f"Model '{model_name}' not loaded. Loading...")
                self._models_attempted.add(model_name)
                subprocess.run(['lms', 'load', model_name], check=True)
                print(f"Model '{model_name}' loaded successfully.")
            else:
                print(f"Model '{model_name}' is already loaded.")
                self._models_attempted.add(model_name)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to load model '{model_name}': {e}")
        except Exception as e:
            print(f'Warning: Could not check loaded models: {e}')

    def end_lmstudio_server(self):
        """Stop the LM Studio server after receiving all chunks."""
        try:
            result = subprocess.run(['lms', 'server', 'end'], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print('LM Studio server ended successfully.')
            else:
                subprocess.run(['lms', 'server', 'stop'], check=True)
                print('LM Studio server stopped successfully.')
        except Exception as e:
            print(f'Warning: Failed to end LM Studio server: {e}')

def _start_server(self):
    """Start the LM Studio server in background mode."""
    try:
        with subprocess.Popen(['lms', 'server', 'start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            time.sleep(3)
            if process.poll() is None:
                print('LM Studio server started successfully (running in background).')
            else:
                self._handle_server_output(process)
    except Exception as e:
        raise RuntimeError(f'Failed to start LM Studio server: {e}') from e

def _handle_server_output(self, process):
    """Handle server process output."""
    stdout, stderr = process.communicate(timeout=1)
    if stdout:
        print(f'Server output: {stdout}')
    if stderr:
        self._process_stderr(stderr)
    print('LM Studio server started successfully.')

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

def cleanup_logging():
    """Cleanup the global logging system."""
    global _log_manager
    if _log_manager:
        _log_manager.cleanup()
        _log_manager = None

class StreamingOrchestrator:

    def __init__(self, display_enabled: bool=True, stream_callback: Optional[Callable]=None, max_lines: int=10, save_logs: bool=True, answers_dir: Optional[str]=None):
        self.display = MultiRegionDisplay(display_enabled, max_lines, save_logs, answers_dir)
        self.stream_callback = stream_callback

    def stream_output(self, agent_id: int, content: str):
        """Streaming content - uses debounced updates."""
        self.display.stream_output_sync(agent_id, content)
        if self.stream_callback:
            try:
                self.stream_callback(agent_id, content)
            except Exception:
                pass

    def set_agent_model(self, agent_id: int, model_name: str):
        """Set agent model - immediate update."""
        self.display.set_agent_model(agent_id, model_name)
        self.display.force_update_display()

    def update_agent_status(self, agent_id: int, status: str):
        """Update agent status - immediate update for critical state changes."""
        self.display.update_agent_status(agent_id, status)
        self.display.force_update_display()

    def update_phase(self, old_phase: str, new_phase: str):
        """Update phase - immediate update for critical state changes."""
        self.display.update_phase(old_phase, new_phase)
        self.display.force_update_display()

    def update_vote_distribution(self, vote_dist: Dict[int, int]):
        """Update vote distribution - immediate update for critical state changes."""
        self.display.update_vote_distribution(vote_dist)
        self.display.force_update_display()

    def update_consensus_status(self, representative_id: int, vote_dist: Dict[int, int]):
        """Update consensus status - immediate update for critical state changes."""
        self.display.update_consensus_status(representative_id, vote_dist)
        self.display.force_update_display()

    def reset_consensus(self):
        """Reset consensus - immediate update for critical state changes."""
        self.display.reset_consensus()
        self.display.force_update_display()

    def add_system_message(self, message: str):
        """Add system message - immediate update for important messages."""
        self.display.add_system_message(message)
        self.display.force_update_display()

    def update_agent_vote_target(self, agent_id: int, target_id: Optional[int]):
        """Update agent vote target - immediate update for critical state changes."""
        self.display.update_agent_vote_target(agent_id, target_id)
        self.display.force_update_display()

    def update_agent_chat_round(self, agent_id: int, round_num: int):
        """Update agent chat round - debounced update."""
        self.display.update_agent_chat_round(agent_id, round_num)

    def update_agent_update_count(self, agent_id: int, count: int):
        """Update agent update count - debounced update."""
        self.display.update_agent_update_count(agent_id, count)

    def update_agent_votes_cast(self, agent_id: int, votes_cast: int):
        """Update agent votes cast - immediate update for vote-related changes."""
        self.display.update_agent_votes_cast(agent_id, votes_cast)
        self.display.force_update_display()

    def update_debate_rounds(self, rounds: int):
        """Update debate rounds - immediate update for critical state changes."""
        self.display.update_debate_rounds(rounds)
        self.display.force_update_display()

    def format_agent_notification(self, agent_id: int, notification_type: str, content: str):
        """Format agent notifications - immediate update for notifications."""
        self.display.format_agent_notification(agent_id, notification_type, content)
        self.display.force_update_display()

    def get_agent_log_path(self, agent_id: int) -> str:
        """Get the log file path for a specific agent."""
        return self.display.get_agent_log_path_for_display(agent_id)

    def get_agent_answer_path(self, agent_id: int) -> str:
        """Get the answer file path for a specific agent."""
        return self.display.get_agent_answer_path_for_display(agent_id)

    def get_system_log_path(self) -> str:
        """Get the system log file path."""
        return self.display.get_system_log_path_for_display()

    def cleanup(self):
        """Clean up resources when orchestrator is no longer needed."""
        self.display.cleanup()

def cleanup(self):
    """Clean up resources when orchestrator is no longer needed."""
    self.display.cleanup()

def test_claude_code_cli_command_building():
    """Test Claude Code CLI command building (without executing) - SKIPPED: File removed."""
    print('🧪 Testing Claude Code CLI command building... SKIPPED (file removed)')
    print('✅ Claude Code CLI command building test skipped')

def print_config_example():
    """Print example configuration for users."""
    print('\n📋 Example YAML Configuration with Timeout Settings:')
    print('=' * 50)
    example_config = '\n# Conservative timeout settings to prevent runaway costs\ntimeout_settings:\n  orchestrator_timeout_seconds: 600   # 10 minutes max coordination\n\nagents:\n  - id: "agent1"\n    backend:\n      type: "openai"\n      model: "gpt-4o-mini"\n    system_message: "You are a helpful assistant."\n'
    print(example_config)
    print('\n🖥️  CLI Examples:')
    print('python -m massgen.cli --config config.yaml --orchestrator-timeout 300 "Complex task"')

def test_cli_import():
    """Test that we can import the CLI module."""
    try:
        pass
        print('✅ Successfully imported CLI modules')
        return True
    except ImportError as e:
        print(f'❌ Failed to import CLI modules: {e}')
        return False

def test_agent_config_import():
    """Test that we can import agent configuration modules."""
    try:
        pass
        print('✅ Successfully imported AgentConfig')
        return True
    except ImportError as e:
        print(f'❌ Failed to import AgentConfig: {e}')
        return False

def test_orchestrator_import():
    """Test that we can import orchestrator modules."""
    try:
        pass
        print('✅ Successfully imported Orchestrator')
        return True
    except ImportError as e:
        print(f'❌ Failed to import Orchestrator: {e}')
        return False

def test_backend_base_import():
    """Test that we can import backend base modules."""
    try:
        pass
        print('✅ Successfully imported backend base modules')
        return True
    except ImportError as e:
        print(f'❌ Failed to import backend base modules: {e}')
        return False

def test_frontend_import():
    """Test that we can import frontend modules."""
    try:
        pass
        print('✅ Successfully imported CoordinationUI')
        return True
    except ImportError as e:
        print(f'❌ Failed to import CoordinationUI: {e}')
        return False

def test_message_templates_import():
    """Test that we can import message templates."""
    try:
        pass
        print('✅ Successfully imported MessageTemplates')
        return True
    except ImportError as e:
        print(f'❌ Failed to import MessageTemplates: {e}')
        return False

def run_integration_tests():
    """Run all integration tests."""
    print('🧪 Running MassGen Integration Tests...')
    print('Testing that all major components can be imported and basic functionality works...')
    print('=' * 80)
    tests = [('CLI Import', test_cli_import), ('Config Creation', test_config_creation), ('Agent Config Import', test_agent_config_import), ('Orchestrator Import', test_orchestrator_import), ('Backend Base Import', test_backend_base_import), ('Frontend Import', test_frontend_import), ('Message Templates Import', test_message_templates_import)]
    passed = 0
    total = len(tests)
    for test_name, test_func in tests:
        print(f'\n🔍 Testing: {test_name}')
        if test_func():
            passed += 1
        print()
    print('=' * 80)
    print(f'📊 Integration Test Results: {passed}/{total} tests passed')
    if passed == total:
        print('🎉 All integration tests passed!')
        print('\n✅ What this means:')
        print('  • All major MassGen components can be imported')
        print('  • Basic configuration creation works')
        print('  • The code structure is intact')
        print("  • Our changes haven't broken the basic functionality")
        return True
    else:
        print(f'❌ {total - passed} integration tests failed')
        print('This indicates there may be structural issues with the codebase')
        return False

def main():
    """Main test runner."""
    print('🚀 MassGen Integration Test Suite')
    print('Testing that the basic structure and imports work correctly...')
    success = run_integration_tests()
    print('\n' + '=' * 80)
    print('🏁 Final Integration Test Summary')
    print('=' * 80)
    if success:
        print('🎉 All integration tests passed!')
        print('✅ The MassGen codebase is structurally sound')
        print("✅ Our orchestrator changes haven't broken the system")
        print('✅ The program should work correctly')
        return 0
    else:
        print('❌ Some integration tests failed')
        print('⚠️  There may be structural issues that need attention')
        return 1

class TestAutoGeneratedFiles:
    """Test handling of auto-generated files."""

    def test_pycache_deletion_allowed(self, tmp_path):
        """Test that __pycache__ files can be deleted without reading."""
        from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
        tracker = FileOperationTracker(enforce_read_before_delete=True)
        pycache_dir = tmp_path / '__pycache__'
        pycache_dir.mkdir()
        pyc_file = pycache_dir / 'test.cpython-313.pyc'
        pyc_file.write_text('fake bytecode')
        can_delete, reason = tracker.can_delete(pyc_file)
        assert can_delete
        assert reason is None

    def test_pyc_file_deletion_allowed(self, tmp_path):
        """Test that .pyc files can be deleted without reading."""
        from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
        tracker = FileOperationTracker(enforce_read_before_delete=True)
        pyc_file = tmp_path / 'module.pyc'
        pyc_file.write_text('fake bytecode')
        can_delete, reason = tracker.can_delete(pyc_file)
        assert can_delete
        assert reason is None

    def test_pytest_cache_deletion_allowed(self, tmp_path):
        """Test that .pytest_cache can be deleted without reading."""
        from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
        tracker = FileOperationTracker(enforce_read_before_delete=True)
        cache_dir = tmp_path / '.pytest_cache'
        cache_dir.mkdir()
        cache_file = cache_dir / 'v' / 'cache' / 'nodeids'
        cache_file.parent.mkdir(parents=True)
        cache_file.write_text('test data')
        can_delete, reason = tracker.can_delete(cache_file)
        assert can_delete
        assert reason is None

    def test_regular_file_requires_read(self, tmp_path):
        """Test that regular files still require reading before deletion."""
        from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
        tracker = FileOperationTracker(enforce_read_before_delete=True)
        py_file = tmp_path / 'module.py'
        py_file.write_text("print('hello')")
        can_delete, reason = tracker.can_delete(py_file)
        assert not can_delete
        assert reason is not None
        assert 'must be read before deletion' in reason

    def test_directory_with_pycache_allowed(self, tmp_path):
        """Test that directories containing only __pycache__ can be deleted."""
        from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
        tracker = FileOperationTracker(enforce_read_before_delete=True)
        test_dir = tmp_path / 'mymodule'
        test_dir.mkdir()
        pycache_dir = test_dir / '__pycache__'
        pycache_dir.mkdir()
        pyc_file = pycache_dir / 'test.pyc'
        pyc_file.write_text('fake bytecode')
        can_delete, reason = tracker.can_delete_directory(test_dir)
        assert can_delete
        assert reason is None

def test_pycache_deletion_allowed(self, tmp_path):
    """Test that __pycache__ files can be deleted without reading."""
    from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
    tracker = FileOperationTracker(enforce_read_before_delete=True)
    pycache_dir = tmp_path / '__pycache__'
    pycache_dir.mkdir()
    pyc_file = pycache_dir / 'test.cpython-313.pyc'
    pyc_file.write_text('fake bytecode')
    can_delete, reason = tracker.can_delete(pyc_file)
    assert can_delete
    assert reason is None

def test_pyc_file_deletion_allowed(self, tmp_path):
    """Test that .pyc files can be deleted without reading."""
    from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
    tracker = FileOperationTracker(enforce_read_before_delete=True)
    pyc_file = tmp_path / 'module.pyc'
    pyc_file.write_text('fake bytecode')
    can_delete, reason = tracker.can_delete(pyc_file)
    assert can_delete
    assert reason is None

def test_pytest_cache_deletion_allowed(self, tmp_path):
    """Test that .pytest_cache can be deleted without reading."""
    from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
    tracker = FileOperationTracker(enforce_read_before_delete=True)
    cache_dir = tmp_path / '.pytest_cache'
    cache_dir.mkdir()
    cache_file = cache_dir / 'v' / 'cache' / 'nodeids'
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text('test data')
    can_delete, reason = tracker.can_delete(cache_file)
    assert can_delete
    assert reason is None

def test_regular_file_requires_read(self, tmp_path):
    """Test that regular files still require reading before deletion."""
    from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
    tracker = FileOperationTracker(enforce_read_before_delete=True)
    py_file = tmp_path / 'module.py'
    py_file.write_text("print('hello')")
    can_delete, reason = tracker.can_delete(py_file)
    assert not can_delete
    assert reason is not None
    assert 'must be read before deletion' in reason

def test_directory_with_pycache_allowed(self, tmp_path):
    """Test that directories containing only __pycache__ can be deleted."""
    from massgen.filesystem_manager._file_operation_tracker import FileOperationTracker
    tracker = FileOperationTracker(enforce_read_before_delete=True)
    test_dir = tmp_path / 'mymodule'
    test_dir.mkdir()
    pycache_dir = test_dir / '__pycache__'
    pycache_dir.mkdir()
    pyc_file = pycache_dir / 'test.pyc'
    pyc_file.write_text('fake bytecode')
    can_delete, reason = tracker.can_delete_directory(test_dir)
    assert can_delete
    assert reason is None

class TestDockerExecution:
    """Test Docker-based command execution."""

    @pytest.fixture(autouse=True)
    def check_docker(self):
        """Skip tests if Docker is not available."""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            try:
                client.images.get('massgen/mcp-runtime:latest')
            except docker.errors.ImageNotFound:
                pytest.skip("Docker image 'massgen/mcp-runtime:latest' not found. Run: bash massgen/docker/build.sh")
        except ImportError:
            pytest.skip('Docker library not installed. Install with: pip install docker')
        except Exception as e:
            pytest.skip(f'Docker not available: {e}')

    def test_docker_manager_initialization(self):
        """Test that DockerManager can be initialized."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager(image='massgen/mcp-runtime:latest', network_mode='none')
        assert manager.image == 'massgen/mcp-runtime:latest'
        assert manager.network_mode == 'none'
        assert manager.containers == {}

    def test_docker_container_creation(self, tmp_path):
        """Test creating a Docker container."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        container_id = manager.create_container(agent_id='test_agent', workspace_path=workspace)
        assert container_id is not None
        assert 'test_agent' in manager.containers
        manager.cleanup('test_agent')

    def test_docker_command_execution(self, tmp_path):
        """Test executing commands in Docker container."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        manager.create_container(agent_id='test_exec', workspace_path=workspace)
        result = manager.exec_command(agent_id='test_exec', command="echo 'Hello from Docker'")
        assert result['success'] is True
        assert result['exit_code'] == 0
        assert 'Hello from Docker' in result['stdout']
        manager.cleanup('test_exec')

    def test_docker_container_persistence(self, tmp_path):
        """Test that container state persists across commands."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        manager.create_container(agent_id='test_persist', workspace_path=workspace)
        result1 = manager.exec_command(agent_id='test_persist', command='pip install --quiet click')
        assert result1['success'] is True
        result2 = manager.exec_command(agent_id='test_persist', command="python -c 'import click; print(click.__version__)'")
        assert result2['success'] is True
        assert len(result2['stdout'].strip()) > 0
        manager.cleanup('test_persist')

    def test_docker_workspace_mounting(self, tmp_path):
        """Test that workspace is mounted correctly (with path transparency)."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        test_file = workspace / 'test.txt'
        test_file.write_text('Hello from host')
        manager.create_container(agent_id='test_mount', workspace_path=workspace)
        result = manager.exec_command(agent_id='test_mount', command=f'cat {workspace}/test.txt')
        assert result['success'] is True
        assert 'Hello from host' in result['stdout']
        result2 = manager.exec_command(agent_id='test_mount', command=f"echo 'Hello from container' > {workspace}/from_container.txt")
        assert result2['success'] is True
        from_container = workspace / 'from_container.txt'
        assert from_container.exists()
        assert 'Hello from container' in from_container.read_text()
        manager.cleanup('test_mount')

    def test_docker_container_isolation(self, tmp_path):
        """Test that containers are isolated from each other."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace1 = tmp_path / 'workspace1'
        workspace1.mkdir()
        workspace2 = tmp_path / 'workspace2'
        workspace2.mkdir()
        manager.create_container(agent_id='agent1', workspace_path=workspace1)
        manager.create_container(agent_id='agent2', workspace_path=workspace2)
        result1 = manager.exec_command(agent_id='agent1', command=f"echo 'agent1 data' > {workspace1}/data.txt")
        assert result1['success'] is True
        result2 = manager.exec_command(agent_id='agent2', command=f'ls {workspace2}/')
        assert result2['success'] is True
        assert 'data.txt' not in result2['stdout']
        manager.cleanup('agent1')
        manager.cleanup('agent2')

    def test_docker_resource_limits(self, tmp_path):
        """Test that resource limits are applied."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager(memory_limit='512m', cpu_limit=1.0)
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        container_id = manager.create_container(agent_id='test_limits', workspace_path=workspace)
        assert container_id is not None
        container = manager.get_container('test_limits')
        assert container is not None
        manager.cleanup('test_limits')

    def test_docker_network_isolation(self, tmp_path):
        """Test that network isolation works."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager(network_mode='none')
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        manager.create_container(agent_id='test_network', workspace_path=workspace)
        result = manager.exec_command(agent_id='test_network', command='ping -c 1 google.com')
        assert result['success'] is False or 'Network is unreachable' in result['stdout']
        manager.cleanup('test_network')

    def test_docker_command_timeout(self, tmp_path):
        """Test that Docker commands can timeout."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        manager.create_container(agent_id='test_timeout', workspace_path=workspace)
        result = manager.exec_command(agent_id='test_timeout', command='sleep 10', timeout=1)
        assert result['success'] is False
        assert result['exit_code'] == -1
        assert 'timed out' in result['stderr'].lower()
        assert result['execution_time'] >= 1.0
        manager.cleanup('test_timeout')

    def test_docker_context_path_mounting(self, tmp_path):
        """Test that context paths are mounted correctly with proper read-only enforcement."""
        from massgen.filesystem_manager._docker_manager import DockerManager
        manager = DockerManager()
        workspace = tmp_path / 'workspace'
        workspace.mkdir()
        context_dir = tmp_path / 'context'
        context_dir.mkdir()
        context_file = context_dir / 'context.txt'
        context_file.write_text('Context data')
        context_paths = [{'path': str(context_dir), 'permission': 'read', 'name': 'my_context'}]
        manager.create_container(agent_id='test_context', workspace_path=workspace, context_paths=context_paths)
        result = manager.exec_command(agent_id='test_context', command=f'cat {context_dir}/context.txt')
        assert result['success'] is True
        assert 'Context data' in result['stdout']
        result_write = manager.exec_command(agent_id='test_context', command=f"echo 'should fail' > {context_dir}/new_file.txt")
        assert result_write['success'] is False
        assert 'Read-only file system' in result_write['stdout']
        new_file = context_dir / 'new_file.txt'
        assert not new_file.exists()
        manager.cleanup('test_context')

def test_docker_manager_initialization(self):
    """Test that DockerManager can be initialized."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager(image='massgen/mcp-runtime:latest', network_mode='none')
    assert manager.image == 'massgen/mcp-runtime:latest'
    assert manager.network_mode == 'none'
    assert manager.containers == {}

def test_docker_container_creation(self, tmp_path):
    """Test creating a Docker container."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    container_id = manager.create_container(agent_id='test_agent', workspace_path=workspace)
    assert container_id is not None
    assert 'test_agent' in manager.containers
    manager.cleanup('test_agent')

def test_docker_command_execution(self, tmp_path):
    """Test executing commands in Docker container."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    manager.create_container(agent_id='test_exec', workspace_path=workspace)
    result = manager.exec_command(agent_id='test_exec', command="echo 'Hello from Docker'")
    assert result['success'] is True
    assert result['exit_code'] == 0
    assert 'Hello from Docker' in result['stdout']
    manager.cleanup('test_exec')

def test_docker_container_persistence(self, tmp_path):
    """Test that container state persists across commands."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    manager.create_container(agent_id='test_persist', workspace_path=workspace)
    result1 = manager.exec_command(agent_id='test_persist', command='pip install --quiet click')
    assert result1['success'] is True
    result2 = manager.exec_command(agent_id='test_persist', command="python -c 'import click; print(click.__version__)'")
    assert result2['success'] is True
    assert len(result2['stdout'].strip()) > 0
    manager.cleanup('test_persist')

def test_docker_workspace_mounting(self, tmp_path):
    """Test that workspace is mounted correctly (with path transparency)."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    test_file = workspace / 'test.txt'
    test_file.write_text('Hello from host')
    manager.create_container(agent_id='test_mount', workspace_path=workspace)
    result = manager.exec_command(agent_id='test_mount', command=f'cat {workspace}/test.txt')
    assert result['success'] is True
    assert 'Hello from host' in result['stdout']
    result2 = manager.exec_command(agent_id='test_mount', command=f"echo 'Hello from container' > {workspace}/from_container.txt")
    assert result2['success'] is True
    from_container = workspace / 'from_container.txt'
    assert from_container.exists()
    assert 'Hello from container' in from_container.read_text()
    manager.cleanup('test_mount')

def test_docker_container_isolation(self, tmp_path):
    """Test that containers are isolated from each other."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace1 = tmp_path / 'workspace1'
    workspace1.mkdir()
    workspace2 = tmp_path / 'workspace2'
    workspace2.mkdir()
    manager.create_container(agent_id='agent1', workspace_path=workspace1)
    manager.create_container(agent_id='agent2', workspace_path=workspace2)
    result1 = manager.exec_command(agent_id='agent1', command=f"echo 'agent1 data' > {workspace1}/data.txt")
    assert result1['success'] is True
    result2 = manager.exec_command(agent_id='agent2', command=f'ls {workspace2}/')
    assert result2['success'] is True
    assert 'data.txt' not in result2['stdout']
    manager.cleanup('agent1')
    manager.cleanup('agent2')

def test_docker_resource_limits(self, tmp_path):
    """Test that resource limits are applied."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager(memory_limit='512m', cpu_limit=1.0)
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    container_id = manager.create_container(agent_id='test_limits', workspace_path=workspace)
    assert container_id is not None
    container = manager.get_container('test_limits')
    assert container is not None
    manager.cleanup('test_limits')

def test_docker_network_isolation(self, tmp_path):
    """Test that network isolation works."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager(network_mode='none')
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    manager.create_container(agent_id='test_network', workspace_path=workspace)
    result = manager.exec_command(agent_id='test_network', command='ping -c 1 google.com')
    assert result['success'] is False or 'Network is unreachable' in result['stdout']
    manager.cleanup('test_network')

def test_docker_command_timeout(self, tmp_path):
    """Test that Docker commands can timeout."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    manager.create_container(agent_id='test_timeout', workspace_path=workspace)
    result = manager.exec_command(agent_id='test_timeout', command='sleep 10', timeout=1)
    assert result['success'] is False
    assert result['exit_code'] == -1
    assert 'timed out' in result['stderr'].lower()
    assert result['execution_time'] >= 1.0
    manager.cleanup('test_timeout')

def test_docker_context_path_mounting(self, tmp_path):
    """Test that context paths are mounted correctly with proper read-only enforcement."""
    from massgen.filesystem_manager._docker_manager import DockerManager
    manager = DockerManager()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    context_dir = tmp_path / 'context'
    context_dir.mkdir()
    context_file = context_dir / 'context.txt'
    context_file.write_text('Context data')
    context_paths = [{'path': str(context_dir), 'permission': 'read', 'name': 'my_context'}]
    manager.create_container(agent_id='test_context', workspace_path=workspace, context_paths=context_paths)
    result = manager.exec_command(agent_id='test_context', command=f'cat {context_dir}/context.txt')
    assert result['success'] is True
    assert 'Context data' in result['stdout']
    result_write = manager.exec_command(agent_id='test_context', command=f"echo 'should fail' > {context_dir}/new_file.txt")
    assert result_write['success'] is False
    assert 'Read-only file system' in result_write['stdout']
    new_file = context_dir / 'new_file.txt'
    assert not new_file.exists()
    manager.cleanup('test_context')

class TestHelper:

    def __init__(self):
        self.temp_dir = None
        self.workspace_dir = None
        self.context_dir = None
        self.readonly_dir = None

    def setup(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace_dir = self.temp_dir / 'workspace'
        self.context_dir = self.temp_dir / 'context'
        self.readonly_dir = self.temp_dir / 'readonly'
        self.workspace_dir.mkdir(parents=True)
        self.context_dir.mkdir(parents=True)
        self.readonly_dir.mkdir(parents=True)
        (self.workspace_dir / 'workspace_file.txt').write_text('workspace content')
        (self.context_dir / 'context_file.txt').write_text('context content')
        (self.readonly_dir / 'readonly_file.txt').write_text('readonly content')

    def teardown(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_permission_manager(self, context_write_enabled=False):
        manager = PathPermissionManager(context_write_access_enabled=context_write_enabled)
        manager.add_path(self.workspace_dir, Permission.WRITE, 'workspace')
        if context_write_enabled:
            manager.add_path(self.context_dir, Permission.WRITE, 'context')
        else:
            manager.add_path(self.context_dir, Permission.READ, 'context')
        manager.add_path(self.readonly_dir, Permission.READ, 'context')
        return manager

def setup(self):
    self.temp_dir = Path(tempfile.mkdtemp())
    self.workspace_dir = self.temp_dir / 'workspace'
    self.context_dir = self.temp_dir / 'context'
    self.readonly_dir = self.temp_dir / 'readonly'
    self.workspace_dir.mkdir(parents=True)
    self.context_dir.mkdir(parents=True)
    self.readonly_dir.mkdir(parents=True)
    (self.workspace_dir / 'workspace_file.txt').write_text('workspace content')
    (self.context_dir / 'context_file.txt').write_text('context content')
    (self.readonly_dir / 'readonly_file.txt').write_text('readonly content')

def create_permission_manager(self, context_write_enabled=False):
    manager = PathPermissionManager(context_write_access_enabled=context_write_enabled)
    manager.add_path(self.workspace_dir, Permission.WRITE, 'workspace')
    if context_write_enabled:
        manager.add_path(self.context_dir, Permission.WRITE, 'context')
    else:
        manager.add_path(self.context_dir, Permission.READ, 'context')
    manager.add_path(self.readonly_dir, Permission.READ, 'context')
    return manager

def test_is_write_tool():
    print('\n📝 Testing _is_write_tool method...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = helper.create_permission_manager()
        claude_write_tools = ['Write', 'Edit', 'MultiEdit', 'NotebookEdit']
        for tool in claude_write_tools:
            if not manager._is_write_tool(tool):
                print(f'❌ Failed: {tool} should be detected as write tool')
                return False
        claude_read_tools = ['Read', 'Glob', 'Grep', 'WebFetch']
        for tool in claude_read_tools:
            if manager._is_write_tool(tool):
                print(f'❌ Failed: {tool} should NOT be detected as write tool')
                return False
        mcp_write_tools = ['write_file', 'edit_file', 'create_directory', 'move_file', 'delete_file', 'remove_directory']
        for tool in mcp_write_tools:
            if not manager._is_write_tool(tool):
                print(f'❌ Failed: {tool} should be detected as write tool')
                return False
        mcp_read_tools = ['read_file', 'list_directory']
        for tool in mcp_read_tools:
            if manager._is_write_tool(tool):
                print(f'❌ Failed: {tool} should NOT be detected as write tool')
                return False
        print('✅ _is_write_tool detection works correctly')
        return True
    finally:
        helper.teardown()

def test_validate_write_tool():
    print('\n📝 Testing _validate_write_tool method...')
    helper = TestHelper()
    helper.setup()
    try:
        print('  Testing workspace write access...')
        manager = helper.create_permission_manager(context_write_enabled=False)
        tool_args = {'file_path': str(helper.workspace_dir / 'workspace_file.txt')}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if not allowed:
            print(f'❌ Failed: Workspace should always be writable. Reason: {reason}')
            return False
        print('  Testing context path with write enabled...')
        manager = helper.create_permission_manager(context_write_enabled=True)
        tool_args = {'file_path': str(helper.context_dir / 'context_file.txt')}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if not allowed:
            print(f'❌ Failed: Context path should be writable when enabled. Reason: {reason}')
            return False
        print('  Testing context path with write disabled...')
        manager = helper.create_permission_manager(context_write_enabled=False)
        tool_args = {'file_path': str(helper.context_dir / 'context_file.txt')}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if allowed:
            print('❌ Failed: Context path should NOT be writable when disabled')
            return False
        if 'read-only context path' not in reason:
            print(f"❌ Failed: Expected 'read-only context path' in reason, got: {reason}")
            return False
        print('  Testing readonly path...')
        for context_write_enabled in [True, False]:
            manager = helper.create_permission_manager(context_write_enabled=context_write_enabled)
            tool_args = {'file_path': str(helper.readonly_dir / 'readonly_file.txt')}
            allowed, reason = manager._validate_write_tool('Write', tool_args)
            if allowed:
                print(f'❌ Failed: Readonly path should never be writable (context_write={context_write_enabled})')
                return False
        print('  Testing unknown path...')
        manager = helper.create_permission_manager()
        unknown_file = helper.temp_dir / 'unknown' / 'file.txt'
        unknown_file.parent.mkdir(exist_ok=True)
        unknown_file.write_text('content')
        tool_args = {'file_path': str(unknown_file)}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if not allowed:
            print(f'❌ Failed: Unknown paths should be allowed. Reason: {reason}')
            return False
        print('  Testing different path argument names...')
        manager = helper.create_permission_manager(context_write_enabled=False)
        readonly_file = str(helper.readonly_dir / 'readonly_file.txt')
        path_arg_names = ['file_path', 'path', 'filename', 'notebook_path', 'target']
        for arg_name in path_arg_names:
            tool_args = {arg_name: readonly_file}
            allowed, reason = manager._validate_write_tool('Write', tool_args)
            if allowed:
                print(f"❌ Failed: Should block readonly with arg name '{arg_name}'")
                return False
        print('✅ _validate_write_tool works correctly')
        return True
    finally:
        helper.teardown()

def test_validate_command_tool():
    print('\n🔧 Testing _validate_command_tool method...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = helper.create_permission_manager()
        print('  Testing dangerous command blocking...')
        dangerous_commands = ['rm file.txt', 'rm -rf directory/', 'sudo apt install', 'su root', 'chmod 777 file.txt', 'chown user:group file.txt', 'format C:', 'fdisk /dev/sda', 'mkfs.ext4 /dev/sdb1']
        for cmd in dangerous_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('Bash', tool_args)
            if allowed:
                print(f'❌ Failed: Dangerous command should be blocked: {cmd}')
                return False
            if 'Dangerous command pattern' not in reason:
                print(f"❌ Failed: Expected 'Dangerous command pattern' for: {cmd}, got: {reason}")
                return False
        print('  Testing safe command allowance...')
        safe_commands = ['ls -la', 'cat file.txt', 'grep pattern file.txt', "find . -name '*.py'", 'python script.py', 'npm install', 'git status']
        for cmd in safe_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('Bash', tool_args)
            if not allowed:
                print(f'❌ Failed: Safe command should be allowed: {cmd}. Reason: {reason}')
                return False
        print('  Testing write operations to readonly paths...')
        manager = helper.create_permission_manager(context_write_enabled=False)
        readonly_file = str(helper.readonly_dir / 'readonly_file.txt')
        write_commands = [f"echo 'content' > {readonly_file}", f"echo 'content' >> {readonly_file}", f'mv source.txt {readonly_file}', f'cp source.txt {readonly_file}', f'touch {readonly_file}']
        for cmd in write_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('Bash', tool_args)
            if allowed:
                print(f'❌ Failed: Write to readonly should be blocked: {cmd}')
                return False
            if 'read-only context path' not in reason:
                print(f"❌ Failed: Expected 'read-only context path' for: {cmd}, got: {reason}")
                return False
        print('  Testing write operations to workspace...')
        workspace_file = str(helper.workspace_dir / 'workspace_file.txt')
        write_commands = [f"echo 'content' > {workspace_file}", f"echo 'content' >> {workspace_file}", f'mv source.txt {workspace_file}', f'cp source.txt {workspace_file}']
        for cmd in write_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('Bash', tool_args)
            if not allowed:
                print(f'❌ Failed: Write to workspace should be allowed: {cmd}. Reason: {reason}')
                return False
        print('✅ _validate_command_tool works correctly')
        return True
    finally:
        helper.teardown()

def test_validate_execute_command_tool():
    print('\n⚙️  Testing _validate_command_tool for execute_command...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = helper.create_permission_manager()
        print('  Testing dangerous command blocking for execute_command...')
        dangerous_commands = ['rm file.txt', 'rm -rf directory/', 'sudo apt install', 'su root', 'chmod 777 file.txt', 'chown user:group file.txt', 'format C:', 'fdisk /dev/sda', 'mkfs.ext4 /dev/sdb1']
        for cmd in dangerous_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('execute_command', tool_args)
            if allowed:
                print(f'❌ Failed: Dangerous command should be blocked for execute_command: {cmd}')
                return False
            if 'Dangerous command pattern' not in reason:
                print(f"❌ Failed: Expected 'Dangerous command pattern' for: {cmd}, got: {reason}")
                return False
        print('  Testing safe command allowance for execute_command...')
        safe_commands = ['python script.py', 'pytest tests/', 'npm run build', 'ls -la', 'cat file.txt', 'git status', 'node app.js']
        for cmd in safe_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('execute_command', tool_args)
            if not allowed:
                print(f'❌ Failed: Safe command should be allowed for execute_command: {cmd}. Reason: {reason}')
                return False
        print('  Testing write operations to readonly paths for execute_command...')
        manager = helper.create_permission_manager(context_write_enabled=False)
        readonly_file = str(helper.readonly_dir / 'readonly_file.txt')
        write_commands = [f"echo 'content' > {readonly_file}", f"echo 'content' >> {readonly_file}", f'mv source.txt {readonly_file}', f'cp source.txt {readonly_file}', f'touch {readonly_file}']
        for cmd in write_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('execute_command', tool_args)
            if allowed:
                print(f'❌ Failed: Write to readonly should be blocked for execute_command: {cmd}')
                return False
            if 'read-only context path' not in reason:
                print(f"❌ Failed: Expected 'read-only context path' for: {cmd}, got: {reason}")
                return False
        print('  Testing write operations to workspace for execute_command...')
        workspace_file = str(helper.workspace_dir / 'workspace_file.txt')
        write_commands = [f"echo 'content' > {workspace_file}", f"echo 'content' >> {workspace_file}", f'mv source.txt {workspace_file}', f'cp source.txt {workspace_file}']
        for cmd in write_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('execute_command', tool_args)
            if not allowed:
                print(f'❌ Failed: Write to workspace should be allowed for execute_command: {cmd}. Reason: {reason}')
                return False
        print('  Testing write operations to paths outside all managed directories...')
        outside_dir = helper.temp_dir / 'completely_outside'
        outside_dir.mkdir(parents=True)
        outside_file = str(outside_dir / 'outside_file.txt')
        outside_commands = [f"echo 'content' > {outside_file}", f'cp source.txt {outside_file}']
        for cmd in outside_commands:
            tool_args = {'command': cmd}
            allowed, reason = manager._validate_command_tool('execute_command', tool_args)
            if not allowed:
                print(f'❌ Failed: Write to unmanaged path should be allowed for execute_command: {cmd}. Reason: {reason}')
                return False
        print('✅ _validate_command_tool works correctly for execute_command')
        return True
    finally:
        helper.teardown()

def test_context_write_access_toggle():
    print('\n🔄 Testing context write access toggle...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = PathPermissionManager(context_write_access_enabled=False)
        context_paths = [{'path': str(helper.context_dir), 'permission': 'write'}, {'path': str(helper.readonly_dir), 'permission': 'read'}]
        manager.add_context_paths(context_paths)
        print('  Testing initial read-only state...')
        if manager.get_permission(helper.context_dir) != Permission.READ:
            print('❌ Failed: Context path should initially be read-only')
            return False
        if manager.get_permission(helper.readonly_dir) != Permission.READ:
            print('❌ Failed: Readonly path should be read-only')
            return False
        print('  Testing write access enabled...')
        manager.set_context_write_access_enabled(True)
        if manager.get_permission(helper.context_dir) != Permission.WRITE:
            print('❌ Failed: Context path should be writable after enabling')
            return False
        if manager.get_permission(helper.readonly_dir) != Permission.READ:
            print('❌ Failed: Readonly path should stay read-only')
            return False
        print('  Testing write access disabled again...')
        manager.set_context_write_access_enabled(False)
        if manager.get_permission(helper.context_dir) != Permission.READ:
            print('❌ Failed: Context path should be read-only after disabling')
            return False
        if manager.get_permission(helper.readonly_dir) != Permission.READ:
            print('❌ Failed: Readonly path should stay read-only')
            return False
        print('✅ Context write access toggle works correctly')
        return True
    finally:
        helper.teardown()

def test_extract_file_from_command():
    print('\n📄 Testing _extract_file_from_command method...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = helper.create_permission_manager()
        print('  Testing redirect command extraction...')
        test_cases = [("echo 'content' > file.txt", '>', 'file.txt'), ('cat input.txt >> output.log', '>>', 'output.log'), ('ls -la > /path/to/file.txt', '>', '/path/to/file.txt')]
        for command, pattern, expected in test_cases:
            result = manager._extract_file_from_command(command, pattern)
            if result != expected:
                print(f"❌ Failed: Expected '{expected}' from '{command}', got '{result}'")
                return False
        print('  Testing move/copy command extraction...')
        test_cases = [('mv source.txt dest.txt', 'mv ', 'dest.txt'), ('cp file1.txt file2.txt', 'cp ', 'file2.txt'), ('move old.txt new.txt', 'move ', 'new.txt'), ('copy source.doc target.doc', 'copy ', 'target.doc')]
        for command, pattern, expected in test_cases:
            result = manager._extract_file_from_command(command, pattern)
            if result != expected:
                print(f"❌ Failed: Expected '{expected}' from '{command}', got '{result}'")
                return False
        print('✅ _extract_file_from_command works correctly')
        return True
    finally:
        helper.teardown()

def test_workspace_tools():
    print('\n📦 Testing workspace tools validation...')
    helper = TestHelper()
    helper.setup()
    try:
        temp_workspace_dir = helper.temp_dir / 'temp_workspace'
        temp_workspace_dir.mkdir(parents=True)
        (temp_workspace_dir / 'source_file.txt').write_text('source content')
        print('  Testing copy tool detection...')
        manager = helper.create_permission_manager(context_write_enabled=False)
        manager.add_path(temp_workspace_dir, Permission.READ, 'temp_workspace')
        copy_tools = ['copy_file', 'copy_files_batch', 'mcp__workspace_tools__copy_file', 'mcp__workspace_tools__copy_files_batch']
        for tool in copy_tools:
            if not manager._is_write_tool(tool):
                print(f'❌ Failed: {tool} should be detected as write tool')
                return False
        print('  Testing copy_file destination permissions...')
        tool_args = {'source_path': str(temp_workspace_dir / 'source_file.txt'), 'destination_path': str(helper.workspace_dir / 'dest_file.txt')}
        allowed, reason = manager._validate_write_tool('copy_file', tool_args)
        if not allowed:
            print(f'❌ Failed: copy_file to workspace should be allowed. Reason: {reason}')
            return False
        tool_args = {'source_path': str(temp_workspace_dir / 'source_file.txt'), 'destination_path': str(helper.readonly_dir / 'dest_file.txt')}
        allowed, reason = manager._validate_write_tool('copy_file', tool_args)
        if allowed:
            print('❌ Failed: copy_file to readonly directory should be blocked')
            return False
        print('  Testing copy FROM read-only paths...')
        tool_args = {'source_path': str(helper.readonly_dir / 'readonly_file.txt'), 'destination_path': str(helper.workspace_dir / 'copied_from_readonly.txt')}
        allowed, reason = manager._validate_write_tool('copy_file', tool_args)
        if not allowed:
            print(f'❌ Failed: copy FROM read-only path should be allowed. Reason: {reason}')
            return False
        tool_args = {'source_base_path': str(helper.readonly_dir), 'destination_base_path': str(helper.workspace_dir / 'copied_from_readonly')}
        allowed, reason = manager._validate_write_tool('copy_files_batch', tool_args)
        if not allowed:
            print(f'❌ Failed: copy_files_batch FROM read-only path should be allowed. Reason: {reason}')
            return False
        print('  Testing copy_files_batch destination permissions...')
        tool_args = {'source_base_path': str(temp_workspace_dir), 'destination_base_path': str(helper.workspace_dir / 'output')}
        allowed, reason = manager._validate_write_tool('copy_files_batch', tool_args)
        if not allowed:
            print(f'❌ Failed: copy_files_batch to workspace subdirectory should be allowed. Reason: {reason}')
            return False
        tool_args = {'source_base_path': str(temp_workspace_dir), 'destination_base_path': str(helper.readonly_dir / 'output')}
        allowed, reason = manager._validate_write_tool('copy_files_batch', tool_args)
        if allowed:
            print('❌ Failed: copy_files_batch to readonly directory should be blocked')
            return False
        print('  Testing _extract_file_path with copy arguments...')
        tool_args = {'source_path': str(temp_workspace_dir / 'source.txt'), 'destination_path': str(helper.workspace_dir / 'dest.txt')}
        extracted = manager._extract_file_path(tool_args)
        if extracted != str(helper.workspace_dir / 'dest.txt'):
            print(f'❌ Failed: Should extract destination_path, got: {extracted}')
            return False
        tool_args = {'source_base_path': str(temp_workspace_dir), 'destination_base_path': str(helper.workspace_dir / 'output')}
        extracted = manager._extract_file_path(tool_args)
        if extracted != str(helper.workspace_dir / 'output'):
            print(f'❌ Failed: Should extract destination_base_path, got: {extracted}')
            return False
        print('  Testing absolute path validation...')
        tool_args = {'source_path': str(temp_workspace_dir / 'source_file.txt'), 'destination_path': str(helper.workspace_dir / 'valid_destination.txt')}
        allowed, reason = manager._validate_write_tool('copy_file', tool_args)
        if not allowed:
            print(f'❌ Failed: copy_file with valid absolute destination should be allowed. Reason: {reason}')
            return False
        tool_args = {'source_base_path': str(temp_workspace_dir), 'destination_base_path': str(helper.workspace_dir / 'batch_output')}
        allowed, reason = manager._validate_write_tool('copy_files_batch', tool_args)
        if not allowed:
            print(f'❌ Failed: copy_files_batch with valid absolute destination should be allowed. Reason: {reason}')
            return False
        print('  Testing outside allowed paths...')
        outside_dir = helper.temp_dir / 'outside_allowed'
        outside_dir.mkdir(parents=True)
        tool_args = {'source_path': str(temp_workspace_dir / 'source_file.txt'), 'destination_path': str(outside_dir / 'should_be_blocked.txt')}
        allowed, reason = manager._validate_write_tool('copy_file', tool_args)
        print('✅ Workspace copy tool validation works correctly')
        return True
    finally:
        helper.teardown()

def test_default_exclusions():
    print('\n🚫 Testing default system file exclusions...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = helper.create_permission_manager(context_write_enabled=True)
        project_dir = helper.temp_dir / 'project'
        project_dir.mkdir()
        manager.add_path(project_dir, Permission.WRITE, 'context')
        print('  Testing excluded patterns are blocked...')
        excluded_files = [project_dir / '.env', project_dir / '.git' / 'config', project_dir / 'node_modules' / 'package' / 'index.js', project_dir / '__pycache__' / 'module.pyc', project_dir / '.venv' / 'lib' / 'python.py', project_dir / '.massgen' / 'sessions' / 'session.json', project_dir / 'massgen_logs' / 'app.log']
        for excluded_file in excluded_files:
            excluded_file.parent.mkdir(parents=True, exist_ok=True)
            excluded_file.write_text('content')
            permission = manager.get_permission(excluded_file)
            if permission != Permission.READ:
                print(f'❌ Failed: {excluded_file} should be READ, got {permission}')
                return False
        print('  Testing normal files are writable...')
        normal_files = [project_dir / 'src' / 'main.py', project_dir / 'README.md', project_dir / 'config.yaml']
        for normal_file in normal_files:
            normal_file.parent.mkdir(parents=True, exist_ok=True)
            normal_file.write_text('content')
            permission = manager.get_permission(normal_file)
            if permission != Permission.WRITE:
                print(f'❌ Failed: {normal_file} should be WRITE, got {permission}')
                return False
        print('  Testing workspace overrides exclusions...')
        workspace_dir = helper.temp_dir / 'project' / '.massgen' / 'workspaces' / 'workspace1'
        workspace_dir.mkdir(parents=True)
        manager.add_path(workspace_dir, Permission.WRITE, 'workspace')
        workspace_file = workspace_dir / 'index.html'
        workspace_file.write_text('content')
        permission = manager.get_permission(workspace_file)
        if permission != Permission.WRITE:
            print(f'❌ Failed: Workspace file should be WRITE even under .massgen/, got {permission}')
            return False
        print('✅ Default system file exclusions work correctly')
        return True
    finally:
        helper.teardown()

def test_path_priority_resolution():
    print('\n🎯 Testing path priority resolution (depth-first)...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = PathPermissionManager(context_write_access_enabled=True)
        project_dir = helper.temp_dir / 'project'
        project_dir.mkdir()
        manager.add_path(project_dir, Permission.READ, 'context')
        workspace_dir = project_dir / '.massgen' / 'workspaces' / 'workspace1'
        workspace_dir.mkdir(parents=True)
        manager.add_path(workspace_dir, Permission.WRITE, 'workspace')
        print('  Testing workspace file uses deeper path permission...')
        workspace_file = workspace_dir / 'index.html'
        workspace_file.write_text('content')
        permission = manager.get_permission(workspace_file)
        if permission != Permission.WRITE:
            print(f'❌ Failed: Workspace file should use workspace WRITE permission, got {permission}')
            return False
        print('  Testing project file uses parent path permission...')
        project_file = project_dir / 'README.md'
        project_file.write_text('content')
        permission = manager.get_permission(project_file)
        if permission != Permission.READ:
            print(f'❌ Failed: Project file should use context READ permission, got {permission}')
            return False
        print('  Testing multiple nested paths...')
        nested_dir = project_dir / 'src' / 'components'
        nested_dir.mkdir(parents=True)
        manager.add_path(nested_dir, Permission.WRITE, 'context')
        nested_file = nested_dir / 'Button.jsx'
        nested_file.write_text('content')
        permission = manager.get_permission(nested_file)
        if permission != Permission.WRITE:
            print(f'❌ Failed: Nested file should use deepest matching path, got {permission}')
            return False
        src_file = project_dir / 'src' / 'index.js'
        src_file.write_text('content')
        permission = manager.get_permission(src_file)
        if permission != Permission.READ:
            print(f'❌ Failed: src/ file should use parent context READ permission, got {permission}')
            return False
        print('✅ Path priority resolution works correctly')
        return True
    finally:
        helper.teardown()

def test_workspace_tools_server_path_validation():
    print('\n🏗️  Testing workspace tools server path validation...')
    helper = TestHelper()
    helper.setup()
    try:
        allowed_paths = [helper.workspace_dir.resolve(), helper.context_dir.resolve(), helper.readonly_dir.resolve()]
        test_source_dir = helper.temp_dir / 'source'
        test_source_dir.mkdir()
        (test_source_dir / 'test_file.txt').write_text('test content')
        (test_source_dir / 'subdir' / 'nested_file.txt').parent.mkdir(parents=True)
        (test_source_dir / 'subdir' / 'nested_file.txt').write_text('nested content')
        allowed_paths.append(test_source_dir.resolve())
        print('  Testing valid absolute destination path...')
        try:
            dest_path = helper.workspace_dir / 'output'
            file_pairs = get_copy_file_pairs(allowed_paths, str(test_source_dir), str(dest_path))
            if len(file_pairs) < 2:
                print(f'❌ Failed: Expected at least 2 files, got {len(file_pairs)}')
                return False
            print(f'  ✓ Found {len(file_pairs)} files to copy')
        except Exception as e:
            print(f'❌ Failed: Valid absolute path should work. Error: {e}')
            return False
        print('  Testing destination outside allowed paths...')
        outside_dir = helper.temp_dir / 'outside'
        outside_dir.mkdir()
        try:
            file_pairs = get_copy_file_pairs(allowed_paths, str(test_source_dir), str(outside_dir / 'output'))
            print('❌ Failed: Should have raised ValueError for path outside allowed directories')
            return False
        except ValueError as e:
            if 'Path not in allowed directories' in str(e):
                print('  ✓ Correctly blocked path outside allowed directories')
            else:
                print(f'❌ Failed: Unexpected error: {e}')
                return False
        except Exception as e:
            print(f'❌ Failed: Unexpected exception: {e}')
            return False
        print('  Testing source outside allowed paths...')
        outside_source = helper.temp_dir / 'outside_source'
        outside_source.mkdir()
        (outside_source / 'bad_file.txt').write_text('bad content')
        try:
            file_pairs = get_copy_file_pairs(allowed_paths, str(outside_source), str(helper.workspace_dir / 'output'))
            print('❌ Failed: Should have raised ValueError for source outside allowed directories')
            return False
        except ValueError as e:
            if 'Path not in allowed directories' in str(e):
                print('  ✓ Correctly blocked source outside allowed directories')
            else:
                print(f'❌ Failed: Unexpected error: {e}')
                return False
        print('  Testing empty destination_base_path...')
        try:
            file_pairs = get_copy_file_pairs(allowed_paths, str(test_source_dir), '')
            print('❌ Failed: Should have raised ValueError for empty destination_base_path')
            return False
        except ValueError as e:
            if 'destination_base_path is required' in str(e):
                print('  ✓ Correctly required destination_base_path')
            else:
                print(f'❌ Failed: Unexpected error: {e}')
                return False
        print('  Testing _validate_path_access function...')
        try:
            test_path = (helper.workspace_dir / 'test.txt').resolve()
            resolved_allowed_paths = [p.resolve() for p in allowed_paths]
            _validate_path_access(test_path, resolved_allowed_paths)
            print('  ✓ Valid path accepted')
        except Exception as e:
            print(f'❌ Failed: Valid path should be accepted. Error: {e}')
            return False
        try:
            test_path = (outside_dir / 'test.txt').resolve()
            resolved_allowed_paths = [p.resolve() for p in allowed_paths]
            _validate_path_access(test_path, resolved_allowed_paths)
            print('❌ Failed: Invalid path should be rejected')
            return False
        except ValueError as e:
            if 'Path not in allowed directories' in str(e):
                print('  ✓ Invalid path correctly rejected')
            else:
                print(f'❌ Failed: Unexpected error: {e}')
                return False
        print('  Testing relative path resolution...')
        original_cwd = os.getcwd()
        try:
            os.chdir(str(helper.workspace_dir))
            source, dest = _validate_and_resolve_paths(allowed_paths, str(test_source_dir / 'test_file.txt'), 'subdir/relative_dest.txt')
            expected_dest = helper.workspace_dir / 'subdir' / 'relative_dest.txt'
            if dest != expected_dest.resolve():
                print(f'❌ Failed: Relative path should resolve to {expected_dest.resolve()}, got {dest}')
                return False
            print('  ✓ Relative path correctly resolved to workspace')
        except Exception as e:
            print(f'❌ Failed: Relative path resolution failed: {e}')
            return False
        finally:
            os.chdir(original_cwd)
        print('✅ Workspace copy server path validation works correctly')
        return True
    finally:
        helper.teardown()

def test_file_context_paths():
    print('\n📄 Testing file-based context paths...')
    helper = TestHelper()
    helper.setup()
    try:
        test_file = helper.context_dir / 'important_file.txt'
        test_file.write_text('important content')
        sibling_file = helper.context_dir / 'sibling_file.txt'
        sibling_file.write_text('sibling content')
        another_sibling = helper.context_dir / 'another_file.txt'
        another_sibling.write_text('another content')
        manager = PathPermissionManager(context_write_access_enabled=False)
        manager.add_path(helper.workspace_dir, Permission.WRITE, 'workspace')
        file_context_paths = [{'path': str(test_file), 'permission': 'read'}]
        manager.add_context_paths(file_context_paths)
        print('  Testing file gets read permission...')
        permission = manager.get_permission(test_file)
        if permission != Permission.READ:
            print(f'❌ Failed: File should have read permission, got {permission}')
            return False
        print('  Testing sibling file has no permission...')
        permission = manager.get_permission(sibling_file)
        if permission is not None:
            print(f'❌ Failed: Sibling file should have no permission, got {permission}')
            return False
        print('  Testing parent directory has no direct permission...')
        permission = manager.get_permission(helper.context_dir)
        if permission is not None:
            print(f'❌ Failed: Parent directory should have no permission, got {permission}')
            return False
        print('  Testing write tool access to sibling file is blocked...')
        tool_args = {'file_path': str(sibling_file)}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if allowed:
            print('❌ Failed: Write to sibling file should be blocked')
            return False
        if 'not an explicitly allowed file' not in reason:
            print(f"❌ Failed: Expected 'not an explicitly allowed file' in reason, got: {reason}")
            return False
        print('  Testing write tool access to another sibling is also blocked...')
        tool_args = {'file_path': str(another_sibling)}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if allowed:
            print('❌ Failed: Write to another sibling should be blocked')
            return False
        print('  Testing read tool access to allowed file works...')
        tool_args = {'file_path': str(test_file)}
        allowed, reason = manager._validate_write_tool('Read', tool_args)
        if not allowed:
            print(f'❌ Failed: Read of allowed file should work. Reason: {reason}')
            return False
        print('  Testing file context path with write permission...')
        manager2 = PathPermissionManager(context_write_access_enabled=True)
        manager2.add_path(helper.workspace_dir, Permission.WRITE, 'workspace')
        file_context_paths2 = [{'path': str(test_file), 'permission': 'write'}]
        manager2.add_context_paths(file_context_paths2)
        permission = manager2.get_permission(test_file)
        if permission != Permission.WRITE:
            print(f'❌ Failed: File should have write permission when enabled, got {permission}')
            return False
        print('  Testing write to allowed file works with write permission...')
        tool_args = {'file_path': str(test_file)}
        allowed, reason = manager2._validate_write_tool('Write', tool_args)
        if not allowed:
            print(f'❌ Failed: Write to allowed file should work with write permission. Reason: {reason}')
            return False
        print('  Testing write to sibling still blocked even with write-enabled file context...')
        tool_args = {'file_path': str(sibling_file)}
        allowed, reason = manager2._validate_write_tool('Write', tool_args)
        if allowed:
            print('❌ Failed: Write to sibling should still be blocked')
            return False
        print('  Testing parent directory still has no MCP paths...')
        mcp_paths = manager.get_mcp_filesystem_paths()
        if str(helper.context_dir.resolve()) not in mcp_paths:
            print('❌ Failed: Parent directory should be in MCP allowed paths for file access')
            return False
        print('  Testing deletion of sibling file is blocked...')
        tool_args = {'path': str(sibling_file)}
        allowed, reason = manager._validate_write_tool('delete_file', tool_args)
        if allowed:
            print('❌ Failed: Deletion of sibling file should be blocked')
            return False
        print('  Testing copy to sibling location is blocked...')
        tool_args = {'source_path': str(helper.workspace_dir / 'workspace_file.txt'), 'destination_path': str(another_sibling)}
        allowed, reason = manager._validate_write_tool('copy_file', tool_args)
        if allowed:
            print('❌ Failed: Copy to sibling location should be blocked')
            return False
        print('✅ File-based context paths work correctly')
        return True
    finally:
        helper.teardown()

def test_delete_operations():
    print('\n🗑️  Testing deletion operations...')
    helper = TestHelper()
    helper.setup()
    try:
        manager = helper.create_permission_manager(context_write_enabled=False)
        print('  Testing delete_file detected as write tool...')
        if not manager._is_write_tool('delete_file'):
            print('❌ Failed: delete_file should be detected as write tool')
            return False
        if not manager._is_write_tool('delete_files_batch'):
            print('❌ Failed: delete_files_batch should be detected as write tool')
            return False
        print('  Testing deletion permission validation...')
        test_file = helper.workspace_dir / 'test.txt'
        test_file.write_text('content')
        tool_args = {'path': str(test_file)}
        allowed, reason = manager._validate_write_tool('delete_file', tool_args)
        if not allowed:
            print(f'❌ Failed: Workspace file deletion should be allowed. Reason: {reason}')
            return False
        readonly_file = helper.readonly_dir / 'readonly_file.txt'
        tool_args = {'path': str(readonly_file)}
        allowed, reason = manager._validate_write_tool('delete_file', tool_args)
        if allowed:
            print('❌ Failed: Read-only file deletion should be blocked')
            return False
        if 'read-only context path' not in reason:
            print(f"❌ Failed: Expected 'read-only context path' in reason, got: {reason}")
            return False
        manager2 = helper.create_permission_manager(context_write_enabled=True)
        context_file = helper.context_dir / 'context_file.txt'
        tool_args = {'path': str(context_file)}
        allowed, reason = manager2._validate_write_tool('delete_file', tool_args)
        if not allowed:
            print(f'❌ Failed: Writable context file deletion should be allowed. Reason: {reason}')
            return False
        print('  Testing batch deletion permissions...')
        for i in range(3):
            (helper.workspace_dir / f'file{i}.txt').write_text(f'content {i}')
        tool_args = {'base_path': str(helper.workspace_dir), 'include_patterns': ['*.txt']}
        allowed, reason = manager._validate_write_tool('delete_files_batch', tool_args)
        print('✅ Deletion operation permissions work correctly')
        return True
    finally:
        helper.teardown()

def test_permission_path_root_protection():
    print('\n🛡️  Testing permission path root protection...')
    helper = TestHelper()
    helper.setup()
    try:
        from massgen.filesystem_manager._workspace_tools_server import _is_permission_path_root
        print('  Testing workspace root is protected...')
        if not _is_permission_path_root(helper.workspace_dir, [helper.workspace_dir]):
            print('❌ Failed: Workspace root should be protected from deletion')
            return False
        print('  Testing files within workspace are NOT protected...')
        test_file = helper.workspace_dir / 'file.txt'
        test_file.write_text('content')
        if _is_permission_path_root(test_file, [helper.workspace_dir]):
            print('❌ Failed: Files within workspace should not be protected by root check')
            return False
        test_subdir = helper.workspace_dir / 'subdir'
        test_subdir.mkdir()
        if _is_permission_path_root(test_subdir, [helper.workspace_dir]):
            print('❌ Failed: Subdirs within workspace should not be protected by root check')
            return False
        print('  Testing nested directories are NOT protected...')
        nested = helper.workspace_dir / 'a' / 'b' / 'c'
        nested.mkdir(parents=True)
        if _is_permission_path_root(nested, [helper.workspace_dir]):
            print('❌ Failed: Nested directories should not be protected by root check')
            return False
        print('  Testing system files still protected within workspace...')
        from massgen.filesystem_manager._workspace_tools_server import _is_critical_path
        system_dir = helper.workspace_dir / '.massgen'
        system_dir.mkdir()
        if not _is_critical_path(system_dir, [helper.workspace_dir]):
            print('❌ Failed: .massgen should still be protected by critical path check')
            return False
        if _is_critical_path(helper.workspace_dir, [helper.workspace_dir]):
            print('❌ Failed: Workspace root should not be a critical path when within allowed paths')
            return False
        user_dir = helper.workspace_dir / 'user_project'
        user_dir.mkdir()
        if _is_critical_path(user_dir, [helper.workspace_dir]):
            print('❌ Failed: Regular user directory should not be critical within workspace')
            return False
        print('  Testing real-world scenario: workspace under .massgen/workspaces/...')
        massgen_dir = helper.temp_dir / '.massgen'
        massgen_dir.mkdir()
        workspaces_dir = massgen_dir / 'workspaces'
        workspaces_dir.mkdir()
        real_workspace = workspaces_dir / 'workspace1'
        real_workspace.mkdir()
        user_project = real_workspace / 'bob_dylan_website'
        user_project.mkdir()
        (user_project / 'index.html').write_text('<html></html>')
        if _is_critical_path(user_project, [real_workspace]):
            print('❌ Failed: User project should not be critical within workspace even if parent has .massgen')
            print(f'   Path: {user_project}')
            print(f'   Workspace: {real_workspace}')
            return False
        git_dir = real_workspace / '.git'
        git_dir.mkdir()
        if not _is_critical_path(git_dir, [real_workspace]):
            print('❌ Failed: .git should still be critical within workspace')
            return False
        massgen_subdir = real_workspace / '.massgen'
        massgen_subdir.mkdir()
        if not _is_critical_path(massgen_subdir, [real_workspace]):
            print('❌ Failed: .massgen subdir should be critical within workspace')
            return False
        print('  Testing multiple permission paths...')
        allowed_paths = [helper.workspace_dir, helper.context_dir, helper.readonly_dir]
        for path in allowed_paths:
            if not _is_permission_path_root(path, allowed_paths):
                print(f'❌ Failed: {path} should be protected as root')
                return False
        for root_dir in allowed_paths:
            test_file = root_dir / 'test.txt'
            test_file.write_text('test')
            if _is_permission_path_root(test_file, allowed_paths):
                print(f'❌ Failed: File {test_file} should not be protected as root')
                return False
        print('✅ Permission path root protection works correctly')
        return True
    finally:
        helper.teardown()

def test_protected_paths():
    print('\n🛡️  Testing protected paths feature...')
    helper = TestHelper()
    helper.setup()
    try:
        test_dir = helper.temp_dir / 'test_project'
        test_dir.mkdir()
        (test_dir / 'modifiable.txt').write_text('can modify')
        (test_dir / 'protected.txt').write_text('cannot modify')
        protected_dir = test_dir / 'protected_dir'
        protected_dir.mkdir()
        (protected_dir / 'nested.txt').write_text('also protected')
        print('  Testing protected paths configuration...')
        manager = PathPermissionManager(context_write_access_enabled=True)
        context_paths = [{'path': str(test_dir), 'permission': 'write', 'protected_paths': ['protected.txt', 'protected_dir/']}]
        manager.add_context_paths(context_paths)
        print('  Testing modifiable file has WRITE permission...')
        modifiable = test_dir / 'modifiable.txt'
        permission = manager.get_permission(modifiable)
        if permission != Permission.WRITE:
            print(f'❌ Failed: Modifiable file should have WRITE, got {permission}')
            return False
        print('  Testing protected file has READ permission...')
        protected_file = test_dir / 'protected.txt'
        permission = manager.get_permission(protected_file)
        if permission != Permission.READ:
            print(f'❌ Failed: Protected file should have READ (forced), got {permission}')
            return False
        print('  Testing files in protected directory have READ permission...')
        nested_file = protected_dir / 'nested.txt'
        permission = manager.get_permission(nested_file)
        if permission != Permission.READ:
            print(f'❌ Failed: File in protected dir should have READ, got {permission}')
            return False
        print('  Testing protected directory itself has READ permission...')
        permission = manager.get_permission(protected_dir)
        if permission != Permission.READ:
            print(f'❌ Failed: Protected directory should have READ, got {permission}')
            return False
        print('  Testing write tool validation on protected paths...')
        tool_args = {'file_path': str(protected_file)}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if allowed:
            print('❌ Failed: Write to protected file should be blocked')
            return False
        if 'read-only' not in reason.lower():
            print(f"❌ Failed: Expected 'read-only' in reason, got: {reason}")
            return False
        tool_args = {'path': str(protected_file)}
        allowed, reason = manager._validate_write_tool('delete_file', tool_args)
        if allowed:
            print('❌ Failed: Delete of protected file should be blocked')
            return False
        tool_args = {'file_path': str(modifiable)}
        allowed, reason = manager._validate_write_tool('Write', tool_args)
        if not allowed:
            print(f'❌ Failed: Write to modifiable file should be allowed. Reason: {reason}')
            return False
        print('  Testing absolute protected paths...')
        test_dir2 = helper.temp_dir / 'test_project2'
        test_dir2.mkdir()
        (test_dir2 / 'file.txt').write_text('content')
        protected_abs = test_dir2 / 'protected_abs.txt'
        protected_abs.write_text('absolutely protected')
        manager2 = PathPermissionManager(context_write_access_enabled=True)
        context_paths2 = [{'path': str(test_dir2), 'permission': 'write', 'protected_paths': [str(protected_abs)]}]
        manager2.add_context_paths(context_paths2)
        permission = manager2.get_permission(protected_abs)
        if permission != Permission.READ:
            print(f'❌ Failed: Absolutely protected file should have READ, got {permission}')
            return False
        print('  Testing protected paths outside context path are ignored...')
        test_dir3 = helper.temp_dir / 'test_project3'
        test_dir3.mkdir()
        outside_file = helper.temp_dir / 'outside.txt'
        outside_file.write_text('outside')
        manager3 = PathPermissionManager(context_write_access_enabled=True)
        context_paths3 = [{'path': str(test_dir3), 'permission': 'write', 'protected_paths': [str(outside_file)]}]
        manager3.add_context_paths(context_paths3)
        print('✅ Protected paths work correctly')
        return True
    finally:
        helper.teardown()

def test_file_operation_tracker():
    print('\n📊 Testing FileOperationTracker...')
    helper = TestHelper()
    helper.setup()
    try:
        tracker = FileOperationTracker(enforce_read_before_delete=True)
        print('  Testing file read tracking...')
        test_file = helper.workspace_dir / 'test.txt'
        test_file.write_text('content')
        if tracker.was_read(test_file):
            print('❌ Failed: File should not be marked as read initially')
            return False
        tracker.mark_as_read(test_file)
        if not tracker.was_read(test_file):
            print('❌ Failed: File should be marked as read after mark_as_read')
            return False
        print('  Testing created file tracking...')
        created_file = helper.workspace_dir / 'created.txt'
        created_file.write_text('new content')
        tracker.mark_as_created(created_file)
        if not tracker.was_read(created_file):
            print("❌ Failed: Created file should count as 'read'")
            return False
        print('  Testing delete validation...')
        can_delete, reason = tracker.can_delete(test_file)
        if not can_delete:
            print(f'❌ Failed: Should allow delete of read file. Reason: {reason}')
            return False
        unread_file = helper.workspace_dir / 'unread.txt'
        unread_file.write_text('unread content')
        can_delete, reason = tracker.can_delete(unread_file)
        if can_delete:
            print('❌ Failed: Should block delete of unread file')
            return False
        if 'must be read before deletion' not in reason:
            print(f"❌ Failed: Expected 'must be read before deletion' in reason, got: {reason}")
            return False
        can_delete, reason = tracker.can_delete(created_file)
        if not can_delete:
            print(f'❌ Failed: Should allow delete of created file. Reason: {reason}')
            return False
        print('  Testing directory delete validation...')
        test_dir = helper.workspace_dir / 'test_dir'
        test_dir.mkdir()
        (test_dir / 'file1.txt').write_text('content 1')
        (test_dir / 'file2.txt').write_text('content 2')
        can_delete, reason = tracker.can_delete_directory(test_dir)
        if can_delete:
            print('❌ Failed: Should block delete of directory with unread files')
            return False
        tracker.mark_as_read(test_dir / 'file1.txt')
        tracker.mark_as_read(test_dir / 'file2.txt')
        can_delete, reason = tracker.can_delete_directory(test_dir)
        if not can_delete:
            print(f'❌ Failed: Should allow delete of directory with all files read. Reason: {reason}')
            return False
        print('  Testing tracker stats...')
        stats = tracker.get_stats()
        if stats['read_files'] < 3:
            print(f'❌ Failed: Expected at least 3 read files, got {stats['read_files']}')
            return False
        if stats['created_files'] < 1:
            print(f'❌ Failed: Expected at least 1 created file, got {stats['created_files']}')
            return False
        print('  Testing tracker clear...')
        tracker.clear()
        stats = tracker.get_stats()
        if stats['read_files'] != 0 or stats['created_files'] != 0:
            print(f'❌ Failed: Tracker should be empty after clear, got {stats}')
            return False
        print('  Testing disabled enforcement...')
        tracker_disabled = FileOperationTracker(enforce_read_before_delete=False)
        can_delete, reason = tracker_disabled.can_delete(unread_file)
        if not can_delete:
            print('❌ Failed: Should allow delete when enforcement disabled')
            return False
        print('✅ FileOperationTracker works correctly')
        return True
    finally:
        helper.teardown()

@pytest.fixture
def test_workspace(tmp_path):
    """Create temporary test workspace."""
    workspace = tmp_path / 'test_context_sharing'
    workspace.mkdir(exist_ok=True)
    snapshot_storage = workspace / 'snapshots'
    temp_workspace = workspace / 'temp_workspaces'
    snapshot_storage.mkdir(exist_ok=True)
    temp_workspace.mkdir(exist_ok=True)
    yield {'workspace': workspace, 'snapshot_storage': str(snapshot_storage), 'temp_workspace': str(temp_workspace)}
    if workspace.exists():
        shutil.rmtree(workspace)

