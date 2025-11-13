# Cluster 4

def evaluate_solution(problem_data: Dict, solution: str, model: str='google/gemini-2.5-flash-lite') -> Dict[str, any]:
    """
    IMO25-style evaluation using rigorous two-stage verification system:
    1. Detailed verification with comprehensive IMO grader prompt
    2. Simple yes/no check on solution correctness

    This eliminates self-judgment bias and provides more accurate assessment
    """
    logger.info(f'Running IMO25-style evaluation for problem {problem_data['id']}')
    imo25_verification = imo25_verify_solution(problem_data['problem'], solution, model, problem_data['id'])
    answer_extraction = extract_final_answer(solution, problem_data['id'])
    quality_analysis = extract_solution_quality(solution)
    correctness_score = 1.0 if imo25_verification['is_correct'] else 0.0
    if imo25_verification['is_correct'] and quality_analysis['completeness_score'] > 0.7:
        confidence = 'high'
    elif imo25_verification['is_correct']:
        confidence = 'medium'
    else:
        confidence = 'low'
    return {'is_correct': imo25_verification['is_correct'], 'verdict': 'Correct' if imo25_verification['is_correct'] else 'Incorrect', 'correctness_score': correctness_score, 'is_likely_correct': imo25_verification['is_correct'], 'confidence': confidence, 'verification_details': {'stage1_analysis': imo25_verification['judge_response'], 'stage2_check': imo25_verification['correctness_check'], 'errors_found': imo25_verification['errors_found'], 'bug_report': imo25_verification['bug_report'] if imo25_verification['bug_report'] else None}, 'layer_scores': {'structural_quality': quality_analysis['completeness_score'], 'insights_verification': 1.0 if imo25_verification['is_correct'] else 0.0, 'llm_judge': correctness_score, 'answer_extraction': answer_extraction['confidence']}, 'weights_used': {'imo25_verification': 1.0}, 'score_variance': 0.0, 'quality_analysis': quality_analysis, 'insights_check': {'required_insights_found': 1 if imo25_verification['is_correct'] else 0, 'total_required_insights': 1, 'insight_score': 1.0 if imo25_verification['is_correct'] else 0.0}, 'llm_verification': imo25_verification, 'answer_extraction': answer_extraction, 'evaluation_method': 'imo25_two_stage_binary'}

def get_problem_by_id(problem_id: int) -> Optional[Dict[str, Any]]:
    """Get problem data by ID"""
    return next((p for p in IMO_2025_PROBLEMS if p['id'] == problem_id), None)

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

class LEAP:

    def __init__(self, system_prompt: str, client, model: str, request_id: str=None):
        self.system_prompt = system_prompt
        self.client = client
        self.model = model
        self.request_id = request_id
        self.low_level_principles = []
        self.high_level_principles = []
        self.leap_completion_tokens = 0

    def extract_output(self, text: str) -> str:
        match = re.search('<output>(.*?)(?:</output>|$)', text, re.DOTALL)
        return match.group(1).strip() if match else ''

    def extract_examples_from_query(self, initial_query: str) -> List[Tuple[str, str]]:
        logger.info('Extracting examples from initial query')
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Analyze the following query and determine if it contains few-shot examples.\n                If it does, extract the examples and their corresponding answers.\n                Format the examples as a JSON array of objects, where each object has "question" and "answer" fields.\n                If there are no examples, return an empty array.\n                Enclose your response within <output></output> tags.\n                Do not put any explanation or any other reponse other than the JSON array within the <output></output> tags.\n\n                Example output format:\n                <output>\n                [\n                    {{"question": "What is 2+2?", "answer": "4"}},\n                    {{"question": "What is the capital of France?", "answer": "Paris"}}\n                ]\n                </output>\n\n                Query: {initial_query}\n                '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        examples_str = self.extract_output(response.choices[0].message.content)
        logger.debug(f'Extracted examples: {examples_str}')
        examples = []
        if examples_str:
            try:
                examples_list = json.loads(examples_str)
                examples = [(example['question'], example['answer']) for example in examples_list]
            except json.JSONDecodeError:
                logger.warning('Failed to parse examples JSON, using empty list')
            except KeyError:
                logger.warning('Parsed JSON does not have the expected structure, using empty list')
        logger.debug(f'Extracted examples: {examples}')
        return examples

    def generate_mistakes(self, examples: List[Tuple[str, str]]) -> List[Tuple[str, str, str, str]]:
        logger.info('Generating mistakes for given examples')
        mistakes = []
        for question, correct_answer in examples:
            provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                    Instruction: Answer the following question step by step. To induce a mistake, \n                    deliberately introduce an error in your reasoning or calculation.\n                    Question: {question}\n                    Provide your step-by-step reasoning, then enclose your final answer within <output></output> tags.\n                    Think step by step, but make sure to include a mistake.\n                    '}], 'temperature': 0.7}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.leap_completion_tokens += response.usage.completion_tokens
            generated_reasoning = response.choices[0].message.content
            generated_answer = self.extract_output(generated_reasoning)
            if generated_answer != correct_answer:
                mistakes.append((question, generated_reasoning, generated_answer, correct_answer))
        return mistakes

    def generate_low_level_principles(self, mistakes: List[Tuple[str, str, str, str]]) -> List[str]:
        logger.info('Generating low-level principles from mistakes')
        for question, generated_reasoning, generated_answer, correct_answer in mistakes:
            provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                    Question: {question}\n                    Generated Reasoning: {generated_reasoning}\n                    Generated Answer: {generated_answer}\n                    Correct Answer: {correct_answer}\n                    Instruction: Conduct a thorough analysis of the generated answer in comparison to the\n                    correct answer. Also observe how the generated reasoning differs from the correct\n                    reasoning. Identify any discrepancies, misunderstandings, or errors. Provide clear\n                    insights, principles, or guidelines that can be derived from this analysis to improve\n                    future responses. We are not focused on this one data point, but rather on the general\n                    principle.\n                    Reasoning: <discuss why the generated answer is wrong>\n                    Insights: Enclose ONLY the principles or insights within <output></output> tags.\n                    '}]}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.leap_completion_tokens += response.usage.completion_tokens
            self.low_level_principles.append(self.extract_output(response.choices[0].message.content))
        return self.low_level_principles

    def generate_high_level_principles(self) -> List[str]:
        logger.info('Generating high-level principles from low-level principles')
        principles_text = '\n'.join(self.low_level_principles)
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Low-level principles: {principles_text}\n                Create a list of *unique* and insightful principles to improve future responses based\n                on the analysis above.\n                Focus on capturing the essence of the feedback while eliminating redundancies.\n                Ensure that each point is clear, concise, and directly derived from the introspection\n                results.\n                Create a numbered list of principles. Leave specific details in place.\n                Limit to at most 8 principles.\n                Enclose your list of principles within <output></output> tags.\n                '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        self.high_level_principles = self.extract_output(response.choices[0].message.content).split('\n')
        return self.high_level_principles

    def apply_principles(self, query: str) -> str:
        logger.info('Applying learned principles to query')
        principles_text = '\n'.join(self.high_level_principles)
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Please answer the following query. Keep in mind these principles:\n\n                {principles_text}\n\n                Query: {query}\n                '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content

    def solve(self, initial_query: str) -> str:
        logger.info('Starting LEAP process')
        examples = self.extract_examples_from_query(initial_query)
        if not examples:
            logger.warning('No examples found in the query. Proceeding with direct answer.')
            return self.apply_principles(initial_query)
        mistakes = self.generate_mistakes(examples)
        self.generate_low_level_principles(mistakes)
        self.generate_high_level_principles()
        return self.apply_principles(initial_query)

def solve(self, initial_query: str) -> str:
    logger.info('Starting LEAP process')
    examples = self.extract_examples_from_query(initial_query)
    if not examples:
        logger.warning('No examples found in the query. Proceeding with direct answer.')
        return self.apply_principles(initial_query)
    mistakes = self.generate_mistakes(examples)
    self.generate_low_level_principles(mistakes)
    self.generate_high_level_principles()
    return self.apply_principles(initial_query)

def thinkdeeper_decode(model: PreTrainedModel, tokenizer: PreTrainedTokenizer, messages: List[Dict[str, str]], request_config: Dict[str, Any]=None) -> str:
    """Main plugin execution function with ThinkDeeper's controlled thinking process"""
    logger.info('Starting ThinkDeeper processing')
    config = DEFAULT_CONFIG.copy()
    if request_config:
        for key in DEFAULT_CONFIG:
            if key in request_config:
                config[key] = request_config[key]
    logger.info(f'Using config: {config}')
    try:
        processor = ThinkDeeperProcessor(config, tokenizer, model)
        response, reasoning_tokens = processor.reasoning_effort(messages)
        return (response, reasoning_tokens)
    except Exception as e:
        logger.error(f'Error in ThinkDeeper processing: {str(e)}')
        raise

