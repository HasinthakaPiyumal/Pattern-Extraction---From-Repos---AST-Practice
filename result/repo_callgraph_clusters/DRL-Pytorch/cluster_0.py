# Cluster 0

class Actor(nn.Module):

    def __init__(self, state_dim, action_dim, net_width, maxaction):
        super(Actor, self).__init__()
        self.l1 = nn.Linear(state_dim, net_width)
        self.l2 = nn.Linear(net_width, 300)
        self.l3 = nn.Linear(300, action_dim)
        self.maxaction = maxaction

    def forward(self, state):
        a = torch.relu(self.l1(state))
        a = torch.relu(self.l2(a))
        a = torch.tanh(self.l3(a)) * self.maxaction
        return a

def __init__(self, state_dim, action_dim, net_width, maxaction):
    super(Actor, self).__init__()
    self.l1 = nn.Linear(state_dim, net_width)
    self.l2 = nn.Linear(net_width, 300)
    self.l3 = nn.Linear(300, action_dim)
    self.maxaction = maxaction

class Q_Critic(nn.Module):

    def __init__(self, state_dim, action_dim, net_width):
        super(Q_Critic, self).__init__()
        self.l1 = nn.Linear(state_dim + action_dim, net_width)
        self.l2 = nn.Linear(net_width, 300)
        self.l3 = nn.Linear(300, 1)

    def forward(self, state, action):
        sa = torch.cat([state, action], 1)
        q = F.relu(self.l1(sa))
        q = F.relu(self.l2(q))
        q = self.l3(q)
        return q

def __init__(self, state_dim, action_dim, net_width):
    super(Q_Critic, self).__init__()
    self.l1 = nn.Linear(state_dim + action_dim, net_width)
    self.l2 = nn.Linear(net_width, 300)
    self.l3 = nn.Linear(300, 1)

def build_net(layer_shape, activation, output_activation):
    """build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q = self.Q(s)
        return q

def __init__(self, state_dim, action_dim, hid_shape):
    super(Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.Q = build_net(layers, nn.ReLU, nn.Identity)

def build_net(layer_shape, activation, output_activation):
    """build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q = self.Q(s)
        return q

