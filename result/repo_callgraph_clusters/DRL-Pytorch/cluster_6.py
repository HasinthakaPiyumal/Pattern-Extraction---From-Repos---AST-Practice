# Cluster 6

class DDPG_agent:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tau = 0.005
        self.actor = Actor(self.state_dim, self.action_dim, self.net_width, self.max_action).to(self.dvc)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.a_lr)
        self.actor_target = copy.deepcopy(self.actor)
        self.q_critic = Q_Critic(self.state_dim, self.action_dim, self.net_width).to(self.dvc)
        self.q_critic_optimizer = torch.optim.Adam(self.q_critic.parameters(), lr=self.c_lr)
        self.q_critic_target = copy.deepcopy(self.q_critic)
        self.replay_buffer = ReplayBuffer(self.state_dim, self.action_dim, max_size=int(500000.0), dvc=self.dvc)

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state[np.newaxis, :]).to(self.dvc)
            a = self.actor(state).cpu().numpy()[0]
            if deterministic:
                return a
            else:
                noise = np.random.normal(0, self.max_action * self.noise, size=self.action_dim)
                return (a + noise).clip(-self.max_action, self.max_action)

    def train(self):
        with torch.no_grad():
            s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
            target_a_next = self.actor_target(s_next)
            target_Q = self.q_critic_target(s_next, target_a_next)
            target_Q = r + ~dw * self.gamma * target_Q
        current_Q = self.q_critic(s, a)
        q_loss = F.mse_loss(current_Q, target_Q)
        self.q_critic_optimizer.zero_grad()
        q_loss.backward()
        self.q_critic_optimizer.step()
        a_loss = -self.q_critic(s, self.actor(s)).mean()
        self.actor_optimizer.zero_grad()
        a_loss.backward()
        self.actor_optimizer.step()
        with torch.no_grad():
            for param, target_param in zip(self.q_critic.parameters(), self.q_critic_target.parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            for param, target_param in zip(self.actor.parameters(), self.actor_target.parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, EnvName, timestep):
        torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
        torch.save(self.q_critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

    def load(self, EnvName, timestep):
        self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
        self.q_critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

def save(self, EnvName, timestep):
    torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
    torch.save(self.q_critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

def load(self, EnvName, timestep):
    self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
    self.q_critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

class DQN_Agent(object):

    def __init__(self, opt):
        self.q_net = Q_Net(opt.state_dim, opt.action_dim, (opt.net_width, opt.net_width)).to(device)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=opt.lr)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.gamma = opt.gamma
        self.tau = 0.005
        self.batch_size = opt.batch_size
        self.exp_noise = opt.exp_noise_init
        self.action_dim = opt.action_dim
        self.DDQN = opt.DDQN

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(device)
            if deterministic:
                a = self.q_net(state).argmax().item()
            elif np.random.rand() < self.exp_noise:
                a = np.random.randint(0, self.action_dim)
            else:
                a = self.q_net(state).argmax().item()
        return a

    def train(self, replay_buffer):
        s, a, r, s_prime, dw_mask, ind, Normed_IS_weight = replay_buffer.sample(self.batch_size)
        'Compute the target Q value'
        with torch.no_grad():
            if self.DDQN:
                argmax_a = self.q_net(s_prime).argmax(dim=1).unsqueeze(-1)
                max_q_prime = self.q_target(s_prime).gather(1, argmax_a)
            else:
                max_q_prime = self.q_target(s_prime).max(1)[0].unsqueeze(1)
            'Avoid impacts caused by reaching max episode steps'
            target_Q = r + (1 - dw_mask) * self.gamma * max_q_prime
        current_q_a = self.q_net(s).gather(1, a)
        td_errors = (current_q_a - target_Q).squeeze(-1)
        loss = (Normed_IS_weight * td_errors ** 2).mean()
        replay_buffer.update_batch_priorities(ind, td_errors.detach().cpu().numpy())
        self.q_net_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.q_net_optimizer.step()
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, algo, EnvName, steps):
        torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

    def load(self, algo, EnvName, steps):
        self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))
        self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))

def save(self, algo, EnvName, steps):
    torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

def load(self, algo, EnvName, steps):
    self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))
    self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))

class DQN_Agent(object):

    def __init__(self, opt):
        self.q_net = Q_Net(opt.state_dim, opt.action_dim, (opt.net_width, opt.net_width)).to(device)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=opt.lr_init)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.env_with_dw = opt.env_with_dw
        self.gamma = opt.gamma
        self.tau = 0.005
        self.batch_size = opt.batch_size
        self.exp_noise = opt.exp_noise_init
        self.action_dim = opt.action_dim
        self.DDQN = opt.DDQN

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(device)
            if deterministic:
                a = self.q_net(state).argmax().item()
                return a
            else:
                Q = self.q_net(state)
                if np.random.rand() < self.exp_noise:
                    a = np.random.randint(0, self.action_dim)
                    q_a = Q[0, a]
                else:
                    a = Q.argmax().item()
                    q_a = Q[0, a]
                return (a, q_a)

    def train(self, replay_buffer):
        s, a, r, s_next, dw, tr, ind, Normed_IS_weight = replay_buffer.sample(self.batch_size)
        'Compute the target Q value'
        with torch.no_grad():
            if self.DDQN:
                argmax_a = self.q_net(s_next).argmax(dim=1).unsqueeze(-1)
                max_q_prime = self.q_target(s_next).gather(1, argmax_a)
            else:
                max_q_prime = self.q_target(s_next).max(1)[0].unsqueeze(1)
            'Avoid impacts caused by reaching max episode steps'
            Q_target = r + ~dw * self.gamma * max_q_prime
        current_Q = self.q_net(s).gather(1, a)
        q_loss = torch.square(~tr * Normed_IS_weight * (Q_target - current_Q)).mean()
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.q_net_optimizer.step()
        with torch.no_grad():
            batch_priorities = ((torch.abs(Q_target - current_Q) + 0.01) ** replay_buffer.alpha).squeeze(-1)
            replay_buffer.priorities[ind] = batch_priorities
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, algo, EnvName, steps):
        torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

    def load(self, algo, EnvName, steps):
        self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))
        self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))

