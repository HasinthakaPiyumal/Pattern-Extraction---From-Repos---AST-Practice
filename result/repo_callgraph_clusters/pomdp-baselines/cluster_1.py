# Cluster 1

def sample_random_normal(dim, n_samples):
    return np.random.normal(size=(n_samples, dim))

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

def __init__(self, input_size, output_size, activation_function):
    super(FeatureExtractor, self).__init__()
    self.output_size = output_size
    self.activation_function = activation_function
    if self.output_size != 0:
        self.fc = nn.Linear(input_size, output_size)
    else:
        self.fc = None

class OrderedSet(Set):

    def __init__(self, iterable=()):
        self.d = OrderedDict.fromkeys(iterable)

    def __len__(self):
        return len(self.d)

    def __contains__(self, element):
        return element in self.d

    def __iter__(self):
        return iter(self.d)

def __len__(self):
    return len(self.d)

def put_in_middle(str1, str2):
    n = len(str1)
    m = len(str2)
    if n <= m:
        return str2
    else:
        start = (n - m) // 2
        return str1[:start] + str2 + str1[start + m:]

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

def _truncate(self, s):
    return s[:30] + '...' if len(s) > 33 else s

class DictWrapper(gym.ObservationWrapper):

    def __init__(self, env):
        super().__init__(env)

    def observation(self, obs_img):
        if len(obs_img.shape) == 1:
            return {'vecobs': obs_img}
        else:
            return {'image': obs_img}

def observation(self, obs_img):
    if len(obs_img.shape) == 1:
        return {'vecobs': obs_img}
    else:
        return {'image': obs_img}

class ModifiableRoboschoolHalfCheetah(RoboschoolHalfCheetah, RoboschoolTrackDistSuccessMixin):
    DEFAULT_DENSITY = 1000
    RANDOM_LOWER_DENSITY = 750
    RANDOM_UPPER_DENSITY = 1250
    EXTREME_LOWER_DENSITY = 500
    EXTREME_UPPER_DENSITY = 1500
    DEFAULT_FRICTION = 0.8
    RANDOM_LOWER_FRICTION = 0.5
    RANDOM_UPPER_FRICTION = 1.1
    EXTREME_LOWER_FRICTION = 0.2
    EXTREME_UPPER_FRICTION = 1.4
    DEFAULT_POWER = 0.9
    RANDOM_LOWER_POWER = 0.7
    RANDOM_UPPER_POWER = 1.1
    EXTREME_LOWER_POWER = 0.5
    EXTREME_UPPER_POWER = 1.3

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.density = self.DEFAULT_DENSITY
        self.friction = self.DEFAULT_FRICTION
        self.power = self.DEFAULT_POWER
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)
            print(tmp_hidden_states)
            print(self.observation_space.shape[0])

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        state = super()._reset()
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super()._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def get_hidden_states(self):
        hidden_states = np.array([self.density / self.DEFAULT_DENSITY, self.friction / self.DEFAULT_FRICTION, self.power / self.DEFAULT_POWER])
        return hidden_states.copy()

def __init__(self, oracle: bool=False, **kwargs):
    super().__init__(**kwargs)
    self.density = self.DEFAULT_DENSITY
    self.friction = self.DEFAULT_FRICTION
    self.power = self.DEFAULT_POWER
    self.oracle = oracle
    if oracle == True:
        print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
        self._reset()
        tmp_hidden_states = self.get_hidden_states()
        self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)
        print(tmp_hidden_states)
        print(self.observation_space.shape[0])

def get_obs(self, state):
    if self.oracle:
        hidden_states = self.get_hidden_states()
        state = np.concatenate([state, hidden_states])
        return state
    else:
        return state

