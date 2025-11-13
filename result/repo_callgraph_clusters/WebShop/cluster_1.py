# Cluster 1

@app.route('/')
def home():
    return redirect(url_for('index', session_id='abc'))

@app.route('/<session_id>', methods=['GET', 'POST'])
def index(session_id):
    global user_log_dir
    global all_products, product_item_dict, product_prices, attribute_to_asins, search_engine, goals, weights, user_sessions
    if search_engine is None:
        all_products, product_item_dict, product_prices, attribute_to_asins = load_products(filepath=DEFAULT_FILE_PATH, num_products=DEBUG_PROD_SIZE)
        search_engine = init_search_engine(num_products=DEBUG_PROD_SIZE)
        goals = get_goals(all_products, product_prices)
        random.seed(233)
        random.shuffle(goals)
        weights = [goal['weight'] for goal in goals]
    if session_id not in user_sessions and 'fixed' in session_id:
        goal_dix = int(session_id.split('_')[-1])
        goal = goals[goal_dix]
        instruction_text = goal['instruction_text']
        user_sessions[session_id] = {'goal': goal, 'done': False}
        if user_log_dir is not None:
            setup_logger(session_id, user_log_dir)
    elif session_id not in user_sessions:
        goal = random.choices(goals, weights)[0]
        instruction_text = goal['instruction_text']
        user_sessions[session_id] = {'goal': goal, 'done': False}
        if user_log_dir is not None:
            setup_logger(session_id, user_log_dir)
    else:
        instruction_text = user_sessions[session_id]['goal']['instruction_text']
    if request.method == 'POST' and 'search_query' in request.form:
        keywords = request.form['search_query'].lower().split(' ')
        return redirect(url_for('search_results', session_id=session_id, keywords=keywords, page=1))
    if user_log_dir is not None:
        logger = logging.getLogger(session_id)
        logger.info(json.dumps(dict(page='index', url=request.url, goal=user_sessions[session_id]['goal'])))
    return map_action_to_html('start', session_id=session_id, instruction_text=instruction_text)

@app.route('/search_results/<session_id>/<keywords>/<page>', methods=['GET', 'POST'])
def search_results(session_id, keywords, page):
    instruction_text = user_sessions[session_id]['goal']['instruction_text']
    page = convert_web_app_string_to_var('page', page)
    keywords = convert_web_app_string_to_var('keywords', keywords)
    top_n_products = get_top_n_product_from_keywords(keywords, search_engine, all_products, product_item_dict, attribute_to_asins)
    products = get_product_per_page(top_n_products, page)
    html = map_action_to_html('search', session_id=session_id, products=products, keywords=keywords, page=page, total=len(top_n_products), instruction_text=instruction_text)
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(page='search_results', url=request.url, goal=user_sessions[session_id]['goal'], content=dict(keywords=keywords, search_result_asins=[p['asin'] for p in products], page=page))))
    return html

@app.route('/item_page/<session_id>/<asin>/<keywords>/<page>/<options>', methods=['GET', 'POST'])
def item_page(session_id, asin, keywords, page, options):
    options = literal_eval(options)
    product_info = product_item_dict[asin]
    goal_instruction = user_sessions[session_id]['goal']['instruction_text']
    product_info['goal_instruction'] = goal_instruction
    html = map_action_to_html('click', session_id=session_id, product_info=product_info, keywords=keywords, page=page, asin=asin, options=options, instruction_text=goal_instruction, show_attrs=SHOW_ATTRS_TAB)
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(page='item_page', url=request.url, goal=user_sessions[session_id]['goal'], content=dict(keywords=keywords, page=page, asin=asin, options=options))))
    return html

@app.route('/item_sub_page/<session_id>/<asin>/<keywords>/<page>/<sub_page>/<options>', methods=['GET', 'POST'])
def item_sub_page(session_id, asin, keywords, page, sub_page, options):
    options = literal_eval(options)
    product_info = product_item_dict[asin]
    goal_instruction = user_sessions[session_id]['goal']['instruction_text']
    product_info['goal_instruction'] = goal_instruction
    html = map_action_to_html(f'click[{sub_page}]', session_id=session_id, product_info=product_info, keywords=keywords, page=page, asin=asin, options=options, instruction_text=goal_instruction)
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(page='item_sub_page', url=request.url, goal=user_sessions[session_id]['goal'], content=dict(keywords=keywords, page=page, asin=asin, options=options))))
    return html

@app.route('/done/<session_id>/<asin>/<options>', methods=['GET', 'POST'])
def done(session_id, asin, options):
    options = literal_eval(options)
    goal = user_sessions[session_id]['goal']
    purchased_product = product_item_dict[asin]
    price = product_prices[asin]
    reward, reward_info = get_reward(purchased_product, goal, price=price, options=options, verbose=True)
    user_sessions[session_id]['done'] = True
    user_sessions[session_id]['reward'] = reward
    print(user_sessions)
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(page='done', url=request.url, goal=goal, content=dict(asin=asin, options=options, price=price), reward=reward, reward_info=reward_info)))
    del logging.root.manager.loggerDict[session_id]
    return map_action_to_html(f'click[{END_BUTTON}]', session_id=session_id, reward=reward, asin=asin, options=options, reward_info=reward_info, query=purchased_product['query'], category=purchased_product['category'], product_category=purchased_product['product_category'], goal_attrs=user_sessions[session_id]['goal']['attributes'], purchased_attrs=purchased_product['Attributes'], goal=goal, mturk_code=generate_mturk_code(session_id))

