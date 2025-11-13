# Cluster 8

def random_idx(cum_weights):
    """Generate random index by sampling uniformly from sum of all weights, then
    selecting the `min` between the position to keep the list sorted (via bisect)
    and the value of the second to last index
    """
    pos = random.uniform(0, cum_weights[-1])
    idx = bisect.bisect(cum_weights, pos)
    idx = min(idx, len(cum_weights) - 2)
    return idx

def load_products(num=None):
    """
    Loads products from the `items.json` file and combine them with reviews
    through `asin`.
    Return: dict[asin, product]
    """
    with open(ITEMS_PATH) as f:
        all_products = json.load(f)
        if num is not None:
            random.shuffle(all_products)
            all_products = all_products[:num]
        products = dict()
        asins = set()
        for p in all_products:
            asin = p['asin']
            if asin in asins:
                continue
            asins.add(asin)
            products[asin] = p
    with open(REVIEWS_PATH) as f:
        reviews = json.load(f)
        reviews = {r['asin']: r for r in reviews}
    for asin, p in products.items():
        if asin in reviews:
            p['review'] = reviews[asin]
        else:
            p['review'] = None
    return products

def get_top_attrs(attributes, k):
    attr_to_asins = defaultdict(list)
    for asin, attr_scores in attributes.items():
        top_attr_scoress = attr_scores[:k]
        for attr, score in top_attr_scoress:
            attr_to_asins[attr].append(asin)
    total = len([asin for asin, _ in attributes.items()])
    top_attrs = [(attr, len(asins) / total) for attr, asins in attr_to_asins.items()]
    top_attrs = sorted(top_attrs, key=lambda x: -x[1])
    top_attrs = [f'{attr} | {score:.4f}' for attr, score in top_attrs]
    return top_attrs

def get_corpus(products, keys=('name', 'small_description'), category_type='category'):
    """
    keys: `name`, `small_description`, `review`
    category_type: `category`, `query`
    """
    all_products = list(products.values())
    asins_by_cat = defaultdict(set)
    corpus_by_cat = defaultdict(list)
    for p in all_products:
        category = p[category_type]
        asin = p['asin']
        if asin in asins_by_cat[category]:
            continue
        asins_by_cat[category].add(asin)
        text = []
        for key in keys:
            if key == 'review':
                rs = p['review']['reviews']
                if r is not None:
                    text_ = ' '.join([r['review'].lower() for r in rs])
                else:
                    text_ = ''
            else:
                text_ = p[key].lower()
            text.append(text_)
        text = ' '.join(text)
        corpus_by_cat[category].append((asin, text))
    return corpus_by_cat

def generate_ngram_attrs(corpus_by_cat, ngram_range, k, attrs):
    vectorizer = TfidfVectorizer(stop_words=get_stop_words(), ngram_range=ngram_range, max_features=1000)
    top_attrs_by_cat = dict()
    for category, corpus in tqdm(corpus_by_cat.items(), total=len(corpus_by_cat)):
        asins = [_[0] for _ in corpus]
        texts = [_[1] for _ in corpus]
        vec = vectorizer.fit_transform(texts).todense()
        df = pd.DataFrame(vec, columns=vectorizer.get_feature_names_out())
        attrs_by_cat = dict()
        for asin, (row_name, row) in zip(asins, df.iterrows()):
            attr_scores = sorted(list(zip(row.index, row)), key=lambda x: -x[1])
            attrs_by_cat[asin] = attr_scores
            attrs[asin] = attr_scores
        top_attrs_by_cat[category.lower()] = get_top_attrs(attrs_by_cat, k=k)
    print(top_attrs_by_cat.keys())
    return top_attrs_by_cat

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

