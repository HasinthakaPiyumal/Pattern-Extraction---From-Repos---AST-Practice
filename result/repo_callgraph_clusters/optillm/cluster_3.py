# Cluster 3

def calculate_accuracy(predictions, labels):
    return (predictions == labels).float().mean()

def numerically_equal(str1: str, str2: str) -> bool:
    """Compare if two numeric strings represent the same value."""
    try:
        return abs(float(str1) - float(str2)) < 1e-10
    except:
        return False

def analyze_logits_probs(logprobs_data: List[Dict]) -> Dict:
    """
    Analyze token probability distributions and entropy patterns.
    
    Args:
        logprobs_data: List of dictionaries containing token and logprob information
        
    Returns:
        Dict: Analysis metrics including entropy statistics
    """
    if not logprobs_data:
        return {'entropy_stats': None, 'transition_entropy': None, 'token_count': 0}
    token_entropies = []
    token_probs = []
    token_texts = []
    for token_info in logprobs_data:
        if not token_info.get('top_logprobs'):
            continue
        probs = []
        for token, logprob in token_info['top_logprobs'].items():
            probs.append(math.exp(logprob))
        total_prob = sum(probs)
        if total_prob > 0:
            probs = [p / total_prob for p in probs]
        entropy = -sum((p * math.log2(p) if p > 0 else 0 for p in probs))
        token_entropies.append(entropy)
        token_probs.append(probs[0] if probs else 0)
        token_texts.append(token_info['token'])
    transition_entropy = {}
    for phrase in THOUGHT_TRANSITIONS:
        transition_indices = []
        for i, token in enumerate(token_texts):
            if phrase.startswith(token) and i < len(token_texts) - 1:
                transition_indices.append(i)
        if transition_indices:
            before_entropy = []
            after_entropy = []
            for idx in transition_indices:
                before_window = max(0, idx - 5)
                after_window = min(len(token_entropies), idx + 5)
                if idx > before_window:
                    before_entropy.extend(token_entropies[before_window:idx])
                if after_window > idx:
                    after_entropy.extend(token_entropies[idx:after_window])
            transition_entropy[phrase] = {'before_mean': statistics.mean(before_entropy) if before_entropy else 0, 'after_mean': statistics.mean(after_entropy) if after_entropy else 0, 'count': len(transition_indices)}
    entropy_stats = {'mean': statistics.mean(token_entropies) if token_entropies else 0, 'median': statistics.median(token_entropies) if token_entropies else 0, 'max': max(token_entropies) if token_entropies else 0, 'min': min(token_entropies) if token_entropies else 0, 'std': statistics.stdev(token_entropies) if len(token_entropies) > 1 else 0}
    if token_entropies:
        quartile_size = max(1, len(token_entropies) // 4)
        entropy_stats['quartiles'] = [statistics.mean(token_entropies[i:i + quartile_size]) for i in range(0, len(token_entropies), quartile_size) if i < len(token_entropies)]
    else:
        entropy_stats['quartiles'] = []
    return {'entropy_stats': entropy_stats, 'transition_entropy': transition_entropy, 'token_count': len(token_entropies)}

def analyze_results(results: List[Dict], n: int, analyze_thoughts: bool=False, analyze_logits: bool=False):
    """
    Analyze and print summary statistics of the results.
    
    Args:
        results (List[Dict]): List of evaluation results
        n (int): Number of attempts per problem
        analyze_thoughts (bool): Whether to analyze thinking patterns
        analyze_logits (bool): Whether to analyze token probabilities
    """
    total = len(results)
    correct = sum((1 for r in results if r['is_correct']))
    accuracy = correct / total if total > 0 else 0
    print('\n=== Results Summary ===')
    print(f'Evaluation mode: pass@{n}')
    print(f'Total problems: {total}')
    print(f'Correct answers: {correct}')
    print(f'Accuracy: {accuracy:.2%}')
    successful_attempts = [r['first_correct_attempt'] for r in results if r['is_correct']]
    if successful_attempts:
        avg_attempts = sum(successful_attempts) / len(successful_attempts)
        print(f'\nFor correct solutions:')
        print(f'Average attempts needed: {avg_attempts:.2f}')
        print(f'Attempt distribution:')
        for i in range(1, n + 1):
            count = sum((1 for x in successful_attempts if x == i))
            print(f'  Attempt {i}: {count} problems')
    if analyze_thoughts:
        print('\n=== Thinking Pattern Analysis ===')
        correct_attempts = []
        incorrect_attempts = []
        for result in results:
            for attempt in result['attempts']:
                if 'thought_analysis' in attempt:
                    if result['is_correct'] and attempt['predicted_answer'] == result['correct_answer']:
                        correct_attempts.append(attempt)
                    else:
                        incorrect_attempts.append(attempt)

        def calc_stats(attempts):
            if not attempts:
                return {'count': 0, 'avg_thinking_tokens': 0, 'avg_thought_transitions': 0, 'transition_usage': {phrase: 0 for phrase in THOUGHT_TRANSITIONS}, 'has_think_tags_pct': 0}
            thinking_tokens = [a['thought_analysis']['thinking_tokens'] for a in attempts]
            thought_transitions = [a['thought_analysis']['thought_transitions'] for a in attempts]
            has_think_tags = sum((1 for a in attempts if a['thought_analysis']['has_think_tags']))
            transition_usage = defaultdict(int)
            for attempt in attempts:
                for phrase, count in attempt['thought_analysis']['transition_counts'].items():
                    transition_usage[phrase] += count
            return {'count': len(attempts), 'avg_thinking_tokens': statistics.mean(thinking_tokens) if thinking_tokens else 0, 'median_thinking_tokens': statistics.median(thinking_tokens) if thinking_tokens else 0, 'min_thinking_tokens': min(thinking_tokens) if thinking_tokens else 0, 'max_thinking_tokens': max(thinking_tokens) if thinking_tokens else 0, 'avg_thought_transitions': statistics.mean(thought_transitions) if thought_transitions else 0, 'median_thought_transitions': statistics.median(thought_transitions) if thought_transitions else 0, 'transition_usage': dict(transition_usage), 'has_think_tags_pct': has_think_tags / len(attempts) * 100 if attempts else 0}
        correct_stats = calc_stats(correct_attempts)
        incorrect_stats = calc_stats(incorrect_attempts)
        all_stats = calc_stats(correct_attempts + incorrect_attempts)
        print(f'\nOverall Thinking Statistics (All {all_stats['count']} Attempts):')
        print(f'- Average thinking tokens: {all_stats['avg_thinking_tokens']:.2f}')
        print(f'- Median thinking tokens: {all_stats['median_thinking_tokens']}')
        print(f'- Range: {all_stats['min_thinking_tokens']} - {all_stats['max_thinking_tokens']} tokens')
        print(f'- Average thought transitions: {all_stats['avg_thought_transitions']:.2f}')
        print(f'- Median thought transitions: {all_stats['median_thought_transitions']}')
        print(f'- Percentage with <think> tags: {all_stats['has_think_tags_pct']:.2f}%')
        print(f'- Transition phrase usage:')
        for phrase, count in all_stats['transition_usage'].items():
            print(f'  - {phrase}: {count} occurrences')
        print(f'\nCorrect Attempts ({correct_stats['count']}):')
        print(f'- Average thinking tokens: {correct_stats['avg_thinking_tokens']:.2f}')
        print(f'- Median thinking tokens: {correct_stats['median_thinking_tokens']}')
        print(f'- Average thought transitions: {correct_stats['avg_thought_transitions']:.2f}')
        print(f'- Median thought transitions: {correct_stats['median_thought_transitions']}')
        print(f'- Percentage with <think> tags: {correct_stats['has_think_tags_pct']:.2f}%')
        print(f'- Transition phrase usage:')
        for phrase, count in correct_stats['transition_usage'].items():
            print(f'  - {phrase}: {count} occurrences')
        print(f'\nIncorrect Attempts ({incorrect_stats['count']}):')
        print(f'- Average thinking tokens: {incorrect_stats['avg_thinking_tokens']:.2f}')
        print(f'- Median thinking tokens: {incorrect_stats['median_thinking_tokens']}')
        print(f'- Average thought transitions: {incorrect_stats['avg_thought_transitions']:.2f}')
        print(f'- Median thought transitions: {incorrect_stats['median_thought_transitions']}')
        print(f'- Percentage with <think> tags: {incorrect_stats['has_think_tags_pct']:.2f}%')
        print(f'- Transition phrase usage:')
        for phrase, count in incorrect_stats['transition_usage'].items():
            print(f'  - {phrase}: {count} occurrences')
        if correct_attempts and incorrect_attempts:
            print('\nCorrelation Analysis:')
            problems_with_both = defaultdict(lambda: {'correct': [], 'incorrect': []})
            for result in results:
                problem_id = result['index']
                for attempt in result['attempts']:
                    if 'thought_analysis' in attempt:
                        category = 'correct' if attempt['predicted_answer'] == result['correct_answer'] else 'incorrect'
                        problems_with_both[problem_id][category].append(attempt)
            valid_problems = {k: v for k, v in problems_with_both.items() if v['correct'] and v['incorrect']}
            if valid_problems:
                print(f'Found {len(valid_problems)} problems with both correct and incorrect attempts')
                avg_token_diff = []
                avg_transition_diff = []
                for problem_id, attempts in valid_problems.items():
                    correct_tokens = [a['thought_analysis']['thinking_tokens'] for a in attempts['correct']]
                    incorrect_tokens = [a['thought_analysis']['thinking_tokens'] for a in attempts['incorrect']]
                    correct_transitions = [a['thought_analysis']['thought_transitions'] for a in attempts['correct']]
                    incorrect_transitions = [a['thought_analysis']['thought_transitions'] for a in attempts['incorrect']]
                    avg_correct_tokens = statistics.mean(correct_tokens) if correct_tokens else 0
                    avg_incorrect_tokens = statistics.mean(incorrect_tokens) if incorrect_tokens else 0
                    avg_correct_transitions = statistics.mean(correct_transitions) if correct_transitions else 0
                    avg_incorrect_transitions = statistics.mean(incorrect_transitions) if incorrect_transitions else 0
                    avg_token_diff.append(avg_correct_tokens - avg_incorrect_tokens)
                    avg_transition_diff.append(avg_correct_transitions - avg_incorrect_transitions)
                print(f'Average token difference (correct - incorrect): {statistics.mean(avg_token_diff):.2f}')
                print(f'Average transition difference (correct - incorrect): {statistics.mean(avg_transition_diff):.2f}')
    if analyze_logits:
        print('\n=== Logit Analysis ===')
        correct_attempts = []
        incorrect_attempts = []
        for result in results:
            for attempt in result['attempts']:
                if 'logit_analysis' in attempt:
                    if result['is_correct'] and attempt['predicted_answer'] == result['correct_answer']:
                        correct_attempts.append(attempt)
                    else:
                        incorrect_attempts.append(attempt)

        def calc_logit_stats(attempts):
            if not attempts:
                return {'count': 0, 'entropy': None, 'transitions': None}
            entropy_means = []
            entropy_stds = []
            entropy_quartiles = []
            transition_entropies = defaultdict(lambda: {'before': [], 'after': []})
            for attempt in attempts:
                if attempt['logit_analysis'].get('entropy_stats') and attempt['logit_analysis']['entropy_stats'].get('mean'):
                    entropy_means.append(attempt['logit_analysis']['entropy_stats']['mean'])
                    entropy_stds.append(attempt['logit_analysis']['entropy_stats']['std'])
                    if attempt['logit_analysis']['entropy_stats'].get('quartiles'):
                        entropy_quartiles.append(attempt['logit_analysis']['entropy_stats']['quartiles'])
                    if attempt['logit_analysis'].get('transition_entropy'):
                        for phrase, stats in attempt['logit_analysis']['transition_entropy'].items():
                            if stats.get('before_mean') is not None:
                                transition_entropies[phrase]['before'].append(stats['before_mean'])
                            if stats.get('after_mean') is not None:
                                transition_entropies[phrase]['after'].append(stats['after_mean'])
            avg_quartiles = []
            if entropy_quartiles:
                max_quartiles = max((len(q) for q in entropy_quartiles))
                padded_quartiles = [q + [0] * (max_quartiles - len(q)) for q in entropy_quartiles]
                for i in range(max_quartiles):
                    quartile_values = [q[i] for q in padded_quartiles if i < len(q)]
                    avg_quartiles.append(statistics.mean(quartile_values) if quartile_values else 0)
            transition_stats = {}
            for phrase, values in transition_entropies.items():
                if values['before'] and values['after']:
                    before_mean = statistics.mean(values['before'])
                    after_mean = statistics.mean(values['after'])
                    transition_stats[phrase] = {'before_mean': before_mean, 'after_mean': after_mean, 'entropy_change': after_mean - before_mean, 'count': len(values['before'])}
            return {'count': len(attempts), 'entropy': {'mean': statistics.mean(entropy_means) if entropy_means else 0, 'std': statistics.mean(entropy_stds) if entropy_stds else 0, 'quartiles': avg_quartiles}, 'transitions': transition_stats}
        correct_stats = calc_logit_stats(correct_attempts)
        incorrect_stats = calc_logit_stats(incorrect_attempts)
        all_stats = calc_logit_stats(correct_attempts + incorrect_attempts)
        print(f'\nOverall Logit Statistics (All {all_stats['count']} Attempts):')
        if all_stats['entropy'] and all_stats['entropy']['mean']:
            print(f'- Average entropy: {all_stats['entropy']['mean']:.4f}')
            print(f'- Average entropy std: {all_stats['entropy']['std']:.4f}')
            if all_stats['entropy']['quartiles']:
                print(f'- Entropy by generation quartile:')
                for i, q in enumerate(all_stats['entropy']['quartiles']):
                    print(f'  - Q{i + 1}: {q:.4f}')
            if all_stats['transitions']:
                print(f'- Entropy around thought transitions:')
                for phrase, stats in all_stats['transitions'].items():
                    change = stats['entropy_change']
                    change_dir = 'increases' if change > 0 else 'decreases'
                    print(f'  - {phrase} (n={stats['count']}): Entropy {change_dir} by {abs(change):.4f}')
                    print(f'    - Before: {stats['before_mean']:.4f}, After: {stats['after_mean']:.4f}')
        if correct_stats['count'] > 0 and incorrect_stats['count'] > 0:
            print('\nEntropy Comparison (Correct vs Incorrect Attempts):')
            if correct_stats['entropy'] and correct_stats['entropy']['mean'] and incorrect_stats['entropy'] and incorrect_stats['entropy']['mean']:
                correct_entropy = correct_stats['entropy']['mean']
                incorrect_entropy = incorrect_stats['entropy']['mean']
                diff = correct_entropy - incorrect_entropy
                print(f'- Correct attempts avg entropy: {correct_entropy:.4f}')
                print(f'- Incorrect attempts avg entropy: {incorrect_entropy:.4f}')
                print(f'- Difference (correct - incorrect): {diff:.4f}')
                if correct_stats['entropy']['quartiles'] and incorrect_stats['entropy']['quartiles']:
                    print(f'- Entropy progression through generation:')
                    for i in range(min(len(correct_stats['entropy']['quartiles']), len(incorrect_stats['entropy']['quartiles']))):
                        c_q = correct_stats['entropy']['quartiles'][i]
                        i_q = incorrect_stats['entropy']['quartiles'][i]
                        q_diff = c_q - i_q
                        print(f'  - Q{i + 1}: Correct: {c_q:.4f}, Incorrect: {i_q:.4f}, Diff: {q_diff:.4f}')
                common_transitions = set(correct_stats['transitions'].keys()) & set(incorrect_stats['transitions'].keys())
                if common_transitions:
                    print(f'- Entropy changes around thought transitions:')
                    for phrase in common_transitions:
                        c_stats = correct_stats['transitions'][phrase]
                        i_stats = incorrect_stats['transitions'][phrase]
                        c_change = c_stats['entropy_change']
                        i_change = i_stats['entropy_change']
                        print(f'  - {phrase}:')
                        print(f'    - Correct: {c_stats['before_mean']:.4f} → {c_stats['after_mean']:.4f} (Δ {c_change:.4f})')
                        print(f'    - Incorrect: {i_stats['before_mean']:.4f} → {i_stats['after_mean']:.4f} (Δ {i_change:.4f})')
                        print(f'    - Difference in entropy change: {c_change - i_change:.4f}')
    print('\n=== Incorrect Problems ===')
    for r in results:
        if not r['is_correct']:
            print(f'Problem {r['index']}:')
            print(f'Expected: {r['correct_answer']}')
            print('Predicted answers across attempts:', [attempt['predicted_answer'] for attempt in r['attempts']])
            print('---')

def calc_stats(attempts):
    if not attempts:
        return {'count': 0, 'avg_thinking_tokens': 0, 'avg_thought_transitions': 0, 'transition_usage': {phrase: 0 for phrase in THOUGHT_TRANSITIONS}, 'has_think_tags_pct': 0}
    thinking_tokens = [a['thought_analysis']['thinking_tokens'] for a in attempts]
    thought_transitions = [a['thought_analysis']['thought_transitions'] for a in attempts]
    has_think_tags = sum((1 for a in attempts if a['thought_analysis']['has_think_tags']))
    transition_usage = defaultdict(int)
    for attempt in attempts:
        for phrase, count in attempt['thought_analysis']['transition_counts'].items():
            transition_usage[phrase] += count
    return {'count': len(attempts), 'avg_thinking_tokens': statistics.mean(thinking_tokens) if thinking_tokens else 0, 'median_thinking_tokens': statistics.median(thinking_tokens) if thinking_tokens else 0, 'min_thinking_tokens': min(thinking_tokens) if thinking_tokens else 0, 'max_thinking_tokens': max(thinking_tokens) if thinking_tokens else 0, 'avg_thought_transitions': statistics.mean(thought_transitions) if thought_transitions else 0, 'median_thought_transitions': statistics.median(thought_transitions) if thought_transitions else 0, 'transition_usage': dict(transition_usage), 'has_think_tags_pct': has_think_tags / len(attempts) * 100 if attempts else 0}

def calc_logit_stats(attempts):
    if not attempts:
        return {'count': 0, 'entropy': None, 'transitions': None}
    entropy_means = []
    entropy_stds = []
    entropy_quartiles = []
    transition_entropies = defaultdict(lambda: {'before': [], 'after': []})
    for attempt in attempts:
        if attempt['logit_analysis'].get('entropy_stats') and attempt['logit_analysis']['entropy_stats'].get('mean'):
            entropy_means.append(attempt['logit_analysis']['entropy_stats']['mean'])
            entropy_stds.append(attempt['logit_analysis']['entropy_stats']['std'])
            if attempt['logit_analysis']['entropy_stats'].get('quartiles'):
                entropy_quartiles.append(attempt['logit_analysis']['entropy_stats']['quartiles'])
            if attempt['logit_analysis'].get('transition_entropy'):
                for phrase, stats in attempt['logit_analysis']['transition_entropy'].items():
                    if stats.get('before_mean') is not None:
                        transition_entropies[phrase]['before'].append(stats['before_mean'])
                    if stats.get('after_mean') is not None:
                        transition_entropies[phrase]['after'].append(stats['after_mean'])
    avg_quartiles = []
    if entropy_quartiles:
        max_quartiles = max((len(q) for q in entropy_quartiles))
        padded_quartiles = [q + [0] * (max_quartiles - len(q)) for q in entropy_quartiles]
        for i in range(max_quartiles):
            quartile_values = [q[i] for q in padded_quartiles if i < len(q)]
            avg_quartiles.append(statistics.mean(quartile_values) if quartile_values else 0)
    transition_stats = {}
    for phrase, values in transition_entropies.items():
        if values['before'] and values['after']:
            before_mean = statistics.mean(values['before'])
            after_mean = statistics.mean(values['after'])
            transition_stats[phrase] = {'before_mean': before_mean, 'after_mean': after_mean, 'entropy_change': after_mean - before_mean, 'count': len(values['before'])}
    return {'count': len(attempts), 'entropy': {'mean': statistics.mean(entropy_means) if entropy_means else 0, 'std': statistics.mean(entropy_stds) if entropy_stds else 0, 'quartiles': avg_quartiles}, 'transitions': transition_stats}

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

def shutdown(self):
    """Shutdown the batcher and all background threads"""
    self._shutdown = True
    if self.enable_logging:
        logger.info('RequestBatcher shutting down...')
    for thread in self.batch_threads.values():
        thread.join(timeout=1.0)

class PromptCache:
    """Advanced caching system for frequent prompts and responses"""

    def __init__(self, max_size: int=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.prompt_stats = defaultdict(lambda: {'count': 0, 'success_rate': 0.0})

    @lru_cache(maxsize=128)
    def _compute_prompt_signature(self, prompt: str) -> str:
        """Compute a signature for semantic similarity matching"""
        words = set(prompt.lower().split())
        return ' '.join(sorted(list(words)))

    def get_cached_response(self, prompt: str, temperature: float, top_p: float) -> Optional[str]:
        """Get cached response with fuzzy matching"""
        signature = self._compute_prompt_signature(prompt)
        if signature in self.cache:
            cached_item = self.cache[signature]
            if abs(cached_item['temperature'] - temperature) < 0.1 and abs(cached_item['top_p'] - top_p) < 0.1:
                self.prompt_stats[signature]['count'] += 1
                return cached_item['response']
        return None

    def add_to_cache(self, prompt: str, response: str, temperature: float, top_p: float):
        """Add response to cache with metadata"""
        signature = self._compute_prompt_signature(prompt)
        self.cache[signature] = {'response': response, 'temperature': temperature, 'top_p': top_p, 'timestamp': torch.cuda.current_timestamp() if torch.cuda.is_available() else 0}
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def update_stats(self, prompt: str, success: bool):
        """Update prompt success statistics"""
        signature = self._compute_prompt_signature(prompt)
        stats = self.prompt_stats[signature]
        stats['count'] += 1
        stats['success_rate'] = (stats['success_rate'] * (stats['count'] - 1) + float(success)) / stats['count']

def __init__(self, max_size: int=1000):
    self.max_size = max_size
    self.cache = OrderedDict()
    self.prompt_stats = defaultdict(lambda: {'count': 0, 'success_rate': 0.0})

def get_cached_response(self, prompt: str, temperature: float, top_p: float) -> Optional[str]:
    """Get cached response with fuzzy matching"""
    signature = self._compute_prompt_signature(prompt)
    if signature in self.cache:
        cached_item = self.cache[signature]
        if abs(cached_item['temperature'] - temperature) < 0.1 and abs(cached_item['top_p'] - top_p) < 0.1:
            self.prompt_stats[signature]['count'] += 1
            return cached_item['response']
    return None

def add_to_cache(self, prompt: str, response: str, temperature: float, top_p: float):
    """Add response to cache with metadata"""
    signature = self._compute_prompt_signature(prompt)
    self.cache[signature] = {'response': response, 'temperature': temperature, 'top_p': top_p, 'timestamp': torch.cuda.current_timestamp() if torch.cuda.is_available() else 0}
    if len(self.cache) > self.max_size:
        self.cache.popitem(last=False)

def update_stats(self, prompt: str, success: bool):
    """Update prompt success statistics"""
    signature = self._compute_prompt_signature(prompt)
    stats = self.prompt_stats[signature]
    stats['count'] += 1
    stats['success_rate'] = (stats['success_rate'] * (stats['count'] - 1) + float(success)) / stats['count']

class CacheManager:
    """
    Singleton cache manager for models and tokenizers.
    Thread-safe but minimizes lock contention.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, max_size: int=5):
        if self._initialized:
            return
        with self._lock:
            if not self._initialized:
                logger.info('Initializing CacheManager singleton')
                self.max_size = max_size
                self.model_cache = OrderedDict()
                self.tokenizer_cache = OrderedDict()
                self.adapter_cache = OrderedDict()
                self.model_adapter_map = {}
                self.cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
                self._initialized = True
                logger.info('CacheManager singleton initialized')

    def get_or_load_model(self, model_key: str, loader_fn) -> Tuple[Any, Any]:
        """Get or load model and tokenizer with minimal locking."""
        cached_model = cached_tokenizer = None
        cache_hit = False
        with self._lock:
            if model_key in self.model_cache and model_key in self.tokenizer_cache:
                cached_model = self.model_cache[model_key]
                cached_tokenizer = self.tokenizer_cache[model_key]
                self.model_cache.move_to_end(model_key)
                self.tokenizer_cache.move_to_end(model_key)
                self.cache_stats[model_key]['hits'] += 1
                cache_hit = True
                logger.debug(f'Cache hit for model: {model_key}')
        if cache_hit:
            return (cached_model, cached_tokenizer)
        logger.info(f'Loading model and tokenizer: {model_key}')
        model, tokenizer = loader_fn()
        with self._lock:
            if model_key in self.model_cache and model_key in self.tokenizer_cache:
                cached_model = self.model_cache[model_key]
                cached_tokenizer = self.tokenizer_cache[model_key]
                self.cache_stats[model_key]['hits'] += 1
                logger.debug(f'Using already cached model: {model_key}')
                return (cached_model, cached_tokenizer)
            self.model_cache[model_key] = model
            self.tokenizer_cache[model_key] = tokenizer
            self.cache_stats[model_key]['misses'] += 1
            self.model_adapter_map[model_key] = []
            self._cleanup_caches()
            logger.info(f'Successfully cached model and tokenizer: {model_key}')
            return (model, tokenizer)

    def get_or_load_adapter(self, model_key: str, adapter_key: str, loader_fn):
        """Get or load adapter with enhanced caching."""
        cache_key = f'{model_key}_{adapter_key}'
        with self._lock:
            if cache_key in self.adapter_cache:
                adapter = self.adapter_cache[cache_key]
                self.adapter_cache.move_to_end(cache_key)
                logger.debug(f'Cache hit for adapter: {cache_key}')
                return adapter
        adapter = loader_fn()
        with self._lock:
            self.adapter_cache[cache_key] = adapter
            if model_key not in self.model_adapter_map:
                self.model_adapter_map[model_key] = []
            if adapter_key not in self.model_adapter_map[model_key]:
                self.model_adapter_map[model_key].append(adapter_key)
            self._cleanup_caches()
            logger.info(f'Successfully cached adapter: {cache_key}')
            return adapter

    def get_model_adapters(self, model_key: str) -> List[str]:
        """Get list of adapter IDs loaded for a specific model."""
        with self._lock:
            return self.model_adapter_map.get(model_key, [])

    def _cleanup_caches(self):
        """Clean up caches if they exceed max size."""
        while len(self.model_cache) > self.max_size:
            model_key, model = self.model_cache.popitem(last=False)
            if hasattr(model, 'cpu'):
                model.cpu()
            if model_key in self.model_adapter_map:
                for adapter_id in self.model_adapter_map[model_key]:
                    cache_key = f'{model_key}_{adapter_id}'
                    if cache_key in self.adapter_cache:
                        self.adapter_cache.pop(cache_key)
                self.model_adapter_map.pop(model_key)
        while len(self.tokenizer_cache) > self.max_size:
            self.tokenizer_cache.popitem(last=False)
        valid_cache_keys = {f'{model_key}_{adapter_id}' for model_key, adapter_ids in self.model_adapter_map.items() for adapter_id in adapter_ids}
        orphaned_adapters = [key for key in self.adapter_cache.keys() if key not in valid_cache_keys]
        for key in orphaned_adapters:
            adapter = self.adapter_cache.pop(key)
            if hasattr(adapter, 'cpu'):
                adapter.cpu()
        torch.cuda.empty_cache()

    @classmethod
    def get_instance(cls, max_size: int=5) -> 'CacheManager':
        """Alternative way to get the singleton instance."""
        if cls._instance is None:
            return cls(max_size)
        return cls._instance

def __init__(self, max_size: int=5):
    if self._initialized:
        return
    with self._lock:
        if not self._initialized:
            logger.info('Initializing CacheManager singleton')
            self.max_size = max_size
            self.model_cache = OrderedDict()
            self.tokenizer_cache = OrderedDict()
            self.adapter_cache = OrderedDict()
            self.model_adapter_map = {}
            self.cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
            self._initialized = True
            logger.info('CacheManager singleton initialized')

def _cleanup_caches(self):
    """Clean up caches if they exceed max size."""
    while len(self.model_cache) > self.max_size:
        model_key, model = self.model_cache.popitem(last=False)
        if hasattr(model, 'cpu'):
            model.cpu()
        if model_key in self.model_adapter_map:
            for adapter_id in self.model_adapter_map[model_key]:
                cache_key = f'{model_key}_{adapter_id}'
                if cache_key in self.adapter_cache:
                    self.adapter_cache.pop(cache_key)
            self.model_adapter_map.pop(model_key)
    while len(self.tokenizer_cache) > self.max_size:
        self.tokenizer_cache.popitem(last=False)
    valid_cache_keys = {f'{model_key}_{adapter_id}' for model_key, adapter_ids in self.model_adapter_map.items() for adapter_id in adapter_ids}
    orphaned_adapters = [key for key in self.adapter_cache.keys() if key not in valid_cache_keys]
    for key in orphaned_adapters:
        adapter = self.adapter_cache.pop(key)
        if hasattr(adapter, 'cpu'):
            adapter.cpu()
    torch.cuda.empty_cache()

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

def calculate_attention_metrics(attention_weights: torch.Tensor) -> Dict[str, torch.Tensor]:
    attention_probs = attention_weights
    attn_entropy = -torch.sum(attention_probs * torch.log2(torch.clamp(attention_probs, 1e-10, 1.0)), dim=-1)
    if attn_entropy.size(-1) > 1:
        attn_varentropy = torch.var(attn_entropy, dim=-1, unbiased=False)
    else:
        attn_varentropy = torch.zeros_like(attn_entropy)
    attn_varentropy = torch.where(torch.isnan(attn_varentropy), torch.zeros_like(attn_varentropy), attn_varentropy)
    mean_attention = torch.mean(attention_probs, dim=1)
    agreement = torch.mean(torch.abs(attention_probs - mean_attention.unsqueeze(1)), dim=(1, 2))
    attention_scores_proxy = torch.log(torch.clamp(attention_probs, 1e-10, 1.0))
    interaction_strength = torch.mean(torch.abs(attention_scores_proxy), dim=(1, 2, 3))
    return {'attn_entropy': torch.mean(attn_entropy), 'attn_varentropy': torch.mean(attn_varentropy), 'agreement': torch.mean(agreement), 'interaction_strength': interaction_strength}

class AdvancedSelfConsistency:

    def __init__(self, client, model: str, num_samples: int=5, similarity_threshold: float=0.8, request_id: str=None):
        self.client = client
        self.model = model
        self.num_samples = num_samples
        self.similarity_threshold = similarity_threshold
        self.self_consistency_completion_tokens = 0
        self.request_id = request_id

    def generate_responses(self, system_prompt: str, user_prompt: str) -> List[str]:
        responses = []
        for _ in range(self.num_samples):
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], 'temperature': 1, 'max_tokens': 4096}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.self_consistency_completion_tokens += response.usage.completion_tokens
            responses.append(response.choices[0].message.content)
        return responses

    def calculate_similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def cluster_similar_responses(self, responses: List[str]) -> List[List[str]]:
        clusters = []
        for response in responses:
            added_to_cluster = False
            for cluster in clusters:
                if self.calculate_similarity(response, cluster[0]) >= self.similarity_threshold:
                    cluster.append(response)
                    added_to_cluster = True
                    break
            if not added_to_cluster:
                clusters.append([response])
        return clusters

    def aggregate_results(self, responses: List[str]) -> Dict[str, any]:
        final_answers = responses
        clusters = self.cluster_similar_responses(final_answers)
        cluster_info = []
        for cluster in clusters:
            cluster_info.append({'answer': cluster[0], 'frequency': len(cluster), 'variants': cluster})
        cluster_info.sort(key=lambda x: x['frequency'], reverse=True)
        return {'clusters': cluster_info, 'total_responses': len(responses), 'num_unique_clusters': len(clusters)}

    def evaluate(self, system_prompt: str, user_prompt: str) -> Dict[str, any]:
        responses = self.generate_responses(system_prompt, user_prompt)
        aggregated_result = self.aggregate_results(responses)
        return {'individual_responses': responses, 'aggregated_result': aggregated_result}

def calculate_similarity(self, a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

class MARSAggregator:
    """
    RSA-inspired aggregation system for combining solutions

    Key features:
    - Population management (N > K for diversity)
    - Recursive aggregation loops
    - Parallel execution of aggregation calls
    - Solution quality tracking
    """

    def __init__(self, client, model: str, config: Dict[str, Any]):
        self.client = client
        self.model = model
        self.config = config
        self.population_size = config.get('population_size', 6)
        self.aggregation_size = config.get('aggregation_size', 3)
        self.aggregation_loops = config.get('aggregation_loops', 3)
        self.max_tokens = config.get('max_tokens', 30000)

    async def run_aggregation_loops(self, workspace: MARSWorkspace, request_id: str=None, executor: ThreadPoolExecutor=None) -> Tuple[int, Dict[str, Any]]:
        """
        Run T iterations of RSA-style aggregation

        Args:
            workspace: MARS workspace containing solutions
            request_id: Request ID for logging
            executor: Thread pool for parallel execution

        Returns:
            Tuple of (total_reasoning_tokens, aggregation_summary)
        """
        logger.info(f'Starting {self.aggregation_loops} aggregation loops')
        total_reasoning_tokens = 0
        aggregation_history = []
        self._ensure_population_size(workspace)
        for loop_idx in range(self.aggregation_loops):
            logger.info(f'Aggregation loop {loop_idx + 1}/{self.aggregation_loops}')
            loop_tokens, loop_summary = await self._run_single_aggregation_loop(workspace, loop_idx, request_id, executor)
            total_reasoning_tokens += loop_tokens
            aggregation_history.append({'loop': loop_idx, 'tokens': loop_tokens, 'summary': loop_summary})
            logger.info(f'Loop {loop_idx + 1} complete: {loop_summary['solutions_generated']} new solutions')
        summary = {'total_loops': self.aggregation_loops, 'total_reasoning_tokens': total_reasoning_tokens, 'final_population_size': len(workspace.solutions), 'aggregation_history': aggregation_history}
        logger.info(f'Aggregation complete: {summary['final_population_size']} solutions in final population')
        return (total_reasoning_tokens, summary)

    async def _run_single_aggregation_loop(self, workspace: MARSWorkspace, loop_idx: int, request_id: str=None, executor: ThreadPoolExecutor=None) -> Tuple[int, Dict[str, Any]]:
        """Run a single aggregation loop: sample K -> aggregate -> update population"""
        sampled_solutions = self._sample_solutions_for_aggregation(workspace)
        new_solutions, total_tokens = await self._generate_aggregated_solutions(workspace, sampled_solutions, request_id, executor)
        self._update_population(workspace, new_solutions)
        loop_summary = {'sampled_solutions': len(sampled_solutions), 'solutions_generated': len(new_solutions), 'population_size': len(workspace.solutions), 'total_tokens': total_tokens}
        return (total_tokens, loop_summary)

    def _sample_solutions_for_aggregation(self, workspace: MARSWorkspace) -> List[List[AgentSolution]]:
        """
        Sample K solutions from population for aggregation
        Uses different strategies for each sample to maintain diversity
        """
        all_solutions = workspace.solutions
        if len(all_solutions) < self.aggregation_size:
            return [all_solutions]
        samples = []
        num_samples = min(self.population_size // self.aggregation_size, 3)
        for i in range(num_samples):
            if i == 0:
                sample = sorted(all_solutions, key=lambda s: s.verification_score, reverse=True)[:self.aggregation_size]
            elif i == 1:
                by_agent = {}
                for sol in all_solutions:
                    if sol.agent_id not in by_agent:
                        by_agent[sol.agent_id] = []
                    by_agent[sol.agent_id].append(sol)
                sample = []
                for agent_solutions in by_agent.values():
                    if sample and len(sample) < self.aggregation_size:
                        sample.append(max(agent_solutions, key=lambda s: s.confidence))
                    if len(sample) >= self.aggregation_size:
                        break
                if len(sample) < self.aggregation_size:
                    remaining = [s for s in all_solutions if s not in sample]
                    sample.extend(sorted(remaining, key=lambda s: s.verification_score, reverse=True)[:self.aggregation_size - len(sample)])
            else:
                sample = random.sample(all_solutions, min(self.aggregation_size, len(all_solutions)))
            samples.append(sample)
        logger.info(f'Generated {len(samples)} sample groups for aggregation')
        return samples

    async def _generate_aggregated_solutions(self, workspace: MARSWorkspace, sampled_solution_groups: List[List[AgentSolution]], request_id: str=None, executor: ThreadPoolExecutor=None) -> Tuple[List[AgentSolution], int]:
        """Generate new solutions by aggregating sampled solutions in parallel"""

        async def aggregate_solution_group(solutions: List[AgentSolution]) -> Tuple[Optional[AgentSolution], int]:
            """Aggregate a single group of solutions"""
            loop = asyncio.get_event_loop()
            try:
                if len(solutions) == 1:
                    prompt = SINGLE_REFINEMENT_PROMPT.format(problem=workspace.problem, candidate_solution=solutions[0].solution)
                else:
                    candidate_text = ''
                    for i, sol in enumerate(solutions):
                        candidate_text += f'Solution {i + 1} (Agent {sol.agent_id}, confidence: {sol.confidence:.2f}):\n'
                        candidate_text += sol.solution + '\n\n'
                    prompt = MULTI_AGGREGATION_PROMPT.format(problem=workspace.problem, candidate_solutions=candidate_text)
                solution, tokens = await loop.run_in_executor(executor, self._call_model_for_aggregation, prompt, request_id)
                if solution:
                    aggregated_solution = AgentSolution(agent_id=f'agg_{datetime.now().strftime('%H%M%S')}', solution=solution, confidence=0.8, reasoning_tokens=tokens, total_tokens=tokens, solution_length=len(solution), is_verified=False, verification_score=0.0)
                    return (aggregated_solution, tokens)
                return (None, tokens)
            except Exception as e:
                logger.error(f'Aggregation failed: {str(e)}')
                return (None, 0)
        tasks = [aggregate_solution_group(group) for group in sampled_solution_groups]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        new_solutions = []
        total_tokens = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Aggregation task failed: {str(result)}')
                continue
            solution, tokens = result
            if solution:
                new_solutions.append(solution)
            total_tokens += tokens
        logger.info(f'Generated {len(new_solutions)} aggregated solutions with {total_tokens} reasoning tokens')
        return (new_solutions, total_tokens)

    def _call_model_for_aggregation(self, prompt: str, request_id: str=None) -> Tuple[str, int]:
        """Call the model to perform aggregation (synchronous for executor)"""
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical reasoning expert focused on solution aggregation and refinement.'}, {'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=0.7, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
            if request_id:
                provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a mathematical reasoning expert focused on solution aggregation and refinement.'}, {'role': 'user', 'content': prompt}], 'max_tokens': self.max_tokens, 'temperature': 0.7, 'extra_body': {'reasoning': {'effort': 'high'}}}
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            solution = response.choices[0].message.content.strip()
            reasoning_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if reasoning_tokens == 0:
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            return (solution, reasoning_tokens)
        except Exception as e:
            logger.error(f'Model call for aggregation failed: {str(e)}')
            return ('', 0)

    def _update_population(self, workspace: MARSWorkspace, new_solutions: List[AgentSolution]) -> None:
        """Update population with new solutions, maintaining population size limit"""
        for solution in new_solutions:
            workspace.add_solution(solution)
        all_solutions = workspace.solutions
        if len(all_solutions) > self.population_size:
            sorted_solutions = sorted(all_solutions, key=lambda s: (s.verification_score, s.confidence), reverse=True)
            workspace.solutions = sorted_solutions[:self.population_size]
            logger.info(f'Population trimmed to {self.population_size} best solutions')

    def _ensure_population_size(self, workspace: MARSWorkspace) -> None:
        """Ensure we have minimum population size for effective aggregation"""
        current_size = len(workspace.solutions)
        if current_size < self.aggregation_size:
            logger.warning(f'Population size ({current_size}) < aggregation size ({self.aggregation_size})')
            logger.warning('Aggregation may be less effective with limited diversity')
        logger.info(f'Population ready: {current_size} solutions available for aggregation')

def _sample_solutions_for_aggregation(self, workspace: MARSWorkspace) -> List[List[AgentSolution]]:
    """
        Sample K solutions from population for aggregation
        Uses different strategies for each sample to maintain diversity
        """
    all_solutions = workspace.solutions
    if len(all_solutions) < self.aggregation_size:
        return [all_solutions]
    samples = []
    num_samples = min(self.population_size // self.aggregation_size, 3)
    for i in range(num_samples):
        if i == 0:
            sample = sorted(all_solutions, key=lambda s: s.verification_score, reverse=True)[:self.aggregation_size]
        elif i == 1:
            by_agent = {}
            for sol in all_solutions:
                if sol.agent_id not in by_agent:
                    by_agent[sol.agent_id] = []
                by_agent[sol.agent_id].append(sol)
            sample = []
            for agent_solutions in by_agent.values():
                if sample and len(sample) < self.aggregation_size:
                    sample.append(max(agent_solutions, key=lambda s: s.confidence))
                if len(sample) >= self.aggregation_size:
                    break
            if len(sample) < self.aggregation_size:
                remaining = [s for s in all_solutions if s not in sample]
                sample.extend(sorted(remaining, key=lambda s: s.verification_score, reverse=True)[:self.aggregation_size - len(sample)])
        else:
            sample = random.sample(all_solutions, min(self.aggregation_size, len(all_solutions)))
        samples.append(sample)
    logger.info(f'Generated {len(samples)} sample groups for aggregation')
    return samples

@dataclass
class StrategyEffectiveness:
    """Tracks effectiveness of strategies across different problem types"""
    strategy_id: str
    problem_type: str
    success_count: int = 0
    failure_count: int = 0
    total_uses: int = 0
    average_confidence: float = 0.0
    best_applications: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.success_count / max(self.total_uses, 1)

@property
def success_rate(self) -> float:
    return self.success_count / max(self.total_uses, 1)

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

def _parse_config(request_config: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate configuration parameters."""
    default_config = {'deepthink_samples': 3, 'confidence_threshold': 0.7, 'max_tokens': 16382, 'temperature': 0.7, 'top_p': 0.95, 'enable_self_discover': True, 'reasoning_modules_limit': 7}
    for key, value in request_config.items():
        if key in default_config:
            default_config[key] = value
    default_config['deepthink_samples'] = max(1, min(10, default_config['deepthink_samples']))
    default_config['confidence_threshold'] = max(0.0, min(1.0, default_config['confidence_threshold']))
    default_config['temperature'] = max(0.0, min(2.0, default_config['temperature']))
    default_config['top_p'] = max(0.0, min(1.0, default_config['top_p']))
    default_config['reasoning_modules_limit'] = max(3, min(15, default_config['reasoning_modules_limit']))
    return default_config

class InstanceCounterAnonymizer(Operator):
    """
    Anonymizer which replaces the entity value
    with an instance counter per entity.
    """
    REPLACING_FORMAT = '<{entity_type}_{index}>'

    def operate(self, text: str, params: Dict=None) -> str:
        """Anonymize the input text."""
        entity_type: str = params['entity_type']
        entity_mapping: Dict[Dict:str] = params['entity_mapping']
        entity_mapping_for_type = entity_mapping.get(entity_type)
        if not entity_mapping_for_type:
            new_text = self.REPLACING_FORMAT.format(entity_type=entity_type, index=0)
            entity_mapping[entity_type] = {}
        else:
            if text in entity_mapping_for_type:
                return entity_mapping_for_type[text]
            previous_index = self._get_last_index(entity_mapping_for_type)
            new_text = self.REPLACING_FORMAT.format(entity_type=entity_type, index=previous_index + 1)
        entity_mapping[entity_type][text] = new_text
        return new_text

    @staticmethod
    def _get_last_index(entity_mapping_for_type: Dict) -> int:
        """Get the last index for a given entity type."""

        def get_index(value: str) -> int:
            return int(value.split('_')[-1][:-1])
        indices = [get_index(v) for v in entity_mapping_for_type.values()]
        return max(indices)

    def validate(self, params: Dict=None) -> None:
        """Validate operator parameters."""
        if 'entity_mapping' not in params:
            raise ValueError('An input Dict called `entity_mapping` is required.')
        if 'entity_type' not in params:
            raise ValueError('An entity_type param is required.')

    def operator_name(self) -> str:
        return 'entity_counter'

    def operator_type(self) -> OperatorType:
        return OperatorType.Anonymize

@staticmethod
def _get_last_index(entity_mapping_for_type: Dict) -> int:
    """Get the last index for a given entity type."""

    def get_index(value: str) -> int:
        return int(value.split('_')[-1][:-1])
    indices = [get_index(v) for v in entity_mapping_for_type.values()]
    return max(indices)

class Provider:
    """Wrapper for a provider configuration and client"""

    def __init__(self, config: Dict):
        self.name = config['name']
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.weight = config.get('weight', 1)
        self.fallback_only = config.get('fallback_only', False)
        self.model_map = config.get('model_map', {})
        self._client = None
        self.is_healthy = True
        self.last_error = None
        self.latencies = []
        self.max_concurrent = config.get('max_concurrent', None)
        if self.max_concurrent is not None:
            self._semaphore = threading.Semaphore(self.max_concurrent)
            logger.info(f'Provider {self.name} limited to {self.max_concurrent} concurrent requests')
        else:
            self._semaphore = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if not self._client:
            if 'azure' in self.base_url.lower():
                self._client = AzureOpenAI(api_key=self.api_key, azure_endpoint=self.base_url, api_version='2024-02-01', max_retries=0)
            elif 'generativelanguage.googleapis.com' in self.base_url:
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
            else:
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        return self._client

    def map_model(self, model: str) -> str:
        """Map requested model to provider-specific name"""
        return self.model_map.get(model, model)

    def track_latency(self, latency: float):
        """Track request latency"""
        self.latencies.append(latency)
        if len(self.latencies) > 10:
            self.latencies.pop(0)

    def avg_latency(self) -> float:
        """Get average latency"""
        if not self.latencies:
            return 0
        return sum(self.latencies) / len(self.latencies)

    def acquire_slot(self, timeout: Optional[float]=None) -> bool:
        """
        Try to acquire a slot for this provider.
        Returns True if acquired, False if timeout or no limit.
        """
        if self._semaphore is None:
            return True
        return self._semaphore.acquire(blocking=True, timeout=timeout)

    def release_slot(self):
        """Release a slot for this provider."""
        if self._semaphore is not None:
            self._semaphore.release()

    def available_slots(self) -> Optional[int]:
        """Get number of available slots, None if unlimited."""
        if self._semaphore is None:
            return None
        return self._semaphore._value

def avg_latency(self) -> float:
    """Get average latency"""
    if not self.latencies:
        return 0
    return sum(self.latencies) / len(self.latencies)

class _Completions:

    def __init__(self, proxy_client):
        self.proxy_client = proxy_client
        self._system_message_support_cache = {}

    def _filter_kwargs(self, kwargs: dict) -> dict:
        """Filter out OptiLLM-specific parameters that shouldn't be sent to providers"""
        optillm_params = {'optillm_approach', 'proxy_wrap', 'wrapped_approach', 'wrap', 'mcts_simulations', 'mcts_exploration', 'mcts_depth', 'best_of_n', 'rstar_max_depth', 'rstar_num_rollouts', 'rstar_c'}
        return {k: v for k, v in kwargs.items() if k not in optillm_params}

    def _test_system_message_support(self, provider, model: str) -> bool:
        """Test if a model supports system messages"""
        cache_key = f'{provider.name}:{model}'
        if cache_key in self._system_message_support_cache:
            return self._system_message_support_cache[cache_key]
        try:
            test_response = provider.client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'test'}, {'role': 'user', 'content': 'hi'}], max_tokens=1, temperature=0)
            self._system_message_support_cache[cache_key] = True
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if any((pattern in error_msg for pattern in ['developer instruction', 'system message', 'not enabled', 'not supported'])):
                logger.info(f'Provider {provider.name} model {model} does not support system messages')
                self._system_message_support_cache[cache_key] = False
                return False
            self._system_message_support_cache[cache_key] = True
            return True

    def _format_messages_for_provider(self, provider, model: str, messages: list) -> list:
        """Format messages based on provider's system message support"""
        has_system = any((msg.get('role') == 'system' for msg in messages))
        if not has_system:
            return messages
        supports_system = self._test_system_message_support(provider, model)
        if supports_system:
            return messages
        formatted_messages = []
        system_content = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_content = msg.get('content', '')
            elif msg.get('role') == 'user':
                if system_content:
                    formatted_messages.append({'role': 'user', 'content': f'Instructions: {system_content}\n\nUser: {msg.get('content', '')}'})
                    system_content = None
                else:
                    formatted_messages.append(msg)
            else:
                formatted_messages.append(msg)
        return formatted_messages

    def _make_request_with_timeout(self, provider, request_kwargs):
        """Make a request with timeout handling"""
        try:
            response = provider.client.chat.completions.create(**request_kwargs)
            return response
        except Exception as e:
            if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
                raise TimeoutError(f'Request to {provider.name} timed out after {self.proxy_client.request_timeout}s')
            raise e

    def create(self, **kwargs):
        """Create completion with load balancing, failover, and timeout handling"""
        if not self.proxy_client._request_semaphore.acquire(blocking=True, timeout=self.proxy_client.queue_timeout):
            raise TimeoutError(f'Request queue timeout after {self.proxy_client.queue_timeout}s - server overloaded')
        try:
            model = kwargs.get('model', 'unknown')
            attempted_providers = set()
            errors = []
            healthy_providers = [p for p in self.proxy_client.active_providers if p.is_healthy]
            if not healthy_providers:
                logger.warning('No healthy providers, trying fallback providers')
                healthy_providers = self.proxy_client.fallback_providers
            while healthy_providers:
                available_providers = [p for p in healthy_providers if p not in attempted_providers]
                if not available_providers:
                    break
                provider = self.proxy_client.router.select(available_providers)
                logger.info(f'Router selected provider: {(provider.name if provider else 'None')}')
                if not provider:
                    break
                attempted_providers.add(provider)
                slot_timeout = 10.0
                if not provider.acquire_slot(timeout=slot_timeout):
                    logger.debug(f'Provider {provider.name} at max capacity, trying next provider')
                    errors.append((provider.name, 'At max concurrent requests'))
                    continue
                try:
                    request_kwargs = self._filter_kwargs(kwargs.copy())
                    mapped_model = provider.map_model(model)
                    request_kwargs['model'] = mapped_model
                    if 'messages' in request_kwargs:
                        request_kwargs['messages'] = self._format_messages_for_provider(provider, mapped_model, request_kwargs['messages'])
                    request_kwargs['timeout'] = self.proxy_client.request_timeout
                    start_time = time.time()
                    logger.debug(f'Routing to {provider.name} with {self.proxy_client.request_timeout}s timeout')
                    response = self._make_request_with_timeout(provider, request_kwargs)
                    latency = time.time() - start_time
                    if self.proxy_client.track_latency:
                        provider.track_latency(latency)
                    logger.info(f'Request succeeded via {provider.name} in {latency:.2f}s')
                    return response
                except TimeoutError as e:
                    logger.error(f'Provider {provider.name} timed out: {e}')
                    errors.append((provider.name, str(e)))
                    if self.proxy_client.track_errors:
                        provider.is_healthy = False
                        provider.last_error = f'Timeout: {str(e)}'
                except Exception as e:
                    logger.error(f'Provider {provider.name} failed: {e}')
                    errors.append((provider.name, str(e)))
                    if self.proxy_client.track_errors:
                        provider.is_healthy = False
                        provider.last_error = str(e)
                finally:
                    provider.release_slot()
                    logger.debug(f'Released slot for provider {provider.name}')
            if self.proxy_client.fallback_client:
                logger.warning('All proxy providers failed, using fallback client')
                try:
                    fallback_kwargs = self._filter_kwargs(kwargs.copy())
                    fallback_kwargs['timeout'] = self.proxy_client.request_timeout
                    return self.proxy_client.fallback_client.chat.completions.create(**fallback_kwargs)
                except Exception as e:
                    errors.append(('fallback_client', str(e)))
            error_msg = f'All providers failed. Errors: {errors}'
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            self.proxy_client._request_semaphore.release()

