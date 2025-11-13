# Cluster 3

class Assigner:

    def __init__(self, config: AssignmentConfig, auto_retry: bool=True) -> None:
        """
        Logic:
            1. Check if output folder exists (resume or create)
            2. Walk through all the folders in output folder, and remove the finished samples
            3. Create agents
        """
        self.auto_retry = auto_retry
        self.tqdm_ordered_by_agent = {}
        self.overall_tqdm = None
        self.config = config
        self.free_worker = config.concurrency.copy(deep=True)
        self.agents: Dict[str, AgentClient] = {}
        self.tasks: Dict[str, TaskClient] = {}
        self.task_indices: Dict[str, List[SampleIndex]] = {}
        self.task_worker_fail_count: Dict[str, int] = {}
        self.assignment_lock = threading.Lock()
        self.remaining_tasks: Dict[str, Dict[str, List[int]]] = {}
        self.completions: Dict[str, Dict[str, List[TaskOutput]]] = {}
        self.finished_count = 0
        self.started_count = 0
        self.running_count = 0
        if not os.path.exists(self.config.output):
            os.makedirs(self.config.output)
            with open(os.path.join(self.config.output, 'config.yaml'), 'w') as f:
                f.write(yaml.dump(self.config.dict()))
        for assignment in self.config.assignments:
            agent = assignment.agent
            task = assignment.task
            runs_file = os.path.join(self.get_output_dir(agent, task), 'runs.jsonl')
            result_file = os.path.join(self.get_output_dir(agent, task), 'overall.json')
            if os.path.exists(result_file):
                continue
            if agent not in self.remaining_tasks:
                self.remaining_tasks[agent] = {}
            if task not in self.remaining_tasks[agent]:
                self.remaining_tasks[agent][task] = []
            if task not in self.tasks:
                print(ColorMessage.green(f'creating {task} client...'))
                self.tasks[task] = self.config.definition.task[task].create()
                self.task_indices[task] = self.tasks[task].get_indices()
            self.remaining_tasks[agent][task] = self.task_indices[task].copy()
            if not os.path.exists(runs_file):
                continue
            with open(runs_file, 'r') as f:
                for line in f:
                    try:
                        run = json.loads(line)
                        run.pop('time')
                        index = run.pop('index')
                        assert index is not None
                        run = TaskClientOutput.parse_obj(run)
                        assert isinstance(run.output, TaskOutput)
                    except:
                        continue
                    if index in self.remaining_tasks[agent][task]:
                        self.remaining_tasks[agent][task].remove(index)
                        self.record_completion(agent, task, index, run.output)
                    else:
                        print(ColorMessage.yellow(f'Warning: {agent}/{task}#{index} is finished, but not in the index list.'))
        count = sum([len(self.remaining_tasks[agent][task]) for agent in self.remaining_tasks for task in self.remaining_tasks[agent]])
        print(ColorMessage.cyan(f'Message: {count} samples remaining.'))
        for agent in self.remaining_tasks:
            agent_ = json.dumps(agent)
            tasks_ = len(self.remaining_tasks[agent])
            samples_ = sum([len(self.remaining_tasks[agent][task]) for task in self.remaining_tasks[agent]])
            if samples_ == 0:
                continue
            print(ColorMessage.cyan(f'Agent {agent_} needs to run {tasks_} tasks with total {samples_} samples:'))
            for task in self.remaining_tasks[agent]:
                print(ColorMessage.cyan(f'    Task {json.dumps(task)}: {len(self.remaining_tasks[agent][task])}'))
        for agent in self.remaining_tasks:
            self.agents[agent] = self.config.definition.agent[agent].create()

    def get_output_dir(self, agent: str, task: str) -> str:
        return os.path.join(self.config.output, agent, task)

    def worker_generator(self, interval=10) -> Iterator[Tuple[str, str, SampleIndex]]:
        node_list = ['SRC', 'DST']
        agent_node_index = {}
        task_node_index = {}
        for agent in self.agents:
            node_list.append(agent)
            agent_node_index[agent] = len(node_list) - 1
        for task in self.tasks:
            node_list.append(task)
            task_node_index[task] = len(node_list) - 1
        while True:
            with self.assignment_lock:
                for task in self.tasks:
                    self.free_worker.task[task] = self.tasks[task].get_concurrency()
                print('Running Count: {}'.format(self.running_count))
            with self.assignment_lock:
                edges = {}
                for agent in self.agents:
                    edges[0, agent_node_index[agent]] = self.free_worker.agent[agent]
                for task in self.tasks:
                    edges[task_node_index[task], 1] = self.free_worker.task[task]
                tot_remaining_samples = 0
                for agent in self.remaining_tasks:
                    for task in self.remaining_tasks[agent]:
                        tot_remaining_samples += len(self.remaining_tasks[agent][task])
                        edges[agent_node_index[agent], task_node_index[task]] = len(self.remaining_tasks[agent][task])
            if tot_remaining_samples == 0:
                if self.running_count == 0:
                    break
                else:
                    time.sleep(interval / 2 + random.random() * interval)
                    continue
            graph = Graph(node_count=len(node_list), edges=edges)
            max_flow = MaxFlow(graph, src=0, dst=1)
            if max_flow.max_flow == 0:
                time.sleep(interval / 2 + random.random() * interval)
                continue
            for (src, dst), e in max_flow.edges_dict.items():
                if src not in agent_node_index.values() or dst not in task_node_index.values():
                    continue
                if e.flow == 0:
                    continue
                agent = node_list[src]
                task = node_list[dst]
                for _ in range(e.flow):
                    with self.assignment_lock:
                        index = self.remaining_tasks[agent][task].pop()
                        self.free_worker.agent[agent] -= 1
                        self.free_worker.task[task] -= 1
                    print(ColorMessage.green(f'Assigned {agent}/{task}#{index}'))
                    yield (agent, task, index)
            time.sleep(interval / 2 + random.random() * interval)

    def start(self, tqdm_out=None):
        self.started_count = sum([len(self.remaining_tasks[agent][task]) for agent in self.remaining_tasks for task in self.remaining_tasks[agent]])
        generator = self.worker_generator()
        self.overall_tqdm = tqdm(total=self.started_count, desc='Total', position=0, file=tqdm_out)
        for idx, agent in enumerate(self.remaining_tasks.keys()):
            self.tqdm_ordered_by_agent[agent] = tqdm(total=sum([len(self.remaining_tasks[agent][task]) for task in self.remaining_tasks[agent]]), desc=agent, position=idx + 1, file=tqdm_out)
        while True:
            try:
                agent, task, index = next(generator)
            except StopIteration:
                break
            self.start_worker(agent, task, index, self.finish_callback)
        self.overall_tqdm.close()
        for agent in self.tqdm_ordered_by_agent:
            self.tqdm_ordered_by_agent[agent].close()
        final_message = '\n\n============================================\n' + ColorMessage.cyan(f'Message: {self.started_count} sample(s) started. ') + '\n' + ColorMessage.green(f'   >> {self.finished_count} sample(s) finished successfully.') + '\n'
        if self.started_count != self.finished_count:
            final_message += ColorMessage.red(f'   >> {self.started_count - self.finished_count} sample(s) failed.') + '\n'
        final_message += ColorMessage.cyan(f'   >> results are saved to {self.config.output}') + '\n'
        final_message += '============================================\n\n'
        print(final_message)

    def record_completion(self, agent: str, task: str, index: SampleIndex, result: TaskOutput):

        def calculate_overall_worker():
            nonlocal agent, task, index, result
            task_client = self.tasks[task]
            overall = task_client.calculate_overall(self.completions[agent][task])
            with open(os.path.join(self.get_output_dir(agent, task), 'overall.json'), 'w') as f:
                f.write(json.dumps(overall, indent=4, ensure_ascii=False))
        overall_calculation = False
        with self.assignment_lock:
            if agent not in self.completions:
                self.completions[agent] = {}
            if task not in self.completions[agent]:
                self.completions[agent][task] = []
            result.index = index
            self.completions[agent][task].append(result)
            if len(self.completions[agent][task]) == len(self.task_indices[task]):
                overall_calculation = True
        if overall_calculation:
            output_dir = self.get_output_dir(agent, task)
            if os.path.exists(os.path.join(output_dir, 'overall.json')):
                return
            threading.Thread(target=calculate_overall_worker).start()

    def finish_callback(self, agent: str, task: str, index: SampleIndex, result: TaskClientOutput):
        if result.error == TaskError.NOT_AVAILABLE.value:
            print(ColorMessage.yellow(f'Warning: {task} is not available, retrying.'))
            with self.assignment_lock:
                self.remaining_tasks[agent][task].insert(0, index)
                self.free_worker.agent[agent] += 1
                self.free_worker.task[task] += 1
                self.running_count -= 1
            return
        if result.error is not None:
            print(ColorMessage.yellow(f'Warning: {agent}/{task}#{index} failed with error {result.error} {result.info} {result.output}'))
            if self.auto_retry:
                with self.assignment_lock:
                    self.remaining_tasks[agent][task].insert(0, index)
        output_folder = self.get_output_dir(agent, task)
        os.makedirs(output_folder, exist_ok=True)
        timestamp: int = int(time.time() * 1000)
        time_str = datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        write_to_file = json.dumps({'index': index, **result.dict(), 'time': {'timestamp': timestamp, 'str': time_str}}) + '\n'
        if not result.error:
            target_file = os.path.join(output_folder, 'runs.jsonl')
            with self.assignment_lock:
                self.finished_count += 1
            self.record_completion(agent, task, index, result.output)
            self.overall_tqdm.update(1)
            self.tqdm_ordered_by_agent[agent].update(1)
        else:
            target_file = os.path.join(output_folder, 'error.jsonl')
        with open(target_file, 'a+', encoding='utf-8') as f:
            f.write(write_to_file)
        with self.assignment_lock:
            self.free_worker.agent[agent] += 1
            self.free_worker.task[task] += 1
            self.running_count -= 1

    def start_worker(self, agent: str, task: str, index: SampleIndex, finish_callback: Union[Callable[[str, str, SampleIndex, TaskClientOutput], None], None]=None):

        def worker_thread():
            nonlocal agent, task, index, finish_callback
            result = self.tasks[task].run_sample(index, self.agents[agent])
            if finish_callback:
                finish_callback(agent, task, index, result)
        with self.assignment_lock:
            self.running_count += 1
        threading.Thread(target=worker_thread).start()

