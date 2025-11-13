# Cluster 5

def evaluate_vae(encoder, decoder, actions, rewards, states):
    """

    :param encoder: RNN encoder network
    :param decoder: reward decoder
    :param actions: array of actions of shape: (T, batch, action_dim)
    :param rewards: array of rewards of shape: (T, batch, 1)
    :param states: array of states of shape: (T, batch, state_dim)
    :return:
    """
    if actions.dim() != 3:
        actions = actions.unsqueeze(dim=0)
        states = states.unsqueeze(dim=0)
        rewards = rewards.unsqueeze(dim=0)
    T, batch_size, _ = actions.size()
    means, logvars, hidden_states, reward_preds = ([], [], [], [])
    with torch.no_grad():
        task_sample, task_mean, task_logvar, hidden_state = encoder.prior(batch_size)
    means.append(task_mean)
    logvars.append(task_logvar)
    hidden_states.append(hidden_state)
    reward_preds.append(ptu.get_numpy(decoder(task_sample, None)))
    for action, reward, state in zip(actions, rewards, states):
        action = action.unsqueeze(dim=0)
        state = state.unsqueeze(dim=0)
        reward = reward.unsqueeze(dim=0)
        with torch.no_grad():
            task_sample, task_mean, task_logvar, hidden_state = encoder(actions=action.float(), states=state, rewards=reward, hidden_state=hidden_state, return_prior=False)
        means.append(task_mean.unsqueeze(dim=0))
        logvars.append(task_logvar.unsqueeze(dim=0))
        hidden_states.append(hidden_state)
        reward_preds.append(ptu.get_numpy(decoder(task_sample.unsqueeze(dim=0), None)))
    means = torch.cat(means, dim=0)
    logvars = torch.cat(logvars, dim=0)
    hidden_states = torch.cat(hidden_states, dim=0)
    reward_preds = np.vstack(reward_preds)
    return (means, logvars, hidden_states, reward_preds)

def rollout_policy(env, learner):
    is_vae_exist = 'vae' in dir(learner)
    observations = []
    actions = []
    rewards = []
    values = []
    if is_vae_exist:
        latent_samples = []
        latent_means = []
        latent_logvars = []
    obs = ptu.from_numpy(env.reset())
    obs = obs.reshape(-1, obs.shape[-1])
    observations.append(obs)
    done_rollout = False
    if is_vae_exist:
        with torch.no_grad():
            task_sample, task_mean, task_logvar, hidden_state = learner.vae.encoder.prior(batch_size=1)
        latent_samples.append(ptu.get_numpy(task_sample[0, 0]))
        latent_means.append(ptu.get_numpy(task_mean[0, 0]))
        latent_logvars.append(ptu.get_numpy(task_logvar[0, 0]))
    while not done_rollout:
        if is_vae_exist:
            augmented_obs = learner.get_augmented_obs(obs=obs, task_mu=task_mean, task_std=task_logvar)
            with torch.no_grad():
                action, value = learner.agent.act(obs=augmented_obs, deterministic=True)
        else:
            action, _, _, _ = learner.agent.act(obs=obs)
        next_obs, reward, done, info = utl.env_step(env, action.squeeze(dim=0))
        observations.append(next_obs)
        actions.append(action)
        values.append(value)
        rewards.append(reward.item())
        done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
        if is_vae_exist:
            task_sample, task_mean, task_logvar, hidden_state = learner.vae.encoder(action, next_obs, reward.reshape((1, 1)), hidden_state, return_prior=False)
            latent_samples.append(ptu.get_numpy(task_sample[0]))
            latent_means.append(ptu.get_numpy(task_mean[0]))
            latent_logvars.append(ptu.get_numpy(task_logvar[0]))
        obs = next_obs.clone()
    if is_vae_exist:
        return (observations, actions, rewards, values, latent_samples, latent_means, latent_logvars)
    else:
        return (observations, actions, rewards, values)

def get_test_rollout(args, env, policy, encoder=None):
    num_episodes = args.max_rollouts_per_task
    episode_prev_obs = [[] for _ in range(num_episodes)]
    episode_next_obs = [[] for _ in range(num_episodes)]
    episode_actions = [[] for _ in range(num_episodes)]
    episode_rewards = [[] for _ in range(num_episodes)]
    episode_returns = []
    episode_lengths = []
    if encoder is not None:
        episode_latent_samples = [[] for _ in range(num_episodes)]
        episode_latent_means = [[] for _ in range(num_episodes)]
        episode_latent_logvars = [[] for _ in range(num_episodes)]
    else:
        curr_latent_sample = curr_latent_mean = curr_latent_logvar = None
        episode_latent_means = episode_latent_logvars = None
    [obs_raw, obs_normalised] = env.reset()
    obs_raw = obs_raw.reshape((1, -1)).to(ptu.device)
    obs_normalised = obs_normalised.reshape((1, -1)).to(ptu.device)
    for episode_idx in range(num_episodes):
        curr_rollout_rew = []
        if encoder is not None:
            if episode_idx == 0 and encoder:
                curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder.prior(1)
                curr_latent_sample = curr_latent_sample[0].to(ptu.device)
                curr_latent_mean = curr_latent_mean[0].to(ptu.device)
                curr_latent_logvar = curr_latent_logvar[0].to(ptu.device)
            episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
            episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
            episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
        for step_idx in range(1, env._max_episode_steps + 1):
            episode_prev_obs[episode_idx].append(obs_raw.clone())
            _, action, _ = utl.select_action(args=args, policy=policy, obs=obs_normalised if args.norm_obs_for_policy else obs_raw, deterministic=True, task_sample=curr_latent_sample, task_mean=curr_latent_mean, task_logvar=curr_latent_logvar)
            (obs_raw, obs_normalised), (rew_raw, rew_normalised), done, infos = utl.env_step(env, action)
            obs_raw = obs_raw.reshape((1, -1)).to(ptu.device)
            obs_normalised = obs_normalised.reshape((1, -1)).to(ptu.device)
            if encoder is not None:
                curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder(action.float().to(ptu.device), obs_raw, rew_raw.reshape((1, 1)).float().to(ptu.device), hidden_state, return_prior=False)
                episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
                episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
                episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
            episode_next_obs[episode_idx].append(obs_raw.clone())
            episode_rewards[episode_idx].append(rew_raw.clone())
            episode_actions[episode_idx].append(action.clone())
            if infos[0]['done_mdp']:
                break
        episode_returns.append(sum(curr_rollout_rew))
        episode_lengths.append(step_idx)
    if encoder is not None:
        episode_latent_means = [torch.stack(e) for e in episode_latent_means]
        episode_latent_logvars = [torch.stack(e) for e in episode_latent_logvars]
    episode_prev_obs = [torch.cat(e) for e in episode_prev_obs]
    episode_next_obs = [torch.cat(e) for e in episode_next_obs]
    episode_actions = [torch.cat(e) for e in episode_actions]
    episode_rewards = [torch.cat(r) for r in episode_rewards]
    return (episode_latent_means, episode_latent_logvars, episode_prev_obs, episode_next_obs, episode_actions, episode_rewards, episode_returns)

def predict_rewards(learner, means, logvars):
    reward_preds = ptu.zeros([means.shape[0], learner.env.num_states])
    for t in range(reward_preds.shape[0]):
        task_samples = learner.vae.encoder._sample_gaussian(ptu.FloatTensor(means[t]), ptu.FloatTensor(logvars[t]), num=50)
        reward_preds[t, :] = learner.vae.reward_decoder(ptu.FloatTensor(task_samples), None).mean(dim=0).detach()
    return ptu.get_numpy(reward_preds)

def env_step(env, action):
    action = ptu.get_numpy(action)
    if env.action_space.__class__.__name__ == 'Discrete':
        action = np.argmax(action)
    next_obs, reward, done, info = env.step(action)
    next_obs = ptu.from_numpy(next_obs).view(-1, next_obs.shape[0])
    reward = ptu.FloatTensor([reward]).view(-1, 1)
    done = ptu.from_numpy(np.array(done, dtype=int)).view(-1, 1)
    return (next_obs, reward, done, info)

def select_action(args, policy, obs, deterministic, task_sample=None, task_mean=None, task_logvar=None):
    """
    Select action using the policy.
    """
    obs = get_augmented_obs(args, obs, task_sample, task_mean, task_logvar)
    action = policy.act(obs, deterministic)
    if isinstance(action, list) or isinstance(action, tuple):
        value, action, action_log_prob = action
    else:
        value = None
        action_log_prob = None
    action = action.to(ptu.device)
    return (value, action, action_log_prob)

def get_augmented_obs(args, obs, posterior_sample=None, task_mu=None, task_std=None):
    obs_augmented = obs.clone()
    if posterior_sample is None:
        sample_embeddings = False
    else:
        sample_embeddings = args.sample_embeddings
    if not args.condition_policy_on_state:
        obs_augmented = ptu.zeros(0)
    if sample_embeddings and posterior_sample is not None:
        obs_augmented = torch.cat((obs_augmented, posterior_sample), dim=1)
    elif task_mu is not None and task_std is not None:
        task_mu = task_mu.reshape((-1, task_mu.shape[-1]))
        task_std = task_std.reshape((-1, task_std.shape[-1]))
        obs_augmented = torch.cat((obs_augmented, task_mu, task_std), dim=-1)
    return obs_augmented

def update_encoding(encoder, obs, action, reward, done, hidden_state):
    if done is not None:
        hidden_state = encoder.reset_hidden(hidden_state, done)
    with torch.no_grad():
        task_sample, task_mean, task_logvar, hidden_state = encoder(actions=action.float(), states=obs, rewards=reward, hidden_state=hidden_state, return_prior=False)
    return (task_sample, task_mean, task_logvar, hidden_state)

def update_linear_schedule(optimizer, epoch, total_num_epochs, initial_lr):
    """Decreases the learning rate linearly"""
    lr = initial_lr - initial_lr * (epoch / float(total_num_epochs))
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr

def recompute_embeddings(policy_storage, encoder, sample, update_idx):
    task_sample = [policy_storage.task_samples[0].detach().clone()]
    task_mean = [policy_storage.task_mu[0].detach().clone()]
    task_logvar = [policy_storage.task_logvar[0].detach().clone()]
    task_sample[0].requires_grad = True
    task_mean[0].requires_grad = True
    task_logvar[0].requires_grad = True
    h = policy_storage.hidden_states[0].detach()
    for i in range(policy_storage.actions.shape[0]):
        reset_task = policy_storage.done[i + 1]
        h = encoder.reset_hidden(h, reset_task)
        ts, tm, tl, h = encoder(policy_storage.actions.float()[i:i + 1], policy_storage.next_obs_raw[i:i + 1], policy_storage.rewards_raw[i:i + 1], h, sample=sample, return_prior=False)
        task_sample.append(ts)
        task_mean.append(tm)
        task_logvar.append(tl)
    if update_idx == 0:
        try:
            assert (torch.cat(policy_storage.task_mu) - torch.cat(task_mean)).sum() == 0
            assert (torch.cat(policy_storage.task_logvar) - torch.cat(task_logvar)).sum() == 0
        except AssertionError:
            warnings.warn('You are not recomputing the embeddings correctly!')
            import pdb
            pdb.set_trace()
    policy_storage.task_samples = task_sample
    policy_storage.task_mu = task_mean
    policy_storage.task_logvar = task_logvar

class ActionRewardResetWrapper(gym.Wrapper):

    def __init__(self, env, no_terminal):
        super().__init__(env)
        self.env = env
        self.no_terminal = no_terminal
        self.action_size = env.action_space.n if hasattr(env.action_space, 'n') else env.action_space.shape[0]

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        if isinstance(action, int):
            action_vec = np.zeros(self.action_size)
            action_vec[action] = 1.0
        else:
            assert isinstance(action, np.ndarray) and action.shape == (self.action_size,), 'Wrong one-hot action shape'
            action_vec = action
        obs['action'] = action_vec
        obs['reward'] = np.array(reward)
        obs['terminal'] = np.array(False if self.no_terminal or info.get('time_limit') else done)
        obs['reset'] = np.array(False)
        return (obs, reward, done, info)

    def reset(self):
        obs = self.env.reset()
        obs['action'] = np.zeros(self.action_size)
        obs['reward'] = np.array(0.0)
        obs['terminal'] = np.array(False)
        obs['reset'] = np.array(True)
        return obs

def reset(self):
    obs = self.env.reset()
    obs['action'] = np.zeros(self.action_size)
    obs['reward'] = np.array(0.0)
    obs['terminal'] = np.array(False)
    obs['reset'] = np.array(True)
    return obs

class CollectWrapper(gym.Wrapper):

    def __init__(self, env):
        super().__init__(env)
        self.env = env
        self.episode = []

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.episode.append(obs.copy())
        if done:
            episode = {k: np.array([t[k] for t in self.episode]) for k in self.episode[0]}
            info['episode'] = episode
        return (obs, reward, done, info)

    def reset(self):
        obs = self.env.reset()
        self.episode = [obs.copy()]
        return obs

def step(self, action):
    obs, reward, done, info = self.env.step(action)
    self.episode.append(obs.copy())
    if done:
        episode = {k: np.array([t[k] for t in self.episode]) for k in self.episode[0]}
        info['episode'] = episode
    return (obs, reward, done, info)

class VizDoomEnvironment(gym.Env):
    metadata = {'render.modes': ['rgb_array'], 'video.frames_per_second': 35}
    scenarios = {'basic': {'baseline': {'scenario': 'basic.wad', 'living_reward': 1, 'death_penalty': 0, 'reward': 'health'}, 'floor_ceiling_flipped': {'scenario': 'basic_floor_ceiling_flipped.wad'}, 'torches': {'scenario': 'basic_torches.wad'}, 'random_textures_set_a': {'sampler': sample_textures(TEXTURES_SET_A)}, 'random_textures_set_b': {'sampler': sample_textures(TEXTURES_SET_B)}, 'random_things_set_a': {'scenario': 'basic_torches.wad', 'sampler': sample_things(THINGS_SET_A, modify_things=[56])}, 'random_things_set_b': {'scenario': 'basic_torches.wad', 'sampler': sample_things(THINGS_SET_B, modify_things=[56])}}, 'navigation': {'baseline': {'scenario': 'navigation.wad', 'living_reward': 1, 'death_penalty': 0, 'reward': 'health'}, 'new_layout': {'scenario': 'navigation_new_layout.wad'}, 'floor_ceiling_flipped': {'scenario': 'navigation_floor_ceiling_flipped.wad'}, 'torches': {'scenario': 'navigation_torches.wad'}, 'random_textures_set_a': {'sampler': sample_textures(TEXTURES_SET_A)}, 'random_textures_set_b': {'sampler': sample_textures(TEXTURES_SET_B)}, 'random_things_set_a': {'scenario': 'navigation_torches.wad', 'sampler': sample_things(THINGS_SET_A, modify_things=[56])}, 'random_things_set_b': {'scenario': 'navigation_torches.wad', 'sampler': sample_things(THINGS_SET_B, modify_things=[56])}}}
    buttons = [vizdoom.Button.MOVE_FORWARD, vizdoom.Button.MOVE_BACKWARD, vizdoom.Button.MOVE_RIGHT, vizdoom.Button.MOVE_LEFT, vizdoom.Button.TURN_LEFT, vizdoom.Button.TURN_RIGHT, vizdoom.Button.ATTACK, vizdoom.Button.SPEED]
    opposite_button_pairs = [(vizdoom.Button.MOVE_FORWARD, vizdoom.Button.MOVE_BACKWARD), (vizdoom.Button.MOVE_RIGHT, vizdoom.Button.MOVE_LEFT), (vizdoom.Button.TURN_LEFT, vizdoom.Button.TURN_RIGHT)]

    def __init__(self, scenario, variant, obs_type='image', frameskip=4):
        if scenario not in self.scenarios:
            raise error.Error('Unsupported scenario: {}'.format(scenario))
        if variant not in self.scenarios[scenario]:
            raise error.Error('Unsupported scenario variant: {}'.format(variant))
        config = {}
        config.update(self.scenarios[scenario]['baseline'])
        config.update(self.scenarios[scenario][variant])
        self._config = config
        self._vizdoom = vizdoom.DoomGame()
        self._vizdoom.set_doom_scenario_path(os.path.join(ASSET_PATH, config['scenario']))
        self._vizdoom.set_doom_map(config.get('map', 'MAP01'))
        self._vizdoom.set_screen_resolution(vizdoom.ScreenResolution.RES_640X480)
        self._vizdoom.set_screen_format(vizdoom.ScreenFormat.BGR24)
        self._vizdoom.set_mode(vizdoom.Mode.PLAYER)
        self._width = 640
        self._height = 480
        self._depth = 3
        self._vizdoom.set_render_hud(False)
        self._vizdoom.set_render_minimal_hud(False)
        self._vizdoom.set_render_crosshair(False)
        self._vizdoom.set_render_weapon(False)
        self._vizdoom.set_render_decals(False)
        self._vizdoom.set_render_particles(False)
        self._vizdoom.set_render_effects_sprites(False)
        self._vizdoom.set_render_messages(False)
        self._vizdoom.set_render_corpses(False)
        self._vizdoom.set_window_visible(False)
        self._vizdoom.set_sound_enabled(False)
        self._vizdoom.set_living_reward(config.get('living_reward', 1))
        self._vizdoom.set_death_penalty(config.get('death_penalty', 100))
        self._vizdoom.set_episode_timeout(config.get('episode_timeout', 2100))
        for button in self.buttons:
            self._vizdoom.add_available_button(button)
        self._action_button_map = []
        for combination in itertools.product([False, True], repeat=len(self.buttons)):
            valid = True
            for a, b in self.opposite_button_pairs:
                if combination[self.buttons.index(a)] and combination[self.buttons.index(b)]:
                    valid = False
                    break
            if valid:
                self._action_button_map.append(list(combination))
        self.action_space = spaces.Discrete(len(self._action_button_map))
        if obs_type == 'image':
            self.observation_space = spaces.Box(low=0, high=255, shape=(self._height, self._width, self._depth))
        else:
            raise error.Error('Unrecognized observation type: {}'.format(obs_type))
        self._scenario = scenario
        self._variant = variant
        self._obs_type = obs_type
        self._frameskip = frameskip
        self._initialized = False
        self._temporary_scenario = None
        self._seed()

    def __getstate__(self):
        return {'scenario': self._scenario, 'variant': self._variant, 'obs_type': self._obs_type, 'frameskip': self._frameskip}

    def __setstate__(self, state):
        self.__init__(**state)

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        self._vizdoom.set_seed(seed % 2 ** 32)
        return [seed]

    def _get_observation(self):
        state = self._vizdoom.get_state()
        if self._obs_type == 'image':
            if not state:
                return np.zeros([self._height, self._width, self._depth])
            return state.screen_buffer
        raise NotImplementedError

    def _reset(self):
        sampler = self._config.get('sampler', None)
        if sampler:
            if self._temporary_scenario:
                try:
                    os.remove(self._temporary_scenario)
                except OSError:
                    pass
                self._temporary_scenario = None
            self._temporary_scenario = sampler(self, self._config)
            self._vizdoom.set_doom_scenario_path(self._temporary_scenario)
        if not self._initialized:
            self._vizdoom.init()
            self._initialized = True
        self._vizdoom.new_episode()
        return self._get_observation()

    def _get_state_variables(self):
        return {'health': self._vizdoom.get_game_variable(vizdoom.GameVariable.HEALTH), 'frags': self._vizdoom.get_game_variable(vizdoom.GameVariable.FRAGCOUNT)}

    def _step(self, action):
        previous_info = self._get_state_variables()
        action = self._action_button_map[action]
        scenario_reward = self._vizdoom.make_action(action, self._frameskip)
        terminal = self._vizdoom.is_episode_finished() or self._vizdoom.is_player_dead()
        observation = self._get_observation()
        info = self._get_state_variables()
        reward_value = self._config.get('reward', 'reward')
        if reward_value == 'reward':
            reward = scenario_reward
        else:
            reward = info[reward_value] - previous_info[reward_value]
        return (observation, reward, terminal, info)

    def get_keys_to_action(self):
        return {(): 0}

