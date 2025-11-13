# Cluster 7

class Variable:

    def __init__(self, type, program):
        self.type = type
        self.program = program

    def __hash__(self) -> int:
        return hash(self.program)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Variable):
            return self.program == __value.program
        else:
            return False

    def __repr__(self) -> str:
        return self.program

def __eq__(self, __value: object) -> bool:
    if isinstance(__value, Variable):
        return self.program == __value.program
    else:
        return False

def get_nesting_level(expression) -> int:
    max_sub = 0
    for item in expression:
        if isinstance(item, list):
            level = get_nesting_level(item)
            if level > max_sub:
                max_sub = level
    return 1 + max_sub

def get_derivations_from_lisp(expression: List):
    if expression[0] == 'AND':
        assert len(expression) == 3
        if isinstance(expression[1], str):
            return get_derivations_from_lisp(expression[2])
        else:
            rtn = get_derivations_from_lisp(expression[1])
            rtn.update(get_derivations_from_lisp(expression[2]))
            return rtn
    elif expression[0] in ['ARGMIN', 'ARGMAX']:
        return None
    elif expression[0] == 'COUNT':
        return get_derivations_from_lisp(expression[1])
    elif expression[0] == 'JOIN':
        assert isinstance(expression[1], str)
        if isinstance(expression[2], str):
            rtn = {expression[2]: [':' + expression[1][:-4] if expression[1][-4:] == '_inv' else '^:' + expression[1]]}
            return rtn
        else:
            previous = get_derivations_from_lisp(expression[2])
            for k in previous:
                relation = expression[1]
                if isinstance(previous[k], list):
                    previous[k].extend([':' + relation[:-4] if relation[-4:] == '_inv' else '^:' + relation])
                elif isinstance(previous[k], tuple):
                    previous[k][0].extend([':' + relation[:-4] if relation[-4:] == '_inv' else '^:' + relation])
            return previous
    elif expression[0] in ['le', 'ge', 'lt', 'gt']:
        assert len(expression) == 3 and isinstance(expression[1], str) and isinstance(expression[2], str)
        rtn = {expression[2]: (['^:' + expression[1]], expression[0])}
        return rtn
    elif expression[0] == 'TC':
        assert len(expression) == 4
        return get_derivations_from_lisp(expression[1])

def retrieve_relations(exp: list):
    rtn = []
    for element in exp:
        if element == 'JOIN':
            continue
        elif isinstance(element, str):
            rtn.append(element)
        elif isinstance(element, list) and element[0] == 'R':
            rtn.append(element)
        elif isinstance(element, list) and element[0] == 'JOIN':
            rtn.extend(retrieve_relations(element))
    return rtn

def _linearize_lisp_expression(expression: list, sub_formula_id):
    sub_formulas = []
    for i, e in enumerate(expression):
        if isinstance(e, list) and e[0] != 'R':
            sub_formulas.extend(_linearize_lisp_expression(e, sub_formula_id))
            expression[i] = '#' + str(sub_formula_id[0] - 1)
    sub_formulas.append(expression)
    sub_formula_id[0] += 1
    return sub_formulas

def lisp_to_lambda(expressions: Union[List[str], str]):
    if not isinstance(expressions, list):
        return expressions
    if expressions[0] == 'AND':
        return lisp_to_lambda(expressions[1]) + ' AND ' + lisp_to_lambda(expressions[2])
    elif expressions[0] == 'JOIN':
        return lisp_to_lambda(expressions[1]) + '*' + lisp_to_lambda(expressions[2])

@DeprecationWarning
def lisp_to_sparql_naive(expressions: Union[List[str], str]):
    if expressions[0] == 'AND':
        clauses = lisp_to_sparql_and(expressions[1:])
    elif expressions[1] == 'JOIN':
        clauses = lisp_to_sparql_join(expressions[1:])
    sparql = 'PREFIX : <http://rdf.freebase.com/ns/> \n SELECT distinct ?x1 WHERE{\n'
    for clause in clauses:
        if not clause.__contains__('2015-08-10'):
            sparql += clause + '\n'
    sparql += '}'
    return sparql

