# Cluster 21

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

class Brick(PhysicalObject):
    """Brick object."""

    def __init__(self, *args, **kwargs):
        self.row = kwargs.pop('row')
        self.column = kwargs.pop('column')
        kwargs['color'] = self.get_color()
        super(Brick, self).__init__('brick.png', *args, **kwargs)

    def get_color(self):
        """Brick color."""
        colors = {0: (255, 0, 0), 1: (255, 174, 0), 2: (252, 255, 0), 3: (0, 255, 0), 4: (0, 0, 255)}
        return colors.get(self.row, (0, 0, 0))

    def get_score(self):
        """Score if the brick is destroyed."""
        scores = {0: 10, 1: 7, 2: 5, 3: 3, 4: 1}
        return scores.get(self.row, 0)

    def get_restitution(self):
        restitution = {0: 1.5, 1: 1.3, 2: 1.2, 3: 1.15, 4: 1.1}
        return restitution.get(self.row, 1.0)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=self.get_restitution())
        return body

    def on_contact(self, other):
        """Destroy the brick on contact with the ball."""
        if not isinstance(other, Ball):
            return
        self.kill()
        ball_velocity_x = other.body.linearVelocity[0]
        if abs(ball_velocity_x) < 0.2:
            other.apply_impulse([0.2 * np.sign(ball_velocity_x), 0.0])
        self._world._score += self.get_score()

def get_color(self):
    """Brick color."""
    colors = {0: (255, 0, 0), 1: (255, 174, 0), 2: (252, 255, 0), 3: (0, 255, 0), 4: (0, 0, 255)}
    return colors.get(self.row, (0, 0, 0))

def get_score(self):
    """Score if the brick is destroyed."""
    scores = {0: 10, 1: 7, 2: 5, 3: 3, 4: 1}
    return scores.get(self.row, 0)

def get_restitution(self):
    restitution = {0: 1.5, 1: 1.3, 2: 1.2, 3: 1.15, 4: 1.1}
    return restitution.get(self.row, 1.0)

class DoorSprite(plab_things.Sprite):
    """Sprite for the door."""

    def __init__(self, corner, position, character, pickup_reward):
        super(DoorSprite, self).__init__(corner, position, character)
        self._pickup_reward = pickup_reward

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[common.PLAYER].position
        pick_up = self.position == player_position
        if pick_up and the_plot.get('has_key'):
            the_plot.add_reward(self._pickup_reward)
            the_plot['has_key'] = False

def update(self, actions, board, layers, backdrop, things, the_plot):
    player_position = things[common.PLAYER].position
    pick_up = self.position == player_position
    if pick_up and the_plot.get('has_key'):
        the_plot.add_reward(self._pickup_reward)
        the_plot['has_key'] = False

class PlayerSprite(prefab_sprites.MazeWalker):
    """Sprite representing the agent."""

    def __init__(self, corner, position, character, max_steps_per_act, moving_player):
        """Indicates to the superclass that we can't walk off the board."""
        super(PlayerSprite, self).__init__(corner, position, character, impassable=[common.BORDER], confined_to_board=True)
        self._moving_player = moving_player
        self._max_steps_per_act = max_steps_per_act
        self._num_steps = 0

    def update(self, actions, board, layers, backdrop, things, the_plot):
        del backdrop
        if actions is not None:
            assert actions in common.ACTIONS
        the_plot.log('Step {} | Action {}'.format(self._num_steps, actions))
        the_plot.add_reward(0.0)
        self._num_steps += 1
        if actions == common.ACTION_QUIT:
            the_plot.terminate_episode()
        if self._moving_player:
            if actions == common.ACTION_WEST:
                self._west(board, the_plot)
            elif actions == common.ACTION_EAST:
                self._east(board, the_plot)
            elif actions == common.ACTION_NORTH:
                self._north(board, the_plot)
            elif actions == common.ACTION_SOUTH:
                self._south(board, the_plot)
        if self._max_steps_per_act == self._num_steps:
            the_plot.terminate_episode()

def update(self, actions, board, layers, backdrop, things, the_plot):
    del backdrop
    if actions is not None:
        assert actions in common.ACTIONS
    the_plot.log('Step {} | Action {}'.format(self._num_steps, actions))
    the_plot.add_reward(0.0)
    self._num_steps += 1
    if actions == common.ACTION_QUIT:
        the_plot.terminate_episode()
    if self._moving_player:
        if actions == common.ACTION_WEST:
            self._west(board, the_plot)
        elif actions == common.ACTION_EAST:
            self._east(board, the_plot)
        elif actions == common.ACTION_NORTH:
            self._north(board, the_plot)
        elif actions == common.ACTION_SOUTH:
            self._south(board, the_plot)
    if self._max_steps_per_act == self._num_steps:
        the_plot.terminate_episode()

class ObjectSprite(plab_things.Sprite):
    """Sprite for a generic object which can be collectable."""

    def __init__(self, corner, position, character, reward=0.0, collectable=True, terminate=True):
        super(ObjectSprite, self).__init__(corner, position, character)
        self._reward = reward
        self._collectable = collectable

    def set_visibility(self, visible):
        self._visible = visible

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[common.PLAYER].position
        pick_up = self.position == player_position
        if pick_up and self.visible:
            the_plot.add_reward(self._reward)
            if self._collectable:
                self.set_visibility(False)
                for v in itervalues(things):
                    if isinstance(v, ObjectSprite):
                        v.set_visibility(False)