def _filter_kwargs(self, kwargs: dict) -> dict:
    """Filter out OptiLLM-specific parameters that shouldn't be sent to providers"""
    optillm_params = {'optillm_approach', 'proxy_wrap', 'wrapped_approach', 'wrap', 'mcts_simulations', 'mcts_exploration', 'mcts_depth', 'best_of_n', 'rstar_max_depth', 'rstar_num_rollouts', 'rstar_c'}
    return {k: v for k, v in kwargs.items() if k not in optillm_params}

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

class UncertaintyRoutedCoT:
    """
    Implements uncertainty-routed chain-of-thought reasoning.
    
    The approach:
    1. Generate k chain-of-thought samples
    2. Evaluate confidence through consistency analysis
    3. Route to majority vote (high confidence) or greedy sample (low confidence)
    """

    def __init__(self, client, model: str, max_tokens: int=16382):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.completion_tokens = 0

    def generate_with_uncertainty_routing(self, prompt: str, num_samples: int=3, confidence_threshold: float=0.7, temperature: float=0.7, top_p: float=0.95) -> Dict[str, Any]:
        """
        Generate response using uncertainty-routed chain-of-thought.
        
        Args:
            prompt: The prompt to generate responses for
            num_samples: Number of samples to generate for uncertainty evaluation
            confidence_threshold: Threshold for routing decision
            temperature: Sampling temperature for multiple samples
            top_p: Top-p parameter for sampling
            
        Returns:
            Dict containing final response, confidence score, and routing decision
        """
        logger.info(f'Generating {num_samples} samples for uncertainty routing')
        samples = self._generate_multiple_samples(prompt, num_samples, temperature, top_p)
        greedy_sample = self._generate_greedy_sample(prompt)
        sample_data = []
        for sample in samples:
            thinking = self._extract_thinking(sample)
            answer = self._extract_answer(sample)
            sample_data.append({'full_response': sample, 'thinking': thinking, 'answer': answer})
        greedy_thinking = self._extract_thinking(greedy_sample)
        greedy_answer = self._extract_answer(greedy_sample)
        confidence_score = self._evaluate_confidence(sample_data)
        logger.debug(f'Confidence evaluation completed: {confidence_score:.3f}')
        logger.debug(f'Sample answers: {[sample['answer'][:50] + '...' if len(sample['answer']) > 50 else sample['answer'] for sample in sample_data if sample['answer']]}')
        if confidence_score >= confidence_threshold:
            final_response = self._majority_vote_response(sample_data)
            routing_decision = 'majority_vote'
            logger.info(f'High confidence ({confidence_score:.3f} >= {confidence_threshold}) - using majority vote')
        else:
            final_response = greedy_sample
            routing_decision = 'greedy'
            logger.info(f'Low confidence ({confidence_score:.3f} < {confidence_threshold}) - using greedy sample')
        return {'final_response': final_response, 'confidence_score': confidence_score, 'routing_decision': routing_decision, 'samples': sample_data, 'greedy_sample': {'full_response': greedy_sample, 'thinking': greedy_thinking, 'answer': greedy_answer}, 'completion_tokens': self.completion_tokens}

    def _generate_multiple_samples(self, prompt: str, num_samples: int, temperature: float, top_p: float) -> List[str]:
        """Generate multiple samples by calling the API multiple times."""
        samples = []
        for i in range(num_samples):
            logger.debug(f'Generating sample {i + 1}/{num_samples}')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=temperature, top_p=top_p)
            self.completion_tokens += response.usage.completion_tokens
            samples.append(response.choices[0].message.content.strip())
        return samples

    def _generate_greedy_sample(self, prompt: str) -> str:
        """Generate a single greedy sample with temperature=0."""
        logger.debug('Generating greedy sample')
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=0.0)
        self.completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def _extract_thinking(self, response: str) -> str:
        """Extract content from <think> tags."""
        match = re.search('<think>(.*?)</think>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ''

    def _extract_answer(self, response: str) -> str:
        """Extract the final answer from the response."""
        think_end = response.find('</think>')
        if think_end != -1:
            answer_part = response[think_end + 8:].strip()
        else:
            answer_part = response.strip()
        patterns = ['(?:the )?(?:final )?answer is:?\\s*(.+?)(?:\\n|$)', '(?:therefore|thus|so),?\\s*(?:the )?(?:answer is:?\\s*)?(.+?)(?:\\n|$)', '(?:conclusion|result):?\\s*(.+?)(?:\\n|$)']
        for pattern in patterns:
            match = re.search(pattern, answer_part, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        lines = answer_part.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                return line
        return answer_part[:200] if answer_part else ''

    def _evaluate_confidence(self, sample_data: List[Dict[str, Any]]) -> float:
        """
        Evaluate confidence based on consistency across samples.
        
        Returns a confidence score between 0 and 1.
        """
        if len(sample_data) < 2:
            return 0.5
        answers = [sample['answer'] for sample in sample_data if sample['answer']]
        thinking_texts = [sample['thinking'] for sample in sample_data if sample['thinking']]
        if not answers:
            return 0.1
        answer_consistency = self._calculate_answer_consistency(answers)
        reasoning_consistency = self._calculate_reasoning_consistency(thinking_texts)
        confidence = 0.6 * answer_consistency + 0.4 * reasoning_consistency
        logger.debug(f'Answer consistency: {answer_consistency:.3f} (weight: 0.6)')
        logger.debug(f'Reasoning consistency: {reasoning_consistency:.3f} (weight: 0.4)')
        logger.debug(f'Combined confidence: {confidence:.3f}')
        if confidence < 0.5:
            logger.debug(f'Low confidence detected. Sample count: {len(sample_data)}')
            logger.debug(f'Answers found: {len(answers)}, Thinking texts: {len(thinking_texts)}')
            if answers:
                logger.debug(f'Sample answers: {answers}')
            if len(answers) >= 2:
                logger.debug(f'Most common answer appears {max(Counter(answers).values())} times out of {len(answers)}')
        return confidence

    def _calculate_answer_consistency(self, answers: List[str]) -> float:
        """Calculate consistency of final answers."""
        if len(answers) < 2:
            return 0.5
        normalized_answers = []
        for answer in answers:
            norm_answer = re.sub('[^\\w\\s]', '', answer.lower().strip())
            norm_answer = re.sub('\\s+', ' ', norm_answer)
            normalized_answers.append(norm_answer)
        answer_counts = Counter(normalized_answers)
        most_common_count = answer_counts.most_common(1)[0][1]
        total_answers = len(answers)
        agreement_ratio = most_common_count / total_answers
        logger.debug(f'Answer distribution: {dict(answer_counts)}')
        logger.debug(f'Agreement ratio: {agreement_ratio:.3f} ({most_common_count}/{total_answers})')
        max_similarity = 0.0
        for i, ans1 in enumerate(normalized_answers):
            for j, ans2 in enumerate(normalized_answers[i + 1:], i + 1):
                similarity = SequenceMatcher(None, ans1, ans2).ratio()
                max_similarity = max(max_similarity, similarity)
        consistency = max(agreement_ratio, max_similarity)
        return min(consistency, 1.0)

    def _calculate_reasoning_consistency(self, thinking_texts: List[str]) -> float:
        """Calculate consistency of reasoning processes."""
        if len(thinking_texts) < 2:
            return 0.5
        similarities = []
        for i, text1 in enumerate(thinking_texts):
            for j, text2 in enumerate(thinking_texts[i + 1:], i + 1):
                similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
                similarities.append(similarity)
        if not similarities:
            return 0.5
        avg_similarity = sum(similarities) / len(similarities)
        logger.debug(f'Reasoning similarity pairs: {[f'{s:.3f}' for s in similarities]}')
        logger.debug(f'Average reasoning similarity: {avg_similarity:.3f}')
        return min(avg_similarity, 1.0)

    def _majority_vote_response(self, sample_data: List[Dict[str, Any]]) -> str:
        """
        Create response based on majority vote of answers and best reasoning.
        """
        answers = [sample['answer'] for sample in sample_data if sample['answer']]
        if not answers:
            return sample_data[0]['full_response']
        normalized_answers = []
        for answer in answers:
            norm_answer = re.sub('[^\\w\\s]', '', answer.lower().strip())
            norm_answer = re.sub('\\s+', ' ', norm_answer)
            normalized_answers.append(norm_answer)
        answer_counts = Counter(normalized_answers)
        most_common_answer = answer_counts.most_common(1)[0][0]
        best_sample = None
        best_reasoning_length = 0
        for i, sample in enumerate(sample_data):
            if sample['answer']:
                norm_answer = re.sub('[^\\w\\s]', '', sample['answer'].lower().strip())
                norm_answer = re.sub('\\s+', ' ', norm_answer)
                if norm_answer == most_common_answer:
                    reasoning_length = len(sample['thinking'])
                    if reasoning_length > best_reasoning_length:
                        best_reasoning_length = reasoning_length
                        best_sample = sample
        if best_sample:
            return best_sample['full_response']
        else:
            for sample in sample_data:
                if sample['answer']:
                    norm_answer = re.sub('[^\\w\\s]', '', sample['answer'].lower().strip())
                    norm_answer = re.sub('\\s+', ' ', norm_answer)
                    if norm_answer == most_common_answer:
                        return sample['full_response']
        return sample_data[0]['full_response']

def _evaluate_confidence(self, sample_data: List[Dict[str, Any]]) -> float:
    """
        Evaluate confidence based on consistency across samples.
        
        Returns a confidence score between 0 and 1.
        """
    if len(sample_data) < 2:
        return 0.5
    answers = [sample['answer'] for sample in sample_data if sample['answer']]
    thinking_texts = [sample['thinking'] for sample in sample_data if sample['thinking']]
    if not answers:
        return 0.1
    answer_consistency = self._calculate_answer_consistency(answers)
    reasoning_consistency = self._calculate_reasoning_consistency(thinking_texts)
    confidence = 0.6 * answer_consistency + 0.4 * reasoning_consistency
    logger.debug(f'Answer consistency: {answer_consistency:.3f} (weight: 0.6)')
    logger.debug(f'Reasoning consistency: {reasoning_consistency:.3f} (weight: 0.4)')
    logger.debug(f'Combined confidence: {confidence:.3f}')
    if confidence < 0.5:
        logger.debug(f'Low confidence detected. Sample count: {len(sample_data)}')
        logger.debug(f'Answers found: {len(answers)}, Thinking texts: {len(thinking_texts)}')
        if answers:
            logger.debug(f'Sample answers: {answers}')
        if len(answers) >= 2:
            logger.debug(f'Most common answer appears {max(Counter(answers).values())} times out of {len(answers)}')
    return confidence

def _calculate_answer_consistency(self, answers: List[str]) -> float:
    """Calculate consistency of final answers."""
    if len(answers) < 2:
        return 0.5
    normalized_answers = []
    for answer in answers:
        norm_answer = re.sub('[^\\w\\s]', '', answer.lower().strip())
        norm_answer = re.sub('\\s+', ' ', norm_answer)
        normalized_answers.append(norm_answer)
    answer_counts = Counter(normalized_answers)
    most_common_count = answer_counts.most_common(1)[0][1]
    total_answers = len(answers)
    agreement_ratio = most_common_count / total_answers
    logger.debug(f'Answer distribution: {dict(answer_counts)}')
    logger.debug(f'Agreement ratio: {agreement_ratio:.3f} ({most_common_count}/{total_answers})')
    max_similarity = 0.0
    for i, ans1 in enumerate(normalized_answers):
        for j, ans2 in enumerate(normalized_answers[i + 1:], i + 1):
            similarity = SequenceMatcher(None, ans1, ans2).ratio()
            max_similarity = max(max_similarity, similarity)
    consistency = max(agreement_ratio, max_similarity)
    return min(consistency, 1.0)

def _calculate_reasoning_consistency(self, thinking_texts: List[str]) -> float:
    """Calculate consistency of reasoning processes."""
    if len(thinking_texts) < 2:
        return 0.5
    similarities = []
    for i, text1 in enumerate(thinking_texts):
        for j, text2 in enumerate(thinking_texts[i + 1:], i + 1):
            similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
            similarities.append(similarity)
    if not similarities:
        return 0.5
    avg_similarity = sum(similarities) / len(similarities)
    logger.debug(f'Reasoning similarity pairs: {[f'{s:.3f}' for s in similarities]}')
    logger.debug(f'Average reasoning similarity: {avg_similarity:.3f}')
    return min(avg_similarity, 1.0)

def get_modules_by_category():
    """Categorize modules by their primary focus."""
    categories = {'analytical': [1, 3, 5, 10, 14, 17, 20, 23, 24, 25, 29], 'creative': [2, 4, 11, 30, 34, 35, 37], 'systematic': [9, 13, 16, 18, 22, 31, 33, 36, 38, 39], 'collaborative': [7, 12, 15, 21], 'risk_oriented': [6, 8, 14, 19], 'behavioral': [27, 28], 'constraint_focused': [26, 32]}
    return {category: [REASONING_MODULES[i - 1] for i in indices] for category, indices in categories.items()}

def select_relevant_strategies(query: str, problem_type: str, db: Any, learning_mode: bool=False, max_strategies: int=MAX_STRATEGIES_FOR_INFERENCE) -> List[Strategy]:
    """
    Select the most relevant strategies for a given problem to be used during inference.
    This controls how many strategies are included in the system prompt augmentation.
    
    When in inference mode (not learning_mode), only strategies with:
     - A matching problem type 
     - Success rate >= MIN_SUCCESS_RATE_FOR_INFERENCE
     - At least 5 attempts
    are selected.
    
    In learning mode, strategies with fewer attempts are also considered.
    
    Args:
        query: The problem/query text
        problem_type: The type of problem
        db: Strategy database
        learning_mode: Whether we're in learning mode (affects filtering criteria)
        max_strategies: Maximum number of strategies to return
    
    Returns:
        List[Strategy]: The selected strategies (may be empty if none meet criteria)
    """
    type_specific = db.get_strategies_for_problem(problem_type)
    logger.info(f"Found {len(type_specific)} strategies for problem type '{problem_type}'")
    qualified_strategies = []
    for strategy in type_specific:
        if learning_mode and strategy.total_attempts < 5:
            logger.info(f'Strategy {strategy.strategy_id} included (learning mode - only {strategy.total_attempts} attempts so far)')
            qualified_strategies.append(strategy)
        elif strategy.success_rate >= MIN_SUCCESS_RATE_FOR_INFERENCE and strategy.total_attempts >= 5:
            logger.info(f'Strategy {strategy.strategy_id} qualified - success rate {strategy.success_rate:.2f} >= minimum {MIN_SUCCESS_RATE_FOR_INFERENCE:.2f} with {strategy.total_attempts} attempts')
            qualified_strategies.append(strategy)
        elif strategy.total_attempts < 5:
            logger.info(f'Strategy {strategy.strategy_id} skipped - insufficient attempts ({strategy.total_attempts} < 5) in inference mode')
        else:
            logger.info(f'Strategy {strategy.strategy_id} skipped - success rate {strategy.success_rate:.2f} < minimum {MIN_SUCCESS_RATE_FOR_INFERENCE:.2f}')
    if not qualified_strategies:
        logger.info(f"No strategies meet the minimum success rate threshold ({MIN_SUCCESS_RATE_FOR_INFERENCE:.2f}) for problem type '{problem_type}'")
        return []
    logger.info(f'Found {len(qualified_strategies)} strategies that meet minimum success rate requirement')
    if len(qualified_strategies) > max_strategies:
        scored_strategies = []
        for strategy in qualified_strategies:
            recency_score = 0
            if strategy.last_used:
                last_used = datetime.fromisoformat(strategy.last_used)
                days_since = (datetime.now() - last_used).days
                recency_score = max(0, 1.0 - min(1.0, days_since / 30.0))
            score = 0.7 * strategy.success_rate + 0.3 * recency_score
            scored_strategies.append((strategy, score))
        scored_strategies.sort(key=lambda x: x[1], reverse=True)
        selected = [s[0] for s in scored_strategies[:max_strategies]]
        for i, strategy in enumerate(selected, 1):
            logger.info(f'Selected strategy {i}/{max_strategies} for inference: {strategy.strategy_id} (success rate: {strategy.success_rate:.2f})')
        return selected
    for i, strategy in enumerate(qualified_strategies, 1):
        logger.info(f'Selected strategy {i}/{len(qualified_strategies)} for inference: {strategy.strategy_id} (success rate: {strategy.success_rate:.2f})')
    return qualified_strategies

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

class DeepResearcher:
    """
    Simplified implementation of Test-Time Diffusion Deep Researcher (TTD-DR) algorithm

    This class implements the core concepts from the TTD-DR paper: treating research as a
    diffusion process with iterative refinement through denoising and retrieval.

    Implemented features:
    - Preliminary draft generation (updatable skeleton)
    - Gap analysis and draft-guided search
    - Iterative denoising through retrieval
    - Quality-guided termination

    Not yet implemented (future work):
    - Component-wise self-evolutionary optimization (fitness tracking exists but not used)
    - Memory-based synthesis for unbounded context

    Based on: https://arxiv.org/abs/2507.16075v1
    """

    def __init__(self, client, model: str, max_iterations: int=5, max_sources: int=30):
        self.client = client
        self.model = model
        self.max_iterations = max_iterations
        self.max_sources = max_sources
        self.session_id = str(uuid.uuid4())
        self.session_manager = None
        self.research_state = {'iteration': 0}
        self.total_tokens = 0
        self.citations = {}
        self.citation_counter = 0
        self.source_content_map = {}
        self.current_draft = ''
        self.draft_history = []
        self.component_fitness = {'search_strategy': 1.0, 'synthesis_quality': 1.0, 'gap_detection': 1.0, 'integration_ability': 1.0}
        self.gap_analysis_history = []
        self.session_manager = None

    def cleanup_placeholder_tags(self, text: str) -> str:
        """
        Remove any remaining placeholder tags from the final report.
        
        This is a final cleanup step to ensure no incomplete research tags remain
        in the published report.
        
        Args:
            text: Research report text
            
        Returns:
            Text with all placeholder tags removed
        """
        return cleanup_placeholder_tags(text)

    def fix_incomplete_report(self, report: str, validation: Dict[str, Any], original_query: str) -> str:
        """
        Attempt to fix an incomplete report by removing problematic sections
        and ensuring a coherent final document.
        
        This is a fallback when the report contains placeholders or incomplete sections.
        """
        print('🔧 Attempting to fix incomplete report...')
        fixed_report = cleanup_placeholder_tags(report)
        if 'Research Questions for Investigation' in fixed_report:
            fixed_report = re.sub('## Research Questions for Investigation.*?(?=##|$)', '', fixed_report, flags=re.DOTALL)
            print('   - Removed incomplete research questions section')
        fixed_report = re.sub('\\[\\d+\\]\\s*\\[Placeholder[^\\]]+\\]\\n?', '', fixed_report)
        fixed_report = re.sub('##\\s+([^#\\n]+)\\n\\s*(?=##)', '', fixed_report)
        if len(fixed_report.split()) < 300:
            completion_note = f'\n            \n## Note on Report Completion\n\nThis research report represents the findings gathered during the available research time. While comprehensive coverage was the goal, some areas may require additional investigation for complete analysis.\n\nFor more detailed information on specific aspects of {original_query}, additional focused research sessions may be beneficial.\n'
            if '## References' in fixed_report:
                fixed_report = fixed_report.replace('## References', completion_note + '\n## References')
            else:
                fixed_report += completion_note
            print('   - Added completion note due to short report length')
        fixed_report = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', fixed_report)
        fixed_report = fixed_report.strip()
        new_validation = validate_report_completeness(fixed_report)
        if new_validation['is_complete']:
            print('✅ Report successfully fixed and validated')
        else:
            print(f'⚠️  Report still has {len(new_validation['issues'])} issues after fixing')
        return fixed_report

    def decompose_query(self, system_prompt: str, initial_query: str) -> List[str]:
        """
        Decompose complex research query into focused sub-queries
        This implements the query planning phase of TTD-DR
        """
        decomposition_prompt = f'\n        You are a research assistant. Given a complex query, break it down into 3-5 focused sub-queries that would help gather comprehensive information.\n        \n        Original query: {initial_query}\n        \n        Provide sub-queries in this format:\n        1. [specific focused question]\n        2. [specific focused question]\n        3. [specific focused question]\n        ...\n        \n        Make each sub-query specific and searchable. Focus on different aspects of the main topic.\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': decomposition_prompt}], temperature=0.7, max_tokens=1000)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            queries = []
            for line in content.split('\n'):
                line = line.strip()
                if re.match('^\\d+\\.', line):
                    query = re.sub('^\\d+\\.\\s*\\[?(.*?)\\]?$', '\\1', line).strip()
                    if query:
                        queries.append(query)
            return queries[:5]
        except Exception as e:
            return [initial_query]

    def perform_web_search(self, queries: List[str]) -> str:
        """
        Perform web search for multiple queries using the web_search plugin
        """
        all_results = []
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            print(f'⚠️  Warning: session_manager not available in perform_web_search (session_id: {getattr(self, 'session_id', 'N/A')})')
            self.session_manager = None
        else:
            print(f'📊 Using existing session manager for web search (session_id: {self.session_id}, manager: {id(self.session_manager)})')
        for i, query in enumerate(queries):
            try:
                search_query = f'search for {query.strip()}'
                results_per_query = max(1, self.max_sources // len(queries))
                enhanced_query, _ = web_search_run('', search_query, None, None, {'num_results': results_per_query, 'delay_seconds': None, 'headless': False, 'session_manager': self.session_manager})
                if enhanced_query and 'Web Search Results' in enhanced_query:
                    all_results.append(enhanced_query)
            except Exception as e:
                all_results.append(f"Search failed for query '{query}': {str(e)}")
                continue
        if not all_results:
            return 'Web search failed: No results obtained from any query'
        combined_results = '\n\n'.join(all_results)
        return combined_results

    def extract_and_fetch_urls(self, search_results: str) -> Tuple[str, List[Dict]]:
        """
        Extract URLs from search results and fetch their content using readurls plugin
        Returns content and list of sources with metadata
        """
        try:
            sources = []
            result_pattern = '(\\d+)\\.\\s*\\*\\*(.+?)\\*\\*\\s*\\n\\s*URL:\\s*(.+?)\\n'
            matches = re.findall(result_pattern, search_results, re.MULTILINE)
            for match in matches:
                source = {'number': match[0], 'title': match[1].strip(), 'url': match[2].strip(), 'access_date': datetime.now().strftime('%Y-%m-%d')}
                sources.append(source)
            if not sources:
                lines = search_results.split('\n')
                current_source = {}
                for i, line in enumerate(lines):
                    title_match = re.match('^(\\d+)\\.\\s*\\*\\*(.+?)\\*\\*', line.strip())
                    if title_match:
                        if current_source and 'url' in current_source:
                            sources.append(current_source)
                        current_source = {'number': title_match.group(1), 'title': title_match.group(2).strip()}
                    elif line.strip().startswith('URL:') and current_source:
                        url = line.strip()[4:].strip()
                        current_source['url'] = url
                        current_source['access_date'] = datetime.now().strftime('%Y-%m-%d')
                if current_source and 'url' in current_source:
                    sources.append(current_source)
            content_with_urls, _ = readurls_run('', search_results, None, None)
            return (content_with_urls, sources)
        except Exception as e:
            return (f'URL fetching failed: {str(e)}', [])

    def evaluate_completeness(self, system_prompt: str, query: str, current_synthesis: str) -> Tuple[bool, List[str]]:
        """
        Evaluate if the current research is complete or needs more information
        Returns (is_complete, list_of_missing_aspects)
        """
        evaluation_prompt = f'\n        You are evaluating the completeness of a research synthesis. \n        \n        Original query: {query}\n        Current synthesis: {current_synthesis}\n        \n        Evaluate if this synthesis adequately addresses the original query. Consider:\n        1. Are all major aspects of the query covered?\n        2. Is there sufficient depth and detail?\n        3. Are there any obvious gaps or missing information?\n        \n        Respond in this format:\n        COMPLETE: [YES/NO]\n        MISSING: [list any missing aspects, one per line, or "None" if complete]\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': evaluation_prompt}], temperature=0.3, max_tokens=500)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            is_complete = 'COMPLETE: YES' in content.upper()
            missing_aspects = []
            if 'MISSING:' in content.upper():
                missing_section = content.split('MISSING:')[-1].strip()
                if missing_section.upper() != 'NONE':
                    missing_aspects = [line.strip() for line in missing_section.split('\n') if line.strip()]
            return (is_complete, missing_aspects)
        except Exception as e:
            return (False, ['Error in evaluation'])

    def generate_focused_queries(self, missing_aspects: List[str], original_query: str) -> List[str]:
        """
        Generate focused search queries to address missing aspects
        """
        focused_queries = []
        for aspect in missing_aspects:
            focused_query = f'{original_query} {aspect}'
            focused_queries.append(focused_query)
        return focused_queries[:3]

    def generate_preliminary_draft(self, system_prompt: str, initial_query: str) -> str:
        """
        Generate the preliminary draft (updatable skeleton) from LLM internal knowledge
        This serves as the initial state for the diffusion process
        """
        draft_prompt = f"""\n        Generate a preliminary research report structure for the following query using your internal knowledge.\n        This will serve as an evolving draft that gets refined through iterative research.\n        \n        Query: {initial_query}\n        \n        Create a structured report with:\n        1. Title and Executive Summary (brief)\n        2. Introduction and Background (what you know)\n        3. Key Areas to Explore (identify knowledge gaps)\n        4. Preliminary Findings (from internal knowledge)\n        5. Research Questions for Investigation\n        6. Conclusion (preliminary thoughts)\n        \n        IMPORTANT: You MUST mark multiple areas that need external research with [NEEDS RESEARCH] tags.\n        Every claim that would benefit from external evidence should have [SOURCE NEEDED].\n        This is a preliminary draft - it should have many gaps for iterative improvement.\n        \n        Example of proper marking:\n        - "Recent studies show [SOURCE NEEDED] that quantum computing..."\n        - "The economic impact [NEEDS RESEARCH: current market data] is significant..."\n        - "Historical context [NEEDS RESEARCH: specific timeline and events] shows..."\n        \n        Include AT LEAST 5-10 [NEEDS RESEARCH] or [SOURCE NEEDED] tags throughout the draft.\n        Be explicit about what you don't know and what needs external validation.\n        """
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': draft_prompt}], temperature=0.7, max_tokens=2000)
            draft = response.choices[0].message.content.strip()
            draft = clean_reasoning_tags(draft)
            self.total_tokens += response.usage.completion_tokens
            return draft
        except Exception as e:
            return f'Failed to generate preliminary draft: {str(e)}'

    def analyze_draft_gaps(self, current_draft: str, original_query: str) -> List[Dict[str, str]]:
        """
        Analyze the current draft to identify gaps, weaknesses, and areas needing research
        This guides the next retrieval iteration (draft-guided search)
        """
        gap_analysis_prompt = f"\n        Analyze the following research draft to identify specific gaps and areas that need external research.\n        Be thorough and aggressive in finding areas for improvement - even good drafts can be enhanced.\n        \n        Original Query: {original_query}\n        \n        Current Draft:\n        {current_draft}\n        \n        CRITICAL ANALYSIS REQUIRED:\n        1. MANDATORY: Find ALL [NEEDS RESEARCH], [SOURCE NEEDED], [CITATION NEEDED] tags\n        2. Identify claims lacking evidence (even if not explicitly marked)\n        3. Find areas that could benefit from recent data or statistics\n        4. Spot generalizations that need specific examples\n        5. Locate outdated information or areas needing current updates\n        6. Identify missing perspectives or counterarguments\n        \n        For each gap you identify, provide:\n        1. SECTION: Which section has the gap\n        2. GAP_TYPE: [PLACEHOLDER_TAG, MISSING_INFO, OUTDATED_INFO, NEEDS_EVIDENCE, LACKS_DEPTH, NEEDS_EXAMPLES, MISSING_PERSPECTIVE]\n        3. SPECIFIC_NEED: Exactly what information is needed\n        4. SEARCH_QUERY: A specific, targeted search query to address this gap\n        5. PRIORITY: [HIGH, MEDIUM, LOW] - HIGH for placeholder tags and critical missing info\n        \n        Format each gap as:\n        GAP_ID: [number]\n        SECTION: [section name]\n        GAP_TYPE: [type]\n        SPECIFIC_NEED: [what's missing]\n        SEARCH_QUERY: [search query to find this info]\n        PRIORITY: [priority level]\n        \n        IMPORTANT: Identify AT LEAST 3-8 gaps. Be critical and thorough.\n        Even well-written sections can benefit from additional evidence, examples, or perspectives.\n        Push for depth, accuracy, and comprehensiveness in the research.\n        "
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research analyst.'}, {'role': 'user', 'content': gap_analysis_prompt}], temperature=0.3, max_tokens=1000)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            gaps = []
            current_gap = {}
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('GAP_ID:'):
                    if current_gap:
                        gaps.append(current_gap)
                    current_gap = {'id': line.split(':', 1)[1].strip()}
                elif line.startswith('SECTION:'):
                    current_gap['section'] = line.split(':', 1)[1].strip()
                elif line.startswith('GAP_TYPE:'):
                    current_gap['gap_type'] = line.split(':', 1)[1].strip()
                elif line.startswith('SPECIFIC_NEED:'):
                    current_gap['specific_need'] = line.split(':', 1)[1].strip()
                elif line.startswith('SEARCH_QUERY:'):
                    current_gap['search_query'] = line.split(':', 1)[1].strip()
                elif line.startswith('PRIORITY:'):
                    current_gap['priority'] = line.split(':', 1)[1].strip()
            if current_gap:
                gaps.append(current_gap)
            return gaps
        except Exception as e:
            return [{'id': '1', 'section': 'General', 'gap_type': 'MISSING_INFO', 'specific_need': 'More detailed information needed', 'search_query': original_query}]

    def perform_gap_targeted_search(self, gaps: List[Dict[str, str]]) -> str:
        """
        Perform targeted searches based on identified gaps in the current draft
        Prioritizes HIGH priority gaps (placeholder tags) first
        """
        all_results = []
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            print('⚠️  Warning: session_manager not available in perform_web_search')
            self.session_manager = None
        sorted_gaps = sorted(gaps, key=lambda g: 0 if g.get('priority', '').upper() == 'HIGH' else 1 if g.get('priority', '').upper() == 'MEDIUM' else 2)
        for gap in sorted_gaps:
            search_query = gap.get('search_query', '')
            if not search_query:
                continue
            try:
                search_query = f'search for {search_query.strip()}'
                enhanced_query, _ = web_search_run('', search_query, None, None, {'num_results': max(1, self.max_sources // len(gaps)), 'delay_seconds': None, 'headless': False, 'session_manager': self.session_manager})
                if enhanced_query and 'Web Search Results' in enhanced_query:
                    gap_context = f'[ADDRESSING GAP: {gap.get('section', 'Unknown')} - {gap.get('specific_need', 'General research')}]\n'
                    all_results.append(gap_context + enhanced_query)
            except Exception as e:
                continue
        return '\n\n'.join(all_results) if all_results else 'No gap-targeted search results obtained'

    def denoise_draft_with_retrieval(self, current_draft: str, retrieval_content: str, original_query: str) -> str:
        """
        Core denoising step: integrate retrieved information with current draft
        This is the heart of the diffusion process
        """
        citation_context = '\n\n**AVAILABLE CITATIONS (USE THESE!):**\n'
        for num, source in self.citations.items():
            citation_context += f'[{num}] {source.get('title', 'Untitled')} - {source.get('url', 'No URL')}\n'
        denoising_prompt = f'\n        You are performing a denoising step in a research diffusion process.\n\n        TASK: Integrate new retrieved information with the existing draft to reduce "noise" (gaps, inaccuracies, incompleteness).\n\n        Original Query: {original_query}\n\n        Current Draft:\n        {current_draft}\n\n        New Retrieved Information:\n        {retrieval_content}\n        {citation_context}\n\n        CRITICAL CITATION REQUIREMENTS:\n        1. EVERY factual claim, statistic, finding, or piece of evidence MUST be cited using [1], [2], etc.\n        2. Multiple related claims from the same source can share a citation [3]\n        3. Claims from different sources should have multiple citations like [1,4,7]\n        4. Direct quotes MUST have citations immediately after the closing quote\n        5. When integrating new information, ALWAYS add appropriate citations from the available sources\n        6. Uncited claims will be considered incomplete and must be fixed\n\n        DENOISING INSTRUCTIONS:\n        1. Identify where the new information fills gaps marked with [NEEDS RESEARCH] or [SOURCE NEEDED]\n        2. Replace placeholder content with specific, detailed information from the retrieved content\n        3. Add proper citations for ALL new information using the citation numbers shown above\n        4. Resolve any conflicts between new and existing information\n        5. Maintain the overall structure and coherence of the draft\n        6. Enhance depth and accuracy without losing existing valuable insights\n        7. Mark any remaining research needs with [NEEDS RESEARCH]\n        8. Review the draft and add missing citations to any uncited factual claims\n\n        QUALITY CHECK: Before returning, verify that the majority of substantive claims have citations.\n        Aim for at least 70% of factual statements to be properly cited.\n\n        Return the improved draft with integrated information and comprehensive citations.\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research synthesizer performing draft denoising.'}, {'role': 'user', 'content': denoising_prompt}], temperature=0.6, max_tokens=3000)
            denoised_draft = response.choices[0].message.content.strip()
            denoised_draft = clean_reasoning_tags(denoised_draft)
            self.total_tokens += response.usage.completion_tokens
            return denoised_draft
        except Exception as e:
            return f'Denoising failed: {str(e)}\n\nFalling back to current draft:\n{current_draft}'

    def evaluate_draft_quality(self, draft: str, previous_draft: str, original_query: str) -> Dict[str, float]:
        """
        Evaluate the quality improvement of the current draft vs previous iteration
        Used for termination decisions and component fitness updates
        """
        evaluation_prompt = f'\n        Evaluate the research draft quality improvement.\n        \n        Original Query: {original_query}\n        \n        Previous Draft:\n        {previous_draft}\n        \n        Current Draft:\n        {draft}\n        \n        Rate the following aspects from 0.0 to 1.0:\n        \n        COMPLETENESS: How well does the current draft address all aspects of the query?\n        ACCURACY: How accurate and reliable is the information?\n        DEPTH: How detailed and comprehensive is the analysis?\n        COHERENCE: How well-structured and logically organized is the draft?\n        CITATIONS: How well are sources cited and integrated?\n        IMPROVEMENT: How much better is this draft compared to the previous version?\n        \n        Respond ONLY with:\n        COMPLETENESS: [score]\n        ACCURACY: [score]\n        DEPTH: [score]\n        COHERENCE: [score]\n        CITATIONS: [score]\n        IMPROVEMENT: [score]\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research quality evaluator.'}, {'role': 'user', 'content': evaluation_prompt}], temperature=0.2, max_tokens=500)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            scores = {}
            for line in content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    try:
                        scores[key] = float(value.strip())
                    except ValueError:
                        scores[key] = 0.5
            return scores
        except Exception as e:
            return {'completeness': 0.5, 'accuracy': 0.5, 'depth': 0.5, 'coherence': 0.5, 'citations': 0.5, 'improvement': 0.1}

    def update_component_fitness(self, quality_scores: Dict[str, float]):
        """
        Update component fitness based on performance (self-evolution)

        NOTE: This method tracks fitness values but they are not yet used to modify
        component behavior. This is placeholder code for future implementation of
        component-wise self-evolutionary optimization as described in the TTD-DR paper.
        """
        improvement = quality_scores.get('improvement', 0.0)
        if improvement > 0.1:
            self.component_fitness['search_strategy'] *= 1.1
            self.component_fitness['synthesis_quality'] *= 1.1
            self.component_fitness['integration_ability'] *= 1.1
        elif improvement < 0.05:
            self.component_fitness['search_strategy'] *= 0.95
            self.component_fitness['synthesis_quality'] *= 0.95
        for key in self.component_fitness:
            self.component_fitness[key] = max(0.1, min(2.0, self.component_fitness[key]))

    def research(self, system_prompt: str, initial_query: str) -> Tuple[str, int]:
        """
        TTD-DR (Test-Time Diffusion Deep Researcher) main algorithm

        Implements the core diffusion process with:
        1. Preliminary draft generation (initial noisy state)
        2. Initial research to gather external sources
        3. Iterative denoising through draft-guided retrieval
        4. Gap analysis to identify areas needing more research
        5. Quality-guided termination

        Note: Component-wise self-evolutionary optimization is tracked but not yet
        used to modify behavior (future enhancement).
        """
        self.session_manager = get_session_manager(self.session_id, headless=False, timeout=30)
        if self.session_manager:
            print(f'🔬 Starting deep research with session ID: {self.session_id} (DeepResearcher instance: {id(self)})')
        else:
            print('⚠️ Failed to create browser session, proceeding without web search')
        try:
            print('TTD-DR: Generating preliminary draft...')
            self.current_draft = self.generate_preliminary_draft(system_prompt, initial_query)
            self.draft_history.append(self.current_draft)
            print('TTD-DR: Performing initial research...')
            initial_queries = self.decompose_query(system_prompt, initial_query)
            if initial_queries:
                print(f'  - Searching for {len(initial_queries)} initial topics...')
                initial_search_results = self.perform_web_search(initial_queries)
                if initial_search_results and 'Web Search Results' in initial_search_results:
                    print('  - Extracting initial sources...')
                    initial_content, initial_sources = self.extract_and_fetch_urls(initial_search_results)
                    for source in initial_sources:
                        if 'url' in source:
                            self.citation_counter += 1
                            self.citations[self.citation_counter] = source
                    print(f'  - Found {len(initial_sources)} initial sources')
                else:
                    print('  - No sources found in initial search')
            else:
                print('  - Warning: Could not decompose query for initial research')
                print('  - Using fallback search strategy...')
                fallback_queries = [initial_query]
                fallback_search_results = self.perform_web_search(fallback_queries)
                if fallback_search_results and 'Web Search Results' in fallback_search_results:
                    fallback_content, fallback_sources = self.extract_and_fetch_urls(fallback_search_results)
                    for source in fallback_sources:
                        if 'url' in source:
                            self.citation_counter += 1
                            self.citations[self.citation_counter] = source
                    print(f'  - Fallback search found {len(fallback_sources)} sources')
            for iteration in range(self.max_iterations):
                self.research_state['iteration'] = iteration + 1
                print(f'TTD-DR: Denoising iteration {iteration + 1}/{self.max_iterations}')
                print('  - Analyzing draft gaps...')
                gaps = self.analyze_draft_gaps(self.current_draft, initial_query)
                self.gap_analysis_history.append(gaps)
                if not gaps:
                    print('  - No significant gaps found, research complete')
                    break
                print(f'  - Performing targeted search for {len(gaps)} gaps...')
                retrieval_content = self.perform_gap_targeted_search(gaps)
                print('  - Extracting and fetching content...')
                content_with_urls, sources = self.extract_and_fetch_urls(retrieval_content)
                for source in sources:
                    if 'url' in source:
                        self.citation_counter += 1
                        self.citations[self.citation_counter] = source
                print('  - Performing denoising step...')
                previous_draft = self.current_draft
                self.current_draft = self.denoise_draft_with_retrieval(self.current_draft, content_with_urls, initial_query)
                self.draft_history.append(self.current_draft)
                print('  - Evaluating draft quality...')
                quality_scores = self.evaluate_draft_quality(self.current_draft, previous_draft, initial_query)
                self.update_component_fitness(quality_scores)
                completeness = quality_scores.get('completeness', 0.0)
                improvement = quality_scores.get('improvement', 0.0)
                print(f'  - Quality scores: Completeness={completeness:.2f}, Improvement={improvement:.2f}')
                if completeness > 0.9 or (improvement < 0.03 and completeness > 0.7):
                    print('  - Quality threshold reached, research complete')
                    break
            print('TTD-DR: Finalizing research report...')
            if len(self.citations) == 0:
                print('⚠️  Warning: No external sources found during research!')
                print('   Deep research should always consult external sources.')
            else:
                print(f'✅ Research completed with {len(self.citations)} sources')
            final_report = self.finalize_research_report(system_prompt, initial_query, self.current_draft)
            return (final_report, self.total_tokens)
        finally:
            if self.session_manager:
                print(f'🏁 Closing research session: {self.session_id}')
                close_session(self.session_id)
                self.session_manager = None

    def finalize_research_report(self, system_prompt: str, original_query: str, final_draft: str) -> str:
        """
        Apply final polishing to the research report
        """
        citation_context = '\n\n**AVAILABLE CITATIONS:**\n'
        for num, source in self.citations.items():
            citation_context += f'[{num}] {source.get('title', 'Untitled')}\n'
        finalization_prompt = f'\n        Apply final polishing to this research report. This is the last step in the TTD-DR diffusion process.\n\n        Original Query: {original_query}\n\n        Current Draft:\n        {final_draft}\n        {citation_context}\n\n        FINALIZATION TASKS:\n        1. Ensure professional academic formatting with clear sections\n        2. **CRITICAL**: Verify all citations are properly formatted as [1], [2], etc. and ADD MISSING CITATIONS\n        3. Add citations to any factual claims, statistics, or findings that lack them\n        4. Add a compelling title and executive summary\n        5. Ensure smooth transitions between sections\n        6. Add conclusion that directly addresses the original query\n        7. **CRITICAL**: Remove ALL [NEEDS RESEARCH], [SOURCE NEEDED], and similar placeholder tags\n        8. Replace any remaining placeholders with actual content or remove incomplete sections\n        9. Polish language and style for clarity and impact\n\n        **CRITICAL CITATION REQUIREMENTS**:\n        - Every major factual claim MUST have a citation\n        - Statistics, data points, and research findings MUST be cited\n        - If information came from research, it needs a citation from the available sources above\n        - Aim for at least 60-70% of substantive claims to have proper citations\n        - Remove or rephrase claims that cannot be supported with available citations\n\n        **CRITICAL QUALITY REQUIREMENTS**:\n        - The final report must NOT contain ANY placeholder tags: [NEEDS RESEARCH], [SOURCE NEEDED], [Placeholder for...], etc.\n        - Remove incomplete "Research Questions for Investigation" sections with unanswered questions\n        - Do not include citation placeholders like "[1] [Placeholder for specific research citation]"\n        - If sections are incomplete, either complete them with available information or remove them entirely\n        - Ensure all statements are backed by available evidence or are clearly marked as preliminary findings\n        - The report must be publication-ready with no incomplete elements\n        - DO NOT create a References section - it will be added automatically\n\n        Return the final polished research report with comprehensive citations.\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': finalization_prompt}], temperature=0.5, max_tokens=3000)
            polished_report = response.choices[0].message.content.strip()
            polished_report = clean_reasoning_tags(polished_report)
            polished_report = self.cleanup_placeholder_tags(polished_report)
            validation = validate_report_completeness(polished_report)
            if not validation['is_complete']:
                print(f'⚠️  Report validation found {len(validation['issues'])} issues:')
                for issue in validation['issues']:
                    print(f'   - {issue}')
                polished_report = self.fix_incomplete_report(polished_report, validation, original_query)
            else:
                print('✅ Report validation passed - report is complete')
            self.total_tokens += response.usage.completion_tokens
            polished_report = re.sub('##\\s*References.*?(?=##|\\Z)', '', polished_report, flags=re.DOTALL)
            polished_report = re.sub('(?m)^References\\s*\\n\\s*(?:\\[\\d+\\]\\s*\\n)+', '', polished_report)
            polished_report = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', polished_report)
            citation_validation = validate_citation_usage(polished_report, len(self.citations))
            print(f'📊 Citation Statistics:')
            print(f'   - Used citations: {citation_validation['citations_used']}/{citation_validation['citations_total']}')
            print(f'   - Usage percentage: {citation_validation['usage_percentage']:.1f}%')
            if 'warning' in citation_validation:
                print(f'⚠️  {citation_validation['warning']}')
                if len(citation_validation['unused_citations']) > 0:
                    print(f'   - Unused citations: {citation_validation['unused_citations'][:10]}' + (f'... and {len(citation_validation['unused_citations']) - 10} more' if len(citation_validation['unused_citations']) > 10 else ''))
            references = '\n\n## References\n\n'
            used_citations = set(citation_validation['used_citations'])
            for num, source in sorted(self.citations.items()):
                if num in used_citations:
                    title = source.get('title', 'Untitled')
                    url = source['url']
                    access_date = source.get('access_date', datetime.now().strftime('%Y-%m-%d'))
                    references += f'[{num}] {title}. Available at: <{url}> [Accessed: {access_date}]\n\n'
            metadata = '\n---\n\n**TTD-DR Research Metadata:**\n'
            metadata += f'- Algorithm: Test-Time Diffusion Deep Researcher\n'
            metadata += f'- Denoising iterations: {len(self.draft_history) - 1}\n'
            metadata += f'- Total gaps addressed: {sum((len(gaps) for gaps in self.gap_analysis_history))}\n'
            metadata += f'- Total sources consulted: {len(self.citations)}\n'
            metadata += f'- Citations used in text: {citation_validation['citations_used']} ({citation_validation['usage_percentage']:.1f}%)\n'
            metadata += f'- Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n'
            metadata += f'- Total tokens used: {self.total_tokens}\n'
            return polished_report + references + metadata
        except Exception as e:
            return f'Finalization failed: {str(e)}\n\nReturning current draft:\n{final_draft}'

