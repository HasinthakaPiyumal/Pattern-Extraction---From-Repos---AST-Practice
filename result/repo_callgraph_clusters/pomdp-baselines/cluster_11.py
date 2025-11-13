# Cluster 11

def reproduce(seed):
    """
    This can only fix the randomness of numpy and torch
    To fix the environment's, please use
        env.seed(seed)
        env.action_space.np_random.seed(seed)
    We have add these in our training script
    """
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

def seed(seed):
    random.seed(seed)
    torch.random.manual_seed(seed)
    np.random.seed(seed)

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

def _seed(self, seed=None):
    self.np_random, seed = seeding.np_random(seed)
    self._vizdoom.set_seed(seed % 2 ** 32)
    return [seed]

class EnvRegistry(object):
    """Register an env by ID. IDs remain stable over time and are
    guaranteed to resolve to the same environment dynamics (or be
    desupported). The goal is that results on a particular environment
    should always be comparable, and not depend on the version of the
    code that was running.
    """

    def __init__(self):
        self.env_specs = {}

    def make(self, id, **kwargs):
        logger.info('Making new env: %s', id)
        spec = self.spec(id)
        env = spec.make(**kwargs)
        if hasattr(env, '_reset') and hasattr(env, '_step') and (not getattr(env, '_gym_disable_underscore_compat', False)):
            patch_deprecated_methods(env)
        if env.spec.timestep_limit is not None and (not spec.tags.get('vnc')):
            from .time_limit import TimeLimit
            env = TimeLimit(env, max_episode_steps=env.spec.max_episode_steps, max_episode_seconds=env.spec.max_episode_seconds)
        return env

    def all(self):
        return self.env_specs.values()

    def spec(self, id):
        match = env_id_re.search(id)
        if not match:
            raise error.Error('Attempted to look up malformed environment ID: {}. (Currently all IDs must be of the form {}.)'.format(id.encode('utf-8'), env_id_re.pattern))
        try:
            return self.env_specs[id]
        except KeyError:
            env_name = match.group(1)
            matching_envs = [valid_env_name for valid_env_name, valid_env_spec in self.env_specs.items() if env_name == valid_env_spec._env_name]
            if matching_envs:
                raise error.DeprecatedEnv('Env {} not found (valid versions include {})'.format(id, matching_envs))
            else:
                raise error.UnregisteredEnv('No registered env with id: {}'.format(id))

    def register(self, id, **kwargs):
        if id in self.env_specs:
            raise error.Error('Cannot re-register id: {}'.format(id))
        self.env_specs[id] = EnvSpec(id, **kwargs)

def make(self, id, **kwargs):
    logger.info('Making new env: %s', id)
    spec = self.spec(id)
    env = spec.make(**kwargs)
    if hasattr(env, '_reset') and hasattr(env, '_step') and (not getattr(env, '_gym_disable_underscore_compat', False)):
        patch_deprecated_methods(env)
    if env.spec.timestep_limit is not None and (not spec.tags.get('vnc')):
        from .time_limit import TimeLimit
        env = TimeLimit(env, max_episode_steps=env.spec.max_episode_steps, max_episode_seconds=env.spec.max_episode_seconds)
    return env

def make(id, **kwargs):
    return registry.make(id, **kwargs)

def spec(id):
    return registry.spec(id)

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

def seed(self, seed=None):
    """Setup random number generator."""
    self.np_random, seed = seeding.np_random(seed)
    return seed

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

def seed(self, seed=None):
    """Seed random number generator."""
    return self._world.seed(seed)

class GymEnvironment(BaseGymEnvironment):
    metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': 50}
    worlds = None

    def __init__(self, obs_type='image', frameskip=4, world='baseline'):
        self._env = PhysicalEnvironment(world=self.worlds[world])
        self._world = world
        self.action_space = spaces.Discrete(self._env.world.n_actions)
        if obs_type == 'image':
            self.observation_space = spaces.Box(low=0, high=255, shape=(self._env.height, self._env.width, 3))
        else:
            raise error.Error('Unrecognized observation type: {}'.format(obs_type))
        self._obs_type = obs_type
        self._frameskip = frameskip

    def __getstate__(self):
        return {'obs_type': self._obs_type, 'frameskip': self._frameskip, 'world': self._world}

    def __setstate__(self, state):
        self.__init__(**state)

    def _get_observation(self):
        if self._obs_type == 'image':
            return self._env.render(mode='rgb_array')
        raise NotImplementedError

    def _reset(self):
        self._env.reset()
        self._env.step()
        return self._get_observation()

    def _seed(self, seed=None):
        seed = self._env.seed(seed)
        return [seed]

    def _step(self, action):
        score = self._env.world.score
        self._env.act(action)
        for _ in range(self._frameskip):
            terminal = self._env.step()
            if terminal:
                break
        observation = self._get_observation()
        reward = self._env.world.score - score
        info = {'lives': self._env.world.lives}
        return (observation, reward, terminal, info)

    def _render(self, mode='human', close=False):
        if close:
            return
        return self._env.render(mode)

    def get_action_meanings(self):
        return []

    @property
    def lives(self):
        return self._env.world.lives

    @property
    def parameters(self):
        parameters = super(GymEnvironment, self).parameters
        parameters.update(self._env.world.parameters)
        return parameters

def _seed(self, seed=None):
    seed = self._env.seed(seed)
    return [seed]

def keep_n_characters_in_grid(grid, character, n, backdrop_char=BACKGROUND):
    """Keeps only a sample of characters `character` in the grid."""
    np_grid = np.array([list(i) for i in grid])
    char_positions = np.argwhere(np_grid == character)
    num_empty_positions = char_positions.shape[0] - n
    if num_empty_positions < 0:
        raise ValueError('Not enough characters `{}` in grid.'.format(character))
    empty_pos = np.random.permutation(char_positions)[:num_empty_positions]
    grid = [list(row) for row in grid]
    for i, j in empty_pos:
        grid[i][j] = backdrop_char
    return [''.join(row) for row in grid]

def make_env(env_id, episodes_per_task, seed=None, oracle=False, **kwargs):
    """
    kwargs: include n_tasks=num_tasks
    """
    env = gym.make(env_id, **kwargs)
    if seed is not None:
        env.seed(seed)
        env.action_space.np_random.seed(seed)
    env = VariBadWrapper(env=env, episodes_per_task=episodes_per_task, oracle=oracle)
    return env

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

def seed(self, seed=None):
    self.np_random, seed = seeding.np_random(seed)
    random.seed(seed)
    return [seed]

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

