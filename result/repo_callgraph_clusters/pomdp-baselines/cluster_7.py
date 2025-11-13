# Cluster 7

class Atari(gym.Env):
    """
    all follow DreamerV2
    NOTE: don't clip rewards here, as we need raw scores for comparison.
    """
    LOCK = threading.Lock()

    def __init__(self, name, action_repeat=4, size=(64, 64), grayscale=True, noops=30, life_done=False, sticky_actions=True, all_actions=True, flatten_img=True):
        assert size[0] == size[1]
        channels = 1 if grayscale else 3
        image_sizes = (channels, size[0], size[1])
        with self.LOCK:
            env = gym.envs.atari.AtariEnv(game=name, obs_type='grayscale' if grayscale else 'rgb', frameskip=1, repeat_action_probability=0.25 if sticky_actions else 0.0, full_action_space=all_actions)
        env.get_obs = lambda: None
        env.spec = gym.envs.registration.EnvSpec('NoFrameskip-v0')
        env = gym.wrappers.AtariPreprocessing(env, noops, action_repeat, size[0], life_done, grayscale)
        self.env = env
        self.action_space = self.env.action_space
        self.image_space = gym.spaces.Box(low=0, high=255, shape=image_sizes, dtype=np.uint8)
        self.flatten_img = flatten_img
        if flatten_img:
            self.observation_space = gym.spaces.Box(low=0, high=255, shape=(np.prod(image_sizes),), dtype=np.uint8)
        else:
            self.observation_space = self.image_space

    def reset(self):
        with self.LOCK:
            image: np.ndarray = self.env.reset()
        return self.observe(image)

    def step(self, action):
        image, reward, done, info = self.env.step(action)
        return (self.observe(image), reward, done, info)

    def observe(self, image):
        if self.flatten_img:
            return image.flatten()
        else:
            return np.expand_dims(image, axis=0)

    def render(self, mode):
        return self.env.render(mode)

def observe(self, image):
    if self.flatten_img:
        return image.flatten()
    else:
        return np.expand_dims(image, axis=0)

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

class ActionDelayWrapper(gym.Wrapper):

    def _step(self, action):
        self._action_buffer.append(action)
        action = self._action_buffer.popleft()
        return self.env.step(action)

    def _reset(self):
        self._action_delay = np.random.randint(delay_range_start, delay_range_end)
        self._action_buffer = collections.deque([0 for _ in range(self._action_delay)])
        return self.env.reset()

def _reset(self):
    self._action_delay = np.random.randint(delay_range_start, delay_range_end)
    self._action_buffer = collections.deque([0 for _ in range(self._action_delay)])
    return self.env.reset()

class DelayedCatch(gym.Env):

    def __init__(self, delay, grid_size=7, flatten_img=True, delayed=True, one_hot_actions=False):
        super().__init__()
        self.grid_size = grid_size
        self.delay = delay
        self.num_catches = (delay + 1) // 7
        self.action_space = gym.spaces.Discrete(3)
        self.image_space = gym.spaces.MultiDiscrete([[[2 for i in range(grid_size)] for i in range(grid_size)]])
        self.flatten_img = flatten_img
        if flatten_img:
            self.observation_space = gym.spaces.MultiDiscrete([2 for i in range(grid_size * grid_size)])
        else:
            self.observation_space = self.image_space
        self.delayed = delayed
        self.one_hot_actions = one_hot_actions

    def _update_state(self, action):
        """
        Input: action and states
        Ouput: new states and reward
        """
        state = self.state
        if self.one_hot_actions:
            action = np.argmax(action)
        if action == 0:
            action = -1
        elif action == 1:
            action = 0
        elif action == 2:
            action = 1
        else:
            raise ValueError('not valid action')
        f0, f1, basket = state[0]
        new_basket = min(max(0, basket + action), self.grid_size - 1)
        f0 += 1
        out = np.asarray([f0, f1, new_basket])
        out = out[np.newaxis]
        assert len(out.shape) == 2
        self.state = out

    def _draw_state(self):
        im_size = (self.grid_size,) * 2
        state = self.state[0]
        canvas = np.zeros(im_size)
        canvas[state[0], state[1]] = -1
        canvas[-1, int(state[2])] = 1
        return canvas

    def _get_reward(self):
        fruit_row, fruit_col, basket = self.state[0]
        if fruit_row == self.grid_size - 1:
            if fruit_col == basket:
                return 1
            else:
                return 0
        else:
            return 0

    def _is_over(self):
        if self.state[0, 0] == self.grid_size - 1:
            return True
        else:
            return False

    def observe(self):
        canvas = self._draw_state()
        if self.flatten_img:
            return canvas.reshape(-1)
        else:
            return np.expand_dims(canvas, axis=0)

    def step(self, action):
        self.time_step += 1
        info = {}
        if self._is_over():
            obs = self.soft_reset()
            reward = self._get_reward()
            info['reward'] = reward
            self.accumulated_reward += reward
            return (obs, 0, False, info)
        self._update_state(action)
        reward = self._get_reward()
        info['reward'] = reward
        self.accumulated_reward += reward
        if not self.delayed:
            return (self.observe(), reward, False, info)
        if self.time_step >= self.delay:
            return (self.observe(), self.accumulated_reward, True, info)
        else:
            return (self.observe(), 0, False, info)

    def reset(self):
        self.catch_count = 0
        self.ns = np.random.randint(0, self.grid_size - 1, size=self.num_catches)
        self.ms = np.random.randint(1, self.grid_size - 2, size=self.num_catches)
        obs = self.soft_reset()
        self.accumulated_reward = 0
        self.time_step = 0
        return obs

    def soft_reset(self):
        n = self.ns[self.catch_count]
        m = self.ms[self.catch_count]
        self.state = np.asarray([0, n, m])[np.newaxis]
        self.catch_count += 1
        return self.observe()

