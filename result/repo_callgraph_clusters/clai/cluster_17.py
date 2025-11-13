# Cluster 17

def cp_tree(from_path, to_path):
    print('copying folder from %s to %s' % (from_path, to_path))
    copy_tree(from_path, to_path)
    if is_zos():
        recursively_tag_untagged_files_as_ebcdic(to_path)

def recursively_tag_untagged_files_as_ebcdic(path):
    for file in os.listdir(path):
        filepath = f'{path}{os.path.sep}{file}'
        if os.path.isdir(filepath) and (not os.path.islink(filepath)):
            recursively_tag_untagged_files_as_ebcdic(filepath)
        else:
            try:
                result: CompletedProcess = subprocess.run(['ls', '-T', filepath], encoding='UTF8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                result = result.stdout.strip()
                match = re.match('(?P<type>\\S+)\\s+(?P<encoding>\\S+)\\s+T\\=(?P<tagging>on|off)\\s+(?P<filepath>.*)', result)
                if match:
                    tagging: str = match.group('tagging')
                    if tagging != 'on':
                        os.system(f'chtag -tc 1047 {filepath}')
            except:
                pass

def map_files(files_args) -> List[FileChange]:
    if not files_args:
        return []
    cont = 0
    files = []
    value_to_add = files_args[cont]
    current_file = None
    while value_to_add != 'NoOp':
        if value_to_add.startswith('/'):
            if current_file is not None:
                files.append(current_file)
            current_file = FileChange(filename=value_to_add)
        elif is_status(value_to_add):
            current_file.status.append(map_status(value_to_add))
        elif is_type(value_to_add):
            current_file.file_type = map_type(value_to_add)
        cont += 1
        value_to_add = files_args[cont]
    return files

class CommandRunnerFactory:

    def __init__(self, agent_datasource: AgentDatasource, config_storage: ConfigStorage, server_status_datasource: ServerStatusDatasource, orchestrator_provider: OrchestratorProvider):
        self.server_status_datasource = server_status_datasource
        self.clai_commands: Dict[str, CommandRunner] = {'skills': ClaiPluginsCommandRunner(agent_datasource), 'orchestrate': ClaiOrchestrateCommandRunner(orchestrator_provider), 'activate': ClaiSelectCommandRunner(config_storage, agent_datasource), 'deactivate': ClaiUnselectCommandRunner(config_storage, agent_datasource), 'manual': ClaiPowerDisableCommandRunner(server_status_datasource), 'auto': ClaiPowerCommandRunner(server_status_datasource), 'install': ClaiInstallCommandRunner(agent_datasource), 'last-info': ClaiLastInfoCommandRunner(server_status_datasource), 'reload': ClaiReloadCommandRunner(agent_datasource), 'help': ClaiHelpCommandRunner()}
        self.clai_post_commands: Dict[str, PostCommandRunner] = {'activate': ClaiSelectCommandRunner(config_storage, agent_datasource), 'last-info': ClaiLastInfoCommandRunner(server_status_datasource), 'install': ClaiInstallCommandRunner(agent_datasource)}

    def provide_command_runner(self, command: str, selected_agent: AgentRunner) -> CommandRunner:
        if command.startswith(CLAI_COMMAND_NAME):
            clai_command_name = command.replace(CLAI_COMMAND_NAME, '', 1).strip()
            return self.__get_clai_command_runner(clai_command_name, selected_agent)
        return AgentCommandRunner(selected_agent, self.server_status_datasource)

    def provide_post_command_runner(self, command: str, selected_agent: AgentRunner) -> PostCommandRunner:
        if command.startswith(CLAI_COMMAND_NAME):
            clai_command_name = command.replace(CLAI_COMMAND_NAME, '', 1).strip()
            return self.__get_clai_post_command_runner(clai_command_name, selected_agent)
        return AgentCommandRunner(selected_agent, self.server_status_datasource)

    def __get_clai_post_command_runner(self, clai_command_name: str, selected_agent: AgentRunner) -> PostCommandRunner:
        clai_post_commands_names = self.clai_post_commands.keys()
        commands_filtered = filter(clai_command_name.startswith, clai_post_commands_names)
        command_found = next(commands_filtered, None)
        if command_found:
            return self.clai_post_commands[command_found]
        return ClaiDelegateToAgentCommandRunner(AgentCommandRunner(selected_agent, self.server_status_datasource))

    def __get_clai_command_runner(self, clai_command_name: str, selected_agent: AgentRunner) -> CommandRunner:
        clai_commands_names = self.clai_commands.keys()
        commands_filtered = filter(clai_command_name.startswith, clai_commands_names)
        command_found = next(commands_filtered, None)
        if command_found:
            return self.clai_commands[command_found]
        return ClaiDelegateToAgentCommandRunner(AgentCommandRunner(selected_agent, self.server_status_datasource, ignore_threshold=True))

def provide_command_runner(self, command: str, selected_agent: AgentRunner) -> CommandRunner:
    if command.startswith(CLAI_COMMAND_NAME):
        clai_command_name = command.replace(CLAI_COMMAND_NAME, '', 1).strip()
        return self.__get_clai_command_runner(clai_command_name, selected_agent)
    return AgentCommandRunner(selected_agent, self.server_status_datasource)

def provide_post_command_runner(self, command: str, selected_agent: AgentRunner) -> PostCommandRunner:
    if command.startswith(CLAI_COMMAND_NAME):
        clai_command_name = command.replace(CLAI_COMMAND_NAME, '', 1).strip()
        return self.__get_clai_post_command_runner(clai_command_name, selected_agent)
    return AgentCommandRunner(selected_agent, self.server_status_datasource)

class ClaiInstallCommandRunner(CommandRunner, PostCommandRunner):
    INSTALL_PLUGIN_DIRECTIVE = 'clai install'

    def __init__(self, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource

    @staticmethod
    def __move_plugin__(dir_to_install: str) -> Action:
        if dir_to_install.startswith('http') or dir_to_install.startswith('https'):
            cmd = f'cd $CLAI_PATH/clai/server/plugins && curl -O {dir_to_install}'
            return Action(suggested_command=cmd, execute=True)
        if not os.path.exists(dir_to_install) or not os.path.isdir(dir_to_install):
            return create_error_install(dir_to_install)
        plugin_name = dir_to_install.split('/')[-1]
        logger.info(f'installing plugin name {plugin_name}')
        cmd = f'cp -R {dir_to_install} $CLAI_PATH/clai/server/plugins'
        return Action(suggested_command=cmd, execute=True)

    def execute(self, state: State) -> Action:
        dir_to_install = state.command.replace(f'{self.INSTALL_PLUGIN_DIRECTIVE}', '').strip()
        logger.info(f'trying to install ${dir_to_install}')
        return self.__move_plugin__(dir_to_install)

    def execute_post(self, state: State) -> Action:
        if state.result_code == '0' and state.action_suggested.suggested_command != ':':
            return create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins())
        return Action()

@staticmethod
def __move_plugin__(dir_to_install: str) -> Action:
    if dir_to_install.startswith('http') or dir_to_install.startswith('https'):
        cmd = f'cd $CLAI_PATH/clai/server/plugins && curl -O {dir_to_install}'
        return Action(suggested_command=cmd, execute=True)
    if not os.path.exists(dir_to_install) or not os.path.isdir(dir_to_install):
        return create_error_install(dir_to_install)
    plugin_name = dir_to_install.split('/')[-1]
    logger.info(f'installing plugin name {plugin_name}')
    cmd = f'cp -R {dir_to_install} $CLAI_PATH/clai/server/plugins'
    return Action(suggested_command=cmd, execute=True)

def extract_quoted_agent_name(plugin_to_select):
    if plugin_to_select.startswith('"'):
        names = plugin_to_select.split('"')[1::2]
        if names:
            return names[0]
    return plugin_to_select

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

def get_next_action(self, state: State) -> Action:
    command = state.command
    for cmd in self.equivalencies:
        if command.startswith(cmd):
            return self.__build_suggestion(command, self.equivalencies[cmd], cmd)
    return Action(suggested_command=NOOP_COMMAND)

def wa_skill_processor_tarbot(msg):
    confidence = 0.0
    data = None
    if msg.startswith('tar'):
        return (None, 0.0)
    response, success = call_wa_skill(msg, __self)
    if not success:
        return ({'text': response}, 0.0)
    try:
        intent = response['intents'][0]['intent']
        confidence = response['intents'][0]['confidence']
    except IndexError or KeyError:
        pass
    entities = {}
    for item in response['entities']:
        if item['entity'] in entities:
            entities[item['entity']].append(item['value'])
        else:
            entities[item['entity']] = [item['value']]
    filename = '<archive-file>'
    dirname = '<directory>'
    extensions = {'images': ['.png, .bmp, .jpg'], 'documents': ['.doc', '.docx', '.txt', '.pdf', '.md']}
    flags = ''
    if 'verbose' in entities:
        flags += 'v'
    if 'tar-type' in entities:
        if 'gz' in entities['tar-type']:
            flags += 'z'
        elif 'bz2' in entities['tar-type']:
            flags += 'j'
    intents = {'check-size': {'text': 'Try >> tar -czf - {} | wc -c'.format(filename)}, 'check-validity': {'text': 'Try >> tar tvfW {}'.format(filename)}, 'tar-usage': {'text': 'Tar Usage and Options: \nc - create a archive file. \nx - extract a archive file. \nv - show the progress of archive file. \nf - filename of archive file. \nt - viewing content of archive file.  \nj - filter archive through bzip2.  \nz - filter archive through gzip. \nr - append or update files or directories to existing archive file.  \nW - Verify a archive file.  wildcards - Specify patterns in unix tar command.'}}
    if intent in intents:
        data = intents[intent]
    elif intent == 'tar-directory-to-file':
        flags = 'c{}f'.format(flags)
        data = {'text': 'Try >> tar -{} {} {}'.format(flags, filename, dirname)}
    elif intent == 'untar-file-to-directory':
        flags = 'x{}f'.format(flags)
        if 'directory-name' in entities:
            data = {'text': 'Try >> tar -{} {} -C {}'.format(flags, filename, dirname)}
        else:
            data = {'text': 'Try >> tar -{} {}'.format(flags, filename)}
    elif intent == 'untar-group-of-files':
        flags = 'x{}f'.format(flags)
        ext = []
        if 'file-extension' in entities:
            ext += entities['file-extension']
        elif 'file-type' in entities:
            ext += extensions[entities['file-type'][0]]
        if not ext:
            ext = ['.ext']
        if 'directory-name' in entities:
            data = {'text': 'Try >> tar -{} {} --wildcards {} -C {}'.format(flags, filename, ' '.join(['*' + e for e in ext]), dirname)}
        else:
            data = {'text': 'Try >> tar -{} {} --wildcards {}'.format(flags, filename, ' '.join(['*' + e for e in ext]))}
    elif intent == 'untar-single-file':
        flags = 'x{}f'.format(flags)
        if 'directory-name' in entities:
            data = {'text': 'Try >> tar -{} {} -C {}'.format(flags, filename, dirname)}
        else:
            data = {'text': 'Try >> tar -{} {}'.format(flags, filename)}
    elif intent == 'add-to-file':
        flags = '{}rf'.format(flags)
        if 'tar-type' in entities:
            if 'gz' in entities['tar-type'] or 'bz2' in entities['tar-type']:
                data = {'text': "The tar command don't have a option to add files or directories to an existing compressed tar.gz and tar.bz2 archive file."}
            else:
                data = {'text': 'Unrecognized option.'}
        else:
            data = {'text': 'Try >> tar -{} {} <file>'.format(flags, filename)}
    elif intent == 'list-contents':
        flags = '{}tf'.format(flags)
        ext = []
        if 'file-extension' in entities:
            ext += entities['file-extension']
        elif 'file-type' in entities:
            ext += extensions[entities['file-type'][0]]
        if not ext:
            data = {'text': 'Try >> tar -{} {}'.format(flags, filename)}
        else:
            data = {'text': "Try >> tar -{} {} '{}'".format(flags, filename, ' '.join(['*' + e for e in ext]))}
    else:
        pass
    return (data, confidence)

def wa_skill_processor_grepbot(msg):
    confidence = 0.0
    data = {}
    try:
        match_string = re.findall('\\"(.+?)\\"', msg)[0]
        msg = msg.replace('"{}"'.format(match_string), '')
    except:
        match_string = '<string>'
    response, success = call_wa_skill(msg, __self)
    if not success:
        return ({'text': response}, 0.0)
    if msg.startswith('grep for'):
        confidence = 1.0
    else:
        confidence = max([item['confidence'] for item in response['intents']])
    filename = '<filename>'
    dirname = None
    for item in response['entities']:
        if item['entity'] == 'directory':
            dirname = '<directory>'
        if item['entity'] == 'starts-with':
            match_string = '^' + match_string
        if item['entity'] == 'ends-with':
            match_string = match_string + '$'
    flags = '-'
    if dirname:
        flags += 'r'
    for intent in response['intents']:
        if intent['confidence'] > 0.25 and intent['intent'] != 'find':
            flags += __flags[intent['intent']]
    if flags == '-':
        flags = ''
    command = 'grep {} "{}"'.format(flags, match_string)
    if dirname:
        command += ' {}'.format(dirname)
    else:
        command += ' {}'.format(filename)
    data = {'text': 'Try >> ' + command}
    return (data, confidence)

def wa_skill_processor_cloudbot(msg):
    if msg.startswith('ibmcloud'):
        return (None, 0.0)
    response, success = call_wa_skill(msg, __self)
    if not success:
        return ({'text': response}, 0.0)
    try:
        intent = response['intents'][0]['intent']
        confidence = response['intents'][0]['confidence']
    except IndexError or KeyError:
        intent = 'generic'
        confidence = 0.0
    data = {'text': 'Try >> ibmcloud ' + __intents[intent]}
    return (data, confidence)

def wa_skill_processor_zosbot(msg):
    confidence = 0.0
    data = None
    response, success = call_wa_skill(msg, __self)
    if not success:
        return ({'text': response}, 0.0)
    try:
        intent = response['intents'][0]['intent']
        confidence = response['intents'][0]['confidence']
    except IndexError or KeyError:
        pass
    entities = {}
    for item in response['entities']:
        if item['entity'] in entities:
            entities[item['entity']].append(item['value'])
        else:
            entities[item['entity']] = [item['value']]
    if intent == 'bpxmtext':
        data = {'text': 'Try >> bpxmtext [reasoncode]'}
    elif intent == 'compile-c-code':
        data = {'text': 'Try >> xlc'}
    elif intent == 'extattr':
        data = {'text': 'Try >> extattr [+alps] [-alps] [-Fformat] [file] ...'}
    elif intent == 'obrowse':
        data = {'text': 'Try >> obrowse -r xx [file]'}
    elif intent == 'oedit':
        data = {'text': 'Try >> oedit -r xx [file]'}
    elif intent == 'oget':
        data = {'text': 'Try >> OGET [pathname] mvs_data_set_name(member_name)'}
    elif intent == 'oput':
        data = {'text': 'Try >> OPUT mvs_data_set_name(member_name) [pathname]'}
    elif intent == 'oeconsol':
        if 'iplinfo' in entities:
            data = {'text': 'Try >> oeconsol [d iplinfo]'}
        elif 'command' in entities:
            data = {'text': 'Try >> oeconsol [command]'}
        else:
            data = {'text': 'Try >> oeconsol [d parmlib]'}
    elif intent == 'tso':
        data = {'text': 'Try >> tso [-o] [-t] TSO_command'}
    else:
        pass
    return (data, confidence)

class MsgCodeAgent(Agent):

    def __init__(self):
        super(MsgCodeAgent, self).__init__()
        inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
        self.store = Datastore(inifile_path)

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

    def post_execute(self, state: State) -> Action:
        logger.info('==================== In zMsgCode Bot:post_execute ============================')
        logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
        logger.info('============================================================================')
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        stderr = state.stderr.strip()
        matches = re.compile(REGEX_ZMSG).match(stderr)
        if matches is None:
            logger.info(f"No Z message ID found in '{stderr}'")
            return Action(suggested_command=state.command)
        logger.info(f"Analyzing error message '{matches[0]}'")
        msgid: str = matches[2]
        helpWasFound = False
        bpx_matches: List[str] = self.__search(matches[0], REGEX_BPX)
        if bpx_matches is not None:
            reason_code: str = bpx_matches[1]
            logger.info(f'==> Reason Code: {reason_code}')
            result: CompletedProcess = subprocess.run(['bpxmtext', reason_code], stdout=subprocess.PIPE)
            if result.returncode == 0:
                messageText = result.stdout.decode('UTF8')
                if self.__search(messageText, REGEX_BPX_BADANSWER) is None:
                    suggested_command = state.command
                    description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I asked bpxmtext about that message:\n').info().append(messageText).warning().to_console()
                    helpWasFound = True
        if not helpWasFound:
            kc_api: Provider = self.store.get_apis()['ibm_kc']
            if kc_api is not None and kc_api.can_run_on_this_os():
                data = self.store.search(msgid, service='ibm_kc', size=1)
                if data:
                    logger.info(f'==> Success!!! Found information for msgid {msgid}')
                    suggested_command = state.command
                    description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I looked up {msgid} in the IBM KnowledgeCenter for you:\n').info().append(kc_api.get_printable_output(data)).warning().to_console()
                    helpWasFound = True
        if not helpWasFound:
            logger.info('Failure: Unable to be helpful')
            logger.info('============================================================================')
            suggested_command = NOOP_COMMAND
            description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"I couldn't find any help for message code '{msgid}'\n").info().to_console()
        return Action(suggested_command=suggested_command, description=description, confidence=1.0)

    def __search(self, target: str, regex_list: List[str]) -> List[str]:
        """Check all possible regexes in a list, return the first match encountered"""
        for regex in regex_list:
            this_match = re.compile(regex).match(target)
            if this_match is not None:
                return this_match
        return None

