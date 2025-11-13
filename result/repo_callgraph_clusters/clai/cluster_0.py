# Cluster 0

def remove(path):
    print('cleaning %s' % path)
    try:
        remove_tree(path)
    except OSError:
        print('folder not found')

def copy(file, to_path):
    print('copying file from %s to %s' % (file, to_path))
    copy_file(file, to_path, update=1)

def download_file(file_url, filename):
    print('Download %s' % file_url)
    from urllib import request
    ssl._create_default_https_context = ssl._create_unverified_context
    request.urlretrieve(file_url, filename=filename)

def remove(path):
    print('cleaning %s' % path)
    remove_tree(path)

@unittest.skip('Only for local testing')
class SearchAgentTest(unittest.TestCase):

    @classmethod
    def set_up_class(cls):
        _agent = HowDoIAgent()
        cls.agent = _agent

    def print_and_verify(self, question, answer):
        state = State(user_name='tester', command_id='0', command=question)
        action = self.agent.get_next_action(state=state)
        print(f'Input: {state.command}')
        print('===========================')
        print(f'Response: {action.suggested_command}')
        print('===========================')
        print(f'Explanation: {action.description}')
        self.assertEqual(answer, action.suggested_command)

    @unittest.skip('Only for local testing')
    def test_get_next_action_pwd_without_question(self):
        self.agent.init_agent()
        if OS_NAME in ('OS/390', 'Z/OS'):
            self.print_and_verify('pds', 'pds')
        else:
            self.print_and_verify('pds', None)

    @unittest.skip('Only for local testing')
    def test_get_next_action_pwd_with_question(self):
        self.agent.init_agent()
        if OS_NAME in ('OS/390', 'Z/OS'):
            self.print_and_verify('What is a pds?', 'man readlink')
        else:
            self.print_and_verify('What is pwd?', 'man pwd')

    @unittest.skip('Only for local testing')
    def test_get_next_action_sudo(self):
        self.agent.init_agent()
        self.print_and_verify('when to use sudo vs su?', 'man su')

    @unittest.skip('Only for local testing')
    def test_get_next_action_disk(self):
        self.agent.init_agent()
        question: str = 'find out disk usage per user?'
        if OS_NAME in ('OS/390', 'Z/OS'):
            self.print_and_verify(question, 'man du')
        else:
            self.print_and_verify(question, 'man df')

    @unittest.skip('Only for local testing')
    def test_get_next_action_zip(self):
        self.agent.init_agent()
        question: str = 'How to process gz files?'
        if OS_NAME in ('OS/390', 'Z/OS'):
            self.print_and_verify(question, 'man dnctl')
        else:
            self.print_and_verify(question, 'man gzip')

    @unittest.skip('Only for local testing')
    def test_get_next_action_pds(self):
        self.agent.init_agent()
        question: str = 'copy a PDS member?'
        if OS_NAME in ('OS/390', 'Z/OS'):
            self.print_and_verify(question, 'man tcsh')
        else:
            self.print_and_verify(question, 'man cmp')

def print_and_verify(self, question, answer):
    state = State(user_name='tester', command_id='0', command=question)
    action = self.agent.get_next_action(state=state)
    print(f'Input: {state.command}')
    print('===========================')
    print(f'Response: {action.suggested_command}')
    print('===========================')
    print(f'Explanation: {action.description}')
    self.assertEqual(answer, action.suggested_command)

@unittest.skip('Only for local testing')
def test_get_next_action_pwd_without_question(self):
    self.agent.init_agent()
    if OS_NAME in ('OS/390', 'Z/OS'):
        self.print_and_verify('pds', 'pds')
    else:
        self.print_and_verify('pds', None)

@unittest.skip('Only for local testing')
def test_get_next_action_pwd_with_question(self):
    self.agent.init_agent()
    if OS_NAME in ('OS/390', 'Z/OS'):
        self.print_and_verify('What is a pds?', 'man readlink')
    else:
        self.print_and_verify('What is pwd?', 'man pwd')

@unittest.skip('Only for local testing')
def test_get_next_action_sudo(self):
    self.agent.init_agent()
    self.print_and_verify('when to use sudo vs su?', 'man su')

@unittest.skip('Only for local testing')
def test_get_next_action_disk(self):
    self.agent.init_agent()
    question: str = 'find out disk usage per user?'
    if OS_NAME in ('OS/390', 'Z/OS'):
        self.print_and_verify(question, 'man du')
    else:
        self.print_and_verify(question, 'man df')

@unittest.skip('Only for local testing')
def test_get_next_action_zip(self):
    self.agent.init_agent()
    question: str = 'How to process gz files?'
    if OS_NAME in ('OS/390', 'Z/OS'):
        self.print_and_verify(question, 'man dnctl')
    else:
        self.print_and_verify(question, 'man gzip')

@unittest.skip('Only for local testing')
def test_get_next_action_pds(self):
    self.agent.init_agent()
    question: str = 'copy a PDS member?'
    if OS_NAME in ('OS/390', 'Z/OS'):
        self.print_and_verify(question, 'man tcsh')
    else:
        self.print_and_verify(question, 'man cmp')

class NLC2CMDCloudTest(unittest.TestCase):

    @classmethod
    def set_up_class(cls):
        cls.state = State(user_name='tester', command_id='0', command='show me the list of cloud tags', result_code='0')
        cls.agent = NLC2CMD()

    @unittest.skip('Local dev testing only')
    def test_get_next_action_cloud_login(self):
        self.state.command = 'how do i login'
        action = self.agent.get_next_action(state=self.state)
        print('Input: {}'.format(self.state.command))
        print('---------------------------')
        print('Explanation: {}'.format(action.description))
        self.assertEqual(NOOP_COMMAND, action.suggested_command)
        self.assertEqual('\x1b[95mTry >> ibmcloud login\x1b[0m', action.description)
        print('===========================')

    @unittest.skip('Local dev testing only')
    def test_get_next_action_cloud_help(self):
        self.state.command = 'help me'
        action = self.agent.get_next_action(state=self.state)
        print('Input: {}'.format(self.state.command))
        print('---------------------------')
        print('Explanation: {}'.format(action.description))
        self.assertEqual(NOOP_COMMAND, action.suggested_command)
        self.assertEqual('\x1b[95mTry >> ibmcloud help COMMAND\x1b[0m', action.description)
        print('===========================')

    @unittest.skip('Local dev testing only')
    def test_get_next_action_cloud_invite(self):
        self.state.command = 'I want to invite someone to my cloud'
        action = self.agent.get_next_action(state=self.state)
        print('Input: {}'.format(self.state.command))
        print('---------------------------')
        print('Explanation: {}'.format(action.description))
        self.assertEqual(NOOP_COMMAND, action.suggested_command)
        self.assertEqual('\x1b[95mTry >> ibmcloud account user-invite USER_EMAIL\x1b[0m', action.description)
        print('===========================')

@classmethod
def set_up_class(cls):
    cls.state = State(user_name='tester', command_id='0', command='show me the list of cloud tags', result_code='0')
    cls.agent = NLC2CMD()

@unittest.skip('Local dev testing only')
def test_get_next_action_cloud_login(self):
    self.state.command = 'how do i login'
    action = self.agent.get_next_action(state=self.state)
    print('Input: {}'.format(self.state.command))
    print('---------------------------')
    print('Explanation: {}'.format(action.description))
    self.assertEqual(NOOP_COMMAND, action.suggested_command)
    self.assertEqual('\x1b[95mTry >> ibmcloud login\x1b[0m', action.description)
    print('===========================')

@unittest.skip('Local dev testing only')
def test_get_next_action_cloud_help(self):
    self.state.command = 'help me'
    action = self.agent.get_next_action(state=self.state)
    print('Input: {}'.format(self.state.command))
    print('---------------------------')
    print('Explanation: {}'.format(action.description))
    self.assertEqual(NOOP_COMMAND, action.suggested_command)
    self.assertEqual('\x1b[95mTry >> ibmcloud help COMMAND\x1b[0m', action.description)
    print('===========================')

@unittest.skip('Local dev testing only')
def test_get_next_action_cloud_invite(self):
    self.state.command = 'I want to invite someone to my cloud'
    action = self.agent.get_next_action(state=self.state)
    print('Input: {}'.format(self.state.command))
    print('---------------------------')
    print('Explanation: {}'.format(action.description))
    self.assertEqual(NOOP_COMMAND, action.suggested_command)
    self.assertEqual('\x1b[95mTry >> ibmcloud account user-invite USER_EMAIL\x1b[0m', action.description)
    print('===========================')

