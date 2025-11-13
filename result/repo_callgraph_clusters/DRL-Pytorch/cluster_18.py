# Cluster 18

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

def forward(self, state):
    a = torch.relu(self.l1(state))
    a = torch.relu(self.l2(a))
    a = torch.tanh(self.l3(a)) * self.maxaction
    return a

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

def forward(self, state, action):
    sa = torch.cat([state, action], 1)
    q = F.relu(self.l1(sa))
    q = F.relu(self.l2(q))
    q = self.l3(q)
    return q

class Policy_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Policy_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.P = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        logits = self.P(s)
        probs = F.softmax(logits, dim=1)
        return probs

def forward(self, s):
    logits = self.P(s)
    probs = F.softmax(logits, dim=1)
    return probs

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

def forward(self, state):
    a = torch.tanh(self.l1(state))
    a = torch.tanh(self.l2(a))
    a = torch.tanh(self.l3(a)) * self.maxaction
    return a

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

def forward(self, obs):
    s = obs.float() / 255
    q = self.net(s)
    return q

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

def forward(self, state):
    v = torch.tanh(self.C1(state))
    v = torch.tanh(self.C2(v))
    v = self.C3(v)
    return v

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

def forward(self, state):
    n = torch.tanh(self.l1(state))
    n = torch.tanh(self.l2(n))
    return n

def pi(self, state, softmax_dim=0):
    n = self.forward(state)
    prob = F.softmax(self.l3(n), dim=softmax_dim)
    return prob

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

def forward(self, state):
    v = torch.relu(self.C1(state))
    v = torch.relu(self.C2(v))
    v = self.C3(v)
    return v

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

def _predict(self, state):
    logits = self.net(state)
    distributions = torch.softmax(logits.view(len(state), self.action_dim, self.n_atoms), dim=2)
    q_values = (distributions * self.atoms).sum(2)
    return (distributions, q_values)

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

def forward(self, state, action):
    sa = torch.cat([state, action], 1)
    q1 = self.Q_1(sa)
    q2 = self.Q_2(sa)
    return (q1, q2)

