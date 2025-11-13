# Cluster 18

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

class ModelManager:

    def __init__(self, cache_manager: CacheManager, device_manager: DeviceManager):
        self.cache_manager = cache_manager
        self.device_manager = device_manager

    def quantize_model(self, model):
        """Quantize model to 4-bit precision using bitsandbytes"""

        def _replace_linear_layers(module):
            for name, child in module.named_children():
                if isinstance(child, torch.nn.Linear):
                    setattr(module, name, bnb.nn.Linear4bit(child.in_features, child.out_features, bias=child.bias is not None, compute_dtype=torch.float16))
                else:
                    _replace_linear_layers(child)
        _replace_linear_layers(model)
        return model

    def load_base_model(self, model_id: str, quantize: bool=True) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:

        def _load_model():
            logger.info(f'Loading base model: {model_id}')
            device = self.device_manager.get_optimal_device()
            logger.info(f'Using device: {device}')
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
            model_kwargs = {'trust_remote_code': True, 'device_map': 'auto' if 'cuda' in device else device}
            if 'cuda' in device:
                compute_capability = torch.cuda.get_device_capability(0)
                if compute_capability[0] >= 8:
                    model_kwargs['torch_dtype'] = torch.bfloat16
                elif compute_capability[0] >= 7:
                    model_kwargs['torch_dtype'] = torch.float16
                try:
                    import flash_attn
                    has_flash_attn = True
                    logger.info('Flash Attention 2 is available')
                    model_kwargs['attn_implementation'] = 'flash_attention_2'
                except ImportError:
                    has_flash_attn = False
                    logger.info('Flash Attention 2 is not installed - falling back to default attention')
            elif 'mps' in device:
                if 'gemma' in model_id.lower():
                    model_kwargs['torch_dtype'] = torch.float32
                    logger.info('Using MPS device with float32 for Gemma model (float16 causes NaN)')
                else:
                    model_kwargs['torch_dtype'] = torch.float16
                    logger.info('Using MPS device with float16 precision')
            elif hasattr(torch.cpu, 'has_fp16') and torch.cpu.has_fp16:
                model_kwargs['torch_dtype'] = torch.float16
                logger.info('Using CPU device with float16 precision')
            else:
                model_kwargs['torch_dtype'] = torch.float32
                logger.info('Using CPU device with float32 precision - FP16 not supported')
            try:
                model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
            except Exception as e:
                if 'attn_implementation' in model_kwargs:
                    logger.warning(f'Failed to load model with Flash Attention: {e}')
                    logger.info('Retrying without Flash Attention...')
                    model_kwargs.pop('attn_implementation')
                    model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
                elif model_kwargs['torch_dtype'] == torch.float16:
                    logger.warning(f'Failed to load model with FP16: {e}')
                    logger.info('Falling back to FP32...')
                    model_kwargs['torch_dtype'] = torch.float32
                    model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
            logger.info(f'Model loaded successfully with dtype: {model_kwargs['torch_dtype']}')
            if quantize and 'cuda' in device and (model_kwargs['torch_dtype'] == torch.float32):
                model = self.quantize_model(model)
            return (model, tokenizer)
        return self.cache_manager.get_or_load_model(model_id, _load_model)

def load_base_model(self, model_id: str, quantize: bool=True) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:

    def _load_model():
        logger.info(f'Loading base model: {model_id}')
        device = self.device_manager.get_optimal_device()
        logger.info(f'Using device: {device}')
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
        model_kwargs = {'trust_remote_code': True, 'device_map': 'auto' if 'cuda' in device else device}
        if 'cuda' in device:
            compute_capability = torch.cuda.get_device_capability(0)
            if compute_capability[0] >= 8:
                model_kwargs['torch_dtype'] = torch.bfloat16
            elif compute_capability[0] >= 7:
                model_kwargs['torch_dtype'] = torch.float16
            try:
                import flash_attn
                has_flash_attn = True
                logger.info('Flash Attention 2 is available')
                model_kwargs['attn_implementation'] = 'flash_attention_2'
            except ImportError:
                has_flash_attn = False
                logger.info('Flash Attention 2 is not installed - falling back to default attention')
        elif 'mps' in device:
            if 'gemma' in model_id.lower():
                model_kwargs['torch_dtype'] = torch.float32
                logger.info('Using MPS device with float32 for Gemma model (float16 causes NaN)')
            else:
                model_kwargs['torch_dtype'] = torch.float16
                logger.info('Using MPS device with float16 precision')
        elif hasattr(torch.cpu, 'has_fp16') and torch.cpu.has_fp16:
            model_kwargs['torch_dtype'] = torch.float16
            logger.info('Using CPU device with float16 precision')
        else:
            model_kwargs['torch_dtype'] = torch.float32
            logger.info('Using CPU device with float32 precision - FP16 not supported')
        try:
            model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
        except Exception as e:
            if 'attn_implementation' in model_kwargs:
                logger.warning(f'Failed to load model with Flash Attention: {e}')
                logger.info('Retrying without Flash Attention...')
                model_kwargs.pop('attn_implementation')
                model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
            elif model_kwargs['torch_dtype'] == torch.float16:
                logger.warning(f'Failed to load model with FP16: {e}')
                logger.info('Falling back to FP32...')
                model_kwargs['torch_dtype'] = torch.float32
                model = AutoModelForCausalLM.from_pretrained(model_id, token=os.getenv('HF_TOKEN'), **model_kwargs)
        logger.info(f'Model loaded successfully with dtype: {model_kwargs['torch_dtype']}')
        if quantize and 'cuda' in device and (model_kwargs['torch_dtype'] == torch.float32):
            model = self.quantize_model(model)
        return (model, tokenizer)
    return self.cache_manager.get_or_load_model(model_id, _load_model)

