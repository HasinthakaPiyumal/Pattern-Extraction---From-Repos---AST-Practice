# Cluster 16

class WebAgentTextEnv(gym.Env):
    """Gym environment for Text mode of WebShop environment"""

    def __init__(self, observation_mode='html', file_path=DEFAULT_FILE_PATH, server=None, **kwargs):
        """
        Constructor for text environment

        Arguments:
        observation_mode (`str`) -- ['html' | 'text'] (default 'html')
        get_image
        filter_goals
        limit_goals
        num_products
        human_goals
        session
        session_prefix
        show_attrs
        """
        super(WebAgentTextEnv, self).__init__()
        self.observation_mode = observation_mode
        self.kwargs = kwargs
        self.file_path = file_path
        self.base_url = 'http://127.0.0.1:3000'
        self.server = SimServer(self.base_url, self.file_path, self.kwargs.get('filter_goals'), self.kwargs.get('limit_goals', -1), self.kwargs.get('num_products'), self.kwargs.get('human_goals'), self.kwargs.get('show_attrs', False)) if server is None else server
        self.browser = SimBrowser(self.server)
        self.session = self.kwargs.get('session')
        self.session_prefix = self.kwargs.get('session_prefix')
        if self.kwargs.get('get_image', 0):
            self.feats = torch.load(FEAT_CONV)
            self.ids = torch.load(FEAT_IDS)
            self.ids = {url: idx for idx, url in enumerate(self.ids)}
        self.prev_obs = []
        self.prev_actions = []
        self.num_prev_obs = self.kwargs.get('num_prev_obs', 0)
        self.num_prev_actions = self.kwargs.get('num_prev_actions', 0)
        self.reset()

    def step(self, action):
        """
        Takes an action, updates WebShop environment, and returns (observation, reward, done, info)

        Arguments:
        action (`str`): An action should be of the following structure:
          - search[keywords]
          - click[value]
        If action not valid, perform nothing.
        """
        info = None
        self.get_available_actions()
        action_name, action_arg = parse_action(action)
        if action_arg is not None:
            action_arg = action_arg.lower()
        if action_name == 'search' and action_arg is not None and (action_arg != ''):
            status = self.browser.search(action_arg)
        elif action_name == 'click' and action_arg in self.text_to_clickable.keys() and (action_arg != 'search'):
            status = self.browser.click(action_arg, self.text_to_clickable)
        else:
            status = dict(reward=0, done=False)
        ob = self.observation
        text_list = [ob]
        self.prev_actions.append(action)
        for i in range(1, 1 + max(self.num_prev_obs, self.num_prev_actions)):
            if len(self.prev_actions) >= i and self.num_prev_actions >= i:
                text_list.append(self.prev_actions[-i])
            if len(self.prev_obs) >= i and self.num_prev_obs >= i:
                text_list.append(self.prev_obs[-i])
        state = ' [SEP] '.join(text_list[::-1])
        self.prev_obs.append(ob)
        return (state, status['reward'], status['done'], info)

    def get_available_actions(self):
        """Returns list of available actions at the current step"""
        html_obj = self._parse_html()
        search_bar = html_obj.find(id='search_input')
        has_search_bar = True if search_bar is not None else False
        buttons = html_obj.find_all(class_='btn')
        product_links = html_obj.find_all(class_='product-link')
        buying_options = html_obj.select('input[type="radio"]')
        self.text_to_clickable = {f'{b.get_text()}'.lower(): b for b in buttons + product_links}
        for opt in buying_options:
            opt_value = opt.get('value')
            self.text_to_clickable[f'{opt_value}'] = opt
        return dict(has_search_bar=has_search_bar, clickables=list(self.text_to_clickable.keys()))

    def get_image(self):
        """Scrape image from page HTML and return as a list of pixel values"""
        html_obj = self._parse_html(self.browser.page_source)
        image_url = html_obj.find(id='product-image')
        if image_url is not None:
            image_url = image_url['src']
            if image_url in self.ids:
                image_idx = self.ids[image_url]
                image = self.feats[image_idx]
                return image
        return torch.zeros(512)

    def get_instruction_text(self):
        """Get corresponding instruction text for current environment session"""
        html_obj = self._parse_html(self.browser.page_source)
        instruction_text = html_obj.find(id='instruction-text').h4.text
        return instruction_text

    def _parse_html(self, html=None):
        """
        Returns web request result wrapped in BeautifulSoup object

        Arguments:
        url (`str`): If no url or html is provided, use the current
            observation (HTML) for parsing.
        """
        if html is None:
            html = self.state['html']
        html_obj = BeautifulSoup(html, 'html.parser')
        return html_obj

    @property
    def observation(self):
        """Compiles state into either the `html` or `text` observation mode"""
        html = self.state['html']
        if self.observation_mode == 'html':
            return html
        elif self.observation_mode == 'text':
            return self.convert_html_to_text(html, simple=True)
        elif self.observation_mode == 'text_rich':
            return self.convert_html_to_text(html, simple=False)
        elif self.observation_mode == 'url':
            return self.state['url']
        else:
            raise ValueError(f'Observation mode {self.observation_mode} not supported.')

    @property
    def state(self):
        """
        State that includes all information. The actual observation are
        likely to be a subset or reduced form of the state.
        """
        return dict(url=self.browser.current_url, html=self.browser.page_source, instruction_text=self.instruction_text)

    def convert_html_to_text(self, html, simple=False):
        """Strip HTML of tags and add separators to convert observation into simple mode"""
        texts = self._parse_html(html).findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        if simple:
            return ' [SEP] '.join((t.strip() for t in visible_texts if t != '\n'))
        else:
            observation = ''
            for t in visible_texts:
                if t == '\n':
                    continue
                if t.parent.name == 'button':
                    processed_t = f'[button] {t} [button_]'
                elif t.parent.name == 'label':
                    if f'"{t}"' in self.state['url']:
                        processed_t = f'  [clicked button] {t} [clicked button_]'
                        observation = f'You have clicked {t}.\n' + observation
                    else:
                        processed_t = f'  [button] {t} [button_]'
                elif t.parent.get('class') == ['product-link']:
                    if f'{t}' in self.server.user_sessions[self.session]['asins']:
                        processed_t = f'\n[clicked button] {t} [clicked button_]'
                    else:
                        processed_t = f'\n[button] {t} [button_]'
                else:
                    processed_t = str(t)
                observation += processed_t + '\n'
            return observation

    def reset(self, session=None, instruction_text=None):
        """Create a new session and reset environment variables"""
        session_int = None
        if session is not None:
            self.session = str(session)
            if isinstance(session, int):
                session_int = session
        else:
            self.session = ''.join(random.choices(string.ascii_lowercase, k=10))
        if self.session_prefix is not None:
            self.session = self.session_prefix + self.session
        init_url = f'{self.base_url}/{self.session}'
        self.browser.get(init_url, session_id=self.session, session_int=session_int)
        self.text_to_clickable = None
        self.instruction_text = self.get_instruction_text() if instruction_text is None else instruction_text
        obs = self.observation
        self.prev_obs = [obs]
        self.prev_actions = []
        return (obs, None)

    def render(self, mode='human'):
        pass

    def close(self):
        pass