def __init__(self, state_dim, action_dim, hid_shape):
    super(Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.Q = build_net(layers, nn.ReLU, nn.Identity)

def build_net(layer_shape, activation, output_activation):
    """build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q = self.Q(s)
        return q

def __init__(self, state_dim, action_dim, hid_shape):
    super(Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.Q = build_net(layers, nn.ReLU, nn.Identity)

class NoisyLinear(nn.Module):
    """From https://github.com/Lizhi-sjtu/DRL-code-pytorch/blob/main/3.Rainbow_DQN/network.py"""

    def __init__(self, in_features, out_features, sigma_init=0.5):
        super(NoisyLinear, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.sigma_init = sigma_init
        self.weight_mu = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.register_buffer('weight_epsilon', torch.FloatTensor(out_features, in_features))
        self.bias_mu = nn.Parameter(torch.FloatTensor(out_features))
        self.bias_sigma = nn.Parameter(torch.FloatTensor(out_features))
        self.register_buffer('bias_epsilon', torch.FloatTensor(out_features))
        self.reset_parameters()
        self.reset_noise()

    def forward(self, x):
        if self.training:
            self.reset_noise()
            weight = self.weight_mu + self.weight_sigma.mul(self.weight_epsilon)
            bias = self.bias_mu + self.bias_sigma.mul(self.bias_epsilon)
        else:
            weight = self.weight_mu
            bias = self.bias_mu
        return F.linear(x, weight, bias)

    def reset_parameters(self):
        mu_range = 1 / math.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        self.weight_sigma.data.fill_(self.sigma_init / math.sqrt(self.in_features))
        self.bias_sigma.data.fill_(self.sigma_init / math.sqrt(self.out_features))

    def reset_noise(self):
        epsilon_i = self.scale_noise(self.in_features)
        epsilon_j = self.scale_noise(self.out_features)
        self.weight_epsilon.copy_(torch.ger(epsilon_j, epsilon_i))
        self.bias_epsilon.copy_(epsilon_j)

    def scale_noise(self, size):
        x = torch.randn(size)
        x = x.sign().mul(x.abs().sqrt())
        return x

def __init__(self, in_features, out_features, sigma_init=0.5):
    super(NoisyLinear, self).__init__()
    self.in_features = in_features
    self.out_features = out_features
    self.sigma_init = sigma_init
    self.weight_mu = nn.Parameter(torch.FloatTensor(out_features, in_features))
    self.weight_sigma = nn.Parameter(torch.FloatTensor(out_features, in_features))
    self.register_buffer('weight_epsilon', torch.FloatTensor(out_features, in_features))
    self.bias_mu = nn.Parameter(torch.FloatTensor(out_features))
    self.bias_sigma = nn.Parameter(torch.FloatTensor(out_features))
    self.register_buffer('bias_epsilon', torch.FloatTensor(out_features))
    self.reset_parameters()
    self.reset_noise()

def _parse_reset_result(reset_result):
    contains_info = isinstance(reset_result, tuple) and len(reset_result) == 2 and isinstance(reset_result[1], dict)
    if contains_info:
        return (reset_result[0], reset_result[1], contains_info)
    return (reset_result, {}, contains_info)

class NoopResetEnv(gym.Wrapper):
    """Sample initial states by taking random number of no-ops on reset.

    No-op is assumed to be action 0.

    :param gym.Env env: the environment to wrap.
    :param int noop_max: the maximum value of no-ops to run.
    """

    def __init__(self, env, noop_max=30) -> None:
        super().__init__(env)
        self.noop_max = noop_max
        self.noop_action = 0
        assert env.unwrapped.get_action_meanings()[0] == 'NOOP'

    def reset(self, **kwargs):
        _, info, return_info = _parse_reset_result(self.env.reset(**kwargs))
        if hasattr(self.unwrapped.np_random, 'integers'):
            noops = self.unwrapped.np_random.integers(1, self.noop_max + 1)
        else:
            noops = self.unwrapped.np_random.randint(1, self.noop_max + 1)
        for _ in range(noops):
            step_result = self.env.step(self.noop_action)
            if len(step_result) == 4:
                obs, rew, done, info = step_result
            else:
                obs, rew, term, trunc, info = step_result
                done = term or trunc
            if done:
                obs, info, _ = _parse_reset_result(self.env.reset())
        if return_info:
            return (obs, info)
        return obs

def __init__(self, env, noop_max=30) -> None:
    super().__init__(env)
    self.noop_max = noop_max
    self.noop_action = 0
    assert env.unwrapped.get_action_meanings()[0] == 'NOOP'

class MaxAndSkipEnv(gym.Wrapper):
    """Return only every `skip`-th frame (frameskipping) using most recent raw observations (for max pooling across time steps).

    :param gym.Env env: the environment to wrap.
    :param int skip: number of `skip`-th frame.
    """

    def __init__(self, env, skip=4) -> None:
        super().__init__(env)
        self._skip = skip

    def step(self, action):
        """Step the environment with the given action.

        Repeat action, sum reward, and max over last observations.
        """
        obs_list, total_reward = ([], 0.0)
        new_step_api = False
        for _ in range(self._skip):
            step_result = self.env.step(action)
            if len(step_result) == 4:
                obs, reward, done, info = step_result
            else:
                obs, reward, term, trunc, info = step_result
                done = term or trunc
                new_step_api = True
            obs_list.append(obs)
            total_reward += reward
            if done:
                break
        max_frame = np.max(obs_list[-2:], axis=0)
        if new_step_api:
            return (max_frame, total_reward, term, trunc, info)
        return (max_frame, total_reward, done, info)

def __init__(self, env, skip=4) -> None:
    super().__init__(env)
    self._skip = skip

class EpisodicLifeEnv(gym.Wrapper):
    """Make end-of-life == end-of-episode, but only reset on true game over.

    It helps the value estimation.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        self.lives = 0
        self.was_real_done = True
        self._return_info = False

    def step(self, action):
        step_result = self.env.step(action)
        if len(step_result) == 4:
            obs, reward, done, info = step_result
            new_step_api = False
        else:
            obs, reward, term, trunc, info = step_result
            done = term or trunc
            new_step_api = True
        self.was_real_done = done
        lives = self.env.unwrapped.ale.lives()
        if 0 < lives < self.lives:
            done = True
            term = True
        self.lives = lives
        if new_step_api:
            return (obs, reward, term, trunc, info)
        return (obs, reward, done, info)

    def reset(self, **kwargs):
        """Calls the Gym environment reset, only when lives are exhausted.

        This way all states are still reachable even though lives are episodic, and
        the learner need not know about any of this behind-the-scenes.
        """
        if self.was_real_done:
            obs, info, self._return_info = _parse_reset_result(self.env.reset(**kwargs))
        else:
            step_result = self.env.step(0)
            obs, info = (step_result[0], step_result[-1])
        self.lives = self.env.unwrapped.ale.lives()
        if self._return_info:
            return (obs, info)
        return obs

def __init__(self, env) -> None:
    super().__init__(env)
    self.lives = 0
    self.was_real_done = True
    self._return_info = False

class FireResetEnv(gym.Wrapper):
    """Take action on reset for environments that are fixed until firing.

    Related discussion: https://github.com/openai/baselines/issues/240.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        assert env.unwrapped.get_action_meanings()[1] == 'FIRE'
        assert len(env.unwrapped.get_action_meanings()) >= 3

    def reset(self, **kwargs):
        _, _, return_info = _parse_reset_result(self.env.reset(**kwargs))
        obs = self.env.step(1)[0]
        return (obs, {}) if return_info else obs

def __init__(self, env) -> None:
    super().__init__(env)
    assert env.unwrapped.get_action_meanings()[1] == 'FIRE'
    assert len(env.unwrapped.get_action_meanings()) >= 3

class WarpFrame(gym.ObservationWrapper):
    """Warp frames to 84x84 as done in the Nature paper and later work.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        self.size = 84
        self.observation_space = gym.spaces.Box(low=np.min(env.observation_space.low), high=np.max(env.observation_space.high), shape=(self.size, self.size), dtype=env.observation_space.dtype)

    def observation(self, frame):
        """Returns the current observation from a frame."""
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return cv2.resize(frame, (self.size, self.size), interpolation=cv2.INTER_AREA)

def __init__(self, env) -> None:
    super().__init__(env)
    self.size = 84
    self.observation_space = gym.spaces.Box(low=np.min(env.observation_space.low), high=np.max(env.observation_space.high), shape=(self.size, self.size), dtype=env.observation_space.dtype)

class ClipRewardEnv(gym.RewardWrapper):
    """clips the reward to {+1, 0, -1} by its sign.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        self.reward_range = (-1, 1)

    def reward(self, reward):
        """Bin reward to {+1, 0, -1} by its sign. Note: np.sign(0) == 0."""
        return np.sign(reward)

def __init__(self, env) -> None:
    super().__init__(env)
    self.reward_range = (-1, 1)

class FrameStack(gym.Wrapper):
    """Stack n_frames last frames.

    :param gym.Env env: the environment to wrap.
    :param int n_frames: the number of frames to stack.
    """

    def __init__(self, env, n_frames) -> None:
        super().__init__(env)
        self.n_frames = n_frames
        self.frames = deque([], maxlen=n_frames)
        shape = (n_frames, *env.observation_space.shape)
        self.observation_space = gym.spaces.Box(low=np.min(env.observation_space.low), high=np.max(env.observation_space.high), shape=shape, dtype=env.observation_space.dtype)

    def reset(self, **kwargs):
        obs, info, return_info = _parse_reset_result(self.env.reset(**kwargs))
        for _ in range(self.n_frames):
            self.frames.append(obs)
        return (self._get_ob(), info) if return_info else self._get_ob()

    def step(self, action):
        step_result = self.env.step(action)
        if len(step_result) == 4:
            obs, reward, done, info = step_result
            new_step_api = False
        else:
            obs, reward, term, trunc, info = step_result
            new_step_api = True
        self.frames.append(obs)
        if new_step_api:
            return (self._get_ob(), reward, term, trunc, info)
        return (self._get_ob(), reward, done, info)

    def _get_ob(self):
        """Note that here is different from original Tianshou Wrapper"""
        return torch.tensor(np.stack(self.frames, axis=0), dtype=torch.uint8)

def __init__(self, env, n_frames) -> None:
    super().__init__(env)
    self.n_frames = n_frames
    self.frames = deque([], maxlen=n_frames)
    shape = (n_frames, *env.observation_space.shape)
    self.observation_space = gym.spaces.Box(low=np.min(env.observation_space.low), high=np.max(env.observation_space.high), shape=shape, dtype=env.observation_space.dtype)

class Q_Net(nn.Module):

    def __init__(self, opt):
        super(Q_Net, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten())
        if opt.Noisy:
            self.fc1 = NoisyLinear(64 * 7 * 7, opt.fc_width)
            self.fc2 = NoisyLinear(opt.fc_width, opt.action_dim)
        else:
            self.fc1 = nn.Linear(64 * 7 * 7, opt.fc_width)
            self.fc2 = nn.Linear(opt.fc_width, opt.action_dim)

    def forward(self, obs):
        s = obs.float() / 255
        s = self.conv(s)
        s = torch.relu(self.fc1(s))
        q = self.fc2(s)
        return q

def __init__(self, opt):
    super(Q_Net, self).__init__()
    self.conv = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten())
    if opt.Noisy:
        self.fc1 = NoisyLinear(64 * 7 * 7, opt.fc_width)
        self.fc2 = NoisyLinear(opt.fc_width, opt.action_dim)
    else:
        self.fc1 = nn.Linear(64 * 7 * 7, opt.fc_width)
        self.fc2 = nn.Linear(opt.fc_width, opt.action_dim)

class Duel_Q_Net(nn.Module):

    def __init__(self, opt):
        super(Duel_Q_Net, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten())
        if opt.Noisy:
            self.fc = NoisyLinear(64 * 7 * 7, opt.fc_width)
            self.A = NoisyLinear(opt.fc_width, opt.action_dim)
            self.V = NoisyLinear(opt.fc_width, 1)
        else:
            self.fc = nn.Linear(64 * 7 * 7, opt.fc_width)
            self.A = nn.Linear(opt.fc_width, opt.action_dim)
            self.V = nn.Linear(opt.fc_width, 1)

    def forward(self, obs):
        s = obs.float() / 255
        s = self.conv(s)
        s = torch.relu(self.fc(s))
        Adv = self.A(s)
        V = self.V(s)
        Q = V + (Adv - torch.mean(Adv, dim=-1, keepdim=True))
        return Q

def __init__(self, opt):
    super(Duel_Q_Net, self).__init__()
    self.conv = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten())
    if opt.Noisy:
        self.fc = NoisyLinear(64 * 7 * 7, opt.fc_width)
        self.A = NoisyLinear(opt.fc_width, opt.action_dim)
        self.V = NoisyLinear(opt.fc_width, 1)
    else:
        self.fc = nn.Linear(64 * 7 * 7, opt.fc_width)
        self.A = nn.Linear(opt.fc_width, opt.action_dim)
        self.V = nn.Linear(opt.fc_width, 1)

