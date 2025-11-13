# Cluster 15

def get_grad_norm(model):
    grad_norm = []
    for p in list(filter(lambda p: p.grad is not None, model.parameters())):
        grad_norm.append(p.grad.data.norm(2).item())
    if grad_norm:
        grad_norm = np.mean(grad_norm)
    else:
        grad_norm = 0.0
    return grad_norm

class WindEnv(Env):
    """
    point robot on a 2-D plane with position control
    tasks vary in noise term in dynamics for fixed goal-reaching
     - noise is fixed for a task
     - reward is sparse
    """

    def __init__(self, max_episode_steps=75, n_tasks=1, goal_radius=0.03, **kwargs):
        self.n_tasks = n_tasks
        self._max_episode_steps = max_episode_steps
        self.step_count = 0
        np.random.seed(1337)
        self.winds = [[np.random.uniform(-0.08, 0.08), np.random.uniform(-0.08, 0.08)] for _ in range(n_tasks)]
        self._goal = np.array([0.0, 1.0])
        self.goal_radius = goal_radius
        self.reset_task(0)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(2,), dtype=np.float32)

    def reset_task(self, idx):
        """reset goal AND reset the agent"""
        if idx is not None:
            self._wind = np.array(self.winds[idx])
        self.reset()

    def set_goal(self, wind):
        self._wind = np.asarray(wind)

    def get_current_task(self):
        return self._wind.copy()

    def get_all_task_idx(self):
        return range(len(self.winds))

    def reset_model(self):
        self._state = np.array([0.0, 0.0])
        return self._get_obs()

    def reset(self):
        self.step_count = 0
        return self.reset_model()

    def _get_obs(self):
        return np.copy(self._state)

    def step(self, action):
        self._state = self._state + action + self._wind
        if self.is_goal_state():
            reward = 1.0
        else:
            reward = 0.0
        self.step_count += 1
        if self.step_count >= self._max_episode_steps:
            done = True
        else:
            done = False
        ob = self._get_obs()
        return (ob, reward, done, dict())

    def viewer_setup(self):
        print('no viewer')
        pass

    def render(self):
        print('current state:', self._state)

    def is_goal_state(self):
        if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
            return True
        else:
            return False

    def plot_env(self):
        ax = plt.gca()
        plt.axis('scaled')
        ax.set_xlim(-1, 1)
        ax.set_ylim(-0.5, 1.5)
        plt.xticks([])
        plt.yticks([])
        circle = plt.Circle((self._goal[0], self._goal[1]), radius=self.goal_radius, alpha=0.3)
        ax.add_artist(circle)
        X, Y = np.meshgrid(np.linspace(-0.8, 1, 5), np.linspace(-0.4, 1.5, 5))
        plt.quiver(X, Y, [self._wind[0]], [self._wind[1]])

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)

def is_goal_state(self):
    if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
        return True
    else:
        return False

