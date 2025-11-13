# Cluster 12

def remove_setup_register():
    rc_files = get_rc_files()
    for file in rc_files:
        remove_lines_setup(file)

def execute(args):
    bin_path = os.getenv('CLAI_PATH', None)
    if '-h' in args or '--help' in args:
        print('usage: uninstall.py [-h] [--help] [--user]\n             \nUninstall CLAI.\n             \noptional arguments:             \n-h, --help            show this help message and exit             \n--user                Uninstalls a local installation of clai for the current user')
        sys.exit(0)
    path = clai_installed(get_setup_file())
    print(f'path= {path}')
    print(f'bin path= {bin_path}')
    if not path and bin_path is None:
        print_error('CLAI is not installed.')
        sys.exit(1)
    if not bin_path:
        bin_path = path
    stat_uninstall(path)
    users = unregister_the_user(path)
    if '--user' in args or is_user_install(bin_path):
        remove_system_folder(bin_path)
    elif not users:
        remove_system_folder()
    remove_setup_file(get_setup_file())
    remove_setup_register()
    print_complete('CLAI has been uninstalled correctly, you will need to restart your shell.')
    return 0

def get_shell(args):
    if args.shell is None:
        return os.path.basename(os.getenv('SHELL', ''))
    return args.shell

def parse_args():
    default_user_destdir = os.path.join(os.path.expanduser('/opt/local/share'), 'clai')
    parser = argparse.ArgumentParser(description='Install CLAI for all users.')
    parser.add_argument('--shell', help='if you like to install for different shell', dest='shell', action='store')
    parser.add_argument('--demo', help='if you like to jump installation restrictions', dest='demo_mode', action='store_true')
    parser.add_argument('--system', help='if you like install it for all users.', dest='system', action='store_true', default=False)
    parser.add_argument('--unassisted', help="Don't ask to he user for questions or inputs in the install process", dest='unassisted', action='store_true', default=False)
    parser.add_argument('--no-skills', help="Don't install the default skills", dest='no_skills', action='store_true', default=False)
    parser.add_argument('-d', '--destdir', metavar='DIR', default=default_user_destdir, help='set destination to DIR')
    parser.add_argument('--user', help='Installs clai in the users own bin directory', dest='user_install', action='store_true', default=False)
    parser.add_argument('--port', help='port listen server', type=int, default=8010, dest='port')
    args = parser.parse_args()
    if not valid_python_version():
        print_error('You need install python 3.6 or upper is required.')
        sys.exit(1)
    if not is_root_user(args):
        if not args.user_install:
            print_error('You need root privileges for the system wide installation process.')
            sys.exit(1)
    if args.user_install:
        if args.destdir == default_user_destdir:
            args.destdir = os.path.join(os.path.expanduser('~/.bin'), 'clai')
    if is_windows():
        print_error('CLAI is not supported on Windows.')
        sys.exit(1)
    shell = get_shell(args)
    if shell not in SUPPORTED_SHELLS:
        print_error('%s is not supported yet.' % shell)
        sys.exit(1)
    if args.system:
        if args.destdir != default_user_destdir:
            print_error('Custom paths incompatible with --system option.')
            sys.exit(1)
    return args

def install_plugins_dependencies(path, plugin, user_install):
    print(f'installing dependencies of plugin {plugin}')
    result = os.system(f'{path}/fileExist.sh {plugin} {path} {('--user' if user_install else '')}')
    return result == 0

def install_orchestration_dependencies(path, orchestrator_name):
    print(f'install dependencies of orchestrator {orchestrator_name}')
    result = os.system(f'{path}/installOrchestrator.sh {orchestrator_name} {path}')
    return result == 0

def cli_executable(cli_path):
    os.system(f'chmod 777 {cli_path}/clai-run')
    os.system(f'chmod 777 {cli_path}/fswatchlog')
    os.system(f'chmod 777 {cli_path}/obtain-command-id')
    os.system(f'chmod 777 {cli_path}/post-execution')
    os.system(f'chmod 777 {cli_path}/process-command')
    os.system(f'chmod 777 {cli_path}/restore-history')