def build_net(layer_shape, hid_activation, output_activation):
    """build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = hid_activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Double_Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Double_Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q1 = build_net(layers, nn.ReLU, nn.Identity)
        self.Q2 = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q1 = self.Q1(s)
        q2 = self.Q2(s)
        return (q1, q2)

def __init__(self, state_dim, action_dim, hid_shape):
    super(Double_Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.Q1 = build_net(layers, nn.ReLU, nn.Identity)
    self.Q2 = build_net(layers, nn.ReLU, nn.Identity)

class Policy_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Policy_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.P = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        logits = self.P(s)
        probs = F.softmax(logits, dim=1)
        return probs

def __init__(self, state_dim, action_dim, hid_shape):
    super(Policy_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.P = build_net(layers, nn.ReLU, nn.Identity)

class Actor(nn.Module):

    def __init__(self, state_dim, action_dim, net_width, maxaction):
        super(Actor, self).__init__()
        self.l1 = nn.Linear(state_dim, net_width)
        self.l2 = nn.Linear(net_width, net_width)
        self.l3 = nn.Linear(net_width, action_dim)
        self.maxaction = maxaction

    def forward(self, state):
        a = torch.tanh(self.l1(state))
        a = torch.tanh(self.l2(a))
        a = torch.tanh(self.l3(a)) * self.maxaction
        return a

def __init__(self, state_dim, action_dim, net_width, maxaction):
    super(Actor, self).__init__()
    self.l1 = nn.Linear(state_dim, net_width)
    self.l2 = nn.Linear(net_width, net_width)
    self.l3 = nn.Linear(net_width, action_dim)
    self.maxaction = maxaction

class Double_Q_Critic(nn.Module):

    def __init__(self, state_dim, action_dim, net_width):
        super(Double_Q_Critic, self).__init__()
        self.l1 = nn.Linear(state_dim + action_dim, net_width)
        self.l2 = nn.Linear(net_width, net_width)
        self.l3 = nn.Linear(net_width, 1)
        self.l4 = nn.Linear(state_dim + action_dim, net_width)
        self.l5 = nn.Linear(net_width, net_width)
        self.l6 = nn.Linear(net_width, 1)

    def forward(self, state, action):
        sa = torch.cat([state, action], 1)
        q1 = F.relu(self.l1(sa))
        q1 = F.relu(self.l2(q1))
        q1 = self.l3(q1)
        q2 = F.relu(self.l4(sa))
        q2 = F.relu(self.l5(q2))
        q2 = self.l6(q2)
        return (q1, q2)

    def Q1(self, state, action):
        sa = torch.cat([state, action], 1)
        q1 = F.relu(self.l1(sa))
        q1 = F.relu(self.l2(q1))
        q1 = self.l3(q1)
        return q1

def __init__(self, state_dim, action_dim, net_width):
    super(Double_Q_Critic, self).__init__()
    self.l1 = nn.Linear(state_dim + action_dim, net_width)
    self.l2 = nn.Linear(net_width, net_width)
    self.l3 = nn.Linear(net_width, 1)
    self.l4 = nn.Linear(state_dim + action_dim, net_width)
    self.l5 = nn.Linear(net_width, net_width)
    self.l6 = nn.Linear(net_width, 1)

def build_net(layer_shape, activation, output_activation):
    """Build networks with For loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q = self.Q(s)
        return q

