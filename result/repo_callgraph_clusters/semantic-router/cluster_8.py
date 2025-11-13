# Cluster 8

def is_valid(route_config: str) -> bool:
    """Check if the route config is valid.

    :param route_config: The route config to check.
    :type route_config: str
    :return: Whether the route config is valid.
    :rtype: bool
    """
    try:
        output_json = json.loads(route_config)
        required_keys = ['name', 'utterances']
        if isinstance(output_json, list):
            for item in output_json:
                missing_keys = [key for key in required_keys if key not in item]
                if missing_keys:
                    logger.warning(f'Missing keys in route config: {', '.join(missing_keys)}')
                    return False
            return True
        else:
            missing_keys = [key for key in required_keys if key not in output_json]
            if missing_keys:
                logger.warning(f'Missing keys in route config: {', '.join(missing_keys)}')
                return False
            else:
                return True
    except json.JSONDecodeError as e:
        logger.error(e)
        return False

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

def get_schemas_openai(items: List[Callable]) -> List[Dict[str, Any]]:
    """Get function schemas for the OpenAI LLM from a list of functions.

    :param items: The functions to get function schemas for.
    :type items: List[Callable]
    :return: The schemas for the OpenAI LLM.
    :rtype: List[Dict[str, Any]]
    """
    schemas = []
    for item in items:
        if not callable(item):
            raise ValueError('Provided item must be a callable function.')
        basic_schema = get_schema(item)
        function_schema = {'name': basic_schema['name'], 'description': basic_schema['description'], 'parameters': {'type': 'object', 'properties': {}, 'required': []}}
        signature = inspect.signature(item)
        docstring = inspect.getdoc(item)
        param_doc_regex = re.compile(':param (\\w+):(.*?)\\n(?=:\\w|$)', re.S)
        doc_params = param_doc_regex.findall(docstring) if docstring else []
        for param_name, param in signature.parameters.items():
            param_type = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any'
            param_description = 'No description available.'
            param_required = param.default is inspect.Parameter.empty
            for doc_param_name, doc_param_desc in doc_params:
                if doc_param_name == param_name:
                    param_description = doc_param_desc.strip()
                    break
            function_schema['parameters']['properties'][param_name] = {'type': convert_python_type_to_json_type(param_type), 'description': param_description}
            if param_required:
                function_schema['parameters']['required'].append(param_name)
        schemas.append({'type': 'function', 'function': function_schema})
    return schemas

class FunctionSchema:
    """Class that consumes a function and can return a schema required by
    different LLMs for function calling.
    """
    name: str = Field(description='The name of the function')
    description: str = Field(description='The description of the function')
    signature: str = Field(description='The signature of the function')
    output: str = Field(description='The output of the function')
    parameters: List[Parameter] = Field(description='The parameters of the function')

    def __init__(self, function: Union[Callable, BaseModel]):
        """Initialize the FunctionSchema.

        :param function: The function to consume.
        :type function: Union[Callable, BaseModel]
        """
        self.function = function
        if callable(function):
            self._process_function(function)
        elif isinstance(function, BaseModel):
            raise NotImplementedError('Pydantic BaseModel not implemented yet.')
        else:
            raise TypeError('Function must be a Callable or BaseModel')

    def _process_function(self, function: Callable):
        """Process the function to get the name, description, signature, and output.

        :param function: The function to process.
        :type function: Callable
        """
        self.name = function.__name__
        self.description = str(inspect.getdoc(function))
        self.signature = str(inspect.signature(function))
        self.output = str(inspect.signature(function).return_annotation)
        parameters = []
        for param in inspect.signature(function).parameters.values():
            parameters.append(Parameter(name=param.name, type=param.annotation.__name__, default=param.default, required=False if param.default is param.empty else True))
        self.parameters = parameters

    def to_ollama(self):
        """Convert the FunctionSchema to an Ollama-compatible function schema dictionary.

        :return: The function schema in dictionary format.
        :rtype: Dict[str, Any]
        """
        schema_dict = {'type': 'function', 'function': {'name': self.name, 'description': self.description, 'parameters': {'type': 'object', 'properties': {param.name: {'description': param.description if isinstance(param.description, str) else None, 'type': self._ollama_type_mapping(param.type)} for param in self.parameters}, 'required': [param.name for param in self.parameters if param.required]}}}
        return schema_dict

    def _ollama_type_mapping(self, param_type: str) -> str:
        """Map the parameter type to an Ollama-compatible type.

        :param param_type: The type of the parameter.
        :type param_type: str
        :return: The Ollama-compatible type.
        :rtype: str
        """
        if param_type == 'int':
            return 'number'
        elif param_type == 'float':
            return 'number'
        elif param_type == 'str':
            return 'string'
        elif param_type == 'bool':
            return 'boolean'
        else:
            return 'object'

def _process_function(self, function: Callable):
    """Process the function to get the name, description, signature, and output.

        :param function: The function to process.
        :type function: Callable
        """
    self.name = function.__name__
    self.description = str(inspect.getdoc(function))
    self.signature = str(inspect.signature(function))
    self.output = str(inspect.signature(function).return_annotation)
    parameters = []
    for param in inspect.signature(function).parameters.values():
        parameters.append(Parameter(name=param.name, type=param.annotation.__name__, default=param.default, required=False if param.default is param.empty else True))
    self.parameters = parameters

def get_schema_list(items: List[Union[BaseModel, Callable]]) -> List[Dict[str, Any]]:
    """Get a list of function schemas from a list of functions or Pydantic BaseModels.

    :param items: The functions or BaseModels to get the schemas for.
    :type items: List[Union[BaseModel, Callable]]
    :return: A list of function schemas.
    :rtype: List[Dict[str, Any]]
    """
    schemas = []
    for item in items:
        schema = get_schema(item)
        schemas.append(schema)
    return schemas

def get_schema(item: Union[BaseModel, Callable]) -> Dict[str, Any]:
    """Get a function schema from a function or Pydantic BaseModel.

    :param item: The function or BaseModel to get the schema for.
    :type item: Union[BaseModel, Callable]
    :return: The function schema.
    :rtype: Dict[str, Any]
    """
    if isinstance(item, BaseModel):
        signature_parts = []
        for field_name, field_model in item.__annotations__.items():
            field_info = item.__fields__[field_name]
            default_value = field_info.default
            if default_value:
                default_repr = repr(default_value)
                signature_part = f'{field_name}: {field_model.__name__} = {default_repr}'
            else:
                signature_part = f'{field_name}: {field_model.__name__}'
            signature_parts.append(signature_part)
        signature = f'({', '.join(signature_parts)}) -> str'
        schema = {'name': item.__class__.__name__, 'description': item.__doc__, 'signature': signature}
    else:
        schema = {'name': item.__name__, 'description': str(inspect.getdoc(item)), 'signature': str(inspect.signature(item)), 'output': str(inspect.signature(item).return_annotation)}
    return schema

class BaseIndex(BaseModel):
    """
    Base class for indices using Pydantic's BaseModel.
    This class outlines the expected interface for index classes.
    Actual method implementations should be provided in subclasses.
    """
    routes: Optional[np.ndarray] = None
    utterances: Optional[np.ndarray] = None
    dimensions: Union[int, None] = None
    type: str = 'base'
    init_async_index: bool = False
    index: Optional[Any] = None

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[Any], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs):
        """Add embeddings to the index.
        This method should be implemented by subclasses.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[Optional[List[Dict[str, Any]]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs):
        """Add vectors to the index asynchronously.
        This method should be implemented by subclasses.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        """
        logger.warning('Async method not implemented.')
        return self.add(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, **kwargs)

    def get_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the
        index, including additional metadata.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects.
        :type include_metadata: bool
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if self.index is None:
            logger.warning('Index is None, could not retrieve utterances.')
            return []
        _, metadata = self._get_all(include_metadata=True)
        route_tuples = parse_route_info(metadata=metadata)
        if not include_metadata:
            route_tuples = [x[:2] for x in route_tuples]
        return [Utterance.from_tuple(x) for x in route_tuples]

    async def aget_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the
        index, including additional metadata.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects.
        :type include_metadata: bool
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if self.index is None:
            logger.warning('Index is None, could not retrieve utterances.')
            return []
        _, metadata = await self._async_get_all(include_metadata=True)
        route_tuples = parse_route_info(metadata=metadata)
        if not include_metadata:
            route_tuples = [x[:2] for x in route_tuples]
        return [Utterance.from_tuple(x) for x in route_tuples]

    def get_routes(self) -> List[Route]:
        """Gets a list of route objects currently stored in the index.

        :return: A list of Route objects.
        :rtype: List[Route]
        """
        utterances = self.get_utterances(include_metadata=True)
        routes_dict: Dict[str, Route] = {}
        for utt in utterances:
            if utt.route not in routes_dict:
                routes_dict[utt.route] = Route(name=utt.route, utterances=[utt.utterance], function_schemas=utt.function_schemas, metadata=utt.metadata)
            else:
                routes_dict[utt.route].utterances.append(utt.utterance)
        routes: List[Route] = []
        for route_name, route in routes_dict.items():
            routes.append(route)
        return routes

    def _remove_and_sync(self, routes_to_delete: dict):
        """
        Remove embeddings in a routes syncing process from the index.
        This method should be implemented by subclasses.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def _async_remove_and_sync(self, routes_to_delete: dict):
        """
        Remove embeddings in a routes syncing process from the index asynchronously.
        This method should be implemented by subclasses.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        """
        logger.warning('Async method not implemented.')
        return self._remove_and_sync(routes_to_delete=routes_to_delete)

    def delete(self, route_name: str):
        """Deletes route by route name.
        This method should be implemented by subclasses.

        :param route_name: Name of the route to delete.
        :type route_name: str
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def adelete(self, route_name: str) -> list[str]:
        """Asynchronously delete specified route from index if it exists. Returns the IDs
        of the vectors deleted.
        This method should be implemented by subclasses.

        :param route_name: Name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted.
        :rtype: list[str]
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def describe(self) -> IndexConfig:
        """Returns an IndexConfig object with index details such as type, dimensions,
        and total vector count.
        This method should be implemented by subclasses.

        :return: An IndexConfig object.
        :rtype: IndexConfig
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.
        This method should be implemented by subclasses.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def ais_ready(self) -> bool:
        """Checks if the index is ready to be used asynchronously.
        This method should be implemented by subclasses.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query_vector and return top_k results.
        This method should be implemented by subclasses.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query_vector and return top_k results.
        This method should be implemented by subclasses.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def aget_routes(self):
        """
        Asynchronously get a list of route and utterance objects currently stored in the index.
        This method should be implemented by subclasses.

        :returns: A list of tuples, each containing a route name and an associated utterance.
        :rtype: list[tuple]
        :raises NotImplementedError: If the method is not implemented by the subclass.
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def delete_all(self):
        """Deletes all records from the index.
        This method should be implemented by subclasses.

        :raises NotImplementedError: If the method is not implemented by the subclass.
        """
        logger.warning('This method should be implemented by subclasses.')
        self.index = None
        self.routes = None
        self.utterances = None

    def delete_index(self):
        """Deletes or resets the index.
        This method should be implemented by subclasses.

        :raises NotImplementedError: If the method is not implemented by the subclass.
        """
        logger.warning('This method should be implemented by subclasses.')
        self.index = None

    async def adelete_index(self):
        """Deletes or resets the index asynchronously.
        This method should be implemented by subclasses.
        """
        logger.warning('This method should be implemented by subclasses.')
        self.index = None

    def _read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the index.

        :param field: The field to read.
        :type field: str
        :param scope: The scope to read.
        :type scope: str | None
        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        logger.warning('This method should be implemented by subclasses.')
        return ConfigParameter(field=field, value='', scope=scope)

    async def _async_read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the index asynchronously.

        :param field: The field to read.
        :type field: str
        :param scope: The scope to read.
        :type scope: str | None
        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        logger.warning('_async_read_config method not implemented.')
        return self._read_config(field=field, scope=scope)

    def _write_config(self, config: ConfigParameter) -> ConfigParameter:
        """Write a config parameter to the index.

        :param config: The config parameter to write.
        :type config: ConfigParameter
        :return: The config parameter that was written.
        :rtype: ConfigParameter
        """
        logger.warning('This method should be implemented by subclasses.')
        return config

    async def _async_write_config(self, config: ConfigParameter) -> ConfigParameter:
        """Write a config parameter to the index asynchronously.

        :param config: The config parameter to write.
        :type config: ConfigParameter
        :return: The config parameter that was written.
        :rtype: ConfigParameter
        """
        logger.warning('Async method not implemented.')
        return self._write_config(config=config)

    def _read_hash(self) -> ConfigParameter:
        """Read the hash of the previously written index.

        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        return self._read_config(field='sr_hash')

    async def _async_read_hash(self) -> ConfigParameter:
        """Read the hash of the previously written index asynchronously.

        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        return await self._async_read_config(field='sr_hash')

    def _is_locked(self, scope: str | None=None) -> bool:
        """Check if the index is locked for a given scope (if applicable).

        :param scope: The scope to check.
        :type scope: str | None
        :return: True if the index is locked, False otherwise.
        :rtype: bool
        """
        lock_config = self._read_config(field='sr_lock', scope=scope)
        if lock_config.value == 'True':
            return True
        elif lock_config.value == 'False' or not lock_config.value:
            return False
        else:
            raise ValueError(f'Invalid lock value: {lock_config.value}')

    async def _ais_locked(self, scope: str | None=None) -> bool:
        """Check if the index is locked for a given scope (if applicable).

        :param scope: The scope to check.
        :type scope: str | None
        :return: True if the index is locked, False otherwise.
        :rtype: bool
        """
        lock_config = await self._async_read_config(field='sr_lock', scope=scope)
        if lock_config.value == 'True':
            return True
        elif lock_config.value == 'False' or not lock_config.value:
            return False
        else:
            raise ValueError(f'Invalid lock value: {lock_config.value}')

    def lock(self, value: bool, wait: int=0, scope: str | None=None) -> ConfigParameter:
        """Lock/unlock the index for a given scope (if applicable). If index
        already locked/unlocked, raises ValueError.

        :param scope: The scope to lock.
        :type scope: str | None
        :param wait: The number of seconds to wait for the index to be unlocked, if
        set to 0, will raise an error if index is already locked/unlocked.
        :type wait: int
        :return: The config parameter that was locked.
        :rtype: ConfigParameter
        """
        start_time = datetime.now()
        while True:
            if self._is_locked(scope=scope) != value:
                break
            elif not value:
                break
            if (datetime.now() - start_time).total_seconds() < wait:
                time.sleep(RETRY_WAIT_TIME)
            else:
                raise ValueError(f'Index is already {('locked' if value else 'unlocked')}.')
        lock_param = ConfigParameter(field='sr_lock', value=str(value), scope=scope)
        self._write_config(lock_param)
        return lock_param

    async def alock(self, value: bool, wait: int=0, scope: str | None=None) -> ConfigParameter:
        """Lock/unlock the index for a given scope (if applicable). If index
        already locked/unlocked, raises ValueError.
        """
        start_time = datetime.now()
        while True:
            if await self._ais_locked(scope=scope) != value:
                break
            if (datetime.now() - start_time).total_seconds() < wait:
                await asyncio.sleep(RETRY_WAIT_TIME)
            else:
                raise ValueError(f'Index is already {('locked' if value else 'unlocked')}.')
        lock_param = ConfigParameter(field='sr_lock', value=str(value), scope=scope)
        await self._async_write_config(lock_param)
        return lock_param

    def _get_all(self, prefix: Optional[str]=None, include_metadata: bool=False):
        """Retrieves all vector IDs from the index.
        This method should be implemented by subclasses.

        :param prefix: The prefix to filter the vectors by.
        :type prefix: Optional[str]
        :param include_metadata: Whether to include metadata in the response.
        :type include_metadata: bool
        :return: A tuple containing a list of vector IDs and a list of metadata dictionaries.
        :rtype: tuple[list[str], list[dict]]
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def _async_get_all(self, prefix: Optional[str]=None, include_metadata: bool=False) -> tuple[list[str], list[dict]]:
        """Retrieves all vector IDs from the index asynchronously.
        This method should be implemented by subclasses.

        :param prefix: The prefix to filter the vectors by.
        :type prefix: Optional[str]
        :param include_metadata: Whether to include metadata in the response.
        :type include_metadata: bool
        :return: A tuple containing a list of vector IDs and a list of metadata dictionaries.
        :rtype: tuple[list[str], list[dict]]
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def _async_get_routes(self) -> List[Tuple]:
        """Asynchronously gets a list of route and utterance objects currently
        stored in the index, including additional metadata.

        :return: A list of tuples, each containing route, utterance, function
        schema and additional metadata.
        :rtype: List[Tuple]
        """
        if self.index is None:
            logger.warning('Index is None, could not retrieve route info.')
            return []
        _, metadata = await self._async_get_all(include_metadata=True)
        route_info = parse_route_info(metadata=metadata)
        return route_info
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def _init_index(self, force_create: bool=False) -> Union[Any, None]:
        """Initializing the index can be done after the object has been created
        to allow for the user to set the dimensions and other parameters.

        If the index doesn't exist and the dimensions are given, the index will
        be created. If the index exists, it will be returned. If the index doesn't
        exist and the dimensions are not given, the index will not be created and
        None will be returned.

        This method must be implemented by subclasses.

        :param force_create: If True, the index will be created even if the
            dimensions are not given (which will raise an error).
        :type force_create: bool, optional
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def _init_async_index(self, force_create: bool=False):
        """Initializing the index can be done after the object has been created
        to allow for the user to set the dimensions and other parameters.

        If the index doesn't exist and the dimensions are given, the index will
        be created. If the index exists, it will be returned. If the index doesn't
        exist and the dimensions are not given, the index will not be created and
        None will be returned.

        This method is used to initialize the index asynchronously.

        This method must be implemented by subclasses.

        :param force_create: If True, the index will be created even if the
            dimensions are not given (which will raise an error).
        :type force_create: bool, optional
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def __len__(self):
        """Returns the total number of vectors in the index. If the index is not initialized
        returns 0.

        :return: The total number of vectors.
        :rtype: int
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def alen(self):
        """Async version of __len__. Returns the total number of vectors in the index.
        Default implementation just calls the sync version.

        :return: The total number of vectors.
        :rtype: int
        """
        return len(self)

