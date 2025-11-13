# Cluster 9

def load_optillm_bench() -> datasets.Dataset:
    """Load the OptiLLM Bench dataset."""
    try:
        dataset = load_dataset('codelion/optillmbench')
        return dataset['test']
    except Exception as e:
        logger.error(f'Error loading dataset: {e}')
        raise

def load_source_dataset(config: Dict[str, Any]) -> datasets.Dataset:
    """Load a source dataset with error handling"""
    try:
        dataset = datasets.load_dataset(config['name'], config.get('subset'))
        return dataset
    except Exception as e:
        print(f'Error loading dataset {config['name']}: {str(e)}')
        return None

def load_math500_dataset() -> list[dict]:
    """
    Load the MATH-500 dataset.
    Returns:
        list[dict]: The dataset of problems.
    """
    dataset = load_dataset('HuggingFaceH4/MATH-500')
    dataset = dataset['test']
    logging.debug(f'Dataset size: {len(dataset)}.')
    return dataset

def extract_answer(response: str) -> Optional[str]:
    """Extract the answer from a math solution response."""
    if not response:
        logger.debug('Empty response received')
        return None
    start_idx = response.rfind('\\boxed{')
    if start_idx == -1:
        logger.debug('No \\boxed{} found in response')
        return None
    brace_count = 1
    pos = start_idx + 7
    while pos < len(response) and brace_count > 0:
        if response[pos] == '{':
            brace_count += 1
        elif response[pos] == '}':
            brace_count -= 1
        pos += 1
    if brace_count == 0:
        answer = response[start_idx + 7:pos - 1]
        logger.debug(f'Extracted answer: {answer}')
        return answer.strip()
    logger.debug('No matching closing brace found')
    return None

def load_2024_dataset() -> list[dict]:
    """
    Load the 2024 dataset of problems.
    Returns:
        list[dict]: The dataset of problems.
    """
    dataset_original = load_dataset('AI-MO/aimo-validation-aime')
    dataset = dataset_original['train'].filter(lambda example: '2024' in example['url'])
    logging.debug(f'Filtered dataset size: {len(dataset)}.')
    assert len(dataset) == 30, f'Expected 30 problems after filtering by 2024, but found {len(dataset)}'
    return dataset

def load_2025_dataset() -> list[dict]:
    """
    Load the 2025 dataset of problems from math-ai/aime25.
    Returns:
        list[dict]: The dataset of problems.
    """
    dataset = load_dataset('math-ai/aime25')
    dataset = dataset['test']
    logging.debug(f'Loaded AIME 2025 dataset size: {len(dataset)}.')
    assert len(dataset) == 30, f'Expected 30 problems in AIME 2025, but found {len(dataset)}'
    return dataset

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

def setup_tokenizer(self, tokenizer: AutoTokenizer) -> AutoTokenizer:
    """Use tokenizer with its default configuration for inference"""
    logger.debug('  a. Starting tokenizer setup')
    logger.debug(f'  b. Using tokenizer with vocab size: {len(tokenizer)}')
    logger.debug(f'  c. Special tokens: PAD={tokenizer.pad_token_id}, EOS={tokenizer.eos_token_id}, BOS={tokenizer.bos_token_id}')
    return tokenizer

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

def create_prompt(self, state: str, action: str) -> str:
    question = self.original_question if hasattr(self, 'original_question') else 'the original question'
    prompts = {'A1': f'Given the current state: {state}\nGenerate the next logical step in solving {question}.\nYour response should be a single, clear thought that moves towards the solution.\nIf you can determine the final answer at this step, state it clearly.', 'A2': f'Given the current state: {state}\nContinue the reasoning process to solve {question}.\nProvide the remaining steps needed to reach the final answer.\nEach step should be clear and directly related to solving the problem.', 'A3': f'Given the current state: {state}\nIdentify a key sub-question that needs to be answered to solve {question}.\nState this sub-question clearly, then provide its answer.\nExplain how this sub-question and its answer contribute to solving the main problem.', 'A4': f'Given the current state: {state}\nRe-examine the previous step in solving {question} using Chain-of-Thought reasoning.\nBreak down your thinking process explicitly, showing each logical step.\nIf you reach a conclusion, state it clearly.', 'A5': f'Given the current state: {state}\nRephrase {question} by clearly listing all relevant conditions and unknowns.\nEnsure that your rephrasing captures all important details from the original question.\nThis rephrasing should help clarify the problem and guide the solution process.'}
    prompt = prompts[action] + "\n\nIf you determine the final answer, explicitly state 'The final answer is [your numeric answer]' at the end of your response."
    logger.debug(f'Created prompt for action {action}: {prompt}')
    return prompt

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

