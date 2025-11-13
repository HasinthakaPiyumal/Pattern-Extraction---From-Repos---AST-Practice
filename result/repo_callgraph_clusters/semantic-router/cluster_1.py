# Cluster 1

class Route(BaseModel):
    """A route for the semantic router.

    :param name: The name of the route.
    :type name: str
    :param utterances: The utterances of the route.
    :type utterances: Union[List[str], List[Any]]
    :param description: The description of the route.
    :type description: Optional[str]
    :param function_schemas: The function schemas of the route.
    :type function_schemas: Optional[List[Dict[str, Any]]]
    :param llm: The LLM to use.
    :type llm: Optional[BaseLLM]
    :param score_threshold: The score threshold of the route.
    :type score_threshold: Optional[float]
    :param metadata: The metadata of the route.
    :type metadata: Optional[Dict[str, Any]]
    """
    name: str
    utterances: Union[List[str], List[Any]]
    description: Optional[str] = None
    function_schemas: Optional[List[Dict[str, Any]]] = None
    llm: Optional[BaseLLM] = None
    score_threshold: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __call__(self, query: Optional[str]=None) -> RouteChoice:
        """Call the route. If dynamic routes have been provided the query must have been
        provided and the llm attribute must be set.

        :param query: The query to pass to the route.
        :type query: Optional[str]
        :return: The route choice.
        :rtype: RouteChoice
        """
        if self.function_schemas:
            if not self.llm:
                raise ValueError('LLM is required for dynamic routes. Please ensure the `llm` attribute is set.')
            elif query is None:
                raise ValueError('Query is required for dynamic routes. Please ensure the `query` argument is passed.')
            try:
                extracted_inputs = self.llm.extract_function_inputs(query=query, function_schemas=self.function_schemas)
                func_call = extracted_inputs
            except Exception:
                logger.error('Error extracting function inputs', exc_info=True)
                func_call = None
        else:
            func_call = None
        return RouteChoice(name=self.name, function_call=func_call)

    async def acall(self, query: Optional[str]=None) -> RouteChoice:
        """Asynchronous call the route. If dynamic routes have been provided the query
        must have been provided and the llm attribute must be set.

        :param query: The query to pass to the route.
        :type query: Optional[str]
        :return: The route choice.
        :rtype: RouteChoice
        """
        if self.function_schemas:
            if not self.llm:
                raise ValueError('LLM is required for dynamic routes. Please ensure the `llm` attribute is set.')
            elif query is None:
                raise ValueError('Query is required for dynamic routes. Please ensure the `query` argument is passed.')
            try:
                extracted_inputs = await self.llm.async_extract_function_inputs(query=query, function_schemas=self.function_schemas)
                func_call = extracted_inputs
            except Exception:
                logger.error('Error extracting function inputs', exc_info=True)
                func_call = None
        else:
            func_call = None
        return RouteChoice(name=self.name, function_call=func_call)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the route to a dictionary.

        :return: The dictionary representation of the route.
        :rtype: Dict[str, Any]
        """
        data = self.dict()
        if self.llm is not None:
            data['llm'] = {'module': self.llm.__module__, 'class': self.llm.__class__.__name__, 'model': self.llm.name}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create a Route object from a dictionary.

        :param data: The dictionary to create the route from.
        :type data: Dict[str, Any]
        :return: The created route.
        :rtype: Route
        """
        return cls(**data)

    @classmethod
    def from_dynamic_route(cls, llm: BaseLLM, entities: List[Union[BaseModel, Callable]], route_name: str):
        """Generate a dynamic Route object from a list of functions or Pydantic models
        using an LLM.

        :param llm: The LLM to use.
        :type llm: BaseLLM
        :param entities: The entities to use.
        :type entities: List[Union[BaseModel, Callable]]
        :param route_name: The name of the route.
        """
        schemas = function_call.get_schema_list(items=entities)
        dynamic_route = cls._generate_dynamic_route(llm=llm, function_schemas=schemas, route_name=route_name)
        dynamic_route.function_schemas = schemas
        return dynamic_route

    @classmethod
    def _parse_route_config(cls, config: str) -> str:
        """Parse the route config from the LLM output using regex. Expects the output
        content to be wrapped in <config></config> tags.

        :param config: The LLM output.
        :type config: str
        :return: The parsed route config.
        :rtype: str
        """
        config_pattern = '<config>(.*?)</config>'
        match = re.search(config_pattern, config, re.DOTALL)
        if match:
            config_content = match.group(1).strip()
            return config_content
        else:
            raise ValueError('No <config></config> tags found in the output.')

    @classmethod
    def _generate_dynamic_route(cls, llm: BaseLLM, function_schemas: List[Dict[str, Any]], route_name: str):
        """Generate a dynamic Route object from a list of function schemas using an LLM.

        :param llm: The LLM to use.
        :type llm: BaseLLM
        :param function_schemas: The function schemas to use.
        :type function_schemas: List[Dict[str, Any]]
        :param route_name: The name of the route.
        """
        formatted_schemas = '\n'.join([json.dumps(schema, indent=4) for schema in function_schemas])
        prompt = f'\n        You are tasked to generate a single JSON configuration for multiple function schemas. \n        Each function schema should contribute five example utterances. \n        Please follow the template below, no other tokens allowed:\n\n        <config>\n        {{\n            "name": "{route_name}",\n            "utterances": [\n                "<example_utterance_1>",\n                "<example_utterance_2>",\n                "<example_utterance_3>",\n                "<example_utterance_4>",\n                "<example_utterance_5>"]\n        }}\n        </config>\n\n        Only include the "name" and "utterances" keys in your answer.\n        The "name" should match the provided route name and the "utterances"\n        should comprise a list of 5 example phrases for each function schema that could be used to invoke\n        the functions. Use real values instead of placeholders.\n\n        Input schemas:\n        {formatted_schemas}\n        '
        llm_input = [Message(role='user', content=prompt)]
        output = llm(llm_input)
        if not output:
            raise Exception('No output generated for dynamic route')
        route_config = cls._parse_route_config(config=output)
        if is_valid(route_config):
            route_config_dict = json.loads(route_config)
            route_config_dict['llm'] = llm
            return Route.from_dict(route_config_dict)
        raise Exception('No config generated')

def __call__(self, query: Optional[str]=None) -> RouteChoice:
    """Call the route. If dynamic routes have been provided the query must have been
        provided and the llm attribute must be set.

        :param query: The query to pass to the route.
        :type query: Optional[str]
        :return: The route choice.
        :rtype: RouteChoice
        """
    if self.function_schemas:
        if not self.llm:
            raise ValueError('LLM is required for dynamic routes. Please ensure the `llm` attribute is set.')
        elif query is None:
            raise ValueError('Query is required for dynamic routes. Please ensure the `query` argument is passed.')
        try:
            extracted_inputs = self.llm.extract_function_inputs(query=query, function_schemas=self.function_schemas)
            func_call = extracted_inputs
        except Exception:
            logger.error('Error extracting function inputs', exc_info=True)
            func_call = None
    else:
        func_call = None
    return RouteChoice(name=self.name, function_call=func_call)

def to_dict(self) -> Dict[str, Any]:
    """Convert the route to a dictionary.

        :return: The dictionary representation of the route.
        :rtype: Dict[str, Any]
        """
    data = self.dict()
    if self.llm is not None:
        data['llm'] = {'module': self.llm.__module__, 'class': self.llm.__class__.__name__, 'model': self.llm.name}
    return data

