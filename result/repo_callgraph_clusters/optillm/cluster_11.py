# Cluster 11

def prepare_safe_globals():
    safe_globals = {'print': print, '__builtins__': {'True': True, 'False': False, 'None': None, 'abs': abs, 'float': float, 'int': int, 'len': len, 'max': max, 'min': min, 'round': round, 'sum': sum, 'complex': complex}}
    safe_globals.update({'log': math.log, 'log2': math.log2, 'sqrt': math.sqrt, 'exp': math.exp, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'pi': math.pi, 'e': math.e})
    safe_globals['I'] = complex(0, 1)
    safe_globals['Complex'] = complex
    return safe_globals

def execute_code_in_process(code: str):
    import z3
    import sympy
    import math
    import itertools
    from fractions import Fraction
    safe_globals = prepare_safe_globals()
    z3_whitelist = set(dir(z3))
    safe_globals.update({name: getattr(z3, name) for name in z3_whitelist})
    sympy_whitelist = set(dir(sympy))
    safe_globals.update({name: getattr(sympy, name) for name in sympy_whitelist})
    safe_globals.update({'z3': z3, 'sympy': sympy, 'Solver': z3.Solver, 'solver': z3.Solver, 'Optimize': z3.Optimize, 'sat': z3.sat, 'unsat': z3.unsat, 'unknown': z3.unknown, 'Real': z3.Real, 'Int': z3.Int, 'Bool': z3.Bool, 'And': z3.And, 'Or': z3.Or, 'Not': z3.Not, 'Implies': z3.Implies, 'If': z3.If, 'Sum': z3.Sum, 'ForAll': z3.ForAll, 'Exists': z3.Exists, 'model': z3.Model, 'Symbol': sympy.Symbol, 'solve': sympy.solve, 'simplify': sympy.simplify, 'expand': sympy.expand, 'factor': sympy.factor, 'diff': sympy.diff, 'integrate': sympy.integrate, 'limit': sympy.limit, 'series': sympy.series})

    def as_numerical(x):
        if z3.is_expr(x):
            if z3.is_int_value(x) or z3.is_rational_value(x):
                return float(x.as_decimal(20))
            elif z3.is_algebraic_value(x):
                return x.approx(20)
        return float(x)
    safe_globals['as_numerical'] = as_numerical

    def Mod(x, y):
        return x % y
    safe_globals['Mod'] = Mod

    def Rational(numerator, denominator=1):
        return z3.Real(str(Fraction(numerator, denominator)))
    safe_globals['Rational'] = Rational
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        try:
            exec(code, safe_globals, {})
        except Exception:
            return ('error', traceback.format_exc())
    return ('success', output_buffer.getvalue())

def load_plugins():
    plugin_approaches.clear()
    import optillm
    package_plugin_dir = os.path.join(os.path.dirname(optillm.__file__), 'plugins')
    current_dir = os.getcwd() if server_config.get('plugins_dir', '') == '' else server_config['plugins_dir']
    local_plugin_dir = os.path.join(current_dir, 'optillm', 'plugins')
    plugin_dirs = []
    plugin_dirs.append((package_plugin_dir, 'package'))
    if local_plugin_dir != package_plugin_dir:
        plugin_dirs.append((local_plugin_dir, 'local'))
    for plugin_dir, source in plugin_dirs:
        logger.info(f'Looking for {source} plugins in: {plugin_dir}')
        if not os.path.exists(plugin_dir):
            logger.debug(f'{source.capitalize()} plugin directory not found: {plugin_dir}')
            continue
        plugin_files = glob.glob(os.path.join(plugin_dir, '*.py'))
        if not plugin_files:
            logger.debug(f'No plugin files found in {source} directory: {plugin_dir}')
            continue
        logger.info(f'Found {source} plugin files: {plugin_files}')
        for plugin_file in plugin_files:
            try:
                module_name = os.path.basename(plugin_file)[:-3]
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'SLUG') and hasattr(module, 'run'):
                    if module.SLUG in plugin_approaches:
                        logger.info(f'Overriding {source} plugin: {module.SLUG}')
                    plugin_approaches[module.SLUG] = module.run
                    logger.info(f'Loaded {source} plugin: {module.SLUG}')
                else:
                    logger.warning(f'Plugin {module_name} from {source} missing required attributes (SLUG and run)')
            except Exception as e:
                logger.error(f'Error loading {source} plugin {plugin_file}: {str(e)}')
    if not plugin_approaches:
        logger.warning('No plugins loaded from any location')

def get_config_path():
    import optillm
    package_config_dir = os.path.join(os.path.dirname(optillm.__file__), 'cepo', 'configs')
    package_config_path = os.path.join(package_config_dir, 'cepo_config.yaml')
    current_dir = os.getcwd() if server_config.get('config_dir', '') == '' else server_config['config_dir']
    local_config_dir = os.path.join(current_dir, 'optillm', 'cepo', 'configs')
    local_config_path = os.path.join(local_config_dir, 'cepo_config.yaml')
    if os.path.exists(local_config_path) and local_config_path != package_config_path:
        logger.debug(f'Using local config from: {local_config_path}')
        return local_config_path
    logger.debug(f'Using package config from: {package_config_path}')
    return package_config_path

def run(system_prompt: str, initial_query: str, client, model: str) -> Tuple[str, int]:
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    longcepo_dir = os.path.join(plugin_dir, 'longcepo')
    main_file = os.path.join(longcepo_dir, 'main.py')
    spec = importlib.util.spec_from_file_location('longcepo_main', main_file)
    longcepo_main = importlib.util.module_from_spec(spec)
    if longcepo_dir not in sys.path:
        sys.path.insert(0, longcepo_dir)
    try:
        spec.loader.exec_module(longcepo_main)
        return longcepo_main.run_longcepo(system_prompt, initial_query, client, model)
    finally:
        if longcepo_dir in sys.path:
            sys.path.remove(longcepo_dir)

