# Cluster 11

class ReplayBuffer:

    def __init__(self, state_dim, action_dim, max_size, dvc):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, action_dim), dtype=torch.float, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = torch.from_numpy(a).to(self.dvc)
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = torch.from_numpy(a).to(self.dvc)
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

class LinearSchedule(object):

    def __init__(self, schedule_timesteps, initial_p, final_p):
        """Linear interpolation between initial_p and final_p over
        schedule_timesteps. After this many timesteps pass final_p is
        returned.
        Parameters
        ----------
        schedule_timesteps: int
            Number of timesteps for which to linearly anneal initial_p
            to final_p
        initial_p: float
            initial output value
        final_p: float
            final output value
        """
        self.schedule_timesteps = schedule_timesteps
        self.initial_p = initial_p
        self.final_p = final_p

    def value(self, t):
        fraction = min(float(t) / self.schedule_timesteps, 1.0)
        return self.initial_p + fraction * (self.final_p - self.initial_p)

def value(self, t):
    fraction = min(float(t) / self.schedule_timesteps, 1.0)
    return self.initial_p + fraction * (self.final_p - self.initial_p)

class LinearSchedule(object):

    def __init__(self, schedule_timesteps, initial_p, final_p):
        """Linear interpolation between initial_p and final_p over
        schedule_timesteps. After this many timesteps pass final_p is
        returned.
        Parameters
        ----------
        schedule_timesteps: int
            Number of timesteps for which to linearly anneal initial_p
            to final_p
        initial_p: float
            initial output value
        final_p: float
            final output value
        """
        self.schedule_timesteps = schedule_timesteps
        self.initial_p = initial_p
        self.final_p = final_p

    def value(self, t):
        fraction = min(float(t) / self.schedule_timesteps, 1.0)
        return self.initial_p + fraction * (self.final_p - self.initial_p)

def value(self, t):
    fraction = min(float(t) / self.schedule_timesteps, 1.0)
    return self.initial_p + fraction * (self.final_p - self.initial_p)

class LightPriorReplayBuffer:
    """
    Obviate the need for explicately saving s_next, more menmory friendly, especially for image state.

    When iterating, use the following way to add new transitions:
        a = model.select(s)
        s_next, r, dw, tr, info = env.step(a)
        buffer.add(s, a, r, dw, tr)  
        # dw: whether the 's_next' is the terminal state
        # tr: whether the episode has been truncated.

    When sampling,
    ind = [ptr - 1] and ind = [size - 1] should be avoided to ensure the consistence of state[ind] and state[ind+1]
    Then,
    s = self.state[ind]
    s_next = self.state[ind+1]

    Importantly, because we do not explicitly save 's_next', when dw or tr is True, the s[ind] and s[ind+1] is not from one episode. 
    when encounter dw=True,
    self.state[ind+1] is not the true next state of self.state[ind], but a new resetted state.
    It doesn't matter, since Q_target[s[ind],a[ind]] = r[ind] + gamma*(1-dw[ind])* max_Q(s[ind+1],·),
    when dw=true, we won't use s[ind+1] at all.
    however, when encounter tr=True,
    self.state[ind+1] is not the true next state of self.state[ind], but a new resetted state, 
    so we have to discard this transition through (1-tr) in the loss function

    Thus, when training,
    Q_target = r + self.gamma * (1-dw) * max_q_next
    current_Q = self.q_net(s).gather(1,a)
    q_loss = torch.square((1-tr) * (current_Q - Q_target)).mean()

    """

    def __init__(self, opt):
        self.device = device
        self.ptr = 0
        self.size = 0
        self.state = torch.zeros((opt.buffer_size, opt.state_dim), device=device)
        self.action = torch.zeros((opt.buffer_size, 1), dtype=torch.int64, device=device)
        self.reward = torch.zeros((opt.buffer_size, 1), device=device)
        self.dw = torch.zeros((opt.buffer_size, 1), dtype=torch.bool, device=device)
        self.tr = torch.zeros((opt.buffer_size, 1), dtype=torch.bool, device=device)
        self.priorities = torch.zeros(opt.buffer_size, dtype=torch.float32, device=device)
        self.buffer_size = opt.buffer_size
        self.alpha = opt.alpha
        self.beta = opt.beta_init
        self.replacement = opt.replacement

    def add(self, state, action, reward, dw, tr, priority):
        self.state[self.ptr] = torch.from_numpy(state).to(device)
        self.action[self.ptr] = action
        self.reward[self.ptr] = reward
        self.dw[self.ptr] = dw
        self.tr[self.ptr] = tr
        self.priorities[self.ptr] = priority
        self.ptr = (self.ptr + 1) % self.buffer_size
        self.size = min(self.size + 1, self.buffer_size)

    def sample(self, batch_size):
        Prob_torch_gpu = self.priorities[0:self.size - 1].clone()
        if self.ptr < self.size:
            Prob_torch_gpu[self.ptr - 1] = 0
        ind = torch.multinomial(Prob_torch_gpu, num_samples=batch_size, replacement=self.replacement)
        IS_weight = (self.size * Prob_torch_gpu[ind]) ** (-self.beta)
        Normed_IS_weight = (IS_weight / IS_weight.max()).unsqueeze(-1)
        return (self.state[ind], self.action[ind], self.reward[ind], self.state[ind + 1], self.dw[ind], self.tr[ind], ind, Normed_IS_weight)