def __init__(self, config: AssignmentConfig, auto_retry: bool=True) -> None:
    """
        Logic:
            1. Check if output folder exists (resume or create)
            2. Walk through all the folders in output folder, and remove the finished samples
            3. Create agents
        """
    self.auto_retry = auto_retry
    self.tqdm_ordered_by_agent = {}
    self.overall_tqdm = None
    self.config = config
    self.free_worker = config.concurrency.copy(deep=True)
    self.agents: Dict[str, AgentClient] = {}
    self.tasks: Dict[str, TaskClient] = {}
    self.task_indices: Dict[str, List[SampleIndex]] = {}
    self.task_worker_fail_count: Dict[str, int] = {}
    self.assignment_lock = threading.Lock()
    self.remaining_tasks: Dict[str, Dict[str, List[int]]] = {}
    self.completions: Dict[str, Dict[str, List[TaskOutput]]] = {}
    self.finished_count = 0
    self.started_count = 0
    self.running_count = 0
    if not os.path.exists(self.config.output):
        os.makedirs(self.config.output)
        with open(os.path.join(self.config.output, 'config.yaml'), 'w') as f:
            f.write(yaml.dump(self.config.dict()))
    for assignment in self.config.assignments:
        agent = assignment.agent
        task = assignment.task
        runs_file = os.path.join(self.get_output_dir(agent, task), 'runs.jsonl')
        result_file = os.path.join(self.get_output_dir(agent, task), 'overall.json')
        if os.path.exists(result_file):
            continue
        if agent not in self.remaining_tasks:
            self.remaining_tasks[agent] = {}
        if task not in self.remaining_tasks[agent]:
            self.remaining_tasks[agent][task] = []
        if task not in self.tasks:
            print(ColorMessage.green(f'creating {task} client...'))
            self.tasks[task] = self.config.definition.task[task].create()
            self.task_indices[task] = self.tasks[task].get_indices()
        self.remaining_tasks[agent][task] = self.task_indices[task].copy()
        if not os.path.exists(runs_file):
            continue
        with open(runs_file, 'r') as f:
            for line in f:
                try:
                    run = json.loads(line)
                    run.pop('time')
                    index = run.pop('index')
                    assert index is not None
                    run = TaskClientOutput.parse_obj(run)
                    assert isinstance(run.output, TaskOutput)
                except:
                    continue
                if index in self.remaining_tasks[agent][task]:
                    self.remaining_tasks[agent][task].remove(index)
                    self.record_completion(agent, task, index, run.output)
                else:
                    print(ColorMessage.yellow(f'Warning: {agent}/{task}#{index} is finished, but not in the index list.'))
    count = sum([len(self.remaining_tasks[agent][task]) for agent in self.remaining_tasks for task in self.remaining_tasks[agent]])
    print(ColorMessage.cyan(f'Message: {count} samples remaining.'))
    for agent in self.remaining_tasks:
        agent_ = json.dumps(agent)
        tasks_ = len(self.remaining_tasks[agent])
        samples_ = sum([len(self.remaining_tasks[agent][task]) for task in self.remaining_tasks[agent]])
        if samples_ == 0:
            continue
        print(ColorMessage.cyan(f'Agent {agent_} needs to run {tasks_} tasks with total {samples_} samples:'))
        for task in self.remaining_tasks[agent]:
            print(ColorMessage.cyan(f'    Task {json.dumps(task)}: {len(self.remaining_tasks[agent][task])}'))
    for agent in self.remaining_tasks:
        self.agents[agent] = self.config.definition.agent[agent].create()

