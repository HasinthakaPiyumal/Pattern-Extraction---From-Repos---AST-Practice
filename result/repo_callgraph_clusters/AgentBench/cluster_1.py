# Cluster 1

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def analysis_size(size_str):
    size_str = size_str.strip()
    availables = {'B': 1, 'Byte': 1, 'K': 1024, 'KB': 1024, 'M': 1024 * 1024, 'MB': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'GB': 1024 * 1024 * 1024, 'T': 1024 * 1024 * 1024 * 1024, 'TB': 1024 * 1024 * 1024 * 1024, 'P': 1024 * 1024 * 1024 * 1024 * 1024, 'PB': 1024 * 1024 * 1024 * 1024 * 1024}
    for size_unit in availables:
        if size_str.endswith(size_unit):
            return int(size_str[:-len(size_unit)]) * availables[size_unit]
    return int(size_str)

def expression_to_lisp(expression) -> str:
    rtn = '('
    for i, e in enumerate(expression):
        if isinstance(e, list):
            rtn += expression_to_lisp(e)
        else:
            rtn += e
        if i != len(expression) - 1:
            rtn += ' '
    rtn += ')'
    return rtn

def binary_nesting(function: str, elements: List[str], types_along_path=None) -> str:
    if len(elements) < 2:
        print('error: binary function should have 2 parameters!')
    if not types_along_path:
        if len(elements) == 2:
            return '(' + function + ' ' + elements[0] + ' ' + elements[1] + ')'
        else:
            return '(' + function + ' ' + elements[0] + ' ' + binary_nesting(function, elements[1:]) + ')'
    elif len(elements) == 2:
        return '(' + function + ' ' + types_along_path[0] + ' ' + elements[0] + ' ' + elements[1] + ')'
    else:
        return '(' + function + ' ' + types_along_path[0] + ' ' + elements[0] + ' ' + binary_nesting(function, elements[1:], types_along_path[1:]) + ')'

def get_canonical_lisp(logical_form: str):
    expression = lisp_to_nested_expression(logical_form)
    new_expression = _anonymize_entities(expression)
    new_logical_form = expression_to_lisp(new_expression)
    return new_logical_form

def _anonymize_entities(expression: list):
    if isinstance(expression, list):
        for i in range(len(expression)):
            if isinstance(expression[i], str):
                if expression[i].__contains__('^^') or expression[i][:2] in ['m.', 'g.']:
                    expression[i] = '[ENT]'
            else:
                _anonymize_entities(expression[i])
    return expression

def postprocess_raw_code(raw_lisp):
    expression = lisp_to_nested_expression(raw_lisp)
    if expression[0] in ['ARGMAX', 'ARGMIN'] and len(expression) > 3:
        expression[2] = binary_nesting('JOIN', expression[2:])
        expression = expression[:3]
        raw_lisp = expression_to_lisp(expression)
    splits = raw_lisp.split(' ')
    for i, s in enumerate(splits):
        if len(s) > 4 and s[-4:] == '_inv':
            splits[i] = f'(R {s[:-4]})'
        if len(s) > 5 and s[-5:] == '_inv)':
            splits[i] = f'(R {s[:-5]}))'
    processed_lisp = ' '.join(splits)
    return processed_lisp

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

def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
    """
            TaskOutput.result 0/1
        """
    overall = {'total': len([config for config in results if config]), 'pass': len([config for config in results if config and config.result and int(config.result.get('result', 0) == 1)])}
    overall['wrong'] = overall['total'] - overall['pass']
    overall['success_rate'] = overall['pass'] / overall['total'] if overall['total'] else 0
    return {'overall': overall}

