# Cluster 6

def save_result(filename: str, result: Dict):
    """Save a single result to the results file."""
    results = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            results = []
    results.append(result)
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

def load_existing_results(filename: str) -> List[Dict]:
    """Load existing results from file if it exists."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_existing_results(filename: str) -> list[Dict]:
    """Load existing results from file if it exists."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_result(filename: str, result: Dict):
    """Save a single result to the results file."""
    results = load_existing_results(filename)
    results.append(result)
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

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

def evaluate_dataset(model: str, output_file: str):
    """Evaluate the dataset using RTC methodology."""
    dataset = load_dataset('lmarena-ai/arena-hard-auto-v0.1')
    results = []
    passed_rtc_count = 0
    total_examples = 0
    for item in tqdm(dataset['train'], desc='Evaluating examples'):
        query = extract_first_turn_content(item['turns'])
        if not query:
            continue
        passed_rtc, similarity_score, details = perform_rtc_evaluation(query, model)
        result = {'id': total_examples, 'query': query, 'passed_rtc': passed_rtc, 'similarity_score': similarity_score, 'evaluation_details': details}
        results.append(result)
        if passed_rtc:
            passed_rtc_count += 1
        total_examples += 1
        with open(output_file, 'w') as f:
            json.dump({'model': model, 'total_examples': total_examples, 'passed_rtc': passed_rtc_count, 'rtc_pass_rate': passed_rtc_count / total_examples if total_examples > 0 else 0, 'results': results}, f, indent=2)
    logger.info(f'\nEvaluation Summary for {model}:')
    logger.info(f'Total examples evaluated: {total_examples}')
    logger.info(f'Examples passing RTC: {passed_rtc_count}')
    logger.info(f'RTC pass rate: {passed_rtc_count / total_examples * 100:.2f}%')

def load_existing_results(filename: str) -> List[Dict]:
    """Load existing results from file if it exists."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_result(filename: str, result: Dict):
    """Save a single result to the results file."""
    results = load_existing_results(filename)
    results.append(result)
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

def save_raw_response(filename: str, problem_id: int, response_data: Dict):
    """Save raw response data (including logprobs) to a separate file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    timestamp = int(time.time())
    response_id = f'{problem_id}_{timestamp}'
    try:
        with open(filename, 'r') as f:
            raw_responses = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        raw_responses = {}
    raw_responses[response_id] = response_data
    with open(filename, 'w') as f:
        json.dump(raw_responses, f)
    return response_id

def load_existing_results(filename: str) -> List[Dict]:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_result(filename: str, result: Dict):
    results = load_existing_results(filename)
    results.append(result)
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

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

class MCPConfigManager:
    """Manages MCP configuration loading and validation"""

    def __init__(self, config_path: Optional[str]=None):
        """Initialize with optional custom config path"""
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / '.optillm' / 'mcp_config.json'
        self.servers: Dict[str, ServerConfig] = {}
        self.log_level: str = 'INFO'

    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if not self.config_path.exists():
                logger.warning(f'MCP config file not found at {self.config_path}')
                return False
            with open(self.config_path, 'r') as f:
                config_data = f.read()
                logger.debug(f'Raw config data: {config_data}')
                config = json.loads(config_data)
            self.log_level = config.get('log_level', 'INFO')
            log_level = getattr(logging, self.log_level.upper(), logging.INFO)
            logger.setLevel(log_level)
            servers_config = config.get('mcpServers', {})
            for server_name, server_config in servers_config.items():
                self.servers[server_name] = ServerConfig.from_dict(server_config)
                logger.debug(f'Loaded server config for {server_name}: {server_config}')
            logger.info(f'Loaded configuration with {len(self.servers)} servers')
            return True
        except Exception as e:
            logger.error(f'Error loading MCP configuration: {e}')
            logger.error(traceback.format_exc())
            return False

    def create_default_config(self) -> bool:
        """Create a default configuration file if none exists"""
        try:
            if self.config_path.exists():
                return True
            default_config = {'mcpServers': {}, 'log_level': 'INFO'}
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f'Created default configuration at {self.config_path}')
            return True
        except Exception as e:
            logger.error(f'Error creating default configuration: {e}')
            return False

