# Cluster 18

def vertices(N):
    """N-dimensional cube vertices -- for latent space debug
    this is 2^N binary vector"""
    return list(product((1, -1), repeat=N))

def save_obj(obj, folder, name):
    filename = os.path.join(folder, name + '.pkl')
    with open(filename, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(folder, name):
    filename = os.path.join(folder, name + '.pkl')
    with open(filename, 'rb') as f:
        return pickle.load(f)

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

def __init__(self, filename_or_file):
    if isinstance(filename_or_file, str):
        self.file = open(filename_or_file, 'wt')
        self.own_file = True
    else:
        assert hasattr(filename_or_file, 'read'), 'expected file or str, got %s' % filename_or_file
        self.file = filename_or_file
        self.own_file = False

def close(self):
    if self.own_file:
        self.file.close()

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

def __init__(self, filename):
    self.file = open(filename, 'wt')

def close(self):
    self.file.close()

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

def __init__(self, filename):
    self.file = open(filename, 'w+t')
    self.keys = []
    self.sep = ','

def close(self):
    self.file.close()

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

def __init__(self, dir):
    os.makedirs(dir, exist_ok=True)
    self.step = 0
    self.writer = SummaryWriter(dir)

def make_output_format(format, ev_dir, log_suffix=''):
    os.makedirs(ev_dir, exist_ok=True)
    if format == 'stdout':
        return HumanOutputFormat(sys.stdout)
    elif format == 'log':
        return HumanOutputFormat(osp.join(ev_dir, 'experiment%s.log' % log_suffix))
    elif format == 'json':
        return JSONOutputFormat(osp.join(ev_dir, 'progress.json'))
    elif format == 'csv':
        return CSVOutputFormat(osp.join(ev_dir, 'progress.csv'))
    elif format == 'tensorboard':
        return TensorBoardOutputFormat(ev_dir)
    else:
        raise ValueError('Unknown format specified: %s' % (format,))

def get_dir():
    """
    Get directory that log files are being written to.
    will be None if there is no output directory (i.e., if you didn't call start)
    """
    return Logger.CURRENT.get_dir()

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

def close(self):
    for fmt in self.output_formats:
        fmt.close()

def wrapper(env, config):
    scenario = os.path.join(ASSET_PATH, config['scenario'])
    map_name = config.get('map', 'MAP01').upper()
    cache_key = (scenario, map_name)
    if cache_key not in _MAP_CACHE:
        wad = omg.WadIO(scenario)
        editor = omg.UDMFMapEditor(wad)
        editor.load(map_name)
        _MAP_CACHE[cache_key] = editor
    else:
        editor = _MAP_CACHE[cache_key]
    editor = copy.deepcopy(editor)
    sampler(env, config, editor)
    updated_wad = tempfile.mktemp(suffix='.wad')
    editor.save(updated_wad)
    return updated_wad

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

def load(name):
    entry_point = pkg_resources.EntryPoint.parse('x={}'.format(name))
    result = entry_point.load(False)
    return result

class RoboschoolXMLModifierMixin:
    """Mixin with XML modification methods."""

    @contextlib.contextmanager
    def modify_xml(self, asset):
        """Context manager allowing XML asset modifcation."""
        tree = ET.parse(os.path.join(ROBOSCHOOL_ASSETS, asset))
        yield tree
        fd, path = tempfile.mkstemp(suffix='.xml')
        os.close(fd)
        tree.write(path)
        if os.path.isfile(self.model_xml):
            os.remove(self.model_xml)
        self.model_xml = path

    def __del__(self):
        """Deletes last remaining xml files after use"""
        if os.path.isfile(self.model_xml):
            os.remove(self.model_xml)

@contextlib.contextmanager
def modify_xml(self, asset):
    """Context manager allowing XML asset modifcation."""
    tree = ET.parse(os.path.join(ROBOSCHOOL_ASSETS, asset))
    yield tree
    fd, path = tempfile.mkstemp(suffix='.xml')
    os.close(fd)
    tree.write(path)
    if os.path.isfile(self.model_xml):
        os.remove(self.model_xml)
    self.model_xml = path

def __del__(self):
    """Deletes last remaining xml files after use"""
    if os.path.isfile(self.model_xml):
        os.remove(self.model_xml)

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

def wrap_environment(wrapped_class, wrappers=None, **kwargs):
    """Helper for wrapping environment classes."""
    if wrappers is None:
        wrappers = []
    env_class = load(wrapped_class)
    env = env_class(**kwargs)
    for wrapper, wrapper_kwargs in wrappers:
        wrapper_class = load(wrapper)
        wrapper = wrapper_class(**wrapper_kwargs)
        env = wrapper(env)
    return env

def replace_grid_symbols(grid, old_to_new_map):
    """Replaces symbols in the grid.

    If mapping is not defined the symbol is not updated.

    Args:
      grid: Represented as a list of strings.
      old_to_new_map: Mapping between symbols.

    Returns:
      Updated grid.
    """

    def symbol_map(x):
        if x in old_to_new_map:
            return old_to_new_map[x]
        return x
    new_grid = []
    for row in grid:
        new_grid.append(''.join((symbol_map(i) for i in row)))
    return new_grid

def mujoco_wrapper(entry_point, **kwargs):
    env_cls = load(entry_point)
    env = env_cls(**kwargs)
    return env

class MujocoEnv(mujoco_env.MujocoEnv, Serializable):
    """
    My own wrapper around MujocoEnv.

    The caller needs to declare
    """

    def __init__(self, model_path, frame_skip=1, model_path_is_local=True, automatically_set_obs_and_action_space=False):
        if model_path_is_local:
            model_path = get_asset_xml(model_path)
        if automatically_set_obs_and_action_space:
            mujoco_env.MujocoEnv.__init__(self, model_path, frame_skip)
        else:
            "\n            Code below is copy/pasted from MujocoEnv's __init__ function.\n            "
            if model_path.startswith('/'):
                fullpath = model_path
            else:
                fullpath = os.path.join(os.path.dirname(__file__), 'assets', model_path)
            if not path.exists(fullpath):
                raise IOError('File %s does not exist' % fullpath)
            self.frame_skip = frame_skip
            self.model = mujoco_py.MjModel(fullpath)
            self.data = self.model.data
            self.viewer = None
            self.metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': int(np.round(1.0 / self.dt))}
            self.init_qpos = self.model.data.qpos.ravel().copy()
            self.init_qvel = self.model.data.qvel.ravel().copy()
            self._seed()

    def init_serialization(self, locals):
        Serializable.quick_init(self, locals)

    def log_diagnostics(self, paths):
        pass

def __init__(self, model_path, frame_skip=1, model_path_is_local=True, automatically_set_obs_and_action_space=False):
    if model_path_is_local:
        model_path = get_asset_xml(model_path)
    if automatically_set_obs_and_action_space:
        mujoco_env.MujocoEnv.__init__(self, model_path, frame_skip)
    else:
        "\n            Code below is copy/pasted from MujocoEnv's __init__ function.\n            "
        if model_path.startswith('/'):
            fullpath = model_path
        else:
            fullpath = os.path.join(os.path.dirname(__file__), 'assets', model_path)
        if not path.exists(fullpath):
            raise IOError('File %s does not exist' % fullpath)
        self.frame_skip = frame_skip
        self.model = mujoco_py.MjModel(fullpath)
        self.data = self.model.data
        self.viewer = None
        self.metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': int(np.round(1.0 / self.dt))}
        self.init_qpos = self.model.data.qpos.ravel().copy()
        self.init_qvel = self.model.data.qvel.ravel().copy()
        self._seed()

def get_asset_xml(xml_name):
    return os.path.join(ENV_ASSET_DIR, xml_name)

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

def round_tensor(tensor, n_digits):
    return (tensor * 10 ** n_digits).round() / 10 ** n_digits

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

def save_model(self, iter, perf):
    save_path = os.path.join(logger.get_dir(), 'save', f'agent_{iter}_perf{perf:.3f}.pt')
    torch.save(self.agent.state_dict(), save_path)

def load_model(self, ckpt_path):
    self.agent.load_state_dict(torch.load(ckpt_path, map_location=ptu.device))
    print('load successfully from', ckpt_path)

