# Cluster 81

@register_model(config_cls=SiliconFlowConfig, alias=['siliconflow'])
class SiliconFlowLLM(OpenAILLM):

    def init_model(self):
        config: SiliconFlowConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'siliconflow_key', 'output_response']

    def _init_client(self, config: SiliconFlowConfig):
        client = OpenAI(api_key=config.siliconflow_key, base_url='https://api.siliconflow.cn/v1')
        return client

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._completion_cost(self.response)
            else:
                output: str = response.choices[0].message.content
                cost = self._completion_cost(response)
                if output_response:
                    print(output)
            self._update_cost(cost=cost)
        except Exception as e:
            if 'account balance is insufficient' in str(e):
                print('Warning: Account balance insufficient. Please recharge your account.')
                return ''
            raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        model: str = self.config.model
        if model not in model_cost:
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
        if 'token_cost' in model_cost[model]:
            input_cost = input_tokens * model_cost[model]['token_cost'] / 1000000.0
            output_cost = output_tokens * model_cost[model]['token_cost'] / 1000000.0
        else:
            input_cost = input_tokens * model_cost[model]['input_token_cost'] / 1000000.0
            output_cost = output_tokens * model_cost[model]['output_token_cost'] / 1000000.0
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)

    def get_cost(self) -> dict:
        cost_info = {}
        try:
            tokens = self.response.usage
            if tokens.prompt_tokens == -1:
                cost_info['note'] = 'Token counts not available in stream mode'
                cost_info['prompt_tokens'] = 0
                cost_info['completion_tokens'] = 0
                cost_info['total_tokens'] = 0
            else:
                cost_info['prompt_tokens'] = tokens.prompt_tokens
                cost_info['completion_tokens'] = tokens.completion_tokens
                cost_info['total_tokens'] = tokens.total_tokens
        except Exception as e:
            print(f'Error during get_cost of SiliconFlow: {str(e)}')
            cost_info['error'] = str(e)
        return cost_info

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        output = ''
        last_chunk = None
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
            last_chunk = chunk
        if output_response:
            print('')
        if hasattr(last_chunk, 'usage'):
            self.response = last_chunk
        else:
            self.response = type('StreamResponse', (), {'usage': type('StreamUsage', (), {'prompt_tokens': -1, 'completion_tokens': -1, 'total_tokens': -1})})
        return output

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

def _completion_cost(self, response: ChatCompletion) -> Cost:
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
    model: str = self.config.model
    if model not in model_cost:
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
    if 'token_cost' in model_cost[model]:
        input_cost = input_tokens * model_cost[model]['token_cost'] / 1000000.0
        output_cost = output_tokens * model_cost[model]['token_cost'] / 1000000.0
    else:
        input_cost = input_tokens * model_cost[model]['input_token_cost'] / 1000000.0
        output_cost = output_tokens * model_cost[model]['output_token_cost'] / 1000000.0
    return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)

@register_model(config_cls=OpenAILLMConfig, alias=['openai_llm'])
class OpenAILLM(BaseLLM):

    def init_model(self):
        config: OpenAILLMConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key']
        if self.config.model not in get_openai_model_cost():
            raise KeyError(f"'{self.config.model}' is not a valid OpenAI model name!")

    def _init_client(self, config: OpenAILLMConfig):
        client = OpenAI(api_key=config.openai_key)
        return client

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        return completion_params

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        """
        Process stream response and return the complete output.

        Args:
            response: The stream response from OpenAI
            output_response: Whether to print the response in real-time
            
        Returns:
            str: The complete output text
        """
        output = ''
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response, output_response: bool=False) -> str:
        """
        Process async stream response and return the complete output.
        
        Args:
            response (AsyncIterator[ChatCompletionChunk]): The async stream response from OpenAI
            output_response (bool): Whether to print the response in real-time
            
            
        Returns:
            str: The complete output text
        """
        output = ''
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
        output = response.choices[0].message.content
        if output_response:
            print(output)
        return output

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            isolated_client = self._init_client(self.config)
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: isolated_client.chat.completions.create(messages=messages, **completion_params))
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of OpenAILLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _stream_cost(self, messages: List[dict], output: str) -> Cost:
        model: str = self.config.model
        input_tokens = token_counter(model=model, messages=messages)
        output_tokens = token_counter(model=model, text=output)
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        input_cost, output_cost = cost_per_token(model=self.config.model, prompt_tokens=input_tokens, completion_tokens=output_tokens)
        cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
        return cost

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

