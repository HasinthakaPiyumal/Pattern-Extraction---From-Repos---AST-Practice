# Cluster 8

def sample_gaussian(mu, logvar, num=None):
    if num is None:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return eps.mul(std).add_(mu)
    else:
        std = torch.exp(0.5 * logvar).repeat(num, 1)
        eps = torch.randn_like(std)
        mu = mu.repeat(num, 1)
        return eps.mul(std).add_(mu)

class TimeLimitWrapper(gym.Wrapper):

    def __init__(self, env, time_limit):
        super().__init__(env)
        self._max_episode_steps = time_limit

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.step_ += 1
        if self.step_ >= self._max_episode_steps:
            done = True
            info['TimeLimit.truncated'] = True
        return (obs, reward, done, info)

    def reset(self):
        self.step_ = 0
        return self.env.reset()

def step(self, action):
    obs, reward, done, info = self.env.step(action)
    self.step_ += 1
    if self.step_ >= self._max_episode_steps:
        done = True
        info['TimeLimit.truncated'] = True
    return (obs, reward, done, info)

class LeftRightMovingInvader(Invader):
    """Invader which moves left and right."""
    max_delta_x = 24

    def __init__(self, *args, **kwargs):
        super(LeftRightMovingInvader, self).__init__(*args, **kwargs)
        self._direction = 1
        self._initial_x = self.position[0]

    def step(self):
        if self.position[0] - self._initial_x >= self.max_delta_x:
            self._direction = -1
        elif self.position[0] - self._initial_x <= -self.max_delta_x:
            self._direction = 1
        self.set_body_position((self.position[0] + self._direction, self.position[1]))
        super(LeftRightMovingInvader, self).step()

def step(self):
    if self.position[0] - self._initial_x >= self.max_delta_x:
        self._direction = -1
    elif self.position[0] - self._initial_x <= -self.max_delta_x:
        self._direction = 1
    self.set_body_position((self.position[0] + self._direction, self.position[1]))
    super(LeftRightMovingInvader, self).step()

class CrossScreenMovingInvader(Invader):
    """Invader which moves across the whole screen."""

    def __init__(self, *args, **kwargs):
        super(CrossScreenMovingInvader, self).__init__(*args, **kwargs)
        self._direction = 1

    def step(self):
        if self.position[0] >= self._world._width - self.width:
            self._direction = -1
        elif self.position[0] <= self.width:
            self._direction = 1
        self.set_body_position((self.position[0] + self._direction, self.position[1]))
        super(CrossScreenMovingInvader, self).step()

def step(self):
    if self.position[0] >= self._world._width - self.width:
        self._direction = -1
    elif self.position[0] <= self.width:
        self._direction = 1
    self.set_body_position((self.position[0] + self._direction, self.position[1]))
    super(CrossScreenMovingInvader, self).step()

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

def step(self, action):
    result = self.env.step(action)
    self.record_parameters()
    return result

def reset(self):
    result = self.env.reset()
    self.record_parameters()
    return result

