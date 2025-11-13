# Cluster 14

def now_str():
    now = datetime.datetime.now(dateutil.tz.tzlocal())
    return now.strftime('%m-%d:%H-%M:%S.%f')[:-4]

class FeatureExtractor(nn.Module):
    """one-layer MLP with relu
    Used for extracting features for vector-based observations/actions/rewards

    NOTE: https://pytorch.org/docs/stable/generated/torch.nn.Linear.html
    torch.linear is a linear transformation in the LAST dimension
    with weight of size (IN, OUT)
    which means it can support the input size larger than 2-dim, in the form
    of (*, IN), and then transform into (*, OUT) with same size (*)
    e.g. In the encoder, the input is (N, B, IN) where N=seq_len.
    """

    def __init__(self, input_size, output_size, activation_function):
        super(FeatureExtractor, self).__init__()
        self.output_size = output_size
        self.activation_function = activation_function
        if self.output_size != 0:
            self.fc = nn.Linear(input_size, output_size)
        else:
            self.fc = None

    def forward(self, inputs):
        if self.output_size != 0:
            return self.activation_function(self.fc(inputs))
        else:
            return ptu.zeros(0)

def forward(self, inputs):
    if self.output_size != 0:
        return self.activation_function(self.fc(inputs))
    else:
        return ptu.zeros(0)

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
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        dashes = '-' * (keywidth + valwidth + 7)
        dashes_time = put_in_middle(dashes, timestamp)
        lines = [dashes_time]
        for key, val in sorted(key2str.items()):
            lines.append('| %s%s | %s%s |' % (key, ' ' * (keywidth - len(key)), val, ' ' * (valwidth - len(val))))
        lines.append(dashes)
        self.file.write('\n'.join(lines) + '\n')
        self.file.flush()

    def _truncate(self, s):
        return s[:30] + '...' if len(s) > 33 else s

    def writeseq(self, seq):
        for arg in seq:
            self.file.write(arg + ' ')
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
    now = datetime.datetime.now(dateutil.tz.tzlocal())
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S.%f %Z')
    dashes = '-' * (keywidth + valwidth + 7)
    dashes_time = put_in_middle(dashes, timestamp)
    lines = [dashes_time]
    for key, val in sorted(key2str.items()):
        lines.append('| %s%s | %s%s |' % (key, ' ' * (keywidth - len(key)), val, ' ' * (valwidth - len(val))))
    lines.append(dashes)
    self.file.write('\n'.join(lines) + '\n')
    self.file.flush()

def writeseq(self, seq):
    for arg in seq:
        self.file.write(arg + ' ')
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
        extra_keys = list(OrderedSet(kvs.keys()) - OrderedSet(self.keys))
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
    extra_keys = list(OrderedSet(kvs.keys()) - OrderedSet(self.keys))
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

class TensorBoardOutputFormat(KVWriter):
    """
    Dumps key/value pairs into TensorBoard's numeric format.
    """

    def __init__(self, dir):
        os.makedirs(dir, exist_ok=True)
        self.step = 0
        self.writer = SummaryWriter(dir)

    def writekvs(self, kvs):
        for k, v in kvs.items():
            self.writer.add_scalar(k, v, self.step)
        self.writer.flush()

    def add_figure(self, tag, figure):
        self.writer.add_figure(tag, figure, self.step)

    def set_step(self, step):
        self.step = step

    def close(self):
        if self.writer:
            self.writer.Close()
            self.writer = None

def writekvs(self, kvs):
    for k, v in kvs.items():
        self.writer.add_scalar(k, v, self.step)
    self.writer.flush()

def add_figure(self, tag, figure):
    self.writer.add_figure(tag, figure, self.step)

def logkv(key, val):
    """
    Log a value of some diagnostic
    Call this once for each diagnostic quantity, each iteration
    If called many times, last value will be used.
    """
    Logger.CURRENT.logkv(key, val)

def logkvs(d):
    """
    Log a dictionary of key-value pairs
    """
    for k, v in d.items():
        logkv(k, v)

def add_figure(*args):
    """
    add_figure for tensorboard
    """
    Logger.CURRENT.add_figure(*args)

class ProfileKV:
    """
    Usage:
    with logger.ProfileKV("interesting_scope"):
        code
    """

    def __init__(self, n):
        self.n = 'wait_' + n

    def __enter__(self):
        self.t1 = time.time()

    def __exit__(self, type, value, traceback):
        Logger.CURRENT.name2val[self.n] += time.time() - self.t1

