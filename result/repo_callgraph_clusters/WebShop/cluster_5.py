# Cluster 5

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

def close(self):
    self.browser.close()
    print('Browser closed.')

def read_html_template(path):
    with open(path) as f:
        template = f.read()
    return template

def read_html_template(path):
    with open(path) as f:
        template = f.read()
    return template

def run_episode(goal, env, verbose=True):
    """
    Interact with amazon to find a product given input goal.
    Input: text goal
    Output: a url of found item on amazon.
    """
    env = env.lower()
    if env not in ENVIRONMENTS:
        print(f'[ERROR] Environment {env} not recognized')
    obs = 'Amazon Shopping Game\nInstruction:' + goal + '\n[button] search [button]'
    info = {'valid': ['search[stuff]'], 'image_feat': torch.zeros(512)}
    product_map = {}
    title_to_asin_map = {}
    search_results_cache = {}
    visited_asins, clicked_options = (set(), set())
    sub_page_type, page_type, page_num = (None, None, None)
    search_terms, prod_title, asin = (None, None, None)
    options = {}
    for i in range(100):
        action = predict(obs, info)
        if verbose:
            print('====')
            print(action)
        action_content = action[action.find('[') + 1:action.find(']')]
        prev_page_type = page_type
        if action.startswith('search['):
            page_type = Page.RESULTS
            search_terms = action_content
            page_num = 1
        elif action.startswith('click['):
            if action.startswith('click[item -'):
                prod_title = action_content[len('item -'):].strip()
                found = False
                for key in title_to_asin_map:
                    if prod_title == key:
                        asin = title_to_asin_map[key]
                        page_type = Page.ITEM_PAGE
                        visited_asins.add(asin)
                        found = True
                        break
                if not found:
                    raise Exception('Product to click not found')
            elif any((x.value in action for x in [Page.DESC, Page.FEATURES, Page.REVIEWS])):
                page_type = Page.SUB_PAGE
                sub_page_type = Page(action_content.lower())
            elif action == 'click[< prev]':
                if sub_page_type is not None:
                    page_type, sub_page_type = (Page.ITEM_PAGE, None)
                elif prev_page_type == Page.ITEM_PAGE:
                    page_type = Page.RESULTS
                    options, clicked_options = ({}, set())
                elif prev_page_type == Page.RESULTS and page_num > 1:
                    page_type = Page.RESULTS
                    page_num -= 1
            elif action == 'click[next >]':
                page_type = Page.RESULTS
                page_num += 1
            elif action.lower() == 'click[back to search]':
                page_type = Page.SEARCH
            elif action == 'click[buy now]':
                return get_return_value(env, asin, options, search_terms, page_num, product_map[asin])
            elif prev_page_type == Page.ITEM_PAGE:
                found = False
                for opt_name, opt_values in product_map[asin]['options'].items():
                    if action_content in opt_values:
                        options[opt_name] = action_content
                        page_type = Page.ITEM_PAGE
                        clicked_options.add(action_content)
                        found = True
                        break
                if not found:
                    raise Exception('Unrecognized action: ' + action)
        else:
            raise Exception('Unrecognized action:' + action)
        if verbose:
            print(f'Parsing {page_type.value} page...')
        if page_type == Page.RESULTS:
            if search_terms in search_results_cache:
                data = search_results_cache[search_terms]
                if verbose:
                    print(f'Loading cached results page for "{search_terms}"')
            else:
                begin = time.time()
                if env == 'amazon':
                    data = parse_results_amz(search_terms, page_num, verbose)
                if env == 'webshop':
                    data = parse_results_ws(search_terms, page_num, verbose)
                if env == 'ebay':
                    data = parse_results_ebay(search_terms, page_num, verbose)
                end = time.time()
                if verbose:
                    print(f'Parsing search results took {end - begin} seconds')
                search_results_cache[search_terms] = data
                for d in data:
                    title_to_asin_map[d['Title']] = d['asin']
        elif page_type == Page.ITEM_PAGE or page_type == Page.SUB_PAGE:
            if asin in product_map:
                if verbose:
                    print('Loading cached item page for', asin)
                data = product_map[asin]
            else:
                begin = time.time()
                if env == 'amazon':
                    data = parse_item_page_amz(asin, verbose)
                if env == 'webshop':
                    data = parse_item_page_ws(asin, search_terms, page_num, options, verbose)
                if env == 'ebay':
                    data = parse_item_page_ebay(asin, verbose)
                end = time.time()
                if verbose:
                    print('Parsing item page took', end - begin, 'seconds')
                product_map[asin] = data
        elif page_type == Page.SEARCH:
            if verbose:
                print('Executing search')
            obs = 'Amazon Shopping Game\nInstruction:' + goal + '\n[button] search [button]'
            info = {'valid': ['search[stuff]'], 'image_feat': torch.zeros(512)}
            continue
        else:
            raise Exception('Page of type `', page_type, '` not found')
        begin = time.time()
        html_str = dict_to_fake_html(data, page_type, asin, sub_page_type, options, product_map, goal)
        obs = convert_html_to_text(html_str, simple=False, clicked_options=clicked_options, visited_asins=visited_asins)
        end = time.time()
        if verbose:
            print('[Page Info -> WebShop HTML -> Observation] took', end - begin, 'seconds')
        begin = time.time()
        prod_arg = product_map if page_type == Page.ITEM_PAGE else data
        info = convert_dict_to_actions(page_type, prod_arg, asin, page_num)
        end = time.time()
        if verbose:
            print('Extracting available actions took', end - begin, 'seconds')
        if i == 50:
            return get_return_value(env, asin, options, search_terms, page_num, product_map[asin])

