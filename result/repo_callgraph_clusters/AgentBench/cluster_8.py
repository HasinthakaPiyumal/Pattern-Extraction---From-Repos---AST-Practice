# Cluster 8

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

def deep_merge(base_item, new_item):
    if isinstance(base_item, dict) and isinstance(new_item, dict):
        ret = deepcopy(base_item)
        for key in new_item:
            if key in ret:
                ret[key] = deep_merge(ret[key], new_item[key])
            else:
                ret[key] = new_item[key]
        return ret
    if isinstance(base_item, list) and isinstance(new_item, list):
        ret = deepcopy(base_item)
        ret.extend(new_item)
        return ret
    return new_item

class ConfigLoader:

    def __init__(self) -> None:
        self.loading: Set[str] = set()
        self.loaded: Dict[str, Any] = dict()

    def load_from(self, path) -> Dict:
        path = os.path.realpath(path)
        if path in self.loading:
            raise Exception('Circular import detected: {}'.format(path))
        if path in self.loaded:
            return deepcopy(self.loaded[path])
        if not os.path.exists(path):
            raise Exception('File not found: {}'.format(path))
        if path.endswith('.yaml') or path.endswith('.yml'):
            with open(path) as f:
                config = yaml.safe_load(f)
        elif path.endswith('.json'):
            with open(path) as f:
                config = json.load(f)
        else:
            raise Exception('Unknown file type: {}'.format(path))
        self.loading.add(path)
        try:
            config = self.parse_imports(os.path.dirname(path), config)
        except Exception as e:
            self.loading.remove(path)
            raise e
        self.loading.remove(path)
        self.loaded[path] = config
        return self.parse_default_and_overwrite(deepcopy(config))

    def parse_imports(self, path, raw_config):
        raw_config = deepcopy(raw_config)
        if isinstance(raw_config, dict):
            ret = {}
            if 'import' in raw_config:
                v = raw_config.pop('import')
                if isinstance(v, str):
                    config = self.load_from(os.path.join(path, v))
                    ret = deep_merge(ret, config)
                elif isinstance(v, list):
                    for vv in v:
                        assert isinstance(vv, str), 'Import list must be a list of strings, found {}'.format(type(vv))
                        config = self.load_from(os.path.join(path, vv))
                        ret = deep_merge(ret, config)
                else:
                    raise Exception('Unknown import value: {}'.format(v))
            for k, v in raw_config.items():
                raw_config[k] = self.parse_imports(path, v)
            ret = deep_merge(ret, raw_config)
            return ret
        elif isinstance(raw_config, list):
            ret = []
            for v in raw_config:
                ret.append(self.parse_imports(path, v))
            return ret
        else:
            return raw_config

    def parse_default_and_overwrite(self, config):
        if isinstance(config, dict):
            if not config:
                return {}
            ret = {}
            overwriting = False
            defaulting = False
            if 'overwrite' in config:
                overwrite = self.parse_default_and_overwrite(config.pop('overwrite'))
                overwriting = True
            if 'default' in config:
                default = self.parse_default_and_overwrite(config.pop('default'))
                defaulting = True
            for k, v in config.items():
                parsed_v = self.parse_default_and_overwrite(v)
                if overwriting:
                    parsed_v = deep_merge(parsed_v, overwrite)
                if defaulting:
                    parsed_v = deep_merge(default, parsed_v)
                ret[k] = parsed_v
            return ret
        elif isinstance(config, list):
            ret = []
            for v in config:
                ret.append(self.parse_default_and_overwrite(v))
            return ret
        else:
            return config

def load_from(self, path) -> Dict:
    path = os.path.realpath(path)
    if path in self.loading:
        raise Exception('Circular import detected: {}'.format(path))
    if path in self.loaded:
        return deepcopy(self.loaded[path])
    if not os.path.exists(path):
        raise Exception('File not found: {}'.format(path))
    if path.endswith('.yaml') or path.endswith('.yml'):
        with open(path) as f:
            config = yaml.safe_load(f)
    elif path.endswith('.json'):
        with open(path) as f:
            config = json.load(f)
    else:
        raise Exception('Unknown file type: {}'.format(path))
    self.loading.add(path)
    try:
        config = self.parse_imports(os.path.dirname(path), config)
    except Exception as e:
        self.loading.remove(path)
        raise e
    self.loading.remove(path)
    self.loaded[path] = config
    return self.parse_default_and_overwrite(deepcopy(config))