def setup_logger(session_id, user_log_dir):
    """Creates a log file and logging object for the corresponding session ID"""
    logger = logging.getLogger(session_id)
    formatter = logging.Formatter('%(message)s')
    file_handler = logging.FileHandler(user_log_dir / f'{session_id}.jsonl', mode='w')
    file_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

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
def state(self):
    """
        State that includes all information. The actual observation are
        likely to be a subset or reduced form of the state.
        """
    return dict(url=self.browser.current_url, html=self.browser.page_source, instruction_text=self.instruction_text)

class SimServer:
    """Lightweight simulator of WebShop Flask application for generating HTML observations"""

    def __init__(self, base_url, file_path, filter_goals=None, limit_goals=-1, num_products=None, human_goals=0, show_attrs=False):
        """
        Constructor for simulated server serving WebShop application
        
        Arguments:
        filter_goals (`func`) -- Select specific goal(s) for consideration based on criteria of custom function
        limit_goals (`int`) -- Limit to number of goals available
        num_products (`int`) -- Number of products to search across
        human_goals (`bool`) -- If true, load human goals; otherwise, load synthetic goals
        """
        self.base_url = base_url
        self.all_products, self.product_item_dict, self.product_prices, _ = load_products(filepath=file_path, num_products=num_products, human_goals=human_goals)
        self.search_engine = init_search_engine(num_products=num_products)
        self.goals = get_goals(self.all_products, self.product_prices, human_goals)
        self.show_attrs = show_attrs
        random.seed(233)
        random.shuffle(self.goals)
        if filter_goals is not None:
            self.goals = [goal for i, goal in enumerate(self.goals) if filter_goals(i, goal)]
        if limit_goals != -1 and limit_goals < len(self.goals):
            self.weights = [goal['weight'] for goal in self.goals]
            self.cum_weights = [0] + np.cumsum(self.weights).tolist()
            idxs = []
            while len(idxs) < limit_goals:
                idx = random_idx(self.cum_weights)
                if idx not in idxs:
                    idxs.append(idx)
            self.goals = [self.goals[i] for i in idxs]
        print(f'Loaded {len(self.goals)} goals.')
        self.weights = [goal['weight'] for goal in self.goals]
        self.cum_weights = [0] + np.cumsum(self.weights).tolist()
        self.user_sessions = dict()
        self.search_time = 0
        self.render_time = 0
        self.sample_time = 0
        self.assigned_instruction_text = None

    @app.route('/', methods=['GET', 'POST'])
    def index(self, session_id, **kwargs):
        """Redirect to the search page with the given session ID"""
        html = map_action_to_html('start', session_id=session_id, instruction_text=kwargs['instruction_text'])
        url = f'{self.base_url}/{session_id}'
        return (html, url)

    @app.route('/', methods=['GET', 'POST'])
    def search_results(self, session_id, **kwargs):
        """Initialize session and return the search results page"""
        session = self.user_sessions[session_id]
        keywords = kwargs['keywords']
        assert isinstance(keywords, list)
        page = 1 if 'page' not in kwargs else kwargs['page']
        session['page'] = page
        session['keywords'] = keywords
        session['actions']['search'] += 1
        session['asin'] = None
        session['options'] = {}
        old_time = time.time()
        top_n_products = get_top_n_product_from_keywords(keywords, self.search_engine, self.all_products, self.product_item_dict)
        self.search_time += time.time() - old_time
        products = get_product_per_page(top_n_products, page)
        keywords_url_string = '+'.join(keywords)
        url = f'{self.base_url}/search_results/{session_id}/{keywords_url_string}/{page}'
        old_time = time.time()
        html = map_action_to_html('search', session_id=session_id, products=products, keywords=session['keywords'], page=page, total=len(top_n_products), instruction_text=session['goal']['instruction_text'])
        self.render_time += time.time() - old_time
        return (html, url)

    @app.route('/', methods=['GET', 'POST'])
    def item_page(self, session_id, **kwargs):
        """Render and return the HTML for a product item page"""
        session = self.user_sessions[session_id]
        clickable_name = kwargs['clickable_name']
        text_to_clickable = kwargs['text_to_clickable']
        clickable = text_to_clickable[clickable_name]
        if clickable.get('class') is not None and clickable.get('class')[0] == 'product-link':
            session['asin'] = clickable_name.upper()
            session['actions']['asin'] += 1
            session['asins'].add(session['asin'])
        elif clickable.get('name') is not None:
            clickable_key = clickable['name'].lower()
            session['options'][clickable_key] = clickable_name
            session['actions']['options'] += 1
        product_info = self.product_item_dict[session['asin']]
        keywords_url_string = '+'.join(session['keywords'])
        option_string = json.dumps(session['options'])
        url = f'{self.base_url}/item_page/{session_id}/{session['asin']}/{keywords_url_string}/{session['page']}/{option_string}'
        html = map_action_to_html('click', session_id=session_id, product_info=product_info, keywords=session['keywords'], page=session['page'], asin=session['asin'], options=session['options'], instruction_text=session['goal']['instruction_text'], show_attrs=self.show_attrs)
        return (html, url)

    @app.route('/', methods=['GET', 'POST'])
    def item_sub_page(self, session_id, **kwargs):
        """Render and return the HTML for a product's sub page (i.e. description, features)"""
        session = self.user_sessions[session_id]
        clickable_name = kwargs['clickable_name']
        for k in ACTION_TO_TEMPLATE:
            if clickable_name.lower() == k.lower():
                clickable_name = k
                break
        product_info = self.product_item_dict[session['asin']]
        session['actions'][clickable_name] += 1
        keywords_url_string = '+'.join(session['keywords'])
        url = f'{self.base_url}/item_sub_page/{session_id}/{session['asin']}/{keywords_url_string}/{session['page']}/{clickable_name}/{session['options']}'
        html = map_action_to_html(f'click[{clickable_name}]', session_id=session_id, product_info=product_info, keywords=session['keywords'], page=session['page'], asin=session['asin'], options=session['options'], instruction_text=session['goal']['instruction_text'])
        return (html, url)

    @app.route('/', methods=['GET', 'POST'])
    def done(self, session_id, **kwargs):
        """Render and return HTML for done page"""
        session = self.user_sessions[session_id]
        goal = self.user_sessions[session_id]['goal']
        purchased_product = self.product_item_dict[session['asin']]
        session['actions']['purchase'] += 1
        price = self.product_prices.get(session['asin'])
        reward, info = get_reward(purchased_product, goal, price=price, options=session['options'], verbose=True)
        self.user_sessions[session_id]['verbose_info'] = info
        self.user_sessions[session_id]['done'] = True
        self.user_sessions[session_id]['reward'] = reward
        url = f'{self.base_url}/done/{session_id}/{session['asin']}/{session['options']}'
        html = map_action_to_html(f'click[{END_BUTTON}]', session_id=session_id, reward=reward, asin=session['asin'], options=session['options'], instruction_text=session['goal']['instruction_text'])
        return (html, url, reward)

    def receive(self, session_id, current_url, session_int=None, **kwargs):
        """Map action to the corresponding page"""
        status = dict(reward=0.0, done=False)
        with app.app_context(), app.test_request_context():
            if session_id not in self.user_sessions:
                idx = session_int if session_int is not None and isinstance(session_int, int) else random_idx(self.cum_weights)
                goal = self.goals[idx]
                instruction_text = goal['instruction_text']
                self.user_sessions[session_id] = {'goal': goal, 'done': False}
            else:
                instruction_text = self.user_sessions[session_id]['goal']['instruction_text']
            if self.assigned_instruction_text is not None:
                instruction_text = self.assigned_instruction_text
                self.user_sessions[session_id]['goal']['instruction_text'] = instruction_text
            session = self.user_sessions[session_id]
            if not kwargs:
                kwargs['instruction_text'] = instruction_text
                html, url = self.index(session_id, **kwargs)
                self.user_sessions[session_id].update({'keywords': None, 'page': None, 'asin': None, 'asins': set(), 'options': dict(), 'actions': defaultdict(int)})
            elif 'keywords' in kwargs:
                html, url = self.search_results(session_id, **kwargs)
            elif 'clickable_name' in kwargs:
                clickable_name = kwargs['clickable_name'].lower()
                if clickable_name == END_BUTTON.lower():
                    html, url, reward = self.done(session_id, **kwargs)
                    status['reward'] = reward
                    status['done'] = True
                elif clickable_name == BACK_TO_SEARCH.lower():
                    html, url, status = self.receive(session_id, current_url)
                elif clickable_name == NEXT_PAGE.lower() and self.get_page_name(current_url) == 'search_results':
                    html, url, status = self.receive(session_id, current_url, keywords=session['keywords'], page=session['page'] + 1)
                elif clickable_name == PREV_PAGE.lower() and self.get_page_name(current_url) == 'search_results':
                    html, url, status = self.receive(session_id, current_url, keywords=session['keywords'], page=session['page'] - 1)
                elif clickable_name == PREV_PAGE.lower() and self.get_page_name(current_url) == 'item_sub_page':
                    html, url = self.item_page(session_id, **kwargs)
                elif clickable_name == PREV_PAGE.lower() and self.get_page_name(current_url) == 'item_page':
                    html, url = self.search_results(session_id, keywords=session['keywords'], page=session['page'], **kwargs)
                elif clickable_name in [k.lower() for k in ACTION_TO_TEMPLATE]:
                    html, url = self.item_sub_page(session_id, **kwargs)
                else:
                    html, url = self.item_page(session_id, **kwargs)
            return (html, url, status)

    def get_page_name(self, url):
        """Determine which page (i.e. item_page, search_results) the given URL is pointing at"""
        if url is None:
            return None
        page_names = ['search_results', 'item_page', 'item_sub_page', 'done']
        for page_name in page_names:
            if page_name in url:
                return page_name
        return ''