class WebEnv:
    """ A wrapper of textEnv for models. Returns valid actions at each step of the game. """

    def __init__(self, args, split, server=None, id=None):
        self.env = WebAgentTextEnv(observation_mode=args.state_format, server=server, filter_goals=None, limit_goals=-1, num_products=args.num, human_goals=args.human_goals, get_image=args.get_image, num_prev_obs=args.num_prev_obs, num_prev_actions=args.num_prev_actions, session_prefix=id)
        if args.num is None:
            if split == 'test':
                self.goal_idxs = range(500)
            elif split == 'eval':
                self.goal_idxs = range(500, 1500)
            elif split == 'train':
                self.goal_idxs = range(1500, len(self.env.server.goals))
        else:
            self.goal_idxs = range(len(self.env.server.goals))
        print(self.goal_idxs)
        self.steps = 0
        self.step_limit = args.step_limit
        self.stats = defaultdict(int)
        self.session = None
        self.click_item_name = args.click_item_name
        self.asin2name = {k.lower(): v['Title'].lower() for k, v in self.env.server.product_item_dict.items()}
        self.name2asin = {v: k for k, v in self.asin2name.items()}
        self.attributes_fail = defaultdict(int)
        self.attributes_success = defaultdict(int)
        self.items_clicked = defaultdict(int)
        self.harsh_reward = args.harsh_reward
        self.go_to_item = args.go_to_item
        self.go_to_search = args.go_to_search
        self.ban_buy = args.ban_buy
        self.prev_ob = self.cur_ob = None
        self.get_image = args.get_image
        self.item_rank = -1
        self.reduce_click = 1
        if args.extra_search_path != '':
            self.extra_search = json.load(open(args.extra_search_path))
            self.extra_search = {k.strip('.'): v for k, v in self.extra_search.items()}
        else:
            self.extra_search = None

    def get_search_texts(self, atts, query, inst):
        if self.extra_search is not None:
            if ', and price lower than' in inst:
                idx = inst.find(', and price lower than')
                inst_ = inst[:idx]
            else:
                inst_ = inst
            texts = self.extra_search.get(inst_, []) + [inst.lower()]
        else:
            texts = [query] + [f'{att} {query}' for att in atts] + [inst.lower()]
        return texts

    def get_valid_actions(self):
        valid_info = self.env.get_available_actions()
        if valid_info['has_search_bar']:
            atts = self.session['goal']['attributes']
            query = self.session['goal']['query']
            inst = self.session['goal']['instruction_text']
            texts = self.get_search_texts(atts, query, inst)
            valids = [f'search[{text}]' for text in texts]
        else:
            valids = []
            for text in valid_info['clickables']:
                if text == 'buy now' and self.ban_buy:
                    cur_options = len(self.session['options'])
                    all_options = len(self.env.server.product_item_dict[self.session['asin']]['customization_options'])
                    if cur_options != all_options:
                        continue
                if text != 'search':
                    if self.click_item_name and text in self.asin2name:
                        text = 'item - ' + self.asin2name[text]
                    valids.append(f'click[{text}]')
                if self.reduce_click and len(valids) > 20:
                    valids = valids[:6] + random.sample(valids[6:], 10)
        if len(valids) == 0:
            valids = ['finish']
        return valids

    def score(self):
        """
        Calculate the score of the current state.
        """
        valid_acts = self.get_valid_actions()
        if 'click[description]' not in valid_acts:
            return 0.0
        product = self.env.server.product_item_dict[self.session['asin']]
        goal = self.session['goal']
        price = self.env.server.product_prices.get(self.session['asin'])
        options = self.session['options']
        return get_reward(product, goal, price, options)

    def estimate_score(self, atts, opts, verify=False):
        """
        Calculate the score of the current state.
        """
        valid_acts = self.get_valid_actions()
        assert 'click[description]' in valid_acts
        desc = self.step('click[description]')[0].lower()
        self.step('click[< prev]')
        feat = self.step('click[features]')[0].lower()
        ob = self.step('click[< prev]')[0].lower()
        n_att = 0
        for att in atts:
            if att in desc or att in feat or att in ob:
                n_att += 1
        r_att = n_att / len(atts)
        n_opt = 0
        for opt in opts:
            for act in valid_acts:
                if opt in act:
                    n_opt += 1
                    break
        r_opt = n_opt / len(opts)
        r = (n_att + n_opt + 1) / (len(atts) + len(opts) + 1)
        return (r, r_att, r_opt)

    def step(self, action):
        if self.click_item_name and action.startswith('click[item - ') and (action[13:-1] in self.name2asin):
            valid_items = [_ for _ in self.get_valid_actions() if _.startswith('click[item - ')]
            if action in valid_items:
                self.item_rank = valid_items.index(action) + 1
            else:
                self.item_rank = -1
            action = f'click[{self.name2asin[action[13:-1]]}]'
        ob, reward, done, info = self.env.step(action)
        if action.startswith('click[') and action[6:-1] in self.asin2name:
            self.items_clicked[action[6:-1]] += 1
            desc = self.env.step('click[description]')[0].lower()
            self.env.step('click[< prev]')
            feat = self.env.step('click[features]')[0].lower()
            self.env.step('click[< prev]')
        else:
            desc = feat = ''
        r_visit = 0.0
        self.cur_ob, self.prev_ob = (ob, self.cur_ob)
        if info is None:
            info = {}
        self.steps += 1
        if self.step_limit and self.steps >= self.step_limit:
            done = True
        if done:
            info['verbose'] = self.session.get('verbose_info', {'r_att': 0.0, 'r_option': 0.0, 'r_price': 0.0, 'r_type': 0.0, 'w_att': 0.0, 'w_option': 0.0, 'w_price': 0.0})
            verbose = info['verbose']
            verbose['r_harsh'] = reward == 1
            verbose['r_exact'] = reward == 1 and self.session['goal']['asin'] == self.session['asin']
            verbose['r_norm'] = reward / self.steps
            verbose['r_visit'] = r_visit
            verbose['rank_item'] = self.item_rank
            if self.harsh_reward:
                reward = verbose['r_harsh']
            for k, v in self.session['actions'].items():
                self.stats[f'action_{k}'] += v
            cat = self.session['goal']['category']
            self.stats[f'cat_{cat}'] += 1
            for att in self.session['goal']['attributes']:
                if att in info['verbose'].get('purchased_attrs', []):
                    self.attributes_success[att] += 1
                else:
                    self.attributes_fail[att] += 1
        info.update({'valid': self.get_valid_actions(), 'goal': self.env.instruction_text, 'score': reward * 10, 'estimate_score': self.score(), 'prev_ob': self.prev_ob, 'desc': desc, 'feat': feat})
        if self.get_image:
            image_feat = self.env.get_image()
            info['image_feat'] = image_feat
        return (ob, (reward + r_visit) * 10, done, info)

    def reset(self, idx=None):
        if idx is None:
            idx = random.sample(self.goal_idxs, k=1)[0]
        ob, info = self.env.reset(idx)
        self.session = self.env.server.user_sessions[self.env.session]
        if info is None:
            info = {}
        self.cur_ob, self.prev_ob = (ob, None)
        info.update({'valid': self.get_valid_actions(), 'goal': self.env.instruction_text, 'score': 0, 'estimate_score': self.score(), 'prev_ob': self.prev_ob, 'desc': '', 'feat': ''})
        self.steps = 0
        if self.go_to_search or self.go_to_item:
            name = self.session['goal']['name'].lower()
            ob, _, _, info = self.step(f'search[{name}]')
            self.stats['action_go_to_search'] += 1
            if self.go_to_item:
                asin = self.session['goal']['asin'].lower()
                if asin in self.env.get_available_actions()['clickables']:
                    ob, _, _, info = self.step(f'click[{asin}]')
                    self.stats['action_go_to_item'] += 1
        self.item_rank = -1
        return (ob, info)

    def close(self):
        self.env.close()