def _get_observation(self):
    state = self._vizdoom.get_state()
    if self._obs_type == 'image':
        if not state:
            return np.zeros([self._height, self._width, self._depth])
        return state.screen_buffer
    raise NotImplementedError

class PhysicalWorld(cocos.layer.Layer):
    """Physical world, which may be rendered."""
    fps = 50
    physical_scale = 32.0
    n_actions = 0

    def __init__(self, width, height):
        super(PhysicalWorld, self).__init__()
        self._contacts = ContactListener()
        self._filter = ContactFilter()
        self._engine = box_2d.b2World(gravity=(0, 0), contactListener=self._contacts, contactFilter=self._filter)
        self._width, self._height = (width, height)
        self._destroy_queue = []
        self.add(cocos.layer.ColorLayer(0, 0, 0, 255))
        self._batch = cocos.batch.BatchNode()
        self.add(self._batch)
        self.seed()
        self.create_world(self._batch)
        self.reset_world()
        self._terminal = False

    def create_world(self, parent):
        """Create the physical world."""
        raise NotImplementedError

    def reset_world(self):
        """Reset the world."""
        self._terminal = False

    def act(self, action):
        """Perform an external action in the world."""
        pass

    def seed(self, seed=None):
        """Setup random number generator."""
        self.np_random, seed = seeding.np_random(seed)
        return seed

    @property
    def is_terminal(self):
        return self._terminal

    @property
    def engine(self):
        """Physics engine world."""
        return self._engine

    @property
    def ground(self):
        """Ground body."""
        return self._ground

    @property
    def parameters(self):
        """World-defining parameters."""
        return {}

    def destroy_body(self, body):
        """Queue specific body for destruction."""
        self._destroy_queue.append(body)

    def process_destroy_queue(self):
        """Process any pending object destructions."""
        for body in self._destroy_queue:
            self._engine.DestroyBody(body)
        self._destroy_queue = []

    def step(self):
        """Perform one simulation step."""
        self.process_destroy_queue()
        self._engine.Step(1.0 / self.fps, 6 * 30, 2 * 30)
        self._engine.ClearForces()

        def step_node(node):
            if not isinstance(node, PhysicalObject):
                return
            node.step()
        self.walk(step_node)

def destroy_body(self, body):
    """Queue specific body for destruction."""
    self._destroy_queue.append(body)

class PhysicalEnvironment:
    """Physical environment based on Box2D/Cocos2D."""

    def __init__(self, world):
        width = 640
        height = 480
        window = getattr(cocos.director.director, 'window', None)
        if window is None:
            pyglet.resource.path = [ASSET_PATH]
            pyglet.resource.reindex()
            window = cocos.director.director.init(width=width, height=height)
        self._window = window
        self._width = width
        self._height = height
        self._world = world(width=width, height=height)
        self._scene = cocos.scene.Scene(cocos.layer.ColorLayer(0, 0, 0, 255), self._world)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def world(self):
        return self._world

    @property
    def is_terminal(self):
        return self._world.is_terminal

    def step(self):
        """Perform one environment update step."""
        self._world.step()
        return self.is_terminal

    def reset(self):
        """Reset the world."""
        self._world.reset_world()

    def act(self, action):
        """Perform an action on the world."""
        self._world.act(action)

    def seed(self, seed=None):
        """Seed random number generator."""
        return self._world.seed(seed)

    def render(self, mode='human'):
        """Render the environment."""
        if cocos.director.director.scene != self._scene:
            cocos.director.director._set_scene(self._scene)
        self._window.switch_to()
        self._window.dispatch_events()
        self._window.dispatch_event('on_draw')
        if mode == 'human':
            self._window.flip()
        elif mode == 'rgb_array':
            color_buffer = pyglet.image.get_buffer_manager().get_color_buffer()
            image_data = color_buffer.get_image_data()
            data = np.fromstring(image_data.data, dtype=np.uint8, sep='')
            data = data.reshape(color_buffer.height, color_buffer.width, 4)
            data = data[::-1, :, 0:3]
            return data

def act(self, action):
    """Perform an action on the world."""
    self._world.act(action)

class PycolabEnvironment(object):
    """A simple environment adapter for pycolab games."""

    def __init__(self, game, num_apples=10, apple_reward=1.0, fix_apple_reward_in_episode=False, final_reward=10.0, respawn_every=20, crop=True, default_reward=0, REWARD_GRID=key_to_door.REWARD_GRID_SR, max_frames=key_to_door.MAX_FRAMES_PER_PHASE_SR):
        """Construct a `environment.Base` adapter that wraps a pycolab game."""
        rng = np.random.RandomState()
        if game == 'key_to_door':
            self._game = key_to_door.Game(rng=rng, num_apples=num_apples, apple_reward=apple_reward, fix_apple_reward_in_episode=fix_apple_reward_in_episode, final_reward=final_reward, respawn_every=respawn_every, crop=crop, REWARD_GRID=REWARD_GRID, max_frames=max_frames)
        else:
            raise ValueError('Unsupported game "%s".' % game)
        self._default_reward = default_reward
        self._num_actions = self._game.num_actions
        colours = nest.map_structure(lambda c: float(c) * 255 / 1000, self._game.colours)
        self._rgb_converter = rendering.ObservationToArray(value_mapping=colours, permute=(1, 2, 0), dtype=np.uint8)
        episode = self._game.make_episode()
        observation, _, _ = episode.its_showtime()
        self._image_shape = self._rgb_converter(observation).shape

    def _process_outputs(self, observation, reward):
        if reward is None:
            reward = self._default_reward
        image = self._rgb_converter(observation)
        return (image, reward)

    def reset(self):
        """Start a new episode."""
        self._episode = self._game.make_episode()
        observation, reward, _ = self._episode.its_showtime()
        return self._process_outputs(observation, reward)

    def step(self, action):
        """Take step in episode."""
        observation, reward, _ = self._episode.play(action)
        return self._process_outputs(observation, reward)

    @property
    def num_actions(self):
        return self._num_actions

    @property
    def observation_shape(self):
        return self._image_shape

    @property
    def episode_length(self):
        return self._game.episode_length

    def last_phase_reward(self):
        return float(self._episode.the_plot['chapter_reward'])

def last_phase_reward(self):
    return float(self._episode.the_plot['chapter_reward'])

class VariBadWrapper(gym.Wrapper):

    def __init__(self, env, episodes_per_task: int, oracle: bool=False):
        """
        Wrapper, creates a multi-episode (BA)MDP around a one-episode MDP. Automatically deals with
        - horizons H in the MDP vs horizons H+ in the BAMDP,
        - resetting the tasks
        - normalized actions in case of continuous action space
        - adding the timestep / done info to the state (might be needed to make states markov)
        """
        super().__init__(env)
        if isinstance(self.env.action_space, gym.spaces.Box):
            self._normalize_actions = True
        else:
            self._normalize_actions = False
        self.oracle = oracle
        if self.oracle == True:
            print('WARNING: YOU ARE RUNNING MDP, NOT POMDP!\n')
            tmp_task = self.env.get_current_task()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_task)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_task)]), dtype=np.float32)
        if episodes_per_task > 1:
            self.add_done_info = True
        else:
            self.add_done_info = False
        if self.add_done_info:
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, 0]), high=np.array([*self.observation_space.high, 1]), dtype=np.float32)
        self.episodes_per_task = episodes_per_task
        self.episode_count = 0
        self.step_count_bamdp = 0.0
        try:
            self.horizon_bamdp = self.episodes_per_task * self.env._max_episode_steps
        except AttributeError:
            self.horizon_bamdp = self.episodes_per_task * self.env.unwrapped._max_episode_steps
        self.done_mdp = True

    def _get_obs(self, state):
        if self.oracle:
            tmp_task = self.env.get_current_task().copy()
            state = np.concatenate([state, tmp_task])
        if self.add_done_info:
            state = np.concatenate((state, [float(self.done_mdp)]))
        return state

    def reset(self, task=None):
        self.env.reset_task(task)
        self.episode_count = 0
        self.step_count_bamdp = 0
        try:
            state = self.env.reset()
        except AttributeError:
            state = self.env.unwrapped.reset()
        self.done_mdp = False
        return self._get_obs(state)

    def wrap_state_with_done(self, state):
        if self.add_done_info:
            state = np.concatenate((state, [float(self.done_mdp)]))
        return state

    def reset_mdp(self):
        state = self.env.reset()
        self.done_mdp = False
        return self._get_obs(state)

    def step(self, action):
        if self._normalize_actions:
            action = np.clip(action, -1, 1)
            lb = self.env.action_space.low
            ub = self.env.action_space.high
            action = lb + (action + 1.0) * 0.5 * (ub - lb)
            action = np.clip(action, lb, ub)
        state, reward, self.done_mdp, info = self.env.step(action)
        info['done_mdp'] = self.done_mdp
        state = self._get_obs(state)
        self.step_count_bamdp += 1
        done_bamdp = False
        if self.done_mdp:
            self.episode_count += 1
            if self.episode_count == self.episodes_per_task:
                done_bamdp = True
        if self.done_mdp and (not done_bamdp):
            info['start_state'] = self.reset_mdp()
        return (state, reward, done_bamdp, info)

def wrap_state_with_done(self, state):
    if self.add_done_info:
        state = np.concatenate((state, [float(self.done_mdp)]))
    return state

class GridNavi(gym.Env):

    def __init__(self, num_cells=5, num_steps=15, n_tasks=2, modify_init_state_dist=False, is_sparse=False, return_belief_rewards=False, seed=None, **kwargs):
        super(GridNavi, self).__init__()
        if seed is not None:
            self.seed(seed)
        self.n_tasks = n_tasks
        self.num_cells = num_cells
        self.num_states = num_cells ** 2
        self.grid_size = (num_cells, num_cells)
        self.is_sparse = is_sparse
        self.return_belief_rewards = return_belief_rewards
        self.modify_init_state_dist = modify_init_state_dist
        self._max_episode_steps = num_steps
        self.step_count = 0
        self.observation_space = spaces.Box(low=0, high=self.num_cells - 1, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Discrete(5)
        self.starting_states = [(0.0, 0.0)]
        self.states = [(x, y) for y in np.arange(0, num_cells) for x in np.arange(0, num_cells)]
        self.possible_goals = self.states.copy()
        for s in self.starting_states:
            self.possible_goals.remove(s)
        self.possible_goals.remove((0, 1))
        self.possible_goals.remove((1, 1))
        self.possible_goals.remove((1, 0))
        self.num_tasks = min(n_tasks, len(self.possible_goals))
        self.goals = random.sample(self.possible_goals, self.num_tasks)
        self.reset_task(0)
        if self.return_belief_rewards:
            self._belief_state = self._reset_belief()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        random.seed(seed)
        return [seed]

    def get_all_task_idx(self):
        return range(len(self.goals))

    def get_task(self):
        return self._goal

    def set_goal(self, goal):
        self._goal = np.asarray(goal)

    def reset_task(self, idx=None):
        """reset goal and state"""
        if idx is not None:
            self._goal = np.array(self.goals[idx])
        self.reset()

    def _reset_belief(self):
        self._belief_state = np.zeros(self.num_cells ** 2)
        for pg in self.possible_goals:
            idx = self.task_to_id(np.array(pg))
            self._belief_state[idx] = 1.0 / len(self.possible_goals)
        return self._belief_state

    def reset_model(self):
        if self.modify_init_state_dist:
            self._state = np.array(random.choice(self.states))
            while (self._state == self._goal).all():
                self._state = np.array(random.choice(self.states))
        else:
            self._state = np.array(random.choice(self.starting_states))
        self._belief_state = self._reset_belief()
        return self.get_obs()

    def get_obs(self):
        return np.copy(self._state)

    def update_belief(self, state):
        if self.is_goal_state():
            self._belief_state *= 0
            self._belief_state[self.task_to_id(self._goal)] = 1
        else:
            self._belief_state[self.task_to_id(state)] = 0
            self._belief_state = np.ceil(self._belief_state)
            self._belief_state /= sum(self._belief_state)

    def reset(self):
        self.step_count = 0
        return self.reset_model()

    def reward(self, state, action=None):
        if state[0] == self._goal[0] and state[1] == self._goal[1]:
            return 1.0
        else:
            return 0.0 if self.is_sparse else -0.1

    def state_transition(self, action):
        """
        Moving the agent between states
        """
        if action == 1:
            self._state[1] = min([self._state[1] + 1, self.num_cells - 1])
        elif action == 2:
            self._state[0] = min([self._state[0] + 1, self.num_cells - 1])
        elif action == 3:
            self._state[1] = max([self._state[1] - 1, 0])
        elif action == 4:
            self._state[0] = max([self._state[0] - 1, 0])

    def step(self, action):
        if isinstance(action, np.ndarray) and action.ndim == 1:
            action = action[0]
        assert self.action_space.contains(action)
        info = {'task': self.get_task()}
        done = False
        self.state_transition(action)
        self.step_count += 1
        if self.step_count >= self._max_episode_steps:
            done = True
        if self.return_belief_rewards:
            self.update_belief(self._state)
            belief_reward = self._compute_belief_reward()
            info.update({'belief_reward': belief_reward})
        reward = self.reward(self._state)
        return (self.get_obs(), reward, done, info)

    def _compute_belief_reward(self):
        num_possible_goal_belief = np.sum(self._belief_state != 0)
        non_goal_rew = 0.0 if self.is_sparse else -0.1
        belief_reward = (1.0 + non_goal_rew * (num_possible_goal_belief - 1)) / num_possible_goal_belief
        return belief_reward

    def is_goal_state(self):
        if self._state[0] == self._goal[0] and self._state[1] == self._goal[1]:
            return True
        else:
            return False

    def task_to_id(self, goals):
        mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).transpose(1, 0)
        if isinstance(goals, list) or isinstance(goals, tuple):
            goals = np.array(goals)
        if isinstance(goals, np.ndarray):
            goals = torch.from_numpy(goals)
        goals = goals.long()
        if goals.dim() == 1:
            goals = goals.unsqueeze(0)
        goal_shape = goals.shape
        if len(goal_shape) > 2:
            goals = goals.reshape(-1, goals.shape[-1])
        classes = mat[goals[:, 0], goals[:, 1]]
        classes = classes.reshape(goal_shape[:-1])
        return classes

    def id_to_task(self, classes):
        mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).numpy().T
        goals = np.zeros((len(classes), 2))
        classes = classes.numpy()
        for i in range(len(classes)):
            pos = np.where(classes[i] == mat)
            goals[i, 0] = float(pos[0][0])
            goals[i, 1] = float(pos[1][0])
        goals = torch.from_numpy(goals).to(ptu.device).float()
        return goals

    def goal_to_onehot_id(self, pos):
        cl = self.task_to_id(pos)
        if cl.dim() == 1:
            cl = cl.view(-1, 1)
        nb_digits = self.num_cells ** 2
        y_onehot = torch.FloatTensor(pos.shape[0], nb_digits).to(ptu.device)
        y_onehot.zero_()
        y_onehot.scatter_(1, cl, 1)
        return y_onehot

    def onehot_id_to_goal(self, pos):
        if isinstance(pos, list):
            pos = [self.id_to_task(p.argmax(dim=1)) for p in pos]
        else:
            pos = self.id_to_task(pos.argmax(dim=1))
        return pos

    def render(self, mode='human'):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def plot_env(self):
        for i in range(self.num_cells):
            for j in range(self.num_cells):
                pos_i = i
                pos_j = j
                rec = Rectangle((pos_i, pos_j), 1, 1, facecolor='none', alpha=0.5, edgecolor='k')
                plt.gca().add_patch(rec)
        goal = np.array(self._goal) + 0.5
        plt.plot(goal[0], goal[1], 'kx')
        plt.plot(goal[0], goal[1], 'kx')

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        if isinstance(observations, tuple) or isinstance(observations, list):
            observations = torch.cat(observations)
        observations = observations + 0.5
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)
        plt.plot(observations[-1, 0], observations[-1, 1], **kwargs)
        plt.xticks([])
        plt.yticks([])
        plt.xlim([0, self.num_cells])
        plt.ylim([0, self.num_cells])
        plt.axis('equal')

