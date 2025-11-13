# Cluster 50

def main() -> None:
    """Main entry point for the config builder."""
    try:
        builder = ConfigBuilder()
        result = builder.run()
        if result and len(result) == 2:
            filepath, question = result
            if question:
                console.print('\n[bold green]✅ Configuration created successfully![/bold green]')
                console.print('\n[bold cyan]Running MassGen...[/bold cyan]\n')
                import asyncio
                import sys
                original_argv = sys.argv.copy()
                sys.argv = ['massgen', '--config', filepath, question]
                try:
                    from .cli import main as cli_main
                    asyncio.run(cli_main())
                finally:
                    sys.argv = original_argv
            else:
                console.print('\n[bold green]✅ Configuration saved![/bold green]')
                console.print('\n[bold cyan]To use it, run:[/bold cyan]')
                console.print(f'  [yellow]massgen --config {filepath} "Your question"[/yellow]\n')
        else:
            console.print('[yellow]Configuration builder exited.[/yellow]')
    except KeyboardInterrupt:
        console.print('\n\n[bold yellow]Configuration cancelled by user[/bold yellow]\n')
    except Exception as e:
        console.print(f'\n[error]❌ Unexpected error in main: {str(e)}[/error]')
        console.print('[info]Please report this issue if it persists.[/info]\n')