def get_routes(self) -> List[Route]:
    """Gets a list of route objects currently stored in the index.

        :return: A list of Route objects.
        :rtype: List[Route]
        """
    utterances = self.get_utterances(include_metadata=True)
    routes_dict: Dict[str, Route] = {}
    for utt in utterances:
        if utt.route not in routes_dict:
            routes_dict[utt.route] = Route(name=utt.route, utterances=[utt.utterance], function_schemas=utt.function_schemas, metadata=utt.metadata)
        else:
            routes_dict[utt.route].utterances.append(utt.utterance)
    routes: List[Route] = []
    for route_name, route in routes_dict.items():
        routes.append(route)
    return routes

def parse_route_info(metadata: List[Dict[str, Any]]) -> List[Tuple]:
    """Parses metadata from index to extract route, utterance, function
    schema and additional metadata.

    :param metadata: List of metadata dictionaries.
    :type metadata: List[Dict[str, Any]]
    :return: A list of tuples, each containing route, utterance, function schema and additional metadata.
    :rtype: List[Tuple]
    """
    route_info = []
    for record in metadata:
        sr_route = record.get('sr_route', '')
        sr_utterance = record.get('sr_utterance', '')
        sr_function_schema = json.loads(record.get('sr_function_schema', '{}'))
        if sr_function_schema == {} or sr_function_schema == 'null':
            sr_function_schema = None
        additional_metadata = {key: value for key, value in record.items() if key not in ['sr_route', 'sr_utterance', 'sr_function_schema']}
        if additional_metadata is None:
            additional_metadata = {}
        route_info.append((sr_route, sr_utterance, sr_function_schema, additional_metadata))
    return route_info

def clean_route_name(route_name: str) -> str:
    return route_name.strip().replace(' ', '-')

class PineconeIndex(BaseIndex):
    index_prefix: str = 'semantic-router--'
    api_key: Optional[str] = None
    index_name: str = 'index'
    dimensions: Union[int, None] = None
    metric: str = 'dotproduct'
    cloud: str = 'aws'
    region: str = 'us-east-1'
    host: str = ''
    client: Any = Field(default=None, exclude=True)
    index: Optional[Any] = Field(default=None, exclude=True)
    ServerlessSpec: Any = Field(default=None, exclude=True)
    namespace: Optional[str] = ''
    base_url: Optional[str] = None
    headers: dict[str, str] = {}
    index_host: Optional[str] = 'http://localhost:5080'
    init_async_index: bool = False

    def __init__(self, api_key: Optional[str]=None, index_name: str='index', dimensions: Optional[int]=None, metric: str='dotproduct', cloud: str='aws', region: str='us-east-1', host: str='', namespace: Optional[str]='', base_url: Optional[str]='https://api.pinecone.io', init_async_index: bool=False):
        """Initialize PineconeIndex.

        :param api_key: Pinecone API key.
        :type api_key: Optional[str]
        :param index_name: Name of the index.
        :type index_name: str
        :param dimensions: Dimensions of the index.
        :type dimensions: Optional[int]
        :param metric: Metric of the index.
        :type metric: str
        :param cloud: Cloud provider of the index.
        :type cloud: str
        :param region: Region of the index.
        :type region: str
        :param host: Host of the index.
        :type host: str
        :param namespace: Namespace of the index.
        :type namespace: Optional[str]
        :param base_url: Base URL of the Pinecone API.
        :type base_url: Optional[str]
        :param init_async_index: Whether to initialize the index asynchronously.
        :type init_async_index: bool
        """
        super().__init__()
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        if not self.api_key:
            raise ValueError('Pinecone API key is required.')
        self.headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json', 'User-Agent': 'source_tag=semanticrouter'}
        if base_url is not None or os.getenv('PINECONE_API_BASE_URL'):
            logger.info('Using pinecone remote API.')
            if os.getenv('PINECONE_API_BASE_URL'):
                self.base_url = os.getenv('PINECONE_API_BASE_URL')
            else:
                self.base_url = base_url
        if self.base_url and 'api.pinecone.io' in self.base_url:
            self.headers['X-Pinecone-API-Version'] = '2024-07'
        self.index_name = index_name
        self.dimensions = dimensions
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.host = host
        if namespace == 'sr_config':
            raise ValueError("Namespace 'sr_config' is reserved for internal use.")
        self.namespace = namespace
        self.type = 'pinecone'
        logger.warning('Default region changed from us-west-2 to us-east-1 in v0.1.0.dev6')
        self.client = self._initialize_client(api_key=self.api_key)
        if not init_async_index:
            self.index = self._init_index()

    def _initialize_client(self, api_key: Optional[str]=None):
        """Initialize the Pinecone client.

        :param api_key: Pinecone API key.
        :type api_key: Optional[str]
        :return: Pinecone client.
        :rtype: Pinecone
        """
        try:
            from pinecone import Pinecone, ServerlessSpec
            self.ServerlessSpec = ServerlessSpec
        except ImportError:
            raise ImportError("Please install pinecone-client to use PineconeIndex. You can install it with: `pip install 'semantic-router[pinecone]'`")
        pinecone_args = {'api_key': api_key, 'source_tag': 'semanticrouter', 'host': self.base_url}
        if self.namespace:
            pinecone_args['namespace'] = self.namespace
        return Pinecone(**pinecone_args)

    def _calculate_index_host(self):
        """Calculate the index host. Used to differentiate between normal
        Pinecone and Pinecone Local instance.

        :return: None
        :rtype: None
        """
        if self.index_host and self.base_url:
            if 'api.pinecone.io' in self.base_url:
                if not self.index_host.startswith('http'):
                    self.index_host = f'https://{self.index_host}'
            elif 'http' not in self.index_host:
                self.index_host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.index_host.split(':')[-1]}'
            elif not self.index_host.startswith('http://'):
                if 'localhost' in self.index_host:
                    self.index_host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.index_host.split(':')[-1]}'
                else:
                    self.index_host = f'http://{self.index_host}'

    def _init_index(self, force_create: bool=False) -> Union[Any, None]:
        """Initializing the index can be done after the object has been created
        to allow for the user to set the dimensions and other parameters.

        If the index doesn't exist and the dimensions are given, the index will
        be created. If the index exists, it will be returned. If the index doesn't
        exist and the dimensions are not given, the index will not be created and
        None will be returned.

        :param force_create: If True, the index will be created even if the
            dimensions are not given (which will raise an error).
        :type force_create: bool, optional
        """
        dimensions_given = self.dimensions is not None
        if self.index is None:
            index_exists = self.client.has_index(name=self.index_name)
            if dimensions_given and (not index_exists):
                self.client.create_index(name=self.index_name, dimension=self.dimensions, metric=self.metric, spec=self.ServerlessSpec(cloud=self.cloud, region=self.region))
                while not self.client.describe_index(self.index_name).status['ready']:
                    time.sleep(0.2)
                index = self.client.Index(self.index_name)
                self.index = index
                time.sleep(0.2)
            elif index_exists:
                self.index_host = self.client.describe_index(self.index_name).host
                self._calculate_index_host()
                index = self.client.Index(self.index_name, host=self.index_host)
                self.index = index
                self.dimensions = index.describe_index_stats()['dimension']
            elif force_create and (not dimensions_given):
                raise ValueError('Cannot create an index without specifying the dimensions.')
            else:
                logger.warning(f'Index could not be initialized. Init parameters: self.index_name={self.index_name!r}, self.dimensions={self.dimensions!r}, self.metric={self.metric!r}, self.cloud={self.cloud!r}, self.region={self.region!r}, self.host={self.host!r}, self.namespace={self.namespace!r}, force_create={force_create!r}')
                index = None
        else:
            index = self.index
        if self.index is not None and self.host == '':
            self.index_host = self.client.describe_index(self.index_name).host
            if self.index_host and self.base_url:
                self._calculate_index_host()
                index = self.client.Index(self.index_name, host=self.index_host)
                self.host = self.index_host
        return index

    async def _init_async_index(self, force_create: bool=False):
        """Initializing the index can be done after the object has been created
        to allow for the user to set the dimensions and other parameters.

        If the index doesn't exist and the dimensions are given, the index will
        be created. If the index exists, it will be returned. If the index doesn't
        exist and the dimensions are not given, the index will not be created and
        None will be returned.

        This method is used to initialize the index asynchronously.

        :param force_create: If True, the index will be created even if the
            dimensions are not given (which will raise an error).
        :type force_create: bool, optional
        """
        index_stats = None
        if self.dimensions is None:
            indexes = await self._async_list_indexes()
            index_names = [i['name'] for i in indexes['indexes']]
            index_exists = self.index_name in index_names
            if index_exists:
                index_stats = await self._async_describe_index(self.index_name)
                self.dimensions = index_stats['dimension']
            elif index_exists and (not force_create):
                logger.warning(f'Index could not be initialized. Init parameters: self.index_name={self.index_name!r}, self.dimensions={self.dimensions!r}, self.metric={self.metric!r}, self.cloud={self.cloud!r}, self.region={self.region!r}, self.host={self.host!r}, self.namespace={self.namespace!r}, force_create={force_create!r}')
            elif force_create:
                raise ValueError(f'Index could not be initialized. Init parameters: self.index_name={self.index_name!r}, self.dimensions={self.dimensions!r}, self.metric={self.metric!r}, ')
            else:
                raise NotImplementedError('Unexpected init conditions. Please report this issue in GitHub.')
        if self.dimensions:
            indexes = await self._async_list_indexes()
            index_names = [i['name'] for i in indexes['indexes']]
            index_exists = self.index_name in index_names
            if not index_exists:
                index_stats = await self._async_describe_index(self.index_name)
                index_status = index_stats.get('status', {})
                index_ready = index_status.get('ready', False) if isinstance(index_status, dict) else False
                if index_ready == 'true' or (isinstance(index_ready, bool) and index_ready):
                    self.index_host = index_stats['host']
                    self._calculate_index_host()
                    self.host = self.index_host
                    return index_stats
                else:
                    await self._async_create_index(name=self.index_name, dimension=self.dimensions, metric=self.metric, cloud=self.cloud, region=self.region)
                    index_ready = 'false'
                    while not (index_ready == 'true' or (isinstance(index_ready, bool) and index_ready)):
                        index_stats = await self._async_describe_index(self.index_name)
                        index_status = index_stats.get('status', {})
                        index_ready = index_status.get('ready', False) if isinstance(index_status, dict) else False
                        await asyncio.sleep(0.1)
                    self.index_host = index_stats['host']
                    self._calculate_index_host()
                    self.host = self.index_host
                    return index_stats
            else:
                index_stats = await self._async_describe_index(self.index_name)
                self.index_host = index_stats['host']
                self._calculate_index_host()
                self.host = self.index_host
                return index_stats
        if index_stats:
            self.index_host = index_stats['host']
            self._calculate_index_host()
            self.host = self.index_host
        else:
            self.host = ''

    def _batch_upsert(self, batch: List[Dict]):
        """Helper method for upserting a single batch of records.

        :param batch: The batch of records to upsert.
        :type batch: List[Dict]
        """
        if self.index is not None:
            self.index.upsert(vectors=batch, namespace=self.namespace)
        else:
            raise ValueError('Index is None, could not upsert.')

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[Optional[List[Dict[str, Any]]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=100, sparse_embeddings: Optional[Optional[List[SparseEmbedding]]]=None, **kwargs):
        """Add vectors to Pinecone in batches.

        :param embeddings: List of embeddings to upsert.
        :type embeddings: List[List[float]]
        :param routes: List of routes to upsert.
        :type routes: List[str]
        :param utterances: List of utterances to upsert.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to upsert.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to upsert.
        :type metadata_list: List[Dict[str, Any]]
        :param batch_size: Number of vectors to upsert in a single batch.
        :type batch_size: int, optional
        :param sparse_embeddings: List of sparse embeddings to upsert.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        if self.index is None:
            self.dimensions = self.dimensions or len(embeddings[0])
            self.index = self._init_index(force_create=True)
        vectors_to_upsert = build_records(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, sparse_embeddings=sparse_embeddings)
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            self._batch_upsert(batch)

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[Optional[List[Dict[str, Any]]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=100, sparse_embeddings: Optional[Optional[List[SparseEmbedding]]]=None, **kwargs):
        """Add vectors to Pinecone in batches.

        :param embeddings: List of embeddings to upsert.
        :type embeddings: List[List[float]]
        :param routes: List of routes to upsert.
        :type routes: List[str]
        :param utterances: List of utterances to upsert.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to upsert.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to upsert.
        :type metadata_list: List[Dict[str, Any]]
        :param batch_size: Number of vectors to upsert in a single batch.
        :type batch_size: int, optional
        :param sparse_embeddings: List of sparse embeddings to upsert.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        vectors_to_upsert = build_records(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, sparse_embeddings=sparse_embeddings)
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            await self._async_upsert(vectors=batch, namespace=self.namespace or '')

    def _remove_and_sync(self, routes_to_delete: dict):
        """Remove specified routes from index if they exist.

        :param routes_to_delete: Routes to delete.
        :type routes_to_delete: dict
        """
        for route, utterances in routes_to_delete.items():
            remote_routes = self._get_routes_with_ids(route_name=route)
            ids_to_delete = [r['id'] for r in remote_routes if (r['route'], r['utterance']) in zip([route] * len(utterances), utterances)]
            if ids_to_delete and self.index:
                self.index.delete(ids=ids_to_delete, namespace=self.namespace)

    async def _async_remove_and_sync(self, routes_to_delete: dict):
        """Remove specified routes from index if they exist.

        This method is asyncronous.

        :param routes_to_delete: Routes to delete.
        :type routes_to_delete: dict
        """
        for route, utterances in routes_to_delete.items():
            remote_routes = await self._async_get_routes_with_ids(route_name=route)
            ids_to_delete = [r['id'] for r in remote_routes if (r['route'], r['utterance']) in zip([route] * len(utterances), utterances)]
            if ids_to_delete and self.index:
                await self._async_delete(ids=ids_to_delete, namespace=self.namespace or '')

    def _get_route_ids(self, route_name: str):
        """Get the IDs of the routes in the index.

        :param route_name: Name of the route to get the IDs for.
        :type route_name: str
        :return: List of IDs of the routes.
        :rtype: list[str]
        """
        clean_route = clean_route_name(route_name)
        ids, _ = self._get_all(prefix=f'{clean_route}#')
        return ids

    async def _async_get_route_ids(self, route_name: str):
        """Get the IDs of the routes in the index.

        :param route_name: Name of the route to get the IDs for.
        :type route_name: str
        :return: List of IDs of the routes.
        :rtype: list[str]
        """
        clean_route = clean_route_name(route_name)
        ids, _ = await self._async_get_all(prefix=f'{clean_route}#')
        return ids

    def _get_routes_with_ids(self, route_name: str):
        """Get the routes with their IDs from the index.

        :param route_name: Name of the route to get the routes with their IDs for.
        :type route_name: str
        :return: List of routes with their IDs.
        :rtype: list[dict]
        """
        clean_route = clean_route_name(route_name)
        ids, metadata = self._get_all(prefix=f'{clean_route}#', include_metadata=True)
        route_tuples = []
        for id, data in zip(ids, metadata):
            route_tuples.append({'id': id, 'route': data['sr_route'], 'utterance': data['sr_utterance']})
        return route_tuples

    async def _async_get_routes_with_ids(self, route_name: str):
        """Get the routes with their IDs from the index.

        :param route_name: Name of the route to get the routes with their IDs for.
        :type route_name: str
        :return: List of routes with their IDs.
        :rtype: list[dict]
        """
        clean_route = clean_route_name(route_name)
        ids, metadata = await self._async_get_all(prefix=f'{clean_route}#', include_metadata=True)
        route_tuples = []
        for id, data in zip(ids, metadata):
            route_tuples.append({'id': id, 'route': data['sr_route'], 'utterance': data['sr_utterance']})
        return route_tuples

    def _get_all(self, prefix: Optional[str]=None, include_metadata: bool=False):
        """Retrieves all vector IDs from the Pinecone index using pagination.

        :param prefix: The prefix to filter the vectors by.
        :type prefix: Optional[str]
        :param include_metadata: Whether to include metadata in the response.
        :type include_metadata: bool
        :return: A tuple containing a list of vector IDs and a list of metadata dictionaries.
        :rtype: tuple[list[str], list[dict]]
        """
        if self.index is None:
            raise ValueError('Index is None, could not retrieve vector IDs.')
        all_vector_ids = []
        metadata = []
        for ids in self.index.list(prefix=prefix, namespace=self.namespace):
            all_vector_ids.extend(ids)
            if include_metadata:
                for id in ids:
                    res_meta = self.index.fetch(ids=[id], namespace=self.namespace) if self.index else {}
                    metadata.extend([x['metadata'] for x in res_meta['vectors'].values()])
        return (all_vector_ids, metadata)

    def delete(self, route_name: str) -> list[str]:
        """Delete specified route from index if it exists. Returns the IDs of the vectors
        deleted.

        :param route_name: Name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted.
        :rtype: list[str]
        """
        route_vec_ids = self._get_route_ids(route_name=route_name)
        if self.index is not None:
            logger.info('index is not None, deleting...')
            if self.base_url and 'api.pinecone.io' in self.base_url:
                self.index.delete(ids=route_vec_ids, namespace=self.namespace)
            else:
                response = requests.post(f'{self.index_host}/vectors/delete', json=DeleteRequest(ids=route_vec_ids, delete_all=True, namespace=self.namespace).model_dump(exclude_none=True), timeout=10)
                if response.status_code == 200:
                    logger.info(f'Deleted {len(route_vec_ids)} vectors from index {self.index_name}.')
                else:
                    error_message = response.text
                    raise Exception(f'Failed to delete vectors: {response.status_code} : {error_message}')
            return route_vec_ids
        else:
            raise ValueError('Index is None, could not delete.')

    async def adelete(self, route_name: str) -> list[str]:
        """Asynchronously delete specified route from index if it exists. Returns the IDs
        of the vectors deleted.

        :param route_name: Name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted.
        :rtype: list[str]
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        route_vec_ids = await self._async_get_route_ids(route_name=route_name)
        await self._async_delete(ids=route_vec_ids, namespace=self.namespace or '')
        return route_vec_ids

    def delete_all(self):
        """Delete all routes from index if it exists.

        :return: None
        :rtype: None
        """
        if self.index is not None:
            self.index.delete(delete_all=True, namespace=self.namespace)
        else:
            raise ValueError('Index is None, could not delete.')

    def describe(self) -> IndexConfig:
        """Describe the index.

        :return: IndexConfig
        :rtype: IndexConfig
        """
        if self.index is not None:
            stats = self.index.describe_index_stats()
            return IndexConfig(type=self.type, dimensions=stats['dimension'], vectors=stats['namespaces'][self.namespace]['vector_count'])
        else:
            return IndexConfig(type=self.type, dimensions=self.dimensions or 0, vectors=0)

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.index is not None

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: An optional sparse vector to include in the query.
        :type sparse_vector: Optional[SparseEmbedding]
        :param kwargs: Additional keyword arguments for the query, including sparse_vector.
        :type kwargs: Any
        :return: A tuple containing an array of scores and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises ValueError: If the index is not populated.
        """
        if self.index is None:
            raise ValueError('Index is not populated.')
        query_vector_list = vector.tolist()
        if route_filter is not None:
            filter_query = {'sr_route': {'$in': route_filter}}
        else:
            filter_query = None
        if sparse_vector is not None:
            logger.error(f'sparse_vector exists:{sparse_vector}')
            if isinstance(sparse_vector, dict):
                sparse_vector = SparseEmbedding.from_dict(sparse_vector)
            if isinstance(sparse_vector, SparseEmbedding):
                sparse_vector = sparse_vector.to_pinecone()
        try:
            results = self.index.query(vector=[query_vector_list], sparse_vector=sparse_vector, top_k=top_k, filter=filter_query, include_metadata=True, namespace=self.namespace)
        except Exception:
            logger.error('retrying query with vector as str')
            results = self.index.query(vector=query_vector_list, sparse_vector=sparse_vector, top_k=top_k, filter=filter_query, include_metadata=True, namespace=self.namespace)
        scores = [result['score'] for result in results['matches']]
        route_names = [result['metadata']['sr_route'] for result in results['matches']]
        return (np.array(scores), route_names)

    def _read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the index.

        :param field: The field to read.
        :type field: str
        :param scope: The scope to read.
        :type scope: str | None
        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        scope = scope or self.namespace
        if self.index is None:
            return ConfigParameter(field=field, value='', scope=scope)
        config_id = f'{field}#{scope}'
        config_record = self.index.fetch(ids=[config_id], namespace='sr_config')
        if config_record.get('vectors'):
            return ConfigParameter(field=field, value=config_record['vectors'][config_id]['metadata']['value'], created_at=config_record['vectors'][config_id]['metadata']['created_at'], scope=scope)
        else:
            logger.warning(f'Configuration for {field} parameter not found in index.')
            return ConfigParameter(field=field, value='', scope=scope)

    async def _async_read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the index asynchronously.

        :param field: The field to read.
        :type field: str
        :param scope: The scope to read.
        :type scope: str | None
        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        scope = scope or self.namespace
        if self.index is None:
            return ConfigParameter(field=field, value='', scope=scope)
        config_id = f'{field}#{scope}'
        config_record = await self._async_fetch_metadata(vector_id=config_id, namespace='sr_config')
        if config_record:
            try:
                return ConfigParameter(field=field, value=config_record['value'], created_at=config_record['created_at'], scope=scope)
            except KeyError:
                raise ValueError(f'Found invalid config record during sync: {config_record}')
        else:
            logger.warning(f'Configuration for {field} parameter not found in index.')
            return ConfigParameter(field=field, value='', scope=scope)

    def _write_config(self, config: ConfigParameter) -> ConfigParameter:
        """Method to write a config parameter to the remote Pinecone index.

        :param config: The config parameter to write to the index.
        :type config: ConfigParameter
        """
        config.scope = config.scope or self.namespace
        if self.index is None:
            raise ValueError('Index has not been initialized.')
        if self.dimensions is None:
            raise ValueError('Must set PineconeIndex.dimensions before writing config.')
        self.index.upsert(vectors=[config.to_pinecone(dimensions=self.dimensions)], namespace='sr_config')
        return config

    async def _async_write_config(self, config: ConfigParameter) -> ConfigParameter:
        """Method to write a config parameter to the remote Pinecone index.

        :param config: The config parameter to write to the index.
        :type config: ConfigParameter
        """
        config.scope = config.scope or self.namespace
        if self.dimensions is None:
            raise ValueError('Must set PineconeIndex.dimensions before writing config.')
        pinecone_config = config.to_pinecone(dimensions=self.dimensions)
        await self._async_upsert(vectors=[pinecone_config], namespace='sr_config')
        return config

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Asynchronously search the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param kwargs: Additional keyword arguments for the query, including sparse_vector.
        :type kwargs: Any
        :keyword sparse_vector: An optional sparse vector to include in the query.
        :type sparse_vector: Optional[dict]
        :return: A tuple containing an array of scores and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises ValueError: If the index is not populated.
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        query_vector_list = vector.tolist()
        if route_filter is not None:
            filter_query = {'sr_route': {'$in': route_filter}}
        else:
            filter_query = None
        sparse_vector_obj: dict[str, Any] | None = None
        if sparse_vector is not None:
            if isinstance(sparse_vector, dict):
                sparse_vector_obj = SparseEmbedding.from_dict(sparse_vector)
            if isinstance(sparse_vector, SparseEmbedding):
                sparse_vector_obj = sparse_vector.to_pinecone()
        results = await self._async_query(vector=query_vector_list, sparse_vector=sparse_vector_obj, namespace=self.namespace or '', filter=filter_query, top_k=top_k, include_metadata=True)
        scores = [result['score'] for result in results['matches']]
        route_names = [result['metadata']['sr_route'] for result in results['matches']]
        return (np.array(scores), route_names)

    async def aget_routes(self) -> list[tuple]:
        """Asynchronously get a list of route and utterance objects currently
        stored in the index.

        :return: A list of (route_name, utterance) objects.
        :rtype: List[Tuple]
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        return await self._async_get_routes()

    def delete_index(self):
        """Delete the index.

        :return: None
        :rtype: None
        """
        self.client.delete_index(self.index_name)
        self.index = None

    async def adelete_index(self):
        """Asynchronously delete the index."""
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        if not self.base_url:
            raise ValueError('base_url is not set for PineconeIndex.')
        async with aiohttp.ClientSession() as session:
            async with session.delete(f'{self.base_url}/indexes/{self.index_name}', headers=self.headers) as response:
                res = await response.json(content_type=None)
                if response.status != 202:
                    raise Exception(f'Failed to delete index: {response.status}', res)
        self.host = ''
        return res

    async def _async_query(self, vector: list[float], sparse_vector: dict[str, Any] | None=None, namespace: str='', filter: Optional[dict]=None, top_k: int=5, include_metadata: bool=False):
        """Asynchronously query the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: list[float]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[str, Any] | None
        :param namespace: The namespace to search for.
        :type namespace: str
        :param filter: The filter to search for.
        :type filter: Optional[dict]
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param include_metadata: Whether to include metadata in the results, defaults to False.
        :type include_metadata: bool, optional
        """
        params = {'vector': vector, 'sparse_vector': sparse_vector, 'namespace': namespace, 'filter': filter, 'top_k': top_k, 'include_metadata': include_metadata, 'topK': top_k, 'includeMetadata': include_metadata}
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        elif self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.host}/query', json=params, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f'Error in query response: {error_text}')
                    return {}
                try:
                    return await response.json(content_type=None)
                except JSONDecodeError as e:
                    logger.error(f'JSON decode error: {e}')
                    return {}

    async def ais_ready(self, client_only: bool=False) -> bool:
        """Checks if class attributes exist to be used for async operations.

        :param client_only: Whether to check only the client attributes. If False
            attributes will be checked for both client and index operations. If True
            only attributes for client operations will be checked. Defaults to False.
        :type client_only: bool, optional
        :return: True if the class attributes exist, False otherwise.
        :rtype: bool
        """
        if not (self.cloud or self.region or self.base_url):
            return False
        if not client_only:
            if not (self.index_name and self.dimensions and self.metric and self.host and (self.host != '')):
                await self._init_async_index()
                if not (self.index_name and self.dimensions and self.metric and self.host and (self.host != '')):
                    return False
        return True

    async def _async_list_indexes(self):
        """Asynchronously lists all indexes within the current Pinecone project.

        :return: List of indexes.
        :rtype: list[dict]
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.base_url}/indexes', headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_upsert(self, vectors: list[dict], namespace: str=''):
        """Asynchronously upserts vectors into the index.

        :param vectors: The vectors to upsert.
        :type vectors: list[dict]
        :param namespace: The namespace to upsert the vectors into.
        :type namespace: str
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        params = {'vectors': vectors, 'namespace': namespace}
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.host}/vectors/upsert', json=params, headers=self.headers) as response:
                res = await response.json(content_type=None)
                return res

    async def _async_create_index(self, name: str, dimension: int, cloud: str, region: str, metric: str='dotproduct'):
        """Asynchronously creates a new index in Pinecone.

        :param name: The name of the index to create.
        :type name: str
        :param dimension: The dimension of the index.
        :type dimension: int
        :param cloud: The cloud provider to create the index on.
        :type cloud: str
        :param region: The region to create the index in.
        :type region: str
        :param metric: The metric to use for the index, defaults to "dotproduct".
        :type metric: str, optional
        """
        params = {'name': name, 'dimension': dimension, 'metric': metric, 'spec': {'serverless': {'cloud': cloud, 'region': region}}, 'deletion_protection': 'disabled'}
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.base_url}/indexes', json=params, headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_delete(self, ids: list[str], namespace: str=''):
        """Asynchronously deletes vectors from the index.

        :param ids: The IDs of the vectors to delete.
        :type ids: list[str]
        :param namespace: The namespace to delete the vectors from.
        :type namespace: str
        """
        params = {'ids': ids, 'namespace': namespace}
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.host}/vectors/delete', json=params, headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_describe_index(self, name: str):
        """Asynchronously describes the index.

        :param name: The name of the index to describe.
        :type name: str
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.base_url}/indexes/{name}', headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_get_all(self, prefix: Optional[str]=None, include_metadata: bool=False) -> tuple[list[str], list[dict]]:
        """Retrieves all vector IDs from the Pinecone index using pagination
        asynchronously.

        :param prefix: The prefix to filter the vectors by.
        :type prefix: Optional[str]
        :param include_metadata: Whether to include metadata in the response.
        :type include_metadata: bool
        :return: A tuple containing a list of vector IDs and a list of metadata dictionaries.
        :rtype: tuple[list[str], list[dict]]
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        all_vector_ids = []
        next_page_token = None
        if prefix:
            prefix_str = f'?prefix={prefix}'
        else:
            prefix_str = ''
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        list_url = f'{self.host}/vectors/list{prefix_str}'
        params: dict = {}
        if self.namespace:
            params['namespace'] = self.namespace
        metadata = []
        async with aiohttp.ClientSession() as session:
            while True:
                if next_page_token:
                    params['paginationToken'] = next_page_token
                async with session.get(list_url, params=params, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f'Error fetching vectors: {error_text}')
                        break
                    response_data = await response.json(content_type=None)
                vector_ids = [vec['id'] for vec in response_data.get('vectors', [])]
                if not vector_ids:
                    break
                all_vector_ids.extend(vector_ids)
                if include_metadata:
                    metadata_tasks = [self._async_fetch_metadata(id) for id in vector_ids]
                    metadata_results = await asyncio.gather(*metadata_tasks)
                    metadata.extend(metadata_results)
                next_page_token = response_data.get('pagination', {}).get('next')
                if not next_page_token:
                    break
        return (all_vector_ids, metadata)

    async def _async_fetch_metadata(self, vector_id: str, namespace: str | None=None) -> dict:
        """Fetch metadata for a single vector ID asynchronously using the
        ClientSession.

        :param vector_id: The ID of the vector to fetch metadata for.
        :type vector_id: str
        :param namespace: The namespace to fetch metadata for.
        :type namespace: str | None
        :return: A dictionary containing the metadata for the vector.
        :rtype: dict
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        url = f'{self.host}/vectors/fetch'
        params = {'ids': [vector_id]}
        if namespace:
            params['namespace'] = [namespace]
        elif self.namespace:
            params['namespace'] = [self.namespace]
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f'Error fetching metadata: {error_text}')
                    return {}
                try:
                    response_data = await response.json(content_type=None)
                except Exception as e:
                    logger.warning(f'No metadata found for vector {vector_id}: {e}')
                    return {}
                return response_data.get('vectors', {}).get(vector_id, {}).get('metadata', {})

    def __len__(self):
        """Returns the total number of vectors in the index. If the index is not initialized
        returns 0.

        :return: The total number of vectors.
        :rtype: int
        """
        if self.index is None:
            logger.warning('Index is not initialized, returning 0')
            return 0
        namespace_stats = self.index.describe_index_stats()['namespaces'].get(self.namespace)
        if namespace_stats:
            return namespace_stats['vector_count']
        else:
            return 0

    async def alen(self):
        """Async version of __len__. Returns the total number of vectors in the index.
        If the index is not initialized, initializes it first or returns 0.

        :return: The total number of vectors.
        :rtype: int
        """
        if not await self.ais_ready():
            logger.warning('Index is not ready, returning 0')
            return 0
        namespace_stats = await self._async_describe_index_stats()
        if namespace_stats and 'namespaces' in namespace_stats:
            ns_stats = namespace_stats['namespaces'].get(self.namespace)
            if ns_stats:
                return ns_stats['vectorCount']
        return 0

    async def _async_describe_index_stats(self):
        """Async version of describe_index_stats.

        :return: Index statistics.
        :rtype: dict
        """
        url = f'{self.index_host}/describe_index_stats'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json={'namespace': self.namespace}, timeout=aiohttp.ClientTimeout(total=300)) as response:
                response.raise_for_status()
                return await response.json()