def save(self, algo, EnvName, steps):
    torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

def load(self, algo, EnvName, steps):
    self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))
    self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))

class DQN_Agent(object):

    def __init__(self, opt):
        self.q_net = Q_Net(opt.state_dim, opt.action_dim, (opt.net_width, opt.net_width)).to(device)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=opt.lr)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.gamma = opt.gamma
        self.tau = 0.005
        self.batch_size = opt.batch_size
        self.exp_noise = opt.exp_noise_init
        self.action_dim = opt.action_dim
        self.DDQN = opt.DDQN

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(device)
            if deterministic:
                a = self.q_net(state).argmax().item()
            elif np.random.rand() < self.exp_noise:
                a = np.random.randint(0, self.action_dim)
            else:
                a = self.q_net(state).argmax().item()
        return a

    def train(self, replay_buffer):
        s, a, r, s_prime, dw_mask, ind, Normed_IS_weight = replay_buffer.sample(self.batch_size)
        'Compute the target Q value'
        with torch.no_grad():
            if self.DDQN:
                argmax_a = self.q_net(s_prime).argmax(dim=1).unsqueeze(-1)
                max_q_prime = self.q_target(s_prime).gather(1, argmax_a)
            else:
                max_q_prime = self.q_target(s_prime).max(1)[0].unsqueeze(1)
            'Avoid impacts caused by reaching max episode steps'
            target_Q = r + (1 - dw_mask) * self.gamma * max_q_prime
        current_q_a = self.q_net(s).gather(1, a)
        td_errors = (current_q_a - target_Q).squeeze(-1)
        loss = (Normed_IS_weight * td_errors ** 2).mean()
        replay_buffer.update_batch_priorities(ind, td_errors.detach().cpu().numpy())
        self.q_net_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.q_net_optimizer.step()
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, algo, EnvName, steps):
        torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

    def load(self, algo, EnvName, steps):
        self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))
        self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))

def save(self, algo, EnvName, steps):
    torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

def load(self, algo, EnvName, steps):
    self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))
    self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=device))

class DeepQ_Agent(object):

    def __init__(self, opt):
        self.dvc = opt.dvc
        self.action_dim = opt.action_dim
        self.batch_size = opt.batch_size
        self.gamma = opt.gamma
        self.train_counter = 0
        self.huber_loss = opt.huber_loss
        self.Double = opt.Double
        self.Duel = opt.Duel
        self.Noisy = opt.Noisy
        if self.Duel:
            self.q_net = Duel_Q_Net(opt).to(self.dvc)
        else:
            self.q_net = Q_Net(opt).to(self.dvc)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=opt.lr)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.target_freq = opt.target_freq

    def select_action(self, state, evaluate):
        with torch.no_grad():
            state = state.unsqueeze(0).to(self.dvc)
            if self.Noisy:
                return self.q_net(state).argmax().item()
            else:
                p = 0.01 if evaluate else self.exp_noise
                if np.random.rand() < p:
                    return np.random.randint(0, self.action_dim)
                else:
                    return self.q_net(state).argmax().item()

    def train(self, replay_buffer):
        self.train_counter += 1
        s, a, r, s_next, dw = replay_buffer.sample(self.batch_size)
        'Compute the target Q value'
        with torch.no_grad():
            if self.Double:
                argmax_a = self.q_net(s_next).argmax(dim=1).unsqueeze(-1)
                max_q_prime = self.q_target(s_next).gather(1, argmax_a)
            else:
                max_q_prime = self.q_target(s_next).max(1)[0].unsqueeze(1)
            'Avoid impacts caused by reaching max episode steps'
            target_Q = r + ~dw * self.gamma * max_q_prime
        current_q = self.q_net(s)
        current_q_a = current_q.gather(1, a)
        if self.huber_loss:
            q_loss = F.huber_loss(current_q_a, target_Q)
        else:
            q_loss = F.mse_loss(current_q_a, target_Q)
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 20)
        self.q_net_optimizer.step()
        if self.train_counter % self.target_freq == 0:
            for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
                target_param.data.copy_(param.data)
        for p in self.q_target.parameters():
            p.requires_grad = False

    def save(self, ExperimentName, index):
        torch.save(self.q_net.state_dict(), f'./model/{ExperimentName}_{index}k.pth')

    def load(self, ExperimentName, index):
        self.q_net.load_state_dict(torch.load(f'./model/{ExperimentName}_{index}k.pth', map_location=self.dvc))
        self.q_target.load_state_dict(torch.load(f'./model/{ExperimentName}_{index}k.pth', map_location=self.dvc))

def save(self, ExperimentName, index):
    torch.save(self.q_net.state_dict(), f'./model/{ExperimentName}_{index}k.pth')

def load(self, ExperimentName, index):
    self.q_net.load_state_dict(torch.load(f'./model/{ExperimentName}_{index}k.pth', map_location=self.dvc))
    self.q_target.load_state_dict(torch.load(f'./model/{ExperimentName}_{index}k.pth', map_location=self.dvc))