def get_output_dir(self, agent: str, task: str) -> str:
    return os.path.join(self.config.output, agent, task)

def start(self, tqdm_out=None):
    self.started_count = sum([len(self.remaining_tasks[agent][task]) for agent in self.remaining_tasks for task in self.remaining_tasks[agent]])
    generator = self.worker_generator()
    self.overall_tqdm = tqdm(total=self.started_count, desc='Total', position=0, file=tqdm_out)
    for idx, agent in enumerate(self.remaining_tasks.keys()):
        self.tqdm_ordered_by_agent[agent] = tqdm(total=sum([len(self.remaining_tasks[agent][task]) for task in self.remaining_tasks[agent]]), desc=agent, position=idx + 1, file=tqdm_out)
    while True:
        try:
            agent, task, index = next(generator)
        except StopIteration:
            break
        self.start_worker(agent, task, index, self.finish_callback)
    self.overall_tqdm.close()
    for agent in self.tqdm_ordered_by_agent:
        self.tqdm_ordered_by_agent[agent].close()
    final_message = '\n\n============================================\n' + ColorMessage.cyan(f'Message: {self.started_count} sample(s) started. ') + '\n' + ColorMessage.green(f'   >> {self.finished_count} sample(s) finished successfully.') + '\n'
    if self.started_count != self.finished_count:
        final_message += ColorMessage.red(f'   >> {self.started_count - self.finished_count} sample(s) failed.') + '\n'
    final_message += ColorMessage.cyan(f'   >> results are saved to {self.config.output}') + '\n'
    final_message += '============================================\n\n'
    print(final_message)

def calculate_overall_worker():
    nonlocal agent, task, index, result
    task_client = self.tasks[task]
    overall = task_client.calculate_overall(self.completions[agent][task])
    with open(os.path.join(self.get_output_dir(agent, task), 'overall.json'), 'w') as f:
        f.write(json.dumps(overall, indent=4, ensure_ascii=False))

def record_completion(self, agent: str, task: str, index: SampleIndex, result: TaskOutput):

    def calculate_overall_worker():
        nonlocal agent, task, index, result
        task_client = self.tasks[task]
        overall = task_client.calculate_overall(self.completions[agent][task])
        with open(os.path.join(self.get_output_dir(agent, task), 'overall.json'), 'w') as f:
            f.write(json.dumps(overall, indent=4, ensure_ascii=False))
    overall_calculation = False
    with self.assignment_lock:
        if agent not in self.completions:
            self.completions[agent] = {}
        if task not in self.completions[agent]:
            self.completions[agent][task] = []
        result.index = index
        self.completions[agent][task].append(result)
        if len(self.completions[agent][task]) == len(self.task_indices[task]):
            overall_calculation = True
    if overall_calculation:
        output_dir = self.get_output_dir(agent, task)
        if os.path.exists(os.path.join(output_dir, 'overall.json')):
            return
        threading.Thread(target=calculate_overall_worker).start()