def __search(self, target: str, regex_list: List[str]) -> List[str]:
    """Check all possible regexes in a list, return the first match encountered"""
    for regex in regex_list:
        this_match = re.compile(regex).match(target)
        if this_match is not None:
            return this_match
    return None

class Service:

    def __init__(self):
        self.state = {'ready_flag': False, 'threshold': 0.9, 'current_intent': None, 'current_branch': None, 'commit_details': None, 'has_done_add': False, 'has_done_commit': False}
        self.gh_session = requests.Session()
        self.gh_session.auth = (_github_username, _github_access_token)

    def __call__(self, *args, **kwargs):
        command = args[0]
        confidence = 0.0
        try:
            response = requests.post(_rasa_service, json={'text': command}).json()
            confidence = response['intent']['confidence']
            if confidence > self.state['threshold']:
                self.state['current_intent'] = response['intent']['name']
        except Exception as ex:
            print('Method failed with status ' + str(ex))
        if self.state['current_intent'] == 'commit':
            if not self.state['ready_flag']:
                self.state['ready_flag'] = True
                temp_description = 'Ready to {}. Press execute to continue.'.format(self.state['current_intent'])
                return [Action(suggested_command='git status | tee {}'.format(_path_to_log_file), execute=True, description=None, confidence=1.0), Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(temp_description).to_console(), confidence=1.0)]
        if command == 'execute':
            now = datetime.now()
            commit_message = now.strftime('%d/%m/%Y %H:%M:%S')
            stdout = open(_path_to_log_file).read().split('\n')
            commit_description = ''
            current_branch = None
            for line in stdout:
                if line.startswith('On branch'):
                    current_branch = line.split()[-1]
                if line.strip().startswith('modified:'):
                    commit_description += line.strip() + ' + '
            if commit_description:
                self.state['commit_details'] = commit_description
            if current_branch:
                self.state['current_branch'] = current_branch
            commit_description = self.state['commit_details']
            respond = Action(suggested_command='git commit -m "{}" -m "{}";'.format(commit_message, commit_description), execute=False, description=None, confidence=1.0)
            if self.state['has_done_add']:
                return respond
            else:
                return [Action(suggested_command='git add -A', execute=True, description='Adding untracked files...', confidence=1.0), respond]
        if self.state['current_intent'] == 'push':
            return Action(suggested_command='git push', execute=False, description=None, confidence=confidence)
        if self.state['current_intent'] == 'merge':
            merge_url = '{}/pulls'.format(_github_url)
            source = None
            target = 'master'
            for entity in response['entities']:
                if entity['entity'] == 'source':
                    source = entity['value']
                if entity['entity'] == 'target':
                    target = entity['value']
            if not source:
                source = self.state['current_branch']
            payload = {'title': 'Dummy PR from gitbot', 'body': 'Example from the `gitbot` screencast. This will not be merged.', 'head': source, 'base': target}
            ping_github = json.loads(self.gh_session.post(merge_url, json=payload).text)
            return Action(suggested_command=NOOP_COMMAND, execute=True, description='Success. Created PR {}'.format(ping_github['number']), confidence=confidence)
        if self.state['current_intent'] == 'comment':
            idx = 0
            comment = None
            for entity in response['entities']:
                if entity['entity'] == 'id':
                    idx = entity['value']
                if entity['entity'] == 'comment':
                    comment = entity['value']
            idx = command.split('<')[-1].split('>')[0]
            comment_url = '{}/issues/{}/comments'.format(_github_url, idx)
            payload = {'body': comment}
            ping_github = json.loads(self.gh_session.post(comment_url, json=payload).text)
            return Action(suggested_command=NOOP_COMMAND, execute=True, description='Success', confidence=confidence)

    def parse_command(self, command: str, stdout: str):
        if command.startswith('git checkout'):
            self.state['current_branch'] = None
        if command.startswith('git add'):
            self.state['has_done_add'] = True
        if command.startswith('commit'):
            self.state['has_done_add'] = False
            self.state['has_done_commit'] = True