def parse_imports(self, path, raw_config):
    raw_config = deepcopy(raw_config)
    if isinstance(raw_config, dict):
        ret = {}
        if 'import' in raw_config:
            v = raw_config.pop('import')
            if isinstance(v, str):
                config = self.load_from(os.path.join(path, v))
                ret = deep_merge(ret, config)
            elif isinstance(v, list):
                for vv in v:
                    assert isinstance(vv, str), 'Import list must be a list of strings, found {}'.format(type(vv))
                    config = self.load_from(os.path.join(path, vv))
                    ret = deep_merge(ret, config)
            else:
                raise Exception('Unknown import value: {}'.format(v))
        for k, v in raw_config.items():
            raw_config[k] = self.parse_imports(path, v)
        ret = deep_merge(ret, raw_config)
        return ret
    elif isinstance(raw_config, list):
        ret = []
        for v in raw_config:
            ret.append(self.parse_imports(path, v))
        return ret
    else:
        return raw_config

def parse_default_and_overwrite(self, config):
    if isinstance(config, dict):
        if not config:
            return {}
        ret = {}
        overwriting = False
        defaulting = False
        if 'overwrite' in config:
            overwrite = self.parse_default_and_overwrite(config.pop('overwrite'))
            overwriting = True
        if 'default' in config:
            default = self.parse_default_and_overwrite(config.pop('default'))
            defaulting = True
        for k, v in config.items():
            parsed_v = self.parse_default_and_overwrite(v)
            if overwriting:
                parsed_v = deep_merge(parsed_v, overwrite)
            if defaulting:
                parsed_v = deep_merge(default, parsed_v)
            ret[k] = parsed_v
        return ret
    elif isinstance(config, list):
        ret = []
        for v in config:
            ret.append(self.parse_default_and_overwrite(v))
        return ret
    else:
        return config

def lisp_to_nested_expression(lisp_string: str) -> List:
    """
    Takes a logical form as a lisp string and returns a nested list representation of the lisp.
    For example, "(count (division first))" would get mapped to ['count', ['division', 'first']].
    """
    stack: List = []
    current_expression: List = []
    tokens = lisp_string.split()
    for token in tokens:
        while token[0] == '(':
            nested_expression: List = []
            current_expression.append(nested_expression)
            stack.append(current_expression)
            current_expression = nested_expression
            token = token[1:]
        current_expression.append(token.replace(')', ''))
        while token[-1] == ')':
            current_expression = stack.pop()
            token = token[:-1]
    return current_expression[0]

def node_match(n1, n2):
    if n1['id'] == n2['id'] and n1['type'] == n2['type']:
        func1 = n1.pop('function', 'none')
        func2 = n2.pop('function', 'none')
        tc1 = n1.pop('tc', 'none')
        tc2 = n2.pop('tc', 'none')
        if func1 == func2 and tc1 == tc2:
            return True
        else:
            return False
    else:
        return False

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

def get_prompt(self, filename: str):
    for k, v in self.prefixes.items():
        if filename.startswith(k):
            example = self.prompts[v]
            return deepcopy(example)
    raise Exception(f'unsupported name: {filename}')

class Graph:

    def __init__(self, node_count: int, edges: Dict[Tuple[int, int], int]):
        """
        edges: {(source, target): edge_weight}}
        """
        self.node_count = node_count
        self.edges = edges

    def iterate_edges(self) -> Iterable[Tuple[int, int, int]]:
        for (source, target), weight in self.edges.items():
            yield (source, target, weight)

def iterate_edges(self) -> Iterable[Tuple[int, int, int]]:
    for (source, target), weight in self.edges.items():
        yield (source, target, weight)

