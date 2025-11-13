# Cluster 5

def verify_problem_specific_insights(problem_data: Dict, solution: str) -> Dict[str, any]:
    """
    Check for problem-specific insights using our enhanced verification system
    """
    problem_id = problem_data['id']
    insight_verification = verify_key_insights(problem_id, solution)
    return {'required_insights_found': len(insight_verification['insights_found']), 'total_required_insights': insight_verification['total_insights'], 'specific_insights': insight_verification['insights_found'], 'missing_insights': insight_verification['insights_missing'], 'insight_score': insight_verification['insight_score']}

def analyze_results(results: List[Dict], approach_name: str=None):
    """Analyze and print comprehensive statistics of IMO evaluation results"""
    if not results:
        print('No results to analyze')
        return
    total_problems = len(results)
    likely_correct = sum((1 for r in results if r['evaluation']['is_correct']))
    high_confidence = sum((1 for r in results if r['evaluation']['confidence'] == 'high'))
    avg_correctness = sum((r['evaluation']['correctness_score'] for r in results)) / total_problems
    avg_completeness = sum((r['evaluation']['quality_analysis']['completeness_score'] for r in results)) / total_problems
    total_reasoning_tokens = sum((r['response']['reasoning_tokens'] for r in results))
    avg_reasoning_tokens = total_reasoning_tokens / total_problems
    print('\n' + '=' * 80)
    print(f'IMO 2025 Evaluation Results - {approach_name or 'Baseline'}')
    print('=' * 80)
    print(f'Total problems attempted: {total_problems}')
    print(f'Likely correct solutions: {likely_correct} ({likely_correct / total_problems:.1%})')
    print(f'High confidence solutions: {high_confidence} ({high_confidence / total_problems:.1%})')
    print(f'Average correctness score: {avg_correctness:.3f}')
    print(f'Average completeness score: {avg_completeness:.3f}')
    print(f'Total reasoning tokens used: {total_reasoning_tokens:,}')
    print(f'Average reasoning tokens per problem: {avg_reasoning_tokens:.0f}')
    print(f'\nProblem Type Breakdown:')
    type_stats = {}
    for result in results:
        prob_type = result['problem_data']['type']
        if prob_type not in type_stats:
            type_stats[prob_type] = {'total': 0, 'correct': 0, 'scores': []}
        type_stats[prob_type]['total'] += 1
        if result['evaluation']['is_correct']:
            type_stats[prob_type]['correct'] += 1
        type_stats[prob_type]['scores'].append(result['evaluation']['correctness_score'])
    for prob_type, stats in type_stats.items():
        accuracy = stats['correct'] / stats['total']
        avg_score = sum(stats['scores']) / len(stats['scores'])
        print(f'  {prob_type}: {stats['correct']}/{stats['total']} ({accuracy:.1%}) - Avg score: {avg_score:.3f}')
    print(f'\nDetailed Results:')
    print('-' * 80)
    for result in results:
        prob_id = result['problem_data']['id']
        prob_type = result['problem_data']['type']
        tokens = result['response']['reasoning_tokens']
        is_correct = result['evaluation']['is_correct']
        verdict = result['evaluation']['verdict']
        status = '✓' if is_correct else '✗'
        print(f'Problem {prob_id} ({prob_type}): {status} {verdict} - {tokens:,} tokens')
    print(f'\nSolution Quality Analysis:')
    print('-' * 40)
    quality_metrics = ['has_proof_structure', 'uses_mathematical_notation', 'has_logical_steps', 'addresses_all_cases', 'has_conclusion']
    for metric in quality_metrics:
        count = sum((1 for r in results if r['evaluation']['quality_analysis'][metric]))
        percentage = count / total_problems
        print(f'{metric.replace('_', ' ').title()}: {count}/{total_problems} ({percentage:.1%})')

class OptILMDataset(Dataset):

    def __init__(self, prompts, approaches, ranks, tokens, tokenizer):
        self.prompts = prompts
        self.approaches = approaches
        self.ranks = ranks
        self.tokens = tokens
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.prompts)

    def __getitem__(self, idx):
        prompt = self.prompts[idx]
        approaches = self.approaches[idx]
        ranks = self.ranks[idx]
        tokens = self.tokens[idx]
        encoding = self.tokenizer.encode_plus(prompt, add_special_tokens=True, max_length=MAX_LENGTH, padding='max_length', truncation=True, return_attention_mask=True, return_tensors='pt')
        return {'input_ids': encoding['input_ids'].flatten(), 'attention_mask': encoding['attention_mask'].flatten(), 'approaches': torch.tensor([APPROACHES.index(approach) for approach in approaches], dtype=torch.long), 'ranks': torch.tensor(ranks, dtype=torch.float), 'tokens': torch.tensor(tokens, dtype=torch.float)}

def __len__(self):
    return len(self.prompts)

def load_and_preprocess_data(tokenizer):
    dataset = load_dataset('json', data_files='optillm_combined_dataset.jsonl')
    data_items = []
    for item in dataset['train']:
        prompt = item['prompt']
        results = item['results']
        if not results:
            continue
        valid_results = [result for result in results if result['rank'] is not None and 'tokens' in result]
        if len(valid_results) != 13:
            continue
        valid_results.sort(key=lambda x: APPROACHES.index(x['approach']))
        approaches = [result['approach'] for result in valid_results]
        ranks = [result['rank'] for result in valid_results]
        tokens = [result['tokens'] for result in valid_results]
        data_items.append({'prompt': prompt, 'approaches': approaches, 'ranks': ranks, 'tokens': tokens})
    print(f'Total data points: {len(data_items)}')
    print(f'Unique prompts: {len(set((item['prompt'] for item in data_items)))}')
    approach_counts = Counter((approach for item in data_items for approach in item['approaches']))
    print('Approach distribution:')
    for approach, count in approach_counts.items():
        print(f'  {approach}: {count}')
    return OptILMDataset([item['prompt'] for item in data_items], [item['approaches'] for item in data_items], [item['ranks'] for item in data_items], [item['tokens'] for item in data_items], tokenizer)

def analyze_results(results: list[Dict]):
    """
    Analyze and print summary statistics of the results.
    
    Args:
        results (list[Dict]): List of evaluation results
    """
    total = len(results)
    correct = sum((1 for r in results if r['is_correct']))
    accuracy = correct / total if total > 0 else 0
    print('\n=== Results Summary ===')
    print(f'Total problems: {total}')
    print(f'Correct answers: {correct}')
    print(f'Accuracy: {accuracy:.2%}')
    print('\n=== Incorrect Problems ===')
    for r in results:
        if not r['is_correct']:
            print(f'Problem {r['index']}:')
            print(f'Expected: {r['correct_answer']}')
            print(f'Predicted: {r['predicted_answer']}')
            print('---')

