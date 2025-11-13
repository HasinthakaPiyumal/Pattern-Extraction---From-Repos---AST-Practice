# Cluster 9

def plot_latents(latent_means, latent_logvars, rewards_preds, num_episodes, num_steps_per_episode):
    """
    Plot mean/variance/pred_rewards over time
    """
    plt.figure(figsize=(10, 8))
    plt.subplot(2, 2, 2)
    plt.plot(range(latent_means.shape[0]), latent_means, '.-', alpha=0.5)
    plt.plot(range(latent_means.shape[0]), latent_means.mean(axis=1), 'k.-')
    for tj in np.cumsum([0, *[num_steps_per_episode for _ in range(num_episodes)]]):
        span = latent_means.max() - latent_means.min()
        plt.plot([tj + 0.5, tj + 0.5], [latent_means.min() - span * 0.05, latent_means.max() + span * 0.05], 'k--', alpha=0.5)
    plt.xlabel('env steps', fontsize=15)
    plt.ylabel('latent mean', fontsize=15)
    plt.subplot(2, 2, 4)
    latent_vars = np.exp(latent_logvars)
    plt.plot(range(latent_vars.shape[0]), latent_vars, '.-', alpha=0.5)
    plt.plot(range(latent_vars.shape[0]), latent_vars.mean(axis=1), 'k.-')
    for tj in np.cumsum([0, *[num_steps_per_episode for _ in range(num_episodes)]]):
        span = latent_vars.max() - latent_vars.min()
        plt.plot([tj + 0.5, tj + 0.5], [latent_vars.min() - span * 0.05, latent_vars.max() + span * 0.05], 'k--', alpha=0.5)
    plt.xlabel('env steps', fontsize=15)
    plt.ylabel('latent variance', fontsize=15)
    plt.subplot(1, 2, 1)
    plt.plot(range(rewards_preds.shape[0]), rewards_preds, '.-', alpha=0.5)
    plt.plot(range(rewards_preds.shape[0]), rewards_preds.mean(axis=1), 'k.-')
    for tj in np.cumsum([0, *[num_steps_per_episode for _ in range(num_episodes)]]):
        span = rewards_preds.max() - rewards_preds.min()
        plt.plot([tj + 0.5, tj + 0.5], [rewards_preds.min() - span * 0.05, rewards_preds.max() + span * 0.05], 'k--', alpha=0.5)
    plt.xlabel('env steps', fontsize=15)
    plt.ylabel('$R^{+}=\\mathbb{E}[P(R=1)]$ for each cell', fontsize=15)
    plt.tight_layout()
    plt.show()

def vis_rew_pred(args, rew_pred_arr, goal, **kwargs):
    env = gym.make(args.env_name)
    if args.env_name.startswith('GridNavi'):
        fig = plt.figure(figsize=(6, 6))
    else:
        fig = plt.figure(figsize=(12, 6))
    ax = plt.gca()
    cmap = plt.cm.viridis
    for state in env.states:
        cell = Rectangle((state[0], state[1]), width=1, height=1, fc=cmap(rew_pred_arr[ptu.get_numpy(env.task_to_id(ptu.FloatTensor(state)))[0]]))
        ax.add_patch(cell)
        ax.text(state[0] + 0.5, state[1] + 0.5, rew_pred_arr[ptu.get_numpy(env.task_to_id(ptu.FloatTensor(state)))[0]], ha='center', va='center', color='w')
    plt.xlim(env.observation_space.low[0] - 0.1, env.observation_space.high[0] + 1 + 0.1)
    plt.ylim(env.observation_space.low[1] - 0.1, env.observation_space.high[1] + 1 + 0.1)
    line = Line2D([goal[0] + 0.3, goal[0] + 0.7], [goal[1] + 0.3, goal[1] + 0.7], lw=5, color='black', axes=ax)
    ax.add_line(line)
    line = Line2D([goal[0] + 0.3, goal[0] + 0.7], [goal[1] + 0.7, goal[1] + 0.3], lw=5, color='black', axes=ax)
    ax.add_line(line)
    if 'title' in kwargs:
        plt.title(kwargs['title'])
    if args.env_name.startswith('GridNavi'):
        ax.axis('equal')
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(axis='both', which='both', length=0)
    fig.tight_layout()
    return fig