def execute(args):
    unassisted = args.unassisted
    no_skills = args.no_skills
    demo_mode = args.demo_mode
    user_install = args.user_install
    bin_path = os.path.join(args.destdir, 'bin')
    code_path = os.path.join(bin_path, 'clai')
    cli_path = os.path.join(bin_path, 'bin')
    temp_path = './tmp'
    mkdir(f'{temp_path}/')
    create_rc_file_if_not_exist(args.system)
    if clai_installed(get_setup_file()):
        print_error('CLAI is already in you system. You should execute uninstall first')
        sys.exit(1)
    if not binary_installed(bin_path):
        mkdir(bin_path)
        mkdir(code_path)
        cp_tree('./clai', code_path)
        cp_tree('./bin', cli_path)
        copy('./scripts/clai.sh', bin_path)
        copy('./scripts/saveFilesChanges.sh', bin_path)
        copy('./configPlugins.json', bin_path)
        copy('./usersInstalled.json', bin_path)
        copy('./anonymize.json', bin_path)
        copy('./scripts/fileExist.sh', bin_path)
        copy('./scripts/installOrchestrator.sh', bin_path)
        os.system(f'chmod 775 {bin_path}/saveFilesChanges.sh')
        os.system(f'chmod 775 {bin_path}/fileExist.sh')
        os.system(f'chmod 775 {bin_path}/installOrchestrator.sh')
        os.system(f'chmod -R 777 {code_path}/server/plugins')
        os.system(f'chmod 777 {bin_path}/clai.sh')
        os.system(f'chmod 666 {bin_path}/configPlugins.json')
        os.system(f'chmod 666 {bin_path}/anonymize.json')
        os.system(f'chmod -R 777 {bin_path}')
        cli_executable(cli_path)
        download_file(URL_BASH_PREEXEC, filename='%s/%s' % (temp_path, BASH_PREEXEC))
        copy('%s/%s' % (temp_path, BASH_PREEXEC), bin_path)
        if is_zos():
            os.system(f'chtag -tc 819 {bin_path}/{BASH_PREEXEC}')
    if user_install:
        mark_user_flag(bin_path, True)
    else:
        mark_user_flag(bin_path, False)
    register_the_user(bin_path, args.system)
    append_setup_to_file(get_setup_file(), bin_path, args.port)
    register_file(args.system)
    install_orchestration(bin_path)
    if not no_skills:
        save_report_info(unassisted, install_plugins(bin_path, user_install), bin_path, demo_mode)
    remove(f'{temp_path}')
    if not user_install:
        os.system(f'chmod -R 777 /var/tmp')
    print_complete('CLAI has been installed correctly, you will need to restart your shell.')

def register_file(system):
    rc_files = get_rc_files(system)
    for file in rc_files:
        encoding = 'utf-8'
        newline = '\n'
        left_bracket = '['
        right_bracket = ']'
        if is_rw_with_EBCDIC(file):
            encoding = 'cp1047'
            left_bracket = 'Ý'
            right_bracket = '¨'
        print(f'registering {file}')
        append_to_file(file, '# CLAI setup' + newline, encoding)
        append_to_file(file, 'if ! ' + left_bracket + ' ${#preexec_functions' + left_bracket + '@' + right_bracket + '} -eq 0 ' + right_bracket + '; then' + newline, encoding)
        append_to_file(file, '  if ! ' + left_bracket + left_bracket + ' " ${preexec_functions' + left_bracket + '@' + right_bracket + '} " =~ " preexec_override_invoke " ' + right_bracket + right_bracket + '; then' + newline, encoding)
        append_to_file(file, f'     source {get_setup_file()} ' + newline, encoding)
        append_to_file(file, '  fi' + newline, encoding)
        append_to_file(file, 'else' + newline, encoding)
        append_to_file(file, f' source {get_setup_file()} ' + newline, encoding)
        append_to_file(file, 'fi' + newline, encoding)
        append_to_file(file, '# End CLAI setup' + newline, encoding)

def append_setup_to_file(rc_path, bin_path, port):
    append_to_file(rc_path, '\n export CLAI_PATH=%s' % bin_path)
    append_to_file(rc_path, '\n export CLAI_PORT=%s' % port)
    append_to_file(rc_path, '\n export PYTHONPATH=%s' % bin_path)
    append_to_file(rc_path, '\n[[ -f %s/bash-preexec.sh ]] && source %s/bash-preexec.sh' % (bin_path, bin_path))
    append_to_file(rc_path, f'\n[[ -f {bin_path}/clai.sh ]] && source {bin_path}/clai.sh --port {port}')

def parse_args():
    parser = argparse.ArgumentParser(description='Setup Clai in a development enviorment to make live changes')
    parser.add_argument('action', action='store', type=str, help=f'action for script to perform one of: {' '.join(ACTIONS)}')
    parser.add_argument('-p', '--path', help='path to source directory', dest='path', action='store')
    parser.add_argument('-i', '--install-directory', dest='install_path', action='store', type=str, help='The location that clai is installed in', default=f'{os.getenv('HOME', '/home/root')}/.bin/clai/bin')
    args = parser.parse_args()
    if args.action not in ACTIONS:
        print_error(f"Not a valid action: '{args.action}' Valid actions: [{', '.join(ACTIONS)}]")
        sys.exit(1)
    if args.path is None:
        print_error('The path flag is required')
        sys.exit(1)
    return args