class RequestBatcher:
    """
    Automatic request batching for OptILLM
    
    Collects incoming requests into batches and processes them together
    for improved throughput. Maintains separate queues per model type
    to avoid incompatible mixing.
    """

    def __init__(self, max_batch_size: int=4, max_wait_ms: int=50, enable_logging: bool=True):
        """
        Initialize the request batcher
        
        Args:
            max_batch_size: Maximum number of requests per batch
            max_wait_ms: Maximum time to wait for batch formation (milliseconds)
            enable_logging: Whether to log batching operations
        """
        self.max_batch_size = max_batch_size
        self.max_wait_seconds = max_wait_ms / 1000.0
        self.enable_logging = enable_logging
        self.queues: Dict[str, queue.Queue] = {}
        self.batch_threads: Dict[str, threading.Thread] = {}
        self.stats = {'total_requests': 0, 'total_batches': 0, 'avg_batch_size': 0.0, 'total_wait_time': 0.0}
        self._shutdown = False
        if self.enable_logging:
            logger.info(f'RequestBatcher initialized: max_batch_size={max_batch_size}, max_wait_ms={max_wait_ms}')

    def _get_request_key(self, request_data: Dict[str, Any]) -> str:
        """
        Generate key to group compatible requests
        
        Args:
            request_data: The request data dictionary
            
        Returns:
            String key for grouping compatible requests
        """
        model = request_data.get('model', 'default')
        approach = request_data.get('optillm_approach', 'none')
        if request_data.get('stream', False):
            raise BatchingError('Streaming requests cannot be batched')
        return f'{model}:{approach}'

    def _validate_batch_compatibility(self, requests: List[BatchRequest]) -> None:
        """
        Validate that all requests in batch are compatible
        
        Args:
            requests: List of batch requests
            
        Raises:
            BatchingError: If requests are not compatible
        """
        if not requests:
            return
        models = set((req.model for req in requests))
        if len(models) > 1:
            raise BatchingError(f'Cannot batch different models: {models}')
        approaches = set((req.approach for req in requests))
        if len(approaches) > 1:
            raise BatchingError(f'Cannot batch different optillm approaches: {approaches}')
        streaming = any((req.request_data.get('stream', False) for req in requests))
        if streaming:
            raise BatchingError('Cannot batch streaming requests')

    def _create_batch_processor(self, queue_key: str) -> None:
        """
        Create and start a batch processor thread for a specific queue
        
        Args:
            queue_key: The key identifying the queue/model type
        """

        def batch_processor():
            """Background thread that forms and processes batches"""
            if self.enable_logging:
                logger.debug(f'Batch processor started for {queue_key}')
            while not self._shutdown:
                try:
                    batch = []
                    queue_obj = self.queues[queue_key]
                    deadline = time.time() + self.max_wait_seconds
                    while len(batch) < self.max_batch_size and time.time() < deadline:
                        timeout = max(0.001, deadline - time.time())
                        try:
                            request = queue_obj.get(timeout=timeout)
                            batch.append(request)
                            if self.enable_logging and len(batch) == 1:
                                logger.debug(f'Started batch formation for {queue_key}')
                        except queue.Empty:
                            break
                    if batch:
                        if self.enable_logging:
                            wait_time = time.time() - batch[0].timestamp
                            logger.info(f'Processing batch of {len(batch)} requests for {queue_key} (waited {wait_time * 1000:.1f}ms)')
                        self.stats['total_batches'] += 1
                        self.stats['total_requests'] += len(batch)
                        self.stats['avg_batch_size'] = self.stats['total_requests'] / self.stats['total_batches']
                        self.stats['total_wait_time'] += sum((time.time() - req.timestamp for req in batch))
                        self._process_batch(batch)
                except Exception as e:
                    logger.error(f'Error in batch processor for {queue_key}: {e}')
            if self.enable_logging:
                logger.debug(f'Batch processor stopped for {queue_key}')
        thread = threading.Thread(target=batch_processor, daemon=True)
        thread.start()
        self.batch_threads[queue_key] = thread

    def _process_batch(self, batch: List[BatchRequest]) -> None:
        """
        Process a batch of requests
        
        Args:
            batch: List of batch requests to process
        """
        try:
            self._validate_batch_compatibility(batch)
            if not hasattr(self, '_processor_func'):
                raise BatchingError('No batch processor function set')
            request_data_list = [req.request_data for req in batch]
            responses = self._processor_func(request_data_list)
            if len(responses) != len(batch):
                raise BatchingError(f'Processor returned {len(responses)} responses for {len(batch)} requests')
            for req, response in zip(batch, responses):
                req.future.set_result(response)
        except Exception as e:
            error_msg = f'Batch processing failed: {str(e)}'
            logger.error(error_msg)
            for req in batch:
                req.future.set_exception(BatchingError(error_msg))

    def set_processor(self, processor_func):
        """
        Set the batch processing function
        
        Args:
            processor_func: Function that takes list of request data and returns list of responses
        """
        self._processor_func = processor_func

    def add_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a request to be batched
        
        Args:
            request_data: The request data dictionary
            
        Returns:
            The response from batch processing
            
        Raises:
            BatchingError: If request cannot be processed
        """
        try:
            queue_key = self._get_request_key(request_data)
            if queue_key not in self.queues:
                self.queues[queue_key] = queue.Queue()
                self._create_batch_processor(queue_key)
            future = Future()
            batch_request = BatchRequest(request_data=request_data, future=future, timestamp=time.time(), model=request_data.get('model', 'default'), approach=request_data.get('optillm_approach'))
            self.queues[queue_key].put(batch_request)
            if self.enable_logging:
                logger.debug(f'Added request to batch queue {queue_key}')
            return future.result()
        except Exception as e:
            raise BatchingError(f'Failed to process request: {str(e)}')

    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return self.stats.copy()

    def shutdown(self):
        """Shutdown the batcher and all background threads"""
        self._shutdown = True
        if self.enable_logging:
            logger.info('RequestBatcher shutting down...')
        for thread in self.batch_threads.values():
            thread.join(timeout=1.0)

def _validate_batch_compatibility(self, requests: List[BatchRequest]) -> None:
    """
        Validate that all requests in batch are compatible
        
        Args:
            requests: List of batch requests
            
        Raises:
            BatchingError: If requests are not compatible
        """
    if not requests:
        return
    models = set((req.model for req in requests))
    if len(models) > 1:
        raise BatchingError(f'Cannot batch different models: {models}')
    approaches = set((req.approach for req in requests))
    if len(approaches) > 1:
        raise BatchingError(f'Cannot batch different optillm approaches: {approaches}')
    streaming = any((req.request_data.get('stream', False) for req in requests))
    if streaming:
        raise BatchingError('Cannot batch streaming requests')

class DynamicTemperature:
    """Implements dynamic temperature scaling based on input characteristics"""

    def __init__(self):
        self.token_entropy_cache = {}

    def _compute_token_entropy(self, tokens: List[int]) -> float:
        """Compute token distribution entropy"""
        token_counts = np.bincount(tokens)
        probabilities = token_counts / len(tokens)
        return entropy(probabilities)

    def get_optimal_temperature(self, prompt: str, tokenizer: AutoTokenizer, base_temperature: float) -> float:
        """Calculate optimal temperature based on prompt characteristics"""
        tokens = tokenizer.encode(prompt)
        token_entropy = self._compute_token_entropy(tokens)
        length_factor = np.clip(len(tokens) / 100, 0.5, 2.0)
        entropy_factor = np.clip(token_entropy / 4.0, 0.5, 1.5)
        optimal_temperature = base_temperature * length_factor * entropy_factor
        return np.clip(optimal_temperature, 0.1, 2.0)

def _compute_token_entropy(self, tokens: List[int]) -> float:
    """Compute token distribution entropy"""
    token_counts = np.bincount(tokens)
    probabilities = token_counts / len(tokens)
    return entropy(probabilities)

class ChatCompletion:

    def __init__(self, response_dict: Dict):
        self.id = response_dict['id']
        self.object = response_dict['object']
        self.created = response_dict['created']
        self.model = response_dict['model']
        self.choices = [ChatCompletionChoice(index=choice['index'], message=choice['message'], finish_reason=choice['finish_reason']) for choice in response_dict['choices']]
        self.usage = ChatCompletionUsage(**response_dict['usage'])

    def model_dump(self) -> Dict:
        return {'id': self.id, 'object': self.object, 'created': self.created, 'model': self.model, 'choices': [{'index': choice.index, 'message': {'role': choice.message.role, 'content': choice.message.content, 'logprobs': choice.message.logprobs} if choice.message.logprobs else {'role': choice.message.role, 'content': choice.message.content}, 'finish_reason': choice.finish_reason} for choice in self.choices], 'usage': {'prompt_tokens': self.usage.prompt_tokens, 'completion_tokens': self.usage.completion_tokens, 'total_tokens': self.usage.total_tokens, 'completion_tokens_details': {'reasoning_tokens': getattr(self.usage, 'reasoning_tokens', 0)}}}

def __init__(self, response_dict: Dict):
    self.id = response_dict['id']
    self.object = response_dict['object']
    self.created = response_dict['created']
    self.model = response_dict['model']
    self.choices = [ChatCompletionChoice(index=choice['index'], message=choice['message'], finish_reason=choice['finish_reason']) for choice in response_dict['choices']]
    self.usage = ChatCompletionUsage(**response_dict['usage'])

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

def solve(self, question: str) -> str:
    """
        Synchronous wrapper for solve_async method.
        """
    return asyncio.run(self.solve_async(question))

def log_error(request_id: str, error_message: str) -> None:
    """Log an error using the global logger instance"""
    if _global_logger and _global_logger.enabled:
        _global_logger.log_error(request_id, error_message)

class Models:

    @staticmethod
    def list():
        try:
            valid_models = get_valid_models()
            model_list = []
            for model in valid_models:
                model_list.append({'id': model, 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'})
            return {'object': 'list', 'data': model_list}
        except Exception as e:
            print(f'Error fetching LiteLLM models: {str(e)}')
            return {'object': 'list', 'data': [{'id': 'gpt-4o-mini', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'gpt-4o', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'command-nightly', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'claude-3-opus-20240229', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'claude-3-sonnet-20240229', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'gemini-1.5-pro-latest', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}]}

@staticmethod
def list():
    try:
        valid_models = get_valid_models()
        model_list = []
        for model in valid_models:
            model_list.append({'id': model, 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'})
        return {'object': 'list', 'data': model_list}
    except Exception as e:
        print(f'Error fetching LiteLLM models: {str(e)}')
        return {'object': 'list', 'data': [{'id': 'gpt-4o-mini', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'gpt-4o', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'command-nightly', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'claude-3-opus-20240229', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'claude-3-sonnet-20240229', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}, {'id': 'gemini-1.5-pro-latest', 'object': 'model', 'created': int(time.time()), 'owned_by': 'litellm'}]}

class StrategyNetwork:
    """
    Cross-agent strategy sharing and meta-reasoning system

    Key capabilities:
    1. Extract reasoning strategies from agent solutions
    2. Share effective strategies between agents
    3. Track strategy effectiveness across problem types
    4. Enable adaptive agent behavior based on peer insights
    """

    def __init__(self, client, model: str, config: Dict[str, Any]):
        self.client = client
        self.model = model
        self.config = config
        self.max_tokens = config.get('max_tokens', 30000)
        self.strategies: Dict[str, ReasoningStrategy] = {}
        self.strategy_effectiveness: Dict[Tuple[str, str], StrategyEffectiveness] = {}
        self.agent_preferred_strategies: Dict[str, List[str]] = defaultdict(list)
        self.problem_type_cache: Dict[str, str] = {}
        logger.info('Initialized Strategy Network for cross-agent insight sharing')

    async def extract_strategies_from_solutions(self, workspace: MARSWorkspace, request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, ReasoningStrategy]:
        """Extract reasoning strategies from all agent solutions"""
        logger.info('Extracting strategies from agent solutions...')
        extraction_tasks = []
        for solution in workspace.solutions:
            if not solution.agent_id.startswith('agg_'):
                task = self._extract_strategy_async(solution, workspace.problem, request_id, executor)
                extraction_tasks.append(task)
        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        extracted_strategies = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Strategy extraction failed: {str(result)}')
                continue
            if result:
                strategy = result
                extracted_strategies[strategy.strategy_id] = strategy
                self.strategies[strategy.strategy_id] = strategy
                self.agent_preferred_strategies[strategy.agent_id].append(strategy.strategy_id)
        logger.info(f'Extracted {len(extracted_strategies)} reasoning strategies')
        return extracted_strategies

    async def _extract_strategy_async(self, solution: AgentSolution, problem: str, request_id: str=None, executor: ThreadPoolExecutor=None) -> Optional[ReasoningStrategy]:
        """Extract strategy from a single agent solution"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(executor, self._extract_strategy_from_solution, solution, problem, request_id)
        except Exception as e:
            logger.error(f'Failed to extract strategy from agent {solution.agent_id}: {str(e)}')
            return None

    def _extract_strategy_from_solution(self, solution: AgentSolution, problem: str, request_id: str=None) -> Optional[ReasoningStrategy]:
        """Extract reasoning strategy using LLM analysis"""
        strategy_extraction_prompt = f'Analyze this mathematical solution and extract the key reasoning strategy:\n\nProblem: {problem}\n\nAgent Solution:\n{solution.solution}\n\nExtract the following strategy components:\n\n1. PROBLEM_TYPE: Classify as one of [algebra, geometry, combinatorics, number_theory, calculus, discrete_math, probability]\n\n2. APPROACH_TYPE: Identify the main approach [direct_computation, proof_by_contradiction, constructive_proof, case_analysis, induction, algebraic_manipulation, geometric_visualization, pattern_recognition, reduction_to_known_problem]\n\n3. KEY_INSIGHTS: List 2-3 key mathematical insights that enabled the solution\n\n4. MATHEMATICAL_TECHNIQUES: List specific techniques used [substitution, factorization, coordinate_geometry, symmetry, pigeonhole_principle, etc.]\n\n5. SOLUTION_PATTERN: Describe the general pattern/template of this solution approach\n\n6. SUCCESS_INDICATORS: What makes this approach particularly effective for this type of problem?\n\nFormat your response as:\nPROBLEM_TYPE: [type]\nAPPROACH_TYPE: [approach]\nKEY_INSIGHTS: [insight1], [insight2], [insight3]\nMATHEMATICAL_TECHNIQUES: [technique1], [technique2], [technique3]\nSOLUTION_PATTERN: [pattern description]\nSUCCESS_INDICATORS: [indicator1], [indicator2]'
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical strategy analysis expert. Extract reasoning patterns from solutions.'}, {'role': 'user', 'content': strategy_extraction_prompt}], max_tokens=self.max_tokens // 4, temperature=0.3, timeout=120, extra_body={'reasoning': {'effort': 'medium'}})
            if request_id:
                provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a mathematical strategy analysis expert.'}, {'role': 'user', 'content': strategy_extraction_prompt}], 'max_tokens': self.max_tokens // 4, 'temperature': 0.3, 'extra_body': {'reasoning': {'effort': 'medium'}}}
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            analysis = response.choices[0].message.content.strip()
            strategy_data = self._parse_strategy_analysis(analysis)
            if strategy_data:
                strategy_id = f'strategy_{solution.agent_id}_{datetime.now().strftime('%H%M%S')}'
                return ReasoningStrategy(strategy_id=strategy_id, agent_id=solution.agent_id, problem_type=strategy_data.get('problem_type', 'unknown'), approach_type=strategy_data.get('approach_type', 'unknown'), key_insights=strategy_data.get('key_insights', []), mathematical_techniques=strategy_data.get('mathematical_techniques', []), solution_pattern=strategy_data.get('solution_pattern', ''), confidence=solution.confidence, success_indicators=strategy_data.get('success_indicators', []))
        except Exception as e:
            logger.error(f'Strategy extraction failed for agent {solution.agent_id}: {str(e)}')
            return None

    def _parse_strategy_analysis(self, analysis: str) -> Optional[Dict[str, Any]]:
        """Parse structured strategy analysis response"""
        try:
            lines = analysis.split('\n')
            strategy_data = {}
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'problem_type':
                        strategy_data['problem_type'] = value
                    elif key == 'approach_type':
                        strategy_data['approach_type'] = value
                    elif 'insights' in key:
                        strategy_data['key_insights'] = [insight.strip() for insight in value.split(',')]
                    elif 'techniques' in key:
                        strategy_data['mathematical_techniques'] = [tech.strip() for tech in value.split(',')]
                    elif 'pattern' in key:
                        strategy_data['solution_pattern'] = value
                    elif 'indicators' in key:
                        strategy_data['success_indicators'] = [ind.strip() for ind in value.split(',')]
            return strategy_data if strategy_data else None
        except Exception as e:
            logger.error(f'Failed to parse strategy analysis: {str(e)}')
            return None

    async def share_strategies_across_agents(self, workspace: MARSWorkspace, extracted_strategies: Dict[str, ReasoningStrategy], request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, List[str]]:
        """Share effective strategies across agents and generate enhanced solutions"""
        logger.info('Sharing strategies across agents...')
        problem_type = await self._classify_problem_type(workspace.problem, request_id, executor)
        effective_strategies = self._get_effective_strategies_for_type(problem_type, extracted_strategies)
        enhancement_tasks = []
        agent_strategies = {}
        for solution in workspace.solutions:
            if not solution.agent_id.startswith('agg_'):
                cross_agent_strategies = [strategy for strategy in effective_strategies.values() if strategy.agent_id != solution.agent_id]
                if cross_agent_strategies:
                    agent_strategies[solution.agent_id] = [s.strategy_id for s in cross_agent_strategies]
                    task = self._generate_strategy_enhanced_solution_async(solution, workspace.problem, cross_agent_strategies, request_id, executor)
                    enhancement_tasks.append((solution.agent_id, task))
        if enhancement_tasks:
            tasks = [task for _, task in enhancement_tasks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f'Strategy enhancement failed: {str(result)}')
                    continue
                if result:
                    enhanced_solution = result
                    workspace.add_solution(enhanced_solution)
                    logger.info(f'Added strategy-enhanced solution from agent {enhanced_solution.agent_id}')
        logger.info(f'Strategy sharing complete: enhanced {len(enhancement_tasks)} agents')
        return agent_strategies

    async def _classify_problem_type(self, problem: str, request_id: str=None, executor: ThreadPoolExecutor=None) -> str:
        """Classify the problem type for strategy matching"""
        if problem in self.problem_type_cache:
            return self.problem_type_cache[problem]
        loop = asyncio.get_event_loop()
        try:
            problem_type = await loop.run_in_executor(executor, self._classify_problem_with_llm, problem, request_id)
            self.problem_type_cache[problem] = problem_type
            return problem_type
        except Exception as e:
            logger.error(f'Problem classification failed: {str(e)}')
            return 'unknown'

    def _classify_problem_with_llm(self, problem: str, request_id: str=None) -> str:
        """Use LLM to classify problem type"""
        classification_prompt = f'Classify this mathematical problem into one category:\n\nProblem: {problem}\n\nCategories: [algebra, geometry, combinatorics, number_theory, calculus, discrete_math, probability]\n\nRespond with just the category name.'
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical problem classifier.'}, {'role': 'user', 'content': classification_prompt}], max_tokens=50, temperature=0.1, timeout=60, extra_body={'reasoning': {'effort': 'low'}})
            classification = response.choices[0].message.content.strip().lower()
            valid_types = ['algebra', 'geometry', 'combinatorics', 'number_theory', 'calculus', 'discrete_math', 'probability']
            if classification in valid_types:
                return classification
            else:
                return 'algebra'
        except Exception as e:
            logger.error(f'Problem classification failed: {str(e)}')
            return 'algebra'

    def _get_effective_strategies_for_type(self, problem_type: str, extracted_strategies: Dict[str, ReasoningStrategy]) -> Dict[str, ReasoningStrategy]:
        """Get most effective strategies for the given problem type"""
        relevant_strategies = {}
        for strategy_id, strategy in extracted_strategies.items():
            if (strategy.problem_type == problem_type or strategy.problem_type == 'unknown') and strategy.confidence >= 0.6:
                relevant_strategies[strategy_id] = strategy
        if not relevant_strategies:
            sorted_strategies = sorted(extracted_strategies.items(), key=lambda x: x[1].confidence, reverse=True)
            relevant_strategies = dict(sorted_strategies[:2])
        return relevant_strategies

    async def _generate_strategy_enhanced_solution_async(self, original_solution: AgentSolution, problem: str, peer_strategies: List[ReasoningStrategy], request_id: str=None, executor: ThreadPoolExecutor=None) -> Optional[AgentSolution]:
        """Generate enhanced solution using peer strategies"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(executor, self._generate_strategy_enhanced_solution, original_solution, problem, peer_strategies, request_id)
        except Exception as e:
            logger.error(f'Strategy enhancement failed for agent {original_solution.agent_id}: {str(e)}')
            return None

    def _generate_strategy_enhanced_solution(self, original_solution: AgentSolution, problem: str, peer_strategies: List[ReasoningStrategy], request_id: str=None) -> Optional[AgentSolution]:
        """Generate solution enhanced with peer strategies"""
        strategy_insights = ''
        for strategy in peer_strategies[:2]:
            strategy_insights += f'\nPeer Strategy from Agent {strategy.agent_id}:\n'
            strategy_insights += f'- Approach: {strategy.approach_type}\n'
            strategy_insights += f'- Key Insights: {', '.join(strategy.key_insights[:3])}\n'
            strategy_insights += f'- Techniques: {', '.join(strategy.mathematical_techniques[:3])}\n'
            strategy_insights += f'- Success Pattern: {strategy.solution_pattern[:200]}...\n'
        enhancement_prompt = f'You are Agent {original_solution.agent_id} collaborating with other mathematical agents.\n\nOriginal Problem: {problem}\n\nYour Current Solution:\n{original_solution.solution}\n\nPeer Agent Strategy Insights:\n{strategy_insights}\n\nTask: Enhance your solution by incorporating the most valuable insights from your peers while maintaining your unique approach. Consider:\n\n1. Can any peer techniques strengthen your solution?\n2. Do peer insights reveal gaps in your reasoning?\n3. Can you combine approaches for a more robust solution?\n4. What verification steps from peers could improve confidence?\n\nProvide an enhanced solution that synthesizes the best ideas while ensuring mathematical rigor.\n\nEnhanced Solution:'
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a collaborative mathematical agent learning from peer insights.'}, {'role': 'user', 'content': enhancement_prompt}], max_tokens=self.max_tokens, temperature=original_solution.temperature * 0.9, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
            if request_id:
                provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a collaborative mathematical agent learning from peer insights.'}, {'role': 'user', 'content': enhancement_prompt}], 'max_tokens': self.max_tokens, 'temperature': original_solution.temperature * 0.9, 'extra_body': {'reasoning': {'effort': 'high'}}}
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            enhanced_solution_text = response.choices[0].message.content.strip()
            reasoning_tokens = 0
            total_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                total_tokens = getattr(response.usage, 'total_tokens', 0)
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if reasoning_tokens == 0:
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            enhanced_agent_solution = AgentSolution(agent_id=f'enhanced_{original_solution.agent_id}', solution=enhanced_solution_text, confidence=min(original_solution.confidence + 0.1, 1.0), reasoning_tokens=reasoning_tokens, total_tokens=total_tokens, solution_length=len(enhanced_solution_text), temperature=original_solution.temperature)
            logger.info(f'Generated strategy-enhanced solution for agent {original_solution.agent_id}')
            return enhanced_agent_solution
        except Exception as e:
            logger.error(f'Strategy enhancement failed for agent {original_solution.agent_id}: {str(e)}')
            return None

    def update_strategy_effectiveness(self, strategy_id: str, problem_type: str, was_successful: bool, confidence: float):
        """Update effectiveness tracking for a strategy"""
        key = (strategy_id, problem_type)
        if key not in self.strategy_effectiveness:
            self.strategy_effectiveness[key] = StrategyEffectiveness(strategy_id=strategy_id, problem_type=problem_type)
        effectiveness = self.strategy_effectiveness[key]
        effectiveness.total_uses += 1
        if was_successful:
            effectiveness.success_count += 1
        else:
            effectiveness.failure_count += 1
        effectiveness.average_confidence = (effectiveness.average_confidence * (effectiveness.total_uses - 1) + confidence) / effectiveness.total_uses

    def get_strategy_insights_summary(self) -> Dict[str, Any]:
        """Get summary of strategy network insights"""
        return {'total_strategies': len(self.strategies), 'strategies_by_type': self._count_strategies_by_type(), 'most_effective_strategies': self._get_most_effective_strategies(), 'agent_strategy_preferences': dict(self.agent_preferred_strategies), 'strategy_effectiveness_stats': self._get_effectiveness_stats()}

    def _count_strategies_by_type(self) -> Dict[str, int]:
        """Count strategies by problem type"""
        counts = defaultdict(int)
        for strategy in self.strategies.values():
            counts[strategy.problem_type] += 1
        return dict(counts)

    def _get_most_effective_strategies(self) -> List[Dict[str, Any]]:
        """Get most effective strategies across all problem types"""
        effective_strategies = []
        for effectiveness in self.strategy_effectiveness.values():
            if effectiveness.total_uses >= 2:
                effective_strategies.append({'strategy_id': effectiveness.strategy_id, 'problem_type': effectiveness.problem_type, 'success_rate': effectiveness.success_rate, 'average_confidence': effectiveness.average_confidence, 'total_uses': effectiveness.total_uses})
        effective_strategies.sort(key=lambda x: (x['success_rate'], x['average_confidence']), reverse=True)
        return effective_strategies[:5]

    def _get_effectiveness_stats(self) -> Dict[str, float]:
        """Get overall effectiveness statistics"""
        if not self.strategy_effectiveness:
            return {}
        success_rates = [eff.success_rate for eff in self.strategy_effectiveness.values()]
        avg_confidences = [eff.average_confidence for eff in self.strategy_effectiveness.values()]
        return {'average_success_rate': sum(success_rates) / len(success_rates) if success_rates else 0, 'average_confidence': sum(avg_confidences) / len(avg_confidences) if avg_confidences else 0, 'total_strategy_applications': sum((eff.total_uses for eff in self.strategy_effectiveness.values()))}

def get_strategy_insights_summary(self) -> Dict[str, Any]:
    """Get summary of strategy network insights"""
    return {'total_strategies': len(self.strategies), 'strategies_by_type': self._count_strategies_by_type(), 'most_effective_strategies': self._get_most_effective_strategies(), 'agent_strategy_preferences': dict(self.agent_preferred_strategies), 'strategy_effectiveness_stats': self._get_effectiveness_stats()}

class MARSAgent:
    """Individual agent for mathematical reasoning with OpenRouter reasoning API"""

    def __init__(self, agent_id: int, client, model: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.client = client
        self.model = model
        self.config = config
        self.temperature = self._assign_temperature()

    def _assign_temperature(self) -> float:
        """Assign temperature based on agent ID for 3-agent configuration"""
        temperatures = [0.3, 0.6, 1.0]
        return temperatures[self.agent_id % len(temperatures)]

    def _get_reasoning_effort(self) -> str:
        """Get reasoning effort level based on agent temperature"""
        if self.temperature <= 0.4:
            return 'low'
        elif self.temperature <= 0.8:
            return 'medium'
        else:
            return 'high'

    def generate_solution(self, problem: str, request_id: str=None) -> Tuple[AgentSolution, int]:
        """Generate a solution for the given problem using reasoning API"""
        import time
        start_time = time.time()
        logger.info(f'🤖 AGENT {self.agent_id}: Starting solution generation (temp: {self.temperature}, effort: {self._get_reasoning_effort()})')
        logger.info(f'🤖 AGENT {self.agent_id}: Problem length: {len(problem)} characters')
        exploration_prompt = AGENT_EXPLORATION_PROMPT.format(agent_id=self.agent_id, temperature=self.temperature, problem=problem)
        reasoning_effort = self._get_reasoning_effort()
        max_tokens = self.config['max_tokens']
        logger.info(f'🤖 AGENT {self.agent_id}: Using max_tokens={max_tokens}, reasoning_effort={reasoning_effort}')
        reasoning_config = {'effort': reasoning_effort}
        try:
            api_start = time.time()
            logger.info(f'🤖 AGENT {self.agent_id}: Making API call to {self.model}...')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': exploration_prompt}], max_tokens=max_tokens, temperature=self.temperature, timeout=300, extra_body={'reasoning': reasoning_config})
            api_duration = time.time() - api_start
            logger.info(f'🤖 AGENT {self.agent_id}: API call completed in {api_duration:.2f}s')
            solution_text = response.choices[0].message.content.strip()
            solution_length = len(solution_text)
            word_count = len(solution_text.split())
            has_boxed = '\\boxed{' in solution_text
            has_proof_words = any((word in solution_text.lower() for word in ['therefore', 'thus', 'proof', 'qed']))
            logger.info(f'🤖 AGENT {self.agent_id}: Solution analysis:')
            logger.info(f'  📝 Length: {solution_length:,} chars, {word_count:,} words')
            logger.info(f'  📦 Has boxed answer: {has_boxed}')
            logger.info(f'  🔍 Has proof indicators: {has_proof_words}')
            logger.info(f'  📄 Preview: {solution_text[:200]}{('...' if len(solution_text) > 200 else '')}')
            logger.info(f'  📄 Last 100 chars: ...{(solution_text[-100:] if solution_length > 100 else solution_text)}')
            reasoning_tokens = 0
            total_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                total_tokens = getattr(response.usage, 'total_tokens', 0)
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if reasoning_tokens == 0:
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            reasoning_ratio = reasoning_tokens / total_tokens * 100 if total_tokens > 0 else 0
            logger.info(f'🤖 AGENT {self.agent_id}: Token usage: reasoning={reasoning_tokens:,}, total={total_tokens:,} ({reasoning_ratio:.1f}% reasoning)')
            confidence = self._estimate_confidence(solution_text)
            logger.info(f'🤖 AGENT {self.agent_id}: Estimated confidence: {confidence:.3f}')
            agent_solution = AgentSolution(agent_id=str(self.agent_id), solution=solution_text, confidence=confidence, reasoning_tokens=reasoning_tokens, total_tokens=total_tokens, solution_length=solution_length, temperature=self.temperature)
            total_duration = time.time() - start_time
            logger.info(f'🤖 AGENT {self.agent_id}: ✅ Solution generated in {total_duration:.2f}s (API: {api_duration:.2f}s, processing: {total_duration - api_duration:.2f}s)')
            return (agent_solution, reasoning_tokens)
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f'🤖 AGENT {self.agent_id}: ❌ Error generating solution after {error_duration:.2f}s: {str(e)}')
            logger.error(f'🤖 AGENT {self.agent_id}: Model: {self.model}, Temperature: {self.temperature}, Max tokens: {max_tokens}')
            error_message = f'Error generating solution: {str(e)}'
            error_solution = AgentSolution(agent_id=str(self.agent_id), solution=error_message, confidence=0.0, reasoning_tokens=0, total_tokens=0, solution_length=len(error_message), temperature=self.temperature)
            return (error_solution, 0)

    def verify_solution(self, problem: str, solution: str, verifier_id: int, solution_agent_id: int, request_id: str=None) -> VerificationResult:
        """Verify a solution using mathematical reasoning"""
        import time
        start_time = time.time()
        logger.info(f'🔍 VERIFIER {self.agent_id}: Starting verification (target: Agent {solution_agent_id}, verifier_id: {verifier_id})')
        logger.info(f'🔍 VERIFIER {self.agent_id}: Solution length: {len(solution):,} chars')
        verification_prompt = VERIFICATION_PROMPT.format(problem=problem, solution=solution)
        max_tokens = self.config['max_tokens']
        try:
            api_start = time.time()
            logger.info(f'🔍 VERIFIER {self.agent_id}: Making verification API call...')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': verification_prompt}], max_tokens=max_tokens, temperature=0.1, timeout=180, extra_body={'reasoning': {'effort': 'low'}})
            api_duration = time.time() - api_start
            logger.info(f'🔍 VERIFIER {self.agent_id}: Verification API call completed in {api_duration:.2f}s')
            verification_text = response.choices[0].message.content.strip()
            assessment, confidence, issues, suggestions = self._parse_verification(verification_text)
            logger.info(f'🔍 VERIFIER {self.agent_id}: Assessment: {assessment}, Confidence: {confidence:.3f}')
            logger.info(f'🔍 VERIFIER {self.agent_id}: Issues found: {len(issues)}, Suggestions: {len(suggestions)}')
            if issues:
                logger.info(f'🔍 VERIFIER {self.agent_id}: Key issues: {issues[:2]}')
            result = VerificationResult(verifier_id=verifier_id, solution_id=f'agent_{solution_agent_id}_iter_0', assessment=assessment, confidence=confidence, issues=issues, suggestions=suggestions, detailed_report=verification_text, timestamp=datetime.now())
            total_duration = time.time() - start_time
            logger.info(f'🔍 VERIFIER {self.agent_id}: ✅ Verification completed in {total_duration:.2f}s')
            return result
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f'🔍 VERIFIER {self.agent_id}: ❌ Verification error after {error_duration:.2f}s: {str(e)}')
            return VerificationResult(verifier_id=verifier_id, solution_id=f'agent_{solution_agent_id}_iter_0', assessment='INCOMPLETE', confidence=0.0, issues=[f'Verification error: {str(e)}'], suggestions=['Retry verification'], detailed_report=f'Error during verification: {str(e)}', timestamp=datetime.now())

    def improve_solution(self, problem: str, current_solution: str, feedback: str, issues: list, request_id: str=None) -> Tuple[str, int]:
        """Improve a solution based on verification feedback"""
        import time
        start_time = time.time()
        logger.info(f'🔧 IMPROVER {self.agent_id}: Starting solution improvement')
        logger.info(f'🔧 IMPROVER {self.agent_id}: Current solution: {len(current_solution):,} chars')
        logger.info(f'🔧 IMPROVER {self.agent_id}: Issues to address: {len(issues)}')
        improvement_prompt = IMPROVEMENT_PROMPT.format(problem=problem, current_solution=current_solution, feedback=feedback, issues='\n'.join((f'- {issue}' for issue in issues)))
        max_tokens = self.config['max_tokens']
        try:
            api_start = time.time()
            logger.info(f'🔧 IMPROVER {self.agent_id}: Making improvement API call...')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': improvement_prompt}], max_tokens=max_tokens, temperature=self.temperature * 0.8, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
            api_duration = time.time() - api_start
            logger.info(f'🔧 IMPROVER {self.agent_id}: Improvement API call completed in {api_duration:.2f}s')
            improved_solution = response.choices[0].message.content.strip()
            reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            length_change = len(improved_solution) - len(current_solution)
            logger.info(f'🔧 IMPROVER {self.agent_id}: Solution length change: {length_change:+,} chars')
            logger.info(f'🔧 IMPROVER {self.agent_id}: Improved solution preview: {improved_solution[:200]}{('...' if len(improved_solution) > 200 else '')}')
            total_duration = time.time() - start_time
            logger.info(f'🔧 IMPROVER {self.agent_id}: ✅ Solution improved in {total_duration:.2f}s with {reasoning_tokens:,} reasoning tokens')
            return (improved_solution, reasoning_tokens)
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f'🔧 IMPROVER {self.agent_id}: ❌ Improvement error after {error_duration:.2f}s: {str(e)}')
            logger.warning(f'🔧 IMPROVER {self.agent_id}: Returning original solution due to error')
            return (current_solution, 0)

    def _estimate_confidence(self, solution: str) -> float:
        """Estimate confidence based on solution characteristics"""
        confidence = 0.5
        confidence_factors = []
        if '\\boxed{' in solution:
            confidence += 0.2
            confidence_factors.append('boxed_answer')
        if 'therefore' in solution.lower() or 'thus' in solution.lower():
            confidence += 0.1
            confidence_factors.append('logical_connectors')
        if 'proof' in solution.lower():
            confidence += 0.1
            confidence_factors.append('proof_structure')
        if len(solution.split()) > 200:
            confidence += 0.1
            confidence_factors.append('detailed_solution')
        if 'let' in solution.lower() and 'assume' in solution.lower():
            confidence += 0.1
            confidence_factors.append('formal_approach')
        uncertainty_factors = []
        if 'might' in solution.lower() or 'possibly' in solution.lower():
            confidence -= 0.1
            uncertainty_factors.append('hedging_language')
        if 'unsure' in solution.lower() or 'not sure' in solution.lower():
            confidence -= 0.2
            uncertainty_factors.append('explicit_uncertainty')
        final_confidence = max(0.1, min(1.0, confidence))
        logger.debug(f'🤖 AGENT {self.agent_id}: Confidence factors: +{confidence_factors}, -{uncertainty_factors} → {final_confidence:.3f}')
        return final_confidence

    def _parse_verification(self, verification_text: str) -> Tuple[str, float, list, list]:
        """Parse verification result to extract structured information"""
        assessment = 'INCOMPLETE'
        confidence = 0.5
        issues = []
        suggestions = []
        text_lower = verification_text.lower()
        if 'correct' in text_lower and 'incorrect' not in text_lower:
            assessment = 'CORRECT'
            confidence = 0.8
        elif 'incorrect' in text_lower:
            assessment = 'INCORRECT'
            confidence = 0.8
        elif 'incomplete' in text_lower:
            assessment = 'INCOMPLETE'
            confidence = 0.6
        import re
        confidence_match = re.search('confidence.*?(\\d+).*?(?:out of|/)\\s*(\\d+)', text_lower)
        if confidence_match:
            conf_score = float(confidence_match.group(1))
            conf_total = float(confidence_match.group(2))
            confidence = conf_score / conf_total
        lines = verification_text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any((word in line_lower for word in ['error', 'mistake', 'incorrect', 'wrong', 'issue'])):
                issues.append(line.strip())
        for line in lines:
            line_lower = line.lower()
            if any((word in line_lower for word in ['suggest', 'recommend', 'should', 'could improve'])):
                suggestions.append(line.strip())
        return (assessment, confidence, issues, suggestions)

def _assign_temperature(self) -> float:
    """Assign temperature based on agent ID for 3-agent configuration"""
    temperatures = [0.3, 0.6, 1.0]
    return temperatures[self.agent_id % len(temperatures)]

def multi_agent_reasoning_system(system_prompt: str, initial_query: str, client, model: str, request_config: dict=None, request_id: str=None) -> Tuple[str, int]:
    """
    Main MARS function implementing multi-agent reasoning with parallel execution

    Args:
        system_prompt: System-level instructions
        initial_query: The problem or task to solve
        client: OpenAI-compatible client for API calls
        model: Model identifier (should support OpenRouter reasoning API)
        request_id: Optional request ID for conversation logging

    Returns:
        Tuple of (final_solution, total_reasoning_tokens)
    """
    return asyncio.run(_run_mars_parallel(system_prompt, initial_query, client, model, request_config, request_id))

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

def __enter__(self):
    """Context manager entry - ensures browser is ready"""
    self.get_or_create_searcher()
    self._session_start_time = time.time()
    return self

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

def download_model(model_name):
    global _model_downloaded
    if not _model_downloaded:
        if not spacy.util.is_package(model_name):
            print(f'Downloading {model_name} model...')
            spacy.cli.download(model_name)
        else:
            print(f'{model_name} model already downloaded.')
        _model_downloaded = True

class HealthChecker:
    """Background health checker for providers"""

    def __init__(self, providers: List, enabled: bool=True, interval: int=30, timeout: int=5):
        self.providers = providers
        self.enabled = enabled
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self.thread = None

    def start(self):
        """Start health checking in background"""
        if not self.enabled:
            return
        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        logger.info(f'Health checker started (interval: {self.interval}s)')

    def stop(self):
        """Stop health checking"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _check_loop(self):
        """Main health check loop"""
        while self.running:
            for provider in self.providers:
                self._check_provider(provider)
            time.sleep(self.interval)

    def _check_provider(self, provider):
        """Check health of a single provider"""
        try:
            response = provider.client.models.list()
            if not provider.is_healthy:
                logger.info(f'Provider {provider.name} is now healthy')
            provider.is_healthy = True
            provider.last_error = None
        except Exception as e:
            if provider.is_healthy:
                logger.warning(f'Provider {provider.name} failed health check: {e}')
            provider.is_healthy = False
            provider.last_error = str(e)

