# Cluster 13

def main():
    """Main entry point"""
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    evaluator = SimpleQAEvaluator(model=args.model, approach=args.approach, base_url=args.base_url, grader_model=args.grader_model, timeout=args.timeout, cache_dir=args.cache_dir, output_dir=args.output_dir, use_verified=args.verified)
    try:
        metrics = evaluator.run_evaluation(num_samples=args.num_samples, start_index=args.start_index)
        print('\n' + '=' * 50)
        print('EVALUATION SUMMARY')
        print('=' * 50)
        print(f'Model: {args.model}')
        print(f'Approach: {args.approach}')
        print(f'Questions: {metrics['total_questions']}')
        print(f'Accuracy: {metrics['accuracy']:.1f}%')
        print(f'F1 Score: {metrics['f1_score']:.3f}')
        print(f'Correct: {metrics['correct']}')
        print(f'Incorrect: {metrics['incorrect']}')
        print(f'Not Attempted: {metrics['not_attempted']}')
        if metrics['errors'] > 0:
            print(f'Errors: {metrics['errors']}')
    except KeyboardInterrupt:
        print('\nEvaluation interrupted by user')
    except Exception as e:
        logger.error(f'Evaluation failed: {e}')
        raise

def leap(system_prompt: str, initial_query: str, client, model: str, request_id: str=None) -> str:
    leap_solver = LEAP(system_prompt, client, model, request_id)
    return (leap_solver.solve(initial_query), leap_solver.leap_completion_tokens)

def execute_single_approach(approach, system_prompt, initial_query, client, model, request_config: dict=None, request_id: str=None):
    if approach in known_approaches:
        if approach == 'none':
            kwargs = request_config.copy() if request_config else {}
            kwargs.pop('n', None)
            kwargs.pop('stream', None)
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            if initial_query:
                messages.append({'role': 'user', 'content': initial_query})
            response = none_approach(original_messages=messages, client=client, model=model, request_id=request_id, **kwargs)
            return (response, 0)
        elif approach == 'mcts':
            return chat_with_mcts(system_prompt, initial_query, client, model, server_config['mcts_simulations'], server_config['mcts_exploration'], server_config['mcts_depth'], request_id)
        elif approach == 'bon':
            return best_of_n_sampling(system_prompt, initial_query, client, model, server_config['best_of_n'], request_id)
        elif approach == 'moa':
            return mixture_of_agents(system_prompt, initial_query, client, model, request_id)
        elif approach == 'rto':
            return round_trip_optimization(system_prompt, initial_query, client, model, request_id)
        elif approach == 'z3':
            z3_solver = Z3SymPySolverSystem(system_prompt, client, model, request_id=request_id)
            return z3_solver.process_query(initial_query)
        elif approach == 'self_consistency':
            return advanced_self_consistency_approach(system_prompt, initial_query, client, model, request_id)
        elif approach == 'pvg':
            return inference_time_pv_game(system_prompt, initial_query, client, model, request_id)
        elif approach == 'rstar':
            rstar = RStar(system_prompt, client, model, max_depth=server_config['rstar_max_depth'], num_rollouts=server_config['rstar_num_rollouts'], c=server_config['rstar_c'], request_id=request_id)
            return rstar.solve(initial_query)
        elif approach == 'cot_reflection':
            return cot_reflection(system_prompt, initial_query, client, model, return_full_response=server_config['return_full_response'], request_config=request_config, request_id=request_id)
        elif approach == 'plansearch':
            return plansearch(system_prompt, initial_query, client, model, n=server_config['n'], request_id=request_id)
        elif approach == 'leap':
            return leap(system_prompt, initial_query, client, model, request_id)
        elif approach == 're2':
            return re2_approach(system_prompt, initial_query, client, model, n=server_config['n'], request_id=request_id)
        elif approach == 'cepo':
            return cepo(system_prompt, initial_query, client, model, cepo_config, request_id)
        elif approach == 'mars':
            return multi_agent_reasoning_system(system_prompt, initial_query, client, model, request_config=request_config, request_id=request_id)
    elif approach in plugin_approaches:
        plugin_func = plugin_approaches[approach]
        import inspect
        sig = inspect.signature(plugin_func)
        is_async = inspect.iscoroutinefunction(plugin_func)
        if is_async:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if 'request_config' in sig.parameters:
                    result = loop.run_until_complete(plugin_func(system_prompt, initial_query, client, model, request_config=request_config))
                else:
                    result = loop.run_until_complete(plugin_func(system_prompt, initial_query, client, model))
                return result
            finally:
                loop.close()
        elif 'request_config' in sig.parameters:
            return plugin_func(system_prompt, initial_query, client, model, request_config=request_config)
        else:
            return plugin_func(system_prompt, initial_query, client, model)
    else:
        raise ValueError(f'Unknown approach: {approach}')