def add(self, state, action, reward, dw, tr, priority):
    self.state[self.ptr] = torch.from_numpy(state).to(device)
    self.action[self.ptr] = action
    self.reward[self.ptr] = reward
    self.dw[self.ptr] = dw
    self.tr[self.ptr] = tr
    self.priorities[self.ptr] = priority
    self.ptr = (self.ptr + 1) % self.buffer_size
    self.size = min(self.size + 1, self.buffer_size)

class LinearSchedule(object):

    def __init__(self, schedule_timesteps, initial_p, final_p):
        """Linear interpolation between initial_p and final_p over
        schedule_timesteps. After this many timesteps pass final_p is
        returned.
        Parameters
        ----------
        schedule_timesteps: int
            Number of timesteps for which to linearly anneal initial_p
            to final_p
        initial_p: float
            initial output value
        final_p: float
            final output value
        """
        self.schedule_timesteps = schedule_timesteps
        self.initial_p = initial_p
        self.final_p = final_p

    def value(self, t):
        fraction = min(float(t) / self.schedule_timesteps, 1.0)
        return self.initial_p + fraction * (self.final_p - self.initial_p)

def value(self, t):
    fraction = min(float(t) / self.schedule_timesteps, 1.0)
    return self.initial_p + fraction * (self.final_p - self.initial_p)

class LinearSchedule(object):

    def __init__(self, schedule_timesteps, final_p, initial_p=1.0):
        """Linear interpolation between initial_p and final_p over
        schedule_timesteps. After this many timesteps pass final_p is
        returned.

        Parameters
        ----------
        schedule_timesteps: int
            Number of timesteps for which to linearly anneal initial_p
            to final_p
        initial_p: float
            initial output value
        final_p: float
            final output value
        """
        self.schedule_timesteps = schedule_timesteps
        self.final_p = final_p
        self.initial_p = initial_p

    def value(self, t):
        fraction = min(float(t) / self.schedule_timesteps, 1.0)
        return self.initial_p + fraction * (self.final_p - self.initial_p)

def value(self, t):
    fraction = min(float(t) / self.schedule_timesteps, 1.0)
    return self.initial_p + fraction * (self.final_p - self.initial_p)

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

def forward(self, obs):
    s = obs.float() / 255
    s = self.conv(s)
    s = torch.relu(self.fc1(s))
    q = self.fc2(s)
    return q

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

def forward(self, obs):
    s = obs.float() / 255
    s = self.conv(s)
    s = torch.relu(self.fc(s))
    Adv = self.A(s)
    V = self.V(s)
    Q = V + (Adv - torch.mean(Adv, dim=-1, keepdim=True))
    return Q

