# Cluster 7

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

class ComputerControl:

    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        pyautogui.PAUSE = 0.5
        self.last_click_position = None

    def perform_action(self, action):
        action_type = action['type']
        before_screenshot = self.take_screenshot()
        try:
            if action_type == 'mouse_move':
                x, y = self.map_from_ai_space(action['x'], action['y'])
                pyautogui.moveTo(x, y)
                time.sleep(0.2)
            elif action_type == 'left_click':
                pyautogui.click()
                time.sleep(0.2)
                self.last_click_position = pyautogui.position()
            elif action_type == 'right_click':
                pyautogui.rightClick()
                time.sleep(0.2)
            elif action_type == 'middle_click':
                pyautogui.middleClick()
                time.sleep(0.2)
            elif action_type == 'double_click':
                pyautogui.doubleClick()
                time.sleep(0.2)
                self.last_click_position = pyautogui.position()
            elif action_type == 'left_click_drag':
                start_x, start_y = pyautogui.position()
                end_x, end_y = self.map_from_ai_space(action['x'], action['y'])
                pyautogui.dragTo(end_x, end_y, button='left', duration=0.5)
                time.sleep(0.2)
            elif action_type == 'type':
                if self.last_click_position:
                    current_pos = pyautogui.position()
                    if current_pos != self.last_click_position:
                        pyautogui.click(self.last_click_position)
                        time.sleep(0.2)
                pyautogui.write(action['text'], interval=0.1)
                time.sleep(0.2)
            elif action_type == 'key':
                pyautogui.press(action['text'])
                time.sleep(0.2)
            elif action_type == 'screenshot':
                return self.take_screenshot()
            elif action_type == 'cursor_position':
                x, y = pyautogui.position()
                return self.map_to_ai_space(x, y)
            else:
                raise ValueError(f'Unsupported action: {action_type}')
            after_screenshot = self.take_screenshot()
            return after_screenshot
        except Exception as e:
            raise Exception(f'Action failed: {action_type} - {str(e)}')

    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        ai_screenshot = self.resize_for_ai(screenshot)
        buffered = io.BytesIO()
        ai_screenshot.save(buffered, format='PNG')
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def map_from_ai_space(self, x, y):
        ai_width, ai_height = (1280, 800)
        return (x * self.screen_width / ai_width, y * self.screen_height / ai_height)

    def map_to_ai_space(self, x, y):
        ai_width, ai_height = (1280, 800)
        return (x * ai_width / self.screen_width, y * ai_height / self.screen_height)

    def resize_for_ai(self, screenshot):
        return screenshot.resize((1280, 800), Image.LANCZOS)

    def cleanup(self):
        """Clean up any resources or running processes"""
        pass

def perform_action(self, action):
    action_type = action['type']
    before_screenshot = self.take_screenshot()
    try:
        if action_type == 'mouse_move':
            x, y = self.map_from_ai_space(action['x'], action['y'])
            pyautogui.moveTo(x, y)
            time.sleep(0.2)
        elif action_type == 'left_click':
            pyautogui.click()
            time.sleep(0.2)
            self.last_click_position = pyautogui.position()
        elif action_type == 'right_click':
            pyautogui.rightClick()
            time.sleep(0.2)
        elif action_type == 'middle_click':
            pyautogui.middleClick()
            time.sleep(0.2)
        elif action_type == 'double_click':
            pyautogui.doubleClick()
            time.sleep(0.2)
            self.last_click_position = pyautogui.position()
        elif action_type == 'left_click_drag':
            start_x, start_y = pyautogui.position()
            end_x, end_y = self.map_from_ai_space(action['x'], action['y'])
            pyautogui.dragTo(end_x, end_y, button='left', duration=0.5)
            time.sleep(0.2)
        elif action_type == 'type':
            if self.last_click_position:
                current_pos = pyautogui.position()
                if current_pos != self.last_click_position:
                    pyautogui.click(self.last_click_position)
                    time.sleep(0.2)
            pyautogui.write(action['text'], interval=0.1)
            time.sleep(0.2)
        elif action_type == 'key':
            pyautogui.press(action['text'])
            time.sleep(0.2)
        elif action_type == 'screenshot':
            return self.take_screenshot()
        elif action_type == 'cursor_position':
            x, y = pyautogui.position()
            return self.map_to_ai_space(x, y)
        else:
            raise ValueError(f'Unsupported action: {action_type}')
        after_screenshot = self.take_screenshot()
        return after_screenshot
    except Exception as e:
        raise Exception(f'Action failed: {action_type} - {str(e)}')

