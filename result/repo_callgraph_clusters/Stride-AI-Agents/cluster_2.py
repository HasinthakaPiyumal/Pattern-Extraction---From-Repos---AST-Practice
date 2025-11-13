# Cluster 2

def generate_completion(role, task, content):
    """
    Generate a completion using OpenAI's GPT model.
    This function demonstrates how to interact with OpenAI's API.
    """
    logging.info(f'Generating completion for {role}')
    response = client.chat.completions.create(model='gpt-4o', messages=[{'role': 'system', 'content': f'You are a {role}. {task}'}, {'role': 'user', 'content': content}])
    return response.choices[0].message.content

def analyze_website_content(content):
    """
    Analyze the scraped website content using OpenAI.
    This function demonstrates how to use AI for content analysis.
    """
    logging.info('Analyzing website content')
    analysis = generate_completion('marketing analyst', 'Analyze the following website content and provide key insights for marketing strategy.', content)
    return {'analysis': analysis}

def create_campaign_idea(target_audience, goals):
    """
    Create a campaign idea based on target audience and goals using OpenAI.
    This function demonstrates AI's capability in strategic planning.
    """
    logging.info('Creating campaign idea')
    campaign_idea = generate_completion('marketing strategist', 'Create an innovative campaign idea based on the target audience and goals provided.', f'Target Audience: {target_audience}\nGoals: {goals}')
    return {'campaign_idea': campaign_idea}

def generate_copy(brief):
    """
    Generate marketing copy based on a brief using OpenAI.
    This function shows how AI can be used for content creation.
    """
    logging.info('Generating marketing copy')
    copy = generate_completion('copywriter', 'Create compelling marketing copy based on the following brief.', brief)
    return {'copy': copy}

def extract_urls(text):
    url_pattern = re.compile('(https?://\\S+)')
    return url_pattern.findall(text)

def extract_urls(text):
    url_pattern = re.compile('(https?://\\S+)')
    return url_pattern.findall(text)

def query_qdrant(query, collection_name, vector_name='article', top_k=5):
    embedded_query = client.embeddings.create(input=query, model=EMBEDDING_MODEL).data[0].embedding
    query_results = qdrant.search(collection_name=collection_name, query_vector=(vector_name, embedded_query), limit=top_k)
    return query_results

def query_qdrant(query, collection_name, vector_name='article', top_k=5):
    embedded_query = client.embeddings.create(input=query, model=EMBEDDING_MODEL).data[0].embedding
    query_results = qdrant.search(collection_name=collection_name, query_vector=(vector_name, embedded_query), limit=top_k)
    return query_results

def query_qdrant(query, collection_name, vector_name='article', top_k=5):
    embedded_query = client.embeddings.create(input=query, model=EMBEDDING_MODEL).data[0].embedding
    query_results = qdrant.search(collection_name=collection_name, query_vector=(vector_name, embedded_query), limit=top_k)
    return query_results