def __init__(self, state_dim, action_dim, hid_shape):
    super(Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.Q = build_net(layers, nn.ReLU, nn.Identity)

class Duel_Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Duel_Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape)
        self.hidden = build_net(layers, nn.ReLU, nn.ReLU)
        self.V = nn.Linear(hid_shape[-1], 1)
        self.A = nn.Linear(hid_shape[-1], action_dim)

    def forward(self, s):
        s = self.hidden(s)
        Adv = self.A(s)
        V = self.V(s)
        Q = V + (Adv - torch.mean(Adv, dim=-1, keepdim=True))
        return Q

def __init__(self, state_dim, action_dim, hid_shape):
    super(Duel_Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape)
    self.hidden = build_net(layers, nn.ReLU, nn.ReLU)
    self.V = nn.Linear(hid_shape[-1], 1)
    self.A = nn.Linear(hid_shape[-1], action_dim)

class Q_Net(nn.Module):

    def __init__(self, action_dim, hidden):
        super(Q_Net, self).__init__()
        self.net = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten(), nn.Linear(64 * 7 * 7, hidden), nn.ReLU(), nn.Linear(hidden, action_dim))

    def forward(self, obs):
        s = obs.float() / 255
        q = self.net(s)
        return q

    def orthogonal_init(self, layer, gain=1.4142):
        for name, param in layer.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                nn.init.orthogonal_(param, gain=gain)
        return layer

