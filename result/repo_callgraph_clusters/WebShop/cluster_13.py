# Cluster 13

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

class HumanPolicy(BasePolicy):

    def __init__(self):
        super().__init__()

    def forward(self, observation, available_actions):
        action = input('> ')
        return action

def __init__(self):
    super().__init__()

class RandomPolicy(BasePolicy):

    def __init__(self):
        super().__init__()

    def forward(self, observation, available_actions):
        if available_actions['has_search_bar']:
            action = 'search[shoes]'
        else:
            action_arg = random.choice(available_actions['clickables'])
            action = f'click[{action_arg}]'
        return action

def __init__(self):
    super().__init__()

class RCDQN(nn.Module):

    def __init__(self, vocab_size, embedding_dim, hidden_dim, arch, grad, embs=None, gru_embed='embedding', get_image=0, bert_path=''):
        super().__init__()
        self.word_dim = embedding_dim
        self.word_emb = nn.Embedding(vocab_size, embedding_dim)
        if embs is not None:
            print('Loading embeddings of shape {}'.format(embs.shape))
            self.word_emb.weight.data.copy_(torch.from_numpy(embs))
        self.hidden_dim = hidden_dim
        self.keep_prob = 1.0
        self.rnn = EncoderRNN(self.word_dim, self.hidden_dim, 1, concat=True, bidir=True, layernorm='None', return_last=False)
        self.att_1 = BiAttention(self.hidden_dim * 2, 1 - self.keep_prob)
        self.att_2 = BiAttention(self.hidden_dim * 2, 1 - self.keep_prob)
        self.att_3 = BiAttention(embedding_dim, 1 - self.keep_prob)
        self.linear_1 = nn.Sequential(nn.Linear(self.hidden_dim * 8, self.hidden_dim), nn.LeakyReLU())
        self.rnn_2 = EncoderRNN(self.hidden_dim, self.hidden_dim, 1, concat=True, bidir=True, layernorm='layer', return_last=False)
        self.linear_2 = nn.Sequential(nn.Linear(self.hidden_dim * 12, self.hidden_dim * 2), nn.LeakyReLU())
        self.linear_3 = nn.Sequential(nn.Linear(self.hidden_dim * 2, self.hidden_dim), nn.LeakyReLU(), nn.Linear(self.hidden_dim, 1))
        self.get_image = get_image
        if self.get_image:
            self.linear_image = nn.Linear(512, self.hidden_dim)

    def prepare(self, ids):
        """
        Prepare the input for the encoder. Pass it through pad, embedding, and rnn.
        """
        lens = [len(_) for _ in ids]
        ids = [torch.tensor(_) for _ in ids]
        ids = nn.utils.rnn.pad_sequence(ids, batch_first=True).cuda()
        mask = (ids > 0).float()
        embed = self.word_emb(ids)
        output = self.rnn(embed, lens)
        return (ids, lens, mask, embed, output)

    def forward(self, state_batch, act_batch, value=False, q=False, act=False):
        if self.arch == 'bert':
            return self.bert_forward(state_batch, act_batch, value, q, act)
        obs_ids, obs_lens, obs_mask, obs_embed, obs_output = self.prepare([state.obs for state in state_batch])
        goal_ids, goal_lens, goal_mask, goal_embed, goal_output = self.prepare([state.goal for state in state_batch])
        state_output = self.att_1(obs_output, goal_output, goal_mask)
        state_output = self.linear_1(state_output)
        if self.get_image:
            images = [state.image_feat for state in state_batch]
            images = [torch.zeros(512) if _ is None else _ for _ in images]
            images = torch.stack([_ for _ in images]).cuda()
            images = self.linear_image(images)
            state_output = torch.cat([images.unsqueeze(1), state_output], dim=1)
            obs_lens = [_ + 1 for _ in obs_lens]
            obs_mask = torch.cat([obs_mask[:, :1], obs_mask], dim=1)
        state_output = self.rnn_2(state_output, obs_lens)
        if value:
            values = get_aggregated(state_output, obs_lens, 'mean')
            values = self.linear_3(values).squeeze(1)
        act_sizes = [len(_) for _ in act_batch]
        act_batch = list(itertools.chain.from_iterable(act_batch))
        act_ids, act_lens, act_mask, act_embed, act_output = self.prepare(act_batch)
        state_output, state_mask, state_lens = duplicate(state_output, obs_mask, obs_lens, act_sizes)
        goal_embed, goal_mask, goal_lens = duplicate(goal_embed, goal_mask, goal_lens, act_sizes)
        state_act_output = self.att_2(act_output, state_output, state_mask)
        goal_act_output = self.att_3(act_embed, goal_embed, goal_mask)
        output = torch.cat([state_act_output, goal_act_output], dim=-1)
        output = get_aggregated(output, act_lens, 'mean')
        output = self.linear_2(output)
        act_values = self.linear_3(output).squeeze(1)
        if not q:
            act_values = torch.cat([F.log_softmax(_, dim=0) for _ in act_values.split(act_sizes)], dim=0)
        if value:
            return (act_values, act_sizes, values)
        else:
            return (act_values, act_sizes)

