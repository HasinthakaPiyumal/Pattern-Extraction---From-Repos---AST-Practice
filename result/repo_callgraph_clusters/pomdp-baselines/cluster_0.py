# Cluster 0

def get_run_down(dataframe, key, last_steps_ratio=FLAGS.last_steps_ratio):
    dataframe[key + auc_tag] = dataframe.groupby([merged_tag, trial_tag])[key].transform(lambda x: x[int(last_steps_ratio * len(x)):].mean())
    tmp_df = dataframe.groupby([merged_tag, trial_tag]).tail(1)
    run_down = tmp_df.groupby([merged_tag])[key + auc_tag].mean()
    run_down_std = tmp_df.groupby([merged_tag])[key + auc_tag].std()
    run_down_std.name += '_std'
    return (run_down, run_down_std)

def get_run_down(dataframe, key, last_steps_ratio=FLAGS.last_steps_ratio):
    dataframe[key + auc_tag] = dataframe.groupby([merged_tag, trial_tag])[key].transform(lambda x: x[int(last_steps_ratio * len(x)):].mean())
    tmp_df = dataframe.groupby([merged_tag, trial_tag]).tail(1)
    run_down = tmp_df.groupby([merged_tag])[key + auc_tag].mean()
    run_down_std = tmp_df.groupby([merged_tag])[key + auc_tag].std()
    run_down_std.name += '_std'
    return (run_down, run_down_std)

def get_variant_tags(trial_str, max_episode_len):
    v = dict()
    if 'sac_' in trial_str:
        v['RL'] = 'sac'
    elif 'sacd_' in trial_str:
        v['RL'] = 'sacd'
    elif 'td3' in trial_str:
        v['RL'] = 'td3'
    if 'lstm' in trial_str:
        v['Encoder'] = 'lstm'
    elif 'gru' in trial_str:
        v['Encoder'] = 'gru'
    if 'shared' in trial_str:
        v['Arch'] = 'shared'
    else:
        v['Arch'] = 'separate'
    v['Len'] = int(trial_str[trial_str.index('len-') + 4:].split('/')[0])
    if v['Len'] == -1:
        v['Len'] = max_episode_len
    v['Inputs'] = trial_str.split('/')[-3]
    return v

def log(*args, level=INFO):
    """
    Write the sequence of args, with no separators, to the console and output files (if you've configured an output file).
    """
    Logger.CURRENT.log(*args, level=level)

def debug(*args):
    log(*args, level=DEBUG)

def info(*args):
    log(*args, level=INFO)

def warn(*args):
    log(*args, level=WARN)

def error(*args):
    log(*args, level=ERROR)