def _reset_belief(self):
    self._belief_state = np.zeros(self.num_cells ** 2)
    for pg in self.possible_goals:
        idx = self.task_to_id(np.array(pg))
        self._belief_state[idx] = 1.0 / len(self.possible_goals)
    return self._belief_state

def id_to_task(self, classes):
    mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).numpy().T
    goals = np.zeros((len(classes), 2))
    classes = classes.numpy()
    for i in range(len(classes)):
        pos = np.where(classes[i] == mat)
        goals[i, 0] = float(pos[0][0])
        goals[i, 1] = float(pos[1][0])
    goals = torch.from_numpy(goals).to(ptu.device).float()
    return goals

def goal_to_onehot_id(self, pos):
    cl = self.task_to_id(pos)
    if cl.dim() == 1:
        cl = cl.view(-1, 1)
    nb_digits = self.num_cells ** 2
    y_onehot = torch.FloatTensor(pos.shape[0], nb_digits).to(ptu.device)
    y_onehot.zero_()
    y_onehot.scatter_(1, cl, 1)
    return y_onehot

class RAMEfficient_SeqReplayBuffer:
    buffer_type = 'seq_efficient'

    def __init__(self, max_replay_buffer_size, observation_dim, action_dim, sampled_seq_len: int, sample_weight_baseline: float, observation_type, **kwargs):
        """
        this buffer is used for sequence/trajectory/episode:
                it stored the whole sequence
                into the buffer (not transition), and can sample (sub)sequences
                that has 3D shape (sampled_seq_len, batch_size, dim)
                based on some rules below.
        it still uses 2D size as normal (max_replay_buffer_size, dim)
                but tracks the sequences

        NOTE: it only save observations once, no next_observation to reduce RAM by ~2,
            especially useful for image observations

        """
        self._max_replay_buffer_size = max_replay_buffer_size
        self._observation_dim = observation_dim
        self._action_dim = action_dim
        if observation_type == np.uint8:
            observation_type = np.uint8
        else:
            observation_type = np.float32
        self._observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=observation_type)
        self._actions = np.zeros((max_replay_buffer_size, action_dim), dtype=np.float32)
        self._rewards = np.zeros((max_replay_buffer_size, 1), dtype=np.float32)
        self._terminals = np.zeros((max_replay_buffer_size, 1), dtype=np.uint8)
        self._ends = np.zeros(max_replay_buffer_size, dtype=np.uint8)
        self._valid_starts = np.zeros(max_replay_buffer_size, dtype=np.float32)
        assert sampled_seq_len >= 2
        assert sample_weight_baseline >= 0.0
        self._sampled_seq_len = sampled_seq_len
        self._sample_weight_baseline = sample_weight_baseline
        self.clear()
        RAM = 0.0
        for name, var in vars(self).items():
            if isinstance(var, np.ndarray):
                RAM += var.nbytes
        print(f'buffer RAM usage: {RAM / 1024 ** 3:.2f} GB')

    def size(self):
        return self._size

    def clear(self):
        self._top = 0
        self._size = 0

    def add_episode(self, observations, actions, rewards, terminals, next_observations):
        """
        NOTE: must add one whole episode/sequence/trajectory,
                        not some partial transitions
        the length of different episode can vary, but must be greater than 2
                so that the end of valid_starts is 0.

        all the inputs have 2D shape of (L, dim)
        """
        assert observations.shape[0] == actions.shape[0] == rewards.shape[0] == terminals.shape[0] == next_observations.shape[0] >= 2
        seq_len = observations.shape[0]
        indices = list(np.arange(self._top, self._top + seq_len) % self._max_replay_buffer_size)
        self._observations[indices] = observations
        self._actions[indices] = actions
        self._rewards[indices] = rewards
        self._terminals[indices] = terminals
        self._valid_starts[indices] = self._compute_valid_starts(seq_len)
        self._ends[indices] = 0
        self._top = (self._top + seq_len) % self._max_replay_buffer_size
        self._observations[self._top] = next_observations[-1]
        self._actions[self._top] = 0.0
        self._rewards[self._top] = 0.0
        self._terminals[self._top] = 1
        self._valid_starts[self._top] = 0.0
        self._ends[self._top] = 1
        self._top = (self._top + 1) % self._max_replay_buffer_size
        self._size = min(self._size + seq_len + 1, self._max_replay_buffer_size)

    def _compute_valid_starts(self, seq_len):
        valid_starts = np.ones(seq_len, dtype=float)
        num_valid_starts = float(max(1.0, seq_len - self._sampled_seq_len + 1.0))
        total_weights = self._sample_weight_baseline + num_valid_starts
        valid_starts *= total_weights / num_valid_starts
        valid_starts[int(num_valid_starts):] = 0.0
        return valid_starts

    def random_episodes(self, batch_size):
        """
        return each item has 3D shape (sampled_seq_len, batch_size, dim)
        """
        sampled_episode_starts = self._sample_indices(batch_size)
        indices = []
        next_indices = []
        for start in sampled_episode_starts:
            end = start + self._sampled_seq_len
            indices += list(np.arange(start, end) % self._max_replay_buffer_size)
            next_indices += list(np.arange(start + 1, end + 1) % self._max_replay_buffer_size)
        batch = self._sample_data(indices, next_indices)
        masks = self._generate_masks(indices, batch_size)
        batch['mask'] = masks
        for k in batch.keys():
            batch[k] = batch[k].reshape(batch_size, self._sampled_seq_len, -1).transpose(1, 0, 2)
        return batch

    def _sample_indices(self, batch_size):
        valid_starts_indices = np.where(self._valid_starts > 0.0)[0]
        sample_weights = np.copy(self._valid_starts[valid_starts_indices])
        sample_weights /= sample_weights.sum()
        return np.random.choice(valid_starts_indices, size=batch_size, p=sample_weights)

    def _sample_data(self, indices, next_indices):
        return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._observations[next_indices])

    def _generate_masks(self, indices, batch_size):
        """
        input: sampled_indices list of len B*T
        output: masks (B, T)
        """
        sampled_seq_ends = np.copy(self._ends[indices]).reshape(batch_size, self._sampled_seq_len).astype(np.float32)
        masks = np.ones_like(sampled_seq_ends)
        diff = sampled_seq_ends[:, :-1] - sampled_seq_ends[:, 1:]
        diff = np.concatenate([np.zeros((batch_size, 1)), diff], axis=1)
        invalid_starts_b, invalid_starts_t = np.where(diff == -1.0)
        invalid_indices_b = []
        invalid_indices_t = []
        last_batch_index = -1
        for batch_index, start_index in zip(invalid_starts_b, invalid_starts_t):
            if batch_index == last_batch_index:
                continue
            last_batch_index = batch_index
            invalid_indices = list(np.arange(start_index, self._sampled_seq_len))
            invalid_indices_b += [batch_index] * len(invalid_indices)
            invalid_indices_t += invalid_indices
        masks[invalid_indices_b, invalid_indices_t] = 0.0
        return masks

def __init__(self, max_replay_buffer_size, observation_dim, action_dim, sampled_seq_len: int, sample_weight_baseline: float, observation_type, **kwargs):
    """
        this buffer is used for sequence/trajectory/episode:
                it stored the whole sequence
                into the buffer (not transition), and can sample (sub)sequences
                that has 3D shape (sampled_seq_len, batch_size, dim)
                based on some rules below.
        it still uses 2D size as normal (max_replay_buffer_size, dim)
                but tracks the sequences

        NOTE: it only save observations once, no next_observation to reduce RAM by ~2,
            especially useful for image observations

        """
    self._max_replay_buffer_size = max_replay_buffer_size
    self._observation_dim = observation_dim
    self._action_dim = action_dim
    if observation_type == np.uint8:
        observation_type = np.uint8
    else:
        observation_type = np.float32
    self._observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=observation_type)
    self._actions = np.zeros((max_replay_buffer_size, action_dim), dtype=np.float32)
    self._rewards = np.zeros((max_replay_buffer_size, 1), dtype=np.float32)
    self._terminals = np.zeros((max_replay_buffer_size, 1), dtype=np.uint8)
    self._ends = np.zeros(max_replay_buffer_size, dtype=np.uint8)
    self._valid_starts = np.zeros(max_replay_buffer_size, dtype=np.float32)
    assert sampled_seq_len >= 2
    assert sample_weight_baseline >= 0.0
    self._sampled_seq_len = sampled_seq_len
    self._sample_weight_baseline = sample_weight_baseline
    self.clear()
    RAM = 0.0
    for name, var in vars(self).items():
        if isinstance(var, np.ndarray):
            RAM += var.nbytes
    print(f'buffer RAM usage: {RAM / 1024 ** 3:.2f} GB')

class SimpleReplayBuffer(ReplayBuffer):
    buffer_type = 'markov'

    def __init__(self, max_replay_buffer_size, observation_dim, action_dim, max_trajectory_len: int, add_timeout: bool=False, **kwargs):
        """
        :param max_replay_buffer_size:
        :param observation_dim:
        :param action_dim:
        :param trajectory_len:
        :param kwargs: reward_types list [goal_reward, contact_reward, ...]

        NOTE: difference from terminal and timeout:
        - for model-based methods (e.g. varibad): add_timeout = False, we only have terminals
                - for VAE, terminal is whether time out, so we use terminal to sample episodes
                - for policy, terminal is whether reach goal, so we use terminal to bootstrap or not in sampled transitions
        - for model-free methods (e.g. RNN policy): add_timeout = True, we have both terminals and dones
                - we only have policy buffer
                - terminal is whether reach goal for bootstrap
                - timeout is whether time out for sampling episodes
        """
        self._max_replay_buffer_size = max_replay_buffer_size
        self._observation_dim = observation_dim
        self._action_dim = action_dim
        self.trajectory_len = max_trajectory_len
        self._observations = np.zeros((max_replay_buffer_size, observation_dim))
        self._next_obs = np.zeros((max_replay_buffer_size, observation_dim))
        self._actions = np.zeros((max_replay_buffer_size, action_dim))
        self._rewards = np.zeros((max_replay_buffer_size, 1))
        self._terminals = np.zeros((max_replay_buffer_size, 1), dtype='uint8')
        self.add_timeout = add_timeout
        if add_timeout:
            self._timeouts = np.zeros((max_replay_buffer_size, 1), dtype='uint8')
        self.clear()

    def add_sample(self, observation, action, reward, terminal, next_observation, timeout=None, **kwargs):
        self._observations[self._top] = observation
        self._actions[self._top] = action
        self._rewards[self._top] = reward
        self._terminals[self._top] = terminal
        self._next_obs[self._top] = next_observation
        if self.add_timeout:
            self._timeouts[self._top] = timeout
        self._advance()
        if self.add_timeout and timeout or (not self.add_timeout and terminal):
            self.terminate_episode()

    def terminate_episode(self):
        self._episode_starts.append(self._curr_episode_start)
        if len(self._episode_starts) > int(self._max_replay_buffer_size / self.trajectory_len):
            del self._episode_starts[0]
        self._curr_episode_start = self._top

    def size(self):
        return self._size

    def clear(self):
        self._top = 0
        self._size = 0
        self._episode_starts = []
        self._curr_episode_start = 0

    def _advance(self, step=1):
        self._top = (self._top + step) % self._max_replay_buffer_size
        self._size = min(self._size + step, self._max_replay_buffer_size)

    def sample_data(self, indices):
        return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._next_obs[indices])

    def random_batch(self, batch_size):
        """batch of unordered transitions"""
        indices = np.random.randint(0, self._size, batch_size)
        return self.sample_data(indices)

    def can_sample_batch(self, batch_size):
        return self._size >= batch_size

    def random_episodes(self, num_episodes, sub_traj_len=-1, replace=False):
        """NOTE: return each item has 3D shape (sub_traj_len, num_episodes, dim)"""
        episode_indices = np.random.choice(range(self.num_complete_episodes()), num_episodes, replace=replace)
        assert sub_traj_len <= self.trajectory_len
        if sub_traj_len == -1:
            sub_traj_len = self.trajectory_len
        assert sub_traj_len >= 1
        sub_traj_starts = np.random.randint(0, self.trajectory_len - sub_traj_len + 1, num_episodes)
        indices = []
        for idx, sub_traj_start in zip(episode_indices, sub_traj_starts):
            start = self._episode_starts[idx] + sub_traj_start
            end = start + sub_traj_len
            indices += list(np.arange(start, end) % self._max_replay_buffer_size)
        raw_batch = self.sample_data(indices)
        batch = dict()
        for k in raw_batch.keys():
            batch[k] = raw_batch[k].reshape(num_episodes, sub_traj_len, -1).transpose(1, 0, 2)
        return batch

    def can_sample_episodes(self, num_episodes=None):
        if num_episodes is None:
            num_episodes = 1
        return self.num_complete_episodes() >= num_episodes

    def num_steps_can_sample(self):
        return self._size

    def num_complete_episodes(self):
        return len(self._episode_starts)

def __init__(self, max_replay_buffer_size, observation_dim, action_dim, max_trajectory_len: int, add_timeout: bool=False, **kwargs):
    """
        :param max_replay_buffer_size:
        :param observation_dim:
        :param action_dim:
        :param trajectory_len:
        :param kwargs: reward_types list [goal_reward, contact_reward, ...]

        NOTE: difference from terminal and timeout:
        - for model-based methods (e.g. varibad): add_timeout = False, we only have terminals
                - for VAE, terminal is whether time out, so we use terminal to sample episodes
                - for policy, terminal is whether reach goal, so we use terminal to bootstrap or not in sampled transitions
        - for model-free methods (e.g. RNN policy): add_timeout = True, we have both terminals and dones
                - we only have policy buffer
                - terminal is whether reach goal for bootstrap
                - timeout is whether time out for sampling episodes
        """
    self._max_replay_buffer_size = max_replay_buffer_size
    self._observation_dim = observation_dim
    self._action_dim = action_dim
    self.trajectory_len = max_trajectory_len
    self._observations = np.zeros((max_replay_buffer_size, observation_dim))
    self._next_obs = np.zeros((max_replay_buffer_size, observation_dim))
    self._actions = np.zeros((max_replay_buffer_size, action_dim))
    self._rewards = np.zeros((max_replay_buffer_size, 1))
    self._terminals = np.zeros((max_replay_buffer_size, 1), dtype='uint8')
    self.add_timeout = add_timeout
    if add_timeout:
        self._timeouts = np.zeros((max_replay_buffer_size, 1), dtype='uint8')
    self.clear()