def __init__(self, base_url, file_path, filter_goals=None, limit_goals=-1, num_products=None, human_goals=0, show_attrs=False):
    """
        Constructor for simulated server serving WebShop application
        
        Arguments:
        filter_goals (`func`) -- Select specific goal(s) for consideration based on criteria of custom function
        limit_goals (`int`) -- Limit to number of goals available
        num_products (`int`) -- Number of products to search across
        human_goals (`bool`) -- If true, load human goals; otherwise, load synthetic goals
        """
    self.base_url = base_url
    self.all_products, self.product_item_dict, self.product_prices, _ = load_products(filepath=file_path, num_products=num_products, human_goals=human_goals)
    self.search_engine = init_search_engine(num_products=num_products)
    self.goals = get_goals(self.all_products, self.product_prices, human_goals)
    self.show_attrs = show_attrs
    random.seed(233)
    random.shuffle(self.goals)
    if filter_goals is not None:
        self.goals = [goal for i, goal in enumerate(self.goals) if filter_goals(i, goal)]
    if limit_goals != -1 and limit_goals < len(self.goals):
        self.weights = [goal['weight'] for goal in self.goals]
        self.cum_weights = [0] + np.cumsum(self.weights).tolist()
        idxs = []
        while len(idxs) < limit_goals:
            idx = random_idx(self.cum_weights)
            if idx not in idxs:
                idxs.append(idx)
        self.goals = [self.goals[i] for i in idxs]
    print(f'Loaded {len(self.goals)} goals.')
    self.weights = [goal['weight'] for goal in self.goals]
    self.cum_weights = [0] + np.cumsum(self.weights).tolist()
    self.user_sessions = dict()
    self.search_time = 0
    self.render_time = 0
    self.sample_time = 0
    self.assigned_instruction_text = None