class RandomOffsetPlayerSpaceInvadersWorld(SpaceInvadersWorld):
    offset_range_start = 25
    offset_range_end = 125

    def initial_shield_configuration(self):
        return [{'health': 20, 'position': (self._width // 4, 200)}, {'health': 20, 'position': (2 * self._width // 4, 200)}, {'health': 20, 'position': (3 * self._width // 4, 200)}]

    def initial_player_ship_position(self):
        """Initial player ship position after reset."""
        self._player_offset = int(self.np_random.uniform(self.offset_range_start, self.offset_range_end))
        return (self._width / 2, self._player_offset)

    @property
    def parameters(self):
        parameters = super(RandomOffsetPlayerSpaceInvadersWorld, self).parameters
        parameters.update({'player_offset': self._player_offset})
        return parameters

def initial_player_ship_position(self):
    """Initial player ship position after reset."""
    self._player_offset = int(self.np_random.uniform(self.offset_range_start, self.offset_range_end))
    return (self._width / 2, self._player_offset)

class RandomOffsetPaddleBreakoutWorld(BreakoutWorld):
    offset_range_start = 25
    offset_range_end = 110

    def initial_paddle_position(self):
        """Initial paddle position after reset."""
        self._paddle_offset = int(self.np_random.uniform(self.offset_range_start, self.offset_range_end))
        return (self._width / 2, self._paddle_offset)

    @property
    def parameters(self):
        parameters = super(RandomOffsetPaddleBreakoutWorld, self).parameters
        parameters.update({'paddle_offset': self._paddle_offset})
        return parameters

def initial_paddle_position(self):
    """Initial paddle position after reset."""
    self._paddle_offset = int(self.np_random.uniform(self.offset_range_start, self.offset_range_end))
    return (self._width / 2, self._paddle_offset)

class RandomOffsetBricksBreakoutWorld(BreakoutWorld):
    brick_offset_range_start = 0
    brick_offset_range_end = 80

    def initial_brick_position(self):
        """Initial brick row offset after reset."""
        self._brick_offset = int(self.np_random.uniform(self.brick_offset_range_start, self.brick_offset_range_end))
        return self._brick_offset

    @property
    def parameters(self):
        parameters = super(RandomOffsetBricksBreakoutWorld, self).parameters
        parameters.update({'brick_offset': self._brick_offset})
        return parameters

def initial_brick_position(self):
    """Initial brick row offset after reset."""
    self._brick_offset = int(self.np_random.uniform(self.brick_offset_range_start, self.brick_offset_range_end))
    return self._brick_offset

class DelayedCatch(gym.Env):

    def __init__(self, delay, grid_size=7, flatten_img=True, delayed=True, one_hot_actions=False):
        super().__init__()
        self.grid_size = grid_size
        self.delay = delay
        self.num_catches = (delay + 1) // 7
        self.action_space = gym.spaces.Discrete(3)
        self.image_space = gym.spaces.MultiDiscrete([[[2 for i in range(grid_size)] for i in range(grid_size)]])
        self.flatten_img = flatten_img
        if flatten_img:
            self.observation_space = gym.spaces.MultiDiscrete([2 for i in range(grid_size * grid_size)])
        else:
            self.observation_space = self.image_space
        self.delayed = delayed
        self.one_hot_actions = one_hot_actions

    def _update_state(self, action):
        """
        Input: action and states
        Ouput: new states and reward
        """
        state = self.state
        if self.one_hot_actions:
            action = np.argmax(action)
        if action == 0:
            action = -1
        elif action == 1:
            action = 0
        elif action == 2:
            action = 1
        else:
            raise ValueError('not valid action')
        f0, f1, basket = state[0]
        new_basket = min(max(0, basket + action), self.grid_size - 1)
        f0 += 1
        out = np.asarray([f0, f1, new_basket])
        out = out[np.newaxis]
        assert len(out.shape) == 2
        self.state = out

    def _draw_state(self):
        im_size = (self.grid_size,) * 2
        state = self.state[0]
        canvas = np.zeros(im_size)
        canvas[state[0], state[1]] = -1
        canvas[-1, int(state[2])] = 1
        return canvas

    def _get_reward(self):
        fruit_row, fruit_col, basket = self.state[0]
        if fruit_row == self.grid_size - 1:
            if fruit_col == basket:
                return 1
            else:
                return 0
        else:
            return 0

    def _is_over(self):
        if self.state[0, 0] == self.grid_size - 1:
            return True
        else:
            return False

    def observe(self):
        canvas = self._draw_state()
        if self.flatten_img:
            return canvas.reshape(-1)
        else:
            return np.expand_dims(canvas, axis=0)

    def step(self, action):
        self.time_step += 1
        info = {}
        if self._is_over():
            obs = self.soft_reset()
            reward = self._get_reward()
            info['reward'] = reward
            self.accumulated_reward += reward
            return (obs, 0, False, info)
        self._update_state(action)
        reward = self._get_reward()
        info['reward'] = reward
        self.accumulated_reward += reward
        if not self.delayed:
            return (self.observe(), reward, False, info)
        if self.time_step >= self.delay:
            return (self.observe(), self.accumulated_reward, True, info)
        else:
            return (self.observe(), 0, False, info)

    def reset(self):
        self.catch_count = 0
        self.ns = np.random.randint(0, self.grid_size - 1, size=self.num_catches)
        self.ms = np.random.randint(1, self.grid_size - 2, size=self.num_catches)
        obs = self.soft_reset()
        self.accumulated_reward = 0
        self.time_step = 0
        return obs

    def soft_reset(self):
        n = self.ns[self.catch_count]
        m = self.ms[self.catch_count]
        self.state = np.asarray([0, n, m])[np.newaxis]
        self.catch_count += 1
        return self.observe()

def _update_state(self, action):
    """
        Input: action and states
        Ouput: new states and reward
        """
    state = self.state
    if self.one_hot_actions:
        action = np.argmax(action)
    if action == 0:
        action = -1
    elif action == 1:
        action = 0
    elif action == 2:
        action = 1
    else:
        raise ValueError('not valid action')
    f0, f1, basket = state[0]
    new_basket = min(max(0, basket + action), self.grid_size - 1)
    f0 += 1
    out = np.asarray([f0, f1, new_basket])
    out = out[np.newaxis]
    assert len(out.shape) == 2
    self.state = out

def _draw_state(self):
    im_size = (self.grid_size,) * 2
    state = self.state[0]
    canvas = np.zeros(im_size)
    canvas[state[0], state[1]] = -1
    canvas[-1, int(state[2])] = 1
    return canvas

class GridNavi(gym.Env):

    def __init__(self, num_cells=5, num_steps=15, n_tasks=2, modify_init_state_dist=False, is_sparse=False, return_belief_rewards=False, seed=None, **kwargs):
        super(GridNavi, self).__init__()
        if seed is not None:
            self.seed(seed)
        self.n_tasks = n_tasks
        self.num_cells = num_cells
        self.num_states = num_cells ** 2
        self.grid_size = (num_cells, num_cells)
        self.is_sparse = is_sparse
        self.return_belief_rewards = return_belief_rewards
        self.modify_init_state_dist = modify_init_state_dist
        self._max_episode_steps = num_steps
        self.step_count = 0
        self.observation_space = spaces.Box(low=0, high=self.num_cells - 1, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Discrete(5)
        self.starting_states = [(0.0, 0.0)]
        self.states = [(x, y) for y in np.arange(0, num_cells) for x in np.arange(0, num_cells)]
        self.possible_goals = self.states.copy()
        for s in self.starting_states:
            self.possible_goals.remove(s)
        self.possible_goals.remove((0, 1))
        self.possible_goals.remove((1, 1))
        self.possible_goals.remove((1, 0))
        self.num_tasks = min(n_tasks, len(self.possible_goals))
        self.goals = random.sample(self.possible_goals, self.num_tasks)
        self.reset_task(0)
        if self.return_belief_rewards:
            self._belief_state = self._reset_belief()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        random.seed(seed)
        return [seed]

    def get_all_task_idx(self):
        return range(len(self.goals))

    def get_task(self):
        return self._goal

    def set_goal(self, goal):
        self._goal = np.asarray(goal)

    def reset_task(self, idx=None):
        """reset goal and state"""
        if idx is not None:
            self._goal = np.array(self.goals[idx])
        self.reset()

    def _reset_belief(self):
        self._belief_state = np.zeros(self.num_cells ** 2)
        for pg in self.possible_goals:
            idx = self.task_to_id(np.array(pg))
            self._belief_state[idx] = 1.0 / len(self.possible_goals)
        return self._belief_state

    def reset_model(self):
        if self.modify_init_state_dist:
            self._state = np.array(random.choice(self.states))
            while (self._state == self._goal).all():
                self._state = np.array(random.choice(self.states))
        else:
            self._state = np.array(random.choice(self.starting_states))
        self._belief_state = self._reset_belief()
        return self.get_obs()

    def get_obs(self):
        return np.copy(self._state)

    def update_belief(self, state):
        if self.is_goal_state():
            self._belief_state *= 0
            self._belief_state[self.task_to_id(self._goal)] = 1
        else:
            self._belief_state[self.task_to_id(state)] = 0
            self._belief_state = np.ceil(self._belief_state)
            self._belief_state /= sum(self._belief_state)

    def reset(self):
        self.step_count = 0
        return self.reset_model()

    def reward(self, state, action=None):
        if state[0] == self._goal[0] and state[1] == self._goal[1]:
            return 1.0
        else:
            return 0.0 if self.is_sparse else -0.1

    def state_transition(self, action):
        """
        Moving the agent between states
        """
        if action == 1:
            self._state[1] = min([self._state[1] + 1, self.num_cells - 1])
        elif action == 2:
            self._state[0] = min([self._state[0] + 1, self.num_cells - 1])
        elif action == 3:
            self._state[1] = max([self._state[1] - 1, 0])
        elif action == 4:
            self._state[0] = max([self._state[0] - 1, 0])

    def step(self, action):
        if isinstance(action, np.ndarray) and action.ndim == 1:
            action = action[0]
        assert self.action_space.contains(action)
        info = {'task': self.get_task()}
        done = False
        self.state_transition(action)
        self.step_count += 1
        if self.step_count >= self._max_episode_steps:
            done = True
        if self.return_belief_rewards:
            self.update_belief(self._state)
            belief_reward = self._compute_belief_reward()
            info.update({'belief_reward': belief_reward})
        reward = self.reward(self._state)
        return (self.get_obs(), reward, done, info)

    def _compute_belief_reward(self):
        num_possible_goal_belief = np.sum(self._belief_state != 0)
        non_goal_rew = 0.0 if self.is_sparse else -0.1
        belief_reward = (1.0 + non_goal_rew * (num_possible_goal_belief - 1)) / num_possible_goal_belief
        return belief_reward

    def is_goal_state(self):
        if self._state[0] == self._goal[0] and self._state[1] == self._goal[1]:
            return True
        else:
            return False

    def task_to_id(self, goals):
        mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).transpose(1, 0)
        if isinstance(goals, list) or isinstance(goals, tuple):
            goals = np.array(goals)
        if isinstance(goals, np.ndarray):
            goals = torch.from_numpy(goals)
        goals = goals.long()
        if goals.dim() == 1:
            goals = goals.unsqueeze(0)
        goal_shape = goals.shape
        if len(goal_shape) > 2:
            goals = goals.reshape(-1, goals.shape[-1])
        classes = mat[goals[:, 0], goals[:, 1]]
        classes = classes.reshape(goal_shape[:-1])
        return classes

    def id_to_task(self, classes):
        mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).numpy().T
        goals = np.zeros((len(classes), 2))
        classes = classes.numpy()
        for i in range(len(classes)):
            pos = np.where(classes[i] == mat)
            goals[i, 0] = float(pos[0][0])
            goals[i, 1] = float(pos[1][0])
        goals = torch.from_numpy(goals).to(ptu.device).float()
        return goals

    def goal_to_onehot_id(self, pos):
        cl = self.task_to_id(pos)
        if cl.dim() == 1:
            cl = cl.view(-1, 1)
        nb_digits = self.num_cells ** 2
        y_onehot = torch.FloatTensor(pos.shape[0], nb_digits).to(ptu.device)
        y_onehot.zero_()
        y_onehot.scatter_(1, cl, 1)
        return y_onehot

    def onehot_id_to_goal(self, pos):
        if isinstance(pos, list):
            pos = [self.id_to_task(p.argmax(dim=1)) for p in pos]
        else:
            pos = self.id_to_task(pos.argmax(dim=1))
        return pos

    def render(self, mode='human'):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def plot_env(self):
        for i in range(self.num_cells):
            for j in range(self.num_cells):
                pos_i = i
                pos_j = j
                rec = Rectangle((pos_i, pos_j), 1, 1, facecolor='none', alpha=0.5, edgecolor='k')
                plt.gca().add_patch(rec)
        goal = np.array(self._goal) + 0.5
        plt.plot(goal[0], goal[1], 'kx')
        plt.plot(goal[0], goal[1], 'kx')

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        if isinstance(observations, tuple) or isinstance(observations, list):
            observations = torch.cat(observations)
        observations = observations + 0.5
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)
        plt.plot(observations[-1, 0], observations[-1, 1], **kwargs)
        plt.xticks([])
        plt.yticks([])
        plt.xlim([0, self.num_cells])
        plt.ylim([0, self.num_cells])
        plt.axis('equal')

def state_transition(self, action):
    """
        Moving the agent between states
        """
    if action == 1:
        self._state[1] = min([self._state[1] + 1, self.num_cells - 1])
    elif action == 2:
        self._state[0] = min([self._state[0] + 1, self.num_cells - 1])
    elif action == 3:
        self._state[1] = max([self._state[1] - 1, 0])
    elif action == 4:
        self._state[0] = max([self._state[0] - 1, 0])

class RAMEfficient_SeqReplayBuffer:
    buffer_type = 'seq_efficient'

    def __init__(self, max_replay_buffer_size, observation_dim, action_dim, sampled_seq_len: int, sample_weight_baseline: float, observation_type, **kwargs):
        """
        this buffer is used for sequence/trajectory/episode:
                it stored the whole sequence
                into the buffer (not transition), and can sample (sub)sequences
                that has 3D shape (sampled_seq_len, batch_size, dim)
                based on some rules below.
        it still uses 2D size as normal (max_replay_buffer_size, dim)
                but tracks the sequences

        NOTE: it only save observations once, no next_observation to reduce RAM by ~2,
            especially useful for image observations

        """
        self._max_replay_buffer_size = max_replay_buffer_size
        self._observation_dim = observation_dim
        self._action_dim = action_dim
        if observation_type == np.uint8:
            observation_type = np.uint8
        else:
            observation_type = np.float32
        self._observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=observation_type)
        self._actions = np.zeros((max_replay_buffer_size, action_dim), dtype=np.float32)
        self._rewards = np.zeros((max_replay_buffer_size, 1), dtype=np.float32)
        self._terminals = np.zeros((max_replay_buffer_size, 1), dtype=np.uint8)
        self._ends = np.zeros(max_replay_buffer_size, dtype=np.uint8)
        self._valid_starts = np.zeros(max_replay_buffer_size, dtype=np.float32)
        assert sampled_seq_len >= 2
        assert sample_weight_baseline >= 0.0
        self._sampled_seq_len = sampled_seq_len
        self._sample_weight_baseline = sample_weight_baseline
        self.clear()
        RAM = 0.0
        for name, var in vars(self).items():
            if isinstance(var, np.ndarray):
                RAM += var.nbytes
        print(f'buffer RAM usage: {RAM / 1024 ** 3:.2f} GB')

    def size(self):
        return self._size

    def clear(self):
        self._top = 0
        self._size = 0

    def add_episode(self, observations, actions, rewards, terminals, next_observations):
        """
        NOTE: must add one whole episode/sequence/trajectory,
                        not some partial transitions
        the length of different episode can vary, but must be greater than 2
                so that the end of valid_starts is 0.

        all the inputs have 2D shape of (L, dim)
        """
        assert observations.shape[0] == actions.shape[0] == rewards.shape[0] == terminals.shape[0] == next_observations.shape[0] >= 2
        seq_len = observations.shape[0]
        indices = list(np.arange(self._top, self._top + seq_len) % self._max_replay_buffer_size)
        self._observations[indices] = observations
        self._actions[indices] = actions
        self._rewards[indices] = rewards
        self._terminals[indices] = terminals
        self._valid_starts[indices] = self._compute_valid_starts(seq_len)
        self._ends[indices] = 0
        self._top = (self._top + seq_len) % self._max_replay_buffer_size
        self._observations[self._top] = next_observations[-1]
        self._actions[self._top] = 0.0
        self._rewards[self._top] = 0.0
        self._terminals[self._top] = 1
        self._valid_starts[self._top] = 0.0
        self._ends[self._top] = 1
        self._top = (self._top + 1) % self._max_replay_buffer_size
        self._size = min(self._size + seq_len + 1, self._max_replay_buffer_size)

    def _compute_valid_starts(self, seq_len):
        valid_starts = np.ones(seq_len, dtype=float)
        num_valid_starts = float(max(1.0, seq_len - self._sampled_seq_len + 1.0))
        total_weights = self._sample_weight_baseline + num_valid_starts
        valid_starts *= total_weights / num_valid_starts
        valid_starts[int(num_valid_starts):] = 0.0
        return valid_starts

    def random_episodes(self, batch_size):
        """
        return each item has 3D shape (sampled_seq_len, batch_size, dim)
        """
        sampled_episode_starts = self._sample_indices(batch_size)
        indices = []
        next_indices = []
        for start in sampled_episode_starts:
            end = start + self._sampled_seq_len
            indices += list(np.arange(start, end) % self._max_replay_buffer_size)
            next_indices += list(np.arange(start + 1, end + 1) % self._max_replay_buffer_size)
        batch = self._sample_data(indices, next_indices)
        masks = self._generate_masks(indices, batch_size)
        batch['mask'] = masks
        for k in batch.keys():
            batch[k] = batch[k].reshape(batch_size, self._sampled_seq_len, -1).transpose(1, 0, 2)
        return batch

    def _sample_indices(self, batch_size):
        valid_starts_indices = np.where(self._valid_starts > 0.0)[0]
        sample_weights = np.copy(self._valid_starts[valid_starts_indices])
        sample_weights /= sample_weights.sum()
        return np.random.choice(valid_starts_indices, size=batch_size, p=sample_weights)

    def _sample_data(self, indices, next_indices):
        return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._observations[next_indices])

    def _generate_masks(self, indices, batch_size):
        """
        input: sampled_indices list of len B*T
        output: masks (B, T)
        """
        sampled_seq_ends = np.copy(self._ends[indices]).reshape(batch_size, self._sampled_seq_len).astype(np.float32)
        masks = np.ones_like(sampled_seq_ends)
        diff = sampled_seq_ends[:, :-1] - sampled_seq_ends[:, 1:]
        diff = np.concatenate([np.zeros((batch_size, 1)), diff], axis=1)
        invalid_starts_b, invalid_starts_t = np.where(diff == -1.0)
        invalid_indices_b = []
        invalid_indices_t = []
        last_batch_index = -1
        for batch_index, start_index in zip(invalid_starts_b, invalid_starts_t):
            if batch_index == last_batch_index:
                continue
            last_batch_index = batch_index
            invalid_indices = list(np.arange(start_index, self._sampled_seq_len))
            invalid_indices_b += [batch_index] * len(invalid_indices)
            invalid_indices_t += invalid_indices
        masks[invalid_indices_b, invalid_indices_t] = 0.0
        return masks