@DeprecationWarning
def lisp_to_sparql_and(expressions: Union[List[str], str], variable=1):
    assert len(expressions) == 2
    clauses = []
    if not isinstance(expressions[0], list):
        pass
    elif expressions[0][0] == 'JOIN':
        clauses.extend(lisp_to_sparql_join(expressions[0][1:], variable))
    elif expressions[0][0] == 'AND':
        clauses.extend(lisp_to_sparql_and(expressions[0][1:], variable))
    if not isinstance(expressions[1], list):
        clauses.append('?x' + str(variable) + ' :type.object.type ' + expressions[0] + ' .')
    elif expressions[1][0] == 'JOIN':
        clauses.extend(lisp_to_sparql_join(expressions[1][1:], variable))
    elif expressions[1][0] == 'AND':
        clauses.extend(lisp_to_sparql_and(expressions[1][1:], variable))
    return clauses

@DeprecationWarning
def lisp_to_sparql_join(expressions: Union[List[str], str], variable=1):
    assert len(expressions) == 2
    clauses = []
    if not isinstance(expressions[1], list):
        if not isinstance(expressions[0], list):
            clauses.append('?x' + str(variable) + ' :' + expressions[0] + ' :' + expressions[1] + ' .')
        else:
            clauses.append(':' + expressions[1] + ' :' + expressions[0][1] + ' ' + '?x' + str(variable) + ' .')
    elif not isinstance(expressions[0], list):
        if expressions[1][0] == 'JOIN':
            clauses.append('?x' + str(variable) + ' :' + expressions[0] + ' ' + '?x' + str(variable + 1) + ' .')
            clauses.extend(lisp_to_sparql_join(expressions[1][1:], variable + 1))
        elif expressions[1][0] == 'AND':
            clauses.append('?x' + str(variable) + ' :' + expressions[0] + ' ' + '?x' + str(variable + 1) + ' .')
            clauses.extend(lisp_to_sparql_and(expressions[1][1:], variable + 1))
    elif expressions[1][0] == 'JOIN':
        clauses.append('?x' + str(variable + 1) + ' :' + expressions[0][1] + ' ' + '?x' + str(variable) + ' .')
        clauses.extend(lisp_to_sparql_join(expressions[1][1:], variable + 1))
    elif expressions[1][0] == 'AND':
        clauses.append('?x' + str(variable + 1) + ' :' + expressions[0][1] + ' ' + '?x' + str(variable) + ' .')
        clauses.extend(lisp_to_sparql_and(expressions[1][1:], variable + 1))
    return clauses

def process_inv_function(expression: List):
    for i, item in enumerate(expression):
        if isinstance(item, list):
            if item[0] == 'R':
                expression[i] = item[1] + '_inv'
            else:
                process_inv_function(item)

def preprocess_relation_path_for_superlatives(expression):
    relations = []
    for element in expression:
        if element == 'JOIN':
            continue
        if isinstance(element, list) and element[0] != 'R':
            assert element[0] == 'JOIN'
            relations.extend(preprocess_relation_path_for_superlatives(element))
            continue
        relations.append(element)
    return relations

def linearize_lisp_expression_for_bottom_up(expression: list, sub_formula_id):
    sub_formulas = []
    level = {}
    max_sub_level = -1
    for i, e in enumerate(expression):
        if isinstance(e, list):
            sf, lvl = linearize_lisp_expression_for_bottom_up(e, sub_formula_id)
            sub_formulas.extend(sf)
            level.update(lvl)
            expression[i] = '#' + str(sub_formula_id[0] - 1)
            if lvl[sub_formula_id[0] - 1] > max_sub_level:
                max_sub_level = lvl[sub_formula_id[0] - 1]
    current_level = max_sub_level + 1
    sub_formulas.append(expression)
    level[sub_formula_id[0]] = current_level
    sub_formula_id[0] += 1
    return (sub_formulas, level)

