# Cluster 3

def annotate(attr_path):
    with open(attr_path) as f:
        attrs_by_cat = yaml.safe_load(f)
    unique_attrs = set()
    all_attrs = []
    for _, attrs in attrs_by_cat.items():
        attrs = [a.split('|')[0].strip() for a in attrs]
        unique_attrs.update(attrs)
        all_attrs += attrs
    print(f'Total unique attributes: {len(unique_attrs)}')
    total = len(all_attrs)
    num_left = len(all_attrs)
    annotated_attrs_by_cat = dict()
    for category, attrs in attrs_by_cat.items():
        print(f'Category: [ {category} ] | Number of attributes: {len(attrs)}\n')
        annotated_attrs = []
        for i, attr in enumerate(attrs):
            attr, score = attr.split(' | ')
            print(f'{'[' + str(i) + ']':<5} [bold green]{attr:<30}[/bold green] | [red]{category}[/red] | {score}')
            tags = input('Annotate [1: ITEM, 2: PROP, 3: USE, ⎵: next example, q: next category] > ')
            print('\n')
            tags = tags.strip()
            annotated_attrs.append(f'{attr} | {score} | {tags}')
            if 'q' in tags:
                break
        num_left -= len(attrs)
        print(f'{num_left} / {total} total attributes left.')
        ans = input('Starting the next category... [y/n] > ')
        if ans == 'n':
            break

def get_stop_words():
    extra_stop_words = set([str(i) for i in range(1000)])
    stop_words = sk_text.ENGLISH_STOP_WORDS.union(extra_stop_words)
    return stop_words

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

def get_type_reward(purchased_product, goal):
    """Determines the type reward - captures whether chosen product is in the same category"""
    query_match = purchased_product['query'] == goal['query']
    purchased_product_category = [x.strip() for x in purchased_product['product_category'].split('›')]
    goal_product_category = [x.strip() for x in goal['product_category'].split('›')]
    category_match = len(set(purchased_product_category) & set(goal_product_category)) >= 2
    purchased_type = purchased_product['name']
    desired_type = goal['name']
    purchased_type_parse = nlp(purchased_type)
    desired_type_parse = nlp(desired_type)
    purchased_type_parse = [t.text.lower() for t in purchased_type_parse if t.pos_ in ('PNOUN', 'NOUN', 'PROPN')]
    desired_type_parse = [t.text.lower() for t in desired_type_parse if t.pos_ in ('PNOUN', 'NOUN', 'PROPN')]
    n_intersect_type = len(set(purchased_type_parse) & set(desired_type_parse))
    if len(desired_type_parse) == 0:
        title_score = 0.2
    else:
        title_score = n_intersect_type / len(desired_type_parse)
    r_type = 1.0
    match = query_match or category_match or title_score > 0.2
    if not match:
        r_type = 0.5
    if title_score < 0.1:
        r_type = 0.1
    if title_score == 0.0:
        r_type = 0.0
    return dict(r_type=r_type, query_match=query_match, category_match=category_match, title_score=title_score)