@property
def observation(self):
    """Compiles state into either the `html` or `text` observation mode"""
    html = self.state['html']
    if self.observation_mode == 'html':
        return html
    elif self.observation_mode == 'text':
        return self.convert_html_to_text(html, simple=True)
    elif self.observation_mode == 'text_rich':
        return self.convert_html_to_text(html, simple=False)
    elif self.observation_mode == 'url':
        return self.state['url']
    else:
        raise ValueError(f'Observation mode {self.observation_mode} not supported.')

class WebAgentSiteEnv(gym.Env):
    """Gym environment for HTML mode of WebShop environment"""

    def __init__(self, observation_mode='html', **kwargs):
        """
        Constructor for HTML environment

        Arguments:
        observation_mode (`str`) -- ['html' | 'text'] (default 'html')
        pause (`float`) -- Pause (in seconds) after taking an action. 
            This is mainly for demo purposes.
            Recommended value: 2.0s
        render (`bool`) -- Show browser if set to `True`.
        session ('str') -- Session ID to initialize environment with
        """
        super(WebAgentSiteEnv, self).__init__()
        self.observation_mode = observation_mode
        self.kwargs = kwargs
        service = Service(join(dirname(abspath(__file__)), 'chromedriver'))
        options = Options()
        if 'render' not in kwargs or not kwargs['render']:
            options.add_argument('--headless')
        self.browser = webdriver.Chrome(service=service, options=options)
        self.text_to_clickable = None
        self.assigned_session = kwargs.get('session')
        self.session = None
        self.reset()

    def step(self, action):
        """
        Takes an action, updates WebShop environment, and returns (observation, reward, done, info)

        Arguments:
        action (`str`): An action should be of the following structure:
          - search[keywords]
          - click[value]
        If action not valid, perform nothing.
        """
        reward = 0.0
        done = False
        info = None
        action_name, action_arg = parse_action(action)
        if action_name == 'search':
            try:
                search_bar = self.browser.find_element_by_id('search_input')
            except Exception:
                pass
            else:
                search_bar.send_keys(action_arg)
                search_bar.submit()
        elif action_name == 'click':
            try:
                self.text_to_clickable[action_arg].click()
            except ElementNotInteractableException:
                button = self.text_to_clickable[action_arg]
                self.browser.execute_script('arguments[0].click();', button)
            reward = self.get_reward()
            if action_arg == END_BUTTON:
                done = True
        elif action_name == 'end':
            done = True
        else:
            print('Invalid action. No action performed.')
        if 'pause' in self.kwargs:
            time.sleep(self.kwargs['pause'])
        return (self.observation, reward, done, info)

    def get_available_actions(self):
        """Returns list of available actions at the current step"""
        try:
            search_bar = self.browser.find_element_by_id('search_input')
        except Exception:
            has_search_bar = False
        else:
            has_search_bar = True
        buttons = self.browser.find_elements_by_class_name('btn')
        product_links = self.browser.find_elements_by_class_name('product-link')
        buying_options = self.browser.find_elements_by_css_selector("input[type='radio']")
        self.text_to_clickable = {f'{b.text}': b for b in buttons + product_links}
        for opt in buying_options:
            opt_value = opt.get_attribute('value')
            self.text_to_clickable[f'{opt_value}'] = opt
        return dict(has_search_bar=has_search_bar, clickables=list(self.text_to_clickable.keys()))

    def _parse_html(self, html=None, url=None):
        """
        Returns web request result wrapped in BeautifulSoup object

        Arguments:
        url (`str`): If no url or html is provided, use the current
            observation (HTML) for parsing.
        """
        if html is None:
            if url is not None:
                html = requests.get(url)
            else:
                html = self.state['html']
        html_obj = BeautifulSoup(html, 'html.parser')
        return html_obj

    def get_reward(self):
        """Get reward value at current step of the environment"""
        html_obj = self._parse_html()
        r = html_obj.find(id='reward')
        r = float(r.findChildren('pre')[0].string) if r is not None else 0.0
        return r

    def get_instruction_text(self):
        """Get corresponding instruction text for environment current step"""
        html_obj = self._parse_html(self.browser.page_source)
        instruction_text = html_obj.find(id='instruction-text').h4.text
        return instruction_text

    def convert_html_to_text(self, html):
        """Strip HTML of tags and add separators to convert observation into simple mode"""
        texts = self._parse_html(html).findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        observation = ' [SEP] '.join((t.strip() for t in visible_texts if t != '\n'))
        return observation

    @property
    def state(self):
        """
        State that includes all information. The actual observation are
        likely to be a subset or reduced form of the state.
        """
        return dict(url=self.browser.current_url, html=self.browser.page_source, instruction_text=self.instruction_text)

    @property
    def observation(self):
        """Compiles state into either the `html` or `text` observation mode"""
        html = self.state['html']
        if self.observation_mode == 'html':
            return html
        elif self.observation_mode == 'text':
            return self.convert_html_to_text(html)
        else:
            raise ValueError(f'Observation mode {self.observation_mode} not supported.')

    @property
    def action_space(self):
        return NotImplementedError

    @property
    def observation_space(self):
        return NotImplementedError

    def reset(self):
        """Create a new session and reset environment variables"""
        if self.assigned_session is not None:
            self.session = self.assigned_session
        else:
            self.session = ''.join(random.choices(string.ascii_lowercase, k=5))
        init_url = f'http://127.0.0.1:3000/{self.session}'
        self.browser.get(init_url)
        self.instruction_text = self.get_instruction_text()
        return (self.observation, None)

    def render(self, mode='human'):
        return NotImplementedError

    def close(self):
        self.browser.close()
        print('Browser closed.')