class MaxFlow:

    def __init__(self, graph: Graph, src: int, dst: int) -> None:
        assert graph.node_count > src >= 0, 'src node out of range, expected [0, {}), got {}'.format(graph.node_count, src)
        assert graph.node_count > dst >= 0, 'dst node out of range, expected [0, {}), got {}'.format(graph.node_count, dst)
        self.src = src
        self.dst = dst
        self.graph = graph
        self.adjacent_edges: List[List[Edge]] = [[] for _ in range(graph.node_count)]
        self.edges_dict: Dict[Tuple[int, int], Edge] = {}
        for source, target, weight in self.graph.iterate_edges():
            if (source, target) in self.edges_dict:
                self.edges_dict[source, target].capacity += weight
            else:
                self.edges_dict[source, target] = Edge(from_node=source, to_node=target, capacity=weight)
                self.edges_dict[target, source] = Edge(from_node=target, to_node=source, capacity=0)
                self.adjacent_edges[source].append(self.edges_dict[source, target])
                self.adjacent_edges[target].append(self.edges_dict[target, source])
        self.max_flow = self.compute_max_flow()

    def compute_max_flow(self) -> int:
        max_flow = 0
        while True:
            augmenting_path = self.find_augmenting_path()
            if not augmenting_path:
                break
            bottleneck = min([edge.capacity - edge.flow for edge in augmenting_path])
            for edge in augmenting_path:
                edge.flow += bottleneck
                self.edges_dict[edge.to_node, edge.from_node].flow -= bottleneck
            max_flow += bottleneck
        return max_flow

    def find_augmenting_path(self) -> Optional[List[Edge]]:
        visited = [False] * self.graph.node_count
        visited[self.src] = True
        queue = [self.src]
        prev: List[Union[None, Edge]] = [None] * self.graph.node_count
        while queue:
            node = queue.pop(0)
            for edge in self.adjacent_edges[node]:
                if not visited[edge.to_node] and edge.capacity > edge.flow:
                    visited[edge.to_node] = True
                    prev[edge.to_node] = edge
                    queue.append(edge.to_node)
                    if edge.to_node == self.dst:
                        break
        if not visited[self.dst]:
            return None
        flow_path = []
        node = self.dst
        while prev[node]:
            flow_path.append(prev[node])
            node = prev[node].from_node
        flow_path.reverse()
        return flow_path

def __init__(self, graph: Graph, src: int, dst: int) -> None:
    assert graph.node_count > src >= 0, 'src node out of range, expected [0, {}), got {}'.format(graph.node_count, src)
    assert graph.node_count > dst >= 0, 'dst node out of range, expected [0, {}), got {}'.format(graph.node_count, dst)
    self.src = src
    self.dst = dst
    self.graph = graph
    self.adjacent_edges: List[List[Edge]] = [[] for _ in range(graph.node_count)]
    self.edges_dict: Dict[Tuple[int, int], Edge] = {}
    for source, target, weight in self.graph.iterate_edges():
        if (source, target) in self.edges_dict:
            self.edges_dict[source, target].capacity += weight
        else:
            self.edges_dict[source, target] = Edge(from_node=source, to_node=target, capacity=weight)
            self.edges_dict[target, source] = Edge(from_node=target, to_node=source, capacity=0)
            self.adjacent_edges[source].append(self.edges_dict[source, target])
            self.adjacent_edges[target].append(self.edges_dict[target, source])
    self.max_flow = self.compute_max_flow()

def find_augmenting_path(self) -> Optional[List[Edge]]:
    visited = [False] * self.graph.node_count
    visited[self.src] = True
    queue = [self.src]
    prev: List[Union[None, Edge]] = [None] * self.graph.node_count
    while queue:
        node = queue.pop(0)
        for edge in self.adjacent_edges[node]:
            if not visited[edge.to_node] and edge.capacity > edge.flow:
                visited[edge.to_node] = True
                prev[edge.to_node] = edge
                queue.append(edge.to_node)
                if edge.to_node == self.dst:
                    break
    if not visited[self.dst]:
        return None
    flow_path = []
    node = self.dst
    while prev[node]:
        flow_path.append(prev[node])
        node = prev[node].from_node
    flow_path.reverse()
    return flow_path