class MLXInferencePipeline:
    """MLX-based inference pipeline that mirrors PyTorch pipeline interface"""

    def __init__(self, model_config: MLXModelConfig, cache_manager):
        self.model_config = model_config
        self.cache_manager = cache_manager
        self.last_used = time.time()
        if not MLX_AVAILABLE:
            raise RuntimeError('MLX framework not available. Install with: pip install mlx-lm')
        if not is_apple_silicon():
            raise RuntimeError('MLX framework is only supported on Apple Silicon')
        try:
            logger.info(f'Loading MLX model: {model_config.model_id}')
            self.model, self.tokenizer = self._load_mlx_model(model_config.model_id)
            logger.info('MLX model loaded successfully')
        except Exception as e:
            logger.error(f'Failed to load MLX model: {str(e)}')
            raise

    def _load_mlx_model(self, model_id: str):
        """Load MLX model and tokenizer with caching"""

        def _load_model():
            start_time = time.time()
            logger.info(f'Loading MLX model: {model_id}')
            try:
                model, tokenizer = mlx_load(model_id)
                load_time = time.time() - start_time
                logger.info(f'MLX model loaded in {load_time:.2f}s')
                return (model, tokenizer)
            except Exception as e:
                logger.error(f'Error loading MLX model {model_id}: {str(e)}')
                raise
        return self.cache_manager.get_or_load_model(f'mlx_{model_id}', _load_model)

    def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int], List[Optional[Dict]]]:
        """Generate text using MLX"""
        start_time = time.time()
        if generation_params is None:
            generation_params = {}
        max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
        temperature = generation_params.get('temperature', self.model_config.temperature)
        top_p = generation_params.get('top_p', self.model_config.top_p)
        repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
        num_return_sequences = generation_params.get('num_return_sequences', 1)
        if generation_params.get('seed') is not None:
            mx.random.seed(generation_params['seed'])
        responses = []
        token_counts = []
        logprobs_results = []
        for _ in range(num_return_sequences):
            try:
                logger.debug(f'Generating with MLX: max_tokens={max_tokens}, temp={temperature}')
                response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                responses.append(response)
                if isinstance(response, str):
                    token_count = len(self.tokenizer.encode(response))
                else:
                    token_count = len(response) if hasattr(response, '__len__') else 0
                token_counts.append(token_count)
                logprobs_results.append(None)
            except Exception as e:
                logger.error(f'Error during MLX generation: {str(e)}')
                logger.error(f'MLX generation parameters: max_tokens={max_tokens}, temp={temperature}, top_p={top_p}')
                responses.append('')
                token_counts.append(0)
                logprobs_results.append(None)
        generation_time = time.time() - start_time
        logger.info(f'MLX generation completed in {generation_time:.2f}s')
        return (responses, token_counts, logprobs_results)

    def _robust_mlx_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float, repetition_penalty: float) -> str:
        """Robust MLX generation using sampler approach"""
        try:
            sampler = make_sampler(temp=temperature, top_p=top_p, min_p=0.0, min_tokens_to_keep=1)
            response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, sampler=sampler, verbose=False)
            return response
        except Exception as e:
            logger.error(f'MLX generation with sampler failed: {str(e)}')
            try:
                logger.debug('Attempting MLX generation without sampler')
                response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, verbose=False)
                return response
            except Exception as fallback_e:
                logger.error(f'MLX fallback generation also failed: {str(fallback_e)}')
                raise

    def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format the prompt according to model's chat template"""
        if hasattr(self.tokenizer, 'apply_chat_template'):
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            try:
                return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            except Exception as e:
                logger.warning(f'Failed to apply chat template: {e}, using fallback')
                return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'
        else:
            return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'

    def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
        """
        Process a batch of prompts with MLX-based batch inference
        
        This method provides true batch processing for MLX models, processing multiple
        prompts simultaneously for improved throughput.
        
        Args:
            system_prompts: List of system prompts
            user_prompts: List of user prompts
            generation_params: Generation parameters (temperature, max_tokens, etc.)
            active_adapter: Active adapter (not used in MLX)
            return_token_count: Whether to return token counts
            
        Returns:
            Tuple of (responses, token_counts)
        """
        import time
        if generation_params is None:
            generation_params = {}
        if len(system_prompts) != len(user_prompts):
            raise ValueError(f'Number of system prompts ({len(system_prompts)}) must match user prompts ({len(user_prompts)})')
        if not system_prompts:
            return ([], [])
        batch_size = len(system_prompts)
        logger.info(f'MLX batch processing {batch_size} prompts')
        start_time = time.time()
        formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
        max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
        temperature = generation_params.get('temperature', self.model_config.temperature)
        top_p = generation_params.get('top_p', self.model_config.top_p)
        repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
        n = generation_params.get('num_return_sequences', 1)
        if generation_params.get('seed') is not None:
            mx.random.seed(generation_params['seed'])
        all_responses = []
        token_counts = []
        try:
            for i, prompt in enumerate(formatted_prompts):
                logger.debug(f'Processing MLX batch item {i + 1}/{batch_size}')
                for _ in range(n):
                    try:
                        response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                        all_responses.append(response)
                        if isinstance(response, str):
                            token_count = len(self.tokenizer.encode(response))
                        else:
                            token_count = len(response) if hasattr(response, '__len__') else 0
                        token_counts.append(token_count)
                    except Exception as e:
                        logger.error(f'Error generating response for batch item {i + 1}: {e}')
                        all_responses.append('')
                        token_counts.append(0)
            processing_time = time.time() - start_time
            logger.info(f'MLX batch processing completed in {processing_time:.2f}s')
            if return_token_count:
                return (all_responses, token_counts)
            return (all_responses, [0] * len(all_responses))
        except Exception as e:
            logger.error(f'MLX batch processing failed: {e}')
            raise

    def _batch_tokenize(self, prompts: List[str]) -> Dict[str, Any]:
        """
        Tokenize a batch of prompts with padding
        
        Args:
            prompts: List of text prompts
            
        Returns:
            Dictionary with tokenized inputs suitable for MLX
        """
        pass

    def _batch_generate(self, input_ids, attention_mask, generation_params: Dict) -> List[str]:
        """
        Perform batch generation using MLX model
        
        Args:
            input_ids: Batched input token IDs
            attention_mask: Attention mask for padded sequences
            generation_params: Generation parameters
            
        Returns:
            List of generated responses
        """
        pass

def __init__(self, model_config: MLXModelConfig, cache_manager):
    self.model_config = model_config
    self.cache_manager = cache_manager
    self.last_used = time.time()
    if not MLX_AVAILABLE:
        raise RuntimeError('MLX framework not available. Install with: pip install mlx-lm')
    if not is_apple_silicon():
        raise RuntimeError('MLX framework is only supported on Apple Silicon')
    try:
        logger.info(f'Loading MLX model: {model_config.model_id}')
        self.model, self.tokenizer = self._load_mlx_model(model_config.model_id)
        logger.info('MLX model loaded successfully')
    except Exception as e:
        logger.error(f'Failed to load MLX model: {str(e)}')
        raise

class MLXManager:
    """Manager for MLX models and operations"""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.available = MLX_AVAILABLE and is_apple_silicon()
        if self.available:
            logger.info('MLX manager initialized - Apple Silicon detected')
        else:
            logger.debug('MLX manager not available - requires Apple Silicon and mlx-lm')

    def create_pipeline(self, model_id: str, **kwargs) -> MLXInferencePipeline:
        """Create an MLX inference pipeline"""
        if not self.available:
            raise RuntimeError('MLX not available on this platform')
        config = MLXModelConfig(model_id=model_id, **kwargs)
        return MLXInferencePipeline(config, self.cache_manager)

    def is_mlx_model(self, model_id: str) -> bool:
        """Check if model should use MLX"""
        return should_use_mlx(model_id)

def __init__(self, cache_manager):
    self.cache_manager = cache_manager
    self.available = MLX_AVAILABLE and is_apple_silicon()
    if self.available:
        logger.info('MLX manager initialized - Apple Silicon detected')
    else:
        logger.debug('MLX manager not available - requires Apple Silicon and mlx-lm')

def create_pipeline(self, model_id: str, **kwargs) -> MLXInferencePipeline:
    """Create an MLX inference pipeline"""
    if not self.available:
        raise RuntimeError('MLX not available on this platform')
    config = MLXModelConfig(model_id=model_id, **kwargs)
    return MLXInferencePipeline(config, self.cache_manager)

def is_mlx_model(self, model_id: str) -> bool:
    """Check if model should use MLX"""
    return should_use_mlx(model_id)