def finish_callback(self, agent: str, task: str, index: SampleIndex, result: TaskClientOutput):
    if result.error == TaskError.NOT_AVAILABLE.value:
        print(ColorMessage.yellow(f'Warning: {task} is not available, retrying.'))
        with self.assignment_lock:
            self.remaining_tasks[agent][task].insert(0, index)
            self.free_worker.agent[agent] += 1
            self.free_worker.task[task] += 1
            self.running_count -= 1
        return
    if result.error is not None:
        print(ColorMessage.yellow(f'Warning: {agent}/{task}#{index} failed with error {result.error} {result.info} {result.output}'))
        if self.auto_retry:
            with self.assignment_lock:
                self.remaining_tasks[agent][task].insert(0, index)
    output_folder = self.get_output_dir(agent, task)
    os.makedirs(output_folder, exist_ok=True)
    timestamp: int = int(time.time() * 1000)
    time_str = datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    write_to_file = json.dumps({'index': index, **result.dict(), 'time': {'timestamp': timestamp, 'str': time_str}}) + '\n'
    if not result.error:
        target_file = os.path.join(output_folder, 'runs.jsonl')
        with self.assignment_lock:
            self.finished_count += 1
        self.record_completion(agent, task, index, result.output)
        self.overall_tqdm.update(1)
        self.tqdm_ordered_by_agent[agent].update(1)
    else:
        target_file = os.path.join(output_folder, 'error.jsonl')
    with open(target_file, 'a+', encoding='utf-8') as f:
        f.write(write_to_file)
    with self.assignment_lock:
        self.free_worker.agent[agent] += 1
        self.free_worker.task[task] += 1
        self.running_count -= 1

def start_worker(self, agent: str, task: str, index: SampleIndex, finish_callback: Union[Callable[[str, str, SampleIndex, TaskClientOutput], None], None]=None):

    def worker_thread():
        nonlocal agent, task, index, finish_callback
        result = self.tasks[task].run_sample(index, self.agents[agent])
        if finish_callback:
            finish_callback(agent, task, index, result)
    with self.assignment_lock:
        self.running_count += 1
    threading.Thread(target=worker_thread).start()

def analyze_output(config: str, output: str, since_timestamp: float):
    """
    Walk through the output folder (including sub-dir) and analyze the overall.json file
    Rule:
        - valid overall file: **/{agent}/{task}/overall.json
        - if a same (agent, task) pair, select the latest one
    """
    loader = ConfigLoader()
    config: dict = loader.load_from(config)
    assert 'definition' in config, 'definition not found in config'
    assert 'agent' in config['definition'], 'agent not found in config.definition'
    assert 'task' in config['definition'], 'task not found in config.definition'
    agents = set(config['definition']['agent'].keys()).intersection(set(MODEL_MAP.keys()))
    tasks = list(config['definition']['task'].keys())
    print(ColorMessage.cyan(f'Available Agents ({len(agents)}):\n    ' + '\n    '.join(agents) + '\n\n' + f'Available Tasks ({len(tasks)}):\n    ' + '\n    '.join(tasks) + '\n'))
    overall_dict = OrderedDict()
    for root, dirs, files in os.walk(output):
        if 'overall.json' in files:
            root = os.path.abspath(root)
            pattern = root.split('/')
            if len(pattern) < 2:
                continue
            agent = pattern[-2]
            task = pattern[-1]
            ct = os.path.getmtime(os.path.join(root, 'overall.json'))
            if agent not in agents:
                continue
            elif task not in tasks:
                continue
            elif ct < since_timestamp:
                continue
            agent = MODEL_MAP[agent]
            if agent in overall_dict and task in overall_dict[agent]:
                if ct < overall_dict[agent][task]['time']:
                    continue
            overall_dict.setdefault(agent, OrderedDict())
            overall_dict[agent][task] = {'file': os.path.join(root, 'overall.json'), 'time': os.path.getmtime(os.path.join(root, 'overall.json'))}
    agent_names = []
    task_names = []
    validation_names = []
    for agent in overall_dict:
        if agent not in agent_names:
            agent_names.append(agent)
        for task in overall_dict[agent]:
            if task not in task_names:
                task_names.append(task)
            overall_dict[agent][task]['time'] = datetime.datetime.fromtimestamp(overall_dict[agent][task]['time']).strftime('%Y-%m-%d %H:%M:%S')
            with open(overall_dict[agent][task]['file'], 'r', encoding='utf-8') as f:
                overall_dict[agent][task]['overall'] = json.load(f)
            if 'validation' in overall_dict[agent][task]['overall']:
                overall_dict[agent][task]['overall']['validation'] = {validation: VALIDATION_MAP_FUNC[validation](overall_dict[agent][task]['overall']['validation']) for validation in VALIDATION_MAP_FUNC}
                for validation in overall_dict[agent][task]['overall']['validation']:
                    if validation not in validation_names:
                        validation_names.append(validation)
    return (agent_names, task_names, validation_names, overall_dict)