def update(self, actions, board, layers, backdrop, things, the_plot):
    player_position = things[common.PLAYER].position
    pick_up = self.position == player_position
    if pick_up and self.visible:
        the_plot.add_reward(self._reward)
        if self._collectable:
            self.set_visibility(False)
            for v in itervalues(things):
                if isinstance(v, ObjectSprite):
                    v.set_visibility(False)

class PlayerSprite(prefab_sprites.MazeWalker):
    """Sprite for the actor."""

    def __init__(self, corner, position, character, impassable=BORDER):
        super(PlayerSprite, self).__init__(corner, position, character, impassable=impassable, confined_to_board=True)

    def update(self, actions, board, layers, backdrop, things, the_plot):
        the_plot.add_reward(0.0)
        if actions == ACTION_QUIT:
            the_plot.next_chapter = None
            the_plot.terminate_episode()
        if actions == ACTION_WEST:
            self._west(board, the_plot)
        elif actions == ACTION_EAST:
            self._east(board, the_plot)
        elif actions == ACTION_NORTH:
            self._north(board, the_plot)
        elif actions == ACTION_SOUTH:
            self._south(board, the_plot)

def update(self, actions, board, layers, backdrop, things, the_plot):
    the_plot.add_reward(0.0)
    if actions == ACTION_QUIT:
        the_plot.next_chapter = None
        the_plot.terminate_episode()
    if actions == ACTION_WEST:
        self._west(board, the_plot)
    elif actions == ACTION_EAST:
        self._east(board, the_plot)
    elif actions == ACTION_NORTH:
        self._north(board, the_plot)
    elif actions == ACTION_SOUTH:
        self._south(board, the_plot)

class AppleDrape(plab_things.Drape):
    """Drape for the apples used in the distractor phase."""

    def __init__(self, curtain, character, respawn_every, reward, fix_apple_reward_in_episode):
        """Constructor.

        Args:
          curtain: Array specifying locations of apples. Obtained from ascii grid.
          character: Character representing the drape.
          respawn_every: respawn frequency of apples.
          reward: Can either be a scalar specifying the reward or a reward range
            [min, max), given as a list or tuple, to uniformly sample from.
          fix_apple_reward_in_episode: If set to True, then only sample the apple's
            reward once in the episode and then fix the value.
        """
        super(AppleDrape, self).__init__(curtain, character)
        self._respawn_every = respawn_every
        if not isinstance(reward, (list, tuple)):
            self._reward = [reward, reward]
        else:
            if len(reward) != 2:
                raise ValueError('Reward must be a scalar or a two element list/tuple.')
            self._reward = reward
        self._fix_apple_reward_in_episode = fix_apple_reward_in_episode
        self._last_pickup = np.where(curtain, np.inf * np.ones_like(curtain), -1.0 * np.ones_like(curtain))

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[PLAYER].position
        if self._fix_apple_reward_in_episode and (not the_plot.get('sampled_apple_reward', None)):
            the_plot['sampled_apple_reward'] = np.random.choice((self._reward[0], self._reward[1]))
        if self.curtain[player_position]:
            self._last_pickup[player_position] = the_plot.frame
            self.curtain[player_position] = False
            if not self._fix_apple_reward_in_episode:
                the_plot.add_reward(np.random.uniform(*self._reward))
            else:
                the_plot.add_reward(the_plot['sampled_apple_reward'])
        if self._respawn_every:
            respawn_cond = the_plot.frame > self._last_pickup + self._respawn_every
            respawn_cond &= self._last_pickup >= 0
            self.curtain[respawn_cond] = True

def update(self, actions, board, layers, backdrop, things, the_plot):
    player_position = things[PLAYER].position
    if self._fix_apple_reward_in_episode and (not the_plot.get('sampled_apple_reward', None)):
        the_plot['sampled_apple_reward'] = np.random.choice((self._reward[0], self._reward[1]))
    if self.curtain[player_position]:
        self._last_pickup[player_position] = the_plot.frame
        self.curtain[player_position] = False
        if not self._fix_apple_reward_in_episode:
            the_plot.add_reward(np.random.uniform(*self._reward))
        else:
            the_plot.add_reward(the_plot['sampled_apple_reward'])
    if self._respawn_every:
        respawn_cond = the_plot.frame > self._last_pickup + self._respawn_every
        respawn_cond &= self._last_pickup >= 0
        self.curtain[respawn_cond] = True

class TimerSprite(plab_things.Sprite):
    """Sprite for the timer.

    The timer is in charge of stopping the current chapter. Timer sprite should be
    placed last in the update order to make sure everything is updated before the
    chapter terminates.
    """

    def __init__(self, corner, position, character, max_frames, track_chapter_reward=False):
        super(TimerSprite, self).__init__(corner, position, character)
        if not isinstance(max_frames, int):
            raise ValueError('max_frames must be of type integer.')
        self._max_frames = max_frames
        self._visible = False
        self._track_chapter_reward = track_chapter_reward
        self._total_chapter_reward = 0.0

    def update(self, actions, board, layers, backdrop, things, the_plot):
        directives = the_plot._get_engine_directives()
        if self._track_chapter_reward:
            self._total_chapter_reward += directives.summed_reward or 0.0
        if the_plot.frame >= self._max_frames or directives.game_over:
            if self._track_chapter_reward:
                the_plot['chapter_reward'] = self._total_chapter_reward
            the_plot.terminate_episode()

def update(self, actions, board, layers, backdrop, things, the_plot):
    directives = the_plot._get_engine_directives()
    if self._track_chapter_reward:
        self._total_chapter_reward += directives.summed_reward or 0.0
    if the_plot.frame >= self._max_frames or directives.game_over:
        if self._track_chapter_reward:
            the_plot['chapter_reward'] = self._total_chapter_reward
        the_plot.terminate_episode()

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

