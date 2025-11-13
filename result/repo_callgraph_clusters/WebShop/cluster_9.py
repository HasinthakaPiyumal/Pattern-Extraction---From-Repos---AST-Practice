# Cluster 9

def generate_mturk_code(session_id: str) -> str:
    """Generates a redeem code corresponding to the session ID for an MTurk
    worker once the session is completed
    """
    sha = hashlib.sha1(session_id.encode())
    return sha.hexdigest()[:10].upper()

def bert_predict(obs, info, softmax=True):
    valid_acts = info['valid']
    assert valid_acts[0].startswith('click[')
    state_encodings = bert_tokenizer(process_str(obs), max_length=512, truncation=True, padding='max_length')
    action_encodings = bert_tokenizer(list(map(process_str, valid_acts)), max_length=512, truncation=True, padding='max_length')
    batch = {'state_input_ids': state_encodings['input_ids'], 'state_attention_mask': state_encodings['attention_mask'], 'action_input_ids': action_encodings['input_ids'], 'action_attention_mask': action_encodings['attention_mask'], 'sizes': len(valid_acts), 'images': info['image_feat'].tolist(), 'labels': 0}
    batch = data_collator([batch])
    outputs = bert_model(**batch)
    if softmax:
        idx = torch.multinomial(torch.nn.functional.softmax(outputs.logits[0], dim=0), 1)[0].item()
    else:
        idx = outputs.logits[0].argmax(0).item()
    return valid_acts[idx]

def predict(obs, info):
    """
    Given WebShop environment observation and info, predict an action.
    """
    valid_acts = info['valid']
    if valid_acts[0].startswith('click['):
        return bert_predict(obs, info)
    else:
        return 'search[' + bart_predict(process_goal(obs)) + ']'

def evaluate(agent, env, split, nb_episodes=10):
    with torch.no_grad():
        total_score = 0
        for method in ['greedy']:
            for ep in range(nb_episodes):
                log('Starting {} episode {}'.format(split, ep))
                if split == 'eval':
                    score = evaluate_episode(agent, env, split, method)
                elif split == 'test':
                    score = evaluate_episode(agent, env, split, method, idx=ep)
                log('{} episode {} ended with score {}\n\n'.format(split, ep, score))
                total_score += score
        avg_score = total_score / nb_episodes
        return avg_score

def evaluate_episode(agent, env, split, method='greedy', idx=None):
    step = 0
    done = False
    ob, info = env.reset(idx)
    state = agent.build_state(ob, info)
    log('Obs{}: {}'.format(step, ob.encode('utf-8')))
    while not done:
        valid_acts = info['valid']
        with torch.no_grad():
            action_str = agent.act([state], [valid_acts], method=method)[0][0]
        log('Action{}: {}'.format(step, action_str))
        ob, rew, done, info = env.step(action_str)
        log('Reward{}: {}, Score {}, Done {}'.format(step, rew, info['score'], done))
        step += 1
        log('Obs{}: {}'.format(step, ob.encode('utf-8')))
        state = agent.build_state(ob, info)
    tb.logkv_mean(f'{split}Score', info['score'])
    if 'verbose' in info:
        for k, v in info['verbose'].items():
            if k.startswith('r'):
                tb.logkv_mean(f'{split}_' + k, v)
    return info['score']