def link(src, dest):
    try:
        if not os.path.exists(dest):
            os.symlink(src, dest)
    except Exception as e:
        print(e)
        sys.exit(1)

def install(repo_path: str, install_path: str):
    createInstallDir(install_path)
    required_scripts = os.listdir(os.path.join(repo_path, 'scripts'))
    required_dirs = ['bin', 'clai']
    required_files = [file for file in os.listdir(repo_path) if file.endswith('.json')]
    print('Linking all needed files to install directory')
    try:
        for script in required_scripts:
            link(os.path.join(repo_path, f'scripts/{script}'), os.path.join(install_path, script))
            os.system(f'chmod 775 {os.path.join(install_path, script)}')
        for directory in required_dirs:
            link(os.path.join(repo_path, directory), os.path.join(install_path, directory))
            if directory == 'bin':
                os.system(f'chmod -R 777 {os.path.join(install_path, directory)}')
        for file in required_files:
            link(os.path.join(repo_path, file), os.path.join(install_path, file))
            os.system(f'chmod 666 {os.path.join(install_path, file)}')
    except Exception as e:
        print(e)
        sys.exit(1)
    download_file(URL_BASH_PREEXEC, filename='%s/%s' % (install_path, BASH_PREEXEC))
    register_the_user(install_path, False)
    append_setup_to_file(get_setup_file(), install_path, DEFAULT_PORT)
    register_file(False)
    install_orchestration(install_path)
    install_plugins(install_path, False)
    print_complete('CLAI has been installed correctly, you need restart your shell.')

def revert(install_path):
    print('Reverting file permissions to original state')
    scripts = [file for file in os.listdir(install_path) if file.endswith('.sh')]
    json_files = [file for file in os.listdir(install_path) if file.endswith('.json')]
    try:
        for script in scripts:
            os.system(f'chmod 644 {os.path.join(install_path, script)}')
        os.system(f'chmod 755 {install_path}/bin')
        for file in os.listdir(f'{install_path}/bin'):
            if file in ['emulator.py', 'process-command']:
                os.system(f'chmod 755 {os.path.join(install_path, f'bin/{file}')}')
            else:
                os.system(f'chmod 644 {os.path.join(install_path, f'bin/{file}')}')
        for file in json_files:
            os.system(f'chmod 666 {os.path.join(install_path, file)}')
    except Exception as e:
        print(e)
        sys.exit(1)

def main(args: list):
    action = args.action
    repo_path = args.path
    install_path = args.install_path
    if action == 'install':
        install(repo_path, install_path)
    elif action == 'uninstall':
        path = clai_installed(get_setup_file())
        if not path:
            print_error('CLAI is not installed.')
            sys.exit(1)
        revert(install_path)
        uninstall(['--user'])
        with open(f'{repo_path}/configPlugins.json', 'w') as file:
            file.write(json.dumps({'selected': {'user': ['']}, 'default': [''], 'default_orchestrator': 'max_orchestrator', 'installed': [], 'report_enable': False}))
    return 0

class Agent(ABC):

    def __init__(self):
        self.agent_name = self.__class__.__name__
        self.ready = False
        self._save_basedir = os.path.join(BASEDIR, 'saved_agents')
        self._save_dirpath = os.path.join(self._save_basedir, self.agent_name)

    def execute(self, state: State) -> Union[Action, List[Action]]:
        try:
            action_to_return = self.get_next_action(state)
        except:
            action_to_return = Action()
        if isinstance(action_to_return, list):
            for action in action_to_return:
                action.agent_owner = self.agent_name
        else:
            action_to_return.agent_owner = self.agent_name
        return action_to_return

    def post_execute(self, state: State) -> Action:
        """Provide a post execution"""
        return Action(origin_command=state.command)

    @abstractmethod
    def get_next_action(self, state: State) -> Union[Action, List[Action]]:
        """Provide next action to execute in the bash console"""

    def init_agent(self):
        """Add here all heavy task for initialize the """

    def get_agent_state(self) -> dict:
        """Returns the agent state to be saved for future loading"""
        return {}

    def __prepare_state_folder__(self):
        os.makedirs(self._save_dirpath, exist_ok=True)
        for file in os.listdir(self._save_dirpath):
            path = os.path.join(self._save_dirpath, file)
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)

    def save_agent(self) -> bool:
        """Saves agent state into persisting memory"""
        try:
            state = self.get_agent_state()
            if not state:
                return True
            self.__prepare_state_folder__()
            for var_name, var_val in state.items():
                with open('{}/{}.p'.format(self._save_dirpath, var_name), 'wb') as file:
                    pickle.dump(var_val, file)
        except Exception:
            return False
        else:
            return True

    def load_saved_state(self) -> dict:
        agent_state = {}
        filenames = []
        if os.path.exists(self._save_dirpath):
            filenames = [file for file in os.listdir(self._save_dirpath) if os.path.isfile(os.path.join(self._save_dirpath, file))]
        for filename in filenames:
            try:
                key = os.path.splitext(filename)[0]
                with open(os.path.join(self._save_dirpath, filename), 'rb') as file:
                    agent_state[key] = pickle.load(file)
            except:
                pass
        return agent_state

    def extract_name_without_extension(self, filename):
        return os.path.splitext(filename)[0]

    def __del__(self):
        self.save_agent()