def get_sub_programs(formula: str):
    expression = lisp_to_nested_expression(formula)
    process_inv_function(expression)
    if expression[0] in ['ARGMIN', 'ARGMAX']:
        if isinstance(expression[2], list) and expression[2][0] == 'JOIN':
            arg_path = preprocess_relation_path_for_superlatives(expression[2])
            expression = expression[:2]
            expression.extend(arg_path)
    sub_formulas, level_mapping = linearize_lisp_expression_for_bottom_up(expression, [0])
    if sub_formulas[-1][0] in ['ARGMAX', 'ARGMIN'] and len(sub_formulas[-1]) > 3:
        last_id = len(level_mapping) - 1
        last_level = level_mapping[last_id]
        new_sub_formulas = sub_formulas[:-1]
        for i in range(len(sub_formulas[-1]) - 2):
            new_sub_formulas.append(sub_formulas[-1][:3 + i])
            level_mapping[last_id] = last_level
            last_id += 1
            last_level += 1
        sub_formulas = new_sub_formulas
    new_level_mapping = defaultdict(lambda: [])
    for k, v in level_mapping.items():
        new_level_mapping[v].append(k)
    return (sub_formulas, new_level_mapping)

def fill_sub_programs(sub_programs, entity_name, use_mid=False):
    sub_programs_filled = []
    for i, p in enumerate(sub_programs):
        p = [*p]
        for j, expression in enumerate(p):
            if expression[0] == '#':
                sub_id = int(expression[1:])
                p[j] = sub_programs_filled[sub_id]
            if not use_mid:
                if expression.__contains__('^^'):
                    p[j] = p[j].split('^^')[0]
                if expression in entity_name:
                    p[j] = entity_name[expression]
        sub_programs_filled.append(f'({' '.join(p)})')
    return sub_programs_filled