class SACD_agent:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tau = 0.005
        self.H_mean = 0
        self.replay_buffer = ReplayBuffer(self.state_dim, self.dvc, max_size=int(1000000.0))
        self.actor = Policy_Net(self.state_dim, self.action_dim, self.hid_shape).to(self.dvc)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.lr)
        self.q_critic = Double_Q_Net(self.state_dim, self.action_dim, self.hid_shape).to(self.dvc)
        self.q_critic_optimizer = torch.optim.Adam(self.q_critic.parameters(), lr=self.lr)
        self.q_critic_target = copy.deepcopy(self.q_critic)
        for p in self.q_critic_target.parameters():
            p.requires_grad = False
        if self.adaptive_alpha:
            self.target_entropy = 0.6 * -np.log(1 / self.action_dim)
            self.log_alpha = torch.tensor(np.log(self.alpha), dtype=float, requires_grad=True, device=self.dvc)
            self.alpha_optim = torch.optim.Adam([self.log_alpha], lr=self.lr)

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state[np.newaxis, :]).to(self.dvc)
            probs = self.actor(state)
            if deterministic:
                a = probs.argmax(-1).item()
            else:
                a = Categorical(probs).sample().item()
            return a

    def train(self):
        s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
        'Compute the target soft Q value'
        with torch.no_grad():
            next_probs = self.actor(s_next)
            next_log_probs = torch.log(next_probs + 1e-08)
            next_q1_all, next_q2_all = self.q_critic_target(s_next)
            min_next_q_all = torch.min(next_q1_all, next_q2_all)
            v_next = torch.sum(next_probs * (min_next_q_all - self.alpha * next_log_probs), dim=1, keepdim=True)
            target_Q = r + ~dw * self.gamma * v_next
        'Update soft Q net'
        q1_all, q2_all = self.q_critic(s)
        q1, q2 = (q1_all.gather(1, a), q2_all.gather(1, a))
        q_loss = F.mse_loss(q1, target_Q) + F.mse_loss(q2, target_Q)
        self.q_critic_optimizer.zero_grad()
        q_loss.backward()
        self.q_critic_optimizer.step()
        probs = self.actor(s)
        log_probs = torch.log(probs + 1e-08)
        with torch.no_grad():
            q1_all, q2_all = self.q_critic(s)
        min_q_all = torch.min(q1_all, q2_all)
        a_loss = torch.sum(probs * (self.alpha * log_probs - min_q_all), dim=1, keepdim=False)
        self.actor_optimizer.zero_grad()
        a_loss.mean().backward()
        self.actor_optimizer.step()
        if self.adaptive_alpha:
            with torch.no_grad():
                self.H_mean = -torch.sum(probs * log_probs, dim=1).mean()
            alpha_loss = self.log_alpha * (self.H_mean - self.target_entropy)
            self.alpha_optim.zero_grad()
            alpha_loss.backward()
            self.alpha_optim.step()
            self.alpha = self.log_alpha.exp().item()
        for param, target_param in zip(self.q_critic.parameters(), self.q_critic_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, timestep, EnvName):
        torch.save(self.actor.state_dict(), f'./model/sacd_actor_{timestep}_{EnvName}.pth')
        torch.save(self.q_critic.state_dict(), f'./model/sacd_critic_{timestep}_{EnvName}.pth')

    def load(self, timestep, EnvName):
        self.actor.load_state_dict(torch.load(f'./model/sacd_actor_{timestep}_{EnvName}.pth', map_location=self.dvc))
        self.q_critic.load_state_dict(torch.load(f'./model/sacd_critic_{timestep}_{EnvName}.pth', map_location=self.dvc))

def save(self, timestep, EnvName):
    torch.save(self.actor.state_dict(), f'./model/sacd_actor_{timestep}_{EnvName}.pth')
    torch.save(self.q_critic.state_dict(), f'./model/sacd_critic_{timestep}_{EnvName}.pth')

def load(self, timestep, EnvName):
    self.actor.load_state_dict(torch.load(f'./model/sacd_actor_{timestep}_{EnvName}.pth', map_location=self.dvc))
    self.q_critic.load_state_dict(torch.load(f'./model/sacd_critic_{timestep}_{EnvName}.pth', map_location=self.dvc))