@property
def observation(self):
    """Compiles state into either the `html` or `text` observation mode"""
    html = self.state['html']
    if self.observation_mode == 'html':
        return html
    elif self.observation_mode == 'text':
        return self.convert_html_to_text(html)
    else:
        raise ValueError(f'Observation mode {self.observation_mode} not supported.')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--output_dir', default='logs')
    parser.add_argument('--ckpt_freq', default=10000, type=int)
    parser.add_argument('--eval_freq', default=500, type=int)
    parser.add_argument('--test_freq', default=5000, type=int)
    parser.add_argument('--log_freq', default=100, type=int)
    parser.add_argument('--wandb', default=1, type=int)
    parser.add_argument('--num_envs', default=4, type=int)
    parser.add_argument('--step_limit', default=100, type=int)
    parser.add_argument('--max_steps', default=300000, type=int)
    parser.add_argument('--learning_rate', default=1e-05, type=float)
    parser.add_argument('--gamma', default=0.9, type=float)
    parser.add_argument('--clip', default=10, type=float)
    parser.add_argument('--bptt', default=8, type=int)
    parser.add_argument('--exploration_method', default='softmax', type=str, choices=['eps', 'softmax'])
    parser.add_argument('--w_pg', default=1, type=float)
    parser.add_argument('--w_td', default=1, type=float)
    parser.add_argument('--w_il', default=0, type=float)
    parser.add_argument('--w_en', default=1, type=float)
    parser.add_argument('--network', default='bert', type=str, choices=['bert', 'rnn'])
    parser.add_argument('--bert_path', default='', type=str, help='which bert to load')
    parser.add_argument('--embedding_dim', default=128, type=int)
    parser.add_argument('--hidden_dim', default=128, type=int)
    parser.add_argument('--grad_encoder', default=1, type=int)
    parser.add_argument('--get_image', default=1, type=int, help='use image in models')
    parser.add_argument('--num', default=None, type=int)
    parser.add_argument('--click_item_name', default=1, type=int)
    parser.add_argument('--state_format', default='text_rich', type=str)
    parser.add_argument('--human_goals', default=1, type=int, help='use human goals')
    parser.add_argument('--num_prev_obs', default=0, type=int, help='number of previous observations')
    parser.add_argument('--num_prev_actions', default=0, type=int, help='number of previous actions')
    parser.add_argument('--extra_search_path', default='./data/goal_query_predict.json', type=str, help='path for extra search queries')
    parser.add_argument('--ban_buy', default=0, type=int, help='ban buy action before selecting options')
    parser.add_argument('--score_handicap', default=0, type=int, help='provide score in state')
    parser.add_argument('--go_to_item', default=0, type=int)
    parser.add_argument('--go_to_search', default=0, type=int)
    parser.add_argument('--harsh_reward', default=0, type=int)
    parser.add_argument('--debug', default=0, type=int, help='debug mode')
    parser.add_argument('--f', help='a dummy argument to fool ipython', default='1')
    return parser.parse_known_args()

