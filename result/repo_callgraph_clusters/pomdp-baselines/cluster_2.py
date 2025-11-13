# Cluster 2

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

def reset(self):
    obs = self.env.reset()
    self.episode = [obs.copy()]
    return obs

@sampler_with_map_editor
def sampler(env, config, editor):
    """Perform thing sampling.

        :param env: Environment instance
        :param config: Configuration dictionary
        :param editor: Map editor
        """
    for thing in editor.things:
        if thing.type not in modify_things:
            continue
        thing.type = int(env.np_random.choice(things))

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

def get_hidden_states(self):
    hidden_states = np.array([self.density / self.DEFAULT_DENSITY, self.friction / self.DEFAULT_FRICTION, self.power / self.DEFAULT_POWER])
    return hidden_states.copy()

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

def get_hidden_states(self):
    hidden_states = np.array([self.density / self.DEFAULT_DENSITY, self.friction / self.DEFAULT_FRICTION, self.power / self.DEFAULT_POWER])
    return hidden_states.copy()

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

def get_hidden_states(self):
    hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
    return hidden_states.copy()

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

def get_hidden_states(self):
    hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
    return hidden_states.copy()

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

def get_hidden_states(self):
    hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
    return hidden_states.copy()

class RandomStrongPushCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomStrongPushCartPole, self).__init__()
        self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomStrongPushCartPole, self).parameters
        parameters.update({'force': self.force_mag})
        return parameters

def reset(self, new=True):
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
    return np.array(self.state)

class RandomWeakPushCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomWeakPushCartPole, self).__init__()
        self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomWeakPushCartPole, self).parameters
        parameters.update({'force': self.force_mag})
        return parameters

def reset(self, new=True):
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
    return np.array(self.state)