def load_products(filepath, num_products=None, human_goals=True):
    with open(filepath) as f:
        products = json.load(f)
    print('Products loaded.')
    products = clean_product_keys(products)
    all_reviews = dict()
    all_ratings = dict()
    if human_goals:
        with open(HUMAN_ATTR_PATH) as f:
            human_attributes = json.load(f)
    with open(DEFAULT_ATTR_PATH) as f:
        attributes = json.load(f)
    with open(HUMAN_ATTR_PATH) as f:
        human_attributes = json.load(f)
    print('Attributes loaded.')
    asins = set()
    all_products = []
    attribute_to_asins = defaultdict(set)
    if num_products is not None:
        products = products[:num_products]
    for i, p in tqdm(enumerate(products), total=len(products)):
        asin = p['asin']
        if asin == 'nan' or len(asin) > 10:
            continue
        if asin in asins:
            continue
        else:
            asins.add(asin)
        products[i]['category'] = p['category']
        products[i]['query'] = p['query']
        products[i]['product_category'] = p['product_category']
        products[i]['Title'] = p['name']
        products[i]['Description'] = p['full_description']
        products[i]['Reviews'] = all_reviews.get(asin, [])
        products[i]['Rating'] = all_ratings.get(asin, 'N.A.')
        for r in products[i]['Reviews']:
            if 'score' not in r:
                r['score'] = r.pop('stars')
            if 'review' not in r:
                r['body'] = ''
            else:
                r['body'] = r.pop('review')
        products[i]['BulletPoints'] = p['small_description'] if isinstance(p['small_description'], list) else [p['small_description']]
        pricing = p.get('pricing')
        if pricing is None or not pricing:
            pricing = [100.0]
            price_tag = '$100.0'
        else:
            pricing = [float(Decimal(re.sub('[^\\d.]', '', price))) for price in pricing.split('$')[1:]]
            if len(pricing) == 1:
                price_tag = f'${pricing[0]}'
            else:
                price_tag = f'${pricing[0]} to ${pricing[1]}'
                pricing = pricing[:2]
        products[i]['pricing'] = pricing
        products[i]['Price'] = price_tag
        options = dict()
        customization_options = p['customization_options']
        option_to_image = dict()
        if customization_options:
            for option_name, option_contents in customization_options.items():
                if option_contents is None:
                    continue
                option_name = option_name.lower()
                option_values = []
                for option_content in option_contents:
                    option_value = option_content['value'].strip().replace('/', ' | ').lower()
                    option_image = option_content.get('image', None)
                    option_values.append(option_value)
                    option_to_image[option_value] = option_image
                options[option_name] = option_values
        products[i]['options'] = options
        products[i]['option_to_image'] = option_to_image
        if asin in attributes and 'attributes' in attributes[asin]:
            products[i]['Attributes'] = attributes[asin]['attributes']
        else:
            products[i]['Attributes'] = ['DUMMY_ATTR']
        if human_goals:
            if asin in human_attributes:
                products[i]['instructions'] = human_attributes[asin]
        else:
            products[i]['instruction_text'] = attributes[asin].get('instruction', None)
            products[i]['instruction_attributes'] = attributes[asin].get('instruction_attributes', None)
        products[i]['MainImage'] = p['images'][0]
        products[i]['query'] = p['query'].lower().strip()
        all_products.append(products[i])
    for p in all_products:
        for a in p['Attributes']:
            attribute_to_asins[a].add(p['asin'])
    product_item_dict = {p['asin']: p for p in all_products}
    product_prices = generate_product_prices(all_products)
    return (all_products, product_item_dict, product_prices, attribute_to_asins)

def normalize_color_size(product_prices: dict) -> Tuple[dict, dict]:
    """Get mappings of all colors, sizes to corresponding values in COLOR_SET, SIZE_PATTERNS"""
    all_colors, all_sizes = (set(), set())
    for (_, color, size), _ in product_prices.items():
        all_colors.add(color.lower())
        all_sizes.add(size.lower())
    color_mapping = {'N.A.': 'not_matched'}
    for c in all_colors:
        matched = False
        for base in COLOR_SET:
            if base in c:
                color_mapping[c] = base
                matched = True
                break
        if not matched:
            color_mapping[c] = 'not_matched'
    size_mapping = {'N.A.': 'not_matched'}
    for s in all_sizes:
        matched = False
        for pattern in SIZE_PATTERNS:
            m = re.search(pattern, s)
            if m is not None:
                matched = True
                size_mapping[s] = pattern.pattern
                break
        if not matched:
            if s.replace('.', '', 1).isdigit():
                size_mapping[s] = 'numeric_size'
                matched = True
        if not matched:
            size_mapping[s] = 'not_matched'
    return (color_mapping, size_mapping)

class HumanPolicy(BasePolicy):

    def __init__(self):
        super().__init__()

    def forward(self, observation, available_actions):
        action = input('> ')
        return action

def forward(self, observation, available_actions):
    action = input('> ')
    return action

def process_str(s):
    s = s.lower().replace('"', '').replace("'", '').strip()
    s = s.replace('[sep]', '[SEP]')
    return s

def process_goal(state):
    state = state.lower().replace('"', '').replace("'", '')
    state = state.replace('amazon shopping game\ninstruction:', '').replace('webshop\ninstruction:', '')
    state = state.replace('\n[button] search [button_]', '').strip()
    if ', and price lower than' in state:
        state = state.split(', and price lower than')[0]
    return state