class RetrievalAgentTest(unittest.TestCase):

    @classmethod
    def set_up_class(cls):
        cls.state = State(user_name='tester', command_id='0', command='./tmp_file.sh', result_code='1', stderr='Permission denied')
        cls.agent = HelpMeAgent()

    @unittest.skip('Need internet connection')
    def test_get_post_execute(self):
        action = self.agent.post_execute(state=self.state)
        print('Input: {}'.format(self.state.command))
        print('===========================')
        print('Response: {}'.format(action.suggested_command))
        print('===========================')
        print('Explanation: {}'.format(action.description))
        self.assertNotEqual(NOOP_COMMAND, action.suggested_command)

    @unittest.skip('Local testing')
    def test_get_forum(self):
        forum = self.agent.store.search('Permission denied', service='stack_exchange', size=1)
        self.assertEqual(1, len(forum))

    @unittest.skip('Local testing')
    def test_get_kc(self):
        kc_hits = self.agent.store.search('Permission denied', service='ibm_kc', size=1)
        print('Got this result from the KnowledgeCenter: ' + str(kc_hits))
        self.assertEqual(1, len(kc_hits))
        man_hits = self.agent.store.search(kc_hits[0]['summary'], service='manpages', size=10)
        print('Got this result from the Manpages service: ' + str(man_hits))
        self.assertEqual('connect', man_hits['commands'][-1])

    @unittest.skip('Local testing')
    def test_get_command(self):
        hits = self.agent.store.search("sudo allows a permitted user to execute a commandas the superuser or another user, as specified by the security policy.  The invoking user's real (not effective) user ID is used to determine the user name with which to query the security policy.", service='manpages', size=10)
        self.assertEqual('sudo', hits['commands'][-1])

@classmethod
def set_up_class(cls):
    cls.state = State(user_name='tester', command_id='0', command='./tmp_file.sh', result_code='1', stderr='Permission denied')
    cls.agent = HelpMeAgent()

@unittest.skip('Need internet connection')
def test_get_post_execute(self):
    action = self.agent.post_execute(state=self.state)
    print('Input: {}'.format(self.state.command))
    print('===========================')
    print('Response: {}'.format(action.suggested_command))
    print('===========================')
    print('Explanation: {}'.format(action.description))
    self.assertNotEqual(NOOP_COMMAND, action.suggested_command)

@unittest.skip('Local testing')
def test_get_forum(self):
    forum = self.agent.store.search('Permission denied', service='stack_exchange', size=1)
    self.assertEqual(1, len(forum))

@unittest.skip('Local testing')
def test_get_kc(self):
    kc_hits = self.agent.store.search('Permission denied', service='ibm_kc', size=1)
    print('Got this result from the KnowledgeCenter: ' + str(kc_hits))
    self.assertEqual(1, len(kc_hits))
    man_hits = self.agent.store.search(kc_hits[0]['summary'], service='manpages', size=10)
    print('Got this result from the Manpages service: ' + str(man_hits))
    self.assertEqual('connect', man_hits['commands'][-1])

@unittest.skip('Local testing')
def test_get_command(self):
    hits = self.agent.store.search("sudo allows a permitted user to execute a commandas the superuser or another user, as specified by the security policy.  The invoking user's real (not effective) user ID is used to determine the user name with which to query the security policy.", service='manpages', size=10)
    self.assertEqual('sudo', hits['commands'][-1])

def clai_plugins_state():
    return State(command_id=ANY_ID, user_name=ANY_NAME, command='clai skills')

def clai_power_state():
    return State(command_id=ANY_ID, user_name=ANY_NAME, command='clai auto')

def clai_power_disabled_state():
    return State(command_id=ANY_ID, user_name=ANY_NAME, command='clai manual')

def command_state():
    return State(command_id=ANY_ID, user_name=ANY_NAME, command='command')

def clai_select_state(plugin_to_select):
    return State(command_id=ANY_ID, user_name=ANY_NAME, command=f'clai activate {plugin_to_select}')

def clai_unselect_state(plugin_to_select):
    return State(command_id=ANY_ID, user_name=ANY_NAME, command=f'clai unselect {plugin_to_select}')