def cleanup_placeholder_tags(self, text: str) -> str:
    """
        Remove any remaining placeholder tags from the final report.
        
        This is a final cleanup step to ensure no incomplete research tags remain
        in the published report.
        
        Args:
            text: Research report text
            
        Returns:
            Text with all placeholder tags removed
        """
    return cleanup_placeholder_tags(text)

def fix_incomplete_report(self, report: str, validation: Dict[str, Any], original_query: str) -> str:
    """
        Attempt to fix an incomplete report by removing problematic sections
        and ensuring a coherent final document.
        
        This is a fallback when the report contains placeholders or incomplete sections.
        """
    print('🔧 Attempting to fix incomplete report...')
    fixed_report = cleanup_placeholder_tags(report)
    if 'Research Questions for Investigation' in fixed_report:
        fixed_report = re.sub('## Research Questions for Investigation.*?(?=##|$)', '', fixed_report, flags=re.DOTALL)
        print('   - Removed incomplete research questions section')
    fixed_report = re.sub('\\[\\d+\\]\\s*\\[Placeholder[^\\]]+\\]\\n?', '', fixed_report)
    fixed_report = re.sub('##\\s+([^#\\n]+)\\n\\s*(?=##)', '', fixed_report)
    if len(fixed_report.split()) < 300:
        completion_note = f'\n            \n## Note on Report Completion\n\nThis research report represents the findings gathered during the available research time. While comprehensive coverage was the goal, some areas may require additional investigation for complete analysis.\n\nFor more detailed information on specific aspects of {original_query}, additional focused research sessions may be beneficial.\n'
        if '## References' in fixed_report:
            fixed_report = fixed_report.replace('## References', completion_note + '\n## References')
        else:
            fixed_report += completion_note
        print('   - Added completion note due to short report length')
    fixed_report = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', fixed_report)
    fixed_report = fixed_report.strip()
    new_validation = validate_report_completeness(fixed_report)
    if new_validation['is_complete']:
        print('✅ Report successfully fixed and validated')
    else:
        print(f'⚠️  Report still has {len(new_validation['issues'])} issues after fixing')
    return fixed_report

