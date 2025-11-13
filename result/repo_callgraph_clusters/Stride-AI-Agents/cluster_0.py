# Cluster 0

def create_website_folder(url):
    domain = urlparse(url).netloc
    folder_name = domain.split('.')[0]
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def main():
    args = parse_args()
    try:
        validate_all_tools(engine_name)
        validate_all_assistants()
    except:
        raise Exception('Validation failed')
    swarm = Swarm(engine_name=engine_name, persist=persist)
    if args.test is not None:
        test_files = args.test
        if len(test_files) == 0:
            test_file_paths = [f'{test_root}/{test_file}']
        else:
            test_file_paths = [f'{test_root}/{file}' for file in test_files]
        swarm = Swarm(engine_name='local')
        swarm.deploy(test_mode=True, test_file_paths=test_file_paths)
    elif args.input:
        while True:
            print("Enter a task (or 'exit' to quit):")
            task_input = input()
            if task_input.lower() == 'exit':
                break
            task_args = shlex.split(task_input)
            task_parser = argparse.ArgumentParser()
            task_parser.add_argument('description', type=str, nargs='?', default='')
            task_parser.add_argument('--iterate', action='store_true', help='Set the iterate flag for the new task.')
            task_parser.add_argument('--evaluate', action='store_true', help='Set the evaluate flag for the new task.')
            task_parser.add_argument('--assistant', type=str, default='user_interface', help='Specify the assistant for the new task.')
            task_parsed_args = task_parser.parse_args(task_args)
            new_task = Task(description=task_parsed_args.description, iterate=task_parsed_args.iterate, evaluate=task_parsed_args.evaluate, assistant=task_parsed_args.assistant)
            swarm.add_task(new_task)
            swarm.deploy()
            swarm.tasks.clear()
    else:
        swarm.load_tasks()
        swarm.deploy()
    print('\n\n🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['local', 'assistants'], default='local', help='Choose the engine to use.')
    parser.add_argument('--test', nargs='*', help='Run the tests.')
    parser.add_argument('--create-task', type=str, help='Create a new task with the given description.')
    parser.add_argument('task_description', type=str, nargs='?', default='', help='Description of the task to create.')
    parser.add_argument('--assistant', type=str, help='Specify the assistant for the new task.')
    parser.add_argument('--evaluate', action='store_true', help='Set the evaluate flag for the new task.')
    parser.add_argument('--iterate', action='store_true', help='Set the iterate flag for the new task.')
    parser.add_argument('--input', action='store_true', help='If we want CLI')
    return parser.parse_args()

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

