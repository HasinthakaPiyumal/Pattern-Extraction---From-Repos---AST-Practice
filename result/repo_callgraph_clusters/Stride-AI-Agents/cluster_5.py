# Cluster 5

def print_result(result):
    console.print(f'\t[bold]Result:[/bold]')
    for key, value in result.model_dump().items():
        if isinstance(value, str) and value:
            console.print(f'\t{key}: [green]{value[:20]}...[/green]')
    if result.extracted_content:
        items = json.loads(result.extracted_content)
        print(f'\t[bold]{len(items)} blocks is extracted![/bold]')

def before_return_html(driver, html):
    print('[HOOK] before_return_html')
    print(len(html))
    return driver

@pytest.mark.parametrize('query,function_name', [('I want to make a refund!', 'transfer_to_refunds'), ('I want to talk to sales.', 'transfer_to_sales')])
def test_triage_agent_calls_correct_function(query, function_name):
    tool_calls = run_and_get_tool_calls(triage_agent, query)
    assert len(tool_calls) == 1
    assert tool_calls[0]['function']['name'] == function_name

@pytest.mark.parametrize('messages', [[{'role': 'user', 'content': 'Who is the lead singer of U2'}, {'role': 'assistant', 'content': 'Bono is the lead singer of U2.'}], [{'role': 'user', 'content': 'Hello!'}, {'role': 'assistant', 'content': 'Hi there! How can I assist you today?'}, {'role': 'user', 'content': 'I want to make a refund.'}, {'role': 'tool', 'tool_name': 'transfer_to_refunds'}, {'role': 'user', 'content': 'Thank you!'}, {'role': 'assistant', 'content': "You're welcome! Have a great day!"}]])
def test_conversation_is_successful(messages):
    result = conversation_was_successful(messages)
    assert result == True

@pytest.mark.parametrize('query', ["What's the weather in NYC?", 'Tell me the weather in London.', "Do I need an umbrella today? I'm in chicago."])
def test_calls_weather_when_asked(query):
    tool_calls = run_and_get_tool_calls(weather_agent, query)
    assert len(tool_calls) == 1
    assert tool_calls[0]['function']['name'] == 'get_weather'

@pytest.mark.parametrize('query', ["Who's the president of the United States?", 'What is the time right now?', 'Hi!'])
def test_does_not_call_weather_when_not_asked(query):
    tool_calls = run_and_get_tool_calls(weather_agent, query)
    assert not tool_calls

def query_docs(query):
    print(f'Searching knowledge base with query: {query}')
    query_results = query_qdrant(query, collection_name=collection_name)
    output = []
    for i, article in enumerate(query_results):
        title = article.payload['title']
        text = article.payload['text']
        url = article.payload['url']
        output.append((title, text, url))
    if output:
        title, content, _ = output[0]
        response = f'Title: {title}\nContent: {content}'
        truncated_content = re.sub('\\s+', ' ', content[:50] + '...' if len(content) > 50 else content)
        print('Most relevant article title:', truncated_content)
        return {'response': response}
    else:
        print('No results')
        return {'response': 'No results found.'}

def query_docs(query):
    """Query the knowledge base for relevant articles."""
    print(f'Searching knowledge base with query: {query}')
    query_results = query_qdrant(query, collection_name=collection_name)
    output = []
    for i, article in enumerate(query_results):
        title = article.payload['title']
        text = article.payload['text']
        url = article.payload['url']
        output.append((title, text, url))
    if output:
        title, content, _ = output[0]
        response = f'Title: {title}\nContent: {content}'
        truncated_content = re.sub('\\s+', ' ', content[:50] + '...' if len(content) > 50 else content)
        print('Most relevant article title:', truncated_content)
        return {'response': response}
    else:
        print('No results')
        return {'response': 'No results found.'}