class ReplayBuffer_torch:

    def __init__(self, device, max_size=int(100000.0)):
        self.device = device
        self.max_size = max_size
        self.ptr = 0
        self.size = 0
        self.state = torch.zeros((max_size, 4, 84, 84), dtype=torch.uint8)
        self.action = torch.zeros((max_size, 1), dtype=torch.int64)
        self.reward = torch.zeros((max_size, 1))
        self.next_state = torch.zeros((max_size, 4, 84, 84), dtype=torch.uint8)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool)

    def add(self, state, action, reward, next_state, dw):
        self.state[self.ptr] = state
        self.action[self.ptr] = action
        self.reward[self.ptr] = reward
        self.next_state[self.ptr] = next_state
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = np.random.randint(0, self.size - 1, batch_size)
        return (self.state[ind].to(self.device), self.action[ind].to(self.device), self.reward[ind].to(self.device), self.next_state[ind].to(self.device), self.dw[ind].to(self.device))

def add(self, state, action, reward, next_state, dw):
    self.state[self.ptr] = state
    self.action[self.ptr] = action
    self.reward[self.ptr] = reward
    self.next_state[self.ptr] = next_state
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

class ReplayBuffer(object):

    def __init__(self, state_dim, dvc, max_size=int(1000000.0)):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, 1), dtype=torch.long, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = a
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = a
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

class ReplayBuffer:

    def __init__(self, state_dim, action_dim, max_size, dvc):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, action_dim), dtype=torch.float, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = torch.from_numpy(a).to(self.dvc)
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = torch.from_numpy(a).to(self.dvc)
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

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

def forward(self, s):
    s = self.hidden(s)
    Adv = self.A(s)
    V = self.V(s)
    Q = V + (Adv - torch.mean(Adv, dim=-1, keepdim=True))
    return Q

class ReplayBuffer(object):

    def __init__(self, state_dim, dvc, max_size=int(1000000.0)):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, 1), dtype=torch.long, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = a
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = a
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

class Actor:

    def __init__(self, opt, shared_data):
        self.shared_data = shared_data
        self.device = torch.device(opt.A_dvc)
        self.max_train_steps = opt.max_train_steps
        self.train_envs = opt.train_envs
        self.action_dim = opt.action_dim
        self.explore_steps = opt.explore_steps
        self.time_feedback = opt.time_feedback
        self.explore_frac_scheduler = LinearSchedule(opt.decay_step, opt.init_explore_frac, opt.end_explore_frac)
        self.p = torch.zeros(opt.train_envs)
        self.min_eps = opt.min_eps
        self.envs = envpool.make_gym(opt.ExpEnvName, num_envs=opt.train_envs, seed=opt.seed, max_episode_steps=int(50000.0 / 4), episodic_life=True, reward_clip=True)
        self.actor_net = Q_Net(opt.action_dim, opt.fc_width).to(self.device)
        self.step_counter = 0

    def run(self):
        ct = np.ones(self.train_envs, dtype=np.bool_)
        s, info = self.envs.reset()
        mean_t, c = (0, 0)
        while True:
            if self.step_counter > self.max_train_steps:
                break
            random_phase = self.step_counter < self.explore_steps
            if random_phase:
                a = np.random.randint(0, self.action_dim, self.train_envs)
            else:
                t0 = time.time()
                a = self.select_action(s)
            s_next, r, dw, tr, info = self.envs.step(a)
            self.shared_data.add(s, a, r, dw, ct)
            ct = ~(dw + tr)
            s = s_next
            self.step_counter += self.train_envs
            self.shared_data.set_total_steps(self.step_counter)
            if not random_phase:
                if self.step_counter % (5 * self.train_envs) == 0:
                    if self.shared_data.get_should_download():
                        self.shared_data.set_should_download(False)
                        self.download_model()
                if self.step_counter % (10 * self.train_envs) == 0:
                    self.fresh_explore_prob(self.step_counter - self.explore_steps)
                if self.step_counter % (100 * self.train_envs) == 0:
                    print('(Actor) Tstep: {}k'.format(int(self.step_counter / 1000.0)))
                if self.time_feedback:
                    c += 1
                    current_t = time.time() - t0
                    mean_t = mean_t + (current_t - mean_t) / c
                    self.shared_data.set_t(mean_t, 0)
                    t = self.shared_data.get_t()
                    if t[0] < t[1]:
                        hold_time = t[1] - t[0]
                        if hold_time > 1:
                            hold_time = 1
                        time.sleep(hold_time)

    def fresh_explore_prob(self, steps):
        explore_frac = self.explore_frac_scheduler.value(steps)
        i = int(explore_frac * self.train_envs)
        explore = torch.arange(i) / (1.25 * i)
        self.p *= 0
        self.p[self.train_envs - i:] = explore
        self.p += self.min_eps

    def select_action(self, s):
        """For envpool, the input is [n,4,84,84], npdarray"""
        with torch.no_grad():
            s = torch.from_numpy(s).to(self.device)
            a = self.actor_net(s).argmax(dim=-1).cpu()
            replace = torch.rand(self.train_envs) < self.p
            rd_a = torch.randint(0, self.action_dim, (self.train_envs,))
            a[replace] = rd_a[replace]
            return a.numpy()

    def download_model(self):
        self.actor_net.load_state_dict(self.shared_data.get_net_param())
        for actor_param in self.actor_net.parameters():
            actor_param.requires_grad = False