class LoRAManager:
    """LoRA manager with enhanced error handling and caching"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.loaded_adapters = {}
        self.adapter_names = {}

    def _get_adapter_name(self, adapter_id: str) -> str:
        """Create a valid adapter name from adapter_id."""
        if adapter_id in self.adapter_names:
            return self.adapter_names[adapter_id]
        name = adapter_id.replace('.', '_').replace('-', '_')
        name = ''.join((c if c.isalnum() or c == '_' else '' for c in name))
        if name[0].isdigit():
            name = f'adapter_{name}'
        self.adapter_names[adapter_id] = name
        return name

    def validate_adapter(self, adapter_id: str) -> bool:
        """Validate if adapter exists and is compatible"""
        try:
            config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
            return True
        except Exception as e:
            logger.error(f'Error validating adapter {adapter_id}: {str(e)}')
            return False

    def load_adapter(self, base_model: PreTrainedModel, adapter_id: str) -> PreTrainedModel:
        """Load a LoRA adapter with enhanced caching"""
        model_key = base_model.config._name_or_path

        def _load_adapter():
            logger.info(f'Loading LoRA adapter: {adapter_id}')
            if not self.validate_adapter(adapter_id):
                error_msg = f'Adapter {adapter_id} not found or is not compatible'
                logger.error(error_msg)
                raise ValueError(error_msg)
            try:
                adapter_name = self._get_adapter_name(adapter_id)
                config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
                model = base_model
                model.add_adapter(config, adapter_name=adapter_name)
                if model not in self.loaded_adapters:
                    self.loaded_adapters[model] = []
                if adapter_id not in self.loaded_adapters[model]:
                    self.loaded_adapters[model].append(adapter_id)
                return model
            except Exception as e:
                error_msg = f'Failed to load adapter {adapter_id}: {str(e)}'
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self.cache_manager.get_or_load_adapter(model_key, adapter_id, _load_adapter)

    def set_active_adapter(self, model: PeftModel, adapter_id: str=None) -> bool:
        """Set a specific adapter as active with error handling"""
        if not isinstance(model, PeftModel):
            logger.warning('Model is not a PeftModel, cannot set active adapter')
            return False
        available_adapters = self.loaded_adapters.get(model, [])
        if not available_adapters:
            logger.warning('No adapters loaded in model')
            return False
        if adapter_id is None:
            adapter_id = available_adapters[-1]
        if adapter_id in available_adapters:
            try:
                model.set_adapter(self._get_adapter_name(adapter_id))
                logger.info(f'Successfully set active adapter to: {adapter_id}')
                return True
            except Exception as e:
                logger.error(f'Error setting adapter {adapter_id}: {str(e)}')
                return False
        else:
            logger.warning(f'Requested adapter {adapter_id} not loaded. Available adapters: {available_adapters}')
            return False

def _load_adapter():
    logger.info(f'Loading LoRA adapter: {adapter_id}')
    if not self.validate_adapter(adapter_id):
        error_msg = f'Adapter {adapter_id} not found or is not compatible'
        logger.error(error_msg)
        raise ValueError(error_msg)
    try:
        adapter_name = self._get_adapter_name(adapter_id)
        config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
        model = base_model
        model.add_adapter(config, adapter_name=adapter_name)
        if model not in self.loaded_adapters:
            self.loaded_adapters[model] = []
        if adapter_id not in self.loaded_adapters[model]:
            self.loaded_adapters[model].append(adapter_id)
        return model
    except Exception as e:
        error_msg = f'Failed to load adapter {adapter_id}: {str(e)}'
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def set_active_adapter(self, model: PeftModel, adapter_id: str=None) -> bool:
    """Set a specific adapter as active with error handling"""
    if not isinstance(model, PeftModel):
        logger.warning('Model is not a PeftModel, cannot set active adapter')
        return False
    available_adapters = self.loaded_adapters.get(model, [])
    if not available_adapters:
        logger.warning('No adapters loaded in model')
        return False
    if adapter_id is None:
        adapter_id = available_adapters[-1]
    if adapter_id in available_adapters:
        try:
            model.set_adapter(self._get_adapter_name(adapter_id))
            logger.info(f'Successfully set active adapter to: {adapter_id}')
            return True
        except Exception as e:
            logger.error(f'Error setting adapter {adapter_id}: {str(e)}')
            return False
    else:
        logger.warning(f'Requested adapter {adapter_id} not loaded. Available adapters: {available_adapters}')
        return False

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

class InferenceClient:
    """OpenAI SDK Compatible client for local inference with dynamic model support"""

    def __init__(self):
        self.cache_manager = CacheManager.get_instance(max_size=4)
        self.device_manager = DeviceManager()
        self.model_manager = ModelManager(self.cache_manager, self.device_manager)
        self.lora_manager = LoRAManager(self.cache_manager)
        self.mlx_manager = MLXManager(self.cache_manager)
        self.chat = self.Chat(self)
        self.models = self.Models()

    def get_pipeline(self, model: str):
        """Get inference pipeline - automatically chooses MLX or PyTorch based on model"""
        if self.mlx_manager.available and should_use_mlx(model):
            logger.info(f'Using MLX pipeline for model: {model}')
            return self.mlx_manager.create_pipeline(model)
        else:
            logger.info(f'Using PyTorch pipeline for model: {model}')
            model_config = parse_model_string(model)
            return InferencePipeline(model_config, self.cache_manager, self.device_manager, self.model_manager, self.lora_manager)

    class Chat:
        """OpenAI-compatible chat interface"""

        def __init__(self, client: 'InferenceClient'):
            self.client = client
            self.completions = self.Completions(client)

        class Completions:

            def __init__(self, client: 'InferenceClient'):
                self.client = client

            def create(self, messages: List[Dict[str, str]], model: str, temperature: float=1.0, top_p: float=1.0, n: int=1, stream: bool=False, stop: Optional[Union[str, List[str]]]=None, max_tokens: Optional[int]=None, presence_penalty: float=0, frequency_penalty: float=0, logit_bias: Optional[Dict[str, float]]=None, seed: Optional[int]=None, logprobs: Optional[bool]=None, top_logprobs: Optional[int]=None, active_adapter: Optional[Dict[str, Any]]=None, decoding: Optional[str]=None, k: int=10, num_beams: int=1, length_penalty: float=1.0, no_repeat_ngram_size: int=0, early_stopping: bool=False, aggregate_paths: bool=True, top_k: int=27, min_p: float=0.03, reasoning_effort: str='low', thought_switch_tokens: List[str]=[], min_thinking_tokens: Optional[int]=None, max_thinking_tokens: Optional[int]=None, max_thoughts: Optional[int]=None, prefill: str='', start_think_token: str='<think>', end_think_token: str='</think>', **kwargs) -> ChatCompletion:
                """Create a chat completion with OpenAI-compatible parameters"""
                logger.info('Starting chat completion creation')
                if stream:
                    raise NotImplementedError('Streaming is not yet supported')
                logger.info(f'Getting pipeline for model: {model}')
                pipeline = self.client.get_pipeline(model)
                logger.info('Pipeline acquired')
                if active_adapter is not None:
                    logger.info(f'Setting active adapter to: {active_adapter}')
                    pipeline.lora_manager.set_active_adapter(pipeline.current_model, active_adapter)
                responses = []
                logprobs_results = []
                prompt_tokens = 0
                completion_tokens = 0
                try:
                    if decoding:
                        logger.info(f'Using specialized decoding approach: {decoding}')
                        mlx_unsupported_decodings = ['cot_decoding', 'entropy_decoding', 'autothink', 'deepconf']
                        if isinstance(pipeline, MLXInferencePipeline) and decoding in mlx_unsupported_decodings:
                            logger.warning(f'{decoding} is not supported for MLX models. Falling back to standard generation.')
                            decoding = None
                    if decoding:
                        if not isinstance(pipeline, MLXInferencePipeline):
                            pipeline.current_model.eval()
                            device = pipeline.current_model.device
                        else:
                            device = None
                        if decoding == 'cot_decoding':
                            cot_params = {'k': k, 'num_beams': num_beams, 'max_new_tokens': max_tokens if max_tokens is not None else 512, 'temperature': temperature, 'top_p': top_p, 'repetition_penalty': 1.0, 'length_penalty': length_penalty, 'no_repeat_ngram_size': no_repeat_ngram_size, 'early_stopping': early_stopping, 'aggregate_paths': aggregate_paths}
                            result, confidence = cot_decode(pipeline.current_model, pipeline.tokenizer, messages, **cot_params)
                            responses = [result]
                            logprobs_results = [{'confidence_score': confidence} if confidence is not None else None]
                            completion_tokens = len(pipeline.tokenizer.encode(result))
                        elif decoding == 'entropy_decoding':
                            original_dtype = pipeline.current_model.dtype
                            pipeline.current_model = pipeline.current_model.to(torch.float32)
                            try:
                                generator = None
                                if seed is not None:
                                    generator = torch.Generator(device=device)
                                    generator.manual_seed(seed)
                                else:
                                    generator = torch.Generator(device=device)
                                    generator.manual_seed(1337)
                                entropy_params = {'max_new_tokens': max_tokens if max_tokens is not None else 4096, 'temperature': temperature, 'top_p': top_p, 'top_k': top_k, 'min_p': min_p, 'generator': generator}
                                with torch.amp.autocast('cuda', enabled=False), torch.inference_mode():
                                    result = entropy_decode(pipeline.current_model, pipeline.tokenizer, messages, **entropy_params)
                                responses = [result]
                                logprobs_results = [None]
                                completion_tokens = len(pipeline.tokenizer.encode(result))
                            finally:
                                pipeline.current_model = pipeline.current_model.to(original_dtype)
                        elif decoding == 'thinkdeeper':
                            thinkdeeper_config = get_effort_profile(reasoning_effort, max_tokens)
                            custom_config = {'min_thinking_tokens': min_thinking_tokens if min_thinking_tokens is not None else thinkdeeper_config['min_thinking_tokens'], 'max_thinking_tokens': max_thinking_tokens if max_thinking_tokens is not None else thinkdeeper_config['max_thinking_tokens'], 'max_thoughts': max_thoughts if max_thoughts is not None else thinkdeeper_config['max_thoughts'], 'thought_switch_tokens': thought_switch_tokens if thought_switch_tokens else thinkdeeper_config['thought_switch_tokens'], 'prefill': prefill if prefill else thinkdeeper_config['prefill'], 'start_think_token': start_think_token, 'end_think_token': end_think_token}
                            thinkdeeper_config.update(custom_config)
                            if isinstance(pipeline, MLXInferencePipeline):
                                logger.info('Using MLX ThinkDeeper implementation')
                                user_max_tokens = max_tokens if max_tokens is not None else 512
                                total_tokens_needed = max_thinking_tokens + 512
                                adjusted_max_tokens = max(user_max_tokens, total_tokens_needed)
                                thinkdeeper_config_with_tokens = thinkdeeper_config.copy()
                                thinkdeeper_config_with_tokens['max_tokens'] = adjusted_max_tokens
                                logger.debug(f'ThinkDeeper tokens: user={user_max_tokens}, thinking={max_thinking_tokens}, adjusted={adjusted_max_tokens}')
                                result, reasoning_tokens = thinkdeeper_decode_mlx(pipeline.model, pipeline.tokenizer, messages, thinkdeeper_config_with_tokens)
                            else:
                                logger.info('Using PyTorch ThinkDeeper implementation')
                                result, reasoning_tokens = thinkdeeper_decode(pipeline.current_model, pipeline.tokenizer, messages, thinkdeeper_config)
                            responses = [result]
                            logprobs_results = [None]
                            completion_tokens = len(pipeline.tokenizer.encode(result))
                        elif decoding == 'autothink':
                            steering_dataset = kwargs.get('steering_dataset', 'codelion/Qwen3-0.6B-pts-steering-vectors')
                            target_layer = kwargs.get('target_layer', 19)
                            autothink_config = {'steering_dataset': steering_dataset, 'target_layer': target_layer, 'pattern_strengths': kwargs.get('pattern_strengths', {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5})}
                            result = autothink_decode(pipeline.current_model, pipeline.tokenizer, messages, autothink_config)
                            responses = [result]
                            logprobs_results = [None]
                            completion_tokens = len(pipeline.tokenizer.encode(result))
                        elif decoding == 'deepconf':
                            deepconf_config = {'variant': kwargs.get('variant', 'low'), 'warmup_samples': kwargs.get('warmup_samples', 16), 'consensus_threshold': kwargs.get('consensus_threshold', 0.95), 'max_traces': kwargs.get('max_traces', 128), 'window_size': kwargs.get('window_size', 2048), 'top_k': kwargs.get('top_k', 5), 'min_trace_length': kwargs.get('min_trace_length', 100), 'max_tokens_per_trace': kwargs.get('max_tokens_per_trace', 4096), 'temperature': temperature, 'confidence_metric': kwargs.get('confidence_metric', 'average_confidence'), 'include_stats': kwargs.get('include_stats', False)}
                            result, tokens_used = deepconf_decode(pipeline.current_model, pipeline.tokenizer, messages, deepconf_config)
                            responses = [result]
                            logprobs_results = [None]
                            completion_tokens = tokens_used
                        else:
                            raise ValueError(f'Unknown specialized decoding approach: {decoding}')
                        prompt_text = pipeline.tokenizer.apply_chat_template(messages, tokenize=False)
                        prompt_tokens = len(pipeline.tokenizer.encode(prompt_text))
                    else:
                        prompt = pipeline.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                        generation_params = {'temperature': temperature, 'top_p': top_p, 'num_return_sequences': n, 'max_new_tokens': max_tokens if max_tokens is not None else 4096, 'presence_penalty': presence_penalty, 'frequency_penalty': frequency_penalty, 'stop_sequences': [stop] if isinstance(stop, str) else stop, 'seed': seed, 'logit_bias': logit_bias, 'logprobs': logprobs, 'top_logprobs': top_logprobs}
                        responses, token_counts, logprobs_results = pipeline.generate(prompt, generation_params=generation_params)
                        prompt_tokens = len(pipeline.tokenizer.encode(prompt))
                        completion_tokens = sum(token_counts)
                    total_reasoning_tokens = 0
                    for response in responses:
                        total_reasoning_tokens += count_reasoning_tokens(response, pipeline.tokenizer)
                    response_dict = {'id': f'chatcmpl-{int(time.time() * 1000)}', 'object': 'chat.completion', 'created': int(time.time()), 'model': model, 'choices': [{'index': idx, 'message': {'role': 'assistant', 'content': response, **({'logprobs': logprob_result} if logprob_result else {})}, 'finish_reason': 'stop'} for idx, (response, logprob_result) in enumerate(zip(responses, logprobs_results))], 'usage': {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': completion_tokens + prompt_tokens, 'reasoning_tokens': total_reasoning_tokens}}
                    logger.debug(f'Response : {response_dict}')
                    return ChatCompletion(response_dict)
                except Exception as e:
                    logger.error(f'Error in chat completion: {str(e)}')
                    raise

    class Models:
        """OpenAI-compatible models interface"""

        def list(self):
            """Return list of supported models"""
            try:
                import requests
                response = requests.get('https://huggingface.co/api/models?sort=downloads&direction=-1&filter=text-generation&limit=20')
                models = response.json()
                model_list = []
                for model in models:
                    if 'pipeline_tag' in model and model['pipeline_tag'] == 'text-generation':
                        model_list.append({'id': model['id'], 'object': 'model', 'created': int(time.time()), 'owned_by': 'huggingface'})
                return {'data': model_list, 'object': 'list'}
            except Exception as e:
                logger.warning(f'Failed to fetch models: {e}')
                return {'data': [{'id': 'HuggingFaceTB/SmolLM-135M-Instruct', 'object': 'model', 'created': int(time.time()), 'owned_by': 'huggingface'}], 'object': 'list'}

def get_pipeline(self, model: str):
    """Get inference pipeline - automatically chooses MLX or PyTorch based on model"""
    if self.mlx_manager.available and should_use_mlx(model):
        logger.info(f'Using MLX pipeline for model: {model}')
        return self.mlx_manager.create_pipeline(model)
    else:
        logger.info(f'Using PyTorch pipeline for model: {model}')
        model_config = parse_model_string(model)
        return InferencePipeline(model_config, self.cache_manager, self.device_manager, self.model_manager, self.lora_manager)

def thinkdeeper_decode_mlx(model, tokenizer, messages: List[Dict[str, str]], request_config: Dict[str, Any]=None) -> str:
    """MLX-compatible ThinkDeeper processing function"""
    logger.info('Starting MLX ThinkDeeper processing')
    if not MLX_AVAILABLE:
        raise RuntimeError('MLX framework not available for ThinkDeeper processing')
    config = DEFAULT_CONFIG.copy()
    if request_config:
        for key in DEFAULT_CONFIG:
            if key in request_config:
                config[key] = request_config[key]
        if 'max_tokens' in request_config:
            config['max_tokens'] = request_config['max_tokens']
    logger.info(f'MLX ThinkDeeper using config: {config}')
    try:
        processor = MLXThinkDeeperProcessor(config, tokenizer, model)
        response, reasoning_tokens = processor.reasoning_effort(messages)
        return (response, reasoning_tokens)
    except Exception as e:
        logger.error(f'Error in MLX ThinkDeeper processing: {str(e)}')
        raise

class ConversationLogger:
    """
    Logger for OptiLLM conversations including all provider interactions and metadata.
    
    Logs are saved in JSONL format (one JSON object per line) with daily rotation.
    Each entry contains the full conversation including all intermediate provider calls.
    """

    def __init__(self, log_dir: Path, enabled: bool=False):
        self.enabled = enabled
        self.log_dir = log_dir
        self.active_entries: Dict[str, ConversationEntry] = {}
        self._lock = threading.Lock()
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f'Conversation logging enabled. Logs will be saved to: {self.log_dir}')
        else:
            logger.debug('Conversation logging disabled')

    def _get_log_file_path(self, timestamp: datetime=None) -> Path:
        """Get the log file path for a given timestamp (defaults to now)"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        date_str = timestamp.strftime('%Y-%m-%d')
        return self.log_dir / f'conversations_{date_str}.jsonl'

    def _generate_request_id(self) -> str:
        """Generate a unique request ID"""
        return f'req_{uuid.uuid4().hex[:8]}'

    def start_conversation(self, client_request: Dict[str, Any], approach: str, model: str) -> str:
        """
        Start logging a new conversation.
        
        Args:
            client_request: The original request from the client
            approach: The optimization approach being used
            model: The model name
            
        Returns:
            str: Unique request ID for this conversation
        """
        if not self.enabled:
            return ''
        request_id = self._generate_request_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = ConversationEntry(request_id=request_id, timestamp=timestamp, approach=approach, model=model, client_request=client_request.copy())
        with self._lock:
            self.active_entries[request_id] = entry
        logger.debug(f'Started conversation logging for request {request_id}')
        return request_id

    def log_provider_call(self, request_id: str, provider_request: Dict[str, Any], provider_response: Dict[str, Any]) -> None:
        """
        Log a provider API call and response.
        
        Args:
            request_id: The request ID for this conversation
            provider_request: The request sent to the provider
            provider_response: The response received from the provider
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.get(request_id)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            call_data = {'call_number': len(entry.provider_calls) + 1, 'timestamp': datetime.now(timezone.utc).isoformat(), 'request': provider_request.copy(), 'response': provider_response.copy()}
            entry.provider_calls.append(call_data)
        logger.debug(f'Logged provider call #{len(entry.provider_calls)} for request {request_id}')

    def log_final_response(self, request_id: str, final_response: Dict[str, Any]) -> None:
        """
        Log the final response sent back to the client.
        
        Args:
            request_id: The request ID for this conversation
            final_response: The final response sent to the client
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.get(request_id)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            entry.final_response = final_response.copy()
            entry.final_response['timestamp'] = datetime.now(timezone.utc).isoformat()

    def log_error(self, request_id: str, error: str) -> None:
        """
        Log an error for this conversation.
        
        Args:
            request_id: The request ID for this conversation  
            error: Error message or description
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.get(request_id)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            entry.error = error
        logger.debug(f'Logged error for request {request_id}: {error}')

    def finalize_conversation(self, request_id: str) -> None:
        """
        Finalize and save the conversation to disk.
        
        Args:
            request_id: The request ID for this conversation
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.pop(request_id, None)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            entry.total_duration_ms = int((time.time() - entry.start_time) * 1000)
            log_entry = {'timestamp': entry.timestamp, 'request_id': entry.request_id, 'approach': entry.approach, 'model': entry.model, 'client_request': entry.client_request, 'provider_calls': entry.provider_calls, 'final_response': entry.final_response, 'total_duration_ms': entry.total_duration_ms, 'error': entry.error}
            self._write_log_entry(log_entry)
        logger.debug(f'Finalized conversation for request {request_id}')

    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Write a log entry to the appropriate JSONL file"""
        try:
            log_file_path = self._get_log_file_path()
            with open(log_file_path, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, separators=(',', ':'))
                f.write('\n')
            logger.debug(f'Wrote log entry to {log_file_path}')
        except Exception as e:
            logger.error(f'Failed to write log entry: {e}')

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation logging"""
        with self._lock:
            active_count = len(self.active_entries)
        stats = {'enabled': self.enabled, 'log_dir': str(self.log_dir), 'active_conversations': active_count}
        if self.enabled:
            log_files = list(self.log_dir.glob('conversations_*.jsonl'))
            total_entries = 0
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        total_entries += sum((1 for line in f if line.strip()))
                except Exception:
                    pass
            stats.update({'log_files_count': len(log_files), 'total_entries_approximate': total_entries})
        return stats