def query_docs(query):
    print(f'Searching knowledge base with query: {query}')
    query_results = query_qdrant(query, collection_name=collection_name)
    output = []
    for i, article in enumerate(query_results):
        title = article.payload['title']
        text = article.payload['text']
        url = article.payload['url']
        output.append((title, text, url))
    if output:
        title, content, _ = output[0]
        response = f'Title: {title}\nContent: {content}'
        truncated_content = re.sub('\\s+', ' ', content[:50] + '...' if len(content) > 50 else content)
        print('Most relevant article title:', truncated_content)
        return {'response': response}
    else:
        print('no results')
        return {'response': 'No results found.'}

def get_completion(client, messages: list[dict[str, str]], model: str='gpt-4-0125-preview', max_tokens=2000, temperature=0.7, tools=None, stream=False):
    request_params = {'model': model, 'messages': messages, 'max_tokens': max_tokens, 'temperature': temperature, 'stream': stream}
    if tools and isinstance(tools, list):
        request_params['tools'] = tools
    if stream:
        completion = client.chat.completions.create(**request_params)
        collected_chunks = []
        collected_messages = []
        for chunk in completion:
            collected_chunks.append(chunk)
            chunk_message = chunk.choices[0].delta.content
            collected_messages.append(chunk_message)
            print(chunk_message, end='')
        return collected_messages
    else:
        completion = client.chat.completions.create(**request_params)
        return completion.choices[0].message

class Conversation:

    def __init__(self):
        self.history = []
        self.current_messages = []
        self.summary = None

    def add_tool_call(self, tool_call):
        self.history.append(tool_call)

    def add_output(self, output):
        self.history.append(output)

    def summarize(self):
        self.summary = 'Summary of the conversation'

    def get_summary(self):
        if not self.summary:
            self.summarize()
        return self.summary

    def clear_current_messages(self):
        self.current_messages = []

    def __repr__(self):
        return f'Conversation(History: {len(self.history)}, Current Messages: {len(self.current_messages)}, Summary: {self.summary})'

def add_tool_call(self, tool_call):
    self.history.append(tool_call)

def add_output(self, output):
    self.history.append(output)

def __repr__(self):
    return f'Conversation(History: {len(self.history)}, Current Messages: {len(self.current_messages)}, Summary: {self.summary})'

