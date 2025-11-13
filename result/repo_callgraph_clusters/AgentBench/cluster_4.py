# Cluster 4

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

def __init__(self) -> None:
    self.loading: Set[str] = set()
    self.loaded: Dict[str, Any] = dict()

class OSInteraction(Task):

    def __init__(self, data_config, docker_config, round_limit=8, tools=None, env_driver: str='docker', env_options: Optional[dict]=None, **kwargs):
        super().__init__(**kwargs)
        self.round_limit: int = round_limit
        self.data_config = data_config
        self.docker_config = docker_config
        self.tools = tools
        self.full_async = True
        self.problem_configs: Dict[str, Dict[str, Any]] = {}
        matches = []
        for item in self.data_config['files']:
            path = item['problem_file']
            for file in glob.glob(path):
                if file.endswith('.json') or file.endswith('.jsonl'):
                    matches.append({'problem_file': file, 'script_dir': item['script_dir'], 'index_prefix': item['index_prefix'] + os.path.basename(file).removesuffix('.json').removesuffix('.jsonl') + '-'})
        self.data_config['files'] = matches
        next_idx = 0
        for item in self.data_config['files']:
            problem_file = item['problem_file']
            single_file_configs = self._load_configs(problem_file, item['script_dir'])
            dict_configs = {}
            for config in single_file_configs:
                dict_configs[next_idx] = {'file': problem_file, 'config': config, 'index': next_idx}
                next_idx += 1
            self.problem_configs.update(dict_configs)
        logging.info(f'Initialized OSInteraction with {len(self.problem_configs)} problem configs')
        self.env_delegation = OSEnvironmentDelegation(self.docker_config['localhost'])
        self.env_controller = create_controller(env_driver, self.env_delegation, **env_options)
        self.env_controller_background_task = None

    def _load_configs(self, config_path, script_root_dir='.') -> List[JudgeConfig]:

        def load_script(script_obj):
            if script_obj is None:
                return None
            if type(script_obj) is str:
                return ('bash', script_obj)
            if 'language' not in script_obj:
                language = 'bash'
            else:
                language = script_obj['language']
            if 'file' in script_obj:
                with open(os.path.join(script_root_dir, script_obj['file']), encoding='utf-8') as f:
                    return (language, f.read())
            elif 'code' in script_obj:
                return (language, script_obj['code'])
            else:
                raise ValueError('Invalid Script Object')
        logging.info(f'Loading config from: {config_path}')
        if config_path.endswith('.json'):
            with open(config_path, encoding='utf-8') as f:
                config_raw = json.load(f)
            if isinstance(config_raw, list):
                pass
            elif isinstance(config_raw, dict):
                config_raw = [config_raw]
            else:
                raise ValueError('Invalid Config File')
        elif config_path.endswith('.jsonl'):
            with open(config_path, encoding='utf-8') as f:
                config_raw = [json.loads(line) for line in f.readlines()]
        else:
            raise ValueError('Invalid Config File')
        configs: list[JudgeConfig] = []
        for item in config_raw:
            config = JudgeConfig()
            config.description = item['description']
            if 'create' in item:
                config.image = item['create']['local'] if 'local' in item['create'] else 'default'
                if 'init' in item['create']:
                    if type(item['create']['init']) is not list:
                        config.init_script = [load_script(item['create']['init'])]
                    else:
                        config.init_script = [load_script(script_obj) for script_obj in item['create']['init']]
                else:
                    config.init_script = []
            else:
                config.image = 'default'
            if 'start' in item:
                config.start = load_script(item['start'])
            evaluation = item['evaluation']
            if 'match' in evaluation:
                if type(evaluation['match']) is str:
                    config.match = {'answer': evaluation['match'], 'strip': True}
                else:
                    config.match = evaluation['match']
            elif 'check' in evaluation:
                if type(evaluation['check']) is not list:
                    config.check = [load_script(evaluation['check'])]
                else:
                    config.check = [load_script(script_obj) for script_obj in evaluation['check']]
            else:
                raise ValueError('check or match must exist.')
            if 'check' in evaluation and 'example' in evaluation:
                config.example_script = load_script(evaluation['example'])
            configs.append(config)
        logging.info(f'Loaded {len(configs)} configuration(s) from {config_path}')
        return configs

    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        overall = {'total': len([config for config in results if config]), 'pass': len([config for config in results if config and config.result and config.result.get('result', False)])}
        overall['wrong'] = overall['total'] - overall['pass']
        overall['acc'] = overall['pass'] / overall['total'] if overall['total'] else 0
        return {'overall': overall}

    def get_indices(self) -> List[Any]:
        return list(self.problem_configs.keys())

    @staticmethod
    def _extract_action(raw: str):
        think_pattern = 'Think:\\s*(.+)'
        act_pattern = 'Act:\\s*(.+)'
        think = re.findall(think_pattern, raw)
        act = re.findall(act_pattern, raw)
        ret = {'thought': '\n'.join(think), 'action': None, 'content': None}
        for action in act[::-1]:
            if action.lower().startswith('bash'):
                ret['action'] = 'bash'
                break
            if action.lower().startswith('finish'):
                ret['action'] = 'commit'
                break
            if action.lower().startswith('answer'):
                content = action[6:].strip()
                left_par_pos = content.find('(')
                right_par_pos = content.rfind(')')
                if left_par_pos == -1 or right_par_pos == -1:
                    continue
                content = content[left_par_pos + 1:right_par_pos]
                ret['action'] = 'commit'
                ret['content'] = content
                break
        if ret['action'] == 'bash':
            content_pattern = '```bash\\n(.*?)\\n```'
            content = re.findall(content_pattern, raw, re.DOTALL)
            content = '\n\n'.join(content)
            ret['content'] = content
        return ret

    @staticmethod
    def _extract_function(func_name: str, arguments: List, thought: str):
        ret = {'thought': thought, 'action': None, 'content': None}
        if func_name == 'bash_action':
            ret['action'] = 'bash'
            ret['content'] = arguments[0]
        if func_name == 'finish_action':
            ret['action'] = 'commit'
            ret['content'] = arguments[0] if arguments else None
        if func_name == 'answer_action':
            ret['action'] = 'commit'
            ret['content'] = arguments[0]
        return ret

    async def start_sample(self, index, session: Session) -> TaskSampleExecutionResult:
        if not self.env_controller_background_task:
            self.env_controller_background_task = asyncio.create_task(self.env_controller.background_task())
            weakref.finalize(self, self.env_controller_background_task.cancel)
        logging.info(f'Starting sample with index: {index}')
        data_item = self.problem_configs[index]
        config = data_item['config']
        file = data_item['file']
        index_in_file = data_item['index']
        container = Container(self.env_controller, config.image)
        try:
            logging.info('Initializing container')
            await container.initialize()
            logging.info('Container initialized successfully')
            logging.info('Starting judge process')
            result = await self._judge(session, config, container)
            result.result['file'] = file
            result.result['index_in_file'] = index_in_file
            logging.info(f'Judge process completed with status: {result.status}')
            return result
        except AgentCancelledException:
            session.inject(RewardHistoryItem(reward=0, score=0))
            return TaskSampleExecutionResult(status=SampleStatus.CANCELLED)
        except:
            logging.exception(f'Error in start_sample')
            session.inject(RewardHistoryItem(reward=0, score=0))
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR, result={'result': False, 'error': traceback.format_exc()})
        finally:
            try:
                await container.cleanup()
            except Exception as e:
                logging.error(f'Error during container cleanup: {str(e)}')

    async def _judge(self, session: Session, config: JudgeConfig, container: Container) -> TaskSampleExecutionResult:
        """执行任务判断的主要逻辑"""
        logging.info('Starting execution')
        setup_result = await self._setup_execution_environment(config, container)
        if setup_result:
            return setup_result
        self._inject_initial_messages(session, config.description)
        finish = False
        function_name = None
        call_id = None
        for round_num in range(self.round_limit):
            logging.info(f'Starting round {round_num + 1}/{self.round_limit}')
            round_reward = 0
            action_result = await self._handle_agent_action(session, container, round_num, finish, round_reward, function_name, call_id)
            function_name = action_result.get('function_name', function_name)
            call_id = action_result.get('id', call_id)
            finish = action_result.get('finish', finish)
            if action_result.get('early_return'):
                return action_result.get('result')
            if 'answer' in action_result:
                answer = action_result['answer']
                break
        else:
            logging.warning('Task round limit reached')
            final_rewardhistory = RewardHistoryItem(reward=0, score=0)
            session.inject(final_rewardhistory)
            return TaskSampleExecutionResult(status=SampleStatus.TASK_LIMIT_REACHED, result={'result': False, 'reason': 'round limit'})
        evaluation_result = await self._evaluate_answer(answer, config, container, session)
        if evaluation_result.get('error'):
            return evaluation_result.get('result')
        jd = evaluation_result.get('success', False)
        os_score = 1 if jd else 0
        final_reward = 1 if jd else 0
        logging.info(f'Task completed {('successfully' if jd else 'unsuccessfully')}')
        final_rewardhistory = RewardHistoryItem(reward=final_reward, score=os_score)
        session.inject(final_rewardhistory)
        return TaskSampleExecutionResult(status=SampleStatus.COMPLETED, result={'result': jd})

    async def _setup_execution_environment(self, config: JudgeConfig, container: Container) -> Optional[TaskSampleExecutionResult]:
        """设置执行环境，运行初始化和启动脚本"""
        if config.init_script:
            for i, script in enumerate(config.init_script):
                logging.info(f'Running init script {i + 1}/{len(config.init_script)}')
                exit_code, _, stderr = await container.execute_independent(script)
                if exit_code != 0:
                    logging.error(f'Init script failed with exit code: {exit_code}')
                    return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN, result={'result': False, 'error': f'Init script {script} failed: {stderr}'})
        if config.start:
            logging.info('Running start script')
            try:
                start = await container.execute(config.start[1])
                if start.exit_code != 0:
                    logging.error(f'Start script failed with exit code: {start.exit_code}')
                    return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN, result={'result': False, 'error': f'Start script {config.start} failed: {start}'})
            except Exception as e:
                logging.error(f'Error in start script: {str(e)}')
                return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN, result={'result': False, 'error': f'Error in start script: {str(e)}'})
        logging.info('Execution setup completed successfully')
        return None

    def _inject_initial_messages(self, session: Session, description: str) -> None:
        """注入系统消息和问题描述"""
        system_message = 'You are an assistant that will act like a person. I will play the role of a Linux (Ubuntu) operating system.\nYour goal is to implement the operations required by me or answer the questions proposed by me.\nFor each of your turns, you should first think about what you should do, and then call exactly one of the provided tools according to the situation.\nIf you think the output is too long, I will truncate it. The truncated output is not complete. You have to deal with the truncating problem by yourself.\nAttention, your bash code should not contain any input operation. Once again, you should use one tool in each turn, and should not respond without function calling.\nNote that if you think the task has been finished, or there is some message missing to completely complete the task, you should respond with calling the function "finish_action", as no additional information will be provided.\nAlso, note that if you have gotten the answer to the question, you should call the "answer_action" tool instead of simply writing your answer in your response.\nYour answers should be exact and precise (for example, a single number), do not answer with full sentences or phrases.\nAlways use a tool provided instead of simply responding with content.'
        session.inject(ChatCompletionSystemMessageParam(role='system', content=system_message))
        session.inject(ChatCompletionUserMessageParam(role='user', content=f'Now, I will start a new problem in a new OS. My problem is:\n\n{description}'))

    async def _handle_agent_action(self, session: Session, container: Container, round_num: int, finish: bool, round_reward: float, function_name: Optional[str], call_id: Optional[str]) -> dict:
        response = await session.action()
        result = {'finish': finish, 'round_reward': round_reward, 'function_name': function_name, 'id': call_id}
        response_content = None
        tool_calls = []
        for message in response.messages:
            if not response_content:
                response_content = message.get('content')
            tool_calls.extend(message.get('tool_calls', []) or [])
        if len(tool_calls) == 0:
            logging.warning('Empty tool calls array')
            session.inject(ChatCompletionUserMessageParam(role='user', content='No executable tool calls found. Please call a tool instead'))
            round_rewardhistory = RewardHistoryItem(reward=round_reward, score=0)
            session.inject(round_rewardhistory)
            return result
        tool_call = tool_calls[0]
        function_name = tool_call['function']['name']
        logging.info(f'Processing tool call: {function_name}')
        result['function_name'] = function_name
        try:
            arguments = tool_call['function']['arguments']
            arguments = json.loads(arguments)
            if not response_content and 'thought' in arguments:
                response_content = arguments['thought']
            arguments = list(arguments.values())
        except Exception as e:
            logging.error(f'Error parsing arguments: {str(e)}')
            call_id = tool_call.get('id')
            result['id'] = call_id
            session.inject(ChatCompletionToolMessageParam(role='tool', content=str(e), tool_call_id=call_id))
            round_rewardhistory = RewardHistoryItem(reward=round_reward, score=0)
            session.inject(round_rewardhistory)
            return result
        call_id = tool_call['id']
        result['id'] = call_id
        action_data = self._extract_function(function_name, arguments, response_content)
        if 'action' not in action_data:
            logging.warning('Invalid action in function extraction')
            session.inject(ChatCompletionToolMessageParam(role='tool', content='Invalid function call. Please call a tool instead', tool_call_id=call_id))
            round_rewardhistory = RewardHistoryItem(reward=round_reward, score=0)
            session.inject(round_rewardhistory)
            return result
        if action_data['action'] not in ['bash', 'commit']:
            logging.warning(f'Unsupported action: {action_data['action']}')
            session.inject(ChatCompletionToolMessageParam(role='tool', content='Invalid function call. Please call a tool instead', tool_call_id=call_id))
            round_rewardhistory = RewardHistoryItem(reward=round_reward, score=0)
            session.inject(round_rewardhistory)
            return result
        action = action_data['action']
        content = action_data['content']
        if action == 'commit':
            logging.info('Received commit action with answer')
            result['answer'] = content
            result['finish'] = True
        elif action == 'bash':
            await self._execute_bash_command(session, container, content, call_id)
        round_rewardhistory = RewardHistoryItem(reward=round_reward, score=0)
        session.inject(round_rewardhistory)
        return result

    async def _execute_bash_command(self, session: Session, container: Container, command: str, id: str) -> None:
        """执行bash命令并处理结果"""
        logging.info('Executing bash command')
        result = await container.execute(command)
        try:
            result_text = result.output.decode('utf-8')
        except Exception as e:
            logging.error(f'Error decoding output: {str(e)}')
            result_text = 'OS Environment output cannot be decoded as UTF-8'
        if len(result_text) > 800:
            logging.debug('Output truncated due to length')
            result_text = result_text[:780] + '\n[truncated because the output is too long]'
        session.inject(ChatCompletionToolMessageParam(role='tool', content=f'The output of the OS:\n\n{result_text}' if result_text else 'The output of the OS is empty.', tool_call_id=id))

    async def _evaluate_answer(self, answer, config: JudgeConfig, container: Container, session: Session) -> dict:
        """评估答案"""
        result = {'success': False}
        if isinstance(answer, str) and config.match and config.match['strip']:
            answer = answer.strip()
        logging.info(f'Final answer: {answer}')
        if config.match:
            result['success'] = self._evaluate_by_match(answer, config)
        elif config.check:
            result['success'] = await self._evaluate_by_check_scripts(answer, config, container)
        else:
            logging.error('No evaluation method specified')
            final_rewardhistory = RewardHistoryItem(reward=0, score=0)
            session.inject(final_rewardhistory)
            result['error'] = True
            result['result'] = TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR, result={'result': False})
        return result

    def _evaluate_by_match(self, answer: str, config: JudgeConfig) -> bool:
        """使用匹配标准评估答案"""
        logging.info('Evaluating answer with match criteria')
        if 'answer' in config.match:
            success = answer == config.match['answer']
        elif 'regex' in config.match:
            success = re.search(config.match['regex'], answer) is not None
        else:
            success = False
        logging.info(f'Match evaluation result: {success}')
        return success

    async def _evaluate_by_check_scripts(self, answer: str, config: JudgeConfig, container: Container) -> bool:
        """使用检查脚本评估答案"""
        logging.info('Evaluating answer with check scripts')
        params = [str(answer)]
        for script_index, script in enumerate(config.check):
            if script is None:
                script = config.example_script
            logging.info(f'Running check script {script_index + 1}/{len(config.check)}')
            exit_code, stdout, _ = await container.execute_independent(script, *params)
            logging.info(f'Check script output: {stdout.decode('utf-8')}')
            if exit_code != 0:
                logging.warning(f'Check script failed with exit code: {exit_code}')
                return False
            params.append(stdout.decode('utf-8'))
        logging.info('Check evaluation result: True')
        return True

