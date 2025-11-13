# Cluster 9

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

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

def sample(self, batch_size):
    ind = np.random.randint(0, self.size - 1, batch_size)
    return (self.state[ind].to(self.device), self.action[ind].to(self.device), self.reward[ind].to(self.device), self.next_state[ind].to(self.device), self.dw[ind].to(self.device))

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

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

class Recorder:
    """Because the running curve written by evaluator can be unsorted,
	we use a Recorder process to sort the running curve point and record it with tensorboard"""

    def __init__(self, opt, shared_data):
        self.shared_data = shared_data
        self.writer = SummaryWriter(log_dir=opt.writepath)

    def run(self):
        while True:
            time.sleep(60)
            curve = self.shared_data.get_curve()
            if len(curve) == 0:
                pass
            else:
                curve = torch.tensor(curve)
                score, steps, walltime = (curve[:, 0], curve[:, 1], curve[:, 2])
                steps, sort_ind = torch.sort(steps)
                score = score[sort_ind]
                walltime = walltime[sort_ind]
                for _ in range(len(curve)):
                    self.writer.add_scalar('ep_r', score[_], steps[_], walltime[_])

def run(self):
    while True:
        time.sleep(60)
        curve = self.shared_data.get_curve()
        if len(curve) == 0:
            pass
        else:
            curve = torch.tensor(curve)
            score, steps, walltime = (curve[:, 0], curve[:, 1], curve[:, 2])
            steps, sort_ind = torch.sort(steps)
            score = score[sort_ind]
            walltime = walltime[sort_ind]
            for _ in range(len(curve)):
                self.writer.add_scalar('ep_r', score[_], steps[_], walltime[_])

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

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

def sample(self, batch_size):
    ind = torch.randint(0, self.size, device=self.dvc, size=(batch_size,))
    return (self.s[ind], self.a[ind], self.r[ind], self.s_next[ind], self.dw[ind])