class Swarm:

    def __init__(self, engine_name, tasks=[], persist=False):
        self.tasks = tasks
        self.engine_name = engine_name
        self.engine = None
        self.persist = persist

    def deploy(self, test_mode=False, test_file_paths=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        client = OpenAI()
        if self.engine_name == 'assistants':
            print(f'{Colors.GREY}Selected engine: Assistants{Colors.ENDC}')
            self.engine = AssistantsEngine(client, self.tasks)
            self.engine.deploy(client, test_mode, test_file_paths)
        elif self.engine_name == 'local':
            print(f'{Colors.GREY}Selected engine: Local{Colors.ENDC}')
            self.engine = LocalEngine(client, self.tasks, persist=self.persist)
            self.engine.deploy(client, test_mode, test_file_paths)

    def load_tasks(self):
        self.tasks = []
        with open(tasks_path, 'r') as file:
            tasks_data = json.load(file)
            for task_json in tasks_data:
                task = Task(description=task_json['description'], iterate=task_json.get('iterate', False), evaluate=task_json.get('evaluate', False), assistant=task_json.get('assistant', 'user_interface'))
                self.tasks.append(task)

    def add_task(self, task):
        self.tasks.append(task)

def add_task(self, task):
    self.tasks.append(task)

class Assistant(BaseModel):
    log_flag: bool
    name: Optional[str] = None
    instance: Optional[Any] = None
    tools: Optional[list] = None
    current_task_id: str = None
    sub_assistants: Optional[list] = None
    runs: list = []
    context: Optional[dict] = {}
    planner: str = 'sequential'

    def initialize_history(self):
        self.context['history'] = []

    def add_user_message(self, message):
        self.context['history'].append({'task_id': self.current_task_id, 'role': 'user', 'content': message})

    def add_assistant_message(self, message):
        self.context['history'].append({'task_id': self.current_task_id, 'role': 'assistant', 'content': message})

    def add_tool_message(self, message):
        self.context['history'].append({'task_id': self.current_task_id, 'role': 'user', 'tool': message})

    def print_conversation(self):
        print(f'\n{Colors.GREY}Conversation with Assistant: {self.name}{Colors.ENDC}\n')
        messages_by_task_id = {}
        for message in self.context['history']:
            task_id = message['task_id']
            if task_id not in messages_by_task_id:
                messages_by_task_id[task_id] = []
            messages_by_task_id[task_id].append(message)
        for task_id, messages in messages_by_task_id.items():
            print(f'{Colors.OKCYAN}Task ID: {task_id}{Colors.ENDC}')
            for message in messages:
                if 'role' in message and message['role'] == 'user':
                    print(f'{Colors.OKBLUE}User:{Colors.ENDC} {message['content']}')
                elif 'tool' in message:
                    tool_message = message['tool']
                    tool_args = ', '.join([f'{arg}: {value}' for arg, value in tool_message['args'].items()])
                    print(f'{Colors.OKGREEN}Tool:{Colors.ENDC} {tool_message['tool']}({tool_args})')
                elif 'role' in message and message['role'] == 'assistant':
                    print(f'{Colors.HEADER}Assistant:{Colors.ENDC} {message['content']}')
            print('\n')

    def evaluate(self, client, task, plan_log):
        """Evaluates the assistant's performance on a task"""
        output = get_completion(client, [{'role': 'user', 'content': EVALUATE_TASK_PROMPT.format(task.description, plan_log)}])
        output.content = output.content.replace("'", '"')
        try:
            return json.loads(output.content)
        except json.JSONDecodeError:
            print('An error occurred while decoding the JSON.')
            return None

    def save_conversation(self, test=False):
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        if not test:
            filename = f'logs/session_{timestamp}.json'
        else:
            filename = f'tests/test_runs/test_{timestamp}.json'
        with open(filename, 'w') as file:
            json.dump(self.context['history'], file)

    def pass_context(self, assistant):
        """Passes the context of the conversation to the assistant"""
        assistant.context['history'] = self.context['history']

def add_user_message(self, message):
    self.context['history'].append({'task_id': self.current_task_id, 'role': 'user', 'content': message})

def add_assistant_message(self, message):
    self.context['history'].append({'task_id': self.current_task_id, 'role': 'assistant', 'content': message})

def add_tool_message(self, message):
    self.context['history'].append({'task_id': self.current_task_id, 'role': 'user', 'tool': message})

class LocalEngine:

    def __init__(self, client, tasks, persist=False):
        self.client = client
        self.assistants = []
        self.last_assistant = None
        self.persist = persist
        self.tasks = tasks
        self.tool_functions = []
        self.global_context = {}

    def load_tools(self):
        tools_path = 'configs/tools'
        self.tool_functions = []
        for tool_dir in os.listdir(tools_path):
            dir_path = os.path.join(tools_path, tool_dir)
            if os.path.isdir(dir_path):
                for tool_name in os.listdir(dir_path):
                    if tool_name.endswith('.json'):
                        with open(os.path.join(dir_path, tool_name), 'r') as file:
                            try:
                                tool_def = json.load(file)
                                tool = Tool(type=tool_def['type'], function=tool_def['function'], human_input=tool_def.get('human_input', False))
                                self.tool_functions.append(tool)
                            except json.JSONDecodeError as e:
                                print(f'Error decoding JSON for tool {tool_name}: {e}')

    def load_all_assistants(self):
        base_path = 'configs/assistants'
        self.load_tools()
        tool_defs = {tool.function.name: tool.function.dict() for tool in self.tool_functions}
        for assistant_dir in os.listdir(base_path):
            if '__pycache__' in assistant_dir:
                continue
            assistant_config_path = os.path.join(base_path, assistant_dir, 'assistant.json')
            if os.path.exists(assistant_config_path):
                try:
                    with open(assistant_config_path, 'r') as file:
                        assistant_config = json.load(file)[0]
                        assistant_tools_names = assistant_config.get('tools', [])
                        assistant_name = assistant_config.get('name', assistant_dir)
                        assistant_tools = [tool for tool in self.tool_functions if tool.function.name in assistant_tools_names]
                        log_flag = assistant_config.pop('log_flag', False)
                        sub_assistants = assistant_config.get('assistants', None)
                        planner = assistant_config.get('planner', 'sequential')
                        print(f"Assistant '{assistant_name}' created.\n")
                        asst_object = Assistant(name=assistant_name, log_flag=log_flag, instance=None, tools=assistant_tools, sub_assistants=sub_assistants, planner=planner)
                        asst_object.initialize_history()
                        self.assistants.append(asst_object)
                except (IOError, json.JSONDecodeError) as e:
                    print(f'Error loading assistant configuration from {assistant_config_path}: {e}')

    def initialize_and_display_assistants(self):
        """
            Loads all assistants and displays their information.
            """
        self.load_all_assistants()
        self.initialize_global_history()
        for asst in self.assistants:
            print(f'\n{Colors.HEADER}Initializing assistant:{Colors.ENDC}')
            print(f'{Colors.OKBLUE}Assistant name:{Colors.ENDC} {Colors.BOLD}{asst.name}{Colors.ENDC}')
            if asst.tools:
                print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} {[tool.function.name for tool in asst.tools]} \n')
            else:
                print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} No tools \n')

    def get_assistant(self, assistant_name):
        for assistant in self.assistants:
            if assistant.name == assistant_name:
                return assistant
        print('No assistant found')
        return None

    def triage_request(self, assistant, message):
        """
        Analyze the user message and delegate it to the appropriate assistant.
        """
        assistant_name = None
        if assistant.sub_assistants is not None:
            assistant_name = self.determine_appropriate_assistant(assistant, message)
            if not assistant_name:
                print('No appropriate assistant determined')
                return None
            assistant_new = self.get_assistant(assistant_name)
            if not assistant_new:
                print(f'No assistant found with name: {assistant_name}')
                return None
            assistant.pass_context(assistant_new)
        else:
            assistant_new = assistant
        if assistant_name and assistant_name != assistant.name:
            print(f'{Colors.OKGREEN}Selecting sub-assistant:{Colors.ENDC} {Colors.BOLD}{assistant_new.name}{Colors.ENDC}')
            assistant.add_assistant_message(f'Selecting sub-assistant: {assistant_new.name}')
        else:
            print(f'{Colors.OKGREEN}Assistant:{Colors.ENDC} {Colors.BOLD}{assistant_new.name}{Colors.ENDC}')
        return assistant_new

    def determine_appropriate_assistant(self, assistant, message):
        triage_message = [{'role': 'system', 'content': TRIAGE_SYSTEM_PROMPT}]
        triage_message.append({'role': 'user', 'content': TRIAGE_MESSAGE_PROMPT.format(message, [(asst.name, asst.tools) for asst in [assistant] + [asst for asst in self.assistants if asst.name in assistant.sub_assistants]])})
        response = get_completion(self.client, triage_message)
        return response.content

    def initiate_run(self, task, assistant, test_mode):
        """
        Run the request with the selected assistant and monitor its status.
        """
        run = Run(assistant, task.description, self.client)
        assistant.current_task_id = task.id
        assistant.runs.append(run)
        planner = assistant.planner
        plan = run.initiate(planner)
        plan_log = {'step': [], 'step_output': []}
        if not isinstance(plan, list):
            plan_log['step'].append('response')
            plan_log['step'].append(plan)
            assistant.add_assistant_message(f'Response to user: {plan}')
            print(f'{Colors.HEADER}Response:{Colors.ENDC} {plan}')
            self.store_context_globally(assistant)
            return (plan_log, plan_log)
        original_plan = plan.copy()
        iterations = 0
        while plan and iterations < max_iterations:
            if isinstance(plan, list):
                step = plan.pop(0)
            else:
                return ('Error generating plan', 'Error generating plan')
            assistant.add_tool_message(step)
            human_input_flag = next((tool.human_input for tool in assistant.tools if tool.function.name == step['tool']), False)
            if step['tool']:
                print(f'{Colors.HEADER}Running Tool:{Colors.ENDC} {step['tool']}')
                if human_input_flag:
                    print(f'\n{Colors.HEADER}Tool {step['tool']} requires human input:{Colors.HEADER}')
                    print(f'{Colors.GREY}Tool arguments:{Colors.ENDC} {step['args']}\n')
                    user_confirmation = input(f"Type 'yes' to execute tool, anything else to skip: ")
                    if user_confirmation.lower() != 'yes':
                        assistant.add_assistant_message(f'Tool {step['tool']} execution skipped by user.')
                        print(f'{Colors.GREY}Skipping tool execution.{Colors.ENDC}')
                        plan_log['step'].append('tool_skipped')
                        plan_log['step_output'].append(f'Tool {step['tool']} execution skipped by user! Task not completed.')
                        continue
                    assistant.add_assistant_message(f'Tool {step['tool']} execution approved by user.')
            tool_output = self.handle_tool_call(assistant, step, test_mode)
            plan_log['step'].append(step)
            plan_log['step_output'].append(tool_output)
            if task.iterate and (not is_dict_empty(plan_log)) and plan:
                iterations += 1
                new_task = ITERATE_PROMPT.format(task.description, original_plan, plan_log)
                plan = run.generate_plan(new_task)
            self.store_context_globally(assistant)
        return (original_plan, plan_log)

    def handle_tool_call(self, assistant, tool_call, test_mode=False):
        tool_name = tool_call['tool']
        tool_dir = os.path.join(os.getcwd(), 'configs/tools', tool_name)
        handler_path = os.path.join(tool_dir, 'handler.py')
        if os.path.isfile(handler_path):
            spec = importlib.util.spec_from_file_location(f'{tool_name}_handler', handler_path)
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            tool_handler = getattr(tool_module, tool_name)
            try:
                tool_response = tool_handler(**tool_call['args'])
            except:
                return 'Failed to execute tool'
            try:
                return tool_response.content
            except:
                return tool_response
        print('No tool file found')
        return 'No tool file found'

    def run_task(self, task, test_mode):
        """
            Processes a given task.
            """
        if not test_mode:
            print(f'{Colors.OKCYAN}User Query:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}')
        else:
            print(f'{Colors.OKCYAN}Test:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}')
        if self.persist and self.last_assistant is not None:
            assistant = self.last_assistant
        else:
            assistant = self.get_assistant(task.assistant)
            assistant.current_task_id = task.id
            assistant.add_user_message(task.description)
        selected_assistant = self.triage_request(assistant, task.description)
        if test_mode:
            task.assistant = selected_assistant.name if selected_assistant else 'None'
        if not selected_assistant:
            if not test_mode:
                print(f'No suitable assistant found for the task: {task.description}')
            return None
        original_plan, plan_log = self.initiate_run(task, selected_assistant, test_mode)
        self.last_assistant = selected_assistant
        if task.evaluate:
            output = assistant.evaluate(self.client, task, plan_log)
            if output is not None:
                success_flag = False
                if not isinstance(output[0], bool):
                    success_flag = False if output[0].lower() == 'false' else bool(output[0])
                message = output[1]
                if success_flag:
                    print(f'\n\x1b[93m{message}\x1b[0m')
                else:
                    print(f'{Colors.RED}{message}{Colors.ENDC}')
                assistant.add_assistant_message(message)
            else:
                message = 'Error evaluating output'
                print(f'{Colors.RED}{message}{Colors.ENDC}')
                assistant.add_assistant_message(message)
        return (original_plan, plan_log)

    def run_tests(self):
        total_groundtruth = 0
        total_planning = 0
        total_assistant = 0
        groundtruth_pass = 0
        planning_pass = 0
        assistant_pass = 0
        for task in self.tasks:
            original_plan, plan_log = self.run_task(task, test_mode=True)
            if task.groundtruth:
                total_groundtruth += 1
                response = get_completion(self.client, [{'role': 'user', 'content': EVAL_GROUNDTRUTH_PROMPT.format(original_plan, task.groundtruth)}])
                if response.content.lower() == 'true':
                    groundtruth_pass += 1
                    print(f'{Colors.OKGREEN}✔ Groundtruth test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}')
                else:
                    print(f'{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}')
                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f'{Colors.OKGREEN}✔ Correct assistant assigned. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
                else:
                    print(f'{Colors.RED}✘ Incorrect assistant assigned. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
            elif task.expected_plan:
                total_planning += 1
                response = get_completion(self.client, [{'role': 'user', 'content': EVAL_PLANNING_PROMPT.format(original_plan, task.expected_plan)}])
                if response.content.lower() == 'true':
                    planning_pass += 1
                    print(f'{Colors.OKGREEN}✔ Planning test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_plan}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}')
                else:
                    print(f'{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_plan}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}')
                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f'{Colors.OKGREEN}✔ Correct assistant assigned.  {Colors.ENDC}{Colors.OKBLUE}Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
                else:
                    print(f'{Colors.RED}✘ Incorrect assistant assigned for. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
            else:
                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f'{Colors.OKGREEN}✔ Correct assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
                else:
                    print(f'{Colors.RED}✘ Incorrect assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
        if total_groundtruth > 0:
            print(f'\n{Colors.OKGREEN}Passed {groundtruth_pass} groundtruth tests out of {total_groundtruth} tests. Success rate: {groundtruth_pass / total_groundtruth * 100}%{Colors.ENDC}\n')
        if total_planning > 0:
            print(f'{Colors.OKGREEN}Passed {planning_pass} planning tests out of {total_planning} tests. Success rate: {planning_pass / total_planning * 100}%{Colors.ENDC}\n')
        if total_assistant > 0:
            print(f'{Colors.OKGREEN}Passed {assistant_pass} assistant tests out of {total_assistant} tests. Success rate: {assistant_pass / total_assistant * 100}%{Colors.ENDC}\n')
        print('Completed testing the swarm\n\n')

    def deploy(self, client, test_mode=False, test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        self.client = client
        if test_mode and test_file_path:
            print('\nTesting the swarm\n\n')
            self.load_test_tasks(test_file_path)
            self.initialize_and_display_assistants()
            self.run_tests()
            for assistant in self.assistants:
                if assistant.name == 'user_interface':
                    assistant.save_conversation(test=True)
        else:
            print('\n🐝🐝🐝 Deploying the swarm 🐝🐝🐝\n\n')
            self.initialize_and_display_assistants()
            print('\n' + '-' * 100 + '\n')
            for task in self.tasks:
                print('Task', task.id)
                print(f'{Colors.BOLD}Running task{Colors.ENDC}')
                self.run_task(task, test_mode)
                print('\n' + '-' * 100 + '\n')
            for assistant in self.assistants:
                if assistant.name == 'user_interface':
                    assistant.save_conversation()

    def load_test_tasks(self, test_file_paths):
        self.tasks = []
        for f in test_file_paths:
            with open(f, 'r') as file:
                for line in file:
                    test_case = json.loads(line)
                    task = EvaluationTask(description=test_case['text'], assistant=test_case.get('assistant', 'user_interface'), groundtruth=test_case.get('groundtruth', None), expected_plan=test_case.get('expected_plan', None), expected_assistant=test_case['expected_assistant'], iterate=test_case.get('iterate', False), evaluate=test_case.get('evaluate', False), eval_function=test_case.get('eval_function', 'default'))
                    self.tasks.append(task)

    def store_context_globally(self, assistant):
        self.global_context['history'].append({assistant.name: assistant.context['history']})

    def initialize_global_history(self):
        self.global_context['history'] = []

def store_context_globally(self, assistant):
    self.global_context['history'].append({assistant.name: assistant.context['history']})