def __init__(self, vocab_size, embedding_dim, hidden_dim, arch, grad, embs=None, gru_embed='embedding', get_image=0, bert_path=''):
    super().__init__()
    self.word_dim = embedding_dim
    self.word_emb = nn.Embedding(vocab_size, embedding_dim)
    if embs is not None:
        print('Loading embeddings of shape {}'.format(embs.shape))
        self.word_emb.weight.data.copy_(torch.from_numpy(embs))
    self.hidden_dim = hidden_dim
    self.keep_prob = 1.0
    self.rnn = EncoderRNN(self.word_dim, self.hidden_dim, 1, concat=True, bidir=True, layernorm='None', return_last=False)
    self.att_1 = BiAttention(self.hidden_dim * 2, 1 - self.keep_prob)
    self.att_2 = BiAttention(self.hidden_dim * 2, 1 - self.keep_prob)
    self.att_3 = BiAttention(embedding_dim, 1 - self.keep_prob)
    self.linear_1 = nn.Sequential(nn.Linear(self.hidden_dim * 8, self.hidden_dim), nn.LeakyReLU())
    self.rnn_2 = EncoderRNN(self.hidden_dim, self.hidden_dim, 1, concat=True, bidir=True, layernorm='layer', return_last=False)
    self.linear_2 = nn.Sequential(nn.Linear(self.hidden_dim * 12, self.hidden_dim * 2), nn.LeakyReLU())
    self.linear_3 = nn.Sequential(nn.Linear(self.hidden_dim * 2, self.hidden_dim), nn.LeakyReLU(), nn.Linear(self.hidden_dim, 1))
    self.get_image = get_image
    if self.get_image:
        self.linear_image = nn.Linear(512, self.hidden_dim)

class EncoderRNN(nn.Module):

    def __init__(self, input_size, num_units, nlayers, concat, bidir, layernorm, return_last):
        super().__init__()
        self.layernorm = layernorm == 'layer'
        if layernorm:
            self.norm = nn.LayerNorm(input_size)
        self.rnns = []
        for i in range(nlayers):
            if i == 0:
                input_size_ = input_size
                output_size_ = num_units
            else:
                input_size_ = num_units if not bidir else num_units * 2
                output_size_ = num_units
            self.rnns.append(nn.GRU(input_size_, output_size_, 1, bidirectional=bidir, batch_first=True))
        self.rnns = nn.ModuleList(self.rnns)
        self.init_hidden = nn.ParameterList([nn.Parameter(torch.zeros(size=(2 if bidir else 1, 1, num_units)), requires_grad=True) for _ in range(nlayers)])
        self.concat = concat
        self.nlayers = nlayers
        self.return_last = return_last
        self.reset_parameters()

    def reset_parameters(self):
        with torch.no_grad():
            for rnn_layer in self.rnns:
                for name, p in rnn_layer.named_parameters():
                    if 'weight_ih' in name:
                        torch.nn.init.xavier_uniform_(p.data)
                    elif 'weight_hh' in name:
                        torch.nn.init.orthogonal_(p.data)
                    elif 'bias' in name:
                        p.data.fill_(0.0)
                    else:
                        p.data.normal_(std=0.1)

    def get_init(self, bsz, i):
        return self.init_hidden[i].expand(-1, bsz, -1).contiguous()

    def forward(self, inputs, input_lengths=None):
        bsz, slen = (inputs.size(0), inputs.size(1))
        if self.layernorm:
            inputs = self.norm(inputs)
        output = inputs
        outputs = []
        lens = 0
        if input_lengths is not None:
            lens = input_lengths
        for i in range(self.nlayers):
            hidden = self.get_init(bsz, i)
            if input_lengths is not None:
                output = rnn.pack_padded_sequence(output, lens, batch_first=True, enforce_sorted=False)
            output, hidden = self.rnns[i](output, hidden)
            if input_lengths is not None:
                output, _ = rnn.pad_packed_sequence(output, batch_first=True)
                if output.size(1) < slen:
                    padding = torch.zeros(size=(1, 1, 1), dtype=output.type(), device=output.device())
                    output = torch.cat([output, padding.expand(output.size(0), slen - output.size(1), output.size(2))], dim=1)
            if self.return_last:
                outputs.append(hidden.permute(1, 0, 2).contiguous().view(bsz, -1))
            else:
                outputs.append(output)
        if self.concat:
            return torch.cat(outputs, dim=2)
        return outputs[-1]

