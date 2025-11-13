# Cluster 10

class SimpleReplayBuffer(ReplayBuffer):
    buffer_type = 'markov'

    def __init__(self, max_replay_buffer_size, observation_dim, action_dim, max_trajectory_len: int, add_timeout: bool=False, **kwargs):
        """
        :param max_replay_buffer_size:
        :param observation_dim:
        :param action_dim:
        :param trajectory_len:
        :param kwargs: reward_types list [goal_reward, contact_reward, ...]

        NOTE: difference from terminal and timeout:
        - for model-based methods (e.g. varibad): add_timeout = False, we only have terminals
                - for VAE, terminal is whether time out, so we use terminal to sample episodes
                - for policy, terminal is whether reach goal, so we use terminal to bootstrap or not in sampled transitions
        - for model-free methods (e.g. RNN policy): add_timeout = True, we have both terminals and dones
                - we only have policy buffer
                - terminal is whether reach goal for bootstrap
                - timeout is whether time out for sampling episodes
        """
        self._max_replay_buffer_size = max_replay_buffer_size
        self._observation_dim = observation_dim
        self._action_dim = action_dim
        self.trajectory_len = max_trajectory_len
        self._observations = np.zeros((max_replay_buffer_size, observation_dim))
        self._next_obs = np.zeros((max_replay_buffer_size, observation_dim))
        self._actions = np.zeros((max_replay_buffer_size, action_dim))
        self._rewards = np.zeros((max_replay_buffer_size, 1))
        self._terminals = np.zeros((max_replay_buffer_size, 1), dtype='uint8')
        self.add_timeout = add_timeout
        if add_timeout:
            self._timeouts = np.zeros((max_replay_buffer_size, 1), dtype='uint8')
        self.clear()

    def add_sample(self, observation, action, reward, terminal, next_observation, timeout=None, **kwargs):
        self._observations[self._top] = observation
        self._actions[self._top] = action
        self._rewards[self._top] = reward
        self._terminals[self._top] = terminal
        self._next_obs[self._top] = next_observation
        if self.add_timeout:
            self._timeouts[self._top] = timeout
        self._advance()
        if self.add_timeout and timeout or (not self.add_timeout and terminal):
            self.terminate_episode()

    def terminate_episode(self):
        self._episode_starts.append(self._curr_episode_start)
        if len(self._episode_starts) > int(self._max_replay_buffer_size / self.trajectory_len):
            del self._episode_starts[0]
        self._curr_episode_start = self._top

    def size(self):
        return self._size

    def clear(self):
        self._top = 0
        self._size = 0
        self._episode_starts = []
        self._curr_episode_start = 0

    def _advance(self, step=1):
        self._top = (self._top + step) % self._max_replay_buffer_size
        self._size = min(self._size + step, self._max_replay_buffer_size)

    def sample_data(self, indices):
        return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._next_obs[indices])

    def random_batch(self, batch_size):
        """batch of unordered transitions"""
        indices = np.random.randint(0, self._size, batch_size)
        return self.sample_data(indices)

    def can_sample_batch(self, batch_size):
        return self._size >= batch_size

    def random_episodes(self, num_episodes, sub_traj_len=-1, replace=False):
        """NOTE: return each item has 3D shape (sub_traj_len, num_episodes, dim)"""
        episode_indices = np.random.choice(range(self.num_complete_episodes()), num_episodes, replace=replace)
        assert sub_traj_len <= self.trajectory_len
        if sub_traj_len == -1:
            sub_traj_len = self.trajectory_len
        assert sub_traj_len >= 1
        sub_traj_starts = np.random.randint(0, self.trajectory_len - sub_traj_len + 1, num_episodes)
        indices = []
        for idx, sub_traj_start in zip(episode_indices, sub_traj_starts):
            start = self._episode_starts[idx] + sub_traj_start
            end = start + sub_traj_len
            indices += list(np.arange(start, end) % self._max_replay_buffer_size)
        raw_batch = self.sample_data(indices)
        batch = dict()
        for k in raw_batch.keys():
            batch[k] = raw_batch[k].reshape(num_episodes, sub_traj_len, -1).transpose(1, 0, 2)
        return batch

    def can_sample_episodes(self, num_episodes=None):
        if num_episodes is None:
            num_episodes = 1
        return self.num_complete_episodes() >= num_episodes

    def num_steps_can_sample(self):
        return self._size

    def num_complete_episodes(self):
        return len(self._episode_starts)

def _advance(self, step=1):
    self._top = (self._top + step) % self._max_replay_buffer_size
    self._size = min(self._size + step, self._max_replay_buffer_size)

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

@staticmethod
def forward_actor(actor, observ):
    new_actions = actor(observ)
    return (new_actions, None)

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