class TD3_agent:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.policy_noise = 0.2 * self.max_action
        self.noise_clip = 0.5 * self.max_action
        self.tau = 0.005
        self.delay_counter = 0
        self.actor = Actor(self.state_dim, self.action_dim, self.net_width, self.max_action).to(self.dvc)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.a_lr)
        self.actor_target = copy.deepcopy(self.actor)
        self.q_critic = Double_Q_Critic(self.state_dim, self.action_dim, self.net_width).to(self.dvc)
        self.q_critic_optimizer = torch.optim.Adam(self.q_critic.parameters(), lr=self.c_lr)
        self.q_critic_target = copy.deepcopy(self.q_critic)
        self.replay_buffer = ReplayBuffer(self.state_dim, self.action_dim, max_size=int(1000000.0), dvc=self.dvc)

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state[np.newaxis, :]).to(self.dvc)
            a = self.actor(state).cpu().numpy()[0]
            if deterministic:
                return a
            else:
                noise = np.random.normal(0, self.max_action * self.explore_noise, size=self.action_dim)
                return (a + noise).clip(-self.max_action, self.max_action)

    def train(self):
        self.delay_counter += 1
        with torch.no_grad():
            s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
            target_a_noise = (torch.randn_like(a) * self.policy_noise).clamp(-self.noise_clip, self.noise_clip)
            '↓↓↓ Target Policy Smoothing Regularization ↓↓↓'
            smoothed_target_a = (self.actor_target(s_next) + target_a_noise).clamp(-self.max_action, self.max_action)
            target_Q1, target_Q2 = self.q_critic_target(s_next, smoothed_target_a)
            '↓↓↓ Clipped Double Q-learning ↓↓↓'
            target_Q = torch.min(target_Q1, target_Q2)
            target_Q = r + ~dw * self.gamma * target_Q
        current_Q1, current_Q2 = self.q_critic(s, a)
        q_loss = F.mse_loss(current_Q1, target_Q) + F.mse_loss(current_Q2, target_Q)
        self.q_critic_optimizer.zero_grad()
        q_loss.backward()
        self.q_critic_optimizer.step()
        '↓↓↓ Clipped Double Q-learning ↓↓↓'
        if self.delay_counter > self.delay_freq:
            a_loss = -self.q_critic.Q1(s, self.actor(s)).mean()
            self.actor_optimizer.zero_grad()
            a_loss.backward()
            self.actor_optimizer.step()
            with torch.no_grad():
                for param, target_param in zip(self.q_critic.parameters(), self.q_critic_target.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                for param, target_param in zip(self.actor.parameters(), self.actor_target.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            self.delay_counter = 0

    def save(self, EnvName, timestep):
        torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
        torch.save(self.q_critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

    def load(self, EnvName, timestep):
        self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
        self.q_critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

def save(self, EnvName, timestep):
    torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
    torch.save(self.q_critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

def load(self, EnvName, timestep):
    self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
    self.q_critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

class DQN_agent(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tau = 0.005
        self.replay_buffer = ReplayBuffer(self.state_dim, self.dvc, max_size=int(1000000.0))
        if self.Duel:
            self.q_net = Duel_Q_Net(self.state_dim, self.action_dim, (self.net_width, self.net_width)).to(self.dvc)
        else:
            self.q_net = Q_Net(self.state_dim, self.action_dim, (self.net_width, self.net_width)).to(self.dvc)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=self.lr)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(self.dvc)
            if deterministic:
                a = self.q_net(state).argmax().item()
            elif np.random.rand() < self.exp_noise:
                a = np.random.randint(0, self.action_dim)
            else:
                a = self.q_net(state).argmax().item()
        return a

    def train(self):
        s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
        'Compute the target Q value'
        with torch.no_grad():
            if self.Double:
                argmax_a = self.q_net(s_next).argmax(dim=1).unsqueeze(-1)
                max_q_next = self.q_target(s_next).gather(1, argmax_a)
            else:
                max_q_next = self.q_target(s_next).max(1)[0].unsqueeze(1)
            target_Q = r + ~dw * self.gamma * max_q_next
        current_q = self.q_net(s)
        current_q_a = current_q.gather(1, a)
        q_loss = F.mse_loss(current_q_a, target_Q)
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        self.q_net_optimizer.step()
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, algo, EnvName, steps):
        torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

    def load(self, algo, EnvName, steps):
        self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=self.dvc))
        self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=self.dvc))

def save(self, algo, EnvName, steps):
    torch.save(self.q_net.state_dict(), './model/{}_{}_{}.pth'.format(algo, EnvName, steps))

def load(self, algo, EnvName, steps):
    self.q_net.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=self.dvc))
    self.q_target.load_state_dict(torch.load('./model/{}_{}_{}.pth'.format(algo, EnvName, steps), map_location=self.dvc))

class QLearningAgent:

    def __init__(self, s_dim, a_dim, lr=0.01, gamma=0.9, exp_noise=0.1):
        self.a_dim = a_dim
        self.lr = lr
        self.gamma = gamma
        self.epsilon = exp_noise
        self.Q = np.zeros((s_dim, a_dim))

    def select_action(self, s, deterministic):
        if deterministic:
            'deterministic policy'
            return np.argmax(self.Q[s, :])
        else:
            'e-greedy policy'
            if np.random.uniform(0, 1) < self.epsilon:
                return np.random.choice(self.a_dim)
            else:
                return np.argmax(self.Q[s, :])

    def train(self, s, a, r, s_next, dw):
        """Update Q table"""
        Q_sa = self.Q[s, a]
        target_Q = r + (1 - dw) * self.gamma * np.max(self.Q[s_next, :])
        self.Q[s, a] += self.lr * (target_Q - Q_sa)

    def save(self):
        """save Q table"""
        npy_file = 'model/q_table.npy'
        np.save(npy_file, self.Q)
        print(npy_file + ' saved.')

    def restore(self, npy_file='model/q_table.npy'):
        """load Q table"""
        self.Q = np.load(npy_file)
        print(npy_file + ' loaded.')

def save(self):
    """save Q table"""
    npy_file = 'model/q_table.npy'
    np.save(npy_file, self.Q)
    print(npy_file + ' saved.')

def restore(self, npy_file='model/q_table.npy'):
    """load Q table"""
    self.Q = np.load(npy_file)
    print(npy_file + ' loaded.')

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

def download_model(self):
    self.actor_net.load_state_dict(self.shared_data.get_net_param())
    for actor_param in self.actor_net.parameters():
        actor_param.requires_grad = False