class AssistantsEngine:

    def __init__(self, client, tasks):
        self.client = client
        self.assistants = []
        self.tasks = tasks
        self.thread = self.initialize_thread()

    def initialize_thread(self):
        thread = self.client.beta.threads.create()
        return thread

    def reset_thread(self):
        self.thread = self.client.beta.threads.create()

    def load_all_assistants(self):
        base_path = 'assistants'
        tools_base_path = 'tools'
        tool_defs = {}
        for tool_dir in os.listdir(tools_base_path):
            if '__pycache__' in tool_dir:
                continue
            tool_dir_path = os.path.join(tools_base_path, tool_dir)
            if os.path.isdir(tool_dir_path):
                tool_json_path = os.path.join(tool_dir_path, 'tool.json')
                if os.path.isfile(tool_json_path):
                    with open(tool_json_path, 'r') as file:
                        tool_def = json.load(file)
                        tool_defs[tool_def['function']['name']] = tool_def['function']
        for assistant_dir in os.listdir(base_path):
            if '__pycache__' in assistant_dir:
                continue
            assistant_config_path = os.path.join(base_path, assistant_dir, 'assistant.json')
            if os.path.exists(assistant_config_path):
                with open(assistant_config_path, 'r') as file:
                    assistant_config = json.load(file)[0]
                    assistant_name = assistant_config.get('name', assistant_dir)
                    log_flag = assistant_config.pop('log_flag', False)
                    assistant_tools_names = assistant_config.get('tools', [])
                    assistant_tools = [tool_defs[name] for name in assistant_tools_names if name in tool_defs]
                    existing_assistants = self.client.beta.assistants.list()
                    loaded_assistant = next((a for a in existing_assistants if a.name == assistant_name), None)
                    if loaded_assistant:
                        assistant_tools = [{'type': 'function', 'function': tool_defs[name]} for name in assistant_tools_names if name in tool_defs]
                        assistant_config['tools'] = assistant_tools
                        assistant_config['name'] = assistant_name
                        loaded_assistant = self.client.beta.assistants.create(**assistant_config)
                        print(f"Assistant '{assistant_name}' created.\n")
                    asst_object = Assistant(name=assistant_name, log_flag=log_flag, instance=loaded_assistant, tools=assistant_tools)
                    self.assistants.append(asst_object)

    def initialize_and_display_assistants(self):
        """
            Loads all assistants and displays their information.
            """
        self.load_all_assistants()
        for asst in self.assistants:
            print(f'\n{Colors.HEADER}Initializing assistant:{Colors.ENDC}')
            print(f'{Colors.OKBLUE}Assistant name:{Colors.ENDC} {Colors.BOLD}{asst.name}{Colors.ENDC}')
            if asst.instance and hasattr(asst.instance, 'tools'):
                print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} {asst.instance.tools} \n')
            else:
                print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} Not available \n')

    def get_assistant(self, assistant_name):
        for assistant in self.assistants:
            if assistant.name == assistant_name:
                return assistant
        print('No assistant found')
        return None

    def triage_request(self, message, test_mode):
        """
        Analyze the user message and delegate it to the appropriate assistant.
        """
        assistant_name = self.determine_appropriate_assistant(message)
        assistant = self.get_assistant(assistant_name)
        if assistant:
            print(f'{Colors.OKGREEN}\nSelected Assistant:{Colors.ENDC} {Colors.BOLD}{assistant.name}{Colors.ENDC}')
            assistant.add_assistant_message('Selected Assistant: ' + assistant.name)
            return assistant
        if not test_mode:
            print('No assistant found')
        return None

    def determine_appropriate_assistant(self, message):
        triage_message = [{'role': 'system', 'content': TRIAGE_SYSTEM_PROMPT}]
        triage_message.append({'role': 'user', 'content': TRIAGE_MESSAGE_PROMPT.format(message, [asst.instance for asst in self.assistants])})
        response = get_completion(self.client, triage_message)
        return response.content

    def run_request(self, request, assistant, test_mode):
        """
        Run the request with the selected assistant and monitor its status.
        """
        self.client.beta.threads.messages.create(thread_id=self.thread.id, role='user', content=request)
        run = self.client.beta.threads.runs.create(thread_id=self.thread.id, assistant_id=assistant.instance.id)
        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            if run.status in ['queued', 'in_progress']:
                time.sleep(2)
                if not test_mode:
                    print('waiting for run')
            elif run.status == 'requires_action':
                tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                self.handle_tool_call(tool_call, run)
            elif run.status in ['completed', 'expired', 'cancelling', 'cancelled', 'failed']:
                if not test_mode:
                    print(f'\nrun {run.status}')
                break
        if assistant.log_flag:
            self.store_messages()
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        assistant_response = next((msg for msg in messages.data if msg.role == 'assistant' and msg.content), None)
        if assistant_response:
            assistant_response_text = assistant_response.content[0].text.value
            if not test_mode:
                print(f'{Colors.RED}Response:{Colors.ENDC} {assistant_response_text}', '\n')
            return assistant_response_text
        return 'No response from the assistant.'

    def handle_tool_call(self, tool_call, run):
        tool_name = tool_call.function.name
        tool_dir = os.path.join(os.getcwd(), 'tools', tool_name)
        handler_path = os.path.join(tool_dir, 'handler.py')
        if os.path.isfile(handler_path):
            spec = importlib.util.spec_from_file_location(f'{tool_name}_handler', handler_path)
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            tool_handler = getattr(tool_module, tool_name + '_assistants')
            handler_args = {'tool_id': tool_call.id}
            tool_args = json.loads(tool_call.function.arguments)
            for arg_name, arg_value in tool_args.items():
                if arg_value is not None:
                    handler_args[arg_name] = arg_value
            print(f'{Colors.HEADER}Running Tool:{Colors.ENDC} {tool_name}')
            print(handler_args)
            tool_response = tool_handler(**handler_args)
            self.client.beta.threads.runs.submit_tool_outputs(thread_id=self.thread.id, run_id=run.id, tool_outputs=[{'tool_call_id': tool_call.id, 'output': json.dumps({'result': tool_response})}])
        else:
            print(f'No handler found for tool {tool_name}')

    def store_messages(self, filename='threads/thread_data.json'):
        thread = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        messages = []
        for message in thread.data:
            role = message.role
            run_id = message.run_id
            assistant_id = message.assistant_id
            thread_id = message.thread_id
            created_at = message.created_at
            content_value = message.content[0].text.value
            messages.append({'role': role, 'run_id': run_id, 'assistant_id': assistant_id, 'thread_id': thread_id, 'created_at': created_at, 'content': content_value})
        try:
            with open(filename, 'r') as file:
                existing_threads = json.load(file)
        except:
            existing_threads = []
        existing_threads.append(messages)
        try:
            with open(filename, 'w') as file:
                json.dump(existing_threads, file, indent=4)
        except Exception as e:
            print(f'Error while saving to file: {e}')

    def run_task(self, task, test_mode):
        """
            Processes a given task. If the assistant is set to 'auto', it determines the appropriate
            assistant using triage_request. Otherwise, it uses the specified assistant.
            """
        if not test_mode:
            print(f'{Colors.OKCYAN}User Query:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}')
        else:
            print(f'{Colors.OKCYAN}Test:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}')
        if task.assistant == 'auto':
            assistant = self.triage_request(task.description, test_mode)
        else:
            assistant = self.get_assistant(task.assistant)
            print(f'{Colors.OKGREEN}\nSelected Assistant:{Colors.ENDC} {Colors.BOLD}{assistant.name}{Colors.ENDC}')
        if test_mode:
            task.assistant = assistant.name if assistant else 'None'
        if not assistant:
            if not test_mode:
                print(f'No suitable assistant found for the task: {task.description}')
            return None
        self.reset_thread()
        return self.run_request(task.description, assistant, test_mode)

    def deploy(self, client, test_mode=False, test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        self.client = client
        if test_mode and test_file_path:
            print('\nTesting the swarm\n\n')
            self.load_test_tasks(test_file_path)
        else:
            print('\n🐝🐝🐝 Deploying the swarm 🐝🐝🐝\n\n')
        self.initialize_and_display_assistants()
        total_tests = 0
        groundtruth_tests = 0
        assistant_tests = 0
        for task in self.tasks:
            output = self.run_task(task, test_mode)
            if test_mode and hasattr(task, 'groundtruth'):
                total_tests += 1
                response = get_completion(self.client, [{'role': 'user', 'content': EVALUATE_TASK_PROMPT.format(output, task.groundtruth)}])
                if response.content == 'True':
                    groundtruth_tests += 1
                    print(f'{Colors.OKGREEN}✔ Groundtruth test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{output}{Colors.ENDC}')
                else:
                    print(f'{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{output}{Colors.ENDC}')
                if task.assistant == task.expected_assistant:
                    print(f'{Colors.OKGREEN}✔ Correct assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
                    assistant_tests += 1
                else:
                    print(f'{Colors.RED}✘ Incorrect assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n')
        if test_mode:
            print(f'\n{Colors.OKGREEN}Passed {groundtruth_tests} groundtruth tests out of {total_tests} tests. Success rate: {groundtruth_tests / total_tests * 100}%{Colors.ENDC}\n')
            print(f'{Colors.OKGREEN}Passed {assistant_tests} assistant tests out of {total_tests} tests. Success rate: {groundtruth_tests / total_tests * 100}%{Colors.ENDC}\n')
            print('Completed testing the swarm\n\n')
        else:
            print('🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n')

    def load_test_tasks(self, test_file_path):
        self.tasks = []
        with open(test_file_path, 'r') as file:
            for line in file:
                test_case = json.loads(line)
                task = EvaluationTask(description=test_case['text'], assistant=test_case.get('assistant', 'auto'), groundtruth=test_case['groundtruth'], expected_assistant=test_case['expected_assistant'])
                self.tasks.append(task)

def initialize_thread(self):
    thread = self.client.beta.threads.create()
    return thread

def reset_thread(self):
    self.thread = self.client.beta.threads.create()

class EvalFunction:

    def __init__(self, client, plan, task):
        self.client = client
        self.eval_function = getattr(self, task.eval_function, None)
        self.task = task
        self.groundtruth = task.groundtruth
        self.plan = plan

    def default(self):
        response = get_completion(self.client, [{'role': 'user', 'content': EVAL_GROUNDTRUTH_PROMPT.format(self.plan, self.groundtruth)}])
        if response.content.lower() == 'true':
            return True
        return False

    def numeric(self):
        number_pattern = '\\d+'
        response = self.plan['step'][-1]
        numbers = re.findall(number_pattern, response)
        print(f'Number(s) to compare: {numbers}')
        try:
            ground_truth = ast.literal_eval(self.groundtruth)
        except:
            print(f'Ground truth is not numeric: {self.groundtruth}')
            return False
        try:
            for n in numbers:
                if int(ground_truth) == int(n) or float(ground_truth) == float(n):
                    return True
        except:
            print(f'Error in comparing numbers: {numbers}')
        return False

    def name(self):
        extract_name_prompt = 'You will be provided with a sentence. Your goal is to extract the full names you see in the sentence. Return the names as an array of strings.'
        response = self.plan['step'][-1]
        completion_result = self.client.chat.completions.create(model='gpt-4-turbo-preview', max_tokens=100, temperature=0, messages=[{'role': 'system', 'content': extract_name_prompt}, {'role': 'user', 'content': f'SENTENCE:\n{response}'}])
        name_extract = completion_result.choices[0].message.content
        print(f'Name extracted: {name_extract}')
        try:
            names = ast.literal_eval(name_extract)
            ground_truth = self.groundtruth
            for n in names:
                if n.lower == ground_truth.lower():
                    return True
        except:
            print(f'Issue with extracted names: {name_extract}')
        return False

    def evaluate(self):
        return self.eval_function()

def numeric(self):
    number_pattern = '\\d+'
    response = self.plan['step'][-1]
    numbers = re.findall(number_pattern, response)
    print(f'Number(s) to compare: {numbers}')
    try:
        ground_truth = ast.literal_eval(self.groundtruth)
    except:
        print(f'Ground truth is not numeric: {self.groundtruth}')
        return False
    try:
        for n in numbers:
            if int(ground_truth) == int(n) or float(ground_truth) == float(n):
                return True
    except:
        print(f'Error in comparing numbers: {numbers}')
    return False

def name(self):
    extract_name_prompt = 'You will be provided with a sentence. Your goal is to extract the full names you see in the sentence. Return the names as an array of strings.'
    response = self.plan['step'][-1]
    completion_result = self.client.chat.completions.create(model='gpt-4-turbo-preview', max_tokens=100, temperature=0, messages=[{'role': 'system', 'content': extract_name_prompt}, {'role': 'user', 'content': f'SENTENCE:\n{response}'}])
    name_extract = completion_result.choices[0].message.content
    print(f'Name extracted: {name_extract}')
    try:
        names = ast.literal_eval(name_extract)
        ground_truth = self.groundtruth
        for n in names:
            if n.lower == ground_truth.lower():
                return True
    except:
        print(f'Issue with extracted names: {name_extract}')
    return False