def terminate_episode(self):
    self._episode_starts.append(self._curr_episode_start)
    if len(self._episode_starts) > int(self._max_replay_buffer_size / self.trajectory_len):
        del self._episode_starts[0]
    self._curr_episode_start = self._top

class SeqReplayBuffer:
    buffer_type = 'seq_vanilla'

    def __init__(self, max_replay_buffer_size, observation_dim, action_dim, sampled_seq_len: int, sample_weight_baseline: float, **kwargs):
        """
        this buffer is used for sequence/trajectory/episode:
                it stored the whole sequence
                into the buffer (not transition), and can sample (sub)sequences
                that has 3D shape (sampled_seq_len, batch_size, dim)
                based on some rules below.
        it still uses 2D size as normal (max_replay_buffer_size, dim)
                but tracks the sequences

        NOTE: it save observations twice, so it is vanilla version of seq replay buffer,
            sufficient to vector-based observations, as RAM is not the bottleneck
        """
        self._max_replay_buffer_size = max_replay_buffer_size
        self._observation_dim = observation_dim
        self._action_dim = action_dim
        self._observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=np.float32)
        self._next_observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=np.float32)
        self._actions = np.zeros((max_replay_buffer_size, action_dim), dtype=np.float32)
        self._rewards = np.zeros((max_replay_buffer_size, 1), dtype=np.float32)
        self._terminals = np.zeros((max_replay_buffer_size, 1), dtype=np.uint8)
        self._valid_starts = np.zeros(max_replay_buffer_size, dtype=np.float32)
        assert sampled_seq_len >= 2
        assert sample_weight_baseline >= 0.0
        self._sampled_seq_len = sampled_seq_len
        self._sample_weight_baseline = sample_weight_baseline
        self.clear()
        RAM = 0.0
        for name, var in vars(self).items():
            if isinstance(var, np.ndarray):
                RAM += var.nbytes
        print(f'buffer RAM usage: {RAM / 1024 ** 3:.2f} GB')

    def size(self):
        return self._size

    def clear(self):
        self._top = 0
        self._size = 0

    def add_episode(self, observations, actions, rewards, terminals, next_observations):
        """
        NOTE: must add one whole episode/sequence/trajectory,
                        not some partial transitions
        the length of different episode can vary, but must be greater than 2
                so that the end of valid_starts is 0.

        all the inputs have 2D shape of (L, dim)
        """
        assert observations.shape[0] == actions.shape[0] == rewards.shape[0] == terminals.shape[0] == next_observations.shape[0] >= 2
        seq_len = observations.shape[0]
        indices = list(np.arange(self._top, self._top + seq_len) % self._max_replay_buffer_size)
        self._observations[indices] = observations
        self._actions[indices] = actions
        self._rewards[indices] = rewards
        self._terminals[indices] = terminals
        self._next_observations[indices] = next_observations
        self._valid_starts[indices] = self._compute_valid_starts(seq_len)
        self._top = (self._top + seq_len) % self._max_replay_buffer_size
        self._size = min(self._size + seq_len, self._max_replay_buffer_size)

    def _compute_valid_starts(self, seq_len):
        valid_starts = np.ones(seq_len, dtype=float)
        num_valid_starts = float(max(1.0, seq_len - self._sampled_seq_len + 1.0))
        total_weights = self._sample_weight_baseline + num_valid_starts
        valid_starts *= total_weights / num_valid_starts
        valid_starts[int(num_valid_starts):] = 0.0
        return valid_starts

    def random_episodes(self, batch_size):
        """
        return each item has 3D shape (sampled_seq_len, batch_size, dim)
        """
        sampled_episode_starts = self._sample_indices(batch_size)
        indices = []
        for start in sampled_episode_starts:
            end = start + self._sampled_seq_len
            indices += list(np.arange(start, end) % self._max_replay_buffer_size)
        batch = self._sample_data(indices)
        masks = self._generate_masks(indices, batch_size)
        batch['mask'] = masks
        for k in batch.keys():
            batch[k] = batch[k].reshape(batch_size, self._sampled_seq_len, -1).transpose(1, 0, 2)
        return batch

    def _sample_indices(self, batch_size):
        valid_starts_indices = np.where(self._valid_starts > 0.0)[0]
        sample_weights = np.copy(self._valid_starts[valid_starts_indices])
        sample_weights /= sample_weights.sum()
        return np.random.choice(valid_starts_indices, size=batch_size, p=sample_weights)

    def _sample_data(self, indices):
        return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._next_observations[indices])

    def _generate_masks(self, indices, batch_size):
        """
        input: sampled_indices list of len B*T
        output: masks (B, T)
        """
        sampled_seq_valids = np.copy(self._valid_starts[indices]).reshape(batch_size, self._sampled_seq_len)
        sampled_seq_valids[sampled_seq_valids > 0.0] = 1.0
        masks = np.ones_like(sampled_seq_valids, dtype=float)
        diff = sampled_seq_valids[:, :-1] - sampled_seq_valids[:, 1:]
        diff = np.concatenate([np.ones((batch_size, 1)), diff], axis=1)
        indices_array = np.array(indices).reshape(batch_size, self._sampled_seq_len)
        diff[indices_array == self._top] = -1.0
        invalid_starts_b, invalid_starts_t = np.where(diff == -1.0)
        invalid_indices_b = []
        invalid_indices_t = []
        last_batch_index = -1
        for batch_index, start_index in zip(invalid_starts_b, invalid_starts_t):
            if batch_index == last_batch_index:
                continue
            last_batch_index = batch_index
            invalid_indices = list(np.arange(start_index, self._sampled_seq_len))
            invalid_indices_b += [batch_index] * len(invalid_indices)
            invalid_indices_t += invalid_indices
        masks[invalid_indices_b, invalid_indices_t] = 0.0
        return masks

def __init__(self, max_replay_buffer_size, observation_dim, action_dim, sampled_seq_len: int, sample_weight_baseline: float, **kwargs):
    """
        this buffer is used for sequence/trajectory/episode:
                it stored the whole sequence
                into the buffer (not transition), and can sample (sub)sequences
                that has 3D shape (sampled_seq_len, batch_size, dim)
                based on some rules below.
        it still uses 2D size as normal (max_replay_buffer_size, dim)
                but tracks the sequences

        NOTE: it save observations twice, so it is vanilla version of seq replay buffer,
            sufficient to vector-based observations, as RAM is not the bottleneck
        """
    self._max_replay_buffer_size = max_replay_buffer_size
    self._observation_dim = observation_dim
    self._action_dim = action_dim
    self._observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=np.float32)
    self._next_observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=np.float32)
    self._actions = np.zeros((max_replay_buffer_size, action_dim), dtype=np.float32)
    self._rewards = np.zeros((max_replay_buffer_size, 1), dtype=np.float32)
    self._terminals = np.zeros((max_replay_buffer_size, 1), dtype=np.uint8)
    self._valid_starts = np.zeros(max_replay_buffer_size, dtype=np.float32)
    assert sampled_seq_len >= 2
    assert sample_weight_baseline >= 0.0
    self._sampled_seq_len = sampled_seq_len
    self._sample_weight_baseline = sample_weight_baseline
    self.clear()
    RAM = 0.0
    for name, var in vars(self).items():
        if isinstance(var, np.ndarray):
            RAM += var.nbytes
    print(f'buffer RAM usage: {RAM / 1024 ** 3:.2f} GB')

class FlattenMlp(Mlp):
    """
    if there are multiple inputs, concatenate along last dim
    """

    def forward(self, *inputs, **kwargs):
        flat_inputs = torch.cat(inputs, dim=-1)
        return super().forward(flat_inputs, **kwargs)

def forward(self, *inputs, **kwargs):
    flat_inputs = torch.cat(inputs, dim=-1)
    return super().forward(flat_inputs, **kwargs)

class TanhNormal(Distribution):
    """aka squashed normal
    Represent distribution of X where
        X ~ tanh(Z)
        Z ~ N(mean, std)
    Note: this is not very numerically stable.
    """

    def __init__(self, normal_mean, normal_std, epsilon=1e-06):
        """
        :param normal_mean: Mean of the normal distribution
        :param normal_std: Std of the normal distribution
        :param epsilon: Numerical stability epsilon when computing log-prob.
        """
        self.normal_mean = normal_mean
        self.normal_std = normal_std
        self.normal = Normal(normal_mean, normal_std)
        self.epsilon = epsilon

    def sample_n(self, n, return_pre_tanh_value=False):
        z = self.normal.sample_n(n)
        if return_pre_tanh_value:
            return (torch.tanh(z), z)
        else:
            return torch.tanh(z)

    def log_prob(self, value, pre_tanh_value=None):
        """
        :param value: some value, x
        :param pre_tanh_value: arctanh(x)
        :return:
        """
        if pre_tanh_value is None:
            pre_tanh_value = torch.atanh(value)
        return self.normal.log_prob(pre_tanh_value) - torch.log(1 - value * value + self.epsilon)

    def sample(self, return_pretanh_value=False):
        z = self.normal.sample()
        if return_pretanh_value:
            return (torch.tanh(z), z)
        else:
            return torch.tanh(z)

    def rsample(self, return_pretanh_value=False):
        z = self.normal_mean + self.normal_std * Variable(Normal(ptu.zeros(self.normal_mean.size()), ptu.ones(self.normal_std.size())).sample())
        if return_pretanh_value:
            return (torch.tanh(z), z)
        else:
            return torch.tanh(z)

def __init__(self, normal_mean, normal_std, epsilon=1e-06):
    """
        :param normal_mean: Mean of the normal distribution
        :param normal_std: Std of the normal distribution
        :param epsilon: Numerical stability epsilon when computing log-prob.
        """
    self.normal_mean = normal_mean
    self.normal_std = normal_std
    self.normal = Normal(normal_mean, normal_std)
    self.epsilon = epsilon

def sample_n(self, n, return_pre_tanh_value=False):
    z = self.normal.sample_n(n)
    if return_pre_tanh_value:
        return (torch.tanh(z), z)
    else:
        return torch.tanh(z)

def sample(self, return_pretanh_value=False):
    z = self.normal.sample()
    if return_pretanh_value:
        return (torch.tanh(z), z)
    else:
        return torch.tanh(z)

def rsample(self, return_pretanh_value=False):
    z = self.normal_mean + self.normal_std * Variable(Normal(ptu.zeros(self.normal_mean.size()), ptu.ones(self.normal_std.size())).sample())
    if return_pretanh_value:
        return (torch.tanh(z), z)
    else:
        return torch.tanh(z)

class PyTorchModule(nn.Module, Serializable, metaclass=abc.ABCMeta):

    def get_param_values(self):
        return self.state_dict()

    def set_param_values(self, param_values):
        self.load_state_dict(param_values)

    def get_param_values_np(self):
        state_dict = self.state_dict()
        np_dict = OrderedDict()
        for key, tensor in state_dict.items():
            np_dict[key] = ptu.get_numpy(tensor)
        return np_dict

    def set_param_values_np(self, param_values):
        torch_dict = OrderedDict()
        for key, tensor in param_values.items():
            torch_dict[key] = ptu.from_numpy(tensor)
        self.load_state_dict(torch_dict)

    def copy(self):
        copy = Serializable.clone(self)
        ptu.copy_model_params_from_to(self, copy)
        return copy

    def save_init_params(self, locals):
        """
        Should call this FIRST THING in the __init__ method if you ever want
        to serialize or clone this network.

        Usage:
        ```
        def __init__(self, ...):
            self.init_serialization(locals())
            ...
        ```
        :param locals:
        :return:
        """
        Serializable.quick_init(self, locals)

    def __getstate__(self):
        d = Serializable.__getstate__(self)
        d['params'] = self.get_param_values()
        return d

    def __setstate__(self, d):
        Serializable.__setstate__(self, d)
        self.set_param_values(d['params'])

    def regularizable_parameters(self):
        """
        Return generator of regularizable parameters. Right now, all non-flat
        vectors are assumed to be regularizabled, presumably because only
        biases are flat.

        :return:
        """
        for param in self.parameters():
            if len(param.size()) > 1:
                yield param

    def eval_np(self, *args, **kwargs):
        """
        Eval this module with a numpy interface

        Same as a call to __call__ except all Variable input/outputs are
        replaced with numpy equivalents.

        Assumes the output is either a single object or a tuple of objects.
        """
        torch_args = tuple((torch_ify(x) for x in args))
        torch_kwargs = {k: torch_ify(v) for k, v in kwargs.items()}
        outputs = self.__call__(*torch_args, **torch_kwargs)
        if isinstance(outputs, tuple):
            return tuple((np_ify(x) for x in outputs))
        else:
            return np_ify(outputs)

def copy(self):
    copy = Serializable.clone(self)
    ptu.copy_model_params_from_to(self, copy)
    return copy

def torch_ify(np_array_or_other):
    if isinstance(np_array_or_other, np.ndarray):
        return ptu.from_numpy(np_array_or_other)
    else:
        return np_array_or_other

def np_ify(tensor_or_other):
    if isinstance(tensor_or_other, Variable):
        return ptu.get_numpy(tensor_or_other)
    else:
        return tensor_or_other

def id_to_onehot(id, n_classes):
    """

    :param id: arr/tensor of size (n, 1)
    :param n_classes: int
    :return: one hot vector of size
    """
    one_hot = zeros((id.shape[0], n_classes))
    one_hot[torch.arange(one_hot.shape[0]), id[:, 0]] = 1
    return one_hot

def list_from_numpy(li):
    """convert all elements in input list to torch"""
    return [from_numpy(element) for element in li]

def FloatTensor(*args, **kwargs):
    return torch.FloatTensor(*args, **kwargs).to(device)

def from_numpy(*args, **kwargs):
    return torch.from_numpy(*args, **kwargs).float().to(device)

def get_numpy(tensor):
    return tensor.to('cpu').detach().numpy()

def zeros(*sizes, **kwargs):
    return torch.zeros(*sizes, **kwargs).to(device)

def zeros_like(*args, **kwargs):
    return torch.zeros_like(*args, **kwargs).to(device)

def ones_like(*args, **kwargs):
    return torch.ones_like(*args, **kwargs).to(device)