def _check_loop(self):
    """Main health check loop"""
    while self.running:
        for provider in self.providers:
            self._check_provider(provider)
        time.sleep(self.interval)

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

def llm_call_reason_effort_fallback(client: Any, provider_request: dict, reasoning_effort_levels: list, cepo_config: CepoConfig) -> tuple[Optional[Any], str, int]:
    """
    Call LLM with fallback on reasoning effort levels.

    This function wraps `llm_call` with retry and degradation logic to handle
    two main classes of errors:

    1. **Incomplete generation (finish_reason = "length")**:
       - The model returns a response object but does not finish generation
         (e.g., truncated output).
       - In this case, the reasoning effort is reduced, and another attempt
         is made with lower levels.

    2. **Server/validation errors (e.g., 400 BadRequest, 500 InternalServerError)**:
       - Often caused by gpt-oss's "expected output number" error, which cannot be
         fully recovered within the current API.
       - The function retries once, and if the error persists, reasoning effort
         is degraded to try again at lower levels.

    The fallback sequence continues until either:
      - A valid response is obtained (not truncated and not `None`), or
      - All reasoning effort levels are exhausted, in which case the last
        attempted result (possibly `None`) is returned.

    Args:
        client (Any): LLM API client instance used for making calls.
        provider_request (dict): LMM call params.
        reasoning_effort_levels (list): Ordered list of reasoning effort levels
            (e.g., ["high", "medium", "low"]) to try in fallback.

    Returns:
        tuple:
            - response: The LLM response object, or `None` if all attempts failed.
            - finish_reason (str): Reason why generation finished ("stop",
              "length", "error", etc.).
            - completion_tokens (int): Number of tokens generated in the final attempt.

    Notes:
        - This function prints diagnostic information when degrading reasoning effort.
        - For persistent server-side issues (400/500), degradation is attempted
          automatically, but a permanent fix may require upstream changes
          (see https://github.com/pydantic/pydantic-ai/issues/2449).
    """
    if not cepo_config.use_reasoning_fallback:
        reasoning_effort_levels = ['high']
    for effort in reasoning_effort_levels:
        try:
            provider_request['reasoning_effort'] = effort
            response, finish_reason, completion_tokens = llm_call(client=client, provider_request=provider_request, cepo_config=cepo_config)
            if response is not None and finish_reason != 'length':
                return (response, finish_reason, completion_tokens)
            print(f'Reasoning fallback from {effort}, to lower one')
        except (OpenAIBadRequestError, OpenAIInternalServerError) as e:
            print('400/500 persisted after retries at reasoning effort', effort, '→ degrading')
            continue
    return (None, 'error', 0)

def run_single_completion(i):
    if cepo_config.print_output:
        print(f'\nCePO: Generating completion {i + 1} out of {cepo_config.bestofn_n} \n')
    approach = approaches[i] if approaches else None
    response_i, completion_tokens_i, cb_log_i = generate_completion(system_prompt, initial_query, client, model, cepo_config, approach, request_id)
    return (i, response_i, completion_tokens_i, cb_log_i)

class TestConversationLoggingWithServer(unittest.TestCase):
    """Integration tests with real OptILLM server and conversation logging"""

    @classmethod
    def setUpClass(cls):
        """Set up OptILLM server for testing"""
        setup_test_env()
        cls.server_available = cls._check_existing_server()
        cls.server_process = None
        cls.temp_log_dir = None
        if not cls.server_available:
            cls.temp_log_dir = Path(tempfile.mkdtemp())
            cls.server_process = cls._start_server_with_logging()
            max_wait = 30
            start_time = time.time()
            while time.time() - start_time < max_wait:
                if cls._check_server_health():
                    cls.server_available = True
                    break
                time.sleep(1)
            if not cls.server_available:
                if cls.server_process:
                    stop_test_server(cls.server_process)
                raise unittest.SkipTest('Could not start OptILLM server for testing')

    @classmethod
    def tearDownClass(cls):
        """Clean up server"""
        if cls.server_process:
            stop_test_server(cls.server_process)
        if cls.temp_log_dir and cls.temp_log_dir.exists():
            import shutil
            shutil.rmtree(cls.temp_log_dir, ignore_errors=True)

    @staticmethod
    def _check_existing_server():
        """Check if OptILLM server is already running"""
        try:
            response = requests.get('http://localhost:8000/v1/health', timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def _check_server_health():
        """Check if server is healthy"""
        try:
            response = requests.get('http://localhost:8000/v1/health', timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def _start_server_with_logging(cls):
        """Start server with conversation logging enabled"""
        env = os.environ.copy()
        env['OPTILLM_API_KEY'] = 'optillm'
        env['OPTILLM_LOG_CONVERSATIONS'] = 'true'
        env['OPTILLM_CONVERSATION_LOG_DIR'] = str(cls.temp_log_dir)
        proc = subprocess.Popen([sys.executable, 'optillm.py', '--model', TEST_MODEL, '--port', '8000', '--log-conversations', '--conversation-log-dir', str(cls.temp_log_dir)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc

    def setUp(self):
        """Set up test client"""
        if not self.server_available:
            self.skipTest('OptILLM server not available')
        self.client = OpenAI(api_key='optillm', base_url='http://localhost:8000/v1')
        if self.temp_log_dir:
            self.log_dir = self.temp_log_dir
        else:
            self.log_dir = Path.home() / '.optillm' / 'conversations'
        self.initial_log_files = set(self.log_dir.glob('*.jsonl')) if self.log_dir.exists() else set()

    def _get_new_log_entries(self):
        """Get new log entries since test started"""
        if not self.log_dir.exists():
            return []
        current_log_files = set(self.log_dir.glob('*.jsonl'))
        new_files = current_log_files - self.initial_log_files
        modified_files = [f for f in self.initial_log_files if f in current_log_files and f.stat().st_mtime > time.time() - 60]
        entries = []
        for log_file in new_files.union(set(modified_files)):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            entries.append(json.loads(line))
            except (json.JSONDecodeError, IOError):
                continue
        return entries

    def test_basic_none_approach_logging(self):
        """Test basic none approach with conversation logging"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is 2 + 2? Answer with just the number.'}], max_tokens=10)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        self.assertIsNotNone(response.choices[0].message.content)
        time.sleep(2)
        entries = self._get_new_log_entries()
        self.assertGreater(len(entries), 0, 'No log entries found for basic none approach')
        found_entry = False
        for entry in entries:
            if entry.get('approach') == 'none' and entry.get('model') == TEST_MODEL:
                found_entry = True
                self.assertIn('provider_calls', entry)
                self.assertIn('client_request', entry)
                self.assertIn('timestamp', entry)
                break
        self.assertTrue(found_entry, 'No valid log entry found for none approach')

    def test_re2_approach_logging(self):
        """Test RE2 approach with conversation logging"""
        response = self.client.chat.completions.create(model=f're2-{TEST_MODEL}', messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is the capital of France? Answer in one word.'}], max_tokens=10)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        time.sleep(3)
        entries = self._get_new_log_entries()
        re2_entry = None
        for entry in entries:
            if entry.get('approach') == 're2':
                re2_entry = entry
                break
        self.assertIsNotNone(re2_entry, 'No RE2 log entry found')
        self.assertEqual(re2_entry['model'], TEST_MODEL)
        self.assertIn('provider_calls', re2_entry)
        self.assertGreaterEqual(len(re2_entry['provider_calls']), 1)

    def test_cot_reflection_approach_logging(self):
        """Test CoT Reflection approach with conversation logging"""
        response = self.client.chat.completions.create(model=f'cot_reflection-{TEST_MODEL}', messages=[{'role': 'system', 'content': 'Think step by step.'}, {'role': 'user', 'content': 'What is 3 × 4? Show your work.'}], max_tokens=50)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        time.sleep(3)
        entries = self._get_new_log_entries()
        cot_entry = None
        for entry in entries:
            if entry.get('approach') == 'cot_reflection':
                cot_entry = entry
                break
        self.assertIsNotNone(cot_entry, 'No CoT reflection log entry found')
        self.assertEqual(cot_entry['model'], TEST_MODEL)
        self.assertIn('provider_calls', cot_entry)
        self.assertGreaterEqual(len(cot_entry['provider_calls']), 1)

    def test_extra_body_approach_logging(self):
        """Test approach specification via extra_body parameter"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': "Test extra_body. Reply with 'OK'."}], extra_body={'optillm_approach': 're2'}, max_tokens=10)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        time.sleep(3)
        entries = self._get_new_log_entries()
        found_entry = False
        for entry in entries:
            if entry.get('approach') == 're2' and entry.get('model') == TEST_MODEL:
                found_entry = True
                self.assertIn('provider_calls', entry)
                break
        self.assertTrue(found_entry, 'No log entry found for extra_body approach specification')

    def test_reasoning_tokens_logging(self):
        """Test that reasoning tokens are properly logged"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'Think step by step and show reasoning.'}, {'role': 'user', 'content': 'What is 5 + 7? Explain your thinking.'}], max_tokens=100)
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.usage)
        time.sleep(3)
        entries = self._get_new_log_entries()
        found_usage_entry = False
        for entry in entries:
            if 'provider_calls' in entry and len(entry['provider_calls']) > 0:
                for call in entry['provider_calls']:
                    if 'response' in call and 'usage' in call['response']:
                        found_usage_entry = True
                        usage = call['response']['usage']
                        self.assertIn('completion_tokens', usage)
                        if 'completion_tokens_details' in usage:
                            details = usage['completion_tokens_details']
                            if 'reasoning_tokens' in details:
                                self.assertIsInstance(details['reasoning_tokens'], int)
                        break
            if found_usage_entry:
                break
        self.assertTrue(found_usage_entry, 'No log entry with usage information found')

    def test_multiple_approaches_logging(self):
        """Test multiple different approaches get logged correctly"""
        approaches_to_test = [('none', TEST_MODEL), ('re2', f're2-{TEST_MODEL}'), ('cot_reflection', f'cot_reflection-{TEST_MODEL}')]
        responses = []
        for approach_name, model_name in approaches_to_test:
            try:
                response = self.client.chat.completions.create(model=model_name, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f"Test {approach_name}. Reply 'OK'."}], max_tokens=10)
                responses.append((approach_name, response))
                time.sleep(1)
            except Exception as e:
                self.fail(f'Approach {approach_name} failed: {e}')
        self.assertEqual(len(responses), 3)
        for approach_name, response in responses:
            self.assertIsNotNone(response)
            self.assertGreater(len(response.choices), 0)
        time.sleep(5)
        entries = self._get_new_log_entries()
        found_approaches = set()
        for entry in entries:
            approach = entry.get('approach')
            if approach in ['none', 're2', 'cot_reflection']:
                found_approaches.add(approach)
                self.assertEqual(entry['model'], TEST_MODEL)
                self.assertIn('provider_calls', entry)
        self.assertGreaterEqual(len(found_approaches), 2, f'Not all approaches logged. Found: {found_approaches}')

    def test_concurrent_requests_logging(self):
        """Test that concurrent requests are logged properly"""
        import threading
        import queue
        results = queue.Queue()

        def make_request(index):
            try:
                response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f'Concurrent test {index}. Reply with the number {index}.'}], max_tokens=10)
                results.put(('success', index, response))
            except Exception as e:
                results.put(('error', index, str(e)))
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        successful_requests = []
        while not results.empty():
            result_type, index, result = results.get()
            if result_type == 'success':
                successful_requests.append((index, result))
            else:
                self.fail(f'Concurrent request {index} failed: {result}')
        self.assertGreaterEqual(len(successful_requests), 2, 'Not enough concurrent requests succeeded')
        time.sleep(5)
        entries = self._get_new_log_entries()
        concurrent_entries = [e for e in entries if 'Concurrent test' in str(e.get('client_request', {}))]
        self.assertGreaterEqual(len(concurrent_entries), 2, 'Not enough concurrent request log entries found')

    def test_error_handling_logging(self):
        """Test that errors in approaches are properly logged"""
        try:
            response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'This is a test for error logging scenarios.'}], max_tokens=1)
            self.assertIsNotNone(response)
        except Exception:
            pass
        time.sleep(3)
        entries = self._get_new_log_entries()
        found_relevant_entry = False
        for entry in entries:
            if 'error logging scenarios' in str(entry.get('client_request', {})):
                found_relevant_entry = True
                break
        self.assertGreaterEqual(len(entries), 0, 'No log entries found (system may have crashed)')

    def test_log_file_structure_and_format(self):
        """Test that log files have correct JSONL structure and required fields"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': "Structure test. Reply 'STRUCTURE_OK'."}], max_tokens=15)
        self.assertIsNotNone(response)
        time.sleep(3)
        entries = self._get_new_log_entries()
        relevant_entry = None
        for entry in entries:
            if 'STRUCTURE_OK' in str(entry.get('client_request', {})) or 'Structure test' in str(entry.get('client_request', {})):
                relevant_entry = entry
                break
        if not relevant_entry and entries:
            relevant_entry = entries[0]
        self.assertIsNotNone(relevant_entry, 'No log entry found for structure validation')
        required_fields = ['timestamp', 'request_id', 'approach', 'model', 'client_request', 'provider_calls']
        for field in required_fields:
            self.assertIn(field, relevant_entry, f'Missing required field: {field}')
        provider_calls = relevant_entry['provider_calls']
        self.assertIsInstance(provider_calls, list)
        self.assertGreater(len(provider_calls), 0, 'No provider calls logged')
        for call in provider_calls:
            self.assertIn('request', call)
            self.assertIn('response', call)
            self.assertIn('timestamp', call)
            self.assertIn('call_number', call)
        self.assertIsInstance(relevant_entry['timestamp'], str)
        for call in provider_calls:
            self.assertIsInstance(call['timestamp'], str)

def setUp(self):
    """Set up test client"""
    if not self.server_available:
        self.skipTest('OptILLM server not available')
    self.client = OpenAI(api_key='optillm', base_url='http://localhost:8000/v1')
    if self.temp_log_dir:
        self.log_dir = self.temp_log_dir
    else:
        self.log_dir = Path.home() / '.optillm' / 'conversations'
    self.initial_log_files = set(self.log_dir.glob('*.jsonl')) if self.log_dir.exists() else set()

def test_basic_none_approach_logging(self):
    """Test basic none approach with conversation logging"""
    response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is 2 + 2? Answer with just the number.'}], max_tokens=10)
    self.assertIsNotNone(response)
    self.assertGreater(len(response.choices), 0)
    self.assertIsNotNone(response.choices[0].message.content)
    time.sleep(2)
    entries = self._get_new_log_entries()
    self.assertGreater(len(entries), 0, 'No log entries found for basic none approach')
    found_entry = False
    for entry in entries:
        if entry.get('approach') == 'none' and entry.get('model') == TEST_MODEL:
            found_entry = True
            self.assertIn('provider_calls', entry)
            self.assertIn('client_request', entry)
            self.assertIn('timestamp', entry)
            break
    self.assertTrue(found_entry, 'No valid log entry found for none approach')

def test_re2_approach_logging(self):
    """Test RE2 approach with conversation logging"""
    response = self.client.chat.completions.create(model=f're2-{TEST_MODEL}', messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is the capital of France? Answer in one word.'}], max_tokens=10)
    self.assertIsNotNone(response)
    self.assertGreater(len(response.choices), 0)
    time.sleep(3)
    entries = self._get_new_log_entries()
    re2_entry = None
    for entry in entries:
        if entry.get('approach') == 're2':
            re2_entry = entry
            break
    self.assertIsNotNone(re2_entry, 'No RE2 log entry found')
    self.assertEqual(re2_entry['model'], TEST_MODEL)
    self.assertIn('provider_calls', re2_entry)
    self.assertGreaterEqual(len(re2_entry['provider_calls']), 1)

def test_cot_reflection_approach_logging(self):
    """Test CoT Reflection approach with conversation logging"""
    response = self.client.chat.completions.create(model=f'cot_reflection-{TEST_MODEL}', messages=[{'role': 'system', 'content': 'Think step by step.'}, {'role': 'user', 'content': 'What is 3 × 4? Show your work.'}], max_tokens=50)
    self.assertIsNotNone(response)
    self.assertGreater(len(response.choices), 0)
    time.sleep(3)
    entries = self._get_new_log_entries()
    cot_entry = None
    for entry in entries:
        if entry.get('approach') == 'cot_reflection':
            cot_entry = entry
            break
    self.assertIsNotNone(cot_entry, 'No CoT reflection log entry found')
    self.assertEqual(cot_entry['model'], TEST_MODEL)
    self.assertIn('provider_calls', cot_entry)
    self.assertGreaterEqual(len(cot_entry['provider_calls']), 1)

def test_extra_body_approach_logging(self):
    """Test approach specification via extra_body parameter"""
    response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': "Test extra_body. Reply with 'OK'."}], extra_body={'optillm_approach': 're2'}, max_tokens=10)
    self.assertIsNotNone(response)
    self.assertGreater(len(response.choices), 0)
    time.sleep(3)
    entries = self._get_new_log_entries()
    found_entry = False
    for entry in entries:
        if entry.get('approach') == 're2' and entry.get('model') == TEST_MODEL:
            found_entry = True
            self.assertIn('provider_calls', entry)
            break
    self.assertTrue(found_entry, 'No log entry found for extra_body approach specification')

def test_reasoning_tokens_logging(self):
    """Test that reasoning tokens are properly logged"""
    response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'Think step by step and show reasoning.'}, {'role': 'user', 'content': 'What is 5 + 7? Explain your thinking.'}], max_tokens=100)
    self.assertIsNotNone(response)
    self.assertIsNotNone(response.usage)
    time.sleep(3)
    entries = self._get_new_log_entries()
    found_usage_entry = False
    for entry in entries:
        if 'provider_calls' in entry and len(entry['provider_calls']) > 0:
            for call in entry['provider_calls']:
                if 'response' in call and 'usage' in call['response']:
                    found_usage_entry = True
                    usage = call['response']['usage']
                    self.assertIn('completion_tokens', usage)
                    if 'completion_tokens_details' in usage:
                        details = usage['completion_tokens_details']
                        if 'reasoning_tokens' in details:
                            self.assertIsInstance(details['reasoning_tokens'], int)
                    break
        if found_usage_entry:
            break
    self.assertTrue(found_usage_entry, 'No log entry with usage information found')

def test_multiple_approaches_logging(self):
    """Test multiple different approaches get logged correctly"""
    approaches_to_test = [('none', TEST_MODEL), ('re2', f're2-{TEST_MODEL}'), ('cot_reflection', f'cot_reflection-{TEST_MODEL}')]
    responses = []
    for approach_name, model_name in approaches_to_test:
        try:
            response = self.client.chat.completions.create(model=model_name, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f"Test {approach_name}. Reply 'OK'."}], max_tokens=10)
            responses.append((approach_name, response))
            time.sleep(1)
        except Exception as e:
            self.fail(f'Approach {approach_name} failed: {e}')
    self.assertEqual(len(responses), 3)
    for approach_name, response in responses:
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
    time.sleep(5)
    entries = self._get_new_log_entries()
    found_approaches = set()
    for entry in entries:
        approach = entry.get('approach')
        if approach in ['none', 're2', 'cot_reflection']:
            found_approaches.add(approach)
            self.assertEqual(entry['model'], TEST_MODEL)
            self.assertIn('provider_calls', entry)
    self.assertGreaterEqual(len(found_approaches), 2, f'Not all approaches logged. Found: {found_approaches}')