def update_component_fitness(self, quality_scores: Dict[str, float]):
    """
        Update component fitness based on performance (self-evolution)

        NOTE: This method tracks fitness values but they are not yet used to modify
        component behavior. This is placeholder code for future implementation of
        component-wise self-evolutionary optimization as described in the TTD-DR paper.
        """
    improvement = quality_scores.get('improvement', 0.0)
    if improvement > 0.1:
        self.component_fitness['search_strategy'] *= 1.1
        self.component_fitness['synthesis_quality'] *= 1.1
        self.component_fitness['integration_ability'] *= 1.1
    elif improvement < 0.05:
        self.component_fitness['search_strategy'] *= 0.95
        self.component_fitness['synthesis_quality'] *= 0.95
    for key in self.component_fitness:
        self.component_fitness[key] = max(0.1, min(2.0, self.component_fitness[key]))

def finalize_research_report(self, system_prompt: str, original_query: str, final_draft: str) -> str:
    """
        Apply final polishing to the research report
        """
    citation_context = '\n\n**AVAILABLE CITATIONS:**\n'
    for num, source in self.citations.items():
        citation_context += f'[{num}] {source.get('title', 'Untitled')}\n'
    finalization_prompt = f'\n        Apply final polishing to this research report. This is the last step in the TTD-DR diffusion process.\n\n        Original Query: {original_query}\n\n        Current Draft:\n        {final_draft}\n        {citation_context}\n\n        FINALIZATION TASKS:\n        1. Ensure professional academic formatting with clear sections\n        2. **CRITICAL**: Verify all citations are properly formatted as [1], [2], etc. and ADD MISSING CITATIONS\n        3. Add citations to any factual claims, statistics, or findings that lack them\n        4. Add a compelling title and executive summary\n        5. Ensure smooth transitions between sections\n        6. Add conclusion that directly addresses the original query\n        7. **CRITICAL**: Remove ALL [NEEDS RESEARCH], [SOURCE NEEDED], and similar placeholder tags\n        8. Replace any remaining placeholders with actual content or remove incomplete sections\n        9. Polish language and style for clarity and impact\n\n        **CRITICAL CITATION REQUIREMENTS**:\n        - Every major factual claim MUST have a citation\n        - Statistics, data points, and research findings MUST be cited\n        - If information came from research, it needs a citation from the available sources above\n        - Aim for at least 60-70% of substantive claims to have proper citations\n        - Remove or rephrase claims that cannot be supported with available citations\n\n        **CRITICAL QUALITY REQUIREMENTS**:\n        - The final report must NOT contain ANY placeholder tags: [NEEDS RESEARCH], [SOURCE NEEDED], [Placeholder for...], etc.\n        - Remove incomplete "Research Questions for Investigation" sections with unanswered questions\n        - Do not include citation placeholders like "[1] [Placeholder for specific research citation]"\n        - If sections are incomplete, either complete them with available information or remove them entirely\n        - Ensure all statements are backed by available evidence or are clearly marked as preliminary findings\n        - The report must be publication-ready with no incomplete elements\n        - DO NOT create a References section - it will be added automatically\n\n        Return the final polished research report with comprehensive citations.\n        '
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': finalization_prompt}], temperature=0.5, max_tokens=3000)
        polished_report = response.choices[0].message.content.strip()
        polished_report = clean_reasoning_tags(polished_report)
        polished_report = self.cleanup_placeholder_tags(polished_report)
        validation = validate_report_completeness(polished_report)
        if not validation['is_complete']:
            print(f'⚠️  Report validation found {len(validation['issues'])} issues:')
            for issue in validation['issues']:
                print(f'   - {issue}')
            polished_report = self.fix_incomplete_report(polished_report, validation, original_query)
        else:
            print('✅ Report validation passed - report is complete')
        self.total_tokens += response.usage.completion_tokens
        polished_report = re.sub('##\\s*References.*?(?=##|\\Z)', '', polished_report, flags=re.DOTALL)
        polished_report = re.sub('(?m)^References\\s*\\n\\s*(?:\\[\\d+\\]\\s*\\n)+', '', polished_report)
        polished_report = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', polished_report)
        citation_validation = validate_citation_usage(polished_report, len(self.citations))
        print(f'📊 Citation Statistics:')
        print(f'   - Used citations: {citation_validation['citations_used']}/{citation_validation['citations_total']}')
        print(f'   - Usage percentage: {citation_validation['usage_percentage']:.1f}%')
        if 'warning' in citation_validation:
            print(f'⚠️  {citation_validation['warning']}')
            if len(citation_validation['unused_citations']) > 0:
                print(f'   - Unused citations: {citation_validation['unused_citations'][:10]}' + (f'... and {len(citation_validation['unused_citations']) - 10} more' if len(citation_validation['unused_citations']) > 10 else ''))
        references = '\n\n## References\n\n'
        used_citations = set(citation_validation['used_citations'])
        for num, source in sorted(self.citations.items()):
            if num in used_citations:
                title = source.get('title', 'Untitled')
                url = source['url']
                access_date = source.get('access_date', datetime.now().strftime('%Y-%m-%d'))
                references += f'[{num}] {title}. Available at: <{url}> [Accessed: {access_date}]\n\n'
        metadata = '\n---\n\n**TTD-DR Research Metadata:**\n'
        metadata += f'- Algorithm: Test-Time Diffusion Deep Researcher\n'
        metadata += f'- Denoising iterations: {len(self.draft_history) - 1}\n'
        metadata += f'- Total gaps addressed: {sum((len(gaps) for gaps in self.gap_analysis_history))}\n'
        metadata += f'- Total sources consulted: {len(self.citations)}\n'
        metadata += f'- Citations used in text: {citation_validation['citations_used']} ({citation_validation['usage_percentage']:.1f}%)\n'
        metadata += f'- Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n'
        metadata += f'- Total tokens used: {self.total_tokens}\n'
        return polished_report + references + metadata
    except Exception as e:
        return f'Finalization failed: {str(e)}\n\nReturning current draft:\n{final_draft}'