class Orchestrator(ChatAgent):
    """
    Orchestrator Agent - Unified chat interface with sub-agent coordination.

    The orchestrator acts as a single agent from the user's perspective, but internally
    coordinates multiple sub-agents using the proven binary decision framework.

    Key Features:
    - Unified chat interface (same as any individual agent)
    - Automatic sub-agent coordination and conflict resolution
    - Transparent MassGen workflow execution
    - Real-time streaming with proper source attribution
    - Graceful restart mechanism for dynamic case transitions
    - Session management

    TODO - Missing Configuration Options:
    - Option to include/exclude voting details in user messages
    - Configurable timeout settings for agent responses
    - Configurable retry limits and backoff strategies
    - Custom voting strategies beyond simple majority
    - Configurable presentation formats for final answers
    - Advanced coordination workflows (hierarchical, weighted voting, etc.)

    TODO (v0.0.14 Context Sharing Enhancement - See docs/dev_notes/v0.0.14-context.md):
    - Add permission validation logic for agent workspace access
    - Implement validate_agent_access() method to check if agent has required permission for resource
    - Replace current prompt-based access control with explicit system-level enforcement
    - Add PermissionManager integration for managing agent access rules
    - Implement audit logging for all access attempts to workspace resources
    - Support dynamic permission negotiation during runtime
    - Add configurable policy framework for permission management
    - Integrate with workspace snapshot mechanism for controlled context sharing

    Restart Behavior:
    When an agent provides new_answer, all agents gracefully restart to ensure
    consistent coordination state. This allows all agents to transition to Case 2
    evaluation with the new answers available.
    """

    def __init__(self, agents: Dict[str, ChatAgent], orchestrator_id: str='orchestrator', session_id: Optional[str]=None, config: Optional[AgentConfig]=None, snapshot_storage: Optional[str]=None, agent_temporary_workspace: Optional[str]=None, previous_turns: Optional[List[Dict[str, Any]]]=None):
        """
        Initialize MassGen orchestrator.

        Args:
            agents: Dictionary of {agent_id: ChatAgent} - can be individual agents or other orchestrators
            orchestrator_id: Unique identifier for this orchestrator (default: "orchestrator")
            session_id: Optional session identifier
            config: Optional AgentConfig for customizing orchestrator behavior
            snapshot_storage: Optional path to store agent workspace snapshots
            agent_temporary_workspace: Optional path for agent temporary workspaces
            previous_turns: List of previous turn metadata for multi-turn conversations (loaded by CLI)
        """
        super().__init__(session_id)
        self.orchestrator_id = orchestrator_id
        self.agents = agents
        self.agent_states = {aid: AgentState() for aid in agents.keys()}
        self.config = config or AgentConfig.create_openai_config()
        self.message_templates = self.config.message_templates or MessageTemplates()
        self.workflow_tools = self.message_templates.get_standard_tools(list(agents.keys()))
        self.current_task: Optional[str] = None
        self.workflow_phase: str = 'idle'
        self._coordination_messages: List[Dict[str, str]] = []
        self._selected_agent: Optional[str] = None
        self._final_presentation_content: Optional[str] = None
        self.total_tokens: int = 0
        self.coordination_start_time: float = 0
        self.is_orchestrator_timeout: bool = False
        self.timeout_reason: Optional[str] = None
        self._active_streams: Dict = {}
        self._active_tasks: Dict = {}
        self._snapshot_storage: Optional[str] = snapshot_storage
        self._agent_temporary_workspace: Optional[str] = agent_temporary_workspace
        self._previous_turns: List[Dict[str, Any]] = previous_turns or []
        self.coordination_tracker = CoordinationTracker()
        self.coordination_tracker.initialize_session(list(agents.keys()))
        if snapshot_storage:
            self._snapshot_storage = snapshot_storage
            snapshot_path = Path(self._snapshot_storage)
            if snapshot_path.exists() and any(snapshot_path.iterdir()):
                shutil.rmtree(snapshot_path)
            snapshot_path.mkdir(parents=True, exist_ok=True)
        for agent_id, agent in self.agents.items():
            if agent.backend.filesystem_manager:
                agent.backend.filesystem_manager.setup_orchestration_paths(agent_id=agent_id, snapshot_storage=self._snapshot_storage, agent_temporary_workspace=self._agent_temporary_workspace)
                agent.backend.filesystem_manager.update_backend_mcp_config(agent.backend.config)

    @staticmethod
    def _get_chunk_type_value(chunk) -> str:
        """
        Extract chunk type as string, handling both legacy and typed chunks.

        Args:
            chunk: StreamChunk, TextStreamChunk, or MultimodalStreamChunk

        Returns:
            String representation of chunk type (e.g., "content", "tool_calls")
        """
        chunk_type = chunk.type
        if isinstance(chunk_type, ChunkType):
            return chunk_type.value
        return str(chunk_type)

    async def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]=None, reset_chat: bool=False, clear_history: bool=False) -> AsyncGenerator[StreamChunk, None]:
        """
        Main chat interface - handles user messages and coordinates sub-agents.

        Args:
            messages: List of conversation messages
            tools: Ignored by orchestrator (uses internal workflow tools)
            reset_chat: If True, reset conversation and start fresh
            clear_history: If True, clear history before processing

        Yields:
            StreamChunk: Streaming response chunks
        """
        _ = tools
        if clear_history:
            self.conversation_history.clear()
        if reset_chat:
            self.reset()
        conversation_context = self._build_conversation_context(messages)
        user_message = conversation_context.get('current_message')
        if not user_message:
            log_stream_chunk('orchestrator', 'error', 'No user message found in conversation')
            yield StreamChunk(type='error', error='No user message found in conversation')
            return
        self.add_to_history('user', user_message)
        if self.workflow_phase == 'idle':
            self.current_task = user_message
            self.coordination_tracker.initialize_session(list(self.agents.keys()), self.current_task)
            self.workflow_phase = 'coordinating'
            if conversation_context and conversation_context.get('conversation_history'):
                self._clear_agent_workspaces()
            async for chunk in self._coordinate_agents_with_timeout(conversation_context):
                yield chunk
        elif self.workflow_phase == 'presenting':
            async for chunk in self._handle_followup(user_message, conversation_context):
                yield chunk
        else:
            log_stream_chunk('orchestrator', 'content', '🔄 Coordinating agents, please wait...')
            yield StreamChunk(type='content', content='🔄 Coordinating agents, please wait...')

    async def chat_simple(self, user_message: str) -> AsyncGenerator[StreamChunk, None]:
        """
        Backwards compatible simple chat interface.

        Args:
            user_message: Simple string message from user

        Yields:
            StreamChunk: Streaming response chunks
        """
        messages = [{'role': 'user', 'content': user_message}]
        async for chunk in self.chat(messages):
            yield chunk

    def _build_conversation_context(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build conversation context from message list."""
        conversation_history = []
        current_message = None
        for message in messages:
            role = message.get('role')
            content = message.get('content', '')
            if role == 'user':
                current_message = content
                if len(conversation_history) > 0 or len(messages) > 1:
                    conversation_history.append(message.copy())
            elif role == 'assistant':
                conversation_history.append(message.copy())
            elif role == 'system':
                pass
        if conversation_history and conversation_history[-1].get('role') == 'user':
            conversation_history.pop()
        return {'current_message': current_message, 'conversation_history': conversation_history, 'full_messages': messages}

    def save_coordination_logs(self):
        """Public method to save coordination logs after final presentation is complete."""
        self.coordination_tracker._end_session()
        log_session_dir = get_log_session_dir()
        if log_session_dir:
            self.coordination_tracker.save_coordination_logs(log_session_dir)

    async def _coordinate_agents_with_timeout(self, conversation_context: Optional[Dict[str, Any]]=None) -> AsyncGenerator[StreamChunk, None]:
        """Execute coordination with orchestrator-level timeout protection."""
        self.coordination_start_time = time.time()
        self.total_tokens = 0
        self.is_orchestrator_timeout = False
        self.timeout_reason = None
        log_orchestrator_activity(self.orchestrator_id, 'Starting coordination with timeout', {'timeout_seconds': self.config.timeout_config.orchestrator_timeout_seconds, 'agents': list(self.agents.keys())})
        self._active_streams = {}
        self._active_tasks = {}
        timeout_seconds = self.config.timeout_config.orchestrator_timeout_seconds
        try:
            async with asyncio.timeout(timeout_seconds):
                async for chunk in self._coordinate_agents(conversation_context):
                    if hasattr(chunk, 'content') and chunk.content:
                        self.total_tokens += len(chunk.content.split())
                    yield chunk
        except asyncio.TimeoutError:
            self.is_orchestrator_timeout = True
            elapsed = time.time() - self.coordination_start_time
            self.timeout_reason = f'Time limit exceeded ({elapsed:.1f}s/{timeout_seconds}s)'
            for agent_id in self.agent_states.keys():
                if not self.agent_states[agent_id].has_voted:
                    self.coordination_tracker.track_agent_action(agent_id, ActionType.TIMEOUT, self.timeout_reason)
            await self._cleanup_active_coordination()
        if self.is_orchestrator_timeout:
            async for chunk in self._handle_orchestrator_timeout():
                yield chunk

    async def _coordinate_agents(self, conversation_context: Optional[Dict[str, Any]]=None) -> AsyncGenerator[StreamChunk, None]:
        """Execute unified MassGen coordination workflow with real-time streaming."""
        log_coordination_step('Starting multi-agent coordination', {'agents': list(self.agents.keys()), 'has_context': conversation_context is not None})
        if self.config.skip_coordination_rounds:
            log_stream_chunk('orchestrator', 'content', '⚡ [DEBUG MODE] Skipping coordination rounds, going straight to final presentation...\n\n', self.orchestrator_id)
            yield StreamChunk(type='content', content='⚡ [DEBUG MODE] Skipping coordination rounds, going straight to final presentation...\n\n', source=self.orchestrator_id)
            self._selected_agent = list(self.agents.keys())[0]
            log_coordination_step('Skipped coordination, selected first agent', {'selected_agent': self._selected_agent})
            async for chunk in self._present_final_answer():
                yield chunk
            return
        log_stream_chunk('orchestrator', 'content', '🚀 Starting multi-agent coordination...\n\n', self.orchestrator_id)
        yield StreamChunk(type='content', content='🚀 Starting multi-agent coordination...\n\n', source=self.orchestrator_id)
        votes = {}
        for agent_id in self.agents.keys():
            self.agent_states[agent_id].has_voted = False
            self.agent_states[agent_id].restart_pending = True
        log_stream_chunk('orchestrator', 'content', '## 📋 Agents Coordinating\n', self.orchestrator_id)
        yield StreamChunk(type='content', content='## 📋 Agents Coordinating\n', source=self.orchestrator_id)
        async for chunk in self._stream_coordination_with_agents(votes, conversation_context):
            yield chunk
        current_answers = {aid: state.answer for aid, state in self.agent_states.items() if state.answer}
        self._selected_agent = self._determine_final_agent_from_votes(votes, current_answers)
        log_coordination_step('Final agent selected', {'selected_agent': self._selected_agent, 'votes': votes})
        async for chunk in self._present_final_answer():
            yield chunk

    async def _stream_coordination_with_agents(self, votes: Dict[str, Dict], conversation_context: Optional[Dict[str, Any]]=None) -> AsyncGenerator[StreamChunk, None]:
        """
        Coordinate agents with real-time streaming of their outputs.

        Processes agent stream signals:
        - "content": Streams real-time agent output to user
        - "result": Records votes/answers, triggers restart_pending for other agents
        - "error": Displays error and closes agent stream (self-terminating)
        - "done": Closes agent stream gracefully

        Restart Mechanism:
        When any agent provides new_answer, all other agents get restart_pending=True
        and gracefully terminate their current work before restarting.
        """
        active_streams = {}
        active_tasks = {}
        self._active_streams = active_streams
        self._active_tasks = active_tasks
        while not all((state.has_voted for state in self.agent_states.values())):
            self.coordination_tracker.start_new_iteration()
            if self.is_orchestrator_timeout:
                break
            current_answers = {aid: state.answer for aid, state in self.agent_states.items() if state.answer}
            for agent_id in self.agents.keys():
                if agent_id not in active_streams and (not self.agent_states[agent_id].has_voted) and (not self.agent_states[agent_id].is_killed):
                    active_streams[agent_id] = self._stream_agent_execution(agent_id, self.current_task, current_answers, conversation_context)
            if not active_streams:
                break
            for agent_id, stream in active_streams.items():
                if agent_id not in active_tasks:
                    active_tasks[agent_id] = asyncio.create_task(self._get_next_chunk(stream))
            if not active_tasks:
                break
            done, _ = await asyncio.wait(active_tasks.values(), return_when=asyncio.FIRST_COMPLETED)
            reset_signal = False
            voted_agents = {}
            answered_agents = {}
            completed_agent_ids = set()
            for task in done:
                agent_id = next((aid for aid, t in active_tasks.items() if t is task))
                del active_tasks[agent_id]
                try:
                    chunk_type, chunk_data = await task
                    if chunk_type == 'content':
                        log_stream_chunk('orchestrator', 'content', chunk_data, agent_id)
                        yield StreamChunk(type='content', content=chunk_data, source=agent_id)
                    elif chunk_type == 'reasoning':
                        log_stream_chunk('orchestrator', 'reasoning', chunk_data, agent_id)
                        yield chunk_data
                    elif chunk_type == 'result':
                        result_type, result_data = chunk_data
                        completed_agent_ids.add(agent_id)
                        log_stream_chunk('orchestrator', f'result.{result_type}', result_data, agent_id)
                        yield StreamChunk(type='agent_status', source=agent_id, status='completed', content='')
                        await self._close_agent_stream(agent_id, active_streams)
                        if result_type == 'answer':
                            agent = self.agents.get(agent_id)
                            agent_context = self.get_last_context(agent_id)
                            answer_timestamp = await self._save_agent_snapshot(agent_id, answer_content=result_data, context_data=agent_context)
                            if agent and agent.backend.filesystem_manager:
                                agent.backend.filesystem_manager.log_current_state('after providing answer')
                            answered_agents[agent_id] = result_data
                            self.coordination_tracker.add_agent_answer(agent_id, result_data, snapshot_timestamp=answer_timestamp)
                            restart_triggered_id = agent_id
                            reset_signal = True
                            log_stream_chunk('orchestrator', 'content', '✅ Answer provided\n', agent_id)
                            log_stream_chunk('orchestrator', 'content', '✅ Answer provided\n', agent_id)
                            yield StreamChunk(type='content', content='✅ Answer provided\n', source=agent_id)
                        elif result_type == 'vote':
                            if self._check_restart_pending(agent_id):
                                voted_for = result_data.get('agent_id', '<unknown>')
                                reason = result_data.get('reason', 'No reason provided')
                                self.coordination_tracker.track_agent_action(agent_id, ActionType.VOTE_IGNORED, f'Voted for {voted_for} but ignored due to restart')
                                log_stream_chunk('orchestrator', 'content', f'🔄 Vote for [{voted_for}] ignored (reason: {reason}) - restarting due to new answers', agent_id)
                                yield StreamChunk(type='content', content=f'🔄 Vote for [{voted_for}] ignored (reason: {reason}) - restarting due to new answers', source=agent_id)
                            else:
                                vote_timestamp = await self._save_agent_snapshot(agent_id=agent_id, vote_data=result_data, context_data=self.get_last_context(agent_id))
                                agent = self.agents.get(agent_id)
                                if agent and agent.backend.filesystem_manager:
                                    self.agents.get(agent_id).backend.filesystem_manager.log_current_state('after voting')
                                voted_agents[agent_id] = result_data
                                self.coordination_tracker.add_agent_vote(agent_id, result_data, snapshot_timestamp=vote_timestamp)
                                voted_for = result_data.get('agent_id', '<unknown>')
                                reason = result_data.get('reason', 'No reason provided')
                                log_stream_chunk('orchestrator', 'content', f'✅ Vote recorded for [{result_data['agent_id']}]', agent_id)
                                yield StreamChunk(type='content', content=f'✅ Vote recorded for [{result_data['agent_id']}]', source=agent_id)
                    elif chunk_type == 'error':
                        self.coordination_tracker.track_agent_action(agent_id, ActionType.ERROR, chunk_data)
                        completed_agent_ids.add(agent_id)
                        log_stream_chunk('orchestrator', 'error', chunk_data, agent_id)
                        yield StreamChunk(type='content', content=f'❌ {chunk_data}', source=agent_id)
                        log_stream_chunk('orchestrator', 'agent_status', 'completed', agent_id)
                        yield StreamChunk(type='agent_status', source=agent_id, status='completed', content='')
                        await self._close_agent_stream(agent_id, active_streams)
                    elif chunk_type == 'debug':
                        log_stream_chunk('orchestrator', 'debug', chunk_data, agent_id)
                        yield StreamChunk(type='debug', content=chunk_data, source=agent_id)
                    elif chunk_type == 'mcp_status':
                        mcp_message = f'🔧 MCP: {chunk_data}'
                        log_stream_chunk('orchestrator', 'mcp_status', chunk_data, agent_id)
                        yield StreamChunk(type='content', content=mcp_message, source=agent_id)
                    elif chunk_type == 'done':
                        completed_agent_ids.add(agent_id)
                        log_stream_chunk('orchestrator', 'done', None, agent_id)
                        yield StreamChunk(type='agent_status', source=agent_id, status='completed', content='')
                        await self._close_agent_stream(agent_id, active_streams)
                except Exception as e:
                    self.coordination_tracker.track_agent_action(agent_id, ActionType.ERROR, f'Stream error - {e}')
                    completed_agent_ids.add(agent_id)
                    log_stream_chunk('orchestrator', 'error', f'❌ Stream error - {e}', agent_id)
                    yield StreamChunk(type='content', content=f'❌ Stream error - {e}', source=agent_id)
                    await self._close_agent_stream(agent_id, active_streams)
            if reset_signal:
                for state in self.agent_states.values():
                    state.has_voted = False
                votes.clear()
                for agent_id in self.agent_states.keys():
                    self.agent_states[agent_id].restart_pending = True
                self.coordination_tracker.track_restart_signal(restart_triggered_id, list(self.agent_states.keys()))
                self.coordination_tracker.complete_agent_restart(restart_triggered_id)
            else:
                for agent_id, vote_data in voted_agents.items():
                    self.agent_states[agent_id].has_voted = True
                    votes[agent_id] = vote_data
            for agent_id, answer in answered_agents.items():
                self.agent_states[agent_id].answer = answer
            for agent_id in completed_agent_ids:
                if agent_id in answered_agents:
                    self.coordination_tracker.change_status(agent_id, AgentStatus.ANSWERED)
                elif agent_id in voted_agents:
                    self.coordination_tracker.change_status(agent_id, AgentStatus.VOTED)
        for agent_id, task in active_tasks.items():
            if not task.done():
                self.coordination_tracker.track_agent_action(agent_id, ActionType.CANCELLED, 'All agents voted - coordination complete')
            task.cancel()
        for agent_id in list(active_streams.keys()):
            await self._close_agent_stream(agent_id, active_streams)

    async def _copy_all_snapshots_to_temp_workspace(self, agent_id: str) -> Optional[str]:
        """Copy all agents' latest workspace snapshots to a temporary workspace for context sharing.

        TODO (v0.0.14 Context Sharing Enhancement - See docs/dev_notes/v0.0.14-context.md):
        - Validate agent permissions before restoring snapshots
        - Check if agent has read access to other agents' workspaces
        - Implement fine-grained control over which snapshots can be accessed
        - Add audit logging for snapshot access attempts

        Args:
            agent_id: ID of the Claude Code agent receiving the context

        Returns:
            Path to the agent's workspace directory if successful, None otherwise
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        if not agent.backend.filesystem_manager:
            return None
        agent_mapping = {}
        sorted_agent_ids = sorted(self.agents.keys())
        for i, real_agent_id in enumerate(sorted_agent_ids, 1):
            agent_mapping[real_agent_id] = f'agent{i}'
        all_snapshots = {}
        if self._snapshot_storage:
            snapshot_base = Path(self._snapshot_storage)
            for source_agent_id in self.agents.keys():
                source_snapshot = snapshot_base / source_agent_id
                if source_snapshot.exists() and source_snapshot.is_dir():
                    all_snapshots[source_agent_id] = source_snapshot
        workspace_path = await agent.backend.filesystem_manager.copy_snapshots_to_temp_workspace(all_snapshots, agent_mapping)
        return str(workspace_path) if workspace_path else None

    async def _save_agent_snapshot(self, agent_id: str, answer_content: str=None, vote_data: Dict[str, Any]=None, is_final: bool=False, context_data: Any=None) -> str:
        """
        Save a snapshot of an agent's working directory and answer/vote with the same timestamp.

        Creates a timestamped directory structure:
        - agent_id/timestamp/workspace/ - Contains the workspace files
        - agent_id/timestamp/answer.txt - Contains the answer text (if provided)
        - agent_id/timestamp/vote.json - Contains the vote data (if provided)
        - agent_id/timestamp/context.txt - Contains the context used (if provided)

        Args:
            agent_id: ID of the agent
            answer_content: The answer content to save (if provided)
            vote_data: The vote data to save (if provided)
            is_final: If True, save as final snapshot for presentation
            context_data: The context data to save (conversation, answers, etc.)

        Returns:
            The timestamp used for this snapshot
        """
        logger.info(f'[Orchestrator._save_agent_snapshot] Called for agent_id={agent_id}, has_answer={bool(answer_content)}, has_vote={bool(vote_data)}, is_final={is_final}')
        agent = self.agents.get(agent_id)
        if not agent:
            logger.warning(f'[Orchestrator._save_agent_snapshot] Agent {agent_id} not found in agents dict')
            return None
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        if answer_content:
            try:
                log_session_dir = get_log_session_dir()
                if log_session_dir:
                    if is_final:
                        timestamped_dir = log_session_dir / 'final' / agent_id
                    else:
                        timestamped_dir = log_session_dir / agent_id / timestamp
                    timestamped_dir.mkdir(parents=True, exist_ok=True)
                    answer_file = timestamped_dir / 'answer.txt'
                    answer_file.write_text(answer_content)
                    logger.info(f'[Orchestrator._save_agent_snapshot] Saved answer to {answer_file}')
            except Exception as e:
                logger.warning(f'[Orchestrator._save_agent_snapshot] Failed to save answer for {agent_id}: {e}')
        if vote_data:
            try:
                log_session_dir = get_log_session_dir()
                if log_session_dir:
                    timestamped_dir = log_session_dir / agent_id / timestamp
                    timestamped_dir.mkdir(parents=True, exist_ok=True)
                    vote_file = timestamped_dir / 'vote.json'
                    current_answers = {aid: state.answer for aid, state in self.agent_states.items() if state.answer}
                    agent_mapping = {}
                    for i, real_id in enumerate(sorted(self.agents.keys()), 1):
                        agent_mapping[f'agent{i}'] = real_id
                    comprehensive_vote_data = {'voter_id': agent_id, 'voter_anon_id': next((anon for anon, real in agent_mapping.items() if real == agent_id), agent_id), 'voted_for': vote_data.get('agent_id', 'unknown'), 'voted_for_anon': next((anon for anon, real in agent_mapping.items() if real == vote_data.get('agent_id')), 'unknown'), 'reason': vote_data.get('reason', ''), 'timestamp': timestamp, 'unix_timestamp': time.time(), 'iteration': self.coordination_tracker.current_iteration if self.coordination_tracker else None, 'coordination_round': self.coordination_tracker.max_round if self.coordination_tracker else None, 'available_options': list(current_answers.keys()), 'available_options_anon': [next((anon for anon, real in agent_mapping.items() if real == aid), aid) for aid in sorted(current_answers.keys())], 'agent_mapping': agent_mapping, 'vote_context': {'total_agents': len(self.agents), 'agents_with_answers': len(current_answers), 'current_task': self.current_task}}
                    with open(vote_file, 'w', encoding='utf-8') as f:
                        json.dump(comprehensive_vote_data, f, indent=2)
                    logger.info(f'[Orchestrator._save_agent_snapshot] Saved comprehensive vote to {vote_file}')
            except Exception as e:
                logger.error(f'[Orchestrator._save_agent_snapshot] Failed to save vote for {agent_id}: {e}')
                logger.error(f'[Orchestrator._save_agent_snapshot] Traceback: {traceback.format_exc()}')
        if agent.backend.filesystem_manager:
            logger.info(f'[Orchestrator._save_agent_snapshot] Agent {agent_id} has filesystem_manager, calling save_snapshot with timestamp={(timestamp if not is_final else None)}')
            await agent.backend.filesystem_manager.save_snapshot(timestamp=timestamp if not is_final else None, is_final=is_final)
            if not is_final:
                agent.backend.filesystem_manager.clear_workspace()
                logger.info(f'[Orchestrator._save_agent_snapshot] Cleared workspace for {agent_id} after saving snapshot')
        else:
            logger.info(f'[Orchestrator._save_agent_snapshot] Agent {agent_id} does not have filesystem_manager')
        if context_data and (answer_content or vote_data):
            try:
                log_session_dir = get_log_session_dir()
                if log_session_dir:
                    if is_final:
                        timestamped_dir = log_session_dir / 'final' / agent_id
                    else:
                        timestamped_dir = log_session_dir / agent_id / timestamp
                    context_file = timestamped_dir / 'context.txt'
                    if isinstance(context_data, dict):
                        context_file.write_text(json.dumps(context_data, indent=2, default=str))
                    else:
                        context_file.write_text(str(context_data))
                    logger.info(f'[Orchestrator._save_agent_snapshot] Saved context to {context_file}')
            except Exception as ce:
                logger.warning(f'[Orchestrator._save_agent_snapshot] Failed to save context for {agent_id}: {ce}')
        return timestamp if not is_final else 'final'

    def get_last_context(self, agent_id: str) -> Any:
        """Get the last context for an agent, or None if not available."""
        return self.agent_states[agent_id].last_context if agent_id in self.agent_states else None

    async def _close_agent_stream(self, agent_id: str, active_streams: Dict[str, AsyncGenerator]) -> None:
        """Close and remove an agent stream safely."""
        if agent_id in active_streams:
            try:
                await active_streams[agent_id].aclose()
            except Exception:
                pass
            del active_streams[agent_id]

    def _check_restart_pending(self, agent_id: str) -> bool:
        """Check if agent should restart and yield restart message if needed. This will always be called when exiting out of _stream_agent_execution()."""
        restart_pending = self.agent_states[agent_id].restart_pending
        return restart_pending

    async def _save_partial_work_on_restart(self, agent_id: str) -> None:
        """
        Save partial work snapshot when agent is restarting due to new answers from others.
        This ensures that any work done before the restart is preserved and shared with other agents.

        Args:
            agent_id: ID of the agent being restarted
        """
        agent = self.agents.get(agent_id)
        if not agent or not agent.backend.filesystem_manager:
            return
        logger.info(f'[Orchestrator._save_partial_work_on_restart] Saving partial work for {agent_id} before restart')
        await self._save_agent_snapshot(agent_id, answer_content=None, context_data=self.get_last_context(agent_id), is_final=False)
        agent.backend.filesystem_manager.log_current_state('after saving partial work on restart')

    def _normalize_workspace_paths_in_answers(self, answers: Dict[str, str], viewing_agent_id: Optional[str]=None) -> Dict[str, str]:
        """Normalize absolute workspace paths in agent answers to accessible temporary workspace paths.

        This addresses the issue where agents working in separate workspace directories
        reference the same logical files using different absolute paths, causing them
        to think they're working on different tasks when voting.

        Converts workspace paths to temporary workspace paths where the viewing agent can actually
        access other agents' files for verification during context sharing.

        TODO: Replace with Docker volume mounts to ensure consistent paths across agents.

        Args:
            answers: Dict mapping agent_id to their answer content
            viewing_agent_id: The agent who will be reading these answers.
                            If None, normalizes to generic "workspace/" prefix.

        Returns:
            Dict with same keys but normalized answer content with accessible paths
        """
        normalized_answers = {}
        temp_workspace_base = None
        if viewing_agent_id:
            viewing_agent = self.agents.get(viewing_agent_id)
            if viewing_agent and viewing_agent.backend.filesystem_manager:
                temp_workspace_base = str(viewing_agent.backend.filesystem_manager.agent_temporary_workspace)
        agent_mapping = {}
        sorted_agent_ids = sorted(self.agents.keys())
        for i, real_agent_id in enumerate(sorted_agent_ids, 1):
            agent_mapping[real_agent_id] = f'agent{i}'
        for agent_id, answer in answers.items():
            normalized_answer = answer
            for other_agent_id, other_agent in self.agents.items():
                if not other_agent.backend.filesystem_manager:
                    continue
                anon_agent_id = agent_mapping.get(other_agent_id, f'agent_{other_agent_id}')
                replace_path = os.path.join(temp_workspace_base, anon_agent_id) if temp_workspace_base else anon_agent_id
                other_workspace = str(other_agent.backend.filesystem_manager.get_current_workspace())
                logger.debug(f'[Orchestrator._normalize_workspace_paths_in_answers] Replacing {other_workspace} in answer from {agent_id} with path {replace_path}. original answer: {normalized_answer}')
                normalized_answer = normalized_answer.replace(other_workspace, replace_path)
                logger.debug(f'[Orchestrator._normalize_workspace_paths_in_answers] Intermediate normalized answer: {normalized_answer}')
            normalized_answers[agent_id] = normalized_answer
        return normalized_answers

    def _normalize_workspace_paths_for_comparison(self, content: str, replacement_path: str='/workspace') -> str:
        """
        Normalize all workspace paths in content to a canonical form for equality comparison.

        Unlike _normalize_workspace_paths_in_answers which normalizes paths for specific agents,
        this method normalizes ALL workspace paths to a neutral canonical form (like '/workspace')
        so that content can be compared for equality regardless of which agent workspace it came from.

        Args:
            content: Content that may contain workspace paths

        Returns:
            Content with all workspace paths normalized to canonical form
        """
        normalized_content = content
        for agent_id, agent in self.agents.items():
            if not agent.backend.filesystem_manager:
                continue
            workspace_path = str(agent.backend.filesystem_manager.get_current_workspace())
            normalized_content = normalized_content.replace(workspace_path, replacement_path)
        return normalized_content

    async def _cleanup_active_coordination(self) -> None:
        """Force cleanup of active coordination streams and tasks on timeout."""
        if hasattr(self, '_active_tasks') and self._active_tasks:
            for agent_id, task in self._active_tasks.items():
                if not task.done():
                    if not self.is_orchestrator_timeout:
                        self.coordination_tracker.track_agent_action(agent_id, ActionType.CANCELLED, 'Coordination cleanup')
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass
            self._active_tasks.clear()
        if hasattr(self, '_active_streams') and self._active_streams:
            for agent_id in list(self._active_streams.keys()):
                await self._close_agent_stream(agent_id, self._active_streams)

    def _create_tool_error_messages(self, agent: 'ChatAgent', tool_calls: List[Dict[str, Any]], primary_error_msg: str, secondary_error_msg: str=None) -> List[Dict[str, Any]]:
        """
        Create tool error messages for all tool calls in a response.

        Args:
            agent: The ChatAgent instance for backend access
            tool_calls: List of tool calls that need error responses
            primary_error_msg: Error message for the first tool call
            secondary_error_msg: Error message for additional tool calls (defaults to primary_error_msg)

        Returns:
            List of tool result messages that can be sent back to the agent
        """
        if not tool_calls:
            return []
        if secondary_error_msg is None:
            secondary_error_msg = primary_error_msg
        enforcement_msgs = []
        first_tool_call = tool_calls[0]
        error_result_msg = agent.backend.create_tool_result_message(first_tool_call, primary_error_msg)
        enforcement_msgs.append(error_result_msg)
        for additional_tool_call in tool_calls[1:]:
            neutral_msg = agent.backend.create_tool_result_message(additional_tool_call, secondary_error_msg)
            enforcement_msgs.append(neutral_msg)
        return enforcement_msgs

    async def _stream_agent_execution(self, agent_id: str, task: str, answers: Dict[str, str], conversation_context: Optional[Dict[str, Any]]=None) -> AsyncGenerator[tuple, None]:
        """
        Stream agent execution with real-time content and final result.

        Yields:
            ("content", str): Real-time agent output (source attribution added by caller)
            ("result", (type, data)): Final result - ("vote", vote_data) or ("answer", content)
            ("error", str): Error message (self-terminating)
            ("done", None): Graceful completion signal

        Restart Behavior:
            If restart_pending is True, agent gracefully terminates with "done" signal.
            restart_pending is cleared at the beginning of execution.
        """
        agent = self.agents[agent_id]
        backend_name = None
        if hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
            backend_name = agent.backend.get_provider_name()
        log_orchestrator_activity(self.orchestrator_id, f'Starting agent execution: {agent_id}', {'agent_id': agent_id, 'backend': backend_name, 'task': task if task else None, 'has_answers': bool(answers), 'num_answers': len(answers) if answers else 0})
        logger.info(f'[Orchestrator] Agent {agent_id} starting execution loop...')
        self.agent_states[agent_id].is_killed = False
        self.agent_states[agent_id].timeout_reason = None
        if self.agent_states[agent_id].restart_pending:
            self.coordination_tracker.complete_agent_restart(agent_id)
        self.agent_states[agent_id].restart_pending = False
        await self._copy_all_snapshots_to_temp_workspace(agent_id)
        if agent.backend.filesystem_manager:
            agent.backend.filesystem_manager.log_current_state('before execution')
        try:
            agent_system_message = agent.get_configurable_system_message()
            if agent.backend.filesystem_manager:
                main_workspace = str(agent.backend.filesystem_manager.get_current_workspace())
                temp_workspace = str(agent.backend.filesystem_manager.agent_temporary_workspace) if agent.backend.filesystem_manager.agent_temporary_workspace else None
                context_paths = agent.backend.filesystem_manager.path_permission_manager.get_context_paths() if agent.backend.filesystem_manager.path_permission_manager else []
                previous_turns_context = self._get_previous_turns_context_paths()
                current_turn_num = len(previous_turns_context) + 1 if previous_turns_context else 1
                turns_to_show = [t for t in previous_turns_context if t['turn'] < current_turn_num - 1]
                workspace_prepopulated = len(previous_turns_context) > 0
                enable_image_generation = False
                if hasattr(agent, 'config') and agent.config:
                    enable_image_generation = agent.config.backend_params.get('enable_image_generation', False)
                elif hasattr(agent, 'backend') and hasattr(agent.backend, 'backend_params'):
                    enable_image_generation = agent.backend.backend_params.get('enable_image_generation', False)
                enable_command_execution = False
                if hasattr(agent, 'config') and agent.config:
                    enable_command_execution = agent.config.backend_params.get('enable_mcp_command_line', False)
                elif hasattr(agent, 'backend') and hasattr(agent.backend, 'backend_params'):
                    enable_command_execution = agent.backend.backend_params.get('enable_mcp_command_line', False)
                filesystem_system_message = self.message_templates.filesystem_system_message(main_workspace=main_workspace, temp_workspace=temp_workspace, context_paths=context_paths, previous_turns=turns_to_show, workspace_prepopulated=workspace_prepopulated, enable_image_generation=enable_image_generation, agent_answers=answers, enable_command_execution=enable_command_execution)
                agent_system_message = f'{agent_system_message}\n\n{filesystem_system_message}' if agent_system_message else filesystem_system_message
            normalized_answers = self._normalize_workspace_paths_in_answers(answers, agent_id) if answers else answers
            if normalized_answers:
                logger.info(f'[Orchestrator] Agent {agent_id} sees normalized answers: {normalized_answers}')
            else:
                logger.info(f'[Orchestrator] Agent {agent_id} sees no existing answers')
            is_coordination_phase = self.workflow_phase == 'coordinating'
            planning_mode_enabled = self.config.coordination_config and self.config.coordination_config.enable_planning_mode and is_coordination_phase if self.config and hasattr(self.config, 'coordination_config') else False
            if planning_mode_enabled and self.config.coordination_config.planning_mode_instruction:
                planning_instructions = f'\n\n{self.config.coordination_config.planning_mode_instruction}'
                agent_system_message = f'{agent_system_message}{planning_instructions}' if agent_system_message else planning_instructions.strip()
            if conversation_context and conversation_context.get('conversation_history'):
                conversation = self.message_templates.build_conversation_with_context(current_task=task, conversation_history=conversation_context.get('conversation_history', []), agent_summaries=normalized_answers, valid_agent_ids=list(normalized_answers.keys()) if normalized_answers else None, base_system_message=agent_system_message)
            else:
                conversation = self.message_templates.build_initial_conversation(task=task, agent_summaries=normalized_answers, valid_agent_ids=list(normalized_answers.keys()) if normalized_answers else None, base_system_message=agent_system_message)
            self.coordination_tracker.track_agent_context(agent_id, answers, conversation.get('conversation_history', []), conversation)
            self.agent_states[agent_id].last_context = conversation
            backend_name = None
            if hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                backend_name = agent.backend.get_provider_name()
            log_orchestrator_agent_message(agent_id, 'SEND', {'system': conversation['system_message'], 'user': conversation['user_message']}, backend_name=backend_name)
            if hasattr(agent.backend, 'set_planning_mode'):
                agent.backend.set_planning_mode(planning_mode_enabled)
                if planning_mode_enabled:
                    logger.info(f'[Orchestrator] Backend planning mode ENABLED for {agent_id} - MCP tools blocked')
                else:
                    logger.info(f'[Orchestrator] Backend planning mode DISABLED for {agent_id} - MCP tools allowed')
            max_attempts = 3
            conversation_messages = [{'role': 'system', 'content': conversation['system_message']}, {'role': 'user', 'content': conversation['user_message']}]
            enforcement_msg = self.message_templates.enforcement_message()
            self.coordination_tracker.change_status(agent_id, AgentStatus.STREAMING)
            for attempt in range(max_attempts):
                logger.info(f'[Orchestrator] Agent {agent_id} attempt {attempt + 1}/{max_attempts}')
                if self._check_restart_pending(agent_id):
                    logger.info(f'[Orchestrator] Agent {agent_id} restarting due to restart_pending flag')
                    await self._save_partial_work_on_restart(agent_id)
                    yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                    yield ('done', None)
                    return
                if attempt == 0:
                    chat_stream = agent.chat(conversation_messages, self.workflow_tools, reset_chat=True, current_stage=CoordinationStage.INITIAL_ANSWER)
                elif isinstance(enforcement_msg, list):
                    chat_stream = agent.chat(enforcement_msg, self.workflow_tools, reset_chat=False, current_stage=CoordinationStage.ENFORCEMENT)
                else:
                    enforcement_message = {'role': 'user', 'content': enforcement_msg}
                    chat_stream = agent.chat([enforcement_message], self.workflow_tools, reset_chat=False, current_stage=CoordinationStage.ENFORCEMENT)
                response_text = ''
                tool_calls = []
                workflow_tool_found = False
                logger.info(f'[Orchestrator] Agent {agent_id} starting to stream chat response...')
                async for chunk in chat_stream:
                    chunk_type = self._get_chunk_type_value(chunk)
                    if chunk_type == 'content':
                        response_text += chunk.content
                        yield ('content', chunk.content)
                        backend_name = None
                        if hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                            backend_name = agent.backend.get_provider_name()
                        log_orchestrator_agent_message(agent_id, 'RECV', {'content': chunk.content}, backend_name=backend_name)
                    elif chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                        reasoning_chunk = StreamChunk(type=chunk.type, content=chunk.content, source=agent_id, reasoning_delta=getattr(chunk, 'reasoning_delta', None), reasoning_text=getattr(chunk, 'reasoning_text', None), reasoning_summary_delta=getattr(chunk, 'reasoning_summary_delta', None), reasoning_summary_text=getattr(chunk, 'reasoning_summary_text', None), item_id=getattr(chunk, 'item_id', None), content_index=getattr(chunk, 'content_index', None), summary_index=getattr(chunk, 'summary_index', None))
                        yield ('reasoning', reasoning_chunk)
                    elif chunk_type == 'backend_status':
                        pass
                    elif chunk_type == 'mcp_status':
                        mcp_content = f'🔧 MCP: {chunk.content}'
                        yield ('content', mcp_content)
                    elif chunk_type == 'debug':
                        yield ('debug', chunk.content)
                    elif chunk_type == 'tool_calls':
                        chunk_tool_calls = getattr(chunk, 'tool_calls', []) or []
                        tool_calls.extend(chunk_tool_calls)
                        backend_name = None
                        if hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                            backend_name = agent.backend.get_provider_name()
                        for tool_call in chunk_tool_calls:
                            tool_name = agent.backend.extract_tool_name(tool_call)
                            tool_args = agent.backend.extract_tool_arguments(tool_call)
                            if tool_name == 'new_answer':
                                content = tool_args.get('content', '')
                                yield ('content', f'💡 Providing answer: "{content}"')
                                log_tool_call(agent_id, 'new_answer', {'content': content}, None, backend_name)
                            elif tool_name == 'vote':
                                agent_voted_for = tool_args.get('agent_id', '')
                                reason = tool_args.get('reason', '')
                                log_tool_call(agent_id, 'vote', {'agent_id': agent_voted_for, 'reason': reason}, None, backend_name)
                                real_agent_id = agent_voted_for
                                if answers:
                                    agent_mapping = {}
                                    for i, real_id in enumerate(sorted(answers.keys()), 1):
                                        agent_mapping[f'agent{i}'] = real_id
                                    real_agent_id = agent_mapping.get(agent_voted_for, agent_voted_for)
                                yield ('content', f'🗳️ Voting for [{real_agent_id}] (options: {', '.join(sorted(answers.keys()))}) : {reason}')
                            else:
                                yield ('content', f'🔧 Using {tool_name}')
                                log_tool_call(agent_id, tool_name, tool_args, None, backend_name)
                    elif chunk_type == 'error':
                        error_msg = getattr(chunk, 'error', str(chunk.content)) if hasattr(chunk, 'error') else str(chunk.content)
                        yield ('content', f'❌ Error: {error_msg}\n')
                vote_calls = [tc for tc in tool_calls if agent.backend.extract_tool_name(tc) == 'vote']
                if len(vote_calls) > 1:
                    if attempt < max_attempts - 1:
                        if self._check_restart_pending(agent_id):
                            await self._save_partial_work_on_restart(agent_id)
                            yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                            yield ('done', None)
                            return
                        error_msg = f'Multiple vote calls not allowed. Made {len(vote_calls)} calls but must make exactly 1. Call vote tool once with chosen agent.'
                        yield ('content', f'❌ {error_msg}')
                        enforcement_msg = self._create_tool_error_messages(agent, tool_calls, error_msg, 'Vote rejected due to multiple votes.')
                        continue
                    else:
                        yield ('error', f'Agent made {len(vote_calls)} vote calls in single response after max attempts')
                        yield ('done', None)
                        return
                new_answer_calls = [tc for tc in tool_calls if agent.backend.extract_tool_name(tc) == 'new_answer']
                if len(vote_calls) > 0 and len(new_answer_calls) > 0:
                    if attempt < max_attempts - 1:
                        if self._check_restart_pending(agent_id):
                            await self._save_partial_work_on_restart(agent_id)
                            yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                            yield ('done', None)
                            return
                        error_msg = "Cannot use both 'vote' and 'new_answer' in same response. Choose one: vote for existing answer OR provide new answer."
                        yield ('content', f'❌ {error_msg}')
                        enforcement_msg = self._create_tool_error_messages(agent, tool_calls, error_msg)
                        continue
                    else:
                        yield ('error', 'Agent used both vote and new_answer tools in single response after max attempts')
                        yield ('done', None)
                        return
                if tool_calls:
                    for tool_call in tool_calls:
                        tool_name = agent.backend.extract_tool_name(tool_call)
                        tool_args = agent.backend.extract_tool_arguments(tool_call)
                        if tool_name == 'vote':
                            logger.info(f'[Orchestrator] Agent {agent_id} voting from options: {(list(answers.keys()) if answers else 'No answers available')}')
                            if self._check_restart_pending(agent_id):
                                await self._save_partial_work_on_restart(agent_id)
                                yield ('content', f'🔄 [{agent_id}] Vote invalid - restarting due to new answers')
                                yield ('done', None)
                                return
                            workflow_tool_found = True
                            if not answers:
                                if attempt < max_attempts - 1:
                                    if self._check_restart_pending(agent_id):
                                        await self._save_partial_work_on_restart(agent_id)
                                        yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                                        yield ('done', None)
                                        return
                                    error_msg = 'Cannot vote when no answers exist. Use new_answer tool.'
                                    yield ('content', f'❌ {error_msg}')
                                    enforcement_msg = self._create_tool_error_messages(agent, [tool_call], error_msg)
                                    continue
                                else:
                                    yield ('error', 'Cannot vote when no answers exist after max attempts')
                                    yield ('done', None)
                                    return
                            voted_agent_anon = tool_args.get('agent_id')
                            reason = tool_args.get('reason', '')
                            agent_mapping = {}
                            for i, real_agent_id in enumerate(sorted(answers.keys()), 1):
                                agent_mapping[f'agent{i}'] = real_agent_id
                            voted_agent = agent_mapping.get(voted_agent_anon, voted_agent_anon)
                            if voted_agent not in answers:
                                if attempt < max_attempts - 1:
                                    if self._check_restart_pending(agent_id):
                                        await self._save_partial_work_on_restart(agent_id)
                                        yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                                        yield ('done', None)
                                        return
                                    reverse_mapping = {real_id: f'agent{i}' for i, real_id in enumerate(sorted(answers.keys()), 1)}
                                    valid_anon_agents = [reverse_mapping[real_id] for real_id in answers.keys()]
                                    error_msg = f"Invalid agent_id '{voted_agent_anon}'. Valid agents: {', '.join(valid_anon_agents)}"
                                    yield ('content', f'❌ {error_msg}')
                                    enforcement_msg = self._create_tool_error_messages(agent, [tool_call], error_msg)
                                    continue
                                else:
                                    yield ('error', f'Invalid agent_id after {max_attempts} attempts')
                                    yield ('done', None)
                                    return
                            self.agent_states[agent_id].votes = {'agent_id': voted_agent, 'reason': reason}
                            yield ('result', ('vote', {'agent_id': voted_agent, 'reason': reason}))
                            yield ('done', None)
                            return
                        elif tool_name == 'new_answer':
                            workflow_tool_found = True
                            content = tool_args.get('content', response_text.strip())
                            normalized_new_content = self._normalize_workspace_paths_for_comparison(content)
                            for existing_agent_id, existing_content in answers.items():
                                normalized_existing_content = self._normalize_workspace_paths_for_comparison(existing_content)
                                if normalized_new_content.strip() == normalized_existing_content.strip():
                                    if attempt < max_attempts - 1:
                                        if self._check_restart_pending(agent_id):
                                            await self._save_partial_work_on_restart(agent_id)
                                            yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                                            yield ('done', None)
                                            return
                                        error_msg = f'Answer already provided by {existing_agent_id}. Provide different answer or vote for existing one.'
                                        yield ('content', f'❌ {error_msg}')
                                        enforcement_msg = self._create_tool_error_messages(agent, [tool_call], error_msg)
                                        continue
                                    else:
                                        yield ('error', f'Duplicate answer provided after {max_attempts} attempts')
                                        yield ('done', None)
                                        return
                            yield ('result', ('answer', content))
                            yield ('done', None)
                            return
                        elif tool_name.startswith('mcp'):
                            pass
                        else:
                            yield ('content', f'🔧 used {tool_name} tool (not implemented)')
                if not workflow_tool_found:
                    if self._check_restart_pending(agent_id):
                        await self._save_partial_work_on_restart(agent_id)
                        yield ('content', f'🔁 [{agent_id}] gracefully restarting due to new answer detected\n')
                        yield ('done', None)
                        return
                    if attempt < max_attempts - 1:
                        yield ('content', '🔄 needs to use workflow tools...\n')
                        enforcement_msg = self.message_templates.enforcement_message()
                        continue
                    else:
                        yield ('error', f'Agent failed to use workflow tools after {max_attempts} attempts')
                        yield ('done', None)
                        return
        except Exception as e:
            yield ('error', f'Agent execution failed: {str(e)}')
            yield ('done', None)

    async def _get_next_chunk(self, stream: AsyncGenerator[tuple, None]) -> tuple:
        """Get the next chunk from an agent stream."""
        try:
            return await stream.__anext__()
        except StopAsyncIteration:
            return ('done', None)
        except Exception as e:
            return ('error', str(e))

    async def _present_final_answer(self) -> AsyncGenerator[StreamChunk, None]:
        """Present the final coordinated answer."""
        log_stream_chunk('orchestrator', 'content', '## 🎯 Final Coordinated Answer\n')
        yield StreamChunk(type='content', content='## 🎯 Final Coordinated Answer\n')
        if not self._selected_agent:
            self._selected_agent = self._determine_final_agent_from_states()
            if self._selected_agent:
                log_stream_chunk('orchestrator', 'content', f'🏆 Selected Agent: {self._selected_agent}\n')
                yield StreamChunk(type='content', content=f'🏆 Selected Agent: {self._selected_agent}\n')
        if self._selected_agent and self._selected_agent in self.agent_states and self.agent_states[self._selected_agent].answer:
            final_answer = self.agent_states[self._selected_agent].answer
            self.add_to_history('assistant', final_answer)
            log_stream_chunk('orchestrator', 'content', f'🏆 Selected Agent: {self._selected_agent}\n')
            yield StreamChunk(type='content', content=f'🏆 Selected Agent: {self._selected_agent}\n')
            log_stream_chunk('orchestrator', 'content', final_answer)
            yield StreamChunk(type='content', content=final_answer)
            log_stream_chunk('orchestrator', 'content', f'\n\n---\n*Coordinated by {len(self.agents)} agents via MassGen framework*')
            yield StreamChunk(type='content', content=f'\n\n---\n*Coordinated by {len(self.agents)} agents via MassGen framework*')
        else:
            error_msg = '❌ Unable to provide coordinated answer - no successful agents'
            self.add_to_history('assistant', error_msg)
            log_stream_chunk('orchestrator', 'error', error_msg)
            yield StreamChunk(type='content', content=error_msg)
        self.workflow_phase = 'presenting'
        log_stream_chunk('orchestrator', 'done', None)
        yield StreamChunk(type='done')

    async def _handle_orchestrator_timeout(self) -> AsyncGenerator[StreamChunk, None]:
        """Handle orchestrator timeout by jumping directly to get_final_presentation."""
        log_stream_chunk('orchestrator', 'content', f'\n⚠️ **Orchestrator Timeout**: {self.timeout_reason}\n', self.orchestrator_id)
        yield StreamChunk(type='content', content=f'\n⚠️ **Orchestrator Timeout**: {self.timeout_reason}\n', source=self.orchestrator_id)
        available_answers = {aid: state.answer for aid, state in self.agent_states.items() if state.answer and (not state.is_killed)}
        log_stream_chunk('orchestrator', 'content', f'📊 Current state: {len(available_answers)} answers available\n', self.orchestrator_id)
        yield StreamChunk(type='content', content=f'📊 Current state: {len(available_answers)} answers available\n', source=self.orchestrator_id)
        if len(available_answers) == 0:
            log_stream_chunk('orchestrator', 'error', '❌ No answers available from any agents due to timeout. No agents had enough time to provide responses.\n', self.orchestrator_id)
            yield StreamChunk(type='content', content='❌ No answers available from any agents due to timeout. No agents had enough time to provide responses.\n', source=self.orchestrator_id)
            self.workflow_phase = 'presenting'
            log_stream_chunk('orchestrator', 'done', None)
            yield StreamChunk(type='done')
            return
        current_votes = {aid: state.votes for aid, state in self.agent_states.items() if state.votes and (not state.is_killed)}
        self._selected_agent = self._determine_final_agent_from_votes(current_votes, available_answers)
        vote_results = self._get_vote_results()
        log_stream_chunk('orchestrator', 'content', f'🎯 Jumping to final presentation with {self._selected_agent} (selected despite timeout)\n', self.orchestrator_id)
        yield StreamChunk(type='content', content=f'🎯 Jumping to final presentation with {self._selected_agent} (selected despite timeout)\n', source=self.orchestrator_id)
        async for chunk in self.get_final_presentation(self._selected_agent, vote_results):
            yield chunk

    def _determine_final_agent_from_votes(self, votes: Dict[str, Dict], agent_answers: Dict[str, str]) -> str:
        """Determine which agent should present the final answer based on votes."""
        if not votes:
            return next(iter(agent_answers)) if agent_answers else None
        vote_counts = {}
        for vote_data in votes.values():
            voted_for = vote_data.get('agent_id')
            if voted_for:
                vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
        if not vote_counts:
            return next(iter(agent_answers)) if agent_answers else None
        max_votes = max(vote_counts.values())
        tied_agents = [agent_id for agent_id, count in vote_counts.items() if count == max_votes]
        for agent_id in agent_answers.keys():
            if agent_id in tied_agents:
                return agent_id
        return tied_agents[0] if tied_agents else next(iter(agent_answers)) if agent_answers else None

    async def get_final_presentation(self, selected_agent_id: str, vote_results: Dict[str, Any]) -> AsyncGenerator[StreamChunk, None]:
        """Ask the winning agent to present their final answer with voting context."""
        self.coordination_tracker.start_final_round(selected_agent_id)
        if selected_agent_id not in self.agents:
            log_stream_chunk('orchestrator', 'error', f'Selected agent {selected_agent_id} not found')
            yield StreamChunk(type='error', error=f'Selected agent {selected_agent_id} not found')
            return
        agent = self.agents[selected_agent_id]
        if agent.backend.filesystem_manager:
            agent.backend.filesystem_manager.path_permission_manager.set_context_write_access_enabled(True)
        if hasattr(agent.backend, 'set_planning_mode'):
            agent.backend.set_planning_mode(False)
            logger.info(f'[Orchestrator] Backend planning mode DISABLED for final presentation: {selected_agent_id} - MCP tools now allowed')
        temp_workspace_path = await self._copy_all_snapshots_to_temp_workspace(selected_agent_id)
        yield StreamChunk(type='debug', content=f'Restored workspace context for final presentation: {temp_workspace_path}', source=selected_agent_id)
        vote_counts = vote_results.get('vote_counts', {})
        voter_details = vote_results.get('voter_details', {})
        is_tie = vote_results.get('is_tie', False)
        voting_summary = f'You received {vote_counts.get(selected_agent_id, 0)} vote(s)'
        if voter_details.get(selected_agent_id):
            reasons = [v['reason'] for v in voter_details[selected_agent_id]]
            voting_summary += f' with feedback: {'; '.join(reasons)}'
        if is_tie:
            voting_summary += ' (tie-broken by registration order)'
        all_answers = {aid: s.answer for aid, s in self.agent_states.items() if s.answer}
        normalized_voting_summary = self._normalize_workspace_paths_in_answers({selected_agent_id: voting_summary}, selected_agent_id)[selected_agent_id]
        normalized_all_answers = self._normalize_workspace_paths_in_answers(all_answers, selected_agent_id)
        presentation_content = self.message_templates.build_final_presentation_message(original_task=self.current_task or 'Task coordination', vote_summary=normalized_voting_summary, all_answers=normalized_all_answers, selected_agent_id=selected_agent_id)
        agent_system_message = agent.get_configurable_system_message()
        enable_image_generation = False
        if hasattr(agent, 'config') and agent.config:
            enable_image_generation = agent.config.backend_params.get('enable_image_generation', False)
        elif hasattr(agent, 'backend') and hasattr(agent.backend, 'backend_params'):
            enable_image_generation = agent.backend.backend_params.get('enable_image_generation', False)
        enable_command_execution = False
        if hasattr(agent, 'config') and agent.config:
            enable_command_execution = agent.config.backend_params.get('enable_mcp_command_line', False)
        elif hasattr(agent, 'backend') and hasattr(agent.backend, 'backend_params'):
            enable_command_execution = agent.backend.backend_params.get('enable_mcp_command_line', False)
        enable_audio_generation = False
        if hasattr(agent, 'config') and agent.config:
            enable_audio_generation = agent.config.backend_params.get('enable_audio_generation', False)
        elif hasattr(agent, 'backend') and hasattr(agent.backend, 'backend_params'):
            enable_audio_generation = agent.backend.backend_params.get('enable_audio_generation', False)
        has_irreversible_actions = False
        if agent.backend.filesystem_manager:
            context_paths = agent.backend.filesystem_manager.path_permission_manager.get_context_paths()
            has_irreversible_actions = any((cp.get('permission') == 'write' for cp in context_paths))
        base_system_message = self.message_templates.final_presentation_system_message(agent_system_message, enable_image_generation, enable_audio_generation, has_irreversible_actions, enable_command_execution)
        for aid, state in self.agent_states.items():
            if aid != selected_agent_id:
                self.coordination_tracker.change_status(aid, AgentStatus.COMPLETED)
        self.coordination_tracker.set_final_agent(selected_agent_id, voting_summary, all_answers)
        if agent.backend.filesystem_manager and temp_workspace_path:
            main_workspace = str(agent.backend.filesystem_manager.get_current_workspace())
            temp_workspace = str(agent.backend.filesystem_manager.agent_temporary_workspace) if agent.backend.filesystem_manager.agent_temporary_workspace else None
            context_paths = agent.backend.filesystem_manager.path_permission_manager.get_context_paths() if agent.backend.filesystem_manager.path_permission_manager else []
            previous_turns_context = self._get_previous_turns_context_paths()
            current_turn_num = len(previous_turns_context) + 1 if previous_turns_context else 1
            turns_to_show = [t for t in previous_turns_context if t['turn'] < current_turn_num - 1]
            workspace_prepopulated = len(previous_turns_context) > 0
            base_system_message = self.message_templates.filesystem_system_message(main_workspace=main_workspace, temp_workspace=temp_workspace, context_paths=context_paths, previous_turns=turns_to_show, workspace_prepopulated=workspace_prepopulated, enable_image_generation=enable_image_generation, agent_answers=all_answers, enable_command_execution=enable_command_execution) + '\n\n## Instructions\n' + base_system_message
        presentation_messages = [{'role': 'system', 'content': base_system_message}, {'role': 'user', 'content': presentation_content}]
        self.agent_states[selected_agent_id].last_context = {'messages': presentation_messages, 'is_final': True, 'vote_summary': voting_summary, 'all_answers': all_answers, 'complete_vote_results': vote_results, 'vote_counts': vote_counts, 'voter_details': voter_details, 'all_votes': {aid: state.votes for aid, state in self.agent_states.items() if state.votes}}
        log_stream_chunk('orchestrator', 'status', f'🎤  [{selected_agent_id}] presenting final answer\n')
        yield StreamChunk(type='status', content=f'🎤  [{selected_agent_id}] presenting final answer\n')
        presentation_content = ''
        try:
            async for chunk in agent.chat(presentation_messages, reset_chat=True, current_stage=CoordinationStage.PRESENTATION):
                chunk_type = self._get_chunk_type_value(chunk)
                self.coordination_tracker.start_new_iteration()
                if chunk_type == 'content' and chunk.content:
                    presentation_content += chunk.content
                    log_stream_chunk('orchestrator', 'content', chunk.content, selected_agent_id)
                    yield StreamChunk(type='content', content=chunk.content, source=selected_agent_id)
                elif chunk_type in ['reasoning', 'reasoning_done', 'reasoning_summary', 'reasoning_summary_done']:
                    reasoning_chunk = StreamChunk(type=chunk_type, content=chunk.content, source=selected_agent_id, reasoning_delta=getattr(chunk, 'reasoning_delta', None), reasoning_text=getattr(chunk, 'reasoning_text', None), reasoning_summary_delta=getattr(chunk, 'reasoning_summary_delta', None), reasoning_summary_text=getattr(chunk, 'reasoning_summary_text', None), item_id=getattr(chunk, 'item_id', None), content_index=getattr(chunk, 'content_index', None), summary_index=getattr(chunk, 'summary_index', None))
                    log_stream_chunk('orchestrator', chunk.type, chunk.content, selected_agent_id)
                    yield reasoning_chunk
                elif chunk_type == 'backend_status':
                    import json
                    status_json = json.loads(chunk.content)
                    cwd = status_json['cwd']
                    session_id = status_json['session_id']
                    content = f'Final Temp Working directory: {cwd}.\n    Final Session ID: {session_id}.\n    '
                    log_stream_chunk('orchestrator', 'content', content, selected_agent_id)
                    yield StreamChunk(type='content', content=content, source=selected_agent_id)
                elif chunk_type == 'mcp_status':
                    mcp_content = f'🔧 MCP: {chunk.content}'
                    log_stream_chunk('orchestrator', 'content', mcp_content, selected_agent_id)
                    yield StreamChunk(type='content', content=mcp_content, source=selected_agent_id)
                elif chunk_type == 'done':
                    final_answer = presentation_content.strip() if presentation_content.strip() else self.agent_states[selected_agent_id].answer
                    final_context = self.get_last_context(selected_agent_id)
                    await self._save_agent_snapshot(self._selected_agent, answer_content=final_answer, is_final=True, context_data=final_context)
                    self.coordination_tracker.set_final_answer(selected_agent_id, final_answer, snapshot_timestamp='final')
                    log_stream_chunk('orchestrator', 'done', None, selected_agent_id)
                    yield StreamChunk(type='done', source=selected_agent_id)
                elif chunk_type == 'error':
                    log_stream_chunk('orchestrator', 'error', chunk.error, selected_agent_id)
                    yield StreamChunk(type='error', error=chunk.error, source=selected_agent_id)
                elif hasattr(chunk, 'source'):
                    log_stream_chunk('orchestrator', chunk_type, getattr(chunk, 'content', ''), selected_agent_id)
                    yield StreamChunk(type=chunk_type, content=getattr(chunk, 'content', ''), source=selected_agent_id, **{k: v for k, v in chunk.__dict__.items() if k not in ['type', 'content', 'source']})
                else:
                    log_stream_chunk('orchestrator', chunk_type, getattr(chunk, 'content', ''), selected_agent_id)
                    yield StreamChunk(type=chunk_type, content=getattr(chunk, 'content', ''), source=selected_agent_id, **{k: v for k, v in chunk.__dict__.items() if k not in ['type', 'content', 'source']})
        finally:
            if presentation_content.strip():
                self._final_presentation_content = presentation_content.strip()
            else:
                stored_answer = self.agent_states[selected_agent_id].answer
                if stored_answer:
                    fallback_content = f'\n📋 Using stored answer as final presentation:\n\n{stored_answer}'
                    log_stream_chunk('orchestrator', 'content', fallback_content, selected_agent_id)
                    yield StreamChunk(type='content', content=fallback_content, source=selected_agent_id)
                    self._final_presentation_content = stored_answer
                else:
                    log_stream_chunk('orchestrator', 'error', '\n❌ No content generated for final presentation and no stored answer available.', selected_agent_id)
                    yield StreamChunk(type='content', content='\n❌ No content generated for final presentation and no stored answer available.', source=selected_agent_id)
            self.coordination_tracker.change_status(selected_agent_id, AgentStatus.COMPLETED)
            self.save_coordination_logs()

    def _get_vote_results(self) -> Dict[str, Any]:
        """Get current vote results and statistics."""
        agent_answers = {aid: state.answer for aid, state in self.agent_states.items() if state.answer}
        votes = {aid: state.votes for aid, state in self.agent_states.items() if state.votes}
        vote_counts = {}
        voter_details = {}
        for voter_id, vote_data in votes.items():
            voted_for = vote_data.get('agent_id')
            if voted_for:
                vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
                if voted_for not in voter_details:
                    voter_details[voted_for] = []
                voter_details[voted_for].append({'voter': voter_id, 'reason': vote_data.get('reason', 'No reason provided')})
        winner = None
        is_tie = False
        if vote_counts:
            max_votes = max(vote_counts.values())
            tied_agents = [agent_id for agent_id, count in vote_counts.items() if count == max_votes]
            is_tie = len(tied_agents) > 1
            for agent_id in agent_answers.keys():
                if agent_id in tied_agents:
                    winner = agent_id
                    break
            if not winner:
                winner = tied_agents[0] if tied_agents else None
        agent_mapping = {}
        for i, real_id in enumerate(sorted(agent_answers.keys()), 1):
            agent_mapping[f'agent{i}'] = real_id
        return {'vote_counts': vote_counts, 'voter_details': voter_details, 'winner': winner, 'is_tie': is_tie, 'total_votes': len(votes), 'agents_with_answers': len(agent_answers), 'agents_voted': len([v for v in votes.values() if v.get('agent_id')]), 'agent_mapping': agent_mapping}

    def _determine_final_agent_from_states(self) -> Optional[str]:
        """Determine final agent based on current agent states."""
        agents_with_answers = {aid: state.answer for aid, state in self.agent_states.items() if state.answer}
        if not agents_with_answers:
            return None
        return next(iter(agents_with_answers))

    async def _handle_followup(self, user_message: str, conversation_context: Optional[Dict[str, Any]]=None) -> AsyncGenerator[StreamChunk, None]:
        """Handle follow-up questions after presenting final answer with conversation context."""
        if conversation_context and len(conversation_context.get('conversation_history', [])) > 0:
            log_stream_chunk('orchestrator', 'content', f"🤔 Thank you for your follow-up question in our ongoing conversation. I understand you're asking: '{user_message}'. Currently, the coordination is complete, but I can help clarify the answer or coordinate a new task that takes our conversation history into account.")
            yield StreamChunk(type='content', content=f"🤔 Thank you for your follow-up question in our ongoing conversation. I understand you're asking: '{user_message}'. Currently, the coordination is complete, but I can help clarify the answer or coordinate a new task that takes our conversation history into account.")
        else:
            log_stream_chunk('orchestrator', 'content', f"🤔 Thank you for your follow-up: '{user_message}'. The coordination is complete, but I can help clarify the answer or coordinate a new task if needed.")
            yield StreamChunk(type='content', content=f"🤔 Thank you for your follow-up: '{user_message}'. The coordination is complete, but I can help clarify the answer or coordinate a new task if needed.")
        log_stream_chunk('orchestrator', 'done', None)
        yield StreamChunk(type='done')

    def add_agent(self, agent_id: str, agent: ChatAgent) -> None:
        """Add a new sub-agent to the orchestrator."""
        self.agents[agent_id] = agent
        self.agent_states[agent_id] = AgentState()

    def remove_agent(self, agent_id: str) -> None:
        """Remove a sub-agent from the orchestrator."""
        if agent_id in self.agents:
            del self.agents[agent_id]
        if agent_id in self.agent_states:
            del self.agent_states[agent_id]

    def get_final_result(self) -> Optional[Dict[str, Any]]:
        """
        Get final result for session persistence.

        Returns:
            Dict with final_answer, winning_agent_id, and workspace_path, or None if not available
        """
        if not self._selected_agent or not self._final_presentation_content:
            return None
        winning_agent = self.agents.get(self._selected_agent)
        workspace_path = None
        if winning_agent and winning_agent.backend.filesystem_manager:
            workspace_path = str(winning_agent.backend.filesystem_manager.get_current_workspace())
        return {'final_answer': self._final_presentation_content, 'winning_agent_id': self._selected_agent, 'workspace_path': workspace_path}

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        vote_results = self._get_vote_results()
        return {'session_id': self.session_id, 'workflow_phase': self.workflow_phase, 'current_task': self.current_task, 'selected_agent': self._selected_agent, 'final_presentation_content': self._final_presentation_content, 'vote_results': vote_results, 'agents': {aid: {'agent_status': agent.get_status(), 'coordination_state': {'answer': state.answer, 'has_voted': state.has_voted}} for aid, (agent, state) in zip(self.agents.keys(), zip(self.agents.values(), self.agent_states.values()))}, 'conversation_length': len(self.conversation_history)}

    def get_configurable_system_message(self) -> Optional[str]:
        """
        Get the configurable system message for the orchestrator.

        This can define how the orchestrator should coordinate agents, construct messages,
        handle conflicts, make decisions, etc. For example:
        - Custom voting strategies
        - Message construction templates
        - Conflict resolution approaches
        - Coordination workflow preferences

        Returns:
            Orchestrator's configurable system message if available, None otherwise
        """
        if self.config and hasattr(self.config, 'get_configurable_system_message'):
            return self.config.get_configurable_system_message()
        elif self.config and hasattr(self.config, 'custom_system_instruction'):
            return self.config.custom_system_instruction
        elif self.config and self.config.backend_params:
            backend_params = self.config.backend_params
            if 'system_prompt' in backend_params:
                return backend_params['system_prompt']
            elif 'append_system_prompt' in backend_params:
                return backend_params['append_system_prompt']
        return None

    def _clear_agent_workspaces(self) -> None:
        """
        Clear all agent workspaces and pre-populate with previous turn's results.

        This creates a WRITABLE copy of turn n-1 in each agent's workspace.
        Note: CLI separately provides turn n-1 as a READ-ONLY context path, allowing
        agents to both modify files (in workspace) and reference originals (via context path).
        """
        previous_turn_workspace = None
        if self._previous_turns:
            latest_turn = self._previous_turns[-1]
            previous_turn_workspace = Path(latest_turn['path'])
        for agent_id, agent in self.agents.items():
            if agent.backend.filesystem_manager:
                workspace_path = agent.backend.filesystem_manager.get_current_workspace()
                if workspace_path and Path(workspace_path).exists():
                    for item in Path(workspace_path).iterdir():
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    logger.info(f'[Orchestrator] Cleared workspace for {agent_id}: {workspace_path}')
                    if previous_turn_workspace and previous_turn_workspace.exists():
                        logger.info(f'[Orchestrator] Pre-populating {agent_id} workspace with writable copy of turn n-1 from {previous_turn_workspace}')
                        for item in previous_turn_workspace.iterdir():
                            dest = Path(workspace_path) / item.name
                            if item.is_file():
                                shutil.copy2(item, dest)
                            elif item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                        logger.info(f'[Orchestrator] Pre-populated {agent_id} workspace with writable copy of turn n-1')

    def _get_previous_turns_context_paths(self) -> List[Dict[str, Any]]:
        """
        Get previous turns as context paths for current turn's agents.

        Returns:
            List of previous turn information with path, turn number, and task
        """
        return self._previous_turns

    async def reset(self) -> None:
        """Reset orchestrator state for new task."""
        self.conversation_history.clear()
        self.current_task = None
        self.workflow_phase = 'idle'
        self._coordination_messages.clear()
        self._selected_agent = None
        self._final_presentation_content = None
        for state in self.agent_states.values():
            state.answer = None
            state.has_voted = False
            state.restart_pending = False
            state.is_killed = False
            state.timeout_reason = None
        self.total_tokens = 0
        self.coordination_start_time = 0
        self.is_orchestrator_timeout = False
        self.timeout_reason = None
        self._active_streams = {}
        self._active_tasks = {}

def _normalize_workspace_paths_for_comparison(self, content: str, replacement_path: str='/workspace') -> str:
    """
        Normalize all workspace paths in content to a canonical form for equality comparison.

        Unlike _normalize_workspace_paths_in_answers which normalizes paths for specific agents,
        this method normalizes ALL workspace paths to a neutral canonical form (like '/workspace')
        so that content can be compared for equality regardless of which agent workspace it came from.

        Args:
            content: Content that may contain workspace paths

        Returns:
            Content with all workspace paths normalized to canonical form
        """
    normalized_content = content
    for agent_id, agent in self.agents.items():
        if not agent.backend.filesystem_manager:
            continue
        workspace_path = str(agent.backend.filesystem_manager.get_current_workspace())
        normalized_content = normalized_content.replace(workspace_path, replacement_path)
    return normalized_content

def get_final_result(self) -> Optional[Dict[str, Any]]:
    """
        Get final result for session persistence.

        Returns:
            Dict with final_answer, winning_agent_id, and workspace_path, or None if not available
        """
    if not self._selected_agent or not self._final_presentation_content:
        return None
    winning_agent = self.agents.get(self._selected_agent)
    workspace_path = None
    if winning_agent and winning_agent.backend.filesystem_manager:
        workspace_path = str(winning_agent.backend.filesystem_manager.get_current_workspace())
    return {'final_answer': self._final_presentation_content, 'winning_agent_id': self._selected_agent, 'workspace_path': workspace_path}

def create_orchestrator(agents: List[tuple], orchestrator_id: str='orchestrator', session_id: Optional[str]=None, config: Optional[AgentConfig]=None, snapshot_storage: Optional[str]=None, agent_temporary_workspace: Optional[str]=None) -> Orchestrator:
    """
    Create a MassGen orchestrator with sub-agents.

    Args:
        agents: List of (agent_id, ChatAgent) tuples
        orchestrator_id: Unique identifier for this orchestrator (default: "orchestrator")
        session_id: Optional session ID
        config: Optional AgentConfig for orchestrator customization
        snapshot_storage: Optional path to store agent workspace snapshots
        agent_temporary_workspace: Optional path for agent temporary workspaces (for Claude Code context sharing)

    Returns:
        Configured Orchestrator
    """
    agents_dict = {agent_id: agent for agent_id, agent in agents}
    return Orchestrator(agents=agents_dict, orchestrator_id=orchestrator_id, session_id=session_id, config=config, snapshot_storage=snapshot_storage, agent_temporary_workspace=agent_temporary_workspace)

class MessageTemplates:
    """Message templates implementing the proven MassGen approach."""

    def __init__(self, **template_overrides):
        """Initialize with optional template overrides."""
        self._template_overrides = template_overrides

    def evaluation_system_message(self) -> str:
        """Standard evaluation system message for all cases."""
        if 'evaluation_system_message' in self._template_overrides:
            return str(self._template_overrides['evaluation_system_message'])
        import time
        return f'You are evaluating answers from multiple agents for final response to a message.\nDifferent agents may have different builtin tools and capabilities.\nDoes the best CURRENT ANSWER address the ORIGINAL MESSAGE well?\n\nIf YES, use the `vote` tool to record your vote and skip the `new_answer` tool.\nOtherwise, digest existing answers, combine their strengths, and do additional work to address their weaknesses,\nthen use the `new_answer` tool to record a better answer to the ORIGINAL MESSAGE.\nMake sure you actually call `vote` or `new_answer` (in tool call format).\n\n*Note*: The CURRENT TIME is **{time.strftime('%Y-%m-%d %H:%M:%S')}**.'

    def format_original_message(self, task: str) -> str:
        """Format the original message section."""
        if 'format_original_message' in self._template_overrides:
            override = self._template_overrides['format_original_message']
            if callable(override):
                return override(task)
            return str(override).format(task=task)
        return f'<ORIGINAL MESSAGE> {task} <END OF ORIGINAL MESSAGE>'

    def format_conversation_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """Format conversation history for agent context."""
        if 'format_conversation_history' in self._template_overrides:
            override = self._template_overrides['format_conversation_history']
            if callable(override):
                return override(conversation_history)
            return str(override)
        if not conversation_history:
            return ''
        lines = ['<CONVERSATION_HISTORY>']
        for message in conversation_history:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            if role == 'user':
                lines.append(f'User: {content}')
            elif role == 'assistant':
                lines.append(f'Assistant: {content}')
            elif role == 'system':
                continue
        lines.append('<END OF CONVERSATION_HISTORY>')
        return '\n'.join(lines)

    def system_message_with_context(self, conversation_history: Optional[List[Dict[str, str]]]=None) -> str:
        """Evaluation system message with conversation context awareness."""
        if 'system_message_with_context' in self._template_overrides:
            override = self._template_overrides['system_message_with_context']
            if callable(override):
                return override(conversation_history)
            return str(override)
        base_message = self.evaluation_system_message()
        if conversation_history and len(conversation_history) > 0:
            context_note = '\n\nIMPORTANT: You are responding to the latest message in an ongoing conversation. Consider the full conversation context when evaluating answers and providing your response.'
            return base_message + context_note
        return base_message

    def format_current_answers_empty(self) -> str:
        """Format current answers section when no answers exist (Case 1)."""
        if 'format_current_answers_empty' in self._template_overrides:
            return str(self._template_overrides['format_current_answers_empty'])
        return '<CURRENT ANSWERS from the agents>\n(no answers available yet)\n<END OF CURRENT ANSWERS>'

    def format_current_answers_with_summaries(self, agent_summaries: Dict[str, str]) -> str:
        """Format current answers section with agent summaries (Case 2) using anonymous agent IDs."""
        if 'format_current_answers_with_summaries' in self._template_overrides:
            override = self._template_overrides['format_current_answers_with_summaries']
            if callable(override):
                return override(agent_summaries)
        lines = ['<CURRENT ANSWERS from the agents>']
        agent_mapping = {}
        for i, agent_id in enumerate(sorted(agent_summaries.keys()), 1):
            agent_mapping[agent_id] = f'agent{i}'
        for agent_id, summary in agent_summaries.items():
            anon_id = agent_mapping[agent_id]
            lines.append(f'<{anon_id}> {summary} <end of {anon_id}>')
        lines.append('<END OF CURRENT ANSWERS>')
        return '\n'.join(lines)

    def enforcement_message(self) -> str:
        """Enforcement message for Case 3 (non-workflow responses)."""
        if 'enforcement_message' in self._template_overrides:
            return str(self._template_overrides['enforcement_message'])
        return 'Finish your work above by making a tool call of `vote` or `new_answer`. Make sure you actually call the tool.'

    def tool_error_message(self, error_msg: str) -> Dict[str, str]:
        """Create a tool role message for tool usage errors."""
        return {'role': 'tool', 'content': error_msg}

    def enforcement_user_message(self) -> Dict[str, str]:
        """Create a user role message for enforcement."""
        return {'role': 'user', 'content': self.enforcement_message()}

    def get_new_answer_tool(self) -> Dict[str, Any]:
        """Get new_answer tool definition.

        TODO: Consider extending with optional context parameters for stateful backends:
        - cwd: Working directory for Claude Code sessions
        - session_id: Backend session identifier for continuity
        - model: Model used to generate the answer
        - tools_used: List of tools actually utilized
        This would enable better context preservation in multi-iteration workflows.
        """
        if 'new_answer_tool' in self._template_overrides:
            return self._template_overrides['new_answer_tool']
        return {'type': 'function', 'function': {'name': 'new_answer', 'description': 'Provide an improved answer to the ORIGINAL MESSAGE', 'parameters': {'type': 'object', 'properties': {'content': {'type': 'string', 'description': 'Your improved answer. If any builtin tools like search or code execution were used, mention how they are used here.'}}, 'required': ['content']}}}

    def get_vote_tool(self, valid_agent_ids: Optional[List[str]]=None) -> Dict[str, Any]:
        """Get vote tool definition with anonymous agent IDs."""
        if 'vote_tool' in self._template_overrides:
            override = self._template_overrides['vote_tool']
            if callable(override):
                return override(valid_agent_ids)
            return override
        tool_def = {'type': 'function', 'function': {'name': 'vote', 'description': 'Vote for the best agent to present final answer', 'parameters': {'type': 'object', 'properties': {'agent_id': {'type': 'string', 'description': "Anonymous agent ID to vote for (e.g., 'agent1', 'agent2')"}, 'reason': {'type': 'string', 'description': 'Brief reason why this agent has the best answer'}}, 'required': ['agent_id', 'reason']}}}
        if valid_agent_ids:
            anon_agent_ids = [f'agent{i}' for i in range(1, len(valid_agent_ids) + 1)]
            tool_def['function']['parameters']['properties']['agent_id']['enum'] = anon_agent_ids
        return tool_def

    def get_standard_tools(self, valid_agent_ids: Optional[List[str]]=None) -> List[Dict[str, Any]]:
        """Get standard tools for MassGen framework."""
        return [self.get_new_answer_tool(), self.get_vote_tool(valid_agent_ids)]

    def final_presentation_system_message(self, original_system_message: Optional[str]=None, enable_image_generation: bool=False, enable_audio_generation: bool=False, has_irreversible_actions: bool=False, enable_command_execution: bool=False) -> str:
        """System message for final answer presentation by winning agent.

        Args:
            original_system_message: The agent's original system message to preserve
            enable_image_generation: Whether image generation is enabled
            enable_audio_generation: Whether audio generation is enabled
            has_irreversible_actions: Whether agent has write access to context paths (requires actual file delivery)
            enable_command_execution: Whether command execution is enabled for this agent
        """
        if 'final_presentation_system_message' in self._template_overrides:
            return str(self._template_overrides['final_presentation_system_message'])
        presentation_instructions = 'You have been selected as the winning presenter in a coordination process.\nPresent the best possible coordinated answer by combining the strengths from all participants.\n\n'
        if enable_image_generation:
            presentation_instructions += 'For image generation tasks:\n- Extract image paths from the existing answer and resolve them in the shared reference.\n- Gather all agent-produced images (ignore non-existent files).\n- MUST call the generate-image tool with these input images to synthesize one final image combining their strengths.\n- MUST save the final outputand output the saved path.\n'
        if enable_audio_generation:
            presentation_instructions += 'For audio generation tasks:\n- Extract audio paths from the existing answer and resolve them in the shared reference.\n- Gather ALL audio files produced by EVERY agent (ignore non-existent files).\n  IMPORTANT: You MUST call the generate_text_with_input_audio tool to obtain transcriptions\n  for EACH AND EVERY audio file from ALL agents - no audio should be skipped or overlooked.\n- MUST combine the strengths of all transcriptions into one final detailed transcription that captures the best elements from each.\n- MUST use the convert_text_to_audio tool to convert this final transcription to a new audio file and save it, then output the saved path.\n'
        if has_irreversible_actions:
            presentation_instructions += '### Write Access to Target Path:\n\nReminder: File Delivery Required. You should first place your final answer in your workspace. However, note your workspace is NOT the final destination. You MUST copy/write files to the Target Path using FULL ABSOLUTE PATHS. Then, clean up this Target Path by deleting any outdated or unused files. Then, you must ALWAYS verify that the Target Path contains the correct final files, as no other agents were allowed to write to this path.\n'
        if enable_command_execution:
            presentation_instructions += '### Package Dependencies:\n\nCreate a `requirements.txt` file listing all Python packages needed to run your code. This helps users reproduce your work later. Include only the packages you actually used in your solution.\n'
        if original_system_message:
            return f'{original_system_message}\n\n{presentation_instructions}'
        else:
            return presentation_instructions

    def build_case1_user_message(self, task: str) -> str:
        """Build Case 1 user message (no summaries exist)."""
        return f'{self.format_original_message(task)}\n\n{self.format_current_answers_empty()}'

    def build_case2_user_message(self, task: str, agent_summaries: Dict[str, str]) -> str:
        """Build Case 2 user message (summaries exist)."""
        return f'{self.format_original_message(task)}\n\n{self.format_current_answers_with_summaries(agent_summaries)}'

    def build_evaluation_message(self, task: str, agent_answers: Optional[Dict[str, str]]=None) -> str:
        """Build evaluation user message for any case."""
        if agent_answers:
            return self.build_case2_user_message(task, agent_answers)
        else:
            return self.build_case1_user_message(task)

    def build_coordination_context(self, current_task: str, conversation_history: Optional[List[Dict[str, str]]]=None, agent_answers: Optional[Dict[str, str]]=None) -> str:
        """Build coordination context including conversation history and current state."""
        if 'build_coordination_context' in self._template_overrides:
            override = self._template_overrides['build_coordination_context']
            if callable(override):
                return override(current_task, conversation_history, agent_answers)
            return str(override)
        context_parts = []
        if conversation_history and len(conversation_history) > 0:
            history_formatted = self.format_conversation_history(conversation_history)
            if history_formatted:
                context_parts.append(history_formatted)
                context_parts.append('')
        context_parts.append(self.format_original_message(current_task))
        context_parts.append('')
        if agent_answers:
            context_parts.append(self.format_current_answers_with_summaries(agent_answers))
        else:
            context_parts.append(self.format_current_answers_empty())
        return '\n'.join(context_parts)

    def build_initial_conversation(self, task: str, agent_summaries: Optional[Dict[str, str]]=None, valid_agent_ids: Optional[List[str]]=None, base_system_message: Optional[str]=None) -> Dict[str, Any]:
        """Build complete initial conversation for MassGen evaluation."""
        if base_system_message:
            system_message = f'{self.evaluation_system_message()}\n\n#Special Requirement\n{base_system_message}'
        else:
            system_message = self.evaluation_system_message()
        return {'system_message': system_message, 'user_message': self.build_evaluation_message(task, agent_summaries), 'tools': self.get_standard_tools(valid_agent_ids)}

    def build_conversation_with_context(self, current_task: str, conversation_history: Optional[List[Dict[str, str]]]=None, agent_summaries: Optional[Dict[str, str]]=None, valid_agent_ids: Optional[List[str]]=None, base_system_message: Optional[str]=None) -> Dict[str, Any]:
        """Build complete conversation with conversation history context for MassGen evaluation."""
        if base_system_message:
            system_message = f'{base_system_message}\n\n{self.system_message_with_context(conversation_history)}'
        else:
            system_message = self.system_message_with_context(conversation_history)
        return {'system_message': system_message, 'user_message': self.build_coordination_context(current_task, conversation_history, agent_summaries), 'tools': self.get_standard_tools(valid_agent_ids)}

    def build_final_presentation_message(self, original_task: str, vote_summary: str, all_answers: Dict[str, str], selected_agent_id: str) -> str:
        """Build final presentation message for winning agent."""
        answers_section = 'All answers provided during coordination:\n'
        for agent_id, answer in all_answers.items():
            marker = ' (YOUR ANSWER)' if agent_id == selected_agent_id else ''
            answers_section += f'\n{agent_id}{marker}: "{answer}"\n'
        return f'{self.format_original_message(original_task)}\n\nVOTING RESULTS:\n{vote_summary}\n\n{answers_section}\n\nBased on the coordination process above, present your final answer:'

    def add_enforcement_message(self, conversation_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Add enforcement message to existing conversation (Case 3)."""
        messages = conversation_messages.copy()
        messages.append({'role': 'user', 'content': self.enforcement_message()})
        return messages

    def command_execution_system_message(self) -> str:
        """Generate concise command execution instructions when command line execution is enabled."""
        parts = ['## Command Execution']
        parts.append('You can run command line commands using the `execute_command` tool.\n')
        parts.append('If a `.venv` directory exists in your workspace, it will be automatically used.')
        return '\n'.join(parts)

    def filesystem_system_message(self, main_workspace: Optional[str]=None, temp_workspace: Optional[str]=None, context_paths: Optional[List[Dict[str, str]]]=None, previous_turns: Optional[List[Dict[str, Any]]]=None, workspace_prepopulated: bool=False, enable_image_generation: bool=False, agent_answers: Optional[Dict[str, str]]=None, enable_command_execution: bool=False) -> str:
        """Generate filesystem access instructions for agents with filesystem support.

        Args:
            main_workspace: Path to agent's main workspace
            temp_workspace: Path to shared reference workspace
            context_paths: List of context paths with permissions
            previous_turns: List of previous turn metadata
            workspace_prepopulated: Whether workspace is pre-populated
            enable_image_generation: Whether image generation is enabled
            agent_answers: Dict of agent answers (keys are agent IDs) to show workspace structure
            enable_command_execution: Whether command line execution is enabled
        """
        if 'filesystem_system_message' in self._template_overrides:
            return str(self._template_overrides['filesystem_system_message'])
        parts = ['## Filesystem Access']
        parts.append('Your working directory is set to your workspace, so all relative paths in your file operations will be resolved from there. This ensures each agent works in isolation while having access to shared references. Only include in your workspace files that should be used in your answer.\n')
        if main_workspace:
            workspace_note = f'**Your Workspace**: `{main_workspace}` - Write actual files here using file tools. All your file operations will be relative to this directory.'
            if workspace_prepopulated:
                workspace_note += " **Note**: Your workspace already contains a writable copy of the previous turn's results - you can modify or build upon these files. The original unmodified version is also available as a read-only context path if you need to reference what was originally there."
            parts.append(workspace_note)
        if temp_workspace:
            workspace_tree = f'**Shared Reference**: `{temp_workspace}` - Contains previous answers from all agents (read/execute-only)\n'
            if agent_answers:
                agent_mapping = {}
                for i, agent_id in enumerate(sorted(agent_answers.keys()), 1):
                    agent_mapping[agent_id] = f'agent{i}'
                workspace_tree += '   Available agent workspaces:\n'
                agent_items = list(agent_mapping.items())
                for idx, (agent_id, anon_id) in enumerate(agent_items):
                    is_last = idx == len(agent_items) - 1
                    prefix = '   └── ' if is_last else '   ├── '
                    workspace_tree += f'{prefix}{temp_workspace}/{anon_id}/\n'
            workspace_tree += '   - To improve upon existing answers: Copy files from Shared Reference to your workspace using `copy_file` or `copy_directory` tools, then modify them\n   - These correspond directly to the answers shown in the CURRENT ANSWERS section\n   - However, not all workspaces may have a matching answer (e.g., if an agent was in the middle of working but restarted before submitting an answer). So, it is wise to check the actual files in the Shared Reference, not rely solely on the CURRENT ANSWERS section.\n'
            parts.append(workspace_tree)
        if context_paths:
            has_target = any((p.get('will_be_writable', False) for p in context_paths))
            has_readonly_context = any((not p.get('will_be_writable', False) and p.get('permission') == 'read' for p in context_paths))
            if has_target:
                parts.append("\n**Important Context**: If the user asks about improving, fixing, debugging, or understanding an existing code/project (e.g., 'Why is this code not working?', 'Fix this bug', 'Add feature X'), they are referring to the Target Path below. First READ the existing files from that path to understand what's there, then make your changes based on that codebase. Final deliverables must end up there.\n")
            elif has_readonly_context:
                parts.append("\n**Important Context**: If the user asks about debugging or understanding an existing code/project (e.g., 'Why is this code not working?', 'Explain this bug'), they are referring to (one of) the Context Path(s) below. Read then provide analysis/explanation based on that codebase - you cannot modify it directly.\n")
            for path_config in context_paths:
                path = path_config.get('path', '')
                permission = path_config.get('permission', 'read')
                will_be_writable = path_config.get('will_be_writable', False)
                if path:
                    if permission == 'read' and will_be_writable:
                        parts.append(f'**Target Path**: `{path}` (read-only now, write access later) - This is where your changes will be delivered. Work in your workspace first, then the final presenter will place or update files DIRECTLY into `{path}` using the FULL ABSOLUTE PATH.')
                    elif permission == 'write':
                        parts.append(f'**Target Path**: `{path}` (write access) - This is where your changes must be delivered. First, ensure you place your answer in your workspace, then copy/write files DIRECTLY into `{path}` using FULL ABSOLUTE PATH (not relative paths). Files must go directly into the target path itself (e.g., `{path}/file.txt`), NOT into a `.massgen/` subdirectory within it.')
                    else:
                        parts.append(f'**Context Path**: `{path}` (read-only) - Use FULL ABSOLUTE PATH when reading.')
        if previous_turns:
            parts.append("\n**Note**: This is a multi-turn conversation. Each User/Assistant exchange in the conversation history represents one turn. The workspace from each turn is available as a read-only context path listed above (e.g., turn 1's workspace is at the path ending in `/turn_1/workspace`).")
        parts.append('\n**Task Handling Priority**: When responding to user requests, follow this priority order:\n1. **Use MCP Tools First**: If you have specialized MCP tools available, call them DIRECTLY to complete the task\n   - Save any outputs/artifacts from MCP tools to your workspace\n2. **Write Code If Needed**: If MCP tools cannot complete the task, write and execute code\n3. **Create Other Files**: Create configs, documents, or other deliverables as needed\n4. **Text Response Otherwise**: If no tools or files are needed, provide a direct text answer\n\n**Important**: Do NOT ask the user for clarification or additional input. Make reasonable assumptions and proceed with sensible defaults. You will not receive user feedback, so complete the task autonomously based on the original request.\n')
        new_answer_guidance = '\n**New Answer**: When calling `new_answer`:\n'
        if enable_command_execution:
            new_answer_guidance += '- If you executed commands (e.g., running tests), explain the results in your answer (what passed, what failed, what the output shows)\n'
        new_answer_guidance += '- If you created files, list your cwd and file paths (but do NOT paste full file contents)\n'
        new_answer_guidance += '- If providing a text response, include your analysis/explanation in the `content` field\n'
        parts.append(new_answer_guidance)
        parts.append('**Workspace Cleanup**: Before submitting your answer with `new_answer`, ensure that your workspace contains only the files relevant to your final answer.\n')
        parts.append("**Comparison Tools**: Use `compare_directories` to see differences between two directories (e.g., comparing your workspace to another agent's workspace or a previous version), or `compare_files` to see line-by-line diffs between two files. These read-only tools help you understand what changed, build upon existing work effectively, or verify solutions before voting.\n")
        parts.append("**Evaluation**: When evaluating agents' answers, do NOT base your decision solely on the answer text. Instead, read and verify the actual files in their workspaces (via Shared Reference) to ensure the work matches their claims.\n")
        if enable_command_execution:
            command_exec_message = self.command_execution_system_message()
            parts.append(f'\n{command_exec_message}')
        return '\n'.join(parts)

def evaluation_system_message(self) -> str:
    """Standard evaluation system message for all cases."""
    if 'evaluation_system_message' in self._template_overrides:
        return str(self._template_overrides['evaluation_system_message'])
    import time
    return f'You are evaluating answers from multiple agents for final response to a message.\nDifferent agents may have different builtin tools and capabilities.\nDoes the best CURRENT ANSWER address the ORIGINAL MESSAGE well?\n\nIf YES, use the `vote` tool to record your vote and skip the `new_answer` tool.\nOtherwise, digest existing answers, combine their strengths, and do additional work to address their weaknesses,\nthen use the `new_answer` tool to record a better answer to the ORIGINAL MESSAGE.\nMake sure you actually call `vote` or `new_answer` (in tool call format).\n\n*Note*: The CURRENT TIME is **{time.strftime('%Y-%m-%d %H:%M:%S')}**.'

def format_current_answers_empty(self) -> str:
    """Format current answers section when no answers exist (Case 1)."""
    if 'format_current_answers_empty' in self._template_overrides:
        return str(self._template_overrides['format_current_answers_empty'])
    return '<CURRENT ANSWERS from the agents>\n(no answers available yet)\n<END OF CURRENT ANSWERS>'

def enforcement_message(self) -> str:
    """Enforcement message for Case 3 (non-workflow responses)."""
    if 'enforcement_message' in self._template_overrides:
        return str(self._template_overrides['enforcement_message'])
    return 'Finish your work above by making a tool call of `vote` or `new_answer`. Make sure you actually call the tool.'

def final_presentation_system_message(self, original_system_message: Optional[str]=None, enable_image_generation: bool=False, enable_audio_generation: bool=False, has_irreversible_actions: bool=False, enable_command_execution: bool=False) -> str:
    """System message for final answer presentation by winning agent.

        Args:
            original_system_message: The agent's original system message to preserve
            enable_image_generation: Whether image generation is enabled
            enable_audio_generation: Whether audio generation is enabled
            has_irreversible_actions: Whether agent has write access to context paths (requires actual file delivery)
            enable_command_execution: Whether command execution is enabled for this agent
        """
    if 'final_presentation_system_message' in self._template_overrides:
        return str(self._template_overrides['final_presentation_system_message'])
    presentation_instructions = 'You have been selected as the winning presenter in a coordination process.\nPresent the best possible coordinated answer by combining the strengths from all participants.\n\n'
    if enable_image_generation:
        presentation_instructions += 'For image generation tasks:\n- Extract image paths from the existing answer and resolve them in the shared reference.\n- Gather all agent-produced images (ignore non-existent files).\n- MUST call the generate-image tool with these input images to synthesize one final image combining their strengths.\n- MUST save the final outputand output the saved path.\n'
    if enable_audio_generation:
        presentation_instructions += 'For audio generation tasks:\n- Extract audio paths from the existing answer and resolve them in the shared reference.\n- Gather ALL audio files produced by EVERY agent (ignore non-existent files).\n  IMPORTANT: You MUST call the generate_text_with_input_audio tool to obtain transcriptions\n  for EACH AND EVERY audio file from ALL agents - no audio should be skipped or overlooked.\n- MUST combine the strengths of all transcriptions into one final detailed transcription that captures the best elements from each.\n- MUST use the convert_text_to_audio tool to convert this final transcription to a new audio file and save it, then output the saved path.\n'
    if has_irreversible_actions:
        presentation_instructions += '### Write Access to Target Path:\n\nReminder: File Delivery Required. You should first place your final answer in your workspace. However, note your workspace is NOT the final destination. You MUST copy/write files to the Target Path using FULL ABSOLUTE PATHS. Then, clean up this Target Path by deleting any outdated or unused files. Then, you must ALWAYS verify that the Target Path contains the correct final files, as no other agents were allowed to write to this path.\n'
    if enable_command_execution:
        presentation_instructions += '### Package Dependencies:\n\nCreate a `requirements.txt` file listing all Python packages needed to run your code. This helps users reproduce your work later. Include only the packages you actually used in your solution.\n'
    if original_system_message:
        return f'{original_system_message}\n\n{presentation_instructions}'
    else:
        return presentation_instructions

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

def get_mcp_filesystem_config(self) -> Dict[str, Any]:
    """
        Generate MCP filesystem server configuration.

        Returns:
            Dictionary with MCP server configuration for filesystem access
        """
    paths = self.path_permission_manager.get_mcp_filesystem_paths()
    config = {'name': 'filesystem', 'type': 'stdio', 'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-filesystem'] + paths, 'cwd': str(self.cwd), 'exclude_tools': ['read_media_file']}
    return config

def get_claude_code_hooks_config(self) -> Dict[str, Any]:
    """
        Get Claude Agent SDK hooks configuration.

        Returns:
            Hooks configuration dict for ClaudeAgentOptions
        """
    return self.path_permission_manager.get_claude_code_hooks_config()

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

def display_with_native_pager(console: Console, content_items: List[Any], title: str='') -> None:
    """
    Use the system's native pager (less/more) for better scrolling support.
    Falls back to simple display if pager is not available.
    """
    import subprocess
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            if title:
                tmp_file.write(f'{title}\n')
                tmp_file.write('=' * len(title) + '\n\n')
            for item in content_items:
                if hasattr(item, '__rich_console__'):
                    with console.capture() as capture:
                        console.print(item)
                    tmp_file.write(capture.get() + '\n')
                else:
                    tmp_file.write(str(item) + '\n')
            tmp_file.write('\n' + '=' * 80 + '\n')
            tmp_file.write("Press 'q' to quit, arrow keys or j/k to scroll\n")
            tmp_file_path = tmp_file.name
        if sys.platform == 'darwin':
            pager_cmd = ['less', '-R', '-S']
        else:
            pager_cmd = ['less', '-R']
        try:
            subprocess.run(pager_cmd + [tmp_file_path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(['more', tmp_file_path], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                display_scrollable_content_macos(console, content_items, title)
        try:
            os.unlink(tmp_file_path)
        except OSError:
            pass
    except Exception:
        display_scrollable_content_macos(console, content_items, title)

class CoordinationTableBuilder:

    def __init__(self, data: Union[List[Dict[str, Any]], Dict[str, Any]]):
        if isinstance(data, dict) and 'events' in data:
            self.events = data['events']
            self.session_metadata = data.get('session_metadata', {})
        else:
            self.events = data if isinstance(data, list) else []
            self.session_metadata = {}
        self.agents = self._extract_agents()
        self.agent_mapping = self._create_agent_mapping()
        self.agent_answers = self._extract_answer_previews()
        self.final_winner = self._find_final_winner()
        self.final_round_num = self._find_final_round_number()
        self.agent_vote_rounds = self._track_vote_rounds()
        self.rounds = self._process_events()
        self.user_question = self._extract_user_question()

    def _extract_agents(self) -> List[str]:
        """Extract unique agent IDs from events using original orchestrator order"""
        metadata_agents = self.session_metadata.get('agent_ids', [])
        if metadata_agents:
            return list(metadata_agents)
        agents = set()
        for event in self.events:
            agent_id = event.get('agent_id')
            if agent_id and agent_id not in [None, 'null']:
                agents.add(agent_id)
        return sorted(list(agents))

    def _create_agent_mapping(self) -> Dict[str, str]:
        """Create explicit mapping from agent_id to agent_number for answer labels"""
        mapping = {}
        for i, agent_id in enumerate(self.agents, 1):
            mapping[agent_id] = str(i)
        return mapping

    def _extract_user_question(self) -> str:
        """Extract the user question from session metadata"""
        return str(self.session_metadata.get('user_prompt', 'No user prompt found'))

    def _extract_answer_previews(self) -> Dict[str, str]:
        """Extract the actual answer text for each agent using explicit mapping"""
        answers = {}
        for event in self.events:
            if event['event_type'] == 'final_agent_selected':
                context = event.get('context', {})
                answers_for_context = context.get('answers_for_context', {})
                for label, answer in answers_for_context.items():
                    if label in self.agents:
                        answers[label] = answer
                    elif label.startswith('agent') and '.' in label:
                        try:
                            agent_num = label.split('.')[0][5:]
                            for agent_id, mapped_num in self.agent_mapping.items():
                                if mapped_num == agent_num:
                                    answers[agent_id] = answer
                                    break
                        except (IndexError, ValueError):
                            continue
        return answers

    def _find_final_winner(self) -> Optional[str]:
        """Find which agent was selected as the final winner"""
        for event in self.events:
            if event['event_type'] == 'final_agent_selected':
                agent_id = event.get('agent_id')
                return agent_id if agent_id is not None else None
        return None

    def _find_final_round_number(self) -> Optional[int]:
        """Find which round number is the final round"""
        for event in self.events:
            if event['event_type'] == 'final_round_start':
                context = event.get('context', {})
                round_num = context.get('round', context.get('final_round'))
                return int(round_num) if round_num is not None else None
        for event in self.events:
            if event['event_type'] == 'final_answer':
                context = event.get('context', {})
                round_num = context.get('round')
                return int(round_num) if round_num is not None else None
        return None

    def _track_vote_rounds(self) -> Dict[str, int]:
        """Track which round each agent cast their vote"""
        vote_rounds = {}
        for event in self.events:
            if event['event_type'] == 'vote_cast':
                agent_id = event.get('agent_id')
                context = event.get('context', {})
                round_num = context.get('round', 0)
                if agent_id:
                    vote_rounds[agent_id] = round_num
        return vote_rounds

    def _process_events(self) -> List[RoundData]:
        """Process events into rounds with proper organization"""
        all_rounds = set()
        for event in self.events:
            context = event.get('context', {})
            round_num = context.get('round', 0)
            all_rounds.add(round_num)
        regular_rounds = sorted(all_rounds - {self.final_round_num} if self.final_round_num else all_rounds)
        rounds = {}
        for r in regular_rounds:
            rounds[r] = {agent: AgentState(round=r) for agent in self.agents}
        if self.final_round_num is not None:
            rounds[self.final_round_num] = {agent: AgentState(round=self.final_round_num) for agent in self.agents}
        for event in self.events:
            event_type = event['event_type']
            agent_id = event.get('agent_id')
            context = event.get('context', {})
            if agent_id and agent_id in self.agents:
                round_num = context.get('round', 0)
                if event_type == 'vote_cast':
                    round_num = context.get('round', 0)
                elif event_type == 'new_answer':
                    round_num = context.get('round', 0)
                elif event_type == 'restart_completed':
                    round_num = context.get('agent_round', context.get('round', 0))
                elif event_type == 'final_answer':
                    round_num = self.final_round_num if self.final_round_num else context.get('round', 0)
                if round_num in rounds:
                    agent_state = rounds[round_num][agent_id]
                    if event_type == 'context_received':
                        labels = context.get('available_answer_labels', [])
                        agent_state.context = labels
                    elif event_type == 'new_answer':
                        label = context.get('label')
                        if label:
                            agent_state.current_answer = label
                            if agent_id in self.agent_answers:
                                agent_state.answer_preview = self.agent_answers[agent_id]
                    elif event_type == 'vote_cast':
                        agent_state.vote = context.get('voted_for_label')
                        agent_state.vote_reason = context.get('reason')
                        agent_state.has_voted = True
                    elif event_type == 'final_answer':
                        agent_state.has_final_answer = True
                        label = context.get('label')
                        agent_state.current_answer = f'Final answer provided ({label})'
                        agent_state.is_final = True
                        if agent_id in self.agent_answers:
                            agent_state.answer_preview = self.agent_answers[agent_id]
                            agent_state.current_answer = self.agent_answers[agent_id]
                    elif event_type == 'final_agent_selected':
                        agent_state.is_selected_winner = True
                    elif event_type == 'status_change':
                        status = event.get('details', '').replace('Changed to status: ', '')
                        agent_state.status = status
        if self.final_winner and self.final_round_num in rounds:
            for agent in self.agents:
                if agent != self.final_winner:
                    rounds[self.final_round_num][agent].status = 'completed'
        round_list = []
        for r in regular_rounds:
            round_type = f'R{r}'
            round_list.append(RoundData(r, round_type, rounds.get(r, {agent: AgentState() for agent in self.agents})))
        if self.final_round_num is not None and self.final_round_num in rounds:
            round_list.append(RoundData(self.final_round_num, 'FINAL', rounds[self.final_round_num]))
        return round_list

    def _format_cell(self, content: str, width: int) -> str:
        """Format content to fit within cell width, centered"""
        if not content:
            return ' ' * width
        if len(content) <= width:
            return content.center(width)
        else:
            truncated = content[:width - 3] + '...'
            return truncated.center(width)

    def _build_agent_cell_content(self, agent_state: AgentState, round_type: str, agent_id: str, round_num: int) -> List[str]:
        """Build the content for an agent's cell in a round"""
        lines = []
        show_context = agent_state.current_answer and (not agent_state.vote) or agent_state.has_final_answer or agent_state.status in ['streaming', 'answering']
        if round_type == 'FINAL' and agent_state.status == 'completed':
            show_context = False
        if show_context:
            if agent_state.context:
                context_str = f'Context: [{', '.join(agent_state.context)}]'
            else:
                context_str = 'Context: []'
            lines.append(context_str)
        if agent_state.vote:
            if agent_state.context:
                lines.append(f'Context: [{', '.join(agent_state.context)}]')
            lines.append(f'VOTE: {agent_state.vote}')
            if agent_state.vote_reason:
                reason = agent_state.vote_reason[:47] + '...' if len(agent_state.vote_reason) > 50 else agent_state.vote_reason
                lines.append(f'Reason: {reason}')
        elif round_type == 'FINAL':
            if agent_state.has_final_answer:
                lines.append(f'FINAL ANSWER: {agent_state.current_answer}')
                if agent_state.answer_preview:
                    clean_preview = agent_state.answer_preview.replace('\n', ' ').strip()
                    lines.append(f'Preview: {clean_preview}')
                else:
                    lines.append('Preview: [Answer not available]')
            elif agent_state.status == 'completed':
                lines.append('(completed)')
            else:
                lines.append('(waiting)')
        elif agent_state.current_answer and (not agent_state.vote):
            lines.append(f'NEW ANSWER: {agent_state.current_answer}')
            if agent_state.answer_preview:
                clean_preview = agent_state.answer_preview.replace('\n', ' ').strip()
                lines.append(f'Preview: {clean_preview}')
            else:
                lines.append('Preview: [Answer not available]')
        elif agent_state.status in ['streaming', 'answering']:
            lines.append('(answering)')
        elif agent_state.status == 'voted':
            lines.append('(voted)')
        elif agent_state.status == 'answered':
            lines.append('(answered)')
        else:
            lines.append('(waiting)')
        return lines

    def generate_event_table(self) -> str:
        """Generate an event-driven formatted table"""
        num_agents = len(self.agents)
        if num_agents <= 2:
            cell_width = 60
        elif num_agents == 3:
            cell_width = 40
        elif num_agents == 4:
            cell_width = 30
        else:
            cell_width = 25
        total_width = 10 + (cell_width + 1) * num_agents + 1
        lines = []

        def add_separator(style: str='-') -> None:
            lines.append('|' + style * 10 + '+' + (style * cell_width + '+') * num_agents)
        lines.extend(self._create_legend_section(cell_width))
        lines.append('+' + '-' * (total_width - 2) + '+')
        header = '|   Event  |'
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num} ({agent})'
            header += self._format_cell(agent_name, cell_width) + '|'
        lines.append(header)
        lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * num_agents)
        question_row = '|   USER   |'
        question_width = cell_width * num_agents + (num_agents - 1)
        question_text = self.user_question.center(question_width)
        question_row += question_text + '|'
        lines.append(question_row)
        lines.append('|' + '=' * 10 + '+' + ('=' * cell_width + '+') * num_agents)
        agent_states: Dict[str, Dict[str, Any]] = {agent: {'status': 'idle', 'context': [], 'answer': None, 'vote': None, 'preview': None, 'last_streaming_logged': False} for agent in self.agents}
        event_num = 1
        for event in self.events:
            event_type = event['event_type']
            agent_id = event.get('agent_id')
            context = event.get('context', {})
            if not agent_id or agent_id not in self.agents:
                continue
            if event_type == 'status_change':
                status = event.get('details', '').replace('Changed to status: ', '')
                old_status = agent_states[agent_id]['status']
                agent_states[agent_id]['status'] = status
                if status in ['streaming', 'answering']:
                    if old_status == 'voted':
                        pass
                    elif old_status not in ['streaming', 'answering'] or not agent_states[agent_id]['last_streaming_logged']:
                        event_lines = []
                        context = agent_states[agent_id]['context']
                        if context:
                            if isinstance(context, list):
                                context_str = ', '.join((str(c) for c in context))
                            else:
                                context_str = str(context)
                            event_lines.append(f'📋 Context: [{context_str}]')
                        else:
                            event_lines.append('📋 Context: []')
                        event_lines.append(f'💭 Started {status}')
                        lines.extend(self._create_multi_line_event_row(event_num, agent_id, event_lines, agent_states, cell_width))
                        add_separator('-')
                        agent_states[agent_id]['last_streaming_logged'] = True
                        event_num += 1
                elif status not in ['streaming', 'answering']:
                    agent_states[agent_id]['last_streaming_logged'] = False
            elif event_type == 'context_received':
                labels = context.get('available_answer_labels', [])
                agent_states[agent_id]['context'] = labels
            elif event_type == 'restart_triggered':
                agent_num = self.agent_mapping.get(agent_id, '?')
                agent_name = f'Agent {agent_num}'
                lines.extend(self._create_system_row(f'🔁 {agent_name} RESTART TRIGGERED', cell_width))
                event_num += 1
            elif event_type == 'restart_completed':
                agent_round = context.get('agent_round', context.get('round', 0))
                lines.extend(self._create_event_row(event_num, agent_id, f'✅ RESTART COMPLETED (Restart {agent_round})', agent_states, cell_width))
                add_separator('-')
                event_num += 1
                agent_states[agent_id]['last_streaming_logged'] = False
            elif event_type == 'new_answer':
                label = context.get('label')
                if label:
                    agent_states[agent_id]['answer'] = label
                    agent_states[agent_id]['status'] = 'answered'
                    agent_states[agent_id]['last_streaming_logged'] = False
                    preview = ''
                    if agent_id in self.agent_answers:
                        preview = self.agent_answers[agent_id]
                        agent_states[agent_id]['preview'] = preview
                    event_lines = []
                    event_lines.append(f'✨ NEW ANSWER: {label}')
                    if preview:
                        clean_preview = preview.replace('\n', ' ').strip()
                        event_lines.append(f'👁️  Preview: {clean_preview}')
                    lines.extend(self._create_multi_line_event_row(event_num, agent_id, event_lines, agent_states, cell_width))
                    add_separator('-')
                    event_num += 1
            elif event_type == 'vote_cast':
                vote = context.get('voted_for_label')
                reason = context.get('reason', '')
                if vote:
                    agent_states[agent_id]['vote'] = vote
                    agent_states[agent_id]['status'] = 'voted'
                    agent_states[agent_id]['last_streaming_logged'] = False
                    event_lines = []
                    event_lines.append(f'🗳️  VOTE: {vote}')
                    if reason:
                        clean_reason = reason.replace('\n', ' ').strip()
                        reason_str = clean_reason[:50] + '...' if len(clean_reason) > 50 else clean_reason
                        event_lines.append(f'💭 Reason: {reason_str}')
                    lines.extend(self._create_multi_line_event_row(event_num, agent_id, event_lines, agent_states, cell_width))
                    add_separator('-')
                    event_num += 1
            elif event_type == 'final_agent_selected':
                agent_num = self.agent_mapping.get(agent_id, '?')
                winner_name = f'Agent {agent_num}'
                lines.extend(self._create_system_row(f'🏆 {winner_name} selected as winner', cell_width))
                for other_agent in self.agents:
                    if other_agent != agent_id:
                        agent_states[other_agent]['status'] = 'completed'
            elif event_type == 'final_answer':
                label = context.get('label')
                if label:
                    agent_states[agent_id]['status'] = 'final'
                    if not agent_states[agent_id]['preview'] and agent_id in self.agent_answers:
                        agent_states[agent_id]['preview'] = self.agent_answers[agent_id]
                    event_lines = []
                    event_lines.append(f'🎯 FINAL ANSWER: {label}')
                    if agent_states[agent_id]['preview']:
                        preview_text = str(agent_states[agent_id]['preview'])
                        clean_preview = preview_text.replace('\n', ' ').strip()
                        event_lines.append(f'👁️  Preview: {clean_preview}')
                    lines.extend(self._create_multi_line_event_row(event_num, agent_id, event_lines, agent_states, cell_width))
                    add_separator('-')
                    event_num += 1
        lines.extend(self._create_summary_section(agent_states, cell_width))
        lines.append('+' + '-' * (total_width - 2) + '+')
        return '\n'.join(lines)

    def _create_event_row(self, event_num: int, active_agent: str, event_description: str, agent_states: dict, cell_width: int) -> list:
        """Create a table row for a single event"""
        row = '|'
        event_label = f'    E{event_num}   '
        row += event_label[-10:].rjust(10) + '|'
        for agent in self.agents:
            if agent == active_agent:
                cell_content = event_description
            else:
                status = agent_states[agent]['status']
                if status in ['streaming', 'answering']:
                    cell_content = f'🔄 ({status})'
                elif status == 'voted':
                    cell_content = '✅ (voted)'
                elif status == 'answered':
                    if agent_states[agent]['answer']:
                        cell_content = f'✅ Answered: {agent_states[agent]['answer']}'
                    else:
                        cell_content = '✅ (answered)'
                elif status == 'completed':
                    cell_content = '✅ (completed)'
                elif status == 'final':
                    cell_content = '🎯 (final answer given)'
                elif status == 'idle':
                    cell_content = '⏳ (waiting)'
                else:
                    cell_content = f'({status})'
            row += self._format_cell(cell_content, cell_width) + '|'
        return [row]

    def _create_multi_line_event_row(self, event_num: int, active_agent: str, event_lines: list, agent_states: dict, cell_width: int) -> list:
        """Create multiple table rows for a single event with multiple lines of content"""
        rows = []
        for line_idx, event_line in enumerate(event_lines):
            row = '|'
            if line_idx == 0:
                event_label = f'    E{event_num}   '
                row += event_label[-10:].rjust(10) + '|'
            else:
                row += ' ' * 10 + '|'
            for agent in self.agents:
                if agent == active_agent:
                    cell_content = event_line
                elif line_idx == 0:
                    status = agent_states[agent]['status']
                    if status in ['streaming', 'answering']:
                        cell_content = f'🔄 ({status})'
                    elif status == 'voted':
                        cell_content = '✅ (voted)'
                    elif status == 'answered':
                        if agent_states[agent]['answer']:
                            cell_content = f'✅ Answered: {agent_states[agent]['answer']}'
                        else:
                            cell_content = '✅ (answered)'
                    elif status == 'completed':
                        cell_content = '✅ (completed)'
                    elif status == 'final':
                        cell_content = '🎯 (final answer given)'
                    elif status == 'idle':
                        cell_content = '⏳ (waiting)'
                    else:
                        cell_content = f'({status})'
                else:
                    cell_content = ''
                row += self._format_cell(cell_content, cell_width) + '|'
            rows.append(row)
        return rows

    def _create_system_row(self, message: str, cell_width: int) -> list:
        """Create a system announcement row that spans all columns"""
        total_width = 10 + (cell_width + 1) * len(self.agents) + 1
        separator = '|' + '-' * 10 + '+' + ('-' * cell_width + '+') * len(self.agents)
        message_width = total_width - 3
        message_row = '|' + message.center(message_width) + '|'
        separator2 = '|' + '-' * 10 + '+' + ('-' * cell_width + '+') * len(self.agents)
        return [separator, message_row, separator2]

    def _create_summary_section(self, agent_states: dict, cell_width: int) -> list:
        """Create summary statistics section"""
        lines = []
        total_answers = sum((1 for agent in self.agents if agent_states[agent]['answer']))
        total_votes = sum((1 for agent in self.agents if agent_states[agent]['vote']))
        total_restarts = len([e for e in self.events if e['event_type'] == 'restart_completed'])
        agent_stats = {}
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            agent_stats[agent_name] = {'answers': 1 if agent_states[agent]['answer'] else 0, 'votes': 1 if agent_states[agent]['vote'] else 0, 'final_status': agent_states[agent]['status']}
        for event in self.events:
            if event['event_type'] == 'restart_completed' and event.get('agent_id') in self.agents:
                agent_id = event['agent_id']
                agent_num = self.agent_mapping.get(agent_id, '?')
                agent_name = f'Agent {agent_num}'
                if agent_name not in agent_stats:
                    agent_stats[agent_name] = {'restarts': 0}
                if 'restarts' not in agent_stats[agent_name]:
                    agent_stats[agent_name]['restarts'] = 0
                agent_stats[agent_name]['restarts'] += 1
        separator = '|' + '=' * 10 + '+' + ('=' * cell_width + '+') * len(self.agents)
        lines.append(separator)
        summary_header = '|  SUMMARY |'
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            summary_header += self._format_cell(agent_name, cell_width) + '|'
        lines.append(summary_header)
        lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * len(self.agents))
        answers_row = '| Answers  |'
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            count = agent_stats.get(agent_name, {}).get('answers', 0)
            answers_row += self._format_cell(f'{count} answer{('s' if count != 1 else '')}', cell_width) + '|'
        lines.append(answers_row)
        votes_row = '| Votes    |'
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            count = agent_stats.get(agent_name, {}).get('votes', 0)
            votes_row += self._format_cell(f'{count} vote{('s' if count != 1 else '')}', cell_width) + '|'
        lines.append(votes_row)
        restarts_row = '| Restarts |'
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            count = agent_stats.get(agent_name, {}).get('restarts', 0)
            restarts_row += self._format_cell(f'{count} restart{('s' if count != 1 else '')}', cell_width) + '|'
        lines.append(restarts_row)
        status_row = '| Status   |'
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            status = agent_states[agent]['status']
            if status == 'final':
                display = '🏆 Winner'
            elif status == 'completed':
                display = '✅ Completed'
            elif status == 'voted':
                display = '✅ Voted'
            else:
                display = f'({status})'
            status_row += self._format_cell(display, cell_width) + '|'
        lines.append(status_row)
        lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * len(self.agents))
        totals_row = '| TOTALS   |'
        total_width = cell_width * len(self.agents) + (len(self.agents) - 1)
        totals_content = f'{total_answers} answers, {total_votes} votes, {total_restarts} restarts'
        winner_name = None
        for agent in self.agents:
            if agent_states[agent]['status'] == 'final':
                winner_name = f'Agent{agent.split('_')[-1]}' if '_' in agent else agent
                break
        if winner_name:
            totals_content += f' → {winner_name} selected'
        totals_row += totals_content.center(total_width) + '|'
        lines.append(totals_row)
        return lines

    def _get_legend_content(self) -> dict:
        """Get legend content as structured data to be formatted by different displays"""
        return {'event_symbols': [('💭 Started streaming', 'Agent begins thinking/processing'), ('✨ NEW ANSWER', 'Agent provides a labeled answer'), ('🗳️  VOTE', 'Agent votes for an answer'), ('💭 Reason', 'Reasoning behind the vote'), ('👁️  Preview', 'Content of the answer'), ('🔁 RESTART TRIGGERED', 'Agent requests to restart'), ('✅ RESTART COMPLETED', 'Agent finishes restart'), ('🎯 FINAL ANSWER', 'Winner provides final response'), ('🏆 Winner selected', 'System announces winner')], 'status_symbols': [('💭 (streaming)', 'Currently thinking/processing'), ('⏳ (waiting)', 'Idle, waiting for turn'), ('✅ (answered)', 'Has provided an answer'), ('✅ (voted)', 'Has cast a vote'), ('✅ (completed)', 'Task completed'), ('🎯 (final answer given)', 'Winner completed final answer')], 'terms': [('Context', 'Available answer options agent can see'), ('Restart', 'Agent starts over (clears memory)'), ('Event', 'Chronological action in the coordination'), ('Answer Labels', "Each answer gets a unique ID (agent1.1, agent2.1, etc.)\n                  Format: agent{N}.{attempt} where N=agent number, attempt=new answer number\n                  Example: agent1.1 = Agent1's 1st answer, agent2.1 = Agent2's 1st answer"), ('agent1.final', "Special label for the winner's final answer")]}

    def _create_legend_section(self, cell_width: int) -> list:
        """Create legend/explanation section at the top for plain text"""
        lines = []
        legend_data = self._get_legend_content()
        lines.append('')
        lines.append('Multi-Agent Coordination Events Log')
        lines.append('=' * 50)
        lines.append('')
        lines.append('📋 EVENT SYMBOLS:')
        for symbol, description in legend_data['event_symbols']:
            padded = f'  {symbol}'.ljust(28)
            lines.append(f'{padded}- {description}')
        lines.append('')
        lines.append('📊 STATUS SYMBOLS:')
        for symbol, description in legend_data['status_symbols']:
            padded = f'  {symbol}'.ljust(28)
            lines.append(f'{padded}- {description}')
        lines.append('')
        lines.append('📖 TERMS:')
        for term, description in legend_data['terms']:
            if '\n' in description:
                first_line = description.split('\n')[0]
                lines.append(f'  {term.ljust(13)} - {first_line}')
                for line in description.split('\n')[1:]:
                    lines.append(f'  {line}')
            else:
                lines.append(f'  {term.ljust(13)} - {description}')
        lines.append('')
        return lines

    def generate_table(self) -> str:
        """Generate the formatted table"""
        num_agents = len(self.agents)
        if num_agents <= 2:
            cell_width = 60
        elif num_agents == 3:
            cell_width = 40
        elif num_agents == 4:
            cell_width = 30
        else:
            cell_width = 25
        total_width = 10 + (cell_width + 1) * num_agents + 1
        lines = []
        lines.append('+' + '-' * (total_width - 2) + '+')
        header = '|  Round   |'
        for agent in self.agents:
            agent_name = agent
            header += self._format_cell(agent_name, cell_width) + '|'
        lines.append(header)
        lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * num_agents)
        question_row = '|   USER   |'
        question_width = cell_width * num_agents + (num_agents - 1)
        question_text = self.user_question.center(question_width)
        question_row += question_text + '|'
        lines.append(question_row)
        lines.append('|' + '=' * 10 + '+' + ('=' * cell_width + '+') * num_agents)
        for i, round_data in enumerate(self.rounds):
            agent_contents = {}
            max_lines = 0
            for agent in self.agents:
                content = self._build_agent_cell_content(round_data.agent_states[agent], round_data.round_type, agent, round_data.round_num)
                agent_contents[agent] = content
                max_lines = max(max_lines, len(content))
            for line_idx in range(max_lines):
                row = '|'
                if line_idx == 0:
                    if round_data.round_type == 'FINAL':
                        round_label = '  FINAL   '
                    else:
                        round_label = f'   {round_data.round_type}   '
                    row += round_label[-10:].rjust(10) + '|'
                else:
                    row += ' ' * 10 + '|'
                for agent in self.agents:
                    content_lines = agent_contents[agent]
                    if line_idx < len(content_lines):
                        row += self._format_cell(content_lines[line_idx], cell_width)
                    else:
                        row += ' ' * cell_width
                    row += '|'
                lines.append(row)
            if i < len(self.rounds) - 1:
                next_round = self.rounds[i + 1]
                if next_round.round_type == 'FINAL':
                    lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * num_agents)
                    if self.final_winner:
                        agent_number = self.agent_mapping.get(self.final_winner)
                        if agent_number:
                            winner_name = f'Agent {agent_number}'
                        else:
                            winner_name = self.final_winner
                        winner_text = f'{winner_name} selected as winner'
                        winner_width = total_width - 1
                        winner_row = '|' + winner_text.center(winner_width) + '|'
                        lines.append(winner_row)
                    lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * num_agents)
                else:
                    lines.append('|' + '~' * 10 + '+' + ('~' * cell_width + '+') * num_agents)
        lines.append('|' + '-' * 10 + '+' + ('-' * cell_width + '+') * num_agents)
        lines.append('+' + '-' * (total_width - 2) + '+')
        return '\n'.join(lines)

    def _create_rich_legend(self) -> Optional[Any]:
        """Create Rich legend panel using shared legend content"""
        try:
            from rich import box
            from rich.panel import Panel
            from rich.text import Text
        except ImportError:
            return None
        legend_data = self._get_legend_content()
        content = Text()
        content.append('📋 EVENT SYMBOLS:\n', style='bold bright_blue')
        for symbol, description in legend_data['event_symbols']:
            padded = f'  {symbol}'.ljust(28)
            content.append(f'{padded}- {description}\n', style='dim white')
        content.append('\n')
        content.append('📊 STATUS SYMBOLS:\n', style='bold bright_green')
        for symbol, description in legend_data['status_symbols']:
            padded = f'  {symbol}'.ljust(28)
            content.append(f'{padded}- {description}\n', style='dim white')
        content.append('\n')
        content.append('📖 TERMS:\n', style='bold bright_yellow')
        for term, description in legend_data['terms']:
            if '\n' in description:
                lines = description.split('\n')
                content.append(f'  {term.ljust(13)} - {lines[0]}\n', style='dim white')
                for line in lines[1:]:
                    content.append(f'  {line}\n', style='dim white')
            else:
                content.append(f'  {term.ljust(13)} - {description}\n', style='dim white')
        return Panel(content, title='[bold bright_cyan]📋 COORDINATION GUIDE[/bold bright_cyan]', border_style='bright_cyan', box=box.ROUNDED, padding=(1, 2))

    def generate_rich_event_table(self) -> Optional[tuple]:
        """Generate a rich event-driven table with legend

        Returns:
            Tuple of (legend_panel, table) or None if Rich not available
        """
        try:
            from rich import box
            from rich.table import Table
            from rich.text import Text
        except ImportError:
            return None
        legend = self._create_rich_legend()
        table = Table(title='[bold cyan]Multi-Agent Coordination Events[/bold cyan]', box=box.DOUBLE_EDGE, expand=True, show_lines=True)
        table.add_column('Event', style='bold yellow', width=8, justify='center')
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num} ({agent})'
            table.add_column(agent_name, style='white', width=45, justify='center')
        question_row = ['[bold cyan]USER[/bold cyan]']
        question_text = f'[bold white]{self.user_question}[/bold white]'
        for _ in range(len(self.agents)):
            question_row.append(question_text)
        table.add_row(*question_row)
        agent_states: Dict[str, Dict[str, Any]] = {agent: {'status': 'idle', 'context': [], 'answer': None, 'vote': None, 'preview': None, 'last_streaming_logged': False} for agent in self.agents}
        event_num = 1
        for event in self.events:
            event_type = event['event_type']
            agent_id = event.get('agent_id')
            context = event.get('context', {})
            if event_type == 'final_agent_selected':
                agent_num = self.agent_mapping.get(agent_id, '?')
                winner_name = f'Agent {agent_num}'
                winner_row = ['[bold green]🏆[/bold green]']
                winner_text = Text(f'🏆 {winner_name} selected as winner 🏆', style='bold green', justify='center')
                for _ in range(len(self.agents)):
                    winner_row.append(winner_text)
                table.add_row(*winner_row)
                continue
            elif event_type == 'restart_triggered' and agent_id and (agent_id in self.agents):
                agent_num = self.agent_mapping.get(agent_id, '?')
                agent_name = f'Agent {agent_num}'
                restart_row = ['[bold yellow]🔁[/bold yellow]']
                restart_text = Text(f'🔁 {agent_name} RESTART TRIGGERED', style='bold yellow', justify='center')
                for _ in range(len(self.agents)):
                    restart_row.append(restart_text)
                table.add_row(*restart_row)
                continue
            if not agent_id or agent_id not in self.agents:
                continue
            if event_type == 'status_change':
                status = event.get('details', '').replace('Changed to status: ', '')
                old_status = agent_states[agent_id]['status']
                agent_states[agent_id]['status'] = status
                if status in ['streaming', 'answering']:
                    if old_status == 'voted':
                        pass
                    elif old_status not in ['streaming', 'answering'] or not agent_states[agent_id]['last_streaming_logged']:
                        row = self._create_rich_event_row(event_num, agent_id, agent_states, 'streaming_start')
                        if row:
                            table.add_row(*row)
                            event_num += 1
                        agent_states[agent_id]['last_streaming_logged'] = True
            elif event_type == 'context_received':
                labels = context.get('available_answer_labels', [])
                agent_states[agent_id]['context'] = labels
            elif event_type == 'restart_completed':
                agent_round = context.get('agent_round', context.get('round', 0))
                row = self._create_rich_event_row(event_num, agent_id, agent_states, 'restart_completed', agent_round)
                if row:
                    table.add_row(*row)
                    event_num += 1
                agent_states[agent_id]['last_streaming_logged'] = False
            elif event_type == 'new_answer':
                label = context.get('label')
                if label:
                    agent_states[agent_id]['answer'] = label
                    agent_states[agent_id]['status'] = 'answered'
                    agent_states[agent_id]['last_streaming_logged'] = False
                    preview = self.agent_answers.get(agent_id, '')
                    agent_states[agent_id]['preview'] = preview
                    row = self._create_rich_event_row(event_num, agent_id, agent_states, 'new_answer', label, preview)
                    if row:
                        table.add_row(*row)
                        event_num += 1
            elif event_type == 'vote_cast':
                vote = context.get('voted_for_label')
                reason = context.get('reason', '')
                if vote:
                    agent_states[agent_id]['vote'] = vote
                    agent_states[agent_id]['status'] = 'voted'
                    agent_states[agent_id]['last_streaming_logged'] = False
                    row = self._create_rich_event_row(event_num, agent_id, agent_states, 'vote', vote, reason)
                    if row:
                        table.add_row(*row)
                        event_num += 1
            elif event_type == 'final_answer':
                label = context.get('label')
                if label:
                    agent_states[agent_id]['status'] = 'final'
                    preview = agent_states[agent_id].get('preview', '')
                    row = self._create_rich_event_row(event_num, agent_id, agent_states, 'final_answer', label, preview)
                    if row:
                        table.add_row(*row)
                        event_num += 1
        self._add_rich_summary(table, agent_states)
        return (legend, table)

    def _create_rich_event_row(self, event_num: int, active_agent: str, agent_states: Dict[str, Any], event_type: str, *args: Any) -> list:
        """Create a rich table row for an event"""
        row = [f'[bold yellow]E{event_num}[/bold yellow]']
        for agent in self.agents:
            if agent == active_agent:
                if event_type == 'streaming_start':
                    context = agent_states[agent]['context']
                    context_str = f'[dim blue]📋 Context: \\[{', '.join(context)}][/dim blue]\n' if context else '[dim blue]📋 Context: \\[][/dim blue]\n'
                    cell = context_str + '[bold cyan]💭 Started streaming[/bold cyan]'
                elif event_type == 'restart_completed':
                    cell = f'[bold green]✅ RESTART COMPLETED (Restart {args[0]})[/bold green]'
                elif event_type == 'new_answer':
                    label, preview = (args[0], args[1] if len(args) > 1 else '')
                    cell = f'[bold green]✨ NEW ANSWER: {label}[/bold green]'
                    if preview:
                        clean_preview = preview.replace('\n', ' ').strip()
                        preview_truncated = clean_preview[:80] + '...' if len(clean_preview) > 80 else clean_preview
                        cell += f'\n[dim white]👁️  Preview: {preview_truncated}[/dim white]'
                elif event_type == 'vote':
                    vote, reason = (args[0], args[1] if len(args) > 1 else '')
                    cell = f'[bold cyan]🗳️  VOTE: {vote}[/bold cyan]'
                    if reason:
                        clean_reason = reason.replace('\n', ' ').strip()
                        reason_preview = clean_reason[:50] + '...' if len(clean_reason) > 50 else clean_reason
                        cell += f'\n[italic dim]💭 Reason: {reason_preview}[/italic dim]'
                elif event_type == 'final_answer':
                    label, preview = (args[0], args[1] if len(args) > 1 else '')
                    cell = f'[bold green]🎯 FINAL ANSWER: {label}[/bold green]'
                    if preview:
                        clean_preview = preview.replace('\n', ' ').strip()
                        preview_truncated = clean_preview[:80] + '...' if len(clean_preview) > 80 else clean_preview
                        cell += f'\n[dim white]👁️  Preview: {preview_truncated}[/dim white]'
                else:
                    cell = ''
                row.append(cell)
            else:
                status = agent_states[agent]['status']
                if status in ['streaming', 'answering']:
                    cell = f'[cyan]🔄 ({status})[/cyan]'
                elif status == 'voted':
                    cell = '[green]✅ (voted)[/green]'
                elif status == 'answered':
                    if agent_states[agent]['answer']:
                        cell = f'[green]✅ Answered: {agent_states[agent]['answer']}[/green]'
                    else:
                        cell = '[green]✅ (answered)[/green]'
                elif status == 'completed':
                    cell = '[green]✅ (completed)[/green]'
                elif status == 'final':
                    cell = '[bold green]🎯 (final answer given)[/bold green]'
                elif status == 'idle':
                    cell = '[dim]⏳ (waiting)[/dim]'
                else:
                    cell = f'[dim]({status})[/dim]'
                row.append(cell)
        return row

    def _add_rich_summary(self, table: Any, agent_states: dict) -> None:
        """Add summary statistics to the rich table"""
        total_answers = sum((1 for agent in self.agents if agent_states[agent]['answer']))
        total_votes = sum((1 for agent in self.agents if agent_states[agent]['vote']))
        total_restarts = len([e for e in self.events if e['event_type'] == 'restart_completed'])
        summary_row = ['[bold magenta]SUMMARY[/bold magenta]']
        for agent in self.agents:
            agent_num = self.agent_mapping.get(agent, '?')
            agent_name = f'Agent {agent_num}'
            summary_row.append(f'[bold magenta]{agent_name}[/bold magenta]')
        table.add_row(*summary_row)
        stats_row = ['[bold]Stats[/bold]']
        for agent in self.agents:
            answer_count = 1 if agent_states[agent]['answer'] else 0
            vote_count = 1 if agent_states[agent]['vote'] else 0
            restart_count = len([e for e in self.events if e['event_type'] == 'restart_completed' and e.get('agent_id') == agent])
            status = agent_states[agent]['status']
            if status == 'final':
                status_str = '[bold green]🏆 Winner[/bold green]'
            elif status == 'completed':
                status_str = '[green]✅ Completed[/green]'
            else:
                status_str = f'[dim]{status}[/dim]'
            stats = f'{answer_count} answer, {vote_count} vote, {restart_count} restarts\n{status_str}'
            stats_row.append(stats)
        table.add_row(*stats_row)
        totals_row = ['[bold]TOTALS[/bold]']
        totals_text = f'[bold cyan]{total_answers} answers, {total_votes} votes, {total_restarts} restarts[/bold cyan]'
        for _ in range(len(self.agents)):
            totals_row.append(totals_text)
        table.add_row(*totals_row)

    def generate_rich_table(self) -> Optional['Table']:
        """Generate a Rich table with proper formatting and colors."""
        if not RICH_AVAILABLE:
            return None
        table = Table(box=box.DOUBLE_EDGE, show_header=True, header_style='bold bright_white on blue', expand=True, padding=(0, 1), title='[bold bright_cyan]Multi-Agent Coordination Flow[/bold bright_cyan]', title_style='bold bright_cyan')
        table.add_column('Round', style='bold bright_white', width=14, justify='center')
        for agent in self.agents:
            agent_name = agent
            table.add_column(agent_name, style='white', justify='center', width=40, overflow='fold')
        from rich.table import Table as InnerTable
        inner_question_table = InnerTable(box=None, show_header=False, expand=True, padding=(0, 0))
        inner_question_table.add_column('Question', justify='center', ratio=1)
        inner_question_table.add_row(f'[bold bright_yellow]{self.user_question}[/bold bright_yellow]')
        question_cells = ['']
        question_cells.append(inner_question_table)
        for i in range(len(self.agents) - 1):
            question_cells.append('')
        table.add_row(*question_cells)
        separator_cells = ['[dim bright_blue]════════════[/dim bright_blue]'] + ['[dim bright_blue]' + '═' * 88 + '[/dim bright_blue]' for _ in self.agents]
        table.add_row(*separator_cells)
        for i, round_data in enumerate(self.rounds):
            agent_contents = {}
            max_lines = 0
            for agent in self.agents:
                content = self._build_rich_agent_cell_content(round_data.agent_states[agent], round_data.round_type, agent, round_data.round_num)
                agent_contents[agent] = content
                max_lines = max(max_lines, len(content))
            for line_idx in range(max_lines):
                row_cells = []
                if line_idx == 0:
                    if round_data.round_type == 'FINAL':
                        round_label = '[bold green]🏁 FINAL 🏁[/bold green]'
                    else:
                        round_label = f'[bold cyan]🔄 {round_data.round_type} 🔄[/bold cyan]'
                    row_cells.append(round_label)
                else:
                    row_cells.append('')
                for agent in self.agents:
                    content_lines = agent_contents[agent]
                    if line_idx < len(content_lines):
                        row_cells.append(content_lines[line_idx])
                    else:
                        row_cells.append('')
                table.add_row(*row_cells)
            if i < len(self.rounds) - 1:
                next_round = self.rounds[i + 1]
                if next_round.round_type == 'FINAL':
                    if self.final_winner:
                        agent_number = self.agent_mapping.get(self.final_winner)
                        if agent_number:
                            winner_name = f'Agent {agent_number}'
                        else:
                            winner_name = self.final_winner
                        winner_announcement = f'🏆 {winner_name} selected as winner 🏆'
                        inner_winner_table = InnerTable(box=None, show_header=False, expand=True, padding=(0, 0))
                        inner_winner_table.add_column('Winner', justify='center', ratio=1)
                        inner_winner_table.add_row(f'[bold bright_green]{winner_announcement}[/bold bright_green]')
                        winner_cells = ['']
                        winner_cells.append(inner_winner_table)
                        for j in range(len(self.agents) - 1):
                            winner_cells.append('')
                        table.add_row(*winner_cells)
                    separator_cells = ['[dim green]────────────[/dim green]'] + ['[dim green]' + '─' * 88 + '[/dim green]' for _ in self.agents]
                    table.add_row(*separator_cells)
                else:
                    separator_cells = ['[dim cyan]~~~~~~~~~~~~[/dim cyan]'] + ['[dim cyan]' + '~' * 88 + '[/dim cyan]' for _ in self.agents]
                    table.add_row(*separator_cells)
        return table

    def _build_rich_agent_cell_content(self, agent_state: AgentState, round_type: str, agent_id: str, round_num: int) -> List[str]:
        """Build Rich-formatted content for an agent's cell in a round."""
        lines = []
        show_context = agent_state.current_answer and (not agent_state.vote) or agent_state.has_final_answer or agent_state.status in ['streaming', 'answering']
        if round_type == 'FINAL' and agent_state.status == 'completed':
            show_context = False
        if show_context and (not agent_state.vote):
            if agent_state.context:
                context_items = ', '.join(agent_state.context)
                context_str = f'📋 Context: \\[{context_items}]'
            else:
                context_str = '📋 Context: \\[]'
            lines.append(f'[dim blue]{context_str}[/dim blue]')
        if agent_state.vote:
            if agent_state.context:
                context_items = ', '.join(agent_state.context)
                context_str = f'📋 Context: \\[{context_items}]'
                lines.append(f'[dim blue]{context_str}[/dim blue]')
            vote_str = f'🗳️  VOTE: {agent_state.vote}'
            lines.append(f'[bold cyan]{vote_str}[/bold cyan]')
            if agent_state.vote_reason:
                clean_reason = agent_state.vote_reason.replace('\n', ' ').strip()
                reason = clean_reason[:65] + '...' if len(clean_reason) > 68 else clean_reason
                reason_str = f'💭 Reason: {reason}'
                lines.append(f'[italic dim]{reason_str}[/italic dim]')
        elif round_type == 'FINAL':
            if agent_state.has_final_answer:
                final_str = f'🎯 FINAL ANSWER: {agent_state.current_answer}'
                lines.append(f'[bold green]{final_str}[/bold green]')
                if agent_state.answer_preview:
                    clean_preview = agent_state.answer_preview.replace('\n', ' ').strip()
                    preview_truncated = clean_preview[:80] + '...' if len(clean_preview) > 80 else clean_preview
                    preview_str = f'👁️  Preview: {preview_truncated}'
                    lines.append(f'[dim white]{preview_str}[/dim white]')
                else:
                    lines.append('[dim red]👁️  Preview: [Answer not available][/dim red]')
            elif agent_state.status == 'completed':
                lines.append('[dim green]✅ (completed)[/dim green]')
            else:
                lines.append('[dim yellow]⏳ (waiting)[/dim yellow]')
        elif agent_state.current_answer and (not agent_state.vote):
            answer_str = f'✨ NEW ANSWER: {agent_state.current_answer}'
            lines.append(f'[bold green]{answer_str}[/bold green]')
            if agent_state.answer_preview:
                clean_preview = agent_state.answer_preview.replace('\n', ' ').strip()
                preview_truncated = clean_preview[:80] + '...' if len(clean_preview) > 80 else clean_preview
                preview_str = f'👁️  Preview: {preview_truncated}'
                lines.append(f'[dim white]{preview_str}[/dim white]')
            else:
                lines.append('[dim red]👁️  Preview: [Answer not available][/dim red]')
        elif agent_state.status in ['streaming', 'answering']:
            lines.append('[bold yellow]🔄 (answering)[/bold yellow]')
        elif agent_state.status == 'voted':
            lines.append('[dim bright_cyan]✅ (voted)[/dim bright_cyan]')
        elif agent_state.status == 'answered':
            lines.append('[dim bright_green]✅ (answered)[/dim bright_green]')
        else:
            lines.append('[dim]⏳ (waiting)[/dim]')
        return lines

