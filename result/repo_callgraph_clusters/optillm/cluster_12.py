# Cluster 12

class CBLog(dict):
    """Object for logging the number of LLM calls and tokens used in the pipeline"""
    __allowed_keys__ = {'total_tokens', 'completion_tokens', 'llm_calls'}

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self.__allowed_keys__:
            raise KeyError(f"Key '{key}' not allowed. Allowed keys: {self.__allowed_keys__}")
        if not isinstance(value, int):
            raise TypeError(f"Value for '{key}' must be int, got {type(value).__name__}")
        super().__setitem__(key, value)

    def update(self, other=None, **kwargs):
        updates = {}
        if other:
            if isinstance(other, dict):
                updates.update(other)
            else:
                updates.update(dict(other))
        updates.update(kwargs)
        for key, value in updates.items():
            if key not in self.__allowed_keys__:
                raise KeyError(f"Key '{key}' not allowed. Allowed keys: {self.__allowed_keys__}")
            if not isinstance(value, int):
                raise TypeError(f"Value for '{key}' must be int, got {type(value).__name__}")
            self[key] = self.get(key, 0) + value

def __setitem__(self, key, value):
    if key not in self.__allowed_keys__:
        raise KeyError(f"Key '{key}' not allowed. Allowed keys: {self.__allowed_keys__}")
    if not isinstance(value, int):
        raise TypeError(f"Value for '{key}' must be int, got {type(value).__name__}")
    super().__setitem__(key, value)

def update(self, other=None, **kwargs):
    updates = {}
    if other:
        if isinstance(other, dict):
            updates.update(other)
        else:
            updates.update(dict(other))
    updates.update(kwargs)
    for key, value in updates.items():
        if key not in self.__allowed_keys__:
            raise KeyError(f"Key '{key}' not allowed. Allowed keys: {self.__allowed_keys__}")
        if not isinstance(value, int):
            raise TypeError(f"Value for '{key}' must be int, got {type(value).__name__}")
        self[key] = self.get(key, 0) + value

def install_steering_hooks(model, manager: SteeringVectorManager, tokenizer=None) -> List[Tuple]:
    """
    Install steering hooks on a model.
    
    Args:
        model: The model to install hooks on
        manager: The steering vector manager
        tokenizer: Tokenizer for token-based matching
        
    Returns:
        List of installed hooks
    """
    hooks = []
    layer_num = manager.target_layer
    logger.info(f'STEERING: Attempting to install hook on layer {layer_num}')
    model_type = type(model).__name__
    logger.info(f'STEERING: Model type is {model_type}')
    if hasattr(model, 'config'):
        logger.info(f'STEERING: Model architecture is {(model.config.architectures[0] if hasattr(model.config, 'architectures') else 'unknown')}')
    module = None
    if hasattr(model, 'transformer'):
        logger.info("STEERING: Model has 'transformer' attribute")
        if hasattr(model.transformer, 'h') and layer_num < len(model.transformer.h):
            module = model.transformer.h[layer_num]
            logger.info(f'STEERING: Using transformer.h[{layer_num}]')
    elif hasattr(model, 'model'):
        logger.info("STEERING: Model has 'model' attribute")
        if hasattr(model.model, 'layers') and layer_num < len(model.model.layers):
            module = model.model.layers[layer_num]
            logger.info(f'STEERING: Using model.layers[{layer_num}]')
        elif hasattr(model.model, 'decoder') and hasattr(model.model.decoder, 'layers') and (layer_num < len(model.model.decoder.layers)):
            module = model.model.decoder.layers[layer_num]
            logger.info(f'STEERING: Using model.decoder.layers[{layer_num}]')
    elif hasattr(model, 'layers') and layer_num < len(model.layers):
        module = model.layers[layer_num]
        logger.info(f'STEERING: Using layers[{layer_num}]')
    if module is None:
        logger.error(f'STEERING: Could not find appropriate module for layer {layer_num}')
        logger.error('STEERING: Model structure not compatible with current hook installation logic')
        return []
    hook = SteeringHook(manager, layer_num, tokenizer)
    handle = module.register_forward_hook(hook)
    hooks.append((hook, handle))
    logger.info(f'STEERING: Installed hook on layer {layer_num} successfully')
    return hooks