class ModifiableRoboschoolHopper(RoboschoolHopper, RoboschoolTrackDistSuccessMixin):
    DEFAULT_DENSITY = 1000
    RANDOM_LOWER_DENSITY = 750
    RANDOM_UPPER_DENSITY = 1250
    EXTREME_LOWER_DENSITY = 500
    EXTREME_UPPER_DENSITY = 1500
    DEFAULT_FRICTION = 0.8
    RANDOM_LOWER_FRICTION = 0.5
    RANDOM_UPPER_FRICTION = 1.1
    EXTREME_LOWER_FRICTION = 0.2
    EXTREME_UPPER_FRICTION = 1.4
    DEFAULT_POWER = 0.75
    RANDOM_LOWER_POWER = 0.6
    RANDOM_UPPER_POWER = 0.9
    EXTREME_LOWER_POWER = 0.4
    EXTREME_UPPER_POWER = 1.1

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.density = self.DEFAULT_DENSITY
        self.friction = self.DEFAULT_FRICTION
        self.power = self.DEFAULT_POWER
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        state = super()._reset()
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super()._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def get_hidden_states(self):
        hidden_states = np.array([self.density / self.DEFAULT_DENSITY, self.friction / self.DEFAULT_FRICTION, self.power / self.DEFAULT_POWER])
        return hidden_states.copy()

def __init__(self, oracle: bool=False, **kwargs):
    super().__init__(**kwargs)
    self.density = self.DEFAULT_DENSITY
    self.friction = self.DEFAULT_FRICTION
    self.power = self.DEFAULT_POWER
    self.oracle = oracle
    if oracle == True:
        print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
        self._reset()
        tmp_hidden_states = self.get_hidden_states()
        self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

def get_obs(self, state):
    if self.oracle:
        hidden_states = self.get_hidden_states()
        state = np.concatenate([state, hidden_states])
        return state
    else:
        return state

class RandomNormalWalker2d_MRPO(RoboschoolXMLModifierMixin, ModifiableRoboschoolWalker2d_MRPO):

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        with self.modify_xml('walker2d.xml') as tree:
            for elem in tree.iterfind('default/geom'):
                elem.set('density', str(self.density) + ' .1 .1')
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        state = super(RandomNormalWalker2d_MRPO, self)._reset(new)
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super(RandomNormalWalker2d_MRPO, self)._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        parameters = super(RandomNormalWalker2d_MRPO, self).parameters
        parameters.update({'density': self.density, 'friction': self.friction})
        return parameters

    def get_hidden_states(self):
        hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
        return hidden_states.copy()

def __init__(self, oracle: bool=False, **kwargs):
    super().__init__(**kwargs)
    self.oracle = oracle
    if oracle == True:
        print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
        self._reset()
        tmp_hidden_states = self.get_hidden_states()
        self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

def get_obs(self, state):
    if self.oracle:
        hidden_states = self.get_hidden_states()
        state = np.concatenate([state, hidden_states])
        return state
    else:
        return state