def main():
    args, unknown = parse_args()
    if args.debug:
        args.num_envs = 2
        args.wandb = 0
        args.human_goals = 0
        args.num = 100
    print(unknown)
    print(args)
    configure_logger(args.output_dir, args.wandb)
    agent = Agent(args)
    train_env = WebEnv(args, split='train', id='train_')
    server = train_env.env.server
    eval_env = WebEnv(args, split='eval', id='eval_', server=server)
    test_env = WebEnv(args, split='test', id='test_', server=server)
    envs = [WebEnv(args, split='train', server=server, id=f'train{i}_') for i in range(args.num_envs)]
    print('loaded')
    train(agent, eval_env, test_env, envs, args)

def parse_args():
    parser = argparse.ArgumentParser(description='Finetune a transformers model on a text classification task')
    parser.add_argument('--model_path', type=str, default='./ckpts/web_click/epoch_9/model.pth', help='Where to store the final model.')
    parser.add_argument('--mem', type=int, default=0, help='State with memory')
    parser.add_argument('--bart_path', type=str, default='./ckpts/web_search/checkpoint-800', help='BART model path if using it')
    parser.add_argument('--bart', type=bool, default=True, help='Flag to specify whether to use bart or not (default: True)')
    parser.add_argument('--image', type=bool, default=True, help='Flag to specify whether to use image or not (default: True)')
    parser.add_argument('--softmax', type=bool, default=True, help='Flag to specify whether to use softmax sampling or not (default: True)')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Finetune a transformers model on a text classification task')
    parser.add_argument('--task_name', type=str, default='mprc', help='The name of the glue task to train on.', choices=list(task_to_keys.keys()))
    parser.add_argument('--train_file', type=str, default=None, help='A csv or a json file containing the training data.')
    parser.add_argument('--validation_file', type=str, default=None, help='A csv or a json file containing the validation data.')
    parser.add_argument('--max_length', type=int, default=128, help='The maximum total input sequence length after tokenization. Sequences longer than this will be truncated, sequences shorter will be padded if `--pad_to_max_lengh` is passed.')
    parser.add_argument('--pad_to_max_length', action='store_true', help='If passed, pad all samples to `max_length`. Otherwise, dynamic padding is used.')
    parser.add_argument('--model_name_or_path', default='bert-base-uncased', type=str, help='Path to pretrained model or model identifier from huggingface.co/models.')
    parser.add_argument('--use_slow_tokenizer', action='store_true', help='If passed, will use a slow tokenizer (not backed by the 🤗 Tokenizers library).')
    parser.add_argument('--per_device_train_batch_size', type=int, default=1, help='Batch size (per device) for the training dataloader.')
    parser.add_argument('--per_device_eval_batch_size', type=int, default=8, help='Batch size (per device) for the evaluation dataloader.')
    parser.add_argument('--learning_rate', type=float, default=2e-05, help='Initial learning rate (after the potential warmup period) to use.')
    parser.add_argument('--weight_decay', type=float, default=0.0, help='Weight decay to use.')
    parser.add_argument('--num_train_epochs', type=int, default=10, help='Total number of training epochs to perform.')
    parser.add_argument('--max_train_steps', type=int, default=None, help='Total number of training steps to perform. If provided, overrides num_train_epochs.')
    parser.add_argument('--gradient_accumulation_steps', type=int, default=32, help='Number of updates steps to accumulate before performing a backward/update pass.')
    parser.add_argument('--lr_scheduler_type', type=SchedulerType, default='linear', help='The scheduler type to use.', choices=['linear', 'cosine', 'cosine_with_restarts', 'polynomial', 'constant', 'constant_with_warmup'])
    parser.add_argument('--num_warmup_steps', type=int, default=0, help='Number of steps for the warmup in the lr scheduler.')
    parser.add_argument('--output_dir', type=str, default='./ckpts/web_click', help='Where to store the final model.')
    parser.add_argument('--seed', type=int, default=None, help='A seed for reproducible training.')
    parser.add_argument('--push_to_hub', action='store_true', help='Whether or not to push the model to the Hub.')
    parser.add_argument('--hub_model_id', type=str, help='The name of the repository to keep in sync with the local `output_dir`.')
    parser.add_argument('--hub_token', type=str, help='The token to use to push to the Model Hub.')
    parser.add_argument('--checkpointing_steps', type=str, default='epoch', help="Whether the various states should be saved at the end of every n steps, or 'epoch' for each epoch.")
    parser.add_argument('--resume_from_checkpoint', type=str, default=None, help='If the training should continue from a checkpoint folder.')
    parser.add_argument('--with_tracking', type=int, default=1, help='Whether to load in all available experiment trackers from the environment and use them for logging.')
    parser.add_argument('--mem', type=int, default=0, help='State with memory')
    parser.add_argument('--image', type=int, default=1, help='State with image')
    parser.add_argument('--pretrain', type=int, default=1, help='Pretrained BERT or not')
    parser.add_argument('--logging_steps', type=int, default=10, help='Logging in training')
    args = parser.parse_args()
    if args.task_name is None and args.train_file is None and (args.validation_file is None):
        raise ValueError('Need either a task name or a training/validation file.')
    else:
        if args.train_file is not None:
            extension = args.train_file.split('.')[-1]
            assert extension in ['csv', 'json'], '`train_file` should be a csv or a json file.'
        if args.validation_file is not None:
            extension = args.validation_file.split('.')[-1]
            assert extension in ['csv', 'json'], '`validation_file` should be a csv or a json file.'
    if args.push_to_hub:
        assert args.output_dir is not None, 'Need an `output_dir` to create a repo when `--push_to_hub` is passed.'
    return args

