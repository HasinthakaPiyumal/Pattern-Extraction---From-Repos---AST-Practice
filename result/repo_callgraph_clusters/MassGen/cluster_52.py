# Cluster 52

class CoordinationTracker:
    """
    Principled coordination tracking that simply records what happens.

    The orchestrator tells us exactly what occurred and when, without
    us having to infer or manage complex state transitions.
    """

    def __init__(self):
        self.events: List[CoordinationEvent] = []
        self.answers_by_agent: Dict[str, List[AgentAnswer]] = {}
        self.final_answers: Dict[str, AgentAnswer] = {}
        self.votes: List[AgentVote] = []
        self.current_iteration: int = 0
        self.agent_rounds: Dict[str, int] = {}
        self.agent_round_context: Dict[str, Dict[int, List[str]]] = {}
        self.iteration_available_labels: List[str] = []
        self.pending_agent_restarts: Dict[str, bool] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.agent_ids: List[str] = []
        self.final_winner: Optional[str] = None
        self.final_context: Optional[Dict[str, Any]] = None
        self.is_final_round: bool = False
        self.user_prompt: Optional[str] = None
        self.agent_context_labels: Dict[str, List[str]] = {}
        self.snapshot_mappings: Dict[str, Dict[str, Any]] = {}

    def _make_snapshot_path(self, kind: str, agent_id: str, timestamp: str) -> str:
        """Generate standardized snapshot paths.

        Args:
            kind: Type of snapshot ('answer', 'vote', 'final_answer', etc.)
            agent_id: The agent ID
            timestamp: The timestamp or 'final' for final answers

        Returns:
            The formatted path string
        """
        if kind == 'final_answer' and timestamp == 'final':
            return f'final/{agent_id}/answer.txt'
        if kind == 'answer':
            return f'{agent_id}/{timestamp}/answer.txt'
        if kind == 'vote':
            return f'{agent_id}/{timestamp}/vote.json'
        return f'{agent_id}/{timestamp}/{kind}.txt'

    def initialize_session(self, agent_ids: List[str], user_prompt: Optional[str]=None):
        """Initialize a new coordination session."""
        self.start_time = time.time()
        self.agent_ids = agent_ids.copy()
        self.answers_by_agent = {aid: [] for aid in agent_ids}
        self.user_prompt = user_prompt
        self.agent_rounds = {aid: 0 for aid in agent_ids}
        self.agent_round_context = {aid: {0: []} for aid in agent_ids}
        self.pending_agent_restarts = {aid: False for aid in agent_ids}
        self.agent_context_labels = {aid: [] for aid in agent_ids}
        self._add_event(EventType.SESSION_START, None, f'Started with agents: {agent_ids}')

    def get_anonymous_id(self, agent_id: str) -> str:
        """Get anonymous ID (agent1, agent2) for a full agent ID."""
        agent_num = self._get_agent_number(agent_id)
        return f'agent{agent_num}' if agent_num else agent_id

    def _get_agent_number(self, agent_id: str) -> Optional[int]:
        """Get the 1-based number for an agent (1, 2, 3, etc.)."""
        if agent_id in self.agent_ids:
            return self.agent_ids.index(agent_id) + 1
        return None

    def get_agent_context_labels(self, agent_id: str) -> List[str]:
        """Get the answer labels this agent can currently see."""
        return self.agent_context_labels.get(agent_id, []).copy()

    def get_latest_answer_label(self, agent_id: str) -> Optional[str]:
        """Get the latest answer label for an agent."""
        if agent_id in self.answers_by_agent and self.answers_by_agent[agent_id]:
            return self.answers_by_agent[agent_id][-1].label
        return None

    def get_agent_round(self, agent_id: str) -> int:
        """Get the current round for a specific agent."""
        return self.agent_rounds.get(agent_id, 0)

    @property
    def max_round(self) -> int:
        """Get the highest round number across all agents."""
        return max(self.agent_rounds.values()) if self.agent_rounds else 0

    def start_new_iteration(self):
        """Start a new coordination iteration."""
        self.current_iteration += 1
        self.iteration_available_labels = []
        for agent_id, answers_list in self.answers_by_agent.items():
            if answers_list:
                latest_answer = answers_list[-1]
                self.iteration_available_labels.append(latest_answer.label)
        self._add_event(EventType.ITERATION_START, None, f'Starting coordination iteration {self.current_iteration}', {'iteration': self.current_iteration, 'available_answers': self.iteration_available_labels.copy()})

    def end_iteration(self, reason: str, details: Dict[str, Any]=None):
        """Record how an iteration ended."""
        context = {'iteration': self.current_iteration, 'end_reason': reason, 'available_answers': self.iteration_available_labels.copy()}
        if details:
            context.update(details)
        self._add_event(EventType.ITERATION_END, None, f'Iteration {self.current_iteration} ended: {reason}', context)

    def set_user_prompt(self, prompt: str):
        """Set or update the user prompt."""
        self.user_prompt = prompt

    def change_status(self, agent_id: str, new_status: AgentStatus):
        """Record when an agent changes status."""
        self._add_event(EventType.STATUS_CHANGE, agent_id, f'Changed to status: {new_status.value}')

    def track_agent_context(self, agent_id: str, answers: Dict[str, str], conversation_history: Optional[Dict[str, Any]]=None, agent_full_context: Optional[str]=None, snapshot_dir: Optional[str]=None):
        """Record when an agent receives context.

        Args:
            agent_id: The agent receiving context
            answers: Dict of agent_id -> answer content
            conversation_history: Optional conversation history
            agent_full_context: Optional full context string/dict to save
            snapshot_dir: Optional directory path to save context.txt
        """
        answer_labels = []
        for answering_agent_id in answers.keys():
            if answering_agent_id in self.answers_by_agent and self.answers_by_agent[answering_agent_id]:
                latest_answer = self.answers_by_agent[answering_agent_id][-1]
                answer_labels.append(latest_answer.label)
        self.agent_context_labels[agent_id] = answer_labels.copy()
        anon_answering_agents = [self.get_anonymous_id(aid) for aid in answers.keys()]
        context = {'available_answers': anon_answering_agents, 'available_answer_labels': answer_labels.copy(), 'answer_count': len(answers), 'has_conversation_history': bool(conversation_history)}
        self._add_event(EventType.CONTEXT_RECEIVED, agent_id, f'Received context with {len(answers)} answers', context)

    def track_restart_signal(self, triggering_agent: str, agents_restarted: List[str]):
        """Record when a restart is triggered - but don't increment rounds yet."""
        for agent_id in agents_restarted:
            if True:
                self.pending_agent_restarts[agent_id] = True
        context = {'affected_agents': agents_restarted, 'triggering_agent': triggering_agent}
        self._add_event(EventType.RESTART_TRIGGERED, triggering_agent, f'Triggered restart affecting {len(agents_restarted)} agents', context)

    def complete_agent_restart(self, agent_id: str):
        """Record when an agent has completed its restart and increment their round.

        Args:
            agent_id: The agent that completed restart
        """
        if not self.pending_agent_restarts.get(agent_id, False):
            return
        self.pending_agent_restarts[agent_id] = False
        self.agent_rounds[agent_id] += 1
        new_round = self.agent_rounds[agent_id]
        if agent_id not in self.agent_round_context:
            self.agent_round_context[agent_id] = {}
        context = {'agent_round': new_round}
        self._add_event(EventType.RESTART_COMPLETED, agent_id, f'Completed restart - now in round {new_round}', context)

    def add_agent_answer(self, agent_id: str, answer: str, snapshot_timestamp: Optional[str]=None):
        """Record when an agent provides a new answer.

        Args:
            agent_id: ID of the agent
            answer: The answer content
            snapshot_timestamp: Timestamp of the filesystem snapshot (if any)
        """
        agent_answer = AgentAnswer(agent_id=agent_id, content=answer, timestamp=time.time())
        agent_num = self._get_agent_number(agent_id)
        answer_num = len(self.answers_by_agent[agent_id]) + 1
        label = f'agent{agent_num}.{answer_num}'
        agent_answer.label = label
        self.answers_by_agent[agent_id].append(agent_answer)
        if snapshot_timestamp:
            self.snapshot_mappings[label] = {'type': 'answer', 'label': label, 'agent_id': agent_id, 'timestamp': snapshot_timestamp, 'iteration': self.current_iteration, 'round': self.get_agent_round(agent_id), 'path': self._make_snapshot_path('answer', agent_id, snapshot_timestamp)}
        context = {'label': label}
        self._add_event(EventType.NEW_ANSWER, agent_id, f'Provided answer {label}', context)

    def add_agent_vote(self, agent_id: str, vote_data: Dict[str, Any], snapshot_timestamp: Optional[str]=None):
        """Record when an agent votes.

        Args:
            agent_id: ID of the voting agent
            vote_data: Dictionary with vote information
            snapshot_timestamp: Timestamp of the filesystem snapshot (if any)
        """
        voted_for = vote_data.get('voted_for') or vote_data.get('agent_id', 'unknown')
        reason = vote_data.get('reason', '')
        voter_anon_id = self.get_anonymous_id(agent_id)
        voted_for_label = 'unknown'
        if voted_for not in self.agent_ids:
            logger.warning(f'Vote from {agent_id} for unknown agent {voted_for}')
        if voted_for in self.agent_ids:
            voted_agent_answers = self.answers_by_agent.get(voted_for, [])
            if voted_agent_answers:
                voted_for_label = voted_agent_answers[-1].label
        vote = AgentVote(voter_id=agent_id, voted_for=voted_for, voted_for_label=voted_for_label, voter_anon_id=voter_anon_id, reason=reason, timestamp=time.time(), available_answers=self.iteration_available_labels.copy())
        self.votes.append(vote)
        if snapshot_timestamp:
            agent_num = self._get_agent_number(agent_id) or 0
            vote_num = len([v for v in self.votes if v.voter_id == agent_id])
            vote_label = f'agent{agent_num}.vote{vote_num}'
            self.snapshot_mappings[vote_label] = {'type': 'vote', 'label': vote_label, 'agent_id': agent_id, 'timestamp': snapshot_timestamp, 'voted_for': voted_for, 'voted_for_label': voted_for_label, 'iteration': self.current_iteration, 'round': self.get_agent_round(agent_id), 'path': self._make_snapshot_path('vote', agent_id, snapshot_timestamp)}
        context = {'voted_for': voted_for, 'voted_for_label': voted_for_label, 'reason': reason, 'available_answers': self.iteration_available_labels.copy()}
        self._add_event(EventType.VOTE_CAST, agent_id, f'Voted for {voted_for_label}', context)

    def set_final_agent(self, agent_id: str, vote_summary: str, all_answers: Dict[str, str]):
        """Record when final agent is selected."""
        self.final_winner = agent_id
        answer_labels = []
        answers_with_labels = {}
        for aid, answer_content in all_answers.items():
            if aid in self.answers_by_agent and self.answers_by_agent[aid]:
                if self.answers_by_agent[aid]:
                    latest_answer = self.answers_by_agent[aid][-1]
                    answer_labels.append(latest_answer.label)
                    answers_with_labels[latest_answer.label] = answer_content
        self.final_context = {'vote_summary': vote_summary, 'all_answers': answer_labels, 'answers_for_context': answers_with_labels}
        self._add_event(EventType.FINAL_AGENT_SELECTED, agent_id, 'Selected as final presenter', self.final_context)

    def set_final_answer(self, agent_id: str, final_answer: str, snapshot_timestamp: Optional[str]=None):
        """Record the final answer presentation.

        Args:
            agent_id: ID of the agent
            final_answer: The final answer content
            snapshot_timestamp: Timestamp of the filesystem snapshot (if any)
        """
        final_answer_obj = AgentAnswer(agent_id=agent_id, content=final_answer, timestamp=time.time())
        agent_num = self._get_agent_number(agent_id)
        label = f'agent{agent_num}.final'
        final_answer_obj.label = label
        self.final_answers[agent_id] = final_answer_obj
        if snapshot_timestamp:
            self.snapshot_mappings[label] = {'type': 'final_answer', 'label': label, 'agent_id': agent_id, 'timestamp': snapshot_timestamp, 'iteration': self.current_iteration, 'round': self.get_agent_round(agent_id), 'path': self._make_snapshot_path('final_answer', agent_id, snapshot_timestamp)}
        context = {'label': label, **(self.final_context or {})}
        self._add_event(EventType.FINAL_ANSWER, agent_id, f'Presented final answer {label}', context)

    def start_final_round(self, selected_agent_id: str):
        """Start the final presentation round."""
        self.is_final_round = True
        final_round = self.max_round + 1
        self.agent_rounds[selected_agent_id] = final_round
        self.final_winner = selected_agent_id
        self.change_status(selected_agent_id, AgentStatus.STREAMING)
        self._add_event(EventType.FINAL_ROUND_START, selected_agent_id, f'Starting final presentation round {final_round}', {'round_type': 'final', 'final_round': final_round})

    def track_agent_action(self, agent_id: str, action_type, details: str=''):
        """Track any agent action using ActionType enum."""
        if action_type == ActionType.NEW_ANSWER:
            self.add_agent_answer(agent_id, details)
        elif action_type == ActionType.VOTE:
            pass
        else:
            event_type = ACTION_TO_EVENT.get(action_type)
            if event_type is None:
                raise ValueError(f'Unsupported ActionType: {action_type}')
            message = f'{action_type.value.upper()}: {details}' if details else action_type.value.upper()
            self._add_event(event_type, agent_id, message)

    def _add_event(self, event_type: EventType, agent_id: Optional[str], details: str, context: Optional[Dict[str, Any]]=None):
        """Internal method to add an event."""
        if context is None:
            context = {}
        context = context.copy()
        context['iteration'] = self.current_iteration
        if agent_id:
            context['round'] = self.get_agent_round(agent_id)
        else:
            context['round'] = self.max_round
        event = CoordinationEvent(timestamp=time.time(), event_type=event_type, agent_id=agent_id, details=details, context=context)
        self.events.append(event)

    def _end_session(self):
        """Mark the end of the coordination session."""
        self.end_time = time.time()
        duration = self.end_time - (self.start_time or self.end_time)
        self._add_event(EventType.SESSION_END, None, f'Session completed in {duration:.1f}s')

    @property
    def all_answers(self) -> Dict[str, str]:
        """Get all answers as a label->content dictionary."""
        result = {}
        for answers in self.answers_by_agent.values():
            for answer in answers:
                result[answer.label] = answer.content
        for answer in self.final_answers.values():
            result[answer.label] = answer.content
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary statistics."""
        duration = (self.end_time or time.time()) - (self.start_time or time.time())
        restart_count = len([e for e in self.events if e.event_type == EventType.RESTART_TRIGGERED])
        return {'duration': duration, 'total_events': len(self.events), 'total_restarts': restart_count, 'total_answers': sum((len(answers) for answers in self.answers_by_agent.values())), 'final_winner': self.final_winner, 'agent_count': len(self.agent_ids)}

    def save_coordination_logs(self, log_dir):
        """Save all coordination data and create timeline visualization.

        Args:
            log_dir: Directory to save logs
            format_style: "old", "new", or "both" (default)
        """
        try:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            events_file = log_dir / 'coordination_events.json'
            with open(events_file, 'w', encoding='utf-8') as f:
                events_data = [event.to_dict() for event in self.events]
                session_data = {'session_metadata': {'user_prompt': self.user_prompt, 'agent_ids': self.agent_ids, 'start_time': self.start_time, 'end_time': self.end_time, 'final_winner': self.final_winner}, 'events': events_data}
                json.dump(session_data, f, indent=2, default=str)
            if self.snapshot_mappings:
                snapshot_mappings_file = log_dir / 'snapshot_mappings.json'
                with open(snapshot_mappings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.snapshot_mappings, f, indent=2, default=str)
            try:
                self._generate_coordination_table(log_dir, session_data)
            except Exception as e:
                logger.warning(f'Warning: Could not generate coordination table: {e}', exc_info=True)
        except Exception as e:
            logger.warning(f'Failed to save coordination logs: {e}', exc_info=True)

    def _generate_coordination_table(self, log_dir, session_data):
        """Generate coordination table using the create_coordination_table.py module."""
        try:
            from massgen.frontend.displays.create_coordination_table import CoordinationTableBuilder
            builder = CoordinationTableBuilder(session_data)
            table_content = builder.generate_event_table()
            table_file = log_dir / 'coordination_table.txt'
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(table_content)
            logger.info(f'Coordination table generated at {table_file}')
        except Exception as e:
            logger.warning(f'Error generating coordination table: {e}', exc_info=True)

    def _get_agent_id_from_label(self, label: str) -> str:
        """Extract agent_id from a label like 'agent1.1' or 'agent2.final'."""
        import re
        match = re.match('agent(\\d+)', label)
        if match:
            agent_num = int(match.group(1))
            if 0 < agent_num <= len(self.agent_ids):
                return self.agent_ids[agent_num - 1]
        return 'unknown'

    def _get_agent_display_name(self, agent_id: str) -> str:
        """Get display name for agent (Agent1, Agent2, etc.)."""
        agent_num = self._get_agent_number(agent_id)
        return f'Agent{agent_num}' if agent_num else agent_id

def end_iteration(self, reason: str, details: Dict[str, Any]=None):
    """Record how an iteration ended."""
    context = {'iteration': self.current_iteration, 'end_reason': reason, 'available_answers': self.iteration_available_labels.copy()}
    if details:
        context.update(details)
    self._add_event(EventType.ITERATION_END, None, f'Iteration {self.current_iteration} ended: {reason}', context)

class ConfigBuilder:
    """Interactive configuration builder for MassGen."""

    @property
    def PROVIDERS(self) -> Dict[str, Dict]:
        """Generate provider configurations from the capabilities registry (single source of truth).

        This dynamically builds the PROVIDERS dict from massgen/backend/capabilities.py,
        ensuring consistency between config builder, documentation, and backend implementations.
        """
        providers = {}
        for backend_type, caps in BACKEND_CAPABILITIES.items():
            supports = list(caps.supported_capabilities)
            if caps.filesystem_support in ['native', 'mcp']:
                supports = [s if s != 'filesystem_native' else 'filesystem' for s in supports]
                if 'filesystem' not in supports:
                    supports.append('filesystem')
            providers[backend_type] = {'name': caps.provider_name, 'type': caps.backend_type, 'env_var': caps.env_var, 'models': caps.models, 'supports': supports}
        return providers
    USE_CASES = {'custom': {'name': 'Custom Configuration', 'description': 'Full flexibility - choose any agents, tools, and settings', 'recommended_agents': 1, 'recommended_tools': [], 'agent_types': 'all', 'notes': 'Choose any combination of agents and tools', 'info': None}, 'coding': {'name': 'Filesystem + Code Execution', 'description': 'Generate, test, and modify code with file operations', 'recommended_agents': 2, 'recommended_tools': ['code_execution', 'filesystem'], 'agent_types': 'all', 'notes': 'Claude Code recommended for best filesystem support', 'info': '[bold cyan]Features auto-configured for this preset:[/bold cyan]\n\n  [green]✓[/green] [bold]Filesystem Access[/bold]\n    • File read/write operations in isolated workspace\n    • Native filesystem (Claude Code) or MCP filesystem (other backends)\n\n  [green]✓[/green] [bold]Code Execution[/bold]\n    • OpenAI: Code Interpreter\n    • Claude/Gemini: Native code execution\n    • Isolated execution environment\n\n[dim]Use this for:[/dim] Code generation, refactoring, testing, or any task requiring file operations.'}, 'coding_docker': {'name': 'Filesystem + Code Execution (Docker)', 'description': 'Secure isolated code execution in Docker containers (requires setup)', 'recommended_agents': 2, 'recommended_tools': ['code_execution', 'filesystem'], 'agent_types': 'all', 'notes': '⚠️ SETUP REQUIRED: Docker Engine 28+, Python docker library, and image build (see massgen/docker/README.md)', 'info': '[bold cyan]Features auto-configured for this preset:[/bold cyan]\n\n  [green]✓[/green] [bold]Filesystem Access[/bold]\n    • File read/write operations\n\n  [green]✓[/green] [bold]Code Execution[/bold]\n    • OpenAI: Code Interpreter\n    • Claude/Gemini: Native code execution\n\n  [green]✓[/green] [bold]Docker Isolation[/bold]\n    • Fully isolated container execution via MCP\n    • Persistent package installations across turns\n    • Network and resource controls\n\n[yellow]⚠️  Requires Docker setup:[/yellow] Docker Engine 28.0.0+, docker Python library, and massgen-executor image\n[dim]Use this for:[/dim] Secure code execution when you need full isolation and persistent dependencies.'}, 'qa': {'name': 'Simple Q&A', 'description': 'Basic question answering with multiple perspectives', 'recommended_agents': 3, 'recommended_tools': [], 'agent_types': 'all', 'notes': 'Multiple agents provide diverse perspectives and cross-verification', 'info': None}, 'research': {'name': 'Research & Analysis', 'description': 'Multi-agent research with web search', 'recommended_agents': 3, 'recommended_tools': ['web_search'], 'agent_types': 'all', 'notes': 'Works best with web search enabled for current information', 'info': '[bold cyan]Features auto-configured for this preset:[/bold cyan]\n\n  [green]✓[/green] [bold]Web Search[/bold]\n    • Real-time internet search for current information\n    • Fact-checking and source verification\n    • Available for: OpenAI, Claude, Gemini, Grok\n\n  [green]✓[/green] [bold]Multi-Agent Collaboration[/bold]\n    • 3 agents recommended for diverse perspectives\n    • Cross-verification of facts and sources\n\n[dim]Use this for:[/dim] Research queries, current events, fact-checking, comparative analysis.'}, 'data_analysis': {'name': 'Data Analysis', 'description': 'Analyze data with code execution and visualizations', 'recommended_agents': 2, 'recommended_tools': ['code_execution', 'filesystem', 'image_understanding'], 'agent_types': 'all', 'notes': 'Code execution helps with data processing and visualization', 'info': '[bold cyan]Features auto-configured for this preset:[/bold cyan]\n\n  [green]✓[/green] [bold]Filesystem Access[/bold]\n    • Read/write data files (CSV, JSON, etc.)\n    • Save visualizations and reports\n\n  [green]✓[/green] [bold]Code Execution[/bold]\n    • Data processing and transformation\n    • Statistical analysis\n    • Visualization generation (matplotlib, seaborn, etc.)\n\n  [green]✓[/green] [bold]Image Understanding[/bold]\n    • Analyze charts, graphs, and visualizations\n    • Extract data from images and screenshots\n    • Available for: OpenAI, Claude Code, Gemini, Azure OpenAI\n\n[dim]Use this for:[/dim] Data analysis, chart interpretation, statistical processing, visualization.'}, 'multimodal': {'name': 'Multimodal Analysis', 'description': 'Analyze images, audio, and video content', 'recommended_agents': 2, 'recommended_tools': ['image_understanding', 'audio_understanding', 'video_understanding'], 'agent_types': 'all', 'notes': 'Different backends support different modalities', 'info': '[bold cyan]Features auto-configured for this preset:[/bold cyan]\n\n  [green]✓[/green] [bold]Image Understanding[/bold]\n    • Analyze images, screenshots, charts\n    • OCR and text extraction\n    • Available for: OpenAI, Claude Code, Gemini, Azure OpenAI\n\n  [green]✓[/green] [bold]Audio Understanding[/bold] [dim](where supported)[/dim]\n    • Transcribe and analyze audio\n    • Available for: Claude, ChatCompletion\n\n  [green]✓[/green] [bold]Video Understanding[/bold] [dim](where supported)[/dim]\n    • Analyze video content\n    • Available for: Claude, ChatCompletion, OpenAI\n\n[dim]Use this for:[/dim] Image analysis, screenshot interpretation, multimedia content analysis.'}}

    def __init__(self, default_mode: bool=False) -> None:
        """Initialize the configuration builder with default config.

        Args:
            default_mode: If True, save config to ~/.config/massgen/config.yaml by default
        """
        self.config = {'agents': [], 'ui': {'display_type': 'rich_terminal', 'logging_enabled': True}}
        self.orchestrator_config = {}
        self.default_mode = default_mode

    def show_banner(self) -> None:
        """Display welcome banner using Rich Panel."""
        console.clear()
        ascii_art = '[bold cyan]\n     ███╗   ███╗ █████╗ ███████╗███████╗ ██████╗ ███████╗███╗   ██╗\n     ████╗ ████║██╔══██╗██╔════╝██╔════╝██╔════╝ ██╔════╝████╗  ██║\n     ██╔████╔██║███████║███████╗███████╗██║  ███╗█████╗  ██╔██╗ ██║\n     ██║╚██╔╝██║██╔══██║╚════██║╚════██║██║   ██║██╔══╝  ██║╚██╗██║\n     ██║ ╚═╝ ██║██║  ██║███████║███████║╚██████╔╝███████╗██║ ╚████║\n     ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold cyan]\n\n     [dim]     🤖 🤖 🤖  →  💬 collaborate  →  🎯 winner  →  📢 final[/dim]\n'
        banner_content = f'{ascii_art}\n[bold bright_cyan]Interactive Configuration Builder[/bold bright_cyan]\n[dim]Create custom multi-agent configurations in minutes![/dim]'
        banner_panel = Panel(banner_content, border_style='bold cyan', padding=(0, 2), width=80)
        console.print(banner_panel)
        console.print()

    def _calculate_visible_length(self, text: str) -> int:
        """Calculate visible length of text, excluding Rich markup tags."""
        import re
        visible_text = re.sub('\\[/?[^\\]]+\\]', '', text)
        return len(visible_text)

    def _pad_with_markup(self, text: str, target_width: int) -> str:
        """Pad text to target width, accounting for Rich markup."""
        visible_len = self._calculate_visible_length(text)
        padding_needed = target_width - visible_len
        return text + (' ' * padding_needed if padding_needed > 0 else '')

    def _safe_prompt(self, prompt_func, error_msg: str='Selection cancelled'):
        """Wrapper for questionary prompts with graceful exit handling.

        Args:
            prompt_func: The questionary prompt function to call
            error_msg: Error message to show if cancelled

        Returns:
            The result from the prompt, or raises KeyboardInterrupt if cancelled

        Raises:
            KeyboardInterrupt: If user cancels (Ctrl+C or returns None)
        """
        try:
            result = prompt_func()
            if result is None:
                raise KeyboardInterrupt
            return result
        except (KeyboardInterrupt, EOFError):
            raise

    def detect_api_keys(self) -> Dict[str, bool]:
        """Detect available API keys from environment with error handling."""
        api_keys = {}
        try:
            for provider_id, provider_info in self.PROVIDERS.items():
                try:
                    if provider_id == 'claude_code':
                        api_keys[provider_id] = True
                        continue
                    env_var = provider_info.get('env_var')
                    if env_var:
                        api_keys[provider_id] = bool(os.getenv(env_var))
                    else:
                        api_keys[provider_id] = True
                except Exception as e:
                    console.print(f'[warning]⚠️  Could not check {provider_id}: {e}[/warning]')
                    api_keys[provider_id] = False
            return api_keys
        except Exception as e:
            console.print(f'[error]❌ Error detecting API keys: {e}[/error]')
            return {provider_id: False for provider_id in self.PROVIDERS.keys()}

    def interactive_api_key_setup(self) -> Dict[str, bool]:
        """Interactive API key setup wizard.

        Prompts user to enter API keys for providers and saves them to .env file.
        Follows CLI tool patterns (AWS CLI, Stripe CLI) for API key management.

        Returns:
            Updated api_keys dict after setup
        """
        try:
            console.print('\n[bold cyan]API Key Setup[/bold cyan]\n')
            console.print('[dim]Configure API keys for cloud AI providers.[/dim]')
            console.print('[dim](Alternatively, you can use local models like vLLM/Ollama - no keys needed)[/dim]\n')
            collected_keys = {}
            all_providers = [('openai', 'OpenAI', 'OPENAI_API_KEY'), ('anthropic', 'Anthropic (Claude)', 'ANTHROPIC_API_KEY'), ('gemini', 'Google Gemini', 'GOOGLE_API_KEY'), ('grok', 'xAI (Grok)', 'XAI_API_KEY'), ('azure_openai', 'Azure OpenAI', 'AZURE_OPENAI_API_KEY'), ('cerebras', 'Cerebras AI', 'CEREBRAS_API_KEY'), ('together', 'Together AI', 'TOGETHER_API_KEY'), ('fireworks', 'Fireworks AI', 'FIREWORKS_API_KEY'), ('groq', 'Groq', 'GROQ_API_KEY'), ('nebius', 'Nebius AI Studio', 'NEBIUS_API_KEY'), ('openrouter', 'OpenRouter', 'OPENROUTER_API_KEY'), ('zai', 'ZAI (Zhipu.ai)', 'ZAI_API_KEY'), ('moonshot', 'Kimi/Moonshot AI', 'MOONSHOT_API_KEY'), ('poe', 'POE', 'POE_API_KEY'), ('qwen', 'Qwen (Alibaba)', 'QWEN_API_KEY')]
            provider_choices = []
            for provider_id, name, env_var in all_providers:
                provider_choices.append(questionary.Choice(f'{name:<25} [{env_var}]', value=(provider_id, name, env_var), checked=False))
            console.print('[dim]Select which providers you want to configure (Space to toggle, Enter to confirm):[/dim]')
            console.print('[dim]Or skip all to use local models (vLLM, Ollama, etc.)[/dim]\n')
            selected_providers = questionary.checkbox('Select cloud providers to configure:', choices=provider_choices, style=questionary.Style([('selected', 'fg:cyan'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
            if selected_providers is None:
                raise KeyboardInterrupt
            if not selected_providers:
                console.print('\n[yellow]⚠️  No providers selected[/yellow]')
                console.print('[dim]Skipping API key setup. You can use local models (vLLM, Ollama) without API keys.[/dim]\n')
                return {}
            console.print(f'\n[cyan]Configuring {len(selected_providers)} provider(s)[/cyan]\n')
            for provider_id, name, env_var in selected_providers:
                console.print(f'[bold cyan]{name}[/bold cyan]')
                console.print(f'[dim]Environment variable: {env_var}[/dim]')
                api_key = Prompt.ask(f'Enter your {name} API key', password=True)
                if api_key is None:
                    raise KeyboardInterrupt
                if api_key and api_key.strip():
                    collected_keys[env_var] = api_key.strip()
                    console.print(f'✅ {name} API key saved')
                else:
                    console.print(f'[yellow]⚠️  Skipped {name} (empty input)[/yellow]')
                console.print()
            if not collected_keys:
                console.print('[error]❌ No API keys were configured.[/error]')
                console.print('[info]At least one API key is required to use MassGen.[/info]')
                return {}
            console.print('\n[bold cyan]Where to Save API Keys[/bold cyan]\n')
            console.print('[dim]Choose where to save your API keys:[/dim]\n')
            console.print('  [1] ~/.massgen/.env (recommended - available globally)')
            console.print('  [2] ./.env (current directory only)')
            console.print()
            save_location = Prompt.ask('[prompt]Choose location[/prompt]', choices=['1', '2'], default='1')
            if save_location is None:
                raise KeyboardInterrupt
            if save_location == '1':
                env_dir = Path.home() / '.massgen'
                env_dir.mkdir(parents=True, exist_ok=True)
                env_path = env_dir / '.env'
            else:
                env_path = Path('.env')
            existing_content = {}
            if env_path.exists():
                console.print(f'\n[yellow]⚠️  {env_path} already exists[/yellow]')
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and (not line.startswith('#')) and ('=' in line):
                                key, value = line.split('=', 1)
                                existing_content[key.strip()] = value.strip()
                except Exception as e:
                    console.print(f'[warning]⚠️  Could not read existing .env: {e}[/warning]')
                merge = Confirm.ask('Merge with existing keys (recommended)?', default=True)
                if merge is None:
                    raise KeyboardInterrupt
                if merge:
                    existing_content.update(collected_keys)
                    collected_keys = existing_content
                else:
                    pass
            try:
                with open(env_path, 'w') as f:
                    f.write('# MassGen API Keys\n')
                    f.write('# Generated by MassGen Interactive Setup\n\n')
                    for env_var, api_key in sorted(collected_keys.items()):
                        f.write(f'{env_var}={api_key}\n')
                console.print(f'\n✅ [success]API keys saved to: {env_path.absolute()}[/success]')
                if env_path == Path('.env'):
                    console.print('\n[yellow]⚠️  Security reminder:[/yellow]')
                    console.print('[yellow]   Add .env to your .gitignore to avoid committing API keys![/yellow]')
            except Exception as e:
                console.print(f'\n[error]❌ Failed to save .env file: {e}[/error]')
                return {}
            console.print('\n[dim]Reloading environment variables...[/dim]')
            load_dotenv(env_path, override=True)
            console.print('[dim]Verifying API keys...[/dim]\n')
            updated_api_keys = self.detect_api_keys()
            available_count = sum((1 for has_key in updated_api_keys.values() if has_key))
            console.print(f'[success]✅ {available_count} provider(s) available[/success]\n')
            return updated_api_keys
        except (KeyboardInterrupt, EOFError):
            console.print('\n\n[yellow]API key setup cancelled[/yellow]\n')
            return {}
        except Exception as e:
            console.print(f'\n[error]❌ Error during API key setup: {e}[/error]')
            return {}

    def show_available_providers(self, api_keys: Dict[str, bool]) -> None:
        """Display providers in a clean Rich table."""
        try:
            table = Table(title='[bold cyan]Available Providers[/bold cyan]', show_header=True, header_style='bold cyan', border_style='cyan', title_style='bold cyan', expand=False, padding=(0, 1))
            table.add_column('', justify='center', width=3, no_wrap=True)
            table.add_column('Provider', style='bold', min_width=20)
            table.add_column('Models', style='dim', min_width=25)
            table.add_column('Capabilities', style='dim cyan', min_width=20)
            for provider_id, provider_info in self.PROVIDERS.items():
                try:
                    has_key = api_keys.get(provider_id, False)
                    status = '✅' if has_key else '❌'
                    name = provider_info.get('name', 'Unknown')
                    models = provider_info.get('models', [])
                    models_display = ', '.join(models[:2])
                    if len(models) > 2:
                        models_display += f' +{len(models) - 2}'
                    caps = provider_info.get('supports', [])
                    cap_abbrev = {'web_search': 'web', 'code_execution': 'code', 'filesystem': 'files', 'image_understanding': 'img', 'reasoning': 'reason', 'mcp': 'mcp', 'audio_understanding': 'audio', 'video_understanding': 'video'}
                    caps_display = ', '.join([cap_abbrev.get(c, c[:4]) for c in caps[:3]])
                    if len(caps) > 3:
                        caps_display += f' +{len(caps) - 3}'
                    if provider_id == 'claude_code':
                        env_var = provider_info.get('env_var', '')
                        api_key_set = bool(os.getenv(env_var)) if env_var else False
                        if api_key_set:
                            table.add_row('✅', name, models_display, caps_display or 'basic')
                        else:
                            name_with_hint = f'{name}\n[dim cyan]⚠️ Requires `claude login` (no API key found)[/dim cyan]'
                            table.add_row('✅', name_with_hint, models_display, caps_display or 'basic')
                    elif has_key:
                        table.add_row(status, name, models_display, caps_display or 'basic')
                    else:
                        env_var = provider_info.get('env_var', '')
                        name_with_hint = f'{name}\n[yellow]Need: {env_var}[/yellow]'
                        table.add_row(status, name_with_hint, models_display, caps_display or 'basic')
                except Exception as e:
                    console.print(f'[warning]⚠️ Could not display {provider_id}: {e}[/warning]')
            console.print(table)
            console.print('\n💡 [dim]Tip: Set API keys in ~/.config/massgen/.env or ~/.massgen/.env[/dim]\n')
        except Exception as e:
            console.print(f'[error]❌ Error displaying providers: {e}[/error]')
            console.print('[info]Continuing with setup...[/info]\n')

    def select_use_case(self) -> str:
        """Let user select a use case template with error handling."""
        try:
            step_panel = Panel('[bold cyan]Step 1 of 4: Select Your Use Case[/bold cyan]\n\n[italic dim]All agent types are supported for every use case[/italic dim]', border_style='cyan', padding=(0, 2), width=80)
            console.print(step_panel)
            console.print()
            choices = []
            display_info = [('custom', '⚙️', 'Custom Configuration', 'Choose your own tools'), ('qa', '💬', 'Simple Q&A', 'Basic chat (no special tools)'), ('research', '🔍', 'Research & Analysis', 'Web search enabled'), ('coding', '💻', 'Code & Files', 'File ops + code execution'), ('coding_docker', '🐳', 'Code & Files (Docker)', 'File ops + isolated Docker execution'), ('data_analysis', '📊', 'Data Analysis', 'Files + code + image analysis'), ('multimodal', '🎨', 'Multimodal Analysis', 'Images, audio, video understanding')]
            for use_case_id, emoji, name, tools_hint in display_info:
                try:
                    use_case_info = self.USE_CASES.get(use_case_id)
                    if not use_case_info:
                        continue
                    display = f'{emoji}  {name:<30} [{tools_hint}]'
                    choices.append(questionary.Choice(title=display, value=use_case_id))
                except Exception as e:
                    console.print(f'[warning]⚠️  Could not display use case: {e}[/warning]')
            console.print('[dim]Choose a preset that matches your task. Each preset auto-configures tools and capabilities.[/dim]')
            console.print('[dim]You can customize everything in later steps.[/dim]\n')
            use_case_id = questionary.select('Select your use case:', choices=choices, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
            if use_case_id is None:
                raise KeyboardInterrupt
            selected_info = self.USE_CASES[use_case_id]
            console.print(f'\n✅ Selected: [green]{selected_info.get('name', use_case_id)}[/green]')
            console.print(f'   [dim]{selected_info.get('description', '')}[/dim]')
            console.print(f'   [dim cyan]→ Recommended: {selected_info.get('recommended_agents', 1)} agent(s)[/dim cyan]\n')
            use_case_details = self.USE_CASES[use_case_id]
            if use_case_details.get('info'):
                preset_panel = Panel(use_case_details['info'], border_style='cyan', title='[bold]Preset Configuration[/bold]', width=80, padding=(1, 2))
                console.print(preset_panel)
                console.print()
            return use_case_id
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            console.print(f'[error]❌ Error selecting use case: {e}[/error]')
            console.print("[info]Defaulting to 'qa' use case[/info]\n")
            return 'qa'

    def add_custom_mcp_server(self) -> Optional[Dict]:
        """Interactive flow to configure a custom MCP server.

        Returns:
            MCP server configuration dict, or None if cancelled
        """
        try:
            console.print('\n[bold cyan]Configure Custom MCP Server[/bold cyan]\n')
            name = questionary.text('Server name (identifier):', validate=lambda x: len(x) > 0).ask()
            if not name:
                return None
            server_type = questionary.select('Server type:', choices=[questionary.Choice('stdio (standard input/output)', value='stdio'), questionary.Choice('sse (server-sent events)', value='sse'), questionary.Choice('Custom type', value='custom')], default='stdio', style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
            if server_type == 'custom':
                server_type = questionary.text('Enter custom type:').ask()
            if not server_type:
                server_type = 'stdio'
            command = questionary.text('Command:', default='npx').ask()
            if not command:
                command = 'npx'
            args_str = questionary.text('Arguments (space-separated, or empty for none):', default='').ask()
            args = args_str.split() if args_str else []
            env_vars = {}
            if questionary.confirm('Add environment variables?', default=False).ask():
                console.print('\n[dim]Tip: Use ${VAR_NAME} to reference from .env file[/dim]\n')
                while True:
                    var_name = questionary.text('Environment variable name (or press Enter to finish):').ask()
                    if not var_name:
                        break
                    var_value = questionary.text(f'Value for {var_name}:', default=f'${{{var_name}}}').ask()
                    if var_value:
                        env_vars[var_name] = var_value
            mcp_server = {'name': name, 'type': server_type, 'command': command, 'args': args}
            if env_vars:
                mcp_server['env'] = env_vars
            console.print(f'\n✅ Custom MCP server configured: {name}\n')
            return mcp_server
        except (KeyboardInterrupt, EOFError):
            console.print('\n[info]Cancelled custom MCP configuration[/info]')
            return None
        except Exception as e:
            console.print(f'[error]❌ Error configuring custom MCP: {e}[/error]')
            return None

    def batch_create_agents(self, count: int, provider_id: str) -> List[Dict]:
        """Create multiple agents with the same provider.

        Args:
            count: Number of agents to create
            provider_id: Provider ID (e.g., 'openai', 'claude')

        Returns:
            List of agent configurations with default models
        """
        agents = []
        provider_info = self.PROVIDERS.get(provider_id, {})
        for i in range(count):
            agent_letter = chr(ord('a') + i)
            agent = {'id': f'agent_{agent_letter}', 'backend': {'type': provider_info.get('type', provider_id), 'model': provider_info.get('models', ['default'])[0]}}
            if provider_info.get('type') == 'claude_code':
                agent['backend']['cwd'] = f'workspace{i + 1}'
            agents.append(agent)
        return agents

    def clone_agent(self, source_agent: Dict, new_id: str) -> Dict:
        """Clone an agent's configuration with a new ID.

        Args:
            source_agent: Agent to clone
            new_id: New agent ID

        Returns:
            Cloned agent with updated ID and workspace (if applicable)
        """
        import copy
        cloned = copy.deepcopy(source_agent)
        cloned['id'] = new_id
        backend_type = cloned.get('backend', {}).get('type')
        if backend_type == 'claude_code' and 'cwd' in cloned.get('backend', {}):
            if '_' in new_id and len(new_id) > 0:
                agent_letter = new_id.split('_')[-1]
                if len(agent_letter) == 1 and agent_letter.isalpha():
                    agent_num = ord(agent_letter.lower()) - ord('a') + 1
                    cloned['backend']['cwd'] = f'workspace{agent_num}'
        return cloned

    def modify_cloned_agent(self, agent: Dict, agent_num: int) -> Dict:
        """Allow selective modification of a cloned agent.

        Args:
            agent: Cloned agent to modify
            agent_num: Agent number (1-indexed)

        Returns:
            Modified agent configuration
        """
        try:
            console.print(f'\n[bold cyan]Selective Modification: {agent['id']}[/bold cyan]')
            console.print('[dim]Choose which settings to modify (or press Enter to keep all)[/dim]\n')
            backend_type = agent.get('backend', {}).get('type')
            provider_info = None
            for pid, pinfo in self.PROVIDERS.items():
                if pinfo.get('type') == backend_type:
                    provider_info = pinfo
                    break
            if not provider_info:
                console.print('[warning]⚠️  Could not find provider info[/warning]')
                return agent
            modify_choices = questionary.checkbox('What would you like to modify? (Space to select, Enter to confirm)', choices=[questionary.Choice('Model', value='model'), questionary.Choice('Tools (web search, code execution)', value='tools'), questionary.Choice('Filesystem settings', value='filesystem'), questionary.Choice('MCP servers', value='mcp')], style=questionary.Style([('selected', 'fg:cyan'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
            if not modify_choices:
                console.print('✅ Keeping all cloned settings')
                return agent
            if 'model' in modify_choices:
                models = provider_info.get('models', [])
                if models:
                    current_model = agent['backend'].get('model')
                    model_choices = [questionary.Choice(f'{model}' + (' (current)' if model == current_model else ''), value=model) for model in models]
                    selected_model = questionary.select(f'Select model for {agent['id']}:', choices=model_choices, default=current_model, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                    if selected_model:
                        agent['backend']['model'] = selected_model
                        console.print(f'✅ Model changed to: {selected_model}')
            if 'tools' in modify_choices:
                supports = provider_info.get('supports', [])
                builtin_tools = [s for s in supports if s in ['web_search', 'code_execution', 'bash']]
                if builtin_tools:
                    current_tools = []
                    if agent['backend'].get('enable_web_search'):
                        current_tools.append('web_search')
                    if agent['backend'].get('enable_code_interpreter') or agent['backend'].get('enable_code_execution'):
                        current_tools.append('code_execution')
                    tool_choices = []
                    if 'web_search' in builtin_tools:
                        tool_choices.append(questionary.Choice('Web Search', value='web_search', checked='web_search' in current_tools))
                    if 'code_execution' in builtin_tools:
                        tool_choices.append(questionary.Choice('Code Execution', value='code_execution', checked='code_execution' in current_tools))
                    if 'bash' in builtin_tools:
                        tool_choices.append(questionary.Choice('Bash/Shell', value='bash', checked='bash' in current_tools))
                    if tool_choices:
                        selected_tools = questionary.checkbox('Enable built-in tools:', choices=tool_choices, style=questionary.Style([('selected', 'fg:cyan'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                        agent['backend'].pop('enable_web_search', None)
                        agent['backend'].pop('enable_code_interpreter', None)
                        agent['backend'].pop('enable_code_execution', None)
                        if selected_tools:
                            if 'web_search' in selected_tools:
                                if backend_type in ['openai', 'claude', 'gemini', 'grok', 'azure_openai']:
                                    agent['backend']['enable_web_search'] = True
                            if 'code_execution' in selected_tools:
                                if backend_type == 'openai' or backend_type == 'azure_openai':
                                    agent['backend']['enable_code_interpreter'] = True
                                elif backend_type in ['claude', 'gemini']:
                                    agent['backend']['enable_code_execution'] = True
                        console.print('✅ Tools updated')
            if 'filesystem' in modify_choices and 'filesystem' in provider_info.get('supports', []):
                enable_fs = questionary.confirm('Enable filesystem access?', default=bool(agent['backend'].get('cwd'))).ask()
                if enable_fs:
                    if backend_type == 'claude_code':
                        current_cwd = agent['backend'].get('cwd', f'workspace{agent_num}')
                        custom_cwd = questionary.text('Workspace directory:', default=current_cwd).ask()
                        if custom_cwd:
                            agent['backend']['cwd'] = custom_cwd
                    else:
                        agent['backend']['cwd'] = f'workspace{agent_num}'
                    console.print(f'✅ Filesystem enabled: {agent['backend']['cwd']}')
                else:
                    agent['backend'].pop('cwd', None)
                    console.print('✅ Filesystem disabled')
            if 'mcp' in modify_choices and 'mcp' in provider_info.get('supports', []):
                if questionary.confirm('Modify MCP servers?', default=False).ask():
                    current_mcps = agent['backend'].get('mcp_servers', [])
                    if current_mcps:
                        console.print(f'\n[dim]Current MCP servers: {len(current_mcps)}[/dim]')
                        for mcp in current_mcps:
                            console.print(f'  • {mcp.get('name', 'unnamed')}')
                    if questionary.confirm('Replace with new MCP servers?', default=False).ask():
                        mcp_servers = []
                        while True:
                            custom_server = self.add_custom_mcp_server()
                            if custom_server:
                                mcp_servers.append(custom_server)
                                if not questionary.confirm('Add another MCP server?', default=False).ask():
                                    break
                            else:
                                break
                        if mcp_servers:
                            agent['backend']['mcp_servers'] = mcp_servers
                            console.print(f'✅ MCP servers updated: {len(mcp_servers)} server(s)')
                        else:
                            agent['backend'].pop('mcp_servers', None)
                            console.print('✅ MCP servers removed')
            console.print(f'\n✅ [green]Agent {agent['id']} modified[/green]\n')
            return agent
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            console.print(f'[error]❌ Error modifying agent: {e}[/error]')
            return agent

    def apply_preset_to_agent(self, agent: Dict, use_case: str) -> Dict:
        """Auto-apply preset configuration to an agent.

        Args:
            agent: Agent configuration dict
            use_case: Use case ID for preset configuration

        Returns:
            Updated agent configuration with preset applied
        """
        if use_case == 'custom':
            return agent
        use_case_info = self.USE_CASES.get(use_case, {})
        recommended_tools = use_case_info.get('recommended_tools', [])
        backend_type = agent.get('backend', {}).get('type')
        provider_info = None
        for pid, pinfo in self.PROVIDERS.items():
            if pinfo.get('type') == backend_type:
                provider_info = pinfo
                break
        if not provider_info:
            return agent
        if 'filesystem' in recommended_tools and 'filesystem' in provider_info.get('supports', []):
            if not agent['backend'].get('cwd'):
                agent['backend']['cwd'] = 'workspace'
        if 'web_search' in recommended_tools:
            if backend_type in ['openai', 'claude', 'gemini', 'grok', 'azure_openai']:
                agent['backend']['enable_web_search'] = True
        if 'code_execution' in recommended_tools:
            if backend_type == 'openai' or backend_type == 'azure_openai':
                agent['backend']['enable_code_interpreter'] = True
            elif backend_type in ['claude', 'gemini']:
                agent['backend']['enable_code_execution'] = True
        if use_case == 'coding_docker' and agent['backend'].get('cwd'):
            agent['backend']['enable_mcp_command_line'] = True
            agent['backend']['command_line_execution_mode'] = 'docker'
        return agent

    def customize_agent(self, agent: Dict, agent_num: int, total_agents: int, use_case: Optional[str]=None) -> Dict:
        """Customize a single agent with Panel UI.

        Args:
            agent: Agent configuration dict
            agent_num: Agent number (1-indexed)
            total_agents: Total number of agents
            use_case: Use case ID for preset recommendations

        Returns:
            Updated agent configuration
        """
        try:
            backend_type = agent.get('backend', {}).get('type')
            provider_info = None
            for pid, pinfo in self.PROVIDERS.items():
                if pinfo.get('type') == backend_type:
                    provider_info = pinfo
                    break
            if not provider_info:
                console.print(f'[warning]⚠️  Could not find provider for {backend_type}[/warning]')
                return agent
            panel_content = []
            panel_content.append(f'[bold]Agent {agent_num} of {total_agents}: {agent['id']}[/bold]\n')
            models = provider_info.get('models', [])
            if models:
                current_model = agent['backend'].get('model')
                panel_content.append(f'[cyan]Current model:[/cyan] {current_model}')
                console.print(Panel('\n'.join(panel_content), border_style='cyan', width=80))
                console.print()
                model_choices = [questionary.Choice(f'{model}' + (' (current)' if model == current_model else ''), value=model) for model in models]
                selected_model = questionary.select(f'Select model for {agent['id']}:', choices=model_choices, default=current_model, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                if selected_model:
                    agent['backend']['model'] = selected_model
                    console.print(f'\n✓ Model set to {selected_model}')
                    if backend_type in ['openai', 'azure_openai']:
                        console.print('\n[dim]Configure text verbosity:[/dim]')
                        console.print('[dim]  • low: Concise responses[/dim]')
                        console.print('[dim]  • medium: Balanced detail (recommended)[/dim]')
                        console.print('[dim]  • high: Detailed, verbose responses[/dim]\n')
                        verbosity_choice = questionary.select('Text verbosity level:', choices=[questionary.Choice('Low (concise)', value='low'), questionary.Choice('Medium (recommended)', value='medium'), questionary.Choice('High (detailed)', value='high')], default='medium', style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                        agent['backend']['text'] = {'verbosity': verbosity_choice if verbosity_choice else 'medium'}
                        console.print(f'✓ Text verbosity set to: {(verbosity_choice if verbosity_choice else 'medium')}\n')
                    if selected_model in ['gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'o4', 'o4-mini']:
                        console.print('[dim]This model supports extended reasoning. Configure reasoning effort:[/dim]')
                        console.print('[dim]  • high: Maximum reasoning depth (slower, more thorough)[/dim]')
                        console.print('[dim]  • medium: Balanced reasoning (recommended)[/dim]')
                        console.print('[dim]  • low: Faster responses with basic reasoning[/dim]\n')
                        if selected_model in ['gpt-5', 'o4']:
                            default_effort = 'medium'
                        elif selected_model in ['gpt-5-mini', 'o4-mini']:
                            default_effort = 'medium'
                        else:
                            default_effort = 'low'
                        effort_choice = questionary.select('Reasoning effort level:', choices=[questionary.Choice('High (maximum depth)', value='high'), questionary.Choice('Medium (balanced - recommended)', value='medium'), questionary.Choice('Low (faster)', value='low')], default=default_effort, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                        agent['backend']['reasoning'] = {'effort': effort_choice if effort_choice else default_effort, 'summary': 'auto'}
                        console.print(f'✓ Reasoning effort set to: {(effort_choice if effort_choice else default_effort)}\n')
            else:
                console.print(Panel('\n'.join(panel_content), border_style='cyan', width=80))
            if 'filesystem' in provider_info.get('supports', []):
                console.print()
                caps = get_capabilities(backend_type)
                fs_type = caps.filesystem_support if caps else 'mcp'
                if backend_type == 'claude_code':
                    current_cwd = agent['backend'].get('cwd', 'workspace')
                    console.print('[dim]Claude Code has native filesystem access (always enabled)[/dim]')
                    console.print(f'[dim]Current workspace: {current_cwd}[/dim]')
                    if questionary.confirm('Customize workspace directory?', default=False).ask():
                        custom_cwd = questionary.text('Enter workspace directory:', default=current_cwd).ask()
                        if custom_cwd:
                            agent['backend']['cwd'] = custom_cwd
                    console.print(f'✅ Filesystem access: {agent['backend']['cwd']} (native)')
                    console.print()
                    console.print('[dim]Claude Code bash execution mode:[/dim]')
                    console.print('[dim]  • local: Run bash commands directly on your machine (default)[/dim]')
                    console.print('[dim]  • docker: Run bash in isolated Docker container (requires Docker setup)[/dim]')
                    enable_docker = questionary.confirm('Enable Docker bash execution? (requires Docker setup)', default=use_case == 'coding_docker').ask()
                    if enable_docker:
                        agent['backend']['enable_mcp_command_line'] = True
                        agent['backend']['command_line_execution_mode'] = 'docker'
                        console.print('🐳 Docker bash execution enabled')
                    else:
                        console.print('💻 Local bash execution enabled (default)')
                else:
                    filesystem_recommended = False
                    if use_case and use_case != 'custom':
                        use_case_info = self.USE_CASES.get(use_case, {})
                        filesystem_recommended = 'filesystem' in use_case_info.get('recommended_tools', [])
                    if fs_type == 'native':
                        console.print('[dim]This backend has native filesystem support[/dim]')
                    else:
                        console.print('[dim]This backend supports filesystem operations via MCP[/dim]')
                    if filesystem_recommended:
                        console.print('[dim]💡 Filesystem access recommended for this preset[/dim]')
                    enable_filesystem = filesystem_recommended
                    if not filesystem_recommended:
                        enable_filesystem = questionary.confirm('Enable filesystem access for this agent?', default=True).ask()
                    if enable_filesystem:
                        if not agent['backend'].get('cwd'):
                            agent['backend']['cwd'] = f'workspace{agent_num}'
                        console.print(f'✅ Filesystem access enabled (via MCP): {agent['backend']['cwd']}')
                        if use_case == 'coding_docker':
                            agent['backend']['enable_mcp_command_line'] = True
                            agent['backend']['command_line_execution_mode'] = 'docker'
                            console.print('🐳 Docker execution mode enabled for isolated code execution')
            if backend_type != 'claude_code':
                supports = provider_info.get('supports', [])
                builtin_tools = [s for s in supports if s in ['web_search', 'code_execution', 'bash']]
                recommended_tools = []
                if use_case:
                    use_case_info = self.USE_CASES.get(use_case, {})
                    recommended_tools = use_case_info.get('recommended_tools', [])
                if builtin_tools:
                    console.print()
                    if recommended_tools and use_case != 'custom':
                        console.print(f'[dim]💡 Preset recommendation: {', '.join(recommended_tools)}[/dim]')
                    tool_choices = []
                    if 'web_search' in builtin_tools:
                        tool_choices.append(questionary.Choice('Web Search', value='web_search', checked='web_search' in recommended_tools))
                    if 'code_execution' in builtin_tools:
                        tool_choices.append(questionary.Choice('Code Execution', value='code_execution', checked='code_execution' in recommended_tools))
                    if 'bash' in builtin_tools:
                        tool_choices.append(questionary.Choice('Bash/Shell', value='bash', checked='bash' in recommended_tools))
                    if tool_choices:
                        selected_tools = questionary.checkbox('Enable built-in tools for this agent (Space to select, Enter to confirm):', choices=tool_choices, style=questionary.Style([('selected', 'fg:cyan'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                        if selected_tools:
                            if 'web_search' in selected_tools:
                                if backend_type in ['openai', 'claude', 'gemini', 'grok', 'azure_openai']:
                                    agent['backend']['enable_web_search'] = True
                            if 'code_execution' in selected_tools:
                                if backend_type == 'openai' or backend_type == 'azure_openai':
                                    agent['backend']['enable_code_interpreter'] = True
                                elif backend_type in ['claude', 'gemini']:
                                    agent['backend']['enable_code_execution'] = True
                            console.print(f'✅ Enabled {len(selected_tools)} built-in tool(s)')
            supports = provider_info.get('supports', [])
            multimodal_caps = [s for s in supports if s in ['image_understanding', 'audio_understanding', 'video_understanding', 'reasoning']]
            if multimodal_caps:
                console.print()
                console.print('[dim]📷 This backend also supports (no configuration needed):[/dim]')
                if 'image_understanding' in multimodal_caps:
                    console.print('[dim]  • Image understanding (analyze images, charts, screenshots)[/dim]')
                if 'audio_understanding' in multimodal_caps:
                    console.print('[dim]  • Audio understanding (transcribe and analyze audio)[/dim]')
                if 'video_understanding' in multimodal_caps:
                    console.print('[dim]  • Video understanding (analyze video content)[/dim]')
                if 'reasoning' in multimodal_caps:
                    console.print('[dim]  • Extended reasoning (deep thinking for complex problems)[/dim]')
            generation_caps = [s for s in supports if s in ['image_generation', 'audio_generation', 'video_generation']]
            if generation_caps:
                console.print()
                console.print('[cyan]Optional generation capabilities (requires explicit enablement):[/cyan]')
                gen_choices = []
                if 'image_generation' in generation_caps:
                    gen_choices.append(questionary.Choice('Image Generation (DALL-E, etc.)', value='image_generation', checked=False))
                if 'audio_generation' in generation_caps:
                    gen_choices.append(questionary.Choice('Audio Generation (TTS, music, etc.)', value='audio_generation', checked=False))
                if 'video_generation' in generation_caps:
                    gen_choices.append(questionary.Choice('Video Generation (Sora, etc.)', value='video_generation', checked=False))
                if gen_choices:
                    selected_gen = questionary.checkbox('Enable generation capabilities (Space to select, Enter to confirm):', choices=gen_choices, style=questionary.Style([('selected', 'fg:cyan'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                    if selected_gen:
                        if 'image_generation' in selected_gen:
                            agent['backend']['enable_image_generation'] = True
                        if 'audio_generation' in selected_gen:
                            agent['backend']['enable_audio_generation'] = True
                        if 'video_generation' in selected_gen:
                            agent['backend']['enable_video_generation'] = True
                        console.print(f'✅ Enabled {len(selected_gen)} generation capability(ies)')
            if 'mcp' in provider_info.get('supports', []):
                console.print()
                console.print('[dim]MCP servers are external integrations. Filesystem is handled internally (configured above).[/dim]')
                if questionary.confirm('Add custom MCP servers?', default=False).ask():
                    mcp_servers = []
                    while True:
                        custom_server = self.add_custom_mcp_server()
                        if custom_server:
                            mcp_servers.append(custom_server)
                            if not questionary.confirm('Add another custom MCP server?', default=False).ask():
                                break
                        else:
                            break
                    if mcp_servers:
                        agent['backend']['mcp_servers'] = mcp_servers
                        console.print(f'\n✅ Total: {len(mcp_servers)} MCP server(s) configured for this agent\n')
            console.print(f'✅ [green]Agent {agent_num} configured[/green]\n')
            return agent
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            console.print(f'[error]❌ Error customizing agent: {e}[/error]')
            return agent

    def configure_agents(self, use_case: str, api_keys: Dict[str, bool]) -> List[Dict]:
        """Configure agents with batch creation and individual customization."""
        try:
            step_panel = Panel('[bold cyan]Step 2 of 4: Agent Setup[/bold cyan]\n\n[italic dim]Choose any provider(s) - all types work for your selected use case[/italic dim]', border_style='cyan', padding=(0, 2), width=80)
            console.print(step_panel)
            console.print()
            self.show_available_providers(api_keys)
            use_case_info = self.USE_CASES.get(use_case, {})
            recommended = use_case_info.get('recommended_agents', 1)
            console.print(f'  💡 [dim]Recommended for this use case: {recommended} agent(s)[/dim]')
            console.print()
            num_choices = [questionary.Choice('1 agent', value=1), questionary.Choice('2 agents', value=2), questionary.Choice('3 agents (recommended for diverse perspectives)', value=3), questionary.Choice('4 agents', value=4), questionary.Choice('5 agents', value=5), questionary.Choice('Custom number', value='custom')]
            default_choice = None
            for choice in num_choices:
                if choice.value == recommended:
                    default_choice = choice.value
                    break
            try:
                num_agents_choice = questionary.select('How many agents?', choices=num_choices, default=default_choice, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                if num_agents_choice is None:
                    raise KeyboardInterrupt
                if num_agents_choice == 'custom':
                    num_agents_text = questionary.text('Enter number of agents:', validate=lambda x: x.isdigit() and int(x) > 0).ask()
                    if num_agents_text is None:
                        raise KeyboardInterrupt
                    num_agents = int(num_agents_text) if num_agents_text else recommended
                else:
                    num_agents = num_agents_choice
            except Exception as e:
                console.print(f'[warning]⚠️  Error with selection: {e}[/warning]')
                console.print(f'[info]Using recommended: {recommended} agents[/info]')
                num_agents = recommended
            if num_agents < 1:
                console.print('[warning]⚠️  Number of agents must be at least 1. Setting to 1.[/warning]')
                num_agents = 1
            available_providers = [p for p, has_key in api_keys.items() if has_key]
            if not available_providers:
                console.print('[error]❌ No providers with API keys found. Please set at least one API key.[/error]')
                raise ValueError('No providers available')
            agents = []
            if num_agents == 1:
                console.print()
                provider_choices = [questionary.Choice(self.PROVIDERS.get(pid, {}).get('name', pid), value=pid) for pid in available_providers]
                provider_id = questionary.select('Select provider:', choices=provider_choices, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                if provider_id is None:
                    raise KeyboardInterrupt
                agents = self.batch_create_agents(1, provider_id)
                provider_name = self.PROVIDERS.get(provider_id, {}).get('name', provider_id)
                console.print()
                console.print(f'  ✅ Created 1 {provider_name} agent')
                console.print()
            else:
                console.print()
                setup_mode = questionary.select('Setup mode:', choices=[questionary.Choice('Same provider for all agents (quick setup)', value='same'), questionary.Choice('Mix different providers (advanced)', value='mix')], style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                if setup_mode is None:
                    raise KeyboardInterrupt
                if setup_mode == 'same':
                    console.print()
                    provider_choices = [questionary.Choice(self.PROVIDERS.get(pid, {}).get('name', pid), value=pid) for pid in available_providers]
                    provider_id = questionary.select('Select provider:', choices=provider_choices, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                    if provider_id is None:
                        raise KeyboardInterrupt
                    agents = self.batch_create_agents(num_agents, provider_id)
                    provider_name = self.PROVIDERS.get(provider_id, {}).get('name', provider_id)
                    console.print()
                    console.print(f'  ✅ Created {num_agents} {provider_name} agents')
                    console.print()
                else:
                    console.print()
                    console.print('[yellow]  💡 Advanced mode: Configure each agent individually[/yellow]')
                    console.print()
                    for i in range(num_agents):
                        try:
                            console.print(f'[bold cyan]Agent {i + 1} of {num_agents}:[/bold cyan]')
                            provider_choices = [questionary.Choice(self.PROVIDERS.get(pid, {}).get('name', pid), value=pid) for pid in available_providers]
                            provider_id = questionary.select(f'Select provider for agent {i + 1}:', choices=provider_choices, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                            if not provider_id:
                                provider_id = available_providers[0]
                            agent_batch = self.batch_create_agents(1, provider_id)
                            agents.extend(agent_batch)
                            provider_name = self.PROVIDERS.get(provider_id, {}).get('name', provider_id)
                            console.print(f'✅ Agent {i + 1} created: {provider_name}\n')
                        except (KeyboardInterrupt, EOFError):
                            raise
                        except Exception as e:
                            console.print(f'[error]❌ Error configuring agent {i + 1}: {e}[/error]')
                            console.print('[info]Skipping this agent...[/info]')
            if not agents:
                console.print('[error]❌ No agents were successfully configured.[/error]')
                raise ValueError('Failed to configure any agents')
            step_panel = Panel('[bold cyan]Step 3 of 4: Agent Configuration[/bold cyan]', border_style='cyan', padding=(0, 2), width=80)
            console.print(step_panel)
            console.print()
            if use_case != 'custom':
                use_case_info = self.USE_CASES.get(use_case, {})
                recommended_tools = use_case_info.get('recommended_tools', [])
                console.print(f'  [bold green]✓ Preset Selected:[/bold green] {use_case_info.get('name', use_case)}')
                console.print(f'  [dim]{use_case_info.get('description', '')}[/dim]')
                console.print()
                if recommended_tools:
                    console.print('  [cyan]This preset will auto-configure:[/cyan]')
                    for tool in recommended_tools:
                        tool_display = {'filesystem': '📁 Filesystem access', 'code_execution': '💻 Code execution', 'web_search': '🔍 Web search', 'mcp': '🔌 MCP servers'}.get(tool, tool)
                        console.print(f'    • {tool_display}')
                    if use_case == 'coding_docker':
                        console.print('    • 🐳 Docker isolated execution')
                    console.print()
                console.print('  [cyan]Select models for your agents:[/cyan]')
                console.print()
                for i, agent in enumerate(agents, 1):
                    backend_type = agent.get('backend', {}).get('type')
                    provider_info = None
                    for pid, pinfo in self.PROVIDERS.items():
                        if pinfo.get('type') == backend_type:
                            provider_info = pinfo
                            break
                    if provider_info:
                        models = provider_info.get('models', [])
                        if models and len(models) > 1:
                            current_model = agent['backend'].get('model')
                            console.print(f'[bold]Agent {i} ({agent['id']}) - {provider_info.get('name')}:[/bold]')
                            model_choices = [questionary.Choice(f'{model}' + (' (default)' if model == current_model else ''), value=model) for model in models]
                            selected_model = questionary.select('Select model:', choices=model_choices, default=current_model, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                            if selected_model:
                                agent['backend']['model'] = selected_model
                                console.print(f'  ✓ {selected_model}')
                                if backend_type in ['openai', 'azure_openai']:
                                    console.print('\n  [dim]Configure text verbosity:[/dim]')
                                    console.print('  [dim]• low: Concise responses[/dim]')
                                    console.print('  [dim]• medium: Balanced detail (recommended)[/dim]')
                                    console.print('  [dim]• high: Detailed, verbose responses[/dim]\n')
                                    verbosity_choice = questionary.select('  Text verbosity:', choices=[questionary.Choice('Low (concise)', value='low'), questionary.Choice('Medium (recommended)', value='medium'), questionary.Choice('High (detailed)', value='high')], default='medium', style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                                    agent['backend']['text'] = {'verbosity': verbosity_choice if verbosity_choice else 'medium'}
                                    console.print(f'  ✓ Text verbosity: {(verbosity_choice if verbosity_choice else 'medium')}\n')
                                if selected_model in ['gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'o4', 'o4-mini']:
                                    console.print('  [dim]Configure reasoning effort:[/dim]')
                                    console.print('  [dim]• high: Maximum depth (slower)[/dim]')
                                    console.print('  [dim]• medium: Balanced (recommended)[/dim]')
                                    console.print('  [dim]• low: Faster responses[/dim]\n')
                                    if selected_model in ['gpt-5', 'o4']:
                                        default_effort = 'medium'
                                    elif selected_model in ['gpt-5-mini', 'o4-mini']:
                                        default_effort = 'medium'
                                    else:
                                        default_effort = 'low'
                                    effort_choice = questionary.select('  Reasoning effort:', choices=[questionary.Choice('High', value='high'), questionary.Choice('Medium (recommended)', value='medium'), questionary.Choice('Low', value='low')], default=default_effort, style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                                    agent['backend']['reasoning'] = {'effort': effort_choice if effort_choice else default_effort, 'summary': 'auto'}
                                    console.print(f'  ✓ Reasoning effort: {(effort_choice if effort_choice else default_effort)}\n')
                console.print()
                console.print('  [cyan]Applying preset configuration to all agents...[/cyan]')
                for i, agent in enumerate(agents):
                    agents[i] = self.apply_preset_to_agent(agent, use_case)
                console.print(f'  [green]✅ {len(agents)} agent(s) configured with preset[/green]')
                console.print()
                customize_choice = Confirm.ask('\n  [prompt]Further customize agent settings (advanced)?[/prompt]', default=False)
                if customize_choice is None:
                    raise KeyboardInterrupt
                if customize_choice:
                    console.print()
                    console.print('  [cyan]Entering advanced customization...[/cyan]')
                    console.print()
                    for i, agent in enumerate(agents, 1):
                        if i > 1:
                            console.print(f'\n[bold cyan]Agent {i} of {len(agents)}: {agent['id']}[/bold cyan]')
                            clone_choice = questionary.select('How would you like to configure this agent?', choices=[questionary.Choice(f"📋 Copy agent_{chr(ord('a') + i - 2)}'s configuration", value='clone'), questionary.Choice(f'✏️  Copy agent_{chr(ord('a') + i - 2)} and modify specific settings', value='clone_modify'), questionary.Choice('⚙️  Configure from scratch', value='scratch')], style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                            if clone_choice == 'clone':
                                source_agent = agents[i - 2]
                                agent = self.clone_agent(source_agent, agent['id'])
                                agents[i - 1] = agent
                                console.print(f'✅ Cloned configuration from agent_{chr(ord('a') + i - 2)}')
                                console.print()
                                continue
                            elif clone_choice == 'clone_modify':
                                source_agent = agents[i - 2]
                                agent = self.clone_agent(source_agent, agent['id'])
                                agent = self.modify_cloned_agent(agent, i)
                                agents[i - 1] = agent
                                continue
                        agent = self.customize_agent(agent, i, len(agents), use_case=use_case)
                        agents[i - 1] = agent
            else:
                console.print('  [cyan]Custom configuration - configuring each agent...[/cyan]')
                console.print()
                for i, agent in enumerate(agents, 1):
                    if i > 1:
                        console.print(f'\n[bold cyan]Agent {i} of {len(agents)}: {agent['id']}[/bold cyan]')
                        clone_choice = questionary.select('How would you like to configure this agent?', choices=[questionary.Choice(f"📋 Copy agent_{chr(ord('a') + i - 2)}'s configuration", value='clone'), questionary.Choice(f'✏️  Copy agent_{chr(ord('a') + i - 2)} and modify specific settings', value='clone_modify'), questionary.Choice('⚙️  Configure from scratch', value='scratch')], style=questionary.Style([('selected', 'fg:cyan bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan')]), use_arrow_keys=True).ask()
                        if clone_choice == 'clone':
                            source_agent = agents[i - 2]
                            agent = self.clone_agent(source_agent, agent['id'])
                            agents[i - 1] = agent
                            console.print(f'✅ Cloned configuration from agent_{chr(ord('a') + i - 2)}')
                            console.print()
                            continue
                        elif clone_choice == 'clone_modify':
                            source_agent = agents[i - 2]
                            agent = self.clone_agent(source_agent, agent['id'])
                            agent = self.modify_cloned_agent(agent, i)
                            agents[i - 1] = agent
                            continue
                    agent = self.customize_agent(agent, i, len(agents), use_case=use_case)
                    agents[i - 1] = agent
            return agents
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            console.print(f'[error]❌ Fatal error in agent configuration: {e}[/error]')
            raise

    def configure_tools(self, use_case: str, agents: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Configure orchestrator-level settings (tools are configured per-agent)."""
        try:
            step_panel = Panel('[bold cyan]Step 4 of 4: Orchestrator Configuration[/bold cyan]\n\n[dim]Note: Tools and capabilities were configured per-agent in the previous step.[/dim]', border_style='cyan', padding=(0, 2), width=80)
            console.print(step_panel)
            console.print()
            orchestrator_config = {}
            has_filesystem = any((a.get('backend', {}).get('cwd') or a.get('backend', {}).get('type') == 'claude_code' for a in agents))
            if has_filesystem:
                console.print('  [cyan]Filesystem-enabled agents detected[/cyan]')
                console.print()
                orchestrator_config['snapshot_storage'] = 'snapshots'
                orchestrator_config['agent_temporary_workspace'] = 'temp_workspaces'
                console.print('  [dim]Context paths give agents access to your project files.[/dim]')
                console.print('  [dim]Paths can be absolute or relative (resolved against current directory).[/dim]')
                console.print('  [dim]Note: During coordination, all context paths are read-only.[/dim]')
                console.print('  [dim]      Write permission applies only to the final agent.[/dim]')
                console.print()
                add_paths = Confirm.ask('[prompt]Add context paths?[/prompt]', default=False)
                if add_paths is None:
                    raise KeyboardInterrupt
                if add_paths:
                    context_paths = []
                    while True:
                        path = Prompt.ask('[prompt]Enter directory or file path (or press Enter to finish)[/prompt]')
                        if path is None:
                            raise KeyboardInterrupt
                        if not path:
                            break
                        permission = Prompt.ask('[prompt]Permission (write means final agent can modify)[/prompt]', choices=['read', 'write'], default='write')
                        if permission is None:
                            raise KeyboardInterrupt
                        context_path_entry = {'path': path, 'permission': permission}
                        if permission == 'write':
                            console.print('[dim]Protected paths are files/directories immune from modification[/dim]')
                            if Confirm.ask('[prompt]Add protected paths (e.g., .env, config.json)?[/prompt]', default=False):
                                protected_paths = []
                                console.print('[dim]Enter paths relative to the context path (or press Enter to finish)[/dim]')
                                while True:
                                    protected_path = Prompt.ask('[prompt]Protected path[/prompt]')
                                    if not protected_path:
                                        break
                                    protected_paths.append(protected_path)
                                    console.print(f'🔒 Protected: {protected_path}')
                                if protected_paths:
                                    context_path_entry['protected_paths'] = protected_paths
                        context_paths.append(context_path_entry)
                        console.print(f'✅ Added: {path} ({permission})')
                    if context_paths:
                        orchestrator_config['context_paths'] = context_paths
            if not orchestrator_config:
                orchestrator_config = {}
            orchestrator_config['session_storage'] = 'sessions'
            console.print()
            console.print('  ✅ Multi-turn sessions enabled (supports persistent conversations with memory)')
            has_mcp = any((a.get('backend', {}).get('mcp_servers') for a in agents))
            if has_mcp:
                console.print()
                console.print('  [dim]Planning Mode: Prevents MCP tool execution during coordination[/dim]')
                console.print('  [dim](for irreversible actions like Discord/Twitter posts)[/dim]')
                console.print()
                planning_choice = Confirm.ask('  [prompt]Enable planning mode for MCP tools?[/prompt]', default=False)
                if planning_choice is None:
                    raise KeyboardInterrupt
                if planning_choice:
                    orchestrator_config['coordination'] = {'enable_planning_mode': True}
                    console.print()
                    console.print('  ✅ Planning mode enabled - MCP tools will plan without executing during coordination')
            return (agents, orchestrator_config)
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            console.print(f'[error]❌ Error configuring orchestrator: {e}[/error]')
            console.print('[info]Returning agents with basic configuration...[/info]')
            return (agents, {})

    def review_and_save(self, agents: List[Dict], orchestrator_config: Dict) -> Optional[str]:
        """Review configuration and save to file with error handling."""
        try:
            review_panel = Panel('[bold green]✅  Review & Save Configuration[/bold green]', border_style='green', padding=(0, 2), width=80)
            console.print(review_panel)
            console.print()
            self.config['agents'] = agents
            if orchestrator_config:
                self.config['orchestrator'] = orchestrator_config
            try:
                yaml_content = yaml.dump(self.config, default_flow_style=False, sort_keys=False)
                config_panel = Panel(yaml_content, title='[bold cyan]Generated Configuration[/bold cyan]', border_style='green', padding=(1, 2), width=min(console.width - 4, 100))
                console.print(config_panel)
            except Exception as e:
                console.print(f'[warning]⚠️  Could not preview YAML: {e}[/warning]')
                console.print('[info]Proceeding with save...[/info]')
            save_choice = Confirm.ask('\n[prompt]Save this configuration?[/prompt]', default=True)
            if save_choice is None:
                raise KeyboardInterrupt
            if not save_choice:
                console.print('[info]Configuration not saved.[/info]')
                return None
            if self.default_mode:
                config_dir = Path.home() / '.config/massgen'
                config_dir.mkdir(parents=True, exist_ok=True)
                filepath = config_dir / 'config.yaml'
                if filepath.exists():
                    if not Confirm.ask('\n[yellow]⚠️  Default config already exists. Overwrite?[/yellow]', default=True):
                        console.print('[info]Configuration not saved.[/info]')
                        return None
                with open(filepath, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                console.print(f'\n✅ [success]Configuration saved to: {filepath}[/success]')
                return str(filepath)
            default_name = 'my_massgen_config.yaml'
            filename = None
            console.print('\nWhere would you like to save the config?')
            console.print('  [1] Current directory (default)')
            console.print('  [2] MassGen config directory (~/.config/massgen/agents/)')
            save_location = Prompt.ask('[prompt]Choose location[/prompt]', choices=['1', '2'], default='1')
            if save_location == '2':
                agents_dir = Path.home() / '.config/massgen/agents'
                agents_dir.mkdir(parents=True, exist_ok=True)
                default_name = str(agents_dir / 'my_massgen_config.yaml')
            while True:
                try:
                    if filename is None:
                        filename = Prompt.ask('[prompt]Config filename[/prompt]', default=default_name)
                    if not filename:
                        console.print('[warning]⚠️  Empty filename, using default.[/warning]')
                        filename = default_name
                    if not filename.endswith('.yaml'):
                        filename += '.yaml'
                    filepath = Path(filename)
                    if filepath.exists():
                        console.print(f"\n[yellow]⚠️  File '{filename}' already exists![/yellow]")
                        console.print('\nWhat would you like to do?')
                        console.print('  1. Rename (enter a new filename)')
                        console.print('  2. Overwrite (replace existing file)')
                        console.print("  3. Cancel (don't save)")
                        choice = Prompt.ask('\n[prompt]Choose an option[/prompt]', choices=['1', '2', '3'], default='1')
                        if choice == '1':
                            filename = Prompt.ask('[prompt]Enter new filename[/prompt]', default=f'config_{Path(filename).stem}.yaml')
                            continue
                        elif choice == '2':
                            pass
                        else:
                            console.print('[info]Save cancelled.[/info]')
                            return None
                    with open(filepath, 'w') as f:
                        yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                    console.print(f'\n✅ [success]Configuration saved to: {filepath.absolute()}[/success]')
                    return str(filepath)
                except PermissionError:
                    console.print(f'[error]❌ Permission denied: Cannot write to {filename}[/error]')
                    console.print('[info]Would you like to try a different filename?[/info]')
                    if Confirm.ask('[prompt]Try again?[/prompt]', default=True):
                        filename = None
                        continue
                    else:
                        return None
                except OSError as e:
                    console.print(f'[error]❌ OS error saving file: {e}[/error]')
                    console.print('[info]Would you like to try a different filename?[/info]')
                    if Confirm.ask('[prompt]Try again?[/prompt]', default=True):
                        filename = None
                        continue
                    else:
                        return None
                except Exception as e:
                    console.print(f'[error]❌ Unexpected error saving file: {e}[/error]')
                    return None
        except (KeyboardInterrupt, EOFError):
            console.print('\n[info]Save cancelled by user.[/info]')
            return None
        except Exception as e:
            console.print(f'[error]❌ Error in review and save: {e}[/error]')
            return None

    def run(self) -> Optional[tuple]:
        """Run the interactive configuration builder with comprehensive error handling."""
        try:
            self.show_banner()
            try:
                api_keys = self.detect_api_keys()
            except Exception as e:
                console.print(f'[error]❌ Failed to detect API keys: {e}[/error]')
                api_keys = {}
            if not any(api_keys.values()):
                console.print('[yellow]⚠️  No API keys or local models detected[/yellow]\n')
                console.print('[dim]MassGen needs at least one of:[/dim]')
                console.print('[dim]  • API keys for cloud providers (OpenAI, Anthropic, Google, etc.)[/dim]')
                console.print('[dim]  • Local models (vLLM, Ollama, etc.)[/dim]')
                console.print("[dim]  • Claude Code with 'claude login'[/dim]\n")
                setup_choice = Confirm.ask('[prompt]Would you like to set up API keys now (interactive)?[/prompt]', default=True)
                if setup_choice is None:
                    raise KeyboardInterrupt
                if setup_choice:
                    api_keys = self.interactive_api_key_setup()
                    if not any(api_keys.values()):
                        console.print('\n[error]❌ No API keys were configured.[/error]')
                        console.print('\n[dim]Alternatives to API keys:[/dim]')
                        console.print('[dim]  • Set up local models (vLLM, Ollama)[/dim]')
                        console.print("[dim]  • Use Claude Code with 'claude login'[/dim]")
                        console.print('[dim]  • Manually create .env file: ~/.massgen/.env or ./.env[/dim]\n')
                        return None
                else:
                    console.print('\n[info]To use MassGen, you need at least one provider.[/info]')
                    console.print('\n[cyan]Option 1: API Keys[/cyan]')
                    console.print('  Create .env file with one or more:')
                    for provider_id, provider_info in self.PROVIDERS.items():
                        if provider_info.get('env_var'):
                            console.print(f'    • {provider_info['env_var']}')
                    console.print('\n[cyan]Option 2: Local Models[/cyan]')
                    console.print('  • Set up vLLM, Ollama, or other local inference')
                    console.print('\n[cyan]Option 3: Claude Code[/cyan]')
                    console.print("  • Run 'claude login' in your terminal")
                    console.print("\n[dim]Run 'massgen --init' anytime to restart this wizard[/dim]\n")
                    return None
            try:
                use_case = self.select_use_case()
                if not use_case:
                    console.print('[warning]⚠️  No use case selected.[/warning]')
                    return None
                agents = self.configure_agents(use_case, api_keys)
                if not agents:
                    console.print('[error]❌ No agents configured.[/error]')
                    return None
                try:
                    agents, orchestrator_config = self.configure_tools(use_case, agents)
                except Exception as e:
                    console.print(f'[warning]⚠️  Error configuring tools: {e}[/warning]')
                    console.print('[info]Continuing with basic configuration...[/info]')
                    orchestrator_config = {}
                filepath = self.review_and_save(agents, orchestrator_config)
                if filepath:
                    run_choice = Confirm.ask('\n[prompt]Run MassGen with this configuration now?[/prompt]', default=True)
                    if run_choice is None:
                        raise KeyboardInterrupt
                    if run_choice:
                        question = Prompt.ask('\n[prompt]Enter your question[/prompt]')
                        if question is None:
                            raise KeyboardInterrupt
                        if question:
                            console.print(f'\n[info]Running: massgen --config {filepath} "{question}"[/info]\n')
                            return (filepath, question)
                        else:
                            console.print('[warning]⚠️  No question provided.[/warning]')
                            return (filepath, None)
                return (filepath, None) if filepath else None
            except (KeyboardInterrupt, EOFError):
                console.print('\n\n[bold yellow]Configuration cancelled by user[/bold yellow]')
                console.print('\n[dim]You can run [bold]massgen --init[/bold] anytime to restart.[/dim]\n')
                return None
            except ValueError as e:
                console.print(f'\n[error]❌ Configuration error: {str(e)}[/error]')
                console.print('[info]Please check your inputs and try again.[/info]')
                return None
            except Exception as e:
                console.print(f'\n[error]❌ Unexpected error during configuration: {str(e)}[/error]')
                console.print(f'[info]Error type: {type(e).__name__}[/info]')
                return None
        except KeyboardInterrupt:
            console.print('\n\n[bold yellow]Configuration cancelled by user[/bold yellow]')
            console.print('\n[dim]You can run [bold]massgen --init[/bold] anytime to restart the configuration wizard.[/dim]\n')
            return None
        except EOFError:
            console.print('\n\n[bold yellow]Configuration cancelled[/bold yellow]')
            console.print('\n[dim]You can run [bold]massgen --init[/bold] anytime to restart the configuration wizard.[/dim]\n')
            return None
        except Exception as e:
            console.print(f'\n[error]❌ Fatal error: {str(e)}[/error]')
            console.print('[info]Please report this issue if it persists.[/info]')
            return None

def show_banner(self) -> None:
    """Display welcome banner using Rich Panel."""
    console.clear()
    ascii_art = '[bold cyan]\n     ███╗   ███╗ █████╗ ███████╗███████╗ ██████╗ ███████╗███╗   ██╗\n     ████╗ ████║██╔══██╗██╔════╝██╔════╝██╔════╝ ██╔════╝████╗  ██║\n     ██╔████╔██║███████║███████╗███████╗██║  ███╗█████╗  ██╔██╗ ██║\n     ██║╚██╔╝██║██╔══██║╚════██║╚════██║██║   ██║██╔══╝  ██║╚██╗██║\n     ██║ ╚═╝ ██║██║  ██║███████║███████║╚██████╔╝███████╗██║ ╚████║\n     ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold cyan]\n\n     [dim]     🤖 🤖 🤖  →  💬 collaborate  →  🎯 winner  →  📢 final[/dim]\n'
    banner_content = f'{ascii_art}\n[bold bright_cyan]Interactive Configuration Builder[/bold bright_cyan]\n[dim]Create custom multi-agent configurations in minutes![/dim]'
    banner_panel = Panel(banner_content, border_style='bold cyan', padding=(0, 2), width=80)
    console.print(banner_panel)
    console.print()

class ChatAgent(ABC):
    """
    Abstract base class defining the common chat interface.

    This interface is implemented by both individual agents and the MassGen orchestrator,
    providing a unified way to interact with any type of agent system.
    """

    def __init__(self, session_id: Optional[str]=None):
        self.session_id = session_id or f'chat_session_{uuid.uuid4().hex[:8]}'
        self.conversation_history: List[Dict[str, Any]] = []

    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]=None, reset_chat: bool=False, clear_history: bool=False, current_stage: CoordinationStage=None) -> AsyncGenerator[StreamChunk, None]:
        """
        Enhanced chat interface supporting tool calls and responses.

        Args:
            messages: List of conversation messages including:
                - {"role": "user", "content": "..."}
                - {"role": "assistant", "content": "...", "tool_calls": [...]}
                - {"role": "tool", "tool_call_id": "...", "content": "..."}
                Or a single string for backwards compatibility
            tools: Optional tools to provide to the agent
            reset_chat: If True, reset the agent's conversation history to the provided messages
            clear_history: If True, clear history but keep system message before processing messages
            current_stage: Optional current coordination stage for orchestrator use

        Yields:
            StreamChunk: Streaming response chunks
        """

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

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and state."""

    @abstractmethod
    async def reset(self) -> None:
        """Reset agent state for new conversation."""

    @abstractmethod
    def get_configurable_system_message(self) -> Optional[str]:
        """
        Get the user-configurable part of the system message.

        Returns the domain expertise, role definition, or custom instructions
        that were configured for this agent, without backend-specific details.

        Returns:
            The configurable system message if available, None otherwise
        """

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history."""
        return self.conversation_history.copy()

    def add_to_history(self, role: str, content: str, **kwargs) -> None:
        """Add message to conversation history."""
        message = {'role': role, 'content': content}
        message.update(kwargs)
        self.conversation_history.append(message)

    def add_tool_message(self, tool_call_id: str, result: str) -> None:
        """Add tool result to conversation history."""
        self.add_to_history('tool', result, tool_call_id=tool_call_id)

    def get_last_tool_calls(self) -> List[Dict[str, Any]]:
        """Get tool calls from the last assistant message."""
        for message in reversed(self.conversation_history):
            if message.get('role') == 'assistant' and 'tool_calls' in message:
                return message['tool_calls']
        return []

    def get_session_id(self) -> str:
        """Get session identifier."""
        return self.session_id

