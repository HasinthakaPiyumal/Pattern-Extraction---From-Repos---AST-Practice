# Cluster 30

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

def render(self, mode):
    return self.env.render(mode)

class GymEnvironment(BaseGymEnvironment):
    metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': 50}
    worlds = None

    def __init__(self, obs_type='image', frameskip=4, world='baseline'):
        self._env = PhysicalEnvironment(world=self.worlds[world])
        self._world = world
        self.action_space = spaces.Discrete(self._env.world.n_actions)
        if obs_type == 'image':
            self.observation_space = spaces.Box(low=0, high=255, shape=(self._env.height, self._env.width, 3))
        else:
            raise error.Error('Unrecognized observation type: {}'.format(obs_type))
        self._obs_type = obs_type
        self._frameskip = frameskip

    def __getstate__(self):
        return {'obs_type': self._obs_type, 'frameskip': self._frameskip, 'world': self._world}

    def __setstate__(self, state):
        self.__init__(**state)

    def _get_observation(self):
        if self._obs_type == 'image':
            return self._env.render(mode='rgb_array')
        raise NotImplementedError

    def _reset(self):
        self._env.reset()
        self._env.step()
        return self._get_observation()

    def _seed(self, seed=None):
        seed = self._env.seed(seed)
        return [seed]

    def _step(self, action):
        score = self._env.world.score
        self._env.act(action)
        for _ in range(self._frameskip):
            terminal = self._env.step()
            if terminal:
                break
        observation = self._get_observation()
        reward = self._env.world.score - score
        info = {'lives': self._env.world.lives}
        return (observation, reward, terminal, info)

    def _render(self, mode='human', close=False):
        if close:
            return
        return self._env.render(mode)

    def get_action_meanings(self):
        return []

    @property
    def lives(self):
        return self._env.world.lives

    @property
    def parameters(self):
        parameters = super(GymEnvironment, self).parameters
        parameters.update(self._env.world.parameters)
        return parameters

def _get_observation(self):
    if self._obs_type == 'image':
        return self._env.render(mode='rgb_array')
    raise NotImplementedError

def _render(self, mode='human', close=False):
    if close:
        return
    return self._env.render(mode)

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

def render(self, mode='human'):
    if mode == 'rgb_array':
        self._get_viewer().render()
        width, height = (500, 500)
        data = self._get_viewer().read_pixels(width, height, depth=False)
        return data
    elif mode == 'human':
        self._get_viewer().render()

