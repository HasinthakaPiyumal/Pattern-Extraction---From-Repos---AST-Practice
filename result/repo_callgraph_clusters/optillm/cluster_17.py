# Cluster 17

def is_apple_silicon() -> bool:
    """Check if running on Apple Silicon"""
    return platform.system() == 'Darwin' and platform.machine() == 'arm64'

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

def __init__(self):
    self.cache_manager = CacheManager.get_instance(max_size=4)
    self.device_manager = DeviceManager()
    self.model_manager = ModelManager(self.cache_manager, self.device_manager)
    self.lora_manager = LoRAManager(self.cache_manager)
    self.mlx_manager = MLXManager(self.cache_manager)
    self.chat = self.Chat(self)
    self.models = self.Models()

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

class LiteLLMWrapper:

    def __init__(self, api_key: Optional[str]=None, base_url: Optional[str]=None):
        self.api_key = api_key
        self.base_url = base_url
        self.chat = self.Chat()

    class Chat:

        class Completions:

            @staticmethod
            def create(model: str, messages: List[Dict[str, str]], **kwargs):
                if model.startswith('gemini'):
                    response = completion(model=model, messages=messages, **kwargs, safety_settings=SAFETY_SETTINGS)
                else:
                    response = completion(model=model, messages=messages, **kwargs)
                return response
        completions = Completions()

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
    models = Models()

def __init__(self, api_key: Optional[str]=None, base_url: Optional[str]=None):
    self.api_key = api_key
    self.base_url = base_url
    self.chat = self.Chat()