def select_action(self, s):
    """For envpool, the input is [n,4,84,84], npdarray"""
    with torch.no_grad():
        s = torch.from_numpy(s).to(self.device)
        a = self.actor_net(s).argmax(dim=-1).cpu()
        replace = torch.rand(self.train_envs) < self.p
        rd_a = torch.randint(0, self.action_dim, (self.train_envs,))
        a[replace] = rd_a[replace]
        return a.numpy()

class LinearSchedule(object):

    def __init__(self, schedule_timesteps, initial_p, final_p):
        """Linear interpolation between initial_p and final_p over
		schedule_timesteps. After this many timesteps pass final_p is
		returned.
		Parameters
		----------
		schedule_timesteps: int
			Number of timesteps for which to linearly anneal initial_p
			to final_p
		initial_p: float
			initial output value
		final_p: float
			final output value
		"""
        self.schedule_timesteps = schedule_timesteps
        self.initial_p = initial_p
        self.final_p = final_p

    def value(self, t):
        fraction = min(float(t) / self.schedule_timesteps, 1.0)
        return self.initial_p + fraction * (self.final_p - self.initial_p)

def value(self, t):
    fraction = min(float(t) / self.schedule_timesteps, 1.0)
    return self.initial_p + fraction * (self.final_p - self.initial_p)