def _calculate_index_host(self):
    """Calculate the index host. Used to differentiate between normal
        Pinecone and Pinecone Local instance.

        :return: None
        :rtype: None
        """
    if self.index_host and self.base_url:
        if 'api.pinecone.io' in self.base_url:
            if not self.index_host.startswith('http'):
                self.index_host = f'https://{self.index_host}'
        elif 'http' not in self.index_host:
            self.index_host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.index_host.split(':')[-1]}'
        elif not self.index_host.startswith('http://'):
            if 'localhost' in self.index_host:
                self.index_host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.index_host.split(':')[-1]}'
            else:
                self.index_host = f'http://{self.index_host}'

def parse_vector(vector_str: Union[str, Any]) -> List[float]:
    """Parses a vector from a string or other representation.

    :param vector_str: The string or object representation of a vector.
    :type vector_str: Union[str, Any]
    :return: A list of floats representing the vector.
    :rtype: List[float]
    """
    if isinstance(vector_str, str):
        vector_str = vector_str.strip('()"[]')
        return list(map(float, vector_str.split(',')))
    else:
        return vector_str

def clean_route_name(route_name: str) -> str:
    """Cleans and formats the route name by stripping spaces and replacing them with hyphens.

    :param route_name: The original route name.
    :type route_name: str
    :return: The cleaned and formatted route name.
    :rtype: str
    """
    return route_name.strip().replace(' ', '-')