def get_human_goals(all_products, product_prices):
    goals = []
    cnt_atts = defaultdict(int)
    cnt = 0
    for item in all_products:
        asin = item['asin']
        if 'instructions' not in item:
            continue
        for product in item['instructions']:
            attributes = product['instruction_attributes']
            if len(attributes) == 0:
                cnt += 1
                continue
            if product_prices is not None:
                price = product_prices[asin]
                price_range = [p for p in PRICE_RANGE if p > price][:4]
                if len(price_range) >= 2:
                    _, price_upper = sorted(random.sample(price_range, 2))
                    price_text = f', and price lower than {price_upper:.2f} dollars'
                else:
                    price_upper = 1000000
                    price_text = ''
            else:
                price_upper = 1000000
            goals.append({'asin': asin, 'category': item['category'], 'query': item['query'], 'name': item['name'], 'product_category': item['product_category'], 'instruction_text': product['instruction'].strip('.') + price_text, 'attributes': attributes, 'price_upper': price_upper, 'goal_options': product['instruction_options']})
            for att in attributes:
                cnt_atts[att] += 1
    for goal in goals:
        goal['weight'] = 1
    print(cnt, 'skipped')
    return goals

def get_synthetic_goals(all_products, product_prices):
    goals = []
    cnt_atts = defaultdict(int)
    for product in all_products:
        if 'instruction_text' not in product or product['instruction_text'] is None:
            continue
        product_goals = []
        asin = product['asin']
        attributes = product['instruction_attributes']
        assert len(attributes) > 0
        if product_prices is not None:
            price = product_prices[asin]
            price_range = [p for p in PRICE_RANGE if p > price][:4]
            if len(price_range) >= 2:
                _, price_upper = sorted(random.sample(price_range, 2))
                price_text = f', and price lower than {price_upper:.2f} dollars'
            else:
                price_upper = 1000000
                price_text = ''
        else:
            price_upper = 1000000
            price_text = ''
        instruction_text = product['instruction_text']
        options = product['options']
        option_names = sorted(options)
        combinations = list(itertools.product(*(options[option_name] for option_name in option_names)))
        for combination in combinations:
            goal_options = dict()
            for i, o in enumerate(combination):
                goal_options[option_names[i]] = o
            option_text = ', and '.join([f'{k}: {v}' for k, v in goal_options.items()])
            option_text = ' with ' + option_text if option_text else ''
            product_goals.append({'asin': asin, 'category': product['category'], 'query': product['query'], 'name': product['name'], 'product_category': product['product_category'], 'instruction_text': f'{instruction_text}{option_text}{price_text}', 'attributes': attributes, 'price_upper': price_upper, 'goal_options': goal_options, 'name': product['Title']})
            for att in attributes:
                cnt_atts[att] += 1
        goals += product_goals
    for goal in goals:
        goal['weight'] = sum((1.0 / cnt_atts[att] for att in goal['attributes'])) / len(goal['attributes'])
    return goals

def get_reward(purchased_product, goal, price, options, **kwargs):
    """Get cumulative reward score for purchased product and goal"""
    r_type_dict = get_type_reward(purchased_product, goal)
    r_price = price <= goal['price_upper'] if goal['price_upper'] > 0 else None
    r_att, num_attr_matches = get_attribute_reward(purchased_product, goal)
    r_option, num_option_matches = get_option_reward(list(options.values()), goal['goal_options'].items() if isinstance(goal['goal_options'], dict) else goal['goal_options'])
    total_reward = (num_attr_matches + num_option_matches + r_price) / (len(goal['attributes']) + len(goal['goal_options']) + 1)
    total_reward *= r_type_dict['r_type']
    if kwargs.get('verbose', False):
        info = {'r_type': r_type_dict['r_type'], 'r_att': r_att, 'w_att': len(goal['attributes']) / (len(goal['attributes']) + len(goal['goal_options']) + 1), 'query_match': r_type_dict['query_match'], 'category_match': r_type_dict['category_match'], 'title_score': r_type_dict['title_score']}
        if r_option is not None:
            info['r_option'] = r_option
            info['w_option'] = len(goal['goal_options']) / (len(goal['attributes']) + len(goal['goal_options']) + 1)
        if r_price is not None:
            info['r_price'] = r_price
            info['w_price'] = 1 / (len(goal['attributes']) + len(goal['goal_options']) + 1)
        return (total_reward, info)
    return total_reward