def run(system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Tuple[str, int]:
    """
    Plugin entry point for System Prompt Learning.
    
    Args:
        system_prompt: The system prompt
        initial_query: The user's query
        client: The LLM client
        model: The model identifier
        request_config: Optional request configuration
                       Can include {'spl_learning': True} to enable learning mode
    
    Returns:
        Tuple[str, int]: The LLM response and token count
    """
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    spl_dir = os.path.join(plugin_dir, 'spl')
    main_file = os.path.join(spl_dir, 'main.py')
    spec = importlib.util.spec_from_file_location('spl_main', main_file)
    spl_main = importlib.util.module_from_spec(spec)
    if spl_dir not in sys.path:
        sys.path.insert(0, spl_dir)
    try:
        spec.loader.exec_module(spl_main)
        return spl_main.run_spl(system_prompt, initial_query, client, model, request_config)
    finally:
        if spl_dir in sys.path:
            sys.path.remove(spl_dir)

def mapreduce(system_prompt: str, query: str, context: str, qa_history: str, client, model: str, tokenizer, longcepo_config: LongCepoConfig, cb_log: CBLog, answer_tags: Tuple[str]=('Answer:', '**Answer**:', '**Answer**'), irrelevance_tags: Tuple[str]=('[NO INFORMATION]',)) -> Tuple[str, CBLog]:
    """
    Executes a MapReduce-style inference pipeline to answer a query from long context.

    The function splits the input context into chunks, summarizes and evaluates each with the model (Map),
    collapses intermediate answers to reduce redundancy, and then generates a final answer (Reduce).
    Irrelevant responses are filtered based on `irrelevance_tags`.

    Args:
        system_prompt (str): System prompt string.
        query (str): User query.
        context (str): Long-form input context to process.
        qa_history (str): QA history string for prompt injection.
        client: LLM API client.
        model (str): Base model name.
        tokenizer: Tokenizer to compute token lengths.
        longcepo_config (LongCepoConfig): Config with hyper-parameters and token limits.
        cb_log (CBLog): Log object for tracking model calls.
        answer_tags (Tuple[str]): Tags used to extract the final answer from model output.
        irrelevance_tags (Tuple[str]): Tags used to identify and remove irrelevant outputs.

    Returns:
        Tuple[str, CBLog]: Final extracted answer and updated log object.
    """
    logger.info(f'MapReduce query: {query}')
    qa_history_stub = f'\n\nAnswers to related questions:\n\n{qa_history}' if qa_history else ''
    context_chunks = chunk_context(context, longcepo_config.chunk_size, tokenizer)

    def fetch_chunk_summary(client, model, chunk, query, system_prompt):
        return get_prompt_response(client, model, longcepo_config.summary_prompt.format(question=query, context=chunk), system_prompt, max_tokens=longcepo_config.max_output_tokens_summary, temperature=longcepo_config.temperature_map)
    summaries, cb_log = concurrent_map(fetch_chunk_summary, client, model, context_chunks, query, system_prompt, cb_log)
    num_summaries = longcepo_config.num_neighbor_summaries
    summaries_per_chunk = ['\n\n'.join(summaries[max(0, summary_idx - num_summaries):min(len(summaries) - 1, summary_idx + num_summaries)]) for summary_idx in range(len(summaries))]

    def fetch_map_response(client, model, chunk, query, system_prompt, summary):
        return get_prompt_response(client, model, longcepo_config.map_prompt.format(question=query, context=chunk, summary=summary, qa_history_stub=qa_history_stub), system_prompt, max_tokens=longcepo_config.max_output_tokens, temperature=longcepo_config.temperature_map)
    result, cb_log = concurrent_map(fetch_map_response, client, model, context_chunks, query, system_prompt, cb_log, summaries_per_chunk=summaries_per_chunk)
    result = remove_chunks(result, irrelevance_tags)
    if not result:
        return ('No information', cb_log)
    logger.info(f'Removed {len(context_chunks) - len(result)} chunks from total {len(context_chunks)} chunks')
    result, cb_log = collapse_chunks(client, model, result, query, system_prompt, qa_history_stub, tokenizer, cb_log, longcepo_config, irrelevance_tags)
    if not result:
        return ('No information', cb_log)
    prompt = longcepo_config.reduce_prompt.format(question=query, context=format_chunk_list(result), qa_history_stub=qa_history_stub)
    gen_fn = partial(get_prompt_response, client=client, model=model, prompt=prompt, system_prompt=system_prompt, max_tokens=longcepo_config.max_output_tokens, temperature=longcepo_config.temperature_reduce)
    reduce_result, upd_log = loop_until_match(gen_fn, answer_tags)
    cb_log.update(upd_log)
    final_answer = reduce_result
    for answer_tag in answer_tags:
        if answer_tag in reduce_result:
            final_answer = reduce_result.split(answer_tag)[-1].strip()
            break
    return (final_answer, cb_log)

def collapse_chunks(client, model: str, context_chunks: List[str], query: str, system_prompt: str, qa_history_stub: str, tokenizer, cb_log: CBLog, longcepo_config: LongCepoConfig, irrelevance_tags: Tuple[str]=('[NO INFORMATION]',)) -> Tuple[List[str], CBLog]:
    """
    Collapses context chunk pairs in sliding window until the total token count fits within the context window.

    Args:
        client: LLM API client.
        model (str): Base model name.
        context_chunks (List[str]): Input context chunks.
        query (str): User query.
        system_prompt (str): System prompt string.
        qa_history_stub (str): QA history prefix.
        tokenizer: Tokenizer to compute token lengths.
        cb_log (CBLog): Log object for tracking model calls.
        longcepo_config (LongCepoConfig): Config with hyper-parameters and token limits.

    Returns:
        Tuple[List[str], CBLog]: Final context chunks and updated logs.
    """
    num_tokens = get_prompt_length(format_chunk_list(context_chunks), tokenizer)
    token_budget = longcepo_config.max_context_window - get_prompt_length(longcepo_config.reduce_prompt, tokenizer) - longcepo_config.max_output_tokens
    logger.info(f'Pre-collapse length of chunks {num_tokens}, allowed {token_budget}')

    def fetch_collapse_response(client, model, docs, query, system_prompt):
        if len(docs) == 1:
            return (docs[0], CBLog())
        return get_prompt_response(client, model, longcepo_config.collapse_prompt.format(question=query, context='\n\n'.join(docs), qa_history_stub=qa_history_stub), system_prompt, max_tokens=longcepo_config.max_output_tokens, temperature=longcepo_config.temperature_collapse)
    merge_pair_idx = 0
    collapse_step = 0
    while num_tokens is not None and num_tokens > token_budget:
        logger.info(f'Length at collapse stage {collapse_step}: {collapse_step}')
        if len(context_chunks) == 1:
            logger.info(f'Post-collapse length of chunks {num_tokens}')
            return (context_chunks, cb_log)
        chunk_groups = [(context_chunks[i],) for i in range(merge_pair_idx)] + [(context_chunks[merge_pair_idx], context_chunks[merge_pair_idx + 1])] + [(context_chunks[i],) for i in range(merge_pair_idx + 2, len(context_chunks))]
        context_chunks, cb_log = concurrent_map(fetch_collapse_response, client, model, chunk_groups, query, system_prompt, cb_log)
        context_chunks = remove_chunks(context_chunks, irrelevance_tags)
        merge_pair_idx = (merge_pair_idx + 1) % max(len(context_chunks) - 1, 1)
        num_tokens = get_prompt_length(format_chunk_list(context_chunks), tokenizer)
        collapse_step += 1
    logger.info(f'Post-collapse length of chunks {num_tokens}')
    return (context_chunks, cb_log)

def run_longcepo(system_prompt: str, initial_query: str, client, model: str) -> Tuple[str, int]:
    """
    Executes the full LongCePO multi-stage pipeline to answer a complex query from long context.

    The pipeline includes:
      - Normalizing the format of the original query
      - Generating a plan of sub-questions
      - Iteratively answering each sub-question using a MapReduce-style question-answering engine
      - Aggregating QA history and producing a final answer with MapReduce

    Args:
        system_prompt (str): System prompt string.
        initial_query (str): Raw input string containing context and query separated by delimiter string.
        client: LLM API client instance.
        model (str): Base model name.

    Returns:
        Tuple[str, int]: Final answer and total number of tokens used across the pipeline.
    """
    context, query, tokenizer, cb_log, longcepo_config = longcepo_init(initial_query)
    normalized_query, upd_log = get_prompt_response(client, model, longcepo_config.query_format_prompt.format(full_query=query), system_prompt, max_tokens=longcepo_config.max_output_tokens)
    cb_log.update(upd_log)
    logger.info(f'Normalized query: {normalized_query}')
    prompt = f'The question is: {normalized_query}'
    gen_fn = partial(get_prompt_response, client=client, model=model, prompt=prompt, system_prompt=longcepo_config.planning_system_prompt, max_tokens=longcepo_config.max_output_tokens)
    planning_response, upd_log = loop_until_match(gen_fn, pattern_list=('<SUB-QUESTIONS>',))
    logger.info(f'Planning stage output:\n\n{planning_response}')
    questions = re.findall('<SUB-QUESTIONS>\\s*(.*?)\\s*</SUB-QUESTIONS>', planning_response, re.DOTALL)[0].strip().splitlines()
    qa_system_prompt = longcepo_config.system_prompt if longcepo_config.system_prompt is not None else system_prompt
    qa_history = ''
    for question in questions:
        if not question:
            continue
        question = re.sub('^\\d+\\.', '', question)
        answer, cb_log = mapreduce(qa_system_prompt, question, context, qa_history, client, model, tokenizer, longcepo_config=longcepo_config, cb_log=cb_log)
        qa_history += f'- Previous question: {question}\n\n'
        answer = re.sub('^:+', '', answer)
        qa_history += f'- Previous answer: {answer}\n\n'
        logger.info(f'QA history:\n\n{qa_history}')
    answer, cb_log = mapreduce(qa_system_prompt, query, context, qa_history, client, model, tokenizer, longcepo_config=longcepo_config, cb_log=cb_log)
    return (answer, cb_log['total_tokens'])

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

def autothink_decode(model: PreTrainedModel, tokenizer: PreTrainedTokenizer, messages: List[Dict[str, str]], request_config: Optional[Dict[str, Any]]=None) -> str:
    """
    Main plugin execution function with AutoThink's controlled thinking process.
    
    Args:
        model: Language model
        tokenizer: Model tokenizer
        messages: List of message dictionaries
        request_config: Optional configuration dictionary
        
    Returns:
        Generated response with thinking process
    """
    logger.info('Starting AutoThink processing')
    config = {}
    if request_config:
        config.update(request_config)
    try:
        processor = AutoThinkProcessor(model, tokenizer, config)
        response = processor.process(messages)
        return response
    except Exception as e:
        logger.error(f'Error in AutoThink processing: {str(e)}')
        raise

def remove_steering_hooks(hooks):
    """
    Remove steering hooks from a model.
    
    Args:
        hooks: List of (hook, handle) tuples
    """
    for _, handle in hooks:
        handle.remove()
    logger.info(f'STEERING: Removed {len(hooks)} hooks')

class TestMARSIMO25(unittest.TestCase):
    """Test MARS on specific IMO25 problems"""

    def setUp(self):
        """Set up test fixtures with logging capture"""
        self.system_prompt = 'You are a mathematical problem solver capable of handling complex olympiad-level problems.'
        self.model = 'mock-model'
        self.log_capture = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.log_handler.setLevel(logging.INFO)
        mars_logger = logging.getLogger('optillm.mars')
        mars_logger.addHandler(self.log_handler)
        mars_logger.setLevel(logging.INFO)
        self.original_level = mars_logger.level

    def tearDown(self):
        """Clean up test fixtures"""
        mars_logger = logging.getLogger('optillm.mars')
        mars_logger.removeHandler(self.log_handler)
        mars_logger.setLevel(self.original_level)
        self.log_handler.close()

    def get_captured_logs(self):
        """Get the captured log output"""
        return self.log_capture.getvalue()

    def test_imo25_problem3_functional_equation(self):
        """Test MARS on IMO25 Problem 3 - Functional Equation (Expected: c = 4)"""
        problem3 = 'Let ℕ denote the set of positive integers. A function f:ℕ→ℕ is said to be bonza if f(a) divides b^a-f(b)^{f(a)} for all positive integers a and b.\n\nDetermine the smallest real constant c such that f(n)≤cn for all bonza functions f and all positive integers n.'
        print(f'\n🧮 Testing MARS on IMO25 Problem 3 (Expected answer: c = 4)...')
        client = MockOpenAIClient(response_delay=0.05, reasoning_tokens=3000)
        start_time = time.time()
        result = multi_agent_reasoning_system(self.system_prompt, problem3, client, self.model)
        execution_time = time.time() - start_time
        self.assertIsInstance(result, tuple)
        response, tokens = result
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 100, 'Response should be substantial for IMO problem')
        self.assertGreater(tokens, 0)
        has_answer_4 = '4' in response
        has_constant_c = 'c' in response.lower()
        print(f'  📊 Execution time: {execution_time:.2f}s')
        print(f'  📊 Response length: {len(response):,} characters')
        print(f'  📊 Total tokens: {tokens:,}')
        print(f'  📊 API calls made: {client.call_count}')
        print(f"  🎯 Contains answer '4': {has_answer_4}")
        print(f"  🎯 Contains 'constant c': {has_constant_c}")
        logs = self.get_captured_logs()
        voting_logs = [line for line in logs.split('\n') if '🗳️  VOTING' in line]
        synthesis_logs = [line for line in logs.split('\n') if '🤝 SYNTHESIS' in line]
        print(f'  📋 Voting log entries: {len(voting_logs)}')
        print(f'  📋 Synthesis log entries: {len(synthesis_logs)}')
        if voting_logs:
            print(f'  📋 Sample voting log: {voting_logs[0][:100]}...')
        answer_extraction_logs = [line for line in logs.split('\n') if 'extracted answer' in line.lower()]
        if answer_extraction_logs:
            print(f'  🔍 Answer extraction logs found: {len(answer_extraction_logs)}')
            for log in answer_extraction_logs[:3]:
                print(f'    {log}')
        response_lines = response.split('\n')
        key_lines = [line for line in response_lines if any((keyword in line.lower() for keyword in ['constant', 'c =', 'answer', '= 4', 'therefore']))]
        if key_lines:
            print(f'  🔑 Key response lines:')
            for line in key_lines[:5]:
                print(f'    {line.strip()}')
        print(f'✅ IMO25 Problem 3 test completed')

    def test_imo25_problem4_number_theory(self):
        """Test MARS on IMO25 Problem 4 - Number Theory (Expected: 6J·12^K formula)"""
        problem4 = 'A proper divisor of a positive integer N is a positive divisor of N other than N itself.\n\nThe infinite sequence a_1,a_2,… consists of positive integers, each of which has at least three proper divisors. For each n≥1, the integer a_{n+1} is the sum of three largest proper divisors of a_n.\n\nDetermine all possible values of a_1.'
        print(f'\n🔢 Testing MARS on IMO25 Problem 4 (Expected: 6J·12^K formula)...')
        client = MockOpenAIClient(response_delay=0.05, reasoning_tokens=3000)
        start_time = time.time()
        result = multi_agent_reasoning_system(self.system_prompt, problem4, client, self.model)
        execution_time = time.time() - start_time
        self.assertIsInstance(result, tuple)
        response, tokens = result
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 100, 'Response should be substantial for IMO problem')
        has_formula_6J = '6J' in response or '6j' in response.lower()
        has_formula_12K = '12^K' in response or '12^k' in response.lower()
        has_gcd_condition = 'gcd' in response.lower()
        print(f'  📊 Execution time: {execution_time:.2f}s')
        print(f'  📊 Response length: {len(response):,} characters')
        print(f"  🎯 Contains '6J': {has_formula_6J}")
        print(f"  🎯 Contains '12^K': {has_formula_12K}")
        print(f"  🎯 Contains 'gcd': {has_gcd_condition}")
        print(f'✅ IMO25 Problem 4 test completed')

    def test_answer_extraction_analysis(self):
        """Test answer extraction specifically with controlled responses"""
        print(f'\n🔍 Testing answer extraction with controlled responses...')

        class ControlledMockClient(MockOpenAIClient):

            def __init__(self):
                super().__init__(response_delay=0.01, reasoning_tokens=1000)
                self.response_index = 0
                self.controlled_responses = ['After careful analysis, I determine that the smallest constant c = 4. This can be proven by construction and bounds analysis.', 'The minimum value is c = 4. Therefore, the answer is 4.', 'Through systematic analysis, the constant c must equal 4. The final answer is c = 4.']

            def chat_completions_create(self, **kwargs):
                result = super().chat_completions_create(**kwargs)
                if self.response_index < len(self.controlled_responses):
                    result.choices[0].message.content = self.controlled_responses[self.response_index]
                    self.response_index += 1
                return result
        simple_problem = 'Find the smallest constant c such that f(n) ≤ cn for all valid functions f.'
        client = ControlledMockClient()
        result = multi_agent_reasoning_system(self.system_prompt, simple_problem, client, self.model)
        response, tokens = result
        logs = self.get_captured_logs()
        voting_logs = [line for line in logs.split('\n') if 'VOTING' in line and 'extracted answer' in line.lower()]
        print(f"  📊 Response contains '4': {'4' in response}")
        print(f"  📊 Response contains 'c = 4': {'c = 4' in response}")
        print(f'  📋 Voting logs with extraction: {len(voting_logs)}')
        if voting_logs:
            for i, log in enumerate(voting_logs[:3]):
                print(f'    Vote {i + 1}: {log}')
        print(f'✅ Answer extraction analysis completed')