class TaskClient:

    def __init__(self, name: str, controller_address: str='http://localhost:5000/api', *_, **__) -> None:
        self.name = name
        self.controller_address = controller_address
        print('TaskClient created: {} ({})'.format(name, controller_address))

    def get_indices(self) -> List[SampleIndex]:
        result = requests.get(self.controller_address + '/get_indices', params={'name': self.name})
        if result.status_code != 200:
            raise AgentBenchException(result.text, result.status_code, self.name)
        return result.json()

    def get_concurrency(self) -> int:
        try:
            result = requests.get(self.controller_address + '/list_workers')
        except Exception as e:
            print(ColorMessage.yellow(f'Warning task {self.name} cannot connect to controller {e}'))
            return 0
        if result.status_code != 200:
            raise AgentBenchException(result.text, result.status_code, self.name)
        result = result.json()
        if self.name not in result:
            print(ColorMessage.yellow(f'task {self.name} not found in worker list'))
            return 0
        concurrency = 0
        for worker in result[self.name]['workers'].values():
            if worker['status'] == WorkerStatus.ALIVE:
                concurrency += worker['capacity'] - worker['current']
        return concurrency

    def run_sample(self, index: SampleIndex, agent: AgentClient) -> TaskClientOutput:
        try:
            result = requests.post(self.controller_address + '/start_sample', json=StartSampleRequest(name=self.name, index=index).dict())
        except Exception as e:
            return TaskClientOutput(error=TaskError.NETWORK_ERROR.value, info=str(e))
        if result.status_code == 406:
            return TaskClientOutput(error=TaskError.NOT_AVAILABLE.value, info=result.text)
        if result.status_code != 200:
            return TaskClientOutput(error=TaskError.START_FAILED.value, info=result.text)
        result = result.json()
        sid = result['session_id']
        latest_result = result
        while SampleStatus(result['output']['status']) == SampleStatus.RUNNING:
            try:
                content = agent.inference(result['output']['history'])
                response = AgentOutput(content=content)
            except AgentContextLimitException:
                response = AgentOutput(status=AgentOutputStatus.AGENT_CONTEXT_LIMIT)
            except Exception as e:
                if hasattr(agent, 'model_name'):
                    model_name = agent.model_name
                elif hasattr(agent, 'name'):
                    model_name = agent.name
                else:
                    model_name = agent.__class__.__name__
                print(f'ERROR: {model_name}/{self.name} agent error', e)
                requests.post(self.controller_address + '/cancel', json=CancelRequest(session_id=sid).dict())
                return TaskClientOutput(error=TaskError.AGENT_FAILED.value, info=str(e), output=latest_result)
            try:
                result = requests.post(self.controller_address + '/interact', json=InteractRequest(session_id=sid, agent_response=response).dict())
            except Exception as e:
                return TaskClientOutput(error=TaskError.NETWORK_ERROR.value, info=str(e), output=latest_result)
            if result.status_code != 200:
                requests.post(self.controller_address + '/cancel', json=CancelRequest(session_id=sid).dict())
                return TaskClientOutput(error=TaskError.INTERACT_FAILED.value, info=result.text, output=latest_result)
            result = result.json()
            latest_result = result
        return TaskClientOutput(output=result['output'])

    def calculate_overall(self, results: List[TaskOutput]) -> JSONSerializable:
        statistics = {s: 0 for s in SampleStatus}
        for result in results:
            statistics[SampleStatus(result.status)] += 1
        for s in SampleStatus:
            statistics[s] /= len(results)
        statistics['average_history_length'] = sum([len(result.history) for result in results]) / len(results)
        statistics['max_history_length'] = max([len(result.history) for result in results])
        statistics['min_history_length'] = min([len(result.history) for result in results])
        ret = {'total': len(results), 'validation': statistics}
        res = requests.post(self.controller_address + '/calculate_overall', json=CalculateOverallRequest(name=self.name, results=results).dict())
        if res.status_code != 200:
            raise TaskNetworkException(res.text)
        ret['custom'] = res.json()
        return ret

def __init__(self, name: str, controller_address: str='http://localhost:5000/api', *_, **__) -> None:
    self.name = name
    self.controller_address = controller_address
    print('TaskClient created: {} ({})'.format(name, controller_address))