class ModifiableCartPoleEnv(CartPoleEnv, EnvBinarySuccessMixin):
    RANDOM_LOWER_FORCE_MAG = 5.0
    RANDOM_UPPER_FORCE_MAG = 15.0
    EXTREME_LOWER_FORCE_MAG = 1.0
    EXTREME_UPPER_FORCE_MAG = 20.0
    RANDOM_LOWER_LENGTH = 0.25
    RANDOM_UPPER_LENGTH = 0.75
    EXTREME_LOWER_LENGTH = 0.05
    EXTREME_UPPER_LENGTH = 1.0
    RANDOM_LOWER_MASSPOLE = 0.05
    RANDOM_UPPER_MASSPOLE = 0.5
    EXTREME_LOWER_MASSPOLE = 0.01
    EXTREME_UPPER_MASSPOLE = 1.0

    def _followup(self):
        """Cascade values of new (variable) parameters"""
        self.total_mass = self.masspole + self.masscart
        self.polemass_length = self.masspole * self.length

    def reset(self, new=True):
        """new is a boolean variable telling whether to regenerate the environment parameters"""
        'Default is to just ignore it'
        self.nsteps = 0
        return super(ModifiableCartPoleEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def step(self, *args, **kwargs):
        """Wrapper to increment new variable nsteps"""
        self.nsteps += 1
        return super().step(*args, **kwargs)

    def is_success(self):
        """Returns True is current state indicates success, False otherwise
        Balance for at least 195 time steps ("definition" of success in Gym:
        https://github.com/openai/gym/wiki/CartPole-v0#solved-requirements)
        """
        target = 195
        if self.nsteps >= target:
            return True
        else:
            return False

def step(self, *args, **kwargs):
    """Wrapper to increment new variable nsteps"""
    self.nsteps += 1
    return super().step(*args, **kwargs)

class ModifiableAcrobotEnv(AcrobotEnv):
    RANDOM_LOWER_MASS = 0.75
    RANDOM_UPPER_MASS = 1.25
    EXTREME_LOWER_MASS = 0.5
    EXTREME_UPPER_MASS = 1.5
    RANDOM_LOWER_LENGTH = 0.75
    RANDOM_UPPER_LENGTH = 1.25
    EXTREME_LOWER_LENGTH = 0.5
    EXTREME_UPPER_LENGTH = 1.5
    RANDOM_LOWER_INERTIA = 0.75
    RANDOM_UPPER_INERTIA = 1.25
    EXTREME_LOWER_INERTIA = 0.5
    EXTREME_UPPER_INERTIA = 1.5

    def reset(self, new=True):
        self.nsteps = 0
        return super(ModifiableAcrobotEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def step(self, *args, **kwargs):
        """Wrapper to increment new variable nsteps"""
        self.nsteps += 1
        ret = super().step(*args, **kwargs)
        target = 90
        if self.nsteps <= target and self._terminal():
            self.success = True
        else:
            self.success = False
        return ret

    def is_success(self):
        """Returns True if current state indicates success, False otherwise

        Success: swing the end of the second link to the desired height within
        90 time steps
        """
        return self.success

def step(self, *args, **kwargs):
    """Wrapper to increment new variable nsteps"""
    self.nsteps += 1
    ret = super().step(*args, **kwargs)
    target = 90
    if self.nsteps <= target and self._terminal():
        self.success = True
    else:
        self.success = False
    return ret

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

def step_node(node):
    if not isinstance(node, PhysicalObject):
        return
    node.step()

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

def step(self):
    """Perform one environment update step."""
    self._world.step()
    return self.is_terminal

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

def _reset(self):
    self._env.reset()
    self._env.step()
    return self._get_observation()

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

class ActionDelayWrapper(gym.Wrapper):

    def _step(self, action):
        self._action_buffer.append(action)
        action = self._action_buffer.popleft()
        return self.env.step(action)

    def _reset(self):
        self._action_delay = np.random.randint(delay_range_start, delay_range_end)
        self._action_buffer = collections.deque([0 for _ in range(self._action_delay)])
        return self.env.reset()

def _step(self, action):
    self._action_buffer.append(action)
    action = self._action_buffer.popleft()
    return self.env.step(action)

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

def step(self):
    super(Ball, self).step()
    speed = self._body.linearVelocity.length
    if speed > self.max_speed:
        self._body.linearDamping = 0.5
    elif speed < self.max_speed:
        self._body.linearDamping = 0.0

class TimeLimitMask(gym.Wrapper):

    def step(self, action):
        obs, rew, done, info = self.env.step(action)
        if done and self.env._max_episode_steps == self.env._elapsed_steps:
            info['bad_transition'] = True
        return (obs, rew, done, info)

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

def step(self, action):
    obs, rew, done, info = self.env.step(action)
    if done and self.env._max_episode_steps == self.env._elapsed_steps:
        info['bad_transition'] = True
    return (obs, rew, done, info)

def randn_like(*args, **kwargs):
    return torch.randn_like(*args, **kwargs).to(device)

class TD3(RLAlgorithmBase):
    name = 'td3'
    continuous_action = True
    use_target_actor = True

    def __init__(self, exploration_noise=0.1, target_noise=0.2, target_noise_clip=0.5, **kwargs):
        self.exploration_noise = exploration_noise
        self.target_noise = target_noise
        self.target_noise_clip = target_noise_clip

    @staticmethod
    def build_actor(input_size, action_dim, hidden_sizes, **kwargs):
        return DeterministicPolicy(obs_dim=input_size, action_dim=action_dim, hidden_sizes=hidden_sizes, **kwargs)

    @staticmethod
    def build_critic(hidden_sizes, input_size=None, obs_dim=None, action_dim=None):
        if obs_dim is not None and action_dim is not None:
            input_size = obs_dim + action_dim
        qf1 = FlattenMlp(input_size=input_size, output_size=1, hidden_sizes=hidden_sizes)
        qf2 = FlattenMlp(input_size=input_size, output_size=1, hidden_sizes=hidden_sizes)
        return (qf1, qf2)

    def select_action(self, actor, observ, deterministic: bool, **kwargs):
        mean = actor(observ)
        if deterministic:
            action_tuple = (mean, mean, None, None)
        else:
            action = (mean + torch.randn_like(mean) * self.exploration_noise).clamp(-1, 1)
            action_tuple = (action, mean, None, None)
        return action_tuple

    @staticmethod
    def forward_actor(actor, observ):
        new_actions = actor(observ)
        return (new_actions, None)

    def _inject_noise(self, actions):
        action_noise = (torch.randn_like(actions) * self.target_noise).clamp(-self.target_noise_clip, self.target_noise_clip)
        new_actions = (actions + action_noise).clamp(-1, 1)
        return new_actions

    def critic_loss(self, markov_actor: bool, markov_critic: bool, actor, actor_target, critic, critic_target, observs, actions, rewards, dones, gamma, next_observs=None):
        with torch.no_grad():
            if markov_actor:
                new_actions, _ = self.forward_actor(actor_target, next_observs if markov_critic else observs)
            else:
                new_actions, _ = actor_target(prev_actions=actions, rewards=rewards, observs=next_observs if markov_critic else observs)
            new_actions = self._inject_noise(new_actions)
            if markov_critic:
                next_q1 = critic_target[0](next_observs, new_actions)
                next_q2 = critic_target[1](next_observs, new_actions)
            else:
                next_q1, next_q2 = critic_target(prev_actions=actions, rewards=rewards, observs=observs, current_actions=new_actions)
            min_next_q_target = torch.min(next_q1, next_q2)
            q_target = rewards + (1.0 - dones) * gamma * min_next_q_target
            if not markov_critic:
                q_target = q_target[1:]
        if markov_critic:
            q1_pred = critic[0](observs, actions)
            q2_pred = critic[1](observs, actions)
        else:
            q1_pred, q2_pred = critic(prev_actions=actions, rewards=rewards, observs=observs, current_actions=actions[1:])
        return ((q1_pred, q2_pred), q_target)

    def actor_loss(self, markov_actor: bool, markov_critic: bool, actor, actor_target, critic, critic_target, observs, actions=None, rewards=None):
        if markov_actor:
            new_actions, _ = self.forward_actor(actor, observs)
        else:
            new_actions, _ = actor(prev_actions=actions, rewards=rewards, observs=observs)
        if markov_critic:
            q1 = critic[0](observs, new_actions)
            q2 = critic[1](observs, new_actions)
        else:
            q1, q2 = critic(prev_actions=actions, rewards=rewards, observs=observs, current_actions=new_actions)
        min_q_new_actions = torch.min(q1, q2)
        policy_loss = -min_q_new_actions
        if not markov_critic:
            policy_loss = policy_loss[:-1]
        return (policy_loss, None)

    def forward_actor_in_target(self, actor, actor_target, next_observ):
        new_next_actions, _ = self.forward_actor(actor_target, next_observ)
        return (self._inject_noise(new_next_actions), None)

    def entropy_bonus(self, log_probs):
        return 0.0

def select_action(self, actor, observ, deterministic: bool, **kwargs):
    mean = actor(observ)
    if deterministic:
        action_tuple = (mean, mean, None, None)
    else:
        action = (mean + torch.randn_like(mean) * self.exploration_noise).clamp(-1, 1)
        action_tuple = (action, mean, None, None)
    return action_tuple

def _inject_noise(self, actions):
    action_noise = (torch.randn_like(actions) * self.target_noise).clamp(-self.target_noise_clip, self.target_noise_clip)
    new_actions = (actions + action_noise).clamp(-1, 1)
    return new_actions

class SACD(RLAlgorithmBase):
    name = 'sacd'
    continuous_action = False
    use_target_actor = False

    def __init__(self, entropy_alpha=0.1, automatic_entropy_tuning=True, target_entropy=None, alpha_lr=0.0003, action_dim=None):
        self.automatic_entropy_tuning = automatic_entropy_tuning
        if self.automatic_entropy_tuning:
            assert target_entropy is not None
            self.target_entropy = float(target_entropy) * np.log(action_dim)
            self.log_alpha_entropy = torch.zeros(1, requires_grad=True, device=ptu.device)
            self.alpha_entropy_optim = Adam([self.log_alpha_entropy], lr=alpha_lr)
            self.alpha_entropy = self.log_alpha_entropy.exp().detach().item()
        else:
            self.alpha_entropy = entropy_alpha

    @staticmethod
    def build_actor(input_size, action_dim, hidden_sizes, **kwargs):
        return CategoricalPolicy(obs_dim=input_size, action_dim=action_dim, hidden_sizes=hidden_sizes, **kwargs)

    @staticmethod
    def build_critic(hidden_sizes, input_size=None, obs_dim=None, action_dim=None):
        assert action_dim is not None
        if obs_dim is not None:
            input_size = obs_dim
        qf1 = FlattenMlp(input_size=input_size, output_size=action_dim, hidden_sizes=hidden_sizes)
        qf2 = FlattenMlp(input_size=input_size, output_size=action_dim, hidden_sizes=hidden_sizes)
        return (qf1, qf2)

    def select_action(self, actor, observ, deterministic: bool, return_log_prob: bool):
        action, prob, log_prob = actor(observ, deterministic, return_log_prob)
        return (action, prob, log_prob, None)

    @staticmethod
    def forward_actor(actor, observ):
        _, probs, log_probs = actor(observ, return_log_prob=True)
        return (probs, log_probs)

    def critic_loss(self, markov_actor: bool, markov_critic: bool, actor, actor_target, critic, critic_target, observs, actions, rewards, dones, gamma, next_observs=None):
        with torch.no_grad():
            if markov_actor:
                new_probs, new_log_probs = self.forward_actor(actor, next_observs if markov_critic else observs)
            else:
                new_probs, new_log_probs = actor(prev_actions=actions, rewards=rewards, observs=next_observs if markov_critic else observs)
            if markov_critic:
                next_q1 = critic_target[0](next_observs)
                next_q2 = critic_target[1](next_observs)
            else:
                next_q1, next_q2 = critic_target(prev_actions=actions, rewards=rewards, observs=observs, current_actions=new_probs)
            min_next_q_target = torch.min(next_q1, next_q2)
            min_next_q_target += self.alpha_entropy * -new_log_probs
            min_next_q_target = (new_probs * min_next_q_target).sum(dim=-1, keepdims=True)
            q_target = rewards + (1.0 - dones) * gamma * min_next_q_target
            if not markov_critic:
                q_target = q_target[1:]
        if markov_critic:
            q1_pred = critic[0](observs)
            q2_pred = critic[1](observs)
            action = actions.long()
            q1_pred = q1_pred.gather(dim=-1, index=action)
            q2_pred = q2_pred.gather(dim=-1, index=action)
        else:
            q1_pred, q2_pred = critic(prev_actions=actions, rewards=rewards, observs=observs, current_actions=actions[1:])
            stored_actions = actions[1:]
            stored_actions = torch.argmax(stored_actions, dim=-1, keepdims=True)
            q1_pred = q1_pred.gather(dim=-1, index=stored_actions)
            q2_pred = q2_pred.gather(dim=-1, index=stored_actions)
        return ((q1_pred, q2_pred), q_target)

    def actor_loss(self, markov_actor: bool, markov_critic: bool, actor, actor_target, critic, critic_target, observs, actions=None, rewards=None):
        if markov_actor:
            new_probs, log_probs = self.forward_actor(actor, observs)
        else:
            new_probs, log_probs = actor(prev_actions=actions, rewards=rewards, observs=observs)
        if markov_critic:
            q1 = critic[0](observs)
            q2 = critic[1](observs)
        else:
            q1, q2 = critic(prev_actions=actions, rewards=rewards, observs=observs, current_actions=new_probs)
        min_q_new_actions = torch.min(q1, q2)
        policy_loss = -min_q_new_actions
        policy_loss += self.alpha_entropy * log_probs
        policy_loss = (new_probs * policy_loss).sum(axis=-1, keepdims=True)
        if not markov_critic:
            policy_loss = policy_loss[:-1]
        log_probs = (new_probs * log_probs).sum(axis=-1, keepdims=True)
        return (policy_loss, log_probs)

    def update_others(self, current_log_probs):
        if self.automatic_entropy_tuning:
            alpha_entropy_loss = -self.log_alpha_entropy.exp() * (current_log_probs + self.target_entropy)
            self.alpha_entropy_optim.zero_grad()
            alpha_entropy_loss.backward()
            self.alpha_entropy_optim.step()
            self.alpha_entropy = self.log_alpha_entropy.exp().item()
        return {'policy_entropy': -current_log_probs, 'alpha': self.alpha_entropy}

def __init__(self, entropy_alpha=0.1, automatic_entropy_tuning=True, target_entropy=None, alpha_lr=0.0003, action_dim=None):
    self.automatic_entropy_tuning = automatic_entropy_tuning
    if self.automatic_entropy_tuning:
        assert target_entropy is not None
        self.target_entropy = float(target_entropy) * np.log(action_dim)
        self.log_alpha_entropy = torch.zeros(1, requires_grad=True, device=ptu.device)
        self.alpha_entropy_optim = Adam([self.log_alpha_entropy], lr=alpha_lr)
        self.alpha_entropy = self.log_alpha_entropy.exp().detach().item()
    else:
        self.alpha_entropy = entropy_alpha

def update_others(self, current_log_probs):
    if self.automatic_entropy_tuning:
        alpha_entropy_loss = -self.log_alpha_entropy.exp() * (current_log_probs + self.target_entropy)
        self.alpha_entropy_optim.zero_grad()
        alpha_entropy_loss.backward()
        self.alpha_entropy_optim.step()
        self.alpha_entropy = self.log_alpha_entropy.exp().item()
    return {'policy_entropy': -current_log_probs, 'alpha': self.alpha_entropy}

class SAC(RLAlgorithmBase):
    name = 'sac'
    continuous_action = True
    use_target_actor = False

    def __init__(self, entropy_alpha=0.1, automatic_entropy_tuning=True, target_entropy=None, alpha_lr=0.0003, action_dim=None):
        self.automatic_entropy_tuning = automatic_entropy_tuning
        if self.automatic_entropy_tuning:
            if target_entropy is not None:
                self.target_entropy = float(target_entropy)
            else:
                self.target_entropy = -float(action_dim)
            self.log_alpha_entropy = torch.zeros(1, requires_grad=True, device=ptu.device)
            self.alpha_entropy_optim = Adam([self.log_alpha_entropy], lr=alpha_lr)
            self.alpha_entropy = self.log_alpha_entropy.exp().detach().item()
        else:
            self.alpha_entropy = entropy_alpha

    def update_others(self, current_log_probs):
        if self.automatic_entropy_tuning:
            alpha_entropy_loss = -self.log_alpha_entropy.exp() * (current_log_probs + self.target_entropy)
            self.alpha_entropy_optim.zero_grad()
            alpha_entropy_loss.backward()
            self.alpha_entropy_optim.step()
            self.alpha_entropy = self.log_alpha_entropy.exp().item()
        return {'policy_entropy': -current_log_probs, 'alpha': self.alpha_entropy}

    @staticmethod
    def build_actor(input_size, action_dim, hidden_sizes, **kwargs):
        return TanhGaussianPolicy(obs_dim=input_size, action_dim=action_dim, hidden_sizes=hidden_sizes, **kwargs)

    @staticmethod
    def build_critic(hidden_sizes, input_size=None, obs_dim=None, action_dim=None):
        if obs_dim is not None and action_dim is not None:
            input_size = obs_dim + action_dim
        qf1 = FlattenMlp(input_size=input_size, output_size=1, hidden_sizes=hidden_sizes)
        qf2 = FlattenMlp(input_size=input_size, output_size=1, hidden_sizes=hidden_sizes)
        return (qf1, qf2)

    def select_action(self, actor, observ, deterministic: bool, return_log_prob: bool):
        return actor(observ, False, deterministic, return_log_prob)

    @staticmethod
    def forward_actor(actor, observ):
        new_actions, _, _, log_probs = actor(observ, return_log_prob=True)
        return (new_actions, log_probs)

    def critic_loss(self, markov_actor: bool, markov_critic: bool, actor, actor_target, critic, critic_target, observs, actions, rewards, dones, gamma, next_observs=None):
        with torch.no_grad():
            if markov_actor:
                new_actions, new_log_probs = self.forward_actor(actor, next_observs if markov_critic else observs)
            else:
                new_actions, new_log_probs = actor(prev_actions=actions, rewards=rewards, observs=next_observs if markov_critic else observs)
            if markov_critic:
                next_q1 = critic_target[0](next_observs, new_actions)
                next_q2 = critic_target[1](next_observs, new_actions)
            else:
                next_q1, next_q2 = critic_target(prev_actions=actions, rewards=rewards, observs=observs, current_actions=new_actions)
            min_next_q_target = torch.min(next_q1, next_q2)
            min_next_q_target += self.alpha_entropy * -new_log_probs
            q_target = rewards + (1.0 - dones) * gamma * min_next_q_target
            if not markov_critic:
                q_target = q_target[1:]
        if markov_critic:
            q1_pred = critic[0](observs, actions)
            q2_pred = critic[1](observs, actions)
        else:
            q1_pred, q2_pred = critic(prev_actions=actions, rewards=rewards, observs=observs, current_actions=actions[1:])
        return ((q1_pred, q2_pred), q_target)

    def actor_loss(self, markov_actor: bool, markov_critic: bool, actor, actor_target, critic, critic_target, observs, actions=None, rewards=None):
        if markov_actor:
            new_actions, log_probs = self.forward_actor(actor, observs)
        else:
            new_actions, log_probs = actor(prev_actions=actions, rewards=rewards, observs=observs)
        if markov_critic:
            q1 = critic[0](observs, new_actions)
            q2 = critic[1](observs, new_actions)
        else:
            q1, q2 = critic(prev_actions=actions, rewards=rewards, observs=observs, current_actions=new_actions)
        min_q_new_actions = torch.min(q1, q2)
        policy_loss = -min_q_new_actions
        policy_loss += self.alpha_entropy * log_probs
        if not markov_critic:
            policy_loss = policy_loss[:-1]
        return (policy_loss, log_probs)

    def forward_actor_in_target(self, actor, actor_target, next_observ):
        return self.forward_actor(actor, next_observ)

    def entropy_bonus(self, log_probs):
        return self.alpha_entropy * -log_probs

def __init__(self, entropy_alpha=0.1, automatic_entropy_tuning=True, target_entropy=None, alpha_lr=0.0003, action_dim=None):
    self.automatic_entropy_tuning = automatic_entropy_tuning
    if self.automatic_entropy_tuning:
        if target_entropy is not None:
            self.target_entropy = float(target_entropy)
        else:
            self.target_entropy = -float(action_dim)
        self.log_alpha_entropy = torch.zeros(1, requires_grad=True, device=ptu.device)
        self.alpha_entropy_optim = Adam([self.log_alpha_entropy], lr=alpha_lr)
        self.alpha_entropy = self.log_alpha_entropy.exp().detach().item()
    else:
        self.alpha_entropy = entropy_alpha

def update_others(self, current_log_probs):
    if self.automatic_entropy_tuning:
        alpha_entropy_loss = -self.log_alpha_entropy.exp() * (current_log_probs + self.target_entropy)
        self.alpha_entropy_optim.zero_grad()
        alpha_entropy_loss.backward()
        self.alpha_entropy_optim.step()
        self.alpha_entropy = self.log_alpha_entropy.exp().item()
    return {'policy_entropy': -current_log_probs, 'alpha': self.alpha_entropy}

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