class RandomNormalHalfCheetah_MRPO(RoboschoolXMLModifierMixin, ModifiableRoboschoolHalfCheetah_MRPO):

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        with self.modify_xml('half_cheetah.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        state = super(RandomNormalHalfCheetah_MRPO, self)._reset(new)
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super(RandomNormalHalfCheetah_MRPO, self)._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        parameters = super(RandomNormalHalfCheetah_MRPO, self).parameters
        parameters.update({'density': self.density, 'friction': self.friction})
        return parameters

    def get_hidden_states(self):
        hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
        return hidden_states.copy()

def __init__(self, oracle: bool=False, **kwargs):
    super().__init__(**kwargs)
    self.oracle = oracle
    if oracle == True:
        print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
        self._reset()
        tmp_hidden_states = self.get_hidden_states()
        self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

def get_obs(self, state):
    if self.oracle:
        hidden_states = self.get_hidden_states()
        state = np.concatenate([state, hidden_states])
        return state
    else:
        return state

class RandomNormalHopper_MRPO(RoboschoolXMLModifierMixin, ModifiableRoboschoolHopper_MRPO):

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        with self.modify_xml('hopper.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        state = super(RandomNormalHopper_MRPO, self)._reset(new)
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super(RandomNormalHopper_MRPO, self)._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        parameters = super(RandomNormalHopper_MRPO, self).parameters
        parameters.update({'density': self.density, 'friction': self.friction})
        return parameters

    def get_hidden_states(self):
        hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
        return hidden_states.copy()

def __init__(self, oracle: bool=False, **kwargs):
    super().__init__(**kwargs)
    self.oracle = oracle
    if oracle == True:
        print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
        self._reset()
        tmp_hidden_states = self.get_hidden_states()
        self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

def get_obs(self, state):
    if self.oracle:
        hidden_states = self.get_hidden_states()
        state = np.concatenate([state, hidden_states])
        return state
    else:
        return state

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

class POMDPWrapper(gym.Wrapper):

    def __init__(self, env, partially_obs_dims: list):
        super().__init__(env)
        self.partially_obs_dims = partially_obs_dims
        assert 0 < len(self.partially_obs_dims) <= self.observation_space.shape[0]
        self.observation_space = spaces.Box(low=self.observation_space.low[self.partially_obs_dims], high=self.observation_space.high[self.partially_obs_dims], dtype=np.float32)
        if self.env.action_space.__class__.__name__ == 'Box':
            self.act_continuous = True
        else:
            self.act_continuous = False

    def get_obs(self, state):
        return state[self.partially_obs_dims].copy()

    def reset(self):
        state = self.env.reset()
        return self.get_obs(state)

    def step(self, action):
        if self.act_continuous:
            action = np.clip(action, -1, 1)
            lb = self.env.action_space.low
            ub = self.env.action_space.high
            action = lb + (action + 1.0) * 0.5 * (ub - lb)
            action = np.clip(action, lb, ub)
        state, reward, done, info = self.env.step(action)
        return (self.get_obs(state), reward, done, info)

def __init__(self, env, partially_obs_dims: list):
    super().__init__(env)
    self.partially_obs_dims = partially_obs_dims
    assert 0 < len(self.partially_obs_dims) <= self.observation_space.shape[0]
    self.observation_space = spaces.Box(low=self.observation_space.low[self.partially_obs_dims], high=self.observation_space.high[self.partially_obs_dims], dtype=np.float32)
    if self.env.action_space.__class__.__name__ == 'Box':
        self.act_continuous = True
    else:
        self.act_continuous = False

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

class AntEnv(MujocoEnv):

    def __init__(self, use_low_gear_ratio=False):
        if use_low_gear_ratio:
            xml_path = 'low_gear_ratio_ant.xml'
        else:
            xml_path = 'ant.xml'
        super().__init__(xml_path, frame_skip=5, automatically_set_obs_and_action_space=True)

    def step(self, a):
        torso_xyz_before = self.get_body_com('torso')
        self.do_simulation(a, self.frame_skip)
        torso_xyz_after = self.get_body_com('torso')
        torso_velocity = torso_xyz_after - torso_xyz_before
        forward_reward = torso_velocity[0] / self.dt
        ctrl_cost = 0.0
        contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 0.0
        reward = forward_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        notdone = np.isfinite(state).all() and state[2] >= 0.2 and (state[2] <= 1.0)
        done = not notdone
        ob = self._get_obs()
        return (ob, reward, done, dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward, torso_velocity=torso_velocity))

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat[2:], self.sim.data.qvel.flat])

    def reset_model(self):
        qpos = self.init_qpos + self.np_random.uniform(size=self.model.nq, low=-0.1, high=0.1)
        qvel = self.init_qvel + self.np_random.randn(self.model.nv) * 0.1
        self.set_state(qpos, qvel)
        return self._get_obs()

    def viewer_setup(self):
        self.viewer.cam.distance = self.model.stat.extent * 0.5

def _get_obs(self):
    return np.concatenate([self.sim.data.qpos.flat[2:], self.sim.data.qvel.flat])