def main(args):
    agent_names, task_names, validation_names, details = analyze_output(args.config, args.output, parse_timestamp(args.time))
    task_names.sort(key=lambda x: TaskHandler.get_handler(x).get_order_priority())
    summary = OrderedDict()
    for agent in details:
        summary[agent] = OrderedDict()
        for task in details[agent]:
            handler = TaskHandler.get_handler(task)
            if handler is not None:
                summary[agent][task] = handler.get_main_metric(details[agent][task]['overall'])
            else:
                summary[agent][task] = details[agent][task]['overall']
    for agent in details:
        for task in details[agent]:
            print(ColorMessage.cyan(f'Agent: {agent:20} Task: {task:20} Path: {details[agent][task]['file']}'))
    final_result = {'summary': summary, 'details': details}
    os.makedirs(args.save, exist_ok=True)
    with open(os.path.join(args.save, 'result.json'), 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=4, ensure_ascii=False, sort_keys=True)
    with open(os.path.join(args.save, 'result.yaml'), 'w', encoding='utf-8') as f:
        yaml.dump(final_result, f, indent=4, allow_unicode=True, sort_keys=True)
    with open(os.path.join(args.save, 'summary.csv'), 'w', encoding='utf-8') as f:
        '\n        Format:\n            Agent\\Task, Task1, Task2, ...\n            Agent1, MainMetric(Agent1,Task1), MainMetric(Agent1,Task2), ...\n            ......\n        '
        f.write('Agent\\Task,' + ','.join(task_names) + '\n')
        for agent in summary:
            f.write(agent + ',' + ','.join([str(summary[agent][task]) if task in summary[agent] else '' for task in task_names]) + '\n')
    agent_validations = {agent: {validation: [] for validation in validation_names} for agent in agent_names}
    task_validations = {task: {validation: [] for validation in validation_names} for task in task_names}
    for agent in summary:
        for task in summary[agent]:
            if 'validation' in details[agent][task]['overall']:
                for validation in details[agent][task]['overall']['validation']:
                    agent_validations[agent][validation].append(details[agent][task]['overall']['validation'][validation])
                    task_validations[task][validation].append(details[agent][task]['overall']['validation'][validation])
    with open(os.path.join(args.save, 'agent_validation.csv'), 'w', encoding='utf-8') as f:
        '\n        Format:\n            Agent\\Validation, Validation1, Validation2, ...\n            Agent1, Avg(Agent1,Validation1), Avg(Agent1,Validation2), ...\n            ......\n        '
        f.write('Agent\\Validation,' + ','.join(validation_names) + '\n')
        for agent in agent_validations:
            f.write(agent + ',' + ','.join([str(sum(agent_validations[agent][validation]) / len(agent_validations[agent][validation])) if validation in agent_validations[agent] and len(agent_validations[agent][validation]) > 0 else '--' for validation in validation_names]) + '\n')
    with open(os.path.join(args.save, 'task_validation.csv'), 'w', encoding='utf-8') as f:
        '\n        Format:\n            Task\\Validation, Validation1, Validation2, ...\n            Task1, Avg(Task1,Validation1), Avg(Task1,Validation2), ...\n            ......\n        '
        f.write('Task\\Validation,' + ','.join(validation_names) + '\n')
        for task in task_validations:
            f.write(task + ',' + ','.join([str(sum(task_validations[task][validation]) / len(task_validations[task][validation])) if validation in task_validations[task] and len(task_validations[task][validation]) > 0 else '--' for validation in validation_names]) + '\n')
    print(ColorMessage.green(f'Analysis result saved to {os.path.abspath(args.save)}'))