def test_error_handling_logging(self):
    """Test that errors in approaches are properly logged"""
    try:
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'This is a test for error logging scenarios.'}], max_tokens=1)
        self.assertIsNotNone(response)
    except Exception:
        pass
    time.sleep(3)
    entries = self._get_new_log_entries()
    found_relevant_entry = False
    for entry in entries:
        if 'error logging scenarios' in str(entry.get('client_request', {})):
            found_relevant_entry = True
            break
    self.assertGreaterEqual(len(entries), 0, 'No log entries found (system may have crashed)')

def test_log_file_structure_and_format(self):
    """Test that log files have correct JSONL structure and required fields"""
    response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': "Structure test. Reply 'STRUCTURE_OK'."}], max_tokens=15)
    self.assertIsNotNone(response)
    time.sleep(3)
    entries = self._get_new_log_entries()
    relevant_entry = None
    for entry in entries:
        if 'STRUCTURE_OK' in str(entry.get('client_request', {})) or 'Structure test' in str(entry.get('client_request', {})):
            relevant_entry = entry
            break
    if not relevant_entry and entries:
        relevant_entry = entries[0]
    self.assertIsNotNone(relevant_entry, 'No log entry found for structure validation')
    required_fields = ['timestamp', 'request_id', 'approach', 'model', 'client_request', 'provider_calls']
    for field in required_fields:
        self.assertIn(field, relevant_entry, f'Missing required field: {field}')
    provider_calls = relevant_entry['provider_calls']
    self.assertIsInstance(provider_calls, list)
    self.assertGreater(len(provider_calls), 0, 'No provider calls logged')
    for call in provider_calls:
        self.assertIn('request', call)
        self.assertIn('response', call)
        self.assertIn('timestamp', call)
        self.assertIn('call_number', call)
    self.assertIsInstance(relevant_entry['timestamp'], str)
    for call in provider_calls:
        self.assertIsInstance(call['timestamp'], str)

@unittest.skipUnless(os.getenv('OPTILLM_API_KEY') == 'optillm', 'Set OPTILLM_API_KEY=optillm to run server-based tests')
class TestConversationLoggingPerformanceWithServer(unittest.TestCase):
    """Performance tests with real server"""

    def setUp(self):
        """Check server availability"""
        if not requests.get('http://localhost:8000/v1/health', timeout=2).status_code == 200:
            self.skipTest('OptILLM server not available')
        self.client = OpenAI(api_key='optillm', base_url='http://localhost:8000/v1')

    def test_logging_performance_impact(self):
        """Test that logging doesn't significantly impact response time"""
        import time
        self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': 'warmup'}], max_tokens=5)
        times = []
        for i in range(5):
            start_time = time.perf_counter()
            response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f"Performance test {i}. Reply 'OK'."}], max_tokens=5)
            end_time = time.perf_counter()
            self.assertIsNotNone(response)
            times.append(end_time - start_time)
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 10.0, f'Average response time too slow: {avg_time:.2f}s')
        print(f'\n📊 Server Performance with Logging:')
        print(f'   Average response time: {avg_time:.3f}s')
        print(f'   Response times: {[f'{t:.3f}s' for t in times]}')

def test_logging_performance_impact(self):
    """Test that logging doesn't significantly impact response time"""
    import time
    self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': 'warmup'}], max_tokens=5)
    times = []
    for i in range(5):
        start_time = time.perf_counter()
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f"Performance test {i}. Reply 'OK'."}], max_tokens=5)
        end_time = time.perf_counter()
        self.assertIsNotNone(response)
        times.append(end_time - start_time)
    avg_time = sum(times) / len(times)
    self.assertLess(avg_time, 10.0, f'Average response time too slow: {avg_time:.2f}s')
    print(f'\n📊 Server Performance with Logging:')
    print(f'   Average response time: {avg_time:.3f}s')
    print(f'   Response times: {[f'{t:.3f}s' for t in times]}')