class ModifiableMountainCarEnv(MountainCarEnv):
    """A variant of mountain car without hardcoded force/mass."""
    RANDOM_LOWER_FORCE = 0.0005
    RANDOM_UPPER_FORCE = 0.005
    EXTREME_LOWER_FORCE = 0.0001
    EXTREME_UPPER_FORCE = 0.01
    RANDOM_LOWER_MASS = 0.001
    RANDOM_UPPER_MASS = 0.005
    EXTREME_LOWER_MASS = 0.0005
    EXTREME_UPPER_MASS = 0.01

    def __init__(self):
        super(ModifiableMountainCarEnv, self).__init__()
        self.force = 0.001
        self.mass = 0.0025

    def step(self, action):
        """Rewritten to remove hard-coding of values in original code"""
        assert self.action_space.contains(action), '%r (%s) invalid' % (action, type(action))
        position, velocity = self.state
        velocity += (action - 1) * self.force + math.cos(3 * position) * -self.mass
        velocity = np.clip(velocity, -self.max_speed, self.max_speed)
        position += velocity
        position = np.clip(position, self.min_position, self.max_position)
        if position == self.min_position and velocity < 0:
            velocity = 0
        done = bool(position >= self.goal_position)
        reward = -1.0
        self.nsteps += 1
        target = 110
        if self.nsteps <= target and done:
            self.success = True
        else:
            self.success = False
        self.state = (position, velocity)
        return (np.array(self.state), reward, done, {})

    def reset(self, new=True):
        self.nsteps = 0
        return super(ModifiableMountainCarEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def is_success(self):
        """Returns True is current state indicates success, False otherwise
        get to the top of the hill within 110 time steps (definition of success in Gym)

        MountainCar sets done=True once the car reaches the "top of the hill",
        so we can just check if done=True and nsteps<=110. See:
        https://github.com/openai/gym/blob/0ccb08dfa1535624b45645e141af9398e2eba416/gym/envs/classic_control/mountain_car.py#L49
        """
        return self.success

def step(self, action):
    """Rewritten to remove hard-coding of values in original code"""
    assert self.action_space.contains(action), '%r (%s) invalid' % (action, type(action))
    position, velocity = self.state
    velocity += (action - 1) * self.force + math.cos(3 * position) * -self.mass
    velocity = np.clip(velocity, -self.max_speed, self.max_speed)
    position += velocity
    position = np.clip(position, self.min_position, self.max_position)
    if position == self.min_position and velocity < 0:
        velocity = 0
    done = bool(position >= self.goal_position)
    reward = -1.0
    self.nsteps += 1
    target = 110
    if self.nsteps <= target and done:
        self.success = True
    else:
        self.success = False
    self.state = (position, velocity)
    return (np.array(self.state), reward, done, {})

class RandomStrongForceMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        if new:
            self.force = self.np_random.uniform(self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomStrongForceMountainCar, self).parameters
        parameters.update({'force': self.force})
        return parameters

def reset(self, new=True):
    if new:
        self.force = self.np_random.uniform(self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
    self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
    return np.array(self.state)

class RandomHeavyCarMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        if new:
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomHeavyCarMountainCar, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def reset(self, new=True):
    if new:
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
    return np.array(self.state)

class RandomNormalMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        self.nsteps = 0
        if new:
            self.force = self.np_random.uniform(self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomNormalMountainCar, self).parameters
        parameters.update({'force': self.force, 'mass': self.mass})
        return parameters

def reset(self, new=True):
    self.nsteps = 0
    if new:
        self.force = self.np_random.uniform(self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
    return np.array(self.state)

class RandomExtremeMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        self.nsteps = 0
        if new:
            self.force = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE, self.EXTREME_UPPER_FORCE, self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomExtremeMountainCar, self).parameters
        parameters.update({'force': self.force, 'mass': self.mass})
        return parameters

def reset(self, new=True):
    self.nsteps = 0
    if new:
        self.force = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE, self.EXTREME_UPPER_FORCE, self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
    return np.array(self.state)

class ModifiablePendulumEnv(PendulumEnv):
    """The pendulum environment without length and mass of object hard-coded."""
    RANDOM_LOWER_MASS = 0.75
    RANDOM_UPPER_MASS = 1.25
    EXTREME_LOWER_MASS = 0.5
    EXTREME_UPPER_MASS = 1.5
    RANDOM_LOWER_LENGTH = 0.75
    RANDOM_UPPER_LENGTH = 1.25
    EXTREME_LOWER_LENGTH = 0.5
    EXTREME_UPPER_LENGTH = 1.5

    def __init__(self):
        super(ModifiablePendulumEnv, self).__init__()
        self.mass = 1.0
        self.length = 1.0

    def step(self, u):
        th, thdot = self.state
        g = 10.0
        dt = self.dt
        u = np.clip(u, -self.max_torque, self.max_torque)[0]
        self.last_u = u
        angle_normalize = (th + np.pi) % (2 * np.pi) - np.pi
        costs = angle_normalize ** 2 + 0.1 * thdot ** 2 + 0.001 * u ** 2
        newthdot = thdot + (-3 * g / (2 * self.length) * np.sin(th + np.pi) + 3.0 / (self.mass * self.length ** 2) * u) * dt
        newth = th + newthdot * dt
        newthdot = np.clip(newthdot, -self.max_speed, self.max_speed)
        normalized = (newth + np.pi) % (2 * np.pi) - np.pi
        self.state = np.array([newth, newthdot])
        self.nsteps += 1
        if -np.pi / 3 <= normalized and normalized <= np.pi / 3:
            self.nsteps_vertical += 1
        else:
            self.nsteps_vertical = 0
        target = 100
        if self.nsteps_vertical >= target:
            self.success = True
        else:
            self.success = False
        return (self._get_obs(), -costs, False, {})

    def reset(self, new=True):
        self.nsteps = 0
        self.nsteps_vertical = 0
        return super(ModifiablePendulumEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def is_success(self):
        """Returns True if current state indicates success, False otherwise

        Success: keep the angle of the pendulum at most pi/3 radians from
        vertical for the last 100 time steps of a trajectory with length 200
        (max_length is set to 200 in sunblaze_envs/__init__.py)
        """
        return self.success

def step(self, u):
    th, thdot = self.state
    g = 10.0
    dt = self.dt
    u = np.clip(u, -self.max_torque, self.max_torque)[0]
    self.last_u = u
    angle_normalize = (th + np.pi) % (2 * np.pi) - np.pi
    costs = angle_normalize ** 2 + 0.1 * thdot ** 2 + 0.001 * u ** 2
    newthdot = thdot + (-3 * g / (2 * self.length) * np.sin(th + np.pi) + 3.0 / (self.mass * self.length ** 2) * u) * dt
    newth = th + newthdot * dt
    newthdot = np.clip(newthdot, -self.max_speed, self.max_speed)
    normalized = (newth + np.pi) % (2 * np.pi) - np.pi
    self.state = np.array([newth, newthdot])
    self.nsteps += 1
    if -np.pi / 3 <= normalized and normalized <= np.pi / 3:
        self.nsteps_vertical += 1
    else:
        self.nsteps_vertical = 0
    target = 100
    if self.nsteps_vertical >= target:
        self.success = True
    else:
        self.success = False
    return (self._get_obs(), -costs, False, {})

class Ball(PhysicalObject):
    """Ball object."""
    asset = 'ball.png'
    max_speed = 9.0

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 0.25)
        kwargs.setdefault('color', (208, 33, 82))
        super(Ball, self).__init__(self.asset, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
        body.CreateCircleFixture(radius=self.width / 2 / self._world.physical_scale, density=1.0, friction=0.0, restitution=1.0)
        return body

    def step(self):
        super(Ball, self).step()
        speed = self._body.linearVelocity.length
        if speed > self.max_speed:
            self._body.linearDamping = 0.5
        elif speed < self.max_speed:
            self._body.linearDamping = 0.0

    def on_contact(self, other):
        """Prevent the ball from bouncing in a straight line up and down."""
        velocity_x = self.body.linearVelocity[0]
        if abs(velocity_x) < 0.1:
            self.apply_impulse([self._world.np_random.uniform(-0.1, 0.1), 0.0])

def on_contact(self, other):
    """Prevent the ball from bouncing in a straight line up and down."""
    velocity_x = self.body.linearVelocity[0]
    if abs(velocity_x) < 0.1:
        self.apply_impulse([self._world.np_random.uniform(-0.1, 0.1), 0.0])

class RandomSmallPaddleBreakoutWorld(BreakoutWorld):

    @property
    def paddle_class(self):
        return self.np_random.choice([Paddle, Small10Paddle, Small20Paddle, Small30Paddle])

@property
def paddle_class(self):
    return self.np_random.choice([Paddle, Small10Paddle, Small20Paddle, Small30Paddle])

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

def get_obs(self, state):
    return state[self.partially_obs_dims].copy()

def step(self, action):
    if self.act_continuous:
        action = np.clip(action, -1, 1)
        lb = self.env.action_space.low
        ub = self.env.action_space.high
        action = lb + (action + 1.0) * 0.5 * (ub - lb)
        action = np.clip(action, lb, ub)
    state, reward, done, info = self.env.step(action)
    return (self.get_obs(state), reward, done, info)

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

def reset_model(self):
    qpos = self.init_qpos + self.np_random.uniform(size=self.model.nq, low=-0.1, high=0.1)
    qvel = self.init_qvel + self.np_random.randn(self.model.nv) * 0.1
    self.set_state(qpos, qvel)
    return self._get_obs()

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

def get_current_task(self):
    return np.array([self._goal_vel])

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

class HalfCheetahDirEnv(HalfCheetahEnv):
    """Half-cheetah environment with target direction, as described in [1]. The
    code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand_direc.py

    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each
    time step a reward composed of a control cost and a reward equal to its
    velocity in the target direction. The tasks are generated by sampling the
    target directions from a Bernoulli distribution on {-1, 1} with parameter
    0.5 (-1: backward, +1: forward).

    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic
        Meta-Learning for Fast Adaptation of Deep Networks", 2017
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for
        model-based control", 2012
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """

    def __init__(self, n_tasks=None, max_episode_steps=200):
        self.n_tasks = n_tasks
        assert n_tasks == None
        self._goal = self._sample_raw_task()['goal']
        self._max_episode_steps = max_episode_steps
        super(HalfCheetahDirEnv, self).__init__()

    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = self._goal * forward_vel
        ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost)
        return (observation, reward, done, infos)

    def get_current_task(self):
        return np.array([self._goal])

    def _sample_raw_task(self):
        direction = np.random.choice([-1.0, 1.0])
        task = {'goal': direction}
        return task

    def reset_task(self, task_info):
        assert task_info is None
        self._goal = self._sample_raw_task()['goal']
        self.reset()

def step(self, action):
    xposbefore = self.sim.data.qpos[0]
    self.do_simulation(action, self.frame_skip)
    xposafter = self.sim.data.qpos[0]
    forward_vel = (xposafter - xposbefore) / self.dt
    forward_reward = self._goal * forward_vel
    ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
    observation = self._get_obs()
    reward = forward_reward - ctrl_cost
    done = False
    infos = dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost)
    return (observation, reward, done, infos)

def get_current_task(self):
    return np.array([self._goal])

def _sample_raw_task(self):
    direction = np.random.choice([-1.0, 1.0])
    task = {'goal': direction}
    return task

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

def get_current_task(self):
    return np.array([np.cos(self._goal), np.sin(self._goal)])

class AntDirEnv(MultitaskAntEnv):
    """
    AntDir: forward_backward=True (unlimited tasks) from on-policy varibad code
    AntDir2D: forward_backward=False (limited tasks) from off-policy varibad code
    """

    def __init__(self, task={}, n_tasks=None, max_episode_steps=200, forward_backward=True, **kwargs):
        self.forward_backward = forward_backward
        self._max_episode_steps = max_episode_steps
        super(AntDirEnv, self).__init__(task, n_tasks, **kwargs)

    def step(self, action):
        torso_xyz_before = np.array(self.get_body_com('torso'))
        direct = (np.cos(self._goal), np.sin(self._goal))
        self.do_simulation(action, self.frame_skip)
        torso_xyz_after = np.array(self.get_body_com('torso'))
        torso_velocity = torso_xyz_after - torso_xyz_before
        forward_reward = np.dot(torso_velocity[:2] / self.dt, direct)
        ctrl_cost = 0.5 * np.square(action).sum()
        contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 1.0
        reward = forward_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        notdone = np.isfinite(state).all() and state[2] >= 0.2 and (state[2] <= 1.0)
        done = not notdone
        ob = self._get_obs()
        return (ob, reward, done, dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward, torso_velocity=torso_velocity))

    def sample_tasks(self, num_tasks: int):
        assert self.forward_backward == False
        velocities = np.random.uniform(0.0, 2.0 * np.pi, size=(num_tasks,))
        tasks = [{'goal': velocity} for velocity in velocities]
        return tasks

    def _sample_raw_task(self):
        assert self.forward_backward == True
        velocity = np.random.choice([-1.0, 1.0])
        task = {'goal': velocity}
        return task