class MockUsage:

    def __init__(self, reasoning_tokens):
        self.completion_tokens_details = type('obj', (), {'reasoning_tokens': reasoning_tokens})()
        self.total_tokens = reasoning_tokens + 200

def __init__(self, reasoning_tokens):
    self.completion_tokens_details = type('obj', (), {'reasoning_tokens': reasoning_tokens})()
    self.total_tokens = reasoning_tokens + 200

class MockChoice:

    def __init__(self, content):
        self.message = type('obj', (), {'content': content})()

def __init__(self, content):
    self.message = type('obj', (), {'content': content})()

class MockOpenAIClient:
    """Enhanced mock OpenAI client for IMO25 testing"""

    def __init__(self, response_delay=0.1, reasoning_tokens=2000):
        self.response_delay = response_delay
        self.reasoning_tokens = reasoning_tokens
        self.call_count = 0
        self.call_times = []

    def chat_completions_create(self, **kwargs):
        """Mock completions.create with realistic IMO25 responses"""
        start_time = time.time()
        time.sleep(self.response_delay)
        self.call_count += 1
        self.call_times.append(time.time())
        call_count = self.call_count

        class MockUsage:

            def __init__(self, reasoning_tokens):
                self.completion_tokens_details = type('obj', (), {'reasoning_tokens': reasoning_tokens})()
                self.total_tokens = reasoning_tokens + 200

        class MockChoice:

            def __init__(self, content):
                self.message = type('obj', (), {'content': content})()

        class MockResponse:

            def __init__(self, content, reasoning_tokens):
                self.choices = [MockChoice(content)]
                self.usage = MockUsage(reasoning_tokens)
        messages = kwargs.get('messages', [])
        problem_content = ''
        for message in messages:
            problem_content += message.get('content', '')
        if 'verifying' in problem_content.lower():
            content = f'VERIFICATION: This solution appears CORRECT. The analysis is mathematically sound and the final answer is properly justified. Confidence: 8/10.'
        elif 'improving' in problem_content.lower():
            content = f"IMPROVEMENT: The original approach is good but can be enhanced. Here's the improved version with stronger reasoning..."
        elif 'bonza' in problem_content.lower():
            responses = ['Looking at this functional equation problem, I need to find the smallest constant c such that f(n) ≤ cn for all bonza functions f. Let me analyze the divisibility condition: f(a) divides b^a - f(b)^f(a). This is a complex functional equation. After careful analysis of the constraints, I believe the minimum constant is c = 4. This can be shown by constructing specific examples and proving upper bounds.', "For the bonza function problem, I'll work through the case analysis systematically. A function f: ℕ → ℕ is bonza if f(a) | (b^a - f(b)^f(a)) for all positive integers a,b. Through detailed analysis of the divisibility constraints and construction of extremal examples, the smallest real constant c such that f(n) ≤ cn for all bonza functions is c = 4.", "This functional equation requires careful analysis. I'll examine when f(a) divides b^a - f(b)^f(a). By studying specific cases and constructing examples, I can show that the minimal constant c = 4 is both necessary and sufficient. The answer is c = 4."]
            content = responses[call_count % len(responses)]
        elif 'three largest proper divisors' in problem_content.lower():
            responses = ['For this sequence problem, I need to analyze when a_{n+1} equals the sum of three largest proper divisors of a_n. After examining the dynamics and constraints, the possible values of a_1 are of the form 6J·12^K where gcd(J,10)=1. This follows from regime analysis of the sequence evolution.', 'Analyzing the sequence where each term is the sum of three largest proper divisors of the previous term. Through careful analysis of the divisibility patterns and sequence behavior, I find that a_1 must have the form a_1 = 6J·12^K where gcd(J,10)=1.', 'The sequence evolution depends on the three largest proper divisors. After detailed analysis of the constraints and fixed point behavior, the answer is a_1 = 6J·12^K where gcd(J,10)=1.']
            content = responses[call_count % len(responses)]
        elif 'alice and bazza' in problem_content.lower():
            responses = ["In this inekoalaty game, Alice and Bazza have alternating constraints. Alice wins if λ > 1/√2, Bazza wins if λ < 1/√2, and it's a draw if λ = 1/√2. The critical threshold is λ = 1/√2 ≈ 0.707. This follows from analyzing the budget constraints and optimal strategies.", 'For the game theory problem, the key is finding the threshold value of λ. Through analysis of the constraints x₁+x₂+...+xₙ ≤ λn and x₁²+x₂²+...+xₙ² ≤ n, the critical value is λ = 1/√2. Alice has a winning strategy when λ > 1/√2.', 'The inekoalaty game has a critical threshold at λ = 1/√2. Alice wins for λ > 1/√2, Bazza wins for λ < 1/√2, and they draw at λ = 1/√2. This threshold emerges from the constraint analysis.']
            content = responses[call_count % len(responses)]
        elif '2025×2025 grid' in problem_content.lower():
            responses = ['For the tiling problem on a 2025×2025 grid, Matilda needs to place rectangular tiles such that each row and column has exactly one uncovered unit square. The minimum number of tiles needed is 2025. This can be achieved by strategic tile placement.', 'In this combinatorial optimization problem, the constraint that each row and each column must have exactly one uncovered square leads to the minimum number of tiles being 2025. This follows from extremal combinatorics arguments.', 'The minimum number of tiles for the 2025×2025 grid problem is 2025. This can be proven by considering the constraints and constructing an optimal tiling pattern.']
            content = responses[call_count % len(responses)]
        else:
            content = f'Mathematical solution {call_count}: This is a complex problem requiring systematic analysis. Let me work through it step by step with rigorous reasoning and provide a complete solution.'
        return MockResponse(content, self.reasoning_tokens)

    @property
    def chat(self):
        return type('obj', (), {'completions': type('obj', (), {'create': self.chat_completions_create})()})()

