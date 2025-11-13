# Cluster 9

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

def norm_newline(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

class SparqlExecuter:

    def __init__(self, url: Union[str, None]=None):
        self.sparql = SPARQLWrapper(url or 'http://164.107.116.56:3093/sparql')
        self.sparql.setReturnFormat(JSON)

    def execute_query(self, query: str) -> List[str]:
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query)
            exit(0)
        rtn = []
        for result in results['results']['bindings']:
            assert len(result) == 1
            for var in result:
                rtn.append(result[var]['value'].replace('http://rdf.freebase.com/ns/', '').replace('-08:00', ''))
        return rtn

    def execute_unary(self, type: str) -> List[str]:
        query = '\n        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n        PREFIX : <http://rdf.freebase.com/ns/> \n        SELECT (?x0 AS ?value) WHERE {\n        SELECT DISTINCT ?x0  WHERE {\n        ?x0 :type.object.type :' + type + '. \n        }\n        }\n        '
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query)
            exit(0)
        rtn = []
        for result in results['results']['bindings']:
            rtn.append(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
        return rtn

    def execute_binary(self, relation: str) -> List[Tuple[str, str]]:
        query = '\n        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n        PREFIX : <http://rdf.freebase.com/ns/> \n        SELECT DISTINCT ?x0 ?x1 WHERE {\n        ?x0 :' + relation + ' ?x1. \n        }\n        '
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query)
            exit(0)
        rtn = []
        for result in results['results']['bindings']:
            rtn.append((result['x0']['value'], result['x1']['value']))
        return rtn

    def is_intersectant(self, derivation1: tuple, derivation2: str):
        if len(derivation1[1]) > 3 or len(derivation2[1]) > 3:
            return False
        if len(derivation1) == 2:
            clause1 = derivation1[0] + ' ' + ' / '.join(derivation1[1]) + ' ?x. \n'
        elif len(derivation1) == 3:
            clause1 = '?y ' + ' / '.join(derivation1[1]) + ' ?x. \n' + f'FILTER (?y {derivation1[2]} {derivation1[0]}) . \n'
        if len(derivation2) == 2:
            clause2 = derivation2[0] + ' ' + ' / '.join(derivation2[1]) + ' ?x. \n'
        elif len(derivation2) == 3:
            clause2 = '?y ' + ' / '.join(derivation2[1]) + ' ?x. \n' + f'FILTER (?y {derivation2[2]} {derivation2[0]}) . \n'
        query = '\n            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n            PREFIX : <http://rdf.freebase.com/ns/> \n            ASK {\n            ' + clause1 + clause2 + '\n    }\n    '
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query)
            exit(0)
        rtn = results['boolean']
        return rtn

    def entity_type_connected(self, entity: str, type: str):
        query = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                ASK {\n                ' + ':' + entity + '  !(<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>|:type.object.type) / :type.object.type :' + type + '\n    }\n    '
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query)
            exit(0)
        rtn = results['boolean']
        return rtn

    def entity_type_connected_2hop(self, entity: str, type: str):
        query = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                ASK {\n                ' + ':' + entity + '  !(<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>|:type.object.type) /  !(<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>|:type.object.type)/ :type.object.type :' + type + '\n    }\n    '
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query)
            exit(0)
        rtn = results['boolean']
        return rtn

    def get_in_attributes(self, value: str):
        in_attributes = set()
        query1 = '\n                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                    PREFIX : <http://rdf.freebase.com/ns/> \n                    SELECT (?x0 AS ?value) WHERE {\n                    SELECT DISTINCT ?x0  WHERE {\n                    ?x1 ?x0 ' + value + '. \n        FILTER regex(?x0, "http://rdf.freebase.com/ns/")\n        }\n        }\n        '
        self.sparql.setQuery(query1)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query1)
            exit(0)
        for result in results['results']['bindings']:
            in_attributes.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
        return in_attributes

    def get_in_relations(self, entity: str):
        in_relations = set()
        query1 = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                SELECT (?x0 AS ?value) WHERE {\n                SELECT DISTINCT ?x0  WHERE {\n                ?x1 ?x0 ' + ':' + entity + '. \n        FILTER regex(?x0, "http://rdf.freebase.com/ns/")\n        }\n        }\n        '
        self.sparql.setQuery(query1)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query1)
            exit(0)
        for result in results['results']['bindings']:
            in_relations.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
        return in_relations

    def get_in_entities(self, entity: str, relation: str):
        neighbors = set()
        query1 = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                SELECT (?x1 AS ?value) WHERE {\n                SELECT DISTINCT ?x1  WHERE {\n                ?x1' + ' :' + relation + ' :' + entity + '. \n                    FILTER regex(?x1, "http://rdf.freebase.com/ns/")\n                    }\n                    }\n                    '
        self.sparql.setQuery(query1)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query1)
            exit(0)
        for result in results['results']['bindings']:
            neighbors.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
        return neighbors

    def get_out_relations(self, entity: str):
        out_relations = set()
        query2 = '\n            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n            PREFIX : <http://rdf.freebase.com/ns/> \n            SELECT (?x0 AS ?value) WHERE {\n            SELECT DISTINCT ?x0  WHERE {\n            :' + entity + ' ?x0 ?x1 . \n        FILTER regex(?x0, "http://rdf.freebase.com/ns/")\n        }\n        }\n        '
        self.sparql.setQuery(query2)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query2)
            exit(0)
        for result in results['results']['bindings']:
            out_relations.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
        return out_relations

    def get_out_entities(self, entity: str, relation: str):
        neighbors = set()
        query2 = '\n            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n            PREFIX : <http://rdf.freebase.com/ns/> \n            SELECT (?x1 AS ?value) WHERE {\n            SELECT DISTINCT ?x1  WHERE {\n            :' + entity + ' :' + relation + ' ?x1 . \n                        FILTER regex(?x1, "http://rdf.freebase.com/ns/")\n                        }\n                        }\n                        '
        self.sparql.setQuery(query2)
        try:
            results = self.sparql.query().convert()
        except urllib.error.URLError:
            print(query2)
            exit(0)
        for result in results['results']['bindings']:
            neighbors.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
        return neighbors

