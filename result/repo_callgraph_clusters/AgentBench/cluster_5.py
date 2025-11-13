# Cluster 5

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

@cache
def get_indices(self) -> List[SampleIndex]:
    return list(range(len(self.data)))

def get_answer_type(query: str):
    try:
        expression = lisp_to_nested_expression(query)
        G = logical_form_to_graph(expression)
        for node in G.nodes.items():
            if 'question_node' in node[1] and node[1]['question_node'] == 1:
                return node[1]['id']
    except Exception:
        return None

def get_symbol_type(symbol: str) -> int:
    if symbol.__contains__('^^'):
        return 2
    elif symbol in types:
        return 3
    elif symbol in relations:
        return 4
    elif symbol:
        return 1

def same_logical_form(form1: str, form2: str) -> bool:
    if form1.__contains__('@@UNKNOWN@@') or form2.__contains__('@@UNKNOWN@@'):
        return False
    try:
        G1 = logical_form_to_graph(lisp_to_nested_expression(form1))
    except Exception:
        return False
    try:
        G2 = logical_form_to_graph(lisp_to_nested_expression(form2))
    except Exception:
        return False

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
    return nx.is_isomorphic(G1, G2, node_match=node_match, edge_match=multi_edge_match)

def logical_form_to_graph(expression: List) -> nx.MultiGraph:
    G = _get_graph(expression)
    G.nodes[len(G.nodes())]['question_node'] = 1
    return G

def _get_graph(expression: List) -> nx.MultiGraph:
    if isinstance(expression, str):
        G = nx.MultiDiGraph()
        if get_symbol_type(expression) == 1:
            G.add_node(1, id=expression, type='entity')
        elif get_symbol_type(expression) == 2:
            G.add_node(1, id=expression, type='literal')
        elif get_symbol_type(expression) == 3:
            G.add_node(1, id=expression, type='class')
        elif get_symbol_type(expression) == 4:
            domain, rang = relation_dr[expression]
            G.add_node(1, id=rang, type='class')
            G.add_node(2, id=domain, type='class')
            G.add_edge(2, 1, relation=expression)
            if REVERSE:
                if expression in reverse_properties:
                    G.add_edge(1, 2, relation=reverse_properties[expression])
        return G
    if expression[0] == 'R':
        if get_symbol_type(expression[1]) != 4:
            pass
        G = _get_graph(expression[1])
        size = len(G.nodes())
        mapping = {}
        for n in G.nodes():
            mapping[n] = size - n + 1
        G = nx.relabel_nodes(G, mapping)
        return G
    elif expression[0] in ['JOIN', 'le', 'ge', 'lt', 'gt']:
        if isinstance(expression[1], str) and get_symbol_type(expression[1]) != 4 or (not isinstance(expression[2], list) and get_symbol_type(expression[2]) not in [1, 2]) or (isinstance(expression[1], list) and expression[1][0] != 'R'):
            pass
        G1 = _get_graph(expression=expression[1])
        G2 = _get_graph(expression=expression[2])
        size = len(G2.nodes())
        qn_id = size
        if G1.nodes[1]['type'] == G2.nodes[qn_id]['type'] == 'class':
            if G2.nodes[qn_id]['id'] in upper_types[G1.nodes[1]['id']]:
                G2.nodes[qn_id]['id'] = G1.nodes[1]['id']
        if G1.nodes[1]['type'] == 'entity':
            mapping = {}
            for n in G1.nodes():
                mapping[n] = n + size
            G1 = nx.relabel_nodes(G1, mapping)
        else:
            mapping = {}
            for n in G1.nodes():
                mapping[n] = n + size - 1
            G1 = nx.relabel_nodes(G1, mapping)
        G = nx.compose(G1, G2)
        if expression[0] != 'JOIN':
            G.nodes[1]['function'] = function_map[expression[0]]
        return G
    elif expression[0] == 'AND':
        if not isinstance(expression[1], list) and get_symbol_type(expression[1]) != 3 or not isinstance(expression[2], list):
            pass
        G1 = _get_graph(expression[1])
        G2 = _get_graph(expression[2])
        size1 = len(G1.nodes())
        size2 = len(G2.nodes())
        if G1.nodes[size1]['type'] == G2.nodes[size2]['type'] == 'class':
            G2.nodes[size2]['id'] = G1.nodes[size1]['id']
        if G1.nodes[1]['type'] == 'entity':
            mapping = {}
            for n in G1.nodes():
                mapping[n] = n + size2
            G1 = nx.relabel_nodes(G1, mapping)
        else:
            mapping = {}
            for n in G1.nodes():
                mapping[n] = n + size2 - 1
            G1 = nx.relabel_nodes(G1, mapping)
        G2 = nx.relabel_nodes(G2, {size2: size1 + size2 - 1})
        G = nx.compose(G1, G2)
        return G
    elif expression[0] == 'COUNT':
        if len(expression) != 2 or not isinstance(expression[1], list):
            pass
        G = _get_graph(expression[1])
        size = len(G.nodes())
        G.nodes[size]['function'] = 'count'
        return G
    elif expression[0].__contains__('ARG'):
        if not isinstance(expression[1], list) and get_symbol_type(expression[1]) != 3 or (not isinstance(expression[2], list) and get_symbol_type(expression[2]) != 4):
            pass
        G1 = _get_graph(expression[1])
        size1 = len(G1.nodes())
        G2 = _get_graph(expression[2])
        size2 = len(G2.nodes())
        G2.nodes[1]['id'] = 0
        G2.nodes[1]['type'] = 'literal'
        G2.nodes[1]['function'] = expression[0].lower()
        if G1.nodes[size1]['type'] == G2.nodes[size2]['type'] == 'class':
            G2.nodes[size2]['id'] = G1.nodes[size1]['id']
        mapping = {}
        for n in G1.nodes():
            mapping[n] = n + size2 - 1
        G1 = nx.relabel_nodes(G1, mapping)
        G2 = nx.relabel_nodes(G2, {size2: size1 + size2 - 1})
        G = nx.compose(G1, G2)
        return G
    elif expression[0] == 'TC':
        G = _get_graph(expression[1])
        size = len(G.nodes())
        G.nodes[size]['tc'] = (expression[2], expression[3])
        return G