def get_top_n_product_from_keywords(keywords, search_engine, all_products, product_item_dict, attribute_to_asins=None):
    if keywords[0] == '<r>':
        top_n_products = random.sample(all_products, k=SEARCH_RETURN_N)
    elif keywords[0] == '<a>':
        attribute = ' '.join(keywords[1:]).strip()
        asins = attribute_to_asins[attribute]
        top_n_products = [p for p in all_products if p['asin'] in asins]
    elif keywords[0] == '<c>':
        category = keywords[1].strip()
        top_n_products = [p for p in all_products if p['category'] == category]
    elif keywords[0] == '<q>':
        query = ' '.join(keywords[1:]).strip()
        top_n_products = [p for p in all_products if p['query'] == query]
    else:
        keywords = ' '.join(keywords)
        hits = search_engine.search(keywords, k=SEARCH_RETURN_N)
        docs = [search_engine.doc(hit.docid) for hit in hits]
        top_n_asins = [json.loads(doc.raw())['id'] for doc in docs]
        top_n_products = [product_item_dict[asin] for asin in top_n_asins if asin in product_item_dict]
    return top_n_products

def generate_product_prices(all_products):
    product_prices = dict()
    for product in all_products:
        asin = product['asin']
        pricing = product['pricing']
        if not pricing:
            price = 100.0
        elif len(pricing) == 1:
            price = pricing[0]
        else:
            price = random.uniform(*pricing[:2])
        product_prices[asin] = price
    return product_prices

def data_collator(batch):
    state_input_ids, state_attention_mask, action_input_ids, action_attention_mask, sizes, labels, images = ([], [], [], [], [], [], [])
    for sample in batch:
        state_input_ids.append(sample['state_input_ids'])
        state_attention_mask.append(sample['state_attention_mask'])
        action_input_ids.extend(sample['action_input_ids'])
        action_attention_mask.extend(sample['action_attention_mask'])
        sizes.append(sample['sizes'])
        labels.append(sample['labels'])
        images.append(sample['images'])
    max_state_len = max((sum(x) for x in state_attention_mask))
    max_action_len = max((sum(x) for x in action_attention_mask))
    return {'state_input_ids': torch.tensor(state_input_ids)[:, :max_state_len], 'state_attention_mask': torch.tensor(state_attention_mask)[:, :max_state_len], 'action_input_ids': torch.tensor(action_input_ids)[:, :max_action_len], 'action_attention_mask': torch.tensor(action_attention_mask)[:, :max_action_len], 'sizes': torch.tensor(sizes), 'images': torch.tensor(images), 'labels': torch.tensor(labels)}

def convert_dict_to_actions(page_type, products=None, asin=None, page_num=None) -> dict:
    info = {'valid': []}
    if page_type == Page.RESULTS:
        info['valid'] = ['click[back to search]']
        if products is None or page_num is None:
            print(page_num)
            print(products)
            raise Exception('Provide `products`, `page_num` to get `results` valid actions')
        if len(products) > 10:
            info['valid'].append('click[next >]')
        if page_num > 1:
            info['valid'].append('click[< prev]')
        for product in products:
            info['valid'].append('click[item - ' + product['Title'] + ']')
    if page_type == Page.ITEM_PAGE:
        if products is None or asin is None:
            raise Exception('Provide `products` and `asin` to get `item_page` valid actions')
        info['valid'] = ['click[back to search]', 'click[< prev]', 'click[description]', 'click[features]', 'click[buy now]']
        if 'options' in products[asin]:
            for key, values in products[asin]['options'].items():
                for value in values:
                    info['valid'].append('click[' + value + ']')
    if page_type == Page.SUB_PAGE:
        info['valid'] = ['click[back to search]', 'click[< prev]']
    info['image_feat'] = torch.zeros(512)
    return info

def agg(envs, attr):
    res = defaultdict(int)
    for env in envs:
        for k, v in getattr(env, attr).items():
            res[k] += v
    return res

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