def execute_n_times(n: int, approaches, operation: str, system_prompt: str, initial_query: str, client: Any, model: str, request_config: dict=None, request_id: str=None) -> Tuple[Union[str, List[str]], int]:
    """
    Execute the pipeline n times and return n responses.
    
    Args:
        n (int): Number of times to run the pipeline
        approaches (list): List of approaches to execute
        operation (str): Operation type ('SINGLE', 'AND', or 'OR')
        system_prompt (str): System prompt
        initial_query (str): Initial query
        client: OpenAI client instance
        model (str): Model identifier
        
    Returns:
        Tuple[Union[str, List[str]], int]: List of responses and total token count
    """
    responses = []
    total_tokens = 0
    for _ in range(n):
        if operation == 'SINGLE':
            response, tokens = execute_single_approach(approaches[0], system_prompt, initial_query, client, model, request_config, request_id)
        elif operation == 'AND':
            response, tokens = execute_combined_approaches(approaches, system_prompt, initial_query, client, model, request_config)
        elif operation == 'OR':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response, tokens = loop.run_until_complete(execute_parallel_approaches(approaches, system_prompt, initial_query, client, model, request_config))
            loop.close()
        else:
            raise ValueError(f'Unknown operation: {operation}')
        if isinstance(response, list):
            responses.extend(response)
        else:
            responses.append(response)
        total_tokens += tokens
    if n == 1 and len(responses) == 1:
        return (responses[0], total_tokens)
    return (responses, total_tokens)