class ALFWorld(Task):

    def __init__(self, data_path: Optional[str], config_path: Optional[str], prompts_path: Optional[str], split: str='dev', max_step: int=20, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.data_path = data_path
        if self.data_path is None:
            raise Exception('missing parameter data_path')
        os.environ['ALFWORLD_DATA'] = self.data_path
        self.config_path = config_path
        if self.config_path is None:
            raise Exception('missing parameter config_path')
        self.config = load_config(self.config_path)
        self.prompts_path = prompts_path
        if self.prompts_path is None:
            raise Exception('missing parameter prompts_path')
        self.prompts = load_prompts(self.prompts_path)
        self.data_files = []
        self.split = split
        data_path = os.path.join('data/alfworld', f'{self.split}.json')
        with open(data_path, 'r') as f:
            content = json.loads(f.read())
        for _, v in content.items():
            self.data_files.extend(v)
        self.data_files = [os.path.join(self.data_path, file) for file in self.data_files]
        self.logger.info(f'successfully loaded {len(self.data_files)} games')
        self.logger.debug(f'self.data_files[0]={self.data_files[0]!r}')
        self.max_step = max_step
        self.prefixes = {'pick_and_place': 'put', 'pick_clean_then_place': 'clean', 'pick_heat_then_place': 'heat', 'pick_cool_then_place': 'cool', 'look_at_obj': 'examine', 'pick_two_obj': 'puttwo'}
        self.env = AlfworldEnvWrapper(self.config)

    def get_indices(self) -> List[Any]:
        return list(range(len(self.data_files)))

    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        """
            TaskOutput.result 0/1
        """
        overall = {'total': len([config for config in results if config]), 'pass': len([config for config in results if config and config.result and int(config.result.get('result', 0) == 1)])}
        overall['wrong'] = overall['total'] - overall['pass']
        overall['success_rate'] = overall['pass'] / overall['total'] if overall['total'] else 0
        return {'overall': overall}

    def sync_start_sample(self, index, session: Session) -> TaskSampleExecutionResult:
        data_item = self.data_files[index]
        env = self.env.create_env(data_item)
        try:
            result, log_info, finish_reason = self.alfworld_run(session, env)
        except AgentCancelledException:
            return TaskSampleExecutionResult(status=SampleStatus.CANCELLED)
        except Exception:
            traceback.print_exc()
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR)
        finally:
            self.env.close_env(env)
        log_info.update({'result': result})
        return TaskSampleExecutionResult(status=finish_reason, result=log_info)

    @staticmethod
    def get_task_instruction():
        return 'Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your target is to perform actions to complete) the task goal. At the beginning of your interactions, you will be given the detailed description of the current environment and your goal to accomplish. A tool will be provided for you to use to submit the action you want to take. This tool is the only tool you should and must take in order to operate any action in the environment. The way you perform action is to place the action chosen by you in the arguments field of your tool call. For each of your turn, you will be given a list of actions which you can choose one to perform in this turn. The action you would like to take should be offered in this format: "the name of your next action", and you should fill it in the argument field of your tool call. Note that you should always call a tool to operate an action from the given choices. After your each turn, the environment will give you immediate feedback based on which you plan your next few steps. if the environment output "Nothing happened", that means the previous action is invalid and you should try more options.\n Reminder:\n1. the action must be chosen from the given available actions. Any actions except provided available actions will be regarded as illegal.\n2. Always call the tool to hand in your next action and think when necessary.'

    def get_prompt(self, filename: str):
        for k, v in self.prefixes.items():
            if filename.startswith(k):
                example = self.prompts[v]
                return deepcopy(example)
        raise Exception(f'unsupported name: {filename}')

    @staticmethod
    def get_available_actions(actions):
        actions = '\n'.join(actions)
        return ' AVAILABLE ACTIONS: ' + actions + '\n'

    def alfworld_run(self, session: Session, env):
        finish_reason = SampleStatus.COMPLETED
        ob, info = self.env.reset_env(env)
        ob = '\n'.join(ob[0].split('\n\n')[1:])
        log_info = {'log': []}
        session.inject(ChatCompletionSystemMessageParam(role='system', content=self.get_task_instruction()))
        init_prompt = 'Here is your task. ' + ob + self.get_available_actions(info.get('admissible_commands', [[]])[0])
        log_info['init_prompt'] = init_prompt
        session.inject(ChatCompletionUserMessageParam(role='user', content=init_prompt))
        for i in range(0, self.max_step):
            output = session.sync_action()
            tool_calls = []
            for message in output.messages:
                tool_calls.extend(message.get('tool_calls', []) or [])
            if not tool_calls:
                finish_reason = SampleStatus.AGENT_VALIDATION_FAILED
                session.inject(ChatCompletionUserMessageParam(role='user', content='No executable tool calls found. Please call a tool instead'))
                session.inject(RewardHistoryItem(reward=0, score=0))
                continue
            try:
                tool_call = tool_calls[0]
                arguments = tool_call['function']['arguments']
                arguments = json.loads(arguments)
                arguments = list(arguments.values())
                call_id = tool_call['id']
                admissible_commands = info.get('admissible_commands', [[]])[0]
                output = arguments[0]
                action = process_action(output, admissible_commands)
            except:
                finish_reason = SampleStatus.AGENT_INVALID_ACTION
                session.inject(ChatCompletionUserMessageParam(role='user', content='No valid tool calls found. Please call a tool instead.'))
                session.inject(RewardHistoryItem(reward=0, score=0))
                continue
            observation, reward, done, info = self.env.step_env(env, action)
            observation, reward, done = (process_ob(observation[0]), info['won'][0], done[0])
            session.inject(ChatCompletionToolMessageParam(role='tool', tool_call_id=call_id, content=observation + self.get_available_actions(info.get('admissible_commands', [[]])[0])))
            round_reward = reward
            if 'Nothing happens' in observation:
                round_reward = 0
            session.inject(RewardHistoryItem(reward=round_reward, score=reward))
            payload = {'round': i + 1, 'output': output, 'action': action, 'admissible_commands': admissible_commands, 'observation': observation, 'done': done}
            log_info['log'].append(payload)
            if len(log_info['log']) > 3:
                pre_logs = log_info['log'][-3:]
                pre_acts = [pre_log['output'] for pre_log in pre_logs]
                if len(list(set(pre_acts))) == 1:
                    self.logger.info('repeat actions for 3 times: failure')
                    return (0, log_info, SampleStatus.AGENT_INVALID_ACTION)
            if done:
                return (reward, log_info, finish_reason)
        else:
            finish_reason = SampleStatus.TASK_LIMIT_REACHED
            final_reward = 0
            reward_history = RewardHistoryItem(reward=final_reward, score=0)
            session.inject(reward_history)
        return (0, log_info, finish_reason)

@staticmethod
def get_available_actions(actions):
    actions = '\n'.join(actions)
    return ' AVAILABLE ACTIONS: ' + actions + '\n'