def __init__(self, log_dir: Path, enabled: bool=False):
    self.enabled = enabled
    self.log_dir = log_dir
    self.active_entries: Dict[str, ConversationEntry] = {}
    self._lock = threading.Lock()
    if self.enabled:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'Conversation logging enabled. Logs will be saved to: {self.log_dir}')
    else:
        logger.debug('Conversation logging disabled')

def chat_with_mcts(system_prompt: str, initial_query: str, client, model: str, num_simulations: int=2, exploration_weight: float=0.2, simulation_depth: int=1, request_id: str=None) -> str:
    logger.info('Starting chat with MCTS')
    logger.info(f'Parameters: num_simulations={num_simulations}, exploration_weight={exploration_weight}, simulation_depth={simulation_depth}')
    mcts = MCTS(simulation_depth=simulation_depth, exploration_weight=exploration_weight, client=client, model=model, request_id=request_id)
    initial_state = DialogueState(system_prompt, [], initial_query)
    logger.info(f'Initial query: {initial_query}')
    final_state = mcts.search(initial_state, num_simulations)
    response = final_state.conversation_history[-1]['content'] if final_state.conversation_history else ''
    logger.info(f'MCTS chat complete. Final response: {response[:100]}...')
    return (response, mcts.completion_tokens)

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