def add_to_history(self, role: str, content: str, **kwargs) -> None:
    """Add message to conversation history."""
    message = {'role': role, 'content': content}
    message.update(kwargs)
    self.conversation_history.append(message)

class FunctionHookManager:
    """Manages registration and execution of function hooks."""

    def __init__(self):
        self._hooks: Dict[HookType, List[FunctionHook]] = {hook_type: [] for hook_type in HookType}
        self._global_hooks: Dict[HookType, List[FunctionHook]] = {hook_type: [] for hook_type in HookType}

    def register_hook(self, function_name: str, hook_type: HookType, hook: FunctionHook):
        """Register a hook for a specific function."""
        if function_name not in self._hooks:
            self._hooks[function_name] = {hook_type: [] for hook_type in HookType}
        if hook_type not in self._hooks[function_name]:
            self._hooks[function_name][hook_type] = []
        self._hooks[function_name][hook_type].append(hook)

    def register_global_hook(self, hook_type: HookType, hook: FunctionHook):
        """Register a hook that applies to all functions."""
        self._global_hooks[hook_type].append(hook)

    def get_hooks_for_function(self, function_name: str) -> Dict[HookType, List[FunctionHook]]:
        """Get all hooks (function-specific + global) for a function."""
        result = {hook_type: [] for hook_type in HookType}
        for hook_type in HookType:
            result[hook_type].extend(self._global_hooks[hook_type])
        if function_name in self._hooks:
            for hook_type in HookType:
                if hook_type in self._hooks[function_name]:
                    result[hook_type].extend(self._hooks[function_name][hook_type])
        return result

    def clear_hooks(self):
        """Clear all registered hooks."""
        self._hooks.clear()
        self._global_hooks = {hook_type: [] for hook_type in HookType}