class Learner:

    def __init__(self, env_args, train_args, eval_args, policy_args, seed, **kwargs):
        self.seed = seed
        self.init_env(**env_args)
        self.init_agent(**policy_args)
        self.init_train(**train_args)
        self.init_eval(**eval_args)

    def init_env(self, env_type, env_name, max_rollouts_per_task=None, num_tasks=None, num_train_tasks=None, num_eval_tasks=None, eval_envs=None, worst_percentile=None, **kwargs):
        assert env_type in ['meta', 'pomdp', 'credit', 'rmdp', 'generalize', 'atari']
        self.env_type = env_type
        if self.env_type == 'meta':
            from envs.meta.make_env import make_env
            self.train_env = make_env(env_name, max_rollouts_per_task, seed=self.seed, n_tasks=num_tasks, **kwargs)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            if self.train_env.n_tasks is not None:
                assert num_train_tasks >= num_eval_tasks > 0
                shuffled_tasks = np.random.permutation(self.train_env.unwrapped.get_all_task_idx())
                self.train_tasks = shuffled_tasks[:num_train_tasks]
                self.eval_tasks = shuffled_tasks[-num_eval_tasks:]
            else:
                assert num_tasks == num_train_tasks == None
                assert num_eval_tasks > 0
                self.train_tasks = []
                self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = max_rollouts_per_task
            self.max_trajectory_len = self.train_env.horizon_bamdp
        elif self.env_type in ['pomdp', 'credit']:
            import envs.pomdp
            import envs.credit_assign
            assert num_eval_tasks > 0
            self.train_env = gym.make(env_name)
            self.train_env.seed(self.seed)
            self.train_env.action_space.np_random.seed(self.seed)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            self.train_tasks = []
            self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        elif self.env_type == 'atari':
            from envs.atari import create_env
            assert num_eval_tasks > 0
            self.train_env = create_env(env_name)
            self.train_env.seed(self.seed)
            self.train_env.action_space.np_random.seed(self.seed)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            self.train_tasks = []
            self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        elif self.env_type == 'rmdp':
            sys.path.append('envs/rl-generalization')
            import sunblaze_envs
            assert num_eval_tasks > 0 and worst_percentile > 0.0 and (worst_percentile < 1.0)
            self.train_env = sunblaze_envs.make(env_name, **kwargs)
            self.train_env.seed(self.seed)
            assert np.all(self.train_env.action_space.low == -1)
            assert np.all(self.train_env.action_space.high == 1)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            self.worst_percentile = worst_percentile
            self.train_tasks = []
            self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        elif self.env_type == 'generalize':
            sys.path.append('envs/rl-generalization')
            import sunblaze_envs
            self.train_env = sunblaze_envs.make(env_name, **kwargs)
            self.train_env.seed(self.seed)
            assert np.all(self.train_env.action_space.low == -1)
            assert np.all(self.train_env.action_space.high == 1)

            def check_env_class(env_name):
                if 'Normal' in env_name:
                    return 'R'
                if 'Extreme' in env_name:
                    return 'E'
                return 'D'
            self.train_env_name = check_env_class(env_name)
            self.eval_envs = {}
            for env_name, num_eval_task in eval_envs.items():
                eval_env = sunblaze_envs.make(env_name, **kwargs)
                eval_env.seed(self.seed + 1)
                self.eval_envs[eval_env] = (check_env_class(env_name), num_eval_task)
            logger.log(self.train_env_name, self.train_env)
            logger.log(self.eval_envs)
            self.train_tasks = []
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        else:
            raise ValueError
        if self.train_env.action_space.__class__.__name__ == 'Box':
            self.act_dim = self.train_env.action_space.shape[0]
            self.act_continuous = True
        else:
            assert self.train_env.action_space.__class__.__name__ == 'Discrete'
            self.act_dim = self.train_env.action_space.n
            self.act_continuous = False
        self.obs_dim = self.train_env.observation_space.shape[0]
        logger.log('obs_dim', self.obs_dim, 'act_dim', self.act_dim)

    def init_agent(self, seq_model, separate: bool=True, image_encoder=None, reward_clip=False, **kwargs):
        if seq_model == 'mlp':
            agent_class = AGENT_CLASSES['Policy_MLP']
            rnn_encoder_type = None
            assert separate == True
        elif '-mlp' in seq_model:
            agent_class = AGENT_CLASSES['Policy_RNN_MLP']
            rnn_encoder_type = seq_model.split('-')[0]
            assert separate == True
        else:
            rnn_encoder_type = seq_model
            if separate == True:
                agent_class = AGENT_CLASSES['Policy_Separate_RNN']
            else:
                agent_class = AGENT_CLASSES['Policy_Shared_RNN']
        self.agent_arch = agent_class.ARCH
        logger.log(agent_class, self.agent_arch)
        if image_encoder is not None:
            image_encoder_fn = lambda: ImageEncoder(image_shape=self.train_env.image_space.shape, **image_encoder)
        else:
            image_encoder_fn = lambda: None
        self.agent = agent_class(encoder=rnn_encoder_type, obs_dim=self.obs_dim, action_dim=self.act_dim, image_encoder_fn=image_encoder_fn, **kwargs).to(ptu.device)
        logger.log(self.agent)
        self.reward_clip = reward_clip

    def init_train(self, buffer_size, batch_size, num_iters, num_init_rollouts_pool, num_rollouts_per_iter, num_updates_per_iter=None, sampled_seq_len=None, sample_weight_baseline=None, buffer_type=None, **kwargs):
        if num_updates_per_iter is None:
            num_updates_per_iter = 1.0
        assert isinstance(num_updates_per_iter, int) or isinstance(num_updates_per_iter, float)
        self.num_updates_per_iter = num_updates_per_iter
        if self.agent_arch == AGENT_ARCHS.Markov:
            self.policy_storage = SimpleReplayBuffer(max_replay_buffer_size=int(buffer_size), observation_dim=self.obs_dim, action_dim=self.act_dim if self.act_continuous else 1, max_trajectory_len=self.max_trajectory_len, add_timeout=False)
        else:
            if sampled_seq_len == -1:
                sampled_seq_len = self.max_trajectory_len
            if buffer_type is None or buffer_type == SeqReplayBuffer.buffer_type:
                buffer_class = SeqReplayBuffer
            elif buffer_type == RAMEfficient_SeqReplayBuffer.buffer_type:
                buffer_class = RAMEfficient_SeqReplayBuffer
            logger.log(buffer_class)
            self.policy_storage = buffer_class(max_replay_buffer_size=int(buffer_size), observation_dim=self.obs_dim, action_dim=self.act_dim if self.act_continuous else 1, sampled_seq_len=sampled_seq_len, sample_weight_baseline=sample_weight_baseline, observation_type=self.train_env.observation_space.dtype)
        self.batch_size = batch_size
        self.num_iters = num_iters
        self.num_init_rollouts_pool = num_init_rollouts_pool
        self.num_rollouts_per_iter = num_rollouts_per_iter
        total_rollouts = num_init_rollouts_pool + num_iters * num_rollouts_per_iter
        self.n_env_steps_total = self.max_trajectory_len * total_rollouts
        logger.log('*** total rollouts', total_rollouts, 'total env steps', self.n_env_steps_total)

    def init_eval(self, log_interval, save_interval, log_tensorboard, eval_stochastic=False, num_episodes_per_task=1, **kwargs):
        self.log_interval = log_interval
        self.save_interval = save_interval
        self.log_tensorboard = log_tensorboard
        self.eval_stochastic = eval_stochastic
        self.eval_num_episodes_per_task = num_episodes_per_task

    def _start_training(self):
        self._n_env_steps_total = 0
        self._n_env_steps_total_last = 0
        self._n_rl_update_steps_total = 0
        self._n_rollouts_total = 0
        self._successes_in_buffer = 0
        self._start_time = time.time()
        self._start_time_last = time.time()

    def train(self):
        """
        training loop
        """
        self._start_training()
        if self.num_init_rollouts_pool > 0:
            logger.log('Collecting initial pool of data..')
            while self._n_env_steps_total < self.num_init_rollouts_pool * self.max_trajectory_len:
                self.collect_rollouts(num_rollouts=1, random_actions=True)
            logger.log('Done! env steps', self._n_env_steps_total, 'rollouts', self._n_rollouts_total)
            if isinstance(self.num_updates_per_iter, float):
                train_stats = self.update(int(self._n_env_steps_total * self.num_updates_per_iter))
                self.log_train_stats(train_stats)
        last_eval_num_iters = 0
        while self._n_env_steps_total < self.n_env_steps_total:
            env_steps = self.collect_rollouts(num_rollouts=self.num_rollouts_per_iter)
            logger.log('env steps', self._n_env_steps_total)
            train_stats = self.update(self.num_updates_per_iter if isinstance(self.num_updates_per_iter, int) else int(math.ceil(self.num_updates_per_iter * env_steps)))
            self.log_train_stats(train_stats)
            current_num_iters = self._n_env_steps_total // (self.num_rollouts_per_iter * self.max_trajectory_len)
            if current_num_iters != last_eval_num_iters and current_num_iters % self.log_interval == 0:
                last_eval_num_iters = current_num_iters
                perf = self.log()
                if self.save_interval > 0 and self._n_env_steps_total > 0.75 * self.n_env_steps_total and (current_num_iters % self.save_interval == 0):
                    self.save_model(current_num_iters, perf)
        self.save_model(current_num_iters, perf)

    @torch.no_grad()
    def collect_rollouts(self, num_rollouts, random_actions=False):
        """collect num_rollouts of trajectories in task and save into policy buffer
        :param random_actions: whether to use policy to sample actions, or randomly sample action space
        """
        before_env_steps = self._n_env_steps_total
        for idx in range(num_rollouts):
            steps = 0
            if self.env_type == 'meta' and self.train_env.n_tasks is not None:
                task = self.train_tasks[np.random.randint(len(self.train_tasks))]
                obs = ptu.from_numpy(self.train_env.reset(task=task))
            else:
                obs = ptu.from_numpy(self.train_env.reset())
            obs = obs.reshape(1, obs.shape[-1])
            done_rollout = False
            if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
                obs_list, act_list, rew_list, next_obs_list, term_list = ([], [], [], [], [])
            if self.agent_arch == AGENT_ARCHS.Memory:
                action, reward, internal_state = self.agent.get_initial_info()
            while not done_rollout:
                if random_actions:
                    action = ptu.FloatTensor([self.train_env.action_space.sample()])
                    if not self.act_continuous:
                        action = F.one_hot(action.long(), num_classes=self.act_dim).float()
                elif self.agent_arch == AGENT_ARCHS.Memory:
                    (action, _, _, _), internal_state = self.agent.act(prev_internal_state=internal_state, prev_action=action, reward=reward, obs=obs, deterministic=False)
                else:
                    action, _, _, _ = self.agent.act(obs, deterministic=False)
                next_obs, reward, done, info = utl.env_step(self.train_env, action.squeeze(dim=0))
                if self.reward_clip and self.env_type == 'atari':
                    reward = torch.tanh(reward)
                done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
                steps += 1
                if self.env_type == 'meta' and 'is_goal_state' in dir(self.train_env.unwrapped):
                    term = self.train_env.unwrapped.is_goal_state()
                    self._successes_in_buffer += int(term)
                elif self.env_type == 'credit':
                    term = done_rollout
                else:
                    term = False if 'TimeLimit.truncated' in info or steps >= self.max_trajectory_len else done_rollout
                if self.agent_arch == AGENT_ARCHS.Markov:
                    self.policy_storage.add_sample(observation=ptu.get_numpy(obs.squeeze(dim=0)), action=ptu.get_numpy(action.squeeze(dim=0) if self.act_continuous else torch.argmax(action.squeeze(dim=0), dim=-1, keepdims=True)), reward=ptu.get_numpy(reward.squeeze(dim=0)), terminal=np.array([term], dtype=float), next_observation=ptu.get_numpy(next_obs.squeeze(dim=0)))
                else:
                    obs_list.append(obs)
                    act_list.append(action)
                    rew_list.append(reward)
                    term_list.append(term)
                    next_obs_list.append(next_obs)
                obs = next_obs.clone()
            if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
                act_buffer = torch.cat(act_list, dim=0)
                if not self.act_continuous:
                    act_buffer = torch.argmax(act_buffer, dim=-1, keepdims=True)
                self.policy_storage.add_episode(observations=ptu.get_numpy(torch.cat(obs_list, dim=0)), actions=ptu.get_numpy(act_buffer), rewards=ptu.get_numpy(torch.cat(rew_list, dim=0)), terminals=np.array(term_list).reshape(-1, 1), next_observations=ptu.get_numpy(torch.cat(next_obs_list, dim=0)))
                print(f'steps: {steps} term: {term} ret: {torch.cat(rew_list, dim=0).sum().item():.2f}')
            self._n_env_steps_total += steps
            self._n_rollouts_total += 1
        return self._n_env_steps_total - before_env_steps

    def sample_rl_batch(self, batch_size):
        """sample batch of episodes for vae training"""
        if self.agent_arch == AGENT_ARCHS.Markov:
            batch = self.policy_storage.random_batch(batch_size)
        else:
            batch = self.policy_storage.random_episodes(batch_size)
        return ptu.np_to_pytorch_batch(batch)

    def update(self, num_updates):
        rl_losses_agg = {}
        for update in range(num_updates):
            batch = self.sample_rl_batch(self.batch_size)
            rl_losses = self.agent.update(batch)
            for k, v in rl_losses.items():
                if update == 0:
                    rl_losses_agg[k] = [v]
                else:
                    rl_losses_agg[k].append(v)
        for k in rl_losses_agg:
            rl_losses_agg[k] = np.mean(rl_losses_agg[k])
        self._n_rl_update_steps_total += num_updates
        return rl_losses_agg

    @torch.no_grad()
    def evaluate(self, tasks, deterministic=True):
        num_episodes = self.max_rollouts_per_task
        returns_per_episode = np.zeros((len(tasks), num_episodes))
        success_rate = np.zeros(len(tasks))
        total_steps = np.zeros(len(tasks))
        if self.env_type == 'meta':
            num_steps_per_episode = self.eval_env.unwrapped._max_episode_steps
            obs_size = self.eval_env.unwrapped.observation_space.shape[0]
            observations = np.zeros((len(tasks), self.max_trajectory_len + 1, obs_size))
        else:
            num_steps_per_episode = self.eval_env._max_episode_steps
            observations = None
        for task_idx, task in enumerate(tasks):
            step = 0
            if self.env_type == 'meta' and self.eval_env.n_tasks is not None:
                obs = ptu.from_numpy(self.eval_env.reset(task=task))
                observations[task_idx, step, :] = ptu.get_numpy(obs[:obs_size])
            else:
                obs = ptu.from_numpy(self.eval_env.reset())
            obs = obs.reshape(1, obs.shape[-1])
            if self.agent_arch == AGENT_ARCHS.Memory:
                action, reward, internal_state = self.agent.get_initial_info()
            for episode_idx in range(num_episodes):
                running_reward = 0.0
                for _ in range(num_steps_per_episode):
                    if self.agent_arch == AGENT_ARCHS.Memory:
                        (action, _, _, _), internal_state = self.agent.act(prev_internal_state=internal_state, prev_action=action, reward=reward, obs=obs, deterministic=deterministic)
                    else:
                        action, _, _, _ = self.agent.act(obs, deterministic=deterministic)
                    next_obs, reward, done, info = utl.env_step(self.eval_env, action.squeeze(dim=0))
                    running_reward += reward.item()
                    if self.reward_clip and self.env_type == 'atari':
                        reward = torch.tanh(reward)
                    step += 1
                    done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
                    if self.env_type == 'meta':
                        observations[task_idx, step, :] = ptu.get_numpy(next_obs[0, :obs_size])
                    obs = next_obs.clone()
                    if self.env_type == 'meta' and 'is_goal_state' in dir(self.eval_env.unwrapped) and self.eval_env.unwrapped.is_goal_state():
                        success_rate[task_idx] = 1.0
                    elif self.env_type == 'generalize' and self.eval_env.unwrapped.is_success():
                        success_rate[task_idx] = 1.0
                    elif 'success' in info and info['success'] == True:
                        success_rate[task_idx] = 1.0
                    if done_rollout:
                        break
                    if self.env_type == 'meta' and info['done_mdp'] == True:
                        break
                returns_per_episode[task_idx, episode_idx] = running_reward
            total_steps[task_idx] = step
        return (returns_per_episode, success_rate, observations, total_steps)

    def log_train_stats(self, train_stats):
        logger.record_step(self._n_env_steps_total)
        for k, v in train_stats.items():
            logger.record_tabular('rl_loss/' + k, v)
        if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
            results = self.agent.report_grad_norm()
            for k, v in results.items():
                logger.record_tabular('rl_loss/' + k, v)
        logger.dump_tabular()

    def log(self):
        logger.record_step(self._n_env_steps_total)
        logger.record_tabular('z/env_steps', self._n_env_steps_total)
        logger.record_tabular('z/rollouts', self._n_rollouts_total)
        logger.record_tabular('z/rl_steps', self._n_rl_update_steps_total)
        if self.env_type == 'meta':
            if self.train_env.n_tasks is not None:
                returns_train, success_rate_train, observations, total_steps_train = self.evaluate(self.train_tasks[:len(self.eval_tasks)])
            returns_eval, success_rate_eval, observations_eval, total_steps_eval = self.evaluate(self.eval_tasks)
            if self.eval_stochastic:
                returns_eval_sto, success_rate_eval_sto, observations_eval_sto, total_steps_eval_sto = self.evaluate(self.eval_tasks, deterministic=False)
            if self.train_env.n_tasks is not None and 'plot_behavior' in dir(self.eval_env.unwrapped):
                for i, task in enumerate(self.train_tasks[:min(5, len(self.eval_tasks))]):
                    self.eval_env.reset(task=task)
                    logger.add_figure('trajectory/train_task_{}'.format(i), utl_eval.plot_rollouts(observations[i, :], self.eval_env))
                for i, task in enumerate(self.eval_tasks[:min(5, len(self.eval_tasks))]):
                    self.eval_env.reset(task=task)
                    logger.add_figure('trajectory/eval_task_{}'.format(i), utl_eval.plot_rollouts(observations_eval[i, :], self.eval_env))
                    if self.eval_stochastic:
                        logger.add_figure('trajectory/eval_task_{}_sto'.format(i), utl_eval.plot_rollouts(observations_eval_sto[i, :], self.eval_env))
            if 'is_goal_state' in dir(self.eval_env.unwrapped):
                logger.record_tabular('metrics/successes_in_buffer', self._successes_in_buffer / self._n_env_steps_total)
                if self.train_env.n_tasks is not None:
                    logger.record_tabular('metrics/success_rate_train', np.mean(success_rate_train))
                logger.record_tabular('metrics/success_rate_eval', np.mean(success_rate_eval))
                if self.eval_stochastic:
                    logger.record_tabular('metrics/success_rate_eval_sto', np.mean(success_rate_eval_sto))
            for episode_idx in range(self.max_rollouts_per_task):
                if self.train_env.n_tasks is not None:
                    logger.record_tabular('metrics/return_train_episode_{}'.format(episode_idx + 1), np.mean(returns_train[:, episode_idx]))
                logger.record_tabular('metrics/return_eval_episode_{}'.format(episode_idx + 1), np.mean(returns_eval[:, episode_idx]))
                if self.eval_stochastic:
                    logger.record_tabular('metrics/return_eval_episode_{}_sto'.format(episode_idx + 1), np.mean(returns_eval_sto[:, episode_idx]))
            if self.train_env.n_tasks is not None:
                logger.record_tabular('metrics/total_steps_train', np.mean(total_steps_train))
                logger.record_tabular('metrics/return_train_total', np.mean(np.sum(returns_train, axis=-1)))
            logger.record_tabular('metrics/total_steps_eval', np.mean(total_steps_eval))
            logger.record_tabular('metrics/return_eval_total', np.mean(np.sum(returns_eval, axis=-1)))
            if self.eval_stochastic:
                logger.record_tabular('metrics/total_steps_eval_sto', np.mean(total_steps_eval_sto))
                logger.record_tabular('metrics/return_eval_total_sto', np.mean(np.sum(returns_eval_sto, axis=-1)))
        elif self.env_type == 'generalize':
            returns_eval, success_rate_eval, total_steps_eval = ({}, {}, {})
            for env, (env_name, eval_num_episodes_per_task) in self.eval_envs.items():
                self.eval_env = env
                for suffix, deterministic in zip(['', '_sto'], [True, False]):
                    if deterministic == False and self.eval_stochastic == False:
                        continue
                    return_eval, success_eval, _, total_step_eval = self.evaluate(eval_num_episodes_per_task * [None], deterministic=deterministic)
                    returns_eval[self.train_env_name + env_name + suffix] = return_eval.squeeze(-1)
                    success_rate_eval[self.train_env_name + env_name + suffix] = success_eval
                    total_steps_eval[self.train_env_name + env_name + suffix] = total_step_eval
            for k, v in returns_eval.items():
                logger.record_tabular(f'metrics/return_eval_{k}', np.mean(v))
            for k, v in success_rate_eval.items():
                logger.record_tabular(f'metrics/succ_eval_{k}', np.mean(v))
            for k, v in total_steps_eval.items():
                logger.record_tabular(f'metrics/total_steps_eval_{k}', np.mean(v))
        elif self.env_type == 'rmdp':
            returns_eval, _, _, total_steps_eval = self.evaluate(self.eval_tasks)
            returns_eval = returns_eval.squeeze(-1)
            cutoff = np.percentile(returns_eval, 100 * self.worst_percentile)
            worst_indices = np.where(returns_eval <= cutoff)
            returns_eval_worst, total_steps_eval_worst = (returns_eval[worst_indices], total_steps_eval[worst_indices])
            logger.record_tabular('metrics/return_eval_avg', returns_eval.mean())
            logger.record_tabular('metrics/return_eval_worst', returns_eval_worst.mean())
            logger.record_tabular('metrics/total_steps_eval_avg', total_steps_eval.mean())
            logger.record_tabular('metrics/total_steps_eval_worst', total_steps_eval_worst.mean())
        elif self.env_type in ['pomdp', 'credit', 'atari']:
            returns_eval, success_rate_eval, _, total_steps_eval = self.evaluate(self.eval_tasks)
            if self.eval_stochastic:
                returns_eval_sto, success_rate_eval_sto, _, total_steps_eval_sto = self.evaluate(self.eval_tasks, deterministic=False)
            logger.record_tabular('metrics/total_steps_eval', np.mean(total_steps_eval))
            logger.record_tabular('metrics/return_eval_total', np.mean(np.sum(returns_eval, axis=-1)))
            logger.record_tabular('metrics/success_rate_eval', np.mean(success_rate_eval))
            if self.eval_stochastic:
                logger.record_tabular('metrics/total_steps_eval_sto', np.mean(total_steps_eval_sto))
                logger.record_tabular('metrics/return_eval_total_sto', np.mean(np.sum(returns_eval_sto, axis=-1)))
                logger.record_tabular('metrics/success_rate_eval_sto', np.mean(success_rate_eval_sto))
        else:
            raise ValueError
        logger.record_tabular('z/time_cost', int(time.time() - self._start_time))
        logger.record_tabular('z/fps', (self._n_env_steps_total - self._n_env_steps_total_last) / (time.time() - self._start_time_last))
        self._n_env_steps_total_last = self._n_env_steps_total
        self._start_time_last = time.time()
        logger.dump_tabular()
        if self.env_type == 'generalize':
            return sum([v.mean() for v in success_rate_eval.values()]) / len(success_rate_eval)
        else:
            return np.mean(np.sum(returns_eval, axis=-1))

    def save_model(self, iter, perf):
        save_path = os.path.join(logger.get_dir(), 'save', f'agent_{iter}_perf{perf:.3f}.pt')
        torch.save(self.agent.state_dict(), save_path)

    def load_model(self, ckpt_path):
        self.agent.load_state_dict(torch.load(ckpt_path, map_location=ptu.device))
        print('load successfully from', ckpt_path)

