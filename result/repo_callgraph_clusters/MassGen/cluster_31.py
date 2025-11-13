# Cluster 31

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

class SingleAgent(ChatAgent):
    """
    Individual agent implementation with direct backend communication.

    This class wraps a single LLM backend and provides the standard chat interface,
    making it interchangeable with the MassGen orchestrator from the user's perspective.
    """

    def __init__(self, backend: LLMBackend, agent_id: Optional[str]=None, system_message: Optional[str]=None, session_id: Optional[str]=None):
        """
        Initialize single agent.

        Args:
            backend: LLM backend for this agent
            agent_id: Optional agent identifier
            system_message: Optional system message for the agent
            session_id: Optional session identifier
        """
        super().__init__(session_id)
        self.backend = backend
        self.agent_id = agent_id or f'agent_{uuid.uuid4().hex[:8]}'
        self.system_message = system_message
        if self.system_message:
            self.conversation_history.append({'role': 'system', 'content': self.system_message})

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

    async def _process_stream(self, backend_stream, tools: List[Dict[str, Any]]=None) -> AsyncGenerator[StreamChunk, None]:
        """Common streaming logic for processing backend responses."""
        assistant_response = ''
        tool_calls = []
        complete_message = None
        try:
            async for chunk in backend_stream:
                chunk_type = self._get_chunk_type_value(chunk)
                if chunk_type == 'content':
                    assistant_response += chunk.content
                    yield chunk
                elif chunk_type == 'tool_calls':
                    chunk_tool_calls = getattr(chunk, 'tool_calls', []) or []
                    tool_calls.extend(chunk_tool_calls)
                    yield chunk
                elif chunk_type == 'complete_message':
                    complete_message = chunk.complete_message
                elif chunk_type == 'complete_response':
                    if chunk.response:
                        complete_message = chunk.response
                        if isinstance(chunk.response, dict) and 'output' in chunk.response:
                            response_tool_calls = []
                            for output_item in chunk.response['output']:
                                if output_item.get('type') == 'function_call':
                                    response_tool_calls.append(output_item)
                                    tool_calls.append(output_item)
                            if response_tool_calls:
                                yield StreamChunk(type='tool_calls', tool_calls=response_tool_calls)
                elif chunk_type == 'done':
                    if complete_message:
                        if isinstance(complete_message, dict) and 'output' in complete_message:
                            self.conversation_history.extend(complete_message['output'])
                        else:
                            self.conversation_history.append(complete_message)
                    elif assistant_response.strip() or tool_calls:
                        message_data = {'role': 'assistant', 'content': assistant_response.strip()}
                        if tool_calls:
                            message_data['tool_calls'] = tool_calls
                        self.conversation_history.append(message_data)
                    yield chunk
                else:
                    yield chunk
        except Exception as e:
            error_msg = f'Error: {str(e)}'
            self.add_to_history('assistant', error_msg)
            yield StreamChunk(type='content', content=error_msg)
            yield StreamChunk(type='error', error=str(e))

    async def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]=None, reset_chat: bool=False, clear_history: bool=False, current_stage: CoordinationStage=None) -> AsyncGenerator[StreamChunk, None]:
        """Process messages through single backend with tool support."""
        if clear_history:
            system_messages = [msg for msg in self.conversation_history if msg.get('role') == 'system']
            self.conversation_history = system_messages.copy()
            if self.backend.is_stateful():
                await self.backend.clear_history()
        if reset_chat:
            self.conversation_history = messages.copy()
            if self.backend.is_stateful():
                await self.backend.reset_state()
            backend_messages = self.conversation_history.copy()
        else:
            self.conversation_history.extend(messages)
            if self.backend.is_stateful():
                backend_messages = messages.copy()
            else:
                backend_messages = self.conversation_history.copy()
        if current_stage:
            self.backend.set_stage(current_stage)
        backend_stream = self.backend.stream_with_tools(messages=backend_messages, tools=tools, agent_id=self.agent_id, session_id=self.session_id, **self._get_backend_params())
        async for chunk in self._process_stream(backend_stream, tools):
            yield chunk

    def _get_backend_params(self) -> Dict[str, Any]:
        """Get additional backend parameters. Override in subclasses."""
        return {}

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {'agent_type': 'single', 'agent_id': self.agent_id, 'session_id': self.session_id, 'system_message': self.system_message, 'conversation_length': len(self.conversation_history)}

    async def reset(self) -> None:
        """Reset conversation for new chat."""
        self.conversation_history.clear()
        if self.backend.is_stateful():
            await self.backend.reset_state()
        if self.system_message:
            self.conversation_history.append({'role': 'system', 'content': self.system_message})

    def get_configurable_system_message(self) -> Optional[str]:
        """Get the user-configurable part of the system message."""
        return self.system_message

    def set_model(self, model: str) -> None:
        """Set the model for this agent."""
        self.model = model

    def set_system_message(self, system_message: str) -> None:
        """Set or update the system message."""
        self.system_message = system_message
        if self.conversation_history and self.conversation_history[0].get('role') == 'system':
            self.conversation_history.pop(0)
        self.conversation_history.insert(0, {'role': 'system', 'content': system_message})

def __init__(self, backend: LLMBackend, agent_id: Optional[str]=None, system_message: Optional[str]=None, session_id: Optional[str]=None):
    """
        Initialize single agent.

        Args:
            backend: LLM backend for this agent
            agent_id: Optional agent identifier
            system_message: Optional system message for the agent
            session_id: Optional session identifier
        """
    super().__init__(session_id)
    self.backend = backend
    self.agent_id = agent_id or f'agent_{uuid.uuid4().hex[:8]}'
    self.system_message = system_message
    if self.system_message:
        self.conversation_history.append({'role': 'system', 'content': self.system_message})

def set_system_message(self, system_message: str) -> None:
    """Set or update the system message."""
    self.system_message = system_message
    if self.conversation_history and self.conversation_history[0].get('role') == 'system':
        self.conversation_history.pop(0)
    self.conversation_history.insert(0, {'role': 'system', 'content': system_message})