class Learner:

    def __init__(self, opt, shared_data):
        self.shared_data = shared_data
        self.device = torch.device(opt.L_dvc)
        self.max_train_steps = opt.max_train_steps
        self.explore_steps = opt.explore_steps
        self.lr = opt.lr
        self.gamma = opt.gamma
        self.DDQN = opt.DDQN
        self.hard_update_freq = opt.hard_update_freq
        self.upload_freq = opt.upload_freq
        self.eval_freq = opt.eval_freq
        self.train_counter = 0
        self.batch_size = opt.batch_size
        self.q_net = Q_Net(opt.action_dim, opt.fc_width).to(self.device)
        self.upload_model()
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=opt.lr, eps=0.00015)
        self.lr_scheduler = LinearSchedule(15000000.0, opt.lr, opt.lr / 3)
        self.time_feedback = opt.time_feedback
        self.rho = opt.train_envs * opt.TPS / opt.batch_size

    def run(self):
        mean_t = 0
        while True:
            global_steps = self.shared_data.get_total_steps()
            if global_steps > self.max_train_steps:
                break
            if global_steps < self.explore_steps:
                time.sleep(0.1)
            else:
                t0 = time.time()
                self.train()
                self.train_counter += 1
                if self.train_counter % self.upload_freq == 0:
                    self.upload_model()
                    self.shared_data.set_should_download(True)
                if self.train_counter % self.hard_update_freq == 0:
                    self.hard_target_update()
                    self.lr_decay(global_steps)
                    print('(Learner) Actual TPS: ', self.train_counter * self.batch_size / (global_steps - self.explore_steps))
                if self.train_counter % self.eval_freq == 0:
                    self.shared_data.add_eval_model(deepcopy(self.q_net).cpu().state_dict(), global_steps - self.explore_steps, time.time())
                if self.time_feedback:
                    current_t = time.time() - t0
                    mean_t = mean_t + (current_t - mean_t) / self.train_counter
                    scalled_learner_time = self.rho * mean_t
                    self.shared_data.set_t(scalled_learner_time, 1)
                    t = self.shared_data.get_t()
                    if t[1] < t[0]:
                        hold_time = (t[0] - t[1]) / self.rho
                        if hold_time > 1:
                            hold_time = 1
                        time.sleep(hold_time)

    def train(self):
        s, a, r, s_next, dw, ct = self.shared_data.sample()
        'Compute target Q value'
        with torch.no_grad():
            if self.DDQN:
                argmax_a = self.q_net(s_next).argmax(dim=-1).unsqueeze(-1)
                max_q_next = self.q_target(s_next).gather(1, argmax_a)
            else:
                max_q_next = self.q_target(s_next).max(1)[0].unsqueeze(1)
            target_Q = r + ~dw * self.gamma * max_q_next
        'Collect Current Q value'
        current_q = self.q_net(s)
        current_q_a = current_q.gather(1, a)
        if ct.all():
            q_loss = F.mse_loss(current_q_a, target_Q)
        else:
            q_loss = torch.square(ct * (current_q_a - target_Q)).mean()
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 40)
        self.q_net_optimizer.step()

    def upload_model(self):
        self.shared_data.set_net_param(deepcopy(self.q_net).cpu().state_dict())

    def hard_target_update(self):
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(param.data)
            target_param.requires_grad = False

    def lr_decay(self, global_step):
        for p in self.q_net_optimizer.param_groups:
            p['lr'] = self.lr_scheduler.value(global_step)

def upload_model(self):
    self.shared_data.set_net_param(deepcopy(self.q_net).cpu().state_dict())

class NoisyNetDQN_agent(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tau = 0.005
        self.replay_buffer = ReplayBuffer(self.state_dim, self.dvc, max_size=self.buffer_size)
        self.q_net = Noisy_Q_Net(self.state_dim, self.action_dim, (self.net_width, self.net_width)).to(self.dvc)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=self.lr)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False

    def select_action(self, state):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(self.dvc)
            a = self.q_net(state).argmax().item()
        return a

    def train(self):
        s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
        'Compute the target Q value'
        with torch.no_grad():
            max_q_next = self.q_target(s_next).max(1)[0].unsqueeze(1)
            target_Q = r + ~dw * self.gamma * max_q_next
        current_q = self.q_net(s)
        current_q_a = current_q.gather(1, a)
        q_loss = F.mse_loss(current_q_a, target_Q)
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        self.q_net_optimizer.step()
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, algo, EnvName, steps):
        torch.save(self.q_net.state_dict(), './model/{}_{}_{}k.pth'.format(algo, EnvName, steps))

    def load(self, algo, EnvName, steps):
        self.q_net.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))
        self.q_target.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))

def save(self, algo, EnvName, steps):
    torch.save(self.q_net.state_dict(), './model/{}_{}_{}k.pth'.format(algo, EnvName, steps))

def load(self, algo, EnvName, steps):
    self.q_net.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))
    self.q_target.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))