def set_final_solution(self, solution: str):
    """Set the final synthesized solution"""
    self.final_solution = solution
    logger.info('Final solution set in workspace')

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

def find_executable(cmd: str) -> Optional[str]:
    """
    Find the full path to an executable command.
    
    Args:
        cmd: The command to find
        
    Returns:
        Full path to the executable if found, None otherwise
    """
    if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
        return cmd
    cmd_path = shutil.which(cmd)
    if cmd_path:
        logger.info(f'Found {cmd} in PATH at {cmd_path}')
        return cmd_path
    common_paths = ['/usr/local/bin', '/usr/bin', '/bin', '/opt/homebrew/bin', os.path.expanduser('~/.npm-global/bin'), os.path.expanduser('~/.nvm/current/bin')]
    for path in common_paths:
        full_path = os.path.join(path, cmd)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            logger.info(f'Found {cmd} at {full_path}')
            return full_path
    logger.error(f'Could not find executable: {cmd}')
    return None

def run(system_prompt: str, initial_query: str, client, model: str, request_config: Dict[str, Any]=None) -> Tuple[str, int]:
    """
    Main entry point for the Deep Think plugin.
    
    Combines SELF-DISCOVER reasoning structure discovery with 
    uncertainty-routed chain-of-thought generation.
    
    Args:
        system_prompt: System prompt for the model
        initial_query: User's initial query/problem
        client: OpenAI-compatible client instance
        model: Model identifier
        request_config: Additional configuration parameters
        
    Returns:
        Tuple of (response_text, completion_tokens_used)
    """
    logger.info('Starting Deep Think reasoning process')
    config = _parse_config(request_config or {})
    self_discover = SelfDiscover(client=client, model=model, max_tokens=config['max_tokens'])
    uncertainty_cot = UncertaintyRoutedCoT(client=client, model=model, max_tokens=config['max_tokens'])
    total_tokens = 0
    reasoning_structure = None
    if config['enable_self_discover']:
        logger.info('Discovering task-specific reasoning structure')
        discovery_result = self_discover.discover_reasoning_structure(task_description=_extract_task_description(initial_query, system_prompt), task_examples=None)
        reasoning_structure = discovery_result['reasoning_structure']
        total_tokens += discovery_result['completion_tokens']
        logger.info(f'Discovered reasoning structure with {len(reasoning_structure)} components')
    enhanced_prompt = _create_enhanced_prompt(system_prompt=system_prompt, initial_query=initial_query, reasoning_structure=reasoning_structure, config=config)
    logger.info('Generating response with uncertainty routing')
    generation_result = uncertainty_cot.generate_with_uncertainty_routing(prompt=enhanced_prompt, num_samples=config['deepthink_samples'], confidence_threshold=config['confidence_threshold'], temperature=config['temperature'], top_p=config['top_p'])
    total_tokens += generation_result['completion_tokens']
    logger.info(f'Routing decision: {generation_result['routing_decision']} (confidence: {generation_result['confidence_score']:.3f})')
    final_response = generation_result['final_response']
    final_response = _clean_response(final_response)
    logger.info(f'Deep Think completed successfully. Total tokens: {total_tokens}')
    return (final_response, total_tokens)

class ProxyConfig:
    """Manages proxy configuration with caching and validation."""
    _cached_config: Optional[Dict[str, Any]] = None
    _config_path: Optional[Path] = None

    @classmethod
    def load(cls, path: str=None, force_reload: bool=False) -> Dict[str, Any]:
        """
        Load and cache configuration.
        
        Args:
            path: Optional path to config file
            force_reload: Force reload even if cached
            
        Returns:
            Loaded and validated configuration dictionary
        """
        if cls._cached_config and (not force_reload):
            return cls._cached_config
        if not path:
            config_locations = [Path.home() / '.optillm' / 'proxy_config.yaml', Path.home() / '.optillm' / 'proxy_config.yml', Path(__file__).parent / 'example_config.yaml']
            for config_path in config_locations:
                if config_path.exists():
                    path = config_path
                    logger.info(f'Using config from: {path}')
                    break
            else:
                path = config_locations[0]
                cls._create_default(path)
        cls._config_path = Path(path)
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f) or {}
            if not isinstance(config, dict):
                raise ValueError('Configuration must be a dictionary')
            config = cls._interpolate_env_vars(config)
            config = cls._apply_defaults(config)
            config = cls._validate_config(config)
            cls._cached_config = config
            logger.debug(f'Loaded config with {len(config.get('providers', []))} providers')
            return config
        except Exception as e:
            logger.error(f'Failed to load proxy config from {path}: {e}')
            return cls._get_minimal_config()

    @classmethod
    def reload(cls) -> Dict[str, Any]:
        """Force reload configuration from disk."""
        return cls.load(force_reload=True)

    @staticmethod
    def _interpolate_env_vars(obj: Any) -> Any:
        """
        Recursively replace ${VAR} and ${VAR:-default} with environment values.
        
        Args:
            obj: Object to process (dict, list, str, or other)
            
        Returns:
            Processed object with environment variables replaced
        """
        if isinstance(obj, str):
            pattern = re.compile('\\$\\{([^}]+)\\}')

            def replacer(match):
                var_expr = match.group(1)
                if ':-' in var_expr:
                    var_name, default = var_expr.split(':-', 1)
                    value = os.environ.get(var_name.strip(), default)
                else:
                    var_name = var_expr.strip()
                    value = os.environ.get(var_name)
                    if value is None:
                        logger.warning(f'Environment variable ${{{var_name}}} not set')
                        return match.group(0)
                return value
            return pattern.sub(replacer, obj)
        elif isinstance(obj, dict):
            return {k: ProxyConfig._interpolate_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ProxyConfig._interpolate_env_vars(item) for item in obj]
        return obj

    @staticmethod
    def _apply_defaults(config: Dict) -> Dict:
        """
        Apply sensible defaults to configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with defaults applied
        """
        config.setdefault('providers', [])
        config.setdefault('routing', {})
        config.setdefault('monitoring', {})
        config.setdefault('timeouts', {})
        config.setdefault('queue', {})
        routing = config['routing']
        routing.setdefault('strategy', 'round_robin')
        routing.setdefault('health_check', {})
        health_check = routing['health_check']
        health_check.setdefault('enabled', True)
        health_check.setdefault('interval', 30)
        health_check.setdefault('timeout', 5)
        monitoring = config['monitoring']
        monitoring.setdefault('log_level', 'INFO')
        monitoring.setdefault('track_latency', True)
        monitoring.setdefault('track_errors', True)
        timeouts = config['timeouts']
        timeouts.setdefault('request', 30)
        timeouts.setdefault('connect', 5)
        queue = config['queue']
        queue.setdefault('max_concurrent', 100)
        queue.setdefault('timeout', 60)
        for i, provider in enumerate(config['providers']):
            provider.setdefault('name', f'provider_{i}')
            provider.setdefault('weight', 1)
            provider.setdefault('fallback_only', False)
            provider.setdefault('model_map', {})
            provider.setdefault('max_concurrent', None)
        return config

    @staticmethod
    def _validate_config(config: Dict) -> Dict:
        """
        Validate configuration structure and values.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validated configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        for provider in config.get('providers', []):
            if 'base_url' not in provider:
                raise ValueError(f'Provider {provider.get('name', 'unknown')} missing base_url')
            if 'api_key' not in provider:
                raise ValueError(f'Provider {provider.get('name', 'unknown')} missing api_key')
            if provider['weight'] <= 0:
                logger.warning(f'Provider {provider['name']} has invalid weight {provider['weight']}, setting to 1')
                provider['weight'] = 1
            if provider.get('max_concurrent') is not None:
                if not isinstance(provider['max_concurrent'], int) or provider['max_concurrent'] <= 0:
                    logger.warning(f'Provider {provider['name']} has invalid max_concurrent {provider['max_concurrent']}, removing limit')
                    provider['max_concurrent'] = None
        valid_strategies = ['weighted', 'round_robin', 'failover']
        strategy = config['routing']['strategy']
        if strategy not in valid_strategies:
            logger.warning(f"Invalid routing strategy '{strategy}', using 'round_robin'")
            config['routing']['strategy'] = 'round_robin'
        return config

    @staticmethod
    def _create_default(path: Path):
        """Create default configuration file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        default = '# OptiLLM Proxy Plugin Configuration\n# \n# This is an auto-generated configuration file.\n# Add your LLM provider endpoints and API keys below.\n# \n# Environment variables are supported: ${VAR_NAME} or ${VAR_NAME:-default_value}\n\nproviders:\n  # Example OpenAI provider (uncomment and configure)\n  # - name: openai_primary\n  #   base_url: https://api.openai.com/v1\n  #   api_key: ${OPENAI_API_KEY}\n  #   weight: 1\n\nrouting:\n  strategy: round_robin  # Options: weighted, round_robin, failover\n  health_check:\n    enabled: true\n    interval: 30  # seconds\n    timeout: 5    # seconds\n\ntimeouts:\n  request: 30     # Maximum time for a request (seconds)\n  connect: 5      # Maximum time for connection (seconds)\n\nqueue:\n  max_concurrent: 100  # Maximum concurrent requests\n  timeout: 60          # Maximum time in queue (seconds)\n\nmonitoring:\n  log_level: INFO\n  track_latency: true\n  track_errors: true\n\n# See proxy/README.md for full documentation\n'
        path.write_text(default)
        logger.info(f'Created default proxy config at {path}')
        logger.info('Please configure your providers in this file')

    @staticmethod
    def _get_minimal_config() -> Dict:
        """Return minimal working config as fallback."""
        return {'providers': [], 'routing': {'strategy': 'round_robin', 'health_check': {'enabled': False}}, 'timeouts': {'request': 30, 'connect': 5}, 'queue': {'max_concurrent': 100, 'timeout': 60}, 'monitoring': {'log_level': 'INFO', 'track_latency': False, 'track_errors': True}}