def __init__(self, action_dim, hidden):
    super(Q_Net, self).__init__()
    self.net = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten(), nn.Linear(64 * 7 * 7, hidden), nn.ReLU(), nn.Linear(hidden, action_dim))

class shared_data_cuda(shared_data_cpu):
    """Using Cuda to store expriences"""

    def __init__(self, opt):
        super(shared_data_cuda, self).__init__(opt)

    def add_core(self, trans):
        """add transitions to buffer,without thread lock"""
        s, a, r, dw, ct = trans
        self.s[self.ptr] = torch.from_numpy(s).to(self.B_dvc)
        self.a[self.ptr] = torch.from_numpy(a).unsqueeze(-1).to(self.B_dvc)
        self.r[self.ptr] = torch.from_numpy(r).unsqueeze(-1).to(self.B_dvc)
        self.dw[self.ptr] = torch.from_numpy(dw).unsqueeze(-1).to(self.B_dvc)
        self.ct[self.ptr] = torch.from_numpy(ct).unsqueeze(-1).to(self.B_dvc)
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)
        if self.size == self.max_size:
            self.full = True

    def sample_core(self):
        """sample batch transitions, without thread lock"""
        if not self.full:
            ind = torch.randint(low=0, high=self.ptr - 1, size=(self.batch_size,), device=self.B_dvc)
        else:
            ind = torch.randint(low=0, high=self.size - 1, size=(self.batch_size,), device=self.B_dvc)
            if self.ptr - 1 in ind:
                ind = ind[ind != self.ptr - 1]
        env_ind = torch.randint(low=0, high=self.train_envs, size=(len(ind),), device=self.B_dvc)
        return (self.s[ind, env_ind, :], self.a[ind, env_ind, :], self.r[ind, env_ind, :], self.s[ind + 1, env_ind, :], self.dw[ind, env_ind, :], self.ct[ind, env_ind, :])

def __init__(self, opt):
    super(shared_data_cuda, self).__init__(opt)

