# Cluster 3

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

def get_backend_type_from_model(model: str) -> str:
    """
    Determine the agent type based on the model name.

    Args:
        model: The model name (e.g., "gpt-4", "gemini-pro", "grok-1")

    Returns:
        Agent type string ("openai", "gemini", "grok", etc.)
    """
    if not model:
        return 'openai'
    model_lower = model.lower()
    for key, models in MODEL_MAPPINGS.items():
        if model_lower in models:
            return key
    raise ValueError(f'Unknown model: {model}')

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

def _get_agent_id_from_label(self, label: str) -> str:
    """Extract agent_id from a label like 'agent1.1' or 'agent2.final'."""
    import re
    match = re.match('agent(\\d+)', label)
    if match:
        agent_num = int(match.group(1))
        if 0 < agent_num <= len(self.agent_ids):
            return self.agent_ids[agent_num - 1]
    return 'unknown'

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

class MCPErrorHandler:
    """Standardized MCP error handling utilities."""

    @staticmethod
    def get_error_details(error: Exception, context: str | None=None, *, log: bool=False) -> tuple[str, str, str]:
        """Return standardized MCP error info and optionally log.

        Returns:
            Tuple of (log_type, user_message, error_category)
        """
        if isinstance(error, MCPConnectionError):
            details = ('connection error', 'MCP connection failed', 'connection')
        elif isinstance(error, MCPTimeoutError):
            details = ('timeout error', 'MCP session timeout', 'timeout')
        elif isinstance(error, MCPServerError):
            details = ('server error', 'MCP server error', 'server')
        elif isinstance(error, MCPValidationError):
            details = ('validation error', 'MCP validation failed', 'validation')
        elif isinstance(error, MCPAuthenticationError):
            details = ('authentication error', 'MCP authentication failed', 'auth')
        elif isinstance(error, MCPResourceError):
            details = ('resource error', 'MCP resource unavailable', 'resource')
        elif isinstance(error, MCPError):
            details = ('MCP error', 'MCP error', 'general')
        else:
            details = ('unexpected error', 'MCP connection failed', 'unknown')
        if log:
            log_type, user_message, error_category = details
            logger.warning(f'MCP {log_type}: {error}', extra={'context': context or 'none'})
        return details

    @staticmethod
    def is_transient_error(error: Exception) -> bool:
        """Determine if an error is transient and should be retried."""
        if isinstance(error, (MCPConnectionError, MCPTimeoutError)):
            return True
        elif isinstance(error, MCPServerError):
            error_str = str(error).lower()
            return any((keyword in error_str for keyword in ['timeout', 'connection', 'network', 'temporary', 'unavailable', '503', '502', '504', '500', 'retry']))
        elif isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return True
        elif isinstance(error, MCPResourceError):
            return True
        return False

    @staticmethod
    def log_error(error: Exception, context: str, level: str='auto', backend_name: str | None=None, agent_id: str | None=None) -> None:
        """Log MCP error with appropriate level and context."""
        log_type, user_message, error_category = MCPErrorHandler.get_error_details(error)
        if level == 'auto':
            level = 'warning' if error_category in ['connection', 'timeout', 'resource'] else 'error'
        log_message = f'MCP {log_type} during {context}: {error}'
        log_mcp_activity(backend_name, f'error ({level})', {'message': log_message}, agent_id=agent_id)

    @staticmethod
    def get_retry_delay(attempt: int, base_delay: float=DEFAULT_RETRY_BASE_DELAY) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        backoff_delay = base_delay * 2 ** attempt
        jitter = random.uniform(DEFAULT_RETRY_JITTER_MIN, DEFAULT_RETRY_JITTER_MAX) * backoff_delay
        return backoff_delay + jitter

    @staticmethod
    def is_auth_or_resource_error(error: Exception) -> bool:
        """Check if error is authentication or resource related (non-retryable)."""
        return isinstance(error, (MCPAuthenticationError, MCPResourceError))