class PlanSearch:

    def __init__(self, system_prompt: str, client, model: str, request_id: str=None):
        self.system_prompt = system_prompt
        self.client = client
        self.model = model
        self.request_id = request_id
        self.plansearch_completion_tokens = 0

    def generate_observations(self, problem: str, num_observations: int=3) -> List[str]:
        prompt = f'You are an expert Python programmer. You will be given a competitive programming question\n(problem specification). You will return several useful, non-obvious, and correct observations\nabout the problem, like hints to solve the problem. You will NOT return any code. Be as\ncreative as possible, going beyond what you think is intuitively correct.\n\nHere is the competitive programming problem:\n{problem}\n\nPlease provide {num_observations} observations.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        observations = response.choices[0].message.content.strip().split('\n')
        return [obs.strip() for obs in observations if obs.strip()]

    def generate_derived_observations(self, problem: str, observations: List[str], num_new_observations: int=2) -> List[str]:
        prompt = f'You are an expert Python programmer. You will be given a competitive programming question\n(problem specification) and several correct observations about the problem.\nYou will brainstorm several new, useful, and correct observations about the problem, derived\nfrom the given observations. You will NOT return any code. Be as creative as possible, going\nbeyond what you think is intuitively correct.\n\nHere is the competitive programming problem:\n{problem}\n\nHere are the existing observations:\n{chr(10).join((f'{i + 1}. {obs}' for i, obs in enumerate(observations)))}\n\nPlease provide {num_new_observations} new observations derived from the existing ones.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        new_observations = response.choices[0].message.content.strip().split('\n')
        return [obs.strip() for obs in new_observations if obs.strip()]

    def generate_solution(self, problem: str, observations: List[str]) -> str:
        prompt = f'Here is the competitive programming problem:\n{problem}\n\nHere are the intelligent observations to help solve the problem:\n{chr(10).join((f'Observation {i + 1}: {obs}' for i, obs in enumerate(observations)))}\n\nUse these observations above to brainstorm a natural language solution to the problem above.\nNote that your intuition may lead you astray, so come up with simple, creative ideas that\ngo beyond what you would usually come up with and exceeds your narrow intuition.\nQuote relevant parts of the observations EXACTLY before each step of the solution. QUOTING\nIS CRUCIAL.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def implement_solution(self, problem: str, solution: str) -> str:
        prompt = f'You are an expert Python programmer. You will be given a question (problem specification)\nand a natural language solution/tutorial that describes how to solve the problem. You will\ngenerate a correct Python program that matches said specification and tutorial and passes\nall tests. You will NOT return anything except for the program inside markdown codeblocks.\n\nProblem:\n{problem}\n\nSolution:\n{solution}\n\nPlease implement the solution in Python.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def solve(self, problem: str, num_initial_observations: int=3, num_derived_observations: int=2) -> Tuple[str, str]:
        logger.info('Generating initial observations')
        initial_observations = self.generate_observations(problem, num_initial_observations)
        logger.info('Generating derived observations')
        derived_observations = self.generate_derived_observations(problem, initial_observations, num_derived_observations)
        all_observations = initial_observations + derived_observations
        logger.info('Generating solution based on observations')
        natural_language_solution = self.generate_solution(problem, all_observations)
        logger.info('Implementing solution in Python')
        python_implementation = self.implement_solution(problem, natural_language_solution)
        return (natural_language_solution, python_implementation)

    def solve_multiple(self, problem: str, n: int, num_initial_observations: int=3, num_derived_observations: int=2) -> List[str]:
        solutions = []
        for _ in range(n):
            _, python_implementation = self.solve(problem, num_initial_observations, num_derived_observations)
            solutions.append(python_implementation)
        return solutions

def solve_multiple(self, problem: str, n: int, num_initial_observations: int=3, num_derived_observations: int=2) -> List[str]:
    solutions = []
    for _ in range(n):
        _, python_implementation = self.solve(problem, num_initial_observations, num_derived_observations)
        solutions.append(python_implementation)
    return solutions

class BrowserSessionManager:
    """
    Manages a single browser session across multiple searches.
    Implements context manager for automatic cleanup.
    """

    def __init__(self, headless: bool=False, timeout: int=30):
        self.headless = headless
        self.timeout = timeout
        self._searcher = None
        self._search_count = 0
        self._session_start_time = None

    def __enter__(self):
        """Context manager entry - ensures browser is ready"""
        self.get_or_create_searcher()
        self._session_start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures browser cleanup"""
        self.close()
        return False

    def get_or_create_searcher(self) -> 'GoogleSearcher':
        """Get existing searcher or create a new one"""
        if self._searcher is None or self._searcher.driver is None:
            if self._searcher is None:
                print('🌐 Creating new browser session for research...')
            else:
                print('🔄 Recreating browser session (previous session invalidated)...')
            self._searcher = GoogleSearcher(headless=self.headless, timeout=self.timeout)
        return self._searcher

    def search(self, query: str, num_results: int=10, delay_seconds: Optional[int]=None) -> List[Dict[str, str]]:
        """Perform a search using the managed browser session with automatic recovery"""
        try:
            searcher = self.get_or_create_searcher()
            self._search_count += 1
            session_duration = time.time() - self._session_start_time if self._session_start_time else 0
            print(f'🔍 Search #{self._search_count} in current session (instance: {id(self)}, duration: {session_duration:.1f}s): {query[:50]}...')
            return searcher.search(query, num_results, delay_seconds)
        except Exception as e:
            error_msg = str(e).lower()
            if 'invalid session id' in error_msg or 'session deleted' in error_msg:
                print('⚠️  Browser session invalidated, attempting recovery...')
                if self._searcher:
                    try:
                        self._searcher.close()
                    except:
                        pass
                self._searcher = None
                try:
                    searcher = self.get_or_create_searcher()
                    print('✅ New browser session created, retrying search...')
                    return searcher.search(query, num_results, delay_seconds)
                except Exception as retry_error:
                    print(f'❌ Session recovery failed: {str(retry_error)}')
                    return []
            else:
                print(f'❌ Search error: {str(e)}')
                return []

    def close(self):
        """Close the browser session"""
        if self._searcher is not None:
            try:
                self._searcher.close()
                if self._session_start_time:
                    duration = time.time() - self._session_start_time
                    print(f'🏁 Browser session closed after {self._search_count} searches ({duration:.1f}s)')
            except Exception as e:
                print(f'⚠️ Error closing browser session: {e}')
            finally:
                self._searcher = None
                self._search_count = 0
                self._session_start_time = None

    def is_active(self) -> bool:
        """Check if browser session is active"""
        return self._searcher is not None and self._searcher.driver is not None

def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit - ensures browser cleanup"""
    self.close()
    return False