class HalfCheetahVelEnv(HalfCheetahEnv):
    """Half-cheetah environment with target velocity, as described in [1]. The
    code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand.py
    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each
    time step a reward composed of a control cost and a penalty equal to the
    difference between its current velocity and the target velocity. The tasks
    are generated by sampling the target velocities from the uniform
    distribution on [0, 3].
    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic
        Meta-Learning for Fast Adaptation of Deep Networks", 2017
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for
        model-based control", 2012
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """

    def __init__(self, task={}, n_tasks=2, max_episode_steps=200, **kwargs):
        self._task = task
        self.n_tasks = n_tasks
        self.tasks = self.sample_tasks(n_tasks)
        self._goal_vel = self.tasks[0].get('velocity', 0.0)
        self._goal = self._goal_vel
        self._max_episode_steps = max_episode_steps
        super(HalfCheetahVelEnv, self).__init__()

    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._goal_vel)
        ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, task=self._task)
        return (observation, reward, done, infos)

    def set_goal(self, goal):
        self._goal = np.asarray(goal)

    def sample_tasks(self, num_tasks):
        velocities = np.random.uniform(0.0, 3.0, size=(num_tasks,))
        tasks = [{'velocity': velocity} for velocity in velocities]
        return tasks

    def get_current_task(self):
        return np.array([self._goal_vel])

    def get_all_task_idx(self):
        return range(len(self.tasks))

    def reset_task(self, idx):
        self._task = self.tasks[idx]
        self._goal_vel = self._task['velocity']
        self._goal = self._goal_vel
        self.reset()

    def reward(self, state, action):
        """Here, state is previous state! r_t = r(s_{t-1}, a_t)
        NOTE: it should be r(st-1, at, st) though det dynamics
        """
        qpos = np.concatenate([np.array([0.0]), state[:8]])
        qvel = state[8:17]
        self.set_state(qpos, qvel)
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._goal_vel)
        ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
        reward = forward_reward - ctrl_cost
        return reward

def get_all_task_idx(self):
    return range(len(self.tasks))

class HumanoidDirEnv(HumanoidEnv):

    def __init__(self, n_tasks=None, max_episode_steps=200):
        self.n_tasks = n_tasks
        assert n_tasks == None
        self._goal = self._sample_raw_task()['goal']
        self._max_episode_steps = max_episode_steps
        super(HumanoidDirEnv, self).__init__()

    def step(self, action):
        pos_before = np.copy(mass_center(self.model, self.sim)[:2])
        self.do_simulation(action, self.frame_skip)
        pos_after = mass_center(self.model, self.sim)[:2]
        alive_bonus = 5.0
        data = self.sim.data
        goal_direction = (np.cos(self._goal), np.sin(self._goal))
        lin_vel_cost = 0.25 * np.sum(goal_direction * (pos_after - pos_before)) / self.model.opt.timestep
        quad_ctrl_cost = 0.1 * np.square(data.ctrl).sum()
        quad_impact_cost = 5e-07 * np.square(data.cfrc_ext).sum()
        quad_impact_cost = min(quad_impact_cost, 10)
        reward = lin_vel_cost - quad_ctrl_cost - quad_impact_cost + alive_bonus
        qpos = self.sim.data.qpos
        done = bool(qpos[2] < 1.0 or qpos[2] > 2.0)
        return (self._get_obs(), reward, done, dict(reward_linvel=lin_vel_cost, reward_quadctrl=-quad_ctrl_cost, reward_alive=alive_bonus, reward_impact=-quad_impact_cost))

    def _get_obs(self):
        data = self.sim.data
        return np.concatenate([data.qpos.flat[2:], data.qvel.flat, data.cinert.flat, data.cvel.flat, data.qfrc_actuator.flat, data.cfrc_ext.flat])

    def get_current_task(self):
        return np.array([np.cos(self._goal), np.sin(self._goal)])

    def _sample_raw_task(self):
        direction = np.random.uniform(0.0, 2.0 * np.pi)
        task = {'goal': direction}
        return task

    def reset_task(self, task_info):
        assert task_info is None
        self._goal = self._sample_raw_task()['goal']
        self.reset()

def _get_obs(self):
    data = self.sim.data
    return np.concatenate([data.qpos.flat[2:], data.qvel.flat, data.cinert.flat, data.cvel.flat, data.qfrc_actuator.flat, data.cfrc_ext.flat])

class MultitaskAntEnv(AntEnv):

    def __init__(self, task={}, n_tasks=2, **kwargs):
        self._task = task
        self.n_tasks = n_tasks
        if n_tasks is None:
            self._goal = self._sample_raw_task()['goal']
        else:
            self.tasks = self.sample_tasks(n_tasks)
            self._goal = self.tasks[0]['goal']
        super(MultitaskAntEnv, self).__init__()

    def get_current_task(self):
        return np.array([self._goal])

    def get_all_task_idx(self):
        return range(len(self.tasks))

    def reset_task(self, task_info):
        if self.n_tasks is None:
            assert task_info is None
            self._task = self._sample_raw_task()
        else:
            self._task = self.tasks[task_info]
        self._goal = self._task['goal']
        self.reset()