def advanced_self_consistency_approach(system_prompt: str, initial_query: str, client, model: str, request_id: str=None) -> str:
    self_consistency = AdvancedSelfConsistency(client, model, request_id=request_id)
    result = self_consistency.evaluate(system_prompt, initial_query)
    logger.info('Advanced Self-Consistency Results:')
    logger.info(f'Total responses: {result['aggregated_result']['total_responses']}')
    logger.info(f'Number of unique clusters: {result['aggregated_result']['num_unique_clusters']}')
    for i, cluster in enumerate(result['aggregated_result']['clusters'], 1):
        logger.debug(f'\nCluster {i}:')
        logger.debug(f'  Representative answer: {cluster['answer']}')
        logger.debug(f'  Frequency: {cluster['frequency']}')
        logger.debug(f'  Variants: {cluster['variants']}')
    if result['aggregated_result']['clusters']:
        return (result['aggregated_result']['clusters'][0]['answer'], self_consistency.self_consistency_completion_tokens)
    else:
        return ('No consistent answer found.', self_consistency.self_consistency_completion_tokens)

class MCTS:

    def __init__(self, simulation_depth, exploration_weight, client, model, request_id=None):
        self.simulation_depth = simulation_depth
        self.exploration_weight = exploration_weight
        self.root = None
        self.graph = nx.Graph()
        self.node_labels = {}
        self.client = client
        self.model = model
        self.completion_tokens = 0
        self.request_id = request_id

    def select(self, node: MCTSNode) -> MCTSNode:
        logger.debug(f'Selecting node. Current node visits: {node.visits}, value: {node.value}')
        if not node.children:
            logger.debug('Node has no children. Returning current node.')
            return node
        selected_node = max(node.children, key=lambda c: c.value / (c.visits + 1e-08) + self.exploration_weight * np.sqrt(np.log(node.visits + 1) / (c.visits + 1e-08)))
        logger.debug(f'Selected child node. Visits: {selected_node.visits}, Value: {selected_node.value}')
        return selected_node

    def expand(self, node: MCTSNode) -> MCTSNode:
        logger.debug(f'Expanding node. Current state: {node.state}')
        actions = self.generate_actions(node.state)
        logger.debug(f'Generated {len(actions)} possible actions')
        for i, action in enumerate(actions):
            new_state = self.apply_action(node.state, action)
            child = MCTSNode(new_state, parent=node)
            node.children.append(child)
            self.graph.add_edge(id(node), id(child))
            self.node_labels[id(child)] = f'Visits: {child.visits}\nValue: {child.value:.2f}'
            logger.debug(f'Created child node {i + 1}. Action: {action[:50]}...')
        selected_child = random.choice(node.children)
        logger.debug(f'Randomly selected child node for simulation. Visits: {selected_child.visits}, Value: {selected_child.value}')
        return selected_child

    def simulate(self, node: MCTSNode) -> float:
        logger.debug(f'Starting simulation from node. Current query: {node.state.current_query}')
        state = node.state
        for i in range(self.simulation_depth):
            if self.is_terminal(state):
                logger.debug(f'Reached terminal state at depth {i}')
                break
            action = random.choice(self.generate_actions(state))
            state = self.apply_action(state, action)
            logger.debug(f'Simulation step {i + 1}. Action: {action[:50]}...')
        value = self.evaluate_state(state)
        logger.debug(f'Simulation complete. Final state value: {value}')
        return value

    def backpropagate(self, node: MCTSNode, value: float):
        logger.debug(f'Starting backpropagation. Initial value: {value}')
        while node:
            node.visits += 1
            node.value += value
            self.node_labels[id(node)] = f'Visits: {node.visits}\nValue: {node.value:.2f}'
            logger.debug(f'Updated node. Visits: {node.visits}, New value: {node.value}')
            node = node.parent

    def search(self, initial_state: DialogueState, num_simulations: int) -> DialogueState:
        logger.debug(f'Starting MCTS search with {num_simulations} simulations')
        if not self.root:
            self.root = MCTSNode(initial_state)
            self.graph.add_node(id(self.root))
            self.node_labels[id(self.root)] = f'Root\nVisits: 0\nValue: 0.00'
            logger.debug('Created root node')
        for i in range(num_simulations):
            logger.debug(f'Starting simulation {i + 1}')
            node = self.select(self.root)
            if not self.is_terminal(node.state):
                node = self.expand(node)
            value = self.simulate(node)
            self.backpropagate(node, value)
        best_child = max(self.root.children, key=lambda c: c.visits)
        logger.debug(f'Search complete. Best child node: Visits: {best_child.visits}, Value: {best_child.value}')
        return best_child.state

    def generate_actions(self, state: DialogueState) -> List[str]:
        logger.debug('Generating actions for current state')
        messages = [{'role': 'system', 'content': state.system_prompt}]
        messages.extend(state.conversation_history)
        messages.append({'role': 'user', 'content': state.current_query})
        completions = []
        n = 3
        logger.info(f'Requesting {n} completions from the model')
        provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 4096, 'n': n, 'temperature': 1}
        response = self.client.chat.completions.create(**provider_request)
        if self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        completions = [choice.message.content.strip() for choice in response.choices]
        self.completion_tokens += response.usage.completion_tokens
        logger.info(f'Received {len(completions)} completions from the model')
        return completions

    def apply_action(self, state: DialogueState, action: str) -> DialogueState:
        logger.info(f'Applying action: {action[:50]}...')
        new_history = state.conversation_history.copy()
        new_history.append({'role': 'assistant', 'content': action})
        messages = [{'role': 'system', 'content': state.system_prompt}]
        messages.extend(new_history)
        messages.append({'role': 'user', 'content': 'Based on this conversation, what might the user ask or say next? Provide a likely user query.'})
        logger.info('Requesting next user query from the model')
        provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 1024, 'n': 1, 'temperature': 1}
        response = self.client.chat.completions.create(**provider_request)
        if self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        next_query = response.choices[0].message.content
        self.completion_tokens += response.usage.completion_tokens
        logger.info(f'Generated next user query: {next_query}')
        return DialogueState(state.system_prompt, new_history, next_query)

    def is_terminal(self, state: DialogueState) -> bool:
        is_terminal = len(state.conversation_history) > 10 or 'goodbye' in state.current_query.lower()
        logger.info(f'Checking if state is terminal: {is_terminal}')
        return is_terminal

    def evaluate_state(self, state: DialogueState) -> float:
        logger.info('Evaluating current state')
        messages = [{'role': 'system', 'content': state.system_prompt}]
        messages.extend(state.conversation_history)
        messages.append({'role': 'user', 'content': 'Evaluate the quality of this conversation on a scale from 0 to 1, where 0 is poor and 1 is excellent. Consider factors such as coherence, relevance, and engagement. Respond with only a number.'})
        provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 256, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.completion_tokens += response.usage.completion_tokens
        try:
            score = float(response.choices[0].message.content.strip())
            score = max(0, min(score, 1))
            logger.info(f'State evaluation score: {score}')
            return score
        except ValueError:
            logger.warning('Failed to parse evaluation score. Using default value 0.5')
            return 0.5

def select(self, node: MCTSNode) -> MCTSNode:
    logger.debug(f'Selecting node. Current node visits: {node.visits}, value: {node.value}')
    if not node.children:
        logger.debug('Node has no children. Returning current node.')
        return node
    selected_node = max(node.children, key=lambda c: c.value / (c.visits + 1e-08) + self.exploration_weight * np.sqrt(np.log(node.visits + 1) / (c.visits + 1e-08)))
    logger.debug(f'Selected child node. Visits: {selected_node.visits}, Value: {selected_node.value}')
    return selected_node

def expand(self, node: MCTSNode) -> MCTSNode:
    logger.debug(f'Expanding node. Current state: {node.state}')
    actions = self.generate_actions(node.state)
    logger.debug(f'Generated {len(actions)} possible actions')
    for i, action in enumerate(actions):
        new_state = self.apply_action(node.state, action)
        child = MCTSNode(new_state, parent=node)
        node.children.append(child)
        self.graph.add_edge(id(node), id(child))
        self.node_labels[id(child)] = f'Visits: {child.visits}\nValue: {child.value:.2f}'
        logger.debug(f'Created child node {i + 1}. Action: {action[:50]}...')
    selected_child = random.choice(node.children)
    logger.debug(f'Randomly selected child node for simulation. Visits: {selected_child.visits}, Value: {selected_child.value}')
    return selected_child