def get_data(split, mem=False, filter_search=True):
    path = MEM_PATH if mem else PATH
    print('Loading data from {}'.format(path))
    with open(path, 'r') as json_file:
        json_list = list(json_file)
    human_goals = json.load(open(HUMAN_GOAL_PATH, 'r'))
    random.seed(233)
    random.shuffle(json_list)
    goal_range = range(len(human_goals))
    if split == 'train':
        goal_range = range(1500, len(human_goals))
    elif split == 'eval':
        goal_range = range(500, 1500)
    elif split == 'test':
        goal_range = range(0, 500)
    bad = cnt = 0
    state_list, action_list, idx_list, size_list = ([], [], [], [])
    image_list = []
    num_trajs = 0
    for json_str in json_list:
        result = json.loads(json_str)
        s = process_goal(result['states'][0])
        assert s in human_goals, s
        goal_idx = human_goals.index(s)
        if goal_idx not in goal_range:
            continue
        num_trajs += 1
        if 'images' not in result:
            result['images'] = [0] * len(result['states'])
        for state, valid_acts, idx, image in zip(result['states'], result['available_actions'], result['action_idxs'], result['images']):
            cnt += 1
            if filter_search and idx == -1:
                continue
            state_list.append(state)
            image_list.append([0.0] * 512 if image == 0 else image)
            if len(valid_acts) > 20:
                bad += 1
                new_idxs = list(range(6)) + random.sample(range(6, len(valid_acts)), 10)
                if idx not in new_idxs:
                    new_idxs += [idx]
                new_idxs = sorted(new_idxs)
                valid_acts = [valid_acts[i] for i in new_idxs]
                idx = new_idxs.index(idx)
            action_list.extend(valid_acts)
            idx_list.append(idx)
            size_list.append(len(valid_acts))
    print('num of {} trajs: {}'.format(split, num_trajs))
    print('total transitions and bad transitions: {} {}'.format(cnt, bad))
    state_list, action_list = (list(map(process, state_list)), list(map(process, action_list)))
    return (state_list, action_list, idx_list, size_list, image_list)

def data_collator(batch):
    state_input_ids, state_attention_mask, action_input_ids, action_attention_mask, sizes, labels, images = ([], [], [], [], [], [], [])
    for sample in batch:
        state_input_ids.append(sample['state_input_ids'])
        state_attention_mask.append(sample['state_attention_mask'])
        action_input_ids.extend(sample['action_input_ids'])
        action_attention_mask.extend(sample['action_attention_mask'])
        sizes.append(sample['sizes'])
        labels.append(sample['labels'])
        images.append(sample['images'])
    max_state_len = max((sum(x) for x in state_attention_mask))
    max_action_len = max((sum(x) for x in action_attention_mask))
    return {'state_input_ids': torch.tensor(state_input_ids)[:, :max_state_len], 'state_attention_mask': torch.tensor(state_attention_mask)[:, :max_state_len], 'action_input_ids': torch.tensor(action_input_ids)[:, :max_action_len], 'action_attention_mask': torch.tensor(action_attention_mask)[:, :max_action_len], 'sizes': torch.tensor(sizes), 'images': torch.tensor(images), 'labels': torch.tensor(labels)}

def get_data(split):
    data = json.load(open(PATH))
    goals, searches = ([], [])
    for goal, search_list in data.items():
        goal = process_goal(goal)
        for search in search_list:
            search = process_str(search)
            goals.append(goal)
            searches.append(search)
    n = len(goals)
    human_goals = json.load(open(HUMAN_GOAL_PATH, 'r'))
    goal_range = range(len(human_goals))
    if split == 'train':
        goal_range = range(500, len(human_goals))
    elif split == 'validation':
        goal_range = range(500, 1500)
    elif split == 'test':
        goal_range = range(0, 500)
    elif split == 'all':
        all_data = json.load(open(GOAL_PATH))
        all_goals = []
        all_goals_processed = []
        for ins_list in all_data.values():
            for ins in ins_list:
                ins = ins['instruction']
                all_goals.append(ins)
                all_goals_processed.append(process_str(ins))
        return (all_goals_processed, all_goals)
    goals_, searches_ = ([], [])
    for goal, search in zip(goals, searches):
        if goal in human_goals and human_goals.index(goal) in goal_range:
            goals_.append(goal)
            searches_.append(search)
    return (goals_, searches_)

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

def writekvs(self, kvs):
    for k, v in sorted(kvs.items()):
        if hasattr(v, 'dtype'):
            v = v.tolist()
            kvs[k] = float(v)
    self.file.write(json.dumps(kvs) + '\n')
    self.file.flush()

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

def __init__(self, dir, output_formats):
    self.name2val = defaultdict(float)
    self.name2cnt = defaultdict(int)
    self.level = INFO
    self.dir = dir
    self.output_formats = output_formats