class Prompter:

    @staticmethod
    def get_prompter(prompter: Union[Dict[str, Any], None]):
        if not prompter:
            return Prompter.default()
        assert isinstance(prompter, dict)
        prompter_name = prompter.get('name', None)
        prompter_args = prompter.get('args', {})
        if hasattr(Prompter, prompter_name) and callable(getattr(Prompter, prompter_name)):
            return getattr(Prompter, prompter_name)(**prompter_args)
        return Prompter.default()

    @staticmethod
    def default():
        return Prompter.role_content_dict()

    @staticmethod
    def batched_role_content_dict(*args, **kwargs):
        base = Prompter.role_content_dict(*args, **kwargs)

        def batched(messages):
            result = base(messages)
            return {key: [result[key]] for key in result}
        return batched

    @staticmethod
    def role_content_dict(message_key: str='messages', role_key: str='role', content_key: str='content', user_role: str='user', agent_role: str='agent'):

        def prompter(messages: List[Dict[str, str]]):
            nonlocal message_key, role_key, content_key, user_role, agent_role
            role_dict = {'user': user_role, 'agent': agent_role}
            prompt = []
            for item in messages:
                prompt.append({role_key: role_dict[item['role']], content_key: item['content']})
            return {message_key: prompt}
        return prompter

    @staticmethod
    def prompt_string(prefix: str='', suffix: str='AGENT:', user_format: str='USER: {content}\n\n', agent_format: str='AGENT: {content}\n\n', prompt_key: str='prompt'):

        def prompter(messages: List[Dict[str, str]]):
            nonlocal prefix, suffix, user_format, agent_format, prompt_key
            prompt = prefix
            for item in messages:
                if item['role'] == 'user':
                    prompt += user_format.format(content=item['content'])
                else:
                    prompt += agent_format.format(content=item['content'])
            prompt += suffix
            print(prompt)
            return {prompt_key: prompt}
        return prompter

    @staticmethod
    def claude():
        return Prompter.prompt_string(prefix='', suffix='Assistant:', user_format='Human: {content}\n\n', agent_format='Assistant: {content}\n\n')

    @staticmethod
    def palm():

        def prompter(messages):
            return {'instances': [Prompter.role_content_dict('messages', 'author', 'content', 'user', 'bot')(messages)]}
        return prompter

@staticmethod
def default():
    return Prompter.role_content_dict()

@staticmethod
def batched_role_content_dict(*args, **kwargs):
    base = Prompter.role_content_dict(*args, **kwargs)

    def batched(messages):
        result = base(messages)
        return {key: [result[key]] for key in result}
    return batched

def prompter(messages):
    return {'instances': [Prompter.role_content_dict('messages', 'author', 'content', 'user', 'bot')(messages)]}

class Prompter:

    @staticmethod
    def get_prompter(prompter: Union[str, None, Dict[str, Any]]):
        name = None
        args = {}
        if isinstance(prompter, str):
            name = prompter
        elif isinstance(prompter, dict):
            name = prompter['name']
            args = prompter['args']
        if not name:
            return None
        if hasattr(Prompter, name) and callable(getattr(Prompter, name)):
            return getattr(Prompter, name)(**args)

    @staticmethod
    def claude():

        def _prompter(messages: List[Dict[str, str]]):
            prompt = ''
            role_dict = {'user': 'Human', 'agent': 'Assistant'}
            for item in messages:
                prompt += f'{role_dict[item['role']]}: {item['content']}\n\n'
            prompt += 'Assistant:'
            return {'prompt': prompt}
        return _prompter

    @staticmethod
    def openchat_v3_1():

        def _prompter(messages: List[Dict[str, str]]):
            prompt = 'Assistant is GPT4<|end_of_turn|>'
            role_dict = {'user': 'User: {content}<|end_of_turn|>', 'agent': 'Assistant: {content}<|end_of_turn|>'}
            for item in messages:
                prompt += role_dict[item['role']].format(content=item['content'])
            prompt += 'Assistant:'
            return {'prompt': prompt}
        return _prompter

    @staticmethod
    def openchat_v3_2():

        def _prompter(messages: List[Dict[str, str]]):
            prompt = ''
            role_dict = {'user': 'GPT4 User: {content}<|end_of_turn|>\n', 'agent': 'GPT4 Assistant: {content}<|end_of_turn|>\n'}
            for item in messages:
                prompt += role_dict[item['role']].format(content=item['content'])
            prompt += 'GPT4 Assistant:'
            return {'prompt': prompt}
        return _prompter

    @staticmethod
    def prompt_string(prefix: str='', suffix: str='AGENT:', user_format: str='USER: {content}\n\n', agent_format: str='AGENT: {content}\n\n', prompt_key: str='prompt'):

        def prompter(messages: List[Dict[str, str]]):
            nonlocal prefix, suffix, user_format, agent_format, prompt_key
            prompt = prefix
            for item in messages:
                if item['role'] == 'user':
                    prompt += user_format.format(content=item['content'])
                else:
                    prompt += agent_format.format(content=item['content'])
            prompt += suffix
            return {prompt_key: prompt}
        return prompter