def observe(self):
    canvas = self._draw_state()
    if self.flatten_img:
        return canvas.reshape(-1)
    else:
        return np.expand_dims(canvas, axis=0)

class KeyToDoor(gym.Env):

    def __init__(self, num_apples=10, apple_reward=1.0, fix_apple_reward_in_episode=True, final_reward=10.0, default_reward=0, respawn_every=20, REWARD_GRID=key_to_door.REWARD_GRID_SR, max_frames=key_to_door.MAX_FRAMES_PER_PHASE_SR, crop=True, flatten_img=True, one_hot_actions=False):
        super().__init__()
        self.pycolab_env = env.PycolabEnvironment(game='key_to_door', num_apples=num_apples, apple_reward=apple_reward, fix_apple_reward_in_episode=fix_apple_reward_in_episode, final_reward=final_reward, respawn_every=respawn_every, crop=crop, default_reward=default_reward, REWARD_GRID=REWARD_GRID, max_frames=max_frames)
        self.action_space = gym.spaces.Discrete(4)
        self.one_hot_actions = one_hot_actions
        self.img_size = (3, 5, 5)
        self.image_space = gym.spaces.Box(shape=self.img_size, low=0, high=255, dtype=np.uint8)
        self.flatten_img = flatten_img
        if flatten_img:
            self.observation_space = gym.spaces.Box(shape=(np.array(self.img_size).prod(),), low=0, high=255, dtype=np.uint8)
        else:
            self.observation_space = self.image_space

    def _convert_obs(self, obs):
        new_obs = np.transpose(obs, (-1, 0, 1))
        if self.flatten_img:
            new_obs = new_obs.flatten()
        return new_obs

    def step(self, action):
        if self.one_hot_actions:
            action = np.argmax(action)
        obs, r = self.pycolab_env.step(action)
        self._ret += r
        info = {}
        if self.pycolab_env._episode.game_over:
            done = True
            info['success'] = self.pycolab_env.last_phase_reward() > 0.0
        else:
            done = False
        return (self._convert_obs(obs), r, done, info)

    def reset(self):
        obs, _ = self.pycolab_env.reset()
        self._ret = 0.0
        return self._convert_obs(obs)

def _convert_obs(self, obs):
    new_obs = np.transpose(obs, (-1, 0, 1))
    if self.flatten_img:
        new_obs = new_obs.flatten()
    return new_obs

class HalfCheetahRandDirOracleEnv(HalfCheetahDirEnv):

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat[1:], self.sim.data.qvel.flat, self.get_body_com('torso').flat, [self._goal]]).astype(np.float32).flatten()

def _get_obs(self):
    return np.concatenate([self.sim.data.qpos.flat[1:], self.sim.data.qvel.flat, self.get_body_com('torso').flat, [self._goal]]).astype(np.float32).flatten()

def mass_center(model, sim):
    mass = np.expand_dims(model.body_mass, 1)
    xpos = sim.data.xipos
    return np.sum(mass * xpos, 0) / np.sum(mass)

