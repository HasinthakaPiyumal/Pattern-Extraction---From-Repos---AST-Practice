# Cluster 5

class SheepEnv(gym.Env):
    max_level = 10
    R = 10
    icons = [i for i in range(10)]
    ranges = [[2, 6], [1, 6], [1, 7], [0, 7], [0, 8]]

    def __init__(self, level: int, bucket_length: int=7, agent: bool=True, max_padding: bool=False) -> None:
        self.level = level
        assert 1 <= self.level <= self.max_level
        self.bucket_length = bucket_length
        self.agent = agent
        self.max_padding = max_padding
        self._make_game()

    def seed(self, seed: int) -> None:
        self._seed = seed
        np.random.seed(self._seed)

    def _make_game(self) -> None:
        self.icon_pool = self.icons[:2 * self.level]
        self.offset_pool = [0, 25, 50, 75][:1 + self.level]
        self.selected_range = self.ranges[min(4, self.level - 1)]
        self.max_item_per_icon = 9
        self.max_level_item_num = len(self.icons) * self.max_item_per_icon + 2
        if self.level >= 10:
            self.item_per_icon = 6 + (self.level - 5 + 1) // 2
            self.item_non_div = 2
        else:
            self.item_per_icon = 6
            self.item_non_div = 0
        self.total_item_num = len(self.icon_pool) * self.item_per_icon + self.item_non_div
        self.scene = []
        self.bucket = deque(maxlen=self.bucket_length)
        N = self.selected_range[1] - self.selected_range[0] - 1
        for i in range(len(self.icon_pool)):
            for j in range(self.item_per_icon):
                row = self.selected_range[0] + np.int64(N * np.random.random())
                column = self.selected_range[0] + np.int64(N * np.random.random())
                offset = self.offset_pool[np.int64(np.random.random() * len(self.offset_pool))]
                item = Item(self.icon_pool[i], offset, row, column)
                self.scene.append(item)
        if self.item_non_div > 0:
            for icon in np.random.choice(self.icon_pool, size=self.item_non_div, replace=False):
                row = self.selected_range[0] + np.int64(N * np.random.random())
                column = self.selected_range[0] + np.int64(N * np.random.random())
                offset = self.offset_pool[np.int64(np.random.random() * len(self.offset_pool))]
                item = Item(int(icon), offset, row, column)
                self.scene.append(item)
        self.cur_item_num = len(self.scene)
        self.reward_3tiles = self.R * 0.5 / (len(self.scene) // 3)
        self._update_visible_accessible()
        self._set_space()

    def _update_visible_accessible(self) -> None:
        for i in range(self.total_item_num):
            covered_items = []
            item1 = self.scene[i]
            if item1 is None:
                continue
            item1.accessible = 1
            for j in range(i + 1, self.total_item_num):
                item2 = self.scene[j]
                if item2 is None:
                    continue
                if not (item2.x + 100 <= item1.x or item2.x >= item1.x + 100 or item2.y + 100 <= item1.y or (item2.y >= item1.y + 100)):
                    item1.accessible = 0
                    if not self.agent:
                        break
                    covered_items.append(item2)
            if self.agent and len(covered_items) > 0:
                flag = np.zeros((2, 2)).astype(np.int64)
                core_x, core_y = (item1.x + 25, item1.y + 25)
                for item in covered_items:
                    min_x = max(core_x, item.x)
                    max_x = min(core_x + 50, item.x + 100)
                    min_y = max(core_y, item.y)
                    max_y = min(core_y + 50, item.y + 100)
                    if min_x < max_x or min_y < max_y:
                        flag[(min_x - core_x) // 25:(max_x - core_x) // 25, (min_y - core_y) // 25:(max_y - core_y) // 25] = 1
                        if flag.sum() == 4:
                            break
                item1.visible = int(flag.sum() < 4)
            else:
                item1.visible = 1

    def _execute_action(self, action: int) -> float:
        action_item = copy.deepcopy(self.scene[action])
        assert action_item is not None, action
        self.scene[action] = None
        self.cur_item_num -= 1
        same_items = []
        for i in range(len(self.bucket)):
            item = self.bucket[i]
            if item.icon == action_item.icon:
                same_items.append(item)
        if len(same_items) == 2:
            for item in same_items:
                self.bucket.remove(item)
            return copy.deepcopy(self.reward_3tiles)
        else:
            self.bucket.append(action_item)
            return 0.0

    def reset(self, level: Optional[int]=None) -> Dict:
        if level is not None:
            self.level = level
            assert 1 <= self.level <= self.max_level
        self._make_game()
        self._set_space()
        return self._get_obs()

    def close(self) -> None:
        pass

    def step(self, action: int) -> Tuple:
        rew = self._execute_action(action)
        self._update_visible_accessible()
        obs = self._get_obs()
        if self.cur_item_num == 0:
            rew += self.R
            done = True
        elif len(self.bucket) == self.bucket_length:
            rew -= self.R
            done = True
        else:
            done = False
        info = {}
        return (obs, rew, done, info)

    def _get_obs(self) -> Dict:
        item_obs = np.zeros((self.total_item_num, self.item_size))
        action_mask = np.zeros(self.total_item_num).astype(np.uint8)
        L, N = (self.L, self.N)
        p1, p2, p3 = (L + N, L + N + N, L + N + N + 2)
        for i in range(len(self.scene)):
            item = self.scene[i]
            if item is None:
                item_obs[i][L - 1] = 1
            else:
                item_obs[i][L + item.grid_x] = 1
                item_obs[i][p1 + item.grid_y] = 1
                item_obs[i][p3 + item.visible] = 1
                if item.visible:
                    item_obs[i][item.icon] = 1
                    item_obs[i][p2 + item.accessible] = 1
                else:
                    item_obs[i][L - 2] = 1
                if item.accessible:
                    action_mask[i] = 1
        bucket_obs = np.zeros(3 * len(self.icons))
        bucket_icon_stat = [0 for _ in range(len(self.icons))]
        for item in self.bucket:
            bucket_icon_stat[item.icon] += 1
        for i in range(len(bucket_icon_stat)):
            bucket_obs[i * 3 + bucket_icon_stat[i]] = 1
        global_obs = np.zeros(self.global_size)
        if self.max_padding:
            global_obs[self.cur_item_num // self.max_item_per_icon] = 1
        else:
            global_obs[self.cur_item_num // self.item_per_icon] = 1
        global_obs[self.global_size - self.bucket_length - 1 + len(self.bucket)] = 1
        return {'item_obs': item_obs, 'bucket_obs': bucket_obs, 'global_obs': global_obs, 'action_mask': action_mask}

    def _set_space(self) -> None:
        if self.max_padding:
            N = self.ranges[-1][1] - self.ranges[-1][0]
            L = len(self.icons) + 2
        else:
            N = self.selected_range[1] - self.selected_range[0]
            L = len(self.icon_pool) + 2
        self.L, self.N = (L, N)
        self.item_size = L + 4 * N * 2 + 2 + 2
        if self.max_padding:
            self.global_size = self.max_level_item_num // self.max_item_per_icon + 1 + self.bucket_length + 1
        else:
            self.global_size = self.total_item_num // self.item_per_icon + 1 + self.bucket_length + 1
        self.observation_space = gym.spaces.Dict({'item_obs': gym.spaces.Box(0, 1, dtype=np.float32, shape=(self.total_item_num, self.item_size)), 'bucket_obs': gym.spaces.Box(0, 1, dtype=np.float32, shape=(3 * len(self.icons),)), 'global_obs': gym.spaces.Box(0, 1, dtype=np.float32, shape=(self.global_size,)), 'action_mask': gym.spaces.Box(0, 1, dtype=np.float32, shape=(self.total_item_num,))})
        self.action_space = gym.spaces.Discrete(self.total_item_num)
        self.reward_space = gym.spaces.Box(-self.R * 1.5, self.R * 1.5, dtype=np.float32)

def seed(self, seed: int) -> None:
    self._seed = seed
    np.random.seed(self._seed)

def main(input_cfg, seed, max_env_step=int(1000000.0), max_train_iter=int(1000000.0)):
    cfg, create_cfg = input_cfg
    cfg = compile_config(cfg, seed=seed, auto=True, create_cfg=create_cfg)
    collector_env = create_env_manager(cfg.env.manager, [lambda: sheep_env_fn(cfg.env.level) for _ in range(cfg.env.collector_env_num)])
    evaluator_env = create_env_manager(cfg.env.manager, [lambda: sheep_env_fn(cfg.env.level) for _ in range(cfg.env.evaluator_env_num)])
    collector_env.seed(cfg.seed, dynamic_seed=False)
    evaluator_env.seed(cfg.seed, dynamic_seed=False)
    set_pkg_seed(cfg.seed, use_cuda=cfg.policy.cuda)
    obs_space = collector_env._env_ref.observation_space
    model = SheepModel(obs_space['item_obs'].shape[1], obs_space['item_obs'].shape[0], 'TF', obs_space['bucket_obs'].shape[0], obs_space['global_obs'].shape[0])
    policy = PPOPolicy(cfg.policy, model=model, enable_field=['learn', 'collect', 'eval'])
    tb_logger = SummaryWriter(os.path.join('./{}/log/'.format(cfg.exp_name), 'serial'))
    learner = BaseLearner(cfg.policy.learn.learner, policy.learn_mode, tb_logger, exp_name=cfg.exp_name)
    collector = create_serial_collector(cfg.policy.collect.collector, env=collector_env, policy=policy.collect_mode, tb_logger=tb_logger, exp_name=cfg.exp_name)
    evaluator = InteractionSerialEvaluator(cfg.policy.eval.evaluator, evaluator_env, policy.eval_mode, tb_logger, exp_name=cfg.exp_name)
    learner.call_hook('before_run')
    while True:
        if evaluator.should_eval(learner.train_iter):
            stop, reward = evaluator.eval(learner.save_checkpoint, learner.train_iter, collector.envstep)
            if stop:
                break
        new_data = collector.collect(train_iter=learner.train_iter)
        learner.train(new_data, collector.envstep)
        if collector.envstep >= max_env_step or learner.train_iter >= max_train_iter:
            break
    learner.call_hook('after_run')

def main(input_cfg, seed, max_env_step=int(10000000.0), max_train_iter=int(10000000.0)):
    cfg, create_cfg = input_cfg
    cfg = compile_config(cfg, seed=seed, auto=True, create_cfg=create_cfg)
    collector_env = create_env_manager(cfg.env.manager, [lambda: sheep_env_fn(cfg.env.level) for _ in range(cfg.env.collector_env_num)])
    evaluator_env = create_env_manager(cfg.env.manager, [lambda: sheep_env_fn(cfg.env.level) for _ in range(cfg.env.evaluator_env_num)])
    collector_env.seed(cfg.seed, dynamic_seed=False)
    evaluator_env.seed(cfg.seed, dynamic_seed=False)
    set_pkg_seed(cfg.seed, use_cuda=cfg.policy.cuda)
    obs_space = collector_env._env_ref.observation_space
    model = SheepModel(obs_space['item_obs'].shape[1], obs_space['item_obs'].shape[0], 'TF', obs_space['bucket_obs'].shape[0], obs_space['global_obs'].shape[0])
    policy = PPOPolicy(cfg.policy, model=model, enable_field=['learn', 'collect', 'eval'])
    tb_logger = SummaryWriter(os.path.join('./{}/log/'.format(cfg.exp_name), 'serial'))
    learner = BaseLearner(cfg.policy.learn.learner, policy.learn_mode, tb_logger, exp_name=cfg.exp_name)
    collector = create_serial_collector(cfg.policy.collect.collector, env=collector_env, policy=policy.collect_mode, tb_logger=tb_logger, exp_name=cfg.exp_name)
    evaluator = InteractionSerialEvaluator(cfg.policy.eval.evaluator, evaluator_env, policy.eval_mode, tb_logger, exp_name=cfg.exp_name)
    learner.call_hook('before_run')
    while True:
        if evaluator.should_eval(learner.train_iter):
            stop, reward = evaluator.eval(learner.save_checkpoint, learner.train_iter, collector.envstep)
            if stop:
                break
        new_data = collector.collect(train_iter=learner.train_iter)
        learner.train(new_data, collector.envstep)
        if collector.envstep >= max_env_step or learner.train_iter >= max_train_iter:
            break
    learner.call_hook('after_run')

@pytest.mark.unittest
def test_naive():
    B, M = (3, 30)
    model = SheepModel(item_num=30, item_encoder_type='two_stage_MLP')
    data = {'item_obs': torch.randn(B, M, 60), 'bucket_obs': torch.randn(B, 30), 'global_obs': torch.randn(B, 17), 'action_mask': torch.randint(0, 2, size=(M,)).bool()}
    output = model.forward(data, mode='compute_actor_critic')
    assert output['logit'].shape == (B, M)
    assert output['value'].shape == (B,)