@torch.no_grad()
def collect_rollouts(self, num_rollouts, random_actions=False):
    """collect num_rollouts of trajectories in task and save into policy buffer
        :param random_actions: whether to use policy to sample actions, or randomly sample action space
        """
    before_env_steps = self._n_env_steps_total
    for idx in range(num_rollouts):
        steps = 0
        if self.env_type == 'meta' and self.train_env.n_tasks is not None:
            task = self.train_tasks[np.random.randint(len(self.train_tasks))]
            obs = ptu.from_numpy(self.train_env.reset(task=task))
        else:
            obs = ptu.from_numpy(self.train_env.reset())
        obs = obs.reshape(1, obs.shape[-1])
        done_rollout = False
        if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
            obs_list, act_list, rew_list, next_obs_list, term_list = ([], [], [], [], [])
        if self.agent_arch == AGENT_ARCHS.Memory:
            action, reward, internal_state = self.agent.get_initial_info()
        while not done_rollout:
            if random_actions:
                action = ptu.FloatTensor([self.train_env.action_space.sample()])
                if not self.act_continuous:
                    action = F.one_hot(action.long(), num_classes=self.act_dim).float()
            elif self.agent_arch == AGENT_ARCHS.Memory:
                (action, _, _, _), internal_state = self.agent.act(prev_internal_state=internal_state, prev_action=action, reward=reward, obs=obs, deterministic=False)
            else:
                action, _, _, _ = self.agent.act(obs, deterministic=False)
            next_obs, reward, done, info = utl.env_step(self.train_env, action.squeeze(dim=0))
            if self.reward_clip and self.env_type == 'atari':
                reward = torch.tanh(reward)
            done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
            steps += 1
            if self.env_type == 'meta' and 'is_goal_state' in dir(self.train_env.unwrapped):
                term = self.train_env.unwrapped.is_goal_state()
                self._successes_in_buffer += int(term)
            elif self.env_type == 'credit':
                term = done_rollout
            else:
                term = False if 'TimeLimit.truncated' in info or steps >= self.max_trajectory_len else done_rollout
            if self.agent_arch == AGENT_ARCHS.Markov:
                self.policy_storage.add_sample(observation=ptu.get_numpy(obs.squeeze(dim=0)), action=ptu.get_numpy(action.squeeze(dim=0) if self.act_continuous else torch.argmax(action.squeeze(dim=0), dim=-1, keepdims=True)), reward=ptu.get_numpy(reward.squeeze(dim=0)), terminal=np.array([term], dtype=float), next_observation=ptu.get_numpy(next_obs.squeeze(dim=0)))
            else:
                obs_list.append(obs)
                act_list.append(action)
                rew_list.append(reward)
                term_list.append(term)
                next_obs_list.append(next_obs)
            obs = next_obs.clone()
        if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
            act_buffer = torch.cat(act_list, dim=0)
            if not self.act_continuous:
                act_buffer = torch.argmax(act_buffer, dim=-1, keepdims=True)
            self.policy_storage.add_episode(observations=ptu.get_numpy(torch.cat(obs_list, dim=0)), actions=ptu.get_numpy(act_buffer), rewards=ptu.get_numpy(torch.cat(rew_list, dim=0)), terminals=np.array(term_list).reshape(-1, 1), next_observations=ptu.get_numpy(torch.cat(next_obs_list, dim=0)))
            print(f'steps: {steps} term: {term} ret: {torch.cat(rew_list, dim=0).sum().item():.2f}')
        self._n_env_steps_total += steps
        self._n_rollouts_total += 1
    return self._n_env_steps_total - before_env_steps

@torch.no_grad()
def evaluate(self, tasks, deterministic=True):
    num_episodes = self.max_rollouts_per_task
    returns_per_episode = np.zeros((len(tasks), num_episodes))
    success_rate = np.zeros(len(tasks))
    total_steps = np.zeros(len(tasks))
    if self.env_type == 'meta':
        num_steps_per_episode = self.eval_env.unwrapped._max_episode_steps
        obs_size = self.eval_env.unwrapped.observation_space.shape[0]
        observations = np.zeros((len(tasks), self.max_trajectory_len + 1, obs_size))
    else:
        num_steps_per_episode = self.eval_env._max_episode_steps
        observations = None
    for task_idx, task in enumerate(tasks):
        step = 0
        if self.env_type == 'meta' and self.eval_env.n_tasks is not None:
            obs = ptu.from_numpy(self.eval_env.reset(task=task))
            observations[task_idx, step, :] = ptu.get_numpy(obs[:obs_size])
        else:
            obs = ptu.from_numpy(self.eval_env.reset())
        obs = obs.reshape(1, obs.shape[-1])
        if self.agent_arch == AGENT_ARCHS.Memory:
            action, reward, internal_state = self.agent.get_initial_info()
        for episode_idx in range(num_episodes):
            running_reward = 0.0
            for _ in range(num_steps_per_episode):
                if self.agent_arch == AGENT_ARCHS.Memory:
                    (action, _, _, _), internal_state = self.agent.act(prev_internal_state=internal_state, prev_action=action, reward=reward, obs=obs, deterministic=deterministic)
                else:
                    action, _, _, _ = self.agent.act(obs, deterministic=deterministic)
                next_obs, reward, done, info = utl.env_step(self.eval_env, action.squeeze(dim=0))
                running_reward += reward.item()
                if self.reward_clip and self.env_type == 'atari':
                    reward = torch.tanh(reward)
                step += 1
                done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
                if self.env_type == 'meta':
                    observations[task_idx, step, :] = ptu.get_numpy(next_obs[0, :obs_size])
                obs = next_obs.clone()
                if self.env_type == 'meta' and 'is_goal_state' in dir(self.eval_env.unwrapped) and self.eval_env.unwrapped.is_goal_state():
                    success_rate[task_idx] = 1.0
                elif self.env_type == 'generalize' and self.eval_env.unwrapped.is_success():
                    success_rate[task_idx] = 1.0
                elif 'success' in info and info['success'] == True:
                    success_rate[task_idx] = 1.0
                if done_rollout:
                    break
                if self.env_type == 'meta' and info['done_mdp'] == True:
                    break
            returns_per_episode[task_idx, episode_idx] = running_reward
        total_steps[task_idx] = step
    return (returns_per_episode, success_rate, observations, total_steps)

class MarkovPolicyBase(Mlp):

    def __init__(self, obs_dim, action_dim, hidden_sizes, init_w=0.001, image_encoder=None, **kwargs):
        self.save_init_params(locals())
        self.action_dim = action_dim
        if image_encoder is None:
            self.input_size = obs_dim
        else:
            self.input_size = image_encoder.embed_size
        super().__init__(hidden_sizes, input_size=self.input_size, output_size=self.action_dim, init_w=init_w, **kwargs)
        self.image_encoder = image_encoder

    def forward(self, obs):
        """
        :param obs: Observation, usually 2D (B, dim), but maybe 3D (T, B, dim)
        return action (*, dim)
        """
        x = self.preprocess(obs)
        return super().forward(x)

    def preprocess(self, obs):
        x = obs
        if self.image_encoder is not None:
            x = self.image_encoder(x)
        return x

def preprocess(self, obs):
    x = obs
    if self.image_encoder is not None:
        x = self.image_encoder(x)
    return x

class DeterministicPolicy(MarkovPolicyBase):
    """
    Usage: TD3
    ```
    policy = DeterministicPolicy(...)
    action = policy(obs)
    ```
    NOTE: action space must be [-1,1]^d
    """

    def forward(self, obs):
        h = super().forward(obs)
        action = torch.tanh(h)
        return action

def forward(self, obs):
    h = super().forward(obs)
    action = torch.tanh(h)
    return action

class CategoricalPolicy(MarkovPolicyBase):
    """Based on https://github.com/ku2482/sac-discrete.pytorch/blob/master/sacd/model.py
    Usage: SAC-discrete
    ```
    policy = CategoricalPolicy(...)
    action, _, _ = policy(obs, deterministic=True)
    action, _, _ = policy(obs, deterministic=False)
    action, prob, log_prob = policy(obs, deterministic=False, return_log_prob=True)
    ```
    NOTE: action space must be discrete
    """

    def forward(self, obs, deterministic=False, return_log_prob=False):
        """
        :param obs: Observation, usually 2D (B, dim), but maybe 3D (T, B, dim)
        :param deterministic: If True, do not sample
        :param return_log_prob: If True, return a sample and its log probability
        return: action (*, B, A), prob (*, B, A), log_prob (*, B, A)
        """
        action_logits = super().forward(obs)
        prob, log_prob = (None, None)
        if deterministic:
            action = torch.argmax(action_logits, dim=-1)
            assert return_log_prob == False
        else:
            prob = F.softmax(action_logits, dim=-1)
            distr = Categorical(prob)
            action = distr.sample()
            if return_log_prob:
                log_prob = torch.log(torch.clamp(prob, min=PROB_MIN))
        action = F.one_hot(action.long(), num_classes=self.action_dim).float()
        return (action, prob, log_prob)

def forward(self, obs, deterministic=False, return_log_prob=False):
    """
        :param obs: Observation, usually 2D (B, dim), but maybe 3D (T, B, dim)
        :param deterministic: If True, do not sample
        :param return_log_prob: If True, return a sample and its log probability
        return: action (*, B, A), prob (*, B, A), log_prob (*, B, A)
        """
    action_logits = super().forward(obs)
    prob, log_prob = (None, None)
    if deterministic:
        action = torch.argmax(action_logits, dim=-1)
        assert return_log_prob == False
    else:
        prob = F.softmax(action_logits, dim=-1)
        distr = Categorical(prob)
        action = distr.sample()
        if return_log_prob:
            log_prob = torch.log(torch.clamp(prob, min=PROB_MIN))
    action = F.one_hot(action.long(), num_classes=self.action_dim).float()
    return (action, prob, log_prob)

