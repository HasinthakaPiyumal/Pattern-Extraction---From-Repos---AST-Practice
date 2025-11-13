# Cluster 32

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

def __init__(self, display_enabled: bool=True, stream_callback: Optional[Callable]=None, max_lines: int=10, save_logs: bool=True, answers_dir: Optional[str]=None):
    self.display = MultiRegionDisplay(display_enabled, max_lines, save_logs, answers_dir)
    self.stream_callback = stream_callback