class PPO_agent(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        if self.Distribution == 'Beta':
            self.actor = BetaActor(self.state_dim, self.action_dim, self.net_width).to(self.dvc)
        elif self.Distribution == 'GS_ms':
            self.actor = GaussianActor_musigma(self.state_dim, self.action_dim, self.net_width).to(self.dvc)
        elif self.Distribution == 'GS_m':
            self.actor = GaussianActor_mu(self.state_dim, self.action_dim, self.net_width).to(self.dvc)
        else:
            print('Dist Error')
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.a_lr)
        self.critic = Critic(self.state_dim, self.net_width).to(self.dvc)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=self.c_lr)
        self.s_hoder = np.zeros((self.T_horizon, self.state_dim), dtype=np.float32)
        self.a_hoder = np.zeros((self.T_horizon, self.action_dim), dtype=np.float32)
        self.r_hoder = np.zeros((self.T_horizon, 1), dtype=np.float32)
        self.s_next_hoder = np.zeros((self.T_horizon, self.state_dim), dtype=np.float32)
        self.logprob_a_hoder = np.zeros((self.T_horizon, self.action_dim), dtype=np.float32)
        self.done_hoder = np.zeros((self.T_horizon, 1), dtype=np.bool_)
        self.dw_hoder = np.zeros((self.T_horizon, 1), dtype=np.bool_)

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(self.dvc)
            if deterministic:
                a = self.actor.deterministic_act(state)
                return (a.cpu().numpy()[0], None)
            else:
                dist = self.actor.get_dist(state)
                a = dist.sample()
                a = torch.clamp(a, 0, 1)
                logprob_a = dist.log_prob(a).cpu().numpy().flatten()
                return (a.cpu().numpy()[0], logprob_a)

    def train(self):
        self.entropy_coef *= self.entropy_coef_decay
        'Prepare PyTorch data from Numpy data'
        s = torch.from_numpy(self.s_hoder).to(self.dvc)
        a = torch.from_numpy(self.a_hoder).to(self.dvc)
        r = torch.from_numpy(self.r_hoder).to(self.dvc)
        s_next = torch.from_numpy(self.s_next_hoder).to(self.dvc)
        logprob_a = torch.from_numpy(self.logprob_a_hoder).to(self.dvc)
        done = torch.from_numpy(self.done_hoder).to(self.dvc)
        dw = torch.from_numpy(self.dw_hoder).to(self.dvc)
        ' Use TD+GAE+LongTrajectory to compute Advantage and TD target'
        with torch.no_grad():
            vs = self.critic(s)
            vs_ = self.critic(s_next)
            'dw for TD_target and Adv'
            deltas = r + self.gamma * vs_ * ~dw - vs
            deltas = deltas.cpu().flatten().numpy()
            adv = [0]
            'done for GAE'
            for dlt, mask in zip(deltas[::-1], done.cpu().flatten().numpy()[::-1]):
                advantage = dlt + self.gamma * self.lambd * adv[-1] * ~mask
                adv.append(advantage)
            adv.reverse()
            adv = copy.deepcopy(adv[0:-1])
            adv = torch.tensor(adv).unsqueeze(1).float().to(self.dvc)
            td_target = adv + vs
            adv = (adv - adv.mean()) / (adv.std() + 0.0001)
        'Slice long trajectopy into short trajectory and perform mini-batch PPO update'
        a_optim_iter_num = int(math.ceil(s.shape[0] / self.a_optim_batch_size))
        c_optim_iter_num = int(math.ceil(s.shape[0] / self.c_optim_batch_size))
        for i in range(self.K_epochs):
            perm = np.arange(s.shape[0])
            np.random.shuffle(perm)
            perm = torch.LongTensor(perm).to(self.dvc)
            s, a, td_target, adv, logprob_a = (s[perm].clone(), a[perm].clone(), td_target[perm].clone(), adv[perm].clone(), logprob_a[perm].clone())
            'update the actor'
            for i in range(a_optim_iter_num):
                index = slice(i * self.a_optim_batch_size, min((i + 1) * self.a_optim_batch_size, s.shape[0]))
                distribution = self.actor.get_dist(s[index])
                dist_entropy = distribution.entropy().sum(1, keepdim=True)
                logprob_a_now = distribution.log_prob(a[index])
                ratio = torch.exp(logprob_a_now.sum(1, keepdim=True) - logprob_a[index].sum(1, keepdim=True))
                surr1 = ratio * adv[index]
                surr2 = torch.clamp(ratio, 1 - self.clip_rate, 1 + self.clip_rate) * adv[index]
                a_loss = -torch.min(surr1, surr2) - self.entropy_coef * dist_entropy
                self.actor_optimizer.zero_grad()
                a_loss.mean().backward()
                torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 40)
                self.actor_optimizer.step()
            'update the critic'
            for i in range(c_optim_iter_num):
                index = slice(i * self.c_optim_batch_size, min((i + 1) * self.c_optim_batch_size, s.shape[0]))
                c_loss = (self.critic(s[index]) - td_target[index]).pow(2).mean()
                for name, param in self.critic.named_parameters():
                    if 'weight' in name:
                        c_loss += param.pow(2).sum() * self.l2_reg
                self.critic_optimizer.zero_grad()
                c_loss.backward()
                self.critic_optimizer.step()

    def put_data(self, s, a, r, s_next, logprob_a, done, dw, idx):
        self.s_hoder[idx] = s
        self.a_hoder[idx] = a
        self.r_hoder[idx] = r
        self.s_next_hoder[idx] = s_next
        self.logprob_a_hoder[idx] = logprob_a
        self.done_hoder[idx] = done
        self.dw_hoder[idx] = dw

    def save(self, EnvName, timestep):
        torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
        torch.save(self.critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

    def load(self, EnvName, timestep):
        self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
        self.critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

def save(self, EnvName, timestep):
    torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
    torch.save(self.critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

def load(self, EnvName, timestep):
    self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
    self.critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

class PPO_discrete:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        'Build Actor and Critic'
        self.actor = Actor(self.state_dim, self.action_dim, self.net_width).to(self.dvc)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.lr)
        self.critic = Critic(self.state_dim, self.net_width).to(self.dvc)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=self.lr)
        'Build Trajectory holder'
        self.s_hoder = np.zeros((self.T_horizon, self.state_dim), dtype=np.float32)
        self.a_hoder = np.zeros((self.T_horizon, 1), dtype=np.int64)
        self.r_hoder = np.zeros((self.T_horizon, 1), dtype=np.float32)
        self.s_next_hoder = np.zeros((self.T_horizon, self.state_dim), dtype=np.float32)
        self.logprob_a_hoder = np.zeros((self.T_horizon, 1), dtype=np.float32)
        self.done_hoder = np.zeros((self.T_horizon, 1), dtype=np.bool_)
        self.dw_hoder = np.zeros((self.T_horizon, 1), dtype=np.bool_)

    def select_action(self, s, deterministic):
        s = torch.from_numpy(s).float().to(self.dvc)
        with torch.no_grad():
            pi = self.actor.pi(s, softmax_dim=0)
            if deterministic:
                a = torch.argmax(pi).item()
                return (a, None)
            else:
                m = Categorical(pi)
                a = m.sample().item()
                pi_a = pi[a].item()
                return (a, pi_a)

    def train(self):
        self.entropy_coef *= self.entropy_coef_decay
        'Prepare PyTorch data from Numpy data'
        s = torch.from_numpy(self.s_hoder).to(self.dvc)
        a = torch.from_numpy(self.a_hoder).to(self.dvc)
        r = torch.from_numpy(self.r_hoder).to(self.dvc)
        s_next = torch.from_numpy(self.s_next_hoder).to(self.dvc)
        old_prob_a = torch.from_numpy(self.logprob_a_hoder).to(self.dvc)
        done = torch.from_numpy(self.done_hoder).to(self.dvc)
        dw = torch.from_numpy(self.dw_hoder).to(self.dvc)
        ' Use TD+GAE+LongTrajectory to compute Advantage and TD target'
        with torch.no_grad():
            vs = self.critic(s)
            vs_ = self.critic(s_next)
            'dw(dead and win) for TD_target and Adv'
            deltas = r + self.gamma * vs_ * ~dw - vs
            deltas = deltas.cpu().flatten().numpy()
            adv = [0]
            'done for GAE'
            for dlt, done in zip(deltas[::-1], done.cpu().flatten().numpy()[::-1]):
                advantage = dlt + self.gamma * self.lambd * adv[-1] * ~done
                adv.append(advantage)
            adv.reverse()
            adv = copy.deepcopy(adv[0:-1])
            adv = torch.tensor(adv).unsqueeze(1).float().to(self.dvc)
            td_target = adv + vs
            if self.adv_normalization:
                adv = (adv - adv.mean()) / (adv.std() + 0.0001)
        'PPO update'
        optim_iter_num = int(math.ceil(s.shape[0] / self.batch_size))
        for _ in range(self.K_epochs):
            perm = np.arange(s.shape[0])
            np.random.shuffle(perm)
            perm = torch.LongTensor(perm).to(self.dvc)
            s, a, td_target, adv, old_prob_a = (s[perm].clone(), a[perm].clone(), td_target[perm].clone(), adv[perm].clone(), old_prob_a[perm].clone())
            'mini-batch PPO update'
            for i in range(optim_iter_num):
                index = slice(i * self.batch_size, min((i + 1) * self.batch_size, s.shape[0]))
                'actor update'
                prob = self.actor.pi(s[index], softmax_dim=1)
                entropy = Categorical(prob).entropy().sum(0, keepdim=True)
                prob_a = prob.gather(1, a[index])
                ratio = torch.exp(torch.log(prob_a) - torch.log(old_prob_a[index]))
                surr1 = ratio * adv[index]
                surr2 = torch.clamp(ratio, 1 - self.clip_rate, 1 + self.clip_rate) * adv[index]
                a_loss = -torch.min(surr1, surr2) - self.entropy_coef * entropy
                self.actor_optimizer.zero_grad()
                a_loss.mean().backward()
                torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 40)
                self.actor_optimizer.step()
                'critic update'
                c_loss = (self.critic(s[index]) - td_target[index]).pow(2).mean()
                for name, param in self.critic.named_parameters():
                    if 'weight' in name:
                        c_loss += param.pow(2).sum() * self.l2_reg
                self.critic_optimizer.zero_grad()
                c_loss.backward()
                self.critic_optimizer.step()

    def put_data(self, s, a, r, s_next, logprob_a, done, dw, idx):
        self.s_hoder[idx] = s
        self.a_hoder[idx] = a
        self.r_hoder[idx] = r
        self.s_next_hoder[idx] = s_next
        self.logprob_a_hoder[idx] = logprob_a
        self.done_hoder[idx] = done
        self.dw_hoder[idx] = dw

    def save(self, episode):
        torch.save(self.critic.state_dict(), './model/ppo_critic{}.pth'.format(episode))
        torch.save(self.actor.state_dict(), './model/ppo_actor{}.pth'.format(episode))

    def load(self, episode):
        self.critic.load_state_dict(torch.load('./model/ppo_critic{}.pth'.format(episode), map_location=self.dvc))
        self.actor.load_state_dict(torch.load('./model/ppo_actor{}.pth'.format(episode), map_location=self.dvc))