def _completion_cost(self, response: ChatCompletion) -> Cost:
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

def _stream_cost(self, messages: List[dict], output: str) -> Cost:
    model: str = self.config.model
    input_tokens = token_counter(model=model, messages=messages)
    output_tokens = token_counter(model=model, text=output)
    return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
    input_cost, output_cost = cost_per_token(model=self.config.model, prompt_tokens=input_tokens, completion_tokens=output_tokens)
    cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
    return cost

@register_model(config_cls=AliyunLLMConfig, alias=['aliyun_llm'])
class AliyunLLM(BaseLLM):

    def init_model(self):
        """
        Initialize the DashScope Generation client.
        """
        config: AliyunLLMConfig = self.config
        if not config.aliyun_api_key:
            raise ValueError('Aliyun API key is required. You should set `aliyun_api_key` in AliyunLLMConfig')
        os.environ['DASHSCOPE_API_KEY'] = config.aliyun_api_key
        dashscope.api_key = config.aliyun_api_key
        self._client = Generation()
        self._default_ignore_fields = ['llm_type', 'output_response', 'aliyun_api_key', 'aliyun_access_key_id', 'aliyun_access_key_secret', 'model_name']

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        """
        Format messages for the Aliyun model.
        
        Args:
            prompts (List[str]): List of user prompts.
            system_messages (Optional[List[str]]): Optional list of system messages.
            
        Returns:
            List[List[dict]]: Formatted messages for the model.
        """
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        """
        Update completion parameters with new values.
        
        Args:
            params1 (dict): Base parameters.
            params2 (dict): New parameters to update with.
            
        Returns:
            dict: Updated parameters.
        """
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        """
        Get completion parameters for the model.
        
        Returns:
            dict: Parameters for model completion.
        """
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        completion_params['model'] = self.config.model
        return completion_params

    def get_stream_output(self, response: Any, output_response: bool=True) -> str:
        """
        Process streaming response from the model.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        output = ''
        try:
            for chunk in response:
                if not hasattr(chunk, 'output') or chunk.output is None:
                    error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                    raise ValueError(f'Model stream chunk error: {error_msg}')
                if hasattr(chunk.output, 'text'):
                    content = chunk.output.text
                elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                    content = chunk.output.choices[0].message.content
                else:
                    continue
                if content:
                    if output_response:
                        print(content, end='', flush=True)
                    output += content
        except Exception as e:
            print(f'Error processing stream: {str(e)}')
            if not output:
                raise RuntimeError(f'Failed to process stream response: {str(e)}')
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response: Any, output_response: bool=False) -> str:
        """
        Process streaming response asynchronously.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        output = ''
        try:
            async for chunk in response:
                if not hasattr(chunk, 'output') or chunk.output is None:
                    error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                    raise ValueError(f'Model stream chunk error: {error_msg}')
                if hasattr(chunk.output, 'text'):
                    content = chunk.output.text
                elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                    content = chunk.output.choices[0].message.content
                else:
                    continue
                if content:
                    if output_response:
                        print(content, end='', flush=True)
                    output += content
        except Exception as e:
            print(f'Error processing async stream: {str(e)}')
            if not output:
                raise RuntimeError(f'Failed to process async stream response: {str(e)}')
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: Any, output_response: bool=True) -> str:
        """
        Process non-streaming response from the model.
        
        Args:
            response: The response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        try:
            if not hasattr(response, 'output') or response.output is None:
                error_msg = getattr(response, 'message', 'Invalid response format from model')
                raise ValueError(f'Model response error: {error_msg}')
            if hasattr(response.output, 'text'):
                output = response.output.text
            elif hasattr(response.output, 'choices') and response.output.choices:
                output = response.output.choices[0].message.content
            else:
                raise ValueError('Unexpected response format')
            if output_response:
                print(output)
            return output
        except Exception as e:
            raise RuntimeError(f'Error processing completion response: {str(e)}')

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response from the model.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for generation.
            
        Returns:
            str: The generated response.
        """
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.call(messages=messages, **completion_params)
            if response is None:
                raise RuntimeError('Received empty response from model')
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(response)
            else:
                output = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
            return output
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of AliyunLLM: {str(e)}')

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """
        Generate responses for a batch of messages.
        
        Args:
            batch_messages (List[List[dict]]): List of conversation histories.
            **kwargs: Additional parameters for generation.
            
        Returns:
            List[str]: List of generated responses.
        """
        if not isinstance(batch_messages, list) or not batch_messages:
            raise ValueError('batch_messages must be a non-empty list of message lists')
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """
        Asynchronously generate a single response.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for the generation.
            
        Returns:
            str: The generated response.
        """
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self._client.call(messages=messages, **completion_params))
            if stream:
                output = await self.get_stream_output_async(response, output_response=output_response)
                cost = self._stream_cost(response)
            else:
                output = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
            return output
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of AliyunLLM: {str(e)}')

    def _completion_cost(self, response: Any) -> Cost:
        """cost"""
        try:
            if not response:
                return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                elif hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                elif hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
            if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
                if hasattr(response.output, 'text'):
                    output_tokens = len(response.output.text.split()) * 1.3
                elif hasattr(response.output, 'choices') and response.output.choices:
                    output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
            total_cost = self._estimate_cost(input_tokens, output_tokens)
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
        except Exception as e:
            logger.warning(f'Error computing completion cost: {str(e)}')
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

    def _stream_cost(self, response: Any) -> Cost:
        """cost"""
        try:
            if not response:
                return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                elif hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                elif hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
            if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
                if hasattr(response.output, 'text'):
                    output_tokens = len(response.output.text.split()) * 1.3
                elif hasattr(response.output, 'choices') and response.output.choices:
                    output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
            total_cost = self._estimate_cost(input_tokens, output_tokens)
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
        except Exception as e:
            logger.warning(f'Error computing stream cost: {str(e)}')
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """cost
        
        """
        model = self.config.model.lower()
        if 'turbo' in model:
            input_cost = input_tokens / 1000 * 0.0005
            output_cost = output_tokens / 1000 * 0.001
        elif 'max' in model:
            input_cost = input_tokens / 1000 * 0.002
            output_cost = output_tokens / 1000 * 0.004
        else:
            input_cost = input_tokens / 1000 * 0.001
            output_cost = output_tokens / 1000 * 0.002
        return input_cost + output_cost

    def _update_cost(self, cost: Cost):
        """
        Update the cost manager with the new cost.
        
        Args:
            cost (Cost): The cost to update.
        """
        try:
            cost_manager.update_cost(cost=cost, model=self.config.model)
        except Exception as e:
            logger.warning(f'Error updating cost: {str(e)}')

