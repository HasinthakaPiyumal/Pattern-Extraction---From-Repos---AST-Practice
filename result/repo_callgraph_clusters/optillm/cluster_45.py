# Cluster 45

class AutoThinkProcessor:
    """
    Main AutoThink processor class for external use.
    Wraps the internal processor implementation.
    """

    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, config: Dict[str, Any]=None):
        """
        Initialize the AutoThink processor.
        
        Args:
            model: Language model
            tokenizer: Model tokenizer
            config: Configuration dictionary
        """
        self.config = config or {}
        self.processor = None
        self.model = model
        self.tokenizer = tokenizer

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        """Process messages with AutoThink's controlled thinking."""
        return self.process(messages)

    def process(self, messages: List[Dict[str, str]]) -> str:
        """Process messages with AutoThink's controlled thinking.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated response
        """
        if self.processor is None:
            self.processor = self._create_processor()
        return self.processor.process(messages)

    def _create_processor(self):
        """Create the internal processor instance."""
        return InternalProcessor(self.config, self.tokenizer, self.model)

def _create_processor(self):
    """Create the internal processor instance."""
    return InternalProcessor(self.config, self.tokenizer, self.model)

