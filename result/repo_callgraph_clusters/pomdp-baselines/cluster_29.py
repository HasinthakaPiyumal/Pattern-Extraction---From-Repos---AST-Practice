# Cluster 29

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

def reset(self):
    with self.LOCK:
        image: np.ndarray = self.env.reset()
    return self.observe(image)

def step(self, action):
    image, reward, done, info = self.env.step(action)
    return (self.observe(image), reward, done, info)

class InvaderMissile(Missile):
    """Invader's missile."""

    @classmethod
    def fire(cls, world, entity, impulse):
        """Fires a missile."""
        missile = cls(world=world, position=(entity.position[0], entity.position[1] - entity.height - 10))
        missile.apply_impulse((0, -impulse / world.physical_scale * missile.body.mass))
        return missile

    def should_collide(self, other):
        """Ignore collisions with invaders and own missiles."""
        return not isinstance(other, (Invader, InvaderMissile))

    def on_contact(self, other):
        if isinstance(other, PlayerShip):
            self._world._lives -= 1
        self.kill()

@classmethod
def fire(cls, world, entity, impulse):
    """Fires a missile."""
    missile = cls(world=world, position=(entity.position[0], entity.position[1] - entity.height - 10))
    missile.apply_impulse((0, -impulse / world.physical_scale * missile.body.mass))
    return missile

class PlayerMissile(Missile):
    """Player's missile."""

    @classmethod
    def fire(cls, world, entity, impulse):
        """Fires a missile."""
        missile = cls(world=world, position=(entity.position[0], entity.position[1] + entity.height + 10))
        missile.apply_impulse((0, impulse / world.physical_scale * missile.body.mass))
        return missile

    def should_collide(self, other):
        """Ignore collisions with own missiles."""
        return not isinstance(other, PlayerMissile)

    def on_contact(self, other):
        if isinstance(other, (Invader, InvaderMissile)):
            other.kill()
        if isinstance(other, Invader):
            self._world.add_kill_score()
        self.kill()

@classmethod
def fire(cls, world, entity, impulse):
    """Fires a missile."""
    missile = cls(world=world, position=(entity.position[0], entity.position[1] + entity.height + 10))
    missile.apply_impulse((0, impulse / world.physical_scale * missile.body.mass))
    return missile

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

class BreakoutWorld(PhysicalWorld):
    paddle_class = Paddle
    brick_class = Brick
    ball_class = Ball
    n_actions = 3

    def create_world(self, parent):
        p_width = self._width / self.physical_scale
        p_height = self._height / self.physical_scale
        ground = self._engine.CreateStaticBody(position=(0, 0))
        ground.CreateEdgeFixture(vertices=[(0, 0), (0, p_height)])
        ground.CreateEdgeFixture(vertices=[(0, p_height), (p_width, p_height)])
        ground.CreateEdgeFixture(vertices=[(p_width, p_height), (p_width, 0)])
        self._ground = ground
        self.ball = self.ball_class(world=self, position=self.initial_ball_position())
        parent.add(self.ball)
        self.paddle = self.paddle_class(world=self, position=self.initial_paddle_position())
        parent.add(self.paddle)

    @property
    def lives(self):
        return self._lives

    @property
    def score(self):
        return self._score

    @property
    def parameters(self):
        parameters = super(BreakoutWorld, self).parameters
        parameters.update({'world': 'breakout'})
        return parameters

    def paddle_impulse(self):
        """Relative paddle impulse strength on movement actions."""
        return 50

    def act(self, action):
        """Perform external action."""
        if action == 0:
            pass
        elif action == 1:
            self.paddle.apply_impulse((-self.paddle_impulse() / self.physical_scale * self.paddle.body.mass, 0))
        elif action == 2:
            self.paddle.apply_impulse((self.paddle_impulse() / self.physical_scale * self.paddle.body.mass, 0))

    def initial_ball_position(self):
        """Initial ball position after reset."""
        return (self._width / 2, self._height / 2)

    def initial_paddle_position(self):
        """Initial paddle position after reset."""
        return (self._width / 2, 25)

    def initial_paddle_rotation(self):
        """Initial paddle rotation after reset (in degrees)."""
        return 0

    def initial_brick_position(self):
        """Initial brick row offset after reset."""
        return 40

    def create_bricks(self):
        """Create bricks."""
        dummy = self.brick_class(row=0, column=0)
        brick_x = dummy.width / 2
        brick_y = self._height - self.initial_brick_position()
        for row in range(5):
            for column in range(self._width // dummy.width):
                brick = self.brick_class(world=self, position=(brick_x, brick_y), row=row, column=column)
                self._batch.add(brick)
                brick_x += dummy.width
            brick_x = dummy.width / 2
            brick_y -= dummy.height

    def reset_world(self):
        """Reset the game."""
        super(BreakoutWorld, self).reset_world()
        self._lives = 5
        self._score = 0

        def remove_bricks(node):
            if not isinstance(node, self.brick_class):
                return
            node.kill()
        self.walk(remove_bricks)
        self.create_bricks()
        self.reset_paddle()
        self.reset_ball()

    def reset_paddle(self):
        """Reset paddle."""
        self.paddle.kill()
        self.paddle = self.paddle_class(world=self, position=self.initial_paddle_position(), rotation=self.initial_paddle_rotation())
        self._batch.add(self.paddle)

    def reset_ball(self):
        """Reset ball position."""
        self.ball.stop_body()
        self.ball.set_body_position(self.initial_ball_position())
        self.ball.apply_impulse(150.0 / self.physical_scale * self.ball.body.mass * np.asarray([self.np_random.uniform(-0.3, 0.3), -self.np_random.uniform(0.6, 1.0)]))

    def step(self):
        """Perform one environment update step."""
        if self._lives <= 0:
            self.reset_world()
        self._terminal = False
        super(BreakoutWorld, self).step()
        if self.ball.position[1] < 0:
            self.reset_ball()
            self._lives -= 1
            if self._lives <= 0:
                self._terminal = True

        def count_bricks(node):
            if not isinstance(node, self.brick_class):
                return
            return 1
        if not sum(self.walk(count_bricks)):
            self._terminal = True

def act(self, action):
    """Perform external action."""
    if action == 0:
        pass
    elif action == 1:
        self.paddle.apply_impulse((-self.paddle_impulse() / self.physical_scale * self.paddle.body.mass, 0))
    elif action == 2:
        self.paddle.apply_impulse((self.paddle_impulse() / self.physical_scale * self.paddle.body.mass, 0))

def reset_ball(self):
    """Reset ball position."""
    self.ball.stop_body()
    self.ball.set_body_position(self.initial_ball_position())
    self.ball.apply_impulse(150.0 / self.physical_scale * self.ball.body.mass * np.asarray([self.np_random.uniform(-0.3, 0.3), -self.np_random.uniform(0.6, 1.0)]))

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

def set_goal(self, goal):
    self._goal = np.asarray(goal)

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

def set_goal(self, wind):
    self._wind = np.asarray(wind)

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

def set_goal(self, goal):
    self._goal = np.asarray(goal)

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

def set_goal(self, goal):
    self._goal = np.asarray(goal)

