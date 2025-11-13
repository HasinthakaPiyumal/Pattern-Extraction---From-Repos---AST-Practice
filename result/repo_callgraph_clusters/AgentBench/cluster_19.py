# Cluster 19

class KnowledgeGraph(Task):

    def __init__(self, data_file: str, max_rounds: int=15, one_shot: bool=False, database_file: Optional[str]=None, env_driver: str='manual', env_options: Optional[dict]=None, **kwargs):
        super().__init__(tools=TOOLS, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.max_rounds = max_rounds
        self.one_shot = one_shot
        self.data: List[Tuple[dict, set]] = []
        self.inputs: List[dict] = []
        self.targets: List[set] = []
        with open(data_file, 'r') as f:
            data_object = json.load(f)
        for item in data_object:
            answer = item.pop('answer')
            gold_answer = set()
            for a in answer:
                gold_answer.add(a['answer_argument'])
            self.data.append((item, gold_answer))
            self.inputs.append(item)
            self.targets.append(gold_answer)
        self.env_delegation = KnowledgeGraphEnvironmentDelegation(database_file)
        self.env_controller = create_controller(env_driver, self.env_delegation, **env_options)
        self.env_controller_background_task = None

    @cache
    def get_indices(self) -> List[SampleIndex]:
        return list(range(len(self.data)))

    async def start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
        self.env_controller.loop = asyncio.get_running_loop()
        if not self.env_controller_background_task:
            self.env_controller_background_task = asyncio.create_task(self.env_controller.background_task())
            weakref.finalize(self, self.env_controller_background_task.cancel)
        return await super().start_sample(index, session)

    def sync_start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
        self.logger.info(f'starting sample {index} with session id {session.id}')
        data_item = self.inputs[index]
        question = data_item['question']
        entities = data_item['entities']
        self.logger.info(f'[session {session.id}] Processing question: {question[:50]}...')
        session_id, _, urls = self.env_controller.sync_start_session(ENV_SUBTYPE)
        try:
            sparql_url = urls[ENV_SUBTYPE]
            sparql_executor = SparqlExecuter(sparql_url)
            api = API(sparql_executor, session.id)
            session.inject(ChatCompletionSystemMessageParam(role='system', content=INSTRUCTIONS.format(max_round=self.max_rounds)))
            if self.one_shot:
                session.inject(ONE_SHOT)
            session.inject(ChatCompletionUserMessageParam(role='user', content=f'{question}\nEntities: [{', '.join([entity for entity in entities])}]'))
            variables_list = []
            for current_round in range(self.max_rounds):
                response = session.sync_action()
                tool_calls = response.messages[0].get('tool_calls') or []
                if not tool_calls:
                    try:
                        final_message = response.messages[0].get('content') or ''
                        final_message = final_message.split('Observation:')[0]
                        final_message = final_message.replace('\\_', '_')
                        final_answer = re.findall('(?:Find|Final) Answer: #(\\d+)', final_message)
                        if final_answer:
                            var_idx = int(final_answer[0])
                            answer_variable = variables_list[var_idx]
                            predicted_answer = set(api.final_execute(answer_variable))
                            gold_answer = self.targets[index]
                            is_correct = len(gold_answer.intersection(predicted_answer)) == len(gold_answer) and len(gold_answer.intersection(predicted_answer)) == len(predicted_answer)
                            f1_score = self._calculate_f1(predicted_answer, gold_answer)
                            session.inject(RewardHistoryItem(reward=int(is_correct), score=f1_score))
                            return TaskSampleExecutionResult(status=SampleStatus.COMPLETED)
                    except IndexError:
                        self.logger.info(f'[session {session.id}] invalid variable index')
                        return TaskSampleExecutionResult(status=SampleStatus.AGENT_VALIDATION_FAILED)
                    except Exception:
                        self.logger.warning(f'[session {session.id}] error parsing final answer', exc_info=True)
                        return TaskSampleExecutionResult(status=SampleStatus.AGENT_VALIDATION_FAILED)
                    session.inject(ChatCompletionUserMessageParam(role='user', content='No valid function calls found! Need to recheck the function calls.'))
                    continue
                for tool_call in tool_calls:
                    tool_call_id: Optional[str] = None
                    try:
                        function_name = tool_call['function']['name']
                        tool_call_id = tool_call['id']
                        arguments = json.loads(tool_call['function']['arguments'])
                        try:
                            function = getattr(api, function_name)
                        except AttributeError:
                            session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Provide an invalid function name. Function {function_name} does not exist', tool_call_id=tool_call_id))
                            continue
                        try:
                            function_arguments = []
                            for argument_name in TOOLS_PARAM_ORDER[function_name]:
                                value = arguments[argument_name]
                                if isinstance(value, str) and value.startswith('#'):
                                    function_arguments.append(variables_list[int(value[1:])])
                                elif value in entities:
                                    function_arguments.append(entities[value])
                                else:
                                    function_arguments.append(value)
                        except KeyError:
                            session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Arguments do not match the function signature. Error processing arguments for {function_name}', tool_call_id=tool_call_id))
                            continue
                        execution, execution_message = function(*function_arguments)
                        self.logger.info(f'[session {session.id}] function {function_name} executed successfully')
                        if '##' in execution_message:
                            execution_message = execution_message.replace('##', f'#{len(variables_list)}')
                            variables_list.append(execution)
                        session.inject(ChatCompletionToolMessageParam(role='tool', content=execution_message, tool_call_id=tool_call_id))
                    except Exception as e:
                        self.logger.warning(f'[session {session.id}] error executing tool call', exc_info=True)
                        if tool_call_id:
                            session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Error processing tool call: {e}', tool_call_id=tool_call_id))
                        else:
                            session.inject(ChatCompletionUserMessageParam(role='user', content=f'Error processing tool call: {e}'))
            else:
                self.logger.info(f'[session {session.id}] max rounds reached')
                return TaskSampleExecutionResult(status=SampleStatus.TASK_LIMIT_REACHED)
        except AgentCancelledException:
            return TaskSampleExecutionResult(status=SampleStatus.CANCELLED)
        except Exception:
            self.logger.exception(f'error in task execution of index={index!r}, session.id={session.id!r}')
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR)
        finally:
            self.env_controller.sync_end_session(session_id)

    @staticmethod
    def _calculate_f1(predict_answer, gold_answer):
        if not isinstance(predict_answer, set):
            predict_answer = set(predict_answer)
        if not isinstance(gold_answer, set):
            gold_answer = set(gold_answer)
        TP = len(gold_answer.intersection(predict_answer))
        FP = len(predict_answer) - TP
        FN = len(gold_answer) - TP
        if TP == 0:
            return 0.0
        precision = TP / (TP + FP)
        recall = TP / (TP + FN)
        return 2 * precision * recall / (precision + recall)