class SparsePointEnv(PointEnv):
    """
    - tasks sampled from unit half-circle
    - reward is L2 distance given only within goal radius
    NOTE that `step()` returns the dense reward because this is used during meta-training
    the algorithm should call `sparsify_rewards()` to get the sparse rewards
    """

    def __init__(self, max_episode_steps=60, n_tasks=2, goal_radius=0.2, modify_init_state_dist=True, on_circle_init_state=True, **kwargs):
        super().__init__(max_episode_steps, n_tasks)
        self.goal_radius = goal_radius
        self.modify_init_state_dist = modify_init_state_dist
        self.on_circle_init_state = on_circle_init_state
        radius = 1.0
        angles = np.random.uniform(0, np.pi, size=n_tasks)
        xs = radius * np.cos(angles)
        ys = radius * np.sin(angles)
        goals = np.stack([xs, ys], axis=1)
        np.random.shuffle(goals)
        goals = goals.tolist()
        self.goals = goals
        self.reset_task(0)

    def sparsify_rewards(self, r):
        """zero out rewards when outside the goal radius"""
        mask = (r >= -self.goal_radius).astype(np.float32)
        r = r * mask
        return r

    def reset_model(self):
        self.step_count = 0
        if self.modify_init_state_dist:
            self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
            if not self.on_circle_init_state:
                while 1 - self.goal_radius <= np.linalg.norm(self._state) <= 1 + self.goal_radius:
                    self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
        else:
            self._state = np.array([0, 0])
        return self._get_obs()

    def step(self, action):
        ob, reward, done, d = super().step(action)
        sparse_reward = self.sparsify_rewards(reward)
        if reward >= -self.goal_radius:
            sparse_reward = 1
        d.update({'sparse_reward': sparse_reward})
        return (ob, sparse_reward, done, d)

    def reward(self, state, action=None):
        return self.sparsify_rewards(super().reward(state, action))

    def is_goal_state(self):
        if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
            return True
        else:
            return False

    def plot_env(self):
        ax = plt.gca()
        angles = np.linspace(0, np.pi, num=100)
        x, y = (np.cos(angles), np.sin(angles))
        plt.plot(x, y, color='k')
        plt.axis('scaled')
        ax.set_xlim(-2, 2)
        ax.set_ylim(-1, 2)
        plt.xticks([])
        plt.yticks([])
        circle = plt.Circle((self._goal[0], self._goal[1]), radius=self.goal_radius, alpha=0.3)
        ax.add_artist(circle)

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        plt.scatter(observations[[0], 0], observations[[0], 1], marker='x', **kwargs)
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)

def reset_model(self):
    self.step_count = 0
    if self.modify_init_state_dist:
        self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
        if not self.on_circle_init_state:
            while 1 - self.goal_radius <= np.linalg.norm(self._state) <= 1 + self.goal_radius:
                self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
    else:
        self._state = np.array([0, 0])
    return self._get_obs()

def is_goal_state(self):
    if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
        return True
    else:
        return False

def soft_update_from_to(source, target, tau):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(target_param.data * (1.0 - tau) + param.data * tau)

def copy_model_params_from_to(source, target):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(param.data)

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

class ModelFreeOffPolicy_RNN_MLP(ModelFreeOffPolicy_Separate_RNN):
    """
    Markov Actor and Recurrent Critic
    It may be more effective on some special cases of POMDPs,
        where the reward is history-dependent, but Markov actor
        is sufficient to solve the task.
    """
    ARCH = 'memory-markov'
    Markov_Actor = True
    Markov_Critic = False

    def __init__(self, obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers=1, lr=0.0003, gamma=0.99, tau=0.005, image_encoder_fn=lambda: None, **kwargs):
        super().__init__(obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers, lr, gamma, tau, image_encoder_fn, **kwargs)
        self.actor = self.algo.build_actor(input_size=obs_dim, action_dim=action_dim, hidden_sizes=policy_layers, image_encoder=image_encoder_fn())
        self.actor_optimizer = Adam(self.actor.parameters(), lr=lr)
        self.actor_target = deepcopy(self.actor)

    @torch.no_grad()
    def act(self, obs, deterministic=False, return_log_prob=False):
        return self.algo.select_action(actor=self.actor, observ=obs, deterministic=deterministic, return_log_prob=return_log_prob)

    def report_grad_norm(self):
        return {'q_grad_norm': utl.get_grad_norm(self.critic), 'q_rnn_grad_norm': utl.get_grad_norm(self.critic.rnn), 'pi_grad_norm': utl.get_grad_norm(self.actor)}

def __init__(self, obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers=1, lr=0.0003, gamma=0.99, tau=0.005, image_encoder_fn=lambda: None, **kwargs):
    super().__init__(obs_dim, action_dim, encoder, algo_name, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, dqn_layers, policy_layers, rnn_num_layers, lr, gamma, tau, image_encoder_fn, **kwargs)
    self.actor = self.algo.build_actor(input_size=obs_dim, action_dim=action_dim, hidden_sizes=policy_layers, image_encoder=image_encoder_fn())
    self.actor_optimizer = Adam(self.actor.parameters(), lr=lr)
    self.actor_target = deepcopy(self.actor)

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