class HalfCheetahEnv(HalfCheetahEnv_):

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat[1:], self.sim.data.qvel.flat, self.get_body_com('torso').flat]).astype(np.float32).flatten()

    def viewer_setup(self):
        camera_id = self.model.camera_name2id('track')
        self.viewer.cam.type = 2
        self.viewer.cam.fixedcamid = camera_id
        self.viewer.cam.distance = self.model.stat.extent * 0.35
        self.viewer._hide_overlay = True

    def render(self, mode='human'):
        if mode == 'rgb_array':
            self._get_viewer().render()
            width, height = (500, 500)
            data = self._get_viewer().read_pixels(width, height, depth=False)
            return data
        elif mode == 'human':
            self._get_viewer().render()

    @staticmethod
    def visualise_behaviour(env, args, policy, iter_idx, encoder=None, image_folder=None, **kwargs):
        num_episodes = args.max_rollouts_per_task
        unwrapped_env = env.venv.unwrapped.envs[0].unwrapped
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
            sample_embeddings = args.sample_embeddings
        else:
            episode_latent_samples = episode_latent_means = episode_latent_logvars = None
            sample_embeddings = False
        env.reset_task()
        obs_raw, obs_normalised = env.reset()
        obs_raw = obs_raw.float().reshape((1, -1)).to(device)
        obs_normalised = obs_normalised.float().reshape((1, -1)).to(device)
        start_obs_raw = obs_raw.clone()
        if hasattr(args, 'hidden_size'):
            hidden_state = torch.zeros((1, args.hidden_size)).to(device)
        else:
            hidden_state = None
        task = env.get_task()
        pos = [[] for _ in range(args.max_rollouts_per_task)]
        pos[0] = [unwrapped_env.get_body_com('torso')[0]]
        for episode_idx in range(num_episodes):
            curr_rollout_rew = []
            if episode_idx == 0:
                if encoder is not None:
                    curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder.prior(1)
                    curr_latent_sample = curr_latent_sample[0].to(device)
                    curr_latent_mean = curr_latent_mean[0].to(device)
                    curr_latent_logvar = curr_latent_logvar[0].to(device)
                else:
                    curr_latent_sample = curr_latent_mean = curr_latent_logvar = None
            if encoder is not None:
                episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
                episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
                episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
            pos[episode_idx].append(unwrapped_env.get_body_com('torso')[0].copy())
            for step_idx in range(1, env._max_episode_steps + 1):
                if step_idx == 1:
                    episode_prev_obs[episode_idx].append(start_obs_raw.clone())
                else:
                    episode_prev_obs[episode_idx].append(obs_raw.clone())
                o_aug = utl.get_augmented_obs(args, obs_normalised if args.norm_obs_for_policy else obs_raw, curr_latent_sample, curr_latent_mean, curr_latent_logvar)
                _, action, _ = policy.act(o_aug, deterministic=True)
                (obs_raw, obs_normalised), (rew_raw, rew_normalised), done, info = env.step(action.cpu().detach())
                obs_raw = obs_raw.float().reshape((1, -1)).to(device)
                obs_normalised = obs_normalised.float().reshape((1, -1)).to(device)
                pos[episode_idx].append(unwrapped_env.get_body_com('torso')[0].copy())
                if encoder is not None:
                    curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder(action.float().to(device), obs_raw, torch.tensor(rew_raw).reshape((1, 1)).float().to(device), hidden_state, return_prior=False)
                    episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
                    episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
                    episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
                episode_next_obs[episode_idx].append(obs_raw.clone())
                episode_rewards[episode_idx].append(rew_raw.clone())
                episode_actions[episode_idx].append(action.clone())
                if info[0]['done_mdp'] and (not done):
                    start_obs_raw = info[0]['start_state']
                    start_obs_raw = torch.from_numpy(start_obs_raw).float().reshape((1, -1)).to(device)
                    break
            episode_returns.append(sum(curr_rollout_rew))
            episode_lengths.append(step_idx)
        if encoder is not None:
            episode_latent_means = [torch.stack(e) for e in episode_latent_means]
            episode_latent_logvars = [torch.stack(e) for e in episode_latent_logvars]
        episode_prev_obs = [torch.cat(e) for e in episode_prev_obs]
        episode_next_obs = [torch.cat(e) for e in episode_next_obs]
        episode_actions = [torch.cat(e) for e in episode_actions]
        episode_rewards = [torch.cat(e) for e in episode_rewards]
        plt.figure(figsize=(7, 4 * num_episodes))
        min_x = min([min(p) for p in pos])
        max_x = max([max(p) for p in pos])
        span = max_x - min_x
        for i in range(num_episodes):
            plt.subplot(num_episodes, 1, i + 1)
            plt.plot(pos[i], range(len(pos[i])), 'k')
            plt.title('task: '.format(task), fontsize=15)
            plt.ylabel('steps (ep {})'.format(i), fontsize=15)
            if i == num_episodes - 1:
                plt.xlabel('position', fontsize=15)
            else:
                plt.xticks([])
            plt.xlim(min_x - 0.05 * span, max_x + 0.05 * span)
        plt.tight_layout()
        if image_folder is not None:
            plt.savefig('{}/{}_behaviour'.format(image_folder, iter_idx))
            plt.close()
        else:
            plt.show()
        return (episode_latent_means, episode_latent_logvars, episode_prev_obs, episode_next_obs, episode_actions, episode_rewards, episode_returns)

