# Cluster 15

class TaskHandler:

    def match(self, task_name) -> bool:
        raise NotImplementedError()

    def get_main_metric(self, overall_result):
        raise NotImplementedError()

    def get_order_priority(self):
        return 100000

    @staticmethod
    def get_handler(task_name) -> 'TaskHandler':
        handlers = [DCG(), HH(), OS(), DB(), KG(), LTP(), WB(), WS()]
        for handler in handlers:
            if handler.match(task_name):
                return handler
        raise ValueError(f'Unknown task: {task_name}')

@staticmethod
def get_handler(task_name) -> 'TaskHandler':
    handlers = [DCG(), HH(), OS(), DB(), KG(), LTP(), WB(), WS()]
    for handler in handlers:
        if handler.match(task_name):
            return handler
    raise ValueError(f'Unknown task: {task_name}')

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

def __hash__(self) -> int:
    return hash(self.program)

class API:

    def __init__(self, sparql_executor: SparqlExecuter, task_id: int=0):
        self.sparql_executor = sparql_executor
        self.task_id = task_id

    def final_execute(self, variable: Variable):
        program = variable.program
        processed_code = postprocess_raw_code(program)
        sparql_query = lisp_to_sparql(processed_code)
        results = self.sparql_executor.execute_query(sparql_query)
        return results

    def get_relations(self, variable: Union[Variable, str]):
        """
        Get all relations of a variable (variable = program derivation or entity id).
        Returns (None, "Observation: [...]").
        """
        if not isinstance(variable, Variable):
            if not re.match('^([mf])\\.[\\w_]+$', variable):
                raise ValueError('get_relations: variable must be a variable or an entity')
        cache_key = (self.task_id, variable if isinstance(variable, str) else hash(variable))
        if cache_key in relation_cache:
            out_relations = relation_cache[cache_key]
        else:
            if isinstance(variable, Variable):
                program = variable.program
                processed_code = postprocess_raw_code(program)
                sparql_query = lisp_to_sparql(processed_code)
                clauses = sparql_query.split('\n')
                new_clauses = [clauses[0], 'SELECT DISTINCT ?rel\nWHERE {\n?x ?rel ?obj .\n{']
                new_clauses.extend(clauses[1:])
                new_clauses.append('}\n}')
                new_query = '\n'.join(new_clauses)
                out_relations = self.sparql_executor.execute_query(new_query)
            else:
                out_relations = self.sparql_executor.get_out_relations(variable)
            out_relations = list(set(out_relations).intersection(set(relations)))
            relation_cache[cache_key] = out_relations
        rtn_str = f'Observation: [{', '.join(out_relations)}]'
        variable_relations_cache[variable] = out_relations
        return (None, rtn_str)

    def get_neighbors(self, variable: Union[Variable, str], relation: str):
        """
        Get neighbors via a relation. Returns (new_variable, "Observation: ...").
        """
        if not isinstance(variable, Variable):
            if not re.match('^([mf])\\.[\\w_]+$', variable):
                raise ValueError('get_neighbors: variable must be a variable or an entity')
        cache_key = (self.task_id, variable if isinstance(variable, str) else hash(variable))
        if cache_key not in relation_cache and variable not in variable_relations_cache:
            self.get_relations(variable)
        relations_to_check = variable_relations_cache.get(variable, [])
        if relation not in relations_to_check:
            raise ValueError('get_neighbors: relation must be a relation of the variable')
        rtn_str = f'Observation: variable ##, which are instances of {range_info[relation]}'
        base_program = variable.program if isinstance(variable, Variable) else variable
        new_variable = Variable(range_info[relation], f'(JOIN {relation + '_inv'} {base_program})')
        return (new_variable, rtn_str)

    def intersection(self, variable1: Variable, variable2: Variable):
        """
        Set intersection. Returns (new_variable, "Observation: ...").
        """
        if variable1.type != variable2.type:
            raise ValueError('intersection: two variables must have the same type')
        if not isinstance(variable1, Variable) or not isinstance(variable2, Variable):
            raise ValueError('intersection: variable must be a variable')
        rtn_str = f'Observation: variable ##, which are instances of {variable1.type}'
        new_variable = Variable(variable1.type, f'(AND {variable1.program} {variable2.program})')
        return (new_variable, rtn_str)

    def union(self, variable1: Variable, variable2: Variable):
        """
        Set union. Returns (new_variable, "Observation: ...").
        """
        if variable1.type != variable2.type:
            raise ValueError('union: two variables must have the same type')
        if not isinstance(variable1, Variable) or not isinstance(variable2, Variable):
            raise ValueError('union: variable must be a variable')
        rtn_str = f'Observation: variable ##, which are instances of {variable1.type}'
        new_variable = Variable(variable1.type, f'(OR {variable1.program} {variable2.program})')
        return (new_variable, rtn_str)

    def count(self, variable: Variable):
        """
        Count variable cardinality. Returns (new_variable(number), "Observation: ...").
        """
        rtn_str = f'Observation: variable ##, which is a number'
        new_variable = Variable('type.int', f'(COUNT {variable.program})')
        return (new_variable, rtn_str)

    def get_attributes(self, variable: Variable):
        """
        Get all attributes of a variable.
        Returns (None, "Observation: [...]").
        """
        cache_key = (self.task_id, hash(variable))
        if cache_key in attribute_cache:
            out_relations = attribute_cache[cache_key]
        else:
            program = variable.program
            processed_code = postprocess_raw_code(program)
            sparql_query = lisp_to_sparql(processed_code)
            clauses = sparql_query.split('\n')
            new_clauses = [clauses[0], 'SELECT DISTINCT ?rel\nWHERE {\n?x ?rel ?obj .\n{']
            new_clauses.extend(clauses[1:])
            new_clauses.append('}\n}')
            new_query = '\n'.join(new_clauses)
            out_relations = self.sparql_executor.execute_query(new_query)
            out_relations = list(set(out_relations).intersection(set(attributes)))
            attribute_cache[cache_key] = out_relations
            variable_attributes_cache[variable] = out_relations
        rtn_str = f'Observation: [{', '.join(out_relations)}]'
        return (None, rtn_str)

    def argmax(self, variable: Variable, attribute: str):
        """
        Argmax by attribute. Returns (new_variable, "Observation: ...").
        """
        cache_key = (self.task_id, hash(variable))
        if cache_key not in attribute_cache and variable not in variable_attributes_cache:
            self.get_attributes(variable)
        if attribute not in variable_attributes_cache.get(variable, []):
            raise ValueError('argmax: attribute must be an attribute of the variable')
        rtn_str = f'Observation: variable ##, which are instances of {variable.type}'
        new_variable = Variable(variable.type, f'(ARGMAX {variable.program} {attribute})')
        return (new_variable, rtn_str)

    def argmin(self, variable: Variable, attribute: str):
        """
        Argmin by attribute. Returns (new_variable, "Observation: ...").
        """
        cache_key = (self.task_id, hash(variable))
        if cache_key not in attribute_cache and variable not in variable_attributes_cache:
            self.get_attributes(variable)
        if attribute not in variable_attributes_cache.get(variable, []):
            raise ValueError('argmin: attribute must be an attribute of the variable')
        rtn_str = f'Observation: variable ##, which are instances of {variable.type}'
        new_variable = Variable(variable.type, f'(ARGMIN {variable.program} {attribute})')
        return (new_variable, rtn_str)