@unittest.skipIf(OS_NAME not in ('OS/390', 'Z/OS'), 'Test only valid on z/OS')
class MsgCodeAgentTest(unittest.TestCase):

    @classmethod
    def set_up_class(cls):
        _agent = MsgCodeAgent()
        cls.agent = _agent

    @classmethod
    def try_command(cls, command_and_args: List[str]) -> Action:
        result: CompletedProcess = subprocess.run(command_and_args, encoding='UTF8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        command: str = None
        if isinstance(result.args, list):
            command = ' '.join(result.args)
        else:
            command = result.args
        result_code: str = str(result.returncode)
        return cls.scaffold_command_response(command=command, result_code=result_code, stdout=result.stdout, stderr=result.stderr)

    @classmethod
    def scaffold_command_response(cls, **kwargs) -> Action:
        state = State(command_id='0', user_name='tester', command=kwargs['command'], result_code=kwargs['result_code'], stderr=kwargs['stderr'])
        print(f'Command: {kwargs['command']}')
        print(f'RetCode: {kwargs['result_code']}')
        print(f"stdout: '{kwargs['stdout']}'")
        print(f"stderr: '{kwargs['stderr']}'")
        print('===========================')
        action = cls.agent.post_execute(state=state)
        print('Input: {}'.format(state.command))
        print('===========================')
        print('Response: {}'.format(action.suggested_command))
        print('===========================')
        print('Explanation: {}'.format(action.description))
        return action

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_message_bad_cd(self):
        self.agent.init_agent()
        with tempfile.NamedTemporaryFile() as our_file:
            action = self.try_command(['cd', our_file.name])
        lines = action.description.strip().split('\n')
        self.assertEqual(f'{Colorize.EMOJI_ROBOT}I asked bpxmtext about that message:', lines[0])
        self.assertEqual('Action: Reissue the service specifying a directory file.', lines[-2])

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_message_bad_cat(self):
        self.agent.init_agent()
        with tempfile.NamedTemporaryFile() as our_file:
            file_that_isnt_there: str = our_file.name
        action = self.try_command(['cat', file_that_isnt_there])
        lines = action.description.strip().split('\n')
        self.assertEqual(f'{Colorize.EMOJI_ROBOT}I asked bpxmtext about that message:', lines[0])
        self.assertEqual('Action: The open service request cannot be processed. Correct the name or the', lines[-3])
        self.assertEqual('open flags and retry the operation.', lines[-2])

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_unhelpful_message_1(self):
        self.agent.init_agent()
        action = self.scaffold_command_response(command=['not', 'a', 'real', 'command'], result_code=str(1), stdout='', stderr='IEB4223I 0xDFDFDFDF')
        lines = action.description.strip().split('\n')
        self.assertEqual(f"{Colorize.EMOJI_ROBOT}I couldn't find any help for message code 'IEB4223I'", lines[0])

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_unhelpful_message_2(self):
        self.agent.init_agent()
        action = self.scaffold_command_response(command=['not', 'a', 'real', 'command'], result_code=str(1), stdout='', stderr='IEB4223I 0xDFDF')
        lines = action.description.strip().split('\n')
        self.assertEqual(f"{Colorize.EMOJI_ROBOT}I couldn't find any help for message code 'IEB4223I'", lines[0])

    @unittest.skip('Only for local testing')
    def test_bad_cp(self):
        self.agent.init_agent()
        with tempfile.NamedTemporaryFile() as our_file:
            action = self.try_command(['cp', our_file.name, our_file.name])
        lines = action.description.strip().split('\n')
        self.assertEqual(f'{Colorize.EMOJI_ROBOT}I looked up FSUM8977 in the IBM KnowledgeCenter for you:', lines[0])
        self.assertEqual(f'{Colorize.INFO}Product: z/OS', lines[1])
        self.assertEqual('Topic: FSUM8977 ...', lines[2])

@classmethod
def scaffold_command_response(cls, **kwargs) -> Action:
    state = State(command_id='0', user_name='tester', command=kwargs['command'], result_code=kwargs['result_code'], stderr=kwargs['stderr'])
    print(f'Command: {kwargs['command']}')
    print(f'RetCode: {kwargs['result_code']}')
    print(f"stdout: '{kwargs['stdout']}'")
    print(f"stderr: '{kwargs['stderr']}'")
    print('===========================')
    action = cls.agent.post_execute(state=state)
    print('Input: {}'.format(state.command))
    print('===========================')
    print('Response: {}'.format(action.suggested_command))
    print('===========================')
    print('Explanation: {}'.format(action.description))
    return action

@unittest.skip('Only for local testing')
def test_bpxmtextable_message_bad_cd(self):
    self.agent.init_agent()
    with tempfile.NamedTemporaryFile() as our_file:
        action = self.try_command(['cd', our_file.name])
    lines = action.description.strip().split('\n')
    self.assertEqual(f'{Colorize.EMOJI_ROBOT}I asked bpxmtext about that message:', lines[0])
    self.assertEqual('Action: Reissue the service specifying a directory file.', lines[-2])

@unittest.skip('Only for local testing')
def test_bpxmtextable_message_bad_cat(self):
    self.agent.init_agent()
    with tempfile.NamedTemporaryFile() as our_file:
        file_that_isnt_there: str = our_file.name
    action = self.try_command(['cat', file_that_isnt_there])
    lines = action.description.strip().split('\n')
    self.assertEqual(f'{Colorize.EMOJI_ROBOT}I asked bpxmtext about that message:', lines[0])
    self.assertEqual('Action: The open service request cannot be processed. Correct the name or the', lines[-3])
    self.assertEqual('open flags and retry the operation.', lines[-2])

@unittest.skip('Only for local testing')
def test_bpxmtextable_unhelpful_message_1(self):
    self.agent.init_agent()
    action = self.scaffold_command_response(command=['not', 'a', 'real', 'command'], result_code=str(1), stdout='', stderr='IEB4223I 0xDFDFDFDF')
    lines = action.description.strip().split('\n')
    self.assertEqual(f"{Colorize.EMOJI_ROBOT}I couldn't find any help for message code 'IEB4223I'", lines[0])

@unittest.skip('Only for local testing')
def test_bpxmtextable_unhelpful_message_2(self):
    self.agent.init_agent()
    action = self.scaffold_command_response(command=['not', 'a', 'real', 'command'], result_code=str(1), stdout='', stderr='IEB4223I 0xDFDF')
    lines = action.description.strip().split('\n')
    self.assertEqual(f"{Colorize.EMOJI_ROBOT}I couldn't find any help for message code 'IEB4223I'", lines[0])

@unittest.skip('Only for local testing')
def test_bad_cp(self):
    self.agent.init_agent()
    with tempfile.NamedTemporaryFile() as our_file:
        action = self.try_command(['cp', our_file.name, our_file.name])
    lines = action.description.strip().split('\n')
    self.assertEqual(f'{Colorize.EMOJI_ROBOT}I looked up FSUM8977 in the IBM KnowledgeCenter for you:', lines[0])
    self.assertEqual(f'{Colorize.INFO}Product: z/OS', lines[1])
    self.assertEqual('Topic: FSUM8977 ...', lines[2])

def launcher_server(host, port, directive, websocket):
    if directive == NEW_DIRECTIVE:
        if not is_port_busy(host, port, False):
            create_server_socket(host, port, websocket)
        else:
            print('The server is up yet')
    if directive == START_DIRECTIVE:
        print(f'starting CLAI')
        while is_port_busy(host, port, True):
            print('')
        create_server_socket(host, port, websocket)

def __remove_clai_history__(lines, original_command):
    if not lines:
        return lines
    if original_command not in lines:
        return lines
    lines_from_last = lines[::-1]
    position = lines_from_last.index(original_command)
    position = len(lines) - position - 1
    if position > 0 and lines[position - 1] == original_command:
        position = position - 1
    new_lines = lines[:position + 1]
    return new_lines

def post_process_command(command_id: str, user_name: str, cmd_result: str, stderr: str):
    process_changes = obtain_last_processes(user_name)
    post_command_action = send_command_post_execute(command_id=command_id, user_name=user_name, result_code=cmd_result, stderr=stderr, processes=ProcessesValues(last_processes=process_changes))
    if stderr:
        print(stderr)
    if post_command_action and post_command_action.description:
        print(post_command_action.description)

class Linuss(Agent):

    def __init__(self):
        super(Linuss, self).__init__()
        self._config_path = os.path.join(Path(__file__).parent.absolute(), 'equivalencies.json')
        self.equivalencies = self.__read_equivalencies()

    def __read_equivalencies(self):
        logger.info('####### read equivalencies inside linuss ########')
        try:
            with open(self._config_path, 'r') as json_file:
                equivalencies = json.load(json_file)
        except Exception as e:
            logger.debug(f'Linuss Error: {e}')
            equivalencies = json.load({})
        return equivalencies

    def __build_suggestion(self, command, options, cmd_key) -> any:
        params: list[Tuple(str)] = []
        suggestion: str = None
        explanations: list[str] = []
        tokens: list[str] = command.split()
        idx = 0
        max_idx = len(tokens) - 1
        while idx <= max_idx:
            token: str = tokens[idx]
            if re.match('-([\\w_-]+)', token):
                if idx < max_idx and (not re.match('-([\\w_-]+)', tokens[idx + 1])):
                    next_token = tokens[idx + 1]
                    params.append((token[1:], next_token))
                    idx = idx + 1
                else:
                    params.append((token[1:], None))
            elif token != cmd_key:
                params.append((None, token))
            idx = idx + 1
        if '' in options:
            suggestion = self.equivalencies[cmd_key]['']['equivalent']
        else:
            suggestion = cmd_key
        for opt, arg in params:
            if opt is not None:
                if opt[0] == '-' or len(opt) == 1:
                    equivalency = self.__get_equavalency(opt, options, cmd_key)
                    if equivalency['equivalent']:
                        suggestion = f'{suggestion} {equivalency['equivalent']}'
                        if 'explanation' in equivalency:
                            explanations.append(equivalency['explanation'])
                    else:
                        explanations.append(f'The -{opt} flag is not available on USS')
                else:
                    for char in opt:
                        equivalency = self.__get_equavalency(char, options, cmd_key)
                        if equivalency['equivalent']:
                            suggestion = f'{suggestion} {equivalency['equivalent']}'
                            if 'explanation' in equivalency:
                                explanations.append(equivalency['explanation'])
                        else:
                            explanations.append(f'The -{char} flag is not available on USS')
            if arg is not None:
                suggestion = f'{suggestion} {arg}'
        if suggestion is not None:
            return Action(suggested_command=suggestion, confidence=1, description='\n'.join(explanations))
        else:
            return Action(suggested_command=NOOP_COMMAND, description=None)

    def __get_equavalency(self, target, options, cmd_key) -> dict:
        target = f'-{target}'
        for option in options:
            if option == '':
                pass
            elif re.search('{}'.format(option), target):
                return self.equivalencies[cmd_key][option]
        return {'equivalent': target}

    def get_next_action(self, state: State) -> Action:
        command = state.command
        for cmd in self.equivalencies:
            if command.startswith(cmd):
                return self.__build_suggestion(command, self.equivalencies[cmd], cmd)
        return Action(suggested_command=NOOP_COMMAND)

def __build_suggestion(self, command, options, cmd_key) -> any:
    params: list[Tuple(str)] = []
    suggestion: str = None
    explanations: list[str] = []
    tokens: list[str] = command.split()
    idx = 0
    max_idx = len(tokens) - 1
    while idx <= max_idx:
        token: str = tokens[idx]
        if re.match('-([\\w_-]+)', token):
            if idx < max_idx and (not re.match('-([\\w_-]+)', tokens[idx + 1])):
                next_token = tokens[idx + 1]
                params.append((token[1:], next_token))
                idx = idx + 1
            else:
                params.append((token[1:], None))
        elif token != cmd_key:
            params.append((None, token))
        idx = idx + 1
    if '' in options:
        suggestion = self.equivalencies[cmd_key]['']['equivalent']
    else:
        suggestion = cmd_key
    for opt, arg in params:
        if opt is not None:
            if opt[0] == '-' or len(opt) == 1:
                equivalency = self.__get_equavalency(opt, options, cmd_key)
                if equivalency['equivalent']:
                    suggestion = f'{suggestion} {equivalency['equivalent']}'
                    if 'explanation' in equivalency:
                        explanations.append(equivalency['explanation'])
                else:
                    explanations.append(f'The -{opt} flag is not available on USS')
            else:
                for char in opt:
                    equivalency = self.__get_equavalency(char, options, cmd_key)
                    if equivalency['equivalent']:
                        suggestion = f'{suggestion} {equivalency['equivalent']}'
                        if 'explanation' in equivalency:
                            explanations.append(equivalency['explanation'])
                    else:
                        explanations.append(f'The -{char} flag is not available on USS')
        if arg is not None:
            suggestion = f'{suggestion} {arg}'
    if suggestion is not None:
        return Action(suggested_command=suggestion, confidence=1, description='\n'.join(explanations))
    else:
        return Action(suggested_command=NOOP_COMMAND, description=None)

class HowDoIAgent(Agent):

    def __init__(self):
        super(HowDoIAgent, self).__init__()
        inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
        self.store = Datastore(inifile_path)
        self.questionIdentifier = QuestionDetection()

    def compute_simple_token_similarity(self, src_sequence, tgt_sequence):
        src_tokens = set([x.lower().strip() for x in src_sequence.split()])
        tgt_tokens = set([x.lower().strip() for x in tgt_sequence.split()])
        return len(src_tokens & tgt_tokens) / len(src_tokens)

    def get_next_action(self, state: State) -> Action:
        logger.info('================== In HowDoI Bot:get_next_action ========================')
        logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
        logger.info('============================================================================')
        is_question = self.questionIdentifier.is_question(state.command)
        if not is_question:
            return Action(suggested_command=state.command, confidence=0.0)
        apis: OrderedDict = self.store.get_apis()
        helpWasFound = False
        for provider in apis:
            if provider == 'manpages':
                logger.info(f"Skipping search provider 'manpages'")
                continue
            thisAPI: Provider = apis[provider]
            if not thisAPI.can_run_on_this_os():
                logger.info(f"Skipping search provider '{provider}'")
                logger.info(f'==> Excluded on platforms: {str(thisAPI.get_excludes())}')
                continue
            logger.info(f"Processing search provider '{provider}'")
            if thisAPI.has_variants():
                logger.info(f'==> Has search variants: {str(thisAPI.get_variants())}')
                variants: List = thisAPI.get_variants()
            else:
                logger.info(f'==> Has no search variants')
                variants: List = [None]
            for variant in variants:
                if variant is not None:
                    logger.info(f"==> Searching variant '{variant}'")
                    data = self.store.search(state.command, service=provider, size=1, searchType=variant)
                else:
                    data = self.store.search(state.command, service=provider, size=1)
                if data:
                    logger.info(f'==> Success!!! Found a result in the {thisAPI}')
                    searchResult = thisAPI.extract_search_result(data)
                    manpages = self.store.search(searchResult, service='manpages', size=5)
                    if manpages:
                        logger.info('==> Success!!! found relevant manpages.')
                        command = manpages['commands'][-1]
                        confidence = manpages['dists'][-1]
                        logger.info('==> Command: {} \t Confidence:{}'.format(command, confidence))
                        suggested_command = 'man {}'.format(command)
                        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I did little bit of Internet searching for you, ').append(f'and found this in the {thisAPI}:\n').info().append(thisAPI.get_printable_output(data)).warning().append('Do you want to try: man {}'.format(command)).to_console()
                        helpWasFound = True
                        break
            if helpWasFound:
                break
        if not helpWasFound:
            logger.info('Failure: Unable to be helpful')
            logger.info('============================================================================')
            suggested_command = NOOP_COMMAND
            description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"Sorry. It looks like you have stumbled across a problem that even the Internet doesn't have answer to.\n").info().append(f'Have you tried turning it OFF and ON again. ;)').to_console()
            confidence = 0.0
        return Action(suggested_command=suggested_command, description=description, confidence=confidence)

