# Cluster 2

def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute cosine similarity between two texts using TF-IDF vectorization.
    This is a local implementation that doesn't require any external API.
    """
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        logger.error(f'Error computing similarity: {e}')
        return 0.0

class RStar:

    def __init__(self, system: str, client, model: str, max_depth: int=3, num_rollouts: int=5, c: float=1.4, request_id: str=None):
        self.client = client
        self.model_name = model
        self.max_depth = max_depth
        self.num_rollouts = num_rollouts
        self.c = c
        self.actions = ['A1', 'A2', 'A3', 'A4', 'A5']
        self.original_question = None
        self.system = system
        self.rstar_completion_tokens = 0
        self.request_id = request_id
        logger.debug(f'Initialized RStar with model: {model}, max_depth: {max_depth}, num_rollouts: {num_rollouts}')

    async def generate_response_async(self, prompt: str) -> str:
        return await asyncio.to_thread(self.generate_response, prompt)

    async def expand_async(self, node: Node, action: str) -> Node:
        prompt = self.create_prompt(node.state, action)
        new_state = await self.generate_response_async(prompt)
        child_node = Node(new_state, action, node)
        node.children.append(child_node)
        logger.debug(f'Expanded node with action: {action}')
        return child_node

    async def simulate_async(self, node: Node) -> float:
        current_node = node
        depth = 0
        logger.debug('Starting simulation')
        while depth < self.max_depth:
            if not current_node.children:
                action = random.choice(self.actions)
                current_node = await self.expand_async(current_node, action)
            else:
                current_node = random.choice(current_node.children)
            depth += 1
        value = self.evaluate(current_node)
        logger.debug(f'Simulation complete. Final value: {value}')
        return value

    async def mcts_async(self, root_state: str) -> List[Node]:
        root = Node(root_state, None)
        tasks = []
        for _ in range(self.num_rollouts):
            tasks.append(self.mcts_rollout_async(root))
        await asyncio.gather(*tasks)
        return self.extract_trajectories(root)

    async def mcts_rollout_async(self, root: Node):
        node = root
        while node.children:
            node, _ = self.select_action(node)
        action = random.choice(self.actions)
        if len(node.children) < len(self.actions):
            node = await self.expand_async(node, action)
        value = await self.simulate_async(node)
        self.backpropagate(node, value)

    async def solve_async(self, question: str) -> str:
        self.original_question = question
        logger.info(f'Solving question: {question}')
        trajectories = await self.mcts_async(question)
        if not trajectories:
            logger.warning('No trajectories found. Unable to solve the question.')
            return 'Unable to solve the question due to insufficient reasoning paths.'
        final_trajectory = self.select_final_trajectory(trajectories)
        logger.debug(f'Final trajectory: {[node.state for node in final_trajectory]}')
        answers = [self.extract_answer(node.state) for node in final_trajectory]
        final_answer = self.select_best_answer(answers)
        logger.info(f'Selected final answer: {final_answer}')
        return (final_answer, self.rstar_completion_tokens)

    def generate_response(self, prompt: str) -> str:
        logger.debug(f'Generating response for prompt: {prompt[:100]}...')
        provider_request = {'model': self.model_name, 'messages': [{'role': 'system', 'content': 'You are a helpful assistant focused on solving mathematical problems. Stick to the given question and avoid introducing new scenarios.'}, {'role': 'user', 'content': prompt}], 'max_tokens': 4096, 'temperature': 0.2}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.rstar_completion_tokens += response.usage.completion_tokens
        generated_response = response.choices[0].message.content.strip()
        logger.debug(f'Generated response: {generated_response}')
        return generated_response

    def select_action(self, node: Node) -> Tuple[Node, str]:
        if not node.children:
            action = random.choice(self.actions)
            logger.debug(f'Selected random action: {action}')
            return (node, action)
        uct_values = []
        for child in node.children:
            if child.visits == 0:
                uct = float('inf')
            else:
                uct = child.value / child.visits + self.c * math.sqrt(math.log(node.visits) / child.visits)
            uct_values.append(uct)
        best_child = node.children[uct_values.index(max(uct_values))]
        logger.debug(f'Selected action: {best_child.action}')
        return (best_child, best_child.action)

    def expand(self, node: Node, action: str) -> Node:
        prompt = self.create_prompt(node.state, action)
        new_state = self.generate_response(prompt)
        child_node = Node(new_state, action, node)
        node.children.append(child_node)
        logger.debug(f'Expanded node with action: {action}')
        return child_node

    def simulate(self, node: Node) -> float:
        current_node = node
        depth = 0
        logger.debug('Starting simulation')
        while depth < self.max_depth:
            if not current_node.children:
                action = random.choice(self.actions)
                current_node = self.expand(current_node, action)
            else:
                current_node = random.choice(current_node.children)
            depth += 1
        value = self.evaluate(current_node)
        logger.debug(f'Simulation complete. Final value: {value}')
        return value

    def backpropagate(self, node: Node, value: float):
        logger.debug('Starting backpropagation')
        while node:
            node.visits += 1
            node.value += value
            node = node.parent
        logger.debug('Backpropagation complete')

    def mcts(self, root_state: str) -> List[Node]:
        root = Node(root_state, None)
        logger.debug(f'Starting MCTS with {self.num_rollouts} rollouts')
        for i in range(self.num_rollouts):
            logger.debug(f'Rollout {i + 1}/{self.num_rollouts}')
            node = root
            while node.children:
                node, _ = self.select_action(node)
            action = random.choice(self.actions)
            if len(node.children) < len(self.actions):
                node = self.expand(node, action)
            value = self.simulate(node)
            self.backpropagate(node, value)
        logger.debug('MCTS complete')
        return self.extract_trajectories(root)

    def extract_trajectories(self, root: Node) -> List[List[Node]]:
        logger.debug('Extracting trajectories')
        trajectories = []
        stack = [(root, [])]
        while stack:
            node, path = stack.pop()
            if not node.children:
                trajectories.append(path + [node])
            else:
                for child in node.children:
                    stack.append((child, path + [node]))
        logger.debug(f'Extracted {len(trajectories)} trajectories')
        return trajectories

    def mutual_consistency(self, trajectory: List[Node]) -> bool:
        split_index = random.randint(1, len(trajectory) - 1)
        partial_trajectory = trajectory[:split_index]
        prompt = self.create_discriminator_prompt(partial_trajectory)
        completion = self.generate_response(prompt)
        is_consistent = self.compare_completions(completion, trajectory[split_index:])
        logger.debug(f'Mutual consistency check: {('Passed' if is_consistent else 'Failed')}')
        return is_consistent

    def select_final_trajectory(self, trajectories: List[List[Node]]) -> List[Node]:
        logger.debug('Selecting final trajectory')
        valid_trajectories = [t for t in trajectories if self.mutual_consistency(t)]
        logger.debug(f'Found {len(valid_trajectories)} valid trajectories')
        if not valid_trajectories:
            logger.warning('No valid trajectories found. Selecting based on value/visits.')
            return max(trajectories, key=lambda t: self.trajectory_score(t))
        return max(valid_trajectories, key=lambda t: self.trajectory_score(t))

    def trajectory_score(self, trajectory: List[Node]) -> float:
        if not trajectory:
            return float('-inf')
        last_node = trajectory[-1]
        if last_node.visits == 0:
            return last_node.value
        return last_node.value / last_node.visits

    def select_best_answer(self, answers: List[Tuple[str, float]]) -> str:
        valid_answers = [(answer, conf) for answer, conf in answers if answer]
        if not valid_answers:
            return 'Unable to determine a valid answer.'
        answer_counts = {}
        for answer, conf in valid_answers:
            if answer in answer_counts:
                answer_counts[answer] = (answer_counts[answer][0] + 1, max(answer_counts[answer][1], conf))
            else:
                answer_counts[answer] = (1, conf)
        sorted_answers = sorted(answer_counts.items(), key=lambda x: (-x[1][1], -x[1][0]))
        best_answer, (count, conf) = sorted_answers[0]
        logger.debug(f'Selected best answer: {best_answer} (count: {count}, confidence: {conf})')
        return best_answer

    def create_prompt(self, state: str, action: str) -> str:
        question = self.original_question if hasattr(self, 'original_question') else 'the original question'
        prompts = {'A1': f'Given the current state: {state}\nGenerate the next logical step in solving {question}.\nYour response should be a single, clear thought that moves towards the solution.\nIf you can determine the final answer at this step, state it clearly.', 'A2': f'Given the current state: {state}\nContinue the reasoning process to solve {question}.\nProvide the remaining steps needed to reach the final answer.\nEach step should be clear and directly related to solving the problem.', 'A3': f'Given the current state: {state}\nIdentify a key sub-question that needs to be answered to solve {question}.\nState this sub-question clearly, then provide its answer.\nExplain how this sub-question and its answer contribute to solving the main problem.', 'A4': f'Given the current state: {state}\nRe-examine the previous step in solving {question} using Chain-of-Thought reasoning.\nBreak down your thinking process explicitly, showing each logical step.\nIf you reach a conclusion, state it clearly.', 'A5': f'Given the current state: {state}\nRephrase {question} by clearly listing all relevant conditions and unknowns.\nEnsure that your rephrasing captures all important details from the original question.\nThis rephrasing should help clarify the problem and guide the solution process.'}
        prompt = prompts[action] + "\n\nIf you determine the final answer, explicitly state 'The final answer is [your numeric answer]' at the end of your response."
        logger.debug(f'Created prompt for action {action}: {prompt}')
        return prompt

    def create_discriminator_prompt(self, partial_trajectory: List[Node]) -> str:
        states = [node.state for node in partial_trajectory]
        partial_reasoning = ' '.join(states)
        return f'Given the partial reasoning:\n{partial_reasoning}\nComplete the reasoning to solve the problem:'

    def compare_completions(self, completion: str, remaining_trajectory: List[Node]) -> bool:
        remaining_states = [node.state for node in remaining_trajectory]
        remaining_reasoning = ' '.join(remaining_states)
        completion_words = set(completion.lower().replace('.', '').replace(',', '').split())
        trajectory_words = set(remaining_reasoning.lower().replace('.', '').replace(',', '').split())
        overlap = len(completion_words.intersection(trajectory_words))
        total_words = len(completion_words.union(trajectory_words))
        return overlap / total_words > 0.7

    def evaluate(self, node: Node) -> float:
        answer, confidence = self.extract_answer(node.state)
        try:
            float(answer)
            logger.debug(f'Evaluated node. Answer: {answer}, Confidence: {confidence}, Value: {confidence}')
            return confidence
        except ValueError:
            logger.debug(f'Evaluated node. Answer: {answer}, Confidence: {confidence}, Value: 0.0')
            return 0.0

    def extract_answer(self, final_state: str) -> Tuple[str, float]:
        logger.debug(f'Extracting answer from state: {final_state}')
        patterns = ['The answer is (\\d+)', 'The final answer is (\\d+)', 'Therefore, the answer is (\\d+)', 'So, the answer is (\\d+)', 'Thus, the answer is (\\d+)', 'In conclusion, the answer is (\\d+)']
        for pattern in patterns:
            match = re.search(pattern, final_state)
            if match:
                answer = match.group(1)
                confidence = 1.0
                logger.debug(f"Answer found using pattern '{pattern}': {answer}")
                return (answer, confidence)
        numbers = re.findall('\\d+', final_state)
        if numbers:
            answer = numbers[-1]
            confidence = 0.5
            logger.debug(f'No pattern found. Using last number as answer: {answer}')
            return (answer, confidence)
        logger.warning('No answer found in the state.')
        return ('', 0.0)

    def solve(self, question: str) -> str:
        """
        Synchronous wrapper for solve_async method.
        """
        return asyncio.run(self.solve_async(question))

def trajectory_score(self, trajectory: List[Node]) -> float:
    if not trajectory:
        return float('-inf')
    last_node = trajectory[-1]
    if last_node.visits == 0:
        return last_node.value
    return last_node.value / last_node.visits

def evaluate(self, node: Node) -> float:
    answer, confidence = self.extract_answer(node.state)
    try:
        float(answer)
        logger.debug(f'Evaluated node. Answer: {answer}, Confidence: {confidence}, Value: {confidence}')
        return confidence
    except ValueError:
        logger.debug(f'Evaluated node. Answer: {answer}, Confidence: {confidence}, Value: 0.0')
        return 0.0

def as_numerical(x):
    if z3.is_expr(x):
        if z3.is_int_value(x) or z3.is_rational_value(x):
            return float(x.as_decimal(20))
        elif z3.is_algebraic_value(x):
            return x.approx(20)
    return float(x)

class Z3SymPySolverSystem:

    def __init__(self, system_prompt: str, client, model: str, timeout: int=30, request_id: str=None):
        self.system_prompt = system_prompt
        self.model = model
        self.client = client
        self.timeout = timeout
        self.solver_completion_tokens = 0
        self.request_id = request_id
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def process_query(self, query: str) -> str:
        try:
            analysis = self.analyze_query(query)
            if 'SOLVER_CAN_BE_APPLIED: True' not in analysis:
                return (self.standard_llm_inference(query), self.solver_completion_tokens)
            formulation = self.extract_and_validate_expressions(analysis)
            solver_result = self.solve_with_z3_sympy(formulation)
            return (self.generate_response(query, analysis, solver_result), self.solver_completion_tokens)
        except Exception as e:
            logging.error(f'An error occurred while processing the query with Z3 and SymPy, returning standard llm inference results: {str(e)}')
            return (self.standard_llm_inference(query), self.solver_completion_tokens)

    def analyze_query(self, query: str) -> str:
        analysis_prompt = f'Analyze the given query and determine if it can be solved using Z3 or SymPy:\n\n1. Identify variables, constraints, and objectives.\n2. Determine the problem type (e.g., SAT, optimization, symbolic manipulation).\n3. Decide if Z3, SymPy, or a combination of both is suitable.\n\nIf Z3 or SymPy can be applied, provide Python code using the appropriate library (or both) to solve the problem. Make sure you define any additional methods you need for solving the problem.\nThe code will be executed in an environment with Z3 and SymPy available, so do not include any other libraries or modules.\n\nQuery: {query}\n\nRespond with:\nSOLVER_CAN_BE_APPLIED: [True/False]\n\nSOLVER_FORMULATION:\n```python\n# Z3 and/or SymPy code here\n```\n\nAnalysis:\n[Your step-by-step analysis]\n'
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': analysis_prompt}], 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
        analysis_response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = analysis_response.model_dump() if hasattr(analysis_response, 'model_dump') else analysis_response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = analysis_response.usage.completion_tokens
        return analysis_response.choices[0].message.content

    def generate_response(self, query: str, analysis: str, solver_result: Dict[str, Any]) -> str:
        if solver_result.get('status') != 'success':
            return self.standard_llm_inference(query)
        response_prompt = f'Provide a clear answer to the query using the analysis and solver result:\n\nQuery: {query}\n\nAnalysis: {analysis}\n\nSolver Result: {solver_result.get('output')}\n\nResponse:\n'
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': response_prompt}], 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = response.usage.completion_tokens
        return response.choices[0].message.content

    def standard_llm_inference(self, query: str) -> str:
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': query}], 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = response.usage.completion_tokens
        return response.choices[0].message.content

    def extract_and_validate_expressions(self, analysis: str) -> str:
        formulation = re.search('```python\\n([\\s\\S]+?)```', analysis)
        if formulation:
            return formulation.group(1).strip()
        raise ValueError('No valid Z3 or SymPy formulation found in the analysis.')

    def solve_with_z3_sympy(self, formulation: str, max_attempts: int=3) -> Dict[str, Any]:
        for attempt in range(max_attempts):
            output = self.execute_solver_code(formulation)
            if 'Error:' not in output:
                return {'status': 'success', 'output': output}
            error_prompt = f'Fix the Z3 or SymPy code that resulted in an error. Follow these steps:\n\n    1. Review the original code and the error message carefully.\n    2. Analyze the error and identify its root cause.\n    3. Think through the necessary changes to fix the error.\n    4. Generate a corrected version of the code.\n\n    Original Code:\n    {formulation}\n\n    Error Message:\n    {output}\n\n    Step-by-Step Analysis:\n    [Provide your step-by-step analysis here]\n\n    Corrected Z3 or SymPy Code:\n    ```python\n    # Corrected code here\n    ```\n    '
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': error_prompt}], 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.solver_completion_tokens = response.usage.completion_tokens
            formulation = self.extract_and_validate_expressions(response.choices[0].message.content)
        return {'status': 'failed', 'output': 'Failed to solve after multiple attempts.'}

    def execute_solver_code(self, code: str) -> str:
        logging.info('Executing Z3 and SymPy solver code')
        logging.info(f'Code: {code}')
        try:
            _ = ast.parse(code)
        except SyntaxError as e:
            logging.error(f'Syntax error in provided code: {e}')
            return f'Error: Syntax error: {e}'
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(1) as pool:
            async_result = pool.apply_async(execute_code_in_process, (code,))
            try:
                status, result = async_result.get(timeout=self.timeout)
            except multiprocessing.TimeoutError:
                pool.terminate()
                logging.error('Execution timed out')
                return 'Error: Execution timed out'
        if status == 'error':
            logging.error(f'Execution error: {result}')
            return f'Error: {result}'
        logging.info('Z3 and SymPy solver code executed successfully')
        return result

def execute_solver_code(self, code: str) -> str:
    logging.info('Executing Z3 and SymPy solver code')
    logging.info(f'Code: {code}')
    try:
        _ = ast.parse(code)
    except SyntaxError as e:
        logging.error(f'Syntax error in provided code: {e}')
        return f'Error: Syntax error: {e}'
    ctx = multiprocessing.get_context('spawn')
    with ctx.Pool(1) as pool:
        async_result = pool.apply_async(execute_code_in_process, (code,))
        try:
            status, result = async_result.get(timeout=self.timeout)
        except multiprocessing.TimeoutError:
            pool.terminate()
            logging.error('Execution timed out')
            return 'Error: Execution timed out'
    if status == 'error':
        logging.error(f'Execution error: {result}')
        return f'Error: {result}'
    logging.info('Z3 and SymPy solver code executed successfully')
    return result

class Memory:

    def __init__(self, max_size: int=100):
        self.max_size = max_size
        self.items: List[str] = []
        self.vectorizer = TfidfVectorizer()
        self.vectors = None
        self.completion_tokens = 0

    def add(self, item: str):
        if len(self.items) >= self.max_size:
            self.items.pop(0)
        self.items.append(item)
        self.vectors = None

    def get_relevant(self, query: str, n: int=10) -> List[str]:
        if not self.items:
            return []
        if self.vectors is None:
            self.vectors = self.vectorizer.fit_transform(self.items)
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors).flatten()
        top_indices = similarities.argsort()[-n:][::-1]
        return [self.items[i] for i in top_indices]

def __init__(self, max_size: int=100):
    self.max_size = max_size
    self.items: List[str] = []
    self.vectorizer = TfidfVectorizer()
    self.vectors = None
    self.completion_tokens = 0

def get_relevant(self, query: str, n: int=10) -> List[str]:
    if not self.items:
        return []
    if self.vectors is None:
        self.vectors = self.vectorizer.fit_transform(self.items)
    query_vector = self.vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, self.vectors).flatten()
    top_indices = similarities.argsort()[-n:][::-1]
    return [self.items[i] for i in top_indices]

class StrategyDatabase:
    """Manages a collection of problem-solving strategies."""

    def __init__(self, db_path: str=STRATEGY_DB_PATH, metrics_path: str=STRATEGY_METRICS_PATH):
        self.db_path = db_path
        self.metrics_path = metrics_path
        self.strategies: List[Strategy] = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.vectors = None
        self.metrics = {'total_queries': 0, 'strategy_applications': 0, 'strategies_created': 0, 'strategies_refined': 0, 'successful_resolutions': 0, 'last_strategy_id': 0, 'reasoning_examples_collected': 0, 'strategies_merged': 0}
        self._load()

    def _load(self) -> None:
        """Load strategies and metrics from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.strategies = [Strategy.from_dict(s) for s in data]
                    for strategy in self.strategies:
                        if strategy.strategy_id.startswith('strategy_'):
                            try:
                                strategy_num = int(strategy.strategy_id.split('_')[1])
                                self.metrics['last_strategy_id'] = max(self.metrics['last_strategy_id'], strategy_num)
                            except ValueError:
                                pass
                logger.info(f'Loaded {len(self.strategies)} strategies from {self.db_path}')
                logger.info(f'Last strategy ID is {self.metrics['last_strategy_id']}')
            except Exception as e:
                logger.error(f'Error loading strategies: {str(e)}')
                self.strategies = []
        if os.path.exists(self.metrics_path):
            try:
                with open(self.metrics_path, 'r') as f:
                    metrics = json.load(f)
                    last_id = self.metrics['last_strategy_id']
                    self.metrics.update(metrics)
                    if 'last_strategy_id' in metrics:
                        self.metrics['last_strategy_id'] = max(last_id, metrics['last_strategy_id'])
                logger.info(f'Loaded metrics from {self.metrics_path}')
                logger.info(f'Last strategy ID is {self.metrics['last_strategy_id']}')
            except Exception as e:
                logger.error(f'Error loading metrics: {str(e)}')

    def _save(self) -> None:
        """Save strategies and metrics to disk."""
        try:
            with open(self.db_path, 'w') as f:
                json.dump([s.to_dict() for s in self.strategies], f, indent=2)
            logger.info(f'Saved {len(self.strategies)} strategies to {self.db_path}')
        except Exception as e:
            logger.error(f'Error saving strategies: {str(e)}')
        try:
            with open(self.metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f'Saved metrics to {self.metrics_path}')
        except Exception as e:
            logger.error(f'Error saving metrics: {str(e)}')

    def add_strategy(self, strategy: Strategy) -> None:
        """Add a new strategy to the database."""
        if strategy.strategy_id.startswith('strategy_'):
            try:
                strategy_num = int(strategy.strategy_id.split('_')[1])
                self.metrics['last_strategy_id'] = max(self.metrics['last_strategy_id'], strategy_num)
            except ValueError:
                pass
        exists = any((s.problem_type == strategy.problem_type for s in self.strategies))
        self.strategies.append(strategy)
        self.vectors = None
        self.metrics['strategies_created'] += 1
        self._save()
        if not exists:
            logger.info(f'Added first strategy for problem type: {strategy.problem_type}')
        else:
            logger.info(f'Added additional strategy for problem type: {strategy.problem_type}')

    def get_strategies_for_problem(self, problem_type: str) -> List[Strategy]:
        """Get all strategies for a specific problem type."""
        return [s for s in self.strategies if s.problem_type == problem_type]

    def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by its ID."""
        for strategy in self.strategies:
            if strategy.strategy_id == strategy_id:
                return strategy
        return None

    def update_strategy_performance(self, strategy_id: str, success: bool) -> None:
        """Update the performance metrics for a strategy."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy:
            strategy.record_attempt(success)
            self.metrics['strategy_applications'] += 1
            if success:
                self.metrics['successful_resolutions'] += 1
            self._save()

    def refine_strategy(self, strategy_id: str, refined_text: str) -> None:
        """Refine a strategy based on new insights."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy:
            strategy.update_strategy(refined_text)
            self.metrics['strategies_refined'] += 1
            self._save()

    def add_reasoning_example(self, strategy_id: str, reasoning: str) -> None:
        """Add a reasoning example to a strategy."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy and reasoning:
            strategy.add_reasoning_example(reasoning)
            self.metrics['reasoning_examples_collected'] += 1
            self._save()

    def add_example_to_strategy(self, strategy_id: str, example: str) -> None:
        """Add an example to a strategy."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy and example:
            strategy.add_example(example)
            self._save()

    def get_similar_strategies(self, query: str, n: int=5) -> List[Tuple[Strategy, float]]:
        """Find strategies similar to a query using TF-IDF similarity."""
        if not self.strategies:
            return []
        strategy_texts = [s.strategy_text for s in self.strategies]
        if self.vectors is None or len(self.vectors.shape) == 0 or self.vectors.shape[0] != len(strategy_texts):
            try:
                self.vectors = self.vectorizer.fit_transform(strategy_texts)
            except Exception as e:
                logger.error(f'Error creating strategy vectors: {str(e)}')
                return []
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.vectors).flatten()
            sorted_indices = similarities.argsort()[::-1]
            return [(self.strategies[i], float(similarities[i])) for i in sorted_indices[:n]]
        except Exception as e:
            logger.error(f'Error finding similar strategies: {str(e)}')
            return []

    def find_similar_strategy(self, problem_type: str, query: str, threshold: float=STRATEGY_CREATION_THRESHOLD) -> Optional[Tuple[Strategy, float]]:
        """
        Find a strategy of the same problem type that is similar to the query.
        
        Args:
            problem_type: The problem type to match
            query: The query to find similarity against
            threshold: The similarity threshold to consider a match
            
        Returns:
            Optional[Tuple[Strategy, float]]: The most similar strategy and its similarity score,
                                             or None if no similar strategy is found
        """
        if not self.strategies:
            return None
        type_strategies = [s for s in self.strategies if s.problem_type == problem_type]
        if not type_strategies:
            return None
        try:
            strategy_texts = [s.strategy_text for s in type_strategies]
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform(strategy_texts + [query])
            query_vector = vectors[-1]
            strategy_vectors = vectors[:-1]
            similarities = cosine_similarity(query_vector, strategy_vectors).flatten()
            if len(similarities) > 0:
                max_idx = similarities.argmax()
                max_similarity = similarities[max_idx]
                if max_similarity >= threshold:
                    return (type_strategies[max_idx], float(max_similarity))
        except Exception as e:
            logger.error(f'Error finding similar strategy: {str(e)}')
        return None

    def find_similar_examples(self, problem_type: str, query: str, threshold: float=STRATEGY_CREATION_THRESHOLD) -> Optional[Tuple[Strategy, float]]:
        """
        Find a strategy of the same problem type with examples similar to the query.
        
        Args:
            problem_type: The problem type to match
            query: The query to find similarity against
            threshold: The similarity threshold to consider a match
            
        Returns:
            Optional[Tuple[Strategy, float]]: The strategy with the most similar examples and the similarity score,
                                             or None if no similar strategy is found
        """
        if not self.strategies:
            return None
        type_strategies = [s for s in self.strategies if s.problem_type == problem_type]
        if not type_strategies:
            return None
        max_similarity = 0.0
        most_similar_strategy = None
        try:
            for strategy in type_strategies:
                if not strategy.examples:
                    continue
                vectorizer = TfidfVectorizer(stop_words='english')
                vectors = vectorizer.fit_transform(strategy.examples + [query])
                query_vector = vectors[-1]
                example_vectors = vectors[:-1]
                similarities = cosine_similarity(query_vector, example_vectors).flatten()
                if len(similarities) > 0:
                    strategy_max_similarity = similarities.max()
                    if strategy_max_similarity > max_similarity:
                        max_similarity = strategy_max_similarity
                        most_similar_strategy = strategy
            if most_similar_strategy and max_similarity >= threshold:
                return (most_similar_strategy, float(max_similarity))
        except Exception as e:
            logger.error(f'Error finding similar examples: {str(e)}')
        return None

    def get_next_strategy_id(self) -> str:
        """Generate a unique ID for a new strategy."""
        self.metrics['last_strategy_id'] += 1
        new_id = f'strategy_{self.metrics['last_strategy_id']}'
        logger.info(f'Generated new strategy ID: {new_id}')
        return new_id

    def increment_query_count(self) -> None:
        """Increment the total query count."""
        self.metrics['total_queries'] += 1
        self._save()

    def get_metrics(self) -> Dict[str, Any]:
        """Get the current metrics."""
        return self.metrics.copy()

    def prune_strategies(self, min_success_rate: float=0.3, min_attempts: int=5) -> int:
        """Prune strategies with poor performance."""
        initial_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s.total_attempts < min_attempts or s.success_rate >= min_success_rate]
        pruned_count = initial_count - len(self.strategies)
        if pruned_count > 0:
            self.vectors = None
            self._save()
        return pruned_count

    def merge_similar_strategies(self, similarity_threshold: float=STRATEGY_MERGING_THRESHOLD) -> int:
        """Merge strategies that are very similar to each other."""
        if len(self.strategies) <= 1:
            return 0
        merged_count = 0
        i = 0
        while i < len(self.strategies):
            j = i + 1
            while j < len(self.strategies):
                if self.strategies[i].problem_type == self.strategies[j].problem_type:
                    text_i = self.strategies[i].strategy_text
                    text_j = self.strategies[j].strategy_text
                    vectorizer = TfidfVectorizer(stop_words='english')
                    vectors = vectorizer.fit_transform([text_i, text_j])
                    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                    if similarity >= similarity_threshold:
                        merged_strategy = self._merge_two_strategies(self.strategies[i], self.strategies[j])
                        self.strategies[i] = merged_strategy
                        self.strategies.pop(j)
                        merged_count += 1
                        self.metrics['strategies_merged'] += 1
                        logger.info(f'Merged strategies {self.strategies[i].strategy_id} and {merged_strategy.strategy_id} with similarity {similarity:.2f}')
                    else:
                        j += 1
                else:
                    j += 1
            i += 1
        if merged_count > 0:
            self.vectors = None
            self._save()
        return merged_count

    def _merge_two_strategies(self, strategy1: Strategy, strategy2: Strategy) -> Strategy:
        """Merge two similar strategies into one."""
        if strategy1.success_rate >= strategy2.success_rate:
            base, other = (strategy1, strategy2)
        else:
            base, other = (strategy2, strategy1)
        merged = Strategy(strategy_id=base.strategy_id, problem_type=base.problem_type, strategy_text=base.strategy_text, examples=list(set(base.examples + other.examples)), success_count=base.success_count + other.success_count, total_attempts=base.total_attempts + other.total_attempts, created_at=min(base.created_at, other.created_at) if base.created_at and other.created_at else base.created_at, last_used=max(base.last_used, other.last_used) if base.last_used and other.last_used else base.last_used, last_updated=datetime.now().isoformat(), confidence=(base.confidence + other.confidence) / 2, tags=list(set(base.tags + other.tags)), reasoning_examples=base.reasoning_examples + other.reasoning_examples)
        if len(merged.reasoning_examples) > 5:
            merged.reasoning_examples = merged.reasoning_examples[-5:]
        return merged

    def limit_strategies_per_type(self, max_per_type: int=MAX_STRATEGIES_PER_TYPE) -> int:
        """
        Limit the number of strategies per problem type to the specified maximum in the database.
        This controls storage limit, not the number of strategies used during inference.
        Keeps the best performing strategies based on success rate and recency.
        
        Args:
            max_per_type: Maximum number of strategies to keep per problem type
            
        Returns:
            int: Number of strategies removed
        """
        strategies_by_type = {}
        for strategy in self.strategies:
            if strategy.problem_type not in strategies_by_type:
                strategies_by_type[strategy.problem_type] = []
            strategies_by_type[strategy.problem_type].append(strategy)
        to_remove = []
        for problem_type, strategies in strategies_by_type.items():
            if len(strategies) <= max_per_type:
                continue
            scored_strategies = []
            for strategy in strategies:
                recency_score = 0
                if strategy.last_used:
                    last_used = datetime.fromisoformat(strategy.last_used)
                    days_since = (datetime.now() - last_used).days
                    recency_score = max(0, 1.0 - min(1.0, days_since / 30.0))
                score = 0.7 * strategy.success_rate + 0.3 * recency_score
                scored_strategies.append((strategy, score))
            scored_strategies.sort(key=lambda x: x[1], reverse=True)
            for strategy, _ in scored_strategies[max_per_type:]:
                to_remove.append(strategy)
        initial_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s not in to_remove]
        removed_count = initial_count - len(self.strategies)
        if removed_count > 0:
            self.vectors = None
            self._save()
            logger.info(f'Removed {removed_count} excess strategies to maintain max {max_per_type} per type in database (storage limit)')
        return removed_count

def __init__(self, db_path: str=STRATEGY_DB_PATH, metrics_path: str=STRATEGY_METRICS_PATH):
    self.db_path = db_path
    self.metrics_path = metrics_path
    self.strategies: List[Strategy] = []
    self.vectorizer = TfidfVectorizer(stop_words='english')
    self.vectors = None
    self.metrics = {'total_queries': 0, 'strategy_applications': 0, 'strategies_created': 0, 'strategies_refined': 0, 'successful_resolutions': 0, 'last_strategy_id': 0, 'reasoning_examples_collected': 0, 'strategies_merged': 0}
    self._load()

def get_similar_strategies(self, query: str, n: int=5) -> List[Tuple[Strategy, float]]:
    """Find strategies similar to a query using TF-IDF similarity."""
    if not self.strategies:
        return []
    strategy_texts = [s.strategy_text for s in self.strategies]
    if self.vectors is None or len(self.vectors.shape) == 0 or self.vectors.shape[0] != len(strategy_texts):
        try:
            self.vectors = self.vectorizer.fit_transform(strategy_texts)
        except Exception as e:
            logger.error(f'Error creating strategy vectors: {str(e)}')
            return []
    try:
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors).flatten()
        sorted_indices = similarities.argsort()[::-1]
        return [(self.strategies[i], float(similarities[i])) for i in sorted_indices[:n]]
    except Exception as e:
        logger.error(f'Error finding similar strategies: {str(e)}')
        return []

def find_similar_strategy(self, problem_type: str, query: str, threshold: float=STRATEGY_CREATION_THRESHOLD) -> Optional[Tuple[Strategy, float]]:
    """
        Find a strategy of the same problem type that is similar to the query.
        
        Args:
            problem_type: The problem type to match
            query: The query to find similarity against
            threshold: The similarity threshold to consider a match
            
        Returns:
            Optional[Tuple[Strategy, float]]: The most similar strategy and its similarity score,
                                             or None if no similar strategy is found
        """
    if not self.strategies:
        return None
    type_strategies = [s for s in self.strategies if s.problem_type == problem_type]
    if not type_strategies:
        return None
    try:
        strategy_texts = [s.strategy_text for s in type_strategies]
        vectorizer = TfidfVectorizer(stop_words='english')
        vectors = vectorizer.fit_transform(strategy_texts + [query])
        query_vector = vectors[-1]
        strategy_vectors = vectors[:-1]
        similarities = cosine_similarity(query_vector, strategy_vectors).flatten()
        if len(similarities) > 0:
            max_idx = similarities.argmax()
            max_similarity = similarities[max_idx]
            if max_similarity >= threshold:
                return (type_strategies[max_idx], float(max_similarity))
    except Exception as e:
        logger.error(f'Error finding similar strategy: {str(e)}')
    return None

def find_similar_examples(self, problem_type: str, query: str, threshold: float=STRATEGY_CREATION_THRESHOLD) -> Optional[Tuple[Strategy, float]]:
    """
        Find a strategy of the same problem type with examples similar to the query.
        
        Args:
            problem_type: The problem type to match
            query: The query to find similarity against
            threshold: The similarity threshold to consider a match
            
        Returns:
            Optional[Tuple[Strategy, float]]: The strategy with the most similar examples and the similarity score,
                                             or None if no similar strategy is found
        """
    if not self.strategies:
        return None
    type_strategies = [s for s in self.strategies if s.problem_type == problem_type]
    if not type_strategies:
        return None
    max_similarity = 0.0
    most_similar_strategy = None
    try:
        for strategy in type_strategies:
            if not strategy.examples:
                continue
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform(strategy.examples + [query])
            query_vector = vectors[-1]
            example_vectors = vectors[:-1]
            similarities = cosine_similarity(query_vector, example_vectors).flatten()
            if len(similarities) > 0:
                strategy_max_similarity = similarities.max()
                if strategy_max_similarity > max_similarity:
                    max_similarity = strategy_max_similarity
                    most_similar_strategy = strategy
        if most_similar_strategy and max_similarity >= threshold:
            return (most_similar_strategy, float(max_similarity))
    except Exception as e:
        logger.error(f'Error finding similar examples: {str(e)}')
    return None

def merge_similar_strategies(self, similarity_threshold: float=STRATEGY_MERGING_THRESHOLD) -> int:
    """Merge strategies that are very similar to each other."""
    if len(self.strategies) <= 1:
        return 0
    merged_count = 0
    i = 0
    while i < len(self.strategies):
        j = i + 1
        while j < len(self.strategies):
            if self.strategies[i].problem_type == self.strategies[j].problem_type:
                text_i = self.strategies[i].strategy_text
                text_j = self.strategies[j].strategy_text
                vectorizer = TfidfVectorizer(stop_words='english')
                vectors = vectorizer.fit_transform([text_i, text_j])
                similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                if similarity >= similarity_threshold:
                    merged_strategy = self._merge_two_strategies(self.strategies[i], self.strategies[j])
                    self.strategies[i] = merged_strategy
                    self.strategies.pop(j)
                    merged_count += 1
                    self.metrics['strategies_merged'] += 1
                    logger.info(f'Merged strategies {self.strategies[i].strategy_id} and {merged_strategy.strategy_id} with similarity {similarity:.2f}')
                else:
                    j += 1
            else:
                j += 1
        i += 1
    if merged_count > 0:
        self.vectors = None
        self._save()
    return merged_count

class AnswerExtractor:
    """Universal answer extractor using math-verify with fallback patterns"""

    def __init__(self):
        self.math_verify_timeout = 5

    def extract_answer(self, solution: str, problem_type: str='general', problem_id: Optional[int]=None) -> Optional[Any]:
        """
        Universal answer extraction using math-verify library with fallback patterns.

        Args:
            solution: The solution text to extract answer from
            problem_type: Type of problem (general, imo, aime, etc.)
            problem_id: Specific problem ID for customized extraction

        Returns:
            Extracted answer in appropriate format (int, str, list, etc.)
        """
        if not solution:
            return None
        logger.debug(f'Extracting answer from solution (type: {problem_type}, id: {problem_id})')
        math_verify_result = self._try_math_verify(solution)
        if math_verify_result is not None:
            logger.debug(f'Math-verify extracted: {math_verify_result}')
            return math_verify_result
        if problem_type == 'imo' and problem_id:
            specific_result = self._extract_imo_specific(solution, problem_id)
            if specific_result is not None:
                logger.debug(f'IMO-specific extracted: {specific_result}')
                return specific_result
        if problem_type == 'aime':
            aime_result = self._extract_aime_answer(solution)
            if aime_result is not None:
                logger.debug(f'AIME-style extracted: {aime_result}')
                return aime_result
        general_result = self._extract_general_answer(solution)
        if general_result is not None:
            logger.debug(f'General pattern extracted: {general_result}')
            return general_result
        logger.debug('No answer extracted')
        return None

    def _try_math_verify(self, solution: str) -> Optional[Any]:
        """Try to extract answer using math-verify library"""
        try:
            parsed_result = math_verify.parse(solution, parsing_timeout=self.math_verify_timeout)
            if parsed_result:
                return self._normalize_math_verify_result(parsed_result)
        except Exception as e:
            logger.debug(f'Math-verify failed: {str(e)}')
        return None

    def _normalize_math_verify_result(self, result) -> Any:
        """Normalize math-verify result to appropriate format"""
        if isinstance(result, (int, float)):
            return int(result) if result == int(result) else result
        elif isinstance(result, str):
            try:
                if result.isdigit():
                    return int(result)
                elif result.replace('.', '', 1).isdigit():
                    float_val = float(result)
                    return int(float_val) if float_val == int(float_val) else float_val
            except ValueError:
                pass
            return result
        elif isinstance(result, (list, tuple)):
            return result
        else:
            return str(result)

    def _extract_imo_specific(self, solution: str, problem_id: int) -> Optional[Any]:
        """Extract answers for specific IMO 2025 problems"""
        solution_lower = solution.lower()
        if problem_id == 1:
            set_patterns = ['\\\\boxed\\{([^}]+)\\}', '\\{([^}]+)\\}', 'k\\s*\\\\in\\s*\\{([^}]+)\\}', 'k\\s*can\\s*be\\s*([0-9,\\s]+)']
            for pattern in set_patterns:
                matches = re.finditer(pattern, solution, re.IGNORECASE)
                for match in matches:
                    content = match.group(1).strip()
                    logger.debug(f'Found set content: {content}')
                    if '...' in content or '\\ldots' in content:
                        return self._parse_set_with_ellipsis(content)
                    elif ',' in content:
                        return self._parse_explicit_set(content)
                    elif content.isdigit():
                        return {int(content)}
            if any((phrase in solution_lower for phrase in ['all non-negative', 'all integers', 'any integer'])):
                return 'all_integers'
        elif problem_id == 3:
            constant_patterns = ['\\\\boxed\\{(\\d+)\\}', 'c\\s*=\\s*(\\d+)', 'constant\\s+is\\s+(\\d+)', 'answer\\s+is\\s+(\\d+)', 'minimum\\s+constant\\s+is\\s+(\\d+)']
            for pattern in constant_patterns:
                matches = list(re.finditer(pattern, solution, re.IGNORECASE))
                if matches:
                    return int(matches[-1].group(1))
        elif problem_id == 6:
            if '4048' in solution:
                return 4048
            number_patterns = ['\\\\boxed\\{(\\d+)\\}', 'answer\\s+is\\s+(\\d+)', 'minimum\\s+number\\s+is\\s+(\\d+)', 'tiles?\\s+is\\s+(\\d+)']
            for pattern in number_patterns:
                matches = list(re.finditer(pattern, solution, re.IGNORECASE))
                if matches:
                    number = int(matches[-1].group(1))
                    if number > 100:
                        return number
        return None

    def _parse_set_with_ellipsis(self, content: str) -> set:
        """Parse set notation with ellipsis like '0, 1, 2, ..., n'"""
        content = content.replace('\\ldots', '...').replace('\\dots', '...')
        numbers_before = re.findall('(\\d+)', content.split('...')[0])
        if len(numbers_before) >= 2:
            start = int(numbers_before[0])
            next_val = int(numbers_before[1])
            step = next_val - start
            if step == 1 and start == 0:
                return {0, 1, 2, 3}
        numbers = [int(x) for x in re.findall('\\d+', content)]
        return set(numbers)

    def _parse_explicit_set(self, content: str) -> set:
        """Parse explicit set like '0, 1, 3'"""
        numbers = re.findall('\\d+', content)
        return {int(x) for x in numbers}

    def _extract_aime_answer(self, solution: str) -> Optional[int]:
        """Extract AIME-style numeric answers (integers 0-999)"""
        patterns = ['\\$n=\\\\boxed{(\\d+)}\\$', '\\\\\\[\\\\boxed{(\\d+)}\\\\\\]', '\\\\\\[\\\\boxed{(\\d+)}\\.\\\\\\]', '\\\\boxed{(\\d+)}', '\\$\\\\boxed{(\\d+)}\\$', 'boxed{(\\d+)}', '\\\\boxed\\s*{\\s*(\\d+)\\s*}', '\\bboxed\\s*{\\s*(\\d+)\\s*}', 'final answer is[^\\d]*(\\d+)', 'answer is[^\\d]*(\\d+)', 'answer:[^\\d]*(\\d+)', '= ?(\\d+)$']
        for pattern in patterns:
            matches = re.finditer(pattern, solution, re.IGNORECASE)
            last_match = None
            for match in matches:
                last_match = match
            if last_match:
                try:
                    number = int(last_match.group(1))
                    if 0 <= number <= 999:
                        return number
                except (ValueError, IndexError):
                    continue
        numbers = re.findall('(\\d+)', solution)
        if numbers:
            try:
                last_number = int(numbers[-1])
                if 0 <= last_number <= 999:
                    return last_number
            except ValueError:
                pass
        return None

    def _extract_general_answer(self, solution: str) -> Optional[Any]:
        """General fallback answer extraction patterns"""
        patterns = [('\\\\boxed\\{([^}]+)\\}', self._parse_boxed_content), ('boxed\\{([^}]+)\\}', self._parse_boxed_content), ('(?:the\\s+)?answer\\s+is\\s+([^\\n.!?]+)', str.strip), ('(?:final\\s+)?answer:\\s*([^\\n.!?]+)', str.strip), ('therefore,?\\s+([^\\n.!?]+)', str.strip), ('thus,?\\s+([^\\n.!?]+)', str.strip), ('=\\s*([^\\n.!?]+)$', str.strip)]
        for pattern, processor in patterns:
            matches = list(re.finditer(pattern, solution, re.IGNORECASE))
            if matches:
                content = matches[-1].group(1).strip()
                if content:
                    processed = processor(content) if processor else content
                    logger.debug(f'General pattern matched: {content} -> {processed}')
                    return processed
        return None

    def _parse_boxed_content(self, content: str) -> Any:
        """Parse content from boxed answers"""
        content = content.strip()
        if content.isdigit():
            return int(content)
        try:
            float_val = float(content)
            return int(float_val) if float_val == int(float_val) else float_val
        except ValueError:
            pass
        if content.startswith('{') and content.endswith('}'):
            try:
                set_content = content[1:-1]
                if ',' in set_content:
                    numbers = [int(x.strip()) for x in set_content.split(',') if x.strip().isdigit()]
                    return set(numbers)
            except ValueError:
                pass
        return content

def _try_math_verify(self, solution: str) -> Optional[Any]:
    """Try to extract answer using math-verify library"""
    try:
        parsed_result = math_verify.parse(solution, parsing_timeout=self.math_verify_timeout)
        if parsed_result:
            return self._normalize_math_verify_result(parsed_result)
    except Exception as e:
        logger.debug(f'Math-verify failed: {str(e)}')
    return None

def extract_answer(solution: str, problem_type: str='general', problem_id: Optional[int]=None) -> Optional[Any]:
    """
    Extract answer from solution text.

    Args:
        solution: The solution text to extract answer from
        problem_type: Type of problem (general, imo, aime, etc.)
        problem_id: Specific problem ID for customized extraction

    Returns:
        Extracted answer in appropriate format
    """
    return answer_extractor.extract_answer(solution, problem_type, problem_id)

def extract_answer_mathverify(response_str, last_n_chars=100):
    response_str = str(response_str)
    try:
        float(response_str)
        return [float(response_str)]
    except:
        response_str = response_str.split('</think>', 1)[1] if '</think>' in response_str else response_str
        if last_n_chars is not None:
            response_str = response_str[-last_n_chars:]
        parsed_result = math_verify.parse(response_str, parsing_timeout=None)
        return parsed_result

def stop_test_server(proc: subprocess.Popen):
    """Stop the test server"""
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