def clear_hooks(self):
    """Clear all registered hooks."""
    self._hooks.clear()
    self._global_hooks = {hook_type: [] for hook_type in HookType}

class PermissionClientSession(ClientSession):
    """
    ClientSession subclass that intercepts tool calls to apply permission hooks.

    This inherits from ClientSession instead of wrapping it, which ensures
    compatibility with SDK type checking and attribute access.
    """

    def __init__(self, wrapped_session: ClientSession, permission_manager):
        """
        Initialize by copying state from an existing ClientSession.

        Args:
            wrapped_session: The actual ClientSession to copy state from
            permission_manager: Object with pre_tool_use_hook method for validation
        """
        self._permission_manager = permission_manager
        self.__dict__.update(wrapped_session.__dict__)
        logger.debug(f'[PermissionClientSession] Created permission session from {id(wrapped_session)}')

    async def call_tool(self, name: str, arguments: dict[str, Any] | None=None, read_timeout_seconds: timedelta | None=None, progress_callback: ProgressFnT | None=None) -> types.CallToolResult:
        """
        Override call_tool to apply permission hooks before calling the actual tool.
        """
        tool_args = arguments or {}
        logger.debug(f'[PermissionClientSession] Intercepted tool call: {name} with args: {tool_args}')
        if self._permission_manager and hasattr(self._permission_manager, 'pre_tool_use_hook'):
            try:
                allowed, reason = await self._permission_manager.pre_tool_use_hook(name, tool_args)
                if not allowed:
                    error_msg = f"Permission denied for tool '{name}'"
                    if reason:
                        error_msg += f': {reason}'
                    logger.warning(f'🚫 [PermissionClientSession] {error_msg}')
                    return types.CallToolResult(content=[types.TextContent(type='text', text=f'Error: {error_msg}')], isError=True)
                else:
                    logger.debug(f"[PermissionClientSession] Tool '{name}' permission check passed")
            except Exception as e:
                logger.error(f'[PermissionClientSession] Error in permission hook: {e}')
        try:
            result = await super().call_tool(name=name, arguments=arguments, read_timeout_seconds=read_timeout_seconds, progress_callback=progress_callback)
            logger.debug(f"[PermissionClientSession] Tool '{name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"[PermissionClientSession] Tool '{name}' failed: {e}")
            raise

def __init__(self, wrapped_session: ClientSession, permission_manager):
    """
        Initialize by copying state from an existing ClientSession.

        Args:
            wrapped_session: The actual ClientSession to copy state from
            permission_manager: Object with pre_tool_use_hook method for validation
        """
    self._permission_manager = permission_manager
    self.__dict__.update(wrapped_session.__dict__)
    logger.debug(f'[PermissionClientSession] Created permission session from {id(wrapped_session)}')

class MCPCircuitBreaker:
    """
    Circuit breaker for MCP server failure handling.

    Provides consistent failure tracking and exponential backoff across all MCP integrations.
    Prevents repeated connection attempts to failing servers while allowing recovery.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig]=None, backend_name: Optional[str]=None, agent_id: Optional[str]=None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration. Uses default if None.
            backend_name: Name of the backend using this circuit breaker for logging context.
            agent_id: Optional agent ID for logging context.
        """
        self.config = config or CircuitBreakerConfig()
        self.backend_name = backend_name
        self.agent_id = agent_id
        self._server_status: Dict[str, ServerStatus] = {}

    def should_skip_server(self, server_name: str, agent_id: Optional[str]=None) -> bool:
        """
        Check if server should be skipped due to circuit breaker.

        Args:
            server_name: Name of the server to check

        Returns:
            True if server should be skipped, False otherwise
        """
        if server_name not in self._server_status:
            return False
        status = self._server_status[server_name]
        if status.failure_count < self.config.max_failures:
            return False
        current_time = time.monotonic()
        time_since_failure = current_time - status.last_failure_time
        backoff_time = self._calculate_backoff_time(status.failure_count)
        if time_since_failure > backoff_time:
            log_mcp_activity(self.backend_name, 'Circuit breaker reset for server', {'server_name': server_name, 'backoff_time_seconds': backoff_time}, agent_id=self.agent_id or agent_id)
            self._reset_server(server_name)
            return False
        return True

    def record_failure(self, server_name: str, agent_id: Optional[str]=None) -> None:
        """
        Record a server failure for circuit breaker.

        Args:
            server_name: Name of the server that failed
        """
        current_time = time.monotonic()
        if server_name not in self._server_status:
            self._server_status[server_name] = ServerStatus()
        status = self._server_status[server_name]
        status.failure_count += 1
        status.last_failure_time = current_time
        if status.failure_count >= self.config.max_failures:
            backoff_time = self._calculate_backoff_time(status.failure_count)
            log_mcp_activity(self.backend_name, 'Server circuit breaker opened', {'server_name': server_name, 'failure_count': status.failure_count, 'backoff_time_seconds': backoff_time}, agent_id=self.agent_id or agent_id)
        else:
            log_mcp_activity(self.backend_name, 'Server failure recorded', {'server_name': server_name, 'failure_count': status.failure_count, 'max_failures': self.config.max_failures}, agent_id=self.agent_id or agent_id)

    def record_success(self, server_name: str, agent_id: Optional[str]=None) -> None:
        """
        Record a successful connection, resetting failure count.

        Args:
            server_name: Name of the server that succeeded
        """
        if server_name in self._server_status:
            old_status = self._server_status[server_name]
            if old_status.failure_count > 0:
                log_mcp_activity(self.backend_name, 'Server recovered', {'server_name': server_name, 'previous_failure_count': old_status.failure_count}, agent_id=self.agent_id or agent_id)
            self._reset_server(server_name)

    def _reset_server(self, server_name: str) -> None:
        """Reset circuit breaker state for a specific server."""
        if server_name in self._server_status:
            del self._server_status[server_name]

    def _calculate_backoff_time(self, failure_count: int) -> float:
        """
        Calculate backoff time based on failure count.

        Args:
            failure_count: Number of failures

        Returns:
            Backoff time in seconds
        """
        if failure_count < self.config.max_failures:
            return 0.0
        exponent = failure_count - self.config.max_failures
        multiplier = min(self.config.backoff_multiplier ** exponent, self.config.max_backoff_multiplier)
        return self.config.reset_time_seconds * multiplier

    def __repr__(self) -> str:
        """String representation for debugging."""
        failing_count = len([s for s in self._server_status.values() if s.is_failing])
        total_servers = len(self._server_status)
        return f'MCPCircuitBreaker(failing={failing_count}/{total_servers}, config={self.config})'

def _calculate_backoff_time(self, failure_count: int) -> float:
    """
        Calculate backoff time based on failure count.

        Args:
            failure_count: Number of failures

        Returns:
            Backoff time in seconds
        """
    if failure_count < self.config.max_failures:
        return 0.0
    exponent = failure_count - self.config.max_failures
    multiplier = min(self.config.backoff_multiplier ** exponent, self.config.max_backoff_multiplier)
    return self.config.reset_time_seconds * multiplier

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

def _invalidate_display_cache(self) -> None:
    """Invalidate all cached display components to force refresh."""
    self._agent_panels_cache.clear()
    self._header_cache = None
    self._footer_cache = None

def _get_adaptive_buffer_length(self) -> int:
    """Get adaptive buffer length based on terminal performance."""
    perf_tier = self._terminal_performance['performance_tier']
    term_type = self._terminal_performance['type']
    lengths = {'high': 800, 'medium': 500, 'low': 200}
    base_length = lengths.get(perf_tier, 500)
    if term_type in ['iterm', 'macos_terminal']:
        base_length = min(base_length, 400)
    return base_length

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

def timeout_flush() -> None:
    with self._lock:
        if agent_id in self._text_buffers and self._text_buffers[agent_id]:
            self._flush_buffer(agent_id)
            self._pending_updates.add(agent_id)
            self._schedule_async_update(force_update=True)

def _force_display_final_vote_statuses(self) -> None:
    """Force display update to show all agents' final vote statuses."""
    with self._lock:
        for agent_id in self.agent_ids:
            self._pending_updates.add(agent_id)
        self._pending_updates.add('footer')
        self._schedule_async_update(force_update=True)
    import time
    time.sleep(0.3)

def priority_update() -> None:
    try:
        self._update_agent_panel_cache(agent_id)
        self._update_display_safe()
    except Exception:
        pass

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

def delayed_update() -> None:
    if self._pending_updates:
        self._schedule_async_update(force_update=False)

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

def _get_terminal_width(self) -> int:
    """Get terminal width with fallback."""
    try:
        return min(os.get_terminal_size().columns, 120)
    except (OSError, AttributeError):
        return 80

def display_scrollable_content_macos(console: Console, content_items: List[Any], title: str='') -> None:
    """
    Display scrollable content with macOS-compatible navigation.
    Works around macOS Terminal's issues with Rich's pager.
    """
    if not content_items:
        console.print('[dim]No content to display[/dim]')
        return
    console.clear()
    console.print('\x1b[H', end='')
    if title:
        console.print(f'\n[bold bright_green]{title}[/bold bright_green]\n')
    for item in content_items:
        console.print(item)
    console.print('\n' + '=' * 80)
    console.print('[bright_cyan]Press Enter to return to agent selector...[/bright_cyan]')
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

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

def _extract_adapter_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract framework-specific configuration."""
    excluded_params = self.get_base_excluded_config_params()
    excluded_params.update({''})
    return {k: v for k, v in config.items() if k not in excluded_params}

class MCPResponseExtractor:
    """
    Extracts MCP tool calls and responses from Gemini SDK stream chunks.

    This class parses the internal SDK chunks to capture:
    - function_call parts (tool invocations)
    - function_response parts (tool results)
    - Paired call-response data for tracking complete tool executions
    """

    def __init__(self):
        """Initialize the extractor with empty storage."""
        self.mcp_calls = []
        self.mcp_responses = []
        self.call_response_pairs = []
        self._pending_call = None

    def extract_function_call(self, function_call) -> Optional[Dict[str, Any]]:
        """
        Extract tool call information from SDK function_call object.

        Tries multiple methods to extract data from different SDK versions:
        1. Direct attributes (name, args)
        2. Dictionary-like interface (get method)
        3. __dict__ attributes
        4. Protobuf _pb attributes
        """
        tool_name = None
        tool_args = None
        tool_name = getattr(function_call, 'name', None)
        tool_args = getattr(function_call, 'args', None)
        if tool_name is None:
            try:
                if hasattr(function_call, 'get'):
                    tool_name = function_call.get('name', None)
                    tool_args = function_call.get('args', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_call, '__dict__'):
                    fc_dict = function_call.__dict__
                    tool_name = fc_dict.get('name', None)
                    tool_args = fc_dict.get('args', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_call, '_pb'):
                    pb = function_call._pb
                    if hasattr(pb, 'name'):
                        tool_name = pb.name
                    if hasattr(pb, 'args'):
                        tool_args = pb.args
            except Exception:
                pass
        if tool_name:
            call_data = {'name': tool_name, 'arguments': tool_args or {}, 'timestamp': time.time(), 'raw': str(function_call)[:200]}
            self.mcp_calls.append(call_data)
            self._pending_call = call_data
            return call_data
        return None

    def extract_function_response(self, function_response) -> Optional[Dict[str, Any]]:
        """
        Extract tool response information from SDK function_response object.

        Uses same extraction methods as function_call for consistency.
        """
        tool_name = None
        tool_response = None
        tool_name = getattr(function_response, 'name', None)
        tool_response = getattr(function_response, 'response', None)
        if tool_name is None:
            try:
                if hasattr(function_response, 'get'):
                    tool_name = function_response.get('name', None)
                    tool_response = function_response.get('response', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_response, '__dict__'):
                    fr_dict = function_response.__dict__
                    tool_name = fr_dict.get('name', None)
                    tool_response = fr_dict.get('response', None)
            except Exception:
                pass
        if tool_name is None:
            try:
                if hasattr(function_response, '_pb'):
                    pb = function_response._pb
                    if hasattr(pb, 'name'):
                        tool_name = pb.name
                    if hasattr(pb, 'response'):
                        tool_response = pb.response
            except Exception:
                pass
        if tool_name:
            response_data = {'name': tool_name, 'response': tool_response or {}, 'timestamp': time.time(), 'raw': str(function_response)[:500]}
            self.mcp_responses.append(response_data)
            if self._pending_call and self._pending_call['name'] == tool_name:
                self.call_response_pairs.append({'call': self._pending_call, 'response': response_data, 'duration': response_data['timestamp'] - self._pending_call['timestamp'], 'paired_at': time.time()})
                self._pending_call = None
            return response_data
        return None

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all extracted MCP tool interactions.
        """
        return {'total_calls': len(self.mcp_calls), 'total_responses': len(self.mcp_responses), 'paired_interactions': len(self.call_response_pairs), 'pending_call': self._pending_call is not None, 'tool_names': list(set((call['name'] for call in self.mcp_calls))), 'average_duration': sum((pair['duration'] for pair in self.call_response_pairs)) / len(self.call_response_pairs) if self.call_response_pairs else 0}

    def clear(self):
        """Clear all stored data."""
        self.mcp_calls.clear()
        self.mcp_responses.clear()
        self.call_response_pairs.clear()
        self._pending_call = None

def clear(self):
    """Clear all stored data."""
    self.mcp_calls.clear()
    self.mcp_responses.clear()
    self.call_response_pairs.clear()
    self._pending_call = None

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

def clear_mcp_results(self):
    """Clear all stored MCP interaction data."""
    self.mcp_extractor.clear()

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

def _calculate_session_duration(self) -> float:
    """Calculate total session duration."""
    if not self.log_entries:
        return 0.0
    start_time = min((entry.timestamp for entry in self.log_entries))
    end_time = max((entry.timestamp for entry in self.log_entries))
    return end_time - start_time

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

def _get_terminal_width(self):
    """Get terminal width with conservative fallback."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 120

def cleanup(self):
    """Clean up resources when display is no longer needed."""
    with self._lock:
        if self._update_timer:
            self._update_timer.cancel()
            self._update_timer = None
        self._pending_update = False
        self._display_updating = False

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

def reset_consensus(self):
    """Reset consensus state for new debate round."""
    with self._lock:
        self.consensus_reached = False
        self.representative_agent_id = None
        self.vote_distribution.clear()

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

def force_update_display(self):
    """Force an immediate display update (for status changes)."""
    with self._lock:
        if self._update_timer:
            self._update_timer.cancel()
        self._pending_update = True
    self._execute_display_update()

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

def clear_history(self) -> None:
    """Clear conversation history."""
    self._conversation_history.clear()