def __init__(self, input_size, num_units, nlayers, concat, bidir, layernorm, return_last):
    super().__init__()
    self.layernorm = layernorm == 'layer'
    if layernorm:
        self.norm = nn.LayerNorm(input_size)
    self.rnns = []
    for i in range(nlayers):
        if i == 0:
            input_size_ = input_size
            output_size_ = num_units
        else:
            input_size_ = num_units if not bidir else num_units * 2
            output_size_ = num_units
        self.rnns.append(nn.GRU(input_size_, output_size_, 1, bidirectional=bidir, batch_first=True))
    self.rnns = nn.ModuleList(self.rnns)
    self.init_hidden = nn.ParameterList([nn.Parameter(torch.zeros(size=(2 if bidir else 1, 1, num_units)), requires_grad=True) for _ in range(nlayers)])
    self.concat = concat
    self.nlayers = nlayers
    self.return_last = return_last
    self.reset_parameters()

class BiAttention(nn.Module):

    def __init__(self, input_size, dropout):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.input_linear = nn.Linear(input_size, 1, bias=False)
        self.memory_linear = nn.Linear(input_size, 1, bias=False)
        self.dot_scale = nn.Parameter(torch.zeros(size=(input_size,)).uniform_(1.0 / input_size ** 0.5), requires_grad=True)
        self.init_parameters()

    def init_parameters(self):
        return

    def forward(self, context, memory, mask):
        bsz, input_len = (context.size(0), context.size(1))
        memory_len = memory.size(1)
        context = self.dropout(context)
        memory = self.dropout(memory)
        input_dot = self.input_linear(context)
        memory_dot = self.memory_linear(memory).view(bsz, 1, memory_len)
        cross_dot = torch.bmm(context * self.dot_scale, memory.permute(0, 2, 1).contiguous())
        att = input_dot + memory_dot + cross_dot
        att = att - 1e+30 * (1 - mask[:, None])
        weight_one = F.softmax(att, dim=-1)
        output_one = torch.bmm(weight_one, memory)
        weight_two = F.softmax(att.max(dim=-1)[0], dim=-1).view(bsz, 1, input_len)
        output_two = torch.bmm(weight_two, context)
        return torch.cat([context, output_one, context * output_one, output_two * output_one], dim=-1)

def __init__(self, input_size, dropout):
    super().__init__()
    self.dropout = nn.Dropout(dropout)
    self.input_linear = nn.Linear(input_size, 1, bias=False)
    self.memory_linear = nn.Linear(input_size, 1, bias=False)
    self.dot_scale = nn.Parameter(torch.zeros(size=(input_size,)).uniform_(1.0 / input_size ** 0.5), requires_grad=True)
    self.init_parameters()

class BertConfigForWebshop(PretrainedConfig):
    model_type = 'bert'

    def __init__(self, pretrained_bert=True, image=False, **kwargs):
        self.pretrained_bert = pretrained_bert
        self.image = image
        super().__init__(**kwargs)

def __init__(self, pretrained_bert=True, image=False, **kwargs):
    self.pretrained_bert = pretrained_bert
    self.image = image
    super().__init__(**kwargs)