def sync_start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
    self.logger.info(f'starting sample {index} with session id {session.id}')
    data_item = self.inputs[index]
    question = data_item['question']
    entities = data_item['entities']
    self.logger.info(f'[session {session.id}] Processing question: {question[:50]}...')
    session_id, _, urls = self.env_controller.sync_start_session(ENV_SUBTYPE)
    try:
        sparql_url = urls[ENV_SUBTYPE]
        sparql_executor = SparqlExecuter(sparql_url)
        api = API(sparql_executor, session.id)
        session.inject(ChatCompletionSystemMessageParam(role='system', content=INSTRUCTIONS.format(max_round=self.max_rounds)))
        if self.one_shot:
            session.inject(ONE_SHOT)
        session.inject(ChatCompletionUserMessageParam(role='user', content=f'{question}\nEntities: [{', '.join([entity for entity in entities])}]'))
        variables_list = []
        for current_round in range(self.max_rounds):
            response = session.sync_action()
            tool_calls = response.messages[0].get('tool_calls') or []
            if not tool_calls:
                try:
                    final_message = response.messages[0].get('content') or ''
                    final_message = final_message.split('Observation:')[0]
                    final_message = final_message.replace('\\_', '_')
                    final_answer = re.findall('(?:Find|Final) Answer: #(\\d+)', final_message)
                    if final_answer:
                        var_idx = int(final_answer[0])
                        answer_variable = variables_list[var_idx]
                        predicted_answer = set(api.final_execute(answer_variable))
                        gold_answer = self.targets[index]
                        is_correct = len(gold_answer.intersection(predicted_answer)) == len(gold_answer) and len(gold_answer.intersection(predicted_answer)) == len(predicted_answer)
                        f1_score = self._calculate_f1(predicted_answer, gold_answer)
                        session.inject(RewardHistoryItem(reward=int(is_correct), score=f1_score))
                        return TaskSampleExecutionResult(status=SampleStatus.COMPLETED)
                except IndexError:
                    self.logger.info(f'[session {session.id}] invalid variable index')
                    return TaskSampleExecutionResult(status=SampleStatus.AGENT_VALIDATION_FAILED)
                except Exception:
                    self.logger.warning(f'[session {session.id}] error parsing final answer', exc_info=True)
                    return TaskSampleExecutionResult(status=SampleStatus.AGENT_VALIDATION_FAILED)
                session.inject(ChatCompletionUserMessageParam(role='user', content='No valid function calls found! Need to recheck the function calls.'))
                continue
            for tool_call in tool_calls:
                tool_call_id: Optional[str] = None
                try:
                    function_name = tool_call['function']['name']
                    tool_call_id = tool_call['id']
                    arguments = json.loads(tool_call['function']['arguments'])
                    try:
                        function = getattr(api, function_name)
                    except AttributeError:
                        session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Provide an invalid function name. Function {function_name} does not exist', tool_call_id=tool_call_id))
                        continue
                    try:
                        function_arguments = []
                        for argument_name in TOOLS_PARAM_ORDER[function_name]:
                            value = arguments[argument_name]
                            if isinstance(value, str) and value.startswith('#'):
                                function_arguments.append(variables_list[int(value[1:])])
                            elif value in entities:
                                function_arguments.append(entities[value])
                            else:
                                function_arguments.append(value)
                    except KeyError:
                        session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Arguments do not match the function signature. Error processing arguments for {function_name}', tool_call_id=tool_call_id))
                        continue
                    execution, execution_message = function(*function_arguments)
                    self.logger.info(f'[session {session.id}] function {function_name} executed successfully')
                    if '##' in execution_message:
                        execution_message = execution_message.replace('##', f'#{len(variables_list)}')
                        variables_list.append(execution)
                    session.inject(ChatCompletionToolMessageParam(role='tool', content=execution_message, tool_call_id=tool_call_id))
                except Exception as e:
                    self.logger.warning(f'[session {session.id}] error executing tool call', exc_info=True)
                    if tool_call_id:
                        session.inject(ChatCompletionToolMessageParam(role='tool', content=f'Error processing tool call: {e}', tool_call_id=tool_call_id))
                    else:
                        session.inject(ChatCompletionUserMessageParam(role='user', content=f'Error processing tool call: {e}'))
        else:
            self.logger.info(f'[session {session.id}] max rounds reached')
            return TaskSampleExecutionResult(status=SampleStatus.TASK_LIMIT_REACHED)
    except AgentCancelledException:
        return TaskSampleExecutionResult(status=SampleStatus.CANCELLED)
    except Exception:
        self.logger.exception(f'error in task execution of index={index!r}, session.id={session.id!r}')
        return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR)
    finally:
        self.env_controller.sync_end_session(session_id)