def parse_command(self, command: str, stdout: str):
    if command.startswith('git checkout'):
        self.state['current_branch'] = None
    if command.startswith('git add'):
        self.state['has_done_add'] = True
    if command.startswith('commit'):
        self.state['has_done_add'] = False
        self.state['has_done_commit'] = True

def cleanup(text: str) -> str:
    text = PATTERN_SPACES.sub(' ', text).strip()
    text = PATTERN_DASH.sub('', text).strip()
    return text

def __clean__(html: str) -> str:
    return re.sub(re.compile('<.*?>'), '', html)

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

def __add_to_action_order__(self, agent_name):
    if agent_name in self._action_order:
        return
    max_action_order = max(self._action_order.values())
    self._action_order[agent_name] = max_action_order + 1

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

def get_prime_text(self):
    """Formats all examples to prime the model."""
    return ''.join([self.format_example(ex) for ex in self.examples.values()])

def get_top_reply(self, prompt, strip_output_suffix=False):
    """Obtains the best result as returned by the API."""
    response = self.submit_request(prompt)
    response = response['choices'][0]['text']
    if strip_output_suffix:
        response = response[len(self.output_prefix):] if response.startswith(self.output_prefix) else response
    return response

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

@staticmethod
def clean_message(text: str):
    text = text[text.find('\n'):]
    text = re.sub('[[0-9;]*m', '', text)
    return text[:text.find(']0;') - 3]