@app.route('/', methods=['GET', 'POST'])
def index(self, session_id, **kwargs):
    """Redirect to the search page with the given session ID"""
    html = map_action_to_html('start', session_id=session_id, instruction_text=kwargs['instruction_text'])
    url = f'{self.base_url}/{session_id}'
    return (html, url)

@app.route('/', methods=['GET', 'POST'])
def search_results(self, session_id, **kwargs):
    """Initialize session and return the search results page"""
    session = self.user_sessions[session_id]
    keywords = kwargs['keywords']
    assert isinstance(keywords, list)
    page = 1 if 'page' not in kwargs else kwargs['page']
    session['page'] = page
    session['keywords'] = keywords
    session['actions']['search'] += 1
    session['asin'] = None
    session['options'] = {}
    old_time = time.time()
    top_n_products = get_top_n_product_from_keywords(keywords, self.search_engine, self.all_products, self.product_item_dict)
    self.search_time += time.time() - old_time
    products = get_product_per_page(top_n_products, page)
    keywords_url_string = '+'.join(keywords)
    url = f'{self.base_url}/search_results/{session_id}/{keywords_url_string}/{page}'
    old_time = time.time()
    html = map_action_to_html('search', session_id=session_id, products=products, keywords=session['keywords'], page=page, total=len(top_n_products), instruction_text=session['goal']['instruction_text'])
    self.render_time += time.time() - old_time
    return (html, url)

@app.route('/', methods=['GET', 'POST'])
def item_page(self, session_id, **kwargs):
    """Render and return the HTML for a product item page"""
    session = self.user_sessions[session_id]
    clickable_name = kwargs['clickable_name']
    text_to_clickable = kwargs['text_to_clickable']
    clickable = text_to_clickable[clickable_name]
    if clickable.get('class') is not None and clickable.get('class')[0] == 'product-link':
        session['asin'] = clickable_name.upper()
        session['actions']['asin'] += 1
        session['asins'].add(session['asin'])
    elif clickable.get('name') is not None:
        clickable_key = clickable['name'].lower()
        session['options'][clickable_key] = clickable_name
        session['actions']['options'] += 1
    product_info = self.product_item_dict[session['asin']]
    keywords_url_string = '+'.join(session['keywords'])
    option_string = json.dumps(session['options'])
    url = f'{self.base_url}/item_page/{session_id}/{session['asin']}/{keywords_url_string}/{session['page']}/{option_string}'
    html = map_action_to_html('click', session_id=session_id, product_info=product_info, keywords=session['keywords'], page=session['page'], asin=session['asin'], options=session['options'], instruction_text=session['goal']['instruction_text'], show_attrs=self.show_attrs)
    return (html, url)

