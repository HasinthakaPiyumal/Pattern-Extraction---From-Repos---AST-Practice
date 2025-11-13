# Cluster 17

class DCG(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return 'card' in task_name or task_name.startswith('cg') or task_name.startswith('dcg')

    def get_main_metric(self, overall_result):
        try:
            return overall_result['custom']['score']
        except:
            return {'win_rate(legacy)': overall_result['custom']['win_rate']}

    def get_order_priority(self):
        return 4

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return 'card' in task_name or task_name.startswith('cg') or task_name.startswith('dcg')

class HH(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('alf')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['overall']['success_rate']

    def get_order_priority(self):
        return 6

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('alf')

class OS(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('os') or task_name.startswith('operating')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['overall']['acc']

    def get_order_priority(self):
        return 1

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('os') or task_name.startswith('operating')

class DB(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('db') or task_name.startswith('database')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['overall_cat_accuracy']

    def get_order_priority(self):
        return 2

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('db') or task_name.startswith('database')

class KG(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('kg') or task_name.startswith('knowledge')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['main']

    def get_order_priority(self):
        return 3

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('kg') or task_name.startswith('knowledge')

class LTP(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('ltp') or task_name.startswith('literal')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['main']

    def get_order_priority(self):
        return 5

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('ltp') or task_name.startswith('literal')

class WB(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('m2w') or task_name.startswith('mind2web')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['step_sr'] / 100

    def get_order_priority(self):
        return 8

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('m2w') or task_name.startswith('mind2web')

class WS(TaskHandler):

    def match(self, task_name) -> bool:
        task_name = task_name.lower()
        return task_name.startswith('ws') or task_name.startswith('webshop')

    def get_main_metric(self, overall_result):
        return overall_result['custom']['reward']

    def get_order_priority(self):
        return 7

def match(self, task_name) -> bool:
    task_name = task_name.lower()
    return task_name.startswith('ws') or task_name.startswith('webshop')

def parse_timestamp(time_str: str) -> float:
    try:
        return float(time_str)
    except:
        pass
    try:
        return datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').timestamp()
    except:
        pass
    try:
        return datetime.datetime.strptime(time_str, '%Y-%m-%d').timestamp()
    except:
        pass
    try:
        return datetime.datetime.strptime(time_str, '%Y-%m').timestamp()
    except:
        pass
    num = float(re.findall('[\\d\\.]+', time_str)[0])
    unit = re.findall('[a-zA-Z]+', time_str)[0]
    if unit == 'd':
        delta = num * 24 * 60 * 60
    elif unit == 'h':
        delta = num * 60 * 60
    elif unit == 'm':
        delta = num * 60
    elif unit == 's':
        delta = num
    else:
        raise Exception('Unknown time unit')
    return time.time() - delta

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

class DBResultProcessor:
    """
    处理数据库查询结果和比较的类
    只对外暴露compare_results和calculate_tables_hash接口
    """

    @staticmethod
    def compare_results(answer, ground_truth, query_type):
        """
        比较答案和标准答案
        
        参数:
        answer - 模型输出的答案
        ground_truth - 标准答案
        query_type - 查询类型 (SELECT/INSERT/UPDATE/DELETE)
        
        返回:
        bool - 答案是否匹配
        """
        try:
            processed_answer = DBResultProcessor._clean_answer(answer)
            processed_ground_truth = DBResultProcessor._clean_answer(ground_truth)
            if query_type in ('INSERT', 'DELETE', 'UPDATE'):
                return processed_answer == processed_ground_truth
            print('Processed answer:', processed_answer)
            print('Processed ground_truth:', processed_ground_truth)
            if len(processed_answer) == 1 and len(processed_ground_truth) == 1:
                ans_val = processed_answer[0]
                gt_val = processed_ground_truth[0]
                if ans_val == '0' and gt_val == '0':
                    return True
                if DBResultProcessor._is_float(ans_val) and DBResultProcessor._is_float(gt_val):
                    return DBResultProcessor._float_equal(ans_val, gt_val)
                return ans_val == gt_val
            else:
                if all((DBResultProcessor._is_float(x) for x in processed_answer)) and all((DBResultProcessor._is_float(x) for x in processed_ground_truth)):
                    if len(processed_answer) != len(processed_ground_truth):
                        return False
                    matched_gt = [False] * len(processed_ground_truth)
                    for ans in processed_answer:
                        matched = False
                        for i, gt in enumerate(processed_ground_truth):
                            if not matched_gt[i] and DBResultProcessor._float_equal(ans, gt):
                                matched_gt[i] = True
                                matched = True
                                break
                        if not matched:
                            return False
                    return all(matched_gt)
                return set(processed_answer) == set(processed_ground_truth)
        except Exception as e:
            print(f'Comparison error: {e}')
            return False

    @staticmethod
    async def calculate_tables_hash_async(database: Database, entry):
        """异步计算所有表的组合哈希值"""
        tables = entry['table'] if isinstance(entry['table'], list) else [entry['table']]
        table_hashes = []
        for table in tables:
            table_name = table['table_name']
            table_info = table['table_info']
            table_hash = await DBResultProcessor._get_table_hash_async(database, table_info, table_name)
            cleaned_hash = table_hash.strip('[]()')
            hash_value = cleaned_hash.split(',')[0].strip().strip("'")
            table_hashes.append(hash_value)
        combined_hash = '_'.join(sorted(table_hashes))
        return combined_hash

    @staticmethod
    async def _get_table_hash_async(database: Database, table_info, table_name):
        """异步获取单个表的MD5哈希值"""
        columns = ','.join([f'`{column['name']}`' for column in table_info['columns']])
        md5_query = f"select md5(group_concat(rowhash order by rowhash)) as hash from( SELECT substring(MD5(CONCAT_WS(',', {columns})), 1, 5) AS rowhash FROM `{table_name}`) as sub;"
        return await database.execute(md5_query)

    @staticmethod
    def _normalize_special_values(value):
        """处理特殊值、百分比和格式化数字"""
        if value is None:
            return '0'
        str_value = str(value).strip()
        if str_value.endswith('%'):
            try:
                return str_value[:-1].strip()
            except:
                pass
        if ',' in str_value and (not str_value.startswith('[')) and (not str_value.endswith(']')):
            try:
                str_value = str_value.replace(',', '')
            except:
                pass
        lower_value = str_value.lower()
        special_values_map = {'none': '0', 'null': '0', 'undefined': '0', 'nan': '0', 'inf': '0', 'infinity': '0', '-inf': '0', '-infinity': '0', '': '0'}
        return special_values_map.get(lower_value, str_value)

    @staticmethod
    def _clean_mysql_result(result):
        """处理MySQL执行结果的特殊格式 [(value,)] 或多元组情况 [(value1,), (value2,), ...]"""
        if isinstance(result, str) and result.startswith('[') and result.endswith(']'):
            try:
                parsed_result = eval(result)
                if isinstance(parsed_result, list) and all((isinstance(item, tuple) for item in parsed_result)):
                    cleaned_values = []
                    for item in parsed_result:
                        if len(item) == 1:
                            value = str(item[0]).strip().strip('\'"')
                            cleaned_values.append(value)
                    return cleaned_values
            except:
                pass
            try:
                result_stripped = result.strip('[]')
                if result_stripped.count('(') == 1 and result_stripped.startswith('(') and result_stripped.endswith(',)'):
                    value = result_stripped[1:-2]
                    value = value.strip().strip('\'"')
                    return [value]
            except:
                pass
        return None

    @staticmethod
    def _clean_answer(answer):
        """清理和标准化答案"""
        if answer is None:
            return ['0']
        mysql_result = DBResultProcessor._clean_mysql_result(answer)
        if mysql_result is not None:
            return [DBResultProcessor._normalize_special_values(x) for x in mysql_result]
        if isinstance(answer, str):
            answer = answer.strip()
            if answer.startswith('[') and answer.endswith(']'):
                try:
                    cleaned = eval(answer)
                    if isinstance(cleaned, list):
                        result = []
                        for item in cleaned:
                            if isinstance(item, tuple) and len(item) == 1:
                                value = str(item[0]).strip().strip('\'"')
                                result.append(DBResultProcessor._normalize_special_values(value))
                            else:
                                value = str(item).strip().strip('\'"')
                                result.append(DBResultProcessor._normalize_special_values(value))
                        return result
                except:
                    answer = answer[1:-1]
                    items = []
                    current = ''
                    in_quotes = False
                    for char in answer:
                        if char in '"\'':
                            in_quotes = not in_quotes
                        elif char == ',' and (not in_quotes):
                            if current:
                                items.append(DBResultProcessor._normalize_special_values(current.strip().strip('\'"')))
                                current = ''
                        else:
                            current += char
                    if current:
                        items.append(DBResultProcessor._normalize_special_values(current.strip().strip('\'"')))
                    return items
            else:
                return [DBResultProcessor._normalize_special_values(answer.strip().strip('\'"'))]
        elif isinstance(answer, (list, tuple)):
            result = []
            for item in answer:
                if isinstance(item, tuple) and len(item) == 1:
                    value = str(item[0]).strip().strip('\'"')
                    result.append(DBResultProcessor._normalize_special_values(value))
                else:
                    value = str(item).strip().strip('\'"')
                    result.append(DBResultProcessor._normalize_special_values(value))
            return result
        else:
            return [DBResultProcessor._normalize_special_values(str(answer).strip().strip('\'"'))]

    @staticmethod
    def _is_float(value):
        """检查是否可以转换为浮点数"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _float_equal(a, b, tol=0.01):
        """比较两个浮点数是否相等（考虑精度）"""
        try:
            return abs(float(a) - float(b)) <= tol
        except (ValueError, TypeError):
            return False

@staticmethod
def _normalize_special_values(value):
    """处理特殊值、百分比和格式化数字"""
    if value is None:
        return '0'
    str_value = str(value).strip()
    if str_value.endswith('%'):
        try:
            return str_value[:-1].strip()
        except:
            pass
    if ',' in str_value and (not str_value.startswith('[')) and (not str_value.endswith(']')):
        try:
            str_value = str_value.replace(',', '')
        except:
            pass
    lower_value = str_value.lower()
    special_values_map = {'none': '0', 'null': '0', 'undefined': '0', 'nan': '0', 'inf': '0', 'infinity': '0', '-inf': '0', '-infinity': '0', '': '0'}
    return special_values_map.get(lower_value, str_value)

@staticmethod
def _is_float(value):
    """检查是否可以转换为浮点数"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

@staticmethod
def _float_equal(a, b, tol=0.01):
    """比较两个浮点数是否相等（考虑精度）"""
    try:
        return abs(float(a) - float(b)) <= tol
    except (ValueError, TypeError):
        return False

def process_ob(ob):
    if ob.startswith('You arrive at loc '):
        ob = ob[ob.find('. ') + 2:]
    return ob

def process_action(action, choices, limit=0.01, to_print=False):
    if to_print:
        print('preprocess action: ', action)
    '\n    match = re.search("ACTION:(.*)", action)\n    if match:\n        action = match.group(1)\n    else:\n        return False\n    '
    action = action.strip().lower().split('\n')[0]
    if not choices:
        return action
    if action in choices:
        return action
    try:
        bleus = [bleu_score(choice, action) for choice in choices]
        max_index = np.argmax(np.array(bleus))
        max_score = bleus[max_index]
        if max_score > limit:
            if to_print:
                print('processed action: ', choices[max_index], ' score: ', max_score)
            return choices[max_index]
    except Exception as e:
        print('encounter exception: ', e)
        print('choices: ', choices)
        print('action: ', action)
    return action