def __enter__(self):
    self.t1 = time.time()

def __exit__(self, type, value, traceback):
    Logger.CURRENT.name2val[self.n] += time.time() - self.t1

class Logger(object):
    DEFAULT = None
    CURRENT = None

    def __init__(self, dir, output_formats, precision=None):
        self.name2val = OrderedDict()
        self.level = INFO
        self.dir = dir
        self.output_formats = output_formats
        self.precision = precision

    def logkv(self, key, val):
        if self.precision is not None and isinstance(val, float):
            self.name2val[key] = round(val, self.precision)
        else:
            self.name2val[key] = val

    def add_figure(self, *args):
        for fmt in self.output_formats:
            if isinstance(fmt, TensorBoardOutputFormat):
                fmt.add_figure(*args)

    def set_tb_step(self, step):
        for fmt in self.output_formats:
            if isinstance(fmt, TensorBoardOutputFormat):
                fmt.set_step(step)

    def dumpkvs(self):
        if self.level == DISABLED:
            return
        for fmt in self.output_formats:
            if isinstance(fmt, KVWriter):
                fmt.writekvs(self.name2val)
        self.name2val.clear()

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

def add_figure(self, *args):
    for fmt in self.output_formats:
        if isinstance(fmt, TensorBoardOutputFormat):
            fmt.add_figure(*args)

def _do_log(self, args):
    for fmt in self.output_formats:
        if isinstance(fmt, SeqWriter):
            fmt.writeseq(map(str, args))