def plot_discretized_belief_halfcircle(belief_rewards, center_points, env, observations):
    fig = plt.figure()
    env.plot_behavior(observations, plot_env=True, color=cols_deep[3], linewidth=5)
    res = center_points[1, 0] - center_points[0, 0]
    normal = pl.Normalize(0.0, 1.0)
    colors = pl.cm.gray(normal(belief_rewards))
    for (x, y), c in zip(center_points, colors):
        rec = Rectangle((x, y), res, res, facecolor=c, alpha=0.85, edgecolor='none')
        plt.gca().add_patch(rec)
    cax, _ = cbar.make_axes(plt.gca())
    cb2 = cbar.ColorbarBase(cax, cmap=pl.cm.gray, norm=normal)
    return fig

def plot_rew_pred_vs_rew(rewards, reward_preds):
    fig = plt.figure()
    plt.scatter(range(len(rewards)), rewards, color=cols_dark[0], label='rew')
    plt.scatter(range(len(reward_preds)), reward_preds, color=cols_dark[1], label='rew pred.')
    plt.legend()
    return fig

def plot_rollouts(observations, env):
    """
        very similar to visualize behaviour but targeted to TensorBoard vis.
    :param observations:
    :param env:
    :return:
    """
    episode_len = env.unwrapped._max_episode_steps
    assert ((len(observations) - 1) / episode_len).is_integer(), 'Error in observations length - env mismatch'
    if isinstance(observations, list):
        observations = torch.cat(observations)
    if observations.shape[-1] > 2:
        observations = observations[:, :2]
    num_episodes = int((len(observations) - 1) / episode_len)
    plot_env = True
    fig = plt.figure(figsize=(12, 10))
    for episode in range(num_episodes):
        env.plot_behavior(observations[episode * episode_len + 1:(episode + 1) * episode_len + 1], plot_env=plot_env, color=cols_dark[episode], label='Episode {}'.format(episode + 1))
        plot_env = False
    plt.legend()
    return fig

def plot_visited_states(observations, env):
    fig = plt.figure(figsize=(12, 10))
    env.plot_env()
    plt.scatter(observations[:, 0], observations[:, 1], color=cols_dark[3], marker='.')
    return fig

def visualize_bahavior(observations, env):
    """

    :param observations:
    :param env:
    :param num_episodes:
    :return:
    """
    episode_len = env.unwrapped._max_episode_steps
    assert ((len(observations) - 1) / episode_len).is_integer(), 'Error in observations length - env mismatch'
    if isinstance(observations, list):
        observations = torch.cat(observations)
    if observations.shape[-1] > 2:
        observations = observations[:, :2]
    num_episodes = int((len(observations) - 1) / episode_len)
    timesteps = np.linspace(1, episode_len, 4, dtype=int)
    fig = plt.figure(figsize=(10, 10))
    for episode in range(num_episodes):
        for t_i, timestep in enumerate(timesteps):
            plt.subplot(num_episodes, len(timesteps), t_i + 1 + episode * len(timesteps))
            env.plot_behavior(torch.cat((observations[:1, :], observations[episode * episode_len + 1:episode * episode_len + 1 + timestep])))
            if t_i == 0:
                plt.ylabel('Episode {}'.format(episode + 1))
            if episode == 0:
                plt.title('t={}'.format(timestep))
    return fig

def visualize_latent_space(latent_dim, n_samples, decoder):
    latents = ptu.FloatTensor(sample_random_normal(latent_dim, n_samples))
    pred_rewards = ptu.get_numpy(decoder(latents, None))
    goal_locations = np.argmax(pred_rewards, axis=-1)
    if latent_dim > 2:
        tsne = TSNE(n_components=2, verbose=1, perplexity=40, n_iter=300)
        tsne_results = tsne.fit_transform(latents)
    data = tsne_results if latent_dim > 2 else latents
    df = pd.DataFrame(data, columns=['x1', 'x2'])
    df['y'] = goal_locations
    fig = plt.figure(figsize=(6, 6))
    sns.scatterplot(x='x1', y='x2', hue='y', s=30, palette=sns.color_palette('hls', len(np.unique(df['y']))), data=df, legend='full', ax=plt.gca())
    fig.show()
    return (data, goal_locations)

