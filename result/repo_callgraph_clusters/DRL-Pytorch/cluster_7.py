# Cluster 7

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

class SumTree(object):
    """
    Story data with its priority in the tree.
    Tree structure and array storage:

    Tree index:
         0         -> storing priority sum
        /       1     2
     / \\   /     3   4 5   6    -> storing priority for transitions

    Array type for storing:
    [0,1,2,3,4,5,6]
    """

    def __init__(self, buffer_capacity):
        self.buffer_capacity = buffer_capacity
        self.tree_capacity = 2 * buffer_capacity - 1
        self.tree = np.zeros(self.tree_capacity)

    def update_priority(self, data_index, priority):
        """ Update the priority for one transition according to its index in buffer """
        tree_index = data_index + self.buffer_capacity - 1
        change = priority - self.tree[tree_index]
        self.tree[tree_index] = priority
        while tree_index != 0:
            tree_index = (tree_index - 1) // 2
            self.tree[tree_index] += change

    def prioritized_sample(self, N, batch_size, beta):
        """ sample a batch of index and normlized IS weight according to priorites """
        batch_index = np.zeros(batch_size, dtype=np.uint32)
        IS_weight = torch.zeros(batch_size, dtype=torch.float32)
        segment = self.priority_sum / batch_size
        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            v = np.random.uniform(a, b)
            buffer_index, priority = self._get_index(v)
            batch_index[i] = buffer_index
            prob = priority / self.priority_sum
            IS_weight[i] = (N * prob) ** (-beta)
        Normed_IS_weight = IS_weight / IS_weight.max()
        return (batch_index, Normed_IS_weight)

    def _get_index(self, v):
        """ sample a index """
        parent_idx = 0
        while True:
            child_left_idx = 2 * parent_idx + 1
            child_right_idx = child_left_idx + 1
            if child_left_idx >= self.tree_capacity:
                tree_index = parent_idx
                break
            elif v <= self.tree[child_left_idx]:
                parent_idx = child_left_idx
            else:
                v -= self.tree[child_left_idx]
                parent_idx = child_right_idx
        data_index = tree_index - self.buffer_capacity + 1
        return (data_index, self.tree[tree_index])

    @property
    def priority_sum(self):
        return self.tree[0]

    @property
    def priority_max(self):
        return self.tree[self.buffer_capacity - 1:].max()

def __init__(self, buffer_capacity):
    self.buffer_capacity = buffer_capacity
    self.tree_capacity = 2 * buffer_capacity - 1
    self.tree = np.zeros(self.tree_capacity)

def prioritized_sample(self, N, batch_size, beta):
    """ sample a batch of index and normlized IS weight according to priorites """
    batch_index = np.zeros(batch_size, dtype=np.uint32)
    IS_weight = torch.zeros(batch_size, dtype=torch.float32)
    segment = self.priority_sum / batch_size
    for i in range(batch_size):
        a = segment * i
        b = segment * (i + 1)
        v = np.random.uniform(a, b)
        buffer_index, priority = self._get_index(v)
        batch_index[i] = buffer_index
        prob = priority / self.priority_sum
        IS_weight[i] = (N * prob) ** (-beta)
    Normed_IS_weight = IS_weight / IS_weight.max()
    return (batch_index, Normed_IS_weight)

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

class SumTree(object):
    """
    Story data with its priority in the tree.
    Tree structure and array storage:

    Tree index:
         0         -> storing priority sum
        /       1     2
     / \\   /     3   4 5   6    -> storing priority for transitions

    Array type for storing:
    [0,1,2,3,4,5,6]
    """

    def __init__(self, buffer_capacity):
        self.buffer_capacity = buffer_capacity
        self.tree_capacity = 2 * buffer_capacity - 1
        self.tree = np.zeros(self.tree_capacity)

    def update_priority(self, data_index, priority):
        """ Update the priority for one transition according to its index in buffer """
        tree_index = data_index + self.buffer_capacity - 1
        change = priority - self.tree[tree_index]
        self.tree[tree_index] = priority
        while tree_index != 0:
            tree_index = (tree_index - 1) // 2
            self.tree[tree_index] += change

    def prioritized_sample(self, N, batch_size, beta):
        """ sample a batch of index and normlized IS weight according to priorites """
        batch_index = np.zeros(batch_size, dtype=np.uint32)
        IS_weight = torch.zeros(batch_size, dtype=torch.float32)
        segment = self.priority_sum / batch_size
        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            v = np.random.uniform(a, b)
            buffer_index, priority = self._get_index(v)
            batch_index[i] = buffer_index
            prob = priority / self.priority_sum
            IS_weight[i] = (N * prob) ** (-beta)
        Normed_IS_weight = IS_weight / IS_weight.max()
        return (batch_index, Normed_IS_weight)

    def _get_index(self, v):
        """ sample a index """
        parent_idx = 0
        while True:
            child_left_idx = 2 * parent_idx + 1
            child_right_idx = child_left_idx + 1
            if child_left_idx >= self.tree_capacity:
                tree_index = parent_idx
                break
            elif v <= self.tree[child_left_idx]:
                parent_idx = child_left_idx
            else:
                v -= self.tree[child_left_idx]
                parent_idx = child_right_idx
        data_index = tree_index - self.buffer_capacity + 1
        return (data_index, self.tree[tree_index])

    @property
    def priority_sum(self):
        return self.tree[0]

    @property
    def priority_max(self):
        return self.tree[self.buffer_capacity - 1:].max()

def __init__(self, buffer_capacity):
    self.buffer_capacity = buffer_capacity
    self.tree_capacity = 2 * buffer_capacity - 1
    self.tree = np.zeros(self.tree_capacity)

def prioritized_sample(self, N, batch_size, beta):
    """ sample a batch of index and normlized IS weight according to priorites """
    batch_index = np.zeros(batch_size, dtype=np.uint32)
    IS_weight = torch.zeros(batch_size, dtype=torch.float32)
    segment = self.priority_sum / batch_size
    for i in range(batch_size):
        a = segment * i
        b = segment * (i + 1)
        v = np.random.uniform(a, b)
        buffer_index, priority = self._get_index(v)
        batch_index[i] = buffer_index
        prob = priority / self.priority_sum
        IS_weight[i] = (N * prob) ** (-beta)
    Normed_IS_weight = IS_weight / IS_weight.max()
    return (batch_index, Normed_IS_weight)

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