def _compute_valid_starts(self, seq_len):
    valid_starts = np.ones(seq_len, dtype=float)
    num_valid_starts = float(max(1.0, seq_len - self._sampled_seq_len + 1.0))
    total_weights = self._sample_weight_baseline + num_valid_starts
    valid_starts *= total_weights / num_valid_starts
    valid_starts[int(num_valid_starts):] = 0.0
    return valid_starts

class SeqReplayBuffer:
    buffer_type = 'seq_vanilla'

    def __init__(self, max_replay_buffer_size, observation_dim, action_dim, sampled_seq_len: int, sample_weight_baseline: float, **kwargs):
        """
        this buffer is used for sequence/trajectory/episode:
                it stored the whole sequence
                into the buffer (not transition), and can sample (sub)sequences
                that has 3D shape (sampled_seq_len, batch_size, dim)
                based on some rules below.
        it still uses 2D size as normal (max_replay_buffer_size, dim)
                but tracks the sequences

        NOTE: it save observations twice, so it is vanilla version of seq replay buffer,
            sufficient to vector-based observations, as RAM is not the bottleneck
        """
        self._max_replay_buffer_size = max_replay_buffer_size
        self._observation_dim = observation_dim
        self._action_dim = action_dim
        self._observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=np.float32)
        self._next_observations = np.zeros((max_replay_buffer_size, observation_dim), dtype=np.float32)
        self._actions = np.zeros((max_replay_buffer_size, action_dim), dtype=np.float32)
        self._rewards = np.zeros((max_replay_buffer_size, 1), dtype=np.float32)
        self._terminals = np.zeros((max_replay_buffer_size, 1), dtype=np.uint8)
        self._valid_starts = np.zeros(max_replay_buffer_size, dtype=np.float32)
        assert sampled_seq_len >= 2
        assert sample_weight_baseline >= 0.0
        self._sampled_seq_len = sampled_seq_len
        self._sample_weight_baseline = sample_weight_baseline
        self.clear()
        RAM = 0.0
        for name, var in vars(self).items():
            if isinstance(var, np.ndarray):
                RAM += var.nbytes
        print(f'buffer RAM usage: {RAM / 1024 ** 3:.2f} GB')

    def size(self):
        return self._size

    def clear(self):
        self._top = 0
        self._size = 0

    def add_episode(self, observations, actions, rewards, terminals, next_observations):
        """
        NOTE: must add one whole episode/sequence/trajectory,
                        not some partial transitions
        the length of different episode can vary, but must be greater than 2
                so that the end of valid_starts is 0.

        all the inputs have 2D shape of (L, dim)
        """
        assert observations.shape[0] == actions.shape[0] == rewards.shape[0] == terminals.shape[0] == next_observations.shape[0] >= 2
        seq_len = observations.shape[0]
        indices = list(np.arange(self._top, self._top + seq_len) % self._max_replay_buffer_size)
        self._observations[indices] = observations
        self._actions[indices] = actions
        self._rewards[indices] = rewards
        self._terminals[indices] = terminals
        self._next_observations[indices] = next_observations
        self._valid_starts[indices] = self._compute_valid_starts(seq_len)
        self._top = (self._top + seq_len) % self._max_replay_buffer_size
        self._size = min(self._size + seq_len, self._max_replay_buffer_size)

    def _compute_valid_starts(self, seq_len):
        valid_starts = np.ones(seq_len, dtype=float)
        num_valid_starts = float(max(1.0, seq_len - self._sampled_seq_len + 1.0))
        total_weights = self._sample_weight_baseline + num_valid_starts
        valid_starts *= total_weights / num_valid_starts
        valid_starts[int(num_valid_starts):] = 0.0
        return valid_starts

    def random_episodes(self, batch_size):
        """
        return each item has 3D shape (sampled_seq_len, batch_size, dim)
        """
        sampled_episode_starts = self._sample_indices(batch_size)
        indices = []
        for start in sampled_episode_starts:
            end = start + self._sampled_seq_len
            indices += list(np.arange(start, end) % self._max_replay_buffer_size)
        batch = self._sample_data(indices)
        masks = self._generate_masks(indices, batch_size)
        batch['mask'] = masks
        for k in batch.keys():
            batch[k] = batch[k].reshape(batch_size, self._sampled_seq_len, -1).transpose(1, 0, 2)
        return batch

    def _sample_indices(self, batch_size):
        valid_starts_indices = np.where(self._valid_starts > 0.0)[0]
        sample_weights = np.copy(self._valid_starts[valid_starts_indices])
        sample_weights /= sample_weights.sum()
        return np.random.choice(valid_starts_indices, size=batch_size, p=sample_weights)

    def _sample_data(self, indices):
        return dict(obs=self._observations[indices], act=self._actions[indices], rew=self._rewards[indices], term=self._terminals[indices], obs2=self._next_observations[indices])

    def _generate_masks(self, indices, batch_size):
        """
        input: sampled_indices list of len B*T
        output: masks (B, T)
        """
        sampled_seq_valids = np.copy(self._valid_starts[indices]).reshape(batch_size, self._sampled_seq_len)
        sampled_seq_valids[sampled_seq_valids > 0.0] = 1.0
        masks = np.ones_like(sampled_seq_valids, dtype=float)
        diff = sampled_seq_valids[:, :-1] - sampled_seq_valids[:, 1:]
        diff = np.concatenate([np.ones((batch_size, 1)), diff], axis=1)
        indices_array = np.array(indices).reshape(batch_size, self._sampled_seq_len)
        diff[indices_array == self._top] = -1.0
        invalid_starts_b, invalid_starts_t = np.where(diff == -1.0)
        invalid_indices_b = []
        invalid_indices_t = []
        last_batch_index = -1
        for batch_index, start_index in zip(invalid_starts_b, invalid_starts_t):
            if batch_index == last_batch_index:
                continue
            last_batch_index = batch_index
            invalid_indices = list(np.arange(start_index, self._sampled_seq_len))
            invalid_indices_b += [batch_index] * len(invalid_indices)
            invalid_indices_t += invalid_indices
        masks[invalid_indices_b, invalid_indices_t] = 0.0
        return masks