def _prompter(messages: List[Dict[str, str]]):
    prompt = ''
    role_dict = {'user': 'GPT4 User: {content}<|end_of_turn|>\n', 'agent': 'GPT4 Assistant: {content}<|end_of_turn|>\n'}
    for item in messages:
        prompt += role_dict[item['role']].format(content=item['content'])
    prompt += 'GPT4 Assistant:'
    return {'prompt': prompt}

def prompter(messages: List[Dict[str, str]]):
    nonlocal prefix, suffix, user_format, agent_format, prompt_key
    prompt = prefix
    for item in messages:
        if item['role'] == 'user':
            prompt += user_format.format(content=item['content'])
        else:
            prompt += agent_format.format(content=item['content'])
    prompt += suffix
    return {prompt_key: prompt}

class CountHistoryAgent(AgentClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inference(self, history: List[dict]) -> str:
        return 'I received {} items in history.'.format(len(history))

def inference(self, history: List[dict]) -> str:
    return 'I received {} items in history.'.format(len(history))

class InstanceFactory(BaseModel):
    module: str
    parameters: Dict[str, Any] = {}

    @validator('parameters', pre=True)
    def _ensure_dict(cls, v):
        if v is None:
            return {}
        return v

    def create(self):
        splits = self.module.split('.')
        if len(splits) == 0:
            raise Exception('Invalid module name: {}'.format(self.module))
        if len(splits) == 1:
            g = globals()
            if self.module in g:
                class_type = g[self.module]
            else:
                class_type = getattr(builtins, self.module)
            return class_type(**self.parameters)
        else:
            path = '.'.join(self.module.split('.')[:-1])
            mod = __import__(path, fromlist=[self.module.split('.')[-1]])
            return getattr(mod, self.module.split('.')[-1])(**self.parameters)

def create(self):
    splits = self.module.split('.')
    if len(splits) == 0:
        raise Exception('Invalid module name: {}'.format(self.module))
    if len(splits) == 1:
        g = globals()
        if self.module in g:
            class_type = g[self.module]
        else:
            class_type = getattr(builtins, self.module)
        return class_type(**self.parameters)
    else:
        path = '.'.join(self.module.split('.')[:-1])
        mod = __import__(path, fromlist=[self.module.split('.')[-1]])
        return getattr(mod, self.module.split('.')[-1])(**self.parameters)

class ClientException(AgentBenchException):

    def __init__(self, reason: str, detail: Union[str, None]=None) -> None:
        super().__init__()
        self.reason = reason
        self.detail = detail

    def __str__(self) -> str:
        if not self.detail:
            return '{CLASS_NAME}[{REASON}]'.format(CLASS_NAME=self.__class__.__name__, REASON=self.reason)
        else:
            return '{CLASS_NAME}[{REASON}]: {DETAIL}'.format(CLASS_NAME=self.__class__.__name__, REASON=self.reason, DETAIL=self.detail)

def __str__(self) -> str:
    if not self.detail:
        return '{CLASS_NAME}[{REASON}]'.format(CLASS_NAME=self.__class__.__name__, REASON=self.reason)
    else:
        return '{CLASS_NAME}[{REASON}]: {DETAIL}'.format(CLASS_NAME=self.__class__.__name__, REASON=self.reason, DETAIL=self.detail)