class LocalIndex(BaseIndex):
    type: str = 'local'
    metadata: Optional[np.ndarray] = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.metadata is None:
            self.metadata = None
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs):
        """Add embeddings to the index.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        """
        embeds = np.array(embeddings)
        routes_arr = np.array(routes)
        if isinstance(utterances[0], str):
            utterances_arr = np.array(utterances)
        else:
            utterances_arr = np.array(utterances, dtype=object)
        if self.index is None:
            self.index = embeds
            self.routes = routes_arr
            self.utterances = utterances_arr
            self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)
        else:
            self.index = np.concatenate([self.index, embeds])
            self.routes = np.concatenate([self.routes, routes_arr])
            self.utterances = np.concatenate([self.utterances, utterances_arr])
            if self.metadata is not None:
                self.metadata = np.concatenate([self.metadata, np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)])
            else:
                self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)

    def _remove_and_sync(self, routes_to_delete: dict) -> np.ndarray:
        """Remove and sync the index.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        :return: A numpy array of the removed route utterances.
        :rtype: np.ndarray
        """
        if self.index is None or self.routes is None or self.utterances is None:
            raise ValueError('Index, routes, or utterances are not populated.')
        route_utterances = np.array([self.routes, self.utterances]).T
        mask = np.ones(len(route_utterances), dtype=bool)
        for route, utterances in routes_to_delete.items():
            for utterance in utterances:
                mask &= ~((route_utterances[:, 0] == route) & (route_utterances[:, 1] == utterance))
        self.index = self.index[mask]
        self.routes = self.routes[mask]
        self.utterances = self.utterances[mask]
        if self.metadata is not None:
            self.metadata = self.metadata[mask]
        return route_utterances[~mask]

    def get_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the index.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects - LocalIndex now includes metadata if present.
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if self.routes is None or self.utterances is None:
            return []
        if include_metadata and self.metadata is not None:
            return [Utterance(route=route, utterance=utterance, function_schemas=None, metadata=metadata) for route, utterance, metadata in zip(self.routes, self.utterances, self.metadata)]
        else:
            return [Utterance.from_tuple(x) for x in zip(self.routes, self.utterances)]

    def describe(self) -> IndexConfig:
        """Describe the index.

        :return: An IndexConfig object.
        :rtype: IndexConfig
        """
        return IndexConfig(type=self.type, dimensions=self.index.shape[1] if self.index is not None else 0, vectors=self.index.shape[0] if self.index is not None else 0)

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.index is not None and self.routes is not None

    async def ais_ready(self) -> bool:
        """Checks if the index is ready to be used asynchronously.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.index is not None and self.routes is not None

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        if self.index is None or self.routes is None:
            raise ValueError('Index or routes are not populated.')
        if route_filter is not None:
            filtered_index = []
            filtered_routes = []
            for route, vec in zip(self.routes, self.index):
                if route in route_filter:
                    filtered_index.append(vec)
                    filtered_routes.append(route)
            if not filtered_routes:
                raise ValueError('No routes found matching the filter criteria.')
            sim = similarity_matrix(vector, np.array(filtered_index))
            scores, idx = top_scores(sim, top_k)
            route_names = [filtered_routes[i] for i in idx]
        else:
            sim = similarity_matrix(vector, self.index)
            scores, idx = top_scores(sim, top_k)
            route_names = [self.routes[i] for i in idx]
        return (scores, route_names)

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        if self.index is None or self.routes is None:
            raise ValueError('Index or routes are not populated.')
        if route_filter is not None:
            filtered_index = []
            filtered_routes = []
            for route, vec in zip(self.routes, self.index):
                if route in route_filter:
                    filtered_index.append(vec)
                    filtered_routes.append(route)
            if not filtered_routes:
                raise ValueError('No routes found matching the filter criteria.')
            sim = similarity_matrix(vector, np.array(filtered_index))
            scores, idx = top_scores(sim, top_k)
            route_names = [filtered_routes[i] for i in idx]
        else:
            sim = similarity_matrix(vector, self.index)
            scores, idx = top_scores(sim, top_k)
            route_names = [self.routes[i] for i in idx]
        return (scores, route_names)

    def aget_routes(self):
        """Get all routes from the index.

        :return: A list of routes.
        :rtype: List[str]
        """
        logger.error('Sync remove is not implemented for LocalIndex.')

    def _write_config(self, config: ConfigParameter):
        """Write the config to the index.

        :param config: The config to write to the index.
        :type config: ConfigParameter
        """
        logger.warning('No config is written for LocalIndex.')

    def delete(self, route_name: str):
        """Delete all records of a specific route from the index.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
        if self.index is not None and self.routes is not None and (self.utterances is not None):
            delete_idx = self._get_indices_for_route(route_name=route_name)
            self.index = np.delete(self.index, delete_idx, axis=0)
            self.routes = np.delete(self.routes, delete_idx, axis=0)
            self.utterances = np.delete(self.utterances, delete_idx, axis=0)
            if self.metadata is not None:
                self.metadata = np.delete(self.metadata, delete_idx, axis=0)
        else:
            raise ValueError('Attempted to delete route records but either index, routes or utterances is None.')

    async def adelete(self, route_name: str):
        """Delete all records of a specific route from the index. Note that this just points
        to the sync delete method as async makes no difference for the local computations
        of the LocalIndex.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
        self.delete(route_name)

    def delete_index(self):
        """Deletes the index, effectively clearing it and setting it to None.

        :return: None
        :rtype: None
        """
        self.index = None
        self.routes = None
        self.utterances = None
        self.metadata = None

    async def adelete_index(self):
        """Deletes the index, effectively clearing it and setting it to None. Note that this just points
        to the sync delete_index method as async makes no difference for the local computations
        of the LocalIndex.

        :return: None
        :rtype: None
        """
        self.index = None
        self.routes = None
        self.utterances = None
        self.metadata = None

    def _get_indices_for_route(self, route_name: str):
        """Gets an array of indices for a specific route.

        :param route_name: The name of the route to get indices for.
        :type route_name: str
        :return: An array of indices for the route.
        :rtype: np.ndarray
        """
        if self.routes is None:
            raise ValueError('Routes are not populated.')
        idx = [i for i, route in enumerate(self.routes) if route == route_name]
        return idx

    def __len__(self):
        if self.index is not None:
            return self.index.shape[0]
        else:
            return 0

def _remove_and_sync(self, routes_to_delete: dict) -> np.ndarray:
    """Remove and sync the index.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        :return: A numpy array of the removed route utterances.
        :rtype: np.ndarray
        """
    if self.index is None or self.routes is None or self.utterances is None:
        raise ValueError('Index, routes, or utterances are not populated.')
    route_utterances = np.array([self.routes, self.utterances]).T
    mask = np.ones(len(route_utterances), dtype=bool)
    for route, utterances in routes_to_delete.items():
        for utterance in utterances:
            mask &= ~((route_utterances[:, 0] == route) & (route_utterances[:, 1] == utterance))
    self.index = self.index[mask]
    self.routes = self.routes[mask]
    self.utterances = self.utterances[mask]
    if self.metadata is not None:
        self.metadata = self.metadata[mask]
    return route_utterances[~mask]

def _get_indices_for_route(self, route_name: str):
    """Gets an array of indices for a specific route.

        :param route_name: The name of the route to get indices for.
        :type route_name: str
        :return: An array of indices for the route.
        :rtype: np.ndarray
        """
    if self.routes is None:
        raise ValueError('Routes are not populated.')
    idx = [i for i, route in enumerate(self.routes) if route == route_name]
    return idx

class HybridLocalIndex(LocalIndex):
    type: str = 'hybrid_local'
    sparse_index: Optional[list[dict]] = None
    route_names: Optional[np.ndarray] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.metadata = None

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], sparse_embeddings: Optional[List[SparseEmbedding]]=None, **kwargs):
        """Add embeddings to the index.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        :param sparse_embeddings: List of sparse embeddings to add to the index.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        if sparse_embeddings is None:
            raise ValueError('Sparse embeddings are required for HybridLocalIndex.')
        if function_schemas is not None:
            logger.warning('Function schemas are not supported for HybridLocalIndex.')
        if metadata_list:
            logger.warning('Metadata is not supported for HybridLocalIndex.')
        embeds = np.array(embeddings)
        routes_arr = np.array(routes)
        if isinstance(utterances[0], str):
            utterances_arr = np.array(utterances)
        else:
            utterances_arr = np.array(utterances, dtype=object)
        if self.index is None or self.sparse_index is None:
            self.index = embeds
            self.sparse_index = [x.to_dict() for x in sparse_embeddings]
            self.routes = routes_arr
            self.utterances = utterances_arr
            self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)
        else:
            self.index = np.concatenate([self.index, embeds])
            self.sparse_index.extend([x.to_dict() for x in sparse_embeddings])
            self.routes = np.concatenate([self.routes, routes_arr])
            self.utterances = np.concatenate([self.utterances, utterances_arr])
            if self.metadata is not None:
                self.metadata = np.concatenate([self.metadata, np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)])
            else:
                self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], sparse_embeddings: Optional[List[SparseEmbedding]]=None, **kwargs):
        """Add embeddings to the index - note that this is not truly async as it is a
        local index and there is no sense to make this method async. Instead, it will
        call the sync `add` method.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        :param sparse_embeddings: List of sparse embeddings to add to the index.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        self.add(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, sparse_embeddings=sparse_embeddings)

    def get_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the index.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects - HybridLocalIndex doesn't include metadata so
        this parameter is ignored.
        :type include_metadata: bool
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if self.routes is None or self.utterances is None:
            return []
        if include_metadata and self.metadata is not None:
            return [Utterance(route=route, utterance=utterance, function_schemas=None, metadata=metadata) for route, utterance, metadata in zip(self.routes, self.utterances, self.metadata)]
        else:
            return [Utterance.from_tuple(x) for x in zip(self.routes, self.utterances)]

    def _sparse_dot_product(self, vec_a: dict[int, float], vec_b: dict[int, float]) -> float:
        """Calculate the dot product of two sparse vectors.

        :param vec_a: The first sparse vector.
        :type vec_a: dict[int, float]
        :param vec_b: The second sparse vector.
        :type vec_b: dict[int, float]
        :return: The dot product of the two sparse vectors.
        :rtype: float
        """
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = (vec_b, vec_a)
        return sum((vec_a[i] * vec_b.get(i, 0) for i in vec_a))

    def _sparse_index_dot_product(self, vec_a: dict[int, float]) -> list[float]:
        """Calculate the dot product of a sparse vector and a list of sparse vectors.

        :param vec_a: The sparse vector.
        :type vec_a: dict[int, float]
        :return: A list of dot products.
        :rtype: list[float]
        """
        if self.sparse_index is None:
            raise ValueError('self.sparse_index is not populated.')
        dot_products = [self._sparse_dot_product(vec_a, vec_b) for vec_b in self.sparse_index]
        return dot_products

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: The sparse vector to search for, must be provided.
        :type sparse_vector: dict[int, float]
        """
        if route_filter:
            raise ValueError('Route filter is not supported for HybridLocalIndex.')
        xq_d = vector.copy()
        if isinstance(sparse_vector, SparseEmbedding):
            xq_s = sparse_vector.to_dict()
        elif isinstance(sparse_vector, dict):
            xq_s = sparse_vector
        else:
            raise ValueError('Sparse vector must be a SparseEmbedding or dict.')
        if self.index is not None and self.sparse_index is not None:
            index_norm = norm(self.index, axis=1)
            xq_d_norm = norm(xq_d)
            sim_d = np.squeeze(np.dot(self.index, xq_d.T)) / (index_norm * xq_d_norm)
            sim_s = np.array(self._sparse_index_dot_product(xq_s))
            total_sim = sim_d + sim_s
            top_k = min(top_k, total_sim.shape[0])
            idx = np.argpartition(total_sim, -top_k)[-top_k:]
            scores = total_sim[idx]
            route_names = self.routes[idx] if self.routes is not None else []
            return (scores, route_names)
        else:
            logger.warning('Index or sparse index is not populated.')
            return (np.array([]), [])

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results. This method calls the
        sync `query` method as everything uses numpy computations which is CPU-bound
        and so no benefit can be gained from making this async.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: The sparse vector to search for, must be provided.
        :type sparse_vector: dict[int, float]
        """
        return self.query(vector=vector, top_k=top_k, route_filter=route_filter, sparse_vector=sparse_vector)

    def aget_routes(self):
        """Get all routes from the index.

        :return: A list of routes.
        :rtype: List[str]
        """
        logger.error(f'Sync remove is not implemented for {self.__class__.__name__}.')

    def _write_config(self, config: ConfigParameter):
        """Write the config to the index.

        :param config: The config to write to the index.
        :type config: ConfigParameter
        """
        logger.warning(f'No config is written for {self.__class__.__name__}.')

    def delete(self, route_name: str):
        """Delete all records of a specific route from the index.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
        if self.index is not None and self.routes is not None and (self.utterances is not None):
            delete_idx = self._get_indices_for_route(route_name=route_name)
            self.index = np.delete(self.index, delete_idx, axis=0)
            self.routes = np.delete(self.routes, delete_idx, axis=0)
            self.utterances = np.delete(self.utterances, delete_idx, axis=0)
            if self.metadata is not None:
                self.metadata = np.delete(self.metadata, delete_idx, axis=0)
        else:
            raise ValueError('Attempted to delete route records but either index, routes or utterances is None.')

    def delete_index(self):
        """Deletes the index, effectively clearing it and setting it to None.

        :return: None
        :rtype: None
        """
        self.index = None
        self.routes = None
        self.utterances = None
        self.metadata = None

    def _get_indices_for_route(self, route_name: str):
        """Gets an array of indices for a specific route.

        :param route_name: The name of the route to get indices for.
        :type route_name: str
        :return: An array of indices for the route.
        :rtype: np.ndarray
        """
        if self.routes is None:
            raise ValueError('Routes are not populated.')
        idx = [i for i, route in enumerate(self.routes) if route == route_name]
        return idx

    def __len__(self):
        if self.index is not None:
            return self.index.shape[0]
        else:
            return 0

def _get_indices_for_route(self, route_name: str):
    """Gets an array of indices for a specific route.

        :param route_name: The name of the route to get indices for.
        :type route_name: str
        :return: An array of indices for the route.
        :rtype: np.ndarray
        """
    if self.routes is None:
        raise ValueError('Routes are not populated.')
    idx = [i for i, route in enumerate(self.routes) if route == route_name]
    return idx

class TfidfEncoder(SparseEncoder, FittableMixin):
    idf: np.ndarray = np.array([])
    word_index: Dict = {}

    def __init__(self, name: str | None=None):
        if name is None:
            name = 'tfidf'
        super().__init__(name=name)
        self.word_index = {}
        self.idf = np.array([])

    def __call__(self, docs: List[str]) -> list[SparseEmbedding]:
        if len(self.word_index) == 0 or self.idf.size == 0:
            raise ValueError('Vectorizer is not initialized.')
        if len(docs) == 0:
            raise ValueError('No documents to encode.')
        docs = [self._preprocess(doc) for doc in docs]
        tf = self._compute_tf(docs)
        tfidf = tf * self.idf
        return self._array_to_sparse_embeddings(tfidf)

    async def acall(self, docs: List[str]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.__call__(docs))

    def fit(self, routes: List[Route]):
        """Trains the encoder weights on the provided routes.

        :param routes: List of routes to train the encoder on.
        :type routes: List[Route]
        """
        self._fit_validate(routes=routes)
        docs = []
        for route in routes:
            for doc in route.utterances:
                docs.append(self._preprocess(doc))
        self.word_index = self._build_word_index(docs)
        if len(self.word_index) == 0:
            raise ValueError(f'Too little data to fit {self.__class__.__name__}.')
        self.idf = self._compute_idf(docs)

    def _fit_validate(self, routes: List[Route]):
        if not isinstance(routes, list) or not isinstance(routes[0], Route):
            raise TypeError('`routes` parameter must be a list of Route objects.')

    def _build_word_index(self, docs: List[str]) -> Dict:
        words = set()
        for doc in docs:
            for word in doc.split():
                words.add(word)
        word_index = {word: i for i, word in enumerate(words)}
        return word_index

    def _compute_tf(self, docs: List[str]) -> np.ndarray:
        if len(self.word_index) == 0:
            raise ValueError('Word index is not initialized.')
        tf = np.zeros((len(docs), len(self.word_index)))
        for i, doc in enumerate(docs):
            word_counts = Counter(doc.split())
            for word, count in word_counts.items():
                if word in self.word_index:
                    tf[i, self.word_index[word]] = count
        tf = tf / np.linalg.norm(tf, axis=1, keepdims=True)
        return tf

    def _compute_idf(self, docs: List[str]) -> np.ndarray:
        if len(self.word_index) == 0:
            raise ValueError('Word index is not initialized.')
        idf = np.zeros(len(self.word_index))
        for doc in docs:
            words = set(doc.split())
            for word in words:
                if word in self.word_index:
                    idf[self.word_index[word]] += 1
        idf = np.log(len(docs) / (idf + 1))
        return idf

    def _preprocess(self, doc: str) -> str:
        lowercased_doc = doc.lower()
        no_punctuation_doc = lowercased_doc.translate(str.maketrans('', '', string.punctuation))
        return no_punctuation_doc

def _build_word_index(self, docs: List[str]) -> Dict:
    words = set()
    for doc in docs:
        for word in doc.split():
            words.add(word)
    word_index = {word: i for i, word in enumerate(words)}
    return word_index

def _compute_tf(self, docs: List[str]) -> np.ndarray:
    if len(self.word_index) == 0:
        raise ValueError('Word index is not initialized.')
    tf = np.zeros((len(docs), len(self.word_index)))
    for i, doc in enumerate(docs):
        word_counts = Counter(doc.split())
        for word, count in word_counts.items():
            if word in self.word_index:
                tf[i, self.word_index[word]] = count
    tf = tf / np.linalg.norm(tf, axis=1, keepdims=True)
    return tf