def _completion_cost(self, response: Any) -> Cost:
    """cost"""
    try:
        if not response:
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'input_tokens'):
                input_tokens = usage.input_tokens
            elif hasattr(usage, 'prompt_tokens'):
                input_tokens = usage.prompt_tokens
            if hasattr(usage, 'output_tokens'):
                output_tokens = usage.output_tokens
            elif hasattr(usage, 'completion_tokens'):
                output_tokens = usage.completion_tokens
        if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
            if hasattr(response.output, 'text'):
                output_tokens = len(response.output.text.split()) * 1.3
            elif hasattr(response.output, 'choices') and response.output.choices:
                output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
        total_cost = self._estimate_cost(input_tokens, output_tokens)
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
    except Exception as e:
        logger.warning(f'Error computing completion cost: {str(e)}')
        return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

def _stream_cost(self, response: Any) -> Cost:
    """cost"""
    try:
        if not response:
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'input_tokens'):
                input_tokens = usage.input_tokens
            elif hasattr(usage, 'prompt_tokens'):
                input_tokens = usage.prompt_tokens
            if hasattr(usage, 'output_tokens'):
                output_tokens = usage.output_tokens
            elif hasattr(usage, 'completion_tokens'):
                output_tokens = usage.completion_tokens
        if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
            if hasattr(response.output, 'text'):
                output_tokens = len(response.output.text.split()) * 1.3
            elif hasattr(response.output, 'choices') and response.output.choices:
                output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
        total_cost = self._estimate_cost(input_tokens, output_tokens)
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
    except Exception as e:
        logger.warning(f'Error computing stream cost: {str(e)}')
        return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