def _compute_valid_starts(self, seq_len):
    valid_starts = np.ones(seq_len, dtype=float)
    num_valid_starts = float(max(1.0, seq_len - self._sampled_seq_len + 1.0))
    total_weights = self._sample_weight_baseline + num_valid_starts
    valid_starts *= total_weights / num_valid_starts
    valid_starts[int(num_valid_starts):] = 0.0
    return valid_starts

class LayerNorm(nn.Module):
    """
    Simple 1D LayerNorm.
    """

    def __init__(self, features, center=True, scale=False, eps=1e-06):
        super().__init__()
        self.center = center
        self.scale = scale
        self.eps = eps
        if self.scale:
            self.scale_param = nn.Parameter(torch.ones(features))
        else:
            self.scale_param = None
        if self.center:
            self.center_param = nn.Parameter(torch.zeros(features))
        else:
            self.center_param = None

    def forward(self, x):
        mean = x.mean(-1, keepdim=True)
        std = x.std(-1, keepdim=True)
        output = (x - mean) / (std + self.eps)
        if self.scale:
            output = output * self.scale_param
        if self.center:
            output = output + self.center_param
        return output

def __init__(self, features, center=True, scale=False, eps=1e-06):
    super().__init__()
    self.center = center
    self.scale = scale
    self.eps = eps
    if self.scale:
        self.scale_param = nn.Parameter(torch.ones(features))
    else:
        self.scale_param = None
    if self.center:
        self.center_param = nn.Parameter(torch.zeros(features))
    else:
        self.center_param = None

def forward(self, x):
    mean = x.mean(-1, keepdim=True)
    std = x.std(-1, keepdim=True)
    output = (x - mean) / (std + self.eps)
    if self.scale:
        output = output * self.scale_param
    if self.center:
        output = output + self.center_param
    return output

class TanhNormal(Distribution):
    """aka squashed normal
    Represent distribution of X where
        X ~ tanh(Z)
        Z ~ N(mean, std)
    Note: this is not very numerically stable.
    """

    def __init__(self, normal_mean, normal_std, epsilon=1e-06):
        """
        :param normal_mean: Mean of the normal distribution
        :param normal_std: Std of the normal distribution
        :param epsilon: Numerical stability epsilon when computing log-prob.
        """
        self.normal_mean = normal_mean
        self.normal_std = normal_std
        self.normal = Normal(normal_mean, normal_std)
        self.epsilon = epsilon

    def sample_n(self, n, return_pre_tanh_value=False):
        z = self.normal.sample_n(n)
        if return_pre_tanh_value:
            return (torch.tanh(z), z)
        else:
            return torch.tanh(z)

    def log_prob(self, value, pre_tanh_value=None):
        """
        :param value: some value, x
        :param pre_tanh_value: arctanh(x)
        :return:
        """
        if pre_tanh_value is None:
            pre_tanh_value = torch.atanh(value)
        return self.normal.log_prob(pre_tanh_value) - torch.log(1 - value * value + self.epsilon)

    def sample(self, return_pretanh_value=False):
        z = self.normal.sample()
        if return_pretanh_value:
            return (torch.tanh(z), z)
        else:
            return torch.tanh(z)

    def rsample(self, return_pretanh_value=False):
        z = self.normal_mean + self.normal_std * Variable(Normal(ptu.zeros(self.normal_mean.size()), ptu.ones(self.normal_std.size())).sample())
        if return_pretanh_value:
            return (torch.tanh(z), z)
        else:
            return torch.tanh(z)