class BM25Encoder(SparseEncoder, FittableMixin, AsymmetricSparseMixin):
    """BM25Encoder, running a vectorized version of ATIRE BM25 algorithm

    Concept:
    - BM25 uses scoring between queries & corpus to retrieve the most relevant documents ∈ corpus
    - most vector databases (VDB) store embedded documents and score them versus received queries for retrieval
    - we need to break up the BM25 formula into `encode_queries` and `encode_documents`, with the latter to be stored in VDB
    - dot product of `encode_queries(q)` and `encode_documents([D_0, D_1, ...])` is the BM25 score of the documents `[D_0, D_1, ...]` for the given query `q`
    - we train a BM25 encoder's normalization parameters on a sufficiently large corpus to capture target language distribution
    - these trained parameter allow us to balance TF & IDF of query & documents for retrieval (read more on how BM25 fixes issues with TF-IDF)

    ATIRE Paper: https://www.cs.otago.ac.nz/research/student-publications/atire-opensource.pdf
    Pinecone Implementation: https://github.com/pinecone-io/pinecone-text/blob/8399f9ff28c4652766c35165c0db9b0eff309077/pinecone_text/sparse/bm25_encoder.py

    :param k1: normalizer parameter that limits how much a single query term `q_i ∈ q` can affect score for document `D_n`
    :type k1: float
    :param b: normalizer parameter that balances the effect of a single document length compared to the average document length
    :type b: float
    :param corpus_size: number of documents in the trained corpus
    :type corpus_size: int, optional
    :param _avg_doc_len: float representing the average document length in the trained corpus
    :type _avg_doc_len: float, optional
    :param _documents_containing_word: (1, tokenizer.vocab_size) shaped array, denoting how many documents contain `token ∈ vocab`
    :type _documents_containing_word: class:`numpy.ndarray`, optional

    """
    type: str = 'sparse'
    k1: float = 1.5
    b: float = 0.75
    corpus_size: int | None = None
    _tokenizer: BaseTokenizer | None
    _avg_doc_len: np.float64 | float | None
    _documents_containing_word: np.ndarray | None

    def __init__(self, tokenizer: BaseTokenizer | None=None, name: str | None=None, k1: float=1.5, b: float=0.75, corpus_size: int | None=None, avg_doc_len: float | None=None, use_default_params: bool=True) -> None:
        if name is None:
            name = 'bm25'
        super().__init__(name=name)
        self.k1 = k1
        self.b = b
        self.corpus_size = corpus_size
        self._avg_doc_len = np.float64(avg_doc_len) if avg_doc_len else None
        if use_default_params and (not tokenizer):
            logger.info('Initializing default BM25 model parameters.')
            self._tokenizer = PretrainedTokenizer('google-bert/bert-base-uncased')
        elif tokenizer is not None:
            self._tokenizer = tokenizer
        else:
            raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')

    def _fit_validate(self, routes: List[Route]):
        if not isinstance(routes, list) or not isinstance(routes[0], Route):
            raise TypeError('`routes` parameter must be a list of Route objects.')

    def fit(self, routes: List[Route]) -> 'BM25Encoder':
        """Trains the encoder weights on the provided routes.

        :param routes: List of routes to train the encoder on.
        :type routes: List[Route]
        """
        if not self._tokenizer:
            raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
        self._fit_validate(routes)
        utterances = [utterance for route in routes for utterance in route.utterances]
        utterance_ids = self._tokenizer.tokenize(utterances, pad=True)
        corpus = self._tf(utterance_ids)
        self.corpus_size = len(utterances)
        doc_lengths = corpus.sum(axis=1)
        self._avg_doc_len = doc_lengths.mean()
        documents_containing_word = np.atleast_2d((corpus > 0).sum(axis=0))
        documents_containing_word[:, 0] *= 0
        self._documents_containing_word = documents_containing_word
        return self

    def _tf(self, docs: np.ndarray) -> np.ndarray:
        """Returns term frequency of query terms in trained corpus

        :param docs: 2D shaped array of each document's token ids
        :type docs: numpy.ndarray
        :return: Matrix where value @ (m, n) represents how many times token id `n` appears in document `m`
        :rtype: numpy.ndarray
        """
        if self._tokenizer is None:
            raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')
        vocab_size = self._tokenizer.vocab_size
        bincount = partial(np.bincount, minlength=vocab_size)
        tf = np.apply_along_axis(bincount, 1, docs)
        tf[:, 0] *= 0
        return tf

    def _df(self, queries: np.ndarray) -> np.ndarray:
        """Returns the amount of times each token in the query appears in trained corpus

        This is done in a faster, vectorized way, instead of looping through each query

        :param queries: 2D shaped array of each query token ids
        :type queries: numpy.ndarray
        :return: Matrix where value @ (m, n) represents how many times token id `n` in query `m` appears in the trained corpus
        :rtype: numpy.ndarray
        """
        if self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. `BM25Encoder.fit` a corpus, or `BM25Encoder.load` a pretrained encoder.')
        if self._tokenizer is None:
            raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')
        n = queries.shape[0]
        row_indices = np.arange(n)[:, None]
        mask = np.zeros((n, self._tokenizer.vocab_size), dtype=bool)
        mask[row_indices, queries] = True
        query_df = mask * self._documents_containing_word
        return query_df

    def encode_queries(self, queries: list[str]) -> list[SparseEmbedding]:
        """Returns BM25 scores for queries using precomputed corpus scores.

        :param queries: List of queries to encode
        :type queries: list
        :return: BM25 scores for each query against the corpus
        :rtype: list[SparseEmbedding]
        """
        if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
        if not self._tokenizer:
            raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
        if queries == []:
            raise ValueError('No documents provided for encoding')
        queries_ids = self._tokenizer.tokenize(queries)
        df = self._df(queries_ids)
        N = self.corpus_size
        df = df + np.where(df > 0, 0.5, 0)
        idf = np.divide(N + 1, df, out=np.zeros_like(df), where=df != 0)
        idf = np.log(idf, out=np.zeros_like(df), where=df != 0)
        idf_norm = np.divide(idf, idf.sum(axis=1)[:, np.newaxis], out=np.zeros_like(idf), where=idf != 0)
        return self._array_to_sparse_embeddings(idf_norm)

    def encode_documents(self, documents: list[str], batch_size: int | None=None) -> list[SparseEmbedding]:
        """Returns document term frequency normed by itself & average trained corpus length
        (This is the right-hand side of the BM25 equation, which gets matmul-ed with the query IDF component)

        LaTeX: $\\frac{f(d_i, D)}{f(d_i, D) + k_1 \\times (1 - b + b \\times \\frac{|D|}{avgdl})}$
        where:
            f(d_i, D) is frequency of term `d_i ∈ D`
            |D| is the document length
            avgdl is average document length in trained corpus

        :param documents: List of queries to encode
        :type documents: list
        :return: Encoded queries (as either sparse or dict)
        :rtype: list[SparseEmbedding]
        """
        if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
        if not self._tokenizer:
            raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
        if documents == []:
            raise ValueError('No documents provided for encoding')
        batch_size = batch_size or len(documents)
        queries_ids = self._tokenizer.tokenize(documents, pad=True)
        tf = self._tf(queries_ids)
        tf_sum = tf.sum(axis=1)
        tf_normed = tf / (self.k1 * (1.0 - self.b * self.b * (tf_sum[:, np.newaxis] / self._avg_doc_len)) + tf)
        return self._array_to_sparse_embeddings(tf_normed)

    def model(self, docs: List[str]) -> list[SparseEmbedding]:
        """Encode documents using BM25, with different encoding for queries vs documents to be indexed.

        :param docs: List of documents to encode
        :param is_query: If True, use query encoding, else use document encoding
        :return: List of sparse embeddings
        """
        if not self._tokenizer:
            raise ValueError('Encoder not fitted. `BM25.index` a corpus, or `BM25.load` a pretrained encoder.')
        if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
        return self.encode_queries(docs)

    async def aencode_queries(self, docs: List[str]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.encode_queries(docs))

    async def aencode_documents(self, docs: List[str]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.encode_documents(docs))

    def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
        return self.encode_queries(docs)

    async def acall(self, docs: List[Any]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.__call__(docs))

def _df(self, queries: np.ndarray) -> np.ndarray:
    """Returns the amount of times each token in the query appears in trained corpus

        This is done in a faster, vectorized way, instead of looping through each query

        :param queries: 2D shaped array of each query token ids
        :type queries: numpy.ndarray
        :return: Matrix where value @ (m, n) represents how many times token id `n` in query `m` appears in the trained corpus
        :rtype: numpy.ndarray
        """
    if self._documents_containing_word is None:
        raise ValueError('Encoder not fitted. `BM25Encoder.fit` a corpus, or `BM25Encoder.load` a pretrained encoder.')
    if self._tokenizer is None:
        raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')
    n = queries.shape[0]
    row_indices = np.arange(n)[:, None]
    mask = np.zeros((n, self._tokenizer.vocab_size), dtype=bool)
    mask[row_indices, queries] = True
    query_df = mask * self._documents_containing_word
    return query_df

def is_valid(layer_config: str) -> bool:
    """Make sure the given string is json format and contains the 3 keys:
    ["encoder_name", "encoder_type", "routes"]"""
    try:
        output_json = json.loads(layer_config)
        required_keys = ['encoder_name', 'encoder_type', 'routes']
        if isinstance(output_json, list):
            for item in output_json:
                missing_keys = [key for key in required_keys if key not in item]
                if missing_keys:
                    logger.warning(f'Missing keys in layer config: {', '.join(missing_keys)}')
                    return False
            return True
        else:
            missing_keys = [key for key in required_keys if key not in output_json]
            if missing_keys:
                logger.warning(f'Missing keys in layer config: {', '.join(missing_keys)}')
                return False
            else:
                return True
    except json.JSONDecodeError as e:
        logger.error(e)
        return False