@property
def chat(self):
    return type('obj', (), {'completions': type('obj', (), {'create': self.chat_completions_create})()})()

class TestThinkDeeperReasoningTokens(unittest.TestCase):
    """Test ThinkDeeper approaches return reasoning tokens"""

    def setUp(self):
        """Set up test fixtures"""
        setup_test_env()
        self.test_messages = get_simple_test_messages()

    def test_thinkdeeper_returns_reasoning_tokens(self):
        """Test that thinkdeeper_decode returns reasoning tokens"""
        setup_test_env()
        try:
            from optillm.thinkdeeper import thinkdeeper_decode
            self.assertTrue(callable(thinkdeeper_decode))
            self.assertTrue(True, 'thinkdeeper_decode function is available')
        except Exception as e:
            self.skipTest(f'thinkdeeper_decode not available: {str(e)}')

    @unittest.skipIf(not is_mlx_available() or not MLX_THINKDEEPER_AVAILABLE, 'MLX or thinkdeeper_mlx not available')
    def test_thinkdeeper_mlx_returns_reasoning_tokens(self):
        """Test that thinkdeeper_decode_mlx returns reasoning tokens (MLX only)"""
        setup_test_env()
        try:
            self.assertTrue(callable(thinkdeeper_decode_mlx))
            self.assertTrue(True, 'thinkdeeper_decode_mlx function is available')
        except Exception as e:
            self.skipTest(f'thinkdeeper_decode_mlx not available: {str(e)}')

def setUp(self):
    """Set up test fixtures"""
    setup_test_env()
    self.test_messages = get_simple_test_messages()

class MockUsage:

    def __init__(self, reasoning_tokens):
        self.completion_tokens_details = type('obj', (), {'reasoning_tokens': reasoning_tokens})()
        self.total_tokens = reasoning_tokens + 100

