# Cluster 13

class PrioritizedReplayBuffer(object):

    def __init__(self, opt):
        self.ptr = 0
        self.size = 0
        max_size = int(opt.buffer_size)
        self.state = np.zeros((max_size, opt.state_dim))
        self.action = np.zeros((max_size, 1))
        self.reward = np.zeros((max_size, 1))
        self.next_state = np.zeros((max_size, opt.state_dim))
        self.dw = np.zeros((max_size, 1))
        self.max_size = max_size
        self.sum_tree = SumTree(max_size)
        self.alpha = opt.alpha
        self.beta = opt.beta_init
        self.device = device

    def add(self, state, action, reward, next_state, dw):
        self.state[self.ptr] = state
        self.action[self.ptr] = action
        self.reward[self.ptr] = reward
        self.next_state[self.ptr] = next_state
        self.dw[self.ptr] = dw
        priority = 1.0 if self.size == 0 else self.sum_tree.priority_max
        self.sum_tree.update_priority(data_index=self.ptr, priority=priority)
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind, Normed_IS_weight = self.sum_tree.prioritized_sample(N=self.size, batch_size=batch_size, beta=self.beta)
        return (torch.tensor(self.state[ind], dtype=torch.float32).to(self.device), torch.tensor(self.action[ind], dtype=torch.long).to(self.device), torch.tensor(self.reward[ind], dtype=torch.float32).to(self.device), torch.tensor(self.next_state[ind], dtype=torch.float32).to(self.device), torch.tensor(self.dw[ind], dtype=torch.float32).to(self.device), ind, Normed_IS_weight.to(self.device))

    def update_batch_priorities(self, batch_index, td_errors):
        priorities = (np.abs(td_errors) + 0.01) ** self.alpha
        for index, priority in zip(batch_index, priorities):
            self.sum_tree.update_priority(data_index=index, priority=priority)

def add(self, state, action, reward, next_state, dw):
    self.state[self.ptr] = state
    self.action[self.ptr] = action
    self.reward[self.ptr] = reward
    self.next_state[self.ptr] = next_state
    self.dw[self.ptr] = dw
    priority = 1.0 if self.size == 0 else self.sum_tree.priority_max
    self.sum_tree.update_priority(data_index=self.ptr, priority=priority)
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

def update_batch_priorities(self, batch_index, td_errors):
    priorities = (np.abs(td_errors) + 0.01) ** self.alpha
    for index, priority in zip(batch_index, priorities):
        self.sum_tree.update_priority(data_index=index, priority=priority)

class PrioritizedReplayBuffer(object):

    def __init__(self, opt):
        self.ptr = 0
        self.size = 0
        max_size = int(opt.buffer_size)
        self.state = np.zeros((max_size, opt.state_dim))
        self.action = np.zeros((max_size, 1))
        self.reward = np.zeros((max_size, 1))
        self.next_state = np.zeros((max_size, opt.state_dim))
        self.dw = np.zeros((max_size, 1))
        self.max_size = max_size
        self.sum_tree = SumTree(max_size)
        self.alpha = opt.alpha
        self.beta = opt.beta_init
        self.device = device

    def add(self, state, action, reward, next_state, dw):
        self.state[self.ptr] = state
        self.action[self.ptr] = action
        self.reward[self.ptr] = reward
        self.next_state[self.ptr] = next_state
        self.dw[self.ptr] = dw
        priority = 1.0 if self.size == 0 else self.sum_tree.priority_max
        self.sum_tree.update_priority(data_index=self.ptr, priority=priority)
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind, Normed_IS_weight = self.sum_tree.prioritized_sample(N=self.size, batch_size=batch_size, beta=self.beta)
        return (torch.tensor(self.state[ind], dtype=torch.float32).to(self.device), torch.tensor(self.action[ind], dtype=torch.long).to(self.device), torch.tensor(self.reward[ind], dtype=torch.float32).to(self.device), torch.tensor(self.next_state[ind], dtype=torch.float32).to(self.device), torch.tensor(self.dw[ind], dtype=torch.float32).to(self.device), ind, Normed_IS_weight.to(self.device))

    def update_batch_priorities(self, batch_index, td_errors):
        priorities = (np.abs(td_errors) + 0.01) ** self.alpha
        for index, priority in zip(batch_index, priorities):
            self.sum_tree.update_priority(data_index=index, priority=priority)

def add(self, state, action, reward, next_state, dw):
    self.state[self.ptr] = state
    self.action[self.ptr] = action
    self.reward[self.ptr] = reward
    self.next_state[self.ptr] = next_state
    self.dw[self.ptr] = dw
    priority = 1.0 if self.size == 0 else self.sum_tree.priority_max
    self.sum_tree.update_priority(data_index=self.ptr, priority=priority)
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

def update_batch_priorities(self, batch_index, td_errors):
    priorities = (np.abs(td_errors) + 0.01) ** self.alpha
    for index, priority in zip(batch_index, priorities):
        self.sum_tree.update_priority(data_index=index, priority=priority)

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

def scale_noise(self, size):
    x = torch.randn(size)
    x = x.sign().mul(x.abs().sqrt())
    return x

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

def reward(self, reward):
    """Bin reward to {+1, 0, -1} by its sign. Note: np.sign(0) == 0."""
    return np.sign(reward)

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

def scale_noise(self, size):
    x = torch.randn(size)
    x = x.sign().mul(x.abs().sqrt())
    return x