def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
    overall = {'total': len([config for config in results if config]), 'pass': len([config for config in results if config and config.result and config.result.get('result', False)])}
    overall['wrong'] = overall['total'] - overall['pass']
    overall['acc'] = overall['pass'] / overall['total'] if overall['total'] else 0
    return {'overall': overall}

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

class HTTPAgent(AgentClient):

    def __init__(self, url, proxies=None, body=None, headers=None, return_format='{response}', prompter=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.url = url
        self.proxies = proxies or {}
        self.headers = headers or {}
        self.body = body or {}
        self.return_format = return_format
        self.prompter = Prompter.get_prompter(prompter)
        if not self.url:
            raise Exception("Please set 'url' parameter")

    def _handle_history(self, history: List[dict]) -> Dict[str, Any]:
        return self.prompter(history)

    def inference(self, history: List[dict]) -> str:
        for _ in range(3):
            try:
                body = self.body.copy()
                body.update(self._handle_history(history))
                with no_ssl_verification():
                    resp = requests.post(self.url, json=body, headers=self.headers, proxies=self.proxies, timeout=120)
                if resp.status_code != 200:
                    if check_context_limit(resp.text):
                        raise AgentContextLimitException(resp.text)
                    else:
                        raise Exception(f'Invalid status code {resp.status_code}:\n\n{resp.text}')
            except AgentClientException as e:
                raise e
            except Exception as e:
                print('Warning: ', e)
                pass
            else:
                resp = resp.json()
                return self.return_format.format(response=resp)
            time.sleep(_ + 2)
        raise Exception('Failed.')

def _handle_history(self, history: List[dict]) -> Dict[str, Any]:
    return self.prompter(history)

def inference(self, history: List[dict]) -> str:
    for _ in range(3):
        try:
            body = self.body.copy()
            body.update(self._handle_history(history))
            with no_ssl_verification():
                resp = requests.post(self.url, json=body, headers=self.headers, proxies=self.proxies, timeout=120)
            if resp.status_code != 200:
                if check_context_limit(resp.text):
                    raise AgentContextLimitException(resp.text)
                else:
                    raise Exception(f'Invalid status code {resp.status_code}:\n\n{resp.text}')
        except AgentClientException as e:
            raise e
        except Exception as e:
            print('Warning: ', e)
            pass
        else:
            resp = resp.json()
            return self.return_format.format(response=resp)
        time.sleep(_ + 2)
    raise Exception('Failed.')

class FastChatAgent(AgentClient):
    """This agent is a test agent, which does nothing. (return empty string for each action)"""

    def __init__(self, model_name, controller_address=None, worker_address=None, temperature=0, max_new_tokens=32, top_p=0, prompter=None, args=None, **kwargs) -> None:
        if controller_address is None and worker_address is None:
            raise ValueError('Either controller_address or worker_address must be specified.')
        self.controller_address = controller_address
        self.worker_address = worker_address
        self.model_name = model_name
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.top_p = top_p
        self.prompter = Prompter.get_prompter(prompter)
        self.args = args or {}
        print(self.max_new_tokens)
        super().__init__(**kwargs)

    def inference(self, history: List[dict]) -> str:
        if self.worker_address:
            worker_addr = self.worker_address
        else:
            controller_addr = self.controller_address
            worker_addr = controller_addr
        if worker_addr == '':
            raise ValueError
        gen_params = {'model': self.model_name, 'temperature': self.temperature, 'max_new_tokens': self.max_new_tokens, 'echo': False, 'top_p': self.top_p, **self.args}
        if self.prompter:
            prompt = self.prompter(history)
            gen_params.update(prompt)
        else:
            conv = get_conversation_template(self.model_name)
            for history_item in history:
                role = history_item['role']
                content = history_item['content']
                if role == 'user':
                    conv.append_message(conv.roles[0], content)
                elif role == 'agent':
                    conv.append_message(conv.roles[1], content)
                else:
                    raise ValueError(f'Unknown role: {role}')
            conv.append_message(conv.roles[1], None)
            prompt = conv.get_prompt()
            gen_params.update({'prompt': prompt, 'stop': conv.stop_str, 'stop_token_ids': conv.stop_token_ids})
        headers = {'User-Agent': 'FastChat Client'}
        for _ in range(3):
            try:
                response = requests.post(controller_addr + '/worker_generate_stream', headers=headers, json=gen_params, stream=True, timeout=120)
                text = ''
                for line in response.iter_lines(decode_unicode=False, delimiter=b'\x00'):
                    if line:
                        data = json.loads(line)
                        if data['error_code'] != 0:
                            raise AgentNetworkException(data['text'])
                        text = data['text']
                return text
            except Timeout:
                print('Timeout, retrying...')
            except ConnectionError:
                print('Connection error, retrying...')
            time.sleep(5)
        else:
            raise Exception('Timeout after 3 retries.')

def inference(self, history: List[dict]) -> str:
    if self.worker_address:
        worker_addr = self.worker_address
    else:
        controller_addr = self.controller_address
        worker_addr = controller_addr
    if worker_addr == '':
        raise ValueError
    gen_params = {'model': self.model_name, 'temperature': self.temperature, 'max_new_tokens': self.max_new_tokens, 'echo': False, 'top_p': self.top_p, **self.args}
    if self.prompter:
        prompt = self.prompter(history)
        gen_params.update(prompt)
    else:
        conv = get_conversation_template(self.model_name)
        for history_item in history:
            role = history_item['role']
            content = history_item['content']
            if role == 'user':
                conv.append_message(conv.roles[0], content)
            elif role == 'agent':
                conv.append_message(conv.roles[1], content)
            else:
                raise ValueError(f'Unknown role: {role}')
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()
        gen_params.update({'prompt': prompt, 'stop': conv.stop_str, 'stop_token_ids': conv.stop_token_ids})
    headers = {'User-Agent': 'FastChat Client'}
    for _ in range(3):
        try:
            response = requests.post(controller_addr + '/worker_generate_stream', headers=headers, json=gen_params, stream=True, timeout=120)
            text = ''
            for line in response.iter_lines(decode_unicode=False, delimiter=b'\x00'):
                if line:
                    data = json.loads(line)
                    if data['error_code'] != 0:
                        raise AgentNetworkException(data['text'])
                    text = data['text']
            return text
        except Timeout:
            print('Timeout, retrying...')
        except ConnectionError:
            print('Connection error, retrying...')
        time.sleep(5)
    else:
        raise Exception('Timeout after 3 retries.')

class AgentOutput(BaseModel):
    status: AgentOutputStatus = AgentOutputStatus.NORMAL
    content: Union[str, None] = None

    @root_validator(pre=False, skip_on_failure=True)
    def post_validate(cls, instance: dict):
        assert instance.get('status') is not AgentOutputStatus.NORMAL or instance.get('content') is not None, 'If status is NORMAL, content should not be None'
        return instance

@root_validator(pre=False, skip_on_failure=True)
def post_validate(cls, instance: dict):
    assert instance.get('status') is not AgentOutputStatus.NORMAL or instance.get('content') is not None, 'If status is NORMAL, content should not be None'
    return instance