def save(self, episode):
    torch.save(self.critic.state_dict(), './model/ppo_critic{}.pth'.format(episode))
    torch.save(self.actor.state_dict(), './model/ppo_actor{}.pth'.format(episode))

def load(self, episode):
    self.critic.load_state_dict(torch.load('./model/ppo_critic{}.pth'.format(episode), map_location=self.dvc))
    self.actor.load_state_dict(torch.load('./model/ppo_actor{}.pth'.format(episode), map_location=self.dvc))

class CDQN_agent(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.atoms = torch.linspace(self.v_min, self.v_max, steps=self.n_atoms, device=self.dvc)
        self.delta_z = (self.v_max - self.v_min) / (self.n_atoms - 1)
        self.m = torch.zeros((self.batch_size, self.n_atoms), device=self.dvc)
        self.q_net = Categorical_Q_Net(self.state_dim, self.action_dim, (self.net_width, self.net_width), self.atoms).to(self.dvc)
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=self.lr)
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.offset = torch.linspace(0, (self.batch_size - 1) * self.n_atoms, self.batch_size, device=self.dvc).unsqueeze(-1).long()
        self.replay_buffer = ReplayBuffer(self.state_dim, self.dvc, max_size=int(1000000.0))
        self.tau = 0.005

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state.reshape(1, -1)).to(self.dvc)
            if not deterministic and np.random.rand() < self.exp_noise:
                return np.random.randint(0, self.action_dim)
            else:
                a, _ = self.q_net(state)
                return a.cpu().item()

    def train(self):
        s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
        'Compute the target distribution:'
        with torch.no_grad():
            if self.DQL:
                argmax_a_next, _ = self.q_net(s_next)
                _, batched_next_distribution = self.q_target(s_next, argmax_a_next)
            else:
                _, batched_next_distribution = self.q_target(s_next)
            self.m *= 0
            t_z = (r + ~dw * self.gamma * self.atoms).clamp(self.v_min, self.v_max)
            b = (t_z - self.v_min) / self.delta_z
            l = b.floor().long()
            u = b.ceil().long()
            delta_m_l = (u + (l == u) - b) * batched_next_distribution
            delta_m_u = (b - l) * batched_next_distribution
            'Distribute probability with tensor operation. Much more faster than the For loop in the original paper.'
            self.m.view(-1).index_add_(0, (l + self.offset).view(-1), delta_m_l.view(-1))
            self.m.view(-1).index_add_(0, (u + self.offset).view(-1), delta_m_u.view(-1))
        _, batched_distribution = self.q_net(s, a.flatten())
        q_loss = (-(self.m * batched_distribution.clamp(min=1e-05, max=1 - 1e-05).log()).sum(-1)).mean()
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        self.q_net_optimizer.step()
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, algo, EnvName, steps):
        torch.save(self.q_net.state_dict(), './model/{}_{}_{}k.pth'.format(algo, EnvName, steps))

    def load(self, algo, EnvName, steps):
        self.q_net.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))
        self.q_target.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))