class NoisyLinear(nn.Module):
    """From https://github.com/Lizhi-sjtu/DRL-code-pytorch/blob/main/3.Rainbow_DQN/network.py"""

    def __init__(self, in_features, out_features, sigma_init=0.5):
        super(NoisyLinear, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.sigma_init = sigma_init
        self.weight_mu = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.register_buffer('weight_epsilon', torch.FloatTensor(out_features, in_features))
        self.bias_mu = nn.Parameter(torch.FloatTensor(out_features))
        self.bias_sigma = nn.Parameter(torch.FloatTensor(out_features))
        self.register_buffer('bias_epsilon', torch.FloatTensor(out_features))
        self.reset_parameters()
        self.reset_noise()

    def forward(self, x):
        if self.training:
            self.reset_noise()
            weight = self.weight_mu + self.weight_sigma.mul(self.weight_epsilon)
            bias = self.bias_mu + self.bias_sigma.mul(self.bias_epsilon)
        else:
            weight = self.weight_mu
            bias = self.bias_mu
        return F.linear(x, weight, bias)

    def reset_parameters(self):
        mu_range = 1 / math.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        self.weight_sigma.data.fill_(self.sigma_init / math.sqrt(self.in_features))
        self.bias_sigma.data.fill_(self.sigma_init / math.sqrt(self.out_features))

    def reset_noise(self):
        epsilon_i = self.scale_noise(self.in_features)
        epsilon_j = self.scale_noise(self.out_features)
        self.weight_epsilon.copy_(torch.ger(epsilon_j, epsilon_i))
        self.bias_epsilon.copy_(epsilon_j)

    def scale_noise(self, size):
        x = torch.randn(size)
        x = x.sign().mul(x.abs().sqrt())
        return x

def __init__(self, in_features, out_features, sigma_init=0.5):
    super(NoisyLinear, self).__init__()
    self.in_features = in_features
    self.out_features = out_features
    self.sigma_init = sigma_init
    self.weight_mu = nn.Parameter(torch.FloatTensor(out_features, in_features))
    self.weight_sigma = nn.Parameter(torch.FloatTensor(out_features, in_features))
    self.register_buffer('weight_epsilon', torch.FloatTensor(out_features, in_features))
    self.bias_mu = nn.Parameter(torch.FloatTensor(out_features))
    self.bias_sigma = nn.Parameter(torch.FloatTensor(out_features))
    self.register_buffer('bias_epsilon', torch.FloatTensor(out_features))
    self.reset_parameters()
    self.reset_noise()

def build_net(layer_shape, activation, output_activation):
    """Build networks with For loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        if j < len(layer_shape) - 2:
            layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), activation()]
        else:
            layers += [NoisyLinear(layer_shape[j], layer_shape[j + 1], sigma_init=0.25), output_activation()]
    return nn.Sequential(*layers)

class Noisy_Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Noisy_Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q = self.Q(s)
        return q

def __init__(self, state_dim, action_dim, hid_shape):
    super(Noisy_Q_Net, self).__init__()
    layers = [state_dim] + list(hid_shape) + [action_dim]
    self.Q = build_net(layers, nn.ReLU, nn.Identity)

class BetaActor(nn.Module):

    def __init__(self, state_dim, action_dim, net_width):
        super(BetaActor, self).__init__()
        self.l1 = nn.Linear(state_dim, net_width)
        self.l2 = nn.Linear(net_width, net_width)
        self.alpha_head = nn.Linear(net_width, action_dim)
        self.beta_head = nn.Linear(net_width, action_dim)

    def forward(self, state):
        a = torch.tanh(self.l1(state))
        a = torch.tanh(self.l2(a))
        alpha = F.softplus(self.alpha_head(a)) + 1.0
        beta = F.softplus(self.beta_head(a)) + 1.0
        return (alpha, beta)

    def get_dist(self, state):
        alpha, beta = self.forward(state)
        dist = Beta(alpha, beta)
        return dist

    def deterministic_act(self, state):
        alpha, beta = self.forward(state)
        mode = alpha / (alpha + beta)
        return mode

def __init__(self, state_dim, action_dim, net_width):
    super(BetaActor, self).__init__()
    self.l1 = nn.Linear(state_dim, net_width)
    self.l2 = nn.Linear(net_width, net_width)
    self.alpha_head = nn.Linear(net_width, action_dim)
    self.beta_head = nn.Linear(net_width, action_dim)

class GaussianActor_musigma(nn.Module):

    def __init__(self, state_dim, action_dim, net_width):
        super(GaussianActor_musigma, self).__init__()
        self.l1 = nn.Linear(state_dim, net_width)
        self.l2 = nn.Linear(net_width, net_width)
        self.mu_head = nn.Linear(net_width, action_dim)
        self.sigma_head = nn.Linear(net_width, action_dim)

    def forward(self, state):
        a = torch.tanh(self.l1(state))
        a = torch.tanh(self.l2(a))
        mu = torch.sigmoid(self.mu_head(a))
        sigma = F.softplus(self.sigma_head(a))
        return (mu, sigma)

    def get_dist(self, state):
        mu, sigma = self.forward(state)
        dist = Normal(mu, sigma)
        return dist

    def deterministic_act(self, state):
        mu, sigma = self.forward(state)
        return mu

def __init__(self, state_dim, action_dim, net_width):
    super(GaussianActor_musigma, self).__init__()
    self.l1 = nn.Linear(state_dim, net_width)
    self.l2 = nn.Linear(net_width, net_width)
    self.mu_head = nn.Linear(net_width, action_dim)
    self.sigma_head = nn.Linear(net_width, action_dim)

class GaussianActor_mu(nn.Module):

    def __init__(self, state_dim, action_dim, net_width, log_std=0):
        super(GaussianActor_mu, self).__init__()
        self.l1 = nn.Linear(state_dim, net_width)
        self.l2 = nn.Linear(net_width, net_width)
        self.mu_head = nn.Linear(net_width, action_dim)
        self.mu_head.weight.data.mul_(0.1)
        self.mu_head.bias.data.mul_(0.0)
        self.action_log_std = nn.Parameter(torch.ones(1, action_dim) * log_std)

    def forward(self, state):
        a = torch.relu(self.l1(state))
        a = torch.relu(self.l2(a))
        mu = torch.sigmoid(self.mu_head(a))
        return mu

    def get_dist(self, state):
        mu = self.forward(state)
        action_log_std = self.action_log_std.expand_as(mu)
        action_std = torch.exp(action_log_std)
        dist = Normal(mu, action_std)
        return dist

    def deterministic_act(self, state):
        return self.forward(state)

def __init__(self, state_dim, action_dim, net_width, log_std=0):
    super(GaussianActor_mu, self).__init__()
    self.l1 = nn.Linear(state_dim, net_width)
    self.l2 = nn.Linear(net_width, net_width)
    self.mu_head = nn.Linear(net_width, action_dim)
    self.mu_head.weight.data.mul_(0.1)
    self.mu_head.bias.data.mul_(0.0)
    self.action_log_std = nn.Parameter(torch.ones(1, action_dim) * log_std)

class Critic(nn.Module):

    def __init__(self, state_dim, net_width):
        super(Critic, self).__init__()
        self.C1 = nn.Linear(state_dim, net_width)
        self.C2 = nn.Linear(net_width, net_width)
        self.C3 = nn.Linear(net_width, 1)

    def forward(self, state):
        v = torch.tanh(self.C1(state))
        v = torch.tanh(self.C2(v))
        v = self.C3(v)
        return v

def __init__(self, state_dim, net_width):
    super(Critic, self).__init__()
    self.C1 = nn.Linear(state_dim, net_width)
    self.C2 = nn.Linear(net_width, net_width)
    self.C3 = nn.Linear(net_width, 1)

class Actor(nn.Module):

    def __init__(self, state_dim, action_dim, net_width):
        super(Actor, self).__init__()
        self.l1 = nn.Linear(state_dim, net_width)
        self.l2 = nn.Linear(net_width, net_width)
        self.l3 = nn.Linear(net_width, action_dim)

    def forward(self, state):
        n = torch.tanh(self.l1(state))
        n = torch.tanh(self.l2(n))
        return n

    def pi(self, state, softmax_dim=0):
        n = self.forward(state)
        prob = F.softmax(self.l3(n), dim=softmax_dim)
        return prob

def __init__(self, state_dim, action_dim, net_width):
    super(Actor, self).__init__()
    self.l1 = nn.Linear(state_dim, net_width)
    self.l2 = nn.Linear(net_width, net_width)
    self.l3 = nn.Linear(net_width, action_dim)

class Critic(nn.Module):

    def __init__(self, state_dim, net_width):
        super(Critic, self).__init__()
        self.C1 = nn.Linear(state_dim, net_width)
        self.C2 = nn.Linear(net_width, net_width)
        self.C3 = nn.Linear(net_width, 1)

    def forward(self, state):
        v = torch.relu(self.C1(state))
        v = torch.relu(self.C2(v))
        v = self.C3(v)
        return v

def __init__(self, state_dim, net_width):
    super(Critic, self).__init__()
    self.C1 = nn.Linear(state_dim, net_width)
    self.C2 = nn.Linear(net_width, net_width)
    self.C3 = nn.Linear(net_width, 1)

def build_net(layer_shape, activation, output_activation):
    """build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Categorical_Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape, atoms):
        super(Categorical_Q_Net, self).__init__()
        self.atoms = atoms
        self.n_atoms = len(atoms)
        self.action_dim = action_dim
        layers = [state_dim] + list(hid_shape) + [action_dim * self.n_atoms]
        self.net = build_net(layers, nn.ReLU, nn.Identity)

    def _predict(self, state):
        logits = self.net(state)
        distributions = torch.softmax(logits.view(len(state), self.action_dim, self.n_atoms), dim=2)
        q_values = (distributions * self.atoms).sum(2)
        return (distributions, q_values)

    def forward(self, state, action=None):
        distributions, q_values = self._predict(state)
        if action is None:
            action = torch.argmax(q_values, dim=1)
        return (action, distributions[torch.arange(len(state)), action])