@staticmethod
def is_transient_error(error: Exception) -> bool:
    """Determine if an error is transient and should be retried."""
    if isinstance(error, (MCPConnectionError, MCPTimeoutError)):
        return True
    elif isinstance(error, MCPServerError):
        error_str = str(error).lower()
        return any((keyword in error_str for keyword in ['timeout', 'connection', 'network', 'temporary', 'unavailable', '503', '502', '504', '500', 'retry']))
    elif isinstance(error, (ConnectionError, TimeoutError, OSError)):
        return True
    elif isinstance(error, MCPResourceError):
        return True
    return False

class MCPSetupManager:
    """MCP setup and initialization utilities."""

    @staticmethod
    def normalize_mcp_servers(servers: Any, backend_name: str | None=None, agent_id: str | None=None) -> list[dict[str, Any]]:
        """Validate and normalize mcp_servers into a list of dicts.

        Args:
            servers: MCP servers configuration (list, dict, or None)
            backend_name: Optional backend name for logging context
            agent_id: Optional agent ID for logging context

        Returns:
            Normalized list of server dictionaries
        """
        if not servers:
            return []
        if isinstance(servers, dict):
            if 'type' in servers:
                servers = [servers]
            else:
                converted = []
                for name, server_config in servers.items():
                    if isinstance(server_config, dict):
                        server = server_config.copy()
                        server['name'] = name
                        converted.append(server)
                servers = converted
        if not isinstance(servers, list):
            log_mcp_activity(backend_name, 'invalid mcp_servers type', {'type': type(servers).__name__, 'expected': 'list or dict'}, agent_id=agent_id)
            return []
        normalized = []
        for i, server in enumerate(servers):
            if not isinstance(server, dict):
                log_mcp_activity(backend_name, 'skipping invalid server', {'index': i, 'server': str(server)}, agent_id=agent_id)
                continue
            if 'type' not in server:
                log_mcp_activity(backend_name, 'server missing type field', {'index': i}, agent_id=agent_id)
                continue
            if 'name' not in server:
                server = server.copy()
                server['name'] = f'server_{i}'
            normalized.append(server)
        return normalized

    @staticmethod
    def separate_stdio_streamable_servers(servers: list[dict[str, Any]], backend_name: str | None=None, agent_id: str | None=None) -> list[dict[str, Any]]:
        """Extract only stdio and streamable-http servers.

        Args:
            servers: List of server configurations
            backend_name: Optional backend name for logging context
            agent_id: Optional agent ID for logging context

        Returns:
            List containing only stdio and streamable-http servers
        """
        stdio_streamable = []
        for server in servers:
            transport_type = server.get('type', '').lower()
            if transport_type in ['stdio', 'streamable-http']:
                stdio_streamable.append(server)
        return stdio_streamable

@staticmethod
def separate_stdio_streamable_servers(servers: list[dict[str, Any]], backend_name: str | None=None, agent_id: str | None=None) -> list[dict[str, Any]]:
    """Extract only stdio and streamable-http servers.

        Args:
            servers: List of server configurations
            backend_name: Optional backend name for logging context
            agent_id: Optional agent ID for logging context

        Returns:
            List containing only stdio and streamable-http servers
        """
    stdio_streamable = []
    for server in servers:
        transport_type = server.get('type', '').lower()
        if transport_type in ['stdio', 'streamable-http']:
            stdio_streamable.append(server)
    return stdio_streamable

def replace_env_var(match):
    var_name = match.group(1)
    env_value = os.environ.get(var_name)
    if env_value is None or env_value.strip() == '':
        raise ValueError(f"Required environment variable '{var_name}' is not set")
    return env_value