def __init__(self, config_path: Optional[str]=None):
    """Initialize with optional custom config path"""
    if config_path:
        self.config_path = Path(config_path)
    else:
        self.config_path = Path.home() / '.optillm' / 'mcp_config.json'
    self.servers: Dict[str, ServerConfig] = {}
    self.log_level: str = 'INFO'

def load_config(self) -> bool:
    """Load configuration from file"""
    try:
        if not self.config_path.exists():
            logger.warning(f'MCP config file not found at {self.config_path}')
            return False
        with open(self.config_path, 'r') as f:
            config_data = f.read()
            logger.debug(f'Raw config data: {config_data}')
            config = json.loads(config_data)
        self.log_level = config.get('log_level', 'INFO')
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)
        servers_config = config.get('mcpServers', {})
        for server_name, server_config in servers_config.items():
            self.servers[server_name] = ServerConfig.from_dict(server_config)
            logger.debug(f'Loaded server config for {server_name}: {server_config}')
        logger.info(f'Loaded configuration with {len(self.servers)} servers')
        return True
    except Exception as e:
        logger.error(f'Error loading MCP configuration: {e}')
        logger.error(traceback.format_exc())
        return False

def create_default_config(self) -> bool:
    """Create a default configuration file if none exists"""
    try:
        if self.config_path.exists():
            return True
        default_config = {'mcpServers': {}, 'log_level': 'INFO'}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f'Created default configuration at {self.config_path}')
        return True
    except Exception as e:
        logger.error(f'Error creating default configuration: {e}')
        return False

def run(system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Tuple[str, int]:
    """
    Main proxy plugin entry point.
    
    Supports three usage modes:
    1. Standalone proxy: model="proxy-gpt-4"
    2. Wrapping approach: extra_body={"optillm_approach": "proxy", "proxy_wrap": "moa"}
    3. Combined approach: model="bon&proxy-gpt-4"
    
    Args:
        system_prompt: System message for the LLM
        initial_query: User's query
        client: Original OpenAI client (used as fallback)
        model: Model identifier
        request_config: Additional request configuration
    
    Returns:
        Tuple of (response_text, token_count)
    """
    try:
        config = ProxyConfig.load()
        if not config.get('providers'):
            logger.warning('No providers configured, falling back to original client')
            response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}])
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            return (response_dict, 0)
        config_key = str(config)
        if config_key not in _proxy_client_cache:
            logger.debug('Creating new proxy client instance')
            _proxy_client_cache[config_key] = ProxyClient(config=config, fallback_client=client)
        else:
            logger.debug('Reusing existing proxy client instance')
        proxy_client = _proxy_client_cache[config_key]
        wrapped_approach = None
        if request_config:
            wrapped_approach = request_config.get('proxy_wrap') or request_config.get('wrapped_approach') or request_config.get('wrap')
        if wrapped_approach:
            logger.info(f'Proxy wrapping approach/plugin: {wrapped_approach}')
            handler = ApproachHandler()
            result = handler.handle(wrapped_approach, system_prompt, initial_query, proxy_client, model, request_config)
            if result is not None:
                return result
            else:
                logger.warning(f"Approach/plugin '{wrapped_approach}' not found, using direct proxy")
        if '-' in model and (not wrapped_approach):
            parts = model.split('-', 1)
            potential_approach = parts[0]
            actual_model = parts[1] if len(parts) > 1 else model
            handler = ApproachHandler()
            result = handler.handle(potential_approach, system_prompt, initial_query, proxy_client, actual_model, request_config)
            if result is not None:
                logger.info(f'Proxy routing approach/plugin: {potential_approach}')
                return result
        logger.info(f'Direct proxy routing for model: {model}')
        supports_system_messages = _get_system_message_support(proxy_client, model)
        messages = _format_messages_for_model(system_prompt, initial_query, supports_system_messages)
        if not supports_system_messages:
            logger.info(f'Using fallback message formatting for {model} (no system message support)')
        response = proxy_client.chat.completions.create(model=model, messages=messages, **request_config or {})
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        return (response_dict, 0)
    except Exception as e:
        logger.error(f'Proxy plugin error: {e}', exc_info=True)
        logger.info('Falling back to original client')
        response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}])
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        return (response_dict, 0)