def get_captured_logs(self):
    """Get the captured log output"""
    return self.log_capture.getvalue()

class TestMARSParallel(unittest.TestCase):
    """Test MARS parallel execution functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.system_prompt = 'You are a mathematical problem solver.'
        self.test_query = 'What is the value of x if 2x + 5 = 15?'
        self.model = 'mock-model'
        self.log_capture = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.log_handler.setLevel(logging.INFO)
        mars_logger = logging.getLogger('optillm.mars')
        mars_logger.addHandler(self.log_handler)
        mars_logger.setLevel(logging.INFO)
        self.original_level = mars_logger.level

    def tearDown(self):
        """Clean up test fixtures"""
        mars_logger = logging.getLogger('optillm.mars')
        mars_logger.removeHandler(self.log_handler)
        mars_logger.setLevel(self.original_level)
        self.log_handler.close()

    def get_captured_logs(self):
        """Get the captured log output"""
        return self.log_capture.getvalue()

    def test_mars_import(self):
        """Test that MARS can be imported correctly"""
        from optillm.mars import multi_agent_reasoning_system
        self.assertTrue(callable(multi_agent_reasoning_system))

    def test_mars_basic_call(self):
        """Test basic MARS functionality with mock client"""
        client = MockOpenAIClient(response_delay=0.01)
        try:
            result = multi_agent_reasoning_system(self.system_prompt, self.test_query, client, self.model)
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            response, tokens = result
            self.assertIsInstance(response, str)
            self.assertIsInstance(tokens, int)
            self.assertGreater(len(response), 0)
            self.assertGreater(tokens, 0)
            print('✅ MARS basic call test passed')
        except Exception as e:
            self.fail(f'MARS basic call failed: {e}')

    def test_mars_parallel_execution_performance(self):
        """Test that parallel execution shows improvement over theoretical sequential"""
        client = MockOpenAIClient(response_delay=0.05, reasoning_tokens=2000)
        start_time = time.time()
        result = multi_agent_reasoning_system(self.system_prompt, self.test_query, client, self.model)
        end_time = time.time()
        execution_time = end_time - start_time
        self.assertLess(execution_time, 30, f'Execution took {execution_time:.2f}s, too long for test')
        self.assertIsInstance(result, tuple)
        response, tokens = result
        self.assertGreater(len(response), 0)
        self.assertGreater(tokens, 0)
        call_times = client.call_times
        if len(call_times) >= 3:
            first_three = call_times[:3]
            time_spread = max(first_three) - min(first_three)
            self.assertLess(time_spread, 0.5, f'First 3 calls spread over {time_spread:.2f}s, not parallel enough')
        logs = self.get_captured_logs()
        self.assertIn('🚀 MARS', logs, 'Should contain main orchestration logs')
        print(f'✅ MARS parallel execution completed in {execution_time:.2f}s with {client.call_count} API calls')
        print(f'📋 Captured {len(logs.split('🚀'))} main log entries')

    def test_mars_worker_pool_calculation(self):
        """Test that worker pool size is calculated correctly"""
        from optillm.mars.mars import DEFAULT_CONFIG
        num_agents = DEFAULT_CONFIG['num_agents']
        verification_passes = DEFAULT_CONFIG['verification_passes_required']
        expected_workers = max(num_agents, num_agents * min(2, verification_passes))
        self.assertEqual(expected_workers, 6)
        print(f'✅ Worker pool size calculation correct: {expected_workers} workers')

    def test_mars_error_handling(self):
        """Test error handling in parallel execution"""

        class FailingMockClient(MockOpenAIClient):

            def __init__(self):
                super().__init__(response_delay=0.01)
                self.failure_count = 0

            def chat_completions_create(self, **kwargs):
                self.failure_count += 1
                if self.failure_count % 3 == 0:
                    raise Exception('Mock API failure')
                return super().chat_completions_create(**kwargs)
        failing_client = FailingMockClient()
        try:
            result = multi_agent_reasoning_system(self.system_prompt, self.test_query, failing_client, self.model)
            self.assertIsInstance(result, tuple)
            response, tokens = result
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            print('✅ MARS error handling test passed')
        except Exception as e:
            self.assertIn('MARS system encountered an error', str(e))
            print('✅ MARS fallback error handling works')

    @patch('optillm.mars.mars.ThreadPoolExecutor')
    def test_mars_uses_thread_pool(self, mock_thread_pool):
        """Test that MARS actually uses ThreadPoolExecutor for parallel execution"""
        mock_executor = Mock()
        mock_thread_pool.return_value.__enter__.return_value = mock_executor
        client = MockOpenAIClient(response_delay=0.01)
        multi_agent_reasoning_system(self.system_prompt, self.test_query, client, self.model)
        mock_thread_pool.assert_called_once()
        call_args = mock_thread_pool.call_args
        self.assertIn('max_workers', call_args.kwargs)
        self.assertEqual(call_args.kwargs['max_workers'], 6)
        print('✅ MARS ThreadPoolExecutor usage test passed')

    def test_mars_hard_problems(self):
        """Test MARS on challenging problems that require deep reasoning"""
        hard_problems = [{'name': 'Advanced Algebra', 'problem': 'Find all positive integer solutions to x^3 + y^3 = z^3 - 1 where x, y, z are all less than 100.', 'expected_features': ['systematic', 'case', 'analysis']}, {'name': 'Number Theory', 'problem': 'Prove that there are infinitely many primes of the form 4k+3.', 'expected_features': ['proof', 'contradiction', 'infinite']}, {'name': 'Combinatorics', 'problem': 'In how many ways can 20 identical balls be distributed into 5 distinct boxes such that each box contains at least 2 balls?', 'expected_features': ['stars', 'bars', 'constraint']}, {'name': 'Geometry', 'problem': 'Given a triangle ABC with sides a, b, c, prove that a^2 + b^2 + c^2 ≥ 4√3 * Area.', 'expected_features': ['inequality', 'area', 'geometric']}]

        class EnhancedMockClient(MockOpenAIClient):

            def __init__(self):
                super().__init__(response_delay=0.1, reasoning_tokens=3000)
                self.problem_responses = {'Advanced Algebra': 'This requires systematic case analysis. Let me examine small values systematically. After checking cases x,y,z < 100, the equation x³ + y³ = z³ - 1 has solutions like (x,y,z) = (1,1,1) since 1³ + 1³ = 2 = 2³ - 6... Actually, let me recalculate: 1³ + 1³ = 2, and z³ - 1 = 2 means z³ = 3, so z ≈ 1.44. Let me check (2,2,2): 8 + 8 = 16 = 8 - 1 = 7? No. This is a difficult Diophantine equation requiring advanced techniques.', 'Number Theory': "I'll prove this by contradiction using Euclid's method. Assume there are only finitely many primes of the form 4k+3: p₁, p₂, ..., pₙ. Consider N = 4(p₁p₂...pₙ) + 3. Since N ≡ 3 (mod 4), at least one prime factor of N must be ≡ 3 (mod 4). But N is not divisible by any of p₁, p₂, ..., pₙ, so there must be another prime of the form 4k+3, contradicting our assumption. Therefore, there are infinitely many such primes.", 'Combinatorics': 'This is a stars and bars problem with constraints. We need to distribute 20 balls into 5 boxes with each box having at least 2 balls. First, place 2 balls in each box (using 10 balls). Now we need to distribute the remaining 10 balls into 5 boxes with no constraints. Using stars and bars: C(10+5-1, 5-1) = C(14,4) = 1001 ways.', 'Geometry': "This is a form of Weitzenböck's inequality. We can prove this using the relationship between area and sides. For a triangle with area S and sides a,b,c, we have S = √[s(s-a)(s-b)(s-c)] where s = (a+b+c)/2. We want to show a² + b² + c² ≥ 4√3 · S. This can be proven using the isoperimetric inequality and Jensen's inequality applied to the convex function f(x) = x²."}

            def chat_completions_create(self, **kwargs):
                result = super().chat_completions_create(**kwargs)
                messages = kwargs.get('messages', [])
                for message in messages:
                    content = message.get('content', '')
                    for prob_type, response in self.problem_responses.items():
                        if any((keyword in content for keyword in prob_type.lower().split())):
                            result.choices[0].message.content = response
                            return result
                result.choices[0].message.content = 'This is a complex problem requiring careful analysis. Let me work through it step by step with rigorous reasoning.'
                return result
        client = EnhancedMockClient()
        for problem_data in hard_problems:
            with self.subTest(problem=problem_data['name']):
                print(f'\n🧠 Testing MARS on {problem_data['name']} problem...')
                start_time = time.time()
                result = multi_agent_reasoning_system(self.system_prompt, problem_data['problem'], client, self.model)
                execution_time = time.time() - start_time
                self.assertIsInstance(result, tuple)
                response, tokens = result
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 50, 'Response should be substantial for hard problems')
                self.assertGreater(tokens, 0)
                response_lower = response.lower()
                found_features = []
                for feature in problem_data['expected_features']:
                    if feature.lower() in response_lower:
                        found_features.append(feature)
                self.assertGreater(len(found_features), 0, f'Response should contain reasoning features like {problem_data['expected_features']}')
                print(f'  ✅ {problem_data['name']}: {execution_time:.2f}s, {len(response):,} chars, features: {found_features}')
        logs = self.get_captured_logs()
        log_checks = [('🚀 MARS', 'Main orchestration logs'), ('🤖 AGENT', 'Agent generation logs'), ('🗳️  VOTING', 'Voting mechanism logs'), ('🤝 SYNTHESIS', 'Synthesis phase logs')]
        for emoji, description in log_checks:
            if emoji in logs:
                count = logs.count(emoji)
                print(f'  📊 Found {count} {description}')
            else:
                print(f'  ⚠️  No {description} found (expected with enhanced logging)')
        print(f'\n✅ MARS hard problems test completed - verified reasoning on {len(hard_problems)} challenging problems')

    def test_mars_logging_and_monitoring(self):
        """Test that MARS logging provides useful monitoring information"""
        print('\n📊 Testing MARS logging and monitoring capabilities...')

        class MonitoringMockClient(MockOpenAIClient):

            def __init__(self):
                super().__init__(response_delay=0.05, reasoning_tokens=2500)
                self.detailed_responses = True

            def chat_completions_create(self, **kwargs):
                result = super().chat_completions_create(**kwargs)
                if 'verifying' in str(kwargs.get('messages', [])):
                    result.choices[0].message.content = 'VERIFICATION: The solution appears CORRECT with high confidence. The reasoning is sound and the final answer is properly justified. Confidence: 9/10.'
                elif 'improving' in str(kwargs.get('messages', [])):
                    result.choices[0].message.content = "IMPROVEMENT: The original solution can be enhanced by adding more rigorous justification. Here's the improved version with stronger mathematical foundations..."
                else:
                    result.choices[0].message.content = "Let me solve this step by step. First, I'll analyze the problem structure. Then I'll apply appropriate mathematical techniques. The solution involves careful reasoning and verification. \\boxed{42}"
                return result
        client = MonitoringMockClient()
        complex_problem = 'Solve the system: x² + y² = 25, x + y = 7. Find all real solutions and verify your answer.'
        start_time = time.time()
        result = multi_agent_reasoning_system(self.system_prompt, complex_problem, client, self.model)
        execution_time = time.time() - start_time
        logs = self.get_captured_logs()
        log_lines = logs.split('\n')
        log_stats = {'🚀 MARS': 0, '🤖 AGENT': 0, '🔍 VERIFIER': 0, '🗳️  VOTING': 0, '🤝 SYNTHESIS': 0, '⏱️  TIMING': 0}
        for line in log_lines:
            for emoji_prefix in log_stats.keys():
                if emoji_prefix in line:
                    log_stats[emoji_prefix] += 1
        total_logs = sum(log_stats.values())
        self.assertGreater(total_logs, 10, 'Should have substantial logging for monitoring')
        monitoring_checks = [('MARS', log_stats['🚀 MARS'], 'Main orchestration phases'), ('AGENT', log_stats['🤖 AGENT'], 'Agent operations'), ('VOTING', log_stats['🗳️  VOTING'], 'Consensus mechanism'), ('SYNTHESIS', log_stats['🤝 SYNTHESIS'], 'Final synthesis')]
        print(f'\n📈 Monitoring Statistics (from {execution_time:.2f}s execution):')
        for name, count, description in monitoring_checks:
            status = '✅' if count > 0 else '⚠️ '
            print(f'  {status} {name}: {count} {description}')
        response, tokens = result
        self.assertGreater(len(response), 100, 'Complex problems should generate substantial responses')
        self.assertGreater(tokens, 1000, 'Should use significant reasoning tokens')
        quality_indicators = ['confidence', 'reasoning', 'verification', 'solution', 'answer']
        found_indicators = []
        logs_lower = logs.lower()
        for indicator in quality_indicators:
            if indicator in logs_lower:
                found_indicators.append(indicator)
        print(f'\n🎯 Quality indicators found in logs: {found_indicators}')
        self.assertGreater(len(found_indicators), 2, 'Should track multiple quality indicators')
        print(f'✅ MARS logging and monitoring test passed - captured {total_logs} log entries')

    def test_mars_consensus_mechanism(self):
        """Test MARS consensus and verification mechanism"""

        class ConsistentMockClient(MockOpenAIClient):

            def chat_completions_create(self, **kwargs):
                result = super().chat_completions_create(**kwargs)
                result.choices[0].message.content = 'The solution is x = 5. Final answer: 5'
                return result
        client = ConsistentMockClient(response_delay=0.01)
        result = multi_agent_reasoning_system(self.system_prompt, self.test_query, client, self.model)
        self.assertIsInstance(result, tuple)
        response, tokens = result
        self.assertIn('5', response)
        logs = self.get_captured_logs()
        if '🗳️  VOTING' in logs:
            print('✅ MARS consensus mechanism test passed with voting logs')
        else:
            print('✅ MARS consensus mechanism test passed')

def get_captured_logs(self):
    """Get the captured log output"""
    return self.log_capture.getvalue()

class TestSSLConfiguration(unittest.TestCase):
    """Test SSL configuration via CLI arguments and environment variables."""

    def setUp(self):
        """Reset server_config before each test."""
        self.original_config = server_config.copy()
        for key in ['OPTILLM_SSL_VERIFY', 'OPTILLM_SSL_CERT_PATH']:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Restore original server_config after each test."""
        server_config.clear()
        server_config.update(self.original_config)

    def test_default_ssl_verify_enabled(self):
        """Test that SSL verification is enabled by default."""
        self.assertTrue(server_config.get('ssl_verify', True))
        self.assertEqual(server_config.get('ssl_cert_path', ''), '')

    def test_cli_no_ssl_verify_flag(self):
        """Test --no-ssl-verify CLI flag disables SSL verification."""
        with patch('sys.argv', ['optillm', '--no-ssl-verify']):
            args = parse_args()
            self.assertFalse(args.ssl_verify)

    def test_cli_ssl_cert_path(self):
        """Test --ssl-cert-path CLI argument."""
        test_cert_path = '/path/to/ca-bundle.crt'
        with patch('sys.argv', ['optillm', '--ssl-cert-path', test_cert_path]):
            args = parse_args()
            self.assertEqual(args.ssl_cert_path, test_cert_path)

    def test_env_ssl_verify_false(self):
        """Test OPTILLM_SSL_VERIFY=false environment variable."""
        os.environ['OPTILLM_SSL_VERIFY'] = 'false'
        with patch('sys.argv', ['optillm']):
            args = parse_args()
            self.assertFalse(args.ssl_verify)

    def test_env_ssl_verify_true(self):
        """Test OPTILLM_SSL_VERIFY=true environment variable."""
        os.environ['OPTILLM_SSL_VERIFY'] = 'true'
        with patch('sys.argv', ['optillm']):
            args = parse_args()
            self.assertTrue(args.ssl_verify)

    def test_env_ssl_cert_path(self):
        """Test OPTILLM_SSL_CERT_PATH environment variable."""
        test_cert_path = '/etc/ssl/certs/custom-ca.pem'
        os.environ['OPTILLM_SSL_CERT_PATH'] = test_cert_path
        with patch('sys.argv', ['optillm']):
            args = parse_args()
            self.assertEqual(args.ssl_cert_path, test_cert_path)

    def test_cli_overrides_env(self):
        """Test that CLI arguments override environment variables."""
        os.environ['OPTILLM_SSL_VERIFY'] = 'true'
        with patch('sys.argv', ['optillm', '--no-ssl-verify']):
            args = parse_args()
            self.assertFalse(args.ssl_verify)