class Atari(gym.Env):
    """
    all follow DreamerV2
    NOTE: don't clip rewards here, as we need raw scores for comparison.
    """
    LOCK = threading.Lock()

    def __init__(self, name, action_repeat=4, size=(64, 64), grayscale=True, noops=30, life_done=False, sticky_actions=True, all_actions=True, flatten_img=True):
        assert size[0] == size[1]
        channels = 1 if grayscale else 3
        image_sizes = (channels, size[0], size[1])
        with self.LOCK:
            env = gym.envs.atari.AtariEnv(game=name, obs_type='grayscale' if grayscale else 'rgb', frameskip=1, repeat_action_probability=0.25 if sticky_actions else 0.0, full_action_space=all_actions)
        env.get_obs = lambda: None
        env.spec = gym.envs.registration.EnvSpec('NoFrameskip-v0')
        env = gym.wrappers.AtariPreprocessing(env, noops, action_repeat, size[0], life_done, grayscale)
        self.env = env
        self.action_space = self.env.action_space
        self.image_space = gym.spaces.Box(low=0, high=255, shape=image_sizes, dtype=np.uint8)
        self.flatten_img = flatten_img
        if flatten_img:
            self.observation_space = gym.spaces.Box(low=0, high=255, shape=(np.prod(image_sizes),), dtype=np.uint8)
        else:
            self.observation_space = self.image_space

    def reset(self):
        with self.LOCK:
            image: np.ndarray = self.env.reset()
        return self.observe(image)

    def step(self, action):
        image, reward, done, info = self.env.step(action)
        return (self.observe(image), reward, done, info)

    def observe(self, image):
        if self.flatten_img:
            return image.flatten()
        else:
            return np.expand_dims(image, axis=0)

    def render(self, mode):
        return self.env.render(mode)

def __init__(self, name, action_repeat=4, size=(64, 64), grayscale=True, noops=30, life_done=False, sticky_actions=True, all_actions=True, flatten_img=True):
    assert size[0] == size[1]
    channels = 1 if grayscale else 3
    image_sizes = (channels, size[0], size[1])
    with self.LOCK:
        env = gym.envs.atari.AtariEnv(game=name, obs_type='grayscale' if grayscale else 'rgb', frameskip=1, repeat_action_probability=0.25 if sticky_actions else 0.0, full_action_space=all_actions)
    env.get_obs = lambda: None
    env.spec = gym.envs.registration.EnvSpec('NoFrameskip-v0')
    env = gym.wrappers.AtariPreprocessing(env, noops, action_repeat, size[0], life_done, grayscale)
    self.env = env
    self.action_space = self.env.action_space
    self.image_space = gym.spaces.Box(low=0, high=255, shape=image_sizes, dtype=np.uint8)
    self.flatten_img = flatten_img
    if flatten_img:
        self.observation_space = gym.spaces.Box(low=0, high=255, shape=(np.prod(image_sizes),), dtype=np.uint8)
    else:
        self.observation_space = self.image_space

class EnvSpec(object):
    """A specification for a particular instance of the environment. Used
    to register the parameters for official evaluations.

    Args:
        id (str): The official environment ID
        entry_point (Optional[str]): The Python entrypoint of the environment class (e.g. module.name:Class)
        trials (int): The number of trials to average reward over
        reward_threshold (Optional[int]): The reward threshold before the task is considered solved
        local_only: True iff the environment is to be used only on the local machine (e.g. debugging envs)
        kwargs (dict): The kwargs to pass to the environment class
        nondeterministic (bool): Whether this environment is non-deterministic even after seeding
        tags (dict[str:any]): A set of arbitrary key-value tags on this environment, including simple property=True tags

    Attributes:
        id (str): The official environment ID
        trials (int): The number of trials run in official evaluation
    """

    def __init__(self, id, entry_point=None, trials=100, reward_threshold=None, local_only=False, kwargs=None, nondeterministic=False, tags=None, max_episode_steps=None, max_episode_seconds=None, timestep_limit=None):
        self.id = id
        self.trials = trials
        self.reward_threshold = reward_threshold
        self.nondeterministic = nondeterministic
        if tags is None:
            tags = {}
        self.tags = tags
        if tags.get('wrapper_config.TimeLimit.max_episode_steps'):
            max_episode_steps = tags.get('wrapper_config.TimeLimit.max_episode_steps')
        tags['wrapper_config.TimeLimit.max_episode_steps'] = max_episode_steps
        if timestep_limit is not None:
            max_episode_steps = timestep_limit
        self.max_episode_steps = max_episode_steps
        self.max_episode_seconds = max_episode_seconds
        match = env_id_re.search(id)
        if not match:
            raise error.Error('Attempted to register malformed environment ID: {}. (Currently all IDs must be of the form {}.)'.format(id, env_id_re.pattern))
        self._env_name = match.group(1)
        self._entry_point = entry_point
        self._local_only = local_only
        self._kwargs = {} if kwargs is None else kwargs

    def make(self, **kwargs):
        """Instantiates an instance of the environment with appropriate kwargs"""
        if self._entry_point is None:
            raise error.Error('Attempting to make deprecated env {}. (HINT: is there a newer registered version of this env?)'.format(self.id))
        elif callable(self._entry_point):
            env = self._entry_point(**kwargs)
        else:
            cls = load(self._entry_point)
            env = cls(**self._kwargs, **kwargs)
        env.unwrapped.spec = self
        return env

    def __repr__(self):
        return 'EnvSpec({})'.format(self.id)

    @property
    def timestep_limit(self):
        return self.max_episode_steps

    @timestep_limit.setter
    def timestep_limit(self, value):
        self.max_episode_steps = value