def get_or_create_searcher(self) -> 'GoogleSearcher':
    """Get existing searcher or create a new one"""
    if self._searcher is None or self._searcher.driver is None:
        if self._searcher is None:
            print('🌐 Creating new browser session for research...')
        else:
            print('🔄 Recreating browser session (previous session invalidated)...')
        self._searcher = GoogleSearcher(headless=self.headless, timeout=self.timeout)
    return self._searcher

def run(system_prompt: str, initial_query: str, client=None, model: str=None, request_config: Optional[Dict]=None) -> Tuple[str, int]:
    """
    Web search plugin that uses Chrome to search Google and return results
    
    Args:
        system_prompt: System prompt for the conversation
        initial_query: User's query that may contain search requests
        client: OpenAI client (unused for this plugin)
        model: Model name (unused for this plugin) 
        request_config: Optional configuration dict with keys:
            - num_results: Number of search results (default: 10)
            - delay_seconds: Delay between searches in seconds (default: random 4-32)
                            Set to 0 to disable delays, or specify exact seconds
            - headless: Run browser in headless mode (default: False)
            - timeout: Browser timeout in seconds (default: 30)
            - session_manager: BrowserSessionManager instance for session reuse
    
    Returns:
        Tuple of (enhanced_query_with_search_results, completion_tokens)
    """
    config = request_config or {}
    num_results = config.get('num_results', 10)
    delay_seconds = config.get('delay_seconds', None)
    headless = config.get('headless', False)
    timeout = config.get('timeout', 30)
    session_manager = config.get('session_manager', None)
    search_queries = extract_search_queries(initial_query)
    if not search_queries:
        return (initial_query, 0)
    own_session = session_manager is None
    try:
        if own_session:
            searcher = GoogleSearcher(headless=headless, timeout=timeout)
        enhanced_query = initial_query
        for query in search_queries:
            if session_manager:
                results = session_manager.search(query, num_results=num_results, delay_seconds=delay_seconds)
            else:
                results = searcher.search(query, num_results=num_results, delay_seconds=delay_seconds)
            if results:
                formatted_results = format_search_results(query, results)
                enhanced_query = f'{enhanced_query}\n\n[Web Search Results]:\n{formatted_results}'
            else:
                enhanced_query = f"{enhanced_query}\n\n[Web Search Results]:\nNo results found for '{query}'. This may be due to network issues or search restrictions."
        return (enhanced_query, 0)
    except Exception as e:
        error_msg = f'Web search error: {str(e)}'
        enhanced_query = f'{initial_query}\n\n[Web Search Error]: {error_msg}'
        return (enhanced_query, 0)
    finally:
        if own_session and 'searcher' in locals():
            searcher.close()

