# Cluster 30

@dataclass
class LogEntry:
    """Represents a single log entry in the MassGen system."""
    timestamp: float
    event_type: str
    agent_id: Optional[int]
    phase: str
    data: Dict[str, Any]
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for JSON serialization."""
    return asdict(self)