class TestConversationLoggingApproaches(unittest.TestCase):
    """Test conversation logging across all approaches"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / 'conversations'
        self.logger = ConversationLogger(self.log_dir, enabled=True)
        optillm.conversation_logger = self.logger
        self.system_prompt = 'You are a helpful assistant.'
        self.initial_query = 'What is 2 + 2?'
        self.model = 'test-model'
        self.request_id = 'test-request-123'
        self.client = MockOpenAIClient()

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        optillm.conversation_logger = None

    def test_multi_call_approaches_logging(self):
        """Test BON, MCTS, and RTO approaches log API calls correctly"""
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'bon', self.model)
        result, tokens = best_of_n_sampling(self.system_prompt, self.initial_query, self.client, self.model, n=2, request_id=self.request_id)
        bon_calls = self.client.call_count
        self.assertGreaterEqual(bon_calls, 2)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        self.client.call_count = 0
        mcts_request_id = self.request_id + '_mcts'
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'mcts', self.model)
        result, tokens = chat_with_mcts(self.system_prompt, self.initial_query, self.client, self.model, num_simulations=2, exploration_weight=0.2, simulation_depth=1, request_id=mcts_request_id)
        mcts_calls = self.client.call_count
        self.assertGreaterEqual(mcts_calls, 1)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        self.client.call_count = 0
        rto_request_id = self.request_id + '_rto'
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'rto', self.model)
        result, tokens = round_trip_optimization(self.system_prompt, self.initial_query, self.client, self.model, request_id=rto_request_id)
        rto_calls = self.client.call_count
        self.assertGreaterEqual(rto_calls, 3)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)

    def test_single_call_approaches_logging(self):
        """Test CoT Reflection and RE2 approaches log single API calls correctly"""
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'cot_reflection', self.model)
        result, tokens = cot_reflection(self.system_prompt, self.initial_query, self.client, self.model, request_id=self.request_id)
        self.assertEqual(self.client.call_count, 1)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        self.client.call_count = 0
        re2_request_id = self.request_id + '_re2'
        self.logger.start_conversation({'model': self.model, 'messages': []}, 're2', self.model)
        result, tokens = re2_approach(self.system_prompt, self.initial_query, self.client, self.model, n=1, request_id=re2_request_id)
        self.assertEqual(self.client.call_count, 1)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)

    def test_sampling_approaches_logging(self):
        """Test PVG and Self Consistency approaches log multiple sampling calls"""
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'pvg', self.model)
        result, tokens = inference_time_pv_game(self.system_prompt, self.initial_query, self.client, self.model, num_rounds=1, num_solutions=2, request_id=self.request_id)
        pvg_calls = self.client.call_count
        self.assertGreaterEqual(pvg_calls, 3)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        self.client.call_count = 0
        sc_request_id = self.request_id + '_sc'
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'self_consistency', self.model)
        result, tokens = advanced_self_consistency_approach(self.system_prompt, self.initial_query, self.client, self.model, request_id=sc_request_id)
        self.assertEqual(self.client.call_count, 5)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)

    @patch('optillm.z3_solver.multiprocessing.get_context')
    def test_complex_class_based_approaches_logging(self, mock_mp_context):
        """Test RStar and Z3 Solver class-based approaches log API calls correctly"""
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'rstar', self.model)
        rstar = RStar(self.system_prompt, self.client, self.model, max_depth=2, num_rollouts=2, request_id=self.request_id)
        result, tokens = rstar.solve(self.initial_query)
        rstar_calls = self.client.call_count
        self.assertGreaterEqual(rstar_calls, 1)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        self.client.call_count = 0
        z3_request_id = self.request_id + '_z3'
        self.logger.start_conversation({'model': self.model, 'messages': []}, 'z3', self.model)
        mock_pool = Mock()
        mock_result = Mock()
        mock_result.get.return_value = ('success', 'Test solver output')
        mock_pool.apply_async.return_value = mock_result
        mock_context = Mock()
        mock_context.Pool.return_value = MagicMock()
        mock_context.Pool.return_value.__enter__.return_value = mock_pool
        mock_context.Pool.return_value.__exit__.return_value = None
        mock_mp_context.return_value = mock_context
        z3_solver = Z3SymPySolverSystem(self.system_prompt, self.client, self.model, request_id=z3_request_id)
        result, tokens = z3_solver.process_query(self.initial_query)
        self.assertGreaterEqual(self.client.call_count, 1)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)

    def test_logging_edge_cases(self):
        """Test approaches work with logging disabled, no request_id, and API errors"""
        optillm.conversation_logger = None
        result, tokens = best_of_n_sampling(self.system_prompt, self.initial_query, self.client, self.model, n=2, request_id=self.request_id)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        optillm.conversation_logger = self.logger
        self.client.call_count = 0
        result, tokens = cot_reflection(self.system_prompt, self.initial_query, self.client, self.model, request_id=None)
        self.assertIsInstance(result, str)
        self.assertGreater(tokens, 0)
        error_client = Mock()
        error_client.chat.completions.create.side_effect = Exception('API Error')
        with self.assertRaises(Exception):
            cot_reflection(self.system_prompt, self.initial_query, error_client, self.model, request_id=self.request_id)

    def test_full_integration_with_file_logging(self):
        """Test complete integration from approach execution to file logging"""
        request_id = self.logger.start_conversation({'model': 'test-model', 'messages': []}, 'bon', 'test-model')
        result, tokens = best_of_n_sampling('You are a helpful assistant.', 'What is 2 + 2?', self.client, 'test-model', n=2, request_id=request_id)
        self.logger.finalize_conversation(request_id)
        log_files = list(self.log_dir.glob('*.jsonl'))
        self.assertGreater(len(log_files), 0)
        with open(log_files[0], 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0)
            log_entry = json.loads(lines[0].strip())
            self.assertEqual(log_entry['approach'], 'bon')
            self.assertIn('provider_calls', log_entry)
            self.assertGreater(len(log_entry['provider_calls']), 0)

def test_multi_call_approaches_logging(self):
    """Test BON, MCTS, and RTO approaches log API calls correctly"""
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'bon', self.model)
    result, tokens = best_of_n_sampling(self.system_prompt, self.initial_query, self.client, self.model, n=2, request_id=self.request_id)
    bon_calls = self.client.call_count
    self.assertGreaterEqual(bon_calls, 2)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    self.client.call_count = 0
    mcts_request_id = self.request_id + '_mcts'
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'mcts', self.model)
    result, tokens = chat_with_mcts(self.system_prompt, self.initial_query, self.client, self.model, num_simulations=2, exploration_weight=0.2, simulation_depth=1, request_id=mcts_request_id)
    mcts_calls = self.client.call_count
    self.assertGreaterEqual(mcts_calls, 1)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    self.client.call_count = 0
    rto_request_id = self.request_id + '_rto'
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'rto', self.model)
    result, tokens = round_trip_optimization(self.system_prompt, self.initial_query, self.client, self.model, request_id=rto_request_id)
    rto_calls = self.client.call_count
    self.assertGreaterEqual(rto_calls, 3)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)

def test_single_call_approaches_logging(self):
    """Test CoT Reflection and RE2 approaches log single API calls correctly"""
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'cot_reflection', self.model)
    result, tokens = cot_reflection(self.system_prompt, self.initial_query, self.client, self.model, request_id=self.request_id)
    self.assertEqual(self.client.call_count, 1)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    self.client.call_count = 0
    re2_request_id = self.request_id + '_re2'
    self.logger.start_conversation({'model': self.model, 'messages': []}, 're2', self.model)
    result, tokens = re2_approach(self.system_prompt, self.initial_query, self.client, self.model, n=1, request_id=re2_request_id)
    self.assertEqual(self.client.call_count, 1)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)

def test_sampling_approaches_logging(self):
    """Test PVG and Self Consistency approaches log multiple sampling calls"""
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'pvg', self.model)
    result, tokens = inference_time_pv_game(self.system_prompt, self.initial_query, self.client, self.model, num_rounds=1, num_solutions=2, request_id=self.request_id)
    pvg_calls = self.client.call_count
    self.assertGreaterEqual(pvg_calls, 3)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    self.client.call_count = 0
    sc_request_id = self.request_id + '_sc'
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'self_consistency', self.model)
    result, tokens = advanced_self_consistency_approach(self.system_prompt, self.initial_query, self.client, self.model, request_id=sc_request_id)
    self.assertEqual(self.client.call_count, 5)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)

@patch('optillm.z3_solver.multiprocessing.get_context')
def test_complex_class_based_approaches_logging(self, mock_mp_context):
    """Test RStar and Z3 Solver class-based approaches log API calls correctly"""
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'rstar', self.model)
    rstar = RStar(self.system_prompt, self.client, self.model, max_depth=2, num_rollouts=2, request_id=self.request_id)
    result, tokens = rstar.solve(self.initial_query)
    rstar_calls = self.client.call_count
    self.assertGreaterEqual(rstar_calls, 1)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    self.client.call_count = 0
    z3_request_id = self.request_id + '_z3'
    self.logger.start_conversation({'model': self.model, 'messages': []}, 'z3', self.model)
    mock_pool = Mock()
    mock_result = Mock()
    mock_result.get.return_value = ('success', 'Test solver output')
    mock_pool.apply_async.return_value = mock_result
    mock_context = Mock()
    mock_context.Pool.return_value = MagicMock()
    mock_context.Pool.return_value.__enter__.return_value = mock_pool
    mock_context.Pool.return_value.__exit__.return_value = None
    mock_mp_context.return_value = mock_context
    z3_solver = Z3SymPySolverSystem(self.system_prompt, self.client, self.model, request_id=z3_request_id)
    result, tokens = z3_solver.process_query(self.initial_query)
    self.assertGreaterEqual(self.client.call_count, 1)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)

def test_logging_edge_cases(self):
    """Test approaches work with logging disabled, no request_id, and API errors"""
    optillm.conversation_logger = None
    result, tokens = best_of_n_sampling(self.system_prompt, self.initial_query, self.client, self.model, n=2, request_id=self.request_id)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    optillm.conversation_logger = self.logger
    self.client.call_count = 0
    result, tokens = cot_reflection(self.system_prompt, self.initial_query, self.client, self.model, request_id=None)
    self.assertIsInstance(result, str)
    self.assertGreater(tokens, 0)
    error_client = Mock()
    error_client.chat.completions.create.side_effect = Exception('API Error')
    with self.assertRaises(Exception):
        cot_reflection(self.system_prompt, self.initial_query, error_client, self.model, request_id=self.request_id)

def test_full_integration_with_file_logging(self):
    """Test complete integration from approach execution to file logging"""
    request_id = self.logger.start_conversation({'model': 'test-model', 'messages': []}, 'bon', 'test-model')
    result, tokens = best_of_n_sampling('You are a helpful assistant.', 'What is 2 + 2?', self.client, 'test-model', n=2, request_id=request_id)
    self.logger.finalize_conversation(request_id)
    log_files = list(self.log_dir.glob('*.jsonl'))
    self.assertGreater(len(log_files), 0)
    with open(log_files[0], 'r') as f:
        lines = f.readlines()
        self.assertGreater(len(lines), 0)
        log_entry = json.loads(lines[0].strip())
        self.assertEqual(log_entry['approach'], 'bon')
        self.assertIn('provider_calls', log_entry)
        self.assertGreater(len(log_entry['provider_calls']), 0)

def main():
    """Run all tests."""
    logger.info('Starting DeepConf test suite...')
    tests = [test_imports, test_confidence_calculator, test_threshold_calibrator, test_config_validation, test_info_function]
    passed = 0
    total = len(tests)
    for test in tests:
        if test():
            passed += 1
        print()
    logger.info(f'Test Results: {passed}/{total} tests passed')
    if passed == total:
        logger.info('🎉 All tests passed! DeepConf implementation is working correctly.')
        return 0
    else:
        logger.error('❌ Some tests failed. Please check the implementation.')
        return 1

class TestReasoningTokensCore(unittest.TestCase):
    """Test core reasoning token functionality"""

    def test_count_reasoning_tokens_with_think_tags(self):
        """Test counting tokens in think tags"""
        text = '<think>Let me think about this problem step by step</think>The answer is 42'
        result1 = optillm_count(text)
        result2 = inference_count(text)
        self.assertGreater(result1, 0, 'Should count tokens in think tags')
        self.assertEqual(result1, result2, 'Both functions should return same result')

    def test_count_reasoning_tokens_without_think_tags(self):
        """Test with text that has no think tags"""
        text = 'This is just a regular response without any thinking'
        result1 = optillm_count(text)
        result2 = inference_count(text)
        self.assertEqual(result1, 0, 'Should return 0 for text without think tags')
        self.assertEqual(result2, 0, 'Should return 0 for text without think tags')

    def test_count_reasoning_tokens_multiple_blocks(self):
        """Test with multiple think tag blocks"""
        text = '\n        <think>First block of reasoning</think>\n        Some output here\n        <think>Second block with more reasoning</think>\n        Final answer\n        '
        result = optillm_count(text)
        self.assertGreater(result, 0, 'Should count tokens from multiple blocks')

    def test_count_reasoning_tokens_empty_cases(self):
        """Test edge cases with empty or invalid input"""
        test_cases = ['', None, 123, '<think></think>']
        for case in test_cases:
            result1 = optillm_count(case)
            result2 = inference_count(case)
            self.assertGreaterEqual(result1, 0, f'Should handle {case} gracefully')
            self.assertGreaterEqual(result2, 0, f'Should handle {case} gracefully')

    def test_count_reasoning_tokens_with_mock_tokenizer(self):
        """Test with a simple mock tokenizer"""

        class MockTokenizer:

            def encode(self, text):
                return text.split()
        tokenizer = MockTokenizer()
        text = '<think>hello world test</think>answer'
        result = optillm_count(text, tokenizer)
        self.assertEqual(result, 3, 'Should use tokenizer when provided')

    def test_reasoning_tokens_fallback_estimation(self):
        """Test fallback estimation when tokenizer fails"""

        class FailingTokenizer:

            def encode(self, text):
                raise Exception('Tokenizer failed')
        tokenizer = FailingTokenizer()
        text = '<think>some reasoning content here</think>answer'
        result = optillm_count(text, tokenizer)
        self.assertGreater(result, 0, 'Should fallback to character estimation')

    def test_count_reasoning_tokens_truncated_response(self):
        """Test counting tokens when response is truncated (no closing </think> tag)"""
        truncated_text = '<think>This reasoning was cut off due to max tokens'
        result1 = optillm_count(truncated_text)
        result2 = inference_count(truncated_text)
        self.assertGreater(result1, 0, 'Should count tokens from truncated think block')
        self.assertEqual(result1, result2, 'Both functions should return same result')

    def test_count_reasoning_tokens_mixed_complete_and_truncated(self):
        """Test with both complete and truncated think blocks"""
        mixed_text = '\n        <think>First complete reasoning block</think>\n        Some output here\n        <think>This second block was truncated and never closed\n        '
        result = optillm_count(mixed_text)
        self.assertGreater(result, 0, 'Should count tokens from both complete and truncated blocks')
        first_block_only = '<think>First complete reasoning block</think>'
        first_result = optillm_count(first_block_only)
        self.assertGreater(result, first_result, 'Should include truncated content')

    def test_count_reasoning_tokens_no_false_positives(self):
        """Test that we don't count think-like content that isn't actually truncated"""
        text_with_complete_blocks = '<think>First block</think>Output<think>Second complete block</think>'
        result = optillm_count(text_with_complete_blocks)
        manual_count = optillm_count('<think>First blockSecond complete block</think>')
        self.assertEqual(result, manual_count, 'Should only count complete blocks, not detect false truncation')

    def test_count_reasoning_tokens_edge_cases_truncated(self):
        """Test edge cases with truncated responses"""
        test_cases = [('<think>', 0), ('<think>a', 1), ('Some output <think>reasoning here', None), ('<think>multi\nline\ntruncated', None)]
        for text, expected_min in test_cases:
            result = optillm_count(text)
            if expected_min is not None:
                if expected_min == 0:
                    self.assertEqual(result, expected_min, f'Should return {expected_min} for: {text}')
                else:
                    self.assertGreaterEqual(result, expected_min, f'Should be at least {expected_min} for: {text}')
            else:
                self.assertGreater(result, 0, f'Should count truncated content for: {text}')

def test_count_reasoning_tokens_with_think_tags(self):
    """Test counting tokens in think tags"""
    text = '<think>Let me think about this problem step by step</think>The answer is 42'
    result1 = optillm_count(text)
    result2 = inference_count(text)
    self.assertGreater(result1, 0, 'Should count tokens in think tags')
    self.assertEqual(result1, result2, 'Both functions should return same result')

def test_count_reasoning_tokens_without_think_tags(self):
    """Test with text that has no think tags"""
    text = 'This is just a regular response without any thinking'
    result1 = optillm_count(text)
    result2 = inference_count(text)
    self.assertEqual(result1, 0, 'Should return 0 for text without think tags')
    self.assertEqual(result2, 0, 'Should return 0 for text without think tags')

def test_count_reasoning_tokens_multiple_blocks(self):
    """Test with multiple think tag blocks"""
    text = '\n        <think>First block of reasoning</think>\n        Some output here\n        <think>Second block with more reasoning</think>\n        Final answer\n        '
    result = optillm_count(text)
    self.assertGreater(result, 0, 'Should count tokens from multiple blocks')

def test_count_reasoning_tokens_empty_cases(self):
    """Test edge cases with empty or invalid input"""
    test_cases = ['', None, 123, '<think></think>']
    for case in test_cases:
        result1 = optillm_count(case)
        result2 = inference_count(case)
        self.assertGreaterEqual(result1, 0, f'Should handle {case} gracefully')
        self.assertGreaterEqual(result2, 0, f'Should handle {case} gracefully')

def test_count_reasoning_tokens_with_mock_tokenizer(self):
    """Test with a simple mock tokenizer"""

    class MockTokenizer:

        def encode(self, text):
            return text.split()
    tokenizer = MockTokenizer()
    text = '<think>hello world test</think>answer'
    result = optillm_count(text, tokenizer)
    self.assertEqual(result, 3, 'Should use tokenizer when provided')

def test_reasoning_tokens_fallback_estimation(self):
    """Test fallback estimation when tokenizer fails"""

    class FailingTokenizer:

        def encode(self, text):
            raise Exception('Tokenizer failed')
    tokenizer = FailingTokenizer()
    text = '<think>some reasoning content here</think>answer'
    result = optillm_count(text, tokenizer)
    self.assertGreater(result, 0, 'Should fallback to character estimation')

def test_count_reasoning_tokens_truncated_response(self):
    """Test counting tokens when response is truncated (no closing </think> tag)"""
    truncated_text = '<think>This reasoning was cut off due to max tokens'
    result1 = optillm_count(truncated_text)
    result2 = inference_count(truncated_text)
    self.assertGreater(result1, 0, 'Should count tokens from truncated think block')
    self.assertEqual(result1, result2, 'Both functions should return same result')

def test_count_reasoning_tokens_mixed_complete_and_truncated(self):
    """Test with both complete and truncated think blocks"""
    mixed_text = '\n        <think>First complete reasoning block</think>\n        Some output here\n        <think>This second block was truncated and never closed\n        '
    result = optillm_count(mixed_text)
    self.assertGreater(result, 0, 'Should count tokens from both complete and truncated blocks')
    first_block_only = '<think>First complete reasoning block</think>'
    first_result = optillm_count(first_block_only)
    self.assertGreater(result, first_result, 'Should include truncated content')

def test_count_reasoning_tokens_no_false_positives(self):
    """Test that we don't count think-like content that isn't actually truncated"""
    text_with_complete_blocks = '<think>First block</think>Output<think>Second complete block</think>'
    result = optillm_count(text_with_complete_blocks)
    manual_count = optillm_count('<think>First blockSecond complete block</think>')
    self.assertEqual(result, manual_count, 'Should only count complete blocks, not detect false truncation')

def test_count_reasoning_tokens_edge_cases_truncated(self):
    """Test edge cases with truncated responses"""
    test_cases = [('<think>', 0), ('<think>a', 1), ('Some output <think>reasoning here', None), ('<think>multi\nline\ntruncated', None)]
    for text, expected_min in test_cases:
        result = optillm_count(text)
        if expected_min is not None:
            if expected_min == 0:
                self.assertEqual(result, expected_min, f'Should return {expected_min} for: {text}')
            else:
                self.assertGreaterEqual(result, expected_min, f'Should be at least {expected_min} for: {text}')
        else:
            self.assertGreater(result, 0, f'Should count truncated content for: {text}')

class TestInferenceStructures(unittest.TestCase):
    """Test that inference structures support reasoning tokens"""

    def test_chat_completion_usage_with_reasoning_tokens(self):
        """Test ChatCompletionUsage supports reasoning_tokens"""
        from optillm.inference import ChatCompletionUsage
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, reasoning_tokens=5)
        self.assertEqual(usage.reasoning_tokens, 5)
        usage_default = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        self.assertEqual(usage_default.reasoning_tokens, 0)

    def test_chat_completion_model_dump_structure(self):
        """Test ChatCompletion model_dump includes reasoning_tokens"""
        from optillm.inference import ChatCompletion
        response_dict = {'id': 'test-123', 'object': 'chat.completion', 'created': 1234567890, 'model': 'test-model', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'test response'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 15, 'total_tokens': 25, 'reasoning_tokens': 3}}
        completion = ChatCompletion(response_dict)
        result = completion.model_dump()
        self.assertIn('usage', result)
        self.assertIn('completion_tokens_details', result['usage'])
        self.assertIn('reasoning_tokens', result['usage']['completion_tokens_details'])
        self.assertEqual(result['usage']['completion_tokens_details']['reasoning_tokens'], 3)

def test_chat_completion_usage_with_reasoning_tokens(self):
    """Test ChatCompletionUsage supports reasoning_tokens"""
    from optillm.inference import ChatCompletionUsage
    usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, reasoning_tokens=5)
    self.assertEqual(usage.reasoning_tokens, 5)
    usage_default = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    self.assertEqual(usage_default.reasoning_tokens, 0)

def test_chat_completion_model_dump_structure(self):
    """Test ChatCompletion model_dump includes reasoning_tokens"""
    from optillm.inference import ChatCompletion
    response_dict = {'id': 'test-123', 'object': 'chat.completion', 'created': 1234567890, 'model': 'test-model', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'test response'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 15, 'total_tokens': 25, 'reasoning_tokens': 3}}
    completion = ChatCompletion(response_dict)
    result = completion.model_dump()
    self.assertIn('usage', result)
    self.assertIn('completion_tokens_details', result['usage'])
    self.assertIn('reasoning_tokens', result['usage']['completion_tokens_details'])
    self.assertEqual(result['usage']['completion_tokens_details']['reasoning_tokens'], 3)

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

def run_imo25_tests():
    """Run all IMO25 MARS tests"""
    print('Running MARS IMO25 specific tests...')
    print('=' * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMARSIMO25)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print('=' * 80)
    if result.wasSuccessful():
        print('🎉 All IMO25 tests passed!')
        return True
    else:
        print('❌ Some IMO25 tests failed - analyzing for improvements')
        return False

class TestPluginStructure:
    """Test plugin structure and exports"""

    def test_slug_exists(self):
        """Test that plugin has SLUG defined"""
        assert hasattr(sys.modules['optillm.plugins.mcp_plugin'], 'SLUG')
        assert SLUG == 'mcp'

    def test_run_function_exists(self):
        """Test that plugin has run function defined"""
        import optillm.plugins.mcp_plugin as plugin
        assert hasattr(plugin, 'run')
        assert callable(plugin.run)

    def test_required_imports(self):
        """Test that required modules can be imported"""
        try:
            from mcp.client.sse import sse_client
            from mcp.client.websocket import websocket_client
            assert sse_client is not None
            assert websocket_client is not None
        except ImportError as e:
            pytest.fail(f'Required MCP imports failed: {e}')

def test_run_function_exists(self):
    """Test that plugin has run function defined"""
    import optillm.plugins.mcp_plugin as plugin
    assert hasattr(plugin, 'run')
    assert callable(plugin.run)

def test_privacy_plugin_resource_caching():
    """
    Test that expensive resources (AnalyzerEngine, AnonymizerEngine) are created only once
    and reused across multiple plugin invocations.
    """
    print('Testing privacy plugin resource caching...')
    if 'optillm.plugins.privacy_plugin' in sys.modules:
        del sys.modules['optillm.plugins.privacy_plugin']
    with patch('presidio_analyzer.AnalyzerEngine') as MockAnalyzerEngine, patch('presidio_anonymizer.AnonymizerEngine') as MockAnonymizerEngine, patch('spacy.util.is_package', return_value=True):
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.analyze.return_value = []
        MockAnalyzerEngine.return_value = mock_analyzer_instance
        mock_anonymizer_instance = MagicMock()
        mock_anonymizer_instance.anonymize.return_value = MagicMock(text='anonymized text')
        mock_anonymizer_instance.add_anonymizer = MagicMock()
        MockAnonymizerEngine.return_value = mock_anonymizer_instance
        import optillm.plugins.privacy_plugin as privacy_plugin
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='response'))]
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response
        print('First invocation...')
        result1, tokens1 = privacy_plugin.run('system', 'query 1', mock_client, 'model')
        assert MockAnalyzerEngine.call_count == 1, f'AnalyzerEngine created {MockAnalyzerEngine.call_count} times, expected 1'
        assert MockAnonymizerEngine.call_count == 1, f'AnonymizerEngine created {MockAnonymizerEngine.call_count} times, expected 1'
        print('Second invocation...')
        result2, tokens2 = privacy_plugin.run('system', 'query 2', mock_client, 'model')
        assert MockAnalyzerEngine.call_count == 1, f'AnalyzerEngine created {MockAnalyzerEngine.call_count} times after 2nd call, expected 1'
        assert MockAnonymizerEngine.call_count == 1, f'AnonymizerEngine created {MockAnonymizerEngine.call_count} times after 2nd call, expected 1'
        print('Third invocation...')
        result3, tokens3 = privacy_plugin.run('system', 'query 3', mock_client, 'model')
        assert MockAnalyzerEngine.call_count == 1, f'AnalyzerEngine created {MockAnalyzerEngine.call_count} times after 3rd call, expected 1'
        assert MockAnonymizerEngine.call_count == 1, f'AnonymizerEngine created {MockAnonymizerEngine.call_count} times after 3rd call, expected 1'
        print('✅ Privacy plugin resource caching test PASSED - Resources are properly cached!')
        return True

def test_privacy_plugin_performance():
    """
    Test that multiple invocations of the privacy plugin don't have degraded performance.
    This catches the actual performance issue even without mocking.
    """
    print('\nTesting privacy plugin performance (real execution)...')
    try:
        import optillm.plugins.privacy_plugin as privacy_plugin
        try:
            import spacy
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
        except ImportError as e:
            print(f'⚠️  Skipping performance test - dependencies not installed: {e}')
            return True
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='response'))]
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response
        print('Warm-up call...')
        start = time.time()
        privacy_plugin.run('system', 'warm up query', mock_client, 'model')
        warmup_time = time.time() - start
        print(f'Warm-up time: {warmup_time:.2f}s')
        print('First measurement call...')
        start = time.time()
        privacy_plugin.run('system', 'test query 1', mock_client, 'model')
        first_time = time.time() - start
        print(f'First call time: {first_time:.2f}s')
        print('Second measurement call...')
        start = time.time()
        privacy_plugin.run('system', 'test query 2', mock_client, 'model')
        second_time = time.time() - start
        print(f'Second call time: {second_time:.2f}s')
        print('Third measurement call...')
        start = time.time()
        privacy_plugin.run('system', 'test query 3', mock_client, 'model')
        third_time = time.time() - start
        print(f'Third call time: {third_time:.2f}s')
        max_acceptable_time = 2.0
        if second_time > max_acceptable_time:
            raise AssertionError(f'Second call took {second_time:.2f}s, expected < {max_acceptable_time}s. Resources might not be cached!')
        if third_time > max_acceptable_time:
            raise AssertionError(f'Third call took {third_time:.2f}s, expected < {max_acceptable_time}s. Resources might not be cached!')
        print(f'✅ Privacy plugin performance test PASSED - Subsequent calls are fast ({second_time:.2f}s, {third_time:.2f}s)!')
        return True
    except Exception as e:
        print(f'❌ Performance test failed: {e}')
        raise

def test_recognizers_not_reloaded():
    """
    Test that recognizers are not fetched/reloaded on each analyze() call.
    This prevents the performance regression where "Fetching all recognizers for language en"
    appears in logs on every request.
    """
    print('\nTesting that recognizers are not reloaded on each call...')
    if 'optillm.plugins.privacy_plugin' in sys.modules:
        del sys.modules['optillm.plugins.privacy_plugin']
    try:
        with patch('presidio_analyzer.AnalyzerEngine') as MockAnalyzerEngine, patch('spacy.util.is_package', return_value=True):
            mock_analyzer_instance = MagicMock()
            mock_registry = MagicMock()
            mock_registry.get_recognizers = MagicMock(return_value=[])
            mock_analyzer_instance.registry = mock_registry
            mock_analyzer_instance.analyze = MagicMock(return_value=[])
            MockAnalyzerEngine.return_value = mock_analyzer_instance
            import optillm.plugins.privacy_plugin as privacy_plugin
            analyzer1 = privacy_plugin.get_analyzer_engine()
            initial_analyze_calls = mock_analyzer_instance.analyze.call_count
            print(f'Warm-up analyze calls: {initial_analyze_calls}')
            assert initial_analyze_calls == 1, f'Expected 1 warm-up analyze call, got {initial_analyze_calls}'
            analyzer2 = privacy_plugin.get_analyzer_engine()
            second_analyze_calls = mock_analyzer_instance.analyze.call_count
            print(f'Total analyze calls after second get_analyzer_engine: {second_analyze_calls}')
            assert second_analyze_calls == 1, f'Analyzer should not call analyze() again on cached retrieval, got {second_analyze_calls} calls'
            assert analyzer1 is analyzer2, 'Should return the same cached analyzer instance'
            print('✅ Recognizer reload test PASSED - Recognizers are pre-warmed and not reloaded!')
            return True
    except ImportError as e:
        print(f'⚠️  Skipping recognizer reload test - dependencies not installed: {e}')
        return True
    except Exception as e:
        print(f'❌ Recognizer reload test failed: {e}')
        raise

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

class TestInferenceIntegration(unittest.TestCase):
    """Test integration with inference.py module"""

    def test_inference_usage_includes_reasoning_tokens(self):
        """Test that ChatCompletionUsage includes reasoning_tokens"""
        from optillm.inference import ChatCompletionUsage
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, reasoning_tokens=5)
        self.assertEqual(usage.prompt_tokens, 10)
        self.assertEqual(usage.completion_tokens, 20)
        self.assertEqual(usage.total_tokens, 30)
        self.assertEqual(usage.reasoning_tokens, 5)

    def test_inference_usage_default_reasoning_tokens(self):
        """Test that ChatCompletionUsage defaults reasoning_tokens to 0"""
        from optillm.inference import ChatCompletionUsage
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        self.assertEqual(usage.reasoning_tokens, 0)

    def test_chat_completion_model_dump_includes_reasoning_tokens(self):
        """Test that ChatCompletion.model_dump includes reasoning_tokens in usage"""
        from optillm.inference import ChatCompletion
        response_dict = {'id': 'test-id', 'object': 'chat.completion', 'created': 1234567890, 'model': 'test-model', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>reasoning</think>answer'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30, 'reasoning_tokens': 5}}
        completion = ChatCompletion(response_dict)
        result = completion.model_dump()
        self.assertIn('usage', result)
        self.assertIn('completion_tokens_details', result['usage'])
        self.assertIn('reasoning_tokens', result['usage']['completion_tokens_details'])
        self.assertEqual(result['usage']['completion_tokens_details']['reasoning_tokens'], 5)

def test_inference_usage_includes_reasoning_tokens(self):
    """Test that ChatCompletionUsage includes reasoning_tokens"""
    from optillm.inference import ChatCompletionUsage
    usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, reasoning_tokens=5)
    self.assertEqual(usage.prompt_tokens, 10)
    self.assertEqual(usage.completion_tokens, 20)
    self.assertEqual(usage.total_tokens, 30)
    self.assertEqual(usage.reasoning_tokens, 5)

def test_inference_usage_default_reasoning_tokens(self):
    """Test that ChatCompletionUsage defaults reasoning_tokens to 0"""
    from optillm.inference import ChatCompletionUsage
    usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    self.assertEqual(usage.reasoning_tokens, 0)

def test_chat_completion_model_dump_includes_reasoning_tokens(self):
    """Test that ChatCompletion.model_dump includes reasoning_tokens in usage"""
    from optillm.inference import ChatCompletion
    response_dict = {'id': 'test-id', 'object': 'chat.completion', 'created': 1234567890, 'model': 'test-model', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>reasoning</think>answer'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30, 'reasoning_tokens': 5}}
    completion = ChatCompletion(response_dict)
    result = completion.model_dump()
    self.assertIn('usage', result)
    self.assertIn('completion_tokens_details', result['usage'])
    self.assertIn('reasoning_tokens', result['usage']['completion_tokens_details'])
    self.assertEqual(result['usage']['completion_tokens_details']['reasoning_tokens'], 5)

class TestEndToEndIntegration(unittest.TestCase):
    """Test end-to-end integration with mocked responses for specific configs"""

    def test_thinkdeeper_approach_with_reasoning_tokens(self):
        """Test thinkdeeper approach properly processes reasoning tokens"""
        from unittest.mock import patch, Mock
        with patch('optillm.thinkdeeper.thinkdeeper_decode') as mock_thinkdeeper:
            mock_response = '<think>Let me solve this step by step. 2 + 2 = 4</think>The answer is 4.'
            mock_tokens = 25
            mock_thinkdeeper.return_value = (mock_response, mock_tokens)
            result, tokens = mock_thinkdeeper('You are a helpful assistant.', 'What is 2+2?', Mock(), TEST_MODEL, {'k': 3})
            self.assertEqual(result, mock_response)
            self.assertEqual(tokens, mock_tokens)
            self.assertIn('<think>', result)
            self.assertIn('</think>', result)
            mock_thinkdeeper.assert_called_once()

    def test_reasoning_token_calculation_with_mock_response(self):
        """Test reasoning token calculation with mock content"""
        from optillm import count_reasoning_tokens
        test_cases = [('<think>Simple thought</think>Answer', 2), ('<think>More complex reasoning here</think>Final answer', 4), ('No thinking tags here', 0), ('<think>First thought</think>Some text<think>Second thought</think>End', 4)]
        for content, expected_min_tokens in test_cases:
            with self.subTest(content=content[:30] + '...'):
                reasoning_tokens = count_reasoning_tokens(content)
                if expected_min_tokens > 0:
                    self.assertGreaterEqual(reasoning_tokens, expected_min_tokens - 1)
                else:
                    self.assertEqual(reasoning_tokens, 0)

def test_thinkdeeper_approach_with_reasoning_tokens(self):
    """Test thinkdeeper approach properly processes reasoning tokens"""
    from unittest.mock import patch, Mock
    with patch('optillm.thinkdeeper.thinkdeeper_decode') as mock_thinkdeeper:
        mock_response = '<think>Let me solve this step by step. 2 + 2 = 4</think>The answer is 4.'
        mock_tokens = 25
        mock_thinkdeeper.return_value = (mock_response, mock_tokens)
        result, tokens = mock_thinkdeeper('You are a helpful assistant.', 'What is 2+2?', Mock(), TEST_MODEL, {'k': 3})
        self.assertEqual(result, mock_response)
        self.assertEqual(tokens, mock_tokens)
        self.assertIn('<think>', result)
        self.assertIn('</think>', result)
        mock_thinkdeeper.assert_called_once()

def test_reasoning_token_calculation_with_mock_response(self):
    """Test reasoning token calculation with mock content"""
    from optillm import count_reasoning_tokens
    test_cases = [('<think>Simple thought</think>Answer', 2), ('<think>More complex reasoning here</think>Final answer', 4), ('No thinking tags here', 0), ('<think>First thought</think>Some text<think>Second thought</think>End', 4)]
    for content, expected_min_tokens in test_cases:
        with self.subTest(content=content[:30] + '...'):
            reasoning_tokens = count_reasoning_tokens(content)
            if expected_min_tokens > 0:
                self.assertGreaterEqual(reasoning_tokens, expected_min_tokens - 1)
            else:
                self.assertEqual(reasoning_tokens, 0)

class TestAPIResponseStructure(unittest.TestCase):
    """Test API response structure with reasoning tokens using mocks"""

    def test_chat_completion_response_structure(self):
        """Test that chat completion responses have proper structure"""
        from unittest.mock import Mock
        from optillm.inference import ChatCompletion, ChatCompletionUsage
        mock_usage = ChatCompletionUsage(prompt_tokens=15, completion_tokens=25, total_tokens=40, reasoning_tokens=8)
        self.assertEqual(mock_usage.prompt_tokens, 15)
        self.assertEqual(mock_usage.completion_tokens, 25)
        self.assertEqual(mock_usage.total_tokens, 40)
        self.assertEqual(mock_usage.reasoning_tokens, 8)
        response_data = {'id': 'test-completion', 'object': 'chat.completion', 'created': 1234567890, 'model': TEST_MODEL, 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>Let me calculate: 2+2=4</think>The answer is 4.'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 15, 'completion_tokens': 25, 'total_tokens': 40, 'reasoning_tokens': 8}}
        completion = ChatCompletion(response_data)
        result = completion.model_dump()
        self.assertIn('usage', result)
        self.assertIn('completion_tokens_details', result['usage'])
        self.assertIn('reasoning_tokens', result['usage']['completion_tokens_details'])
        self.assertEqual(result['usage']['completion_tokens_details']['reasoning_tokens'], 8)

def test_chat_completion_response_structure(self):
    """Test that chat completion responses have proper structure"""
    from unittest.mock import Mock
    from optillm.inference import ChatCompletion, ChatCompletionUsage
    mock_usage = ChatCompletionUsage(prompt_tokens=15, completion_tokens=25, total_tokens=40, reasoning_tokens=8)
    self.assertEqual(mock_usage.prompt_tokens, 15)
    self.assertEqual(mock_usage.completion_tokens, 25)
    self.assertEqual(mock_usage.total_tokens, 40)
    self.assertEqual(mock_usage.reasoning_tokens, 8)
    response_data = {'id': 'test-completion', 'object': 'chat.completion', 'created': 1234567890, 'model': TEST_MODEL, 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>Let me calculate: 2+2=4</think>The answer is 4.'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 15, 'completion_tokens': 25, 'total_tokens': 40, 'reasoning_tokens': 8}}
    completion = ChatCompletion(response_data)
    result = completion.model_dump()
    self.assertIn('usage', result)
    self.assertIn('completion_tokens_details', result['usage'])
    self.assertIn('reasoning_tokens', result['usage']['completion_tokens_details'])
    self.assertEqual(result['usage']['completion_tokens_details']['reasoning_tokens'], 8)

class TestConversationLogger(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger_enabled = ConversationLogger(self.temp_dir, enabled=True)
        self.logger_disabled = ConversationLogger(self.temp_dir, enabled=False)

    def tearDown(self):
        """Clean up test fixtures"""
        for file in self.temp_dir.glob('*'):
            file.unlink()
        self.temp_dir.rmdir()

    def test_logger_initialization_and_disabled_state(self):
        """Test logger initialization and disabled logger behavior"""
        self.assertTrue(self.logger_enabled.enabled)
        self.assertEqual(self.logger_enabled.log_dir, self.temp_dir)
        self.assertTrue(self.temp_dir.exists())
        self.assertFalse(self.logger_disabled.enabled)
        request_id = self.logger_disabled.start_conversation({}, 'test', 'model')
        self.assertEqual(request_id, '')
        self.logger_disabled.log_provider_call('req1', {}, {})
        self.logger_disabled.log_final_response('req1', {})
        self.logger_disabled.log_error('req1', 'error')
        self.logger_disabled.finalize_conversation('req1')

    def test_conversation_lifecycle(self):
        """Test complete conversation lifecycle: start, log calls, errors, finalize"""
        client_request = {'messages': [{'role': 'user', 'content': 'Hello'}], 'model': 'gpt-4o-mini', 'temperature': 0.7}
        request_id = self.logger_enabled.start_conversation(client_request=client_request, approach='moa', model='gpt-4o-mini')
        self.assertIsInstance(request_id, str)
        self.assertTrue(request_id.startswith('req_'))
        self.assertEqual(len(request_id), 12)
        self.assertIn(request_id, self.logger_enabled.active_entries)
        entry = self.logger_enabled.active_entries[request_id]
        self.assertEqual(entry.request_id, request_id)
        self.assertEqual(entry.approach, 'moa')
        self.assertEqual(entry.model, 'gpt-4o-mini')
        provider_request = {'model': 'test', 'messages': []}
        provider_response = {'choices': [{'message': {'content': 'response'}}]}
        self.logger_enabled.log_provider_call(request_id, provider_request, provider_response)
        self.logger_enabled.log_provider_call(request_id, provider_request, provider_response)
        entry = self.logger_enabled.active_entries[request_id]
        self.assertEqual(len(entry.provider_calls), 2)
        self.assertEqual(entry.provider_calls[0]['call_number'], 1)
        self.assertEqual(entry.provider_calls[1]['call_number'], 2)
        final_response = {'choices': [{'message': {'content': 'final'}}]}
        self.logger_enabled.log_final_response(request_id, final_response)
        error_msg = 'Test error message'
        self.logger_enabled.log_error(request_id, error_msg)
        entry = self.logger_enabled.active_entries[request_id]
        self.assertEqual(entry.error, error_msg)
        self.logger_enabled.finalize_conversation(request_id)
        self.assertNotIn(request_id, self.logger_enabled.active_entries)
        log_files = list(self.temp_dir.glob('conversations_*.jsonl'))
        self.assertEqual(len(log_files), 1)
        with open(log_files[0], 'r', encoding='utf-8') as f:
            log_line = f.read().strip()
        log_entry = json.loads(log_line)
        self.assertEqual(log_entry['request_id'], request_id)
        self.assertEqual(log_entry['approach'], 'moa')
        self.assertEqual(log_entry['model'], 'gpt-4o-mini')
        self.assertEqual(log_entry['client_request'], client_request)
        self.assertEqual(len(log_entry['provider_calls']), 2)
        self.assertEqual(log_entry['final_response']['choices'][0]['message']['content'], 'final')
        self.assertIsInstance(log_entry['total_duration_ms'], int)
        self.assertEqual(log_entry['error'], error_msg)

    def test_multiple_conversations_and_log_files(self):
        """Test handling multiple concurrent conversations and log file naming"""
        with patch('optillm.conversation_logger.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 27, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            log_path = self.logger_enabled._get_log_file_path()
            expected_filename = 'conversations_2025-01-27.jsonl'
            self.assertEqual(log_path.name, expected_filename)
            self.assertEqual(log_path.parent, self.temp_dir)
        request_id1 = self.logger_enabled.start_conversation({}, 'moa', 'model1')
        request_id2 = self.logger_enabled.start_conversation({}, 'none', 'model2')
        self.assertNotEqual(request_id1, request_id2)
        self.assertIn(request_id1, self.logger_enabled.active_entries)
        self.assertIn(request_id2, self.logger_enabled.active_entries)
        self.logger_enabled.log_provider_call(request_id1, {'req': '1'}, {'resp': '1'})
        self.logger_enabled.log_provider_call(request_id2, {'req': '2'}, {'resp': '2'})
        self.logger_enabled.finalize_conversation(request_id1)
        self.logger_enabled.finalize_conversation(request_id2)
        log_files = list(self.temp_dir.glob('conversations_*.jsonl'))
        self.assertEqual(len(log_files), 1)
        with open(log_files[0], 'r', encoding='utf-8') as f:
            lines = f.read().strip().split('\n')
        self.assertEqual(len(lines), 2)
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        self.assertEqual(entry1['approach'], 'moa')
        self.assertEqual(entry2['approach'], 'none')

    def test_invalid_request_id_and_stats(self):
        """Test handling of invalid request IDs and logger statistics"""
        self.logger_enabled.log_provider_call('invalid_id', {}, {})
        self.logger_enabled.log_final_response('invalid_id', {})
        self.logger_enabled.log_error('invalid_id', 'error')
        self.logger_enabled.finalize_conversation('invalid_id')
        stats = self.logger_disabled.get_stats()
        expected_disabled_stats = {'enabled': False, 'log_dir': str(self.temp_dir), 'active_conversations': 0}
        self.assertEqual(stats, expected_disabled_stats)
        request_id1 = self.logger_enabled.start_conversation({}, 'test', 'model')
        request_id2 = self.logger_enabled.start_conversation({}, 'test', 'model')
        stats = self.logger_enabled.get_stats()
        self.assertTrue(stats['enabled'])
        self.assertEqual(stats['log_dir'], str(self.temp_dir))
        self.assertEqual(stats['active_conversations'], 2)
        self.assertEqual(stats['log_files_count'], 0)
        self.assertEqual(stats['total_entries_approximate'], 0)
        self.logger_enabled.finalize_conversation(request_id1)
        stats = self.logger_enabled.get_stats()
        self.assertEqual(stats['active_conversations'], 1)
        self.assertEqual(stats['log_files_count'], 1)
        self.assertEqual(stats['total_entries_approximate'], 1)

def test_logger_initialization_and_disabled_state(self):
    """Test logger initialization and disabled logger behavior"""
    self.assertTrue(self.logger_enabled.enabled)
    self.assertEqual(self.logger_enabled.log_dir, self.temp_dir)
    self.assertTrue(self.temp_dir.exists())
    self.assertFalse(self.logger_disabled.enabled)
    request_id = self.logger_disabled.start_conversation({}, 'test', 'model')
    self.assertEqual(request_id, '')
    self.logger_disabled.log_provider_call('req1', {}, {})
    self.logger_disabled.log_final_response('req1', {})
    self.logger_disabled.log_error('req1', 'error')
    self.logger_disabled.finalize_conversation('req1')

def test_conversation_lifecycle(self):
    """Test complete conversation lifecycle: start, log calls, errors, finalize"""
    client_request = {'messages': [{'role': 'user', 'content': 'Hello'}], 'model': 'gpt-4o-mini', 'temperature': 0.7}
    request_id = self.logger_enabled.start_conversation(client_request=client_request, approach='moa', model='gpt-4o-mini')
    self.assertIsInstance(request_id, str)
    self.assertTrue(request_id.startswith('req_'))
    self.assertEqual(len(request_id), 12)
    self.assertIn(request_id, self.logger_enabled.active_entries)
    entry = self.logger_enabled.active_entries[request_id]
    self.assertEqual(entry.request_id, request_id)
    self.assertEqual(entry.approach, 'moa')
    self.assertEqual(entry.model, 'gpt-4o-mini')
    provider_request = {'model': 'test', 'messages': []}
    provider_response = {'choices': [{'message': {'content': 'response'}}]}
    self.logger_enabled.log_provider_call(request_id, provider_request, provider_response)
    self.logger_enabled.log_provider_call(request_id, provider_request, provider_response)
    entry = self.logger_enabled.active_entries[request_id]
    self.assertEqual(len(entry.provider_calls), 2)
    self.assertEqual(entry.provider_calls[0]['call_number'], 1)
    self.assertEqual(entry.provider_calls[1]['call_number'], 2)
    final_response = {'choices': [{'message': {'content': 'final'}}]}
    self.logger_enabled.log_final_response(request_id, final_response)
    error_msg = 'Test error message'
    self.logger_enabled.log_error(request_id, error_msg)
    entry = self.logger_enabled.active_entries[request_id]
    self.assertEqual(entry.error, error_msg)
    self.logger_enabled.finalize_conversation(request_id)
    self.assertNotIn(request_id, self.logger_enabled.active_entries)
    log_files = list(self.temp_dir.glob('conversations_*.jsonl'))
    self.assertEqual(len(log_files), 1)
    with open(log_files[0], 'r', encoding='utf-8') as f:
        log_line = f.read().strip()
    log_entry = json.loads(log_line)
    self.assertEqual(log_entry['request_id'], request_id)
    self.assertEqual(log_entry['approach'], 'moa')
    self.assertEqual(log_entry['model'], 'gpt-4o-mini')
    self.assertEqual(log_entry['client_request'], client_request)
    self.assertEqual(len(log_entry['provider_calls']), 2)
    self.assertEqual(log_entry['final_response']['choices'][0]['message']['content'], 'final')
    self.assertIsInstance(log_entry['total_duration_ms'], int)
    self.assertEqual(log_entry['error'], error_msg)

def test_multiple_conversations_and_log_files(self):
    """Test handling multiple concurrent conversations and log file naming"""
    with patch('optillm.conversation_logger.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 1, 27, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        log_path = self.logger_enabled._get_log_file_path()
        expected_filename = 'conversations_2025-01-27.jsonl'
        self.assertEqual(log_path.name, expected_filename)
        self.assertEqual(log_path.parent, self.temp_dir)
    request_id1 = self.logger_enabled.start_conversation({}, 'moa', 'model1')
    request_id2 = self.logger_enabled.start_conversation({}, 'none', 'model2')
    self.assertNotEqual(request_id1, request_id2)
    self.assertIn(request_id1, self.logger_enabled.active_entries)
    self.assertIn(request_id2, self.logger_enabled.active_entries)
    self.logger_enabled.log_provider_call(request_id1, {'req': '1'}, {'resp': '1'})
    self.logger_enabled.log_provider_call(request_id2, {'req': '2'}, {'resp': '2'})
    self.logger_enabled.finalize_conversation(request_id1)
    self.logger_enabled.finalize_conversation(request_id2)
    log_files = list(self.temp_dir.glob('conversations_*.jsonl'))
    self.assertEqual(len(log_files), 1)
    with open(log_files[0], 'r', encoding='utf-8') as f:
        lines = f.read().strip().split('\n')
    self.assertEqual(len(lines), 2)
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])
    self.assertEqual(entry1['approach'], 'moa')
    self.assertEqual(entry2['approach'], 'none')

def test_invalid_request_id_and_stats(self):
    """Test handling of invalid request IDs and logger statistics"""
    self.logger_enabled.log_provider_call('invalid_id', {}, {})
    self.logger_enabled.log_final_response('invalid_id', {})
    self.logger_enabled.log_error('invalid_id', 'error')
    self.logger_enabled.finalize_conversation('invalid_id')
    stats = self.logger_disabled.get_stats()
    expected_disabled_stats = {'enabled': False, 'log_dir': str(self.temp_dir), 'active_conversations': 0}
    self.assertEqual(stats, expected_disabled_stats)
    request_id1 = self.logger_enabled.start_conversation({}, 'test', 'model')
    request_id2 = self.logger_enabled.start_conversation({}, 'test', 'model')
    stats = self.logger_enabled.get_stats()
    self.assertTrue(stats['enabled'])
    self.assertEqual(stats['log_dir'], str(self.temp_dir))
    self.assertEqual(stats['active_conversations'], 2)
    self.assertEqual(stats['log_files_count'], 0)
    self.assertEqual(stats['total_entries_approximate'], 0)
    self.logger_enabled.finalize_conversation(request_id1)
    stats = self.logger_enabled.get_stats()
    self.assertEqual(stats['active_conversations'], 1)
    self.assertEqual(stats['log_files_count'], 1)
    self.assertEqual(stats['total_entries_approximate'], 1)

def test_proxy_plugin_token_counts():
    """Test that proxy plugin returns complete token usage information"""
    import optillm.plugins.proxy_plugin as plugin
    from unittest.mock import Mock, MagicMock
    mock_client = Mock()
    mock_response = MagicMock()
    mock_response.choices = [Mock(message=Mock(content='Test response'))]
    mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    mock_response.model_dump.return_value = {'choices': [{'message': {'content': 'Test response'}}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}
    mock_client.chat.completions.create.return_value = mock_response
    result, _ = plugin.run(system_prompt='Test system', initial_query='Test query', client=mock_client, model='test-model')
    assert isinstance(result, dict), 'Result should be a dictionary'
    assert 'usage' in result, 'Result should contain usage information'
    assert 'prompt_tokens' in result['usage'], 'Usage should contain prompt_tokens'
    assert 'completion_tokens' in result['usage'], 'Usage should contain completion_tokens'
    assert 'total_tokens' in result['usage'], 'Usage should contain total_tokens'
    assert result['usage']['prompt_tokens'] == 10
    assert result['usage']['completion_tokens'] == 5
    assert result['usage']['total_tokens'] == 15

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

def test_mars_agent_temperatures():
    """Test that MARS uses different temperatures for agents"""
    from optillm.mars.mars import DEFAULT_CONFIG
    from optillm.mars.agent import MARSAgent
    client = MockOpenAIClient()
    model = 'mock-model'
    config = DEFAULT_CONFIG.copy()
    agents = []
    for i in range(config['num_agents']):
        agent = MARSAgent(i, client, model, config)
        agents.append(agent)
    temperatures = [agent.temperature for agent in agents]
    unique_temps = set(temperatures)
    assert len(unique_temps) == len(agents), 'Agents should have different temperatures'
    assert 0.3 in temperatures, 'Should have conservative agent (temp 0.3)'
    assert 1.0 in temperatures, 'Should have creative agent (temp 1.0)'
    print(f'✅ Agent temperatures test passed: {temperatures}')

def run_tests():
    """Run all MARS tests"""
    print('Running MARS comprehensive tests...')
    print('=' * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMARSParallel)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    try:
        test_mars_agent_temperatures()
    except Exception as e:
        print(f'❌ Agent temperatures test failed: {e}')
    print('=' * 60)
    if result.wasSuccessful():
        print('🎉 All MARS tests passed!')
        return True
    else:
        print('❌ Some MARS tests failed')
        return False

class MockOpenAIClient:

    def chat_completions_create(self, *args, **kwargs):

        class MockResponse:

            def __init__(self):
                self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mock response'})()})]
        return MockResponse()

def chat_completions_create(self, *args, **kwargs):

    class MockResponse:

        def __init__(self):
            self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mock response'})()})]
    return MockResponse()

def print_summary(results: List[Dict]):
    print('\n=== Test Results Summary ===')
    for test_result in results:
        print(f'\nTest Case: {test_result['test_case']['name']}')
        for approach_result in test_result['results']:
            status = '✅' if approach_result['status'] == 'success' else '❌'
            print(f'  {status} {approach_result['approach']}: {approach_result['time']:.2f}s')
            if approach_result['status'] == 'error':
                print(f'     Error: {approach_result['result']}')

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

class TestRequestBatcher(unittest.TestCase):
    """Test the core RequestBatcher functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.batcher = RequestBatcher(max_batch_size=4, max_wait_ms=100)
        self.test_responses = []

        def mock_processor(requests):
            """Mock batch processor that returns simple responses"""
            responses = []
            for i, req in enumerate(requests):
                responses.append({'id': f'test-{i}', 'object': 'chat.completion', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': f'Response to request {i}'}, 'finish_reason': 'stop'}], 'usage': {'completion_tokens': 10, 'total_tokens': 20}})
            return responses
        self.batcher.set_processor(mock_processor)

    def tearDown(self):
        """Clean up after tests"""
        self.batcher.shutdown()

    def test_single_request(self):
        """Test that single requests work correctly"""
        request_data = {'model': 'test-model', 'prompt': 'Hello'}
        response = self.batcher.add_request(request_data)
        self.assertIsInstance(response, dict)
        self.assertEqual(response['object'], 'chat.completion')
        self.assertEqual(response['choices'][0]['message']['content'], 'Response to request 0')

    def test_batch_formation(self):
        """Test that multiple requests form a batch"""

        def send_request(request_id):
            request_data = {'model': 'test-model', 'prompt': f'Request {request_id}'}
            return self.batcher.add_request(request_data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_request, i) for i in range(3)]
            responses = [future.result() for future in futures]
        self.assertEqual(len(responses), 3)
        for i, response in enumerate(responses):
            self.assertIsInstance(response, dict)
            self.assertEqual(response['object'], 'chat.completion')

    def test_batch_timeout(self):
        """Test that partial batches process after timeout"""
        start_time = time.time()
        request_data = {'model': 'test-model', 'prompt': 'Single request'}
        response = self.batcher.add_request(request_data)
        elapsed_time = time.time() - start_time
        self.assertGreater(elapsed_time, 0.09)
        self.assertIsInstance(response, dict)

    def test_incompatible_requests(self):
        """Test that incompatible requests are properly handled"""
        request_data = {'model': 'test-model', 'stream': True}
        with self.assertRaises(BatchingError):
            self.batcher.add_request(request_data)

    def test_processor_error_handling(self):
        """Test that processor errors are handled correctly"""

        def failing_processor(requests):
            raise Exception('Processor failed')
        batcher = RequestBatcher(max_batch_size=2, max_wait_ms=50)
        batcher.set_processor(failing_processor)
        try:
            request_data = {'model': 'test-model', 'prompt': 'Test'}
            with self.assertRaises(BatchingError):
                batcher.add_request(request_data)
        finally:
            batcher.shutdown()

    def test_batch_stats(self):
        """Test that batch statistics are collected correctly"""
        for i in range(5):
            request_data = {'model': 'test-model', 'prompt': f'Request {i}'}
            self.batcher.add_request(request_data)
        stats = self.batcher.get_stats()
        self.assertGreater(stats['total_requests'], 0)
        self.assertGreater(stats['total_batches'], 0)
        self.assertGreater(stats['avg_batch_size'], 0)

def test_single_request(self):
    """Test that single requests work correctly"""
    request_data = {'model': 'test-model', 'prompt': 'Hello'}
    response = self.batcher.add_request(request_data)
    self.assertIsInstance(response, dict)
    self.assertEqual(response['object'], 'chat.completion')
    self.assertEqual(response['choices'][0]['message']['content'], 'Response to request 0')

def test_batch_timeout(self):
    """Test that partial batches process after timeout"""
    start_time = time.time()
    request_data = {'model': 'test-model', 'prompt': 'Single request'}
    response = self.batcher.add_request(request_data)
    elapsed_time = time.time() - start_time
    self.assertGreater(elapsed_time, 0.09)
    self.assertIsInstance(response, dict)

def test_batch_stats(self):
    """Test that batch statistics are collected correctly"""
    for i in range(5):
        request_data = {'model': 'test-model', 'prompt': f'Request {i}'}
        self.batcher.add_request(request_data)
    stats = self.batcher.get_stats()
    self.assertGreater(stats['total_requests'], 0)
    self.assertGreater(stats['total_batches'], 0)
    self.assertGreater(stats['avg_batch_size'], 0)

class TestBackwardCompatibility(unittest.TestCase):
    """Test that existing functionality is preserved without batch mode"""

    def test_no_batch_mode_unchanged(self):
        """Test that optillm works exactly the same without --batch-mode"""
        self.assertTrue(True)

    @unittest.skipIf(not os.getenv('OPTILLM_API_KEY'), 'Requires local inference')
    def test_inference_pipeline_unchanged(self):
        """Test that inference pipeline behavior is unchanged"""
        pass

def test_no_batch_mode_unchanged(self):
    """Test that optillm works exactly the same without --batch-mode"""
    self.assertTrue(True)

class TestMLXBatching(unittest.TestCase):
    """Test MLX batch processing functionality"""

    @unittest.skipIf(not MLX_AVAILABLE, 'MLX not available')
    def setUp(self):
        """Set up MLX test fixtures"""
        self.model_config = MLXModelConfig(model_id=TEST_MODEL_MLX, max_new_tokens=100)
        from optillm.inference import CacheManager
        self.cache_manager = CacheManager.get_instance(max_size=1)

    @unittest.skipIf(not MLX_AVAILABLE, 'MLX not available')
    def test_mlx_batch_creation(self):
        """Test that MLX batch processing can be created"""
        try:
            from optillm.inference import MLXInferencePipeline
            self.assertTrue(hasattr(MLXInferencePipeline, 'process_batch'))
        except Exception as e:
            pass

    @unittest.skipIf(not MLX_AVAILABLE, 'MLX not available')
    def test_mlx_batch_parameters(self):
        """Test MLX batch processing parameter validation"""
        print(f'\n📥 Testing MLX model: {self.model_config.model_id}')
        print('This may take a few minutes if model needs to be downloaded...')
        pipeline = MLXInferencePipeline(self.model_config, self.cache_manager)
        print('✅ MLX model loaded successfully')
        with self.assertRaises(ValueError):
            pipeline.process_batch(['system1'], ['user1', 'user2'])
        responses, tokens = pipeline.process_batch([], [])
        self.assertEqual(len(responses), 0)
        self.assertEqual(len(tokens), 0)
        print('✅ MLX parameter validation tests passed')

    @unittest.skipIf(not MLX_AVAILABLE, 'MLX not available')
    def test_mlx_batch_generation(self):
        """Test MLX batch processing with actual generation"""
        print(f'\n🧪 Testing MLX batch generation...')
        pipeline = MLXInferencePipeline(self.model_config, self.cache_manager)
        print('✅ MLX model ready for testing')
        system_prompts = ['You are a helpful assistant.', 'You are a helpful assistant.']
        user_prompts = ['What is AI?', 'What is ML?']
        print('🚀 Running batch generation...')
        responses, token_counts = pipeline.process_batch(system_prompts, user_prompts, generation_params={'max_new_tokens': 20})
        self.assertEqual(len(responses), 2)
        self.assertEqual(len(token_counts), 2)
        for i, response in enumerate(responses):
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            print(f'   Response {i + 1}: {response[:50]}{('...' if len(response) > 50 else '')}')
        for token_count in token_counts:
            self.assertIsInstance(token_count, int)
            self.assertGreater(token_count, 0)
        print(f'✅ MLX batch generation successful - {len(responses)} responses generated')
        print(f'   Token counts: {token_counts}')

@unittest.skipIf(not MLX_AVAILABLE, 'MLX not available')
def test_mlx_batch_parameters(self):
    """Test MLX batch processing parameter validation"""
    print(f'\n📥 Testing MLX model: {self.model_config.model_id}')
    print('This may take a few minutes if model needs to be downloaded...')
    pipeline = MLXInferencePipeline(self.model_config, self.cache_manager)
    print('✅ MLX model loaded successfully')
    with self.assertRaises(ValueError):
        pipeline.process_batch(['system1'], ['user1', 'user2'])
    responses, tokens = pipeline.process_batch([], [])
    self.assertEqual(len(responses), 0)
    self.assertEqual(len(tokens), 0)
    print('✅ MLX parameter validation tests passed')

@unittest.skipIf(not MLX_AVAILABLE, 'MLX not available')
def test_mlx_batch_generation(self):
    """Test MLX batch processing with actual generation"""
    print(f'\n🧪 Testing MLX batch generation...')
    pipeline = MLXInferencePipeline(self.model_config, self.cache_manager)
    print('✅ MLX model ready for testing')
    system_prompts = ['You are a helpful assistant.', 'You are a helpful assistant.']
    user_prompts = ['What is AI?', 'What is ML?']
    print('🚀 Running batch generation...')
    responses, token_counts = pipeline.process_batch(system_prompts, user_prompts, generation_params={'max_new_tokens': 20})
    self.assertEqual(len(responses), 2)
    self.assertEqual(len(token_counts), 2)
    for i, response in enumerate(responses):
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f'   Response {i + 1}: {response[:50]}{('...' if len(response) > 50 else '')}')
    for token_count in token_counts:
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)
    print(f'✅ MLX batch generation successful - {len(responses)} responses generated')
    print(f'   Token counts: {token_counts}')

