# Cluster 29

class PromptTemplate(BaseModule):
    instruction: str = Field(description='The instruction that the LLM will follow.')
    context: Optional[str] = Field(default=None, description='Additional context that can help the LLM understand the instruction.')
    constraints: Optional[Union[List[str], str]] = Field(default=None, description='Constraints that the LLM must follow.')
    tools: Optional[List[Toolkit]] = Field(default=None, description='Tools that the LLM can use.')
    demonstrations: Optional[List[dict]] = Field(default=None, description='Examples of how to use the instruction.')
    history: Optional[List[Any]] = Field(default=None, description='History of the conversation between the user and the LLM.')

    def get_field_names(self) -> List[str]:
        return [name for name, _ in type(self).model_fields.items() if name != 'class_name']

    def get(self, key: str) -> Any:
        fields = self.get_field_names()
        if key not in fields:
            raise ValueError(f'Invalid key `{key}` for `{self.__class__.__name__}`. Valid keys are: {fields}')
        return getattr(self, key)

    def set(self, key: str, value: Any):
        fields = self.get_field_names()
        if key not in fields:
            raise ValueError(f'Invalid key `{key}` for `{self.__class__.__name__}`. Valid keys are: {fields}')
        setattr(self, key, value)

    def get_instruction(self) -> str:
        return self.instruction

    def get_demonstrations(self) -> List[Any]:
        return self.demonstrations

    def get_context(self) -> Optional[str]:
        return self.context

    def get_history(self) -> Optional[List[Any]]:
        return self.history

    def get_constraints(self) -> Optional[Union[List[str], str]]:
        return self.constraints

    def get_tools(self) -> Optional[List[str]]:
        return self.tools

    def set_instruction(self, instruction: str):
        self.set('instruction', instruction)

    def set_demonstrations(self, demonstrations: List[Any]):
        self.set('demonstrations', demonstrations)

    def set_context(self, context: str):
        self.set('context', context)

    def set_history(self, history: List[Any]):
        self.set('history', history)

    def set_constraints(self, constraints: Union[List[str], str]):
        self.set('constraints', constraints)

    def set_tools(self, tools: List[Toolkit]):
        self.set('tools', tools)

    def get_required_inputs_or_outputs(self, format: Type[LLMOutputParser]) -> List[str]:
        """
        Get the required fields of the format.
        """
        required_fields = []
        attrs = format.get_attrs()
        for field_name, field_info in format.model_fields.items():
            if field_name not in attrs:
                continue
            field_default = field_info.default
            if field_default is PydanticUndefined:
                required_fields.append(field_name)
        return required_fields

    def clear_placeholders(self, text: str) -> str:
        """
        Find all {xx} placeholders in the text, and replace them with `xx`,
        adding backticks only if not already present.
        """
        matches = set(regex.findall('(?<!\\{)\\{([^\\{\\},\\s]+)\\}(?!\\})', text))
        for field in matches:
            pattern = '(?<!\\{)\\{' + regex.escape(field) + '\\}(?!\\})'

            def replacer(match):
                start, end = (match.start(), match.end())
                before = text[start - 1] if start > 0 else ''
                after = text[end] if end < len(text) else ''
                replacement = field
                if before != '`':
                    replacement = '`' + replacement
                if after != '`':
                    replacement = replacement + '`'
                return replacement
            text = regex.sub(pattern, replacer, text)
        return text

    def check_required_inputs(self, inputs_format: Type[LLMOutputParser], values: dict):
        if inputs_format is None:
            return
        required_inputs = self.get_required_inputs_or_outputs(inputs_format)
        missing_required_inputs = [field for field in required_inputs if field not in values]
        if missing_required_inputs:
            logger.warning(f'Missing required inputs (without default values) for `{inputs_format.__name__}`: {missing_required_inputs}, will set them to empty strings.')

    def render_input_example(self, inputs_format: Type[LLMOutputParser], values: dict, missing_field_value: str='') -> str:
        if inputs_format is None and values is None:
            return ''
        if inputs_format is not None:
            fields = inputs_format.get_attrs()
            field_values = {field: values.get(field, missing_field_value) for field in fields}
        else:
            field_values = values
        return '\n'.join((f'[[ **{field}** ]]:\n{value}' for field, value in field_values.items()))

    def get_output_template(self, outputs_format: Type[LLMOutputParser], parse_mode: str='title', title_format: str='## {title}') -> str:
        if outputs_format is None:
            raise ValueError('`outputs_format` is required in `get_output_format`.')
        valid_modes = ['json', 'xml', 'title']
        if parse_mode not in valid_modes:
            raise ValueError(f'Invalid parse mode `{parse_mode}` for `{self.__class__.__name__}.get_output_template`. Valid modes are: {valid_modes}.')
        fields = outputs_format.get_attrs()
        required_fields = self.get_required_inputs_or_outputs(outputs_format)
        if parse_mode == 'json':
            json_template = '{{\n'
            for field in fields:
                json_template += f'    "{field}"'
                json_template += f': "{{{field}}}",\n' if field in required_fields else f' (Optional): "{{{field}}}",\n'
            json_template = json_template.rstrip(',\n') + '\n}}'
            output_template, output_keys = (json_template, fields)
        elif parse_mode == 'xml':
            xml_template = ''
            for field in fields:
                xml_template += f'<{field}>\n' if field in required_fields else f'<{field}> (Optional)\n'
                xml_template += f'{{{field}}}\n</{field}>\n'
            xml_template = xml_template.rstrip('\n')
            output_template, output_keys = (xml_template, fields)
        elif parse_mode == 'title':
            title_template = ''
            for field in fields:
                title_section = title_format.format(title=field)
                title_section += '\n' if field in required_fields else ' (Optional)\n'
                title_section += f'{{{field}}}\n\n'
                title_template += title_section
            title_template = title_template.rstrip('\n')
            output_template, output_keys = (title_template, fields)
        return (output_template, output_keys)

    def render_instruction(self) -> str:
        instruction_str = self.clear_placeholders(self.instruction)
        return f'### Instruction\nThis is the main task instruction you must follow:\n{instruction_str}\n'

    def render_context(self) -> str:
        if not self.context:
            return ''
        return f'### Context\nHere is some additional background information to help you understand the task:\n{self.context}\n'

    def render_tools(self) -> str:
        if not self.tools:
            return ''
        tools_schemas = [tool.get_tool_schemas() for tool in self.tools]
        tools_schemas = [j for i in tools_schemas for j in i]
        return TOOL_CALLING_TEMPLATE.format(tools_description=tools_schemas)

    def render_constraints(self) -> str:
        if not self.constraints:
            return ''
        if isinstance(self.constraints, list):
            constraints_str = '\n'.join((f'- {c}' for c in self.constraints))
        else:
            constraints_str = self.constraints
        return f'### Constraints\nYou must follow these rules or constraints when generating your output:\n{constraints_str}\n'

    def _render_system_message(self, system_prompt: Optional[str]=None) -> str:
        """
        Render the system message by combining system prompt, instruction, context, tools and constraints.
        """
        prompt_pieces = []
        if system_prompt:
            prompt_pieces.append(system_prompt + '\n')
        prompt_pieces.append(self.render_instruction())
        if self.context:
            prompt_pieces.append(self.render_context())
        if self.tools:
            prompt_pieces.append(self.render_tools())
        if self.constraints:
            prompt_pieces.append(self.render_constraints())
        return '\n'.join(prompt_pieces)

    def render_outputs(self, outputs_format: Type[LLMOutputParser], parse_mode: str='title', title_format: str='## {title}') -> str:
        if outputs_format is None or parse_mode in [None, 'str', 'custom'] or len(outputs_format.get_attrs()) == 0:
            return '### Outputs Format\nPlease generate a response that best fits the task instruction.\n'
        ouptut_template, output_keys = self.get_output_template(outputs_format, parse_mode=parse_mode, title_format=title_format)
        output_str = '### Outputs Format\nYou MUST strictly follow the following format when generating your output:\n\n'
        if parse_mode == 'json':
            output_str += 'Format your output in json format, such as:\n'
        elif parse_mode == 'xml':
            output_str += 'Format your output in xml format, such as:\n'
        elif parse_mode == 'title':
            output_str += 'Format your output in sectioned title format, such as:\n'
        example_values = {}
        for key in output_keys:
            field_info = outputs_format.model_fields.get(key)
            if field_info and field_info.description:
                example_values[key] = '[' + field_info.description + ']'
            else:
                example_values[key] = '[Your output here]'
        output_str += ouptut_template.format(**example_values)
        if '(Optional)' in ouptut_template:
            output_str += '\n\nNote: For optional fields, you can omit them in your output if they are not necessary.'
        output_str += '\n'
        return output_str

    def format(self, inputs_format: Optional[Type[LLMOutputParser]]=None, outputs_format: Optional[Type[LLMOutputParser]]=None, values: Optional[dict]=None, parse_mode: Optional[str]='title', title_format: Optional[str]='## {title}', output_format: Optional[str]=None, **kwargs) -> str:
        raise NotImplementedError(f'`format` method is not implemented for `{self.__class__.__name__}`.')

    def get_config(self) -> dict:
        return self.to_dict()

    def copy(self, **kwargs) -> 'PromptTemplate':
        """
        Create a deep-copied new PromptTemplate, optionally overriding fields with provided kwargs.
        """
        config = self.get_config()
        new_config = deepcopy(config)
        new_config = {k: kwargs.get(k, v) for k, v in new_config.items()}
        return self.__class__.from_dict(new_config)

def render_instruction(self) -> str:
    instruction_str = self.clear_placeholders(self.instruction)
    return f'### Instruction\nThis is the main task instruction you must follow:\n{instruction_str}\n'