def _get_obs(self):
    return np.concatenate([self.sim.data.qpos.flat[1:], self.sim.data.qvel.flat, self.get_body_com('torso').flat]).astype(np.float32).flatten()

class SparsePointEnv(PointEnv):
    """
    - tasks sampled from unit half-circle
    - reward is L2 distance given only within goal radius
    NOTE that `step()` returns the dense reward because this is used during meta-training
    the algorithm should call `sparsify_rewards()` to get the sparse rewards
    """

    def __init__(self, max_episode_steps=60, n_tasks=2, goal_radius=0.2, modify_init_state_dist=True, on_circle_init_state=True, **kwargs):
        super().__init__(max_episode_steps, n_tasks)
        self.goal_radius = goal_radius
        self.modify_init_state_dist = modify_init_state_dist
        self.on_circle_init_state = on_circle_init_state
        radius = 1.0
        angles = np.random.uniform(0, np.pi, size=n_tasks)
        xs = radius * np.cos(angles)
        ys = radius * np.sin(angles)
        goals = np.stack([xs, ys], axis=1)
        np.random.shuffle(goals)
        goals = goals.tolist()
        self.goals = goals
        self.reset_task(0)

    def sparsify_rewards(self, r):
        """zero out rewards when outside the goal radius"""
        mask = (r >= -self.goal_radius).astype(np.float32)
        r = r * mask
        return r

    def reset_model(self):
        self.step_count = 0
        if self.modify_init_state_dist:
            self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
            if not self.on_circle_init_state:
                while 1 - self.goal_radius <= np.linalg.norm(self._state) <= 1 + self.goal_radius:
                    self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
        else:
            self._state = np.array([0, 0])
        return self._get_obs()

    def step(self, action):
        ob, reward, done, d = super().step(action)
        sparse_reward = self.sparsify_rewards(reward)
        if reward >= -self.goal_radius:
            sparse_reward = 1
        d.update({'sparse_reward': sparse_reward})
        return (ob, sparse_reward, done, d)

    def reward(self, state, action=None):
        return self.sparsify_rewards(super().reward(state, action))

    def is_goal_state(self):
        if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
            return True
        else:
            return False

    def plot_env(self):
        ax = plt.gca()
        angles = np.linspace(0, np.pi, num=100)
        x, y = (np.cos(angles), np.sin(angles))
        plt.plot(x, y, color='k')
        plt.axis('scaled')
        ax.set_xlim(-2, 2)
        ax.set_ylim(-1, 2)
        plt.xticks([])
        plt.yticks([])
        circle = plt.Circle((self._goal[0], self._goal[1]), radius=self.goal_radius, alpha=0.3)
        ax.add_artist(circle)

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        plt.scatter(observations[[0], 0], observations[[0], 1], marker='x', **kwargs)
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)

def sparsify_rewards(self, r):
    """zero out rewards when outside the goal radius"""
    mask = (r >= -self.goal_radius).astype(np.float32)
    r = r * mask
    return r

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

def random_batch(self, batch_size):
    """batch of unordered transitions"""
    indices = np.random.randint(0, self._size, batch_size)
    return self.sample_data(indices)

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

def filter_batch(np_batch):
    for k, v in np_batch.items():
        if v.dtype == np.bool:
            yield (k, v.astype(int))
        else:
            yield (k, v)