@staticmethod
def _create_default(path: Path):
    """Create default configuration file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    default = '# OptiLLM Proxy Plugin Configuration\n# \n# This is an auto-generated configuration file.\n# Add your LLM provider endpoints and API keys below.\n# \n# Environment variables are supported: ${VAR_NAME} or ${VAR_NAME:-default_value}\n\nproviders:\n  # Example OpenAI provider (uncomment and configure)\n  # - name: openai_primary\n  #   base_url: https://api.openai.com/v1\n  #   api_key: ${OPENAI_API_KEY}\n  #   weight: 1\n\nrouting:\n  strategy: round_robin  # Options: weighted, round_robin, failover\n  health_check:\n    enabled: true\n    interval: 30  # seconds\n    timeout: 5    # seconds\n\ntimeouts:\n  request: 30     # Maximum time for a request (seconds)\n  connect: 5      # Maximum time for connection (seconds)\n\nqueue:\n  max_concurrent: 100  # Maximum concurrent requests\n  timeout: 60          # Maximum time in queue (seconds)\n\nmonitoring:\n  log_level: INFO\n  track_latency: true\n  track_errors: true\n\n# See proxy/README.md for full documentation\n'
    path.write_text(default)
    logger.info(f'Created default proxy config at {path}')
    logger.info('Please configure your providers in this file')

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

def _discover_handlers(self):
    """Discover available approaches and plugins dynamically"""
    self._discover_approaches()
    self._discover_plugins()
    logger.info(f'Discovered {len(self._approaches_cache)} approaches, {len(self._plugins_cache)} plugins')

def loop_until_match(function: Callable, pattern_list: Tuple[str], num_attempts: int=10):
    """
    Repeatedly calls a function until its output matches one of the given patterns or max attempts is reached.

    Args:
        function (Callable): Function returning (answer: str, cb_log).
        pattern_list (Tuple[str]): Patterns to match in the answer.
        num_attempts (int): Max number of attempts (default: 10).

    Returns:
        Tuple[str, Any]: The matching answer and its corresponding log object.
    """
    correct_format = False
    for _ in range(num_attempts):
        answer, cb_log = function()
        for pattern in pattern_list:
            if pattern in answer:
                correct_format = True
        if correct_format:
            break
        logger.info('Wrong output formatting, retrying...')
    return (answer, cb_log)

class SelfDiscover:
    """
    Implementation of the SELF-DISCOVER framework.
    
    The framework operates in two stages:
    1. Stage 1: Discover task-specific reasoning structure (SELECT, ADAPT, IMPLEMENT)
    2. Stage 2: Use discovered structure to solve problem instances
    """

    def __init__(self, client, model: str, max_tokens: int=16382):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.reasoning_modules = get_all_modules()
        self.completion_tokens = 0

    def discover_reasoning_structure(self, task_description: str, task_examples: List[str]=None) -> Dict[str, Any]:
        """
        Stage 1: Discover reasoning structure for the given task.
        
        Args:
            task_description: Description of the task type
            task_examples: Optional examples of the task (without labels)
            
        Returns:
            Dict containing the discovered reasoning structure
        """
        logger.info('Starting SELF-DISCOVER reasoning structure discovery')
        selected_modules = self._select_modules(task_description, task_examples)
        logger.info(f'Selected {len(selected_modules)} reasoning modules')
        adapted_modules = self._adapt_modules(selected_modules, task_description, task_examples)
        logger.info('Adapted modules to be task-specific')
        reasoning_structure = self._implement_structure(adapted_modules, task_description, task_examples)
        logger.info('Implemented reasoning structure')
        return {'selected_modules': selected_modules, 'adapted_modules': adapted_modules, 'reasoning_structure': reasoning_structure, 'completion_tokens': self.completion_tokens}

    def _select_modules(self, task_description: str, task_examples: List[str]=None) -> List[Dict[str, Any]]:
        """SELECT: Choose relevant reasoning modules for the task."""
        module_descriptions = get_module_descriptions()
        modules_text = '\n'.join([f'{i + 1}. {desc}' for i, desc in enumerate(module_descriptions)])
        examples_text = ''
        if task_examples:
            examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
        select_prompt = f'You are an expert in problem-solving and reasoning. Given a task description and available reasoning modules, select the most relevant modules that would be useful for solving this type of task.\n\nTask description: {task_description}{examples_text}\n\nAvailable reasoning modules:\n{modules_text}\n\nInstructions:\n1. Analyze the task and identify what types of reasoning would be most helpful\n2. Select 3-7 reasoning modules that are most relevant for this task\n3. Consider both the complexity of the task and the complementary nature of different modules\n4. Avoid selecting too many similar modules\n5. IMPORTANT: Respond ONLY with a valid JSON array of numbers\n\nExample response format: [1, 5, 9, 15, 23]\n\nSelected modules (JSON array only):'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': select_prompt}], max_tokens=1024, temperature=0.3)
        self.completion_tokens += response.usage.completion_tokens
        try:
            response_text = response.choices[0].message.content.strip()
            json_match = re.search('\\[[\\d,\\s]+\\]', response_text)
            if json_match:
                selected_indices = json.loads(json_match.group(0))
            else:
                numbers = re.findall('\\b(\\d+)\\b', response_text)
                selected_indices = [int(n) for n in numbers[:7]]
            selected_modules = []
            for idx in selected_indices:
                if 1 <= idx <= len(self.reasoning_modules):
                    selected_modules.append(self.reasoning_modules[idx - 1])
            return selected_modules[:7]
        except Exception as e:
            logger.warning(f'Error parsing selected modules: {e}')
            return self.reasoning_modules[:5]

    def _adapt_modules(self, selected_modules: List[Dict[str, Any]], task_description: str, task_examples: List[str]=None) -> List[str]:
        """ADAPT: Rephrase modules to be more task-specific."""
        modules_text = '\n'.join([f'- {module['description']}' for module in selected_modules])
        examples_text = ''
        if task_examples:
            examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
        adapt_prompt = f'You are an expert in adapting general reasoning strategies to specific tasks. Given the selected reasoning modules and task description, rephrase each module to be more specific and tailored to this particular type of task.\n\nTask description: {task_description}{examples_text}\n\nSelected reasoning modules:\n{modules_text}\n\nInstructions:\n1. For each module, rephrase the description to be more specific to this task\n2. Keep the core reasoning approach but make it more actionable for this specific type of problem\n3. Use terminology and concepts relevant to the task domain\n4. Make the adapted descriptions more concrete and specific\n\nProvide the adapted modules as a numbered list:'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': adapt_prompt}], max_tokens=2048, temperature=0.3)
        self.completion_tokens += response.usage.completion_tokens
        response_text = response.choices[0].message.content.strip()
        adapted_modules = []
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if re.match('^\\d+\\.', line):
                adapted_desc = re.sub('^\\d+\\.\\s*', '', line)
                adapted_modules.append(adapted_desc)
        return adapted_modules

    def _implement_structure(self, adapted_modules: List[str], task_description: str, task_examples: List[str]=None) -> Dict[str, Any]:
        """IMPLEMENT: Create a structured reasoning plan in JSON format."""
        modules_text = '\n'.join([f'{i + 1}. {module}' for i, module in enumerate(adapted_modules)])
        examples_text = ''
        if task_examples:
            examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
        demo_structure = '{\n    "problem_analysis": "Analyze the core components and requirements",\n    "approach_selection": "Choose the most appropriate solution method",\n    "step_by_step_solution": {\n        "step_1": "First logical step with clear reasoning",\n        "step_2": "Second step building on previous results", \n        "step_3": "Continue logical progression"\n    },\n    "verification": "Check the solution for accuracy and completeness",\n    "final_answer": "Present the final result clearly"\n}'
        implement_prompt = f'You are an expert in creating structured reasoning plans. Given the adapted reasoning modules for a specific task, create a detailed JSON reasoning structure that can be followed step-by-step to solve instances of this task.\n\nTask description: {task_description}{examples_text}\n\nAdapted reasoning modules:\n{modules_text}\n\nExample of a reasoning structure format:\n{demo_structure}\n\nInstructions:\n1. Create a JSON structure that operationalizes the adapted reasoning modules\n2. The structure should be specific enough to guide step-by-step reasoning\n3. Include clear field names that indicate what should be filled in each step\n4. Make it actionable - each field should represent a concrete reasoning step\n5. Ensure the structure flows logically from problem understanding to final answer\n6. The structure should be comprehensive enough to handle the complexity of the task\n\n7. IMPORTANT: Return ONLY valid JSON with double quotes around all property names and string values\n8. Do not include any text before or after the JSON structure\n\nValid JSON reasoning structure:'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': implement_prompt}], max_tokens=2048, temperature=0.3)
        self.completion_tokens += response.usage.completion_tokens
        response_text = response.choices[0].message.content.strip()
        return self._parse_json_structure(response_text)

    def _parse_json_structure(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON structure with robust error handling and cleanup."""
        fallback_structure = {'problem_understanding': 'Analyze and understand the problem requirements', 'solution_approach': 'Determine the best approach based on problem characteristics', 'step_by_step_reasoning': 'Work through the problem systematically', 'verification': 'Verify the solution is correct and complete', 'final_answer': 'State the final answer clearly'}
        strategies = [self._extract_json_strategy_1, self._extract_json_strategy_2, self._extract_json_strategy_3, self._clean_and_parse_strategy]
        for i, strategy in enumerate(strategies, 1):
            try:
                structure = strategy(response_text)
                if structure and isinstance(structure, dict) and (len(structure) > 0):
                    logger.debug(f'Successfully parsed JSON using strategy {i}')
                    return structure
            except Exception as e:
                logger.debug(f'Strategy {i} failed: {e}')
                continue
        logger.warning(f'All JSON parsing strategies failed. Using fallback structure.')
        logger.debug(f'Raw response that failed to parse: {response_text[:500]}...')
        return fallback_structure

    def _extract_json_strategy_1(self, text: str) -> Dict[str, Any]:
        """Strategy 1: Find first complete JSON object with balanced braces."""
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError('No opening brace found')
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        if brace_count != 0:
            raise ValueError('Unbalanced braces')
        json_str = text[start_idx:end_idx]
        return json.loads(json_str)

    def _extract_json_strategy_2(self, text: str) -> Dict[str, Any]:
        """Strategy 2: Use regex with non-greedy matching."""
        json_match = re.search('\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}', text)
        if not json_match:
            raise ValueError('No JSON object found with regex')
        json_str = json_match.group(0)
        return json.loads(json_str)

    def _extract_json_strategy_3(self, text: str) -> Dict[str, Any]:
        """Strategy 3: Extract between ```json``` code blocks."""
        patterns = ['```json\\s*([^`]+)```', '```\\s*([^`]+)```', '`([^`]+)`']
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                try:
                    return json.loads(json_str)
                except:
                    continue
        raise ValueError('No valid JSON found in code blocks')

    def _clean_and_parse_strategy(self, text: str) -> Dict[str, Any]:
        """Strategy 4: Clean common formatting issues and parse."""
        json_match = re.search('\\{.*\\}', text, re.DOTALL)
        if not json_match:
            raise ValueError('No JSON-like content found')
        json_str = json_match.group(0)
        cleanups = [("(?<!\\\\)'([^']*)'(?=\\s*[,}])", '"\\1"'), ('([{,]\\s*)([a-zA-Z_][a-zA-Z0-9_]*)\\s*:', '\\1"\\2":'), (',\\s*([}\\]])', '\\1'), (',,+', ',')]
        for pattern, replacement in cleanups:
            json_str = re.sub(pattern, replacement, json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if 'line 1 column 2' in str(e):
                json_str = re.sub('^[^{]*', '', json_str)
                return json.loads(json_str)
            else:
                raise e

    def solve_with_structure(self, problem: str, reasoning_structure: Dict[str, Any]) -> str:
        """
        Stage 2: Use the discovered reasoning structure to solve a specific problem.
        """
        structure_text = json.dumps(reasoning_structure, indent=2)
        solve_prompt = f'Follow the step-by-step reasoning structure below to solve the given problem. Fill in each field with your reasoning and analysis, then provide your final answer.\n\nReasoning Structure:\n{structure_text}\n\nProblem to solve: {problem}\n\nInstructions:\n1. Work through each field in the reasoning structure systematically\n2. Provide detailed reasoning for each step\n3. Use the structure to guide your thinking process\n4. Ensure your reasoning is logical and well-supported\n5. Wrap your internal reasoning in <think> tags\n6. Provide a clear final answer after your reasoning\n\n<think>\n[Follow the reasoning structure step by step here]\n</think>\n\nBased on my systematic analysis using the reasoning structure, the answer is:'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': solve_prompt}], max_tokens=self.max_tokens, temperature=0.7)
        self.completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

def discover_reasoning_structure(self, task_description: str, task_examples: List[str]=None) -> Dict[str, Any]:
    """
        Stage 1: Discover reasoning structure for the given task.
        
        Args:
            task_description: Description of the task type
            task_examples: Optional examples of the task (without labels)
            
        Returns:
            Dict containing the discovered reasoning structure
        """
    logger.info('Starting SELF-DISCOVER reasoning structure discovery')
    selected_modules = self._select_modules(task_description, task_examples)
    logger.info(f'Selected {len(selected_modules)} reasoning modules')
    adapted_modules = self._adapt_modules(selected_modules, task_description, task_examples)
    logger.info('Adapted modules to be task-specific')
    reasoning_structure = self._implement_structure(adapted_modules, task_description, task_examples)
    logger.info('Implemented reasoning structure')
    return {'selected_modules': selected_modules, 'adapted_modules': adapted_modules, 'reasoning_structure': reasoning_structure, 'completion_tokens': self.completion_tokens}

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

def get_next_strategy_id(self) -> str:
    """Generate a unique ID for a new strategy."""
    self.metrics['last_strategy_id'] += 1
    new_id = f'strategy_{self.metrics['last_strategy_id']}'
    logger.info(f'Generated new strategy ID: {new_id}')
    return new_id

def should_create_new_strategy(problem_type: str, query: str, existing_strategies: List[Strategy], db: StrategyDatabase) -> Tuple[bool, Optional[Strategy]]:
    """
    Determine whether to create a new strategy or update an existing one.
    
    Args:
        problem_type: The type of problem
        query: The current query/problem
        existing_strategies: Existing strategies for this problem type
        db: Strategy database
    
    Returns:
        Tuple[bool, Optional[Strategy]]: 
            - Boolean indicating if a new strategy should be created
            - The similar strategy to update (if any)
    """
    if not existing_strategies:
        return (True, None)
    if len(existing_strategies) >= MAX_STRATEGIES_PER_TYPE:
        similar_strategy_result = db.find_similar_strategy(problem_type, query)
        if similar_strategy_result:
            similar_strategy, similarity = similar_strategy_result
            logger.info(f'Found similar strategy {similar_strategy.strategy_id} with text similarity {similarity:.2f}')
            return (False, similar_strategy)
        similar_examples_result = db.find_similar_examples(problem_type, query)
        if similar_examples_result:
            similar_strategy, similarity = similar_examples_result
            logger.info(f'Found strategy {similar_strategy.strategy_id} with similar examples, similarity {similarity:.2f}')
            return (False, similar_strategy)
        if existing_strategies:
            existing_strategies.sort(key=lambda s: s.success_rate)
            worst_strategy = existing_strategies[0]
            logger.info(f'At maximum strategies for {problem_type}, updating lowest performing strategy {worst_strategy.strategy_id}')
            return (False, worst_strategy)
    similar_strategy_result = db.find_similar_strategy(problem_type, query, threshold=STRATEGY_CREATION_THRESHOLD)
    if similar_strategy_result:
        similar_strategy, similarity = similar_strategy_result
        logger.info(f'Found similar strategy {similar_strategy.strategy_id} with text similarity {similarity:.2f}')
        return (False, similar_strategy)
    logger.info(f'No similar strategy found for {problem_type}, creating a new one')
    return (True, None)

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

def __init__(self):
    self._sessions: Dict[str, BrowserSessionManager] = {}
    self._lock = threading.Lock()
    self._session_timestamps: Dict[str, float] = {}
    self._max_session_age = 300

class AutoThinkProcessor:
    """
    AutoThink processor for controlled thinking with 
    complexity classification and steering vectors.
    """

    def __init__(self, config: Dict[str, Any], tokenizer: PreTrainedTokenizer, model: PreTrainedModel):
        """
        Initialize the AutoThink processor.
        
        Args:
            config: Configuration dictionary
            tokenizer: Model tokenizer
            model: Language model
        """
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        self.classifier = ComplexityClassifier(self.config['classifier_model'])
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
            logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
            logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
        self.steering_manager = None
        self.steering_hooks = []
        if self.config['steering_dataset']:
            self._setup_steering()

    def _setup_steering(self):
        """Set up steering vector management."""
        try:
            self.steering_manager = SteeringVectorManager(dataset_name=self.config['steering_dataset'], target_layer=self.config['target_layer'])
            if 'pattern_strengths' in self.config:
                for pattern, strength in self.config['pattern_strengths'].items():
                    self.steering_manager.set_steering_strength(pattern, strength)
            self.steering_manager.create_tokenized_contexts(self.tokenizer)
            self.steering_hooks = install_steering_hooks(self.model, self.steering_manager, self.tokenizer)
            logger.info(f'STEERING: Set up steering with {len(self.steering_hooks)} hooks')
        except Exception as e:
            logger.error(f'STEERING: Error setting up steering: {e}')
            self.steering_manager = None
            self.steering_hooks = []

    def _cleanup_steering(self):
        """Clean up steering hooks."""
        if self.steering_hooks:
            remove_steering_hooks(self.steering_hooks)
            self.steering_hooks = []
            logger.info('STEERING: Hooks removed successfully')

    def classify_complexity(self, query: str) -> Tuple[str, float]:
        """
        Classify query complexity.
        
        Args:
            query: The query to classify
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
        complexity, confidence = self.classifier.get_complexity_with_confidence(query)
        logger.info(f'Query classified as {complexity} with confidence {confidence:.2f}')
        return (complexity, confidence)

    def get_token_budget(self, complexity: str) -> Tuple[int, int]:
        """
        Get token budget based on complexity.
        
        Args:
            complexity: Complexity label (HIGH or LOW)
            
        Returns:
            Tuple of (min_tokens, max_tokens)
        """
        if complexity == 'HIGH':
            return (self.config['high_complexity_min_tokens'], self.config['high_complexity_max_tokens'])
        else:
            return (self.config['low_complexity_min_tokens'], self.config['low_complexity_max_tokens'])

    def is_thought_switch(self, token: int) -> bool:
        """
        Check if adding this token creates a thought switch sequence.
        
        Args:
            token: Token ID to check
            
        Returns:
            Boolean indicating if this completes a thought switch
        """
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    @torch.inference_mode()
    def process(self, messages: List[Dict[str, str]]) -> str:
        """
        Process messages with AutoThink's controlled thinking.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated response
        """
        try:
            query = self._extract_query(messages)
            complexity, confidence = self.classify_complexity(query)
            min_tokens, max_tokens = self.get_token_budget(complexity)
            logger.info(f'Using token budget: {min_tokens}-{max_tokens} for {complexity} complexity')
            thinking_messages = messages.copy()
            thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
            tokens = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=True, return_tensors='pt').to(self.model.device)
            if self.steering_hooks:
                token_ids = tokens[0].tolist()
                prompt_text = self.tokenizer.decode(token_ids)
                for hook, _ in self.steering_hooks:
                    hook.reset()
                    hook.update_token_history(token_ids)
                    hook.update_context(prompt_text)
                    hook.try_match()
            kv = DynamicCache()
            n_thinking_tokens = 0
            seen_end_think = False
            response_chunks = []
            while True:
                out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
                logits = out.logits[0, -1, :]
                force_end = n_thinking_tokens >= max_tokens or self.thought_count >= self.config['max_thoughts']
                if force_end and (not seen_end_think):
                    logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
                    next_token = self.end_think_token
                    response_chunks.append(self.tokenizer.decode([next_token]))
                    seen_end_think = True
                    tokens = torch.tensor([[next_token]]).to(tokens.device)
                    continue
                else:
                    next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
                kv = out.past_key_values
                next_str = self.tokenizer.decode([next_token])
                if self.steering_hooks:
                    for hook, _ in self.steering_hooks:
                        hook.update_token_history([next_token])
                if not seen_end_think and self.is_thought_switch(next_token):
                    self.thought_count += 1
                    logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
                    self.current_sequence = []
                if next_token == self.end_think_token:
                    seen_end_think = True
                    logger.debug('Found end think token')
                    if n_thinking_tokens < min_tokens:
                        replacement = random.choice(self.config['thought_switch_tokens'])
                        logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                        response_chunks.append(replacement)
                        replacement_tokens = self.tokenizer.encode(replacement)
                        n_thinking_tokens += len(replacement_tokens)
                        tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                        self.thought_count += 1
                        seen_end_think = False
                        continue
                if next_token == self.model.config.eos_token_id:
                    logger.debug('Found EOS token')
                    if seen_end_think:
                        logger.debug('Reached EOS after end think token - stopping generation')
                        response_chunks.append(next_str)
                        break
                    elif n_thinking_tokens < min_tokens:
                        replacement = random.choice(self.config['thought_switch_tokens'])
                        logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                        response_chunks.append(replacement)
                        replacement_tokens = self.tokenizer.encode(replacement)
                        n_thinking_tokens += len(replacement_tokens)
                        tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                        self.thought_count += 1
                        continue
                    else:
                        logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                        response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                        tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                        seen_end_think = True
                        continue
                response_chunks.append(next_str)
                if not seen_end_think:
                    n_thinking_tokens += 1
                if self.steering_hooks:
                    for hook, _ in self.steering_hooks:
                        hook.update_token_history([next_token])
                        hook.update_context(next_str)
                        hook.try_match()
                tokens = torch.tensor([[next_token]]).to(tokens.device)
            if self.steering_hooks:
                for hook, _ in self.steering_hooks:
                    hook.reset()
            self._cleanup_steering()
            response = ''.join(response_chunks)
            full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
            logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}')
            return full_response
        except Exception as e:
            self._cleanup_steering()
            logger.error(f'Error in AutoThink processing: {str(e)}')
            raise

    def _extract_query(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract the query from messages for classification.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Extracted query string
        """
        user_messages = [m['content'] for m in messages if m['role'] == 'user']
        if user_messages:
            return user_messages[-1]
        return ' '.join((m['content'] for m in messages))

def _setup_steering(self):
    """Set up steering vector management."""
    try:
        self.steering_manager = SteeringVectorManager(dataset_name=self.config['steering_dataset'], target_layer=self.config['target_layer'])
        if 'pattern_strengths' in self.config:
            for pattern, strength in self.config['pattern_strengths'].items():
                self.steering_manager.set_steering_strength(pattern, strength)
        self.steering_manager.create_tokenized_contexts(self.tokenizer)
        self.steering_hooks = install_steering_hooks(self.model, self.steering_manager, self.tokenizer)
        logger.info(f'STEERING: Set up steering with {len(self.steering_hooks)} hooks')
    except Exception as e:
        logger.error(f'STEERING: Error setting up steering: {e}')
        self.steering_manager = None
        self.steering_hooks = []

def _cleanup_steering(self):
    """Clean up steering hooks."""
    if self.steering_hooks:
        remove_steering_hooks(self.steering_hooks)
        self.steering_hooks = []
        logger.info('STEERING: Hooks removed successfully')

def classify_complexity(self, query: str) -> Tuple[str, float]:
    """
        Classify query complexity.
        
        Args:
            query: The query to classify
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
    complexity, confidence = self.classifier.get_complexity_with_confidence(query)
    logger.info(f'Query classified as {complexity} with confidence {confidence:.2f}')
    return (complexity, confidence)

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

def set_steering_strength(self, pattern: str, strength: float):
    """
        Set the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            strength: The steering strength
        """
    self.pattern_strengths[pattern] = strength
    logger.info(f'STEERING: Set strength for {pattern} to {strength}')

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

class ConfidenceThresholdCalibrator:
    """
    Calibrates confidence thresholds based on warmup traces.
    """

    def __init__(self, variant: str='low'):
        """
        Initialize the threshold calibrator.
        
        Args:
            variant: "low" (aggressive, top 10%) or "high" (conservative, top 90%)
        """
        self.variant = variant
        self.warmup_confidences = []

    def add_warmup_trace(self, confidence_stats: Dict[str, float]):
        """
        Add confidence statistics from a warmup trace.
        
        Args:
            confidence_stats: Dictionary with confidence metrics
        """
        self.warmup_confidences.append(confidence_stats)

    def calculate_threshold(self, metric: str='average_confidence') -> float:
        """
        Calculate the confidence threshold based on warmup traces.
        
        Args:
            metric: Which confidence metric to use for threshold calculation
            
        Returns:
            Calculated threshold value
        """
        if not self.warmup_confidences:
            logger.warning('No warmup traces available for threshold calculation')
            return 0.0
        confidences = [stats[metric] for stats in self.warmup_confidences]
        if self.variant == 'low':
            threshold = np.percentile(confidences, 90)
        else:
            threshold = np.percentile(confidences, 10)
        logger.info(f'Calculated {self.variant} threshold: {threshold:.4f} for metric: {metric}')
        return threshold

    def should_terminate_trace(self, current_confidence: float, threshold: float) -> bool:
        """
        Determine if current trace should be terminated based on confidence.
        
        Args:
            current_confidence: Current confidence value
            threshold: Threshold for termination
            
        Returns:
            True if trace should be terminated
        """
        return current_confidence < threshold

def calculate_threshold(self, metric: str='average_confidence') -> float:
    """
        Calculate the confidence threshold based on warmup traces.
        
        Args:
            metric: Which confidence metric to use for threshold calculation
            
        Returns:
            Calculated threshold value
        """
    if not self.warmup_confidences:
        logger.warning('No warmup traces available for threshold calculation')
        return 0.0
    confidences = [stats[metric] for stats in self.warmup_confidences]
    if self.variant == 'low':
        threshold = np.percentile(confidences, 90)
    else:
        threshold = np.percentile(confidences, 10)
    logger.info(f'Calculated {self.variant} threshold: {threshold:.4f} for metric: {metric}')
    return threshold

def test_imports():
    """Test that all DeepConf components can be imported."""
    logger.info('Testing DeepConf imports...')
    try:
        from optillm.deepconf import deepconf_decode
        from optillm.deepconf.confidence import ConfidenceCalculator, ConfidenceThresholdCalibrator
        from optillm.deepconf.processor import DeepConfProcessor, TraceResult, DEFAULT_CONFIG
        logger.info('✓ All imports successful')
        return True
    except ImportError as e:
        logger.error(f'✗ Import failed: {e}')
        return False

def test_threshold_calibrator():
    """Test ConfidenceThresholdCalibrator functionality."""
    logger.info('Testing ConfidenceThresholdCalibrator...')
    try:
        from optillm.deepconf.confidence import ConfidenceThresholdCalibrator
        calibrator = ConfidenceThresholdCalibrator(variant='low')
        for i in range(5):
            stats = {'average_confidence': 1.0 + i * 0.1, 'bottom_10_percent': 0.8 + i * 0.05, 'lowest_group': 0.7 + i * 0.02}
            calibrator.add_warmup_trace(stats)
        threshold = calibrator.calculate_threshold('average_confidence')
        assert isinstance(threshold, float) and threshold > 0
        should_terminate = calibrator.should_terminate_trace(0.5, threshold)
        import numpy as np
        assert isinstance(should_terminate, (bool, np.bool_))
        logger.info('✓ ConfidenceThresholdCalibrator tests passed')
        return True
    except Exception as e:
        import traceback
        logger.error(f'✗ ConfidenceThresholdCalibrator test failed: {e}')
        logger.error(traceback.format_exc())
        return False

def test_info_function():
    """Test the info function."""
    logger.info('Testing get_deepconf_info...')
    try:
        from optillm.deepconf.deepconf import get_deepconf_info
        info = get_deepconf_info()
        required_keys = ['name', 'description', 'local_models_only', 'variants', 'default_config']
        for key in required_keys:
            assert key in info, f'Missing key: {key}'
        assert info['local_models_only'] == True
        assert 'low' in info['variants'] and 'high' in info['variants']
        logger.info('✓ Info function tests passed')
        return True
    except Exception as e:
        logger.error(f'✗ Info function test failed: {e}')
        return False

def run_tests(test_cases: List[Dict], approaches: List[str], client, model: str, single_test_name: str=None) -> List[Dict]:
    results = []
    for test_case in test_cases:
        if single_test_name is None or test_case['name'] == single_test_name:
            result = run_test_case(test_case, approaches, client, model)
            results.append(result)
            logger.info(f'Completed test case: {test_case['name']}')
        if single_test_name and test_case['name'] == single_test_name:
            break
    return results