def read_json(fname):
    import pandas
    ds = []
    with open(fname, 'rt') as fh:
        for line in fh:
            ds.append(json.loads(line))
    return pandas.DataFrame(ds)

def read_tb(path):
    """
    path : a tensorboard file OR a directory, where we will find all TB files
           of the form events.*
    """
    import pandas
    import numpy as np
    from glob import glob
    from collections import defaultdict
    import tensorflow as tf
    if osp.isdir(path):
        fnames = glob(osp.join(path, 'events.*'))
    elif osp.basename(path).startswith('events.'):
        fnames = [path]
    else:
        raise NotImplementedError('Expected tensorboard file or directory containing them. Got %s' % path)
    tag2pairs = defaultdict(list)
    maxstep = 0
    for fname in fnames:
        for summary in tf.train.summary_iterator(fname):
            if summary.step > 0:
                for v in summary.summary.value:
                    pair = (summary.step, v.simple_value)
                    tag2pairs[v.tag].append(pair)
                maxstep = max(summary.step, maxstep)
    data = np.empty((maxstep, len(tag2pairs)))
    data[:] = np.nan
    tags = sorted(tag2pairs.keys())
    for colidx, tag in enumerate(tags):
        pairs = tag2pairs[tag]
        for step, value in pairs:
            data[step - 1, colidx] = value
    return pandas.DataFrame(data, columns=tags)

def test_get_attribute_reward():
    goal = {'attributes': ['tea tree', 'essential oils', 'natural ingredients']}
    purchased = {'Attributes': ['tea tree', 'essential oil', 'natural ingredients']}
    r_attr, num_attr_matches = get_attribute_reward(purchased, goal)
    assert r_attr == 1
    assert num_attr_matches == 3
    goal = {'attributes': ['tea tree', 'essential oils', 'natural ingredients']}
    purchased = {'Attributes': ['essential oil', 'natural ingredients'], 'Title': '', 'BulletPoints': [], 'Description': ''}
    r_attr, num_attr_matches = get_attribute_reward(purchased, goal)
    assert r_attr == 2.0 / 3.0
    assert num_attr_matches == 2
    goal = {'attributes': ['tea tree', 'essential oils', 'natural ingredients']}
    purchased = {'Attributes': [], 'Title': '', 'BulletPoints': ['This shampoo has essential oils and smells like lemons'], 'Description': 'Best shampoo on the market, made with natural ingredients'}
    r_attr, num_attr_matches = get_attribute_reward(purchased, goal)
    assert r_attr == 2.0 / 3.0
    assert num_attr_matches == 2
    goal = {'attributes': ['tea tree', 'essential oils', 'natural ingredients']}
    purchased = {'Attributes': ['tea bag', 'earl gray', 'lipton'], 'Title': 'English tea for breakfast', 'BulletPoints': ['Soothing aroma', 'Calming, great feeling'], 'Description': 'Best tea made by Lipton, great to pair with breakfast'}
    r_attr, num_attr_matches = get_attribute_reward(purchased, goal)
    assert r_attr == 0
    assert num_attr_matches == 0

def test_get_option_reward():
    goal = ['grey', 'XL', 'pack of 12']
    purchased = ['pack of 12', 'grey', 'XL']
    r_option, matches = get_option_reward(purchased, goal)
    assert matches == len(goal)
    assert r_option == 1
    goal = ['grey', 'XL', 'pack of 12']
    purchased = ['pack of 12', 'blue', 'XL']
    r_option, matches = get_option_reward(purchased, goal)
    assert matches == len(goal) - 1
    assert r_option == 2.0 / 3.0
    goal = ['cool powder snow', 'XL', 'pack of 12']
    purchased = ['pack of 12', 'powder snow', 'XL']
    r_option, matches = get_option_reward(purchased, goal)
    assert matches == len(goal)
    assert r_option == 1
    goal = []
    purchased = ['goal 1', 'goal 2']
    r_option, matches = get_option_reward(purchased, goal)
    assert matches == 0
    assert r_option == None
    goal = ['goal 1', 'goal 2']
    purchased = []
    r_option, matches = get_option_reward(purchased, goal)
    assert matches == 0
    assert r_option == 0