def tearDown(self):
    """Restore original server_config after each test."""
    server_config.clear()
    server_config.update(self.original_config)

class TestHTTPClientSSLConfiguration(unittest.TestCase):
    """Test that SSL configuration is properly applied to HTTP clients."""

    def setUp(self):
        """Set up test environment."""
        self.original_config = server_config.copy()

    def tearDown(self):
        """Restore original server_config."""
        server_config.clear()
        server_config.update(self.original_config)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_httpx_client_ssl_verify_disabled(self):
        """Test httpx.Client created with verify=False when SSL disabled."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_httpx_client.assert_called_once_with(verify=False)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_httpx_client_ssl_verify_enabled(self):
        """Test httpx.Client created with verify=True by default."""
        from optillm.server import get_config
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = ''
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_httpx_client.assert_called_once_with(verify=True)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_httpx_client_custom_cert_path(self):
        """Test httpx.Client created with custom certificate path."""
        from optillm.server import get_config
        test_cert_path = '/path/to/custom-ca.pem'
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = test_cert_path
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_httpx_client.assert_called_once_with(verify=test_cert_path)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_openai_client_receives_http_client(self):
        """Test that OpenAI client receives the configured httpx client."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        server_config['base_url'] = ''
        mock_http_client_instance = MagicMock()
        with patch('httpx.Client', return_value=mock_http_client_instance) as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            self.assertIn('http_client', call_kwargs)
            self.assertEqual(call_kwargs['http_client'], mock_http_client_instance)

    @patch.dict(os.environ, {'CEREBRAS_API_KEY': 'test-key'})
    def test_cerebras_client_receives_http_client(self):
        """Test that Cerebras client receives the configured httpx client."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        server_config['base_url'] = ''
        mock_http_client_instance = MagicMock()
        with patch('httpx.Client', return_value=mock_http_client_instance) as mock_httpx_client, patch('optillm.server.Cerebras') as mock_cerebras:
            get_config()
            mock_cerebras.assert_called_once()
            call_kwargs = mock_cerebras.call_args[1]
            self.assertIn('http_client', call_kwargs)
            self.assertEqual(call_kwargs['http_client'], mock_http_client_instance)

    @patch.dict(os.environ, {'AZURE_OPENAI_API_KEY': 'test-key', 'AZURE_API_VERSION': '2024-02-15-preview', 'AZURE_API_BASE': 'https://test.openai.azure.com'})
    def test_azure_client_receives_http_client(self):
        """Test that AzureOpenAI client receives the configured httpx client."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        mock_http_client_instance = MagicMock()
        with patch('httpx.Client', return_value=mock_http_client_instance) as mock_httpx_client, patch('optillm.server.AzureOpenAI') as mock_azure:
            get_config()
            mock_azure.assert_called_once()
            call_kwargs = mock_azure.call_args[1]
            self.assertIn('http_client', call_kwargs)
            self.assertEqual(call_kwargs['http_client'], mock_http_client_instance)