@app.route('/', methods=['GET', 'POST'])
def item_sub_page(self, session_id, **kwargs):
    """Render and return the HTML for a product's sub page (i.e. description, features)"""
    session = self.user_sessions[session_id]
    clickable_name = kwargs['clickable_name']
    for k in ACTION_TO_TEMPLATE:
        if clickable_name.lower() == k.lower():
            clickable_name = k
            break
    product_info = self.product_item_dict[session['asin']]
    session['actions'][clickable_name] += 1
    keywords_url_string = '+'.join(session['keywords'])
    url = f'{self.base_url}/item_sub_page/{session_id}/{session['asin']}/{keywords_url_string}/{session['page']}/{clickable_name}/{session['options']}'
    html = map_action_to_html(f'click[{clickable_name}]', session_id=session_id, product_info=product_info, keywords=session['keywords'], page=session['page'], asin=session['asin'], options=session['options'], instruction_text=session['goal']['instruction_text'])
    return (html, url)

@app.route('/', methods=['GET', 'POST'])
def done(self, session_id, **kwargs):
    """Render and return HTML for done page"""
    session = self.user_sessions[session_id]
    goal = self.user_sessions[session_id]['goal']
    purchased_product = self.product_item_dict[session['asin']]
    session['actions']['purchase'] += 1
    price = self.product_prices.get(session['asin'])
    reward, info = get_reward(purchased_product, goal, price=price, options=session['options'], verbose=True)
    self.user_sessions[session_id]['verbose_info'] = info
    self.user_sessions[session_id]['done'] = True
    self.user_sessions[session_id]['reward'] = reward
    url = f'{self.base_url}/done/{session_id}/{session['asin']}/{session['options']}'
    html = map_action_to_html(f'click[{END_BUTTON}]', session_id=session_id, reward=reward, asin=session['asin'], options=session['options'], instruction_text=session['goal']['instruction_text'])
    return (html, url, reward)

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
def state(self):
    """
        State that includes all information. The actual observation are
        likely to be a subset or reduced form of the state.
        """
    return dict(url=self.browser.current_url, html=self.browser.page_source, instruction_text=self.instruction_text)

def map_action_to_html(action, **kwargs):
    action_name, action_arg = parse_action(action)
    if action_name == 'start':
        path = os.path.join(TEMPLATE_DIR, 'search_page.html')
        html = render_template_string(read_html_template(path=path), session_id=kwargs['session_id'], instruction_text=kwargs['instruction_text'])
    elif action_name == 'search':
        path = os.path.join(TEMPLATE_DIR, 'results_page.html')
        html = render_template_string(read_html_template(path=path), session_id=kwargs['session_id'], products=kwargs['products'], keywords=kwargs['keywords'], page=kwargs['page'], total=kwargs['total'], instruction_text=kwargs['instruction_text'])
    elif action_name == 'click' and action_arg == END_BUTTON:
        path = os.path.join(TEMPLATE_DIR, 'done_page.html')
        html = render_template_string(read_html_template(path), session_id=kwargs['session_id'], reward=kwargs['reward'], asin=kwargs['asin'], options=kwargs['options'], reward_info=kwargs.get('reward_info'), goal_attrs=kwargs.get('goal_attrs'), purchased_attrs=kwargs.get('purchased_attrs'), goal=kwargs.get('goal'), mturk_code=kwargs.get('mturk_code'), query=kwargs.get('query'), category=kwargs.get('category'), product_category=kwargs.get('product_category'))
    elif action_name == 'click' and action_arg in ACTION_TO_TEMPLATE:
        path = os.path.join(TEMPLATE_DIR, ACTION_TO_TEMPLATE[action_arg])
        html = render_template_string(read_html_template(path), session_id=kwargs['session_id'], product_info=kwargs['product_info'], keywords=kwargs['keywords'], page=kwargs['page'], asin=kwargs['asin'], options=kwargs['options'], instruction_text=kwargs.get('instruction_text'))
    elif action_name == 'click':
        path = os.path.join(TEMPLATE_DIR, 'item_page.html')
        html = render_template_string(read_html_template(path), session_id=kwargs['session_id'], product_info=kwargs['product_info'], keywords=kwargs['keywords'], page=kwargs['page'], asin=kwargs['asin'], options=kwargs['options'], instruction_text=kwargs.get('instruction_text'), show_attrs=kwargs['show_attrs'])
    else:
        raise ValueError('Action name not recognized.')
    return html

def convert_web_app_string_to_var(name, string):
    if name == 'keywords':
        keywords = string
        if keywords.startswith('['):
            keywords = literal_eval(keywords)
        else:
            keywords = [keywords]
        var = keywords
    elif name == 'page':
        page = string
        page = int(page)
        var = page
    else:
        raise ValueError('Name of variable not recognized.')
    return var

def init_search_engine(num_products=None):
    if num_products == 100:
        indexes = 'indexes_100'
    elif num_products == 1000:
        indexes = 'indexes_1k'
    elif num_products == 100000:
        indexes = 'indexes_100k'
    elif num_products is None:
        indexes = 'indexes'
    else:
        raise NotImplementedError(f'num_products being {num_products} is not supported yet.')
    search_engine = LuceneSearcher(os.path.join(BASE_DIR, f'../search_engine/{indexes}'))
    return search_engine