def log_prob(self, value, pre_tanh_value=None):
    """
        :param value: some value, x
        :param pre_tanh_value: arctanh(x)
        :return:
        """
    if pre_tanh_value is None:
        pre_tanh_value = torch.atanh(value)
    return self.normal.log_prob(pre_tanh_value) - torch.log(1 - value * value + self.epsilon)

def cross_entropy_one_hot(source, target, reduction='none'):
    _, labels = target.max(dim=-1)
    return F.cross_entropy(source, labels, reduction=reduction)

def ones(*sizes, **kwargs):
    return torch.ones(*sizes, **kwargs).to(device)

class Learner:

    def __init__(self, env_args, train_args, eval_args, policy_args, seed, **kwargs):
        self.seed = seed
        self.init_env(**env_args)
        self.init_agent(**policy_args)
        self.init_train(**train_args)
        self.init_eval(**eval_args)

    def init_env(self, env_type, env_name, max_rollouts_per_task=None, num_tasks=None, num_train_tasks=None, num_eval_tasks=None, eval_envs=None, worst_percentile=None, **kwargs):
        assert env_type in ['meta', 'pomdp', 'credit', 'rmdp', 'generalize', 'atari']
        self.env_type = env_type
        if self.env_type == 'meta':
            from envs.meta.make_env import make_env
            self.train_env = make_env(env_name, max_rollouts_per_task, seed=self.seed, n_tasks=num_tasks, **kwargs)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            if self.train_env.n_tasks is not None:
                assert num_train_tasks >= num_eval_tasks > 0
                shuffled_tasks = np.random.permutation(self.train_env.unwrapped.get_all_task_idx())
                self.train_tasks = shuffled_tasks[:num_train_tasks]
                self.eval_tasks = shuffled_tasks[-num_eval_tasks:]
            else:
                assert num_tasks == num_train_tasks == None
                assert num_eval_tasks > 0
                self.train_tasks = []
                self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = max_rollouts_per_task
            self.max_trajectory_len = self.train_env.horizon_bamdp
        elif self.env_type in ['pomdp', 'credit']:
            import envs.pomdp
            import envs.credit_assign
            assert num_eval_tasks > 0
            self.train_env = gym.make(env_name)
            self.train_env.seed(self.seed)
            self.train_env.action_space.np_random.seed(self.seed)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            self.train_tasks = []
            self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        elif self.env_type == 'atari':
            from envs.atari import create_env
            assert num_eval_tasks > 0
            self.train_env = create_env(env_name)
            self.train_env.seed(self.seed)
            self.train_env.action_space.np_random.seed(self.seed)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            self.train_tasks = []
            self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        elif self.env_type == 'rmdp':
            sys.path.append('envs/rl-generalization')
            import sunblaze_envs
            assert num_eval_tasks > 0 and worst_percentile > 0.0 and (worst_percentile < 1.0)
            self.train_env = sunblaze_envs.make(env_name, **kwargs)
            self.train_env.seed(self.seed)
            assert np.all(self.train_env.action_space.low == -1)
            assert np.all(self.train_env.action_space.high == 1)
            self.eval_env = self.train_env
            self.eval_env.seed(self.seed + 1)
            self.worst_percentile = worst_percentile
            self.train_tasks = []
            self.eval_tasks = num_eval_tasks * [None]
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        elif self.env_type == 'generalize':
            sys.path.append('envs/rl-generalization')
            import sunblaze_envs
            self.train_env = sunblaze_envs.make(env_name, **kwargs)
            self.train_env.seed(self.seed)
            assert np.all(self.train_env.action_space.low == -1)
            assert np.all(self.train_env.action_space.high == 1)

            def check_env_class(env_name):
                if 'Normal' in env_name:
                    return 'R'
                if 'Extreme' in env_name:
                    return 'E'
                return 'D'
            self.train_env_name = check_env_class(env_name)
            self.eval_envs = {}
            for env_name, num_eval_task in eval_envs.items():
                eval_env = sunblaze_envs.make(env_name, **kwargs)
                eval_env.seed(self.seed + 1)
                self.eval_envs[eval_env] = (check_env_class(env_name), num_eval_task)
            logger.log(self.train_env_name, self.train_env)
            logger.log(self.eval_envs)
            self.train_tasks = []
            self.max_rollouts_per_task = 1
            self.max_trajectory_len = self.train_env._max_episode_steps
        else:
            raise ValueError
        if self.train_env.action_space.__class__.__name__ == 'Box':
            self.act_dim = self.train_env.action_space.shape[0]
            self.act_continuous = True
        else:
            assert self.train_env.action_space.__class__.__name__ == 'Discrete'
            self.act_dim = self.train_env.action_space.n
            self.act_continuous = False
        self.obs_dim = self.train_env.observation_space.shape[0]
        logger.log('obs_dim', self.obs_dim, 'act_dim', self.act_dim)

    def init_agent(self, seq_model, separate: bool=True, image_encoder=None, reward_clip=False, **kwargs):
        if seq_model == 'mlp':
            agent_class = AGENT_CLASSES['Policy_MLP']
            rnn_encoder_type = None
            assert separate == True
        elif '-mlp' in seq_model:
            agent_class = AGENT_CLASSES['Policy_RNN_MLP']
            rnn_encoder_type = seq_model.split('-')[0]
            assert separate == True
        else:
            rnn_encoder_type = seq_model
            if separate == True:
                agent_class = AGENT_CLASSES['Policy_Separate_RNN']
            else:
                agent_class = AGENT_CLASSES['Policy_Shared_RNN']
        self.agent_arch = agent_class.ARCH
        logger.log(agent_class, self.agent_arch)
        if image_encoder is not None:
            image_encoder_fn = lambda: ImageEncoder(image_shape=self.train_env.image_space.shape, **image_encoder)
        else:
            image_encoder_fn = lambda: None
        self.agent = agent_class(encoder=rnn_encoder_type, obs_dim=self.obs_dim, action_dim=self.act_dim, image_encoder_fn=image_encoder_fn, **kwargs).to(ptu.device)
        logger.log(self.agent)
        self.reward_clip = reward_clip

    def init_train(self, buffer_size, batch_size, num_iters, num_init_rollouts_pool, num_rollouts_per_iter, num_updates_per_iter=None, sampled_seq_len=None, sample_weight_baseline=None, buffer_type=None, **kwargs):
        if num_updates_per_iter is None:
            num_updates_per_iter = 1.0
        assert isinstance(num_updates_per_iter, int) or isinstance(num_updates_per_iter, float)
        self.num_updates_per_iter = num_updates_per_iter
        if self.agent_arch == AGENT_ARCHS.Markov:
            self.policy_storage = SimpleReplayBuffer(max_replay_buffer_size=int(buffer_size), observation_dim=self.obs_dim, action_dim=self.act_dim if self.act_continuous else 1, max_trajectory_len=self.max_trajectory_len, add_timeout=False)
        else:
            if sampled_seq_len == -1:
                sampled_seq_len = self.max_trajectory_len
            if buffer_type is None or buffer_type == SeqReplayBuffer.buffer_type:
                buffer_class = SeqReplayBuffer
            elif buffer_type == RAMEfficient_SeqReplayBuffer.buffer_type:
                buffer_class = RAMEfficient_SeqReplayBuffer
            logger.log(buffer_class)
            self.policy_storage = buffer_class(max_replay_buffer_size=int(buffer_size), observation_dim=self.obs_dim, action_dim=self.act_dim if self.act_continuous else 1, sampled_seq_len=sampled_seq_len, sample_weight_baseline=sample_weight_baseline, observation_type=self.train_env.observation_space.dtype)
        self.batch_size = batch_size
        self.num_iters = num_iters
        self.num_init_rollouts_pool = num_init_rollouts_pool
        self.num_rollouts_per_iter = num_rollouts_per_iter
        total_rollouts = num_init_rollouts_pool + num_iters * num_rollouts_per_iter
        self.n_env_steps_total = self.max_trajectory_len * total_rollouts
        logger.log('*** total rollouts', total_rollouts, 'total env steps', self.n_env_steps_total)

    def init_eval(self, log_interval, save_interval, log_tensorboard, eval_stochastic=False, num_episodes_per_task=1, **kwargs):
        self.log_interval = log_interval
        self.save_interval = save_interval
        self.log_tensorboard = log_tensorboard
        self.eval_stochastic = eval_stochastic
        self.eval_num_episodes_per_task = num_episodes_per_task

    def _start_training(self):
        self._n_env_steps_total = 0
        self._n_env_steps_total_last = 0
        self._n_rl_update_steps_total = 0
        self._n_rollouts_total = 0
        self._successes_in_buffer = 0
        self._start_time = time.time()
        self._start_time_last = time.time()

    def train(self):
        """
        training loop
        """
        self._start_training()
        if self.num_init_rollouts_pool > 0:
            logger.log('Collecting initial pool of data..')
            while self._n_env_steps_total < self.num_init_rollouts_pool * self.max_trajectory_len:
                self.collect_rollouts(num_rollouts=1, random_actions=True)
            logger.log('Done! env steps', self._n_env_steps_total, 'rollouts', self._n_rollouts_total)
            if isinstance(self.num_updates_per_iter, float):
                train_stats = self.update(int(self._n_env_steps_total * self.num_updates_per_iter))
                self.log_train_stats(train_stats)
        last_eval_num_iters = 0
        while self._n_env_steps_total < self.n_env_steps_total:
            env_steps = self.collect_rollouts(num_rollouts=self.num_rollouts_per_iter)
            logger.log('env steps', self._n_env_steps_total)
            train_stats = self.update(self.num_updates_per_iter if isinstance(self.num_updates_per_iter, int) else int(math.ceil(self.num_updates_per_iter * env_steps)))
            self.log_train_stats(train_stats)
            current_num_iters = self._n_env_steps_total // (self.num_rollouts_per_iter * self.max_trajectory_len)
            if current_num_iters != last_eval_num_iters and current_num_iters % self.log_interval == 0:
                last_eval_num_iters = current_num_iters
                perf = self.log()
                if self.save_interval > 0 and self._n_env_steps_total > 0.75 * self.n_env_steps_total and (current_num_iters % self.save_interval == 0):
                    self.save_model(current_num_iters, perf)
        self.save_model(current_num_iters, perf)

    @torch.no_grad()
    def collect_rollouts(self, num_rollouts, random_actions=False):
        """collect num_rollouts of trajectories in task and save into policy buffer
        :param random_actions: whether to use policy to sample actions, or randomly sample action space
        """
        before_env_steps = self._n_env_steps_total
        for idx in range(num_rollouts):
            steps = 0
            if self.env_type == 'meta' and self.train_env.n_tasks is not None:
                task = self.train_tasks[np.random.randint(len(self.train_tasks))]
                obs = ptu.from_numpy(self.train_env.reset(task=task))
            else:
                obs = ptu.from_numpy(self.train_env.reset())
            obs = obs.reshape(1, obs.shape[-1])
            done_rollout = False
            if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
                obs_list, act_list, rew_list, next_obs_list, term_list = ([], [], [], [], [])
            if self.agent_arch == AGENT_ARCHS.Memory:
                action, reward, internal_state = self.agent.get_initial_info()
            while not done_rollout:
                if random_actions:
                    action = ptu.FloatTensor([self.train_env.action_space.sample()])
                    if not self.act_continuous:
                        action = F.one_hot(action.long(), num_classes=self.act_dim).float()
                elif self.agent_arch == AGENT_ARCHS.Memory:
                    (action, _, _, _), internal_state = self.agent.act(prev_internal_state=internal_state, prev_action=action, reward=reward, obs=obs, deterministic=False)
                else:
                    action, _, _, _ = self.agent.act(obs, deterministic=False)
                next_obs, reward, done, info = utl.env_step(self.train_env, action.squeeze(dim=0))
                if self.reward_clip and self.env_type == 'atari':
                    reward = torch.tanh(reward)
                done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
                steps += 1
                if self.env_type == 'meta' and 'is_goal_state' in dir(self.train_env.unwrapped):
                    term = self.train_env.unwrapped.is_goal_state()
                    self._successes_in_buffer += int(term)
                elif self.env_type == 'credit':
                    term = done_rollout
                else:
                    term = False if 'TimeLimit.truncated' in info or steps >= self.max_trajectory_len else done_rollout
                if self.agent_arch == AGENT_ARCHS.Markov:
                    self.policy_storage.add_sample(observation=ptu.get_numpy(obs.squeeze(dim=0)), action=ptu.get_numpy(action.squeeze(dim=0) if self.act_continuous else torch.argmax(action.squeeze(dim=0), dim=-1, keepdims=True)), reward=ptu.get_numpy(reward.squeeze(dim=0)), terminal=np.array([term], dtype=float), next_observation=ptu.get_numpy(next_obs.squeeze(dim=0)))
                else:
                    obs_list.append(obs)
                    act_list.append(action)
                    rew_list.append(reward)
                    term_list.append(term)
                    next_obs_list.append(next_obs)
                obs = next_obs.clone()
            if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
                act_buffer = torch.cat(act_list, dim=0)
                if not self.act_continuous:
                    act_buffer = torch.argmax(act_buffer, dim=-1, keepdims=True)
                self.policy_storage.add_episode(observations=ptu.get_numpy(torch.cat(obs_list, dim=0)), actions=ptu.get_numpy(act_buffer), rewards=ptu.get_numpy(torch.cat(rew_list, dim=0)), terminals=np.array(term_list).reshape(-1, 1), next_observations=ptu.get_numpy(torch.cat(next_obs_list, dim=0)))
                print(f'steps: {steps} term: {term} ret: {torch.cat(rew_list, dim=0).sum().item():.2f}')
            self._n_env_steps_total += steps
            self._n_rollouts_total += 1
        return self._n_env_steps_total - before_env_steps

    def sample_rl_batch(self, batch_size):
        """sample batch of episodes for vae training"""
        if self.agent_arch == AGENT_ARCHS.Markov:
            batch = self.policy_storage.random_batch(batch_size)
        else:
            batch = self.policy_storage.random_episodes(batch_size)
        return ptu.np_to_pytorch_batch(batch)

    def update(self, num_updates):
        rl_losses_agg = {}
        for update in range(num_updates):
            batch = self.sample_rl_batch(self.batch_size)
            rl_losses = self.agent.update(batch)
            for k, v in rl_losses.items():
                if update == 0:
                    rl_losses_agg[k] = [v]
                else:
                    rl_losses_agg[k].append(v)
        for k in rl_losses_agg:
            rl_losses_agg[k] = np.mean(rl_losses_agg[k])
        self._n_rl_update_steps_total += num_updates
        return rl_losses_agg

    @torch.no_grad()
    def evaluate(self, tasks, deterministic=True):
        num_episodes = self.max_rollouts_per_task
        returns_per_episode = np.zeros((len(tasks), num_episodes))
        success_rate = np.zeros(len(tasks))
        total_steps = np.zeros(len(tasks))
        if self.env_type == 'meta':
            num_steps_per_episode = self.eval_env.unwrapped._max_episode_steps
            obs_size = self.eval_env.unwrapped.observation_space.shape[0]
            observations = np.zeros((len(tasks), self.max_trajectory_len + 1, obs_size))
        else:
            num_steps_per_episode = self.eval_env._max_episode_steps
            observations = None
        for task_idx, task in enumerate(tasks):
            step = 0
            if self.env_type == 'meta' and self.eval_env.n_tasks is not None:
                obs = ptu.from_numpy(self.eval_env.reset(task=task))
                observations[task_idx, step, :] = ptu.get_numpy(obs[:obs_size])
            else:
                obs = ptu.from_numpy(self.eval_env.reset())
            obs = obs.reshape(1, obs.shape[-1])
            if self.agent_arch == AGENT_ARCHS.Memory:
                action, reward, internal_state = self.agent.get_initial_info()
            for episode_idx in range(num_episodes):
                running_reward = 0.0
                for _ in range(num_steps_per_episode):
                    if self.agent_arch == AGENT_ARCHS.Memory:
                        (action, _, _, _), internal_state = self.agent.act(prev_internal_state=internal_state, prev_action=action, reward=reward, obs=obs, deterministic=deterministic)
                    else:
                        action, _, _, _ = self.agent.act(obs, deterministic=deterministic)
                    next_obs, reward, done, info = utl.env_step(self.eval_env, action.squeeze(dim=0))
                    running_reward += reward.item()
                    if self.reward_clip and self.env_type == 'atari':
                        reward = torch.tanh(reward)
                    step += 1
                    done_rollout = False if ptu.get_numpy(done[0][0]) == 0.0 else True
                    if self.env_type == 'meta':
                        observations[task_idx, step, :] = ptu.get_numpy(next_obs[0, :obs_size])
                    obs = next_obs.clone()
                    if self.env_type == 'meta' and 'is_goal_state' in dir(self.eval_env.unwrapped) and self.eval_env.unwrapped.is_goal_state():
                        success_rate[task_idx] = 1.0
                    elif self.env_type == 'generalize' and self.eval_env.unwrapped.is_success():
                        success_rate[task_idx] = 1.0
                    elif 'success' in info and info['success'] == True:
                        success_rate[task_idx] = 1.0
                    if done_rollout:
                        break
                    if self.env_type == 'meta' and info['done_mdp'] == True:
                        break
                returns_per_episode[task_idx, episode_idx] = running_reward
            total_steps[task_idx] = step
        return (returns_per_episode, success_rate, observations, total_steps)

    def log_train_stats(self, train_stats):
        logger.record_step(self._n_env_steps_total)
        for k, v in train_stats.items():
            logger.record_tabular('rl_loss/' + k, v)
        if self.agent_arch in [AGENT_ARCHS.Memory, AGENT_ARCHS.Memory_Markov]:
            results = self.agent.report_grad_norm()
            for k, v in results.items():
                logger.record_tabular('rl_loss/' + k, v)
        logger.dump_tabular()

    def log(self):
        logger.record_step(self._n_env_steps_total)
        logger.record_tabular('z/env_steps', self._n_env_steps_total)
        logger.record_tabular('z/rollouts', self._n_rollouts_total)
        logger.record_tabular('z/rl_steps', self._n_rl_update_steps_total)
        if self.env_type == 'meta':
            if self.train_env.n_tasks is not None:
                returns_train, success_rate_train, observations, total_steps_train = self.evaluate(self.train_tasks[:len(self.eval_tasks)])
            returns_eval, success_rate_eval, observations_eval, total_steps_eval = self.evaluate(self.eval_tasks)
            if self.eval_stochastic:
                returns_eval_sto, success_rate_eval_sto, observations_eval_sto, total_steps_eval_sto = self.evaluate(self.eval_tasks, deterministic=False)
            if self.train_env.n_tasks is not None and 'plot_behavior' in dir(self.eval_env.unwrapped):
                for i, task in enumerate(self.train_tasks[:min(5, len(self.eval_tasks))]):
                    self.eval_env.reset(task=task)
                    logger.add_figure('trajectory/train_task_{}'.format(i), utl_eval.plot_rollouts(observations[i, :], self.eval_env))
                for i, task in enumerate(self.eval_tasks[:min(5, len(self.eval_tasks))]):
                    self.eval_env.reset(task=task)
                    logger.add_figure('trajectory/eval_task_{}'.format(i), utl_eval.plot_rollouts(observations_eval[i, :], self.eval_env))
                    if self.eval_stochastic:
                        logger.add_figure('trajectory/eval_task_{}_sto'.format(i), utl_eval.plot_rollouts(observations_eval_sto[i, :], self.eval_env))
            if 'is_goal_state' in dir(self.eval_env.unwrapped):
                logger.record_tabular('metrics/successes_in_buffer', self._successes_in_buffer / self._n_env_steps_total)
                if self.train_env.n_tasks is not None:
                    logger.record_tabular('metrics/success_rate_train', np.mean(success_rate_train))
                logger.record_tabular('metrics/success_rate_eval', np.mean(success_rate_eval))
                if self.eval_stochastic:
                    logger.record_tabular('metrics/success_rate_eval_sto', np.mean(success_rate_eval_sto))
            for episode_idx in range(self.max_rollouts_per_task):
                if self.train_env.n_tasks is not None:
                    logger.record_tabular('metrics/return_train_episode_{}'.format(episode_idx + 1), np.mean(returns_train[:, episode_idx]))
                logger.record_tabular('metrics/return_eval_episode_{}'.format(episode_idx + 1), np.mean(returns_eval[:, episode_idx]))
                if self.eval_stochastic:
                    logger.record_tabular('metrics/return_eval_episode_{}_sto'.format(episode_idx + 1), np.mean(returns_eval_sto[:, episode_idx]))
            if self.train_env.n_tasks is not None:
                logger.record_tabular('metrics/total_steps_train', np.mean(total_steps_train))
                logger.record_tabular('metrics/return_train_total', np.mean(np.sum(returns_train, axis=-1)))
            logger.record_tabular('metrics/total_steps_eval', np.mean(total_steps_eval))
            logger.record_tabular('metrics/return_eval_total', np.mean(np.sum(returns_eval, axis=-1)))
            if self.eval_stochastic:
                logger.record_tabular('metrics/total_steps_eval_sto', np.mean(total_steps_eval_sto))
                logger.record_tabular('metrics/return_eval_total_sto', np.mean(np.sum(returns_eval_sto, axis=-1)))
        elif self.env_type == 'generalize':
            returns_eval, success_rate_eval, total_steps_eval = ({}, {}, {})
            for env, (env_name, eval_num_episodes_per_task) in self.eval_envs.items():
                self.eval_env = env
                for suffix, deterministic in zip(['', '_sto'], [True, False]):
                    if deterministic == False and self.eval_stochastic == False:
                        continue
                    return_eval, success_eval, _, total_step_eval = self.evaluate(eval_num_episodes_per_task * [None], deterministic=deterministic)
                    returns_eval[self.train_env_name + env_name + suffix] = return_eval.squeeze(-1)
                    success_rate_eval[self.train_env_name + env_name + suffix] = success_eval
                    total_steps_eval[self.train_env_name + env_name + suffix] = total_step_eval
            for k, v in returns_eval.items():
                logger.record_tabular(f'metrics/return_eval_{k}', np.mean(v))
            for k, v in success_rate_eval.items():
                logger.record_tabular(f'metrics/succ_eval_{k}', np.mean(v))
            for k, v in total_steps_eval.items():
                logger.record_tabular(f'metrics/total_steps_eval_{k}', np.mean(v))
        elif self.env_type == 'rmdp':
            returns_eval, _, _, total_steps_eval = self.evaluate(self.eval_tasks)
            returns_eval = returns_eval.squeeze(-1)
            cutoff = np.percentile(returns_eval, 100 * self.worst_percentile)
            worst_indices = np.where(returns_eval <= cutoff)
            returns_eval_worst, total_steps_eval_worst = (returns_eval[worst_indices], total_steps_eval[worst_indices])
            logger.record_tabular('metrics/return_eval_avg', returns_eval.mean())
            logger.record_tabular('metrics/return_eval_worst', returns_eval_worst.mean())
            logger.record_tabular('metrics/total_steps_eval_avg', total_steps_eval.mean())
            logger.record_tabular('metrics/total_steps_eval_worst', total_steps_eval_worst.mean())
        elif self.env_type in ['pomdp', 'credit', 'atari']:
            returns_eval, success_rate_eval, _, total_steps_eval = self.evaluate(self.eval_tasks)
            if self.eval_stochastic:
                returns_eval_sto, success_rate_eval_sto, _, total_steps_eval_sto = self.evaluate(self.eval_tasks, deterministic=False)
            logger.record_tabular('metrics/total_steps_eval', np.mean(total_steps_eval))
            logger.record_tabular('metrics/return_eval_total', np.mean(np.sum(returns_eval, axis=-1)))
            logger.record_tabular('metrics/success_rate_eval', np.mean(success_rate_eval))
            if self.eval_stochastic:
                logger.record_tabular('metrics/total_steps_eval_sto', np.mean(total_steps_eval_sto))
                logger.record_tabular('metrics/return_eval_total_sto', np.mean(np.sum(returns_eval_sto, axis=-1)))
                logger.record_tabular('metrics/success_rate_eval_sto', np.mean(success_rate_eval_sto))
        else:
            raise ValueError
        logger.record_tabular('z/time_cost', int(time.time() - self._start_time))
        logger.record_tabular('z/fps', (self._n_env_steps_total - self._n_env_steps_total_last) / (time.time() - self._start_time_last))
        self._n_env_steps_total_last = self._n_env_steps_total
        self._start_time_last = time.time()
        logger.dump_tabular()
        if self.env_type == 'generalize':
            return sum([v.mean() for v in success_rate_eval.values()]) / len(success_rate_eval)
        else:
            return np.mean(np.sum(returns_eval, axis=-1))

    def save_model(self, iter, perf):
        save_path = os.path.join(logger.get_dir(), 'save', f'agent_{iter}_perf{perf:.3f}.pt')
        torch.save(self.agent.state_dict(), save_path)

    def load_model(self, ckpt_path):
        self.agent.load_state_dict(torch.load(ckpt_path, map_location=ptu.device))
        print('load successfully from', ckpt_path)