def validate_server_security(config: dict) -> dict:
    """
    Validate and sanitize MCP server configuration with comprehensive security checks.

    Args:
        config: Server configuration dictionary

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If configuration is invalid or insecure
    """
    if not isinstance(config, dict):
        raise ValueError('Server configuration must be a dictionary')
    validated_config = config.copy()
    if 'name' not in validated_config:
        raise ValueError("Server configuration must include 'name'")
    server_name = validated_config['name']
    _validate_non_empty_string(server_name, 'Server name')
    _validate_string_length(server_name, MAX_SERVER_NAME_LENGTH, 'Server name')
    if not re.match('^[a-zA-Z0-9_-]+$', server_name):
        raise ValueError('Server name can only contain alphanumeric characters, underscores, and hyphens')
    transport_type = validated_config.get('type', 'stdio')
    security_cfg = _get_dict_from_config(validated_config, 'security')
    security_level = security_cfg.get('level', 'strict')
    if transport_type == 'stdio':
        if 'command' not in validated_config and 'args' not in validated_config:
            raise ValueError("Stdio server configuration must include 'command' or 'args'")
        if 'command' in validated_config:
            if isinstance(validated_config['command'], str):
                validated_config['command'] = prepare_command(validated_config['command'], security_level=security_level, allowed_executables=_get_set_from_config(security_cfg, 'allowed_executables'))
            elif isinstance(validated_config['command'], list):
                if not validated_config['command']:
                    raise ValueError('Command list cannot be empty')
                command_str = ' '.join((shlex.quote(arg) for arg in validated_config['command']))
                validated_config['command'] = prepare_command(command_str, security_level=security_level, allowed_executables=_get_set_from_config(security_cfg, 'allowed_executables'))
            else:
                raise ValueError('Command must be a string or list')
        if 'args' in validated_config:
            args = validated_config['args']
            if not isinstance(args, list):
                raise ValueError('Arguments must be a list')
            for i, arg in enumerate(args):
                if not isinstance(arg, str):
                    raise ValueError(f'Argument {i} must be a string')
                if len(arg) > MAX_ARG_LENGTH:
                    raise ValueError(f'Argument {i} too long: {len(arg)} > {MAX_ARG_LENGTH} characters')
        if 'env' in validated_config:
            env_policy = _get_dict_from_config(security_cfg, 'env')
            validated_config['env'] = validate_environment_variables(validated_config['env'], level=env_policy.get('level', security_level), mode=env_policy.get('mode', 'denylist'), allowed_vars=_get_set_from_config(env_policy, 'allowed_vars') or set(), denied_vars=_get_set_from_config(env_policy, 'denied_vars'))
        if 'cwd' in validated_config:
            cwd = validated_config['cwd']
            if not isinstance(cwd, str):
                raise ValueError('Working directory must be a string')
            _validate_string_length(cwd, MAX_CWD_LENGTH, 'Working directory path')
            cwd_path = Path(cwd)
            if any((part == '..' for part in cwd_path.parts)):
                raise ValueError("Working directory cannot contain parent directory components ('..')")
    elif transport_type == 'streamable-http':
        if 'url' not in validated_config:
            raise ValueError(f"{transport_type} server configuration must include 'url'")
        allowed_hostnames_cfg = security_cfg.get('allowed_hostnames')
        allowed_hostnames = None
        if isinstance(allowed_hostnames_cfg, (list, set, tuple)):
            allowed_hostnames = {str(h) for h in allowed_hostnames_cfg if isinstance(h, (str, bytes))}
        validate_url(validated_config['url'], resolve_dns=bool(security_cfg.get('resolve_dns', False)), allow_private_ips=bool(security_cfg.get('allow_private_ips', False)), allow_localhost=bool(security_cfg.get('allow_localhost', False)), allowed_hostnames=allowed_hostnames)
        if 'headers' in validated_config:
            headers = validated_config['headers']
            if not isinstance(headers, dict):
                raise ValueError('Headers must be a dictionary')
            for key, value in headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError('Header keys and values must be strings')
                _validate_string_length(key, MAX_HEADER_KEY_LENGTH, 'Header name')
                _validate_string_length(value, MAX_HEADER_VALUE_LENGTH, 'Header value')
        if 'timeout' in validated_config:
            timeout = validated_config['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValueError('Timeout must be a positive number')
            if timeout > MAX_TIMEOUT_SECONDS:
                raise ValueError(f'Timeout too large: {timeout} > {MAX_TIMEOUT_SECONDS} seconds')
        if 'http_read_timeout' in validated_config:
            http_read_timeout = validated_config['http_read_timeout']
            if not isinstance(http_read_timeout, (int, float)) or http_read_timeout <= 0:
                raise ValueError('http_read_timeout must be a positive number')
            if http_read_timeout > MAX_TIMEOUT_SECONDS:
                raise ValueError(f'http_read_timeout too large: {http_read_timeout} > {MAX_TIMEOUT_SECONDS} seconds')
    else:
        supported_types = ['stdio', 'streamable-http']
        raise ValueError(f"Unsupported transport type: {transport_type}. Supported types: {supported_types}. Note: 'sse' transport was deprecated in MCP v2025-03-26, use 'streamable-http' instead.")
    return validated_config

def sanitize_tool_name(tool_name: str, server_name: str) -> str:
    """
    Create a sanitized tool name with server prefix and comprehensive validation.

    Args:
        tool_name: Original tool name
        server_name: Server name for prefixing

    Returns:
        Sanitized tool name with prefix

    Raises:
        ValueError: If tool name or server name is invalid
    """
    _validate_non_empty_string(tool_name, 'Tool name')
    _validate_non_empty_string(server_name, 'Server name')
    _validate_string_length(tool_name, MAX_TOOL_NAME_LENGTH, 'Tool name')
    _validate_string_length(server_name, MAX_SERVER_NAME_FOR_TOOL_LENGTH, 'Server name')
    if tool_name.startswith('mcp__'):
        tool_name = tool_name[5:]
        if '__' in tool_name:
            parts = tool_name.split('__', 1)
            if len(parts) == 2:
                tool_name = parts[1]
    reserved_names = {'connect', 'disconnect', 'list', 'help', 'version', 'status', 'health', 'ping', 'debug', 'admin', 'system', 'config', 'settings', 'auth', 'login', 'logout', 'exit', 'quit'}
    if tool_name.lower() in reserved_names:
        raise ValueError(f"Tool name '{tool_name}' is reserved and cannot be used")
    if not re.match('^[a-zA-Z0-9_.-]+$', tool_name):
        raise ValueError(f"Tool name '{tool_name}' contains invalid characters. Only alphanumeric, underscore, hyphen, and dot are allowed.")
    if not re.match('^[a-zA-Z0-9_-]+$', server_name):
        raise ValueError(f"Server name '{server_name}' contains invalid characters. Only alphanumeric, underscore, and hyphen are allowed.")
    safe_server_name = server_name.strip('_-')
    safe_tool_name = tool_name.strip('_.-')
    if not safe_server_name:
        raise ValueError(f"Server name '{server_name}' becomes empty after sanitization")
    if not safe_tool_name:
        raise ValueError(f"Tool name '{tool_name}' becomes empty after sanitization")
    final_name = f'mcp__{safe_server_name}__{safe_tool_name}'
    _validate_string_length(final_name, MAX_FINAL_TOOL_NAME_LENGTH, 'Final tool name')
    return final_name

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

def _check_command_filters(command: str, allowed_patterns: Optional[List[str]], blocked_patterns: Optional[List[str]]) -> None:
    """
    Check command against whitelist/blacklist filters.

    Args:
        command: The command to check
        allowed_patterns: Whitelist regex patterns (if provided, command MUST match one)
        blocked_patterns: Blacklist regex patterns (command must NOT match any)

    Raises:
        ValueError: If command doesn't match whitelist or matches blacklist
    """
    if allowed_patterns:
        if not any((re.match(pattern, command) for pattern in allowed_patterns)):
            raise ValueError(f'Command not in allowed list. Allowed patterns: {', '.join(allowed_patterns)}')
    if blocked_patterns:
        for pattern in blocked_patterns:
            if re.match(pattern, command):
                raise ValueError(f"Command matches blocked pattern: '{pattern}'")

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

def _is_web_search_content(self, line: str) -> bool:
    """Check if content is from web search and needs special formatting."""
    web_search_indicators = ['[Provider Tool: Web Search]', '🔍 [Search Query]', '✅ [Provider Tool: Web Search]', '🔍 [Provider Tool: Web Search]']
    return any((indicator in line for indicator in web_search_indicators))

def _should_filter_line(self, line: str) -> bool:
    """Determine if a specific line should be filtered out."""
    filter_patterns = ['^\\s*\\([^)]+\\)\\s*$', '^\\s*\\[[^\\]]+\\]\\s*$', '^\\s*https?://\\S+\\s*$', '^\\s*\\.\\.\\.\\s*$']
    for pattern in filter_patterns:
        if re.match(pattern, line):
            return True
    return False

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

def _is_content_important(self, content: str, content_type: str) -> bool:
    """Determine if content is important enough to trigger a display update."""
    if content_type in self._important_content_types:
        return True
    if any((keyword in content.lower() for keyword in self._status_change_keywords)):
        return True
    if any((keyword in content.lower() for keyword in ['error', 'exception', 'failed', 'timeout'])):
        return True
    return False

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

def _is_action_content(self, content: str) -> bool:
    """Check if content represents an action that should be on its own line."""
    action_indicators = ['💡', '🗳️', '✅', '🔄', '❌', '🔧', 'Providing answer:', 'Voting for', 'Answer provided', 'Vote recorded', 'Vote ignored', 'Vote invalid', 'Using']
    return any((indicator in content for indicator in action_indicators))

def is_macos_terminal() -> bool:
    """Check if running in macOS Terminal or similar."""
    if sys.platform != 'darwin':
        return False
    term_program = os.environ.get('TERM_PROGRAM', '').lower()
    return term_program in ['apple_terminal', 'terminal', 'iterm.app', '']

class ResponseFormatter(FormatterBase):
    """Formatter for Response API format with multimodal support."""

    def format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert messages from Chat Completions format to Response API format.

        Chat Completions tool message: {"role": "tool", "tool_call_id": "...", "content": "..."}
        Response API tool message: {"type": "function_call_output", "call_id": "...", "output": "..."}

        Also handles multimodal content conversion:
        - {"type": "text", "text": "..."} → {"type": "input_text", "text": "..."}
        - {"type": "image", "url": "..."} → {"type": "input_image", "image_url": "..."}
        - {"type": "image", "base64": "..."} → {"type": "input_image", "image_url": "data:image/...;base64,..."}

        Note: Assistant messages with tool_calls should not be in input - they're generated by the backend.
        """
        cleaned_messages = []
        for message in messages:
            if 'status' in message and 'role' not in message:
                cleaned_message = {k: v for k, v in message.items() if k != 'status'}
                cleaned_messages.append(cleaned_message)
            else:
                cleaned_messages.append(message)
        converted_messages = []
        for message in cleaned_messages:
            if message.get('role') == 'tool':
                converted_message = {'type': 'function_call_output', 'call_id': message.get('tool_call_id'), 'output': message.get('content', '')}
                converted_messages.append(converted_message)
            elif message.get('type') == 'function_call_output':
                converted_messages.append(message)
            elif message.get('role') == 'assistant' and 'tool_calls' in message:
                cleaned_message = {k: v for k, v in message.items() if k != 'tool_calls'}
                converted_messages.append(cleaned_message)
            else:
                converted_message = self._convert_multimodal_content(message.copy())
                converted_messages.append(converted_message)
        return converted_messages

    def _convert_multimodal_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert multimodal content to Response API format.

        Handles conversion of content arrays with text and image items:
        - text items: {"type": "text", "text": "..."} → {"type": "input_text", "text": "..."}
        - image URL: {"type": "image", "url": "..."} → {"type": "input_image", "image_url": "..."}
        - image base64: {"type": "image", "base64": "...", "mime_type": "..."} →
                        {"type": "input_image", "image_url": "data:image/...;base64,..."}
        - file: {"type": "file", "file_id": "..."} → {"type": "input_file", "file_id": "..."}

        Args:
            message: Message dictionary that may contain multimodal content

        Returns:
            Message with content converted to Response API format
        """
        content = message.get('content')
        if not isinstance(content, list):
            return message
        converted_content = []
        for item in content:
            if not isinstance(item, dict):
                converted_content.append({'type': 'input_text', 'text': str(item)})
                continue
            item_type = item.get('type')
            if item_type == 'text':
                converted_content.append({'type': 'input_text', 'text': item.get('text', '')})
            elif item_type == 'image':
                converted_item = self._convert_image_content(item)
                if converted_item:
                    converted_content.append(converted_item)
            elif item_type == 'file':
                converted_content.append({'type': 'input_file', 'file_id': item.get('file_id', '')})
            elif item_type == 'file_pending_upload':
                converted_content.append(item)
            elif item_type in ['input_text', 'input_image', 'input_file']:
                converted_content.append(item)
            else:
                converted_content.append(item)
        message['content'] = converted_content
        return message

    def _convert_image_content(self, image_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert image content item to Response API format.

        Supports:
        - URL format: {"type": "image", "url": "https://..."}
        - Base64 format: {"type": "image", "base64": "...", "mime_type": "image/jpeg"}
        - Image URL format: {"type": "image", "image_url": "..."} (already correct)

        Args:
            image_item: Image content item dictionary

        Returns:
            Converted image item in Response API format, or None if invalid
        """
        if 'image_url' in image_item:
            return {'type': 'input_image', 'image_url': image_item['image_url']}
        if 'url' in image_item:
            return {'type': 'input_image', 'image_url': image_item['url']}
        if 'base64' in image_item:
            mime_type = image_item.get('mime_type', 'image/jpeg')
            base64_data = image_item['base64']
            if not self._validate_base64_image(base64_data):
                return None
            data_url = f'data:{mime_type};base64,{base64_data}'
            return {'type': 'input_image', 'image_url': data_url}
        return None

    def _validate_base64_image(self, base64_data: str) -> bool:
        """
        Validate base64 image data.

        Checks:
        - Data is not empty
        - Data is valid base64 (basic check)
        - Data size is within limits (20MB)

        Args:
            base64_data: Base64 encoded image string

        Returns:
            True if valid, False otherwise
        """
        if not base64_data:
            return False
        max_base64_size = 27 * 1024 * 1024
        if len(base64_data) > max_base64_size:
            return False
        import re
        if not re.match('^[A-Za-z0-9+/]*={0,2}$', base64_data):
            return False
        return True

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools from Chat Completions format to Response API format if needed.

        Chat Completions format: {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
        Response API format: {"type": "function", "name": ..., "description": ..., "parameters": ...}
        """
        if not tools:
            return tools
        converted_tools = []
        for tool in tools:
            if tool.get('type') == 'function' and 'function' in tool:
                func = tool['function']
                converted_tools.append({'type': 'function', 'name': func['name'], 'description': func['description'], 'parameters': func.get('parameters', {})})
            else:
                converted_tools.append(tool)
        return converted_tools

    def format_mcp_tools(self, mcp_functions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Response API format (OpenAI function declarations)."""
        if not mcp_functions:
            return []
        converted_tools = []
        for mcp_function in mcp_functions.values():
            if hasattr(mcp_function, 'to_openai_format'):
                tool = mcp_function.to_openai_format()
            else:
                tool = {'type': 'function', 'name': getattr(mcp_function, 'name', 'unknown'), 'description': getattr(mcp_function, 'description', ''), 'parameters': getattr(mcp_function, 'input_schema', {})}
            converted_tools.append(tool)
        return converted_tools

def _validate_base64_image(self, base64_data: str) -> bool:
    """
        Validate base64 image data.

        Checks:
        - Data is not empty
        - Data is valid base64 (basic check)
        - Data size is within limits (20MB)

        Args:
            base64_data: Base64 encoded image string

        Returns:
            True if valid, False otherwise
        """
    if not base64_data:
        return False
    max_base64_size = 27 * 1024 * 1024
    if len(base64_data) > max_base64_size:
        return False
    import re
    if not re.match('^[A-Za-z0-9+/]*={0,2}$', base64_data):
        return False
    return True

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

def _process_stderr(self, stderr):
    """Process server stderr output."""
    stderr_lower = stderr.lower()
    if 'success' in stderr_lower or 'running on port' in stderr_lower:
        print(f'Server info: {stderr.strip()}')
    elif 'warning' in stderr_lower or 'warn' in stderr_lower:
        print(f'Server warning: {stderr.strip()}')
    else:
        print(f'Server error: {stderr.strip()}')

def get_agent_type_from_model(model: str) -> str:
    """
    Determine the agent type based on the model name.

    Args:
        model: The model name (e.g., "gpt-4", "gemini-pro", "grok-1")

    Returns:
        Agent type string ("openai", "gemini", "grok")
    """
    if not model:
        return 'openai'
    model_lower = model.lower()
    for key, models in MODEL_MAPPINGS.items():
        if model_lower in models:
            return key
    raise ValueError(f'Unknown model: {model}')

@mcp.tool()
def get_events(day: str) -> str:
    """Get events for a day"""
    events = {'wednesday': 'Team meeting at 10 AM', 'friday': 'Previews at 10 AM, Deploy at 4 PM'}
    return events.get(day.lower(), f'No events for {day}')

def test_turn1_context():
    """Test context building for the first turn (no history)."""
    print('🔷 TURN 1 CONTEXT BUILDING')
    print('Scenario: User asks initial question, no conversation history')
    templates = MessageTemplates()
    conversation = templates.build_conversation_with_context(current_task='What are the main benefits of renewable energy?', conversation_history=[], agent_summaries=None, valid_agent_ids=None)
    print_message_structure('Turn 1: Initial Question', conversation)
    user_msg = conversation['user_message']
    has_history = 'CONVERSATION_HISTORY' in user_msg
    has_original = 'ORIGINAL MESSAGE' in user_msg
    has_answers = 'CURRENT ANSWERS' in user_msg and 'no answers available yet' in user_msg
    print('\n✅ VALIDATION:')
    print(f'   Contains conversation history section: {has_history}')
    print(f'   Contains original message section: {has_original}')
    print(f'   Contains empty answers section: {has_answers}')
    print(f'   System message mentions context: {'conversation' in conversation['system_message'].lower()}')

def test_turn2_context():
    """Test context building for the second turn (with history)."""
    print('\n🔷 TURN 2 CONTEXT BUILDING')
    print('Scenario: User asks follow-up, with previous exchange in history')
    templates = MessageTemplates()
    conversation_history = [{'role': 'user', 'content': 'What are the main benefits of renewable energy?'}, {'role': 'assistant', 'content': 'Renewable energy offers several key benefits including environmental sustainability, economic advantages, and energy security. It reduces greenhouse gas emissions, creates jobs, and decreases dependence on fossil fuel imports.'}]
    conversation = templates.build_conversation_with_context(current_task='What about the challenges and limitations?', conversation_history=conversation_history, agent_summaries={'researcher': 'Key benefits include environmental and economic advantages.'}, valid_agent_ids=['researcher'])
    print_message_structure('Turn 2: Follow-up with History', conversation)
    user_msg = conversation['user_message']
    has_history = 'CONVERSATION_HISTORY' in user_msg and 'User: What are the main benefits' in user_msg
    has_original = 'ORIGINAL MESSAGE' in user_msg and 'challenges and limitations' in user_msg
    has_answers = 'CURRENT ANSWERS' in user_msg and 'researcher' in user_msg
    print('\n✅ VALIDATION:')
    print(f'   Contains conversation history: {has_history}')
    print(f'   Contains current question: {has_original}')
    print(f'   Contains agent answers: {has_answers}')
    print(f'   System message is context-aware: {'conversation' in conversation['system_message'].lower()}')

def test_turn3_context():
    """Test context building for the third turn (extended history)."""
    print('\n🔷 TURN 3 CONTEXT BUILDING')
    print('Scenario: User asks third question, with extended conversation history')
    templates = MessageTemplates()
    conversation_history = [{'role': 'user', 'content': 'What are the main benefits of renewable energy?'}, {'role': 'assistant', 'content': 'Renewable energy offers environmental, economic, and energy security benefits.'}, {'role': 'user', 'content': 'What about the challenges and limitations?'}, {'role': 'assistant', 'content': 'Main challenges include high upfront costs, intermittency issues, and infrastructure requirements.'}]
    conversation = templates.build_conversation_with_context(current_task='How can governments support the transition?', conversation_history=conversation_history, agent_summaries={'researcher': 'Benefits include environmental and economic advantages.', 'analyst': 'Challenges include costs, intermittency, and infrastructure needs.'}, valid_agent_ids=['researcher', 'analyst'])
    print_message_structure('Turn 3: Extended Conversation', conversation)
    user_msg = conversation['user_message']
    has_full_history = 'CONVERSATION_HISTORY' in user_msg and user_msg.count('User:') >= 2
    has_original = 'ORIGINAL MESSAGE' in user_msg and 'governments support' in user_msg
    has_multiple_answers = 'CURRENT ANSWERS' in user_msg and 'researcher' in user_msg and ('analyst' in user_msg)
    print('\n✅ VALIDATION:')
    print(f'   Contains full conversation history: {has_full_history}')
    print(f'   Contains current question: {has_original}')
    print(f'   Contains multiple agent answers: {has_multiple_answers}')
    print(f'   History shows progression: {user_msg.count('User:') >= 2}')

def test_context_comparison():
    """Compare context building across different turns."""
    print('\n🔍 CONTEXT COMPARISON ACROSS TURNS')
    print('=' * 80)
    templates = MessageTemplates()
    conv1 = templates.build_conversation_with_context(current_task='What is solar energy?', conversation_history=[], agent_summaries=None)
    history = [{'role': 'user', 'content': 'What is solar energy?'}, {'role': 'assistant', 'content': 'Solar energy is power derived from sunlight.'}]
    conv2 = templates.build_conversation_with_context(current_task='How efficient is it?', conversation_history=history, agent_summaries={'expert': 'Solar energy harnesses sunlight for power generation.'})
    extended_history = [{'role': 'user', 'content': 'What is solar energy?'}, {'role': 'assistant', 'content': 'Solar energy is power derived from sunlight.'}, {'role': 'user', 'content': 'How efficient is it?'}, {'role': 'assistant', 'content': 'Modern solar panels achieve 15-22% efficiency.'}]
    conv3 = templates.build_conversation_with_context(current_task='What are the costs?', conversation_history=extended_history, agent_summaries={'expert': 'Solar energy harnesses sunlight for power generation.', 'engineer': 'Modern panels achieve 15-22% efficiency.'})
    print('📊 CONTEXT SIZE PROGRESSION:')
    print(f'   Turn 1 (no history):     {len(conv1['user_message']):,} chars')
    print(f'   Turn 2 (with history):   {len(conv2['user_message']):,} chars')
    print(f'   Turn 3 (extended):       {len(conv3['user_message']):,} chars')
    print('\n📈 CONTEXT ELEMENTS:')
    elements = ['CONVERSATION_HISTORY', 'ORIGINAL MESSAGE', 'CURRENT ANSWERS']
    for i, (conv, turn) in enumerate([(conv1, 'Turn 1'), (conv2, 'Turn 2'), (conv3, 'Turn 3')], 1):
        user_msg = conv['user_message']
        print(f'\n   {turn}:')
        for element in elements:
            present = element in user_msg
            print(f'     {element}: {('✅' if present else '❌')}')
        if 'CONVERSATION_HISTORY' in user_msg:
            exchange_count = user_msg.count('User:')
            print(f'     Previous exchanges: {exchange_count}')