def compute_simple_token_similarity(self, src_sequence, tgt_sequence):
    src_tokens = set([x.lower().strip() for x in src_sequence.split()])
    tgt_tokens = set([x.lower().strip() for x in tgt_sequence.split()])
    return len(src_tokens & tgt_tokens) / len(src_tokens)

class GPT3(Agent):

    def __init__(self):
        super(GPT3, self).__init__()
        self._gpt3_api = self.__init_gpt3_api__()

    def __init_gpt3_api__(self):
        current_directory = str(Path(__file__).parent.absolute())
        path_to_gpt3_key = os.path.join(current_directory, 'openai_api.key')
        path_to_gpt3_prompts = os.path.join(current_directory, 'prompt.json')
        gpt3_key = open(path_to_gpt3_key, 'r').read()
        gpt3_prompts = json.load(open(path_to_gpt3_prompts, 'r'))
        gpt3_api = GPT(temperature=0)
        gpt3_api.set_api_key(gpt3_key)
        for prompt in gpt3_prompts:
            ip, op = (prompt['input'], prompt['output'])
            example = Example(ip, op)
            gpt3_api.add_example(example)
        return gpt3_api

    def get_next_action(self, state: State) -> Action:
        command = state.command
        command = command[:1000]
        try:
            response = self._gpt3_api.get_top_reply(command, strip_output_suffix=True)
            response = response.strip()
            return Action(suggested_command=response, execute=False, description='Currently the GPT-3 skill does not provide an explanation. Got an idea? Contribute to CLAI!', confidence=0.0)
        except Exception as ex:
            return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

def get_next_action(self, state: State) -> Action:
    command = state.command
    command = command[:1000]
    try:
        response = self._gpt3_api.get_top_reply(command, strip_output_suffix=True)
        response = response.strip()
        return Action(suggested_command=response, execute=False, description='Currently the GPT-3 skill does not provide an explanation. Got an idea? Contribute to CLAI!', confidence=0.0)
    except Exception as ex:
        return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

class KubeTracker:

    def __init__(self):
        self.domain = open(_path_to_domain_file, mode='r', encoding='utf-8-sig').read()
        self.template = open(_path_to_problem_template, mode='r', encoding='utf-8-sig').read()
        self.obs = []
        self.goal = None
        self.local_port = None
        self.host_port = None
        self.yaml = None
        self.namespace = None
        self.cluster_name = None
        self.protocol = None
        self.name = None
        self.tag = None
        self.image_to_remove = None

    def parse_command(self, command: str, stdout: str):
        if 'docker build' in command:
            temp = command.split(':')
            self.name = temp[0].split(' ')[-1]
            self.tag = temp[1].split(' ')[0]
            self.refresh_observations()
            self.add_observation('(docker-build)')
        elif 'docker run' in command:
            self.add_observation('(docker-run)')
        elif 'ibmcloud ks clusters' in command:
            lines = stdout.split('\n')
            flag = False
            for line in lines:
                if flag:
                    self.cluster_name = line.strip().split(' ')[0].strip()
                    break
                if line.startswith('Name'):
                    flag = True
        elif 'ibmcloud account show' in command:
            if 'PAYG' not in stdout:
                self.protocol = 'NodePort'
        elif 'ibmcloud cr namespaces' in command:
            self.namespace = re.findall('Namespace\\s+\\n\\w+', stdout)[0].strip().split('\n')[-1]
        else:
            pass

    def add_observation(self, obs: str):
        self.obs.append(obs)
        return self

    def get_observations(self) -> list:
        return self.obs

    def refresh_observations(self):
        self.obs = ['set-state']
        return self

    def set_goal(self, utterance: str):
        if utterance == 'deploy to kube':
            self.goal = '(deployed)'
        elif utterance == 'run Dockerfile':
            self.goal = '(docker_running)'
        elif utterance == 'build yaml':
            self.goal = '(known yaml)'
        else:
            pass
        return self

def parse_command(self, command: str, stdout: str):
    if 'docker build' in command:
        temp = command.split(':')
        self.name = temp[0].split(' ')[-1]
        self.tag = temp[1].split(' ')[0]
        self.refresh_observations()
        self.add_observation('(docker-build)')
    elif 'docker run' in command:
        self.add_observation('(docker-run)')
    elif 'ibmcloud ks clusters' in command:
        lines = stdout.split('\n')
        flag = False
        for line in lines:
            if flag:
                self.cluster_name = line.strip().split(' ')[0].strip()
                break
            if line.startswith('Name'):
                flag = True
    elif 'ibmcloud account show' in command:
        if 'PAYG' not in stdout:
            self.protocol = 'NodePort'
    elif 'ibmcloud cr namespaces' in command:
        self.namespace = re.findall('Namespace\\s+\\n\\w+', stdout)[0].strip().split('\n')[-1]
    else:
        pass