class shared_data_cpu:
    """Using RAM to store expriences"""

    def __init__(self, opt):
        self.B_dvc = torch.device(opt.B_dvc)
        self.L_dvc = torch.device(opt.L_dvc)
        self.max_size = int(opt.buffersize / opt.train_envs)
        self.train_envs = opt.train_envs
        self.ptr = 0
        self.size = 0
        self.full = False
        self.batch_size = opt.batch_size
        self.t = [0, 0]
        self.net_param = None
        self.total_steps = 0
        self.eval_deque = deque()
        self.train_curve = []
        self.should_download = False
        self.s = torch.zeros((self.max_size, opt.train_envs, 4, 84, 84), dtype=torch.uint8, device=self.B_dvc)
        self.a = torch.zeros((self.max_size, opt.train_envs, 1), dtype=torch.int64, device=self.B_dvc)
        self.r = torch.zeros((self.max_size, opt.train_envs, 1), device=self.B_dvc)
        self.dw = torch.zeros((self.max_size, opt.train_envs, 1), dtype=torch.bool, device=self.B_dvc)
        self.ct = torch.zeros((self.max_size, opt.train_envs, 1), dtype=torch.bool, device=self.B_dvc)
        self.get_lock_time = 0.0002
        self.set_lock_time = 0.0001
        self.busy = [False, False, False]

    def add(self, s, a, r, dw, ct):
        """add transitions to buffer,with thread lock"""
        self.set_lock(self.add_core, 1, (s, a, r, dw, ct))

    def add_core(self, trans):
        """add transitions to buffer,without thread lock"""
        s, a, r, dw, ct = trans
        self.s[self.ptr] = torch.from_numpy(s)
        self.a[self.ptr] = torch.from_numpy(a).unsqueeze(-1)
        self.r[self.ptr] = torch.from_numpy(r).unsqueeze(-1)
        self.dw[self.ptr] = torch.from_numpy(dw).unsqueeze(-1)
        self.ct[self.ptr] = torch.from_numpy(ct).unsqueeze(-1)
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)
        if self.size == self.max_size:
            self.full = True

    def sample(self):
        """sample batch transitions, with threading lock"""
        return self.get_lock(self.sample_core, 1)

    def sample_core(self):
        """sample batch transitions, without thread lock"""
        if not self.full:
            ind = torch.randint(low=0, high=self.ptr - 1, size=(self.batch_size,))
        else:
            ind = torch.randint(low=0, high=self.size - 1, size=(self.batch_size,))
            if self.ptr - 1 in ind:
                ind = ind[ind != self.ptr - 1]
        env_ind = torch.randint(low=0, high=self.train_envs, size=(len(ind),))
        return (self.s[ind, env_ind, :].to(self.L_dvc), self.a[ind, env_ind, :].to(self.L_dvc), self.r[ind, env_ind, :].to(self.L_dvc), self.s[ind + 1, env_ind, :].to(self.L_dvc), self.dw[ind, env_ind, :].to(self.L_dvc), self.ct[ind, env_ind, :].to(self.L_dvc))

    def get_net_param(self):
        return self.get_lock(self.get_net_param_core, 0)

    def get_net_param_core(self):
        return self.net_param

    def set_net_param(self, net_param):
        self.set_lock(self.set_net_param_core, 0, net_param)

    def set_net_param_core(self, net_param):
        self.net_param = net_param

    def add_curvepoint(self, curvepoint):
        self.set_lock(self.add_curvepoint_core, 2, curvepoint)

    def add_curvepoint_core(self, curvepoint):
        self.train_curve.append(curvepoint)

    def get_curve(self):
        return self.get_lock(self.get_curve_core, 2)

    def get_curve_core(self):
        curve = copy.deepcopy(self.train_curve)
        self.train_curve = []
        return curve

    def add_eval_model(self, params, global_steps, walltime):
        self.eval_deque.append({'model': params, 'steps': global_steps, 'time': walltime})

    def get_eval_model(self):
        if self.eval_deque:
            return self.eval_deque.popleft()
        else:
            return None

    def get_t(self):
        return self.t

    def set_t(self, time, idx):
        self.t[idx] = time

    def get_total_steps(self):
        return self.total_steps

    def set_total_steps(self, total_steps):
        self.total_steps = total_steps

    def get_should_download(self):
        return self.should_download

    def set_should_download(self, bol):
        self.should_download = bol

    def get_lock(self, get_func, idx):
        """ get_func is the function to be lock, idx is the index of self.busy """
        while True:
            if self.busy[idx]:
                time.sleep(self.get_lock_time)
            else:
                time.sleep(self.get_lock_time)
                if not self.busy[idx]:
                    self.busy[idx] = True
                    data = get_func()
                    self.busy[idx] = False
                    return data

    def set_lock(self, set_func, idx, data):
        """ set_func is the function to be lock, idx is the index of self.busy, data is the data to be set """
        while True:
            if self.busy[idx]:
                time.sleep(self.set_lock_time)
            else:
                time.sleep(self.set_lock_time)
                if not self.busy[idx]:
                    self.busy[idx] = True
                    set_func(data)
                    self.busy[idx] = False
                    break