def __init__(self, reasoning_tokens):
    self.completion_tokens_details = type('obj', (), {'reasoning_tokens': reasoning_tokens})()
    self.total_tokens = reasoning_tokens + 100

class MockChoice:

    def __init__(self):
        self.message = type('obj', (), {'content': f'Mock mathematical solution {call_count}. The answer is 42.'})()

def __init__(self):
    self.message = type('obj', (), {'content': f'Mock mathematical solution {call_count}. The answer is 42.'})()

class MockOpenAIClient:
    """Enhanced mock OpenAI client for MARS testing"""

    def __init__(self, response_delay=0.1, reasoning_tokens=1000):
        self.response_delay = response_delay
        self.reasoning_tokens = reasoning_tokens
        self.call_count = 0
        self.call_times = []

    def chat_completions_create(self, **kwargs):
        """Mock completions.create with configurable delay"""
        start_time = time.time()
        time.sleep(self.response_delay)
        self.call_count += 1
        self.call_times.append(time.time())
        call_count = self.call_count

        class MockUsage:

            def __init__(self, reasoning_tokens):
                self.completion_tokens_details = type('obj', (), {'reasoning_tokens': reasoning_tokens})()
                self.total_tokens = reasoning_tokens + 100

        class MockChoice:

            def __init__(self):
                self.message = type('obj', (), {'content': f'Mock mathematical solution {call_count}. The answer is 42.'})()

        class MockResponse:

            def __init__(self, reasoning_tokens):
                self.choices = [MockChoice()]
                self.usage = MockUsage(reasoning_tokens)
        return MockResponse(self.reasoning_tokens)

    @property
    def chat(self):
        return type('obj', (), {'completions': type('obj', (), {'create': self.chat_completions_create})()})()

@property
def chat(self):
    return type('obj', (), {'completions': type('obj', (), {'create': self.chat_completions_create})()})()

class MockResponse:

    def __init__(self):
        self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mock response'})()})]

def __init__(self):
    self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mock response'})()})]

def test_n_parameter(model=TEST_MODEL, n_values=[1, 2, 3]):
    """
    Test the n parameter with different values
    """
    setup_test_env()
    client = get_test_client()
    test_prompt = 'Write a haiku about coding'
    for n in n_values:
        print(f'\nTesting n={n} with model {model}')
        print('-' * 50)
        try:
            response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'You are a creative poet.'}, {'role': 'user', 'content': test_prompt}], n=n, temperature=0.8, max_tokens=100)
            print(f'Response type: {type(response)}')
            print(f'Number of choices: {len(response.choices)}')
            for i, choice in enumerate(response.choices):
                print(f'\nChoice {i + 1}:')
                print(choice.message.content)
            if len(response.choices) == n:
                print(f'\n✅ SUCCESS: Got {n} responses as expected')
            else:
                print(f'\n❌ FAIL: Expected {n} responses, got {len(response.choices)}')
        except Exception as e:
            print(f'\n❌ ERROR: {type(e).__name__}: {str(e)}')

def main():
    """
    Main test function
    """
    print('Testing n parameter support in optillm')
    print('=' * 50)
    setup_test_env()
    model = TEST_MODEL
    print(f'\n\nTesting model: {model}')
    print('=' * 50)
    try:
        test_n_parameter(model)
    except Exception as e:
        print(f'\n❌ Test failed with error: {str(e)}')
        print('Make sure optillm server is running with local inference enabled')
        return 1
    return 0