def init_agent(self, seq_model, separate: bool=True, image_encoder=None, reward_clip=False, **kwargs):
    if seq_model == 'mlp':
        agent_class = AGENT_CLASSES['Policy_MLP']
        rnn_encoder_type = None
        assert separate == True
    elif '-mlp' in seq_model:
        agent_class = AGENT_CLASSES['Policy_RNN_MLP']
        rnn_encoder_type = seq_model.split('-')[0]
        assert separate == True
    else:
        rnn_encoder_type = seq_model
        if separate == True:
            agent_class = AGENT_CLASSES['Policy_Separate_RNN']
        else:
            agent_class = AGENT_CLASSES['Policy_Shared_RNN']
    self.agent_arch = agent_class.ARCH
    logger.log(agent_class, self.agent_arch)
    if image_encoder is not None:
        image_encoder_fn = lambda: ImageEncoder(image_shape=self.train_env.image_space.shape, **image_encoder)
    else:
        image_encoder_fn = lambda: None
    self.agent = agent_class(encoder=rnn_encoder_type, obs_dim=self.obs_dim, action_dim=self.act_dim, image_encoder_fn=image_encoder_fn, **kwargs).to(ptu.device)
    logger.log(self.agent)
    self.reward_clip = reward_clip

def init_train(self, buffer_size, batch_size, num_iters, num_init_rollouts_pool, num_rollouts_per_iter, num_updates_per_iter=None, sampled_seq_len=None, sample_weight_baseline=None, buffer_type=None, **kwargs):
    if num_updates_per_iter is None:
        num_updates_per_iter = 1.0
    assert isinstance(num_updates_per_iter, int) or isinstance(num_updates_per_iter, float)
    self.num_updates_per_iter = num_updates_per_iter
    if self.agent_arch == AGENT_ARCHS.Markov:
        self.policy_storage = SimpleReplayBuffer(max_replay_buffer_size=int(buffer_size), observation_dim=self.obs_dim, action_dim=self.act_dim if self.act_continuous else 1, max_trajectory_len=self.max_trajectory_len, add_timeout=False)
    else:
        if sampled_seq_len == -1:
            sampled_seq_len = self.max_trajectory_len
        if buffer_type is None or buffer_type == SeqReplayBuffer.buffer_type:
            buffer_class = SeqReplayBuffer
        elif buffer_type == RAMEfficient_SeqReplayBuffer.buffer_type:
            buffer_class = RAMEfficient_SeqReplayBuffer
        logger.log(buffer_class)
        self.policy_storage = buffer_class(max_replay_buffer_size=int(buffer_size), observation_dim=self.obs_dim, action_dim=self.act_dim if self.act_continuous else 1, sampled_seq_len=sampled_seq_len, sample_weight_baseline=sample_weight_baseline, observation_type=self.train_env.observation_space.dtype)
    self.batch_size = batch_size
    self.num_iters = num_iters
    self.num_init_rollouts_pool = num_init_rollouts_pool
    self.num_rollouts_per_iter = num_rollouts_per_iter
    total_rollouts = num_init_rollouts_pool + num_iters * num_rollouts_per_iter
    self.n_env_steps_total = self.max_trajectory_len * total_rollouts
    logger.log('*** total rollouts', total_rollouts, 'total env steps', self.n_env_steps_total)