def tearDown(self):
    """Restore original server_config."""
    server_config.clear()
    server_config.update(self.original_config)

class TestPluginSSLConfiguration(unittest.TestCase):
    """Test that plugins properly use SSL configuration."""

    def setUp(self):
        """Set up test environment."""
        self.original_config = server_config.copy()

    def tearDown(self):
        """Restore original server_config."""
        server_config.clear()
        server_config.update(self.original_config)

    @patch('optillm.plugins.readurls_plugin.requests.get')
    def test_readurls_plugin_ssl_verify_disabled(self, mock_requests_get):
        """Test readurls plugin respects SSL verification disabled."""
        from optillm.plugins.readurls_plugin import fetch_webpage_content
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        fetch_webpage_content('https://example.com')
        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('verify', call_kwargs)
        self.assertFalse(call_kwargs['verify'])

    @patch('optillm.plugins.readurls_plugin.requests.get')
    def test_readurls_plugin_ssl_verify_enabled(self, mock_requests_get):
        """Test readurls plugin respects SSL verification enabled."""
        from optillm.plugins.readurls_plugin import fetch_webpage_content
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = ''
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        fetch_webpage_content('https://example.com')
        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('verify', call_kwargs)
        self.assertTrue(call_kwargs['verify'])

    @patch('optillm.plugins.readurls_plugin.requests.get')
    def test_readurls_plugin_custom_cert_path(self, mock_requests_get):
        """Test readurls plugin uses custom certificate path."""
        from optillm.plugins.readurls_plugin import fetch_webpage_content
        test_cert_path = '/path/to/custom-ca.pem'
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = test_cert_path
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        fetch_webpage_content('https://example.com')
        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('verify', call_kwargs)
        self.assertEqual(call_kwargs['verify'], test_cert_path)