class KubeExe(KubeTracker):

    def __init__(self):
        super().__init__()
        self.refresh_observations()

    def get_plan(self) -> list:
        problem = copy.deepcopy(self.template).replace('<GOAL>', self.goal)
        plan = get_plan_from_pr2plan(domain=self.domain, problem=problem, obs=self.get_observations())
        return plan

    def execute_action(self, action: str) -> str:
        try:
            command = getattr(self, action.replace('-', '_'))()
            if command:
                return command
        except Exception as e:
            print(e)

    def set_state(self):
        if not self.host_port:
            self.host_port = '8085'
        if not self.name:
            self.name = 'app'
        if not self.tag:
            self.tag = 'v1'
        return None

    def docker_build(self):
        command = 'docker build -t {}:{} .'.format(self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def dockerfile_read(self):
        with open('Dockerfile', 'r') as f:
            dockerfile_contents = f.read()
        self.local_port = re.findall('EXPOSE\\s[0-9]+', dockerfile_contents)[0].strip().split(' ')[-1].strip()
        return None

    def docker_run(self):
        command = 'docker run -i -p {}:{} -d {}:{}'.format(self.host_port, self.local_port, self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0)

    def ibmcloud_login(self):
        command = 'ibmcloud login'
        return Action(suggested_command=command, confidence=1.0)

    def ibmcloud_cr_login(self):
        command = 'ibmcloud cr login'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def get_namespace(self):
        command = 'ibmcloud cr namespaces'
        return None

    def docker_tag_for_ibmcloud(self):
        if not self.namespace:
            self.namespace = '<enter-namespace>'
        command = 'docker tag {}:{} us.icr.io/{}/{}:{}'.format(self.name, self.tag, self.namespace, self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def docker_push(self):
        if not self.namespace:
            self.namespace = '<enter-namespace>'
        command = 'docker push us.icr.io/{}/{}:{}'.format(self.namespace, self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def list_images(self):
        command = 'ibmcloud cr image-list'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def get_image_name_to_delete(self):
        return None

    def ibmcloud_delete_image(self):
        command = 'ibmcloud cr image-rm us.icr.io/{}/'.format(self.namespace, self.image_to_remove)
        return Action(suggested_command=command, confidence=1.0)

    def check_account_free(self):
        command = 'ibmcloud account show'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def check_account_paid(self):
        command = 'ibmcloud account show'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def set_protocol(self):
        return None

    def ask_protocol(self):
        description = 'Do you want to use NodePort protocol?'
        return Action(suggested_command=NOOP_COMMAND, description=description, confidence=1.0, execute=False)

    def build_yaml(self):
        app_yaml = open(_path_to_yaml_temnplate, 'r').read()
        app_yaml = app_yaml.replace('{name}', self.name).replace('{tag}', self.tag).replace('{namespace}', self.namespace).replace('{protocol}', self.protocol).replace('{host_port}', self.host_port).replace('{local_port}', self.local_port)
        with open(_real_path + '/app.yaml', 'w') as f:
            f.write(app_yaml)
        self.yaml = app_yaml
        return Action(suggested_command=NOOP_COMMAND, description=self.yaml)

    def get_set_cluster_config(self):
        if not self.cluster_name:
            self.cluster_name = '<enter-cluster-name>'
        command = 'ibmcloud ks cluster-config {} | grep -e "export" | echo'.format(self.cluster_name)
        return Action(suggested_command=command, confidence=1.0)

    def kube_deploy(self):
        command = 'kubectl apply -f {}'.format(_path_to_yaml_temnplate)
        return Action(suggested_command=command, confidence=1.0)

def dockerfile_read(self):
    with open('Dockerfile', 'r') as f:
        dockerfile_contents = f.read()
    self.local_port = re.findall('EXPOSE\\s[0-9]+', dockerfile_contents)[0].strip().split(' ')[-1].strip()
    return None

def get_plan_from_pr2plan(domain: str, problem: str, obs: list, q: list=None) -> list:
    try:
        obs_format = '\n'.join(['({})'.format(o) for o in obs])
        output = requests.put(_pr2plan_hostname + '/solve', json={'domain': domain, 'problem': problem, 'obs': obs_format}, timeout=3).json()
        plan = [action.strip()[1:-4] if '_1' in action else action[1:-2] for action in output['fd-output'].strip().split('\n')[:-1]]
        remaining_plan = ['set-state']
        for action in plan[::-1]:
            if 'explain_obs' in action:
                pass
            else:
                remaining_plan.insert(1, action)
        return remaining_plan
    except Exception as e:
        return None

class HelpMeAgent(Agent):

    def __init__(self):
        super(HelpMeAgent, self).__init__()
        inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
        self.store = Datastore(inifile_path)

    def compute_simple_token_similarity(self, src_sequence, tgt_sequence):
        src_tokens = set([x.lower().strip() for x in src_sequence.split()])
        tgt_tokens = set([x.lower().strip() for x in tgt_sequence.split()])
        return len(src_tokens & tgt_tokens) / len(src_tokens)

    def compute_confidence(self, query, forum, manpage):
        """
        Computes the confidence based on query, stack-exchange post answer and manpage

        Algorithm:
            1. Compute token-wise similarity b/w query and forum text
            2. Compute token-wise similarity b/w forum text and manpage description
            3. Return product of two similarities


        Args:
            query (str): standard error captured in state variable
            forum (str): answer text from most relevant stack exchange post w.r.t query
            manpage (str): manpage description for most relevant manpage w.r.t. forum

        Returns:
             confidence (float): confidence on the returned manpage w.r.t. query
        """
        query_forum_similarity = self.compute_simple_token_similarity(query, forum[0]['Content'])
        forum_manpage_similarity = self.compute_simple_token_similarity(forum[0]['Answer'], manpage)
        confidence = query_forum_similarity * forum_manpage_similarity
        return confidence

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

    def post_execute(self, state: State) -> Action:
        logger.info('==================== In Helpme Bot:post_execute ============================')
        logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
        logger.info('============================================================================')
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        apis: OrderedDict = self.store.get_apis()
        helpWasFound = False
        for provider in apis:
            if provider == 'manpages':
                logger.info(f"Skipping search provider 'manpages'")
                continue
            thisAPI: Provider = apis[provider]
            if not thisAPI.can_run_on_this_os():
                logger.info(f"Skipping search provider '{provider}'")
                logger.info(f'==> Excluded on platforms: {str(thisAPI.get_excludes())}')
                continue
            logger.info(f"Processing search provider '{provider}'")
            if thisAPI.has_variants():
                logger.info(f'==> Has search variants: {str(thisAPI.get_variants())}')
                variants: List = thisAPI.get_variants()
            else:
                logger.info(f'==> Has no search variants')
                variants: List = [None]
            for variant in variants:
                if variant is not None:
                    logger.info(f"==> Searching variant '{variant}'")
                    data = self.store.search(state.stderr, service=provider, size=1, searchType=variant)
                else:
                    data = self.store.search(state.stderr, service=provider, size=1)
                if data:
                    apiString = str(thisAPI)
                    if variant is not None:
                        apiString = f"{apiString} '{variant}' variant"
                    logger.info(f'==> Success!!! Found a result in the {apiString}')
                    searchResult = thisAPI.extract_search_result(data)
                    manpages = self.store.search(searchResult, service='manpages', size=5)
                    if manpages:
                        logger.info('==> Success!!! found relevant manpages.')
                        command = manpages['commands'][-1]
                        confidence = manpages['dists'][-1]
                        confidence = 1.0
                        logger.info('==> Command: {} \t Confidence:{}'.format(command, confidence))
                        suggested_command = 'man {}'.format(command)
                        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I did little bit of Internet searching for you, ').append(f'and found this in the {thisAPI}:\n').info().append(thisAPI.get_printable_output(data)).warning().append('Do you want to try: man {}'.format(command)).to_console()
                        helpWasFound = True
                        break
            if helpWasFound:
                break
        if not helpWasFound:
            logger.info('Failure: Unable to be helpful')
            logger.info('============================================================================')
            suggested_command = NOOP_COMMAND
            description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"Sorry. It looks like you have stumbled across a problem that even the Internet doesn't have answer to.\n").info().append(f'Have you tried turning it OFF and ON again. ;)').to_console()
            confidence = 0.0
        return Action(suggested_command=suggested_command, description=description, confidence=confidence)

def compute_simple_token_similarity(self, src_sequence, tgt_sequence):
    src_tokens = set([x.lower().strip() for x in src_sequence.split()])
    tgt_tokens = set([x.lower().strip() for x in tgt_sequence.split()])
    return len(src_tokens & tgt_tokens) / len(src_tokens)

class Voice(Agent):

    def __init__(self):
        super(Voice, self).__init__()
        self._api_filename = 'openai_api.key'
        self._priming_filename = 'priming.json'
        self._tmp_filepath = os.path.join(tempfile.gettempdir(), 'tts.mp3')
        self._gpt_api = self.__init_gpt_api__()
        self.__prime_gpt_model__()

    def __init_gpt_api__(self):
        curdir = str(Path(__file__).parent.absolute())
        key_filepath = os.path.join(curdir, self._api_filename)
        with open(key_filepath, 'r') as f:
            key = f.read()
        gpt_api = GPT()
        gpt_api.set_api_key(key)
        return gpt_api

    def __prime_gpt_model__(self):
        curdir = str(Path(__file__).parent.absolute())
        priming_filepath = os.path.join(curdir, self._priming_filename)
        with open(priming_filepath, 'r') as f:
            priming_examples = json.load(f)
        for priming_set in priming_examples:
            ip, op = (priming_set['input'], priming_set['output'])
            example = Example(ip, op)
            self._gpt_api.add_example(example)

    def summarize_output(self, state):
        stderr = str(state.stderr)
        prompt = stderr.split('\n')[0]
        gpt_summary = self._gpt_api.get_top_reply(prompt, strip_output_suffix=True)
        summary = f'error. {gpt_summary}'
        return summary

    def synthesize(self, text):
        """ Converts text to audio and saves to temp file """
        tts = gTTS(text, lang='en', lang_check=False)
        tts.save(self._tmp_filepath)

    def speak(self):
        subprocess.Popen(['nohup', 'ffplay', '-nodisp', '-autoexit', '-nostats', '-hide_banner', '-loglevel', 'warning', self._tmp_filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def post_execute(self, state: State) -> Action:
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        text_to_speak = self.summarize_output(state)
        self.synthesize(text_to_speak)
        self.speak()
        return Action(suggested_command=NOOP_COMMAND, confidence=0.01)

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

def summarize_output(self, state):
    stderr = str(state.stderr)
    prompt = stderr.split('\n')[0]
    gpt_summary = self._gpt_api.get_top_reply(prompt, strip_output_suffix=True)
    summary = f'error. {gpt_summary}'
    return summary

class Provider:
    base_uri: str = ''
    excludes: list = []

    def __init__(self, name: str, description: str, section: dict):
        self.name = name
        self.description = description
        api_value: str = section.get('api')
        self.base_uri = api_value if api_value.endswith('/') else api_value + '/'
        if 'exclude' in section.keys():
            self.excludes = [excludeTarget.lower() for excludeTarget in section.get('exclude').split()]
        else:
            self.excludes = []
        if 'variants' in section.keys():
            self.variants = [variant.upper() for variant in section.get('variants').split()]
        else:
            self.variants = []

    def __str__(self) -> str:
        return self.description

    def __log_info__(self, message):
        logger.info(f'{self.name}: {message}')

    def __log_warning__(self, message):
        logger.warning(f'{self.name}: {message}')

    def __log_debug__(self, message):
        logger.debug(f'{self.name}: {message}')

    def __log_json__(self, data):
        output: List[str] = ['']
        getters: List[str] = []
        is_json_data: bool = False
        if isinstance(data, Request):
            output.append(f'{data.method} --> {data.url}')
            getters = ['files', 'data', 'json', 'params', 'auth', 'cookies', 'hooks']
        elif isinstance(data, Response):
            output.append(f'RESPONSE[{data.status_code}] <-- {data.url}')
            getters = ['apparent_encoding', 'cookies', 'elapsed', 'encoding', 'ok', 'status_code', 'reason', 'content']
        if data.headers.keys():
            output.append('.--[Headers]'.ljust(80, '-'))
            for key in data.headers.keys():
                if key == 'Content-Type':
                    if '/json' in data.headers[key]:
                        is_json_data = True
                line_header = f'|    {key}: '
                print_data: str = str(data.headers[key])
                if len(print_data) > 64:
                    print_data = f'{print_data[:50]} ... {print_data[-10:]}'
                output.append(f'{line_header}{print_data}')
            output.append('`'.ljust(80, '-'))
        for method in getters:
            result = getattr(data, method)
            if method == 'content' and is_json_data:
                outstr = json.dumps(json.loads(result), indent=2)
                output.append(f'{method}: ' + outstr.replace('\n', '\n\t'))
            else:
                print_data: str = str(result)
                line_header = f'{method}: '
                if len(print_data) > 64:
                    print_data = f'{print_data[:50]} ... {print_data[-10:]}'
                output.append(f'{line_header}{print_data}')
        self.__log_info__('\n\t'.join(output))

    def __set_default_values__(self, args: dict, **kwargs) -> dict:
        for key in kwargs.keys():
            if key not in args:
                args[key] = kwargs[key]
        return args

    def __send_request__(self, method: str, uri: str, **kwargs) -> Response:
        kwargs = self.__set_default_values__(kwargs, headers={'Content-Type': 'application/json', 'Accept': '*/*'}, data=None, params=None)
        request: Request = Request(method, uri.rstrip('/'), headers=kwargs['headers'], data=kwargs['data'], params=kwargs['params'])
        self.__log_json__(request)
        session: Session = Session()
        response: Response = session.send(request=request.prepare())
        self.__log_json__(response)
        return response

    def __send_get_request__(self, uri: str, **kwargs):
        return self.__send_request__(method='GET', uri=uri, **kwargs)

    def __send_post_request__(self, uri: str, **kwargs):
        return self.__send_request__(method='POST', uri=uri, **kwargs)

    def get_excludes(self) -> list:
        """Returns a list of operating systems that the search provider cannot
          be run from
        """
        return self.excludes

    def has_variants(self) -> bool:
        """Returns `True` if this search provider has more than one search
          variant
        """
        return len(self.variants) > 0

    def get_variants(self) -> list:
        """Returns a list of search variants supported by this search provider
        """
        return self.variants

    def can_run_on_this_os(self) -> bool:
        """Returns True if this search provider can be used on the client OS
        """
        if not self.excludes:
            return True
        os_name: str = os.uname().sysname.lower()
        return os_name not in self.excludes

    @abc.abstractclassmethod
    def extract_search_result(self, data: List[Dict]) -> str:
        """Given the result of an API search, extract the search result from it
        """
        pass

    @abc.abstractclassmethod
    def get_printable_output(self, data: List[Dict]) -> str:
        """Extract the result string from the data returned by an API search
        """
        pass

    @abc.abstractclassmethod
    def call(self, query: str, limit: int=1, **kwargs):
        """Perform a query on the API
        """
        pass

def has_variants(self) -> bool:
    """Returns `True` if this search provider has more than one search
          variant
        """
    return len(self.variants) > 0

class RLTKBandit(Orchestrator):

    def __init__(self):
        super(RLTKBandit, self).__init__()
        self._config_filepath = os.path.join(Path(__file__).parent.absolute(), 'config.yml')
        self._bandit_config_filepath = os.path.join(Path(__file__).parent.absolute(), 'bandit_config.json')
        self._noop_confidence = None
        self._agent = None
        self._n_actions = None
        self._action_order = None
        self._warm_start = None
        self._warm_start_type = None
        self._warm_start_kwargs = None
        self._reward_match_threshold = None
        self.load_bandit_state()
        self.load_state()
        self.warm_start_orchestrator()

    def load_bandit_state(self):
        with open(self._bandit_config_filepath, 'r') as conf_file:
            bandit_config = json.load(conf_file)
        self._noop_confidence = bandit_config['noop_confidence']
        self._warm_start = bandit_config['warm_start']
        self._warm_start_type = bandit_config['warm_start_config']['type']
        self._warm_start_kwargs = bandit_config['warm_start_config']['kwargs']
        self._reward_match_threshold = bandit_config.get('reward_match_threshold', 0.7)

    def get_orchestrator_state(self):
        state = {'agent': self._agent, 'action_order': self._action_order, 'warm_start': self._warm_start}
        return state

    def load_state(self):
        state = self.load()
        default_action_order = {self.noop_command: 0}
        self._agent = state.get('agent', None)
        if self._agent is None:
            self._agent = instantiate_from_file(self._config_filepath)
        self._action_order = state.get('action_order', None)
        if self._action_order is None:
            self._action_order = default_action_order
        self._n_actions = self._agent.num_actions
        self._warm_start = state.get('warm_start', self._warm_start)

    def warm_start_orchestrator(self):
        """
        Warm starts the orchestrator (pre-trains the weights) to suit a
        particular profile
        """

        def noop_setup():
            profile = 'noop-always'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'noop_position': 0}
            return (profile, kwargs)

        def ignore_skill_setup(skill_name):
            self.__add_to_action_order__(skill_name)
            profile = 'ignore-skill'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'skill_idx': self._action_order[skill_name]}
            return (profile, kwargs)

        def max_orchestrator_setup():
            profile = 'max-orchestrator'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions}
            return (profile, kwargs)

        def preferred_skill_orchestrator_setup(advantage_skill, disadvantage_skill):
            self.__add_to_action_order__(advantage_skill)
            self.__add_to_action_order__(disadvantage_skill)
            profile = 'preferred-skill'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'advantage_skillidx': self._action_order[advantage_skill], 'disadvantage_skillidx': self._action_order[disadvantage_skill]}
            return (profile, kwargs)
        try:
            warm_start_methods = {'noop': noop_setup, 'ignore-skill': ignore_skill_setup, 'max-orchestrator': max_orchestrator_setup, 'preferred-skill': preferred_skill_orchestrator_setup}
            method = warm_start_methods[self._warm_start_type.lower()]
            profile, kwargs = method(**self._warm_start_kwargs)
            tids, contexts, arm_rewards = warm_start_datagen.get_warmstart_data(profile, **kwargs)
            self._agent.warm_start(tids, arm_rewards, contexts=contexts)
            self._warm_start = False
            self.save()
        except Exception as err:
            logger.warning('Exception in warm starting orchestrator. Error: ' + str(err))
            raise err

    def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str):
        if not candidate_actions:
            return None
        if isinstance(candidate_actions, Action):
            candidate_actions = [candidate_actions]
        context = self.__build_context__(candidate_actions)
        action_idx = self._agent.choose(t_id=command.command_id, context=context, num_arms=1)
        suggested_action = self.__choose_action__(action_idx[0], candidate_actions)
        if suggested_action is None:
            suggested_action = Action(suggested_command=command.command)
        return suggested_action

    def __build_context__(self, candidate_actions: Optional[List[Union[Action, List[Action]]]]) -> np.array:
        context = [0.0] * self._n_actions
        noop_pos = self._action_order[self.noop_command]
        context[noop_pos] = self._noop_confidence
        for action in candidate_actions:
            self.__add_to_action_order__(action.agent_owner)
            pos = self._action_order[action.agent_owner]
            conf = self.__calculate_confidence__(action)
            context[pos] = conf
        return np.array(context, dtype=np.float)

    def __add_to_action_order__(self, agent_name):
        if agent_name in self._action_order:
            return
        max_action_order = max(self._action_order.values())
        self._action_order[agent_name] = max_action_order + 1

    def __choose_action__(self, action_idx: int, candidate_actions: Optional[List[Union[Action, List[Action]]]]):
        suggested_agent = None
        for agent_name, agent_idx in self._action_order.items():
            if agent_idx == action_idx:
                suggested_agent = agent_name
                break
        if suggested_agent == self.noop_command or suggested_agent is None:
            return None
        for action in candidate_actions:
            if action.agent_owner == suggested_agent:
                return action
        return None

    def record_transition(self, prev_state: TerminalReplayMemoryComplete, current_state_pre: TerminalReplayMemory):
        try:
            prev_state_pre = prev_state.pre_replay
            prev_state_post = prev_state.post_replay
            if prev_state_pre.command.action_suggested is None or prev_state_post.command.action_suggested is None or prev_state_post.command.action_suggested.suggested_command == self.noop_command:
                return
            reward = float(prev_state_post.command.suggested_executed)
            currently_executed_command = current_state_pre.command.command
            all_the_stuff_from_last_execution = prev_state_pre.command.action_suggested.suggested_command + prev_state_pre.command.action_suggested.description + prev_state_post.command.action_suggested.description
            base = set(currently_executed_command.split())
            reference = set(all_the_stuff_from_last_execution.split())
            match_score = len(base & reference) / len(base)
            reward += float(match_score > self._reward_match_threshold)
            self._agent.observe(prev_state.post_replay.command.command_id, reward)
        except Exception as err:
            logger.warning(f'Error in record_transition of bandit orchestrator. Error: {err}')