def multi_edge_match(e1, e2):
    if len(e1) != len(e2):
        return False
    values1 = []
    values2 = []
    for v in e1.values():
        values1.append(v['relation'])
    for v in e2.values():
        values2.append(v['relation'])
    return sorted(values1) == sorted(values2)

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

def _inject_initial_messages(self, session: Session, description: str) -> None:
    """注入系统消息和问题描述"""
    system_message = 'You are an assistant that will act like a person. I will play the role of a Linux (Ubuntu) operating system.\nYour goal is to implement the operations required by me or answer the questions proposed by me.\nFor each of your turns, you should first think about what you should do, and then call exactly one of the provided tools according to the situation.\nIf you think the output is too long, I will truncate it. The truncated output is not complete. You have to deal with the truncating problem by yourself.\nAttention, your bash code should not contain any input operation. Once again, you should use one tool in each turn, and should not respond without function calling.\nNote that if you think the task has been finished, or there is some message missing to completely complete the task, you should respond with calling the function "finish_action", as no additional information will be provided.\nAlso, note that if you have gotten the answer to the question, you should call the "answer_action" tool instead of simply writing your answer in your response.\nYour answers should be exact and precise (for example, a single number), do not answer with full sentences or phrases.\nAlways use a tool provided instead of simply responding with content.'
    session.inject(ChatCompletionSystemMessageParam(role='system', content=system_message))
    session.inject(ChatCompletionUserMessageParam(role='user', content=f'Now, I will start a new problem in a new OS. My problem is:\n\n{description}'))

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

class AlfworldEnvWrapper:

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.lock = threading.Lock()

    def create_env(self, data_item: str):
        with self.lock:
            self.logger.info('initializing alfworld environment')
            alf_env = SingleAlfredTWEnv(self.config, data_item)
            return alf_env.init_env(batch_size=1)

    def reset_env(self, env):
        with self.lock:
            self.logger.info('resetting alfworld environment')
            return env.reset()

    def step_env(self, env, action):
        with self.lock:
            return env.step([action])

    def close_env(self, env):
        with self.lock:
            self.logger.info('closing alfworld environment')
            try:
                env.close()
            except Exception:
                self.logger.warning('error closing alfworld environment', exc_info=True)

def create_env(self, data_item: str):
    with self.lock:
        self.logger.info('initializing alfworld environment')
        alf_env = SingleAlfredTWEnv(self.config, data_item)
        return alf_env.init_env(batch_size=1)

def reset_env(self, env):
    with self.lock:
        self.logger.info('resetting alfworld environment')
        return env.reset()

def step_env(self, env, action):
    with self.lock:
        return env.step([action])

def close_env(self, env):
    with self.lock:
        self.logger.info('closing alfworld environment')
        try:
            env.close()
        except Exception:
            self.logger.warning('error closing alfworld environment', exc_info=True)

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

@contextlib.contextmanager
def no_ssl_verification():
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        opened_adapters.add(self.get_adapter(url))
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings
    requests.Session.merge_environment_settings = merge_environment_settings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings
        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass

