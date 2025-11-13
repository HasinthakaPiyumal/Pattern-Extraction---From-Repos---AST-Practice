# Cluster 24

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