def __del__(self):
    self.save_agent()

class Logger:
    MAX_IN_MB = 100000000

    def __init__(self):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        log_file = os.getenv('CLAI_LOG_FILE', '/var/tmp/app.log')
        self.logger = logging.getLogger('clai_logger')
        self.logger.setLevel(logging.INFO)
        self.log_handler = handlers.RotatingFileHandler(log_file, mode='a', maxBytes=Logger.MAX_IN_MB, backupCount=10, encoding=None, delay=0)
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.log_handler)

    def info(self, text):
        self.logger.info(text)

    def warning(self, text):
        self.logger.warning(text)

    def debug(self, text):
        self.logger.debug(text)

def __init__(self):
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    log_file = os.getenv('CLAI_LOG_FILE', '/var/tmp/app.log')
    self.logger = logging.getLogger('clai_logger')
    self.logger.setLevel(logging.INFO)
    self.log_handler = handlers.RotatingFileHandler(log_file, mode='a', maxBytes=Logger.MAX_IN_MB, backupCount=10, encoding=None, delay=0)
    self.log_handler.setLevel(logging.INFO)
    self.log_handler.setFormatter(log_formatter)
    self.logger.addHandler(self.log_handler)

def get_own_name(file: str) -> str:
    return os.path.basename(file).replace('.py', '')

class QuestionDetection(object):

    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.WH_TAGS = ['WDT', 'WP', 'WP$', 'WRB']

    def is_question(self, text):
        """
        A function to check if text is phrased as a question.

        Algorithm:
            1. Test if the text ends with "?". If yes, then it's a question.
            2. Test if the text contains any "WH" word tags (indicative of WH type of question)

        Args:
            text (str): a text to be tested

        Returns:
            (bool): True if the text is a question.
        """
        if text.endswith('?'):
            return True
        doc = self.nlp(text)
        for token in doc:
            if token.tag_ in self.WH_TAGS:
                return True
        return False

def is_question(self, text):
    """
        A function to check if text is phrased as a question.

        Algorithm:
            1. Test if the text ends with "?". If yes, then it's a question.
            2. Test if the text contains any "WH" word tags (indicative of WH type of question)

        Args:
            text (str): a text to be tested

        Returns:
            (bool): True if the text is a question.
        """
    if text.endswith('?'):
        return True
    doc = self.nlp(text)
    for token in doc:
        if token.tag_ in self.WH_TAGS:
            return True
    return False

class GITBOT(Agent):

    def __init__(self):
        super(GITBOT, self).__init__()
        self.service = Service()
    ' pre execution processing '

    def get_next_action(self, state: State) -> Action:
        command = state.command
        return self.service(command)
    ' pre execution processing '

    def post_execute(self, state: State) -> Action:
        if state.result_code == '0':
            self.service.parse_command(state.command, stdout='')
        return Action(suggested_command=NOOP_COMMAND)

    def save_agent(self) -> bool:
        os.system('lsof -t -i tcp:{} | xargs kill'.format(_rasa_port_number))
        super().save_agent()

def save_agent(self) -> bool:
    os.system('lsof -t -i tcp:{} | xargs kill'.format(_rasa_port_number))
    super().save_agent()

class QuestionDetection(object):

    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.WH_TAGS = ['WDT', 'WP', 'WP$', 'WRB']

    def is_question(self, text):
        if text.endswith('?'):
            return True
        doc = self.nlp(text)
        for token in doc:
            if token.tag_ in self.WH_TAGS:
                return True
        return False

def is_question(self, text):
    if text.endswith('?'):
        return True
    doc = self.nlp(text)
    for token in doc:
        if token.tag_ in self.WH_TAGS:
            return True
    return False

def is_windows():
    return platform.system() == 'Windows'

def is_mac():
    return platform.system() == 'Darwin'

def check_if_process_running() -> bool:
    return os.system('ps -Ao args | grep "[c]lai-run" > /dev/null 2>&1') == 0