class DBBenchTask(Task):

    def __init__(self, data_file: str, db_file: Optional[str]=None, db_password: str='password', max_round: int=20, env_driver: str='docker', env_options: Optional[dict]=None, **configs):
        super().__init__(**configs)
        self.full_async = True
        self.logger = logging.getLogger(__name__)
        self.max_round = max_round
        self.data_file = data_file
        self.db_root_dir = db_file
        self.dataset = []
        with open(self.data_file) as f:
            raw_data = f.read()
            if self.data_file.endswith('json'):
                data = json.loads(raw_data)
            else:
                data = [json.loads(line) for line in raw_data.strip().split('\n')]
        for entry in data:
            ans_key = 'answer_md5' if entry['type'][0] in ('INSERT', 'DELETE', 'UPDATE') else 'label'
            ans = entry.pop(ans_key, None)
            inp = entry
            self.dataset.append((inp, ans))
        self.env_delegation = DBBenchEnvironmentDelegation(db_password)
        self.env_controller = create_controller(env_driver, self.env_delegation, **env_options)
        self.env_controller_background_task = None
        self.logger.info(f'DBBench initialized with {len(self.dataset)} samples. Root dir: {self.db_root_dir}')

    def get_indices(self) -> List[SampleIndex]:
        return list(range(len(self.dataset)))

    async def start_sample(self, index: int, session: Session) -> TaskSampleExecutionResult:
        self.env_controller.loop = asyncio.get_running_loop()
        if not self.env_controller_background_task:
            self.env_controller_background_task = asyncio.create_task(self.env_controller.background_task())
            weakref.finalize(self, self.env_controller_background_task.cancel)
        database: Optional[Database] = None
        try:
            entry = self.dataset[index][0]
            ground_truth = self.dataset[index][1]
            use_sqlite = entry.get('user_sqlite', False)
            if use_sqlite:
                db_dir = entry['create']['database']
                init_file = entry['create']['init']
                sqlite_path = os.path.join(self.db_root_dir, db_dir, init_file)
                database = SQLiteDatabase(sqlite_path)
                await database.initialize()
            else:
                init_sql = self._build_init_sql(entry)
                database = MySQLDatabase(self.env_controller)
                await database.initialize()
                await database.batch_execute(init_sql)
            session.inject(ChatCompletionSystemMessageParam(role='system', content=SYSTEM_PROMPT))
            user_prompt = ''
            if 'evidence' in entry and entry['evidence'] != '':
                user_prompt += 'Evidence about the question: ' + entry['evidence'] + '\n'
            if 'add_description' in entry and entry['add_description'] != '':
                user_prompt += 'Additional table information about the question: ' + entry['add_description'] + '\n'
            user_prompt += 'Question: ' + entry['description'] + '\n'
            session.inject(ChatCompletionUserMessageParam(role='user', content=user_prompt))
            for current_round in range(self.max_round):
                response = await session.action()
                tool_calls = []
                for message in response.messages:
                    tool_calls.extend(message.get('tool_calls', []) or [])
                if not tool_calls:
                    session.inject(ChatCompletionUserMessageParam(role='user', content='Internal error: No tool calls found despite finish reason.'))
                    continue
                for tool_call in tool_calls:
                    call_id = tool_call.get('id', '')
                    try:
                        function_name = tool_call.get('function', {}).get('name', '')
                        arguments = tool_call.get('function', {}).get('arguments', '{}')
                        arguments = json.loads(arguments)
                    except:
                        session.inject(ChatCompletionToolMessageParam(role='tool', tool_call_id=call_id, content='Error: Failed to parse tool call. Tool call format is incorrect.'))
                        self.logger.warning(f'Error parsing tool call: {tool_call}', exc_info=True)
                        continue
                    if function_name == 'execute_sql':
                        try:
                            sql = list(arguments.values())[0]
                            self.logger.info(f'Executing SQL: {sql}')
                            response = await asyncio.wait_for(database.execute(sql), 60)
                            self.logger.info(f'DB response: {response[:100]}{('...' if len(response) > 100 else '')}')
                            if not response:
                                response = 'No response from database.'
                            if 'Error' in response or 'error' in response.lower():
                                if 'syntax' in response.lower():
                                    self.logger.warning(f'SQL syntax error detected: {sql}')
                        except asyncio.TimeoutError:
                            self.logger.warning(f'Timeout executing SQL: {sql}')
                            response = 'Error: SQL execution timed out.'
                        except Exception as e:
                            self.logger.exception(f'Error executing query', exc_info=True)
                            response = f'Error executing query: {e}'
                        session.inject(ChatCompletionToolMessageParam(role='tool', tool_call_id=call_id, content=response))
                    elif function_name == 'commit_final_answer':
                        answer = list(arguments.values())[0]
                        if not answer:
                            self.logger.warning('Empty answer submitted')
                        else:
                            self.logger.info(f'Final answer submitted: {answer[:100]}{('...' if len(answer) > 100 else '')}')
                        std_sql = entry.get('sql', {}).get('query')
                        db_type = database.type
                        if entry['type'][0] in ('INSERT', 'DELETE', 'UPDATE'):
                            self.logger.info(f'Calculating table hash ({db_type})...')
                            if db_type == TYPE_SQLITE:
                                self.logger.warning(f'Table hash calculation for SQLite not implemented.')
                                answer_to_compare = 'SQLite hash not implemented'
                            else:
                                answer_to_compare = await DBResultProcessor.calculate_tables_hash_async(database, entry)
                            if ground_truth == '':
                                answer_db: Optional[Database] = None
                                try:
                                    answer_db = MySQLDatabase(self.env_controller)
                                    await answer_db.initialize()
                                    init_sql = self._build_init_sql(entry)
                                    await answer_db.batch_execute(init_sql)
                                    await answer_db.execute(std_sql)
                                    ground_truth = await DBResultProcessor.calculate_tables_hash_async(answer_db, entry)
                                finally:
                                    if answer_db:
                                        await answer_db.delete()
                        else:
                            answer_to_compare = answer
                        self.logger.info(f'Final Answer: {str(answer_to_compare)[:100]}{('...' if len(str(answer_to_compare)) > 100 else '')}')
                        self.logger.info(f'Ground Truth: {str(ground_truth)[:100]}{('...' if len(str(ground_truth)) > 100 else '')}')
                        is_correct = DBResultProcessor.compare_results(answer_to_compare, ground_truth, entry['type'][0])
                        self.logger.info(f'Correct: {is_correct}')
                        session.inject(RewardHistoryItem(reward=1 if is_correct else 0, score=1 if is_correct else 0))
                        return TaskSampleExecutionResult(status=SampleStatus.COMPLETED, result={'is_correct': is_correct, 'answer': answer, 'ground_truth': ground_truth, 'std_sql': std_sql, 'type': entry['type'][0]})
                    else:
                        self.logger.warning(f'Invalid function call: {function_name}')
                        session.inject(ChatCompletionToolMessageParam(role='tool', tool_call_id=call_id, content='Invalid function call. Please call a tool instead.'))
            else:
                session.inject(RewardHistoryItem(reward=0, score=0))
                return TaskSampleExecutionResult(status=SampleStatus.TASK_LIMIT_REACHED)
        except AgentCancelledException:
            session.inject(RewardHistoryItem(reward=0, score=0))
            return TaskSampleExecutionResult(status=SampleStatus.CANCELLED)
        except:
            self.logger.exception('Error during task execution')
            session.inject(RewardHistoryItem(reward=0, score=0))
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR)
        finally:
            if database:
                try:
                    await database.delete()
                except:
                    self.logger.warning('Error during database cleanup', exc_info=True)

    @staticmethod
    def _build_init_sql(entry: dict) -> List[Union[str, Tuple[str, Sequence[str]]]]:
        """Builds initialization SQL for MySQL."""
        tables = entry['table'] if isinstance(entry['table'], list) else [entry['table']]
        final_sql = []
        for table in tables:
            name = table['table_name']
            columns = ','.join([f'`{c['name']}` TEXT' for c in table['table_info']['columns']])
            column_names = ','.join([f'`{c['name']}`' for c in table['table_info']['columns']])
            items = []
            items_data = ()
            for row in table['table_info']['rows']:
                item = '(' + ','.join(['%s'] * len(row)) + ')'
                items_data += tuple((str(col) for col in row))
                items.append(item)
            items_str = ','.join(items)
            final_sql.append(f'CREATE TABLE IF NOT EXISTS `{name}` ({columns})')
            final_sql.append((f'INSERT INTO `{name}` ({column_names}) VALUES {items_str}', items_data))
        return final_sql