@register_model(config_cls=OpenRouterConfig, alias=['openrouter'])
class OpenRouterLLM(BaseLLM):

    def init_model(self):
        config: OpenRouterConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'openrouter_key', 'openrouter_base', 'openrouter_model_base', 'output_response']

    def _init_client(self, config: OpenRouterConfig):
        client = OpenAI(api_key=config.openrouter_key, base_url=config.openrouter_base)
        return client

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        return completion_params

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        output = ''
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response, output_response: bool=False) -> str:
        output = ''
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
        output = response.choices[0].message.content
        if output_response:
            print(output)
        return output

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of OpenRouterLLM: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            isolated_client = self._init_client(self.config)
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: isolated_client.chat.completions.create(messages=messages, **completion_params))
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of OpenRouterLLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _stream_cost(self, messages: List[dict], output: str) -> Cost:
        model: str = self.config.model
        input_tokens = token_counter(model=model, messages=messages)
        output_tokens = token_counter(model=model, text=output)
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        input_cost_per_token, output_cost_per_token = self._get_cost()
        input_cost = input_tokens * input_cost_per_token
        output_cost = output_tokens * output_cost_per_token
        cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
        return cost

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

    def _get_cost(self):
        url = self.config.openrouter_model_base
        response = requests.get(url)
        data = response.json()
        for model in data['data']:
            if model['id'] == self.config.model:
                pricing = model.get('pricing', {})
                input_cost = float(pricing.get('prompt', 0))
                output_cost = float(pricing.get('completion', 0))
                return (input_cost, output_cost)
        return (0, 0)

def _completion_cost(self, response: ChatCompletion) -> Cost:
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

def _stream_cost(self, messages: List[dict], output: str) -> Cost:
    model: str = self.config.model
    input_tokens = token_counter(model=model, messages=messages)
    output_tokens = token_counter(model=model, text=output)
    return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
    input_cost_per_token, output_cost_per_token = self._get_cost()
    input_cost = input_tokens * input_cost_per_token
    output_cost = output_tokens * output_cost_per_token
    cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
    return cost