def graph_to_logical_form(G, start, count: bool=False):
    if count:
        return '(COUNT ' + none_function(G, start) + ')'
    else:
        return none_function(G, start)

def get_end_num(G, s):
    end_num = defaultdict(lambda: 0)
    for edge in list(G.edges(s)):
        end_num[list(edge)[1]] += 1
    return end_num

def set_visited(G, s, e, relation):
    end_num = get_end_num(G, s)
    for i in range(0, end_num[e]):
        if G.edges[s, e, i]['relation'] == relation:
            G.edges[s, e, i]['visited'] = True

def count_function(G, start):
    return '(COUNT ' + none_function(G, start) + ')'

def none_function(G, start, arg_node=None, type_constraint=True):
    if arg_node is not None:
        arg = G.nodes[arg_node]['function']
        path = list(nx.all_simple_paths(G, start, arg_node))
        assert len(path) == 1
        arg_clause = []
        for i in range(0, len(path[0]) - 1):
            edge = G.edges[path[0][i], path[0][i + 1], 0]
            if edge['reverse']:
                relation = '(R ' + edge['relation'] + ')'
            else:
                relation = edge['relation']
            arg_clause.append(relation)
        while i >= 0:
            flag = False
            if G.out_degree[path[0][i]] > 2:
                flag = True
            G.remove_edge(path[0][i], path[0][i + 1], 0)
            i -= 1
            if flag:
                break
        if len(arg_clause) > 1:
            arg_clause = binary_nesting(function='JOIN', elements=arg_clause)
        else:
            arg_clause = arg_clause[0]
        return '(' + arg.upper() + ' ' + none_function(G, start) + ' ' + arg_clause + ')'
    if G.nodes[start]['type'] != 'class':
        return G.nodes[start]['id']
    end_num = get_end_num(G, start)
    clauses = []
    if G.nodes[start]['question'] and type_constraint:
        clauses.append(G.nodes[start]['id'])
    for key in end_num.keys():
        for i in range(0, end_num[key]):
            if not G.edges[start, key, i]['visited']:
                relation = G.edges[start, key, i]['relation']
                G.edges[start, key, i]['visited'] = True
                set_visited(G, key, start, relation)
                if G.edges[start, key, i]['reverse']:
                    relation = '(R ' + relation + ')'
                if G.nodes[key]['function'].__contains__('<') or G.nodes[key]['function'].__contains__('>'):
                    if G.nodes[key]['function'] == '>':
                        clauses.append('(gt ' + relation + ' ' + none_function(G, key) + ')')
                    if G.nodes[key]['function'] == '>=':
                        clauses.append('(ge ' + relation + ' ' + none_function(G, key) + ')')
                    if G.nodes[key]['function'] == '<':
                        clauses.append('(lt ' + relation + ' ' + none_function(G, key) + ')')
                    if G.nodes[key]['function'] == '<=':
                        clauses.append('(le ' + relation + ' ' + none_function(G, key) + ')')
                else:
                    clauses.append('(JOIN ' + relation + ' ' + none_function(G, key) + ')')
    if len(clauses) == 0:
        return G.nodes[start]['id']
    if len(clauses) == 1:
        return clauses[0]
    else:
        return binary_nesting(function='AND', elements=clauses)