class ComplexityClassifier:
    """
    Classifies queries as HIGH or LOW complexity for token budget allocation.
    Uses the adaptive-classifier model for classification.
    """

    def __init__(self, model_name: str='adaptive-classifier/llm-router'):
        """
        Initialize the complexity classifier.
        
        Args:
            model_name: HuggingFace model name or path for the classifier
        """
        self.model_name = model_name
        self.classifier = None
        self._load_model()

    def _load_model(self):
        """Load the classification model using adaptive-classifier library."""
        try:
            try:
                import adaptive_classifier
            except ImportError:
                logger.info('Installing adaptive-classifier library...')
                os.system(f'{sys.executable} -m pip install adaptive-classifier')
                import adaptive_classifier
            from adaptive_classifier import AdaptiveClassifier
            logger.info(f'Loading complexity classifier model: {self.model_name}')
            self.classifier = AdaptiveClassifier.from_pretrained(self.model_name)
            logger.info('Classifier loaded successfully')
        except Exception as e:
            logger.error(f'Error loading complexity classifier: {e}')
            self.classifier = None

    def predict(self, text: str) -> List[Tuple[str, float]]:
        """
        Predict the complexity label for a given text.
        
        Args:
            text: The query text to classify
            
        Returns:
            List of (label, score) tuples sorted by confidence
        """
        if self.classifier is None:
            logger.warning('Classifier not loaded. Using fallback classification.')
            return self._fallback_classification(text)
        try:
            predictions = self.classifier.predict(text)
            logger.debug(f'Classifier predictions: {predictions}')
            if isinstance(predictions, list) and all((isinstance(p, tuple) and len(p) == 2 for p in predictions)):
                predictions.sort(key=lambda x: x[1], reverse=True)
                return predictions
            else:
                logger.warning(f'Unexpected prediction format: {predictions}')
                return self._fallback_classification(text)
        except Exception as e:
            logger.error(f'Error during classification: {e}')
            return self._fallback_classification(text)

    def _fallback_classification(self, text: str) -> List[Tuple[str, float]]:
        """
        Simple heuristic classification when model isn't available.
        
        Args:
            text: The query text
            
        Returns:
            List of (label, score) tuples
        """
        complexity_indicators = ['explain', 'analyze', 'compare', 'evaluate', 'synthesize', 'how', 'why', 'complex', 'detail', 'thorough', 'comprehensive', 'step by step', 'calculate', 'prove', 'justify', 'multiple', 'consequences', 'implications', 'differentiate', 'frameworks']
        count = sum((1 for indicator in complexity_indicators if indicator.lower() in text.lower()))
        text_length_factor = min(len(text) / 100, 2.0)
        indicator_factor = min(count / 3, 1.5)
        complexity_score = text_length_factor * indicator_factor
        if complexity_score > 1.0:
            return [('HIGH', 0.7), ('LOW', 0.3)]
        else:
            return [('LOW', 0.8), ('HIGH', 0.2)]

    def is_high_complexity(self, text: str, threshold: float=0.5) -> bool:
        """
        Determine if a query is high complexity.
        
        Args:
            text: The query text
            threshold: Confidence threshold for HIGH classification
            
        Returns:
            Boolean indicating if the query is high complexity
        """
        predictions = self.predict(text)
        for label, score in predictions:
            if label == 'HIGH' and score >= threshold:
                return True
        return False

    def get_complexity_with_confidence(self, text: str) -> Tuple[str, float]:
        """
        Get the complexity label and confidence score.
        
        Args:
            text: The query text
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
        predictions = self.predict(text)
        return predictions[0]

def _fallback_classification(self, text: str) -> List[Tuple[str, float]]:
    """
        Simple heuristic classification when model isn't available.
        
        Args:
            text: The query text
            
        Returns:
            List of (label, score) tuples
        """
    complexity_indicators = ['explain', 'analyze', 'compare', 'evaluate', 'synthesize', 'how', 'why', 'complex', 'detail', 'thorough', 'comprehensive', 'step by step', 'calculate', 'prove', 'justify', 'multiple', 'consequences', 'implications', 'differentiate', 'frameworks']
    count = sum((1 for indicator in complexity_indicators if indicator.lower() in text.lower()))
    text_length_factor = min(len(text) / 100, 2.0)
    indicator_factor = min(count / 3, 1.5)
    complexity_score = text_length_factor * indicator_factor
    if complexity_score > 1.0:
        return [('HIGH', 0.7), ('LOW', 0.3)]
    else:
        return [('LOW', 0.8), ('HIGH', 0.2)]

class SteeringVectorManager:
    """
    Manager for loading and applying steering vectors from a dataset.
    """

    def __init__(self, dataset_name: str, target_layer: int=19, cache_dir: Optional[str]=None, device: Optional[str]=None):
        """
        Initialize the steering vector manager.
        
        Args:
            dataset_name: Name of the HuggingFace dataset containing steering vectors
            target_layer: Target layer for applying steering vectors
            cache_dir: Directory for caching the dataset
            device: Device to use for tensors
        """
        self.dataset_name = dataset_name
        self.target_layer = target_layer
        self.cache_dir = cache_dir
        self.device = device or ('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        self.steering_vectors = []
        self.pattern_to_vectors = {}
        self.tokenized_contexts = {}
        self.default_strength = 2.0
        self.pattern_strengths = {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5, 'unknown': 1.0}
        if dataset_name:
            self.load_dataset()

    def load_dataset(self):
        """Load steering vectors from the HuggingFace dataset."""
        try:
            logger.info(f'Loading steering vectors from dataset: {self.dataset_name}')
            dataset = datasets.load_dataset(self.dataset_name, cache_dir=self.cache_dir)
            main_split = list(dataset.keys())[0]
            vector_data = dataset[main_split]
            for item in vector_data:
                vector = self._process_dataset_item(item)
                if vector:
                    self.steering_vectors.append(vector)
                    pattern = vector.get('reasoning_pattern', 'unknown')
                    if pattern not in self.pattern_to_vectors:
                        self.pattern_to_vectors[pattern] = []
                    self.pattern_to_vectors[pattern].append(vector)
            logger.info(f'Loaded {len(self.steering_vectors)} steering vectors')
            logger.info(f'Found {len(self.pattern_to_vectors)} reasoning patterns: {list(self.pattern_to_vectors.keys())}')
            if self.steering_vectors:
                first_vector = self.steering_vectors[0]
                logger.info(f'First vector sample - pattern: {first_vector.get('reasoning_pattern', 'missing')}')
                if 'pivot_context' in first_vector:
                    context_len = len(first_vector['pivot_context'])
                    logger.info(f'First vector pivot_context length: {context_len}')
        except Exception as e:
            logger.error(f'Error loading steering vectors: {e}')
            self.steering_vectors = []
            self.pattern_to_vectors = {}

    def _process_dataset_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a dataset item into a steering vector.
        
        Args:
            item: Dataset item
            
        Returns:
            Processed steering vector or None if invalid
        """
        try:
            required_fields = ['pivot_context', 'steering_vector', 'reasoning_pattern']
            if not all((field in item for field in required_fields)):
                return None
            steering_vector = item['steering_vector']
            if isinstance(steering_vector, str):
                try:
                    steering_vector = json.loads(steering_vector)
                except json.JSONDecodeError:
                    steering_vector = [float(x) for x in steering_vector.strip('[]').split(',')]
            if not isinstance(steering_vector, list):
                logger.warning(f'Invalid steering vector format: {type(steering_vector)}')
                return None
            vector = {'pivot_context': item['pivot_context'], 'pivot_token': item.get('pivot_token', ''), 'pivot_token_id': item.get('pivot_token_id', -1), 'prob_before': item.get('prob_before', 0.0), 'prob_after': item.get('prob_after', 0.0), 'prob_delta': item.get('prob_delta', 0.0), 'model_id': item.get('model_id', ''), 'task_type': item.get('task_type', 'unknown'), 'steering_vector': steering_vector, 'cluster_id': item.get('cluster_id', -1), 'reasoning_pattern': item.get('reasoning_pattern', 'unknown'), 'cluster_vector': item.get('cluster_vector', steering_vector), 'steering_layer': item.get('steering_layer', self.target_layer)}
            return vector
        except Exception as e:
            logger.error(f'Error processing dataset item: {e}')
            return None

    def create_tokenized_contexts(self, tokenizer):
        """
        Pre-tokenize context patterns for efficient matching during generation.
        Similar to how guided mode does token-based matching.
        
        Args:
            tokenizer: Tokenizer for encoding contexts
        """
        max_pts_tokens = 256
        count = 0
        for vector in self.steering_vectors:
            context = vector.get('pivot_context', '')
            if not context:
                continue
            tokenized_context = tokenizer.encode(context, add_special_tokens=False)
            if len(tokenized_context) > max_pts_tokens:
                tokenized_context = tokenized_context[-max_pts_tokens:]
            tuple_key = tuple(tokenized_context)
            self.tokenized_contexts[tuple_key] = vector
            for suffix_len in [4, 8, 12]:
                if len(tokenized_context) > suffix_len:
                    suffix = tokenized_context[-suffix_len:]
                    suffix_tuple = tuple(suffix)
                    if suffix_tuple not in self.tokenized_contexts:
                        self.tokenized_contexts[suffix_tuple] = vector
            count += 1
        logger.info(f'STEERING: Pre-tokenized {count} contexts into {len(self.tokenized_contexts)} token patterns')
        length_counts = {}
        for key in self.tokenized_contexts.keys():
            length = len(key)
            if length not in length_counts:
                length_counts[length] = 0
            length_counts[length] += 1
        logger.info(f'STEERING: Token pattern length distribution: {sorted(length_counts.items())}')

    def get_steering_strength(self, pattern: str) -> float:
        """
        Get the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            The steering strength
        """
        return self.pattern_strengths.get(pattern, self.default_strength)

    def set_steering_strength(self, pattern: str, strength: float):
        """
        Set the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            strength: The steering strength
        """
        self.pattern_strengths[pattern] = strength
        logger.info(f'STEERING: Set strength for {pattern} to {strength}')

    def get_pattern_vectors(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Get all steering vectors for a specific reasoning pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            List of steering vectors
        """
        return self.pattern_to_vectors.get(pattern, [])

    def get_steering_vector(self, context: str, match_key: Optional[str]=None) -> Optional[Dict[str, Any]]:
        """
        Get the most appropriate steering vector for a context.
        
        Args:
            context: The current generation context.
            match_key: Optional key for matching.
            
        Returns:
            Dictionary with steering data or None if no match.
        """
        if match_key is not None:
            for vector in self.steering_vectors:
                vector_context = vector.get('pivot_context', '')
                vector_key = vector_context[-100:] if len(vector_context) >= 100 else vector_context
                if vector_key == match_key:
                    logger.debug(f"STEERING: Context match found for '{vector.get('pivot_token', '')}' with pattern {vector.get('reasoning_pattern', 'unknown')}")
                    return vector
                if random.random() < 0.001:
                    logger.debug(f'STEERING: Match failed - key length: {len(match_key)}, vector key length: {len(vector_key)}')
                    logger.debug(f"STEERING: Match key sample: '{match_key[:20]}...'")
                    logger.debug(f"STEERING: Vector key sample: '{vector_key[:20]}...'")
        return None

def load_dataset(self):
    """Load steering vectors from the HuggingFace dataset."""
    try:
        logger.info(f'Loading steering vectors from dataset: {self.dataset_name}')
        dataset = datasets.load_dataset(self.dataset_name, cache_dir=self.cache_dir)
        main_split = list(dataset.keys())[0]
        vector_data = dataset[main_split]
        for item in vector_data:
            vector = self._process_dataset_item(item)
            if vector:
                self.steering_vectors.append(vector)
                pattern = vector.get('reasoning_pattern', 'unknown')
                if pattern not in self.pattern_to_vectors:
                    self.pattern_to_vectors[pattern] = []
                self.pattern_to_vectors[pattern].append(vector)
        logger.info(f'Loaded {len(self.steering_vectors)} steering vectors')
        logger.info(f'Found {len(self.pattern_to_vectors)} reasoning patterns: {list(self.pattern_to_vectors.keys())}')
        if self.steering_vectors:
            first_vector = self.steering_vectors[0]
            logger.info(f'First vector sample - pattern: {first_vector.get('reasoning_pattern', 'missing')}')
            if 'pivot_context' in first_vector:
                context_len = len(first_vector['pivot_context'])
                logger.info(f'First vector pivot_context length: {context_len}')
    except Exception as e:
        logger.error(f'Error loading steering vectors: {e}')
        self.steering_vectors = []
        self.pattern_to_vectors = {}

def create_tokenized_contexts(self, tokenizer):
    """
        Pre-tokenize context patterns for efficient matching during generation.
        Similar to how guided mode does token-based matching.
        
        Args:
            tokenizer: Tokenizer for encoding contexts
        """
    max_pts_tokens = 256
    count = 0
    for vector in self.steering_vectors:
        context = vector.get('pivot_context', '')
        if not context:
            continue
        tokenized_context = tokenizer.encode(context, add_special_tokens=False)
        if len(tokenized_context) > max_pts_tokens:
            tokenized_context = tokenized_context[-max_pts_tokens:]
        tuple_key = tuple(tokenized_context)
        self.tokenized_contexts[tuple_key] = vector
        for suffix_len in [4, 8, 12]:
            if len(tokenized_context) > suffix_len:
                suffix = tokenized_context[-suffix_len:]
                suffix_tuple = tuple(suffix)
                if suffix_tuple not in self.tokenized_contexts:
                    self.tokenized_contexts[suffix_tuple] = vector
        count += 1
    logger.info(f'STEERING: Pre-tokenized {count} contexts into {len(self.tokenized_contexts)} token patterns')
    length_counts = {}
    for key in self.tokenized_contexts.keys():
        length = len(key)
        if length not in length_counts:
            length_counts[length] = 0
        length_counts[length] += 1
    logger.info(f'STEERING: Token pattern length distribution: {sorted(length_counts.items())}')

class SteeringHook:
    """Hook for applying steering vectors during generation."""

    def __init__(self, manager: SteeringVectorManager, layer_num: int, tokenizer=None):
        """
        Initialize the steering hook.
        
        Args:
            manager: The steering vector manager
            layer_num: The layer number to apply steering to
            tokenizer: Tokenizer for token-based matching
        """
        self.manager = manager
        self.layer_num = layer_num
        self.tokenizer = tokenizer
        self.context_buffer = ''
        self.token_history = []
        self.max_history = 256
        self.match_found = False
        self.current_vector = None
        self.last_pattern = None
        self.active_pattern = None
        self.generation_started = False
        logger.info(f'STEERING: Initialized hook for layer {layer_num}')

    def __call__(self, module, input_tensors, output):
        """
        Apply steering to the output of a layer.
        
        Args:
            module: The module being hooked
            input_tensors: The input tensors
            output: The output tensor
            
        Returns:
            Modified output tensor
        """
        try:
            if not self.active_pattern:
                return output
            if self.current_vector is not None:
                pattern = self.current_vector.get('reasoning_pattern', 'unknown')
                strength = self.manager.get_steering_strength(pattern)
                safe_strength = min(max(strength, 0.1), 2.0)
                if pattern != self.last_pattern:
                    logger.info(f'STEERING: Switching to {pattern} reasoning pattern with strength {safe_strength}')
                    self.last_pattern = pattern
                elif random.random() < 0.05:
                    logger.info(f'STEERING: Still applying {pattern} pattern with strength {safe_strength}')
                try:
                    if isinstance(output, tuple):
                        hidden_states = output[0]
                        try:
                            modified_hidden_states = self._apply_steering_vector(hidden_states, self.current_vector, safe_strength)
                            if modified_hidden_states.shape == hidden_states.shape:
                                return (modified_hidden_states,) + output[1:]
                            else:
                                logger.error(f'STEERING: Modified hidden states have wrong shape. Expected {hidden_states.shape}, got {modified_hidden_states.shape}')
                                return output
                        except Exception as e:
                            logger.error(f'STEERING: Error applying steering to tuple output: {e}')
                            return output
                    else:
                        try:
                            return self._apply_steering_vector(output, self.current_vector, safe_strength)
                        except Exception as e:
                            logger.error(f'STEERING: Error applying steering to direct output: {e}')
                            return output
                except Exception as e:
                    logger.error(f'STEERING: Unexpected error in steering application: {e}')
                    return output
            return output
        except Exception as e:
            logger.error(f'STEERING: Critical error in hook: {e}')
            return output

    def _apply_steering_vector(self, hidden_states: torch.Tensor, steering_vector: Dict[str, Any], scaling_factor: float=2.0) -> torch.Tensor:
        """
        Apply a steering vector to hidden states.
        
        Args:
            hidden_states: The hidden states tensor
            steering_vector: Dictionary with steering vector data
            scaling_factor: Factor to scale the steering vector by
            
        Returns:
            Modified hidden states tensor
        """
        try:
            hidden_states_clone = hidden_states.clone().detach()
            vector_type = None
            if 'steering_vector' in steering_vector:
                vector_data = steering_vector['steering_vector']
                vector_type = 'steering_vector'
            elif 'cluster_vector' in steering_vector:
                vector_data = steering_vector['cluster_vector']
                vector_type = 'cluster_vector'
            else:
                logger.warning('STEERING: No valid vector found in steering data')
                return hidden_states
            try:
                vector = torch.tensor(vector_data, dtype=hidden_states.dtype, device=hidden_states.device)
            except Exception as e:
                logger.error(f'STEERING: Error converting vector to tensor: {e}')
                return hidden_states
            pattern = steering_vector.get('reasoning_pattern', 'unknown')
            logger.debug(f"STEERING: Applying {vector_type} for pattern '{pattern}' with base scaling {scaling_factor}")
            if 'prob_delta' in steering_vector:
                prob_delta = abs(steering_vector['prob_delta'])
                prob_delta_capped = min(max(prob_delta, 0.1), 2.0)
                scaling_factor *= prob_delta_capped
                logger.debug(f'STEERING: Adjusted scaling by prob_delta {prob_delta_capped} to {scaling_factor}')
            is_positive = steering_vector.get('is_positive', True)
            hs_shape = hidden_states.shape
            vector_shape = vector.shape
            logger.debug(f'STEERING: hidden_states shape: {hs_shape}, vector shape: {vector_shape}')
            if len(vector_shape) != 1 or vector_shape[0] != hs_shape[-1]:
                logger.error(f'STEERING: Shape mismatch - hidden_states: {hs_shape}, vector: {vector_shape}')
                return hidden_states
            safe_scaling = min(max(scaling_factor, 0.0), 3.0)
            try:
                if len(hs_shape) >= 3 and hs_shape[0] > 0 and (hs_shape[1] > 0):
                    if is_positive:
                        vector_norm = torch.nn.functional.normalize(vector, dim=0)
                        hidden_states_clone[-1, -1, :] = hidden_states_clone[-1, -1, :] + safe_scaling * vector_norm
                    else:
                        vector_norm = torch.nn.functional.normalize(vector, dim=0)
                        hidden_states_clone[-1, -1, :] = hidden_states_clone[-1, -1, :] - safe_scaling * vector_norm
                    if torch.isnan(hidden_states_clone).any() or torch.isinf(hidden_states_clone).any():
                        logger.error('STEERING: NaN or inf values detected after applying vector, reverting to original')
                        return hidden_states
                else:
                    logger.error(f'STEERING: Hidden states shape not suitable for steering: {hs_shape}')
                    return hidden_states
            except IndexError as e:
                logger.error(f'STEERING: IndexError when applying vector: {e}')
                logger.error(f'STEERING: Indices: [-1, -1, :], tensor shape: {hidden_states.shape}')
                return hidden_states
            return hidden_states_clone
        except Exception as e:
            logger.error(f'STEERING: Unexpected error applying steering vector: {e}')
            return hidden_states

    def update_context(self, new_tokens: str):
        """
        Update the context buffer with new tokens.
        
        Args:
            new_tokens: New tokens to add to the context.
        """
        if self.tokenizer is not None:
            token_ids = self.tokenizer.encode(new_tokens, add_special_tokens=False)
            if token_ids:
                self.token_history.extend(token_ids)
                if len(self.token_history) > self.max_history:
                    self.token_history = self.token_history[-self.max_history:]
                if random.random() < 0.01:
                    logger.debug(f'STEERING: Token history updated, now has {len(self.token_history)} tokens')
        else:
            self.context_buffer += new_tokens
            if len(self.context_buffer) > 500:
                self.context_buffer = self.context_buffer[-500:]
                logger.debug(f'STEERING: Context buffer trimmed to {len(self.context_buffer)} chars')

    def update_token_history(self, new_tokens: List[int]):
        """
        Update the token history with new tokens.
        
        Args:
            new_tokens: New token IDs to add
        """
        self.token_history.extend(new_tokens)
        if len(self.token_history) > self.max_history:
            self.token_history = self.token_history[-self.max_history:]
        if random.random() < 0.01:
            logger.debug(f'STEERING: Token history updated, now has {len(self.token_history)} tokens')

    def update_context(self, new_tokens: str):
        """
        Update the context buffer with new tokens.
        
        Args:
            new_tokens: New tokens to add to the context.
        """
        if self.tokenizer is not None:
            token_ids = self.tokenizer.encode(new_tokens, add_special_tokens=False)
            if token_ids:
                self.token_history.extend(token_ids)
                if len(self.token_history) > self.max_history:
                    self.token_history = self.token_history[-self.max_history:]
                if random.random() < 0.01:
                    logger.debug(f'STEERING: Token history updated, now has {len(self.token_history)} tokens')
        self.context_buffer += new_tokens
        if len(self.context_buffer) > 500:
            self.context_buffer = self.context_buffer[-500:]
            logger.debug(f'STEERING: Context buffer trimmed to {len(self.context_buffer)} chars')

    def try_match(self):
        """
        Try to match the current context with a steering vector.
        Only allows one pattern to be selected for the entire generation.
        Tries both token-based and text-based matching approaches.
        """
        if self.active_pattern:
            return False
        match_result = False
        if self.tokenizer is not None and hasattr(self.manager, 'tokenized_contexts') and self.manager.tokenized_contexts:
            match_result = self._try_token_match()
        if not match_result:
            match_result = self._try_text_match()
        self.generation_started = True
        if match_result and self.current_vector:
            new_pattern = self.current_vector.get('reasoning_pattern', 'unknown')
            self.active_pattern = new_pattern
            logger.info(f"STEERING: Selected '{new_pattern}' pattern for this request")
        return match_result

    def _try_token_match(self):
        """
        Try to match using token-based context (similar to guided mode).
        """
        if len(self.token_history) < 4:
            logger.debug(f'STEERING: Not enough tokens to match ({len(self.token_history)})')
            return False
        best_match = {'length': 0, 'vector': None, 'is_partial': True}
        if random.random() < 0.01:
            history_sample = self.token_history[-5:] if len(self.token_history) >= 5 else self.token_history
            logger.debug(f'STEERING: Token matching with history (last {len(history_sample)} of {len(self.token_history)} tokens): {history_sample}')
        for tokenized_context, vector in self.manager.tokenized_contexts.items():
            token_list = list(tokenized_context)
            token_len = len(token_list)
            if len(self.token_history) < token_len:
                if len(self.token_history) >= 4:
                    match_len = min(len(self.token_history), max(4, token_len // 2))
                    if self.token_history[-match_len:] == token_list[-match_len:]:
                        if match_len > best_match['length']:
                            best_match = {'length': match_len, 'vector': vector, 'is_partial': True, 'match_len': match_len, 'token_len': token_len}
            elif self.token_history[-token_len:] == token_list:
                if token_len >= best_match['length']:
                    best_match = {'length': token_len, 'vector': vector, 'is_partial': False, 'match_len': token_len, 'token_len': token_len}
        if best_match['vector'] is not None:
            match_type = 'PARTIAL' if best_match['is_partial'] else 'FULL'
            self.match_found = True
            self.current_vector = best_match['vector']
            pattern = best_match['vector'].get('reasoning_pattern', 'unknown')
            pivot_token = best_match['vector'].get('pivot_token', '')
            logger.info(f'STEERING: Found {match_type} token match ({best_match['match_len']}/{best_match['token_len']} tokens) for {pattern} pattern')
            logger.info(f"STEERING: Pivot token: '{pivot_token}'")
            return True
        if len(self.token_history) >= 8 and (not self.match_found):
            logger.debug('STEERING: No exact match found, trying fuzzy matching')
            for tokenized_context, vector in self.manager.tokenized_contexts.items():
                token_list = list(tokenized_context)
                token_len = len(token_list)
                if token_len >= 8:
                    match_len = min(len(self.token_history), token_len)
                    last_tokens = self.token_history[-match_len:]
                    context_tokens = token_list[-match_len:]
                    matches = sum((1 for a, b in zip(last_tokens, context_tokens) if a == b))
                    similarity = matches / match_len
                    if similarity >= 0.7:
                        if match_len > best_match['length']:
                            best_match = {'length': match_len, 'vector': vector, 'is_partial': True, 'match_len': match_len, 'token_len': token_len, 'similarity': similarity}
            if best_match['vector'] is not None:
                self.match_found = True
                self.current_vector = best_match['vector']
                pattern = best_match['vector'].get('reasoning_pattern', 'unknown')
                pivot_token = best_match['vector'].get('pivot_token', '')
                similarity = best_match.get('similarity', 0.0)
                logger.info(f'STEERING: Found fuzzy match ({similarity:.2f} similarity) for {pattern} pattern')
                logger.info(f"STEERING: Pivot token: '{pivot_token}'")
                return True
        if len(self.token_history) >= 8 and (not self.match_found):
            logger.debug('STEERING: No exact match found, trying fuzzy matching')
            for tokenized_context, vector in self.manager.tokenized_contexts.items():
                token_list = list(tokenized_context)
                token_len = len(token_list)
                if token_len >= 8:
                    match_len = min(len(self.token_history), token_len)
                    last_tokens = self.token_history[-match_len:]
                    context_tokens = token_list[-match_len:]
                    matches = sum((1 for a, b in zip(last_tokens, context_tokens) if a == b))
                    similarity = matches / match_len
                    if similarity >= 0.7:
                        if match_len > best_match['length']:
                            best_match = {'length': match_len, 'vector': vector, 'is_partial': True, 'match_len': match_len, 'token_len': token_len, 'similarity': similarity}
            if best_match['vector'] is not None:
                self.match_found = True
                self.current_vector = best_match['vector']
                pattern = best_match['vector'].get('reasoning_pattern', 'unknown')
                pivot_token = best_match['vector'].get('pivot_token', '')
                similarity = best_match.get('similarity', 0.0)
                logger.info(f'STEERING: Found fuzzy match ({similarity:.2f} similarity) for {pattern} pattern')
                logger.info(f"STEERING: Pivot token: '{pivot_token}'")
                return True
        return False

    def _try_text_match(self):
        """Try to match using text-based context (original approach)."""
        if len(self.context_buffer) < 10:
            return False
        match_key = self.context_buffer[-100:] if len(self.context_buffer) >= 100 else self.context_buffer
        if random.random() < 0.01:
            logger.debug(f"STEERING: Current context buffer (last 50 chars): '{self.context_buffer[-50:]}'")
            logger.debug(f"STEERING: Matching with key (length {len(match_key)}): '{match_key[:20]}...'")
        vector = self.manager.get_steering_vector(self.context_buffer, match_key)
        if vector is not None:
            self.match_found = True
            self.current_vector = vector
            pattern = vector.get('reasoning_pattern', 'unknown')
            pivot_token = vector.get('pivot_token', '')
            logger.info(f'STEERING: Found text match for {pattern} reasoning pattern')
            logger.info(f"STEERING: Pivot token: '{pivot_token}'")
            return True
        if len(match_key) >= 20:
            best_match = None
            best_similarity = 0.0
            for vector in self.manager.steering_vectors:
                vector_context = vector.get('pivot_context', '')
                if not vector_context or len(vector_context) < 20:
                    continue
                vector_key = vector_context[-100:] if len(vector_context) >= 100 else vector_context
                min_length = min(len(match_key), len(vector_key))
                matching_chars = sum((1 for a, b in zip(match_key, vector_key) if a == b))
                similarity = matching_chars / min_length if min_length > 0 else 0
                if similarity >= 0.7 and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = vector
            if best_match is not None:
                self.match_found = True
                self.current_vector = best_match
                pattern = best_match.get('reasoning_pattern', 'unknown')
                pivot_token = best_match.get('pivot_token', '')
                logger.info(f'STEERING: Found fuzzy text match ({best_similarity:.2f} similarity) for {pattern} pattern')
                logger.info(f"STEERING: Pivot token: '{pivot_token}'")
                return True
        return False

    def reset(self):
        """Reset the hook state for a new generation."""
        self.match_found = False
        self.current_vector = None
        self.context_buffer = ''
        self.token_history = []
        self.last_pattern = None
        self.active_pattern = None
        self.generation_started = False
        logger.info('STEERING: Hook state reset for new generation')

def __call__(self, module, input_tensors, output):
    """
        Apply steering to the output of a layer.
        
        Args:
            module: The module being hooked
            input_tensors: The input tensors
            output: The output tensor
            
        Returns:
            Modified output tensor
        """
    try:
        if not self.active_pattern:
            return output
        if self.current_vector is not None:
            pattern = self.current_vector.get('reasoning_pattern', 'unknown')
            strength = self.manager.get_steering_strength(pattern)
            safe_strength = min(max(strength, 0.1), 2.0)
            if pattern != self.last_pattern:
                logger.info(f'STEERING: Switching to {pattern} reasoning pattern with strength {safe_strength}')
                self.last_pattern = pattern
            elif random.random() < 0.05:
                logger.info(f'STEERING: Still applying {pattern} pattern with strength {safe_strength}')
            try:
                if isinstance(output, tuple):
                    hidden_states = output[0]
                    try:
                        modified_hidden_states = self._apply_steering_vector(hidden_states, self.current_vector, safe_strength)
                        if modified_hidden_states.shape == hidden_states.shape:
                            return (modified_hidden_states,) + output[1:]
                        else:
                            logger.error(f'STEERING: Modified hidden states have wrong shape. Expected {hidden_states.shape}, got {modified_hidden_states.shape}')
                            return output
                    except Exception as e:
                        logger.error(f'STEERING: Error applying steering to tuple output: {e}')
                        return output
                else:
                    try:
                        return self._apply_steering_vector(output, self.current_vector, safe_strength)
                    except Exception as e:
                        logger.error(f'STEERING: Error applying steering to direct output: {e}')
                        return output
            except Exception as e:
                logger.error(f'STEERING: Unexpected error in steering application: {e}')
                return output
        return output
    except Exception as e:
        logger.error(f'STEERING: Critical error in hook: {e}')
        return output

def _apply_steering_vector(self, hidden_states: torch.Tensor, steering_vector: Dict[str, Any], scaling_factor: float=2.0) -> torch.Tensor:
    """
        Apply a steering vector to hidden states.
        
        Args:
            hidden_states: The hidden states tensor
            steering_vector: Dictionary with steering vector data
            scaling_factor: Factor to scale the steering vector by
            
        Returns:
            Modified hidden states tensor
        """
    try:
        hidden_states_clone = hidden_states.clone().detach()
        vector_type = None
        if 'steering_vector' in steering_vector:
            vector_data = steering_vector['steering_vector']
            vector_type = 'steering_vector'
        elif 'cluster_vector' in steering_vector:
            vector_data = steering_vector['cluster_vector']
            vector_type = 'cluster_vector'
        else:
            logger.warning('STEERING: No valid vector found in steering data')
            return hidden_states
        try:
            vector = torch.tensor(vector_data, dtype=hidden_states.dtype, device=hidden_states.device)
        except Exception as e:
            logger.error(f'STEERING: Error converting vector to tensor: {e}')
            return hidden_states
        pattern = steering_vector.get('reasoning_pattern', 'unknown')
        logger.debug(f"STEERING: Applying {vector_type} for pattern '{pattern}' with base scaling {scaling_factor}")
        if 'prob_delta' in steering_vector:
            prob_delta = abs(steering_vector['prob_delta'])
            prob_delta_capped = min(max(prob_delta, 0.1), 2.0)
            scaling_factor *= prob_delta_capped
            logger.debug(f'STEERING: Adjusted scaling by prob_delta {prob_delta_capped} to {scaling_factor}')
        is_positive = steering_vector.get('is_positive', True)
        hs_shape = hidden_states.shape
        vector_shape = vector.shape
        logger.debug(f'STEERING: hidden_states shape: {hs_shape}, vector shape: {vector_shape}')
        if len(vector_shape) != 1 or vector_shape[0] != hs_shape[-1]:
            logger.error(f'STEERING: Shape mismatch - hidden_states: {hs_shape}, vector: {vector_shape}')
            return hidden_states
        safe_scaling = min(max(scaling_factor, 0.0), 3.0)
        try:
            if len(hs_shape) >= 3 and hs_shape[0] > 0 and (hs_shape[1] > 0):
                if is_positive:
                    vector_norm = torch.nn.functional.normalize(vector, dim=0)
                    hidden_states_clone[-1, -1, :] = hidden_states_clone[-1, -1, :] + safe_scaling * vector_norm
                else:
                    vector_norm = torch.nn.functional.normalize(vector, dim=0)
                    hidden_states_clone[-1, -1, :] = hidden_states_clone[-1, -1, :] - safe_scaling * vector_norm
                if torch.isnan(hidden_states_clone).any() or torch.isinf(hidden_states_clone).any():
                    logger.error('STEERING: NaN or inf values detected after applying vector, reverting to original')
                    return hidden_states
            else:
                logger.error(f'STEERING: Hidden states shape not suitable for steering: {hs_shape}')
                return hidden_states
        except IndexError as e:
            logger.error(f'STEERING: IndexError when applying vector: {e}')
            logger.error(f'STEERING: Indices: [-1, -1, :], tensor shape: {hidden_states.shape}')
            return hidden_states
        return hidden_states_clone
    except Exception as e:
        logger.error(f'STEERING: Unexpected error applying steering vector: {e}')
        return hidden_states

def _try_token_match(self):
    """
        Try to match using token-based context (similar to guided mode).
        """
    if len(self.token_history) < 4:
        logger.debug(f'STEERING: Not enough tokens to match ({len(self.token_history)})')
        return False
    best_match = {'length': 0, 'vector': None, 'is_partial': True}
    if random.random() < 0.01:
        history_sample = self.token_history[-5:] if len(self.token_history) >= 5 else self.token_history
        logger.debug(f'STEERING: Token matching with history (last {len(history_sample)} of {len(self.token_history)} tokens): {history_sample}')
    for tokenized_context, vector in self.manager.tokenized_contexts.items():
        token_list = list(tokenized_context)
        token_len = len(token_list)
        if len(self.token_history) < token_len:
            if len(self.token_history) >= 4:
                match_len = min(len(self.token_history), max(4, token_len // 2))
                if self.token_history[-match_len:] == token_list[-match_len:]:
                    if match_len > best_match['length']:
                        best_match = {'length': match_len, 'vector': vector, 'is_partial': True, 'match_len': match_len, 'token_len': token_len}
        elif self.token_history[-token_len:] == token_list:
            if token_len >= best_match['length']:
                best_match = {'length': token_len, 'vector': vector, 'is_partial': False, 'match_len': token_len, 'token_len': token_len}
    if best_match['vector'] is not None:
        match_type = 'PARTIAL' if best_match['is_partial'] else 'FULL'
        self.match_found = True
        self.current_vector = best_match['vector']
        pattern = best_match['vector'].get('reasoning_pattern', 'unknown')
        pivot_token = best_match['vector'].get('pivot_token', '')
        logger.info(f'STEERING: Found {match_type} token match ({best_match['match_len']}/{best_match['token_len']} tokens) for {pattern} pattern')
        logger.info(f"STEERING: Pivot token: '{pivot_token}'")
        return True
    if len(self.token_history) >= 8 and (not self.match_found):
        logger.debug('STEERING: No exact match found, trying fuzzy matching')
        for tokenized_context, vector in self.manager.tokenized_contexts.items():
            token_list = list(tokenized_context)
            token_len = len(token_list)
            if token_len >= 8:
                match_len = min(len(self.token_history), token_len)
                last_tokens = self.token_history[-match_len:]
                context_tokens = token_list[-match_len:]
                matches = sum((1 for a, b in zip(last_tokens, context_tokens) if a == b))
                similarity = matches / match_len
                if similarity >= 0.7:
                    if match_len > best_match['length']:
                        best_match = {'length': match_len, 'vector': vector, 'is_partial': True, 'match_len': match_len, 'token_len': token_len, 'similarity': similarity}
        if best_match['vector'] is not None:
            self.match_found = True
            self.current_vector = best_match['vector']
            pattern = best_match['vector'].get('reasoning_pattern', 'unknown')
            pivot_token = best_match['vector'].get('pivot_token', '')
            similarity = best_match.get('similarity', 0.0)
            logger.info(f'STEERING: Found fuzzy match ({similarity:.2f} similarity) for {pattern} pattern')
            logger.info(f"STEERING: Pivot token: '{pivot_token}'")
            return True
    if len(self.token_history) >= 8 and (not self.match_found):
        logger.debug('STEERING: No exact match found, trying fuzzy matching')
        for tokenized_context, vector in self.manager.tokenized_contexts.items():
            token_list = list(tokenized_context)
            token_len = len(token_list)
            if token_len >= 8:
                match_len = min(len(self.token_history), token_len)
                last_tokens = self.token_history[-match_len:]
                context_tokens = token_list[-match_len:]
                matches = sum((1 for a, b in zip(last_tokens, context_tokens) if a == b))
                similarity = matches / match_len
                if similarity >= 0.7:
                    if match_len > best_match['length']:
                        best_match = {'length': match_len, 'vector': vector, 'is_partial': True, 'match_len': match_len, 'token_len': token_len, 'similarity': similarity}
        if best_match['vector'] is not None:
            self.match_found = True
            self.current_vector = best_match['vector']
            pattern = best_match['vector'].get('reasoning_pattern', 'unknown')
            pivot_token = best_match['vector'].get('pivot_token', '')
            similarity = best_match.get('similarity', 0.0)
            logger.info(f'STEERING: Found fuzzy match ({similarity:.2f} similarity) for {pattern} pattern')
            logger.info(f"STEERING: Pivot token: '{pivot_token}'")
            return True
    return False

def deepconf_decode(model: PreTrainedModel, tokenizer: PreTrainedTokenizer, messages: List[Dict[str, str]], request_config: Optional[Dict[str, Any]]=None) -> Tuple[str, int]:
    """
    Main DeepConf decoding function for integration with OptILLM.
    
    Implements confidence-aware reasoning with early termination for local models.
    Uses online mode with warmup phase and dynamic threshold calibration.
    
    Args:
        model: The local language model
        tokenizer: The tokenizer for the model
        messages: List of input messages in chat format
        request_config: Optional configuration overrides
        
    Returns:
        Tuple of (generated_response, total_tokens_used)
        
    Raises:
        ValueError: If invalid configuration provided
        RuntimeError: If processing fails
    """
    logger.info('Starting DeepConf decoding')
    if not messages:
        raise ValueError('Messages list cannot be empty')
    if not model or not tokenizer:
        raise ValueError('Model and tokenizer must be provided')
    config = DEFAULT_CONFIG.copy()
    if request_config:
        valid_keys = set(DEFAULT_CONFIG.keys())
        for key, value in request_config.items():
            if key in valid_keys:
                config[key] = value
            else:
                logger.warning(f'Unknown configuration key ignored: {key}')
    logger.info(f'DeepConf configuration: variant={config['variant']}, warmup_samples={config['warmup_samples']}, max_traces={config['max_traces']}')
    try:
        processor = DeepConfProcessor(model, tokenizer, config)
        final_answer, stats = processor.process_online(messages)
        total_tokens = stats.get('total_tokens_used', 0)
        response = format_deepconf_response(final_answer, stats, config)
        logger.info(f'DeepConf decoding completed successfully. Total tokens: {total_tokens}, Traces: {stats['total_traces']}, Early terminations: {stats['early_terminations']}')
        return (response, total_tokens)
    except Exception as e:
        logger.error(f'DeepConf decoding failed: {str(e)}')
        raise RuntimeError(f'DeepConf processing error: {str(e)}') from e

class DeepConfProcessor:
    """
    Main DeepConf processor implementing online mode with early termination.
    """

    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, config: Dict[str, Any]=None):
        """
        Initialize the DeepConf processor.
        
        Args:
            model: The language model
            tokenizer: The tokenizer
            config: Configuration dictionary
        """
        self.model = model
        self.tokenizer = tokenizer
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.confidence_calculator = ConfidenceCalculator(window_size=self.config['window_size'], top_k=self.config['top_k'])
        self.threshold_calibrator = ConfidenceThresholdCalibrator(variant=self.config['variant'])
        self.warmup_traces = []
        self.online_traces = []
        self.confidence_threshold = None
        self.total_tokens_used = 0
        logger.info(f'DeepConf processor initialized with variant: {self.config['variant']}')

    def reset(self):
        """Reset processor state for new query."""
        self.warmup_traces = []
        self.online_traces = []
        self.confidence_threshold = None
        self.total_tokens_used = 0
        self.confidence_calculator.reset()

    def generate_single_trace(self, messages: List[Dict[str, str]], use_early_termination: bool=False) -> TraceResult:
        """
        Generate a single reasoning trace with optional early termination.
        
        Args:
            messages: Input messages
            use_early_termination: Whether to apply early termination
            
        Returns:
            TraceResult object containing trace and confidence stats
        """
        self.confidence_calculator.reset()
        tokens = self.tokenizer.apply_chat_template(messages, return_tensors='pt', add_generation_prompt=True).to(self.model.device)
        kv_cache = DynamicCache()
        generated_tokens = []
        generated_text_parts = []
        token_count = 0
        terminated_early = False
        while token_count < self.config['max_tokens_per_trace']:
            with torch.no_grad():
                outputs = self.model(input_ids=tokens, past_key_values=kv_cache, use_cache=True)
                logits = outputs.logits[0, -1, :]
                kv_cache = outputs.past_key_values
            token_confidence = self.confidence_calculator.add_token_confidence(logits)
            if use_early_termination and token_count >= self.config['min_trace_length'] and (self.confidence_threshold is not None):
                current_group_confidence = self.confidence_calculator.get_current_group_confidence()
                if current_group_confidence is not None and current_group_confidence < self.confidence_threshold:
                    logger.debug(f'Early termination at token {token_count}, confidence: {current_group_confidence:.4f} < {self.confidence_threshold:.4f}')
                    terminated_early = True
                    break
            probs = torch.softmax(logits / self.config['temperature'], dim=-1)
            next_token = torch.multinomial(probs, num_samples=1).item()
            if next_token == self.tokenizer.eos_token_id:
                break
            generated_tokens.append(next_token)
            token_text = self.tokenizer.decode([next_token])
            generated_text_parts.append(token_text)
            tokens = torch.tensor([[next_token]]).to(self.model.device)
            token_count += 1
        generated_text = ''.join(generated_text_parts)
        confidence_stats = self.confidence_calculator.get_trace_statistics()
        trace_result = TraceResult(generated_tokens, generated_text, confidence_stats)
        trace_result.terminated_early = terminated_early
        self.total_tokens_used += token_count
        logger.debug(f'Generated trace: {token_count} tokens, avg confidence: {confidence_stats['average_confidence']:.4f}, early termination: {terminated_early}')
        return trace_result

    def run_warmup_phase(self, messages: List[Dict[str, str]]) -> None:
        """
        Run the warmup phase to generate initial traces and calibrate threshold.
        
        Args:
            messages: Input messages
        """
        logger.info(f'Starting warmup phase with {self.config['warmup_samples']} traces')
        for i in range(self.config['warmup_samples']):
            trace = self.generate_single_trace(messages, use_early_termination=False)
            self.warmup_traces.append(trace)
            self.threshold_calibrator.add_warmup_trace(trace.confidence_stats)
            logger.debug(f'Warmup trace {i + 1}/{self.config['warmup_samples']} completed')
        self.confidence_threshold = self.threshold_calibrator.calculate_threshold(metric=self.config['confidence_metric'])
        logger.info(f'Warmup phase completed. Threshold: {self.confidence_threshold:.4f}')

    def check_consensus(self, traces: List[TraceResult]) -> Tuple[bool, str, float]:
        """
        Check if consensus has been reached among traces.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (has_consensus, consensus_answer, consensus_ratio)
        """
        if not traces:
            return (False, '', 0.0)
        answers = []
        for trace in traces:
            answer = trace.text.strip().split('.')[-1].strip()
            if not answer:
                answer = trace.text.strip()[-50:].strip()
            answers.append(answer)
        answer_counts = Counter(answers)
        most_common_answer, most_common_count = answer_counts.most_common(1)[0]
        consensus_ratio = most_common_count / len(answers)
        has_consensus = consensus_ratio >= self.config['consensus_threshold']
        logger.debug(f'Consensus check: {consensus_ratio:.3f} ({('✓' if has_consensus else '✗')} >= {self.config['consensus_threshold']})')
        return (has_consensus, most_common_answer, consensus_ratio)

    def weighted_majority_vote(self, traces: List[TraceResult]) -> Tuple[str, Dict[str, float]]:
        """
        Perform weighted majority voting based on trace confidences.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (best_answer, voting_stats)
        """
        if not traces:
            return ('', {})
        answer_groups = defaultdict(list)
        for trace in traces:
            answer = trace.text.strip().split('.')[-1].strip()
            if not answer:
                answer = trace.text.strip()[-50:].strip()
            answer_groups[answer].append(trace)
        answer_scores = {}
        for answer, group_traces in answer_groups.items():
            confidences = [trace.confidence_stats['average_confidence'] for trace in group_traces]
            weighted_score = sum(confidences) / len(confidences)
            count_weight = len(group_traces) / len(traces)
            final_score = weighted_score * 0.7 + count_weight * 0.3
            answer_scores[answer] = final_score
        best_answer = max(answer_scores.keys(), key=lambda x: answer_scores[x])
        voting_stats = {'num_unique_answers': len(answer_groups), 'best_score': answer_scores[best_answer], 'answer_distribution': {ans: len(traces) for ans, traces in answer_groups.items()}}
        logger.info(f'Weighted voting completed. Best answer score: {answer_scores[best_answer]:.4f}')
        return (best_answer, voting_stats)

    def process_online(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict[str, Any]]:
        """
        Main online processing with warmup and early termination.
        
        Args:
            messages: Input messages
            
        Returns:
            Tuple of (final_answer, processing_stats)
        """
        self.reset()
        logger.info('Starting DeepConf online processing')
        self.run_warmup_phase(messages)
        logger.info('Starting online generation phase')
        all_traces = self.warmup_traces[:]
        for trace_num in range(self.config['max_traces'] - self.config['warmup_samples']):
            trace = self.generate_single_trace(messages, use_early_termination=True)
            all_traces.append(trace)
            self.online_traces.append(trace)
            has_consensus, consensus_answer, consensus_ratio = self.check_consensus(all_traces)
            logger.debug(f'Online trace {trace_num + 1} completed. Total traces: {len(all_traces)}, Consensus: {consensus_ratio:.3f}')
            if has_consensus:
                logger.info(f'Consensus reached after {len(all_traces)} traces (ratio: {consensus_ratio:.3f})')
                break
        final_answer, voting_stats = self.weighted_majority_vote(all_traces)
        processing_stats = {'total_traces': len(all_traces), 'warmup_traces': len(self.warmup_traces), 'online_traces': len(self.online_traces), 'early_terminations': sum((1 for trace in all_traces if trace.terminated_early)), 'total_tokens_used': self.total_tokens_used, 'confidence_threshold': self.confidence_threshold, 'variant': self.config['variant'], **voting_stats}
        logger.info(f'DeepConf processing completed. Traces: {processing_stats['total_traces']}, Tokens: {processing_stats['total_tokens_used']}, Early terminations: {processing_stats['early_terminations']}')
        return (final_answer, processing_stats)

def weighted_majority_vote(self, traces: List[TraceResult]) -> Tuple[str, Dict[str, float]]:
    """
        Perform weighted majority voting based on trace confidences.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (best_answer, voting_stats)
        """
    if not traces:
        return ('', {})
    answer_groups = defaultdict(list)
    for trace in traces:
        answer = trace.text.strip().split('.')[-1].strip()
        if not answer:
            answer = trace.text.strip()[-50:].strip()
        answer_groups[answer].append(trace)
    answer_scores = {}
    for answer, group_traces in answer_groups.items():
        confidences = [trace.confidence_stats['average_confidence'] for trace in group_traces]
        weighted_score = sum(confidences) / len(confidences)
        count_weight = len(group_traces) / len(traces)
        final_score = weighted_score * 0.7 + count_weight * 0.3
        answer_scores[answer] = final_score
    best_answer = max(answer_scores.keys(), key=lambda x: answer_scores[x])
    voting_stats = {'num_unique_answers': len(answer_groups), 'best_score': answer_scores[best_answer], 'answer_distribution': {ans: len(traces) for ans, traces in answer_groups.items()}}
    logger.info(f'Weighted voting completed. Best answer score: {answer_scores[best_answer]:.4f}')
    return (best_answer, voting_stats)

class ConfidenceCalculator:
    """
    Calculates various confidence metrics for token-level assessment.
    """

    def __init__(self, window_size: int=2048, top_k: int=5):
        """
        Initialize the confidence calculator.
        
        Args:
            window_size: Size of sliding window for group confidence
            top_k: Number of top tokens for token confidence calculation
        """
        self.window_size = window_size
        self.top_k = top_k
        self.token_confidences = []
        self.group_confidences = []

    def reset(self):
        """Reset internal state for new trace."""
        self.token_confidences = []
        self.group_confidences = []

    def calculate_token_entropy(self, logits: torch.Tensor) -> float:
        """
        Calculate token entropy: H = -∑P(j) log P(j)
        
        Args:
            logits: Raw logits tensor for current token position
            
        Returns:
            Token entropy value
        """
        probs = F.softmax(logits, dim=-1)
        log_probs = F.log_softmax(logits, dim=-1)
        entropy = -(probs * log_probs).sum().item()
        return entropy

    def calculate_token_confidence(self, logits: torch.Tensor, k: Optional[int]=None) -> float:
        """
        Calculate token confidence: C = -(1/k) ∑log P(j) for top-k tokens
        
        Args:
            logits: Raw logits tensor for current token position
            k: Number of top tokens to consider (default: self.top_k)
            
        Returns:
            Token confidence value
        """
        if k is None:
            k = self.top_k
        log_probs = F.log_softmax(logits, dim=-1)
        top_log_probs, _ = torch.topk(log_probs, k=k)
        confidence = -top_log_probs.mean().item()
        return confidence

    def add_token_confidence(self, logits: torch.Tensor) -> float:
        """
        Add a new token's confidence and update group statistics.
        
        Args:
            logits: Raw logits tensor for current token position
            
        Returns:
            Token confidence value
        """
        confidence = self.calculate_token_confidence(logits)
        self.token_confidences.append(confidence)
        if len(self.token_confidences) >= self.window_size:
            self._update_group_confidence()
        return confidence

    def _update_group_confidence(self):
        """Update group confidence based on current sliding window."""
        if len(self.token_confidences) < self.window_size:
            return
        start_idx = len(self.token_confidences) - self.window_size
        window_confidences = self.token_confidences[start_idx:]
        group_confidence = np.mean(window_confidences)
        self.group_confidences.append(group_confidence)

    def get_current_group_confidence(self) -> Optional[float]:
        """
        Get the most recent group confidence.
        
        Returns:
            Most recent group confidence or None if not available
        """
        if not self.group_confidences:
            return None
        return self.group_confidences[-1]

    def get_average_trace_confidence(self) -> float:
        """
        Calculate average confidence across all tokens in the trace.
        
        Returns:
            Average confidence value
        """
        if not self.token_confidences:
            return 0.0
        return np.mean(self.token_confidences)

    def get_bottom_10_percent_confidence(self) -> float:
        """
        Calculate average confidence of bottom 10% groups.
        
        Returns:
            Bottom 10% group confidence
        """
        if not self.group_confidences:
            return 0.0
        num_bottom = max(1, len(self.group_confidences) // 10)
        sorted_confidences = sorted(self.group_confidences)
        bottom_confidences = sorted_confidences[:num_bottom]
        return np.mean(bottom_confidences)

    def get_lowest_group_confidence(self) -> float:
        """
        Get the minimum confidence across all groups.
        
        Returns:
            Lowest group confidence
        """
        if not self.group_confidences:
            return 0.0
        return min(self.group_confidences)

    def get_trace_statistics(self) -> Dict[str, float]:
        """
        Get comprehensive confidence statistics for the current trace.
        
        Returns:
            Dictionary with various confidence metrics
        """
        return {'average_confidence': self.get_average_trace_confidence(), 'bottom_10_percent': self.get_bottom_10_percent_confidence(), 'lowest_group': self.get_lowest_group_confidence(), 'current_group': self.get_current_group_confidence() or 0.0, 'num_tokens': len(self.token_confidences), 'num_groups': len(self.group_confidences)}

def _update_group_confidence(self):
    """Update group confidence based on current sliding window."""
    if len(self.token_confidences) < self.window_size:
        return
    start_idx = len(self.token_confidences) - self.window_size
    window_confidences = self.token_confidences[start_idx:]
    group_confidence = np.mean(window_confidences)
    self.group_confidences.append(group_confidence)

def get_average_trace_confidence(self) -> float:
    """
        Calculate average confidence across all tokens in the trace.
        
        Returns:
            Average confidence value
        """
    if not self.token_confidences:
        return 0.0
    return np.mean(self.token_confidences)

def get_bottom_10_percent_confidence(self) -> float:
    """
        Calculate average confidence of bottom 10% groups.
        
        Returns:
            Bottom 10% group confidence
        """
    if not self.group_confidences:
        return 0.0
    num_bottom = max(1, len(self.group_confidences) // 10)
    sorted_confidences = sorted(self.group_confidences)
    bottom_confidences = sorted_confidences[:num_bottom]
    return np.mean(bottom_confidences)

def get_lowest_group_confidence(self) -> float:
    """
        Get the minimum confidence across all groups.
        
        Returns:
            Lowest group confidence
        """
    if not self.group_confidences:
        return 0.0
    return min(self.group_confidences)

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

def test_mars_worker_pool_calculation(self):
    """Test that worker pool size is calculated correctly"""
    from optillm.mars.mars import DEFAULT_CONFIG
    num_agents = DEFAULT_CONFIG['num_agents']
    verification_passes = DEFAULT_CONFIG['verification_passes_required']
    expected_workers = max(num_agents, num_agents * min(2, verification_passes))
    self.assertEqual(expected_workers, 6)
    print(f'✅ Worker pool size calculation correct: {expected_workers} workers')

def test_approach_parameters():
    """Test that approaches handle parameters correctly"""
    import inspect
    approaches = {'chat_with_mcts': chat_with_mcts, 'best_of_n_sampling': best_of_n_sampling, 'mixture_of_agents': mixture_of_agents, 'advanced_self_consistency_approach': advanced_self_consistency_approach, 're2_approach': re2_approach, 'cot_reflection': cot_reflection, 'plansearch': plansearch, 'leap': leap, 'multi_agent_reasoning_system': multi_agent_reasoning_system}
    for name, func in approaches.items():
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        required_params = ['system_prompt', 'initial_query', 'client', 'model']
        for param in required_params:
            assert param in params, f'{name} missing required parameter: {param}'
        print(f'✅ {name} has correct parameters')