def close(self):
    self.env.close()

class HumanOutputFormat(KVWriter, SeqWriter):

    def __init__(self, filename_or_file):
        if isinstance(filename_or_file, str):
            self.file = open(filename_or_file, 'wt')
            self.own_file = True
        else:
            assert hasattr(filename_or_file, 'read'), 'expected file or str, got %s' % filename_or_file
            self.file = filename_or_file
            self.own_file = False

    def writekvs(self, kvs):
        key2str = {}
        for key, val in sorted(kvs.items()):
            if isinstance(val, float):
                valstr = '%-8.3g' % (val,)
            else:
                valstr = str(val)
            key2str[self._truncate(key)] = self._truncate(valstr)
        if len(key2str) == 0:
            print('WARNING: tried to write empty key-value dict')
            return
        else:
            keywidth = max(map(len, key2str.keys()))
            valwidth = max(map(len, key2str.values()))
        dashes = '-' * (keywidth + valwidth + 7)
        lines = [dashes]
        for key, val in sorted(key2str.items()):
            lines.append('| %s%s | %s%s |' % (key, ' ' * (keywidth - len(key)), val, ' ' * (valwidth - len(val))))
        lines.append(dashes)
        self.file.write('\n'.join(lines) + '\n')
        self.file.flush()

    def _truncate(self, s):
        return s[:20] + '...' if len(s) > 23 else s

    def writeseq(self, seq):
        seq = list(seq)
        for i, elem in enumerate(seq):
            self.file.write(elem)
            if i < len(seq) - 1:
                self.file.write(' ')
        self.file.write('\n')
        self.file.flush()

    def close(self):
        if self.own_file:
            self.file.close()

def close(self):
    if self.own_file:
        self.file.close()

class JSONOutputFormat(KVWriter):

    def __init__(self, filename):
        self.file = open(filename, 'wt')

    def writekvs(self, kvs):
        for k, v in sorted(kvs.items()):
            if hasattr(v, 'dtype'):
                v = v.tolist()
                kvs[k] = float(v)
        self.file.write(json.dumps(kvs) + '\n')
        self.file.flush()

    def close(self):
        self.file.close()

def __init__(self, filename):
    self.file = open(filename, 'wt')

def close(self):
    self.file.close()

class CSVOutputFormat(KVWriter):

    def __init__(self, filename):
        self.file = open(filename, 'w+t')
        self.keys = []
        self.sep = ','

    def writekvs(self, kvs):
        extra_keys = kvs.keys() - self.keys
        if extra_keys:
            self.keys.extend(extra_keys)
            self.file.seek(0)
            lines = self.file.readlines()
            self.file.seek(0)
            for i, k in enumerate(self.keys):
                if i > 0:
                    self.file.write(',')
                self.file.write(k)
            self.file.write('\n')
            for line in lines[1:]:
                self.file.write(line[:-1])
                self.file.write(self.sep * len(extra_keys))
                self.file.write('\n')
        for i, k in enumerate(self.keys):
            if i > 0:
                self.file.write(',')
            v = kvs.get(k)
            if v is not None:
                self.file.write(str(v))
        self.file.write('\n')
        self.file.flush()

    def close(self):
        self.file.close()

