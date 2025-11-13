# Cluster 15

class SystemPromptDialog(QDialog):

    def __init__(self, parent=None, prompt_manager=None):
        super().__init__(parent)
        self.prompt_manager = prompt_manager
        self.setWindowTitle('Edit System Prompt')
        self.setFixedSize(800, 600)
        layout = QVBoxLayout()
        desc_label = QLabel("Edit the system prompt that defines the agent's behavior. Be careful with changes as they may affect functionality.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet('color: #666; margin: 10px 0;')
        layout.addWidget(desc_label)
        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlainText(self.prompt_manager.get_current_prompt())
        self.prompt_editor.setStyleSheet('\n            QTextEdit {\n                background-color: #262626;\n                border: 1px solid #333333;\n                border-radius: 8px;\n                color: #ffffff;\n                padding: 12px;\n                font-family: Inter;\n                font-size: 14px;\n            }\n        ')
        layout.addWidget(self.prompt_editor)
        button_layout = QHBoxLayout()
        reset_btn = QPushButton('Reset to Default')
        reset_btn.clicked.connect(self.reset_prompt)
        reset_btn.setStyleSheet('\n            QPushButton {\n                background-color: #666666;\n                color: white;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 5px;\n            }\n            QPushButton:hover {\n                background-color: #777777;\n            }\n        ')
        save_btn = QPushButton('Save Changes')
        save_btn.clicked.connect(self.save_changes)
        save_btn.setStyleSheet('\n            QPushButton {\n                background-color: #4CAF50;\n                color: white;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 5px;\n            }\n            QPushButton:hover {\n                background-color: #45a049;\n            }\n        ')
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def reset_prompt(self):
        if self.prompt_manager.reset_to_default():
            self.prompt_editor.setPlainText(self.prompt_manager.get_current_prompt())

    def save_changes(self):
        new_prompt = self.prompt_editor.toPlainText()
        if self.prompt_manager.save_prompt(new_prompt):
            self.accept()
        else:
            pass

def reset_prompt(self):
    if self.prompt_manager.reset_to_default():
        self.prompt_editor.setPlainText(self.prompt_manager.get_current_prompt())

class Store:

    def __init__(self):
        self.instructions = ''
        self.fully_auto = True
        self.running = False
        self.error = None
        self.run_history = []
        self.last_tool_use_id = None
        try:
            self.anthropic_client = AnthropicClient()
        except ValueError as e:
            self.error = str(e)
            logger.error(f'AnthropicClient initialization error: {self.error}')
        self.computer_control = ComputerControl()

    def set_instructions(self, instructions):
        self.instructions = instructions
        logger.info(f'Instructions set: {instructions}')

    def run_agent(self, update_callback):
        if self.error:
            update_callback(f'Error: {self.error}')
            logger.error(f'Agent run failed due to initialization error: {self.error}')
            return
        self.running = True
        self.error = None
        self.run_history = [{'role': 'user', 'content': self.instructions}]
        logger.info('Starting agent run')
        while self.running:
            try:
                message = self.anthropic_client.get_next_action(self.run_history)
                self.run_history.append(message)
                logger.debug(f'Received message from Anthropic: {message}')
                self.display_assistant_message(message, update_callback)
                action = self.extract_action(message)
                logger.info(f'Extracted action: {action}')
                if action['type'] == 'error':
                    self.error = action['message']
                    update_callback(f'Error: {self.error}')
                    logger.error(f'Action extraction error: {self.error}')
                    self.running = False
                    break
                elif action['type'] == 'finish':
                    update_callback('Task completed successfully.')
                    logger.info('Task completed successfully')
                    self.running = False
                    break
                try:
                    screenshot = self.computer_control.perform_action(action)
                    if screenshot:
                        self.run_history.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': self.last_tool_use_id, 'content': [{'type': 'text', 'text': 'Here is a screenshot after the action was executed'}, {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}}]}]})
                        logger.debug('Screenshot added to run history')
                except Exception as action_error:
                    error_msg = f'Action failed: {str(action_error)}'
                    update_callback(f'Error: {error_msg}')
                    logger.error(error_msg)
                    self.run_history.append({'role': 'user', 'content': [{'type': 'text', 'text': error_msg}]})
            except Exception as e:
                self.error = str(e)
                update_callback(f'Error: {self.error}')
                logger.exception(f'Unexpected error during agent run: {self.error}')
                self.running = False
                break

    def stop_run(self):
        """Stop the current agent run and clean up resources"""
        self.running = False
        if hasattr(self, 'computer_control'):
            self.computer_control.cleanup()
        logger.info('Agent run stopped')
        self.run_history.append({'role': 'user', 'content': [{'type': 'text', 'text': 'Agent run stopped by user.'}]})

    def extract_action(self, message):
        logger.debug(f'Extracting action from message: {message}')
        if not isinstance(message, BetaMessage):
            logger.error(f'Unexpected message type: {type(message)}')
            return {'type': 'error', 'message': 'Unexpected message type'}
        for item in message.content:
            if isinstance(item, BetaToolUseBlock):
                tool_use = item
                logger.debug(f'Found tool use: {tool_use}')
                self.last_tool_use_id = tool_use.id
                if tool_use.name == 'finish_run':
                    return {'type': 'finish'}
                if tool_use.name != 'computer':
                    logger.error(f'Unexpected tool: {tool_use.name}')
                    return {'type': 'error', 'message': f'Unexpected tool: {tool_use.name}'}
                input_data = tool_use.input
                action_type = input_data.get('action')
                if action_type in ['mouse_move', 'left_click_drag']:
                    if 'coordinate' not in input_data or len(input_data['coordinate']) != 2:
                        logger.error(f'Invalid coordinate for mouse action: {input_data}')
                        return {'type': 'error', 'message': 'Invalid coordinate for mouse action'}
                    return {'type': action_type, 'x': input_data['coordinate'][0], 'y': input_data['coordinate'][1]}
                elif action_type in ['left_click', 'right_click', 'middle_click', 'double_click', 'screenshot', 'cursor_position']:
                    return {'type': action_type}
                elif action_type in ['type', 'key']:
                    if 'text' not in input_data:
                        logger.error(f'Missing text for keyboard action: {input_data}')
                        return {'type': 'error', 'message': 'Missing text for keyboard action'}
                    return {'type': action_type, 'text': input_data['text']}
                else:
                    logger.error(f'Unsupported action: {action_type}')
                    return {'type': 'error', 'message': f'Unsupported action: {action_type}'}
        logger.error('No tool use found in message')
        return {'type': 'error', 'message': 'No tool use found in message'}

    def display_assistant_message(self, message, update_callback):
        if isinstance(message, BetaMessage):
            for item in message.content:
                if isinstance(item, BetaTextBlock):
                    text = item.text.strip()
                    if text:
                        update_callback(f'Assistant: {text}')
                elif isinstance(item, BetaToolUseBlock):
                    tool_name = item.name
                    tool_input = item.input
                    if tool_name == 'computer':
                        action = {'type': tool_input.get('action'), 'x': tool_input.get('coordinate', [0, 0])[0] if 'coordinate' in tool_input else None, 'y': tool_input.get('coordinate', [0, 0])[1] if 'coordinate' in tool_input else None, 'text': tool_input.get('text')}
                        update_callback(f'Performed action: {json.dumps(action)}')
                    elif tool_name == 'finish_run':
                        update_callback('Assistant: Task completed! ')
                    else:
                        update_callback(f'Assistant action: {tool_name} - {json.dumps(tool_input)}')

    def cleanup(self):
        if hasattr(self, 'computer_control'):
            self.computer_control.cleanup()

def __init__(self):
    self.instructions = ''
    self.fully_auto = True
    self.running = False
    self.error = None
    self.run_history = []
    self.last_tool_use_id = None
    try:
        self.anthropic_client = AnthropicClient()
    except ValueError as e:
        self.error = str(e)
        logger.error(f'AnthropicClient initialization error: {self.error}')
    self.computer_control = ComputerControl()

def set_instructions(self, instructions):
    self.instructions = instructions
    logger.info(f'Instructions set: {instructions}')

def run_agent(self, update_callback):
    if self.error:
        update_callback(f'Error: {self.error}')
        logger.error(f'Agent run failed due to initialization error: {self.error}')
        return
    self.running = True
    self.error = None
    self.run_history = [{'role': 'user', 'content': self.instructions}]
    logger.info('Starting agent run')
    while self.running:
        try:
            message = self.anthropic_client.get_next_action(self.run_history)
            self.run_history.append(message)
            logger.debug(f'Received message from Anthropic: {message}')
            self.display_assistant_message(message, update_callback)
            action = self.extract_action(message)
            logger.info(f'Extracted action: {action}')
            if action['type'] == 'error':
                self.error = action['message']
                update_callback(f'Error: {self.error}')
                logger.error(f'Action extraction error: {self.error}')
                self.running = False
                break
            elif action['type'] == 'finish':
                update_callback('Task completed successfully.')
                logger.info('Task completed successfully')
                self.running = False
                break
            try:
                screenshot = self.computer_control.perform_action(action)
                if screenshot:
                    self.run_history.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': self.last_tool_use_id, 'content': [{'type': 'text', 'text': 'Here is a screenshot after the action was executed'}, {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}}]}]})
                    logger.debug('Screenshot added to run history')
            except Exception as action_error:
                error_msg = f'Action failed: {str(action_error)}'
                update_callback(f'Error: {error_msg}')
                logger.error(error_msg)
                self.run_history.append({'role': 'user', 'content': [{'type': 'text', 'text': error_msg}]})
        except Exception as e:
            self.error = str(e)
            update_callback(f'Error: {self.error}')
            logger.exception(f'Unexpected error during agent run: {self.error}')
            self.running = False
            break

def extract_action(self, message):
    logger.debug(f'Extracting action from message: {message}')
    if not isinstance(message, BetaMessage):
        logger.error(f'Unexpected message type: {type(message)}')
        return {'type': 'error', 'message': 'Unexpected message type'}
    for item in message.content:
        if isinstance(item, BetaToolUseBlock):
            tool_use = item
            logger.debug(f'Found tool use: {tool_use}')
            self.last_tool_use_id = tool_use.id
            if tool_use.name == 'finish_run':
                return {'type': 'finish'}
            if tool_use.name != 'computer':
                logger.error(f'Unexpected tool: {tool_use.name}')
                return {'type': 'error', 'message': f'Unexpected tool: {tool_use.name}'}
            input_data = tool_use.input
            action_type = input_data.get('action')
            if action_type in ['mouse_move', 'left_click_drag']:
                if 'coordinate' not in input_data or len(input_data['coordinate']) != 2:
                    logger.error(f'Invalid coordinate for mouse action: {input_data}')
                    return {'type': 'error', 'message': 'Invalid coordinate for mouse action'}
                return {'type': action_type, 'x': input_data['coordinate'][0], 'y': input_data['coordinate'][1]}
            elif action_type in ['left_click', 'right_click', 'middle_click', 'double_click', 'screenshot', 'cursor_position']:
                return {'type': action_type}
            elif action_type in ['type', 'key']:
                if 'text' not in input_data:
                    logger.error(f'Missing text for keyboard action: {input_data}')
                    return {'type': 'error', 'message': 'Missing text for keyboard action'}
                return {'type': action_type, 'text': input_data['text']}
            else:
                logger.error(f'Unsupported action: {action_type}')
                return {'type': 'error', 'message': f'Unsupported action: {action_type}'}
    logger.error('No tool use found in message')
    return {'type': 'error', 'message': 'No tool use found in message'}

def display_assistant_message(self, message, update_callback):
    if isinstance(message, BetaMessage):
        for item in message.content:
            if isinstance(item, BetaTextBlock):
                text = item.text.strip()
                if text:
                    update_callback(f'Assistant: {text}')
            elif isinstance(item, BetaToolUseBlock):
                tool_name = item.name
                tool_input = item.input
                if tool_name == 'computer':
                    action = {'type': tool_input.get('action'), 'x': tool_input.get('coordinate', [0, 0])[0] if 'coordinate' in tool_input else None, 'y': tool_input.get('coordinate', [0, 0])[1] if 'coordinate' in tool_input else None, 'text': tool_input.get('text')}
                    update_callback(f'Performed action: {json.dumps(action)}')
                elif tool_name == 'finish_run':
                    update_callback('Assistant: Task completed! ')
                else:
                    update_callback(f'Assistant action: {tool_name} - {json.dumps(tool_input)}')

class AnthropicClient:

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError('ANTHROPIC_API_KEY not found in environment variables')
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.prompt_manager = PromptManager()
        except Exception as e:
            raise ValueError(f'Failed to initialize Anthropic client: {str(e)}')

    def get_next_action(self, run_history) -> BetaMessage:
        try:
            cleaned_history = []
            for message in run_history:
                if isinstance(message, BetaMessage):
                    cleaned_history.append({'role': message.role, 'content': message.content})
                elif isinstance(message, dict):
                    cleaned_history.append(message)
                else:
                    raise ValueError(f'Unexpected message type: {type(message)}')
            response = self.client.beta.messages.create(model='claude-3-5-sonnet-20241022', max_tokens=1024, tools=[{'type': 'computer_20241022', 'name': 'computer', 'display_width_px': 1280, 'display_height_px': 800, 'display_number': 1}, {'name': 'finish_run', 'description': 'Call this function when you have achieved the goal of the task.', 'input_schema': {'type': 'object', 'properties': {'success': {'type': 'boolean', 'description': 'Whether the task was successful'}, 'error': {'type': 'string', 'description': 'The error message if the task was not successful'}}, 'required': ['success']}}], messages=cleaned_history, system=self.prompt_manager.get_current_prompt(), betas=['computer-use-2024-10-22'])
            has_tool_use = any((isinstance(content, BetaToolUseBlock) for content in response.content))
            if not has_tool_use:
                text_content = next((content.text for content in response.content if isinstance(content, BetaTextBlock)), '')
                response.content.append(BetaToolUseBlock(id='synthetic_finish', type='tool_use', name='finish_run', input={'success': False, 'error': f'Claude needs more information: {text_content}'}))
                logging.info(f'Added synthetic finish_run for text-only response: {text_content}')
            return response
        except anthropic.APIError as e:
            raise Exception(f'API Error: {str(e)}')
        except Exception as e:
            raise Exception(f'Unexpected error: {str(e)}')

def get_next_action(self, run_history) -> BetaMessage:
    try:
        cleaned_history = []
        for message in run_history:
            if isinstance(message, BetaMessage):
                cleaned_history.append({'role': message.role, 'content': message.content})
            elif isinstance(message, dict):
                cleaned_history.append(message)
            else:
                raise ValueError(f'Unexpected message type: {type(message)}')
        response = self.client.beta.messages.create(model='claude-3-5-sonnet-20241022', max_tokens=1024, tools=[{'type': 'computer_20241022', 'name': 'computer', 'display_width_px': 1280, 'display_height_px': 800, 'display_number': 1}, {'name': 'finish_run', 'description': 'Call this function when you have achieved the goal of the task.', 'input_schema': {'type': 'object', 'properties': {'success': {'type': 'boolean', 'description': 'Whether the task was successful'}, 'error': {'type': 'string', 'description': 'The error message if the task was not successful'}}, 'required': ['success']}}], messages=cleaned_history, system=self.prompt_manager.get_current_prompt(), betas=['computer-use-2024-10-22'])
        has_tool_use = any((isinstance(content, BetaToolUseBlock) for content in response.content))
        if not has_tool_use:
            text_content = next((content.text for content in response.content if isinstance(content, BetaTextBlock)), '')
            response.content.append(BetaToolUseBlock(id='synthetic_finish', type='tool_use', name='finish_run', input={'success': False, 'error': f'Claude needs more information: {text_content}'}))
            logging.info(f'Added synthetic finish_run for text-only response: {text_content}')
        return response
    except anthropic.APIError as e:
        raise Exception(f'API Error: {str(e)}')
    except Exception as e:
        raise Exception(f'Unexpected error: {str(e)}')