def _create_agent_mapping(self) -> Dict[str, str]:
    """Create explicit mapping from agent_id to agent_number for answer labels"""
    mapping = {}
    for i, agent_id in enumerate(self.agents, 1):
        mapping[agent_id] = str(i)
    return mapping

def _extract_user_question(self) -> str:
    """Extract the user question from session metadata"""
    return str(self.session_metadata.get('user_prompt', 'No user prompt found'))

def _extract_answer_previews(self) -> Dict[str, str]:
    """Extract the actual answer text for each agent using explicit mapping"""
    answers = {}
    for event in self.events:
        if event['event_type'] == 'final_agent_selected':
            context = event.get('context', {})
            answers_for_context = context.get('answers_for_context', {})
            for label, answer in answers_for_context.items():
                if label in self.agents:
                    answers[label] = answer
                elif label.startswith('agent') and '.' in label:
                    try:
                        agent_num = label.split('.')[0][5:]
                        for agent_id, mapped_num in self.agent_mapping.items():
                            if mapped_num == agent_num:
                                answers[agent_id] = answer
                                break
                    except (IndexError, ValueError):
                        continue
    return answers

class FormatterBase(ABC):
    """Abstract base class for API parameter handlers."""

    def __init__(self) -> None:
        """Initialize the API params handler.

        Args:
            backend_instance: The backend instance containing necessary formatters and config
        """
        return None

    @abstractmethod
    def format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @staticmethod
    def extract_tool_name(tool_call: Dict[str, Any]) -> str:
        """
        Extract tool name from a tool call (handles multiple formats).

        Supports:
        - Chat Completions format: {"function": {"name": "...", ...}}
        - Response API format: {"name": "..."}
        - Claude native format: {"name": "..."}

        Args:
            tool_call: Tool call data structure from any backend

        Returns:
            Tool name string
        """
        if 'function' in tool_call:
            return tool_call.get('function', {}).get('name', 'unknown')
        elif 'name' in tool_call:
            return tool_call.get('name', 'unknown')
        return 'unknown'

    @staticmethod
    def extract_tool_arguments(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tool arguments from a tool call (handles multiple formats).

        Supports:
        - Chat Completions format: {"function": {"arguments": ...}}
        - Response API format: {"arguments": ...}
        - Claude native format: {"input": ...}

        Args:
            tool_call: Tool call data structure from any backend

        Returns:
            Tool arguments dictionary (parsed from JSON string if needed)
        """
        import json
        if 'function' in tool_call:
            args = tool_call.get('function', {}).get('arguments', {})
        elif 'input' in tool_call:
            args = tool_call.get('input', {})
        elif 'arguments' in tool_call:
            args = tool_call.get('arguments', {})
        else:
            args = {}
        if isinstance(args, str):
            try:
                return json.loads(args) if args.strip() else {}
            except (json.JSONDecodeError, ValueError):
                return {}
        return args if isinstance(args, dict) else {}

    @staticmethod
    def extract_tool_call_id(tool_call: Dict[str, Any]) -> str:
        """
        Extract tool call ID from a tool call (handles multiple formats).

        Supports:
        - Chat Completions format: {"id": "..."}
        - Response API format: {"call_id": "..."}
        - Claude native format: {"id": "..."}

        Args:
            tool_call: Tool call data structure from any backend

        Returns:
            Tool call ID string
        """
        return tool_call.get('id') or tool_call.get('call_id') or ''

    @staticmethod
    def _serialize_tool_arguments(arguments) -> str:
        """Safely serialize tool call arguments to JSON string.

        Args:
            arguments: Tool arguments (can be string, dict, or other types)

        Returns:
            JSON string representation of arguments
        """
        import json
        if isinstance(arguments, str):
            try:
                json.loads(arguments)
                return arguments
            except (json.JSONDecodeError, ValueError):
                return json.dumps(arguments)
        elif arguments is None:
            return '{}'
        else:
            try:
                return json.dumps(arguments)
            except (TypeError, ValueError) as e:
                print(f'Warning: Failed to serialize tool arguments: {e}, arguments: {arguments}')
                return '{}'

@staticmethod
def _serialize_tool_arguments(arguments) -> str:
    """Safely serialize tool call arguments to JSON string.

        Args:
            arguments: Tool arguments (can be string, dict, or other types)

        Returns:
            JSON string representation of arguments
        """
    import json
    if isinstance(arguments, str):
        try:
            json.loads(arguments)
            return arguments
        except (json.JSONDecodeError, ValueError):
            return json.dumps(arguments)
    elif arguments is None:
        return '{}'
    else:
        try:
            return json.dumps(arguments)
        except (TypeError, ValueError) as e:
            print(f'Warning: Failed to serialize tool arguments: {e}, arguments: {arguments}')
            return '{}'

class TokenCostCalculator:
    """Unified token estimation and cost calculation."""
    PROVIDER_PRICING: Dict[str, Dict[str, ModelPricing]] = {'OpenAI': {'gpt-4o': ModelPricing(0.0025, 0.01, 128000, 16384), 'gpt-4o-mini': ModelPricing(0.00015, 0.0006, 128000, 16384), 'gpt-4-turbo': ModelPricing(0.01, 0.03, 128000, 4096), 'gpt-4': ModelPricing(0.03, 0.06, 8192, 8192), 'gpt-3.5-turbo': ModelPricing(0.0005, 0.0015, 16385, 4096), 'o1-preview': ModelPricing(0.015, 0.06, 128000, 32768), 'o1-mini': ModelPricing(0.003, 0.012, 128000, 65536), 'o3-mini': ModelPricing(0.0011, 0.0044, 200000, 100000)}, 'Anthropic': {'claude-3-5-sonnet': ModelPricing(0.003, 0.015, 200000, 8192), 'claude-3-5-haiku': ModelPricing(0.001, 0.005, 200000, 8192), 'claude-3-opus': ModelPricing(0.015, 0.075, 200000, 4096), 'claude-3-sonnet': ModelPricing(0.003, 0.015, 200000, 4096), 'claude-3-haiku': ModelPricing(0.00025, 0.00125, 200000, 4096)}, 'Google': {'gemini-2.0-flash-exp': ModelPricing(0.0, 0.0, 1048576, 8192), 'gemini-2.0-flash-thinking-exp': ModelPricing(0.0, 0.0, 32767, 8192), 'gemini-1.5-pro': ModelPricing(0.00125, 0.005, 2097152, 8192), 'gemini-1.5-flash': ModelPricing(7.5e-05, 0.0003, 1048576, 8192), 'gemini-1.5-flash-8b': ModelPricing(3.75e-05, 0.00015, 1048576, 8192), 'gemini-1.0-pro': ModelPricing(0.00025, 0.00125, 32760, 8192)}, 'Cerebras': {'llama3.3-70b': ModelPricing(0.00035, 0.00035, 128000, 8192), 'llama3.1-70b': ModelPricing(0.00035, 0.00035, 128000, 8192), 'llama3.1-8b': ModelPricing(1e-05, 1e-05, 128000, 8192)}, 'Together': {'meta-llama/Llama-3.3-70B-Instruct-Turbo': ModelPricing(0.00059, 0.00079, 128000, 32768), 'meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo': ModelPricing(0.00059, 0.00079, 128000, 32768), 'meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo': ModelPricing(0.00088, 0.00088, 130000, 4096), 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo': ModelPricing(0.00018, 0.00018, 131072, 65536), 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo': ModelPricing(6e-05, 6e-05, 131072, 16384), 'Qwen/QwQ-32B-Preview': ModelPricing(0.00015, 0.00015, 32768, 32768), 'Qwen/Qwen2.5-72B-Instruct-Turbo': ModelPricing(0.00012, 0.00012, 32768, 8192), 'mistralai/Mixtral-8x22B-Instruct-v0.1': ModelPricing(0.0009, 0.0009, 65536, 65536), 'deepseek-ai/deepseek-r1-distill-llama-70b': ModelPricing(0.00015, 0.00015, 65536, 8192)}, 'Fireworks': {'llama-3.3-70b': ModelPricing(0.0002, 0.0002, 128000, 16384), 'llama-3.1-405b': ModelPricing(0.0009, 0.0009, 131072, 16384), 'llama-3.1-70b': ModelPricing(0.0002, 0.0002, 131072, 16384), 'llama-3.1-8b': ModelPricing(2e-05, 2e-05, 131072, 16384), 'qwen2.5-72b': ModelPricing(0.0002, 0.0002, 32768, 16384)}, 'Groq': {'llama-3.3-70b-versatile': ModelPricing(0.00059, 0.00079, 128000, 32768), 'llama-3.1-70b-versatile': ModelPricing(0.00059, 0.00079, 131072, 8000), 'llama-3.1-8b-instant': ModelPricing(5e-05, 8e-05, 131072, 8000), 'mixtral-8x7b-32768': ModelPricing(0.00024, 0.00024, 32768, 32768)}, 'xAI': {'grok-2-latest': ModelPricing(0.005, 0.015, 131072, 131072), 'grok-2': ModelPricing(0.005, 0.015, 131072, 131072), 'grok-2-mini': ModelPricing(0.001, 0.003, 131072, 65536)}, 'DeepSeek': {'deepseek-reasoner': ModelPricing(0.00014, 0.0028, 163840, 8192), 'deepseek-chat': ModelPricing(0.00014, 0.00028, 64000, 8192)}}

    def __init__(self):
        """Initialize the calculator with optional tiktoken for accurate estimation."""
        self.tiktoken_encoder = None
        self._try_init_tiktoken()

    def _try_init_tiktoken(self):
        """Try to initialize tiktoken encoder for more accurate token counting."""
        try:
            import tiktoken
            self.tiktoken_encoder = tiktoken.get_encoding('cl100k_base')
            logger.debug('Tiktoken encoder initialized for accurate token counting')
        except ImportError:
            logger.debug('Tiktoken not available, using simple estimation')
        except Exception as e:
            logger.warning(f'Failed to initialize tiktoken: {e}')

    def estimate_tokens(self, text: Union[str, List[Dict[str, Any]]], method: str='auto') -> int:
        """
        Estimate token count for text or messages.

        Args:
            text: Text string or list of message dictionaries
            method: Estimation method ("tiktoken", "simple", "auto")

        Returns:
            Estimated token count
        """
        if isinstance(text, list):
            text = self._messages_to_text(text)
        if method == 'auto':
            if self.tiktoken_encoder:
                return self.estimate_tokens_tiktoken(text)
            else:
                return self.estimate_tokens_simple(text)
        elif method == 'tiktoken':
            return self.estimate_tokens_tiktoken(text)
        else:
            return self.estimate_tokens_simple(text)

    def estimate_tokens_tiktoken(self, text: str) -> int:
        """
        Estimate tokens using tiktoken (OpenAI's tokenizer).
        Most accurate for OpenAI models.

        Args:
            text: Text to estimate

        Returns:
            Token count
        """
        if not self.tiktoken_encoder:
            logger.warning('Tiktoken not available, falling back to simple estimation')
            return self.estimate_tokens_simple(text)
        try:
            tokens = self.tiktoken_encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f'Tiktoken encoding failed: {e}, using simple estimation')
            return self.estimate_tokens_simple(text)

    def estimate_tokens_simple(self, text: str) -> int:
        """
        Simple token estimation based on character/word count.
        Roughly 1 token ≈ 4 characters or 0.75 words.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        char_estimate = len(text) / 4
        words = text.split()
        word_estimate = len(words) / 0.75
        estimate = (char_estimate + word_estimate) / 2
        return int(estimate)

    def _messages_to_text(self, messages: List[Dict[str, Any]]) -> str:
        """Convert message list to text for token estimation."""
        text_parts = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if isinstance(content, str):
                text_parts.append(f'{role}: {content}')
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            text_parts.append(f'{role}: {item.get('text', '')}')
                        elif item.get('type') == 'tool_result':
                            text_parts.append(f'tool_result: {item.get('content', '')}')
                    else:
                        text_parts.append(f'{role}: {str(item)}')
            else:
                text_parts.append(f'{role}: {str(content)}')
            if 'tool_calls' in msg:
                tool_calls = msg['tool_calls']
                if isinstance(tool_calls, list):
                    for call in tool_calls:
                        text_parts.append(f'tool_call: {str(call)}')
        return '\n'.join(text_parts)

    def get_model_pricing(self, provider: str, model: str) -> Optional[ModelPricing]:
        """
        Get pricing information for a specific model.

        Args:
            provider: Provider name (e.g., "OpenAI", "Anthropic")
            model: Model name or identifier

        Returns:
            ModelPricing object or None if not found
        """
        provider = self._normalize_provider(provider)
        provider_models = self.PROVIDER_PRICING.get(provider, {})
        if model in provider_models:
            return provider_models[model]
        for model_key, pricing in provider_models.items():
            if model_key.lower() in model.lower() or model.lower() in model_key.lower():
                return pricing
        model_lower = model.lower()
        if 'gpt-4o' in model_lower and 'mini' in model_lower:
            return provider_models.get('gpt-4o-mini')
        elif 'gpt-4o' in model_lower:
            return provider_models.get('gpt-4o')
        elif 'gpt-4' in model_lower and 'turbo' in model_lower:
            return provider_models.get('gpt-4-turbo')
        elif 'gpt-4' in model_lower:
            return provider_models.get('gpt-4')
        elif 'gpt-3.5' in model_lower:
            return provider_models.get('gpt-3.5-turbo')
        elif 'claude-3-5-sonnet' in model_lower or 'claude-3.5-sonnet' in model_lower:
            return provider_models.get('claude-3-5-sonnet')
        elif 'claude-3-5-haiku' in model_lower or 'claude-3.5-haiku' in model_lower:
            return provider_models.get('claude-3-5-haiku')
        elif 'claude-3-opus' in model_lower:
            return provider_models.get('claude-3-opus')
        elif 'claude-3-sonnet' in model_lower:
            return provider_models.get('claude-3-sonnet')
        elif 'claude-3-haiku' in model_lower:
            return provider_models.get('claude-3-haiku')
        elif 'gemini-2' in model_lower and 'flash' in model_lower:
            return provider_models.get('gemini-2.0-flash-exp')
        elif 'gemini-1.5-pro' in model_lower:
            return provider_models.get('gemini-1.5-pro')
        elif 'gemini-1.5-flash' in model_lower:
            return provider_models.get('gemini-1.5-flash')
        logger.debug(f'No pricing found for {provider}/{model}')
        return None

    def _normalize_provider(self, provider: str) -> str:
        """Normalize provider name for lookup."""
        provider_map = {'openai': 'OpenAI', 'anthropic': 'Anthropic', 'claude': 'Anthropic', 'google': 'Google', 'gemini': 'Google', 'vertex': 'Google', 'cerebras': 'Cerebras', 'cerebras ai': 'Cerebras', 'together': 'Together', 'together ai': 'Together', 'fireworks': 'Fireworks', 'fireworks ai': 'Fireworks', 'groq': 'Groq', 'xai': 'xAI', 'x.ai': 'xAI', 'grok': 'xAI', 'deepseek': 'DeepSeek'}
        provider_lower = provider.lower()
        return provider_map.get(provider_lower, provider)

    def calculate_cost(self, input_tokens: int, output_tokens: int, provider: str, model: str) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: Provider name
            model: Model name

        Returns:
            Estimated cost in USD
        """
        pricing = self.get_model_pricing(provider, model)
        if not pricing:
            logger.debug(f'No pricing for {provider}/{model}, returning 0')
            return 0.0
        input_cost = input_tokens / 1000 * pricing.input_cost_per_1k
        output_cost = output_tokens / 1000 * pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        logger.debug(f'Cost calculation for {provider}/{model}: {input_tokens} input @ ${pricing.input_cost_per_1k}/1k = ${input_cost:.4f}, {output_tokens} output @ ${pricing.output_cost_per_1k}/1k = ${output_cost:.4f}, total = ${total_cost:.4f}')
        return total_cost

    def update_token_usage(self, usage: TokenUsage, messages: List[Dict[str, Any]], response_content: str, provider: str, model: str) -> TokenUsage:
        """
        Update token usage with new conversation turn.

        Args:
            usage: Existing TokenUsage to update
            messages: Input messages
            response_content: Response content
            provider: Provider name
            model: Model name

        Returns:
            Updated TokenUsage object
        """
        input_tokens = self.estimate_tokens(messages)
        output_tokens = self.estimate_tokens(response_content)
        cost = self.calculate_cost(input_tokens, output_tokens, provider, model)
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.estimated_cost += cost
        return usage

    def format_cost(self, cost: float) -> str:
        """Format cost for display."""
        if cost < 0.01:
            return f'${cost:.4f}'
        elif cost < 1.0:
            return f'${cost:.3f}'
        else:
            return f'${cost:.2f}'

    def format_usage_summary(self, usage: TokenUsage) -> str:
        """Format token usage summary for display."""
        return f'Tokens: {usage.input_tokens:,} input, {usage.output_tokens:,} output, Cost: {self.format_cost(usage.estimated_cost)}'

def estimate_tokens(self, text: Union[str, List[Dict[str, Any]]], method: str='auto') -> int:
    """
        Estimate token count for text or messages.

        Args:
            text: Text string or list of message dictionaries
            method: Estimation method ("tiktoken", "simple", "auto")

        Returns:
            Estimated token count
        """
    if isinstance(text, list):
        text = self._messages_to_text(text)
    if method == 'auto':
        if self.tiktoken_encoder:
            return self.estimate_tokens_tiktoken(text)
        else:
            return self.estimate_tokens_simple(text)
    elif method == 'tiktoken':
        return self.estimate_tokens_tiktoken(text)
    else:
        return self.estimate_tokens_simple(text)

def estimate_tokens_tiktoken(self, text: str) -> int:
    """
        Estimate tokens using tiktoken (OpenAI's tokenizer).
        Most accurate for OpenAI models.

        Args:
            text: Text to estimate

        Returns:
            Token count
        """
    if not self.tiktoken_encoder:
        logger.warning('Tiktoken not available, falling back to simple estimation')
        return self.estimate_tokens_simple(text)
    try:
        tokens = self.tiktoken_encoder.encode(text)
        return len(tokens)
    except Exception as e:
        logger.warning(f'Tiktoken encoding failed: {e}, using simple estimation')
        return self.estimate_tokens_simple(text)

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

class MCPResponseTracker:
    """
    Tracks MCP tool responses across streaming chunks to handle deduplication.

    Similar to MCPCallTracker but for tracking tool responses to avoid duplicate output.
    """

    def __init__(self):
        """Initialize the tracker with empty storage."""
        self.processed_responses = set()
        self.response_history = []

    def get_response_hash(self, tool_name: str, tool_response: Any) -> str:
        """
        Generate a unique hash for a tool response based on name and response content.

        Args:
            tool_name: Name of the tool that responded
            tool_response: Response from the tool

        Returns:
            MD5 hash string identifying this specific response
        """
        content = f'{tool_name}:{str(tool_response)}'
        return hashlib.md5(content.encode()).hexdigest()

    def is_new_response(self, tool_name: str, tool_response: Any) -> bool:
        """
        Check if this is a new tool response we haven't seen before.

        Args:
            tool_name: Name of the tool that responded
            tool_response: Response from the tool

        Returns:
            True if this is a new response, False if already processed
        """
        response_hash = self.get_response_hash(tool_name, tool_response)
        return response_hash not in self.processed_responses

    def add_response(self, tool_name: str, tool_response: Any) -> Dict[str, Any]:
        """
        Add a new response to the tracker.

        Args:
            tool_name: Name of the tool that responded
            tool_response: Response from the tool

        Returns:
            Dictionary containing response details and timestamp
        """
        response_hash = self.get_response_hash(tool_name, tool_response)
        self.processed_responses.add(response_hash)
        record = {'tool_name': tool_name, 'response': tool_response, 'hash': response_hash, 'timestamp': time.time()}
        self.response_history.append(record)
        return record

def get_response_hash(self, tool_name: str, tool_response: Any) -> str:
    """
        Generate a unique hash for a tool response based on name and response content.

        Args:
            tool_name: Name of the tool that responded
            tool_response: Response from the tool

        Returns:
            MD5 hash string identifying this specific response
        """
    content = f'{tool_name}:{str(tool_response)}'
    return hashlib.md5(content.encode()).hexdigest()

class MCPCallTracker:
    """
    Tracks MCP tool calls across streaming chunks to handle deduplication.

    Uses hashing to identify unique tool calls and timestamps to track when they occurred.
    This ensures we don't double-count the same tool call appearing in multiple chunks.
    """

    def __init__(self):
        """Initialize the tracker with empty storage."""
        self.processed_calls = set()
        self.call_history = []
        self.last_chunk_calls = []
        self.dedup_window = 0.5

    def get_call_hash(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Generate a unique hash for a tool call based on name and arguments.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            MD5 hash string identifying this specific call
        """
        content = f'{tool_name}:{json.dumps(tool_args, sort_keys=True)}'
        return hashlib.md5(content.encode()).hexdigest()

    def is_new_call(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """
        Check if this is a new tool call we haven't seen before.

        Uses a time-window based approach: identical calls within the dedup_window
        are considered duplicates (likely from streaming chunks), while those outside
        the window are considered new calls (likely intentional repeated calls).

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            True if this is a new call, False if we've seen it before
        """
        call_hash = self.get_call_hash(tool_name, tool_args)
        current_time = time.time()
        for call in self.call_history[-10:]:
            if call.get('hash') == call_hash:
                time_diff = current_time - call.get('timestamp', 0)
                if time_diff < self.dedup_window:
                    return False
        self.processed_calls.add(call_hash)
        return True

    def add_call(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new tool call to the history.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            Dictionary containing the call details with timestamp and hash
        """
        call_record = {'name': tool_name, 'arguments': tool_args, 'timestamp': time.time(), 'hash': self.get_call_hash(tool_name, tool_args), 'sequence': len(self.call_history)}
        self.call_history.append(call_record)
        if len(self.call_history) > 100:
            self.call_history = self.call_history[-50:]
        return call_record

    def get_summary(self) -> str:
        """
        Get a summary of all tracked tool calls.

        Returns:
            Human-readable summary of tool usage
        """
        if not self.call_history:
            return 'No MCP tools called'
        tool_names = [call['name'] for call in self.call_history]
        unique_tools = list(dict.fromkeys(tool_names))
        return f'Used {len(self.call_history)} MCP tool calls: {', '.join(unique_tools)}'

def get_call_hash(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
    """
        Generate a unique hash for a tool call based on name and arguments.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool

        Returns:
            MD5 hash string identifying this specific call
        """
    content = f'{tool_name}:{json.dumps(tool_args, sort_keys=True)}'
    return hashlib.md5(content.encode()).hexdigest()

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

def python_interpreter(code: str, timeout: Optional[int]=10) -> Dict[str, Any]:
    """
    Execute Python code in an isolated subprocess and return its output.

    Args:
        code: The Python code string to execute
        timeout: Maximum execution time in seconds (default: 10, Must be less than 60 seconds)

    Returns:
        A dictionary containing:
        - 'stdout': Standard output from the code execution
        - 'stderr': Standard error from the code execution
        - 'returncode': Exit code of the process (0 for success)
        - 'success': Boolean indicating if execution was successful
        - 'error': Error message if execution failed
    """
    timeout = max(min(timeout, 60), 0)
    try:
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=timeout)
        return json.dumps({'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode, 'success': result.returncode == 0, 'error': None})
    except subprocess.TimeoutExpired:
        return json.dumps({'stdout': '', 'stderr': '', 'returncode': -1, 'success': False, 'error': f'Code execution timed out after {timeout} seconds'})
    except Exception as e:
        return json.dumps({'stdout': '', 'stderr': '', 'returncode': -1, 'success': False, 'error': f'Failed to execute code: {str(e)}'})

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

def run_command_directly(command: str, cwd: str=None, timeout: int=10) -> tuple:
    """Helper to run commands directly for testing."""
    result = subprocess.run(command, shell=True, cwd=cwd, timeout=timeout, capture_output=True, text=True)
    return (result.returncode, result.stdout, result.stderr)

class TestCodeExecutionBasics:
    """Test basic command execution functionality."""

    def test_simple_python_command(self, tmp_path):
        """Test executing a simple Python command."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "print(\\"Hello, World!\\")"', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'Hello, World!' in stdout

    def test_python_script_execution(self, tmp_path):
        """Test executing a Python script."""
        script_path = tmp_path / 'test_script.py'
        script_path.write_text("print('Script executed')\nprint('Success')")
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} test_script.py', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'Script executed' in stdout
        assert 'Success' in stdout

    def test_command_with_error(self, tmp_path):
        """Test that command errors are captured."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "import sys; sys.exit(1)"', cwd=str(tmp_path))
        assert exit_code == 1

    def test_command_timeout(self, tmp_path):
        """Test that commands can timeout."""
        with pytest.raises(subprocess.TimeoutExpired):
            run_command_directly(f'{sys.executable} -c "import time; time.sleep(10)"', cwd=str(tmp_path), timeout=1)

    def test_working_directory(self, tmp_path):
        """Test that working directory is respected."""
        test_file = tmp_path / 'test.txt'
        test_file.write_text('test content')
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "import os; print(os.listdir())"', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'test.txt' in stdout

def test_simple_python_command(self, tmp_path):
    """Test executing a simple Python command."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "print(\\"Hello, World!\\")"', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'Hello, World!' in stdout

def test_python_script_execution(self, tmp_path):
    """Test executing a Python script."""
    script_path = tmp_path / 'test_script.py'
    script_path.write_text("print('Script executed')\nprint('Success')")
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} test_script.py', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'Script executed' in stdout
    assert 'Success' in stdout

def test_command_with_error(self, tmp_path):
    """Test that command errors are captured."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "import sys; sys.exit(1)"', cwd=str(tmp_path))
    assert exit_code == 1

def test_command_timeout(self, tmp_path):
    """Test that commands can timeout."""
    with pytest.raises(subprocess.TimeoutExpired):
        run_command_directly(f'{sys.executable} -c "import time; time.sleep(10)"', cwd=str(tmp_path), timeout=1)

def test_working_directory(self, tmp_path):
    """Test that working directory is respected."""
    test_file = tmp_path / 'test.txt'
    test_file.write_text('test content')
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "import os; print(os.listdir())"', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'test.txt' in stdout

class TestPathValidation:
    """Test path validation and security."""

    def test_path_exists_validation(self, tmp_path):
        """Test that non-existent paths are rejected."""
        non_existent = tmp_path / 'does_not_exist'
        with pytest.raises(FileNotFoundError):
            run_command_directly('echo "test"', cwd=str(non_existent))

    def test_relative_path_resolution(self, tmp_path):
        """Test that relative paths are resolved correctly."""
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        test_file = subdir / 'test.txt'
        test_file.write_text('content')
        exit_code, stdout, stderr = run_command_directly(f'''{sys.executable} -c "import os; print(os.path.exists('subdir/test.txt'))"''', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'True' in stdout

def test_path_exists_validation(self, tmp_path):
    """Test that non-existent paths are rejected."""
    non_existent = tmp_path / 'does_not_exist'
    with pytest.raises(FileNotFoundError):
        run_command_directly('echo "test"', cwd=str(non_existent))

def test_relative_path_resolution(self, tmp_path):
    """Test that relative paths are resolved correctly."""
    subdir = tmp_path / 'subdir'
    subdir.mkdir()
    test_file = subdir / 'test.txt'
    test_file.write_text('content')
    exit_code, stdout, stderr = run_command_directly(f'''{sys.executable} -c "import os; print(os.path.exists('subdir/test.txt'))"''', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'True' in stdout

class TestCommandSanitization:
    """Test command sanitization patterns."""

    def test_dangerous_command_patterns(self):
        """Test that dangerous patterns are identified."""
        from massgen.filesystem_manager._code_execution_server import _sanitize_command
        dangerous_commands = ['rm -rf /', 'dd if=/dev/zero of=/dev/sda', ':(){ :|:& };:', 'mv file /dev/null', 'sudo apt install something', 'su root', 'chown root file.txt', 'chmod 777 file.txt']
        for cmd in dangerous_commands:
            with pytest.raises(ValueError, match='dangerous|not allowed'):
                _sanitize_command(cmd)

    def test_safe_commands_pass(self):
        """Test that safe commands pass sanitization."""
        from massgen.filesystem_manager._code_execution_server import _sanitize_command
        safe_commands = ['python script.py', 'pytest tests/', 'npm run build', 'ls -la', 'rm file.txt', 'git submodule update', "echo 'summary'", 'python -m pip install --user requests']
        for cmd in safe_commands:
            _sanitize_command(cmd)

def test_dangerous_command_patterns(self):
    """Test that dangerous patterns are identified."""
    from massgen.filesystem_manager._code_execution_server import _sanitize_command
    dangerous_commands = ['rm -rf /', 'dd if=/dev/zero of=/dev/sda', ':(){ :|:& };:', 'mv file /dev/null', 'sudo apt install something', 'su root', 'chown root file.txt', 'chmod 777 file.txt']
    for cmd in dangerous_commands:
        with pytest.raises(ValueError, match='dangerous|not allowed'):
            _sanitize_command(cmd)

def test_safe_commands_pass(self):
    """Test that safe commands pass sanitization."""
    from massgen.filesystem_manager._code_execution_server import _sanitize_command
    safe_commands = ['python script.py', 'pytest tests/', 'npm run build', 'ls -la', 'rm file.txt', 'git submodule update', "echo 'summary'", 'python -m pip install --user requests']
    for cmd in safe_commands:
        _sanitize_command(cmd)

class TestOutputHandling:
    """Test output capture and size limits."""

    def test_stdout_capture(self, tmp_path):
        """Test that stdout is captured correctly."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "print(\\"line1\\"); print(\\"line2\\")"', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'line1' in stdout
        assert 'line2' in stdout

    def test_stderr_capture(self, tmp_path):
        """Test that stderr is captured correctly."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "import sys; sys.stderr.write(\\"error message\\\\n\\")"', cwd=str(tmp_path))
        assert 'error message' in stderr

    def test_large_output_handling(self, tmp_path):
        """Test handling of large output."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "for i in range(1000): print(i)"', cwd=str(tmp_path))
        assert exit_code == 0
        assert len(stdout) > 0

def test_stdout_capture(self, tmp_path):
    """Test that stdout is captured correctly."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "print(\\"line1\\"); print(\\"line2\\")"', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'line1' in stdout
    assert 'line2' in stdout

def test_stderr_capture(self, tmp_path):
    """Test that stderr is captured correctly."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "import sys; sys.stderr.write(\\"error message\\\\n\\")"', cwd=str(tmp_path))
    assert 'error message' in stderr

def test_large_output_handling(self, tmp_path):
    """Test handling of large output."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -c "for i in range(1000): print(i)"', cwd=str(tmp_path))
    assert exit_code == 0
    assert len(stdout) > 0

class TestCrossPlatform:
    """Test cross-platform compatibility."""

    def test_python_version_check(self, tmp_path):
        """Test that Python version can be checked."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} --version', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'Python' in stdout or 'Python' in stderr

    def test_pip_install(self, tmp_path):
        """Test that pip commands work."""
        exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -m pip --version', cwd=str(tmp_path))
        assert exit_code == 0
        assert 'pip' in stdout or 'pip' in stderr

def test_python_version_check(self, tmp_path):
    """Test that Python version can be checked."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} --version', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'Python' in stdout or 'Python' in stderr

def test_pip_install(self, tmp_path):
    """Test that pip commands work."""
    exit_code, stdout, stderr = run_command_directly(f'{sys.executable} -m pip --version', cwd=str(tmp_path))
    assert exit_code == 0
    assert 'pip' in stdout or 'pip' in stderr

class TestVirtualEnvironment:
    """Test virtual environment handling."""

    def test_auto_detect_venv(self, tmp_path):
        """Test auto-detection of .venv directory."""
        from massgen.filesystem_manager._code_execution_server import _prepare_environment
        venv_dir = tmp_path / '.venv'
        venv_bin = venv_dir / 'bin'
        venv_bin.mkdir(parents=True, exist_ok=True)
        env = _prepare_environment(tmp_path)
        assert 'PATH' in env
        assert str(venv_bin) in env['PATH']
        assert 'VIRTUAL_ENV' in env
        assert str(venv_dir) in env['VIRTUAL_ENV']

    def test_no_venv_fallback(self, tmp_path):
        """Test fallback to system environment when no venv."""
        import os
        from massgen.filesystem_manager._code_execution_server import _prepare_environment
        env = _prepare_environment(tmp_path)
        assert env['PATH'] == os.environ['PATH']

def test_auto_detect_venv(self, tmp_path):
    """Test auto-detection of .venv directory."""
    from massgen.filesystem_manager._code_execution_server import _prepare_environment
    venv_dir = tmp_path / '.venv'
    venv_bin = venv_dir / 'bin'
    venv_bin.mkdir(parents=True, exist_ok=True)
    env = _prepare_environment(tmp_path)
    assert 'PATH' in env
    assert str(venv_bin) in env['PATH']
    assert 'VIRTUAL_ENV' in env
    assert str(venv_dir) in env['VIRTUAL_ENV']

def test_no_venv_fallback(self, tmp_path):
    """Test fallback to system environment when no venv."""
    import os
    from massgen.filesystem_manager._code_execution_server import _prepare_environment
    env = _prepare_environment(tmp_path)
    assert env['PATH'] == os.environ['PATH']

@pytest.fixture
def mock_agents():
    """Create mock Claude Code agents."""
    agents = {}
    for i in range(1, 4):
        agent_id = f'claude_code_{i}'
        cwd = f'test_workspace/agent_{i}'
        agents[agent_id] = MockClaudeCodeAgent(agent_id, cwd)
    return agents

def test_non_claude_code_agents_ignored(test_workspace):
    """Test that non-Claude Code agents are ignored for context sharing."""
    agents = {'claude_code_1': MockClaudeCodeAgent('claude_code_1'), 'regular_agent': MagicMock(backend=MagicMock(get_provider_name=lambda: 'openai'))}
    orchestrator = Orchestrator(agents=agents, snapshot_storage=test_workspace['snapshot_storage'], agent_temporary_workspace=test_workspace['temp_workspace'])
    assert 'claude_code_1' in orchestrator._agent_id_mapping
    assert 'regular_agent' not in orchestrator._agent_id_mapping
    assert len(orchestrator._agent_id_mapping) == 1

class AgentAdapter(ABC):
    """
    Abstract base class for external agent adapters.

    Adapters handle:
    - Message format conversion between MassGen and external agents
    - Tool/function conversion and mapping
    - Streaming simulation for non-streaming agents
    - State management for stateful agents
    """

    def __init__(self, **kwargs):
        """Initialize adapter with agent-specific configuration."""
        self.config = kwargs
        self._conversation_history = []
        self.coordination_stage = None

    @abstractmethod
    async def execute_streaming(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response with tool support.

        This method must:
        1. Convert MassGen messages to agent format
        2. Convert MassGen tools to agent format
        3. Call the agent
        4. Convert response back to MassGen format
        5. Simulate streaming if agent doesn't support it

        Args:
            messages: MassGen format messages
            tools: MassGen format tools
            **kwargs: Additional parameters

        Yields:
            StreamChunk: Standardized response chunks

        """

    async def simulate_streaming(self, content: str, tool_calls: Optional[List[Dict[str, Any]]]=None, delay: float=0.01) -> AsyncGenerator[StreamChunk, None]:
        """
        Simulate streaming for agents that don't support it natively.

        Args:
            content: Complete response content
            tool_calls: Tool calls to include
            delay: Delay between chunks (seconds)

        Yields:
            StreamChunk: Simulated streaming chunks
        """
        if content:
            words = content.split()
            for i, word in enumerate(words):
                chunk_text = word + (' ' if i < len(words) - 1 else '')
                yield StreamChunk(type='content', content=chunk_text)
                await asyncio.sleep(delay)
        if tool_calls:
            yield StreamChunk(type='tool_calls', tool_calls=tool_calls)
        complete_message = {'role': 'assistant', 'content': content or ''}
        if tool_calls:
            complete_message['tool_calls'] = tool_calls
        yield StreamChunk(type='complete_message', complete_message=complete_message)
        yield StreamChunk(type='done')

    @staticmethod
    def _get_tool_name(tool: Dict[str, Any]) -> str:
        """
        Extract tool name from tool schema.

        Supports both formats:
        - {"type": "function", "function": {"name": "tool_name", ...}}
        - {"name": "tool_name", ...}
        """
        if 'function' in tool:
            return tool['function'].get('name', '')
        return tool.get('name', '')

    def convert_messages_from_massgen(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Convert MassGen messages to agent-specific format.

        Override this method for agent-specific conversion.

        Args:
            messages: List of MassGen format messages

        Returns:
            agent-specific message format
        """
        return messages

    def convert_response_to_massgen(self, response: Any) -> Dict[str, Any]:
        """
        Convert agent response to MassGen format.

        Override this method for agent-specific conversion.

        Args:
            response: agent-specific response

        Returns:
            MassGen format response with content and optional tool_calls
        """
        return {'content': str(response), 'tool_calls': None}

    def convert_tools_from_massgen(self, tools: List[Dict[str, Any]]) -> Any:
        """
        Convert MassGen tools to agent-specific format.

        Override this method for agent-specific conversion.

        Args:
            tools: List of MassGen format tools

        Returns:
            agent-specific tool format
        """
        return tools

    def is_stateful(self) -> bool:
        """
        Check if this adapter maintains conversation state.

        Override if your agent is stateless.
        """
        return False

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history.clear()

    def reset_state(self) -> None:
        """Reset adapter state."""
        self.clear_history()

    def set_stage(self, stage: CoordinationStage) -> None:
        """Set the coordination stage for the adapter, if applicable."""
        self.coordination_stage = stage

def convert_response_to_massgen(self, response: Any) -> Dict[str, Any]:
    """
        Convert agent response to MassGen format.

        Override this method for agent-specific conversion.

        Args:
            response: agent-specific response

        Returns:
            MassGen format response with content and optional tool_calls
        """
    return {'content': str(response), 'tool_calls': None}

class AG2Adapter(AgentAdapter):
    """
    Adapter for AG2 (AutoGen) framework.

    Supports:
    - Single AG2 agents (ConversableAgent, AssistantAgent)
    - Function/tool calling
    - Code execution with multiple executor types:
      * LocalCommandLineCodeExecutor (local shell)
      * DockerCommandLineCodeExecutor (Docker containers)
      * JupyterCodeExecutor (Jupyter kernels)
      * YepCodeCodeExecutor (YepCode serverless)
    - Async execution with a_generate_reply
    - No human-in-the-loop (autonomous operation)

    Todos:
    - Group chat support with patterns (e.g., AutoPattern, DefaultPattern, etc.)
    - More tool support including MCP
    """

    def __init__(self, **kwargs):
        """
        Initialize AG2 adapter.

        The adapter receives the entire backend configuration from MassGen.
        It should contain EITHER 'agent_config' OR 'group_config' (not both).

        Args:
            **kwargs: Backend configuration containing either:
                - agent_config: Configuration for single AG2 agent
                - group_config: Configuration for AG2 GroupChat
        """
        super().__init__(**kwargs)
        setup_api_keys()
        self.agent_config = kwargs.get('agent_config')
        self.group_config = kwargs.get('group_config')
        if self.agent_config and self.group_config:
            raise ValueError("Backend configuration should contain EITHER 'agent_config' OR 'group_config', not both.")
        if not self.agent_config and (not self.group_config):
            raise ValueError("Backend configuration must contain either 'agent_config' for single agent or 'group_config' for GroupChat.")
        self.agent_id = None
        self._setup_agents()

    def _setup_agents(self):
        """Set up AG2 agents based on configuration."""
        if self.group_config:
            self._setup_group_chat()
        else:
            self._setup_single_agent()

    def _setup_single_agent(self):
        """Set up a single AG2 agent."""
        self.agent = setup_agent_from_config(self.agent_config)
        self.is_group_chat = False

    def _setup_group_chat(self):
        """Set up AG2 GroupChat with multiple agents and pattern."""
        if 'pattern' not in self.group_config:
            raise ValueError("group_config must include 'pattern' configuration")
        self.default_llm_config = self.group_config.get('llm_config')
        if not self.default_llm_config:
            raise ValueError("group_config must include 'llm_config' as default for all agents")
        agents = []
        agent_name_map = {}
        for agent_cfg in self.group_config.get('agents', []):
            agent = setup_agent_from_config(agent_cfg, default_llm_config=self.default_llm_config)
            agents.append(agent)
            agent_name_map[agent.name] = agent
        if not agents:
            raise ValueError('No valid agents configured for group chat')
        pattern_config = self.group_config['pattern']
        pattern_type = pattern_config.get('type')
        if not pattern_type:
            raise ValueError("pattern configuration must include 'type' field")
        if pattern_type not in SUPPORTED_GROUPCHAT_PATTERNS:
            raise NotImplementedError(f"Pattern type '{pattern_type}' not supported. Supported types: {', '.join(SUPPORTED_GROUPCHAT_PATTERNS)}")
        self.user_agent = self._setup_user_agent(user_agent_config=self.group_config.get('user_agent'), default_llm_config=self.default_llm_config)
        group_manager_args = self._setup_group_manager_args(pattern_config, self.default_llm_config)
        self.pattern = self._create_pattern(pattern_type, pattern_config, agents, agent_name_map, group_manager_args)
        self.agents = agents
        self.group_max_rounds = self.group_config.get('max_rounds', DEFAULT_MAX_ROUNDS)
        self.is_group_chat = True
        logger.info(f'[AG2Adapter] GroupChat setup complete with {len(agents)} agents and {pattern_type} pattern')

    def _setup_user_agent(self, user_agent_config: Any, default_llm_config: Any) -> ConversableAgent:
        """
        Set up user_agent for group chat.

        User agent makes final decisions and calls workflow tools.
        Its name MUST be "User" for termination condition to work.

        Args:
            user_agent_config: Optional user agent configuration from YAML
            default_llm_config: Default llm_config to use if not specified

        Returns:
            ConversableAgent with name "User"
        """
        if user_agent_config:
            user_agent = setup_agent_from_config(user_agent_config, default_llm_config=default_llm_config)
            if user_agent.name != 'User':
                raise ValueError(f"user_agent name must be 'User', got '{user_agent.name}' for termination condition to work")
            return user_agent
        else:
            return ConversableAgent(name='User', system_message=get_user_agent_default_system_message(), description=get_user_agent_default_description(), human_input_mode='NEVER', code_execution_config=False, llm_config=create_llm_config(default_llm_config))

    def _setup_group_manager_args(self, pattern_config: Dict[str, Any], default_llm_config: Any) -> Dict[str, Any]:
        """
        Set up group_manager_args for pattern.

        Args:
            pattern_config: Pattern configuration from YAML
            default_llm_config: Default llm_config to use if not specified

        Returns:
            Dict with llm_config and termination condition
        """
        group_manager_args = pattern_config.get('group_manager_args', {})
        if 'llm_config' not in group_manager_args:
            group_manager_args['llm_config'] = create_llm_config(default_llm_config)
        else:
            group_manager_args['llm_config'] = create_llm_config(group_manager_args['llm_config'])
        group_manager_args['is_termination_msg'] = lambda msg: msg.get('name') == self.user_agent.name and 'TERMINATE' in msg.get('content', '')
        return group_manager_args

    def _create_pattern(self, pattern_type: str, pattern_config: Dict[str, Any], agents: List[ConversableAgent], agent_name_map: Dict[str, ConversableAgent], group_manager_args: Dict[str, Any], *args) -> Any:
        """
        Create AG2 pattern based on type.

        Args:
            pattern_type: Type of pattern (currently only "auto")
            pattern_config: Pattern configuration from YAML
            agents: List of expert agents
            agent_name_map: Mapping from agent names to agent objects
            group_manager_args: Group manager configuration

        Returns:
            Pattern instance (AutoPattern)
        """
        initial_agent_name = pattern_config.get('initial_agent')
        if not initial_agent_name:
            raise ValueError('initial_agent must be specified in pattern configuration')
        if initial_agent_name not in agent_name_map:
            raise ValueError(f"initial_agent '{initial_agent_name}' not found in agents list")
        initial_agent = agent_name_map[initial_agent_name]
        extra_args = {k: v for k, v in pattern_config.items() if k not in ['type', 'initial_agent', 'group_manager_args']}
        if pattern_type == 'auto':
            return AutoPattern(initial_agent=initial_agent, agents=agents, user_agent=self.user_agent, group_manager_args=group_manager_args, **extra_args)
        else:
            raise NotImplementedError(f"Pattern type '{pattern_type}' not supported")

    async def _execute_single_agent(self, messages: List[Dict[str, Any]], agent: ConversableAgent) -> AsyncGenerator[StreamChunk, None]:
        """
        Execute single AG2 agent.

        Args:
            messages: Conversation messages
            agent_id: Agent ID for logging

        Returns:
            Tuple of (content, tool_calls)
        """
        result = await agent.a_generate_reply(messages)
        content = result.get('content', '') if isinstance(result, dict) else str(result)
        tool_calls = result.get('tool_calls') if isinstance(result, dict) else None
        log_backend_activity('ag2', 'Received response data from AG2', {'has_content': bool(content), 'content_length': len(content) if content else 0, 'has_tool_calls': bool(tool_calls), 'tool_count': len(tool_calls) if tool_calls else 0}, agent_id=self.agent_id)
        async for chunk in self.simulate_streaming(content, tool_calls):
            yield chunk

    async def _execute_group_chat(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """
        Execute AG2 group chat with pattern.

        Args:
            messages: Conversation messages
            agent_id: Agent ID for logging

        Returns:
            Tuple of (content, tool_calls)
        """
        for message in messages:
            message['name'] = 'User'
        response = await a_run_group_chat(pattern=self.pattern, messages=messages, max_rounds=self.group_max_rounds)
        last_group_chat_event_msgs = []

        def process_and_log_event(*args, **kwargs) -> None:
            """Process and log AG2 event, returning string representation."""
            line = ' '.join((str(arg) for arg in args))
            last_group_chat_event_msgs.append(line)
        async for event in response.events:
            last_group_chat_event_msgs.clear()
            event.print(f=process_and_log_event)
            formatted_message = '\n'.join(last_group_chat_event_msgs)
            log_backend_activity('ag2', 'Received response from AG2', {'message': formatted_message}, agent_id=self.agent_id)
            yield formatted_message

    async def _execute_group_chat_with_user_agent(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[StreamChunk, None]:
        messages_to_execute = []
        if self.coordination_stage == CoordinationStage.INITIAL_ANSWER:
            self.user_agent.update_system_message(get_user_agent_default_system_message())
            messages[0] = get_group_initial_message()
            async for event_msg in self._execute_group_chat(messages):
                yield StreamChunk(type='content', content=event_msg)
            results = list(self.user_agent._oai_messages.values())[0]
            self.user_agent.update_system_message(get_user_agent_tool_call_message())
            register_tools_for_agent(self.workflow_tools, self.user_agent)
            messages_to_execute = postprocess_group_chat_results(results)
        elif self.coordination_stage == CoordinationStage.ENFORCEMENT:
            register_tools_for_agent(self.workflow_tools, self.user_agent)
            messages_to_execute = messages
        elif self.coordination_stage == CoordinationStage.PRESENTATION:
            self.user_agent.update_system_message(messages[0]['content'])
            messages_to_execute = [messages[1]]
        async for chunk in self._execute_single_agent(messages=messages_to_execute, agent=self.user_agent):
            yield chunk

    async def execute_streaming(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from AG2 agent(s).

        Since AG2 doesn't support streaming, we simulate it.
        """
        try:
            self._register_tools(tools)
            agent_id = kwargs.get('agent_id')
            if agent_id:
                self.agent_id = agent_id
            log_backend_activity('ag2', 'Starting execute_streaming', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
            if self.is_group_chat:
                async for chunk in self._execute_group_chat_with_user_agent(messages):
                    yield chunk
            else:
                async for chunk in self._execute_single_agent(messages, self.agent):
                    yield chunk
            unregister_tools_for_agent(self.workflow_tools, self.user_agent)
        except Exception as e:
            logger.error(f'[AG2Adapter] Error in execute_streaming: {e}', exc_info=True)
            agent_id = kwargs.get('agent_id', 'ag2_agent')
            log_backend_activity('ag2', 'Error during execution', {'error': str(e), 'error_type': type(e).__name__}, agent_id=agent_id)
            yield StreamChunk(type='error', error=f'AG2 execution error: {str(e)}')

    def _register_tools(self, tools: List[Dict[str, Any]]) -> None:
        """
        Register tools with the agent(s).

        For single agent: Register all tools to the agent.

        For group chat:
        - Workflow tools (new_answer, vote) → register ONLY to user_agent
        - Other tools (MCP, etc.) → register to ALL expert agents (not user_agent)

        MassGen and AG2 both use OpenAI function format for tools.
        """
        if not tools:
            return
        if self.is_group_chat:
            self._register_tools_for_group_chat(tools)
        else:
            register_tools_for_agent(tools, self.agent)

    def _register_tools_for_group_chat(self, tools: List[Dict[str, Any]]) -> None:
        """Register tools to group chat agents based on type."""
        workflow_tools, other_tools = self._separate_workflow_and_other_tools(tools)
        for agent in self.agents:
            for tool in other_tools:
                register_tools_for_agent([tool], agent)
            if other_tools:
                logger.info(f"[AG2Adapter] Registered {len(other_tools)} non-workflow tools to agent '{agent.name}'")
        self.workflow_tools = workflow_tools

    def _separate_workflow_and_other_tools(self, tools: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Separate workflow tools from other tools.

        Args:
            tools: List of all tools

        Returns:
            Tuple of (workflow_tools, other_tools)
        """
        workflow_tools = []
        other_tools = []
        for tool in tools:
            tool_name = self._get_tool_name(tool)
            if tool_name in ['new_answer', 'vote']:
                workflow_tools.append(tool)
            else:
                other_tools.append(tool)
        if 'new_answer' in workflow_tools and 'vote' not in workflow_tools:
            raise ValueError("Both 'new_answer' and 'vote' workflow tools must be provided.")
        return (workflow_tools, other_tools)

def _setup_single_agent(self):
    """Set up a single AG2 agent."""
    self.agent = setup_agent_from_config(self.agent_config)
    self.is_group_chat = False

def _register_tools(self, tools: List[Dict[str, Any]]) -> None:
    """
        Register tools with the agent(s).

        For single agent: Register all tools to the agent.

        For group chat:
        - Workflow tools (new_answer, vote) → register ONLY to user_agent
        - Other tools (MCP, etc.) → register to ALL expert agents (not user_agent)

        MassGen and AG2 both use OpenAI function format for tools.
        """
    if not tools:
        return
    if self.is_group_chat:
        self._register_tools_for_group_chat(tools)
    else:
        register_tools_for_agent(tools, self.agent)

def _register_tools_for_group_chat(self, tools: List[Dict[str, Any]]) -> None:
    """Register tools to group chat agents based on type."""
    workflow_tools, other_tools = self._separate_workflow_and_other_tools(tools)
    for agent in self.agents:
        for tool in other_tools:
            register_tools_for_agent([tool], agent)
        if other_tools:
            logger.info(f"[AG2Adapter] Registered {len(other_tools)} non-workflow tools to agent '{agent.name}'")
    self.workflow_tools = workflow_tools

def test_register_tools_for_agent():
    """Test registering tools with agent."""
    mock_agent = MagicMock()
    tools = [{'type': 'function', 'function': {'name': 'search', 'description': 'Search tool'}}, {'type': 'function', 'function': {'name': 'calc', 'description': 'Calculator tool'}}]
    register_tools_for_agent(tools, mock_agent)
    assert mock_agent.update_tool_signature.call_count == len(tools)
    for call in mock_agent.update_tool_signature.call_args_list:
        assert call[1]['is_remove'] is False

def test_unregister_tools_for_agent():
    """Test unregistering tools from agent."""
    mock_agent = MagicMock()
    tools = [{'type': 'function', 'function': {'name': 'search', 'description': 'Search tool'}}]
    unregister_tools_for_agent(tools, mock_agent)
    mock_agent.update_tool_signature.assert_called_once()
    call_kwargs = mock_agent.update_tool_signature.call_args[1]
    assert call_kwargs['is_remove'] is True

@patch('massgen.adapters.utils.ag2_utils.AssistantAgent')
def test_setup_agent_from_config_assistant(mock_assistant):
    """Test setting up AssistantAgent from config."""
    config = {'type': 'assistant', 'name': 'test_agent', 'system_message': 'You are helpful', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}
    setup_agent_from_config(config)
    mock_assistant.assert_called_once()
    call_kwargs = mock_assistant.call_args[1]
    assert call_kwargs['name'] == 'test_agent'
    assert call_kwargs['system_message'] == 'You are helpful'
    assert call_kwargs['human_input_mode'] == 'NEVER'

@patch('massgen.adapters.utils.ag2_utils.ConversableAgent')
def test_setup_agent_from_config_conversable(mock_conversable):
    """Test setting up ConversableAgent from config."""
    config = {'type': 'conversable', 'name': 'test_agent', 'llm_config': [{'api_type': 'openai', 'model': 'gpt-4o'}]}
    setup_agent_from_config(config)
    mock_conversable.assert_called_once()
    call_kwargs = mock_conversable.call_args[1]
    assert call_kwargs['name'] == 'test_agent'
    assert call_kwargs['human_input_mode'] == 'NEVER'

def test_setup_agent_missing_llm_config():
    """Test that missing llm_config raises error."""
    config = {'type': 'assistant', 'name': 'test_agent'}
    with pytest.raises(ValueError) as exc_info:
        setup_agent_from_config(config)
    assert 'llm_config' in str(exc_info.value)

def test_setup_agent_missing_name():
    """Test that missing name raises error."""
    config = {'type': 'assistant', 'llm_config': [{'api_type': 'openai', 'model': 'gpt-4o'}]}
    with pytest.raises(ValueError) as exc_info:
        setup_agent_from_config(config)
    assert 'name' in str(exc_info.value)

@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
def test_adapter_init_single_agent(mock_setup):
    """Test adapter initialization with single agent config."""
    mock_agent = MagicMock()
    mock_setup.return_value = mock_agent
    agent_config = {'type': 'assistant', 'name': 'test', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}
    adapter = AG2Adapter(agent_config=agent_config)
    assert adapter.is_group_chat is False
    assert adapter.agent == mock_agent
    mock_setup.assert_called_once_with(agent_config)

def test_adapter_init_requires_config():
    """Test that adapter requires either agent_config or group_config."""
    with pytest.raises(ValueError) as exc_info:
        AG2Adapter()
    assert 'agent_config' in str(exc_info.value) or 'group_config' in str(exc_info.value)

def test_adapter_init_rejects_both_configs():
    """Test that adapter rejects both agent_config and group_config."""
    with pytest.raises(ValueError) as exc_info:
        AG2Adapter(agent_config={'name': 'test', 'llm_config': []}, group_config={'agents': []})
    assert 'not both' in str(exc_info.value).lower()

@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
def test_register_tools_single_agent(mock_setup):
    """Test tool registration with single agent."""
    mock_agent = MagicMock()
    mock_setup.return_value = mock_agent
    agent_config = {'type': 'assistant', 'name': 'test', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}
    adapter = AG2Adapter(agent_config=agent_config)
    tools = [{'type': 'function', 'function': {'name': 'search', 'description': 'Search tool'}}]
    adapter._register_tools(tools)
    assert mock_agent.update_tool_signature.call_count == len(tools)

@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
def test_register_tools_empty_list(mock_setup):
    """Test that empty tool list doesn't call update_tool_signature."""
    mock_agent = MagicMock()
    mock_setup.return_value = mock_agent
    agent_config = {'type': 'assistant', 'name': 'test', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}
    adapter = AG2Adapter(agent_config=agent_config)
    adapter._register_tools([])
    mock_agent.update_tool_signature.assert_not_called()

@patch('autogen.coding.LocalCommandLineCodeExecutor')
@patch('massgen.adapters.utils.ag2_utils.AssistantAgent')
def test_setup_agent_with_local_code_executor(mock_assistant, mock_executor):
    """Test setting up agent with LocalCommandLineCodeExecutor."""
    config = {'type': 'assistant', 'name': 'coder', 'llm_config': [{'api_type': 'openai', 'model': 'gpt-4o'}], 'code_execution_config': {'executor': {'type': 'LocalCommandLineCodeExecutor', 'timeout': 60, 'work_dir': './workspace'}}}
    setup_agent_from_config(config)
    mock_executor.assert_called_once_with(timeout=60, work_dir='./workspace')
    call_kwargs = mock_assistant.call_args[1]
    assert 'code_execution_config' in call_kwargs
    assert 'executor' in call_kwargs['code_execution_config']

@patch('autogen.coding.DockerCommandLineCodeExecutor')
@patch('massgen.adapters.utils.ag2_utils.ConversableAgent')
def test_setup_agent_with_docker_executor(mock_conversable, mock_executor):
    """Test setting up agent with DockerCommandLineCodeExecutor."""
    config = {'type': 'conversable', 'name': 'docker_coder', 'llm_config': [{'api_type': 'openai', 'model': 'gpt-4o'}], 'code_execution_config': {'executor': {'type': 'DockerCommandLineCodeExecutor', 'image': 'python:3.10', 'timeout': 120}}}
    setup_agent_from_config(config)
    mock_executor.assert_called_once_with(image='python:3.10', timeout=120)
    call_kwargs = mock_conversable.call_args[1]
    assert 'code_execution_config' in call_kwargs

def test_setup_agent_invalid_executor_type():
    """Test that invalid executor type raises error."""
    config = {'type': 'assistant', 'name': 'coder', 'llm_config': [{'api_type': 'openai', 'model': 'gpt-4o'}], 'code_execution_config': {'executor': {'type': 'InvalidExecutor', 'timeout': 60}}}
    with pytest.raises(ValueError) as exc_info:
        setup_agent_from_config(config)
    assert 'Unsupported code executor type' in str(exc_info.value)
    assert 'InvalidExecutor' in str(exc_info.value)

def test_setup_agent_missing_executor_type():
    """Test that missing executor type raises error."""
    config = {'type': 'assistant', 'name': 'coder', 'llm_config': [{'api_type': 'openai', 'model': 'gpt-4o'}], 'code_execution_config': {'executor': {'timeout': 60}}}
    with pytest.raises(ValueError) as exc_info:
        setup_agent_from_config(config)
    assert "must include 'type' field" in str(exc_info.value)

@patch('massgen.adapters.ag2_adapter.ConversableAgent')
@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
@patch('massgen.adapters.ag2_adapter.AutoPattern')
def test_adapter_init_group_chat(mock_pattern, mock_setup, mock_conversable):
    """Test adapter initialization with group chat config."""
    mock_agent1 = MagicMock()
    mock_agent1.name = 'Agent1'
    mock_agent2 = MagicMock()
    mock_agent2.name = 'Agent2'
    mock_user_agent = MagicMock()
    mock_user_agent.name = 'User'
    mock_setup.side_effect = [mock_agent1, mock_agent2]
    mock_conversable.return_value = mock_user_agent
    group_config = {'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}, 'agents': [{'type': 'assistant', 'name': 'Agent1', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}, {'type': 'assistant', 'name': 'Agent2', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}], 'pattern': {'type': 'auto', 'initial_agent': 'Agent1', 'group_manager_args': {'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}}}
    adapter = AG2Adapter(group_config=group_config)
    assert adapter.is_group_chat is True
    assert len(adapter.agents) == 2
    assert adapter.user_agent is not None
    mock_pattern.assert_called_once()

@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
def test_adapter_separate_workflow_and_other_tools(mock_setup):
    """Test separation of workflow and other tools."""
    mock_agent = MagicMock()
    mock_setup.return_value = mock_agent
    agent_config = {'type': 'assistant', 'name': 'test', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}
    adapter = AG2Adapter(agent_config=agent_config)
    tools = [{'type': 'function', 'function': {'name': 'new_answer', 'description': 'Submit answer'}}, {'type': 'function', 'function': {'name': 'vote', 'description': 'Vote for answer'}}, {'type': 'function', 'function': {'name': 'search', 'description': 'Search tool'}}]
    workflow_tools, other_tools = adapter._separate_workflow_and_other_tools(tools)
    assert len(workflow_tools) == 2
    assert len(other_tools) == 1
    assert any((t['function']['name'] == 'new_answer' for t in workflow_tools))
    assert any((t['function']['name'] == 'vote' for t in workflow_tools))
    assert other_tools[0]['function']['name'] == 'search'

@patch('massgen.adapters.ag2_adapter.ConversableAgent')
@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
@patch('massgen.adapters.ag2_adapter.AutoPattern')
def test_adapter_setup_user_agent_custom(mock_pattern, mock_setup, mock_conversable):
    """Test setting up custom user agent."""
    mock_user_agent = MagicMock()
    mock_user_agent.name = 'User'
    mock_agent = MagicMock()
    mock_agent.name = 'TestAgent'
    mock_setup.side_effect = [mock_agent, mock_user_agent]
    group_config = {'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}, 'agents': [{'type': 'assistant', 'name': 'TestAgent', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}], 'pattern': {'type': 'auto', 'initial_agent': 'TestAgent', 'group_manager_args': {'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}}, 'user_agent': {'name': 'User', 'system_message': 'Custom user agent', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}}
    adapter = AG2Adapter(group_config=group_config)
    assert adapter.user_agent.name == 'User'
    assert mock_setup.call_count == 2

@patch('massgen.adapters.ag2_adapter.setup_agent_from_config')
@patch('massgen.adapters.ag2_adapter.AutoPattern')
def test_adapter_invalid_pattern_type(mock_pattern, mock_setup):
    """Test that invalid pattern type raises error."""
    mock_agent = MagicMock()
    mock_agent.name = 'Agent1'
    mock_setup.return_value = mock_agent
    group_config = {'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}, 'agents': [{'type': 'assistant', 'name': 'Agent1', 'llm_config': {'api_type': 'openai', 'model': 'gpt-4o'}}], 'pattern': {'type': 'invalid_pattern', 'initial_agent': 'Agent1'}}
    with pytest.raises(NotImplementedError) as exc_info:
        AG2Adapter(group_config=group_config)
    assert 'invalid_pattern' in str(exc_info.value)