def __init__(self, state_dim, action_dim, hid_shape, atoms):
    super(Categorical_Q_Net, self).__init__()
    self.atoms = atoms
    self.n_atoms = len(atoms)
    self.action_dim = action_dim
    layers = [state_dim] + list(hid_shape) + [action_dim * self.n_atoms]
    self.net = build_net(layers, nn.ReLU, nn.Identity)

def build_net(layer_shape, hidden_activation, output_activation):
    """Build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = hidden_activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)

class Actor(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape, hidden_activation=nn.ReLU, output_activation=nn.ReLU):
        super(Actor, self).__init__()
        layers = [state_dim] + list(hid_shape)
        self.a_net = build_net(layers, hidden_activation, output_activation)
        self.mu_layer = nn.Linear(layers[-1], action_dim)
        self.log_std_layer = nn.Linear(layers[-1], action_dim)
        self.LOG_STD_MAX = 2
        self.LOG_STD_MIN = -20

    def forward(self, state, deterministic, with_logprob):
        """Network with Enforcing Action Bounds"""
        net_out = self.a_net(state)
        mu = self.mu_layer(net_out)
        log_std = self.log_std_layer(net_out)
        log_std = torch.clamp(log_std, self.LOG_STD_MIN, self.LOG_STD_MAX)
        std = torch.exp(log_std)
        dist = Normal(mu, std)
        if deterministic:
            u = mu
        else:
            u = dist.rsample()
        '↓↓↓ Enforcing Action Bounds, see Page 16 of https://arxiv.org/pdf/1812.05905.pdf ↓↓↓'
        a = torch.tanh(u)
        if with_logprob:
            logp_pi_a = dist.log_prob(u).sum(axis=1, keepdim=True) - (2 * (np.log(2) - u - F.softplus(-2 * u))).sum(axis=1, keepdim=True)
        else:
            logp_pi_a = None
        return (a, logp_pi_a)

def __init__(self, state_dim, action_dim, hid_shape, hidden_activation=nn.ReLU, output_activation=nn.ReLU):
    super(Actor, self).__init__()
    layers = [state_dim] + list(hid_shape)
    self.a_net = build_net(layers, hidden_activation, output_activation)
    self.mu_layer = nn.Linear(layers[-1], action_dim)
    self.log_std_layer = nn.Linear(layers[-1], action_dim)
    self.LOG_STD_MAX = 2
    self.LOG_STD_MIN = -20

class Double_Q_Critic(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Double_Q_Critic, self).__init__()
        layers = [state_dim + action_dim] + list(hid_shape) + [1]
        self.Q_1 = build_net(layers, nn.ReLU, nn.Identity)
        self.Q_2 = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, state, action):
        sa = torch.cat([state, action], 1)
        q1 = self.Q_1(sa)
        q2 = self.Q_2(sa)
        return (q1, q2)

def __init__(self, state_dim, action_dim, hid_shape):
    super(Double_Q_Critic, self).__init__()
    layers = [state_dim + action_dim] + list(hid_shape) + [1]
    self.Q_1 = build_net(layers, nn.ReLU, nn.Identity)
    self.Q_2 = build_net(layers, nn.ReLU, nn.Identity)