def final_execute(self, variable: Variable):
    program = variable.program
    processed_code = postprocess_raw_code(program)
    sparql_query = lisp_to_sparql(processed_code)
    results = self.sparql_executor.execute_query(sparql_query)
    return results

def get_relations(self, variable: Union[Variable, str]):
    """
        Get all relations of a variable (variable = program derivation or entity id).
        Returns (None, "Observation: [...]").
        """
    if not isinstance(variable, Variable):
        if not re.match('^([mf])\\.[\\w_]+$', variable):
            raise ValueError('get_relations: variable must be a variable or an entity')
    cache_key = (self.task_id, variable if isinstance(variable, str) else hash(variable))
    if cache_key in relation_cache:
        out_relations = relation_cache[cache_key]
    else:
        if isinstance(variable, Variable):
            program = variable.program
            processed_code = postprocess_raw_code(program)
            sparql_query = lisp_to_sparql(processed_code)
            clauses = sparql_query.split('\n')
            new_clauses = [clauses[0], 'SELECT DISTINCT ?rel\nWHERE {\n?x ?rel ?obj .\n{']
            new_clauses.extend(clauses[1:])
            new_clauses.append('}\n}')
            new_query = '\n'.join(new_clauses)
            out_relations = self.sparql_executor.execute_query(new_query)
        else:
            out_relations = self.sparql_executor.get_out_relations(variable)
        out_relations = list(set(out_relations).intersection(set(relations)))
        relation_cache[cache_key] = out_relations
    rtn_str = f'Observation: [{', '.join(out_relations)}]'
    variable_relations_cache[variable] = out_relations
    return (None, rtn_str)