def parse_results_ebay(query, page_num=None, verbose=True):
    query_string = '+'.join(query.split())
    page_num = 1 if page_num is None else page_num
    url = f'https://www.ebay.com/sch/i.html?_nkw={query_string}&_pgn={page_num}'
    if verbose:
        print(f'Search Results URL: {url}')
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    soup = BeautifulSoup(webpage.text, 'html.parser')
    products = soup.select('.s-item__wrapper.clearfix')
    results = []
    for item in products[:NUM_PROD_LIMIT]:
        title = item.select_one('.s-item__title').text.strip()
        if 'shop on ebay' in title.lower():
            continue
        link = item.select_one('.s-item__link')['href']
        asin = link.split('?')[0][len('https://www.ebay.com/itm/'):]
        try:
            price = item.select_one('.s-item__price').text
            if 'to' in price:
                prices = price.split(' to ')
                price = [p.strip('$') for p in prices]
        except:
            price = None
        results.append({'asin': asin, 'Title': title, 'Price': price})
    if verbose:
        print(f'Scraped {len(results)} products')
    return results

def parse_item_page_ebay(asin, verbose=True):
    product_dict = {}
    product_dict['asin'] = asin
    url = f'https://www.ebay.com/itm/{asin}'
    if verbose:
        print(f'Item Page URL: {url}')
    begin = time.time()
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    end = time.time()
    if verbose:
        print(f'Item page scraping took {end - begin} seconds')
    soup = BeautifulSoup(webpage.content, 'html.parser')
    try:
        product_dict['Title'] = soup.find('h1', {'class': 'x-item-title__mainTitle'}).text.strip()
    except:
        product_dict['Title'] = 'N/A'
    try:
        price_str = soup.find('div', {'class': 'mainPrice'}).text
        prices = re.findall('\\d*\\.?\\d+', price_str)
        product_dict['Price'] = prices[0]
    except:
        product_dict['Price'] = 'N/A'
    try:
        img_div = soup.find('div', {'id': 'mainImgHldr'})
        img_link = img_div.find('img', {'id': 'icImg'})['src']
        product_dict['MainImage'] = img_link
    except:
        product_dict['MainImage'] = ''
    try:
        rating = soup.find('span', {'class': 'reviews-star-rating'})['title'].split()[0]
    except:
        rating = None
    product_dict['Rating'] = rating
    options, options_to_images = ({}, {})
    try:
        option_blocks = soup.findAll('select', {'class': 'msku-sel'})
        for block in option_blocks:
            name = block['name'].strip().strip(':')
            option_tags = block.findAll('option')
            opt_list = []
            for option_tag in option_tags:
                if 'select' not in option_tag.text.lower():
                    opt_list.append(option_tag.text)
            options[name] = opt_list
    except:
        options = {}
    product_dict['options'], product_dict['option_to_image'] = (options, options_to_images)
    desc = None
    try:
        desc_link = soup.find('iframe', {'id': 'desc_ifr'})['src']
        desc_webpage = requests.get(desc_link, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
        desc_soup = BeautifulSoup(desc_webpage.content, 'html.parser')
        desc = ' '.join(desc_soup.text.split())
    except:
        desc = 'N/A'
    product_dict['Description'] = desc
    features = None
    try:
        features = soup.find('div', {'class': 'x-about-this-item'}).text
    except:
        features = 'N/A'
    product_dict['BulletPoints'] = features
    return product_dict

def parse_results_ws(query, page_num=None, verbose=True):
    query_string = '+'.join(query.split())
    page_num = 1 if page_num is None else page_num
    url = f'{WEBSHOP_URL}/search_results/{WEBSHOP_SESSION}/{query_string}/{page_num}'
    if verbose:
        print(f'Search Results URL: {url}')
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    soup = BeautifulSoup(webpage.content, 'html.parser')
    products = soup.findAll('div', {'class': 'list-group-item'})
    results = []
    for product in products:
        asin = product.find('a', {'class': 'product-link'})
        title = product.find('h4', {'class': 'product-title'})
        price = product.find('h5', {'class': 'product-price'})
        if '\n' in title:
            title = title.text.split('\n')[0].strip()
        else:
            title = title.text.strip().strip('\n')
        if 'to' in price.text:
            prices = price.text.split(' to ')
            price = [float(p.strip().strip('\n$')) for p in prices]
        else:
            price = float(price.text.strip().strip('\n$'))
        results.append({'asin': asin.text, 'Title': title, 'Price': price})
    if verbose:
        print(f'Scraped {len(results)} products')
    return results

def parse_item_page_ws(asin, query, page_num, options, verbose=True):
    product_dict = {}
    product_dict['asin'] = asin
    query_string = '+'.join(query.split())
    options_string = json.dumps(options)
    url = f'{WEBSHOP_URL}/item_page/{WEBSHOP_SESSION}/{asin}/{query_string}/{page_num}/{options_string}'
    if verbose:
        print(f'Item Page URL: {url}')
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    soup = BeautifulSoup(webpage.content, 'html.parser')
    product_dict['Title'] = soup.find('h2').text
    h4_headers = soup.findAll('h4')
    for header in h4_headers:
        text = header.text
        if 'Price' in text:
            product_dict['Price'] = text.split(':')[1].strip().strip('$')
        elif 'Rating' in text:
            product_dict['Rating'] = text.split(':')[1].strip()
    product_dict['MainImage'] = soup.find('img')['src']
    options, options_to_image = ({}, {})
    option_blocks = soup.findAll('div', {'class': 'radio-toolbar'})
    for block in option_blocks:
        name = block.find('input')['name']
        labels = block.findAll('label')
        inputs = block.findAll('input')
        opt_list = []
        for label, input in zip(labels, inputs):
            opt = label.text
            opt_img_path = input['onclick'].split('href=')[1].strip("';")
            opt_img_url = f'{WEBSHOP_URL}{opt_img_path}'
            opt_list.append(opt)
            options_to_image[opt] = opt_img_url
        options[name] = opt_list
    product_dict['options'] = options
    product_dict['option_to_image'] = options_to_image
    url = f'{WEBSHOP_URL}/item_sub_page/{WEBSHOP_SESSION}/{asin}/{query_string}/{page_num}/Description/{options_string}'
    if verbose:
        print(f'Item Description URL: {url}')
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    soup = BeautifulSoup(webpage.content, 'html.parser')
    product_dict['Description'] = soup.find(name='p', attrs={'class': 'product-info'}).text.strip()
    url = f'{WEBSHOP_URL}/item_sub_page/{WEBSHOP_SESSION}/{asin}/{query_string}/{page_num}/Features/{options_string}'
    if verbose:
        print(f'Item Features URL: {url}')
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    soup = BeautifulSoup(webpage.content, 'html.parser')
    bullets = soup.find(name='ul').findAll(name='li')
    product_dict['BulletPoints'] = '\n'.join([b.text.strip() for b in bullets])
    return product_dict

def parse_results_amz(query, page_num=None, verbose=True):
    url = 'https://www.amazon.com/s?k=' + query.replace(' ', '+')
    if page_num is not None:
        url += '&page=' + str(page_num)
    if verbose:
        print(f'Search Results URL: {url}')
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    soup = BeautifulSoup(webpage.content, 'html.parser')
    products = soup.findAll('div', {'data-component-type': 's-search-result'})
    if products is None:
        temp = open(DEBUG_HTML, 'w')
        temp.write(str(soup))
        temp.close()
        raise Exception("Couldn't find search results page, outputted html for inspection")
    results = []
    for product in products[:NUM_PROD_LIMIT]:
        asin = product['data-asin']
        title = product.find('h2', {'class': 'a-size-mini'})
        price_div = product.find('div', {'class': 's-price-instructions-style'})
        price = price_div.find('span', {'class': 'a-offscreen'})
        result = {'asin': asin, 'Title': title.text.strip(), 'Price': price.text.strip().strip('$')}
        results.append(result)
    if verbose:
        print('Scraped', len(results), 'products')
    return results

def parse_item_page_amz(asin, verbose=True):
    product_dict = {}
    product_dict['asin'] = asin
    url = f'https://www.amazon.com/dp/{asin}'
    if verbose:
        print('Item Page URL:', url)
    begin = time.time()
    webpage = requests.get(url, headers={'User-Agent': HEADER_, 'Accept-Language': 'en-US, en;q=0.5'})
    end = time.time()
    if verbose:
        print(f'Item page scraping took {end - begin} seconds')
    soup = BeautifulSoup(webpage.content, 'html.parser')
    try:
        title = soup.find('span', attrs={'id': 'productTitle'})
        title = title.string.strip().replace(',', '')
    except AttributeError:
        title = 'N/A'
    product_dict['Title'] = title
    try:
        parent_price_span = soup.find(name='span', class_='apexPriceToPay')
        price_span = parent_price_span.find(name='span', class_='a-offscreen')
        price = float(price_span.getText().replace('$', ''))
    except AttributeError:
        price = 'N/A'
    product_dict['Price'] = price
    try:
        rating = soup.find(name='span', attrs={'id': 'acrPopover'})
        if rating is None:
            rating = 'N/A'
        else:
            rating = rating.text
    except AttributeError:
        rating = 'N/A'
    product_dict['Rating'] = rating.strip('\n').strip()
    try:
        features = soup.find(name='div', attrs={'id': 'feature-bullets'}).text
    except AttributeError:
        features = 'N/A'
    product_dict['BulletPoints'] = features
    try:
        desc_body = soup.find(name='div', attrs={'id': 'productDescription_feature_div'})
        desc_div = desc_body.find(name='div', attrs={'id': 'productDescription'})
        desc_ps = desc_div.findAll(name='p')
        desc = ' '.join([p.text for p in desc_ps])
    except AttributeError:
        desc = 'N/A'
    product_dict['Description'] = desc.strip()
    try:
        imgtag = soup.find('img', {'id': 'landingImage'})
        imageurl = dict(imgtag.attrs)['src']
    except AttributeError:
        imageurl = ''
    product_dict['MainImage'] = imageurl
    options, options_to_image = ({}, {})
    try:
        option_body = soup.find(name='div', attrs={'id': 'softlinesTwister_feature_div'})
        if option_body is None:
            option_body = soup.find(name='div', attrs={'id': 'twister_feature_div'})
        option_blocks = option_body.findAll(name='ul')
        for block in option_blocks:
            name = json.loads(block['data-a-button-group'])['name']
            opt_list = []
            for li in block.findAll('li'):
                img = li.find(name='img')
                if img is not None:
                    opt = img['alt'].strip()
                    opt_img = img['src']
                    if len(opt) > 0:
                        options_to_image[opt] = opt_img
                else:
                    opt = li.text.strip()
                if len(opt) > 0:
                    opt_list.append(opt)
            options[name.replace('_name', '').replace('twister_', '')] = opt_list
    except AttributeError:
        options = {}
    product_dict['options'], product_dict['option_to_image'] = (options, options_to_image)
    return product_dict

def convert_html_to_text(html, simple=False, clicked_options=None, visited_asins=None):

    def tag_visible(element):
        ignore = {'style', 'script', 'head', 'title', 'meta', '[document]'}
        return element.parent.name not in ignore and (not isinstance(element, Comment))
    html_obj = BeautifulSoup(html, 'html.parser')
    texts = html_obj.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    if simple:
        return ' [SEP] '.join((t.strip() for t in visible_texts if t != '\n'))
    else:
        observation = ''
        for t in visible_texts:
            if t == '\n':
                continue
            if t.parent.name == 'button':
                processed_t = f'[button] {t} [button]'
            elif t.parent.name == 'label':
                if f'{t}' in clicked_options:
                    processed_t = f'  [clicked button] {t} [clicked button]'
                    observation = f'You have clicked {t}.\n' + observation
                else:
                    processed_t = f'  [button] {t} [button]'
            elif t.parent.get('class') == ['product-link']:
                if f'{t}' in visited_asins:
                    processed_t = f'\n[clicked button] {t} [clicked button]'
                else:
                    processed_t = f'\n[button] {t} [button]'
            else:
                processed_t = str(t)
            observation += processed_t + '\n'
        return observation

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

def process(s):
    s = s.lower().replace('"', '').replace("'", '').strip()
    s = s.replace('[sep]', '[SEP]')
    return s

def process_goal(state):
    state = state.lower().replace('"', '').replace("'", '')
    state = state.replace('amazon shopping game\ninstruction:', '').replace('webshop\ninstruction:', '')
    state = state.replace('\n[button] search [button_]', '').strip()
    if ', and price lower than' in state:
        state = state.split(', and price lower than')[0]
    return state

def process_str(s):
    s = s.lower().replace('"', '').replace("'", '').strip()
    return s

def process_goal(state):
    state = state.lower().replace('"', '').replace("'", '')
    state = state.replace('amazon shopping game\ninstruction:', '').replace('webshop\ninstruction:', '')
    state = state.replace('\n[button] search [button_]', '').strip()
    if ', and price lower than' in state:
        state = state.split(', and price lower than')[0]
    return state

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

def encode(self, observation, max_length=512):
    """ Encode an observation """
    observation = observation.lower().replace('"', '').replace("'", '').strip()
    observation = observation.replace('[sep]', '[SEP]')
    token_ids = self.tokenizer.encode(observation, truncation=True, max_length=max_length)
    return token_ids

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

def summary_val(k, v):
    kwargs = {'tag': k, 'simple_value': float(v)}
    return self.tf.Summary.Value(**kwargs)