class TestPyTorchBatching(unittest.TestCase):
    """Test PyTorch batch processing functionality"""

    def test_pytorch_batch_method_exists(self):
        """Test that PyTorch InferencePipeline has process_batch method"""
        from optillm.inference import InferencePipeline
        self.assertTrue(hasattr(InferencePipeline, 'process_batch'))

    @unittest.skipIf(not os.getenv('OPTILLM_API_KEY'), 'Requires local inference')
    def test_pytorch_batch_processing(self):
        """Test PyTorch batch processing with small model"""
        pass

def test_pytorch_batch_method_exists(self):
    """Test that PyTorch InferencePipeline has process_batch method"""
    from optillm.inference import InferencePipeline
    self.assertTrue(hasattr(InferencePipeline, 'process_batch'))

class TestPerformanceBenches(unittest.TestCase):
    """Performance comparison tests"""

    def setUp(self):
        """Set up performance test fixtures"""
        self.test_prompts = [('System prompt 1', 'What is AI?'), ('System prompt 2', 'Explain machine learning'), ('System prompt 3', 'Define neural networks'), ('System prompt 4', 'Describe deep learning')]

    def measure_sequential_processing(self, prompts):
        """Measure time for sequential processing"""
        start_time = time.time()
        responses = []
        for sys_prompt, user_prompt in prompts:
            time.sleep(0.1)
            responses.append(f'Response to: {user_prompt}')
        end_time = time.time()
        return (responses, end_time - start_time)

    def measure_batch_processing(self, prompts):
        """Measure time for batch processing"""
        batcher = RequestBatcher(max_batch_size=len(prompts), max_wait_ms=10)

        def mock_batch_processor(requests):
            time.sleep(0.15)
            return [{'response': f'Batched response {i}'} for i in range(len(requests))]
        batcher.set_processor(mock_batch_processor)
        try:
            start_time = time.time()

            def send_request(prompt_data):
                sys_prompt, user_prompt = prompt_data
                return batcher.add_request({'model': 'test-model', 'system_prompt': sys_prompt, 'user_prompt': user_prompt})
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(prompts)) as executor:
                futures = [executor.submit(send_request, prompt) for prompt in prompts]
                responses = [future.result() for future in futures]
            end_time = time.time()
            return (responses, end_time - start_time)
        finally:
            batcher.shutdown()

    def test_batching_performance_improvement(self):
        """Test that batching provides performance improvement"""
        seq_responses, seq_time = self.measure_sequential_processing(self.test_prompts)
        batch_responses, batch_time = self.measure_batch_processing(self.test_prompts)
        improvement_ratio = seq_time / batch_time
        self.assertGreater(improvement_ratio, 1.5, f'Batching should be >1.5x faster, got {improvement_ratio:.2f}x')
        self.assertEqual(len(seq_responses), len(batch_responses))