class ModelFreeOffPolicy_Shared_RNN(nn.Module):
    """
    Recurrent Actor and Recurrent Critic with shared RNN
    """
    ARCH = 'memory'

    def __init__(self, obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, lr=0.0003, gamma=0.99, tau=0.005, **kwargs):
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.algo = RL_ALGORITHMS[algo_name](**kwargs[algo_name], action_dim=action_dim)
        self.observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
        self.action_embedder = utl.FeatureExtractor(action_dim, action_embedding_size, F.relu)
        self.reward_embedder = utl.FeatureExtractor(1, reward_embedding_size, F.relu)
        rnn_input_size = action_embedding_size + observ_embedding_size + reward_embedding_size
        self.rnn_hidden_size = rnn_hidden_size
        assert encoder in [LSTM_name, GRU_name]
        self.encoder = encoder
        self.num_layers = 1
        self.rnn = RNNs[encoder](input_size=rnn_input_size, hidden_size=self.rnn_hidden_size, num_layers=self.num_layers, batch_first=False, bias=True)
        for name, param in self.rnn.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                nn.init.orthogonal_(param)
        self.current_observ_action_embedder = utl.FeatureExtractor(obs_dim + action_dim, rnn_input_size, F.relu)
        self.qf1, self.qf2 = self.algo.build_critic(input_size=self.rnn_hidden_size + rnn_input_size, hidden_sizes=dqn_layers, action_dim=action_dim)
        self.qf1_target = deepcopy(self.qf1)
        self.qf2_target = deepcopy(self.qf2)
        self.current_observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
        self.policy = self.algo.build_actor(input_size=self.rnn_hidden_size + observ_embedding_size, action_dim=self.action_dim, hidden_sizes=policy_layers)
        self.policy_target = deepcopy(self.policy)
        self.optimizer = Adam([*self.observ_embedder.parameters(), *self.action_embedder.parameters(), *self.reward_embedder.parameters(), *self.rnn.parameters(), *self.current_observ_action_embedder.parameters(), *self.current_observ_embedder.parameters(), *self.qf1.parameters(), *self.qf2.parameters(), *self.policy.parameters()], lr=lr)

    def get_hidden_states(self, prev_actions, rewards, observs, initial_internal_state=None):
        input_a = self.action_embedder(prev_actions)
        input_r = self.reward_embedder(rewards)
        input_s = self.observ_embedder(observs)
        inputs = torch.cat((input_a, input_r, input_s), dim=-1)
        if initial_internal_state is None:
            output, _ = self.rnn(inputs)
            return output
        else:
            output, current_internal_state = self.rnn(inputs, initial_internal_state)
            return (output, current_internal_state)

    def forward(self, actions, rewards, observs, dones, masks):
        """
        For actions a, rewards r, observs o, dones d: (T+1, B, dim)
                where for each t in [0, T], take action a[t], then receive reward r[t], done d[t], and next obs o[t]
                the hidden state h[t](, c[t]) = RNN(h[t-1](, c[t-1]), a[t], r[t], o[t])
                specially, a[0]=r[0]=d[0]=h[0]=c[0]=0.0, o[0] is the initial obs

        The loss is still on the Q value Q(h[t], a[t]) with real actions taken, i.e. t in [1, T]
                based on Masks (T, B, 1)
        """
        assert actions.dim() == rewards.dim() == dones.dim() == observs.dim() == masks.dim() == 3
        assert actions.shape[0] == rewards.shape[0] == dones.shape[0] == observs.shape[0] == masks.shape[0] + 1
        num_valid = torch.clamp(masks.sum(), min=1.0)
        hidden_states = self.get_hidden_states(prev_actions=actions, rewards=rewards, observs=observs)
        obs_embeds = self.current_observ_embedder(observs)
        joint_policy_embeds = torch.cat((hidden_states, obs_embeds), dim=-1)
        with torch.no_grad():
            new_next_actions, new_next_log_probs = self.algo.forward_actor_in_target(actor=self.policy, actor_target=self.policy_target, next_observ=joint_policy_embeds)
            obs_act_embeds = self.current_observ_action_embedder(torch.cat((observs, new_next_actions), dim=-1))
            joint_q_embeds = torch.cat((hidden_states, obs_act_embeds), dim=-1)
            next_q1 = self.qf1_target(joint_q_embeds)
            next_q2 = self.qf2_target(joint_q_embeds)
            min_next_q_target = torch.min(next_q1, next_q2)
            min_next_q_target += self.algo.entropy_bonus(new_next_log_probs)
            q_target = rewards + (1.0 - dones) * self.gamma * min_next_q_target
            q_target = q_target[1:]
        curr_obs_act_embeds = self.current_observ_action_embedder(torch.cat((observs[:-1], actions[1:]), dim=-1))
        curr_joint_q_embeds = torch.cat((hidden_states[:-1], curr_obs_act_embeds), dim=-1)
        q1_pred = self.qf1(curr_joint_q_embeds)
        q2_pred = self.qf2(curr_joint_q_embeds)
        q1_pred, q2_pred = (q1_pred * masks, q2_pred * masks)
        q_target = q_target * masks
        qf1_loss = ((q1_pred - q_target) ** 2).sum() / num_valid
        qf2_loss = ((q2_pred - q_target) ** 2).sum() / num_valid
        new_actions, new_log_probs = self.algo.forward_actor(actor=self.policy, observ=joint_policy_embeds)
        new_obs_act_embeds = self.current_observ_action_embedder(torch.cat((observs, new_actions), dim=-1))
        new_joint_q_embeds = torch.cat((hidden_states, new_obs_act_embeds), dim=-1)
        q1 = self.qf1(new_joint_q_embeds)
        q2 = self.qf2(new_joint_q_embeds)
        min_q_new_actions = torch.min(q1, q2)
        policy_loss = -min_q_new_actions
        policy_loss += -self.algo.entropy_bonus(new_log_probs)
        policy_loss = policy_loss[:-1]
        policy_loss = (policy_loss * masks).sum() / num_valid
        total_loss = 0.5 * (qf1_loss + qf2_loss) + policy_loss
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        outputs = {'qf1_loss': qf1_loss.item(), 'qf2_loss': qf2_loss.item(), 'policy_loss': policy_loss.item()}
        self.soft_target_update()
        if new_log_probs is not None:
            with torch.no_grad():
                current_log_probs = (new_log_probs[:-1] * masks).sum() / num_valid
                current_log_probs = current_log_probs.item()
            other_info = self.algo.update_others(current_log_probs)
            outputs.update(other_info)
        return outputs

    def soft_target_update(self):
        ptu.soft_update_from_to(self.qf1, self.qf1_target, self.tau)
        ptu.soft_update_from_to(self.qf2, self.qf2_target, self.tau)
        if self.algo.use_target_actor:
            ptu.soft_update_from_to(self.policy, self.policy_target, self.tau)

    def report_grad_norm(self):
        return {'rnn_grad_norm': utl.get_grad_norm(self.rnn), 'q_grad_norm': utl.get_grad_norm(self.qf1), 'pi_grad_norm': utl.get_grad_norm(self.policy)}

    def update(self, batch):
        actions, rewards, dones = (batch['act'], batch['rew'], batch['term'])
        _, batch_size, _ = actions.shape
        masks = batch['mask']
        obs, next_obs = (batch['obs'], batch['obs2'])
        observs = torch.cat((obs[[0]], next_obs), dim=0)
        actions = torch.cat((ptu.zeros((1, batch_size, self.action_dim)).float(), actions), dim=0)
        rewards = torch.cat((ptu.zeros((1, batch_size, 1)).float(), rewards), dim=0)
        dones = torch.cat((ptu.zeros((1, batch_size, 1)).float(), dones), dim=0)
        return self.forward(actions, rewards, observs, dones, masks)

    @torch.no_grad()
    def get_initial_info(self):
        prev_action = ptu.zeros((1, self.action_dim)).float()
        reward = ptu.zeros((1, 1)).float()
        hidden_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
        if self.encoder == GRU_name:
            internal_state = hidden_state
        else:
            cell_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
            internal_state = (hidden_state, cell_state)
        return (prev_action, reward, internal_state)

    @torch.no_grad()
    def act(self, prev_internal_state, prev_action, reward, obs, deterministic=False, return_log_prob=False):
        prev_action = prev_action.unsqueeze(0)
        reward = reward.unsqueeze(0)
        obs = obs.unsqueeze(0)
        hidden_state, current_internal_state = self.get_hidden_states(prev_actions=prev_action, rewards=reward, observs=obs, initial_internal_state=prev_internal_state)
        curr_embed = self.current_observ_embedder(obs)
        joint_embeds = torch.cat((hidden_state, curr_embed), dim=-1)
        if joint_embeds.dim() == 3:
            joint_embeds = joint_embeds.squeeze(0)
        action_tuple = self.algo.select_action(actor=self.policy, observ=joint_embeds, deterministic=deterministic, return_log_prob=return_log_prob)
        return (action_tuple, current_internal_state)

def get_hidden_states(self, prev_actions, rewards, observs, initial_internal_state=None):
    input_a = self.action_embedder(prev_actions)
    input_r = self.reward_embedder(rewards)
    input_s = self.observ_embedder(observs)
    inputs = torch.cat((input_a, input_r, input_s), dim=-1)
    if initial_internal_state is None:
        output, _ = self.rnn(inputs)
        return output
    else:
        output, current_internal_state = self.rnn(inputs, initial_internal_state)
        return (output, current_internal_state)

def update(self, batch):
    actions, rewards, dones = (batch['act'], batch['rew'], batch['term'])
    _, batch_size, _ = actions.shape
    masks = batch['mask']
    obs, next_obs = (batch['obs'], batch['obs2'])
    observs = torch.cat((obs[[0]], next_obs), dim=0)
    actions = torch.cat((ptu.zeros((1, batch_size, self.action_dim)).float(), actions), dim=0)
    rewards = torch.cat((ptu.zeros((1, batch_size, 1)).float(), rewards), dim=0)
    dones = torch.cat((ptu.zeros((1, batch_size, 1)).float(), dones), dim=0)
    return self.forward(actions, rewards, observs, dones, masks)

@torch.no_grad()
def get_initial_info(self):
    prev_action = ptu.zeros((1, self.action_dim)).float()
    reward = ptu.zeros((1, 1)).float()
    hidden_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
    if self.encoder == GRU_name:
        internal_state = hidden_state
    else:
        cell_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
        internal_state = (hidden_state, cell_state)
    return (prev_action, reward, internal_state)

@torch.no_grad()
def act(self, prev_internal_state, prev_action, reward, obs, deterministic=False, return_log_prob=False):
    prev_action = prev_action.unsqueeze(0)
    reward = reward.unsqueeze(0)
    obs = obs.unsqueeze(0)
    hidden_state, current_internal_state = self.get_hidden_states(prev_actions=prev_action, rewards=reward, observs=obs, initial_internal_state=prev_internal_state)
    curr_embed = self.current_observ_embedder(obs)
    joint_embeds = torch.cat((hidden_state, curr_embed), dim=-1)
    if joint_embeds.dim() == 3:
        joint_embeds = joint_embeds.squeeze(0)
    action_tuple = self.algo.select_action(actor=self.policy, observ=joint_embeds, deterministic=deterministic, return_log_prob=return_log_prob)
    return (action_tuple, current_internal_state)

class ModelFreeOffPolicy_RNN_MLP(ModelFreeOffPolicy_Separate_RNN):
    """
    Markov Actor and Recurrent Critic
    It may be more effective on some special cases of POMDPs,
        where the reward is history-dependent, but Markov actor
        is sufficient to solve the task.
    """
    ARCH = 'memory-markov'
    Markov_Actor = True
    Markov_Critic = False

    def __init__(self, obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers=1, lr=0.0003, gamma=0.99, tau=0.005, image_encoder_fn=lambda: None, **kwargs):
        super().__init__(obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers, lr, gamma, tau, image_encoder_fn, **kwargs)
        self.actor = self.algo.build_actor(input_size=obs_dim, action_dim=action_dim, hidden_sizes=policy_layers, image_encoder=image_encoder_fn())
        self.actor_optimizer = Adam(self.actor.parameters(), lr=lr)
        self.actor_target = deepcopy(self.actor)

    @torch.no_grad()
    def act(self, obs, deterministic=False, return_log_prob=False):
        return self.algo.select_action(actor=self.actor, observ=obs, deterministic=deterministic, return_log_prob=return_log_prob)

    def report_grad_norm(self):
        return {'q_grad_norm': utl.get_grad_norm(self.critic), 'q_rnn_grad_norm': utl.get_grad_norm(self.critic.rnn), 'pi_grad_norm': utl.get_grad_norm(self.actor)}

@torch.no_grad()
def act(self, obs, deterministic=False, return_log_prob=False):
    return self.algo.select_action(actor=self.actor, observ=obs, deterministic=deterministic, return_log_prob=return_log_prob)

class ModelFreeOffPolicy_MLP(nn.Module):
    """
    standard off-policy Markovian Policy using MLP
    including TD3 and SAC
    NOTE: it can only solve MDP problem, not POMDPs
    """
    ARCH = 'markov'
    Markov_Actor = True
    Markov_Critic = True

    def __init__(self, obs_dim, action_dim, algo_name, dqn_layers, policy_layers, lr=0.0003, gamma=0.99, tau=0.005, **kwargs):
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.algo = RL_ALGORITHMS[algo_name](**kwargs[algo_name], action_dim=action_dim)
        self.qf1, self.qf2 = self.algo.build_critic(obs_dim=obs_dim, hidden_sizes=dqn_layers, action_dim=action_dim)
        self.qf1_optim = Adam(self.qf1.parameters(), lr=lr)
        self.qf2_optim = Adam(self.qf2.parameters(), lr=lr)
        self.qf1_target = copy.deepcopy(self.qf1)
        self.qf2_target = copy.deepcopy(self.qf2)
        self.policy = self.algo.build_actor(input_size=obs_dim, action_dim=action_dim, hidden_sizes=policy_layers)
        self.policy_optim = Adam(self.policy.parameters(), lr=lr)
        self.policy_target = copy.deepcopy(self.policy)

    @torch.no_grad()
    def act(self, obs, deterministic=False, return_log_prob=False):
        return self.algo.select_action(actor=self.policy, observ=obs, deterministic=deterministic, return_log_prob=return_log_prob)

    def update(self, batch):
        observs, next_observs = (batch['obs'], batch['obs2'])
        actions, rewards, dones = (batch['act'], batch['rew'], batch['term'])
        (q1_pred, q2_pred), q_target = self.algo.critic_loss(markov_actor=self.Markov_Actor, markov_critic=self.Markov_Critic, actor=self.policy, actor_target=self.policy_target, critic=(self.qf1, self.qf2), critic_target=(self.qf1_target, self.qf2_target), observs=observs, actions=actions, rewards=rewards, dones=dones, gamma=self.gamma, next_observs=next_observs)
        qf1_loss = F.mse_loss(q1_pred, q_target)
        qf2_loss = F.mse_loss(q2_pred, q_target)
        self.qf1_optim.zero_grad()
        self.qf2_optim.zero_grad()
        qf1_loss.backward()
        qf2_loss.backward()
        self.qf1_optim.step()
        self.qf2_optim.step()
        self.soft_target_update()
        policy_loss, log_probs = self.algo.actor_loss(markov_actor=self.Markov_Actor, markov_critic=self.Markov_Critic, actor=self.policy, actor_target=self.policy_target, critic=(self.qf1, self.qf2), critic_target=(self.qf1_target, self.qf2_target), observs=observs)
        policy_loss = policy_loss.mean()
        self.policy_optim.zero_grad()
        policy_loss.backward()
        self.policy_optim.step()
        outputs = {'qf1_loss': qf1_loss.item(), 'qf2_loss': qf2_loss.item(), 'policy_loss': policy_loss.item()}
        if log_probs is not None:
            current_log_probs = log_probs.mean().item()
            other_info = self.algo.update_others(current_log_probs)
            outputs.update(other_info)
        return outputs

    def soft_target_update(self):
        ptu.soft_update_from_to(self.qf1, self.qf1_target, self.tau)
        ptu.soft_update_from_to(self.qf2, self.qf2_target, self.tau)
        if self.algo.use_target_actor:
            ptu.soft_update_from_to(self.policy, self.policy_target, self.tau)

@torch.no_grad()
def act(self, obs, deterministic=False, return_log_prob=False):
    return self.algo.select_action(actor=self.policy, observ=obs, deterministic=deterministic, return_log_prob=return_log_prob)