def clean_product_keys(products):
    for product in products:
        product.pop('product_information', None)
        product.pop('brand', None)
        product.pop('brand_url', None)
        product.pop('list_price', None)
        product.pop('availability_quantity', None)
        product.pop('availability_status', None)
        product.pop('total_reviews', None)
        product.pop('total_answered_questions', None)
        product.pop('seller_id', None)
        product.pop('seller_name', None)
        product.pop('fulfilled_by_amazon', None)
        product.pop('fast_track_message', None)
        product.pop('aplus_present', None)
        product.pop('small_description_old', None)
    print('Keys cleaned.')
    return products

@app.route('/', methods=['GET', 'POST'])
def index(session_id, **kwargs):
    print('Hello world')

@app.route('/', methods=['GET', 'POST'])
def search_results(data):
    path = os.path.join(TEMPLATE_DIR, 'results_page.html')
    html = render_template_string(read_html_template(path=path), session_id=SESSION_ID, products=data, keywords=KEYWORDS, page=1, total=len(data), instruction_text=QUERY)
    return html

@app.route('/', methods=['GET', 'POST'])
def item_page(session_id, asin, keywords, page, options):
    path = os.path.join(TEMPLATE_DIR, 'item_page.html')
    html = render_template_string(read_html_template(path=path), session_id=session_id, product_info=product_map[asin], keywords=keywords, page=page, asin=asin, options=options, instruction_text=QUERY)
    return html

@app.route('/', methods=['GET', 'POST'])
def item_sub_page(session_id, asin, keywords, page, sub_page, options):
    path = os.path.join(TEMPLATE_DIR, sub_page.value.lower() + '_page.html')
    html = render_template_string(read_html_template(path), session_id=session_id, product_info=product_map[asin], keywords=keywords, page=page, asin=asin, options=options, instruction_text=QUERY)
    return html

@app.route('/', methods=['GET', 'POST'])
def done(asin, options, session_id, **kwargs):
    path = os.path.join(TEMPLATE_DIR, 'done_page.html')
    html = render_template_string(read_html_template(path), session_id=session_id, reward=1, asin=asin, options=product_map[asin]['options'], reward_info=kwargs.get('reward_info'), goal_attrs=kwargs.get('goal_attrs'), purchased_attrs=kwargs.get('purchased_attrs'), goal=kwargs.get('goal'), mturk_code=kwargs.get('mturk_code'), query=kwargs.get('query'), category=kwargs.get('category'), product_category=kwargs.get('product_category'))
    return html

def get_return_value(env, asin, options, search_terms, page_num, product):
    asin_url = None
    if env == 'webshop':
        query_str = '+'.join(search_terms.split())
        options_str = json.dumps(options)
        asin_url = f'{WEBSHOP_URL}/item_page/{WEBSHOP_SESSION}/{asin}/{query_str}/{page_num}/{options_str}'
    else:
        asin_url = f'https://www.ebay.com/itm/{asin}' if env == 'ebay' else f'https://www.amazon.com/dp/{asin}'
    product_reduced = {k: v for k, v in product.items() if k in ['asin', 'Title', 'Description', 'BulletPoints']}
    product_reduced['Description'] = product_reduced['Description'][:100] + '...'
    product_reduced['Features'] = product_reduced.pop('BulletPoints')
    product_reduced['Features'] = product_reduced['Features'][:100] + '...'
    html = '<!DOCTYPE html><html><head><title>Chosen Product</title></head><body>'
    html += f'Product Image:<img src="{product['MainImage']}" height="50px" /><br>' if len(product['MainImage']) > 0 else ''
    html += f'Link to Product:\n        <a href="{asin_url}" style="color:blue;text-decoration:underline;" target="_blank">{asin_url}</a>\n        </body></html>'
    return (product_reduced, options if len(options) > 0 else 'None Selected', html)