def __init__(self, id, entry_point=None, trials=100, reward_threshold=None, local_only=False, kwargs=None, nondeterministic=False, tags=None, max_episode_steps=None, max_episode_seconds=None, timestep_limit=None):
    self.id = id
    self.trials = trials
    self.reward_threshold = reward_threshold
    self.nondeterministic = nondeterministic
    if tags is None:
        tags = {}
    self.tags = tags
    if tags.get('wrapper_config.TimeLimit.max_episode_steps'):
        max_episode_steps = tags.get('wrapper_config.TimeLimit.max_episode_steps')
    tags['wrapper_config.TimeLimit.max_episode_steps'] = max_episode_steps
    if timestep_limit is not None:
        max_episode_steps = timestep_limit
    self.max_episode_steps = max_episode_steps
    self.max_episode_seconds = max_episode_seconds
    match = env_id_re.search(id)
    if not match:
        raise error.Error('Attempted to register malformed environment ID: {}. (Currently all IDs must be of the form {}.)'.format(id, env_id_re.pattern))
    self._env_name = match.group(1)
    self._entry_point = entry_point
    self._local_only = local_only
    self._kwargs = {} if kwargs is None else kwargs

def make(self, **kwargs):
    """Instantiates an instance of the environment with appropriate kwargs"""
    if self._entry_point is None:
        raise error.Error('Attempting to make deprecated env {}. (HINT: is there a newer registered version of this env?)'.format(self.id))
    elif callable(self._entry_point):
        env = self._entry_point(**kwargs)
    else:
        cls = load(self._entry_point)
        env = cls(**self._kwargs, **kwargs)
    env.unwrapped.spec = self
    return env

def __repr__(self):
    return 'EnvSpec({})'.format(self.id)

class EnvRegistry(object):
    """Register an env by ID. IDs remain stable over time and are
    guaranteed to resolve to the same environment dynamics (or be
    desupported). The goal is that results on a particular environment
    should always be comparable, and not depend on the version of the
    code that was running.
    """

    def __init__(self):
        self.env_specs = {}

    def make(self, id, **kwargs):
        logger.info('Making new env: %s', id)
        spec = self.spec(id)
        env = spec.make(**kwargs)
        if hasattr(env, '_reset') and hasattr(env, '_step') and (not getattr(env, '_gym_disable_underscore_compat', False)):
            patch_deprecated_methods(env)
        if env.spec.timestep_limit is not None and (not spec.tags.get('vnc')):
            from .time_limit import TimeLimit
            env = TimeLimit(env, max_episode_steps=env.spec.max_episode_steps, max_episode_seconds=env.spec.max_episode_seconds)
        return env

    def all(self):
        return self.env_specs.values()

    def spec(self, id):
        match = env_id_re.search(id)
        if not match:
            raise error.Error('Attempted to look up malformed environment ID: {}. (Currently all IDs must be of the form {}.)'.format(id.encode('utf-8'), env_id_re.pattern))
        try:
            return self.env_specs[id]
        except KeyError:
            env_name = match.group(1)
            matching_envs = [valid_env_name for valid_env_name, valid_env_spec in self.env_specs.items() if env_name == valid_env_spec._env_name]
            if matching_envs:
                raise error.DeprecatedEnv('Env {} not found (valid versions include {})'.format(id, matching_envs))
            else:
                raise error.UnregisteredEnv('No registered env with id: {}'.format(id))

    def register(self, id, **kwargs):
        if id in self.env_specs:
            raise error.Error('Cannot re-register id: {}'.format(id))
        self.env_specs[id] = EnvSpec(id, **kwargs)