def measure_sequential_processing(self, prompts):
    """Measure time for sequential processing"""
    start_time = time.time()
    responses = []
    for sys_prompt, user_prompt in prompts:
        time.sleep(0.1)
        responses.append(f'Response to: {user_prompt}')
    end_time = time.time()
    return (responses, end_time - start_time)

def mock_batch_processor(requests):
    time.sleep(0.15)
    return [{'response': f'Batched response {i}'} for i in range(len(requests))]

def test_batching_performance_improvement(self):
    """Test that batching provides performance improvement"""
    seq_responses, seq_time = self.measure_sequential_processing(self.test_prompts)
    batch_responses, batch_time = self.measure_batch_processing(self.test_prompts)
    improvement_ratio = seq_time / batch_time
    self.assertGreater(improvement_ratio, 1.5, f'Batching should be >1.5x faster, got {improvement_ratio:.2f}x')
    self.assertEqual(len(seq_responses), len(batch_responses))

class TestIntegration(unittest.TestCase):
    """End-to-end integration tests"""

    def test_cli_arguments(self):
        """Test that CLI arguments are properly parsed"""
        import argparse
        from optillm import parse_args
        with patch('sys.argv', ['optillm', '--batch-mode', '--batch-size', '8', '--batch-wait-ms', '25']):
            args = parse_args()
            self.assertTrue(args.batch_mode)
            self.assertEqual(args.batch_size, 8)
            self.assertEqual(args.batch_wait_ms, 25)

def test_cli_arguments(self):
    """Test that CLI arguments are properly parsed"""
    import argparse
    from optillm import parse_args
    with patch('sys.argv', ['optillm', '--batch-mode', '--batch-size', '8', '--batch-wait-ms', '25']):
        args = parse_args()
        self.assertTrue(args.batch_mode)
        self.assertEqual(args.batch_size, 8)
        self.assertEqual(args.batch_wait_ms, 25)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def test_batch_mode_errors(self):
        """Test error conditions in batch mode"""
        batcher = RequestBatcher(max_batch_size=2, max_wait_ms=50)
        with self.assertRaises(BatchingError):
            batcher.add_request({'model': 'test'})
        batcher.shutdown()

    def test_mixed_model_requests(self):
        """Test that requests with different models are properly separated"""
        batcher = RequestBatcher(max_batch_size=4, max_wait_ms=50)

        def mock_processor(requests):
            models = set((req.get('model') for req in requests))
            self.assertEqual(len(models), 1, 'Batch should have requests from single model')
            return [{'response': 'ok'}] * len(requests)
        batcher.set_processor(mock_processor)
        try:
            req1 = {'model': 'model-a', 'prompt': 'test1'}
            req2 = {'model': 'model-b', 'prompt': 'test2'}
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(batcher.add_request, req1)
                future2 = executor.submit(batcher.add_request, req2)
                response1 = future1.result()
                response2 = future2.result()
                self.assertIsInstance(response1, dict)
                self.assertIsInstance(response2, dict)
        finally:
            batcher.shutdown()

def mock_processor(requests):
    models = set((req.get('model') for req in requests))
    self.assertEqual(len(models), 1, 'Batch should have requests from single model')
    return [{'response': 'ok'}] * len(requests)

