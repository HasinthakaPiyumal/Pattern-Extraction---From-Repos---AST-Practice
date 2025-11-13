# Cluster 5

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

def add(self, s, a, r, dw, ct):
    """add transitions to buffer,with thread lock"""
    self.set_lock(self.add_core, 1, (s, a, r, dw, ct))

def set_net_param(self, net_param):
    self.set_lock(self.set_net_param_core, 0, net_param)

def add_curvepoint(self, curvepoint):
    self.set_lock(self.add_curvepoint_core, 2, curvepoint)