def execute_code(code: str) -> Tuple[Any, str]:
    """Attempt to execute the code using Jupyter notebook kernel and return result or error."""
    logger.info('Attempting to execute code in notebook kernel')
    logger.info(f'Code:\n{code}')
    try:
        sanitized_code = sanitize_code(code)
        notebook = nbformat.v4.new_notebook()
        enhanced_code = f"""\n{sanitized_code}\n\n# Capture the answer variable for output\nif 'answer' in locals():\n    print(f"ANSWER_RESULT: {{answer}}")\nelse:\n    print("ANSWER_RESULT: No answer variable found")\n"""
        notebook['cells'] = [nbformat.v4.new_code_cell(enhanced_code)]
        notebook_json = nbformat.writes(notebook)
        notebook_bytes = notebook_json.encode('utf-8')
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.ipynb', delete=False) as tmp:
            tmp.write(notebook_bytes)
            tmp.flush()
            tmp_name = tmp.name
        try:
            with open(tmp_name, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            ep = ExecutePreprocessor(timeout=30, kernel_name='python3')
            ep.preprocess(nb, {'metadata': {'path': './'}})
            output = ''
            error_output = ''
            for cell in nb.cells:
                if cell.cell_type == 'code' and cell.outputs:
                    for output_item in cell.outputs:
                        if output_item.output_type == 'stream':
                            if output_item.name == 'stdout':
                                output += output_item.text
                            elif output_item.name == 'stderr':
                                error_output += output_item.text
                        elif output_item.output_type == 'execute_result':
                            output += str(output_item.data.get('text/plain', ''))
                        elif output_item.output_type == 'error':
                            error_output += f'{output_item.ename}: {output_item.evalue}'
            if error_output:
                logger.error(f'Execution failed: {error_output}')
                return (None, error_output)
            output = output.strip()
            if 'ANSWER_RESULT:' in output:
                answer_line = [line for line in output.split('\n') if 'ANSWER_RESULT:' in line][-1]
                answer_str = answer_line.split('ANSWER_RESULT:', 1)[1].strip()
                if answer_str == 'No answer variable found':
                    error = 'Code executed but did not produce an answer variable'
                    logger.warning(error)
                    return (None, error)
                try:
                    answer = ast.literal_eval(answer_str)
                except (ValueError, SyntaxError):
                    answer = answer_str
                logger.info(f'Execution successful. Answer: {answer}')
                return (answer, None)
            elif output:
                logger.info(f'Execution completed with output: {output}')
                return (output, None)
            else:
                error = 'Code executed but produced no output'
                logger.warning(error)
                return (None, error)
        finally:
            try:
                os.unlink(tmp_name)
            except:
                pass
    except Exception as e:
        error = f'Notebook execution failed: {str(e)}'
        logger.error(error)
        return (None, error)

def execute_code(code: str) -> str:
    """Execute Python code in a Jupyter notebook environment."""
    notebook = nbformat.v4.new_notebook()
    notebook['cells'] = [nbformat.v4.new_code_cell(code)]
    notebook_json = nbformat.writes(notebook)
    notebook_bytes = notebook_json.encode('utf-8')
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ipynb', delete=False) as tmp:
        tmp.write(notebook_bytes)
        tmp.flush()
        tmp_name = tmp.name
    try:
        with open(tmp_name, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=30, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': './'}})
        output = ''
        for cell in nb.cells:
            if cell.cell_type == 'code' and cell.outputs:
                for output_item in cell.outputs:
                    if output_item.output_type == 'stream':
                        output += output_item.text
                    elif output_item.output_type == 'execute_result':
                        output += str(output_item.data.get('text/plain', ''))
        return output.strip()
    finally:
        os.unlink(tmp_name)

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

def init_cepo_config(cmd_line_args: dict) -> CepoConfig:
    cepo_args = {key.split('cepo_')[1]: value for key, value in cmd_line_args.items() if 'cepo' in key and 'cepo_config_file' != key and (value is not None)}
    cepo_config_yaml = {}
    if cmd_line_args.get('cepo_config_file', None):
        with open(cmd_line_args['cepo_config_file'], 'r') as yaml_file:
            cepo_config_yaml = yaml.safe_load(yaml_file)
    cepo_args = {**cepo_config_yaml, **cepo_args}
    return CepoConfig(**cepo_args)

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

class TestMCPConfigManager:
    """Test MCP configuration management"""

    def test_init_default_path(self):
        """Test default configuration path"""
        manager = MCPConfigManager()
        expected_path = Path.home() / '.optillm' / 'mcp_config.json'
        assert manager.config_path == expected_path

    def test_init_custom_path(self):
        """Test custom configuration path"""
        custom_path = '/tmp/custom_mcp_config.json'
        manager = MCPConfigManager(custom_path)
        assert manager.config_path == Path(custom_path)

    def test_create_default_config(self):
        """Test creating default configuration file"""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'test_config.json'
            manager = MCPConfigManager(str(config_path))
            success = manager.create_default_config()
            assert success
            assert config_path.exists()
            with open(config_path) as f:
                config = json.load(f)
            assert 'mcpServers' in config
            assert 'log_level' in config
            assert config['mcpServers'] == {}
            assert config['log_level'] == 'INFO'

    def test_load_valid_config(self):
        """Test loading valid configuration"""
        import tempfile
        config_data = {'mcpServers': {'test_server': {'transport': 'stdio', 'command': 'test-command', 'args': ['arg1', 'arg2']}}, 'log_level': 'DEBUG'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        try:
            manager = MCPConfigManager(config_path)
            success = manager.load_config()
            assert success
            assert len(manager.servers) == 1
            assert 'test_server' in manager.servers
            assert manager.servers['test_server'].command == 'test-command'
            assert manager.log_level == 'DEBUG'
        finally:
            os.unlink(config_path)

    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration"""
        manager = MCPConfigManager('/nonexistent/path.json')
        success = manager.load_config()
        assert not success
        assert len(manager.servers) == 0

def test_init_default_path(self):
    """Test default configuration path"""
    manager = MCPConfigManager()
    expected_path = Path.home() / '.optillm' / 'mcp_config.json'
    assert manager.config_path == expected_path

def test_init_custom_path(self):
    """Test custom configuration path"""
    custom_path = '/tmp/custom_mcp_config.json'
    manager = MCPConfigManager(custom_path)
    assert manager.config_path == Path(custom_path)

def test_create_default_config(self):
    """Test creating default configuration file"""
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / 'test_config.json'
        manager = MCPConfigManager(str(config_path))
        success = manager.create_default_config()
        assert success
        assert config_path.exists()
        with open(config_path) as f:
            config = json.load(f)
        assert 'mcpServers' in config
        assert 'log_level' in config
        assert config['mcpServers'] == {}
        assert config['log_level'] == 'INFO'

def test_load_valid_config(self):
    """Test loading valid configuration"""
    import tempfile
    config_data = {'mcpServers': {'test_server': {'transport': 'stdio', 'command': 'test-command', 'args': ['arg1', 'arg2']}}, 'log_level': 'DEBUG'}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name
    try:
        manager = MCPConfigManager(config_path)
        success = manager.load_config()
        assert success
        assert len(manager.servers) == 1
        assert 'test_server' in manager.servers
        assert manager.servers['test_server'].command == 'test-command'
        assert manager.log_level == 'DEBUG'
    finally:
        os.unlink(config_path)

def test_load_nonexistent_config(self):
    """Test loading non-existent configuration"""
    manager = MCPConfigManager('/nonexistent/path.json')
    success = manager.load_config()
    assert not success
    assert len(manager.servers) == 0

class TestMCPServerManager:
    """Test MCP server manager functionality"""

    def test_init(self):
        """Test MCPServerManager initialization"""
        config_manager = MCPConfigManager()
        manager = MCPServerManager(config_manager)
        assert manager.config_manager == config_manager
        assert manager.servers == {}
        assert not manager.initialized
        assert manager.all_tools == []
        assert manager.all_resources == []
        assert manager.all_prompts == []

    def test_get_tools_for_model_empty(self):
        """Test getting tools when no tools are available"""
        config_manager = MCPConfigManager()
        manager = MCPServerManager(config_manager)
        tools = manager.get_tools_for_model()
        assert tools == []

    def test_get_capabilities_description_no_servers(self):
        """Test getting capabilities description with no servers"""
        config_manager = MCPConfigManager()
        manager = MCPServerManager(config_manager)
        description = manager.get_capabilities_description()
        assert 'No MCP servers available' in description

def test_init(self):
    """Test MCPServerManager initialization"""
    config_manager = MCPConfigManager()
    manager = MCPServerManager(config_manager)
    assert manager.config_manager == config_manager
    assert manager.servers == {}
    assert not manager.initialized
    assert manager.all_tools == []
    assert manager.all_resources == []
    assert manager.all_prompts == []

def test_get_tools_for_model_empty(self):
    """Test getting tools when no tools are available"""
    config_manager = MCPConfigManager()
    manager = MCPServerManager(config_manager)
    tools = manager.get_tools_for_model()
    assert tools == []

def test_get_capabilities_description_no_servers(self):
    """Test getting capabilities description with no servers"""
    config_manager = MCPConfigManager()
    manager = MCPServerManager(config_manager)
    description = manager.get_capabilities_description()
    assert 'No MCP servers available' in description

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

def test_proxy_plugin_timeout_config():
    """Test that proxy plugin properly configures timeout settings"""
    from optillm.plugins.proxy.config import ProxyConfig
    import tempfile
    import yaml
    config = {'providers': [{'name': 'test_provider', 'base_url': 'http://localhost:8000/v1', 'api_key': 'test-key'}], 'timeouts': {'request': 10, 'connect': 3}, 'queue': {'max_concurrent': 50, 'timeout': 30}}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    try:
        loaded_config = ProxyConfig.load(config_path)
        assert 'timeouts' in loaded_config, 'Config should contain timeouts section'
        assert loaded_config['timeouts'].get('request') == 10, 'Request timeout should be 10'
        assert loaded_config['timeouts'].get('connect') == 3, 'Connect timeout should be 3'
        assert 'queue' in loaded_config, 'Config should contain queue section'
        assert loaded_config['queue']['max_concurrent'] == 50, 'Max concurrent should be 50'
        assert loaded_config['queue']['timeout'] == 30, 'Queue timeout should be 30'
    finally:
        import os
        os.unlink(config_path)

def test_proxy_plugin_timeout_handling():
    """Test that proxy plugin handles timeouts correctly"""
    from optillm.plugins.proxy.client import ProxyClient
    from unittest.mock import Mock, patch
    import concurrent.futures
    config = {'providers': [{'name': 'slow_provider', 'base_url': 'http://localhost:8001/v1', 'api_key': 'test-key-1'}, {'name': 'fast_provider', 'base_url': 'http://localhost:8002/v1', 'api_key': 'test-key-2'}], 'routing': {'strategy': 'round_robin', 'health_check': {'enabled': False}}, 'timeouts': {'request': 2, 'connect': 1}, 'queue': {'max_concurrent': 10, 'timeout': 5}}
    proxy_client = ProxyClient(config)
    assert proxy_client.request_timeout == 2, 'Request timeout should be 2'
    assert proxy_client.connect_timeout == 1, 'Connect timeout should be 1'
    assert proxy_client.max_concurrent_requests == 10, 'Max concurrent should be 10'
    assert proxy_client.queue_timeout == 5, 'Queue timeout should be 5'

def load_test_cases(file_path: str) -> List[Dict]:
    with open(file_path, 'r') as f:
        return json.load(f)