def step(self, action):
    torso_xyz_before = np.array(self.get_body_com('torso'))
    direct = (np.cos(self._goal), np.sin(self._goal))
    self.do_simulation(action, self.frame_skip)
    torso_xyz_after = np.array(self.get_body_com('torso'))
    torso_velocity = torso_xyz_after - torso_xyz_before
    forward_reward = np.dot(torso_velocity[:2] / self.dt, direct)
    ctrl_cost = 0.5 * np.square(action).sum()
    contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
    survive_reward = 1.0
    reward = forward_reward - ctrl_cost - contact_cost + survive_reward
    state = self.state_vector()
    notdone = np.isfinite(state).all() and state[2] >= 0.2 and (state[2] <= 1.0)
    done = not notdone
    ob = self._get_obs()
    return (ob, reward, done, dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward, torso_velocity=torso_velocity))

def _sample_raw_task(self):
    assert self.forward_backward == True
    velocity = np.random.choice([-1.0, 1.0])
    task = {'goal': velocity}
    return task

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

def get_current_task(self):
    return np.array([self._goal])

class AntGoalEnv(MultitaskAntEnv):

    def __init__(self, task={}, n_tasks=2, max_episode_steps=200, **kwargs):
        super(AntGoalEnv, self).__init__(task, n_tasks, **kwargs)
        self._max_episode_steps = max_episode_steps

    def step(self, action):
        self.do_simulation(action, self.frame_skip)
        xposafter = np.array(self.get_body_com('torso'))
        goal_reward = -np.sum(np.abs(xposafter[:2] - self._goal))
        ctrl_cost = 0.1 * np.square(action).sum()
        contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 0.0
        reward = goal_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        done = False
        ob = self._get_obs()
        return (ob, reward, done, dict(goal_forward=goal_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward))

    def sample_tasks(self, num_tasks):
        a = np.random.random(num_tasks) * 2 * np.pi
        r = 3 * np.random.random(num_tasks) ** 0.5
        goals = np.stack((r * np.cos(a), r * np.sin(a)), axis=-1)
        tasks = [{'goal': goal} for goal in goals]
        return tasks

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat, self.sim.data.qvel.flat, np.clip(self.sim.data.cfrc_ext, -1, 1).flat])

