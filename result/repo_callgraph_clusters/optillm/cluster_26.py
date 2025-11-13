# Cluster 26

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

def __init__(self, client: 'InferenceClient'):
    self.client = client
    self.completions = self.Completions(client)

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

def __init__(self, parent):
    self.parent = parent
    self.completions = self.Completions(parent)

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
    self.completions = self.Completions()