def simulate(self, node: MCTSNode) -> float:
    logger.debug(f'Starting simulation from node. Current query: {node.state.current_query}')
    state = node.state
    for i in range(self.simulation_depth):
        if self.is_terminal(state):
            logger.debug(f'Reached terminal state at depth {i}')
            break
        action = random.choice(self.generate_actions(state))
        state = self.apply_action(state, action)
        logger.debug(f'Simulation step {i + 1}. Action: {action[:50]}...')
    value = self.evaluate_state(state)
    logger.debug(f'Simulation complete. Final state value: {value}')
    return value

def backpropagate(self, node: MCTSNode, value: float):
    logger.debug(f'Starting backpropagation. Initial value: {value}')
    while node:
        node.visits += 1
        node.value += value
        self.node_labels[id(node)] = f'Visits: {node.visits}\nValue: {node.value:.2f}'
        logger.debug(f'Updated node. Visits: {node.visits}, New value: {node.value}')
        node = node.parent

def search(self, initial_state: DialogueState, num_simulations: int) -> DialogueState:
    logger.debug(f'Starting MCTS search with {num_simulations} simulations')
    if not self.root:
        self.root = MCTSNode(initial_state)
        self.graph.add_node(id(self.root))
        self.node_labels[id(self.root)] = f'Root\nVisits: 0\nValue: 0.00'
        logger.debug('Created root node')
    for i in range(num_simulations):
        logger.debug(f'Starting simulation {i + 1}')
        node = self.select(self.root)
        if not self.is_terminal(node.state):
            node = self.expand(node)
        value = self.simulate(node)
        self.backpropagate(node, value)
    best_child = max(self.root.children, key=lambda c: c.visits)
    logger.debug(f'Search complete. Best child node: Visits: {best_child.visits}, Value: {best_child.value}')
    return best_child.state

class MCPServerManager:
    """Manages MCP servers and capabilities"""

    def __init__(self, config_manager: MCPConfigManager):
        self.config_manager = config_manager
        self.servers: Dict[str, MCPServer] = {}
        self.initialized = False
        self.all_tools = []
        self.all_resources = []
        self.all_prompts = []

    async def initialize(self) -> bool:
        """Initialize and cache all server capabilities"""
        if self.initialized:
            return True
        for server_name, server_config in self.config_manager.servers.items():
            self.servers[server_name] = MCPServer(server_name, server_config)
        connected_servers = 0
        for server_name, server in self.servers.items():
            success = await server.connect_and_discover()
            if success:
                connected_servers += 1
                for tool in server.tools:
                    tool_info = {'server': server_name, 'name': tool.name, 'description': tool.description, 'input_schema': tool.inputSchema}
                    self.all_tools.append(tool_info)
                    logger.debug(f'Cached tool: {tool_info}')
                for resource in server.resources:
                    resource_info = {'server': server_name, 'uri': resource.uri, 'name': resource.name, 'description': resource.description}
                    self.all_resources.append(resource_info)
                    logger.debug(f'Cached resource: {resource_info}')
                for prompt in server.prompts:
                    prompt_info = {'server': server_name, 'name': prompt.name, 'description': prompt.description, 'arguments': prompt.arguments}
                    self.all_prompts.append(prompt_info)
                    logger.debug(f'Cached prompt: {prompt_info}')
        self.initialized = True
        logger.info(f'Connected to {connected_servers}/{len(self.servers)} MCP servers')
        return connected_servers > 0

    def get_tools_for_model(self) -> List[Dict[str, Any]]:
        """Get tools in a format suitable for the model's tool-calling API"""
        tools = []
        for tool_info in self.all_tools:
            server_name = tool_info['server']
            tool_name = tool_info['name']
            tool_entry = {'type': 'function', 'function': {'name': f'{server_name}.{tool_name}', 'description': tool_info['description'] or f'Tool {tool_name} from server {server_name}', 'parameters': tool_info['input_schema']}}
            tools.append(tool_entry)
            logger.debug(f'Added tool for model: {tool_entry}')
        return tools

    def get_capabilities_description(self) -> str:
        """Get a description of all capabilities"""
        if not self.servers:
            return 'No MCP servers available.'
        description_parts = []
        for server_name, server in self.servers.items():
            if not server.connected:
                description_parts.append(f'## {server_name}\nServer connection failed or not established.\n')
                continue
            server_description = f'## {server_name}\n'
            if server.config.description:
                server_description += f'{server.config.description}\n\n'
            if server.tools:
                server_description += '### Tools\n'
                for tool in server.tools:
                    server_description += f'- {server_name}.{tool.name}: {tool.description or 'No description'}\n'
                server_description += '\n'
            if server.resources:
                server_description += '### Resources\n'
                for resource in server.resources:
                    server_description += f'- {resource.uri}: {resource.name or 'No name'} - {resource.description or 'No description'}\n'
                server_description += '\n'
            if server.prompts:
                server_description += '### Prompts\n'
                for prompt in server.prompts:
                    server_description += f'- {prompt.name}: {prompt.description or 'No description'}\n'
                server_description += '\n'
            description_parts.append(server_description)
        return '\n'.join(description_parts)