def get_all_task_idx(self):
    return range(len(self.tasks))

class WindEnv(Env):
    """
    point robot on a 2-D plane with position control
    tasks vary in noise term in dynamics for fixed goal-reaching
     - noise is fixed for a task
     - reward is sparse
    """

    def __init__(self, max_episode_steps=75, n_tasks=1, goal_radius=0.03, **kwargs):
        self.n_tasks = n_tasks
        self._max_episode_steps = max_episode_steps
        self.step_count = 0
        np.random.seed(1337)
        self.winds = [[np.random.uniform(-0.08, 0.08), np.random.uniform(-0.08, 0.08)] for _ in range(n_tasks)]
        self._goal = np.array([0.0, 1.0])
        self.goal_radius = goal_radius
        self.reset_task(0)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(2,), dtype=np.float32)

    def reset_task(self, idx):
        """reset goal AND reset the agent"""
        if idx is not None:
            self._wind = np.array(self.winds[idx])
        self.reset()

    def set_goal(self, wind):
        self._wind = np.asarray(wind)

    def get_current_task(self):
        return self._wind.copy()

    def get_all_task_idx(self):
        return range(len(self.winds))

    def reset_model(self):
        self._state = np.array([0.0, 0.0])
        return self._get_obs()

    def reset(self):
        self.step_count = 0
        return self.reset_model()

    def _get_obs(self):
        return np.copy(self._state)

    def step(self, action):
        self._state = self._state + action + self._wind
        if self.is_goal_state():
            reward = 1.0
        else:
            reward = 0.0
        self.step_count += 1
        if self.step_count >= self._max_episode_steps:
            done = True
        else:
            done = False
        ob = self._get_obs()
        return (ob, reward, done, dict())

    def viewer_setup(self):
        print('no viewer')
        pass

    def render(self):
        print('current state:', self._state)

    def is_goal_state(self):
        if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
            return True
        else:
            return False

    def plot_env(self):
        ax = plt.gca()
        plt.axis('scaled')
        ax.set_xlim(-1, 1)
        ax.set_ylim(-0.5, 1.5)
        plt.xticks([])
        plt.yticks([])
        circle = plt.Circle((self._goal[0], self._goal[1]), radius=self.goal_radius, alpha=0.3)
        ax.add_artist(circle)
        X, Y = np.meshgrid(np.linspace(-0.8, 1, 5), np.linspace(-0.4, 1.5, 5))
        plt.quiver(X, Y, [self._wind[0]], [self._wind[1]])

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)

def __init__(self, max_episode_steps=75, n_tasks=1, goal_radius=0.03, **kwargs):
    self.n_tasks = n_tasks
    self._max_episode_steps = max_episode_steps
    self.step_count = 0
    np.random.seed(1337)
    self.winds = [[np.random.uniform(-0.08, 0.08), np.random.uniform(-0.08, 0.08)] for _ in range(n_tasks)]
    self._goal = np.array([0.0, 1.0])
    self.goal_radius = goal_radius
    self.reset_task(0)
    self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)
    self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(2,), dtype=np.float32)

def get_all_task_idx(self):
    return range(len(self.winds))

def viewer_setup(self):
    print('no viewer')
    pass

def render(self):
    print('current state:', self._state)