def record_transition(self, prev_state: TerminalReplayMemoryComplete, current_state_pre: TerminalReplayMemory):
    try:
        prev_state_pre = prev_state.pre_replay
        prev_state_post = prev_state.post_replay
        if prev_state_pre.command.action_suggested is None or prev_state_post.command.action_suggested is None or prev_state_post.command.action_suggested.suggested_command == self.noop_command:
            return
        reward = float(prev_state_post.command.suggested_executed)
        currently_executed_command = current_state_pre.command.command
        all_the_stuff_from_last_execution = prev_state_pre.command.action_suggested.suggested_command + prev_state_pre.command.action_suggested.description + prev_state_post.command.action_suggested.description
        base = set(currently_executed_command.split())
        reference = set(all_the_stuff_from_last_execution.split())
        match_score = len(base & reference) / len(base)
        reward += float(match_score > self._reward_match_threshold)
        self._agent.observe(prev_state.post_replay.command.command_id, reward)
    except Exception as err:
        logger.warning(f'Error in record_transition of bandit orchestrator. Error: {err}')

class GPT:
    """The main class for a user to interface with the OpenAI API.

    A user can add examples and set parameters of the API request.
    """

    def __init__(self, engine='davinci', temperature=0.5, max_tokens=100, input_prefix='input: ', input_suffix='\n', output_prefix='output: ', output_suffix='\n\n', append_output_prefix_to_query=False):
        self.examples = {}
        self.engine = engine
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.input_prefix = input_prefix
        self.input_suffix = input_suffix
        self.output_prefix = output_prefix
        self.output_suffix = output_suffix
        self.append_output_prefix_to_query = append_output_prefix_to_query
        self.stop = (output_suffix + input_prefix).strip()

    def set_api_key(self, key):
        """ Sets OpenAI API key """
        openai.api_key = key

    def add_example(self, ex):
        """Adds an example to the object.

        Example must be an instance of the Example class.
        """
        assert isinstance(ex, Example), 'Please create an Example object.'
        self.examples[ex.get_id()] = ex

    def delete_example(self, id):
        """Delete example with the specific id."""
        if id in self.examples:
            del self.examples[id]

    def get_example(self, id):
        """Get a single example."""
        return self.examples.get(id, None)

    def get_all_examples(self):
        """Returns all examples as a list of dicts."""
        return {k: v.as_dict() for k, v in self.examples.items()}

    def get_prime_text(self):
        """Formats all examples to prime the model."""
        return ''.join([self.format_example(ex) for ex in self.examples.values()])

    def get_engine(self):
        """Returns the engine specified for the API."""
        return self.engine

    def get_temperature(self):
        """Returns the temperature specified for the API."""
        return self.temperature

    def get_max_tokens(self):
        """Returns the max tokens specified for the API."""
        return self.max_tokens

    def craft_query(self, prompt):
        """Creates the query for the API request."""
        q = self.get_prime_text() + self.input_prefix + prompt + self.input_suffix
        if self.append_output_prefix_to_query:
            q = q + self.output_prefix
        return q

    def submit_request(self, prompt):
        """Calls the OpenAI API with the specified parameters."""
        response = openai.Completion.create(engine=self.get_engine(), prompt=self.craft_query(prompt), max_tokens=self.get_max_tokens(), temperature=self.get_temperature(), top_p=1, n=1, stream=False, stop=self.stop)
        return response

    def get_top_reply(self, prompt, strip_output_suffix=False):
        """Obtains the best result as returned by the API."""
        response = self.submit_request(prompt)
        response = response['choices'][0]['text']
        if strip_output_suffix:
            response = response[len(self.output_prefix):] if response.startswith(self.output_prefix) else response
        return response

    def format_example(self, ex):
        """Formats the input, output pair."""
        return self.input_prefix + ex.get_input() + self.input_suffix + self.output_prefix + ex.get_output() + self.output_suffix