def tearDown(self):
    """Restore original server_config."""
    server_config.clear()
    server_config.update(self.original_config)

class TestSSLWarnings(unittest.TestCase):
    """Test that appropriate warnings are shown when SSL is disabled."""

    def setUp(self):
        """Set up test environment."""
        self.original_config = server_config.copy()

    def tearDown(self):
        """Restore original server_config."""
        server_config.clear()
        server_config.update(self.original_config)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_warning_when_ssl_disabled(self):
        """Test that a warning is logged when SSL verification is disabled."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai, patch('optillm.server.logger.warning') as mock_logger_warning:
            get_config()
            mock_logger_warning.assert_called()
            warning_message = mock_logger_warning.call_args[0][0]
            self.assertIn('SSL certificate verification is DISABLED', warning_message)
            self.assertIn('insecure', warning_message.lower())

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_info_when_custom_cert_used(self):
        """Test that an info message is logged when using custom certificate."""
        from optillm.server import get_config
        test_cert_path = '/path/to/custom-ca.pem'
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = test_cert_path
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai, patch('optillm.server.logger.info') as mock_logger_info:
            get_config()
            mock_logger_info.assert_called()
            info_message = mock_logger_info.call_args[0][0]
            self.assertIn('custom CA certificate bundle', info_message)
            self.assertIn(test_cert_path, info_message)

def tearDown(self):
    """Restore original server_config."""
    server_config.clear()
    server_config.update(self.original_config)