class BertModelForWebshop(PreTrainedModel):
    config_class = BertConfigForWebshop

    def __init__(self, config):
        super().__init__(config)
        bert_config = BertConfig.from_pretrained('bert-base-uncased')
        if config.pretrained_bert:
            self.bert = BertModel.from_pretrained('bert-base-uncased')
        else:
            self.bert = BertModel(config)
        self.bert.resize_token_embeddings(30526)
        self.attn = BiAttention(768, 0.0)
        self.linear_1 = nn.Linear(768 * 4, 768)
        self.relu = nn.ReLU()
        self.linear_2 = nn.Linear(768, 1)
        if config.image:
            self.image_linear = nn.Linear(512, 768)
        else:
            self.image_linear = None
        self.linear_3 = nn.Sequential(nn.Linear(768, 128), nn.LeakyReLU(), nn.Linear(128, 1))

    def forward(self, state_input_ids, state_attention_mask, action_input_ids, action_attention_mask, sizes, images=None, labels=None):
        sizes = sizes.tolist()
        state_rep = self.bert(state_input_ids, attention_mask=state_attention_mask)[0]
        if images is not None and self.image_linear is not None:
            images = self.image_linear(images)
            state_rep = torch.cat([images.unsqueeze(1), state_rep], dim=1)
            state_attention_mask = torch.cat([state_attention_mask[:, :1], state_attention_mask], dim=1)
        action_rep = self.bert(action_input_ids, attention_mask=action_attention_mask)[0]
        state_rep = torch.cat([state_rep[i:i + 1].repeat(j, 1, 1) for i, j in enumerate(sizes)], dim=0)
        state_attention_mask = torch.cat([state_attention_mask[i:i + 1].repeat(j, 1) for i, j in enumerate(sizes)], dim=0)
        act_lens = action_attention_mask.sum(1).tolist()
        state_action_rep = self.attn(action_rep, state_rep, state_attention_mask)
        state_action_rep = self.relu(self.linear_1(state_action_rep))
        act_values = get_aggregated(state_action_rep, act_lens, 'mean')
        act_values = self.linear_2(act_values).squeeze(1)
        logits = [F.log_softmax(_, dim=0) for _ in act_values.split(sizes)]
        loss = None
        if labels is not None:
            loss = -sum([logit[label] for logit, label in zip(logits, labels)]) / len(logits)
        return SequenceClassifierOutput(loss=loss, logits=logits)

    def rl_forward(self, state_batch, act_batch, value=False, q=False, act=False):
        act_values = []
        act_sizes = []
        values = []
        for state, valid_acts in zip(state_batch, act_batch):
            with torch.set_grad_enabled(not act):
                state_ids = torch.tensor([state.obs]).cuda()
                state_mask = (state_ids > 0).int()
                act_lens = [len(_) for _ in valid_acts]
                act_ids = [torch.tensor(_) for _ in valid_acts]
                act_ids = nn.utils.rnn.pad_sequence(act_ids, batch_first=True).cuda()
                act_mask = (act_ids > 0).int()
                act_size = torch.tensor([len(valid_acts)]).cuda()
                if self.image_linear is not None:
                    images = [state.image_feat]
                    images = [torch.zeros(512) if _ is None else _ for _ in images]
                    images = torch.stack(images).cuda()
                else:
                    images = None
                logits = self.forward(state_ids, state_mask, act_ids, act_mask, act_size, images=images).logits[0]
                act_values.append(logits)
                act_sizes.append(len(valid_acts))
            if value:
                v = self.bert(state_ids, state_mask)[0]
                values.append(self.linear_3(v[0][0]))
        act_values = torch.cat(act_values, dim=0)
        act_values = torch.cat([F.log_softmax(_, dim=0) for _ in act_values.split(act_sizes)], dim=0)
        if value:
            values = torch.cat(values, dim=0)
            return (act_values, act_sizes, values)
        else:
            return (act_values, act_sizes)

def __init__(self, config):
    super().__init__(config)
    bert_config = BertConfig.from_pretrained('bert-base-uncased')
    if config.pretrained_bert:
        self.bert = BertModel.from_pretrained('bert-base-uncased')
    else:
        self.bert = BertModel(config)
    self.bert.resize_token_embeddings(30526)
    self.attn = BiAttention(768, 0.0)
    self.linear_1 = nn.Linear(768 * 4, 768)
    self.relu = nn.ReLU()
    self.linear_2 = nn.Linear(768, 1)
    if config.image:
        self.image_linear = nn.Linear(512, 768)
    else:
        self.image_linear = None
    self.linear_3 = nn.Sequential(nn.Linear(768, 128), nn.LeakyReLU(), nn.Linear(128, 1))