class TensorBoardOutputFormat(KVWriter):
    """
    Dumps key/value pairs into TensorBoard's numeric format.
    """

    def __init__(self, dir):
        os.makedirs(dir, exist_ok=True)
        self.dir = dir
        self.step = 1
        prefix = 'events'
        path = osp.join(osp.abspath(dir), prefix)
        import tensorflow as tf
        from tensorflow.python import pywrap_tensorflow
        from tensorflow.core.util import event_pb2
        from tensorflow.python.util import compat
        self.tf = tf
        self.event_pb2 = event_pb2
        self.pywrap_tensorflow = pywrap_tensorflow
        self.writer = pywrap_tensorflow.EventsWriter(compat.as_bytes(path))

    def writekvs(self, kvs):

        def summary_val(k, v):
            kwargs = {'tag': k, 'simple_value': float(v)}
            return self.tf.Summary.Value(**kwargs)
        summary = self.tf.Summary(value=[summary_val(k, v) for k, v in kvs.items()])
        event = self.event_pb2.Event(wall_time=time.time(), summary=summary)
        event.step = self.step
        self.writer.WriteEvent(event)
        self.writer.Flush()
        self.step += 1

    def close(self):
        if self.writer:
            self.writer.Close()
            self.writer = None

def __init__(self, dir):
    os.makedirs(dir, exist_ok=True)
    self.dir = dir
    self.step = 1
    prefix = 'events'
    path = osp.join(osp.abspath(dir), prefix)
    import tensorflow as tf
    from tensorflow.python import pywrap_tensorflow
    from tensorflow.core.util import event_pb2
    from tensorflow.python.util import compat
    self.tf = tf
    self.event_pb2 = event_pb2
    self.pywrap_tensorflow = pywrap_tensorflow
    self.writer = pywrap_tensorflow.EventsWriter(compat.as_bytes(path))

def make_output_format(format, ev_dir, log_suffix='', args=None):
    os.makedirs(ev_dir, exist_ok=True)
    if format == 'stdout':
        return HumanOutputFormat(sys.stdout)
    elif format == 'log':
        return HumanOutputFormat(osp.join(ev_dir, 'log%s.txt' % log_suffix))
    elif format == 'json':
        return JSONOutputFormat(osp.join(ev_dir, 'progress%s.json' % log_suffix))
    elif format == 'csv':
        return CSVOutputFormat(osp.join(ev_dir, 'progress%s.csv' % log_suffix))
    elif format == 'tensorboard':
        return TensorBoardOutputFormat(osp.join(ev_dir, 'tb%s' % log_suffix))
    elif format == 'wandb':
        return WandBOutputFormat(ev_dir)
    else:
        raise ValueError('Unknown format specified: %s' % (format,))