@register_model(config_cls=LiteLLMConfig, alias=['litellm'])
class LiteLLM(OpenAILLM):

    def init_model(self):
        """
        Initialize the model based on the configuration.
        """
        if self.config.llm_type != 'LiteLLM':
            raise ValueError("llm_type must be 'LiteLLM'")
        self.model = self.config.model
        self.api_base = self.config.api_base
        self.api_key = self.config.api_key
        company = infer_litellm_company_from_model(self.model)
        if self.config.is_local or company == 'local':
            if not self.api_base:
                raise ValueError('api_base is required for local models in LiteLLMConfig')
            litellm.api_base = self.api_base
            litellm.api_key = self.api_key
        elif company == 'openai':
            if not self.config.openai_key:
                raise ValueError('OpenAI API key is required for OpenAI models. You should set `openai_key` in LiteLLMConfig')
            os.environ['OPENAI_API_KEY'] = self.config.openai_key
        elif company == 'azure':
            if not self.config.azure_key or not self.config.azure_endpoint:
                raise ValueError('Azure OpenAI key and endpoint are required for Azure models. You should set `azure_key` and `azure_endpoint` in LiteLLMConfig')
            os.environ['AZURE_API_KEY'] = self.config.azure_key
            os.environ['AZURE_API_BASE'] = self.config.azure_endpoint
            if self.config.api_version:
                os.environ['AZURE_API_VERSION'] = self.config.api_version
        elif company == 'deepseek':
            if not self.config.deepseek_key:
                raise ValueError('DeepSeek API key is required for DeepSeek models. You should set `deepseek_key` in LiteLLMConfig')
            os.environ['DEEPSEEK_API_KEY'] = self.config.deepseek_key
        elif company == 'anthropic':
            if not self.config.anthropic_key:
                raise ValueError('Anthropic API key is required for Anthropic models. You should set `anthropic_key` in LiteLLMConfig')
            os.environ['ANTHROPIC_API_KEY'] = self.config.anthropic_key
        elif company == 'gemini':
            if not self.config.gemini_key:
                raise ValueError('Gemini API key is required for Gemini models. You should set `gemini_key` in LiteLLMConfig')
            os.environ['GEMINI_API_KEY'] = self.config.gemini_key
        elif company == 'meta_llama':
            if not self.config.meta_llama_key:
                raise ValueError('Meta Llama API key is required for Meta Llama models. You should set `meta_llama_key` in LiteLLMConfig')
            os.environ['LLAMA_API_KEY'] = self.config.meta_llama_key
        elif company == 'openrouter':
            if not self.config.openrouter_key:
                raise ValueError('OpenRouter API key is required for OpenRouter models. You should set `openrouter_key` in LiteLLMConfig. You can also set `openrouter_base` in LiteLLMConfig to use a custom base URL [optional]')
            os.environ['OPENROUTER_API_KEY'] = self.config.openrouter_key
            os.environ['OPENROUTER_API_BASE'] = self.config.openrouter_base
        elif company == 'perplexity':
            if not self.config.perplexity_key:
                raise ValueError('Perplexity API key is required for Perplexity models. You should set `perplexity_key` in LiteLLMConfig')
            os.environ['PERPLEXITYAI_API_KEY'] = self.config.perplexity_key
        elif company == 'groq':
            if not self.config.groq_key:
                raise ValueError('Groq API key is required for Groq models. You should set `groq_key` in LiteLLMConfig')
            os.environ['GROQ_API_KEY'] = self.config.groq_key
        else:
            raise ValueError(f'Unsupported company: {company}')
        self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key', 'api_base', 'is_local', 'azure_endpoint', 'azure_key', 'api_version', 'api_key']

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        if self.config.is_local:
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
        return super()._compute_cost(input_tokens, output_tokens)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response using the completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            company = infer_litellm_company_from_model(self.model)
            if self.config.is_local or company == 'local':
                completion_params['api_base'] = self.api_base
            elif company == 'azure':
                completion_params['api_base'] = self.config.azure_endpoint
                completion_params['api_version'] = self.config.api_version
                completion_params['api_key'] = self.config.azure_key
            response = completion(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response=response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """
        Generate responses for a batch of messages.

        Args: 
            batch_messages (List[List[dict]]): A list of message lists, where each sublist represents a conversation.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            List[str]: A list of responses for each conversation.
        """
        results = []
        for messages in batch_messages:
            response = self.single_generate(messages, **kwargs)
            results.append(response)
        return results

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response using the async completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            company = infer_litellm_company_from_model(self.model)
            if self.config.is_local or company == 'local':
                completion_params['api_base'] = self.api_base
            elif company == 'azure':
                completion_params['api_base'] = self.config.azure_endpoint
                completion_params['api_version'] = self.config.api_version
                completion_params['api_key'] = self.config.azure_key
            response = await acompletion(messages=messages, **completion_params)
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response=response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async: {str(e)}')
        return output

def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
    if self.config.is_local:
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
    return super()._compute_cost(input_tokens, output_tokens)

