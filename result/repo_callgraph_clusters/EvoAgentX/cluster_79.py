# Cluster 79

class Message(BaseModule):
    """
    the base class for message. 

    Attributes: 
        content (Any): the content of the message, need to implement str() function. 
        agent (str): the sender of the message, normally set as the agent name.
        action (str): the trigger of the message, normally set as the action name.
        prompt (str): the prompt used to obtain the generated text. 
        next_actions (List[str]): the following actions. 
        msg_type (str): the type of the message, such as "request", "response", "command" etc. 
        wf_goal (str): the goal of the whole workflow. 
        wf_task (str): the name of a task in the workflow, i.e., the ``name`` of a WorkFlowNode instance. 
        wf_task_desc (str): the description of a task in the workflow, i.e., the ``description`` of a WorkFlowNode instance.
        message_id (str): the unique identifier of the message. 
        timestamp (str): the timestame of the message. 
    """
    content: Any
    agent: Optional[str] = None
    action: Optional[str] = None
    prompt: Optional[Union[str, List[dict]]] = None
    next_actions: Optional[List[str]] = None
    msg_type: Optional[MessageType] = MessageType.UNKNOWN
    wf_goal: Optional[str] = None
    wf_task: Optional[str] = None
    wf_task_desc: Optional[str] = None
    message_id: Optional[str] = Field(default_factory=generate_id)
    timestamp: Optional[str] = Field(default_factory=get_timestamp)
    conversation_id: Optional[str] = Field(default_factory=generate_id)

    def __str__(self) -> str:
        return self.to_str()

    def __eq__(self, other: 'Message'):
        return self.message_id == other.message_id

    def __hash__(self):
        return self.message_id

    def to_str(self) -> str:
        msg_part = []
        if self.timestamp:
            msg_part.append(f'[{self.timestamp}]')
        if self.agent:
            msg_part.append(f'Agent: {self.agent}')
        if self.msg_type and self.msg_type != MessageType.UNKNOWN:
            msg_part.append(f'Type: {self.msg_type}')
        if self.action:
            msg_part.append(f'Action: {self.action}')
        if self.wf_goal:
            msg_part.append(f'Goal: {self.wf_goal}')
        if self.wf_task:
            msg_part.append(f'Task: {self.wf_task} ({self.wf_task_desc or 'No description'})')
        if self.content:
            msg_part.append(f'Content: {str(self.content)}')
        msg = '\n'.join(msg_part)
        return msg

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        """
        Convert the Message to a dictionary for saving. 
        """
        data = super().to_dict(exclude_none=exclude_none, ignore=ignore, **kwargs)
        if self.msg_type:
            data['msg_type'] = self.msg_type.value
        return data

    @model_validator(mode='before')
    @classmethod
    def validate_data(cls, data: Any) -> Any:
        if 'msg_type' in data and data['msg_type'] and isinstance(data['msg_type'], str):
            data['msg_type'] = MessageType(data['msg_type'])
        return data

    @classmethod
    def sort_by_timestamp(cls, messages: List['Message'], reverse: bool=False) -> List['Message']:
        """
        sort the messages based on the timestamp. 

        Args: 
            messages (List[Message]): the messages to be sorted. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
        messages.sort(key=lambda msg: datetime.strptime(msg.timestamp, '%Y-%m-%d %H:%M:%S'), reverse=reverse)
        return messages

    @classmethod
    def sort(cls, messages: List['Message'], key: Optional[Callable[['Message'], Any]]=None, reverse: bool=False) -> List['Message']:
        """
        sort the messages using key or timestamp (by default). 

        Args:
            messages (List[Message]): the messages to be sorted. 
            key (Optional[Callable[['Message'], Any]]): the function used to sort messages. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
        if key is None:
            return cls.sort_by_timestamp(messages, reverse=reverse)
        messages.sort(key=key, reverse=reverse)
        return messages

    @classmethod
    def merge(cls, messages: List[List['Message']], sort: bool=False, key: Optional[Callable[['Message'], Any]]=None, reverse: bool=False) -> List['Message']:
        """
        merge different message list. 

        Args:
            messages (List[List[Message]]): the message lists to be merged. 
            sort (bool): whether to sort the merged messages.
            key (Optional[Callable[['Message'], Any]]): the function used to sort messages. 
            reverse (bool): If True, sort the messages in descending order. Otherwise, sort the messages in ascending order.
        """
        merged_messages = sum(messages, [])
        if sort:
            merged_messages = cls.sort(merged_messages, key=key, reverse=reverse)
        return merged_messages