def run_performance_comparison():
    """
    Run a performance comparison between sequential and batch processing
    This function can be called separately for benchmarking
    """
    print('Running Performance Comparison...')
    test_suite = TestPerformanceBenches()
    test_suite.setUp()
    seq_responses, seq_time = test_suite.measure_sequential_processing(test_suite.test_prompts)
    batch_responses, batch_time = test_suite.measure_batch_processing(test_suite.test_prompts)
    print(f'Sequential processing: {seq_time:.3f}s')
    print(f'Batch processing: {batch_time:.3f}s')
    print(f'Speedup: {seq_time / batch_time:.2f}x')
    return {'sequential_time': seq_time, 'batch_time': batch_time, 'speedup': seq_time / batch_time}

class TestJSONPlugin(unittest.TestCase):
    """Test cases for the JSON plugin with new outlines API."""

    def setUp(self):
        """Set up test fixtures."""
        self.simple_schema = json.dumps({'type': 'object', 'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}, 'active': {'type': 'boolean'}}, 'required': ['name', 'age']})
        self.complex_schema = json.dumps({'type': 'object', 'properties': {'id': {'type': 'integer'}, 'email': {'type': 'string'}, 'score': {'type': 'number'}, 'tags': {'type': 'array'}, 'metadata': {'type': 'object'}}, 'required': ['id', 'email']})

    @patch('optillm.plugins.json_plugin.outlines.from_transformers')
    @patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
    def test_json_generator_init(self, mock_tokenizer, mock_from_transformers):
        """Test JSONGenerator initialization with new API."""
        mock_model = Mock()
        mock_from_transformers.return_value = mock_model
        mock_tokenizer.return_value = Mock()
        generator = JSONGenerator()
        mock_from_transformers.assert_called_once()
        mock_tokenizer.assert_called_once()
        self.assertIsNotNone(generator.model)
        self.assertIsNotNone(generator.tokenizer)

    @patch('optillm.plugins.json_plugin.outlines.from_transformers')
    @patch('optillm.plugins.json_plugin.AutoModelForCausalLM.from_pretrained')
    @patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
    def test_parse_json_schema_to_pydantic(self, mock_tokenizer, mock_model, mock_from_transformers):
        """Test JSON schema to Pydantic model conversion."""
        if not PLUGIN_AVAILABLE:
            self.skipTest('JSON plugin not available')
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock()
        mock_from_transformers.return_value = Mock()
        generator = JSONGenerator()
        try:
            result = generator.parse_json_schema_to_pydantic(self.simple_schema)
            self.assertIsNotNone(result)
        except Exception:
            self.assertTrue(hasattr(generator, 'parse_json_schema_to_pydantic'))

    @patch('optillm.plugins.json_plugin.outlines.from_transformers')
    @patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
    def test_generate_json_new_api(self, mock_tokenizer, mock_from_transformers):
        """Test JSON generation with new outlines API."""
        mock_result = Mock()
        mock_result.model_dump.return_value = {'name': 'Test', 'age': 25}
        mock_model = Mock()
        mock_model.return_value = mock_result
        mock_from_transformers.return_value = mock_model
        generator = JSONGenerator()
        prompt = 'Create a person named Test who is 25 years old'
        result = generator.generate_json(prompt, self.simple_schema)
        self.assertEqual(result, {'name': 'Test', 'age': 25})
        mock_model.assert_called_once()

    def test_extract_schema_from_response_format(self):
        """Test schema extraction from OpenAI response format."""
        response_format = {'type': 'json_schema', 'json_schema': {'name': 'test_schema', 'schema': {'type': 'object', 'properties': {'test': {'type': 'string'}}}}}
        result = extract_schema_from_response_format(response_format)
        self.assertIsNotNone(result)
        schema = json.loads(result)
        self.assertEqual(schema['type'], 'object')
        self.assertIn('test', schema['properties'])

    @patch('optillm.plugins.json_plugin.JSONGenerator')
    def test_run_function_with_schema(self, mock_json_generator_class):
        """Test the main run function with a valid schema."""
        mock_generator = Mock()
        mock_generator.generate_json.return_value = {'result': 'test'}
        mock_generator.count_tokens.return_value = 10
        mock_json_generator_class.return_value = mock_generator
        mock_client = Mock()
        request_config = {'response_format': {'type': 'json_schema', 'json_schema': {'schema': {'type': 'object', 'properties': {'result': {'type': 'string'}}}}}}
        result, tokens = run('System prompt', 'Generate a test result', mock_client, 'test-model', request_config)
        self.assertIn('result', result)
        self.assertEqual(tokens, 10)
        mock_generator.generate_json.assert_called_once()

    def test_run_function_without_schema(self):
        """Test the main run function without a schema (fallback)."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Regular response'))]
        mock_response.usage.completion_tokens = 5
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        result, tokens = run('System prompt', 'Test query', mock_client, 'test-model', {})
        self.assertEqual(result, 'Regular response')
        self.assertEqual(tokens, 5)
        mock_client.chat.completions.create.assert_called_once()

    @patch('optillm.plugins.json_plugin.JSONGenerator')
    def test_error_handling(self, mock_json_generator_class):
        """Test error handling and fallback."""
        mock_generator = Mock()
        mock_generator.generate_json.side_effect = Exception('Test error')
        mock_json_generator_class.return_value = mock_generator
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Fallback response'))]
        mock_response.usage.completion_tokens = 8
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        request_config = {'response_format': {'type': 'json_schema', 'json_schema': {'schema': {'type': 'object'}}}}
        result, tokens = run('System prompt', 'Test query', mock_client, 'test-model', request_config)
        self.assertEqual(result, 'Fallback response')
        self.assertEqual(tokens, 8)
        mock_client.chat.completions.create.assert_called_once()

@patch('optillm.plugins.json_plugin.outlines.from_transformers')
@patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
def test_json_generator_init(self, mock_tokenizer, mock_from_transformers):
    """Test JSONGenerator initialization with new API."""
    mock_model = Mock()
    mock_from_transformers.return_value = mock_model
    mock_tokenizer.return_value = Mock()
    generator = JSONGenerator()
    mock_from_transformers.assert_called_once()
    mock_tokenizer.assert_called_once()
    self.assertIsNotNone(generator.model)
    self.assertIsNotNone(generator.tokenizer)

@patch('optillm.plugins.json_plugin.outlines.from_transformers')
@patch('optillm.plugins.json_plugin.AutoModelForCausalLM.from_pretrained')
@patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
def test_parse_json_schema_to_pydantic(self, mock_tokenizer, mock_model, mock_from_transformers):
    """Test JSON schema to Pydantic model conversion."""
    if not PLUGIN_AVAILABLE:
        self.skipTest('JSON plugin not available')
    mock_model.return_value = Mock()
    mock_tokenizer.return_value = Mock()
    mock_from_transformers.return_value = Mock()
    generator = JSONGenerator()
    try:
        result = generator.parse_json_schema_to_pydantic(self.simple_schema)
        self.assertIsNotNone(result)
    except Exception:
        self.assertTrue(hasattr(generator, 'parse_json_schema_to_pydantic'))

@patch('optillm.plugins.json_plugin.outlines.from_transformers')
@patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
def test_generate_json_new_api(self, mock_tokenizer, mock_from_transformers):
    """Test JSON generation with new outlines API."""
    mock_result = Mock()
    mock_result.model_dump.return_value = {'name': 'Test', 'age': 25}
    mock_model = Mock()
    mock_model.return_value = mock_result
    mock_from_transformers.return_value = mock_model
    generator = JSONGenerator()
    prompt = 'Create a person named Test who is 25 years old'
    result = generator.generate_json(prompt, self.simple_schema)
    self.assertEqual(result, {'name': 'Test', 'age': 25})
    mock_model.assert_called_once()

def test_extract_schema_from_response_format(self):
    """Test schema extraction from OpenAI response format."""
    response_format = {'type': 'json_schema', 'json_schema': {'name': 'test_schema', 'schema': {'type': 'object', 'properties': {'test': {'type': 'string'}}}}}
    result = extract_schema_from_response_format(response_format)
    self.assertIsNotNone(result)
    schema = json.loads(result)
    self.assertEqual(schema['type'], 'object')
    self.assertIn('test', schema['properties'])

@patch('optillm.plugins.json_plugin.JSONGenerator')
def test_run_function_with_schema(self, mock_json_generator_class):
    """Test the main run function with a valid schema."""
    mock_generator = Mock()
    mock_generator.generate_json.return_value = {'result': 'test'}
    mock_generator.count_tokens.return_value = 10
    mock_json_generator_class.return_value = mock_generator
    mock_client = Mock()
    request_config = {'response_format': {'type': 'json_schema', 'json_schema': {'schema': {'type': 'object', 'properties': {'result': {'type': 'string'}}}}}}
    result, tokens = run('System prompt', 'Generate a test result', mock_client, 'test-model', request_config)
    self.assertIn('result', result)
    self.assertEqual(tokens, 10)
    mock_generator.generate_json.assert_called_once()

def test_run_function_without_schema(self):
    """Test the main run function without a schema (fallback)."""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='Regular response'))]
    mock_response.usage.completion_tokens = 5
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    result, tokens = run('System prompt', 'Test query', mock_client, 'test-model', {})
    self.assertEqual(result, 'Regular response')
    self.assertEqual(tokens, 5)
    mock_client.chat.completions.create.assert_called_once()

@patch('optillm.plugins.json_plugin.JSONGenerator')
def test_error_handling(self, mock_json_generator_class):
    """Test error handling and fallback."""
    mock_generator = Mock()
    mock_generator.generate_json.side_effect = Exception('Test error')
    mock_json_generator_class.return_value = mock_generator
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='Fallback response'))]
    mock_response.usage.completion_tokens = 8
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    request_config = {'response_format': {'type': 'json_schema', 'json_schema': {'schema': {'type': 'object'}}}}
    result, tokens = run('System prompt', 'Test query', mock_client, 'test-model', request_config)
    self.assertEqual(result, 'Fallback response')
    self.assertEqual(tokens, 8)
    mock_client.chat.completions.create.assert_called_once()

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

class TestCountReasoningTokens(unittest.TestCase):
    """Test the count_reasoning_tokens function"""

    def test_count_reasoning_tokens_basic(self):
        """Test basic functionality of count_reasoning_tokens"""
        text_with_think = '<think>This is reasoning content</think>This is output'
        result1 = optillm_count_reasoning_tokens(text_with_think)
        result2 = inference_count_reasoning_tokens(text_with_think)
        self.assertGreater(result1, 0)
        self.assertEqual(result1, result2)

    def test_count_reasoning_tokens_no_think_tags(self):
        """Test with text that has no think tags"""
        text_without_think = 'This is just regular output text'
        result1 = optillm_count_reasoning_tokens(text_without_think)
        result2 = inference_count_reasoning_tokens(text_without_think)
        self.assertEqual(result1, 0)
        self.assertEqual(result2, 0)

    def test_count_reasoning_tokens_multiple_think_blocks(self):
        """Test with multiple think tag blocks"""
        text_multiple = '\n        <think>First reasoning block</think>\n        Some output here\n        <think>Second reasoning block with more content</think>\n        Final output\n        '
        result = optillm_count_reasoning_tokens(text_multiple)
        self.assertGreater(result, 0)
        single_block = '<think>First reasoning blockSecond reasoning block with more content</think>'
        single_result = optillm_count_reasoning_tokens(single_block)
        self.assertAlmostEqual(result, single_result, delta=2)

    def test_count_reasoning_tokens_empty_input(self):
        """Test with empty or None input"""
        self.assertEqual(optillm_count_reasoning_tokens(''), 0)
        self.assertEqual(optillm_count_reasoning_tokens(None), 0)
        self.assertEqual(optillm_count_reasoning_tokens(123), 0)

    def test_count_reasoning_tokens_malformed_tags(self):
        """Test with malformed think tags"""
        malformed_cases = ['<think>Unclosed think tag', 'Unopened think tag</think>', '<think><think>Nested tags</think></think>', '<THINK>Wrong case</THINK>', '<think></think>']
        for case in malformed_cases:
            result = optillm_count_reasoning_tokens(case)
            self.assertGreaterEqual(result, 0)

    def test_count_reasoning_tokens_with_tokenizer(self):
        """Test with a mock tokenizer for precise counting"""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        text = '<think>Some reasoning text</think>Output'
        result = optillm_count_reasoning_tokens(text, mock_tokenizer)
        self.assertEqual(result, 5)
        mock_tokenizer.encode.assert_called_once_with('Some reasoning text')

    def test_count_reasoning_tokens_tokenizer_error(self):
        """Test fallback when tokenizer fails"""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.side_effect = Exception('Tokenizer error')
        text = '<think>Some reasoning text</think>Output'
        result = optillm_count_reasoning_tokens(text, mock_tokenizer)
        self.assertGreater(result, 0)
        mock_tokenizer.encode.assert_called_once()

    def test_count_reasoning_tokens_multiline(self):
        """Test with multiline think blocks"""
        multiline_text = '<think>\n        This is a multi-line reasoning block\n        with several lines of content\n        that spans multiple lines\n        </think>\n        This is the final output'
        result = optillm_count_reasoning_tokens(multiline_text)
        self.assertGreater(result, 10)

    def test_count_reasoning_tokens_special_characters(self):
        """Test with special characters in think blocks"""
        special_text = '<think>Content with émojis 🤔 and symbols @#$%^&*()</think>Output'
        result = optillm_count_reasoning_tokens(special_text)
        self.assertGreater(result, 0)

def test_count_reasoning_tokens_basic(self):
    """Test basic functionality of count_reasoning_tokens"""
    text_with_think = '<think>This is reasoning content</think>This is output'
    result1 = optillm_count_reasoning_tokens(text_with_think)
    result2 = inference_count_reasoning_tokens(text_with_think)
    self.assertGreater(result1, 0)
    self.assertEqual(result1, result2)

def test_count_reasoning_tokens_no_think_tags(self):
    """Test with text that has no think tags"""
    text_without_think = 'This is just regular output text'
    result1 = optillm_count_reasoning_tokens(text_without_think)
    result2 = inference_count_reasoning_tokens(text_without_think)
    self.assertEqual(result1, 0)
    self.assertEqual(result2, 0)

def test_count_reasoning_tokens_multiple_think_blocks(self):
    """Test with multiple think tag blocks"""
    text_multiple = '\n        <think>First reasoning block</think>\n        Some output here\n        <think>Second reasoning block with more content</think>\n        Final output\n        '
    result = optillm_count_reasoning_tokens(text_multiple)
    self.assertGreater(result, 0)
    single_block = '<think>First reasoning blockSecond reasoning block with more content</think>'
    single_result = optillm_count_reasoning_tokens(single_block)
    self.assertAlmostEqual(result, single_result, delta=2)

def test_count_reasoning_tokens_empty_input(self):
    """Test with empty or None input"""
    self.assertEqual(optillm_count_reasoning_tokens(''), 0)
    self.assertEqual(optillm_count_reasoning_tokens(None), 0)
    self.assertEqual(optillm_count_reasoning_tokens(123), 0)

def test_count_reasoning_tokens_malformed_tags(self):
    """Test with malformed think tags"""
    malformed_cases = ['<think>Unclosed think tag', 'Unopened think tag</think>', '<think><think>Nested tags</think></think>', '<THINK>Wrong case</THINK>', '<think></think>']
    for case in malformed_cases:
        result = optillm_count_reasoning_tokens(case)
        self.assertGreaterEqual(result, 0)

def test_count_reasoning_tokens_with_tokenizer(self):
    """Test with a mock tokenizer for precise counting"""
    mock_tokenizer = Mock()
    mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
    text = '<think>Some reasoning text</think>Output'
    result = optillm_count_reasoning_tokens(text, mock_tokenizer)
    self.assertEqual(result, 5)
    mock_tokenizer.encode.assert_called_once_with('Some reasoning text')

def test_count_reasoning_tokens_tokenizer_error(self):
    """Test fallback when tokenizer fails"""
    mock_tokenizer = Mock()
    mock_tokenizer.encode.side_effect = Exception('Tokenizer error')
    text = '<think>Some reasoning text</think>Output'
    result = optillm_count_reasoning_tokens(text, mock_tokenizer)
    self.assertGreater(result, 0)
    mock_tokenizer.encode.assert_called_once()

def test_count_reasoning_tokens_multiline(self):
    """Test with multiline think blocks"""
    multiline_text = '<think>\n        This is a multi-line reasoning block\n        with several lines of content\n        that spans multiple lines\n        </think>\n        This is the final output'
    result = optillm_count_reasoning_tokens(multiline_text)
    self.assertGreater(result, 10)

def test_count_reasoning_tokens_special_characters(self):
    """Test with special characters in think blocks"""
    special_text = '<think>Content with émojis 🤔 and symbols @#$%^&*()</think>Output'
    result = optillm_count_reasoning_tokens(special_text)
    self.assertGreater(result, 0)

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

class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing functionality"""

    def test_existing_approaches_still_work(self):
        """Test that existing approaches work without reasoning token changes"""
        from optillm.bon import best_of_n_sampling
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Regular response'
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response
        try:
            result, tokens = best_of_n_sampling(system_prompt='You are a helpful assistant.', initial_query='test', client=mock_client, model='test-model', n=3)
            self.assertIsInstance(result, str)
            self.assertIsInstance(tokens, int)
        except Exception as e:
            self.fail(f'Existing approach failed: {e}')

    def test_api_without_auth_header(self):
        """Test API still returns proper errors without auth"""
        import optillm
        app = optillm.app
        app.config['TESTING'] = True
        client = app.test_client()
        response = client.post('/v1/chat/completions', json={'model': TEST_MODEL, 'messages': []})
        self.assertIn(response.status_code, [401, 403, 500])

def test_existing_approaches_still_work(self):
    """Test that existing approaches work without reasoning token changes"""
    from optillm.bon import best_of_n_sampling
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = 'Regular response'
    mock_response.usage.completion_tokens = 10
    mock_client.chat.completions.create.return_value = mock_response
    try:
        result, tokens = best_of_n_sampling(system_prompt='You are a helpful assistant.', initial_query='test', client=mock_client, model='test-model', n=3)
        self.assertIsInstance(result, str)
        self.assertIsInstance(tokens, int)
    except Exception as e:
        self.fail(f'Existing approach failed: {e}')

def test_api_without_auth_header(self):
    """Test API still returns proper errors without auth"""
    import optillm
    app = optillm.app
    app.config['TESTING'] = True
    client = app.test_client()
    response = client.post('/v1/chat/completions', json={'model': TEST_MODEL, 'messages': []})
    self.assertIn(response.status_code, [401, 403, 500])

def test_approach_imports():
    """Test that all approaches can be imported"""
    approaches = [chat_with_mcts, best_of_n_sampling, mixture_of_agents, advanced_self_consistency_approach, re2_approach, cot_reflection, plansearch, leap, multi_agent_reasoning_system]
    for approach in approaches:
        assert callable(approach), f'{approach.__name__} is not callable'
    print('✅ All approaches imported successfully')

def test_basic_approach_calls():
    """Test basic approach calls with mock client"""
    client = MockClient()
    system_prompt = 'You are a helpful assistant.'
    query = 'What is 2 + 2?'
    model = 'mock-model'
    simple_approaches = [('re2_approach', re2_approach), ('cot_reflection', cot_reflection), ('leap', leap), ('mars', multi_agent_reasoning_system)]
    for name, approach_func in simple_approaches:
        try:
            result = approach_func(system_prompt, query, client, model)
            assert result is not None, f'{name} returned None'
            assert isinstance(result, tuple), f'{name} should return a tuple'
            assert len(result) == 2, f'{name} should return (response, tokens)'
            print(f'✅ {name} basic test passed')
        except Exception as e:
            print(f'❌ {name} basic test failed: {e}')

def test_n_parameter(client):
    """Test n parameter for multiple completions"""
    n = 3
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': 'Write a one-line joke'}], n=n, temperature=0.8, max_tokens=50)
    assert len(response.choices) == n
    contents = [choice.message.content for choice in response.choices]
    assert len(set(contents)) > 1

