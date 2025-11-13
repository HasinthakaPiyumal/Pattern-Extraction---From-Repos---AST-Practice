# Cluster 25

class ChatCompletionChoice:

    def __init__(self, index: int, message: Dict[str, Any], finish_reason: str='stop', logprobs: Optional[Dict]=None):
        self.index = index
        self.message = ChatCompletionMessage(**message)
        self.finish_reason = finish_reason
        if logprobs:
            self.message.logprobs = logprobs

def __init__(self, index: int, message: Dict[str, Any], finish_reason: str='stop', logprobs: Optional[Dict]=None):
    self.index = index
    self.message = ChatCompletionMessage(**message)
    self.finish_reason = finish_reason
    if logprobs:
        self.message.logprobs = logprobs