def execute_query(self, query: str) -> List[str]:
    self.sparql.setQuery(query)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query)
        exit(0)
    rtn = []
    for result in results['results']['bindings']:
        assert len(result) == 1
        for var in result:
            rtn.append(result[var]['value'].replace('http://rdf.freebase.com/ns/', '').replace('-08:00', ''))
    return rtn

def execute_unary(self, type: str) -> List[str]:
    query = '\n        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n        PREFIX : <http://rdf.freebase.com/ns/> \n        SELECT (?x0 AS ?value) WHERE {\n        SELECT DISTINCT ?x0  WHERE {\n        ?x0 :type.object.type :' + type + '. \n        }\n        }\n        '
    self.sparql.setQuery(query)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query)
        exit(0)
    rtn = []
    for result in results['results']['bindings']:
        rtn.append(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
    return rtn

def execute_binary(self, relation: str) -> List[Tuple[str, str]]:
    query = '\n        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n        PREFIX : <http://rdf.freebase.com/ns/> \n        SELECT DISTINCT ?x0 ?x1 WHERE {\n        ?x0 :' + relation + ' ?x1. \n        }\n        '
    self.sparql.setQuery(query)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query)
        exit(0)
    rtn = []
    for result in results['results']['bindings']:
        rtn.append((result['x0']['value'], result['x1']['value']))
    return rtn

def is_intersectant(self, derivation1: tuple, derivation2: str):
    if len(derivation1[1]) > 3 or len(derivation2[1]) > 3:
        return False
    if len(derivation1) == 2:
        clause1 = derivation1[0] + ' ' + ' / '.join(derivation1[1]) + ' ?x. \n'
    elif len(derivation1) == 3:
        clause1 = '?y ' + ' / '.join(derivation1[1]) + ' ?x. \n' + f'FILTER (?y {derivation1[2]} {derivation1[0]}) . \n'
    if len(derivation2) == 2:
        clause2 = derivation2[0] + ' ' + ' / '.join(derivation2[1]) + ' ?x. \n'
    elif len(derivation2) == 3:
        clause2 = '?y ' + ' / '.join(derivation2[1]) + ' ?x. \n' + f'FILTER (?y {derivation2[2]} {derivation2[0]}) . \n'
    query = '\n            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n            PREFIX : <http://rdf.freebase.com/ns/> \n            ASK {\n            ' + clause1 + clause2 + '\n    }\n    '
    self.sparql.setQuery(query)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query)
        exit(0)
    rtn = results['boolean']
    return rtn