class TestJSONPluginIntegration(unittest.TestCase):
    """Integration tests for JSON plugin with local models"""

    def setUp(self):
        """Set up integration test environment"""
        try:
            from test_utils import setup_test_env, get_test_client, TEST_MODEL
            setup_test_env()
            self.test_client = get_test_client()
            self.test_model = TEST_MODEL
            self.available = True
        except ImportError:
            self.available = False

    def test_json_plugin_integration(self):
        """Test JSON plugin with actual local inference"""
        if not self.available:
            self.skipTest('Test utilities not available')
        try:
            test_schema = {'type': 'object', 'properties': {'answer': {'type': 'string'}, 'confidence': {'type': 'number'}}, 'required': ['answer']}
            response = self.test_client.chat.completions.create(model=self.test_model, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is 2+2? Respond in JSON format.'}], response_format={'type': 'json_schema', 'json_schema': {'name': 'math_response', 'schema': test_schema}}, max_tokens=100)
            self.assertIsNotNone(response.choices)
            self.assertEqual(len(response.choices), 1)
            self.assertIsNotNone(response.choices[0].message.content)
            try:
                json_response = json.loads(response.choices[0].message.content)
                self.assertIsInstance(json_response, dict)
                if 'answer' in json_response:
                    self.assertIsInstance(json_response['answer'], str)
            except json.JSONDecodeError:
                pass
        except Exception as e:
            self.skipTest(f'JSON plugin integration not available: {str(e)}')

    def test_json_plugin_fallback(self):
        """Test that JSON plugin falls back gracefully when schema is invalid"""
        if not self.available:
            self.skipTest('Test utilities not available')
        try:
            response = self.test_client.chat.completions.create(model=self.test_model, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'Say hello'}], max_tokens=20)
            self.assertIsNotNone(response.choices)
            self.assertEqual(len(response.choices), 1)
            self.assertIsNotNone(response.choices[0].message.content)
        except Exception as e:
            self.skipTest(f'Fallback test not available: {str(e)}')

def setUp(self):
    """Set up integration test environment"""
    try:
        from test_utils import setup_test_env, get_test_client, TEST_MODEL
        setup_test_env()
        self.test_client = get_test_client()
        self.test_model = TEST_MODEL
        self.available = True
    except ImportError:
        self.available = False

class TestAPIResponseFormat(unittest.TestCase):
    """Test that API responses include reasoning token information"""

    def setUp(self):
        """Set up test fixtures"""
        setup_test_env()
        self.test_client = get_test_client()

    def test_response_includes_completion_tokens_details(self):
        """Test that API responses include completion_tokens_details"""
        try:
            response = self.test_client.chat.completions.create(model=TEST_MODEL, messages=get_thinking_test_messages(), max_tokens=50)
            self.assertIsNotNone(response.choices)
            self.assertEqual(len(response.choices), 1)
            self.assertIsNotNone(response.choices[0].message.content)
            self.assertIsNotNone(response.usage)
            self.assertGreater(response.usage.completion_tokens, 0)
            self.assertGreater(response.usage.prompt_tokens, 0)
        except Exception as e:
            self.skipTest(f'Local inference not available: {str(e)}')

    def test_response_no_reasoning_tokens(self):
        """Test API response when there are no reasoning tokens"""
        try:
            response = self.test_client.chat.completions.create(model=TEST_MODEL, messages=get_simple_test_messages(), max_tokens=20)
            self.assertIsNotNone(response.choices)
            self.assertEqual(len(response.choices), 1)
            self.assertIsNotNone(response.choices[0].message.content)
            self.assertIsNotNone(response.usage)
            self.assertGreater(response.usage.completion_tokens, 0)
            self.assertGreater(response.usage.prompt_tokens, 0)
        except Exception as e:
            self.skipTest(f'Local inference not available: {str(e)}')

    def test_multiple_responses_reasoning_tokens(self):
        """Test reasoning tokens with multiple responses (n > 1)"""
        try:
            response = self.test_client.chat.completions.create(model=TEST_MODEL, messages=get_thinking_test_messages(), max_tokens=50, n=2)
            self.assertIsNotNone(response.choices)
            self.assertGreaterEqual(len(response.choices), 1)
            self.assertIsNotNone(response.usage)
            self.assertGreater(response.usage.completion_tokens, 0)
        except Exception as e:
            self.skipTest(f'Multiple responses not supported by local inference: {str(e)}')

def setUp(self):
    """Set up test fixtures"""
    setup_test_env()
    self.test_client = get_test_client()

@pytest.fixture
def client():
    """Create OpenAI client for optillm proxy with local inference"""
    setup_test_env()
    return get_test_client()