class Agent:

    def __init__(self, args):
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', truncation_side='left', max_length=512)
        self.tokenizer.add_tokens(['[button], [button_], [clicked button], [clicked button_]'], special_tokens=True)
        vocab_size = len(self.tokenizer)
        embedding_dim = args.embedding_dim
        if args.network == 'rnn':
            self.network = RCDQN(vocab_size, embedding_dim, args.hidden_dim, args.arch_encoder, args.grad_encoder, None, args.gru_embed, args.get_image, args.bert_path)
            self.network.rl_forward = self.network.forward
        elif args.network == 'bert':
            config = BertConfigForWebshop(image=args.get_image, pretrained_bert=args.bert_path != 'scratch')
            self.network = BertModelForWebshop(config)
            if args.bert_path != '' and args.bert_path != 'scratch':
                self.network.load_state_dict(torch.load(args.bert_path, map_location=torch.device('cpu')), strict=False)
        else:
            raise ValueError('Unknown network: {}'.format(args.network))
        self.network = self.network.to(device)
        self.save_path = args.output_dir
        self.clip = args.clip
        self.w = {'loss_pg': args.w_pg, 'loss_td': args.w_td, 'loss_il': args.w_il, 'loss_en': args.w_en}
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=args.learning_rate)
        self.gamma = args.gamma

    def build_state(self, ob, info):
        """ Returns a state representation built from various info sources. """
        obs_ids = self.encode(ob)
        goal_ids = self.encode(info['goal'])
        click = info['valid'][0].startswith('click[')
        estimate = info['estimate_score']
        obs_str = ob.replace('\n', '[SEP]')
        goal_str = info['goal']
        image_feat = info.get('image_feat')
        return State(obs_ids, goal_ids, click, estimate, obs_str, goal_str, image_feat)

    def encode(self, observation, max_length=512):
        """ Encode an observation """
        observation = observation.lower().replace('"', '').replace("'", '').strip()
        observation = observation.replace('[sep]', '[SEP]')
        token_ids = self.tokenizer.encode(observation, truncation=True, max_length=max_length)
        return token_ids

    def decode(self, act):
        act = self.tokenizer.decode(act, skip_special_tokens=True)
        act = act.replace(' [ ', '[').replace(' ]', ']')
        return act

    def encode_valids(self, valids, max_length=64):
        """ Encode a list of lists of strs """
        return [[self.encode(act, max_length=max_length) for act in valid] for valid in valids]

    def act(self, states, valid_acts, method, state_strs=None, eps=0.1):
        """ Returns a string action from poss_acts. """
        act_ids = self.encode_valids(valid_acts)
        act_values, act_sizes, values = self.network.rl_forward(states, act_ids, value=True, act=True)
        act_values = act_values.split(act_sizes)
        if method == 'softmax':
            act_probs = [F.softmax(vals, dim=0) for vals in act_values]
            act_idxs = [torch.multinomial(probs, num_samples=1).item() for probs in act_probs]
        elif method == 'greedy':
            act_idxs = [vals.argmax(dim=0).item() for vals in act_values]
        elif method == 'eps':
            act_idxs = [vals.argmax(dim=0).item() if random.random() > eps else random.randint(0, len(vals) - 1) for vals in act_values]
        acts = [acts[idx] for acts, idx in zip(act_ids, act_idxs)]
        act_strs, act_ids = ([], [])
        for act, idx, valids in zip(acts, act_idxs, valid_acts):
            if torch.is_tensor(act):
                act = act.tolist()
            if 102 in act:
                act = act[:act.index(102) + 1]
            act_ids.append(act)
            if idx is None:
                act_str = self.decode(act)
            else:
                act_str = valids[idx]
            act_strs.append(act_str)
        return (act_strs, act_ids, values)

    def update(self, transitions, last_values, step=None, rewards_invdy=None):
        returns, advs = discount_reward(transitions, last_values, self.gamma)
        stats_global = defaultdict(float)
        for transition, adv in zip(transitions, advs):
            stats = {}
            log_valid, valid_sizes = self.network.rl_forward(transition.state, transition.valid_acts)
            act_values = log_valid.split(valid_sizes)
            log_a = torch.stack([values[acts.index(act)] for values, acts, act in zip(act_values, transition.valid_acts, transition.act)])
            stats['loss_pg'] = -(log_a * adv.detach()).mean()
            stats['loss_td'] = adv.pow(2).mean()
            stats['loss_il'] = -log_valid.mean()
            stats['loss_en'] = (log_valid * log_valid.exp()).mean()
            for k in stats:
                stats[k] = self.w[k] * stats[k] / len(transitions)
            stats['loss'] = sum((stats[k] for k in stats))
            stats['returns'] = torch.stack(returns).mean() / len(transitions)
            stats['advs'] = torch.stack(advs).mean() / len(transitions)
            stats['loss'].backward()
            stats['gradnorm_unclipped'] = sum((p.grad.norm(2).item() for p in self.network.parameters() if p.grad is not None))
            nn.utils.clip_grad_norm_(self.network.parameters(), self.clip)
            stats['gradnorm_clipped'] = sum((p.grad.norm(2).item() for p in self.network.parameters() if p.grad is not None))
            for k, v in stats.items():
                stats_global[k] += v.item() if torch.is_tensor(v) else v
            del stats
        self.optimizer.step()
        self.optimizer.zero_grad()
        return stats_global

    def load(self):
        try:
            self.network = torch.load(os.path.join(self.save_path, 'model.pt'))
        except Exception as e:
            print('Error saving model.', e)

    def save(self):
        try:
            torch.save(self.network, os.path.join(self.save_path, 'model.pt'))
        except Exception as e:
            print('Error saving model.', e)

def load(self):
    try:
        self.network = torch.load(os.path.join(self.save_path, 'model.pt'))
    except Exception as e:
        print('Error saving model.', e)

def test_random_idx():
    random.seed(24)
    weights = [random.randint(0, 10) for _ in range(0, 50)]
    cml_weights = [0] + np.cumsum(weights).tolist()
    idx_1, expected_1 = (random_idx(cml_weights), 44)
    idx_2, expected_2 = (random_idx(cml_weights), 15)
    idx_3, expected_3 = (random_idx(cml_weights), 36)
    assert idx_1 == expected_1
    assert idx_2 == expected_2
    assert idx_3 == expected_3