def get_lisp_from_graph_query(graph_query):
    G = nx.MultiDiGraph()
    aggregation = 'none'
    arg_node = None
    for node in graph_query['nodes']:
        G.add_node(node['nid'], id=node['id'], type=node['node_type'], question=node['question_node'], function=node['function'], cla=node['class'])
        if node['question_node'] == 1:
            qid = node['nid']
        if node['function'] != 'none':
            aggregation = node['function']
            if node['function'].__contains__('arg'):
                arg_node = node['nid']
    for edge in graph_query['edges']:
        G.add_edge(edge['start'], edge['end'], relation=edge['relation'], reverse=False, visited=False)
        G.add_edge(edge['end'], edge['start'], relation=edge['relation'], reverse=True, visited=False)
    if 'count' == aggregation:
        return count_function(G, qid)
    else:
        return none_function(G, qid, arg_node=arg_node)

def lisp_to_sparql(lisp_program: str):
    clauses = []
    order_clauses = []
    entities = set()
    identical_variables_r = {}
    expression = lisp_to_nested_expression(lisp_program)
    superlative = False
    if expression[0] in ['ARGMAX', 'ARGMIN']:
        superlative = True
        if isinstance(expression[2], list):

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
            relations = retrieve_relations(expression[2])
            expression = expression[:2]
            expression.extend(relations)
    sub_programs = _linearize_lisp_expression(expression, [0])
    question_var = len(sub_programs) - 1
    count = False

    def get_root(var: int):
        while var in identical_variables_r:
            var = identical_variables_r[var]
        return var
    for i, subp in enumerate(sub_programs):
        i = str(i)
        if subp[0] == 'JOIN':
            if isinstance(subp[1], list):
                if subp[2][:2] in ['m.', 'g.']:
                    clauses.append('ns:' + subp[2] + ' ns:' + subp[1][1] + ' ?x' + i + ' .')
                    entities.add(subp[2])
                elif subp[2][0] == '#':
                    clauses.append('?x' + subp[2][1:] + ' ns:' + subp[1][1] + ' ?x' + i + ' .')
                else:
                    if subp[2].__contains__('^^'):
                        data_type = subp[2].split('^^')[1].split('#')[1]
                        if data_type not in ['integer', 'float', 'dateTime', 'double']:
                            subp[2] = f'"{subp[2].split('^^')[0] + '-08:00'}"^^<{subp[2].split('^^')[1]}>'
                        else:
                            subp[2] = f'"{subp[2].split('^^')[0]}"^^<{subp[2].split('^^')[1]}>'
                    clauses.append(subp[2] + ' ns:' + subp[1][1] + ' ?x' + i + ' .')
            elif subp[2][:2] in ['m.', 'g.']:
                clauses.append('?x' + i + ' ns:' + subp[1] + ' ns:' + subp[2] + ' .')
                entities.add(subp[2])
            elif subp[2][0] == '#':
                clauses.append('?x' + i + ' ns:' + subp[1] + ' ?x' + subp[2][1:] + ' .')
            elif subp[2].__contains__('^^'):
                data_type = subp[2].split('^^')[1].split('#')[1]
                if data_type not in ['integer', 'float', 'dateTime', 'double']:
                    subp[2] = f'"{subp[2].split('^^')[0] + '-08:00'}"^^<{subp[2].split('^^')[1]}>'
                else:
                    subp[2] = f'"{subp[2].split('^^')[0]}"^^<{subp[2].split('^^')[1]}>'
                clauses.append('?x' + i + ' ns:' + subp[1] + ' ' + subp[2] + ' .')
            else:
                clauses.append(f'?x ns:{subp[1]} ?obj .')
                clauses.append(f'FILTER (str(?obj) = "{subp[2]}") .')
        elif subp[0] == 'AND':
            var1 = int(subp[2][1:])
            rooti = get_root(int(i))
            root1 = get_root(var1)
            if rooti > root1:
                identical_variables_r[rooti] = root1
            else:
                identical_variables_r[root1] = rooti
                root1 = rooti
            if subp[1][0] == '#':
                var2 = int(subp[1][1:])
                root2 = get_root(var2)
                if root1 > root2:
                    identical_variables_r[root1] = root2
                else:
                    identical_variables_r[root2] = root1
            else:
                clauses.append('?x' + i + ' ns:type.object.type ns:' + subp[1] + ' .')
        elif subp[0] in ['le', 'lt', 'ge', 'gt']:
            clauses.append('?x' + i + ' ns:' + subp[1] + ' ?y' + i + ' .')
            if subp[0] == 'le':
                op = '<='
            elif subp[0] == 'lt':
                op = '<'
            elif subp[0] == 'ge':
                op = '>='
            else:
                op = '>'
            if subp[2].__contains__('^^'):
                data_type = subp[2].split('^^')[1].split('#')[1]
                if data_type not in ['integer', 'float', 'dateTime', 'double']:
                    subp[2] = f'"{subp[2].split('^^')[0] + '-08:00'}"^^<{subp[2].split('^^')[1]}>'
                else:
                    subp[2] = f'"{subp[2].split('^^')[0]}"^^<{subp[2].split('^^')[1]}>'
            clauses.append(f'FILTER (?y{i} {op} {subp[2]})')
        elif subp[0] == 'TC':
            var = int(subp[1][1:])
            rooti = get_root(int(i))
            root_var = get_root(var)
            if rooti > root_var:
                identical_variables_r[rooti] = root_var
            else:
                identical_variables_r[root_var] = rooti
            year = subp[3]
            if year == 'NOW':
                from_para = '"2015-08-10"^^xsd:dateTime'
                to_para = '"2015-08-10"^^xsd:dateTime'
            else:
                from_para = f'"{year}-12-31"^^xsd:dateTime'
                to_para = f'"{year}-01-01"^^xsd:dateTime'
            clauses.append(f'FILTER(NOT EXISTS {{?x{i} ns:{subp[2]} ?sk0}} || ')
            clauses.append(f'EXISTS {{?x{i} ns:{subp[2]} ?sk1 . ')
            clauses.append(f'FILTER(xsd:datetime(?sk1) <= {from_para}) }})')
            if subp[2][-4:] == 'from':
                clauses.append(f'FILTER(NOT EXISTS {{?x{i} ns:{subp[2][:-4] + 'to'} ?sk2}} || ')
                clauses.append(f'EXISTS {{?x{i} ns:{subp[2][:-4] + 'to'} ?sk3 . ')
            else:
                clauses.append(f'FILTER(NOT EXISTS {{?x{i} ns:{subp[2][:-9] + 'to_date'} ?sk2}} || ')
                clauses.append(f'EXISTS {{?x{i} ns:{subp[2][:-9] + 'to_date'} ?sk3 . ')
            clauses.append(f'FILTER(xsd:datetime(?sk3) >= {to_para}) }})')
        elif subp[0] in ['ARGMIN', 'ARGMAX']:
            superlative = True
            if subp[1][0] == '#':
                var = int(subp[1][1:])
                rooti = get_root(int(i))
                root_var = get_root(var)
                if rooti > root_var:
                    identical_variables_r[rooti] = root_var
                else:
                    identical_variables_r[root_var] = rooti
            else:
                clauses.append(f'?x{i} ns:type.object.type ns:{subp[1]} .')
            if len(subp) == 3:
                clauses.append(f'?x{i} ns:{subp[2]} ?sk0 .')
            elif len(subp) > 3:
                for j, relation in enumerate(subp[2:-1]):
                    if j == 0:
                        var0 = f'x{i}'
                    else:
                        var0 = f'c{j - 1}'
                    var1 = f'c{j}'
                    if isinstance(relation, list) and relation[0] == 'R':
                        clauses.append(f'?{var1} ns:{relation[1]} ?{var0} .')
                    else:
                        clauses.append(f'?{var0} ns:{relation} ?{var1} .')
                clauses.append(f'?c{j} ns:{subp[-1]} ?sk0 .')
            if subp[0] == 'ARGMIN':
                order_clauses.append('ORDER BY ?sk0')
            elif subp[0] == 'ARGMAX':
                order_clauses.append('ORDER BY DESC(?sk0)')
            order_clauses.append('LIMIT 1')
        elif subp[0] == 'COUNT':
            var = int(subp[1][1:])
            root_var = get_root(var)
            identical_variables_r[int(i)] = root_var
            count = True
    for i in range(len(clauses)):
        for k in identical_variables_r:
            clauses[i] = clauses[i].replace(f'?x{k} ', f'?x{get_root(k)} ')
    question_var = get_root(question_var)
    for i in range(len(clauses)):
        clauses[i] = clauses[i].replace(f'?x{question_var} ', f'?x ')
    if superlative:
        arg_clauses = clauses[:]
    for entity in entities:
        clauses.append(f'FILTER (?x != ns:{entity})')
    clauses.insert(0, f"FILTER (!isLiteral(?x) OR lang(?x) = '' OR langMatches(lang(?x), 'en'))")
    clauses.insert(0, 'WHERE {')
    if count:
        clauses.insert(0, f'SELECT COUNT DISTINCT ?x')
    elif superlative:
        clauses.insert(0, '{SELECT ?sk0')
        clauses = arg_clauses + clauses
        clauses.insert(0, 'WHERE {')
        clauses.insert(0, f'SELECT DISTINCT ?x')
    else:
        clauses.insert(0, f'SELECT DISTINCT ?x')
    clauses.insert(0, 'PREFIX ns: <http://rdf.freebase.com/ns/>')
    clauses.append('}')
    clauses.extend(order_clauses)
    if superlative:
        clauses.append('}')
        clauses.append('}')
    return '\n'.join(clauses)

def max_count_relations(program: str):
    expression = lisp_to_nested_expression(program)
    relations_count = count_relations_expression(expression)
    max = 0
    for r in relations_count:
        if relations_count[r] > max:
            max = relations_count[r]
    return max

def count_relations_expression(expression: List):
    rtn = defaultdict(lambda: 0)
    for item in expression:
        if isinstance(item, str):
            if get_symbol_type(item) == 4:
                rtn[item] += 1
                if item in reverse_properties:
                    rtn[reverse_properties[item]] += 1
        else:
            item_rtn = count_relations_expression(item)
            for r in item_rtn:
                if r in rtn:
                    rtn[r] = rtn[r] + item_rtn[r]
                else:
                    rtn[r] = item_rtn[r]
    return rtn

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

def get_indices(self) -> List[Any]:
    return list(self.problem_configs.keys())

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

def get_indices(self) -> List[SampleIndex]:
    return list(range(len(self.dataset)))

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

def get_indices(self) -> List[Any]:
    return list(range(len(self.data_files)))

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

def get_indices(self) -> List[Any]:
    return list(range(*self.ranging))