def train(self):
    """
        training loop
        """
    self._start_training()
    if self.num_init_rollouts_pool > 0:
        logger.log('Collecting initial pool of data..')
        while self._n_env_steps_total < self.num_init_rollouts_pool * self.max_trajectory_len:
            self.collect_rollouts(num_rollouts=1, random_actions=True)
        logger.log('Done! env steps', self._n_env_steps_total, 'rollouts', self._n_rollouts_total)
        if isinstance(self.num_updates_per_iter, float):
            train_stats = self.update(int(self._n_env_steps_total * self.num_updates_per_iter))
            self.log_train_stats(train_stats)
    last_eval_num_iters = 0
    while self._n_env_steps_total < self.n_env_steps_total:
        env_steps = self.collect_rollouts(num_rollouts=self.num_rollouts_per_iter)
        logger.log('env steps', self._n_env_steps_total)
        train_stats = self.update(self.num_updates_per_iter if isinstance(self.num_updates_per_iter, int) else int(math.ceil(self.num_updates_per_iter * env_steps)))
        self.log_train_stats(train_stats)
        current_num_iters = self._n_env_steps_total // (self.num_rollouts_per_iter * self.max_trajectory_len)
        if current_num_iters != last_eval_num_iters and current_num_iters % self.log_interval == 0:
            last_eval_num_iters = current_num_iters
            perf = self.log()
            if self.save_interval > 0 and self._n_env_steps_total > 0.75 * self.n_env_steps_total and (current_num_iters % self.save_interval == 0):
                self.save_model(current_num_iters, perf)
    self.save_model(current_num_iters, perf)

def update(self, num_updates):
    rl_losses_agg = {}
    for update in range(num_updates):
        batch = self.sample_rl_batch(self.batch_size)
        rl_losses = self.agent.update(batch)
        for k, v in rl_losses.items():
            if update == 0:
                rl_losses_agg[k] = [v]
            else:
                rl_losses_agg[k].append(v)
    for k in rl_losses_agg:
        rl_losses_agg[k] = np.mean(rl_losses_agg[k])
    self._n_rl_update_steps_total += num_updates
    return rl_losses_agg