def entity_type_connected(self, entity: str, type: str):
    query = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                ASK {\n                ' + ':' + entity + '  !(<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>|:type.object.type) / :type.object.type :' + type + '\n    }\n    '
    self.sparql.setQuery(query)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query)
        exit(0)
    rtn = results['boolean']
    return rtn

def entity_type_connected_2hop(self, entity: str, type: str):
    query = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                ASK {\n                ' + ':' + entity + '  !(<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>|:type.object.type) /  !(<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>|:type.object.type)/ :type.object.type :' + type + '\n    }\n    '
    self.sparql.setQuery(query)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query)
        exit(0)
    rtn = results['boolean']
    return rtn

def get_in_attributes(self, value: str):
    in_attributes = set()
    query1 = '\n                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                    PREFIX : <http://rdf.freebase.com/ns/> \n                    SELECT (?x0 AS ?value) WHERE {\n                    SELECT DISTINCT ?x0  WHERE {\n                    ?x1 ?x0 ' + value + '. \n        FILTER regex(?x0, "http://rdf.freebase.com/ns/")\n        }\n        }\n        '
    self.sparql.setQuery(query1)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query1)
        exit(0)
    for result in results['results']['bindings']:
        in_attributes.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
    return in_attributes

def get_in_relations(self, entity: str):
    in_relations = set()
    query1 = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                SELECT (?x0 AS ?value) WHERE {\n                SELECT DISTINCT ?x0  WHERE {\n                ?x1 ?x0 ' + ':' + entity + '. \n        FILTER regex(?x0, "http://rdf.freebase.com/ns/")\n        }\n        }\n        '
    self.sparql.setQuery(query1)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query1)
        exit(0)
    for result in results['results']['bindings']:
        in_relations.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
    return in_relations

def get_in_entities(self, entity: str, relation: str):
    neighbors = set()
    query1 = '\n                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n                PREFIX : <http://rdf.freebase.com/ns/> \n                SELECT (?x1 AS ?value) WHERE {\n                SELECT DISTINCT ?x1  WHERE {\n                ?x1' + ' :' + relation + ' :' + entity + '. \n                    FILTER regex(?x1, "http://rdf.freebase.com/ns/")\n                    }\n                    }\n                    '
    self.sparql.setQuery(query1)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query1)
        exit(0)
    for result in results['results']['bindings']:
        neighbors.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
    return neighbors

def get_out_relations(self, entity: str):
    out_relations = set()
    query2 = '\n            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n            PREFIX : <http://rdf.freebase.com/ns/> \n            SELECT (?x0 AS ?value) WHERE {\n            SELECT DISTINCT ?x0  WHERE {\n            :' + entity + ' ?x0 ?x1 . \n        FILTER regex(?x0, "http://rdf.freebase.com/ns/")\n        }\n        }\n        '
    self.sparql.setQuery(query2)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query2)
        exit(0)
    for result in results['results']['bindings']:
        out_relations.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
    return out_relations

def get_out_entities(self, entity: str, relation: str):
    neighbors = set()
    query2 = '\n            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n            PREFIX : <http://rdf.freebase.com/ns/> \n            SELECT (?x1 AS ?value) WHERE {\n            SELECT DISTINCT ?x1  WHERE {\n            :' + entity + ' :' + relation + ' ?x1 . \n                        FILTER regex(?x1, "http://rdf.freebase.com/ns/")\n                        }\n                        }\n                        '
    self.sparql.setQuery(query2)
    try:
        results = self.sparql.query().convert()
    except urllib.error.URLError:
        print(query2)
        exit(0)
    for result in results['results']['bindings']:
        neighbors.add(result['value']['value'].replace('http://rdf.freebase.com/ns/', ''))
    return neighbors

def interaction(agent: AgentClient):
    try:
        history = []
        while True:
            print('================= USER  ===================')
            user = input('>>> ')
            history.append({'role': 'user', 'content': user})
            try:
                agent_response = agent.inference(history)
                print('================ AGENT ====================')
                print(agent_response)
                history.append({'role': 'agent', 'content': agent_response})
            except Exception as e:
                print(e)
                exit(0)
    except KeyboardInterrupt:
        print('\n[Exit] KeyboardInterrupt')
        exit(0)

def merge_environment_settings(self, url, proxies, stream, verify, cert):
    opened_adapters.add(self.get_adapter(url))
    settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
    settings['verify'] = False
    return settings

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