def __str__(self) -> str:
    return self.to_str()

class BaseModule(BaseModel, metaclass=MetaModule):
    """
    Base module class that serves as the foundation for all modules in the EvoAgentX framework.
    
    This class provides serialization/deserialization capabilities, supports creating instances from
    dictionaries, JSON, or files, and exporting instances to these formats.
    
    Attributes:
        class_name: The class name, defaults to None but is automatically set during subclass initialization
        model_config: Pydantic model configuration that controls type matching and behavior
    """
    class_name: str = None
    model_config = {'arbitrary_types_allowed': True, 'extra': 'allow', 'protected_namespaces': (), 'validate_assignment': False}

    def __init_subclass__(cls, **kwargs):
        """
        Subclass initialization method that automatically sets the class_name attribute.
        
        Args:
            cls (Type): The subclass being initialized
            **kwargs (Any): Additional keyword arguments
        """
        super().__init_subclass__(**kwargs)
        cls.class_name = cls.__name__

    def __init__(self, **kwargs):
        """
        Initializes a BaseModule instance.
        
        Args:
            **kwargs (Any): Keyword arguments used to initialize the instance
        
        Raises:
            ValidationError: When parameter validation fails
            Exception: When other errors occur during initialization
        """
        try:
            for field_name, _ in type(self).model_fields.items():
                field_value = kwargs.get(field_name, None)
                if field_value:
                    kwargs[field_name] = self._process_data(field_value)
            super().__init__(**kwargs)
            self.init_module()
        except (ValidationError, Exception) as e:
            exception_handler = callback_manager.get_callback('exception_buffer')
            if exception_handler is None:
                error_message = get_base_module_init_error_message(cls=self.__class__, data=kwargs, errors=e)
                logger.error(error_message)
                raise
            else:
                exception_handler.add(e)

    def init_module(self):
        """
        Module initialization method that subclasses can override to provide additional initialization logic.
        """
        pass

    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        
        Returns:
            str: String representation of the object
        """
        return self.to_str()

    @property
    def kwargs(self) -> dict:
        """
        Returns the extra fields of the model.
        
        Returns:
            dict: Dictionary containing all extra keyword arguments
        """
        return self.model_extra

    @classmethod
    def _create_instance(cls, data: Dict[str, Any]) -> 'BaseModule':
        """
        Internal method for creating an instance from a dictionary.
        
        Args:
            data: Dictionary containing instance data
        
        Returns:
            BaseModule: The created instance
        """
        processed_data = {k: cls._process_data(v) for k, v in data.items()}
        return cls.model_validate(processed_data)

    @classmethod
    def _process_data(cls, data: Any) -> Any:
        """
        Recursive method for processing data, with special handling for dictionaries containing class_name.
        
        Args:
            data: Data to be processed
        
        Returns:
            Processed data
        """
        if isinstance(data, dict):
            if 'class_name' in data:
                sub_class = MODULE_REGISTRY.get_module(data.get('class_name'))
                return sub_class._create_instance(data)
            else:
                return {k: cls._process_data(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [cls._process_data(x) for x in data]
        else:
            return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> 'BaseModule':
        """
        Instantiate the BaseModule from a dictionary.
        
        Args:
            data: Dictionary containing instance data
            **kwargs (Any): Additional keyword arguments, can include log to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            Exception: When errors occur during initialization
        """
        use_logger = kwargs.get('log', True)
        with exception_buffer() as buffer:
            try:
                class_name = data.get('class_name', None)
                if class_name:
                    cls = MODULE_REGISTRY.get_module(class_name)
                module = cls._create_instance(data)
                if len(buffer.exceptions) > 0:
                    error_message = get_base_module_init_error_message(cls, data, buffer.exceptions)
                    if use_logger:
                        logger.error(error_message)
                    raise Exception(get_error_message(buffer.exceptions))
            finally:
                pass
        return module

    @classmethod
    def from_json(cls, content: str, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a JSON string.
        
        This method uses yaml.safe_load to parse the JSON string into a Python object,
        which supports more flexible parsing than standard json.loads (including handling
        single quotes, trailing commas, etc). The parsed data is then passed to from_dict
        to create the instance.
        
        Args:
            content: JSON string
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input is not a valid JSON string
        """
        use_logger = kwargs.get('log', True)
        try:
            data = yaml.safe_load(content)
        except Exception:
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        if not isinstance(data, (list, dict)):
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        return cls.from_dict(data, log=use_logger)

    @classmethod
    def from_str(cls, content: str, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a string that may contain JSON.
        
        This method is more forgiving than `from_json` as it can extract valid JSON
        objects embedded within larger text. It uses `parse_json_from_text` to extract 
        all potential JSON strings from the input text, then tries to create an instance 
        from each extracted JSON string until successful.
        
        Args:
            content: Text that may contain JSON strings
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input does not contain valid JSON strings or the JSON is incompatible with the class
        """
        use_logger = kwargs.get('log', True)
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) == 0:
            error_message = f'The input to {cls.__name__}.from_str does not contain any valid JSON str.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        module = None
        for json_str in extracted_json_list:
            try:
                module = cls.from_json(json_str, log=False)
            except Exception:
                continue
            break
        if module is None:
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_str either does not contain a valide JSON str, or the JSON str is incomplete or incompatable (incorrect variables or types) with {cls.__name__}.'
            error_message += f'\nInput:\n{content}'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        return module

    @classmethod
    def load_module(cls, path: str, **kwargs) -> dict:
        """
        Load the values for a module from a file.
        
        By default, it opens the specified file and uses `yaml.safe_load` to parse its contents 
        into a Python object (typically a dictionary).
        
        Args:
            path: The path of the file
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            dict: The JSON object instantiated from the file
        """
        with open(path, mode='r', encoding='utf-8') as file:
            content = yaml.safe_load(file.read())
        return content

    @classmethod
    def from_file(cls, path: str, load_function: Callable=None, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a file.
        
        This method reads and parses a file into a data structure, then creates
        a module instance from that data. It first verifies that the file exists,
        then uses either the provided `load_function` or the default `load_module`
        method to read and parse the file content, and finally calls `from_dict`
        to create the instance.
        
        Args:
            path: The path of the file
            load_function: The function used to load the data, takes a file path as input and returns a JSON object
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the file does not exist
        """
        use_logger = kwargs.get('log', True)
        if not os.path.exists(path):
            error_message = f'File "{path}" does not exist!'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        function = load_function or cls.load_module
        content = function(path, **kwargs)
        module = cls.from_dict(content, log=use_logger)
        return module

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        """
        Convert the BaseModule to a dictionary.
        
        Args:
            exclude_none: Whether to exclude fields with None values
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            dict: Dictionary containing the object data
        """
        data = {}
        for field_name, _ in type(self).model_fields.items():
            if field_name in ignore:
                continue
            field_value = getattr(self, field_name, None)
            if exclude_none and field_value is None:
                continue
            if isinstance(field_value, BaseModule):
                data[field_name] = field_value.to_dict(exclude_none=exclude_none, ignore=ignore)
            elif isinstance(field_value, list):
                data[field_name] = [item.to_dict(exclude_none=exclude_none, ignore=ignore) if isinstance(item, BaseModule) else item for item in field_value]
            elif isinstance(field_value, dict):
                data[field_name] = {key: value.to_dict(exclude_none=exclude_none, ignore=ignore) if isinstance(value, BaseModule) else value for key, value in field_value.items()}
            else:
                data[field_name] = field_value
        return data

    def to_json(self, use_indent: bool=False, ignore: List[str]=[], **kwargs) -> str:
        """
        Convert the BaseModule to a JSON string.
        
        Args:
            use_indent: Whether to use indentation
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The JSON string
        """
        if use_indent:
            kwargs['indent'] = kwargs.get('indent', 4)
        else:
            kwargs.pop('indent', None)
        if kwargs.get('default', None) is None:
            kwargs['default'] = custom_serializer
        data = self.to_dict(exclude_none=True)
        for ignore_field in ignore:
            data.pop(ignore_field, None)
        return json.dumps(data, **kwargs)

    def to_str(self, **kwargs) -> str:
        """
        Convert the BaseModule to a string. Use .to_json to output JSON string by default.
        
        Args:
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The string
        """
        return self.to_json(use_indent=False)

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """
        Save the BaseModule to a file.
        
        This method will set non-serializable objects to None by default.
        If you want to save non-serializable objects, override this method.
        Remember to also override the `load_module` function to ensure the loaded
        object can be correctly parsed by `cls.from_dict`.
        
        Args:
            path: The path to save the file
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The path where the file is saved, same as the input path
        """
        logger.info('Saving {} to {}', self.__class__.__name__, path)
        return save_json(self.to_json(use_indent=True, default=lambda x: None, ignore=ignore), path=path)

    def deepcopy(self):
        """Deep copy the module.

        This is a tweak to the default python deepcopy that only deep copies `self.parameters()`, and for other
        attributes, we just do the shallow copy.
        """
        try:
            return copy.deepcopy(self)
        except Exception:
            pass
        new_instance = self.__class__.__new__(self.__class__)
        for attr, value in self.__dict__.items():
            if isinstance(value, BaseModule):
                setattr(new_instance, attr, value.deepcopy())
            else:
                try:
                    setattr(new_instance, attr, copy.deepcopy(value))
                except Exception:
                    logging.warning(f"Failed to deep copy attribute '{attr}' of {self.__class__.__name__}, falling back to shallow copy or reference copy.")
                    try:
                        setattr(new_instance, attr, copy.copy(value))
                    except Exception:
                        setattr(new_instance, attr, value)
        return new_instance

def __str__(self) -> str:
    """
        Returns a string representation of the object.
        
        Returns:
            str: String representation of the object
        """
    return self.to_str()

class LLMOutputParser(Parser):
    """A basic parser for LLM-generated content.
    
    This parser stores the raw text generated by an LLM in the `.content` attribute
    and provides methods to extract structured data from this text using different
    parsing strategies.
    
    Attributes:
        content: The raw text generated by the LLM.
    """
    content: str = Field(default=None, exclude=True, description='the text generated by LLM')

    @classmethod
    def get_attrs(cls, return_type: bool=False) -> List[Union[str, tuple]]:
        """Returns the attributes of the LLMOutputParser class.
        
        Excludes ["class_name", "content"] by default.

        Args:
            return_type: Whether to return the type of the attributes along with their names.
        
        Returns:
            If `return_type` is True, returns a list of tuples where each tuple contains 
            the attribute name and its type. Otherwise, returns a list of attribute names.
        """
        attrs = []
        exclude_attrs = ['class_name', 'content']
        for field, field_info in cls.model_fields.items():
            if field not in exclude_attrs:
                if return_type:
                    field_type = get_type_name(field_info.annotation)
                    attrs.append((field, field_type))
                else:
                    attrs.append(field)
        return attrs

    @classmethod
    def get_attr_descriptions(cls) -> dict:
        """Returns the attributes and their descriptions.
        
        Returns:
            A dictionary mapping attribute names to their descriptions.
        """
        attrs = cls.get_attrs()
        results = {}
        for field_name, field_info in cls.model_fields.items():
            if field_name not in attrs:
                continue
            field_desc = field_info.description if field_info.description is not None else 'None'
            results[field_name] = field_desc
        return results

    @classmethod
    def get_content_data(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> dict:
        """Parses LLM-generated content into a dictionary.
        
        This method takes content from an LLM response and converts it to a structured
        dictionary based on the specified parsing mode.

        Args:
            content: The content to parse.
            parse_mode: The mode to parse the content. Must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. It will return a dictionary parsed from the first valid JSON string.
                - 'xml': Parses content using XML tags. It will return a dictionary parsed from the XML tags.
                - 'title': Parses content with Markdown-style headings.
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function.
            parse_func: The function to parse the content, only valid when parse_mode is 'custom'.
            **kwargs (Any): Additional arguments passed to the parsing function.
        
        Returns:
            The parsed content as a dictionary.
            
        Raises:
            ValueError: If parse_mode is invalid or if parse_func is not provided when parse_mode is 'custom'.
        """
        attrs = cls.get_attrs()
        if len(attrs) <= 0:
            return {}
        if parse_mode == 'str':
            parse_func = cls._parse_str_content
        elif parse_mode == 'json':
            parse_func = cls._parse_json_content
        elif parse_mode == 'xml':
            parse_func = cls._parse_xml_content
        elif parse_mode == 'title':
            parse_func = cls._parse_title_content
        elif parse_mode == 'custom':
            if parse_func is None:
                raise ValueError("`parse_func` must be provided when `parse_mode` is 'custom'.")
            signature = inspect.signature(parse_func)
            if 'content' not in signature.parameters:
                raise ValueError('`parse_func` must have an input argument `content`.')
            func_args = {}
            func_args['content'] = content
            for param_name, param in signature.parameters.items():
                if param_name == 'content':
                    continue
                if param_name in kwargs:
                    func_args[param_name] = kwargs[param_name]
            data = parse_func(**func_args)
            if not isinstance(data, dict):
                raise ValueError(f'The output of `parse_func` must be a dictionary, but found {type(data)}.')
            return data
        else:
            raise ValueError(f"Invalid value '{parse_mode}' detected for `parse_mode`. Available choices: {PARSER_VALID_MODE}")
        data = parse_func(content=content, **kwargs)
        return data

    @classmethod
    def _parse_str_content(cls, content: str, **kwargs) -> dict:
        """Parses content by setting all attributes to the raw content.
        
        Args:
            content: The content to parse.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping all attributes to the raw content.
        """
        attrs = cls.get_attrs()
        return {attr: content for attr in attrs}

    @classmethod
    def _parse_json_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting and parsing a JSON object. 
        If the content contains multiple JSON objects, only the first one will be used. 
        
        Args:
            content: The content containing a JSON object.
            **kwargs: Additional arguments (not used).
        
        Returns:
            The parsed JSON as a dictionary.
            
        Raises:
            ValueError: If the content doesn't contain a valid JSON object.
        """
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) > 0:
            json_str = extracted_json_list[0]
            try:
                data = yaml.safe_load(json_str)
                if not isinstance(data, dict):
                    if isinstance(data, list):
                        attrs = cls.get_attrs()
                        if len(attrs) == 1:
                            return {attrs[0]: data}
                        else:
                            raise ValueError('The generated content is a list of JSON strings, but the attribute name for the list is not specified. You should instruct the LLM to specify the attribute name for the list.')
                    else:
                        raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
            except Exception:
                raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
        else:
            raise ValueError(f'The following generated content does not contain JSON string!\n{content}')
        return data

    @classmethod
    def _parse_xml_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting values from XML tags.
        
        Each attribute of the parser is expected to be enclosed in XML tags
        with the attribute name as the tag name.
        
        Args:
            content: The content containing XML tags.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping attributes to their extracted values.
            
        Raises:
            ValueError: If the content is missing expected XML tags or if the
                        extracted values can't be converted to the expected types.
        """
        attrs_with_types: List[tuple] = cls.get_attrs(return_type=True)
        data = {}
        for attr, attr_type in attrs_with_types:
            attr_raw_value_list = parse_xml_from_text(text=content, label=attr)
            if len(attr_raw_value_list) > 0:
                attr_raw_value = attr_raw_value_list[0]
                try:
                    attr_value = parse_data_from_text(text=attr_raw_value, datatype=attr_type)
                except Exception:
                    raise ValueError(f'Cannot parse text: {attr_raw_value} into {attr_type} data!')
            else:
                raise ValueError(f'The following generated content does not contain xml label <{attr}>xxx</{attr}>!\n{content}')
            data[attr] = attr_value
        return data

    @classmethod
    def _parse_title_content(cls, content: str, title_format: str='## {title}', **kwargs) -> dict:
        """Parses content with markdown-style titles.
        
        Extracts sections from content that are divided by titles following
        the specified format described in `title_format`. The default format is "## {title}".
        For example:
        ```
        ## title1
        content1
        ## title2
        content2
        ```
        This content will be parsed into:
        ```
        {
            "title1": "content1",
            "title2": "content2"
        }
        ```
        Args:
            content: The content with title-divided sections.
            title_format: The format of the titles, default is "## {title}".
            **kwargs: Additional arguments (not used).

        Returns:
            A dictionary mapping title names to their section contents.
        """
        attrs: List[str] = cls.get_attrs()
        if not attrs:
            return {}
        output_titles = [title_format.format(title=attr) for attr in attrs]

        def is_output_title(text: str):
            for title in output_titles:
                if text.strip().lower().startswith(title.lower()):
                    return (True, title)
            return (False, None)
        data = {}
        current_output_name: str = None
        current_output_content: list = None
        for line in content.split('\n'):
            is_title, title = is_output_title(line)
            if is_title:
                if current_output_name is not None and current_output_content is not None:
                    data[current_output_name] = '\n'.join(current_output_content)
                current_output_content = []
                current_output_name = title.replace('#', '').strip()
                output_titles.remove(title)
            elif current_output_content is not None:
                current_output_content.append(line)
        if current_output_name is not None and current_output_content is not None:
            data[current_output_name] = '\n'.join(current_output_content)
        return data

    @classmethod
    def parse(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> 'LLMOutputParser':
        """Parses LLM-generated text into a structured parser instance.
        
        This is the main method for creating parser instances from LLM output.
        
        Args:
            content: The text generated by the LLM.
            parse_mode: The mode to parse the content, must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. Uses the first valid JSON string to create an instance of LLMOutputParser.
                - 'xml': Parses content using XML tags. Uses the XML tags to create an instance of LLMOutputParser.
                - 'title': Parses content with Markdown-style headings. Uses the Markdown-style headings to create an instance of LLMOutputParser. The default title format is "## {title}", you can change it by providing `title_format` parameter, which should be a string that contains `{title}` placeholder. 
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function. The `parse_func` must have a parameter named `content` and return a dictionary where the keys are the attribute names and the values are the parsed data. 
            parse_func: The function to parse the content, only valid when `parse_mode` is 'custom'.
            **kwargs (Any): Additional arguments passed to parsing functions, such as:
                - `title_format` for `parse_mode="title"`.
            
        Returns:
            An instance of LLMOutputParser containing the parsed data.
            
        Raises:
            ValueError: If parse_mode is invalid or if content is not a string.
        """
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
        if not isinstance(content, str):
            raise ValueError(f'The input to {cls.__name__}.parse should be a str, but found {type(content)}.')
        data = cls.get_content_data(content=content, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
        data.update({'content': content})
        parser = cls.from_dict(data, **kwargs)
        return parser

    def __str__(self) -> str:
        """
        Returns a string representation of the parser.
        """
        return self.to_str()

    def to_str(self, **kwargs) -> str:
        """
        Converts the parser to a string.
        """
        return self.content

    def get_structured_data(self) -> dict:
        """Extracts structured data from the parser.
        
        Returns:
            A dictionary containing only the defined attributes and their values,
            excluding metadata like class_name.
        """
        attrs = type(self).get_attrs()
        data = self.to_dict(ignore=['class_name'])
        structured_data = {key: value for key, value in data.items() if key in attrs}
        return structured_data

def __str__(self) -> str:
    """
        Returns a string representation of the parser.
        """
    return self.to_str()

class ToyContent:

    def __init__(self, content: str):
        self.content = content

    def __str__(self) -> str:
        return self.to_str()

    def to_str(self) -> str:
        return self.content

def __str__(self) -> str:
    return self.to_str()