class BaseRouter(BaseModel):
    """Base class for all routers."""
    encoder: DenseEncoder = Field(default_factory=OpenAIEncoder)
    sparse_encoder: Optional[SparseEncoder] = Field(default=None)
    index: BaseIndex = Field(default_factory=BaseIndex)
    score_threshold: Optional[float] = Field(default=None)
    routes: List[Route] = Field(default_factory=list)
    llm: Optional[BaseLLM] = None
    top_k: int = 5
    aggregation: str = 'mean'
    aggregation_method: Optional[Callable] = None
    auto_sync: Optional[str] = None
    init_async_index: bool = False
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, encoder: Optional[DenseEncoder]=None, sparse_encoder: Optional[SparseEncoder]=None, llm: Optional[BaseLLM]=None, routes: Optional[List[Route]]=None, index: Optional[BaseIndex]=None, top_k: int=5, aggregation: str='mean', auto_sync: Optional[str]=None, init_async_index: bool=False):
        """Initialize a BaseRouter object. Expected to be used as a base class only,
        not directly instantiated.

        :param encoder: The encoder to use.
        :type encoder: Optional[DenseEncoder]
        :param sparse_encoder: The sparse encoder to use.
        :type sparse_encoder: Optional[SparseEncoder]
        :param llm: The LLM to use.
        :type llm: Optional[BaseLLM]
        :param routes: The routes to use.
        :type routes: Optional[List[Route]]
        :param index: The index to use.
        :type index: Optional[BaseIndex]
        :param top_k: The number of routes to return.
        :type top_k: int
        :param aggregation: The aggregation method to use.
        :type aggregation: str
        :param auto_sync: The auto sync mode to use.
        :type auto_sync: Optional[str]
        """
        routes = routes.copy() if routes else []
        super().__init__(encoder=encoder, sparse_encoder=sparse_encoder, llm=llm, routes=routes, index=index, top_k=top_k, aggregation=aggregation, auto_sync=auto_sync)
        self.encoder = self._get_encoder(encoder=encoder)
        self.sparse_encoder = self._get_sparse_encoder(sparse_encoder=sparse_encoder)
        self.llm = llm
        self.routes = routes
        self.index = self._get_index(index=index)
        self._set_score_threshold()
        self.top_k = top_k
        if self.top_k < 1:
            raise ValueError(f'top_k needs to be >= 1, but was: {self.top_k}.')
        self.aggregation = aggregation
        if self.aggregation not in ['sum', 'mean', 'max']:
            raise ValueError(f"Unsupported aggregation method chosen: {aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'.")
        self.aggregation_method = self._set_aggregation_method(self.aggregation)
        if isinstance(self.index, PostgresIndex):
            self.auto_sync = 'local'
        else:
            self.auto_sync = auto_sync
        for route in self.routes:
            if route.score_threshold is None:
                route.score_threshold = self.score_threshold
        if not init_async_index:
            self._init_index_state()

    def _get_index(self, index: Optional[BaseIndex]) -> BaseIndex:
        """Get the index to use.

        :param index: The index to use.
        :type index: Optional[BaseIndex]
        :return: The index to use.
        :rtype: BaseIndex
        """
        if index is None:
            logger.warning('No index provided. Using default LocalIndex.')
            index = LocalIndex()
        else:
            index = index
        return index

    def _get_encoder(self, encoder: Optional[DenseEncoder]) -> DenseEncoder:
        """Get the dense encoder to be used for creating dense vector embeddings.

        :param encoder: The encoder to use.
        :type encoder: Optional[DenseEncoder]
        :return: The encoder to use.
        :rtype: DenseEncoder
        """
        if encoder is None:
            logger.warning('No encoder provided. Using default OpenAIEncoder.')
            encoder = OpenAIEncoder()
        else:
            encoder = encoder
        return encoder

    def _get_sparse_encoder(self, sparse_encoder: Optional[SparseEncoder]) -> Optional[SparseEncoder]:
        """Get the sparse encoder to be used for creating sparse vector embeddings.

        :param sparse_encoder: The sparse encoder to use.
        :type sparse_encoder: Optional[SparseEncoder]
        :return: The sparse encoder to use.
        :rtype: Optional[SparseEncoder]
        """
        if sparse_encoder is None:
            return None
        raise NotImplementedError(f'Sparse encoder not implemented for {self.__class__.__name__}')

    def _init_index_state(self):
        """Initializes an index (where required) and runs auto_sync if active."""
        if self.index.dimensions is None:
            dims = len(self.encoder(['test'])[0])
            self.index.dimensions = dims
        if isinstance(self.index, PineconeIndex) or isinstance(self.index, PostgresIndex):
            self.index.index = self.index._init_index(force_create=True)
        if self.auto_sync:
            local_utterances = self.to_config().to_utterances()
            remote_utterances = self.index.get_utterances(include_metadata=True)
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
            sync_strategy = diff.get_sync_strategy(self.auto_sync)
            self._execute_sync_strategy(sync_strategy)

    async def _async_init_index_state(self):
        """Asynchronously initializes an index (where required) and runs auto_sync if active."""
        if self.index is None or self.index.dimensions is None:
            dims = len(self.encoder(['test'])[0])
            self.index.dimensions = dims
        if isinstance(self.index, PineconeIndex) or isinstance(self.index, PostgresIndex):
            await self.index._init_async_index(force_create=True)
        if self.auto_sync:
            local_utterances = self.to_config().to_utterances()
            remote_utterances = await self.index.aget_utterances(include_metadata=True)
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
            sync_strategy = diff.get_sync_strategy(self.auto_sync)
            await self._async_execute_sync_strategy(sync_strategy)

    def _set_score_threshold(self):
        """Set the score threshold for the layer based on the encoder
        score threshold.

        When no score threshold is used a default `None` value
        is used, which means that a route will always be returned when
        the layer is called."""
        if self.encoder.score_threshold is not None:
            self.score_threshold = self.encoder.score_threshold
            if self.score_threshold is None:
                logger.warning("No score threshold value found in encoder. Using the default 'None' value can lead to unexpected results.")

    def check_for_matching_routes(self, top_class: str) -> Optional[Route]:
        """Check for a matching route in the routes list.

        :param top_class: The top class to check for.
        :type top_class: str
        :return: The matching route if found, otherwise None.
        :rtype: Optional[Route]
        """
        matching_route = next((route for route in self.routes if route.name == top_class), None)
        if matching_route is None:
            logger.error(f'No route found with name {top_class}. Check to see if any Routes have been defined.')
            return None
        return matching_route

    def __call__(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, simulate_static: bool=False, route_filter: Optional[List[str]]=None, limit: int | None=1) -> RouteChoice | List[RouteChoice]:
        """Call the router to get a route choice.

        :param text: The text to route.
        :type text: Optional[str]
        :param vector: The vector to route.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :return: The route choice.
        :rtype: RouteChoice | List[RouteChoice]
        """
        if not self.index.is_ready():
            raise ValueError('Index is not ready.')
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            vector = self._encode(text=[text], input_type='queries')
        vector = xq_reshape(vector)
        scores, routes = self.index.query(vector=vector[0], top_k=self.top_k, route_filter=route_filter)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(routes, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        return self._pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)

    def _pass_routes(self, scored_routes: List[Tuple[str, float, List[float]]], simulate_static: bool, text: Optional[str], limit: int | None) -> RouteChoice | list[RouteChoice]:
        """Returns a list of RouteChoice objects that passed the thresholds set.

        :param scored_routes: The scored routes to pass.
        :type scored_routes: List[Tuple[str, float, List[float]]]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param text: The text to route.
        :type text: Optional[str]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :return: The route choice.
        :rtype: RouteChoice | list[RouteChoice]
        """
        passed_routes: list[RouteChoice] = []
        for route_name, total_score, scores in scored_routes:
            route = self.check_for_matching_routes(top_class=route_name)
            if route is None:
                continue
            if (current_threshold := (route.score_threshold if route.score_threshold is not None else self.score_threshold)):
                passed = total_score >= current_threshold
            else:
                passed = True
            if passed and route is not None and (not simulate_static):
                if route.function_schemas and text is None:
                    raise ValueError('Route has a function schema, but no text was provided.')
                if route.function_schemas and (not isinstance(route.llm, BaseLLM)):
                    if not self.llm:
                        logger.warning('No LLM provided for dynamic route, will use OpenAI LLM default. Ensure API key is set in OPENAI_API_KEY environment variable.')
                        self.llm = OpenAILLM()
                        route.llm = self.llm
                    else:
                        route.llm = self.llm
                route_choice = route(query=text)
                if route_choice is not None and route_choice.similarity_score is None:
                    route_choice.similarity_score = total_score
                passed_routes.append(route_choice)
            elif passed and route is not None and simulate_static:
                passed_routes.append(RouteChoice(name=route.name, function_call=None, similarity_score=None))
            if limit is None:
                continue
            if len(passed_routes) >= limit:
                if limit == 1:
                    return passed_routes[0]
                else:
                    return passed_routes
        if len(passed_routes) == 1:
            return passed_routes[0]
        elif len(passed_routes) > 1:
            return passed_routes
        else:
            return RouteChoice()

    async def _async_pass_routes(self, scored_routes: List[Tuple[str, float, List[float]]], simulate_static: bool, text: Optional[str], limit: int | None) -> RouteChoice | list[RouteChoice]:
        """Returns a list of RouteChoice objects that passed the thresholds set. Runs any
        dynamic route calls asynchronously. If there are no dynamic routes this method is
        equivalent to _pass_routes.

        :param scored_routes: The scored routes to pass.
        :type scored_routes: List[Tuple[str, float, List[float]]]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param text: The text to route.
        :type text: Optional[str]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :return: The route choice.
        :rtype: RouteChoice | list[RouteChoice]
        """
        passed_routes: list[RouteChoice] = []
        for route_name, total_score, scores in scored_routes:
            route = self.check_for_matching_routes(top_class=route_name)
            if route is None:
                continue
            if (current_threshold := (route.score_threshold if route.score_threshold is not None else self.score_threshold)):
                passed = total_score >= current_threshold
            else:
                passed = True
            if passed and route is not None and (not simulate_static):
                if route.function_schemas and text is None:
                    raise ValueError('Route has a function schema, but no text was provided.')
                if route.function_schemas and (not isinstance(route.llm, BaseLLM)):
                    if not self.llm:
                        logger.warning('No LLM provided for dynamic route, will use OpenAI LLM default. Ensure API key is set in OPENAI_API_KEY environment variable.')
                        self.llm = OpenAILLM()
                        route.llm = self.llm
                    else:
                        route.llm = self.llm
                route_choice = await route.acall(query=text)
                if route_choice is not None and route_choice.similarity_score is None:
                    route_choice.similarity_score = total_score
                passed_routes.append(route_choice)
            elif passed and route is not None and simulate_static:
                passed_routes.append(RouteChoice(name=route.name, function_call=None, similarity_score=None))
            if limit is None:
                continue
            if len(passed_routes) >= limit:
                if limit == 1:
                    return passed_routes[0]
                else:
                    return passed_routes
        if len(passed_routes) == 1:
            return passed_routes[0]
        elif len(passed_routes) > 1:
            return passed_routes
        else:
            return RouteChoice()

    async def acall(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, limit: int | None=1, simulate_static: bool=False, route_filter: Optional[List[str]]=None) -> RouteChoice | list[RouteChoice]:
        """Asynchronously call the router to get a route choice.

        :param text: The text to route.
        :type text: Optional[str]
        :param vector: The vector to route.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route (ie avoid dynamic route
            LLM calls during fit or evaluate).
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :return: The route choice.
        :rtype: RouteChoice
        """
        if not await self.index.ais_ready():
            await self._async_init_index_state()
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            vector = await self._async_encode(text=[text], input_type='queries')
        vector = xq_reshape(vector)
        scores, routes = await self.index.aquery(vector=vector[0], top_k=self.top_k, route_filter=route_filter)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(routes, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        return await self._async_pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)

    def _index_ready(self) -> bool:
        """Method to check if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        if self.index.index is None or self.routes is None:
            return False
        if isinstance(self.index, QdrantIndex):
            info = self.index.describe()
            if info.vectors == 0:
                return False
        return True

    def sync(self, sync_mode: str, force: bool=False, wait: int=0) -> List[str]:
        """Runs a sync of the local routes with the remote index.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :param force: Whether to force the sync even if the local and remote
            hashes already match. Defaults to False.
        :type force: bool, optional
        :param wait: The number of seconds to wait for the index to be unlocked
        before proceeding with the sync. If set to 0, will raise an error if
        index is already locked/unlocked.
        :type wait: int
        :return: A list of diffs describing the addressed differences between
            the local and remote route layers.
        :rtype: List[str]
        """
        if not force and self.is_synced():
            logger.warning('Local and remote route layers are already synchronized.')
            local_utterances = self.to_config().to_utterances()
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=local_utterances)
            return diff.to_utterance_str()
        try:
            diff_utt_str: list[str] = []
            _ = self.index.lock(value=True, wait=wait)
            try:
                local_utterances = self.to_config().to_utterances()
                remote_utterances = self.index.get_utterances(include_metadata=True)
                diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
                sync_strategy = diff.get_sync_strategy(sync_mode=sync_mode)
                self._execute_sync_strategy(sync_strategy)
                diff_utt_str = diff.to_utterance_str()
            except Exception as e:
                logger.error(f'Failed to create diff: {e}')
                raise e
            finally:
                _ = self.index.lock(value=False)
        except Exception as e:
            logger.error(f'Failed to lock index for sync: {e}')
            raise e
        return diff_utt_str

    async def async_sync(self, sync_mode: str, force: bool=False, wait: int=0) -> List[str]:
        """Runs a sync of the local routes with the remote index.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :param force: Whether to force the sync even if the local and remote
            hashes already match. Defaults to False.
        :type force: bool, optional
        :param wait: The number of seconds to wait for the index to be unlocked
        before proceeding with the sync. If set to 0, will raise an error if
        index is already locked/unlocked.
        :type wait: int
        :return: A list of diffs describing the addressed differences between
            the local and remote route layers.
        :rtype: List[str]
        """
        if not force and await self.async_is_synced():
            logger.warning('Local and remote route layers are already synchronized.')
            local_utterances = self.to_config().to_utterances()
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=local_utterances)
            return diff.to_utterance_str()
        try:
            diff_utt_str: list[str] = []
            _ = await self.index.alock(value=True, wait=wait)
            try:
                local_utterances = self.to_config().to_utterances()
                remote_utterances = await self.index.aget_utterances(include_metadata=True)
                diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
                sync_strategy = diff.get_sync_strategy(sync_mode=sync_mode)
                await self._async_execute_sync_strategy(sync_strategy)
                diff_utt_str = diff.to_utterance_str()
            except Exception as e:
                logger.error(f'Failed to create diff: {e}')
                raise e
            finally:
                _ = await self.index.alock(value=False)
        except Exception as e:
            logger.error(f'Failed to lock index for sync: {e}')
            raise e
        return diff_utt_str

    def _execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            self.index._remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            self.index.add(embeddings=self.encoder(utterances_text), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']])
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        self._write_hash()

    async def _async_execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            await self.index._async_remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            await self.index.aadd(embeddings=await self.encoder.acall(docs=utterances_text), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']])
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        await self._async_write_hash()

    def _local_upsert(self, utterances: List[Utterance]):
        """Adds new routes to the SemanticRouter.

        :param utterances: The utterances to add to the local SemanticRouter.
        :type utterances: List[Utterance]
        """
        new_routes = {route.name: route for route in self.routes}
        for utt_obj in utterances:
            if utt_obj.route not in new_routes.keys():
                new_routes[utt_obj.route] = Route(name=utt_obj.route, utterances=[utt_obj.utterance], function_schemas=utt_obj.function_schemas, metadata=utt_obj.metadata)
            else:
                if utt_obj.utterance not in new_routes[utt_obj.route].utterances:
                    new_routes[utt_obj.route].utterances.append(utt_obj.utterance)
                new_routes[utt_obj.route].function_schemas = utt_obj.function_schemas
                new_routes[utt_obj.route].metadata = utt_obj.metadata
        self.routes = list(new_routes.values())

    def _local_delete(self, utterances: List[Utterance]):
        """Deletes routes from the local SemanticRouter.

        :param utterances: The utterances to delete from the local SemanticRouter.
        :type utterances: List[Utterance]
        """
        route_dict: dict[str, List[str]] = {}
        for utt in utterances:
            route_dict.setdefault(utt.route, []).append(utt.utterance)
        new_routes = []
        for route in self.routes:
            if route.name in route_dict.keys():
                new_utterances = list(set(route.utterances) - set(route_dict[route.name]))
                if len(new_utterances) == 0:
                    continue
                else:
                    new_routes.append(Route(name=route.name, utterances=new_utterances, function_schemas=route.function_schemas, metadata=route.metadata))
            else:
                new_routes.append(route)
        self.routes = new_routes

    def __str__(self):
        return f'{self.__class__.__name__}(encoder={self.encoder}, score_threshold={self.score_threshold}, routes={self.routes})'

    @classmethod
    def from_json(cls, file_path: str):
        """Load a RouterConfig from a JSON file.

        :param file_path: The path to the JSON file.
        :type file_path: str
        :return: The RouterConfig object.
        :rtype: RouterConfig
        """
        config = RouterConfig.from_file(file_path)
        encoder = AutoEncoder(type=config.encoder_type, name=config.encoder_name).model
        if isinstance(encoder, DenseEncoder):
            return cls(encoder=encoder, routes=config.routes)
        else:
            raise ValueError(f'{type(encoder)} not supported for loading from JSON.')

    @classmethod
    def from_yaml(cls, file_path: str):
        """Load a RouterConfig from a YAML file.

        :param file_path: The path to the YAML file.
        :type file_path: str
        :return: The RouterConfig object.
        :rtype: RouterConfig
        """
        config = RouterConfig.from_file(file_path)
        encoder = AutoEncoder(type=config.encoder_type, name=config.encoder_name).model
        if isinstance(encoder, DenseEncoder):
            return cls(encoder=encoder, routes=config.routes)
        else:
            raise ValueError(f'{type(encoder)} not supported for loading from YAML.')

    @classmethod
    def from_config(cls, config: RouterConfig, index: Optional[BaseIndex]=None):
        """Create a Router from a RouterConfig object.

        :param config: The RouterConfig object.
        :type config: RouterConfig
        :param index: The index to use.
        :type index: Optional[BaseIndex]
        """
        encoder = AutoEncoder(type=config.encoder_type, name=config.encoder_name).model
        if isinstance(encoder, DenseEncoder):
            return cls(encoder=encoder, routes=config.routes, index=index)
        else:
            raise ValueError(f'{type(encoder)} not supported for loading from config.')

    def add(self, routes: List[Route] | Route):
        """Add a route to the local SemanticRouter and index.

        :param route: The route to add.
        :type route: Route
        """
        raise NotImplementedError('This method must be implemented by subclasses.')

    async def aadd(self, routes: List[Route] | Route):
        """Add a route to the local SemanticRouter and index asynchronously.

        :param route: The route to add.
        :type route: Route
        """
        logger.warning('Async method not implemented.')
        return self.add(routes)

    def list_route_names(self) -> List[str]:
        return [route.name for route in self.routes]

    def update(self, name: str, threshold: Optional[float]=None, utterances: Optional[List[str]]=None):
        """Updates the route specified in name. Allows the update of
        threshold and/or utterances. If no values are provided via the
        threshold or utterances parameters, those fields are not updated.
        If neither field is provided raises a ValueError.

        The name must exist within the local SemanticRouter, if not a
        KeyError will be raised.

        :param name: The name of the route to update.
        :type name: str
        :param threshold: The threshold to update.
        :type threshold: Optional[float]
        :param utterances: The utterances to update.
        :type utterances: Optional[List[str]]
        """
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if threshold is None and utterances is None:
            raise ValueError("At least one of 'threshold' or 'utterances' must be provided.")
        if utterances:
            raise NotImplementedError('The update method cannot be used for updating utterances yet.')
        route = self.get(name)
        if route:
            if threshold:
                old_threshold = route.score_threshold
                route.score_threshold = threshold
                logger.info(f"Updated threshold for route '{route.name}' from {old_threshold} to {threshold}")
        else:
            raise ValueError(f"Route '{name}' not found. Nothing updated.")
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    def delete(self, route_name: str):
        """Deletes a route given a specific route name.

        :param route_name: the name of the route to be deleted
        :type str:
        """
        if self.index._is_locked():
            raise ValueError('Index is locked. Cannot delete route.')
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if route_name not in [route.name for route in self.routes]:
            err_msg = f'Route `{route_name}` not found in {self.__class__.__name__}'
            logger.warning(err_msg)
            try:
                self.index.delete(route_name=route_name)
            except Exception as e:
                logger.error(f'Failed to delete route from the index: {e}')
        else:
            self.routes = [route for route in self.routes if route.name != route_name]
            self.index.delete(route_name=route_name)
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    async def adelete(self, route_name: str):
        """Deletes a route given a specific route name asynchronously.

        :param route_name: the name of the route to be deleted
        :type str:
        """
        if await self.index._ais_locked():
            raise ValueError('Index is locked. Cannot delete route.')
        current_local_hash = self._get_hash()
        current_remote_hash = await self.index._async_read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if route_name not in [route.name for route in self.routes]:
            err_msg = f'Route `{route_name}` not found in {self.__class__.__name__}'
            logger.warning(err_msg)
            try:
                await self.index.adelete(route_name=route_name)
            except Exception as e:
                logger.error(f'Failed to delete route from the index: {e}')
        else:
            self.routes = [route for route in self.routes if route.name != route_name]
            await self.index.adelete(route_name=route_name)
        if current_local_hash.value == current_remote_hash.value:
            await self._async_write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    def _refresh_routes(self):
        """Pulls out the latest routes from the index.

        Not yet implemented for BaseRouter.
        """
        raise NotImplementedError('This method has not yet been implemented.')
        route_mapping = {route.name: route for route in self.routes}
        index_routes = self.index.get_utterances()
        new_routes_names = []
        new_routes = []
        for route_name, utterance in index_routes:
            if route_name in route_mapping:
                if route_name not in new_routes_names:
                    existing_route = route_mapping[route_name]
                    new_routes.append(existing_route)
                new_routes.append(Route(name=route_name, utterances=[utterance]))
            route = route_mapping[route_name]
            self.routes.append(route)

    def _get_hash(self) -> ConfigParameter:
        """Get the hash of the current routes.

        :return: The hash of the current routes.
        :rtype: ConfigParameter
        """
        config = self.to_config()
        return config.get_hash()

    def _write_hash(self) -> ConfigParameter:
        """Write the hash of the current routes to the index.

        :return: The hash of the current routes.
        :rtype: ConfigParameter
        """
        config = self.to_config()
        hash_config = config.get_hash()
        self.index._write_config(config=hash_config)
        return hash_config

    async def _async_write_hash(self) -> ConfigParameter:
        """Write the hash of the current routes to the index asynchronously.

        :return: The hash of the current routes.
        :rtype: ConfigParameter
        """
        config = self.to_config()
        hash_config = config.get_hash()
        await self.index._async_write_config(config=hash_config)
        return hash_config

    def is_synced(self) -> bool:
        """Check if the local and remote route layer instances are
        synchronized.

        :return: True if the local and remote route layers are synchronized,
            False otherwise.
        :rtype: bool
        """
        local_hash = self._get_hash()
        remote_hash = self.index._read_hash()
        if local_hash.value == remote_hash.value:
            return True
        else:
            return False

    async def async_is_synced(self) -> bool:
        """Check if the local and remote route layer instances are
        synchronized asynchronously.

        :return: True if the local and remote route layers are synchronized,
            False otherwise.
        :rtype: bool
        """
        local_hash = self._get_hash()
        remote_hash = await self.index._async_read_hash()
        if local_hash.value == remote_hash.value:
            return True
        else:
            return False

    def get_utterance_diff(self, include_metadata: bool=False) -> List[str]:
        """Get the difference between the local and remote utterances. Returns
        a list of strings showing what is different in the remote when compared
        to the local. For example:

        ["  route1: utterance1",
         "  route1: utterance2",
         "- route2: utterance3",
         "- route2: utterance4"]

        Tells us that the remote is missing "route2: utterance3" and "route2:
        utterance4", which do exist locally. If we see:

        ["  route1: utterance1",
         "  route1: utterance2",
         "+ route2: utterance3",
         "+ route2: utterance4"]

        This diff tells us that the remote has "route2: utterance3" and
        "route2: utterance4", which do not exist locally.

        :param include_metadata: Whether to include metadata in the diff.
        :type include_metadata: bool
        :return: A list of strings showing the difference between the local and remote
            utterances.
        :rtype: List[str]
        """
        remote_utterances = self.index.get_utterances(include_metadata=include_metadata)
        local_utterances = self.to_config().to_utterances()
        diff_obj = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
        return diff_obj.to_utterance_str(include_metadata=include_metadata)

    async def aget_utterance_diff(self, include_metadata: bool=False) -> List[str]:
        """Get the difference between the local and remote utterances asynchronously.
        Returns a list of strings showing what is different in the remote when
        compared to the local. For example:

        ["  route1: utterance1",
         "  route1: utterance2",
         "- route2: utterance3",
         "- route2: utterance4"]

        Tells us that the remote is missing "route2: utterance3" and "route2:
        utterance4", which do exist locally. If we see:

        ["  route1: utterance1",
         "  route1: utterance2",
         "+ route2: utterance3",
         "+ route2: utterance4"]

        This diff tells us that the remote has "route2: utterance3" and
        "route2: utterance4", which do not exist locally.

        :param include_metadata: Whether to include metadata in the diff.
        :type include_metadata: bool
        :return: A list of strings showing the difference between the local and remote
            utterances.
        :rtype: List[str]
        """
        remote_utterances = await self.index.aget_utterances(include_metadata=include_metadata)
        local_utterances = self.to_config().to_utterances()
        diff_obj = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
        return diff_obj.to_utterance_str(include_metadata=include_metadata)

    def _extract_routes_details(self, routes: List[Route], include_metadata: bool=False) -> Tuple:
        """Extract the routes details.

        :param routes: The routes to extract the details from.
        :type routes: List[Route]
        :param include_metadata: Whether to include metadata in the details.
        :type include_metadata: bool
        :return: A tuple of the route names, utterances, and function schemas.
        """
        route_names = [route.name for route in routes for _ in route.utterances]
        utterances = [utterance for route in routes for utterance in route.utterances]
        function_schemas = [route.function_schemas[0] if route.function_schemas and len(route.function_schemas) > 0 else {} for route in routes for _ in route.utterances]
        if include_metadata:
            metadata = [route.metadata for route in routes for _ in route.utterances]
            return (route_names, utterances, function_schemas, metadata)
        return (route_names, utterances, function_schemas)

    def _encode(self, text: list[str], input_type: EncodeInputType) -> Any:
        """Generates embeddings for a given text.

        Must be implemented by a subclass.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The embeddings of the text.
        :rtype: Any
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def _async_encode(self, text: list[str], input_type: EncodeInputType) -> Any:
        """Asynchronously generates embeddings for a given text.

        Must be implemented by a subclass.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The embeddings of the text.
        :rtype: Any
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def _set_aggregation_method(self, aggregation: str='sum'):
        """Set the aggregation method.

        :param aggregation: The aggregation method to use.
        :type aggregation: str
        :return: The aggregation method.
        :rtype: Callable
        """
        if aggregation == 'sum':
            return lambda x: sum(x)
        elif aggregation == 'mean':
            return lambda x: np.mean(x)
        elif aggregation == 'max':
            return lambda x: max(x)
        else:
            raise ValueError(f"Unsupported aggregation method chosen: {aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'.")

    def _score_routes(self, query_results: list[dict]) -> list[tuple[str, float, list[float]]]:
        """Score the routes based on the query results.

        :param query_results: The query results to score.
        :type query_results: List[Dict]
        :return: A tuple of routes, their total scores, and their individual scores.
        """
        scores_by_class = self.group_scores_by_class(query_results)
        if self.aggregation_method is None:
            raise ValueError('self.aggregation_method is not set.')
        total_scores = [(route, self.aggregation_method(scores), scores) for route, scores in scores_by_class.items()]
        total_scores.sort(key=lambda x: x[1], reverse=True)
        return total_scores

    @deprecated('Direct use of `_semantic_classify` is deprecated. Use `__call__` or `acall` instead.')
    def _semantic_classify(self, query_results: List[Dict]) -> Tuple[str, List[float]]:
        """Classify the query results into a single class based on the highest total score.
        If no classification is found, return an empty string and an empty list.

        :param query_results: The query results to classify. Expected format is a list of
        dictionaries with "route" and "score" keys.
        :type query_results: List[Dict]
        :return: A tuple containing the top class and its associated scores.
        :rtype: Tuple[str, List[float]]
        """
        top_class, top_score, scores = self._score_routes(query_results)[0]
        if top_class is not None:
            return (str(top_class), scores)
        else:
            logger.warning('No classification found for semantic classifier.')
            return ('', [])

    def get(self, name: str) -> Optional[Route]:
        """Get a route by name.

        :param name: The name of the route to get.
        :type name: str
        :return: The route.
        :rtype: Optional[Route]
        """
        for route in self.routes:
            if route.name == name:
                return route
        logger.error(f'Route `{name}` not found')
        return None

    def group_scores_by_class(self, query_results: List[Dict]) -> Dict[str, List[float]]:
        """Group the scores by class.

        :param query_results: The query results to group. Expected format is a list of
        dictionaries with "route" and "score" keys.
        :type query_results: List[Dict]
        :return: A dictionary of route names and their associated scores.
        :rtype: Dict[str, List[float]]
        """
        scores_by_class: Dict[str, List[float]] = {}
        for result in query_results:
            score = result['score']
            route = result['route']
            if route in scores_by_class:
                scores_by_class[route].append(score)
            else:
                scores_by_class[route] = [score]
        return scores_by_class

    def _update_thresholds(self, route_thresholds: Optional[Dict[str, float]]=None):
        """Update the score thresholds for each route using a dictionary of
        route names and thresholds.

        :param route_thresholds: A dictionary of route names and thresholds.
        :type route_thresholds: Dict[str, float] | None
        """
        if route_thresholds:
            for route, threshold in route_thresholds.items():
                self.set_threshold(threshold=threshold, route_name=route)

    def set_threshold(self, threshold: float, route_name: str | None=None):
        """Set the score threshold for a specific route or all routes. A `threshold` of 0.0
        will mean that the route will be returned no matter how low it scores whereas
        a threshold of 1.0 will mean that a route must contain an exact utterance match
        to be returned.

        :param threshold: The threshold to set.
        :type threshold: float
        :param route_name: The name of the route to set the threshold for. If None, the
        threshold will be set for all routes.
        :type route_name: str | None
        """
        if route_name is None:
            for route in self.routes:
                route.score_threshold = threshold
            self.score_threshold = threshold
        else:
            route_get: Route | None = self.get(route_name)
            if route_get is not None:
                route_get.score_threshold = threshold
            else:
                logger.error(f'Route `{route_name}` not found')

    def to_config(self) -> RouterConfig:
        """Convert the router to a RouterConfig object.

        :return: The RouterConfig object.
        :rtype: RouterConfig
        """
        return RouterConfig(encoder_type=self.encoder.type, encoder_name=self.encoder.name, routes=self.routes)

    def to_json(self, file_path: str):
        """Convert the router to a JSON file.

        :param file_path: The path to the JSON file.
        :type file_path: str
        """
        config = self.to_config()
        config.to_file(file_path)

    def to_yaml(self, file_path: str):
        """Convert the router to a YAML file.

        :param file_path: The path to the YAML file.
        :type file_path: str
        """
        config = self.to_config()
        config.to_file(file_path)

    def get_thresholds(self) -> Dict[str, float]:
        """Get the score thresholds for each route.

        :return: A dictionary of route names and their associated thresholds.
        :rtype: Dict[str, float]
        """
        thresholds = {route.name: route.score_threshold or self.score_threshold or 0.0 for route in self.routes}
        return thresholds

    def fit(self, X: List[str], y: List[str], batch_size: int=500, max_iter: int=500, local_execution: bool=False):
        """Fit the router to the data. Works best with a large number of examples for each
        route and with many `None` utterances.

        :param X: The input data.
        :type X: List[str]
        :param y: The output data.
        :type y: List[str]
        :param batch_size: The batch size to use for fitting.
        :type batch_size: int
        :param max_iter: The maximum number of iterations to use for fitting.
        :type max_iter: int
        :param local_execution: Whether to execute the fitting locally.
        :type local_execution: bool
        """
        original_index = self.index
        if local_execution:
            from semantic_router.index.local import LocalIndex
            remote_utterances = self.index.get_utterances(include_metadata=True)
            routes = []
            utterances = []
            metadata = []
            for utterance in remote_utterances:
                routes.append(utterance.route)
                utterances.append(utterance.utterance)
                metadata.append(utterance.metadata)
            embeddings = self.encoder(utterances)
            self.index = LocalIndex()
            self.index.add(embeddings=embeddings, routes=routes, utterances=utterances, metadata_list=metadata)
        Xq: List[List[float]] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb = np.array(self.encoder(X[i:i + batch_size]))
            Xq.extend(emb)
        best_acc = self._vec_evaluate(Xq_d=np.array(Xq), y=y)
        best_thresholds = self.get_thresholds()
        for _ in (pbar := tqdm(range(max_iter), desc='Training')):
            pbar.set_postfix({'acc': round(best_acc, 2)})
            thresholds = threshold_random_search(route_layer=self, search_range=0.8)
            self._update_thresholds(route_thresholds=thresholds)
            acc = self._vec_evaluate(Xq_d=Xq, y=y)
            if acc > best_acc:
                best_acc = acc
                best_thresholds = thresholds
        self._update_thresholds(route_thresholds=best_thresholds)
        if local_execution:
            self.index = original_index

    def evaluate(self, X: List[str], y: List[str], batch_size: int=500) -> float:
        """Evaluate the accuracy of the route selection.

        :param X: The input data.
        :type X: List[str]
        :param y: The output data.
        :type y: List[str]
        :param batch_size: The batch size to use for evaluation.
        :type batch_size: int
        :return: The accuracy of the route selection.
        :rtype: float
        """
        Xq: List[List[float]] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb = np.array(self.encoder(X[i:i + batch_size]))
            Xq.extend(emb)
        accuracy = self._vec_evaluate(Xq_d=np.array(Xq), y=y)
        return accuracy

    def _vec_evaluate(self, Xq_d: Union[List[float], Any], y: List[str], **kwargs) -> float:
        """Evaluate the accuracy of the route selection.

        :param Xq_d: The input data.
        :type Xq_d: Union[List[float], Any]
        :param y: The output data.
        :type y: List[str]
        :return: The accuracy of the route selection.
        :rtype: float
        """
        correct = 0
        for xq, target_route in zip(Xq_d, y):
            route_choice = self(vector=xq, simulate_static=True)
            if isinstance(route_choice, list):
                route_name = route_choice[0].name
            else:
                route_name = route_choice.name
            if route_name == target_route:
                correct += 1
        accuracy = correct / len(Xq_d)
        return accuracy

    def _get_route_names(self) -> List[str]:
        """Get the names of the routes.

        :return: The names of the routes.
        :rtype: List[str]
        """
        return [route.name for route in self.routes]

    @deprecated('Use `__call__` or `acall` with `limit=None` instead.')
    def _semantic_classify_multiple_routes(self, query_results: list[dict]) -> list[dict]:
        """Classify the query results into a list of routes.

        :param query_results: The query results to classify.
        :type query_results: List[Dict]
        :return: Most similar results with scores.
        :rtype list[dict]:
        """
        raise NotImplementedError('This method has been deprecated. Use `__call__` or `acall` with `limit=None` instead.')

def _local_upsert(self, utterances: List[Utterance]):
    """Adds new routes to the SemanticRouter.

        :param utterances: The utterances to add to the local SemanticRouter.
        :type utterances: List[Utterance]
        """
    new_routes = {route.name: route for route in self.routes}
    for utt_obj in utterances:
        if utt_obj.route not in new_routes.keys():
            new_routes[utt_obj.route] = Route(name=utt_obj.route, utterances=[utt_obj.utterance], function_schemas=utt_obj.function_schemas, metadata=utt_obj.metadata)
        else:
            if utt_obj.utterance not in new_routes[utt_obj.route].utterances:
                new_routes[utt_obj.route].utterances.append(utt_obj.utterance)
            new_routes[utt_obj.route].function_schemas = utt_obj.function_schemas
            new_routes[utt_obj.route].metadata = utt_obj.metadata
    self.routes = list(new_routes.values())

def _score_routes(self, query_results: list[dict]) -> list[tuple[str, float, list[float]]]:
    """Score the routes based on the query results.

        :param query_results: The query results to score.
        :type query_results: List[Dict]
        :return: A tuple of routes, their total scores, and their individual scores.
        """
    scores_by_class = self.group_scores_by_class(query_results)
    if self.aggregation_method is None:
        raise ValueError('self.aggregation_method is not set.')
    total_scores = [(route, self.aggregation_method(scores), scores) for route, scores in scores_by_class.items()]
    total_scores.sort(key=lambda x: x[1], reverse=True)
    return total_scores

def group_scores_by_class(self, query_results: List[Dict]) -> Dict[str, List[float]]:
    """Group the scores by class.

        :param query_results: The query results to group. Expected format is a list of
        dictionaries with "route" and "score" keys.
        :type query_results: List[Dict]
        :return: A dictionary of route names and their associated scores.
        :rtype: Dict[str, List[float]]
        """
    scores_by_class: Dict[str, List[float]] = {}
    for result in query_results:
        score = result['score']
        route = result['route']
        if route in scores_by_class:
            scores_by_class[route].append(score)
        else:
            scores_by_class[route] = [score]
    return scores_by_class

def _update_thresholds(self, route_thresholds: Optional[Dict[str, float]]=None):
    """Update the score thresholds for each route using a dictionary of
        route names and thresholds.

        :param route_thresholds: A dictionary of route names and thresholds.
        :type route_thresholds: Dict[str, float] | None
        """
    if route_thresholds:
        for route, threshold in route_thresholds.items():
            self.set_threshold(threshold=threshold, route_name=route)

def _vec_evaluate(self, Xq_d: Union[List[float], Any], y: List[str], **kwargs) -> float:
    """Evaluate the accuracy of the route selection.

        :param Xq_d: The input data.
        :type Xq_d: Union[List[float], Any]
        :param y: The output data.
        :type y: List[str]
        :return: The accuracy of the route selection.
        :rtype: float
        """
    correct = 0
    for xq, target_route in zip(Xq_d, y):
        route_choice = self(vector=xq, simulate_static=True)
        if isinstance(route_choice, list):
            route_name = route_choice[0].name
        else:
            route_name = route_choice.name
        if route_name == target_route:
            correct += 1
    accuracy = correct / len(Xq_d)
    return accuracy

def threshold_random_search(route_layer: BaseRouter, search_range: Union[int, float]) -> Dict[str, float]:
    """Performs a random search iteration given a route layer and a search range.

    :param route_layer: The route layer to search.
    :type route_layer: BaseRouter
    :param search_range: The search range to use.
    :type search_range: Union[int, float]
    :return: A dictionary of route names and their associated thresholds.
    :rtype: Dict[str, float]
    """
    routes = route_layer.get_thresholds()
    route_names = list(routes.keys())
    route_thresholds = list(routes.values())
    score_threshold_values = []
    for threshold in route_thresholds:
        score_threshold_values.append(np.linspace(start=max(threshold - search_range, 0.0), stop=min(threshold + search_range, 1.0), num=100))
    score_thresholds = {route: random.choice(score_threshold_values[i]) for i, route in enumerate(route_names)}
    return score_thresholds

class HybridRouter(BaseRouter):
    """A hybrid layer that uses both dense and sparse embeddings to classify routes."""
    sparse_encoder: Optional[SparseEncoder] = Field(default=None)
    alpha: float = 0.3

    def __init__(self, encoder: DenseEncoder, sparse_encoder: Optional[SparseEncoder]=None, llm: Optional[BaseLLM]=None, routes: Optional[List[Route]]=None, index: Optional[HybridLocalIndex]=None, top_k: int=5, aggregation: str='mean', auto_sync: Optional[str]=None, alpha: float=0.3, init_async_index: bool=False):
        """Initialize the HybridRouter.

        :param encoder: The dense encoder to use.
        :type encoder: DenseEncoder
        :param sparse_encoder: The sparse encoder to use.
        :type sparse_encoder: Optional[SparseEncoder]
        """
        if index is None:
            logger.warning('No index provided. Using default HybridLocalIndex.')
            index = HybridLocalIndex()
        encoder = self._get_encoder(encoder=encoder)
        sparse_encoder = self._get_sparse_encoder(sparse_encoder=sparse_encoder)
        if isinstance(sparse_encoder, FittableMixin) and routes:
            sparse_encoder.fit(routes)
        super().__init__(encoder=encoder, sparse_encoder=sparse_encoder, llm=llm, routes=routes, index=index, top_k=top_k, aggregation=aggregation, auto_sync=auto_sync, init_async_index=init_async_index)
        self.alpha = alpha

    def _set_score_threshold(self):
        """Set the score threshold for the HybridRouter. Unlike the base router the
        encoder score threshold is not used directly. Instead, the dense encoder
        score threshold is multiplied by the alpha value, resulting in a lower
        score threshold. This is done to account for the difference in returned
        scores from the hybrid router.
        """
        if self.encoder.score_threshold is not None:
            self.score_threshold = self.encoder.score_threshold * self.alpha
            if self.score_threshold is None:
                logger.warning("No score threshold value found in encoder. Using the default 'None' value can lead to unexpected results.")

    def add(self, routes: List[Route] | Route):
        """Add a route to the local HybridRouter and index.

        :param route: The route to add.
        :type route: Route
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse Encoder not initialised.')
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if isinstance(routes, Route):
            routes = [routes]
        self.routes.extend(routes)
        if isinstance(self.sparse_encoder, FittableMixin) and self.routes:
            self.sparse_encoder.fit(self.routes)
        route_names, all_utterances, all_function_schemas, all_metadata = self._extract_routes_details(routes, include_metadata=True)
        dense_emb, sparse_emb = self._encode(all_utterances, input_type='documents')
        self.index.add(embeddings=dense_emb.tolist(), routes=route_names, utterances=all_utterances, function_schemas=all_function_schemas, metadata_list=all_metadata, sparse_embeddings=sparse_emb)
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    async def aadd(self, routes: List[Route] | Route):
        """Add a route to the local HybridRouter and index asynchronously.

        :param routes: The route(s) to add.
        :type routes: List[Route] | Route
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse Encoder not initialised.')
        current_local_hash = self._get_hash()
        current_remote_hash = await self.index._async_read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if isinstance(routes, Route):
            routes = [routes]
        self.routes.extend(routes)
        if isinstance(self.sparse_encoder, FittableMixin) and self.routes:
            self.sparse_encoder.fit(self.routes)
        route_names, all_utterances, all_function_schemas, all_metadata = self._extract_routes_details(routes, include_metadata=True)
        dense_emb, sparse_emb = await self._async_encode(all_utterances, input_type='documents')
        await self.index.aadd(embeddings=dense_emb.tolist(), routes=route_names, utterances=all_utterances, function_schemas=all_function_schemas, metadata_list=all_metadata, sparse_embeddings=sparse_emb)
        if current_local_hash.value == current_remote_hash.value:
            await self._async_write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    def _execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse Encoder not initialised.')
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            self.index._remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            dense_emb, sparse_emb = self._encode(utterances_text, input_type='documents')
            self.index.add(embeddings=dense_emb.tolist(), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']], sparse_embeddings=sparse_emb)
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        self._write_hash()
        if isinstance(self.sparse_encoder, FittableMixin) and self.routes:
            self.sparse_encoder.fit(self.routes)

    def _get_index(self, index: Optional[BaseIndex]) -> BaseIndex:
        """Get the index.

        :param index: The index to get.
        :type index: Optional[BaseIndex]
        :return: The index.
        :rtype: BaseIndex
        """
        if index is None:
            logger.warning('No index provided. Using default HybridLocalIndex.')
            index = HybridLocalIndex()
        else:
            index = index
        return index

    def _get_sparse_encoder(self, sparse_encoder: Optional[SparseEncoder]) -> SparseEncoder:
        """Get the sparse encoder.

        :param sparse_encoder: The sparse encoder to get.
        :type sparse_encoder: Optional[SparseEncoder]
        :return: The sparse encoder.
        :rtype: Optional[SparseEncoder]
        """
        if sparse_encoder is None:
            logger.warning('No sparse_encoder provided. Using default BM25Encoder.')
            sparse_encoder = BM25Encoder()
        else:
            sparse_encoder = sparse_encoder
        return sparse_encoder

    def _encode(self, text: list[str], input_type: EncodeInputType) -> tuple[np.ndarray, list[SparseEmbedding]]:
        """Given some text, generates dense and sparse embeddings, then scales them
        using the chosen alpha value.

        :param text: List of texts to encode
        :type text: List[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: Tuple of dense and sparse embeddings
        """
        if self.sparse_encoder is None:
            raise ValueError('self.sparse_encoder is not set.')
        if isinstance(self.encoder, AsymmetricDenseMixin):
            match input_type:
                case 'queries':
                    dense_v = self.encoder.encode_queries(text)
                case 'documents':
                    dense_v = self.encoder.encode_documents(text)
        else:
            dense_v = self.encoder(text)
        xq_d = np.array(dense_v)
        if isinstance(self.sparse_encoder, AsymmetricSparseMixin):
            match input_type:
                case 'queries':
                    xq_s = self.sparse_encoder.encode_queries(text)
                case 'documents':
                    xq_s = self.sparse_encoder.encode_documents(text)
        else:
            xq_s = self.sparse_encoder(text)
        xq_d, xq_s = self._convex_scaling(dense=xq_d, sparse=xq_s)
        return (xq_d, xq_s)

    async def _async_encode(self, text: List[str], input_type: EncodeInputType) -> tuple[np.ndarray, list[SparseEmbedding]]:
        """Given some text, generates dense and sparse embeddings, then scales them
        using the chosen alpha value.

        :param text: The text to encode.
        :type text: List[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: A tuple of the dense and sparse embeddings.
        :rtype: tuple[np.ndarray, list[SparseEmbedding]]
        """
        if self.sparse_encoder is None:
            raise ValueError('self.sparse_encoder is not set.')
        if isinstance(self.encoder, AsymmetricDenseMixin):
            match input_type:
                case 'queries':
                    dense_coro = self.encoder.aencode_queries(text)
                case 'documents':
                    dense_coro = self.encoder.aencode_documents(text)
        else:
            dense_coro = self.encoder.acall(text)
        if isinstance(self.sparse_encoder, AsymmetricSparseMixin):
            match input_type:
                case 'queries':
                    sparse_coro = self.sparse_encoder.aencode_queries(text)
                case 'documents':
                    sparse_coro = self.sparse_encoder.aencode_documents(text)
        else:
            sparse_coro = self.sparse_encoder.acall(text)
        dense_vec, xq_s = await asyncio.gather(dense_coro, sparse_coro)
        xq_d = np.array(dense_vec)
        xq_d, xq_s = self._convex_scaling(dense=xq_d, sparse=xq_s)
        return (xq_d, xq_s)

    def __call__(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, simulate_static: bool=False, route_filter: Optional[List[str]]=None, limit: int | None=1, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> RouteChoice | list[RouteChoice]:
        """Call the HybridRouter.

        :param text: The text to encode.
        :type text: Optional[str]
        :param vector: The vector to encode.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :param sparse_vector: The sparse vector to use.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A RouteChoice or a list of RouteChoices.
        :rtype: RouteChoice | list[RouteChoice]
        """
        if not self.index.is_ready():
            raise ValueError('Index is not ready.')
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        potential_sparse_vector: List[SparseEmbedding] | None = None
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            xq_d = np.array(self.encoder([text]))
            xq_s = self.sparse_encoder([text])
            vector, potential_sparse_vector = self._convex_scaling(dense=xq_d, sparse=xq_s)
        vector = xq_reshape(vector)
        if sparse_vector is None:
            if text is None:
                raise ValueError('Either text or sparse_vector must be provided')
            sparse_vector = potential_sparse_vector[0] if potential_sparse_vector else None
        if sparse_vector is None:
            raise ValueError('Sparse vector is required for HybridLocalIndex.')
        scores, route_names = self.index.query(vector=vector[0], top_k=self.top_k, route_filter=route_filter, sparse_vector=sparse_vector)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(route_names, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        route_choices = self._pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)
        return route_choices

    async def acall(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, limit: int | None=1, simulate_static: bool=False, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> RouteChoice | list[RouteChoice]:
        """Asynchronously call the router to get a route choice.

        :param text: The text to route.
        :type text: Optional[str]
        :param vector: The vector to route.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route (ie avoid dynamic route
            LLM calls during fit or evaluate).
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to use.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: The route choice.
        :rtype: RouteChoice
        """
        if not await self.index.ais_ready():
            await self._async_init_index_state()
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        potential_sparse_vector: List[SparseEmbedding] | None = None
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            vector, potential_sparse_vector = await self._async_encode(text=[text], input_type='queries')
        vector = xq_reshape(xq=vector)
        if sparse_vector is None:
            if text is None:
                raise ValueError('Either text or sparse_vector must be provided')
            sparse_vector = potential_sparse_vector[0] if potential_sparse_vector else None
        scores, routes = await self.index.aquery(vector=vector[0], top_k=self.top_k, route_filter=route_filter, sparse_vector=sparse_vector)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(routes, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        return await self._async_pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)

    async def _async_execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            await self.index._async_remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            await self.index.aadd(embeddings=await self.encoder.acall(docs=utterances_text), sparse_embeddings=await self.sparse_encoder.acall(docs=utterances_text), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']])
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        await self._async_write_hash()

    def _convex_scaling(self, dense: np.ndarray, sparse: list[SparseEmbedding]) -> tuple[np.ndarray, list[SparseEmbedding]]:
        """Convex scaling of the dense and sparse vectors.

        :param dense: The dense vector to scale.
        :type dense: np.ndarray
        :param sparse: The sparse vector to scale.
        :type sparse: list[SparseEmbedding]
        """
        sparse_dicts = [sparse_vec.to_dict() for sparse_vec in sparse]
        scaled_dense = np.array(dense) * self.alpha
        scaled_sparse = []
        for sparse_dict in sparse_dicts:
            scaled_sparse.append(SparseEmbedding.from_dict({k: v * (1 - self.alpha) for k, v in sparse_dict.items()}))
        return (scaled_dense, scaled_sparse)

    def fit(self, X: List[str], y: List[str], batch_size: int=500, max_iter: int=500, local_execution: bool=False):
        """Fit the HybridRouter.

        :param X: The input data.
        :type X: List[str]
        :param y: The output data.
        :type y: List[str]
        :param batch_size: The batch size to use for fitting.
        :type batch_size: int
        :param max_iter: The maximum number of iterations to use for fitting.
        :type max_iter: int
        :param local_execution: Whether to execute the fitting locally.
        :type local_execution: bool
        """
        original_index = self.index
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        if local_execution:
            from semantic_router.index.hybrid_local import HybridLocalIndex
            remote_utterances = self.index.get_utterances(include_metadata=True)
            routes = []
            utterances = []
            metadata = []
            for utterance in remote_utterances:
                routes.append(utterance.route)
                utterances.append(utterance.utterance)
                metadata.append(utterance.metadata)
            embeddings = self.encoder(utterances) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_documents(utterances)
            sparse_embeddings = self.sparse_encoder(utterances) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_documents(utterances)
            self.index = HybridLocalIndex()
            self.index.add(embeddings=embeddings, sparse_embeddings=sparse_embeddings, routes=routes, utterances=utterances, metadata_list=metadata)
        Xq_d: List[List[float]] = []
        Xq_s: List[SparseEmbedding] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb_d = np.array(self.encoder(X[i:i + batch_size]) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(X[i:i + batch_size]))
            emb_s = self.sparse_encoder(X[i:i + batch_size]) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_queries(X[i:i + batch_size])
            Xq_d.extend(emb_d)
            Xq_s.extend(emb_s)
        best_acc = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
        best_thresholds = self.get_thresholds()
        for _ in (pbar := tqdm(range(max_iter), desc='Training')):
            pbar.set_postfix({'acc': round(best_acc, 2)})
            thresholds = threshold_random_search(route_layer=self, search_range=0.8)
            self._update_thresholds(route_thresholds=thresholds)
            acc = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
            if acc > best_acc:
                best_acc = acc
                best_thresholds = thresholds
        self._update_thresholds(route_thresholds=best_thresholds)
        if local_execution:
            self.index = original_index

    def evaluate(self, X: List[str], y: List[str], batch_size: int=500) -> float:
        """Evaluate the accuracy of the route selection.

        :param X: The input data.
        :type X: List[str]
        :param y: The output data.
        :type y: List[str]
        :param batch_size: The batch size to use for evaluation.
        :type batch_size: int
        :return: The accuracy of the route selection.
        :rtype: float
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        Xq_d: List[List[float]] = []
        Xq_s: List[SparseEmbedding] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb_d = np.array(self.encoder(X[i:i + batch_size]) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(X[i:i + batch_size]))
            emb_s = self.sparse_encoder(X[i:i + batch_size]) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_queries(X[i:i + batch_size])
            Xq_d.extend(emb_d)
            Xq_s.extend(emb_s)
        accuracy = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
        return accuracy

    def _vec_evaluate(self, Xq_d: Union[List[float], Any], Xq_s: list[SparseEmbedding], y: List[str]) -> float:
        """Evaluate the accuracy of the route selection.

        :param Xq_d: The dense vectors to evaluate.
        :type Xq_d: Union[List[float], Any]
        :param Xq_s: The sparse vectors to evaluate.
        :type Xq_s: list[SparseEmbedding]
        :param y: The output data.
        :type y: List[str]
        :return: The accuracy of the route selection.
        :rtype: float
        """
        correct = 0
        for xq_d, xq_s, target_route in zip(Xq_d, Xq_s, y):
            route_choice = self(vector=xq_d, sparse_vector=xq_s, simulate_static=True)
            if isinstance(route_choice, list):
                route_name = route_choice[0].name
            else:
                route_name = route_choice.name
            if route_name == target_route:
                correct += 1
        accuracy = correct / len(Xq_d)
        return accuracy

def _convex_scaling(self, dense: np.ndarray, sparse: list[SparseEmbedding]) -> tuple[np.ndarray, list[SparseEmbedding]]:
    """Convex scaling of the dense and sparse vectors.

        :param dense: The dense vector to scale.
        :type dense: np.ndarray
        :param sparse: The sparse vector to scale.
        :type sparse: list[SparseEmbedding]
        """
    sparse_dicts = [sparse_vec.to_dict() for sparse_vec in sparse]
    scaled_dense = np.array(dense) * self.alpha
    scaled_sparse = []
    for sparse_dict in sparse_dicts:
        scaled_sparse.append(SparseEmbedding.from_dict({k: v * (1 - self.alpha) for k, v in sparse_dict.items()}))
    return (scaled_dense, scaled_sparse)

def _vec_evaluate(self, Xq_d: Union[List[float], Any], Xq_s: list[SparseEmbedding], y: List[str]) -> float:
    """Evaluate the accuracy of the route selection.

        :param Xq_d: The dense vectors to evaluate.
        :type Xq_d: Union[List[float], Any]
        :param Xq_s: The sparse vectors to evaluate.
        :type Xq_s: list[SparseEmbedding]
        :param y: The output data.
        :type y: List[str]
        :return: The accuracy of the route selection.
        :rtype: float
        """
    correct = 0
    for xq_d, xq_s, target_route in zip(Xq_d, Xq_s, y):
        route_choice = self(vector=xq_d, sparse_vector=xq_s, simulate_static=True)
        if isinstance(route_choice, list):
            route_name = route_choice[0].name
        else:
            route_name = route_choice.name
        if route_name == target_route:
            correct += 1
    accuracy = correct / len(Xq_d)
    return accuracy

def test_function_schema():
    schema = FunctionSchema(scrape_webpage)
    assert schema.name == scrape_webpage.__name__
    assert schema.description == str(inspect.getdoc(scrape_webpage))
    assert schema.signature == str(inspect.signature(scrape_webpage))
    assert schema.output == str(inspect.signature(scrape_webpage).return_annotation)
    assert len(schema.parameters) == 2

def test_ollama_function_schema():
    schema = FunctionSchema(scrape_webpage)
    ollama_schema = schema.to_ollama()
    assert ollama_schema['type'] == 'function'
    assert ollama_schema['function']['name'] == schema.name
    assert ollama_schema['function']['description'] == schema.description
    assert ollama_schema['function']['parameters']['type'] == 'object'
    assert ollama_schema['function']['parameters']['properties']['url']['type'] == 'string'
    assert ollama_schema['function']['parameters']['properties']['name']['type'] == 'string'
    assert ollama_schema['function']['parameters']['properties']['url']['description'] is None
    assert ollama_schema['function']['parameters']['properties']['name']['description'] is None
    assert ollama_schema['function']['parameters']['required'] == ['name']

def get_test_encoders():
    encoders = [OpenAIEncoder]
    if importlib.util.find_spec('cohere') is not None:
        encoders.append(CohereEncoder)
    return encoders

def get_test_indexes():
    indexes = [LocalIndex]
    if importlib.util.find_spec('qdrant_client') is not None:
        indexes.append(QdrantIndex)
    if importlib.util.find_spec('pinecone') is not None:
        indexes.append(PineconeIndex)
    if importlib.util.find_spec('psycopg') is not None:
        indexes.append(PostgresIndex)
    return indexes

def get_test_async_indexes():
    indexes = [LocalIndex]
    if importlib.util.find_spec('qdrant_client') is not None:
        indexes.append(QdrantIndex)
    if importlib.util.find_spec('pinecone') is not None:
        indexes.append(PineconeIndex)
    if importlib.util.find_spec('psycopg') is not None:
        indexes.append(PostgresIndex)
    return indexes

class TestRoute:

    def test_value_error_in_route_call(self):
        function_schemas = [{'name': 'test_function', 'type': 'function'}]
        route = Route(name='test_function', utterances=['utterance1', 'utterance2'], function_schemas=function_schemas)
        with pytest.raises(ValueError):
            route('test_query')

    def test_generate_dynamic_route(self):
        mock_llm = MockLLM(name='test')
        function_schemas = {'name': 'test_function', 'type': 'function'}
        route = Route._generate_dynamic_route(llm=mock_llm, function_schemas=function_schemas, route_name='test_route')
        assert route.name == 'test_function'
        assert route.utterances == ['example_utterance_1', 'example_utterance_2', 'example_utterance_3', 'example_utterance_4', 'example_utterance_5']

    def test_to_dict(self):
        route = Route(name='test', utterances=['utterance'])
        expected_dict = {'name': 'test', 'utterances': ['utterance'], 'description': None, 'function_schemas': None, 'llm': None, 'score_threshold': None, 'metadata': {}}
        assert route.to_dict() == expected_dict

    def test_from_dict(self):
        route_dict = {'name': 'test', 'utterances': ['utterance']}
        route = Route.from_dict(route_dict)
        assert route.name == 'test'
        assert route.utterances == ['utterance']

    def test_from_dynamic_route(self):
        mock_llm = MockLLM(name='test')

        def test_function(input: str):
            """Test function docstring"""
            pass
        dynamic_route = Route.from_dynamic_route(llm=mock_llm, entities=[test_function], route_name='test_route')
        assert dynamic_route.name == 'test_function'
        assert dynamic_route.utterances == ['example_utterance_1', 'example_utterance_2', 'example_utterance_3', 'example_utterance_4', 'example_utterance_5']

    def test_parse_route_config(self):
        config = '\n        <config>\n        {\n            "name": "test_function",\n            "utterances": [\n                "example_utterance_1",\n                "example_utterance_2",\n                "example_utterance_3",\n                "example_utterance_4",\n                "example_utterance_5"]\n        }\n        </config>\n        '
        expected_config = '\n        {\n            "name": "test_function",\n            "utterances": [\n                "example_utterance_1",\n                "example_utterance_2",\n                "example_utterance_3",\n                "example_utterance_4",\n                "example_utterance_5"]\n        }\n        '
        assert Route._parse_route_config(config).strip() == expected_config.strip()

def test_from_dict(self):
    route_dict = {'name': 'test', 'utterances': ['utterance']}
    route = Route.from_dict(route_dict)
    assert route.name == 'test'
    assert route.utterances == ['utterance']

def test_parse_route_config(self):
    config = '\n        <config>\n        {\n            "name": "test_function",\n            "utterances": [\n                "example_utterance_1",\n                "example_utterance_2",\n                "example_utterance_3",\n                "example_utterance_4",\n                "example_utterance_5"]\n        }\n        </config>\n        '
    expected_config = '\n        {\n            "name": "test_function",\n            "utterances": [\n                "example_utterance_1",\n                "example_utterance_2",\n                "example_utterance_3",\n                "example_utterance_4",\n                "example_utterance_5"]\n        }\n        '
    assert Route._parse_route_config(config).strip() == expected_config.strip()

def get_test_indexes():
    indexes = []
    if importlib.util.find_spec('qdrant_client') is not None:
        indexes.append(QdrantIndex)
    if importlib.util.find_spec('pinecone') is not None:
        indexes.append(PineconeIndex)
    return indexes

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

def get_test_indexes():
    indexes = [LocalIndex]
    if importlib.util.find_spec('qdrant_client') is not None:
        indexes.append(QdrantIndex)
    if importlib.util.find_spec('pinecone') is not None:
        indexes.append(PineconeIndex)
    if importlib.util.find_spec('psycopg') is not None:
        indexes.append(PostgresIndex)
    return indexes

def get_test_encoders():
    encoders = [OpenAIEncoder]
    if importlib.util.find_spec('cohere') is not None:
        encoders.append(CohereEncoder)
    return encoders

def has_valid_openai_api_key():
    """Check if a valid OpenAI API key is available."""
    api_key = os.environ.get('OPENAI_API_KEY')
    return api_key is not None and api_key.strip() != ''