def __init__(self, engine='davinci', temperature=0.5, max_tokens=100, input_prefix='input: ', input_suffix='\n', output_prefix='output: ', output_suffix='\n\n', append_output_prefix_to_query=False):
    self.examples = {}
    self.engine = engine
    self.temperature = temperature
    self.max_tokens = max_tokens
    self.input_prefix = input_prefix
    self.input_suffix = input_suffix
    self.output_prefix = output_prefix
    self.output_suffix = output_suffix
    self.append_output_prefix_to_query = append_output_prefix_to_query
    self.stop = (output_suffix + input_prefix).strip()

class PendingActions:

    def __init__(self, command_id: str, pending_actions: List[Action]):
        self.command_id = command_id
        self.current_action = 0
        self.pending_actions = pending_actions

    def next(self) -> Optional[Action]:
        if self.current_action >= len(self.pending_actions):
            return None
        action_to_return = self.pending_actions[self.current_action]
        self.current_action += 1
        action_to_return.pending_actions = self.current_action < len(self.pending_actions)
        return action_to_return

def next(self) -> Optional[Action]:
    if self.current_action >= len(self.pending_actions):
        return None
    action_to_return = self.pending_actions[self.current_action]
    self.current_action += 1
    action_to_return.pending_actions = self.current_action < len(self.pending_actions)
    return action_to_return

class EmulatorPresenter:

    def __init__(self, emulator_docker_bridge: EmulatorDockerBridge, on_skills_ready, on_server_running, on_server_stopped):
        self.server_running = False
        self.server_process = None
        self.current_active_skill = ''
        self.emulator_docker_bridge = emulator_docker_bridge
        self.on_skills_ready = on_skills_ready
        self.on_server_running = on_server_running
        self.on_server_stopped = on_server_stopped
        self.log_value = ''
        self.log_read = None

    @staticmethod
    def __get_base_path():
        root_path = os.getcwd()
        if 'bin' in root_path:
            return '../'
        return '.'

    def select_skill(self, skill_name: str):
        if skill_name == self.current_active_skill:
            return
        self._send_select(skill_name)
        self._send_unselect(self.current_active_skill)
        self.request_skills()

    def request_skills(self):
        self.emulator_docker_bridge.request_skills()

    def send_message(self, message):
        self.emulator_docker_bridge.send_message(message)

    def attach_log(self, chunked_read):
        self.log_read = chunked_read

    def _send_select(self, skill_name: str):
        self.emulator_docker_bridge.select_skill(skill_name)

    def _send_unselect(self, skill_name: str):
        self.emulator_docker_bridge.unselect_skill(skill_name)

    def run_server(self):
        self.emulator_docker_bridge.start()
        self.server_running = True
        self.on_server_running()
        self.request_skills()

    def stop_server(self):
        print(f'is server running {self.server_running}')
        if self.server_running:
            self.emulator_docker_bridge.stop_server()
            self.server_running = False
        self.on_server_stopped()

    def refresh_files(self):
        self.emulator_docker_bridge.refresh_files()

    def retrieve_messages(self, add_row):
        reply = self.emulator_docker_bridge.retrieve_message()
        if reply:
            if reply.docker_reply == 'skills':
                skills_as_array = reply.message.splitlines()
                self.on_skills_ready(skills_as_array[2:-1])
            elif reply.docker_reply == 'reply_message':
                info_as_string = reply.info[reply.info.index('{'):]
                info_as_string = info_as_string[:info_as_string.index('\n')]
                print(f'----> {info_as_string}')
                info = InfoDebug(**json.loads(info_as_string))
                add_row(reply.message, info)
            elif reply.docker_reply == 'log':
                self.log_value = self.extract_chunk_log(self.log_value, reply.message)
                if self.log_read:
                    self.log_read(self.log_value)
            else:
                print(f'-----> {reply.docker_reply} : {reply.message}')

    @staticmethod
    def extract_chunk_log(log_value, message):
        if not message:
            return ''
        log_as_list = log_value.split('\n')
        message_as_list = message.split('\n')
        new_log = []
        if log_as_list.__contains__(message_as_list[0]):
            index = log_as_list.index(message_as_list[0])
            new_log = message_as_list[len(log_as_list) - index - 1:]
        else:
            new_log = message_as_list
        return '\n'.join(new_log)

def send_message(self, message):
    self.emulator_docker_bridge.send_message(message)

def _send_select(self, skill_name: str):
    self.emulator_docker_bridge.select_skill(skill_name)

@staticmethod
def extract_chunk_log(log_value, message):
    if not message:
        return ''
    log_as_list = log_value.split('\n')
    message_as_list = message.split('\n')
    new_log = []
    if log_as_list.__contains__(message_as_list[0]):
        index = log_as_list.index(message_as_list[0])
        new_log = message_as_list[len(log_as_list) - index - 1:]
    else:
        new_log = message_as_list
    return '\n'.join(new_log)