def configure(dir=None, format_strs=None, log_suffix='', precision=None):
    if dir is None:
        dir = os.getenv('OPENAI_LOGDIR')
    if dir is None:
        dir = osp.join(tempfile.gettempdir(), datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    assert isinstance(dir, str)
    os.makedirs(dir, exist_ok=True)
    if format_strs is None:
        strs = os.getenv('OPENAI_LOG_FORMAT')
        format_strs = strs.split(',') if strs else LOG_OUTPUT_FORMATS
    output_formats = [make_output_format(f, dir, log_suffix) for f in format_strs]
    Logger.CURRENT = Logger(dir=dir, output_formats=output_formats, precision=precision)
    log('Logging to %s' % dir)

class TimeLimit(TimeLimitBase):
    """Updated to support reset() with reset_params flag for Adaptive"""

    def reset(self, reset_params=True):
        self._episode_started_at = time.time()
        self._elapsed_steps = 0
        return self.env.reset(reset_params)

def reset(self, reset_params=True):
    self._episode_started_at = time.time()
    self._elapsed_steps = 0
    return self.env.reset(reset_params)

class SpaceInvadersWorld(PhysicalWorld):
    missile_class = Missile
    shield_class = Shield
    player_ship_class = PlayerShip
    invader_class = LeftRightMovingInvader
    n_actions = 4
    parameters_player_missile = {'class': PlayerMissile, 'fire_rate': 20, 'max_missiles': 2, 'missile_impulse': 100}
    parameters_invader_missile = {'class': InvaderMissile, 'fire_rate': 15, 'max_missiles': 10, 'missile_impulse': 100}
    invaders_per_row = 11

    def create_world(self, parent):
        p_width = self._width / self.physical_scale
        p_height = self._height / self.physical_scale
        ground = self._engine.CreateStaticBody(position=(0, 0))
        ground.CreateEdgeFixture(vertices=[(0, 0), (0, p_height)])
        ground.CreateEdgeFixture(vertices=[(0, 0), (p_width, 0)])
        ground.CreateEdgeFixture(vertices=[(0, p_height), (p_width, p_height)])
        ground.CreateEdgeFixture(vertices=[(p_width, p_height), (p_width, 0)])
        self._ground = ground
        self.create_invaders()
        self.create_shields()
        self.player_ship = self.player_ship_class(world=self, position=self.initial_player_ship_position())
        parent.add(self.player_ship)

    def create_shields(self):
        """Create protective shields."""
        for config in self.initial_shield_configuration():
            shield = self.shield_class(world=self, **config)
            self._batch.add(shield)

    def create_invaders(self):
        """Create invader grid."""
        offset_x = 80
        offset_y = self.initial_invader_row()
        for row, invader_type in enumerate(self.initial_invader_configuration()):
            for column in range(self.invaders_per_row):
                invader = self.invader_class(world=self, position=(offset_x, offset_y), invader_type=invader_type)
                self._batch.add(invader)
                offset_x += 48
            offset_x = 80
            offset_y -= invader.height * 2

    def fire_missile(self, entity, parameters):

        def count_missiles(node):
            if not isinstance(node, parameters['class']):
                return
            return 1
        if sum(self.walk(count_missiles)) >= parameters['max_missiles']:
            return
        last_fire_step = self._last_fire_step.get(parameters['class'], 0)
        if self._step - last_fire_step <= parameters['fire_rate']:
            return
        self._last_fire_step[parameters['class']] = self._step
        missile = parameters['class'].fire(world=self, entity=entity, impulse=parameters['missile_impulse'])
        self._batch.add(missile)

    @property
    def lives(self):
        return self._lives

    @property
    def score(self):
        return self._score

    @property
    def parameters(self):
        parameters = super(SpaceInvadersWorld, self).parameters
        parameters.update({'world': 'space_invaders'})
        return parameters

    def ship_impulse(self):
        """Relative paddle impulse strength on movement actions."""
        return 50

    def act(self, action):
        """Perform external action."""
        if action == 0:
            pass
        elif action == 1:
            self.player_ship.apply_impulse((-self.ship_impulse() / self.physical_scale * self.player_ship.body.mass, 0))
        elif action == 2:
            self.player_ship.apply_impulse((self.ship_impulse() / self.physical_scale * self.player_ship.body.mass, 0))
        elif action == 3:
            self.fire_missile(self.player_ship, self.parameters_player_missile)

    def initial_shield_configuration(self):
        return [{'health': 20, 'position': (self._width // 4, 200)}, {'health': 20, 'position': (2 * self._width // 4, 200)}, {'health': 20, 'position': (3 * self._width // 4, 200)}]

    def initial_invader_row(self):
        return self._height - 50

    def initial_invader_configuration(self):
        return [Invader.TYPE_1, Invader.TYPE_2, Invader.TYPE_2, Invader.TYPE_3, Invader.TYPE_3]

    def initial_player_ship_position(self):
        """Initial player ship position after reset."""
        return (self._width / 2, 25)

    def adjust_invader_missiles(self, n_invaders):
        """Adjust invader missile inventory."""
        if n_invaders >= 45:
            missiles = 10
        elif n_invaders >= 40:
            missiles = 9
        elif n_invaders >= 35:
            missiles = 8
        elif n_invaders >= 30:
            missiles = 7
        elif n_invaders >= 25:
            missiles = 6
        else:
            missiles = 5
        self.parameters_invader_missile['max_missiles'] = missiles

    def add_kill_score(self):
        """Add score when an invader is killed."""
        self._score += 1

    def reset_world(self):
        """Reset the game."""
        super(SpaceInvadersWorld, self).reset_world()
        self._lives = 3
        self._score = 0
        self._step = 0
        self._last_fire_step = {}

        def remove_nodes(node):
            if isinstance(node, (Missile, Invader, Shield)):
                node.kill()
        self.walk(remove_nodes)
        self.create_invaders()
        self.create_shields()
        self.player_ship.kill()
        self.player_ship = self.player_ship_class(world=self, position=self.initial_player_ship_position())
        self._batch.add(self.player_ship)

    def step(self):
        """Perform one environment update step."""
        if self._lives <= 0:
            self.reset_world()
        self._terminal = False
        self._step += 1

        def collect_invaders(node):
            if isinstance(node, self.invader_class):
                return node
        invaders = self.walk(collect_invaders)
        n_invaders = len(invaders)
        if invaders:
            invader = invaders[self.np_random.randint(0, n_invaders)]
            self.fire_missile(invader, self.parameters_invader_missile)
        self.adjust_invader_missiles(n_invaders)
        super(SpaceInvadersWorld, self).step()
        if self._lives <= 0 or not n_invaders:
            self._terminal = True

def create_invaders(self):
    """Create invader grid."""
    offset_x = 80
    offset_y = self.initial_invader_row()
    for row, invader_type in enumerate(self.initial_invader_configuration()):
        for column in range(self.invaders_per_row):
            invader = self.invader_class(world=self, position=(offset_x, offset_y), invader_type=invader_type)
            self._batch.add(invader)
            offset_x += 48
        offset_x = 80
        offset_y -= invader.height * 2

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

def all(self):
    return self.env_specs.values()

class MonitorParameters(gym.Wrapper):
    """Environment wrapper which records all environment parameters."""
    current_parameters = None

    def __init__(self, env, output_filename):
        """
        Construct parameter monitor wrapper.

        :param env: Wrapped environment
        :param output_filename: Output log filename
        """
        self._output_filename = output_filename
        with open(output_filename, 'w'):
            pass
        super(MonitorParameters, self).__init__(env)

    def step(self, action):
        result = self.env.step(action)
        self.record_parameters()
        return result

    def reset(self):
        result = self.env.reset()
        self.record_parameters()
        return result

    def record_parameters(self):
        """Record current environment parameters."""
        if not hasattr(self.env.unwrapped, 'parameters'):
            return
        if self.env.unwrapped.parameters == self.current_parameters:
            return
        self.current_parameters = self.env.unwrapped.parameters
        with open(self._output_filename, 'a') as output_file:
            output_file.write(json.dumps(self.current_parameters))
            output_file.write('\n')

def record_parameters(self):
    """Record current environment parameters."""
    if not hasattr(self.env.unwrapped, 'parameters'):
        return
    if self.env.unwrapped.parameters == self.current_parameters:
        return
    self.current_parameters = self.env.unwrapped.parameters
    with open(self._output_filename, 'a') as output_file:
        output_file.write(json.dumps(self.current_parameters))
        output_file.write('\n')

class Game(game.AbstractGame):
    """Key To Door Game."""

    def __init__(self, rng, num_apples=10, apple_reward=(1, 10), fix_apple_reward_in_episode=True, final_reward=10.0, respawn_every=common.DEFAULT_APPLE_RESPAWN_TIME, crop=True, max_frames=MAX_FRAMES_PER_PHASE_SR, REWARD_GRID=REWARD_GRID_SR):
        del rng
        self._num_apples = num_apples
        self._apple_reward = apple_reward
        self._fix_apple_reward_in_episode = fix_apple_reward_in_episode
        self._final_reward = final_reward
        self._respawn_every = respawn_every
        self._crop = crop
        self._max_frames = max_frames
        self._episode_length = sum(self._max_frames.values())
        self._REWARD_GRID = REWARD_GRID
        self._num_actions = common.NUM_ACTIONS
        self._colours = common.FIXED_COLOURS.copy()
        self._colours.update(COLOURS)
        self._extra_observation_fields = ['chapter_reward_as_string']

    @property
    def extra_observation_fields(self):
        """The field names of extra observations."""
        return self._extra_observation_fields

    @property
    def num_actions(self):
        """Number of possible actions in the game."""
        return self._num_actions

    @property
    def episode_length(self):
        return self._episode_length

    @property
    def colours(self):
        """Symbol to colour map for key to door."""
        return self._colours

    def _make_explore_phase(self):
        explore_grid = common.keep_n_characters_in_grid(EXPLORE_GRID, common.KEY, 1)
        explore_grid = common.keep_n_characters_in_grid(explore_grid, common.PLAYER, 1)
        return ascii_art.ascii_art_to_game(art=explore_grid, what_lies_beneath=' ', sprites={common.PLAYER: PlayerSprite, common.KEY: KeySprite, common.INDICATOR: ascii_art.Partial(objects.IndicatorObjectSprite, char_to_track=common.KEY, override_position=(0, 5)), common.TIMER: ascii_art.Partial(common.TimerSprite, self._max_frames['explore'])}, update_schedule=[common.PLAYER, common.KEY, common.INDICATOR, common.TIMER], z_order=[common.KEY, common.INDICATOR, common.PLAYER, common.TIMER])

    def _make_distractor_phase(self):
        return common.distractor_phase(player_sprite=PlayerSprite, num_apples=self._num_apples, max_frames=self._max_frames['distractor'], apple_reward=self._apple_reward, fix_apple_reward_in_episode=self._fix_apple_reward_in_episode, respawn_every=self._respawn_every)

    def _make_reward_phase(self):
        reward_grid = common.keep_n_characters_in_grid(self._REWARD_GRID, common.DOOR, 1)
        reward_grid = common.keep_n_characters_in_grid(reward_grid, common.PLAYER, 1)
        return ascii_art.ascii_art_to_game(art=reward_grid, what_lies_beneath=' ', sprites={common.PLAYER: PlayerSprite, common.DOOR: ascii_art.Partial(DoorSprite, pickup_reward=self._final_reward), common.TIMER: ascii_art.Partial(common.TimerSprite, self._max_frames['reward'], track_chapter_reward=True)}, update_schedule=[common.PLAYER, common.DOOR, common.TIMER], z_order=[common.PLAYER, common.DOOR, common.TIMER])

    def make_episode(self):
        """Factory method for generating new episodes of the game."""
        if self._crop:
            croppers = common.get_cropper()
        else:
            croppers = None
        return storytelling.Story([self._make_explore_phase, self._make_distractor_phase, self._make_reward_phase], croppers=croppers)

def __init__(self, rng, num_apples=10, apple_reward=(1, 10), fix_apple_reward_in_episode=True, final_reward=10.0, respawn_every=common.DEFAULT_APPLE_RESPAWN_TIME, crop=True, max_frames=MAX_FRAMES_PER_PHASE_SR, REWARD_GRID=REWARD_GRID_SR):
    del rng
    self._num_apples = num_apples
    self._apple_reward = apple_reward
    self._fix_apple_reward_in_episode = fix_apple_reward_in_episode
    self._final_reward = final_reward
    self._respawn_every = respawn_every
    self._crop = crop
    self._max_frames = max_frames
    self._episode_length = sum(self._max_frames.values())
    self._REWARD_GRID = REWARD_GRID
    self._num_actions = common.NUM_ACTIONS
    self._colours = common.FIXED_COLOURS.copy()
    self._colours.update(COLOURS)
    self._extra_observation_fields = ['chapter_reward_as_string']

class Mlp(PyTorchModule):

    def __init__(self, hidden_sizes, output_size, input_size, init_w=0.003, hidden_activation=F.relu, output_activation=ptu.identity, hidden_init=ptu.fanin_init, b_init_value=0.1, layer_norm=False, layer_norm_kwargs=None):
        self.save_init_params(locals())
        super().__init__()
        if layer_norm_kwargs is None:
            layer_norm_kwargs = dict()
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_sizes = hidden_sizes
        self.hidden_activation = hidden_activation
        self.output_activation = output_activation
        self.layer_norm = layer_norm
        self.fcs = []
        self.layer_norms = []
        in_size = input_size
        for i, next_size in enumerate(hidden_sizes):
            fc = nn.Linear(in_size, next_size)
            in_size = next_size
            hidden_init(fc.weight)
            fc.bias.data.fill_(b_init_value)
            self.__setattr__('fc{}'.format(i), fc)
            self.fcs.append(fc)
            if self.layer_norm:
                ln = LayerNorm(next_size)
                self.__setattr__('layer_norm{}'.format(i), ln)
                self.layer_norms.append(ln)
        self.last_fc = nn.Linear(in_size, output_size)
        self.last_fc.weight.data.uniform_(-init_w, init_w)
        self.last_fc.bias.data.uniform_(-init_w, init_w)

    def forward(self, input, return_preactivations=False):
        h = input
        for i, fc in enumerate(self.fcs):
            h = fc(h)
            if self.layer_norm and i < len(self.fcs) - 1:
                h = self.layer_norms[i](h)
            h = self.hidden_activation(h)
        preactivation = self.last_fc(h)
        output = self.output_activation(preactivation)
        if return_preactivations:
            return (output, preactivation)
        else:
            return output

def forward(self, input, return_preactivations=False):
    h = input
    for i, fc in enumerate(self.fcs):
        h = fc(h)
        if self.layer_norm and i < len(self.fcs) - 1:
            h = self.layer_norms[i](h)
        h = self.hidden_activation(h)
    preactivation = self.last_fc(h)
    output = self.output_activation(preactivation)
    if return_preactivations:
        return (output, preactivation)
    else:
        return output

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

def _start_training(self):
    self._n_env_steps_total = 0
    self._n_env_steps_total_last = 0
    self._n_rl_update_steps_total = 0
    self._n_rollouts_total = 0
    self._successes_in_buffer = 0
    self._start_time = time.time()
    self._start_time_last = time.time()

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

def forward(self, obs):
    """
        :param obs: Observation, usually 2D (B, dim), but maybe 3D (T, B, dim)
        return action (*, dim)
        """
    x = self.preprocess(obs)
    return super().forward(x)

class TanhGaussianPolicy(MarkovPolicyBase):
    """
    Usage: SAC
    ```
    policy = TanhGaussianPolicy(...)
    action, mean, log_std, _ = policy(obs)
    action, mean, log_std, _ = policy(obs, deterministic=True)
    action, mean, log_std, log_prob = policy(obs, return_log_prob=True)
    ```
    Here, mean and log_std are the mean and log_std of the Gaussian that is
    sampled from.
    If deterministic is True, action = tanh(mean).
    If return_log_prob is False (default), log_prob = None
        This is done because computing the log_prob can be a bit expensive.
    NOTE: action space must be [-1,1]^d
    """

    def __init__(self, obs_dim, action_dim, hidden_sizes, std=None, init_w=0.001, image_encoder=None, **kwargs):
        self.save_init_params(locals())
        super().__init__(obs_dim, action_dim, hidden_sizes, init_w, image_encoder, **kwargs)
        self.log_std = None
        self.std = std
        if std is None:
            last_hidden_size = self.input_size
            if len(hidden_sizes) > 0:
                last_hidden_size = hidden_sizes[-1]
            self.last_fc_log_std = nn.Linear(last_hidden_size, action_dim)
            self.last_fc_log_std.weight.data.uniform_(-init_w, init_w)
            self.last_fc_log_std.bias.data.uniform_(-init_w, init_w)
        else:
            self.log_std = np.log(std)
            assert LOG_SIG_MIN <= self.log_std <= LOG_SIG_MAX

    def forward(self, obs, reparameterize=True, deterministic=False, return_log_prob=False):
        """
        :param obs: Observation, usually 2D (B, dim), but maybe 3D (T, B, dim)
        :param deterministic: If True, do not sample
        :param return_log_prob: If True, return a sample and its log probability
        """
        h = self.preprocess(obs)
        for fc in self.fcs:
            h = self.hidden_activation(fc(h))
        mean = self.last_fc(h)
        if self.std is None:
            log_std = self.last_fc_log_std(h)
            log_std = torch.clamp(log_std, LOG_SIG_MIN, LOG_SIG_MAX)
            std = torch.exp(log_std)
        else:
            std = self.std
            log_std = self.log_std
        log_prob = None
        if deterministic:
            action = torch.tanh(mean)
            assert return_log_prob == False
        else:
            tanh_normal = TanhNormal(mean, std)
            if return_log_prob:
                if reparameterize:
                    action, pre_tanh_value = tanh_normal.rsample(return_pretanh_value=True)
                else:
                    action, pre_tanh_value = tanh_normal.sample(return_pretanh_value=True)
                log_prob = tanh_normal.log_prob(action, pre_tanh_value=pre_tanh_value)
                log_prob = log_prob.sum(dim=-1, keepdim=True)
            elif reparameterize:
                action = tanh_normal.rsample()
            else:
                action = tanh_normal.sample()
        return (action, mean, log_std, log_prob)

def forward(self, obs, reparameterize=True, deterministic=False, return_log_prob=False):
    """
        :param obs: Observation, usually 2D (B, dim), but maybe 3D (T, B, dim)
        :param deterministic: If True, do not sample
        :param return_log_prob: If True, return a sample and its log probability
        """
    h = self.preprocess(obs)
    for fc in self.fcs:
        h = self.hidden_activation(fc(h))
    mean = self.last_fc(h)
    if self.std is None:
        log_std = self.last_fc_log_std(h)
        log_std = torch.clamp(log_std, LOG_SIG_MIN, LOG_SIG_MAX)
        std = torch.exp(log_std)
    else:
        std = self.std
        log_std = self.log_std
    log_prob = None
    if deterministic:
        action = torch.tanh(mean)
        assert return_log_prob == False
    else:
        tanh_normal = TanhNormal(mean, std)
        if return_log_prob:
            if reparameterize:
                action, pre_tanh_value = tanh_normal.rsample(return_pretanh_value=True)
            else:
                action, pre_tanh_value = tanh_normal.sample(return_pretanh_value=True)
            log_prob = tanh_normal.log_prob(action, pre_tanh_value=pre_tanh_value)
            log_prob = log_prob.sum(dim=-1, keepdim=True)
        elif reparameterize:
            action = tanh_normal.rsample()
        else:
            action = tanh_normal.sample()
    return (action, mean, log_std, log_prob)

