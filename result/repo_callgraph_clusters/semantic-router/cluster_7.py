# Cluster 7

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

def test_generate_dynamic_route(self):
    mock_llm = MockLLM(name='test')
    function_schemas = {'name': 'test_function', 'type': 'function'}
    route = Route._generate_dynamic_route(llm=mock_llm, function_schemas=function_schemas, route_name='test_route')
    assert route.name == 'test_function'
    assert route.utterances == ['example_utterance_1', 'example_utterance_2', 'example_utterance_3', 'example_utterance_4', 'example_utterance_5']

def test_from_dynamic_route(self):
    mock_llm = MockLLM(name='test')

    def test_function(input: str):
        """Test function docstring"""
        pass
    dynamic_route = Route.from_dynamic_route(llm=mock_llm, entities=[test_function], route_name='test_route')
    assert dynamic_route.name == 'test_function'
    assert dynamic_route.utterances == ['example_utterance_1', 'example_utterance_2', 'example_utterance_3', 'example_utterance_4', 'example_utterance_5']