def step(self, action):
    self.do_simulation(action, self.frame_skip)
    xposafter = np.array(self.get_body_com('torso'))
    goal_reward = -np.sum(np.abs(xposafter[:2] - self._goal))
    ctrl_cost = 0.1 * np.square(action).sum()
    contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
    survive_reward = 0.0
    reward = goal_reward - ctrl_cost - contact_cost + survive_reward
    state = self.state_vector()
    done = False
    ob = self._get_obs()
    return (ob, reward, done, dict(goal_forward=goal_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward))

def sample_tasks(self, num_tasks):
    a = np.random.random(num_tasks) * 2 * np.pi
    r = 3 * np.random.random(num_tasks) ** 0.5
    goals = np.stack((r * np.cos(a), r * np.sin(a)), axis=-1)
    tasks = [{'goal': goal} for goal in goals]
    return tasks

def _get_obs(self):
    return np.concatenate([self.sim.data.qpos.flat, self.sim.data.qvel.flat, np.clip(self.sim.data.cfrc_ext, -1, 1).flat])

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

def reset_task(self, idx):
    """reset goal AND reset the agent"""
    if idx is not None:
        self._wind = np.array(self.winds[idx])
    self.reset()

def get_current_task(self):
    return self._wind.copy()

def reset_model(self):
    self._state = np.array([0.0, 0.0])
    return self._get_obs()

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