class PointEnv(Env):
    """
    point robot on a 2-D plane with position control
    tasks (aka goals) are positions on the plane
     - tasks sampled from unit square
     - reward is L2 distance
    """

    def __init__(self, max_episode_steps=60, n_tasks=2, modify_init_state_dist=True, on_circle_init_state=True, **kwargs):
        self.n_tasks = n_tasks
        self._max_episode_steps = max_episode_steps
        self.step_count = 0
        self.modify_init_state_dist = modify_init_state_dist
        self.on_circle_init_state = on_circle_init_state
        goals = [[np.random.uniform(-1.0, 1.0), np.random.uniform(-1.0, 1.0)] for _ in range(n_tasks)]
        self.goals = goals
        self.reset_task(0)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(2,), dtype=np.float32)

    def reset_task(self, idx):
        """reset goal AND reset the agent"""
        if idx is not None:
            self._goal = np.array(self.goals[idx])
        self.reset()

    def set_goal(self, goal):
        self._goal = np.asarray(goal)

    def get_current_task(self):
        return self._goal.copy()

    def get_all_task_idx(self):
        return range(len(self.goals))

    def reset_model(self):
        self._state = np.random.uniform(-1.0, 1.0, size=(2,))
        return self._get_obs()

    def reset(self):
        self.step_count = 0
        return self.reset_model()

    def _get_obs(self):
        return np.copy(self._state)

    def step(self, action):
        self._state = self._state + action
        reward = -((self._state[0] - self._goal[0]) ** 2 + (self._state[1] - self._goal[1]) ** 2) ** 0.5
        self.step_count += 1
        if self.step_count >= self._max_episode_steps:
            done = True
        else:
            done = False
        ob = self._get_obs()
        return (ob, reward, done, dict())

    def reward(self, state, action=None):
        return -((state[0] - self._goal[0]) ** 2 + (state[1] - self._goal[1]) ** 2) ** 0.5

    def viewer_setup(self):
        print('no viewer')
        pass

    def render(self):
        print('current state:', self._state)

def __init__(self, max_episode_steps=60, n_tasks=2, modify_init_state_dist=True, on_circle_init_state=True, **kwargs):
    self.n_tasks = n_tasks
    self._max_episode_steps = max_episode_steps
    self.step_count = 0
    self.modify_init_state_dist = modify_init_state_dist
    self.on_circle_init_state = on_circle_init_state
    goals = [[np.random.uniform(-1.0, 1.0), np.random.uniform(-1.0, 1.0)] for _ in range(n_tasks)]
    self.goals = goals
    self.reset_task(0)
    self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)
    self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(2,), dtype=np.float32)

def get_all_task_idx(self):
    return range(len(self.goals))

def viewer_setup(self):
    print('no viewer')
    pass

def render(self):
    print('current state:', self._state)

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

def get_all_task_idx(self):
    return range(len(self.goals))

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

def num_complete_episodes(self):
    return len(self._episode_starts)

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

class ImageEncoder(nn.Module):

    def __init__(self, image_shape, embed_size=100, depths=[8, 16], kernel_size=2, stride=1, activation=relu_name, from_flattened=False, normalize_pixel=False):
        super(ImageEncoder, self).__init__()
        self.shape = image_shape
        self.kernel_size = kernel_size
        self.stride = stride
        self.depths = [image_shape[0]] + depths
        layers = []
        h_w = self.shape[-2:]
        for i in range(len(self.depths) - 1):
            layers.append(nn.Conv2d(self.depths[i], self.depths[i + 1], kernel_size, stride))
            layers.append(ACTIVATIONS[activation]())
            h_w = conv_output_shape(h_w, kernel_size, stride)
        self.cnn = nn.Sequential(*layers)
        self.linear = nn.Linear(h_w[0] * h_w[1] * self.depths[-1], embed_size)
        self.from_flattened = from_flattened
        self.normalize_pixel = normalize_pixel
        self.embed_size = embed_size

    def forward(self, image):
        if self.from_flattened:
            batch_size = image.shape[:-1]
            img_shape = [np.prod(batch_size)] + list(self.shape)
            image = torch.reshape(image, img_shape)
        else:
            batch_size = [image.shape[0]]
        if self.normalize_pixel:
            image = image / 255.0
        embed = self.cnn(image)
        embed = torch.reshape(embed, list(batch_size) + [-1])
        embed = self.linear(embed)
        return embed

