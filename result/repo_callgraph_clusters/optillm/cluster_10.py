# Cluster 10

class SimpleQAEvaluator:
    """Main evaluator class for SimpleQA benchmark"""

    def __init__(self, model: str, approach: str, base_url: str=DEFAULT_BASE_URL, grader_model: str=DEFAULT_GRADER_MODEL, timeout: int=DEFAULT_TIMEOUT, cache_dir: str='cache', output_dir: str='results', use_verified: bool=False):
        self.model = model
        self.approach = approach
        self.base_url = base_url
        self.grader_model = grader_model
        self.timeout = timeout
        self.use_verified = use_verified
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.optillm_client = OpenAI(api_key='optillm', base_url=base_url, timeout=httpx.Timeout(timeout, connect=5.0), max_retries=0)
        try:
            self.grader_client = OpenAI(api_key='optillm', base_url=base_url, timeout=httpx.Timeout(timeout, connect=5.0), max_retries=0)
            logger.info('Using OptILLM for grading responses')
        except Exception as e:
            logger.warning(f'Could not initialize grader client: {e}')
            logger.warning('Grading will be skipped.')
            self.grader_client = None
        self.results = []
        self.metrics = {'correct': 0, 'incorrect': 0, 'not_attempted': 0, 'errors': 0, 'total_processed': 0}

    def download_dataset(self) -> str:
        """Download SimpleQA dataset if not cached"""
        if self.use_verified:
            cache_file = self.cache_dir / 'simpleqa_verified.csv'
            url = SIMPLEQA_VERIFIED_CSV_URL
            dataset_name = 'SimpleQA-Verified'
        else:
            cache_file = self.cache_dir / 'simple_qa_test_set.csv'
            url = SIMPLEQA_CSV_URL
            dataset_name = 'SimpleQA'
        if cache_file.exists():
            logger.info(f'Using cached {dataset_name} dataset: {cache_file}')
            return str(cache_file)
        logger.info(f'Downloading {dataset_name} dataset from {url}')
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            logger.info(f'Dataset downloaded to {cache_file}')
            return str(cache_file)
        except Exception as e:
            logger.error(f'Failed to download dataset: {e}')
            raise

    def load_dataset(self, num_samples: Optional[int]=None, start_index: int=0) -> List[Dict]:
        """Load and parse SimpleQA dataset"""
        dataset_file = self.download_dataset()
        questions = []
        try:
            with open(dataset_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i < start_index:
                        continue
                    if num_samples and len(questions) >= num_samples:
                        break
                    if self.use_verified:
                        metadata = {'original_index': row.get('original_index', i), 'topic': row.get('topic', ''), 'answer_type': row.get('answer_type', ''), 'multi_step': row.get('multi_step', ''), 'requires_reasoning': row.get('requires_reasoning', ''), 'urls': row.get('urls', '')}
                        question_id = row.get('original_index', i)
                    else:
                        try:
                            metadata = json.loads(row['metadata']) if row.get('metadata') else {}
                        except:
                            metadata = {}
                        question_id = i
                    question_data = {'id': question_id, 'metadata': metadata, 'question': row['problem'], 'gold_answer': row['answer']}
                    questions.append(question_data)
            dataset_type = 'SimpleQA-Verified' if self.use_verified else 'SimpleQA'
            logger.info(f'Loaded {len(questions)} questions from {dataset_type} dataset')
            return questions
        except Exception as e:
            logger.error(f'Failed to load dataset: {e}')
            raise

    def get_approach_config(self) -> Dict:
        """Get configuration for specific approach"""
        if self.approach == 'none':
            return {}
        elif self.approach == 'web_search':
            return {'num_results': 10, 'headless': True, 'timeout': 30}
        elif self.approach == 'deep_research':
            return {'max_iterations': 1, 'max_sources': 10}
        else:
            return {}

    def query_optillm(self, question: str) -> Tuple[str, bool]:
        """Query OptILLM with the specified approach"""
        try:
            if self.approach == 'none':
                model_name = self.model
            else:
                model_name = f'{self.approach}-{self.model}'
            messages = [{'role': 'system', 'content': 'You are a helpful assistant that provides accurate, factual answers to questions. Be direct and concise.'}, {'role': 'user', 'content': question}]
            extra_body = {}
            approach_config = self.get_approach_config()
            if approach_config:
                extra_body.update(approach_config)
            logger.debug(f'Querying model: {model_name}')
            logger.debug(f'Question: {question}')
            response = self.optillm_client.chat.completions.create(model=model_name, messages=messages, extra_body=extra_body if extra_body else None, max_tokens=4096, temperature=0.6)
            answer = response.choices[0].message.content
            answer = remove_thinking_blocks(answer)
            logger.debug(f'Response: {answer}')
            return (answer, True)
        except Exception as e:
            logger.error(f'Error querying OptILLM: {e}')
            return (f'Error: {str(e)}', False)

    def grade_response(self, question: str, gold_answer: str, response: str) -> str:
        """Grade response using SimpleQA methodology"""
        if not self.grader_client:
            return 'NOT_GRADED'
        try:
            grading_prompt = GRADING_PROMPT.format(question=question, gold_answer=gold_answer, response=response)
            grader_response = self.grader_client.chat.completions.create(model=self.grader_model, messages=[{'role': 'user', 'content': grading_prompt}], temperature=0.6, max_tokens=4096)
            grade_text = grader_response.choices[0].message.content.strip()
            grade_text = re.sub('<think>.*?</think>', '', grade_text, flags=re.DOTALL).strip()
            if grade_text.startswith('A'):
                return 'CORRECT'
            elif grade_text.startswith('B'):
                return 'INCORRECT'
            elif grade_text.startswith('C'):
                return 'NOT_ATTEMPTED'
            else:
                logger.warning(f'Unexpected grade format: {grade_text}')
                return 'NOT_GRADED'
        except Exception as e:
            logger.error(f'Error grading response: {e}')
            return 'ERROR_GRADING'

    def evaluate_question(self, question_data: Dict) -> Dict:
        """Evaluate a single question"""
        question = question_data['question']
        gold_answer = question_data['gold_answer']
        response, success = self.query_optillm(question)
        result = {'id': question_data['id'], 'metadata': question_data['metadata'], 'question': question, 'gold_answer': gold_answer, 'response': response, 'success': success, 'timestamp': datetime.now().isoformat()}
        if success:
            grade = self.grade_response(question, gold_answer, response)
            result['grade'] = grade
            if grade == 'CORRECT':
                self.metrics['correct'] += 1
            elif grade == 'INCORRECT':
                self.metrics['incorrect'] += 1
            elif grade == 'NOT_ATTEMPTED':
                self.metrics['not_attempted'] += 1
        else:
            result['grade'] = 'ERROR'
            self.metrics['errors'] += 1
        self.metrics['total_processed'] += 1
        return result

    def calculate_metrics(self) -> Dict:
        """Calculate final evaluation metrics"""
        total = self.metrics['total_processed']
        correct = self.metrics['correct']
        incorrect = self.metrics['incorrect']
        not_attempted = self.metrics['not_attempted']
        errors = self.metrics['errors']
        if total == 0:
            return {'error': 'No questions processed'}
        accuracy = correct / total * 100 if total > 0 else 0
        attempted = correct + incorrect
        correct_given_attempted = correct / attempted * 100 if attempted > 0 else 0
        precision = correct / (correct + incorrect) if correct + incorrect > 0 else 0
        recall = correct / (correct + not_attempted) if correct + not_attempted > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
        return {'total_questions': total, 'correct': correct, 'incorrect': incorrect, 'not_attempted': not_attempted, 'errors': errors, 'accuracy': accuracy, 'correct_given_attempted': correct_given_attempted, 'precision': precision, 'recall': recall, 'f1_score': f1_score, 'attempted_rate': attempted / total * 100 if total > 0 else 0}

    def save_results(self, timestamp: str) -> Tuple[str, str, str]:
        """Save evaluation results to files"""
        dataset_suffix = '_verified' if self.use_verified else ''
        run_dir = self.output_dir / f'simpleqa{dataset_suffix}_{self.model}_{self.approach}'
        run_dir.mkdir(parents=True, exist_ok=True)
        detailed_file = run_dir / f'{timestamp}_detailed.json'
        metrics_file = run_dir / f'{timestamp}_metrics.json'
        summary_file = run_dir / f'{timestamp}_summary.csv'
        with open(detailed_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        final_metrics = self.calculate_metrics()
        final_metrics.update({'model': self.model, 'approach': self.approach, 'timestamp': timestamp, 'base_url': self.base_url, 'grader_model': self.grader_model})
        with open(metrics_file, 'w') as f:
            json.dump(final_metrics, f, indent=2)
        df = pd.DataFrame(self.results)
        df.to_csv(summary_file, index=False)
        logger.info(f'Results saved to {run_dir}')
        return (str(detailed_file), str(metrics_file), str(summary_file))

    def run_evaluation(self, num_samples: Optional[int]=None, start_index: int=0) -> Dict:
        """Run the complete evaluation"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dataset_type = 'SimpleQA-Verified' if self.use_verified else 'SimpleQA'
        logger.info(f'Starting {dataset_type} evaluation')
        logger.info(f'Model: {self.model}')
        logger.info(f'Approach: {self.approach}')
        logger.info(f'Dataset: {dataset_type} ({('1k verified questions' if self.use_verified else '4.3k questions')})')
        logger.info(f'Base URL: {self.base_url}')
        logger.info(f'Timeout: {self.timeout}s')
        questions = self.load_dataset(num_samples, start_index)
        for question_data in tqdm(questions, desc='Evaluating questions'):
            try:
                result = self.evaluate_question(question_data)
                self.results.append(result)
                if len(self.results) % 10 == 0:
                    metrics = self.calculate_metrics()
                    logger.info(f'Progress: {len(self.results)}/{len(questions)} - Accuracy: {metrics['accuracy']:.1f}%')
            except KeyboardInterrupt:
                logger.info('Evaluation interrupted by user')
                break
            except Exception as e:
                logger.error(f'Error evaluating question {question_data['id']}: {e}')
                continue
        detailed_file, metrics_file, summary_file = self.save_results(timestamp)
        final_metrics = self.calculate_metrics()
        logger.info('Evaluation completed!')
        logger.info(f'Total questions: {final_metrics['total_questions']}')
        logger.info(f'Accuracy: {final_metrics['accuracy']:.1f}%')
        logger.info(f'F1 Score: {final_metrics['f1_score']:.3f}')
        logger.info(f'Correct: {final_metrics['correct']}')
        logger.info(f'Incorrect: {final_metrics['incorrect']}')
        logger.info(f'Not Attempted: {final_metrics['not_attempted']}')
        return final_metrics

def load_dataset(self, num_samples: Optional[int]=None, start_index: int=0) -> List[Dict]:
    """Load and parse SimpleQA dataset"""
    dataset_file = self.download_dataset()
    questions = []
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i < start_index:
                    continue
                if num_samples and len(questions) >= num_samples:
                    break
                if self.use_verified:
                    metadata = {'original_index': row.get('original_index', i), 'topic': row.get('topic', ''), 'answer_type': row.get('answer_type', ''), 'multi_step': row.get('multi_step', ''), 'requires_reasoning': row.get('requires_reasoning', ''), 'urls': row.get('urls', '')}
                    question_id = row.get('original_index', i)
                else:
                    try:
                        metadata = json.loads(row['metadata']) if row.get('metadata') else {}
                    except:
                        metadata = {}
                    question_id = i
                question_data = {'id': question_id, 'metadata': metadata, 'question': row['problem'], 'gold_answer': row['answer']}
                questions.append(question_data)
        dataset_type = 'SimpleQA-Verified' if self.use_verified else 'SimpleQA'
        logger.info(f'Loaded {len(questions)} questions from {dataset_type} dataset')
        return questions
    except Exception as e:
        logger.error(f'Failed to load dataset: {e}')
        raise

def extract_first_turn_content(turns: List[Dict]) -> str:
    """Extract the content from the first turn in the conversation."""
    if not turns or not isinstance(turns, list):
        return ''
    return turns[0].get('content', '')

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

def suggest_mlx_alternative(model_id: str) -> str:
    """Suggest MLX alternative for a given model"""
    mlx_alternatives = {'Qwen/Qwen3-0.6B': 'mlx-community/Qwen3-0.6B-4bit', 'Qwen/Qwen3-1.7B': 'mlx-community/Qwen3-1.7B-4bit', 'Qwen/Qwen3-4B': 'mlx-community/Qwen3-4B-4bit', 'Qwen/Qwen3-8B': 'mlx-community/Qwen3-8B-4bit', 'Qwen/Qwen3-14B': 'mlx-community/Qwen3-14B-4bit', 'Qwen/Qwen3-32B': 'mlx-community/Qwen3-32B-4bit', 'google/gemma-3-1b-it': 'mlx-community/gemma-3-1b-it-4bit', 'google/gemma-3-4b-it': 'mlx-community/gemma-3-4b-it-4bit', 'google/gemma-3-12b-it': 'mlx-community/gemma-3-12b-it-4bit', 'google/gemma-3-27b-it': 'mlx-community/gemma-3-27b-it-4bit'}
    return mlx_alternatives.get(model_id, f'mlx-community/{model_id.split('/')[-1]}-4bit')

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

def get_model_adapters(self, model_key: str) -> List[str]:
    """Get list of adapter IDs loaded for a specific model."""
    with self._lock:
        return self.model_adapter_map.get(model_key, [])

@classmethod
def get_instance(cls, max_size: int=5) -> 'CacheManager':
    """Alternative way to get the singleton instance."""
    if cls._instance is None:
        return cls(max_size)
    return cls._instance

class InferencePipeline:

    def __init__(self, model_config: ModelConfig, cache_manager, device_manager, model_manager, lora_manager):
        self.model_config = model_config
        self.cache_manager = cache_manager
        self.device_manager = device_manager
        self.model_manager = model_manager
        self.lora_manager = lora_manager
        self.last_used = time.time()
        try:
            self.base_model, self.tokenizer = self.model_manager.load_base_model(model_config.base_model_id, quantize=model_config.quantization_bits == 4)
            self.tokenizer = self.setup_tokenizer(self.tokenizer)
            if self.base_model.get_input_embeddings().num_embeddings != len(self.tokenizer):
                self.base_model.resize_token_embeddings(len(self.tokenizer))
            self.current_model = self.base_model
            if model_config.adapter_ids:
                for adapter_id in model_config.adapter_ids:
                    try:
                        self.current_model = self.lora_manager.load_adapter(self.current_model, adapter_id)
                    except Exception as e:
                        logger.error(f'Error loading adapter {adapter_id}: {e}')
                if isinstance(self.current_model, PeftModel):
                    success = self.lora_manager.set_active_adapter(self.current_model)
                    if not success:
                        logger.error('Failed to set active adapter')
            self.dtype = self.current_model.dtype
            self.optimal_batch_size = self._find_optimal_batch_size()
        except Exception as e:
            logger.error(f'Pipeline initialization error: {str(e)}')
            logger.error(f'Error traceback: {traceback.format_exc()}')
            raise

    def setup_tokenizer(self, tokenizer: AutoTokenizer) -> AutoTokenizer:
        """Use tokenizer with its default configuration for inference"""
        logger.debug('  a. Starting tokenizer setup')
        logger.debug(f'  b. Using tokenizer with vocab size: {len(tokenizer)}')
        logger.debug(f'  c. Special tokens: PAD={tokenizer.pad_token_id}, EOS={tokenizer.eos_token_id}, BOS={tokenizer.bos_token_id}')
        return tokenizer

    def get_optimized_generation_config(self, generation_params: Optional[Dict[str, Any]]=None) -> Dict:
        """Get optimized generation config"""
        config = {'max_new_tokens': generation_params.get('max_new_tokens', 4096), 'do_sample': generation_params.get('temperature', 1.0) > 0, 'temperature': generation_params.get('temperature', 1.0), 'top_p': generation_params.get('top_p', 0.95), 'num_return_sequences': generation_params.get('num_return_sequences', 1), 'pad_token_id': self.tokenizer.pad_token_id, 'eos_token_id': self.tokenizer.eos_token_id, 'return_dict_in_generate': True, 'output_scores': generation_params.get('logprobs', False), 'use_cache': True}
        return config

    def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int]]:
        """Generate completions with optional logprobs"""
        start_time = time.time()
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        tokenize_start = time.time()
        inputs = self.tokenizer(prompt, padding=True, truncation=True, return_tensors='pt').to(self.current_model.device)
        logger.info(f'Tokenization time: {time.time() - tokenize_start:.2f}s')
        calculate_logprobs = generation_params.get('logprobs', False)
        top_logprobs = generation_params.get('top_logprobs', 0)
        if top_logprobs and (not calculate_logprobs):
            raise ValueError('logprobs must be true when top_logprobs is specified')
        if top_logprobs and (not 0 <= top_logprobs <= 20):
            raise ValueError('top_logprobs must be between 0 and 20')
        gen_config = self.get_optimized_generation_config(generation_params)
        if generation_params:
            if generation_params.get('presence_penalty', 0) != 0:
                gen_config['presence_penalty'] = generation_params['presence_penalty']
            if generation_params.get('frequency_penalty', 0) != 0:
                gen_config['repetition_penalty'] = 1.0 + generation_params['frequency_penalty']
            if generation_params.get('stop_sequences'):
                gen_config['stopping_criteria'] = self._create_stopping_criteria(generation_params['stop_sequences'], inputs['input_ids'].shape[1])
            if generation_params.get('seed') is not None:
                torch.manual_seed(generation_params['seed'])
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(generation_params['seed'])
        generate_start = time.time()
        with torch.inference_mode():
            outputs = self.current_model.generate(**inputs, **gen_config)
        logger.info(f'Generation time: {time.time() - generate_start:.2f}s')
        generated_sequences = outputs.sequences
        input_length = inputs['input_ids'].shape[1]
        process_start = time.time()
        responses = []
        token_counts = []
        logprobs_results = []
        for sequence in generated_sequences:
            response_tokens = sequence[input_length:]
            response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            responses.append(response_text)
            token_counts.append(len(response_tokens))
            if calculate_logprobs:
                calculator = LogProbsCalculator(self.tokenizer, self.current_model)
                logprobs_result = calculator.calculate_logprobs(input_ids=sequence.unsqueeze(0), generated_ids=sequence.unsqueeze(0), attention_mask=torch.ones_like(sequence).unsqueeze(0), num_alternatives=top_logprobs or 5)
                logprobs_results.append({'content': [{'token': token, 'logprob': logprob, 'bytes': bytes_, 'top_logprobs': top_logprobs} for token, logprob, bytes_, top_logprobs in zip(logprobs_result.tokens[input_length:], logprobs_result.token_logprobs[input_length:], logprobs_result.bytes_per_token[input_length:], logprobs_result.top_logprobs[input_length:])]})
            else:
                logprobs_results.append(None)
        logger.info(f'Post-processing time: {time.time() - process_start:.2f}s')
        logger.info(f'Total generation time: {time.time() - start_time:.2f}s')
        return (responses, token_counts, logprobs_results)

    def setup_efficient_attention(self):
        """Replace standard attention with memory-efficient version"""
        if hasattr(self.current_model, 'config') and hasattr(self.current_model.config, 'hidden_size'):
            hidden_size = self.current_model.config.hidden_size
            num_attention_heads = self.current_model.config.num_attention_heads
            self.efficient_attention = MemoryEfficientAttention(hidden_size, num_attention_heads)
            if hasattr(self.current_model, 'encoder') and hasattr(self.current_model.encoder, 'layer'):
                for layer in self.current_model.encoder.layer:
                    if hasattr(layer, 'attention'):
                        layer.attention.self = self.efficient_attention
            logger.info('Memory-efficient attention mechanism enabled')

    def _find_optimal_batch_size(self, initial_batch_size: int=1, max_batch_size: int=128) -> int:
        """Find optimal batch size through binary search with memory monitoring"""
        if not torch.cuda.is_available():
            return initial_batch_size
        device = self.current_model.device
        if 'cuda' not in str(device):
            return initial_batch_size
        left, right = (initial_batch_size, max_batch_size)
        optimal_size = initial_batch_size
        sample_text = 'Sample input text for batch size optimization.'
        while left <= right:
            mid = (left + right) // 2
            try:
                torch.cuda.empty_cache()
                inputs = self.tokenizer([sample_text] * mid, padding=True, truncation=True, return_tensors='pt').to(device)
                with torch.amp.autocast('cuda', dtype=self.dtype):
                    with torch.no_grad():
                        _ = self.current_model.generate(**inputs, max_new_tokens=1, num_return_sequences=1, pad_token_id=self.tokenizer.pad_token_id)
                optimal_size = mid
                left = mid + 1
                memory_used = torch.cuda.memory_allocated(device)
                total_memory = torch.cuda.get_device_properties(device).total_memory
                if memory_used > 0.9 * total_memory:
                    break
            except torch.cuda.OutOfMemoryError:
                right = mid - 1
                torch.cuda.empty_cache()
        return max(1, int(optimal_size * 0.9))

    def optimize_generation_params(self, prompt: str) -> Dict[str, Any]:
        """Optimize generation parameters based on prompt characteristics"""
        base_params = {'max_new_tokens': self.model_config.max_new_tokens, 'do_sample': self.model_config.do_sample, 'top_p': self.model_config.top_p, 'top_k': self.model_config.top_k, 'temperature': self.model_config.temperature, 'num_return_sequences': self.model_config.num_return_sequences, 'repetition_penalty': self.model_config.repetition_penalty, 'pad_token_id': self.model_config.pad_token_id or self.tokenizer.pad_token_id}
        if self.model_config.dynamic_temperature:
            base_params['temperature'] = self.dynamic_temperature.get_optimal_temperature(prompt, self.tokenizer, base_params['temperature'])
        return base_params

    def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format the prompt according to model's chat template"""
        if hasattr(self.tokenizer, 'apply_chat_template'):
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            return self.tokenizer.apply_chat_template(messages, tokenize=False)
        else:
            return f'<|system|>{system_prompt}</s><|user|>{user_prompt}</s><|assistant|>'

    def _create_stopping_criteria(self, stop_sequences: List[str], input_length: int):
        """Create stopping criteria for generation"""
        from transformers import StoppingCriteria, StoppingCriteriaList

        class StopSequenceCriteria(StoppingCriteria):

            def __init__(self, tokenizer, stop_sequences, input_length):
                self.tokenizer = tokenizer
                self.stop_ids = [self.tokenizer.encode(seq, add_special_tokens=False) for seq in stop_sequences]
                self.input_length = input_length

            def __call__(self, input_ids, scores, **kwargs):
                for stop_ids in self.stop_ids:
                    if input_ids[0, -len(stop_ids):].tolist() == stop_ids:
                        return True
                return False
        return StoppingCriteriaList([StopSequenceCriteria(self.tokenizer, stop_sequences, input_length=input_length)])

    def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
        """Process a batch of prompts with all optimizations"""
        if isinstance(self.current_model, PeftModel) and active_adapter is not None:
            self.lora_manager.set_active_adapter(self.current_model, active_adapter)
        all_responses = []
        token_counts = []
        formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
        n = generation_params.get('num_return_sequences', 1) if generation_params else 1
        for i in range(0, len(formatted_prompts), self.optimal_batch_size):
            batch_prompts = formatted_prompts[i:i + self.optimal_batch_size]
            batch_system = system_prompts[i:i + self.optimal_batch_size]
            batch_user = user_prompts[i:i + self.optimal_batch_size]
            if self.model_config.enable_prompt_caching:
                cached_responses = []
                uncached_indices = []
                for idx, prompt in enumerate(batch_prompts):
                    temp = generation_params.get('temperature', self.model_config.temperature) if generation_params else self.model_config.temperature
                    top_p = generation_params.get('top_p', self.model_config.top_p) if generation_params else self.model_config.top_p
                    cached_response = self.cache_manager.prompt_cache.get_cached_response(prompt, temp, top_p)
                    if cached_response is not None:
                        cached_responses.extend([cached_response] * n)
                    else:
                        uncached_indices.append(idx)
                if uncached_indices:
                    batch_prompts = [batch_prompts[i] for i in uncached_indices]
                else:
                    batch_prompts = []
            if batch_prompts:
                base_params = {'max_new_tokens': generation_params.get('max_new_tokens', 4096) if generation_params else self.model_config.max_new_tokens, 'do_sample': generation_params.get('temperature', 1.0) > 0 if generation_params else self.model_config.do_sample, 'temperature': generation_params.get('temperature', 1.0) if generation_params else self.model_config.temperature, 'top_p': generation_params.get('top_p', 1.0) if generation_params else self.model_config.top_p, 'num_return_sequences': n, 'pad_token_id': self.tokenizer.pad_token_id, 'eos_token_id': self.tokenizer.eos_token_id}
                if generation_params:
                    if generation_params.get('presence_penalty', 0) != 0:
                        base_params['presence_penalty'] = generation_params['presence_penalty']
                    if generation_params.get('frequency_penalty', 0) != 0:
                        base_params['repetition_penalty'] = 1.0 + generation_params['frequency_penalty']
                    if generation_params.get('logit_bias'):
                        base_params['logit_bias'] = generation_params['logit_bias']
                    if generation_params.get('seed') is not None:
                        torch.manual_seed(generation_params['seed'])
                        if torch.cuda.is_available():
                            torch.cuda.manual_seed(generation_params['seed'])
                inputs = self.tokenizer(batch_prompts, padding=True, truncation=True, return_tensors='pt').to(self.current_model.device)
                input_lengths = inputs['input_ids'].shape[1]
                if generation_params and generation_params.get('stop_sequences'):
                    base_params['stopping_criteria'] = self._create_stopping_criteria(generation_params['stop_sequences'], input_lengths)
                with torch.amp.autocast('cuda', dtype=self.dtype):
                    with torch.no_grad():
                        outputs = self.current_model.generate(**inputs, **base_params)
                batch_responses = []
                batch_token_counts = []
                num_return_sequences = base_params['num_return_sequences']
                for i in range(0, len(outputs), num_return_sequences):
                    sequences = outputs[i:i + num_return_sequences]
                    for seq in sequences:
                        response_tokens = seq[input_lengths:]
                        response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
                        batch_responses.append(response_text)
                        batch_token_counts.append(len(response_tokens))
                if self.model_config.enable_prompt_caching:
                    for prompt, response in zip(batch_prompts, batch_responses[::n]):
                        self.cache_manager.prompt_cache.add_to_cache(prompt, response, base_params['temperature'], base_params['top_p'])
                all_responses.extend(cached_responses)
                if uncached_indices:
                    response_idx = 0
                    for original_idx in range(len(formatted_prompts[i:i + self.optimal_batch_size])):
                        if original_idx in uncached_indices:
                            for _ in range(n):
                                while len(all_responses) < original_idx * n + _:
                                    all_responses.append('')
                                if response_idx < len(batch_responses):
                                    all_responses.append(batch_responses[response_idx])
                                    response_idx += 1
                if return_token_count:
                    token_counts.extend([0] * len(cached_responses))
                    token_counts.extend(batch_token_counts)
        if return_token_count:
            return (all_responses, token_counts)
        return (all_responses, [0] * len(all_responses))

def get_optimized_generation_config(self, generation_params: Optional[Dict[str, Any]]=None) -> Dict:
    """Get optimized generation config"""
    config = {'max_new_tokens': generation_params.get('max_new_tokens', 4096), 'do_sample': generation_params.get('temperature', 1.0) > 0, 'temperature': generation_params.get('temperature', 1.0), 'top_p': generation_params.get('top_p', 0.95), 'num_return_sequences': generation_params.get('num_return_sequences', 1), 'pad_token_id': self.tokenizer.pad_token_id, 'eos_token_id': self.tokenizer.eos_token_id, 'return_dict_in_generate': True, 'output_scores': generation_params.get('logprobs', False), 'use_cache': True}
    return config

def aggregate_paths_based_on_scores(paths: List[Tuple[str, float]]) -> Tuple[str, float]:
    """Aggregate multiple paths based on their confidence scores."""
    answer_scores = {}
    for answer, delta in paths:
        answer_scores[answer] = answer_scores.get(answer, 0) + delta
    best_answer = max(answer_scores, key=answer_scores.get)
    return (best_answer, answer_scores[best_answer])

def get_config():
    import httpx
    API_KEY = None
    ssl_verify = server_config.get('ssl_verify', True)
    ssl_cert_path = server_config.get('ssl_cert_path', '')
    if not ssl_verify:
        logger.warning('SSL certificate verification is DISABLED. This is insecure and should only be used for development.')
        http_client = httpx.Client(verify=False)
    elif ssl_cert_path:
        logger.info(f'Using custom CA certificate bundle: {ssl_cert_path}')
        http_client = httpx.Client(verify=ssl_cert_path)
    else:
        http_client = httpx.Client(verify=True)
    if os.environ.get('OPTILLM_API_KEY'):
        from optillm.inference import create_inference_client
        API_KEY = os.environ.get('OPTILLM_API_KEY')
        default_client = create_inference_client()
    elif os.environ.get('CEREBRAS_API_KEY'):
        API_KEY = os.environ.get('CEREBRAS_API_KEY')
        base_url = server_config['base_url']
        if base_url != '':
            default_client = Cerebras(api_key=API_KEY, base_url=base_url, http_client=http_client)
        else:
            default_client = Cerebras(api_key=API_KEY, http_client=http_client)
    elif os.environ.get('OPENAI_API_KEY'):
        API_KEY = os.environ.get('OPENAI_API_KEY')
        base_url = server_config['base_url']
        if base_url != '':
            default_client = OpenAI(api_key=API_KEY, base_url=base_url)
            logger.info(f'Created OpenAI client with base_url: {base_url}')
        else:
            default_client = OpenAI(api_key=API_KEY)
            logger.info('Created OpenAI client without base_url')
    elif os.environ.get('AZURE_OPENAI_API_KEY'):
        API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
        API_VERSION = os.environ.get('AZURE_API_VERSION')
        AZURE_ENDPOINT = os.environ.get('AZURE_API_BASE')
        if API_KEY is not None:
            default_client = AzureOpenAI(api_key=API_KEY, api_version=API_VERSION, azure_endpoint=AZURE_ENDPOINT, http_client=http_client)
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            azure_credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(azure_credential, 'https://cognitiveservices.azure.com/.default')
            default_client = AzureOpenAI(api_version=API_VERSION, azure_endpoint=AZURE_ENDPOINT, azure_ad_token_provider=token_provider, http_client=http_client)
    else:
        from optillm.litellm_wrapper import LiteLLMWrapper
        default_client = LiteLLMWrapper()
        logger.info('Created LiteLLMWrapper as fallback')
    logger.info(f'Client type: {type(default_client)}')
    return (default_client, API_KEY)

def execute_combined_approaches(approaches, system_prompt, initial_query, client, model, request_config: dict=None):
    final_response = initial_query
    total_tokens = 0
    for approach in approaches:
        response, tokens = execute_single_approach(approach, system_prompt, final_response, client, model, request_config)
        final_response = response
        total_tokens += tokens
    return (final_response, total_tokens)

def extract_contents(response_obj):
    contents = []
    responses = response_obj if isinstance(response_obj, list) else [response_obj]
    for response in responses:
        if response.get('choices') and len(response['choices']) > 0 and response['choices'][0].get('message') and response['choices'][0]['message'].get('content'):
            contents.append(response['choices'][0]['message']['content'])
    return contents

@app.before_request
def check_api_key():
    if server_config['optillm_api_key']:
        if request.path == '/health':
            return
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return (jsonify({'error': "Invalid Authorization header. Expected format: 'Authorization: Bearer YOUR_API_KEY'"}), 401)
        client_key = auth_header.split('Bearer ', 1)[1].strip()
        if not secrets.compare_digest(client_key, server_config['optillm_api_key']):
            return (jsonify({'error': 'Invalid API key'}), 401)

@app.route('/v1/chat/completions', methods=['POST'])
def proxy():
    logger.info('Received request to /v1/chat/completions')
    data = request.get_json()
    auth_header = request.headers.get('Authorization')
    bearer_token = ''
    if auth_header and auth_header.startswith('Bearer '):
        bearer_token = auth_header.split('Bearer ')[1].strip()
        logger.debug(f'Intercepted Bearer Token: {bearer_token}')
    logger.debug(f'Request data: {data}')
    stream = data.get('stream', False)
    messages = data.get('messages', [])
    model = data.get('model', server_config['model'])
    n = data.get('n', server_config['n'])
    response_format = data.get('response_format', None)
    explicit_keys = {'stream', 'messages', 'model', 'n', 'response_format'}
    request_config = {k: v for k, v in data.items() if k not in explicit_keys}
    request_config.update({'stream': stream, 'n': n, 'response_format': response_format})
    optillm_approach = data.get('optillm_approach', server_config['approach'])
    logger.debug(data)
    server_config['mcts_depth'] = data.get('mcts_depth', server_config['mcts_depth'])
    server_config['mcts_exploration'] = data.get('mcts_exploration', server_config['mcts_exploration'])
    server_config['mcts_simulations'] = data.get('mcts_simulations', server_config['mcts_simulations'])
    system_prompt, initial_query, message_optillm_approach = parse_conversation(messages)
    if message_optillm_approach:
        optillm_approach = message_optillm_approach
    if optillm_approach != 'auto':
        model = f'{optillm_approach}-{model}'
    base_url = server_config['base_url']
    default_client, api_key = get_config()
    operation, approaches, model = parse_combined_approach(model, known_approaches, plugin_approaches)
    request_id = None
    if conversation_logger and conversation_logger.enabled:
        request_id = conversation_logger.start_conversation(client_request={'messages': messages, 'model': data.get('model', server_config['model']), 'stream': stream, 'n': n, **{k: v for k, v in data.items() if k not in {'messages', 'model', 'stream', 'n'}}}, approach=approaches[0] if len(approaches) == 1 else f'{operation}({','.join(approaches)})', model=model)
    request_id_str = f' [Request: {request_id}]' if request_id else ''
    logger.info(f'Using approach(es) {approaches}, operation {operation}, with model {model}{request_id_str}')
    if request_id:
        logger.info(f'Request {request_id}: Starting processing')
    if bearer_token != '' and bearer_token.startswith('sk-'):
        api_key = bearer_token
        if base_url != '':
            client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            client = OpenAI(api_key=api_key)
    else:
        client = default_client
    try:
        if request_batcher is not None:
            try:
                batch_request_data = {'system_prompt': system_prompt, 'initial_query': initial_query, 'client': client, 'model': model, 'request_config': request_config, 'approaches': approaches, 'operation': operation, 'n': n, 'stream': stream, 'optillm_approach': optillm_approach}
                logger.debug('Routing request to batch processor')
                result = request_batcher.add_request(batch_request_data)
                return (jsonify(result), 200)
            except BatchingError as e:
                logger.error(f'Batch processing failed: {e}')
                return (jsonify({'error': str(e)}), 500)
        contains_none = any((approach == 'none' for approach in approaches))
        if operation == 'SINGLE' and approaches[0] == 'none':
            result, completion_tokens = execute_single_approach(approaches[0], system_prompt, initial_query, client, model, request_config, request_id)
            logger.debug(f'Direct proxy response: {result}')
            if conversation_logger and request_id:
                conversation_logger.log_final_response(request_id, result)
                conversation_logger.finalize_conversation(request_id)
            if stream:
                if request_id:
                    logger.info(f'Request {request_id}: Completed (streaming response)')
                return Response(generate_streaming_response(extract_contents(result), model), content_type='text/event-stream')
            else:
                if request_id:
                    logger.info(f'Request {request_id}: Completed')
                return (jsonify(result), 200)
        elif operation == 'AND' or operation == 'OR':
            if contains_none:
                raise ValueError("'none' approach cannot be combined with other approaches")
        response, completion_tokens = execute_n_times(n, approaches, operation, system_prompt, initial_query, client, model, request_config, request_id)
        if operation == 'SINGLE' and isinstance(response, dict) and ('choices' in response) and ('usage' in response):
            if conversation_logger and request_id:
                conversation_logger.log_final_response(request_id, response)
                conversation_logger.finalize_conversation(request_id)
            if stream:
                if request_id:
                    logger.info(f'Request {request_id}: Completed (streaming response)')
                return Response(generate_streaming_response(extract_contents(response), model), content_type='text/event-stream')
            else:
                if request_id:
                    logger.info(f'Request {request_id}: Completed')
                return (jsonify(response), 200)
    except Exception as e:
        if conversation_logger and request_id:
            conversation_logger.log_error(request_id, str(e))
            conversation_logger.finalize_conversation(request_id)
        request_id_str = f' {request_id}' if request_id else ''
        logger.error(f'Error processing request{request_id_str}: {str(e)}')
        return (jsonify({'error': str(e)}), 500)
    if isinstance(response, list):
        processed_response = tagged_conversation_to_messages(response)
        if processed_response != response:
            response = [msg[-1]['content'] if isinstance(msg, list) and msg else msg for msg in processed_response]
    else:
        messages = tagged_conversation_to_messages(response)
        if isinstance(messages, list) and messages:
            response = messages[-1]['content']
    if stream:
        return Response(generate_streaming_response(response, model), content_type='text/event-stream')
    else:
        reasoning_tokens = 0
        if isinstance(response, str):
            reasoning_tokens = count_reasoning_tokens(response)
        elif isinstance(response, list) and response:
            reasoning_tokens = sum((count_reasoning_tokens(resp) for resp in response if isinstance(resp, str)))
        response_data = {'model': model, 'choices': [], 'usage': {'completion_tokens': completion_tokens, 'completion_tokens_details': {'reasoning_tokens': reasoning_tokens}}}
        if isinstance(response, list):
            for index, resp in enumerate(response):
                response_data['choices'].append({'index': index, 'message': {'role': 'assistant', 'content': resp}, 'finish_reason': 'stop'})
        else:
            response_data['choices'].append({'index': 0, 'message': {'role': 'assistant', 'content': response}, 'finish_reason': 'stop'})
        if conversation_logger and request_id:
            conversation_logger.log_final_response(request_id, response_data)
            conversation_logger.finalize_conversation(request_id)
        logger.debug(f'API response: {response_data}')
        if request_id:
            logger.info(f'Request {request_id}: Completed')
        return (jsonify(response_data), 200)

@app.route('/v1/models', methods=['GET'])
def proxy_models():
    logger.info('Received request to /v1/models')
    default_client, API_KEY = get_config()
    try:
        if server_config['base_url']:
            client = OpenAI(api_key=API_KEY, base_url=server_config['base_url'])
            models_response = client.models.list()
            models_data = {'object': 'list', 'data': [model.dict() for model in models_response.data]}
        else:
            current_model = server_config.get('model', 'gpt-3.5-turbo')
            models_data = {'object': 'list', 'data': [{'id': current_model, 'object': 'model', 'created': 1677610602, 'owned_by': 'optillm'}]}
        logger.debug('Models retrieved successfully')
        return (jsonify(models_data), 200)
    except Exception as e:
        logger.error(f'Error fetching models: {str(e)}')
        return (jsonify({'error': f'Error fetching models: {str(e)}'}), 500)

@app.route('/health', methods=['GET'])
def health():
    return (jsonify({'status': 'ok'}), 200)

def main():
    global server_config
    global cepo_config
    global request_batcher
    global conversation_logger
    load_plugins()
    args = parse_args()
    server_config.update(vars(args))
    port = server_config['port']
    if server_config.get('batch_mode', False):
        logger.info(f'Batch mode enabled: size={server_config['batch_size']}, wait={server_config['batch_wait_ms']}ms')
        request_batcher = RequestBatcher(max_batch_size=server_config['batch_size'], max_wait_ms=server_config['batch_wait_ms'], enable_logging=True)

        def process_batch_requests(batch_requests):
            """
            Process a batch of requests using true batching when possible
            
            Args:
                batch_requests: List of request data dictionaries
                
            Returns:
                List of response dictionaries
            """
            import time
            from optillm.batching import BatchingError
            if not batch_requests:
                return []
            logger.info(f'Processing batch of {len(batch_requests)} requests')
            can_use_true_batching = True
            first_req = batch_requests[0]
            for req_data in batch_requests:
                if req_data['stream'] or req_data['approaches'] != first_req['approaches'] or req_data['operation'] != first_req['operation'] or (req_data['model'] != first_req['model']):
                    can_use_true_batching = False
                    break
            responses = []
            for i, req_data in enumerate(batch_requests):
                try:
                    logger.debug(f'Processing batch request {i + 1}/{len(batch_requests)}')
                    system_prompt = req_data['system_prompt']
                    initial_query = req_data['initial_query']
                    client = req_data['client']
                    model = req_data['model']
                    request_config = req_data['request_config']
                    approaches = req_data['approaches']
                    operation = req_data['operation']
                    n = req_data['n']
                    stream = req_data['stream']
                    if stream:
                        raise BatchingError('Streaming requests cannot be batched')
                    contains_none = any((approach == 'none' for approach in approaches))
                    if operation == 'SINGLE' and approaches[0] == 'none':
                        result, completion_tokens = execute_single_approach(approaches[0], system_prompt, initial_query, client, model, request_config)
                    elif operation == 'AND' or operation == 'OR':
                        if contains_none:
                            raise ValueError("'none' approach cannot be combined with other approaches")
                        result, completion_tokens = execute_n_times(n, approaches, operation, system_prompt, initial_query, client, model, request_config)
                    else:
                        result, completion_tokens = execute_n_times(n, approaches, operation, system_prompt, initial_query, client, model, request_config)
                    if isinstance(result, list):
                        processed_response = tagged_conversation_to_messages(result)
                        if processed_response != result:
                            result = [msg[-1]['content'] if isinstance(msg, list) and msg else msg for msg in processed_response]
                    else:
                        messages = tagged_conversation_to_messages(result)
                        if isinstance(messages, list) and messages:
                            result = messages[-1]['content']
                    if isinstance(result, list):
                        choices = []
                        for j, res in enumerate(result):
                            choices.append({'index': j, 'message': {'role': 'assistant', 'content': res}, 'finish_reason': 'stop'})
                    else:
                        choices = [{'index': 0, 'message': {'role': 'assistant', 'content': result}, 'finish_reason': 'stop'}]
                    response_dict = {'id': f'chatcmpl-{int(time.time() * 1000)}-{i}', 'object': 'chat.completion', 'created': int(time.time()), 'model': model, 'choices': choices, 'usage': {'prompt_tokens': 0, 'completion_tokens': completion_tokens if isinstance(completion_tokens, int) else 0, 'total_tokens': completion_tokens if isinstance(completion_tokens, int) else 0}}
                    responses.append(response_dict)
                except Exception as e:
                    logger.error(f'Error processing batch request {i + 1}: {e}')
                    raise BatchingError(f'Failed to process request {i + 1}: {str(e)}')
            logger.info(f'Completed batch processing of {len(responses)} requests')
            return responses
        request_batcher.set_processor(process_batch_requests)
    logging_level = server_config['log']
    if logging_level in logging_levels.keys():
        logger.setLevel(logging_levels[logging_level])
    global conversation_logger
    conversation_logger = ConversationLogger(log_dir=Path(server_config['conversation_log_dir']), enabled=server_config['log_conversations'])
    optillm.conversation_logger.set_global_logger(conversation_logger)
    if server_config['log_conversations']:
        logger.info(f'Conversation logging enabled. Logs will be saved to: {server_config['conversation_log_dir']}')
    cepo_config = init_cepo_config(server_config)
    if args.approach == 'cepo':
        logger.info(f'CePO Config: {cepo_config}')
    logger.info(f'Starting server with approach: {server_config['approach']}')
    server_config_clean = server_config.copy()
    if server_config_clean['optillm_api_key']:
        server_config_clean['optillm_api_key'] = '[REDACTED]'
    logger.info(f'Server configuration: {server_config_clean}')
    if server_config.get('launch_gui'):
        try:
            import gradio as gr
            import threading
            server_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': port})
            server_thread.daemon = True
            server_thread.start()
            base_url = f'http://localhost:{port}/v1'
            logger.info(f'Launching Gradio interface connected to {base_url}')

            def chat_with_optillm(message, history):
                import httpx
                from openai import OpenAI
                custom_client = OpenAI(api_key='optillm', base_url=base_url, timeout=httpx.Timeout(1800.0, connect=5.0), max_retries=0)
                messages = []
                for h in history:
                    if h[0]:
                        messages.append({'role': 'user', 'content': h[0]})
                    if h[1]:
                        messages.append({'role': 'assistant', 'content': h[1]})
                messages.append({'role': 'user', 'content': message})
                try:
                    response = custom_client.chat.completions.create(model=server_config['model'], messages=messages)
                    return response.choices[0].message.content
                except Exception as e:
                    return f'Error: {str(e)}'
            demo = gr.ChatInterface(chat_with_optillm, title='OptILLM Chat Interface', description=f'Connected to OptILLM proxy at {base_url}')
            demo.queue()
            demo.launch(server_name='0.0.0.0', share=False)
        except ImportError:
            logger.error('Gradio is required for GUI. Install it with: pip install gradio')
            return
    app.run(host='0.0.0.0', port=port)

def process_batch_requests(batch_requests):
    """
            Process a batch of requests using true batching when possible
            
            Args:
                batch_requests: List of request data dictionaries
                
            Returns:
                List of response dictionaries
            """
    import time
    from optillm.batching import BatchingError
    if not batch_requests:
        return []
    logger.info(f'Processing batch of {len(batch_requests)} requests')
    can_use_true_batching = True
    first_req = batch_requests[0]
    for req_data in batch_requests:
        if req_data['stream'] or req_data['approaches'] != first_req['approaches'] or req_data['operation'] != first_req['operation'] or (req_data['model'] != first_req['model']):
            can_use_true_batching = False
            break
    responses = []
    for i, req_data in enumerate(batch_requests):
        try:
            logger.debug(f'Processing batch request {i + 1}/{len(batch_requests)}')
            system_prompt = req_data['system_prompt']
            initial_query = req_data['initial_query']
            client = req_data['client']
            model = req_data['model']
            request_config = req_data['request_config']
            approaches = req_data['approaches']
            operation = req_data['operation']
            n = req_data['n']
            stream = req_data['stream']
            if stream:
                raise BatchingError('Streaming requests cannot be batched')
            contains_none = any((approach == 'none' for approach in approaches))
            if operation == 'SINGLE' and approaches[0] == 'none':
                result, completion_tokens = execute_single_approach(approaches[0], system_prompt, initial_query, client, model, request_config)
            elif operation == 'AND' or operation == 'OR':
                if contains_none:
                    raise ValueError("'none' approach cannot be combined with other approaches")
                result, completion_tokens = execute_n_times(n, approaches, operation, system_prompt, initial_query, client, model, request_config)
            else:
                result, completion_tokens = execute_n_times(n, approaches, operation, system_prompt, initial_query, client, model, request_config)
            if isinstance(result, list):
                processed_response = tagged_conversation_to_messages(result)
                if processed_response != result:
                    result = [msg[-1]['content'] if isinstance(msg, list) and msg else msg for msg in processed_response]
            else:
                messages = tagged_conversation_to_messages(result)
                if isinstance(messages, list) and messages:
                    result = messages[-1]['content']
            if isinstance(result, list):
                choices = []
                for j, res in enumerate(result):
                    choices.append({'index': j, 'message': {'role': 'assistant', 'content': res}, 'finish_reason': 'stop'})
            else:
                choices = [{'index': 0, 'message': {'role': 'assistant', 'content': result}, 'finish_reason': 'stop'}]
            response_dict = {'id': f'chatcmpl-{int(time.time() * 1000)}-{i}', 'object': 'chat.completion', 'created': int(time.time()), 'model': model, 'choices': choices, 'usage': {'prompt_tokens': 0, 'completion_tokens': completion_tokens if isinstance(completion_tokens, int) else 0, 'total_tokens': completion_tokens if isinstance(completion_tokens, int) else 0}}
            responses.append(response_dict)
        except Exception as e:
            logger.error(f'Error processing batch request {i + 1}: {e}')
            raise BatchingError(f'Failed to process request {i + 1}: {str(e)}')
    logger.info(f'Completed batch processing of {len(responses)} requests')
    return responses

class MARSWorkspace:
    """Shared workspace for agent collaboration and solution tracking"""

    def __init__(self, problem: str, config: Dict[str, Any]):
        self.problem = problem
        self.config = config
        self.solutions: List[AgentSolution] = []
        self.verification_results: List[VerificationResult] = []
        self.synthesis_attempts: List[Dict] = []
        self.final_solution: Optional[str] = None
        self.iteration_count = 0
        self.total_reasoning_tokens = 0
        logger.info(f'Initialized MARS workspace for problem: {problem[:100]}...')

    def add_solution(self, agent_solution: AgentSolution) -> str:
        """Add a new agent solution to the workspace"""
        solution_id = f'agent_{agent_solution.agent_id}_iter_{self.iteration_count}'
        self.solutions.append(agent_solution)
        self.total_reasoning_tokens += agent_solution.reasoning_tokens
        logger.info(f'Added solution {solution_id} with {agent_solution.reasoning_tokens} reasoning tokens')
        return solution_id

    def add_verification(self, verification: VerificationResult):
        """Add a verification result to the workspace"""
        self.verification_results.append(verification)
        if verification.solution_id.startswith('agent_'):
            try:
                agent_id_str = verification.solution_id.split('_')[1]
                for solution in self.solutions:
                    if str(solution.agent_id) == agent_id_str:
                        solution.verification_results.append({'assessment': verification.assessment, 'confidence': verification.confidence, 'issues': verification.issues, 'detailed_report': verification.detailed_report})
                        verified_count = len([v for v in solution.verification_results if v['assessment'] == 'CORRECT'])
                        total_verifications = len(solution.verification_results)
                        solution.verification_score = verified_count / total_verifications if total_verifications > 0 else 0
                        consecutive_correct = 0
                        for v in reversed(solution.verification_results):
                            if v['assessment'] == 'CORRECT':
                                consecutive_correct += 1
                            else:
                                break
                        verification_threshold = self.config.get('verification_passes_required', 5)
                        solution.is_verified = consecutive_correct >= verification_threshold
                        break
            except (IndexError, ValueError):
                logger.warning(f'Invalid solution_id format: {verification.solution_id}')
        logger.info(f'Added verification for {verification.solution_id}: {verification.assessment}')

    def get_verified_solutions(self) -> List[AgentSolution]:
        """Get all solutions that have passed verification"""
        return [s for s in self.solutions if s.is_verified]

    def get_best_solution(self) -> Optional[AgentSolution]:
        """Get the best solution based on verification score and confidence"""
        if not self.solutions:
            return None
        verified_solutions = self.get_verified_solutions()
        if verified_solutions:
            return max(verified_solutions, key=lambda s: s.confidence)
        else:
            return max(self.solutions, key=lambda s: s.verification_score)

    def has_consensus(self) -> bool:
        """Check if we have enough verified solutions to reach consensus"""
        verified_count = len(self.get_verified_solutions())
        required_consensus = self.config.get('consensus_threshold', 2)
        return verified_count >= required_consensus

    def should_continue_iteration(self) -> bool:
        """Determine if we should continue with another iteration"""
        max_iterations = self.config.get('max_iterations', 5)
        min_verified = self.config.get('min_verified_solutions', 1)
        return self.iteration_count < max_iterations and len(self.get_verified_solutions()) < min_verified

    def get_synthesis_input(self) -> Dict[str, Any]:
        """Prepare input data for solution synthesis"""
        return {'problem': self.problem, 'solutions': [{'agent_id': s.agent_id, 'solution': s.solution, 'confidence': s.confidence, 'verification_score': s.verification_score, 'verification_results': s.verification_results} for s in self.solutions], 'verification_summary': self._get_verification_summary(), 'total_reasoning_tokens': self.total_reasoning_tokens}

    def _get_verification_summary(self) -> Dict[str, Any]:
        """Generate a summary of all verification results"""
        total_verifications = len(self.verification_results)
        if total_verifications == 0:
            return {'total': 0, 'correct': 0, 'incorrect': 0, 'incomplete': 0}
        assessments = [v.assessment for v in self.verification_results]
        return {'total': total_verifications, 'correct': assessments.count('CORRECT'), 'incorrect': assessments.count('INCORRECT'), 'incomplete': assessments.count('INCOMPLETE'), 'avg_confidence': sum((v.confidence for v in self.verification_results)) / total_verifications}

    def set_final_solution(self, solution: str):
        """Set the final synthesized solution"""
        self.final_solution = solution
        logger.info('Final solution set in workspace')

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workspace state"""
        return {'problem': self.problem, 'total_solutions': len(self.solutions), 'verified_solutions': len(self.get_verified_solutions()), 'total_verifications': len(self.verification_results), 'iterations_completed': self.iteration_count, 'total_reasoning_tokens': self.total_reasoning_tokens, 'has_consensus': self.has_consensus(), 'final_solution': self.final_solution, 'verification_summary': self._get_verification_summary()}

def get_best_solution(self) -> Optional[AgentSolution]:
    """Get the best solution based on verification score and confidence"""
    if not self.solutions:
        return None
    verified_solutions = self.get_verified_solutions()
    if verified_solutions:
        return max(verified_solutions, key=lambda s: s.confidence)
    else:
        return max(self.solutions, key=lambda s: s.verification_score)

def has_consensus(self) -> bool:
    """Check if we have enough verified solutions to reach consensus"""
    verified_count = len(self.get_verified_solutions())
    required_consensus = self.config.get('consensus_threshold', 2)
    return verified_count >= required_consensus

def should_continue_iteration(self) -> bool:
    """Determine if we should continue with another iteration"""
    max_iterations = self.config.get('max_iterations', 5)
    min_verified = self.config.get('min_verified_solutions', 1)
    return self.iteration_count < max_iterations and len(self.get_verified_solutions()) < min_verified

def get_synthesis_input(self) -> Dict[str, Any]:
    """Prepare input data for solution synthesis"""
    return {'problem': self.problem, 'solutions': [{'agent_id': s.agent_id, 'solution': s.solution, 'confidence': s.confidence, 'verification_score': s.verification_score, 'verification_results': s.verification_results} for s in self.solutions], 'verification_summary': self._get_verification_summary(), 'total_reasoning_tokens': self.total_reasoning_tokens}

def get_summary(self) -> Dict[str, Any]:
    """Get a summary of the workspace state"""
    return {'problem': self.problem, 'total_solutions': len(self.solutions), 'verified_solutions': len(self.get_verified_solutions()), 'total_verifications': len(self.verification_results), 'iterations_completed': self.iteration_count, 'total_reasoning_tokens': self.total_reasoning_tokens, 'has_consensus': self.has_consensus(), 'final_solution': self.final_solution, 'verification_summary': self._get_verification_summary()}

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

def __init__(self, client, model: str, config: Dict[str, Any]):
    self.client = client
    self.model = model
    self.config = config
    self.population_size = config.get('population_size', 6)
    self.aggregation_size = config.get('aggregation_size', 3)
    self.aggregation_loops = config.get('aggregation_loops', 3)
    self.max_tokens = config.get('max_tokens', 30000)

def _log_solution_overview(workspace: MARSWorkspace):
    """Log comprehensive overview of all solutions before synthesis"""
    logger.info(f'📋 SOLUTION OVERVIEW: Analyzing {len(workspace.solutions)} solutions before synthesis')
    total_chars = sum((len(sol.solution) for sol in workspace.solutions))
    avg_chars = total_chars / len(workspace.solutions) if workspace.solutions else 0
    verified_solutions = workspace.get_verified_solutions()
    logger.info(f'📋 SOLUTION OVERVIEW: Statistics:')
    logger.info(f'📋 SOLUTION OVERVIEW:   Total solutions: {len(workspace.solutions)}')
    logger.info(f'📋 SOLUTION OVERVIEW:   Verified solutions: {len(verified_solutions)}')
    logger.info(f'📋 SOLUTION OVERVIEW:   Total characters: {total_chars:,}')
    logger.info(f'📋 SOLUTION OVERVIEW:   Average length: {avg_chars:.0f} chars')
    for i, solution in enumerate(workspace.solutions):
        status = '✅ VERIFIED' if solution.is_verified else '❌ UNVERIFIED'
        logger.info(f'📋 SOLUTION OVERVIEW: Solution {i + 1} (Agent {solution.agent_id}):')
        logger.info(f'📋 SOLUTION OVERVIEW:   Status: {status}')
        logger.info(f'📋 SOLUTION OVERVIEW:   Length: {len(solution.solution):,} chars')
        logger.info(f'📋 SOLUTION OVERVIEW:   Confidence: {solution.confidence:.2f}')
        logger.info(f'📋 SOLUTION OVERVIEW:   Verification score: {solution.verification_score:.2f}')
        logger.info(f'📋 SOLUTION OVERVIEW:   Reasoning tokens: {solution.reasoning_tokens:,}')
        logger.info(f'📋 SOLUTION OVERVIEW:   Temperature: {solution.temperature}')
        preview = solution.solution[:300].replace('\n', ' ').strip()
        if len(solution.solution) > 300:
            preview += '...'
        logger.info(f'📋 SOLUTION OVERVIEW:   Preview: {preview}')

class MARSVerifier:
    """Multi-pass verification system inspired by IMO25 solver"""

    def __init__(self, agents: List[MARSAgent], workspace: MARSWorkspace, config: Dict[str, Any]):
        self.agents = agents
        self.workspace = workspace
        self.config = config
        self.verification_threshold = config.get('verification_passes_required', 5)

    def verify_solutions(self, request_id: str=None) -> Dict[str, Any]:
        """Run comprehensive verification on all solutions in workspace"""
        logger.info(f'Starting verification process with {self.verification_threshold}-pass threshold')
        verification_summary = {'total_verifications': 0, 'solutions_verified': 0, 'consensus_reached': False, 'verification_details': []}
        solutions = self.workspace.solutions
        if not solutions:
            logger.warning('No solutions to verify')
            return verification_summary
        for solution in solutions:
            solution_verification = self._verify_single_solution(solution, request_id)
            verification_summary['verification_details'].append(solution_verification)
            verification_summary['total_verifications'] += solution_verification['verification_count']
            if solution_verification['passes_threshold']:
                verification_summary['solutions_verified'] += 1
        verified_solutions = self.workspace.get_verified_solutions()
        verification_summary['consensus_reached'] = len(verified_solutions) >= self.config.get('consensus_threshold', 2)
        logger.info(f'Verification complete: {verification_summary['solutions_verified']} solutions verified')
        return verification_summary

    async def verify_solutions_parallel(self, request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, Any]:
        """Run comprehensive verification on all solutions in workspace with parallel execution"""
        logger.info(f'Starting parallel verification process with {self.verification_threshold}-pass threshold')
        verification_summary = {'total_verifications': 0, 'solutions_verified': 0, 'consensus_reached': False, 'verification_details': []}
        solutions = self.workspace.solutions
        if not solutions:
            logger.warning('No solutions to verify')
            return verification_summary

        async def verify_solution_async(solution: AgentSolution):
            """Async wrapper for single solution verification"""
            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(executor, self._verify_single_solution, solution, request_id)
                return result
            except Exception as e:
                logger.error(f'Verification failed for solution from agent {solution.agent_id}: {str(e)}')
                return {'solution_agent_id': solution.agent_id, 'verification_count': 0, 'consecutive_passes': 0, 'passes_threshold': False, 'verification_results': []}
        tasks = [verify_solution_async(solution) for solution in solutions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Verification task failed: {str(result)}')
                continue
            verification_summary['verification_details'].append(result)
            verification_summary['total_verifications'] += result['verification_count']
            if result['passes_threshold']:
                verification_summary['solutions_verified'] += 1
        verified_solutions = self.workspace.get_verified_solutions()
        verification_summary['consensus_reached'] = len(verified_solutions) >= self.config.get('consensus_threshold', 2)
        logger.info(f'Parallel verification complete: {verification_summary['solutions_verified']} solutions verified')
        return verification_summary

    def _verify_single_solution(self, solution: AgentSolution, request_id: str=None) -> Dict[str, Any]:
        """Verify a single solution with multiple passes"""
        logger.info(f'Verifying solution from agent {solution.agent_id}')
        verification_results = []
        consecutive_passes = 0
        max_verification_attempts = self.config.get('max_verification_attempts', 10)
        for attempt in range(max_verification_attempts):
            verifier_agent = self._select_verifier_agent(solution.agent_id)
            if not verifier_agent:
                logger.warning('No suitable verifier agent available')
                break
            try:
                verification = verifier_agent.verify_solution(problem=self.workspace.problem, solution=solution.solution, verifier_id=verifier_agent.agent_id, solution_agent_id=solution.agent_id, request_id=request_id)
                verification_results.append(verification)
                self.workspace.add_verification(verification)
                if verification.assessment == 'CORRECT':
                    consecutive_passes += 1
                    logger.info(f'Verification pass {consecutive_passes}/{self.verification_threshold}')
                    if consecutive_passes >= self.verification_threshold:
                        logger.info(f'Solution from agent {solution.agent_id} passed {self.verification_threshold}-pass verification')
                        break
                else:
                    consecutive_passes = 0
                    logger.info(f'Verification failed: {verification.assessment}')
            except Exception as e:
                logger.error(f'Verification attempt {attempt + 1} failed: {str(e)}')
                consecutive_passes = 0
        return {'solution_agent_id': solution.agent_id, 'verification_count': len(verification_results), 'consecutive_passes': consecutive_passes, 'passes_threshold': consecutive_passes >= self.verification_threshold, 'verification_results': [{'verifier_id': v.verifier_id, 'assessment': v.assessment, 'confidence': v.confidence, 'issues_count': len(v.issues)} for v in verification_results]}

    def _select_verifier_agent(self, solution_agent_id: int) -> MARSAgent:
        """Select an agent different from the solution creator for verification"""
        available_agents = [agent for agent in self.agents if agent.agent_id != solution_agent_id]
        if not available_agents:
            available_agents = self.agents
        if len(available_agents) > 1:
            solution_agent = next((a for a in self.agents if a.agent_id == solution_agent_id), None)
            if solution_agent:
                solution_temp = solution_agent.temperature
                available_agents.sort(key=lambda a: abs(a.temperature - solution_temp), reverse=True)
        return available_agents[0] if available_agents else None

    def iterative_improvement(self, request_id: str=None) -> Dict[str, Any]:
        """Run iterative improvement on solutions that failed verification"""
        logger.info('Starting iterative improvement process')
        improvement_summary = {'solutions_improved': 0, 'improvement_attempts': 0, 'total_reasoning_tokens': 0}
        unverified_solutions = [s for s in self.workspace.solutions if not s.is_verified]
        for solution in unverified_solutions:
            if solution.verification_results:
                latest_verification = solution.verification_results[-1]
                if latest_verification['assessment'] in ['INCORRECT', 'INCOMPLETE']:
                    original_agent = next((a for a in self.agents if a.agent_id == solution.agent_id), None)
                    if original_agent:
                        try:
                            improved_solution, reasoning_tokens = original_agent.improve_solution(problem=self.workspace.problem, current_solution=solution.solution, feedback=latest_verification['detailed_report'], issues=latest_verification['issues'], request_id=request_id)
                            solution.solution = improved_solution
                            solution.timestamp = datetime.now()
                            solution.reasoning_tokens += reasoning_tokens
                            improvement_summary['solutions_improved'] += 1
                            improvement_summary['total_reasoning_tokens'] += reasoning_tokens
                            logger.info(f'Improved solution from agent {solution.agent_id}')
                        except Exception as e:
                            logger.error(f'Failed to improve solution from agent {solution.agent_id}: {str(e)}')
                    improvement_summary['improvement_attempts'] += 1
        return improvement_summary

    async def iterative_improvement_parallel(self, request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, Any]:
        """Run iterative improvement on solutions that failed verification with parallel execution"""
        logger.info('Starting parallel iterative improvement process')
        improvement_summary = {'solutions_improved': 0, 'improvement_attempts': 0, 'total_reasoning_tokens': 0}
        unverified_solutions = [s for s in self.workspace.solutions if not s.is_verified]
        improvable_solutions = []
        for solution in unverified_solutions:
            if solution.verification_results:
                latest_verification = solution.verification_results[-1]
                if latest_verification['assessment'] in ['INCORRECT', 'INCOMPLETE']:
                    original_agent = next((a for a in self.agents if a.agent_id == solution.agent_id), None)
                    if original_agent:
                        improvable_solutions.append((solution, original_agent, latest_verification))
        if not improvable_solutions:
            logger.info('No solutions need improvement')
            return improvement_summary

        async def improve_solution_async(solution_data):
            """Async wrapper for solution improvement"""
            solution, agent, verification = solution_data
            loop = asyncio.get_event_loop()
            try:
                improved_solution, reasoning_tokens = await loop.run_in_executor(executor, agent.improve_solution, self.workspace.problem, solution.solution, verification['detailed_report'], verification['issues'], request_id)
                solution.solution = improved_solution
                solution.timestamp = datetime.now()
                solution.reasoning_tokens += reasoning_tokens
                logger.info(f'Improved solution from agent {solution.agent_id}')
                return (solution.agent_id, True, reasoning_tokens, None)
            except Exception as e:
                logger.error(f'Failed to improve solution from agent {solution.agent_id}: {str(e)}')
                return (solution.agent_id, False, 0, e)
        tasks = [improve_solution_async(sol_data) for sol_data in improvable_solutions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            improvement_summary['improvement_attempts'] += 1
            if isinstance(result, Exception):
                logger.error(f'Improvement task failed: {str(result)}')
                continue
            agent_id, success, tokens, error = result
            if success:
                improvement_summary['solutions_improved'] += 1
                improvement_summary['total_reasoning_tokens'] += tokens
        logger.info(f'Parallel improvement complete: {improvement_summary['solutions_improved']} solutions improved')
        return improvement_summary

    def final_consensus_check(self) -> bool:
        """Final check to determine if consensus has been reached"""
        verified_solutions = self.workspace.get_verified_solutions()
        consensus_threshold = self.config.get('consensus_threshold', 2)
        has_consensus = len(verified_solutions) >= consensus_threshold
        if has_consensus:
            logger.info(f'Consensus reached with {len(verified_solutions)} verified solutions')
            for solution in verified_solutions:
                logger.info(f'Verified solution from agent {solution.agent_id} (score: {solution.verification_score:.2f})')
        else:
            logger.info(f'No consensus: only {len(verified_solutions)} solutions verified (need {consensus_threshold})')
        return has_consensus

def __init__(self, agents: List[MARSAgent], workspace: MARSWorkspace, config: Dict[str, Any]):
    self.agents = agents
    self.workspace = workspace
    self.config = config
    self.verification_threshold = config.get('verification_passes_required', 5)

def verify_solutions(self, request_id: str=None) -> Dict[str, Any]:
    """Run comprehensive verification on all solutions in workspace"""
    logger.info(f'Starting verification process with {self.verification_threshold}-pass threshold')
    verification_summary = {'total_verifications': 0, 'solutions_verified': 0, 'consensus_reached': False, 'verification_details': []}
    solutions = self.workspace.solutions
    if not solutions:
        logger.warning('No solutions to verify')
        return verification_summary
    for solution in solutions:
        solution_verification = self._verify_single_solution(solution, request_id)
        verification_summary['verification_details'].append(solution_verification)
        verification_summary['total_verifications'] += solution_verification['verification_count']
        if solution_verification['passes_threshold']:
            verification_summary['solutions_verified'] += 1
    verified_solutions = self.workspace.get_verified_solutions()
    verification_summary['consensus_reached'] = len(verified_solutions) >= self.config.get('consensus_threshold', 2)
    logger.info(f'Verification complete: {verification_summary['solutions_verified']} solutions verified')
    return verification_summary

def final_consensus_check(self) -> bool:
    """Final check to determine if consensus has been reached"""
    verified_solutions = self.workspace.get_verified_solutions()
    consensus_threshold = self.config.get('consensus_threshold', 2)
    has_consensus = len(verified_solutions) >= consensus_threshold
    if has_consensus:
        logger.info(f'Consensus reached with {len(verified_solutions)} verified solutions')
        for solution in verified_solutions:
            logger.info(f'Verified solution from agent {solution.agent_id} (score: {solution.verification_score:.2f})')
    else:
        logger.info(f'No consensus: only {len(verified_solutions)} solutions verified (need {consensus_threshold})')
    return has_consensus

def run(system_prompt: str, initial_query: str, client, model: str, request_config: Optional[Dict]=None) -> Tuple[str, int]:
    """
    Deep Research plugin implementing TTD-DR (Test-Time Diffusion Deep Researcher)
    
    This plugin orchestrates web search, URL fetching, and memory synthesis to provide
    comprehensive research responses using an iterative refinement approach.
    
    Based on: "Deep Researcher with Test-Time Diffusion" 
    https://arxiv.org/abs/2507.16075v1
    
    Args:
        system_prompt: System prompt for the conversation
        initial_query: User's research query
        client: OpenAI client for LLM calls
        model: Model name to use for synthesis
        request_config: Optional configuration dict with keys:
            - max_iterations: Maximum research iterations (default: 5)
            - max_sources: Maximum web sources per search (default: 30)
    
    Returns:
        Tuple of (comprehensive_research_response, total_completion_tokens)
    """
    config = request_config or {}
    max_iterations = config.get('max_iterations', 5)
    max_sources = config.get('max_sources', 30)
    if not initial_query.strip():
        return ('Error: No research query provided', 0)
    if not client:
        return ('Error: No LLM client provided for research synthesis', 0)
    wrapped_client = DeepResearchClientWrapper(client, timeout=1800.0, max_retries=0)
    researcher = DeepResearcher(client=wrapped_client, model=model, max_iterations=max_iterations, max_sources=max_sources)
    try:
        result, total_tokens = researcher.research(system_prompt, initial_query)
        return (result, total_tokens)
    except Exception as e:
        error_message = f'Deep research failed: {str(e)}'
        return (error_message, 0)

@dataclass
class ServerConfig:
    """Configuration for a single MCP server"""
    transport: str = 'stdio'
    command: Optional[str] = None
    args: List[str] = None
    url: Optional[str] = None
    headers: Dict[str, str] = None
    env: Dict[str, str] = None
    description: Optional[str] = None
    timeout: float = 5.0
    sse_read_timeout: float = 300.0

    def __post_init__(self):
        """Initialize default values for mutable fields"""
        if self.args is None:
            self.args = []
        if self.headers is None:
            self.headers = {}
        if self.env is None:
            self.env = {}

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ServerConfig':
        """Create ServerConfig from a dictionary"""
        return cls(transport=config.get('transport', 'stdio'), command=config.get('command'), args=config.get('args', []), url=config.get('url'), headers=config.get('headers', {}), env=config.get('env', {}), description=config.get('description'), timeout=config.get('timeout', 5.0), sse_read_timeout=config.get('sse_read_timeout', 300.0))

@classmethod
def from_dict(cls, config: Dict[str, Any]) -> 'ServerConfig':
    """Create ServerConfig from a dictionary"""
    return cls(transport=config.get('transport', 'stdio'), command=config.get('command'), args=config.get('args', []), url=config.get('url'), headers=config.get('headers', {}), env=config.get('env', {}), description=config.get('description'), timeout=config.get('timeout', 5.0), sse_read_timeout=config.get('sse_read_timeout', 300.0))

def _get_system_message_support(proxy_client, model: str) -> bool:
    """
    Get cached system message support status, testing if not cached.
    Thread-safe with locking.
    """
    cache_key = f'{getattr(proxy_client, '_base_identifier', 'default')}:{model}'
    with _cache_lock:
        if cache_key not in _system_message_support_cache:
            logger.debug(f'Testing system message support for {model}')
            _system_message_support_cache[cache_key] = _test_system_message_support(proxy_client, model)
        return _system_message_support_cache[cache_key]

class JSONGenerator:

    def get_device(self):
        """Get the appropriate device (mps, cuda, or cpu)."""
        if torch.backends.mps.is_available():
            return torch.device('mps')
        elif torch.cuda.is_available():
            return torch.device('cuda')
        else:
            return torch.device('cpu')

    def __init__(self, model_name: str='google/gemma-3-270m-it'):
        """Initialize the JSON generator with a specific model."""
        self.device = self.get_device()
        logger.info(f'Using device: {self.device}')
        try:
            hf_model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto' if str(self.device) != 'cpu' else None, torch_dtype=torch.float16 if str(self.device) != 'cpu' else torch.float32)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = outlines.from_transformers(hf_model, self.tokenizer)
            logger.info(f'Successfully loaded model: {model_name}')
        except Exception as e:
            logger.error(f'Error loading model: {str(e)}')
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f'Error counting tokens: {str(e)}')
            return 0

    def parse_json_schema_to_pydantic(self, schema_str: str) -> type[BaseModel]:
        """Convert JSON schema string to Pydantic model."""
        try:
            schema_dict = json.loads(schema_str)
            properties = schema_dict.get('properties', {})
            required = schema_dict.get('required', [])
            fields = {}
            for field_name, field_def in properties.items():
                field_type = str
                if field_def.get('type') == 'integer':
                    field_type = int
                elif field_def.get('type') == 'number':
                    field_type = float
                elif field_def.get('type') == 'boolean':
                    field_type = bool
                elif field_def.get('type') == 'array':
                    field_type = list
                elif field_def.get('type') == 'object':
                    field_type = dict
                if field_name in required:
                    fields[field_name] = (field_type, ...)
                else:
                    fields[field_name] = (Optional[field_type], None)
            return create_model('DynamicModel', **fields)
        except Exception as e:
            logger.error(f'Error parsing JSON schema: {str(e)}')
            raise

    def generate_json(self, prompt: str, schema: str) -> Dict[str, Any]:
        """Generate JSON based on the provided schema and prompt."""
        try:
            pydantic_model = self.parse_json_schema_to_pydantic(schema)
            logger.info('Parsed JSON schema to Pydantic model')
            result = self.model(prompt, pydantic_model)
            logger.info('Successfully generated JSON response')
            if hasattr(result, 'model_dump'):
                return result.model_dump()
            elif hasattr(result, 'dict'):
                return result.dict()
            else:
                return dict(result)
        except Exception as e:
            logger.error(f'Error generating JSON: {str(e)}')
            raise

def parse_json_schema_to_pydantic(self, schema_str: str) -> type[BaseModel]:
    """Convert JSON schema string to Pydantic model."""
    try:
        schema_dict = json.loads(schema_str)
        properties = schema_dict.get('properties', {})
        required = schema_dict.get('required', [])
        fields = {}
        for field_name, field_def in properties.items():
            field_type = str
            if field_def.get('type') == 'integer':
                field_type = int
            elif field_def.get('type') == 'number':
                field_type = float
            elif field_def.get('type') == 'boolean':
                field_type = bool
            elif field_def.get('type') == 'array':
                field_type = list
            elif field_def.get('type') == 'object':
                field_type = dict
            if field_name in required:
                fields[field_name] = (field_type, ...)
            else:
                fields[field_name] = (Optional[field_type], None)
        return create_model('DynamicModel', **fields)
    except Exception as e:
        logger.error(f'Error parsing JSON schema: {str(e)}')
        raise

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

def replace_placeholder(match):
    placeholder = match.group(0)
    return reverse_map.get(placeholder, placeholder)

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

def start(self):
    """Start health checking in background"""
    if not self.enabled:
        return
    self.running = True
    self.thread = threading.Thread(target=self._check_loop, daemon=True)
    self.thread.start()
    logger.info(f'Health checker started (interval: {self.interval}s)')

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

class ProxyClient:
    """OpenAI-compatible client that proxies to multiple providers"""

    def __init__(self, config: Dict, fallback_client=None):
        self.config = config
        self.fallback_client = fallback_client
        self.providers = [Provider(p) for p in config.get('providers', [])]
        self.active_providers = [p for p in self.providers if not p.fallback_only]
        self.fallback_providers = [p for p in self.providers if p.fallback_only]
        strategy = config.get('routing', {}).get('strategy', 'round_robin')
        self.router = RouterFactory.create(strategy, self.active_providers)
        health_config = config.get('routing', {}).get('health_check', {})
        self.health_checker = HealthChecker(providers=self.providers, enabled=health_config.get('enabled', True), interval=health_config.get('interval', 30), timeout=health_config.get('timeout', 5))
        self.health_checker.start()
        timeout_config = config.get('timeouts', {})
        self.request_timeout = timeout_config.get('request', 30)
        self.connect_timeout = timeout_config.get('connect', 5)
        queue_config = config.get('queue', {})
        self.max_concurrent_requests = queue_config.get('max_concurrent', 100)
        self.queue_timeout = queue_config.get('timeout', 60)
        self._request_semaphore = threading.Semaphore(self.max_concurrent_requests)
        monitoring = config.get('monitoring', {})
        self.track_latency = monitoring.get('track_latency', True)
        self.track_errors = monitoring.get('track_errors', True)
        self.chat = self._Chat(self)

    class _Chat:

        def __init__(self, proxy_client):
            self.proxy_client = proxy_client
            self.completions = proxy_client._Completions(proxy_client)

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

def __init__(self, config: Dict, fallback_client=None):
    self.config = config
    self.fallback_client = fallback_client
    self.providers = [Provider(p) for p in config.get('providers', [])]
    self.active_providers = [p for p in self.providers if not p.fallback_only]
    self.fallback_providers = [p for p in self.providers if p.fallback_only]
    strategy = config.get('routing', {}).get('strategy', 'round_robin')
    self.router = RouterFactory.create(strategy, self.active_providers)
    health_config = config.get('routing', {}).get('health_check', {})
    self.health_checker = HealthChecker(providers=self.providers, enabled=health_config.get('enabled', True), interval=health_config.get('interval', 30), timeout=health_config.get('timeout', 5))
    self.health_checker.start()
    timeout_config = config.get('timeouts', {})
    self.request_timeout = timeout_config.get('request', 30)
    self.connect_timeout = timeout_config.get('connect', 5)
    queue_config = config.get('queue', {})
    self.max_concurrent_requests = queue_config.get('max_concurrent', 100)
    self.queue_timeout = queue_config.get('timeout', 60)
    self._request_semaphore = threading.Semaphore(self.max_concurrent_requests)
    monitoring = config.get('monitoring', {})
    self.track_latency = monitoring.get('track_latency', True)
    self.track_errors = monitoring.get('track_errors', True)
    self.chat = self._Chat(self)

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

class RouterFactory:
    """Factory for creating routers"""

    @staticmethod
    def create(strategy: str, providers: List) -> Router:
        strategies = {'round_robin': RoundRobinRouter, 'weighted': WeightedRouter, 'failover': FailoverRouter}
        router_class = strategies.get(strategy, RoundRobinRouter)
        return router_class(providers)

@staticmethod
def create(strategy: str, providers: List) -> Router:
    strategies = {'round_robin': RoundRobinRouter, 'weighted': WeightedRouter, 'failover': FailoverRouter}
    router_class = strategies.get(strategy, RoundRobinRouter)
    return router_class(providers)

class Strategy:
    """Represents a problem-solving strategy learned by the system."""

    def __init__(self, strategy_id: str, problem_type: str, strategy_text: str, examples: List[str]=None, success_count: int=0, total_attempts: int=0, created_at: str=None, last_used: str=None, last_updated: str=None, confidence: float=0.5, tags: List[str]=None, reasoning_examples: List[str]=None):
        self.strategy_id = strategy_id
        self.problem_type = problem_type if problem_type in VALID_PROBLEM_TYPES else 'general_problem'
        self.strategy_text = strategy_text
        self.examples = examples or []
        self.success_count = success_count
        self.total_attempts = total_attempts
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used
        self.last_updated = last_updated or self.created_at
        self.confidence = confidence
        self.tags = tags or []
        self.reasoning_examples = reasoning_examples or []

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of this strategy."""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convert the strategy to a dictionary for serialization."""
        return {'strategy_id': self.strategy_id, 'problem_type': self.problem_type, 'strategy_text': self.strategy_text, 'examples': self.examples, 'success_count': self.success_count, 'total_attempts': self.total_attempts, 'created_at': self.created_at, 'last_used': self.last_used, 'last_updated': self.last_updated, 'confidence': self.confidence, 'tags': self.tags, 'reasoning_examples': self.reasoning_examples}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """Create a Strategy instance from a dictionary."""
        return cls(strategy_id=data['strategy_id'], problem_type=data['problem_type'], strategy_text=data['strategy_text'], examples=data.get('examples', []), success_count=data.get('success_count', 0), total_attempts=data.get('total_attempts', 0), created_at=data.get('created_at'), last_used=data.get('last_used'), last_updated=data.get('last_updated'), confidence=data.get('confidence', 0.5), tags=data.get('tags', []), reasoning_examples=data.get('reasoning_examples', []))

    def record_attempt(self, success: bool) -> None:
        """Record an attempt to use this strategy."""
        self.total_attempts += 1
        if success:
            self.success_count += 1
        self.last_used = datetime.now().isoformat()
        alpha = 0.1
        self.confidence = (1 - alpha) * self.confidence + alpha * (1.0 if success else 0.0)

    def update_strategy(self, new_strategy_text: str) -> None:
        """Update the strategy text with a refined version."""
        self.strategy_text = new_strategy_text
        self.last_updated = datetime.now().isoformat()

    def add_reasoning_example(self, reasoning: str) -> None:
        """Add a reasoning example to the strategy."""
        if reasoning and reasoning.strip():
            if len(self.reasoning_examples) >= 5:
                self.reasoning_examples.pop(0)
            self.reasoning_examples.append(reasoning.strip())

    def add_example(self, example: str) -> None:
        """Add an example to the strategy."""
        if example and example not in self.examples:
            self.examples.append(example)

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
    """Create a Strategy instance from a dictionary."""
    return cls(strategy_id=data['strategy_id'], problem_type=data['problem_type'], strategy_text=data['strategy_text'], examples=data.get('examples', []), success_count=data.get('success_count', 0), total_attempts=data.get('total_attempts', 0), created_at=data.get('created_at'), last_used=data.get('last_used'), last_updated=data.get('last_updated'), confidence=data.get('confidence', 0.5), tags=data.get('tags', []), reasoning_examples=data.get('reasoning_examples', []))

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

def get_steering_strength(self, pattern: str) -> float:
    """
        Get the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            The steering strength
        """
    return self.pattern_strengths.get(pattern, self.default_strength)

def get_pattern_vectors(self, pattern: str) -> List[Dict[str, Any]]:
    """
        Get all steering vectors for a specific reasoning pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            List of steering vectors
        """
    return self.pattern_to_vectors.get(pattern, [])

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

def format_deepconf_response(answer: str, stats: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Format the DeepConf response with optional statistics.
    
    Args:
        answer: The final answer from weighted voting
        stats: Processing statistics
        config: Configuration used
        
    Returns:
        Formatted response string
    """
    response = answer.strip()
    if config.get('include_stats', False):
        stats_text = f'\n\nDeepConf Statistics:\n- Variant: {stats['variant']}\n- Total traces: {stats['total_traces']} (warmup: {stats['warmup_traces']}, online: {stats['online_traces']})\n- Early terminations: {stats['early_terminations']}\n- Total tokens: {stats['total_tokens_used']}\n- Confidence threshold: {stats['confidence_threshold']:.4f}\n- Unique answers: {stats['num_unique_answers']}'
        response += stats_text
    return response

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

def setUp(self):
    """Check server availability"""
    if not requests.get('http://localhost:8000/v1/health', timeout=2).status_code == 200:
        self.skipTest('OptILLM server not available')
    self.client = OpenAI(api_key='optillm', base_url='http://localhost:8000/v1')

class MockOpenAIClient:
    """Mock OpenAI client for testing"""

    def __init__(self, response_content='Test response', usage_tokens=10, n_responses=1):
        self.chat = Mock()
        self.chat.completions = Mock()
        self.responses = []
        for i in range(20):
            response = MockOpenAIResponse(response_content, usage_tokens, n_responses, i)
            self.responses.append(response)
        self.call_count = 0
        self.chat.completions.create = self._create_response

    def _create_response(self, **kwargs):
        """Return the next response in sequence"""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        n = kwargs.get('n', 1)
        if n > 1:
            return MockOpenAIResponse('Different response', 10, n, self.call_count)
        return response

def __init__(self, response_content='Test response', usage_tokens=10, n_responses=1):
    self.chat = Mock()
    self.chat.completions = Mock()
    self.responses = []
    for i in range(20):
        response = MockOpenAIResponse(response_content, usage_tokens, n_responses, i)
        self.responses.append(response)
    self.call_count = 0
    self.chat.completions.create = self._create_response

def _create_response(self, **kwargs):
    """Return the next response in sequence"""
    response = self.responses[self.call_count % len(self.responses)]
    self.call_count += 1
    n = kwargs.get('n', 1)
    if n > 1:
        return MockOpenAIResponse('Different response', 10, n, self.call_count)
    return response

class TestServerConfig:
    """Test ServerConfig dataclass functionality"""

    def test_default_stdio_config(self):
        """Test default configuration for stdio transport"""
        config = ServerConfig()
        assert config.transport == 'stdio'
        assert config.command is None
        assert config.args == []
        assert config.url is None
        assert config.headers == {}
        assert config.env == {}
        assert config.timeout == 5.0
        assert config.sse_read_timeout == 300.0

    def test_stdio_config_from_dict(self):
        """Test creating stdio config from dictionary"""
        config_dict = {'transport': 'stdio', 'command': 'npx', 'args': ['@modelcontextprotocol/server-filesystem', '/tmp'], 'env': {'PATH': '/usr/local/bin'}, 'description': 'Filesystem server'}
        config = ServerConfig.from_dict(config_dict)
        assert config.transport == 'stdio'
        assert config.command == 'npx'
        assert config.args == ['@modelcontextprotocol/server-filesystem', '/tmp']
        assert config.env == {'PATH': '/usr/local/bin'}
        assert config.description == 'Filesystem server'

    def test_sse_config_from_dict(self):
        """Test creating SSE config from dictionary"""
        config_dict = {'transport': 'sse', 'url': 'https://api.example.com/mcp', 'headers': {'Authorization': 'Bearer token123'}, 'timeout': 10.0, 'sse_read_timeout': 600.0, 'description': 'Remote SSE server'}
        config = ServerConfig.from_dict(config_dict)
        assert config.transport == 'sse'
        assert config.url == 'https://api.example.com/mcp'
        assert config.headers == {'Authorization': 'Bearer token123'}
        assert config.timeout == 10.0
        assert config.sse_read_timeout == 600.0
        assert config.description == 'Remote SSE server'

    def test_websocket_config_from_dict(self):
        """Test creating WebSocket config from dictionary"""
        config_dict = {'transport': 'websocket', 'url': 'wss://api.example.com/mcp', 'description': 'WebSocket server'}
        config = ServerConfig.from_dict(config_dict)
        assert config.transport == 'websocket'
        assert config.url == 'wss://api.example.com/mcp'
        assert config.description == 'WebSocket server'

def test_default_stdio_config(self):
    """Test default configuration for stdio transport"""
    config = ServerConfig()
    assert config.transport == 'stdio'
    assert config.command is None
    assert config.args == []
    assert config.url is None
    assert config.headers == {}
    assert config.env == {}
    assert config.timeout == 5.0
    assert config.sse_read_timeout == 300.0

@pytest.mark.asyncio
class TestMCPServer:
    """Test MCP server connection and capability discovery"""

    def test_init(self):
        """Test MCPServer initialization"""
        config = ServerConfig()
        server = MCPServer('test_server', config)
        assert server.server_name == 'test_server'
        assert server.config == config
        assert server.tools == []
        assert server.resources == []
        assert server.prompts == []
        assert not server.connected
        assert not server.has_tools_capability
        assert not server.has_resources_capability
        assert not server.has_prompts_capability

    async def test_connect_stdio_validation(self):
        """Test stdio connection validation"""
        config = ServerConfig(transport='stdio')
        server = MCPServer('test_server', config)
        result = await server.connect_stdio_native()
        assert not result

    async def test_connect_sse_validation(self):
        """Test SSE connection validation"""
        config = ServerConfig(transport='sse')
        server = MCPServer('test_server', config)
        result = await server.connect_sse()
        assert not result

    async def test_connect_websocket_validation(self):
        """Test WebSocket connection validation"""
        config = ServerConfig(transport='websocket')
        server = MCPServer('test_server', config)
        result = await server.connect_websocket()
        assert not result

    async def test_connect_and_discover_unsupported_transport(self):
        """Test unsupported transport type"""
        config = ServerConfig(transport='invalid')
        server = MCPServer('test_server', config)
        result = await server.connect_and_discover()
        assert not result

    @patch('optillm.plugins.mcp_plugin.sse_client')
    async def test_connect_sse_success(self, mock_sse_client):
        """Test successful SSE connection"""
        mock_streams = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.capabilities = Mock()
        mock_session.initialize.return_value = mock_result
        config = ServerConfig(transport='sse', url='https://api.example.com/mcp', headers={'Authorization': 'Bearer token'})
        server = MCPServer('test_server', config)
        with patch.object(server, 'connect_stdio', return_value=True):
            with patch('optillm.plugins.mcp_plugin.LoggingClientSession') as mock_session_class:
                mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)
                result = await server.connect_sse()
                assert result

def test_init(self):
    """Test MCPServer initialization"""
    config = ServerConfig()
    server = MCPServer('test_server', config)
    assert server.server_name == 'test_server'
    assert server.config == config
    assert server.tools == []
    assert server.resources == []
    assert server.prompts == []
    assert not server.connected
    assert not server.has_tools_capability
    assert not server.has_resources_capability
    assert not server.has_prompts_capability

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

def test_required_imports(self):
    """Test that required modules can be imported"""
    try:
        from mcp.client.sse import sse_client
        from mcp.client.websocket import websocket_client
        assert sse_client is not None
        assert websocket_client is not None
    except ImportError as e:
        pytest.fail(f'Required MCP imports failed: {e}')

class TestMockScenarios:
    """Test various scenarios with mocked dependencies"""

    @patch('optillm.plugins.mcp_plugin.find_executable')
    def test_stdio_command_not_found(self, mock_find_executable):
        """Test stdio transport when command is not found"""
        mock_find_executable.return_value = None
        config = ServerConfig(transport='stdio', command='nonexistent-command')

        async def test_async():
            result = await execute_tool_stdio(config, 'test_tool', {})
            assert 'error' in result
            assert 'Failed to find executable' in result['error']
        asyncio.run(test_async())

    def test_environment_variable_expansion(self):
        """Test environment variable expansion in SSE headers"""
        os.environ['TEST_TOKEN'] = 'test-token-value'
        try:
            config = ServerConfig(transport='sse', url='https://api.example.com/mcp', headers={'Authorization': 'Bearer ${TEST_TOKEN}'})
            server = MCPServer('test', config)
            expanded_headers = {}
            for key, value in config.headers.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    expanded_value = os.environ.get(env_var)
                    if expanded_value:
                        expanded_headers[key] = expanded_value
                else:
                    expanded_headers[key] = value
            assert expanded_headers['Authorization'] == 'Bearer test-token-value'
        finally:
            del os.environ['TEST_TOKEN']

@patch('optillm.plugins.mcp_plugin.find_executable')
def test_stdio_command_not_found(self, mock_find_executable):
    """Test stdio transport when command is not found"""
    mock_find_executable.return_value = None
    config = ServerConfig(transport='stdio', command='nonexistent-command')

    async def test_async():
        result = await execute_tool_stdio(config, 'test_tool', {})
        assert 'error' in result
        assert 'Failed to find executable' in result['error']
    asyncio.run(test_async())

def test_environment_variable_expansion(self):
    """Test environment variable expansion in SSE headers"""
    os.environ['TEST_TOKEN'] = 'test-token-value'
    try:
        config = ServerConfig(transport='sse', url='https://api.example.com/mcp', headers={'Authorization': 'Bearer ${TEST_TOKEN}'})
        server = MCPServer('test', config)
        expanded_headers = {}
        for key, value in config.headers.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                expanded_value = os.environ.get(env_var)
                if expanded_value:
                    expanded_headers[key] = expanded_value
            else:
                expanded_headers[key] = value
        assert expanded_headers['Authorization'] == 'Bearer test-token-value'
    finally:
        del os.environ['TEST_TOKEN']

def test_plugin_module_imports():
    """Test that plugin modules can be imported"""
    plugin_modules = ['optillm.plugins.memory_plugin', 'optillm.plugins.readurls_plugin', 'optillm.plugins.privacy_plugin', 'optillm.plugins.genselect_plugin', 'optillm.plugins.majority_voting_plugin', 'optillm.plugins.web_search_plugin', 'optillm.plugins.deep_research_plugin', 'optillm.plugins.deepthink_plugin', 'optillm.plugins.longcepo_plugin', 'optillm.plugins.spl_plugin', 'optillm.plugins.proxy_plugin', 'optillm.plugins.mcp_plugin']
    for module_name in plugin_modules:
        try:
            module = importlib.import_module(module_name)
            assert hasattr(module, 'run'), f"{module_name} missing 'run' function"
            assert hasattr(module, 'SLUG'), f"{module_name} missing 'SLUG' attribute"
        except ImportError as e:
            if pytest:
                pytest.fail(f'Failed to import {module_name}: {e}')
            else:
                raise AssertionError(f'Failed to import {module_name}: {e}')

def test_plugin_approach_detection():
    """Test plugin approach detection after loading"""
    load_plugins()
    expected_plugins = ['memory', 'readurls', 'privacy', 'web_search', 'deep_research', 'deepthink', 'longcepo', 'spl', 'proxy', 'mcp']
    for plugin_name in expected_plugins:
        assert plugin_name in plugin_approaches, f'Plugin {plugin_name} not loaded'

def test_no_relative_import_errors():
    """Test that plugins load without relative import errors"""
    import importlib
    import sys
    plugins_with_subdirs = ['optillm.plugins.deepthink_plugin', 'optillm.plugins.deep_research_plugin', 'optillm.plugins.longcepo_plugin', 'optillm.plugins.spl_plugin', 'optillm.plugins.proxy_plugin']
    for plugin_name in plugins_with_subdirs:
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith(plugin_name)]
        for mod in modules_to_clear:
            del sys.modules[mod]
        try:
            module = importlib.import_module(plugin_name)
            assert hasattr(module, 'run'), f'{plugin_name} missing run function'
        except ImportError as e:
            if 'attempted relative import' in str(e):
                if pytest:
                    pytest.fail(f'Relative import error in {plugin_name}: {e}')
                else:
                    raise AssertionError(f'Relative import error in {plugin_name}: {e}')
            else:
                raise

def get_test_client(base_url: str='http://localhost:8000/v1') -> OpenAI:
    """Get OpenAI client configured for local optillm"""
    return OpenAI(api_key='optillm', base_url=base_url)

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

def send_request(request_id):
    request_data = {'model': 'test-model', 'prompt': f'Request {request_id}'}
    return self.batcher.add_request(request_data)

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

def send_request(prompt_data):
    sys_prompt, user_prompt = prompt_data
    return batcher.add_request({'model': 'test-model', 'system_prompt': sys_prompt, 'user_prompt': user_prompt})

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

def test_batch_mode_errors(self):
    """Test error conditions in batch mode"""
    batcher = RequestBatcher(max_batch_size=2, max_wait_ms=50)
    with self.assertRaises(BatchingError):
        batcher.add_request({'model': 'test'})
    batcher.shutdown()