class Actor_RNN(nn.Module):

    def __init__(self, obs_dim, action_dim, encoder, algo, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, policy_layers, rnn_num_layers, image_encoder=None, **kwargs):
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
        self.num_layers = rnn_num_layers
        self.rnn = RNNs[encoder](input_size=rnn_input_size, hidden_size=self.rnn_hidden_size, num_layers=self.num_layers, batch_first=False, bias=True)
        for name, param in self.rnn.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                nn.init.orthogonal_(param)
        if self.image_encoder is None:
            self.current_observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
        self.policy = self.algo.build_actor(input_size=self.rnn_hidden_size + observ_embedding_size, action_dim=self.action_dim, hidden_sizes=policy_layers)

    def _get_obs_embedding(self, observs):
        if self.image_encoder is None:
            return self.observ_embedder(observs)
        else:
            return self.image_encoder(observs)

    def _get_shortcut_obs_embedding(self, observs):
        if self.image_encoder is None:
            return self.current_observ_embedder(observs)
        else:
            return self.image_encoder(observs)

    def get_hidden_states(self, prev_actions, rewards, observs, initial_internal_state=None):
        input_a = self.action_embedder(prev_actions)
        input_r = self.reward_embedder(rewards)
        input_s = self._get_obs_embedding(observs)
        inputs = torch.cat((input_a, input_r, input_s), dim=-1)
        if initial_internal_state is None:
            output, _ = self.rnn(inputs)
            return output
        else:
            output, current_internal_state = self.rnn(inputs, initial_internal_state)
            return (output, current_internal_state)

    def forward(self, prev_actions, rewards, observs):
        """
        For prev_actions a, rewards r, observs o: (T+1, B, dim)
                a[t] -> r[t], o[t]

        return current actions a' (T+1, B, dim) based on previous history

        """
        assert prev_actions.dim() == rewards.dim() == observs.dim() == 3
        assert prev_actions.shape[0] == rewards.shape[0] == observs.shape[0]
        hidden_states = self.get_hidden_states(prev_actions=prev_actions, rewards=rewards, observs=observs)
        curr_embed = self._get_shortcut_obs_embedding(observs)
        joint_embeds = torch.cat((hidden_states, curr_embed), dim=-1)
        return self.algo.forward_actor(actor=self.policy, observ=joint_embeds)

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
        hidden_state, current_internal_state = self.get_hidden_states(prev_actions=prev_action, rewards=reward, observs=obs, initial_internal_state=prev_internal_state)
        curr_embed = self._get_shortcut_obs_embedding(obs)
        joint_embeds = torch.cat((hidden_state, curr_embed), dim=-1)
        if joint_embeds.dim() == 3:
            joint_embeds = joint_embeds.squeeze(0)
        action_tuple = self.algo.select_action(actor=self.policy, observ=joint_embeds, deterministic=deterministic, return_log_prob=return_log_prob)
        return (action_tuple, current_internal_state)

def __init__(self, obs_dim, action_dim, encoder, algo, action_embedding_size, observ_embedding_size, reward_embedding_size, rnn_hidden_size, policy_layers, rnn_num_layers, image_encoder=None, **kwargs):
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
    self.num_layers = rnn_num_layers
    self.rnn = RNNs[encoder](input_size=rnn_input_size, hidden_size=self.rnn_hidden_size, num_layers=self.num_layers, batch_first=False, bias=True)
    for name, param in self.rnn.named_parameters():
        if 'bias' in name:
            nn.init.constant_(param, 0)
        elif 'weight' in name:
            nn.init.orthogonal_(param)
    if self.image_encoder is None:
        self.current_observ_embedder = utl.FeatureExtractor(obs_dim, observ_embedding_size, F.relu)
    self.policy = self.algo.build_actor(input_size=self.rnn_hidden_size + observ_embedding_size, action_dim=self.action_dim, hidden_sizes=policy_layers)

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