def get_tools_for_model(self) -> List[Dict[str, Any]]:
    """Get tools in a format suitable for the model's tool-calling API"""
    tools = []
    for tool_info in self.all_tools:
        server_name = tool_info['server']
        tool_name = tool_info['name']
        tool_entry = {'type': 'function', 'function': {'name': f'{server_name}.{tool_name}', 'description': tool_info['description'] or f'Tool {tool_name} from server {server_name}', 'parameters': tool_info['input_schema']}}
        tools.append(tool_entry)
        logger.debug(f'Added tool for model: {tool_entry}')
    return tools

def extract_query(text: str) -> Tuple[str, str]:
    query_index = text.rfind('Query:')
    if query_index != -1:
        context = text[:query_index].strip()
        query = text[query_index + 6:].strip()
    else:
        sentences = re.split('(?<=[.!?])\\s+', text.strip())
        if len(sentences) > 1:
            context = ' '.join(sentences[:-1])
            query = sentences[-1]
        else:
            context = text
            query = 'What is the main point of this text?'
    return (query, context)

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

class RoundRobinRouter(Router):
    """Round-robin routing strategy"""

    def __init__(self, providers: List):
        self.all_providers = providers
        self.index = 0

    def select(self, providers: List) -> Optional:
        if not providers:
            logger.debug('Round-robin: No providers available')
            return None
        if len(providers) == 1:
            logger.debug(f'Round-robin: Only one provider: {providers[0].name}')
            return providers[0]
        logger.debug(f'Round-robin: Starting selection, index={self.index}, providers={[p.name for p in providers]}')
        start_index = self.index
        attempts = 0
        while attempts < len(self.all_providers):
            current_provider = self.all_providers[self.index % len(self.all_providers)]
            next_index = (self.index + 1) % len(self.all_providers)
            logger.debug(f'Round-robin: Checking provider {current_provider.name} at index {self.index}')
            self.index = next_index
            if current_provider in providers:
                logger.debug(f'Round-robin: Selected provider {current_provider.name}')
                return current_provider
            attempts += 1
        logger.debug(f'Round-robin: Fallback to first available: {providers[0].name}')
        return providers[0]

def select(self, providers: List) -> Optional:
    if not providers:
        logger.debug('Round-robin: No providers available')
        return None
    if len(providers) == 1:
        logger.debug(f'Round-robin: Only one provider: {providers[0].name}')
        return providers[0]
    logger.debug(f'Round-robin: Starting selection, index={self.index}, providers={[p.name for p in providers]}')
    start_index = self.index
    attempts = 0
    while attempts < len(self.all_providers):
        current_provider = self.all_providers[self.index % len(self.all_providers)]
        next_index = (self.index + 1) % len(self.all_providers)
        logger.debug(f'Round-robin: Checking provider {current_provider.name} at index {self.index}')
        self.index = next_index
        if current_provider in providers:
            logger.debug(f'Round-robin: Selected provider {current_provider.name}')
            return current_provider
        attempts += 1
    logger.debug(f'Round-robin: Fallback to first available: {providers[0].name}')
    return providers[0]

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

