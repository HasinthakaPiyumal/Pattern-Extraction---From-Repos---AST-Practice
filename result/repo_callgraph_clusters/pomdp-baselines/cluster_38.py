# Cluster 38

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

def _reset(self, new=True):
    state = super()._reset()
    return self.get_obs(state)

def _step(self, a):
    state, reward, done, info = super()._step(a)
    return (self.get_obs(state), reward, done, info)

class RandomNormalHalfCheetah(RoboschoolXMLModifierMixin, ModifiableRoboschoolHalfCheetah):

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = self.np_random.uniform(self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('half_cheetah.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

def _reset(self, new=True):
    if new:
        self.randomize_env()
    return super()._reset(new)

class RandomExtremeHalfCheetah(RoboschoolXMLModifierMixin, ModifiableRoboschoolHalfCheetah):

    def randomize_env(self):
        """
        # self.armature = self.np_random.uniform(0.2, 0.5)
        self.density = self.np_random.uniform(self.LOWER_DENSITY, self.UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.LOWER_FRICTION, self.UPPER_FRICTION)
        self.power = self.np_random.uniform(self.LOWER_POWER, self.UPPER_POWER)
        """
        self.density = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_DENSITY, self.EXTREME_UPPER_DENSITY, self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FRICTION, self.EXTREME_UPPER_FRICTION, self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_POWER, self.EXTREME_UPPER_POWER, self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('half_cheetah.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

def _reset(self, new=True):
    if new:
        self.randomize_env()
    return super()._reset(new)

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

def _reset(self, new=True):
    state = super()._reset()
    return self.get_obs(state)

def _step(self, a):
    state, reward, done, info = super()._step(a)
    return (self.get_obs(state), reward, done, info)

class RandomNormalHopper(RoboschoolXMLModifierMixin, ModifiableRoboschoolHopper):

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = self.np_random.uniform(self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('hopper.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

def _reset(self, new=True):
    if new:
        self.randomize_env()
    return super()._reset(new)

class RandomExtremeHopper(RoboschoolXMLModifierMixin, ModifiableRoboschoolHopper):

    def randomize_env(self):
        """
        self.density = self.np_random.uniform(self.LOWER_DENSITY, self.UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.LOWER_FRICTION, self.UPPER_FRICTION)
        self.power = self.np_random.uniform(self.LOWER_POWER, self.UPPER_POWER)
        """
        self.density = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_DENSITY, self.EXTREME_UPPER_DENSITY, self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FRICTION, self.EXTREME_UPPER_FRICTION, self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_POWER, self.EXTREME_UPPER_POWER, self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('hopper.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

def _reset(self, new=True):
    if new:
        self.randomize_env()
    return super()._reset(new)

class ModifiableRoboschoolWalker2d_MRPO(RoboschoolWalker2d, RoboschoolTrackDistSuccessMixin):
    RANDOM_LOWER_DENSITY = 750
    RANDOM_UPPER_DENSITY = 1250
    EXTREME_LOWER_DENSITY = 1
    EXTREME_UPPER_DENSITY = 750
    RANDOM_LOWER_FRICTION = 0.2
    RANDOM_UPPER_FRICTION = 2.5
    EXTREME_LOWER_FRICTION = 0.05
    EXTREME_UPPER_FRICTION = 0.2

    def _reset(self, new=True):
        return super(ModifiableRoboschoolWalker2d_MRPO, self)._reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

def _reset(self, new=True):
    return super(ModifiableRoboschoolWalker2d_MRPO, self)._reset()

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

def _reset(self, new=True):
    if new:
        self.randomize_env()
    state = super(RandomNormalWalker2d_MRPO, self)._reset(new)
    return self.get_obs(state)

def _step(self, a):
    state, reward, done, info = super(RandomNormalWalker2d_MRPO, self)._step(a)
    return (self.get_obs(state), reward, done, info)

class ModifiableRoboschoolHalfCheetah_MRPO(RoboschoolHalfCheetah, RoboschoolTrackDistSuccessMixin):
    RANDOM_LOWER_DENSITY = 750
    RANDOM_UPPER_DENSITY = 1250
    EXTREME_LOWER_DENSITY = 1
    EXTREME_UPPER_DENSITY = 750
    RANDOM_LOWER_FRICTION = 0.2
    RANDOM_UPPER_FRICTION = 2.25
    EXTREME_LOWER_FRICTION = 0.05
    EXTREME_UPPER_FRICTION = 0.2

    def _reset(self, new=True):
        return super(ModifiableRoboschoolHalfCheetah_MRPO, self)._reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

def _reset(self, new=True):
    return super(ModifiableRoboschoolHalfCheetah_MRPO, self)._reset()

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

def _reset(self, new=True):
    if new:
        self.randomize_env()
    state = super(RandomNormalHalfCheetah_MRPO, self)._reset(new)
    return self.get_obs(state)

def _step(self, a):
    state, reward, done, info = super(RandomNormalHalfCheetah_MRPO, self)._step(a)
    return (self.get_obs(state), reward, done, info)

class ModifiableRoboschoolHopper_MRPO(RoboschoolHopper, RoboschoolTrackDistSuccessMixin):
    RANDOM_LOWER_DENSITY = 750
    RANDOM_UPPER_DENSITY = 1250
    EXTREME_LOWER_DENSITY = 1
    EXTREME_UPPER_DENSITY = 750
    RANDOM_LOWER_FRICTION = 0.5
    RANDOM_UPPER_FRICTION = 1.1
    EXTREME_LOWER_FRICTION = 0.2
    EXTREME_UPPER_FRICTION = 0.5

    def _reset(self, new=True):
        return super(ModifiableRoboschoolHopper_MRPO, self)._reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

def _reset(self, new=True):
    return super(ModifiableRoboschoolHopper_MRPO, self)._reset()

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

def _reset(self, new=True):
    if new:
        self.randomize_env()
    state = super(RandomNormalHopper_MRPO, self)._reset(new)
    return self.get_obs(state)

def _step(self, a):
    state, reward, done, info = super(RandomNormalHopper_MRPO, self)._step(a)
    return (self.get_obs(state), reward, done, info)

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

def reset(self):
    state = self.env.reset()
    return self.get_obs(state)

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

def reward(self, state, action=None):
    return self.sparsify_rewards(super().reward(state, action))

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