def spec(self, id):
    match = env_id_re.search(id)
    if not match:
        raise error.Error('Attempted to look up malformed environment ID: {}. (Currently all IDs must be of the form {}.)'.format(id.encode('utf-8'), env_id_re.pattern))
    try:
        return self.env_specs[id]
    except KeyError:
        env_name = match.group(1)
        matching_envs = [valid_env_name for valid_env_name, valid_env_spec in self.env_specs.items() if env_name == valid_env_spec._env_name]
        if matching_envs:
            raise error.DeprecatedEnv('Env {} not found (valid versions include {})'.format(id, matching_envs))
        else:
            raise error.UnregisteredEnv('No registered env with id: {}'.format(id))

def register(self, id, **kwargs):
    if id in self.env_specs:
        raise error.Error('Cannot re-register id: {}'.format(id))
    self.env_specs[id] = EnvSpec(id, **kwargs)

class HalfCheetahEnv(HalfCheetahEnv_):

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat[1:], self.sim.data.qvel.flat, self.get_body_com('torso').flat]).astype(np.float32).flatten()

    def viewer_setup(self):
        camera_id = self.model.camera_name2id('track')
        self.viewer.cam.type = 2
        self.viewer.cam.fixedcamid = camera_id
        self.viewer.cam.distance = self.model.stat.extent * 0.35
        self.viewer._hide_overlay = True

    def render(self, mode='human'):
        if mode == 'rgb_array':
            self._get_viewer().render()
            width, height = (500, 500)
            data = self._get_viewer().read_pixels(width, height, depth=False)
            return data
        elif mode == 'human':
            self._get_viewer().render()

    @staticmethod
    def visualise_behaviour(env, args, policy, iter_idx, encoder=None, image_folder=None, **kwargs):
        num_episodes = args.max_rollouts_per_task
        unwrapped_env = env.venv.unwrapped.envs[0].unwrapped
        episode_prev_obs = [[] for _ in range(num_episodes)]
        episode_next_obs = [[] for _ in range(num_episodes)]
        episode_actions = [[] for _ in range(num_episodes)]
        episode_rewards = [[] for _ in range(num_episodes)]
        episode_returns = []
        episode_lengths = []
        if encoder is not None:
            episode_latent_samples = [[] for _ in range(num_episodes)]
            episode_latent_means = [[] for _ in range(num_episodes)]
            episode_latent_logvars = [[] for _ in range(num_episodes)]
            sample_embeddings = args.sample_embeddings
        else:
            episode_latent_samples = episode_latent_means = episode_latent_logvars = None
            sample_embeddings = False
        env.reset_task()
        obs_raw, obs_normalised = env.reset()
        obs_raw = obs_raw.float().reshape((1, -1)).to(device)
        obs_normalised = obs_normalised.float().reshape((1, -1)).to(device)
        start_obs_raw = obs_raw.clone()
        if hasattr(args, 'hidden_size'):
            hidden_state = torch.zeros((1, args.hidden_size)).to(device)
        else:
            hidden_state = None
        task = env.get_task()
        pos = [[] for _ in range(args.max_rollouts_per_task)]
        pos[0] = [unwrapped_env.get_body_com('torso')[0]]
        for episode_idx in range(num_episodes):
            curr_rollout_rew = []
            if episode_idx == 0:
                if encoder is not None:
                    curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder.prior(1)
                    curr_latent_sample = curr_latent_sample[0].to(device)
                    curr_latent_mean = curr_latent_mean[0].to(device)
                    curr_latent_logvar = curr_latent_logvar[0].to(device)
                else:
                    curr_latent_sample = curr_latent_mean = curr_latent_logvar = None
            if encoder is not None:
                episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
                episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
                episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
            pos[episode_idx].append(unwrapped_env.get_body_com('torso')[0].copy())
            for step_idx in range(1, env._max_episode_steps + 1):
                if step_idx == 1:
                    episode_prev_obs[episode_idx].append(start_obs_raw.clone())
                else:
                    episode_prev_obs[episode_idx].append(obs_raw.clone())
                o_aug = utl.get_augmented_obs(args, obs_normalised if args.norm_obs_for_policy else obs_raw, curr_latent_sample, curr_latent_mean, curr_latent_logvar)
                _, action, _ = policy.act(o_aug, deterministic=True)
                (obs_raw, obs_normalised), (rew_raw, rew_normalised), done, info = env.step(action.cpu().detach())
                obs_raw = obs_raw.float().reshape((1, -1)).to(device)
                obs_normalised = obs_normalised.float().reshape((1, -1)).to(device)
                pos[episode_idx].append(unwrapped_env.get_body_com('torso')[0].copy())
                if encoder is not None:
                    curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder(action.float().to(device), obs_raw, torch.tensor(rew_raw).reshape((1, 1)).float().to(device), hidden_state, return_prior=False)
                    episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
                    episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
                    episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
                episode_next_obs[episode_idx].append(obs_raw.clone())
                episode_rewards[episode_idx].append(rew_raw.clone())
                episode_actions[episode_idx].append(action.clone())
                if info[0]['done_mdp'] and (not done):
                    start_obs_raw = info[0]['start_state']
                    start_obs_raw = torch.from_numpy(start_obs_raw).float().reshape((1, -1)).to(device)
                    break
            episode_returns.append(sum(curr_rollout_rew))
            episode_lengths.append(step_idx)
        if encoder is not None:
            episode_latent_means = [torch.stack(e) for e in episode_latent_means]
            episode_latent_logvars = [torch.stack(e) for e in episode_latent_logvars]
        episode_prev_obs = [torch.cat(e) for e in episode_prev_obs]
        episode_next_obs = [torch.cat(e) for e in episode_next_obs]
        episode_actions = [torch.cat(e) for e in episode_actions]
        episode_rewards = [torch.cat(e) for e in episode_rewards]
        plt.figure(figsize=(7, 4 * num_episodes))
        min_x = min([min(p) for p in pos])
        max_x = max([max(p) for p in pos])
        span = max_x - min_x
        for i in range(num_episodes):
            plt.subplot(num_episodes, 1, i + 1)
            plt.plot(pos[i], range(len(pos[i])), 'k')
            plt.title('task: '.format(task), fontsize=15)
            plt.ylabel('steps (ep {})'.format(i), fontsize=15)
            if i == num_episodes - 1:
                plt.xlabel('position', fontsize=15)
            else:
                plt.xticks([])
            plt.xlim(min_x - 0.05 * span, max_x + 0.05 * span)
        plt.tight_layout()
        if image_folder is not None:
            plt.savefig('{}/{}_behaviour'.format(image_folder, iter_idx))
            plt.close()
        else:
            plt.show()
        return (episode_latent_means, episode_latent_logvars, episode_prev_obs, episode_next_obs, episode_actions, episode_rewards, episode_returns)