def run(system_prompt, initial_query, client, model, **kwargs):
    try:
        router_model, tokenizer, device = load_optillm_model()
        input_ids, attention_mask = preprocess_input(tokenizer, system_prompt, initial_query)
        predicted_approach, _ = predict_approach(router_model, input_ids, attention_mask, device)
        print(f'Router predicted approach: {predicted_approach}')
        if predicted_approach == 'none':
            response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}])
            return (response.choices[0].message.content, response.usage.completion_tokens)
        elif predicted_approach == 'mcts':
            return chat_with_mcts(system_prompt, initial_query, client, model, **kwargs)
        elif predicted_approach == 'bon':
            return best_of_n_sampling(system_prompt, initial_query, client, model, **kwargs)
        elif predicted_approach == 'moa':
            return mixture_of_agents(system_prompt, initial_query, client, model)
        elif predicted_approach == 'rto':
            return round_trip_optimization(system_prompt, initial_query, client, model)
        elif predicted_approach == 'z3':
            z3_solver = Z3SymPySolverSystem(system_prompt, client, model)
            return z3_solver.process_query(initial_query)
        elif predicted_approach == 'self_consistency':
            return advanced_self_consistency_approach(system_prompt, initial_query, client, model)
        elif predicted_approach == 'pvg':
            return inference_time_pv_game(system_prompt, initial_query, client, model)
        elif predicted_approach == 'rstar':
            rstar = RStar(system_prompt, client, model, **kwargs)
            return rstar.solve(initial_query)
        elif predicted_approach == 'cot_reflection':
            return cot_reflection(system_prompt, initial_query, client, model, **kwargs)
        elif predicted_approach == 'plansearch':
            return plansearch(system_prompt, initial_query, client, model, **kwargs)
        elif predicted_approach == 'leap':
            return leap(system_prompt, initial_query, client, model)
        elif predicted_approach == 're2':
            return re2_approach(system_prompt, initial_query, client, model, **kwargs)
        else:
            raise ValueError(f'Unknown approach: {predicted_approach}')
    except Exception as e:
        print(f'Error in router plugin: {str(e)}. Falling back to direct model usage.')
        response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}])
        return (response.choices[0].message.content, response.usage.completion_tokens)