def __init__(self, filename):
    self.file = open(filename, 'w+t')
    self.keys = []
    self.sep = ','

def close(self):
    self.file.close()

class Logger(object):
    DEFAULT = None
    CURRENT = None

    def __init__(self, dir, output_formats):
        self.name2val = defaultdict(float)
        self.name2cnt = defaultdict(int)
        self.level = INFO
        self.dir = dir
        self.output_formats = output_formats

    def logkv(self, key, val):
        self.name2val[key] = val

    def logkv_mean(self, key, val):
        if val is None:
            self.name2val[key] = None
            return
        oldval, cnt = (self.name2val[key], self.name2cnt[key])
        self.name2val[key] = oldval * cnt / (cnt + 1) + val / (cnt + 1)
        self.name2cnt[key] = cnt + 1

    def dumpkvs(self):
        if self.level == DISABLED:
            return
        for fmt in self.output_formats:
            if isinstance(fmt, KVWriter):
                fmt.writekvs(self.name2val)
        self.name2val.clear()
        self.name2cnt.clear()

    def log(self, *args, level=INFO):
        if self.level <= level:
            self._do_log(args)

    def set_level(self, level):
        self.level = level

    def get_dir(self):
        return self.dir

    def close(self):
        for fmt in self.output_formats:
            fmt.close()

    def _do_log(self, args):
        for fmt in self.output_formats:
            if isinstance(fmt, SeqWriter):
                fmt.writeseq(map(str, args))

def close(self):
    for fmt in self.output_formats:
        fmt.close()

class scoped_configure(object):

    def __init__(self, dir=None, format_strs=None):
        self.dir = dir
        self.format_strs = format_strs
        self.prevlogger = None

    def __enter__(self):
        self.prevlogger = Logger.CURRENT
        configure(dir=self.dir, format_strs=self.format_strs)

    def __exit__(self, *args):
        Logger.CURRENT.close()
        Logger.CURRENT = self.prevlogger

def __exit__(self, *args):
    Logger.CURRENT.close()
    Logger.CURRENT = self.prevlogger