@staticmethod
def visualise_behaviour(env, args, policy, iter_idx, encoder=None, image_folder=None, **kwargs):
    num_episodes = args.max_rollouts_per_task
    unwrapped_env = env.venv.unwrapped.envs[0].unwrapped
    episode_prev_obs = [[] for _ in range(num_episodes)]
    episode_next_obs = [[] for _ in range(num_episodes)]
    episode_actions = [[] for _ in range(num_episodes)]
    episode_rewards = [[] for _ in range(num_episodes)]
    episode_returns = []
    episode_lengths = []
    if encoder is not None:
        episode_latent_samples = [[] for _ in range(num_episodes)]
        episode_latent_means = [[] for _ in range(num_episodes)]
        episode_latent_logvars = [[] for _ in range(num_episodes)]
        sample_embeddings = args.sample_embeddings
    else:
        episode_latent_samples = episode_latent_means = episode_latent_logvars = None
        sample_embeddings = False
    env.reset_task()
    obs_raw, obs_normalised = env.reset()
    obs_raw = obs_raw.float().reshape((1, -1)).to(device)
    obs_normalised = obs_normalised.float().reshape((1, -1)).to(device)
    start_obs_raw = obs_raw.clone()
    if hasattr(args, 'hidden_size'):
        hidden_state = torch.zeros((1, args.hidden_size)).to(device)
    else:
        hidden_state = None
    task = env.get_task()
    pos = [[] for _ in range(args.max_rollouts_per_task)]
    pos[0] = [unwrapped_env.get_body_com('torso')[0]]
    for episode_idx in range(num_episodes):
        curr_rollout_rew = []
        if episode_idx == 0:
            if encoder is not None:
                curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder.prior(1)
                curr_latent_sample = curr_latent_sample[0].to(device)
                curr_latent_mean = curr_latent_mean[0].to(device)
                curr_latent_logvar = curr_latent_logvar[0].to(device)
            else:
                curr_latent_sample = curr_latent_mean = curr_latent_logvar = None
        if encoder is not None:
            episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
            episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
            episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
        pos[episode_idx].append(unwrapped_env.get_body_com('torso')[0].copy())
        for step_idx in range(1, env._max_episode_steps + 1):
            if step_idx == 1:
                episode_prev_obs[episode_idx].append(start_obs_raw.clone())
            else:
                episode_prev_obs[episode_idx].append(obs_raw.clone())
            o_aug = utl.get_augmented_obs(args, obs_normalised if args.norm_obs_for_policy else obs_raw, curr_latent_sample, curr_latent_mean, curr_latent_logvar)
            _, action, _ = policy.act(o_aug, deterministic=True)
            (obs_raw, obs_normalised), (rew_raw, rew_normalised), done, info = env.step(action.cpu().detach())
            obs_raw = obs_raw.float().reshape((1, -1)).to(device)
            obs_normalised = obs_normalised.float().reshape((1, -1)).to(device)
            pos[episode_idx].append(unwrapped_env.get_body_com('torso')[0].copy())
            if encoder is not None:
                curr_latent_sample, curr_latent_mean, curr_latent_logvar, hidden_state = encoder(action.float().to(device), obs_raw, torch.tensor(rew_raw).reshape((1, 1)).float().to(device), hidden_state, return_prior=False)
                episode_latent_samples[episode_idx].append(curr_latent_sample[0].clone())
                episode_latent_means[episode_idx].append(curr_latent_mean[0].clone())
                episode_latent_logvars[episode_idx].append(curr_latent_logvar[0].clone())
            episode_next_obs[episode_idx].append(obs_raw.clone())
            episode_rewards[episode_idx].append(rew_raw.clone())
            episode_actions[episode_idx].append(action.clone())
            if info[0]['done_mdp'] and (not done):
                start_obs_raw = info[0]['start_state']
                start_obs_raw = torch.from_numpy(start_obs_raw).float().reshape((1, -1)).to(device)
                break
        episode_returns.append(sum(curr_rollout_rew))
        episode_lengths.append(step_idx)
    if encoder is not None:
        episode_latent_means = [torch.stack(e) for e in episode_latent_means]
        episode_latent_logvars = [torch.stack(e) for e in episode_latent_logvars]
    episode_prev_obs = [torch.cat(e) for e in episode_prev_obs]
    episode_next_obs = [torch.cat(e) for e in episode_next_obs]
    episode_actions = [torch.cat(e) for e in episode_actions]
    episode_rewards = [torch.cat(e) for e in episode_rewards]
    plt.figure(figsize=(7, 4 * num_episodes))
    min_x = min([min(p) for p in pos])
    max_x = max([max(p) for p in pos])
    span = max_x - min_x
    for i in range(num_episodes):
        plt.subplot(num_episodes, 1, i + 1)
        plt.plot(pos[i], range(len(pos[i])), 'k')
        plt.title('task: '.format(task), fontsize=15)
        plt.ylabel('steps (ep {})'.format(i), fontsize=15)
        if i == num_episodes - 1:
            plt.xlabel('position', fontsize=15)
        else:
            plt.xticks([])
        plt.xlim(min_x - 0.05 * span, max_x + 0.05 * span)
    plt.tight_layout()
    if image_folder is not None:
        plt.savefig('{}/{}_behaviour'.format(image_folder, iter_idx))
        plt.close()
    else:
        plt.show()
    return (episode_latent_means, episode_latent_logvars, episode_prev_obs, episode_next_obs, episode_actions, episode_rewards, episode_returns)

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

def tensor(*args, **kwargs):
    return torch.tensor(*args, **kwargs).to(device)