@staticmethod
def _build_init_sql(entry: dict) -> List[Union[str, Tuple[str, Sequence[str]]]]:
    """Builds initialization SQL for MySQL."""
    tables = entry['table'] if isinstance(entry['table'], list) else [entry['table']]
    final_sql = []
    for table in tables:
        name = table['table_name']
        columns = ','.join([f'`{c['name']}` TEXT' for c in table['table_info']['columns']])
        column_names = ','.join([f'`{c['name']}`' for c in table['table_info']['columns']])
        items = []
        items_data = ()
        for row in table['table_info']['rows']:
            item = '(' + ','.join(['%s'] * len(row)) + ')'
            items_data += tuple((str(col) for col in row))
            items.append(item)
        items_str = ','.join(items)
        final_sql.append(f'CREATE TABLE IF NOT EXISTS `{name}` ({columns})')
        final_sql.append((f'INSERT INTO `{name}` ({column_names}) VALUES {items_str}', items_data))
    return final_sql

class JsonEncoder(json.JSONEncoder):
    """Convert numpy classes to JSON serializable objects."""

    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(JsonEncoder, self).default(obj)

def default(self, obj):
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return super(JsonEncoder, self).default(obj)

def serialize(obj, max_depth=5, compress=False):
    """
    dump into json, including only basic types, list types and dict types.
    If other types are included, they will be converted into string.
    """
    if max_depth <= 0:
        return '...'
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, list) or isinstance(obj, tuple):
        if not compress or len(obj) <= 5:
            return [serialize(item, max_depth - 1, compress) for item in obj]
        else:
            return [serialize(item, max_depth - 1, True) for item in obj[:5]] + ['...(total: %d)' % len(obj)]
    elif isinstance(obj, dict):
        if not compress or len(obj) <= 5:
            return {str(key): serialize(obj[key], max_depth - 1, compress) for key in obj}
        else:
            ret = {str(key): serialize(obj[key], max_depth - 1, True) for key in list(obj.keys())[:5]}
            ret['...total...'] = len(obj)
            return ret
    elif hasattr(obj, '__dict__'):
        return serialize(obj.__dict__, max_depth, True)
    else:
        ret = str(obj)
        if len(ret) > 100:
            ret = ret[:45] + '   ...   ' + ret[-45:]
        return ret

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
def get_prompter(prompter: Union[Dict[str, Any], None]):
    if not prompter:
        return Prompter.default()
    assert isinstance(prompter, dict)
    prompter_name = prompter.get('name', None)
    prompter_args = prompter.get('args', {})
    if hasattr(Prompter, prompter_name) and callable(getattr(Prompter, prompter_name)):
        return getattr(Prompter, prompter_name)(**prompter_args)
    return Prompter.default()

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

@validator('parameters', pre=True)
def _ensure_dict(cls, v):
    if v is None:
        return {}
    return v