class WebShop(Task):

    def __init__(self, tools=None, **configs):
        super().__init__(**configs)
        self.logger = logging.getLogger(__name__)
        self.ranging = (configs.pop('start', 0), configs.pop('end', 500))
        self.logger.info('Initializing WebShop environment...')
        self.server = WebAgentTextEnv(observation_mode='text', human_goals=True).server
        self.tools = tools
        self.max_rounds = configs.get('round', 20)

    def get_indices(self) -> List[Any]:
        return list(range(*self.ranging))

    def sync_start_sample(self, index: int, session: Session) -> TaskSampleExecutionResult:
        history = []
        env = WebAgentTextEnv(observation_mode='text', server=self.server, human_goals=True, session_prefix=str(uuid4()) + '-')
        try:
            env.reset(index)
            session.inject(ChatCompletionSystemMessageParam(role='system', content=prompt_with_max_turn))
            action = None
            observation = env.observation
            reward = 0
            call_id = None
            for j in range(self.max_rounds):
                available_actions = env.get_available_actions()
                if j == 0:
                    session.inject(ChatCompletionUserMessageParam(role='user', content=f'The initial observation:\n{observation}\n\nAvailable Actions:\n{available_actions}'))
                elif action is None:
                    session.inject(ChatCompletionUserMessageParam(role='user', content=f'Observation:\n{observation}\n\nAvailable Actions:\n{available_actions}'))
                else:
                    session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Action: {action}\n\nObservation:\n{observation}\n\nAvailable Actions:\n{available_actions}', tool_call_id=call_id))
                response = session.sync_action()
                tool_calls = []
                for message in response.messages:
                    tool_calls.extend(message.get('tool_calls', []) or [])
                finish_reason = SampleStatus.COMPLETED
                if not tool_calls:
                    action = None
                    observation = 'No executable tool calls found! You should call a tool instead.'
                else:
                    action = None
                    try:
                        tool_call = tool_calls[0]
                        func_name = tool_call['function']['name']
                        arguments = tool_call['function']['arguments']
                        arguments = json.loads(arguments)
                        arguments = list(arguments.values())
                        call_id = tool_call['id']
                        if func_name == 'search_action':
                            action = f'search[{arguments[0]}]'
                        elif func_name == 'click_action':
                            action = f'click[{arguments[0]}]'
                    except:
                        self.logger.warning(f'Error processing tool call. tool_calls={tool_calls!r}', exc_info=True)
                        session.inject(ChatCompletionUserMessageParam(role='user', content=f'No valid tool call found from agent.'))
                        session.inject(RewardHistoryItem(reward=0, score=0))
                        continue
                history.append({'observation': observation, 'available_actions': available_actions, 'response': response, 'action': action})
                if not action:
                    reward = 0
                    done = False
                    round_reward = 0
                else:
                    observation, reward, done, info = env.step(action)
                    round_reward = reward
                history[-1]['reward'] = reward
                history[-1]['done'] = done
                rewardhistory = RewardHistoryItem(reward=round_reward, score=round_reward)
                session.inject(rewardhistory)
                if done:
                    break
            else:
                finish_reason = SampleStatus.TASK_LIMIT_REACHED
                rewardhistory = RewardHistoryItem(reward=0, score=0)
                session.inject(rewardhistory)
                session.inject(ChatCompletionToolMessageParam(role='tool', content='Task limit reached.', tool_call_id=call_id))
            return TaskSampleExecutionResult(status=finish_reason, result={'reward': reward, 'history': history})
        except AgentCancelledException:
            session.inject(RewardHistoryItem(reward=0, score=0))
            return TaskSampleExecutionResult(status=SampleStatus.CANCELLED, result={'reward': 0, 'history': history})
        except:
            self.logger.exception(f'Error during sample execution')
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR, result={'reward': 0, 'history': history})
        finally:
            try:
                env.close()
            except:
                pass

    def calculate_overall(self, results: List[TaskOutput]) -> Dict:

        def factory(key):

            def f(output):
                output = [x for x in output if x]
                if key == 'history':
                    return sum([len(x[key]) for x in output]) / len(output) if len(output) > 0 else 0
                return sum([x[key] for x in output]) / len(output) if len(output) > 0 else 0
            return f
        results = [x.result for x in results if x]
        return {'reward': factory('reward')(results)}

def f(output):
    output = [x for x in output if x]
    if key == 'history':
        return sum([len(x[key]) for x in output]) / len(output) if len(output) > 0 else 0
    return sum([x[key] for x in output]) / len(output) if len(output) > 0 else 0

class Claude(AgentClient):

    def __init__(self, api_args=None, *args, **config):
        super().__init__(*args, **config)
        if not api_args:
            api_args = {}
        api_args = deepcopy(api_args)
        self.key = api_args.pop('key', None) or os.getenv('Claude_API_KEY')
        api_args['model'] = api_args.pop('model', None)
        if not self.key:
            raise ValueError('Claude API KEY is required, please assign api_args.key or set OPENAI_API_KEY environment variable.')
        if not api_args['model']:
            raise ValueError('Claude model is required, please assign api_args.model.')
        self.api_args = api_args
        if not self.api_args.get('stop_sequences'):
            self.api_args['stop_sequences'] = [anthropic.HUMAN_PROMPT]

    def inference(self, history: List[dict]) -> str:
        prompt = ''
        for message in history:
            if message['role'] == 'user':
                prompt += anthropic.HUMAN_PROMPT + message['content']
            else:
                prompt += anthropic.AI_PROMPT + message['content']
        prompt += anthropic.AI_PROMPT
        c = anthropic.Client(api_key=self.key)
        resp = c.completions.create(prompt=prompt, **self.api_args)
        return str(resp.completion)

def inference(self, history: List[dict]) -> str:
    prompt = ''
    for message in history:
        if message['role'] == 'user':
            prompt += anthropic.HUMAN_PROMPT + message['content']
        else:
            prompt += anthropic.AI_PROMPT + message['content']
    prompt += anthropic.AI_PROMPT
    c = anthropic.Client(api_key=self.key)
    resp = c.completions.create(prompt=prompt, **self.api_args)
    return str(resp.completion)

def get_predefined_structure():
    now = datetime.datetime.now()
    return {'TIMESTAMP': now.strftime('%Y-%m-%d-%H-%M-%S'), 'TIMESTAMP_DATE': now.strftime('%Y-%m-%d'), 'TIMESTAMP_TIME': now.strftime('%H-%M-%S')}