class ConfigurableAgent(SingleAgent):
    """
    Single agent that uses AgentConfig for advanced configuration.

    This bridges the gap between SingleAgent and the MassGen system by supporting
    all the advanced configuration options (web search, code execution, etc.)
    while maintaining the simple chat interface.

    TODO: Consider merging with SingleAgent. The main difference is:
    - SingleAgent: backend parameters passed directly to constructor/methods
    - ConfigurableAgent: backend parameters come from AgentConfig object

    Could be unified by making SingleAgent accept an optional config parameter
    and using _get_backend_params() pattern for all parameter sources.
    """

    def __init__(self, config, backend: LLMBackend, session_id: Optional[str]=None):
        """
        Initialize configurable agent.

        Args:
            config: AgentConfig with all settings
            backend: LLM backend
            session_id: Optional session identifier
        """
        super().__init__(backend=backend, agent_id=config.agent_id, system_message=config.custom_system_instruction, session_id=session_id)
        self.config = config

    def _get_backend_params(self) -> Dict[str, Any]:
        """Get backend parameters from config."""
        return self.config.get_backend_params()

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status with config details."""
        status = super().get_status()
        status.update({'agent_type': 'configurable', 'config': self.config.to_dict(), 'capabilities': {'web_search': self.config.backend_params.get('enable_web_search', False), 'code_execution': self.config.backend_params.get('enable_code_interpreter', False)}})
        return status

    def get_configurable_system_message(self) -> Optional[str]:
        """Get the user-configurable part of the system message for ConfigurableAgent."""
        if self.config and self.config.backend_params:
            backend_params = self.config.backend_params
            if 'system_prompt' in backend_params:
                return backend_params['system_prompt']
            if 'append_system_prompt' in backend_params:
                return backend_params['append_system_prompt']
        if self.config and self.config.custom_system_instruction:
            return self.config.custom_system_instruction
        return super().get_configurable_system_message()

def __init__(self, config, backend: LLMBackend, session_id: Optional[str]=None):
    """
        Initialize configurable agent.

        Args:
            config: AgentConfig with all settings
            backend: LLM backend
            session_id: Optional session identifier
        """
    super().__init__(backend=backend, agent_id=config.agent_id, system_message=config.custom_system_instruction, session_id=session_id)
    self.config = config

def get_configurable_system_message(self) -> Optional[str]:
    """Get the user-configurable part of the system message for ConfigurableAgent."""
    if self.config and self.config.backend_params:
        backend_params = self.config.backend_params
        if 'system_prompt' in backend_params:
            return backend_params['system_prompt']
        if 'append_system_prompt' in backend_params:
            return backend_params['append_system_prompt']
    if self.config and self.config.custom_system_instruction:
        return self.config.custom_system_instruction
    return super().get_configurable_system_message()

class MCPError(Exception):
    """
    Base exception for MCP-related errors.

    Provides structured error information and context preservation
    with enhanced debugging capabilities.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None, timestamp: Optional[datetime]=None):
        super().__init__(message)
        self.context = self._sanitize_context(context or {})
        self.error_code = error_code
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.original_message = message

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context to remove sensitive information and ensure serializability.
        """
        sanitized = {}
        sensitive_keys = {'password', 'token', 'secret', 'key', 'auth', 'credential'}
        for key, value in context.items():
            if any((sensitive in key.lower() for sensitive in sensitive_keys)):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    def _build_context_from_kwargs(self, base_context: Optional[Dict[str, Any]]=None, **kwargs: Any) -> Dict[str, Any]:
        """
        Merge base context with kwargs, ignoring None values.

        Copies the provided base_context (or initializes an empty dict) and updates it
        with key/value pairs from kwargs where the value is not None. Returns the
        resulting context dict for use in specialized error classes.
        """
        context: Dict[str, Any] = dict(base_context or {})
        for key, value in kwargs.items():
            if value is None:
                continue
            context[key] = value
        return context

    def __str__(self) -> str:
        parts = [self.original_message]
        if self.error_code:
            parts.append(f'Code: {self.error_code}')
        if self.context:
            context_items = [f'{k}={v}' for k, v in self.context.items()]
            parts.append(f'Context: {', '.join(context_items)}')
        return ' | '.join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {'error_type': self.__class__.__name__, 'message': self.original_message, 'error_code': self.error_code, 'context': self.context, 'timestamp': self.timestamp.isoformat()}

    def log_error(self) -> None:
        """Log the error with appropriate level and context."""
        logger.error(f'{self.__class__.__name__}: {self.original_message}', extra={'mcp_error': self.to_dict()})

def __init__(self, message: str, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None, timestamp: Optional[datetime]=None):
    super().__init__(message)
    self.context = self._sanitize_context(context or {})
    self.error_code = error_code
    self.timestamp = timestamp or datetime.now(timezone.utc)
    self.original_message = message

class MCPConnectionError(MCPError):
    """
    Raised when MCP server connection fails.

    Includes connection details for debugging and retry logic.
    """

    def __init__(self, message: str, server_name: Optional[str]=None, transport_type: Optional[str]=None, host: Optional[str]=None, port: Optional[int]=None, retry_count: Optional[int]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        ctx = self._build_context_from_kwargs(context or {}, server_name=server_name, transport_type=transport_type, host=host, port=port, retry_count=retry_count)
        super().__init__(message, ctx, error_code)
        self.server_name = server_name
        self.transport_type = transport_type
        self.host = host
        self.port = port
        self.retry_count = retry_count

def __init__(self, message: str, server_name: Optional[str]=None, transport_type: Optional[str]=None, host: Optional[str]=None, port: Optional[int]=None, retry_count: Optional[int]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    ctx = self._build_context_from_kwargs(context or {}, server_name=server_name, transport_type=transport_type, host=host, port=port, retry_count=retry_count)
    super().__init__(message, ctx, error_code)
    self.server_name = server_name
    self.transport_type = transport_type
    self.host = host
    self.port = port
    self.retry_count = retry_count

class MCPServerError(MCPError):
    """
    Raised when MCP server returns an error.

    Includes server error codes, HTTP status codes, and additional context.
    """

    def __init__(self, message: str, code: Optional[Union[int, str]]=None, server_name: Optional[str]=None, http_status: Optional[int]=None, response_data: Optional[Dict[str, Any]]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        ctx = self._build_context_from_kwargs(context or {}, server_error_code=code, server_name=server_name, http_status=http_status, response_data=response_data)
        super().__init__(message, ctx, error_code)
        self.code = code
        self.server_name = server_name
        self.http_status = http_status
        self.response_data = response_data

def __init__(self, message: str, code: Optional[Union[int, str]]=None, server_name: Optional[str]=None, http_status: Optional[int]=None, response_data: Optional[Dict[str, Any]]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    ctx = self._build_context_from_kwargs(context or {}, server_error_code=code, server_name=server_name, http_status=http_status, response_data=response_data)
    super().__init__(message, ctx, error_code)
    self.code = code
    self.server_name = server_name
    self.http_status = http_status
    self.response_data = response_data

class MCPValidationError(MCPError):
    """
    Raised when MCP configuration or input validation fails.

    Includes detailed validation information for debugging.
    """

    def __init__(self, message: str, field: Optional[str]=None, value: Optional[Any]=None, expected_type: Optional[str]=None, validation_rule: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        value_str: Optional[str] = None
        if value is not None:
            try:
                value_str = str(value)
            except Exception:
                value_str = '[UNCONVERTIBLE]'
            if len(value_str) > 100:
                value_str = value_str[:100]
        ctx = self._build_context_from_kwargs(context or {}, field=field, value=value_str, expected_type=expected_type, validation_rule=validation_rule)
        super().__init__(message, ctx, error_code)
        self.field = field
        self.value = value
        self.expected_type = expected_type
        self.validation_rule = validation_rule

def __init__(self, message: str, field: Optional[str]=None, value: Optional[Any]=None, expected_type: Optional[str]=None, validation_rule: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    value_str: Optional[str] = None
    if value is not None:
        try:
            value_str = str(value)
        except Exception:
            value_str = '[UNCONVERTIBLE]'
        if len(value_str) > 100:
            value_str = value_str[:100]
    ctx = self._build_context_from_kwargs(context or {}, field=field, value=value_str, expected_type=expected_type, validation_rule=validation_rule)
    super().__init__(message, ctx, error_code)
    self.field = field
    self.value = value
    self.expected_type = expected_type
    self.validation_rule = validation_rule

class MCPTimeoutError(MCPError):
    """
    Raised when MCP operations timeout.

    Includes timeout details and operation context for retry logic.
    """

    def __init__(self, message: str, timeout_seconds: Optional[float]=None, operation: Optional[str]=None, elapsed_seconds: Optional[float]=None, server_name: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        ctx = self._build_context_from_kwargs(context or {}, timeout_seconds=timeout_seconds, operation=operation, elapsed_seconds=elapsed_seconds, server_name=server_name)
        super().__init__(message, ctx, error_code)
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        self.elapsed_seconds = elapsed_seconds
        self.server_name = server_name

def __init__(self, message: str, timeout_seconds: Optional[float]=None, operation: Optional[str]=None, elapsed_seconds: Optional[float]=None, server_name: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    ctx = self._build_context_from_kwargs(context or {}, timeout_seconds=timeout_seconds, operation=operation, elapsed_seconds=elapsed_seconds, server_name=server_name)
    super().__init__(message, ctx, error_code)
    self.timeout_seconds = timeout_seconds
    self.operation = operation
    self.elapsed_seconds = elapsed_seconds
    self.server_name = server_name

class MCPAuthenticationError(MCPError):
    """
    Raised when MCP authentication or authorization fails.

    Includes authentication context without exposing sensitive information.
    """

    def __init__(self, message: str, auth_type: Optional[str]=None, username: Optional[str]=None, server_name: Optional[str]=None, permission_required: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        ctx = self._build_context_from_kwargs(context or {}, auth_type=auth_type, username=username, server_name=server_name, permission_required=permission_required)
        super().__init__(message, ctx, error_code)
        self.auth_type = auth_type
        self.username = username
        self.server_name = server_name
        self.permission_required = permission_required

def __init__(self, message: str, auth_type: Optional[str]=None, username: Optional[str]=None, server_name: Optional[str]=None, permission_required: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    ctx = self._build_context_from_kwargs(context or {}, auth_type=auth_type, username=username, server_name=server_name, permission_required=permission_required)
    super().__init__(message, ctx, error_code)
    self.auth_type = auth_type
    self.username = username
    self.server_name = server_name
    self.permission_required = permission_required

class MCPConfigurationError(MCPError):
    """
    Raised when MCP configuration is invalid or missing.

    Includes configuration details for troubleshooting.
    """

    def __init__(self, message: str, config_file: Optional[str]=None, config_section: Optional[str]=None, missing_keys: Optional[list]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        ctx = self._build_context_from_kwargs(context or {}, config_file=config_file, config_section=config_section, missing_keys=missing_keys)
        super().__init__(message, ctx, error_code)
        self.config_file = config_file
        self.config_section = config_section
        self.missing_keys = missing_keys

def __init__(self, message: str, config_file: Optional[str]=None, config_section: Optional[str]=None, missing_keys: Optional[list]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    ctx = self._build_context_from_kwargs(context or {}, config_file=config_file, config_section=config_section, missing_keys=missing_keys)
    super().__init__(message, ctx, error_code)
    self.config_file = config_file
    self.config_section = config_section
    self.missing_keys = missing_keys

class MCPResourceError(MCPError):
    """
    Raised when MCP resource operations fail.

    Includes resource details and operation context.
    """

    def __init__(self, message: str, resource_type: Optional[str]=None, resource_id: Optional[str]=None, operation: Optional[str]=None, server_name: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
        ctx = self._build_context_from_kwargs(context or {}, resource_type=resource_type, resource_id=resource_id, operation=operation, server_name=server_name)
        super().__init__(message, ctx, error_code)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.operation = operation
        self.server_name = server_name

def __init__(self, message: str, resource_type: Optional[str]=None, resource_id: Optional[str]=None, operation: Optional[str]=None, server_name: Optional[str]=None, context: Optional[Dict[str, Any]]=None, error_code: Optional[str]=None):
    ctx = self._build_context_from_kwargs(context or {}, resource_type=resource_type, resource_id=resource_id, operation=operation, server_name=server_name)
    super().__init__(message, ctx, error_code)
    self.resource_type = resource_type
    self.resource_id = resource_id
    self.operation = operation
    self.server_name = server_name

@dataclass
class _ServerClient:
    """Internal container for per-server state."""
    session: Optional[ClientSession] = None
    manager_task: Optional[asyncio.Task] = None
    connected_event: asyncio.Event = None
    disconnect_event: asyncio.Event = None
    connection_lock: asyncio.Lock = None
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    initialized: bool = False

    def __post_init__(self):
        if self.connected_event is None:
            self.connected_event = asyncio.Event()
        if self.disconnect_event is None:
            self.disconnect_event = asyncio.Event()
        if self.connection_lock is None:
            self.connection_lock = asyncio.Lock()

def __post_init__(self):
    if self.connected_event is None:
        self.connected_event = asyncio.Event()
    if self.disconnect_event is None:
        self.disconnect_event = asyncio.Event()
    if self.connection_lock is None:
        self.connection_lock = asyncio.Lock()

class MCPClient:
    """
    Unified MCP client for communicating with single or multiple MCP servers.
    Provides improved security, error handling, and async context management.

    Accepts a list of server configurations and automatically handles:
    - Consistent tool naming: Always uses prefixed names (mcp__server__tool)
    - Circuit breaker protection for all servers
    - Parallel connection for multi-server scenarios
    - Sequential connection for single-server scenarios
    """

    def __init__(self, server_configs: List[Dict[str, Any]], *, timeout_seconds: int=30, allowed_tools: Optional[List[str]]=None, exclude_tools: Optional[List[str]]=None, status_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]]=None, hooks: Optional[Dict[HookType, List[Callable[[str, Dict[str, Any]], Awaitable[bool]]]]]=None):
        """
        Initialize MCP client.

        Args:
            server_configs: List of server configuration dicts (always a list, even for single server)
            timeout_seconds: Timeout for operations in seconds
            allowed_tools: Optional list of tool names to include (if None, includes all)
            exclude_tools: Optional list of tool names to exclude (if None, excludes none)
            status_callback: Optional async callback for status updates
            hooks: Optional dict mapping hook types to lists of hook functions
        """
        self._server_configs = [MCPConfigValidator.validate_server_config(config) for config in server_configs]
        self.name = self._server_configs[0]['name']
        self.timeout_seconds = timeout_seconds
        self.allowed_tools = allowed_tools
        self.exclude_tools = exclude_tools
        self.status_callback = status_callback
        self.hooks = hooks or {}
        self._circuit_breaker = MCPCircuitBreaker()
        self._server_clients: Dict[str, _ServerClient] = {}
        for config in self._server_configs:
            self._server_clients[config['name']] = _ServerClient()
        self.tools: Dict[str, mcp_types.Tool] = {}
        self._tool_to_server: Dict[str, str] = {}
        self._initialized = False
        self._cleanup_done = False
        self._cleanup_lock = asyncio.Lock()
        self._context_managed = False

    @property
    def session(self) -> Optional[ClientSession]:
        """Return first server's session for backward compatibility."""
        if self._server_configs:
            first_server_name = self._server_configs[0]['name']
            server_client = self._server_clients.get(first_server_name)
            if server_client:
                return server_client.session
        return None

    def _get_server_session(self, server_name: str) -> ClientSession:
        """Get session for server, raising error if not connected."""
        server_client = self._server_clients.get(server_name)
        if not server_client or not server_client.session:
            raise MCPConnectionError(f"Server '{server_name}' not connected", server_name=server_name)
        return server_client.session

    async def connect(self) -> None:
        """Connect to MCP server(s) and discover capabilities with circuit breaker integration."""
        if self._initialized:
            return
        logger.info(f'Connecting to {len(self._server_configs)} MCP server(s)...')
        if self.status_callback:
            await self.status_callback('connecting', {'message': f'Connecting to {len(self._server_configs)} MCP server(s)', 'server_count': len(self._server_configs)})
        if len(self._server_configs) > 1:
            await self._connect_all_parallel()
        else:
            await self._connect_single()
        self._initialized = any((sc.initialized for sc in self._server_clients.values()))
        successful_count = len([sc for sc in self._server_clients.values() if sc.initialized])
        failed_count = len(self._server_configs) - successful_count
        if self.status_callback:
            await self.status_callback('connection_summary', {'message': f'Connected to {successful_count}/{len(self._server_configs)} server(s)' + (f' ({failed_count} failed)' if failed_count > 0 else ''), 'successful_count': successful_count, 'failed_count': failed_count, 'total_count': len(self._server_configs), 'tools_count': len(self.tools)})

    async def _connect_server(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Connect to a single server with circuit breaker integration.

        Returns:
            True on success, False on failure
        """
        server_client = self._server_clients[server_name]
        async with server_client.connection_lock:
            if self._circuit_breaker.should_skip_server(server_name):
                logger.warning(f'Skipping server {server_name} due to circuit breaker')
                server_client.connection_state = ConnectionState.FAILED
                return False
            server_client.connection_state = ConnectionState.CONNECTING
            try:
                server_client.manager_task = asyncio.create_task(self._run_manager(server_name, config))
                await asyncio.wait_for(server_client.connected_event.wait(), timeout=30.0)
                if not server_client.initialized or server_client.connection_state != ConnectionState.CONNECTED:
                    raise MCPConnectionError(f'Failed to connect to {server_name}')
                self._circuit_breaker.record_success(server_name)
                logger.info(f"✅ MCP server '{server_name}' connected successfully!")
                return True
            except Exception as e:
                self._circuit_breaker.record_failure(server_name)
                server_client.connection_state = ConnectionState.FAILED
                logger.error(f'Failed to connect to {server_name}: {e}')
                if server_client.manager_task and (not server_client.manager_task.done()):
                    server_client.disconnect_event.set()
                    try:
                        await asyncio.wait_for(server_client.manager_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Manager task for {server_name} didn't shutdown gracefully, cancelling")
                        server_client.manager_task.cancel()
                        try:
                            await server_client.manager_task
                        except asyncio.CancelledError:
                            pass
                    except Exception as cleanup_error:
                        logger.error(f'Error cleaning up manager task for {server_name}: {cleanup_error}')
                    finally:
                        server_client.manager_task = None
                return False

    async def _connect_single(self) -> None:
        """Connect to single server."""
        config = self._server_configs[0]
        server_name = config['name']
        success = await self._connect_server(server_name, config)
        if not success:
            raise MCPConnectionError(f'Failed to connect to {server_name}')

    async def _connect_all_parallel(self) -> None:
        """Connect to all servers in parallel."""
        tasks = [self._connect_server(c['name'], c) for c in self._server_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum((1 for r in results if r is True))
        logger.info(f'Connected to {successful}/{len(self._server_configs)} servers')

    def _create_transport_context(self, config: Dict[str, Any]):
        """Create the appropriate transport context manager based on config."""
        transport_type = config.get('type', 'stdio')
        server_name = config['name']
        if transport_type == 'stdio':
            command = config.get('command', [])
            args = config.get('args', [])
            logger.debug(f'Setting up stdio transport for {server_name}: command={command}, args={args}')
            if isinstance(command, str):
                full_command = prepare_command(command)
                if args:
                    full_command.extend(args)
            elif isinstance(command, list):
                full_command = command + (args or [])
            else:
                full_command = args or []
            if not full_command:
                raise MCPConnectionError(f'No command specified for stdio transport in {server_name}')
            env = config.get('env', {})
            if env:
                env = {**get_default_environment(), **env}
            else:
                env = get_default_environment()
            substituted_args = []
            for arg in full_command[1:] if len(full_command) > 1 else []:
                if isinstance(arg, str):
                    try:
                        substituted_args.append(substitute_env_variables(arg))
                    except ValueError as e:
                        raise MCPConnectionError(f'Environment variable substitution failed in args: {e}', server_name=server_name) from e
                else:
                    substituted_args.append(arg)
            for key, value in list(env.items()):
                if isinstance(value, str):
                    try:
                        env[key] = substitute_env_variables(value)
                    except ValueError as e:
                        raise MCPConnectionError(f'Environment variable substitution failed for {key}: {e}', server_name=server_name) from e
            cwd = config.get('cwd')
            server_params = StdioServerParameters(command=full_command[0], args=substituted_args, env=env, cwd=cwd)
            from ..logger_config import get_log_session_dir
            log_dir = get_log_session_dir()
            errlog_path = log_dir / f'mcp_{server_name}_stderr.log'
            errlog_file = open(errlog_path, 'w', encoding='utf-8')
            if not hasattr(self, '_errlog_files'):
                self._errlog_files = {}
            self._errlog_files[server_name] = errlog_file
            return stdio_client(server_params, errlog=errlog_file)
        elif transport_type == 'streamable-http':
            url = config['url']
            headers = config.get('headers', {})
            substituted_headers = {}
            for key, value in headers.items():
                if isinstance(value, str):
                    try:
                        substituted_headers[key] = substitute_env_variables(value)
                    except ValueError as e:
                        raise MCPConnectionError(f'Environment variable substitution failed in header {key}: {e}', server_name=server_name) from e
                else:
                    substituted_headers[key] = value
            timeout_raw = config.get('timeout', self.timeout_seconds)
            http_read_timeout_raw = config.get('http_read_timeout', 60 * 5)
            timeout = _ensure_timedelta(timeout_raw, self.timeout_seconds)
            http_read_timeout = _ensure_timedelta(http_read_timeout_raw, 60 * 5)
            return streamablehttp_client(url=url, headers=substituted_headers, timeout=timeout, sse_read_timeout=http_read_timeout)
        else:
            raise MCPConnectionError(f'Unsupported transport type: {transport_type}')

    async def _run_manager(self, server_name: str, config: Dict[str, Any]) -> None:
        """Background task that owns the transport and session contexts for a server."""
        server_client = self._server_clients[server_name]
        connection_successful = False
        try:
            transport_ctx = self._create_transport_context(config)
            async with transport_ctx as session_params:
                read, write = session_params[0:2]
                session_timeout_timedelta = _ensure_timedelta(self.timeout_seconds, 30.0)
                async with ClientSession(read, write, read_timeout_seconds=session_timeout_timedelta) as session:
                    server_client.session = session
                    await session.initialize()
                    await self._discover_capabilities(server_name, config)
                    server_client.initialized = True
                    server_client.connection_state = ConnectionState.CONNECTED
                    connection_successful = True
                    server_client.connected_event.set()
                    logger.info(f"✅ MCP server '{server_name}' connected successfully!")
                    if self.status_callback:
                        await self.status_callback('connected', {'server': server_name, 'message': f"Server '{server_name}' ready"})
                    await server_client.disconnect_event.wait()
        except Exception as e:
            logger.error(f'MCP manager error for {server_name}: {e}', exc_info=True)
            if self.status_callback:
                await self.status_callback('error', {'server': server_name, 'message': f"Failed to connect to MCP server '{server_name}': {e}", 'error': str(e)})
            if not server_client.connected_event.is_set():
                server_client.connected_event.set()
        finally:
            server_client.initialized = False
            server_client.session = None
            if not connection_successful:
                server_client.connection_state = ConnectionState.FAILED
                if not server_client.connected_event.is_set():
                    server_client.connected_event.set()
            else:
                server_client.connection_state = ConnectionState.DISCONNECTED

    async def _discover_capabilities(self, server_name: str, config: Dict[str, Any]) -> None:
        """Discover server capabilities (tools, resources, prompts) with name prefixing for multi-server."""
        logger.debug(f'Discovering capabilities for {server_name}')
        session = self._get_server_session(server_name)
        try:
            server_exclude = config.get('exclude_tools', [])
            combined_exclude = list(set((self.exclude_tools or []) + server_exclude))
            server_allowed = config.get('allowed_tools')
            combined_allowed = server_allowed if server_allowed is not None else self.allowed_tools
            available_tools = await session.list_tools()
            tools_list = getattr(available_tools, 'tools', []) if available_tools else []
            for tool in tools_list:
                if combined_exclude and tool.name in combined_exclude:
                    continue
                if combined_allowed is None or tool.name in combined_allowed:
                    prefixed_name = sanitize_tool_name(tool.name, server_name)
                    self.tools[prefixed_name] = tool
                    self._tool_to_server[prefixed_name] = server_name
            logger.info(f'Discovered capabilities for {server_name}: {len([t for t, s in self._tool_to_server.items() if s == server_name])} tools')
        except Exception as e:
            logger.error(f'Failed to discover server capabilities for {server_name}: {e}', exc_info=True)
            raise MCPConnectionError(f'Failed to discover server capabilities: {e}') from e

    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        if not self._initialized:
            return
        tasks = [self._disconnect_one(name, client) for name, client in self._server_clients.items() if client.connection_state != ConnectionState.DISCONNECTED]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._initialized = False

    async def _disconnect_one(self, server_name: str, server_client: _ServerClient) -> None:
        """Disconnect a single server."""
        server_client.connection_state = ConnectionState.DISCONNECTING
        if server_client.manager_task and (not server_client.manager_task.done()):
            server_client.disconnect_event.set()
            try:
                await asyncio.wait_for(server_client.manager_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Manager task for {server_name} didn't shutdown gracefully, cancelling")
                server_client.manager_task.cancel()
                try:
                    await server_client.manager_task
                except asyncio.CancelledError:
                    logger.debug(f'Manager task for {server_name} cancelled successfully')
            except Exception as e:
                logger.error(f'Error during manager task shutdown for {server_name}: {e}')
            finally:
                server_client.manager_task = None
        server_client.initialized = False
        server_client.connection_state = ConnectionState.DISCONNECTED

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool with validation and timeout handling.

        Args:
            tool_name: Name of the tool to call (always prefixed as mcp__server__toolname)
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPError: If tool is not available
            MCPConnectionError: If no active session
            MCPValidationError: If arguments are invalid
            MCPTimeoutError: If tool call times out
            MCPServerError: If tool execution fails
        """
        if tool_name not in self.tools:
            available_tools = list(self.tools.keys())
            raise MCPError(f"Tool '{tool_name}' not available", context={'available_tools': available_tools, 'total': len(available_tools)})
        try:
            validated_arguments = validate_tool_arguments(arguments)
        except ValueError as e:
            raise MCPValidationError(f'Invalid tool arguments: {e}', field='arguments', value=arguments, context={'tool_name': tool_name}) from e
        pre_tool_hooks = self.hooks.get(HookType.PRE_TOOL_USE, [])
        for hook in pre_tool_hooks:
            try:
                allowed = await hook(tool_name, validated_arguments)
                if not allowed:
                    raise MCPValidationError('Tool call blocked by pre-tool hook', field='tool_name', value=tool_name, context={'arguments': validated_arguments})
            except Exception as e:
                if isinstance(e, MCPValidationError):
                    raise
                logger.warning(f'Pre-tool hook error for {tool_name}: {e}', exc_info=True)
        server_name = self._tool_to_server.get(tool_name)
        if not server_name:
            raise MCPError(f"Tool '{tool_name}' not mapped to any server")
        original_tool_name = tool_name[len(f'mcp__{server_name}__'):]
        session = self._get_server_session(server_name)
        logger.debug(f'Calling tool {original_tool_name} on {server_name} with arguments: {validated_arguments}')
        if self.status_callback:
            await self.status_callback('tool_call_start', {'server': server_name, 'tool': original_tool_name, 'message': f"Calling tool '{original_tool_name}' on server '{server_name}'", 'arguments': validated_arguments})
        try:
            result = await asyncio.wait_for(session.call_tool(original_tool_name, validated_arguments), timeout=self.timeout_seconds)
            logger.debug(f'Tool {original_tool_name} completed successfully on {server_name}')
            if self.status_callback:
                await self.status_callback('tool_call_success', {'server': server_name, 'tool': original_tool_name, 'message': f"Tool '{original_tool_name}' executed successfully"})
            return result
        except asyncio.TimeoutError:
            if self.status_callback:
                await self.status_callback('tool_call_timeout', {'server': server_name, 'tool': original_tool_name, 'message': f"Tool '{original_tool_name}' timed out after {self.timeout_seconds} seconds", 'timeout': self.timeout_seconds})
            self._circuit_breaker.record_failure(server_name)
            raise MCPTimeoutError(f'Tool call timed out after {self.timeout_seconds} seconds', timeout_seconds=self.timeout_seconds, operation=f'call_tool({original_tool_name})', context={'tool_name': original_tool_name, 'server_name': server_name})
        except Exception as e:
            logger.error(f'Tool call failed for {original_tool_name} on {server_name}: {e}', exc_info=True)
            self._circuit_breaker.record_failure(server_name)
            if self.status_callback:
                await self.status_callback('tool_call_error', {'server': server_name, 'tool': original_tool_name, 'message': f"Tool '{original_tool_name}' failed: {e}", 'error': str(e)})
            raise MCPServerError(f'Tool call failed: {e}', server_name=server_name, context={'tool_name': original_tool_name, 'arguments': validated_arguments}) from e

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())

    def is_connected(self) -> bool:
        """Check if any servers are connected."""
        return self._initialized and any((sc.initialized for sc in self._server_clients.values()))

    def get_server_names(self) -> List[str]:
        """Get list of connected server names."""
        return [name for name, sc in self._server_clients.items() if sc.initialized]

    def get_active_sessions(self) -> List[ClientSession]:
        """Return active MCP ClientSession objects for all connected servers."""
        sessions = []
        for server_client in self._server_clients.values():
            if server_client.session is not None and server_client.initialized:
                sessions.append(server_client.session)
        return sessions

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all connected MCP servers.

        Returns:
            Dictionary mapping server names to health status
        """
        health_status = {}
        for server_name, server_client in self._server_clients.items():
            if not server_client.initialized or not server_client.session:
                health_status[server_name] = False
                continue
            try:
                await server_client.session.list_tools()
                health_status[server_name] = True
            except Exception as e:
                logger.warning(f'Health check failed for {server_name}: {e}')
                health_status[server_name] = False
        return health_status

    async def health_check(self) -> bool:
        """
        Perform a health check on all servers.

        Returns:
            True if all connected servers are healthy, False otherwise
        """
        health_status = await self.health_check_all()
        return all(health_status.values()) if health_status else False

    async def _reconnect_failed_servers(self, max_retries: int=3) -> Dict[str, bool]:
        """
        Attempt to reconnect any failed servers with circuit breaker integration.

        Args:
            max_retries: Maximum number of reconnection attempts per server

        Returns:
            Dictionary mapping server names to reconnection success status
        """
        health_status = await self.health_check_all()
        reconnect_results = {}
        for server_name, is_healthy in health_status.items():
            if not is_healthy:
                if self._circuit_breaker.should_skip_server(server_name):
                    logger.warning(f'Skipping reconnection for {server_name} due to circuit breaker')
                    reconnect_results[server_name] = False
                    continue
                logger.info(f'Attempting to reconnect failed server: {server_name}')
                config = next((c for c in self._server_configs if c['name'] == server_name), None)
                if not config:
                    reconnect_results[server_name] = False
                    continue
                success = False
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            await asyncio.sleep(1.0 * 2 ** attempt)
                        server_client = self._server_clients[server_name]
                        await self._disconnect_one(server_name, server_client)
                        server_client.connected_event = asyncio.Event()
                        server_client.disconnect_event = asyncio.Event()
                        server_client.manager_task = asyncio.create_task(self._run_manager(server_name, config))
                        await asyncio.wait_for(server_client.connected_event.wait(), timeout=30.0)
                        if server_client.initialized:
                            self._circuit_breaker.record_success(server_name)
                            success = True
                            logger.info(f'Successfully reconnected server: {server_name}')
                            break
                    except Exception as e:
                        logger.warning(f'Reconnection attempt {attempt + 1} failed for {server_name}: {e}')
                        self._circuit_breaker.record_failure(server_name)
                reconnect_results[server_name] = success
            else:
                reconnect_results[server_name] = True
        return reconnect_results

    async def reconnect(self, max_retries: int=3) -> bool:
        """
        Attempt to reconnect all servers with circuit breaker integration.

        Args:
            max_retries: Maximum number of reconnection attempts
                Uses exponential backoff between retries: 2s, 4s, 8s, 16s...

        Returns:
            True if all reconnections successful, False otherwise
        """
        results = await self._reconnect_failed_servers(max_retries)
        return all(results.values()) if results else False

    async def _cleanup(self) -> None:
        """Comprehensive cleanup of all resources."""
        async with self._cleanup_lock:
            if self._cleanup_done:
                return
            logger.debug('Starting cleanup for MCPClient')
            try:
                await self.disconnect()
                if hasattr(self, '_errlog_files'):
                    for server_name, errlog_file in self._errlog_files.items():
                        try:
                            errlog_file.close()
                        except Exception as e:
                            logger.debug(f'Error closing errlog file for {server_name}: {e}')
                    self._errlog_files.clear()
                self.tools.clear()
                self._tool_to_server.clear()
                self._cleanup_done = True
                logger.debug('Cleanup completed for MCPClient')
            except Exception as e:
                logger.error(f'Error during cleanup: {e}')
                raise

    async def __aenter__(self) -> 'MCPClient':
        """Async context manager entry."""
        self._context_managed = True
        await self.connect()
        return self

    async def __aexit__(self, _exc_type: Optional[type], _exc_val: Optional[BaseException], _exc_tb: Optional[TracebackType]) -> None:
        """Async context manager exit."""
        try:
            await self._cleanup()
        except Exception as e:
            logger.error(f'Error during context manager cleanup: {e}')
        finally:
            self._context_managed = False

    @classmethod
    async def create_and_connect(cls, server_configs: List[Dict[str, Any]], *, timeout_seconds: int=30, allowed_tools: Optional[List[str]]=None, exclude_tools: Optional[List[str]]=None) -> 'MCPClient':
        """
        Create and connect MCP client in one step.

        Args:
            server_configs: List of server configuration dictionaries
            timeout_seconds: Timeout for operations in seconds
            allowed_tools: Optional list of tool names to include
            exclude_tools: Optional list of tool names to exclude

        Returns:
            Connected MCPClient instance
        """
        client = cls(server_configs, timeout_seconds=timeout_seconds, allowed_tools=allowed_tools, exclude_tools=exclude_tools)
        await client.connect()
        return client

def __init__(self, server_configs: List[Dict[str, Any]], *, timeout_seconds: int=30, allowed_tools: Optional[List[str]]=None, exclude_tools: Optional[List[str]]=None, status_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]]=None, hooks: Optional[Dict[HookType, List[Callable[[str, Dict[str, Any]], Awaitable[bool]]]]]=None):
    """
        Initialize MCP client.

        Args:
            server_configs: List of server configuration dicts (always a list, even for single server)
            timeout_seconds: Timeout for operations in seconds
            allowed_tools: Optional list of tool names to include (if None, includes all)
            exclude_tools: Optional list of tool names to exclude (if None, excludes none)
            status_callback: Optional async callback for status updates
            hooks: Optional dict mapping hook types to lists of hook functions
        """
    self._server_configs = [MCPConfigValidator.validate_server_config(config) for config in server_configs]
    self.name = self._server_configs[0]['name']
    self.timeout_seconds = timeout_seconds
    self.allowed_tools = allowed_tools
    self.exclude_tools = exclude_tools
    self.status_callback = status_callback
    self.hooks = hooks or {}
    self._circuit_breaker = MCPCircuitBreaker()
    self._server_clients: Dict[str, _ServerClient] = {}
    for config in self._server_configs:
        self._server_clients[config['name']] = _ServerClient()
    self.tools: Dict[str, mcp_types.Tool] = {}
    self._tool_to_server: Dict[str, str] = {}
    self._initialized = False
    self._cleanup_done = False
    self._cleanup_lock = asyncio.Lock()
    self._context_managed = False

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

def __init__(self, agent_ids, **kwargs):
    """Initialize simple display."""
    super().__init__(agent_ids, **kwargs)
    self.show_agent_prefixes = kwargs.get('show_agent_prefixes', True)
    self.show_events = kwargs.get('show_events', True)

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

class TerminalDisplay(BaseDisplay):
    """Rich terminal display with live agent columns and coordination events."""

    def __init__(self, agent_ids: List[str], **kwargs):
        """Initialize terminal display.

        Args:
            agent_ids: List of agent IDs to display
            **kwargs: Additional configuration options
                - terminal_width: Override terminal width (default: auto-detect)
                - max_events: Max coordination events to show (default: 5)
        """
        super().__init__(agent_ids, **kwargs)
        self.terminal_width = kwargs.get('terminal_width', self._get_terminal_width())
        self.max_events = kwargs.get('max_events', 5)
        self.num_agents = len(agent_ids)
        self.log_filename = None
        self._last_refresh_time = 0
        if self.num_agents == 1:
            self.col_width = self.terminal_width - 4
            self.separators = ''
        elif self.num_agents == 2:
            self.col_width = (self.terminal_width - 3) // 2
            self.separators = ' │ '
        else:
            self.col_width = (self.terminal_width - (self.num_agents - 1) * 3) // self.num_agents
            self.separators = ' │ '

    def _get_terminal_width(self) -> int:
        """Get terminal width with fallback."""
        try:
            return min(os.get_terminal_size().columns, 120)
        except (OSError, AttributeError):
            return 80

    def initialize(self, question: str, log_filename: Optional[str]=None):
        """Initialize the display with column headers."""
        self.log_filename = log_filename
        import os
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
        except Exception:
            print('\x1b[2J\x1b[H', end='')
        title = f'🚀 {('Multi' if self.num_agents > 2 else 'Two' if self.num_agents == 2 else 'Single')}-Agent Coordination Dashboard'
        print(title)
        if log_filename:
            print(f'📁 Log: {log_filename}')
        print('=' * self.terminal_width)
        headers = []
        for agent_id in self.agent_ids:
            backend_name = 'Unknown'
            if hasattr(self, 'orchestrator') and self.orchestrator and hasattr(self.orchestrator, 'agents'):
                agent = self.orchestrator.agents.get(agent_id)
                if agent and hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                    try:
                        backend_name = agent.backend.get_provider_name()
                    except Exception:
                        backend_name = 'Unknown'
            header_text = f'{agent_id.upper()} ({backend_name})'
            headers.append(f'{header_text:^{self.col_width}}')
        if self.num_agents == 1:
            print(headers[0])
            print('─' * self.col_width)
        else:
            print(self.separators.join(headers))
            print(self.separators.join(['─' * self.col_width] * self.num_agents))
        print('=' * self.terminal_width)
        print()

    def update_agent_content(self, agent_id: str, content: str, content_type: str='thinking'):
        """Update content for a specific agent."""
        if agent_id not in self.agent_ids:
            return
        clean_content = content
        if clean_content.startswith(f'[{agent_id}]'):
            clean_content = clean_content[len(f'[{agent_id}]'):]
        if clean_content.startswith(f'🤖 **{agent_id}**'):
            clean_content = clean_content.replace(f'🤖 **{agent_id}**', '🤖')
        if '\n' not in clean_content:
            clean_content = clean_content.strip()
        should_refresh = False
        if content_type == 'tool':
            self.agent_outputs[agent_id].append(f'→ {clean_content}')
            should_refresh = True
        elif content_type == 'status':
            self.agent_outputs[agent_id].append(clean_content)
            should_refresh = True
        elif content_type == 'presentation':
            self.agent_outputs[agent_id].append(f'🎤 {clean_content}')
            should_refresh = True
        elif self.agent_outputs[agent_id] and self.agent_outputs[agent_id][-1] == '⚡ Working...':
            self.agent_outputs[agent_id][-1] = clean_content
            should_refresh = True
        elif self._is_action_content(clean_content):
            self.agent_outputs[agent_id].append(clean_content)
            should_refresh = True
        elif self.agent_outputs[agent_id] and (not self.agent_outputs[agent_id][-1].startswith('→')) and (not self.agent_outputs[agent_id][-1].startswith('🎤')) and (not self._is_action_content(self.agent_outputs[agent_id][-1])):
            if '\n' in clean_content:
                parts = clean_content.split('\n')
                self.agent_outputs[agent_id][-1] += parts[0]
                for part in parts[1:]:
                    self.agent_outputs[agent_id].append(part)
                should_refresh = True
            else:
                current_content = self.agent_outputs[agent_id][-1]
                if current_content and clean_content and (not current_content[-1].isspace()) and (not clean_content[0].isspace()) and (current_content[-1] not in '.,!?;:-()[]{}"\'') and (clean_content[0] not in '.,!?;:-()[]{}"\'') and (not clean_content.startswith('\n')) and (clean_content[0].isalpha() or clean_content[0].isdigit()) and (current_content[-1].isalpha() or current_content[-1].isdigit()) and (len(clean_content.strip()) > 2):
                    self.agent_outputs[agent_id][-1] += ' ' + clean_content
                else:
                    self.agent_outputs[agent_id][-1] += clean_content
        else:
            self.agent_outputs[agent_id].append(clean_content)
            should_refresh = True
        if should_refresh:
            self._refresh_display()

    def _is_action_content(self, content: str) -> bool:
        """Check if content represents an action that should be on its own line."""
        action_indicators = ['💡', '🗳️', '✅', '🔄', '❌', '🔧', 'Providing answer:', 'Voting for', 'Answer provided', 'Vote recorded', 'Vote ignored', 'Vote invalid', 'Using']
        return any((indicator in content for indicator in action_indicators))

    def update_agent_status(self, agent_id: str, status: str):
        """Update status for a specific agent."""
        if agent_id not in self.agent_ids:
            return
        old_status = self.agent_status.get(agent_id)
        if old_status == status:
            return
        self.agent_status[agent_id] = status
        if old_status != 'working' and status == 'working':
            agent_prefix = f'[{agent_id}] ' if self.num_agents > 1 else ''
            print(f'\n{agent_prefix}⚡  Working...')
            if not self.agent_outputs[agent_id] or not self.agent_outputs[agent_id][-1].startswith('⚡'):
                self.agent_outputs[agent_id].append('⚡  Working...')
        self._refresh_display()

    def add_orchestrator_event(self, event: str):
        """Add an orchestrator coordination event."""
        self.orchestrator_events.append(event)
        self._refresh_display()

    def show_final_answer(self, answer: str, vote_results=None, selected_agent=None):
        """Display the final coordinated answer prominently."""
        print('\n🎯 FINAL COORDINATED ANSWER:')
        print('=' * 60)
        print(f'📋 {answer}')
        if selected_agent:
            print(f'✅ Selected by: {selected_agent}')
        if vote_results:
            vote_summary = ', '.join([f'{agent}: {votes}' for agent, votes in vote_results.items()])
            print(f'🗳️ Vote results: {vote_summary}')
        print('=' * 60)

    def cleanup(self):
        """Clean up display resources."""

    def _refresh_display(self):
        """Refresh the entire display with proper columns."""
        import time
        current_time = time.time()
        if current_time - self._last_refresh_time < 0.005:
            return
        self._last_refresh_time = current_time
        print('\x1b[7;1H\x1b[0J', end='')
        max_lines = max((len(self.agent_outputs[agent_id]) for agent_id in self.agent_ids)) if self.agent_outputs else 0
        if self.num_agents == 1:
            for i in range(max_lines):
                line = self.agent_outputs[self.agent_ids[0]][i] if i < len(self.agent_outputs[self.agent_ids[0]]) else ''
                print(line)
        else:
            wrapped_outputs = {}
            for agent_id in self.agent_ids:
                wrapped_outputs[agent_id] = []
                for line in self.agent_outputs[agent_id]:
                    if len(line) > self.col_width - 2:
                        words = line.split(' ')
                        current_line = ''
                        for word in words:
                            test_line = current_line + (' ' if current_line else '') + word
                            if len(test_line) > self.col_width - 2:
                                if current_line:
                                    wrapped_outputs[agent_id].append(current_line)
                                    current_line = word
                                else:
                                    wrapped_outputs[agent_id].append(word[:self.col_width - 2] + '…')
                                    current_line = ''
                            else:
                                current_line = test_line
                        if current_line:
                            wrapped_outputs[agent_id].append(current_line)
                    else:
                        wrapped_outputs[agent_id].append(line)
            max_wrapped_lines = max((len(wrapped_outputs[agent_id]) for agent_id in self.agent_ids)) if wrapped_outputs else 0
            for i in range(max_wrapped_lines):
                output_lines = []
                for agent_id in self.agent_ids:
                    line = wrapped_outputs[agent_id][i] if i < len(wrapped_outputs[agent_id]) else ''
                    output_lines.append(f'{line:<{self.col_width}}')
                print(self.separators.join(output_lines))
        print('\n' + '=' * self.terminal_width)
        status_lines = []
        for agent_id in self.agent_ids:
            backend_name = 'Unknown'
            if hasattr(self, 'orchestrator') and self.orchestrator and hasattr(self.orchestrator, 'agents'):
                agent = self.orchestrator.agents.get(agent_id)
                if agent and hasattr(agent, 'backend') and hasattr(agent.backend, 'get_provider_name'):
                    try:
                        backend_name = agent.backend.get_provider_name()
                    except Exception:
                        backend_name = 'Unknown'
            status_text = f'{agent_id.upper()} ({backend_name}): {self.agent_status[agent_id]}'
            status_lines.append(f'{status_text:^{self.col_width}}')
        if self.num_agents == 1:
            print(status_lines[0])
        else:
            print(self.separators.join(status_lines))
        print('=' * self.terminal_width)
        if self.orchestrator_events:
            print('\n📋 RECENT COORDINATION EVENTS:')
            recent_events = self.orchestrator_events[-2:]
            for event in recent_events:
                print(f'   • {event}')
        print()

def __init__(self, agent_ids: List[str], **kwargs):
    """Initialize terminal display.

        Args:
            agent_ids: List of agent IDs to display
            **kwargs: Additional configuration options
                - terminal_width: Override terminal width (default: auto-detect)
                - max_events: Max coordination events to show (default: 5)
        """
    super().__init__(agent_ids, **kwargs)
    self.terminal_width = kwargs.get('terminal_width', self._get_terminal_width())
    self.max_events = kwargs.get('max_events', 5)
    self.num_agents = len(agent_ids)
    self.log_filename = None
    self._last_refresh_time = 0
    if self.num_agents == 1:
        self.col_width = self.terminal_width - 4
        self.separators = ''
    elif self.num_agents == 2:
        self.col_width = (self.terminal_width - 3) // 2
        self.separators = ' │ '
    else:
        self.col_width = (self.terminal_width - (self.num_agents - 1) * 3) // self.num_agents
        self.separators = ' │ '

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

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key='lm-studio', **kwargs)
    self._models_attempted = set()
    self.start_lmstudio_server(**kwargs)

class AzureOpenAIBackend(LLMBackend):
    """Azure OpenAI backend using the official Azure OpenAI client.

    Supports Azure OpenAI deployments with proper Azure authentication and configuration.

    Environment Variables:
        AZURE_OPENAI_API_KEY: Azure OpenAI API key
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        AZURE_OPENAI_API_VERSION: Azure OpenAI API version (optional, defaults to 2024-12-01-preview)
    """

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('Azure OpenAI API key is required. Set AZURE_OPENAI_API_KEY environment variable or pass api_key parameter.')

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return 'Azure OpenAI'

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a response with tool calling support using Azure OpenAI.

        Args:
            messages: Conversation messages
            tools: Available tools schema
            **kwargs: Additional parameters including model (deployment name)
        """
        agent_id = kwargs.get('agent_id', None)
        log_backend_activity(self.get_provider_name(), 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        try:
            all_params = {**self.config, **kwargs}
            from openai import AsyncAzureOpenAI
            azure_endpoint = all_params.get('azure_endpoint') or all_params.get('base_url') or os.getenv('AZURE_OPENAI_ENDPOINT')
            api_version = all_params.get('api_version') or os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
            if not azure_endpoint:
                raise ValueError('Azure OpenAI endpoint URL is required. Set AZURE_OPENAI_ENDPOINT environment variable or pass azure_endpoint/base_url parameter.')
            if not api_version:
                raise ValueError('Azure OpenAI API version is required. Set AZURE_OPENAI_API_VERSION environment variable or pass api_version parameter.')
            if azure_endpoint.endswith('/'):
                azure_endpoint = azure_endpoint[:-1]
            self.client = AsyncAzureOpenAI(api_version=api_version, azure_endpoint=azure_endpoint, api_key=self.api_key)
            deployment_name = all_params.get('model')
            if not deployment_name:
                raise ValueError("Azure OpenAI requires a deployment name. Pass it as the 'model' parameter.")
            workflow_tools = [t for t in tools if t.get('function', {}).get('name') in ['new_answer', 'vote']] if tools else []
            has_workflow_tools = len(workflow_tools) > 0
            modified_messages = self._prepare_messages_with_workflow_tools(messages, workflow_tools) if has_workflow_tools else messages
            log_backend_agent_message(agent_id or 'default', 'SEND', {'messages': modified_messages, 'tools': len(tools) if tools else 0}, backend_name=self.get_provider_name())
            api_params = {'messages': modified_messages, 'model': deployment_name, 'stream': True}
            if tools and len(tools) > 0:
                converted_tools = self._convert_tools_format(tools)
                api_params['tools'] = converted_tools
            else:
                api_params['tool_choice'] = 'none'
            excluded_params = self.get_base_excluded_config_params() | {'model', 'messages', 'stream', 'tools'}
            for key, value in kwargs.items():
                if key not in excluded_params and value is not None:
                    api_params[key] = value
            stream = await self.client.chat.completions.create(**api_params)
            accumulated_content = ''
            complete_response = ''
            last_yield_type = None
            async for chunk in stream:
                converted = self._convert_chunk_to_stream_chunk(chunk)
                if converted.type == 'content' and converted.content:
                    accumulated_content += converted.content
                    complete_response += converted.content
                    if len(accumulated_content) >= 10 or ' ' in accumulated_content:
                        log_backend_agent_message(agent_id or 'default', 'RECV', {'content': accumulated_content}, backend_name=self.get_provider_name())
                        log_stream_chunk('backend.azure_openai', 'content', accumulated_content, agent_id)
                        yield StreamChunk(type='content', content=accumulated_content)
                        accumulated_content = ''
                elif converted.type != 'content':
                    if converted.type == 'error':
                        log_stream_chunk('backend.azure_openai', 'error', converted.error, agent_id)
                    elif converted.type == 'done':
                        log_stream_chunk('backend.azure_openai', 'done', None, agent_id)
                    last_yield_type = converted.type
                    yield converted
            if accumulated_content:
                log_backend_agent_message(agent_id or 'default', 'RECV', {'content': accumulated_content}, backend_name=self.get_provider_name())
                log_stream_chunk('backend.azure_openai', 'content', accumulated_content, agent_id)
                yield StreamChunk(type='content', content=accumulated_content)
            if has_workflow_tools:
                workflow_tool_calls = self._extract_workflow_tool_calls(complete_response)
                if workflow_tool_calls:
                    log_stream_chunk('backend.azure_openai', 'tool_calls', workflow_tool_calls, agent_id)
                    yield StreamChunk(type='tool_calls', tool_calls=workflow_tool_calls)
                    last_yield_type = 'tool_calls'
            if last_yield_type != 'done':
                log_stream_chunk('backend.azure_openai', 'done', None, agent_id)
                yield StreamChunk(type='done')
        except Exception as e:
            error_msg = f'Azure OpenAI API error: {str(e)}'
            log_stream_chunk('backend.azure_openai', 'error', error_msg, agent_id)
            yield StreamChunk(type='error', error=error_msg)

    def _prepare_messages_with_workflow_tools(self, messages: List[Dict[str, Any]], workflow_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages with workflow tool instructions."""
        if not workflow_tools:
            return messages
        system_message = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_message = msg
                break
        enhanced_system = self._build_workflow_tools_system_prompt(system_message.get('content', '') if system_message else '', workflow_tools)
        new_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                new_messages.append({'role': 'system', 'content': enhanced_system})
            else:
                new_messages.append(msg)
        return new_messages

    def _build_workflow_tools_system_prompt(self, base_system: str, workflow_tools: List[Dict[str, Any]]) -> str:
        """Build system prompt with workflow tool instructions."""
        system_parts = []
        if base_system:
            system_parts.append(base_system)
        if workflow_tools:
            system_parts.append('\n--- Available Tools ---')
            for tool in workflow_tools:
                name = tool.get('function', {}).get('name', 'unknown')
                description = tool.get('function', {}).get('description', 'No description')
                system_parts.append(f'- {name}: {description}')
                if name == 'new_answer':
                    system_parts.append('    Usage: {"tool_name": "new_answer", "arguments": {"content": "your answer"}}')
                elif name == 'vote':
                    agent_id_enum = None
                    for t in workflow_tools:
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
            system_parts.append('\n--- MassGen Workflow Instructions ---')
            system_parts.append('IMPORTANT: You must respond with a structured JSON decision at the end of your response.')
            system_parts.append('You must use the coordination tools (new_answer, vote) to participate in multi-agent workflows.')
            system_parts.append('The JSON MUST be formatted as a strict JSON code block:')
            system_parts.append('1. Start with ```json on one line')
            system_parts.append('2. Include your JSON content (properly formatted)')
            system_parts.append('3. End with ``` on one line')
            system_parts.append('Example format:\n```json\n{"tool_name": "vote", "arguments": {"agent_id": "agent1", "reason": "explanation"}}\n```')
            system_parts.append('The JSON block should be placed at the very end of your response, after your analysis.')
        return '\n'.join(system_parts)

    def _extract_workflow_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract workflow tool calls from content."""
        try:
            import json
            import re
            markdown_json_pattern = '```json\\s*(\\{.*?\\})\\s*```'
            markdown_matches = re.findall(markdown_json_pattern, content, re.DOTALL)
            for match in reversed(markdown_matches):
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        tool_call = {'id': f'call_{hash(match) % 10000}', 'type': 'function', 'function': {'name': parsed['tool_name'], 'arguments': json.dumps(parsed['arguments'])}}
                        return [tool_call]
                except json.JSONDecodeError:
                    continue
            json_pattern = '\\{[^{}]*"tool_name"[^{}]*\\}'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            for match in json_matches:
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'tool_name' in parsed:
                        tool_call = {'id': f'call_{hash(match) % 10000}', 'type': 'function', 'function': {'name': parsed['tool_name'], 'arguments': json.dumps(parsed['arguments'])}}
                        return [tool_call]
                except json.JSONDecodeError:
                    continue
            return []
        except Exception:
            return []

    def _convert_tools_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Azure OpenAI format if needed."""
        return tools

    def _convert_chunk_to_stream_chunk(self, chunk) -> StreamChunk:
        """Convert Azure OpenAI chunk to MassGen StreamChunk format."""
        try:
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, 'delta') and choice.delta:
                    delta = choice.delta
                    if hasattr(delta, 'content') and delta.content:
                        return StreamChunk(type='content', content=delta.content)
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        tool_call_text = ''
                        for tool_call in delta.tool_calls:
                            if hasattr(tool_call, 'function') and tool_call.function:
                                if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                    tool_call_text += tool_call.function.arguments
                        if tool_call_text:
                            return StreamChunk(type='content', content=tool_call_text)
                    if hasattr(choice, 'finish_reason') and choice.finish_reason:
                        if choice.finish_reason == 'stop':
                            return StreamChunk(type='done')
                        elif choice.finish_reason == 'tool_calls':
                            return StreamChunk(type='done')
            return StreamChunk(type='content', content='')
        except Exception as e:
            return StreamChunk(type='error', error=f'Error processing chunk: {str(e)}')

    def extract_tool_call_id(self, tool_call: Dict[str, Any]) -> str:
        """Extract tool call id from Chat Completions-style tool call."""
        return tool_call.get('id', '')

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
    if not self.api_key:
        raise ValueError('Azure OpenAI API key is required. Set AZURE_OPENAI_API_KEY environment variable or pass api_key parameter.')

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

class InferenceBackend(ChatCompletionsBackend):
    """Backend for local inference servers (vLLM and SGLang).

    This backend connects to inference servers running with OpenAI-compatible API.
    It supports both vLLM and SGLang specific parameters like guided generation,
    thinking mode, and separate reasoning.
    """

    def __init__(self, backend_type: str='vllm', api_key: Optional[str]=None, **kwargs):
        """Initialize inference backend.

        Args:
            backend_type: Type of backend ("vllm" or "sglang")
            api_key: API key (usually "EMPTY" for local servers)
            **kwargs: Additional arguments passed to parent
        """
        self._backend_type = backend_type.lower()
        if 'base_url' not in kwargs:
            if self._backend_type == 'sglang':
                kwargs['base_url'] = 'http://localhost:30000/v1'
            else:
                kwargs['base_url'] = 'http://localhost:8000/v1'
        if api_key is None:
            if self._backend_type == 'sglang':
                api_key = os.getenv('SGLANG_API_KEY') or 'EMPTY'
            else:
                api_key = os.getenv('VLLM_API_KEY') or 'EMPTY'
        super().__init__(api_key, **kwargs)
        self.api_params_handler = InferenceAPIParamsHandler(self)

    def get_provider_name(self) -> str:
        """Get the provider name for this backend."""
        if self._backend_type == 'sglang':
            return 'SGLang'
        return 'vLLM'

    def _build_extra_body(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Build backend-specific extra_body parameters and strip them from kwargs.

        Args:
            kwargs: Keyword arguments that may contain backend parameters

        Returns:
            Dictionary of backend-specific parameters for extra_body
        """
        extra_body: Dict[str, Any] = {}
        top_k = kwargs.pop('top_k', None)
        if top_k is not None:
            extra_body['top_k'] = top_k
        repetition_penalty = kwargs.pop('repetition_penalty', None)
        if repetition_penalty is not None:
            extra_body['repetition_penalty'] = repetition_penalty
        chat_template_kwargs = kwargs.pop('chat_template_kwargs', None)
        if chat_template_kwargs is not None:
            extra_body['chat_template_kwargs'] = chat_template_kwargs
        if self._backend_type == 'sglang':
            separate_reasoning = kwargs.pop('separate_reasoning', None)
            if separate_reasoning is not None:
                extra_body['separate_reasoning'] = separate_reasoning
        return extra_body

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI-compatible Chat Completions API with backend-specific parameters.

        Args:
            messages: List of messages
            tools: List of tool definitions
            **kwargs: Additional parameters including backend-specific ones

        Yields:
            StreamChunk objects
        """
        extra_body = self._build_extra_body(kwargs)
        if extra_body:
            if 'extra_body' in kwargs:
                kwargs['extra_body'].update(extra_body)
            else:
                kwargs['extra_body'] = extra_body
        async for chunk in super().stream_with_tools(messages, tools, **kwargs):
            yield chunk

    def get_supported_builtin_tools(self) -> List[str]:
        """Return list of supported builtin tools.

        Local inference servers (vLLM/SGLang) do not provide provider-specific builtin tools.
        """
        return []

def __init__(self, backend_type: str='vllm', api_key: Optional[str]=None, **kwargs):
    """Initialize inference backend.

        Args:
            backend_type: Type of backend ("vllm" or "sglang")
            api_key: API key (usually "EMPTY" for local servers)
            **kwargs: Additional arguments passed to parent
        """
    self._backend_type = backend_type.lower()
    if 'base_url' not in kwargs:
        if self._backend_type == 'sglang':
            kwargs['base_url'] = 'http://localhost:30000/v1'
        else:
            kwargs['base_url'] = 'http://localhost:8000/v1'
    if api_key is None:
        if self._backend_type == 'sglang':
            api_key = os.getenv('SGLANG_API_KEY') or 'EMPTY'
        else:
            api_key = os.getenv('VLLM_API_KEY') or 'EMPTY'
    super().__init__(api_key, **kwargs)
    self.api_params_handler = InferenceAPIParamsHandler(self)

def _build_extra_body(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Build backend-specific extra_body parameters and strip them from kwargs.

        Args:
            kwargs: Keyword arguments that may contain backend parameters

        Returns:
            Dictionary of backend-specific parameters for extra_body
        """
    extra_body: Dict[str, Any] = {}
    top_k = kwargs.pop('top_k', None)
    if top_k is not None:
        extra_body['top_k'] = top_k
    repetition_penalty = kwargs.pop('repetition_penalty', None)
    if repetition_penalty is not None:
        extra_body['repetition_penalty'] = repetition_penalty
    chat_template_kwargs = kwargs.pop('chat_template_kwargs', None)
    if chat_template_kwargs is not None:
        extra_body['chat_template_kwargs'] = chat_template_kwargs
    if self._backend_type == 'sglang':
        separate_reasoning = kwargs.pop('separate_reasoning', None)
        if separate_reasoning is not None:
            extra_body['separate_reasoning'] = separate_reasoning
    return extra_body

class ChatCompletionsBackend(MCPBackend):
    """Complete OpenAI-compatible Chat Completions API backend.

    Can be used directly with any OpenAI-compatible provider by setting provider name.
    Supports Cerebras AI, Together AI, Fireworks AI, DeepInfra, and other compatible providers.

    Environment Variables:
        Provider-specific API keys are automatically detected based on provider name.
        See ProviderRegistry.PROVIDERS for the complete list.

    """

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.backend_name = self.get_provider_name()
        self.formatter = ChatCompletionsFormatter()
        self.api_params_handler = ChatCompletionsAPIParamsHandler(self)

    def supports_upload_files(self) -> bool:
        """Chat Completions backend supports upload_files preprocessing."""
        return True

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI Response API with unified MCP/non-MCP processing."""
        async for chunk in super().stream_with_tools(messages, tools, **kwargs):
            yield chunk

    async def _stream_with_mcp_tools(self, current_messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Recursively stream MCP responses, executing function calls as needed."""
        all_params = {**self.config, **kwargs}
        api_params = await self.api_params_handler.build_api_params(current_messages, tools, all_params)
        provider_tools = self.api_params_handler.get_provider_tools(all_params)
        if provider_tools:
            if 'tools' not in api_params:
                api_params['tools'] = []
            api_params['tools'].extend(provider_tools)
        stream = await client.chat.completions.create(**api_params)
        captured_function_calls = []
        current_tool_calls = {}
        response_completed = False
        content = ''
        async for chunk in stream:
            try:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta
                        if getattr(delta, 'content', None):
                            content_chunk = delta.content
                            content += content_chunk
                            yield StreamChunk(type='content', content=content_chunk)
                        if getattr(delta, 'tool_calls', None):
                            for tool_call_delta in delta.tool_calls:
                                index = getattr(tool_call_delta, 'index', 0)
                                if index not in current_tool_calls:
                                    current_tool_calls[index] = {'id': '', 'function': {'name': '', 'arguments': ''}}
                                if getattr(tool_call_delta, 'id', None):
                                    current_tool_calls[index]['id'] = tool_call_delta.id
                                if hasattr(tool_call_delta, 'function') and tool_call_delta.function:
                                    if getattr(tool_call_delta.function, 'name', None):
                                        current_tool_calls[index]['function']['name'] = tool_call_delta.function.name
                                    if getattr(tool_call_delta.function, 'arguments', None):
                                        current_tool_calls[index]['function']['arguments'] += tool_call_delta.function.arguments
                    if getattr(choice, 'finish_reason', None):
                        if choice.finish_reason == 'tool_calls' and current_tool_calls:
                            final_tool_calls = []
                            for index in sorted(current_tool_calls.keys()):
                                call = current_tool_calls[index]
                                function_name = call['function']['name']
                                arguments_str = call['function']['arguments']
                                arguments_str_sanitized = arguments_str if arguments_str.strip() else '{}'
                                final_tool_calls.append({'id': call['id'], 'type': 'function', 'function': {'name': function_name, 'arguments': arguments_str_sanitized}})
                            for tool_call in final_tool_calls:
                                args_value = tool_call['function']['arguments']
                                if not isinstance(args_value, str):
                                    args_value = self.formatter._serialize_tool_arguments(args_value)
                                captured_function_calls.append({'call_id': tool_call['id'], 'name': tool_call['function']['name'], 'arguments': args_value})
                            yield StreamChunk(type='tool_calls', tool_calls=final_tool_calls)
                            response_completed = True
                            break
                        elif choice.finish_reason in ['stop', 'length']:
                            response_completed = True
                            yield StreamChunk(type='done')
                            return
            except Exception as chunk_error:
                yield StreamChunk(type='error', error=f'Chunk processing error: {chunk_error}')
                continue
        if captured_function_calls and response_completed:
            non_mcp_functions = [call for call in captured_function_calls if call['name'] not in self._mcp_functions]
            if non_mcp_functions:
                logger.info(f'Non-MCP function calls detected (will be ignored in MCP execution): {[call['name'] for call in non_mcp_functions]}')
            if not await self._check_circuit_breaker_before_execution():
                yield StreamChunk(type='mcp_status', status='mcp_blocked', content='⚠️ [MCP] All servers blocked by circuit breaker', source='circuit_breaker')
                yield StreamChunk(type='done')
                return
            mcp_functions_executed = False
            updated_messages = current_messages.copy()
            if self.is_planning_mode_enabled():
                logger.info('[MCP] Planning mode enabled - blocking all MCP tool execution')
                yield StreamChunk(type='mcp_status', status='planning_mode_blocked', content='🚫 [MCP] Planning mode active - MCP tools blocked during coordination', source='planning_mode')
                yield StreamChunk(type='done')
                return
            if captured_function_calls:
                all_tool_calls = []
                for call in captured_function_calls:
                    all_tool_calls.append({'id': call['call_id'], 'type': 'function', 'function': {'name': call['name'], 'arguments': self.formatter._serialize_tool_arguments(call['arguments'])}})
                if all_tool_calls:
                    assistant_message = {'role': 'assistant', 'content': content.strip() if content.strip() else None, 'tool_calls': all_tool_calls}
                    updated_messages.append(assistant_message)
            tool_results = []
            for call in captured_function_calls:
                function_name = call['name']
                if self.is_mcp_tool_call(function_name):
                    yield StreamChunk(type='mcp_status', status='mcp_tool_called', content=f'🔧 [MCP Tool] Calling {function_name}...', source=f'mcp_{function_name}')
                    tools_info = f' ({len(self._mcp_functions)} tools available)' if self._mcp_functions else ''
                    yield StreamChunk(type='mcp_status', status='mcp_tools_initiated', content=f'MCP tool call initiated (call #{self._mcp_tool_calls_count}){tools_info}: {function_name}', source=f'mcp_{function_name}')
                    try:
                        result_str, result_obj = await self._execute_mcp_function_with_retry(function_name, call['arguments'])
                        if isinstance(result_str, str) and result_str.startswith('Error:'):
                            logger.warning(f'MCP function {function_name} failed after retries: {result_str}')
                            tool_results.append({'tool_call_id': call['call_id'], 'content': result_str, 'success': False})
                        else:
                            yield StreamChunk(type='mcp_status', status='mcp_tools_success', content=f'MCP tool call succeeded (call #{self._mcp_tool_calls_count})', source=f'mcp_{function_name}')
                            tool_results.append({'tool_call_id': call['call_id'], 'content': result_str, 'success': True, 'result_obj': result_obj})
                    except Exception as e:
                        logger.error(f'Unexpected error in MCP function execution: {e}')
                        error_msg = f'Error executing {function_name}: {str(e)}'
                        tool_results.append({'tool_call_id': call['call_id'], 'content': error_msg, 'success': False})
                        continue
                    yield StreamChunk(type='mcp_status', status='function_call', content=f'Arguments for Calling {function_name}: {call['arguments']}', source=f'mcp_{function_name}')
                    logger.info(f'Executed MCP function {function_name} (stdio/streamable-http)')
                    mcp_functions_executed = True
                else:
                    logger.info(f'Non-MCP function {function_name} detected, creating placeholder response')
                    tool_results.append({'tool_call_id': call['call_id'], 'content': f'Function {function_name} is not available in this MCP session.', 'success': False})
            for result in tool_results:
                result_text = str(result['content'])
                if result.get('success') and hasattr(result.get('result_obj'), 'content') and result['result_obj'].content:
                    obj = result['result_obj']
                    if isinstance(obj.content, list) and len(obj.content) > 0:
                        first_item = obj.content[0]
                        if hasattr(first_item, 'text'):
                            result_text = first_item.text
                yield StreamChunk(type='mcp_status', status='function_call_output', content=f'Results for Calling {function_name}: {result_text}', source=f'mcp_{function_name}')
                function_output_msg = {'role': 'tool', 'tool_call_id': result['tool_call_id'], 'content': result['content']}
                updated_messages.append(function_output_msg)
                yield StreamChunk(type='mcp_status', status='mcp_tool_response', content=f'✅ [MCP Tool] {function_name} completed', source=f'mcp_{function_name}')
            if mcp_functions_executed:
                updated_messages = self._trim_message_history(updated_messages)
                async for chunk in self._stream_with_mcp_tools(updated_messages, tools, client, **kwargs):
                    yield chunk
            else:
                yield StreamChunk(type='done')
                return
        elif response_completed:
            yield StreamChunk(type='mcp_status', status='mcp_session_complete', content='✅ [MCP] Session completed', source='mcp_session')
            return

    async def _process_stream(self, stream, all_params, agent_id) -> AsyncGenerator[StreamChunk, None]:
        """Handle standard Chat Completions API streaming format with logging."""
        content = ''
        current_tool_calls = {}
        search_sources_used = 0
        provider_name = self.get_provider_name()
        enable_web_search = all_params.get('enable_web_search', False)
        log_prefix = f'backend.{provider_name.lower().replace(' ', '_')}'
        async for chunk in stream:
            try:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta
                        if getattr(delta, 'content', None):
                            reasoning_chunk = self._handle_reasoning_transition(log_prefix, agent_id)
                            if reasoning_chunk:
                                yield reasoning_chunk
                            content_chunk = delta.content
                            content += content_chunk
                            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': content_chunk}, backend_name=provider_name)
                            log_stream_chunk(log_prefix, 'content', content_chunk, agent_id)
                            yield StreamChunk(type='content', content=content_chunk)
                        if getattr(delta, 'reasoning_content', None):
                            reasoning_active_key = '_reasoning_active'
                            setattr(self, reasoning_active_key, True)
                            thinking_delta = getattr(delta, 'reasoning_content')
                            if thinking_delta:
                                log_stream_chunk(log_prefix, 'reasoning', thinking_delta, agent_id)
                                yield StreamChunk(type='reasoning', content=thinking_delta, reasoning_delta=thinking_delta)
                        if getattr(delta, 'tool_calls', None):
                            reasoning_chunk = self._handle_reasoning_transition(log_prefix, agent_id)
                            if reasoning_chunk:
                                yield reasoning_chunk
                            for tool_call_delta in delta.tool_calls:
                                index = getattr(tool_call_delta, 'index', 0)
                                if index not in current_tool_calls:
                                    current_tool_calls[index] = {'id': '', 'function': {'name': '', 'arguments': ''}}
                                if getattr(tool_call_delta, 'id', None):
                                    current_tool_calls[index]['id'] = tool_call_delta.id
                                if hasattr(tool_call_delta, 'function') and tool_call_delta.function:
                                    if getattr(tool_call_delta.function, 'name', None):
                                        current_tool_calls[index]['function']['name'] = tool_call_delta.function.name
                                    if getattr(tool_call_delta.function, 'arguments', None):
                                        current_tool_calls[index]['function']['arguments'] += tool_call_delta.function.arguments
                    if getattr(choice, 'finish_reason', None):
                        reasoning_chunk = self._handle_reasoning_transition(log_prefix, agent_id)
                        if reasoning_chunk:
                            yield reasoning_chunk
                        if choice.finish_reason == 'tool_calls' and current_tool_calls:
                            final_tool_calls = []
                            for index in sorted(current_tool_calls.keys()):
                                call = current_tool_calls[index]
                                function_name = call['function']['name']
                                arguments_str = call['function']['arguments']
                                arguments_str_sanitized = arguments_str if arguments_str.strip() else '{}'
                                final_tool_calls.append({'id': call['id'], 'type': 'function', 'function': {'name': function_name, 'arguments': arguments_str_sanitized}})
                            log_stream_chunk(log_prefix, 'tool_calls', final_tool_calls, agent_id)
                            yield StreamChunk(type='tool_calls', tool_calls=final_tool_calls)
                            complete_message = {'role': 'assistant', 'content': content.strip(), 'tool_calls': final_tool_calls}
                            yield StreamChunk(type='complete_message', complete_message=complete_message)
                            log_stream_chunk(log_prefix, 'done', None, agent_id)
                            yield StreamChunk(type='done')
                            return
                        elif choice.finish_reason in ['stop', 'length']:
                            if search_sources_used > 0:
                                search_complete_msg = f'\n✅ [Live Search Complete] Used {search_sources_used} sources\n'
                                log_stream_chunk(log_prefix, 'content', search_complete_msg, agent_id)
                                yield StreamChunk(type='content', content=search_complete_msg)
                            if hasattr(chunk, 'citations') and chunk.citations:
                                if enable_web_search:
                                    citation_text = '\n📚 **Citations:**\n'
                                    for i, citation in enumerate(chunk.citations, 1):
                                        citation_text += f'{i}. {citation}\n'
                                    log_stream_chunk(log_prefix, 'content', citation_text, agent_id)
                                    yield StreamChunk(type='content', content=citation_text)
                            complete_message = {'role': 'assistant', 'content': content.strip()}
                            yield StreamChunk(type='complete_message', complete_message=complete_message)
                            log_stream_chunk(log_prefix, 'done', None, agent_id)
                            yield StreamChunk(type='done')
                            return
                if hasattr(chunk, 'usage') and chunk.usage:
                    if getattr(chunk.usage, 'num_sources_used', 0) > 0:
                        search_sources_used = chunk.usage.num_sources_used
                        if enable_web_search:
                            search_msg = f'\n📊 [Live Search] Using {search_sources_used} sources for real-time data\n'
                            log_stream_chunk(log_prefix, 'content', search_msg, agent_id)
                            yield StreamChunk(type='content', content=search_msg)
            except Exception as chunk_error:
                error_msg = f'Chunk processing error: {chunk_error}'
                log_stream_chunk(log_prefix, 'error', error_msg, agent_id)
                yield StreamChunk(type='error', error=error_msg)
                continue
        log_stream_chunk(log_prefix, 'done', None, agent_id)
        yield StreamChunk(type='done')

    def create_tool_result_message(self, tool_call: Dict[str, Any], result_content: str) -> Dict[str, Any]:
        """Create tool result message for Chat Completions format."""
        tool_call_id = self.extract_tool_call_id(tool_call)
        return {'role': 'tool', 'tool_call_id': tool_call_id, 'content': result_content}

    def extract_tool_result_content(self, tool_result_message: Dict[str, Any]) -> str:
        """Extract content from Chat Completions tool result message."""
        return tool_result_message.get('content', '')

    def _convert_messages_for_mcp_chat_completions(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages for MCP Chat Completions format if needed."""
        converted_messages = []
        for message in messages:
            if message.get('type') == 'function_call_output':
                converted_message = {'role': 'tool', 'tool_call_id': message.get('call_id'), 'content': message.get('output', '')}
                converted_messages.append(converted_message)
            else:
                converted_messages.append(message.copy())
        return converted_messages

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        if 'provider' in self.config:
            return self.config['provider']
        elif 'provider_name' in self.config:
            return self.config['provider_name']
        base_url = self.config.get('base_url', '')
        if 'openai.com' in base_url:
            return 'OpenAI'
        elif 'cerebras.ai' in base_url:
            return 'Cerebras AI'
        elif 'together.xyz' in base_url:
            return 'Together AI'
        elif 'fireworks.ai' in base_url:
            return 'Fireworks AI'
        elif 'groq.com' in base_url:
            return 'Groq'
        elif 'openrouter.ai' in base_url:
            return 'OpenRouter'
        elif 'z.ai' in base_url or 'bigmodel.cn' in base_url:
            return 'ZAI'
        elif 'nebius.com' in base_url:
            return 'Nebius AI Studio'
        elif 'moonshot.ai' in base_url or 'moonshot.cn' in base_url:
            return 'Kimi'
        elif 'poe.com' in base_url:
            return 'POE'
        elif 'aliyuncs.com' in base_url:
            return 'Qwen'
        else:
            return 'ChatCompletion'

    def get_filesystem_support(self) -> FilesystemSupport:
        """Chat Completions supports filesystem through MCP servers."""
        return FilesystemSupport.MCP

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by this provider."""
        return []

    def _create_client(self, **kwargs) -> AsyncOpenAI:
        """Create OpenAI client with consistent configuration."""
        import openai
        all_params = {**self.config, **kwargs}
        base_url = all_params.get('base_url', 'https://api.openai.com/v1')
        return openai.AsyncOpenAI(api_key=self.api_key, base_url=base_url)

    def _handle_reasoning_transition(self, log_prefix: str, agent_id: Optional[str]) -> Optional[StreamChunk]:
        """Handle reasoning state transition and return StreamChunk if transition occurred."""
        reasoning_active_key = '_reasoning_active'
        if hasattr(self, reasoning_active_key):
            if getattr(self, reasoning_active_key) is True:
                setattr(self, reasoning_active_key, False)
                log_stream_chunk(log_prefix, 'reasoning_done', '', agent_id)
                return StreamChunk(type='reasoning_done', content='')
        return None

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.backend_name = self.get_provider_name()
    self.formatter = ChatCompletionsFormatter()
    self.api_params_handler = ChatCompletionsAPIParamsHandler(self)

class ExternalAgentBackend(LLMBackend):
    """
    Backend for integrating external agent frameworks through adapters.

    This backend acts as a bridge between MassGen's orchestration system
    and external agent frameworks like AG2 (AutoGen), LangChain, etc.
    """

    def __init__(self, adapter_type: str, api_key: Optional[str]=None, **kwargs):
        """
        Initialize external agent backend.

        Args:
            adapter_type: Framework/adapter type (e.g., "ag2", "langchain")
            api_key: Optional API key for frameworks that need it
            **kwargs: Framework-specific configuration
        """
        self.adapter_type = adapter_type.lower()
        if self.adapter_type not in adapter_registry:
            raise ValueError(f'Unsupported framework: {self.adapter_type}. Supported frameworks: {', '.join(adapter_registry.keys())}')
        adapter_class = adapter_registry[self.adapter_type]
        adapter_config = self._extract_adapter_config(kwargs)
        self.adapter = adapter_class(**adapter_config)
        super().__init__(api_key=api_key, **kwargs)

    def _extract_adapter_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract framework-specific configuration."""
        excluded_params = self.get_base_excluded_config_params()
        excluded_params.update({''})
        return {k: v for k, v in config.items() if k not in excluded_params}

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from external agent with tool support.

        Args:
            messages: Conversation messages
            tools: Available tools
            **kwargs: Additional parameters

        Yields:
            StreamChunk: Response chunks
        """
        if self.coordination_stage:
            self.adapter.set_stage(self.coordination_stage)
        async for chunk in self.adapter.execute_streaming(messages, tools, **kwargs):
            yield chunk

    def get_provider_name(self) -> str:
        """Get provider name."""
        return f'{self.adapter_type}'

    def get_filesystem_support(self) -> FilesystemSupport:
        """
        External agents typically use MCP for filesystem operations.

        Some frameworks may have their own filesystem tools, but we
        standardize on MCP for consistency.
        """
        if hasattr(self.adapter, 'get_filesystem_support'):
            return self.adapter.get_filesystem_support()
        return FilesystemSupport.MCP

    def is_stateful(self) -> bool:
        """Check if this backend maintains conversation state."""
        if hasattr(self.adapter, 'is_stateful'):
            return self.adapter.is_stateful()
        return False

    def clear_history(self) -> None:
        """Clear conversation history."""
        if hasattr(self.adapter, 'clear_history'):
            self.adapter.clear_history()

    def reset_state(self) -> None:
        """Reset backend state."""
        if hasattr(self.adapter, 'reset_state'):
            self.adapter.reset_state()

def __init__(self, adapter_type: str, api_key: Optional[str]=None, **kwargs):
    """
        Initialize external agent backend.

        Args:
            adapter_type: Framework/adapter type (e.g., "ag2", "langchain")
            api_key: Optional API key for frameworks that need it
            **kwargs: Framework-specific configuration
        """
    self.adapter_type = adapter_type.lower()
    if self.adapter_type not in adapter_registry:
        raise ValueError(f'Unsupported framework: {self.adapter_type}. Supported frameworks: {', '.join(adapter_registry.keys())}')
    adapter_class = adapter_registry[self.adapter_type]
    adapter_config = self._extract_adapter_config(kwargs)
    self.adapter = adapter_class(**adapter_config)
    super().__init__(api_key=api_key, **kwargs)

class ResponseBackend(MCPBackend):
    """Backend using the standard Response API format with multimodal support."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.formatter = ResponseFormatter()
        self.api_params_handler = ResponseAPIParamsHandler(self)
        self._pending_image_saves = []
        self._vector_store_ids: List[str] = []
        self._uploaded_file_ids: List[str] = []

    def supports_upload_files(self) -> bool:
        return True

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using OpenAI Response API with unified MCP/non-MCP processing.

        Wraps parent implementation to ensure File Search cleanup happens after streaming completes.
        """
        try:
            async for chunk in super().stream_with_tools(messages, tools, **kwargs):
                yield chunk
        finally:
            await self._cleanup_file_search_if_needed(**kwargs)

    async def _cleanup_file_search_if_needed(self, **kwargs) -> None:
        """Cleanup File Search resources if needed."""
        if not (self._vector_store_ids or self._uploaded_file_ids):
            return
        agent_id = kwargs.get('agent_id')
        logger.info('Cleaning up File Search resources...')
        client = None
        try:
            client = self._create_client(**kwargs)
            await self._cleanup_file_search_resources(client, agent_id)
        except Exception as cleanup_error:
            logger.error(f'Error during File Search cleanup: {cleanup_error}', extra={'agent_id': agent_id})
        finally:
            if client and hasattr(client, 'aclose'):
                try:
                    await client.aclose()
                except Exception:
                    pass

    async def _stream_without_mcp_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        agent_id = kwargs.get('agent_id')
        all_params = {**self.config, **kwargs}
        processed_messages = await self._process_upload_files(messages, all_params)
        if all_params.get('_has_file_search_files'):
            logger.info('Processing File Search uploads...')
            processed_messages, vector_store_id = await self._upload_files_and_create_vector_store(processed_messages, client, agent_id)
            if vector_store_id:
                existing_ids = list(all_params.get('_file_search_vector_store_ids', []))
                existing_ids.append(vector_store_id)
                all_params['_file_search_vector_store_ids'] = existing_ids
                logger.info(f'File Search enabled with vector store: {vector_store_id}')
            all_params.pop('_has_file_search_files', None)
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
        stream = await client.responses.create(**api_params)
        async for chunk in self._process_stream(stream, all_params, agent_id):
            yield chunk

    async def _stream_with_mcp_tools(self, current_messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], client, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Recursively stream MCP responses, executing function calls as needed."""
        agent_id = kwargs.get('agent_id')
        all_params = {**self.config, **kwargs}
        if all_params.get('_has_file_search_files'):
            logger.info('Processing File Search uploads...')
            current_messages, vector_store_id = await self._upload_files_and_create_vector_store(current_messages, client, agent_id)
            if vector_store_id:
                existing_ids = list(all_params.get('_file_search_vector_store_ids', []))
                existing_ids.append(vector_store_id)
                all_params['_file_search_vector_store_ids'] = existing_ids
                logger.info(f'File Search enabled with vector store: {vector_store_id}')
            all_params.pop('_has_file_search_files', None)
        api_params = await self.api_params_handler.build_api_params(current_messages, tools, all_params)
        stream = await client.responses.create(**api_params)
        captured_function_calls = []
        current_function_call = None
        response_completed = False
        async for chunk in stream:
            if hasattr(chunk, 'type'):
                if chunk.type == 'response.output_item.added' and hasattr(chunk, 'item') and chunk.item and (getattr(chunk.item, 'type', None) == 'function_call'):
                    current_function_call = {'call_id': getattr(chunk.item, 'call_id', ''), 'name': getattr(chunk.item, 'name', ''), 'arguments': ''}
                    logger.info(f'Function call detected: {current_function_call['name']}')
                elif chunk.type == 'response.function_call_arguments.delta' and current_function_call is not None:
                    delta = getattr(chunk, 'delta', '')
                    current_function_call['arguments'] += delta
                elif chunk.type == 'response.output_item.done' and current_function_call is not None:
                    captured_function_calls.append(current_function_call)
                    current_function_call = None
                elif chunk.type == 'response.output_text.delta':
                    delta = getattr(chunk, 'delta', '')
                    yield TextStreamChunk(type=ChunkType.CONTENT, content=delta, source='response_api')
                else:
                    result = self._process_stream_chunk(chunk, agent_id)
                    yield result
                if chunk.type == 'response.completed':
                    response_completed = True
                    if captured_function_calls:
                        break
                    else:
                        yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                        return
        if captured_function_calls and response_completed:
            non_mcp_functions = [call for call in captured_function_calls if call['name'] not in self._mcp_functions]
            if non_mcp_functions:
                logger.info(f'Non-MCP function calls detected: {[call['name'] for call in non_mcp_functions]}. Ending MCP processing.')
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                return
            if not await super()._check_circuit_breaker_before_execution():
                logger.warning('All MCP servers blocked by circuit breaker')
                yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_blocked', content='⚠️ [MCP] All servers blocked by circuit breaker', source='circuit_breaker')
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                return
            mcp_functions_executed = False
            updated_messages = current_messages.copy()
            if self.is_planning_mode_enabled():
                logger.info('[MCP] Planning mode enabled - blocking all MCP tool execution')
                yield StreamChunk(type='mcp_status', status='planning_mode_blocked', content='🚫 [MCP] Planning mode active - MCP tools blocked during coordination', source='planning_mode')
                yield StreamChunk(type='done')
                return
            processed_call_ids = set()
            for call in captured_function_calls:
                function_name = call['name']
                if function_name in self._mcp_functions:
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_tool_called', content=f'🔧 [MCP Tool] Calling {function_name}...', source=f'mcp_{function_name}')
                    try:
                        result, result_obj = await super()._execute_mcp_function_with_retry(function_name, call['arguments'])
                        if isinstance(result, str) and result.startswith('Error:'):
                            logger.warning(f'MCP function {function_name} failed after retries: {result}')
                            function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': function_name, 'arguments': call['arguments']}
                            updated_messages.append(function_call_msg)
                            error_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': result}
                            updated_messages.append(error_output_msg)
                            processed_call_ids.add(call['call_id'])
                            mcp_functions_executed = True
                            continue
                    except Exception as e:
                        logger.error(f'Unexpected error in MCP function execution: {e}')
                        error_msg = f'Error executing {function_name}: {str(e)}'
                        function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': function_name, 'arguments': call['arguments']}
                        updated_messages.append(function_call_msg)
                        error_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': error_msg}
                        updated_messages.append(error_output_msg)
                        processed_call_ids.add(call['call_id'])
                        mcp_functions_executed = True
                        continue
                    function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': function_name, 'arguments': call['arguments']}
                    updated_messages.append(function_call_msg)
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='function_call', content=f'Arguments for Calling {function_name}: {call['arguments']}', source=f'mcp_{function_name}')
                    function_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': str(result)}
                    updated_messages.append(function_output_msg)
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='function_call_output', content=f'Results for Calling {function_name}: {str(result_obj.content[0].text)}', source=f'mcp_{function_name}')
                    logger.info(f'Executed MCP function {function_name} (stdio/streamable-http)')
                    processed_call_ids.add(call['call_id'])
                    yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_tool_response', content=f'✅ [MCP Tool] {function_name} completed', source=f'mcp_{function_name}')
                    mcp_functions_executed = True
            for call in captured_function_calls:
                if call['call_id'] not in processed_call_ids:
                    logger.warning(f'Tool call {call['call_id']} for function {call['name']} was not processed - adding error result')
                    function_call_msg = {'type': 'function_call', 'call_id': call['call_id'], 'name': call['name'], 'arguments': call['arguments']}
                    updated_messages.append(function_call_msg)
                    error_output_msg = {'type': 'function_call_output', 'call_id': call['call_id'], 'output': f'Error: Tool call {call['call_id']} for function {call['name']} was not processed. This may indicate a validation or execution error.'}
                    updated_messages.append(error_output_msg)
                    mcp_functions_executed = True
            if mcp_functions_executed:
                updated_messages = super()._trim_message_history(updated_messages)
                async for chunk in self._stream_with_mcp_tools(updated_messages, tools, client, **kwargs):
                    yield chunk
            else:
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
                return
        elif response_completed:
            yield TextStreamChunk(type=ChunkType.MCP_STATUS, status='mcp_session_complete', content='✅ [MCP] Session completed', source='mcp_session')
            yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
            return

    async def _upload_files_and_create_vector_store(self, messages: List[Dict[str, Any]], client: AsyncOpenAI, agent_id: Optional[str]=None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Upload file_pending_upload items and create a vector store."""
        try:
            pending_files: List[Dict[str, Any]] = []
            file_locations: List[Tuple[int, int]] = []
            for message_index, message in enumerate(messages):
                content = message.get('content')
                if not isinstance(content, list):
                    continue
                for item_index, item in enumerate(content):
                    if isinstance(item, dict) and item.get('type') == 'file_pending_upload':
                        pending_files.append(item)
                        file_locations.append((message_index, item_index))
            if not pending_files:
                return (messages, None)
            uploaded_file_ids: List[str] = []
            http_client: Optional[httpx.AsyncClient] = None
            try:
                for pending in pending_files:
                    source = pending.get('source')
                    if source == 'local':
                        path_str = pending.get('path')
                        if not path_str:
                            logger.warning('Missing local path for file_pending_upload entry')
                            continue
                        file_path = Path(path_str)
                        if not file_path.exists():
                            raise UploadFileError(f'File not found for upload: {file_path}')
                        try:
                            with file_path.open('rb') as file_handle:
                                uploaded_file = await client.files.create(purpose='assistants', file=file_handle)
                        except Exception as exc:
                            raise UploadFileError(f'Failed to upload file {file_path}: {exc}') from exc
                    elif source == 'url':
                        file_url = pending.get('url')
                        if not file_url:
                            logger.warning('Missing URL for file_pending_upload entry')
                            continue
                        parsed = urlparse(file_url)
                        if parsed.scheme not in {'http', 'https'}:
                            raise UploadFileError(f'Unsupported URL scheme for file upload: {file_url}')
                        if http_client is None:
                            http_client = httpx.AsyncClient()
                        try:
                            response = await http_client.get(file_url, timeout=30.0)
                            response.raise_for_status()
                        except httpx.HTTPError as exc:
                            raise UploadFileError(f'Failed to download file from URL {file_url}: {exc}') from exc
                        filename = Path(parsed.path).name or 'remote_file'
                        file_bytes = BytesIO(response.content)
                        try:
                            uploaded_file = await client.files.create(purpose='assistants', file=(filename, file_bytes))
                        except Exception as exc:
                            raise UploadFileError(f'Failed to upload file from URL {file_url}: {exc}') from exc
                    else:
                        raise UploadFileError(f'Unknown file_pending_upload source: {source}')
                    file_id = getattr(uploaded_file, 'id', None)
                    if not file_id:
                        raise UploadFileError('Uploaded file response missing ID')
                    uploaded_file_ids.append(file_id)
                    self._uploaded_file_ids.append(file_id)
                    logger.info(f'Uploaded file for File Search (file_id={file_id})')
            finally:
                if http_client is not None:
                    await http_client.aclose()
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            vector_store_name = f'massgen_file_search_{agent_id or 'default'}_{timestamp}'
            try:
                vector_store = await client.vector_stores.create(name=vector_store_name)
            except Exception as exc:
                raise UploadFileError(f'Failed to create vector store: {exc}') from exc
            vector_store_id = getattr(vector_store, 'id', None)
            if not vector_store_id:
                raise UploadFileError('Vector store response missing ID')
            self._vector_store_ids.append(vector_store_id)
            logger.info('Created vector store for File Search', extra={'vector_store_id': vector_store_id, 'file_count': len(uploaded_file_ids)})
            for file_id in uploaded_file_ids:
                try:
                    vs_file = await client.vector_stores.files.create_and_poll(vector_store_id=vector_store_id, file_id=file_id)
                    logger.info('File indexed and attached to vector store', extra={'vector_store_id': vector_store_id, 'file_id': file_id, 'status': getattr(vs_file, 'status', None)})
                except Exception as exc:
                    raise UploadFileError(f'Failed to attach and index file {file_id} to vector store {vector_store_id}: {exc}') from exc
            if uploaded_file_ids:
                logger.info('All files indexed for File Search; waiting 2s for vector store to stabilize', extra={'vector_store_id': vector_store_id, 'file_count': len(uploaded_file_ids)})
                await asyncio.sleep(2)
            updated_messages = []
            for message in messages:
                cloned = dict(message)
                if isinstance(message.get('content'), list):
                    cloned['content'] = [dict(item) if isinstance(item, dict) else item for item in message['content']]
                updated_messages.append(cloned)
            for message_index, item_index in reversed(file_locations):
                content_list = updated_messages[message_index].get('content')
                if isinstance(content_list, list):
                    content_list.pop(item_index)
                    if not content_list:
                        content_list.append({'type': 'text', 'text': '[Files uploaded for search integration]'})
            return (updated_messages, vector_store_id)
        except Exception as error:
            logger.warning(f'File Search upload failed: {error}. Continuing without file search.')
            return (messages, None)

    async def _cleanup_file_search_resources(self, client: AsyncOpenAI, agent_id: Optional[str]=None) -> None:
        """Clean up File Search vector stores and uploaded files."""
        for vector_store_id in list(self._vector_store_ids):
            try:
                await client.vector_stores.delete(vector_store_id)
                logger.info('Deleted File Search vector store', extra={'vector_store_id': vector_store_id, 'agent_id': agent_id})
            except Exception as exc:
                logger.warning(f'Failed to delete vector store {vector_store_id}: {exc}', extra={'agent_id': agent_id})
        for file_id in list(self._uploaded_file_ids):
            try:
                await client.files.delete(file_id)
                logger.debug('Deleted File Search uploaded file', extra={'file_id': file_id, 'agent_id': agent_id})
            except Exception as exc:
                logger.warning(f'Failed to delete file {file_id}: {exc}', extra={'agent_id': agent_id})
        self._vector_store_ids.clear()
        self._uploaded_file_ids.clear()

    def _convert_mcp_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools (stdio + streamable-http) to OpenAI function declarations."""
        if not self._mcp_functions:
            return []
        converted_tools = []
        for function in self._mcp_functions.values():
            converted_tools.append(function.to_openai_format())
        logger.debug(f'Converted {len(converted_tools)} MCP tools (stdio + streamable-http) to OpenAI format')
        return converted_tools

    async def _process_stream(self, stream, all_params, agent_id=None):
        async for chunk in stream:
            processed = self._process_stream_chunk(chunk, agent_id)
            if processed.type == 'complete_response':
                yield processed
                log_stream_chunk('backend.response', 'done', None, agent_id)
                yield TextStreamChunk(type=ChunkType.DONE, source='response_api')
            else:
                yield processed

    def _process_stream_chunk(self, chunk, agent_id) -> Union[TextStreamChunk, StreamChunk]:
        """
        Process individual stream chunks and convert to appropriate chunk format.

        Returns TextStreamChunk for text/reasoning/tool content,
        or legacy StreamChunk for backward compatibility.
        """
        if not hasattr(chunk, 'type'):
            return StreamChunk(type='content', content='')
        chunk_type = chunk.type
        if chunk_type == 'response.output_text.delta' and hasattr(chunk, 'delta'):
            log_backend_agent_message(agent_id or 'default', 'RECV', {'content': chunk.delta}, backend_name=self.get_provider_name())
            log_stream_chunk('backend.response', 'content', chunk.delta, agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content=chunk.delta, source='response_api')
        elif chunk_type == 'response.reasoning_text.delta' and hasattr(chunk, 'delta'):
            log_stream_chunk('backend.response', 'reasoning', chunk.delta, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING, content=f'🧠 [Reasoning] {chunk.delta}', reasoning_delta=chunk.delta, item_id=getattr(chunk, 'item_id', None), content_index=getattr(chunk, 'content_index', None), source='response_api')
        elif chunk_type == 'response.reasoning_text.done':
            reasoning_text = getattr(chunk, 'text', '')
            log_stream_chunk('backend.response', 'reasoning_done', reasoning_text, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING_DONE, content='\n🧠 [Reasoning Complete]\n', reasoning_text=reasoning_text, item_id=getattr(chunk, 'item_id', None), content_index=getattr(chunk, 'content_index', None), source='response_api')
        elif chunk_type == 'response.reasoning_summary_text.delta' and hasattr(chunk, 'delta'):
            log_stream_chunk('backend.response', 'reasoning_summary', chunk.delta, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING_SUMMARY, content=chunk.delta, reasoning_summary_delta=chunk.delta, item_id=getattr(chunk, 'item_id', None), summary_index=getattr(chunk, 'summary_index', None), source='response_api')
        elif chunk_type == 'response.reasoning_summary_text.done':
            summary_text = getattr(chunk, 'text', '')
            log_stream_chunk('backend.response', 'reasoning_summary_done', summary_text, agent_id)
            return TextStreamChunk(type=ChunkType.REASONING_SUMMARY_DONE, content='\n📋 [Reasoning Summary Complete]\n', reasoning_summary_text=summary_text, item_id=getattr(chunk, 'item_id', None), summary_index=getattr(chunk, 'summary_index', None), source='response_api')
        elif chunk_type == 'response.file_search_call.in_progress':
            item_id = getattr(chunk, 'item_id', None)
            output_index = getattr(chunk, 'output_index', None)
            log_stream_chunk('backend.response', 'file_search', 'Starting file search', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n📁 [File Search] Starting search...', item_id=item_id, content_index=output_index, source='response_api')
        elif chunk_type == 'response.file_search_call.searching':
            item_id = getattr(chunk, 'item_id', None)
            output_index = getattr(chunk, 'output_index', None)
            queries = getattr(chunk, 'queries', None)
            query_text = ''
            if queries:
                try:
                    if isinstance(queries, (list, tuple)):
                        query_text = ', '.join((str(q) for q in queries if q))
                    else:
                        query_text = str(queries)
                except Exception:
                    query_text = ''
            message = '\n📁 [File Search] Searching...'
            if query_text:
                message += f' Query: {query_text}'
            log_stream_chunk('backend.response', 'file_search', f'Searching files{(f' for {query_text}' if query_text else '')}', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content=message, item_id=item_id, content_index=output_index, source='response_api')
        elif chunk_type == 'response.file_search_call.completed':
            item_id = getattr(chunk, 'item_id', None)
            output_index = getattr(chunk, 'output_index', None)
            results = getattr(chunk, 'results', None)
            if results is None:
                results = getattr(chunk, 'search_results', None)
            queries = getattr(chunk, 'queries', None)
            query_text = ''
            if queries:
                try:
                    if isinstance(queries, (list, tuple)):
                        query_text = ', '.join((str(q) for q in queries if q))
                    else:
                        query_text = str(queries)
                except Exception:
                    query_text = ''
            if results is not None:
                try:
                    result_count = len(results)
                except Exception:
                    result_count = None
            else:
                result_count = None
            message_parts = ['\n✅ [File Search] Completed']
            if query_text:
                message_parts.append(f'Query: {query_text}')
            if result_count is not None:
                message_parts.append(f'Results: {result_count}')
            message = ' '.join(message_parts)
            log_stream_chunk('backend.response', 'file_search', f'Completed file search{(f' for {query_text}' if query_text else '')}{(f' with {result_count} results' if result_count is not None else '')}', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content=message, item_id=item_id, content_index=output_index, source='response_api')
        elif chunk_type == 'response.web_search_call.in_progress':
            log_stream_chunk('backend.response', 'web_search', 'Starting search', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🔍 [Provider Tool: Web Search] Starting search...', source='response_api')
        elif chunk_type == 'response.web_search_call.searching':
            log_stream_chunk('backend.response', 'web_search', 'Searching', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🔍 [Provider Tool: Web Search] Searching...', source='response_api')
        elif chunk_type == 'response.web_search_call.completed':
            log_stream_chunk('backend.response', 'web_search', 'Search completed', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Provider Tool: Web Search] Search completed', source='response_api')
        elif chunk_type == 'response.code_interpreter_call.in_progress':
            log_stream_chunk('backend.response', 'code_interpreter', 'Starting execution', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n💻 [Provider Tool: Code Interpreter] Starting execution...', source='response_api')
        elif chunk_type == 'response.code_interpreter_call.executing':
            log_stream_chunk('backend.response', 'code_interpreter', 'Executing', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n💻 [Provider Tool: Code Interpreter] Executing...', source='response_api')
        elif chunk_type == 'response.code_interpreter_call.completed':
            log_stream_chunk('backend.response', 'code_interpreter', 'Execution completed', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Provider Tool: Code Interpreter] Execution completed', source='response_api')
        elif chunk_type == 'response.image_generation_call.in_progress':
            log_stream_chunk('backend.response', 'image_generation', 'Starting image generation', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🎨 [Provider Tool: Image Generation] Starting generation...', source='response_api')
        elif chunk_type == 'response.image_generation_call.generating':
            log_stream_chunk('backend.response', 'image_generation', 'Generating image', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n🎨 [Provider Tool: Image Generation] Generating image...', source='response_api')
        elif chunk_type == 'response.image_generation_call.completed':
            log_stream_chunk('backend.response', 'image_generation', 'Image generation completed', agent_id)
            return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Provider Tool: Image Generation] Image generated successfully', source='response_api')
        elif chunk_type == 'image_generation.completed':
            if hasattr(chunk, 'b64_json'):
                log_stream_chunk('backend.response', 'image_generation', 'Image data received', agent_id)
                return TextStreamChunk(type=ChunkType.CONTENT, content='\n✅ [Image Generation] Image successfully created', source='response_api')
        elif chunk.type == 'response.output_item.done':
            if hasattr(chunk, 'item') and chunk.item:
                if hasattr(chunk.item, 'type') and chunk.item.type == 'web_search_call':
                    if hasattr(chunk.item, 'action') and 'query' in chunk.item.action:
                        search_query = chunk.item.action['query']
                        if search_query:
                            log_stream_chunk('backend.response', 'search_query', search_query, agent_id)
                            return TextStreamChunk(type=ChunkType.CONTENT, content=f"\n🔍 [Search Query] '{search_query}'\n", source='response_api')
                elif hasattr(chunk.item, 'type') and chunk.item.type == 'code_interpreter_call':
                    if hasattr(chunk.item, 'code') and chunk.item.code:
                        log_stream_chunk('backend.response', 'code_executed', chunk.item.code, agent_id)
                        return TextStreamChunk(type=ChunkType.CONTENT, content=f'💻 [Code Executed]\n```\n{chunk.item.code}\n```\n', source='response_api')
                    if hasattr(chunk.item, 'outputs') and chunk.item.outputs:
                        for output in chunk.item.outputs:
                            output_text = None
                            if hasattr(output, 'text') and output.text:
                                output_text = output.text
                            elif hasattr(output, 'content') and output.content:
                                output_text = output.content
                            elif hasattr(output, 'data') and output.data:
                                output_text = str(output.data)
                            elif isinstance(output, str):
                                output_text = output
                            elif isinstance(output, dict):
                                if 'text' in output:
                                    output_text = output['text']
                                elif 'content' in output:
                                    output_text = output['content']
                                elif 'data' in output:
                                    output_text = str(output['data'])
                            if output_text and output_text.strip():
                                log_stream_chunk('backend.response', 'code_result', output_text.strip(), agent_id)
                                return TextStreamChunk(type=ChunkType.CONTENT, content=f'📊 [Result] {output_text.strip()}\n', source='response_api')
                elif hasattr(chunk.item, 'type') and chunk.item.type == 'image_generation_call':
                    if hasattr(chunk.item, 'action') and chunk.item.action:
                        prompt = chunk.item.action.get('prompt', '')
                        size = chunk.item.action.get('size', '1024x1024')
                        if prompt:
                            log_stream_chunk('backend.response', 'image_prompt', prompt, agent_id)
                            return TextStreamChunk(type=ChunkType.CONTENT, content=f"\n🎨 [Image Generated] Prompt: '{prompt}' (Size: {size})\n", source='response_api')
        elif chunk_type == 'response.mcp_list_tools.started':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n🔧 [MCP] Listing available tools...', source='response_api')
        elif chunk_type == 'response.mcp_list_tools.completed':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n✅ [MCP] Tool listing completed', source='response_api')
        elif chunk_type == 'response.mcp_list_tools.failed':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n❌ [MCP] Tool listing failed', source='response_api')
        elif chunk_type == 'response.mcp_call.started':
            tool_name = getattr(chunk, 'tool_name', 'unknown')
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content=f"\n🔧 [MCP] Calling tool '{tool_name}'...", source='response_api')
        elif chunk_type == 'response.mcp_call.in_progress':
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content='\n⏳ [MCP] Tool execution in progress...', source='response_api')
        elif chunk_type == 'response.mcp_call.completed':
            tool_name = getattr(chunk, 'tool_name', 'unknown')
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content=f"\n✅ [MCP] Tool '{tool_name}' completed", source='response_api')
        elif chunk_type == 'response.mcp_call.failed':
            tool_name = getattr(chunk, 'tool_name', 'unknown')
            error_msg = getattr(chunk, 'error', 'unknown error')
            return TextStreamChunk(type=ChunkType.MCP_STATUS, content=f"\n❌ [MCP] Tool '{tool_name}' failed: {error_msg}", source='response_api')
        elif chunk.type == 'response.completed':
            if hasattr(chunk, 'response'):
                response_dict = self._convert_to_dict(chunk.response)
                if isinstance(response_dict, dict) and 'output' in response_dict:
                    for item in response_dict['output']:
                        if item.get('type') == 'code_interpreter_call':
                            status = item.get('status', 'unknown')
                            code = item.get('code', '')
                            outputs = item.get('outputs')
                            content = f'\n🔧 Code Interpreter [{status.title()}]'
                            if code:
                                content += f': {code}'
                            if outputs:
                                content += f' → {outputs}'
                            log_stream_chunk('backend.response', 'code_interpreter_result', content, agent_id)
                            return TextStreamChunk(type=ChunkType.CONTENT, content=content, source='response_api')
                        elif item.get('type') == 'web_search_call':
                            status = item.get('status', 'unknown')
                            query = item.get('action', {}).get('query', '')
                            results = item.get('results')
                            if query:
                                content = f'\n🔧 Web Search [{status.title()}]: {query}'
                                if results:
                                    content += f' → Found {len(results)} results'
                                log_stream_chunk('backend.response', 'web_search_result', content, agent_id)
                                return TextStreamChunk(type=ChunkType.CONTENT, content=content, source='response_api')
                        elif item.get('type') == 'image_generation_call':
                            status = item.get('status', 'unknown')
                            action = item.get('action', {})
                            prompt = action.get('prompt', '')
                            size = action.get('size', '1024x1024')
                            if prompt:
                                content = f'\n🔧 Image Generation [{status.title()}]: {prompt} (Size: {size})'
                                log_stream_chunk('backend.response', 'image_generation_result', content, agent_id)
                                return TextStreamChunk(type=ChunkType.CONTENT, content=content, source='response_api')
                log_stream_chunk('backend.response', 'complete_response', 'Response completed', agent_id)
                return TextStreamChunk(type=ChunkType.COMPLETE_RESPONSE, response=response_dict, source='response_api')
        return StreamChunk(type='content', content='')

    def create_tool_result_message(self, tool_call: Dict[str, Any], result_content: str) -> Dict[str, Any]:
        """Create tool result message for OpenAI Responses API format."""
        tool_call_id = self.extract_tool_call_id(tool_call)
        return {'type': 'function_call_output', 'call_id': tool_call_id, 'output': result_content}

    def extract_tool_result_content(self, tool_result_message: Dict[str, Any]) -> str:
        """Extract content from OpenAI Responses API tool result message."""
        return tool_result_message.get('output', '')

    def _create_client(self, **kwargs) -> AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=self.api_key)

    def _convert_to_dict(self, obj) -> Dict[str, Any]:
        """Convert any object to dictionary with multiple fallback methods."""
        try:
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            else:
                return dict(obj)
        except Exception:
            return {key: getattr(obj, key, None) for key in dir(obj) if not key.startswith('_') and (not callable(getattr(obj, key, None)))}

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return 'OpenAI'

    def get_filesystem_support(self) -> FilesystemSupport:
        """OpenAI supports filesystem through MCP servers."""
        return FilesystemSupport.MCP

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by OpenAI."""
        return ['web_search', 'code_interpreter']

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.api_key = api_key or os.getenv('OPENAI_API_KEY')
    self.formatter = ResponseFormatter()
    self.api_params_handler = ResponseAPIParamsHandler(self)
    self._pending_image_saves = []
    self._vector_store_ids: List[str] = []
    self._uploaded_file_ids: List[str] = []

class GeminiBackend(LLMBackend):
    """Google Gemini backend using structured output for coordination and MCP tool integration."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.search_count = 0
        self.code_execution_count = 0
        self.mcp_servers = self.config.get('mcp_servers', [])
        self.allowed_tools = kwargs.pop('allowed_tools', None)
        self.exclude_tools = kwargs.pop('exclude_tools', None)
        self._mcp_client: Optional[MCPClient] = None
        self._mcp_initialized = False
        self._mcp_tool_calls_count = 0
        self._mcp_tool_failures = 0
        self._mcp_tool_successes = 0
        self.mcp_extractor = MCPResponseExtractor()
        self._max_mcp_message_history = kwargs.pop('max_mcp_message_history', 200)
        self._mcp_connection_retries = 0
        self._circuit_breakers_enabled = kwargs.pop('circuit_breaker_enabled', True)
        self._mcp_tools_circuit_breaker = None
        self.agent_id = kwargs.get('agent_id', None)
        if self._circuit_breakers_enabled:
            if MCPCircuitBreakerManager is None:
                raise RuntimeError('Circuit breakers enabled but MCPCircuitBreakerManager is not available')
            try:
                from ..mcp_tools.circuit_breaker import MCPCircuitBreaker
                if MCPConfigHelper is not None:
                    mcp_tools_config = MCPConfigHelper.build_circuit_breaker_config('mcp_tools', backend_name='gemini')
                else:
                    mcp_tools_config = None
                if mcp_tools_config:
                    self._mcp_tools_circuit_breaker = MCPCircuitBreaker(mcp_tools_config, backend_name='gemini', agent_id=self.agent_id)
                    log_backend_activity('gemini', 'Circuit breaker initialized for MCP tools', {'enabled': True}, agent_id=self.agent_id)
                else:
                    log_backend_activity('gemini', 'Circuit breaker config unavailable', {'fallback': 'disabled'}, agent_id=self.agent_id)
                    self._circuit_breakers_enabled = False
            except ImportError:
                log_backend_activity('gemini', 'Circuit breaker import failed', {'fallback': 'disabled'}, agent_id=self.agent_id)
                self._circuit_breakers_enabled = False

    def _setup_permission_hooks(self):
        """Override base class - Gemini uses session-based permissions, not function hooks."""
        logger.debug('[Gemini] Using session-based permissions, skipping function hook setup')

    async def _setup_mcp_with_status_stream(self, agent_id: Optional[str]=None) -> AsyncGenerator[StreamChunk, None]:
        """Initialize MCP client with status streaming."""
        status_queue: asyncio.Queue[StreamChunk] = asyncio.Queue()

        async def status_callback(status: str, details: Dict[str, Any]) -> None:
            """Callback to queue status updates as StreamChunks."""
            chunk = StreamChunk(type='mcp_status', status=status, content=details.get('message', ''), source='mcp_tools')
            await status_queue.put(chunk)
        setup_task = asyncio.create_task(self._setup_mcp_tools_internal(agent_id, status_callback))
        while not setup_task.done():
            try:
                chunk = await asyncio.wait_for(status_queue.get(), timeout=0.1)
                yield chunk
            except asyncio.TimeoutError:
                continue
        try:
            await setup_task
        except Exception as e:
            yield StreamChunk(type='mcp_status', status='error', content=f'MCP setup failed: {e}', source='mcp_tools')

    async def _setup_mcp_tools(self, agent_id: Optional[str]=None) -> None:
        """Initialize MCP client (sessions only) - backward compatibility."""
        if not self.mcp_servers or self._mcp_initialized:
            return
        async for _ in self._setup_mcp_with_status_stream(agent_id):
            pass

    async def _setup_mcp_tools_internal(self, agent_id: Optional[str]=None, status_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]]=None) -> None:
        """Internal MCP setup logic."""
        if not self.mcp_servers or self._mcp_initialized:
            return
        if MCPClient is None:
            reason = 'MCP import failed - MCPClient not available'
            log_backend_activity('gemini', 'MCP import failed', {'reason': reason, 'fallback': 'workflow_tools'}, agent_id=agent_id)
            if status_callback:
                await status_callback('error', {'message': 'MCP import failed - falling back to workflow tools'})
            self.mcp_servers = []
            return
        try:
            validated_config = {'mcp_servers': self.mcp_servers, 'allowed_tools': self.allowed_tools, 'exclude_tools': self.exclude_tools}
            if MCPConfigValidator is not None:
                try:
                    backend_config = {'mcp_servers': self.mcp_servers, 'allowed_tools': self.allowed_tools, 'exclude_tools': self.exclude_tools}
                    validator = MCPConfigValidator()
                    validated_config = validator.validate_backend_mcp_config(backend_config)
                    self.mcp_servers = validated_config.get('mcp_servers', self.mcp_servers)
                    log_backend_activity('gemini', 'MCP configuration validated', {'server_count': len(self.mcp_servers)}, agent_id=agent_id)
                    if status_callback:
                        await status_callback('info', {'message': f'MCP configuration validated: {len(self.mcp_servers)} servers'})
                    if True:
                        server_names = [server.get('name', 'unnamed') for server in self.mcp_servers]
                        log_backend_activity('gemini', 'MCP servers validated', {'servers': server_names}, agent_id=agent_id)
                except MCPConfigurationError as e:
                    log_backend_activity('gemini', 'MCP configuration validation failed', {'error': e.original_message}, agent_id=agent_id)
                    if status_callback:
                        await status_callback('error', {'message': f'Invalid MCP configuration: {e.original_message}'})
                    self._mcp_client = None
                    raise RuntimeError(f'Invalid MCP configuration: {e.original_message}') from e
                except MCPValidationError as e:
                    log_backend_activity('gemini', 'MCP validation failed', {'error': e.original_message}, agent_id=agent_id)
                    if status_callback:
                        await status_callback('error', {'message': f'MCP validation error: {e.original_message}'})
                    self._mcp_client = None
                    raise RuntimeError(f'MCP validation error: {e.original_message}') from e
                except Exception as e:
                    if isinstance(e, (ImportError, AttributeError)):
                        log_backend_activity('gemini', 'MCP validation unavailable', {'reason': str(e)}, agent_id=agent_id)
                    else:
                        log_backend_activity('gemini', 'MCP validation error', {'error': str(e)}, agent_id=agent_id)
                        self._mcp_client = None
                        raise RuntimeError(f'MCP configuration validation failed: {e}') from e
            else:
                log_backend_activity('gemini', 'MCP validation skipped', {'reason': 'validator_unavailable'}, agent_id=agent_id)
            normalized_servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
            log_backend_activity('gemini', 'Setting up MCP sessions', {'server_count': len(normalized_servers)}, agent_id=agent_id)
            if status_callback:
                await status_callback('info', {'message': f'Setting up MCP sessions for {len(normalized_servers)} servers'})
            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                filtered_servers = MCPCircuitBreakerManager.apply_circuit_breaker_filtering(normalized_servers, self._mcp_tools_circuit_breaker, backend_name='gemini', agent_id=agent_id)
            else:
                filtered_servers = normalized_servers
            if not filtered_servers:
                log_backend_activity('gemini', 'All MCP servers blocked by circuit breaker', {}, agent_id=agent_id)
                if status_callback:
                    await status_callback('warning', {'message': 'All MCP servers blocked by circuit breaker'})
                return
            if len(filtered_servers) < len(normalized_servers):
                log_backend_activity('gemini', 'Circuit breaker filtered servers', {'filtered_count': len(normalized_servers) - len(filtered_servers)}, agent_id=agent_id)
                if status_callback:
                    await status_callback('warning', {'message': f'Circuit breaker filtered {len(normalized_servers) - len(filtered_servers)} servers'})
            allowed_tools = validated_config.get('allowed_tools')
            exclude_tools = validated_config.get('exclude_tools')
            if allowed_tools:
                log_backend_activity('gemini', 'MCP tool filtering configured', {'allowed_tools': allowed_tools}, agent_id=agent_id)
            if exclude_tools:
                log_backend_activity('gemini', 'MCP tool filtering configured', {'exclude_tools': exclude_tools}, agent_id=agent_id)
            self._mcp_client = MCPClient(filtered_servers, timeout_seconds=30, allowed_tools=allowed_tools, exclude_tools=exclude_tools, status_callback=status_callback, hooks=self.filesystem_manager.get_pre_tool_hooks() if self.filesystem_manager else {})
            await self._mcp_client.connect()
            try:
                connected_server_names = self._mcp_client.get_server_names()
            except Exception:
                connected_server_names = []
            if not connected_server_names:
                if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                    await MCPCircuitBreakerManager.record_event(filtered_servers, self._mcp_tools_circuit_breaker, 'failure', error_message='No servers connected', backend_name='gemini', agent_id=agent_id)
                log_backend_activity('gemini', 'MCP connection failed: no servers connected', {}, agent_id=agent_id)
                if status_callback:
                    await status_callback('error', {'message': 'MCP connection failed: no servers connected'})
                self._mcp_client = None
                return
            connected_server_configs = [server for server in filtered_servers if server.get('name') in connected_server_names]
            if connected_server_configs:
                if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                    await MCPCircuitBreakerManager.record_event(connected_server_configs, self._mcp_tools_circuit_breaker, 'success', backend_name='gemini', agent_id=agent_id)
            self._mcp_initialized = True
            log_backend_activity('gemini', 'MCP sessions initialized successfully', {}, agent_id=agent_id)
            if status_callback:
                await status_callback('success', {'message': f'MCP sessions initialized successfully with {len(connected_server_names)} servers'})
        except Exception as e:
            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
                await MCPCircuitBreakerManager.record_event(servers, self._mcp_tools_circuit_breaker, 'failure', error_message=str(e), backend_name='gemini', agent_id=agent_id)
            if isinstance(e, RuntimeError) and 'MCP configuration' in str(e):
                raise
            elif isinstance(e, MCPConnectionError):
                log_backend_activity('gemini', 'MCP connection failed during setup', {'error': str(e)}, agent_id=agent_id)
                if status_callback:
                    await status_callback('error', {'message': f'Failed to establish MCP connections: {e}'})
                self._mcp_client = None
                raise RuntimeError(f'Failed to establish MCP connections: {e}') from e
            elif isinstance(e, MCPTimeoutError):
                log_backend_activity('gemini', 'MCP connection timeout during setup', {'error': str(e)}, agent_id=agent_id)
                if status_callback:
                    await status_callback('error', {'message': f'MCP connection timeout: {e}'})
                self._mcp_client = None
                raise RuntimeError(f'MCP connection timeout: {e}') from e
            elif isinstance(e, MCPServerError):
                log_backend_activity('gemini', 'MCP server error during setup', {'error': str(e)}, agent_id=agent_id)
                if status_callback:
                    await status_callback('error', {'message': f'MCP server error: {e}'})
                self._mcp_client = None
                raise RuntimeError(f'MCP server error: {e}') from e
            elif isinstance(e, MCPError):
                log_backend_activity('gemini', 'MCP error during setup', {'error': str(e)}, agent_id=agent_id)
                if status_callback:
                    await status_callback('error', {'message': f'MCP error during setup: {e}'})
                self._mcp_client = None
                return
            else:
                log_backend_activity('gemini', 'MCP session setup failed', {'error': str(e)}, agent_id=agent_id)
                if status_callback:
                    await status_callback('error', {'message': f'MCP session setup failed: {e}'})
                self._mcp_client = None

    def detect_coordination_tools(self, tools: List[Dict[str, Any]]) -> bool:
        """Detect if tools contain vote/new_answer coordination tools."""
        if not tools:
            return False
        tool_names = set()
        for tool in tools:
            if tool.get('type') == 'function':
                if 'function' in tool:
                    tool_names.add(tool['function'].get('name', ''))
                elif 'name' in tool:
                    tool_names.add(tool.get('name', ''))
        return 'vote' in tool_names and 'new_answer' in tool_names

    def build_structured_output_prompt(self, base_content: str, valid_agent_ids: Optional[List[str]]=None) -> str:
        """Build prompt that encourages structured output for coordination."""
        agent_list = ''
        if valid_agent_ids:
            agent_list = f'Valid agents: {', '.join(valid_agent_ids)}'
        return f"""{base_content}\n\nIMPORTANT: You must respond with a structured JSON decision at the end of your response.\n\nIf you want to VOTE for an existing agent's answer:\n{{\n  "action_type": "vote",\n  "vote_data": {{\n    "action": "vote",\n    "agent_id": "agent1",  // Choose from: {agent_list or 'agent1, agent2, agent3, etc.'}\n    "reason": "Brief reason for your vote"\n  }}\n}}\n\nIf you want to provide a NEW ANSWER:\n{{\n  "action_type": "new_answer",\n  "answer_data": {{\n    "action": "new_answer",\n    "content": "Your complete improved answer here"\n  }}\n}}\n\nMake your decision and include the JSON at the very end of your response."""

    def extract_structured_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract structured JSON response from model output."""
        try:
            markdown_json_pattern = '```json\\s*(\\{.*?\\})\\s*```'
            markdown_matches = re.findall(markdown_json_pattern, response_text, re.DOTALL)
            for match in reversed(markdown_matches):
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, dict) and 'action_type' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            json_pattern = '\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)
            for match in reversed(json_matches):
                try:
                    cleaned_match = match.strip()
                    parsed = json.loads(cleaned_match)
                    if isinstance(parsed, dict) and 'action_type' in parsed:
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
                            if isinstance(parsed, dict) and 'action_type' in parsed:
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
                    if isinstance(parsed, dict) and 'action_type' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
            return None
        except Exception:
            return None

    def convert_structured_to_tool_calls(self, structured_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert structured response to tool call format."""
        action_type = structured_response.get('action_type')
        if action_type == 'vote':
            vote_data = structured_response.get('vote_data', {})
            return [{'id': f'vote_{abs(hash(str(vote_data))) % 10000 + 1}', 'type': 'function', 'function': {'name': 'vote', 'arguments': {'agent_id': vote_data.get('agent_id', ''), 'reason': vote_data.get('reason', '')}}}]
        elif action_type == 'new_answer':
            answer_data = structured_response.get('answer_data', {})
            return [{'id': f'new_answer_{abs(hash(str(answer_data))) % 10000 + 1}', 'type': 'function', 'function': {'name': 'new_answer', 'arguments': {'content': answer_data.get('content', '')}}}]
        return []

    async def _handle_mcp_retry_error(self, error: Exception, retry_count: int, max_retries: int) -> tuple[bool, AsyncGenerator[StreamChunk, None]]:
        """Handle MCP retry errors with specific messaging and fallback logic.

        Returns:
            tuple: (should_continue_retrying, error_chunks_generator)
        """
        log_type, user_message, _ = MCPErrorHandler.get_error_details(error, None, log=False)
        log_backend_activity('gemini', f'MCP {log_type} on retry', {'attempt': retry_count, 'error': str(error)}, agent_id=self.agent_id)
        if retry_count >= max_retries:

            async def error_chunks():
                yield StreamChunk(type='content', content=f'\n⚠️  {user_message} after {max_retries} attempts; falling back to workflow tools\n')
            return (False, error_chunks())

        async def empty_chunks():
            if False:
                yield
        return (True, empty_chunks())

    async def _handle_mcp_error_and_fallback(self, error: Exception) -> AsyncGenerator[StreamChunk, None]:
        """Handle MCP errors with specific messaging"""
        self._mcp_tool_failures += 1
        log_type, user_message, _ = MCPErrorHandler.get_error_details(error, None, log=False)
        log_backend_activity('gemini', 'MCP tool call failed', {'call_number': self._mcp_tool_calls_count, 'error_type': log_type, 'error': str(error)}, agent_id=self.agent_id)
        yield StreamChunk(type='content', content=f'\n⚠️  {user_message} ({error}); continuing without MCP tools\n')

    async def _execute_mcp_function_with_retry(self, function_name: str, args: Dict[str, Any], agent_id: Optional[str]=None) -> Any:
        """Execute MCP function with exponential backoff retry logic."""
        if MCPExecutionManager is None:
            raise RuntimeError('MCPExecutionManager is not available - MCP backend utilities are missing')

        async def stats_callback(action: str) -> int:
            if action == 'increment_calls':
                self._mcp_tool_calls_count += 1
                return self._mcp_tool_calls_count
            elif action == 'increment_failures':
                self._mcp_tool_failures += 1
                return self._mcp_tool_failures
            return 0

        async def circuit_breaker_callback(event: str, error_msg: str) -> None:
            if event == 'failure':
                if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                    servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
                    await MCPCircuitBreakerManager.record_event(servers, self._mcp_tools_circuit_breaker, 'failure', error_message=error_msg, backend_name='gemini', agent_id=agent_id)
            else:
                connected_names: List[str] = []
                try:
                    if self._mcp_client:
                        connected_names = self._mcp_client.get_server_names()
                except Exception:
                    connected_names = []
                if connected_names:
                    servers_to_record = [{'name': name} for name in connected_names]
                    if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                        await MCPCircuitBreakerManager.record_event(servers_to_record, self._mcp_tools_circuit_breaker, 'success', backend_name='gemini', agent_id=agent_id)
        return await MCPExecutionManager.execute_function_with_retry(function_name=function_name, args=args, functions=self.functions, max_retries=3, stats_callback=stats_callback, circuit_breaker_callback=circuit_breaker_callback, logger_instance=logger)

    async def stream_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using Gemini API with structured output for coordination and MCP tool support."""
        agent_id = self.agent_id or kwargs.get('agent_id', None)
        client = None
        stream = None
        log_backend_activity('gemini', 'Starting stream_with_tools', {'num_messages': len(messages), 'num_tools': len(tools) if tools else 0}, agent_id=agent_id)
        if self.mcp_servers and MCPMessageManager is not None and hasattr(self, '_max_mcp_message_history') and (self._max_mcp_message_history > 0):
            original_count = len(messages)
            messages = MCPMessageManager.trim_message_history(messages, self._max_mcp_message_history)
            if len(messages) < original_count:
                log_backend_activity('gemini', 'Trimmed MCP message history', {'original': original_count, 'trimmed': len(messages), 'limit': self._max_mcp_message_history}, agent_id=agent_id)
        try:
            from google import genai
            if not self._mcp_initialized and self.mcp_servers:
                async for chunk in self._setup_mcp_with_status_stream(agent_id):
                    yield chunk
            elif not self._mcp_initialized:
                await self._setup_mcp_tools(agent_id)
            all_params = {**self.config, **kwargs}
            enable_web_search = all_params.get('enable_web_search', False)
            enable_code_execution = all_params.get('enable_code_execution', False)
            using_sdk_mcp = bool(self.mcp_servers)
            is_coordination = self.detect_coordination_tools(tools)
            valid_agent_ids = None
            if is_coordination:
                for tool in tools:
                    if tool.get('type') == 'function':
                        func_def = tool.get('function', {})
                        if func_def.get('name') == 'vote':
                            agent_id_param = func_def.get('parameters', {}).get('properties', {}).get('agent_id', {})
                            if 'enum' in agent_id_param:
                                valid_agent_ids = agent_id_param['enum']
                            break
            conversation_content = ''
            system_message = ''
            for msg in messages:
                role = msg.get('role')
                if role == 'system':
                    system_message = msg.get('content', '')
                elif role == 'user':
                    conversation_content += f'User: {msg.get('content', '')}\n'
                elif role == 'assistant':
                    conversation_content += f'Assistant: {msg.get('content', '')}\n'
                elif role == 'tool':
                    tool_output = msg.get('content', '')
                    conversation_content += f'Tool Result: {tool_output}\n'
            if is_coordination:
                conversation_content = self.build_structured_output_prompt(conversation_content, valid_agent_ids)
            full_content = ''
            if system_message:
                full_content += f'{system_message}\n\n'
            full_content += conversation_content
            client = genai.Client(api_key=self.api_key)
            builtin_tools = []
            if enable_web_search:
                try:
                    from google.genai import types
                    grounding_tool = types.Tool(google_search=types.GoogleSearch())
                    builtin_tools.append(grounding_tool)
                except ImportError:
                    yield StreamChunk(type='content', content='\n⚠️  Web search requires google.genai.types\n')
            if enable_code_execution:
                try:
                    from google.genai import types
                    code_tool = types.Tool(code_execution=types.ToolCodeExecution())
                    builtin_tools.append(code_tool)
                except ImportError:
                    yield StreamChunk(type='content', content='\n⚠️  Code execution requires google.genai.types\n')
            config = {}
            excluded_params = self.get_base_excluded_config_params() | {'enable_web_search', 'enable_code_execution', 'use_multi_mcp', 'mcp_sdk_auto', 'allowed_tools', 'exclude_tools'}
            for key, value in all_params.items():
                if key not in excluded_params and value is not None:
                    if key == 'max_tokens':
                        config['max_output_tokens'] = value
                    elif key == 'model':
                        model_name = value
                    else:
                        config[key] = value
            all_tools = []
            if using_sdk_mcp and self.mcp_servers:
                if not self._mcp_client or not getattr(self._mcp_client, 'is_connected', lambda: False)():
                    max_mcp_retries = 5
                    mcp_connected = False
                    for retry_count in range(1, max_mcp_retries + 1):
                        try:
                            self._mcp_connection_retries = retry_count
                            if retry_count > 1:
                                log_backend_activity('gemini', 'MCP connection retry', {'attempt': retry_count, 'max_retries': max_mcp_retries}, agent_id=agent_id)
                                yield StreamChunk(type='mcp_status', status='mcp_retry', content=f'Retrying MCP connection (attempt {retry_count}/{max_mcp_retries})', source='mcp_tools')
                                await asyncio.sleep(0.5 * retry_count)
                            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                                filtered_retry_servers = MCPCircuitBreakerManager.apply_circuit_breaker_filtering(self.mcp_servers, self._mcp_tools_circuit_breaker, backend_name='gemini', agent_id=agent_id)
                            else:
                                filtered_retry_servers = self.mcp_servers
                            if not filtered_retry_servers:
                                log_backend_activity('gemini', 'All MCP servers blocked during retry', {}, agent_id=agent_id)
                                yield StreamChunk(type='mcp_status', status='mcp_blocked', content='All MCP servers blocked by circuit breaker', source='mcp_tools')
                                using_sdk_mcp = False
                                break
                            backend_config = {'mcp_servers': self.mcp_servers}
                            if MCPConfigValidator is not None:
                                try:
                                    validator = MCPConfigValidator()
                                    validated_config_retry = validator.validate_backend_mcp_config(backend_config)
                                    allowed_tools_retry = validated_config_retry.get('allowed_tools')
                                    exclude_tools_retry = validated_config_retry.get('exclude_tools')
                                except Exception:
                                    allowed_tools_retry = None
                                    exclude_tools_retry = None
                            else:
                                allowed_tools_retry = None
                                exclude_tools_retry = None
                            self._mcp_client = await MCPClient.create_and_connect(filtered_retry_servers, timeout_seconds=30, allowed_tools=allowed_tools_retry, exclude_tools=exclude_tools_retry)
                            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                                await MCPCircuitBreakerManager.record_event(filtered_retry_servers, self._mcp_tools_circuit_breaker, 'success', backend_name='gemini', agent_id=agent_id)
                            mcp_connected = True
                            log_backend_activity('gemini', 'MCP connection successful on retry', {'attempt': retry_count}, agent_id=agent_id)
                            yield StreamChunk(type='mcp_status', status='mcp_connected', content=f'MCP connection successful on attempt {retry_count}', source='mcp_tools')
                            break
                        except (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError, Exception) as e:
                            if self._circuit_breakers_enabled and self._mcp_tools_circuit_breaker:
                                servers = MCPSetupManager.normalize_mcp_servers(self.mcp_servers)
                                await MCPCircuitBreakerManager.record_event(servers, self._mcp_tools_circuit_breaker, 'failure', error_message=str(e), backend_name='gemini', agent_id=agent_id)
                            should_continue, error_chunks = await self._handle_mcp_retry_error(e, retry_count, max_mcp_retries)
                            if not should_continue:
                                async for chunk in error_chunks:
                                    yield chunk
                                using_sdk_mcp = False
                    if not mcp_connected:
                        using_sdk_mcp = False
                        self._mcp_client = None
            if not using_sdk_mcp:
                all_tools.extend(builtin_tools)
                if all_tools:
                    config['tools'] = all_tools
            if is_coordination:
                if not using_sdk_mcp and (not all_tools):
                    config['response_mime_type'] = 'application/json'
                    config['response_schema'] = CoordinationResponse.model_json_schema()
                else:
                    pass
            log_backend_agent_message(agent_id or 'default', 'SEND', {'content': full_content, 'builtin_tools': len(builtin_tools) if builtin_tools else 0}, backend_name='gemini')
            full_content_text = ''
            final_response = None
            if using_sdk_mcp and self.mcp_servers:
                try:
                    if not self._mcp_client:
                        raise RuntimeError('MCP client not initialized')
                    mcp_sessions = self._mcp_client.get_active_sessions()
                    if not mcp_sessions:
                        raise RuntimeError('No active MCP sessions available')
                    if self.filesystem_manager:
                        logger.info(f'[Gemini] Converting {len(mcp_sessions)} MCP sessions to permission sessions')
                        try:
                            from ..mcp_tools.hooks import convert_sessions_to_permission_sessions
                            mcp_sessions = convert_sessions_to_permission_sessions(mcp_sessions, self.filesystem_manager.path_permission_manager)
                        except Exception as e:
                            logger.error(f'[Gemini] Failed to convert sessions to permission sessions: {e}')
                    else:
                        logger.debug('[Gemini] No filesystem manager found, using standard sessions')
                    session_config = dict(config)
                    available_tools = []
                    if self._mcp_client:
                        available_tools = list(self._mcp_client.tools.keys())
                    if self.is_planning_mode_enabled():
                        logger.info('[Gemini] Planning mode enabled - blocking MCP tools during coordination')
                        log_backend_activity('gemini', 'MCP tools blocked in planning mode', {'blocked_tools': len(available_tools), 'session_count': len(mcp_sessions)}, agent_id=agent_id)
                    else:
                        logger.debug(f'[Gemini] Passing {len(mcp_sessions)} sessions to SDK: {[type(s).__name__ for s in mcp_sessions]}')
                        session_config['tools'] = mcp_sessions
                    self._mcp_tool_calls_count += 1
                    log_backend_activity('gemini', 'MCP tool call initiated', {'call_number': self._mcp_tool_calls_count, 'session_count': len(mcp_sessions), 'available_tools': available_tools[:], 'total_tools': len(available_tools)}, agent_id=agent_id)
                    log_tool_call(agent_id, 'mcp_session_tools', {'session_count': len(mcp_sessions), 'call_number': self._mcp_tool_calls_count, 'available_tools': available_tools}, backend_name='gemini')
                    tools_info = f' ({len(available_tools)} tools available)' if available_tools else ''
                    yield StreamChunk(type='mcp_status', status='mcp_tools_initiated', content=f'MCP tool call initiated (call #{self._mcp_tool_calls_count}){tools_info}: {', '.join(available_tools[:5])}{('...' if len(available_tools) > 5 else '')}', source='mcp_tools')
                    stream = await client.aio.models.generate_content_stream(model=model_name, contents=full_content, config=session_config)
                    mcp_tracker = MCPCallTracker()
                    mcp_response_tracker = MCPResponseTracker()
                    mcp_tools_used = []
                    async for chunk in stream:
                        if hasattr(chunk, 'automatic_function_calling_history') and chunk.automatic_function_calling_history:
                            for history_item in chunk.automatic_function_calling_history:
                                if hasattr(history_item, 'parts') and history_item.parts is not None:
                                    for part in history_item.parts:
                                        if hasattr(part, 'function_call') and part.function_call:
                                            call_data = self.mcp_extractor.extract_function_call(part.function_call)
                                            if call_data:
                                                tool_name = call_data['name']
                                                tool_args = call_data['arguments']
                                                if mcp_tracker.is_new_call(tool_name, tool_args):
                                                    call_record = mcp_tracker.add_call(tool_name, tool_args)
                                                    mcp_tools_used.append({'name': tool_name, 'arguments': tool_args, 'timestamp': call_record['timestamp']})
                                                    timestamp_str = time.strftime('%H:%M:%S', time.localtime(call_record['timestamp']))
                                                    yield StreamChunk(type='mcp_status', status='mcp_tool_called', content=f'🔧 MCP Tool Called: {tool_name} at {timestamp_str} with args: {json.dumps(tool_args, indent=2)}', source='mcp_tools')
                                                    log_tool_call(agent_id, tool_name, tool_args, backend_name='gemini')
                                        elif hasattr(part, 'function_response') and part.function_response:
                                            response_data = self.mcp_extractor.extract_function_response(part.function_response)
                                            if response_data:
                                                tool_name = response_data['name']
                                                tool_response = response_data['response']
                                                if mcp_response_tracker.is_new_response(tool_name, tool_response):
                                                    response_record = mcp_response_tracker.add_response(tool_name, tool_response)
                                                    response_text = None
                                                    if isinstance(tool_response, dict) and 'result' in tool_response:
                                                        result = tool_response['result']
                                                        if hasattr(result, 'content') and result.content:
                                                            first_content = result.content[0]
                                                            if hasattr(first_content, 'text'):
                                                                response_text = first_content.text
                                                    if response_text is None:
                                                        response_text = str(tool_response)
                                                    timestamp_str = time.strftime('%H:%M:%S', time.localtime(response_record['timestamp']))
                                                    yield StreamChunk(type='mcp_status', status='mcp_tool_response', content=f'✅ MCP Tool Response from {tool_name} at {timestamp_str}: {response_text}', source='mcp_tools')
                                                    log_backend_activity('gemini', 'MCP tool response received', {'tool_name': tool_name, 'response_preview': str(tool_response)[:]}, agent_id=agent_id)
                            if not hasattr(self, '_mcp_stream_started'):
                                self._mcp_tool_successes += 1
                                self._mcp_stream_started = True
                                log_backend_activity('gemini', 'MCP tool call succeeded', {'call_number': self._mcp_tool_calls_count}, agent_id=agent_id)
                                log_tool_call(agent_id, 'mcp_session_tools', {'session_count': len(mcp_sessions), 'call_number': self._mcp_tool_calls_count}, result='success', backend_name='gemini')
                                yield StreamChunk(type='mcp_status', status='mcp_tools_success', content=f'MCP tool call succeeded (call #{self._mcp_tool_calls_count})', source='mcp_tools')
                        if hasattr(chunk, 'text') and chunk.text:
                            chunk_text = chunk.text
                            full_content_text += chunk_text
                            log_backend_agent_message(agent_id, 'RECV', {'content': chunk_text}, backend_name='gemini')
                            log_stream_chunk('backend.gemini', 'content', chunk_text, agent_id)
                            yield StreamChunk(type='content', content=chunk_text)
                    if hasattr(self, '_mcp_stream_started'):
                        delattr(self, '_mcp_stream_started')
                    tools_summary = mcp_tracker.get_summary()
                    if not tools_summary or tools_summary == 'No MCP tools called':
                        tools_summary = 'MCP session completed (no tools explicitly called)'
                    else:
                        tools_summary = f'MCP session complete - {tools_summary}'
                    log_stream_chunk('backend.gemini', 'mcp_indicator', tools_summary, agent_id)
                    yield StreamChunk(type='mcp_status', status='mcp_session_complete', content=f'MCP session complete - {tools_summary}', source='mcp_tools')
                except (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError, Exception) as e:
                    log_stream_chunk('backend.gemini', 'mcp_error', str(e), agent_id)
                    async for chunk in self._handle_mcp_error_and_fallback(e):
                        yield chunk
                    manual_config = dict(config)
                    if all_tools:
                        manual_config['tools'] = all_tools
                    stream = await client.aio.models.generate_content_stream(model=model_name, contents=full_content, config=manual_config)
                    async for chunk in stream:
                        if hasattr(chunk, 'text') and chunk.text:
                            chunk_text = chunk.text
                            full_content_text += chunk_text
                            log_stream_chunk('backend.gemini', 'fallback_content', chunk_text, agent_id)
                            yield StreamChunk(type='content', content=chunk_text)
            else:
                stream = await client.aio.models.generate_content_stream(model=model_name, contents=full_content, config=config)
                async for chunk in stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                        full_content_text += chunk_text
                        log_stream_chunk('backend.gemini', 'content', chunk_text, agent_id)
                        log_backend_agent_message(agent_id, 'RECV', {'content': chunk_text}, backend_name='gemini')
                        yield StreamChunk(type='content', content=chunk_text)
            content = full_content_text
            tool_calls_detected: List[Dict[str, Any]] = []
            if is_coordination and content.strip() and (not tool_calls_detected):
                structured_response = None
                try:
                    structured_response = json.loads(content.strip())
                except json.JSONDecodeError:
                    structured_response = self.extract_structured_response(content)
                if structured_response and isinstance(structured_response, dict) and ('action_type' in structured_response):
                    tool_calls = self.convert_structured_to_tool_calls(structured_response)
                    if tool_calls:
                        tool_calls_detected = tool_calls
                        log_stream_chunk('backend.gemini', 'tool_calls', tool_calls, agent_id)
                        try:
                            for tool_call in tool_calls:
                                log_tool_call(agent_id, tool_call.get('function', {}).get('name', 'unknown_coordination_tool'), tool_call.get('function', {}).get('arguments', {}), result='coordination_tool_called', backend_name='gemini')
                        except Exception:
                            pass
            if builtin_tools and final_response and hasattr(final_response, 'candidates') and final_response.candidates:
                candidate = final_response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    search_actually_used = False
                    search_queries = []
                    if hasattr(candidate.grounding_metadata, 'web_search_queries') and candidate.grounding_metadata.web_search_queries:
                        try:
                            for query in candidate.grounding_metadata.web_search_queries:
                                if query and query.strip():
                                    search_queries.append(query.strip())
                                    search_actually_used = True
                        except (TypeError, AttributeError):
                            pass
                    if hasattr(candidate.grounding_metadata, 'grounding_chunks') and candidate.grounding_metadata.grounding_chunks:
                        try:
                            if len(candidate.grounding_metadata.grounding_chunks) > 0:
                                search_actually_used = True
                        except (TypeError, AttributeError):
                            pass
                    if search_actually_used:
                        log_stream_chunk('backend.gemini', 'web_search_result', {'queries': search_queries, 'results_integrated': True}, agent_id)
                        log_tool_call(agent_id, 'google_search_retrieval', {'queries': search_queries, 'chunks_found': len(candidate.grounding_metadata.grounding_chunks) if hasattr(candidate.grounding_metadata, 'grounding_chunks') else 0}, result='search_completed', backend_name='gemini')
                        yield StreamChunk(type='content', content='🔍 [Builtin Tool: Web Search] Results integrated\n')
                        for query in search_queries:
                            log_stream_chunk('backend.gemini', 'web_search_result', {'queries': search_queries, 'results_integrated': True}, agent_id)
                            yield StreamChunk(type='content', content=f"🔍 [Search Query] '{query}'\n")
                        self.search_count += 1
                if enable_code_execution and hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    code_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'executable_code') and part.executable_code:
                            code_content = getattr(part.executable_code, 'code', str(part.executable_code))
                            code_parts.append(f'Code: {code_content}')
                        elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                            result_content = getattr(part.code_execution_result, 'output', str(part.code_execution_result))
                            code_parts.append(f'Result: {result_content}')
                    if code_parts:
                        log_stream_chunk('backend.gemini', 'code_execution', 'Code executed', agent_id)
                        try:
                            log_tool_call(agent_id, 'code_execution', {'code_parts_count': len(code_parts)}, result='code_executed', backend_name='gemini')
                        except Exception:
                            pass
                        yield StreamChunk(type='content', content='💻 [Builtin Tool: Code Execution] Code executed\n')
                        for part in code_parts:
                            if part.startswith('Code: '):
                                code_content = part[6:]
                                log_stream_chunk('backend.gemini', 'code_execution_result', {'code_parts': len(code_parts), 'execution_successful': True, 'snippet': code_content}, agent_id)
                                yield StreamChunk(type='content', content=f'💻 [Code Executed]\n```python\n{code_content}\n```\n')
                            elif part.startswith('Result: '):
                                result_content = part[8:]
                                log_stream_chunk('backend.gemini', 'code_execution_result', {'code_parts': len(code_parts), 'execution_successful': True, 'result': result_content}, agent_id)
                                yield StreamChunk(type='content', content=f'📊 [Result] {result_content}\n')
                        self.code_execution_count += 1
            if tool_calls_detected:
                log_stream_chunk('backend.gemini', 'tool_calls_yielded', {'tool_count': len(tool_calls_detected), 'tool_names': [tc.get('function', {}).get('name') for tc in tool_calls_detected]}, agent_id)
                yield StreamChunk(type='tool_calls', tool_calls=tool_calls_detected)
            complete_message = {'role': 'assistant', 'content': content.strip()}
            if tool_calls_detected:
                complete_message['tool_calls'] = tool_calls_detected
            log_stream_chunk('backend.gemini', 'complete_message', {'content_length': len(content.strip()), 'has_tool_calls': bool(tool_calls_detected)}, agent_id)
            yield StreamChunk(type='complete_message', complete_message=complete_message)
            log_stream_chunk('backend.gemini', 'done', None, agent_id)
            yield StreamChunk(type='done')
        except Exception as e:
            error_msg = f'Gemini API error: {e}'
            log_stream_chunk('backend.gemini', 'stream_error', {'error_type': type(e).__name__, 'error_message': str(e)}, agent_id)
            yield StreamChunk(type='error', error=error_msg)
        finally:
            await self._cleanup_resources(stream, client)
            try:
                await self.__aexit__(None, None, None)
            except Exception as e:
                log_backend_activity('gemini', 'MCP cleanup failed', {'error': str(e)}, agent_id=self.agent_id)

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return 'Gemini'

    def get_filesystem_support(self) -> FilesystemSupport:
        """Gemini supports filesystem through MCP servers."""
        return FilesystemSupport.MCP

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by Gemini."""
        return ['google_search_retrieval', 'code_execution']

    def get_mcp_results(self) -> Dict[str, Any]:
        """
        Get all captured MCP tool calls and responses.

        Returns:
            Dict containing:
            - calls: List of all MCP tool calls
            - responses: List of all MCP tool responses
            - pairs: List of matched call-response pairs
            - summary: Statistical summary of interactions
        """
        return {'calls': self.mcp_extractor.mcp_calls, 'responses': self.mcp_extractor.mcp_responses, 'pairs': self.mcp_extractor.call_response_pairs, 'summary': self.mcp_extractor.get_summary()}

    def get_mcp_paired_results(self) -> List[Dict[str, Any]]:
        """
        Get only the paired MCP tool calls and responses.

        Returns:
            List of dictionaries containing matched call-response pairs
        """
        return self.mcp_extractor.call_response_pairs

    def get_mcp_summary(self) -> Dict[str, Any]:
        """
        Get a summary of MCP tool interactions.

        Returns:
            Dictionary with statistics about MCP tool usage
        """
        return self.mcp_extractor.get_summary()

    def clear_mcp_results(self):
        """Clear all stored MCP interaction data."""
        self.mcp_extractor.clear()

    def reset_tool_usage(self):
        """Reset tool usage tracking."""
        self.search_count = 0
        self.code_execution_count = 0
        self._mcp_tool_calls_count = 0
        self._mcp_tool_failures = 0
        self._mcp_tool_successes = 0
        self._mcp_connection_retries = 0
        self.mcp_extractor.clear()
        super().reset_token_usage()

    async def cleanup_mcp(self):
        """Cleanup MCP connections."""
        if self._mcp_client:
            try:
                await self._mcp_client.disconnect()
                log_backend_activity('gemini', 'MCP client disconnected', {}, agent_id=self.agent_id)
            except (MCPConnectionError, MCPTimeoutError, MCPServerError, MCPError, Exception) as e:
                MCPErrorHandler.get_error_details(e, 'disconnect', log=True)
            finally:
                self._mcp_client = None
                self._mcp_initialized = False

    async def _cleanup_resources(self, stream, client):
        """Cleanup google-genai resources to avoid unclosed aiohttp sessions."""
        try:
            if stream is not None:
                close_fn = getattr(stream, 'aclose', None) or getattr(stream, 'close', None)
                if close_fn is not None:
                    maybe = close_fn()
                    if hasattr(maybe, '__await__'):
                        await maybe
        except Exception as e:
            log_backend_activity('gemini', 'Stream cleanup failed', {'error': str(e)}, agent_id=self.agent_id)
        try:
            if client is not None:
                base_client = getattr(client, '_api_client', None)
                if base_client is not None:
                    session = getattr(base_client, '_aiohttp_session', None)
                    if session is not None and hasattr(session, 'close'):
                        if not session.closed:
                            await session.close()
                            log_backend_activity('gemini', 'Closed google-genai aiohttp session', {}, agent_id=self.agent_id)
                        base_client._aiohttp_session = None
                        await asyncio.sleep(0)
        except Exception as e:
            log_backend_activity('gemini', 'Failed to close google-genai aiohttp session', {'error': str(e)}, agent_id=self.agent_id)
        try:
            if client is not None and hasattr(client, 'aio') and (client.aio is not None):
                aio_obj = client.aio
                for method_name in ('close', 'stop'):
                    method = getattr(aio_obj, method_name, None)
                    if method:
                        maybe = method()
                        if hasattr(maybe, '__await__'):
                            await maybe
                        break
        except Exception as e:
            log_backend_activity('gemini', 'Client AIO cleanup failed', {'error': str(e)}, agent_id=self.agent_id)
        try:
            if client is not None:
                for method_name in ('aclose', 'close'):
                    method = getattr(client, method_name, None)
                    if method:
                        maybe = method()
                        if hasattr(maybe, '__await__'):
                            await maybe
                        break
        except Exception as e:
            log_backend_activity('gemini', 'Client cleanup failed', {'error': str(e)}, agent_id=self.agent_id)

    async def __aenter__(self) -> 'GeminiBackend':
        """Async context manager entry."""
        try:
            await self._setup_mcp_tools(agent_id=self.agent_id)
        except Exception as e:
            log_backend_activity('gemini', 'MCP setup failed during context entry', {'error': str(e)}, agent_id=self.agent_id)
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        """Async context manager exit with automatic resource cleanup."""
        _ = (exc_type, exc_val, exc_tb)
        try:
            await self.cleanup_mcp()
        except Exception as e:
            log_backend_activity('gemini', 'Backend cleanup error', {'error': str(e)}, agent_id=self.agent_id)

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    self.search_count = 0
    self.code_execution_count = 0
    self.mcp_servers = self.config.get('mcp_servers', [])
    self.allowed_tools = kwargs.pop('allowed_tools', None)
    self.exclude_tools = kwargs.pop('exclude_tools', None)
    self._mcp_client: Optional[MCPClient] = None
    self._mcp_initialized = False
    self._mcp_tool_calls_count = 0
    self._mcp_tool_failures = 0
    self._mcp_tool_successes = 0
    self.mcp_extractor = MCPResponseExtractor()
    self._max_mcp_message_history = kwargs.pop('max_mcp_message_history', 200)
    self._mcp_connection_retries = 0
    self._circuit_breakers_enabled = kwargs.pop('circuit_breaker_enabled', True)
    self._mcp_tools_circuit_breaker = None
    self.agent_id = kwargs.get('agent_id', None)
    if self._circuit_breakers_enabled:
        if MCPCircuitBreakerManager is None:
            raise RuntimeError('Circuit breakers enabled but MCPCircuitBreakerManager is not available')
        try:
            from ..mcp_tools.circuit_breaker import MCPCircuitBreaker
            if MCPConfigHelper is not None:
                mcp_tools_config = MCPConfigHelper.build_circuit_breaker_config('mcp_tools', backend_name='gemini')
            else:
                mcp_tools_config = None
            if mcp_tools_config:
                self._mcp_tools_circuit_breaker = MCPCircuitBreaker(mcp_tools_config, backend_name='gemini', agent_id=self.agent_id)
                log_backend_activity('gemini', 'Circuit breaker initialized for MCP tools', {'enabled': True}, agent_id=self.agent_id)
            else:
                log_backend_activity('gemini', 'Circuit breaker config unavailable', {'fallback': 'disabled'}, agent_id=self.agent_id)
                self._circuit_breakers_enabled = False
        except ImportError:
            log_backend_activity('gemini', 'Circuit breaker import failed', {'fallback': 'disabled'}, agent_id=self.agent_id)
            self._circuit_breakers_enabled = False

def reset_tool_usage(self):
    """Reset tool usage tracking."""
    self.search_count = 0
    self.code_execution_count = 0
    self._mcp_tool_calls_count = 0
    self._mcp_tool_failures = 0
    self._mcp_tool_successes = 0
    self._mcp_connection_retries = 0
    self.mcp_extractor.clear()
    super().reset_token_usage()

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

class GrokBackend(ChatCompletionsBackend):
    """Grok backend using xAI's OpenAI-compatible API."""

    def __init__(self, api_key: Optional[str]=None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv('XAI_API_KEY')
        self.base_url = 'https://api.x.ai/v1'

    def _create_client(self, **kwargs) -> AsyncOpenAI:
        """Create OpenAI client configured for xAI's Grok API."""
        import openai
        return openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    def _build_base_api_params(self, messages: List[Dict[str, Any]], all_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build base API params for xAI's Grok API."""
        api_params = super()._build_base_api_params(messages, all_params)
        enable_web_search = all_params.get('enable_web_search', False)
        if enable_web_search:
            existing_extra = api_params.get('extra_body', {})
            if isinstance(existing_extra, dict) and 'search_parameters' in existing_extra:
                error_message = "Conflict: Cannot use both 'enable_web_search: true' and manual 'extra_body.search_parameters'. Use one or the other."
                log_stream_chunk('backend.grok', 'error', error_message, self.agent_id)
                raise ValueError(error_message)
            search_params = {'mode': 'auto', 'return_citations': True}
            merged_extra = existing_extra.copy()
            merged_extra['search_parameters'] = search_params
            api_params['extra_body'] = merged_extra
        return api_params

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return 'Grok'

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by Grok."""
        return ['web_search']

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.api_key = api_key or os.getenv('XAI_API_KEY')
    self.base_url = 'https://api.x.ai/v1'

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

def __init__(self, cli_command: str, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.cli_command = cli_command
    self.working_dir = kwargs.get('working_dir', Path.cwd())
    self.timeout = kwargs.get('timeout', 300)

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

def __init__(self, api_key: Optional[str]=None, **kwargs):
    super().__init__(api_key, **kwargs)
    self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    self.search_count = 0
    self.code_session_hours = 0.0
    self.formatter = ClaudeFormatter()
    self.api_params_handler = ClaudeAPIParamsHandler(self)
    self._uploaded_file_ids: List[str] = []

def reset_tool_usage(self):
    """Reset tool usage tracking."""
    self.search_count = 0
    self.code_session_hours = 0.0
    super().reset_token_usage()

class OpenAIMassAgent(MassAgent):
    """MassAgent wrapper for OpenAI agent implementation."""

    def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
        super().__init__(agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, stream_callback=stream_callback, **kwargs)

def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
    super().__init__(agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, stream_callback=stream_callback, **kwargs)

class GrokMassAgent(OpenAIMassAgent):
    """MassAgent wrapper for Grok agent implementation."""

    def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
        super().__init__(agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, stream_callback=stream_callback, **kwargs)

def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
    super().__init__(agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, stream_callback=stream_callback, **kwargs)

class GeminiMassAgent(OpenAIMassAgent):
    """MassAgent wrapper for Gemini agent implementation."""

    def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
        super().__init__(agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, stream_callback=stream_callback, **kwargs)

    def _get_curr_messages_and_tools(self, task: TaskInput):
        """Get the current messages and tools for the agent."""
        system_tools = self._get_system_tools()
        built_in_tools = self._get_builtin_tools()
        custom_tools = self._get_registered_tools()
        tool_switch = bool(built_in_tools)
        if tool_switch:
            function_call_enabled = False
            available_tools = built_in_tools
        else:
            function_call_enabled = True
            available_tools = system_tools + custom_tools
        working_status, user_input = self._get_task_input(task)
        working_messages = self._get_task_input_messages(user_input)
        return (working_status, working_messages, available_tools, system_tools, custom_tools, built_in_tools, tool_switch, function_call_enabled)

    def work_on_task(self, task: TaskInput) -> List[Dict[str, str]]:
        """
        Work on the task using the Gemini backend with conversation continuation.

        NOTE:
        Gemini's does not support built-in tools and function call at the same time.
        Therefore, we provide them interchangedly in different rounds.
        The way the conversation is constructed is also different from OpenAI.
        You can provide consecutive user messages to represent the function call results.

        Args:
            task: The task to work on
            messages: Current conversation history
            restart_instruction: Optional instruction for restarting work (e.g., updates from other agents)

        Returns:
            Updated conversation history including agent's work
        """
        curr_round = 0
        working_status, working_messages, available_tools, system_tools, custom_tools, built_in_tools, tool_switch, function_call_enabled = self._get_curr_messages_and_tools(task)
        while curr_round < self.max_rounds and self.state.status == 'working':
            try:
                if working_messages[-1].get('role', '') == 'user':
                    if not function_call_enabled:
                        working_messages[-1]['content'] += '\n\n' + 'Note that the `add_answer` and `vote` tools are not enabled now. Please prioritize using the built-in tools to analyze the task first.'
                    else:
                        working_messages[-1]['content'] += '\n\n' + 'Note that the `add_answer` and `vote` tools are enabled now.'
                result = self.process_message(messages=working_messages, tools=available_tools)
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
                        if tool_switch:
                            available_tools = built_in_tools
                            function_call_enabled = False
                            print(f'🔄 Agent {self.agent_id} (Gemini) switching to built-in tools in the next round')
                    else:
                        working_status, working_messages, available_tools, system_tools, custom_tools, built_in_tools, tool_switch, function_call_enabled = self._get_curr_messages_and_tools(task)
                else:
                    if self.state.status == 'voted':
                        break
                    elif has_update and working_status != 'initial':
                        working_status, working_messages, available_tools, system_tools, custom_tools, built_in_tools, tool_switch, function_call_enabled = self._get_curr_messages_and_tools(task)
                    else:
                        working_messages.append({'role': 'user', 'content': 'Finish your work above by making a tool call of `vote` or `add_answer`. Make sure you actually call the tool.'})
                    if tool_switch:
                        available_tools = system_tools + custom_tools
                        function_call_enabled = True
                        print(f'🔄 Agent {self.agent_id} (Gemini) switching to custom tools in the next round')
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

def __init__(self, agent_id: int, orchestrator=None, model_config: Optional[ModelConfig]=None, stream_callback: Optional[Callable]=None, **kwargs):
    super().__init__(agent_id=agent_id, orchestrator=orchestrator, model_config=model_config, stream_callback=stream_callback, **kwargs)

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

class MassOrchestrator:
    """
    Central orchestrator for managing multiple agents in the MassGen framework, and logging for all events.

    Simplified workflow:
    1. Agents work on task (status: "working")
    2. When agents vote, they become "voted"
    3. When all votable agents have voted:
       - Check consensus
       - If consensus reached: select representative to present final answer
       - If no consensus: restart all agents for debate
    4. Representative presents final answer and system completes
    """

    def __init__(self, max_duration: int=600, consensus_threshold: float=0.0, max_debate_rounds: int=1, status_check_interval: float=2.0, thread_pool_timeout: int=5, streaming_orchestrator=None):
        """
        Initialize the orchestrator.

        Args:
            max_duration: Maximum duration for the entire task in seconds
            consensus_threshold: Fraction of agents that must agree for consensus (1.0 = unanimous)
            max_debate_rounds: Maximum number of debate rounds before fallback
            status_check_interval: Interval for checking agent status (seconds)
            thread_pool_timeout: Timeout for shutting down thread pool executor (seconds)
            streaming_orchestrator: Optional streaming orchestrator for real-time display
        """
        self.agents: Dict[int, Any] = {}
        self.agent_states: Dict[int, AgentState] = {}
        self.votes: List[VoteRecord] = []
        self.system_state = SystemState()
        self.max_duration = max_duration
        self.consensus_threshold = consensus_threshold
        self.max_debate_rounds = max_debate_rounds
        self.status_check_interval = status_check_interval
        self.thread_pool_timeout = thread_pool_timeout
        self.streaming_orchestrator = streaming_orchestrator
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self.communication_log: List[Dict[str, Any]] = []
        self.final_response: Optional[str] = None
        self.log_manager = get_log_manager()

    def register_agent(self, agent):
        """
        Register an agent with the orchestrator.

        Args:
            agent: MassAgent instance to register
        """
        with self._lock:
            self.agents[agent.agent_id] = agent
            self.agent_states[agent.agent_id] = agent.state
            agent.orchestrator = self

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an orchestrator event."""
        self.communication_log.append({'timestamp': time.time(), 'event_type': event_type, 'data': data})

    def update_agent_answer(self, agent_id: int, answer: str):
        """
        Update an agent's running answer.

        Args:
            agent_id: ID of the agent updating their answer
            answer: New answer content
        """
        with self._lock:
            if agent_id not in self.agent_states:
                raise ValueError(f'Agent {agent_id} not registered')
            old_answer_length = len(self.agent_states[agent_id].curr_answer)
            self.agent_states[agent_id].add_update(answer)
            preview = answer[:100] + '...' if len(answer) > 100 else answer
            print(f'📝 Agent {agent_id} answer updated ({old_answer_length} → {len(answer)} chars)')
            print(f'   🔍 {preview}')
            if self.log_manager:
                self.log_manager.log_agent_answer_update(agent_id=agent_id, answer=answer, phase=self.system_state.phase, orchestrator=self)
            self._log_event('answer_updated', {'agent_id': agent_id, 'answer': answer, 'timestamp': time.time()})

    def _get_current_vote_counts(self) -> Counter:
        """
        Get current vote counts based on agent states' vote_target.
        Returns Counter of agent_id -> vote_count for ALL agents (0 if no votes).
        """
        current_votes = []
        for agent_id, state in self.agent_states.items():
            if state.status == 'voted' and state.curr_vote is not None:
                current_votes.append(state.curr_vote.target_id)
        vote_counts = Counter(current_votes)
        for agent_id in self.agent_states.keys():
            if agent_id not in vote_counts:
                vote_counts[agent_id] = 0
        return vote_counts

    def _get_current_voted_agents_count(self) -> int:
        """
        Get count of agents who currently have status "voted".
        """
        return len([s for s in self.agent_states.values() if s.status == 'voted'])

    def _get_voting_status(self) -> Dict[str, Any]:
        """Get current voting status and distribution."""
        vote_counts = self._get_current_vote_counts()
        total_agents = len(self.agents)
        failed_agents = len([s for s in self.agent_states.values() if s.status == 'failed'])
        votable_agents = total_agents - failed_agents
        voted_agents = self._get_current_voted_agents_count()
        return {'vote_distribution': dict(vote_counts), 'total_agents': total_agents, 'failed_agents': failed_agents, 'votable_agents': votable_agents, 'voted_agents': voted_agents, 'votes_needed_for_consensus': max(1, int(votable_agents * self.consensus_threshold)), 'leading_agent': vote_counts.most_common(1)[0] if vote_counts else None}

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status information."""
        return {'phase': self.system_state.phase, 'consensus_reached': self.system_state.consensus_reached, 'agents': {agent_id: {'status': state.status, 'update_times': len(state.updated_answers), 'chat_round': state.chat_round, 'vote_target': state.curr_vote.target_id if state.curr_vote else None, 'execution_time': state.execution_time} for agent_id, state in self.agent_states.items()}, 'voting_status': self._get_voting_status(), 'runtime': time.time() - self.system_state.start_time if self.system_state.start_time else 0}

    def cast_vote(self, voter_id: int, target_id: int, reason: str=''):
        """
        Record a vote from one agent for another agent's solution.

        Args:
            voter_id: ID of the agent casting the vote
            target_id: ID of the agent being voted for
            reason: The reason for the vote (optional)
        """
        with self._lock:
            logger.info(f'🗳️ VOTING: Agent {voter_id} casting vote')
            print(f'🗳️  VOTE: Agent {voter_id} → Agent {target_id} ({self.system_state.phase})')
            if reason:
                print(f'   📝 Voting reason: {len(reason)} chars')
            if voter_id not in self.agent_states:
                logger.error(f'   ❌ Invalid voter: Agent {voter_id} not registered')
                raise ValueError(f'Voter agent {voter_id} not registered')
            if target_id not in self.agent_states:
                logger.error(f'   ❌ Invalid target: Agent {target_id} not registered')
                raise ValueError(f'Target agent {target_id} not registered')
            previous_vote = self.agent_states[voter_id].curr_vote
            if previous_vote:
                logger.info(f'   🔄 Agent {voter_id} changed vote from Agent {previous_vote.target_id} to Agent {target_id}')
            else:
                logger.info(f'   ✨ Agent {voter_id} new vote for Agent {target_id}')
            vote = VoteRecord(voter_id=voter_id, target_id=target_id, reason=reason, timestamp=time.time())
            self.votes.append(vote)
            old_status = self.agent_states[voter_id].status
            self.agent_states[voter_id].status = 'voted'
            self.agent_states[voter_id].curr_vote = vote
            self.agent_states[voter_id].cast_votes.append(vote)
            self.agent_states[voter_id].execution_end_time = time.time()
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_agent_status(voter_id, 'voted')
                self.streaming_orchestrator.update_agent_vote_target(voter_id, target_id)
                update_count = len(self.agent_states[voter_id].updated_answers)
                self.streaming_orchestrator.update_agent_update_count(voter_id, update_count)
                for agent_id, agent_state in self.agent_states.items():
                    vote_cast_count = len(agent_state.cast_votes)
                    self.streaming_orchestrator.update_agent_votes_cast(agent_id, vote_cast_count)
                vote_counts = self._get_current_vote_counts()
                self.streaming_orchestrator.update_vote_distribution(dict(vote_counts))
                vote_msg = f'👍 Agent {voter_id} voted for Agent {target_id}'
                self.streaming_orchestrator.add_system_message(vote_msg)
            if self.log_manager:
                self.log_manager.log_voting_event(voter_id=voter_id, target_id=target_id, phase=self.system_state.phase, reason=reason, orchestrator=self)
                self.log_manager.log_agent_status_change(agent_id=voter_id, old_status=old_status, new_status='voted', phase=self.system_state.phase)
            vote_counts = self._get_current_vote_counts()
            voted_agents_count = self._get_current_voted_agents_count()
            logger.info(f'   📊 Vote distribution: {dict(vote_counts)}')
            logger.info(f'   📈 Voting progress: {voted_agents_count}/{len(self.agent_states)} agents voted')
            total_agents = len(self.agent_states)
            votes_needed = max(1, int(total_agents * self.consensus_threshold))
            if vote_counts:
                leading_agent, leading_votes = vote_counts.most_common(1)[0]
                logger.info(f'   🏆 Leading: Agent {leading_agent} with {leading_votes} votes (need {votes_needed} for consensus)')
            self._log_event('vote_cast', {'voter_id': voter_id, 'target_id': target_id, 'timestamp': vote.timestamp, 'vote_distribution': dict(vote_counts), 'total_votes': voted_agents_count})

    def notify_answer_update(self, agent_id: int, answer: str):
        """
        Called when an agent updates their answer.
        This should restart all voted agents who haven't seen this update yet.
        """
        logger.info(f'📢 Agent {agent_id} updated answer')
        self.update_agent_answer(agent_id, answer)
        if self.streaming_orchestrator:
            answer_msg = f'📝 Agent {agent_id} updated answer ({len(answer)} chars)'
            self.streaming_orchestrator.add_system_message(answer_msg)
            update_count = len(self.agent_states[agent_id].updated_answers)
            self.streaming_orchestrator.update_agent_update_count(agent_id, update_count)
        with self._lock:
            restarted_agents = []
            time.time()
            for other_agent_id, state in self.agent_states.items():
                if other_agent_id != agent_id and state.status == 'voted':
                    state.status = 'working'
                    state.curr_vote = None
                    state.execution_start_time = time.time()
                    restarted_agents.append(other_agent_id)
                    logger.info(f'🔄 Agent {other_agent_id} restarted due to update from Agent {agent_id}')
                    if self.streaming_orchestrator:
                        self.streaming_orchestrator.update_agent_status(other_agent_id, 'working')
                        self.streaming_orchestrator.update_agent_vote_target(other_agent_id, None)
                        update_count = len(self.agent_states[other_agent_id].updated_answers)
                        self.streaming_orchestrator.update_agent_update_count(other_agent_id, update_count)
                        restart_msg = f'🔄 Agent {other_agent_id} restarted due to new update'
                        self.streaming_orchestrator.add_system_message(restart_msg)
                    if self.log_manager:
                        self.log_manager.log_agent_restart(agent_id=other_agent_id, reason=f'new_update_from_agent_{agent_id}', phase=self.system_state.phase)
            if restarted_agents:
                logger.info(f'🔄 Restarted agents: {restarted_agents}')
                if self.streaming_orchestrator:
                    vote_counts = self._get_current_vote_counts()
                    self.streaming_orchestrator.update_vote_distribution(dict(vote_counts))
                    for agent_id, agent_state in self.agent_states.items():
                        vote_cast_count = len(agent_state.cast_votes)
                        self.streaming_orchestrator.update_agent_votes_cast(agent_id, vote_cast_count)
            return restarted_agents

    def _check_consensus(self) -> bool:
        """
        Check if consensus has been reached based on current votes.
        Improved to handle edge cases and ensure proper consensus calculation.
        """
        with self._lock:
            total_agents = len(self.agents)
            failed_agents_count = len([s for s in self.agent_states.values() if s.status == 'failed'])
            votable_agents_count = total_agents - failed_agents_count
            if votable_agents_count == 0:
                logger.warning('⚠️ No votable agents available for consensus')
                return False
            if votable_agents_count == 1:
                working_agents = [aid for aid, state in self.agent_states.items() if state.status == 'working']
                if not working_agents:
                    votable_agent = [aid for aid, state in self.agent_states.items() if state.status != 'failed'][0]
                    logger.info(f'🎯 Single agent consensus: Agent {votable_agent}')
                    self._reach_consensus(votable_agent)
                    return True
                return False
            vote_counts = self._get_current_vote_counts()
            votes_needed = max(1, int(votable_agents_count * self.consensus_threshold))
            if vote_counts and vote_counts.most_common(1)[0][1] >= votes_needed:
                winning_agent_id = vote_counts.most_common(1)[0][0]
                winning_votes = vote_counts.most_common(1)[0][1]
                if self.agent_states[winning_agent_id].status == 'failed':
                    logger.warning(f'⚠️ Winning agent {winning_agent_id} has failed - recalculating')
                    return False
                logger.info(f'✅ Consensus reached: Agent {winning_agent_id} with {winning_votes}/{votable_agents_count} votes')
                self._reach_consensus(winning_agent_id)
                return True
            return False

    def mark_agent_failed(self, agent_id: int, reason: str=''):
        """
        Mark an agent as failed.

        Args:
            agent_id: ID of the agent to mark as failed
            reason: Optional reason for the failure
        """
        with self._lock:
            logger.info(f'💥 AGENT FAILURE: Agent {agent_id} marked as failed')
            print(f'      💥 MARK_FAILED: Agent {agent_id}')
            print(f'      📊 Current phase: {self.system_state.phase}')
            if agent_id not in self.agent_states:
                logger.error(f'   ❌ Invalid agent: Agent {agent_id} not registered')
                raise ValueError(f'Agent {agent_id} not registered')
            old_status = self.agent_states[agent_id].status
            self.agent_states[agent_id].status = 'failed'
            self.agent_states[agent_id].execution_end_time = time.time()
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_agent_status(agent_id, 'failed')
                failure_msg = f'💥 Agent {agent_id} failed: {reason}' if reason else f'💥 Agent {agent_id} failed'
                self.streaming_orchestrator.add_system_message(failure_msg)
            if self.log_manager:
                self.log_manager.log_agent_status_change(agent_id=agent_id, old_status=old_status, new_status='failed', phase=self.system_state.phase)
            self._log_event('agent_failed', {'agent_id': agent_id, 'reason': reason, 'timestamp': time.time(), 'old_status': old_status})
            status_counts = Counter((state.status for state in self.agent_states.values()))
            logger.info(f'   📊 Status distribution: {dict(status_counts)}')
            logger.info(f'   📈 Failed agents: {status_counts.get('failed', 0)}/{len(self.agent_states)} total')

    def _reach_consensus(self, winning_agent_id: int):
        """Mark consensus as reached and finalize the system."""
        old_phase = self.system_state.phase
        self.system_state.consensus_reached = True
        self.system_state.representative_agent_id = winning_agent_id
        self.system_state.phase = 'consensus'
        if self.streaming_orchestrator:
            vote_distribution = dict(self._get_current_vote_counts())
            self.streaming_orchestrator.update_consensus_status(winning_agent_id, vote_distribution)
            self.streaming_orchestrator.update_phase(old_phase, 'consensus')
        if self.log_manager:
            vote_distribution = dict(self._get_current_vote_counts())
            self.log_manager.log_consensus_reached(winning_agent_id=winning_agent_id, vote_distribution=vote_distribution, is_fallback=False, phase=self.system_state.phase)
            self.log_manager.log_phase_transition(old_phase=old_phase, new_phase='consensus', additional_data={'consensus_reached': True, 'winning_agent_id': winning_agent_id, 'is_fallback': False})
        self._log_event('consensus_reached', {'winning_agent_id': winning_agent_id, 'fallback_to_majority': False, 'final_vote_distribution': dict(self._get_current_vote_counts())})

    def export_detailed_session_log(self) -> Dict[str, Any]:
        """
        Export complete detailed session information for comprehensive analysis.
        Includes all outputs, metrics, and evaluation results.
        """
        session_log = {'session_metadata': {'session_id': f'mass_session_{int(self.system_state.start_time)}' if self.system_state.start_time else None, 'start_time': self.system_state.start_time, 'end_time': self.system_state.end_time, 'total_duration': self.system_state.end_time - self.system_state.start_time if self.system_state.start_time and self.system_state.end_time else None, 'timestamp': datetime.now().isoformat(), 'system_version': 'MassGen v1.0'}, 'task_information': {'question': self.system_state.task.question if self.system_state.task else None, 'task_id': self.system_state.task.task_id if self.system_state.task else None, 'context': self.system_state.task.context if self.system_state.task else None}, 'system_configuration': {'max_duration': self.max_duration, 'consensus_threshold': self.consensus_threshold, 'max_debate_rounds': self.max_debate_rounds, 'agents': [agent.model for agent in self.agents.values()]}, 'agent_details': {agent_id: {'status': state.status, 'updates_count': len(state.updated_answers), 'chat_length': len(state.chat_history), 'chat_round': state.chat_round, 'vote_target': state.curr_vote.target_id if state.curr_vote else None, 'execution_time': state.execution_time, 'execution_start_time': state.execution_start_time, 'execution_end_time': state.execution_end_time, 'updated_answers': [{'timestamp': update.timestamp, 'status': update.status, 'answer_length': len(update.answer)} for update in state.updated_answers]} for agent_id, state in self.agent_states.items()}, 'voting_analysis': {'vote_records': [{'voter_id': vote.voter_id, 'target_id': vote.target_id, 'timestamp': vote.timestamp, 'reason_length': len(vote.reason) if vote.reason else 0} for vote in self.votes], 'vote_timeline': [{'timestamp': vote.timestamp, 'event': f'Agent {vote.voter_id} → Agent {vote.target_id}'} for vote in self.votes]}, 'communication_log': self.communication_log, 'system_events': [{'timestamp': entry['timestamp'], 'event_type': entry['event_type'], 'data_summary': {k: len(v) if isinstance(v, (str, list, dict)) else v for k, v in entry['data'].items()}} for entry in self.communication_log]}
        return session_log

    def start_task(self, task: TaskInput):
        """
        Initialize the system for a new task and run the main workflow.

        Args:
            task: TaskInput containing the problem to solve

        Returns:
            response: Dict[str, Any] containing the final answer to the task's question, and relevant information
        """
        with self._lock:
            logger.info('🎯 ORCHESTRATOR: Starting new task')
            logger.info(f'   Task ID: {task.task_id}')
            logger.info(f'   Question preview: {task.question}')
            logger.info(f'   Registered agents: {list(self.agents.keys())}')
            logger.info(f'   Max duration: {self.max_duration}')
            logger.info(f'   Consensus threshold: {self.consensus_threshold}')
            self.system_state.task = task
            self.system_state.start_time = time.time()
            self.system_state.phase = 'collaboration'
            self.final_response = None
            for agent_id, agent in self.agents.items():
                agent.state = AgentState(agent_id=agent_id)
                self.agent_states[agent_id] = agent.state
                agent.state.chat_history = []
                if self.streaming_orchestrator:
                    self.streaming_orchestrator.set_agent_model(agent_id, agent.model)
                    self.streaming_orchestrator.update_agent_status(agent_id, 'working')
                    self.streaming_orchestrator.update_agent_update_count(agent_id, 0)
            self.votes.clear()
            self.communication_log.clear()
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_phase('unknown', 'collaboration')
                self.streaming_orchestrator.update_debate_rounds(0)
                init_msg = f'🚀 Starting MassGen task with {len(self.agents)} agents'
                self.streaming_orchestrator.add_system_message(init_msg)
            self._log_event('task_started', {'task_id': task.task_id, 'question': task.question})
            logger.info('✅ Task initialization completed successfully')
        return self._run_mass_workflow(task)

    def _run_mass_workflow(self, task: TaskInput) -> Dict[str, Any]:
        """
        Run the MassGen workflow with dynamic agent restart support:
        1. All agents work in parallel
        2. Agents restart when others share updates (if they had voted)
        3. When all have voted, check consensus
        4. If no consensus, restart all for debate
        5. If consensus, representative presents final answer
        """
        logger.info('🚀 Starting MassGen workflow')
        debate_rounds = 0
        start_time = time.time()
        while not self._stop_event.is_set():
            if time.time() - start_time > self.max_duration:
                logger.warning('⏰ Maximum duration reached - forcing consensus')
                self._force_consensus_by_timeout()
                self._present_final_answer(task)
                break
            logger.info(f'📢 Starting collaboration round {debate_rounds + 1}')
            self._run_all_agents_with_dynamic_restart(task)
            if self._all_agents_voted():
                logger.info('🗳️ All agents have voted - checking consensus')
                if self._check_consensus():
                    logger.info('🎉 Consensus reached!')
                    self._present_final_answer(task)
                    break
                else:
                    debate_rounds += 1
                    if self.streaming_orchestrator:
                        self.streaming_orchestrator.update_debate_rounds(debate_rounds)
                    if debate_rounds > self.max_debate_rounds:
                        logger.warning(f'⚠️ Maximum debate rounds ({self.max_debate_rounds}) reached')
                        self._force_consensus_by_timeout()
                        self._present_final_answer(task)
                        break
                    logger.info(f'🗣️ No consensus - starting debate round {debate_rounds}')
                    self._restart_all_agents_for_debate()
            else:
                time.sleep(self.status_check_interval)
        return self._finalize_session()

    def _run_all_agents_with_dynamic_restart(self, task: TaskInput):
        """
        Run all agents in parallel with support for dynamic restarts.
        This approach handles agents restarting mid-execution.
        """
        active_futures = {}
        executor = ThreadPoolExecutor(max_workers=len(self.agents))
        try:
            for agent_id in self.agents.keys():
                if self.agent_states[agent_id].status not in ['failed']:
                    self._start_agent_if_working(agent_id, task, executor, active_futures)
            while active_futures and (not self._all_agents_voted()):
                completed_futures = []
                for agent_id, future in list(active_futures.items()):
                    if future.done():
                        completed_futures.append(agent_id)
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f'❌ Agent {agent_id} failed: {e}')
                            self.mark_agent_failed(agent_id, str(e))
                for agent_id in completed_futures:
                    del active_futures[agent_id]
                for agent_id in self.agents.keys():
                    if agent_id not in active_futures and self.agent_states[agent_id].status == 'working':
                        self._start_agent_if_working(agent_id, task, executor, active_futures)
                time.sleep(0.1)
        finally:
            for future in active_futures.values():
                future.cancel()
            executor.shutdown(wait=True)

    def _start_agent_if_working(self, agent_id: int, task: TaskInput, executor: ThreadPoolExecutor, active_futures: Dict):
        """Start an agent if it's in working status and not already running."""
        if self.agent_states[agent_id].status == 'working' and agent_id not in active_futures:
            self.agent_states[agent_id].execution_start_time = time.time()
            future = executor.submit(self._run_single_agent, agent_id, task)
            active_futures[agent_id] = future
            logger.info(f'🤖 Agent {agent_id} started/restarted')

    def _run_single_agent(self, agent_id: int, task: TaskInput):
        """Run a single agent's work_on_task method."""
        agent = self.agents[agent_id]
        try:
            logger.info(f'🤖 Agent {agent_id} starting work')
            updated_messages = agent.work_on_task(task)
            self.agent_states[agent_id].chat_history.append(updated_messages)
            self.agent_states[agent_id].chat_round = agent.state.chat_round
            if self.streaming_orchestrator:
                self.streaming_orchestrator.update_agent_chat_round(agent_id, agent.state.chat_round)
                update_count = len(self.agent_states[agent_id].updated_answers)
                self.streaming_orchestrator.update_agent_update_count(agent_id, update_count)
            logger.info(f'✅ Agent {agent_id} completed work with status: {self.agent_states[agent_id].status}')
        except Exception as e:
            logger.error(f'❌ Agent {agent_id} failed: {e}')
            self.mark_agent_failed(agent_id, str(e))

    def _all_agents_voted(self) -> bool:
        """Check if all votable agents have voted."""
        votable_agents = [aid for aid, state in self.agent_states.items() if state.status not in ['failed']]
        voted_agents = [aid for aid, state in self.agent_states.items() if state.status == 'voted']
        return len(voted_agents) == len(votable_agents) and len(votable_agents) > 0

    def _restart_all_agents_for_debate(self):
        """
        Restart all agents for debate by resetting their status
        We don't clear vote target when restarting for debate as answers are not updated
        """
        logger.info('🔄 Restarting all agents for debate')
        with self._lock:
            if self.streaming_orchestrator:
                self.streaming_orchestrator.reset_consensus()
                self.streaming_orchestrator.update_phase(self.system_state.phase, 'collaboration')
                self.streaming_orchestrator.add_system_message('🗣️ Starting debate phase - no consensus reached')
            if self.log_manager:
                self.log_manager.log_debate_started(phase='collaboration')
                self.log_manager.log_phase_transition(old_phase=self.system_state.phase, new_phase='collaboration', additional_data={'reason': 'no_consensus_reached', 'debate_round': True})
            for agent_id, state in self.agent_states.items():
                if state.status not in ['failed']:
                    state.status
                    state.status = 'working'
                    if self.streaming_orchestrator:
                        self.streaming_orchestrator.update_agent_status(agent_id, 'working')
                    if self.log_manager:
                        self.log_manager.log_agent_restart(agent_id=agent_id, reason='debate_phase_restart', phase='collaboration')
            self.system_state.phase = 'collaboration'

    def _present_final_answer(self, task: TaskInput):
        """
        Run the final presentation by the representative agent.
        """
        representative_id = self.system_state.representative_agent_id
        if not representative_id:
            logger.error('No representative agent selected')
            return
        logger.info(f'🎯 Agent {representative_id} presenting final answer')
        try:
            representative_agent = self.agents[representative_id]
            _, user_input = representative_agent._get_task_input(task)
            messages = [{'role': 'system', 'content': "\nYou are given a task and multiple agents' answers and their votes.\nPlease incorporate these information and provide a final BEST answer to the original message.\n"}, {'role': 'user', 'content': user_input + '\nPlease provide the final BEST answer to the original message by incorporating these information.\nThe final answer must be self-contained, complete, well-sourced, compelling, and ready to serve as the definitive final response.\n'}]
            result = representative_agent.process_message(messages)
            self.final_response = result.text
            self.system_state.phase = 'completed'
            self.system_state.end_time = time.time()
            logger.info(f'✅ Final presentation completed by Agent {representative_id}')
        except Exception as e:
            logger.error(f'❌ Final presentation failed: {e}')
            self.final_response = f'Error in final presentation: {str(e)}'

    def _force_consensus_by_timeout(self):
        """
        Force consensus selection when maximum duration is reached.
        """
        logger.warning('⏰ Forcing consensus due to timeout')
        with self._lock:
            vote_counts = self._get_current_vote_counts()
            if vote_counts:
                winning_agent_id = vote_counts.most_common(1)[0][0]
                logger.info(f'   Selected Agent {winning_agent_id} with {vote_counts[winning_agent_id]} votes')
            else:
                working_agents = [aid for aid, state in self.agent_states.items() if state.status == 'working']
                winning_agent_id = working_agents[0] if working_agents else list(self.agents.keys())[0]
                logger.info(f'   No votes - selected Agent {winning_agent_id} as fallback')
            self._reach_consensus(winning_agent_id)

    def _finalize_session(self) -> Dict[str, Any]:
        """
        Finalize the session and return comprehensive results.
        """
        logger.info('🏁 Finalizing session')
        with self._lock:
            if not self.system_state.end_time:
                self.system_state.end_time = time.time()
            session_duration = self.system_state.end_time - self.system_state.start_time if self.system_state.start_time else 0
            if self.log_manager:
                self.log_manager.save_agent_states(self)
                self.log_manager.log_task_completion({'final_answer': self.final_response, 'consensus_reached': self.system_state.consensus_reached, 'representative_agent_id': self.system_state.representative_agent_id, 'session_duration': session_duration})
            result = {'answer': self.final_response or 'No final answer generated', 'consensus_reached': self.system_state.consensus_reached, 'representative_agent_id': self.system_state.representative_agent_id, 'session_duration': session_duration, 'summary': {'total_agents': len(self.agents), 'failed_agents': len([s for s in self.agent_states.values() if s.status == 'failed']), 'total_votes': len(self.votes), 'final_vote_distribution': dict(self._get_current_vote_counts())}, 'system_logs': self.export_detailed_session_log()}
            if self.log_manager and (not self.log_manager.non_blocking):
                try:
                    result_file = self.log_manager.session_dir / 'result.json'
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                    logger.info(f'💾 Result saved to {result_file}')
                except Exception as e:
                    logger.warning(f'⚠️ Failed to save result.json: {e}')
            logger.info(f'✅ Session completed in {session_duration:.2f} seconds')
            logger.info(f'   Consensus: {result['consensus_reached']}')
            logger.info(f'   Representative: Agent {result['representative_agent_id']}')
            return result

    def cleanup(self):
        """
        Clean up resources and stop all agents.
        """
        logger.info('🧹 Cleaning up orchestrator resources')
        self._stop_event.set()
        if self.log_manager and self.agent_states:
            try:
                self.log_manager.save_agent_states(self)
                logger.info('✅ Final agent states saved')
            except Exception as e:
                logger.warning(f'⚠️ Error saving final agent states: {e}')
        if self.log_manager:
            try:
                self.log_manager.cleanup()
                logger.info('✅ Log manager cleaned up')
            except Exception as e:
                logger.warning(f'⚠️ Error cleaning up log manager: {e}')
        if self.streaming_orchestrator:
            try:
                self.streaming_orchestrator.cleanup()
                logger.info('✅ Streaming orchestrator cleaned up')
            except Exception as e:
                logger.warning(f'⚠️ Error cleaning up streaming orchestrator: {e}')
        logger.info('✅ Orchestrator cleanup completed')

def __init__(self, max_duration: int=600, consensus_threshold: float=0.0, max_debate_rounds: int=1, status_check_interval: float=2.0, thread_pool_timeout: int=5, streaming_orchestrator=None):
    """
        Initialize the orchestrator.

        Args:
            max_duration: Maximum duration for the entire task in seconds
            consensus_threshold: Fraction of agents that must agree for consensus (1.0 = unanimous)
            max_debate_rounds: Maximum number of debate rounds before fallback
            status_check_interval: Interval for checking agent status (seconds)
            thread_pool_timeout: Timeout for shutting down thread pool executor (seconds)
            streaming_orchestrator: Optional streaming orchestrator for real-time display
        """
    self.agents: Dict[int, Any] = {}
    self.agent_states: Dict[int, AgentState] = {}
    self.votes: List[VoteRecord] = []
    self.system_state = SystemState()
    self.max_duration = max_duration
    self.consensus_threshold = consensus_threshold
    self.max_debate_rounds = max_debate_rounds
    self.status_check_interval = status_check_interval
    self.thread_pool_timeout = thread_pool_timeout
    self.streaming_orchestrator = streaming_orchestrator
    self._lock = threading.RLock()
    self._stop_event = threading.Event()
    self.communication_log: List[Dict[str, Any]] = []
    self.final_response: Optional[str] = None
    self.log_manager = get_log_manager()

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

class genai:

    @staticmethod
    def configure(**kwargs):
        raise ImportError('Google genai package not installed. Install with: pip install google-genai')

@staticmethod
def configure(**kwargs):
    raise ImportError('Google genai package not installed. Install with: pip install google-genai')

class _FakeResponses:

    async def create(self, **kwargs: Any):

        def _item():
            return SimpleNamespace(type='response.completed', response={'output': []})
        return _FakeStreamSingleStop(_item)

def _item():
    return SimpleNamespace(type='response.completed', response={'output': []})

class _FakeOpenAIClient(_FakeAsyncClientBase):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.responses = _FakeResponses()

def __init__(self, *args: Any, **kwargs: Any):
    super().__init__(*args, **kwargs)
    self.responses = _FakeResponses()

class _FakeChatCompletions:

    async def create(self, **kwargs: Any):

        def _item():
            choice = SimpleNamespace(delta=None, finish_reason='stop')
            return SimpleNamespace(choices=[choice], usage=None)
        return _FakeStreamSingleStop(_item)

def _item():
    choice = SimpleNamespace(delta=None, finish_reason='stop')
    return SimpleNamespace(choices=[choice], usage=None)

class _FakeOpenAIClientForGrok(_FakeAsyncClientBase):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.chat = SimpleNamespace(completions=_FakeChatCompletions())

def __init__(self, *args: Any, **kwargs: Any):
    super().__init__(*args, **kwargs)
    self.chat = SimpleNamespace(completions=_FakeChatCompletions())

class _FakeClaudeMessages:

    async def create(self, **kwargs: Any):

        def _item():
            return SimpleNamespace(type='message_stop')
        return _FakeStreamSingleStop(_item)

def _item():
    return SimpleNamespace(type='message_stop')

class _FakeAnthropicClient(_FakeAsyncClientBase):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.messages = _FakeClaudeMessages()
        self.beta = SimpleNamespace(messages=_FakeClaudeMessages())

def __init__(self, *args: Any, **kwargs: Any):
    super().__init__(*args, **kwargs)
    self.messages = _FakeClaudeMessages()
    self.beta = SimpleNamespace(messages=_FakeClaudeMessages())

class MockClaudeCodeAgent(ChatAgent):
    """Mock Claude Code agent for testing."""

    def __init__(self, agent_id: str, cwd: str=None):
        super().__init__(session_id=f'session_{agent_id}')
        self.agent_id = agent_id
        self.backend = MockClaudeCodeBackend(cwd)

    async def chat(self, messages, tools=None, reset_chat=False, clear_history=False):
        """Mock chat implementation."""
        for _ in range(3):
            yield {'type': 'content', 'content': f'Working on task from {self.agent_id}'}
        yield {'type': 'result', 'data': ('answer', f'Solution from {self.agent_id}')}

def __init__(self, agent_id: str, cwd: str=None):
    super().__init__(session_id=f'session_{agent_id}')
    self.agent_id = agent_id
    self.backend = MockClaudeCodeBackend(cwd)

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

def test_setup_api_keys_copies_gemini_key():
    """Test that GEMINI_API_KEY is copied to GOOGLE_GEMINI_API_KEY."""
    os.environ['GEMINI_API_KEY'] = 'test_key'
    if 'GOOGLE_GEMINI_API_KEY' in os.environ:
        del os.environ['GOOGLE_GEMINI_API_KEY']
    setup_api_keys()
    assert os.environ['GOOGLE_GEMINI_API_KEY'] == 'test_key'
    del os.environ['GEMINI_API_KEY']
    del os.environ['GOOGLE_GEMINI_API_KEY']