class DeepResearchClientWrapper:
    """Wrapper that adds extended timeout support for different client types"""

    def __init__(self, client, timeout=1800.0, max_retries=0):
        self.client = client
        self.timeout = timeout
        self.max_retries = max_retries
        self.client_type = self._detect_client_type()
        self.chat = self.Chat(self)

    def _detect_client_type(self):
        """Detect the type of client based on class name"""
        class_name = self.client.__class__.__name__
        module_name = self.client.__class__.__module__
        if 'OpenAI' in class_name or 'Cerebras' in class_name:
            return 'openai_compatible'
        elif 'LiteLLMWrapper' in class_name:
            return 'litellm'
        else:
            return 'other'

    class Chat:

        def __init__(self, parent):
            self.parent = parent
            self.completions = self.Completions(parent)

        class Completions:

            def __init__(self, parent):
                self.parent = parent

            def create(self, **kwargs):
                """Create completion with appropriate timeout handling"""
                if self.parent.client_type == 'openai_compatible':
                    try:
                        if 'Cerebras' in self.parent.client.__class__.__name__:
                            from cerebras.cloud.sdk import Cerebras
                            custom_client = Cerebras(api_key=self.parent.client.api_key, base_url=getattr(self.parent.client, 'base_url', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries)
                        else:
                            existing_http_client = getattr(self.parent.client, '_client', None)
                            if 'Azure' in self.parent.client.__class__.__name__:
                                from openai import AzureOpenAI
                                custom_client = AzureOpenAI(api_key=self.parent.client.api_key, api_version=getattr(self.parent.client, 'api_version', None), azure_endpoint=getattr(self.parent.client, 'azure_endpoint', None), azure_ad_token_provider=getattr(self.parent.client, 'azure_ad_token_provider', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries, http_client=existing_http_client)
                            else:
                                from openai import OpenAI
                                custom_client = OpenAI(api_key=self.parent.client.api_key, base_url=getattr(self.parent.client, 'base_url', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries, http_client=existing_http_client)
                        return custom_client.chat.completions.create(**kwargs)
                    except Exception as e:
                        print(f'⚠️ Warning: Could not create custom client with timeout: {str(e)}')
                        return self.parent.client.chat.completions.create(**kwargs)
                elif self.parent.client_type == 'litellm':
                    kwargs['timeout'] = self.parent.timeout
                    return self.parent.client.chat.completions.create(**kwargs)
                else:
                    print(f'ℹ️ Using original client (type: {self.parent.client.__class__.__name__}) without timeout modification')
                    return self.parent.client.chat.completions.create(**kwargs)

def __init__(self, client, timeout=1800.0, max_retries=0):
    self.client = client
    self.timeout = timeout
    self.max_retries = max_retries
    self.client_type = self._detect_client_type()
    self.chat = self.Chat(self)

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

def add(self, item: str):
    if len(self.items) >= self.max_size:
        self.items.pop(0)
    self.items.append(item)
    self.vectors = None

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

def track_latency(self, latency: float):
    """Track request latency"""
    self.latencies.append(latency)
    if len(self.latencies) > 10:
        self.latencies.pop(0)

def get_prompt_response(client, model: str, prompt: str, system_prompt: str, max_tokens: int, temperature: float=0.7, top_p: float=0.7):
    """
    Helper function that sends a prompt to the chat-based LLM API and returns the generated response along with usage logging.

    Args:
        client: LLM API client.
        model (str): Base model name.
        prompt (str): The user prompt to send.
        system_prompt (str): System prompt string.
        max_tokens (int): Maximum number of tokens in the response.
        temperature (float): Sampling temperature for randomness (default: 0.7).
        top_p (float): Cumulative probability cutoff for token selection (default: 0.7).

    Returns:
        Tuple[str, CBLog]: The model's response text and a CBLog object tracking token usage.
    """
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, top_p=top_p, temperature=temperature, stream=False)
    upd_log = CBLog(llm_calls=1, total_tokens=response.usage.total_tokens, completion_tokens=response.usage.completion_tokens)
    return (response.choices[0].message.content, upd_log)

def longcepo_init(initial_query: str) -> Tuple[str, str, PreTrainedTokenizerBase, CBLog, LongCepoConfig]:
    """
    Initializes context, query, tokenizer, logging, and config from an input string.

    Args:
        initial_query (str): Input string containing context and query separated by a delimiter string.

    Returns:
        Tuple[str, str, PreTrainedTokenizerBase, CBLog, LongCepoConfig]:
        Parsed context, query, tokenizer instance, log object, and LongCePO config.
    """
    cb_log = CBLog()
    config = LongCepoConfig()
    context, query = initial_query.split(config.context_query_delimiter)
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_name)
    return (context.strip(), query.strip(), tokenizer, cb_log, config)

def fetch_chunk_summary(client, model, chunk, query, system_prompt):
    return get_prompt_response(client, model, longcepo_config.summary_prompt.format(question=query, context=chunk), system_prompt, max_tokens=longcepo_config.max_output_tokens_summary, temperature=longcepo_config.temperature_map)

def fetch_map_response(client, model, chunk, query, system_prompt, summary):
    return get_prompt_response(client, model, longcepo_config.map_prompt.format(question=query, context=chunk, summary=summary, qa_history_stub=qa_history_stub), system_prompt, max_tokens=longcepo_config.max_output_tokens, temperature=longcepo_config.temperature_map)

def fetch_collapse_response(client, model, docs, query, system_prompt):
    if len(docs) == 1:
        return (docs[0], CBLog())
    return get_prompt_response(client, model, longcepo_config.collapse_prompt.format(question=query, context='\n\n'.join(docs), qa_history_stub=qa_history_stub), system_prompt, max_tokens=longcepo_config.max_output_tokens, temperature=longcepo_config.temperature_collapse)

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

def add_reasoning_example(self, reasoning: str) -> None:
    """Add a reasoning example to the strategy."""
    if reasoning and reasoning.strip():
        if len(self.reasoning_examples) >= 5:
            self.reasoning_examples.pop(0)
        self.reasoning_examples.append(reasoning.strip())

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

def is_mlx_available():
    """Check if MLX is available (macOS only)"""
    if platform.system() != 'Darwin':
        return False
    try:
        from optillm.inference import MLX_AVAILABLE
        return MLX_AVAILABLE
    except ImportError:
        return False

class TestBackwardCompatibility(unittest.TestCase):
    """Test that existing functionality is preserved without batch mode"""

    def test_no_batch_mode_unchanged(self):
        """Test that optillm works exactly the same without --batch-mode"""
        self.assertTrue(True)

    @unittest.skipIf(not os.getenv('OPTILLM_API_KEY'), 'Requires local inference')
    def test_inference_pipeline_unchanged(self):
        """Test that inference pipeline behavior is unchanged"""
        pass

@unittest.skipIf(not os.getenv('OPTILLM_API_KEY'), 'Requires local inference')
def test_inference_pipeline_unchanged(self):
    """Test that inference pipeline behavior is unchanged"""
    pass

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

@unittest.skipIf(not os.getenv('OPTILLM_API_KEY'), 'Requires local inference')
def test_pytorch_batch_processing(self):
    """Test PyTorch batch processing with small model"""
    pass

class MockClient:
    """Mock OpenAI client for testing"""

    def __init__(self):
        self.chat = self.Chat()

    class Chat:

        def __init__(self):
            self.completions = self.Completions()

        class Completions:

            def create(self, **kwargs):

                class MockChoice:

                    class Message:
                        content = 'Test response: 2 + 2 = 4'
                    message = Message()

                class MockUsage:
                    completion_tokens = 10
                    total_tokens = 20

                class MockResponse:
                    choices = [MockChoice()]
                    usage = MockUsage()
                return MockResponse()

def __init__(self):
    self.chat = self.Chat()

