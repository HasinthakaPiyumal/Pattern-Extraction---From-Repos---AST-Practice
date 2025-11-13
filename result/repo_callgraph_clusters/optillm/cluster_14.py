# Cluster 14

class MockResponse:

    def __init__(self, content, reasoning_tokens):
        self.choices = [MockChoice(content)]
        self.usage = MockUsage(reasoning_tokens)

def __init__(self, content, reasoning_tokens):
    self.choices = [MockChoice(content)]
    self.usage = MockUsage(reasoning_tokens)

class MockResponse:

    def __init__(self, reasoning_tokens):
        self.choices = [MockChoice()]
        self.usage = MockUsage(reasoning_tokens)

def __init__(self, reasoning_tokens):
    self.choices = [MockChoice()]
    self.usage = MockUsage(reasoning_tokens)

class Completions:

    def create(self, **kwargs):

        class MockChoice:

            class Message:
                content = 'Test response: 2 + 2 = 4'
            message = Message()

        class MockUsage:
            completion_tokens = 10
            total_tokens = 20

        class MockResponse:
            choices = [MockChoice()]
            usage = MockUsage()
        return MockResponse()

def create(self, **kwargs):

    class MockChoice:

        class Message:
            content = 'Test response: 2 + 2 = 4'
        message = Message()

    class MockUsage:
        completion_tokens = 10
        total_tokens = 20

    class MockResponse:
        choices = [MockChoice()]
        usage = MockUsage()
    return MockResponse()