@requests_mock.Mocker(kw='mock')
def test_parse_item_page_ws(**kwargs):
    mock_file = open('tests/transfer/mocks/mock_parse_item_page_ws', 'rb')
    mock_body = mock_file.read()
    mock_file.close()
    mock_desc_file = open('tests/transfer/mocks/mock_parse_item_page_ws_desc', 'rb')
    mock_desc_body = mock_desc_file.read()
    mock_desc_file.close()
    mock_feat_file = open('tests/transfer/mocks/mock_parse_item_page_ws_feat', 'rb')
    mock_feat_body = mock_feat_file.read()
    mock_feat_file.close()
    mock_asin = 'B09P87V3LZ'
    mock_query = 'red basketball shoes'
    mock_options = {}
    query_str = '+'.join(mock_query.split())
    options_str = json.dumps(mock_options)
    url = f'{WEBSHOP_URL}/item_page/{WEBSHOP_SESSION}/{mock_asin}/{query_str}/1/{options_str}'
    url_desc = f'{WEBSHOP_URL}/item_sub_page/{WEBSHOP_SESSION}/{mock_asin}/{query_str}/1/Description/{options_str}'
    url_feat = f'{WEBSHOP_URL}/item_sub_page/{WEBSHOP_SESSION}/{mock_asin}/{query_str}/1/Features/{options_str}'
    print(f'Item Page URL: {url}')
    print(f'Item Description URL: {url_desc}')
    print(f'Item Features URL: {url_feat}')
    kwargs['mock'].get(url, content=mock_body)
    kwargs['mock'].get(url_desc, content=mock_desc_body)
    kwargs['mock'].get(url_feat, content=mock_feat_body)
    output = parse_item_page_ws(mock_asin, mock_query, 1, mock_options)
    expected = {'MainImage': 'https://m.media-amazon.com/images/I/51ltvkzGhGL.jpg', 'Price': '100.0', 'Rating': 'N.A.', 'Title': 'PMUYBHF Womens Fashion Flat Shoes Comfortable Running Shoes Sneakers Tennis Athletic Shoe Casual Walking Shoes', 'asin': mock_asin, 'option_to_image': {'6.5': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27size%27:%20%276.5%27%7D', '7.5': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27size%27:%20%277.5%27%7D', '8': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27size%27:%20%278%27%7D', '8.5': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27size%27:%20%278.5%27%7D', '9': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27size%27:%20%279%27%7D', 'black': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27color%27:%20%27black%27%7D', 'purple': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27color%27:%20%27purple%27%7D', 'red': 'http://3.83.245.205:3000/item_page/abc/B09P87V3LZ/%5B%27red%27%2C%20%27basketball%27%2C%20%27shoes%27%5D/1/%7B%27color%27:%20%27red%27%7D'}, 'options': {'color': ['black', 'purple', 'red'], 'size': ['6.5', '7.5', '8', '8.5', '9']}, 'BulletPoints': 'Pure Running Shoe\nComfort Flat Sneakers\n[FEATURES]: Soles with unique non-slip pattern, it has great abrasion resistant and provide protection when you walking or running. (Pure Running Shoe Mesh Walking Shoes Fashion Sneakers Slip On Sneakers Wedge Platform Loafers Modern Walking Shoes Sock Sneakers Platform Loafers Shoes Non Slip Running Shoes Athletic Tennis Shoes Blade Type Sneakers Lace-up Sneaker) sole\n[WIDE ANKLE DESIGN]: Perfect accord with human body engineering, green, healthy concept design make the walking shoes wear more comfortable, wide width wlking shoes. (Low Top Walking Shoes Fashion Canvas Sneakers Slip On Shoes Casual Walking Shoes Hidden Wedge Sneaker Low Top Canvas Sneakers Lace-up Classic Casual Shoes Walking Tennis Shoes Lightweight Casual Sneakers Slip on Sock Sneakers Air Cushion Platform Loafers Slip-On Mule Sneaker )\n[CUSHION WITH ARCH SUPPORT]: Gives you a comfort for all day long. Wear these lightweight walking shoes, let every step of moving on a comfortable feeling. (Fashion Casual Shoes Athletic Workout Shoes Fitness Sneaker Athletic Running Shoes Air Cushion Sneakers Stylish Athletic Shoes Lace Up Canvas Shoes Slip on Walking Shoe Fashion Sneakers Low Top Classic Sneakers Comfort Fall Shoes Memory Foam Slip On Sneakers Air Cushion Sneakers Running Walking Shoes)\n[NON-SLIP SOLE]: Made from ultra soft and lightweight RUBBER material,with the function of shock absorbing and cushioning,offering the best durability and traction. (Wedge Sneakers Walking Tennis Shoes Slip On Running Shoes Lightweight Fashion Sneakers Fashion Travel Shoes Walking Running Shoes Non Slip Running Shoes Athletic Tennis Sneakers Sports Walking Shoes Platform Fashion Sneaker Memory Foam Tennis Sneakers Running Jogging Shoes Sock Sneakers Canvas Fashion Sneakers)\n[OCCASIONS]: Ultra lightweight design provides actual feelings of being barefooted and like walking on the feather, perfect for walking, hiking, bike riding, working, shopping, indoor, outdoor, casual, sports, travel, exercise, vacation, and etc. (Flat Fashion Sneakers Lightweight Walking Sneakers Platform Loafers Sport Running Shoes Casual Flat Loafers Slip-On Sneaker Casual Walking Shoes High Top Canvas Sneakers Lace up Sneakers Workout Walking Shoes Tennis Fitness Sneaker)\n[Customers Are Our Priority]: We follow the principle of customer first, so if you encounter any problems after buying shoes, we will try our best to solve them for you. (Breathable Air Cushion Sneakers Walking Tennis Shoes Air Athletic Running Shoes Air Cushion Shoes Mesh Sneakers Fashion Tennis Shoes Jogging Walking Sneakers Breathable Casual Sneakers Fashion Walking Shoes Athletic Running Sneakers Walking Work Shoes Air Running Shoes Slip on Sneakers Mesh Walking Shoes)', 'Description': 'Here Are The Things You Want To Knowa─=≡Σ(((つ̀ώ)つSTORE INTRODUCTION:>>>>Our store helps our customers improve their quality of life~As a distributor, we value quality and service.Focus on the high quality and durability of the product.Committed to creating a store that satisfies and reassures our customers.TIPS:>>>>1. Please allow minor errors in the data due to manual measurements.2. Due to the color settings of the display, the actual color may be slightly different from the online image.QUALITY PROMISE:>>>>Our goal is to continuously provide a range of quality products.We place a huge emphasis on the values of quality and reliability.We have always insisted on fulfilling this commitment.In short, we want our customers to have the same great product experience every time and be trusted to deliver on this commitment.Please give us a chance to serve you.OTHER:>>>>athletic sneaker laces athletic sneakers white athletic sneakers for women clearance leather Sneaker leather sneakers women leather sneakers for menleather sneaker laces leather sneaker platform basketball shoes basketball shoes for men basketball shoe laces basketball shoe grip basketball shoes for women fitness shoes for men fitness shoes women workout fitness shoes women fitness shoes women size 5 fitness shoes men workout fitness shoes for men high top sneakers for women walking shoes sneakers with arch support for women'}
    assert output == expected

@requests_mock.Mocker(kw='mock')
def test_parse_item_page_ebay(**kwargs):
    mock_file = open('tests/transfer/mocks/mock_parse_item_page_ebay', 'rb')
    mock_body = mock_file.read()
    mock_file.close()
    mock_asin = '403760625150'
    kwargs['mock'].get(f'https://www.ebay.com/itm/{mock_asin}', content=mock_body)
    output = parse_item_page_ebay(mock_asin)
    expected = {'BulletPoints': 'Item specifics Condition:New without box: A brand-new, unused, and unworn item (including handmade items) that is not in ...  Read moreabout the conditionNew without box: A brand-new, unused, and unworn item (including handmade items) that is not in original packaging or may be missing original packaging materials (such as the original box or bag). The original tags may not be attached. For example, new shoes (with absolutely no signs of wear) that are no longer in their original box fall into this category.  See all condition definitionsopens in a new window or tab  Closure:Lace Up US Shoe Size:10 Occasion:Activewear, Casual Silhouette:Puma Fabric Type:Mesh Vintage:No Cushioning Level:Moderate Department:Men Style:Sneaker Outsole Material:Rubber Features:Breathable, Comfort, Cushioned, Performance Season:Fall, Spring, Summer, Winter Idset_Mpn:193990-21 Shoe Shaft Style:Low Top Style Code:193990-16 Pattern:Solid Character:J. Cole Lining Material:Synthetic Color:Red Brand:PUMA Type:Athletic Customized:No Model:RS-Dreamer Theme:Sports Shoe Width:Standard Upper Material:Textile Insole Material:Synthetic Performance/Activity:Basketball Product Line:Puma Dreamer', 'Description': 'N/A', 'MainImage': 'https://i.ebayimg.com/images/g/4ggAAOSwpk1ioTWz/s-l500.jpg', 'Price': 'N/A', 'Rating': None, 'Title': "Puma RS-Dreamer J. Cole Basketball Shoes Red 193990-16 Men's Size 10.0", 'asin': '403760625150', 'option_to_image': {}, 'options': {}}
    assert output == expected

@requests_mock.Mocker(kw='mock')
def test_parse_item_page_amz(**kwargs):
    mock_file = open('tests/transfer/mocks/mock_parse_item_page_amz', 'rb')
    mock_body = mock_file.read()
    mock_file.close()
    mock_asin = 'B073WRF565'
    kwargs['mock'].get(f'https://www.amazon.com/dp/{mock_asin}', content=mock_body)
    output = parse_item_page_amz(mock_asin)
    expected = {'asin': 'B073WRF565', 'Title': 'Amazon Basics Foldable 14" Black Metal Platform Bed Frame with Tool-Free Assembly No Box Spring Needed - Full', 'Price': 'N/A', 'Rating': '4.8 out of 5 stars', 'BulletPoints': ' \n About this item    Product dimensions: 75" L x 54" W x 14" H | Weight: 41.4 pounds    Designed for sleepers up to 250 pounds    Full size platform bed frame offers a quiet, noise-free, supportive foundation for a mattress. No box spring needed    Folding mechanism makes the frame easy to store and move in tight spaces    Provides extra under-the-bed storage space with a vertical clearance of about 13 inches    \n › See more product details ', 'Description': 'Amazon Basics Foldable, 14" Black Metal Platform Bed Frame with Tool-Free Assembly, No Box Spring Needed - Full   Amazon Basics', 'MainImage': 'https://images-na.ssl-images-amazon.com/images/I/41WIGwt-asL.__AC_SY300_SX300_QL70_FMwebp_.jpg', 'options': {'size': ['Twin', 'Full', 'Queen', 'King'], 'style': ['14-Inch', '18-Inch']}, 'option_to_image': {}}
    assert output == expected

@requests_mock.Mocker(kw='mock')
def test_parse_results_ebay(**kwargs):
    mock_file = open('tests/transfer/mocks/mock_parse_results_ebay', 'rb')
    mock_body = mock_file.read()
    mock_file.close()
    mock_query = 'red basketball shoes'
    query = mock_query.replace(' ', '+')
    kwargs['mock'].get(f'https://www.ebay.com/sch/i.html?_nkw={query}&_pgn=1', content=mock_body)
    output = parse_results_ebay(mock_query, 1)
    expected = [{'Price': ['100.00', '150.00'], 'Title': "Reebok Answer IV Men's Basketball Shoes", 'asin': '175065123030'}, {'Price': '$119.90', 'Title': "Air Jordan Stay Loyal Shoes Black Red White DB2884-001 Men's Multi Size NEW", 'asin': '265672133690'}, {'Price': '$100.00', 'Title': "Fila Men's Stackhouse Spaghetti Basketball Shoes Black Red White 1BM01788-113", 'asin': '175282509234'}, {'Price': ['61.99', '85.99'], 'Title': 'Puma Disc Rebirth 19481203 Mens Black Red Synthetic Athletic Basketball Shoes', 'asin': '313944854658'}, {'Price': '$0.01', 'Title': "Puma RS-Dreamer J. Cole Basketball Shoes Red 193990-16 Men's Size 10.0", 'asin': '403760625150'}, {'Price': '$45.00', 'Title': 'Nike Mens 9.5 PG 5  Maroon Red White Basketball Shoes Sneaker DM 5045–601￼ Flaw', 'asin': '115456853186'}, {'Price': ['114.90', '119.90'], 'Title': "Air Jordan Stay Loyal Shoes White Black Red DB2884-106 Men's Multi Size NEW", 'asin': '155046831159'}, {'Price': '$8.99', 'Title': "Harden Volume 3 Men's Basketball Shoes Size 9.5", 'asin': '175342407862'}, {'Price': '$59.97', 'Title': "Men's Nike Precision 5 Basketball Shoes Gym Red Black Grey Bred Multi Size NEW", 'asin': '134149634710'}]
    assert output == expected

@requests_mock.Mocker(kw='mock')
def test_parse_results_amz(**kwargs):
    mock_file = open('tests/transfer/mocks/mock_parse_results_amz', 'rb')
    mock_body = mock_file.read()
    mock_file.close()
    mock_query = 'red basketball shoes'
    query = mock_query.replace(' ', '+')
    kwargs['mock'].get(f'https://www.amazon.com/s?k={query}&page=1', content=mock_body)
    output = parse_results_amz(mock_query, 1)
    expected = [{'Price': '59.49', 'Title': 'High Top Mens Basketball Shoes Lou Williams Streetball Master Breathable Non Slip Outdoor Sneakers Cushioning Workout Shoes for Fitness', 'asin': 'B083QCWF61'}, {'Price': '45.99', 'Title': 'Kids Basketball Shoes High-top Sports Shoes Sneakers Durable Lace-up Non-Slip Running Shoes Secure for Little Kids Big Kids and Boys Girls', 'asin': 'B08FWWWQ11'}, {'Price': '64.99', 'Title': 'Unisex-Adult Lockdown 5 Basketball Shoe', 'asin': 'B0817BFNC4'}, {'Price': '63.75', 'Title': 'Unisex-Child Team Hustle D 9 (Gs) Sneaker', 'asin': 'B07HHTS79M'}, {'Price': '74.64', 'Title': 'Unisex-Adult D.O.N. Issue 3 Basketball Shoe', 'asin': 'B08N8DQLS2'}, {'Price': '104.90', 'Title': "Men's Lebron Witness IV Basketball Shoes", 'asin': 'B07TKMMHVB'}, {'Price': '36.68', 'Title': "Unisex-Child Pre-School Jet '21 Basketball Shoe", 'asin': 'B08N6VRHV4'}, {'Price': '59.98', 'Title': "Men's Triple Basketball Shoe", 'asin': 'B08QCL8VKM'}, {'Price': '45.98', 'Title': 'Unisex-Child Pre School Lockdown 4 Basketball Shoe', 'asin': 'B07HKP12DH'}, {'Price': '143.72', 'Title': "Men's Basketball Shoes", 'asin': 'B07SNR7HRF'}]
    assert output == expected

@requests_mock.Mocker(kw='mock')
def test_parse_results_ws(**kwargs):
    mock_file = open('tests/transfer/mocks/mock_parse_results_ws', 'rb')
    mock_body = mock_file.read()
    mock_file.close()
    mock_query = 'red basketball shoes'
    query_str = mock_query.replace(' ', '+')
    url = f'{WEBSHOP_URL}/search_results/{WEBSHOP_SESSION}/{query_str}/1'
    kwargs['mock'].get(url, content=mock_body)
    output = parse_results_ws(mock_query, 1)
    expected = [{'Price': [24.49, 39.99], 'Title': "BinGoDug Men's Basketball Shoes, Men's Fashion Sneakers, Air Basketball Shoes for Men, Womens Basketball Shoes, Mens Basketball Shoes, Boys Basketball Shoes, Youth Basketball Shoes Men Women", 'asin': 'B09GKFNQWT'}, {'Price': [1.89, 7.58], 'Title': "RQWEIN Comfortable Mesh Sneakers Men's Roading Running Shoes Tennis Shoes Casual Fashion Sneakers Outdoor Non Slip Gym Athletic Sport Shoes", 'asin': 'B09BFY2R3R'}, {'Price': 100.0, 'Title': 'PMUYBHF Womens Fashion Flat Shoes Comfortable Running Shoes Sneakers Tennis Athletic Shoe Casual Walking Shoes', 'asin': 'B09P87V3LZ'}, {'Price': 100.0, 'Title': 'PMUYBHF Fashion Travel Shoes Jogging Walking Sneakers Air Cushion Platform Loafers Air Cushion Mesh Shoes Walking Dance Shoes', 'asin': 'B09N6SNKC1'}, {'Price': 100.0, 'Title': "PMUYBHF Women's Ballet Flats Walking Flats Shoes Dressy Work Low Wedge Arch Suport Flats Shoes Slip On Dress Shoes", 'asin': 'B09N6X5S74'}, {'Price': 100.0, 'Title': "PWKSELW High-top Men's Basketball Shoes Outdoor Sports Shoes Cushioning Training Shoes Casual Running Shoes", 'asin': 'B09MDB9V5W'}, {'Price': 100.0, 'Title': "Women's Flat Shoes Classic Round Toe Slip Office Black Ballet Flats Walking Flats Shoes Casual Ballet Flats", 'asin': 'B09N6PDFRF'}, {'Price': 100.0, 'Title': "Women's Mid-Calf Boots Wide Calf Boots for Women Fashion Zipper Womens Shoes Pu Leather Casual Boots Womens Slip-On Womens Flat Shoes Med Heel Womens' Boots Winter Snow Boot Comfy Boots(,5.5)", 'asin': 'B09N8ZHFNM'}, {'Price': 100.0, 'Title': 'PMUYBHF Womens Leisure Fitness Running Sport Warm Sneakers Shoes Slip-On Mule Sneakers Womens Mules', 'asin': 'B09P87DWGR'}, {'Price': 100.0, 'Title': 'Men Dress Shoes Leather Modern Classic Business Shoes Lace Up Classic Office Shoes Business Formal Shoes for Men', 'asin': 'B09R9MMTKR'}]
    assert output == expected

def test_convert_dict_to_actions():
    asin = '334490012932'
    page_num = 2
    products = [{'asin': '125331076844', 'Title': 'Modern Tall Torchiere Floor Lamp Brushed Nickel Chrome Metal Decor Living Room', 'Price': '$129.95'}, {'asin': '125109985453', 'Title': 'Floor Lamps Set of 2 Polished Steel Crystal Glass for Living Room Bedroom', 'Price': '$179.99'}, {'asin': '125265434055', 'Title': 'Floor Lamp Nickel/Polished Concrete Finish with Off-White Linen Fabric Shade', 'Price': '$130.68'}, {'asin': '195197281169', 'Title': 'New ListingVintage Mid Century Modern Glass Amber Globe Tension Pole Floor Lamp Light', 'Price': '$165.00'}, {'asin': '195197512929', 'Title': 'New ListingVTG Brass Floor Lamp Glass Shade 63.5" Tall 12" Diameter Glass Shade Original', 'Price': '$279.45'}, {'asin': '304550250934', 'Title': 'Vintage Mid Century Modern 3 Light Tension Pole Floor Lamp glass shades atomic a', 'Price': '$149.99'}, {'asin': '175338033811', 'Title': 'Antique FOSTORIA Ornate Brass Piano  Adjustable Floor Oil Lamp up to 76" Tall !!', 'Price': '$1,995.00'}, {'asin': '334490012932', 'Title': 'Vintage Mid Century Glass Shade Amber Globe 3 Tension Pole Floor Lamp Light MCM', 'Price': '$128.00'}, {'asin': '185433933521', 'Title': 'Brass & Pink Glass Lotus 6 Petal Lamp Shades Set Of Two Replacement Parts As Is', 'Price': '$90.00'}]
    actions = convert_dict_to_actions(Page.RESULTS, products, asin, page_num)
    assert actions['valid'] == ['click[back to search]', 'click[< prev]', 'click[item - Modern Tall Torchiere Floor Lamp Brushed Nickel Chrome Metal Decor Living Room]', 'click[item - Floor Lamps Set of 2 Polished Steel Crystal Glass for Living Room Bedroom]', 'click[item - Floor Lamp Nickel/Polished Concrete Finish with Off-White Linen Fabric Shade]', 'click[item - New ListingVintage Mid Century Modern Glass Amber Globe Tension Pole Floor Lamp Light]', 'click[item - New ListingVTG Brass Floor Lamp Glass Shade 63.5" Tall 12" Diameter Glass Shade Original]', 'click[item - Vintage Mid Century Modern 3 Light Tension Pole Floor Lamp glass shades atomic a]', 'click[item - Antique FOSTORIA Ornate Brass Piano  Adjustable Floor Oil Lamp up to 76" Tall !!]', 'click[item - Vintage Mid Century Glass Shade Amber Globe 3 Tension Pole Floor Lamp Light MCM]', 'click[item - Brass & Pink Glass Lotus 6 Petal Lamp Shades Set Of Two Replacement Parts As Is]']
    asin = '224636269803'
    products = {'224636269803': {'asin': '224636269803', 'Title': 'Sony SRS-XB01 EXTRA BASS Portable Water-Resistant  Wireless Bluetooth Speaker', 'Price': '24.99', 'MainImage': 'https://i.ebayimg.com/images/g/jVEAAOSwCLBhXLuD/s-l500.jpg', 'Rating': None, 'options': {'Color': ['Black', 'White', 'Red', 'Blue']}, 'option_to_image': {}, 'Description': "eBay Sony EXTRA BASS Portable Water-Resistant Wireless Bluetooth SpeakerBRAND NEW ITEMFREE SHIPPING WITHIN USA30 DAY RETURN POLICYKey FeaturesEXTRA BASS for deep, punchy soundCompact portable designUp to 6 hours of battery lifeWater resistant for worry-free useSupplied with color-coordinated strap What's in the Box?Sony EXTRA BASS Portable Bluetooth SpeakerPower supplyUser manual HIGHLIGHTSMUSIC THAT TRAVELSSmall size but mighty in volume to deliver powerful beats wherever you travelHANDS FREE CALLINGWith the built-in microphone, taking calls from your smartphone is easy. SPLASHPROOF CASINGTake to the pool or beach without worrying about water damaging the speaker unit UPGRADE THE AUDIOWirelessly connects 2 speakers and achieve stereo sound with speaker add function LONGER BATTERY LIFELonger Virtual Happy Hours with this rechargeable speaker's 6 hour battery life Technical SpecsFeatureValueBrandSonyTypePortable speakerModel NumberSRSXB01BluetoothYesFrequency range2.4 GHzMax. Communication Range32 ftBattery LifeApprox. 6 hrsWater ProtectionIPX5Input and Output TerminalsStereo Mini Jack (IN)Dimensions (W x H x D)Approx. 3 1/4 × 2 3/8 × 2 1/4 inWeightApprox. 5.65 oz", 'BulletPoints': "Item specifics Condition:New: A brand-new, unused, unopened, undamaged item in its original packaging (where packaging is ...  Read moreabout the conditionNew: A brand-new, unused, unopened, undamaged item in its original packaging (where packaging is applicable). Packaging should be the same as what is found in a retail store, unless the item is handmade or was packaged by the manufacturer in non-retail packaging, such as an unprinted box or plastic bag. See the seller's listing for full details. See all condition definitionsopens in a new window or tab  Model:EXTRA BASS Connectivity:Bluetooth, Wireless Type:Portable Speaker System Compatible Model:EXTRA BASS, Portable Water-Resistant Features:Bluetooth, Water-Resistant MPN:SRS-XB01/B, SRS-XB01/L, SRS-XB01/R, SRS-XB01/W Brand:Sony"}}
    actions = convert_dict_to_actions(Page.ITEM_PAGE, products, asin, 1)
    assert actions['valid'] == ['click[back to search]', 'click[< prev]', 'click[description]', 'click[features]', 'click[buy now]', 'click[Black]', 'click[White]', 'click[Red]', 'click[Blue]']
    actions = convert_dict_to_actions(Page.SUB_PAGE, {}, '12345', 1)
    assert actions['valid'] == ['click[back to search]', 'click[< prev]']