def __init__(self, image_shape, embed_size=100, depths=[8, 16], kernel_size=2, stride=1, activation=relu_name, from_flattened=False, normalize_pixel=False):
    super(ImageEncoder, self).__init__()
    self.shape = image_shape
    self.kernel_size = kernel_size
    self.stride = stride
    self.depths = [image_shape[0]] + depths
    layers = []
    h_w = self.shape[-2:]
    for i in range(len(self.depths) - 1):
        layers.append(nn.Conv2d(self.depths[i], self.depths[i + 1], kernel_size, stride))
        layers.append(ACTIVATIONS[activation]())
        h_w = conv_output_shape(h_w, kernel_size, stride)
    self.cnn = nn.Sequential(*layers)
    self.linear = nn.Linear(h_w[0] * h_w[1] * self.depths[-1], embed_size)
    self.from_flattened = from_flattened
    self.normalize_pixel = normalize_pixel
    self.embed_size = embed_size

def forward(self, image):
    if self.from_flattened:
        batch_size = image.shape[:-1]
        img_shape = [np.prod(batch_size)] + list(self.shape)
        image = torch.reshape(image, img_shape)
    else:
        batch_size = [image.shape[0]]
    if self.normalize_pixel:
        image = image / 255.0
    embed = self.cnn(image)
    embed = torch.reshape(embed, list(batch_size) + [-1])
    embed = self.linear(embed)
    return embed

class Normal(Distribution):
    """
        Creates a normal (also called Gaussian) distribution parameterized by
        `mean` and `std`.
        Example::
            >>> m = Normal(torch.Tensor([0.0]), torch.Tensor([1.0]))
            >>> m.sample()  # normally distributed with mean=0 and stddev=1
             0.1046
            [torch.FloatTensor of size 1]
        Args:
            mean (float or Tensor or Variable): mean of the distribution
            std (float or Tensor or Variable): standard deviation of the distribution
        """

    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def sample(self):
        return torch.normal(self.mean, self.std)

    def sample_n(self, n):

        def expand(v):
            if isinstance(v, Number):
                return torch.Tensor([v]).expand(n, 1)
            else:
                return v.expand(n, *v.size())
        return torch.normal(expand(self.mean), expand(self.std))

    def log_prob(self, value):
        var = self.std ** 2
        log_std = math.log(self.std) if isinstance(self.std, Number) else self.std.log()
        return -(value - self.mean) ** 2 / (2 * var) - log_std - math.log(math.sqrt(2 * math.pi))

def sample(self):
    return torch.normal(self.mean, self.std)

def expand(v):
    if isinstance(v, Number):
        return torch.Tensor([v]).expand(n, 1)
    else:
        return v.expand(n, *v.size())

def sample_n(self, n):

    def expand(v):
        if isinstance(v, Number):
            return torch.Tensor([v]).expand(n, 1)
        else:
            return v.expand(n, *v.size())
    return torch.normal(expand(self.mean), expand(self.std))

def log_prob(self, value):
    var = self.std ** 2
    log_std = math.log(self.std) if isinstance(self.std, Number) else self.std.log()
    return -(value - self.mean) ** 2 / (2 * var) - log_std - math.log(math.sqrt(2 * math.pi))

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

def fanin_init(tensor):
    size = tensor.size()
    if len(size) == 2:
        fan_in = size[0]
    elif len(size) > 2:
        fan_in = np.prod(size[1:])
    else:
        raise Exception('Shape must be have dimension at least 2.')
    bound = 1.0 / np.sqrt(fan_in)
    return tensor.data.uniform_(-bound, bound)

def fanin_init_weights_like(tensor):
    size = tensor.size()
    if len(size) == 2:
        fan_in = size[0]
    elif len(size) > 2:
        fan_in = np.prod(size[1:])
    else:
        raise Exception('Shape must be have dimension at least 2.')
    bound = 1.0 / np.sqrt(fan_in)
    new_tensor = FloatTensor(tensor.size())
    new_tensor.uniform_(-bound, bound)
    return new_tensor

def normal(*args, **kwargs):
    return torch.normal(*args, **kwargs).to(device)

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

def __init__(self, obs_dim, action_dim, hidden_sizes, init_w=0.001, image_encoder=None, **kwargs):
    self.save_init_params(locals())
    self.action_dim = action_dim
    if image_encoder is None:
        self.input_size = obs_dim
    else:
        self.input_size = image_encoder.embed_size
    super().__init__(hidden_sizes, input_size=self.input_size, output_size=self.action_dim, init_w=init_w, **kwargs)
    self.image_encoder = image_encoder

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