class ApproachHandler:
    """Dynamically handles both approaches and plugins"""

    def __init__(self):
        self._approaches_cache = {}
        self._plugins_cache = {}
        self._discovered = False

    def handle(self, name: str, system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Optional[Tuple[str, int]]:
        """
        Try to handle the given name as an approach or plugin.
        Returns None if not found, otherwise returns (response, tokens)
        """
        if not self._discovered:
            self._discover_handlers()
            self._discovered = True
        if name in self._approaches_cache:
            logger.info(f"Routing approach '{name}' through proxy")
            handler = self._approaches_cache[name]
            return self._execute_handler(handler, system_prompt, initial_query, client, model, request_config)
        if name in self._plugins_cache:
            logger.info(f"Routing plugin '{name}' through proxy")
            handler = self._plugins_cache[name]
            return self._execute_handler(handler, system_prompt, initial_query, client, model, request_config)
        logger.debug(f"'{name}' not recognized as approach or plugin")
        return None

    def _discover_handlers(self):
        """Discover available approaches and plugins dynamically"""
        self._discover_approaches()
        self._discover_plugins()
        logger.info(f'Discovered {len(self._approaches_cache)} approaches, {len(self._plugins_cache)} plugins')

    def _discover_approaches(self):
        """Discover built-in approaches from optillm package"""
        approach_modules = {'mcts': ('optillm.mcts', 'chat_with_mcts'), 'bon': ('optillm.bon', 'best_of_n_sampling'), 'moa': ('optillm.moa', 'mixture_of_agents'), 'rto': ('optillm.rto', 'round_trip_optimization'), 'self_consistency': ('optillm.self_consistency', 'advanced_self_consistency_approach'), 'pvg': ('optillm.pvg', 'inference_time_pv_game'), 'z3': ('optillm.z3_solver', None), 'rstar': ('optillm.rstar', None), 'cot_reflection': ('optillm.cot_reflection', 'cot_reflection'), 'plansearch': ('optillm.plansearch', 'plansearch'), 'leap': ('optillm.leap', 'leap'), 're2': ('optillm.reread', 're2_approach'), 'cepo': ('optillm.cepo.cepo', 'cepo')}
        for name, (module_path, func_name) in approach_modules.items():
            try:
                module = importlib.import_module(module_path)
                if name == 'z3':
                    solver_class = getattr(module, 'Z3SymPySolverSystem')
                    self._approaches_cache[name] = lambda s, q, c, m, **kw: solver_class(s, c, m).process_query(q)
                elif name == 'rstar':
                    rstar_class = getattr(module, 'RStar')
                    self._approaches_cache[name] = lambda s, q, c, m, **kw: rstar_class(s, c, m, **kw).solve(q)
                elif name == 'cepo':
                    cepo_func = getattr(module, func_name)
                    self._approaches_cache[name] = cepo_func
                elif func_name:
                    self._approaches_cache[name] = getattr(module, func_name)
            except (ImportError, AttributeError) as e:
                logger.debug(f"Could not load approach '{name}': {e}")

    def _discover_plugins(self):
        """Discover available plugins dynamically"""
        try:
            import optillm
            import os
            import glob
            package_dir = Path(optillm.__file__).parent / 'plugins'
            plugin_files = []
            if package_dir.exists():
                plugin_files.extend(glob.glob(str(package_dir / '*.py')))
            for plugin_file in plugin_files:
                if '__pycache__' in plugin_file or '__init__' in plugin_file:
                    continue
                try:
                    module_name = Path(plugin_file).stem
                    if module_name == 'proxy_plugin':
                        continue
                    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'SLUG') and hasattr(module, 'run'):
                            slug = getattr(module, 'SLUG')
                            run_func = getattr(module, 'run')
                            self._plugins_cache[slug] = run_func
                except Exception as e:
                    logger.debug(f'Could not load plugin from {plugin_file}: {e}')
        except Exception as e:
            logger.debug(f'Error discovering plugins: {e}')

    def _execute_handler(self, handler, system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Tuple[str, int]:
        """Execute a handler function with proper signature detection"""
        try:
            sig = inspect.signature(handler)
            params = sig.parameters
            args = [system_prompt, initial_query, client, model]
            kwargs = {}
            if 'request_config' in params:
                kwargs['request_config'] = request_config
            if any((p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())):
                if request_config:
                    safe_kwargs = {k: v for k, v in request_config.items() if k not in ['model', 'messages', 'system_prompt', 'initial_query']}
                    kwargs.update(safe_kwargs)
            return handler(*args, **kwargs)
        except Exception as e:
            logger.error(f'Error executing handler: {e}')
            raise

def _discover_approaches(self):
    """Discover built-in approaches from optillm package"""
    approach_modules = {'mcts': ('optillm.mcts', 'chat_with_mcts'), 'bon': ('optillm.bon', 'best_of_n_sampling'), 'moa': ('optillm.moa', 'mixture_of_agents'), 'rto': ('optillm.rto', 'round_trip_optimization'), 'self_consistency': ('optillm.self_consistency', 'advanced_self_consistency_approach'), 'pvg': ('optillm.pvg', 'inference_time_pv_game'), 'z3': ('optillm.z3_solver', None), 'rstar': ('optillm.rstar', None), 'cot_reflection': ('optillm.cot_reflection', 'cot_reflection'), 'plansearch': ('optillm.plansearch', 'plansearch'), 'leap': ('optillm.leap', 'leap'), 're2': ('optillm.reread', 're2_approach'), 'cepo': ('optillm.cepo.cepo', 'cepo')}
    for name, (module_path, func_name) in approach_modules.items():
        try:
            module = importlib.import_module(module_path)
            if name == 'z3':
                solver_class = getattr(module, 'Z3SymPySolverSystem')
                self._approaches_cache[name] = lambda s, q, c, m, **kw: solver_class(s, c, m).process_query(q)
            elif name == 'rstar':
                rstar_class = getattr(module, 'RStar')
                self._approaches_cache[name] = lambda s, q, c, m, **kw: rstar_class(s, c, m, **kw).solve(q)
            elif name == 'cepo':
                cepo_func = getattr(module, func_name)
                self._approaches_cache[name] = cepo_func
            elif func_name:
                self._approaches_cache[name] = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not load approach '{name}': {e}")

class ResearchSessionState:
    """
    Thread-safe session state manager for deep research.
    Ensures only one browser session is active per research query.
    """

    def __init__(self):
        self._sessions: Dict[str, BrowserSessionManager] = {}
        self._lock = threading.Lock()
        self._session_timestamps: Dict[str, float] = {}
        self._max_session_age = 300

    def get_or_create_session(self, session_id: str, headless: bool=False, timeout: int=30) -> Optional[BrowserSessionManager]:
        """
        Get an existing session or create a new one for the given session ID.
        """
        with self._lock:
            print(f'🔍 Session state: {len(self._sessions)} active sessions, checking for ID: {session_id}')
            self._cleanup_old_sessions()
            if session_id in self._sessions:
                session = self._sessions[session_id]
                print(f'📋 Found existing session for ID: {session_id}, active: {session.is_active()}, instance: {id(session)}')
                if session.is_active():
                    print(f'♻️  Reusing existing browser session for research ID: {session_id}')
                    return session
                else:
                    print(f'🔄 Removing inactive session for research ID: {session_id}')
                    del self._sessions[session_id]
                    if session_id in self._session_timestamps:
                        del self._session_timestamps[session_id]
            print(f'🌐 Creating new browser session for research ID: {session_id}')
            session = BrowserSessionManager(headless=headless, timeout=timeout)
            session.get_or_create_searcher()
            self._sessions[session_id] = session
            self._session_timestamps[session_id] = time.time()
            print(f'✅ Created new session instance: {id(session)} for ID: {session_id}')
            print(f'📊 Total active sessions: {len(self._sessions)}')
            return session

    def remove_session(self, session_id: str):
        """
        Remove and close a session.
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                try:
                    session.close()
                except Exception as e:
                    print(f'⚠️ Error closing session {session_id}: {e}')
                del self._sessions[session_id]
                if session_id in self._session_timestamps:
                    del self._session_timestamps[session_id]
                print(f'🏁 Removed session for research ID: {session_id}')

    def _cleanup_old_sessions(self):
        """
        Clean up sessions older than max_session_age.
        """
        current_time = time.time()
        sessions_to_remove = []
        for session_id, timestamp in self._session_timestamps.items():
            if current_time - timestamp > self._max_session_age:
                sessions_to_remove.append(session_id)
        for session_id in sessions_to_remove:
            print(f'🧹 Cleaning up old session: {session_id}')
            if session_id in self._sessions:
                try:
                    self._sessions[session_id].close()
                except:
                    pass
                del self._sessions[session_id]
            del self._session_timestamps[session_id]

def remove_session(self, session_id: str):
    """
        Remove and close a session.
        """
    with self._lock:
        if session_id in self._sessions:
            session = self._sessions[session_id]
            try:
                session.close()
            except Exception as e:
                print(f'⚠️ Error closing session {session_id}: {e}')
            del self._sessions[session_id]
            if session_id in self._session_timestamps:
                del self._session_timestamps[session_id]
            print(f'🏁 Removed session for research ID: {session_id}')

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