def add_core(self, trans):
    """add transitions to buffer,without thread lock"""
    s, a, r, dw, ct = trans
    self.s[self.ptr] = torch.from_numpy(s)
    self.a[self.ptr] = torch.from_numpy(a).unsqueeze(-1)
    self.r[self.ptr] = torch.from_numpy(r).unsqueeze(-1)
    self.dw[self.ptr] = torch.from_numpy(dw).unsqueeze(-1)
    self.ct[self.ptr] = torch.from_numpy(ct).unsqueeze(-1)
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)
    if self.size == self.max_size:
        self.full = True

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

class Evaluator:

    def __init__(self, eid, opt, shared_data):
        self.eid = eid
        self.shared_data = shared_data
        self.device = torch.device(opt.E_dvc)
        self.envname = opt.ExpEnvName
        self.eval_envs = opt.eval_envs
        self.max_train_steps = opt.max_train_steps
        self.eval_net = Q_Net(opt.action_dim, opt.fc_width).to(self.device)
        self.envs = envpool.make_gym(self.envname, num_envs=opt.eval_envs, seed=opt.seed + 1, max_episode_steps=int(108000.0 / 4), episodic_life=False, reward_clip=False)

    def run(self):
        while True:
            data = self.shared_data.get_eval_model()
            global_steps = self.shared_data.get_total_steps()
            if global_steps > self.max_train_steps and data is None:
                break
            if data is None:
                time.sleep(5)
            else:
                self.eval_net.load_state_dict(data['model'])
                for eval_param in self.eval_net.parameters():
                    eval_param.requires_grad = False
                score = self.evaluate()
                self.shared_data.add_curvepoint([score, data['steps'], data['time']])
                print('(Evaluator {}) '.format(self.eid), self.envname, '  Tstep:{}k'.format(round(data['steps'] / 1000, 2)), '  score:', score)

    def evaluate(self):
        s, info = self.envs.reset()
        dones, total_r = (np.zeros(self.eval_envs, dtype=np.bool_), 0)
        while not dones.all():
            a = self.select_action(s)
            s, r, dw, tr, info = self.envs.step(a)
            total_r += (~dones * r).sum()
            dones += dw + tr
        return round(total_r / self.eval_envs, 1)

    def select_action(self, s):
        """for envpool"""
        with torch.no_grad():
            s = torch.from_numpy(s).to(self.device)
            return self.eval_net(s).argmax(dim=-1).cpu().numpy()

def select_action(self, s):
    """for envpool"""
    with torch.no_grad():
        s = torch.from_numpy(s).to(self.device)
        return self.eval_net(s).argmax(dim=-1).cpu().numpy()

class ReplayBuffer(object):

    def __init__(self, state_dim, dvc, max_size=int(1000000.0)):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, 1), dtype=torch.long, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = a
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = a
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

class ReplayBuffer(object):

    def __init__(self, state_dim, dvc, max_size=int(1000000.0)):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, 1), dtype=torch.long, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = a
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = a
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

class ReplayBuffer:

    def __init__(self, state_dim, action_dim, max_size, dvc):
        self.max_size = max_size
        self.dvc = dvc
        self.ptr = 0
        self.size = 0
        self.s = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.a = torch.zeros((max_size, action_dim), dtype=torch.float, device=self.dvc)
        self.r = torch.zeros((max_size, 1), dtype=torch.float, device=self.dvc)
        self.s_next = torch.zeros((max_size, state_dim), dtype=torch.float, device=self.dvc)
        self.dw = torch.zeros((max_size, 1), dtype=torch.bool, device=self.dvc)

    def add(self, s, a, r, s_next, dw):
        self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
        self.a[self.ptr] = torch.from_numpy(a).to(self.dvc)
        self.r[self.ptr] = r
        self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
        self.dw[self.ptr] = dw
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
        return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

def add(self, s, a, r, s_next, dw):
    self.s[self.ptr] = torch.from_numpy(s).to(self.dvc)
    self.a[self.ptr] = torch.from_numpy(a).to(self.dvc)
    self.r[self.ptr] = r
    self.s_next[self.ptr] = torch.from_numpy(s_next).to(self.dvc)
    self.dw[self.ptr] = dw
    self.ptr = (self.ptr + 1) % self.max_size
    self.size = min(self.size + 1, self.max_size)