def save(self, algo, EnvName, steps):
    torch.save(self.q_net.state_dict(), './model/{}_{}_{}k.pth'.format(algo, EnvName, steps))

def load(self, algo, EnvName, steps):
    self.q_net.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))
    self.q_target.load_state_dict(torch.load('./model/{}_{}_{}k.pth'.format(algo, EnvName, steps), map_location=self.dvc))

class SAC_countinuous:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tau = 0.005
        self.actor = Actor(self.state_dim, self.action_dim, (self.net_width, self.net_width)).to(self.dvc)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.a_lr)
        self.q_critic = Double_Q_Critic(self.state_dim, self.action_dim, (self.net_width, self.net_width)).to(self.dvc)
        self.q_critic_optimizer = torch.optim.Adam(self.q_critic.parameters(), lr=self.c_lr)
        self.q_critic_target = copy.deepcopy(self.q_critic)
        for p in self.q_critic_target.parameters():
            p.requires_grad = False
        self.replay_buffer = ReplayBuffer(self.state_dim, self.action_dim, max_size=int(1000000.0), dvc=self.dvc)
        if self.adaptive_alpha:
            self.target_entropy = torch.tensor(-self.action_dim, dtype=float, requires_grad=True, device=self.dvc)
            self.log_alpha = torch.tensor(np.log(self.alpha), dtype=float, requires_grad=True, device=self.dvc)
            self.alpha_optim = torch.optim.Adam([self.log_alpha], lr=self.c_lr)

    def select_action(self, state, deterministic):
        with torch.no_grad():
            state = torch.FloatTensor(state[np.newaxis, :]).to(self.dvc)
            a, _ = self.actor(state, deterministic, with_logprob=False)
        return a.cpu().numpy()[0]

    def train(self):
        s, a, r, s_next, dw = self.replay_buffer.sample(self.batch_size)
        with torch.no_grad():
            a_next, log_pi_a_next = self.actor(s_next, deterministic=False, with_logprob=True)
            target_Q1, target_Q2 = self.q_critic_target(s_next, a_next)
            target_Q = torch.min(target_Q1, target_Q2)
            target_Q = r + ~dw * self.gamma * (target_Q - self.alpha * log_pi_a_next)
        current_Q1, current_Q2 = self.q_critic(s, a)
        q_loss = F.mse_loss(current_Q1, target_Q) + F.mse_loss(current_Q2, target_Q)
        self.q_critic_optimizer.zero_grad()
        q_loss.backward()
        self.q_critic_optimizer.step()
        for params in self.q_critic.parameters():
            params.requires_grad = False
        a, log_pi_a = self.actor(s, deterministic=False, with_logprob=True)
        current_Q1, current_Q2 = self.q_critic(s, a)
        Q = torch.min(current_Q1, current_Q2)
        a_loss = (self.alpha * log_pi_a - Q).mean()
        self.actor_optimizer.zero_grad()
        a_loss.backward()
        self.actor_optimizer.step()
        for params in self.q_critic.parameters():
            params.requires_grad = True
        if self.adaptive_alpha:
            alpha_loss = -(self.log_alpha * (log_pi_a + self.target_entropy).detach()).mean()
            self.alpha_optim.zero_grad()
            alpha_loss.backward()
            self.alpha_optim.step()
            self.alpha = self.log_alpha.exp()
        for param, target_param in zip(self.q_critic.parameters(), self.q_critic_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save(self, EnvName, timestep):
        torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
        torch.save(self.q_critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

    def load(self, EnvName, timestep):
        self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
        self.q_critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

def save(self, EnvName, timestep):
    torch.save(self.actor.state_dict(), './model/{}_actor{}.pth'.format(EnvName, timestep))
    torch.save(self.q_critic.state_dict(), './model/{}_q_critic{}.pth'.format(EnvName, timestep))

def load(self, EnvName, timestep):
    self.actor.load_state_dict(torch.load('./model/{}_actor{}.pth'.format(EnvName, timestep), map_location=self.dvc))
    self.q_critic.load_state_dict(torch.load('./model/{}_q_critic{}.pth'.format(EnvName, timestep), map_location=self.dvc))