def get_neighbors(self, variable: Union[Variable, str], relation: str):
    """
        Get neighbors via a relation. Returns (new_variable, "Observation: ...").
        """
    if not isinstance(variable, Variable):
        if not re.match('^([mf])\\.[\\w_]+$', variable):
            raise ValueError('get_neighbors: variable must be a variable or an entity')
    cache_key = (self.task_id, variable if isinstance(variable, str) else hash(variable))
    if cache_key not in relation_cache and variable not in variable_relations_cache:
        self.get_relations(variable)
    relations_to_check = variable_relations_cache.get(variable, [])
    if relation not in relations_to_check:
        raise ValueError('get_neighbors: relation must be a relation of the variable')
    rtn_str = f'Observation: variable ##, which are instances of {range_info[relation]}'
    base_program = variable.program if isinstance(variable, Variable) else variable
    new_variable = Variable(range_info[relation], f'(JOIN {relation + '_inv'} {base_program})')
    return (new_variable, rtn_str)

def intersection(self, variable1: Variable, variable2: Variable):
    """
        Set intersection. Returns (new_variable, "Observation: ...").
        """
    if variable1.type != variable2.type:
        raise ValueError('intersection: two variables must have the same type')
    if not isinstance(variable1, Variable) or not isinstance(variable2, Variable):
        raise ValueError('intersection: variable must be a variable')
    rtn_str = f'Observation: variable ##, which are instances of {variable1.type}'
    new_variable = Variable(variable1.type, f'(AND {variable1.program} {variable2.program})')
    return (new_variable, rtn_str)

def union(self, variable1: Variable, variable2: Variable):
    """
        Set union. Returns (new_variable, "Observation: ...").
        """
    if variable1.type != variable2.type:
        raise ValueError('union: two variables must have the same type')
    if not isinstance(variable1, Variable) or not isinstance(variable2, Variable):
        raise ValueError('union: variable must be a variable')
    rtn_str = f'Observation: variable ##, which are instances of {variable1.type}'
    new_variable = Variable(variable1.type, f'(OR {variable1.program} {variable2.program})')
    return (new_variable, rtn_str)

def count(self, variable: Variable):
    """
        Count variable cardinality. Returns (new_variable(number), "Observation: ...").
        """
    rtn_str = f'Observation: variable ##, which is a number'
    new_variable = Variable('type.int', f'(COUNT {variable.program})')
    return (new_variable, rtn_str)

def get_attributes(self, variable: Variable):
    """
        Get all attributes of a variable.
        Returns (None, "Observation: [...]").
        """
    cache_key = (self.task_id, hash(variable))
    if cache_key in attribute_cache:
        out_relations = attribute_cache[cache_key]
    else:
        program = variable.program
        processed_code = postprocess_raw_code(program)
        sparql_query = lisp_to_sparql(processed_code)
        clauses = sparql_query.split('\n')
        new_clauses = [clauses[0], 'SELECT DISTINCT ?rel\nWHERE {\n?x ?rel ?obj .\n{']
        new_clauses.extend(clauses[1:])
        new_clauses.append('}\n}')
        new_query = '\n'.join(new_clauses)
        out_relations = self.sparql_executor.execute_query(new_query)
        out_relations = list(set(out_relations).intersection(set(attributes)))
        attribute_cache[cache_key] = out_relations
        variable_attributes_cache[variable] = out_relations
    rtn_str = f'Observation: [{', '.join(out_relations)}]'
    return (None, rtn_str)

def argmax(self, variable: Variable, attribute: str):
    """
        Argmax by attribute. Returns (new_variable, "Observation: ...").
        """
    cache_key = (self.task_id, hash(variable))
    if cache_key not in attribute_cache and variable not in variable_attributes_cache:
        self.get_attributes(variable)
    if attribute not in variable_attributes_cache.get(variable, []):
        raise ValueError('argmax: attribute must be an attribute of the variable')
    rtn_str = f'Observation: variable ##, which are instances of {variable.type}'
    new_variable = Variable(variable.type, f'(ARGMAX {variable.program} {attribute})')
    return (new_variable, rtn_str)

def argmin(self, variable: Variable, attribute: str):
    """
        Argmin by attribute. Returns (new_variable, "Observation: ...").
        """
    cache_key = (self.task_id, hash(variable))
    if cache_key not in attribute_cache and variable not in variable_attributes_cache:
        self.get_attributes(variable)
    if attribute not in variable_attributes_cache.get(variable, []):
        raise ValueError('argmin: attribute must be an attribute of the variable')
    rtn_str = f'Observation: variable ##, which are instances of {variable.type}'
    new_variable = Variable(variable.type, f'(ARGMIN {variable.program} {attribute})')
    return (new_variable, rtn_str)

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

def bleu_score(reference, candidate):
    reference_tokens = reference.split()
    candidate_tokens = candidate.split()
    smoothie = SmoothingFunction().method4
    score = sentence_bleu([reference_tokens], candidate_tokens, smoothing_function=smoothie)
    return score