class ClaiEmulator:

    def __init__(self, emulator_docker_bridge: EmulatorDockerBridge):
        self.presenter = EmulatorPresenter(emulator_docker_bridge, self.on_skills_ready, self.on_server_running, self.on_server_stopped)
        self.log_window = None

    def launch(self):
        self.root = tk.Tk()
        self.root.wait_visibility(self.root)
        self.title_font = Font(size=16, weight='bold')
        self.bold_font = Font(weight='bold')
        self.root.geometry('900x600')
        style = ttk.Style(self.root)
        style.configure('TLable', bg='black')
        self.add_toolbar(self.root)
        self.add_send_command_box(self.root)
        self.add_list_commands(self.root)
        self.root.protocol('WM_DELETE_WINDOW', lambda root=self.root: self.on_closing(root))
        self.root.createcommand('exit', lambda root=self.root: self.on_closing(root))
        self.root.mainloop()

    def on_closing(self, root):
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            self.presenter.stop_server()
            root.destroy()

    def on_skills_ready(self, skills_as_array: List[str]):
        self.selected_skills_dropmenu.configure(state='active')
        self.selected_skills_dropmenu['menu'].delete(0, 'end')
        for skill in skills_as_array[1:-1]:
            name_skill, active = self.clear_text(skill)
            self.selected_skills_dropmenu['menu'].add_command(label=name_skill, command=tk._setit(self.selected_skills, name_skill))
            if active:
                self.presenter.current_active_skill = self.extract_skill_name(name_skill)[0]
                self.selected_skills.set(name_skill)

    def on_server_running(self):
        self.run_button.configure(image=self.stop_image)
        self.loading_text.set('Starting CLAI. It will take a while')
        self.__listen_messages()

    def on_server_stopped(self):
        self.run_button.configure(image=self.run_image)

    def on_skill_selected(self, *args):
        self.loading_text.set('')
        print(f'new skills {self.selected_skills.get()}')
        skill_name = self.extract_skill_name(self.selected_skills.get())[0]
        self.presenter.select_skill(skill_name)

    def add_detail_label(self, parent: ttk.Frame, title: str, text_value: str, side: str):
        row = ttk.Frame(parent)
        title_label = ttk.Label(parent, text=title, font=self.bold_font, anchor='n', padding=(10, 0, 0, 0))
        title_label.pack(side=side, fill=tk.BOTH)
        row_value = ttk.Label(parent, text=text_value, wraplength=250, anchor='nw')
        if side == tk.LEFT:
            row_value.pack(side=side, fill=tk.BOTH, expand=True)
        else:
            row_value.pack(side=side, fill=tk.BOTH, before=title_label)
        row.pack(side=side, fill=tk.BOTH, expand=True)

    def add_row(self, response: str, info: InfoDebug):
        response = self.clean_message(response)
        toggled_frame = ToggledFrame(self.frame, text=response, relief=tk.RAISED, borderwidth=1)
        toggled_frame.pack(fill='x', expand=1, pady=2, padx=2, anchor='n')
        first_row = ttk.Frame(toggled_frame.sub_frame)
        first_row.pack(fill='x', expand=True)
        self.add_detail_label(first_row, 'Original:', info.command, side=tk.LEFT)
        self.add_detail_label(first_row, 'Id:', info.command_id, side=tk.RIGHT)
        second_row = ttk.Frame(toggled_frame.sub_frame)
        second_row.pack(fill='x', expand=True)
        self.add_detail_label(second_row, 'Description:', self.remove_emoji(info.action_suggested.description), tk.LEFT)
        self.add_detail_label(second_row, 'Confidence:', f'{info.action_suggested.confidence}', tk.RIGHT)
        self.add_detail_label(second_row, 'Force:', f'{info.action_suggested.execute}', tk.RIGHT)
        third_row = ttk.Frame(toggled_frame.sub_frame)
        third_row.pack(fill='x', expand=True)
        self.add_detail_label(third_row, 'Agent:', text_value=info.action_suggested.agent_owner, side=tk.LEFT)
        self.add_detail_label(third_row, 'Sugestion:', text_value=info.action_suggested.suggested_command, side=tk.RIGHT)
        self.add_detail_label(third_row, 'Applied:', text_value=f'{info.already_processed}', side=tk.RIGHT)
        fourth_row = ttk.Frame(toggled_frame.sub_frame)
        fourth_row.pack(fill='x', expand=True)
        process_text = ','.join(list(map(lambda process: process.name, info.processes.last_processes)))
        self.add_detail_label(fourth_row, 'Processes:', text_value=f'{process_text}', side=tk.LEFT)
        post_title_frame = ttk.Frame(toggled_frame.sub_frame)
        post_title_frame.pack(fill='x', expand=True)
        ttk.Label(post_title_frame, text=f'Post execution', anchor='center', font=self.title_font).pack(side=tk.LEFT, padx=10, fill='x', expand=True)
        fifth_row = ttk.Frame(toggled_frame.sub_frame)
        fifth_row.pack(fill='x', expand=True)
        post_description = ''
        post_confidence = 0
        if info.action_post_suggested:
            post_description = info.action_post_suggested.description
            post_confidence = info.action_post_suggested.confidence
        self.add_detail_label(fifth_row, 'Description:', text_value=f'{self.remove_emoji(post_description)}', side=tk.LEFT)
        self.add_detail_label(fifth_row, 'Confidence:', text_value=f'{post_confidence}', side=tk.RIGHT)
        self.root.after(100, self.__scroll_down_after_create)

    def __scroll_down_after_create(self):
        self.canvas.yview_moveto(1.0)

    def add_send_command_box(self, root):
        button_bar_frame = tk.Frame(root, bd=1, relief=tk.RAISED)
        send_button = tk.Button(button_bar_frame, padx=10, text=u'✓', command=self.on_send_click)
        send_button.pack(side=tk.RIGHT, padx=5)
        self.text_input = tk.StringVar()
        send_edit_text = tk.Entry(button_bar_frame, textvariable=self.text_input)
        send_edit_text.bind('<Return>', self.on_enter)
        send_edit_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        button_bar_frame.pack(side=tk.BOTTOM, pady=2, fill=tk.X)

    def add_toolbar(self, root):
        toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        self.add_play_button(toolbar)
        self.add_refresh_button(toolbar)
        self.add_log_button(toolbar)
        self.add_skills_selector(root, toolbar)
        self.add_loading_progress(toolbar)
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def add_skills_selector(self, root, toolbar):
        label = ttk.Label(toolbar, text=u'Skills')
        label.pack(side=tk.LEFT, padx=2)
        self.selected_skills = tk.StringVar(root)
        self.selected_skills.set('')
        self.selected_skills.trace('w', self.on_skill_selected)
        self.selected_skills_dropmenu = tk.OptionMenu(toolbar, self.selected_skills, [])
        self.selected_skills_dropmenu.configure(state='disabled')
        self.selected_skills_dropmenu.pack(side=tk.LEFT, padx=2)

    def add_play_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        self.run_image = tk.PhotoImage(file=f'{path}/run.gif')
        self.stop_image = tk.PhotoImage(file=f'{path}/stop.gif')
        self.run_button = ttk.Button(toolbar, image=self.run_image, command=self.on_run_click)
        self.run_button.pack(side=tk.LEFT, padx=2, pady=2)

    def add_refresh_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        temp_image = Image.open(f'{path}/refresh.png')
        self.refresh_image = ImageTk.PhotoImage(temp_image)
        refresh_button = ttk.Button(toolbar, image=self.refresh_image, command=self.on_refresh_click)
        refresh_button.pack(side=tk.LEFT, padx=2, pady=2)

    def add_log_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        temp_image = Image.open(f'{path}/log.png')
        self.log_image = ImageTk.PhotoImage(temp_image)
        log_button = ttk.Button(toolbar, image=self.log_image, command=self.open_log_window)
        log_button.pack(side=tk.LEFT, padx=2, pady=2)

    def add_loading_progress(self, toolbar):
        self.loading_text = tk.StringVar()
        loading_label = ttk.Label(toolbar, textvariable=self.loading_text)
        loading_label.pack(side=tk.LEFT, padx=2)

    def open_log_window(self):
        if not self.log_window:
            self.log_window = LogWindow(self.root, self.presenter)

    def on_enter(self, event):
        self.send_command(self.text_input.get())

    def on_send_click(self):
        self.send_command(self.text_input.get())

    @staticmethod
    def clean_message(text: str):
        text = text[text.find('\n'):]
        text = re.sub('[[0-9;]*m', '', text)
        return text[:text.find(']0;') - 3]

    def send_command(self, command):
        self.presenter.send_message(command)
        self.text_input.set('')

    def on_run_click(self):
        if not self.presenter.server_running:
            self.presenter.run_server()
        else:
            self.presenter.stop_server()

    def on_refresh_click(self):
        self.presenter.refresh_files()

    @staticmethod
    def on_configure(canvas):
        canvas.configure(scrollregion=canvas.bbox('all'))

    def canvas_resize(self, event, canvas):
        canvas_width = event.width
        canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def add_list_commands(self, root):
        canvas = tk.Canvas(root, borderwidth=0)
        self.frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(root, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        self.canvas_frame = canvas.create_window((4, 4), window=self.frame, anchor='nw')
        canvas.bind('<Configure>', lambda event, canvas=canvas: self.canvas_resize(event, canvas))
        self.frame.bind('<Configure>', lambda event, canvas=canvas: self.on_configure(canvas))
        self.frame.bind_all('<MouseWheel>', lambda event, canvas=canvas: canvas.yview_scroll(-1 * event.delta, 'units'))
        self.canvas = canvas

    @staticmethod
    def clear_text(skill):
        active = '[x]' in skill
        skill_without_tick = skill.replace('[x]\x1b[32m ', '').replace('\x1b[0m', '').replace('[ ]', '').strip()
        return (skill_without_tick, active)

    @staticmethod
    def extract_skill_name(skill):
        installed = '(Installed)' in skill
        return (skill.replace('(Installed)', '').replace('(Not Installed)', '').strip(), installed)

    @staticmethod
    def remove_emoji(description):
        if not description:
            return ''
        char_list = [description[j] for j in range(len(description)) if ord(description[j]) in range(65536)]
        description = ''
        for char in char_list:
            description = description + char
        return description

    def __listen_messages(self):
        self.presenter.retrieve_messages(self.add_row)
        self.root.after(100, self.__listen_messages)

def on_skills_ready(self, skills_as_array: List[str]):
    self.selected_skills_dropmenu.configure(state='active')
    self.selected_skills_dropmenu['menu'].delete(0, 'end')
    for skill in skills_as_array[1:-1]:
        name_skill, active = self.clear_text(skill)
        self.selected_skills_dropmenu['menu'].add_command(label=name_skill, command=tk._setit(self.selected_skills, name_skill))
        if active:
            self.presenter.current_active_skill = self.extract_skill_name(name_skill)[0]
            self.selected_skills.set(name_skill)

def on_skill_selected(self, *args):
    self.loading_text.set('')
    print(f'new skills {self.selected_skills.get()}')
    skill_name = self.extract_skill_name(self.selected_skills.get())[0]
    self.presenter.select_skill(skill_name)

def send_command(self, command):
    self.presenter.send_message(command)
    self.text_input.set('')