class ModelFreeOffPolicy_Separate_RNN(nn.Module):
    """Recommended Architecture
    Recurrent Actor and Recurrent Critic with separate RNNs
    """
    ARCH = 'memory'
    Markov_Actor = False
    Markov_Critic = False

    def __init__(self, obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers=1, lr=0.0003, gamma=0.99, tau=0.005, image_encoder_fn=lambda: None, **kwargs):
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.algo = RL_ALGORITHMS[algo_name](**kwargs[algo_name], action_dim=action_dim)
        self.critic = Critic_RNN(obs_dim, action_dim, encoder, self.algo, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, rnn_num_layers, image_encoder=image_encoder_fn())
        self.critic_optimizer = Adam(self.critic.parameters(), lr=lr)
        self.critic_target = deepcopy(self.critic)
        self.actor = Actor_RNN(obs_dim, action_dim, encoder, self.algo, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, policy_layers, rnn_num_layers, image_encoder=image_encoder_fn())
        self.actor_optimizer = Adam(self.actor.parameters(), lr=lr)
        self.actor_target = deepcopy(self.actor)

    @torch.no_grad()
    def get_initial_info(self):
        return self.actor.get_initial_info()

    @torch.no_grad()
    def act(self, prev_internal_state, prev_action, reward, obs, deterministic=False, return_log_prob=False):
        prev_action = prev_action.unsqueeze(0)
        reward = reward.unsqueeze(0)
        obs = obs.unsqueeze(0)
        current_action_tuple, current_internal_state = self.actor.act(prev_internal_state=prev_internal_state, prev_action=prev_action, reward=reward, obs=obs, deterministic=deterministic, return_log_prob=return_log_prob)
        return (current_action_tuple, current_internal_state)

    def forward(self, actions, rewards, observs, dones, masks):
        """
        For actions a, rewards r, observs o, dones d: (T+1, B, dim)
                where for each t in [0, T], take action a[t], then receive reward r[t], done d[t], and next obs o[t]
                the hidden state h[t](, c[t]) = RNN(h[t-1](, c[t-1]), a[t], r[t], o[t])
                specially, a[0]=r[0]=d[0]=h[0]=c[0]=0.0, o[0] is the initial obs

        The loss is still on the Q value Q(h[t], a[t]) with real actions taken, i.e. t in [1, T]
                based on Masks (T, B, 1)
        """
        assert actions.dim() == rewards.dim() == dones.dim() == observs.dim() == masks.dim() == 3
        assert actions.shape[0] == rewards.shape[0] == dones.shape[0] == observs.shape[0] == masks.shape[0] + 1
        num_valid = torch.clamp(masks.sum(), min=1.0)
        (q1_pred, q2_pred), q_target = self.algo.critic_loss(markov_actor=self.Markov_Actor, markov_critic=self.Markov_Critic, actor=self.actor, actor_target=self.actor_target, critic=self.critic, critic_target=self.critic_target, observs=observs, actions=actions, rewards=rewards, dones=dones, gamma=self.gamma)
        q1_pred, q2_pred = (q1_pred * masks, q2_pred * masks)
        q_target = q_target * masks
        qf1_loss = ((q1_pred - q_target) ** 2).sum() / num_valid
        qf2_loss = ((q2_pred - q_target) ** 2).sum() / num_valid
        self.critic_optimizer.zero_grad()
        (qf1_loss + qf2_loss).backward()
        self.critic_optimizer.step()
        policy_loss, log_probs = self.algo.actor_loss(markov_actor=self.Markov_Actor, markov_critic=self.Markov_Critic, actor=self.actor, actor_target=self.actor_target, critic=self.critic, critic_target=self.critic_target, observs=observs, actions=actions, rewards=rewards)
        policy_loss = (policy_loss * masks).sum() / num_valid
        self.actor_optimizer.zero_grad()
        policy_loss.backward()
        self.actor_optimizer.step()
        outputs = {'qf1_loss': qf1_loss.item(), 'qf2_loss': qf2_loss.item(), 'policy_loss': policy_loss.item()}
        self.soft_target_update()
        if log_probs is not None:
            with torch.no_grad():
                current_log_probs = (log_probs[:-1] * masks).sum() / num_valid
                current_log_probs = current_log_probs.item()
            other_info = self.algo.update_others(current_log_probs)
            outputs.update(other_info)
        return outputs

    def soft_target_update(self):
        ptu.soft_update_from_to(self.critic, self.critic_target, self.tau)
        if self.algo.use_target_actor:
            ptu.soft_update_from_to(self.actor, self.actor_target, self.tau)

    def report_grad_norm(self):
        return {'q_grad_norm': utl.get_grad_norm(self.critic), 'q_rnn_grad_norm': utl.get_grad_norm(self.critic.rnn), 'pi_grad_norm': utl.get_grad_norm(self.actor), 'pi_rnn_grad_norm': utl.get_grad_norm(self.actor.rnn)}

    def update(self, batch):
        actions, rewards, dones = (batch['act'], batch['rew'], batch['term'])
        _, batch_size, _ = actions.shape
        if not self.algo.continuous_action:
            actions = F.one_hot(actions.squeeze(-1).long(), num_classes=self.action_dim).float()
        masks = batch['mask']
        obs, next_obs = (batch['obs'], batch['obs2'])
        observs = torch.cat((obs[[0]], next_obs), dim=0)
        actions = torch.cat((ptu.zeros((1, batch_size, self.action_dim)).float(), actions), dim=0)
        rewards = torch.cat((ptu.zeros((1, batch_size, 1)).float(), rewards), dim=0)
        dones = torch.cat((ptu.zeros((1, batch_size, 1)).float(), dones), dim=0)
        return self.forward(actions, rewards, observs, dones, masks)

@torch.no_grad()
def get_initial_info(self):
    return self.actor.get_initial_info()

@torch.no_grad()
def act(self, prev_internal_state, prev_action, reward, obs, deterministic=False, return_log_prob=False):
    prev_action = prev_action.unsqueeze(0)
    reward = reward.unsqueeze(0)
    obs = obs.unsqueeze(0)
    current_action_tuple, current_internal_state = self.actor.act(prev_internal_state=prev_internal_state, prev_action=prev_action, reward=reward, obs=obs, deterministic=deterministic, return_log_prob=return_log_prob)
    return (current_action_tuple, current_internal_state)

def update(self, batch):
    actions, rewards, dones = (batch['act'], batch['rew'], batch['term'])
    _, batch_size, _ = actions.shape
    if not self.algo.continuous_action:
        actions = F.one_hot(actions.squeeze(-1).long(), num_classes=self.action_dim).float()
    masks = batch['mask']
    obs, next_obs = (batch['obs'], batch['obs2'])
    observs = torch.cat((obs[[0]], next_obs), dim=0)
    actions = torch.cat((ptu.zeros((1, batch_size, self.action_dim)).float(), actions), dim=0)
    rewards = torch.cat((ptu.zeros((1, batch_size, 1)).float(), rewards), dim=0)
    dones = torch.cat((ptu.zeros((1, batch_size, 1)).float(), dones), dim=0)
    return self.forward(actions, rewards, observs, dones, masks)

class Actor_RNN(nn.Module):

    def __init__(self, obs_dim, action_dim, encoder, algo, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, policy_layers, rnn_num_layers, image_encoder=None, **kwargs):
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.algo = algo
        self.image_encoder = image_encoder
        if self.image_encoder is None:
            self.observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
        else:
            assert observ_embedding_size == 0
            observ_embedding_size = self.image_encoder.embed_size
        self.action_embedder = utl.FeatureExtractor(action_dim, action_embedding_size, F.relu)
        self.reward_embedder = utl.FeatureExtractor(1, reward_embedding_size, F.relu)
        rnn_input_size = action_embedding_size + observ_embedding_size + reward_embedding_size
        self.rnn_hidden_size = rnn_hidden_size
        assert encoder in RNNs
        self.encoder = encoder
        self.num_layers = rnn_num_layers
        self.rnn = RNNs[encoder](input_size=rnn_input_size, hidden_size=self.rnn_hidden_size, num_layers=self.num_layers, batch_first=False, bias=True)
        for name, param in self.rnn.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                nn.init.orthogonal_(param)
        if self.image_encoder is None:
            self.current_observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
        self.policy = self.algo.build_actor(input_size=self.rnn_hidden_size + observ_embedding_size, action_dim=self.action_dim, hidden_sizes=policy_layers)

    def _get_obs_embedding(self, observs):
        if self.image_encoder is None:
            return self.observ_embedder(observs)
        else:
            return self.image_encoder(observs)

    def _get_shortcut_obs_embedding(self, observs):
        if self.image_encoder is None:
            return self.current_observ_embedder(observs)
        else:
            return self.image_encoder(observs)

    def get_hidden_states(self, prev_actions, rewards, observs, initial_internal_state=None):
        input_a = self.action_embedder(prev_actions)
        input_r = self.reward_embedder(rewards)
        input_s = self._get_obs_embedding(observs)
        inputs = torch.cat((input_a, input_r, input_s), dim=-1)
        if initial_internal_state is None:
            output, _ = self.rnn(inputs)
            return output
        else:
            output, current_internal_state = self.rnn(inputs, initial_internal_state)
            return (output, current_internal_state)

    def forward(self, prev_actions, rewards, observs):
        """
        For prev_actions a, rewards r, observs o: (T+1, B, dim)
                a[t] -> r[t], o[t]

        return current actions a' (T+1, B, dim) based on previous history

        """
        assert prev_actions.dim() == rewards.dim() == observs.dim() == 3
        assert prev_actions.shape[0] == rewards.shape[0] == observs.shape[0]
        hidden_states = self.get_hidden_states(prev_actions=prev_actions, rewards=rewards, observs=observs)
        curr_embed = self._get_shortcut_obs_embedding(observs)
        joint_embeds = torch.cat((hidden_states, curr_embed), dim=-1)
        return self.algo.forward_actor(actor=self.policy, observ=joint_embeds)

    @torch.no_grad()
    def get_initial_info(self):
        prev_action = ptu.zeros((1, self.action_dim)).float()
        reward = ptu.zeros((1, 1)).float()
        hidden_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
        if self.encoder == GRU_name:
            internal_state = hidden_state
        else:
            cell_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
            internal_state = (hidden_state, cell_state)
        return (prev_action, reward, internal_state)

    @torch.no_grad()
    def act(self, prev_internal_state, prev_action, reward, obs, deterministic=False, return_log_prob=False):
        hidden_state, current_internal_state = self.get_hidden_states(prev_actions=prev_action, rewards=reward, observs=obs, initial_internal_state=prev_internal_state)
        curr_embed = self._get_shortcut_obs_embedding(obs)
        joint_embeds = torch.cat((hidden_state, curr_embed), dim=-1)
        if joint_embeds.dim() == 3:
            joint_embeds = joint_embeds.squeeze(0)
        action_tuple = self.algo.select_action(actor=self.policy, observ=joint_embeds, deterministic=deterministic, return_log_prob=return_log_prob)
        return (action_tuple, current_internal_state)

def _get_obs_embedding(self, observs):
    if self.image_encoder is None:
        return self.observ_embedder(observs)
    else:
        return self.image_encoder(observs)

def _get_shortcut_obs_embedding(self, observs):
    if self.image_encoder is None:
        return self.current_observ_embedder(observs)
    else:
        return self.image_encoder(observs)

def get_hidden_states(self, prev_actions, rewards, observs, initial_internal_state=None):
    input_a = self.action_embedder(prev_actions)
    input_r = self.reward_embedder(rewards)
    input_s = self._get_obs_embedding(observs)
    inputs = torch.cat((input_a, input_r, input_s), dim=-1)
    if initial_internal_state is None:
        output, _ = self.rnn(inputs)
        return output
    else:
        output, current_internal_state = self.rnn(inputs, initial_internal_state)
        return (output, current_internal_state)

def forward(self, prev_actions, rewards, observs):
    """
        For prev_actions a, rewards r, observs o: (T+1, B, dim)
                a[t] -> r[t], o[t]

        return current actions a' (T+1, B, dim) based on previous history

        """
    assert prev_actions.dim() == rewards.dim() == observs.dim() == 3
    assert prev_actions.shape[0] == rewards.shape[0] == observs.shape[0]
    hidden_states = self.get_hidden_states(prev_actions=prev_actions, rewards=rewards, observs=observs)
    curr_embed = self._get_shortcut_obs_embedding(observs)
    joint_embeds = torch.cat((hidden_states, curr_embed), dim=-1)
    return self.algo.forward_actor(actor=self.policy, observ=joint_embeds)

@torch.no_grad()
def get_initial_info(self):
    prev_action = ptu.zeros((1, self.action_dim)).float()
    reward = ptu.zeros((1, 1)).float()
    hidden_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
    if self.encoder == GRU_name:
        internal_state = hidden_state
    else:
        cell_state = ptu.zeros((self.num_layers, 1, self.rnn_hidden_size)).float()
        internal_state = (hidden_state, cell_state)
    return (prev_action, reward, internal_state)

@torch.no_grad()
def act(self, prev_internal_state, prev_action, reward, obs, deterministic=False, return_log_prob=False):
    hidden_state, current_internal_state = self.get_hidden_states(prev_actions=prev_action, rewards=reward, observs=obs, initial_internal_state=prev_internal_state)
    curr_embed = self._get_shortcut_obs_embedding(obs)
    joint_embeds = torch.cat((hidden_state, curr_embed), dim=-1)
    if joint_embeds.dim() == 3:
        joint_embeds = joint_embeds.squeeze(0)
    action_tuple = self.algo.select_action(actor=self.policy, observ=joint_embeds, deterministic=deterministic, return_log_prob=return_log_prob)
    return (action_tuple, current_internal_state)

class Critic_RNN(nn.Module):

    def __init__(self, obs_dim, action_dim, encoder, algo, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, rnn_num_layers, image_encoder=None, **kwargs):
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.algo = algo
        self.image_encoder = image_encoder
        if self.image_encoder is None:
            self.observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
        else:
            assert observ_embedding_size == 0
            observ_embedding_size = self.image_encoder.embed_size
        self.action_embedder = utl.FeatureExtractor(action_dim, action_embedding_size, F.relu)
        self.reward_embedder = utl.FeatureExtractor(1, reward_embedding_size, F.relu)
        rnn_input_size = action_embedding_size + observ_embedding_size + reward_embedding_size
        self.rnn_hidden_size = rnn_hidden_size
        assert encoder in RNNs
        self.encoder = encoder
        self.rnn = RNNs[encoder](input_size=rnn_input_size, hidden_size=self.rnn_hidden_size, num_layers=rnn_num_layers, batch_first=False, bias=True)
        for name, param in self.rnn.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                nn.init.orthogonal_(param)
        shortcut_embedding_size = rnn_input_size
        if self.algo.continuous_action and self.image_encoder is None:
            self.current_shortcut_embedder = utl.FeatureExtractor(obs_dim + action_dim, shortcut_embedding_size, F.relu)
        elif self.algo.continuous_action and self.image_encoder is not None:
            self.current_shortcut_embedder = utl.FeatureExtractor(action_dim, shortcut_embedding_size, F.relu)
            shortcut_embedding_size += self.image_encoder.embed_size
        elif not self.algo.continuous_action and self.image_encoder is None:
            self.current_shortcut_embedder = utl.FeatureExtractor(obs_dim, shortcut_embedding_size, F.relu)
        elif not self.algo.continuous_action and self.image_encoder is not None:
            shortcut_embedding_size = self.image_encoder.embed_size
        else:
            raise NotImplementedError
        self.qf1, self.qf2 = self.algo.build_critic(input_size=self.rnn_hidden_size + shortcut_embedding_size, hidden_sizes=dqn_layers, action_dim=action_dim)

    def _get_obs_embedding(self, observs):
        if self.image_encoder is None:
            return self.observ_embedder(observs)
        else:
            return self.image_encoder(observs)

    def _get_shortcut_obs_act_embedding(self, observs, current_actions):
        if self.algo.continuous_action and self.image_encoder is None:
            return self.current_shortcut_embedder(torch.cat([observs, current_actions], dim=-1))
        elif self.algo.continuous_action and self.image_encoder is not None:
            return torch.cat([self.image_encoder(observs), self.current_shortcut_embedder(current_actions)], dim=-1)
        elif not self.algo.continuous_action and self.image_encoder is None:
            return self.current_shortcut_embedder(observs)
        elif not self.algo.continuous_action and self.image_encoder is not None:
            return self.image_encoder(observs)

    def get_hidden_states(self, prev_actions, rewards, observs):
        input_a = self.action_embedder(prev_actions)
        input_r = self.reward_embedder(rewards)
        input_s = self._get_obs_embedding(observs)
        inputs = torch.cat((input_a, input_r, input_s), dim=-1)
        output, _ = self.rnn(inputs)
        return output

    def forward(self, prev_actions, rewards, observs, current_actions):
        """
        For prev_actions a, rewards r, observs o: (T+1, B, dim)
                a[t] -> r[t], o[t]
        current_actions (or action probs for discrete actions) a': (T or T+1, B, dim)
                o[t] -> a'[t]
        NOTE: there is one timestep misalignment in prev_actions and current_actions
        """
        assert prev_actions.dim() == rewards.dim() == observs.dim() == current_actions.dim() == 3
        assert prev_actions.shape[0] == rewards.shape[0] == observs.shape[0]
        hidden_states = self.get_hidden_states(prev_actions=prev_actions, rewards=rewards, observs=observs)
        if current_actions.shape[0] == observs.shape[0]:
            curr_embed = self._get_shortcut_obs_act_embedding(observs, current_actions)
            joint_embeds = torch.cat((hidden_states, curr_embed), dim=-1)
        else:
            curr_embed = self._get_shortcut_obs_act_embedding(observs[:-1], current_actions)
            joint_embeds = torch.cat((hidden_states[:-1], curr_embed), dim=-1)
        q1 = self.qf1(joint_embeds)
        q2 = self.qf2(joint_embeds)
        return (q1, q2)

def _get_obs_embedding(self, observs):
    if self.image_encoder is None:
        return self.observ_embedder(observs)
    else:
        return self.image_encoder(observs)

def _get_shortcut_obs_act_embedding(self, observs, current_actions):
    if self.algo.continuous_action and self.image_encoder is None:
        return self.current_shortcut_embedder(torch.cat([observs, current_actions], dim=-1))
    elif self.algo.continuous_action and self.image_encoder is not None:
        return torch.cat([self.image_encoder(observs), self.current_shortcut_embedder(current_actions)], dim=-1)
    elif not self.algo.continuous_action and self.image_encoder is None:
        return self.current_shortcut_embedder(observs)
    elif not self.algo.continuous_action and self.image_encoder is not None:
        return self.image_encoder(observs)

def get_hidden_states(self, prev_actions, rewards, observs):
    input_a = self.action_embedder(prev_actions)
    input_r = self.reward_embedder(rewards)
    input_s = self._get_obs_embedding(observs)
    inputs = torch.cat((input_a, input_r, input_s), dim=-1)
    output, _ = self.rnn(inputs)
    return output