def train(agent, eval_env, test_env, envs, args):
    start = time.time()
    states, valids, transitions = ([], [], [])
    state0 = None
    for env in envs:
        ob, info = env.reset()
        if state0 is None:
            state0 = (ob, info)
        states.append(agent.build_state(ob, info))
        valids.append(info['valid'])
    for step in range(1, args.max_steps + 1):
        action_strs, action_ids, values = agent.act(states, valids, method=args.exploration_method)
        with torch.no_grad():
            action_values, _ = agent.network.rl_forward(states[:1], agent.encode_valids(valids[:1]))
        actions = sorted(zip(state0[1]['valid'], action_values.tolist()), key=lambda x: -x[1])
        log('State  {}: {}'.format(step, state0[0].lower().encode('utf-8')))
        log('Goal   {}: {}'.format(step, state0[1]['goal'].lower().encode('utf-8')))
        log('Actions{}: {}'.format(step, actions))
        log('>> Values{}: {}'.format(step, float(values[0])))
        log('>> Action{}: {}'.format(step, action_strs[0]))
        state0 = None
        next_states, next_valids, rewards, dones = ([], [], [], [])
        for env, action_str, action_id, state in zip(envs, action_strs, action_ids, states):
            ob, reward, done, info = env.step(action_str)
            if state0 is None:
                state0 = (ob, info)
                r_att = r_opt = 0
                if 'verbose' in info:
                    r_att = info['verbose'].get('r_att', 0)
                    r_option = info['verbose'].get('r_option ', 0)
                    r_price = info['verbose'].get('r_price', 0)
                    r_type = info['verbose'].get('r_type', 0)
                    w_att = info['verbose'].get('w_att', 0)
                    w_option = info['verbose'].get('w_option', 0)
                    w_price = info['verbose'].get('w_price', 0)
                    reward_str = f'{reward / 10:.2f} = ({r_att:.2f} * {w_att:.2f} + {r_option:.2f} * {w_option:.2f} + {r_price:.2f} * {w_price:.2f}) * {r_type:.2f}'
                else:
                    reward_str = str(reward)
                log('Reward{}: {}, Done {}\n'.format(step, reward_str, done))
            next_state = agent.build_state(ob, info)
            next_valid = info['valid']
            next_states, next_valids, rewards, dones = (next_states + [next_state], next_valids + [next_valid], rewards + [reward], dones + [done])
            if done:
                tb.logkv_mean('EpisodeScore', info['score'])
                category = env.session['goal']['category']
                tb.logkv_mean(f'EpisodeScore_{category}', info['score'])
                if 'verbose' in info:
                    for k, v in info['verbose'].items():
                        if k.startswith('r'):
                            tb.logkv_mean(k, v)
        transitions.append(TransitionPG(states, action_ids, rewards, values, agent.encode_valids(valids), dones))
        if len(transitions) >= args.bptt:
            _, _, last_values = agent.act(next_states, next_valids, method='softmax')
            stats = agent.update(transitions, last_values, step=step)
            for k, v in stats.items():
                tb.logkv_mean(k, v)
            del transitions[:]
            torch.cuda.empty_cache()
        for i, env in enumerate(envs):
            if dones[i]:
                ob, info = env.reset()
                if i == 0:
                    state0 = (ob, info)
                next_states[i] = agent.build_state(ob, info)
                next_valids[i] = info['valid']
        states, valids = (next_states, next_valids)
        if step % args.eval_freq == 0:
            evaluate(agent, eval_env, 'eval')
        if step % args.test_freq == 0:
            evaluate(agent, test_env, 'test', 500)
        if step % args.log_freq == 0:
            tb.logkv('Step', step)
            tb.logkv('FPS', int(step * len(envs) / (time.time() - start)))
            for k, v in agg(envs, 'stats').items():
                tb.logkv(k, v)
            items_clicked = agg(envs, 'items_clicked')
            tb.logkv('ItemsClicked', len(items_clicked))
            tb.dumpkvs()
        if step % args.ckpt_freq == 0:
            agent.save()

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

def predict(obs, info, model, softmax=False, rule=False, bart_model=None):
    valid_acts = info['valid']
    if valid_acts[0].startswith('search['):
        if bart_model is None:
            return valid_acts[-1]
        else:
            goal = process_goal(obs)
            query = bart_predict(goal, bart_model, num_return_sequences=5, num_beams=5)
            query = query[0]
            return f'search[{query}]'
    if rule:
        item_acts = [act for act in valid_acts if act.startswith('click[item - ')]
        if item_acts:
            return item_acts[0]
        else:
            assert 'click[buy now]' in valid_acts
            return 'click[buy now]'
    state_encodings = tokenizer(process(obs), max_length=512, truncation=True, padding='max_length')
    action_encodings = tokenizer(list(map(process, valid_acts)), max_length=512, truncation=True, padding='max_length')
    batch = {'state_input_ids': state_encodings['input_ids'], 'state_attention_mask': state_encodings['attention_mask'], 'action_input_ids': action_encodings['input_ids'], 'action_attention_mask': action_encodings['attention_mask'], 'sizes': len(valid_acts), 'images': info['image_feat'].tolist(), 'labels': 0}
    batch = data_collator([batch])
    batch = {k: v.cuda() for k, v in batch.items()}
    outputs = model(**batch)
    if softmax:
        idx = torch.multinomial(F.softmax(outputs.logits[0], dim=0), 1)[0].item()
    else:
        idx = outputs.logits[0].argmax(0).item()
    return valid_acts[idx]

def episode(model, idx=None, verbose=False, softmax=False, rule=False, bart_model=None):
    obs, info = env.reset(idx)
    if verbose:
        print(info['goal'])
    for i in range(100):
        action = predict(obs, info, model, softmax=softmax, rule=rule, bart_model=bart_model)
        if verbose:
            print(action)
        obs, reward, done, info = env.step(action)
        if done:
            return reward
    return 0

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

class WandBOutputFormat(KVWriter):

    def __init__(self, filename):
        group = None
        if filename.endswith('trial'):
            group = filename[:-6]
        wandb.init(project='web_drrn', name=filename, group=group)

    def writekvs(self, kvs):
        wandb.log(kvs)

    def close(self):
        pass

def writekvs(self, kvs):
    wandb.log(kvs)

def logkv_mean(key, val):
    """
    The same as logkv(), but if called many times, values averaged.
    """
    Logger.CURRENT.logkv_mean(key, val)

def log(*args, level=INFO):
    """
    Write the sequence of args, with no separators, to the console and output files (if you've configured an output file).
    """
    Logger.CURRENT.log(*args, level=level)

def debug(*args):
    log(*args, level=DEBUG)

def info(*args):
    log(*args, level=INFO)

def warn(*args):
    log(*args, level=WARN)

def error(*args):
    log(*args, level=ERROR)

def reset():
    if Logger.CURRENT is not Logger.DEFAULT:
        Logger.CURRENT.close()
        Logger.CURRENT = Logger.DEFAULT
        log('Reset logger')

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