class BaseLLM(BaseModel):
    """Base class for LLMs typically used by dynamic routes.

    This class provides a base implementation for LLMs. It defines the common
    configuration and methods for all LLM classes.
    """
    name: str
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = None
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, name: str, **kwargs):
        """Initialize the BaseLLM.

        :param name: The name of the LLM.
        :type name: str
        :param **kwargs: Additional keyword arguments for the LLM.
        :type **kwargs: dict
        """
        super().__init__(name=name, **kwargs)

    def __call__(self, messages: List[Message]) -> Optional[str]:
        """Call the LLM.

        Must be implemented by subclasses.

        :param messages: The messages to pass to the LLM.
        :type messages: List[Message]
        :return: The response from the LLM.
        :rtype: Optional[str]
        """
        raise NotImplementedError('Subclasses must implement this method')

    def _check_for_mandatory_inputs(self, inputs: dict[str, Any], mandatory_params: List[str]) -> bool:
        """Check for mandatory parameters in inputs.

        :param inputs: The inputs to check for mandatory parameters.
        :type inputs: dict[str, Any]
        :param mandatory_params: The mandatory parameters to check for.
        :type mandatory_params: List[str]
        :return: True if all mandatory parameters are present, False otherwise.
        :rtype: bool
        """
        for name in mandatory_params:
            if name not in inputs:
                logger.error(f'Mandatory input {name} missing from query')
                return False
        return True

    def _check_for_extra_inputs(self, inputs: dict[str, Any], all_params: List[str]) -> bool:
        """Check for extra parameters not defined in the signature.

        :param inputs: The inputs to check for extra parameters.
        :type inputs: dict[str, Any]
        :param all_params: The all parameters to check for.
        :type all_params: List[str]
        :return: True if all extra parameters are present, False otherwise.
        :rtype: bool
        """
        input_keys = set(inputs.keys())
        param_keys = set(all_params)
        if not input_keys.issubset(param_keys):
            extra_keys = input_keys - param_keys
            logger.error(f'Extra inputs provided that are not in the signature: {extra_keys}')
            return False
        return True

    def _is_valid_inputs(self, inputs: List[Dict[str, Any]], function_schemas: List[Dict[str, Any]]) -> bool:
        """Determine if the functions chosen by the LLM exist within the function_schemas,
        and if the input arguments are valid for those functions.

        :param inputs: The inputs to check for validity.
        :type inputs: List[Dict[str, Any]]
        :param function_schemas: The function schemas to check against.
        :type function_schemas: List[Dict[str, Any]]
        :return: True if the inputs are valid, False otherwise.
        :rtype: bool
        """
        try:
            if len(inputs) != 1:
                logger.error('Only one set of function inputs is allowed.')
                return False
            if len(function_schemas) != 1:
                logger.error('Only one function schema is allowed.')
                return False
            if not self._validate_single_function_inputs(inputs[0], function_schemas[0]):
                return False
            return True
        except Exception as e:
            logger.error(f'Input validation error: {str(e)}')
            return False

    def _validate_single_function_inputs(self, inputs: Dict[str, Any], function_schema: Dict[str, Any]) -> bool:
        """Validate the extracted inputs against the function schema.

        :param inputs: The inputs to validate.
        :type inputs: Dict[str, Any]
        :param function_schema: The function schema to validate against.
        :type function_schema: Dict[str, Any]
        :return: True if the inputs are valid, False otherwise.
        :rtype: bool
        """
        try:
            signature = function_schema['signature']
            param_info = [param.strip() for param in signature[1:-1].split(',')]
            mandatory_params = []
            all_params = []
            for info in param_info:
                parts = info.split('=')
                name_type_pair = parts[0].strip()
                if ':' in name_type_pair:
                    name, _ = name_type_pair.split(':')
                else:
                    name = name_type_pair
                all_params.append(name)
                if len(parts) == 1:
                    mandatory_params.append(name)
            if not self._check_for_mandatory_inputs(inputs, mandatory_params):
                return False
            if not self._check_for_extra_inputs(inputs, all_params):
                return False
            return True
        except Exception as e:
            logger.error(f'Single input validation error: {str(e)}')
            return False

    def _extract_parameter_info(self, signature: str) -> tuple[List[str], List[str]]:
        """Extract parameter names and types from the function signature.

        :param signature: The function signature to extract parameter names and types from.
        :type signature: str
        :return: A tuple of parameter names and types.
        :rtype: tuple[List[str], List[str]]
        """
        param_info = [param.strip() for param in signature[1:-1].split(',')]
        param_names = [info.split(':')[0].strip() for info in param_info]
        param_types = [info.split(':')[1].strip().split('=')[0].strip() for info in param_info]
        return (param_names, param_types)

    def extract_function_inputs(self, query: str, function_schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract the function inputs from the query.

        :param query: The query to extract the function inputs from.
        :type query: str
        :param function_schemas: The function schemas to extract the function inputs from.
        :type function_schemas: List[Dict[str, Any]]
        :return: The function inputs.
        :rtype: List[Dict[str, Any]]
        """
        logger.info('Extracting function input...')
        prompt = f"""\nYou are an accurate and reliable computer program that only outputs valid JSON. \nYour task is to output JSON representing the input arguments of a Python function.\n\nThis is the Python function's schema:\n\n### FUNCTION_SCHEMAS Start ###\n\t{function_schemas}\n### FUNCTION_SCHEMAS End ###\n\nThis is the input query.\n\n### QUERY Start ###\n\t{query}\n### QUERY End ###\n\nThe arguments that you need to provide values for, together with their datatypes, are stated in "signature" in the FUNCTION_SCHEMAS.\nThe values these arguments must take are made clear by the QUERY.\nUse the FUNCTION_SCHEMAS "description" too, as this might provide helpful clues about the arguments and their values.\nReturn only JSON, stating the argument names and their corresponding values.\n\n### FORMATTING_INSTRUCTIONS Start ###\n\tReturn a respones in valid JSON format. Do not return any other explanation or text, just the JSON.\n\tThe JSON-Keys are the names of the arguments, and JSON-values are the values those arguments should take.\n### FORMATTING_INSTRUCTIONS End ###\n\n### EXAMPLE Start ###\n\t=== EXAMPLE_INPUT_QUERY Start ===\n\t\t"How is the weather in Hawaii right now in International units?"\n\t=== EXAMPLE_INPUT_QUERY End ===\n\t=== EXAMPLE_INPUT_SCHEMA Start ===\n\t\t{{\n\t\t\t"name": "get_weather",\n\t\t\t"description": "Useful to get the weather in a specific location",\n\t\t\t"signature": "(location: str, degree: str) -> str",\n\t\t\t"output": "<class 'str'>",\n\t\t}}\n\t=== EXAMPLE_INPUT_QUERY End ===\n\t=== EXAMPLE_OUTPUT Start ===\n\t\t{{\n\t\t\t"location": "Hawaii",\n\t\t\t"degree": "Celsius",\n\t\t}}\n\t=== EXAMPLE_OUTPUT End ===\n### EXAMPLE End ###\n\nNote: I will tip $500 for an accurate JSON output. You will be penalized for an inaccurate JSON output.\n\nProvide JSON output now:\n"""
        llm_input = [Message(role='user', content=prompt)]
        output = self(llm_input)
        if not output:
            raise Exception('No output generated for extract function input')
        output = output.replace("'", '"').strip().rstrip(',')
        logger.info(f'LLM output: {output}')
        function_inputs = json.loads(output)
        if not isinstance(function_inputs, list):
            function_inputs = [function_inputs]
        logger.info(f'Function inputs: {function_inputs}')
        if not self._is_valid_inputs(function_inputs, function_schemas):
            raise ValueError('Invalid inputs')
        return function_inputs

def _is_valid_inputs(self, inputs: List[Dict[str, Any]], function_schemas: List[Dict[str, Any]]) -> bool:
    """Determine if the functions chosen by the LLM exist within the function_schemas,
        and if the input arguments are valid for those functions.

        :param inputs: The inputs to check for validity.
        :type inputs: List[Dict[str, Any]]
        :param function_schemas: The function schemas to check against.
        :type function_schemas: List[Dict[str, Any]]
        :return: True if the inputs are valid, False otherwise.
        :rtype: bool
        """
    try:
        if len(inputs) != 1:
            logger.error('Only one set of function inputs is allowed.')
            return False
        if len(function_schemas) != 1:
            logger.error('Only one function schema is allowed.')
            return False
        if not self._validate_single_function_inputs(inputs[0], function_schemas[0]):
            return False
        return True
    except Exception as e:
        logger.error(f'Input validation error: {str(e)}')
        return False

class OpenAILLM(BaseLLM):
    """LLM for OpenAI. Requires an OpenAI API key from https://platform.openai.com/api-keys."""
    _client: Optional[openai.OpenAI] = PrivateAttr(default=None)
    _async_client: Optional[openai.AsyncOpenAI] = PrivateAttr(default=None)

    def __init__(self, name: Optional[str]=None, openai_api_key: Optional[str]=None, temperature: float=0.01, max_tokens: int=200):
        """Initialize the OpenAILLM.

        :param name: The name of the OpenAI model to use.
        :type name: Optional[str]
        :param openai_api_key: The OpenAI API key.
        :type openai_api_key: Optional[str]
        :param temperature: The temperature of the LLM.
        :type temperature: float
        :param max_tokens: The maximum number of tokens to generate.
        :type max_tokens: int
        """
        if name is None:
            name = EncoderDefault.OPENAI.value['language_model']
        super().__init__(name=name)
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if api_key is None:
            raise ValueError("OpenAI API key cannot be 'None'.")
        try:
            self._async_client = openai.AsyncOpenAI(api_key=api_key)
            self._client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f'OpenAI API client failed to initialize. Error: {e}') from e
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _extract_tool_calls_info(self, tool_calls: List[ChatCompletionMessageToolCall]) -> List[Dict[str, Any]]:
        """Extract the tool calls information from the tool calls.

        :param tool_calls: The tool calls to extract the information from.
        :type tool_calls: List[ChatCompletionMessageToolCall]
        :return: The tool calls information.
        :rtype: List[Dict[str, Any]]
        """
        tool_calls_info = []
        for tool_call in tool_calls:
            if tool_call.function.arguments is None:
                raise ValueError('Invalid output, expected arguments to be specified for each tool call.')
            tool_calls_info.append({'function_name': tool_call.function.name, 'arguments': json.loads(tool_call.function.arguments)})
        return tool_calls_info

    async def async_extract_tool_calls_info(self, tool_calls: List[ChatCompletionMessageToolCall]) -> List[Dict[str, Any]]:
        """Extract the tool calls information from the tool calls.

        :param tool_calls: The tool calls to extract the information from.
        :type tool_calls: List[ChatCompletionMessageToolCall]
        :return: The tool calls information.
        :rtype: List[Dict[str, Any]]
        """
        tool_calls_info = []
        for tool_call in tool_calls:
            if tool_call.function.arguments is None:
                raise ValueError('Invalid output, expected arguments to be specified for each tool call.')
            tool_calls_info.append({'function_name': tool_call.function.name, 'arguments': json.loads(tool_call.function.arguments)})
        return tool_calls_info

    def __call__(self, messages: List[Message], function_schemas: Optional[List[Dict[str, Any]]]=None) -> str:
        """Call the OpenAILLM.

        :param messages: The messages to pass to the OpenAILLM.
        :type messages: List[Message]
        :param function_schemas: The function schemas to pass to the OpenAILLM.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :return: The response from the OpenAILLM.
        :rtype: str
        """
        if self._client is None:
            raise ValueError('OpenAI client is not initialized.')
        try:
            tools: Union[List[Dict[str, Any]], NotGiven] = function_schemas if function_schemas else NOT_GIVEN
            completion = self._client.chat.completions.create(model=self.name, messages=[m.to_openai() for m in messages], temperature=self.temperature, max_tokens=self.max_tokens, tools=tools)
            if function_schemas:
                tool_calls = completion.choices[0].message.tool_calls
                if tool_calls is None:
                    raise ValueError('Invalid output, expected a tool call.')
                if len(tool_calls) < 1:
                    raise ValueError('Invalid output, expected at least one tool to be specified.')
                output = str(self._extract_tool_calls_info(tool_calls))
            else:
                content = completion.choices[0].message.content
                if content is None:
                    raise ValueError('Invalid output, expected content.')
                output = content
            return output
        except Exception as e:
            logger.error(f'LLM error: {e}')
            raise Exception(f'LLM error: {e}') from e

    async def acall(self, messages: List[Message], function_schemas: Optional[List[Dict[str, Any]]]=None) -> str:
        """Call the OpenAILLM asynchronously.

        :param messages: The messages to pass to the OpenAILLM.
        :type messages: List[Message]
        :param function_schemas: The function schemas to pass to the OpenAILLM.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :return: The response from the OpenAILLM.
        :rtype: str
        """
        if self._async_client is None:
            raise ValueError('OpenAI async_client is not initialized.')
        try:
            tools: Union[List[Dict[str, Any]], NotGiven] = function_schemas if function_schemas is not None else NOT_GIVEN
            completion = await self._async_client.chat.completions.create(model=self.name, messages=[m.to_openai() for m in messages], temperature=self.temperature, max_tokens=self.max_tokens, tools=tools)
            if function_schemas:
                tool_calls = completion.choices[0].message.tool_calls
                if tool_calls is None:
                    raise ValueError('Invalid output, expected a tool call.')
                if len(tool_calls) < 1:
                    raise ValueError('Invalid output, expected at least one tool to be specified.')
                output = str(await self.async_extract_tool_calls_info(tool_calls))
            else:
                content = completion.choices[0].message.content
                if content is None:
                    raise ValueError('Invalid output, expected content.')
                output = content
            return output
        except Exception as e:
            logger.error(f'LLM error: {e}')
            raise Exception(f'LLM error: {e}') from e

    def extract_function_inputs(self, query: str, function_schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract the function inputs from the query.

        :param query: The query to extract the function inputs from.
        :type query: str
        :param function_schemas: The function schemas to extract the function inputs from.
        :type function_schemas: List[Dict[str, Any]]
        :return: The function inputs.
        :rtype: List[Dict[str, Any]]
        """
        system_prompt = 'You are an intelligent AI. Given a command or request from the user, call the function to complete the request.'
        messages = [Message(role='system', content=system_prompt), Message(role='user', content=query)]
        output = self(messages=messages, function_schemas=function_schemas)
        if not output:
            raise Exception('No output generated for extract function input')
        output = output.replace("'", '"')
        function_inputs = json.loads(output)
        if not self._is_valid_inputs(function_inputs, function_schemas):
            raise ValueError('Invalid inputs')
        return function_inputs

    async def async_extract_function_inputs(self, query: str, function_schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract the function inputs from the query asynchronously.

        :param query: The query to extract the function inputs from.
        :type query: str
        :param function_schemas: The function schemas to extract the function inputs from.
        :type function_schemas: List[Dict[str, Any]]
        :return: The function inputs.
        :rtype: List[Dict[str, Any]]
        """
        system_prompt = 'You are an intelligent AI. Given a command or request from the user, call the function to complete the request.'
        messages = [Message(role='system', content=system_prompt), Message(role='user', content=query)]
        output = await self.acall(messages=messages, function_schemas=function_schemas)
        if not output:
            raise Exception('No output generated for extract function input')
        output = output.replace("'", '"')
        function_inputs = json.loads(output)
        if not self._is_valid_inputs(function_inputs, function_schemas):
            raise ValueError('Invalid inputs')
        return function_inputs

    def _is_valid_inputs(self, inputs: List[Dict[str, Any]], function_schemas: List[Dict[str, Any]]) -> bool:
        """Determine if the functions chosen by the LLM exist within the function_schemas,
        and if the input arguments are valid for those functions.

        :param inputs: The inputs to check for validity.
        :type inputs: List[Dict[str, Any]]
        :param function_schemas: The function schemas to check against.
        :type function_schemas: List[Dict[str, Any]]
        :return: True if the inputs are valid, False otherwise.
        :rtype: bool
        """
        try:
            for input_dict in inputs:
                if 'function_name' not in input_dict or 'arguments' not in input_dict:
                    logger.error("Missing 'function_name' or 'arguments' in inputs")
                    return False
                function_name = input_dict['function_name']
                arguments = input_dict['arguments']
                matching_schema = next((schema['function'] for schema in function_schemas if schema['function']['name'] == function_name), None)
                if not matching_schema:
                    logger.error(f'No matching function schema found for function name: {function_name}')
                    return False
                if not self._validate_single_function_inputs(arguments, matching_schema):
                    logger.error(f'Validation failed for function name: {function_name}')
                    return False
            return True
        except Exception as e:
            logger.error(f'Input validation error: {str(e)}')
            return False

    def _validate_single_function_inputs(self, inputs: Dict[str, Any], function_schema: Dict[str, Any]) -> bool:
        """Validate the extracted inputs against the function schema.

        :param inputs: The inputs to validate.
        :type inputs: Dict[str, Any]
        :param function_schema: The function schema to validate against.
        :type function_schema: Dict[str, Any]
        :return: True if the inputs are valid, False otherwise.
        """
        try:
            parameters = function_schema['parameters']['properties']
            required_params = function_schema['parameters'].get('required', [])
            for param_name in required_params:
                if param_name not in inputs:
                    logger.error(f"Required input '{param_name}' missing from query")
                    return False
            for param_name, param_info in parameters.items():
                if param_name in inputs:
                    expected_type = param_info['type']
                    if expected_type == 'string' and (not isinstance(inputs[param_name], str)):
                        logger.error(f"Input type for '{param_name}' is not {expected_type}")
                        return False
            return True
        except Exception as e:
            logger.error(f'Single input validation error: {str(e)}')
            return False

def __call__(self, messages: List[Message], function_schemas: Optional[List[Dict[str, Any]]]=None) -> str:
    """Call the OpenAILLM.

        :param messages: The messages to pass to the OpenAILLM.
        :type messages: List[Message]
        :param function_schemas: The function schemas to pass to the OpenAILLM.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :return: The response from the OpenAILLM.
        :rtype: str
        """
    if self._client is None:
        raise ValueError('OpenAI client is not initialized.')
    try:
        tools: Union[List[Dict[str, Any]], NotGiven] = function_schemas if function_schemas else NOT_GIVEN
        completion = self._client.chat.completions.create(model=self.name, messages=[m.to_openai() for m in messages], temperature=self.temperature, max_tokens=self.max_tokens, tools=tools)
        if function_schemas:
            tool_calls = completion.choices[0].message.tool_calls
            if tool_calls is None:
                raise ValueError('Invalid output, expected a tool call.')
            if len(tool_calls) < 1:
                raise ValueError('Invalid output, expected at least one tool to be specified.')
            output = str(self._extract_tool_calls_info(tool_calls))
        else:
            content = completion.choices[0].message.content
            if content is None:
                raise ValueError('Invalid output, expected content.')
            output = content
        return output
    except Exception as e:
        logger.error(f'LLM error: {e}')
        raise Exception(f'LLM error: {e}') from e

class TestMessageDataclass:

    def test_message_creation(self):
        message = Message(role='user', content='Hello!')
        assert message.role == 'user'
        assert message.content == 'Hello!'
        with pytest.raises(ValidationError):
            Message(user_role='invalid_role', message='Hello!')

    def test_message_to_openai(self):
        message = Message(role='user', content='Hello!')
        openai_format = message.to_openai()
        assert openai_format == {'role': 'user', 'content': 'Hello!'}
        message = Message(role='invalid_role', content='Hello!')
        with pytest.raises(ValueError):
            message.to_openai()

    def test_message_to_cohere(self):
        message = Message(role='user', content='Hello!')
        cohere_format = message.to_cohere()
        assert cohere_format == {'role': 'user', 'message': 'Hello!'}

def test_message_creation(self):
    message = Message(role='user', content='Hello!')
    assert message.role == 'user'
    assert message.content == 'Hello!'
    with pytest.raises(ValidationError):
        Message(user_role='invalid_role', message='Hello!')

@pytest.fixture
def mock_openai_llm(mocker):
    mocker.patch.object(OpenAILLM, '__call__', return_value='mocked response')

    async def async_mock_llm_call(messages=None, **kwargs):
        return 'mocked response'
    mocker.patch.object(OpenAILLM, 'acall', side_effect=async_mock_llm_call)
    return OpenAILLM(name='fake-model-v1')

class TestRouterConfig:

    def test_from_file_json(self, tmp_path):
        config_path = tmp_path / 'config.json'
        config_path.write_text(layer_json())
        layer_config = RouterConfig.from_file(str(config_path))
        assert layer_config.encoder_type == 'cohere'
        assert layer_config.encoder_name == 'embed-english-v3.0'
        assert len(layer_config.routes) == 2
        assert layer_config.routes[0].name == 'politics'

    def test_from_file_yaml(self, tmp_path):
        config_path = tmp_path / 'config.yaml'
        config_path.write_text(layer_yaml())
        layer_config = RouterConfig.from_file(str(config_path))
        assert layer_config.encoder_type == 'cohere'
        assert layer_config.encoder_name == 'embed-english-v3.0'
        assert len(layer_config.routes) == 2
        assert layer_config.routes[0].name == 'politics'

    def test_from_file_invalid_path(self):
        with pytest.raises(FileNotFoundError) as excinfo:
            RouterConfig.from_file('nonexistent_path.json')
        assert "[Errno 2] No such file or directory: 'nonexistent_path.json'" in str(excinfo.value)

    def test_from_file_unsupported_type(self, tmp_path):
        config_path = tmp_path / 'config.unsupported'
        config_path.write_text(layer_json())
        with pytest.raises(ValueError) as excinfo:
            RouterConfig.from_file(str(config_path))
        assert 'Unsupported file type' in str(excinfo.value)

    def test_from_file_invalid_config(self, tmp_path):
        invalid_config_json = '\n        {\n            "encoder_type": "cohere",\n            "encoder_name": "embed-english-v3.0",\n            "routes": "This should be a list, not a string"\n        }'
        config_path = tmp_path / 'invalid_config.json'
        with open(config_path, 'w') as file:
            file.write(invalid_config_json)
        with patch('semantic_router.routers.base.is_valid', return_value=False):
            with pytest.raises(Exception) as excinfo:
                RouterConfig.from_file(str(config_path))
            assert 'Invalid config JSON or YAML' in str(excinfo.value), 'Loading an invalid configuration should raise an exception.'

    def test_from_file_with_llm(self, tmp_path):
        llm_config_json = '\n        {\n            "encoder_type": "cohere",\n            "encoder_name": "embed-english-v3.0",\n            "routes": [\n                {\n                    "name": "llm_route",\n                    "utterances": ["tell me a joke", "say something funny"],\n                    "llm": {\n                        "module": "semantic_router.llms.base",\n                        "class": "BaseLLM",\n                        "model": "fake-model-v1"\n                    }\n                }\n            ]\n        }'
        config_path = tmp_path / 'config_with_llm.json'
        with open(config_path, 'w') as file:
            file.write(llm_config_json)
        layer_config = RouterConfig.from_file(str(config_path))
        assert isinstance(layer_config.routes[0].llm, BaseLLM), 'LLM should be instantiated and associated with the route based on the '
        'config'
        assert layer_config.routes[0].llm.name == 'fake-model-v1', "LLM instance should have the 'name' attribute set correctly"

    def test_init(self):
        layer_config = RouterConfig()
        assert layer_config.routes == []

    def test_to_file_json(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        with patch('builtins.open', mock_open()) as mocked_open:
            layer_config.to_file('data/test_output.json')
            mocked_open.assert_called_once_with('data/test_output.json', 'w')

    def test_to_file_yaml(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        with patch('builtins.open', mock_open()) as mocked_open:
            layer_config.to_file('data/test_output.yaml')
            mocked_open.assert_called_once_with('data/test_output.yaml', 'w')

    def test_to_file_invalid(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        with pytest.raises(ValueError):
            layer_config.to_file('test_output.txt')

    def test_from_file_invalid(self):
        with open('test.txt', 'w') as f:
            f.write('dummy content')
        with pytest.raises(ValueError):
            RouterConfig.from_file('test.txt')
        os.remove('test.txt')

    def test_to_dict(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        assert layer_config.to_dict()['routes'] == [route.to_dict()]

    def test_add(self):
        route = Route(name='test', utterances=['utterance'])
        route2 = Route(name='test2', utterances=['utterance2'])
        layer_config = RouterConfig()
        layer_config.add(route)
        assert layer_config.routes == [route]
        layer_config.add(route2)
        assert layer_config.routes == [route, route2]

    def test_get(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        assert layer_config.get('test') == route

    def test_get_not_found(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        assert layer_config.get('not_found') is None

    def test_remove(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        layer_config.remove('test')
        assert layer_config.routes == []

    def test_setting_aggregation_methods(self, openai_encoder, routes):
        for agg in ['sum', 'mean', 'max']:
            route_layer = SemanticRouter(encoder=openai_encoder, routes=routes, aggregation=agg)
            assert route_layer.aggregation == agg

    def test_semantic_classify_multiple_routes_with_different_aggregation(self, openai_encoder, routes):
        route_scores = [{'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 2', 'score': 0.4}, {'route': 'Route 2', 'score': 0.6}, {'route': 'Route 2', 'score': 0.8}, {'route': 'Route 3', 'score': 0.1}, {'route': 'Route 3', 'score': 1.0}]
        for agg in ['sum', 'mean', 'max']:
            route_layer = SemanticRouter(encoder=openai_encoder, routes=routes, aggregation=agg)
            classification, score = route_layer._semantic_classify(route_scores)
            if agg == 'sum':
                assert classification == 'Route 1'
                assert score == [0.5, 0.5, 0.5, 0.5]
            elif agg == 'mean':
                assert classification == 'Route 2'
                assert score == [0.4, 0.6, 0.8]
            elif agg == 'max':
                assert classification == 'Route 3'
                assert score == [0.1, 1.0]

def test_from_file_json(self, tmp_path):
    config_path = tmp_path / 'config.json'
    config_path.write_text(layer_json())
    layer_config = RouterConfig.from_file(str(config_path))
    assert layer_config.encoder_type == 'cohere'
    assert layer_config.encoder_name == 'embed-english-v3.0'
    assert len(layer_config.routes) == 2
    assert layer_config.routes[0].name == 'politics'

def test_from_file_yaml(self, tmp_path):
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(layer_yaml())
    layer_config = RouterConfig.from_file(str(config_path))
    assert layer_config.encoder_type == 'cohere'
    assert layer_config.encoder_name == 'embed-english-v3.0'
    assert len(layer_config.routes) == 2
    assert layer_config.routes[0].name == 'politics'

def test_from_file_invalid_path(self):
    with pytest.raises(FileNotFoundError) as excinfo:
        RouterConfig.from_file('nonexistent_path.json')
    assert "[Errno 2] No such file or directory: 'nonexistent_path.json'" in str(excinfo.value)

def test_from_file_unsupported_type(self, tmp_path):
    config_path = tmp_path / 'config.unsupported'
    config_path.write_text(layer_json())
    with pytest.raises(ValueError) as excinfo:
        RouterConfig.from_file(str(config_path))
    assert 'Unsupported file type' in str(excinfo.value)

def test_from_file_invalid_config(self, tmp_path):
    invalid_config_json = '\n        {\n            "encoder_type": "cohere",\n            "encoder_name": "embed-english-v3.0",\n            "routes": "This should be a list, not a string"\n        }'
    config_path = tmp_path / 'invalid_config.json'
    with open(config_path, 'w') as file:
        file.write(invalid_config_json)
    with patch('semantic_router.routers.base.is_valid', return_value=False):
        with pytest.raises(Exception) as excinfo:
            RouterConfig.from_file(str(config_path))
        assert 'Invalid config JSON or YAML' in str(excinfo.value), 'Loading an invalid configuration should raise an exception.'

def test_from_file_with_llm(self, tmp_path):
    llm_config_json = '\n        {\n            "encoder_type": "cohere",\n            "encoder_name": "embed-english-v3.0",\n            "routes": [\n                {\n                    "name": "llm_route",\n                    "utterances": ["tell me a joke", "say something funny"],\n                    "llm": {\n                        "module": "semantic_router.llms.base",\n                        "class": "BaseLLM",\n                        "model": "fake-model-v1"\n                    }\n                }\n            ]\n        }'
    config_path = tmp_path / 'config_with_llm.json'
    with open(config_path, 'w') as file:
        file.write(llm_config_json)
    layer_config = RouterConfig.from_file(str(config_path))
    assert isinstance(layer_config.routes[0].llm, BaseLLM), 'LLM should be instantiated and associated with the route based on the '
    'config'
    assert layer_config.routes[0].llm.name == 'fake-model-v1', "LLM instance should have the 'name' attribute set correctly"

def test_from_file_invalid(self):
    with open('test.txt', 'w') as f:
        f.write('dummy content')
    with pytest.raises(ValueError):
        RouterConfig.from_file('test.txt')
    os.remove('test.txt')

@pytest.fixture
def openrouter_llm(mocker):
    mocker.patch('openai.Client')
    return OpenRouterLLM(openrouter_api_key='test_api_key')

class TestOpenRouterLLM:

    def test_openrouter_llm_init_with_api_key(self, openrouter_llm):
        assert openrouter_llm._client is not None, 'Client should be initialized'
        assert openrouter_llm.name == 'mistralai/mistral-7b-instruct', 'Default name not set correctly'

    def test_openrouter_llm_init_success(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        llm = OpenRouterLLM()
        assert llm._client is not None

    def test_openrouter_llm_init_without_api_key(self, mocker):
        mocker.patch('os.getenv', return_value=None)
        with pytest.raises(ValueError) as _:
            OpenRouterLLM()

    def test_openrouter_llm_call_uninitialized_client(self, openrouter_llm):
        openrouter_llm._client = None
        with pytest.raises(ValueError) as e:
            llm_input = [Message(role='user', content='test')]
            openrouter_llm(llm_input)
        assert 'OpenRouter client is not initialized.' in str(e.value)

    def test_openrouter_llm_init_exception(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('openai.OpenAI', side_effect=Exception('Initialization error'))
        with pytest.raises(ValueError) as e:
            OpenRouterLLM()
        assert 'OpenRouter API client failed to initialize. Error: Initialization error' in str(e.value)

    def test_openrouter_llm_call_success(self, openrouter_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.content = 'test'
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch.object(openrouter_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        output = openrouter_llm(llm_input)
        assert output == 'test'

def test_openrouter_llm_init_success(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    llm = OpenRouterLLM()
    assert llm._client is not None

def test_openrouter_llm_init_without_api_key(self, mocker):
    mocker.patch('os.getenv', return_value=None)
    with pytest.raises(ValueError) as _:
        OpenRouterLLM()

def test_openrouter_llm_call_uninitialized_client(self, openrouter_llm):
    openrouter_llm._client = None
    with pytest.raises(ValueError) as e:
        llm_input = [Message(role='user', content='test')]
        openrouter_llm(llm_input)
    assert 'OpenRouter client is not initialized.' in str(e.value)

def test_openrouter_llm_init_exception(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('openai.OpenAI', side_effect=Exception('Initialization error'))
    with pytest.raises(ValueError) as e:
        OpenRouterLLM()
    assert 'OpenRouter API client failed to initialize. Error: Initialization error' in str(e.value)

def test_openrouter_llm_call_success(self, openrouter_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.content = 'test'
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch.object(openrouter_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    output = openrouter_llm(llm_input)
    assert output == 'test'

@pytest.fixture
def azure_openai_llm(mocker):
    mocker.patch('openai.Client')
    return AzureOpenAILLM(openai_api_key='test_api_key', azure_endpoint='test_endpoint')

class TestOpenAILLM:

    def test_azure_openai_llm_init_with_api_key(self, azure_openai_llm):
        assert azure_openai_llm._client is not None, 'Client should be initialized'
        assert azure_openai_llm.name == 'gpt-4o', 'Default name not set correctly'

    def test_azure_openai_llm_init_success(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        llm = AzureOpenAILLM()
        assert llm._client is not None

    def test_azure_openai_llm_init_without_api_key(self, mocker):
        mocker.patch('os.getenv', return_value=None)
        with pytest.raises(ValueError) as _:
            AzureOpenAILLM()

    def test_azure_openai_llm_init_without_azure_endpoint(self, mocker):
        mocker.patch('os.getenv', side_effect=lambda key, default=None: {'OPENAI_CHAT_MODEL_NAME': 'test-model-name'}.get(key, default))
        with pytest.raises(ValueError) as e:
            AzureOpenAILLM(openai_api_key='test_api_key')
        assert "Azure endpoint API key cannot be 'None'" in str(e.value)

    def test_azure_openai_llm_call_uninitialized_client(self, azure_openai_llm):
        azure_openai_llm._client = None
        with pytest.raises(ValueError) as e:
            llm_input = [Message(role='user', content='test')]
            azure_openai_llm(llm_input)
        assert 'AzureOpenAI client is not initialized.' in str(e.value)

    def test_azure_openai_llm_init_exception(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('openai.AzureOpenAI', side_effect=Exception('Initialization error'))
        with pytest.raises(ValueError) as e:
            AzureOpenAILLM()
        assert 'AzureOpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

    def test_azure_openai_llm_temperature_max_tokens_initialization(self):
        test_temperature = 0.5
        test_max_tokens = 100
        azure_llm = AzureOpenAILLM(openai_api_key='test_api_key', azure_endpoint='test_endpoint', temperature=test_temperature, max_tokens=test_max_tokens)
        assert azure_llm.temperature == test_temperature, 'Temperature not set correctly'
        assert azure_llm.max_tokens == test_max_tokens, 'Max tokens not set correctly'

    def test_azure_openai_llm_call_success(self, azure_openai_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.content = 'test'
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch.object(azure_openai_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        output = azure_openai_llm(llm_input)
        assert output == 'test'

def test_azure_openai_llm_init_success(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    llm = AzureOpenAILLM()
    assert llm._client is not None

def test_azure_openai_llm_init_without_api_key(self, mocker):
    mocker.patch('os.getenv', return_value=None)
    with pytest.raises(ValueError) as _:
        AzureOpenAILLM()

def test_azure_openai_llm_init_without_azure_endpoint(self, mocker):
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {'OPENAI_CHAT_MODEL_NAME': 'test-model-name'}.get(key, default))
    with pytest.raises(ValueError) as e:
        AzureOpenAILLM(openai_api_key='test_api_key')
    assert "Azure endpoint API key cannot be 'None'" in str(e.value)

def test_azure_openai_llm_call_uninitialized_client(self, azure_openai_llm):
    azure_openai_llm._client = None
    with pytest.raises(ValueError) as e:
        llm_input = [Message(role='user', content='test')]
        azure_openai_llm(llm_input)
    assert 'AzureOpenAI client is not initialized.' in str(e.value)

def test_azure_openai_llm_init_exception(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('openai.AzureOpenAI', side_effect=Exception('Initialization error'))
    with pytest.raises(ValueError) as e:
        AzureOpenAILLM()
    assert 'AzureOpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

def test_azure_openai_llm_temperature_max_tokens_initialization(self):
    test_temperature = 0.5
    test_max_tokens = 100
    azure_llm = AzureOpenAILLM(openai_api_key='test_api_key', azure_endpoint='test_endpoint', temperature=test_temperature, max_tokens=test_max_tokens)
    assert azure_llm.temperature == test_temperature, 'Temperature not set correctly'
    assert azure_llm.max_tokens == test_max_tokens, 'Max tokens not set correctly'

def test_azure_openai_llm_call_success(self, azure_openai_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.content = 'test'
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch.object(azure_openai_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    output = azure_openai_llm(llm_input)
    assert output == 'test'

@pytest.fixture
def llamacpp_llm(mocker):
    mock_llama = mocker.patch('llama_cpp.Llama', spec=Llama)
    llm = mock_llama.return_value
    return LlamaCppLLM(llm=llm)

class TestLlamaCppLLM:

    def test_llama_cpp_import_errors(self, llamacpp_llm):
        with patch.dict('sys.modules', {'llama_cpp': None}):
            with pytest.raises(ImportError) as error:
                LlamaCppLLM(llamacpp_llm.llm)
        assert "Please install LlamaCPP to use Llama CPP llm. You can install it with: `pip install 'semantic-router[local]'`" in str(error.value)

    def test_llamacpp_llm_init_success(self, llamacpp_llm):
        assert llamacpp_llm.name == 'llama.cpp'
        assert llamacpp_llm.temperature == 0.2
        assert llamacpp_llm.max_tokens == 200
        assert llamacpp_llm.llm is not None

    def test_llamacpp_llm_call_success(self, llamacpp_llm, mocker):
        llamacpp_llm.llm.create_chat_completion = mocker.Mock(return_value={'choices': [{'message': {'content': 'test'}}]})
        llm_input = [Message(role='user', content='test')]
        output = llamacpp_llm(llm_input)
        assert output == 'test'

    def test_llamacpp_llm_grammar(self, llamacpp_llm):
        llamacpp_llm._grammar()

    def test_llamacpp_extract_function_inputs(self, llamacpp_llm, mocker):
        llamacpp_llm.llm.create_chat_completion = mocker.Mock(return_value={'choices': [{'message': {'content': "{'timezone': 'America/New_York'}"}}]})
        test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
        test_query = 'What time is it in America/New_York?'
        llamacpp_llm.extract_function_inputs(query=test_query, function_schemas=[test_schema])

    def test_llamacpp_extract_function_inputs_invalid(self, llamacpp_llm, mocker):
        with pytest.raises(ValueError):
            llamacpp_llm.llm.create_chat_completion = mocker.Mock(return_value={'choices': [{'message': {'content': "{'time': 'America/New_York'}"}}]})
            test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
            test_query = 'What time is it in America/New_York?'
            llamacpp_llm.extract_function_inputs(query=test_query, function_schemas=[test_schema])

def test_llama_cpp_import_errors(self, llamacpp_llm):
    with patch.dict('sys.modules', {'llama_cpp': None}):
        with pytest.raises(ImportError) as error:
            LlamaCppLLM(llamacpp_llm.llm)
    assert "Please install LlamaCPP to use Llama CPP llm. You can install it with: `pip install 'semantic-router[local]'`" in str(error.value)

def test_llamacpp_llm_call_success(self, llamacpp_llm, mocker):
    llamacpp_llm.llm.create_chat_completion = mocker.Mock(return_value={'choices': [{'message': {'content': 'test'}}]})
    llm_input = [Message(role='user', content='test')]
    output = llamacpp_llm(llm_input)
    assert output == 'test'

def test_llamacpp_extract_function_inputs(self, llamacpp_llm, mocker):
    llamacpp_llm.llm.create_chat_completion = mocker.Mock(return_value={'choices': [{'message': {'content': "{'timezone': 'America/New_York'}"}}]})
    test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
    test_query = 'What time is it in America/New_York?'
    llamacpp_llm.extract_function_inputs(query=test_query, function_schemas=[test_schema])

def test_llamacpp_extract_function_inputs_invalid(self, llamacpp_llm, mocker):
    with pytest.raises(ValueError):
        llamacpp_llm.llm.create_chat_completion = mocker.Mock(return_value={'choices': [{'message': {'content': "{'time': 'America/New_York'}"}}]})
        test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
        test_query = 'What time is it in America/New_York?'
        llamacpp_llm.extract_function_inputs(query=test_query, function_schemas=[test_schema])

class TestOllamaLLM:

    def test_ollama_llm_init_success(self, ollama_llm):
        assert ollama_llm.temperature == 0.2
        assert ollama_llm.name == 'openhermes'
        assert ollama_llm.max_tokens == 200
        assert ollama_llm.stream is False

    def test_ollama_llm_call_success(self, ollama_llm, mocker):
        mock_response = mocker.MagicMock()
        mock_response.json.return_value = {'message': {'content': 'test response'}}
        mocker.patch('requests.post', return_value=mock_response)
        output = ollama_llm([Message(role='user', content='test')])
        assert output == 'test response'

    def test_ollama_llm_error_handling(self, ollama_llm, mocker):
        mocker.patch('requests.post', side_effect=Exception('LLM error'))
        with pytest.raises(Exception) as exc_info:
            ollama_llm([Message(role='user', content='test')])
        assert 'LLM error' in str(exc_info.value)

def test_ollama_llm_call_success(self, ollama_llm, mocker):
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {'message': {'content': 'test response'}}
    mocker.patch('requests.post', return_value=mock_response)
    output = ollama_llm([Message(role='user', content='test')])
    assert output == 'test response'

def test_ollama_llm_error_handling(self, ollama_llm, mocker):
    mocker.patch('requests.post', side_effect=Exception('LLM error'))
    with pytest.raises(Exception) as exc_info:
        ollama_llm([Message(role='user', content='test')])
    assert 'LLM error' in str(exc_info.value)

@pytest.fixture
def mistralai_llm(mocker):
    mocker.patch('mistralai.client.MistralClient')
    return MistralAILLM(mistralai_api_key='test_api_key')

class TestMistralAILLM:

    def test_mistral_llm_import_errors(self):
        with patch.dict('sys.modules', {'mistralai': None}):
            with pytest.raises(ImportError) as error:
                MistralAILLM()
        assert "Please install MistralAI to use MistralAI LLM. You can install it with: `pip install 'semantic-router[mistralai]'`" in str(error.value)

    def test_mistralai_llm_init_with_api_key(self, mistralai_llm):
        assert mistralai_llm._client is not None, 'Client should be initialized'
        assert mistralai_llm.name == 'mistral-tiny', 'Default name not set correctly'

    def test_mistralai_llm_init_success(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        llm = MistralAILLM()
        assert llm._client is not None

    def test_mistralai_llm_init_without_api_key(self, mocker):
        mocker.patch('os.getenv', return_value=None)
        with pytest.raises(ValueError) as _:
            MistralAILLM()

    def test_mistralai_llm_call_uninitialized_client(self, mistralai_llm):
        mistralai_llm._client = None
        with pytest.raises(ValueError) as e:
            llm_input = [Message(role='user', content='test')]
            mistralai_llm(llm_input)
        assert 'MistralAI client is not initialized.' in str(e.value)

    def test_mistralai_llm_init_exception(self, mocker):
        mocker.patch('mistralai.client.MistralClient', side_effect=Exception('Initialization error'))
        with pytest.raises(ValueError) as e:
            MistralAILLM()
        assert "MistralAI API key cannot be 'None'." in str(e.value)

    def test_mistralai_llm_call_success(self, mistralai_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.content = 'test'
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch.object(mistralai_llm._client, 'chat', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        output = mistralai_llm(llm_input)
        assert output == 'test'

def test_mistral_llm_import_errors(self):
    with patch.dict('sys.modules', {'mistralai': None}):
        with pytest.raises(ImportError) as error:
            MistralAILLM()
    assert "Please install MistralAI to use MistralAI LLM. You can install it with: `pip install 'semantic-router[mistralai]'`" in str(error.value)

def test_mistralai_llm_init_success(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    llm = MistralAILLM()
    assert llm._client is not None

def test_mistralai_llm_init_without_api_key(self, mocker):
    mocker.patch('os.getenv', return_value=None)
    with pytest.raises(ValueError) as _:
        MistralAILLM()

def test_mistralai_llm_call_uninitialized_client(self, mistralai_llm):
    mistralai_llm._client = None
    with pytest.raises(ValueError) as e:
        llm_input = [Message(role='user', content='test')]
        mistralai_llm(llm_input)
    assert 'MistralAI client is not initialized.' in str(e.value)

def test_mistralai_llm_init_exception(self, mocker):
    mocker.patch('mistralai.client.MistralClient', side_effect=Exception('Initialization error'))
    with pytest.raises(ValueError) as e:
        MistralAILLM()
    assert "MistralAI API key cannot be 'None'." in str(e.value)

def test_mistralai_llm_call_success(self, mistralai_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.content = 'test'
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch.object(mistralai_llm._client, 'chat', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    output = mistralai_llm(llm_input)
    assert output == 'test'

@pytest.fixture
def cohere_llm(mocker):
    mocker.patch('cohere.Client')
    return CohereLLM(cohere_api_key='test_api_key')

class TestCohereLLM:

    def test_initialization_with_api_key(self, cohere_llm):
        assert cohere_llm._client is not None, 'Client should be initialized'
        assert cohere_llm.name == 'command', 'Default name not set correctly'

    def test_initialization_without_api_key(self, mocker, monkeypatch):
        monkeypatch.delenv('COHERE_API_KEY', raising=False)
        mocker.patch('cohere.Client')
        with pytest.raises(ValueError):
            CohereLLM()

    def test_call_method(self, cohere_llm, mocker):
        mock_llm = mocker.MagicMock()
        mock_llm.text = 'test'
        cohere_llm._client.chat.return_value = mock_llm
        llm_input = [Message(role='user', content='test')]
        result = cohere_llm(llm_input)
        assert isinstance(result, str), 'Result should be a str'
        cohere_llm._client.chat.assert_called_once()

    def test_raises_value_error_if_cohere_client_fails_to_initialize(self, mocker):
        mocker.patch('cohere.Client', side_effect=Exception('Failed to initialize client'))
        with pytest.raises(ValueError):
            CohereLLM(cohere_api_key='test_api_key')

    def test_raises_value_error_if_cohere_client_is_not_initialized(self, mocker):
        mocker.patch('cohere.Client', return_value=None)
        llm = CohereLLM(cohere_api_key='test_api_key')
        with pytest.raises(ValueError):
            llm('test')

    def test_call_method_raises_error_on_api_failure(self, cohere_llm, mocker):
        mocker.patch.object(cohere_llm._client, '__call__', side_effect=Exception('API call failed'))
        with pytest.raises(ValueError):
            cohere_llm('test')

def test_initialization_without_api_key(self, mocker, monkeypatch):
    monkeypatch.delenv('COHERE_API_KEY', raising=False)
    mocker.patch('cohere.Client')
    with pytest.raises(ValueError):
        CohereLLM()

def test_call_method(self, cohere_llm, mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.text = 'test'
    cohere_llm._client.chat.return_value = mock_llm
    llm_input = [Message(role='user', content='test')]
    result = cohere_llm(llm_input)
    assert isinstance(result, str), 'Result should be a str'
    cohere_llm._client.chat.assert_called_once()

def test_raises_value_error_if_cohere_client_fails_to_initialize(self, mocker):
    mocker.patch('cohere.Client', side_effect=Exception('Failed to initialize client'))
    with pytest.raises(ValueError):
        CohereLLM(cohere_api_key='test_api_key')

def test_raises_value_error_if_cohere_client_is_not_initialized(self, mocker):
    mocker.patch('cohere.Client', return_value=None)
    llm = CohereLLM(cohere_api_key='test_api_key')
    with pytest.raises(ValueError):
        llm('test')

def test_call_method_raises_error_on_api_failure(self, cohere_llm, mocker):
    mocker.patch.object(cohere_llm._client, '__call__', side_effect=Exception('API call failed'))
    with pytest.raises(ValueError):
        cohere_llm('test')

class TestBaseLLM:

    @pytest.fixture
    def base_llm(self):
        return BaseLLM(name='TestLLM')

    @pytest.fixture
    def mixed_function_schema(self):
        return [{'name': 'test_function', 'description': 'A test function with mixed mandatory and optional parameters.', 'signature': "(mandatory1, mandatory2: int, optional1=None, optional2: str = 'default')"}]

    @pytest.fixture
    def mandatory_params(self):
        return ['param1', 'param2']

    @pytest.fixture
    def all_params(self):
        return ['param1', 'param2', 'optional1']

    def test_base_llm_initialization(self, base_llm):
        assert base_llm.name == 'TestLLM', 'Initialization of name failed'

    def test_base_llm_call_method_not_implemented(self, base_llm):
        with pytest.raises(NotImplementedError):
            base_llm('test')

    def test_base_llm_is_valid_inputs_valid_input_pass(self, base_llm):
        test_schemas = [{'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}]
        test_inputs = [{'timezone': 'America/New_York'}]
        assert base_llm._is_valid_inputs(test_inputs, test_schemas) is True

    @pytest.mark.skip(reason='TODO: bug in is_valid_inputs')
    def test_base_llm_is_valid_inputs_valid_input_fail(self, base_llm):
        test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
        test_inputs = {'timezone': None}
        assert base_llm._is_valid_inputs(test_inputs, test_schema) is False

    def test_base_llm_is_valid_inputs_invalid_false(self, base_llm):
        test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.'}
        test_inputs = {'timezone': 'America/New_York'}
        assert base_llm._is_valid_inputs(test_inputs, test_schema) is False

    def test_base_llm_extract_function_inputs(self, base_llm):
        with pytest.raises(NotImplementedError):
            test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
            test_query = 'What time is it in America/New_York?'
            base_llm.extract_function_inputs(test_schema, test_query)

    def test_base_llm_extract_function_inputs_no_output(self, base_llm, mocker):
        with pytest.raises(Exception):
            base_llm.output = mocker.Mock(return_value=None)
            test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
            test_query = 'What time is it in America/New_York?'
            base_llm.extract_function_inputs(test_schema, test_query)

    def test_mandatory_args_only(self, base_llm, mixed_function_schema):
        inputs = [{'mandatory1': 'value1', 'mandatory2': 42}]
        assert base_llm._is_valid_inputs(inputs, mixed_function_schema)

    def test_all_args_provided(self, base_llm, mixed_function_schema):
        inputs = [{'mandatory1': 'value1', 'mandatory2': 42, 'optional1': 'opt1', 'optional2': 'opt2'}]
        assert base_llm._is_valid_inputs(inputs, mixed_function_schema)

    def test_missing_mandatory_arg(self, base_llm, mixed_function_schema):
        inputs = [{'mandatory1': 'value1', 'optional1': 'opt1', 'optional2': 'opt2'}]
        assert not base_llm._is_valid_inputs(inputs, mixed_function_schema)

    def test_extra_arg_provided(self, base_llm, mixed_function_schema):
        inputs = [{'mandatory1': 'value1', 'mandatory2': 42, 'optional1': 'opt1', 'optional2': 'opt2', 'extra': 'value'}]
        assert not base_llm._is_valid_inputs(inputs, mixed_function_schema)

    def test_check_for_mandatory_inputs_all_present(self, base_llm, mandatory_params):
        inputs = {'param1': 'value1', 'param2': 'value2'}
        assert base_llm._check_for_mandatory_inputs(inputs, mandatory_params)

    def test_check_for_mandatory_inputs_missing_one(self, base_llm, mandatory_params):
        inputs = {'param1': 'value1'}
        assert not base_llm._check_for_mandatory_inputs(inputs, mandatory_params)

    def test_check_for_extra_inputs_no_extras(self, base_llm, all_params):
        inputs = {'param1': 'value1', 'param2': 'value2'}
        assert base_llm._check_for_extra_inputs(inputs, all_params)

    def test_check_for_extra_inputs_with_extras(self, base_llm, all_params):
        inputs = {'param1': 'value1', 'param2': 'value2', 'extra_param': 'extra'}
        assert not base_llm._check_for_extra_inputs(inputs, all_params)

    def test_is_valid_inputs_multiple_inputs(self, base_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        test_inputs = [{'timezone': 'America/New_York'}, {'timezone': 'Europe/London'}]
        test_schemas = [{'name': 'get_time', 'description': 'Finds the current time in a specific timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}]
        result = base_llm._is_valid_inputs(test_inputs, test_schemas)
        assert not result, 'Method should return False when multiple inputs are provided'
        mocked_logger.assert_called_once_with('Only one set of function inputs is allowed.')

    def test_is_valid_inputs_exception_handling(self, base_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        with patch('semantic_router.llms.base.BaseLLM._validate_single_function_inputs', side_effect=Exception('Test Exception')):
            test_inputs = [{'timezone': 'America/New_York'}]
            test_schemas = [{'name': 'get_time', 'description': 'Finds the current time in a specific timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}]
            result = base_llm._is_valid_inputs(test_inputs, test_schemas)
            assert not result, 'Method should return False when an exception occurs'
            mocked_logger.assert_called_once_with('Input validation error: Test Exception')

    def test_validate_single_function_inputs_exception_handling(self, base_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        test_inputs = {'timezone': 'America/New_York'}
        malformed_function_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.', 'signiture': '(timezone: str)', 'output': "<class 'str'>"}
        result = base_llm._validate_single_function_inputs(test_inputs, malformed_function_schema)
        assert not result, 'Method should return False when an exception occurs'
        expected_error_message = "Single input validation error: 'signature'"
        mocked_logger.assert_called_once_with(expected_error_message)

    def test_extract_parameter_info_valid(self, base_llm):
        signature = "(param1: int, param2: str = 'default')"
        expected_names = ['param1', 'param2']
        expected_types = ['int', 'str']
        param_names, param_types = base_llm._extract_parameter_info(signature)
        assert param_names == expected_names, 'Parameter names did not match expected'
        assert param_types == expected_types, 'Parameter types did not match expected'

    def test_extract_parameter_info_malformed(self, base_llm):
        signature = "(param1 int, param2: str = 'default')"
        with pytest.raises(IndexError):
            base_llm._extract_parameter_info(signature)

def test_base_llm_call_method_not_implemented(self, base_llm):
    with pytest.raises(NotImplementedError):
        base_llm('test')

def test_base_llm_is_valid_inputs_valid_input_pass(self, base_llm):
    test_schemas = [{'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}]
    test_inputs = [{'timezone': 'America/New_York'}]
    assert base_llm._is_valid_inputs(test_inputs, test_schemas) is True

@pytest.mark.skip(reason='TODO: bug in is_valid_inputs')
def test_base_llm_is_valid_inputs_valid_input_fail(self, base_llm):
    test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
    test_inputs = {'timezone': None}
    assert base_llm._is_valid_inputs(test_inputs, test_schema) is False

def test_base_llm_is_valid_inputs_invalid_false(self, base_llm):
    test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.'}
    test_inputs = {'timezone': 'America/New_York'}
    assert base_llm._is_valid_inputs(test_inputs, test_schema) is False

def test_base_llm_extract_function_inputs(self, base_llm):
    with pytest.raises(NotImplementedError):
        test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
        test_query = 'What time is it in America/New_York?'
        base_llm.extract_function_inputs(test_schema, test_query)

def test_base_llm_extract_function_inputs_no_output(self, base_llm, mocker):
    with pytest.raises(Exception):
        base_llm.output = mocker.Mock(return_value=None)
        test_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.\n\n:param timezone: The timezone to find the current time in, should\n    be a valid timezone from the IANA Time Zone Database like\n    "America/New_York" or "Europe/London". Do NOT put the place\n    name itself like "rome", or "new york", you must provide\n    the IANA format.\n:type timezone: str\n:return: The current time in the specified timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}
        test_query = 'What time is it in America/New_York?'
        base_llm.extract_function_inputs(test_schema, test_query)

def test_mandatory_args_only(self, base_llm, mixed_function_schema):
    inputs = [{'mandatory1': 'value1', 'mandatory2': 42}]
    assert base_llm._is_valid_inputs(inputs, mixed_function_schema)

def test_all_args_provided(self, base_llm, mixed_function_schema):
    inputs = [{'mandatory1': 'value1', 'mandatory2': 42, 'optional1': 'opt1', 'optional2': 'opt2'}]
    assert base_llm._is_valid_inputs(inputs, mixed_function_schema)

def test_missing_mandatory_arg(self, base_llm, mixed_function_schema):
    inputs = [{'mandatory1': 'value1', 'optional1': 'opt1', 'optional2': 'opt2'}]
    assert not base_llm._is_valid_inputs(inputs, mixed_function_schema)

def test_extra_arg_provided(self, base_llm, mixed_function_schema):
    inputs = [{'mandatory1': 'value1', 'mandatory2': 42, 'optional1': 'opt1', 'optional2': 'opt2', 'extra': 'value'}]
    assert not base_llm._is_valid_inputs(inputs, mixed_function_schema)

def test_is_valid_inputs_multiple_inputs(self, base_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    test_inputs = [{'timezone': 'America/New_York'}, {'timezone': 'Europe/London'}]
    test_schemas = [{'name': 'get_time', 'description': 'Finds the current time in a specific timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}]
    result = base_llm._is_valid_inputs(test_inputs, test_schemas)
    assert not result, 'Method should return False when multiple inputs are provided'
    mocked_logger.assert_called_once_with('Only one set of function inputs is allowed.')

def test_is_valid_inputs_exception_handling(self, base_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    with patch('semantic_router.llms.base.BaseLLM._validate_single_function_inputs', side_effect=Exception('Test Exception')):
        test_inputs = [{'timezone': 'America/New_York'}]
        test_schemas = [{'name': 'get_time', 'description': 'Finds the current time in a specific timezone.', 'signature': '(timezone: str) -> str', 'output': "<class 'str'>"}]
        result = base_llm._is_valid_inputs(test_inputs, test_schemas)
        assert not result, 'Method should return False when an exception occurs'
        mocked_logger.assert_called_once_with('Input validation error: Test Exception')

def test_validate_single_function_inputs_exception_handling(self, base_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    test_inputs = {'timezone': 'America/New_York'}
    malformed_function_schema = {'name': 'get_time', 'description': 'Finds the current time in a specific timezone.', 'signiture': '(timezone: str)', 'output': "<class 'str'>"}
    result = base_llm._validate_single_function_inputs(test_inputs, malformed_function_schema)
    assert not result, 'Method should return False when an exception occurs'
    expected_error_message = "Single input validation error: 'signature'"
    mocked_logger.assert_called_once_with(expected_error_message)

def test_extract_parameter_info_valid(self, base_llm):
    signature = "(param1: int, param2: str = 'default')"
    expected_names = ['param1', 'param2']
    expected_types = ['int', 'str']
    param_names, param_types = base_llm._extract_parameter_info(signature)
    assert param_names == expected_names, 'Parameter names did not match expected'
    assert param_types == expected_types, 'Parameter types did not match expected'

def test_extract_parameter_info_malformed(self, base_llm):
    signature = "(param1 int, param2: str = 'default')"
    with pytest.raises(IndexError):
        base_llm._extract_parameter_info(signature)

@pytest.fixture
def openai_llm(mocker):
    mocker.patch('openai.Client')
    return OpenAILLM(openai_api_key='test_api_key')

class TestOpenAILLM:

    def test_openai_llm_init_with_api_key(self, openai_llm):
        assert openai_llm._client is not None, 'Client should be initialized'
        assert openai_llm.name == 'gpt-4o', 'Default name not set correctly'

    def test_openai_llm_init_success(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        llm = OpenAILLM()
        assert llm._client is not None

    def test_openai_llm_init_without_api_key(self, mocker):
        mocker.patch('os.getenv', return_value=None)
        with pytest.raises(ValueError) as _:
            OpenAILLM()

    def test_openai_llm_call_uninitialized_client(self, openai_llm):
        openai_llm._client = None
        with pytest.raises(ValueError) as e:
            llm_input = [Message(role='user', content='test')]
            openai_llm(llm_input)
        assert 'OpenAI client is not initialized.' in str(e.value)

    def test_openai_llm_init_exception(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('openai.OpenAI', side_effect=Exception('Initialization error'))
        with pytest.raises(ValueError) as e:
            OpenAILLM()
        assert 'OpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

    def test_openai_llm_call_success(self, openai_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.content = 'test'
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        output = openai_llm(llm_input)
        assert output == 'test'

    def test_get_schemas_openai_with_valid_callable(self):

        def sample_function(param1: int, param2: str='default') -> str:
            """Sample function for testing."""
            return f'param1: {param1}, param2: {param2}'
        expected_schema = [{'type': 'function', 'function': {'name': 'sample_function', 'description': 'Sample function for testing.', 'parameters': {'type': 'object', 'properties': {'param1': {'type': 'number', 'description': 'No description available.'}, 'param2': {'type': 'string', 'description': 'No description available.'}}, 'required': ['param1']}}}]
        schema = get_schemas_openai([sample_function])
        assert schema == expected_schema, 'Schema did not match expected output.'

    def test_get_schemas_openai_with_non_callable(self):
        non_callable = 'I am not a function'
        with pytest.raises(ValueError):
            get_schemas_openai([non_callable])

    def test_openai_llm_call_with_function_schema(self, openai_llm, mocker):
        mock_function = mocker.MagicMock(arguments='{"timezone":"America/New_York"}')
        mock_function.name = 'sample_function'
        mock_tool_call = mocker.MagicMock(function=mock_function)
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.tool_calls = [mock_tool_call]
        mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        function_schemas = [{'type': 'function', 'name': 'sample_function'}]
        output = openai_llm(llm_input, function_schemas)
        assert output == "[{'function_name': 'sample_function', 'arguments': {'timezone': 'America/New_York'}}]", 'Output did not match expected result with function schema'

    def test_openai_llm_call_with_invalid_tool_calls(self, openai_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.tool_calls = None
        mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        function_schemas = [{'type': 'function', 'name': 'sample_function'}]
        with pytest.raises(Exception) as exc_info:
            openai_llm(llm_input, function_schemas)
        expected_error_message = 'LLM error: Invalid output, expected a tool call.'
        actual_error_message = str(exc_info.value)
        assert expected_error_message in actual_error_message, f"Expected error message: '{expected_error_message}', but got: '{actual_error_message}'"

    def test_openai_llm_call_with_no_arguments_in_tool_calls(self, openai_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.tool_calls = [mocker.MagicMock(function=mocker.MagicMock(arguments=None))]
        mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        function_schemas = [{'type': 'function', 'name': 'sample_function'}]
        with pytest.raises(Exception) as exc_info:
            openai_llm(llm_input, function_schemas)
        expected_error_message = 'LLM error: Invalid output, expected arguments to be specified for each tool call.'
        actual_error_message = str(exc_info.value)
        assert expected_error_message in actual_error_message, f"Expected error message: '{expected_error_message}', but got: '{actual_error_message}'"

    def test_extract_function_inputs(self, openai_llm, mocker):
        query = 'fetch user data'
        function_schemas = get_user_data_schema
        mocker.patch.object(OpenAILLM, '__call__', return_value='[{"function_name": "get_user_data", "arguments": {"user_id": "123"}}]')
        result = openai_llm.extract_function_inputs(query, function_schemas)
        expected_messages = [Message(role='system', content='You are an intelligent AI. Given a command or request from the user, call the function to complete the request.'), Message(role='user', content=query)]
        openai_llm.__call__.assert_called_once_with(messages=expected_messages, function_schemas=function_schemas)
        assert result == [{'function_name': 'get_user_data', 'arguments': {'user_id': '123'}}], 'The function inputs should match the expected dictionary.'

    def test_openai_llm_call_with_no_tool_calls_specified(self, openai_llm, mocker):
        mock_completion = mocker.MagicMock()
        mock_completion.choices[0].message.tool_calls = []
        mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
        llm_input = [Message(role='user', content='test')]
        function_schemas = [{'type': 'function', 'name': 'sample_function'}]
        with pytest.raises(Exception) as exc_info:
            openai_llm(llm_input, function_schemas)
        expected_error_message = 'LLM error: Invalid output, expected at least one tool to be specified.'
        assert str(exc_info.value) == expected_error_message, f"Expected error message: '{expected_error_message}', but got: '{str(exc_info.value)}'"

    def test_extract_function_inputs_no_output(self, openai_llm, mocker):
        query = 'fetch user data'
        function_schemas = [{'type': 'function', 'name': 'get_user_data'}]
        mocker.patch.object(OpenAILLM, '__call__', return_value='')
        with pytest.raises(Exception) as exc_info:
            openai_llm.extract_function_inputs(query, function_schemas)
        assert str(exc_info.value) == 'No output generated for extract function input', 'Expected exception message not found'

    def test_extract_function_inputs_invalid_output(self, openai_llm, mocker):
        query = 'fetch user data'
        function_schemas = [{'type': 'function', 'name': 'get_user_data'}]
        mocker.patch.object(OpenAILLM, '__call__', return_value='[{"function_name": "get_user_data", "arguments": {"user_id": "123"}}]')
        mocker.patch.object(OpenAILLM, '_is_valid_inputs', return_value=False)
        with pytest.raises(ValueError) as exc_info:
            openai_llm.extract_function_inputs(query, function_schemas)
        assert str(exc_info.value) == 'Invalid inputs', 'Expected exception message not found'

    def test_is_valid_inputs_missing_function_name(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        inputs = [{'arguments': {'user_id': '123'}}]
        function_schemas = get_user_data_schema
        result = openai_llm._is_valid_inputs(inputs, function_schemas)
        assert not result, "The method should return False when 'function_name' is missing"
        mocked_logger.assert_called_once_with("Missing 'function_name' or 'arguments' in inputs")

    def test_is_valid_inputs_missing_arguments(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        inputs = [{'function_name': 'get_user_data'}]
        function_schemas = get_user_data_schema
        result = openai_llm._is_valid_inputs(inputs, function_schemas)
        assert not result, "The method should return False when 'arguments' is missing"
        mocked_logger.assert_called_once_with("Missing 'function_name' or 'arguments' in inputs")

    def test_is_valid_inputs_no_matching_schema(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        inputs = [{'function_name': 'name_that_does_not_exist_in_schema', 'arguments': {'user_id': '123'}}]
        function_schemas = get_user_data_schema
        result = openai_llm._is_valid_inputs(inputs, function_schemas)
        assert not result, 'The method should return False when no matching function schema is found'
        expected_error_message = 'No matching function schema found for function name: name_that_does_not_exist_in_schema'
        mocked_logger.assert_called_once_with(expected_error_message)

    def test_is_valid_inputs_validation_failed(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        inputs = [{'function_name': 'get_user_data', 'arguments': {'user_id': 123}}]
        function_schemas = get_user_data_schema
        mocker.patch.object(OpenAILLM, '_validate_single_function_inputs', return_value=False)
        result = openai_llm._is_valid_inputs(inputs, function_schemas)
        assert not result, 'The method should return False when validation fails'
        expected_error_message = 'Validation failed for function name: get_user_data'
        mocked_logger.assert_called_once_with(expected_error_message)

    def test_is_valid_inputs_exception_handling(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        inputs = [{'function_name': 'get_user_data', 'arguments': {'user_id': '123'}}]
        function_schemas = get_user_data_schema
        mocker.patch.object(OpenAILLM, '_validate_single_function_inputs', side_effect=Exception('Test exception'))
        result = openai_llm._is_valid_inputs(inputs, function_schemas)
        assert not result, 'The method should return False when an exception occurs'
        mocked_logger.assert_called_once_with('Input validation error: Test exception')

    def test_validate_single_function_inputs_missing_required_param(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        function_schema = example_function_schema
        inputs = {}
        result = openai_llm._validate_single_function_inputs(inputs, function_schema)
        assert not result, 'The method should return False when a required parameter is missing'
        expected_error_message = "Required input 'user_id' missing from query"
        mocked_logger.assert_called_once_with(expected_error_message)

    def test_validate_single_function_inputs_incorrect_type(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
        function_schema = example_function_schema
        inputs = {'user_id': 123}
        result = openai_llm._validate_single_function_inputs(inputs, function_schema)
        assert not result, 'The method should return False when input type is incorrect'
        expected_error_message = "Input type for 'user_id' is not string"
        mocked_logger.assert_called_once_with(expected_error_message)

    def test_validate_single_function_inputs_exception_handling(self, openai_llm, mocker):
        mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')

        class SchemaSimulator:

            def __getitem__(self, item):
                raise Exception('Test exception')
        function_schema = SchemaSimulator()
        result = openai_llm._validate_single_function_inputs({'user_id': '123'}, function_schema)
        assert not result, 'The method should return False when an exception occurs'
        mocked_logger.assert_called_once_with('Single input validation error: Test exception')

def test_openai_llm_init_success(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    llm = OpenAILLM()
    assert llm._client is not None

def test_openai_llm_init_without_api_key(self, mocker):
    mocker.patch('os.getenv', return_value=None)
    with pytest.raises(ValueError) as _:
        OpenAILLM()

def test_openai_llm_call_uninitialized_client(self, openai_llm):
    openai_llm._client = None
    with pytest.raises(ValueError) as e:
        llm_input = [Message(role='user', content='test')]
        openai_llm(llm_input)
    assert 'OpenAI client is not initialized.' in str(e.value)

def test_openai_llm_init_exception(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('openai.OpenAI', side_effect=Exception('Initialization error'))
    with pytest.raises(ValueError) as e:
        OpenAILLM()
    assert 'OpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

def test_openai_llm_call_success(self, openai_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.content = 'test'
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    output = openai_llm(llm_input)
    assert output == 'test'

def test_get_schemas_openai_with_valid_callable(self):

    def sample_function(param1: int, param2: str='default') -> str:
        """Sample function for testing."""
        return f'param1: {param1}, param2: {param2}'
    expected_schema = [{'type': 'function', 'function': {'name': 'sample_function', 'description': 'Sample function for testing.', 'parameters': {'type': 'object', 'properties': {'param1': {'type': 'number', 'description': 'No description available.'}, 'param2': {'type': 'string', 'description': 'No description available.'}}, 'required': ['param1']}}}]
    schema = get_schemas_openai([sample_function])
    assert schema == expected_schema, 'Schema did not match expected output.'

def test_get_schemas_openai_with_non_callable(self):
    non_callable = 'I am not a function'
    with pytest.raises(ValueError):
        get_schemas_openai([non_callable])

def test_openai_llm_call_with_function_schema(self, openai_llm, mocker):
    mock_function = mocker.MagicMock(arguments='{"timezone":"America/New_York"}')
    mock_function.name = 'sample_function'
    mock_tool_call = mocker.MagicMock(function=mock_function)
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.tool_calls = [mock_tool_call]
    mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    function_schemas = [{'type': 'function', 'name': 'sample_function'}]
    output = openai_llm(llm_input, function_schemas)
    assert output == "[{'function_name': 'sample_function', 'arguments': {'timezone': 'America/New_York'}}]", 'Output did not match expected result with function schema'

def test_openai_llm_call_with_invalid_tool_calls(self, openai_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.tool_calls = None
    mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    function_schemas = [{'type': 'function', 'name': 'sample_function'}]
    with pytest.raises(Exception) as exc_info:
        openai_llm(llm_input, function_schemas)
    expected_error_message = 'LLM error: Invalid output, expected a tool call.'
    actual_error_message = str(exc_info.value)
    assert expected_error_message in actual_error_message, f"Expected error message: '{expected_error_message}', but got: '{actual_error_message}'"

def test_openai_llm_call_with_no_arguments_in_tool_calls(self, openai_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.tool_calls = [mocker.MagicMock(function=mocker.MagicMock(arguments=None))]
    mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    function_schemas = [{'type': 'function', 'name': 'sample_function'}]
    with pytest.raises(Exception) as exc_info:
        openai_llm(llm_input, function_schemas)
    expected_error_message = 'LLM error: Invalid output, expected arguments to be specified for each tool call.'
    actual_error_message = str(exc_info.value)
    assert expected_error_message in actual_error_message, f"Expected error message: '{expected_error_message}', but got: '{actual_error_message}'"

def test_extract_function_inputs(self, openai_llm, mocker):
    query = 'fetch user data'
    function_schemas = get_user_data_schema
    mocker.patch.object(OpenAILLM, '__call__', return_value='[{"function_name": "get_user_data", "arguments": {"user_id": "123"}}]')
    result = openai_llm.extract_function_inputs(query, function_schemas)
    expected_messages = [Message(role='system', content='You are an intelligent AI. Given a command or request from the user, call the function to complete the request.'), Message(role='user', content=query)]
    openai_llm.__call__.assert_called_once_with(messages=expected_messages, function_schemas=function_schemas)
    assert result == [{'function_name': 'get_user_data', 'arguments': {'user_id': '123'}}], 'The function inputs should match the expected dictionary.'

def test_openai_llm_call_with_no_tool_calls_specified(self, openai_llm, mocker):
    mock_completion = mocker.MagicMock()
    mock_completion.choices[0].message.tool_calls = []
    mocker.patch.object(openai_llm._client.chat.completions, 'create', return_value=mock_completion)
    llm_input = [Message(role='user', content='test')]
    function_schemas = [{'type': 'function', 'name': 'sample_function'}]
    with pytest.raises(Exception) as exc_info:
        openai_llm(llm_input, function_schemas)
    expected_error_message = 'LLM error: Invalid output, expected at least one tool to be specified.'
    assert str(exc_info.value) == expected_error_message, f"Expected error message: '{expected_error_message}', but got: '{str(exc_info.value)}'"

def test_extract_function_inputs_no_output(self, openai_llm, mocker):
    query = 'fetch user data'
    function_schemas = [{'type': 'function', 'name': 'get_user_data'}]
    mocker.patch.object(OpenAILLM, '__call__', return_value='')
    with pytest.raises(Exception) as exc_info:
        openai_llm.extract_function_inputs(query, function_schemas)
    assert str(exc_info.value) == 'No output generated for extract function input', 'Expected exception message not found'

def test_extract_function_inputs_invalid_output(self, openai_llm, mocker):
    query = 'fetch user data'
    function_schemas = [{'type': 'function', 'name': 'get_user_data'}]
    mocker.patch.object(OpenAILLM, '__call__', return_value='[{"function_name": "get_user_data", "arguments": {"user_id": "123"}}]')
    mocker.patch.object(OpenAILLM, '_is_valid_inputs', return_value=False)
    with pytest.raises(ValueError) as exc_info:
        openai_llm.extract_function_inputs(query, function_schemas)
    assert str(exc_info.value) == 'Invalid inputs', 'Expected exception message not found'

def test_is_valid_inputs_missing_function_name(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    inputs = [{'arguments': {'user_id': '123'}}]
    function_schemas = get_user_data_schema
    result = openai_llm._is_valid_inputs(inputs, function_schemas)
    assert not result, "The method should return False when 'function_name' is missing"
    mocked_logger.assert_called_once_with("Missing 'function_name' or 'arguments' in inputs")

def test_is_valid_inputs_missing_arguments(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    inputs = [{'function_name': 'get_user_data'}]
    function_schemas = get_user_data_schema
    result = openai_llm._is_valid_inputs(inputs, function_schemas)
    assert not result, "The method should return False when 'arguments' is missing"
    mocked_logger.assert_called_once_with("Missing 'function_name' or 'arguments' in inputs")

def test_is_valid_inputs_no_matching_schema(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    inputs = [{'function_name': 'name_that_does_not_exist_in_schema', 'arguments': {'user_id': '123'}}]
    function_schemas = get_user_data_schema
    result = openai_llm._is_valid_inputs(inputs, function_schemas)
    assert not result, 'The method should return False when no matching function schema is found'
    expected_error_message = 'No matching function schema found for function name: name_that_does_not_exist_in_schema'
    mocked_logger.assert_called_once_with(expected_error_message)

def test_is_valid_inputs_validation_failed(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    inputs = [{'function_name': 'get_user_data', 'arguments': {'user_id': 123}}]
    function_schemas = get_user_data_schema
    mocker.patch.object(OpenAILLM, '_validate_single_function_inputs', return_value=False)
    result = openai_llm._is_valid_inputs(inputs, function_schemas)
    assert not result, 'The method should return False when validation fails'
    expected_error_message = 'Validation failed for function name: get_user_data'
    mocked_logger.assert_called_once_with(expected_error_message)

def test_is_valid_inputs_exception_handling(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    inputs = [{'function_name': 'get_user_data', 'arguments': {'user_id': '123'}}]
    function_schemas = get_user_data_schema
    mocker.patch.object(OpenAILLM, '_validate_single_function_inputs', side_effect=Exception('Test exception'))
    result = openai_llm._is_valid_inputs(inputs, function_schemas)
    assert not result, 'The method should return False when an exception occurs'
    mocked_logger.assert_called_once_with('Input validation error: Test exception')

def test_validate_single_function_inputs_missing_required_param(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    function_schema = example_function_schema
    inputs = {}
    result = openai_llm._validate_single_function_inputs(inputs, function_schema)
    assert not result, 'The method should return False when a required parameter is missing'
    expected_error_message = "Required input 'user_id' missing from query"
    mocked_logger.assert_called_once_with(expected_error_message)

def test_validate_single_function_inputs_incorrect_type(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')
    function_schema = example_function_schema
    inputs = {'user_id': 123}
    result = openai_llm._validate_single_function_inputs(inputs, function_schema)
    assert not result, 'The method should return False when input type is incorrect'
    expected_error_message = "Input type for 'user_id' is not string"
    mocked_logger.assert_called_once_with(expected_error_message)

def test_validate_single_function_inputs_exception_handling(self, openai_llm, mocker):
    mocked_logger = mocker.patch('semantic_router.utils.logger.logger.error')

    class SchemaSimulator:

        def __getitem__(self, item):
            raise Exception('Test exception')
    function_schema = SchemaSimulator()
    result = openai_llm._validate_single_function_inputs({'user_id': '123'}, function_schema)
    assert not result, 'The method should return False when an exception occurs'
    mocked_logger.assert_called_once_with('Single input validation error: Test exception')

class SchemaSimulator:

    def __getitem__(self, item):
        raise Exception('Test exception')

def __getitem__(self, item):
    raise Exception('Test exception')

class TestDenseEncoder:

    @pytest.fixture
    def base_encoder(self):
        return DenseEncoder(name='TestEncoder', score_threshold=0.5)

    def test_base_encoder_initialization(self, base_encoder):
        assert base_encoder.name == 'TestEncoder', 'Initialization of name failed'
        assert base_encoder.score_threshold == 0.5

    def test_base_encoder_call_method_not_implemented(self, base_encoder):
        with pytest.raises(NotImplementedError):
            base_encoder(['some', 'texts'])

def test_base_encoder_call_method_not_implemented(self, base_encoder):
    with pytest.raises(NotImplementedError):
        base_encoder(['some', 'texts'])

@pytest.fixture
def bedrock_encoder(mocker):
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
    return BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')

@pytest.fixture
def bedrock_encoder_with_cohere(mocker):
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
    return BedrockEncoder(name='cohere_model', access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')

class TestBedrockEncoder:

    def test_initialisation_with_default_values(self, bedrock_encoder):
        assert bedrock_encoder.input_type == 'search_query', 'Default input type not set correctly'
        assert bedrock_encoder.region == 'us-west-2', 'Region should be initialised'

    def test_initialisation_with_custom_values(self, mocker):
        name = 'custom_model'
        score_threshold = 0.5
        input_type = 'custom_input'
        bedrock_encoder = BedrockEncoder(name=name, score_threshold=score_threshold, input_type=input_type, access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
        assert bedrock_encoder.name == name, 'Custom name not set correctly'
        assert bedrock_encoder.region == 'us-west-2', 'Custom region not set correctly'
        assert bedrock_encoder.score_threshold == score_threshold, 'Custom score threshold not set correctly'
        assert bedrock_encoder.input_type == input_type, 'Custom input type not set correctly'

    def test_initialisation_with_session_token(self, mocker):
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        bedrock_encoder = BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
        assert bedrock_encoder.session_token == 'fake_token', 'Session token not set correctly'

    def test_initialisation_with_missing_access_key(self, mocker):
        mocker.patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'env_id'})
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        bedrock_encoder = BedrockEncoder(access_key_id=None, secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
        assert bedrock_encoder.access_key_id == 'env_id', 'Access key ID not set correctly from environment variable'

    def test_missing_access_key_id(self, mocker):
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id=None, secret_access_key='fake_secret')

    def test_missing_secret_access_key(self, mocker):
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id='fake_id', secret_access_key=None)

    def test_initialisation_missing_env_variables(self, mocker):
        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id=None, secret_access_key=None, session_token=None, region=None)

    def test_failed_client_initialisation(self, mocker):
        mocker.patch.dict(os.environ, clear=True)
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client', side_effect=Exception('Initialization failed'))
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret')

    def test_call_method(self, bedrock_encoder):
        response_content = json.dumps({'embedding': [0.1, 0.2, 0.3]})
        response_body = BytesIO(response_content.encode('utf-8'))
        mock_response = {'body': response_body}
        bedrock_encoder.client.invoke_model.return_value = mock_response
        result = bedrock_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(item, list) for item in result)), 'Each item in result should be a list'
        assert result == [[0.1, 0.2, 0.3]], 'Embedding should be [0.1, 0.2, 0.3]'

    def test_call_with_expired_token(self, mocker, bedrock_encoder):
        from botocore.exceptions import ClientError
        error_response = {'Error': {'Code': 'ExpiredTokenException'}}
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client', return_value=None)

        def invoke_model_side_effect(*args, **kwargs):
            if not invoke_model_side_effect.expired_token_raised:
                invoke_model_side_effect.expired_token_raised = True
                raise ClientError(error_response, 'invoke_model')
            else:
                return {'body': BytesIO(json.dumps({'embedding': [0.1, 0.2, 0.3]}).encode('utf-8'))}
        invoke_model_side_effect.expired_token_raised = False
        bedrock_encoder.client.invoke_model.side_effect = invoke_model_side_effect
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])
        bedrock_encoder._initialize_client.assert_called_once_with(bedrock_encoder.access_key_id, bedrock_encoder.secret_access_key, None, bedrock_encoder.region)

    def test_raises_value_error_if_call_to_bedrock_fails(self, bedrock_encoder):
        bedrock_encoder.client.invoke_model.side_effect = Exception('Bedrock call failed.')
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])

    def test_call_with_unknown_model_name(self, bedrock_encoder):
        bedrock_encoder.name = 'unknown_model'
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])

    def test_chunking_functionality(self, bedrock_encoder):
        docs = ['This is a long text that needs to be chunked properly.']
        chunked_docs = bedrock_encoder.chunk_strings(docs, MAX_WORDS=5)
        assert isinstance(chunked_docs, list), 'Chunked result should be a list'
        assert len(chunked_docs[0]) > 1, 'Document should be chunked into multiple parts'
        assert all((isinstance(chunk, str) for chunk in chunked_docs[0])), 'Chunks should be strings'

    def test_get_env_variable(self):
        var_name = 'TEST_ENV_VAR'
        default_value = 'default'
        os.environ[var_name] = 'env_value'
        assert BedrockEncoder.get_env_variable(var_name, None) == 'env_value'
        assert BedrockEncoder.get_env_variable(var_name, None, default_value) == 'env_value'
        assert BedrockEncoder.get_env_variable('NON_EXISTENT_VAR', None, default_value) == default_value

    def test_get_env_variable_missing(self):
        with pytest.raises(ValueError):
            BedrockEncoder.get_env_variable('MISSING_VAR', None)

    def test_uninitialised_client(self, bedrock_encoder):
        bedrock_encoder.client = None
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])

    def test_missing_env_variables(self, mocker):
        mocker.patch.dict(os.environ, clear=True)
        with pytest.raises(ValueError):
            BedrockEncoder()

def test_initialisation_with_custom_values(self, mocker):
    name = 'custom_model'
    score_threshold = 0.5
    input_type = 'custom_input'
    bedrock_encoder = BedrockEncoder(name=name, score_threshold=score_threshold, input_type=input_type, access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
    assert bedrock_encoder.name == name, 'Custom name not set correctly'
    assert bedrock_encoder.region == 'us-west-2', 'Custom region not set correctly'
    assert bedrock_encoder.score_threshold == score_threshold, 'Custom score threshold not set correctly'
    assert bedrock_encoder.input_type == input_type, 'Custom input type not set correctly'

def test_initialisation_with_session_token(self, mocker):
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
    bedrock_encoder = BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
    assert bedrock_encoder.session_token == 'fake_token', 'Session token not set correctly'

def test_initialisation_with_missing_access_key(self, mocker):
    mocker.patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'env_id'})
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
    bedrock_encoder = BedrockEncoder(access_key_id=None, secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
    assert bedrock_encoder.access_key_id == 'env_id', 'Access key ID not set correctly from environment variable'

def test_missing_access_key_id(self, mocker):
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
    with pytest.raises(ValueError):
        BedrockEncoder(access_key_id=None, secret_access_key='fake_secret')

def test_missing_secret_access_key(self, mocker):
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
    with pytest.raises(ValueError):
        BedrockEncoder(access_key_id='fake_id', secret_access_key=None)

def test_initialisation_missing_env_variables(self, mocker):
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(ValueError):
        BedrockEncoder(access_key_id=None, secret_access_key=None, session_token=None, region=None)

def test_failed_client_initialisation(self, mocker):
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client', side_effect=Exception('Initialization failed'))
    with pytest.raises(ValueError):
        BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret')

def test_call_with_expired_token(self, mocker, bedrock_encoder):
    from botocore.exceptions import ClientError
    error_response = {'Error': {'Code': 'ExpiredTokenException'}}
    mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client', return_value=None)

    def invoke_model_side_effect(*args, **kwargs):
        if not invoke_model_side_effect.expired_token_raised:
            invoke_model_side_effect.expired_token_raised = True
            raise ClientError(error_response, 'invoke_model')
        else:
            return {'body': BytesIO(json.dumps({'embedding': [0.1, 0.2, 0.3]}).encode('utf-8'))}
    invoke_model_side_effect.expired_token_raised = False
    bedrock_encoder.client.invoke_model.side_effect = invoke_model_side_effect
    with pytest.raises(ValueError):
        bedrock_encoder(['test'])
    bedrock_encoder._initialize_client.assert_called_once_with(bedrock_encoder.access_key_id, bedrock_encoder.secret_access_key, None, bedrock_encoder.region)

def test_raises_value_error_if_call_to_bedrock_fails(self, bedrock_encoder):
    bedrock_encoder.client.invoke_model.side_effect = Exception('Bedrock call failed.')
    with pytest.raises(ValueError):
        bedrock_encoder(['test'])

def test_call_with_unknown_model_name(self, bedrock_encoder):
    bedrock_encoder.name = 'unknown_model'
    with pytest.raises(ValueError):
        bedrock_encoder(['test'])

def test_uninitialised_client(self, bedrock_encoder):
    bedrock_encoder.client = None
    with pytest.raises(ValueError):
        bedrock_encoder(['test'])

def test_missing_env_variables(self, mocker):
    mocker.patch.dict(os.environ, clear=True)
    with pytest.raises(ValueError):
        BedrockEncoder()

@pytest.fixture
def mock_openai_client():
    with patch('openai.Client') as mock_client:
        yield mock_client

@pytest.fixture
def mock_openai_async_client():
    with patch('openai.AsyncClient') as mock_async_client:
        yield mock_async_client

class TestOpenAIEncoder:

    def test_openai_encoder_init_success(self, mocker):
        side_effect = ['fake-model-name', 'fake-api-key', 'fake-org-id']
        mocker.patch('os.getenv', side_effect=side_effect)
        encoder = OpenAIEncoder()
        assert encoder._client is not None

    def test_openai_encoder_init_no_api_key(self, mocker):
        mocker.patch('os.getenv', return_value=None)
        with pytest.raises(ValueError) as _:
            OpenAIEncoder()

    def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
        openai_encoder._client = None
        with pytest.raises(ValueError) as e:
            openai_encoder(['test document'])
        assert 'OpenAI client is not initialized.' in str(e.value)

    def test_openai_encoder_init_exception(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('openai.Client', side_effect=Exception('Initialization error'))
        with pytest.raises(ValueError) as e:
            OpenAIEncoder()
        assert 'OpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

    def test_openai_encoder_call_success(self, openai_encoder, mocker):
        mock_embeddings = mocker.Mock()
        mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('time.sleep', return_value=None)
        mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
        mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
        responses = [OpenAIError('OpenAI error'), mock_response]
        mocker.patch.object(openai_encoder._client.embeddings, 'create', side_effect=responses)
        with patch('semantic_router.encoders.openai.sleep', return_value=None):
            embeddings = openai_encoder(['test document'])
        assert embeddings == [[0.1, 0.2]]

    def test_openai_encoder_call_failure_non_openai_error(self, openai_encoder, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('time.sleep', return_value=None)
        mocker.patch.object(openai_encoder._client.embeddings, 'create', side_effect=Exception('Non-OpenAIError'))
        with patch('semantic_router.encoders.openai.sleep', return_value=None):
            with pytest.raises(ValueError) as e:
                openai_encoder(['test document'])
        assert 'OpenAI API call failed. Error: Non-OpenAIError' in str(e.value)

    def test_openai_encoder_call_successful_retry(self, openai_encoder, mocker):
        mock_embeddings = mocker.Mock()
        mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('time.sleep', return_value=None)
        mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
        mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
        responses = [OpenAIError('OpenAI error'), mock_response]
        mocker.patch.object(openai_encoder._client.embeddings, 'create', side_effect=responses)
        with patch('semantic_router.encoders.openai.sleep', return_value=None):
            embeddings = openai_encoder(['test document'])
        assert embeddings == [[0.1, 0.2]]

    def test_retry_logic_sync(self, openai_encoder, mock_openai_client, mocker):
        mock_create = Mock(side_effect=[OpenAIError('API error'), OpenAIError('API error'), CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 5, 'total_tokens': 5})])
        mock_openai_client.return_value.embeddings.create = mock_create
        mocker.patch('time.sleep', return_value=None)
        with patch('semantic_router.encoders.openai.sleep', return_value=None):
            result = openai_encoder(['test document'])
        assert result == [[0.1, 0.2, 0.3]]
        assert mock_create.call_count == 3

    def test_no_retry_on_max_retries_zero(self, openai_encoder, mock_openai_client):
        openai_encoder.max_retries = 0
        mock_create = Mock(side_effect=OpenAIError('API error'))
        mock_openai_client.return_value.embeddings.create = mock_create
        with pytest.raises(OpenAIError):
            openai_encoder(['test document'])
        assert mock_create.call_count == 1

    def test_retry_logic_sync_max_retries_exceeded(self, openai_encoder, mock_openai_client, mocker):
        mock_create = Mock(side_effect=OpenAIError('API error'))
        mock_openai_client.return_value.embeddings.create = mock_create
        mocker.patch('time.sleep', return_value=None)
        with patch('semantic_router.encoders.openai.sleep', return_value=None):
            with pytest.raises(OpenAIError):
                openai_encoder(['test document'])
        assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logic_async(self, openai_encoder, mock_openai_async_client, mocker):
        mock_create = AsyncMock(side_effect=[OpenAIError('API error'), OpenAIError('API error'), CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 5, 'total_tokens': 5})])
        mock_openai_async_client.return_value.embeddings.create = mock_create
        mocker.patch('asyncio.sleep', return_value=None)
        with patch('semantic_router.encoders.openai.asleep', return_value=None):
            result = await openai_encoder.acall(['test document'])
        assert result == [[0.1, 0.2, 0.3]]
        assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logic_async_max_retries_exceeded(self, openai_encoder, mock_openai_async_client, mocker):

        async def raise_error(*args, **kwargs):
            raise OpenAIError('API error')
        mock_create = Mock(side_effect=raise_error)
        mock_openai_async_client.return_value.embeddings.create = mock_create
        mocker.patch('asyncio.sleep', return_value=None)
        with patch('semantic_router.encoders.openai.asleep', return_value=None):
            with pytest.raises(OpenAIError):
                await openai_encoder.acall(['test document'])
        assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_max_retries_zero_async(self, openai_encoder, mock_openai_async_client):
        openai_encoder.max_retries = 0

        async def raise_error(*args, **kwargs):
            raise OpenAIError('API error')
        mock_create = AsyncMock(side_effect=raise_error)
        mock_openai_async_client.return_value.embeddings.create = mock_create
        with pytest.raises(OpenAIError):
            await openai_encoder.acall(['test document'])
        assert mock_create.call_count == 1

def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
    openai_encoder._client = None
    with pytest.raises(ValueError) as e:
        openai_encoder(['test document'])
    assert 'OpenAI client is not initialized.' in str(e.value)

def test_openai_encoder_init_exception(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('openai.Client', side_effect=Exception('Initialization error'))
    with pytest.raises(ValueError) as e:
        OpenAIEncoder()
    assert 'OpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

def test_openai_encoder_call_success(self, openai_encoder, mocker):
    mock_embeddings = mocker.Mock()
    mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('time.sleep', return_value=None)
    mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
    mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
    responses = [OpenAIError('OpenAI error'), mock_response]
    mocker.patch.object(openai_encoder._client.embeddings, 'create', side_effect=responses)
    with patch('semantic_router.encoders.openai.sleep', return_value=None):
        embeddings = openai_encoder(['test document'])
    assert embeddings == [[0.1, 0.2]]

def test_openai_encoder_call_failure_non_openai_error(self, openai_encoder, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('time.sleep', return_value=None)
    mocker.patch.object(openai_encoder._client.embeddings, 'create', side_effect=Exception('Non-OpenAIError'))
    with patch('semantic_router.encoders.openai.sleep', return_value=None):
        with pytest.raises(ValueError) as e:
            openai_encoder(['test document'])
    assert 'OpenAI API call failed. Error: Non-OpenAIError' in str(e.value)

def test_openai_encoder_call_successful_retry(self, openai_encoder, mocker):
    mock_embeddings = mocker.Mock()
    mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('time.sleep', return_value=None)
    mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
    mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
    responses = [OpenAIError('OpenAI error'), mock_response]
    mocker.patch.object(openai_encoder._client.embeddings, 'create', side_effect=responses)
    with patch('semantic_router.encoders.openai.sleep', return_value=None):
        embeddings = openai_encoder(['test document'])
    assert embeddings == [[0.1, 0.2]]

def test_retry_logic_sync(self, openai_encoder, mock_openai_client, mocker):
    mock_create = Mock(side_effect=[OpenAIError('API error'), OpenAIError('API error'), CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 5, 'total_tokens': 5})])
    mock_openai_client.return_value.embeddings.create = mock_create
    mocker.patch('time.sleep', return_value=None)
    with patch('semantic_router.encoders.openai.sleep', return_value=None):
        result = openai_encoder(['test document'])
    assert result == [[0.1, 0.2, 0.3]]
    assert mock_create.call_count == 3

def test_no_retry_on_max_retries_zero(self, openai_encoder, mock_openai_client):
    openai_encoder.max_retries = 0
    mock_create = Mock(side_effect=OpenAIError('API error'))
    mock_openai_client.return_value.embeddings.create = mock_create
    with pytest.raises(OpenAIError):
        openai_encoder(['test document'])
    assert mock_create.call_count == 1

def test_retry_logic_sync_max_retries_exceeded(self, openai_encoder, mock_openai_client, mocker):
    mock_create = Mock(side_effect=OpenAIError('API error'))
    mock_openai_client.return_value.embeddings.create = mock_create
    mocker.patch('time.sleep', return_value=None)
    with patch('semantic_router.encoders.openai.sleep', return_value=None):
        with pytest.raises(OpenAIError):
            openai_encoder(['test document'])
    assert mock_create.call_count == 3

@pytest.fixture
def mock_ollama_client():
    with patch('ollama.Client') as mock_client:
        yield mock_client

class TestOllamaEncoder:

    def test_ollama_encoder_init_success(self, mocker):
        mocker.patch('ollama.Client', return_value=Mock())
        encoder = OllamaEncoder(base_url='http://localhost:11434')
        assert encoder.client is not None
        assert encoder.type == 'ollama'

    def test_ollama_encoder_init_import_error(self, mocker):
        mocker.patch.dict('sys.modules', {'ollama': None})
        with patch('builtins.__import__', side_effect=ImportError("No module named 'ollama'")):
            with pytest.raises(ImportError):
                OllamaEncoder(base_url='http://localhost:11434')

    def test_ollama_encoder_call_success(self, mocker):
        mock_client = Mock()
        mock_embed_result = Mock()
        mock_embed_result.embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_client.embed.return_value = mock_embed_result
        mocker.patch('ollama.Client', return_value=mock_client)
        encoder = OllamaEncoder(base_url='http://localhost:11434')
        encoder.client = mock_client
        docs = ['doc1', 'doc2']
        result = encoder(docs)
        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_client.embed.assert_called_once_with(model=encoder.name, input=docs)

    def test_ollama_encoder_call_client_not_initialized(self, mocker):
        encoder = OllamaEncoder(base_url='http://localhost:11434')
        encoder.client = None
        with pytest.raises(ValueError) as e:
            encoder(['doc1'])
        assert 'OLLAMA Platform client is not initialized.' in str(e.value)

    def test_ollama_encoder_call_api_error(self, mocker):
        mock_client = Mock()
        mock_client.embed.side_effect = Exception('API error')
        mocker.patch('ollama.Client', return_value=mock_client)
        encoder = OllamaEncoder(base_url='http://localhost:11434')
        encoder.client = mock_client
        with pytest.raises(ValueError) as e:
            encoder(['doc1'])
        assert 'OLLAMA API call failed. Error: API error' in str(e.value)

    def test_ollama_encoder_uses_env_base_url(self, mocker):
        test_url = 'http://env-ollama:1234'
        mock_client = Mock()
        mock_client.host = test_url
        mocker.patch('ollama.Client', return_value=mock_client)
        with patch.dict(os.environ, {'OLLAMA_BASE_URL': test_url}):
            encoder = OllamaEncoder()
            assert encoder.client is not None
            assert encoder.client.host == test_url

def test_ollama_encoder_init_success(self, mocker):
    mocker.patch('ollama.Client', return_value=Mock())
    encoder = OllamaEncoder(base_url='http://localhost:11434')
    assert encoder.client is not None
    assert encoder.type == 'ollama'

def test_ollama_encoder_init_import_error(self, mocker):
    mocker.patch.dict('sys.modules', {'ollama': None})
    with patch('builtins.__import__', side_effect=ImportError("No module named 'ollama'")):
        with pytest.raises(ImportError):
            OllamaEncoder(base_url='http://localhost:11434')

def test_ollama_encoder_call_success(self, mocker):
    mock_client = Mock()
    mock_embed_result = Mock()
    mock_embed_result.embeddings = [[0.1, 0.2], [0.3, 0.4]]
    mock_client.embed.return_value = mock_embed_result
    mocker.patch('ollama.Client', return_value=mock_client)
    encoder = OllamaEncoder(base_url='http://localhost:11434')
    encoder.client = mock_client
    docs = ['doc1', 'doc2']
    result = encoder(docs)
    assert result == [[0.1, 0.2], [0.3, 0.4]]
    mock_client.embed.assert_called_once_with(model=encoder.name, input=docs)

def test_ollama_encoder_call_client_not_initialized(self, mocker):
    encoder = OllamaEncoder(base_url='http://localhost:11434')
    encoder.client = None
    with pytest.raises(ValueError) as e:
        encoder(['doc1'])
    assert 'OLLAMA Platform client is not initialized.' in str(e.value)

def test_ollama_encoder_call_api_error(self, mocker):
    mock_client = Mock()
    mock_client.embed.side_effect = Exception('API error')
    mocker.patch('ollama.Client', return_value=mock_client)
    encoder = OllamaEncoder(base_url='http://localhost:11434')
    encoder.client = mock_client
    with pytest.raises(ValueError) as e:
        encoder(['doc1'])
    assert 'OLLAMA API call failed. Error: API error' in str(e.value)

def test_ollama_encoder_uses_env_base_url(self, mocker):
    test_url = 'http://env-ollama:1234'
    mock_client = Mock()
    mock_client.host = test_url
    mocker.patch('ollama.Client', return_value=mock_client)
    with patch.dict(os.environ, {'OLLAMA_BASE_URL': test_url}):
        encoder = OllamaEncoder()
        assert encoder.client is not None
        assert encoder.client.host == test_url

@pytest.fixture
def mock_litellm(mocker):
    mock_embed = litellm.EmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')])
    mocker.patch.object(litellm, 'embedding', return_value=mock_embed)
    return mock_embed

@pytest.mark.parametrize('provider, model_in, model_name, api_key_env_var, encoder', matrix)
class TestEncoders:

    def test_initialization_with_api_key(self, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        enc = encoder(model_in)
        assert enc.name == model_name, 'Default name not set correctly'
        assert enc.type == provider, 'Default type/provider not set correctly'

    def test_initialization_without_api_key(self, monkeypatch, provider, model_in, model_name, api_key_env_var, encoder):
        monkeypatch.delenv(api_key_env_var, raising=False)
        with pytest.raises(ValueError):
            encoder()

    def test_call_method(self, mock_litellm, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        result = encoder(model_in)(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        litellm.embedding.assert_called_once()

    def test_returns_list_of_embeddings_for_valid_input(self, mock_litellm, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        result = encoder(model_in)(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        litellm.embedding.assert_called_once()

    def test_handles_multiple_inputs_correctly(self, mocker, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        mock_embed = litellm.EmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding'), Embedding(embedding=[0.4, 0.5, 0.6], index=1, object='embedding')])
        mocker.patch.object(litellm, 'embedding', return_value=mock_embed)
        result = encoder(model_in)(['test1', 'test2'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        litellm.embedding.assert_called_once()

    def test_call_method_raises_error_on_api_failure(self, mocker, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        mocker.patch.object(litellm, 'embedding', side_effect=Exception('API call failed'))
        with pytest.raises(ValueError):
            encoder(model_in)(['test'])

def test_initialization_without_api_key(self, monkeypatch, provider, model_in, model_name, api_key_env_var, encoder):
    monkeypatch.delenv(api_key_env_var, raising=False)
    with pytest.raises(ValueError):
        encoder()

def test_handles_multiple_inputs_correctly(self, mocker, provider, model_in, model_name, api_key_env_var, encoder):
    os.environ[api_key_env_var] = 'test_api_key'
    mock_embed = litellm.EmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding'), Embedding(embedding=[0.4, 0.5, 0.6], index=1, object='embedding')])
    mocker.patch.object(litellm, 'embedding', return_value=mock_embed)
    result = encoder(model_in)(['test1', 'test2'])
    assert isinstance(result, list), 'Result should be a list'
    assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
    litellm.embedding.assert_called_once()

def test_call_method_raises_error_on_api_failure(self, mocker, provider, model_in, model_name, api_key_env_var, encoder):
    os.environ[api_key_env_var] = 'test_api_key'
    mocker.patch.object(litellm, 'embedding', side_effect=Exception('API call failed'))
    with pytest.raises(ValueError):
        encoder(model_in)(['test'])

@pytest.fixture
def mock_openai_client():
    with patch('openai.AzureOpenAI') as mock_client:
        yield mock_client

@pytest.fixture
def mock_openai_async_client():
    with patch('openai.AsyncAzureOpenAI') as mock_async_client:
        yield mock_async_client

@pytest.fixture
def openai_encoder(mock_openai_client, mock_openai_async_client):
    return AzureOpenAIEncoder(azure_endpoint='https://test-endpoint.openai.azure.com', api_version='test-version', api_key='test_api_key', http_client_options={'timeout': 10}, deployment_name='test-deployment', dimensions=1536, max_retries=2)

class TestAzureOpenAIEncoder:

    def test_openai_encoder_init_success(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        encoder = AzureOpenAIEncoder()
        assert encoder.client is not None

    def test_openai_encoder_init_no_api_key(self, mocker):
        mocker.patch('os.getenv', return_value=None)
        with pytest.raises(ValueError) as _:
            AzureOpenAIEncoder()

    def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
        openai_encoder.client = None
        with pytest.raises(ValueError) as e:
            openai_encoder(['test document'])
        assert 'OpenAI client is not initialized.' in str(e.value)

    def test_openai_encoder_init_exception(self, mocker):
        mocker.patch('os.getenv', return_value='fake-api-stuff')
        mocker.patch('openai.AzureOpenAI', side_effect=Exception('Initialization error'))
        with pytest.raises(ValueError) as e:
            AzureOpenAIEncoder()
        assert 'OpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

    def test_openai_encoder_call_success(self, openai_encoder, mocker):
        mock_embeddings = mocker.Mock()
        mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('time.sleep', return_value=None)
        mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
        mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
        responses = [OpenAIError('OpenAI error'), mock_response]
        mocker.patch.object(openai_encoder.client.embeddings, 'create', side_effect=responses)
        with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
            embeddings = openai_encoder(['test document'])
        assert embeddings == [[0.1, 0.2]]

    def test_openai_encoder_call_failure_non_openai_error(self, openai_encoder, mocker):
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('time.sleep', return_value=None)
        mocker.patch.object(openai_encoder.client.embeddings, 'create', side_effect=Exception('Non-OpenAIError'))
        with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
            with pytest.raises(ValueError) as e:
                openai_encoder(['test document'])
        assert 'OpenAI API call failed. Error: Non-OpenAIError' in str(e.value)

    def test_openai_encoder_call_successful_retry(self, openai_encoder, mocker):
        mock_embeddings = mocker.Mock()
        mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
        mocker.patch('os.getenv', return_value='fake-api-key')
        mocker.patch('time.sleep', return_value=None)
        mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
        mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
        responses = [OpenAIError('OpenAI error'), mock_response]
        mocker.patch.object(openai_encoder.client.embeddings, 'create', side_effect=responses)
        with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
            embeddings = openai_encoder(['test document'])
        assert embeddings == [[0.1, 0.2]]

    def test_retry_logic_sync(self, openai_encoder, mock_openai_client, mocker):
        mock_create = Mock(side_effect=[OpenAIError('API error'), OpenAIError('API error'), CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 5, 'total_tokens': 5})])
        mock_openai_client.return_value.embeddings.create = mock_create
        mocker.patch('time.sleep', return_value=None)
        with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
            result = openai_encoder(['test document'])
        assert result == [[0.1, 0.2, 0.3]]
        assert mock_create.call_count == 3

    def test_no_retry_on_max_retries_zero(self, openai_encoder, mock_openai_client):
        openai_encoder.max_retries = 0
        mock_create = Mock(side_effect=OpenAIError('API error'))
        mock_openai_client.return_value.embeddings.create = mock_create
        with pytest.raises(OpenAIError):
            openai_encoder(['test document'])
        assert mock_create.call_count == 1

    def test_retry_logic_sync_max_retries_exceeded(self, openai_encoder, mock_openai_client, mocker):
        mock_create = Mock(side_effect=OpenAIError('API error'))
        mock_openai_client.return_value.embeddings.create = mock_create
        mocker.patch('time.sleep', return_value=None)
        with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
            with pytest.raises(OpenAIError):
                openai_encoder(['test document'])
        assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logic_async(self, openai_encoder, mock_openai_async_client, mocker):
        mock_create = AsyncMock(side_effect=[OpenAIError('API error'), OpenAIError('API error'), CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 5, 'total_tokens': 5})])
        mock_openai_async_client.return_value.embeddings.create = mock_create
        mocker.patch('asyncio.sleep', return_value=None)
        with patch('semantic_router.encoders.azure_openai.asleep', return_value=None):
            result = await openai_encoder.acall(['test document'])
        assert result == [[0.1, 0.2, 0.3]]
        assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logic_async_max_retries_exceeded(self, openai_encoder, mock_openai_async_client, mocker):

        async def raise_error(*args, **kwargs):
            raise OpenAIError('API error')
        mock_create = Mock(side_effect=raise_error)
        mock_openai_async_client.return_value.embeddings.create = mock_create
        mocker.patch('asyncio.sleep', return_value=None)
        with patch('semantic_router.encoders.azure_openai.asleep', return_value=None):
            with pytest.raises(OpenAIError):
                await openai_encoder.acall(['test document'])
        assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_max_retries_zero_async(self, openai_encoder, mock_openai_async_client):
        openai_encoder.max_retries = 0

        async def raise_error(*args, **kwargs):
            raise OpenAIError('API error')
        mock_create = AsyncMock(side_effect=raise_error)
        mock_openai_async_client.return_value.embeddings.create = mock_create
        with pytest.raises(OpenAIError):
            await openai_encoder.acall(['test document'])
        assert mock_create.call_count == 1

def test_openai_encoder_init_success(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    encoder = AzureOpenAIEncoder()
    assert encoder.client is not None

def test_openai_encoder_init_no_api_key(self, mocker):
    mocker.patch('os.getenv', return_value=None)
    with pytest.raises(ValueError) as _:
        AzureOpenAIEncoder()

def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
    openai_encoder.client = None
    with pytest.raises(ValueError) as e:
        openai_encoder(['test document'])
    assert 'OpenAI client is not initialized.' in str(e.value)

def test_openai_encoder_init_exception(self, mocker):
    mocker.patch('os.getenv', return_value='fake-api-stuff')
    mocker.patch('openai.AzureOpenAI', side_effect=Exception('Initialization error'))
    with pytest.raises(ValueError) as e:
        AzureOpenAIEncoder()
    assert 'OpenAI API client failed to initialize. Error: Initialization error' in str(e.value)

def test_openai_encoder_call_success(self, openai_encoder, mocker):
    mock_embeddings = mocker.Mock()
    mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('time.sleep', return_value=None)
    mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
    mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
    responses = [OpenAIError('OpenAI error'), mock_response]
    mocker.patch.object(openai_encoder.client.embeddings, 'create', side_effect=responses)
    with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
        embeddings = openai_encoder(['test document'])
    assert embeddings == [[0.1, 0.2]]

def test_openai_encoder_call_failure_non_openai_error(self, openai_encoder, mocker):
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('time.sleep', return_value=None)
    mocker.patch.object(openai_encoder.client.embeddings, 'create', side_effect=Exception('Non-OpenAIError'))
    with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
        with pytest.raises(ValueError) as e:
            openai_encoder(['test document'])
    assert 'OpenAI API call failed. Error: Non-OpenAIError' in str(e.value)

def test_openai_encoder_call_successful_retry(self, openai_encoder, mocker):
    mock_embeddings = mocker.Mock()
    mock_embeddings.data = [Embedding(embedding=[0.1, 0.2], index=0, object='embedding')]
    mocker.patch('os.getenv', return_value='fake-api-key')
    mocker.patch('time.sleep', return_value=None)
    mock_embedding = Embedding(index=0, object='embedding', embedding=[0.1, 0.2])
    mock_response = CreateEmbeddingResponse(model='text-embedding-ada-002', object='list', usage=Usage(prompt_tokens=0, total_tokens=20), data=[mock_embedding])
    responses = [OpenAIError('OpenAI error'), mock_response]
    mocker.patch.object(openai_encoder.client.embeddings, 'create', side_effect=responses)
    with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
        embeddings = openai_encoder(['test document'])
    assert embeddings == [[0.1, 0.2]]

def test_retry_logic_sync(self, openai_encoder, mock_openai_client, mocker):
    mock_create = Mock(side_effect=[OpenAIError('API error'), OpenAIError('API error'), CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 5, 'total_tokens': 5})])
    mock_openai_client.return_value.embeddings.create = mock_create
    mocker.patch('time.sleep', return_value=None)
    with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
        result = openai_encoder(['test document'])
    assert result == [[0.1, 0.2, 0.3]]
    assert mock_create.call_count == 3

def test_no_retry_on_max_retries_zero(self, openai_encoder, mock_openai_client):
    openai_encoder.max_retries = 0
    mock_create = Mock(side_effect=OpenAIError('API error'))
    mock_openai_client.return_value.embeddings.create = mock_create
    with pytest.raises(OpenAIError):
        openai_encoder(['test document'])
    assert mock_create.call_count == 1

def test_retry_logic_sync_max_retries_exceeded(self, openai_encoder, mock_openai_client, mocker):
    mock_create = Mock(side_effect=OpenAIError('API error'))
    mock_openai_client.return_value.embeddings.create = mock_create
    mocker.patch('time.sleep', return_value=None)
    with patch('semantic_router.encoders.azure_openai.sleep', return_value=None):
        with pytest.raises(OpenAIError):
            openai_encoder(['test document'])
    assert mock_create.call_count == 3

@pytest.fixture
def google_encoder(mocker):
    mocker.patch('google.cloud.aiplatform.init')
    mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
    return GoogleEncoder(project_id='test_project_id')

class TestGoogleEncoder:

    def test_initialization_with_project_id(self, google_encoder):
        assert google_encoder.client is not None, 'Client should be initialized'
        assert google_encoder.name == 'textembedding-gecko@003', 'Default name not set correctly'

    def test_initialization_without_project_id(self, mocker, monkeypatch):
        monkeypatch.delenv('GOOGLE_PROJECT_ID', raising=False)
        mocker.patch('google.cloud.aiplatform.init')
        mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
        with pytest.raises(ValueError):
            GoogleEncoder()

    def test_call_method(self, google_encoder, mocker):
        mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False))]
        mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
        result = google_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        google_encoder.client.get_embeddings.assert_called_once()

    def test_returns_list_of_embeddings_for_valid_input(self, google_encoder, mocker):
        mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False))]
        mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
        result = google_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        google_encoder.client.get_embeddings.assert_called_once()

    def test_handles_multiple_inputs_correctly(self, google_encoder, mocker):
        mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False)), TextEmbedding(values=[0.4, 0.5, 0.6], statistics=TextEmbeddingStatistics(token_count=6, truncated=False))]
        mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
        result = google_encoder(['test1', 'test2'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        google_encoder.client.get_embeddings.assert_called_once()

    def test_raises_value_error_if_project_id_is_none(self, mocker, monkeypatch):
        monkeypatch.delenv('GOOGLE_PROJECT_ID', raising=False)
        mocker.patch('google.cloud.aiplatform.init')
        mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
        with pytest.raises(ValueError):
            GoogleEncoder()

    def test_raises_value_error_if_google_client_fails_to_initialize(self, mocker):
        mocker.patch('google.cloud.aiplatform.init', side_effect=Exception('Failed to initialize client'))
        with pytest.raises(ValueError):
            GoogleEncoder(project_id='test_project_id')

    def test_raises_value_error_if_google_client_is_not_initialized(self, mocker):
        mocker.patch('google.cloud.aiplatform.init')
        mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained', return_value=None)
        encoder = GoogleEncoder(project_id='test_project_id')
        with pytest.raises(ValueError):
            encoder(['test'])

    def test_call_method_raises_error_on_api_failure(self, google_encoder, mocker):
        mocker.patch.object(google_encoder.client, 'get_embeddings', side_effect=GoogleAPICallError('API call failed'))
        with pytest.raises(ValueError):
            google_encoder(['test'])

def test_initialization_without_project_id(self, mocker, monkeypatch):
    monkeypatch.delenv('GOOGLE_PROJECT_ID', raising=False)
    mocker.patch('google.cloud.aiplatform.init')
    mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
    with pytest.raises(ValueError):
        GoogleEncoder()

def test_raises_value_error_if_project_id_is_none(self, mocker, monkeypatch):
    monkeypatch.delenv('GOOGLE_PROJECT_ID', raising=False)
    mocker.patch('google.cloud.aiplatform.init')
    mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
    with pytest.raises(ValueError):
        GoogleEncoder()

def test_raises_value_error_if_google_client_fails_to_initialize(self, mocker):
    mocker.patch('google.cloud.aiplatform.init', side_effect=Exception('Failed to initialize client'))
    with pytest.raises(ValueError):
        GoogleEncoder(project_id='test_project_id')

def test_raises_value_error_if_google_client_is_not_initialized(self, mocker):
    mocker.patch('google.cloud.aiplatform.init')
    mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained', return_value=None)
    encoder = GoogleEncoder(project_id='test_project_id')
    with pytest.raises(ValueError):
        encoder(['test'])

class TestClipEncoder:

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder__import_errors_transformers(self):
        with patch.dict('sys.modules', {'transformers': None}):
            with pytest.raises(ImportError) as error:
                CLIPEncoder()
        assert 'install transformers' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder__import_errors_torch(self):
        with patch.dict('sys.modules', {'torch': None}):
            with pytest.raises(ImportError) as error:
                CLIPEncoder()
        assert 'install Pytorch' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_initialization(self):
        clip_encoder = CLIPEncoder(name=test_model_name)
        assert clip_encoder.name == test_model_name
        assert clip_encoder.type == 'huggingface'
        assert clip_encoder.score_threshold == 0.2
        assert clip_encoder.device == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_call_text(self):
        clip_encoder = CLIPEncoder(name=test_model_name)
        embeddings = clip_encoder(['hello', 'world'])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == embed_dim

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_call_image(self, dummy_pil_image):
        clip_encoder = CLIPEncoder(name=test_model_name)
        encoded_images = clip_encoder([dummy_pil_image] * 3)
        assert len(encoded_images) == 3
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_call_misshaped(self, dummy_pil_image, misshaped_pil_image):
        clip_encoder = CLIPEncoder(name=test_model_name)
        encoded_images = clip_encoder([dummy_pil_image, misshaped_pil_image])
        assert len(encoded_images) == 2
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_device(self):
        clip_encoder = CLIPEncoder(name=test_model_name)
        device = clip_encoder._model.device.type
        assert device == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_ensure_rgb(self, dummy_black_and_white_img):
        clip_encoder = CLIPEncoder(name=test_model_name)
        rgb_image = clip_encoder._ensure_rgb(dummy_black_and_white_img)
        assert rgb_image.mode == 'RGB'
        assert np.array(rgb_image).shape == (224, 224, 3)

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder__import_errors_transformers(self):
    with patch.dict('sys.modules', {'transformers': None}):
        with pytest.raises(ImportError) as error:
            CLIPEncoder()
    assert 'install transformers' in str(error.value)

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder__import_errors_torch(self):
    with patch.dict('sys.modules', {'torch': None}):
        with pytest.raises(ImportError) as error:
            CLIPEncoder()
    assert 'install Pytorch' in str(error.value)

class TestHuggingFaceEncoder:

    def test_huggingface_encoder_import_errors_transformers(self):
        with patch.dict('sys.modules', {'transformers': None}):
            with pytest.raises(ImportError) as error:
                HuggingFaceEncoder()
        assert 'Please install transformers to use HuggingFaceEncoder' in str(error.value)

    def test_huggingface_encoder_import_errors_torch(self):
        with patch.dict('sys.modules', {'torch': None}):
            with pytest.raises(ImportError) as error:
                HuggingFaceEncoder()
        assert 'Please install transformers to use HuggingFaceEncoder' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_huggingface_encoder_mean_pooling(self):
        encoder = HuggingFaceEncoder(name=test_model_name)
        test_docs = ['This is a test', 'This is another test']
        embeddings = encoder(test_docs, pooling_strategy='mean')
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_docs)
        assert all((isinstance(embedding, list) for embedding in embeddings))
        assert all((len(embedding) > 0 for embedding in embeddings))

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_huggingface_encoder_max_pooling(self):
        encoder = HuggingFaceEncoder(name=test_model_name)
        test_docs = ['This is a test', 'This is another test']
        embeddings = encoder(test_docs, pooling_strategy='max')
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_docs)
        assert all((isinstance(embedding, list) for embedding in embeddings))
        assert all((len(embedding) > 0 for embedding in embeddings))

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_huggingface_encoder_normalized_embeddings(self):
        encoder = HuggingFaceEncoder(name=test_model_name)
        docs = ['This is a test document.', 'Another test document.']
        unnormalized_embeddings = encoder(docs, normalize_embeddings=False)
        normalized_embeddings = encoder(docs, normalize_embeddings=True)
        assert len(unnormalized_embeddings) == len(normalized_embeddings)
        for unnormalized, normalized in zip(unnormalized_embeddings, normalized_embeddings):
            norm_unnormalized = np.linalg.norm(unnormalized, ord=2)
            norm_normalized = np.linalg.norm(normalized, ord=2)
            assert np.isclose(norm_normalized, 1.0)
            np.testing.assert_allclose(normalized, np.divide(unnormalized, norm_unnormalized), rtol=1e-05, atol=1e-05)

def test_huggingface_encoder_import_errors_transformers(self):
    with patch.dict('sys.modules', {'transformers': None}):
        with pytest.raises(ImportError) as error:
            HuggingFaceEncoder()
    assert 'Please install transformers to use HuggingFaceEncoder' in str(error.value)

def test_huggingface_encoder_import_errors_torch(self):
    with patch.dict('sys.modules', {'torch': None}):
        with pytest.raises(ImportError) as error:
            HuggingFaceEncoder()
    assert 'Please install transformers to use HuggingFaceEncoder' in str(error.value)

class TestHFEndpointEncoder:

    def test_initialization(self, encoder):
        assert encoder.huggingface_url == 'https://api-inference.huggingface.co/models/bert-base-uncased'
        assert encoder.huggingface_api_key == 'test-api-key'
        assert encoder.score_threshold == 0.8

    def test_initialization_failure_no_api_key(self):
        with pytest.raises(ValueError) as exc_info:
            HFEndpointEncoder(huggingface_url='https://api-inference.huggingface.co/models/bert-base-uncased')
        assert "HuggingFace API key cannot be 'None'" in str(exc_info.value)

    def test_initialization_failure_no_url(self):
        with pytest.raises(ValueError) as exc_info:
            HFEndpointEncoder(huggingface_api_key='test-api-key')
        assert "HuggingFace endpoint url cannot be 'None'" in str(exc_info.value)

    def test_query_success(self, encoder, requests_mock):
        requests_mock.post('https://api-inference.huggingface.co/models/bert-base-uncased', json=[0.1, 0.2, 0.3], status_code=200)
        response = encoder.query({'inputs': 'Hello World!', 'parameters': {}})
        assert response == [0.1, 0.2, 0.3]

    def test_query_failure(self, encoder, requests_mock):
        requests_mock.post('https://api-inference.huggingface.co/models/bert-base-uncased', text='Error', status_code=400)
        with pytest.raises(ValueError) as exc_info:
            encoder.query({'inputs': 'Hello World!', 'parameters': {}})
        assert 'Query failed with status 400: Error' in str(exc_info.value)

    def test_encode_documents_success(self, encoder, requests_mock):
        requests_mock.post('https://api-inference.huggingface.co/models/bert-base-uncased', json=[0.1, 0.2, 0.3], status_code=200)
        embeddings = encoder(['Hello World!'])
        assert embeddings == [[0.1, 0.2, 0.3]]

def test_initialization_failure_no_api_key(self):
    with pytest.raises(ValueError) as exc_info:
        HFEndpointEncoder(huggingface_url='https://api-inference.huggingface.co/models/bert-base-uncased')
    assert "HuggingFace API key cannot be 'None'" in str(exc_info.value)

def test_initialization_failure_no_url(self):
    with pytest.raises(ValueError) as exc_info:
        HFEndpointEncoder(huggingface_api_key='test-api-key')
    assert "HuggingFace endpoint url cannot be 'None'" in str(exc_info.value)

def test_query_failure(self, encoder, requests_mock):
    requests_mock.post('https://api-inference.huggingface.co/models/bert-base-uncased', text='Error', status_code=400)
    with pytest.raises(ValueError) as exc_info:
        encoder.query({'inputs': 'Hello World!', 'parameters': {}})
    assert 'Query failed with status 400: Error' in str(exc_info.value)

class TestVitEncoder:

    def test_vit_encoder__import_errors_transformers(self):
        with patch.dict('sys.modules', {'transformers': None}):
            with pytest.raises(ImportError) as error:
                VitEncoder()
        assert 'Please install transformers to use VitEncoder' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_initialization(self):
        vit_encoder = VitEncoder(name=test_model_name)
        assert vit_encoder.name == test_model_name
        assert vit_encoder.type == 'huggingface'
        assert vit_encoder.score_threshold == 0.5
        assert vit_encoder.device == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_call(self, dummy_pil_image):
        vit_encoder = VitEncoder(name=test_model_name)
        encoded_images = vit_encoder([dummy_pil_image] * 3)
        assert len(encoded_images) == 3
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_call_misshaped(self, dummy_pil_image, misshaped_pil_image):
        vit_encoder = VitEncoder(name=test_model_name)
        encoded_images = vit_encoder([dummy_pil_image, misshaped_pil_image])
        assert len(encoded_images) == 2
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_process_images_device(self, dummy_pil_image):
        vit_encoder = VitEncoder(name=test_model_name)
        imgs = vit_encoder._process_images([dummy_pil_image] * 3)['pixel_values']
        assert imgs.device.type == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_ensure_rgb(self, dummy_black_and_white_img):
        vit_encoder = VitEncoder(name=test_model_name)
        rgb_image = vit_encoder._ensure_rgb(dummy_black_and_white_img)
        assert rgb_image.mode == 'RGB'
        assert np.array(rgb_image).shape == (224, 224, 3)

def test_vit_encoder__import_errors_transformers(self):
    with patch.dict('sys.modules', {'transformers': None}):
        with pytest.raises(ImportError) as error:
            VitEncoder()
    assert 'Please install transformers to use VitEncoder' in str(error.value)

class TestOpenAIEncoder:

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_init_success(self, openai_encoder):
        assert openai_encoder._client is not None

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_dims(self, openai_encoder):
        embeddings = openai_encoder(['test document'])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_call_truncation(self, openai_encoder):
        openai_encoder([long_doc])

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_call_no_truncation(self, openai_encoder):
        with pytest.raises(OpenAIError) as _:
            openai_encoder([long_doc], truncate=False)

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
        openai_encoder._client = None
        with pytest.raises(ValueError) as e:
            openai_encoder(['test document'])
        assert 'OpenAI client is not initialized.' in str(e.value)

@pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
    openai_encoder._client = None
    with pytest.raises(ValueError) as e:
        openai_encoder(['test document'])
    assert 'OpenAI client is not initialized.' in str(e.value)