def test_get_type_reward():
    goal = {'query': 'Query 1', 'product_category': 'a › b › c', 'name': 'Name 1'}
    purchased = {'query': 'Query 1', 'product_category': 'a › b › c', 'name': 'Name 1'}
    result = get_type_reward(purchased, goal)
    assert result['r_type'] == 1.0
    assert result['query_match'] == True
    assert result['category_match'] == True
    assert result['title_score'] == 1
    purchased['query'] = 'Query 2'
    result = get_type_reward(purchased, goal)
    assert result['query_match'] == False
    purchased['product_category'] = 'b › c › a'
    result = get_type_reward(purchased, goal)
    assert result['category_match'] == True
    purchased['product_category'] = 'd › e › f'
    result = get_type_reward(purchased, goal)
    assert result['category_match'] == False
    purchased['product_category'] = 'a › d › b'
    result = get_type_reward(purchased, goal)
    assert result['category_match'] == True
    purchased['product_category'] = 'a › a › b'
    result = get_type_reward(purchased, goal)
    assert result['category_match'] == True
    purchased['product_category'] = 'a › a › d'
    result = get_type_reward(purchased, goal)
    assert result['category_match'] == False
    goal['name'] = 'Mens D.O.N. Issue 2 Gca Basketball Sneakers Shoes Casual - Off White'
    purchased['name'] = 'PEAK High Top Mens Basketball Shoes Lou Williams Streetball Master Breathable Non Slip Outdoor Sneakers'
    result = get_type_reward(purchased, goal)
    assert isclose(result['title_score'], 0.333, abs_tol=0.01)
    goal['name'] = 'Saireed UL Listed 2 Prong Power Cord for JBL Bar 3.1 Bar 2.1 Channel 4K Ultra HD Soundbar Home Theater System Subwoofer'
    purchased['name'] = 'BRST AC Power Cord Outlet Socket Cable Plug Lead for Panasonic SC-HT830V DVD/VCR Combo Home Theater System'
    result = get_type_reward(purchased, goal)
    assert isclose(result['title_score'], 0.3, abs_tol=0.01)
    goal['name'] = 'Saireed UL Listed 2 Prong Power Cord for JBL Bar 3.1 Bar 2.1 Channel 4K Ultra HD Soundbar'
    purchased['name'] = 'BRST AC Power Cord Outlet Socket Cable Plug Lead for Panasonic SC-HT830V DVD/VCR Combo Home Theater System'
    result = get_type_reward(purchased, goal)
    assert isclose(result['title_score'], 0.15, abs_tol=0.01)
    goal['name'] = 'Rusticware 921ORB Kitchen and Bath Cabinet Knob'
    purchased['name'] = 'Minkissy 2pcs Stainless Steel Eyebrow Tweezers Blackhead Acne Remover Portable Makeup Tweezers (Silver)'
    result = get_type_reward(purchased, goal)
    assert result['title_score'] < 0.05

def test_get_reward():
    goal = {'query': 'Query 1', 'product_category': 'a › b › c', 'name': 'Mens D.O.N. Issue 2 Gca Basketball Sneakers Shoes Casual - Off White', 'attributes': ['tea tree', 'essential oils', 'natural ingredients'], 'goal_options': {'color': 'grey', 'size': 'XL'}, 'price_upper': 40.0}
    purchased = {'query': 'Query 1', 'product_category': 'a › b › c', 'name': 'Mens D.O.N. Issue 2 Gca Basketball Sneakers Shoes Casual - Off White', 'Attributes': ['tea tree', 'essential oil', 'natural ingredients'], 'Title': '', 'BulletPoints': [], 'Description': '', 'goal_options': {'color': 'grey', 'size': 'XL'}}
    total_reward = get_reward(purchased, goal, 35, purchased['goal_options'])
    assert total_reward == 1
    purchased['Attributes'] = []
    purchased['Title'] = ''
    purchased['BulletPoints'] = 'This shampoo has essential oils and smells like lemons'
    purchased['Description'] = 'Best shampoo on the market, made with natural ingredients'
    total_reward = get_reward(purchased, goal, 35, purchased['goal_options'])
    assert isclose(total_reward, 2.0 / 3.0, abs_tol=0.01)
    goal['goal_options'] = {'color': 'grey', 'size': 'XL', 'amount': 'pack of 12'}
    total_reward = get_reward(purchased, goal, 35, purchased['goal_options'])
    assert isclose(total_reward, 0.5714, abs_tol=0.01)
    goal['name'] = 'Saireed UL Listed 2 Prong Power Cord for JBL Bar 3.1 Bar 2.1 Channel 4K Ultra HD Soundbar'
    purchased['name'] = 'BRST AC Power Cord Outlet Socket Cable Plug Lead for Panasonic SC-HT830V DVD/VCR Combo Home Theater System'
    purchased['query'] = 'Query 2'
    purchased['product_category'] = 'a › d › e'
    total_reward = get_reward(purchased, goal, 35, purchased['goal_options'])
    assert isclose(total_reward, 0.2857, abs_tol=0.01)