def reset_task(self, idx):
    """reset goal AND reset the agent"""
    if idx is not None:
        self._goal = np.array(self.goals[idx])
    self.reset()

def get_current_task(self):
    return self._goal.copy()

def reset_model(self):
    self._state = np.random.uniform(-1.0, 1.0, size=(2,))
    return self._get_obs()

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

def reset_task(self, idx=None):
    """reset goal and state"""
    if idx is not None:
        self._goal = np.array(self.goals[idx])
    self.reset()

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

def _compute_belief_reward(self):
    num_possible_goal_belief = np.sum(self._belief_state != 0)
    non_goal_rew = 0.0 if self.is_sparse else -0.1
    belief_reward = (1.0 + non_goal_rew * (num_possible_goal_belief - 1)) / num_possible_goal_belief
    return belief_reward

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

def _sample_indices(self, batch_size):
    valid_starts_indices = np.where(self._valid_starts > 0.0)[0]
    sample_weights = np.copy(self._valid_starts[valid_starts_indices])
    sample_weights /= sample_weights.sum()
    return np.random.choice(valid_starts_indices, size=batch_size, p=sample_weights)

def _sample_data(self, indices, next_indices):
    return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._observations[next_indices])

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

def sample_data(self, indices):
    return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._next_obs[indices])

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

def _sample_indices(self, batch_size):
    valid_starts_indices = np.where(self._valid_starts > 0.0)[0]
    sample_weights = np.copy(self._valid_starts[valid_starts_indices])
    sample_weights /= sample_weights.sum()
    return np.random.choice(valid_starts_indices, size=batch_size, p=sample_weights)

def _sample_data(self, indices):
    return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._next_observations[indices])

def randn(*args, **kwargs):
    return torch.randn(*args, **kwargs).to(device)