class AssignmentConfig(BaseModel):
    assignments: List[Assignment]
    concurrency: ConcurrencyConfig
    definition: DefinitionConfig
    output: str = None

    @validator('assignments', pre=True)
    def assignments_validation(cls, v):
        assert isinstance(v, list), f"'assignments' must be a list, but got {type(v)}"
        ret = []
        for item in v:
            assert isinstance(item, dict), f"Each item in 'assignments' must be a dict, but got {type(item)}"
            agent = item.get('agent', None)
            if agent is None:
                raise ValueError("'agent' must be specified")
            if isinstance(agent, str):
                agent = [agent]
            task = item.get('task')
            if task is None:
                raise ValueError("'task' must be specified")
            if isinstance(task, str):
                task = [task]
            for a in agent:
                for t in task:
                    ret.append(Assignment(agent=a, task=t))
        return ret

    @validator('output', pre=True)
    def output_validation(cls, v):
        predefined_structure = get_predefined_structure()
        if v is None:
            v = 'output/{TIMESTAMP}'
        assert isinstance(v, str), f"'output' must be a string, but got {type(v)}"
        return v.format(**predefined_structure)

    @classmethod
    def post_validate(cls, instance: 'AssignmentConfig'):
        REMOVE_UNUSED_IN_DEFINITION = True
        REMOVE_UNUSED_IN_CONCURRENCY = True
        agent_in_assignment = set()
        task_in_assignment = set()
        for assignment in instance.assignments:
            assert assignment.agent in instance.definition.agent, f'Agent {assignment.agent} is not defined.'
            agent_in_assignment.add(assignment.agent)
            assert assignment.task in instance.definition.task, f'Task {assignment.task} is not defined.'
            task_in_assignment.add(assignment.task)
        for agent in agent_in_assignment:
            assert agent in instance.concurrency.agent, f'Concurrency of {agent} is not specified.'
        for task in task_in_assignment:
            assert task in instance.concurrency.task, f'Concurrency of {task} is not specified.'

        def remove_unused(target: Union[DefinitionConfig, ConcurrencyConfig], warning_suffix: str):
            nonlocal agent_in_assignment, task_in_assignment
            removed_agents = set()
            removed_tasks = set()
            for definition_agent in target.agent.keys():
                if definition_agent not in agent_in_assignment:
                    removed_agents.add(definition_agent)
            for definition_task in target.task.keys():
                if definition_task not in task_in_assignment:
                    removed_tasks.add(definition_task)
            if len(removed_agents) > 0 or len(removed_tasks) > 0:
                print(ColorMessage.yellow(f'Warning: {len(removed_agents)} agent(s) and {len(removed_tasks)} task(s) are ' + warning_suffix), file=sys.stderr)
                print(ColorMessage.yellow(f'    Agent: {removed_agents}'))
                print(ColorMessage.yellow(f'    Task: {removed_tasks}'))
                for agent in removed_agents:
                    target.agent.pop(agent)
                for task in removed_tasks:
                    target.task.pop(task)
        if REMOVE_UNUSED_IN_DEFINITION:
            remove_unused(instance.definition, 'defined but not used, they will be ignored.')
        if REMOVE_UNUSED_IN_CONCURRENCY:
            remove_unused(instance.concurrency, 'specified in concurrency but not defined, they will be ignored.')
        assignments = set()
        for assignment in instance.assignments:
            target = (assignment.agent, assignment.task)
            if target in assignments:
                agent_ = json.dumps(target[0], ensure_ascii=False)
                task_ = json.dumps(target[1], ensure_ascii=False)
                print(ColorMessage.yellow(f'Warning: Assignment(agent={agent_}, task={task_}) is duplicated, only the first one will be kept.'))
            assignments.add(target)
        instance.assignments = []
        for agent, task in assignments:
            instance.assignments.append(Assignment(agent=agent, task=task))
        return instance

@classmethod
def post_validate(cls, instance: 'AssignmentConfig'):
    REMOVE_UNUSED_IN_DEFINITION = True
    REMOVE_UNUSED_IN_CONCURRENCY = True
    agent_in_assignment = set()
    task_in_assignment = set()
    for assignment in instance.assignments:
        assert assignment.agent in instance.definition.agent, f'Agent {assignment.agent} is not defined.'
        agent_in_assignment.add(assignment.agent)
        assert assignment.task in instance.definition.task, f'Task {assignment.task} is not defined.'
        task_in_assignment.add(assignment.task)
    for agent in agent_in_assignment:
        assert agent in instance.concurrency.agent, f'Concurrency of {agent} is not specified.'
    for task in task_in_assignment:
        assert task in instance.concurrency.task, f'Concurrency of {task} is not specified.'

    def remove_unused(target: Union[DefinitionConfig, ConcurrencyConfig], warning_suffix: str):
        nonlocal agent_in_assignment, task_in_assignment
        removed_agents = set()
        removed_tasks = set()
        for definition_agent in target.agent.keys():
            if definition_agent not in agent_in_assignment:
                removed_agents.add(definition_agent)
        for definition_task in target.task.keys():
            if definition_task not in task_in_assignment:
                removed_tasks.add(definition_task)
        if len(removed_agents) > 0 or len(removed_tasks) > 0:
            print(ColorMessage.yellow(f'Warning: {len(removed_agents)} agent(s) and {len(removed_tasks)} task(s) are ' + warning_suffix), file=sys.stderr)
            print(ColorMessage.yellow(f'    Agent: {removed_agents}'))
            print(ColorMessage.yellow(f'    Task: {removed_tasks}'))
            for agent in removed_agents:
                target.agent.pop(agent)
            for task in removed_tasks:
                target.task.pop(task)
    if REMOVE_UNUSED_IN_DEFINITION:
        remove_unused(instance.definition, 'defined but not used, they will be ignored.')
    if REMOVE_UNUSED_IN_CONCURRENCY:
        remove_unused(instance.concurrency, 'specified in concurrency but not defined, they will be ignored.')
    assignments = set()
    for assignment in instance.assignments:
        target = (assignment.agent, assignment.task)
        if target in assignments:
            agent_ = json.dumps(target[0], ensure_ascii=False)
            task_ = json.dumps(target[1], ensure_ascii=False)
            print(ColorMessage.yellow(f'Warning: Assignment(agent={agent_}, task={task_}) is duplicated, only the first one will be kept.'))
        assignments.add(target)
    instance.assignments = []
    for agent, task in assignments:
        instance.assignments.append(Assignment(agent=agent, task=task))
    return instance

